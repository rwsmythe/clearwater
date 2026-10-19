"""Time sustained runs of the prototype pipeline and record their memory (WP1.2 A and B).

Usage::

    uv run python tools/prototype/bench.py --device {cpu,gpu} --method {ancuti2018,c3}
        --out DIR (--size {4k,5.3k,WxH} | --input CLIP) --frames N [--start-fraction F]
        [--proxy S ...] [--seed N] [--note TEXT] [--config FILE]
    uv run python tools/prototype/bench.py --mode {analysis,end-to-end,decode-only,passthrough}
        --input CLIP --device {cpu,gpu} --method M [--statistics FILE] [--hwaccel none|cuda]
        [--resident] [--frames N] [--out DIR] [--note TEXT] [--config FILE]

The instrument of WP1.2. In the default ``core`` mode it times
:func:`prototype.pipeline.correct` alone, ``N`` times in sequence on the chosen device,
and writes one JSON record, ``<out>/bench-<device>-<size>-<method>-<stamp>.json``, whose
path it prints. The frames are either ONE synthetic frame (``--size``,
:func:`synthetic_frame`; Part A; the record is labelled ``SYNTHETIC``) or REAL frames
(``--input``; Part B): ``CLIP`` is a footage stem found with
:func:`local_config.find_footage_file` or a path outside the footage folder
(:func:`prototype.clip.resolve_clip`); for a video, the ``N`` consecutive frames from the
first frame at or after ``--start-fraction`` (default 0.3) of the clip are decoded first
(:func:`prototype.clip.decode_frames`, which checks every frame's pts) and held as
integers, and frame ``i`` of the run is frame ``i`` of them; an image (8-bit through
Pillow, or a 16-bit PNG) is one frame used ``N`` times. Each frame is converted to float32
before its timer starts. The record is labelled ``REAL`` and its ``input`` entry names the
source, the frames' pts and the decode command.

The other modes time a WHOLE clip through :mod:`prototype.clip` (Part B claims 3 and 4)
with the memory and ambient readings below, and write
``<out>/bench-<mode>-<stem>-<method>-<stamp>.json`` under ``<working folder>/wp1.2b``
(``--out`` defaults to ``<working folder>/wp1.2b/bench`` and must lie inside it): ``analysis``
runs the analysis pass (:func:`prototype.clip.analyse`) and also writes its analysis
record, the statistics a render reads; ``end-to-end`` runs the export loop
(:func:`prototype.clip.export`) with ``--statistics`` (an analysis record of the same
clip, parameters and decode), then compares the output with the source
(``container_spike.compare``, after the timed bracket); ``decode-only`` and
``passthrough`` are the split's decode and encode passes. ``--frames`` limits these modes
to the first ``N`` frames.

Timing. Each frame's wall-clock time is ``time.perf_counter()`` around ``correct()`` on
the NumPy frame followed by ``synchronize()`` of the backend, so the time includes the
host-to-device copy of the input, every kernel, and the device-to-host copy of every array
of the result. The first frame (kernel compilation, pool growth) is discarded as warm-up
before the median and the 95th percentile; the drift is the median of the last ten frames
over the median of the first ten after the warm-up. On the GPU a second, supplementary
loop of ``N`` frames times the device-resident path a renderer would use: the input copied
to the device, ``correct()`` on the device array, and only the output copied back.

Memory. Peak RSS is the maximum of ``psutil`` samples taken by a thread every 50 ms during
the timed loop. On the GPU, CuPy's default memory pool is wrapped by a counting allocator
that records the pool's used bytes after every allocation (its high-water mark), and the
pool's reserved bytes are read after the timed loop (the pool's cache is emptied before the
loop and the pool never returns memory during it, so that is its own high-water mark).
``nvidia-smi --query-gpu=memory.used`` is read before the backend starts and the CUDA
runtime's device-wide used memory just after it starts (the CUDA context then exists);
both are read again after the timed loop, while the pool still holds its memory. The
``nvidia-smi`` per-process figure is recorded as the driver reports it (``[N/A]`` under
Windows' WDDM driver model). :func:`prototype.backend.memory_estimate_bytes` is recorded
beside them.

Ambient. The record also holds the power source, the Windows power scheme and power-mode
overlay (read only; ``None`` off Windows), and the card's clocks, temperature, power draw,
P-state and clock-limit reasons just before and just after the timed loop, outside it
(and, in the whole-clip modes, every :data:`GPU_SAMPLE_INTERVAL_S` during it). The
``ambient`` entry also holds the head commit of this tree and any tracked file changed in
it (:func:`head_record`), and the processes using at least :data:`STRAY_CPU_PERCENT` % of
one logical CPU just before and just after the timed loop (:func:`stray_processes`).

``--proxy S`` (repeatable) also computes the whole-frame statistics on the frame
downscaled to short side ``S`` and records them with their relative error against the
full-size ones (D60, D109). On the synthetic frame: the channel means, the white-balance
gains and the normalisation bounds, Pillow's BOX filter (Part A). On real frames: every
statistic of :func:`prototype.temporal.statistics_of`, on each frame, with the analysis
proxy's area mean (:func:`prototype.temporal.proxy`, a whole-factor block mean), the
relative error's mean and largest over the frames, and WP1.4's stability figure, the
relative step (:func:`relative_step`), of each statistic at each size.

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, on a bad
argument, an unusable device or an output that cannot be written.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, NoReturn

import numpy as np
import psutil
import scipy
from numpy.typing import NDArray
from PIL import Image as PILImage
from scipy import ndimage

if not __package__:
    # Script mode (``python tools/prototype/bench.py``): sys.path[0] is tools/prototype, so
    # put the tools directory first to make the ``prototype`` package importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_config import LocalConfigError, load_local_config
from lookcheck.frames import ExtractError, OutputRoots, read_png16
from prototype import clip, temporal
from prototype.backend import Backend, memory_estimate_bytes, select_backend
from prototype.params import METHODS, Params
from prototype.pipeline import (
    compensate_ancuti2018,
    compensate_c3,
    correct,
    normalisation_bounds,
    white_balance,
)

SIZES: dict[str, tuple[int, int]] = {"4k": (2160, 3840), "5.3k": (2988, 5312)}
"""Named sizes as ``(height, width)``: UHD 4K and the GoPro 16:9 5.3K mode."""

BUDGET_30FPS_S = 0.111
"""N6 per-frame budget at 30 fps, end to end (D106: about 3.3 min per min of footage)."""

BUDGET_60FPS_S = 0.056
"""N6 per-frame budget at 60 fps, end to end."""

RSS_SAMPLE_INTERVAL_S = 0.05
"""Interval of the peak-RSS sampling thread."""

GPU_SAMPLE_INTERVAL_S = 60.0
"""Interval of the card-state samples taken during a whole-clip mode."""

STRAY_CPU_PERCENT = 10.0
"""A process using at least this share of one logical CPU is listed by the stray check."""

START_FRACTION = 0.3
"""Real video frames are read from this fraction of the clip's duration on (Part B claim 2)."""

