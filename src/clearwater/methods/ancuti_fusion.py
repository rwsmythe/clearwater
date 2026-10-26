"""The IF-3 correction methods ``c3`` and ``ancuti2018``: staged analysis and render (AD-6).

Both methods are [A18]'s colour balance and fusion with a selectable channel compensation
(D16): ``c3`` compensates with 3C (no whole-frame statistic, no gain cap, D49) and
``ancuti2018`` with Ancuti 2018's red (and blue) compensation and its gain caps. They share the
white balance and the fusion steps (architecture section 3); one class, two instances.

Stages (AD-6, D97; each measured on the image corrected with the SUPPLIED records of the
stages before it):

- ``ancuti2018``: ``compensation`` (the input's channel means, the gain-cap statistic of red
  and blue, and the capped alpha per frame; source-only), ``white_balance`` (the means and
  gray-world gains of the compensated image), ``fusion`` (the N{} bounds of the white-balanced
  image and the saliency Lab mean of each fusion input).
- ``c3``: ``white_balance`` and ``fusion`` as above, on the 3C-compensated image
  (``clearwater.interfaces.stubs.C3_STAGES``, frozen).

The statistics contract (Y-1, as ruled): ``analyze`` returns every statistic its stage
declares, as float64 host arrays of a fixed shape (:data:`STATISTIC_SHAPES`). White-balance
``gains`` are the gray-world gains before the strength and the D99 clamp, which apply after
smoothing: inside ``render`` and inside the fusion stage's ``analyze``. Ancuti ``alpha`` is
the capped alpha per frame, smoothed as a value; ``alpha[1]`` (blue) is 0 when blue
compensation is off. ``closed_form`` is non-None only for the source-only ``compensation``
stage: alpha recomputed from the measured means and cap statistics with the current
parameters, bit-identical to ``analyze``. Supplied records are checked (Y-2): a missing or
unexpected statistic, a wrong shape or a non-finite value is one ValueError naming the stage
and the statistic.

``render`` measures nothing: it renders from the supplied records only, so a preview and an
export rendered from the same records agree by construction (spec 6.6, V8). It ends with the
blend ``(1 - b) * fused + b * input``, ``b = blend_with_original / 100`` (AD-8). The backend is
the one the image's device names (``clearwater.core.backend_for``); pixels of another backend
are refused. The host reads per frame (DR-38 a) are those of the measuring steps: ancuti2018
three in ``compensation``, one in ``white_balance`` and three in ``fusion``; c3 one and three;
``render`` none.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Mapping
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from clearwater.core import CoreBackend, backend_for, channel_means
from clearwater.interfaces.image import Array, Image
from clearwater.interfaces.method import Parameter, Stage, Statistics

from .compensation import cap_statistics, compensate_ancuti2018, compensate_c3, effective_alphas
from .fusion import (
    fusion_inputs,
    multiscale_fusion,
    normalisation_bounds,
    saliency_reference,
    weight_maps,
)
from .schema import ANCUTI2018_PARAMETERS, C3_PARAMETERS, resolve_parameters
from .white_balance import applied_gains, apply_white_balance, gray_world_gains

type MethodId = Literal["c3", "ancuti2018"]
type _Record = dict[str, NDArray[np.float64]]

STATISTIC_SHAPES: dict[str, tuple[int, ...]] = {
    "means": (3,),
    "cap_statistics": (2,),
    "alpha": (2,),
    "gains": (3,),
    "bounds": (2,),
    "saliency_means": (2, 3),
}
"""The shape of each statistic (Y-1 a). ``cap_statistics`` and ``alpha`` are (red, blue);
``saliency_means`` is one Lab vector per fusion input, in input order."""

_FUSION_PARAMETERS = (
    "white_balance_strength",
    "max_white_balance_gain",
    "sharpen_blur_fraction",
    "normalisation_low",
    "normalisation_high",
    "gamma",
    "sharpen_strength",
)
# The fusion stage's measurement depends on these directly; the compensation parameters reach
# it through ``depends_on_stages`` (the transitive convention of the frozen C3_STAGES).

C3_STAGES: tuple[Stage, ...] = (
    Stage(
        name="white_balance",
        statistics=("means", "gains"),
        smoothed=("means", "gains"),
        depends_on_parameters=(
            "kappa",
            "lambda_",
            "c3_strength",
            "c3_kernel_fraction",
            "c3_mask_threshold",
            "c3_mask_smooth_fraction",
        ),
        depends_on_stages=(),
        source_only=False,
    ),
    Stage(
        name="fusion",
        statistics=("bounds", "saliency_means"),
        smoothed=("bounds", "saliency_means"),
        depends_on_parameters=_FUSION_PARAMETERS,
        depends_on_stages=("white_balance",),
        source_only=False,
    ),
)
"""The ``c3`` stages, equal to the frozen ``clearwater.interfaces.stubs.C3_STAGES``."""

ANCUTI2018_STAGES: tuple[Stage, ...] = (
    Stage(
        name="compensation",
        statistics=("means", "cap_statistics", "alpha"),
        smoothed=("means", "alpha"),
        depends_on_parameters=("alpha", "blue_compensation", "red_gain_cap", "blue_gain_cap"),
        depends_on_stages=(),
        source_only=True,
    ),
    Stage(
        name="white_balance",
        statistics=("means", "gains"),
        smoothed=("means", "gains"),
        depends_on_parameters=(),
        depends_on_stages=("compensation",),
        source_only=False,
    ),
    Stage(
        name="fusion",
        statistics=("bounds", "saliency_means"),
        smoothed=("bounds", "saliency_means"),
        depends_on_parameters=_FUSION_PARAMETERS,
        depends_on_stages=("compensation", "white_balance"),
        source_only=False,
    ),
)
"""The ``ancuti2018`` stages. ``compensation`` is the only source-only stage: its measured
statistics (``means``, ``cap_statistics``) depend on the source alone and its ``alpha`` is
their closed form; ``cap_statistics`` is not smoothed (the render does not read it)."""


class AncutiFusionMethod:
    """One of the two registered correction methods (IF-3 ``CorrectionMethod``).

    Attributes:
        id: ``"c3"`` or ``"ancuti2018"``.
        label: The GUI label.
        parameters: The method's schema (:mod:`clearwater.methods.schema`).
        stages: The ordered statistic stages.
    """

    def __init__(self, method_id: MethodId) -> None:
        """Create the method.

        Args:
            method_id: ``"c3"`` or ``"ancuti2018"``.

        Raises:
            ValueError: Another id.
        """
        self.id: str
        self.label: str
        self.parameters: tuple[Parameter, ...]
        self.stages: tuple[Stage, ...]
        if method_id == "c3":
            self.id, self.label = "c3", "3C"
            self.parameters, self.stages = C3_PARAMETERS, C3_STAGES
        elif method_id == "ancuti2018":
            self.id, self.label = "ancuti2018", "Ancuti 2018"
            self.parameters, self.stages = ANCUTI2018_PARAMETERS, ANCUTI2018_STAGES
        else:
            raise ValueError(f"unknown method id {method_id!r}; known: c3, ancuti2018")
        self._stage_by_name = {stage.name: stage for stage in self.stages}

    def __repr__(self) -> str:
        """Return the method's id."""
        return f"{type(self).__name__}({self.id!r})"

    # -- IF-3 ---------------------------------------------------------------------------------

    def analyze(
        self,
        stage: str,
        image: Image,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
    ) -> Statistics:
        """Measure one stage's statistics on ``image``, given the earlier stages' records.

        The image is first corrected up to the stage with the records in ``earlier``, used
        exactly as given (smoothed or raw); only this stage's statistics are measured.

        Args:
            stage: The stage name.
            image: The image to measure (the analysis proxy).
            params: The parameter values; missing names take their defaults.
            earlier: The records of the stages this stage depends on, by stage name.

        Returns:
            The stage's raw statistics, every declared name (Y-1 a).

        Raises:
            ValueError: An unknown stage, a parameter problem (one error naming it), an
                ``earlier`` key that is not a stage of the method, a supplied record that does
                not fit (Y-2), or an image whose device has no backend or whose pixels are not
                a float32 ``(H, W, 3)`` array.
            KeyError: A stage this stage depends on is missing from ``earlier``.
            TypeError: The pixels are not arrays of the backend ``image.device`` names.
        """
        spec = self._stage(stage)
        values = resolve_parameters(self.id, self.parameters, params)
        records = self._records(earlier, spec.depends_on_stages)
        backend, pixels = _pixels(image)
        if spec.name == "compensation":
            return self._measure_compensation(backend, pixels, values)
        compensated = self._compensate(backend, pixels, values, records)
        if spec.name == "white_balance":
            means = channel_means(backend, compensated)
            return {"means": _array(means), "gains": _array(gray_world_gains(means))}
        balanced = self._white_balance(backend, compensated, values, records["white_balance"])
        del compensated
        bounds = normalisation_bounds(
            backend,
            balanced,
            sharpen_blur_fraction=values["sharpen_blur_fraction"],
            normalisation_low=values["normalisation_low"],
            normalisation_high=values["normalisation_high"],
        )
        inputs = fusion_inputs(
            backend,
            balanced,
            gamma=values["gamma"],
            sharpen_strength=values["sharpen_strength"],
            sharpen_blur_fraction=values["sharpen_blur_fraction"],
            bounds=bounds,
        )
        del balanced
        saliency = [saliency_reference(backend, fusion_input) for fusion_input in inputs]
        return {"bounds": _array(bounds), "saliency_means": _array(saliency)}

    def render(
        self,
        image: Image,
        params: Mapping[str, Any],
        statistics: Mapping[str, Statistics],
    ) -> Image:
        """Correct ``image`` from the supplied statistics; measures nothing.

        Args:
            image: The image to correct.
            params: The parameter values; missing names take their defaults.
            statistics: The record of every stage, by stage name (smoothed for video).

        Returns:
            The corrected image: float32 ``(H, W, 3)`` in [0, 1] on the same device, with the
            input's colour description and type (a ``Frame`` keeps its presentation time).

        Raises:
            ValueError: A parameter problem, a key that is not a stage of the method, a
                record that does not fit (Y-2), or an image whose device has no backend or
                whose pixels are not a float32 ``(H, W, 3)`` array.
            KeyError: A stage is missing from ``statistics``.
            TypeError: The pixels are not arrays of the backend ``image.device`` names.
        """
        values = resolve_parameters(self.id, self.parameters, params)
        records = self._records(statistics, tuple(self._stage_by_name))
        backend, pixels = _pixels(image)
        compensated = self._compensate(backend, pixels, values, records)
        balanced = self._white_balance(backend, compensated, values, records["white_balance"])
        del compensated
        fusion = records["fusion"]
        inputs = fusion_inputs(
            backend,
            balanced,
            gamma=values["gamma"],
            sharpen_strength=values["sharpen_strength"],
            sharpen_blur_fraction=values["sharpen_blur_fraction"],
            bounds=fusion["bounds"].tolist(),
        )
        del balanced
        weights = weight_maps(
            backend,
            inputs,
            laplacian_fraction=values["laplacian_fraction"],
            saliency_blur_fraction=values["saliency_blur_fraction"],
            weight_delta=values["weight_delta"],
            saliency_means=fusion["saliency_means"].tolist(),
        )
        fused = multiscale_fusion(
            backend, inputs, weights, pyramid_min_level_size=values["pyramid_min_level_size"]
        )
        del inputs, weights
        out = blend_with_original(fused, pixels, values["blend_with_original"])
        return dataclasses.replace(image, pixels=out)

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        """Update a stage's record from the current parameters, without touching the image.

        Only ``ancuti2018``'s ``compensation`` has a closed form (Y-1 d): its ``means`` and
        ``cap_statistics`` are passed through and ``alpha`` is recomputed (AD-7), exactly as
        ``analyze`` computes it. Every other stage's measurement depends on parameters or
        earlier stages: None.

        Args:
            stage: The stage name.
            params: The parameter values; missing names take their defaults.
            earlier: The records of the earlier stages (not consumed by any closed form).
            measured: The record measured for the stage.

        Returns:
            The updated record, or None when the stage has no closed form.

        Raises:
            ValueError: An unknown stage, a parameter problem, an ``earlier`` key that is not
                a stage of the method, or a ``measured`` record that does not fit (Y-2).
        """
        spec = self._stage(stage)
        values = resolve_parameters(self.id, self.parameters, params)
        self._records(earlier, ())
        record = _checked_record(spec, measured)
        if not spec.source_only:
            return None
        return _compensation_record(record["means"], record["cap_statistics"], values)

    # -- the steps ------------------------------------------------------------------------------

    def _stage(self, name: str) -> Stage:
        """Return the stage called ``name``, or raise ValueError."""
        spec = self._stage_by_name.get(name)
        if spec is None:
            raise ValueError(
                f"unknown stage {name!r} of method {self.id!r}; stages: "
                f"{', '.join(self._stage_by_name)}"
            )
        return spec

    def _records(
        self, supplied: Mapping[str, Statistics], required: tuple[str, ...]
    ) -> dict[str, _Record]:
        """Check the supplied records: known stage names, the required ones present (Y-2)."""
        for name in supplied:
            if name not in self._stage_by_name:
                raise ValueError(
                    f"statistics for {name!r}, which is not a stage of method {self.id!r}"
                )
        for name in required:
            if name not in supplied:
                raise KeyError(f"missing statistics for stage {name!r}")
        return {
            name: _checked_record(self._stage_by_name[name], supplied[name]) for name in required
        }

    def _measure_compensation(
        self, backend: CoreBackend, pixels: Array, values: Mapping[str, Any]
    ) -> _Record:
        """Ancuti stage 1: the means and both cap statistics of the input, and the alpha."""
        means = channel_means(backend, pixels)
        caps = cap_statistics(backend, pixels, blue_compensation=True)
        return _compensation_record(_array(means), _array((caps["red"], caps["blue"])), values)

    def _compensate(
        self,
        backend: CoreBackend,
        pixels: Array,
        values: Mapping[str, Any],
        records: Mapping[str, _Record],
    ) -> Array:
        """Compensate: 3C, or Ancuti 2018 from the supplied compensation record."""
        if self.id == "c3":
            return compensate_c3(
                backend,
                pixels,
                kappa=values["kappa"],
                lambda_=values["lambda_"],
                c3_strength=values["c3_strength"],
                c3_kernel_fraction=values["c3_kernel_fraction"],
                c3_mask_threshold=values["c3_mask_threshold"],
                c3_mask_smooth_fraction=values["c3_mask_smooth_fraction"],
            )
        record = records["compensation"]
        alphas = {"red": float(record["alpha"][0])}
        if values["blue_compensation"]:
            alphas["blue"] = float(record["alpha"][1])
        return compensate_ancuti2018(backend, pixels, means=record["means"].tolist(), alphas=alphas)

    def _white_balance(
        self,
        backend: CoreBackend,
        compensated: Array,
        values: Mapping[str, Any],
        record: _Record,
    ) -> Array:
        """White-balance with the supplied gray-world gains: strength, then the D99 clamp."""
        gains, _clamped = applied_gains(
            record["gains"].tolist(),
            white_balance_strength=values["white_balance_strength"],
            max_white_balance_gain=values["max_white_balance_gain"],
        )
        return apply_white_balance(backend, compensated, gains)


