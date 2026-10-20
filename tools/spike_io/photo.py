"""WP2.1S photo leg: HEIC read and 16-bit PNG write with ICC and EXIF, on synthetic images.

Two questions for WP2.1 (AD-17), answered on synthetic fixtures only (no owner photo exists,
D102):

- **HEIC read** (pillow-heif): does the ICC profile come back byte for byte, which EXIF
  fields are read, are the pixels already rotated (by the container's ``irot`` or by EXIF),
  is the Orientation tag still there after the read (a consumer that honours it would rotate
  twice, D63), and what bit depth does a 10-bit file return.
- **PNG write**: can Pillow write a 16-bit-per-channel RGB PNG with an ICC profile and the
  D63 EXIF subset; if not, the one alternative is the stdlib writer here
  (:func:`encode_png16`: zlib + struct, chunks ``IHDR`` ``iCCP`` ``eXIf`` ``IDAT`` ``IEND``)
  with the EXIF bytes built by Pillow's ``Image.Exif`` (CHARC ruling 1b). An 8-bit PNG is
  written through Pillow as well (spec 8.1 offers both depths).

Every written PNG is re-read by a reader that did not write it:

- a file the stdlib writer wrote: Pillow (``iCCP``, ``eXIf``, and the chunk order through
  Pillow's ``PngStream``) and PyAV's bundled FFmpeg PNG decoder (exact 16-bit samples);
- a file Pillow wrote: PyAV (exact samples) and the stdlib chunk walker :func:`png_chunks`
  (``iCCP``, ``eXIf``, chunk order), which never reads a file the stdlib writer wrote.

The ICC profile is built here (:func:`display_p3_profile`): an ICC v4 matrix/TRC display
profile with Display P3 primaries and the sRGB tone curve. No third-party profile file is
used or committed.

Run from the repository root: ``uv run python tools/spike_io/photo.py run``; the fixtures and
the record ``photo.json`` go to ``<working folder>/wp2.1s/photo/``.
"""

from __future__ import annotations

import argparse
import importlib.metadata
import io
import json
import struct
import sys
import zlib
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any

import av
import numpy as np
import pillow_heif
from numpy.typing import NDArray
from PIL import ExifTags, Image, ImageCms, ImageOps, PngImagePlugin
from pillow_heif.constants import HeifCompressionFormat
from pillow_heif.misc import CtxEncode

if not __package__:
    # Script mode: sys.path[0] is tools/spike_io; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from local_config import load_local_config

WORK_SUBDIR = "wp2.1s"
"""The folder inside the working folder that every output of this package goes to."""

WIDTH = 64
"""Width of the upright synthetic image (not square, so a quarter turn changes the shape)."""

HEIGHT = 48
"""Height of the upright synthetic image."""

HEIC_QUALITY = 95
"""pillow-heif encoder quality for the HEIC fixtures (lossy; orientation is found by match)."""

MATCH_TOLERANCE = 8.0
"""Largest mean absolute difference, on an 8-bit scale, for a decoded HEIC to match a pose."""

SOFTWARE = "Clearwater"
"""The EXIF Software value a written file carries (D63)."""

PROFILE_DESCRIPTION = "Clearwater synthetic Display P3"
"""The ``desc`` text of the profile built by :func:`display_p3_profile`."""

D50 = (0.9642, 1.0, 0.8249)
"""The ICC profile connection space illuminant (XYZ)."""

D65_WHITE = (0.3127, 0.3290)
"""Display P3's white point (xy)."""

DISPLAY_P3_PRIMARIES = ((0.680, 0.320), (0.265, 0.690), (0.150, 0.060))
"""Display P3's red, green and blue primaries (xy)."""

EXIF_PREFIX = b"Exif\x00\x00"
"""The prefix Pillow and pillow-heif put before the TIFF bytes; a PNG ``eXIf`` omits it."""

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
"""The eight bytes every PNG starts with."""

ORIENTATION = int(ExifTags.Base.Orientation)
SOFTWARE_TAG = int(ExifTags.Base.Software)
PIXEL_X = int(ExifTags.Base.ExifImageWidth)  # PixelXDimension
PIXEL_Y = int(ExifTags.Base.ExifImageHeight)  # PixelYDimension
EXIF_IFD = ExifTags.IFD.Exif
GPS_IFD = ExifTags.IFD.GPSInfo

_BRADFORD = np.array(
    [[0.8951, 0.2664, -0.1614], [-0.7502, 1.7135, 0.0367], [0.0389, -0.0685, 1.0296]]
)
_INVERSE_ORIENTATION = {6: 8, 8: 6}


class PhotoError(Exception):
    """A fixture or a check could not be made as specified."""


# --- The ICC profile ------------------------------------------------------------------------


def _xyz(xy: Sequence[float]) -> NDArray[np.float64]:
    """Return the XYZ (Y = 1) of a chromaticity."""
    x, y = xy
    return np.array([x / y, 1.0, (1.0 - x - y) / y])


def primaries_matrix(
    primaries: Sequence[Sequence[float]], white: Sequence[float]
) -> NDArray[np.float64]:
    """Return the linear RGB to XYZ matrix of a set of primaries and a white point.

    Args:
        primaries: The red, green and blue chromaticities (xy).
        white: The white point's chromaticity (xy); RGB (1, 1, 1) maps to its XYZ, Y = 1.

    Returns:
        A 3x3 matrix whose columns are the primaries' XYZ.
    """
    columns = np.column_stack([_xyz(p) for p in primaries])
    scale = np.linalg.solve(columns, _xyz(white))
    return columns * scale


