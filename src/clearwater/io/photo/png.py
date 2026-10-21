"""PNG chunks, the stdlib writer (8 and 16 bit) and the 16-bit reader (WP3.6; AD-17).

Pillow 12.3 cannot write a 16-bit RGB PNG and reads one at 8 bits (DR-11), so this module owns
both directions for the depths Pillow gets wrong. The writer is one code path for 8 and 16 bit:
``IHDR``, ``iCCP``, ``eXIf``, the provenance ``iTXt``, ``IDAT``, ``IEND``. The reader decodes
non-interlaced 16-bit PNG only; an interlaced (Adam7) file is refused by name.
"""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from clearwater.io.photo.errors import PhotoReadError
from clearwater.io.photo.icc import description

SIGNATURE = b"\x89PNG\r\n\x1a\n"
"""The eight bytes every PNG starts with."""

PROVENANCE_KEYWORD = "clearwater-provenance"
"""The ``iTXt`` keyword of the provenance chunk (D91)."""

_IDAT_SIZE = 1 << 20
_BLOCK_ROWS = 256
_COMPRESSION_LEVEL = 6
_DEFAULT_PROFILE_NAME = "ICC profile"
_CHANNELS = {0: 1, 2: 3, 4: 2, 6: 4}


def chunk(kind: bytes, data: bytes) -> bytes:
    """Encode one PNG chunk: length, type, data, CRC-32 over type and data.

    Args:
        kind: The four-byte chunk type.
        data: The chunk data.

    Returns:
        The chunk's bytes.
    """
    crc = zlib.crc32(kind + data) & 0xFFFFFFFF
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", crc)


def keyword_problem(name: str) -> str | None:
    """Return why ``name`` is not a valid PNG keyword, or None when it is (DR-31 (1)).

    The rule: 1 to 79 bytes of Latin-1, each in 32 to 126 or 161 to 255 (no control
    characters), no leading, trailing or consecutive spaces.

    Args:
        name: The proposed keyword or profile name.

    Returns:
        A short reason, or None.
    """
    try:
        raw = name.encode("latin-1")
    except UnicodeEncodeError:
        return "is not Latin-1"
    if not 1 <= len(raw) <= 79:
        return "must be 1 to 79 bytes"
    if any(not (32 <= b <= 126 or 161 <= b <= 255) for b in raw):
        return "contains a control character"
    if raw.startswith(b" ") or raw.endswith(b" "):
        return "has a leading or trailing space"
    if b"  " in raw:
        return "has consecutive spaces"
    return None


def check_keyword(name: str) -> None:
    """Raise ``ValueError`` when ``name`` breaks the PNG keyword rule.

    Args:
        name: The proposed keyword or profile name.

    Raises:
        ValueError: With the rule that failed.
    """
    problem = keyword_problem(name)
    if problem is not None:
        raise ValueError(f"PNG keyword {name!r} {problem}")


def profile_name(icc: bytes) -> str:
    """Choose the ``iCCP`` profile name: the profile's own description if valid, else a default.

    Args:
        icc: The profile bytes.

    Returns:
        A name that satisfies :func:`check_keyword`.
    """
    text = description(icc)
    if text is not None and keyword_problem(text) is None:
        return text
    return _DEFAULT_PROFILE_NAME


def itxt_chunk(keyword: str, text: str) -> bytes:
    """Encode an uncompressed UTF-8 ``iTXt`` chunk with no language tag.

    Args:
        keyword: The keyword (must satisfy :func:`check_keyword`).
        text: The text.

    Returns:
        The chunk's bytes.
    """
    check_keyword(keyword)
    body = keyword.encode("latin-1") + b"\0\0\0\0\0" + text.encode("utf-8")
    return chunk(b"iTXt", body)


