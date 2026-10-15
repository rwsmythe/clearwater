"""Tests of the WP1.4 temporal statistics module and the supplied-statistics hook.

The numbered tests are the brief's (``docs/briefs/wp1.4-brief.md``, Tests row); test 2 is the
existing prototype suite, unchanged; test 7 (``footage``) runs ``tools/statistics_experiments.py``
on 10 frames of ``GX011628.MP4``.
"""

from __future__ import annotations

import dataclasses
import json
import math
import shutil
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import prototype.pipeline as pipeline
import statistics_experiments as runner
from local_config import load_local_config
from lookcheck.frames import OutputPathError, OutputRoots
from prototype import temporal
from prototype.backend import CPU, Backend, select_backend
from prototype.params import Params
from prototype.pipeline import Statistics, correct
from prototype.temporal import (
    ROBUST_CANDIDATES,
    STAGES,
    Smoother,
    analyse_flat,
    analyse_staged,
    clipped_fraction,
    flatten,
    flicker,
    half_width,
    measure,
    mismatch,
    robust_bounds,
    stack,
    statistics_of,
    unflatten,
)

_AUTO = select_backend("auto")
requires_gpu = pytest.mark.skipif(
    _AUTO.name != "gpu", reason=f"no CUDA device usable: {_AUTO.reason}"
)

NTSC = Fraction(30000, 1001)

VARIANTS = {
    "ancuti2018": Params(),
    "ancuti2018-blue": Params(blue_compensation=True),
    "c3": Params(method="c3"),
}