def bradford(
    source: Sequence[float] | NDArray[np.float64], target: Sequence[float]
) -> NDArray[np.float64]:
    """Return the Bradford chromatic adaptation matrix between two white points (XYZ)."""
    ratio = (_BRADFORD @ np.asarray(target)) / (_BRADFORD @ np.asarray(source))
    return np.asarray(np.linalg.inv(_BRADFORD) @ np.diag(ratio) @ _BRADFORD)


def _s15fixed16(value: float) -> bytes:
    """Encode an ICC ``s15Fixed16Number``."""
    return struct.pack(">i", round(value * 65536))


def _xyz_tag(xyz: Sequence[float] | NDArray[np.float64]) -> bytes:
    """Encode an ICC ``XYZType`` with one value."""
    return b"XYZ \0\0\0\0" + b"".join(_s15fixed16(v) for v in xyz)


def _mluc_tag(text: str) -> bytes:
    """Encode an ICC ``multiLocalizedUnicodeType`` with one en-US record."""
    encoded = text.encode("utf-16-be")
    return (
        b"mluc\0\0\0\0" + struct.pack(">II2s2sII", 1, 12, b"en", b"US", len(encoded), 28) + encoded
    )


def _srgb_curve_tag() -> bytes:
    """Encode the sRGB tone curve as an ICC ``parametricCurveType`` (function type 3)."""
    parameters = (2.4, 1 / 1.055, 0.055 / 1.055, 1 / 12.92, 0.04045)
    return b"para\0\0\0\0" + struct.pack(">HH", 3, 0) + b"".join(map(_s15fixed16, parameters))


def _sf32_tag(matrix: NDArray[np.float64]) -> bytes:
    """Encode an ICC ``s15Fixed16ArrayType`` (the ``chad`` matrix, row by row)."""
    return b"sf32\0\0\0\0" + b"".join(_s15fixed16(float(v)) for v in matrix.flatten())


def display_p3_profile() -> bytes:
    """Build an ICC v4.3 display profile with Display P3 primaries and the sRGB tone curve.

    The colorants are the primaries adapted from D65 to the D50 connection space with the
    Bradford matrix, which the ``chad`` tag records. The profile opens in Pillow's ``ImageCms``
    (LittleCMS); the profile ID is left zero (allowed: not computed).

    Returns:
        The profile's bytes.
    """
    adapt = bradford(_xyz(D65_WHITE), D50)
    colorants = adapt @ primaries_matrix(DISPLAY_P3_PRIMARIES, D65_WHITE)
    curve = _srgb_curve_tag()
    tags = [
        (b"desc", _mluc_tag(PROFILE_DESCRIPTION)),
        (b"cprt", _mluc_tag("No copyright; synthetic test profile")),
        (b"wtpt", _xyz_tag(D50)),
        (b"chad", _sf32_tag(adapt)),
        (b"rXYZ", _xyz_tag(colorants[:, 0])),
        (b"gXYZ", _xyz_tag(colorants[:, 1])),
        (b"bXYZ", _xyz_tag(colorants[:, 2])),
        (b"rTRC", curve),
        (b"gTRC", curve),
        (b"bTRC", curve),
    ]
    offset = 128 + 4 + 12 * len(tags)
    table = struct.pack(">I", len(tags))
    data = b""
    for signature, body in tags:
        table += struct.pack(">4sII", signature, offset + len(data), len(body))
        data += body + b"\0" * (-len(body) % 4)
    size = offset + len(data)
    header = (
        struct.pack(">I4sI4s4s4s", size, b"\0\0\0\0", 0x04300000, b"mntr", b"RGB ", b"XYZ ")
        + struct.pack(">6H", 2026, 10, 20, 0, 0, 0)
        + b"acsp"
        + b"\0" * 24  # platform, flags, manufacturer, model, attributes
        + struct.pack(">I", 0)  # rendering intent: perceptual
        + b"".join(map(_s15fixed16, D50))
        + b"\0" * 48  # creator, profile ID, reserved
    )
    if len(header) != 128:
        raise PhotoError(f"ICC header is {len(header)} bytes, not 128")
    return header + table + data


def open_profile(icc: bytes) -> ImageCms.ImageCmsProfile:
    """Open ICC bytes in Pillow's ``ImageCms`` (raises ``PIL.ImageCms.PyCMSError`` if invalid)."""
    return ImageCms.ImageCmsProfile(io.BytesIO(icc))


# --- Synthetic pixels and orientation -------------------------------------------------------


def upright_image(bits: int, width: int = WIDTH, height: int = HEIGHT) -> NDArray[Any]:
    """Return the upright synthetic RGB image: ramps that tell every rotation and flip apart.

    Red rises left to right, green top to bottom, blue with their product. Every value of the
    16-bit image has a non-zero low byte somewhere, so a truncation to 8 bits shows.

    Args:
        bits: 8 (``uint8``), 10 (``uint16`` holding 0..1023) or 16 (``uint16``).
        width: Image width.
        height: Image height.

    Returns:
        A ``(height, width, 3)`` array.
    """
    x = np.linspace(0.0, 1.0, width)[None, :] * np.ones((height, 1))
    y = np.linspace(0.0, 1.0, height)[:, None] * np.ones((1, width))
    unit = np.stack([x, y, 0.2 + 0.6 * x * y], axis=-1)
    if bits == 8:
        return np.round(unit * 255).astype(np.uint8)
    if bits in (10, 16):
        top = (1 << bits) - 1
        return np.round(unit * top).astype(np.uint16)
    raise PhotoError(f"unsupported bit depth {bits}")


