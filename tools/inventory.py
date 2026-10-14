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
import csv
import dataclasses
import io
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path, PurePath
from typing import Any

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
        rotation_degrees: Clockwise rotation (0, 90, 180 or 270) a player applies; ``None``
            only when there is no video stream.
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
        width: Stored pixel width, before the display rotation given by ``orientation``.
        height: Stored pixel height, before the display rotation given by ``orientation``.
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


def _one_line(text: str) -> str:
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
    older ``rotate`` tag is already clockwise. No rotation metadata means 0.
    """
    side_data = stream.get("side_data_list")
    if isinstance(side_data, list):
        for entry in side_data:
            rotation = _as_float(_as_dict(entry).get("rotation"))
            if rotation is not None:
                return round(-rotation) % 360
    rotate = _as_float(_as_dict(stream.get("tags")).get("rotate"))
    return round(rotate) % 360 if rotate is not None else 0


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
        error=_one_line(error),
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
        error=_one_line(error),
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
    ``height`` are the stored dimensions: for HEIF, where the library applies the
    container's rotation on load, they are swapped back when ``orientation`` is 5 to 8, so
    all formats report the same convention. A missing bit depth (HEIC without
    pillow-heif's figure) leaves ``bit_depth`` ``None`` with a reason in ``error``.

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
            if is_heif and orientation is not None and orientation >= 5:
                width, height = height, width
            bit_depth = _photo_bit_depth(image, path)
            record = PhotoRecord(
                path=path,
                size_bytes=size_bytes,
                format=image.format or "",
                width=width,
                height=height,
                bit_depth=bit_depth,
                color_profile=_icc_description(image.info.get("icc_profile")),
                orientation=orientation,
                error=None if bit_depth is not None else f"bit depth unavailable ({image.mode})",
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
        *_count_lines(Counter(f"{p.width}x{p.height}" for p in photos if p.width and p.height)),
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
    Files are created exclusively, so an existing report is never overwritten: when either
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
    attempt = 0
    while True:
        suffix = f"-{attempt}" if attempt else ""
        csv_path = reports / f"inventory-{stamp}{suffix}.csv"
        summary_path = reports / f"inventory-{stamp}{suffix}-summary.md"
        attempt += 1
        try:
            csv_handle = csv_path.open("x", encoding="utf-8-sig", newline="")
        except FileExistsError:
            continue
        with csv_handle:
            try:
                summary_handle = summary_path.open("x", encoding="utf-8", newline="\n")
            except FileExistsError:
                summary_handle = None
            if summary_handle is not None:
                with summary_handle:
                    summary_handle.write(summary_text)
                writer = csv.DictWriter(csv_handle, fieldnames=CSV_COLUMNS)
                writer.writeheader()
                writer.writerows(_csv_row(record) for record in records)
                return csv_path, summary_path
        csv_path.unlink()  # The summary name was taken: give the CSV back and try the next suffix.


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
