"""The AD-5 measured test: which on-disk form the proxy cache uses (WP3.12 task 2).

Usage::

    uv run python tools/cache_store_test.py prepare [--stride N]
    uv run python tools/cache_store_test.py sizes [--only NAME ...] [--workers N]
    uv run python tools/cache_store_test.py readcost [--only NAME ...]
    uv run python tools/cache_store_test.py report
    uv run python tools/cache_store_test.py readcost-product
    uv run python tools/cache_store_test.py meansize
    uv run python tools/cache_store_test.py signed

``prepare`` decodes the footage through the FFmpeg command line to 3840x2160 ``rgb24``, takes the
exact 4x4 block mean (the analysis proxy of AD-5, 960x540) and keeps two things per clip under
``<working folder>/wp3.12/``: the 8-bit proxy of every frame (``round(255 * float proxy)``, the form
AD-5 stores) and the statistics of the FLOAT proxy of every ``stride``-th frame (the reference the
store must reproduce). ``sizes`` runs every candidate store over the 8-bit proxies, records the
bytes per frame of every frame, decodes the stride frames back and compares the statistics with the
reference, as AD-5 requires: the channel means and white-balance gains within 1e-3 relative, the
N{} bounds within 1 % (relative to each bound, and, since a bound near zero makes that ill-defined,
also relative to the bounds' range). ``readcost`` times the decode of one stored proxy per
candidate; it is the only timing here and is meant for an EXCLUSIVE window (nothing else heavy
running). ``report`` prints the markdown table from the recorded results and judges each
candidate by the criteria of AD-5 as ruled 2026-10-20 (means and gains within 1e-3 of the float
proxy; the N{} bounds deviation beyond the 8-bit floor within 10 % of the range) and, as
information, by the original 1 % bounds criterion. ``readcost-product`` times
``DiskProxyCache.proxy`` per product codec (EXCLUSIVE window). ``meansize`` encodes every frame
of both clips with the product JPEG codecs and writes the whole-clip mean, median and 95th
percentile sizes and the 60-minute extrapolations to ``meansize.txt`` (sizes only, no timing);
``signed`` writes to ``signed-bounds.txt`` the SIGNED change of the N{} bounds range of the
decoded default proxy against the float proxy and against the 8-bit proxy alone (every second
statistics frame).

Sizes are the bytes of the stored payload per frame (the product adds a 24-byte record header
and a small codec header per frame; stream candidates count the packet payloads, without
container overhead); the png-pillow-opt candidate is sized on the statistics frames only
(``sample_only``), every other candidate on every frame; the maximum and mean pixel error are
taken over the statistics frames only. ``meansize.txt`` and ``readcost-product`` use the product
codecs and carry the product sizes.

Footage is only ever read, through :func:`local_config.find_footage_file`; every file written is
under the working folder. The 4K decode and the candidates are the instrument's own; the
statistics are the prototype's (:func:`prototype.temporal.measure`, the ``c3`` default parameters).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import io
import json
import statistics
import subprocess
import sys
import time
import zlib
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

from clearwater.io.video.probe import find_tool
from local_config import find_footage_file, load_local_config
from prototype import temporal
from prototype.backend import select_backend
from prototype.params import Params

PROXY_SHORT_SIDE = 540
FACTOR = 4
SIXTY_MINUTES_FRAMES = 107_892
"""60 minutes at 29.97 fps (the brief's extrapolation basis)."""
BOUND_BYTES = 10 * 10**9
"""AD-5: a 60-minute 4K clip must fit under 10 GB."""
FRAME_RATE = "30000/1001"
WINDOW_FRAMES = 60
WINDOW_STARTS_S = (30.0, 130.0, 230.0, 330.0, 430.0)
"""GX011625 sample: five 60-frame windows spread over the 498 s clip."""
CLIPS: dict[str, tuple[float, ...] | None] = {"GX011627": None, "GX011625": WINDOW_STARTS_S}
EXPECTED_FRAMES = {"GX011627": 681, "GX011625": WINDOW_FRAMES * len(WINDOW_STARTS_S)}
"""The frames each clip must yield; ``prepare`` refuses a truncated decode."""
"""Clip stem -> window start times in seconds; None = the whole clip."""
READ_ROUNDS = 8
"""How many times each stored proxy is read back in the product read-cost row."""
CRITERIA = {"means": 1e-3, "gains": 1e-3, "bounds": 1e-2}
"""AD-5 as first written: means, gains and N{} bounds (per bound) against the float proxy."""
RULED_BOUNDS_RANGE = 0.10
"""AD-5 as ruled 2026-10-20: bounds deviation beyond the 8-bit floor, relative to the range."""

Frames = NDArray[np.uint8]
Stats = dict[str, NDArray[np.float64]]


def out_dir() -> Path:
    """Return (and create) the folder every file of this instrument goes to."""
    root = load_local_config().working_path
    out = root / "wp3.12"
    out.mkdir(parents=True, exist_ok=True)
    return out


# --- statistics -----------------------------------------------------------------------------------


def frame_stats(proxy: NDArray[np.float32]) -> Stats:
    """Return the statistics AD-5 and AD-7 care about, measured on a float proxy.

    Args:
        proxy: A proxy in [0, 1], float32, shape ``(540, 960, 3)``.

    Returns:
        ``means`` and ``gains`` (3,), ``bounds`` (2,), ``saliency`` (6,), and ``caps`` (2,): the
        Ancuti cap statistic ``mean((1 - I_c) I_g)`` for red and blue. All from
        :func:`prototype.temporal.measure` with the ``c3`` default parameters.
    """
    stats = temporal.measure(proxy, Params(), None, select_backend("cpu"))
    assert stats.white_balance_means is not None
    assert stats.white_balance_gains is not None
    assert stats.normalisation_bounds is not None
    assert stats.saliency_means is not None
    green = proxy[..., 1].astype(np.float64)
    caps = [float(np.mean((1.0 - proxy[..., c].astype(np.float64)) * green)) for c in (0, 2)]
    return {
        "means": np.asarray(stats.white_balance_means, dtype=np.float64),
        "gains": np.asarray(stats.white_balance_gains, dtype=np.float64),
        "bounds": np.asarray(stats.normalisation_bounds, dtype=np.float64),
        "saliency": np.asarray(stats.saliency_means, dtype=np.float64).reshape(-1),
        "caps": np.asarray(caps, dtype=np.float64),
    }


def deviation(candidate: Stats, reference: Stats) -> dict[str, float]:
    """Return the worst relative deviations of one frame's statistics from the reference.

    Args:
        candidate: Statistics measured on the decoded proxy.
        reference: Statistics measured on the float proxy.

    Returns:
        ``means``, ``gains``, ``bounds`` (relative to each bound), ``bounds_range`` (relative to
        the bounds' range), ``saliency`` and ``caps`` (relative), each the maximum over its entries.
    """

    def rel(name: str) -> float:
        a, b = candidate[name], reference[name]
        return float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-12)))

    span = float(reference["bounds"][1] - reference["bounds"][0])
    bound_range = float(np.max(np.abs(candidate["bounds"] - reference["bounds"])) / span)
    return {
        "means": rel("means"),
        "gains": rel("gains"),
        "bounds": rel("bounds"),
        "bounds_range": bound_range,
        "saliency": rel("saliency"),
        "caps": rel("caps"),
    }


