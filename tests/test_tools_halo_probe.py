"""Unit tests of the WP5.7 halo probe (``tools/halo_probe.py``) on synthetic edges.

Parallel leg: CPU only, no footage. Each band test has a twin that must NOT see a band (or must
see one), so a probe that measured nothing, or always measured something, fails here. The
step-2A tests (Reviewer A round 0) add the reviewer's controls: a pure contrast remap reports no
band, a one-sample spike or plateau noise never qualifies, a weak edge is undecided, the
attribution adds up to the detected band, and every write stays inside ``<working>/wp5.7``.
The step-2B tests (CHARC's rulings S1 and S2) add the pointwise controls (a sharpened source
through x^1.5 or a 1.2 gain is no band at its own stage, still a band at input 2) and the
attributed stage (fused first, input 2 attributed).
"""

from __future__ import annotations

import dataclasses
import json
import math
import os
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from scipy import ndimage

import halo_probe as hp
from clearwater.interfaces import ColorDescription, Image
from clearwater.io.photo.png import write_png
from clearwater.methods import AncutiFusionMethod
from local_config import LocalConfig

SRGB = ColorDescription("bt709", "srgb", "identity", "full", 8, False, None)

FWHM_PER_SIGMA = 2.0 * math.sqrt(2.0 * math.log(2.0))
"""The full width at half maximum of a Gaussian, in its sigmas."""


