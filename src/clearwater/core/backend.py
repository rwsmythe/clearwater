"""The two array backends of IF-2 and the device choice (AD-1, AD-9, D107, D111).

:class:`NumpyBackend` (CPU) and :class:`CupyBackend` (GPU) share one implementation,
:class:`CoreBackend`, which reaches its device only through two modules: ``xp`` (``numpy`` or
``cupy``) and ``ndimage`` (``scipy.ndimage`` or ``cupyx.scipy.ndimage``). So the same code runs
on either device (D107, N3). CuPy is imported only here and only when a :class:`CupyBackend` is
built or :func:`select_backend` probes the device, so ``import clearwater.core`` works without
it. ``CoreBackend.xp`` is for ``clearwater.core`` only (WP3.1 ruling 1.1).

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
from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import ArrayLike, DTypeLike, NDArray
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

_BINOMIAL_5 = np.array([1.0, 4.0, 6.0, 4.0, 1.0], dtype=np.float32) / np.float32(16.0)

_MIB = 1024 * 1024

# Luma coefficients (K_R, K_B) by matrix name.
_LUMA_COEFFICIENTS: dict[str, tuple[float, float]] = {
    "bt709": (0.2126, 0.0722),  # ITU-R BT.709-6, Part 2 items 3.2-3.3
    "bt601": (0.299, 0.114),  # ITU-R BT.601-7, item 2.5.1
}
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
        """Raise unless ``a`` is a float32 ``(H, W, 3)`` array.

        Args:
            a: The candidate array.

        Raises:
            TypeError: ``a`` is not an array of this backend.
            ValueError: ``a`` is not float32 or has another shape.
        """
        self.check(a)
        assert isinstance(a, self.xp.ndarray)
        if a.ndim != 3 or a.shape[2] != 3:
            raise ValueError(f"expected an (H, W, 3) array, got shape {a.shape}")

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
            a: An array of this backend.

        Returns:
            The NumPy array (``a`` itself on the CPU).

        Raises:
            TypeError: ``a`` is not an array of this backend.
        """
        if not isinstance(a, self.xp.ndarray):
            raise TypeError(
                f"the {self.name} backend takes {self.xp.__name__} arrays, got "
                f"{type(a).__module__}.{type(a).__name__}"
            )
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
            The blurred array, float32, same shape.

        Raises:
            ValueError: ``sigma_px`` is out of range, or ``a`` has the wrong dtype or shape.
            TypeError: ``a`` is not an array of this backend.
        """
        self.check_spatial(a)
        check_sigma(sigma_px)
        sigmas = (sigma_px, sigma_px) + (0.0,) * (a.ndim - 2)
        out: Array = self.ndimage.gaussian_filter(
            a, sigma=sigmas, mode="reflect", truncate=GAUSSIAN_TRUNCATE
        )
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


class CupyBackend(CoreBackend):
    """The GPU backend: CuPy and ``cupyx.scipy.ndimage`` on the current CUDA device."""

    def __init__(self) -> None:
        """Import CuPy and bind it to the current device.

        Raises:
            ImportError: CuPy or ``cupyx.scipy.ndimage`` is not installed.
        """
        cupy = importlib.import_module("cupy")
        ndimage = importlib.import_module("cupyx.scipy.ndimage")
        device = f"cuda:{int(cupy.cuda.runtime.getDevice())}"
        super().__init__("cupy", device, cupy, ndimage)

    def free_device_bytes(self) -> int | None:
        """Return the memory free for this process's arrays, in bytes.

        That is the driver's free figure (``cudaMemGetInfo``) plus the blocks CuPy's default
        memory pool holds but no array uses: the driver counts those as used, yet the next
        frame's arrays are allocated from them first. Without them, the second frame of a clip
        would see the first frame's working set as taken and fall back to the CPU.
        """
        free, _total = self.xp.cuda.runtime.memGetInfo()
        return int(free) + int(self.xp.get_default_memory_pool().free_bytes())


def check_sigma(sigma_px: float) -> None:
    """Raise unless ``sigma_px`` is a usable Gaussian standard deviation in pixels.

    Args:
        sigma_px: The standard deviation.

    Raises:
        ValueError: ``sigma_px`` is not finite, not positive, or its radius
            ``int(4 * sigma_px + 0.5)`` exceeds :data:`MAX_KERNEL_RADIUS`.
    """
    if not (math.isfinite(sigma_px) and sigma_px > 0.0):
        raise ValueError(f"sigma must be finite and positive, got {sigma_px!r} px")
    if int(GAUSSIAN_TRUNCATE * sigma_px + 0.5) > MAX_KERNEL_RADIUS:
        raise ValueError(
            f"sigma {sigma_px:.6g} px gives a filter radius beyond {MAX_KERNEL_RADIUS} px"
        )


_NUMPY_BACKEND = NumpyBackend()


@functools.cache
def _probe_gpu() -> tuple[CupyBackend | None, str]:
    """Return the GPU backend, or None and the CPU reason; probed once per process."""
    try:
        cupy = importlib.import_module("cupy")
    except ImportError as exc:
        _LOG.info("CuPy not installed: %s", exc)
        return None, "CPU: CuPy not installed"
    except Exception as exc:  # an installed CuPy that fails to initialise (a DLL, a driver)
        _LOG.info("CuPy failed to load: %s: %s", type(exc).__name__, exc)
        return None, "CPU: CuPy failed to load"
    try:
        count = int(cupy.cuda.runtime.getDeviceCount())
    except Exception as exc:  # no driver, or the runtime cannot reach one
        _LOG.info("the CUDA runtime did not answer: %s", exc)
        return None, "CPU: no CUDA device"
    if count < 1:
        return None, "CPU: no CUDA device"
    try:
        backend = CupyBackend()
    except Exception as exc:  # an incomplete installation without cupyx
        _LOG.info("cupyx failed to load: %s: %s", type(exc).__name__, exc)
        return None, "CPU: CuPy failed to load"
    try:
        probe = cupy.arange(4, dtype=cupy.float32) + cupy.float32(1.0)
        if float(probe.sum()) != 10.0:
            return None, "CPU: CUDA device unusable"
    except Exception as exc:  # a missing runtime library or header shows at the first kernel
        _LOG.info("a test kernel failed on the CUDA device: %s", exc)
        return None, "CPU: CUDA device unusable"
    return backend, "GPU"


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
