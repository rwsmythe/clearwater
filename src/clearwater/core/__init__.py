"""The correction core's array layer: IF-2 backends, device choice and image operations.

``select_backend`` picks :class:`NumpyBackend` (CPU) or :class:`CupyBackend` (GPU) for a frame
(AD-1, AD-9, D111); both implement IF-2 ``ArrayBackend`` by one code path (D107).
``backend_for`` returns the backend an image's device names (IF-1 ``Image.device``). The
functions of :mod:`clearwater.core.ops` add the operations IF-2 does not carry. Importing this
package never imports CuPy; only ``clearwater.core`` may import ``cupy`` or ``cupyx`` (plan 8.1,
WP3.1 ruling 1.1).
"""

from __future__ import annotations

from .backend import (
    GAUSSIAN_TRUNCATE,
    MAX_KERNEL_RADIUS,
    CoreBackend,
    CupyBackend,
    NumpyBackend,
    backend_for,
    check_sigma,
    rgb_to_ycbcr_matrix,
    select_backend,
)
from .memory import METHOD_IDS, memory_estimate_bytes
from .ops import (
    channel_means,
    collapse_pyramid,
    gaussian_pyramid,
    laplacian,
    laplacian_pyramid,
    luminance,
    mean,
    pyramid_levels,
    rgb_to_lab,
    spatial_sigma,
)

__all__ = [
    "GAUSSIAN_TRUNCATE",
    "MAX_KERNEL_RADIUS",
    "METHOD_IDS",
    "CoreBackend",
    "CupyBackend",
    "NumpyBackend",
    "backend_for",
    "channel_means",
    "check_sigma",
    "collapse_pyramid",
    "gaussian_pyramid",
    "laplacian",
    "laplacian_pyramid",
    "luminance",
    "mean",
    "memory_estimate_bytes",
    "pyramid_levels",
    "rgb_to_lab",
    "rgb_to_ycbcr_matrix",
    "select_backend",
    "spatial_sigma",
]
