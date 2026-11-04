"""Frame extraction for the WP1.3 look check (reused by WP1.4): FFmpeg as a process.

``extract`` decodes chosen frames of a video and ``excerpt`` decodes every frame of a time
range, both to 16-bit RGB PNG. The record of each frame (:class:`FrameFile`) carries the
exact presentation timestamp of the frame in the source, as the stream's time base ticks
read from ``ffprobe -show_frames`` and confirmed by the decode itself, and the stream's
colour tags.

**Colour.** The stream's pixel format, range and matrix are read with ``ffprobe`` and
passed to FFmpeg's ``scale`` filter explicitly (``in_range``, ``in_color_matrix``,
``out_range=full``), so the conversion to RGB follows the tags and never an assumption.
(For a ``yuvj`` pixel format, which is what FFmpeg's HEVC decoder reports for a full-range
stream, the scaler takes the range from the pixel format and ignores ``in_range``; the
decoder sets that format from the same tag, and a stream whose pixel format and range tag
disagree is refused. The explicit range governs every other format.)
Chroma is upsampled to full resolution by the scaler's default method. A stream with no
range or matrix tag is read as BT.709 limited range and the record says it assumed that
(spec D54, 6.5). The values are display-encoded RGB in the source's primaries, written as
16-bit PNG with no colour chunk (spec 6.5): FFmpeg's ``cICP``, ``cHRM`` and ``gAMA`` chunks are
stripped (:func:`strip_ancillary_chunks`) so that a source frame and its corrected twin, which
the prototype writes untagged, display the same way. The tags are in the frame record. A
stream whose matrix this module does not map, or that carries a rotation, is refused: it is
outside the declared envelope. The conversion is proved by ``tests/test_lookcheck.py``
against RGB values known in advance, for full-range and limited-range clips.

**Output safety.** Every file written, and every file FFmpeg is told to write, is first
checked with :meth:`OutputRoots.check`: the resolved path lies inside the allowed folder
(by default ``<working folder>/wp1.3``), outside the footage folder, and is not an
existing file with more than one hard link. This mirrors ``check_output_path`` of
``container_spike.compare`` (WP1.5) with messages that name this package's folder; it is
mirrored, not imported, so that the messages are right and the two instruments stay
independent. ``FFREPORT`` is removed from the environment of every FFmpeg and ffprobe
process, as WP1.5's ``tool_env`` does.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import struct
import subprocess
import uuid
import zlib
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from footage_guard import is_inside
from local_config import LocalConfig, load_local_config

WORK_SUBDIR = "wp1.3"
"""The default allowed output folder inside the working folder."""

TOOL_TIMEOUT_SECONDS = 3600.0
"""Seconds before an FFmpeg or ffprobe run is abandoned."""

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"

_YUVJ = frozenset({"yuvj420p", "yuvj422p", "yuvj440p", "yuvj444p"})
_RANGES = {"tv": "limited", "pc": "full"}
# ffprobe's color_space name -> the scale filter's in_color_matrix name.
_MATRICES = {
    "bt709": "bt709",
    "bt470bg": "bt470",
    "smpte170m": "smpte170m",
    "smpte240m": "smpte240m",
    "fcc": "fcc",
    "bt2020nc": "bt2020",
}
_UNKNOWN = ("", "unknown", "unspecified", "N/A")
_SHOWINFO = re.compile(r"showinfo.*\] n:\s*(\d+)\s+pts:\s*(-?\d+)\s+pts_time:")
_WINDOW_MARGIN_S = Fraction(1, 2)

Naming = Literal["pts", "index"]
"""How a decode names its files: by pts, or by position in the call."""


class ExtractError(Exception):
    """A probe, decode or encode step failed or is outside the envelope; the message says why."""


class OutputPathError(ExtractError):
    """An output path is outside the allowed folder, inside the footage folder or shared."""


def tool_env() -> dict[str, str]:
    """Return the environment for an FFmpeg or ffprobe process: this one without ``FFREPORT``.

    ``FFREPORT`` makes both tools write a log file (by default into the current folder,
    whatever it is), so it is never passed on.

    Returns:
        A copy of ``os.environ`` without ``FFREPORT``.
    """
    return {key: value for key, value in os.environ.items() if key.upper() != "FFREPORT"}


def run_tool(
    command: Sequence[str], timeout: float = TOOL_TIMEOUT_SECONDS
) -> subprocess.CompletedProcess[bytes]:
    """Run an FFmpeg or ffprobe command without a shell, capturing both output streams.

    The process gets :func:`tool_env` and no standard input.

    Args:
        command: The command and its arguments.
        timeout: Seconds before the run is abandoned.

    Returns:
        The completed process (bytes output); the exit status is not checked.

    Raises:
        ExtractError: The program is absent, cannot start or times out.
    """
    try:
        return subprocess.run(
            list(command),
            capture_output=True,
            stdin=subprocess.DEVNULL,
            env=tool_env(),
            timeout=timeout,
            check=False,
        )
    except FileNotFoundError:
        raise ExtractError(f"{command[0]} not found on PATH") from None
    except subprocess.TimeoutExpired:
        raise ExtractError(f"{command[0]} timed out after {timeout:g} s") from None
    except OSError as exc:
        raise ExtractError(f"{command[0]} could not run: {exc}") from None


def tool_version(program: str = "ffmpeg") -> str:
    """Return the first line of ``<program> -version``.

    Args:
        program: ``"ffmpeg"`` or ``"ffprobe"``.

    Returns:
        The version line.

    Raises:
        ExtractError: The program cannot be run.
    """
    done = run_tool([program, "-hide_banner", "-version"], timeout=60)
    if done.returncode != 0:
        raise ExtractError(f"{program} -version failed")
    return done.stdout.decode("utf-8", errors="replace").splitlines()[0]


# --- output safety --------------------------------------------------------------------


def _normalised(path: Path) -> Path:
    """Resolve links and normalise case for the output-folder check (not the footage one)."""
    return Path(os.path.normcase(path.resolve()))


def check_output_path(path: Path, allowed_root: Path, footage_root: Path) -> Path:
    """Refuse an output path outside the allowed folder or inside the footage folder.

    Both checks run on the resolved path (links followed), so a symbolic link or junction
    that leads into the footage folder is refused. A hard link resolves to itself, so an
    existing file with more than one link is refused as well: writing to it would change
    every other name of the same file, wherever that name is. The check is made once,
    before the write; a concurrent process that swaps a checked path between the check and
    the write is outside what it guards against.

    Args:
        path: The intended output file or folder.
        allowed_root: The folder every output must lie in (or equal).
        footage_root: The read-only footage folder.

    Returns:
        The resolved path.

    Raises:
        OutputPathError: The path is not inside ``allowed_root`` (or equal to it), is
            inside (or equal to) ``footage_root``, or is an existing file with more than
            one hard link.
    """
    resolved = _normalised(path)
    allowed = _normalised(allowed_root)
    if is_inside(path, footage_root):  # by identity where it exists (footage_guard, DR-122)
        raise OutputPathError(f"output path {path} lies inside the footage folder")
    if resolved != allowed and allowed not in resolved.parents:
        raise OutputPathError(f"output path {path} lies outside the output folder {allowed_root}")
    target = path.resolve()
    if target.exists() and not target.is_dir() and (links := target.stat().st_nlink) > 1:
        raise OutputPathError(f"output path {path} exists with {links} hard links")
    return target


@dataclass(frozen=True)
class OutputRoots:
    """The two folders that bound every write: where outputs may go and the footage folder.

    Attributes:
        allowed: The folder all outputs must lie in (``<working folder>/wp1.3`` by default).
        footage: The read-only footage folder, which no output may touch.
    """

    allowed: Path
    footage: Path

    @classmethod
    def from_config(
        cls, config: LocalConfig | None = None, subdir: str = WORK_SUBDIR
    ) -> OutputRoots:
        """Build the roots from the local configuration.

        Args:
            config: The configuration; defaults to ``load_local_config()``.
            subdir: The folder inside the working folder that outputs may use.

        Returns:
            The roots.

        Raises:
            local_config.LocalConfigError: The configuration is missing or invalid.
        """
        loaded = load_local_config() if config is None else config
        return cls(allowed=loaded.working_path / subdir, footage=loaded.footage_path)

    def check(self, path: Path) -> Path:
        """Check one output path (see :func:`check_output_path`).

        Args:
            path: The intended output file or folder.

        Returns:
            The resolved path.

        Raises:
            OutputPathError: The path is refused.
        """
        return check_output_path(path, self.allowed, self.footage)

    def mkdir(self, path: Path) -> Path:
        """Create a folder (and its parents) after checking it.

        Args:
            path: The folder.

        Returns:
            ``path``.

        Raises:
            OutputPathError: The path is refused.
        """
        self.check(path).mkdir(parents=True, exist_ok=True)
        return path

    def write_text(self, path: Path, text: str) -> Path:
        """Write UTF-8 text to a file after checking the file's own resolved path.

        Args:
            path: The file.
            text: The content.

        Returns:
            ``path``.

        Raises:
            OutputPathError: The path is refused.
        """
        target = self.check(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        return path

    def write_bytes(self, path: Path, data: bytes) -> Path:
        """Write bytes to a file after checking the file's own resolved path.

        Args:
            path: The file.
            data: The content.

        Returns:
            ``path``.

        Raises:
            OutputPathError: The path is refused.
        """
        target = self.check(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        return path

    def remove(self, path: Path) -> None:
        """Delete one file inside the allowed folder (a missing file is not an error).

        Args:
            path: The file.

        Raises:
            OutputPathError: The path is refused.
        """
        target = self.check(path)
        target.unlink(missing_ok=True)

    def rename(self, source: Path, target: Path) -> Path:
        """Move one file to a new name, replacing ``target``; both names are checked.

        Args:
            source: The existing file.
            target: Its new name (an existing file of that name is replaced).

        Returns:
            ``target``.

        Raises:
            OutputPathError: Either path is refused.
            OSError: The move fails.
        """
        moved = self.check(source)
        self.check(target)
        moved.replace(target)
        return target


# --- probing ----------------------------------------------------------------------------


@dataclass(frozen=True)
class StreamTags:
    """The pixel format and colour tags that decide how a stream is converted to RGB.

    Attributes:
        pix_fmt: The decoder's pixel format as ``ffprobe`` reports it (``yuvj420p`` for
            full-range 8-bit 4:2:0 HEVC).
        color_range: ``"tv"`` (limited) or ``"pc"`` (full), as used for the conversion.
        color_space: The matrix, ``ffprobe`` name (``"bt709"``), as used.
        color_transfer: The transfer characteristic as read (``"unknown"`` if untagged).
        color_primaries: The primaries as read (``"unknown"`` if untagged).
        assumed: Which of ``"color_range"`` and ``"color_space"`` were absent from the
            stream and assumed (BT.709 limited range, spec D54); empty when both were read.
    """

    pix_fmt: str
    color_range: str
    color_space: str
    color_transfer: str
    color_primaries: str
    assumed: tuple[str, ...] = ()

    def record(self) -> dict[str, Any]:
        """Return the tags as a JSON-ready dictionary."""
        return {
            "pix_fmt": self.pix_fmt,
            "color_range": self.color_range,
            "color_space": self.color_space,
            "color_transfer": self.color_transfer,
            "color_primaries": self.color_primaries,
            "assumed": list(self.assumed),
        }


@dataclass(frozen=True)
class StreamInfo:
    """What the probe found out about the first video stream.

    Attributes:
        width: Coded width in pixels.
        height: Coded height in pixels.
        time_base: The stream time base in seconds per tick.
        frame_rate: The average frame rate in frames per second.
        duration_s: The stream (else container) duration in seconds.
        tags: The pixel format and colour tags.
    """

    width: int
    height: int
    time_base: Fraction
    frame_rate: Fraction
    duration_s: float
    tags: StreamTags


def _field(stream: Mapping[str, Any], key: str) -> str:
    """The stream's string field, or ``"unknown"`` when it is absent or unspecified."""
    value = str(stream.get(key, "unknown"))
    return "unknown" if value in _UNKNOWN else value