def _scene(height: int = 96, width: int = 128, seed: int = 7) -> np.ndarray:
    """A textured blue-green scene with a weak red channel, float32 in [0, 1]."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0:height, 0:width].astype(np.float32)
    y /= height
    x /= width
    red = 0.08 + 0.10 * x + 0.05 * np.sin(9 * np.pi * x * y)
    green = 0.40 + 0.25 * y + 0.08 * np.cos(7 * np.pi * x)
    blue = 0.50 + 0.20 * x * y + 0.06 * np.sin(5 * np.pi * y)
    image = np.stack([red, green, blue], axis=2) + rng.normal(0.0, 0.02, (height, width, 3))
    return np.clip(image, 0.0, 1.0).astype(np.float32)


def _arrays(result: pipeline.Result) -> list[np.ndarray]:
    arrays = [result.output, result.fused, result.compensated, result.white_balanced]
    arrays += [result.input1, result.input2]
    for group in dataclasses.astuple(result.weights):
        arrays += list(group)
    return arrays


def _assert_bit_identical(a: pipeline.Result, b: pipeline.Result) -> None:
    for left, right in zip(_arrays(a), _arrays(b), strict=True):
        assert left.dtype == right.dtype
        assert np.array_equal(left, right)
    assert a.compensation == b.compensation
    assert a.white_balance == b.white_balance


# --- test 1: the hook is identity-preserving ------------------------------------------------------


def _identity(backend: Backend, name: str) -> None:
    params = VARIANTS[name]
    image = _scene()
    supplied = statistics_of(image, params, backend)
    _assert_bit_identical(
        correct(image, params, backend, statistics=supplied), correct(image, params, backend)
    )
    # the same through the JSON form the runner writes and reads back
    restored = unflatten(json.loads(json.dumps(flatten(supplied))))
    assert restored == supplied
    _assert_bit_identical(
        correct(image, params, backend, statistics=restored), correct(image, params, backend)
    )


@pytest.mark.parametrize("name", list(VARIANTS))
def test_1_identity_on_the_cpu(name: str) -> None:
    _identity(CPU, name)


@pytest.mark.gpu
@requires_gpu
@pytest.mark.parametrize("name", list(VARIANTS))
def test_1_identity_on_the_gpu(name: str) -> None:
    _identity(select_backend("gpu"), name)


def test_an_empty_record_is_the_unsupplied_pipeline() -> None:
    image = _scene()
    for params in VARIANTS.values():
        _assert_bit_identical(
            correct(image, params, statistics=Statistics()), correct(image, params)
        )


def _perturbed(supplied: Statistics, field: str) -> Statistics:
    values = flatten(supplied)
    changed = {
        name: value * 1.1 if name.split(".", 1)[0] == field else value
        for name, value in values.items()
    }
    return dataclasses.replace(Statistics(), **{field: getattr(unflatten(changed), field)})


@pytest.mark.parametrize(
    "field",
    [
        "compensation_means",
        "compensation_alpha",
        "white_balance_gains",
        "normalisation_bounds",
        "saliency_means",
    ],
)
def test_every_supplied_field_is_used(field: str) -> None:
    """Positive control: a supplied value that differs from the frame's own changes the output,
    and only the step it belongs to and later ones."""
    params = Params(alpha=0.8, red_gain_cap=None)
    image = _scene()
    own = correct(image, params)
    changed = correct(image, params, statistics=_perturbed(statistics_of(image, params), field))
    assert not np.array_equal(changed.output, own.output)
    if field.startswith("compensation"):
        assert not np.array_equal(changed.compensated, own.compensated)
    else:
        assert np.array_equal(changed.compensated, own.compensated)
    if field in ("normalisation_bounds", "saliency_means"):
        assert np.array_equal(changed.white_balanced, own.white_balanced)
    if field == "saliency_means":
        assert np.array_equal(changed.input2, own.input2)
        assert np.array_equal(changed.weights.laplacian[0], own.weights.laplacian[0])


def test_supplied_gains_still_meet_strength_and_clamp() -> None:
    """D99: the clamp limits the gains used for rendering, also when they are supplied."""
    params = Params(max_white_balance_gain=1.2, white_balance_strength=0.5)
    image = _scene()
    result = correct(image, params, statistics=Statistics(white_balance_gains=(3.0, 1.0, 0.5)))
    assert result.white_balance.gray_world_gains == (3.0, 1.0, 0.5)
    assert result.white_balance.requested_gains == (2.0, 1.0, 0.75)
    assert result.white_balance.applied_gains == (1.2, 1.0, 0.75)
    assert result.white_balance.clamped == (True, False, False)


def test_supplied_statistics_that_do_not_fit_the_method_are_refused() -> None:
    image = _scene()
    with pytest.raises(ValueError, match="3C"):
        correct(image, Params(method="c3"), statistics=Statistics(compensation_means=(1, 1, 1)))
    with pytest.raises(ValueError, match="compensation_alpha"):
        correct(image, Params(), statistics=Statistics(compensation_alpha={"blue": 1.0}))
    with pytest.raises(ValueError, match="compensation_alpha"):
        correct(
            image,
            Params(blue_compensation=True),
            statistics=Statistics(compensation_alpha={"red": 1.0}),
        )
    with pytest.raises(ValueError, match="saliency"):
        correct(image, Params(), statistics=Statistics(saliency_means=((50.0, 0.0, 0.0),)))


def test_measure_reports_the_supplied_values_and_measures_the_rest() -> None:
    params = Params()
    image = _scene()
    own = statistics_of(image, params)
    supplied = Statistics(white_balance_gains=(1.5, 1.0, 0.9))
    got = measure(image, params, supplied)
    assert got.compensation_means == own.compensation_means
    assert got.white_balance_gains == (1.5, 1.0, 0.9)
    balanced = correct(image, params, statistics=supplied).white_balanced
    assert got.normalisation_bounds == pipeline.normalisation_bounds(balanced, params)


# --- test 3: staged and flat on a synthetic 3-frame sequence --------------------------------------


def _uniform(rgb: tuple[float, float, float]) -> np.ndarray:
    return np.broadcast_to(np.array(rgb, dtype=np.float32), (8, 8, 3)).copy()


def _f32(value: float) -> float:
    return float(np.float32(value))


def _compensated_red(red: float, green: float, red_mean: float, green_mean: float) -> float:
    """[A18]'s red compensation of a uniform frame, alpha 1, no cap."""
    return red + (green_mean - red_mean) * (1.0 - red) * green


def _red_gain(red: float, green: float, blue: float) -> float:
    """Gray-world red gain of a uniform frame."""
    return ((red + green + blue) / 3.0) / red


