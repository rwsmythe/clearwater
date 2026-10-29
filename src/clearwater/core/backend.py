"""The two array backends of IF-2 and the device choice (AD-1, AD-9, D107, D111).

:class:`NumpyBackend` (CPU) and :class:`CupyBackend` (GPU) share one implementation,
:class:`CoreBackend`, which reaches its device only through two modules: ``xp`` (``numpy`` or
``cupy``) and ``ndimage`` (``scipy.ndimage`` or ``cupyx.scipy.ndimage``). So the same code runs
on either device (D107, N3). CuPy is imported only here and only when a :class:`CupyBackend` is
built or :func:`select_backend` probes the device, so ``import clearwater.core`` works without
it. ``CoreBackend.xp`` is for ``clearwater.core`` only (WP3.1 ruling 1.1).

IF-2 device extensions (AD-29, WP3.21): :class:`CupyBackend` also converts FFmpeg's planar
frames on the device (``planes_to_rgb``, ``rgb_to_planes``) and takes the analysis proxy's exact
block sums there (``block_sums``). They are NOT part of the frozen ABC; the GPU backend provides
them and the CPU backend does not, so a consumer that tests for its own package's Protocol takes
its host path on the CPU by structure.

Conventions (spec 6.4, D39; IF-1):

- Every image method takes and returns float32. A non-float32 input raises ValueError and an
  array of the other backend's kind raises TypeError: nothing is cast or moved silently.
  :meth:`CoreBackend.asarray` is the only way in and :meth:`CoreBackend.to_host` the only way
  out; on the GPU every result stays on the device (Gate 1, WP3.21).
- The filters (``gaussian_blur``, ``pyramid_reduce``, ``pyramid_expand``) accept an
  ``(H, W)`` map or an ``(H, W, C)`` image and filter the two spatial axes only.
- Borders are symmetric (``ndimage`` mode ``"reflect"``: ``d c b a | a b c d``). The Gaussian
  keeps a radius of ``int(4 * sigma + 0.5)`` pixels (SciPy's rule with ``truncate=4.0``; under
  1/8 px the kernel is exactly ``[1]``). SciPy accumulates in float64 and returns float32;
  cupyx accumulates in float32. CPU and GPU agree within AD-11, and each matches
  ``tools/prototype`` bit for bit on its own device, because the calls are the prototype's.
- The FFT Gaussian (WP3.21 task 6, CHARC Q-R1 / Q4): when :func:`fft_route` holds (the short
  side at least :data:`FFT_MIN_SHORT_SIDE` and sigma at least :data:`FFT_MIN_SIGMA`, the same
  rule on both backends), ``gaussian_blur`` convolves each spatial axis by a float32 real FFT
  (``scipy.fft`` / ``cupyx.scipy.fft``) with the SAME truncated kernel and the same ``reflect``
  padding, axis 0 then axis 1. Only the rounding differs from the direct filter (within 1e-5 on
  [0, 1] data); no analysis proxy reaches the route, because every proxy's short side is under
  1080. On the GPU the cuFFT plans stay cached per thread until
  :meth:`CupyBackend.release_fft_plans` (an export job's end).

YCbCr (``rgb_to_ycbcr``, ``ycbcr_to_rgb``): matrices ``bt709`` (K_R 0.2126, K_B 0.0722, ITU-R
BT.709-6) and ``bt601`` (K_R 0.299, K_B 0.114, ITU-R BT.601-7). In ``"full"`` range, Y spans
[0, 1] and Cb, Cr span [-0.5, 0.5] centred on 0 (the prototype's convention, D47). In
``"limited"`` range, the studio swing over 8-bit codes normalised by 255 (WP3.1 ruling R0-1),
with chroma still centred on 0: ``Y' = 16/255 + (219/255) Y``, ``Cb' = (224/255) Cb``,
``Cr' = (224/255) Cr``. ``ycbcr_to_rgb`` is the exact inverse in float64, cast to float32 once,
and does not clip. Any other matrix (``identity``, ``unknown``) or range raises ValueError.
Video colour conversion is FFmpeg's (AD-10); these conversions are for the correction core.
"""

from __future__ import annotations

import functools
import importlib
import logging
import math
from collections.abc import Buffer, Sequence
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray
from scipy import fft as _scipy_fft
from scipy import ndimage as _scipy_ndimage

from clearwater.interfaces.backend import ArrayBackend
from clearwater.interfaces.image import Array
from clearwater.interfaces.settings import Settings

from . import memory

_LOG = logging.getLogger(__name__)

GAUSSIAN_TRUNCATE = 4.0
"""The Gaussian support in sigmas (IF-2: 4-sigma truncation)."""

MAX_KERNEL_RADIUS = 2**23
"""The widest Gaussian radius accepted, in pixels (a kernel of about 2 ** 24 taps)."""

FFT_MIN_SHORT_SIDE = 1080
"""The FFT Gaussian's floor on ``min(H, W)`` (Q-R1): every analysis proxy's short side is less."""

FFT_MIN_SIGMA = 32.0
"""The FFT Gaussian's floor on sigma in pixels (Q-R1; the Q-R5 micro-timing kept it at 32)."""

FFT_BATCH_LINES = 512
"""The most lines (1-D transforms) per FFT batch (CHARC ruling (A), yield 13)."""

FFT_BOUND_BYTES_PER_SAMPLE = 48
"""The FFT route's bound, in bytes per sample of one batch (``FFT_BATCH_LINES`` lines of the
bound's transform length): the plans of both axes plus one batch's buffers. Measured with the
plan cache and the pool cleared first (Q-C5a condition 2, WP3.21 cell 5): at most 8.91 float32
samples, about 36 bytes, at 1080p, 4K and 5.3K for every fraction up to 0.25 and 1 or 3 channels;
48 bytes is 12 samples."""

_BINOMIAL_5 = np.array([1.0, 4.0, 6.0, 4.0, 1.0], dtype=np.float32) / np.float32(16.0)

_MIB = 1024 * 1024

