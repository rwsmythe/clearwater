"""Channel compensation, spec 6.2 step 1: Ancuti 2018 (6.3.1) and 3C (6.3.2), as step functions.

Each method is split as AD-6 and AD-7 stage it, so that a render can run on supplied
(smoothed) values (spec 7.1, 7.2 step 3) and never measures a whole-frame value itself:

- **Ancuti 2018.** Measure: the channel means of the input (``clearwater.core.channel_means``)
  and :func:`cap_statistics`. Closed form: :func:`effective_alphas` (the gain cap, D50, D52,
  D100). Render: :func:`compensate_ancuti2018` from supplied means and alphas.
- **3C.** No whole-frame statistic and no gain cap (D49): :func:`compensate_c3` is the render.

Every function mirrors the ``tools/prototype/pipeline`` function named in its docstring with
the same operations (array methods and operators where the prototype called ``xp``), so on the
same device it matches the prototype bit for bit. Image data stays float32 (D39); the scalar
reductions accumulate in float64 through the core helpers, as the prototype's do. The functions
take a :class:`~clearwater.core.CoreBackend` (DR-37 b) and an IF-1 array of that backend; the
array's [0, 1] range is the producer's contract (IF-1) and is not re-read here.

Validation (DR-19 items 1 and 2, the X-4 rule): a step validates only the values it derives
from its own parameters and the image size, before any array work, and reports a failure as
one ValueError naming the parameter. Supplied values (means, statistics, alphas) of the wrong
length or keys, or not finite, raise one ValueError naming the argument. A parameter's own
range is the schema's (WP3.4) and is not re-checked.
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence

import numpy as np

from clearwater.core import (
    CoreBackend,
    check_sigma,
    mean,
    rgb_to_ycbcr_matrix,
    spatial_sigma,
)
from clearwater.interfaces.backend import ArrayBackend
from clearwater.interfaces.image import Array

_CHANNEL_INDEX = {"red": 0, "blue": 2}
"""The channel each compensated channel name refers to (the prototype's ``Statistics`` keys)."""

# The exact inverse of the BT.709 full-range RGB -> YCbCr matrix, built in float64 and cast
# once, as the prototype's ``YCBCR_TO_RGB.astype(float32)``.
_YCBCR_TO_RGB_709 = np.linalg.inv(rgb_to_ycbcr_matrix("bt709")).astype(np.float32)


def _compensated_channels(*, blue_compensation: bool) -> tuple[str, ...]:
    """Return the channels Ancuti 2018 compensates: red, and blue when it is on (D51).

    Args:
        blue_compensation: Whether blue compensation is on (off by default, D51).

    Returns:
        ``("red",)`` or ``("red", "blue")``.
    """
    return ("red", "blue") if blue_compensation else ("red",)


def cap_statistics(backend: ArrayBackend, a: Array, *, blue_compensation: bool) -> dict[str, float]:
    """Measure the gain-cap statistic ``mean((1 - I_c) * I_g)`` of each compensated channel.

    Mirrors ``pipeline._cap_statistic((1.0 - image[..., c]) * green)`` in
    ``pipeline.compensate_ancuti2018``: a whole-frame mean of the input, accumulated in
    float64 (``clearwater.core.mean``). It is source-only (AD-7): it depends on the input
    image alone. Each channel is a device-to-host SYNC POINT (one scalar).

    Args:
        backend: The core backend ``a`` lives on.
        a: The input image, float32 ``(H, W, 3)``.
        blue_compensation: Whether blue is compensated too (D51).

    Returns:
        The statistic per compensated channel, keyed ``"red"`` (and ``"blue"``).

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not float32 or not ``(H, W, 3)``.
    """
    core = _core(backend)
    core.check_rgb(a)
    green = a[..., 1]
    return {
        name: mean(core, (1.0 - a[..., _CHANNEL_INDEX[name]]) * green)
        for name in _compensated_channels(blue_compensation=blue_compensation)
    }


def effective_alphas(
    *,
    means: Sequence[float],
    cap_statistics: Mapping[str, float],
    alpha: float,
    blue_compensation: bool,
    red_gain_cap: float | None,
    blue_gain_cap: float | None,
) -> dict[str, float]:
    """Return the compensation strength per channel after the gain cap (spec 6.3.1, D50, D52).

    Mirrors ``pipeline.compensate_ancuti2018``: the mean amount added to channel c per unit
    alpha is ``added_per_alpha = (mean_g - mean_c) * cap_statistic_c``; when the channel's cap
    is not None and ``added_per_alpha > 0``, the strength becomes
    ``min(alpha, cap * mean_c / added_per_alpha)``, so the mean added amount does not exceed
    ``cap`` times the channel's original mean. Red takes ``red_gain_cap`` and blue
    ``blue_gain_cap`` (separate caps, D52); None disables a cap (D100, AD-26). Pure Python on
    the supplied values (closed form, AD-7); the result is the capped alpha AD-6 smooths.

    Args:
        means: The R, G and B means of the compensation input.
        cap_statistics: The statistic of :func:`cap_statistics` per channel; it must hold every
            compensated channel (other keys are ignored).
        alpha: The requested compensation strength (6.3.1, paper value 1).
        blue_compensation: Whether blue is compensated too (D51).
        red_gain_cap: The red gain cap, or None for no cap.
        blue_gain_cap: The blue gain cap, or None for no cap.

    Returns:
        The effective alpha per compensated channel, keyed ``"red"`` (and ``"blue"``).

    Raises:
        ValueError: ``means`` is not three finite numbers, or ``cap_statistics`` lacks a
            compensated channel or holds a non-finite value; the message names the argument.
    """
    supplied = _triple(means, "means")
    caps = {"red": red_gain_cap, "blue": blue_gain_cap}
    alphas: dict[str, float] = {}
    for name in _compensated_channels(blue_compensation=blue_compensation):
        if name not in cap_statistics:
            raise ValueError(
                f"cap_statistics has no {name!r} value; it has {sorted(cap_statistics, key=repr)}"
            )
        statistic = _finite(cap_statistics[name], f"cap_statistics[{name!r}]")
        index = _CHANNEL_INDEX[name]
        added_per_alpha = (supplied[1] - supplied[index]) * statistic
        effective = alpha
        cap = caps[name]
        if cap is not None and added_per_alpha > 0.0:
            effective = min(effective, cap * supplied[index] / added_per_alpha)
        alphas[name] = float(effective)
    return alphas


def compensate_ancuti2018(
    backend: ArrayBackend, a: Array, *, means: Sequence[float], alphas: Mapping[str, float]
) -> Array:
    """Compensate red (and blue) per [A18] from supplied means and alphas (spec 6.3.1).

    ``I_rc = I_r + alpha_r * (mean_g - mean_r) * (1 - I_r) * I_g`` and, when ``alphas`` holds
    blue, ``I_bc = I_b + alpha_b * (mean_g - mean_b) * (1 - I_b) * I_g``; each compensated
    channel is clipped to [0, 1]; green, and blue when not compensated, are unchanged. Mirrors
    ``pipeline.compensate_ancuti2018`` with ``Statistics(compensation_means=means,
    compensation_alpha=alphas)``: it measures nothing (the render of AD-6 stage 1).

    Args:
        backend: The core backend ``a`` lives on.
        a: The input image, float32 ``(H, W, 3)``.
        means: The R, G and B means of the input (measured or smoothed).
        alphas: The effective alpha per compensated channel (:func:`effective_alphas`):
            ``"red"``, plus ``"blue"`` exactly when blue is compensated.

    Returns:
        The compensated image, float32 ``(H, W, 3)``, a new array.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not float32 or not ``(H, W, 3)``; ``means`` is not three finite
            numbers; ``alphas`` is not ``{"red"}`` or ``{"red", "blue"}`` with finite values.
    """
    core = _core(backend)
    core.check_rgb(a)
    supplied = _triple(means, "means")
    if set(alphas) not in ({"red"}, {"red", "blue"}):
        raise ValueError(
            f"alphas must name 'red' and optionally 'blue', got {sorted(alphas, key=repr)}"
        )
    strengths = {name: _finite(value, f"alphas[{name!r}]") for name, value in alphas.items()}
    green = a[..., 1]
    out = a.copy()
    for name in ("red", "blue"):
        if name not in strengths:
            continue
        index = _CHANNEL_INDEX[name]
        difference = supplied[1] - supplied[index]
        shape = (1.0 - a[..., index]) * green
        out[..., index] = (a[..., index] + (strengths[name] * difference) * shape).clip(0.0, 1.0)
    return out


def compensate_c3(
    backend: ArrayBackend,
    a: Array,
    *,
    kappa: float,
    lambda_: float,
    c3_strength: float,
    c3_kernel_fraction: float,
    c3_mask_threshold: float,
    c3_mask_smooth_fraction: float,
) -> Array:
    """Compensate the opponent channels per [3C] in BT.709 full-range YCbCr (spec 6.3.2).

    ``Cr' = Cr - kappa * M * G{Cr}`` and ``Cb' = Cb - lambda * M * G{Cb}`` with
    ``kappa = c3_strength * kappa`` and ``lambda = c3_strength * lambda_`` (D48); Y is
    unchanged. YCbCr is always BT.709 full range, whatever the source's matrix (D47). The mask
    M is 0 where ``mean(R, G, B) > c3_mask_threshold`` and 1 elsewhere, smoothed by a Gaussian
    of ``c3_mask_smooth_fraction``; ``G{}`` is a Gaussian of ``c3_kernel_fraction`` (both
    fractions of the short side, D56). The output is ``RGB + YCbCr_to_RGB @ (0, dCb, dCr)``
    clipped to [0, 1], so a pixel with ``M = 0`` is bit-identical to its input. No gain cap
    applies (D49) and nothing is measured over the whole frame. Mirrors
    ``pipeline.compensate_c3``.

    The two fractions are validated before any array work (X-4): each sigma must be finite,
    positive and within the core's filter bound (``clearwater.core.check_sigma``).

    Args:
        backend: The core backend ``a`` lives on.
        a: The input image, float32 ``(H, W, 3)``.
        kappa: The Cr strength (paper value 1.0).
        lambda_: The Cb strength (paper value 0.7).
        c3_strength: The Basic slider scaling both (D48).
        c3_kernel_fraction: The sigma of the local mean ``G{}``, fraction of the short side.
        c3_mask_threshold: The mean RGB above which a pixel is protected (M = 0).
        c3_mask_smooth_fraction: The sigma that smooths the mask, fraction of the short side.

    Returns:
        The compensated image, float32 ``(H, W, 3)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not float32 or not ``(H, W, 3)``, or a fraction gives an unusable
            sigma at this image size (the message names the parameter).
    """
    core = _core(backend)
    core.check_rgb(a)
    kernel_sigma = _derived_sigma(a.shape, "c3_kernel_fraction", c3_kernel_fraction)
    mask_sigma = _derived_sigma(a.shape, "c3_mask_smooth_fraction", c3_mask_smooth_fraction)
    # Python floats, so a NumPy-scalar parameter cannot widen the float32 image arithmetic (D39)
    strength = float(c3_strength)
    kappa_effective = strength * float(kappa)
    lambda_effective = strength * float(lambda_)
    threshold = float(c3_mask_threshold)
    to_rgb = core.asarray(_YCBCR_TO_RGB_709)
    ycbcr = core.rgb_to_ycbcr(a, "bt709", "full")
    bright = a.mean(axis=2, dtype=np.float32) > threshold
    mask = core.gaussian_blur((~bright).astype(np.float32), mask_sigma)
    delta_cb = -lambda_effective * mask * core.gaussian_blur(ycbcr[..., 1], kernel_sigma)
    delta_cr = -kappa_effective * mask * core.gaussian_blur(ycbcr[..., 2], kernel_sigma)
    delta = delta_cb[..., None] * to_rgb[:, 1] + delta_cr[..., None] * to_rgb[:, 2]
    out: Array = (a + delta).clip(0.0, 1.0).astype(np.float32, copy=False)
    return out


def _core(backend: ArrayBackend) -> CoreBackend:
    """Return ``backend`` as a :class:`CoreBackend`, or raise TypeError."""
    if not isinstance(backend, CoreBackend):
        raise TypeError(f"expected a clearwater.core backend, got {type(backend).__name__}")
    return backend


def _derived_sigma(shape: tuple[int, ...], name: str, fraction: float) -> float:
    """Return the sigma in pixels of a spatial fraction, or raise the X-4 ValueError.

    The core's ``check_sigma`` decides (finite, positive, radius within its bound); its
    message, which names no parameter, is re-raised prefixed with the parameter, its value and
    the short side. An OverflowError from it (a finite sigma near the float maximum, whose
    ``4 * sigma`` is infinite) is reported the same way.
    """
    sigma = spatial_sigma(shape, fraction)
    try:
        check_sigma(sigma)
    except (ValueError, OverflowError) as exc:
        raise ValueError(
            f"{name}={fraction!r} gives a sigma of {sigma:.6g} px at the short side "
            f"{min(shape[0], shape[1])} px; {exc}"
        ) from exc
    return sigma


def _finite(value: float, name: str) -> float:
    """Return ``value`` as a Python float, or raise ValueError naming ``name``."""
    number = float(value)
    if not math.isfinite(number):
        raise ValueError(f"{name} must be finite, got {value!r}")
    return number


def _triple(values: Sequence[float], name: str) -> tuple[float, float, float]:
    """Return three finite values as Python floats, or raise ValueError naming ``name``."""
    if len(values) != 3:
        raise ValueError(f"{name} needs 3 values, got {len(values)}")
    return (
        _finite(values[0], f"{name}[0]"),
        _finite(values[1], f"{name}[1]"),
        _finite(values[2], f"{name}[2]"),
    )