def _step(n: int = 241, *, bright: float = 0.6, dark: float = 0.2) -> np.ndarray:
    """A 1-D step: bright water for the first half, a dark object after (edge between samples)."""
    out = np.full(n, dark)
    out[: n // 2] = bright
    return out


def _unsharp(profile: np.ndarray, sigma: float, amount: float = 1.0) -> np.ndarray:
    """Unsharp mask ``I + amount * (I - G*I)`` of a 1-D profile (the classic halo maker)."""
    return profile + amount * (profile - ndimage.gaussian_filter1d(profile, sigma, mode="nearest"))


def _ring(n: int, edge: int, *, height: float, sigma: float, offset: float) -> np.ndarray:
    """A Gaussian bump on the water side, ``offset`` samples before the edge (zero after it)."""
    index = np.arange(n, dtype=np.float64)
    bump = height * np.exp(-0.5 * ((index - (edge - offset)) / sigma) ** 2)
    out: np.ndarray = bump * (index <= edge)
    return out


# --- line_profile ---


def test_line_profile_samples_a_plane_exactly() -> None:
    yy, xx = np.mgrid[0:50, 0:80].astype(np.float64)
    plane = 0.01 * xx + 0.002 * yy
    line = hp.Line(10.0, 20.0, 60.0, 20.0)
    profile = hp.line_profile(plane, line, half_width=3)
    expected = 0.01 * np.arange(10, 61) + 0.002 * 20
    assert profile.shape == (51,)
    np.testing.assert_allclose(profile, expected, atol=1e-12)


def test_line_profile_diagonal_and_averaging() -> None:
    yy, xx = np.mgrid[0:100, 0:100].astype(np.float64)
    plane = (xx + yy) / 200.0
    line = hp.Line(20.0, 20.0, 60.0, 60.0)  # along the gradient
    profile = hp.line_profile(plane, line, half_width=4)  # the parallels lie on iso-lines
    t = np.linspace(0, 1, profile.size)
    np.testing.assert_allclose(profile, (40 + 80 * t) / 200.0, atol=1e-12)
    noisy = plane + np.random.default_rng(1).normal(0, 0.05, plane.shape)
    single = hp.line_profile(noisy, hp.Line(10, 50, 90, 50), half_width=0)
    wide = hp.line_profile(noisy, hp.Line(10, 50, 90, 50), half_width=8)
    assert np.std(np.diff(wide)) < np.std(np.diff(single)) / 2  # averaging lowers the noise


def test_line_profile_refusals() -> None:
    with pytest.raises(ValueError, match="at least 4"):
        hp.line_profile(np.zeros((10, 10)), hp.Line(1, 1, 2, 2))
    with pytest.raises(ValueError, match=r"\(H, W\)"):
        hp.line_profile(np.zeros((10, 10, 3)), hp.Line(1, 1, 8, 8))


def test_line_profile_refuses_a_strip_that_leaves_the_array() -> None:
    # Fix 5: the averaging strip is never clamped into the array (a clamp repeats edge pixels).
    plane = np.zeros((40, 60))
    assert hp.line_profile(plane, hp.Line(5, 4, 50, 4), half_width=4).size == 46  # rows 0..8
    with pytest.raises(ValueError, match="leaves"):
        hp.line_profile(plane, hp.Line(5, 3, 50, 3), half_width=4)  # row -1
    with pytest.raises(ValueError, match="leaves"):
        hp.line_profile(plane, hp.Line(5, 20, 60, 20), half_width=0)  # column 60


# --- the step edge (the two-sided diagnostic) ---


def test_clean_step_has_no_band() -> None:
    stats = hp.band_statistics(_step())
    assert stats["contrast"] == pytest.approx(0.4, abs=1e-9)
    assert stats["band"] < 1e-9
    assert not stats["exceeds"]
    fits = hp.profile_fits(_step())
    assert fits.edge in (119, 120)  # between the two levels
    assert fits.high_first


@pytest.mark.parametrize("sigma", [6.0, 12.0])
def test_unsharp_step_band_matches_the_analytic_overshoot(sigma: float) -> None:
    clean = _step(481)
    halo = _unsharp(clean, sigma)
    stats = hp.band_statistics(halo)
    # Continuous step: the high-pass at distance d is C * (1 - Phi(d / sigma)); the nearest
    # sample is half a pixel from the edge, so the peak is just under C / 2 on each side.
    expected = 0.5 - 0.5 * math.erf(0.5 / sigma / math.sqrt(2))
    assert stats["band_ratio"] == pytest.approx(expected, rel=0.08)
    assert stats["overshoot_ratio"] == pytest.approx(stats["undershoot_ratio"], rel=0.02)
    assert stats["exceeds"]
    assert stats["peak_distance_px"] <= 1
    # Half maximum where 1 - Phi(d / sigma) = expected / 2: d is about 0.73 sigma.
    assert stats["fwhm_px"] == pytest.approx(0.73 * sigma, abs=1.5)


def test_band_width_scales_with_the_sharpening_sigma() -> None:
    narrow = hp.band_statistics(_unsharp(_step(601), 8.0))
    wide = hp.band_statistics(_unsharp(_step(601), 16.0))
    assert wide["fwhm_px"] / narrow["fwhm_px"] == pytest.approx(2.0, rel=0.25)
    assert wide["extent_px"] > narrow["extent_px"]


# --- the water-side band (the table's metric) ---


def test_water_band_is_zero_against_itself_and_counts_only_outward_overshoot() -> None:
    clean = _step(401)
    fits = hp.profile_fits(clean)
    same = hp.water_band(clean, clean, fits)
    assert same["band_ratio"] == 0.0
    assert not same["exceeds"]
    assert same["verdict"] == "none"
    halo = hp.water_band(_unsharp(clean, 8.0), clean, fits)
    assert halo["qualifies"]
    assert halo["verdict"] == "band"
    assert halo["band"] > 0.3  # a bright ring in the water beside a dark object
    # A glow (the object's level spreading into the water) is not an overshoot past the
    # water's plateau: it is no band.
    index = np.arange(clean.size)
    glow = clean - 0.15 * np.exp(-(((index - fits.edge) / 25.0) ** 2)) * (index <= fits.edge)
    inward = hp.water_band(glow, clean, fits)
    assert inward["band_ratio"] == 0.0
    assert not inward["qualifies"]


def test_water_band_bright_object_on_dark_water() -> None:
    clean = _step(401, bright=0.2, dark=0.7)  # start side (water) dark, object bright
    fits = hp.profile_fits(clean)
    halo = hp.water_band(_unsharp(clean, 8.0), clean, fits)
    assert halo["contrast"] < 0  # the source's signed contrast, shared by every stage
    assert halo["qualifies"]  # the dark ring beside a bright object
    assert halo["band"] > 0.3


def test_reviewer_control_object_plateau_change_is_no_band() -> None:
    # Reviewer A round 0, finding 1: a Gaussian-softened 0.6/0.2 step (sigma 8); the stage
    # raises only the distant object plateau by 0.2. Every water-side sample is identical.
    clean = ndimage.gaussian_filter1d(_step(241), 8.0, mode="nearest")
    fits = hp.profile_fits(clean)
    stage = clean.copy()
    stage[fits.edge + 40 :] += 0.2
    np.testing.assert_array_equal(stage[: fits.edge + 1], clean[: fits.edge + 1])
    stats = hp.water_band(stage, clean, fits)
    assert stats["band_ratio"] < 1e-9
    assert not stats["exceeds"]


def _softened_gray_step(height: int = 128, width: int = 192, sigma: float = 4.0) -> np.ndarray:
    """A monotonic softened 0.8/0.05 grey step across a vertical edge at x = 96 (bright left)."""
    x = np.arange(width, dtype=np.float64)
    values = 0.05 + 0.75 * 0.5 * (1.0 - np.vectorize(math.erf)((x - 95.5) / (sigma * math.sqrt(2))))
    plane = np.broadcast_to(values, (height, width))
    return np.ascontiguousarray(np.repeat(plane[..., None], 3, axis=2), dtype=np.float32)


def test_reviewer_control_gamma_on_a_monotonic_step_is_no_band() -> None:
    # Reviewer A round 0, finding 1: the real product at the shipped c3 defaults on a monotonic
    # softened 0.8/0.05 step. Grey, so compensation and white balance are identities; gamma is
    # a monotonic remap and makes no overshoot beyond either plateau.
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = Image(pixels=_softened_gray_step(), device="cpu", color=SRGB, orientation_applied=True)
    statistics = hp.photo_statistics(method, image, params)
    line = hp.Line(20.0, 64.0, 172.0, 64.0)
    frame = hp.probe_frame(
        method,
        image,
        params,
        statistics,
        lines=[line],
        region=hp.region_for([line], image.pixels.shape, 10),
        half_width=2,
        threshold=0.1,
        crops=None,
        prefix="photo",
    )
    water = frame["lines"][0]["water"]
    for stage in ("compensated", "balanced", "input1"):
        assert water[stage]["Y"]["band_ratio"] < 0.01, stage
    assert frame["lines"][0]["first_stage_over_threshold"] not in ("compensated", "balanced")
    assert frame["lines"][0]["first_stage_over_threshold"] != "input1"


# --- qualification: support, noise, weak edges ---


def test_reviewer_control_one_sample_spike_does_not_qualify() -> None:
    # Reviewer A round 0, finding 3: a clean 0.4-contrast step with 0.041 added at ONE
    # water-side sample read as a 10.25 % band of width 1 px.
    clean = _step(241)
    fits = hp.profile_fits(clean)
    spiked = clean.copy()
    spiked[fits.edge - 10] += 0.041
    stats = hp.water_band(spiked, clean, fits)
    assert stats["band_ratio"] == pytest.approx(0.1025, abs=1e-9)
    assert stats["exceeds"]  # over the threshold ...
    assert stats["support_samples"] == 1
    assert not stats["qualifies"]  # ... but one sample is not a band
    assert stats["verdict"] == "undecided"


def test_plateau_noise_does_not_qualify_and_a_real_ring_through_it_does() -> None:
    clean = _step(401)
    fits = hp.profile_fits(clean)
    # Correlated noise (Gaussian-filtered, sigma 2 px), RMS 0.02 = 5 % of the 0.4 contrast. The
    # seed is the one whose excursion reaches 0.20 of C over a broad run: three times the
    # plateau's residual RMS alone would have called it a band (the extrapolated line's error
    # is what the uncertainty adds).
    rng = np.random.default_rng(6)
    noise = ndimage.gaussian_filter1d(rng.normal(0, 1, clean.size), 2.0)
    noise *= 0.02 / np.std(noise)
    noise[fits.edge + 1 :] = 0.0
    noisy = clean + noise
    stats = hp.water_band(noisy, clean, fits)
    assert stats["band"] > 0.19  # noise alone crosses 10 % of the edge ...
    assert stats["exceeds"]
    assert stats["noise_ratio"] > 0.05
    assert not stats["qualifies"]  # ... but not the noise level
    assert stats["verdict"] == "undecided"
    ring = noisy + _ring(clean.size, fits.edge, height=0.2, sigma=4.0, offset=12)
    assert hp.water_band(ring, clean, fits)["qualifies"]


def test_weak_edge_is_undecided_whatever_its_band() -> None:
    clean = _step(241, bright=0.5, dark=0.485)  # contrast 0.015 < MIN_CONTRAST
    fits = hp.profile_fits(clean)
    ring = clean + _ring(clean.size, fits.edge, height=0.01, sigma=4.0, offset=10)
    stats = hp.water_band(ring, clean, fits)
    assert stats["weak_edge"]
    assert stats["band_ratio"] > 0.5
    assert not stats["qualifies"]
    assert stats["verdict"] == "undecided"


# --- widths ---


def test_widths_interpolate_the_crossings_and_use_the_sample_spacing() -> None:
    clean = _step(401)
    fits = hp.profile_fits(clean)
    ring = clean + _ring(clean.size, fits.edge, height=0.12, sigma=2.5, offset=20)
    stats = hp.water_band(ring, clean, fits)
    assert stats["fwhm_px"] == pytest.approx(FWHM_PER_SIGMA * 2.5, abs=0.15)  # 5.89, not 5
    doubled = hp.water_band(ring, clean, fits, spacing=2.0)
    assert doubled["fwhm_px"] == pytest.approx(2.0 * stats["fwhm_px"])
    assert doubled["peak_distance_px"] == pytest.approx(2.0 * stats["peak_distance_px"])
    assert hp.sample_spacing(hp.Line(0.0, 0.0, 10.6, 0.0)) == pytest.approx(10.6 / 11)
    assert hp.sample_spacing(hp.Line(0.0, 0.0, 30.0, 40.0)) == pytest.approx(1.0)


# --- the first-stage selector ---


def _stage_bands(planted: set[str], *, spike: bool = False) -> dict[str, dict[str, Any]]:
    """Per product stage, the water band of a clean step, with a ring (or spike) where planted."""
    clean = _step(241)
    fits = hp.profile_fits(clean)
    extra = _ring(clean.size, fits.edge, height=0.12, sigma=3.0, offset=6)
    if spike:
        extra = np.zeros(clean.size)
        extra[fits.edge - 10] = 0.041
    return {
        stage: hp.water_band(clean + extra if stage in planted else clean, clean, fits)
        for stage in hp.PRODUCT_STAGES[1:]
    }


@pytest.mark.parametrize("stage", hp.PRODUCT_STAGES[1:])
def test_first_stage_names_the_one_stage_with_a_planted_band(stage: str) -> None:
    # A band planted in one stage only (input 1 only, input 2 only, ...): the selector names
    # that stage, so a selector that returned a constant stage fails all but one case.
    assert hp.first_stage(_stage_bands({stage})) == stage


def test_first_stage_follows_a_band_that_persists_from_where_it_appears() -> None:
    stages = list(hp.PRODUCT_STAGES[1:])
    for position, stage in enumerate(stages):
        assert hp.first_stage(_stage_bands(set(stages[position:]))) == stage
    assert hp.first_stage(_stage_bands(set())) is None


def test_first_stage_is_undecided_on_a_spike_or_a_weak_edge() -> None:
    # Finding 3: the spike placed in ``compensated`` (and carried on) once named compensation.
    stages = set(hp.PRODUCT_STAGES[1:])
    assert hp.first_stage(_stage_bands(stages, spike=True)) == "undecided"
    weak = _step(241, bright=0.5, dark=0.485)
    fits = hp.profile_fits(weak)
    ring = weak + _ring(weak.size, fits.edge, height=0.01, sigma=3.0, offset=6)
    bands = {stage: hp.water_band(ring, weak, fits) for stage in hp.PRODUCT_STAGES[1:]}
    assert hp.first_stage(bands) == "undecided"


# --- the staged render follows the product -------------------------------------------------------


def _scene(height: int = 96, width: int = 128) -> np.ndarray:
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    rgb = np.stack([0.15 + 0.001 * xx, 0.45 + 0.0008 * yy, 0.55 + 0.0005 * xx], axis=2)
    disc = np.hypot(xx - 80, yy - 48) <= 22
    rgb[disc] = [0.35, 0.3, 0.25]
    noise = np.random.default_rng(7).normal(0, 0.01, rgb.shape).astype(np.float32)
    return np.ascontiguousarray((rgb + noise).clip(0, 1), dtype=np.float32)


def _halo_scene(height: int = 128, width: int = 176) -> np.ndarray:
    """Water with a gentle gradient, a dark disc, and an in-camera halo already in the source."""
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float64)
    rgb = np.stack([0.25 + 0.0004 * xx, 0.45 + 0.0003 * yy, 0.5 + 0.0002 * xx], axis=2)
    disc = np.hypot(xx - 110, yy - 64) <= 30
    rgb[disc] = [0.12, 0.2, 0.22]
    rgb = ndimage.gaussian_filter(rgb, (1.0, 1.0, 0))
    rgb = rgb + 0.6 * (rgb - ndimage.gaussian_filter(rgb, (6.0, 6.0, 0)))  # in-camera sharpening
    rgb = rgb + np.random.default_rng(5).normal(0, 0.002, rgb.shape)
    return np.ascontiguousarray(rgb.clip(0, 1), dtype=np.float32)


