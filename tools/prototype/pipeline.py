"""The reference correction pipeline (spec sections 6.2 and 6.3), on the CPU with NumPy.

The pipeline runs five steps on one display-encoded RGB image (spec 6.2):

1. channel compensation, Ancuti 2018 (:func:`compensate_ancuti2018`) or 3C
   (:func:`compensate_c3`);
2. gray-world white balance with the D99 gain clamp (:func:`white_balance`);
3. two fusion inputs, gamma and sharpened (:func:`fusion_inputs`);
4. three weight maps per input, normalised across the inputs (:func:`weight_maps`);
5. multiscale Laplacian-pyramid fusion (:func:`multiscale_fusion`);

and a final blend with the original. :func:`correct` runs them all and keeps every
intermediate.

The two reference papers are authoritative over the spec's summaries (spec 6.1):

- [A18] C. O. Ancuti, C. Ancuti, C. De Vleeschouwer, P. Bekaert, "Color Balance and Fusion
  for Underwater Image Enhancement", IEEE TIP 27(1), 2018.
- [3C] C. O. Ancuti, C. Ancuti, C. De Vleeschouwer, M. Sbert, "Color Channel Compensation
  (3C): A Fundamental Pre-Processing Step for Image Enhancement", IEEE TIP 29, 2020.

Conventions: every image is a ``numpy`` float32 array of shape ``(H, W, 3)`` holding
display-encoded RGB in [0, 1] (spec 6.4, 6.5); every single-channel map is float32 of shape
``(H, W)``. Every function is pure (it never modifies its arguments) and does no I/O.
Every spatial parameter is a fraction of the short side and is turned into pixels by
:func:`spatial_sigma` only (spec 6.6, D56). Gaussian filters use symmetric borders
(``scipy.ndimage`` mode ``"reflect"``: ``d c b a | a b c d``) and a support of 4 sigma.
"""

from __future__ import annotations

import itertools
import math
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage

from .params import Params

Image = NDArray[np.float32]
"""A display-encoded RGB image, float32, shape ``(H, W, 3)``, values in [0, 1]."""

Map = NDArray[np.float32]
"""A single-channel map, float32, shape ``(H, W)``."""

_GAUSSIAN_TRUNCATE = 4.0
_EPS = 1e-6

# ITU-R BT.709-6, Part 2 item 3.2-3.3: the luma coefficients K_R and K_B (K_G = 1 - K_R - K_B).
_KR = 0.2126
_KB = 0.0722
_KG = 1.0 - _KR - _KB

RGB_TO_YCBCR = np.array(
    [
        [_KR, _KG, _KB],  # Y  = K_R R + K_G G + K_B B
        [-_KR / (2 * (1 - _KB)), -_KG / (2 * (1 - _KB)), 0.5],  # Cb = (B - Y) / 1.8556
        [0.5, -_KG / (2 * (1 - _KR)), -_KB / (2 * (1 - _KR))],  # Cr = (R - Y) / 1.5748
    ],
    dtype=np.float64,
)
"""BT.709 full-range RGB -> (Y, Cb, Cr) matrix on [0, 1] values (spec 6.3.2, D47).

Source: ITU-R BT.709-6, Part 2, items 3.2 (E'_Y), 3.3 (E'_CB, E'_CR), which define
``Y = 0.2126 R + 0.7152 G + 0.0722 B``, ``Cb = (B - Y) / 1.8556`` and
``Cr = (R - Y) / 1.5748`` on the analogue (unquantised) signals. Full range, no offsets:
Y spans [0, 1] and Cb, Cr span [-0.5, 0.5] centred on 0, so a neutral gray has
``Cb = Cr = 0``. Numerically::

    [[ 0.2126     0.7152     0.0722   ]
     [-0.1145722 -0.3854278  0.5      ]
     [ 0.5       -0.4541529 -0.0458471]]
"""

YCBCR_TO_RGB = np.linalg.inv(RGB_TO_YCBCR)
"""The exact inverse of :data:`RGB_TO_YCBCR` (``R = Y + 1.5748 Cr``, ``B = Y + 1.8556 Cb``)."""

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

# The Burt-Adelson 5-tap binomial kernel [1 4 6 4 1] / 16.
_BINOMIAL_5 = np.array([1.0, 4.0, 6.0, 4.0, 1.0], dtype=np.float32) / np.float32(16.0)


