from __future__ import annotations

import dataclasses
import struct
import subprocess
import sys
import zlib
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from scipy import ndimage

from prototype import run
from prototype.params import Params
from prototype.pipeline import (
    compensate_ancuti2018,
    compensate_c3,
    correct,
    fusion_inputs,
    multiscale_fusion,
    pyramid_levels,
    rgb_to_ycbcr,
    spatial_sigma,
    srgb_to_lab,
    weight_maps,
    white_balance,
)

SIZES = [(64, 96), (97, 65)]
METHODS = ["ancuti2018", "c3"]
# Params.neutral() output vs input, max absolute difference (open-values report).
NEUTRAL_TOLERANCE = 1e-6
# Resolution independence at 2x (open-values report): mean and 99th percentile of the
# absolute difference between the downscaled output and the output of the downscaled input.
RESOLUTION_MEAN_TOLERANCE = 0.01
RESOLUTION_P99_TOLERANCE = 0.02
# The same with the default Params on a 512 x 768 textured scene.
DEFAULTS_RESOLUTION_MEAN_TOLERANCE = 0.0015
DEFAULTS_RESOLUTION_P99_TOLERANCE = 0.005


def _synthetic(height: int, width: int, seed: int = 0) -> np.ndarray:
    """Gradients with a blue-green cast and a tiny noise field, float32 in [0, 1]."""
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    y /= max(height - 1, 1)
    x /= max(width - 1, 1)
    red = 0.05 + 0.15 * x
    green = 0.35 + 0.35 * y
    blue = 0.45 + 0.25 * x * y
    image = np.stack([red, green, blue], axis=2)
    noise = np.random.default_rng(seed).normal(0.0, 0.01, image.shape)
    return np.clip(image + noise, 0.0, 1.0).astype(np.float32)


def _flat(height: int, width: int, rgb: tuple[float, float, float]) -> np.ndarray:
    return np.broadcast_to(np.array(rgb, dtype=np.float32), (height, width, 3)).copy()


def _smooth_scene(height: int, width: int) -> np.ndarray:
    """A band-limited scene (low-frequency waves) with a blue-green cast, for the 2x test."""
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    y /= height
    x /= width
    red = 0.10 + 0.08 * np.sin(2 * np.pi * x) * np.cos(np.pi * y)
    green = 0.45 + 0.20 * np.sin(np.pi * (x + y))
    blue = 0.55 + 0.15 * np.cos(2 * np.pi * y) * np.sin(np.pi * x)
    return np.clip(np.stack([red, green, blue], axis=2), 0.0, 1.0).astype(np.float32)


def _textured_scene(height: int, width: int) -> np.ndarray:
    """The smooth scene modulated by a random texture of scale 0.01 of the short side.

    A soft-edged bright disc (mean above 0.85) makes the 3C mask and its smoothing matter.
    """
    short = min(height, width)
    rng = np.random.default_rng(5)
    field = ndimage.gaussian_filter(rng.random((height, width)), 0.01 * short)
    field = (field - field.min()) / (field.max() - field.min())
    textured = _smooth_scene(height, width) * (0.6 + 0.8 * field[..., None])
    y, x = np.mgrid[0:height, 0:width]
    disc = ((y - 0.39 * height) ** 2 + (x - 0.65 * width) ** 2 < (0.176 * short) ** 2) * 1.0
    alpha = ndimage.gaussian_filter(disc, 0.02 * short)[..., None]
    textured = textured * (1 - alpha) + np.array([0.88, 0.95, 0.97]) * alpha
    return np.clip(textured, 0.0, 1.0).astype(np.float32)


