"""Compare a source video container with its re-encode, item by item (spec D105, 7.5, 8.2).

Usage::

    uv run python tools/container_spike/compare.py SOURCE OUTPUT [--out DIR] [--config FILE]

Both files are read only. The facts come from two places: ``ffprobe`` (FFmpeg as a
separate process) for the streams, the decoded per-frame presentation timestamps and the
per-packet data hashes; and an ISO base media box walker for what ``ffprobe`` does not
show (the raw edit lists, the track header matrices, the ``mvhd`` creation time, the
sample entry boxes and the camera's ``moov/udta`` atoms). Every timing value is an exact
rational number of seconds (``Fraction``); no timestamp comparison is rounded or sampled.

Each item carries a class:

* ``MANDATORY`` (D94, D95, D105, section 7.5): the full sequence of per-frame
  presentation timestamps, frame count, video stream duration, start offset, the edit
  lists of the video and audio tracks judged by their presentation effect, audio
  present, passed through and in sync, and display orientation. A frame's presentation
  duration is the step to the next timestamp (the last frame ends at the stream
  duration); the per-frame ``duration`` that ``ffprobe`` prints is the packet's decode
  delta, which follows decode order and moves with the encoder's B-frame structure, so
  it is not compared.
* ``REQUIRED`` (D55, D114, section 8.2): colour tags and range, pixel format, chroma
  subsampling, bit depth and frame geometry. These are set by encoder options in every
  approach, so they do not separate the three approaches.
* ``BEST-EFFORT`` (D105, section 8.2): creation time, the GPMF and timecode tracks, the
  camera atoms, the edit lists as written, and other tags.

The record is written as ``<DIR>/<output stem>.compare.json`` and a markdown table
``<DIR>/<output stem>.compare.md``. ``DIR`` defaults to the configured working folder's
``wp1.5`` directory and must lie inside it and outside the footage folder.

Exit status 0 when the comparison ran (whatever it found); 2, with a one-line
``error: ...`` on standard error, when a file cannot be probed or the output folder is
refused.
"""

from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import os
import struct
import subprocess
import sys
from collections import Counter
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import Any

if not __package__:
    # Script mode (``python tools/container_spike/compare.py``): sys.path[0] is
    # tools/container_spike, so put the tools directory first to make ``local_config``
    # importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_config import LocalConfigError, load_local_config

MANDATORY = "MANDATORY"
REQUIRED = "REQUIRED"
BEST_EFFORT = "BEST-EFFORT"
SAME = "SAME"
DIFFERENT = "DIFFERENT"
SPIKE_SUBDIR = "wp1.5"
FFPROBE_TIMEOUT_SECONDS = 3600.0
_MOOV_MAX_BYTES = 256 * 1024 * 1024
_CELL_MAX_CHARS = 90
# Box types whose payload is only child boxes (descended by the walker).
_CONTAINER_BOXES = frozenset({"moov", "trak", "mdia", "minf", "stbl", "edts", "dinf"})
# A VisualSampleEntry's fixed fields before its child boxes (ISO/IEC 14496-12 12.1.3).
_VISUAL_SAMPLE_ENTRY_FIXED = 78


class ProbeError(Exception):
    """``ffprobe`` failed on a file, or the file's boxes could not be read."""


class OutputPathError(Exception):
    """An output path lies outside the spike folder or inside the footage folder."""


@dataclass(frozen=True)
class Edit:
    """One edit list entry as written.

    Attributes:
        segment_duration: Duration of the edit in the movie timescale.
        media_time: Start of the edit in the media timescale; -1 marks an empty edit.
        rate: Media rate (1 for normal play).
    """

    segment_duration: int
    media_time: int
    rate: Fraction


@dataclass(frozen=True)
class Track:
    """What the box walker reads from one ``trak`` box.

    Attributes:
        track_id: The ``tkhd`` track ID (``ffprobe`` reports it as the stream ``id``).
        flags: The ``tkhd`` flags (enabled, in movie, in preview).
        handler: The ``hdlr`` handler type, for example ``vide``, ``soun``, ``tmcd``.
        handler_name: The ``hdlr`` name string.
        sample_entry: The first ``stsd`` sample entry's format, for example ``hvc1``.
        sample_entry_boxes: The child box types of a visual sample entry (empty for
            other handlers).
        media_timescale: The ``mdhd`` timescale.
        media_duration: The ``mdhd`` duration, in the media timescale.
        matrix: The nine ``tkhd`` matrix values as stored (16.16 and 2.30 fixed point).
        edits: The ``elst`` entries, or None when the track has no edit list.
        earliest_composition: The smallest sample composition time (decode time plus
            ``ctts`` offset), in the media timescale; None for a track with no samples.
    """

    track_id: int
    flags: int
    handler: str
    handler_name: str
    sample_entry: str
    sample_entry_boxes: tuple[str, ...]
    media_timescale: int
    media_duration: int
    matrix: tuple[int, ...]
    edits: tuple[Edit, ...] | None
    earliest_composition: int | None


@dataclass(frozen=True)
class Movie:
    """What the box walker reads from the top level and the ``moov`` box.

    Attributes:
        top_level: The top-level box types in file order.
        major_brand: The ``ftyp`` major brand.
        compatible_brands: The ``ftyp`` compatible brands.
        timescale: The ``mvhd`` timescale.
        creation_time: The ``mvhd`` creation time, seconds since 1904-01-01 UTC.
        tracks: The tracks in ``trak`` order.
        udta: The ``moov/udta`` child atoms as (type, payload bytes, payload MD5).
    """

    top_level: tuple[str, ...]
    major_brand: str
    compatible_brands: tuple[str, ...]
    timescale: int
    creation_time: int
    tracks: tuple[Track, ...]
    udta: tuple[tuple[str, int, str], ...]


@dataclass(frozen=True)
class Packet:
    """One demuxed packet of a non-video stream, in presentation terms.

    Attributes:
        pts: Presentation time in seconds, or None when ``ffprobe`` has none.
        duration: Duration in seconds, or None.
        size: Payload size in bytes.
        md5: MD5 of the payload, as ``ffprobe -show_data_hash MD5`` prints it.
    """

    pts: Fraction | None
    duration: Fraction | None
    size: int
    md5: str


@dataclass(frozen=True)
class Facts:
    """Everything the comparison reads from one file.

    Attributes:
        path: The file.
        probe: The ``ffprobe -show_format -show_streams`` document.
        movie: The box walker's reading.
        video_index: The ``ffprobe`` index of the first non-cover-art video stream, or
            None.
        pts: Every decoded video frame's presentation timestamp in seconds, in
            presentation order, the whole sequence.
        packets: Per non-video stream index, its whole packet sequence.
        keys: Per ``ffprobe`` stream index, a key that pairs streams across files: the
            handler type and its occurrence (``vide#0``, ``soun#0``, ``meta#0``).
    """

    path: Path
    probe: dict[str, Any]
    movie: Movie
    video_index: int | None
    pts: list[Fraction | None]
    packets: dict[int, list[Packet]]
    keys: dict[int, str]


