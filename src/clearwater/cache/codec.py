"""Proxy codecs: how one 8-bit proxy becomes the bytes of a pack record (AD-5).

Every record carries the id of the codec that wrote it, so the container does not depend on
the store form chosen by the AD-5 measured test. The lossless ``deflate`` codec filters the rows
(PNG-style Sub or Up, whichever is smaller) and compresses them with zlib; it reproduces the
proxy bit for bit.
"""

from __future__ import annotations

import struct
import zlib
from collections.abc import Callable
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray

Proxy = NDArray[np.uint8]


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
    """

    codec_id: int
    name: str
    lossless: bool
    encode: Callable[[Proxy], bytes]
    decode: Callable[[bytes], Proxy]
    shape: Callable[[bytes], tuple[int, int, int]]


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

CODECS: dict[int, ProxyCodec] = {DEFLATE.codec_id: DEFLATE}
"""Every codec a pack may contain, by id. A record naming another id is treated as damaged."""

DEFAULT_CODEC = DEFLATE
"""The codec new records are written with unless the store is given another."""
