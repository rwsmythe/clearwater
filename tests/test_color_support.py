"""Shared helpers of the WP3.5 colour tests (no tests here).

* ``make_stream`` builds a ``VideoStreamInfo`` by hand for the cases no sample covers.
* ``flat_yuv420`` is an INDEPENDENT reference: it computes the Y'CbCr codes of a flat RGB colour
  from the matrix coefficients with NumPy, so the truth the decode is compared with does not come
  from FFmpeg. The limited-range mapping is the standard code mapping (8-bit: Y = 16 + 219 Y,
  C = 128 + 224 C; 10-bit: the same times 4), which is WP3.1 R0-1's float convention (``Y' =
  16/255 + (219/255) Y``, chroma centred on 0) written in code units.
* ``measure_roundtrip`` runs the AD-10 pair through FFmpeg without an encoder (raw Y'CbCr) and
  reports the decoded-RGB difference.
"""

from __future__ import annotations

import subprocess
from collections.abc import Iterator
from dataclasses import dataclass, field, replace
from fractions import Fraction
from pathlib import Path

import numpy as np

from clearwater.color import (
    decode_filter,
    encode_filter,
    encode_pix_fmt,
    planes_to_rgb,
    rgb_frame_bytes,
    rgb_pix_fmt,
    rgb_to_planes,
)
from clearwater.interfaces.image import ColorDescription
from clearwater.interfaces.video import VideoStreamInfo
from clearwater.io.video import find_tool

HIST_RES = 16  # histogram bins per 1/255
HIST_TOP = 256
COEFFICIENTS = {"bt709": (0.2126, 0.0722), "bt601": (0.299, 0.114)}


def make_stream(
    *,
    pix_fmt: str = "yuv420p",
    matrix: str = "bt709",
    range_: str = "limited",
    siting: str = "left",
    width: int = 64,
    height: int = 32,
    assumed: bool = False,
) -> VideoStreamInfo:
    """Return a hand-built stream; the bit depth follows the pixel format."""
    bit_depth = 10 if "10" in pix_fmt else 8
    color = ColorDescription("bt709", "bt709", matrix, range_, bit_depth, assumed, None)
    return VideoStreamInfo(
        codec="hevc",
        width=width,
        height=height,
        bit_depth=bit_depth,
        pix_fmt=pix_fmt,
        chroma_siting=siting,
        color=color,
        frame_rate=Fraction(30),
        time_base=Fraction(1, 30000),
        nb_frames=None,
        rotation=0,
        vfr=False,
    )


def with_depth(stream: VideoStreamInfo, pix_fmt: str, bit_depth: int) -> VideoStreamInfo:
    """Return the stream as the raw Y'CbCr that the encode filter produces."""
    return replace(
        stream,
        pix_fmt=pix_fmt,
        bit_depth=bit_depth,
        color=replace(stream.color, bit_depth=bit_depth),
    )