def _box_down2(image: np.ndarray) -> np.ndarray:
    h, w = image.shape[0] // 2 * 2, image.shape[1] // 2 * 2
    blocks = image[:h, :w].reshape(h // 2, 2, w // 2, 2, -1)
    return blocks.mean(axis=(1, 3)).astype(np.float32)


def _assert_image(array: np.ndarray, shape: tuple[int, ...]) -> None:
    assert array.shape == shape
    assert array.dtype == np.float32
    assert np.isfinite(array).all()
    assert array.min() >= 0.0
    assert array.max() <= 1.0


# --- shapes, dtype and range ------------------------------------------------------------


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("method", METHODS)
def test_every_stage_keeps_shape_dtype_and_range(size: tuple[int, int], method: str) -> None:
    image = _synthetic(*size)
    params = Params(method=method, blue_compensation=True)  # type: ignore[arg-type]
    result = correct(image, params)
    shape = (*size, 3)
    for stage in (
        result.output,
        result.fused,
        result.compensated,
        result.white_balanced,
        result.input1,
        result.input2,
    ):
        _assert_image(stage, shape)
    weights = result.weights
    for group in (weights.laplacian, weights.saliency, weights.saturation, weights.aggregated):
        assert len(group) == 2
        for weight in group:
            assert weight.shape == size
            assert weight.dtype == np.float32
            assert np.isfinite(weight).all()
            assert weight.min() >= 0.0
    for weight in weights.normalised:
        _assert_image(weight, size)
    np.testing.assert_array_equal(image, _synthetic(*size))  # the input is not modified


@pytest.mark.parametrize("size", SIZES)
def test_individual_steps_keep_shape_dtype_and_range(size: tuple[int, int]) -> None:
    image = _synthetic(*size)
    params = Params()
    shape = (*size, 3)
    for step in (compensate_ancuti2018, compensate_c3, white_balance):
        out, _ = step(image, params)
        _assert_image(out, shape)
    for out in fusion_inputs(image, params):
        _assert_image(out, shape)


def test_steps_reject_bad_images() -> None:
    with pytest.raises(ValueError, match="float32"):
        correct(_synthetic(8, 8).astype(np.float64), Params())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="shape"):
        correct(np.zeros((8, 8), dtype=np.float32), Params())
    with pytest.raises(ValueError, match=r"\[0, 1\]"):
        correct(_flat(8, 8, (0.5, 1.5, 0.5)), Params())


# --- pyramid ----------------------------------------------------------------------------


@pytest.mark.parametrize("size", [*SIZES, (33, 17)])
@pytest.mark.parametrize("min_level", [1, 4, 16])
def test_fusing_identical_inputs_is_identity(size: tuple[int, int], min_level: int) -> None:
    rng = np.random.default_rng(1)
    image = rng.random((*size, 3), dtype=np.float32)
    weight = rng.random(size, dtype=np.float32)
    params = Params(pyramid_min_level_size=min_level)
    fused = multiscale_fusion([image, image], [weight, 1.0 - weight], params)
    np.testing.assert_allclose(fused, image, atol=1e-5, rtol=0)


@pytest.mark.parametrize("size", SIZES)
def test_fusion_with_weights_one_and_zero_returns_the_first_input(size: tuple[int, int]) -> None:
    rng = np.random.default_rng(2)
    first = rng.random((*size, 3), dtype=np.float32)
    second = rng.random((*size, 3), dtype=np.float32)
    ones = np.ones(size, dtype=np.float32)
    params = Params(pyramid_min_level_size=2)
    fused = multiscale_fusion([first, second], [ones, np.zeros_like(ones)], params)
    np.testing.assert_allclose(fused, first, atol=1e-4, rtol=0)


def test_fusion_blends_a_weight_seam_across_scales() -> None:
    # Two flat inputs and a hard weight seam: a per-pixel blend keeps the seam hard; the
    # pyramid blends it through the Gaussian pyramid of the weights.
    first = _flat(64, 96, (0.2, 0.2, 0.2))
    second = _flat(64, 96, (0.8, 0.8, 0.8))
    weight = np.zeros((64, 96), dtype=np.float32)
    weight[:, :48] = 1.0
    weights = [weight, 1 - weight]
    single = multiscale_fusion([first, second], weights, Params(pyramid_min_level_size=64))
    per_pixel = weight[..., None] * first + (1 - weight[..., None]) * second
    np.testing.assert_allclose(single, per_pixel, atol=1e-6)  # one level = per-pixel blend
    fused = multiscale_fusion([first, second], weights, Params(pyramid_min_level_size=4))
    row = fused[32, :, 0]
    assert row[44] > 0.25  # 4 px left of the seam: already blended
    assert row[51] < 0.75
    assert row[0] < row[44] < row[51] < row[95]
    assert (np.diff(row) >= -1e-6).all()  # a smooth, monotone transition
    assert fused.min() >= 0.2 - 1e-6
    assert fused.max() <= 0.8 + 1e-6


def test_pyramid_depth_follows_the_minimum_level_size() -> None:
    assert pyramid_levels((64, 96, 3), 16) == 3  # 64 -> 32 -> 16
    assert pyramid_levels((97, 65, 3), 16) == 3  # 65 -> 33 -> 17
    assert pyramid_levels((128, 192, 3), 16) == 4  # one level more at 2x
    assert pyramid_levels((10, 10, 3), 16) == 1
    assert pyramid_levels((1, 1, 3), 1) == 1