def _stats_job(frame: Frames) -> Stats:
    """Measure one decoded 8-bit proxy (a process-pool job)."""
    return frame_stats(frame.astype(np.float32) / np.float32(255.0))


# --- prepare --------------------------------------------------------------------------------------


def _probe_size(path: Path) -> tuple[int, int]:
    """Return the (width, height) of the first video stream of ``path``."""
    done = subprocess.run(
        [
            str(find_tool("ffprobe")),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=p=0",
            str(path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    first = next(line for line in done.stdout.splitlines() if line.strip())
    width, height = first.strip().split(",")[:2]
    return int(width), int(height)


def block_proxy(frame: Frames) -> tuple[Frames, NDArray[np.float32]]:
    """Return the 8-bit and the float proxy of a decoded 4K frame (exact 4x4 block mean).

    Args:
        frame: The decoded frame, uint8, shape ``(2160, 3840, 3)``.

    Returns:
        The 8-bit proxy ``floor((block sum + 8) / 16)`` (round half up of the block mean) and the
        float32 proxy ``block sum / (16 * 255)``, both ``(540, 960, 3)``.
    """
    height, width = frame.shape[0], frame.shape[1]
    blocks = frame.reshape(height // FACTOR, FACTOR, width // FACTOR, FACTOR, 3).sum(
        axis=(1, 3), dtype=np.uint16
    )
    u8 = ((blocks + 8) >> 4).astype(np.uint8)
    flt = (blocks.astype(np.float32) / np.float32(FACTOR * FACTOR * 255.0)).astype(np.float32)
    return u8, flt


def _decode_segments(path: Path, starts: tuple[float, ...] | None, width: int, height: int) -> Any:
    """Yield decoded 4K frames of one clip: all of it, or WINDOW_FRAMES from each start."""
    segments: list[tuple[float | None, int | None]] = (
        [(None, None)] if starts is None else [(s, WINDOW_FRAMES) for s in starts]
    )
    size = width * height * 3
    for start, count in segments:
        command = [str(find_tool("ffmpeg")), "-v", "error"]
        if start is not None:
            command += ["-ss", str(start)]
        command += ["-i", str(path)]
        if count is not None:
            command += ["-frames:v", str(count)]
        command += ["-an", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
        with subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=32 * 1024 * 1024) as proc:
            assert proc.stdout is not None
            while True:
                raw = proc.stdout.read(size)
                if not raw:
                    break
                if len(raw) < size:
                    raise RuntimeError(f"{path.name}: a decoded frame was cut short")
                yield np.frombuffer(raw, dtype=np.uint8).reshape(height, width, 3)
            code = proc.wait()
        if code != 0:
            raise RuntimeError(f"ffmpeg exited with {code} decoding {path.name}")


def prepare(stride: int) -> None:
    """Decode the clips, write the 8-bit proxies and the float-proxy reference statistics."""
    out = out_dir()
    for stem, starts in CLIPS.items():
        path = find_footage_file(stem)
        width, height = _probe_size(path)
        if height != PROXY_SHORT_SIDE * FACTOR:
            raise SystemExit(f"{stem}: {width}x{height} is not a 4x4 block of 960x540")
        raw_path = out / f"proxy-{stem}.u8"
        reference: dict[int, Stats] = {}
        count = 0
        started = time.perf_counter()
        with raw_path.open("wb") as raw:
            for index, frame in enumerate(_decode_segments(path, starts, width, height)):
                u8, flt = block_proxy(frame)
                if index == 0:
                    check = temporal.proxy(frame.astype(np.float32) / np.float32(255.0))
                    drift = float(np.max(np.abs(check - flt)))
                    assert drift < 1e-6, f"block proxy differs from temporal.proxy by {drift}"
                raw.write(u8.tobytes())
                if index % stride == 0:
                    reference[index] = frame_stats(flt)
                count = index + 1
        if count != EXPECTED_FRAMES[stem]:
            raise SystemExit(f"{stem}: decoded {count} frames, expected {EXPECTED_FRAMES[stem]}")
        meta = {
            "stem": stem,
            "frames": count,
            "stride": stride,
            "stat_indices": sorted(reference),
            "reference": {
                str(i): {k: v.tolist() for k, v in s.items()} for i, s in reference.items()
            },
            "windows": None
            if starts is None
            else {"starts_s": list(starts), "frames": WINDOW_FRAMES},
            "seconds": time.perf_counter() - started,
        }
        (out / f"proxy-{stem}.json").write_text(json.dumps(meta), encoding="utf-8")
        print(f"{stem}: {count} frames, {len(reference)} reference frames, {meta['seconds']:.0f} s")


@dataclass
class ClipData:
    """One prepared clip: the 8-bit proxies (memory-mapped) and the reference statistics."""

    stem: str
    frames: Frames
    stat_indices: list[int]
    reference: dict[int, Stats]
    baseline: dict[int, Stats] = field(default_factory=dict)


def load_clip(stem: str) -> ClipData:
    """Load a clip written by :func:`prepare`."""
    out = out_dir()
    meta = json.loads((out / f"proxy-{stem}.json").read_text(encoding="utf-8"))
    count = int(meta["frames"])
    frames = np.memmap(out / f"proxy-{stem}.u8", dtype=np.uint8, mode="r").reshape(
        count, PROXY_SHORT_SIDE, 960, 3
    )
    reference = {
        int(i): {k: np.asarray(v, dtype=np.float64) for k, v in s.items()}
        for i, s in meta["reference"].items()
    }
    return ClipData(stem, frames, list(meta["stat_indices"]), reference)


# --- candidates -----------------------------------------------------------------------------------


def _filter_rows(frame: Frames, mode: str) -> bytes:
    """Return the PNG-style filtered bytes of a frame (``sub``, ``up`` or ``none``)."""
    rows = frame.reshape(frame.shape[0], -1)
    if mode == "sub":
        out = rows.copy()
        out[:, 3:] = rows[:, 3:] - rows[:, :-3]
    elif mode == "up":
        out = rows.copy()
        out[1:] = rows[1:] - rows[:-1]
    else:
        out = rows
    return out.tobytes()


def _unfilter_rows(data: bytes, mode: str, shape: tuple[int, int, int]) -> Frames:
    """Invert :func:`_filter_rows` (vectorised: a wrapped cumulative sum along the filter axis)."""
    rows = np.frombuffer(data, dtype=np.uint8).reshape(shape[0], shape[1] * shape[2])
    if mode == "sub":
        out = np.cumsum(rows.reshape(shape[0], shape[1], 3), axis=1, dtype=np.uint8)
    elif mode == "up":
        out = np.cumsum(rows.reshape(shape), axis=0, dtype=np.uint8)
    else:
        out = rows.reshape(shape)
    return np.ascontiguousarray(out)


def deflate_encode(frame: Frames, level: int, drop_bits: int = 0) -> bytes:
    """Encode one proxy as ``mode byte + zlib(filtered rows)`` with the smaller of Sub and Up.

    Args:
        frame: The 8-bit proxy.
        level: The zlib level.
        drop_bits: Low bits dropped before filtering (0 = lossless); the decoder re-centres.

    Returns:
        The blob.
    """
    work = frame
    if drop_bits:
        step = 1 << drop_bits
        work = np.minimum(
            (frame.astype(np.uint16) + step // 2) >> drop_bits, 255 >> drop_bits
        ).astype(np.uint8)
    best: bytes | None = None
    best_mode = 0
    for number, mode in enumerate(("sub", "up")):
        blob = zlib.compress(_filter_rows(work, mode), level)
        if best is None or len(blob) < len(best):
            best, best_mode = blob, number
    assert best is not None
    return bytes([best_mode]) + best


def deflate_decode(blob: bytes, drop_bits: int = 0) -> Frames:
    """Decode a blob of :func:`deflate_encode`."""
    mode = ("sub", "up")[blob[0]]
    out = _unfilter_rows(zlib.decompress(blob[1:]), mode, (PROXY_SHORT_SIDE, 960, 3))
    if drop_bits:
        wide = (out.astype(np.uint16) << drop_bits) + (1 << (drop_bits - 1))
        out = np.minimum(wide, 255).astype(np.uint8)
    return out


def _jpeg_encode(frame: Frames, quality: int, subsampling: int) -> bytes:
    from PIL import Image, ImageFile

    ImageFile.MAXBLOCK = 1 << 26  # optimize=True needs the whole scan in one buffer

    buffer = io.BytesIO()
    Image.fromarray(frame).save(
        buffer, "JPEG", quality=quality, subsampling=subsampling, optimize=True
    )
    return buffer.getvalue()


def _jpeg_decode(blob: bytes) -> Frames:
    from PIL import Image

    return np.asarray(Image.open(io.BytesIO(blob)).convert("RGB"), dtype=np.uint8)


def _png_encode(frame: Frames) -> bytes:
    from PIL import Image

    buffer = io.BytesIO()
    Image.fromarray(frame).save(buffer, "PNG", optimize=True)
    return buffer.getvalue()


def _png_decode(blob: bytes) -> Frames:
    from PIL import Image

    return np.asarray(Image.open(io.BytesIO(blob)).convert("RGB"), dtype=np.uint8)


@dataclass
class Candidate:
    """One store form under test.

    Attributes:
        name: Row name.
        family: ``deflate``, ``qdeflate``, ``png``, ``jpeg`` or an FFmpeg stream.
        lossless: Whether the form is claimed lossless (checked on the decoded frames).
        encode: Blob encoder for per-frame forms.
        decode: Blob decoder for per-frame forms.
        ffmpeg: FFmpeg output arguments for stream forms (the input is the raw 8-bit proxy file).
        sample_only: Size only the stride frames (slow encoders).
        per_read: What one read costs in the product: ``python`` (a decode call) or ``process``.
    """

    name: str
    family: str
    lossless: bool
    encode: Callable[[Frames], bytes] | None = None
    decode: Callable[[bytes], Frames] | None = None
    ffmpeg: list[str] = field(default_factory=list)
    sample_only: bool = False
    per_read: str = "python"


def candidates() -> list[Candidate]:
    """Return every candidate of the measured test (brief task 2, rulings 2 and D)."""
    rows: list[Candidate] = []
    for level in (1, 6, 9):
        rows.append(
            Candidate(
                f"deflate-L{level}",
                "deflate",
                True,
                lambda f, level=level: deflate_encode(f, level),  # type: ignore[misc]
                deflate_decode,
            )
        )
    rows.append(
        Candidate("png-pillow-opt", "png", True, _png_encode, _png_decode, sample_only=True)
    )
    ffv1 = ["-c:v", "ffv1", "-level", "3", "-g", "1", "-slicecrc", "0"]
    rows.append(Candidate("ffv1-intra", "stream", True, ffmpeg=ffv1, per_read="process"))
    rows.append(
        Candidate(
            "utvideo-median",
            "stream",
            True,
            ffmpeg=["-c:v", "utvideo", "-pred", "median"],
            per_read="process",
        )
    )
    for crf in (0, 10, 14, 18, 22):
        rows.append(
            Candidate(
                f"x264rgb-intra-crf{crf}",
                "stream",
                crf == 0,
                ffmpeg=["-c:v", "libx264rgb", "-g", "1", "-crf", str(crf), "-preset", "medium"],
                per_read="process",
            )
        )
    for crf in (6, 10, 14, 18):
        rows.append(
            Candidate(
                f"x264-444-intra-crf{crf}",
                "stream",
                False,
                ffmpeg=[
                    "-vf",
                    "scale=in_range=full:out_range=full:out_color_matrix=bt709",
                    "-c:v",
                    "libx264",
                    "-g",
                    "1",
                    "-crf",
                    str(crf),
                    "-preset",
                    "medium",
                    "-pix_fmt",
                    "yuv444p",
                    "-color_range",
                    "pc",
                    "-colorspace",
                    "bt709",
                ],
                per_read="process",
            )
        )
    for q in (2, 4, 8):
        rows.append(
            Candidate(
                f"mjpeg-444-q{q}",
                "stream",
                False,
                ffmpeg=[
                    "-c:v",
                    "mjpeg",
                    "-q:v",
                    str(q),
                    "-pix_fmt",
                    "yuvj444p",
                    "-huffman",
                    "optimal",
                ],
                per_read="process",
            )
        )
    for quality, sub, label in (
        (70, 0, "444"),
        (75, 0, "444"),
        (80, 0, "444"),
        (70, 2, "420"),
        (80, 2, "420"),
        (85, 0, "444"),
        (90, 0, "444"),
        (95, 0, "444"),
        (98, 0, "444"),
        (90, 2, "420"),
        (95, 2, "420"),
    ):
        rows.append(
            Candidate(
                f"jpeg-q{quality}-{label}",
                "jpeg",
                False,
                lambda f, q=quality, s=sub: _jpeg_encode(f, q, s),  # type: ignore[misc]
                _jpeg_decode,
            )
        )
    for bits in (1, 2, 3):
        rows.append(
            Candidate(
                f"qdeflate-drop{bits}-L6",
                "qdeflate",
                False,
                lambda f, b=bits: deflate_encode(f, 6, b),  # type: ignore[misc]
                lambda blob, b=bits: deflate_decode(blob, b),  # type: ignore[misc]
            )
        )
    return rows


def _run_ffmpeg_stream(clip: ClipData, cand: Candidate, out: Path) -> tuple[list[int], Frames]:
    """Encode the clip's raw proxies with an FFmpeg stream form; return packet sizes and frames."""
    raw = out / f"proxy-{clip.stem}.u8"
    stream = out / f"stream-{clip.stem}-{cand.name}.mkv"
    decoded = out / f"decoded-{clip.stem}-{cand.name}.u8"
    ffmpeg = str(find_tool("ffmpeg"))
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-y",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            "-s",
            "960x540",
            "-r",
            FRAME_RATE,
            "-i",
            str(raw),
            *cand.ffmpeg,
            str(stream),
        ],
        check=True,
    )
    probe = subprocess.run(
        [
            str(find_tool("ffprobe")),
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=size",
            "-of",
            "csv=p=0",
            str(stream),
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    sizes = [int(line) for line in probe.stdout.split() if line]
    subprocess.run(
        [
            ffmpeg,
            "-v",
            "error",
            "-y",
            "-i",
            str(stream),
            "-fps_mode",
            "passthrough",
            "-f",
            "rawvideo",
            "-pix_fmt",
            "rgb24",
            str(decoded),
        ],
        check=True,
    )
    frames = np.memmap(decoded, dtype=np.uint8, mode="r").reshape(-1, PROXY_SHORT_SIDE, 960, 3)
    return sizes, frames


@dataclass
class Row:
    """The recorded result of one candidate on one clip."""

    candidate: str
    clip: str
    frames_sized: int
    bytes_median: float
    bytes_p95: float
    bytes_max: int
    max_abs_error: int
    mean_abs_error: float
    exact: bool
    dev_max: dict[str, float]
    dev_p95: dict[str, float]
    dev8_max: dict[str, float]
    dev8_p95: dict[str, float]
    stat_frames: int


def _summarise(values: Sequence[float]) -> tuple[float, float, float]:
    """Return (median, 95th percentile, maximum) of ``values``."""
    arr = np.asarray(values, dtype=np.float64)
    return float(np.median(arr)), float(np.percentile(arr, 95)), float(arr.max())


def run_candidate(
    clip: ClipData, cand: Candidate, out: Path, pool: concurrent.futures.Executor
) -> Row:
    """Measure one candidate on one clip: sizes, error against the 8-bit proxy, statistics."""
    stat = clip.stat_indices
    sample = cand.sample_only
    if cand.family == "stream":
        sizes_all, frames = _run_ffmpeg_stream(clip, cand, out)
        sizes = [sizes_all[i] for i in stat] if sample else sizes_all
        decoded = [np.asarray(frames[i]) for i in stat]
    else:
        assert cand.encode is not None and cand.decode is not None
        indices = stat if sample else range(clip.frames.shape[0])
        blobs = {i: cand.encode(np.asarray(clip.frames[i])) for i in indices}
        sizes = [len(b) for b in blobs.values()]
        decoded = [
            cand.decode(blobs[i] if i in blobs else cand.encode(np.asarray(clip.frames[i])))
            for i in stat
        ]
    errs = [
        np.abs(d.astype(np.int16) - np.asarray(clip.frames[i]).astype(np.int16))
        for d, i in zip(decoded, stat, strict=True)
    ]
    max_err = int(max(int(e.max()) for e in errs))
    mean_err = float(np.mean([e.mean() for e in errs]))
    measured = list(pool.map(_stats_job, decoded))
    devs = [deviation(m, clip.reference[i]) for m, i in zip(measured, stat, strict=True)]
    devs8 = [deviation(m, clip.baseline[i]) for m, i in zip(measured, stat, strict=True)]
    keys = devs[0].keys()
    median, p95, top = _summarise(sizes)
    return Row(
        candidate=cand.name,
        clip=clip.stem,
        frames_sized=len(sizes),
        bytes_median=median,
        bytes_p95=p95,
        bytes_max=int(top),
        max_abs_error=max_err,
        mean_abs_error=mean_err,
        exact=max_err == 0,
        dev_max={k: max(d[k] for d in devs) for k in keys},
        dev_p95={k: float(np.percentile([d[k] for d in devs], 95)) for k in keys},
        dev8_max={k: max(d[k] for d in devs8) for k in keys},
        dev8_p95={k: float(np.percentile([d[k] for d in devs8], 95)) for k in keys},
        stat_frames=len(stat),
    )


def baseline_stats(
    clip: ClipData, out: Path, pool: concurrent.futures.Executor
) -> dict[int, Stats]:
    """Return the statistics of the stored 8-bit proxies themselves (the lossless baseline)."""
    path = out / f"baseline-{clip.stem}.json"
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        return {int(i): {k: np.asarray(v) for k, v in s.items()} for i, s in raw.items()}
    frames = [np.asarray(clip.frames[i]) for i in clip.stat_indices]
    found = dict(zip(clip.stat_indices, pool.map(_stats_job, frames), strict=True))
    path.write_text(
        json.dumps({str(i): {k: v.tolist() for k, v in s.items()} for i, s in found.items()}),
        encoding="utf-8",
    )
    return found


def sizes_mode(only: list[str], workers: int) -> None:
    """Run the size and statistics measurement; write ``results.json``."""
    out = out_dir()
    clips = [load_clip(stem) for stem in CLIPS]
    results_path = out / "results.json"
    results: list[dict[str, Any]] = (
        json.loads(results_path.read_text(encoding="utf-8")) if results_path.exists() else []
    )
    chosen = [c for c in candidates() if not only or c.name in only]
    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        for clip in clips:
            clip.baseline = baseline_stats(clip, out, pool)
        for cand in chosen:
            for clip in clips:
                started = time.perf_counter()
                row = run_candidate(clip, cand, out, pool)
                results = [
                    r for r in results if (r["candidate"], r["clip"]) != (row.candidate, row.clip)
                ]
                results.append(asdict(row))
                results_path.write_text(json.dumps(results, indent=1), encoding="utf-8")
                print(
                    f"{cand.name:26s} {clip.stem}: median {row.bytes_median / 1000:8.1f} KB  "
                    f"err max {row.max_abs_error:3d}  means {row.dev_max['means']:.1e}  "
                    f"gains {row.dev_max['gains']:.1e}  bounds {row.dev_max['bounds']:.1e}  "
                    f"({time.perf_counter() - started:.0f} s)",
                    flush=True,
                )


# --- read cost ------------------------------------------------------------------------------------


def readcost_mode(only: list[str]) -> None:
    """Time the decode of one stored proxy per candidate (run in an EXCLUSIVE window)."""
    out = out_dir()
    clip = load_clip("GX011627")
    picks = [int(i) for i in np.linspace(0, clip.frames.shape[0] - 1, 25)]
    ffmpeg = str(find_tool("ffmpeg"))
    found: dict[str, dict[str, Any]] = {}
    for cand in candidates():
        if only and cand.name not in only:
            continue
        times: list[float] = []
        if cand.family == "stream":
            # A stream form is read one frame at a time by an FFmpeg process: write each frame as
            # a stand-alone one-frame stream and time the process that decodes it.
            for i in picks[:12]:
                one = out / "readcost-one.u8"
                one.write_bytes(np.asarray(clip.frames[i]).tobytes())
                one_stream = out / "readcost-one.mkv"
                subprocess.run(
                    [
                        ffmpeg,
                        "-v",
                        "error",
                        "-y",
                        "-f",
                        "rawvideo",
                        "-pix_fmt",
                        "rgb24",
                        "-s",
                        "960x540",
                        "-i",
                        str(one),
                        *cand.ffmpeg,
                        str(one_stream),
                    ],
                    check=True,
                )
                t0 = time.perf_counter()
                done = subprocess.run(
                    [
                        ffmpeg,
                        "-v",
                        "error",
                        "-i",
                        str(one_stream),
                        "-f",
                        "rawvideo",
                        "-pix_fmt",
                        "rgb24",
                        "-",
                    ],
                    capture_output=True,
                    check=True,
                )
                times.append(time.perf_counter() - t0)
                assert len(done.stdout) == 960 * 540 * 3
        else:
            assert cand.encode is not None and cand.decode is not None
            blobs = [cand.encode(np.asarray(clip.frames[i])) for i in picks]
            for blob in blobs:
                t0 = time.perf_counter()
                cand.decode(blob)
                times.append(time.perf_counter() - t0)
        found[cand.name] = {
            "median_ms": statistics.median(times) * 1000,
            "max_ms": max(times) * 1000,
            "reads": len(times),
        }
        print(
            f"{cand.name:26s} median {found[cand.name]['median_ms']:7.1f} ms  "
            f"max {found[cand.name]['max_ms']:7.1f} ms"
        )
    path = out / "readcost.json"
    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    previous.update(found)
    previous["_conditions"] = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "clip": "GX011627",
        "note": "median of the reads, per candidate",
    }
    path.write_text(json.dumps(previous, indent=1), encoding="utf-8")


def readcost_product_mode() -> None:
    """Time ``DiskProxyCache.proxy`` (file read, checksum, decode) per product codec.

    The 25 evenly spaced proxies of GX011627 are stored with each codec in a cache folder under
    the working folder, then each is read back ``READ_ROUNDS`` times; run in an EXCLUSIVE window.
    """
    from clearwater.cache import DEFLATE, JPEG_Q75_444, JPEG_Q80_420, DiskProxyCache
    from clearwater.interfaces.cache import CacheKey

    out = out_dir()
    clip = load_clip("GX011627")
    picks = [int(i) for i in np.linspace(0, clip.frames.shape[0] - 1, 25)]
    found: dict[str, dict[str, Any]] = {}
    for codec in (DEFLATE, JPEG_Q75_444, JPEG_Q80_420):
        folder = out / f"readcost-cache-{codec.name}"
        with DiskProxyCache(folder, codec=codec) as cache:
            cache.clear()
            key = CacheKey(1, 1, cache.cache_version)
            sizes = []
            for i in picks:
                cache.store_proxy(key, i, np.asarray(clip.frames[i]))
            entry = cache.lookup(key)
            assert entry is not None
            sizes.append(entry.size_bytes / len(picks))
            times: list[float] = []
            for _ in range(READ_ROUNDS):
                for i in picks:
                    t0 = time.perf_counter()
                    cache.proxy(key, i)
                    times.append(time.perf_counter() - t0)
            cache.clear()
        found[f"product-{codec.name}"] = {
            "median_ms": statistics.median(times) * 1000,
            "p95_ms": float(np.percentile(times, 95)) * 1000,
            "max_ms": max(times) * 1000,
            "reads": len(times),
            "bytes_per_frame": sizes[0],
        }
        row = found[f"product-{codec.name}"]
        print(
            f"{codec.name:14s} median {row['median_ms']:6.2f} ms  p95 {row['p95_ms']:6.2f} ms  "
            f"max {row['max_ms']:6.2f} ms  {row['bytes_per_frame'] / 1000:.1f} KB/frame"
        )
    path = out / "readcost.json"
    previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    previous.update(found)
    previous["_product_conditions"] = {
        "at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "clip": "GX011627",
        "frames": len(picks),
        "rounds": READ_ROUNDS,
        "note": "proxy(): read + CRC + decode, file in the OS cache",
    }
    path.write_text(json.dumps(previous, indent=1), encoding="utf-8")


# --- report ---------------------------------------------------------------------------------------


def report_mode() -> None:
    """Print the results as a markdown table, worse clip per column."""
    out = out_dir()
    results = json.loads((out / "results.json").read_text(encoding="utf-8"))
    cost_path = out / "readcost.json"
    cost = json.loads(cost_path.read_text(encoding="utf-8")) if cost_path.exists() else {}
    names = list(dict.fromkeys(r["candidate"] for r in results))
    print(
        "| candidate | median KB/frame (worst clip) | p95 KB | max KB | 60-min GB (median) "
        "| 60-min GB (p95) | fits 10 GB | max err | mean err | means | gains | bounds (value) "
        "| bounds (range) | vs 8-bit: means | gains | bounds (value) | bounds (range) "
        "| verdict (ruled criteria; original 1 % bounds shown for information) | read ms |"
    )
    print("|" + "---|" * 19)
    for name in names:
        rows = [r for r in results if r["candidate"] == name]
        median = max(r["bytes_median"] for r in rows)
        p95 = max(r["bytes_p95"] for r in rows)
        top = max(r["bytes_max"] for r in rows)
        gb_median = median * SIXTY_MINUTES_FRAMES / 1e9
        gb_p95 = p95 * SIXTY_MINUTES_FRAMES / 1e9
        dev = {k: max(r["dev_max"][k] for r in rows) for k in rows[0]["dev_max"]}
        dev8 = {k: max(r["dev8_max"][k] for r in rows) for k in rows[0]["dev8_max"]}
        ok_stats = (
            dev["means"] <= CRITERIA["means"]
            and dev["gains"] <= CRITERIA["gains"]
            and dev8["bounds_range"] <= RULED_BOUNDS_RANGE
        )
        original_bounds = dev["bounds"] <= CRITERIA["bounds"]
        fits = median * SIXTY_MINUTES_FRAMES <= BOUND_BYTES
        read = cost.get(name, {}).get("median_ms")
        print(
            f"| {name} | {median / 1000:.1f} | {p95 / 1000:.1f} | {top / 1000:.1f} "
            f"| {gb_median:.1f} | {gb_p95:.1f} "
            f"| {'yes' if fits else 'no'} | {max(r['max_abs_error'] for r in rows)} "
            f"| {max(r['mean_abs_error'] for r in rows):.3f} | {dev['means']:.1e} "
            f"| {dev['gains']:.1e} "
            f"| {dev['bounds']:.1e} | {dev['bounds_range']:.1e} "
            f"| {dev8['means']:.1e} | {dev8['gains']:.1e} | {dev8['bounds']:.1e} "
            f"| {dev8['bounds_range']:.1e} "
            f"| {'ruled criteria ok' if ok_stats else 'ruled criteria FAIL'}"
            f"{' + fits' if ok_stats and fits else ''}"
            f" (original 1 % bounds: {'met' if original_bounds else 'not met'}) "
            f"| {'' if read is None else f'{read:.1f}'} |"
        )


def meansize_mode() -> None:
    """Write the whole-clip sizes of the product JPEG codecs to ``meansize.txt`` (no timing)."""
    from clearwater.cache import JPEG_Q75_444, JPEG_Q80_420

    out = out_dir()
    lines = [
        "# product-codec (clearwater.cache.codec) payload sizes over whole clips; "
        f"written {time.strftime('%Y-%m-%d')} by tools/cache_store_test.py meansize "
        "(sizes only, no timing); 60min = 107892 frames"
    ]
    for codec in (JPEG_Q75_444, JPEG_Q80_420):
        for stem in CLIPS:
            clip = load_clip(stem)
            sizes = np.array(
                [
                    len(codec.encode(np.asarray(clip.frames[i])))
                    for i in range(clip.frames.shape[0])
                ],
                dtype=np.float64,
            )
            lines.append(
                f"{codec.name} {stem} frames={len(sizes)} mean={sizes.mean() / 1000:.1f}KB "
                f"median={np.median(sizes) / 1000:.1f}KB "
                f"p95={np.percentile(sizes, 95) / 1000:.1f}KB "
                f"max={sizes.max() / 1000:.1f}KB  "
                f"60min(mean)={sizes.mean() * SIXTY_MINUTES_FRAMES / 1e9:.1f}GB "
                f"60min(median)={np.median(sizes) * SIXTY_MINUTES_FRAMES / 1e9:.1f}GB"
            )
    (out / "meansize.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def signed_mode() -> None:
    """Write the signed change of the default proxy's N{} bounds range to ``signed-bounds.txt``.

    For every second statistics frame the range of the bounds measured on the decoded default
    proxy, and on the 8-bit proxy alone, is compared with the range measured on the float proxy
    (c3 ``Params()``, CPU): ``(range - float range) / float range``.
    """
    from clearwater.cache import round_trip

    out = out_dir()
    lines = [
        "# signed change of the N{} bounds RANGE (high-pass 0.5/99.5 percentile span) against the "
        "float proxy, c3 Params(), CPU, every 2nd statistics frame; written "
        f"{time.strftime('%Y-%m-%d')} by tools/cache_store_test.py signed"
    ]

    def summary(values: list[float]) -> str:
        a = np.asarray(values)
        return (
            f"min {a.min():+.3f} med {np.median(a):+.3f} max {a.max():+.3f}  "
            f"neg {int((a < 0).sum())}/{len(a)}"
        )

    for stem in CLIPS:
        clip = load_clip(stem)
        indices = clip.stat_indices[::2]
        plain: list[float] = []
        jpeg: list[float] = []
        for i in indices:
            frame = np.asarray(clip.frames[i])
            reference = clip.reference[i]["bounds"]
            span = float(reference[1] - reference[0])
            for target, picture in ((plain, frame), (jpeg, round_trip(frame))):
                bounds = frame_stats(picture.astype(np.float32) / 255.0)["bounds"]
                target.append((float(bounds[1] - bounds[0]) - span) / span)
        lines.append(f"{stem} {len(indices)} 8-bit only  range change: {summary(plain)}")
        lines.append(f"{stem} {len(indices)} jpeg q75    range change: {summary(jpeg)}")
    (out / "signed-bounds.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))


def main(argv: Sequence[str] | None = None) -> int:
    """Run one mode of the instrument."""
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0] if __doc__ else "")
    sub = parser.add_subparsers(dest="mode", required=True)
    p_prepare = sub.add_parser("prepare")
    p_prepare.add_argument("--stride", type=int, default=8)
    p_sizes = sub.add_parser("sizes")
    p_sizes.add_argument("--only", nargs="*", default=[])
    p_sizes.add_argument("--workers", type=int, default=4)
    p_read = sub.add_parser("readcost")
    p_read.add_argument("--only", nargs="*", default=[])
    sub.add_parser("readcost-product")
    sub.add_parser("meansize")
    sub.add_parser("signed")
    sub.add_parser("report")
    args = parser.parse_args(argv)
    if args.mode == "prepare":
        prepare(args.stride)
    elif args.mode == "sizes":
        sizes_mode(args.only, args.workers)
    elif args.mode == "readcost":
        readcost_mode(args.only)
    elif args.mode == "readcost-product":
        readcost_product_mode()
    elif args.mode == "meansize":
        meansize_mode()
    elif args.mode == "signed":
        signed_mode()
    else:
        report_mode()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