def flat_yuv420(rgb: tuple[int, int, int], stream: VideoStreamInfo, *, frames: int = 1) -> bytes:
    """Return raw 4:2:0 planar Y'CbCr of a flat 8-bit RGB colour, from the matrix definition.

    Args:
        rgb: The colour, 8-bit R, G, B.
        stream: Gives matrix, range, bit depth and size.
        frames: How many identical frames.

    Returns:
        The raw frames in the stream's pixel format (Y plane, Cb plane, Cr plane).
    """
    kr, kb = COEFFICIENTS[stream.color.matrix]
    r, g, b = (c / 255 for c in rgb)
    y = kr * r + (1 - kr - kb) * g + kb * b
    cb = (b - y) / (2 * (1 - kb))
    cr = (r - y) / (2 * (1 - kr))
    n = 2 ** (stream.bit_depth - 8)
    if stream.color.range == "limited":
        codes = (16 * n + 219 * n * y, 128 * n + 224 * n * cb, 128 * n + 224 * n * cr)
    else:
        top = 256 * n - 1
        codes = (top * y, 128 * n + top * cb, 128 * n + top * cr)
    dtype = np.uint8 if stream.bit_depth == 8 else np.dtype("<u2")
    w, h = stream.width, stream.height
    planes = [
        np.full((h, w), round(codes[0]), dtype),
        np.full((h // 2, w // 2), round(codes[1]), dtype),
        np.full((h // 2, w // 2), round(codes[2]), dtype),
    ]
    return b"".join(p.tobytes() for p in planes) * frames


def ffmpeg(args: list[str], data: bytes | None = None) -> bytes:
    """Run ``ffmpeg`` quietly with the arguments and return standard output."""
    command = [str(find_tool("ffmpeg")), "-nostdin", "-hide_banner", "-loglevel", "error", *args]
    result = subprocess.run(command, input=data, capture_output=True, check=False, timeout=600)
    assert result.returncode == 0, result.stderr.decode(errors="replace")[-2000:]
    return result.stdout


def decode_raw(data: bytes, stream: VideoStreamInfo, vf: str | None = None) -> bytes:
    """Decode raw Y'CbCr frames of ``stream`` with a decode filter, to planar RGB bytes."""
    args = [
        "-f", "rawvideo", "-pix_fmt", stream.pix_fmt,
        "-s", f"{stream.width}x{stream.height}", "-i", "pipe:0",
        "-vf", vf if vf is not None else decode_filter(stream), "-f", "rawvideo", "pipe:1",
    ]  # fmt: skip
    return ffmpeg(args, data)


def split_frames(data: bytes, size: int) -> list[bytes]:
    """Cut a byte string into whole frames of ``size`` bytes."""
    assert len(data) % size == 0
    return [data[i : i + size] for i in range(0, len(data), size)]


def decode_file_frames(
    path: Path, stream: VideoStreamInfo, frames: int, vf: str | None = None
) -> Iterator[bytes]:
    """Yield the first ``frames`` frames of a video file, decoded with the decode filter."""
    size = rgb_frame_bytes(stream.width, stream.height, stream.bit_depth)
    command = [
        str(find_tool("ffmpeg")), "-nostdin", "-hide_banner", "-loglevel", "error",
        "-noautorotate", "-i", str(path), "-map", "0:v:0", "-an", "-sn", "-dn",
        "-vf", vf if vf is not None else decode_filter(stream),
        "-frames:v", str(frames), "-fps_mode", "passthrough", "-f", "rawvideo", "pipe:1",
    ]  # fmt: skip
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as proc:
        assert proc.stdout is not None
        while True:
            chunk = proc.stdout.read(size)
            if len(chunk) < size:
                assert not chunk, f"a short final frame: {len(chunk)} of {size} bytes"
                break
            yield chunk
        assert proc.wait(timeout=60) == 0, f"ffmpeg exited with {proc.returncode}"


@dataclass
class Figures:
    """Decoded-RGB differences, in 1/255 units: ``max``, ``mean`` and the share above 2/255."""

    frames: int = 0
    max: float = 0.0
    total: float = 0.0
    samples: int = 0
    over_2: int = 0
    histogram: np.ndarray = field(
        default_factory=lambda: np.zeros(HIST_TOP * HIST_RES + 1, np.int64)
    )

    @property
    def mean(self) -> float:
        """The mean absolute difference."""
        return self.total / self.samples

    @property
    def share_over_2(self) -> float:
        """The share of samples that differ by more than 2/255."""
        return self.over_2 / self.samples

    def add(self, a: np.ndarray, b: np.ndarray) -> None:
        """Accumulate the difference of two float RGB frames."""
        d = np.abs(a.astype(np.float64) - b.astype(np.float64)) * 255
        self.frames += 1
        self.max = max(self.max, float(d.max()))
        self.total += float(d.sum())
        self.samples += d.size
        self.over_2 += int((d > 2).sum())
        bins = np.minimum((d * HIST_RES).astype(np.int64).ravel(), HIST_TOP * HIST_RES)
        self.histogram += np.bincount(bins, minlength=HIST_TOP * HIST_RES + 1)

    def percentile(self, q: float) -> float:
        """Return the q-th percentile of the difference (1/255 units, bin upper edge)."""
        cumulative = np.cumsum(self.histogram)
        index = int(np.searchsorted(cumulative, q / 100 * self.samples))
        return (index + 1) / HIST_RES

    def __str__(self) -> str:
        """Return the figures in 1/255 units."""
        return (
            f"{self.frames} frames: max {self.max:.2f}, mean {self.mean:.3f}, "
            f"p99.9 {self.percentile(99.9):.2f}, >2: {100 * self.share_over_2:.2f} %"
        )


def measure_roundtrip(
    path: Path,
    stream: VideoStreamInfo,
    *,
    frames: int,
    out_depth: int | None = None,
    batch: int = 5,
    decode_vf: str | None = None,
    encode_vf: str | None = None,
    decode2_vf: str | None = None,
) -> Figures:
    """Measure the decoded-RGB difference of the AD-10 pair, encoder excluded (V9).

    Per batch: decode with the decode filter to planar RGB, to float and back with
    ``samples.py`` (asserted exact at the source depth), then through the encode filter to raw
    Y'CbCr in the source pixel format (no encoder), decode that again, and compare the two float
    RGB results. The ``*_vf`` arguments replace a filter to plant a defect: ``decode_vf`` the
    first decode, ``encode_vf`` the encode, ``decode2_vf`` the second decode.

    Args:
        path: The video file.
        stream: Its probed stream.
        frames: How many frames from the start.
        out_depth: The output bit depth (the source's own by default; 10 for D76).
        batch: Frames per FFmpeg round.
        decode_vf: Replaces the first decode filter.
        encode_vf: Replaces the encode filter.
        decode2_vf: Replaces the second decode filter (default: ``decode_vf``, then the product's).

    Returns:
        The accumulated figures.
    """
    depth = stream.bit_depth if out_depth is None else out_depth
    enc_stream = with_depth(stream, encode_pix_fmt(stream, bit_depth=depth), depth)
    enc_vf = encode_vf if encode_vf is not None else encode_filter(stream, bit_depth=depth)
    second_vf = decode2_vf if decode2_vf is not None else decode_vf
    figures = Figures()
    pending: list[bytes] = []

    def flush() -> None:
        floats = [
            planes_to_rgb(f, width=stream.width, height=stream.height, bit_depth=stream.bit_depth)
            for f in pending
        ]
        if depth == stream.bit_depth:
            assert [rgb_to_planes(a, bit_depth=depth) for a in floats] == pending
        rgb = b"".join(rgb_to_planes(a, bit_depth=depth) for a in floats)
        yuv = ffmpeg(
            [
                "-f",
                "rawvideo",
                "-pix_fmt",
                rgb_pix_fmt(depth),
                "-s",
                f"{stream.width}x{stream.height}",
                "-i",
                "pipe:0",
                "-vf",
                enc_vf,
                "-f",
                "rawvideo",
                "pipe:1",
            ],
            rgb,
        )
        back = decode_raw(yuv, enc_stream, second_vf)
        size = rgb_frame_bytes(stream.width, stream.height, depth)
        for a, raw in zip(floats, split_frames(back, size), strict=True):
            b = planes_to_rgb(raw, width=stream.width, height=stream.height, bit_depth=depth)
            figures.add(a, b)
        pending.clear()

    for frame in decode_file_frames(path, stream, frames, decode_vf):
        pending.append(frame)
        if len(pending) == batch:
            flush()
    if pending:
        flush()
    return figures
