"""Tests of WP1.4b: the default method flip, the noise estimator, the grid and the runner."""

from __future__ import annotations

import dataclasses
import itertools
import json
import shutil
import struct
from fractions import Fraction
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image

import camera_state
import noise_experiments
from local_config import find_footage_file, load_local_config
from lookcheck.frames import OutputRoots
from prototype import run, temporal
from prototype.backend import select_backend
from prototype.params import Params
from prototype.pipeline import compensate_ancuti2018, correct
from prototype.temporal import Smoother

CPU = select_backend("cpu")

# --- the default flip (spec v0.5.3 D16) ----------------------------------------------------------


def test_the_default_method_is_c3() -> None:
    assert Params().method == "c3"
    assert Params.neutral().method == "c3"


def test_run_without_a_method_follows_the_params_default(tmp_path: Path) -> None:
    source = tmp_path / "scene.png"
    rng = np.random.default_rng(0)
    Image.fromarray((rng.random((32, 48, 3)) * 255).astype(np.uint8)).save(source)
    out = tmp_path / "out"
    assert run.main(["--in", str(source), "--out", str(out)]) == 0
    assert sorted(path.name for path in out.iterdir()) == ["scene-c3.png"]


def test_run_help_names_c3_as_the_default_and_lists_the_options(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit):
        run.main(["--help"])
    text = " ".join(capsys.readouterr().out.split())
    assert "compensation method (default c3; ancuti2018, or ancuti2018 with --blue)" in text
    assert "(ancuti2018-blue)" in text
    assert "defaults to the :class:`Params` default, ``c3``" in (run.__doc__ or "")


# --- the noise estimator (claim 4) ---------------------------------------------------------------


def _gradient(height: int = 512, width: int = 512) -> NDArray[np.float32]:
    """A smooth, noise-free RGB scene: a ramp across plus a slow vertical wave, in [0.3, 0.8]."""
    y, x = np.mgrid[0:height, 0:width].astype(np.float64)
    plane = 0.3 + 0.4 * x / width + 0.1 * np.sin(np.pi * y / height)
    return np.repeat(plane[..., None], 3, axis=2).astype(np.float32)


def _noisy(image: NDArray[np.float32], sigma: float, seed: int = 0) -> NDArray[np.float32]:
    noise = np.random.default_rng(seed).normal(0.0, sigma, image.shape)
    return (image + noise).astype(np.float32)