@dataclass(frozen=True)
class Item:
    """One compared item.

    Attributes:
        name: What is compared.
        item_class: ``MANDATORY``, ``REQUIRED`` or ``BEST-EFFORT``.
        clause: The spec clause the class comes from.
        source: The source value (JSON-ready; a summary for long sequences).
        output: The output value, in the same form.
        status: ``SAME`` or ``DIFFERENT``, decided on the full values.
        note: Where a sequence first differs, or why the item is read as it is.
    """

    name: str
    item_class: str
    clause: str
    source: Any
    output: Any
    status: str
    note: str = ""


# --- box walker ---------------------------------------------------------------------


def _children(buf: bytes, start: int, end: int) -> list[tuple[str, int, int]]:
    """List the boxes in ``buf[start:end]`` as (type, payload start, box end).

    Raises:
        ProbeError: If a box size runs past ``end`` or is smaller than its header.
    """
    found = []
    while start + 8 <= end:
        size, kind = struct.unpack_from(">I4s", buf, start)
        header = 8
        if size == 1:
            if start + 16 > end:
                raise ProbeError("box header out of range")
            (size,) = struct.unpack_from(">Q", buf, start + 8)
            header = 16
        elif size == 0:
            size = end - start
        if size < header or start + size > end:
            raise ProbeError("box size out of range")
        found.append((kind.decode("latin-1"), start + header, start + size))
        start += size
    return found


def _child(buf: bytes, start: int, end: int, kind: str) -> tuple[int, int] | None:
    """Return (payload start, end) of the first child box of ``kind``, or None."""
    for name, payload, box_end in _children(buf, start, end):
        if name == kind:
            return payload, box_end
    return None


def _path(buf: bytes, start: int, end: int, kinds: Sequence[str]) -> tuple[int, int] | None:
    """Follow a chain of child box types from ``buf[start:end]``; None if a link is absent."""
    span: tuple[int, int] | None = (start, end)
    for kind in kinds:
        if span is None:
            return None
        span = _child(buf, span[0], span[1], kind)
    return span


def _edits(buf: bytes, start: int) -> tuple[Edit, ...]:
    """Parse an ``elst`` payload (versions 0 and 1)."""
    version = buf[start]
    (count,) = struct.unpack_from(">I", buf, start + 4)
    position = start + 8
    edits = []
    for _ in range(count):
        if version == 1:
            duration, media_time = struct.unpack_from(">Qq", buf, position)
            position += 16
        else:
            duration, media_time = struct.unpack_from(">Ii", buf, position)
            position += 8
        whole, part = struct.unpack_from(">hH", buf, position)
        position += 4
        edits.append(Edit(duration, media_time, Fraction(whole) + Fraction(part, 65536)))
    return tuple(edits)


def _runs(buf: bytes, span: tuple[int, int] | None, signed: bool) -> list[tuple[int, int]]:
    """Parse an ``stts`` or ``ctts`` payload into (sample count, value) runs.

    ``ctts`` offsets are read as signed in both versions, as FFmpeg's demuxer reads them.
    """
    if span is None:
        return []
    start = span[0]
    (count,) = struct.unpack_from(">I", buf, start + 4)
    layout = ">Ii" if signed else ">II"
    return [struct.unpack_from(layout, buf, start + 8 + 8 * i) for i in range(count)]


def _earliest_composition(stts: list[tuple[int, int]], ctts: list[tuple[int, int]]) -> int | None:
    """Return the smallest decode time plus composition offset over all samples."""
    offsets = [offset for count, offset in ctts for _ in range(count)]
    earliest: int | None = None
    decode_time = 0
    sample = 0
    for count, delta in stts:
        for _ in range(count):
            composition = decode_time + (offsets[sample] if sample < len(offsets) else 0)
            earliest = composition if earliest is None else min(earliest, composition)
            decode_time += delta
            sample += 1
    return earliest


def _handler(buf: bytes, span: tuple[int, int] | None) -> tuple[str, str]:
    """Return (handler type, name) from an ``hdlr`` payload; ("", "") when absent."""
    if span is None:
        return "", ""
    start, end = span
    handler = buf[start + 8 : start + 12].decode("latin-1")
    raw = buf[start + 24 : end]
    if raw and raw[0] == len(raw) - 1:  # QuickTime writes a Pascal string
        raw = raw[1:]
    return handler, raw.split(b"\0", 1)[0].decode("utf-8", errors="replace")


def _track(buf: bytes, start: int, end: int) -> Track:
    """Read one ``trak`` payload."""
    tkhd = _child(buf, start, end, "tkhd")
    if tkhd is None:
        raise ProbeError("trak without tkhd")
    version = buf[tkhd[0]]
    flags = int.from_bytes(buf[tkhd[0] + 1 : tkhd[0] + 4], "big")
    if version == 1:
        (track_id,) = struct.unpack_from(">I", buf, tkhd[0] + 20)
        matrix_at = tkhd[0] + 52
    else:
        (track_id,) = struct.unpack_from(">I", buf, tkhd[0] + 12)
        matrix_at = tkhd[0] + 40
    matrix = struct.unpack_from(">9i", buf, matrix_at)

    mdia = _child(buf, start, end, "mdia")
    if mdia is None:
        raise ProbeError("trak without mdia")
    mdhd = _child(buf, mdia[0], mdia[1], "mdhd")
    if mdhd is None:
        raise ProbeError("mdia without mdhd")
    if buf[mdhd[0]] == 1:
        timescale, duration = struct.unpack_from(">IQ", buf, mdhd[0] + 20)
    else:
        timescale, duration = struct.unpack_from(">II", buf, mdhd[0] + 12)
    handler, handler_name = _handler(buf, _child(buf, mdia[0], mdia[1], "hdlr"))

    stbl = _path(buf, mdia[0], mdia[1], ("minf", "stbl"))
    sample_entry = ""
    entry_boxes: tuple[str, ...] = ()
    earliest: int | None = None
    if stbl is not None:
        stsd = _child(buf, stbl[0], stbl[1], "stsd")
        if stsd is not None and stsd[0] + 16 <= stsd[1]:
            entry_size, entry_kind = struct.unpack_from(">I4s", buf, stsd[0] + 8)
            sample_entry = entry_kind.decode("latin-1")
            entry_start = stsd[0] + 8
            if handler == "vide":
                try:
                    entry_boxes = tuple(
                        kind
                        for kind, _, _ in _children(
                            buf,
                            entry_start + 8 + _VISUAL_SAMPLE_ENTRY_FIXED,
                            min(entry_start + entry_size, stsd[1]),
                        )
                    )
                except ProbeError:
                    entry_boxes = ("(unreadable)",)
        stts = _runs(buf, _child(buf, stbl[0], stbl[1], "stts"), signed=False)
        ctts = _runs(buf, _child(buf, stbl[0], stbl[1], "ctts"), signed=True)
        earliest = _earliest_composition(stts, ctts)

    elst = _path(buf, start, end, ("edts", "elst"))
    return Track(
        track_id=track_id,
        flags=flags,
        handler=handler,
        handler_name=handler_name,
        sample_entry=sample_entry,
        sample_entry_boxes=entry_boxes,
        media_timescale=timescale,
        media_duration=duration,
        matrix=tuple(matrix),
        edits=None if elst is None else _edits(buf, elst[0]),
        earliest_composition=earliest,
    )


