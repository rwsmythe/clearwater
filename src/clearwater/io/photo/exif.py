r"""EXIF reading and the D63 edit (spec 8.1; WP3.6).

``PhotoMetadata.exif`` is the bare TIFF-structured block (it starts ``II*\0`` or ``MM\0*``; an
``Exif\0\0`` prefix is stripped on read). Pillow's ``Image.Exif`` supplies decoded read views;
the writer relocates raw TIFF entries so their types, counts and value bytes survive.
"""

from __future__ import annotations

import logging
import struct

from PIL import ExifTags, Image

_log = logging.getLogger(__name__)

PREFIX = b"Exif\x00\x00"
"""The prefix Pillow and pillow-heif put before the TIFF bytes; a PNG ``eXIf`` omits it."""

SOFTWARE = "Clearwater"
"""The EXIF Software value a written file carries (D63, spec 8.1)."""

ORIENTATION = int(ExifTags.Base.Orientation)
SOFTWARE_TAG = int(ExifTags.Base.Software)
PIXEL_X = int(ExifTags.Base.ExifImageWidth)  # PixelXDimension
PIXEL_Y = int(ExifTags.Base.ExifImageHeight)  # PixelYDimension
EXIF_IFD = ExifTags.IFD.Exif
GPS_IFD = ExifTags.IFD.GPSInfo
INTEROP_IFD = ExifTags.IFD.Interop
INTEROP_POINTER = int(ExifTags.IFD.Interop)  # 40965, a tag of the Exif IFD
IFD_POINTERS = frozenset({int(ExifTags.IFD.Exif), int(ExifTags.IFD.GPSInfo), INTEROP_POINTER, 330})
"""IFD0 tags that point to other IFDs (Exif, GPS, Interop, SubIFDs); never copied as values."""

# TIFF structure and embedded blobs that are not EXIF fields: dropped when an EXIF block is
# built from a TIFF source's IFD0 (WP3.6 round 0, section E).
_TIFF_STRUCTURE = frozenset(
    {254, 256, 257, 258, 259, 262, 266, 273, 277, 278, 279, 284, 317, 320, 322, 323, 324, 325}
    | {338, 339, 347, 529, 530, 531, 532}  # extra samples, sample format, JPEG, YCbCr
    | {700, 33723, 34377, 34675}  # XMP, IPTC, Photoshop, ICC profile
)

_TYPE_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}


class _Entry:
    """A raw TIFF entry, optionally pointing at a carried child directory."""

    def __init__(
        self,
        tag: int,
        kind: int,
        count: int,
        value: bytes,
        child: list[_Entry] | None = None,
    ) -> None:
        self.tag = tag
        self.kind = kind
        self.count = count
        self.value = value
        self.child = child


