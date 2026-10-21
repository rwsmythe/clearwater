"""Smoothing over pts (AD-3, D95, DR-23, DR-25 (7)): CFR equality with the prototype, VFR."""

from __future__ import annotations

import math
from fractions import Fraction

import numpy as np
import pytest
from numpy.typing import NDArray

from clearwater.analysis import (
    KINDS,
    STEP_AWARE_KINDS,
    exact_window,
    half_window_ticks,
    reach,
    smooth_series,
)
from prototype.temporal import Smoother

VFR_STEPS = (1001, 1001, 2002)
"""``vid-vfr``'s frame durations in ticks of a 1/30000 clock, in turn (manifest)."""


def _reference(
    times: NDArray[np.float64], values: NDArray[np.float64], window_s: float
) -> NDArray[np.float64]:
    """A direct, unvectorised ``median_gaussian`` over times, written from the definition.

    Virtual samples past each end at the end spacing hold the end value (of the input for the
    median, of the median's output for the Gaussian).
    """

    def extended(series: NDArray[np.float64], half: float) -> tuple[list[float], list[float]]:
        t, v = list(times), list(series)
        if len(t) >= 2:
            step0, step1 = t[1] - t[0], t[-1] - t[-2]
            k = 1
            while k * step0 <= half + 1e-12:
                t.insert(0, times[0] - k * step0)
                v.insert(0, series[0])
                k += 1
            k = 1
            while k * step1 <= half + 1e-12:
                t.append(times[-1] + k * step1)
                v.append(series[-1])
                k += 1
        return t, v

    t, v = extended(values, 0.05)
    median = np.array(
        [float(np.median([b for a, b in zip(t, v, strict=True) if abs(a - c) <= 0.05 + 1e-12]))
         for c in times]
    )  # fmt: skip
    t, v = extended(median, window_s / 2)
    sigma = (window_s / 2) / math.sqrt(2 * math.log(100))
    out = []
    for c in times:
        pairs = [(math.exp(-((a - c) ** 2) / (2 * sigma**2)), b) for a, b in zip(t, v, strict=True)
                 if abs(a - c) <= window_s / 2 + 1e-12]  # fmt: skip
        out.append(sum(w * b for w, b in pairs) / sum(w for w, _ in pairs))
    return np.array(out)


@pytest.mark.parametrize(
    ("rate", "time_base", "step"),
    [
        (Fraction(30000, 1001), Fraction(1, 30000), 1001),
        (Fraction(30), Fraction(1, 90000), 3000),
        (Fraction(25), Fraction(1, 1000), 40),
        (Fraction(60000, 1001), Fraction(1, 60000), 1001),
        (Fraction(240), Fraction(1, 240), 1),
    ],
)
@pytest.mark.parametrize("count", [1, 2, 5, 61, 400])
@pytest.mark.parametrize("window_s", [2.0, 0.5, 4.0, 0.01])
def test_cfr_series_equals_the_prototype_smoother(
    rate: Fraction, time_base: Fraction, step: int, count: int, window_s: float
) -> None:
    """On CFR, ``median_gaussian`` over pts is the prototype ``Smoother.apply`` within 1e-12."""
    rng = np.random.default_rng(count + step)
    values = rng.normal(size=count)
    ticks = 12345 + np.arange(count) * step
    ours = smooth_series(ticks, time_base, values, window_s, "median_gaussian")
    theirs = Smoother("median_gaussian", window_s).apply(values, rate)
    assert np.max(np.abs(ours - theirs)) <= 1e-12


def test_cfr_equality_holds_per_component_of_a_multi_dimensional_statistic() -> None:
    """A ``(2, 3)`` statistic is smoothed component by component, as the prototype's fields."""
    rng = np.random.default_rng(9)
    values = rng.normal(size=(150, 2, 3))
    ticks = np.arange(150) * 1001
    ours = smooth_series(ticks, Fraction(1, 30000), values, 2.0, "median_gaussian")
    assert ours.shape == (150, 2, 3)
    for i in range(2):
        for j in range(3):
            theirs = Smoother("median_gaussian", 2.0).apply(values[:, i, j], Fraction(30000, 1001))
            assert np.max(np.abs(ours[:, i, j] - theirs)) <= 1e-12


