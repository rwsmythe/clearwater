r"""EXIF reading and the D63 edit (spec 8.1; WP3.6).

``PhotoMetadata.exif`` is the bare TIFF-structured block (it starts ``II*\0`` or ``MM\0*``; an
``Exif\0\0`` prefix is stripped on read). Pillow's ``Image.Exif`` parses and serialises it.
"""

from __future__ import annotations

import io
import logging

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


def edit(source: bytes | None, width: int, height: int) -> bytes:
    r"""Return the D63-edited EXIF block a written image carries.

    Orientation is set to 1 (the rotation is in the pixels), the thumbnail (IFD1) is dropped
    (Pillow's writer does not write it), PixelXDimension and PixelYDimension are set to the
    written size, Software is set to :data:`SOFTWARE`; every other field of IFD0, the Exif IFD,
    the Interop IFD and the GPS IFD is kept. A source without EXIF gets a minimal block with
    those four fields.

    Args:
        source: The source EXIF block, or None.
        width: Width of the written image.
        height: Height of the written image.

    Returns:
        The bare TIFF-structured block (no ``Exif\0\0`` prefix).
    """
    exif = load(source) if source else Image.Exif()
    exif[ORIENTATION] = 1
    exif[SOFTWARE_TAG] = SOFTWARE
    sub = exif.get_ifd(EXIF_IFD)
    sub[PIXEL_X] = width
    sub[PIXEL_Y] = height
    return strip_prefix(exif.tobytes())


def _materialise_interop(source: Image.Exif, fields: dict[int, object]) -> None:
    """Replace the Exif IFD's Interop pointer in ``fields`` by the Interop IFD it points to.

    The pointer is a file offset into the TIFF, meaningless in the block built from it, so the
    IFD itself is carried (Pillow writes a dict value as a nested IFD). A pointer to an IFD
    that is empty or unreadable is dropped rather than left dangling.
    """
    if INTEROP_POINTER not in fields:
        return
    try:
        interop = dict(source.get_ifd(INTEROP_IFD))
    except Exception as error:  # Pillow raises assorted types on a bad offset
        _log.warning("TIFF Interop IFD cannot be read (%s); dropped", error)
        interop = {}
    if interop:
        fields[INTEROP_POINTER] = interop
    else:
        del fields[INTEROP_POINTER]


def from_tiff(data: bytes) -> bytes | None:
    """Build the EXIF block of a TIFF source from its IFD0, Exif IFD and GPS IFD.

    Pillow opens the file lazily for its tags only, never for pixels. Structural tags, the
    embedded profile and the XMP, IPTC and Photoshop blobs are left out. The Exif IFD's Interop
    IFD is carried as an IFD, not as the file offset the TIFF stores.

    Args:
        data: The TIFF file's bytes.

    Returns:
        The bare EXIF block, or None when the file has no EXIF-like fields or Pillow cannot
        read its tags (a warning is logged).
    """
    found = False
    try:
        with Image.open(io.BytesIO(data)) as image:
            source = image.getexif()
            built = Image.Exif()
            built.endian = source.endian  # Pillow writes big-endian when unset
            for tag, value in source.items():
                if int(tag) not in _TIFF_STRUCTURE and int(tag) not in IFD_POINTERS:
                    built[tag] = value
                    found = True
            for pointer in (EXIF_IFD, GPS_IFD):
                fields = dict(source.get_ifd(pointer))
                if pointer == EXIF_IFD:
                    _materialise_interop(source, fields)
                if fields:
                    built.get_ifd(pointer).update(fields)
                    found = True
    except Exception as error:  # Pillow raises assorted types on odd TIFF tags
        _log.warning("TIFF tags cannot be read for EXIF (%s); no EXIF carried", error)
        return None
    if not found:
        return None
    return strip_prefix(built.tobytes())


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