def apply_orientation(pixels: NDArray[Any], orientation: int) -> NDArray[Any]:
    """Transform stored pixels as a viewer honouring EXIF Orientation shows them.

    Matches Pillow's ``ImageOps.exif_transpose`` for the eight values (checked in the tests).

    Args:
        pixels: A ``(height, width, channels)`` array as stored.
        orientation: The EXIF Orientation value, 1 to 8.

    Returns:
        The displayed array (a view where possible).
    """
    transforms = {
        1: lambda p: p,
        2: lambda p: p[:, ::-1],
        3: lambda p: p[::-1, ::-1],
        4: lambda p: p[::-1],
        5: lambda p: p.transpose(1, 0, 2),
        6: lambda p: np.rot90(p, -1),
        7: lambda p: np.rot90(p.transpose(1, 0, 2), 2),
        8: lambda p: np.rot90(p, 1),
    }
    if orientation not in transforms:
        raise PhotoError(f"EXIF Orientation {orientation} is not 1-8")
    return np.ascontiguousarray(transforms[orientation](pixels))


def stored_image(upright: NDArray[Any], orientation: int) -> NDArray[Any]:
    """Return the pixels a camera stores so that ``orientation`` displays ``upright``."""
    return apply_orientation(upright, _INVERSE_ORIENTATION.get(orientation, orientation))


def _to_unit(pixels: NDArray[Any], bits: int) -> NDArray[np.float64]:
    """Scale samples to 0..1."""
    return pixels.astype(np.float64) / ((1 << bits) - 1)


def pose(
    decoded: NDArray[Any],
    bits: int,
    upright: NDArray[Any],
    upright_bits: int,
    orientation: int,
) -> str:
    """Classify a decoded image against the poses a reader can produce.

    Args:
        decoded: The decoded pixels.
        bits: Bit depth of ``decoded``'s scale (8, or 16 for pillow-heif's shifted 10-bit).
        upright: The upright image the fixture was made from.
        upright_bits: Bit depth of ``upright``'s scale (8 or 10).
        orientation: The orientation the fixture carries.

    Returns:
        ``"upright"`` (rotated once, correct), ``"stored"`` (not rotated), ``"twice"``
        (the rotation applied twice) or ``"other"``. For orientation 1 every pose is
        ``"upright"``.
    """
    reference = _to_unit(upright, upright_bits)
    candidates = {
        "upright": reference,
        "stored": stored_image(reference, orientation),
        "twice": apply_orientation(reference, orientation),
    }
    measured = _to_unit(decoded, bits)
    best, best_error = "other", MATCH_TOLERANCE / 255
    for name, candidate in candidates.items():
        if candidate.shape != measured.shape:
            continue
        error = float(np.mean(np.abs(candidate - measured)))
        if error < best_error:  # strict: a tie keeps the earlier pose ("upright" first)
            best, best_error = name, error
    return best


# --- EXIF -----------------------------------------------------------------------------------


def source_exif(orientation: int, width: int, height: int, thumbnail: bool = False) -> bytes:
    """Build a camera-like EXIF block with Pillow's ``Image.Exif``.

    IFD0 carries Make, Model, DateTime and Orientation; the Exif IFD DateTimeOriginal, an
    FNumber and the pixel dimensions; the GPS IFD a latitude reference. With ``thumbnail`` an
    IFD1 with a small JPEG is appended (:func:`add_thumbnail`), as a camera JPEG carries.

    Args:
        orientation: The Orientation value.
        width: PixelXDimension.
        height: PixelYDimension.
        thumbnail: Append an IFD1 thumbnail.

    Returns:
        :data:`EXIF_PREFIX` followed by the TIFF bytes.
    """
    exif = Image.Exif()
    exif[int(ExifTags.Base.Make)] = "Apple"
    exif[int(ExifTags.Base.Model)] = "iPhone (synthetic)"
    exif[int(ExifTags.Base.DateTime)] = "2026:10:20 10:00:00"
    exif[ORIENTATION] = orientation
    sub = exif.get_ifd(EXIF_IFD)
    sub[int(ExifTags.Base.DateTimeOriginal)] = "2026:10:20 10:00:00"
    sub[int(ExifTags.Base.FNumber)] = 1.8
    sub[PIXEL_X] = width
    sub[PIXEL_Y] = height
    exif.get_ifd(GPS_IFD)[int(ExifTags.GPS.GPSLatitudeRef)] = "N"
    data = exif.tobytes()
    if thumbnail:
        buffer = io.BytesIO()
        Image.new("RGB", (8, 6), (90, 140, 160)).save(buffer, "JPEG")
        data = add_thumbnail(data, buffer.getvalue())
    return data


def add_thumbnail(exif: bytes, jpeg: bytes) -> bytes:
    """Append an IFD1 carrying a JPEG thumbnail to EXIF bytes that have none.

    Pillow's EXIF writer cannot write IFD1, so the IFD is appended here: IFD0's next-IFD
    offset is pointed at a new IFD1 (Compression 6, JPEGInterchangeFormat and its length)
    followed by the JPEG. Existing offsets are unchanged.

    Args:
        exif: :data:`EXIF_PREFIX` plus TIFF bytes, IFD0 last in its chain.
        jpeg: The thumbnail.

    Returns:
        The EXIF bytes with the thumbnail.

    Raises:
        PhotoError: IFD0 already links to another IFD.
    """
    tiff = exif.removeprefix(EXIF_PREFIX)
    endian = "<" if tiff[:2] == b"II" else ">"
    (ifd0,) = struct.unpack(endian + "I", tiff[4:8])
    (count,) = struct.unpack(endian + "H", tiff[ifd0 : ifd0 + 2])
    link = ifd0 + 2 + 12 * count
    if struct.unpack(endian + "I", tiff[link : link + 4]) != (0,):
        raise PhotoError("IFD0 already links to a next IFD")
    padding = b"\0" * (len(tiff) % 2)
    ifd1_at = len(tiff) + len(padding)
    thumb_at = ifd1_at + 2 + 3 * 12 + 4
    entries = (
        struct.pack(endian + "HHIHH", 0x0103, 3, 1, 6, 0)
        + struct.pack(endian + "HHII", 0x0201, 4, 1, thumb_at)
        + struct.pack(endian + "HHII", 0x0202, 4, 1, len(jpeg))
    )
    ifd1 = struct.pack(endian + "H", 3) + entries + struct.pack(endian + "I", 0)
    out = tiff[:link] + struct.pack(endian + "I", ifd1_at) + tiff[link + 4 :] + padding
    return EXIF_PREFIX + out + ifd1 + jpeg