@dataclass(frozen=True)
class CompensationInfo:
    """What the channel compensation step measured and did.

    Attributes:
        method: ``"ancuti2018"`` or ``"c3"``.
        channel_means: Mean of R, G and B of the input image.
        requested: Requested strength per compensated channel: ``{"red": alpha}`` (and
            ``"blue"`` when blue compensation is on) for Ancuti 2018;
            ``{"cr": kappa, "cb": lambda_}`` for 3C.
        effective: Strength actually applied per channel: alpha after the gain cap for
            Ancuti 2018; ``c3_strength * kappa`` and ``c3_strength * lambda_`` for 3C.
        mean_added: Mean change of each RGB channel (``"red"``, ``"green"``, ``"blue"``),
            output minus input, after clipping to [0, 1].
    """

    method: str
    channel_means: tuple[float, float, float]
    requested: dict[str, float]
    effective: dict[str, float]
    mean_added: dict[str, float]


@dataclass(frozen=True)
class WhiteBalanceInfo:
    """What the white balance step measured and did.

    Attributes:
        channel_means: Mean of R, G and B of the image entering the step.
        target: The gray-world target, the mean of the three channel means.
        gray_world_gains: ``target / channel mean`` per channel (full gray world).
        requested_gains: The gains after scaling by ``white_balance_strength``, before
            the clamp.
        applied_gains: The gains used, after the D99 clamp to ``max_white_balance_gain``.
        clamped: Per channel, whether the D99 clamp lowered the gain.
    """

    channel_means: tuple[float, float, float]
    target: float
    gray_world_gains: tuple[float, float, float]
    requested_gains: tuple[float, float, float]
    applied_gains: tuple[float, float, float]
    clamped: tuple[bool, bool, bool]


@dataclass(frozen=True)
class Weights:
    """The weight maps of the fusion inputs, one entry per input in input order.

    Attributes:
        laplacian: Laplacian contrast weight W_L of each input.
        saliency: Saliency weight W_S of each input.
        saturation: Saturation weight W_Sat of each input.
        aggregated: ``W_k = W_L + W_S + W_Sat`` of each input.
        normalised: ``(W_k + delta) / (sum_k W_k + K * delta)`` of each input; they sum
            to 1 at every pixel.
    """

    laplacian: tuple[Map, ...]
    saliency: tuple[Map, ...]
    saturation: tuple[Map, ...]
    aggregated: tuple[Map, ...]
    normalised: tuple[Map, ...]


@dataclass(frozen=True)
class Result:
    """The output of :func:`correct` and every intermediate it computed.

    Attributes:
        output: The final image, after the blend with the original.
        fused: The multiscale fusion result, before the blend.
        compensated: The image after channel compensation (step 1).
        white_balanced: The image after white balance (step 2).
        input1: Fusion input 1, the gamma-corrected image (step 3).
        input2: Fusion input 2, the sharpened image (step 3).
        weights: The six raw weight maps, the two aggregated and the two normalised
            weights (step 4).
        compensation: The compensation step's record.
        white_balance: The white balance step's record.
        params: The parameters used.
    """

    output: Image
    fused: Image
    compensated: Image
    white_balanced: Image
    input1: Image
    input2: Image
    weights: Weights
    compensation: CompensationInfo
    white_balance: WhiteBalanceInfo
    params: Params


def spatial_sigma(image_shape: tuple[int, ...], fraction: float) -> float:
    """Turn a spatial parameter given as a fraction of the short side into pixels (D56).

    This is the single place where the conversion happens, so that every spatial
    parameter scales with the image (spec 6.6). There is no floor: a sigma well under
    one pixel gives a sampled Gaussian close to the identity (``scipy.ndimage`` keeps a
    support of ``round(4 * sigma)`` pixels, so under 1/8 px the kernel is exactly
    ``[1]``), which is the right limit for an image too small to hold that detail.

    Args:
        image_shape: The image shape; the first two entries are height and width.
        fraction: The parameter as a fraction of ``min(height, width)``.

    Returns:
        The parameter in pixels.
    """
    short_side = min(image_shape[0], image_shape[1])
    return fraction * short_side


