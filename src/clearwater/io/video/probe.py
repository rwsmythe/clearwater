"""Probe one video file into an IF-5 :class:`ProbeResult` (WP3.7).

The probe runs ``ffprobe`` three times at most: one call for the container and stream facts, one
for the video packets (timing, variable frame rate, truncation) and, only when the file is not
already known to be cut short, one bounded decode of the last group of pictures to see whether
the end of the file is readable. It never decodes a whole file. Every time is an exact
``Fraction`` built from integer ticks and a stream time base; no decimal string that ffprobe
prints is parsed into a time. The ``ffprobe`` calls name the fields they want, so container and
stream tags (which can carry identifiers) are never requested.

The edit list and the GoPro settings come from :mod:`clearwater.io.video.boxes` and
:mod:`clearwater.io.video.gopro`.
"""

from __future__ import annotations

import itertools
import json
import logging
import math
import re
import shutil
import subprocess
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any, Literal

from clearwater.interfaces.image import ColorDescription
from clearwater.interfaces.video import (
    AudioStreamInfo,
    DataStreamInfo,
    EditEntry,
    Fault,
    GoProInfo,
    ProbeResult,
    VideoStreamInfo,
)
from clearwater.io.video.boxes import BoxError, MovieBoxes, read_movie_boxes
from clearwater.io.video.gopro import GPMFError, parse_settings
from clearwater.io.video.inputs import is_sidecar

_log = logging.getLogger(__name__)

TOOL_TIMEOUT_S = 120
"""Seconds an ``ffprobe`` call may run before the file is reported as unreadable."""

_STREAM_FIELDS = (
    "index,codec_type,codec_name,codec_tag_string,width,height,pix_fmt,chroma_location,"
    "color_range,color_space,color_transfer,color_primaries,r_frame_rate,avg_frame_rate,"
    "time_base,start_pts,duration_ts,nb_frames,sample_rate,channels"
)
_STREAMS_ENTRIES = (
    f"format=format_name:stream={_STREAM_FIELDS}:stream_side_data=rotation,displaymatrix"
)

_TAIL_SPAN_S = 86400
"""End offset of the tail interval. An open-ended ``-read_intervals`` interval drops frames at
random on ffprobe 9.0.2 (measured: about 1 run in 50 delivered a partial frame list with no
error), which would read as a false unreadable tail; an explicit end does not (0 in 500 runs)."""

_ACCEPTED_CODECS = frozenset({"hevc", "h264"})
_PIX_FMT = re.compile(r"^yuvj?4\d\dp(\d\d)?(?:le|be)?$")
_MATRIX_ROW = re.compile(r"^\d+:\s+(-?\d+)\s+(-?\d+)\s+(-?\d+)\s*$", re.MULTILINE)

_UNSET = frozenset({"", "unknown", "unspecified"})
_PRIMARIES = {"bt709": "bt709", "smpte432": "display-p3"}
_TRANSFER = {"bt709": "bt709", "iec61966-2-1": "srgb"}
_MATRIX = {"bt709": "bt709", "smpte170m": "bt601", "bt470bg": "bt601", "gbr": "identity"}
_RANGE = {"pc": "full", "tv": "limited"}
_HDR_TRANSFER: dict[str, Literal["hlg", "pq"]] = {"arib-std-b67": "hlg", "smpte2084": "pq"}
_GP_LOG_PROFILES = frozenset({"NATURAL", "FLAT", "VIBRANT"})

ProbeErrorKind = Literal["unreadable", "unsupported", "sidecar", "missing_tool"]


class VideoProbeError(Exception):
    """A file cannot be probed: it is unreadable, unsupported, a sidecar, or ffprobe is absent.

    Attributes:
        kind: ``"unreadable"`` (cannot be read at all, spec 5.4), ``"unsupported"`` (a container,
            codec, pixel format or orientation outside the supported set), ``"sidecar"`` (an
            excluded ``.LRV`` or ``.THM``, D83) or ``"missing_tool"`` (no ``ffprobe``).
    """

    def __init__(self, kind: ProbeErrorKind, message: str) -> None:
        """Store the kind and the user-readable message.

        Args:
            kind: The reason class.
            message: A message the GUI can show (G10).
        """
        super().__init__(message)
        self.kind: ProbeErrorKind = kind