def load_exif(data: bytes) -> Image.Exif:
    """Load EXIF bytes (with or without the :data:`EXIF_PREFIX`) into Pillow's reader."""
    exif = Image.Exif()
    exif.load(data if data.startswith(EXIF_PREFIX) else EXIF_PREFIX + data)
    return exif


def edit_exif(source: bytes, width: int, height: int) -> bytes:
    """Return the D63-edited EXIF a written image carries, built by Pillow's ``Image.Exif``.

    Orientation is set to 1 (the rotation is applied to the pixels), the thumbnail is
    dropped (Pillow's writer does not write IFD1), PixelXDimension and PixelYDimension are
    set to the written size, Software is set to :data:`SOFTWARE`; every other field of IFD0,
    the Exif IFD and the GPS IFD is kept.

    Args:
        source: The source image's EXIF bytes.
        width: Width of the written image.
        height: Height of the written image.

    Returns:
        :data:`EXIF_PREFIX` followed by the TIFF bytes.
    """
    exif = load_exif(source)
    sub = exif.get_ifd(EXIF_IFD)
    exif.get_ifd(GPS_IFD)  # materialise, so the writer serialises it
    exif[ORIENTATION] = 1
    exif[SOFTWARE_TAG] = SOFTWARE
    sub[PIXEL_X] = width
    sub[PIXEL_Y] = height
    return exif.tobytes()


def _fields(exif: Image.Exif) -> dict[str, Any]:
    """Name every IFD0, Exif-IFD and GPS field with a plain value (pointers left out)."""
    pointers = {int(EXIF_IFD), int(GPS_IFD), int(ExifTags.IFD.Interop)}
    names = {int(t): t.name for t in ExifTags.Base}
    out: dict[str, Any] = {
        f"IFD0.{names.get(k, k)}": v for k, v in exif.items() if int(k) not in pointers
    }
    out.update({f"Exif.{names.get(k, k)}": v for k, v in exif.get_ifd(EXIF_IFD).items()})
    gps = {int(t): t.name for t in ExifTags.GPS}
    out.update({f"GPS.{gps.get(k, k)}": v for k, v in exif.get_ifd(GPS_IFD).items()})
    return out


def exif_fields(data: bytes) -> dict[str, str]:
    """Return EXIF fields by name with their values as text (for the record)."""
    return {name: str(value) for name, value in _fields(load_exif(data)).items()}


def has_ifd1(data: bytes) -> bool:
    """Return True when IFD0 links to an IFD1 (a thumbnail), read with Pillow's reader."""
    return bool(load_exif(data).get_ifd(ExifTags.IFD.IFD1))


def exif_problems(written: bytes, source: bytes, width: int, height: int) -> list[str]:
    """Check written EXIF against D63; return the name of every failed property.

    Args:
        written: The EXIF found in the written file.
        source: The source EXIF.
        width: Width of the written image.
        height: Height of the written image.

    Returns:
        Failed properties: ``"Orientation"``, ``"IFD1"``, ``"PixelXDimension"``,
        ``"PixelYDimension"``, ``"Software"``, ``"kept:<field>"``; empty when all hold.
    """
    exif = load_exif(written)
    sub = exif.get_ifd(EXIF_IFD)
    problems = []
    if exif.get(ORIENTATION) != 1:
        problems.append("Orientation")
    if has_ifd1(written):
        problems.append("IFD1")
    if sub.get(PIXEL_X) != width:
        problems.append("PixelXDimension")
    if sub.get(PIXEL_Y) != height:
        problems.append("PixelYDimension")
    if exif.get(SOFTWARE_TAG) != SOFTWARE:
        problems.append("Software")
    edited = {"IFD0.Orientation", "IFD0.Software", "Exif.ExifImageWidth", "Exif.ExifImageHeight"}
    kept = _fields(exif)
    for name, value in _fields(load_exif(source)).items():
        if name not in edited and kept.get(name) != value:
            problems.append(f"kept:{name}")
    return problems


# --- PNG: writers ---------------------------------------------------------------------------


