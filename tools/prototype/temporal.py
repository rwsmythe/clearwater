"""Whole-frame statistics over time: extraction, staged and flat analysis, smoothing (WP1.4).

The prototype's first draft of the analyse/render split of IF-3 (plan section 8; spec 7.1,
7.2, D95, D97, D98), used by ``tools/statistics_experiments.py`` on real footage:

- :func:`measure` runs the pipeline's chain up to the fusion inputs on one image, with any
  statistics supplied (:class:`prototype.pipeline.Statistics`) in place of its own, and
  returns every whole-frame statistic it used or measured; :func:`statistics_of` is the
  unsupplied case, the frame's own statistics, which make
  ``correct(image, params, statistics=statistics_of(image, params))`` equal ``correct(image,
  params)`` bit for bit.
- :data:`STAGES` lists each method's ordered stages (spec 7.1: Ancuti 2018 starts with the
  compensation, 3C with the white balance).
- :func:`analyse_staged` measures each stage on the frames corrected with the SMOOTHED
  results of the stages before it, then smooths it (D97); :func:`analyse_flat` smooths the
  raw per-frame statistics, each independently (the single-stage method of D98).
- :class:`Smoother` is a centred (zero-phase) temporal filter whose window is given in
  seconds and converted with the clip's frame rate (D95).
- :func:`flicker` is the package's flicker measure (an instrument of WP1.4, NOT the V3 test
  of D112, which is measured on a synthetic clip later).
- :data:`ROBUST_CANDIDATES` and :func:`robust_bounds` are the candidate statistics for the
  N{} bounds (spec 14.1, DR-14).

A series of statistics is a mapping from a scalar's name (:func:`flatten`, for example
``white_balance_gains.R``) to a float64 array with one value per frame. Statistics are
measured on proxies (spec 7.3; :func:`proxy`).
"""

from __future__ import annotations

import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from fractions import Fraction
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray
from scipy import ndimage

from .backend import Backend, of
from .params import Params
from .pipeline import (
    RGB_TO_YCBCR,
    Image,
    Statistics,
    check_derived_values,
    check_statistics,
    compensate_ancuti2018,
    compensate_c3,
    correct,
    fusion_inputs,
    high_pass_of,
    normalisation_bounds,
    saliency_reference,
    white_balance,
)

Series = dict[str, NDArray[np.float64]]
"""Per-frame statistics of a clip: scalar name -> one float64 value per frame."""

PROXY_SHORT_SIDE = 540
"""Short side of the analysis proxy in pixels (WP1.4 brief, decision fixed at issue)."""

GAUSSIAN_FALLOFF = 0.01
"""The Gaussian kernel falls to this fraction of its peak at the ends of its window."""

MEDIAN_WINDOW_S = 0.1
"""Window of the median that precedes the Gaussian in ``median_gaussian`` (3 frames at 30 fps)."""

EDGE_MODE = "nearest"
"""How the filters extend a series past its ends: the end value is held (``a a | a b c``)."""

FLAT_FLOOR = 1e-6
"""N{} counts as collapsed (the flat-image rule) below this spread; ``pipeline._EPS``."""

TRIM_PERCENT = 1.0
"""The trimmed standard deviation drops the values below this percentile and above 100 minus it."""

MIN_FRAMES = 2
"""The fewest frames a sequence analysis accepts: the flicker measure needs one frame step."""

ALPHA_CHANNELS = ("red", "blue")
"""The channels Ancuti 2018 can compensate, in the order their alphas are flattened."""

_RGB = ("R", "G", "B")
_LAB = ("L", "a", "b")
_LUMA = RGB_TO_YCBCR[0]
SIGNALS = ("R", "G", "B", "luma")
"""The per-frame signals of the flicker measure: the frame's channel means and luma mean."""

FilterKind = Literal["moving_average", "gaussian", "median_gaussian"]
_FILTER_KINDS: tuple[FilterKind, ...] = ("moving_average", "gaussian", "median_gaussian")


@dataclass(frozen=True)
class Stage:
    """One analysis stage of a method: its name and the :class:`Statistics` fields it measures.

    Attributes:
        name: ``"compensation"``, ``"white_balance"`` or ``"fusion"``.
        fields: The :class:`prototype.pipeline.Statistics` fields of the stage.
    """

    name: str
    fields: tuple[str, ...]


_COMPENSATION = Stage("compensation", ("compensation_means", "compensation_alpha"))
_WHITE_BALANCE = Stage("white_balance", ("white_balance_means", "white_balance_gains"))
_FUSION = Stage("fusion", ("normalisation_bounds", "saliency_means"))

STAGES: dict[str, tuple[Stage, ...]] = {
    "ancuti2018": (_COMPENSATION, _WHITE_BALANCE, _FUSION),
    "c3": (_WHITE_BALANCE, _FUSION),
}
"""Each method's ordered stages (spec 7.1). 3C compensates with local means only, so its chain
starts at the white balance. The fusion stage holds the N{} bounds, measured on the
white-balanced image, and the saliency reference of each fusion input, measured on the
inputs built from that image with the frame's own N{} bounds (in-stage)."""