def tags_from_stream(stream: Mapping[str, Any]) -> StreamTags:
    """Build :class:`StreamTags` from one ``ffprobe -show_streams`` stream object.

    Args:
        stream: The stream's JSON object.

    Returns:
        The tags; an absent range or matrix is replaced by BT.709 limited range and listed
        in :attr:`StreamTags.assumed`.

    Raises:
        ExtractError: The pixel format is not YUV, the range tag contradicts a ``yuvj``
            pixel format, or the matrix is not one this module maps.
    """
    pix_fmt = _field(stream, "pix_fmt")
    if not pix_fmt.startswith("yuv"):
        raise ExtractError(f"pixel format {pix_fmt} is not YUV: outside the envelope")
    assumed: list[str] = []
    colour_range = _field(stream, "color_range")
    if colour_range == "unknown":
        colour_range = "pc" if pix_fmt in _YUVJ else "tv"
        assumed.append("color_range")
    if colour_range not in _RANGES:
        raise ExtractError(f"unexpected color_range {colour_range!r}")
    if pix_fmt in _YUVJ and colour_range != "pc":
        raise ExtractError(
            f"pixel format {pix_fmt} is full range but color_range is {colour_range}"
        )
    matrix = _field(stream, "color_space")
    if matrix == "unknown":
        matrix = "bt709"
        assumed.append("color_space")
    if matrix not in _MATRICES:
        raise ExtractError(f"color_space {matrix!r} is not mapped: outside the envelope")
    return StreamTags(
        pix_fmt=pix_fmt,
        color_range=colour_range,
        color_space=matrix,
        color_transfer=_field(stream, "color_transfer"),
        color_primaries=_field(stream, "color_primaries"),
        assumed=tuple(assumed),
    )