def _top_level(path: Path) -> tuple[list[str], bytes, bytes]:
    """Return the top-level box types, the ``ftyp`` payload and the whole ``moov`` box.

    Only ``ftyp`` and ``moov`` are read into memory; other boxes (``mdat``) are skipped
    by seeking. The file is opened read only.

    Raises:
        ProbeError: If the file cannot be read, a box is malformed, or there is no
            ``moov`` box.
    """
    top: list[str] = []
    ftyp = b""
    moov = b""
    try:
        with path.open("rb") as handle:
            total = os.fstat(handle.fileno()).st_size
            position = 0
            while position + 8 <= total:
                handle.seek(position)
                header = handle.read(16)
                size, kind_bytes = struct.unpack_from(">I4s", header)
                header_size = 8
                if size == 1:
                    (size,) = struct.unpack_from(">Q", header, 8)
                    header_size = 16
                elif size == 0:
                    size = total - position
                if size < header_size or position + size > total:
                    raise ProbeError(f"top-level box size out of range at byte {position}")
                kind = kind_bytes.decode("latin-1")
                top.append(kind)
                if kind in ("ftyp", "moov"):
                    if size > _MOOV_MAX_BYTES:
                        raise ProbeError(f"{kind} box larger than {_MOOV_MAX_BYTES} bytes")
                    handle.seek(position)
                    payload = handle.read(size)
                    if kind == "ftyp":
                        ftyp = payload[header_size:]
                    else:
                        moov = payload
                position += size
    except OSError as exc:
        raise ProbeError(f"cannot read {path}: {exc.strerror or exc}") from None
    if not moov:
        raise ProbeError(f"no moov box in {path}")
    return top, ftyp, moov


def _moov_header_size(moov: bytes) -> int:
    """Return the header size of a whole ``moov`` box (16 for a 64-bit size)."""
    return 16 if struct.unpack_from(">I", moov)[0] == 1 else 8


def udta_atom(path: Path, kind: str) -> bytes | None:
    """Return the payload of one ``moov/udta`` child atom (for example GoPro's ``GPMF``).

    Args:
        path: The MP4 file (read only).
        kind: The four-character atom type.

    Returns:
        The payload, or None when there is no such atom.

    Raises:
        ProbeError: If the file's boxes cannot be read.
    """
    _, _, moov = _top_level(path)
    span = _path(moov, _moov_header_size(moov), len(moov), ("udta", kind))
    return None if span is None else moov[span[0] : span[1]]


def read_movie(path: Path) -> Movie:
    """Read the top-level boxes and the ``moov`` box of an ISO base media file.

    Args:
        path: The MP4 or MOV file (read only; ``mdat`` is skipped, not read).

    Returns:
        The reading.

    Raises:
        ProbeError: If the file cannot be read, a box is malformed, or there is no
            ``moov`` box.
    """
    top, ftyp, moov = _top_level(path)
    moov_header = _moov_header_size(moov)
    mvhd = _child(moov, moov_header, len(moov), "mvhd")
    if mvhd is None:
        raise ProbeError("moov without mvhd")
    if moov[mvhd[0]] == 1:
        creation, _, timescale = struct.unpack_from(">QQI", moov, mvhd[0] + 4)
    else:
        creation, _, timescale = struct.unpack_from(">III", moov, mvhd[0] + 4)
    tracks = tuple(
        _track(moov, payload, end)
        for kind, payload, end in _children(moov, moov_header, len(moov))
        if kind == "trak"
    )
    udta_span = _child(moov, moov_header, len(moov), "udta")
    udta = (
        tuple(
            (kind, end - payload, hashlib.md5(moov[payload:end]).hexdigest())
            for kind, payload, end in _children(moov, udta_span[0], udta_span[1])
        )
        if udta_span is not None
        else ()
    )
    major = ftyp[:4].decode("latin-1")
    brands = tuple(ftyp[i : i + 4].decode("latin-1") for i in range(8, len(ftyp) - 3, 4))
    return Movie(
        top_level=tuple(top),
        major_brand=major,
        compatible_brands=brands,
        timescale=timescale,
        creation_time=creation,
        tracks=tracks,
        udta=udta,
    )


# --- ffprobe ------------------------------------------------------------------------


def run_ffprobe(arguments: Sequence[str]) -> dict[str, Any]:
    """Run ``ffprobe -v error -print_format json`` with ``arguments``, without a shell.

    Args:
        arguments: The remaining arguments, ending with the input file.

    Returns:
        The parsed JSON document.

    Raises:
        ProbeError: If ``ffprobe`` is absent, times out, fails or prints no JSON object.
    """
    command = ["ffprobe", "-v", "error", "-print_format", "json", *arguments]
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=FFPROBE_TIMEOUT_SECONDS,
            check=False,
        )
    except FileNotFoundError:
        raise ProbeError("ffprobe not found") from None
    except subprocess.TimeoutExpired:
        raise ProbeError(f"ffprobe timed out after {FFPROBE_TIMEOUT_SECONDS:g} s") from None
    except OSError as exc:
        raise ProbeError(f"ffprobe could not run: {exc}") from None
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", errors="replace").strip()
        raise ProbeError(f"ffprobe failed (status {result.returncode}): {detail[:300]}")
    try:
        data = json.loads(result.stdout.decode("utf-8", errors="replace"))
    except ValueError:
        raise ProbeError("ffprobe output is not valid JSON") from None
    if not isinstance(data, dict):
        raise ProbeError("ffprobe output is not a JSON object")
    return data