def test_fusion_rejects_mismatched_weights() -> None:
    image = _synthetic(16, 16)
    with pytest.raises(ValueError, match="one weight map per input"):
        multiscale_fusion([image, image], [np.ones((16, 16), np.float32)], Params())
    with pytest.raises(ValueError, match="differ in shape"):
        multiscale_fusion([image], [np.ones((8, 16), np.float32)], Params())


# --- weights ----------------------------------------------------------------------------


@pytest.mark.parametrize("size", SIZES)
def test_normalised_weights_sum_to_one(size: tuple[int, int]) -> None:
    input1, input2 = fusion_inputs(_synthetic(*size), Params())
    weights = weight_maps((input1, input2), Params())
    total = weights.normalised[0] + weights.normalised[1]
    np.testing.assert_allclose(total, 1.0, atol=1e-6, rtol=0)


def test_weight_maps_follow_their_definitions() -> None:
    gray = _flat(32, 32, (0.4, 0.4, 0.4))
    colour = _flat(32, 32, (0.6, 0.3, 0.2))
    weights = weight_maps((gray, colour), Params())
    # Flat images: no Laplacian contrast and no saliency (blurred Lab == mean Lab).
    for index in (0, 1):
        np.testing.assert_allclose(weights.laplacian[index], 0.0, atol=1e-6)
        np.testing.assert_allclose(weights.saliency[index], 0.0, atol=1e-4)
    np.testing.assert_allclose(weights.saturation[0], 0.0, atol=1e-6)
    luma = 0.2126 * 0.6 + 0.7152 * 0.3 + 0.0722 * 0.2
    expected = np.sqrt(((0.6 - luma) ** 2 + (0.3 - luma) ** 2 + (0.2 - luma) ** 2) / 3)
    np.testing.assert_allclose(weights.saturation[1], expected, rtol=1e-5)
    # (W_k + delta) / (sum W_k + 2 delta) with W_0 = 0.
    np.testing.assert_allclose(weights.normalised[0], 0.1 / (expected + 0.2), rtol=1e-5, atol=1e-6)


def test_srgb_to_lab_matches_reference_values() -> None:
    # CIELAB (D65) of the sRGB white and primaries, as published for IEC 61966-2-1.
    colours = np.array([[[1, 1, 1], [1, 0, 0], [0, 1, 0], [0, 0, 1]]], dtype=np.float32)
    expected = [[100.0, 0.0, 0.0], [53.24, 80.09, 67.20], [87.73, -86.18, 83.18]]
    expected.append([32.30, 79.19, -107.86])
    np.testing.assert_allclose(srgb_to_lab(colours)[0], expected, atol=0.1)


def test_laplacian_weight_on_an_edge() -> None:
    image = _flat(64, 96, (0.2, 0.2, 0.2))
    image[:, 48:] = 0.8
    weights = weight_maps((image, image), Params(laplacian_fraction=0.02))
    sigma = 0.02 * 64
    luma = image[..., 0].astype(np.float64)  # gray: luma equals every channel
    smoothed = ndimage.gaussian_filter(luma, sigma, mode="reflect", truncate=4.0)
    expected = sigma**2 * np.abs(ndimage.laplace(smoothed, mode="reflect"))
    np.testing.assert_allclose(weights.laplacian[0], expected, atol=1e-5)
    assert weights.laplacian[0][:, 46:50].min() > 0.05  # strong at the edge
    assert weights.laplacian[0][:, :30].max() < 1e-6  # zero far from it


def test_saliency_weight_on_a_coloured_patch() -> None:
    image = _flat(64, 96, (0.4, 0.4, 0.4))
    image[20:40, 30:60] = (0.8, 0.3, 0.2)
    weights = weight_maps((image, image), Params(saliency_blur_fraction=0.02))
    lab = srgb_to_lab(image).astype(np.float64)
    blurred = ndimage.gaussian_filter(lab, (1.28, 1.28, 0), mode="reflect", truncate=4.0)
    expected = np.linalg.norm(blurred - lab.reshape(-1, 3).mean(axis=0), axis=2) / 100
    np.testing.assert_allclose(weights.saliency[0], expected, atol=1e-4)
    assert weights.saliency[0][30, 45] > 3 * weights.saliency[0][5, 5]