def _chunk(kind: bytes, data: bytes) -> bytes:
    """Encode one PNG chunk (length, type, data, CRC-32 over type and data)."""
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def encode_png16(
    pixels: NDArray[np.uint16], icc: bytes, exif: bytes, profile_name: str = "Display P3"
) -> bytes:
    """Encode a 16-bit RGB PNG with an ICC profile and EXIF, with the stdlib only.

    Chunks, in order: ``IHDR`` (bit depth 16, colour type 2, no interlace), ``iCCP`` (the
    profile deflated), ``eXIf`` (the TIFF bytes, :data:`EXIF_PREFIX` removed), one ``IDAT``
    (filter 0 on every row, big-endian samples) and ``IEND``.

    Args:
        pixels: A ``(height, width, 3)`` ``uint16`` array.
        icc: The ICC profile.
        exif: EXIF bytes, with or without the :data:`EXIF_PREFIX`.
        profile_name: The ``iCCP`` profile name (Latin-1, 1-79 bytes).

    Returns:
        The PNG file's bytes.

    Raises:
        PhotoError: The array is not ``(h, w, 3)`` ``uint16``.
    """
    if pixels.dtype != np.uint16 or pixels.ndim != 3 or pixels.shape[2] != 3:
        raise PhotoError(f"need (h, w, 3) uint16, got {pixels.shape} {pixels.dtype}")
    height, width = pixels.shape[:2]
    rows = np.zeros((height, 1 + width * 6), dtype=np.uint8)
    rows[:, 1:] = pixels.astype(">u2").view(np.uint8).reshape(height, width * 6)
    return (
        PNG_SIGNATURE
        + _chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 16, 2, 0, 0, 0))
        + _chunk(b"iCCP", profile_name.encode("latin-1") + b"\0\0" + zlib.compress(icc))
        + _chunk(b"eXIf", exif.removeprefix(EXIF_PREFIX))
        + _chunk(b"IDAT", zlib.compress(rows.tobytes()))
        + _chunk(b"IEND", b"")
    )


def pillow_png16_attempt(pixels: NDArray[np.uint16], icc: bytes, exif: bytes) -> dict[str, Any]:
    """Try Pillow's 16-bit RGB PNG path (AD-17) and report what it actually writes.

    Two routes: ``Image.fromarray`` on the ``uint16`` array, and ``Image.frombytes`` with
    the big-endian 16-bit raw mode ``RGB;16B``. The second's PNG is saved with the profile and
    EXIF to memory and its ``IHDR`` read by :func:`png_chunks`.

    Args:
        pixels: A ``(height, width, 3)`` ``uint16`` array.
        icc: The ICC profile.
        exif: EXIF bytes.

    Returns:
        ``fromarray`` (the mode, or the error), ``frombytes_mode``, ``png_bit_depth`` and
        ``writes_16bit_rgb`` (True only if the PNG has bit depth 16 and colour type 2).
    """
    record: dict[str, Any] = {}
    try:
        record["fromarray"] = Image.fromarray(pixels).mode
    except (TypeError, ValueError) as error:
        record["fromarray"] = f"{type(error).__name__}: {error}"
    height, width = pixels.shape[:2]
    image = Image.frombytes(
        "RGB", (width, height), pixels.astype(">u2").tobytes(), "raw", "RGB;16B"
    )
    record["frombytes_mode"] = image.mode
    buffer = io.BytesIO()
    image.save(buffer, "PNG", icc_profile=icc, exif=exif)
    ihdr = dict(png_chunks(buffer.getvalue()))["IHDR"]
    record["png_bit_depth"], record["png_colour_type"] = ihdr[8], ihdr[9]
    record["writes_16bit_rgb"] = ihdr[8] == 16 and ihdr[9] == 2
    return record


def write_png8_pillow(path: Path, pixels: NDArray[np.uint8], icc: bytes, exif: bytes) -> None:
    """Write an 8-bit RGB PNG with an ICC profile and EXIF through Pillow."""
    Image.fromarray(pixels).save(path, "PNG", icc_profile=icc, exif=exif)


# --- PNG: readers ---------------------------------------------------------------------------


def png_chunks(data: bytes) -> list[tuple[str, bytes]]:
    """Walk a PNG's chunks with the stdlib (type, data), checking each CRC.

    Used only on files Pillow wrote: it shares no code with :func:`encode_png16`.

    Raises:
        PhotoError: The signature or a CRC is wrong.
    """
    if not data.startswith(PNG_SIGNATURE):
        raise PhotoError("not a PNG")
    chunks = []
    at = len(PNG_SIGNATURE)
    while at < len(data):
        (length,) = struct.unpack(">I", data[at : at + 4])
        kind = data[at + 4 : at + 8]
        body = data[at + 8 : at + 8 + length]
        (crc,) = struct.unpack(">I", data[at + 8 + length : at + 12 + length])
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise PhotoError(f"bad CRC on {kind!r}")
        chunks.append((kind.decode("latin-1"), body))
        at += 12 + length
    return chunks


def stdlib_iccp(data: bytes) -> bytes | None:
    """Return the inflated ``iCCP`` profile of a PNG Pillow wrote (stdlib walker), if any."""
    for kind, body in png_chunks(data):
        if kind == "iCCP":
            name_end = body.index(b"\0")
            return zlib.decompress(body[name_end + 2 :])
    return None


def pillow_chunk_order(path: Path) -> list[str]:
    """Return a PNG's chunk types in order, read with Pillow's ``PngStream``."""
    order = []
    with path.open("rb") as handle:
        handle.read(len(PNG_SIGNATURE))
        stream = PngImagePlugin.PngStream(handle)
        while True:
            kind, position, length = stream.read()
            order.append(kind.decode("latin-1"))
            if kind == b"IEND":
                break
            handle.seek(position + length + 4)
    return order


def pyav_png(path: Path) -> tuple[NDArray[Any], str]:
    """Decode a PNG with PyAV's bundled FFmpeg PNG decoder.

    The frame's ICC side data is NOT read: with PyAV 16.1.0, touching ``frame.side_data`` on
    a PNG frame that carries an ICC profile makes the process crash (access violation) when
    the frame is freed (report section 8).

    Returns:
        The samples (``uint16`` native for ``rgb48be``, ``uint8`` for ``rgb24``) and the
        decoder's pixel format.
    """
    with av.open(str(path), format="png_pipe") as container:
        frame = next(container.decode(video=0))
        return np.array(frame.to_ndarray()), frame.format.name


