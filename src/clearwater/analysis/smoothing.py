"""Temporal smoothing of per-frame statistics over pts (AD-3, D95, DR-23, DR-25 (7)).

Every window is a time window over the frames' exact presentation times, never a tap count
from a nominal frame rate. Times are integer ticks of one time base; a sample is inside a
half-window ``h`` of another when ``|ticks difference| * time_base <= h`` exactly.

``median_gaussian`` (the default, PROVISIONAL, AD-3): a centred running median over the
samples within ``MEDIAN_WINDOW_S / 2`` of each frame, then a centred Gaussian over the samples
within ``window_s / 2``, its weight ``exp(-dt^2 / (2 s^2))`` falling to ``GAUSSIAN_FALLOFF`` at
half the window, normalised per output. Past each end of the series, virtual samples at the end
frame's own spacing hold the end value (of the input for the median, of the median's output
for the Gaussian), which on a constant-rate series is SciPy's ``mode="nearest"``: the result
equals ``tools.prototype.temporal.Smoother("median_gaussian", w).apply`` there. A median over
an even number of samples (a variable-rate gap on one side) is the mean of the two middle ones.

The step-aware candidates of the design task (AD-3, WP3.11 question 6) are extra kinds; the
default does not change here (a change of default is spec 7.2, owner-reserved).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from fractions import Fraction
from typing import Any

import numpy as np
from numpy.typing import NDArray

DEFAULT_KIND = "median_gaussian"
"""The default smoothing kind (spec 7.2, AD-3; PROVISIONAL, DR-25 (3))."""

DEFAULT_WINDOW_S = 2.0
"""The default full window in seconds (spec 7.2, AD-3; PROVISIONAL)."""

MEDIAN_WINDOW_S = Fraction(1, 10)
"""The running median's full window: 0.1 s, 3 frames at 30 fps (the prototype's value)."""

GAUSSIAN_FALLOFF = 0.01
"""The Gaussian's weight at half the window, relative to its peak (1 %)."""

STEP_HALF_S = Fraction(1, 2)
"""Step-aware kinds: the span of the before and after means a step is detected with (s)."""

STEP_THRESHOLD = 6.0
"""Step-aware ``median_gaussian_cut``: a step is a before/after difference above this many
robust noise units (fixed before the evaluation run)."""

BILATERAL_SCALE = 3.0
"""Step-aware ``median_bilateral``: the range kernel's width in robust noise units (fixed
before the evaluation run)."""

STEP_AWARE_KINDS = ("median_gaussian_cut", "median_bilateral")
"""The step-aware candidate kinds (design task, AD-3); not the default."""

KINDS = (DEFAULT_KIND, "gaussian", *STEP_AWARE_KINDS)
"""Every smoothing kind this module implements."""

_LOCAL_KINDS = (DEFAULT_KIND, "gaussian")
"""Kinds whose output at a frame reads only the samples within its windows."""

_CHUNK_ELEMENTS = 1 << 22
"""The largest ``frames x samples x components`` block one median pass holds at once."""


def exact_window(window_s: float | Fraction | str) -> Fraction:
    """Return a window as an exact decimal fraction: ``Fraction(str(window_s))`` (DR-25 (7)).

    Args:
        window_s: The window in seconds; a float is read as the decimal it prints as.

    Returns:
        The window as an exact fraction (2.0 -> 2, 0.1 -> 1/10).

    Raises:
        ValueError: The window is negative, not finite or not a number.
    """
    if isinstance(window_s, Fraction):
        value = window_s
    else:
        if isinstance(window_s, float) and not math.isfinite(window_s):
            raise ValueError(f"unusable smoothing window {window_s!r} s")
        try:
            value = Fraction(str(window_s))
        except (ValueError, ZeroDivisionError) as exc:
            raise ValueError(f"unusable smoothing window {window_s!r} s") from exc
    if value < 0:
        raise ValueError(f"unusable smoothing window {window_s!r} s")
    return value