def run_ffprobe(arguments: Sequence[str]) -> dict[str, Any]:
    """Run ``ffprobe -v error -of json`` with ``arguments`` and return the parsed document.

    Args:
        arguments: The remaining arguments, ending with the input file.

    Returns:
        The parsed JSON document.

    Raises:
        ExtractError: ``ffprobe`` is absent, fails or prints something that is not a JSON
            object.
    """
    done = run_tool(["ffprobe", "-v", "error", "-of", "json", *arguments])
    if done.returncode != 0:
        detail = done.stderr.decode("utf-8", errors="replace").strip().splitlines()
        raise ExtractError(f"ffprobe failed: {detail[-1] if detail else done.returncode}")
    try:
        document = json.loads(done.stdout)
    except ValueError as exc:
        raise ExtractError(f"ffprobe printed invalid JSON: {exc}") from None
    if not isinstance(document, dict):
        raise ExtractError("ffprobe printed a JSON document that is not an object")
    return document


def probe_stream(video: Path) -> StreamInfo:
    """Read the first video stream of ``video`` with ``ffprobe``.

    Args:
        video: The video file (read only).

    Returns:
        The stream's size, timing and colour tags.

    Raises:
        ExtractError: The file has no video stream, the stream is rotated by a display
            matrix, has no usable size, time base, frame rate or duration (a frame rate
            of 0/0 is refused), or its tags are outside the envelope
            (:func:`tags_from_stream`).
    """
    document = run_ffprobe(["-select_streams", "v:0", "-show_streams", "-show_format", str(video)])
    streams = document.get("streams") or []
    if not streams:
        raise ExtractError(f"{video.name} has no video stream")
    stream: Mapping[str, Any] = streams[0]
    for side in stream.get("side_data_list", []):
        rotation = side.get("rotation")
        if rotation is not None and int(rotation) % 360 != 0:
            raise ExtractError(
                f"{video.name} is rotated by {rotation} degrees: outside the envelope"
            )
    duration = stream.get("duration")
    if duration in (None, "N/A"):
        duration = document.get("format", {}).get("duration")
    if duration is None or duration == "N/A":
        raise ExtractError(f"{video.name} reports no duration")
    try:
        return StreamInfo(
            width=int(stream["width"]),
            height=int(stream["height"]),
            time_base=Fraction(stream["time_base"]),
            frame_rate=Fraction(stream["avg_frame_rate"]),
            duration_s=float(duration),
            tags=tags_from_stream(stream),
        )
    except (KeyError, ValueError, ZeroDivisionError) as exc:
        raise ExtractError(f"{video.name}: unusable stream properties ({exc!r})") from None


