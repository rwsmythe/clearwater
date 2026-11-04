"""Run a whole clip through the prototype: the analysis pass and the export loop (WP1.2 Part B).

Usage::

    uv run python tools/prototype/clip.py analyse CLIP [--method M] [--neutral]
        [--device gpu|cpu] [--hwaccel none|cuda] [--frames N] [--out DIR]
    uv run python tools/prototype/clip.py render CLIP --statistics FILE [--neutral]
        [--device gpu|cpu] [--resident] [--frames N] [--out DIR] [--no-compare]
    uv run python tools/prototype/clip.py witness --run RUN_RECORD [--device gpu|cpu] [--count N]

``CLIP`` is a footage stem (``GX011627``), found anywhere under the footage folder with
:func:`local_config.find_footage_file`, or the path of a video OUTSIDE the footage folder
(a test clip); a path inside the footage folder is refused, so footage is always named by
its stem. The footage folder is only ever an input. Every file written goes under
``<working folder>/wp1.2b/`` (``--out`` must lie inside it), and each path is checked
before anything writes it (:func:`lookcheck.frames.check_output_path`: inside that folder,
outside the footage folder, not a file with several hard links).

**The analysis pass** (spec 7.2 steps 1 and 2) decodes every frame once to a raw RGB pipe,
area-averages it to the 540-line proxy (:func:`prototype.temporal.proxy`) and computes the
STAGED statistics of WP1.4 (D97) with the smoother :data:`SMOOTHER` (``median_gaussian``,
2 s: WP1.4's recommendation, PROVISIONAL per DR-25(3); the default is WP2.1's decision).
:class:`StagedStream` is :func:`prototype.temporal.analyse_staged` in streaming form: the
same calls (:func:`prototype.temporal.measure` per stage and frame with the smoothed
earlier stages supplied, :meth:`prototype.temporal.Smoother.apply`), giving the same
numbers bit for bit (``tests/test_prototype_clip.py``), but holding only the proxies that
a later stage still has to measure instead of the whole clip's (a 31,364-frame clip has
about 190 GB of float32 proxies). The record (``analysis/<stem>-<method>-<stamp>.json``)
holds the source's identity, every frame's pts, the smoothed statistics of every frame,
the per-stage measured series, and each frame's channel means (the content witness).

**The export loop** (spec 7.2 step 3; the WP1.5 SIMPLE path with the correction
inserted): FFmpeg decodes the source to a raw RGB pipe (``rgb24`` for an 8-bit source,
``rgb48le`` for a 10-bit one; FFmpeg converts YCbCr to RGB and upsamples the chroma here,
with the source's range and matrix passed to ``scale`` explicitly, which the product does
itself under WP3.5); each frame becomes float32 in [0, 1] and goes through
:func:`prototype.pipeline.correct` with the frame's smoothed statistics from the analysis
record; the output is rounded back to integers and written to a second raw pipe, from which
FFmpeg encodes HEVC with ``hevc_nvenc`` at the source's bit depth and the WP1.5 settings,
and muxes it with the source's audio and data streams copied and its metadata, colour tags
and timestamps carried (:func:`encode_command`). Frame timestamps are carried by the decode
order: the sources are constant frame rate with the first frame at 0 (checked; anything
else is outside this prototype's envelope and refused). Buffering is bounded: two float
input buffers (one being filled, one in the core) and two output slots (a slot is taken
before the core computes a frame and given back once the frame is written), so at most two
frames are in flight on each side of the core.

The frame boundaries of both pipes are exact: a frame is exactly
``width * height * 3 * bytes per sample`` bytes (:func:`frame_bytes`), a short read at the
end of the stream is :class:`PartialFrameError` and a frame count other than the source's
is :class:`FrameCountError`. The render refuses a statistics record made for another
file, another frame count or pts list, other parameters or another decode
(:class:`StatisticsMismatchError`), and checks the content witness, the channel means of
every 30th decoded frame and of the last, against the record while it runs.

Timing (:class:`LoopTiming`) runs from the moment the first decoded frame has been read
from the pipe to the moment both FFmpeg processes have been reaped (the decoder's status
collected, then the encoder's, which exits after the muxer has closed the file). The export
writes to a temporary name beside the final one and renames it only after that, so the
rename lies outside the bracket. ``prototype.bench --mode`` records the same functions with
memory and ambient readings; this command line is the runner without them.

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, on a
configuration, probe, path, pipe or FFmpeg failure.

Windows / NVIDIA evidence; not a Mac instrument (WP6.4, audit row T34): the prototype encodes
with NVENC only; its algorithms are not ported to the Mac.
"""

from __future__ import annotations

import argparse
import contextlib
import dataclasses
import datetime
import json
import math
import queue
import re
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass, field
from fractions import Fraction
from pathlib import Path
from typing import IO, Any

import numpy as np
from numpy.typing import NDArray

if not __package__:
    # Script mode (``python tools/prototype/clip.py``): sys.path[0] is tools/prototype, so
    # put the tools directory first to make ``prototype`` and its siblings importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from container_spike.compare import (
    MANDATORY,
    REQUIRED,
    ProbeError,
    compare_files,
    pix_fmt_shape,
    run_ffprobe,
    tool_env,
    write_record,
)
from container_spike.spike import ENCODER_SETTINGS
from local_config import LocalConfigError, find_footage_file, load_local_config
from lookcheck.frames import (
    ExtractError,
    OutputRoots,
    StreamInfo,
    probe_stream,
    scale_matrix,
    scale_range,
)
from prototype import temporal
from prototype.backend import Backend, select_backend
from prototype.params import METHODS, Params
from prototype.pipeline import Statistics, correct
from prototype.temporal import Series, Smoother

WORK_SUBDIR = "wp1.2b"
"""The folder inside the working folder that every output of this package goes to."""

SMOOTHER = Smoother("median_gaussian", 2.0)
"""WP1.4's recommended smoother, PROVISIONAL per DR-25(3) (the default is WP2.1's)."""

PIPE_FORMATS: dict[int, tuple[str, int]] = {8: ("rgb24", 1), 10: ("rgb48le", 2)}
"""Source bit depth -> (raw pipe pixel format, bytes per sample)."""

ENCODE_FORMATS: dict[int, tuple[str, str]] = {8: ("yuv420p", "main"), 10: ("p010le", "main10")}
"""Source bit depth -> (encoder pixel format, HEVC profile), 4:2:0 as WP1.5."""

ENCODER = "hevc_nvenc"
"""The encoder of the export loop (WP1.5 SIMPLE)."""

HWACCELS = ("none", "cuda")
"""Decode choices: software, or ``-hwaccel cuda`` (frames downloaded to system memory)."""

OUTPUT_FRAMES = 2
"""Frames alive at once on the output side: a slot is taken before the core computes a frame
and given back when the writer has written it, so at most two frames are being computed,
queued or written."""

INPUT_BUFFERS = 2
"""Float input buffers: one being filled by the reader, one in the core."""

PASSTHROUGH_BUFFERS = INPUT_BUFFERS + OUTPUT_FRAMES
"""Integer buffers of a pass-through: the frames an export holds in flight on both sides."""

WITNESS_EVERY = 30
"""The render checks the channel means of every this-many-th decoded frame (and the last)."""

WITNESS_TOLERANCE = 1e-8
"""Largest accepted difference between a frame's channel means in the analysis and render."""

ANALYSIS_SCHEMA = "wp1.2b-analysis/1"
"""Schema tag of the analysis record."""

PROVISIONAL_NOTE = (
    "median_gaussian 2 s is WP1.4's recommended smoothing, PROVISIONAL per DR-25(3); "
    "the default is WP2.1's decision"
)

WITNESS_FRAMES = 24
"""Frame indices the output witness checks, spread evenly over the clip, first and last included."""

WITNESS_MARGIN_DB = 2.0
"""The output witness passes frame i when PSNR(output i, expected i) is at least the encoder's
own loss on that frame less this margin. The encoder's own loss, ``ref_i``, is measured per
frame: the expected frames from the export's GOP start (its last I-frame at or before ``i``)
through the next I/P anchor after ``i`` are encoded through the export's own encode chain
(:func:`encode_command`), decoded, and compared with themselves, so that frame ``i`` is coded
in its own position with the future frame it is predicted from. The margin is the
orchestrator's ruling. For scale: such a reference of GX011627 frames 0-32 coded frame 30 bit
for bit as the export did (``work/wp1.2b/remediation/anchor_reference_repro.json``)."""

WITNESS_MARGIN_BASIS = (
    "orchestrator ruling: own_i >= ref_i - 2.0 dB, ref_i the encoder's own loss on the expected "
    "frame i, encoded from the export's GOP start through the next I/P anchor after i through "
    "the export's chain; for scale, GX011627 frame 30: reference identical to the export"
)
"""The basis of :data:`WITNESS_MARGIN_DB`, as recorded in each witness record."""

WITNESS_SANITY_DB = 20.0
"""An absolute floor beneath the relative rule, which catches a gross failure even if the
reference encode itself is broken."""

FIRST_FLOOR_DB = 28.0
"""The output witness's FIRST criterion (an absolute floor from WP1.5's identity re-encode of
GX011627: Y 35.83 dB mean, 32.27 dB min), REPLACED before re-scoring: it failed GX011627 frame 30
at 27.79 dB, whose encoder-alone loss is 28.76 dB. Each witness record keeps the frame's verdict
under it (``first_floor_ok``) so that nothing is hidden."""

SHOWINFO_PATTERN = re.compile(r"showinfo.*\] n:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:")
"""A ``showinfo`` frame line: frame number and pts (the pattern of ``lookcheck.frames``)."""

N6_MINUTES_PER_MINUTE = 3.3
"""N6 / D106: minutes of processing per minute of footage, end to end. At a frame rate ``r``
the per-frame budget is ``3.3 * 60 / (60 * r) = 3.3 / r`` seconds (0.1101 s at 29.97 fps)."""

PROCESS_TIMEOUT_S = 600.0
"""Seconds to wait for an FFmpeg process to exit once its input has ended."""

STALL_TIMEOUT_S = 300.0
"""Seconds the main loop waits for a frame from the reader, or for room at the writer, or for
a thread to end, before it calls the pass stalled (far above any frame time in the envelope:
the CPU core takes about 11 s on a 4K frame)."""

_SENTINEL: Any = object()
_SQUARE_PIXELS = frozenset({"1:1", "0:1", "N/A", ""})  # ffprobe prints 0:1 for "unknown"


class ClipError(Exception):
    """A clip cannot be processed: outside the envelope, a tool failed, or a check refused."""


class PipeError(ClipError):
    """A raw pipe did not carry whole frames, or not the expected number of them."""


class PartialFrameError(PipeError):
    """The stream ended inside a frame: the frame boundaries are not where they must be."""


class FrameCountError(PipeError):
    """A pipe carried another number of frames than the source has."""


class OutputWitnessError(ClipError):
    """The output witness found an exported frame that is not the corrected source frame."""


class OutputMismatchError(OutputWitnessError):
    """An output frame scored below the witness floor against its expected frame."""


class OutputOrderError(OutputWitnessError):
    """An output frame matched a neighbour's expected frame at least as well as its own."""


class StatisticsMismatchError(ClipError):
    """A statistics record does not belong to this clip, these parameters or this decode."""


# --- the source ---------------------------------------------------------------------------------


@dataclass(frozen=True)
class Source:
    """A video to process, with what the loop needs to know about it.

    Attributes:
        path: The file (read only).
        info: The first video stream's probe (size, time base, frame rate, colour tags).
        bit_depth: 8 or 10.
        pts_ticks: Every frame's presentation timestamp in ticks of ``info.time_base``, in
            presentation order (the video packets' pts, sorted).
        streams: The ``ffprobe -show_streams`` stream objects of the file.
        video_index: The ``ffprobe`` index of the video stream.
        size_bytes: File size.
        mtime_ns: Modification time, nanoseconds.
    """

    path: Path
    info: StreamInfo
    bit_depth: int
    pts_ticks: tuple[int, ...]
    streams: tuple[Mapping[str, Any], ...]
    video_index: int
    size_bytes: int
    mtime_ns: int

    @property
    def frame_count(self) -> int:
        """Number of frames."""
        return len(self.pts_ticks)

    @property
    def pipe_format(self) -> str:
        """The raw pipe pixel format (``rgb24`` or ``rgb48le``)."""
        return PIPE_FORMATS[self.bit_depth][0]

    @property
    def frame_bytes(self) -> int:
        """Bytes of one raw RGB frame."""
        return frame_bytes(self.info.width, self.info.height, self.bit_depth)

    @property
    def footage_seconds(self) -> Fraction:
        """The clip's length: frames times the frame period (exact)."""
        return self.frame_count / self.info.frame_rate

    def identity(self) -> dict[str, Any]:
        """Return what identifies the clip in a record: name, size, time, frames, pts ends."""
        return {
            "stem": self.path.stem,
            "name": self.path.name,
            "path": str(self.path),
            "size_bytes": self.size_bytes,
            "mtime_ns": self.mtime_ns,
            "frames": self.frame_count,
            "first_pts_ticks": self.pts_ticks[0],
            "last_pts_ticks": self.pts_ticks[-1],
            "time_base": _ratio(self.info.time_base),
            "frame_rate": _ratio(self.info.frame_rate),
            "width": self.info.width,
            "height": self.info.height,
            "bit_depth": self.bit_depth,
            "tags": self.info.tags.record(),
        }


