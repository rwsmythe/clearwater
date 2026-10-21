"""Proxy codecs: how one 8-bit proxy becomes the bytes of a pack record (AD-5).

Every record carries the id of the codec that wrote it, so the container does not depend on
the store form. The default is JPEG (AD-5 as ruled 2026-10-20, from the WP3.12 measured test):
quality 75 with 4:4:4 sampling, or quality 80 with 4:2:0; the stored, decoded proxy IS the
analysis proxy, so statistics are measured from it on the first pass and on reopen alike. A
JPEG decode depends on the library that does it, so each JPEG codec has an ``identity`` (Pillow
and libjpeg versions, read at runtime) that :mod:`clearwater.cache.keys` folds into the cache
version: a changed decoder invalidates the cache. The lossless ``deflate`` codec filters the rows
(PNG-style Sub or Up, whichever is smaller) and compresses them with zlib; it reproduces the
proxy bit for bit. Pillow is imported only when a JPEG codec runs.
"""

from __future__ import annotations

import io
import struct
import zlib
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Proxy = NDArray[np.uint8]


def _no_identity() -> str:
    """Return the identity of a codec that depends on nothing outside itself."""
    return ""


@dataclass(frozen=True)
class ProxyCodec:
    """One way of storing a proxy.

    Attributes:
        codec_id: The id written into every record (1 to 255, never reused).
        name: A short name for logs.
        lossless: Whether :attr:`decode` returns exactly what :attr:`encode` was given.
        encode: Turns a ``(H, W, 3)`` uint8 proxy into bytes.
        decode: Turns those bytes back into the proxy.
        shape: Reads ``(H, W, 3)`` from the first :data:`SHAPE_PREFIX_BYTES` bytes of a blob.
        identity: Returns what the codec's output and decoding depend on besides its settings
            (empty for a codec that depends on nothing); read at runtime, folded into the cache
            version.
    """

    codec_id: int
    name: str
    lossless: bool
    encode: Callable[[Proxy], bytes]
    decode: Callable[[bytes], Proxy]
    shape: Callable[[bytes], tuple[int, int, int]]
    identity: Callable[[], str] = _no_identity


SHAPE_PREFIX_BYTES = 16
"""How many leading bytes of a blob :attr:`ProxyCodec.shape` may be given."""

_HEAD = struct.Struct("<BII")
_MODES = ("sub", "up")
_LEVEL = 1


def _filter(rows: Proxy, mode: str) -> bytes:
    """Return the filtered bytes of a proxy: each sample minus its left or upper neighbour."""
    flat = rows.reshape(rows.shape[0], -1)
    out = flat.copy()
    if mode == "sub":
        out[:, 3:] = flat[:, 3:] - flat[:, :-3]
    else:
        out[1:] = flat[1:] - flat[:-1]
    return out.tobytes()


def _unfilter(data: bytes, mode: str, shape: tuple[int, int, int]) -> Proxy:
    """Invert :func:`_filter`: a wrapped cumulative sum along the filter direction."""
    rows = np.frombuffer(data, dtype=np.uint8)
    if rows.size != shape[0] * shape[1] * shape[2]:
        raise ValueError("a deflate proxy has the wrong number of samples")
    cube = rows.reshape(shape)
    out = np.cumsum(cube, axis=1 if mode == "sub" else 0, dtype=np.uint8)
    return np.ascontiguousarray(out)


def _deflate_encode(proxy: Proxy) -> bytes:
    """Encode with the smaller of Sub and Up filtering at zlib level 1."""
    best: tuple[int, bytes] | None = None
    for number, mode in enumerate(_MODES):
        blob = zlib.compress(_filter(proxy, mode), _LEVEL)
        if best is None or len(blob) < len(best[1]):
            best = (number, blob)
    assert best is not None
    height, width = proxy.shape[0], proxy.shape[1]
    return _HEAD.pack(best[0], height, width) + best[1]


def _deflate_shape(prefix: bytes) -> tuple[int, int, int]:
    """Read ``(H, W, 3)`` from the head of a deflate blob."""
    if len(prefix) < _HEAD.size:
        raise ValueError("a deflate proxy is shorter than its header")
    _, height, width = _HEAD.unpack_from(prefix)
    return int(height), int(width), 3


def _deflate_decode(blob: bytes) -> Proxy:
    """Decode a deflate blob."""
    shape = _deflate_shape(blob[: _HEAD.size])
    mode_number = blob[0]
    if mode_number >= len(_MODES):
        raise ValueError("a deflate proxy names an unknown filter")
    return _unfilter(zlib.decompress(blob[_HEAD.size :]), _MODES[mode_number], shape)