def half_window_ticks(window_s: float | Fraction | str, time_base: Fraction) -> int:
    """Return the largest tick distance inside half a window: ``floor(window / 2 / time_base)``.

    Args:
        window_s: The full window in seconds.
        time_base: Seconds per tick.

    Returns:
        The half-window in whole ticks.

    Raises:
        ValueError: The window is unusable or the time base is not positive.
    """
    if time_base <= 0:
        raise ValueError(f"the time base must be positive, got {time_base}")
    return math.floor(exact_window(window_s) / 2 / time_base)


def _check_kind(kind: str) -> None:
    """Refuse an unknown kind."""
    if kind not in KINDS:
        raise ValueError(f"unknown smoothing kind {kind!r}; known: {', '.join(KINDS)}")


def _span(ticks: NDArray[np.int64], lo: int, hi: int, half: int) -> tuple[int, int]:
    """Return the index interval of the samples within ``half`` ticks of ``ticks[lo..hi]``."""
    first = int(np.searchsorted(ticks, ticks[lo] - half, side="left"))
    last = int(np.searchsorted(ticks, ticks[hi] + half, side="right")) - 1
    return first, last


def reach(
    ticks: Sequence[int] | NDArray[np.int64],
    time_base: Fraction,
    window_s: float | Fraction | str,
    kind: str,
    lo: int,
    hi: int,
) -> tuple[int, int]:
    """Return the index interval of every input sample the outputs ``lo..hi`` read.

    The Gaussian's half-window around the outputs, then the median's half-window around that
    (for ``median_gaussian``), over the actual pts; the virtual end samples hold the end
    frame's value, which is inside the interval whenever they are reached. A step-aware kind
    reads the whole series (its noise scale is the series').

    Args:
        ticks: The series' pts ticks, strictly ascending.
        time_base: Seconds per tick.
        window_s: The full window in seconds.
        kind: The smoothing kind.
        lo: The first output index.
        hi: The last output index.

    Returns:
        ``(first, last)`` input indices, inclusive.

    Raises:
        ValueError: An unknown kind, an unusable window, or an empty or out-of-range interval.
    """
    _check_kind(kind)
    pts = np.asarray(ticks, dtype=np.int64)
    if not 0 <= lo <= hi < len(pts):
        raise ValueError(f"output interval {lo}..{hi} outside 0..{len(pts) - 1}")
    if kind not in _LOCAL_KINDS:
        return 0, len(pts) - 1
    first, last = _span(pts, lo, hi, half_window_ticks(window_s, time_base))
    if kind == DEFAULT_KIND:
        first, last = _span(pts, first, last, half_window_ticks(MEDIAN_WINDOW_S, time_base))
    return first, last


def _extend(
    ticks: NDArray[np.int64], half: int, at_start: bool, at_end: bool
) -> tuple[NDArray[np.int64], int, int]:
    """Add the virtual end samples: the end frame's spacing, as far as ``half`` reaches.

    Returns:
        The extended ticks, the number of virtual samples before and after.
    """
    if len(ticks) < 2 or half <= 0:
        return ticks, 0, 0
    first_step = int(ticks[1] - ticks[0])
    last_step = int(ticks[-1] - ticks[-2])
    before = half // first_step if at_start else 0
    after = half // last_step if at_end else 0
    head = ticks[0] - np.arange(before, 0, -1, dtype=np.int64) * first_step
    tail = ticks[-1] + np.arange(1, after + 1, dtype=np.int64) * last_step
    return np.concatenate([head, ticks, tail]), before, after


def _hold(values: NDArray[np.float64], before: int, after: int) -> NDArray[np.float64]:
    """Pad ``values`` (rows) with copies of the first and last row."""
    return np.concatenate(
        [np.repeat(values[:1], before, axis=0), values, np.repeat(values[-1:], after, axis=0)]
    )