def verify_png16(path: Path, pixels: NDArray[np.uint16], icc: bytes, exif: bytes) -> dict[str, Any]:
    """Re-read a PNG the stdlib writer wrote, with Pillow and PyAV only.

    Args:
        path: The PNG.
        pixels: The samples written.
        icc: The profile written.
        exif: The EXIF written.

    Returns:
        The record: each property with the reader that verified it (keys end in the reader).
    """
    decoded, pixel_format = pyav_png(path)
    with Image.open(path) as image:
        image.load()
        pillow_mode = image.mode
        pillow_icc = image.info.get("icc_profile")
        pillow_exif = image.info.get("exif")
        pillow_finds_exif = bool(image.getexif())
        pillow_sample = image.getpixel((WIDTH - 1, 0))
    order = pillow_chunk_order(path)
    exact = decoded.dtype == np.uint16 and decoded.shape == pixels.shape
    differing = int(np.count_nonzero(decoded != pixels)) if exact else pixels.size
    return {
        "writer": "stdlib (encode_png16)",
        "values_exact_pyav": exact and differing == 0,
        "differing_samples_pyav": differing,
        "pixel_format_pyav": pixel_format,
        "iccp_identical_pillow": pillow_icc == icc,
        "exif_identical_pillow": pillow_exif == EXIF_PREFIX + exif.removeprefix(EXIF_PREFIX),
        "pillow_finds_exif": pillow_finds_exif,
        "pillow_mode": pillow_mode,
        "pillow_sample_top_right": list(pillow_sample)
        if isinstance(pillow_sample, tuple)
        else pillow_sample,
        "chunk_order_pillow": order,
        "iccp_before_idat": _before(order, "iCCP", "IDAT"),
        "exif_before_idat": _before(order, "eXIf", "IDAT"),
    }


def verify_png8(path: Path, pixels: NDArray[np.uint8], icc: bytes, exif: bytes) -> dict[str, Any]:
    """Re-read a PNG Pillow wrote, with PyAV and the stdlib chunk walker only.

    Args:
        path: The PNG.
        pixels: The samples written.
        icc: The profile written.
        exif: The EXIF written.

    Returns:
        The record: each property with the reader that verified it (keys end in the reader).
    """
    data = path.read_bytes()
    decoded, pixel_format = pyav_png(path)
    chunks = png_chunks(data)
    order = [kind for kind, _ in chunks]
    written_exif = dict(chunks).get("eXIf")
    exact = decoded.dtype == np.uint8 and decoded.shape == pixels.shape
    differing = int(np.count_nonzero(decoded != pixels)) if exact else pixels.size
    ihdr = dict(chunks)["IHDR"]
    return {
        "writer": "Pillow",
        "png_bit_depth_stdlib": ihdr[8],
        "values_exact_pyav": exact and differing == 0,
        "differing_samples_pyav": differing,
        "pixel_format_pyav": pixel_format,
        "iccp_identical_stdlib": stdlib_iccp(data) == icc,
        "exif_identical_stdlib": written_exif == exif.removeprefix(EXIF_PREFIX),
        "chunk_order_stdlib": order,
        "iccp_before_idat": _before(order, "iCCP", "IDAT"),
        "exif_before_idat": _before(order, "eXIf", "IDAT"),
    }


def _before(order: Sequence[str], first: str, second: str) -> bool:
    """Return True when chunk ``first`` is present and precedes ``second``."""
    return first in order and second in order and order.index(first) < order.index(second)


VERIFIED = (
    "values_exact_pyav",
    "iccp_identical_pillow",
    "iccp_identical_stdlib",
    "exif_identical_pillow",
    "exif_identical_stdlib",
    "iccp_before_idat",
)
"""The verification properties that must hold; :func:`failures` names any that does not."""


def failures(record: Mapping[str, Any]) -> list[str]:
    """Name every property of :data:`VERIFIED` present in ``record`` and not True."""
    return [key for key in VERIFIED if key in record and record[key] is not True]


# --- HEIC -----------------------------------------------------------------------------------


HEIC_MODES = ("public", "exif-only", "irot-only")
"""How a HEIC fixture carries its orientation.

``public``: pillow-heif's public ``encode``, which writes an ``irot``/``imir`` transform from
the EXIF Orientation and keeps the tag (the iPhone's layout); ``exif-only``: the tag with no
transform; ``irot-only``: the transform with the tag set to 1. The last two use pillow-heif's
private ``misc.CtxEncode`` (its ``image_orientation`` argument): the public API has no way to
write one without the other.
"""