def blend_with_original(fused: Array, original: Array, percent: float) -> Array:
    """Return ``(1 - b) * fused + b * original`` with ``b = percent / 100`` (spec 6.7, AD-8).

    0 % gives the fused image, 100 % the original (identical values, the other term being
    multiplied by exactly 0; the sign of zero aside, as ``0 * x + -0.0`` may give ``+0.0``).
    Linear in the display-encoded values, as the prototype's ``correct``; both arrays lie in
    [0, 1], so the result does too and is not clipped.

    Args:
        fused: The corrected image, float32 ``(H, W, 3)``.
        original: The input image, same shape and backend.
        percent: ``blend_with_original``, 0 to 100.

    Returns:
        The blend, float32.
    """
    blend = float(percent) / 100.0
    out: Array = ((1.0 - blend) * fused + blend * original).astype(np.float32, copy=False)
    return out


def _pixels(image: Image) -> tuple[CoreBackend, Array]:
    """Return the backend ``image.device`` names and the image's checked pixels."""
    backend = backend_for(image.device)
    backend.check_rgb(image.pixels)
    return backend, image.pixels


def _array(values: Any) -> NDArray[np.float64]:
    """Return ``values`` as a new float64 host array."""
    return np.array(values, dtype=np.float64)


def _compensation_record(
    means: NDArray[np.float64], caps: NDArray[np.float64], values: Mapping[str, Any]
) -> _Record:
    """The Ancuti compensation record: the measured values and the capped alpha (AD-6, AD-7)."""
    alphas = effective_alphas(
        means=means.tolist(),
        cap_statistics={"red": float(caps[0]), "blue": float(caps[1])},
        alpha=values["alpha"],
        blue_compensation=values["blue_compensation"],
        red_gain_cap=values["red_gain_cap"],
        blue_gain_cap=values["blue_gain_cap"],
    )
    return {
        "means": means.copy(),
        "cap_statistics": caps.copy(),
        "alpha": _array((alphas["red"], alphas.get("blue", 0.0))),
    }