MODES = ("core", "analysis", "end-to-end", "decode-only", "passthrough")
"""``core`` times ``correct()`` alone; the others time a whole clip through ``clip``."""

IMAGE_SUFFIXES = frozenset({".png", ".jpg", ".jpeg", ".tif", ".tiff"})
"""File suffixes ``--input`` reads as a still image."""

_MIB = 1024 * 1024
_SIZE_PATTERN = re.compile(r"^([1-9][0-9]*)x([1-9][0-9]*)$")


class _UsageError(Exception):
    """A bad command-line argument or an unusable device; exit status 2."""


class _Parser(argparse.ArgumentParser):
    """An argument parser that raises :class:`_UsageError` instead of exiting."""

    def error(self, message: str) -> NoReturn:
        """Raise the parse error instead of printing usage and exiting.

        Args:
            message: The parser's error message.

        Raises:
            _UsageError: Always.
        """
        raise _UsageError(message)


def synthetic_frame(height: int, width: int, seed: int = 0) -> NDArray[np.float32]:
    """Build the seeded synthetic test frame: a blue-green cast over texture and noise.

    The frame is ``clip(base * (1 + 0.3 * texture) + noise, 0, 1)``, with ``x`` and ``y``
    running over [0, 1] across the frame:

    - ``base``, the cast: red ``0.05 + 0.15 x``, green ``0.35 + 0.35 y``, blue
      ``0.45 + 0.25 x y`` (weak red, strong green and blue, as at depth);
    - ``texture``, a band-limited pattern: uniform noise smoothed by a Gaussian of sigma
      0.004 of the short side and rescaled to [-1, 1], so the pattern scales with the frame;
    - ``noise``, per-pixel, per-channel Gaussian noise of standard deviation 0.01 (a sensor
      noise floor, which does not scale with the frame).

    Args:
        height: Frame height in pixels.
        width: Frame width in pixels.
        seed: Seed of the NumPy random generator.

    Returns:
        The frame, float32, shape ``(height, width, 3)``, values in [0, 1].
    """
    rng = np.random.default_rng(seed)
    y = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    x = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :]
    base = np.empty((height, width, 3), dtype=np.float32)
    base[..., 0] = 0.05 + 0.15 * x
    base[..., 1] = 0.35 + 0.35 * y
    base[..., 2] = 0.45 + 0.25 * x * y
    field: NDArray[np.float32] = ndimage.gaussian_filter(
        rng.random((height, width), dtype=np.float32), 0.004 * min(height, width)
    )
    low, high = float(field.min()), float(field.max())
    texture = np.asarray(2.0 * (field - low) / max(high - low, 1e-12) - 1.0, dtype=np.float32)
    frame = base * (1.0 + 0.3 * texture[..., None])
    frame += rng.normal(0.0, 0.01, frame.shape).astype(np.float32)
    return np.clip(frame, 0.0, 1.0).astype(np.float32, copy=False)


def proxy_frame(frame: NDArray[np.float32], short_side: int) -> NDArray[np.float32]:
    """Downscale a frame to the given short side by area averaging (Pillow's BOX filter).

    Args:
        frame: The full-size frame, float32, ``(H, W, 3)``.
        short_side: The proxy's short side in pixels; the aspect ratio is kept (the long
            side is rounded to the nearest pixel).

    Returns:
        The proxy, float32, ``(h, w, 3)``; the frame itself when ``short_side`` is its own.
    """
    height, width = frame.shape[0], frame.shape[1]
    if short_side == min(height, width):
        return frame
    scale = short_side / min(height, width)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    channels = [
        np.asarray(
            PILImage.fromarray(np.ascontiguousarray(frame[..., c])).resize(
                size, PILImage.Resampling.BOX
            ),
            dtype=np.float32,
        )
        for c in range(3)
    ]
    return np.clip(np.stack(channels, axis=2), 0.0, 1.0).astype(np.float32, copy=False)