# --- measuring ------------------------------------------------------------------------------------


def measure(
    image: Image,
    params: Params,
    supplied: Statistics | None = None,
    backend: Backend | None = None,
) -> Statistics:
    """Run the chain up to the fusion inputs and return every whole-frame statistic it used.

    The steps are the pipeline's own (:func:`prototype.pipeline.compensate_ancuti2018` or
    :func:`~prototype.pipeline.compensate_c3`, :func:`~prototype.pipeline.white_balance`,
    :func:`~prototype.pipeline.fusion_inputs`), with ``supplied`` passed to each, so a
    supplied value is used and every other one is measured on the image as it stands at
    that step. The returned record holds, per field, the supplied value or the measurement:
    the compensation means and effective alpha (Ancuti 2018; ``None`` for 3C), the channel
    means of the compensated image that the white balance measures and the gray-world gains
    derived from them, the N{} bounds of the white-balanced image, and the mean Lab vector of
    each fusion input (input 2 built with the bounds in the record).

    Args:
        image: The display-encoded RGB image, float32 in [0, 1], shape ``(H, W, 3)``.
        params: The parameter set.
        supplied: Statistics to use instead of measuring them; ``None`` measures all.
        backend: Where the steps run; ``None`` runs them where the image is.

    Returns:
        The statistics, every field filled except the compensation fields under 3C.

    Raises:
        ValueError: The image or a derived value is unusable, or ``supplied`` does not fit
            the method or holds a non-finite number (as :func:`prototype.pipeline.correct`).
    """
    given = Statistics() if supplied is None else supplied
    check_statistics(given)
    check_derived_values(image.shape, params)
    device = of(image) if backend is None else backend
    work = device.to_device(image)
    means: tuple[float, float, float] | None = None
    alpha: dict[str, float] | None = None
    if params.method == "c3":
        if (given.compensation_means, given.compensation_alpha) != (None, None):
            raise ValueError("3C uses no whole-frame compensation statistics")
        compensated, _ = compensate_c3(work, params)
    else:
        compensated, info = compensate_ancuti2018(work, params, given)
        means, alpha = info.channel_means, dict(info.effective)
    balanced, balance = white_balance(compensated, params, given)
    if given.normalisation_bounds is None:
        bounds = normalisation_bounds(balanced, params)
    else:
        low, high = given.normalisation_bounds
        bounds = (float(low), float(high))
    if given.saliency_means is None:
        inputs = fusion_inputs(balanced, params, Statistics(normalisation_bounds=bounds))
        saliency = tuple(saliency_reference(fusion_input) for fusion_input in inputs)
    else:
        saliency = tuple(_three(mean) for mean in given.saliency_means)
    return Statistics(
        compensation_means=means,
        compensation_alpha=alpha,
        white_balance_means=(
            balance.channel_means
            if given.white_balance_means is None
            else _three(given.white_balance_means)
        ),
        white_balance_gains=balance.gray_world_gains,
        normalisation_bounds=bounds,
        saliency_means=saliency,
    )


def statistics_of(image: Image, params: Params, backend: Backend | None = None) -> Statistics:
    """Return the frame's own whole-frame statistics, those :func:`correct` measures on it.

    Fed back through ``correct(image, params, backend, statistics=...)`` they give the same
    result as ``correct(image, params, backend)``, bit for bit, when both run on the same
    device (``tests/test_prototype_temporal.py``, test 1).

    Args:
        image: The image.
        params: The parameter set.
        backend: Where the steps run; ``None`` runs them where the image is.

    Returns:
        The unsmoothed statistics of the image (:func:`measure` with nothing supplied).
    """
    return measure(image, params, None, backend)


def white_balanced_high_pass(
    image: Image, params: Params, backend: Backend | None = None
) -> NDArray[np.float32]:
    """Return the high-pass ``I - G*I`` of the white-balanced image, on the host.

    The chain is the frame's own (nothing supplied); this is the array whose percentiles are
    the N{} bounds, and on which the robust candidates are evaluated (:func:`robust_bounds`).

    Args:
        image: The image.
        params: The parameter set.
        backend: Where the steps run; ``None`` runs them where the image is.

    Returns:
        The high-pass, float32, shape ``(H, W, 3)``, as a NumPy array.
    """
    check_derived_values(image.shape, params)
    device = of(image) if backend is None else backend
    work = device.to_device(image)
    if params.method == "c3":
        compensated, _ = compensate_c3(work, params)
    else:
        compensated, _ = compensate_ancuti2018(work, params)
    balanced, _ = white_balance(compensated, params)
    return device.to_host(high_pass_of(balanced, params))