def _time_base(stream: Mapping[str, Any]) -> Fraction:
    """Return a stream's time base as an exact fraction."""
    text = str(stream.get("time_base", ""))
    numerator, _, denominator = text.partition("/")
    try:
        return Fraction(int(numerator), int(denominator))
    except (ValueError, ZeroDivisionError):
        raise ProbeError(f"stream has no usable time_base: {text!r}") from None


def _ticks(value: object, base: Fraction) -> Fraction | None:
    """Convert an integer tick count (or None) to exact seconds."""
    if isinstance(value, int) and not isinstance(value, bool):
        return value * base
    return None


def video_pts(path: Path, index: int, base: Fraction) -> list[Fraction | None]:
    """Decode one video stream and return every frame's presentation timestamp in seconds.

    The frames are in presentation order, with the container's edit list applied by
    the demuxer, as a player sees them.

    Args:
        path: The file.
        index: The ``ffprobe`` stream index.
        base: The stream's time base.

    Returns:
        One timestamp per decoded frame; None where ``ffprobe`` reports none.
    """
    data = run_ffprobe(["-select_streams", str(index), "-show_entries", "frame=pts", str(path)])
    return [
        _ticks(frame.get("pts"), base)
        for frame in data.get("frames", [])
        if isinstance(frame, dict)
    ]


def stream_packets(path: Path, index: int, base: Fraction) -> list[Packet]:
    """Return every packet of one stream, with an MD5 of each payload.

    Args:
        path: The file.
        index: The ``ffprobe`` stream index.
        base: The stream's time base.

    Returns:
        The packets in file order.
    """
    data = run_ffprobe(
        [
            "-select_streams",
            str(index),
            "-show_entries",
            "packet=pts,duration,size,data_hash",
            "-show_data_hash",
            "MD5",
            str(path),
        ]
    )
    packets = []
    for packet in data.get("packets", []):
        if not isinstance(packet, dict):
            continue
        size = packet.get("size")
        packets.append(
            Packet(
                pts=_ticks(packet.get("pts"), base),
                duration=_ticks(packet.get("duration"), base),
                size=int(size) if isinstance(size, (int, str)) and str(size).isdigit() else -1,
                md5=str(packet.get("data_hash", "")),
            )
        )
    return packets


def _stream_keys(streams: Sequence[Mapping[str, Any]], movie: Movie) -> dict[int, str]:
    """Pair each ``ffprobe`` stream with its track and name it by handler and occurrence."""
    by_id = {track.track_id: track for track in movie.tracks}
    seen: Counter[str] = Counter()
    keys = {}
    for stream in streams:
        index = int(stream.get("index", -1))
        try:
            track = by_id.get(int(str(stream.get("id", "")), 16))
        except ValueError:
            track = None
        kind = track.handler if track is not None else str(stream.get("codec_type", "unknown"))
        keys[index] = f"{kind}#{seen[kind]}"
        seen[kind] += 1
    return keys


def gather(path: Path) -> Facts:
    """Read every fact the comparison needs from one file (read only).

    Args:
        path: The file.

    Returns:
        The facts.

    Raises:
        ProbeError: If ``ffprobe`` or the box walker fails.
    """
    probe = run_ffprobe(["-show_format", "-show_streams", str(path)])
    movie = read_movie(path)
    streams = [s for s in probe.get("streams", []) if isinstance(s, dict)]
    video = next(
        (
            s
            for s in streams
            if s.get("codec_type") == "video"
            and not dict(s.get("disposition") or {}).get("attached_pic")
        ),
        None,
    )
    video_index = int(video["index"]) if video is not None else None
    pts = [] if video is None else video_pts(path, int(video["index"]), _time_base(video))
    packets = {
        int(s["index"]): stream_packets(path, int(s["index"]), _time_base(s))
        for s in streams
        if s.get("codec_type") in ("audio", "data")
    }
    return Facts(
        path=path,
        probe=probe,
        movie=movie,
        video_index=video_index,
        pts=pts,
        packets=packets,
        keys=_stream_keys(streams, movie),
    )


# --- values -------------------------------------------------------------------------


def exact(value: Fraction | None) -> str | None:
    """Render exact seconds as ``"<6 decimals> (<numerator>/<denominator>)"``.

    Two renderings are equal exactly when the two fractions are equal.

    Args:
        value: Seconds, or None.

    Returns:
        The text, or None for None.
    """
    if value is None:
        return None
    return f"{float(value):.6f} ({value.numerator}/{value.denominator})"


def _sha256(values: Sequence[object]) -> str:
    """Hash a sequence of JSON-ready values (the canonical JSON text)."""
    return hashlib.sha256(json.dumps(values, separators=(",", ":")).encode()).hexdigest()


def _first_difference(source: Sequence[object], output: Sequence[object]) -> str:
    """Describe where two sequences first differ."""
    for position, (left, right) in enumerate(zip(source, output, strict=False)):
        if left != right:
            return f"first difference at index {position}: {left} vs {right}"
    if len(source) != len(output):
        return f"lengths differ: {len(source)} vs {len(output)}"
    return ""


def _sequence_summary(values: Sequence[Any]) -> dict[str, Any]:
    """Summarise a JSON-ready sequence: count, first, last and SHA-256 of the whole."""
    return {
        "count": len(values),
        "first": values[0] if values else None,
        "last": values[-1] if values else None,
        "sha256": _sha256(list(values)),
    }


def _pts_summary(pts: Sequence[Fraction | None]) -> dict[str, Any]:
    """Summarise a pts sequence, with the count of each step between consecutive values.

    The steps show a variable frame rate's gaps (D95) as extra distinct values.
    """
    steps: Counter[str] = Counter()
    for previous, current in itertools.pairwise(pts):
        step = exact(current - previous) if previous is not None and current is not None else None
        steps[str(step)] += 1
    return {**_sequence_summary([exact(value) for value in pts]), "steps": dict(steps)}


def _sequence_item(
    name: str,
    item_class: str,
    clause: str,
    source: Sequence[Any],
    output: Sequence[Any],
    summarise: Callable[[Sequence[Any]], Any],
) -> Item:
    """Compare two whole sequences exactly and record their summaries."""
    status = SAME if list(source) == list(output) else DIFFERENT
    note = "" if status == SAME else _first_difference(source, output)
    return Item(name, item_class, clause, summarise(source), summarise(output), status, note)


def _item(
    name: str, item_class: str, clause: str, source: Any, output: Any, note: str = ""
) -> Item:
    """Compare two JSON-ready values."""
    status = SAME if source == output else DIFFERENT
    return Item(name, item_class, clause, source, output, status, note)


