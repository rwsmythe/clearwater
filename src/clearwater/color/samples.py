"""Planar integer samples to IF-1 float32 RGB and back (WP3.5, D39, spec 5.2).

FFmpeg delivers and takes full-range planar RGB (AD-10): ``gbrp`` (8-bit) or ``gbrp10le``
(10-bit, little-endian 16-bit words), planes in G, B, R order. This module converts one frame
between that layout and the IF-1 array (float32 ``(H, W, 3)`` RGB in [0, 1]). Quantisation
happens only on the way out (D39): the way in is an exact division by ``2**n - 1`` and 10-bit
data is never truncated. The functions run on host NumPy, or on the device with CuPy (WP3.21
#2): :func:`planes_to_rgb` uploads the integer planes and divides there when given CuPy as its
array module, and :func:`rgb_to_planes` quantises a device array where it lies and downloads
the planes. Both are the same IEEE float32 operations (one correctly rounded division; one
clip, multiply and round half to even), so the device gives the host's values bit for bit.
"""

from __future__ import annotations

import importlib
from collections.abc import Buffer
from typing import Any

import numpy as np

from clearwater.color.swscale import ColorError, rgb_pix_fmt
from clearwater.interfaces.image import Array

_G, _B, _R = 0, 1, 2


def _dtype(bit_depth: int) -> np.dtype[np.uint8] | np.dtype[np.uint16]:
    """Return the sample dtype FFmpeg uses at a bit depth (little-endian words for 10-bit)."""
    rgb_pix_fmt(bit_depth)  # refuses anything but 8 and 10, by name
    return np.dtype(np.uint8) if bit_depth == 8 else np.dtype("<u2")


def _array_module(a: Any) -> Any:
    """Return NumPy for a host array and CuPy for a device array (CuPy is loaded already then)."""
    if isinstance(a, np.ndarray) or not hasattr(a, "__cuda_array_interface__"):
        return np
    return importlib.import_module("cupy")


def rgb_frame_bytes(width: int, height: int, bit_depth: int) -> int:
    """Return the size in bytes of one planar RGB frame.

    Args:
        width: Frame width in pixels.
        height: Frame height in pixels.
        bit_depth: 8 or 10.

    Returns:
        ``3 * width * height`` samples of 1 byte (8-bit) or 2 bytes (10-bit).

    Raises:
        ColorError: The bit depth is neither 8 nor 10, or the size is not positive.
    """
    if width < 1 or height < 1:
        raise ColorError(f"a frame must be at least 1x1, not {width}x{height}")
    return 3 * width * height * _dtype(bit_depth).itemsize


def planes_to_rgb(data: Buffer, *, width: int, height: int, bit_depth: int, xp: Any = np) -> Array:
    """Convert one planar G, B, R frame to a float32 RGB array in [0, 1].

    Each sample is divided by ``2**bit_depth - 1``, so the integer codes are recovered exactly by
    :func:`rgb_to_planes`. The samples are trusted to be within the bit depth, as FFmpeg writes
    them.

    Args:
        data: The raw frame as FFmpeg's ``gbrp`` / ``gbrp10le`` writes it.
        width: Frame width in pixels.
        height: Frame height in pixels.
        bit_depth: 8 or 10.
        xp: The array module of the result: NumPy (the default), or CuPy to upload the integer
            planes (a third or two thirds of the float32 frame's bytes) and convert on the
            device. ``data`` may be reused once this returns: the upload has read it.

    Returns:
        A new C-contiguous float32 array of shape ``(height, width, 3)``, channels R, G, B, of
        the module ``xp``.

    Raises:
        ColorError: The bit depth or size is unsupported, or ``data`` is not exactly one
            contiguous frame.
    """
    dtype = _dtype(bit_depth)
    view = memoryview(data)
    if not view.c_contiguous:
        raise ColorError("the frame buffer must be contiguous")
    expected = rgb_frame_bytes(width, height, bit_depth)
    if view.nbytes != expected:
        raise ColorError(
            f"a {width}x{height} {bit_depth}-bit frame is {expected} bytes, not {view.nbytes}"
        )
    planes = np.frombuffer(view, dtype=dtype).reshape(3, height, width)
    if xp is not np:
        planes = xp.asarray(planes)  # from pageable memory: the buffer is free again on return
    scale = np.float32(2**bit_depth - 1)
    rgb: Array = xp.empty((height, width, 3), dtype=np.float32)
    rgb[..., 0] = planes[_R] / scale
    rgb[..., 1] = planes[_G] / scale
    rgb[..., 2] = planes[_B] / scale
    return rgb


def rgb_to_planes(a: Array, *, bit_depth: int) -> bytes:
    """Quantise a float32 RGB array to one planar G, B, R frame (the only quantisation, D39).

    Values are clipped to [0, 1], scaled by ``2**bit_depth - 1`` and rounded half to even
    (``numpy.rint``). A device (CuPy) array is quantised on the device and only its planes are
    downloaded; the bytes are the host's.

    Args:
        a: A float32 ``(H, W, 3)`` RGB array, on the host or on the device.
        bit_depth: 8 or 10.

    Returns:
        The frame as FFmpeg's ``gbrp`` (8-bit) or ``gbrp10le`` (10-bit) reads it.

    Raises:
        ColorError: The bit depth is unsupported, the array is not a non-empty float32
            ``(H, W, 3)``, or it holds a NaN.
    """
    dtype = _dtype(bit_depth)
    if a.dtype != np.float32 or a.ndim != 3 or a.shape[2] != 3 or a.size == 0:
        raise ColorError(f"expected a non-empty float32 (H, W, 3) array, got {a.dtype} {a.shape}")
    xp = _array_module(a)
    scaled = xp.clip(a, np.float32(0), np.float32(1)) * np.float32(2**bit_depth - 1)
    if bool(xp.isnan(scaled.sum())):
        raise ColorError("the array holds a NaN; it cannot be quantised")
    height, width = a.shape[:2]
    planes = xp.empty((3, height, width), dtype=dtype)
    planes[_G] = xp.rint(scaled[..., 1])
    planes[_B] = xp.rint(scaled[..., 2])
    planes[_R] = xp.rint(scaled[..., 0])
    if xp is not np:
        planes = xp.asnumpy(planes)  # synchronous: the download has completed on return
    return bytes(planes.tobytes())
