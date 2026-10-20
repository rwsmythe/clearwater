"""Image operations of the correction core beyond IF-2, as plain functions on a backend.

These are the plan's WP3.1 operations that IF-2 does not carry (WP3.1 ruling 1, round-0 ruling
R0-2): the D56 fraction-to-pixels conversion, the pyramid depth (spec 6.6), Gaussian and
Laplacian pyramids, the luma, Lab and Laplacian that the fusion weights need, and whole-frame
means. Each mirrors the ``tools/prototype/pipeline`` function named in its docstring with the
same calls, so each matches the prototype bit for bit on the same device.

Every function takes the backend the arrays live on; it must be a :class:`CoreBackend`
(``select_backend`` returns one). Arrays stay on that backend's device. The functions that
return Python floats (:func:`channel_means`, :func:`mean`) read a few scalars back to the host:
each is a device-to-host SYNC POINT, to be counted by the device-resident work (WP3.21).
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence

import numpy as np

from clearwater.interfaces.backend import ArrayBackend
from clearwater.interfaces.image import Array

from .backend import CoreBackend, rgb_to_ycbcr_matrix

# IEC 61966-2-1:1999 (sRGB), linear RGB -> CIE XYZ, D65 white.
_SRGB_TO_XYZ = np.array(
    [
        [0.4124, 0.3576, 0.1805],
        [0.2126, 0.7152, 0.0722],
        [0.0193, 0.1192, 0.9505],
    ],
    dtype=np.float32,
)
# CIE D65 reference white (CIE 15:2004), Y normalised to 1.
_D65_WHITE = np.array([0.95047, 1.0, 1.08883], dtype=np.float32)
_LAB_DELTA = 6.0 / 29.0
_LUMA_709 = rgb_to_ycbcr_matrix("bt709")[0].astype(np.float32)


def _core(backend: ArrayBackend) -> CoreBackend:
    """Return ``backend`` as a :class:`CoreBackend`, or raise TypeError."""
    if not isinstance(backend, CoreBackend):
        raise TypeError(f"expected a clearwater.core backend, got {type(backend).__name__}")
    return backend


def spatial_sigma(shape: tuple[int, ...], fraction: float) -> float:
    """Turn a spatial parameter given as a fraction of the short side into pixels (D56).

    Mirrors ``pipeline.spatial_sigma``: no floor; a sigma under 1/8 px gives the kernel ``[1]``.

    Args:
        shape: The array shape; the first two entries are height and width.
        fraction: The parameter as a fraction of ``min(height, width)``.

    Returns:
        The parameter in pixels.
    """
    return fraction * min(shape[0], shape[1])


def pyramid_levels(shape: tuple[int, ...], min_level_size: int) -> int:
    """Return the pyramid depth: halve while the short side stays at least ``min_level_size``.

    Mirrors ``pipeline.pyramid_levels`` (spec 6.6): each level halves the short side, rounding
    up; a level is added only while the halved short side is still at least
    ``min_level_size``, so the coarsest level is never smaller than that (or is the image).

    Args:
        shape: The array shape; the first two entries are height and width.
        min_level_size: The minimum short side of the coarsest level, in pixels, at least 1.

    Returns:
        The number of levels, at least 1.

    Raises:
        ValueError: ``min_level_size`` is under 1.
    """
    if min_level_size < 1:
        raise ValueError(f"min_level_size must be at least 1, got {min_level_size}")
    size = min(shape[0], shape[1])
    levels = 1
    while math.ceil(size / 2) >= min_level_size and size > 1:
        size = math.ceil(size / 2)
        levels += 1
    return levels


def gaussian_pyramid(backend: ArrayBackend, a: Array, levels: int) -> list[Array]:
    """Build a Gaussian pyramid of ``levels`` levels, finest first (level 0 is ``a``).

    Mirrors ``pipeline.gaussian_pyramid`` through :meth:`CoreBackend.pyramid_reduce`.

    Args:
        backend: The backend ``a`` lives on.
        a: An ``(H, W)`` map or ``(H, W, C)`` image, float32.
        levels: The number of levels, at least 1.

    Returns:
        The levels.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``levels`` is under 1, or ``a`` is not float32 or has the wrong shape.
    """
    core = _core(backend)
    if levels < 1:
        raise ValueError(f"levels must be at least 1, got {levels}")
    core.check_spatial(a)
    pyramid = [a]
    for _ in range(levels - 1):
        pyramid.append(core.pyramid_reduce(pyramid[-1]))
    return pyramid


def laplacian_pyramid(backend: ArrayBackend, a: Array, levels: int) -> list[Array]:
    """Build a Laplacian pyramid: ``L_l = G_l - EXPAND(G_{l+1})``, the last level ``G_top``.

    Mirrors ``pipeline.laplacian_pyramid``; :func:`collapse_pyramid` inverts it up to float
    round-off.

    Args:
        backend: The backend ``a`` lives on.
        a: An ``(H, W)`` map or ``(H, W, C)`` image, float32.
        levels: The number of levels, at least 1.

    Returns:
        The band-pass levels, finest first, ending with the coarsest Gaussian level.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``levels`` is under 1, or ``a`` is not float32 or has the wrong shape.
    """
    core = _core(backend)
    gaussian = gaussian_pyramid(core, a, levels)
    bands = [
        fine - core.pyramid_expand(coarse, (fine.shape[0], fine.shape[1]))
        for fine, coarse in itertools.pairwise(gaussian)
    ]
    bands.append(gaussian[-1])
    return bands


def collapse_pyramid(backend: ArrayBackend, pyramid: Sequence[Array]) -> Array:
    """Collapse a Laplacian pyramid: from the coarsest level, ``G_l = L_l + EXPAND(G_{l+1})``.

    Mirrors ``pipeline.collapse_pyramid``.

    Args:
        backend: The backend the levels live on.
        pyramid: The levels, finest first, at least one.

    Returns:
        The reconstructed full-size array.

    Raises:
        TypeError: ``backend`` is not a core backend or a level is not one of its arrays.
        ValueError: ``pyramid`` is empty, or a level is not float32 or does not fit.
    """
    core = _core(backend)
    if not pyramid:
        raise ValueError("collapse_pyramid needs at least one level")
    image = pyramid[-1]
    core.check(image)
    for band in reversed(pyramid[:-1]):
        image = band + core.pyramid_expand(image, (band.shape[0], band.shape[1]))
    return image


def luminance(backend: ArrayBackend, a: Array) -> Array:
    """Return the BT.709 luma ``Y = 0.2126 R + 0.7152 G + 0.0722 B`` (``pipeline.luminance``).

    Args:
        backend: The backend ``a`` lives on.
        a: RGB, float32, ``(H, W, 3)``.

    Returns:
        Y, float32, ``(H, W)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not float32 or has the wrong shape.
    """
    core = _core(backend)
    core.check_rgb(a)
    out: Array = core.xp.asarray(a @ core.constant("luma_709", _LUMA_709), dtype=np.float32)
    return out


def rgb_to_lab(backend: ArrayBackend, a: Array) -> Array:
    """Convert display-encoded RGB, read as sRGB, to CIELAB (D65) (``pipeline.srgb_to_lab``).

    The sRGB transfer function and matrix (IEC 61966-2-1:1999), then CIELAB with the D65
    white (CIE 15:2004); float32 throughout. It feeds the saliency weight only.

    Args:
        backend: The backend ``a`` lives on.
        a: RGB, float32, ``(H, W, 3)``, values in [0, 1].

    Returns:
        L*, a*, b* (L* in [0, 100]), float32, ``(H, W, 3)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not float32 or has the wrong shape.
    """
    core = _core(backend)
    core.check_rgb(a)
    xp = core.xp
    linear = xp.where(
        a <= 0.04045,
        a / np.float32(12.92),
        xp.power((a + np.float32(0.055)) / np.float32(1.055), np.float32(2.4)),
    )
    xyz = (linear @ core.constant("srgb_to_xyz_t", _SRGB_TO_XYZ.T)) / core.constant(
        "d65_white", _D65_WHITE
    )
    f = xp.where(
        xyz > _LAB_DELTA**3,
        xp.cbrt(xyz),
        xyz / np.float32(3.0 * _LAB_DELTA**2) + np.float32(4.0 / 29.0),
    )
    lab = xp.empty_like(f)
    lab[..., 0] = 116.0 * f[..., 1] - 16.0
    lab[..., 1] = 500.0 * (f[..., 0] - f[..., 1])
    lab[..., 2] = 200.0 * (f[..., 1] - f[..., 2])
    out: Array = lab.astype(np.float32, copy=False)
    return out


def laplacian(backend: ArrayBackend, a: Array) -> Array:
    """Return the discrete 5-point Laplacian of a map, symmetric borders (``ndimage.laplace``).

    Zero-sum, so a flat map gives exactly 0 (the prototype's W_L uses it on the smoothed luma).

    Args:
        backend: The backend ``a`` lives on.
        a: A float32 ``(H, W)`` map.

    Returns:
        The Laplacian, float32, ``(H, W)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not float32 or has the wrong shape.
    """
    core = _core(backend)
    core.check_spatial(a)
    if a.ndim != 2:
        raise ValueError(f"expected an (H, W) map, got shape {a.shape}")
    out: Array = core.xp.asarray(core.ndimage.laplace(a, mode="reflect"), dtype=np.float32)
    return out


def channel_means(backend: ArrayBackend, a: Array) -> tuple[float, float, float]:
    """Return the mean of each channel over the whole image, accumulated in float64.

    Mirrors ``pipeline._channel_means``. A device-to-host SYNC POINT: three scalars are read
    back to the host as Python floats.

    Args:
        backend: The backend ``a`` lives on.
        a: A float32 ``(H, W, 3)`` image.

    Returns:
        The three means.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not float32 or has the wrong shape.
    """
    core = _core(backend)
    core.check_rgb(a)
    means = a.reshape(-1, 3).mean(axis=0, dtype=np.float64).tolist()
    return float(means[0]), float(means[1]), float(means[2])


def mean(backend: ArrayBackend, a: Array) -> float:
    """Return the mean of every element, accumulated in float64 (``pipeline._cap_statistic``).

    A device-to-host SYNC POINT: one scalar is read back to the host as a Python float.

    Args:
        backend: The backend ``a`` lives on.
        a: A float32 array.

    Returns:
        The mean.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is empty or not float32.
    """
    core = _core(backend)
    core.check(a)
    if a.size == 0:
        raise ValueError("mean of an empty array")
    return float(a.mean(dtype=np.float64))