# Luma coefficients (K_R, K_B) by matrix name.
_LUMA_COEFFICIENTS: dict[str, tuple[float, float]] = {
    "bt709": (0.2126, 0.0722),  # ITU-R BT.709-6, Part 2 items 3.2-3.3
    "bt601": (0.299, 0.114),  # ITU-R BT.601-7, item 2.5.1
}
_FLOAT64_SIGNIFICAND_BITS = 53
"""float64's significand bits: a sum that needs no more is exact in any order (WP3.21 #3)."""

_PLANE_G, _PLANE_B, _PLANE_R = 0, 1, 2
"""FFmpeg's planar RGB order (``gbrp`` / ``gbrp10le``, AD-10): the IF-2 device extensions."""

_RANGES = ("full", "limited")
# Limited range: per-component scale and offset applied to the full-range (Y, Cb, Cr).
_LIMITED_SCALE = np.array([219.0 / 255.0, 224.0 / 255.0, 224.0 / 255.0], dtype=np.float64)
_LIMITED_OFFSET = np.array([16.0 / 255.0, 0.0, 0.0], dtype=np.float64)


def rgb_to_ycbcr_matrix(matrix: str) -> NDArray[np.float64]:
    """Return the full-range RGB -> (Y, Cb, Cr) matrix, float64, rows Y, Cb, Cr.

    Built exactly as ``tools/prototype/pipeline.RGB_TO_YCBCR``:
    ``Y = K_R R + K_G G + K_B B``, ``Cb = (B - Y) / (2 (1 - K_B))``,
    ``Cr = (R - Y) / (2 (1 - K_R))``.

    Args:
        matrix: ``"bt709"`` or ``"bt601"``.

    Returns:
        The 3 x 3 matrix.

    Raises:
        ValueError: ``matrix`` is not ``"bt709"`` or ``"bt601"``.
    """
    if matrix not in _LUMA_COEFFICIENTS:
        raise ValueError(f"unsupported YCbCr matrix {matrix!r}; supported: bt709, bt601")
    kr, kb = _LUMA_COEFFICIENTS[matrix]
    kg = 1.0 - kr - kb
    return np.array(
        [
            [kr, kg, kb],
            [-kr / (2 * (1 - kb)), -kg / (2 * (1 - kb)), 0.5],
            [0.5, -kg / (2 * (1 - kr)), -kb / (2 * (1 - kr))],
        ],
        dtype=np.float64,
    )


@functools.cache
def _conversion(matrix: str, range_: str) -> tuple[NDArray[np.float32], NDArray[np.float32]]:
    """The float32 (forward, inverse) right-hand matrices of a conversion, built in float64.

    Forward: ``ycbcr = rgb @ forward (+ offset)``; inverse: ``rgb = (ycbcr - offset) @ inverse``.
    """
    if range_ not in _RANGES:
        raise ValueError(f"unsupported YCbCr range {range_!r}; supported: full, limited")
    forward = rgb_to_ycbcr_matrix(matrix)
    inverse = np.linalg.inv(forward)
    if range_ == "limited":
        forward = forward * _LIMITED_SCALE[:, None]
        inverse = inverse / _LIMITED_SCALE[None, :]
    return forward.T.astype(np.float32), inverse.T.astype(np.float32)


def _plane_dtype(bit_depth: int) -> np.dtype[Any]:
    """Return FFmpeg's planar sample dtype at a bit depth (little-endian words for 10-bit).

    Raises:
        ValueError: The bit depth is not 8 or 10.
    """
    if bit_depth not in (8, 10):
        raise ValueError(f"the bit depth must be 8 or 10, got {bit_depth!r}")
    return np.dtype(np.uint8) if bit_depth == 8 else np.dtype("<u2")