def frame_pts(video: Path, info: StreamInfo, start: Fraction, end: Fraction) -> list[int]:
    """List the presentation timestamps (stream ticks) of the frames in ``[start, end)``.

    The list comes from ``ffprobe -show_frames`` over a read interval that runs half a
    second past ``end`` (the last frames of an interval can be held back by the decoder's
    reordering). ``ffprobe`` starts that interval at the keyframe before ``start``, so the
    frames are filtered by their exact timestamp here.

    Args:
        video: The video file.
        info: Its :func:`probe_stream` result (for the time base).
        start: Start of the range in seconds, inclusive.
        end: End of the range in seconds, exclusive.

    Returns:
        The timestamps in ticks, ascending.

    Raises:
        ExtractError: ``ffprobe`` fails or reports a frame without a timestamp.
    """
    interval = f"{float(max(start, Fraction(0))):.6f}%{float(end + _WINDOW_MARGIN_S):.6f}"
    document = run_ffprobe(
        [
            "-select_streams",
            "v:0",
            "-read_intervals",
            interval,
            "-show_frames",
            "-show_entries",
            "frame=pts",
            str(video),
        ]
    )
    ticks: list[int] = []
    for frame in document.get("frames", []):
        if "pts" not in frame:
            raise ExtractError(f"ffprobe reported a frame of {video.name} without a pts")
        pts = int(frame["pts"])
        if start <= pts * info.time_base < end:
            ticks.append(pts)
    return sorted(set(ticks))