def _median(
    ticks: NDArray[np.int64], values: NDArray[np.float64], half: int, at_start: bool, at_end: bool
) -> NDArray[np.float64]:
    """The running median over the samples within ``half`` ticks (virtual ends held)."""
    n = len(ticks)
    ext_ticks, before, after = _extend(ticks, half, at_start, at_end)
    ext = _hold(values, before, after)
    centre = np.arange(before, before + n)
    lo = np.searchsorted(ext_ticks, ext_ticks[centre] - half, side="left")
    hi = np.searchsorted(ext_ticks, ext_ticks[centre] + half, side="right") - 1
    width = int(np.max(hi - lo)) + 1 if n else 1
    if width == 1:
        return values.copy()
    out = np.empty_like(values)
    components = values.shape[1]
    chunk = max(1, _CHUNK_ELEMENTS // (width * max(1, components)))
    for start in range(0, n, chunk):
        rows = slice(start, min(n, start + chunk))
        index = lo[rows, None] + np.arange(width)[None, :]
        inside = index <= hi[rows, None]
        gathered = ext[np.minimum(index, len(ext) - 1)]
        gathered = np.where(inside[:, :, None], gathered, np.nan)
        out[rows] = np.nanmedian(gathered, axis=1)
    return out


def _noise(series: NDArray[np.float64]) -> NDArray[np.float64]:
    """Robust frame-to-frame noise per component: 1.4826 x the MAD of the differences."""
    if len(series) < 3:
        return np.zeros(series.shape[1])
    steps = np.diff(series, axis=0)
    mad = np.median(np.abs(steps - np.median(steps, axis=0)), axis=0)
    return np.asarray(1.4826 * mad, dtype=np.float64)


def _segments(
    ticks: NDArray[np.int64], series: NDArray[np.float64], time_base: Fraction
) -> NDArray[np.int64]:
    """Segment ids per sample and component: a new segment starts after each detected step.

    A step lies between samples ``i`` and ``i + 1`` when the difference of the means over
    ``STEP_HALF_S`` after and before the boundary is a local maximum of its size and exceeds
    ``STEP_THRESHOLD`` robust noise units.
    """
    n, components = series.shape
    ids = np.zeros((n, components), dtype=np.int64)
    if n < 3:
        return ids
    half = half_window_ticks(2 * STEP_HALF_S, time_base)
    cumulative = np.concatenate([np.zeros((1, components)), np.cumsum(series, axis=0)])
    boundary = np.arange(n - 1)  # between sample b and b + 1
    lo = np.searchsorted(ticks, ticks[boundary] - half, side="left")
    hi = np.searchsorted(ticks, ticks[boundary + 1] + half, side="right")
    before = (cumulative[boundary + 1] - cumulative[lo]) / (boundary + 1 - lo)[:, None]
    after = (cumulative[hi] - cumulative[boundary + 1]) / (hi - boundary - 1)[:, None]
    jump = np.abs(after - before)
    scale = np.maximum(_noise(series), 1e-12)
    padded = np.concatenate([np.zeros((1, components)), jump, np.zeros((1, components))])
    peak = (jump >= padded[:-2]) & (jump >= padded[2:])
    steps = peak & (jump > STEP_THRESHOLD * scale)
    ids[1:] = np.cumsum(steps, axis=0)
    return ids


def smooth_series(
    ticks: Sequence[int] | NDArray[np.int64],
    time_base: Fraction,
    values: NDArray[Any],
    window_s: float | Fraction | str,
    kind: str,
    out: tuple[int, int] | None = None,
) -> NDArray[np.float64]:
    """Smooth a per-frame series over pts.

    Args:
        ticks: The frames' pts ticks, strictly ascending.
        time_base: Seconds per tick.
        values: ``(frames,)`` or ``(frames, components)``; each component is smoothed on its
            own. Rows outside the reach of ``out`` are not read (they may be NaN).
        window_s: The full window in seconds.
        kind: The smoothing kind (:data:`KINDS`).
        out: ``(lo, hi)``, the output rows wanted (inclusive); None for every row.

    Returns:
        float64 rows ``lo..hi`` of the smoothed series, components as in ``values``.

    Raises:
        ValueError: An unknown kind, an unusable window or time base, ticks not strictly
            ascending, mismatched lengths, or a NaN inside the reach of ``out``.
    """
    _check_kind(kind)
    pts = np.asarray(ticks, dtype=np.int64)
    data = np.asarray(values, dtype=np.float64)
    flat = data.reshape(len(data), -1) if data.ndim != 1 else data[:, None]
    n = len(pts)
    if len(flat) != n:
        raise ValueError(f"{n} pts but {len(flat)} values")
    if n == 0:
        return flat.reshape(data.shape).copy()
    if np.any(np.diff(pts) <= 0):
        raise ValueError("the pts must be strictly ascending")
    lo, hi = (0, n - 1) if out is None else out
    first, last = reach(pts, time_base, window_s, kind, lo, hi)
    part_ticks = pts[first : last + 1]
    part = flat[first : last + 1]
    if np.isnan(part).any():
        raise ValueError("a value inside the smoothing reach is missing (NaN)")
    at_start, at_end = first == 0, last == n - 1
    result = _smooth(part_ticks, part, time_base, window_s, kind, at_start, at_end)
    rows = result[lo - first : hi - first + 1]
    shape = (hi - lo + 1, *data.shape[1:])
    return rows.reshape(shape)


def _smooth(
    ticks: NDArray[np.int64],
    values: NDArray[np.float64],
    time_base: Fraction,
    window_s: float | Fraction | str,
    kind: str,
    at_start: bool,
    at_end: bool,
) -> NDArray[np.float64]:
    """Smooth every row of a contiguous part of the series (see :func:`smooth_series`)."""
    series = values
    if kind != "gaussian":
        half_m = half_window_ticks(MEDIAN_WINDOW_S, time_base)
        series = _median(ticks, values, half_m, at_start, at_end)
    window = exact_window(window_s)
    half = half_window_ticks(window, time_base)
    n = len(ticks)
    if half == 0 or n == 1:
        return series.copy()
    sigma_s = float(window) / 2.0 / math.sqrt(2.0 * math.log(1.0 / GAUSSIAN_FALLOFF))
    seconds_per_tick = float(time_base)
    ext_ticks, before, after = _extend(ticks, half, at_start, at_end)
    ext = _hold(series, before, after)
    centre = np.arange(before, before + n)
    segment: NDArray[np.int64] | None = None
    range_scale: NDArray[np.float64] | None = None
    if kind == "median_gaussian_cut":
        ids = _segments(ticks, series, time_base).astype(np.float64)
        segment = _hold(ids, before, after).astype(np.int64)
    elif kind == "median_bilateral":
        range_scale = np.maximum(BILATERAL_SCALE * _noise(series), 1e-12)
    total = np.ones_like(series)
    acc = series.copy()
    offset = 1
    while True:
        moved = False
        for sign in (1, -1):
            index = centre + sign * offset
            valid = (index >= 0) & (index < len(ext_ticks))
            if not valid.any():
                continue
            safe = np.clip(index, 0, len(ext_ticks) - 1)
            gap = np.abs(ext_ticks[safe] - ext_ticks[centre])
            valid &= gap <= half
            if not valid.any():
                continue
            moved = True
            dt = gap.astype(np.float64) * seconds_per_tick
            weight = np.where(valid, np.exp(-(dt**2) / (2.0 * sigma_s**2)), 0.0)[:, None]
            neighbour = ext[safe]
            if segment is not None:
                weight = weight * (segment[safe] == segment[centre])
            if range_scale is not None:
                weight = weight * np.exp(-((neighbour - series) ** 2) / (2.0 * range_scale**2))
            weight = np.broadcast_to(weight, series.shape)
            acc += weight * neighbour
            total += weight
        if not moved:
            break
        offset += 1
    smoothed: NDArray[np.float64] = acc / total
    return smoothed