def _read_entries(
    data: bytes, drop: frozenset[int], *, warn: bool = True
) -> tuple[str, list[_Entry]]:
    """Read at most four label-specific IFDs, keeping whole entries from cut arrays."""
    if len(data) < 8 or data[:2] not in (b"II", b"MM"):
        raise ValueError("invalid TIFF header")
    order = "<" if data[:2] == b"II" else ">"
    magic, root = struct.unpack_from(order + "HI", data, 2)
    if magic == 43:
        raise ValueError("BigTIFF cannot be read for EXIF")
    if magic != 42:
        raise ValueError("invalid TIFF magic")

    def read(offset: int, label: str, ancestors: frozenset[int]) -> list[_Entry]:
        # Ancestor offsets are cycles; same-offset siblings are parsed per label.
        if offset < 8 or offset > len(data) - 2 or offset in ancestors:
            raise ValueError("invalid or cyclic IFD offset")
        declared = struct.unpack_from(order + "H", data, offset)[0]
        count = min(declared, (len(data) - offset - 2) // 12)
        if count < declared and warn:
            _log.warning(
                "TIFF %s entry array cut short: declared %s entries, kept %s whole entries",
                label,
                declared,
                count,
            )
        pointers = (
            {int(EXIF_IFD): "Exif", int(GPS_IFD): "GPS"}
            if label == "IFD0"
            else {INTEROP_POINTER: "Interop"}
            if label == "Exif"
            else {}
        )
        entries = []
        followed: set[int] = set()
        for index in range(count):
            at = offset + 2 + index * 12
            tag, kind, number = struct.unpack_from(order + "HHI", data, at)
            if tag in pointers:
                if tag in followed:
                    if warn:
                        _log.warning("TIFF %s duplicate IFD pointer entry %s dropped", label, tag)
                    continue
                followed.add(tag)
            if (
                (kind == 13 and tag not in pointers)
                or tag == 330
                or (tag in IFD_POINTERS and tag not in pointers)
            ):
                if warn:
                    _log.warning("%s IFD-valued entry %s (type %s) dropped", label, tag, kind)
                continue
            if label == "IFD0" and (tag in drop or tag in (513, 514)):
                continue

            def value_bytes(kind: int = kind, number: int = number, at: int = at) -> bytes:
                if kind not in _TYPE_SIZES:
                    raise ValueError(f"unsupported TIFF field type {kind}")
                length = number * _TYPE_SIZES[kind]
                start = at + 8
                if length > 4:
                    start = struct.unpack_from(order + "I", data, start)[0]
                    if start < 8:
                        raise ValueError("value offset points inside TIFF header")
                if start > len(data) or length > len(data) - start:
                    raise ValueError("IFD value runs past block")
                return data[start : start + length]

            try:
                value = value_bytes()
            except ValueError as error:
                if warn:
                    _log.warning("TIFF %s entry %s cannot be read (%s); dropped", label, tag, error)
                continue
            if tag in pointers:
                try:
                    if kind not in (3, 4, 13) or number != 1:
                        raise ValueError("IFD pointer is not a single unsigned offset")
                    child_offset = struct.unpack(order + ("H" if kind == 3 else "I"), value)[0]
                    child = read(child_offset, pointers[tag], ancestors | {offset})
                except ValueError as error:
                    if warn:
                        _log.warning(
                            "TIFF %s IFD cannot be read (%s); %s entry %s dropped",
                            pointers[tag],
                            error,
                            label,
                            tag,
                        )
                    continue
                if child:
                    entries.append(_Entry(tag, kind, number, value, child))
            else:
                entries.append(_Entry(tag, kind, number, value))
        return entries

    return order, read(root, "IFD0", frozenset())


def _put(entries: list[_Entry], replacement: _Entry, label: str, *, warn: bool = True) -> None:
    """Replace the first D63 entry, drop later copies, or insert an absent entry by tag."""
    for index, entry in enumerate(entries):
        if entry.tag == replacement.tag:
            entries[index] = replacement
            for later in range(len(entries) - 1, index, -1):
                if entries[later].tag == replacement.tag:
                    del entries[later]
                    if warn:
                        _log.warning(
                            "TIFF %s duplicate D63 entry %s dropped", label, replacement.tag
                        )
            return
    index = next(
        (index for index, entry in enumerate(entries) if entry.tag > replacement.tag), len(entries)
    )
    entries.insert(index, replacement)


def _apply_d63(
    entries: list[_Entry], order: str, width: int, height: int, *, warn: bool = True
) -> None:
    """Change the D63 fields, creating the single Exif child when absent."""
    _put(entries, _Entry(ORIENTATION, 3, 1, struct.pack(order + "H", 1)), "IFD0", warn=warn)
    _put(entries, _Entry(SOFTWARE_TAG, 2, 11, b"Clearwater\0"), "IFD0", warn=warn)
    pointer = next((entry for entry in entries if entry.tag == EXIF_IFD), None)
    if pointer is None:
        pointer = _Entry(int(EXIF_IFD), 4, 1, bytes(4), [])
        _put(entries, pointer, "IFD0", warn=warn)
    assert pointer.child is not None
    for tag, size in ((PIXEL_X, width), (PIXEL_Y, height)):
        previous = next((entry for entry in pointer.child if entry.tag == tag), None)
        kind = 3 if previous is not None and previous.kind == 3 and 0 <= size <= 65535 else 4
        _put(
            pointer.child,
            _Entry(tag, kind, 1, struct.pack(order + ("H" if kind == 3 else "I"), size)),
            "Exif",
            warn=warn,
        )


def _write_entries(order: str, entries: list[_Entry]) -> bytes:
    """Write the at-most-four directories, relocating raw values with word padding."""
    output = bytearray((b"II" if order == "<" else b"MM") + struct.pack(order + "HI", 42, 8))

    def write(fields: list[_Entry]) -> int:
        if len(fields) > 65535:
            raise ValueError("too many TIFF entries")
        offset = len(output)
        output.extend(bytes(6 + len(fields) * 12))
        struct.pack_into(order + "H", output, offset, len(fields))
        for index, entry in enumerate(fields):
            at = offset + 2 + index * 12
            kind = entry.kind
            value = entry.value
            if entry.child is not None:
                child_offset = write(entry.child)
                if kind == 3 and child_offset > 65535:
                    kind = 4
                value = struct.pack(order + ("H" if kind == 3 else "I"), child_offset)
            struct.pack_into(order + "HHI", output, at, entry.tag, kind, entry.count)
            if len(value) <= 4:
                output[at + 8 : at + 12] = value.ljust(4, b"\0")
            else:
                struct.pack_into(order + "I", output, at + 8, len(output))
                output.extend(value)
                if len(output) % 2:
                    output.append(0)
        # The reserved next-IFD pointer remains zero: IFD1 is deliberately not carried.
        return offset

    write(entries)
    return bytes(output)


def strip_prefix(block: bytes) -> bytes:
    r"""Remove a leading ``Exif\0\0`` from an EXIF block.

    Args:
        block: EXIF bytes with or without the prefix.

    Returns:
        The bare TIFF-structured block.
    """
    return block[len(PREFIX) :] if block.startswith(PREFIX) else block


def load(block: bytes) -> Image.Exif:
    """Parse an EXIF block (with or without the prefix) with Pillow's reader.

    Args:
        block: EXIF bytes.

    Returns:
        The parsed ``Image.Exif``.
    """
    exif = Image.Exif()
    exif.load(block if block.startswith(PREFIX) else PREFIX + block)
    return exif


def orientation_of(block: bytes | None) -> int:
    """Return the EXIF Orientation of a block, or 1 when absent, invalid or unreadable.

    Args:
        block: EXIF bytes, or None.

    Returns:
        1 to 8. A value outside 1 to 8, or a block that cannot be parsed, gives 1 with a warning.
    """
    if not block:
        return 1
    try:
        value = load(block).get(ORIENTATION)
    except Exception as error:  # Pillow raises assorted types on malformed blocks
        _log.warning("EXIF block cannot be parsed (%s); orientation taken as 1", error)
        return 1
    if value is None:
        return 1
    if isinstance(value, int) and 1 <= value <= 8:
        return value
    _log.warning("EXIF Orientation %r is not 1 to 8; taken as 1", value)
    return 1


def sanitise(block: bytes | None, name: str) -> bytes | None:
    """Return ``block`` if the D63 edit can process it, else None with a logged warning.

    A damaged block (a CRC-valid ``eXIf`` chunk or a JPEG APP1 segment holding bytes that are not
    a TIFF structure) is dropped at read, so :func:`edit` never meets it in the writer; the written
    file then carries the minimal block. The trial edit suppresses entry warnings; the writer
    emits them once when it performs the actual edit. A rejected block still warns here.

    Args:
        block: The bare EXIF block of the source, or None.
        name: The file name for the log message.

    Returns:
        The block unchanged when it is usable, otherwise None.
    """
    if not block:
        return None
    try:
        edit(block, 1, 1, _warn=False)
    except Exception as error:  # Reject any block the trial cannot rewrite.
        _log.warning("%s: the EXIF block is damaged (%s); it is not carried", name, error)
        return None
    return block


def edit(source: bytes | None, width: int, height: int, *, _warn: bool = True) -> bytes:
    r"""Return the D63-edited EXIF block a written image carries.

    Orientation is set to 1 (the rotation is in the pixels), the thumbnail (IFD1) is dropped
    (the next-IFD pointer is zero), PixelXDimension and PixelYDimension are set to the
    written size, Software is set to :data:`SOFTWARE`; every other field of IFD0, the Exif IFD,
    the Interop IFD and the GPS IFD is kept when readable. Individual damaged entries are
    dropped with IFD/tag warnings. A cut array keeps all whole entries with one warning naming
    the IFD and declared/kept counts; an absent next-IFD pointer is accepted. Invalid child
    offsets/cycles, empty children and unsupported IFD-valued entries are dropped. Header
    faults or an IFD0 offset past the block raise; cycles drop only the child. An output
    directory exceeding 65,535 entries also raises. Only the first occurrence of each carried
    pointer tag per parent is followed; later occurrences warn and are dropped. At most IFD0,
    Exif, GPS and Interop are parsed and written. Same-offset siblings are parsed per label;
    D63 dimensions affect only Exif. Written entry count is bounded by four times the source
    byte length divided by 12, plus at most five D63 insertions. Later duplicates of the four
    D63 fields are removed; other non-pointer duplicates are retained. A source without EXIF
    gets a minimal block with those four fields. A relocated SHORT pointer promotes to LONG
    if needed.

    Args:
        source: The source EXIF block, or None.
        width: Width of the written image.
        height: Height of the written image.
        _warn: Emit entry/damage warnings; False is reserved for sanitise's trial edit.

    Returns:
        The bare TIFF-structured block (no ``Exif\0\0`` prefix).

    Raises:
        ValueError: The source header is faulty, the IFD0 offset runs past the block, or the
            output directory has too many entries for classic TIFF.
        struct.error: A requested dimension or relocated offset cannot be represented.
    """
    order, entries = (
        _read_entries(strip_prefix(source), frozenset(), warn=_warn) if source else (">", [])
    )
    _apply_d63(entries, order, width, height, warn=_warn)
    return _write_entries(order, entries)


def from_tiff(data: bytes) -> bytes | None:
    """Build the EXIF block of a TIFF source from its IFD0, Exif IFD and GPS IFD.

    Raw entry bytes are carried without decoding values or reading pixels. Structural tags,
    the embedded profile and the XMP, IPTC and Photoshop blobs are left out. The Exif IFD's Interop
    IFD is carried as an IFD, not as the file offset the TIFF stores. A faulty entry is
    dropped alone with an IFD/tag warning. Cut arrays retain all whole entries with one
    IFD/declared-count/kept-count warning; a missing next pointer is accepted. Invalid child
    offsets/cycles and empty children are dropped with their pointers; a faulty header or
    invalid IFD0 offset discards the block. Only the first carried pointer tag per parent is
    followed; later occurrences are dropped with individual IFD/tag warnings. At most four
    directories are parsed and written; same-offset siblings are parsed separately per label.
    Carried pointers retain type 4 or 13; type 3 is retained unless relocation requires
    promotion to LONG. Other pointer types are dropped with an IFD/tag warning.

    Args:
        data: The TIFF file's bytes.

    Returns:
        The bare EXIF block, or None when no EXIF-like fields survive or the header/IFD0
        offset cannot be read (a warning is logged). BigTIFF is unsupported. D63 field replacement
        happens subsequently in :func:`edit`.
    """
    try:
        order, entries = _read_entries(data, _TIFF_STRUCTURE | {330})
        if not entries:
            return None
        return _write_entries(order, entries)
    except (ValueError, struct.error) as error:
        _log.warning("TIFF tags cannot be read for EXIF (%s); no EXIF carried", error)
        return None


def describe(block: bytes | None) -> dict[str, str]:
    """Name every IFD0, Exif-IFD and GPS field of a block with its value as text.

    Args:
        block: EXIF bytes, or None.

    Returns:
        ``"IFD0.Make"``-style names to values; empty for None.
    """
    if not block:
        return {}
    exif = load(block)
    names = {int(t): t.name for t in ExifTags.Base}
    gps = {int(t): t.name for t in ExifTags.GPS}
    out = {
        f"IFD0.{names.get(int(k), k)}": str(v)
        for k, v in exif.items()
        if int(k) not in IFD_POINTERS
    }
    out.update({f"Exif.{names.get(int(k), k)}": str(v) for k, v in exif.get_ifd(EXIF_IFD).items()})
    out.update({f"GPS.{gps.get(int(k), k)}": str(v) for k, v in exif.get_ifd(GPS_IFD).items()})
    return out


def has_thumbnail(block: bytes) -> bool:
    """Return True when IFD0 links to an IFD1 (an embedded thumbnail).

    Args:
        block: EXIF bytes.
    """
    return bool(load(block).get_ifd(ExifTags.IFD.IFD1))