def compensate_ancuti2018(image: Image, params: Params) -> tuple[Image, CompensationInfo]:
    """Compensate the red (and, when enabled, the blue) channel per [A18] (spec 6.3.1).

    [A18], white-balancing section (the red and blue compensation equations), on values
    in [0, 1], with the channel means taken over the whole input image:

    - ``I_rc(x) = I_r(x) + alpha * (mean_g - mean_r) * (1 - I_r(x)) * I_g(x)``
    - ``I_bc(x) = I_b(x) + alpha * (mean_g - mean_b) * (1 - I_b(x)) * I_g(x)``

    alpha is ``params.alpha`` (paper value 1). The gain cap (spec 6.3.1, D50, D52, D100)
    reduces alpha per channel so that the mean added amount,
    ``alpha * (mean_g - mean_c) * mean((1 - I_c) * I_g)``, does not exceed
    ``cap * mean_c``. The result is clipped to [0, 1]; the green channel is unchanged.

    Args:
        image: The input image.
        params: Uses ``alpha``, ``blue_compensation``, ``red_gain_cap``,
            ``blue_gain_cap``.

    Returns:
        The compensated image and the step's record.
    """
    _check_image(image)
    means = _channel_means(image)
    green = image[..., 1]
    out = image.copy()
    requested: dict[str, float] = {}
    effective: dict[str, float] = {}
    channels = [("red", 0, params.red_gain_cap)]
    if params.blue_compensation:
        channels.append(("blue", 2, params.blue_gain_cap))
    for name, index, cap in channels:
        difference = means[1] - means[index]
        shape = (1.0 - image[..., index]) * green
        added_per_alpha = difference * float(shape.mean(dtype=np.float64))
        alpha = params.alpha
        if cap is not None and added_per_alpha > 0.0:
            alpha = min(alpha, cap * means[index] / added_per_alpha)
        requested[name] = params.alpha
        effective[name] = alpha
        out[..., index] = np.clip(image[..., index] + (alpha * difference) * shape, 0.0, 1.0)
    info = CompensationInfo(
        method="ancuti2018",
        channel_means=means,
        requested=requested,
        effective=effective,
        mean_added=_mean_added(image, out),
    )
    return out, info


def compensate_c3(image: Image, params: Params) -> tuple[Image, CompensationInfo]:
    """Compensate the opponent colour channels per [3C] in BT.709 YCbCr (spec 6.3.2, D47).

    [3C] compensates the opponent channels by subtracting a weighted Gaussian local mean;
    the spec's YCbCr form (spec 6.3.2), with ``G{}`` a Gaussian of large support:

    - ``Cr'(x) = Cr(x) - kappa * M(x) * G{Cr}(x)``  (kappa: the paper's a*, red-green)
    - ``Cb'(x) = Cb(x) - lambda * M(x) * G{Cb}(x)`` (lambda: the paper's b*, blue-yellow)

    with ``kappa = c3_strength * params.kappa`` and ``lambda = c3_strength *
    params.lambda_`` (paper values 1.0 and 0.7). Y is unchanged. The mask M is 0 where
    ``mean(R, G, B) > c3_mask_threshold`` (0.85) and 1 elsewhere, then smoothed with a
    Gaussian of sigma ``c3_mask_smooth_fraction``; ``G{}`` has sigma
    ``c3_kernel_fraction`` (both fractions of the short side). Y, Cb and Cr come from
    :data:`RGB_TO_YCBCR` on the display-encoded values. Because the transform is linear
    and Y is unchanged, the output is formed as ``RGB + YCBCR_TO_RGB @ (0, dCb, dCr)``,
    which equals the round trip through YCbCr exactly and leaves a pixel with ``M = 0``
    bit-identical. The result is clipped to [0, 1].

    Args:
        image: The input image.
        params: Uses ``kappa``, ``lambda_``, ``c3_strength``, ``c3_kernel_fraction``,
            ``c3_mask_threshold``, ``c3_mask_smooth_fraction``.

    Returns:
        The compensated image and the step's record.
    """
    _check_image(image)
    kappa = params.c3_strength * params.kappa
    lambda_ = params.c3_strength * params.lambda_
    ycbcr = rgb_to_ycbcr(image)
    bright = image.mean(axis=2, dtype=np.float32) > params.c3_mask_threshold
    mask = _gaussian(
        np.where(bright, np.float32(0.0), np.float32(1.0)),
        spatial_sigma(image.shape, params.c3_mask_smooth_fraction),
    )
    sigma = spatial_sigma(image.shape, params.c3_kernel_fraction)
    delta_cb = -lambda_ * mask * _gaussian(ycbcr[..., 1], sigma)
    delta_cr = -kappa * mask * _gaussian(ycbcr[..., 2], sigma)
    to_rgb = YCBCR_TO_RGB.astype(np.float32)
    delta = delta_cb[..., None] * to_rgb[:, 1] + delta_cr[..., None] * to_rgb[:, 2]
    out = np.clip(image + delta, 0.0, 1.0).astype(np.float32, copy=False)
    info = CompensationInfo(
        method="c3",
        channel_means=_channel_means(image),
        requested={"cr": params.kappa, "cb": params.lambda_},
        effective={"cr": kappa, "cb": lambda_},
        mean_added=_mean_added(image, out),
    )
    return out, info