def frame_bytes(width: int, height: int, bit_depth: int) -> int:
    """Return the size of one raw RGB frame on the pipe.

    Args:
        width: Frame width in pixels.
        height: Frame height in pixels.
        bit_depth: The source bit depth (8: ``rgb24``, 1 byte per sample; 10: ``rgb48le``,
            2 bytes per sample).

    Returns:
        ``width * height * 3 * bytes per sample``.

    Raises:
        ClipError: The bit depth has no pipe format.
    """
    if bit_depth not in PIPE_FORMATS:
        raise ClipError(f"bit depth {bit_depth} is outside the envelope (8 or 10)")
    return width * height * 3 * PIPE_FORMATS[bit_depth][1]


def resolve_clip(name: str, footage_root: Path) -> Path:
    """Return the video a command-line ``CLIP`` names: a footage stem or an outside path.

    Args:
        name: A bare stem (found under the footage folder) or the path of an existing file
            outside the footage folder.
        footage_root: The footage folder.

    Returns:
        The file.

    Raises:
        ClipError: ``name`` is a path inside the footage folder (name footage by its stem).
        local_config.FootageLookupError: The stem matches no file or several.
    """
    candidate = Path(name)
    if candidate.is_file():
        resolved, footage = candidate.resolve(), footage_root.resolve()
        if resolved == footage or footage in resolved.parents:
            raise ClipError(f"{name} is inside the footage folder: name footage clips by stem")
        return candidate
    return find_footage_file(name, footage_root)


def open_source(path: Path) -> Source:
    """Probe a video and check that the loop can carry its frames by decode order.

    Args:
        path: The file (read only).

    Returns:
        The source.

    A stream rotated by a display matrix is refused by :func:`lookcheck.frames.probe_stream`
    and one with non-square pixels here: the raw pipe carries neither, so the output could
    not keep them.

    Raises:
        ClipError: The stream is not 8- or 10-bit 4:2:0, is rotated, has non-square pixels,
            its frames are not at a constant frame rate starting at pts 0, or a probe fails.
    """
    try:
        info = probe_stream(path)
        probe = run_ffprobe(["-show_format", "-show_streams", str(path)])
        packets = run_ffprobe(["-select_streams", "v:0", "-show_entries", "packet=pts", str(path)])
    except Exception as exc:  # ExtractError and container_spike's ProbeError
        raise ClipError(f"cannot probe {path.name}: {exc}") from None
    streams = tuple(s for s in probe.get("streams", []) if isinstance(s, dict))
    video = next(
        (
            s
            for s in streams
            if s.get("codec_type") == "video"
            and not dict(s.get("disposition") or {}).get("attached_pic")
        ),
        None,
    )
    if video is None:
        raise ClipError(f"{path.name} has no video stream")
    if str(video.get("sample_aspect_ratio", "1:1")) not in _SQUARE_PIXELS:
        raise ClipError(
            f"{path.name}: sample aspect ratio {video.get('sample_aspect_ratio')} is outside "
            "the envelope (the raw pipe carries square pixels only)"
        )
    chroma, depth = pix_fmt_shape(str(video.get("pix_fmt")))
    if chroma != "4:2:0" or depth not in PIPE_FORMATS:
        raise ClipError(
            f"{path.name}: pixel format {video.get('pix_fmt')} is outside the envelope "
            "(8- or 10-bit 4:2:0)"
        )
    ticks: list[int] = []
    for packet in packets.get("packets", []):
        pts = packet.get("pts") if isinstance(packet, dict) else None
        if not isinstance(pts, int):
            raise ClipError(f"{path.name}: a video packet has no pts")
        ticks.append(pts)
    ticks.sort()
    _check_constant_rate(path.name, ticks, info)
    stat = path.stat()
    return Source(
        path=path,
        info=info,
        bit_depth=int(depth),
        pts_ticks=tuple(ticks),
        streams=streams,
        video_index=int(video["index"]),
        size_bytes=int(stat.st_size),
        mtime_ns=int(stat.st_mtime_ns),
    )


def _check_constant_rate(name: str, ticks: Sequence[int], info: StreamInfo) -> None:
    """Refuse a stream whose pts do not run 0, step, 2 step, ... at its frame rate."""
    if len(ticks) < temporal.MIN_FRAMES:
        raise ClipError(f"{name}: {len(ticks)} frames; at least {temporal.MIN_FRAMES} needed")
    step = 1 / (info.frame_rate * info.time_base)
    if step.denominator != 1:
        raise ClipError(f"{name}: the frame period is not a whole number of ticks ({step})")
    expected = [index * int(step) for index in range(len(ticks))]
    if list(ticks) != expected:
        raise ClipError(
            f"{name}: pts are not constant-rate from 0 (first {list(ticks[:3])}, step {step}): "
            "a VFR or offset clip is outside this prototype's envelope"
        )


# --- the FFmpeg commands ------------------------------------------------------------------------


def decode_command(
    source: Source,
    hwaccel: str = "none",
    frames: int | None = None,
    seek_ticks: int | None = None,
    showinfo: bool = False,
) -> list[str]:
    """Return the FFmpeg command that decodes the source's video to the raw RGB pipe.

    The conversion follows the stream's tags (``scale`` with ``in_range``,
    ``in_color_matrix``, ``out_range=full`` and ``accurate_rnd``, as
    :func:`lookcheck.frames.colour_filter`), to ``rgb24`` (8-bit) or ``rgb48le`` (10-bit).
    ``-fps_mode passthrough`` neither drops nor repeats a frame; ``-noautorotate`` keeps
    the pixels as stored. The output is standard output only (``pipe:1``): this command
    writes no file.

    Args:
        source: The source.
        hwaccel: ``"none"`` (software decode) or ``"cuda"`` (``-hwaccel cuda``; frames are
            downloaded to system memory before the conversion).
        frames: Decode only this many frames; ``None`` decodes all.
        seek_ticks: Start at the frame with this pts: the input is seeked to half a frame
            before it with ``-copyts``, so FFmpeg discards the frames before it and keeps
            the source timestamps (the WP1.3 extraction's method).
        showinfo: Put ``showinfo`` first in the filter chain, so that each frame's pts is
            printed on standard error (a check of which frames were decoded).

    Returns:
        The command.

    Raises:
        ClipError: ``hwaccel`` is not one of :data:`HWACCELS`.
    """
    if hwaccel not in HWACCELS:
        raise ClipError(f"hwaccel must be one of {', '.join(HWACCELS)}, got {hwaccel!r}")
    tags = source.info.tags
    chain = (
        f"scale=in_range={scale_range(tags)}:in_color_matrix={scale_matrix(tags)}"
        f":out_range=full:flags=accurate_rnd,format={source.pipe_format}"
    )
    command = ["ffmpeg", "-nostdin", "-hide_banner", "-nostats", "-loglevel", "error"]
    if showinfo:
        command[-1] = "info"
    if hwaccel == "cuda":
        command += ["-hwaccel", "cuda"]
    command.append("-noautorotate")
    if seek_ticks is not None:
        seek = seek_ticks * source.info.time_base - 1 / (2 * source.info.frame_rate)
        command += ["-copyts", "-ss", f"{float(max(seek, Fraction(0))):.6f}"]
    command += ["-i", str(source.path), "-map", "0:v:0", "-an", "-sn", "-dn"]
    command += ["-vf", f"showinfo,{chain}" if showinfo else chain]
    if frames is not None:
        command += ["-frames:v", str(frames)]
    command += ["-fps_mode", "passthrough", "-f", "rawvideo", "pipe:1"]
    return command


def encode_command(source: Source, output: Path, frames: int | None = None) -> list[str]:
    """Return the FFmpeg command that encodes the raw RGB pipe and muxes it with the source.

    Input 0 is the raw pipe (the source's size and frame rate; pts 0, 1, 2, ... frame
    periods, which is the source's own sequence, :func:`open_source`); input 1 is the
    source, for its audio and data streams and metadata. The video is converted back to
    YCbCr with the source's matrix and range (``scale`` ``out_color_matrix``,
    ``out_range``, ``accurate_rnd``) at the source's bit depth, 4:2:0, and encoded with
    ``hevc_nvenc`` and WP1.5's settings (:data:`container_spike.spike.ENCODER_SETTINGS`),
    tagged ``hvc1`` and with the source's colour tags, on the frames (``setparams``: the raw
    frames carry no primaries or transfer, and the encoder takes the frames' tags) and on
    the stream (``-color_primaries`` and the rest, as WP1.5). The WP1.5 timing flags: ``-copyts``,
    ``-fps_mode passthrough``, the encoder time base set to the source's
    (``-enc_time_base:v``) and the video track's timescale to its denominator,
    ``+negative_cts_offsets``. Audio and every data stream except the timecode track are
    copied (the timecode track is written again from the ``timecode`` tag,
    ``-write_tmcd 1``); container metadata (``-map_metadata 1``) and the video stream's
    metadata (``-map_metadata:s:v:0 1:s:v:0``) come from the source. ``-y`` is passed for
    an output path the caller has checked.

    Args:
        source: The source.
        output: The output file (already checked by the caller).
        frames: When only the first ``frames`` frames are encoded, the source's other
            streams are cut to their length (``-t`` on input 1).

    Returns:
        The command.
    """
    info = source.info
    pix_fmt, profile = ENCODE_FORMATS[source.bit_depth]
    video = next(s for s in source.streams if int(s.get("index", -1)) == source.video_index)
    colour: list[str] = []
    frame_tags: list[str] = []
    for key, option, param in (
        ("color_primaries", "-color_primaries", "color_primaries"),
        ("color_transfer", "-color_trc", "color_trc"),
        ("color_space", "-colorspace", "colorspace"),
        ("color_range", "-color_range", "range"),
    ):
        value = video.get(key)
        if isinstance(value, str) and value not in ("", "unknown"):
            colour += [option, value]
            frame_tags.append(f"{param}={value}")
    maps = ["-map", "0:v:0"]
    for stream in source.streams:
        if stream.get("codec_type") == "audio" or (
            stream.get("codec_type") == "data" and stream.get("codec_tag_string") != "tmcd"
        ):
            maps += ["-map", f"1:{stream['index']}"]
    cut = [] if frames is None else ["-t", f"{float(frames / info.frame_rate):.6f}"]
    to_yuv = (
        f"scale=out_color_matrix={scale_matrix(info.tags)}:out_range={scale_range(info.tags)}"
        f":flags=accurate_rnd,format={pix_fmt}"
    )
    if frame_tags:
        # The raw frames carry no primaries or transfer; the encoder takes the frames' tags.
        to_yuv += f",setparams={':'.join(frame_tags)}"
    return [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "error",
        "-y",
        "-copyts",
        "-f",
        "rawvideo",
        "-pix_fmt",
        source.pipe_format,
        "-s",
        f"{info.width}x{info.height}",
        "-framerate",
        _ratio(info.frame_rate),
        "-i",
        "pipe:0",
        *cut,
        "-i",
        str(source.path),
        *maps,
        "-vf",
        to_yuv,
        "-c:v",
        ENCODER,
        *ENCODER_SETTINGS[ENCODER],
        "-pix_fmt",
        pix_fmt,
        "-profile:v",
        profile,
        *colour,
        "-tag:v",
        "hvc1",
        "-fps_mode",
        "passthrough",
        "-enc_time_base:v",
        _ratio(info.time_base),
        "-video_track_timescale",
        str(info.time_base.denominator),
        "-c:a",
        "copy",
        "-c:d",
        "copy",
        "-map_metadata",
        "1",
        "-map_metadata:s:v:0",
        "1:s:v:0",
        "-write_tmcd",
        "1",
        "-movflags",
        "+negative_cts_offsets",
        str(output),
    ]


# --- raw pipes ----------------------------------------------------------------------------------


def read_frame(stream: IO[bytes], buffer: NDArray[Any]) -> bool:
    """Fill ``buffer`` with exactly one frame from a raw pipe.

    Args:
        stream: The pipe (an unbuffered binary stream).
        buffer: A C-contiguous array of exactly one frame's bytes.

    Returns:
        True when a whole frame was read; False at the end of the stream, before any byte
        of a new frame.

    Raises:
        PartialFrameError: The stream ended inside the frame.
    """
    view = memoryview(buffer).cast("B")
    filled = 0
    while filled < len(view):
        count = stream.readinto(view[filled:])  # type: ignore[attr-defined]
        if not count:
            break
        filled += count
    if filled == 0:
        return False
    if filled != len(view):
        raise PartialFrameError(
            f"the pipe ended {filled} bytes into a frame of {len(view)} bytes: "
            "the frame boundaries are wrong"
        )
    return True


def write_frame(stream: IO[bytes], frame: NDArray[Any]) -> None:
    """Write one whole frame to a raw pipe, in as many ``write`` calls as the pipe takes.

    Args:
        stream: The pipe (an unbuffered binary stream).
        frame: The frame.

    Raises:
        PipeError: A write accepted no byte (or the stream would block): the frame did not
            reach the encoder whole.
    """
    view = memoryview(np.ascontiguousarray(frame)).cast("B")
    written = 0
    while written < len(view):
        count = stream.write(view[written:])
        if not count:
            raise PipeError(
                f"the pipe accepted {written} of the {len(view)} bytes of a frame: "
                "the frame boundaries are wrong"
            )
        written += count