def _stream(facts: Facts, index: int | None) -> dict[str, Any]:
    """Return the ``ffprobe`` stream with ``index`` (an empty dict when None or absent)."""
    for stream in facts.probe.get("streams", []):
        if isinstance(stream, dict) and stream.get("index") == index:
            return stream
    return {}


def _streams_of(facts: Facts, codec_type: str, tag: str | None = None) -> list[dict[str, Any]]:
    """Return the ``ffprobe`` streams of one type, optionally with one codec tag."""
    return [
        s
        for s in facts.probe.get("streams", [])
        if isinstance(s, dict)
        and s.get("codec_type") == codec_type
        and (tag is None or s.get("codec_tag_string") == tag)
    ]


def _track_of(facts: Facts, index: int | None) -> Track | None:
    """Return the box walker's track for an ``ffprobe`` stream index."""
    stream = _stream(facts, index)
    try:
        track_id = int(str(stream.get("id", "")), 16)
    except ValueError:
        return None
    return next((t for t in facts.movie.tracks if t.track_id == track_id), None)


def _edits_as_written(movie: Movie, track: Track) -> list[dict[str, Any]] | None:
    """Render a track's edit list as written, each time in exact seconds."""
    if track.edits is None:
        return None
    return [
        {
            "duration": exact(Fraction(edit.segment_duration, movie.timescale)),
            "media_time": "empty"
            if edit.media_time == -1
            else exact(Fraction(edit.media_time, track.media_timescale)),
            "rate": str(edit.rate),
        }
        for edit in track.edits
    ]


def edit_effect(movie: Movie, track: Track) -> list[dict[str, Any]]:
    """Render a track's edit list by its effect on the presentation.

    A track with no edit list is given its implicit edit: the whole media from its
    start, at rate 1. Each entry's media time is taken relative to the track's earliest
    composition time, so an edit that only absorbs the encoder's reordering delay (the
    shift a B-frame encoder needs) reads as starting at 0, while a real trim of the
    media's head keeps its length. Empty edits keep their duration (a start offset).

    Args:
        movie: The movie, for its timescale.
        track: The track.

    Returns:
        One dict per entry with exact-seconds ``duration`` and ``media_start`` (or
        ``"empty"``) and the ``rate``.
    """
    earliest = track.earliest_composition or 0
    if track.edits is None:
        return [
            {
                "duration": exact(Fraction(track.media_duration, track.media_timescale)),
                "media_start": exact(Fraction(0)),
                "rate": "1",
            }
        ]
    return [
        {
            "duration": exact(Fraction(edit.segment_duration, movie.timescale)),
            "media_start": "empty"
            if edit.media_time == -1
            else exact(Fraction(edit.media_time - earliest, track.media_timescale)),
            "rate": str(edit.rate),
        }
        for edit in track.edits
    ]


def _rotation(stream: Mapping[str, Any]) -> dict[str, Any]:
    """Return the display matrix rotation and matrix text ``ffprobe`` reports, if any."""
    for entry in stream.get("side_data_list", []) or []:
        if isinstance(entry, dict) and "rotation" in entry:
            return {"rotation": entry.get("rotation"), "displaymatrix": entry.get("displaymatrix")}
    return {"rotation": None, "displaymatrix": None}


def pix_fmt_shape(pix_fmt: str | None) -> tuple[str | None, int | None]:
    """Return (chroma subsampling, bit depth) for the pixel formats GoPro and FFmpeg use.

    Args:
        pix_fmt: An FFmpeg pixel format name, for example ``yuvj420p`` or ``p010le``.

    Returns:
        Subsampling as ``"4:2:0"``, ``"4:2:2"`` or ``"4:4:4"`` and the bit depth; None
        for a part that is not recognised.
    """
    if not pix_fmt:
        return None, None
    name = pix_fmt.removesuffix("le").removesuffix("be")
    semiplanar = {"nv12": ("4:2:0", 8), "nv16": ("4:2:2", 8), "nv24": ("4:4:4", 8)}
    if name in semiplanar:
        return semiplanar[name]
    if name[:1] == "p" and name[1:4].isdigit():  # p010, p210, p410, p016 ...
        chroma = {"0": "4:2:0", "2": "4:2:2", "4": "4:4:4"}.get(name[1])
        return chroma, int(name[2:4])
    for prefix in ("yuvj", "yuv"):
        if name.startswith(prefix) and name[len(prefix) : len(prefix) + 3].isdigit():
            digits = name[len(prefix) : len(prefix) + 3]
            chroma = f"{digits[0]}:{digits[1]}:{digits[2]}"
            depth_text = name[len(prefix) + 4 :]
            return chroma, int(depth_text) if depth_text.isdigit() else 8
    return None, None


def _packet_rows(packets: Sequence[Packet]) -> list[list[Any]]:
    """Render packets as [pts, duration, size, md5] rows with exact seconds."""
    return [[exact(p.pts), exact(p.duration), p.size, p.md5] for p in packets]


def _packets_summary(rows: Sequence[list[Any]]) -> dict[str, Any]:
    """Summarise packet rows: count, first and last rows, SHA-256 of the whole list."""
    return {
        "count": len(rows),
        "first": rows[0] if rows else None,
        "last": rows[-1] if rows else None,
        "sha256": _sha256(list(rows)),
    }


def _tags(mapping: Mapping[str, Any] | None, drop: Sequence[str] = ()) -> dict[str, Any]:
    """Return a tag dict without the named keys."""
    return {k: v for k, v in dict(mapping or {}).items() if k not in drop}


def _first_video_pts(facts: Facts) -> Fraction | None:
    """Return the first decoded frame's pts (the presentation start of the video)."""
    return facts.pts[0] if facts.pts else None


def _keyed_packets(facts: Facts, codec_type: str, tag: str | None = None) -> dict[str, Any]:
    """Return {stream key: packet rows} for the streams of one type (and codec tag)."""
    return {
        facts.keys[int(s["index"])]: _packet_rows(facts.packets.get(int(s["index"]), []))
        for s in _streams_of(facts, codec_type, tag)
    }


def _keyed_edits(
    facts: Facts, render: Callable[[Movie, Track], Any], handlers: Sequence[str]
) -> dict[str, Any]:
    """Return {stream key: rendered edit list} for the tracks with the given handlers."""
    result = {}
    for index, key in facts.keys.items():
        track = _track_of(facts, index)
        if track is not None and track.handler in handlers:
            result[key] = render(facts.movie, track)
    return result