def test_staged_render_equals_the_product_render(tmp_path: Path) -> None:
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = Image(pixels=_scene(), device="cpu", color=SRGB, orientation_applied=True)
    statistics = hp.photo_statistics(method, image, params)
    names = [name for name, _ in hp.staged_render(method, image, params, statistics)]
    assert names[:5] == ["source", "compensated", "balanced", "high_pass", "stretched"]
    for stage in hp.IMAGE_STAGES:
        assert stage in names
    levels = hp.pyramid_levels((96, 128), params["pyramid_min_level_size"])
    assert sum(name.startswith("term_") for name in names) == 2 * levels
    assert sum(name.startswith("srcterm_") for name in names) == 2 * levels
    assert names[-1] == "prefused"
    line = hp.Line(30.0, 48.0, 90.0, 48.0)
    frame = hp.probe_frame(
        method,
        image,
        params,
        statistics,
        lines=[line],
        region=hp.region_for([line], (96, 128, 3), 10),
        half_width=1,
        threshold=0.1,
        crops=tmp_path,
        prefix="photo",
    )
    assert frame["render_check_equal"]
    assert frame["prefused_check_equal"]
    assert (tmp_path / "photo-input2.png").read_bytes()[24] == 16  # IHDR bit depth
    assert (tmp_path / "photo-output-marked.png").exists()
    assert not (tmp_path / "photo-prefused.png").exists()


ATTRIBUTION_TOLERANCE = 1e-4
"""The attribution's sum may differ from the detected band by this much (contrast units): the
terms are float32 images summed in a different order from the product's own collapse."""


