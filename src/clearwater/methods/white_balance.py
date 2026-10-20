"""Gray-world white balance with the D99 gain clamp, spec 6.2 step 2, as step functions.

Split as AD-6 and AD-7 stage it, so the render runs on supplied (smoothed) gains:

- Measure: the R, G and B means of the compensated image (``clearwater.core.channel_means``).
- Closed form: :func:`gray_world_gains` (``target / mean_c``, the smoothable gains), then
  :func:`applied_gains`, which applies ``white_balance_strength`` and then the D99 clamp to
  whatever gains it is given (the smoothed ones for video, spec 6.2), never inside a measure.
- Render: :func:`apply_white_balance` from the applied gains.

The closed forms are pure Python on the values of ``pipeline.white_balance``; the render makes
the prototype's operations on the same device, so it matches bit for bit. Supplied values of
the wrong length, or not finite, raise one ValueError naming the argument. The parameters'
own ranges are the schema's (WP3.4) and are not re-checked.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from clearwater.core import CoreBackend
from clearwater.interfaces.backend import ArrayBackend
from clearwater.interfaces.image import Array

_EPS = 1e-6
"""The floor on a channel mean in the gray-world gain (the prototype's ``_EPS``)."""


def gray_world_gains(means: Sequence[float]) -> tuple[float, float, float]:
    """Return the gray-world gains ``target / max(mean_c, 1e-6)``, ``target`` the mean of means.

    Mirrors ``pipeline.white_balance`` (the gains before the strength and the clamp). A channel
    with a mean under 1e-6 is treated as having mean 1e-6; its gain then ends at the clamp in
    :func:`applied_gains`.

    Args:
        means: The R, G and B means of the compensated image (measured or smoothed).

    Returns:
        The three gains.

    Raises:
        ValueError: ``means`` is not three finite numbers.
    """
    supplied = _triple(means, "means")
    target = sum(supplied) / 3.0
    return (
        target / max(supplied[0], _EPS),
        target / max(supplied[1], _EPS),
        target / max(supplied[2], _EPS),
    )


def applied_gains(
    gray_world: Sequence[float],
    *,
    white_balance_strength: float,
    max_white_balance_gain: float,
) -> tuple[tuple[float, float, float], tuple[bool, bool, bool]]:
    """Apply the strength, then the D99 clamp, to gray-world gains (spec 6.2 step 2).

    Requested gain ``1 + s * (g - 1)`` with ``s = white_balance_strength``; applied gain
    ``min(requested, max_white_balance_gain)``. The clamp is an upper limit only and comes after
    the strength. Mirrors ``pipeline.white_balance``.

    Args:
        gray_world: The gray-world gains (:func:`gray_world_gains`, or their smoothed values).
        white_balance_strength: The strength ``s`` (0 leaves the image unchanged).
        max_white_balance_gain: The D99 maximum per-channel gain.

    Returns:
        The applied gains, and per channel whether the clamp lowered the gain.

    Raises:
        ValueError: ``gray_world`` is not three finite numbers.
    """
    supplied = _triple(gray_world, "gray_world")
    requested = tuple(1.0 + white_balance_strength * (g - 1.0) for g in supplied)
    applied = tuple(float(min(g, max_white_balance_gain)) for g in requested)
    return (
        (applied[0], applied[1], applied[2]),
        (requested[0] > applied[0], requested[1] > applied[1], requested[2] > applied[2]),
    )


def apply_white_balance(backend: ArrayBackend, a: Array, gains: Sequence[float]) -> Array:
    """Return ``clip(a * gains, 0, 1)`` with the gains cast to float32 (the render).

    Mirrors the render of ``pipeline.white_balance``. It measures nothing; the gains go to the
    device as one three-value float32 array.

    Args:
        backend: The core backend ``a`` lives on.
        a: The compensated image, float32 ``(H, W, 3)``.
        gains: The applied R, G and B gains (:func:`applied_gains`).

    Returns:
        The white-balanced image, float32 ``(H, W, 3)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not float32 or not ``(H, W, 3)``, or ``gains`` is not three
            finite numbers.
    """
    if not isinstance(backend, CoreBackend):
        raise TypeError(f"expected a clearwater.core backend, got {type(backend).__name__}")
    backend.check_rgb(a)
    device_gains = backend.asarray(_triple(gains, "gains"))
    out: Array = (a * device_gains).clip(0.0, 1.0).astype(np.float32, copy=False)
    return out


def _triple(values: Sequence[float], name: str) -> tuple[float, float, float]:
    """Return three finite values as Python floats, or raise ValueError naming ``name``."""
    if len(values) != 3:
        raise ValueError(f"{name} needs 3 values, got {len(values)}")
    numbers = (float(values[0]), float(values[1]), float(values[2]))
    if not all(math.isfinite(number) for number in numbers):
        raise ValueError(f"{name} must be finite, got {list(values)}")
    return numbers