def _keyed_packet_items(
    source: Facts,
    output: Facts,
    name: str,
    item_class: str,
    clause: str,
    rows: Callable[[Facts], dict[str, Any]],
) -> list[Item]:
    """Compare per-stream packet sequences, one item per stream key in either file."""
    left, right = rows(source), rows(output)
    items = []
    for key in sorted(set(left) | set(right)):
        items.append(
            _sequence_item(
                f"{name} [{key}]",
                item_class,
                clause,
                left.get(key, []),
                right.get(key, []),
                _packets_summary,
            )
        )
    if not items:
        items.append(_item(name, item_class, clause, "absent", "absent"))
    return items


def compare_facts(source: Facts, output: Facts) -> list[Item]:
    """Compare two files' facts item by item.

    Args:
        source: The source file's facts.
        output: The output file's facts.

    Returns:
        The items, mandatory first.
    """
    items: list[Item] = []
    src_video, out_video = _stream(source, source.video_index), _stream(output, output.video_index)
    timing = "D94, D95, D105, 7.5"

    # MANDATORY: per-frame timing and duration.
    items.append(_item("video frame count", MANDATORY, timing, len(source.pts), len(output.pts)))
    items.append(
        _sequence_item(
            "video per-frame pts (presentation, exact, full sequence)",
            MANDATORY,
            timing,
            source.pts,
            output.pts,
            _pts_summary,
        )
    )
    items.append(
        _item(
            "video stream duration",
            MANDATORY,
            timing,
            exact(_ticks(src_video.get("duration_ts"), _time_base(src_video)))
            if src_video
            else None,
            exact(_ticks(out_video.get("duration_ts"), _time_base(out_video)))
            if out_video
            else None,
        )
    )

    # MANDATORY: start offset.
    items.append(
        _item(
            "start offset: first video frame pts",
            MANDATORY,
            "D94, D105, 7.5",
            exact(_first_video_pts(source)),
            exact(_first_video_pts(output)),
        )
    )

    def stream_starts(facts: Facts) -> dict[str, str | None]:
        return {
            facts.keys[int(s["index"])]: exact(_ticks(s.get("start_pts"), _time_base(s)))
            for s in _streams_of(facts, "video") + _streams_of(facts, "audio")
        }

    items.append(
        _item(
            "start offset: video and audio stream start_pts",
            MANDATORY,
            "D94, D105, 7.5",
            stream_starts(source),
            stream_starts(output),
        )
    )

    def container_start(facts: Facts) -> str | None:
        # The exact form of ffprobe's container start_time: the earliest stream start.
        starts = [
            start
            for s in facts.probe.get("streams", [])
            if isinstance(s, dict)
            and (start := _ticks(s.get("start_pts"), _time_base(s))) is not None
        ]
        return exact(min(starts)) if starts else None

    items.append(
        _item(
            "start offset: container start (earliest stream start, exact)",
            MANDATORY,
            "D94, D105, 7.5",
            container_start(source),
            container_start(output),
        )
    )

    # MANDATORY: edit lists of the video and audio tracks, by presentation effect.
    items.append(
        _item(
            "edit list, video and audio tracks (presentation effect)",
            MANDATORY,
            "D94, 7.5",
            _keyed_edits(source, edit_effect, ("vide", "soun")),
            _keyed_edits(output, edit_effect, ("vide", "soun")),
            note="media start is relative to the track's earliest composition time",
        )
    )

    # MANDATORY: audio present, passed through, in sync.
    def audio_layout(facts: Facts) -> dict[str, Any]:
        return {
            facts.keys[int(s["index"])]: {
                k: s.get(k)
                for k in ("codec_name", "profile", "sample_rate", "channels", "channel_layout")
            }
            for s in _streams_of(facts, "audio")
        }

    items.append(
        _item(
            "audio streams present",
            MANDATORY,
            "D105, 7.5",
            audio_layout(source),
            audio_layout(output),
        )
    )
    items.extend(
        _keyed_packet_items(
            source,
            output,
            "audio packets passed through (pts, duration, size, MD5)",
            MANDATORY,
            "7.5",
            lambda facts: _keyed_packets(facts, "audio"),
        )
    )

    def audio_sync(facts: Facts) -> dict[str, Any]:
        video_start = _first_video_pts(facts)
        result: dict[str, Any] = {}
        for s in _streams_of(facts, "audio"):
            starts = [p.pts for p in facts.packets.get(int(s["index"]), []) if p.pts is not None]
            first = min(starts) if starts else None
            result[facts.keys[int(s["index"])]] = (
                exact(first - video_start)
                if first is not None and video_start is not None
                else None
            )
        return result

    items.append(
        _item(
            "audio sync: first audio pts minus first video pts",
            MANDATORY,
            "D105, 7.5",
            audio_sync(source),
            audio_sync(output),
        )
    )

    # MANDATORY: display orientation.
    items.append(
        _item(
            "display orientation: display matrix (ffprobe side data)",
            MANDATORY,
            "D105, 8.2",
            _rotation(src_video),
            _rotation(out_video),
        )
    )
    src_track, out_track = (
        _track_of(source, source.video_index),
        _track_of(output, output.video_index),
    )
    items.append(
        _item(
            "display orientation: video tkhd matrix",
            MANDATORY,
            "D105, 8.2",
            list(src_track.matrix) if src_track else None,
            list(out_track.matrix) if out_track else None,
        )
    )

    # REQUIRED: colour tags, pixel format, geometry.
    for field, label, clause in (
        ("color_primaries", "colour primaries", "D55, 6.5"),
        ("color_transfer", "colour transfer", "D55, 6.5"),
        ("color_space", "colour matrix", "D55, 6.5"),
        ("color_range", "colour range", "D55, 6.5"),
        ("pix_fmt", "pixel format (decoded)", "D114, 6.5"),
    ):
        items.append(_item(label, REQUIRED, clause, src_video.get(field), out_video.get(field)))
    src_shape, out_shape = (
        pix_fmt_shape(src_video.get("pix_fmt")),
        pix_fmt_shape(out_video.get("pix_fmt")),
    )
    items.append(_item("chroma subsampling", REQUIRED, "D114, 8.2", src_shape[0], out_shape[0]))
    items.append(_item("bit depth", REQUIRED, "8.2, D76", src_shape[1], out_shape[1]))
    items.append(
        _item(
            "frame size and sample aspect ratio",
            REQUIRED,
            "8.2 (identity re-encode)",
            [src_video.get("width"), src_video.get("height"), src_video.get("sample_aspect_ratio")],
            [out_video.get("width"), out_video.get("height"), out_video.get("sample_aspect_ratio")],
        )
    )

    # BEST-EFFORT: creation time.
    best = "D105, 8.2"
    items.append(
        _item(
            "creation time: container tag",
            BEST_EFFORT,
            best,
            _tags(dict(source.probe.get("format") or {}).get("tags")).get("creation_time"),
            _tags(dict(output.probe.get("format") or {}).get("tags")).get("creation_time"),
        )
    )
    items.append(
        _item(
            "creation time: mvhd (seconds since 1904)",
            BEST_EFFORT,
            best,
            source.movie.creation_time,
            output.movie.creation_time,
        )
    )

    def stream_creation(facts: Facts) -> dict[str, Any]:
        return {
            facts.keys[int(s["index"])]: _tags(s.get("tags")).get("creation_time")
            for s in facts.probe.get("streams", [])
            if isinstance(s, dict)
        }

    items.append(
        _item(
            "creation time: per-stream tags",
            BEST_EFFORT,
            best,
            stream_creation(source),
            stream_creation(output),
        )
    )

    # BEST-EFFORT: GPMF and timecode tracks.
    items.extend(
        _keyed_packet_items(
            source,
            output,
            "GPMF track gpmd (pts, duration, size, MD5)",
            BEST_EFFORT,
            best,
            lambda facts: _keyed_packets(facts, "data", "gpmd"),
        )
    )
    items.extend(
        _keyed_packet_items(
            source,
            output,
            "timecode track tmcd (pts, duration, size, MD5)",
            BEST_EFFORT,
            best,
            lambda facts: _keyed_packets(facts, "data", "tmcd"),
        )
    )

    def timecode_tags(facts: Facts) -> dict[str, Any]:
        return {
            facts.keys[int(s["index"])]: _tags(s.get("tags")).get("timecode")
            for s in facts.probe.get("streams", [])
            if isinstance(s, dict) and _tags(s.get("tags")).get("timecode") is not None
        }

    items.append(
        _item(
            "timecode value (stream tags)",
            BEST_EFFORT,
            best,
            timecode_tags(source),
            timecode_tags(output),
        )
    )

    # BEST-EFFORT: camera atoms and other tags.
    items.append(
        _item(
            "camera atoms: moov/udta children (type, bytes, MD5)",
            BEST_EFFORT,
            best,
            [list(atom) for atom in source.movie.udta],
            [list(atom) for atom in output.movie.udta],
        )
    )
    items.append(
        _item(
            "ftyp brands",
            BEST_EFFORT,
            best,
            [source.movie.major_brand, list(source.movie.compatible_brands)],
            [output.movie.major_brand, list(output.movie.compatible_brands)],
        )
    )
    items.append(
        _item(
            "container tags other than creation_time",
            BEST_EFFORT,
            best,
            _tags(dict(source.probe.get("format") or {}).get("tags"), ("creation_time",)),
            _tags(dict(output.probe.get("format") or {}).get("tags"), ("creation_time",)),
        )
    )

    def stream_tags(facts: Facts) -> dict[str, Any]:
        return {
            facts.keys[int(s["index"])]: _tags(s.get("tags"), ("creation_time", "timecode"))
            for s in facts.probe.get("streams", [])
            if isinstance(s, dict)
        }

    items.append(
        _item(
            "stream tags other than creation_time and timecode",
            BEST_EFFORT,
            best,
            stream_tags(source),
            stream_tags(output),
        )
    )
    items.append(
        _item(
            "chroma location",
            BEST_EFFORT,
            best,
            src_video.get("chroma_location"),
            out_video.get("chroma_location"),
        )
    )

    def layout(facts: Facts) -> list[str]:
        return [
            f"{facts.keys[index]}:{track.sample_entry}:flags={track.flags:#x}"
            for index in sorted(facts.keys)
            if (track := _track_of(facts, index)) is not None
        ]

    items.append(
        _item(
            "track layout (key:sample entry:tkhd flags)",
            BEST_EFFORT,
            best,
            layout(source),
            layout(output),
        )
    )
    items.append(
        _item(
            "video sample entry child boxes",
            BEST_EFFORT,
            best,
            list(src_track.sample_entry_boxes) if src_track else None,
            list(out_track.sample_entry_boxes) if out_track else None,
        )
    )
    items.append(
        _item(
            "edit lists as written (all tracks; media_time in media seconds)",
            BEST_EFFORT,
            best,
            _keyed_edits(
                source, _edits_as_written, ("vide", "soun", "tmcd", "meta", "text", "subt")
            ),
            _keyed_edits(
                output, _edits_as_written, ("vide", "soun", "tmcd", "meta", "text", "subt")
            ),
            note="media_time is tied to the encoded stream's composition offsets",
        )
    )
    items.append(
        _item(
            "edit list, data tracks (presentation effect)",
            BEST_EFFORT,
            best,
            _keyed_edits(source, edit_effect, ("tmcd", "meta", "text", "subt")),
            _keyed_edits(output, edit_effect, ("tmcd", "meta", "text", "subt")),
        )
    )
    items.append(
        _item(
            "container duration (ffprobe, 1 us)",
            BEST_EFFORT,
            best,
            dict(source.probe.get("format") or {}).get("duration"),
            dict(output.probe.get("format") or {}).get("duration"),
            note="the longest track; follows the data tracks",
        )
    )
    return items