DEFLATE = ProxyCodec(1, "deflate", True, _deflate_encode, _deflate_decode, _deflate_shape)
"""The lossless codec: row filter plus zlib, stdlib only."""

_JPEG_HEAD = struct.Struct("<II")
_MAXBLOCK = 1 << 26


def jpeg_identity() -> str:
    """Return the JPEG library identity: Pillow, libjpeg and libjpeg-turbo versions.

    Read at runtime each time it is asked, so that a different decoder changes the cache version.

    Returns:
        A string such as ``"pillow=12.3.0;libjpeg=8.0;turbo=3.1.4.1"``.
    """
    import PIL
    from PIL import features

    jpg = features.version("jpg")
    turbo = features.version("libjpeg_turbo")
    return f"pillow={PIL.__version__};libjpeg={jpg};turbo={turbo}"


def _jpeg_identity() -> str:
    """Return :func:`jpeg_identity`, looked up at call time (so a test can replace it)."""
    return jpeg_identity()


def _jpeg_encoder(quality: int, subsampling: int) -> Callable[[Proxy], bytes]:
    """Return an encoder: ``<II`` height and width, then a baseline JPEG with optimised Huffman."""

    def encode(proxy: Proxy) -> bytes:
        from PIL import Image, ImageFile

        if ImageFile.MAXBLOCK < _MAXBLOCK:
            # optimize=True needs the whole scan in one buffer; only ever raised, never lowered
            ImageFile.MAXBLOCK = _MAXBLOCK
        buffer = io.BytesIO()
        Image.fromarray(proxy).save(
            buffer, "JPEG", quality=quality, subsampling=subsampling, optimize=True
        )
        return _JPEG_HEAD.pack(proxy.shape[0], proxy.shape[1]) + buffer.getvalue()

    return encode


def _jpeg_shape(prefix: bytes) -> tuple[int, int, int]:
    """Read ``(H, W, 3)`` from the head of a JPEG blob."""
    if len(prefix) < _JPEG_HEAD.size:
        raise ValueError("a JPEG proxy is shorter than its header")
    height, width = _JPEG_HEAD.unpack_from(prefix)
    return int(height), int(width), 3


def _jpeg_decode(blob: bytes) -> Proxy:
    """Decode a JPEG blob to a new RGB array and check it against the stored size."""
    from PIL import Image

    shape = _jpeg_shape(blob[: _JPEG_HEAD.size])
    with Image.open(io.BytesIO(blob[_JPEG_HEAD.size :])) as image:
        decoded = np.array(image.convert("RGB"), dtype=np.uint8)
    if decoded.shape != shape:
        raise ValueError("a JPEG proxy decodes to the wrong size")
    return decoded


JPEG_Q75_444 = ProxyCodec(
    2, "jpeg-q75-444", False, _jpeg_encoder(75, 0), _jpeg_decode, _jpeg_shape, _jpeg_identity
)
"""The default: JPEG quality 75, 4:4:4 (WP3.12 measured test: about 9.0 GB per 60 minutes)."""

JPEG_Q80_420 = ProxyCodec(
    3, "jpeg-q80-420", False, _jpeg_encoder(80, 2), _jpeg_decode, _jpeg_shape, _jpeg_identity
)
"""JPEG quality 80, 4:2:0: the alternative if its read cost justifies it."""

CODECS: dict[int, ProxyCodec] = {c.codec_id: c for c in (DEFLATE, JPEG_Q75_444, JPEG_Q80_420)}
"""Every codec a pack may contain, by id. A record naming another id is treated as damaged."""

DEFAULT_CODEC = JPEG_Q75_444
"""The codec new records are written with unless the store is given another."""


def round_trip(proxy: Proxy, codec: ProxyCodec = DEFAULT_CODEC) -> Proxy:
    """Return the proxy as the cache would give it back: encoded, then decoded (AD-5 ruling).

    At the first analysis the proxy must go through this BEFORE any statistic is measured, so
    that the first pass and a reopen measure the same pixels; the float proxy is never a
    statistics source.

    Args:
        proxy: The 8-bit proxy, ``(H, W, 3)``.
        codec: The store codec.

    Returns:
        A new array; equal to ``proxy`` for a lossless codec.
    """
    return codec.decode(codec.encode(np.ascontiguousarray(proxy)))