def render(
    image: Image, params: Params, statistics: Statistics | None, backend: Backend | None = None
) -> Image:
    """Correct one image from supplied statistics: :func:`prototype.pipeline.correct`'s output.

    Args:
        image: The image (full resolution or proxy).
        params: The parameter set.
        statistics: The statistics to render with (``None``: the frame's own).
        backend: Where the steps run; ``None`` runs them where the image is.

    Returns:
        The corrected image, of the kind of ``image``.
    """
    return correct(image, params, backend, statistics=statistics).output


def proxy(image: NDArray[np.float32], short_side: int = PROXY_SHORT_SIDE) -> NDArray[np.float32]:
    """Return the analysis proxy of a frame: an area average to ``short_side`` (spec 7.3).

    The frame is divided into ``f x f`` blocks, ``f = min(H, W) / short_side``, and each
    block is replaced by its mean (accumulated in float64, then cast to float32): 3840x2160
    to 960x540 is an exact 4x4 block mean. Only a whole factor that divides both sides is
    accepted; anything else is outside this package's envelope.

    Args:
        image: The full-resolution frame, float32, shape ``(H, W, 3)``.
        short_side: The proxy's short side in pixels.

    Returns:
        The proxy, float32, shape ``(H / f, W / f, 3)``.

    Raises:
        ValueError: The short side is not a whole multiple of ``short_side`` or the factor
            does not divide the long side.
    """
    height, width = image.shape[0], image.shape[1]
    factor, remainder = divmod(min(height, width), short_side)
    if factor < 1 or remainder or height % factor or width % factor:
        raise ValueError(
            f"a {width}x{height} frame has no whole-factor area average to short side {short_side}"
        )
    blocks = image.reshape(height // factor, factor, width // factor, factor, image.shape[2])
    out: NDArray[np.float32] = blocks.mean(axis=(1, 3), dtype=np.float64).astype(np.float32)
    return out


# --- series ---------------------------------------------------------------------------------------


def flatten(statistics: Statistics) -> dict[str, float]:
    """Return the record's scalars by name, in a fixed order (absent fields are left out).

    Names: ``compensation_means.R|G|B``, ``compensation_alpha.red|blue``,
    ``white_balance_means.R|G|B``, ``white_balance_gains.R|G|B``,
    ``normalisation_bounds.low|high`` and ``saliency_means.input1.L|a|b``,
    ``saliency_means.input2.L|a|b``.

    Args:
        statistics: The record.

    Returns:
        Name to value.
    """
    values: dict[str, float] = {}
    if statistics.compensation_means is not None:
        values.update(_named("compensation_means", _RGB, statistics.compensation_means))
    if statistics.compensation_alpha is not None:
        for channel in ALPHA_CHANNELS:
            if channel in statistics.compensation_alpha:
                values[f"compensation_alpha.{channel}"] = float(
                    statistics.compensation_alpha[channel]
                )
    if statistics.white_balance_means is not None:
        values.update(_named("white_balance_means", _RGB, statistics.white_balance_means))
    if statistics.white_balance_gains is not None:
        values.update(_named("white_balance_gains", _RGB, statistics.white_balance_gains))
    if statistics.normalisation_bounds is not None:
        values.update(
            _named("normalisation_bounds", ("low", "high"), statistics.normalisation_bounds)
        )
    if statistics.saliency_means is not None:
        for number, mean in enumerate(statistics.saliency_means, start=1):
            values.update(_named(f"saliency_means.input{number}", _LAB, mean))
    return values


def unflatten(values: Mapping[str, float]) -> Statistics:
    """Build a record from :func:`flatten`'s names; a field none of whose names occur is ``None``.

    Args:
        values: Name to value.

    Returns:
        The record.

    Raises:
        ValueError: A name is not exactly one :func:`flatten` produces (an unknown field, or a
            known field with an unknown suffix), the saliency inputs are not numbered 1, 2, ...
            without a gap, or a field is incomplete.
    """
    _check_names(values)
    alpha = {
        channel: float(values[f"compensation_alpha.{channel}"])
        for channel in ALPHA_CHANNELS
        if f"compensation_alpha.{channel}" in values
    }
    inputs = sorted(
        {name.split(".")[1] for name in values if name.startswith("saliency_means.")},
        key=lambda label: int(label.removeprefix("input")),
    )
    if [int(label.removeprefix("input")) for label in inputs] != list(range(1, len(inputs) + 1)):
        raise ValueError(f"saliency_means inputs {inputs} are not numbered 1, 2, ... without a gap")
    saliency = tuple(_three(_pick(values, f"saliency_means.{label}", _LAB)) for label in inputs)
    return Statistics(
        compensation_means=_optional_triple(values, "compensation_means"),
        compensation_alpha=alpha or None,
        white_balance_gains=_optional_triple(values, "white_balance_gains"),
        normalisation_bounds=_optional_bounds(values),
        saliency_means=saliency or None,
        white_balance_means=_optional_triple(values, "white_balance_means"),
    )


def stack(records: Sequence[Statistics]) -> Series:
    """Turn per-frame records into a series (one float64 array per scalar name).

    Args:
        records: One record per frame, all with the same fields.

    Returns:
        The series.

    Raises:
        ValueError: The records do not all hold the same scalars, or there are none.
    """
    if not records:
        raise ValueError("no frames")
    flat = [flatten(record) for record in records]
    names = list(flat[0])
    if any(list(values) != names for values in flat):
        raise ValueError("the frames' statistics differ in their fields")
    return {name: np.array([values[name] for values in flat], dtype=np.float64) for name in names}


def at(
    series: Mapping[str, NDArray[np.float64]], index: int, fields: Sequence[str] = ()
) -> Statistics:
    """Return frame ``index`` of a series as a record, optionally limited to some fields.

    Args:
        series: The series.
        index: The frame.
        fields: :class:`prototype.pipeline.Statistics` field names to keep; empty keeps all.

    Returns:
        The record (fields not kept are ``None``, so they are measured where it is used).
    """
    return unflatten(
        {
            name: float(values[index])
            for name, values in series.items()
            if not fields or name.split(".", 1)[0] in fields
        }
    )


def frame_count(series: Mapping[str, NDArray[np.float64]]) -> int:
    """Return the number of frames of a series (all its arrays have that length)."""
    return len(next(iter(series.values())))


def linear_trend(series: Mapping[str, NDArray[np.float64]]) -> Series:
    """Return each scalar's least-squares straight line over the frames (a pure drift).

    Rendering with it gives the flicker measure's floor for a statistic that only follows
    the excerpt's slow scene change, with no frame-to-frame jitter at all.

    Args:
        series: The series.

    Returns:
        The fitted series (same names and length).
    """
    out: Series = {}
    for name, values in series.items():
        index = np.arange(len(values), dtype=np.float64)
        slope, intercept = np.polyfit(index, values, 1) if len(values) > 1 else (0.0, values[0])
        out[name] = intercept + slope * index
    return out


def constant_statistics(series: Mapping[str, NDArray[np.float64]]) -> Statistics:
    """Return the record whose every scalar is the mean of that scalar over the series.

    Used as the constant-statistics reference of :func:`flicker`.

    Args:
        series: The series.

    Returns:
        The record.
    """
    return unflatten({name: float(np.mean(values)) for name, values in series.items()})


# --- smoothing ------------------------------------------------------------------------------------


def half_width(window_s: float, frame_rate: Fraction) -> int:
    """Return the half-width in frames of a centred window of ``window_s`` seconds.

    The window holds the frames whose distance from the centre is at most half the window:
    ``floor(window_s / 2 * frame_rate)`` frames on each side (D95: the window is in time).

    Args:
        window_s: The full window in seconds, non-negative.
        frame_rate: Frames per second.

    Returns:
        The number of frames on each side of the centre.

    Raises:
        ValueError: The window is negative or not finite, or the rate is not positive.
    """
    if not (math.isfinite(window_s) and window_s >= 0.0) or frame_rate <= 0:
        raise ValueError(f"unusable window {window_s} s at {frame_rate} fps")
    return math.floor(Fraction(window_s) / 2 * frame_rate)


@dataclass(frozen=True)
class Smoother:
    """A centred temporal filter for a statistic, with its window in seconds (D95).

    Kinds, each with a symmetric kernel over the ``2h + 1`` frames of :func:`half_width`:

    - ``moving_average``: equal weights.
    - ``gaussian``: weights ``exp(-t^2 / (2 s^2))`` with ``s`` chosen so that the kernel
      falls to :data:`GAUSSIAN_FALLOFF` (1 %) of its peak at ``t = window / 2``:
      ``s = (window / 2) / sqrt(2 ln 100)`` (the window is the kernel's full width at 1 %).
    - ``median_gaussian``: a centred running median over :data:`MEDIAN_WINDOW_S` (3 frames at
      30 fps), which removes a single bad frame, then the ``gaussian``.

    Weights are normalised to sum to 1. Past the ends of the series the end value is held
    (:data:`EDGE_MODE`). A window shorter than two frame periods is the identity.

    Attributes:
        kind: The filter.
        window_s: The full window in seconds.
    """

    kind: FilterKind
    window_s: float

    @property
    def label(self) -> str:
        """``<kind> <window> s``, for tables."""
        return f"{self.kind} {self.window_s:g} s"

    def radius(self, frame_rate: Fraction) -> int:
        """Return the frames on each side that can influence one output value.

        The Gaussian's (or the moving average's) half-width, plus the running median's
        half-width for ``median_gaussian``, whose median looks one frame further out before the
        Gaussian is applied (60 frames at 4 s and 30000/1001 fps: 59 + 1). A value at least this
        far from both ends of a series is untouched by the edge rule (:data:`EDGE_MODE`).

        Args:
            frame_rate: Frames per second.

        Returns:
            The reach of the whole filter chain in frames.
        """
        reach = half_width(self.window_s, frame_rate)
        if self.kind == "median_gaussian":
            reach += half_width(MEDIAN_WINDOW_S, frame_rate)
        return reach

    def kernel(self, frame_rate: Fraction) -> NDArray[np.float64]:
        """Return the linear kernel (the Gaussian for ``median_gaussian``), centre in the middle.

        Args:
            frame_rate: Frames per second.

        Returns:
            ``2h + 1`` weights summing to 1, symmetric.
        """
        half = half_width(self.window_s, frame_rate)
        offsets = np.arange(-half, half + 1, dtype=np.float64)
        if self.kind == "moving_average" or half == 0:
            weights = np.ones_like(offsets)
        else:
            sigma = (self.window_s / 2.0 * float(frame_rate)) / math.sqrt(
                2.0 * math.log(1.0 / GAUSSIAN_FALLOFF)
            )
            weights = np.exp(-(offsets**2) / (2.0 * sigma**2))
        out: NDArray[np.float64] = weights / weights.sum()
        return out

    def apply(self, values: NDArray[np.float64], frame_rate: Fraction) -> NDArray[np.float64]:
        """Smooth one series of values (one per frame, in presentation order).

        Args:
            values: The values, float64, shape ``(frames,)``.
            frame_rate: Frames per second.

        Returns:
            The smoothed values, the same shape.
        """
        series = np.asarray(values, dtype=np.float64)
        if self.kind == "median_gaussian":
            size = 2 * half_width(MEDIAN_WINDOW_S, frame_rate) + 1
            series = ndimage.median_filter(series, size=size, mode=EDGE_MODE)
        smoothed: NDArray[np.float64] = ndimage.convolve1d(
            series, self.kernel(frame_rate), mode=EDGE_MODE
        )
        return smoothed


SMOOTHING_CANDIDATES: tuple[Smoother, ...] = tuple(
    Smoother(kind, window) for kind in _FILTER_KINDS for window in (0.5, 1.0, 2.0, 4.0)
)
"""The candidates of the smoothing study (WP1.4 brief, claim 3)."""

COMPARISON_SMOOTHER = Smoother("gaussian", 1.0)
"""The one filter of the staged-versus-flat comparison (WP1.4 brief, claim 2)."""


def smooth(
    series: Mapping[str, NDArray[np.float64]],
    smoother: Smoother,
    frame_rate: Fraction,
    fields: Sequence[str] = (),
) -> Series:
    """Smooth every scalar of a series independently (optionally only some fields).

    Args:
        series: The series.
        smoother: The filter.
        frame_rate: Frames per second.
        fields: :class:`prototype.pipeline.Statistics` fields to smooth; empty smooths all.
            Scalars of other fields are left out of the result.

    Returns:
        The smoothed series.
    """
    return {
        name: smoother.apply(values, frame_rate)
        for name, values in series.items()
        if not fields or name.split(".", 1)[0] in fields
    }


def analyse_flat(
    raw: Mapping[str, NDArray[np.float64]], smoother: Smoother, frame_rate: Fraction
) -> Series:
    """FLAT analysis (D98, single stage): every raw statistic smoothed on its own.

    The raw statistics are each frame's own (:func:`statistics_of`, every stage measured
    on the frame corrected with its own unsmoothed earlier stages); nothing is re-measured.

    Args:
        raw: The raw per-frame series.
        smoother: The filter.
        frame_rate: Frames per second.

    Returns:
        The smoothed series.
    """
    return smooth(raw, smoother, frame_rate)


def analyse_staged(
    images: Sequence[Image],
    params: Params,
    smoother: Smoother,
    frame_rate: Fraction,
    backend: Backend | None = None,
) -> tuple[Series, dict[str, Series]]:
    """STAGED analysis (D97): each stage measured on frames corrected with smoothed earlier stages.

    For each stage of :data:`STAGES` in order: every frame is measured (:func:`measure`)
    with the SMOOTHED statistics of all earlier stages supplied (so the image the stage sees
    is corrected with them) and the stage's own and later statistics measured; the stage's
    statistics are then smoothed and kept for the next stages.

    Args:
        images: The frames (proxies), in presentation order.
        params: The parameter set (its method decides the stages).
        smoother: The filter.
        frame_rate: Frames per second.
        backend: Where the steps run.

    Returns:
        The smoothed series of every stage together, and per stage name the series that
        stage measured before smoothing (its own fields only).

    Raises:
        ValueError: There are fewer than :data:`MIN_FRAMES` frames.
    """
    if len(images) < MIN_FRAMES:
        raise ValueError(
            f"a sequence analysis needs at least {MIN_FRAMES} frames, got {len(images)}"
        )
    smoothed: Series = {}
    measured: dict[str, Series] = {}
    for stage in STAGES[params.method]:
        records = [
            measure(image, params, at(smoothed, index) if smoothed else None, backend)
            for index, image in enumerate(images)
        ]
        stage_series = {
            name: values
            for name, values in stack(records).items()
            if name.split(".", 1)[0] in stage.fields
        }
        measured[stage.name] = stage_series
        smoothed.update(smooth(stage_series, smoother, frame_rate))
    return smoothed, measured


def mismatch(
    flat: Mapping[str, NDArray[np.float64]], staged: Mapping[str, NDArray[np.float64]]
) -> dict[str, dict[str, float | int]]:
    """Return, per scalar, the flat-minus-staged difference over the frames.

    Args:
        flat: The flat series.
        staged: The staged series (same names and length).

    Returns:
        Per name: ``mean`` (signed), ``mean_abs``, ``max_abs`` and ``frame`` (the index of
        the largest absolute difference).
    """
    out: dict[str, dict[str, float | int]] = {}
    for name, values in flat.items():
        difference = values - staged[name]
        worst = int(np.argmax(np.abs(difference)))
        out[name] = {
            "mean": float(np.mean(difference)),
            "mean_abs": float(np.mean(np.abs(difference))),
            "max_abs": float(abs(difference[worst])),
            "frame": worst,
        }
    return out


# --- the flicker measure --------------------------------------------------------------------------


def frame_signals(image: NDArray[np.float32]) -> NDArray[np.float64]:
    """Return the four flicker signals of a frame: the R, G, B means and the BT.709 luma mean.

    The means are accumulated in float64 on the host.

    Args:
        image: An RGB image (NumPy), shape ``(H, W, 3)``.

    Returns:
        ``[mean R, mean G, mean B, mean luma]`` in [0, 1].
    """
    means = np.asarray(image, dtype=np.float32).reshape(-1, 3).mean(axis=0, dtype=np.float64)
    return np.append(means, float(means @ _LUMA))


@dataclass(frozen=True)
class Flicker:
    """The flicker of a rendered sequence against its constant-statistics reference.

    Attributes:
        per_step: ``|d(signal) - d(reference signal)|`` per frame step and signal, in 8-bit
            levels, shape ``(frames - 1, 4)`` (:data:`SIGNALS` order).
        per_signal: The mean of ``per_step`` over the steps, per signal.
        value: The mean over the steps and the four signals: the figure tabulated.
    """

    per_step: NDArray[np.float64]
    per_signal: dict[str, float]
    value: float


def flicker(
    signals: NDArray[np.float64], reference: NDArray[np.float64], steps: slice | None = None
) -> Flicker:
    """The package's flicker measure: frame-to-frame change not explained by content.

    ``signals`` are :func:`frame_signals` of the frames rendered with the statistics under
    test, ``reference`` those of the SAME frames rendered with constant statistics (the
    mean of the raw series, :func:`constant_statistics`). Per signal and frame step,
    ``|(s[t+1] - s[t]) - (r[t+1] - r[t])|`` in 8-bit levels (x 255): the content's own change
    passes through both renders alike and cancels to first order, so what remains is the
    change caused by the statistics changing. Zero when the statistics are constant.

    Args:
        signals: Shape ``(frames, 4)``.
        reference: Shape ``(frames, 4)``.
        steps: Which frame steps to average (``slice(a, b)`` keeps the steps from frame
            ``a`` to ``a + 1`` up to ``b - 1`` to ``b``); ``None`` keeps all.

    Returns:
        The measure.

    Raises:
        ValueError: The shapes differ or there is less than one step.
    """
    if signals.shape != reference.shape or signals.ndim != 2 or len(signals) < 2:
        raise ValueError("signals and reference must have the same (frames >= 2, 4) shape")
    per_step = np.abs(np.diff(signals, axis=0) - np.diff(reference, axis=0)) * 255.0
    if steps is not None:
        per_step = per_step[steps]
    if not len(per_step):
        raise ValueError("no frame step selected")
    per_signal = {name: float(per_step[:, k].mean()) for k, name in enumerate(SIGNALS)}
    return Flicker(per_step=per_step, per_signal=per_signal, value=float(per_step.mean()))


def source_referenced_flicker(
    signals: NDArray[np.float64], source: NDArray[np.float64]
) -> dict[str, float]:
    """The brief's suggested form, kept as a cross-check: ``mean|d s| - mean|d source|``.

    Per signal, the mean absolute frame-to-frame change of the rendered frames minus that of
    the source frames, in 8-bit levels. Content change cancels only where the correction
    leaves its size unchanged (a gain different from 1 scales it), so this is not the
    tabulated measure (:func:`flicker`).

    Args:
        signals: Rendered frames' signals, shape ``(frames, 4)``.
        source: Source frames' signals, the same shape.

    Returns:
        Per signal name the difference, and ``"mean"`` over the four.
    """
    rendered = np.abs(np.diff(signals, axis=0)).mean(axis=0)
    original = np.abs(np.diff(source, axis=0)).mean(axis=0)
    difference = (rendered - original) * 255.0
    out = {name: float(difference[k]) for k, name in enumerate(SIGNALS)}
    out["mean"] = float(difference.mean())
    return out


# --- the step response ----------------------------------------------------------------------------


def step_response(
    smoother: Smoother, frame_rate: Fraction, frequencies_hz: Sequence[float] = (0.5, 1.0, 2.0)
) -> dict[str, Any]:
    """Measure a filter's responsiveness: its response to a step, an outlier and sinusoids.

    - Step: a series of 0 then 1 over 30 s, the step half-way; the step instant is the
      midpoint between the last 0 and the first 1. ``t90_s`` is the time from that instant
      to the first frame at or above 0.9; ``t10_s`` (negative for a centred filter: it
      responds before the step) to the first frame at or above 0.1; ``rise_10_90_s`` their
      difference.
    - Outlier: a single frame of 1 in a series of 0: ``outlier_peak`` is the response at
      that frame (0 when the filter removes it).
    - Sinusoids of unit amplitude at ``frequencies_hz``: ``gain`` is the amplitude of the
      response fitted over the interior (one window from each end), per frequency.

    Args:
        smoother: The filter.
        frame_rate: Frames per second.
        frequencies_hz: The sinusoid frequencies.

    Returns:
        ``t10_s``, ``t90_s``, ``rise_10_90_s``, ``outlier_peak`` and ``gain`` (frequency as a
        string to the amplitude).
    """
    rate = float(frame_rate)
    count = round(30.0 * rate)
    middle = count // 2
    step = np.zeros(count)
    step[middle:] = 1.0
    response = smoother.apply(step, frame_rate)
    instant = middle - 0.5
    t10 = (int(np.argmax(response >= 0.1)) - instant) / rate
    t90 = (int(np.argmax(response >= 0.9)) - instant) / rate
    outlier = np.zeros(count)
    outlier[middle] = 1.0
    peak = float(smoother.apply(outlier, frame_rate)[middle])
    margin = 2 * half_width(smoother.window_s, frame_rate) + 1
    times = np.arange(count) / rate
    gains: dict[str, float] = {}
    for frequency in frequencies_hz:
        basis = np.stack(
            [np.sin(2 * np.pi * frequency * times), np.cos(2 * np.pi * frequency * times)], axis=1
        )
        smoothed = smoother.apply(basis[:, 0], frame_rate)
        inner = slice(margin, count - margin)
        coefficients, *_ = np.linalg.lstsq(basis[inner], smoothed[inner], rcond=None)
        gains[f"{frequency:g}"] = float(np.hypot(*coefficients))
    return {
        "t10_s": t10,
        "t90_s": t90,
        "rise_10_90_s": t90 - t10,
        "outlier_peak": peak,
        "gain": gains,
    }


# --- robust statistics for the N{} bounds ---------------------------------------------------------


@dataclass(frozen=True)
class RobustBound:
    """A candidate statistic for the N{} bounds of a high-pass (spec 14.1, DR-14).

    Attributes:
        name: Label for tables.
        kind: ``"percentile"`` (``min``/``max`` are percentiles 0 and 100) or
            ``"trimmed_sd"``.
        low: Lower percentile (``percentile``).
        high: Upper percentile (``percentile``).
        k: The multiple of the standard deviation (``trimmed_sd``).
    """

    name: str
    kind: Literal["percentile", "trimmed_sd"]
    low: float = 0.0
    high: float = 100.0
    k: float = 0.0


ROBUST_CANDIDATES: tuple[RobustBound, ...] = (
    RobustBound("min/max", "percentile", 0.0, 100.0),
    RobustBound("p0.5/p99.5 (default)", "percentile", 0.5, 99.5),
    RobustBound("p1/p99", "percentile", 1.0, 99.0),
    RobustBound("p2/p98", "percentile", 2.0, 98.0),
    RobustBound("trimmed mean +- 2.5 sd", "trimmed_sd", k=2.5),
    RobustBound("trimmed mean +- 3 sd", "trimmed_sd", k=3.0),
)
"""The candidates of the robust-statistics study (WP1.4 brief, claim 5)."""


def robust_bounds(values: NDArray[np.floating[Any]], candidate: RobustBound) -> tuple[float, float]:
    """Return a candidate's low and high bound over all values (pixels and channels).

    - ``percentile``: NumPy's linear-interpolation percentiles, as the pipeline takes them
      (:func:`prototype.pipeline.normalisation_bounds`); 0 and 100 are the minimum and
      maximum ([A18]'s stretch).
    - ``trimmed_sd``: the values below percentile :data:`TRIM_PERCENT` and above
      ``100 - TRIM_PERCENT`` are dropped; with ``m`` and ``s`` the mean and the population
      standard deviation of the rest (float64), the bounds are ``m - k s`` and ``m + k s``.

    Args:
        values: The high-pass values (any shape).
        candidate: The candidate.

    Returns:
        The low and high bound.
    """
    flat = np.asarray(values).reshape(-1)
    if candidate.kind == "percentile":
        low, high = np.percentile(flat, [candidate.low, candidate.high], method="linear")
        return float(low), float(high)
    cut_low, cut_high = np.percentile(flat, [TRIM_PERCENT, 100.0 - TRIM_PERCENT], method="linear")
    kept = flat[(flat >= cut_low) & (flat <= cut_high)].astype(np.float64)
    centre = float(kept.mean())
    spread = float(kept.std())
    return centre - candidate.k * spread, centre + candidate.k * spread


def clipped_fraction(values: NDArray[np.floating[Any]], bounds: tuple[float, float]) -> float:
    """Return the fraction of PIXELS the stretch with ``bounds`` clips.

    A pixel counts as clipped when any of its three channels is below ``low`` or above
    ``high`` (the stretch clips each channel value; this counts the pixels it touches).

    Args:
        values: The high-pass, shape ``(..., 3)`` (the last axis is the channels).
        bounds: The low and high bound.

    Returns:
        A fraction in [0, 1].

    Raises:
        ValueError: The last axis does not hold three channels.
    """
    pixels = _as_pixels(values)
    low, high = bounds
    return float(np.count_nonzero(((pixels < low) | (pixels > high)).any(axis=1)) / len(pixels))


def clipped_sample_fraction(
    values: NDArray[np.floating[Any]], bounds: tuple[float, float]
) -> float:
    """Return the fraction of channel SAMPLES the stretch with ``bounds`` clips.

    Each of the ``3 * H * W`` values counts on its own (the quantity :func:`clipped_fraction`
    reported before WP1.4's remediation); a pixel with two clipped channels counts twice.

    Args:
        values: The high-pass, any shape.
        bounds: The low and high bound.

    Returns:
        A fraction in [0, 1].
    """
    flat = np.asarray(values).reshape(-1)
    low, high = bounds
    return float(np.count_nonzero((flat < low) | (flat > high)) / flat.size)


# --- helpers --------------------------------------------------------------------------------------


def _as_pixels(values: NDArray[np.floating[Any]]) -> NDArray[np.floating[Any]]:
    """The values as one row of three channels per pixel; any other last axis is refused."""
    array = np.asarray(values)
    if array.ndim < 1 or array.shape[-1] != 3:
        raise ValueError(f"values need a last axis of 3 channels, got shape {array.shape}")
    return array.reshape(-1, 3)


def _check_names(values: Mapping[str, float]) -> None:
    """Raise ValueError naming the first name that :func:`flatten` cannot produce."""
    suffixes = {
        "compensation_means": _RGB,
        "compensation_alpha": ALPHA_CHANNELS,
        "white_balance_means": _RGB,
        "white_balance_gains": _RGB,
        "normalisation_bounds": ("low", "high"),
    }
    for name in values:
        field, _, rest = name.partition(".")
        if field in suffixes:
            valid = rest in suffixes[field]
        elif field == "saliency_means":
            label, _, component = rest.partition(".")
            digits = label.removeprefix("input")
            valid = (
                label.startswith("input")
                and digits.isascii()
                and digits.isdigit()
                and digits == str(int(digits))
                and int(digits) >= 1
                and component in _LAB
            )
        else:
            valid = False
        if not valid:
            raise ValueError(f"unknown statistic {name!r}")


def _named(prefix: str, labels: Sequence[str], values: Sequence[float]) -> dict[str, float]:
    """``{prefix.label: value}`` for labels and values of the same length."""
    if len(labels) != len(values):
        raise ValueError(f"{prefix} needs {len(labels)} values, got {len(values)}")
    return {f"{prefix}.{label}": float(value) for label, value in zip(labels, values, strict=True)}


def _pick(values: Mapping[str, float], prefix: str, labels: Sequence[str]) -> tuple[float, ...]:
    """The values of ``prefix.label`` for every label; all must be present."""
    missing = [label for label in labels if f"{prefix}.{label}" not in values]
    if missing:
        raise ValueError(f"{prefix} lacks {missing}")
    return tuple(float(values[f"{prefix}.{label}"]) for label in labels)


def _optional_triple(values: Mapping[str, float], prefix: str) -> tuple[float, float, float] | None:
    """An R, G, B triple from ``values``, or ``None`` when none of its names occur."""
    if not any(name.startswith(prefix + ".") for name in values):
        return None
    red, green, blue = _pick(values, prefix, _RGB)
    return red, green, blue


def _optional_bounds(values: Mapping[str, float]) -> tuple[float, float] | None:
    """The N{} bounds from ``values``, or ``None`` when neither occurs."""
    if not any(name.startswith("normalisation_bounds.") for name in values):
        return None
    low, high = _pick(values, "normalisation_bounds", ("low", "high"))
    return low, high


def _three(values: Sequence[float]) -> tuple[float, float, float]:
    """Three floats from a sequence of exactly three."""
    if len(values) != 3:
        raise ValueError(f"a triple needs 3 values, got {len(values)}")
    return float(values[0]), float(values[1]), float(values[2])
