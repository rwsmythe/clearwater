"""Fusion inputs, weight maps and the multiscale blend (spec 6.2 steps 3-5) on an IF-2 backend.

The steps shared by both correction methods (``c3`` and ``ancuti2018``, architecture section 3),
after [A18] (C. O. Ancuti et al., "Color Balance and Fusion for Underwater Image Enhancement",
IEEE TIP 27(1), 2018), with ``tools/prototype/pipeline.py`` as the numerical reference:

1. two fusion inputs from the white-balanced image (:func:`fusion_inputs`): the gamma input
   ``I ** gamma`` and the sharpened input ``S = (I + N{I - G*I}) / 2``;
2. three weight maps per input, normalised across the inputs (:func:`weight_maps`);
3. the Laplacian-pyramid blend (:func:`multiscale_fusion`).

Measure and render (AD-4, AD-6). The two whole-frame statistics of this stage are measured by
their own functions, :func:`normalisation_bounds` (the bounds of N{}) and
:func:`saliency_reference` (one input's mean Lab vector), and SUPPLIED to the render functions,
which never measure a whole-frame value: so the preview and the export, rendered from the same
supplied values, agree by construction (V8). The measuring functions are the only device-to-host
SYNC POINTS of this module: :func:`normalisation_bounds` reads two values, and
:func:`saliency_reference` reads three (``clearwater.core.channel_means``).

The N{} floor (AD-4 as amended 2026-10-20, DR-14): when the supplied bounds are closer than
:data:`NORMALISATION_RANGE_FLOOR`, :func:`fusion_inputs` widens them symmetrically about their
midpoint to that range, so a flat image still stretches to 0.5 and a near-flat one is amplified
at most ``1 / 0.02`` times. It replaces the prototype's rule (bounds closer than 1e-6 give 0.5).

Derived values (DR-19 under the shared rule X-4): each step validates only the values it
derives from its own parameters and the image size, here the three fusion sigmas, before any
array work. A failure is one ValueError naming the parameter, its value and the short side;
the support bound is :func:`clearwater.core.check_sigma`'s, re-raised with the parameter named.
A parameter's own range is the schema's (WP3.4).

Conventions: every function takes a ``clearwater.core`` backend (:class:`CoreBackend`) and its
arrays; an image is a float32 ``(H, W, 3)`` RGB array in [0, 1] (IF-1) and a map is float32
``(H, W)``; every result is float32 on the backend's device. Inputs are checked for backend,
dtype and shape only: a value-range check would read the device (the prototype's per-step
minimum and maximum are not carried). Every spatial parameter is a fraction of the short side,
turned into pixels by :func:`clearwater.core.spatial_sigma` (spec 6.6, D56). Scalar parameters
are taken as Python floats, so they meet the float32 image data as float32 scalars (D39).
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np

from clearwater.core import (
    CoreBackend,
    channel_means,
    check_sigma,
    collapse_pyramid,
    gaussian_pyramid,
    laplacian,
    laplacian_pyramid,
    luminance,
    pyramid_levels,
    rgb_to_lab,
    spatial_sigma,
)
from clearwater.interfaces.backend import ArrayBackend
from clearwater.interfaces.image import Array

NORMALISATION_RANGE_FLOOR = 0.02
"""The smallest range of the N{} bounds :func:`fusion_inputs` stretches over (AD-4, DR-14).

