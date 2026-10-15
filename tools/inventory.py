"""List every video and photo in the footage folder as a CSV table plus a summary.

Usage::

    uv run python tools/inventory.py [--config PATH] [--footage DIR] [--out DIR]

The tool walks the footage folder (read-only), probes each video with ``ffprobe`` and each
photo with Pillow, and writes ``<working>/reports/inventory-<YYYYMMDDTHHMMSSZ>.csv`` (one
row per file, an empty ``category`` column for the owner to fill in) and
``inventory-<stamp>-summary.md`` (recording modes, photo sizes, chaptered recordings,
``.LRV`` coverage, probe errors). Nothing is ever written under the footage folder, and an
existing report is never overwritten: on a name collision both files take a numeric suffix.

A file that cannot be probed (truncated, locked, unreadable) still gets a row with ``error``
set; a file that vanishes before it is read is counted as skipped. The run never aborts on
one file. With both ``--footage`` and ``--out`` given, the configuration file is not read.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import dataclasses
import io
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import IO, Any

import pillow_heif
from PIL import Image, ImageCms

from local_config import LocalConfigError, load_local_config

FFPROBE_TIMEOUT_SECONDS = 60.0
VIDEO_EXTENSIONS = frozenset({".mp4", ".mov", ".360"})
PHOTO_EXTENSIONS = frozenset({".heic", ".heif", ".jpg", ".jpeg", ".png", ".tif", ".tiff"})
SIDECAR_EXTENSIONS = frozenset({".lrv", ".thm"})
CATEGORY_REMINDER = (
    "shallow with caustics",
    "deeper",
    "mostly open blue water",
    "photo, shallow",
    "photo, deeper",
    "chaptered recording",
    "static shot",
)
_VFR_TOLERANCE = 0.005
_ERROR_MAX_CHARS = 200
_HEIF_META_MAX_BYTES = 64 * 1024 * 1024
_DIMENSIONS_NOTE = "Dimensions are as stored; apply the orientation column for display."
_EXIF_ORIENTATION = 0x0112
_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
_TIFF_BITS_PER_SAMPLE = 258
_GOPRO_MODERN = re.compile(r"G[XHS](\d{2})(\d{4})", re.IGNORECASE)
_GOPRO_LEGACY_FIRST = re.compile(r"GOPR(\d{4})", re.IGNORECASE)
_GOPRO_LEGACY_NEXT = re.compile(r"GP(\d{2})(\d{4})", re.IGNORECASE)
_BIT_DEPTH_BY_MODE = {
    "1": 1,
    "L": 8,
    "LA": 8,
    "P": 8,
    "PA": 8,
    "RGB": 8,
    "RGBA": 8,
    "RGBX": 8,
    "CMYK": 8,
    "YCbCr": 8,
    "LAB": 8,
    "HSV": 8,
    "I;16": 16,
    "I;16L": 16,
    "I;16B": 16,
    "I;16N": 16,
}
_PIX_FMT_SEMIPLANAR = re.compile(r"p([0-9])([0-9]{2})(?:le|be)?")
_PIX_FMT_HIGH_DEPTH = re.compile(r"(?:yuvj?a?\d{3}p|gbra?p|gray|ya)(\d+)(?:le|be)")
_PIX_FMT_EIGHT_BIT = re.compile(
    r"yuvj?a?\d{3}p|nv12|nv21|gray|gbra?p|ya8|rgb24|bgr24|argb|abgr|rgba|bgra|0rgb|rgb0|0bgr|bgr0|pal8"
)
_PIX_FMT_YUV = re.compile(r"yuvj?a?(\d)(\d)(\d)p")

# Column order of the CSV: shared fields first, then the rest of the video fields in
# declaration order, then the photo-only fields.
CSV_COLUMNS = (
    "kind",
    "path",
    "category",
    "size_bytes",
    "error",
    "container",
    "codec",
    "width",
    "height",
    "frame_rate",
    "frame_rate_variable",
    "bit_depth",
    "chroma_format",
    "color_primaries",
    "color_transfer",
    "color_matrix",
    "color_range",
    "duration_seconds",
    "rotation_degrees",
    "tracks",
    "gopro_recording",
    "gopro_chapter",
    "lrv_present",
    "format",
    "color_profile",
    "orientation",
)


@dataclass(frozen=True)
class VideoRecord:
    """One video file and the metadata the prototype gate needs.

    Attributes:
        path: Path of the file; relative to the footage root when produced by ``scan``.
        size_bytes: File size in bytes (0 when the file could not be examined).
        container: The ``ffprobe`` format name, for example ``mov,mp4,m4a,3gp,3g2,mj2``.
        codec: Codec name of the first video stream; empty when there is none.
        width: Coded frame width in pixels, before any rotation.
        height: Coded frame height in pixels, before any rotation.
        frame_rate: Average frame rate in frames per second.
        frame_rate_variable: True when ``r_frame_rate`` and ``avg_frame_rate`` differ by more
            than 0.5 percent; ``None`` when either is unknown.
        bit_depth: Bits per sample, from the pixel format.
        chroma_format: Chroma subsampling such as ``4:2:0``.
        color_primaries: Color primaries tag, verbatim from ``ffprobe``.
        color_transfer: Transfer characteristics tag, verbatim from ``ffprobe``.
        color_matrix: Matrix coefficients tag (``ffprobe`` calls it ``color_space``).
        color_range: ``tv`` or ``pc`` as tagged, or ``None``.
        duration_seconds: Duration of the video stream, else of the container.
        rotation_degrees: Clockwise rotation (0, 90, 180 or 270) a player applies: 0 when
            absent (no rotation metadata); ``None`` only when there is no video stream.
        tracks: One ``"<index>:<type>:<codec>"`` entry per stream.
        gopro_recording: GoPro recording number from the file name, or ``None``.
        gopro_chapter: GoPro chapter number (first chapter is 1), or ``None``.
        lrv_present: Whether an ``.LRV`` sidecar sits beside the file.
        category: The owner's CP1 category; always empty here.
        error: Why the probe failed (the row still exists), or ``None``.
    """

    path: Path
    size_bytes: int
    container: str
    codec: str
    width: int | None
    height: int | None
    frame_rate: float | None
    frame_rate_variable: bool | None
    bit_depth: int | None
    chroma_format: str | None
    color_primaries: str | None
    color_transfer: str | None
    color_matrix: str | None
    color_range: str | None
    duration_seconds: float | None
    rotation_degrees: int | None
    tracks: tuple[str, ...]
    gopro_recording: int | None
    gopro_chapter: int | None
    lrv_present: bool
    category: str = ""
    error: str | None = None


@dataclass(frozen=True)
class PhotoRecord:
    """One photo file and its metadata.

    Attributes:
        path: Path of the file; relative to the footage root when produced by ``scan``.
        size_bytes: File size in bytes (0 when the file could not be examined).
        format: Pillow format name, for example ``HEIF``, ``JPEG`` or ``PNG``.
        width: Stored pixel width, before the display rotation given by ``orientation``
            (for HEIF, before the ``irot`` rotation the decoder applies).
        height: Stored pixel height, likewise.
        bit_depth: Bits per sample, or ``None`` when it cannot be determined.
        color_profile: Description of the embedded ICC profile, or ``None``.
        orientation: EXIF orientation value 1 to 8, or ``None`` when absent.
        category: The owner's CP1 category; always empty here.
        error: Why the probe failed or a field is missing, or ``None``.
    """

    path: Path
    size_bytes: int
    format: str
    width: int | None
    height: int | None
    bit_depth: int | None
    color_profile: str | None
    orientation: int | None
    category: str = ""
    error: str | None = None


Record = VideoRecord | PhotoRecord


@dataclass(frozen=True)
class ScanResult:
    """What ``scan_tree`` found.

    Attributes:
        records: One record per video or photo, sorted by relative path.
        ignored: Files that are neither media nor sidecars.
        skipped: Files that vanished before they were read, plus folders that could not
            be listed.
        sidecars: ``.lrv`` and ``.thm`` files (not rows).
    """

    records: tuple[Record, ...]
    ignored: int
    skipped: int
    sidecars: int


class _ProbeError(Exception):
    """A probe could not produce its record; the message is a one-line reason."""


def _one_line(text: str, path: Path | None = None) -> str:
    """Make an error reason one line of at most ``_ERROR_MAX_CHARS`` characters.

    Tools quote the full path of the file in their messages; the row already names the
    file, so each quoted path is cut down to the file name and the room goes to the reason.
    """
    if path is not None:
        full = str(path)
        # Python reprs (Pillow messages) double the backslashes of a Windows path.
        for quoted in (full.replace("\\", "\\\\"), full, path.as_posix()):
            text = text.replace(quoted, path.name)
    collapsed = " ".join(text.split())
    if len(collapsed) > _ERROR_MAX_CHARS:
        return collapsed[: _ERROR_MAX_CHARS - 3] + "..."
    return collapsed


def parse_gopro_name(name: str) -> tuple[int | None, int | None]:
    """Read the recording and chapter numbers from a GoPro file name.

    Understands ``GX<cc><nnnn>``, ``GH<cc><nnnn>`` and ``GS<cc><nnnn>`` (chapter ``cc``,
    first chapter 01; recording ``nnnn``) and the legacy ``GOPR<nnnn>`` (chapter 1) and
    ``GP<cc><nnnn>`` (chapter ``cc`` + 1) forms. Matching is case-insensitive and ignores
    any extension.

    Args:
        name: A file name or stem such as ``GX010001.MP4``.

    Returns:
        ``(recording, chapter)``, or ``(None, None)`` for any other name.
    """
    stem = PurePath(name).stem
    if match := _GOPRO_MODERN.fullmatch(stem):
        return int(match.group(2)), int(match.group(1))
    if match := _GOPRO_LEGACY_FIRST.fullmatch(stem):
        return int(match.group(1)), 1
    if match := _GOPRO_LEGACY_NEXT.fullmatch(stem):
        return int(match.group(2)), int(match.group(1)) + 1
    return None, None


def lrv_beside(video: Path) -> bool:
    """Report whether a low-resolution ``.LRV`` sidecar sits beside a video.

    The sidecar has the same stem (``GOPR0001.MP4`` and ``GOPR0001.LRV``) or, for the
    modern GoPro names, the first two letters replaced by ``GL`` (``GX010001.MP4`` and
    ``GL010001.LRV``). Case is ignored, including the extension.

    Args:
        video: Path of the video file.

    Returns:
        True when a matching sidecar exists in the same directory; False otherwise,
        including when the directory cannot be listed.
    """
    stem = video.stem.lower()
    wanted = {f"{stem}.lrv"}
    if _GOPRO_MODERN.fullmatch(video.stem):
        wanted.add(f"gl{stem[2:]}.lrv")
    try:
        names = os.listdir(video.parent)
    except OSError:
        return False
    return any(name.lower() in wanted for name in names)


def _as_dict(value: object) -> dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _as_int(value: object) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        return int(value)
    return None


def _as_float(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        number = float(value)
    except ValueError:
        return None
    return number if math.isfinite(number) else None


def _as_text(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _parse_rate(value: object) -> float | None:
    """Parse an ``ffprobe`` rate such as ``30000/1001``; zero or unparsable gives None."""
    if not isinstance(value, str):
        return None
    numerator, _, denominator = value.partition("/")
    top = _as_float(numerator)
    bottom = _as_float(denominator) if denominator else 1.0
    if top is None or bottom is None or top <= 0 or bottom <= 0:
        return None
    return top / bottom


def _bit_depth(pix_fmt: str | None, bits_per_raw_sample: object) -> int | None:
    """Return bits per sample from the pixel format, else from ``bits_per_raw_sample``."""
    if pix_fmt:
        if match := _PIX_FMT_SEMIPLANAR.fullmatch(pix_fmt):
            return int(match.group(2))
        if match := _PIX_FMT_HIGH_DEPTH.fullmatch(pix_fmt):
            return int(match.group(1))
        if _PIX_FMT_EIGHT_BIT.fullmatch(pix_fmt):
            return 8
    return _as_int(bits_per_raw_sample)


def _chroma_format(pix_fmt: str | None) -> str | None:
    """Return the chroma subsampling of a pixel format as ``J:a:b``, or None if unknown."""
    if not pix_fmt:
        return None
    if match := _PIX_FMT_YUV.match(pix_fmt):
        return ":".join(match.groups())
    if pix_fmt in {"nv12", "nv21"}:
        return "4:2:0"
    if match := _PIX_FMT_SEMIPLANAR.fullmatch(pix_fmt):
        return {"0": "4:2:0", "2": "4:2:2", "4": "4:4:4"}.get(match.group(1))
    if pix_fmt.startswith(("gray", "ya")):
        return "4:0:0"
    if pix_fmt.startswith(("gbr", "rgb", "bgr")):
        return "4:4:4"
    return None


def _rotation_degrees(stream: Mapping[str, Any]) -> int:
    """Return the clockwise display rotation (0, 90, 180 or 270) a stream asks for.

    The display-matrix side data reports counter-clockwise degrees and is negated; the
    older ``rotate`` tag is already clockwise. The result is snapped to the nearest quarter
    turn. No rotation metadata means 0.
    """
    side_data = stream.get("side_data_list")
    if isinstance(side_data, list):
        for entry in side_data:
            rotation = _as_float(_as_dict(entry).get("rotation"))
            if rotation is not None:
                return round(-rotation / 90) * 90 % 360
    rotate = _as_float(_as_dict(stream.get("tags")).get("rotate"))
    return round(rotate / 90) * 90 % 360 if rotate is not None else 0


def _video_from_ffprobe(
    path: Path, size_bytes: int, data: Mapping[str, Any], lrv_present: bool
) -> VideoRecord:
    """Build a ``VideoRecord`` from parsed ``ffprobe -print_format json`` output.

    A document with no (non-cover-art) video stream still yields a record, with
    ``error`` set to ``"no video stream"``.

    Args:
        path: Path stored in the record.
        size_bytes: File size stored in the record.
        data: The parsed ``ffprobe`` document.
        lrv_present: Whether an ``.LRV`` sidecar sits beside the file.

    Returns:
        The record.
    """
    container_info = _as_dict(data.get("format"))
    raw_streams = data.get("streams")
    streams = [_as_dict(s) for s in raw_streams] if isinstance(raw_streams, list) else []
    video = next(
        (
            s
            for s in streams
            if s.get("codec_type") == "video"
            and not _as_dict(s.get("disposition")).get("attached_pic")
        ),
        None,
    )
    tracks = tuple(
        f"{_as_int(s.get('index')) if _as_int(s.get('index')) is not None else position}"
        f":{_as_text(s.get('codec_type')) or 'unknown'}"
        f":{_as_text(s.get('codec_name')) or 'unknown'}"
        for position, s in enumerate(streams)
    )
    recording, chapter = parse_gopro_name(path.name)
    common: dict[str, Any] = {
        "path": path,
        "size_bytes": size_bytes,
        "container": _as_text(container_info.get("format_name")) or "",
        "tracks": tracks,
        "gopro_recording": recording,
        "gopro_chapter": chapter,
        "lrv_present": lrv_present,
    }
    if video is None:
        return VideoRecord(
            codec="",
            width=None,
            height=None,
            frame_rate=None,
            frame_rate_variable=None,
            bit_depth=None,
            chroma_format=None,
            color_primaries=None,
            color_transfer=None,
            color_matrix=None,
            color_range=None,
            duration_seconds=_positive(_as_float(container_info.get("duration"))),
            rotation_degrees=None,
            error="no video stream",
            **common,
        )
    average = _parse_rate(video.get("avg_frame_rate"))
    nominal = _parse_rate(video.get("r_frame_rate"))
    variable = (
        abs(nominal - average) / nominal > _VFR_TOLERANCE
        if average is not None and nominal is not None
        else None
    )
    pix_fmt = _as_text(video.get("pix_fmt"))
    duration = _positive(_as_float(video.get("duration")))
    if duration is None:
        duration = _positive(_as_float(container_info.get("duration")))
    return VideoRecord(
        codec=_as_text(video.get("codec_name")) or "",
        width=_as_int(video.get("width")),
        height=_as_int(video.get("height")),
        frame_rate=average,
        frame_rate_variable=variable,
        bit_depth=_bit_depth(pix_fmt, video.get("bits_per_raw_sample")),
        chroma_format=_chroma_format(pix_fmt),
        color_primaries=_as_text(video.get("color_primaries")),
        color_transfer=_as_text(video.get("color_transfer")),
        color_matrix=_as_text(video.get("color_space")),
        color_range=_as_text(video.get("color_range")),
        duration_seconds=duration,
        rotation_degrees=_rotation_degrees(video),
        error=None,
        **common,
    )


def _positive(value: float | None) -> float | None:
    return value if value is not None and value >= 0 else None


def _failed_video(path: Path, size_bytes: int, error: str) -> VideoRecord:
    """Return a video row that carries only what the file name and folder reveal."""
    recording, chapter = parse_gopro_name(path.name)
    return VideoRecord(
        path=path,
        size_bytes=size_bytes,
        container="",
        codec="",
        width=None,
        height=None,
        frame_rate=None,
        frame_rate_variable=None,
        bit_depth=None,
        chroma_format=None,
        color_primaries=None,
        color_transfer=None,
        color_matrix=None,
        color_range=None,
        duration_seconds=None,
        rotation_degrees=None,
        tracks=(),
        gopro_recording=recording,
        gopro_chapter=chapter,
        lrv_present=lrv_beside(path),
        error=_one_line(error, path),
    )


def _run_ffprobe(path: Path) -> dict[str, Any]:
    """Run ``ffprobe`` on a file without a shell and return its parsed JSON.

    Raises:
        _ProbeError: If ``ffprobe`` is absent, times out, exits non-zero or prints
            something other than a JSON object.
    """
    command = [
        "ffprobe",
        "-v",
        "error",
        "-print_format",
        "json",
        "-show_format",
        "-show_streams",
        str(path),
    ]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=FFPROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        raise _ProbeError("ffprobe not found") from None
    except subprocess.TimeoutExpired:
        raise _ProbeError(f"ffprobe timed out after {FFPROBE_TIMEOUT_SECONDS:g} s") from None
    except OSError as exc:
        raise _ProbeError(f"ffprobe could not run: {exc}") from None
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise _ProbeError(f"ffprobe failed (status {result.returncode}): {detail}")
    try:
        data = json.loads(result.stdout.decode("utf-8", errors="replace"))
    except ValueError:
        raise _ProbeError("ffprobe output is not valid JSON") from None
    if not isinstance(data, dict):
        raise _ProbeError("ffprobe output is not a JSON object")
    return data


def probe_video(path: Path) -> VideoRecord:
    """Probe one video file with ``ffprobe``.

    Never raises: any failure yields a record whose ``error`` says why. The record's
    ``path`` is the path as given (``scan`` makes it relative to the footage root).

    Args:
        path: The video file.

    Returns:
        The record.
    """
    try:
        size_bytes = path.stat().st_size
    except OSError as exc:
        return _failed_video(path, 0, f"cannot read file: {exc.strerror or exc}")
    try:
        data = _run_ffprobe(path)
    except _ProbeError as exc:
        return _failed_video(path, size_bytes, str(exc))
    return _video_from_ffprobe(path, size_bytes, data, lrv_beside(path))


def _boxes(buf: bytes, start: int, end: int) -> list[tuple[bytes, int, int]]:
    """List the ISO base media boxes in ``buf[start:end]`` as (type, payload start, end)."""
    found = []
    while start + 8 <= end:
        size, kind = struct.unpack_from(">I4s", buf, start)
        header = 8
        if size == 1:
            (size,) = struct.unpack_from(">Q", buf, start + 8)
            header = 16
        elif size == 0:
            size = end - start
        if size < header or start + size > end:
            raise ValueError("box size out of range")
        found.append((kind, start + header, start + size))
        start += size
    return found


def _heif_meta_payload(path: Path) -> bytes:
    """Return the payload of the top-level ``meta`` box of a HEIF file.

    Raises:
        ValueError: If there is no ``meta`` box in the file, or it is implausibly large.
    """
    with path.open("rb") as handle:
        while head := handle.read(8):
            if len(head) < 8:
                break
            size, kind = struct.unpack(">I4s", head)
            header = 8
            if size == 1:
                (size,) = struct.unpack(">Q", handle.read(8))
                header = 16
            if kind == b"meta":
                if not header <= size <= _HEIF_META_MAX_BYTES:
                    raise ValueError("meta box size out of range")
                return handle.read(size - header)
            if size < header:
                break
            handle.seek(size - header, os.SEEK_CUR)
    raise ValueError("no meta box")


def _primary_item_properties(meta: bytes) -> list[tuple[bytes, int]]:
    """Return the (type, payload start) of every property linked to the primary item.

    Raises:
        ValueError: If the boxes needed to find them are missing or malformed.
    """
    children = _boxes(meta, 4, len(meta))  # meta is a FullBox: skip its version and flags
    primary = next((b for b in children if b[0] == b"pitm"), None)
    properties = next((b for b in children if b[0] == b"iprp"), None)
    if primary is None or properties is None:
        raise ValueError("no pitm or iprp box")
    item_format = ">H" if meta[primary[1]] == 0 else ">I"
    (item_id,) = struct.unpack_from(item_format, meta, primary[1] + 4)
    inside = _boxes(meta, properties[1], properties[2])
    container = next((b for b in inside if b[0] == b"ipco"), None)
    if container is None:
        raise ValueError("no ipco box")
    candidates = _boxes(meta, container[1], container[2])
    indexes: set[int] = set()
    for kind, begin, _end in inside:
        if kind != b"ipma":
            continue
        entry_format = ">H" if meta[begin] == 0 else ">I"
        entry_size = struct.calcsize(entry_format)
        wide = bool(meta[begin + 3] & 1)
        (count,) = struct.unpack_from(">I", meta, begin + 4)
        position = begin + 8
        for _ in range(count):
            (entry,) = struct.unpack_from(entry_format, meta, position)
            links = meta[position + entry_size]
            position += entry_size + 1
            for _ in range(links):
                if wide:
                    (link,) = struct.unpack_from(">H", meta, position)
                    index = link & 0x7FFF
                    position += 2
                else:
                    index = meta[position] & 0x7F
                    position += 1
                if entry == item_id:
                    indexes.add(index)
    return [(candidates[i - 1][0], candidates[i - 1][1]) for i in sorted(indexes) if i >= 1]


def _heif_axes_swapped(path: Path) -> bool | None:
    """Tell whether the primary image of a HEIF file carries a quarter-turn ``irot``.

    The decoder applies that transformation, so the size it reports has width and height
    exchanged relative to the stored image. The EXIF orientation is deliberately not used:
    it can disagree with the container (a file may carry EXIF orientation 6 and no ``irot``).

    Args:
        path: The HEIF file.

    Returns:
        True when the primary image has an ``irot`` of 90 or 270 degrees, False when it has
        none or a half turn, and None when the container could not be parsed.
    """
    try:
        meta = _heif_meta_payload(path)
        for kind, begin in _primary_item_properties(meta):
            if kind == b"irot":
                return meta[begin] & 3 in (1, 3)
    except (OSError, ValueError, IndexError, struct.error):
        return None
    return False


def _failed_photo(path: Path, size_bytes: int, error: str) -> PhotoRecord:
    return PhotoRecord(
        path=path,
        size_bytes=size_bytes,
        format="",
        width=None,
        height=None,
        bit_depth=None,
        color_profile=None,
        orientation=None,
        error=_one_line(error, path),
    )


def _icc_description(profile: object) -> str | None:
    if not isinstance(profile, bytes) or not profile:
        return None
    try:
        description = ImageCms.getProfileDescription(ImageCms.ImageCmsProfile(io.BytesIO(profile)))
    except Exception:  # LittleCMS raises ImageCmsError, OSError and others on bad profiles.
        return None
    return " ".join(description.split()) or None


def _png_bit_depth(path: Path) -> int | None:
    """Read the bit depth from the PNG header chunk (Pillow converts 16-bit RGB on load)."""
    with path.open("rb") as handle:
        header = handle.read(25)
    if len(header) == 25 and header.startswith(_PNG_SIGNATURE) and header[12:16] == b"IHDR":
        return header[24]
    return None


def _photo_bit_depth(image: Image.Image, path: Path) -> int | None:
    """Return the bits per sample of an open image, or None when it cannot be told."""
    if image.format == "HEIF":
        return _as_int(image.info.get("bit_depth"))
    if image.format == "PNG":
        return _png_bit_depth(path)
    if image.format == "TIFF":
        bits = getattr(image, "tag_v2", {}).get(_TIFF_BITS_PER_SAMPLE)
        if isinstance(bits, int):
            return bits
        if isinstance(bits, tuple) and bits and all(isinstance(b, int) for b in bits):
            return int(max(bits))
    return _BIT_DEPTH_BY_MODE.get(image.mode)


def probe_photo(path: Path) -> PhotoRecord:
    """Read a photo's header with Pillow (and pillow-heif for HEIC); no pixels are decoded.

    Never raises: any failure yields a record whose ``error`` says why. ``width`` and
    ``height`` are the stored dimensions, before the display rotation given by
    ``orientation``. For HEIF the decoder has already applied the container's ``irot``
    rotation, so width and height are swapped back exactly when the primary image has a
    quarter-turn ``irot`` (read from the container, never inferred from EXIF); when the
    container cannot be parsed they stay as decoded and ``error`` says so. A missing bit
    depth (HEIC without pillow-heif's figure) leaves ``bit_depth`` ``None`` with a reason
    in ``error``.

    Args:
        path: The photo file.

    Returns:
        The record. Its ``path`` is the path as given.
    """
    try:
        size_bytes = path.stat().st_size
    except OSError as exc:
        return _failed_photo(path, 0, f"cannot read file: {exc.strerror or exc}")
    pillow_heif.register_heif_opener()
    try:
        with Image.open(path) as image:
            width, height = image.size
            is_heif = image.format == "HEIF"
            raw_orientation = image.info.get("original_orientation") if is_heif else None
            if raw_orientation is None:
                raw_orientation = image.getexif().get(_EXIF_ORIENTATION)
            orientation = _as_int(raw_orientation)
            if orientation is not None and not 1 <= orientation <= 8:
                orientation = None
            problems = []
            if is_heif:
                swapped = _heif_axes_swapped(path)
                if swapped:
                    width, height = height, width
                elif swapped is None:
                    problems.append("HEIF rotation unreadable, width and height as decoded")
            bit_depth = _photo_bit_depth(image, path)
            if bit_depth is None:
                problems.append(f"bit depth unavailable ({image.mode})")
            record = PhotoRecord(
                path=path,
                size_bytes=size_bytes,
                format=image.format or "",
                width=width,
                height=height,
                bit_depth=bit_depth,
                color_profile=_icc_description(image.info.get("icc_profile")),
                orientation=orientation,
                error="; ".join(problems) or None,
            )
    except Exception as exc:  # Pillow and pillow-heif raise many types on bad input.
        return _failed_photo(path, size_bytes, f"cannot read image: {type(exc).__name__}: {exc}")
    return record


def scan_tree(footage_root: Path) -> ScanResult:
    """Walk the footage folder read-only and probe every video and photo.

    Symbolic links to folders are not followed. A file that vanishes before it is read
    is counted as skipped; any other per-file failure becomes a row with ``error`` set.

    Args:
        footage_root: The footage folder; nothing is created or changed under it.

    Returns:
        The records (relative paths, sorted) and the counts of other files.
    """
    skipped = 0
    ignored = 0
    sidecars = 0
    found: list[tuple[str, Path, bool]] = []

    def on_walk_error(_error: OSError) -> None:
        nonlocal skipped
        skipped += 1

    for directory, _folders, names in os.walk(footage_root, onerror=on_walk_error):
        for name in names:
            suffix = Path(name).suffix.lower()
            full = Path(directory) / name
            if suffix in VIDEO_EXTENSIONS or suffix in PHOTO_EXTENSIONS:
                relative = full.relative_to(footage_root)
                found.append((relative.as_posix(), full, suffix in VIDEO_EXTENSIONS))
            elif suffix in SIDECAR_EXTENSIONS:
                sidecars += 1
            else:
                ignored += 1
    found.sort(key=lambda item: item[0])

    records: list[Record] = []
    for relative_text, full, is_video in found:
        try:
            full.stat()
        except FileNotFoundError:
            skipped += 1
            continue
        except OSError:
            pass  # The probe reports it as the row's error.
        relative = Path(relative_text)
        try:
            record: Record = probe_video(full) if is_video else probe_photo(full)
        except Exception as exc:  # A bug or odd file must not abort the whole inventory.
            reason = f"unexpected failure: {type(exc).__name__}: {exc}"
            record = _failed_video(full, 0, reason) if is_video else _failed_photo(full, 0, reason)
        records.append(dataclasses.replace(record, path=relative))
    return ScanResult(tuple(records), ignored, skipped, sidecars)


def scan(footage_root: Path) -> list[Record]:
    """List every video and photo under the footage folder.

    Recursive and sorted by relative path. Video extensions are ``.mp4 .mov .360``; photo
    extensions are ``.heic .heif .jpg .jpeg .png .tif .tiff``; ``.lrv`` and ``.thm`` files
    are sidecars, not rows. Files are opened read-only and nothing is created under the
    root. See ``scan_tree`` for the counts of ignored and skipped files.

    Args:
        footage_root: The footage folder.

    Returns:
        One record per media file, with ``path`` relative to ``footage_root``.
    """
    return list(scan_tree(footage_root).records)


def _cell(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.6g}"
    if isinstance(value, tuple):
        return ";".join(str(item) for item in value)
    if isinstance(value, Path):
        return value.as_posix()
    return str(value)


def _csv_row(record: Record) -> dict[str, str]:
    kind = "video" if isinstance(record, VideoRecord) else "photo"
    row = {column: "" for column in CSV_COLUMNS}
    row["kind"] = kind
    for field in dataclasses.fields(record):
        row[field.name] = _cell(getattr(record, field.name))
    if isinstance(record, VideoRecord) and record.duration_seconds is not None:
        row["duration_seconds"] = f"{record.duration_seconds:.3f}"
    return row


def _mode_label(record: VideoRecord) -> str:
    size = f"{record.width or '?'}x{record.height or '?'}"
    rate = f"{round(record.frame_rate, 3):g}" if record.frame_rate is not None else "?"
    depth = f"{record.bit_depth}-bit" if record.bit_depth is not None else "?-bit"
    return f"{size} @ {rate} {record.codec or '?'} {depth} {record.chroma_format or '?'}"


def _count_lines(counter: Counter[str]) -> list[str]:
    ordered = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [f"- {label}: {count}" for label, count in ordered] or ["- none"]


def _chaptered(videos: Sequence[VideoRecord]) -> list[str]:
    groups: dict[tuple[str, int], list[VideoRecord]] = {}
    for video in videos:
        if video.gopro_recording is not None and video.gopro_chapter is not None:
            key = (video.path.parent.as_posix(), video.gopro_recording)
            groups.setdefault(key, []).append(video)
    lines = []
    for (folder, recording), members in sorted(groups.items()):
        chapters = sorted({m.gopro_chapter for m in members if m.gopro_chapter is not None})
        if len(chapters) > 1:
            where = "" if folder == "." else f"{folder}/"
            listing = ", ".join(str(c) for c in chapters)
            lines.append(f"- {where}recording {recording:04d}: chapters {listing}")
    return lines or ["- none"]


def _summary_text(
    records: Sequence[Record],
    stamp: str,
    footage_root: Path | None,
    ignored: int,
    skipped: int,
    sidecars: int,
) -> str:
    videos = [r for r in records if isinstance(r, VideoRecord)]
    photos = [r for r in records if isinstance(r, PhotoRecord)]
    failing = [r for r in records if r.error is not None]
    with_lrv = sum(1 for v in videos if v.lrv_present)
    lines = ["# Footage inventory summary", "", f"- Run stamp (UTC): {stamp}"]
    if footage_root is not None:
        lines.append(f"- Footage folder: {footage_root.as_posix()}")
    lines += [
        f"- {_DIMENSIONS_NOTE}",
        "",
        "## Counts",
        "",
        f"- Videos: {len(videos)}",
        f"- Photos: {len(photos)}",
        f"- Files with probe errors: {len(failing)}",
        f"- Ignored files (not media, not sidecars): {ignored}",
        f"- Sidecar files (.lrv, .thm; not rows): {sidecars}",
        f"- Skipped (vanished before reading, or folder not listable): {skipped}",
        "",
        "## Video recording modes",
        "",
        "Width x height @ frame rate, codec, bit depth, chroma format (files without errors).",
        "",
        *_count_lines(Counter(_mode_label(v) for v in videos if v.error is None)),
        "",
        f"Variable frame rate: {sum(1 for v in videos if v.frame_rate_variable)}",
        "",
        "## Photo sizes",
        "",
        "Stored width x height (files without errors).",
        "",
        *_count_lines(Counter(f"{p.width}x{p.height}" for p in photos if p.error is None)),
        "",
        "## Photo formats",
        "",
        *_count_lines(Counter(p.format for p in photos if p.format)),
        "",
        "## Chaptered recordings",
        "",
        "Recording numbers with more than one chapter (chapters are recorded, not joined).",
        "",
        *_chaptered(videos),
        "",
        "## .LRV coverage",
        "",
        f"- Videos with an .LRV sidecar: {with_lrv} of {len(videos)}",
        "",
        "## Files with probe errors",
        "",
        *([f"- {r.path.as_posix()}: {r.error}" for r in failing] or ["- none"]),
        "",
    ]
    return "\n".join(lines)


def write_inventory(
    records: Sequence[Record],
    working: Path,
    *,
    ignored: int = 0,
    skipped: int = 0,
    sidecars: int = 0,
    footage_root: Path | None = None,
    stamp: str | None = None,
) -> tuple[Path, Path]:
    """Write the inventory CSV and its summary under ``<working>/reports``.

    The CSV is ``inventory-<stamp>.csv`` (UTF-8 with a byte-order mark so Excel opens it;
    one row per record; ``category`` empty) and the summary is ``inventory-<stamp>-summary.md``.
    Each file is written to a temporary name first and only then given its final name, so a
    failed write leaves no partial report. An existing report is never overwritten: when either
    name exists, both files take the same ``-N`` suffix (``inventory-<stamp>-1.csv``, ...).

    Args:
        records: The records to write.
        working: The working folder; ``reports`` below it is created when absent.
        ignored: Count of ignored files, for the summary.
        skipped: Count of skipped files, for the summary.
        sidecars: Count of sidecar files, for the summary.
        footage_root: Footage folder to name in the summary, if any.
        stamp: ``YYYYMMDDTHHMMSSZ`` text for the file names; defaults to the current UTC time.

    Returns:
        The paths of the CSV and the summary.

    Raises:
        OSError: If the folder cannot be created or a file cannot be written.
    """
    stamp = stamp or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    reports = working / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    summary_text = _summary_text(records, stamp, footage_root, ignored, skipped, sidecars)

    def write_csv(handle: IO[str]) -> None:
        writer = csv.DictWriter(handle, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        writer.writerows(_csv_row(record) for record in records)

    staged: list[Path] = []
    try:
        csv_temp = _stage(reports, "utf-8-sig", "", write_csv)
        staged.append(csv_temp)
        summary_temp = _stage(reports, "utf-8", "\n", lambda handle: handle.write(summary_text))
        staged.append(summary_temp)
        attempt = 0
        while True:
            suffix = f"-{attempt}" if attempt else ""
            csv_path = reports / f"inventory-{stamp}{suffix}.csv"
            summary_path = reports / f"inventory-{stamp}{suffix}-summary.md"
            attempt += 1
            try:
                _publish(csv_temp, csv_path)
            except FileExistsError:
                continue
            try:
                _publish(summary_temp, summary_path)
            except FileExistsError:
                csv_path.unlink()  # Give the CSV back and try the next suffix.
                continue
            except BaseException:
                csv_path.unlink(missing_ok=True)
                raise
            return csv_path, summary_path
    finally:
        for temp in staged:
            with contextlib.suppress(OSError):
                temp.unlink(missing_ok=True)


def _stage(reports: Path, encoding: str, newline: str, write: Callable[[IO[str]], object]) -> Path:
    """Write a report to a new temporary file in ``reports`` and return its path.

    The temporary file is removed again if writing fails.
    """
    descriptor, name = tempfile.mkstemp(dir=reports, prefix=".inventory-", suffix=".tmp")
    temp = Path(name)
    try:
        with os.fdopen(descriptor, "w", encoding=encoding, newline=newline) as handle:
            write(handle)
    except BaseException:
        temp.unlink(missing_ok=True)
        raise
    return temp


def _publish(temp: Path, final: Path) -> None:
    """Give a finished temporary file its final name without replacing any existing file.

    The temporary file is kept (the caller removes it), so a published report can be
    withdrawn and published again under another name. A hard link makes the final name
    appear complete in one step; on a volume without hard links the content is copied
    into an exclusively created file, which is removed again if the copy fails.

    Raises:
        FileExistsError: If ``final`` already exists; it is left untouched.
        OSError: If the file cannot be written; no ``final`` is left behind.
    """
    try:
        os.link(temp, final)
    except FileExistsError:
        raise
    except OSError:
        pass  # No hard links here: fall back to a copy.
    else:
        return
    try:
        with temp.open("rb") as source, final.open("xb") as target:
            shutil.copyfileobj(source, target)
    except FileExistsError:
        raise
    except BaseException:
        final.unlink(missing_ok=True)
        raise


def _resolved(path: Path) -> Path:
    return Path(os.path.normcase(path.resolve()))


def main(argv: list[str] | None = None) -> int:
    """Inventory the footage folder and print the paths of the two reports.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2 (with a one-line ``error: ...`` on standard error) when the
        configuration cannot be loaded, the footage folder is missing, the working folder
        lies inside it, or the reports cannot be written.
    """
    parser = argparse.ArgumentParser(description="Inventory the footage folder (read-only).")
    parser.add_argument("--config", type=Path, help="local configuration file to read")
    parser.add_argument("--footage", type=Path, help="footage folder instead of the configured one")
    parser.add_argument("--out", type=Path, help="working folder instead of the configured one")
    args = parser.parse_args(argv)

    footage: Path | None = args.footage
    working: Path | None = args.out
    if footage is None or working is None:
        try:
            config = load_local_config(args.config)
        except LocalConfigError as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2
        footage = config.footage_path if footage is None else footage
        working = config.working_path if working is None else working

    if not footage.is_dir():
        print(f"error: footage folder not found: {footage}", file=sys.stderr)
        return 2
    footage_resolved = _resolved(footage)
    # The reports folder is checked too: it may be a link that leads back into the footage.
    for target in (working, working / "reports"):
        target_resolved = _resolved(target)
        if target_resolved == footage_resolved or footage_resolved in target_resolved.parents:
            print(
                f"error: working folder {working} must lie outside the footage folder",
                file=sys.stderr,
            )
            return 2
    try:
        (working / "reports").mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print(f"error: cannot write under the working folder {working}: {exc}", file=sys.stderr)
        return 2

    print(f"Scanning {footage} ...")
    result = scan_tree(footage)
    try:
        csv_path, summary_path = write_inventory(
            result.records,
            working,
            ignored=result.ignored,
            skipped=result.skipped,
            sidecars=result.sidecars,
            footage_root=footage,
        )
    except OSError as exc:
        print(f"error: cannot write the reports under {working}: {exc}", file=sys.stderr)
        return 2
    print(csv_path)
    print(summary_path)
    print(
        "Next (checkpoint CP1): fill the category column with one of: "
        + "; ".join(CATEGORY_REMINDER)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