def white_balance(image: Image, params: Params) -> tuple[Image, WhiteBalanceInfo]:
    """Gray-world white balance with the D99 gain clamp (spec 6.2 step 2).

    [A18]'s white-balancing section applies the Gray-World assumption after compensation. Per
    channel c, with ``mean_c`` the channel mean over the whole image and ``target`` the
    mean of the three channel means:

    - gray-world gain ``g_c = target / mean_c``;
    - requested gain ``1 + s * (g_c - 1)``, ``s = white_balance_strength``;
    - applied gain ``min(requested, max_white_balance_gain)`` (D99).

    The output is ``clip(I_c * applied_c, 0, 1)``. A channel with a mean under 1e-6 is
    treated as having mean 1e-6 (its gain then ends at the clamp).

    Args:
        image: The compensated image.
        params: Uses ``white_balance_strength`` and ``max_white_balance_gain``.

    Returns:
        The white-balanced image and the step's record.
    """
    _check_image(image)
    means = _channel_means(image)
    target = sum(means) / 3.0
    gray_world = tuple(target / max(mean, _EPS) for mean in means)
    requested = tuple(1.0 + params.white_balance_strength * (g - 1.0) for g in gray_world)
    applied = tuple(min(g, params.max_white_balance_gain) for g in requested)
    gains = np.array(applied, dtype=np.float32)
    out = np.clip(image * gains, 0.0, 1.0).astype(np.float32, copy=False)
    info = WhiteBalanceInfo(
        channel_means=means,
        target=target,
        gray_world_gains=_triple(gray_world),
        requested_gains=_triple(requested),
        applied_gains=_triple(applied),
        clamped=(requested[0] > applied[0], requested[1] > applied[1], requested[2] > applied[2]),
    )
    return out, info


def fusion_inputs(image: Image, params: Params) -> tuple[Image, Image]:
    """Derive the two fusion inputs from the white-balanced image (spec 6.2 step 3).

    Input 1 ([A18], fusion inputs: gamma correction): ``I ** gamma``.

    Input 2 ([A18], fusion inputs: normalised unsharp masking):
    ``S = (I + N{I - G*I}) / 2``, where ``G*I`` is a Gaussian blur of sigma
    ``sharpen_blur_fraction`` and N{} is the linear normalisation (histogram stretch) that
    shifts and scales ALL pixel values of all three channels with ONE shift and ONE scale
    ([A18]: "a unique shifting and scaling factor") so that they cover [0, 1]. The bounds
    are the ``normalisation_low`` and ``normalisation_high`` percentiles of ``I - G*I``
    over the whole image (spec 6.2, 14.1); values outside are clipped. When the two
    bounds are closer than 1e-6 (a flat image) N{} is 0.5 everywhere, the stretched
    image of a zero high-pass. ``sharpen_strength`` s interpolates
    ``I + s * (S - I)``: 1 gives the paper's S, 0 gives ``I``. Both inputs are clipped to
    [0, 1].

    Args:
        image: The white-balanced image.
        params: Uses ``gamma``, ``sharpen_strength``, ``sharpen_blur_fraction``,
            ``normalisation_low`` and ``normalisation_high``.

    Returns:
        Input 1 (gamma) and input 2 (sharpened).
    """
    _check_image(image)
    input1 = np.power(image, np.float32(params.gamma)).astype(np.float32, copy=False)
    high_pass = image - _gaussian(image, spatial_sigma(image.shape, params.sharpen_blur_fraction))
    low, high = (
        float(v)
        for v in np.percentile(high_pass, [params.normalisation_low, params.normalisation_high])
    )
    if high - low < _EPS:
        stretched = np.full_like(image, 0.5)
    else:
        stretched = np.clip((high_pass - low) / (high - low), 0.0, 1.0)
    sharpened = (image + stretched) / 2.0
    input2 = np.clip(image + params.sharpen_strength * (sharpened - image), 0.0, 1.0)
    return input1, input2.astype(np.float32, copy=False)