Measured ranges on the analysis proxy are 0.028-0.64 (WP1.4b claim 9), so the floor binds on
none of them. Spec 6.7 lists no control for it.
"""

_FLOAT32_MAX = float(np.finfo(np.float32).max)


def high_pass(backend: ArrayBackend, a: Array, *, sharpen_blur_fraction: float) -> Array:
    """Return the high-pass ``I - G*I`` whose stretch N{} gives fusion input 2.

    ``G*I`` is the Gaussian blur of sigma ``sharpen_blur_fraction`` of the short side
    (``pipeline.high_pass_of``).

    Args:
        backend: The backend ``a`` lives on.
        a: The white-balanced image.
        sharpen_blur_fraction: Sigma of the sharpening blur, as a fraction of the short side.

    Returns:
        The high-pass, float32, ``(H, W, 3)``, values in about [-1, 1].

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not a float32 ``(H, W, 3)`` array, or the derived sigma is
            unusable (the message names ``sharpen_blur_fraction``).
    """
    _check_image(backend, a)
    sigma = _derived_sigma("sharpen_blur_fraction", sharpen_blur_fraction, a.shape)
    return _high_pass(backend, a, sigma)


def normalisation_bounds(
    backend: ArrayBackend,
    a: Array,
    *,
    sharpen_blur_fraction: float,
    normalisation_low: float,
    normalisation_high: float,
) -> tuple[float, float]:
    """Measure the bounds of the histogram stretch N{} of fusion input 2 (AD-4).

    The ``normalisation_low`` and ``normalisation_high`` percentiles (0-100, linear
    interpolation) of :func:`high_pass`, taken jointly over all pixels and channels ([A18]: "a
    unique shifting and scaling factor"). IF-2 ``percentile`` interpolates in float64 and casts
    to float32 once, so each bound is the prototype's float64 bound rounded to float32. A
    device-to-host SYNC POINT: the two values are read back as Python floats.

    Args:
        backend: The backend ``a`` lives on.
        a: The white-balanced image (the analysis proxy, AD-4, AD-5).
        sharpen_blur_fraction: Sigma of the sharpening blur, as a fraction of the short side.
        normalisation_low: The lower percentile.
        normalisation_high: The upper percentile.

    Returns:
        The low and the high bound.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not a float32 ``(H, W, 3)`` array, the derived sigma is unusable,
            or a percentile lies outside 0-100.
    """
    hp = high_pass(backend, a, sharpen_blur_fraction=sharpen_blur_fraction)
    q = [float(normalisation_low), float(normalisation_high)]
    values = backend.to_host(backend.percentile(hp, q)).tolist()
    return float(values[0]), float(values[1])


def fusion_inputs(
    backend: ArrayBackend,
    a: Array,
    *,
    gamma: float,
    sharpen_strength: float,
    sharpen_blur_fraction: float,
    bounds: Sequence[float],
) -> tuple[Array, Array]:
    """Derive the two fusion inputs from the white-balanced image (spec 6.2 step 3).

    Input 1: ``I ** gamma``. Input 2: ``S = (I + N{I - G*I}) / 2`` with
    ``N{x} = clip((x - low) / (high - low), 0, 1)`` on the SUPPLIED bounds (never measured here,
    AD-4), widened about their midpoint to :data:`NORMALISATION_RANGE_FLOOR` when they are
    closer; ``sharpen_strength`` s then gives ``I + s * (S - I)``. Both inputs are clipped to
    [0, 1]. The prototype's code clips input 2 only; for ``I`` in [0, 1] and ``gamma >= 0`` the
    clip of input 1 changes no value.

    Args:
        backend: The backend ``a`` lives on.
        a: The white-balanced image.
        gamma: The exponent of input 1.
        sharpen_strength: The strength of input 2: 1 gives the paper's S, 0 gives ``I``.
        sharpen_blur_fraction: Sigma of the sharpening blur, as a fraction of the short side.
        bounds: The low and high bound of N{} (:func:`normalisation_bounds`, possibly
            smoothed).

    Returns:
        Input 1 (gamma) and input 2 (sharpened), float32, ``(H, W, 3)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not a float32 ``(H, W, 3)`` array, the derived sigma is unusable,
            or ``bounds`` is not two finite values with ``low <= high`` whose values and
            range lie in the float32 range (the message names ``bounds``).
    """
    _check_image(backend, a)
    sigma = _derived_sigma("sharpen_blur_fraction", sharpen_blur_fraction, a.shape)
    low, high = _floored(*_checked_bounds(bounds))
    input1: Array = (a ** np.float32(float(gamma))).clip(0.0, 1.0)
    stretched = ((_high_pass(backend, a, sigma) - low) / (high - low)).clip(0.0, 1.0)
    sharpened = (a + stretched) / 2.0
    input2: Array = (a + float(sharpen_strength) * (sharpened - a)).clip(0.0, 1.0)
    return input1, input2


def saliency_reference(backend: ArrayBackend, a: Array) -> tuple[float, float, float]:
    """Measure the saliency reference of one fusion input: its mean Lab vector ``I_mu``.

    The mean of each channel of :func:`clearwater.core.rgb_to_lab` accumulated in float64 and
    rounded to float32 (``pipeline.saliency_reference``), returned as three Python floats. A
    device-to-host SYNC POINT (``channel_means``).

    Args:
        backend: The backend ``a`` lives on.
        a: A fusion input.

    Returns:
        The mean L*, a* and b*.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not a float32 ``(H, W, 3)`` array.
    """
    _check_image(backend, a)
    means = channel_means(backend, rgb_to_lab(backend, a))
    return float(np.float32(means[0])), float(np.float32(means[1])), float(np.float32(means[2]))


def laplacian_weight(backend: ArrayBackend, a: Array, *, laplacian_fraction: float) -> Array:
    """Return the Laplacian contrast weight ``W_L = |sigma^2 * Lap(G_sigma * Y)|`` of one input.

    ``Y`` is the BT.709 luma. [A18] takes the absolute Laplacian of the luminance at the pixel
    scale; spec 6.6 (D56) makes the Laplacian a fraction of the short side, so this is the
    prototype's DELIBERATE ADAPTATION: the discrete 5-point Laplacian of the luma smoothed by a
    Gaussian of sigma ``laplacian_fraction`` of the short side, times sigma squared (scale
    normalisation, so the weight keeps its size relative to the other two at every resolution).

    Args:
        backend: The backend ``a`` lives on.
        a: A fusion input.
        laplacian_fraction: Sigma of the smoothing, as a fraction of the short side.

    Returns:
        W_L, float32, ``(H, W)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not a float32 ``(H, W, 3)`` array, or the derived sigma is
            unusable (the message names ``laplacian_fraction``).
    """
    _check_image(backend, a)
    sigma = _derived_sigma("laplacian_fraction", laplacian_fraction, a.shape)
    return _laplacian_weight(backend, a, sigma)


def saliency_weight(
    backend: ArrayBackend,
    a: Array,
    *,
    saliency_blur_fraction: float,
    saliency_mean: Sequence[float],
) -> Array:
    """Return the saliency weight ``W_S = ||I_mu - I_whc|| / 100`` of one input.

    The frequency-tuned saliency of Achanta et al. (CVPR 2009): the Euclidean distance in
    CIELAB between the supplied mean Lab vector ``I_mu`` (:func:`saliency_reference`) and the
    Lab image blurred by a Gaussian of sigma ``saliency_blur_fraction`` of the short side,
    divided by 100 so that L* spans [0, 1].

    Args:
        backend: The backend ``a`` lives on.
        a: A fusion input.
        saliency_blur_fraction: Sigma of the blur, as a fraction of the short side.
        saliency_mean: The input's mean L*, a* and b* (cast to float32).

    Returns:
        W_S, float32, ``(H, W)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not a float32 ``(H, W, 3)`` array, the derived sigma is unusable
            (the message names ``saliency_blur_fraction``), or ``saliency_mean`` is not three
            finite values.
    """
    _check_image(backend, a)
    sigma = _derived_sigma("saliency_blur_fraction", saliency_blur_fraction, a.shape)
    mean = _checked_triple("saliency_mean", saliency_mean)
    return _saliency_weight(backend, a, sigma, mean)


def saturation_weight(backend: ArrayBackend, a: Array) -> Array:
    """Return the saturation weight ``W_Sat`` of one input: the RMS deviation of R, G, B from Y.

    ``W_Sat = sqrt(((R - Y)^2 + (G - Y)^2 + (B - Y)^2) / 3)`` with ``Y`` the BT.709 luma
    ([A18]).

    Args:
        backend: The backend ``a`` lives on.
        a: A fusion input.

    Returns:
        W_Sat, float32, ``(H, W)``.

    Raises:
        TypeError: ``backend`` is not a core backend or ``a`` is not one of its arrays.
        ValueError: ``a`` is not a float32 ``(H, W, 3)`` array.
    """
    _check_image(backend, a)
    luma = luminance(backend, a)
    out: Array = (((a - luma[..., None]) ** 2).mean(axis=2)) ** 0.5
    return out


def weight_maps(
    backend: ArrayBackend,
    inputs: Sequence[Array],
    *,
    laplacian_fraction: float,
    saliency_blur_fraction: float,
    weight_delta: float,
    saliency_means: Sequence[Sequence[float]],
) -> tuple[Array, ...]:
    """Return the normalised weight map of each fusion input (spec 6.2 step 4).

    Per input k, ``W_k = W_L + W_S + W_Sat`` (:func:`laplacian_weight`, :func:`saliency_weight`
    with the supplied mean, :func:`saturation_weight`); then the paper's regularisation
    ``Wbar_k = (W_k + delta) / (sum_k W_k + K * delta)`` with ``delta = weight_delta`` and K the
    number of inputs. The maps sum to 1 at every pixel up to float32 round-off.

    Args:
        backend: The backend the inputs live on.
        inputs: The fusion inputs, in order (input 1, input 2), at least one, all one shape.
        laplacian_fraction: Sigma of the Laplacian weight's smoothing (short-side fraction).
        saliency_blur_fraction: Sigma of the saliency weight's blur (short-side fraction).
        weight_delta: The regularisation delta.
        saliency_means: The mean Lab vector of each input, in input order
            (:func:`saliency_reference`, possibly smoothed).

    Returns:
        The normalised maps, float32, ``(H, W)``, in input order.

    Raises:
        TypeError: ``backend`` is not a core backend or an input is not one of its arrays.
        ValueError: ``inputs`` is empty or differs in shape, an input is not a float32
            ``(H, W, 3)`` array, a derived sigma is unusable (the message names the parameter),
            or ``saliency_means`` does not hold three finite values per input.
    """
    if not inputs:
        raise ValueError("weight_maps needs at least one input")
    for image in inputs:  # every input checked before any shape is read
        _check_image(backend, image)
    shape = inputs[0].shape
    for image in inputs:
        if image.shape != shape:
            raise ValueError(f"fusion inputs differ in shape: {image.shape} and {shape}")
    laplacian_sigma = _derived_sigma("laplacian_fraction", laplacian_fraction, shape)
    saliency_sigma = _derived_sigma("saliency_blur_fraction", saliency_blur_fraction, shape)
    if len(saliency_means) != len(inputs):
        raise ValueError(
            f"saliency_means holds {len(saliency_means)} vectors for {len(inputs)} fusion inputs"
        )
    means = [_checked_triple(f"saliency_means[{k}]", mean) for k, mean in enumerate(saliency_means)]
    delta = float(weight_delta)
    aggregated = [
        _laplacian_weight(backend, image, laplacian_sigma)
        + _saliency_weight(backend, image, saliency_sigma, mean)
        + saturation_weight(backend, image)
        for image, mean in zip(inputs, means, strict=True)
    ]
    # The prototype's order: (K * delta + W_0) + W_1 + ...
    denominator = aggregated[0] + len(aggregated) * delta
    for w in aggregated[1:]:
        denominator = denominator + w
    return tuple((w + delta) / denominator for w in aggregated)


def multiscale_fusion(
    backend: ArrayBackend,
    inputs: Sequence[Array],
    weights: Sequence[Array],
    *,
    pyramid_min_level_size: int,
) -> Array:
    """Blend the inputs' Laplacian pyramids with their weights' Gaussian pyramids (step 5).

    [A18], after Burt and Adelson: per level ``R_l = sum_k G_l{Wbar_k} * L_l{I_k}``; the fused
    pyramid is collapsed and clipped to [0, 1]. The depth is
    :func:`clearwater.core.pyramid_levels` of the minimum coarsest-level size (spec 6.6, D56).

    Args:
        backend: The backend the arrays live on.
        inputs: The fusion inputs, at least one, all one shape.
        weights: One normalised weight map per input (:func:`weight_maps`).
        pyramid_min_level_size: The minimum short side of the coarsest level, in pixels.

    Returns:
        The fused image, float32, ``(H, W, 3)``.

    Raises:
        TypeError: ``backend`` is not a core backend or an array is not one of its arrays.
        ValueError: The counts or shapes of inputs and weights do not match, an array is not
            float32, or ``pyramid_min_level_size`` is under 1.
    """
    if not inputs or len(inputs) != len(weights):
        raise ValueError(
            f"multiscale_fusion needs one weight map per input, got {len(inputs)} inputs "
            f"and {len(weights)} weights"
        )
    core = _core(backend)
    for image, weight in zip(inputs, weights, strict=True):  # checked before any shape is read
        core.check_rgb(image)
        core.check_spatial(weight)
    shape = inputs[0].shape
    for image, weight in zip(inputs, weights, strict=True):
        if image.shape != shape or weight.shape != shape[:2]:
            raise ValueError(
                f"fusion inputs and weights differ in shape: {image.shape}, {weight.shape}"
            )
    levels = pyramid_levels(shape, pyramid_min_level_size)
    fused: list[Array] = []
    for image, weight in zip(inputs, weights, strict=True):
        pairs = zip(
            gaussian_pyramid(core, weight, levels),
            laplacian_pyramid(core, image, levels),
            strict=True,
        )
        blended = [w[..., None] * band for w, band in pairs]
        fused = blended if not fused else [f + b for f, b in zip(fused, blended, strict=True)]
    out: Array = collapse_pyramid(core, fused).clip(0.0, 1.0)
    return out


def _core(backend: ArrayBackend) -> CoreBackend:
    """Return ``backend`` as a :class:`CoreBackend`, or raise TypeError."""
    if not isinstance(backend, CoreBackend):
        raise TypeError(f"expected a clearwater.core backend, got {type(backend).__name__}")
    return backend


def _check_image(backend: ArrayBackend, a: object) -> None:
    """Raise unless ``a`` is a float32 ``(H, W, 3)`` array of the core backend ``backend``."""
    _core(backend).check_rgb(a)


def _derived_sigma(name: str, fraction: float, shape: tuple[int, ...]) -> float:
    """Return the sigma in pixels of a spatial parameter, or raise X-4's ValueError.

    Raises:
        ValueError: :func:`clearwater.core.check_sigma` refuses the sigma; the message names
            the parameter, its value and the short side, and the core's reason follows.
    """
    sigma = spatial_sigma(shape, fraction)
    try:
        check_sigma(sigma)
    except ValueError as exc:
        raise ValueError(
            f"{name}={fraction!r} gives a sigma of {sigma:.6g} px at the short side "
            f"{min(shape[0], shape[1])} px; {exc}"
        ) from exc
    return sigma


def _checked_bounds(bounds: Sequence[float]) -> tuple[float, float]:
    """Return supplied N{} bounds as two Python floats, or raise ValueError naming ``bounds``.

    The bounds and their range ``high - low`` must be finite in float32, the precision they
    meet the image data in (a finite float64 beyond it becomes infinite there); then the
    floor's midpoint, formed in float64, cannot overflow either.
    """
    if len(bounds) != 2:
        raise ValueError(f"bounds needs 2 values (low, high), got {len(bounds)}")
    low, high = float(bounds[0]), float(bounds[1])
    if not (math.isfinite(low) and math.isfinite(high)):
        raise ValueError(f"bounds is not finite: {[low, high]}")
    if low > high:
        raise ValueError(f"bounds has low {low} above high {high}")
    if max(abs(low), abs(high), high - low) > _FLOAT32_MAX:
        raise ValueError(f"bounds or their range exceed the float32 range: {[low, high]}")
    return low, high


def _floored(low: float, high: float) -> tuple[float, float]:
    """Widen bounds closer than the floor symmetrically about their midpoint (AD-4, DR-14)."""
    if high - low >= NORMALISATION_RANGE_FLOOR:
        return low, high
    mid = (low + high) / 2.0
    half = NORMALISATION_RANGE_FLOOR / 2.0
    return mid - half, mid + half


def _checked_triple(name: str, values: Sequence[float]) -> tuple[float, float, float]:
    """Return a supplied Lab vector as three Python floats, or raise ValueError naming ``name``."""
    if len(values) != 3:
        raise ValueError(f"{name} needs 3 values, got {len(values)}")
    triple = float(values[0]), float(values[1]), float(values[2])
    if not all(math.isfinite(value) for value in triple):
        raise ValueError(f"{name} is not finite: {list(triple)}")
    return triple


def _high_pass(backend: ArrayBackend, a: Array, sigma: float) -> Array:
    """``a - G_sigma * a`` (sigma already validated)."""
    out: Array = a - backend.gaussian_blur(a, sigma)
    return out


def _laplacian_weight(backend: ArrayBackend, a: Array, sigma: float) -> Array:
    """W_L of one input (see :func:`laplacian_weight`; sigma already validated)."""
    # The zero-sum discrete Laplacian of the smoothed luma, so a flat image gives exactly 0.
    log = laplacian(backend, backend.gaussian_blur(luminance(backend, a), sigma))
    out: Array = abs(log * np.float32(sigma**2))
    return out


def _saliency_weight(
    backend: ArrayBackend, a: Array, sigma: float, mean: tuple[float, float, float]
) -> Array:
    """W_S of one input (see :func:`saliency_weight`; sigma and mean already validated)."""
    lab = rgb_to_lab(backend, a)
    reference = backend.asarray(list(mean))
    blurred = backend.gaussian_blur(lab, sigma)
    out: Array = (((blurred - reference) ** 2).sum(axis=2)) ** 0.5 / np.float32(100.0)
    return out
