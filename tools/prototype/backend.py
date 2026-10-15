"""Array backends of the prototype pipeline: NumPy on the CPU, CuPy on the graphics card.

The pipeline is written once (D30, D107, spec N3). Every pipeline function obtains its
array namespace from its input with :func:`of`, so one code path runs on either device:
a NumPy array is processed by NumPy and ``scipy.ndimage``, a CuPy array by CuPy and
``cupyx.scipy.ndimage``. :func:`select_backend` chooses the device for a run, and
:func:`prototype.pipeline.correct` moves its input there once and its results back once.

CuPy is optional at import time: this module never imports it statically, so the CPU path
works (and type-checks) on a machine without CuPy or without a CUDA device.

:func:`memory_estimate_bytes` is the working-set estimate that the spec's fallback rule
needs (D68, D110, N4: a frame that is estimated not to fit in graphics memory is
processed on the CPU); WP1.2 compares it with the measured peaks.
"""

from __future__ import annotations

import importlib
import logging
import math
import sys
from dataclasses import dataclass
from types import ModuleType
from typing import Any, Literal

import numpy as np
from scipy import ndimage as _scipy_ndimage

from .params import Params

Device = Literal["auto", "cpu", "gpu"]
DEVICES: tuple[Device, ...] = ("auto", "cpu", "gpu")

_LOG = logging.getLogger(__name__)

# The working-set model of memory_estimate_bytes: the peak in float32 planes of the image
# size (25 + 13 1/3 + 11 3/4, see that function's docstring), its margin and a fixed part.
_PEAK_PLANES = 25.0 + 40.0 / 3.0 + 11.75
_ESTIMATE_MARGIN = 1.25
_FIXED_BYTES = 1024 * 1024


@dataclass(frozen=True)
class Backend:
    """An array namespace and its device: NumPy on the CPU or CuPy on the graphics card.

    Attributes:
        name: ``"cpu"`` or ``"gpu"``.
        xp: The array module, ``numpy`` or ``cupy``.
        ndimage: The filter module, ``scipy.ndimage`` or ``cupyx.scipy.ndimage``.
        reason: Why :func:`select_backend` chose this backend when ``"auto"`` fell back to
            the CPU; empty otherwise.
    """

    name: str
    xp: Any
    ndimage: Any
    reason: str = ""

    def to_device(self, array: Any) -> Any:
        """Return ``array`` as an array of this backend's kind, copying only if needed.

        Args:
            array: A NumPy or CuPy array.

        Returns:
            The same values on this backend's device (``array`` itself if it is already
            there).
        """
        if self.name == "cpu":
            return self.to_host(array)
        return self.xp.asarray(array)

    def to_host(self, array: Any) -> np.ndarray[Any, Any]:
        """Return ``array`` as a NumPy array in host memory, copying only if needed.

        Args:
            array: A NumPy or CuPy array.

        Returns:
            A NumPy array with the same values (``array`` itself if it is NumPy).
        """
        if isinstance(array, np.ndarray):
            return array
        host: np.ndarray[Any, Any] = of(array).xp.asnumpy(array)
        return host

    def synchronize(self) -> None:
        """Wait until all work queued on this backend's device has finished (CPU: no-op)."""
        if self.name == "gpu":
            self.xp.cuda.Device().synchronize()


CPU = Backend(name="cpu", xp=np, ndimage=_scipy_ndimage)
"""The NumPy backend."""

_gpu: Backend | None = None


def select_backend(device: str = "auto") -> Backend:
    """Choose the backend for a run.

    ``"gpu"`` is usable when ``cupy`` imports, the CUDA runtime reports at least one
    device, and a small kernel compiles and runs on it (the last step catches a missing
    CUDA runtime library or header set, which only shows when the first kernel is built).

    Args:
        device: ``"cpu"``; ``"gpu"``; or ``"auto"``, the graphics card if usable, else the
            CPU.

    Returns:
        The backend. With ``"auto"`` and no usable graphics card, the CPU backend with
        :attr:`Backend.reason` set; the reason is also logged at INFO level.

    Raises:
        ValueError: ``device`` is not one of ``"auto"``, ``"cpu"``, ``"gpu"``.
        RuntimeError: ``device`` is ``"gpu"`` and no CUDA device is usable; the message
            gives the reason. ``"auto"`` never raises.
    """
    if device not in DEVICES:
        raise ValueError(f"device must be one of {', '.join(DEVICES)}, got {device!r}")
    if device == "cpu":
        return CPU
    backend, reason = _probe_gpu()
    if backend is not None:
        return backend
    if device == "gpu":
        raise RuntimeError(f"no usable CUDA device: {reason}")
    _LOG.info("using the CPU backend: %s", reason)
    return Backend(name="cpu", xp=np, ndimage=_scipy_ndimage, reason=reason)