def frame_statistics(
    frame: NDArray[np.float32], params: Params, backend: Backend
) -> dict[str, Any]:
    """Compute the pipeline's whole-frame statistics of one frame on ``backend``.

    Args:
        frame: The frame, float32, ``(H, W, 3)``, on the host.
        params: The parameter set (its method selects the compensation).
        backend: Where to compute.

    Returns:
        The input channel means, the channel means after compensation (the white
        balance's input), the applied white-balance gains and the normalisation bounds.
    """
    work = backend.to_device(frame)
    compensate = compensate_c3 if params.method == "c3" else compensate_ancuti2018
    compensated, compensation = compensate(work, params)
    balanced, balance = white_balance(compensated, params)
    low, high = normalisation_bounds(balanced, params)
    return {
        "input_means": list(compensation.channel_means),
        "compensated_means": list(balance.channel_means),
        "white_balance_gains": list(balance.applied_gains),
        "normalisation_bounds": [low, high],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark and write its JSON record.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2 on a bad argument, an unusable device, an unreadable input, a
        failed whole-clip pass or an unwritable output, with a one-line error on standard
        error.
    """
    try:
        args = _parse(argv)
        if args.mode != "core":
            return _clip_mode(args)
        if (args.size is None) == (args.input is None):
            raise _UsageError("give exactly one of --size and --input")
        if args.out is None:
            raise _UsageError("--out is required in the core mode")
        if args.frames is None or args.frames < 1:
            raise _UsageError(f"--frames must be at least 1, got {args.frames}")
        if not 0.0 <= args.start_fraction < 1.0:
            raise _UsageError(f"--start-fraction must lie in [0, 1), got {args.start_fraction}")
        real: RealFrames | None = None
        roots: OutputRoots | None = None
        if args.input is not None:
            # Real-frame records are Part B outputs: they go under <working folder>/wp1.2b.
            roots = clip.work_roots(args.config)
            roots.check(args.out)
            real = load_real_frames(args.input, args.frames, args.start_fraction, args.config)
            height, width = real.shape[0], real.shape[1]
        else:
            height, width = _parse_size(args.size)
        for side in args.proxy:
            if not 1 <= side <= min(height, width):
                raise _UsageError(
                    f"--proxy must lie in [1, {min(height, width)}] for this size, got {side}"
                )
            factor, remainder = divmod(min(height, width), side)
            if real is not None and (remainder or height % factor or width % factor):
                raise _UsageError(f"--proxy {side} is not a whole-factor area mean of this size")
        ambient_gpu = _nvidia_smi_gpu()
        cuda_before = None
        backend = select_backend(args.device)
    except (_UsageError, RuntimeError, clip.ClipError, ExtractError, LocalConfigError) as exc:
        print(f"error: {_one_line(exc)}", file=sys.stderr)
        return 2

    params = Params(method=args.method)
    tracker = _PoolTracker(backend) if backend.name == "gpu" else None
    if tracker is not None:
        cuda_before = tracker.cuda_used_bytes()
    frame = synthetic_frame(height, width, args.seed) if real is None else None
    process = psutil.Process()
    rss_baseline = int(process.memory_info().rss)

    sampler = _PeakRssSampler(process)
    head = head_record()
    stray_before = stray_processes()
    gpu_start = _gpu_state()
    window_start = _local_now()
    sampler.start()
    try:
        if real is None:
            assert frame is not None
            times = _timed_loop(frame, params, backend, args.frames)
        else:
            times = _timed_real_loop(real, params, backend, args.frames)
        window_end = _local_now()
        gpu_end = _gpu_state()
    finally:
        sampler.stop()
        if tracker is not None:
            tracker.close()
    stray_after = stray_processes()

    memory = _memory_record(rss_baseline, sampler.peak, process)
    if tracker is not None:
        memory |= tracker.record(ambient_gpu, cuda_before)
    resident = None
    if backend.name == "gpu":
        # The supplementary loop's own window; the memory figures above are the main loop's.
        resident_window: dict[str, Any] = {"start_local": _local_now()}
        resident_window["gpu_state_start"] = _gpu_state()
        resident_times = (
            _resident_loop(frame, params, backend, args.frames)
            if frame is not None
            else _resident_real_loop(real, params, backend, args.frames)
            if real is not None
            else []
        )
        resident_window |= {"end_local": _local_now(), "gpu_state_end": _gpu_state()}
        resident = _timing_record(resident_times) | {"window": resident_window}
    shape = (height, width, 3)
    estimate = memory_estimate_bytes(shape, params)
    if frame is not None:
        proxy = _proxy_record(frame, params, backend, args.proxy)
    elif real is not None:
        proxy = _real_proxy_record(real, params, backend, args.proxy)
    record: dict[str, Any] = {
        "label": "SYNTHETIC" if real is None else "REAL",
        "tool": "tools/prototype/bench.py",
        "created": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "device": args.device,
        "backend": backend.name,
        "size": args.size if real is None else f"{width}x{height}",
        "shape": list(shape),
        "method": args.method,
        "frames": args.frames,
        "seed": args.seed if real is None else None,
        "generator": (
            "synthetic_frame(): blue-green cast, band-limited texture, pixel noise"
            if real is None
            else None
        ),
        "params": dataclasses.asdict(params),
        "timing": _timing_record(times),
        "device_resident": resident,
        "memory": memory,
        "estimate": _estimate_record(estimate, memory),
        "proxy": proxy,
        "versions": _versions(backend),
        "machine": _machine(ambient_gpu),
        "ambient": _ambient(ambient_gpu, args.note)
        | {
            "gpu_state_loop_start": gpu_start,
            "gpu_state_loop_end": gpu_end,
            "stray_processes_before": stray_before,
            "stray_processes_after": stray_after,
            "window_start_local": window_start,
            "window_end_local": window_end,
            "head": head,
        },
    }
    label = args.size
    if real is not None:
        record["input"] = real.record
        label = real.stem
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = args.out / f"bench-{backend.name}-{label}-{args.method}-{stamp}.json"
    try:
        if roots is not None:
            roots.mkdir(args.out)
            roots.write_text(path, json.dumps(record, indent=2) + "\n")
        else:
            _refuse_footage(args.out, args.config)
            args.out.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    except (OSError, _UsageError, ExtractError) as exc:
        print(f"error: cannot write to {args.out}: {_one_line(exc)}", file=sys.stderr)
        return 2
    print(path)
    return 0


def _local_now() -> str:
    """The local time now, ISO 8601 with its offset, to the second."""
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the command line.

    Raises:
        _UsageError: A missing or malformed argument.
    """
    parser = _Parser(description="Time the prototype pipeline (WP1.2 Parts A and B).")
    parser.add_argument("--mode", choices=MODES, default="core")
    parser.add_argument("--device", choices=("cpu", "gpu"), required=True)
    parser.add_argument("--size", help="4k, 5.3k or WIDTHxHEIGHT (synthetic frame)")
    parser.add_argument("--input", help="footage stem, or a video or image path outside it")
    parser.add_argument("--frames", type=int, help="frames in the timed run (a limit elsewhere)")
    parser.add_argument("--method", choices=METHODS, required=True)
    parser.add_argument("--out", type=Path, help="folder for the JSON record")
    parser.add_argument(
        "--proxy", type=int, action="append", default=[], metavar="S", help="proxy short side"
    )
    parser.add_argument("--seed", type=int, default=0, help="seed of the synthetic frame")
    parser.add_argument(
        "--start-fraction", type=float, default=START_FRACTION, help="where real frames start"
    )
    parser.add_argument("--statistics", type=Path, help="analysis record (end-to-end mode)")
    parser.add_argument("--hwaccel", choices=clip.HWACCELS, default="none")
    parser.add_argument("--resident", action="store_true", help="device-resident export core")
    parser.add_argument("--config", type=Path, help="local configuration file to read")
    parser.add_argument("--note", default="", help="free text stored with the ambient record")
    return parser.parse_args(argv)


def _refuse_footage(folder: Path, config_path: Path | None) -> None:
    """Refuse a core-mode output folder inside the configured footage folder (if any).

    Raises:
        _UsageError: The folder lies inside (or is) the footage folder.
    """
    try:
        footage = load_local_config(config_path).footage_path.resolve()
    except LocalConfigError:
        return  # no configuration: no footage folder to protect
    resolved = folder.resolve()
    if resolved == footage or footage in resolved.parents:
        raise _UsageError(f"{folder} lies inside the footage folder")


# --- real frames ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class RealFrames:
    """Real frames held for a core-mode run, as integers (or float32 for a 16-bit PNG).

    Attributes:
        stem: The source's file stem (names the record).
        frames: The frames, ``(H, W, 3)``; ``uint8``, ``uint16`` or float32.
        bit_depth: 8 or 10 for video frames (:func:`prototype.clip.to_float`); ``None`` for
            an image (``uint8`` is divided by 255; float32 is used as it is).
        shape: ``(H, W, 3)``.
        record: The record's ``input`` entry.
    """

    stem: str
    frames: list[NDArray[Any]]
    bit_depth: int | None
    shape: tuple[int, int, int]
    record: dict[str, Any]

    def image(self, index: int) -> NDArray[np.float32]:
        """Return frame ``index`` (modulo the number held) as float32 in [0, 1].

        Args:
            index: The run's frame number.

        Returns:
            A new float32 array.
        """
        frame = self.frames[index % len(self.frames)]
        if frame.dtype == np.float32:
            return frame.copy()
        out: NDArray[np.float32] = clip.to_float(frame, np, self.bit_depth or 8)
        return out


def load_real_frames(
    name: str, count: int, start_fraction: float, config_path: Path | None = None
) -> RealFrames:
    """Read the real frames of a core-mode run (``--input``).

    A video: the ``count`` consecutive frames from the first whose pts is at or after
    ``start_fraction`` of the clip's length, decoded with their pts checked
    (:func:`prototype.clip.decode_frames`). An image: one frame.

    Args:
        name: A footage stem or a path outside the footage folder.
        count: Frames of a video to read.
        start_fraction: Where in the clip they start, in [0, 1).
        config_path: The local configuration file; ``None`` for the default.

    Returns:
        The frames and their record.

    Raises:
        local_config.LocalConfigError: The configuration does not load, or the stem matches
            no file or several.
        prototype.clip.ClipError: The video cannot be probed or decoded, or has fewer frames
            after the start than ``count``.
        _UsageError: The image cannot be read.
    """
    footage = load_local_config(config_path).footage_path
    path = clip.resolve_clip(name, footage)
    if path.suffix.lower() in IMAGE_SUFFIXES:
        return _image_frames(path)
    source = clip.open_source(path)
    start = Fraction(start_fraction).limit_denominator(1_000_000) * source.footage_seconds
    first = next(
        (i for i, ticks in enumerate(source.pts_ticks) if ticks * source.info.time_base >= start),
        source.frame_count,
    )
    frames, command = clip.decode_frames(source, first, count)
    ticks = list(source.pts_ticks[first : first + count])
    held = sum(frame.nbytes for frame in frames) / _MIB
    return RealFrames(
        stem=path.stem,
        frames=frames,
        bit_depth=source.bit_depth,
        shape=(source.info.height, source.info.width, 3),
        record={
            "kind": "video",
            "source": source.identity(),
            "start_fraction": start_fraction,
            "first_index": first,
            "pts_ticks": ticks,
            "pts_seconds_first": float(ticks[0] * source.info.time_base),
            "pts_seconds_last": float(ticks[-1] * source.info.time_base),
            "decode_command": command,
            "frames_held_mb": held,
            "conversion": "integer / (2**bits - 1) as float32 (clip.to_float), before the timer",
        },
    )


def _image_frames(path: Path) -> RealFrames:
    """One still image as a :class:`RealFrames`: a 16-bit PNG, else 8-bit RGB via Pillow."""
    data = path.read_bytes()
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n" and len(data) > 24 and data[24] == 16:
            frame: NDArray[Any] = read_png16(path)
            kind = "16-bit PNG (lookcheck.frames.read_png16)"
        else:
            with PILImage.open(path) as opened:
                frame = np.asarray(opened.convert("RGB"), dtype=np.uint8)
                kind = f"Pillow {opened.format} {opened.mode} -> 8-bit RGB"
    except (OSError, ValueError, ExtractError) as exc:
        raise _UsageError(f"cannot read the image {path.name}: {_one_line(exc)}") from None
    height, width = frame.shape[0], frame.shape[1]
    return RealFrames(
        stem=path.stem,
        frames=[frame],
        bit_depth=None,
        shape=(height, width, 3),
        record={
            "kind": "image",
            "path": str(path),
            "size_bytes": len(data),
            "reader": kind,
            "frames_held_mb": frame.nbytes / _MIB,
        },
    )


def _timed_real_loop(
    real: RealFrames, params: Params, backend: Backend, frames: int
) -> list[float]:
    """Run ``correct()`` on real frame ``i`` for ``i < frames``; return each frame's seconds.

    Each frame is converted to float32 before its timer starts.
    """
    times: list[float] = []
    for index in range(frames):
        image = real.image(index)
        start = time.perf_counter()
        result = correct(image, params, backend)
        backend.synchronize()
        times.append(time.perf_counter() - start)
        del result, image
    return times


def _resident_real_loop(
    real: RealFrames, params: Params, backend: Backend, frames: int
) -> list[float]:
    """The device-resident loop (:func:`_resident_loop`) over the real frames."""
    times: list[float] = []
    for index in range(frames):
        image = real.image(index)
        start = time.perf_counter()
        result = correct(backend.to_device(image), params)
        output = backend.to_host(result.output)
        backend.synchronize()
        times.append(time.perf_counter() - start)
        del result, output, image
    return times


def relative_step(values: NDArray[np.float64]) -> float | None:
    """WP1.4's stability figure: the mean absolute frame-to-frame change over the mean value.

    ``mean(|diff(values)|) / mean(|values|)``, as ``_relative_step`` of
    ``tools/statistics_experiments.py``.

    Args:
        values: One value per frame, in order.

    Returns:
        The figure; ``None`` for fewer than two values or a zero mean.
    """
    if len(values) < 2 or not np.abs(values).mean():
        return None
    return float(np.abs(np.diff(values)).mean() / np.abs(values).mean())


def _real_proxy_record(
    real: RealFrames, params: Params, backend: Backend, sides: list[int]
) -> list[dict[str, Any]]:
    """Every whole-frame statistic on each real frame at each proxy size against full size."""
    if not sides:
        return []
    full_side = min(real.shape[0], real.shape[1])
    order = [full_side, *sorted(set(sides) - {full_side}, reverse=True)]
    measured: dict[int, list[dict[str, float]]] = {side: [] for side in order}
    for index in range(len(real.frames)):
        image = real.image(index)
        for side in order:
            proxy = image if side == full_side else temporal.proxy(image, side)
            measured[side].append(temporal.flatten(temporal.statistics_of(proxy, params, backend)))
    full = measured[full_side]
    names = list(full[0])
    records = []
    for side in order:
        rows = measured[side]
        factor = full_side // side
        errors = {
            name: [
                _relative_error(row[name], ref[name]) for row, ref in zip(rows, full, strict=True)
            ]
            for name in names
        }
        records.append(
            {
                "short_side": side,
                "shape": [real.shape[0] // factor, real.shape[1] // factor, 3],
                "frames": len(rows),
                "statistics": {name: [row[name] for row in rows] for name in names},
                "relative_error": {name: _error_summary(values) for name, values in errors.items()},
                "relative_step": {
                    name: relative_step(np.array([row[name] for row in rows])) for name in names
                },
            }
        )
    return records


def _error_summary(values: list[float | None]) -> dict[str, float | None]:
    """Mean and largest of the defined relative errors."""
    defined = [value for value in values if value is not None]
    if not defined:
        return {"mean": None, "max": None}
    return {"mean": float(np.mean(defined)), "max": float(np.max(defined))}


# --- whole-clip modes ----------------------------------------------------------------------------


def _clip_mode(args: argparse.Namespace) -> int:
    """Run one whole-clip mode (analysis, end-to-end, decode-only, passthrough) and record it.

    The memory samplers, the card-state samples and the stray-process checks bracket the
    pass; the container comparison of an output runs after the pass has ended.

    Raises:
        _UsageError: A missing or contradictory argument (caught by :func:`main`).
    """
    if args.input is None:
        raise _UsageError(f"--mode {args.mode} needs --input")
    if args.size is not None or args.proxy:
        raise _UsageError("--size and --proxy belong to the core mode")
    if args.frames is not None and args.frames < temporal.MIN_FRAMES:
        raise _UsageError(f"--frames must be at least {temporal.MIN_FRAMES} in a whole-clip mode")
    if (args.mode == "end-to-end") != (args.statistics is not None):
        raise _UsageError("--statistics is required by, and only by, the end-to-end mode")
    if args.resident and args.mode != "end-to-end":
        raise _UsageError("--resident belongs to the end-to-end mode")
    try:
        config = load_local_config(args.config)
        roots = OutputRoots(
            allowed=config.working_path / clip.WORK_SUBDIR, footage=config.footage_path
        )
        source = clip.open_source(clip.resolve_clip(args.input, roots.footage))
        params = Params(method=args.method)
        statistics = None
        frame_means: list[list[float]] | None = None
        if args.mode == "end-to-end":
            analysis = json.loads(args.statistics.read_text(encoding="utf-8"))
            clip.check_statistics_record(analysis, source, params, args.hwaccel, args.frames)
            statistics = clip.per_frame_statistics(analysis)
            frame_means = analysis["frame_means"]
        stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        base = f"{source.path.stem}-{args.mode}-{args.method}-{stamp}"
        folder = (roots.allowed / "bench" if args.out is None else args.out) / base
        record_path, decode_log, encode_log, output, analysis_path = clip.output_paths(
            roots,
            folder,
            [
                f"bench-{base}.json",
                "decode.log",
                "encode.log",
                f"{source.path.stem}_corrected.mp4",
                f"{source.path.stem}-{args.method}-{args.hwaccel}-analysis.json",
            ],
        )
        ambient_gpu = _nvidia_smi_gpu()
        backend = select_backend(args.device)
    except (RuntimeError, clip.ClipError, ExtractError, LocalConfigError, OSError) as exc:
        print(f"error: {_one_line(exc)}", file=sys.stderr)
        return 2

    tracker = _PoolTracker(backend) if backend.name == "gpu" else None
    cuda_before = None if tracker is None else tracker.cuda_used_bytes()
    process = psutil.Process()
    rss_baseline = int(process.memory_info().rss)
    sampler, card = _PeakRssSampler(process), _GpuSampler()
    head = head_record()
    stray_before = stray_processes()
    gpu_start = _gpu_state()
    window_start = _local_now()
    sampler.start()
    card.start()
    result: clip.Export | None = None
    done: clip.Analysis | None = None
    try:
        if args.mode == "analysis":
            done = clip.analyse(
                source, params, backend, decode_log, args.hwaccel, frames=args.frames
            )
        elif args.mode == "end-to-end":
            result = clip.export(
                source,
                output,
                params,
                statistics,
                backend,
                (decode_log, encode_log),
                frame_means,
                args.hwaccel,
                args.resident,
                args.frames,
            )
        elif args.mode == "passthrough":
            logs = (decode_log, encode_log)
            result = clip.passthrough(source, output, logs, args.hwaccel, args.frames)
        else:
            result = clip.decode_only(source, decode_log, args.hwaccel, args.frames)
        gpu_end = _gpu_state()
    except (clip.ClipError, OSError) as exc:
        print(f"error: {_one_line(exc)}", file=sys.stderr)
        return 2
    finally:
        sampler.stop()
        card.stop()
        if tracker is not None:
            tracker.close()
    window_end = _local_now()
    stray_after = stray_processes()
    memory = _memory_record(rss_baseline, sampler.peak, process)
    if tracker is not None:
        memory |= tracker.record(ambient_gpu, cuda_before)
    timing = done.timing if done is not None else result.timing if result is not None else None
    assert timing is not None
    footage = Fraction(timing.frames) / source.info.frame_rate
    shape = (source.info.height, source.info.width, 3)
    if args.mode == "analysis":
        factor = min(shape[0], shape[1]) // temporal.PROXY_SHORT_SIDE
        shape = (shape[0] // factor, shape[1] // factor, 3)
    record: dict[str, Any] = {
        "label": "REAL",
        "tool": "tools/prototype/bench.py",
        "mode": args.mode,
        "created": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "window": {"start_local": window_start, "end_local": window_end},
        "device": args.device,
        "backend": backend.name,
        "method": args.method,
        "params": dataclasses.asdict(params),
        "source": source.identity(),
        "frames": timing.frames,
        "frames_limit": args.frames,
        "hwaccel": args.hwaccel,
        "resident": args.resident,
        "statistics": None if args.statistics is None else str(args.statistics),
        "timing": timing.record(footage),
        "n6": clip.n6_record(timing, source),
        "memory": memory,
        "estimate": _estimate_record(memory_estimate_bytes(shape, params), memory)
        | {"shape": list(shape)},
        "versions": _versions(backend),
        "machine": _machine(ambient_gpu),
        "ambient": _ambient(ambient_gpu, args.note)
        | {
            "gpu_state_loop_start": gpu_start,
            "gpu_state_loop_end": gpu_end,
            "gpu_state_samples": card.samples,
            "stray_processes_before": stray_before,
            "stray_processes_after": stray_after,
            "head": head,
        },
    }
    try:
        if done is not None:
            document = clip.analysis_record(source, params, done, args.hwaccel, clip.SMOOTHER)
            roots.write_text(analysis_path, json.dumps(document) + "\n")
            record["analysis_record"] = str(analysis_path)
            record["analysis"] = {
                key: document[key]
                for key in ("smoother", "peak_proxies_held", "measure_s_per_stage", "smooth_s")
            }
        if result is not None:
            run = clip.export_record(source, result, args.statistics, None)
            run.pop("timing")  # the same readings as record["timing"]
            record["run"] = run
            if result.encode_command is not None:
                record["output"] = str(output)
                record["output_bytes"] = output.stat().st_size
                record["compare"] = clip.compare_output(source.path, output, folder, roots)
        roots.write_text(record_path, json.dumps(record, indent=1) + "\n")
    except (OSError, clip.ClipError, ExtractError) as exc:
        print(f"error: {_one_line(exc)}", file=sys.stderr)
        return 2
    print(record_path)
    return 0


def _parse_size(text: str) -> tuple[int, int]:
    """Return ``(height, width)`` for a named size or ``WIDTHxHEIGHT``.

    Raises:
        _UsageError: The size is neither.
    """
    if text in SIZES:
        return SIZES[text]
    match = _SIZE_PATTERN.match(text)
    if match is None:
        raise _UsageError(f"--size must be 4k, 5.3k or WIDTHxHEIGHT, got {text!r}")
    return int(match.group(2)), int(match.group(1))


def _timed_loop(
    frame: NDArray[np.float32], params: Params, backend: Backend, frames: int
) -> list[float]:
    """Run ``correct()`` on the host frame ``frames`` times; return each frame's seconds."""
    times: list[float] = []
    for _ in range(frames):
        start = time.perf_counter()
        result = correct(frame, params, backend)
        backend.synchronize()
        times.append(time.perf_counter() - start)
        del result
    return times


def _resident_loop(
    frame: NDArray[np.float32], params: Params, backend: Backend, frames: int
) -> list[float]:
    """Time the device-resident path: input to the device, output alone back to the host."""
    times: list[float] = []
    for _ in range(frames):
        start = time.perf_counter()
        result = correct(backend.to_device(frame), params)
        output = backend.to_host(result.output)
        backend.synchronize()
        times.append(time.perf_counter() - start)
        del result, output
    return times


def _timing_record(times: list[float]) -> dict[str, Any]:
    """Summarise per-frame times: all of them, then statistics without the warm-up frame."""
    steady = times[1:]
    record: dict[str, Any] = {
        "method": "perf_counter() around correct() and synchronize(); first frame is warm-up",
        "per_frame_s": times,
        "warmup_discarded": 1,
        "median_s": None,
        "p95_s": None,
        "first10_median_s": None,
        "last10_median_s": None,
        "drift": None,
        "budget_share_30fps": None,
        "budget_share_60fps": None,
    }
    if not steady:
        return record
    median = float(np.median(steady))
    first = float(np.median(steady[:10]))
    last = float(np.median(steady[-10:]))
    record |= {
        "median_s": median,
        "p95_s": float(np.percentile(steady, 95.0, method="linear")),
        "first10_median_s": first,
        "last10_median_s": last,
        "drift": last / first - 1.0,
        "budget_share_30fps": median / BUDGET_30FPS_S,
        "budget_share_60fps": median / BUDGET_60FPS_S,
    }
    return record


def _memory_record(rss_baseline: int, rss_peak: int, process: Any) -> dict[str, Any]:
    """The host memory figures, in MiB."""
    info = process.memory_info()
    peak_wset = getattr(info, "peak_wset", None)  # reported by psutil on some systems only
    return {
        "unit": "MiB",
        "rss_sampling": f"psutil RSS, thread sampling every {RSS_SAMPLE_INTERVAL_S * 1000:.0f} ms",
        "rss_baseline_mb": rss_baseline / _MIB,
        "rss_peak_mb": rss_peak / _MIB,
        "os_peak_working_set_mb": None if peak_wset is None else int(peak_wset) / _MIB,
    }


def _estimate_record(estimate: int, memory: dict[str, Any]) -> dict[str, Any]:
    """The working-set estimate and its ratio to each measured peak."""
    estimate_mb = estimate / _MIB
    record: dict[str, Any] = {
        "bytes": estimate,
        "mb": estimate_mb,
        "ratio_to_rss_peak": estimate_mb / memory["rss_peak_mb"],
        "ratio_to_gpu_pool_reserved": None,
        "ratio_to_gpu_pool_peak_used": None,
    }
    if memory.get("gpu_pool_reserved_mb"):
        record["ratio_to_gpu_pool_reserved"] = estimate_mb / memory["gpu_pool_reserved_mb"]
        record["ratio_to_gpu_pool_peak_used"] = estimate_mb / memory["gpu_pool_peak_used_mb"]
    return record


def _proxy_record(
    frame: NDArray[np.float32], params: Params, backend: Backend, sides: list[int]
) -> list[dict[str, Any]]:
    """The whole-frame statistics at each proxy short side against the full-size ones."""
    if not sides:
        return []
    full_side = min(frame.shape[0], frame.shape[1])
    full = frame_statistics(frame, params, backend)
    records = []
    for side in [full_side, *sorted(set(sides) - {full_side}, reverse=True)]:
        proxy = proxy_frame(frame, side)
        stats = full if side == full_side else frame_statistics(proxy, params, backend)
        errors = {
            key: [_relative_error(p, f) for p, f in zip(stats[key], full[key], strict=True)]
            for key in full
        }
        records.append(
            {"short_side": side, "shape": list(proxy.shape), **stats, "relative_error": errors}
        )
    return records


def _relative_error(value: float, reference: float) -> float | None:
    """``|value - reference| / |reference|``; ``None`` for a zero reference."""
    if reference == 0.0:
        return None
    return abs(value - reference) / abs(reference)


def _versions(backend: Backend) -> dict[str, Any]:
    """Library and driver versions."""
    versions: dict[str, Any] = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "cupy": None,
        "cuda_runtime": None,
        "cuda_driver_api": None,
    }
    if backend.name == "gpu":
        runtime = backend.xp.cuda.runtime
        versions |= {
            "cupy": backend.xp.__version__,
            "cuda_runtime": _cuda_version(int(runtime.runtimeGetVersion())),
            "cuda_driver_api": _cuda_version(int(runtime.driverGetVersion())),
        }
    return versions


def _machine(gpu: dict[str, str] | None) -> dict[str, Any]:
    """The machine: operating system, processor, memory and graphics card."""
    return {
        "platform": platform.platform(),
        "processor": _cpu_brand(),
        "logical_cpus": os.cpu_count(),
        "ram_total_mb": int(psutil.virtual_memory().total) / _MIB,
        "gpu_name": None if gpu is None else gpu.get("name"),
        "gpu_memory_total_mb": None if gpu is None else _float(gpu.get("memory.total")),
        "nvidia_driver": None if gpu is None else gpu.get("driver_version"),
    }


def _ambient(gpu: dict[str, str] | None, note: str) -> dict[str, Any]:
    """The conditions of the run: graphics memory in use, power source and plan, a note."""
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    return {
        "nvidia_smi_used_before_mb": None if gpu is None else _float(gpu.get("memory.used")),
        "power_plugged": None if battery is None else bool(battery.power_plugged),
        "battery_percent": None if battery is None else float(battery.percent),
        **_windows_power(),
        "note": note,
    }


def _gpu_state() -> dict[str, str] | None:
    """The card's clocks, temperature, power draw, P-state and clock-limit reasons now.

    Read with ``nvidia-smi`` (outside the timed region); ``None`` when it cannot run. The
    reasons are ``clocks_event_reasons.active``, a bit mask (``0x...01`` = idle,
    ``0x...04`` = power cap, ``0x...20`` / ``0x...40`` = thermal slowdown).
    """
    fields = (
        "clocks.gr",
        "clocks.sm",
        "clocks.mem",
        "temperature.gpu",
        "power.draw",
        "pstate",
        "clocks_event_reasons.active",
    )
    lines = _nvidia_smi([f"--query-gpu={','.join(fields)}", "--format=csv,noheader,nounits"])
    if not lines:
        return None
    values = [value.strip() for value in lines[0].split(",")]
    if len(values) != len(fields):
        return None
    return dict(zip(fields, values, strict=True))


# The overlay GUIDs of the Windows 11 power-mode slider; any other is recorded as "unknown".
_OVERLAY_NAMES = {
    "961cc777-2547-4f9d-8174-7d86181b8a7a": "Best power efficiency",
    "00000000-0000-0000-0000-000000000000": "Balanced",
    "ded574b5-45a0-4f42-8737-46345c09c238": "Best performance",
}


def _windows_power() -> dict[str, Any]:
    """The Windows power plan (scheme) and power-mode overlay in effect, read only.

    Windows 11 applies a power-mode overlay ("Best performance" and so on, the Settings
    slider) on top of the power scheme that ``powercfg /getactivescheme`` reports; both
    are read through ``powrprof`` (``PowerGetActiveScheme``,
    ``PowerGetEffectiveOverlayScheme``) and nothing is changed. Elsewhere, and if a call
    fails, the values are ``None``: this instrument reading is Windows-only by its nature.
    """
    record: dict[str, Any] = {
        "power_scheme": None,
        "power_overlay": None,
        "power_overlay_name": None,
    }
    if sys.platform != "win32":
        return record
    import ctypes
    import uuid

    try:
        powrprof = ctypes.WinDLL("powrprof")
        scheme = ctypes.c_void_p()
        if powrprof.PowerGetActiveScheme(None, ctypes.byref(scheme)) == 0 and scheme.value:
            record["power_scheme"] = str(uuid.UUID(bytes_le=ctypes.string_at(scheme, 16)))
            ctypes.windll.kernel32.LocalFree(scheme)
        overlay = (ctypes.c_ubyte * 16)()
        if powrprof.PowerGetEffectiveOverlayScheme(ctypes.byref(overlay)) == 0:
            guid = str(uuid.UUID(bytes_le=bytes(overlay)))
            record["power_overlay"] = guid
            record["power_overlay_name"] = _OVERLAY_NAMES.get(guid, "unknown")
    except (OSError, AttributeError):  # an older Windows without the overlay call
        pass
    return record


class _PeakRssSampler:
    """A thread that samples the process's RSS every :data:`RSS_SAMPLE_INTERVAL_S`."""

    def __init__(self, process: Any) -> None:
        """Prepare the sampler; :meth:`start` begins sampling."""
        self._process = process
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.peak = int(process.memory_info().rss)

    def start(self) -> None:
        """Start sampling."""
        self._thread.start()

    def stop(self) -> None:
        """Stop sampling, after one last sample."""
        self._stop.set()
        self._thread.join()
        self._sample()

    def _run(self) -> None:
        """Sample until :meth:`stop` is called."""
        while not self._stop.wait(RSS_SAMPLE_INTERVAL_S):
            self._sample()

    def _sample(self) -> None:
        """Take one RSS sample and keep the maximum."""
        self.peak = max(self.peak, int(self._process.memory_info().rss))


class _GpuSampler:
    """A thread that reads the card's state (:func:`_gpu_state`) at a fixed interval.

    Each sample is the state with ``seconds``, the time since :meth:`start`; the interval
    is :data:`GPU_SAMPLE_INTERVAL_S` by default.
    """

    def __init__(self, interval_s: float = GPU_SAMPLE_INTERVAL_S) -> None:
        """Prepare the sampler; :meth:`start` begins sampling."""
        self._interval = interval_s
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._started = 0.0
        self.samples: list[dict[str, Any]] = []

    def start(self) -> None:
        """Start sampling (the first sample is one interval in)."""
        self._started = time.perf_counter()
        self._thread.start()

    def stop(self) -> None:
        """Stop sampling."""
        self._stop.set()
        self._thread.join()

    def _run(self) -> None:
        """Sample until :meth:`stop` is called."""
        while not self._stop.wait(self._interval):
            state = _gpu_state()
            seconds = round(time.perf_counter() - self._started, 1)
            self.samples.append({"seconds": seconds, **(state or {})})


def stray_processes(
    threshold_percent: float = STRAY_CPU_PERCENT, interval_s: float = 0.5
) -> list[dict[str, Any]]:
    """List the other processes busy right now: the stray-process check of a timed window.

    Every process's CPU use is sampled over ``interval_s`` (``psutil``, where 100 is one
    logical CPU fully used); this process and the idle process are left out.

    Args:
        threshold_percent: The least use, in percent of one logical CPU, that is listed.
        interval_s: The sampling interval.

    Returns:
        ``{"pid", "name", "cpu_percent"}`` per busy process, busiest first.
    """
    processes = []
    for process in psutil.process_iter(["pid", "name"]):
        try:
            process.cpu_percent(None)
            processes.append(process)
        except psutil.Error:
            continue
    time.sleep(interval_s)
    busy = []
    for process in processes:
        try:
            used = float(process.cpu_percent(None))
        except psutil.Error:
            continue
        if process.pid not in (0, os.getpid()) and used >= threshold_percent:
            busy.append({"pid": process.pid, "name": process.info["name"], "cpu_percent": used})
    return sorted(busy, key=lambda entry: -float(entry["cpu_percent"]))


def head_record() -> dict[str, Any]:
    """The commit this tool runs from, and the tracked files changed in its tree.

    Read with ``git`` from the repository that holds this file; the values are ``None``
    when ``git`` cannot answer.

    Returns:
        ``{"head": <full SHA>, "changed": [<porcelain lines>]}``.
    """
    root = Path(__file__).resolve().parent.parent.parent
    record: dict[str, Any] = {"head": None, "changed": None}
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
        status = subprocess.run(
            ["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
            capture_output=True,
            text=True,
            timeout=30,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return record
    record["head"] = head.stdout.strip()
    record["changed"] = [line for line in status.stdout.splitlines() if line.strip()]
    return record


class _PoolTracker:
    """Counts the high-water mark of CuPy's default memory pool through its allocator."""

    def __init__(self, backend: Backend) -> None:
        """Empty the default pool's cache and install a counting allocator in front of it."""
        self._cupy = backend.xp
        self._pool = self._cupy.get_default_memory_pool()
        self._pool.free_all_blocks()
        self.peak_used = int(self._pool.used_bytes())
        self._cupy.cuda.set_allocator(self._malloc)

    def _malloc(self, size: int) -> Any:
        """Allocate from the pool and update the high-water mark of its used bytes."""
        memory = self._pool.malloc(size)
        self.peak_used = max(self.peak_used, int(self._pool.used_bytes()))
        return memory

    def close(self) -> None:
        """Hand allocation back to the pool directly (the pool keeps its memory)."""
        self._cupy.cuda.set_allocator(self._pool.malloc)

    def cuda_used_bytes(self) -> int:
        """Device memory in use on the whole card, from the CUDA runtime."""
        free, total = self._cupy.cuda.runtime.memGetInfo()
        return int(total) - int(free)

    def record(self, gpu_before: dict[str, str] | None, cuda_before: int | None) -> dict[str, Any]:
        """The graphics memory figures, in MiB, read now (the pool still holds its memory)."""
        after = _nvidia_smi_gpu()
        cuda_after = self.cuda_used_bytes()
        return {
            "gpu_pool_peak_used_mb": self.peak_used / _MIB,
            "gpu_pool_reserved_mb": int(self._pool.total_bytes()) / _MIB,
            "gpu_pool_method": "counting allocator over cupy's default pool; reserved at end",
            "nvidia_smi_used_before_mb": None
            if gpu_before is None
            else _float(gpu_before.get("memory.used")),
            "nvidia_smi_used_after_mb": None if after is None else _float(after.get("memory.used")),
            "nvidia_smi_process_mb": _nvidia_smi_process_mb(),
            "cuda_used_before_mb": None if cuda_before is None else cuda_before / _MIB,
            "cuda_used_after_mb": cuda_after / _MIB,
        }


def _nvidia_smi_gpu() -> dict[str, str] | None:
    """Read name, driver and memory of the first GPU from ``nvidia-smi``; None if absent."""
    fields = ("name", "driver_version", "memory.total", "memory.used")
    lines = _nvidia_smi([f"--query-gpu={','.join(fields)}", "--format=csv,noheader,nounits"])
    if not lines:
        return None
    values = [value.strip() for value in lines[0].split(",")]
    if len(values) != len(fields):
        return None
    return dict(zip(fields, values, strict=True))


def _nvidia_smi_process_mb() -> float | str | None:
    """This process's graphics memory as ``nvidia-smi`` reports it (a string if not a number)."""
    lines = _nvidia_smi(["--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"])
    if lines is None:
        return None
    for line in lines:
        pid, _, used = (value.strip() for value in line.partition(","))
        if pid == str(os.getpid()):
            number = _float(used)
            return used if number is None else number
    return "not listed"


def _nvidia_smi(arguments: list[str]) -> list[str] | None:
    """Run ``nvidia-smi`` with ``arguments``; its output lines, or None if it cannot run."""
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None
    try:
        completed = subprocess.run(
            [executable, *arguments], capture_output=True, text=True, timeout=20, check=True
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return [line for line in completed.stdout.splitlines() if line.strip()]


def _cpu_brand() -> str:
    """The processor's name (py-cpuinfo), or ``platform.processor()`` if that fails."""
    try:
        import cpuinfo

        return str(cpuinfo.get_cpu_info().get("brand_raw", "")) or platform.processor()
    except Exception:  # py-cpuinfo is best effort on an unusual system
        return platform.processor()


def _cuda_version(code: int) -> str:
    """A CUDA version code (``1000 * major + 10 * minor``) as ``major.minor``."""
    return f"{code // 1000}.{code % 1000 // 10}"


def _float(text: str | None) -> float | None:
    """``text`` as a float, or None if it is not a number."""
    try:
        return None if text is None else float(text)
    except ValueError:
        return None


def _one_line(exc: BaseException) -> str:
    """The exception's message on one line (its class name when the message is empty)."""
    return " ".join(str(exc).split()) or type(exc).__name__


if __name__ == "__main__":
    raise SystemExit(main())
