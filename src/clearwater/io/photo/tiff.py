"""TIFF input at every bit depth, through ``tifffile`` (WP3.6; AD-17 amended 2026-10-20).

Pillow reads a 16-bit RGB TIFF at 8 bits, so it is never used for TIFF pixels. ``tifffile`` decodes
uncompressed, Deflate, PackBits and LZMA data (striped or tiled, chunky or planar, with or without
the horizontal predictor) without further packages. Any other compression (LZW, JPEG, Zstandard,
...) is refused by name: ``imagecodecs`` is not a dependency and no TIFF decoder is hand-written.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import Any

import numpy as np
import tifffile
from numpy.typing import NDArray

from clearwater.io.photo.errors import PhotoReadError

_log = logging.getLogger(__name__)

_ORIENTATION_TAG = 274
_ICC_TAG = 34675

_DECODED = {
    int(tifffile.COMPRESSION.NONE): "uncompressed",
    int(tifffile.COMPRESSION.ADOBE_DEFLATE): "Deflate",
    int(tifffile.COMPRESSION.DEFLATE): "Deflate",
    int(tifffile.COMPRESSION.PACKBITS): "PackBits",
    int(tifffile.COMPRESSION.LZMA): "LZMA",
}


@dataclass(frozen=True)
class TiffPicture:
    """A decoded TIFF page.

    Attributes:
        samples: ``(H, W, 3)`` ``uint8`` or ``uint16`` RGB samples at the file's own depth.
        bit_depth: 8 or 16.
        icc: The embedded ICC profile bytes (tag 34675), or None.
        orientation_tag: The IFD0 Orientation as stored (None when absent).
        pages: How many pages the file has (only the first is read).
    """

    samples: NDArray[Any]
    bit_depth: int
    icc: bytes | None
    orientation_tag: int | None
    pages: int


def _refuse(name: str, why: str) -> PhotoReadError:
    return PhotoReadError("unsupported", f"{name} is not supported: {why}.")


def read_tiff(data: bytes, name: str, max_pixels: int) -> TiffPicture:
    """Decode the first page of a TIFF to RGB samples at the file's own bit depth.

    Grey pages (WhiteIsZero ones are inverted) and palette pages are expanded to RGB and an
    alpha channel is dropped (a warning is logged); a palette's 16-bit colour map is reduced to
    8 bits.

    Args:
        data: The file's bytes.
        name: The file name for messages.
        max_pixels: The largest pixel count that is decoded.

    Returns:
        The decoded page.

    Raises:
        PhotoReadError: ``"unsupported"`` for a compression that is not decoded, CMYK, float,
            YCbCr, other bit depths or too many pixels; ``"unreadable"`` for a file that is not a
            TIFF or whose data is truncated or corrupt.
    """
    try:
        with tifffile.TiffFile(io.BytesIO(data)) as tif:
            page = tif.pages[0]
            pages = len(tif.pages)
            if not isinstance(page, tifffile.TiffPage):
                raise _refuse(name, "the first TIFF page is not an image")
            compression = int(page.compression)
            if compression not in _DECODED:
                label = getattr(page.compression, "name", str(compression))
                raise _refuse(
                    name,
                    f"TIFF compression {label} is not read; save the TIFF uncompressed or "
                    "with Deflate",
                )
            if page.imagewidth * page.imagelength > max_pixels:
                raise _refuse(name, "the image has too many pixels")
            photometric = page.photometric
            dtype = page.dtype
            if dtype not in (np.dtype(np.uint8), np.dtype(np.uint16)):
                raise _refuse(name, f"TIFF samples of type {dtype} are not read")
            kinds = tifffile.PHOTOMETRIC
            if photometric not in (kinds.RGB, kinds.MINISBLACK, kinds.MINISWHITE, kinds.PALETTE):
                raise _refuse(name, f"TIFF colour space {getattr(photometric, 'name', '?')}")
            if page.bitspersample not in (8, 16) and photometric != kinds.PALETTE:
                raise _refuse(name, f"TIFF samples of {page.bitspersample} bits are not read")
            array = page.asarray()
            if photometric == kinds.MINISWHITE:  # WhiteIsZero: stored inverted
                array = np.iinfo(array.dtype).max - array
            if page.axes.startswith("S") and array.ndim == 3:
                array = np.moveaxis(array, 0, -1)
            colormap = page.colormap if photometric == kinds.PALETTE else None
            orientation = page.tags.get(_ORIENTATION_TAG)
            profile = page.tags.get(_ICC_TAG)
            icc = bytes(profile.value) if profile is not None else None
            orientation_tag = int(orientation.value) if orientation is not None else None
    except PhotoReadError:
        raise
    except Exception as error:  # tifffile raises ValueError, TiffFileError, struct.error, ...
        raise PhotoReadError(
            "unreadable", f"{name} cannot be read: the TIFF is damaged or truncated ({error})."
        ) from error
    if pages > 1:
        _log.warning("%s has %d pages; only the first is read", name, pages)
    if colormap is not None:
        table = np.asarray(colormap, dtype=np.uint16)
        array = (table[:, array.astype(np.intp)] >> 8).astype(np.uint8).transpose(1, 2, 0)
        return TiffPicture(np.ascontiguousarray(array), 8, icc, orientation_tag, pages)
    if array.ndim == 2:
        array = np.repeat(array[:, :, None], 3, axis=2)
    elif array.shape[2] == 2:
        _log.warning("%s has an alpha channel; it is dropped", name)
        array = np.repeat(array[:, :, :1], 3, axis=2)
    elif array.shape[2] == 4:
        _log.warning("%s has an alpha channel; it is dropped", name)
        array = array[:, :, :3]
    elif array.shape[2] != 3:
        raise _refuse(name, f"TIFF with {array.shape[2]} samples per pixel")
    return TiffPicture(
        np.ascontiguousarray(array),
        16 if array.dtype == np.uint16 else 8,
        icc,
        orientation_tag,
        pages,
    )