def _quantise(block: NDArray[np.float32], bit_depth: int) -> NDArray[Any]:
    """Quantise float [0, 1] samples: clip, then round half to even (no dithering)."""
    top = (1 << bit_depth) - 1
    scaled = np.rint(np.clip(block, 0.0, 1.0).astype(np.float64) * top)
    if bit_depth == 16:
        return scaled.astype(">u2")
    return scaled.astype(np.uint8)


def write_png(
    out_path: Path,
    pixels: NDArray[np.float32],
    *,
    bit_depth: int,
    icc: bytes | None,
    exif: bytes | None,
    provenance_json: str | None,
) -> None:
    r"""Write an RGB PNG of 8 or 16 bits per channel; the only quantisation in the photo path.

    Samples are clipped to [0, 1], scaled by ``2**depth - 1`` and rounded half to even; 16-bit
    samples are big-endian. Rows are quantised, framed (filter 0) and deflated in blocks, so the
    memory beside the image stays small. The file is opened ``"wb"`` and closed before return;
    nothing else is written.

    Args:
        out_path: The output file.
        pixels: A float32 ``(H, W, 3)`` array.
        bit_depth: 8 or 16.
        icc: The profile to embed byte-identical, or None for no ``iCCP``.
        exif: The EXIF TIFF block (no ``Exif\0\0`` prefix), or None for no ``eXIf``.
        provenance_json: The provenance text for the ``iTXt`` chunk, or None for none.

    Raises:
        ValueError: ``bit_depth`` is not 8 or 16, ``pixels`` is not a float32 ``(H, W, 3)``
            array, a sample is NaN or infinite, or the suffix is not ``.png``.
    """
    if bit_depth not in (8, 16):
        raise ValueError(f"PNG bit depth must be 8 or 16, got {bit_depth}")
    if pixels.dtype != np.float32 or pixels.ndim != 3 or pixels.shape[2] != 3:
        raise ValueError(f"need float32 (H, W, 3) pixels, got {pixels.dtype} {pixels.shape}")
    if out_path.suffix.lower() != ".png":
        raise ValueError(f"output file {out_path.name} must end in .png")
    height, width = pixels.shape[:2]
    if height < 1 or width < 1:
        raise ValueError("an empty image cannot be written")
    for start in range(0, height, _BLOCK_ROWS):
        if not np.isfinite(pixels[start : start + _BLOCK_ROWS]).all():
            raise ValueError("the image contains NaN or infinite samples")
    head = [
        SIGNATURE,
        chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, bit_depth, 2, 0, 0, 0)),
    ]
    if icc is not None:
        head.append(
            chunk(b"iCCP", profile_name(icc).encode("latin-1") + b"\0\0" + zlib.compress(icc))
        )
    if exif is not None:
        head.append(chunk(b"eXIf", exif))
    if provenance_json is not None:
        head.append(itxt_chunk(PROVENANCE_KEYWORD, provenance_json))
    bytes_per_row = width * 3 * (bit_depth // 8)
    compressor = zlib.compressobj(_COMPRESSION_LEVEL)
    with out_path.open("wb") as handle:
        handle.write(b"".join(head))
        pending = bytearray()

        def flush(final: bool) -> None:
            while len(pending) >= _IDAT_SIZE or (final and pending):
                handle.write(chunk(b"IDAT", bytes(pending[:_IDAT_SIZE])))
                del pending[:_IDAT_SIZE]

        for start in range(0, height, _BLOCK_ROWS):
            block = pixels[start : start + _BLOCK_ROWS]
            rows = np.zeros((block.shape[0], 1 + bytes_per_row), dtype=np.uint8)
            quantised = _quantise(block, bit_depth)
            rows[:, 1:] = quantised.view(np.uint8).reshape(block.shape[0], bytes_per_row)
            pending += compressor.compress(rows.tobytes())
            flush(False)
        pending += compressor.flush()
        flush(True)
        handle.write(chunk(b"IEND", b""))


@dataclass(frozen=True)
class PngScan:
    """The header and the colour/EXIF chunks of a PNG, every chunk CRC-checked.

    Attributes:
        width: Image width.
        height: Image height.
        bit_depth: Bits per sample.
        color_type: PNG colour type (0 grey, 2 RGB, 3 palette, 4 grey+alpha, 6 RGBA).
        interlace: 0 (none) or 1 (Adam7).
        icc: The inflated ``iCCP`` profile, or None.
        exif: The ``eXIf`` chunk data (a TIFF block), or None.
        srgb: True when an ``sRGB`` chunk is present.
        idat: The concatenated ``IDAT`` data.
    """

    width: int
    height: int
    bit_depth: int
    color_type: int
    interlace: int
    icc: bytes | None
    exif: bytes | None
    srgb: bool
    idat: bytes


def scan_png(data: bytes, name: str) -> PngScan:
    """Walk a PNG, checking the signature, every chunk's CRC and the closing ``IEND``.

    Args:
        data: The file's bytes.
        name: The file name for messages.

    Returns:
        The scan.

    Raises:
        PhotoReadError: ``"unreadable"`` when the signature, a CRC, the chunk layout or the
            ``IHDR`` is wrong, or ``IEND`` is missing (a truncated file).
    """

    def bad(why: str) -> PhotoReadError:
        return PhotoReadError("unreadable", f"{name} cannot be read: PNG {why}.")

    if data[:8] != SIGNATURE:
        raise bad("signature is wrong")
    at = 8
    header: tuple[int, ...] | None = None
    icc: bytes | None = None
    exif: bytes | None = None
    srgb = False
    idat = bytearray()
    ended = False
    while at + 12 <= len(data):
        (size,) = struct.unpack(">I", data[at : at + 4])
        kind = data[at + 4 : at + 8]
        body = data[at + 8 : at + 8 + size]
        end = at + 12 + size
        if len(body) < size or end > len(data):
            raise bad("is truncated")
        (crc,) = struct.unpack(">I", data[end - 4 : end])
        if zlib.crc32(kind + body) & 0xFFFFFFFF != crc:
            raise bad(f"chunk {kind.decode('latin-1')} has a bad checksum")
        if kind == b"IHDR":
            if size != 13 or header is not None:
                raise bad("header is malformed")
            header = struct.unpack(">IIBBBBB", body)
        elif header is None:
            raise bad("has no header first")
        elif kind == b"IDAT":
            idat += body
        elif kind == b"iCCP" and icc is None:
            separator = body.find(b"\0")
            if separator > 0 and body[separator + 1 : separator + 2] == b"\0":
                try:
                    icc = zlib.decompress(body[separator + 2 :])
                except zlib.error:
                    icc = None
        elif kind == b"eXIf" and exif is None:
            exif = body
        elif kind == b"sRGB":
            srgb = True
        at = end
        if kind == b"IEND":
            ended = True
            break
    if header is None or not ended:
        raise bad("is truncated")
    width, height, depth, color_type, _, _, interlace = header
    if width < 1 or height < 1:
        raise bad("has no pixels")
    return PngScan(width, height, depth, color_type, interlace, icc, exif, srgb, bytes(idat))


def _unfilter_wavefront(
    filtered: NDArray[np.uint8], types: NDArray[np.uint8], bpp: int
) -> NDArray[np.uint8]:
    """Undo PNG filters 0 to 4 along anti-diagonals (pixels with equal x + y are independent).

    Args:
        filtered: ``(H, W, bpp)`` filtered bytes.
        types: ``(H,)`` filter type of each row.
        bpp: Bytes per pixel.

    Returns:
        ``(H, W, bpp)`` reconstructed bytes.
    """
    height, width = filtered.shape[:2]
    padded = np.zeros((height + 1, width + 1, bpp), dtype=np.uint8)
    present = {int(t) for t in np.unique(types)}
    for d in range(height + width - 1):
        xs = np.arange(max(0, d - height + 1), min(d, width - 1) + 1)
        ys = d - xs
        out = filtered[ys, xs].astype(np.int16)
        row_types = types[ys][:, None]
        left = padded[ys + 1, xs].astype(np.int16)
        up = padded[ys, xs + 1].astype(np.int16)
        pred = np.zeros_like(out)
        if 1 in present:
            pred = np.where(row_types == 1, left, pred)
        if 2 in present:
            pred = np.where(row_types == 2, up, pred)
        if 3 in present:
            pred = np.where(row_types == 3, (left + up) // 2, pred)
        if 4 in present:
            corner = padded[ys, xs].astype(np.int16)
            estimate = left + up - corner
            da, db, dc = abs(estimate - left), abs(estimate - up), abs(estimate - corner)
            paeth = np.where((da <= db) & (da <= dc), left, np.where(db <= dc, up, corner))
            pred = np.where(row_types == 4, paeth, pred)
        padded[ys + 1, xs + 1] = ((out + pred) & 255).astype(np.uint8)
    return padded[1:, 1:]


def _unfilter(rows: NDArray[np.uint8], width: int, bpp: int) -> NDArray[np.uint8]:
    """Undo the row filters of ``(H, 1 + W * bpp)`` scanlines; return ``(H, W, bpp)`` bytes."""
    types = rows[:, 0]
    filtered = rows[:, 1:].reshape(rows.shape[0], width, bpp)
    if not types.any():
        return filtered
    if (types > 2).any():
        return _unfilter_wavefront(filtered, types, bpp)
    out = filtered.copy()
    for y in range(out.shape[0]):
        if types[y] == 1:
            np.cumsum(out[y], axis=0, dtype=np.uint8, out=out[y])
        elif types[y] == 2 and y > 0:
            out[y] += out[y - 1]
    return out


def read_png16(scan: PngScan, name: str) -> NDArray[np.uint16]:
    """Decode a non-interlaced 16-bit PNG to ``uint16`` RGB samples, at full precision.

    Colour types 2 and 6 give RGB (alpha dropped); 0 and 4 are expanded to RGB.

    Args:
        scan: The scan of the file (:func:`scan_png`).
        name: The file name for messages.

    Returns:
        A ``(H, W, 3)`` ``uint16`` array.

    Raises:
        PhotoReadError: ``"unsupported"`` for an interlaced file, a palette image or another
            colour type; ``"unreadable"`` when the data is corrupt or short.
    """
    if scan.interlace != 0:
        raise PhotoReadError(
            "unsupported",
            f"{name} is not supported: interlaced (Adam7) 16-bit PNG files are not read; "
            "save it without interlacing.",
        )
    channels = _CHANNELS.get(scan.color_type)
    if scan.bit_depth != 16 or channels is None:
        raise PhotoReadError(
            "unsupported", f"{name} is not supported: 16-bit PNG colour type {scan.color_type}."
        )
    width, height, bpp = scan.width, scan.height, 2 * channels
    expected = height * (1 + width * bpp)
    inflater = zlib.decompressobj()
    try:
        raw = inflater.decompress(scan.idat, expected + 1)
    except zlib.error as error:
        raise PhotoReadError(
            "unreadable", f"{name} cannot be read: PNG pixel data is corrupt ({error})."
        ) from error
    if len(raw) != expected or inflater.unconsumed_tail or not inflater.eof:
        raise PhotoReadError(
            "unreadable", f"{name} cannot be read: PNG pixel data is the wrong length."
        )
    rows = np.frombuffer(raw, dtype=np.uint8).reshape(height, 1 + width * bpp)
    if (rows[:, 0] > 4).any():
        raise PhotoReadError("unreadable", f"{name} cannot be read: PNG has a bad row filter.")
    samples = _unfilter(rows, width, bpp).view(">u2").reshape(height, width, channels)
    if channels in (1, 2):
        samples = np.repeat(samples[:, :, :1], 3, axis=2)
    return np.ascontiguousarray(samples[:, :, :3].astype(np.uint16))