def weight_maps(input_: Sequence[Image], params: Params) -> Weights:
    """Compute the three weight maps of each fusion input and normalise them (step 4).

    Per input k ([A18], weights of the fusion process), with ``L_k`` the BT.709
    luma of the input (:data:`RGB_TO_YCBCR` row Y):

    - Laplacian contrast ``W_L = |sigma^2 * Laplacian(G_sigma * L_k)|``: the absolute
      value of the paper's discrete Laplacian (the 5-point kernel, per pixel) applied to
      the luminance smoothed by a Gaussian of sigma = ``laplacian_fraction`` of the short
      side, times sigma squared (scale normalisation). The smoothing and the sigma^2
      factor make the paper's per-pixel Laplacian resolution independent (spec 6.6).
    - Saliency ``W_S = ||I_mu - I_whc(x)|| / 100``, the frequency-tuned saliency of
      Achanta et al. (CVPR 2009): the Euclidean distance in CIELAB between the
      image's mean Lab vector ``I_mu`` and the Gaussian-blurred Lab image ``I_whc``
      (sigma ``saliency_blur_fraction``), divided by 100 so that L* spans [0, 1]. Lab
      from :func:`srgb_to_lab`.
    - Saturation ``W_Sat = sqrt(((R_k - L_k)^2 + (G_k - L_k)^2 + (B_k - L_k)^2) / 3)``
      ([A18]).

    ``W_k = W_L + W_S + W_Sat`` ([A18]: the three maps are summed), then
    ``Wbar_k = (W_k + delta) / (sum_k W_k + K * delta)`` with ``delta = weight_delta``
    (0.1) and K the number of inputs (2) ([A18], weight normalisation; spec 6.2 step 4).

    Args:
        input_: The fusion inputs, in order (input 1, input 2).
        params: Uses ``laplacian_fraction``, ``saliency_blur_fraction``,
            ``weight_delta``.

    Returns:
        The raw, aggregated and normalised weight maps.

    Raises:
        ValueError: ``input_`` is empty or its images differ in shape.
    """
    if not input_:
        raise ValueError("weight_maps needs at least one input")
    for image in input_:
        _check_image(image)
        if image.shape != input_[0].shape:
            raise ValueError("fusion inputs differ in shape")
    laplacian = tuple(_laplacian_weight(image, params) for image in input_)
    saliency = tuple(_saliency_weight(image, params) for image in input_)
    saturation = tuple(_saturation_weight(image) for image in input_)
    aggregated = tuple(
        (lw + sw + tw).astype(np.float32, copy=False)
        for lw, sw, tw in zip(laplacian, saliency, saturation, strict=True)
    )
    delta = params.weight_delta
    denominator = np.full_like(aggregated[0], len(aggregated) * delta)
    for w in aggregated:
        denominator += w
    normalised = tuple(((w + delta) / denominator).astype(np.float32) for w in aggregated)
    return Weights(laplacian, saliency, saturation, aggregated, normalised)


def multiscale_fusion(inputs: Sequence[Image], weights: Sequence[Map], params: Params) -> Image:
    """Fuse the inputs with a Laplacian pyramid blended by Gaussian pyramids (step 5).

    [A18], multiscale fusion (after Burt and Adelson): each input k is decomposed into a Laplacian
    pyramid ``L_l{I_k}`` and its normalised weight into a Gaussian pyramid
    ``G_l{Wbar_k}``; level by level ``R_l = sum_k G_l{Wbar_k} * L_l{I_k}``; the fused
    pyramid R is collapsed and the result clipped to [0, 1]. The depth comes from
    :func:`pyramid_levels` with ``pyramid_min_level_size`` (spec 6.6). Resampling: see
    :func:`gaussian_pyramid` and :func:`laplacian_pyramid`.

    Args:
        inputs: The fusion inputs.
        weights: One normalised weight map per input.
        params: Uses ``pyramid_min_level_size``.

    Returns:
        The fused image.

    Raises:
        ValueError: The counts or shapes of inputs and weights do not match.
    """
    if not inputs or len(inputs) != len(weights):
        raise ValueError("multiscale_fusion needs one weight map per input")
    shape = inputs[0].shape
    for image, weight in zip(inputs, weights, strict=True):
        _check_image(image)
        if image.shape != shape or weight.shape != shape[:2]:
            raise ValueError("fusion inputs and weights differ in shape")
    levels = pyramid_levels(shape, params.pyramid_min_level_size)
    fused: list[NDArray[np.float32]] | None = None
    for image, weight in zip(inputs, weights, strict=True):
        image_pyramid = laplacian_pyramid(image, levels)
        weight_pyramid = gaussian_pyramid(np.asarray(weight, dtype=np.float32), levels)
        pairs = zip(weight_pyramid, image_pyramid, strict=True)
        blended = [w[..., None] * band for w, band in pairs]
        fused = blended if fused is None else [f + b for f, b in zip(fused, blended, strict=True)]
    assert fused is not None
    return np.clip(collapse_pyramid(fused), 0.0, 1.0).astype(np.float32, copy=False)