def test_3_staged_and_flat_differ_as_documented() -> None:
    """Frame 1 of 3 has a lower red mean. With a 3-frame moving average (nearest edges):

    FLAT smooths the per-frame red gains, each measured on the frame compensated with its
    OWN red mean. STAGED smooths the red means first and measures each gain on the frame
    compensated with the SMOOTHED red mean. Documented direction: on every frame the staged
    red gain is HIGHER than the flat one (flat minus staged = -0.01115 here), because the
    smoothed red mean of the shifted frame is higher than its own, so it is compensated less
    and its red gain rises more than the unshifted frames' gains fall.
    """
    params = Params(red_gain_cap=None)
    red = (_f32(0.2), _f32(0.1), _f32(0.2))
    green, blue = _f32(0.6), _f32(0.5)
    frames = [_uniform((r, 0.6, 0.5)) for r in red]
    rate = Fraction(1)
    smoother = Smoother("moving_average", 2.0)  # 1 frame each side at 1 fps
    assert half_width(2.0, rate) == 1

    def window(values: list[float], index: int) -> float:
        padded = [values[0], *values, values[-1]]
        return sum(padded[index : index + 3]) / 3.0

    raw_gains = [_red_gain(_compensated_red(r, green, r, green), green, blue) for r in red]
    smoothed_red = [window(list(red), t) for t in range(3)]
    staged_gains = [
        _red_gain(_compensated_red(r, green, smoothed_red[t], green), green, blue)
        for t, r in enumerate(red)
    ]
    expected = [window(raw_gains, t) - window(staged_gains, t) for t in range(3)]

    raw = stack([statistics_of(frame, params) for frame in frames])
    flat = analyse_flat(raw, smoother, rate)
    staged, measured = analyse_staged(frames, params, smoother, rate)
    np.testing.assert_allclose(measured["compensation"]["compensation_means.R"], red, atol=1e-7)
    np.testing.assert_allclose(raw["white_balance_gains.R"], raw_gains, atol=2e-6)
    np.testing.assert_allclose(
        measured["white_balance"]["white_balance_gains.R"], staged_gains, atol=2e-6
    )
    found = flat["white_balance_gains.R"] - staged["white_balance_gains.R"]
    np.testing.assert_allclose(found, expected, atol=5e-6)
    assert all(value < -0.011 for value in found)
    assert math.isclose(expected[1], -0.01115, abs_tol=5e-5)
    # stage 1 is measured on the raw frames in both analyses: no mismatch there
    report = mismatch(flat, staged)
    assert report["compensation_means.R"]["max_abs"] == 0.0
    assert report["white_balance_gains.R"]["max_abs"] > 0.011


def test_staged_measures_each_stage_on_the_smoothed_earlier_ones() -> None:
    """A spy on measure(): stage k is called with exactly the smoothed fields of stages < k."""
    calls: list[tuple[str, ...]] = []
    original = temporal.measure

    def spy(image: Any, params: Params, supplied: Any = None, backend: Any = None) -> Statistics:
        fields = (
            () if supplied is None else tuple(sorted(n.split(".")[0] for n in flatten(supplied)))
        )
        calls.append(tuple(dict.fromkeys(fields)))
        return original(image, params, supplied, backend)

    frames = [_scene(seed=s) for s in range(4)]
    smoother = Smoother("gaussian", 2.0)
    with pytest.MonkeyPatch.context() as patch:
        patch.setattr(temporal, "measure", spy)
        smoothed, _ = analyse_staged(frames, Params(), smoother, Fraction(2))
    assert calls[:4] == [()] * 4
    assert calls[4:8] == [("compensation_alpha", "compensation_means")] * 4
    assert calls[8:] == [("compensation_alpha", "compensation_means", "white_balance_gains")] * 4
    raw = stack([statistics_of(frame, Params()) for frame in frames])
    for name in ("compensation_means.R", "compensation_alpha.red"):
        np.testing.assert_array_equal(smoothed[name], smoother.apply(raw[name], Fraction(2)))