def find_tool(name: str) -> Path:
    """Locate an FFmpeg command-line tool on the PATH.

    WP3.9 and WP3.10 use this too, for ``ffmpeg``.

    Args:
        name: The tool name, for example ``"ffprobe"`` or ``"ffmpeg"``.

    Returns:
        The tool's path.

    Raises:
        VideoProbeError: With kind ``"missing_tool"`` when it is not on the PATH.
    """
    found = shutil.which(name)
    if found is None:
        raise VideoProbeError(
            "missing_tool",
            f"{name} was not found on the PATH. Install FFmpeg and make sure {name} can be run "
            "from a command prompt.",
        )
    return Path(found)


def _run_ffprobe(args: Sequence[str]) -> tuple[int, str, str]:
    """Run ``ffprobe`` with the given arguments and return exit status, stdout and stderr."""
    command = [str(find_tool("ffprobe")), *args]
    try:
        done = subprocess.run(command, capture_output=True, timeout=TOOL_TIMEOUT_S, check=False)
    except subprocess.TimeoutExpired as error:
        raise VideoProbeError(
            "unreadable", "The file took too long to read and was given up on."
        ) from error
    except OSError as error:
        raise VideoProbeError("unreadable", f"ffprobe could not be run: {error}") from error
    return (
        done.returncode,
        done.stdout.decode("utf-8", errors="replace"),
        done.stderr.decode("utf-8", errors="replace"),
    )


def _json(text: str, path: Path) -> dict[str, Any]:
    """Parse ffprobe's JSON output, or raise the unreadable-file error."""
    try:
        data = json.loads(text)
    except ValueError as error:
        raise VideoProbeError("unreadable", _unreadable(path)) from error
    if not isinstance(data, dict):
        raise VideoProbeError("unreadable", _unreadable(path))
    return data


def _unreadable(path: Path) -> str:
    """Return the message for a file that cannot be read at all (spec 5.4)."""
    return f"{path.name} cannot be read as a video file; it may be damaged or not a video."


def _fraction(text: object) -> Fraction | None:
    """Parse a rational such as ``"30000/1001"``; None when absent, malformed or zero-valued."""
    try:
        value = Fraction(str(text))
    except (ValueError, ZeroDivisionError):
        return None
    return value if value != 0 else None