def correct(image: Image, params: Params) -> Result:
    """Run the whole pipeline on one image and keep every intermediate.

    Steps (spec 6.2): compensation (``params.method``), white balance, fusion inputs,
    weight maps, multiscale fusion; then the blend with the original,
    ``output = (1 - b) * fused + b * image`` with ``b = blend_with_original`` (0.0 =
    fully corrected, 1.0 = the original).

    Args:
        image: The display-encoded RGB input, float32 in [0, 1], shape ``(H, W, 3)``.
        params: The parameter set.

    Returns:
        The output and every intermediate.
    """
    _check_image(image)
    if params.method == "c3":
        compensated, compensation = compensate_c3(image, params)
    else:
        compensated, compensation = compensate_ancuti2018(image, params)
    balanced, balance = white_balance(compensated, params)
    input1, input2 = fusion_inputs(balanced, params)
    weights = weight_maps((input1, input2), params)
    fused = multiscale_fusion((input1, input2), weights.normalised, params)
    blend = params.blend_with_original
    output = ((1.0 - blend) * fused + blend * image).astype(np.float32, copy=False)
    return Result(
        output=output,
        fused=fused,
        compensated=compensated,
        white_balanced=balanced,
        input1=input1,
        input2=input2,
        weights=weights,
        compensation=compensation,
        white_balance=balance,
        params=params,
    )


def rgb_to_ycbcr(image: Image) -> Image:
    """Convert display-encoded RGB to full-range BT.709 (Y, Cb, Cr) (:data:`RGB_TO_YCBCR`).

    Args:
        image: RGB, float32, shape ``(H, W, 3)``.

    Returns:
        Y in [0, 1] and Cb, Cr in [-0.5, 0.5], float32, shape ``(H, W, 3)``.
    """
    return (image @ RGB_TO_YCBCR.T.astype(np.float32)).astype(np.float32, copy=False)


def ycbcr_to_rgb(ycbcr: Image) -> Image:
    """Convert full-range BT.709 (Y, Cb, Cr) back to RGB (:data:`YCBCR_TO_RGB`), unclipped.

    Args:
        ycbcr: Y, Cb, Cr, float32, shape ``(H, W, 3)``.

    Returns:
        RGB, float32, shape ``(H, W, 3)``.
    """
    return (ycbcr @ YCBCR_TO_RGB.T.astype(np.float32)).astype(np.float32, copy=False)


def luminance(image: Image) -> Map:
    """Return the BT.709 luma ``Y = 0.2126 R + 0.7152 G + 0.0722 B`` of an RGB image.

    Args:
        image: RGB, float32, shape ``(H, W, 3)``.

    Returns:
        Y, float32, shape ``(H, W)``.
    """
    return np.asarray(image @ RGB_TO_YCBCR[0].astype(np.float32), dtype=np.float32)


def srgb_to_lab(image: Image) -> Image:
    """Convert display-encoded RGB, read as sRGB, to CIELAB (D65), for the saliency weight.

    The values are decoded with the sRGB transfer function and converted with the sRGB
    matrix (IEC 61966-2-1:1999), then to CIELAB with the D65 white (CIE 15:2004):
    ``L* = 116 f(Y/Yn) - 16``, ``a* = 500 (f(X/Xn) - f(Y/Yn))``,
    ``b* = 200 (f(Y/Yn) - f(Z/Zn))``, ``f(t) = t^(1/3)`` above ``(6/29)^3`` and
    ``t / (3 (6/29)^2) + 4/29`` below. A Display P3 source is read as sRGB here too: the
    conversion only feeds a weight map, and no colour management is in scope (WP1.1).

    Args:
        image: RGB, float32, shape ``(H, W, 3)``, values in [0, 1].

    Returns:
        L*, a*, b* (L* in [0, 100]), float32, shape ``(H, W, 3)``.
    """
    linear = np.where(
        image <= 0.04045,
        image / np.float32(12.92),
        np.power((image + np.float32(0.055)) / np.float32(1.055), np.float32(2.4)),
    )
    xyz = (linear @ _SRGB_TO_XYZ.T) / _D65_WHITE
    f = np.where(
        xyz > _LAB_DELTA**3,
        np.cbrt(xyz),
        xyz / np.float32(3.0 * _LAB_DELTA**2) + np.float32(4.0 / 29.0),
    )
    lab = np.empty_like(f)
    lab[..., 0] = 116.0 * f[..., 1] - 16.0
    lab[..., 1] = 500.0 * (f[..., 0] - f[..., 1])
    lab[..., 2] = 200.0 * (f[..., 1] - f[..., 2])
    return lab.astype(np.float32, copy=False)