def test_the_stage_lists() -> None:
    assert [stage.name for stage in STAGES["ancuti2018"]] == [
        "compensation",
        "white_balance",
        "fusion",
    ]
    assert [stage.name for stage in STAGES["c3"]] == ["white_balance", "fusion"]


# --- test 4: the filters are centred and their window is in seconds -------------------------------


@pytest.mark.parametrize("kind", ["moving_average", "gaussian", "median_gaussian"])
@pytest.mark.parametrize("window", [0.5, 1.0, 2.0, 4.0])
def test_4_every_filter_is_centred(kind: Any, window: float) -> None:
    smoother = Smoother(kind, window)
    count, step_at = 400, 200
    step = np.zeros(count)
    step[step_at:] = 1.0
    response = smoother.apply(step, NTSC)
    # zero phase: the response is antisymmetric about the step instant (step_at - 1/2)
    for j in range(150):
        assert math.isclose(response[step_at - 1 - j] + response[step_at + j], 1.0, abs_tol=1e-12)
    kernel = smoother.kernel(NTSC)
    np.testing.assert_allclose(kernel, kernel[::-1], rtol=0, atol=0)
    assert math.isclose(kernel.sum(), 1.0, abs_tol=1e-12)


def test_4_the_window_is_converted_from_seconds_by_the_frame_rate() -> None:
    assert half_width(1.0, NTSC) == 14  # 0.5 s * 29.97 = 14.985 frames
    assert half_width(1.0, Fraction(60)) == 30
    assert len(Smoother("moving_average", 1.0).kernel(NTSC)) == 29
    assert len(Smoother("moving_average", 1.0).kernel(Fraction(60))) == 61
    # the Gaussian falls to 1 % of its peak at half the window (here 1 s = 10 frames at 10 fps)
    kernel = Smoother("gaussian", 2.0).kernel(Fraction(10))
    assert len(kernel) == 21
    assert math.isclose(kernel[0] / kernel[10], 0.01, rel_tol=1e-12)
    # the median's window is in seconds too: 3 frames at 30 fps, 7 at 60
    assert half_width(temporal.MEDIAN_WINDOW_S, NTSC) == 1
    assert half_width(temporal.MEDIAN_WINDOW_S, Fraction(60)) == 3


def test_the_median_gaussian_removes_a_single_bad_frame() -> None:
    values = np.full(90, 0.3)
    values[45] = 5.0
    cleaned = Smoother("median_gaussian", 1.0).apply(values, NTSC)
    np.testing.assert_allclose(cleaned, 0.3, atol=1e-12)
    assert Smoother("gaussian", 1.0).apply(values, NTSC)[45] > 0.5


def test_step_response_figures() -> None:
    moving = temporal.step_response(Smoother("moving_average", 1.0), NTSC)
    # 29 equal taps: 90 % is reached 12 frames after the step's first frame
    assert math.isclose(moving["t90_s"], 12.5 / float(NTSC), rel_tol=1e-12)
    assert math.isclose(moving["t10_s"], -11.5 / float(NTSC), rel_tol=1e-12)
    assert math.isclose(moving["outlier_peak"], 1 / 29, rel_tol=1e-12)
    median = temporal.step_response(Smoother("median_gaussian", 1.0), NTSC)
    assert median["outlier_peak"] == 0.0
    assert 0.0 < moving["gain"]["2"] < moving["gain"]["0.5"] < 1.0


# --- test 5: the flicker measure ------------------------------------------------------------------


def test_5_flicker_is_zero_on_a_constant_sequence_and_positive_on_an_alternating_one() -> None:
    constant = np.full((10, 4), 0.4)
    assert flicker(constant, constant).value == 0.0
    alternating = constant + np.array([0.01, -0.01] * 5)[:, None]
    measured = flicker(alternating, constant)
    assert math.isclose(measured.value, 0.02 * 255, rel_tol=1e-9)
    assert measured.per_step.shape == (9, 4)