def write_heic(
    path: Path, upright: NDArray[Any], bits: int, orientation: int, mode: str, icc: bytes
) -> bytes:
    """Write a HEIC fixture with pillow-heif's encoder (x265).

    The stored pixels are ``upright`` turned so that ``orientation`` displays it upright.

    Args:
        path: The output file.
        upright: The upright image (``uint8`` for 8 bits; ``uint16`` 0..1023 for 10 bits).
        bits: 8 or 10. A 10-bit fixture is passed as ``RGB;16`` (values shifted left by 6),
            which pillow-heif encodes at 10 bits.
        orientation: The orientation the file carries (1, 6 or 8).
        mode: One of :data:`HEIC_MODES`.
        icc: The ICC profile to embed (``prof`` type).

    Returns:
        The EXIF bytes written (:func:`source_exif` of the stored size; Orientation 1 for
        ``irot-only``).

    Raises:
        PhotoError: Unknown mode or bit depth.
    """
    stored = stored_image(upright, orientation)
    height, width = stored.shape[:2]
    if bits == 8:
        pixel_mode, data = "RGB", stored.astype(np.uint8).tobytes()
    elif bits == 10:
        pixel_mode, data = "RGB;16", (stored.astype(np.uint16) << 6).tobytes()
    else:
        raise PhotoError(f"unsupported HEIC bit depth {bits}")
    tag = 1 if mode == "irot-only" else orientation
    exif = source_exif(tag, width, height)
    size = (width, height)
    if mode == "public":
        pillow_heif.encode(
            pixel_mode, size, data, str(path), quality=HEIC_QUALITY, icc_profile=icc, exif=exif
        )
        return exif
    if mode not in HEIC_MODES:
        raise PhotoError(f"unknown HEIC mode {mode!r}")
    transform = orientation if mode == "irot-only" else 1
    encoder = CtxEncode(HeifCompressionFormat.HEVC, quality=HEIC_QUALITY)
    encoder.add_image(
        size,
        pixel_mode,
        data,
        image_orientation=transform,
        primary=True,
        icc_profile=icc,
        exif=exif,
    )
    encoder.save(str(path))
    return exif


def _exif_orientation(exif: bytes | None) -> int | None:
    """Return the Orientation in EXIF bytes, or None when absent."""
    if not exif:
        return None
    value = load_exif(exif).get(ORIENTATION)
    return int(value) if value is not None else None


def heif_transforms(data: bytes) -> dict[str, Any]:
    """Find the transform properties in a HEIF file's ``meta/iprp/ipco`` box (stdlib walk).

    Args:
        data: The HEIF file's bytes.

    Returns:
        ``irot``: the rotation in degrees anticlockwise, or None when there is no ``irot``
        box; ``imir``: the mirror axis (0 vertical, 1 horizontal), or None. The ``ipma``
        box that associates properties with items is NOT read, so this is valid only for a
        file with one image item, as the fixtures are. A real camera HEIC (a grid of tiles,
        thumbnails, auxiliary images) needs the primary item's ``ipma`` entries.
    """

    def boxes(start: int, end: int) -> list[tuple[str, int, int]]:
        found = []
        at = start
        while at + 8 <= end:
            (size,) = struct.unpack(">I", data[at : at + 4])
            kind = data[at + 4 : at + 8].decode("latin-1")
            header = 8
            if size == 1:
                (size,) = struct.unpack(">Q", data[at + 8 : at + 16])
                header = 16
            elif size == 0:
                size = end - at
            found.append((kind, at + header, at + size))
            at += size
        return found

    def child(kind: str, start: int, end: int) -> tuple[int, int] | None:
        for name, body, stop in boxes(start, end):
            if name == kind:
                return body, stop
        return None

    result: dict[str, Any] = {"irot": None, "imir": None}
    meta = child("meta", 0, len(data))
    iprp = child("iprp", meta[0] + 4, meta[1]) if meta else None  # meta is a full box
    ipco = child("ipco", *iprp) if iprp else None
    if ipco:
        for name, body, _ in boxes(*ipco):
            if name == "irot":
                result["irot"] = (data[body] & 3) * 90
            elif name == "imir":
                result["imir"] = data[body] & 1
    return result


def read_heic(
    path: Path, upright: NDArray[Any], bits: int, orientation: int, icc: bytes, exif: bytes
) -> dict[str, Any]:
    """Read a HEIC fixture back two ways and report the D63-relevant facts.

    - ``raw``: ``pillow_heif.open_heif`` (8-bit default, and ``convert_hdr_to_8bit=False``).
      libheif applies the container transform; ``info["exif"]`` is the file's EXIF as stored.
    - ``plugin``: ``Image.open`` with pillow-heif's Pillow opener, which also resets the EXIF
      Orientation to 1 and keeps the old value in ``info["original_orientation"]``.

    For each, ``pose`` is where the decoded pixels are, and ``pose_after_exif`` where they are
    once a consumer honours the Orientation tag it is handed (``ImageOps.exif_transpose`` for
    the plugin, :func:`apply_orientation` for raw): ``"twice"`` there is the double rotation.

    Args:
        path: The HEIC.
        upright: The upright image the fixture was made from.
        bits: ``upright``'s bit depth (8 or 10).
        orientation: The orientation the fixture carries.
        icc: The profile embedded.
        exif: The EXIF written (:func:`write_heic`'s return).

    Returns:
        The per-case record. ``exif_fields_raw_equal``: every field and value of the file's
        EXIF equals what was written; ``exif_fields_plugin_mismatch``: the fields whose value
        differs through the plugin (only Orientation is expected, after its reset).
    """
    written = exif_fields(exif)
    raw = pillow_heif.open_heif(str(path))
    raw_pixels = np.asarray(raw)
    raw_tag = _exif_orientation(raw.info.get("exif"))
    raw_after = apply_orientation(raw_pixels, raw_tag or 1)
    hdr = pillow_heif.open_heif(str(path), convert_hdr_to_8bit=False)
    hdr_pixels = np.asarray(hdr)
    hdr_bits = 16 if hdr_pixels.dtype == np.uint16 else 8
    pillow_heif.register_heif_opener()
    with Image.open(path) as image:
        image.load()
        plugin_pixels = np.asarray(image.convert("RGB"))
        plugin_icc = image.info.get("icc_profile")
        plugin_exif = image.info.get("exif")
        plugin_original = image.info.get("original_orientation")
        plugin_after = np.asarray(ImageOps.exif_transpose(image).convert("RGB"))
    through_plugin = exif_fields(plugin_exif) if plugin_exif else {}
    return {
        "container_transform": heif_transforms(path.read_bytes()),
        "file_exif_orientation": raw_tag,
        "file_bit_depth": raw.info.get("bit_depth"),
        "icc_identical_raw": raw.info.get("icc_profile") == icc,
        "icc_identical_plugin": plugin_icc == icc,
        "exif_fields_plugin": sorted(exif_fields(plugin_exif)) if plugin_exif else [],
        "exif_fields_raw_equal": exif_fields(raw.info.get("exif") or b"") == written,
        "exif_fields_plugin_mismatch": sorted(
            name
            for name in set(written) | set(through_plugin)
            if written.get(name) != through_plugin.get(name)
        ),
        "raw_pose": pose(raw_pixels, 8, upright, bits, orientation),
        "raw_pose_after_exif": pose(raw_after, 8, upright, bits, orientation),
        "plugin_exif_orientation": _exif_orientation(plugin_exif),
        "plugin_original_orientation": plugin_original,
        "plugin_pose": pose(plugin_pixels, 8, upright, bits, orientation),
        "plugin_pose_after_exif": pose(plugin_after, 8, upright, bits, orientation),
        "default_mode": raw.mode,
        "hdr_mode": hdr.mode,
        "hdr_dtype": str(hdr_pixels.dtype),
        "hdr_max": int(hdr_pixels.max()),
        "hdr_pose": pose(hdr_pixels, hdr_bits, upright, bits, orientation),
    }


