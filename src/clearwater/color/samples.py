"""Planar integer samples to IF-1 float32 RGB and back (WP3.5, D39, spec 5.2).

FFmpeg delivers and takes full-range planar RGB (AD-10): ``gbrp`` (8-bit) or ``gbrp10le``
(10-bit, little-endian 16-bit words), planes in G, B, R order. This module converts one frame
between that layout and the IF-1 array (float32 ``(H, W, 3)`` RGB in [0, 1]). Quantisation
happens only on the way out (D39): the way in is an exact division by ``2**n - 1`` and 10-bit
data is never truncated. The functions run on host NumPy; the caller moves the array to the
device with the backend's ``asarray``.
"""

from __future__ import annotations

from collections.abc import Buffer

import numpy as np

from clearwater.color.swscale import ColorError, rgb_pix_fmt
from clearwater.interfaces.image import Array

_G, _B, _R = 0, 1, 2


def _dtype(bit_depth: int) -> np.dtype[np.uint8] | np.dtype[np.uint16]:
    """Return the sample dtype FFmpeg uses at a bit depth (little-endian words for 10-bit)."""
    rgb_pix_fmt(bit_depth)  # refuses anything but 8 and 10, by name
    return np.dtype(np.uint8) if bit_depth == 8 else np.dtype("<u2")


def rgb_frame_bytes(width: int, height: int, bit_depth: int) -> int:
    """Return the size in bytes of one planar RGB frame.

    Args:
        width: Frame width in pixels.
        height: Frame height in pixels.
        bit_depth: 8 or 10.

    Returns:
        ``3 * width * height`` samples of 1 byte (8-bit) or 2 bytes (10-bit).

    Raises:
        ColorError: The bit depth is neither 8 nor 10.
    """
    return 3 * width * height * _dtype(bit_depth).itemsize


def planes_to_rgb(data: Buffer, *, width: int, height: int, bit_depth: int) -> Array:
    """Convert one planar G, B, R frame to a float32 RGB array in [0, 1].

    Each sample is divided by ``2**bit_depth - 1``, so the integer codes are recovered exactly by
    :func:`rgb_to_planes`. The samples are trusted to be within the bit depth, as FFmpeg writes
    them.

    Args:
        data: The raw frame as FFmpeg's ``gbrp`` / ``gbrp10le`` writes it.
        width: Frame width in pixels.
        height: Frame height in pixels.
        bit_depth: 8 or 10.

    Returns:
        A new C-contiguous float32 array of shape ``(height, width, 3)``, channels R, G, B.

    Raises:
        ColorError: The bit depth is unsupported, or ``data`` is not exactly one frame.
    """
    dtype = _dtype(bit_depth)
    view = memoryview(data)
    expected = rgb_frame_bytes(width, height, bit_depth)
    if view.nbytes != expected:
        raise ColorError(
            f"a {width}x{height} {bit_depth}-bit frame is {expected} bytes, not {view.nbytes}"
        )
    planes = np.frombuffer(view, dtype=dtype).reshape(3, height, width)
    scale = np.float32(2**bit_depth - 1)
    rgb = np.empty((height, width, 3), dtype=np.float32)
    rgb[..., 0] = planes[_R] / scale
    rgb[..., 1] = planes[_G] / scale
    rgb[..., 2] = planes[_B] / scale
    return rgb


def rgb_to_planes(a: Array, *, bit_depth: int) -> bytes:
    """Quantise a float32 RGB array to one planar G, B, R frame (the only quantisation, D39).

    Values are clipped to [0, 1], scaled by ``2**bit_depth - 1`` and rounded half to even
    (``numpy.rint``).

    Args:
        a: A float32 ``(H, W, 3)`` RGB array on the host.
        bit_depth: 8 or 10.

    Returns:
        The frame as FFmpeg's ``gbrp`` (8-bit) or ``gbrp10le`` (10-bit) reads it.

    Raises:
        ColorError: The bit depth is unsupported, the array is not float32 ``(H, W, 3)``, or it
            holds a NaN.
    """
    dtype = _dtype(bit_depth)
    if a.dtype != np.float32 or a.ndim != 3 or a.shape[2] != 3:
        raise ColorError(f"expected a float32 (H, W, 3) array, got {a.dtype} {a.shape}")
    scaled = np.clip(a, np.float32(0), np.float32(1)) * np.float32(2**bit_depth - 1)
    if np.isnan(scaled.sum()):
        raise ColorError("the array holds a NaN; it cannot be quantised")
    height, width = a.shape[:2]
    planes = np.empty((3, height, width), dtype=dtype)
    planes[_G] = np.rint(scaled[..., 1])
    planes[_B] = np.rint(scaled[..., 2])
    planes[_R] = np.rint(scaled[..., 0])
    return planes.tobytes()