def test_attribution_adds_up_to_the_detected_added_band() -> None:
    # Fix 2: the per-input and per-level attributions measure the SAME quantity the detection
    # reports (the added band at its peak, over the source's contrast), the clip's share apart.
    # The sharpening blur is widened (0.03 of the short side, 3.8 px here) so the ring spans
    # more than MIN_SUPPORT_SAMPLES on this small frame; the decomposition does not depend on it.
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, ["sharpen_blur_fraction=0.03"])
    image = Image(pixels=_halo_scene(), device="cpu", color=SRGB, orientation_applied=True)
    statistics = hp.photo_statistics(method, image, params)
    line = hp.Line(40.0, 64.0, 120.0, 64.0)
    frame = hp.probe_frame(
        method,
        image,
        params,
        statistics,
        lines=[line],
        region=hp.region_for([line], image.pixels.shape, 10),
        half_width=2,
        threshold=0.1,
        crops=None,
        prefix="photo",
    )
    record = frame["lines"][0]
    fused = record["water"]["fused"]["Y"]
    assert fused["verdict"] == "band"
    attribution = record["attribution"]
    assert attribution["peak_index"] == fused["peak_index"]
    assert record["attributed_stage"] == "input2"  # S2: the record carries both columns
    assert record["first_stage_over_threshold"] in hp.PRODUCT_STAGES[1:]
    assert attribution["clip"] == pytest.approx(0.0, abs=1e-9)  # the clip does not bind here
    assert attribution["source_subtracted"]  # the source's own halo is under the peak
    target = attribution["excess_at_peak"]
    assert target == pytest.approx(fused["band"], abs=1e-12)
    by_input = sum(attribution["per_input"].values()) + attribution["clip"]
    by_level = sum(attribution["per_level"].values()) + attribution["clip"]
    assert by_input == pytest.approx(target, abs=ATTRIBUTION_TOLERANCE)
    assert by_level == pytest.approx(target, abs=ATTRIBUTION_TOLERANCE)
    assert abs(attribution["residual"]) <= ATTRIBUTION_TOLERANCE
    # The test can fail: the raw terms (no source subtraction) miss the band by far more.
    raw = sum(attribution["raw_per_input"].values()) + attribution["clip"]
    assert abs(raw - target) > 100 * ATTRIBUTION_TOLERANCE


def _dark_water_scene(height: int = 128, width: int = 176) -> np.ndarray:
    """Near-black water (0.02) with a bright disc (0.5): the fused dark ring clips at 0."""
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float64)
    rgb = np.stack([0.0 + 0.0001 * xx, 0.02 + 0.0001 * yy, 0.01 + 0.0001 * xx], axis=2)
    rgb[np.hypot(xx - 110, yy - 64) <= 30] = [0.5, 0.53, 0.54]
    rgb = ndimage.gaussian_filter(rgb, (1.0, 1.0, 0))
    rgb = rgb + np.random.default_rng(5).normal(0, 0.002, rgb.shape)
    return np.ascontiguousarray(rgb.clip(0, 1), dtype=np.float32)


def test_attribution_carries_a_binding_clip() -> None:
    # Reviewer A round 1, finding 4: the final clip BINDS at the band's peak (a dark ring on
    # near-black water is cut at 0), so the clip's share is not zero, and the shares still add
    # up to the detected band only WITH it. Forcing the record's ``clip`` to 0 fails this test.
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, ["sharpen_blur_fraction=0.03"])
    image = Image(pixels=_dark_water_scene(), device="cpu", color=SRGB, orientation_applied=True)
    statistics = hp.photo_statistics(method, image, params)
    line = hp.Line(40.0, 64.0, 120.0, 64.0)
    frame = hp.probe_frame(
        method,
        image,
        params,
        statistics,
        lines=[line],
        region=hp.region_for([line], image.pixels.shape, 10),
        half_width=2,
        threshold=0.1,
        crops=None,
        prefix="photo",
    )
    record = frame["lines"][0]
    fused = record["water"]["fused"]["Y"]
    attribution = record["attribution"]
    assert fused["verdict"] == "band"
    assert attribution["clip"] < -100 * ATTRIBUTION_TOLERANCE  # about -0.016 of C
    target = attribution["excess_at_peak"]
    by_input = sum(attribution["per_input"].values()) + attribution["clip"]
    by_level = sum(attribution["per_level"].values()) + attribution["clip"]
    assert by_input == pytest.approx(target, abs=ATTRIBUTION_TOLERANCE)
    assert by_level == pytest.approx(target, abs=ATTRIBUTION_TOLERANCE)
    assert abs(attribution["residual"]) <= ATTRIBUTION_TOLERANCE


def test_stretched_stage_matches_the_input2_formula() -> None:
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = Image(pixels=_scene(), device="cpu", color=SRGB, orientation_applied=True)
    statistics = hp.photo_statistics(method, image, params)
    stages = dict(hp.staged_render(method, image, params, statistics))
    # At sharpen_strength 1, input2 = clip((I + N) / 2) with N the stretched high-pass.
    expected = ((stages["balanced"] + stages["stretched"]) / 2).clip(0, 1)
    np.testing.assert_allclose(stages["input2"], expected, atol=1e-6)


# --- step 2B: CHARC's S1 (pointwise reference) and S2 (attributed stage) rulings -------------


def _sharpened_step_profile(n: int = 241) -> np.ndarray:
    """The S1 control source: the unsharp-masked 0.6 / 0.2 step (sigma 8), in-camera style."""
    return _unsharp(_step(n), 8.0)


@pytest.mark.parametrize(
    ("stage", "remap", "face_value"),
    [("input1", lambda x: x**1.5, 0.1185), ("balanced", lambda x: 1.2 * x, 0.0950)],
)
def test_s1_pointwise_remap_of_a_sharpened_source_is_no_band(
    stage: str, remap: Any, face_value: float
) -> None:
    # S1: a pointwise stage is measured against the SOURCE remapped through its own operation,
    # so a monotonic tone remap of a source that already overshoots is charged nothing. Step 2A
    # measured the face values 0.1185 (x^1.5) and 0.0950 (a 1.2 gain) on these controls.
    source = _sharpened_step_profile()
    fits = hp.profile_fits(source)
    profile = remap(source)
    references = {"balanced": source, "input1": source, stage: profile}
    assert hp.water_band(profile, source, fits)["band"] == pytest.approx(face_value, abs=1e-4)
    stats = hp.stage_band(stage, profile, source, fits, references=references)
    assert stats["reference"] == "remapped_source"
    assert stats["band"] < 1e-9
    assert stats["verdict"] == "none"
    # The same profile at INPUT 2 is read at face value: its overshoot is still charged there.
    face = hp.stage_band("input2", profile, source, fits, references=references)
    assert face["reference"] == "source"
    assert face["band"] == pytest.approx(face_value, abs=1e-4)