def _stripes(image: NDArray[np.float32], columns: int) -> NDArray[np.float32]:
    """Add sharp, noise-free diagonal stripes (period 6 px, height 0.3) to the first columns."""
    out = image.copy()
    width = columns * noise_experiments.TILE
    y, x = np.mgrid[0 : image.shape[0], 0:width]
    out[:, :width] += (0.3 * (((x + y) // 3) % 2)).astype(np.float32)[..., None]
    return np.clip(out, 0.0, 1.0)


@pytest.mark.parametrize("sigma", [0.002, 0.01, 0.03])
def test_the_estimator_recovers_a_known_gaussian_sigma(sigma: float) -> None:
    image = _noisy(_gradient(), sigma)
    tiles = noise_experiments.flat_tiles(image)
    assert noise_experiments.donoho_sigma(image[..., 0], tiles) == pytest.approx(sigma, rel=0.10)
    assert noise_experiments.immerkaer_sigma(image[..., 0], tiles) == pytest.approx(sigma, rel=0.10)


def test_the_estimator_is_near_zero_on_the_noise_free_gradient() -> None:
    image = _gradient()
    tiles = noise_experiments.flat_tiles(image)
    assert noise_experiments.donoho_sigma(image[..., 0], tiles) < 0.0005
    assert noise_experiments.immerkaer_sigma(image[..., 0], tiles) < 0.0005


def test_a_sharp_noise_free_edge_does_not_inflate_the_estimate() -> None:
    clean = _stripes(_gradient(), columns=5)  # 5 of 8 tile columns carry sharp edges
    tiles = noise_experiments.flat_tiles(clean)
    assert set(tiles[:, 1].tolist()) <= {5, 6, 7}  # the selection excludes every edge tile
    assert noise_experiments.donoho_sigma(clean[..., 0], tiles) < 0.0005
    noisy = _stripes(_noisy(_gradient(), 0.01), columns=5)
    tiles = noise_experiments.flat_tiles(noisy)
    assert noise_experiments.donoho_sigma(noisy[..., 0], tiles) == pytest.approx(0.01, rel=0.10)
    # Positive control: without the flat-tile selection the edges dominate the median.
    every = noise_experiments.flat_tiles(noisy, fraction=1.0)
    assert noise_experiments.donoho_sigma(noisy[..., 0], every) > 3 * 0.01


@pytest.mark.parametrize("gain", [0.5, 2.0])
def test_the_estimate_follows_a_gain(gain: float) -> None:
    image = _noisy(_gradient() * np.float32(0.5), 0.01, seed=3)  # about 0.12-0.43: x2 never clips
    tiles = noise_experiments.flat_tiles(image)
    base = noise_experiments.donoho_sigma(image[..., 0], tiles)
    scaled = (image * np.float32(gain))[..., 0]
    assert noise_experiments.donoho_sigma(scaled, tiles) == pytest.approx(gain * base, rel=0.05)
    cross = noise_experiments.immerkaer_sigma(image[..., 0], tiles)
    assert noise_experiments.immerkaer_sigma(scaled, tiles) == pytest.approx(gain * cross, rel=0.05)


def test_the_haar_detail_is_orthonormal_and_blind_to_a_plane() -> None:
    block = np.array([[[1.0, 2.0], [3.0, 5.0]]])
    assert noise_experiments.haar_hh1(block).tolist() == [[[(1.0 - 2.0 - 3.0 + 5.0) / 2.0]]]
    y, x = np.mgrid[0:8, 0:8].astype(np.float64)
    assert np.all(noise_experiments.haar_hh1((3.0 * x + 5.0 * y)[None]) == 0.0)


def test_flat_tiles_takes_a_quarter_of_the_full_tiles_flattest_first() -> None:
    image = _noisy(_gradient(520, 700), 0.01)  # 8 x 10 full tiles; the partial edge is unused
    tiles = noise_experiments.flat_tiles(image)
    assert len(tiles) == 20
    energy = noise_experiments.gradient_energy(noise_experiments.luma(image))
    assert energy.shape == (8, 10)
    chosen = energy[tiles[:, 0], tiles[:, 1]]
    assert np.all(np.diff(chosen) >= 0.0)
    assert chosen.max() <= np.sort(energy, axis=None)[19]


def _red_dark_left(columns: int) -> NDArray[np.float32]:
    """A noisy gradient whose red is below 16/255 in every tile column but the last ones."""
    image = _noisy(_gradient(), 0.01, seed=5)
    image[:, : columns * noise_experiments.TILE, 0] *= np.float32(0.05)  # red mean < 0.045
    return image


def test_red_lit_tiles_takes_the_flattest_quarter_of_the_tiles_with_a_red_baseline() -> None:
    image = _red_dark_left(columns=4)  # 8 x 8 tiles, 32 of them red-lit
    tiles, eligible = noise_experiments.red_lit_tiles(image)
    assert eligible == 32 and len(tiles) == 8
    assert set(tiles[:, 1].tolist()) <= {4, 5, 6, 7}
    energy = noise_experiments.gradient_energy(noise_experiments.luma(image))
    chosen = energy[tiles[:, 0], tiles[:, 1]]
    assert np.all(np.diff(chosen) >= 0.0)
    assert chosen.max() <= np.sort(energy[:, 4:], axis=None)[7]
    sets, record = noise_experiments.tile_sets(image)
    assert sets["red_lit"] is not None and np.array_equal(sets["red_lit"], tiles)
    assert record["red_lit"]["too_few"] is False and record["flat"]["count"] == 16


def test_a_red_lit_set_of_fewer_than_eight_tiles_is_reported_as_too_few() -> None:
    image = _red_dark_left(columns=6)  # 16 red-lit tiles: a quarter is 4
    sets, record = noise_experiments.tile_sets(image)
    assert sets["red_lit"] is None and sets["flat"] is not None
    assert record["red_lit"] == {
        "floor_8bit": 16.0,
        "count": 4,
        "chosen_from": 16,
        "too_few": True,
        "rows_cols": record["red_lit"]["rows_cols"],
    }
    source = noise_experiments.source_noise(image, sets)
    assert source["red_lit"] is None and source["flat"] is not None
    figures = noise_experiments.noise_figures(image[..., 0], sets, {"flat": None, "red_lit": None})
    assert figures == {"flat": None, "red_lit": None}


def _quantised(
    sigma_code: float, seed: int, ramp: bool = True
) -> tuple[NDArray[np.float32], float]:
    """8-bit-quantised Gaussian noise of ``sigma_code`` code values on the gradient (or a flat
    field at code 100); returns the image on [0, 1] and the true sigma of its total error."""
    clean = _gradient().astype(np.float64) * 255.0 if ramp else np.full((512, 512, 3), 100.0)
    noise = np.random.default_rng(seed).normal(0.0, sigma_code, clean.shape[:2])
    quantised = np.round(clean + noise[..., None])
    truth = float(np.std(quantised[..., 0] - clean[..., 0])) / 255.0
    return (quantised / 255.0).astype(np.float32), truth


@pytest.mark.parametrize("seed", [0, 1, 2])
def test_immerkaer_holds_where_quantisation_collapses_the_donoho_median(seed: int) -> None:
    # The regime that defeated Donoho on the deep frames: noise this weak, quantised to 8 bits,
    # leaves more than half of the HH1 coefficients exactly 0, so their median is 0.
    image, truth = _quantised(0.25, seed)
    tiles = noise_experiments.flat_tiles(image)
    red = image[..., 0]
    assert noise_experiments.hh1_zero_fraction(red, tiles) > 0.5
    assert noise_experiments.donoho_sigma(red, tiles) == 0.0
    # Immerkaer converts the mean absolute mask response with sqrt(pi / 2), exact for a
    # Gaussian response; mostly-zero quantised noise gives a heavier-tailed response, so it
    # under-reads (about 9-11 % here over 20 seeds): 15 % bounds that bias with margin.
    assert noise_experiments.immerkaer_sigma(red, tiles) == pytest.approx(truth, rel=0.15)


def test_immerkaer_keeps_the_order_of_quantised_noise_levels_that_donoho_cannot_tell_apart() -> (
    None
):
    levels = (0.2, 0.25, 0.3, 0.35, 0.5)
    immerkaer, donoho = [], []
    for sigma in levels:
        image, _ = _quantised(sigma, seed=7, ramp=False)  # flat field: the deepest regime
        tiles = noise_experiments.flat_tiles(image)
        immerkaer.append(noise_experiments.immerkaer_sigma(image[..., 0], tiles))
        donoho.append(noise_experiments.donoho_sigma(image[..., 0], tiles))
    assert all(a < b for a, b in itertools.pairwise(immerkaer))
    # Donoho only reads quantisation levels: 0, or half a code value over 0.6745.
    half_step = 0.5 / 255.0 / noise_experiments.DONOHO_CONSTANT
    assert {round(value / half_step, 6) for value in donoho} <= {0.0, 1.0}
    assert donoho[0] == donoho[1] == 0.0


# --- the settings grid and the render record (claims 3 and 5) ----------------------------------


def test_the_grid_is_the_brief_s_25_settings_each_labelled_from_its_params() -> None:
    grid = noise_experiments.settings_grid()
    assert len(grid) == 25
    assert len({setting.label for setting in grid}) == 25
    defaults = dataclasses.asdict(Params())
    varied = {"method", "red_gain_cap", "max_white_balance_gain", "blue_compensation"}
    seen = set()
    for setting in grid:
        params = setting.params
        assert setting.label == noise_experiments.setting_label(params)
        assert params.blue_compensation is False
        fixed = {k: v for k, v in dataclasses.asdict(params).items() if k not in varied}
        assert fixed == {k: v for k, v in defaults.items() if k not in varied}
        cap = params.red_gain_cap if params.method == "ancuti2018" else "n/a"
        seen.add((params.method, cap, params.max_white_balance_gain))
    clamps = (1.5, 2.0, 3.0, 5.0, 1000.0)
    expected = {("ancuti2018", c, m) for c in (None, 0.5, 1.0, 2.0) for m in clamps}
    expected |= {("c3", "n/a", m) for m in clamps}
    assert seen == expected
    assert set(noise_experiments.CROP_SETTINGS) <= {setting.label for setting in grid}
    assert set(noise_experiments.DEFAULT_SETTINGS) == {"ancuti2018 cap=2 clamp=3", "c3 clamp=3"}


def test_a_render_record_reads_the_pipeline_s_own_flags() -> None:
    image = _noisy(_gradient(256, 256), 0.01)
    image[..., 0] *= np.float32(0.05)  # red-starved: the cap and the red clamp bind
    sets, _ = noise_experiments.tile_sets(image)
    assert sets["red_lit"] is None  # no tile reaches a red mean of 16/255
    source = {
        name: None if per is None else per["R"]
        for name, per in noise_experiments.source_noise(image, sets).items()
    }
    params = Params(method="ancuti2018", red_gain_cap=0.5, max_white_balance_gain=1.5)
    result = correct(image, params, CPU)
    entry = noise_experiments.render_record(result, CPU, sets, source)
    assert entry["label"] == "ancuti2018 cap=0.5 clamp=1.5"
    assert entry["bound"]["red_gain_cap"] is (
        result.compensation.effective["red"] < result.compensation.requested["red"]
    )
    assert entry["bound"]["red_gain_cap"] is True
    assert entry["white_balance"]["clamped"] == result.white_balance.clamped
    assert entry["white_balance"]["clamped"][0] is True
    assert entry["white_balance"]["applied_gains"] == result.white_balance.applied_gains
    added = result.compensation.mean_added["red"]
    assert entry["green_fraction"] == pytest.approx(
        added / (result.compensation.channel_means[0] + added)
    )
    means = result.output.reshape(-1, 3).mean(axis=0, dtype=np.float64)
    assert entry["residual_cast"]["R/G"] == pytest.approx(means[0] / means[1])
    flat, reference = entry["noise_red"]["flat"], source["flat"]
    assert flat is not None and reference is not None
    assert entry["noise_red"]["red_lit"] is None
    flat_tiles = sets["flat"]
    assert flat_tiles is not None
    output_red = result.output[..., 0]
    assert flat["immerkaer"] == noise_experiments.immerkaer_sigma(output_red, flat_tiles)
    assert flat["donoho"] == noise_experiments.donoho_sigma(output_red, flat_tiles)
    ratio = flat["immerkaer"] / reference["immerkaer"]
    assert flat["immerkaer_amplification"] == pytest.approx(ratio)
    assert flat["immerkaer_8bit"] == pytest.approx(255.0 * flat["immerkaer"])
    c3 = noise_experiments.render_record(
        correct(image, Params(method="c3"), CPU), CPU, sets, source
    )
    assert c3["green_fraction"] is None and c3["cap"] == {"red": None, "blue": None}


# --- claim 10: the derived alpha ---------------------------------------------------------------


def _red_starved_sequence(count: int = 12) -> list[NDArray[np.float32]]:
    frames = []
    for index in range(count):
        image = _noisy(_gradient(64, 96), 0.01, seed=index)
        image[..., 0] *= np.float32(0.05 + 0.1 * (index % 4))  # the cap binds on some frames
        frames.append(np.clip(image, 0.0, 1.0))
    return frames


def test_capped_alpha_is_the_pipeline_s_effective_alpha() -> None:
    bound = 0
    for image in _red_starved_sequence(6):
        for cap in (None, 0.5, 2.0):
            params = Params(method="ancuti2018", red_gain_cap=cap)
            _, info = compensate_ancuti2018(image, params)
            derived = noise_experiments.capped_alpha(
                noise_experiments.channel_means(image),
                noise_experiments.cap_statistic(image),
                params,
            )
            assert derived == info.effective["red"]
            bound += derived < 1.0
    assert bound > 0


def test_variant_b_matches_variant_a_without_smoothing_and_shares_its_means() -> None:
    frames = _red_starved_sequence()
    params = Params(method="ancuti2018", red_gain_cap=0.5)
    rate = Fraction(30)
    identity = Smoother("gaussian", 0.0)
    a, _ = temporal.analyse_staged(frames, params, identity, rate, CPU)
    b, measured = noise_experiments.analyse_staged_derived_alpha(
        frames, params, identity, rate, CPU
    )
    assert set(a) == set(b)
    for name in a:
        np.testing.assert_array_equal(a[name], b[name], err_msg=name)
    assert np.any(a["compensation_alpha.red"] < 1.0)  # the cap does bind on this sequence
    assert "cap_statistic" in measured["compensation"]
    smoother = Smoother("gaussian", 0.2)
    a, _ = temporal.analyse_staged(frames, params, smoother, rate, CPU)
    b, _ = noise_experiments.analyse_staged_derived_alpha(frames, params, smoother, rate, CPU)
    for channel in "RGB":
        name = f"compensation_means.{channel}"
        np.testing.assert_array_equal(a[name], b[name])
    assert not np.array_equal(a["compensation_alpha.red"], b["compensation_alpha.red"])
    with pytest.raises(ValueError, match="Ancuti 2018"):
        noise_experiments.analyse_staged_derived_alpha(frames, Params(method="c3"), smoother, rate)


# --- the summary helpers ------------------------------------------------------------------------


def test_rank_correlation_and_discordant_pairs() -> None:
    assert noise_experiments.rank_correlation([1, 2, 3, 4], [10, 20, 30, 40]) == pytest.approx(1.0)
    assert noise_experiments.rank_correlation([1, 2, 3], [3, 2, 1]) == pytest.approx(-1.0)
    assert noise_experiments.rank_correlation([1, 2, 3], [5, 5, 5]) is None
    assert noise_experiments.discordant_pairs([1, 2, 3], [1, 3, 2]) == 1
    assert noise_experiments.discordant_pairs([1, 2, 3], [1, 2, 3]) == 0


def test_wanted_frames_needs_eight_deep_frames() -> None:
    entry = {"frame": "GX1_0001.000", "chapter": "GX1", "pts_ticks": 30000, "time_base": "1/30000"}
    listed = {"deepest": [entry] * 7, "cases": {"open-blue-water": {"frames": []}}}
    with pytest.raises(ValueError, match="7 deep frames"):
        noise_experiments.wanted_frames(listed)
    listed["deepest"] = [entry] * 8
    roles = [wanted.role for wanted in noise_experiments.wanted_frames(listed)]
    assert roles == ["deep"] * 8 + ["shallow"]


# --- the camera-state reader (claim 2a) ---------------------------------------------------------


def _klv(key: bytes, type_: str, size: int, payload: bytes) -> bytes:
    repeat = len(payload) // size if size else 0
    head = key + bytes([0 if type_ == "\0" else ord(type_), size]) + struct.pack(">H", repeat)
    return head + payload + b"\0" * (-len(payload) % 4)


def _nest(key: bytes, *children: bytes) -> bytes:
    body = b"".join(children)
    return key + bytes([0, 4]) + struct.pack(">H", len(body) // 4) + body


def test_the_reader_decodes_the_six_keys_and_skips_every_other_undecoded() -> None:
    first = _nest(
        b"STRM",
        _klv(b"STNM", "c", 1, b"camera"),  # unknown key, 6 bytes: padded to 8
        _klv(b"ACCL", "s", 3, b"\xff" * 9),  # IMU-named: size 3 is no int16 multiple
        _klv(b"ISOE", "S", 2, struct.pack(">3H", 100, 200, 400)),  # 6 bytes: padded
        _klv(b"SHUT", "f", 4, struct.pack(">2f", 0.5, 0.25)),
    )
    second = _nest(
        b"STRM",
        _klv(b"GPS9", "?", 5, b"\x01" * 10),  # GPS-named, complex type: skipped
        _klv(b"SCAL", "S", 2, struct.pack(">H", 10)),
        _klv(b"YAVG", "S", 2, struct.pack(">2H", 1420, 1250)),
        _klv(b"WRGB", "f", 12, struct.pack(">3f", 2.0, 1.0, 1.5)),
    )
    data = _nest(b"DEVC", first, second) + _nest(
        b"DEVC", _nest(b"STRM", _klv(b"ISOE", "S", 2, struct.pack(">H", 800)))
    )
    state = camera_state.read_camera_state(data)
    assert state == {
        "ISOE": [(100.0,), (200.0,), (400.0,), (800.0,)],
        "SHUT": [(0.5,), (0.25,)],
        "YAVG": [(142.0,), (125.0,)],
        "WRGB": [(0.2, 0.1, 0.15)],
    }
    with pytest.raises(ValueError, match="size 3"):
        camera_state.decode(next(camera_state.items(first[8:][16:])))  # ACCL, if it were decoded
    with pytest.raises(ValueError, match="runs past"):
        list(camera_state.items(data[:-4]))


def test_the_timing_rule_spreads_the_samples_over_the_stream() -> None:
    samples = [(float(k),) for k in range(30)]
    assert camera_state.nearest(samples, 1.0, 0.0) == (0.0,)
    assert camera_state.nearest(samples, 1.0, 0.5) == (15.0,)
    assert camera_state.nearest(samples, 1.0, 2.0) == (29.0,)
    state = {"ISOE": samples, "WRGB": [(2.0, 1.0, 1.5)]}
    assert camera_state.state_at(state, 1.0, 0.5) == {"ISOE": 15.0, "WRGB": [2.0, 1.0, 1.5]}
    with pytest.raises(ValueError):
        camera_state.nearest([], 1.0, 0.0)


def _work_roots(tmp_path: Path) -> OutputRoots:
    return OutputRoots(allowed=tmp_path / "wp1.4b", footage=load_local_config().footage_path)


@pytest.mark.footage
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")
def test_isoe_is_read_from_a_scuba_chapter_in_place(tmp_path: Path) -> None:
    video = find_footage_file("GX011589")
    roots = _work_roots(tmp_path)
    state, duration, index = noise_experiments.chapter_camera_state(video, roots)
    assert index == 3 and duration > 0.0
    assert (roots.allowed / "gpmd" / "GX011589.bin").is_file()
    assert set(state) == set(camera_state.CAMERA_KEYS)
    iso = [sample[0] for sample in state["ISOE"]]
    assert iso and all(50.0 <= value <= 25600.0 for value in iso)
    rate = len(iso) / duration
    assert rate == pytest.approx(30000 / 1001, rel=0.01)  # one sample per video frame


# --- the runner on real footage (claim 3) -------------------------------------------------------


@pytest.mark.footage
@pytest.mark.gpu
@pytest.mark.slow
@pytest.mark.skipif(shutil.which("ffmpeg") is None, reason="ffmpeg not on PATH")
def test_the_runner_records_one_deep_frame_under_two_settings(tmp_path: Path) -> None:
    try:
        backend = select_backend("gpu")
    except RuntimeError as exc:
        pytest.skip(f"no usable graphics card: {exc}")
    config = load_local_config()
    roots = _work_roots(tmp_path)
    wanted = noise_experiments.Wanted(
        "GX011600_0665.031", "GX011600", 19950931, Fraction(1, 30000), "deep", {"D": 0.2}
    )
    record = noise_experiments.frame_record(wanted, config, roots, {})
    assert record["frame"]["pts_ticks"] == 19950931
    assert record["frame"]["width"] == 3840 and record["frame"]["height"] == 2160
    assert "ISOE" in record["camera"]["state"]
    chosen = [
        setting
        for setting in noise_experiments.settings_grid()
        if setting.label in ("ancuti2018 cap=2 clamp=3", "c3 clamp=3")
    ]
    noise_experiments.run_frame(record, chosen, roots, backend, log=lambda _: None)
    written = json.loads((roots.allowed / "grid" / "GX011600_0665.031.json").read_text("utf-8"))
    assert [entry["label"] for entry in written["renders"]] == [s.label for s in chosen]
    for entry, setting in zip(written["renders"], chosen, strict=True):
        assert entry["params"] == dataclasses.asdict(setting.params)
        for name in ("flat", "red_lit"):
            figures, source = entry["noise_red"][name], written["source_noise"][name]
            assert figures["immerkaer_8bit"] > 0.0 and figures["donoho_8bit"] >= 0.0
            for kind in ("immerkaer", "donoho"):
                amplification = figures[f"{kind}_amplification"]
                assert (amplification is None) is (source["R"][kind] == 0.0)
    assert written["tiles"]["flat"]["count"] == round(0.25 * 60 * 33)
    lit = written["tiles"]["red_lit"]
    assert lit["count"] == round(0.25 * lit["chosen_from"]) and not lit["too_few"]
    crops = roots.allowed / "crops" / "GX011600_0665.031"
    assert (crops / "flat-source-red.png").is_file()
    assert (crops / "textured-c3_clamp-3-rgb.png").is_file()