# --- Ancuti 2018 compensation ----------------------------------------------------------


def test_red_compensation_is_identity_when_red_and_green_means_match() -> None:
    image = _synthetic(64, 96)
    image[..., 0] = np.roll(image[..., 1], 7, axis=1)  # same mean, different pixels
    out, info = compensate_ancuti2018(image, Params())
    assert info.channel_means[0] == pytest.approx(info.channel_means[1], abs=1e-9)
    np.testing.assert_allclose(out, image, atol=1e-7, rtol=0)


def test_red_compensation_adds_a_positive_amount_when_red_is_weaker() -> None:
    image = _synthetic(64, 96)
    out, info = compensate_ancuti2018(image, Params(red_gain_cap=None))
    assert info.mean_added["red"] > 0.0
    assert (out[..., 0] >= image[..., 0]).all()
    np.testing.assert_array_equal(out[..., 1:], image[..., 1:])  # blue off by default
    assert info.effective == {"red": 1.0}
    # The formula itself, pixel by pixel.
    mean_r, mean_g = image[..., 0].mean(), image[..., 1].mean()
    expected = image[..., 0] + (mean_g - mean_r) * (1 - image[..., 0]) * image[..., 1]
    np.testing.assert_allclose(out[..., 0], expected, atol=1e-6)


def test_blue_compensation_when_enabled() -> None:
    image = _flat(16, 16, (0.1, 0.6, 0.2))
    out, info = compensate_ancuti2018(image, Params(blue_compensation=True, blue_gain_cap=None))
    expected_blue = 0.2 + (0.6 - 0.2) * (1 - 0.2) * 0.6
    np.testing.assert_allclose(out[..., 2], expected_blue, atol=1e-6)
    assert set(info.effective) == {"red", "blue"}


@pytest.mark.parametrize("cap", [0.25, 0.5, 1.0])
def test_gain_cap_limits_the_mean_added_amount(cap: float) -> None:
    image = _synthetic(64, 96)
    mean_red = float(image[..., 0].mean(dtype=np.float64))
    _, uncapped = compensate_ancuti2018(image, Params(red_gain_cap=None))
    assert uncapped.mean_added["red"] > cap * mean_red  # the cap binds for this image
    out, info = compensate_ancuti2018(image, Params(red_gain_cap=cap))
    assert info.mean_added["red"] == pytest.approx(cap * mean_red, rel=1e-4)
    assert info.effective["red"] < info.requested["red"] == 1.0
    assert float(out[..., 0].mean(dtype=np.float64)) == pytest.approx(
        (1 + cap) * mean_red, rel=1e-4
    )


def test_gain_cap_is_inactive_when_it_does_not_bind() -> None:
    image = _synthetic(64, 96)
    _, info = compensate_ancuti2018(image, Params(red_gain_cap=1000.0))
    assert info.effective["red"] == 1.0


# --- 3C ---------------------------------------------------------------------------------


def test_c3_is_identity_on_a_neutral_gray_image() -> None:
    y, _ = np.mgrid[0:64, 0:96].astype(np.float32)
    gray = np.repeat((0.1 + 0.8 * y / 63)[..., None], 3, axis=2).astype(np.float32)
    out, info = compensate_c3(gray, Params(method="c3"))
    np.testing.assert_array_equal(out, gray)
    assert all(abs(v) < 1e-9 for v in info.mean_added.values())


def test_c3_raises_cr_on_a_red_deficient_image() -> None:
    image = _synthetic(64, 96)
    out, info = compensate_c3(image, Params(method="c3"))
    cr_before = rgb_to_ycbcr(image)[..., 2]
    cr_after = rgb_to_ycbcr(out)[..., 2]
    assert cr_before.mean() < 0.0
    assert cr_after.mean() > cr_before.mean() + 0.05
    assert info.mean_added["red"] > 0.0
    assert info.effective == {"cr": 1.0, "cb": pytest.approx(0.7)}
    # Y is unchanged where nothing was clipped.
    np.testing.assert_allclose(rgb_to_ycbcr(out)[..., 0], rgb_to_ycbcr(image)[..., 0], atol=1e-5)