def decode_frames(
    source: Source, first: int, count: int, hwaccel: str = "none"
) -> tuple[list[NDArray[Any]], list[str]]:
    """Decode ``count`` consecutive frames from frame ``first`` on, checking their pts.

    The decode seeks to frame ``first`` (:func:`decode_command` with ``seek_ticks`` and
    ``showinfo``) and reads exactly ``count`` frames from the pipe; the pts that
    ``showinfo`` printed for them must equal the source's ``pts_ticks[first:first + count]``,
    else nothing is returned. FFmpeg's standard error is read through a pipe by a thread
    (it holds the ``showinfo`` lines), so the decode writes no file at all.

    Args:
        source: The clip.
        first: Index of the first frame (presentation order).
        count: Number of frames.
        hwaccel: The decode choice.

    Returns:
        The frames (integer arrays ``(H, W, 3)``) and the command.

    Raises:
        ClipError: The range is outside the clip, FFmpeg fails, or it decoded other frames.
    """
    wanted = list(source.pts_ticks[first : first + count])
    if first < 0 or count < 1 or len(wanted) != count:
        raise ClipError(f"frames {first}..{first + count - 1} are outside {source.path.name}")
    command = decode_command(source, hwaccel, count, seek_ticks=wanted[0], showinfo=True)
    frames: list[NDArray[Any]] = []
    decoder = reader = drain = None
    chunks: list[bytes] = []
    try:
        decoder = _spawn(command, subprocess.PIPE, None, subprocess.PIPE)
        drain = threading.Thread(target=lambda: chunks.append(decoder.stderr.read()), daemon=True)
        drain.start()
        # One buffer per frame, kept, and one more on which the reader meets the end.
        reader = _Reader(source, decoder.stdout, LoopTiming(), "raw", buffers=count + 1)
        reader.start()
        while (item := _take(reader.ready, "the decoder")) is not _SENTINEL:
            frames.append(item[1])
        _join(reader, "the reader")
        if reader.error is not None:
            raise reader.error
        status = _finish(decoder, "the decoder")
        _join(drain, "the stderr reader")
    finally:
        _stop(decoder)
        _release(reader, None)
    stderr = b"".join(chunks).decode("utf-8", errors="replace")
    if status != 0:
        raise ClipError(f"the decoder failed (status {status}): {stderr.strip()[-300:]}")
    seen = [int(match.group(2)) for match in SHOWINFO_PATTERN.finditer(stderr)][:count]
    if len(frames) != count or seen != wanted:
        raise FrameCountError(
            f"decoded {len(frames)} frames with pts {seen[:3]}...; wanted {count} from pts "
            f"{wanted[0]}: refusing to label the frames"
        )
    return frames, command


def to_float(frame: Any, xp: Any, bit_depth: int) -> Any:
    """Return an integer RGB frame as float32 in [0, 1]: ``value / (2**8 - 1)`` or ``/ 65535``.

    Args:
        frame: The frame, ``uint8`` (8-bit) or ``uint16`` (10-bit, ``rgb48le``), of ``xp``.
        xp: ``numpy`` or ``cupy``.
        bit_depth: The source bit depth.

    Returns:
        The frame, float32, correctly rounded quotients.
    """
    scale = 255.0 if bit_depth == 8 else 65535.0
    return xp.divide(frame.astype(xp.float32), xp.float32(scale))


def to_integer(image: NDArray[np.float32], out: NDArray[Any], scratch: NDArray[np.float32]) -> None:
    """Round a float32 RGB image in [0, 1] into the pipe's integer frame.

    ``out = clip(rint(image * maximum), 0, maximum)``, with the maximum of ``out``'s type
    (255 or 65535), so a value ``k / maximum`` of :func:`to_float` comes back as ``k``.

    Args:
        image: The corrected image, float32, on the host.
        out: The integer frame to fill (``uint8`` or ``uint16``), the image's shape.
        scratch: A float32 work array of the image's shape.
    """
    maximum = float(np.iinfo(out.dtype).max)
    np.multiply(image, np.float32(maximum), out=scratch)
    np.rint(scratch, out=scratch)
    np.clip(scratch, 0.0, maximum, out=scratch)
    out[...] = scratch


def _pipe_dtype(bit_depth: int) -> type[np.unsignedinteger[Any]]:
    """The integer sample type of the raw pipe."""
    return np.uint8 if bit_depth == 8 else np.uint16


def frame_buffer(source: Source) -> NDArray[Any]:
    """Allocate one integer frame of the raw pipe, asserting it is exactly one frame's bytes.

    Every reader and writer of a pipe uses buffers from here, so the frame boundaries are
    those of :func:`frame_bytes`: a buffer of another size is refused before any byte moves.

    Args:
        source: The clip.

    Returns:
        An uninitialised ``(H, W, 3)`` array of the pipe's sample type.

    Raises:
        PipeError: The buffer's size is not :attr:`Source.frame_bytes`.
    """
    buffer = np.empty((source.info.height, source.info.width, 3), _pipe_dtype(source.bit_depth))
    if buffer.nbytes != source.frame_bytes:
        raise PipeError(
            f"frame size mismatch: a {buffer.shape} {buffer.dtype} frame is {buffer.nbytes} "
            f"bytes, the pipe carries {source.frame_bytes} per frame"
        )
    return buffer


def _spawn(
    command: Sequence[str], log: IO[bytes] | int, stdin: int | None, stdout: int | None
) -> Any:
    """Start an FFmpeg process with standard error to ``log`` (a file or ``PIPE``)."""
    try:
        return subprocess.Popen(
            list(command),
            stdin=subprocess.DEVNULL if stdin is None else stdin,
            stdout=subprocess.DEVNULL if stdout is None else stdout,
            stderr=log,
            env=tool_env(),
            bufsize=0,
        )
    except OSError as exc:
        raise ClipError(f"{command[0]} could not start: {exc}") from None


def _finish(process: Any, name: str) -> int:
    """Wait for an FFmpeg process and return its exit status (killing it after the timeout)."""
    try:
        return int(process.wait(timeout=PROCESS_TIMEOUT_S))
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()
        raise ClipError(f"{name} did not exit within {PROCESS_TIMEOUT_S:g} s") from None


def _stop(*processes: Any) -> None:
    """Kill processes that are still running (after a failure)."""
    for process in processes:
        if process is not None and process.poll() is None:
            process.kill()
            process.wait()


def _take(source: queue.Queue[Any], what: str) -> Any:
    """Take the next item from a thread's queue, or call the pass stalled.

    Raises:
        ClipError: Nothing arrived within :data:`STALL_TIMEOUT_S`.
    """
    try:
        return source.get(timeout=STALL_TIMEOUT_S)
    except queue.Empty:
        raise ClipError(
            f"{what} sent nothing for {STALL_TIMEOUT_S:g} s: the pass stalled"
        ) from None


def _give(target: queue.Queue[Any], item: Any, what: str) -> None:
    """Hand an item to a thread's queue, or call the pass stalled.

    Raises:
        ClipError: No room appeared within :data:`STALL_TIMEOUT_S`.
    """
    try:
        target.put(item, timeout=STALL_TIMEOUT_S)
    except queue.Full:
        raise ClipError(
            f"{what} took nothing for {STALL_TIMEOUT_S:g} s: the pass stalled"
        ) from None


def _slot(writer: _Writer, what: str) -> None:
    """Take an output slot (:attr:`_Writer.slots`), or call the pass stalled.

    Raises:
        ClipError: No slot came free within :data:`STALL_TIMEOUT_S`.
    """
    if not writer.slots.acquire(timeout=STALL_TIMEOUT_S):
        raise ClipError(f"{what} took nothing for {STALL_TIMEOUT_S:g} s: the pass stalled")


def _join(thread: threading.Thread | None, what: str) -> None:
    """Wait for a thread to end, or call the pass stalled.

    Raises:
        ClipError: The thread is still running after :data:`STALL_TIMEOUT_S`.
    """
    if thread is None:
        return
    thread.join(timeout=STALL_TIMEOUT_S)
    if thread.is_alive():
        raise ClipError(f"{what} did not end within {STALL_TIMEOUT_S:g} s: the pass stalled")


def _release(reader: _Reader | None, writer: _Writer | None) -> None:
    """After a failure (the processes already stopped): let the threads end, briefly."""
    if reader is not None:
        reader.free.put(_SENTINEL)
    if writer is not None:
        with contextlib.suppress(queue.Full):
            writer.queue.put(_SENTINEL, timeout=5.0)
    for thread in (reader, writer):
        if thread is not None:
            thread.join(timeout=10.0)


def _log_tail(path: Path) -> str:
    """The last three lines of an FFmpeg log, on one line."""
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").strip().splitlines()
    except OSError:
        return ""
    return " / ".join(lines[-3:])


# --- timing -------------------------------------------------------------------------------------


@dataclass
class LoopTiming:
    """The clock readings of one pass over a clip (``time.perf_counter`` seconds).

    Attributes:
        spawned: When the first FFmpeg process was started.
        first_frame: When the first decoded frame had been read from the pipe whole.
        last_frame: When the main loop finished its last frame.
        closed: When the pass ended: for a render, a pass-through or an encode-only pass,
            when BOTH child processes had been reaped (the decoder's exit status is collected
            first, then the encoder's, which exits after the muxer closes the file; which one
            exited first and the gap are not recorded); for an analysis, when the decoder had
            been reaped and the last statistics computed; for a decode-only pass, when the
            decoder had been reaped.
        frames: Frames processed.
        wait_input: Per frame, the main loop's wait for the next decoded frame.
        core: Per frame, the main loop's work (the correction for a render; proxy and
            statistics for an analysis).
        wait_output: Per frame, the main loop's wait for an output slot (the writer behind).
        read: Per frame, the reader thread's time to read the frame from the pipe.
        convert_in: Per frame, the reader thread's conversion to float (render).
        convert_out: Per frame, the writer thread's conversion to integers.
        write: Per frame, the writer thread's write to the encoder pipe.
    """

    spawned: float = 0.0
    first_frame: float | None = None
    last_frame: float | None = None
    closed: float | None = None
    frames: int = 0
    wait_input: list[float] = field(default_factory=list)
    core: list[float] = field(default_factory=list)
    wait_output: list[float] = field(default_factory=list)
    read: list[float] = field(default_factory=list)
    convert_in: list[float] = field(default_factory=list)
    convert_out: list[float] = field(default_factory=list)
    write: list[float] = field(default_factory=list)

    def bracket_s(self) -> float:
        """Seconds from the first decoded frame to the end of the pass."""
        if self.first_frame is None or self.closed is None:
            raise ClipError("the pass did not run to its end")
        return self.closed - self.first_frame

    def record(self, footage_seconds: Fraction) -> dict[str, Any]:
        """Summarise the readings against the clip's length and the N6 budget.

        Args:
            footage_seconds: The clip's length (frames / frame rate) of the frames timed.

        Returns:
            The bracket, seconds per frame, minutes of processing per minute of footage,
            the startup and tail outside the main loop, each per-frame series' sum,
            median and 95th percentile, and the per-frame series themselves (rounded to
            microseconds).
        """
        bracket = self.bracket_s()
        assert self.first_frame is not None and self.closed is not None
        series = {
            name: getattr(self, name)
            for name in (
                "wait_input",
                "core",
                "wait_output",
                "read",
                "convert_in",
                "convert_out",
                "write",
            )
        }
        main_loop = sum(self.wait_input) + sum(self.core) + sum(self.wait_output)
        tail = None if self.last_frame is None else self.closed - self.last_frame
        return {
            "bracket": "first decoded frame read whole -> both children reaped",
            "frames": self.frames,
            "footage_s": float(footage_seconds),
            "bracket_s": bracket,
            "seconds_per_frame": bracket / self.frames if self.frames else None,
            "minutes_per_minute": bracket / float(footage_seconds),
            "startup_s": self.first_frame - self.spawned,
            "tail_s": tail,
            "main_loop_sum_s": main_loop,
            "main_loop_share_of_bracket": main_loop / bracket if bracket else None,
            "residual_s": None if tail is None else bracket - main_loop - tail,
            "residual_note": "bracket - main loop - tail: bookkeeping between frames",
            "summary": {name: _summary(values) for name, values in series.items() if values},
            "per_frame_s": {
                name: [round(value, 6) for value in values]
                for name, values in series.items()
                if values
            },
        }


def _bracketed(started: float, timing: LoopTiming) -> float:
    """Clip the first frame's wait to the bracket.

    The first wait counts from the first frame read whole, not from the decoder's start, so
    the main loop's per-frame series add up inside the bracket.
    """
    if timing.frames == 0 and timing.first_frame is not None:
        return max(started, timing.first_frame)
    return started


def _summary(values: Sequence[float]) -> dict[str, float]:
    """Sum, median and 95th percentile of a per-frame series."""
    array = np.asarray(values, dtype=np.float64)
    return {
        "sum_s": float(array.sum()),
        "median_s": float(np.median(array)),
        "p95_s": float(np.percentile(array, 95.0)),
    }