def _sharpened_gray_image(height: int = 128) -> np.ndarray:
    """The S1 control as an image: the sharpened step across x (bright water left), grey."""
    plane = np.broadcast_to(_sharpened_step_profile(), (height, 241))
    return np.ascontiguousarray(np.repeat(plane[..., None], 3, axis=2), dtype=np.float32)


@pytest.mark.parametrize("gain", [None, 1.2])
def test_s1_controls_through_the_real_staged_render(gain: float | None) -> None:
    # S1 through the product at the shipped c3 defaults: grey, so compensation is an identity and
    # the measured gray-world gains are 1; ``gain`` replaces them with a linear 1.2 (the render
    # uses the supplied gains, as the export does). The step-2A probe charged input 1 0.1185
    # (gains 1) and white balance 0.0950 (gain 1.2), and at gain 1.2 named input 1 first.
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = Image(
        pixels=_sharpened_gray_image(), device="cpu", color=SRGB, orientation_applied=True
    )
    statistics = hp.photo_statistics(method, image, params)
    if gain is not None:
        balance = {**statistics["white_balance"], "gains": np.array([gain, gain, gain])}
        statistics = {**statistics, "white_balance": balance}
    line = hp.Line(20.0, 64.0, 220.0, 64.0)
    frame = hp.probe_frame(
        method,
        image,
        params,
        statistics,
        lines=[line],
        region=hp.region_for([line], image.pixels.shape, 10),
        half_width=2,
        threshold=0.1,
        crops=None,
        prefix="photo",
    )
    record = frame["lines"][0]
    water = record["water"]
    for stage in ("balanced", "input1"):
        assert water[stage]["Y"]["band"] < 1e-4, stage
        assert water[stage]["Y"]["verdict"] == "none", stage
    assert record["first_stage_over_threshold"] not in ("compensated", "balanced", "input1")
    for stage in ("balanced", "input1"):
        assert water[stage]["Y"]["reference"] == "remapped_source", stage
    # Input 2 stays at face value: it still reads the overshoot (its own and the source's).
    input2 = water["input2"]["Y"]
    assert input2["reference"] == "source"
    assert input2["exceeds"]
    assert water["fused"]["Y"]["reference"] == "source"


def test_s1_references_are_the_source_through_the_render_gains_and_gamma() -> None:
    # Reviewer A round 2, finding 4: a CHROMATIC scene, where 3C is not an identity, so the
    # source reference and the compensated image differ. Both references must be the SOURCE
    # through the supplied gains (strength, then the D99 clamp) and then the gamma, computed
    # here without the probe; the balanced and input-1 images themselves would fail this.
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = Image(pixels=_scene(), device="cpu", color=SRGB, orientation_applied=True)
    statistics = hp.photo_statistics(method, image, params)
    stages = dict(hp.staged_render(method, image, params, statistics))
    source = np.asarray(stages["source"], dtype=np.float64)
    assert np.abs(np.asarray(stages["compensated"]) - source).max() > 1e-3  # 3C acts here
    strength = params["white_balance_strength"]
    requested = 1.0 + strength * (np.asarray(statistics["white_balance"]["gains"]) - 1.0)
    gains = np.minimum(requested, params["max_white_balance_gain"])
    balanced = np.clip(source * gains, 0.0, 1.0)
    input1 = np.clip(balanced ** params["gamma"], 0.0, 1.0)
    np.testing.assert_allclose(stages["remap_balanced"], balanced, atol=1e-6)
    np.testing.assert_allclose(stages["remap_input1"], input1, atol=1e-6)
    # The control discriminates: the stage images are not the references here.
    assert np.abs(np.asarray(stages["balanced"]) - balanced).max() > 1e-3
    assert np.abs(np.asarray(stages["input1"]) - input1).max() > 1e-3


def _attribution_scene() -> tuple[dict[str, dict[str, Any]], dict[str, Any], dict[str, Any]]:
    """S2: a synthetic line whose fused band qualifies while input 2's own band does not.

    Input 2 carries a ring 1.6 times the fused one through sample-to-sample plateau noise
    (+-0.04, 10 % of the contrast: amplified grain), which lifts its qualifying level to about
    0.34 of C and breaks its support; the fused stage carries the clean ring (0.25 of C), 80 % of
    it in input 2's terms. Returns the per-stage luma bands, the attribution and the fused band.
    """
    clean = _step(401)
    fits = hp.profile_fits(clean)
    noise = 0.04 * (-1.0) ** np.arange(clean.size)
    noise[fits.edge + 1 :] = 0.0
    ring = _ring(clean.size, fits.edge, height=0.1, sigma=4.0, offset=12)
    input2 = clean + noise + 1.6 * ring
    fused = clean + ring
    bands = {
        "compensated": hp.water_band(clean, clean, fits),
        "balanced": hp.water_band(clean, clean, fits),
        "input1": hp.water_band(clean, clean, fits),
        "input2": hp.water_band(input2, clean, fits),
        "fused": hp.water_band(fused, clean, fits),
        "output": hp.water_band(fused, clean, fits),
    }
    profiles = {
        "source": clean,
        "fused": fused,
        "prefused": fused,
        "term_k1_l0": 0.5 * clean + 0.2 * ring,
        "term_k2_l0": 0.5 * clean + 0.8 * ring,
        "srcterm_k1_l0": 0.5 * clean,
        "srcterm_k2_l0": 0.5 * clean,
    }
    attribution = hp.attribute_band(bands["fused"], profiles, fits)
    assert attribution is not None
    return bands, attribution, bands["fused"]


def test_s2_fused_first_and_input2_attributed() -> None:
    bands, attribution, fused = _attribution_scene()
    assert bands["input2"]["exceeds"]
    assert bands["input2"]["verdict"] == "undecided"  # its own level is noisier ...
    assert fused["verdict"] == "band"  # ... while the fused band qualifies
    assert hp.first_stage(bands) == "fused"
    assert attribution["per_input"]["k2"] == pytest.approx(0.8 * fused["band"], abs=1e-9)
    assert hp.attributed_stage(fused, attribution) == "input2"


def test_s2_attributed_stage_rule_on_ties_and_unqualified_bands() -> None:
    _bands, attribution, fused = _attribution_scene()
    swapped = {**attribution, "per_input": {"k1": 0.6, "k2": 0.1}}
    assert hp.attributed_stage(fused, swapped) == "input1"
    tie = {**attribution, "per_input": {"k1": 0.2, "k2": 0.2 + hp.ATTRIBUTION_TIE / 2}}
    assert hp.attributed_stage(fused, tie) == "undecided"
    clipped = {**attribution, "per_input": {"k1": -0.01, "k2": -0.02}}
    assert hp.attributed_stage(fused, clipped) == "undecided"  # the inputs carry none of it
    assert hp.attributed_stage({**fused, "verdict": "undecided"}, attribution) == "undecided"
    assert hp.attributed_stage({**fused, "verdict": "none"}, None) == "none"