def pyramid_levels(image_shape: tuple[int, ...], min_level_size: int) -> int:
    """Return the pyramid depth for an image: halve while the short side stays large enough.

    Starting from the short side, each level halves it (rounding up, as
    :func:`gaussian_pyramid` keeps every second sample starting at the first). A level is
    added only while the halved short side is still at least ``min_level_size``, so the
    coarsest level has a short side of at least ``min_level_size`` pixels (or is the
    image itself when the image is smaller), and its size relative to the image scales
    with the image (spec 6.6).

    Args:
        image_shape: The image shape; the first two entries are height and width.
        min_level_size: Minimum short side of the coarsest level, in pixels.

    Returns:
        The number of levels, at least 1.
    """
    size = min(image_shape[0], image_shape[1])
    levels = 1
    while math.ceil(size / 2) >= min_level_size and size > 1:
        size = math.ceil(size / 2)
        levels += 1
    return levels


def gaussian_pyramid(image: NDArray[np.float32], levels: int) -> list[NDArray[np.float32]]:
    """Build a Gaussian pyramid of ``levels`` levels (level 0 is the image).

    Each level is the previous one filtered with the separable 5-tap binomial kernel
    ``[1 4 6 4 1] / 16`` (Burt and Adelson's REDUCE, the paper's practice) with symmetric
    borders, then subsampled by keeping rows and columns 0, 2, 4, ... (so an odd size n
    becomes ``(n + 1) / 2``).

    Args:
        image: An ``(H, W)`` map or an ``(H, W, C)`` image, float32.
        levels: Number of levels, at least 1.

    Returns:
        The levels, finest first.
    """
    pyramid = [image]
    for _ in range(levels - 1):
        pyramid.append(_binomial_blur(pyramid[-1])[::2, ::2])
    return pyramid


def laplacian_pyramid(image: NDArray[np.float32], levels: int) -> list[NDArray[np.float32]]:
    """Build a Laplacian pyramid: ``L_l = G_l - EXPAND(G_{l+1})``, the last level ``G_top``.

    EXPAND (:func:`expand`) is the same for building and collapsing, so
    :func:`collapse_pyramid` reconstructs the image exactly up to float round-off.

    Args:
        image: An ``(H, W)`` map or an ``(H, W, C)`` image, float32.
        levels: Number of levels, at least 1.

    Returns:
        The band-pass levels, finest first, ending with the coarsest Gaussian level.
    """
    gaussian = gaussian_pyramid(image, levels)
    bands = [fine - expand(coarse, fine.shape) for fine, coarse in itertools.pairwise(gaussian)]
    bands.append(gaussian[-1])
    return bands


def collapse_pyramid(pyramid: Sequence[NDArray[np.float32]]) -> NDArray[np.float32]:
    """Collapse a Laplacian pyramid: from the coarsest level, ``G_l = L_l + EXPAND(G_{l+1})``.

    Args:
        pyramid: The levels, finest first.

    Returns:
        The reconstructed full-size array.
    """
    image = pyramid[-1]
    for band in reversed(pyramid[:-1]):
        image = band + expand(image, band.shape)
    return image


def expand(image: NDArray[np.float32], shape: tuple[int, ...]) -> NDArray[np.float32]:
    """Upsample a pyramid level to ``shape`` (Burt and Adelson's EXPAND, normalised).

    The samples are placed at rows and columns 0, 2, 4, ... of a zero array of the
    target shape, filtered with the 5-tap binomial kernel (symmetric borders), and
    divided by the same filter applied to the sample-position indicator. In the interior
    the divisor is exactly 1/4 (the classical ``4 * filter`` EXPAND); at the borders the
    division keeps a constant level constant.

    Args:
        image: The coarse level, ``(h, w)`` or ``(h, w, C)``.
        shape: The fine level's shape; ``h == ceil(H / 2)`` and ``w == ceil(W / 2)``.

    Returns:
        The upsampled array, float32, of ``shape``.
    """
    upsampled = np.zeros(shape, dtype=np.float32)
    upsampled[::2, ::2] = image
    indicator = np.zeros(shape[:2], dtype=np.float32)
    indicator[::2, ::2] = 1.0
    norm = _binomial_blur(indicator)
    blurred = _binomial_blur(upsampled)
    if blurred.ndim == 3:
        return (blurred / norm[..., None]).astype(np.float32, copy=False)
    return (blurred / norm).astype(np.float32, copy=False)