# --- the reader and writer threads -------------------------------------------------------------


class _Reader(threading.Thread):
    """Reads whole frames from the decoder pipe and hands them to the main loop.

    In ``"float"`` mode it converts each frame into one of the :data:`INPUT_BUFFERS` float
    buffers the main loop hands back. In ``"raw"`` mode it hands over the integer frame
    itself, from ``buffers`` integer buffers that come back to :attr:`free` once used (by
    the main loop of an analysis, by the writer of a pass-through). With a ``witness`` it
    checks the channel means of the frames it names against the analysis.
    """

    def __init__(
        self,
        source: Source,
        stream: IO[bytes],
        timing: LoopTiming,
        mode: str,
        witness: Mapping[int, Sequence[float]] | None = None,
        limit: int | None = None,
        buffers: int = INPUT_BUFFERS,
    ) -> None:
        """Prepare the reader; ``start()`` runs it.

        ``limit`` is the number of frames the pass reads (the witness checks the last of
        them); ``None`` is the whole clip.
        """
        super().__init__(daemon=True)
        self._source, self._stream, self._timing = source, stream, timing
        self._mode, self._witness, self._limit = mode, witness or {}, limit
        shape = (source.info.height, source.info.width, 3)
        self.ready: queue.Queue[Any] = queue.Queue()
        self.free: queue.Queue[Any] = queue.Queue()
        for _ in range(INPUT_BUFFERS if mode == "float" else buffers):
            self.free.put(np.empty(shape, np.float32) if mode == "float" else frame_buffer(source))
        self._raw = frame_buffer(source)
        self.frames = 0
        self.error: BaseException | None = None
        self.witnessed = 0

    def run(self) -> None:
        """Read until the end of the stream, then hand over the end marker."""
        try:
            while True:
                buffer = self.free.get()
                if buffer is _SENTINEL:
                    return
                target = self._raw if self._mode == "float" else buffer
                started = time.perf_counter()
                if not read_frame(self._stream, target):
                    break
                read_done = time.perf_counter()
                if self._timing.first_frame is None:
                    self._timing.first_frame = read_done
                self._timing.read.append(read_done - started)
                if self._mode == "float":
                    np.divide(
                        self._raw,
                        np.float32(255.0 if self._source.bit_depth == 8 else 65535.0),
                        out=buffer,
                        dtype=np.float32,
                    )
                    self._timing.convert_in.append(time.perf_counter() - read_done)
                    self._check_witness(self.frames, buffer)
                self.ready.put((self.frames, buffer))
                self.frames += 1
        except BaseException as exc:  # handed to the main loop, which re-raises it
            self.error = exc
        finally:
            self.ready.put(_SENTINEL)

    def _check_witness(self, index: int, image: NDArray[np.float32]) -> None:
        """Compare a frame's channel means with the analysis record's, if it names the frame."""
        last = (self._limit or self._source.frame_count) - 1
        if index % WITNESS_EVERY and index != last:
            return
        expected = self._witness.get(index)
        if expected is None:
            return
        means = np.mean(image, axis=(0, 1), dtype=np.float64)
        worst = float(np.max(np.abs(means - np.asarray(expected, dtype=np.float64))))
        if worst > WITNESS_TOLERANCE:
            raise StatisticsMismatchError(
                f"frame {index}: channel means {means.tolist()} differ from the analysis "
                f"record's {list(expected)} by {worst:.3g}: not the analysed frames"
            )
        self.witnessed += 1


class _Writer(threading.Thread):
    """Takes frames from the main loop, converts float ones to integers, writes them out.

    An integer frame (a pass-through) is written as it is and then handed to ``recycle``,
    the reader's free-buffer queue. :attr:`slots` bounds the output side: the main loop takes
    a slot before it computes (or forwards) a frame, and the writer gives it back once the
    frame is written (:data:`OUTPUT_FRAMES`).
    """

    def __init__(
        self,
        source: Source,
        stream: IO[bytes],
        timing: LoopTiming,
        recycle: queue.Queue[Any] | None = None,
    ) -> None:
        """Prepare the writer; ``start()`` runs it."""
        super().__init__(daemon=True)
        self._stream, self._timing, self._recycle = stream, timing, recycle
        shape = (source.info.height, source.info.width, 3)
        self._out = frame_buffer(source)
        self._scratch = np.empty(shape, np.float32)
        self.queue: queue.Queue[Any] = queue.Queue(maxsize=OUTPUT_FRAMES + 1)
        self.slots = threading.Semaphore(OUTPUT_FRAMES)
        self.frames = 0
        self.error: BaseException | None = None

    def run(self) -> None:
        """Write until the end marker, then close the pipe."""
        try:
            while True:
                item = self.queue.get()
                if item is _SENTINEL:
                    break
                started = time.perf_counter()
                if item.dtype == np.float32:
                    to_integer(item, self._out, self._scratch)
                    data = self._out
                    converted = time.perf_counter()
                    self._timing.convert_out.append(converted - started)
                else:
                    data, converted = item, started
                write_frame(self._stream, data)
                self._timing.write.append(time.perf_counter() - converted)
                self.frames += 1
                if data is item and self._recycle is not None:
                    self._recycle.put(item)
                self.slots.release()
        except BaseException as exc:  # handed to the main loop, which re-raises it
            self.error = exc
            # Let the main loop finish its puts (and keep the reader's buffers moving).
            while (item := self.queue.get()) is not _SENTINEL:
                if item.dtype != np.float32 and self._recycle is not None:
                    self._recycle.put(item)
                self.slots.release()
        finally:
            try:
                self._stream.close()
            except OSError as exc:
                self.error = self.error or exc


# --- the streaming staged analysis --------------------------------------------------------------


class StagedStream:
    """:func:`prototype.temporal.analyse_staged` over frames that arrive one at a time.

    ``analyse_staged`` measures stage 1 on every frame, smooths it, measures stage 2 on
    every frame with smoothed stage 1 supplied, and so on, so it holds every frame. Here a
    stage measures frame ``i`` as soon as the earlier stages' smoothed values at ``i``
    exist, and a stage's smoothed value at ``i`` is computed as soon as its measurements
    reach ``i + radius`` (:meth:`prototype.temporal.Smoother.radius`, the reach of the
    filter chain) or the end of the clip. The smoothed value is
    :meth:`~prototype.temporal.Smoother.apply` on the measurements in ``[i - radius,
    i + radius]`` (clipped to the clip), taken at ``i``: the filters at ``i`` read nothing
    outside that window, and where the window is clipped it is clipped at the clip's own
    ends, so the edge rule (``nearest``) sees what it sees on the whole series. The result
    is the same, bit for bit (``tests/test_prototype_clip.py``). A frame is dropped once
    the last stage has measured it: at most about ``(stages - 1) * radius + 1`` frames are
    held.

    Args:
        params: The parameter set (its method decides the stages, :data:`temporal.STAGES`).
        smoother: The temporal filter.
        frame_rate: Frames per second.
        backend: Where the measurements run.
    """

    def __init__(
        self, params: Params, smoother: Smoother, frame_rate: Fraction, backend: Backend
    ) -> None:
        """Prepare an empty stream."""
        self._params, self._smoother, self._rate = params, smoother, frame_rate
        self._backend = backend
        self._stages = temporal.STAGES[params.method]
        self._radius = smoother.radius(frame_rate)
        self._images: dict[int, Any] = {}
        self._measured: list[dict[str, list[float]]] = [{} for _ in self._stages]
        self._measured_count = [0 for _ in self._stages]
        self._smoothed: list[dict[str, list[float]]] = [{} for _ in self._stages]
        self._smoothed_count = [0 for _ in self._stages]
        self._count = 0
        self._ended = False
        self.peak_held = 0
        self.measure_s = [0.0 for _ in self._stages]
        self.smooth_s = 0.0

    @property
    def radius(self) -> int:
        """The smoother's reach in frames."""
        return self._radius

    def push(self, image: Any) -> None:
        """Add the next frame (a proxy, on the backend's device) and advance every stage.

        Args:
            image: The frame, float32 ``(H, W, 3)``.

        Raises:
            ClipError: The stream has already ended.
        """
        if self._ended:
            raise ClipError("no frame can be added after finish()")
        self._images[self._count] = image
        self._count += 1
        self.peak_held = max(self.peak_held, len(self._images))
        self._advance()

    def finish(self) -> tuple[Series, dict[str, Series]]:
        """End the stream, complete every stage and return what ``analyse_staged`` returns.

        Returns:
            The smoothed series of every stage together, and per stage name the series the
            stage measured before smoothing (its own fields only).

        Raises:
            ValueError: Fewer than :data:`temporal.MIN_FRAMES` frames were added.
        """
        if self._count < temporal.MIN_FRAMES:
            raise ValueError(
                f"a sequence analysis needs at least {temporal.MIN_FRAMES} frames, "
                f"got {self._count}"
            )
        self._ended = True
        self._advance()
        smoothed: Series = {}
        measured: dict[str, Series] = {}
        for number, stage in enumerate(self._stages):
            assert self._smoothed_count[number] == self._count
            measured[stage.name] = {
                name: np.asarray(values, dtype=np.float64)
                for name, values in self._measured[number].items()
            }
            smoothed.update(
                {
                    name: np.asarray(values, dtype=np.float64)
                    for name, values in self._smoothed[number].items()
                }
            )
        return smoothed, measured

    def _advance(self) -> None:
        """Measure and smooth every stage as far as the frames and earlier stages allow."""
        last = len(self._stages) - 1
        for number, stage in enumerate(self._stages):
            ready = self._count if number == 0 else self._smoothed_count[number - 1]
            while self._measured_count[number] < ready:
                index = self._measured_count[number]
                started = time.perf_counter()
                record = temporal.measure(
                    self._images[index], self._params, self._supplied(number, index), self._backend
                )
                self.measure_s[number] += time.perf_counter() - started
                for name, value in temporal.flatten(record).items():
                    if name.split(".", 1)[0] in stage.fields:
                        self._measured[number].setdefault(name, []).append(value)
                self._measured_count[number] += 1
                if number == last:
                    del self._images[index]
            started = time.perf_counter()
            self._smooth(number)
            self.smooth_s += time.perf_counter() - started

    def _supplied(self, number: int, index: int) -> Statistics | None:
        """The smoothed statistics of the stages before ``number`` at frame ``index``."""
        if number == 0:
            return None
        values = {
            name: series[index]
            for earlier in self._smoothed[:number]
            for name, series in earlier.items()
        }
        return temporal.unflatten(values)

    def _smooth(self, number: int) -> None:
        """Compute stage ``number``'s smoothed values that its measurements now determine."""
        measured = self._measured_count[number]
        total = self._count if self._ended and measured == self._count else None
        radius = self._radius
        while self._smoothed_count[number] < measured:
            index = self._smoothed_count[number]
            if total is None and index + radius >= measured:
                return
            low, high = max(0, index - radius), min(measured, index + radius + 1)
            for name, values in self._measured[number].items():
                window = np.asarray(values[low:high], dtype=np.float64)
                smoothed = self._smoother.apply(window, self._rate)[index - low]
                self._smoothed[number].setdefault(name, []).append(float(smoothed))
            self._smoothed_count[number] += 1


# --- the analysis pass --------------------------------------------------------------------------


@dataclass
class Analysis:
    """The result of :func:`analyse`.

    Attributes:
        smoothed: The smoothed series of every stage (one value per frame).
        measured: Per stage name, the series it measured before smoothing.
        frame_means: Each frame's channel means (float64, from the full-resolution float
            frame): the content witness the render checks.
        timing: The pass's clock readings.
        decode_command: The FFmpeg decode command.
        decoder_status: The decoder's exit status.
        peak_held: The most proxies held at once by :class:`StagedStream`.
        measure_s: Seconds spent measuring, per stage.
        smooth_s: Seconds spent smoothing.
        frames_limit: The ``frames`` argument (``None``: the whole clip).
    """

    smoothed: Series
    measured: dict[str, Series]
    frame_means: list[list[float]]
    timing: LoopTiming
    decode_command: list[str]
    decoder_status: int
    peak_held: int
    measure_s: list[float]
    smooth_s: float
    frames_limit: int | None