def test_c3_matches_the_equations_pixel_by_pixel() -> None:
    # An independent float64 evaluation of spec 6.3.2 with the BT.709 equations written out.
    image = _synthetic(64, 96)
    image[:20, :30] = (0.9, 0.95, 0.9)  # a masked bright patch
    params = Params(method="c3", kappa=0.9, lambda_=0.6, c3_strength=0.8)
    out, _ = compensate_c3(image, params)
    r, g, b = (image[..., i].astype(np.float64) for i in range(3))
    y = 0.2126 * r + 0.7152 * g + 0.0722 * b
    cb, cr = (b - y) / 1.8556, (r - y) / 1.5748
    assert abs(cb.mean()) > 0.02  # the image has a Cb component to compensate
    bright = (image.mean(axis=2) <= 0.85).astype(np.float64)
    mask = ndimage.gaussian_filter(bright, 0.01 * 64, mode="reflect", truncate=4.0)

    def local_mean(channel: np.ndarray) -> np.ndarray:
        return ndimage.gaussian_filter(channel, 0.05 * 64, mode="reflect", truncate=4.0)

    cr2 = cr - 0.8 * 0.9 * mask * local_mean(cr)
    cb2 = cb - 0.8 * 0.6 * mask * local_mean(cb)
    r2, b2 = y + 1.5748 * cr2, y + 1.8556 * cb2
    g2 = (y - 0.2126 * r2 - 0.0722 * b2) / 0.7152
    expected = np.clip(np.stack([r2, g2, b2], axis=2), 0.0, 1.0)
    np.testing.assert_allclose(out, expected, atol=1e-5)


def test_c3_strength_scales_kappa_and_lambda_together() -> None:
    _, info = compensate_c3(_synthetic(32, 32), Params(method="c3", c3_strength=0.5))
    assert info.effective == {"cr": 0.5, "cb": pytest.approx(0.35)}


def test_c3_mask_leaves_bright_pixels_unchanged() -> None:
    image = _synthetic(64, 96)
    image[:, :48] = (0.80, 0.95, 0.95)  # mean 0.9 > 0.85, but with a colour cast
    params = Params(method="c3", c3_mask_smooth_fraction=0.02)
    sigma = spatial_sigma(image.shape, params.c3_mask_smooth_fraction)
    margin = int(np.ceil(4 * sigma)) + 1
    out, _ = compensate_c3(image, params)
    np.testing.assert_array_equal(out[:, : 48 - margin], image[:, : 48 - margin])
    assert np.abs(out[:, 60:] - image[:, 60:]).max() > 0.01  # the dark side does change
    # Control: with the threshold above every pixel, the bright side changes too.
    unmasked, _ = compensate_c3(image, dataclasses.replace(params, c3_mask_threshold=1.0))
    assert np.abs(unmasked[:, : 48 - margin] - image[:, : 48 - margin]).max() > 0.01


# --- white balance ----------------------------------------------------------------------


def test_white_balance_gray_world_gains_on_a_flat_colour_field() -> None:
    image = _flat(16, 24, (0.2, 0.4, 0.6))
    out, info = white_balance(image, Params())
    assert info.target == pytest.approx(0.4)
    assert info.gray_world_gains == pytest.approx((2.0, 1.0, 2.0 / 3.0), rel=1e-6)
    assert info.applied_gains == pytest.approx((2.0, 1.0, 2.0 / 3.0), rel=1e-6)
    assert info.clamped == (False, False, False)
    np.testing.assert_allclose(out, 0.4, atol=1e-6)


def test_white_balance_strength_interpolates_the_gains() -> None:
    _, info = white_balance(_flat(8, 8, (0.2, 0.4, 0.6)), Params(white_balance_strength=0.5))
    assert info.requested_gains == pytest.approx((1.5, 1.0, 1 - 1 / 6), rel=1e-6)
    _, none = white_balance(_flat(8, 8, (0.2, 0.4, 0.6)), Params(white_balance_strength=0.0))
    assert none.applied_gains == (1.0, 1.0, 1.0)


def test_white_balance_gain_clamp_holds_the_maximum() -> None:
    image = _flat(16, 24, (0.05, 0.4, 0.6))
    out, info = white_balance(image, Params(max_white_balance_gain=3.0))
    assert info.gray_world_gains[0] == pytest.approx(7.0, rel=1e-6)
    assert info.applied_gains[0] == 3.0
    assert info.clamped == (True, False, False)
    np.testing.assert_allclose(out[..., 0], 0.15, atol=1e-6)


# --- fusion inputs ----------------------------------------------------------------------