# --- the frame record ---------------------------------------------------------------------


@dataclass(frozen=True)
class FrameFile:
    """One extracted frame: the PNG, where it came from and how it was decoded.

    Attributes:
        path: The 16-bit RGB PNG.
        source: The video the frame was decoded from.
        pts_ticks: The frame's exact presentation timestamp in the source, in ticks of
            ``time_base``.
        time_base: The source stream's time base in seconds per tick.
        width: PNG width in pixels.
        height: PNG height in pixels.
        tags: The source stream's pixel format and colour tags used for the conversion.
        command: The FFmpeg command line that decoded the frame (shared by the frames of
            one ``excerpt`` call).
    """

    path: Path
    source: Path
    pts_ticks: int
    time_base: Fraction
    width: int
    height: int
    tags: StreamTags
    command: tuple[str, ...]

    @property
    def pts(self) -> Fraction:
        """The exact presentation timestamp in seconds."""
        return self.pts_ticks * self.time_base

    @property
    def chapter(self) -> str:
        """The source file's stem (``GX011627``)."""
        return self.source.stem

    def record(self) -> dict[str, Any]:
        """Return the frame as a JSON-ready dictionary (the shape of ``frames.json`` entries).

        Returns:
            ``file``, ``source``, ``chapter``, the exact ``pts_ticks``, ``time_base`` and
            ``pts_exact`` (a fraction of seconds), ``pts_seconds`` (a float), the PNG size,
            the colour ``tags`` and the FFmpeg ``command``.
        """
        return {
            "file": self.path.name,
            "source": str(self.source),
            "chapter": self.chapter,
            "pts_ticks": self.pts_ticks,
            "time_base": f"{self.time_base.numerator}/{self.time_base.denominator}",
            "pts_exact": f"{self.pts.numerator}/{self.pts.denominator}",
            "pts_seconds": float(self.pts),
            "width": self.width,
            "height": self.height,
            "tags": self.tags.record(),
            "command": list(self.command),
        }


def frame_stem(chapter: str, pts_seconds: float) -> str:
    """Return the file stem of a frame: ``<chapter>_<pts-seconds 0000.000>``.

    Args:
        chapter: The source file's stem.
        pts_seconds: The presentation timestamp in seconds.

    Returns:
        For example ``GX011625_0030.012``.
    """
    return f"{chapter}_{pts_seconds:08.3f}"


# --- PNG reading ----------------------------------------------------------------------------


def strip_ancillary_chunks(data: bytes) -> bytes:
    """Return a PNG file's bytes with every chunk but IHDR, IDAT and IEND removed.

    FFmpeg's PNG encoder copies the stream's colour description into ancillary chunks
    (``cICP``, ``cHRM``, ``gAMA``, ``pHYs``); the prototype's corrected PNGs carry none. A
    colour-managed viewer would then show a source frame and its corrected twin differently,
    so the extracted frames are stripped to match: both sides are untagged display-encoded
    RGB (spec 6.5). The colour tags stay in :class:`FrameFile` and ``frames.json``. The kept
    chunks are copied byte for byte, so the pixels are untouched.

    Args:
        data: The PNG file content.

    Returns:
        The PNG with only the critical chunks.

    Raises:
        ValueError: ``data`` is not a PNG file or ends inside a chunk.
    """
    if data[:8] != PNG_SIGNATURE:
        raise ValueError("not a PNG file")
    kept = [PNG_SIGNATURE]
    position = 8
    while position < len(data):
        if position + 12 > len(data):
            raise ValueError("PNG ends inside a chunk")
        (length,) = struct.unpack(">I", data[position : position + 4])
        end = position + 12 + length
        if end > len(data):
            raise ValueError("PNG ends inside a chunk")
        if data[position + 4 : position + 8] in (b"IHDR", b"IDAT", b"IEND"):
            kept.append(data[position:end])
        position = end
    return b"".join(kept)