def analyse(
    source: Source,
    params: Params,
    backend: Backend,
    log_path: Path,
    hwaccel: str = "none",
    smoother: Smoother = SMOOTHER,
    frames: int | None = None,
    progress: Callable[[int], None] | None = None,
) -> Analysis:
    """Run the analysis pass: decode every frame, proxy it, compute the staged statistics.

    Per frame, on the main thread: the integer frame from the reader is copied to the
    backend's device, converted to float32 (:func:`to_float`), its channel means taken,
    area-averaged to the 540-line proxy (:func:`prototype.temporal.proxy`) and pushed into
    :class:`StagedStream`, whose measurements run on the device. The timed pass ends when
    the decoder has exited and the last smoothed value is computed.

    Args:
        source: The clip.
        params: The parameter set.
        backend: Where the proxies and statistics are computed.
        log_path: The decoder's log file (already checked).
        hwaccel: ``"none"`` or ``"cuda"`` (:func:`decode_command`).
        smoother: The temporal filter.
        frames: Analyse only the first this many frames.
        progress: Called with the frame count after each frame.

    Returns:
        The analysis.

    Raises:
        ClipError: The decode failed (:class:`PipeError` for a frame boundary or count
            error).
    """
    expected = source.frame_count if frames is None else min(frames, source.frame_count)
    command = decode_command(source, hwaccel, frames)
    stream = StagedStream(params, smoother, source.info.frame_rate, backend)
    timing = LoopTiming()
    xp = backend.xp
    means: list[list[float]] = []
    decoder = reader = None
    with log_path.open("wb") as log:
        try:
            timing.spawned = time.perf_counter()
            decoder = _spawn(command, log, None, subprocess.PIPE)
            reader = _Reader(source, decoder.stdout, timing, "raw")
            reader.start()
            while True:
                started = time.perf_counter()
                item = _take(reader.ready, "the decoder")
                got = time.perf_counter()
                if item is _SENTINEL:
                    break
                started = _bracketed(started, timing)
                _, raw = item
                image = to_float(backend.to_device(raw), xp, source.bit_depth)
                means.append([float(v) for v in xp.mean(image, axis=(0, 1), dtype=xp.float64)])
                stream.push(temporal.proxy(image))
                backend.synchronize()
                reader.free.put(raw)  # only once the device work on the frame has finished
                done = time.perf_counter()
                timing.wait_input.append(got - started)
                timing.core.append(done - got)
                timing.frames += 1
                timing.last_frame = done
                if progress is not None:
                    progress(timing.frames)
            reader.free.put(_SENTINEL)
            _join(reader, "the reader")
            if reader.error is not None:
                raise reader.error
            status = _finish(decoder, "the decoder")
            if status != 0:
                raise ClipError(f"the decoder failed (status {status}): {_log_tail(log_path)}")
            if timing.frames != expected:
                raise FrameCountError(
                    f"the decoder delivered {timing.frames} frames; {source.path.name} has "
                    f"{expected}"
                )
            smoothed, measured = stream.finish()
            backend.synchronize()
            timing.closed = time.perf_counter()
        finally:
            _stop(decoder)
            _release(reader, None)
    return Analysis(
        smoothed=smoothed,
        measured=measured,
        frame_means=means,
        timing=timing,
        decode_command=command,
        decoder_status=status,
        peak_held=stream.peak_held,
        measure_s=stream.measure_s,
        smooth_s=stream.smooth_s,
        frames_limit=frames,
    )


def analysis_record(
    source: Source, params: Params, analysis: Analysis, hwaccel: str, smoother: Smoother
) -> dict[str, Any]:
    """Build the analysis record the render reads (and the analysis timing figures).

    Args:
        source: The clip.
        params: The parameter set.
        analysis: The pass's result.
        hwaccel: The decode choice.
        smoother: The temporal filter.

    Returns:
        The JSON-ready record.
    """
    count = analysis.timing.frames
    footage = Fraction(count) / source.info.frame_rate
    return {
        "schema": ANALYSIS_SCHEMA,
        "tool": "tools/prototype/clip.py analyse",
        "written": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "source": source.identity(),
        "frames_analysed": count,
        "frames_limit": analysis.frames_limit,
        "pts_ticks": list(source.pts_ticks[:count]),
        "params": dataclasses.asdict(params),
        "method": params.method,
        "smoother": {
            "kind": smoother.kind,
            "window_s": smoother.window_s,
            "radius_frames": smoother.radius(source.info.frame_rate),
            "note": PROVISIONAL_NOTE,
        },
        "analysis": "STAGED (D97), streaming form of prototype.temporal.analyse_staged",
        "proxy": {"short_side": temporal.PROXY_SHORT_SIDE, "method": "temporal.proxy area mean"},
        "decode": {"hwaccel": hwaccel, "command": analysis.decode_command},
        "decoder_status": analysis.decoder_status,
        "peak_proxies_held": analysis.peak_held,
        "measure_s_per_stage": analysis.measure_s,
        "smooth_s": analysis.smooth_s,
        "timing": analysis.timing.record(footage),
        "frame_means": analysis.frame_means,
        "smoothed": {name: values.tolist() for name, values in analysis.smoothed.items()},
        "measured": {
            stage: {name: values.tolist() for name, values in series.items()}
            for stage, series in analysis.measured.items()
        },
    }


def check_statistics_record(
    record: Mapping[str, Any],
    source: Source,
    params: Params,
    hwaccel: str,
    frames: int | None,
    smoother: Smoother = SMOOTHER,
) -> None:
    """Refuse an analysis record that was not made on this clip with these settings.

    Args:
        record: The analysis record.
        source: The clip to render.
        params: The render's parameter set.
        hwaccel: The render's decode choice.
        frames: The render's frame limit (``None``: the whole clip).
        smoother: The smoothing the render expects to apply (:data:`SMOOTHER`).

    Raises:
        StatisticsMismatchError: The schema, the source identity (name, size,
            modification time, frame count, size, colour tags, time base, frame rate, bit
            depth), the pts list, the frame count analysed, the parameters, the full decode
            command, the decode choice, the analysis (STAGED, the 540-line
            proxy, the smoother) or the set of smoothed statistics (exactly the names the
            method's chain measures, :func:`statistic_names`) differ.
    """
    expected = source.frame_count if frames is None else min(frames, source.frame_count)
    if record.get("schema") != ANALYSIS_SCHEMA:
        raise StatisticsMismatchError(f"not an analysis record: schema {record.get('schema')!r}")
    theirs, ours = dict(record.get("source") or {}), source.identity()
    keys = ("name", "size_bytes", "mtime_ns", "frames", "width", "height", "tags")
    for key in (*keys, "time_base", "frame_rate", "bit_depth"):
        if theirs.get(key) != ours[key]:
            raise StatisticsMismatchError(
                f"the record was made on another file: {key} {theirs.get(key)!r} != {ours[key]!r}"
            )
    if record.get("frames_analysed") != expected:
        raise StatisticsMismatchError(
            f"the record analysed {record.get('frames_analysed')} frames; the render needs "
            f"{expected}"
        )
    if record.get("pts_ticks") != list(source.pts_ticks[:expected]):
        raise StatisticsMismatchError("the record's pts list differs from the source's")
    if record.get("params") != dataclasses.asdict(params):
        raise StatisticsMismatchError("the record was made with other parameters")
    if dict(record.get("decode") or {}).get("hwaccel") != hwaccel:
        raise StatisticsMismatchError(
            f"the record was decoded with hwaccel {dict(record.get('decode') or {}).get('hwaccel')}"
            f", the render decodes with {hwaccel}: the frames would not be the same bytes"
        )
    if dict(record.get("decode") or {}).get("command") != decode_command(source, hwaccel, frames):
        raise StatisticsMismatchError(
            "the record's decode command differs from the render's: the frames would not be "
            "the same bytes"
        )
    if not str(record.get("analysis", "")).startswith("STAGED"):
        raise StatisticsMismatchError(f"the record's analysis is {record.get('analysis')!r}")
    if dict(record.get("proxy") or {}).get("short_side") != temporal.PROXY_SHORT_SIDE:
        raise StatisticsMismatchError(f"the record's proxy is {record.get('proxy')!r}")
    made = dict(record.get("smoother") or {})
    if (made.get("kind"), made.get("window_s")) != (smoother.kind, smoother.window_s):
        raise StatisticsMismatchError(
            f"the record was smoothed with {made.get('kind')} {made.get('window_s')} s, "
            f"the render applies {smoother.label}"
        )
    smoothed = record.get("smoothed") or {}
    if set(smoothed) != set(statistic_names(params)):
        raise StatisticsMismatchError(
            f"the record's smoothed statistics {sorted(smoothed)} are not the "
            f"{params.method} chain's {sorted(statistic_names(params))}"
        )
    if any(len(values) != expected for values in smoothed.values()):
        raise StatisticsMismatchError("the record's smoothed series do not hold one value a frame")
    if len(record.get("frame_means") or []) != expected:
        raise StatisticsMismatchError("the record's frame means do not hold one entry a frame")


def statistic_names(params: Params) -> tuple[str, ...]:
    """Return the flattened names of every whole-frame statistic the method's chain uses.

    They are read off :func:`prototype.temporal.statistics_of` on a small gradient image
    (the names do not depend on the values): for Ancuti 2018 the compensation means and
    alpha, then for both methods the white-balance means and gains, the N{} bounds and both
    saliency means.

    Args:
        params: The parameter set (its method and blue compensation decide the names).

    Returns:
        The names, in :func:`prototype.temporal.flatten`'s order.
    """
    ramp = np.linspace(0.1, 0.9, 64 * 96 * 3, dtype=np.float32).reshape(64, 96, 3)
    return tuple(temporal.flatten(temporal.statistics_of(ramp, params)))


def per_frame_statistics(record: Mapping[str, Any]) -> list[Statistics]:
    """Return each frame's smoothed statistics from an analysis record.

    Args:
        record: The analysis record (checked by :func:`check_statistics_record`).

    Returns:
        One :class:`prototype.pipeline.Statistics` per frame (every name through
        :func:`prototype.temporal.unflatten`, which refuses an unknown one).
    """
    smoothed: Mapping[str, Sequence[float]] = record["smoothed"]
    count = len(next(iter(smoothed.values())))
    return [
        temporal.unflatten({name: float(values[index]) for name, values in smoothed.items()})
        for index in range(count)
    ]


# --- the export loop and the split passes ------------------------------------------------------


@dataclass
class Export:
    """The result of :func:`export`, :func:`passthrough` or :func:`decode_only`.

    Attributes:
        timing: The pass's clock readings.
        decode_command: The decoder's command.
        encode_command: The encoder's command (``None`` for a decode-only pass).
        decoder_status: The decoder's exit status.
        encoder_status: The encoder's exit status (``None`` for a decode-only pass).
        frames_written: Frames written to the encoder.
        witnessed: Frames whose channel means were checked against the analysis record.
        resident: Whether the device-resident variant ran.
    """

    timing: LoopTiming
    decode_command: list[str]
    encode_command: list[str] | None
    decoder_status: int
    encoder_status: int | None
    frames_written: int
    witnessed: int = 0
    resident: bool = False


def export(
    source: Source,
    output: Path,
    params: Params,
    statistics: Sequence[Statistics] | None,
    backend: Backend,
    logs: tuple[Path, Path],
    frame_means: Sequence[Sequence[float]] | None = None,
    hwaccel: str = "none",
    resident: bool = False,
    frames: int | None = None,
    progress: Callable[[int], None] | None = None,
) -> Export:
    """Run the export loop: decode -> correct each frame -> encode and mux (see the module).

    The production-shaped core is ``correct(frame, params, backend, statistics=...)`` on
    the host float frame, which copies it to the device and every array of the result
    back (as WP1.2A timed it); ``resident`` runs the device-resident variant instead:
    the frame copied to the device, ``correct()`` there, and only the output copied back.

    Args:
        source: The clip.
        output: The output MP4 (already checked by the caller).
        params: The parameter set.
        statistics: Each frame's smoothed statistics (:func:`per_frame_statistics`);
            ``None`` lets every frame measure its own.
        backend: Where the correction runs.
        logs: The decoder's and the encoder's log files (already checked).
        frame_means: The analysis record's frame means, for the content witness.
        hwaccel: The decode choice.
        resident: Run the device-resident variant.
        frames: Export only the first this many frames.
        progress: Called with the frame count after each frame.

    Returns:
        The export's result.

    Raises:
        ClipError: A process failed, a pipe broke, a frame count or boundary is wrong
            (:class:`PipeError`), or the content witness failed
            (:class:`StatisticsMismatchError`).
    """
    expected = source.frame_count if frames is None else min(frames, source.frame_count)
    if statistics is not None and len(statistics) != expected:
        raise StatisticsMismatchError(f"{len(statistics)} statistics records for {expected} frames")
    witness = None if frame_means is None else dict(enumerate(frame_means))

    def core(index: int, image: NDArray[np.float32]) -> NDArray[np.float32]:
        supplied = None if statistics is None else statistics[index]
        if resident:
            on_device = correct(backend.to_device(image), params, statistics=supplied)
            out = backend.to_host(on_device.output)
        else:
            out = correct(image, params, backend, statistics=supplied).output
        backend.synchronize()
        return np.asarray(out, dtype=np.float32)

    result = _run_pipeline(source, output, logs, hwaccel, frames, "float", core, witness, progress)
    result.resident = resident
    return result


def passthrough(
    source: Source,
    output: Path,
    logs: tuple[Path, Path],
    hwaccel: str = "none",
    frames: int | None = None,
    progress: Callable[[int], None] | None = None,
) -> Export:
    """Run the split's encode pass: the decoded frames fed to the encoder unchanged.

    The same processes, pipes and threads as :func:`export`, with no float conversion and
    no correction: each integer frame read from the decoder is written to the encoder.

    Args:
        source: The clip.
        output: The output MP4 (already checked by the caller).
        logs: The decoder's and the encoder's log files (already checked).
        hwaccel: The decode choice.
        frames: Only the first this many frames.
        progress: Called with the frame count after each frame.

    Returns:
        The pass's result.

    Raises:
        ClipError: As :func:`export`.
    """
    return _run_pipeline(source, output, logs, hwaccel, frames, "raw", None, None, progress)