class CoreBackend:
    """The IF-2 implementation shared by both devices, over an array and a filter module.

    Attributes:
        name: ``"numpy"`` or ``"cupy"``.
        device: ``"cpu"`` or ``"cuda:<n>"``.
        xp: The array module (``numpy`` or ``cupy``); for ``clearwater.core`` only.
        ndimage: The filter module (``scipy.ndimage`` or ``cupyx.scipy.ndimage``).
    """

    name: str
    device: str
    xp: Any
    ndimage: Any
    fft: Any
    """The FFT module (``scipy.fft`` or ``cupyx.scipy.fft``), set by the subclass."""

    def __init__(self, name: str, device: str, xp: Any, ndimage: Any) -> None:
        """Bind the backend to its modules.

        Args:
            name: The backend name.
            device: The device the arrays live on.
            xp: The array module.
            ndimage: The filter module.
        """
        self.name = name
        self.device = device
        self.xp = xp
        self.ndimage = ndimage
        self._constants: dict[str, Any] = {}

    def __repr__(self) -> str:
        """Return the backend's name and device."""
        return f"{type(self).__name__}(device={self.device!r})"

    # -- checks and constants -------------------------------------------------------------

    def check(self, a: object) -> None:
        """Raise unless ``a`` is a float32 array of this backend's kind.

        Args:
            a: The candidate array.

        Raises:
            TypeError: ``a`` is not an array of this backend (for example a NumPy array given
                to the CuPy backend).
            ValueError: ``a`` is not float32.
        """
        if not isinstance(a, self.xp.ndarray):
            raise TypeError(
                f"the {self.name} backend takes {self.xp.__name__} arrays, got "
                f"{type(a).__module__}.{type(a).__name__}; use asarray to convert"
            )
        if a.dtype != np.float32:
            raise ValueError(f"the backend array type is float32, got {a.dtype}")

    def constant(self, key: str, value: NDArray[Any]) -> Any:
        """Return a host constant on this backend's device, uploaded once per backend.

        Args:
            key: The cache key; one key always names the same value.
            value: The NumPy constant.

        Returns:
            The constant as an array of this backend.
        """
        cached = self._constants.get(key)
        if cached is None:
            cached = self.xp.asarray(value)
            self._constants[key] = cached
        return cached

    def check_spatial(self, a: object) -> None:
        """Raise unless ``a`` is a float32 ``(H, W)`` or ``(H, W, C)`` array with H, W >= 1.

        Args:
            a: The candidate array.

        Raises:
            TypeError: ``a`` is not an array of this backend.
            ValueError: ``a`` is not float32 or has another shape.
        """
        self.check(a)
        assert isinstance(a, self.xp.ndarray)
        if a.ndim not in (2, 3) or a.shape[0] < 1 or a.shape[1] < 1:
            raise ValueError(f"expected an (H, W) or (H, W, C) array, got shape {a.shape}")

    def check_rgb(self, a: object) -> None:
        """Raise unless ``a`` is a float32 ``(H, W, 3)`` array with H, W >= 1.

        Args:
            a: The candidate array.

        Raises:
            TypeError: ``a`` is not an array of this backend.
            ValueError: ``a`` is not float32 or has another shape (an empty spatial size
                included, DR-38 c).
        """
        self.check(a)
        assert isinstance(a, self.xp.ndarray)
        if a.ndim != 3 or a.shape[2] != 3 or a.shape[0] < 1 or a.shape[1] < 1:
            raise ValueError(f"expected an (H, W, 3) array with H, W >= 1, got shape {a.shape}")

    # -- IF-2 -----------------------------------------------------------------------------

    def asarray(self, a: ArrayLike, dtype: DTypeLike = np.float32) -> Array:
        """Convert ``a`` to a float32 array of this backend (the explicit way in).

        On the GPU this uploads a host array. A NumPy backend refuses a device array (use
        that backend's :meth:`to_host`).

        Args:
            a: The input.
            dtype: Must be float32.

        Returns:
            ``a`` as a float32 array of this backend.

        Raises:
            ValueError: ``dtype`` is not float32.
            TypeError: ``a`` is an array of a device this backend cannot read.
        """
        if np.dtype(dtype) != np.float32:
            raise ValueError(f"the backend array type is float32, not {np.dtype(dtype)}")
        if (
            self.xp is np
            and not isinstance(a, np.ndarray)
            and hasattr(a, "__cuda_array_interface__")
        ):
            raise TypeError("the numpy backend does not download device arrays; use to_host")
        out: Array = self.xp.asarray(a, dtype=np.float32)
        return out

    def to_host(self, a: Array) -> NDArray[Any]:
        """Return ``a`` as a NumPy array on the host (the explicit way out).

        Args:
            a: A float32 array of this backend.

        Returns:
            The NumPy array, float32 (``a`` itself on the CPU).

        Raises:
            TypeError: ``a`` is not an array of this backend.
            ValueError: ``a`` is not float32.
        """
        self.check(a)
        if self.xp is np:
            same: NDArray[Any] = a
            return same
        host: NDArray[Any] = self.xp.asnumpy(a)
        return host

    def gaussian_blur(self, a: Array, sigma_px: float) -> Array:
        """Blur the spatial axes with a Gaussian: symmetric borders, 4-sigma truncation.

        Args:
            a: An ``(H, W)`` or ``(H, W, C)`` float32 array.
            sigma_px: The standard deviation in pixels: finite, positive, and with a radius
                ``int(4 * sigma_px + 0.5)`` of at most :data:`MAX_KERNEL_RADIUS`.

        Returns:
            The blurred array, float32, same shape. Where :func:`fft_route` holds, by the FFT
            route (see the module notes); otherwise by ``ndimage.gaussian_filter``.

        Raises:
            ValueError: ``sigma_px`` is out of range, or ``a`` has the wrong dtype or shape.
            TypeError: ``a`` is not an array of this backend.
        """
        self.check_spatial(a)
        check_sigma(sigma_px)
        if fft_route(a.shape[0], a.shape[1], sigma_px):
            weights = gaussian_kernel(sigma_px).astype(np.float32)
            return self._fft_correlate(self._fft_correlate(a, weights, 0), weights, 1)
        sigmas = (sigma_px, sigma_px) + (0.0,) * (a.ndim - 2)
        out: Array = self.ndimage.gaussian_filter(
            a, sigma=sigmas, mode="reflect", truncate=GAUSSIAN_TRUNCATE
        )
        return out

    def _fft_correlate(self, a: Array, weights: NDArray[np.float32], axis: int) -> Array:
        """Correlate one spatial axis with a symmetric kernel by a float32 real FFT, in batches.

        Each line along ``axis`` is padded as ``mode="reflect"`` pads it (repeated reflection
        included), transformed with the kernel at a fast length of at least ``n + 2r`` (so the
        ``n`` kept samples see no wrap-around), multiplied and transformed back; a symmetric
        kernel makes the convolution the correlation ``gaussian_filter`` computes. The lines go
        through in batches of at most :data:`FFT_BATCH_LINES` lines (``FFT_BATCH_LINES // C``
        positions along the other spatial axis, each with its ``C`` channels), the last batch
        being the final positions (see :func:`fft_batch_starts`), so every transform of the axis
        has one shape and one plan set, and the plans and buffers are bounded by the batch and
        the transform length whatever the width (CHARC ruling (A)). The transform length is
        EVEN: at an odd length cuFFT's result for a line depends on its position in the batch
        (measured at 4725 and 6561, not at any even length tried), so the last, overlapping
        batch would not equal the lines it recomputes; at an even length every batch gives the
        unbatched transform's lines bit for bit.
        """
        xp, fft = self.xp, self.fft
        radius = (weights.size - 1) // 2
        n = a.shape[axis]
        size = int(fft.next_fast_len(n + 2 * radius, real=True))
        while size % 2:  # cuFFT's odd real lengths give a line's result by its batch position
            size = int(fft.next_fast_len(size + 1, real=True))
        shape = [1] * a.ndim
        shape[axis] = size // 2 + 1
        kernel = fft.rfft(xp.asarray(weights), n=size).reshape(shape)
        index = xp.asarray(reflect_index(n, radius))
        kept = [slice(None)] * a.ndim
        kept[axis] = slice(2 * radius, 2 * radius + n)
        other = 1 - axis
        channels = a.shape[2] if a.ndim == 3 else 1
        batch = max(1, FFT_BATCH_LINES // channels)  # positions x channels <= FFT_BATCH_LINES
        out: Array = xp.empty_like(a)
        for start in fft_batch_starts(a.shape[other], batch):
            lines = [slice(None)] * a.ndim
            lines[other] = slice(start, start + batch)
            spectrum = fft.rfft(xp.take(a[tuple(lines)], index, axis=axis), n=size, axis=axis)
            spectrum *= kernel
            full = fft.irfft(spectrum, n=size, axis=axis)
            del spectrum
            out[tuple(lines)] = full[tuple(kept)]  # an overlapped line is recomputed, not blended
        return out

    def _binomial_blur(self, a: Array) -> Array:
        """Separable [1 4 6 4 1]/16 filter over the two spatial axes, symmetric borders."""
        kernel = self.constant("binomial_5", _BINOMIAL_5)
        rows = self.ndimage.correlate1d(a, kernel, axis=0, mode="reflect")
        both: Array = self.ndimage.correlate1d(rows, kernel, axis=1, mode="reflect")
        return both

    def pyramid_reduce(self, a: Array) -> Array:
        """Reduce by one pyramid level: [1 4 6 4 1]/16, keeping even rows and columns.

        An odd size n becomes ``(n + 1) / 2``.

        Args:
            a: An ``(H, W)`` or ``(H, W, C)`` float32 array.

        Returns:
            The reduced array, float32, ``(ceil(H/2), ceil(W/2)[, C])``, contiguous.

        Raises:
            ValueError: ``a`` has the wrong dtype or shape.
            TypeError: ``a`` is not an array of this backend.
        """
        self.check_spatial(a)
        out: Array = self.xp.ascontiguousarray(self._binomial_blur(a)[::2, ::2])
        return out

    def pyramid_expand(self, a: Array, shape: tuple[int, int]) -> Array:
        """Expand by one pyramid level: zero-insert, same filter, normalised.

        The samples go to rows and columns 0, 2, 4, ... of a zero array of the target size,
        which is filtered with [1 4 6 4 1]/16 and divided by the same filter of the sample
        indicator (exactly 1/4 in the interior; at the borders it keeps a constant level
        constant).

        Args:
            a: The coarse ``(h, w)`` or ``(h, w, C)`` float32 array.
            shape: The target ``(height, width)``, with ``h == ceil(height / 2)`` and
                ``w == ceil(width / 2)``.

        Returns:
            The expanded array, float32, ``(height, width[, C])``.

        Raises:
            ValueError: ``shape`` does not match ``a``, or ``a`` has the wrong dtype or shape.
            TypeError: ``a`` is not an array of this backend.
        """
        self.check_spatial(a)
        if len(shape) != 2:
            raise ValueError(f"shape must be (height, width), got {shape!r}")
        height, width = int(shape[0]), int(shape[1])
        if a.shape[0] != math.ceil(height / 2) or a.shape[1] != math.ceil(width / 2):
            raise ValueError(
                f"a level of {a.shape[0]} x {a.shape[1]} does not expand to {height} x {width}"
            )
        xp = self.xp
        upsampled = xp.zeros((height, width, *a.shape[2:]), dtype=np.float32)
        upsampled[::2, ::2] = a
        indicator = xp.zeros((height, width), dtype=np.float32)
        indicator[::2, ::2] = 1.0
        norm = self._binomial_blur(indicator)
        blurred = self._binomial_blur(upsampled)
        if blurred.ndim == 3:
            norm = norm[..., None]
        out: Array = (blurred / norm).astype(np.float32, copy=False)
        return out

    def rgb_to_ycbcr(self, a: Array, matrix: str, range_: str) -> Array:
        """Convert RGB to YCbCr (see the module docstring for the conventions).

        Args:
            a: The RGB array, float32, ``(H, W, 3)``.
            matrix: ``"bt709"`` or ``"bt601"``.
            range_: ``"full"`` or ``"limited"``.

        Returns:
            The YCbCr array, float32, ``(H, W, 3)``.

        Raises:
            ValueError: An unsupported matrix or range, or ``a`` has the wrong dtype or shape.
            TypeError: ``a`` is not an array of this backend.
        """
        forward, _ = _conversion(matrix, range_)
        self.check_rgb(a)
        out: Array = (a @ self.constant(f"rgb_to_ycbcr/{matrix}/{range_}", forward)).astype(
            np.float32, copy=False
        )
        if range_ == "limited":
            out += self.constant("limited_offset", _LIMITED_OFFSET.astype(np.float32))
        return out

    def ycbcr_to_rgb(self, a: Array, matrix: str, range_: str) -> Array:
        """Convert YCbCr to RGB, unclipped (the exact inverse of :meth:`rgb_to_ycbcr`).

        Args:
            a: The YCbCr array, float32, ``(H, W, 3)``.
            matrix: ``"bt709"`` or ``"bt601"``.
            range_: ``"full"`` or ``"limited"``.

        Returns:
            The RGB array, float32, ``(H, W, 3)``.

        Raises:
            ValueError: An unsupported matrix or range, or ``a`` has the wrong dtype or shape.
            TypeError: ``a`` is not an array of this backend.
        """
        _, inverse = _conversion(matrix, range_)
        self.check_rgb(a)
        if range_ == "limited":
            a = a - self.constant("limited_offset", _LIMITED_OFFSET.astype(np.float32))
        out: Array = (a @ self.constant(f"ycbcr_to_rgb/{matrix}/{range_}", inverse)).astype(
            np.float32, copy=False
        )
        return out

    def percentile(self, a: Array, q: Sequence[float]) -> Array:
        """Return percentiles of the whole array by linear interpolation (R-7).

        The order statistics are interpolated in float64 by ``xp.percentile`` (as the
        prototype's N{} bounds) and the result is cast to float32 once.

        Args:
            a: A float32 array of this backend, not empty.
            q: The percentiles, each finite and within 0 to 100.

        Returns:
            The values, float32, shape ``(len(q),)``, on this backend's device.

        Raises:
            ValueError: ``a`` is empty or not float32, or a percentile is out of range.
            TypeError: ``a`` is not an array of this backend.
        """
        self.check(a)
        if a.size == 0:
            raise ValueError("percentile of an empty array")
        qs = [float(value) for value in q]
        for value in qs:
            if not (math.isfinite(value) and 0.0 <= value <= 100.0):
                raise ValueError(f"percentiles must lie in [0, 100], got {value!r}")
        out: Array = self.xp.percentile(a, qs, method="linear").astype(np.float32)
        return out

    def memory_estimate_bytes(self, height: int, width: int, method_id: str) -> int:
        """Estimate the device memory a frame of this size needs (AD-1).

        Args:
            height: Frame height in pixels.
            width: Frame width in pixels.
            method_id: The correction method id (``"c3"`` or ``"ancuti2018"``).

        Returns:
            The estimate in bytes (:func:`clearwater.core.memory.memory_estimate_bytes`).

        Raises:
            ValueError: An unknown method id or a size under 1.
        """
        return memory.memory_estimate_bytes(height, width, method_id)

    def free_device_bytes(self) -> int | None:
        """Return the free device memory in bytes, or None on CPU."""
        return None


class NumpyBackend(CoreBackend):
    """The CPU backend: NumPy and ``scipy.ndimage`` (IF-2 ``name = "numpy"``)."""

    def __init__(self) -> None:
        """Bind NumPy and ``scipy.ndimage``."""
        super().__init__("numpy", "cpu", np, _scipy_ndimage)
        self.fft = _scipy_fft


class CupyBackend(CoreBackend):
    """The GPU backend: CuPy and ``cupyx.scipy.ndimage`` on the current CUDA device."""

    def __init__(self) -> None:
        """Import CuPy and bind it to the current device.

        Raises:
            ImportError: CuPy or ``cupyx.scipy.ndimage`` is not installed.
            cupy.cuda.runtime.CUDARuntimeError: The current device cannot be bound.
        """
        cupy = importlib.import_module("cupy")
        ndimage = importlib.import_module("cupyx.scipy.ndimage")
        self._device_id = int(cupy.cuda.runtime.getDevice())
        super().__init__("cupy", f"cuda:{self._device_id}", cupy, ndimage)

    @functools.cached_property
    def fft(self) -> Any:
        """``cupyx.scipy.fft``, imported at the first FFT Gaussian rather than at construction."""
        return importlib.import_module("cupyx.scipy.fft")

    # -- IF-2 device extensions (AD-29) ---------------------------------------------------------
    #
    # IF-2 device extensions: NOT part of the frozen ABC; provided by the GPU backend; absent on
    # the CPU backend. A consumer reaches them only through the one ``runtime_checkable``
    # Protocol of its own package (``clearwater.io.video.decode.DeviceFrameBackend``,
    # ``clearwater.analysis.proxy.AnalysisDeviceBackend``), with the same names and signatures,
    # and takes its host path when a backend lacks them.

    def planes_to_rgb(self, data: Buffer, *, width: int, height: int, bit_depth: int) -> Array:
        """Upload one planar G, B, R frame and convert it to float32 RGB on the device.

        The device twin of ``clearwater.color.planes_to_rgb`` (WP3.21 #2): only the integer
        planes cross the bus (a third of the float32 frame's bytes at 8-bit, two thirds at
        10-bit), and each sample is divided by ``float32(2**bit_depth - 1)`` on the device. That
        is one correctly rounded IEEE float32 division per sample, the host's operation, so the
        result equals the host conversion bit for bit.

        Args:
            data: The raw frame as FFmpeg's ``gbrp`` / ``gbrp10le`` writes it. It may be reused
                once this returns: the copy from pageable host memory has read it.
            width: Frame width in pixels.
            height: Frame height in pixels.
            bit_depth: 8 or 10.

        Returns:
            A new C-contiguous float32 device array of shape ``(height, width, 3)``, channels
            R, G, B.

        Raises:
            ValueError: The bit depth is not 8 or 10, or ``data`` is not exactly one contiguous
                frame of that size.
        """
        dtype = _plane_dtype(bit_depth)
        view = memoryview(data)
        if not view.c_contiguous:
            raise ValueError("the frame buffer must be contiguous")
        expected = 3 * width * height * dtype.itemsize
        if width < 1 or height < 1 or view.nbytes != expected:
            raise ValueError(
                f"a {width}x{height} {bit_depth}-bit frame is {expected} bytes, not {view.nbytes}"
            )
        planes = self.xp.asarray(np.frombuffer(view, dtype=dtype).reshape(3, height, width))
        scale = np.float32(2**bit_depth - 1)
        rgb: Array = self.xp.empty((height, width, 3), dtype=np.float32)
        rgb[..., 0] = planes[_PLANE_R] / scale
        rgb[..., 1] = planes[_PLANE_G] / scale
        rgb[..., 2] = planes[_PLANE_B] / scale
        return rgb

    def rgb_to_planes(self, a: Array, *, bit_depth: int) -> bytes:
        """Quantise a float32 RGB device array to one planar G, B, R frame on the device.

        The device twin of ``clearwater.color.rgb_to_planes`` (D39, WP3.21 #2): clipped to
        [0, 1], scaled by ``2**bit_depth - 1`` and rounded half to even, each a kernel of its
        own (no fused multiply-add), so the bytes are the host's; only the planes are
        downloaded (synchronously: the copy has completed on return).

        Args:
            a: A float32 ``(H, W, 3)`` RGB array on this backend's device.
            bit_depth: 8 or 10.

        Returns:
            The frame as FFmpeg's ``gbrp`` (8-bit) or ``gbrp10le`` (10-bit) reads it.

        Raises:
            TypeError: ``a`` is not an array of this backend, or lies on another device.
            ValueError: The bit depth is not 8 or 10, ``a`` is not a float32 ``(H, W, 3)``
                array, or it holds a NaN.
        """
        dtype = _plane_dtype(bit_depth)
        self.check_rgb(a)
        self._check_device_id(a)
        xp = self.xp
        scaled = xp.clip(a, np.float32(0), np.float32(1)) * np.float32(2**bit_depth - 1)
        if bool(xp.isnan(scaled.sum())):
            raise ValueError("the array holds a NaN; it cannot be quantised")
        height, width = a.shape[:2]
        planes = xp.empty((3, height, width), dtype=dtype)
        planes[_PLANE_G] = xp.rint(scaled[..., 1])
        planes[_PLANE_B] = xp.rint(scaled[..., 2])
        planes[_PLANE_R] = xp.rint(scaled[..., 0])
        host: NDArray[Any] = xp.asnumpy(planes)
        return host.tobytes()

    def block_sums(self, a: Array, k: int) -> NDArray[np.float64] | None:
        """Return the ``k x k`` block sums of a device array in float64 on the host, when exact.

        The sums the analysis proxy's block mean divides and quantises (WP3.21 #3, AD-5): each
        output is the sum of the source pixels its block covers, ``ceil(H / k) x ceil(W / k)``,
        the last row and column of blocks covering fewer pixels when ``k`` does not divide the
        size. They are taken on the device (rows, then columns) and only they are downloaded,
        ``k * k`` times fewer values than the frame.

        They are returned only when every sum, and every partial sum on the way, is exact in
        float64, so that any summation order gives the host's sums bit for bit. A finite
        non-zero float32 ``v`` with ``2**e <= |v|`` is a multiple of ``2**(e - 23)``; with every
        ``|v| <= 1`` each partial sum is a multiple of ``2**(e_min - 23)`` (``e_min`` the
        exponent of the smallest non-zero ``|v|``) below ``2**m``, ``m = ceil(log2(k * k + 1))``,
        which float64 holds exactly when ``m - (e_min - 23) <= 53``. A decoded frame always
        passes: its values are ``c / 255`` or ``c / 1023`` (``e_min`` -8 or -10), so 38 bits at
        ``k = 8`` for 8-bit input and 40 bits for 10-bit input.

        Args:
            a: A float32 ``(H, W, C)`` array on this backend's device.
            k: The block factor, at least 1.

        Returns:
            float64 ``(ceil(H / k), ceil(W / k), C)`` on the host, or None when the bound does
            not hold (a NaN, an infinity, a value above 1 in magnitude, or non-zero values too
            small for it): the caller then reduces the frame on the host.

        Raises:
            TypeError: ``a`` is not an array of this backend, or lies on another device.
            ValueError: ``a`` is not a float32 ``(H, W, C)`` array, or ``k`` is below 1.
        """
        if k < 1:
            raise ValueError(f"the block factor must be at least 1, got {k}")
        self.check(a)
        if a.ndim != 3 or a.shape[0] < 1 or a.shape[1] < 1:
            raise ValueError(f"expected an (H, W, C) array, got shape {a.shape}")
        self._check_device_id(a)
        if not self._sums_are_exact(a, k):
            return None
        xp = self.xp
        height, width, channels = a.shape
        full_rows, full_cols = height // k, width // k
        rows, cols = -(-height // k), -(-width // k)
        by_rows = xp.empty((rows, width, channels), dtype=np.float64)
        if full_rows:
            by_rows[:full_rows] = (
                a[: full_rows * k]
                .reshape(full_rows, k, width, channels)
                .sum(axis=1, dtype=np.float64)
            )
        if rows > full_rows:
            by_rows[full_rows] = a[full_rows * k :].sum(axis=0, dtype=np.float64)
        summed = xp.empty((rows, cols, channels), dtype=np.float64)
        if full_cols:
            summed[:, :full_cols] = (
                by_rows[:, : full_cols * k].reshape(rows, full_cols, k, channels).sum(axis=2)
            )
        if cols > full_cols:
            summed[:, full_cols] = by_rows[:, full_cols * k :].sum(axis=1)
        host: NDArray[np.float64] = xp.asnumpy(summed)
        return host

    def _sums_are_exact(self, a: Any, k: int) -> bool:
        """Tell whether :meth:`block_sums`' bound holds on ``a`` (see there), by reductions only."""
        top = max(float(a.max()), -float(a.min()))  # NaN propagates: ``not top <= 1`` below
        if not top <= 1.0:  # a NaN, an infinity or a value above 1 in magnitude
            return False
        if top == 0.0:
            return True
        smallest = float(self._min_nonzero_magnitude(a))
        lowest_bit = math.frexp(smallest)[1] - 1 - 23
        highest_bit = math.ceil(math.log2(k * k + 1))
        return highest_bit - lowest_bit <= _FLOAT64_SIGNIFICAND_BITS

    @functools.cached_property
    def _min_nonzero_magnitude(self) -> Any:
        """A reduction kernel: the smallest non-zero ``|v|`` (no frame-sized temporary).

        Called only once every ``|v| <= 1`` and some ``v`` is non-zero, so 2 stands for "no
        value" (a zero, and the identity).
        """
        return self.xp.ReductionKernel(
            "T x",
            "T y",
            "x == (T)0 ? (T)2 : abs(x)",
            "min(a, b)",
            "y = a",
            "(T)2",
            "clearwater_min_nonzero_magnitude",
        )

    def _check_device_id(self, a: Any) -> None:
        """Raise TypeError when the CuPy array ``a`` lies on another device than this backend's."""
        if int(a.device.id) != self._device_id:
            raise TypeError(f"the array lies on cuda:{int(a.device.id)}, not {self.device}")

    def release_fft_plans(self) -> None:
        """Free the calling thread's cuFFT plans and the memory pool's free blocks (Q-C5a).

        The FFT Gaussian keeps CuPy's default plan cache, so within an export job every frame
        reuses its plans; ``clearwater.jobs`` calls this once at the end of each job (success,
        failure or cancel), never per frame, so the plans of one clip do not outlive its job.
        CuPy's plan cache is per thread and per device: this clears the current device's cache of
        the calling thread (the job's, where it renders).
        """
        self.xp.fft.config.get_plan_cache().clear()
        self.xp.get_default_memory_pool().free_all_blocks()

    def memory_estimate_bytes(self, height: int, width: int, method_id: str) -> int:
        """Estimate the device memory a frame of this size needs on the GPU (AD-1, Q-C5a).

        The base estimate plus :func:`fft_memory_bound_bytes`: the FFT Gaussian's cached plans
        and batch buffers, which a frame meeting the gate's shape may need.

        Args:
            height: Frame height in pixels.
            width: Frame width in pixels.
            method_id: The correction method id (``"c3"`` or ``"ancuti2018"``).

        Returns:
            The estimate in bytes.

        Raises:
            ValueError: An unknown method id or a size under 1.
        """
        base = memory.memory_estimate_bytes(height, width, method_id)
        return base + fft_memory_bound_bytes(height, width)

    def free_device_bytes(self) -> int | None:
        """Return the memory free for this process's arrays, in bytes.

        That is the driver's free figure (``cudaMemGetInfo``) plus the blocks CuPy's default
        memory pool holds but no array uses: the driver counts those as used, yet the next
        frame's arrays are allocated from them first. Without them, the second frame of a clip
        would see the first frame's working set as taken and fall back to the CPU.
        """
        free, _total = self.xp.cuda.runtime.memGetInfo()
        return int(free) + int(self.xp.get_default_memory_pool().free_bytes())


def fft_route(height: int, width: int, sigma_px: float) -> bool:
    """Tell whether ``gaussian_blur`` takes the FFT route for this shape and sigma (Q-R1).

    The rule reads the shape and sigma only, never the device or its free memory, so the route,
    and so the output, is the same on every machine and on both backends.

    Args:
        height: The array's first spatial axis.
        width: Its second spatial axis.
        sigma_px: The standard deviation in pixels.

    Returns:
        True when ``min(height, width) >= FFT_MIN_SHORT_SIDE`` and ``sigma_px >= FFT_MIN_SIGMA``.
    """
    return min(height, width) >= FFT_MIN_SHORT_SIDE and sigma_px >= FFT_MIN_SIGMA


def fft_memory_bound_bytes(height: int, width: int) -> int:
    """Return a bound on the FFT Gaussian's plans and batch buffers for a frame (Q-C5a (2)).

    With the batch fixed, the cost depends only on the transform length (cuFFT's plan size
    follows the transform length, not the image shape) and the batch. Every gated call's
    radius is at most the short side plus one (every spatial fraction of both methods is at most
    0.25, so ``4 * sigma`` is at most the short side), so no transform is longer than the
    power of two at or above ``longer + 2 * (shorter + 1)``, which is even and so at least the
    route's own length. 0 when no call can meet the gate's shape.

    Args:
        height: Frame height in pixels.
        width: Frame width in pixels.

    Returns:
        ``FFT_BOUND_BYTES_PER_SAMPLE * FFT_BATCH_LINES * length`` bytes, or 0.
    """
    shorter, longer = min(height, width), max(height, width)
    if shorter < FFT_MIN_SHORT_SIDE:
        return 0
    length = 1 << (longer + 2 * (shorter + 1) - 1).bit_length()
    return FFT_BOUND_BYTES_PER_SAMPLE * FFT_BATCH_LINES * length


def fft_batch_starts(lines: int, batch: int) -> list[int]:
    """Return the first line of each FFT batch: every batch is ``batch`` lines long.

    The batches step by ``batch`` and the last one is the final ``batch`` lines, overlapping its
    predecessor when ``lines`` is not a multiple of ``batch``; fewer lines than ``batch`` make one
    batch of them all.

    Args:
        lines: The number of lines.
        batch: The batch length.

    Returns:
        The start of each batch, ascending.
    """
    if lines <= batch:
        return [0]
    return [*range(0, lines - batch, batch), lines - batch]


def gaussian_kernel(sigma_px: float) -> NDArray[np.float64]:
    """Return SciPy's order-0 Gaussian correlation weights for ``sigma_px`` (float64).

    The weights ``scipy.ndimage`` and ``cupyx.scipy.ndimage`` build (``_gaussian_kernel1d``):
    ``exp(-0.5 / sigma**2 * x**2)`` over ``x`` in ``[-r, r]``, ``r = int(4 * sigma + 0.5)``,
    normalised to sum 1.

    Args:
        sigma_px: The standard deviation in pixels (already checked by :func:`check_sigma`).

    Returns:
        The ``2r + 1`` weights.
    """
    radius = int(GAUSSIAN_TRUNCATE * float(sigma_px) + 0.5)
    x = np.arange(-radius, radius + 1)
    sigma2 = float(sigma_px) * float(sigma_px)
    weights: NDArray[np.float64] = np.exp(-0.5 / sigma2 * x**2)
    weights /= weights.sum()
    return weights


def reflect_index(n: int, radius: int) -> NDArray[np.intp]:
    """Return the source index of each sample of a line padded as ``mode="reflect"``.

    ``d c b a | a b c d | d c b a``: the edge sample repeats, and a radius beyond the line
    reflects again (period ``2n``).

    Args:
        n: The line's length (at least 1).
        radius: The padding on each side.

    Returns:
        ``n + 2 * radius`` indices into the line.
    """
    i = np.mod(np.arange(-radius, n + radius), 2 * n)
    out: NDArray[np.intp] = np.where(i < n, i, 2 * n - 1 - i)
    return out


def check_sigma(sigma_px: float) -> None:
    """Raise unless ``sigma_px`` is a usable Gaussian standard deviation in pixels.

    Args:
        sigma_px: The standard deviation.

    Raises:
        ValueError: ``sigma_px`` is not finite, not positive, or its radius
            ``int(4 * sigma_px + 0.5)`` exceeds :data:`MAX_KERNEL_RADIUS` (a finite sigma whose
            ``4 * sigma_px`` overflows to infinity included: ValueError, never OverflowError,
            DR-38 d).
    """
    if not (math.isfinite(sigma_px) and sigma_px > 0.0):
        raise ValueError(f"sigma must be finite and positive, got {sigma_px!r} px")
    reach = GAUSSIAN_TRUNCATE * sigma_px + 0.5
    if not math.isfinite(reach) or int(reach) > MAX_KERNEL_RADIUS:
        raise ValueError(
            f"sigma {sigma_px:.6g} px gives a filter radius beyond {MAX_KERNEL_RADIUS} px"
        )


_NUMPY_BACKEND = NumpyBackend()


@functools.cache
def _probe_gpu() -> tuple[CupyBackend | None, str]:
    """Return the GPU backend, or None and the CPU reason; probed once per process."""
    try:
        cupy = importlib.import_module("cupy")
    except Exception as exc:
        # Only a ModuleNotFoundError naming cupy itself means it is not installed (DR-37 a);
        # any other failure, an ImportError of a DLL or of a module inside or beside CuPy
        # included, is an installed CuPy that fails to load.
        if isinstance(exc, ModuleNotFoundError) and exc.name == "cupy":
            _LOG.info("CuPy not installed: %s", exc)
            return None, "CPU: CuPy not installed"
        _LOG.info("CuPy failed to load: %s: %s", type(exc).__name__, exc)
        return None, "CPU: CuPy failed to load"
    try:
        importlib.import_module("cupyx.scipy.ndimage")
    except Exception as exc:  # an incomplete installation without cupyx
        _LOG.info("cupyx failed to load: %s: %s", type(exc).__name__, exc)
        return None, "CPU: CuPy failed to load"
    try:
        count = int(cupy.cuda.runtime.getDeviceCount())
    except Exception as exc:  # no driver, or the runtime cannot reach one
        _LOG.info("the CUDA runtime did not answer: %s", exc)
        return None, "CPU: no CUDA device"
    if count < 1:
        return None, "CPU: no CUDA device"
    try:
        backend = CupyBackend()  # both modules are loaded: what can fail is the device
    except Exception as exc:  # the current device cannot be bound (unavailable, lost)
        _LOG.info("the CUDA device could not be bound: %s: %s", type(exc).__name__, exc)
        return None, "CPU: CUDA device unusable"
    try:
        probe = cupy.arange(4, dtype=cupy.float32) + cupy.float32(1.0)
        if float(probe.sum()) != 10.0:
            return None, "CPU: CUDA device unusable"
    except Exception as exc:  # a missing runtime library or header shows at the first kernel
        _LOG.info("a test kernel failed on the CUDA device: %s", exc)
        return None, "CPU: CUDA device unusable"
    return backend, "GPU"


def backend_for(device: str) -> CoreBackend:
    """Return the core backend whose arrays live on ``device`` (IF-1 ``Image.device``).

    ``"cpu"`` gives the process's :class:`NumpyBackend` (the one :func:`select_backend`
    returns, without importing CuPy); the GPU's own ``"cuda:<n>"`` gives the probed
    :class:`CupyBackend` (probed once per process, as :func:`select_backend` does). So a method
    given an image recovers the backend its pixels belong to.

    Args:
        device: The device name, ``"cpu"`` or ``"cuda:<n>"``.

    Returns:
        The backend of that device.

    Raises:
        ValueError: No backend of this process lives on ``device`` (an unknown name, a CUDA
            device that is not the probed one, or no usable GPU); the message names the
            device and the GPU probe's reason.
    """
    if device == "cpu":
        return _NUMPY_BACKEND
    gpu, reason = _probe_gpu()
    if gpu is not None and device == gpu.device:
        return gpu
    available = "cpu" if gpu is None else f"cpu, {gpu.device}"
    raise ValueError(f"no backend for device {device!r}; available: {available} ({reason})")


def select_backend(
    settings: Settings, height: int, width: int, method_id: str
) -> tuple[ArrayBackend, str]:
    """Choose the backend for a frame size (IF-2; AD-1, AD-9, D111, N4).

    The first matching rule wins: ``settings.force_cpu`` gives the CPU (``"CPU: forced"``);
    then CuPy must import, a CUDA device must exist and a test kernel must run (probed once per
    process); then the free device memory is read (on every call; a failure to read it gives
    ``"CPU: CUDA device unusable"``); then the GPU is chosen when the estimate is strictly
    below it, else the CPU with both figures in MiB, the estimate rounded up and the free
    memory rounded down.

    Args:
        settings: The application settings (``force_cpu``).
        height: Frame height in pixels.
        width: Frame width in pixels.
        method_id: The correction method id (``"c3"`` or ``"ancuti2018"``).

    Returns:
        The backend and the reason: ``"GPU"``, ``"CPU: forced"``, ``"CPU: CuPy not
        installed"``, ``"CPU: CuPy failed to load"``, ``"CPU: no CUDA device"``, ``"CPU: CUDA
        device unusable"`` or ``"CPU: estimate 1,982 MiB exceeds free 1,200 MiB"``.

    Raises:
        ValueError: An unknown method id or a size under 1.
    """
    estimate = memory.memory_estimate_bytes(height, width, method_id)
    if settings.force_cpu:
        return _NUMPY_BACKEND, "CPU: forced"
    gpu, reason = _probe_gpu()
    if gpu is None:
        return _NUMPY_BACKEND, reason
    try:
        free = gpu.free_device_bytes()
    except Exception as exc:  # the device was lost after the probe (a driver reset, a TDR)
        _LOG.info("free device memory could not be read: %s: %s", type(exc).__name__, exc)
        return _NUMPY_BACKEND, "CPU: CUDA device unusable"
    assert free is not None  # a CUDA backend always reports its free memory
    if estimate < free:
        return gpu, "GPU"
    estimate_mib = -(-estimate // _MIB)
    free_mib = free // _MIB
    return _NUMPY_BACKEND, f"CPU: estimate {estimate_mib:,} MiB exceeds free {free_mib:,} MiB"