def test_5_content_change_cancels_to_first_order() -> None:
    """Moving content: two renders with different CONSTANT statistics (gains 3 % apart) keep
    their content change, which the measure cancels down to the second-order term (about 3 %
    of it); the brief's source-referenced form keeps the whole gain-scaled difference."""
    params = Params()
    wide = _scene(96, 256)
    frames = [np.ascontiguousarray(wide[:, s : s + 128]) for s in range(0, 128, 24)]
    reference = statistics_of(frames[0], params)
    assert reference.white_balance_gains is not None
    other = dataclasses.replace(
        reference, white_balance_gains=tuple(1.03 * g for g in reference.white_balance_gains)
    )

    def signals(statistics: Statistics) -> np.ndarray:
        return np.array(
            [temporal.frame_signals(temporal.render(f, params, statistics)) for f in frames]
        )

    first, second = signals(reference), signals(other)
    content = float(np.abs(np.diff(first, axis=0)).mean() * 255)
    assert content > 1.0  # the content does change, by more than a level per step
    assert flicker(first, first.copy()).value == 0.0
    assert flicker(second, first).value < 0.06 * content
    own = signals(None)
    assert flicker(own, first).value > 0.0


# --- test 6: robust statistics --------------------------------------------------------------------


def test_6_robust_candidates_on_a_known_array() -> None:
    values = np.arange(1001, dtype=np.float64) / 1000.0  # 0.000, 0.001, ..., 1.000
    found = {candidate.name: robust_bounds(values, candidate) for candidate in ROBUST_CANDIDATES}
    np.testing.assert_allclose(found["min/max"], (0.0, 1.0))
    np.testing.assert_allclose(found["p0.5/p99.5 (default)"], (0.005, 0.995))
    np.testing.assert_allclose(found["p1/p99"], (0.01, 0.99))
    np.testing.assert_allclose(found["p2/p98"], (0.02, 0.98))
    # trimmed: 0.010 ... 0.990 kept (981 values), mean 0.5, population sd sqrt(490 * 491 / 3) / 1000
    sd = math.sqrt(490 * 491 / 3) / 1000.0
    np.testing.assert_allclose(found["trimmed mean +- 2.5 sd"], (0.5 - 2.5 * sd, 0.5 + 2.5 * sd))
    np.testing.assert_allclose(found["trimmed mean +- 3 sd"], (0.5 - 3 * sd, 0.5 + 3 * sd))
    assert clipped_fraction(values, (0.01, 0.99)) == 20 / 1001
    # the default candidate is the pipeline's own N{} bound rule
    image = _scene()
    high_pass = temporal.white_balanced_high_pass(image, Params())
    assert robust_bounds(high_pass, ROBUST_CANDIDATES[1]) == pipeline.normalisation_bounds(
        correct(image, Params()).white_balanced, Params()
    )


def test_6_the_flat_image_case() -> None:
    """DR-14: on a flat high-pass every candidate collapses and the 1e-6 floor triggers."""
    flat = np.full((16, 16, 3), 0.25, dtype=np.float32)
    for candidate in ROBUST_CANDIDATES:
        low, high = robust_bounds(flat, candidate)
        assert math.isclose(low, 0.25, abs_tol=1e-7) and math.isclose(high, 0.25, abs_tol=1e-7)
        assert high - low < temporal.FLAT_FLOOR
    assert temporal.FLAT_FLOOR == pipeline._EPS
    # the floor makes N{} 0.5 everywhere when the supplied bounds collapse
    image = _scene()
    result = correct(
        image, Params(sharpen_strength=1.0), statistics=Statistics(normalisation_bounds=(0.1, 0.1))
    )
    np.testing.assert_allclose(
        result.input2, np.clip((result.white_balanced + 0.5) / 2, 0, 1), atol=1e-7
    )


# --- the proxy and the series helpers -------------------------------------------------------------


def test_the_proxy_is_an_exact_block_mean() -> None:
    full = np.random.default_rng(2).random((216, 384, 3), dtype=np.float32)
    proxy = temporal.proxy(full, short_side=54)
    assert proxy.shape == (54, 96, 3) and proxy.dtype == np.float32
    expected = full.astype(np.float64)[:4, :4].mean(axis=(0, 1)).astype(np.float32)
    np.testing.assert_array_equal(proxy[0, 0], expected)
    with pytest.raises(ValueError, match="whole-factor"):
        temporal.proxy(np.zeros((100, 150, 3), dtype=np.float32), short_side=30)