def spool(
    source: Source, path: Path, log_path: Path, hwaccel: str = "none", frames: int | None = None
) -> list[str]:
    """Decode the clip to a raw RGB file: the input of the split's encode-only pass (untimed).

    The decode is :func:`decode_command`'s with the file ``path`` as output in place of the
    pipe (``-y`` for a path the caller has checked); the file must then hold exactly the
    clip's frames.

    Args:
        source: The clip.
        path: The spool file (already checked by the caller).
        log_path: The decoder's log file (already checked).
        hwaccel: The decode choice.
        frames: Only the first this many frames.

    Returns:
        The command.

    Raises:
        ClipError: FFmpeg failed or the file is not a whole number of the clip's frames
            (:class:`PipeError`).
    """
    expected = source.frame_count if frames is None else min(frames, source.frame_count)
    command = [*decode_command(source, hwaccel, frames)[:-1], "-y", str(path)]
    with log_path.open("wb") as log:
        process = _spawn(command, log, None, None)
        try:
            status = _finish(process, "the spool decoder")
        finally:
            _stop(process)
    if status != 0:
        raise ClipError(f"the spool decode failed (status {status}): {_log_tail(log_path)}")
    size = path.stat().st_size
    if size != expected * source.frame_bytes:
        raise PipeError(
            f"the spool holds {size} bytes, not {expected} frames of {source.frame_bytes}"
        )
    return command


def encode_only(
    source: Source,
    spool_path: Path,
    output: Path,
    logs: tuple[Path, Path],
    frames: int | None = None,
    progress: Callable[[int], None] | None = None,
) -> Export:
    """Run the split's encode pass: frames read from a spool (:func:`spool`), fed unchanged.

    The export's reader and writer threads, buffers and encoder, with the reader on the
    spool file instead of a decoder, so no decode runs while the encoder is timed.

    Args:
        source: The clip.
        spool_path: The spool file.
        output: The output MP4 (already checked by the caller).
        logs: An unused decoder log and the encoder's log file (already checked).
        frames: Only the first this many frames (the spool must hold exactly those).
        progress: Called with the frame count after each frame.

    Returns:
        The pass's result (``decode_command`` names the spool).

    Raises:
        ClipError: As :func:`export`.
    """
    return _run_pipeline(
        source, output, logs, "none", frames, "raw", None, None, progress, spool_path
    )


def decode_only(
    source: Source,
    log_path: Path,
    hwaccel: str = "none",
    frames: int | None = None,
    progress: Callable[[int], None] | None = None,
) -> Export:
    """Run the split's decode pass: decode to the pipe, read every frame whole, discard it.

    Args:
        source: The clip.
        log_path: The decoder's log file (already checked).
        hwaccel: The decode choice.
        frames: Only the first this many frames.
        progress: Called with the frame count after each frame.

    Returns:
        The pass's result (``encode_command`` and ``encoder_status`` are ``None``).

    Raises:
        ClipError: The decoder failed or a frame boundary or count is wrong.
    """
    expected = source.frame_count if frames is None else min(frames, source.frame_count)
    command = decode_command(source, hwaccel, frames)
    timing = LoopTiming()
    decoder = reader = None
    with log_path.open("wb") as log:
        try:
            timing.spawned = time.perf_counter()
            decoder = _spawn(command, log, None, subprocess.PIPE)
            # The export's reader thread and buffer count; each frame's buffer goes straight back.
            reader = _Reader(source, decoder.stdout, timing, "raw", buffers=PASSTHROUGH_BUFFERS)
            reader.start()
            while True:
                started = time.perf_counter()
                item = _take(reader.ready, "the decoder")
                got = time.perf_counter()
                if item is _SENTINEL:
                    break
                reader.free.put(item[1])
                timing.wait_input.append(got - _bracketed(started, timing))
                timing.frames += 1
                timing.last_frame = got
                if progress is not None:
                    progress(timing.frames)
            reader.free.put(_SENTINEL)
            _join(reader, "the reader")
            if reader.error is not None:
                raise reader.error
            status = _finish(decoder, "the decoder")
            timing.closed = time.perf_counter()
        finally:
            _stop(decoder)
            _release(reader, None)
    if status != 0:
        raise ClipError(f"the decoder failed (status {status}): {_log_tail(log_path)}")
    if timing.frames != expected:
        raise FrameCountError(
            f"the decoder delivered {timing.frames} frames; {source.path.name} has {expected}"
        )
    return Export(timing, command, None, status, None, 0)


def partial_name(output: Path) -> Path:
    """Return the temporary name an export writes before it is complete.

    Args:
        output: The final output path.

    Returns:
        ``<stem>.partial<suffix>`` in the same folder (the suffix keeps the muxer's format).
    """
    return output.with_name(f"{output.stem}.partial{output.suffix}")


def _run_pipeline(
    source: Source,
    output: Path,
    logs: tuple[Path, Path],
    hwaccel: str,
    frames: int | None,
    mode: str,
    core: Callable[[int, NDArray[np.float32]], NDArray[np.float32]] | None,
    witness: Mapping[int, Sequence[float]] | None,
    progress: Callable[[int], None] | None,
    spool: Path | None = None,
) -> Export:
    """Decoder (or a spool file) -> reader thread -> main loop (``core``) -> writer -> encoder.

    Per frame the main loop takes an output slot (``wait_output``), takes the next frame
    (``wait_input``), runs the core and queues the result (``core``). ``last_frame`` is the
    moment the last frame was queued, so the reader's end-of-stream, the threads' ends and
    the processes' exits fall into the tail.

    The encoder writes :func:`partial_name` and the file is renamed to ``output`` only when
    the pass has succeeded (both processes exited 0, every frame written), after the bracket
    has closed. An existing ``output`` is never overwritten, and the partial file is removed
    on every failure.

    Raises:
        ClipError: ``output`` already exists, or the pass failed (see :func:`export`).
    """
    expected = source.frame_count if frames is None else min(frames, source.frame_count)
    if output.exists():
        raise ClipError(f"{output.name} already exists; an export never overwrites a file")
    partial = partial_name(output)
    partial.unlink(missing_ok=True)  # a leftover of a killed run, under this pass's own name
    decode = decode_command(source, hwaccel, frames)
    encode = encode_command(source, partial, frames)
    timing = LoopTiming()
    done = False
    try:
        result = _run_stages(
            source, logs, decode, encode, expected, mode, core, witness, progress, spool, timing
        )
        if output.exists():
            raise ClipError(f"{output.name} appeared during the export; refusing to replace it")
        partial.rename(output)
        done = True
        return result
    finally:
        if not done:
            partial.unlink(missing_ok=True)


def _run_stages(
    source: Source,
    logs: tuple[Path, Path],
    decode: list[str],
    encode: list[str],
    expected: int,
    mode: str,
    core: Callable[[int, NDArray[np.float32]], NDArray[np.float32]] | None,
    witness: Mapping[int, Sequence[float]] | None,
    progress: Callable[[int], None] | None,
    spool: Path | None,
    timing: LoopTiming,
) -> Export:
    """The stages of :func:`_run_pipeline`: spawn, run the loop, reap, check."""
    decoder = encoder = reader = writer = None
    spooled = None
    with logs[0].open("wb") as decode_log, logs[1].open("wb") as encode_log:
        try:
            timing.spawned = time.perf_counter()
            encoder = _spawn(encode, encode_log, subprocess.PIPE, None)
            if spool is None:
                decoder = _spawn(decode, decode_log, None, subprocess.PIPE)
                stream = decoder.stdout
            else:
                spooled = stream = spool.open("rb", buffering=0)
            # A pass-through holds as many integer frames as the export holds frames in flight.
            reader = _Reader(source, stream, timing, mode, witness, expected, PASSTHROUGH_BUFFERS)
            writer = _Writer(source, encoder.stdin, timing, None if core else reader.free)
            reader.start()
            writer.start()
            while True:
                started = time.perf_counter()
                _slot(writer, "the encoder")
                slotted = time.perf_counter()
                item = _take(reader.ready, "the decoder")
                got = time.perf_counter()
                if item is _SENTINEL:
                    writer.slots.release()
                    break
                index, image = item
                out = image if core is None else core(index, image)
                if core is not None:
                    reader.free.put(image)
                _give(writer.queue, out, "the encoder")
                handed = time.perf_counter()
                begun = _bracketed(started, timing)  # the first frame counts from the bracket
                slot_ready = max(slotted, begun)
                timing.wait_output.append(slot_ready - begun)
                timing.wait_input.append(got - slot_ready)
                timing.core.append(handed - got)
                timing.frames += 1
                timing.last_frame = handed
                if writer.error is not None:
                    break
                if progress is not None:
                    progress(timing.frames)
            reader.free.put(_SENTINEL)
            _give(writer.queue, _SENTINEL, "the encoder")
            _join(writer, "the writer")
            _join(reader, "the reader")
            for error in (reader.error, writer.error):
                if isinstance(error, OSError):
                    raise ClipError(f"a pipe failed: {error}") from error
                if error is not None:
                    raise error
            decoder_status = 0 if decoder is None else _finish(decoder, "the decoder")
            encoder_status = _finish(encoder, "the encoder")
            timing.closed = time.perf_counter()
        finally:
            _stop(decoder, encoder)
            _release(reader, writer)
            if spooled is not None:
                spooled.close()
    if decoder_status != 0:
        raise ClipError(f"the decoder failed (status {decoder_status}): {_log_tail(logs[0])}")
    if encoder_status != 0:
        raise ClipError(f"the encoder failed (status {encoder_status}): {_log_tail(logs[1])}")
    if timing.frames != expected or writer.frames != expected:
        raise FrameCountError(
            f"{timing.frames} frames decoded and {writer.frames} written; "
            f"{source.path.name} has {expected}"
        )
    return Export(
        timing,
        decode if spool is None else ["(spool)", str(spool)],
        encode,
        decoder_status,
        encoder_status,
        writer.frames,
        reader.witnessed,
    )


def witness_indices(count: int, wanted: int = WITNESS_FRAMES) -> list[int]:
    """Return up to ``wanted`` frame indices spread evenly over ``count`` frames, ends included.

    Args:
        count: Frames in the clip.
        wanted: How many indices.

    Returns:
        Sorted distinct indices, ``0`` and ``count - 1`` among them.
    """
    return sorted({round(float(x)) for x in np.linspace(0, count - 1, min(wanted, count))})


def psnr(first: NDArray[Any], second: NDArray[Any]) -> float:
    """Return the PSNR of two integer images of the same type, in dB (``inf`` when equal).

    Args:
        first: An image, ``uint8`` or ``uint16``.
        second: The other, same shape and type.

    Returns:
        ``10 log10(maximum^2 / MSE)`` over every sample.
    """
    maximum = float(np.iinfo(first.dtype).max)
    error = float(np.mean((first.astype(np.float64) - second.astype(np.float64)) ** 2))
    return math.inf if error == 0.0 else 10.0 * math.log10(maximum * maximum / error)


def reference_frames(index: int, count: int) -> list[int]:
    """Return the three frames whose expected images form frame ``index``'s reference encode.

    ``index - 1, index, index + 1``, so that ``index`` is not the reference's I-frame; at the
    clip's first frame ``0, 1, 2`` and at its last ``count - 3, count - 2, count - 1``.

    Args:
        index: The checked frame.
        count: Frames in the clip (at least 3).

    Returns:
        The three indices, ascending.
    """
    first = min(max(index - 1, 0), count - 3)
    return [first, first + 1, first + 2]


def picture_types(output: Source) -> list[str]:
    """Return the output's picture type per frame, in presentation order (``I``, ``P``, ``B``).

    Read with ``ffprobe -show_entries frame=pict_type`` on the output (it decodes the stream).

    Args:
        output: The export.

    Returns:
        One type per frame.

    Raises:
        ClipError: ``ffprobe`` fails or reports another number of frames.
    """
    try:
        document = run_ffprobe(
            ["-select_streams", "v:0", "-show_entries", "frame=pict_type", str(output.path)]
        )
    except Exception as exc:  # container_spike's ProbeError
        raise ClipError(f"cannot read the picture types of {output.path.name}: {exc}") from None
    types = [str(frame.get("pict_type", "?")) for frame in document.get("frames", [])]
    if len(types) != output.frame_count:
        raise ClipError(f"{len(types)} picture types for {output.frame_count} frames")
    return types


def gop_start(types: Sequence[str], index: int) -> int:
    """Return the last I-frame at or before ``index`` (0 when there is none).

    Args:
        types: The output's picture types (:func:`picture_types`).
        index: A frame.

    Returns:
        The index of the GOP's I-frame.
    """
    return next((j for j in range(index, -1, -1) if types[j] == "I"), 0)


def next_anchor(types: Sequence[str], index: int) -> int:
    """Return the first I- or P-frame after ``index`` (the clip's last frame when there is none).

    A B-frame is predicted from the anchor after it, so a reference encode that stops before
    that anchor does not code the frame as the export did.

    Args:
        types: The output's picture types (:func:`picture_types`).
        index: A frame.

    Returns:
        The anchor's index, at least ``index``.
    """
    return next((j for j in range(index + 1, len(types)) if types[j] in ("I", "P")), len(types) - 1)