def _laplacian_weight(image: Image, params: Params) -> Map:
    """W_L of one input: ``|sigma^2 * Lap(G_sigma * L)|`` (see :func:`weight_maps`)."""
    # The discrete Laplacian (zero-sum, so a flat image gives exactly 0) of the
    # Gaussian-smoothed luminance; scipy's sampled Gaussian second derivative is not
    # zero-sum at small sigma and would give a flat image a nonzero contrast weight.
    sigma = spatial_sigma(image.shape, params.laplacian_fraction)
    log = ndimage.laplace(_gaussian(luminance(image), sigma), mode="reflect")
    return np.abs(np.asarray(log, dtype=np.float32) * np.float32(sigma**2))


def _saliency_weight(image: Image, params: Params) -> Map:
    """W_S of one input: ``||mean Lab - blurred Lab|| / 100`` (see :func:`weight_maps`)."""
    lab = srgb_to_lab(image)
    mean = lab.reshape(-1, 3).mean(axis=0, dtype=np.float64).astype(np.float32)
    blurred = _gaussian(lab, spatial_sigma(image.shape, params.saliency_blur_fraction))
    distance = np.sqrt(np.sum((blurred - mean) ** 2, axis=2))
    return (distance / np.float32(100.0)).astype(np.float32, copy=False)


def _saturation_weight(image: Image) -> Map:
    """W_Sat of one input: the RMS deviation of R, G, B from the luma."""
    luma = luminance(image)
    deviation = np.mean((image - luma[..., None]) ** 2, axis=2)
    return np.sqrt(deviation).astype(np.float32, copy=False)


def _gaussian(array: NDArray[np.float32], sigma: float) -> NDArray[np.float32]:
    """Gaussian filter over the two spatial axes only (symmetric borders, 4 sigma)."""
    sigmas = (sigma, sigma) + (0.0,) * (array.ndim - 2)
    filtered = ndimage.gaussian_filter(
        array, sigma=sigmas, mode="reflect", truncate=_GAUSSIAN_TRUNCATE
    )
    return np.asarray(filtered, dtype=np.float32)


def _binomial_blur(array: NDArray[np.float32]) -> NDArray[np.float32]:
    """Separable 5-tap binomial filter over the two spatial axes (symmetric borders)."""
    rows = ndimage.correlate1d(array, _BINOMIAL_5, axis=0, mode="reflect")
    both = ndimage.correlate1d(rows, _BINOMIAL_5, axis=1, mode="reflect")
    return np.asarray(both, dtype=np.float32)


def _channel_means(image: Image) -> tuple[float, float, float]:
    """Mean of each RGB channel over the whole image, accumulated in float64."""
    means = image.reshape(-1, 3).mean(axis=0, dtype=np.float64)
    return float(means[0]), float(means[1]), float(means[2])


def _mean_added(before: Image, after: Image) -> dict[str, float]:
    """Mean change of each RGB channel, ``after`` minus ``before``."""
    added = _channel_means(after)
    original = _channel_means(before)
    return {name: added[i] - original[i] for i, name in enumerate(("red", "green", "blue"))}


def _triple(values: tuple[float, ...]) -> tuple[float, float, float]:
    """The first three values as a tuple of three Python floats."""
    return float(values[0]), float(values[1]), float(values[2])


def _check_image(image: Image) -> None:
    """Raise ValueError unless ``image`` is a float32 ``(H, W, 3)`` array in [0, 1]."""
    if not isinstance(image, np.ndarray) or image.dtype != np.float32:
        raise ValueError("image must be a float32 numpy array")
    if image.ndim != 3 or image.shape[2] != 3 or image.shape[0] < 1 or image.shape[1] < 1:
        raise ValueError(f"image must have shape (H, W, 3), got {image.shape}")
    low, high = float(image.min()), float(image.max())
    if not (low >= 0.0 and high <= 1.0):
        raise ValueError(f"image values must lie in [0, 1], got [{low}, {high}]")