def test_flatten_and_unflatten_round_trip() -> None:
    for params in VARIANTS.values():
        record = statistics_of(_scene(), params)
        assert unflatten(flatten(record)) == record
    assert unflatten({}) == Statistics()
    with pytest.raises(ValueError, match="unknown"):
        unflatten({"gains.R": 1.0})
    with pytest.raises(ValueError, match="lacks"):
        unflatten({"white_balance_gains.R": 1.0})


# --- the runner ---------------------------------------------------------------------------------


def test_series_records_round_trip_with_their_pts() -> None:
    series = stack([statistics_of(_scene(seed=s), Params()) for s in range(3)])
    frames = [{"index": i, "pts_ticks": 1001 * i, "pts_seconds": i / 29.97} for i in range(3)]
    record = runner.series_record(series, frames)
    assert [entry["pts_ticks"] for entry in record] == [0, 1001, 2002]
    restored = runner.series_from_record(json.loads(json.dumps(record)))
    assert restored.keys() == series.keys()
    for name in series:
        np.testing.assert_array_equal(restored[name], series[name])


def test_the_interior_frame_steps() -> None:
    assert half_width(runner.INTERIOR_WINDOW_S, NTSC) == 59
    assert runner._interior(180, NTSC) == slice(59, 120)
    assert runner._interior(10, NTSC) is None


def test_the_runner_writes_only_inside_its_folder(tmp_path: Path) -> None:
    footage = tmp_path / "footage"
    roots = OutputRoots(allowed=tmp_path / "work" / "wp1.4", footage=footage)
    with pytest.raises(OutputPathError, match="footage"):
        runner._save_array(roots, footage / "proxies.npy", np.zeros(3))
    with pytest.raises(OutputPathError, match="outside"):
        runner._write_json(roots, tmp_path / "work" / "results.json", {})
    with pytest.raises(OutputPathError, match="outside"):
        runner._write_png(roots, tmp_path / "x.png", np.zeros((2, 2, 3), dtype=np.float32))
    assert not footage.exists()
    assert list(tmp_path.iterdir()) == []


@pytest.mark.footage
@pytest.mark.skipif(
    shutil.which("ffmpeg") is None or shutil.which("ffprobe") is None,
    reason="ffmpeg/ffprobe not on PATH",
)
def test_7_the_runner_on_ten_frames_writes_its_record(tmp_path: Path) -> None:
    config = load_local_config()
    chapter = config.footage_path / "GX011628.MP4"
    if not chapter.is_file():
        pytest.skip("GX011628.MP4 is not in the footage folder")
    roots = OutputRoots(allowed=tmp_path / "wp1.4", footage=config.footage_path)
    spec = runner.ExcerptSpec("ten", "GX011628", 0.30, 10 / float(NTSC), False, False)
    backend = select_backend("auto")
    document = runner.extract_excerpt(spec, config.footage_path, roots, backend)
    folder = roots.allowed / "ten"
    assert document["frames_count"] == 10
    assert document["tags"]["color_range"] == "pc" and document["tags"]["assumed"] == []
    assert np.load(folder / "proxies.npy").shape == (10, 540, 960, 3)
    assert len(list((folder / "frames").glob("*.png"))) == 3  # first, middle, last kept
    runner.analyse_statistics(folder, roots, backend)
    ticks = [entry["pts_ticks"] for entry in document["frames"]]
    assert ticks == sorted(ticks) and len(set(ticks)) == 10
    for kind in ("raw", "staged", "flat"):
        record = json.loads((folder / f"statistics-{kind}.json").read_text(encoding="utf-8"))
        methods = record["proxy"] if kind == "raw" else record["methods"]
        assert set(methods) == {"ancuti2018", "c3"}
        for method in methods.values():
            assert [entry["pts_ticks"] for entry in method["frames"]] == ticks
    staged = json.loads((folder / "statistics-staged.json").read_text(encoding="utf-8"))
    assert list(staged["methods"]["c3"]["measured_per_stage"]) == ["white_balance", "fusion"]