def test_fusion_inputs_follow_the_paper() -> None:
    image = _synthetic(64, 96)
    input1, input2 = fusion_inputs(image, Params(gamma=2.0, sharpen_strength=0.0))
    np.testing.assert_allclose(input1, image**2, atol=1e-6)
    np.testing.assert_array_equal(input2, image)
    _, sharpened = fusion_inputs(image, Params(normalisation_low=0.0, normalisation_high=100.0))
    # S = (I + N{.}) / 2 with N{} spanning exactly [0, 1].
    stretched = 2 * sharpened - image
    assert stretched.min() == pytest.approx(0.0, abs=1e-5)
    assert stretched.max() == pytest.approx(1.0, abs=1e-5)


def test_sharpening_of_a_flat_image_uses_the_midpoint() -> None:
    image = _flat(16, 16, (0.2, 0.4, 0.6))
    _, sharpened = fusion_inputs(image, Params())
    np.testing.assert_allclose(sharpened, (image + 0.5) / 2, atol=1e-6)


# --- neutral parameters, blend, resolution independence ---------------------------------


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("method", METHODS)
def test_neutral_params_reproduce_the_input(size: tuple[int, int], method: str) -> None:
    image = _synthetic(*size)
    params = dataclasses.replace(Params.neutral(), method=method)  # type: ignore[arg-type]
    result = correct(image, params)
    assert np.abs(result.output - image).max() <= NEUTRAL_TOLERANCE


def test_blend_with_original_runs_from_corrected_to_original() -> None:
    image = _synthetic(64, 96)
    corrected = correct(image, Params()).output
    np.testing.assert_array_equal(correct(image, Params(blend_with_original=1.0)).output, image)
    half = correct(image, Params(blend_with_original=0.5)).output
    np.testing.assert_allclose(half, (corrected + image) / 2, atol=1e-6)


@pytest.mark.parametrize("method", METHODS)
def test_output_is_resolution_independent_at_2x(method: str) -> None:
    large = _smooth_scene(128, 192)
    small = _box_down2(large)
    # Fractions large enough that every spatial scale is resolved on the 64 px short side.
    params = Params(
        method=method,  # type: ignore[arg-type]
        laplacian_fraction=0.02,
        saliency_blur_fraction=0.02,
        sharpen_blur_fraction=0.03,
        c3_kernel_fraction=0.1,
        c3_mask_smooth_fraction=0.03,
        pyramid_min_level_size=8,
    )
    from_large = _box_down2(correct(large, params).output)
    from_small = correct(small, params).output
    difference = np.abs(from_large - from_small)
    assert difference.mean() <= RESOLUTION_MEAN_TOLERANCE
    assert np.percentile(difference, 99) <= RESOLUTION_P99_TOLERANCE


@pytest.mark.parametrize("method", METHODS)
def test_default_params_are_resolution_independent_at_2x(method: str) -> None:
    large = _textured_scene(512, 768)
    assert (large.mean(axis=2) > 0.85).mean() > 0.02  # the 3C mask is active
    params = Params(method=method)  # type: ignore[arg-type]
    from_large = _box_down2(correct(large, params).output)
    from_small = correct(_box_down2(large), params).output
    difference = np.abs(from_large - from_small)
    assert difference.mean() <= DEFAULTS_RESOLUTION_MEAN_TOLERANCE
    assert np.percentile(difference, 99) <= DEFAULTS_RESOLUTION_P99_TOLERANCE


def test_spatial_sigma_is_a_fraction_of_the_short_side() -> None:
    assert spatial_sigma((300, 400, 3), 0.01) == pytest.approx(3.0)
    assert spatial_sigma((400, 300), 0.01) == pytest.approx(3.0)
    assert spatial_sigma((10, 10, 3), 0.001) == pytest.approx(0.01)  # no floor