# --- record -------------------------------------------------------------------------


def _tool_version() -> str:
    """Return the first line of ``ffprobe -version`` (empty when it cannot run)."""
    try:
        result = subprocess.run(
            ["ffprobe", "-version"],
            capture_output=True,
            stdin=subprocess.DEVNULL,
            timeout=60,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout.decode("utf-8", errors="replace").partition("\n")[0].strip()


def build_record(source: Facts, output: Facts, items: Sequence[Item]) -> dict[str, Any]:
    """Assemble the JSON record of one comparison.

    Args:
        source: The source file's facts.
        output: The output file's facts.
        items: The compared items.

    Returns:
        The record: the two paths, the ``ffprobe`` version, informational codec fields,
        every item, and a summary listing the DIFFERENT items per class.
    """

    def info(facts: Facts) -> dict[str, Any]:
        video = _stream(facts, facts.video_index)
        return {
            "codec": video.get("codec_name"),
            "profile": video.get("profile"),
            "bit_rate": video.get("bit_rate"),
            "size_bytes": dict(facts.probe.get("format") or {}).get("size"),
            "streams": [
                f"{facts.keys[int(s['index'])]}:{s.get('codec_type')}:{s.get('codec_tag_string')}"
                for s in facts.probe.get("streams", [])
                if isinstance(s, dict)
            ],
        }

    different: dict[str, list[str]] = {MANDATORY: [], REQUIRED: [], BEST_EFFORT: []}
    for item in items:
        if item.status == DIFFERENT:
            different[item.item_class].append(item.name)
    return {
        "source": str(source.path),
        "output": str(output.path),
        "ffprobe": _tool_version(),
        "info": {"source": info(source), "output": info(output)},
        "items": [
            {
                "name": item.name,
                "class": item.item_class,
                "clause": item.clause,
                "source": item.source,
                "output": item.output,
                "status": item.status,
                "note": item.note,
            }
            for item in items
        ],
        "summary": {
            "items": len(items),
            "different": {key: len(names) for key, names in different.items()},
            "different_items": different,
            "mandatory_all_same": not different[MANDATORY],
        },
    }


def compare_files(source: Path, output: Path) -> dict[str, Any]:
    """Compare two files and return the JSON record (nothing is written).

    Args:
        source: The source file (read only).
        output: The re-encoded file (read only).

    Returns:
        The record (see :func:`build_record`).

    Raises:
        ProbeError: If either file cannot be probed.
    """
    source_facts, output_facts = gather(source), gather(output)
    return build_record(source_facts, output_facts, compare_facts(source_facts, output_facts))


def _cell(value: Any) -> str:
    """Render one value for a markdown table cell (sequences by count, ends and hash)."""
    if isinstance(value, dict) and "sha256" in value and "count" in value:
        text = f"n={value['count']}; first {value['first']}; last {value['last']}; "
        text += f"sha256 {str(value['sha256'])[:12]}"
        if "steps" in value:
            text += f"; steps {value['steps']}"
    elif isinstance(value, str):
        text = value
    else:
        text = json.dumps(value, separators=(",", ":"))
    text = text.replace("|", "/").replace("\n", " ")
    return text if len(text) <= _CELL_MAX_CHARS else text[: _CELL_MAX_CHARS - 3] + "..."


def markdown_table(record: Mapping[str, Any]) -> str:
    """Render a record as a markdown table (cells shortened; the JSON holds every value).

    Args:
        record: A record from :func:`build_record`.

    Returns:
        The markdown text.
    """
    lines = [
        f"Source: `{record['source']}`  ",
        f"Output: `{record['output']}`  ",
        f"Tool: {record['ffprobe']}",
        "",
        "| Item | Class | Clause | Source | Output | Result |",
        "|---|---|---|---|---|---|",
    ]
    for item in record["items"]:
        result = item["status"] + (f" ({_cell(item['note'])})" if item["note"] else "")
        lines.append(
            f"| {item['name']} | {item['class']} | {item['clause']} | {_cell(item['source'])} "
            f"| {_cell(item['output'])} | {result} |"
        )
    summary = record["summary"]
    lines += [
        "",
        f"Items: {summary['items']}. DIFFERENT by class: "
        + ", ".join(f"{key} {count}" for key, count in summary["different"].items())
        + f". Every MANDATORY item SAME: {summary['mandatory_all_same']}.",
    ]
    return "\n".join(lines) + "\n"


def _normalised(path: Path) -> Path:
    """Resolve links and normalise case for a containment check."""
    return Path(os.path.normcase(path.resolve()))


def check_output_path(path: Path, allowed_root: Path, footage_root: Path) -> Path:
    """Refuse an output path outside the spike folder or inside the footage folder.

    Both checks run on the resolved path (links followed), so a link that leads into the
    footage folder is refused.

    Args:
        path: The intended output file or folder.
        allowed_root: The spike folder (the working folder's ``wp1.5``).
        footage_root: The read-only footage folder.

    Returns:
        The resolved path.

    Raises:
        OutputPathError: If the path is not inside ``allowed_root`` (or equal to it) or
            is inside (or equal to) ``footage_root``.
    """
    resolved = _normalised(path)
    allowed = _normalised(allowed_root)
    footage = _normalised(footage_root)
    if resolved == footage or footage in resolved.parents:
        raise OutputPathError(f"output path {path} lies inside the footage folder")
    if resolved != allowed and allowed not in resolved.parents:
        raise OutputPathError(f"output path {path} lies outside the spike folder {allowed_root}")
    return path.resolve()


def write_checked(text: str, path: Path, allowed_root: Path, footage_root: Path) -> Path:
    """Write ``text`` to ``path`` after checking the file's own resolved path.

    The file path itself is checked, not only its folder, so a link planted at the file
    name cannot redirect the write.

    Args:
        text: The content (UTF-8).
        path: The file.
        allowed_root: The spike folder (see :func:`check_output_path`).
        footage_root: The footage folder.

    Returns:
        The path written.

    Raises:
        OutputPathError: If the resolved path is refused.
    """
    target = check_output_path(path, allowed_root, footage_root)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return path


def write_record(
    record: Mapping[str, Any], folder: Path, name: str, allowed_root: Path, footage_root: Path
) -> tuple[Path, Path]:
    """Write ``<folder>/<name>.compare.json`` and ``<folder>/<name>.compare.md``.

    Each file is checked with :func:`check_output_path` on its own resolved path before
    it is written.

    Args:
        record: The record.
        folder: The output folder (created if absent).
        name: The file name stem.
        allowed_root: The spike folder.
        footage_root: The footage folder.

    Returns:
        The JSON and markdown paths.

    Raises:
        OutputPathError: If either path is refused (nothing is written then).
    """
    json_path = folder / f"{name}.compare.json"
    md_path = folder / f"{name}.compare.md"
    for path in (json_path, md_path):
        check_output_path(path, allowed_root, footage_root)
    write_checked(json.dumps(record, indent=1) + "\n", json_path, allowed_root, footage_root)
    write_checked(markdown_table(record), md_path, allowed_root, footage_root)
    return json_path, md_path


def main(argv: list[str] | None = None) -> int:
    """Compare SOURCE with OUTPUT and write the record into the spike folder.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 when the comparison ran; 2 (with a one-line ``error: ...``) on a probe failure,
        an unreadable configuration or a refused output folder.
    """
    parser = argparse.ArgumentParser(description="Compare a source container with its re-encode.")
    parser.add_argument("source", type=Path, help="the source file (read only)")
    parser.add_argument("output", type=Path, help="the re-encoded file (read only)")
    parser.add_argument("--out", type=Path, help="record folder (default: <working>/wp1.5)")
    parser.add_argument("--config", type=Path, help="local configuration file to read")
    args = parser.parse_args(argv)
    try:
        config = load_local_config(args.config)
        spike_root = config.working_path / SPIKE_SUBDIR
        folder = check_output_path(args.out or spike_root, spike_root, config.footage_path)
        record = compare_files(args.source, args.output)
        json_path, md_path = write_record(
            record, folder, args.output.stem, spike_root, config.footage_path
        )
    except (LocalConfigError, OutputPathError, ProbeError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json_path)
    print(md_path)
    summary = record["summary"]
    print(
        f"DIFFERENT by class: {summary['different']}; "
        f"every MANDATORY item SAME: {summary['mandatory_all_same']}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
