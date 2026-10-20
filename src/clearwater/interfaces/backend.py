"""IF-2: the array backend.

The correction core runs one code path on NumPy (CPU) or CuPy (GPU) through the
:class:`ArrayBackend` protocol (AD-1, D107). Spatial parameters are fractions of the short side
(D56); the backend converts them to pixels. CuPy is never imported here.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable

from numpy.typing import ArrayLike, DTypeLike, NDArray

from .image import Array
from .settings import Settings


@runtime_checkable
class ArrayBackend(Protocol):
    """The array operations the correction core needs, on one device (IF-2).

    Attributes:
        name: ``"numpy"`` or ``"cupy"``.
        device: The device the arrays live on, for example ``"cpu"`` or ``"cuda:0"``.
    """

    name: str
    device: str

    def asarray(self, a: ArrayLike, dtype: DTypeLike = ...) -> Array:
        """Convert ``a`` to a backend array.

        Args:
            a: The input.
            dtype: The element type; the product uses float32.

        Returns:
            The backend array.
        """
        ...

    def to_host(self, a: Array) -> NDArray[Any]:
        """Return ``a`` as a NumPy array on the host.

        Args:
            a: A backend array.

        Returns:
            The NumPy array.
        """
        ...

    def gaussian_blur(self, a: Array, sigma_px: float) -> Array:
        """Blur ``a`` with a Gaussian: symmetric borders, 4-sigma truncation.

        Args:
            a: The image array.
            sigma_px: The standard deviation in pixels.

        Returns:
            The blurred array.
        """
        ...

    def pyramid_reduce(self, a: Array) -> Array:
        """Reduce by one pyramid level: [1 4 6 4 1]/16, keeping even rows and columns.

        Args:
            a: The image array.

        Returns:
            The reduced array.
        """
        ...

    def pyramid_expand(self, a: Array, shape: tuple[int, int]) -> Array:
        """Expand by one pyramid level: zero-insert, same filter, normalised.

        Args:
            a: The image array.
            shape: The target ``(height, width)``.

        Returns:
            The expanded array.
        """
        ...

    def rgb_to_ycbcr(self, a: Array, matrix: str, range_: str) -> Array:
        """Convert RGB to YCbCr.

        Args:
            a: The RGB array.
            matrix: The colour matrix name.
            range_: ``"full"`` or ``"limited"``.

        Returns:
            The YCbCr array.
        """
        ...

    def ycbcr_to_rgb(self, a: Array, matrix: str, range_: str) -> Array:
        """Convert YCbCr to RGB.

        Args:
            a: The YCbCr array.
            matrix: The colour matrix name.
            range_: ``"full"`` or ``"limited"``.

        Returns:
            The RGB array.
        """
        ...

    def percentile(self, a: Array, q: Sequence[float]) -> Array:
        """Return percentiles of ``a`` by linear interpolation (R-7).

        Args:
            a: The array.
            q: The percentiles, 0 to 100.

        Returns:
            The percentile values.
        """
        ...

    def memory_estimate_bytes(self, height: int, width: int, method_id: str) -> int:
        """Estimate the device memory a frame of this size needs.

        Args:
            height: Frame height in pixels.
            width: Frame width in pixels.
            method_id: The correction method id.

        Returns:
            The estimate in bytes.
        """
        ...

    def free_device_bytes(self) -> int | None:
        """Return the free device memory in bytes, or None on CPU."""
        ...


def select_backend(
    settings: Settings, height: int, width: int, method_id: str
) -> tuple[ArrayBackend, str]:
    """Choose the backend for a frame size (IF-2; AD-1, AD-9).

    Implemented by WP3.1; this interface-level definition has no behaviour.

    Args:
        settings: The application settings (``force_cpu``).
        height: Frame height in pixels.
        width: Frame width in pixels.
        method_id: The correction method id.

    Returns:
        The backend and a human reason, such as ``"GPU"``, ``"CPU: forced"`` or
        ``"CPU: estimate 1,982 MiB exceeds free 1,200 MiB"``.

    Raises:
        NotImplementedError: Always; IF-2 ``select_backend`` is implemented by WP3.1.
    """
    raise NotImplementedError("IF-2 select_backend is implemented by WP3.1")