# --- The run --------------------------------------------------------------------------------


def run(out: Path) -> dict[str, Any]:
    """Write every fixture under ``out`` and return the record.

    Args:
        out: The output folder (created).

    Returns:
        The record: libraries, the profile check, the HEIC cases, the Pillow 16-bit attempt,
        the 16-bit stdlib PNG and the 8-bit Pillow PNG with their verifications.
    """
    out.mkdir(parents=True, exist_ok=True)
    icc = display_p3_profile()
    (out / "display-p3.icc").write_bytes(icc)
    profile = open_profile(icc)
    record: dict[str, Any] = {
        "libraries": {
            "pillow": importlib.metadata.version("pillow"),
            "pillow_heif": pillow_heif.__version__,
            "libheif": pillow_heif.libheif_info(),
            "av": av.__version__,
            "ffmpeg_in_av": av.ffmpeg_version_info,
        },
        "profile": {
            "bytes": len(icc),
            "imagecms_description": ImageCms.getProfileDescription(profile).strip(),
            "colorants_xyY": [
                getattr(profile.profile, f"{c}_colorant")[1] for c in ("red", "green", "blue")
            ],
        },
    }
    heic: list[dict[str, Any]] = []
    for bits in (8, 10):
        upright = upright_image(bits)
        for mode, orientation in [("public", 1), ("public", 6), ("public", 8)] + (
            [("exif-only", 6), ("irot-only", 6)] if bits == 8 else []
        ):
            path = out / f"heic-{bits}bit-{mode}-o{orientation}.heic"
            exif = write_heic(path, upright, bits, orientation, mode, icc)
            case = {"file": path.name, "bits": bits, "mode": mode, "orientation": orientation}
            case.update(read_heic(path, upright, bits, orientation, icc, exif))
            heic.append(case)
    record["heic"] = heic
    pixels16 = upright_image(16)
    pixels8 = upright_image(8)
    source = source_exif(6, HEIGHT, WIDTH, thumbnail=True)
    edited = edit_exif(source, WIDTH, HEIGHT)
    record["exif"] = {
        "source_fields": exif_fields(source),
        "source_has_ifd1": has_ifd1(source),
        "edited_fields": exif_fields(edited),
        "edited_problems": exif_problems(edited, source, WIDTH, HEIGHT),
    }
    record["pillow_png16"] = pillow_png16_attempt(pixels16, icc, edited)
    png16 = out / "rgb16-stdlib.png"
    png16.write_bytes(encode_png16(pixels16, icc, edited))
    record["png16"] = {"file": png16.name, **verify_png16(png16, pixels16, icc, edited)}
    with Image.open(png16) as image:
        found = image.info.get("exif", b"")
    record["png16"]["exif_problems_pillow"] = exif_problems(found, source, WIDTH, HEIGHT)
    png8 = out / "rgb8-pillow.png"
    write_png8_pillow(png8, pixels8, icc, edited)
    record["png8"] = {"file": png8.name, **verify_png8(png8, pixels8, icc, edited)}
    found8 = dict(png_chunks(png8.read_bytes())).get("eXIf", b"")
    record["png8"]["exif_problems_stdlib"] = exif_problems(found8, source, WIDTH, HEIGHT)
    record["failures"] = {
        "png16": failures(record["png16"]),
        "png8": failures(record["png8"]),
    }
    return record


def _work_folder(config_path: Path | None) -> Path:
    """Return ``<working folder>/wp2.1s/photo``, refusing a folder inside the footage folder."""
    config = load_local_config(config_path)
    out = config.working_path / WORK_SUBDIR / "photo"
    footage = config.footage_path.resolve()
    resolved = out.resolve()
    if resolved == footage or footage in resolved.parents:
        raise PhotoError(f"{out} is inside the footage folder")
    return out


def main(argv: Sequence[str] | None = None) -> int:
    """Command line: ``run`` writes the fixtures and ``photo.json`` to the working folder."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("command", choices=["run"])
    parser.add_argument("--config", type=Path, default=None, help="local configuration file")
    arguments = parser.parse_args(argv)
    out = _work_folder(arguments.config)
    record = run(out)
    path = out / "photo.json"
    path.write_text(json.dumps(record, indent=1, default=str) + "\n", encoding="utf-8")
    print(path)
    return 0


if __name__ == "__main__":
    sys.exit(main())
