"""The working-set estimate that drives the CPU fallback (AD-1, D111, N4).

The estimate is the prototype's counted formula (``tools/prototype/backend.py``, WP1.2 Part A
and Part B): the peak of the correction core in float32 planes of the frame size, located with a
counting allocator at the finest EXPAND of the fusion pyramid collapse,

- 25 planes of results still alive (the device copy of the input, the compensated and
  white-balanced images and the two fusion inputs, 15; the ten weight maps, 10);
- 13 1/3 planes of fusion pyramids (the fused pyramid, the last input's Laplacian and blended
  pyramids, 4 each; its weight's Gaussian pyramid, 4/3);
- 11 3/4 planes of EXPAND temporaries at the finest level (the zero-stuffed image 3, its blur's
  row pass and result 3 + 3, the sample indicator and its blur 1 + 1, the coarser level 3/4);

50 1/12 planes in all, times 1.25 for the memory pool's rounding and fragmentation and for odd
pyramid sizes, plus 1 MiB for constant arrays and per-allocation rounding. At 4K
(3840 x 2160) that is 1,982 MiB, 1.16x the pool's reserved peak measured in WP1.2 Part B
(AD-1). The CUDA context and library workspaces are not counted: they already exist when the
decision is taken, so the figure is compared with the device's free memory.

Both built-in methods (``c3`` and ``ancuti2018``, IF-3) share the count (WP3.1 brief ruling 3;
the product peak is re-checked by WP3.4). Any other method id is refused, so that a new method
registers its own count instead of being under-estimated (WP3.1 round-0 ruling R0-5).
"""

from __future__ import annotations

import math

METHOD_IDS: tuple[str, ...] = ("c3", "ancuti2018")
"""The method ids the estimate knows (IF-3 ``CorrectionMethod.id``)."""

_PEAK_PLANES = 25.0 + 40.0 / 3.0 + 11.75
_ESTIMATE_MARGIN = 1.25
_FIXED_BYTES = 1024 * 1024


def memory_estimate_bytes(height: int, width: int, method_id: str) -> int:
    """Estimate, as an upper bound, the device memory one frame of this size needs.

    Args:
        height: Frame height in pixels, at least 1.
        width: Frame width in pixels, at least 1.
        method_id: The correction method id, one of :data:`METHOD_IDS`.

    Returns:
        The estimate in bytes.

    Raises:
        ValueError: A size is under 1, or ``method_id`` is not one of :data:`METHOD_IDS`.
    """
    if method_id not in METHOD_IDS:
        raise ValueError(
            f"no memory estimate for method {method_id!r}; known: {', '.join(METHOD_IDS)}"
        )
    if height < 1 or width < 1:
        raise ValueError(f"frame size must be at least 1 x 1, got {height} x {width}")
    pixels = int(height) * int(width)
    return math.ceil(_PEAK_PLANES * _ESTIMATE_MARGIN * 4 * pixels) + _FIXED_BYTES