def _int(value: object) -> int | None:
    """Return an int from an int or an integer string; None otherwise."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and re.fullmatch(r"-?\d+", value):
        return int(value)
    return None


def _ticks(value: object, time_base: Fraction | None) -> Fraction | None:
    """Convert integer ticks of a time base to seconds, or None when either is missing."""
    ticks = _int(value)
    return None if ticks is None or time_base is None else ticks * time_base


def _bit_depth(pix_fmt: str, path: Path) -> int:
    """Return the bit depth a pixel format name says (8 or 10), or refuse the file."""
    match = _PIX_FMT.match(pix_fmt)
    depth = 8 if match is None or match.group(1) is None else int(match.group(1))
    if match is None or depth not in (8, 10):
        raise VideoProbeError(
            "unsupported",
            f"{path.name} uses the pixel format {pix_fmt}; only 8-bit and 10-bit YUV video is "
            "supported.",
        )
    return depth


def _matrix_rows(text: object) -> list[tuple[int, int, int]]:
    """Parse the three rows of the display matrix text ffprobe prints."""
    if not isinstance(text, str):
        return []
    return [(int(a), int(b), int(c)) for a, b, c in _MATRIX_ROW.findall(text)]


def _rotation(stream: Mapping[str, Any], path: Path) -> int:
    """Return the display rotation, counter-clockwise positive, as 0, 90, 180 or 270 (AD-20).

    Raises:
        VideoProbeError: With kind ``"unsupported"`` for a mirrored matrix or an angle that is
            not a multiple of 90 degrees (rounding would mis-orient the output, D105).
    """
    for item in stream.get("side_data_list") or []:
        if not isinstance(item, Mapping) or "rotation" not in item:
            continue
        rows = _matrix_rows(item.get("displaymatrix"))
        if len(rows) >= 2:
            determinant = rows[0][0] * rows[1][1] - rows[0][1] * rows[1][0]
            if determinant < 0:
                raise VideoProbeError(
                    "unsupported", f"{path.name} is stored mirrored, which is not supported."
                )
        try:
            angle = Fraction(str(item["rotation"])) % 360
        except (ValueError, ZeroDivisionError) as error:
            raise VideoProbeError("unreadable", _unreadable(path)) from error
        if angle % 90 != 0:
            raise VideoProbeError(
                "unsupported",
                f"{path.name} is rotated by {item['rotation']} degrees; only multiples of 90 "
                "degrees are supported.",
            )
        return int(angle)
    return 0


@dataclass(frozen=True)
class _Color:
    """The colour resolution of one video stream."""

    description: ColorDescription
    defaulted: tuple[str, ...]
    transfer_missing: bool
    hdr: Literal["hlg", "pq"] | None


def _tag(stream: Mapping[str, Any], key: str) -> str | None:
    """Return a colour tag string, or None when absent, empty or unspecified."""
    value = stream.get(key)
    if not isinstance(value, str) or value in _UNSET:
        return None
    return value


def _resolve(
    tag: str | None, table: Mapping[str, str], default: str, name: str, defaulted: list[str]
) -> str:
    """Map one colour tag, or apply the D54 default and record why."""
    if tag is None:
        defaulted.append(f"{name} missing")
        return default
    if tag in table:
        return table[tag]
    defaulted.append(f"{name} {tag} unexpected")
    return default


def _resolve_color(stream: Mapping[str, Any], pix_fmt: str, bit_depth: int) -> _Color:
    """Map ffprobe's colour tags to the IF-1 vocabulary, applying D54 per field.

    A ``yuvj`` pixel format with no range tag is a full-range signal and needs no default
    (ruling 7.3). HLG and PQ transfers are not mapped: the result carries ``transfer="unknown"``
    and the caller raises the refusal.
    """
    primaries, transfer = _tag(stream, "color_primaries"), _tag(stream, "color_transfer")
    matrix, range_tag = _tag(stream, "color_space"), _tag(stream, "color_range")
    j_format = pix_fmt.startswith("yuvj")
    hdr = _HDR_TRANSFER.get(transfer or "")
    if hdr is not None:
        description = ColorDescription(
            primaries=_PRIMARIES.get(primaries or "", "unknown"),
            transfer="unknown",
            matrix=_MATRIX.get(matrix or "", "unknown"),
            range=_RANGE.get(range_tag or "", "full" if j_format else "limited"),
            bit_depth=bit_depth,
            assumed=False,
            icc_profile=None,
        )
        return _Color(description, (), False, hdr)
    defaulted: list[str] = []
    if range_tag is None and j_format:
        range_value = "full"
    else:
        range_value = _resolve(range_tag, _RANGE, "limited", "range", defaulted)
    description = ColorDescription(
        primaries=_resolve(primaries, _PRIMARIES, "bt709", "primaries", defaulted),
        transfer=_resolve(transfer, _TRANSFER, "bt709", "transfer", defaulted),
        matrix=_resolve(matrix, _MATRIX, "bt709", "matrix", defaulted),
        range=range_value,
        bit_depth=bit_depth,
        assumed=bool(defaulted),
        icc_profile=None,
    )
    return _Color(description, tuple(defaulted), transfer is None, None)


def _packets(text: str, path: Path) -> list[tuple[int | None, int | None, str]]:
    """Parse the packet list into ``(pts, duration, flags)`` triples in file order."""
    items = _json(text, path).get("packets") or []
    return [
        (_int(item.get("pts")), _int(item.get("duration")), str(item.get("flags", "")))
        for item in items
        if isinstance(item, Mapping)
    ]


def _is_variable(pts: Sequence[int]) -> bool:
    """Return whether the presentation times step by more than one tick count (D95).

    The pts values are sorted first, so B-frame reordering does not matter. The last frame has
    no following frame and contributes no step.
    """
    ordered = sorted(pts)
    return len({b - a for a, b in itertools.pairwise(ordered)}) > 1


def _frame_rate(
    stream: Mapping[str, Any], pts: Sequence[int], time_base: Fraction, path: Path
) -> Fraction:
    """Return the average frame rate: ffprobe's rational, else frames over the pts span."""
    rate = _fraction(stream.get("avg_frame_rate"))
    if rate is not None:
        return rate
    if len(pts) >= 2 and max(pts) > min(pts):
        return Fraction(len(pts) - 1) / ((max(pts) - min(pts)) * time_base)
    rate = _fraction(stream.get("r_frame_rate"))
    if rate is None:
        raise VideoProbeError("unreadable", _unreadable(path))
    return rate