def read_png16(path: Path) -> NDArray[np.float32]:
    """Read a non-interlaced 16-bit RGB PNG into float32 RGB in [0, 1].

    Pillow reads 16-bit RGB at 8-bit precision, so this reads the file itself. Scanline
    filter types None, Sub and Up are supported (what FFmpeg's ``-pred none`` and the
    prototype's PNG writer produce); Average and Paeth raise.

    Args:
        path: The PNG file.

    Returns:
        The image, shape ``(H, W, 3)``, values ``v / 65535``.

    Raises:
        ValueError: The file is not a non-interlaced 16-bit RGB PNG, is damaged, or uses a
            scanline filter this reader does not support.
        OSError: The file cannot be read.
    """
    data = path.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        raise ValueError(f"{path.name} is not a PNG file")
    header: tuple[int, ...] | None = None
    idat: list[bytes] = []
    position = 8
    while position + 8 <= len(data):
        (length,) = struct.unpack(">I", data[position : position + 4])
        kind = data[position + 4 : position + 8]
        body = data[position + 8 : position + 8 + length]
        position += 12 + length
        if kind == b"IHDR":
            header = struct.unpack(">IIBBBBB", body)
        elif kind == b"IDAT":
            idat.append(body)
        elif kind == b"IEND":
            break
    if header is None or not idat:
        raise ValueError(f"{path.name} is damaged: no IHDR or IDAT chunk")
    width, height, depth, colour_type, _compression, _filter, interlace = header
    if (depth, colour_type, interlace) != (16, 2, 0):
        raise ValueError(f"{path.name} is not a non-interlaced 16-bit RGB PNG")
    stride = width * 6
    raw = np.frombuffer(zlib.decompress(b"".join(idat)), dtype=np.uint8)
    if raw.size != height * (stride + 1):
        raise ValueError(f"{path.name} is damaged: unexpected image data size")
    rows = raw.reshape(height, stride + 1)
    filters = rows[:, 0]
    samples = rows[:, 1:].copy()
    for y in np.nonzero(filters)[0]:
        kind_of_filter = int(filters[y])
        if kind_of_filter == 1:
            summed = np.cumsum(samples[y].reshape(width, 6), axis=0, dtype=np.uint32)
            samples[y] = (summed % 256).astype(np.uint8).reshape(stride)
        elif kind_of_filter == 2:
            if y > 0:
                samples[y] += samples[y - 1]
        else:
            raise ValueError(f"{path.name} uses scanline filter {kind_of_filter}: not supported")
    values = samples.reshape(height, -1).view(">u2").reshape(height, width, 3)
    out: NDArray[np.float32] = values.astype(np.float32) / np.float32(65535.0)
    return out


def to_uint8(image: NDArray[np.float32]) -> NDArray[np.uint8]:
    """Round float RGB in [0, 1] to 8-bit (values outside [0, 1] are clipped).

    Args:
        image: The image.

    Returns:
        The same shape as ``uint8``.
    """
    return np.round(np.clip(image, 0.0, 1.0) * 255.0).astype(np.uint8)


# --- decoding -----------------------------------------------------------------------------------


def scale_range(tags: StreamTags) -> str:
    """Return the range name the ``scale`` filter takes for ``tags`` (``limited`` or ``full``)."""
    return _RANGES[tags.color_range]


def scale_matrix(tags: StreamTags) -> str:
    """Return the matrix name the ``scale`` filter takes for ``tags`` (``bt709``, ...)."""
    return _MATRICES[tags.color_space]


def colour_filter(tags: StreamTags, size: tuple[int, int] | None = None) -> str:
    """Build the FFmpeg filter that converts a decoded YUV frame to 16-bit RGB.

    The range and matrix come from ``tags``, passed to ``scale`` explicitly; the scaler's
    default method upsamples the chroma. ``accurate_rnd`` changes only the rounding: without
    it limited-range YUV comes out about 2 levels (of 255) too dark, which the range test
    measured (limited-range test clip: 3 levels without, under 1 with). With ``size`` the
    same scaler also resizes.

    Args:
        tags: The source stream's tags.
        size: The output ``(width, height)``, or ``None`` for the source size.

    Returns:
        The filter chain text (``scale=...,format=rgb48be``).
    """
    dimension = "" if size is None else f"w={size[0]}:h={size[1]}:"
    return (
        f"scale={dimension}in_range={scale_range(tags)}"
        f":in_color_matrix={scale_matrix(tags)}:out_range=full:flags=accurate_rnd,format=rgb48be"
    )