def _vfr_ticks(count: int) -> NDArray[np.int64]:
    steps = [VFR_STEPS[i % 3] for i in range(count - 1)]
    return np.concatenate([[0], np.cumsum(steps)]).astype(np.int64)


def test_vfr_series_is_smoothed_by_time_not_by_taps() -> None:
    """DR-23: on ``vid-vfr``'s 1001/1001/2002 durations the filter follows pts, not frame counts."""
    count = 120
    ticks = _vfr_ticks(count)
    rng = np.random.default_rng(4)
    values = np.sin(ticks / 30000.0 * 3.0) + rng.normal(0, 0.05, count)
    ours = smooth_series(ticks, Fraction(1, 30000), values, 2.0, "median_gaussian")
    reference = _reference(ticks / 30000.0, values, 2.0)
    assert np.max(np.abs(ours - reference)) <= 1e-12
    # The planted tap-count filter (a kernel from the nominal 22500/1001 rate) is not this.
    planted = Smoother("median_gaussian", 2.0).apply(values, Fraction(22500, 1001))
    assert np.max(np.abs(planted - reference)) > 1e-3


def test_vfr_median_takes_the_mean_of_two_middle_values() -> None:
    """A frame with a neighbour on one side only (a 2002-tick gap) gets the mean of two values."""
    ticks = np.array([0, 1001, 3003, 4004])
    values = np.array([0.0, 1.0, 5.0, 7.0])
    out = smooth_series(ticks, Fraction(1, 30000), values, 0.01, "median_gaussian")
    # Window 0.01 s: the Gaussian is the identity; the median over +-0.05 s remains.
    assert out.tolist() == [0.0, 0.5, 6.0, 7.0]


def test_windows_are_exact_decimals() -> None:
    """DR-25 (7): the window is ``Fraction(str(w))``; 2.0 s at 30000/1001 is exact."""
    assert exact_window(2.0) == 2
    assert exact_window(0.1) == Fraction(1, 10)
    assert half_window_ticks(2.0, Fraction(1, 30000)) == 30000
    assert half_window_ticks(2.0, Fraction(1001, 30000)) == 29
    # 0.3 s at 20 fps: half a window is exactly 3 frames; the binary float would give 2.
    assert half_window_ticks(0.3, Fraction(1, 20)) == 3
    assert math.floor(Fraction(0.3) / 2 / Fraction(1, 20)) == 2
    # A neighbour exactly at half the window is inside: 2.0 s at 1/30 includes +-30 ticks.
    ticks = np.arange(0, 61)
    values = np.zeros(61)
    values[60] = 1.0
    out = smooth_series(ticks, Fraction(1, 30), values, 2.0, "gaussian", (30, 30))
    assert out[0] > 0.0
    with pytest.raises(ValueError, match="unusable"):
        exact_window(-1.0)
    with pytest.raises(ValueError, match="unusable"):
        exact_window(float("nan"))


def test_edges_hold_the_end_value() -> None:
    """Past the ends the end value is held: a constant series stays constant to the last frame."""
    ticks = np.arange(40) * 1001
    out = smooth_series(ticks, Fraction(1, 30000), np.full(40, 0.25), 2.0, "median_gaussian")
    assert np.allclose(out, 0.25, rtol=0, atol=1e-15)


