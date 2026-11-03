"""Unit tests of the WP5.7 halo probe (``tools/halo_probe.py``) on synthetic edges.

Parallel leg: CPU only, no footage. Each band test has a twin that must NOT see a band (or must
see one), so a probe that measured nothing, or always measured something, fails here.
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest
from scipy import ndimage

import halo_probe as hp
from clearwater.interfaces import ColorDescription, Image
from clearwater.io.photo.png import write_png
from clearwater.methods import AncutiFusionMethod

SRGB = ColorDescription("bt709", "srgb", "identity", "full", 8, False, None)


def _step(n: int = 241, *, bright: float = 0.6, dark: float = 0.2) -> np.ndarray:
    """A 1-D step: bright water for the first half, a dark object after (edge between samples)."""
    out = np.full(n, dark)
    out[: n // 2] = bright
    return out


def _unsharp(profile: np.ndarray, sigma: float, amount: float = 1.0) -> np.ndarray:
    """Unsharp mask ``I + amount * (I - G*I)`` of a 1-D profile (the classic halo maker)."""
    return profile + amount * (profile - ndimage.gaussian_filter1d(profile, sigma, mode="nearest"))


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


# --- the step edge ---


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


def test_water_band_is_zero_against_itself_and_signed_by_direction() -> None:
    clean = _step(401)
    fits = hp.profile_fits(clean)
    same = hp.water_band(clean, clean, fits)
    assert same["band_ratio"] == 0.0
    assert not same["exceeds"]
    halo = hp.water_band(_unsharp(clean, 8.0), clean, fits)
    assert halo["exceeds"]
    assert halo["direction"] == "outward"  # a bright ring in the water beside a dark object
    assert halo["band"] > 0.3
    # A glow: the object's level spreads into the water (inward), as a too-coarse blend would.
    index = np.arange(clean.size)
    glow = clean - 0.15 * np.exp(-(((index - fits.edge) / 25.0) ** 2)) * (index <= fits.edge)
    inward = hp.water_band(glow, clean, fits)
    assert inward["direction"] == "inward"
    assert inward["band"] == pytest.approx(-0.15 / 0.4, rel=0.1)
    assert inward["fwhm_px"] == pytest.approx(2 * 25.0 * math.sqrt(math.log(2)) / 2, abs=3)


def test_water_band_bright_object_on_dark_water() -> None:
    clean = _step(401, bright=0.2, dark=0.7)  # start side (water) dark, object bright
    fits = hp.profile_fits(clean)
    halo = hp.water_band(_unsharp(clean, 8.0), clean, fits)
    assert halo["contrast"] < 0
    assert halo["direction"] == "outward"  # the dark ring beside a bright object
    assert halo["exceeds"]


# --- a disc on a gradient ---


def _disc_on_gradient(size: int = 400, radius: float = 70.0) -> np.ndarray:
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float64)
    background = 0.35 + 0.0012 * xx  # a strong left-to-right gradient of the water
    disc = np.hypot(xx - size / 2, yy - size / 2) <= radius
    return np.where(disc, background - 0.2, background)


def test_disc_on_gradient_clean_has_no_band_and_unsharp_has_one() -> None:
    plane = _disc_on_gradient()
    line = hp.Line(20.0, 200.0, 190.0, 200.0)  # from the water on the left into the disc
    clean = hp.line_profile(plane, line, half_width=2)
    stats = hp.band_statistics(clean)
    assert stats["band_ratio"] < 0.02  # the linear plateau fit absorbs the gradient
    halo_plane = plane + (plane - ndimage.gaussian_filter(plane, 6.0, mode="nearest"))
    halo = hp.line_profile(halo_plane, line, half_width=2)
    fits = hp.profile_fits(clean)
    water = hp.water_band(halo, clean, fits)
    assert water["exceeds"]
    assert water["direction"] == "outward"
    assert hp.band_statistics(halo)["band_ratio"] > 0.3


def test_a_constant_plateau_would_misread_the_gradient() -> None:
    # The reason for the linear fit: a median plateau reads the gradient as a band.
    clean = hp.line_profile(_disc_on_gradient(), hp.Line(20.0, 200.0, 190.0, 200.0))
    fits = hp.profile_fits(clean)
    water = clean[: fits.edge]
    naive_overshoot = (water.max() - np.median(water[: fits.outer])) / 0.2
    assert naive_overshoot > 0.1
    assert hp.band_statistics(clean)["band_ratio"] < 0.02


# --- the staged render follows the product -------------------------------------------------------


def _scene(height: int = 96, width: int = 128) -> np.ndarray:
    yy, xx = np.mgrid[0:height, 0:width].astype(np.float32)
    rgb = np.stack([0.15 + 0.001 * xx, 0.45 + 0.0008 * yy, 0.55 + 0.0005 * xx], axis=2)
    disc = np.hypot(xx - 80, yy - 48) <= 22
    rgb[disc] = [0.35, 0.3, 0.25]
    noise = np.random.default_rng(7).normal(0, 0.01, rgb.shape).astype(np.float32)
    return np.ascontiguousarray((rgb + noise).clip(0, 1), dtype=np.float32)


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
    record = frame["lines"][0]
    # The input-and-level terms add up to the fused deviation at the peak.
    assert record["attribution_sum"] == pytest.approx(record["fused_deviation_at_peak"], abs=1e-4)
    assert (tmp_path / "photo-input2.png").read_bytes()[24] == 16  # IHDR bit depth
    assert (tmp_path / "photo-output-marked.png").exists()


def test_stretched_stage_matches_the_input2_formula() -> None:
    method = AncutiFusionMethod("c3")
    params = hp.resolve_parameters(method, [])
    image = Image(pixels=_scene(), device="cpu", color=SRGB, orientation_applied=True)
    statistics = hp.photo_statistics(method, image, params)
    stages = dict(hp.staged_render(method, image, params, statistics))
    # At sharpen_strength 1, input2 = clip((I + N) / 2) with N the stretched high-pass.
    expected = ((stages["balanced"] + stages["stretched"]) / 2).clip(0, 1)
    np.testing.assert_allclose(stages["input2"], expected, atol=1e-6)


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


def test_main_on_a_synthetic_photo(tmp_path: Path) -> None:
    source = tmp_path / "scene.png"
    write_png(source, _scene(), bit_depth=16, icc=None, exif=None, provenance_json=None)
    out = tmp_path / "out"
    argv = ["--source", str(source), "--out", str(out), "--cache-dir", str(tmp_path / "c")]
    status = hp.main([*argv, "--line", "30,48,90,48", "--margin", "8", "--force-cpu"])
    assert status == 0
    record = json.loads((out / "scene.json").read_text(encoding="utf-8"))
    assert record["kind"] == "photo"
    assert record["method"] == "c3"
    frame = record["frames"][0]
    assert frame["render_check_equal"] is True
    assert set(frame["lines"][0]["water"]) == set(hp.IMAGE_STAGES)
    assert "fwhm_sigma" in frame["lines"][0]["water"]["fused"]["Y"]
    assert (out / "overview-output.png").exists()
    # A second run refuses to overwrite the record unless asked.
    assert hp.main([*argv, "--line", "30,48,90,48", "--force-cpu"]) == 2
    assert hp.main([*argv, "--line", "30,48,90,48", "--force-cpu", "--replace"]) == 0


def test_main_refuses_an_output_inside_the_footage_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    footage = tmp_path / "footage"
    footage.mkdir()
    source = tmp_path / "scene.png"
    write_png(source, _scene(), bit_depth=16, icc=None, exif=None, provenance_json=None)
    monkeypatch.setattr(hp.headless_export, "configured_footage_folder", lambda: footage)
    argv = ["--source", str(source), "--out", str(footage / "out"), "--cache-dir", str(tmp_path)]
    status = hp.main([*argv, "--line", "30,48,90,48", "--force-cpu"])
    assert status == 2
    assert not (footage / "out").exists()


def test_main_refusals(tmp_path: Path) -> None:
    source = tmp_path / "scene.png"
    write_png(source, _scene(), bit_depth=16, icc=None, exif=None, provenance_json=None)
    base = ["--source", str(source), "--out", str(tmp_path / "o"), "--cache-dir", str(tmp_path)]
    base.append("--force-cpu")
    assert hp.main([*base, "--line", "30,48,90"]) == 2  # three numbers
    assert hp.main([*base, "--line", "30,48,90,48", "--method", "nope"]) == 2
    assert hp.main([*base, "--line", "30,48,90,48", "--region", "0,0,20,20"]) == 2  # outside