def decode_command(
    video: Path,
    tags: StreamTags,
    first: Fraction,
    count: int,
    output_pattern: Path,
    size: tuple[int, int] | None = None,
) -> list[str]:
    """Build the FFmpeg command that decodes ``count`` frames from ``first`` seconds on.

    ``-copyts`` keeps the source timestamps so that ``showinfo`` reports the frames' own
    pts, which :func:`extract` compares with the probe; ``-fps_mode passthrough`` drops
    and repeats nothing; ``-pred none`` writes unfiltered scanlines (see :func:`read_png16`).

    Args:
        video: The source video.
        tags: Its tags (:func:`colour_filter`).
        first: Seek position in seconds (a little before the first wanted frame).
        count: The number of frames to write.
        output_pattern: The output path with a ``%06d`` frame counter.
        size: The output size, or ``None`` for the source size.

    Returns:
        The command and its arguments.
    """
    return [
        "ffmpeg",
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-y",
        "-noautorotate",
        "-copyts",
        "-ss",
        f"{float(max(first, Fraction(0))):.6f}",
        "-i",
        str(video),
        "-map",
        "0:v:0",
        "-an",
        "-sn",
        "-dn",
        "-vf",
        f"showinfo,{colour_filter(tags, size)}",
        "-frames:v",
        str(count),
        "-fps_mode",
        "passthrough",
        "-pred",
        "none",
        str(output_pattern),
    ]


def _target_size(info: StreamInfo, short_side: int | None) -> tuple[int, int] | None:
    """The output size for a requested short side, or ``None`` for the source size."""
    if short_side is None:
        return None
    if short_side < 1:
        raise ValueError(f"short_side must be at least 1, got {short_side}")
    scale = Fraction(short_side, min(info.width, info.height))
    return max(1, round(info.width * scale)), max(1, round(info.height * scale))


def _decode(
    video: Path,
    info: StreamInfo,
    ticks: Sequence[int],
    out_dir: Path,
    short_side: int | None,
    roots: OutputRoots,
    tags: StreamTags | None = None,
    naming: Naming = "pts",
) -> list[FrameFile]:
    """Decode the frames at consecutive ``ticks`` (ascending) and move them to ``out_dir``.

    The seek position is half a frame before the first wanted frame. The decode's own
    ``showinfo`` timestamps must equal ``ticks`` exactly, else nothing is kept.

    Args:
        video: The source video.
        info: Its probe result.
        ticks: The wanted frames' timestamps, consecutive frames of the stream.
        out_dir: Where the PNGs go (named ``<chapter>_<pts>.png``).
        short_side: Resize so the shorter side has this many pixels; ``None`` keeps the size.
        roots: The output safety roots.
        tags: Tags to convert with instead of the stream's (for the range control test).
        naming: ``"pts"``: ``<chapter>_<pts-seconds 0000.000>.png``; ``"index"``:
            ``<chapter>_f<0000>.png``, the position in this call, so that the files form
            a sequence FFmpeg can read back (the pts is in each :class:`FrameFile`).

    Returns:
        One :class:`FrameFile` per tick.

    Raises:
        ExtractError: FFmpeg fails, or it decoded different frames than the probe listed.
        OutputPathError: An output path is refused.
    """
    used = info.tags if tags is None else tags
    size = _target_size(info, short_side)
    shape = size if size is not None else (info.width, info.height)
    roots.mkdir(out_dir)
    scratch = out_dir / f".extract-{uuid.uuid4().hex[:8]}"
    roots.mkdir(scratch)
    try:
        pattern = scratch / "f%06d.png"
        for index in range(1, len(ticks) + 1):
            roots.check(scratch / f"f{index:06d}.png")
        seek = ticks[0] * info.time_base - 1 / (2 * info.frame_rate)
        command = decode_command(video, used, seek, len(ticks), pattern, size)
        done = run_tool(command)
        stderr = done.stderr.decode("utf-8", errors="replace")
        if done.returncode != 0:
            tail = stderr.strip().splitlines()[-1:] or [str(done.returncode)]
            raise ExtractError(f"ffmpeg failed decoding {video.name}: {tail[0]}")
        # showinfo sits before the frame limit, so the decoder may have passed it a few more
        # frames than were written; the first len(ticks) are the written ones.
        seen = [int(match.group(2)) for match in _SHOWINFO.finditer(stderr)][: len(ticks)]
        if seen != list(ticks):
            raise ExtractError(
                f"ffmpeg decoded pts {seen[:3]}... of {video.name}, the probe listed "
                f"{list(ticks)[:3]}...; refusing to label the frames"
            )
        frames: list[FrameFile] = []
        for index, pts in enumerate(ticks, start=1):
            produced = scratch / f"f{index:06d}.png"
            if not produced.is_file():
                raise ExtractError(f"ffmpeg wrote no frame {index} for {video.name}")
            if naming == "index":
                name = f"{video.stem}_f{index - 1:04d}.png"
            else:
                name = frame_stem(video.stem, float(pts * info.time_base)) + ".png"
            final = out_dir / name
            if any(frame.path == final for frame in frames):
                raise ExtractError(f"two frames of {video.name} would be named {name}")
            roots.check(final)
            roots.write_bytes(final, strip_ancillary_chunks(produced.read_bytes()))
            produced.unlink()
            frames.append(
                FrameFile(
                    path=final,
                    source=video,
                    pts_ticks=pts,
                    time_base=info.time_base,
                    width=shape[0],
                    height=shape[1],
                    tags=used,
                    command=tuple(command),
                )
            )
        return frames
    finally:
        shutil.rmtree(roots.check(scratch), ignore_errors=True)