def output_witness(
    source: Source,
    output: Source,
    statistics: Sequence[Statistics],
    params: Params,
    backend: Backend,
    indices: Sequence[int],
    reference_path: Path,
    margin_db: float = WITNESS_MARGIN_DB,
) -> dict[str, Any]:
    """Check exported frames against the corrected source frames, after the export (untimed).

    For each index ``i``:
    - output frame ``i`` is decoded (:func:`decode_frames`, the export's own conversion to RGB);
    - the source frames are decoded and corrected exactly as the export corrects them
      (:func:`to_float`, ``correct(..., statistics=statistics[j])``, :func:`to_integer`): the
      EXPECTED frames;
    - the REFERENCE: the expected frames from the export's GOP start (the last I-frame at or
      before ``i`` in the OUTPUT's picture types, :func:`picture_types`) through the next
      anchor after ``i`` (:func:`next_anchor`, so a B-frame keeps the future frame it is
      predicted from) are encoded through the export's own encode chain
      (:func:`encode_command`; the source is decoded :data:`WITNESS_CHUNK` frames at a time,
      about 380 MiB at 4K, and of the expected frames only ``i - 1 .. i + 1`` are kept) and
      decoded: ``ref_i = PSNR(decoded expected i, expected i)``, the encoder's own
      loss on frame ``i`` in its own coding position. The reference's picture type at ``i`` is
      read back and recorded beside the output's;
    - ``own_i = PSNR(output i, expected i)``.

    Frame ``i`` passes when ``own_i >= ref_i - margin_db``, ``own_i >=``
    :data:`WITNESS_SANITY_DB`, and ``own_i`` is strictly higher than its PSNR against the
    expected frames ``i - 1`` and ``i + 1`` (those that exist). So a frame that is not the
    corrected source frame, sits at another position, or was corrected with another frame's
    statistics fails. This covers what the in-loop witness does not: the writer, the integer
    conversion, the encoder and the muxer.

    Each row also keeps the criteria this one replaced, for the record: the first absolute
    floor (:data:`FIRST_FLOOR_DB`), the 3-frame reference (the expected frames of
    :func:`reference_frames` encoded alone, which codes ``i`` next to a fresh I-frame), and the
    GOP-start reference that stops at ``i + 1`` (which can cut a B-frame off its anchor).

    Args:
        source: The clip that was exported.
        output: The export, opened with :func:`open_source`.
        statistics: The per-frame statistics the export applied.
        params: The parameters the export used.
        backend: Where to correct.
        indices: The frame indices to check.
        reference_path: Where the reference encodes are written (checked by the caller;
            overwritten for each frame and removed at the end).
        margin_db: The margin below the reference.

    Returns:
        The record: the rule, one row per index and ``passed``.

    Raises:
        ClipError: The output's frame count differs from the statistics', or a decode or a
            reference encode fails.
    """
    count = len(statistics)
    if output.frame_count != count:
        raise ClipError(f"the output has {output.frame_count} frames, the statistics {count}")
    if count < 3:
        raise ClipError("the output witness needs at least 3 frames")
    scratch = np.empty((source.info.height, source.info.width, 3), np.float32)

    def expect(frame: NDArray[Any], j: int) -> NDArray[Any]:
        corrected = correct(
            to_float(frame, np, source.bit_depth), params, backend, statistics=statistics[j]
        )
        out = np.empty_like(frame)
        to_integer(np.asarray(corrected.output, dtype=np.float32), out, scratch)
        return out

    types = picture_types(output)
    rows: list[dict[str, Any]] = []
    try:
        for index in indices:
            (exported,), _ = decode_frames(output, index, 1)
            first = gop_start(types, index)
            ends = [next_anchor(types, index), min(index + 1, count - 1)]
            short_path = reference_path.with_name(
                f"{reference_path.stem}-i1{reference_path.suffix}"
            )
            keep = _gop_reference(source, first, ends, index, expect, [reference_path, short_path])
            reference = open_source(reference_path)
            (decoded,), _ = decode_frames(reference, index - first, 1)
            ref = psnr(decoded, keep[index])
            reference_type = picture_types(reference)[index - first]
            (decoded_short,), _ = decode_frames(open_source(short_path), index - first, 1)
            ref_i1 = psnr(decoded_short, keep[index])
            three = reference_frames(index, count)
            for j in [*three, index - 1]:
                if 0 <= j < count and j not in keep:
                    (frame,), _ = decode_frames(source, j, 1)
                    keep[j] = expect(frame, j)
            short = _reference_encode(source, [keep[j] for j in three], reference_path)
            ref3 = psnr(short[three.index(index)], keep[index])
            own = psnr(exported, keep[index])
            neighbours = {j: psnr(exported, keep[j]) for j in (index - 1, index + 1) if j in keep}
            threshold = max(ref - margin_db, WITNESS_SANITY_DB)
            rows.append(
                {
                    "index": index,
                    "picture_type": types[index],
                    "reference_picture_type": reference_type,
                    "gop_start": first,
                    "reference_frames": [first, ends[0]],
                    "own_db": own,
                    "ref_db": ref,
                    "margin_db": margin_db,
                    "threshold_db": threshold,
                    "neighbours_db": {str(j): v for j, v in neighbours.items()},
                    "match_ok": own >= threshold,
                    "order_ok": all(own > v for v in neighbours.values()),
                    "misplaced": any(v >= own and v >= threshold for v in neighbours.values()),
                    "ref_i1_db": ref_i1,
                    "match_i1_ok": own >= max(ref_i1 - margin_db, WITNESS_SANITY_DB),
                    "ref3_db": ref3,
                    "relative3_ok": own >= max(ref3 - margin_db, WITNESS_SANITY_DB),
                    "first_floor_ok": own >= FIRST_FLOOR_DB,
                }
            )
    finally:
        reference_path.unlink(missing_ok=True)
        reference_path.with_name(f"{reference_path.stem}-i1{reference_path.suffix}").unlink(
            missing_ok=True
        )
    return {
        "check": (
            "own_i = PSNR(output i, expected i), expected = correct(source i, statistics i); "
            "pass: own_i >= max(ref_i - margin, sanity) and own_i > PSNR against expected i +- 1"
        ),
        "reference": (
            "ref_i = PSNR(decoded expected i, expected i), the expected frames from the export's "
            "GOP start (the last I-frame at or before i in the output's picture types) through "
            "the next I or P anchor after i, encoded through the export's own encode chain"
        ),
        "picture_types_from": "ffprobe -select_streams v:0 -show_entries frame=pict_type <output>",
        "margin_db": margin_db,
        "margin_basis": WITNESS_MARGIN_BASIS,
        "sanity_floor_db": WITNESS_SANITY_DB,
        "replaced_criteria": {
            "first_floor_db": FIRST_FLOOR_DB,
            "first_floor": (
                "absolute 28 dB from WP1.5's identity re-encode; failed GX011627 frame 30 at "
                "27.79 dB, whose encode-alone loss is 28.76 dB (row field first_floor_ok)"
            ),
            "three_frame_reference": (
                "ref3_i from the expected i-1, i, i+1 encoded alone; unrepresentative: it codes i "
                "next to a fresh I-frame, while the export has GOP 250 with B and P frames (row "
                "fields ref3_db, relative3_ok)"
            ),
            "gop_start_through_i_plus_1": (
                "the orchestrator's ruled reference (row fields ref_i1_db, match_i1_ok); it stops "
                "a B-frame before its future anchor; extended to the anchor after Reviewer A "
                "(remediation round 2), which reproduced GX011627 frame 30 bit for bit"
            ),
            "sequence": "each was replaced before the next re-scoring; the last change is for "
            "the orchestrator to adjudicate at the gate",
        },
        "frames_checked": len(rows),
        "rows": rows,
        "min_own_db": min(row["own_db"] for row in rows),
        "min_own_minus_ref_db": min(row["own_db"] - row["ref_db"] for row in rows),
        "passed": all(row["match_ok"] and row["order_ok"] for row in rows),
        "order_passed": all(row["order_ok"] and not row["misplaced"] for row in rows),
        "relative3_passed": all(row["relative3_ok"] for row in rows),
        "i_plus_1_passed": all(row["match_i1_ok"] for row in rows),
        "reference_types_match": all(
            row["reference_picture_type"] == row["picture_type"] for row in rows
        ),
        "first_floor_passed": all(row["first_floor_ok"] for row in rows),
    }


WITNESS_CHUNK = 16
"""Source frames decoded at a time while a GOP-start reference is streamed to the encoder."""


def _gop_reference(
    source: Source,
    first: int,
    ends: Sequence[int],
    index: int,
    expect: Callable[[NDArray[Any], int], NDArray[Any]],
    paths: Sequence[Path],
) -> dict[int, NDArray[Any]]:
    """Encode the expected frames ``first..ends[k]`` through the export's chain into ``paths[k]``.

    The frames are decoded :data:`WITNESS_CHUNK` at a time, corrected once (``expect``) and
    written to every encoder whose end has not passed; only frames ``index - 1 .. index + 1``
    are kept.

    Returns:
        The kept expected frames by index.

    Raises:
        ClipError: An encoder fails.
    """
    keep: dict[int, NDArray[Any]] = {}
    encoders: list[Any] = []
    last = max(ends)
    try:
        for path, end in zip(paths, ends, strict=True):
            command = encode_command(source, path, end - first + 1)
            encoders.append(_spawn(command, subprocess.DEVNULL, subprocess.PIPE, None))
        for chunk in range(first, last + 1, WITNESS_CHUNK):
            frames, _ = decode_frames(source, chunk, min(WITNESS_CHUNK, last + 1 - chunk))
            for offset, frame in enumerate(frames):
                j = chunk + offset
                expected = expect(frame, j)
                for encoder, end in zip(encoders, ends, strict=True):
                    if j <= end:
                        write_frame(encoder.stdin, expected)
                        if j == end:
                            encoder.stdin.close()
                if index - 1 <= j <= index + 1:
                    keep[j] = expected
        statuses = [_finish(encoder, "a reference encoder") for encoder in encoders]
    finally:
        _stop(*encoders)
    if any(statuses):
        raise ClipError(f"a reference encode failed (statuses {statuses})")
    return keep


def _reference_encode(
    source: Source, frames: Sequence[NDArray[Any]], path: Path
) -> list[NDArray[Any]]:
    """Encode frames through the export's own encode chain and decode them back.

    Args:
        source: The clip (the chain's tags, size, rate and muxed streams come from it).
        frames: The integer frames, in order.
        path: The output file (checked by the caller; overwritten).

    Returns:
        The decoded frames, in order.

    Raises:
        ClipError: The encode fails or does not give the frames back.
    """
    command = encode_command(source, path, len(frames))
    done = subprocess.run(
        command,
        input=b"".join(np.ascontiguousarray(frame).tobytes() for frame in frames),
        capture_output=True,
        env=tool_env(),
        check=False,
    )
    if done.returncode != 0:
        tail = done.stderr.decode("utf-8", errors="replace").strip()[-300:]
        raise ClipError(f"the reference encode failed (status {done.returncode}): {tail}")
    decoded, _ = decode_frames(open_source(path), 0, len(frames))
    return decoded


def require_witness(record: Mapping[str, Any]) -> None:
    """Raise the named error for a failed output witness record.

    Args:
        record: An :func:`output_witness` record.

    A frame that matches a neighbour's expected frame at its threshold or better, and at
    least as well as its own, is MISPLACED (a frame out of order): that is reported first. A
    frame that matches its own expected frame below the threshold is a MISMATCH (for example
    corrected with other statistics). A frame above the threshold that still scores no better
    than a neighbour is an order failure too.

    Raises:
        OutputOrderError: A frame is misplaced, or scores no better than a neighbour.
        OutputMismatchError: A frame scored below its threshold against its expected frame.
    """
    misplaced = [row["index"] for row in record["rows"] if row["misplaced"]]
    if misplaced:
        raise OutputOrderError(f"output frames {misplaced} match a neighbour's expected frame")
    low = [row["index"] for row in record["rows"] if not row["match_ok"]]
    if low:
        raise OutputMismatchError(
            f"output frames {low} score below the encoder's own loss less "
            f"{record['margin_db']} dB against the corrected source"
        )
    unordered = [row["index"] for row in record["rows"] if not row["order_ok"]]
    if unordered:
        raise OutputOrderError(f"output frames {unordered} score no better than a neighbour")