def test_resolve_parameters_overrides_by_type() -> None:
    method = AncutiFusionMethod("c3")
    values = hp.resolve_parameters(method, ["sharpen_strength=0.5", "pyramid_min_level_size=8"])
    assert values["sharpen_strength"] == 0.5
    assert values["pyramid_min_level_size"] == 8
    assert isinstance(values["pyramid_min_level_size"], int)
    assert values["gamma"] == 1.5  # untouched defaults
    with pytest.raises(hp.ProbeError):
        hp.resolve_parameters(method, ["no_such=1"])
    with pytest.raises(hp.ProbeError):
        hp.resolve_parameters(method, ["gamma=high"])


# --- the command line ---


@pytest.fixture
def working(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """A local configuration in ``tmp_path``; returns its ``<working>/wp5.7`` folder."""
    footage = tmp_path / "footage"
    footage.mkdir()
    work = tmp_path / "work"
    (work / "wp5.7").mkdir(parents=True)
    config = LocalConfig(footage_path=footage, working_path=work)
    monkeypatch.setattr(hp, "load_local_config", lambda path=None: config)
    monkeypatch.setattr(
        hp.headless_export, "configured_footage_folder", lambda config=None: footage
    )
    return work / "wp5.7"


def _scene_file(tmp_path: Path) -> Path:
    source = tmp_path / "scene.png"
    write_png(source, _scene(), bit_depth=16, icc=None, exif=None, provenance_json=None)
    return source


def test_main_on_a_synthetic_photo(tmp_path: Path, working: Path) -> None:
    source = _scene_file(tmp_path)
    out = working / "out"
    argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(working / "c")]
    status = hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"])
    assert status == 0
    record = json.loads((out / "scene.json").read_text(encoding="utf-8"))
    assert record["kind"] == "photo"
    assert record["method"] == "c3"
    frame = record["frames"][0]
    assert frame["render_check_equal"] is True
    assert set(frame["lines"][0]["water"]) == set(hp.IMAGE_STAGES)
    assert "fwhm_sigma" in frame["lines"][0]["water"]["fused"]["Y"]
    assert frame["lines"][0]["attributed_stage"] in ("input1", "input2", "undecided", "none")
    assert "attributed=" in hp.summary(record)
    assert (out / "photo-remap_input1.png").exists()  # the S1 reference is kept as a crop
    assert (out / "overview-output.png").exists()
    # A second run refuses to overwrite the record unless asked.
    assert hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"]) == 2
    replace = [*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu", "--replace"]
    assert hp.main(replace) == 0
    # Round 1, fix 2: the replaced publication is kept beside it, never deleted.
    kept = [p for p in working.iterdir() if p.name.startswith("out.replaced-")]
    assert len(kept) == 1
    assert (kept[0] / "scene.json").is_file()
    assert (out / "scene.json").is_file()
    assert not [p for p in working.iterdir() if "staging" in p.name or "failed" in p.name]


def _snapshot(folder: Path) -> dict[str, bytes]:
    """Every file under ``folder`` (relative path -> bytes)."""
    return {
        p.relative_to(folder).as_posix(): p.read_bytes()
        for p in sorted(folder.rglob("*"))
        if p.is_file()
    }


def _drift_render(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the product's render differ from the staged one (the probe's render check fails)."""
    original = AncutiFusionMethod.render

    def drifted(self: AncutiFusionMethod, *args: Any, **kwargs: Any) -> Image:
        result = original(self, *args, **kwargs)
        return dataclasses.replace(result, pixels=result.pixels + np.float32(1e-3))

    monkeypatch.setattr(AncutiFusionMethod, "render", drifted)


def test_main_failed_replace_leaves_the_prior_publication_untouched(
    tmp_path: Path, working: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Round 1, fix 2: a failed --replace run (render check, after the crops are made) neither
    # mixes new crops into the old record's folder nor publishes anything.
    source = _scene_file(tmp_path)
    out = working / "out"
    argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(working / "c")]
    assert hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"]) == 0
    before = _snapshot(out)
    _drift_render(monkeypatch)
    again = [*argv, "--line", "30,48,90,48", "--margin", "12", "--force-cpu", "--replace"]
    assert hp.main(again) == 1
    assert _snapshot(out) == before
    assert not [p for p in working.iterdir() if p.name.startswith("out.replaced-")]
    failed = [p for p in working.iterdir() if p.name.startswith(".out.failed-")]
    assert len(failed) == 1  # the failed run's partial output, kept under a failed name
    assert not (failed[0] / "scene.json").exists()


def test_main_fresh_run_publishes_only_on_success(
    tmp_path: Path, working: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _scene_file(tmp_path)
    out = working / "fresh"
    _drift_render(monkeypatch)
    argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(working / "c")]
    assert hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"]) == 1
    assert not out.exists()
    # A refusal inside the run, before anything was written, leaves no folder at all.
    monkeypatch.undo()
    refused = [*argv, "--line", "30,48,90,48", "--region", "0,0,20,20", "--force-cpu"]
    assert hp.main(refused) == 2
    assert not out.exists()
    assert len([p for p in working.iterdir() if p.name.startswith(".fresh.failed-")]) == 1


@pytest.mark.parametrize("kind", ["hard", "symbolic"])
def test_main_never_writes_through_a_link_planted_in_a_prior_output(
    tmp_path: Path, working: Path, kind: str
) -> None:
    # Round 1, fix 1: a prior output folder holding ``photo-source.png`` as a link to a
    # protected file (a CP5 pack PNG) must not truncate it: the run writes a fresh folder.
    source = _scene_file(tmp_path)
    out = working / "out"
    argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(working / "c")]
    assert hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"]) == 0
    protected = working.parent / "wp5.3" / "pair.png"
    protected.parent.mkdir()
    protected.write_bytes(b"CP5 evidence, read-only")
    planted = out / "photo-source.png"
    planted.unlink()
    try:
        if kind == "hard":
            os.link(protected, planted)
        else:
            planted.symlink_to(protected)
    except OSError as exc:  # symbolic links need a privilege on Windows
        pytest.skip(f"cannot create a {kind} link here: {exc}")
    replace = [*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu", "--replace"]
    assert hp.main(replace) == 0
    assert protected.read_bytes() == b"CP5 evidence, read-only"
    assert not (out / "photo-source.png").is_symlink()
    assert (out / "photo-source.png").read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"


@pytest.mark.parametrize(
    "name", ["NUL", "nul", "CON", "prn.json", "Aux.txt", "COM1", "com9.x", "LPT1", "lpt9", "NUL .x"]
)
def test_main_refuses_a_windows_device_name(tmp_path: Path, working: Path, name: str) -> None:
    # Round 1, fix 3: a device name (any case, with or without an extension) would send the
    # record to a device and report success; refused on every OS.
    source = _scene_file(tmp_path)
    argv = ["--source", str(source), "--out", str(working / "o"), "--cache-dir", str(working / "c")]
    status = hp.main([*argv, "--name", name, "--line", "30,48,90,48", "--margin", "8"])
    assert status == 2
    assert not (working / "o").exists()


def _failing_renames(
    monkeypatch: pytest.MonkeyPatch, publish: BaseException, undo: BaseException | None
) -> None:
    """Make the publish rename (staging -> out) raise ``publish``; the rollback (replaced ->
    out) raise ``undo`` when given. Every other rename runs."""
    original = Path.rename

    def rename(self: Path, target: Any) -> Any:
        if self.name.startswith(".out.staging-") and Path(target).name == "out":
            raise publish
        if (
            self.name.startswith("out.replaced-")
            and undo is not None
            and Path(target).name == "out"
        ):
            raise undo
        return original(self, target)

    monkeypatch.setattr(Path, "rename", rename)


def _published(tmp_path: Path, working: Path) -> tuple[list[str], Path, dict[str, bytes]]:
    """One successful publication in ``working/out``; the argv to replace it, and its files."""
    source = _scene_file(tmp_path)
    out = working / "out"
    argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(working / "c")]
    argv += ["--line", "30,48,90,48", "--margin", "8", "--force-cpu"]
    assert hp.main(argv) == 0
    return [*argv, "--replace"], out, _snapshot(out)


def test_main_failed_publish_and_failed_rollback_names_both_and_the_kept_folder(
    tmp_path: Path,
    working: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    # Round 2, fix 2: the publish rename fails, and so does putting the old publication back:
    # the message names both failures and the folder that now holds the old publication.
    replace, _out, before = _published(tmp_path, working)
    capsys.readouterr()
    _failing_renames(monkeypatch, OSError("publish-boom"), OSError("undo-boom"))
    assert hp.main(replace) == 1
    message = capsys.readouterr().err
    kept = [p for p in working.iterdir() if p.name.startswith("out.replaced-")]
    assert len(kept) == 1
    assert _snapshot(kept[0]) == before  # the old publication, whole, in the kept folder
    assert "publish-boom" in message
    assert "undo-boom" in message
    assert kept[0].name in message


@pytest.mark.parametrize("undo_fails", [False, True])
def test_main_interrupted_publish_rolls_back(
    tmp_path: Path,
    working: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    undo_fails: bool,
) -> None:
    # Round 2, fix 2: an interrupt during the publish rename still puts the old publication
    # back (and is re-raised); if putting it back fails too, the kept folder is named.
    replace, out, before = _published(tmp_path, working)
    capsys.readouterr()
    _failing_renames(monkeypatch, KeyboardInterrupt(), OSError("undo-boom") if undo_fails else None)
    if not undo_fails:
        with pytest.raises(KeyboardInterrupt):
            hp.main(replace)
        assert _snapshot(out) == before
        assert not [p for p in working.iterdir() if p.name.startswith("out.replaced-")]
        _assert_staging_retired(working)  # round 3, fix 3
        return
    assert hp.main(replace) == 1
    kept = [p for p in working.iterdir() if p.name.startswith("out.replaced-")]
    assert len(kept) == 1
    assert _snapshot(kept[0]) == before
    message = capsys.readouterr().err
    assert "KeyboardInterrupt" in message
    assert "undo-boom" in message
    assert kept[0].name in message


def _assert_staging_retired(working: Path) -> None:
    """No staging folder is left; exactly one ``.out.failed-*`` holds the unpublished record."""
    assert not [p for p in working.iterdir() if p.name.startswith(".out.staging-")]
    failed = [p for p in working.iterdir() if p.name.startswith(".out.failed-")]
    assert len(failed) == 1
    assert (failed[0] / "scene.json").is_file()


@pytest.mark.parametrize("after", [True, False])
def test_main_interrupt_at_the_aside_rename_rolls_back_only_what_moved(
    tmp_path: Path, working: Path, monkeypatch: pytest.MonkeyPatch, after: bool
) -> None:
    # Round 3, fix 2: an interrupt delivered at the first publication rename (out -> replaced),
    # just AFTER it took effect (``after``) or before it did. Either way ``out`` ends as it was,
    # the interrupt is re-raised, no replaced folder is left, and the staging folder is retired
    # (fix 3). The rollback must tell "renamed aside" (put it back) from "not yet renamed"
    # (move nothing: a blind rollback would fail on the absent replaced folder).
    replace, out, before = _published(tmp_path, working)
    original = Path.rename

    def rename(self: Path, target: Any) -> Any:
        if self.name == "out" and Path(target).name.startswith("out.replaced-"):
            if after:
                original(self, target)
            raise KeyboardInterrupt
        return original(self, target)

    monkeypatch.setattr(Path, "rename", rename)
    with pytest.raises(KeyboardInterrupt):
        hp.main(replace)
    monkeypatch.undo()
    assert _snapshot(out) == before
    assert not [p for p in working.iterdir() if p.name.startswith("out.replaced-")]
    _assert_staging_retired(working)


@pytest.mark.parametrize(
    "cache", ["out", "out/c", ".", "out.replaced-20261103T000000Z/c", ".out.staging-x"]
)
def test_main_refuses_a_cache_folder_in_the_publication_tree(
    tmp_path: Path, working: Path, cache: str
) -> None:
    # Round 2, fix 3: the cache equal to, inside or containing the output folder, or inside one
    # of its sibling folders (staging, failed, replaced), is refused before any write.
    source = _scene_file(tmp_path)
    out = working / "out"
    argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(working / cache)]
    status = hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"])
    assert status == 2
    assert sorted(p.name for p in working.iterdir()) == []


def test_main_refuses_an_output_inside_the_footage_folder(tmp_path: Path, working: Path) -> None:
    source = _scene_file(tmp_path)
    footage = tmp_path / "footage"
    argv = [
        "--source",
        str(source),
        "--out",
        str(footage / "out"),
        "--cache-dir",
        str(working / "c"),
    ]
    status = hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"])
    assert status == 2
    assert not (footage / "out").exists()


@pytest.mark.parametrize("name", ["../escape", "a/b", "a\\b", "C:escape", "..", "", "ABS"])
def test_main_refuses_a_name_that_is_not_a_plain_stem(
    tmp_path: Path, working: Path, name: str
) -> None:
    # Fix 4: ``--name`` becomes a path component, so it must be a plain stem.
    source = _scene_file(tmp_path)
    if name == "ABS":
        name = str(tmp_path / "absolute")
    argv = ["--source", str(source), "--out", str(working / "o"), "--cache-dir", str(working / "c")]
    status = hp.main([*argv, "--name", name, "--line", "30,48,90,48", "--margin", "8"])
    assert status == 2
    assert not list(tmp_path.rglob("*.json"))
    assert not (working / "o").exists()


def test_main_refuses_outputs_outside_the_wp57_working_folder(
    tmp_path: Path, working: Path
) -> None:
    # Fix 4: the output and the cache folders must both lie under ``<working>/wp5.7``.
    source = _scene_file(tmp_path)
    cases = [
        (tmp_path / "elsewhere", working / "c"),
        (working / "o", tmp_path / "cache-elsewhere"),
        (working / ".." / "o2", working / "c"),
        (tmp_path / "work" / "wp5.3" / "records", working / "c"),
    ]
    for out, cache in cases:
        argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(cache)]
        status = hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"])
        assert status == 2, (out, cache)
        assert not out.exists(), out
    assert not list(tmp_path.rglob("*.json"))


def test_main_fails_without_a_record_when_the_render_check_differs(
    tmp_path: Path, working: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Fix 6: a probe that drifted from the product is a failed run, not a recorded one.
    original = AncutiFusionMethod.render

    def drifted(self: AncutiFusionMethod, *args: Any, **kwargs: Any) -> Image:
        result = original(self, *args, **kwargs)
        return dataclasses.replace(result, pixels=result.pixels + np.float32(1e-3))

    monkeypatch.setattr(AncutiFusionMethod, "render", drifted)
    source = _scene_file(tmp_path)
    out = working / "o"
    argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(working / "c")]
    status = hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"])
    assert status == 1
    assert not (out / "scene.json").exists()
    assert not out.exists()  # round 1, fix 2: nothing is published


def test_main_refusals(tmp_path: Path, working: Path) -> None:
    source = _scene_file(tmp_path)
    base = ["--source", str(source), "--out", str(working / "o"), "--cache-dir", str(working / "c")]
    base.append("--force-cpu")
    assert hp.main([*base, "--line", "30,48,90"]) == 2  # three numbers
    assert hp.main([*base, "--line", "30,48,90,48", "--method", "nope"]) == 2
    assert hp.main([*base, "--line", "30,48,90,48", "--region", "0,0,20,20"]) == 2  # outside


def test_main_refuses_a_strip_that_leaves_the_region_or_the_image(
    tmp_path: Path, working: Path
) -> None:
    # Fix 5: the line's ends lie inside the region but its averaging strip (half width 4) does
    # not; and a line at the image's top row, whose strip leaves the image.
    source = _scene_file(tmp_path)
    base = ["--source", str(source), "--out", str(working / "o"), "--cache-dir", str(working / "c")]
    base.append("--force-cpu")
    assert hp.main([*base, "--line", "30,42,90,42", "--region", "20,40,80,20"]) == 2
    assert hp.main([*base, "--line", "30,2,90,2", "--margin", "8"]) == 2
    assert not list(tmp_path.rglob("*.json"))


# --- the video path (fakes for the source and the analysis) ---


def _fake_video(monkeypatch: pytest.MonkeyPatch, *, skip: set[int]) -> dict[str, Any]:
    """Replace the decoder and the analysis by fakes over five frames of :func:`_scene`."""
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    pixels = _scene()
    image = Image(pixels=pixels, device="cpu", color=SRGB, orientation_applied=True)
    statistics = hp.photo_statistics(method, image, params)
    video = SimpleNamespace(height=96, width=128, time_base=Fraction(1, 30), nb_frames=5)
    probe = SimpleNamespace(video=video, faults=(), path=Path("clip.mp4"))
    captured: dict[str, Any] = {}

    class Source:
        def probe(self, path: Path) -> SimpleNamespace:
            return probe

        def frames(self, probe: object, *, hw_decode: bool = False) -> Any:
            for pts in range(5):
                if pts not in skip:
                    yield SimpleNamespace(
                        pts_ticks=pts, pixels=pixels, color=SRGB, orientation_applied=True
                    )

    class Engine:
        def __init__(self, **kwargs: Any) -> None:
            captured.update(kwargs)
            self.store = SimpleNamespace(axis=lambda: list(range(5)))
            self.schema_hash = "h"

        def analysis_job(self) -> Any:
            return lambda progress: SimpleNamespace(ok=True, failure=None)

        def smoothed_record(self, pts: int, *, schema_hash: str) -> Any:
            return statistics

    monkeypatch.setattr(hp, "FFmpegVideoSource", Source)
    monkeypatch.setattr(hp, "AnalysisEngine", Engine)
    monkeypatch.setattr(hp, "DiskProxyCache", lambda folder: None)
    monkeypatch.setattr(hp, "cache_key", lambda path: "key")
    return {"method": method, "params": params, "captured": captured}


def _video_options(out: Path) -> dict[str, Any]:
    out.mkdir(parents=True, exist_ok=True)
    return {
        "lines": [hp.Line(30.0, 48.0, 90.0, 48.0)],
        "region": None,
        "margin": 8,
        "half_width": 1,
        "threshold": 0.1,
        "out": out,
        "start": 0.0,
        "end": 0.1,
        "crop_at": [],
        "cache_dir": out / "cache",
    }


def test_run_video_passes_the_expected_frames_and_renders_every_selected_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Fix 8: the analysis is told the clip's frame count, as the export tells it.
    fake = _fake_video(monkeypatch, skip=set())
    run = hp.run_video(
        Path("clip.mp4"),
        fake["method"],
        fake["params"],
        force_cpu=True,
        options=_video_options(tmp_path / "v"),
    )
    assert fake["captured"]["expected_frames"] == 5
    assert [frame["pts_ticks"] for frame in run["frames"]] == [0, 1, 2, 3]


def test_run_video_fails_when_the_decode_skips_a_selected_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake = _fake_video(monkeypatch, skip={2})
    with pytest.raises(hp.ProbeFailedError, match="2"):
        hp.run_video(
            Path("clip.mp4"),
            fake["method"],
            fake["params"],
            force_cpu=True,
            options=_video_options(tmp_path / "v"),
        )