def extract(
    video: Path,
    timestamps_s: Sequence[float],
    out_dir: Path,
    *,
    short_side: int | None = None,
    roots: OutputRoots | None = None,
) -> list[FrameFile]:
    """Extract, for each timestamp, the first frame at or after it, as a 16-bit RGB PNG.

    The frame's exact pts comes from ``ffprobe -show_frames`` and is confirmed by the
    decode (:func:`_decode`). The file is ``<out_dir>/<chapter>_<pts-seconds 0000.000>.png``
    and the conversion follows the stream's tags (module docstring).

    Args:
        video: The source video (read only).
        timestamps_s: Wanted positions in seconds.
        out_dir: Folder for the PNGs (inside ``roots.allowed``).
        short_side: Resize so the shorter side has this many pixels; ``None`` (the default)
            keeps the full resolution.
        roots: The output safety roots; defaults to the local configuration's working
            folder ``wp1.3`` and footage folder.

    Returns:
        One :class:`FrameFile` per timestamp, in the order given.

    Raises:
        ExtractError: A probe or decode fails, a timestamp is past the last frame, or the
            stream is outside the envelope.
        OutputPathError: An output path is refused.
        local_config.LocalConfigError: ``roots`` is ``None`` and the configuration is bad.
    """
    guard = OutputRoots.from_config() if roots is None else roots
    info = probe_stream(video)
    frames: list[FrameFile] = []
    for timestamp in timestamps_s:
        start = Fraction(timestamp).limit_denominator(1_000_000)
        listed = frame_pts(video, info, start, start + _WINDOW_MARGIN_S)
        if not listed:
            raise ExtractError(f"{video.name} has no frame at or after {timestamp} s")
        frames.extend(_decode(video, info, listed[:1], out_dir, short_side, guard))
    return frames


def excerpt(
    video: Path,
    start_s: float,
    duration_s: float,
    out_dir: Path,
    *,
    short_side: int | None = None,
    roots: OutputRoots | None = None,
    naming: Naming = "pts",
) -> list[FrameFile]:
    """Extract every frame with pts in ``[start_s, start_s + duration_s)``, in order.

    Same output, naming and checks as :func:`extract`; all frames come from one FFmpeg run.

    Args:
        video: The source video (read only).
        start_s: Start of the range in seconds.
        duration_s: Length of the range in seconds.
        out_dir: Folder for the PNGs (inside ``roots.allowed``).
        short_side: Resize so the shorter side has this many pixels; ``None`` keeps the size.
        roots: The output safety roots; defaults as in :func:`extract`.
        naming: File naming, see :func:`_decode`; ``"index"`` gives the numbered sequence
            ``<chapter>_f0000.png``... that an FFmpeg image-sequence input reads.

    Returns:
        The frames in presentation order.

    Raises:
        ExtractError: A probe or decode fails, or the range holds no frame.
        OutputPathError: An output path is refused.
        local_config.LocalConfigError: ``roots`` is ``None`` and the configuration is bad.
    """
    guard = OutputRoots.from_config() if roots is None else roots
    info = probe_stream(video)
    start = Fraction(start_s).limit_denominator(1_000_000)
    end = start + Fraction(duration_s).limit_denominator(1_000_000)
    listed = frame_pts(video, info, start, end)
    if not listed:
        raise ExtractError(f"{video.name} has no frame in [{start_s}, {start_s + duration_s}) s")
    return _decode(video, info, listed, out_dir, short_side, guard, naming=naming)