def _seek_string(seconds: Fraction) -> str:
    """Format a seek position, rounded up to a microsecond (a command argument, not a time)."""
    micro = max(0, math.ceil(seconds * 1_000_000))
    return f"{micro // 1_000_000}.{micro % 1_000_000:06d}"


def _tail_unreadable(
    path: Path, packets: Sequence[tuple[int | None, int | None, str]], time_base: Fraction
) -> bool:
    """Decode only the last group of pictures and report whether its end is unreadable.

    The decode starts at the last keyframe, so its cost does not grow with the clip. The tail is
    unreadable when ffprobe writes any error line, exits nonzero, or does not deliver the last
    packet's frame. A stream whose packets carry no keyframe flag is not checked.
    """
    keyframes = [pts for pts, _, flags in packets if pts is not None and "K" in flags]
    last = max((pts for pts, _, _ in packets if pts is not None), default=None)
    if not keyframes or last is None:
        return False
    start = _seek_string(max(keyframes) * time_base)
    status, out, err = _run_ffprobe(
        [
            "-v",
            "error",
            "-of",
            "json",
            "-select_streams",
            "v:0",
            "-read_intervals",
            f"{start}%+{_TAIL_SPAN_S}",
            "-show_entries",
            "frame=pts",
            str(path),
        ]
    )
    try:
        frames = json.loads(out).get("frames") or []
    except ValueError:
        return True
    delivered = {_int(item.get("pts")) for item in frames if isinstance(item, Mapping)}
    return status != 0 or bool(err.strip()) or last not in delivered


def _edit_list(boxes: MovieBoxes) -> tuple[EditEntry, ...]:
    """Convert the raw edit list to seconds (segment in movie ticks, media time in media ticks).

    Raises:
        BoxError: If an entry needs a time scale the file does not give.
    """
    if not boxes.edits:
        return ()
    if boxes.movie_timescale is None or boxes.video_timescale is None:
        raise BoxError("edit list without a time scale")
    return tuple(
        EditEntry(
            segment_duration_s=Fraction(edit.segment_duration, boxes.movie_timescale),
            media_time_s=None
            if edit.media_time == -1
            else Fraction(edit.media_time, boxes.video_timescale),
            media_rate=edit.media_rate,
        )
        for edit in boxes.edits
    )


def _movie(path: Path) -> tuple[tuple[EditEntry, ...], GoProInfo | None]:
    """Read the edit list and the GoPro settings; structural problems are logged, not raised."""
    try:
        boxes = read_movie_boxes(path)
        edits = _edit_list(boxes)
    except (BoxError, OSError) as error:
        _log.warning("movie boxes of %s not read: %s", path.name, error)
        return (), None
    if boxes.gpmf is None:
        return edits, None
    try:
        return edits, parse_settings(boxes.gpmf)
    except GPMFError as error:
        _log.warning("GPMF atom malformed: %s; colour profile unavailable for %s", error, path.name)
        return edits, None