def run_witness(
    run_record: Path, roots: OutputRoots, backend: Backend, wanted: int = WITNESS_FRAMES
) -> Path:
    """Run the output witness on an existing export and write ``output-witness.json`` beside it.

    The run record (a ``bench.py --mode end-to-end`` record or a ``clip.py render`` run
    record) names the source, the analysis record and the output (looked for beside the run
    record when the recorded path is gone, as after a moved run folder; the record notes it).
    The analysis record is
    checked against the source (:func:`check_statistics_record`) and supplies the parameters
    and the per-frame statistics. Untimed: it runs after the export, on its file.

    Args:
        run_record: The export's run record.
        roots: The output roots (the record is written into the output's folder).
        backend: Where to correct.
        wanted: How many frame indices to check.

    Returns:
        The witness record's path.

    Raises:
        ClipError: A record does not fit, or a decode fails.
        OutputWitnessError: The witness failed (the record is written first).
    """
    run = json.loads(run_record.read_text(encoding="utf-8"))
    identity = run["source"]
    recorded = Path(identity["path"])
    footage = roots.footage.resolve()
    inside = footage in recorded.resolve().parents
    source = open_source(resolve_clip(identity["stem"] if inside else str(recorded), roots.footage))
    analysis = json.loads(Path(run["statistics"]).read_text(encoding="utf-8"))
    params = Params(**analysis["params"])
    hwaccel = dict(analysis.get("decode") or {}).get("hwaccel", "none")
    check_statistics_record(analysis, source, params, hwaccel, run.get("frames_limit"))
    output_path = Path(run["output"])
    relocated = None
    if not output_path.exists() and (run_record.parent / output_path.name).is_file():
        # The run's folder was moved after the run (as W4's were); the output sits beside it.
        relocated, output_path = str(output_path), run_record.parent / output_path.name
    output = open_source(output_path)
    statistics = per_frame_statistics(analysis)
    reference = roots.check(output_path.parent / "witness-reference.mp4")
    roots.check(output_path.parent / "witness-reference-i1.mp4")  # the through-i+1 reference
    record = output_witness(
        source,
        output,
        statistics,
        params,
        backend,
        witness_indices(len(statistics), wanted),
        reference,
    )
    record |= {
        "tool": "tools/prototype/clip.py witness (untimed, after the export)",
        "written": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "run_record": str(run_record),
        "output": str(output_path),
        "output_recorded_as": relocated,
        "statistics": run["statistics"],
        "source": source.identity(),
        "backend": backend.name,
    }
    path = output_path.parent / "output-witness.json"
    roots.write_text(path, json.dumps(record, indent=1) + "\n")
    require_witness(record)
    return path


def compare_output(source: Path, output: Path, folder: Path, roots: OutputRoots) -> dict[str, Any]:
    """Compare the export with its source (``container_spike.compare``) and write the record.

    Args:
        source: The source file.
        output: The export.
        folder: Where ``<output stem>.compare.json`` and ``.md`` go (checked).
        roots: The output roots.

    Returns:
        The summary: the record paths, ``mandatory_and_required_all_same``, and the
        DIFFERENT items per class with their names.
    """
    try:
        record = compare_files(source, output)
    except ProbeError as exc:
        raise ClipError(f"the comparison could not probe a file: {exc}") from None
    json_path, md_path = write_record(record, folder, output.stem, roots.allowed, roots.footage)
    summary = record["summary"]
    return {
        "compare_json": str(json_path),
        "compare_md": str(md_path),
        "mandatory_and_required_all_same": summary["mandatory_and_required_all_same"],
        "mandatory_all_same": summary["mandatory_all_same"],
        "different_items": summary["different_items"],
        "blocking_classes": [MANDATORY, REQUIRED],
    }


# --- command line -------------------------------------------------------------------------------


def _ratio(value: Fraction) -> str:
    """A fraction as ``numerator/denominator``."""
    return f"{value.numerator}/{value.denominator}"


def _stamp() -> str:
    """A local timestamp for file names."""
    return datetime.datetime.now().strftime("%Y%m%d-%H%M%S")


def work_roots(config_path: Path | None = None) -> OutputRoots:
    """Return the output roots of this package: ``<working folder>/wp1.2b`` and the footage.

    Args:
        config_path: The local configuration file; ``None`` for the default.

    Returns:
        The roots.

    Raises:
        local_config.LocalConfigError: The configuration is missing or invalid.
    """
    config = load_local_config(config_path)
    return OutputRoots(allowed=config.working_path / WORK_SUBDIR, footage=config.footage_path)


def make_params(method: str, neutral: bool) -> Params:
    """Return the parameter set: the defaults or the neutral set (V9), with ``method``.

    Args:
        method: ``ancuti2018`` or ``c3``.
        neutral: Start from :meth:`prototype.params.Params.neutral`.

    Returns:
        The parameters.
    """
    base = Params.neutral() if neutral else Params()
    return dataclasses.replace(base, method=method)  # type: ignore[arg-type]


def output_paths(roots: OutputRoots, folder: Path, names: Sequence[str]) -> list[Path]:
    """Check an output folder and the files to be written in it; create the folder.

    Args:
        roots: The output roots.
        folder: The folder.
        names: The file names.

    Returns:
        The checked file paths (``folder / name``), in order.

    Raises:
        lookcheck.frames.OutputPathError: The folder or a file is refused.
    """
    roots.mkdir(folder)
    paths = [folder / name for name in names]
    for path in paths:
        roots.check(path)
    return paths


def _progress(label: str, total: int) -> Callable[[int], None]:
    """A progress printer: one line on standard error every 300 frames and at the end."""
    started = time.perf_counter()

    def report(done: int) -> None:
        if done % 300 == 0 or done == total:
            elapsed = time.perf_counter() - started
            print(f"{label}: {done}/{total} frames, {elapsed:.0f} s", file=sys.stderr, flush=True)

    return report


def main(argv: Sequence[str] | None = None) -> int:
    """Run ``analyse`` or ``render`` (see the module docstring).

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2 (with a one-line ``error: ...``) on failure.
    """
    parser = argparse.ArgumentParser(description="Clearwater prototype: whole-clip runner.")
    parser.add_argument("--config", type=Path, help="local configuration file to read")
    steps = parser.add_subparsers(dest="step", required=True)
    for name in ("analyse", "render"):
        step = steps.add_parser(name)
        step.add_argument("clip", help="footage stem, or a video path outside the footage")
        step.add_argument(
            "--method",
            choices=METHODS,
            default="ancuti2018",
            help="compensation method (default ancuti2018, kept so the WP1.2B report reproduces;"
            " the Params() and product default is c3; options c3, ancuti2018)",
        )
        step.add_argument("--neutral", action="store_true", help="start from Params.neutral()")
        step.add_argument("--device", choices=("gpu", "cpu"), default="gpu")
        step.add_argument("--hwaccel", choices=HWACCELS, default="none")
        step.add_argument("--frames", type=int, help="only the first N frames")
        step.add_argument("--out", type=Path, help=f"output folder inside the {WORK_SUBDIR} folder")
    witness_step = steps.add_parser("witness", help="untimed output witness of an export")
    witness_step.add_argument("--run", type=Path, required=True, help="the export's run record")
    witness_step.add_argument("--device", choices=("gpu", "cpu"), default="gpu")
    witness_step.add_argument("--count", type=int, default=WITNESS_FRAMES, help="frames to check")
    render_step = steps.choices["render"]
    render_step.add_argument("--statistics", type=Path, required=True, help="analysis record")
    render_step.add_argument("--resident", action="store_true", help="device-resident core")
    render_step.add_argument("--no-compare", action="store_true", help="skip compare.py")
    args = parser.parse_args(argv)
    try:
        if args.step == "witness":
            if args.count < 2:
                raise ClipError("--count must be at least 2 (the first and the last frame)")
            path = run_witness(
                args.run, work_roots(args.config), select_backend(args.device), args.count
            )
            print(path)
            return 0
        if args.frames is not None and args.frames < temporal.MIN_FRAMES:
            raise ClipError(f"--frames must be at least {temporal.MIN_FRAMES}")
        roots = work_roots(args.config)
        source = open_source(resolve_clip(args.clip, roots.footage))
        params = make_params(args.method, args.neutral)
        backend = select_backend(args.device)
        if args.step == "analyse":
            path = run_analyse(source, params, backend, roots, args.out, args.hwaccel, args.frames)
        else:
            path = run_render(
                source,
                params,
                backend,
                roots,
                args.statistics,
                args.out,
                args.hwaccel,
                args.resident,
                args.frames,
                not args.no_compare,
            )
    except (ClipError, ExtractError, LocalConfigError, OSError, RuntimeError, ValueError) as exc:
        print(f"error: {' '.join(str(exc).split()) or type(exc).__name__}", file=sys.stderr)
        return 2
    print(path)
    return 0


def run_analyse(
    source: Source,
    params: Params,
    backend: Backend,
    roots: OutputRoots,
    out: Path | None,
    hwaccel: str,
    frames: int | None,
) -> Path:
    """Run the analysis pass and write its record; return the record's path.

    Args:
        source: The clip.
        params: The parameter set.
        backend: Where the statistics are computed.
        roots: The output roots.
        out: The output folder (default ``<roots.allowed>/analysis``).
        hwaccel: The decode choice.
        frames: Only the first this many frames.

    Returns:
        The record's path.

    Raises:
        ClipError: The pass failed.
        lookcheck.frames.OutputPathError: An output path is refused.
    """
    folder = roots.allowed / "analysis" if out is None else out
    stem = f"{source.path.stem}-{params.method}-{hwaccel}-{_stamp()}"
    record_path, log_path = output_paths(roots, folder, [f"{stem}.json", f"{stem}.decode.log"])
    total = source.frame_count if frames is None else min(frames, source.frame_count)
    analysis = analyse(
        source,
        params,
        backend,
        log_path,
        hwaccel,
        frames=frames,
        progress=_progress(f"analyse {source.path.stem}", total),
    )
    record = analysis_record(source, params, analysis, hwaccel, SMOOTHER)
    roots.write_text(record_path, json.dumps(record) + "\n")
    return record_path


def run_render(
    source: Source,
    params: Params,
    backend: Backend,
    roots: OutputRoots,
    statistics_path: Path,
    out: Path | None,
    hwaccel: str,
    resident: bool,
    frames: int | None,
    compare: bool,
) -> Path:
    """Run the export loop with an analysis record's statistics; return the run record's path.

    Args:
        source: The clip.
        params: The parameter set (must be the analysis record's).
        backend: Where the correction runs.
        roots: The output roots.
        statistics_path: The analysis record.
        out: The output folder (default ``<roots.allowed>/render``).
        hwaccel: The decode choice (must be the analysis record's).
        resident: Run the device-resident variant.
        frames: Only the first this many frames (must match the analysis).
        compare: Compare the output with the source afterwards.

    Returns:
        The run record's path.

    Raises:
        ClipError: The record does not fit, or the export failed.
        lookcheck.frames.OutputPathError: An output path is refused.
    """
    record = json.loads(statistics_path.read_text(encoding="utf-8"))
    check_statistics_record(record, source, params, hwaccel, frames)
    statistics = per_frame_statistics(record)
    folder = roots.allowed / "render" if out is None else out
    stem = f"{source.path.stem}_corrected"
    names = [f"{stem}.mp4", f"{stem}.decode.log", f"{stem}.encode.log", f"{stem}.run.json"]
    roots.check(partial_name(folder / names[0]))
    output, decode_log, encode_log, run_path = output_paths(roots, folder, names)
    total = len(statistics)
    result = export(
        source,
        output,
        params,
        statistics,
        backend,
        (decode_log, encode_log),
        record["frame_means"],
        hwaccel,
        resident,
        frames,
        _progress(f"render {source.path.stem}", total),
    )
    run = export_record(source, result, statistics_path, output)
    if compare:
        run["compare"] = compare_output(source.path, output, folder, roots)
    roots.write_text(run_path, json.dumps(run, indent=1) + "\n")
    return run_path


def export_record(
    source: Source, result: Export, statistics_path: Path | None, output: Path | None
) -> dict[str, Any]:
    """Build the JSON record of an export, pass-through or decode-only pass.

    Args:
        source: The clip.
        result: The pass's result.
        statistics_path: The analysis record applied (``None`` when none was).
        output: The output file (``None`` for a decode-only pass).

    Returns:
        The record.
    """
    footage = Fraction(result.timing.frames) / source.info.frame_rate
    return {
        "source": source.identity(),
        "output": None if output is None else str(output),
        "statistics": None if statistics_path is None else str(statistics_path),
        "decode_command": result.decode_command,
        "encode_command": result.encode_command,
        "decoder_status": result.decoder_status,
        "encoder_status": result.encoder_status,
        "frames_written": result.frames_written,
        "witness_frames_checked": result.witnessed,
        "resident": result.resident,
        "buffering": {
            "input_float_buffers": INPUT_BUFFERS,
            "output_frames_in_flight": OUTPUT_FRAMES,
            "frame_bytes": source.frame_bytes,
            "pipe_format": source.pipe_format,
        },
        "timing": result.timing.record(footage),
        "n6": n6_record(result.timing, source),
    }


def n6_record(timing: LoopTiming, source: Source) -> dict[str, Any]:
    """The pass against N6 (D106): 3.3 minutes per minute, and the per-frame budget.

    Args:
        timing: The pass's readings.
        source: The clip (for its frame rate).

    Returns:
        The budget in minutes per minute and in seconds per frame at the clip's rate, the
        measured figures and their ratio to the budget.
    """
    rate = float(source.info.frame_rate)
    budget_frame = N6_MINUTES_PER_MINUTE / rate
    bracket = timing.bracket_s()
    measured = bracket / (timing.frames / rate)
    return {
        "budget_minutes_per_minute": N6_MINUTES_PER_MINUTE,
        "budget_seconds_per_frame": budget_frame,
        "measured_minutes_per_minute": measured,
        "measured_seconds_per_frame": bracket / timing.frames,
        "times_budget": measured / N6_MINUTES_PER_MINUTE,
    }


if __name__ == "__main__":
    raise SystemExit(main())
