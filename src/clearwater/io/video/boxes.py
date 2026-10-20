"""A small, bounds-checked reader of the ISO base media boxes the probe needs (WP3.7).

ffprobe's JSON carries no edit list and no GoPro settings atom, so this module reads them from
``moov`` itself: the movie and video-media time scales, the video track's edit list (``elst``,
versions 0 and 1) and the raw payload of ``moov/udta/GPMF``. Only ``moov`` is read: top-level
boxes are walked by their sizes and the media data box is skipped, never read.

Every box size is checked against the box that contains it and every walk advances by at least a
header, so a malformed or truncated file raises :class:`BoxError` rather than looping or reading
out of bounds.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

MAX_MOOV_BYTES = 512 * 1024 * 1024
"""The largest ``moov`` box that is read; a larger one is refused as malformed."""

_HEADER = 8
_LARGE_HEADER = 16


class BoxError(Exception):
    """A box is malformed, truncated or inconsistent with the box that contains it."""


@dataclass(frozen=True)
class RawEdit:
    """One ``elst`` entry as written, before conversion to seconds.

    Attributes:
        segment_duration: The entry's duration in movie time-scale ticks.
        media_time: The media time the entry starts at, in media time-scale ticks; -1 for an
            empty edit.
        media_rate: The playback rate of the entry (16.16 fixed point, as a Fraction).
    """

    segment_duration: int
    media_time: int
    media_rate: Fraction


@dataclass(frozen=True)
class MovieBoxes:
    """What the probe needs from ``moov``.

    Attributes:
        movie_timescale: Ticks per second of ``mvhd``, or None when there is no ``moov``.
        video_timescale: Ticks per second of the video track's ``mdhd``, or None.
        edits: The video track's ``elst`` entries (empty when it has none).
        gpmf: The payload of ``moov/udta/GPMF``, or None when there is no such atom.
    """

    movie_timescale: int | None
    video_timescale: int | None
    edits: tuple[RawEdit, ...]
    gpmf: bytes | None


_EMPTY = MovieBoxes(None, None, (), None)


def _children(data: bytes, start: int, end: int) -> list[tuple[str, int, int]]:
    """List the child boxes in ``data[start:end]`` as ``(type, payload_start, box_end)``.

    Args:
        data: The enclosing bytes.
        start: Where the first child begins.
        end: Where the enclosing box ends.

    Returns:
        The children in order.

    Raises:
        BoxError: If a child is smaller than its header or extends past ``end``.
    """
    found: list[tuple[str, int, int]] = []
    pos = start
    while pos < end:
        if end - pos < _HEADER:
            if not any(data[pos:end]):
                break  # QuickTime writes a 32-bit zero terminator after the last child
            raise BoxError("box header past the end of its parent")
        size, kind = struct.unpack_from(">I4s", data, pos)
        header = _HEADER
        if size == 1:
            if end - pos < _LARGE_HEADER:
                raise BoxError("64-bit box header past the end of its parent")
            (size,) = struct.unpack_from(">Q", data, pos + _HEADER)
            header = _LARGE_HEADER
        elif size == 0:
            size = end - pos
        if size < header or pos + size > end:
            raise BoxError("box size is inconsistent with its parent")
        found.append((kind.decode("latin-1"), pos + header, pos + size))
        pos += size
    return found


def _find(data: bytes, start: int, end: int, kind: str) -> tuple[int, int] | None:
    """Return the payload span of the first child of the given type, or None."""
    for found_kind, payload, box_end in _children(data, start, end):
        if found_kind == kind:
            return payload, box_end
    return None


def _timescale(data: bytes, span: tuple[int, int]) -> int:
    """Read the time scale from an ``mvhd`` or ``mdhd`` payload (versions 0 and 1)."""
    start, end = span
    if end - start < 4:
        raise BoxError("header box too short")
    version = data[start]
    offset = start + 4 + (16 if version == 1 else 8)
    if version not in (0, 1) or offset + 4 > end:
        raise BoxError("header box too short or of unknown version")
    (scale,) = struct.unpack_from(">I", data, offset)
    if scale == 0:
        raise BoxError("time scale is zero")
    return int(scale)


def _edits(data: bytes, span: tuple[int, int]) -> tuple[RawEdit, ...]:
    """Read an ``elst`` payload (versions 0 and 1)."""
    start, end = span
    if end - start < 8:
        raise BoxError("elst too short")
    version = data[start]
    if version not in (0, 1):
        raise BoxError("elst of unknown version")
    (count,) = struct.unpack_from(">I", data, start + 4)
    entry = 20 if version == 1 else 12
    if count * entry > end - start - 8:
        raise BoxError("elst entry count past the end of the box")
    form = ">QqhH" if version == 1 else ">IihH"
    edits = []
    for index in range(count):
        duration, media_time, rate_int, rate_frac = struct.unpack_from(
            form, data, start + 8 + index * entry
        )
        edits.append(RawEdit(duration, media_time, Fraction(rate_int * 65536 + rate_frac, 65536)))
    return tuple(edits)


def _handler(data: bytes, mdia: tuple[int, int]) -> str | None:
    """Return the ``hdlr`` handler type of a ``mdia`` payload, or None."""
    span = _find(data, mdia[0], mdia[1], "hdlr")
    if span is None or span[1] - span[0] < 12:
        return None
    return data[span[0] + 8 : span[0] + 12].decode("latin-1")


def parse_moov(moov: bytes) -> MovieBoxes:
    """Read the movie boxes the probe needs from the payload of a ``moov`` box.

    Args:
        moov: The bytes after the ``moov`` header.

    Returns:
        The time scales, the first video track's edit list and the ``GPMF`` payload.

    Raises:
        BoxError: If any box on the path is malformed.
    """
    mvhd = _find(moov, 0, len(moov), "mvhd")
    movie_scale = _timescale(moov, mvhd) if mvhd else None
    video_scale: int | None = None
    edits: tuple[RawEdit, ...] = ()
    gpmf: bytes | None = None
    video_seen = False
    for kind, payload, end in _children(moov, 0, len(moov)):
        if kind == "trak" and not video_seen:
            mdia = _find(moov, payload, end, "mdia")
            if mdia is None or _handler(moov, mdia) != "vide":
                continue
            video_seen = True
            mdhd = _find(moov, mdia[0], mdia[1], "mdhd")
            video_scale = _timescale(moov, mdhd) if mdhd else None
            edts = _find(moov, payload, end, "edts")
            elst = _find(moov, edts[0], edts[1], "elst") if edts else None
            edits = _edits(moov, elst) if elst else ()
        elif kind == "udta":
            atom = _find(moov, payload, end, "GPMF")
            if atom is not None and gpmf is None:
                gpmf = bytes(moov[atom[0] : atom[1]])
    return MovieBoxes(movie_scale, video_scale, edits, gpmf)


def read_movie_boxes(path: Path) -> MovieBoxes:
    """Read the movie boxes of an MP4 or MOV file without reading its media data.

    Args:
        path: The file (opened read only).

    Returns:
        The movie boxes; empty (all None) when the file has no ``moov`` box.

    Raises:
        BoxError: If a top-level box or a box inside ``moov`` is malformed.
        OSError: If the file cannot be read.
    """
    with path.open("rb") as handle:
        handle.seek(0, 2)
        total = handle.tell()
        pos = 0
        while pos < total:
            handle.seek(pos)
            head = handle.read(_LARGE_HEADER)
            if len(head) < _HEADER:
                raise BoxError("top-level box header is cut short")
            size, kind = struct.unpack_from(">I4s", head)
            header = _HEADER
            if size == 1:
                if len(head) < _LARGE_HEADER:
                    raise BoxError("64-bit top-level box header is cut short")
                (size,) = struct.unpack_from(">Q", head, _HEADER)
                header = _LARGE_HEADER
            elif size == 0:
                size = total - pos
            if size < header:
                raise BoxError("top-level box smaller than its header")
            if kind == b"moov":
                if pos + size > total:
                    raise BoxError("moov extends past the end of the file")
                if size - header > MAX_MOOV_BYTES:
                    raise BoxError("moov is larger than the supported maximum")
                handle.seek(pos + header)
                return parse_moov(handle.read(size - header))
            pos += size
    return _EMPTY