def _colour_faults(color: _Color) -> list[Fault]:
    """Return the HLG/PQ refusal or the missing-tags warning for a stream's colour."""
    if color.hdr is not None:
        name = "HLG" if color.hdr == "hlg" else "PQ (HDR10)"
        return [
            Fault(
                color.hdr,
                "refuse",
                f"This video uses {name} HDR, which Clearwater does not support. "
                "Record in standard (SDR) mode instead.",
            )
        ]
    if color.defaulted:
        return [
            Fault(
                "missing_tags",
                "warn",
                "The video's colour tags are missing or unexpected ("
                + "; ".join(color.defaulted)
                + "). Clearwater assumes BT.709 colours and limited range for those.",
            )
        ]
    return []


def _gp_log_fault(gopro: GoProInfo | None, color: _Color) -> list[Fault]:
    """Return the GP-Log warning when the colour profile or a missing tag says log (AD-16)."""
    if gopro is None or color.hdr is not None:
        return []
    profile = (gopro.color_profile or "").upper()
    if profile and profile not in _GP_LOG_PROFILES:
        reason = f"colour profile {gopro.color_profile}"
    elif gopro.protune is True and color.transfer_missing:
        reason = "Protune is on and the video has no transfer tag"
    else:
        return []
    return [
        Fault(
            "gp_log",
            "warn",
            f"This looks like a GoPro Log clip ({reason}). Clearwater does not convert Log "
            "footage, so the result may look wrong.",
        )
    ]


def _tail_fault(
    path: Path,
    packets: Sequence[tuple[int | None, int | None, str]],
    nb_frames: int | None,
    stderr: str,
    time_base: Fraction,
) -> list[Fault]:
    """Return the truncation or unreadable-tail warning, never both (D86)."""
    corrupt_last = bool(packets) and "C" in packets[-1][2]
    readable = len(packets) - (1 if corrupt_last else 0)
    short = nb_frames is not None and len(packets) < nb_frames
    if "partial file" in stderr.lower() or corrupt_last or short:
        of_total = f" of {nb_frames}" if nb_frames is not None else ""
        return [
            Fault(
                "truncated",
                "warn",
                f"{path.name} is cut short: only {readable}{of_total} frames can be read. "
                "Clearwater will process up to the readable part.",
            )
        ]
    if packets and _tail_unreadable(path, packets, time_base):
        return [
            Fault(
                "unreadable_tail",
                "warn",
                f"The end of {path.name} cannot be decoded. Clearwater will process up to the "
                "last readable frame.",
            )
        ]
    return []


def _audio(stream: Mapping[str, Any]) -> AudioStreamInfo:
    """Build the audio stream record (start time from integer ticks)."""
    start = _ticks(stream.get("start_pts"), _fraction(stream.get("time_base")))
    return AudioStreamInfo(
        index=_int(stream.get("index")) or 0,
        codec=str(stream.get("codec_name", "")),
        sample_rate=_int(stream.get("sample_rate")) or 0,
        channels=_int(stream.get("channels")) or 0,
        start_s=start if start is not None else Fraction(0),
    )