def _checked_record(stage: Stage, record: Statistics) -> _Record:
    """Return a supplied record as float64 host arrays, or raise ValueError (Y-2).

    The names must be exactly the stage's statistics, each a host array (or nested list) of
    integer or real numbers, of its fixed shape and finite. Booleans, complex numbers, text,
    Python objects and dates are refused before any conversion would coerce them; a Python int
    too large for any integer dtype lands as an object array and is refused with them.
    """
    for name in stage.statistics:
        if name not in record:
            raise ValueError(f"stage {stage.name!r}: statistic {name!r} is missing")
    for name in record:
        if name not in stage.statistics:
            raise ValueError(f"stage {stage.name!r}: statistic {name!r} is not one it declares")
    checked: _Record = {}
    for name in stage.statistics:
        try:
            supplied = np.asarray(record[name])
            if supplied.dtype.kind not in "iuf":
                raise TypeError(f"dtype {supplied.dtype} is not integer or real")
            value = np.array(supplied, dtype=np.float64)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                f"stage {stage.name!r}: statistic {name!r} is not a host array of numbers ({exc})"
            ) from exc
        if value.shape != STATISTIC_SHAPES[name]:
            raise ValueError(
                f"stage {stage.name!r}: statistic {name!r} has shape {value.shape}, "
                f"expected {STATISTIC_SHAPES[name]}"
            )
        if not np.isfinite(value).all():
            raise ValueError(
                f"stage {stage.name!r}: statistic {name!r} is not finite: {value.tolist()}"
            )
        checked[name] = value
    return checked