def test_one_clip_is_smoothed_without_a_reset() -> None:
    """Spec 7.2 line 325 read as single-clip: no reset inside a clip."""
    ticks = np.arange(200) * 1001
    values = np.concatenate([np.zeros(100), np.ones(100)])
    whole = smooth_series(ticks, Fraction(1, 30000), values, 2.0, "median_gaussian")
    first_half = smooth_series(
        ticks[:100], Fraction(1, 30000), values[:100], 2.0, "median_gaussian"
    )
    assert whole[99] > 0.1
    assert first_half[99] == 0.0


def test_reach_per_stage_is_thirty_frames_at_29_97() -> None:
    """Premise P1: the Gaussian's 29 frames plus the median's 1 is 30 frames per stage."""
    ticks = np.arange(301) * 1001
    assert reach(ticks, Fraction(1, 30000), 2.0, "median_gaussian", 150, 150) == (120, 180)
    assert reach(ticks, Fraction(1, 30000), 2.0, "gaussian", 150, 150) == (121, 179)
    assert reach(ticks, Fraction(1, 30000), 2.0, "median_gaussian", 120, 180) == (90, 210)
    assert reach(ticks, Fraction(1, 30000), 2.0, "median_gaussian", 0, 0) == (0, 30)
    assert reach(ticks, Fraction(1, 30000), 2.0, "median_bilateral", 150, 150) == (0, 300)
    assert Smoother("median_gaussian", 2.0).radius(Fraction(30000, 1001)) == 30


def test_partial_output_equals_the_whole_series_bit_for_bit() -> None:
    """Rows computed from their reach alone equal the whole computation exactly (the near phase)."""
    rng = np.random.default_rng(2)
    ticks = _vfr_ticks(300)
    values = rng.normal(size=(300, 3))
    whole = smooth_series(ticks, Fraction(1, 30000), values, 2.0, "median_gaussian")
    first, last = reach(ticks, Fraction(1, 30000), 2.0, "median_gaussian", 140, 160)
    masked = values.copy()
    masked[:first] = np.nan
    masked[last + 1 :] = np.nan
    part = smooth_series(ticks, Fraction(1, 30000), masked, 2.0, "median_gaussian", (140, 160))
    assert np.array_equal(part, whole[140:161])
    with pytest.raises(ValueError, match="missing"):
        smooth_series(ticks, Fraction(1, 30000), masked, 2.0, "median_gaussian", (100, 160))


def test_step_aware_kinds_keep_a_step_that_median_gaussian_spreads() -> None:
    """The design-task kinds keep a clean step sharper than the default (AD-3, question 6)."""
    rng = np.random.default_rng(6)
    ticks = np.arange(180) * 1001
    values = np.where(np.arange(180) < 90, 0.0, 1.0) + rng.normal(0, 0.01, 180)
    default = smooth_series(ticks, Fraction(1, 30000), values, 2.0, "median_gaussian")
    for kind in STEP_AWARE_KINDS:
        aware = smooth_series(ticks, Fraction(1, 30000), values, 2.0, kind)
        assert abs(aware[95] - 1.0) < 0.05 < abs(default[95] - 1.0)
        # Away from the step the noise is still smoothed.
        assert np.std(np.diff(aware[20:70])) < 0.5 * np.std(np.diff(values[20:70]))
    assert set(STEP_AWARE_KINDS) < set(KINDS)


def test_refusals() -> None:
    """Unknown kinds, unordered pts and mismatched lengths are refused by name."""
    with pytest.raises(ValueError, match="unknown smoothing kind"):
        smooth_series([0, 1], Fraction(1, 30), [0.0, 1.0], 2.0, "box")
    with pytest.raises(ValueError, match="strictly ascending"):
        smooth_series([0, 0], Fraction(1, 30), [0.0, 1.0], 2.0, "median_gaussian")
    with pytest.raises(ValueError, match="2 pts but 3 values"):
        smooth_series([0, 1], Fraction(1, 30), [0.0, 1.0, 2.0], 2.0, "median_gaussian")
    with pytest.raises(ValueError, match="time base"):
        half_window_ticks(2.0, Fraction(0))