# --- parameters ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "changes",
    [
        {"method": "other"},
        {"alpha": -0.1},
        {"gamma": 0.0},
        {"red_gain_cap": -1.0},
        {"normalisation_low": 60.0, "normalisation_high": 50.0},
        {"normalisation_high": 101.0},
        {"pyramid_min_level_size": 0},
        {"blend_with_original": 1.5},
        {"laplacian_fraction": 0.0},
        {"max_white_balance_gain": 0.5},
        {"pyramid_min_level_size": 1.5},
        {"pyramid_min_level_size": "16"},
        {"pyramid_min_level_size": True},
        {"alpha": "1"},
        {"blue_compensation": 1},
        {"red_gain_cap": "2"},
        {"kappa": float("nan")},
    ],
)
def test_params_reject_unusable_values(changes: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        Params(**changes)  # type: ignore[arg-type]


def test_white_balance_strength_zero_is_neutral_at_any_allowed_maximum() -> None:
    image = _synthetic(16, 16)
    params = Params(white_balance_strength=0.0, max_white_balance_gain=1.0)
    out, info = white_balance(image, params)
    np.testing.assert_array_equal(out, image)
    assert info.applied_gains == (1.0, 1.0, 1.0)


def test_params_accept_numpy_scalars_and_disabled_caps() -> None:
    params = Params(alpha=np.float32(0.5), pyramid_min_level_size=np.int64(8))  # type: ignore[arg-type]
    assert params.alpha == 0.5
    assert Params(red_gain_cap=None, blue_gain_cap=None).red_gain_cap is None


def test_neutral_params() -> None:
    neutral = Params.neutral()
    assert (neutral.alpha, neutral.c3_strength, neutral.white_balance_strength) == (0, 0, 0)
    assert (neutral.gamma, neutral.sharpen_strength, neutral.blend_with_original) == (1, 0, 0)


# --- run.py -------------------------------------------------------------------------------


def _png_header(path: Path) -> tuple[int, int, int, int]:
    data = path.read_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    assert data[12:16] == b"IHDR"
    width, height, depth, colour = struct.unpack(">IIBB", data[16:26])
    return width, height, depth, colour


def _read_png16(path: Path) -> np.ndarray:
    """Decode a PNG written by run.write_png16 (one IDAT, filter type 0)."""
    data = path.read_bytes()
    width, height, _, colour = _png_header(path)
    channels = 3 if colour == 2 else 1
    length = struct.unpack(">I", data[33:37])[0]
    assert data[37:41] == b"IDAT"
    raw = np.frombuffer(zlib.decompress(data[41 : 41 + length]), dtype=np.uint8)
    rows = raw.reshape(height, 1 + width * channels * 2)
    assert (rows[:, 0] == 0).all()
    samples = rows[:, 1:].copy().view(">u2").reshape(height, width, channels)
    return samples.squeeze()


def _write_input(tmp_path: Path, size: tuple[int, int] = (40, 56)) -> Path:
    image = (_synthetic(*size) * 255).round().astype(np.uint8)
    path = tmp_path / "scene.png"
    Image.fromarray(image).save(path)
    return path


def test_write_png16_round_trips(tmp_path: Path) -> None:
    rgb = _synthetic(5, 7)
    run.write_png16(tmp_path / "rgb.png", rgb)
    np.testing.assert_array_equal(
        _read_png16(tmp_path / "rgb.png"), np.round(rgb * 65535).astype(np.uint16)
    )
    gray = rgb[..., 1].copy()
    run.write_png16(tmp_path / "gray.png", gray)
    assert _png_header(tmp_path / "gray.png") == (7, 5, 16, 0)
    with Image.open(tmp_path / "rgb.png") as opened:  # a valid PNG to an independent reader
        assert opened.size == (7, 5)
    with pytest.raises(ValueError, match="shape"):
        run.write_png16(tmp_path / "bad.png", np.zeros((2, 2, 4), np.float32))


@pytest.mark.parametrize("method", METHODS)
def test_run_writes_a_16_bit_png(tmp_path: Path, method: str) -> None:
    source = _write_input(tmp_path)
    out = tmp_path / "out"
    assert run.main(["--in", str(source), "--out", str(out), "--method", method]) == 0
    written = out / f"scene-{method}.png"
    assert _png_header(written) == (56, 40, 16, 2)
    assert _read_png16(written).shape == (40, 56, 3)


def test_run_dump_writes_every_intermediate(tmp_path: Path) -> None:
    source = _write_input(tmp_path)
    out = tmp_path / "out"
    assert run.main(["--in", str(source), "--out", str(out), "--dump", "--blue"]) == 0
    stem = "scene-ancuti2018"
    expected = {f"{stem}.png"}
    expected |= {
        f"{stem}-{stage}.png"
        for stage in ("compensated", "white-balanced", "input1", "input2", "fused")
    }
    for kind in ("laplacian", "saliency", "saturation", "aggregated", "normalised"):
        expected |= {f"{stem}-weight-{kind}{index}.png" for index in (1, 2)}
    expected |= {f"{stem}-{name}.json" for name in ("compensation", "white-balance", "weights")}
    assert {p.name for p in out.iterdir()} == expected
    compensation = (out / f"{stem}-compensation.json").read_text(encoding="utf-8")
    assert '"blue"' in compensation


def test_run_neutral_and_overrides(tmp_path: Path) -> None:
    source = _write_input(tmp_path)
    out = tmp_path / "out"
    args = ["--in", str(source), "--out", str(out), "--neutral", "--set", "red_gain_cap=none"]
    assert run.main([*args, "--set", "blue_compensation=true", "--set", "gamma=1"]) == 0
    written = _read_png16(out / "scene-ancuti2018.png").astype(np.float64) / 65535
    with Image.open(source) as opened:
        original = np.asarray(opened, dtype=np.float64) / 255
    assert np.abs(written - original).max() < 1e-4


@pytest.mark.parametrize(
    "extra",
    [
        ["--method", "bogus"],
        ["--set", "nosuch=1"],
        ["--set", "gamma"],
        ["--set", "gamma=abc"],
        ["--set", "gamma=-1"],
        ["--set", "blue_compensation=maybe"],
        ["--frobnicate"],
    ],
)
def test_run_bad_arguments_exit_2(
    tmp_path: Path, extra: list[str], capsys: pytest.CaptureFixture[str]
) -> None:
    source = _write_input(tmp_path)
    assert run.main(["--in", str(source), "--out", str(tmp_path / "out"), *extra]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: ")
    assert err.count("\n") == 1
    assert not (tmp_path / "out").exists()


def test_run_missing_arguments_exit_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert run.main(["--out", str(tmp_path)]) == 2
    assert capsys.readouterr().err.count("\n") == 1


@pytest.mark.parametrize("content", [None, b"not an image"])
def test_run_unreadable_image_exits_2(
    tmp_path: Path, content: bytes | None, capsys: pytest.CaptureFixture[str]
) -> None:
    source = tmp_path / "broken.png"
    if content is not None:
        source.write_bytes(content)
    assert run.main(["--in", str(source), "--out", str(tmp_path / "out")]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: cannot read image broken.png")
    assert err.count("\n") == 1


def test_run_oversized_image_exits_2(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    # A PNG header announcing 20000 x 20000 pixels trips Pillow's decompression-bomb error.
    header = struct.pack(">IIBBBBB", 20000, 20000, 8, 2, 0, 0, 0)
    chunk = struct.pack(">I", len(header)) + b"IHDR" + header
    chunk += struct.pack(">I", zlib.crc32(b"IHDR" + header) & 0xFFFFFFFF)
    source = tmp_path / "huge.png"
    source.write_bytes(b"\x89PNG\r\n\x1a\n" + chunk)
    assert run.main(["--in", str(source), "--out", str(tmp_path / "out")]) == 2
    err = capsys.readouterr().err
    assert err.startswith("error: cannot read image huge.png")
    assert err.count("\n") == 1


def test_read_image_modes_and_notes(tmp_path: Path) -> None:
    gray16 = np.array([[0, 32768, 65535]], dtype=np.uint16)
    Image.fromarray(gray16).save(tmp_path / "gray16.png")
    image, notes = run.read_image(tmp_path / "gray16.png")
    assert image.shape == (1, 3, 3)
    np.testing.assert_allclose(image[0, :, 0], gray16[0] / 65535, atol=1e-7)
    assert notes == []

    rgba = np.zeros((2, 2, 4), dtype=np.uint8)
    rgba[..., 0] = 255
    Image.fromarray(rgba).save(tmp_path / "rgba.png")
    image, _ = run.read_image(tmp_path / "rgba.png")
    np.testing.assert_array_equal(image[0, 0], [1.0, 0.0, 0.0])

    run.write_png16(tmp_path / "rgb16.png", _synthetic(4, 4))
    _, notes = run.read_image(tmp_path / "rgb16.png")
    assert any("16-bit RGB" in note for note in notes)


def test_run_works_as_a_script(tmp_path: Path) -> None:
    source = _write_input(tmp_path, (24, 32))
    script = Path(__file__).resolve().parent.parent / "tools" / "prototype" / "run.py"
    completed = subprocess.run(
        [sys.executable, str(script), "--in", str(source), "--out", str(tmp_path / "o")],
        capture_output=True,
        text=True,
        check=False,
        timeout=120,
    )
    assert completed.returncode == 0, completed.stderr
    assert (tmp_path / "o" / "scene-ancuti2018.png").is_file()