def probe(path: Path) -> ProbeResult:
    """Probe one video file (IF-5).

    Args:
        path: The video file; opened read only, never written.

    Returns:
        The probe result. HLG or PQ files are returned with a ``refuse`` fault and are never to
        be decoded; truncation, missing colour tags and GP-Log are ``warn`` faults.

    Raises:
        VideoProbeError: ``"sidecar"`` for a ``.LRV`` or ``.THM`` (nothing is run),
            ``"missing_tool"`` when ffprobe is absent, ``"unreadable"`` when the file cannot be
            read at all (spec 5.4) and ``"unsupported"`` for a container, codec, pixel format
            or orientation outside the supported set.
    """
    if is_sidecar(path):
        raise VideoProbeError(
            "sidecar", f"{path.name} is a camera proxy or thumbnail file, not a video to correct."
        )
    if not path.is_file():
        raise VideoProbeError("unreadable", f"{path.name} was not found.")
    status, out, _ = _run_ffprobe(
        ["-v", "error", "-of", "json", "-show_entries", _STREAMS_ENTRIES, str(path)]
    )
    if status != 0:
        raise VideoProbeError("unreadable", _unreadable(path))
    data = _json(out, path)
    container = str((data.get("format") or {}).get("format_name", ""))
    streams = [s for s in data.get("streams") or [] if isinstance(s, Mapping)]
    video = next((s for s in streams if s.get("codec_type") == "video"), None)
    if video is None:
        raise VideoProbeError("unsupported", f"{path.name} has no video stream.")
    if not ({"mov", "mp4"} & set(container.split(","))):
        raise VideoProbeError(
            "unsupported",
            f"{path.name} is not an MP4 or MOV file (found {container or 'unknown'}).",
        )
    codec = str(video.get("codec_name", ""))
    if codec not in _ACCEPTED_CODECS:
        raise VideoProbeError(
            "unsupported", f"{path.name} uses the codec {codec or 'unknown'}; H.265 and H.264 only."
        )
    pix_fmt = str(video.get("pix_fmt", ""))
    bit_depth = _bit_depth(pix_fmt, path)
    rotation = _rotation(video, path)
    time_base = _fraction(video.get("time_base"))
    if time_base is None:
        raise VideoProbeError("unreadable", _unreadable(path))

    status, out, packet_err = _run_ffprobe(
        [
            "-v",
            "error",
            "-of",
            "json",
            "-select_streams",
            "v:0",
            "-show_entries",
            "packet=pts,duration,flags",
            str(path),
        ]
    )
    if status != 0 and not out.strip():
        raise VideoProbeError("unreadable", _unreadable(path))
    packets = _packets(out, path)
    pts = [p for p, _, _ in packets if p is not None]
    nb_frames = _int(video.get("nb_frames"))
    color = _resolve_color(video, pix_fmt, bit_depth)
    edits, gopro = _movie(path)

    timed = [s for s in streams if s.get("codec_type") in ("video", "audio")]
    durations = [
        d
        for s in timed
        if (d := _ticks(s.get("duration_ts"), _fraction(s.get("time_base")))) is not None
    ]
    starts = [
        d
        for s in timed
        if (d := _ticks(s.get("start_pts"), _fraction(s.get("time_base")))) is not None
    ]
    if durations:
        duration = max(durations)
    elif pts:
        duration = (max(pts) + (packets[-1][1] or 0)) * time_base
    else:
        duration = Fraction(0)

    faults = [
        *_colour_faults(color),
        *_gp_log_fault(gopro, color),
        *_tail_fault(path, packets, nb_frames, packet_err, time_base),
    ]
    chroma = _tag(video, "chroma_location")
    info = VideoStreamInfo(
        codec=codec,
        width=_int(video.get("width")) or 0,
        height=_int(video.get("height")) or 0,
        bit_depth=bit_depth,
        pix_fmt=pix_fmt,
        chroma_siting=chroma if chroma is not None else "unknown",
        color=color.description,
        frame_rate=_frame_rate(video, pts, time_base, path),
        time_base=time_base,
        nb_frames=nb_frames,
        rotation=rotation,
        vfr=_is_variable(pts),
    )
    return ProbeResult(
        path=path,
        container=container,
        duration_s=duration,
        start_offset_s=min(starts) if starts else Fraction(0),
        video=info,
        audio=tuple(_audio(s) for s in streams if s.get("codec_type") == "audio"),
        data=tuple(
            DataStreamInfo(
                index=_int(s.get("index")) or 0, codec_tag=str(s.get("codec_tag_string", ""))
            )
            for s in streams
            if s.get("codec_type") == "data"
        ),
        edit_list=edits,
        faults=tuple(faults),
        gopro=gopro,
    )