def of(array: Any) -> Backend:
    """Return the backend an existing array belongs to, by its type.

    Args:
        array: A NumPy or CuPy array.

    Returns:
        :data:`CPU` for a NumPy array, the GPU backend for a CuPy array.

    Raises:
        TypeError: ``array`` is neither a NumPy nor a CuPy array.
    """
    if isinstance(array, np.ndarray):
        return CPU
    cupy = sys.modules.get("cupy")
    if cupy is not None and isinstance(array, cupy.ndarray):
        return _gpu_backend(cupy)
    raise TypeError(f"expected a numpy or cupy array, got {type(array).__name__}")


def memory_estimate_bytes(image_shape: tuple[int, ...], params: Params) -> int:
    """Estimate, as an upper bound, the working-set bytes :func:`correct` needs for an image.

    Counted in float32 planes of the image size (one plane is 4 bytes per pixel; an RGB
    image is 3 planes) at the peak of :func:`prototype.pipeline.correct` on a device,
    which is the finest EXPAND of the pyramid collapse at the end of the multiscale
    fusion (located with a counting allocator in WP1.2):

    - 25 planes of results still alive: the device copy of the input, the compensated
      and white-balanced images and the two fusion inputs (15), and the ten weight maps
      that :class:`prototype.pipeline.Weights` holds (10);
    - 13 1/3 planes of fusion pyramids: the fused pyramid being collapsed, and the last
      input's Laplacian pyramid and blended pyramid, still referenced (4 planes each,
      an RGB level 0 of 3 planes plus at most 1/3 of that again for the coarser levels),
      and its weight's Gaussian pyramid (4/3);
    - 11 3/4 planes of EXPAND temporaries at the finest level: the zero-stuffed image (3),
      its blur's row pass and result (3 + 3), the sample indicator and its blur (1 + 1),
      and the collapsed coarser level being expanded (3/4).

    That is 50 1/12 planes; the bound multiplies it by 1.25 for the memory pool's
    rounding and fragmentation (measured at 8 percent on this machine) and for pyramids
    of odd sizes, and adds 1 MiB for the pipeline's constant arrays and the pool's
    rounding of each allocation to 512 bytes, which dominate only for tiny images. It
    does not count the CUDA context or library workspaces (not part of the working set;
    they already exist when the decision is taken, so compare this figure with the
    device's free memory). The CPU path holds the same arrays, so the figure also bounds
    its arrays in RAM, but not the interpreter and libraries. No current parameter
    changes the count (the pyramid depth only moves the 4/3 bound's tightness), so
    ``params`` is accepted for a future one and is not read.

    Args:
        image_shape: The image shape; the first two entries are height and width.
        params: The parameter set (not read by the current count).

    Returns:
        The estimate in bytes.
    """
    del params  # no current parameter changes the working set (see above)
    pixels = int(image_shape[0]) * int(image_shape[1])
    return math.ceil(_PEAK_PLANES * _ESTIMATE_MARGIN * 4 * pixels) + _FIXED_BYTES


def _probe_gpu() -> tuple[Backend | None, str]:
    """Return the GPU backend if CuPy and a CUDA device are usable, else ``None`` and why."""
    try:
        cupy = importlib.import_module("cupy")
    except ImportError as exc:
        return None, f"cupy is not installed ({_one_line(exc)})"
    except Exception as exc:  # an installed CuPy that fails to initialise (a DLL, a driver)
        return None, f"cupy failed to import ({type(exc).__name__}: {_one_line(exc)})"
    try:
        count = int(cupy.cuda.runtime.getDeviceCount())
    except Exception as exc:  # any CUDA runtime failure means "not usable"
        return None, f"the CUDA runtime did not answer ({_one_line(exc)})"
    if count < 1:
        return None, "the CUDA runtime reports no device"
    try:
        probe = cupy.arange(4, dtype=cupy.float32) + cupy.float32(1.0)
        if float(probe.sum()) != 10.0:
            return None, "a test kernel on the CUDA device returned a wrong result"
    except Exception as exc:  # a missing runtime library or header shows here
        return None, f"a test kernel failed on the CUDA device ({_one_line(exc)})"
    try:
        return _gpu_backend(cupy), ""
    except Exception as exc:  # an incomplete CuPy installation without cupyx
        return None, f"cupyx.scipy.ndimage did not import ({_one_line(exc)})"


def _gpu_backend(cupy: ModuleType) -> Backend:
    """The (cached) GPU backend for an imported ``cupy`` module."""
    global _gpu
    if _gpu is None or _gpu.xp is not cupy:
        ndimage = importlib.import_module("cupyx.scipy.ndimage")
        _gpu = Backend(name="gpu", xp=cupy, ndimage=ndimage)
    return _gpu


def _one_line(exc: BaseException) -> str:
    """The exception's message on one line (its class name when the message is empty)."""
    return " ".join(str(exc).split()) or type(exc).__name__
