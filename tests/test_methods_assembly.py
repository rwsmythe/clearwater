"""WP3.4: the IF-3 methods ``c3`` and ``ancuti2018`` -- stages, closed form, render and schema.

The contract tests (IF-3, Y-1, Y-2, AD-6, AD-7, D49, D99, AD-8, DR-19, DR-38, DR-40) run on
seeded synthetic images. Each ``check_*`` function is one claim about a method; the planted
tests at the end run it on a named wrong implementation and require it to fail, so each claim
is shown to distinguish. The prototype comparisons, CPU against GPU, V8 and V9 are in
``test_methods_assembly_prototype.py``.
"""

from __future__ import annotations

import dataclasses
import json
import math
import subprocess
import sys
from collections.abc import Callable, Iterator, Mapping
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

import clearwater.methods.ancuti_fusion as af
import clearwater.methods.compensation as compensation_module
import clearwater.methods.fusion as fusion_module
from clearwater.core import CoreBackend, NumpyBackend, backend_for, check_sigma, spatial_sigma
from clearwater.core.backend import _probe_gpu
from clearwater.interfaces.image import ColorDescription, Frame, Image
from clearwater.interfaces.method import CorrectionMethod, Parameter, Statistics
from clearwater.interfaces.parameters import ParameterSet, validate_parameter_set
from clearwater.interfaces.stubs import C3_STAGES
from clearwater.methods import AncutiFusionMethod, available_methods
from clearwater.methods.compensation import (
    compensate_ancuti2018,
    compensate_c3,
    effective_alphas,
)
from clearwater.methods.fusion import fusion_inputs, normalisation_bounds, weight_maps
from clearwater.methods.schema import ANCUTI2018_PARAMETERS, C3_PARAMETERS
from clearwater.methods.white_balance import applied_gains, apply_white_balance
from prototype.params import Params

COLOR = ColorDescription("bt709", "bt709", "bt709", "full", 8, False, None)
METHOD_IDS = ("c3", "ancuti2018")
# Parameters that make the spatial steps reach several pixels on the small test images.
WIDE = {
    "sharpen_blur_fraction": 0.03,
    "laplacian_fraction": 0.02,
    "saliency_blur_fraction": 0.03,
    "pyramid_min_level_size": 4,
}
SPATIAL = (
    "c3_kernel_fraction",
    "c3_mask_smooth_fraction",
    "sharpen_blur_fraction",
    "laplacian_fraction",
    "saliency_blur_fraction",
)


# -- helpers ---------------------------------------------------------------------------------------


def method(method_id: str) -> AncutiFusionMethod:
    return AncutiFusionMethod("c3" if method_id == "c3" else "ancuti2018")


def scene(shape: tuple[int, int] = (48, 72), seed: int = 0) -> np.ndarray:
    """A textured green scene in [0, 1]: weak red, blue below green, and a highlight."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]].astype(np.float32)
    texture = 0.5 + 0.25 * np.sin(x / 3.0) * np.cos(y / 4.0)
    image = np.empty((*shape, 3), dtype=np.float32)
    image[..., 0] = 0.08 + 0.1 * texture
    image[..., 1] = 0.4 + 0.3 * texture
    image[..., 2] = 0.25 + 0.2 * texture
    image += rng.normal(0.0, 0.02, image.shape).astype(np.float32)
    image[:4, :6] = 0.95  # a highlight 3C's mask protects
    return np.clip(image, 0.0, 1.0).astype(np.float32)


def as_image(pixels: Any, backend: CoreBackend | None = None) -> Image:
    backend = NumpyBackend() if backend is None else backend
    return Image(
        pixels=backend.asarray(pixels),
        device=backend.device,
        color=COLOR,
        orientation_applied=True,
    )


def analyze_all(
    m: CorrectionMethod, image: Image, params: Mapping[str, Any]
) -> dict[str, Statistics]:
    """Every stage in order on the frame's own raw earlier records (``measure_statistics``)."""
    records: dict[str, Statistics] = {}
    for stage in m.stages:
        records[stage.name] = m.analyze(stage.name, image, params, dict(records))
    return records


def host(a: Any) -> np.ndarray:
    return a.get() if hasattr(a, "get") else np.asarray(a)


def values_of(m: CorrectionMethod, **overrides: Any) -> dict[str, Any]:
    values = {p.name: p.default for p in m.parameters}
    values.update(overrides)
    return values


def same(a: Mapping[str, Any], b: Mapping[str, Any]) -> bool:
    """Whether two records hold the same names and bit-identical values."""
    return set(a) == set(b) and all(
        np.asarray(a[k]).tobytes() == np.asarray(b[k]).tobytes() for k in a
    )


@pytest.fixture
def gpu() -> CoreBackend:
    backend, reason = _probe_gpu()
    if backend is None:
        pytest.skip(reason)
    return backend


@pytest.fixture(params=["numpy", pytest.param("cupy", marks=pytest.mark.gpu)])
def backend(request: pytest.FixtureRequest) -> CoreBackend:
    if request.param == "numpy":
        return NumpyBackend()
    gpu_backend, reason = _probe_gpu()
    if gpu_backend is None:
        pytest.skip(reason)
    return gpu_backend


# -- IF conformance and the registry ---------------------------------------------------------------


def test_registry_c3_first_new_instances() -> None:
    first, second = available_methods(), available_methods()
    assert list(first) == ["c3", "ancuti2018"]
    for method_id, m in first.items():
        assert isinstance(m, CorrectionMethod)
        assert m.id == method_id
        assert m is not second[method_id]
    assert (first["c3"].label, first["ancuti2018"].label) == ("3C", "Ancuti 2018")


def test_unknown_method_id_refused() -> None:
    with pytest.raises(ValueError, match="ancuti2018-blue"):
        AncutiFusionMethod("ancuti2018-blue")  # type: ignore[arg-type]


def test_c3_stages_equal_the_frozen_stub() -> None:
    assert method("c3").stages == C3_STAGES


def test_ancuti_stage_table() -> None:
    stages = {s.name: s for s in method("ancuti2018").stages}
    assert [s.name for s in method("ancuti2018").stages] == [
        "compensation",
        "white_balance",
        "fusion",
    ]
    comp, wb, fusion = stages["compensation"], stages["white_balance"], stages["fusion"]
    assert comp.statistics == ("means", "cap_statistics", "alpha")
    assert comp.smoothed == ("means", "alpha")
    assert set(comp.depends_on_parameters) == {
        "alpha",
        "blue_compensation",
        "red_gain_cap",
        "blue_gain_cap",
    }
    assert comp.depends_on_stages == () and comp.source_only
    assert (wb.statistics, wb.smoothed) == (("means", "gains"), ("means", "gains"))
    assert wb.depends_on_parameters == () and wb.depends_on_stages == ("compensation",)
    assert not wb.source_only
    c3_fusion = C3_STAGES[1]
    assert fusion.statistics == c3_fusion.statistics and fusion.smoothed == c3_fusion.smoothed
    assert fusion.depends_on_parameters == c3_fusion.depends_on_parameters
    assert fusion.depends_on_stages == ("compensation", "white_balance")
    assert not fusion.source_only
    # exactly one source-only stage overall (Y-1 e)
    assert [s.name for s in (*C3_STAGES, *stages.values()) if s.source_only] == ["compensation"]


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_analyze_returns_every_declared_name_as_float64_host_arrays(method_id: str) -> None:
    m = method(method_id)
    records = analyze_all(m, as_image(scene()), WIDE)
    for stage in m.stages:
        record = records[stage.name]
        assert tuple(record) == stage.statistics
        for name, value in record.items():
            assert type(value) is np.ndarray and value.dtype == np.float64, (stage.name, name)
            assert value.shape == af.STATISTIC_SHAPES[name]
            assert np.isfinite(value).all()
        assert set(stage.smoothed) <= set(stage.statistics)


# -- dependencies: every parameter that changes a stage's statistics is declared -------------------

# A second valid value per parameter, chosen to change what it governs on ``scene()``.
OTHER_VALUE: dict[str, Any] = {
    "alpha": 0.4,
    "c3_strength": 0.5,
    "blue_compensation": True,
    "white_balance_strength": 0.5,
    "sharpen_strength": 0.5,
    "blend_with_original": 40.0,
    "red_gain_cap": 0.05,
    "blue_gain_cap": 0.01,
    "kappa": 0.3,
    "lambda_": 2.0,
    "max_white_balance_gain": 1.0,
    "gamma": 2.5,
    "pyramid_min_level_size": 2,
    "c3_kernel_fraction": 0.2,
    "c3_mask_threshold": 0.3,
    "c3_mask_smooth_fraction": 0.08,
    "sharpen_blur_fraction": 0.01,
    "normalisation_low": 10.0,
    "normalisation_high": 80.0,
    "laplacian_fraction": 0.005,
    "saliency_blur_fraction": 0.01,
    "weight_delta": 0.5,
}


def upstream_parameters(m: CorrectionMethod, stage_name: str) -> set[str]:
    """The parameters of every stage ``stage_name`` depends on, transitively."""
    stages = {s.name: s for s in m.stages}
    found: set[str] = set()
    pending = list(stages[stage_name].depends_on_stages)
    while pending:
        earlier = stages[pending.pop()]
        found.update(earlier.depends_on_parameters)
        pending.extend(earlier.depends_on_stages)
    return found


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_dependencies_are_complete(method_id: str) -> None:
    """With the earlier records fixed, every declared parameter changes its stage, and a
    parameter that changes a stage is declared by it or by a stage it depends on; the
    render-only parameters change no stage."""
    m = method(method_id)
    image = as_image(scene((64, 96)))
    base_params = {**WIDE, "blue_compensation": True} if method_id == "ancuti2018" else WIDE
    base = analyze_all(m, image, base_params)
    every_stage = {n for st in m.stages for n in st.depends_on_parameters}
    render_only = {p.name for p in m.parameters} - every_stage
    assert render_only == {
        "laplacian_fraction",
        "saliency_blur_fraction",
        "weight_delta",
        "pyramid_min_level_size",
        "blend_with_original",
    }
    for parameter in m.parameters:
        changed_params = {**base_params, parameter.name: OTHER_VALUE[parameter.name]}
        if parameter.name == "blue_compensation":
            changed_params[parameter.name] = False
        for stage in m.stages:
            earlier = {s: base[s] for s in stage.depends_on_stages}
            changed = not same(
                m.analyze(stage.name, image, changed_params, earlier), base[stage.name]
            )
            if parameter.name in stage.depends_on_parameters:
                assert changed, ("declared but no effect", parameter.name, stage.name)
            elif changed:  # only through a stage it depends on (the transitive convention)
                assert parameter.name in upstream_parameters(m, stage.name), (
                    "undeclared",
                    parameter.name,
                    stage.name,
                )


# -- V1: staged ordering ---------------------------------------------------------------------------


def check_stage_uses_supplied_earlier(m: CorrectionMethod) -> None:
    """Each later stage measures the image corrected with the SUPPLIED earlier records."""
    backend = NumpyBackend()
    pixels = scene()
    image = as_image(pixels)
    own = analyze_all(m, image, WIDE)
    values = values_of(m, **WIDE)
    altered: dict[str, dict[str, np.ndarray]] = {}
    if m.id == "ancuti2018":
        altered["compensation"] = {
            "means": own["compensation"]["means"] * np.array([0.5, 1.1, 1.0]),
            "cap_statistics": np.asarray(own["compensation"]["cap_statistics"]).copy(),
            "alpha": np.array([1.7, 0.0]),
        }
        compensated = compensate_ancuti2018(
            backend,
            pixels,
            means=altered["compensation"]["means"].tolist(),
            alphas={"red": 1.7},
        )
    else:
        compensated = compensate_c3(
            backend, pixels, **{k: values[k] for k in compensation_kwargs_c3()}
        )
    earlier = {"compensation": altered["compensation"]} if m.id == "ancuti2018" else {}
    wb = m.analyze("white_balance", image, WIDE, earlier)
    expected_means = compensated.reshape(-1, 3).mean(axis=0, dtype=np.float64)
    assert np.array_equal(wb["means"], expected_means), "white balance not on the supplied record"
    altered["white_balance"] = {"means": wb["means"], "gains": np.array([1.6, 0.8, 0.9])}
    fusion = m.analyze(
        "fusion", image, WIDE, {**earlier, "white_balance": altered["white_balance"]}
    )
    gains, _ = applied_gains(
        [1.6, 0.8, 0.9], white_balance_strength=1.0, max_white_balance_gain=3.0
    )
    balanced = apply_white_balance(backend, compensated, gains)
    bounds = normalisation_bounds(
        backend,
        balanced,
        sharpen_blur_fraction=WIDE["sharpen_blur_fraction"],
        normalisation_low=0.5,
        normalisation_high=99.5,
    )
    assert fusion["bounds"].tolist() == list(bounds), "fusion not on the supplied gains"


def compensation_kwargs_c3() -> tuple[str, ...]:
    return (
        "kappa",
        "lambda_",
        "c3_strength",
        "c3_kernel_fraction",
        "c3_mask_threshold",
        "c3_mask_smooth_fraction",
    )


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_v1_stage_measured_with_the_supplied_earlier_records(method_id: str) -> None:
    check_stage_uses_supplied_earlier(method(method_id))


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_missing_earlier_stage_refused_by_name(method_id: str) -> None:
    m = method(method_id)
    image = as_image(scene())
    own = analyze_all(m, image, {})
    for stage in m.stages:
        for missing in stage.depends_on_stages:
            earlier = {s: own[s] for s in stage.depends_on_stages if s != missing}
            with pytest.raises(KeyError, match=repr(missing)):
                m.analyze(stage.name, image, {}, earlier)


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_unknown_stage_and_unknown_earlier_key_refused(method_id: str) -> None:
    m = method(method_id)
    image = as_image(scene())
    with pytest.raises(ValueError, match="unknown stage 'sharpening'"):
        m.analyze("sharpening", image, {}, {})
    with pytest.raises(ValueError, match="unknown stage 'sharpening'"):
        m.closed_form("sharpening", {}, {}, {})
    with pytest.raises(ValueError, match="'flicker', which is not a stage"):
        m.analyze(m.stages[0].name, image, {}, {"flicker": {}})
    if method_id == "c3":
        with pytest.raises(ValueError, match="'compensation', which is not a stage"):
            m.analyze("white_balance", image, {}, {"compensation": {}})


# -- Y-2: supplied records are checked -------------------------------------------------------------


def broken_records(record: Mapping[str, Any], names: tuple[str, ...]) -> Iterator[tuple[str, Any]]:
    """(the statistic named in the error, a broken copy of ``record``)."""
    first = names[0]
    yield first, {k: v for k, v in record.items() if k != first}
    yield "surplus", {**record, "surplus": np.zeros(3)}
    for name in names:
        value = np.asarray(record[name])
        yield name, {**record, name: np.zeros(value.size + 1)}
        bad = value.astype(np.float64).copy()
        bad.flat[0] = math.nan
        yield name, {**record, name: bad}
        bad = value.astype(np.float64).copy()
        bad.flat[-1] = math.inf
        yield name, {**record, name: bad}
        yield name, {**record, name: "not numbers"}
        too_large = value.astype(np.float64).astype(object)
        too_large.flat[0] = 10**400  # no float holds it: OverflowError inside np.array (R1 F1)
        yield name, {**record, name: too_large.tolist()}


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_y2_render_and_analyze_refuse_a_record_that_does_not_fit(method_id: str) -> None:
    m = method(method_id)
    image = as_image(scene())
    own = analyze_all(m, image, {})
    for stage in m.stages:
        for statistic, record in broken_records(own[stage.name], stage.statistics):
            pattern = rf"stage '{stage.name}': statistic '{statistic}'"
            with pytest.raises(ValueError, match=pattern):
                m.render(image, {}, {**own, stage.name: record})
            later = [s for s in m.stages if stage.name in s.depends_on_stages]
            for consumer in later:
                earlier = {s: own[s] for s in consumer.depends_on_stages}
                earlier[stage.name] = record
                with pytest.raises(ValueError, match=pattern):
                    m.analyze(consumer.name, image, {}, earlier)
            with pytest.raises(ValueError, match=pattern):
                m.closed_form(stage.name, {}, {}, record)


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_render_refuses_a_missing_stage(method_id: str) -> None:
    m = method(method_id)
    image = as_image(scene())
    own = analyze_all(m, image, {})
    for stage in m.stages:
        with pytest.raises(KeyError, match=repr(stage.name)):
            m.render(image, {}, {k: v for k, v in own.items() if k != stage.name})


def test_records_accept_lists_and_float32_arrays() -> None:
    m = method("c3")
    image = as_image(scene())
    own = analyze_all(m, image, {})
    as_lists = {s: {k: np.asarray(v).tolist() for k, v in r.items()} for s, r in own.items()}
    reference = host(m.render(image, {}, own).pixels)
    assert host(m.render(image, {}, as_lists).pixels).tobytes() == reference.tobytes()


# -- closed form (AD-7, Y-1 d) ---------------------------------------------------------------------

CLOSED_FORM_SETS: list[dict[str, Any]] = [
    {},
    {"alpha": 0.3},
    {"blue_compensation": True},
    {"blue_compensation": True, "red_gain_cap": 0.05, "blue_gain_cap": 0.01},
    {"red_gain_cap": None, "blue_gain_cap": None, "blue_compensation": True, "alpha": 2.0},
    {"alpha": 0.0, "red_gain_cap": 0.0},
]


def check_closed_form_equals_reanalysis(m: CorrectionMethod) -> None:
    image = as_image(scene())
    for stage in m.stages:
        for params in CLOSED_FORM_SETS if m.id == "ancuti2018" else [{}]:
            earlier = analyze_all(m, image, params)
            measured = earlier[stage.name]
            # the record measured under OTHER parameters, brought to these by the closed form
            stale = analyze_all(m, image, {"alpha": 1.0} if m.id == "ancuti2018" else {})
            result = m.closed_form(stage.name, params, {}, stale[stage.name])
            if not stage.source_only:
                assert result is None, stage.name
                continue
            assert result is not None
            assert same(result, measured), (stage.name, params)


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_closed_form_equals_reanalysis_bit_for_bit(method_id: str) -> None:
    check_closed_form_equals_reanalysis(method(method_id))


def test_closed_form_alpha_follows_the_parameters() -> None:
    m = method("ancuti2018")
    record = m.analyze("compensation", as_image(scene()), {}, {})
    means, caps = record["means"].tolist(), record["cap_statistics"]
    for params in CLOSED_FORM_SETS:
        updated = m.closed_form("compensation", params, {}, record)
        assert updated is not None
        values = values_of(m, **params)
        expected = effective_alphas(
            means=means,
            cap_statistics={"red": float(caps[0]), "blue": float(caps[1])},
            alpha=values["alpha"],
            blue_compensation=values["blue_compensation"],
            red_gain_cap=values["red_gain_cap"],
            blue_gain_cap=values["blue_gain_cap"],
        )
        assert updated["alpha"].tolist() == [expected["red"], expected.get("blue", 0.0)]
        assert same({"m": updated["means"]}, {"m": record["means"]})
        assert updated["means"] is not record["means"]  # a new record, not the caller's arrays


def test_dr40a_np_float_alpha_reaches_the_result() -> None:
    """DR-40 (a): the early ``float(alpha)`` in ``effective_alphas`` is what this pins.

    Cap None: alpha (an ``np.float64``) reaches the result unchanged as a Python float. A
    binding cap within float32 rounding below ``alpha=np.float32(1.0)``: with the early cast,
    ``min`` compares in float64 and keeps the cap's value; without it (NEP 50) the comparison
    runs in float32 and returns 1.0 (round-0 probe P-2).
    """
    means = (0.1, 0.5, 0.4)
    uncapped = effective_alphas(
        means=means,
        cap_statistics={"red": 0.3},
        alpha=np.float64(0.7),
        blue_compensation=False,
        red_gain_cap=None,
        blue_gain_cap=None,
    )
    assert type(uncapped["red"]) is float and uncapped["red"] == 0.7
    cap = (1 - 1e-9) / (0.1 / 0.12)  # added_per_alpha = 0.4 * 0.3 = 0.12
    capped = effective_alphas(
        means=means,
        cap_statistics={"red": 0.3},
        alpha=np.float32(1.0),
        blue_compensation=False,
        red_gain_cap=cap,
        blue_gain_cap=None,
    )
    assert type(capped["red"]) is float
    assert capped["red"] == cap * 0.1 / ((0.5 - 0.1) * 0.3) and capped["red"] < 1.0
    # the planted defect: the comparison made with the float32 alpha
    assert float(min(np.float32(1.0), cap * 0.1 / ((0.5 - 0.1) * 0.3))) == 1.0


# -- render (10.1, AD-4, D99, AD-8) ----------------------------------------------------------------


def composed_render(
    m: CorrectionMethod, pixels: np.ndarray, params: Mapping[str, Any], records: Any
) -> np.ndarray:
    """The render rebuilt from the WP3.2/WP3.3 steps, independently of the method's code."""
    backend = NumpyBackend()
    values = values_of(m, **params)
    if m.id == "c3":
        compensated = compensate_c3(
            backend, pixels, **{k: values[k] for k in compensation_kwargs_c3()}
        )
    else:
        record = records["compensation"]
        alphas = {"red": float(record["alpha"][0])}
        if values["blue_compensation"]:
            alphas["blue"] = float(record["alpha"][1])
        compensated = compensate_ancuti2018(
            backend, pixels, means=list(map(float, record["means"])), alphas=alphas
        )
    gains, _ = applied_gains(
        list(map(float, records["white_balance"]["gains"])),
        white_balance_strength=values["white_balance_strength"],
        max_white_balance_gain=values["max_white_balance_gain"],
    )
    balanced = apply_white_balance(backend, compensated, gains)
    inputs = fusion_inputs(
        backend,
        balanced,
        gamma=values["gamma"],
        sharpen_strength=values["sharpen_strength"],
        sharpen_blur_fraction=values["sharpen_blur_fraction"],
        bounds=[float(b) for b in records["fusion"]["bounds"]],
    )
    weights = weight_maps(
        backend,
        inputs,
        laplacian_fraction=values["laplacian_fraction"],
        saliency_blur_fraction=values["saliency_blur_fraction"],
        weight_delta=values["weight_delta"],
        saliency_means=np.asarray(records["fusion"]["saliency_means"]).tolist(),
    )
    from clearwater.methods.fusion import multiscale_fusion

    fused = multiscale_fusion(
        backend, inputs, weights, pyramid_min_level_size=values["pyramid_min_level_size"]
    )
    b = values["blend_with_original"] / 100.0
    return ((1.0 - b) * fused + b * pixels).astype(np.float32)


def smoothed_like(m: CorrectionMethod, own: Mapping[str, Statistics]) -> dict[str, Any]:
    """A record set that differs from the frame's own, as smoothed values do."""
    out: dict[str, Any] = {
        s: {k: np.asarray(v).copy() for k, v in r.items()} for s, r in own.items()
    }
    out["white_balance"]["gains"] = np.array([4.5, 0.9, 1.2])  # red above the D99 clamp
    out["fusion"]["bounds"] = out["fusion"]["bounds"] + np.array([-0.01, 0.02])
    out["fusion"]["saliency_means"] = out["fusion"]["saliency_means"] + 1.5
    if m.id == "ancuti2018":
        out["compensation"]["means"] = out["compensation"]["means"] * np.array([0.9, 1.0, 1.05])
        out["compensation"]["alpha"] = np.array([0.37, 0.61])  # not the closed form of the means
    return out


def check_render_from_supplied_records(m: CorrectionMethod) -> None:
    """Render is the step composition on the SUPPLIED records: alpha, clamp, bounds, means."""
    pixels = scene()
    image = as_image(pixels)
    for params in ({**WIDE}, {**WIDE, "blue_compensation": True, "blend_with_original": 30.0}):
        if m.id == "c3":
            params.pop("blue_compensation", None)
        records = smoothed_like(m, analyze_all(m, image, params))
        got = host(m.render(image, params, records).pixels)
        expected = composed_render(m, pixels, params, records)
        assert got.tobytes() == expected.tobytes(), params


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_render_uses_the_supplied_records(method_id: str) -> None:
    check_render_from_supplied_records(method(method_id))


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_render_output_type_device_and_range(method_id: str, backend: CoreBackend) -> None:
    m = method(method_id)
    image = as_image(scene(), backend)
    records = analyze_all(m, image, WIDE)
    out = m.render(image, WIDE, records)
    assert type(out) is Image and out.device == image.device and out.color is image.color
    assert out.orientation_applied == image.orientation_applied
    assert type(out.pixels) is type(image.pixels) and out.pixels.dtype == np.float32
    assert out.pixels.shape == image.pixels.shape
    pixels = host(out.pixels)
    assert float(pixels.min()) >= 0.0 and float(pixels.max()) <= 1.0
    frame = Frame(
        pixels=image.pixels,
        device=image.device,
        color=COLOR,
        orientation_applied=True,
        pts=Fraction(1001, 30000),
        pts_ticks=1001,
        time_base=Fraction(1, 30000),
        index=1,
    )
    rendered = m.render(frame, WIDE, records)
    assert type(rendered) is Frame and rendered.pts_ticks == 1001
    assert host(rendered.pixels).tobytes() == pixels.tobytes()


def check_blend_direction(m: CorrectionMethod) -> None:
    pixels = scene()
    image = as_image(pixels)
    records = analyze_all(m, image, WIDE)
    fused = host(m.render(image, {**WIDE, "blend_with_original": 0.0}, records).pixels)
    original = host(m.render(image, {**WIDE, "blend_with_original": 100.0}, records).pixels)
    half = host(m.render(image, {**WIDE, "blend_with_original": 50}, records).pixels)
    assert original.tobytes() == pixels.tobytes(), "100 % is the original"
    assert not np.array_equal(fused, pixels), "0 % is the corrected image"
    expected_half = (0.5 * fused + 0.5 * pixels).astype(np.float32)
    assert half.tobytes() == expected_half.tobytes()


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_blend_with_original_direction_and_percent(method_id: str) -> None:
    check_blend_direction(method(method_id))


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_device_and_pixels_must_agree(method_id: str) -> None:
    m = method(method_id)
    good = as_image(scene())
    records = analyze_all(m, good, {})
    with pytest.raises(ValueError, match="no backend for device 'cuda:9'"):
        m.render(dataclasses.replace(good, device="cuda:9"), {}, records)
    with pytest.raises(ValueError, match="no backend for device 'tpu'"):
        m.analyze(m.stages[0].name, dataclasses.replace(good, device="tpu"), {}, {})
    with pytest.raises(ValueError, match="float32"):
        m.render(dataclasses.replace(good, pixels=good.pixels.astype(np.float64)), {}, records)
    with pytest.raises(ValueError, match="H, W >= 1"):
        m.render(dataclasses.replace(good, pixels=np.zeros((0, 4, 3), np.float32)), {}, records)


@pytest.mark.gpu
def test_host_pixels_on_a_gpu_image_refused(gpu: CoreBackend) -> None:
    m = method("c3")
    image = as_image(scene())
    records = analyze_all(m, image, {})
    with pytest.raises(TypeError, match="cupy"):
        m.render(dataclasses.replace(image, device=gpu.device), {}, records)
    gpu_image = as_image(scene(), gpu)
    with pytest.raises(TypeError, match="numpy"):
        m.render(dataclasses.replace(gpu_image, device="cpu"), {}, records)


# -- host reads per frame (DR-38 a) and the device-resident render (Gate 1) ------------------------


class ReadCounter:
    """Counts the measuring steps' host reads: ``channel_means``, ``mean`` and ``to_host``."""

    def __init__(self, monkeypatch: pytest.MonkeyPatch, backend: CoreBackend) -> None:
        self.count = 0
        self.monkeypatch = monkeypatch
        self.allow: Callable[[], Any] | None = None
        for module, name in (
            (af, "channel_means"),
            (fusion_module, "channel_means"),
            (compensation_module, "mean"),
        ):
            monkeypatch.setattr(module, name, self.wrap(getattr(module, name)))
        monkeypatch.setattr(backend, "to_host", self.wrap(backend.to_host))

    def wrap(self, function: Callable[..., Any]) -> Callable[..., Any]:
        def wrapped(*args: Any, **kwargs: Any) -> Any:
            self.count += 1
            if self.allow is None:
                return function(*args, **kwargs)
            with self.allow():
                return function(*args, **kwargs)

        return wrapped


EXPECTED_READS = {
    "ancuti2018": {"compensation": 3, "white_balance": 1, "fusion": 3},
    "c3": {"white_balance": 1, "fusion": 3},
}


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_dr38a_host_reads_counted_per_stage_and_none_in_render(
    method_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    m = method(method_id)
    backend = backend_for("cpu")
    image = as_image(scene(), backend)
    records = analyze_all(m, image, {"blue_compensation": True} if method_id != "c3" else {})
    counter = ReadCounter(monkeypatch, backend)
    for stage in m.stages:
        counter.count = 0
        earlier = {s: records[s] for s in stage.depends_on_stages}
        m.analyze(stage.name, image, {}, earlier)
        assert counter.count == EXPECTED_READS[method_id][stage.name], stage.name
    counter.count = 0
    m.render(image, {}, records)
    assert counter.count == 0
    assert sum(EXPECTED_READS[method_id].values()) == (7 if method_id == "ancuti2018" else 4)


@pytest.mark.gpu
@pytest.mark.filterwarnings("ignore:cupyx.allow_synchronize will be removed")
@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_gpu_reads_only_at_the_counted_points_and_render_reads_nothing(
    method_id: str, gpu: CoreBackend, monkeypatch: pytest.MonkeyPatch
) -> None:
    import cupyx

    m = method(method_id)
    image = as_image(scene((64, 96)), gpu)
    records = analyze_all(m, image, WIDE)
    with cupyx.allow_synchronize(False):
        out = m.render(image, WIDE, records)  # a host read here raises DeviceSynchronized
    assert out.pixels.dtype == np.float32
    counter = ReadCounter(monkeypatch, gpu)
    counter.allow = lambda: cupyx.allow_synchronize(True)
    for stage in m.stages:
        counter.count = 0
        earlier = {s: records[s] for s in stage.depends_on_stages}
        with cupyx.allow_synchronize(False):  # any read outside the counted points raises
            again = m.analyze(stage.name, image, WIDE, earlier)
        assert same(again, records[stage.name])
        assert counter.count == EXPECTED_READS[method_id][stage.name], stage.name


# -- DR-38 (b): grey inputs give every weight 1/K --------------------------------------------------


@pytest.mark.parametrize("method_id", METHOD_IDS)
@pytest.mark.parametrize("level", [0.0, 1.0])
def test_dr38b_all_black_and_all_white_weights_are_one_half(
    method_id: str, level: float, monkeypatch: pytest.MonkeyPatch
) -> None:
    m = method(method_id)
    image = as_image(np.full((24, 40, 3), level, np.float32))
    records = analyze_all(m, image, {})
    captured: list[tuple[Any, ...]] = []

    def capture(*args: Any, **kwargs: Any) -> tuple[Any, ...]:
        weights = weight_maps(*args, **kwargs)
        captured.append(weights)
        return weights

    monkeypatch.setattr(af, "weight_maps", capture)
    out = host(m.render(image, {}, records).pixels)
    (weights,) = captured
    assert len(weights) == 2
    for w in weights:
        assert np.abs(host(w) - 0.5).max() <= 1e-6, float(np.abs(host(w) - 0.5).max())
    assert np.isfinite(out).all() and float(np.ptp(out)) <= 1e-6  # a flat input stays flat


# -- schema (6.7, D17, D49, AD-8, DR-13, DR-19) ----------------------------------------------------

PROTOTYPE_DEFAULTS = Params()
NEUTRAL = Params.neutral()
BASIC = {
    "c3": {"c3_strength", "white_balance_strength", "sharpen_strength", "blend_with_original"},
    "ancuti2018": {
        "alpha",
        "blue_compensation",
        "white_balance_strength",
        "sharpen_strength",
        "blend_with_original",
    },
}
ANCUTI_ONLY = {"alpha", "blue_compensation", "red_gain_cap", "blue_gain_cap"}
C3_ONLY = {
    "kappa",
    "lambda_",
    "c3_strength",
    "c3_kernel_fraction",
    "c3_mask_threshold",
    "c3_mask_smooth_fraction",
}


def ad8_value(name: str, params: Params) -> Any:
    """The prototype value of a schema parameter; the blend is the schema's percent."""
    value = getattr(params, name)
    return value * 100.0 if name == "blend_with_original" else value


def check_schema(method_id: str, parameters: tuple[Parameter, ...]) -> None:
    names = [p.name for p in parameters]
    assert len(names) == len(set(names))
    prototype_fields = {f.name for f in dataclasses.fields(Params)} - {"method"}
    if method_id == "c3":
        assert set(names) == prototype_fields - ANCUTI_ONLY, "c3 holds exactly its parameters"
        assert not {n for n in names if n.endswith("_gain_cap")}, "D49: no cap in c3"
    else:
        assert set(names) == prototype_fields - C3_ONLY
    for p in parameters:
        assert p.default == ad8_value(p.name, PROTOTYPE_DEFAULTS), f"AD-8 default of {p.name}"
        assert type(p.default) is type(ad8_value(p.name, PROTOTYPE_DEFAULTS)), p.name
        assert p.neutral == ad8_value(p.name, NEUTRAL), f"V9 neutral of {p.name}"
        assert p.panel == ("basic" if p.name in BASIC[method_id] else "advanced"), p.name
        assert p.label and p.help and p.label.isascii() and p.help.isascii(), p.name
        assert p.nullable == p.name.endswith("_gain_cap"), p.name
        if p.type in ("float", "int"):
            assert p.minimum is not None and p.maximum is not None, p.name
            assert math.isfinite(p.minimum) and math.isfinite(p.maximum), p.name
            assert p.minimum <= p.default <= p.maximum, p.name  # type: ignore[operator]
            assert p.minimum <= p.neutral <= p.maximum, p.name  # type: ignore[operator]
        else:
            assert (p.type, p.minimum, p.maximum, p.choices) == ("bool", None, None, None)


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_schema_against_6_7_d17_d49_and_ad8(method_id: str) -> None:
    check_schema(method_id, method(method_id).parameters)
    assert {p.name: p.panel for p in method(method_id).parameters}["laplacian_fraction"] == (
        "advanced"
    )  # DR-13: placement only


def test_schema_spot_values() -> None:
    schema = {p.name: p for p in ANCUTI2018_PARAMETERS}
    blend = schema["blend_with_original"]
    assert (blend.minimum, blend.maximum, blend.label) == (0.0, 100.0, "Blend with original (%)")
    assert schema["max_white_balance_gain"].minimum == 1.0
    assert schema["laplacian_fraction"].default == 0.001
    assert schema["red_gain_cap"].nullable and schema["red_gain_cap"].minimum == 0.0
    c3 = {p.name: p for p in C3_PARAMETERS}
    assert c3["gamma"].neutral == 1.0 and c3["gamma"].minimum > 0.0
    assert c3["pyramid_min_level_size"].type == "int"
    assert [p.panel for p in C3_PARAMETERS].index("advanced") == 4  # Basic first


def parameter_set(method_id: str, parameters: Mapping[str, Any]) -> ParameterSet:
    from datetime import UTC, datetime

    return ParameterSet(
        method=method_id,
        parameters=dict(parameters),
        created=datetime(2026, 10, 21, tzinfo=UTC),
        app_version="test",
    )


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_defaults_neutral_partial_and_extremes_are_valid(method_id: str) -> None:
    """DR-19 (5): legal values, the inclusive bounds and large legal values are accepted."""
    m = method(method_id)
    defaults = {p.name: p.default for p in m.parameters}
    neutral = {p.name: p.neutral for p in m.parameters}
    lows = {p.name: p.minimum for p in m.parameters if p.minimum is not None}
    highs = {p.name: p.maximum for p in m.parameters if p.maximum is not None}
    lows["normalisation_high"] = 1.0  # the one relation: low < high
    highs["normalisation_low"] = 99.0
    for values in (defaults, neutral, {}, {"gamma": 2}, lows, highs):
        assert validate_parameter_set(parameter_set(m.id, values), m.id, m.parameters) == []
    image = as_image(scene((20, 30)))
    for values in (lows, highs):
        int_values = {k: int(v) if k == "pyramid_min_level_size" else v for k, v in values.items()}
        out = host(m.render(image, int_values, analyze_all(m, image, int_values)).pixels)
        assert np.isfinite(out).all() and out.min() >= 0.0 and out.max() <= 1.0


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_every_bound_refused_with_one_error_naming_the_parameter(method_id: str) -> None:
    m = method(method_id)
    image = as_image(scene((20, 30)))
    records = analyze_all(m, image, {})
    for p in m.parameters:
        if p.minimum is None:
            continue
        assert p.maximum is not None
        step = 1 if p.type == "int" else max(abs(p.maximum), 1.0) * 1e-9
        for bad in (p.minimum - step, p.maximum + step, math.nan, math.inf, -math.inf):
            if p.type == "int" and not (isinstance(bad, int) or math.isfinite(bad)):
                continue
            params = {p.name: int(bad) if p.type == "int" else bad}
            first = m.stages[0].name
            pattern = rf"^{m.id}: {p.name}: "
            with pytest.raises(ValueError, match=pattern):
                m.analyze(first, image, params, {})
            with pytest.raises(ValueError, match=pattern):
                m.render(image, params, records)
            with pytest.raises(ValueError, match=pattern):
                m.closed_form(first, params, {}, records[first])


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_types_and_unknown_names_refused(method_id: str) -> None:
    """DR-19 (5): every float takes an int (as a float), no parameter is special-cased."""
    m = method(method_id)
    image = as_image(scene((20, 30)))
    records = analyze_all(m, image, {})
    reference = host(m.render(image, {}, records).pixels)
    for p in m.parameters:
        if p.type == "float" and float(p.default).is_integer():  # type: ignore[arg-type]
            as_int = host(m.render(image, {p.name: int(p.default)}, records).pixels)  # type: ignore[call-overload]
            assert as_int.tobytes() == reference.tobytes(), p.name
        wrong: list[Any] = ["1", [1.0]]
        wrong += [1.5] if p.type == "int" else []
        wrong += [1] if p.type == "bool" else [True]
        wrong += [] if p.nullable else [None]
        for value in wrong:
            with pytest.raises(ValueError, match=rf"^{m.id}: {p.name}: "):
                m.render(image, {p.name: value}, records)
    other = ANCUTI_ONLY if method_id == "c3" else C3_ONLY
    for name in sorted(other):
        with pytest.raises(ValueError, match=rf"^{m.id}: unknown parameter '{name}'"):
            m.render(image, {name: 1.0}, records)


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_caps_none_and_nullable_only_in_ancuti(method_id: str) -> None:
    m = method(method_id)
    image = as_image(scene((20, 30)))
    params = {"red_gain_cap": None, "blue_gain_cap": None}
    if method_id == "c3":
        with pytest.raises(ValueError, match="unknown parameter 'red_gain_cap'"):
            m.analyze("white_balance", image, params, {})
        return
    record = m.analyze(
        "compensation", image, {**params, "alpha": 2.0, "blue_compensation": True}, {}
    )
    assert record["alpha"].tolist() == [2.0, 2.0]  # no cap: the requested alpha


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_normalisation_order_is_the_one_cross_check(method_id: str) -> None:
    m = method(method_id)
    image = as_image(scene((20, 30)))
    for low, high in ((50.0, 50.0), (60.0, 40.0), (100.0, 0.0)):
        with pytest.raises(ValueError, match=rf"^{m.id}: normalisation_low={low!r} must be below"):
            m.analyze(
                m.stages[-1].name, image, {"normalisation_low": low, "normalisation_high": high}, {}
            )


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_parameter_errors_come_before_any_array_work(method_id: str) -> None:
    m = method(method_id)
    not_pixels = dataclasses.replace(as_image(scene((4, 4))), pixels=[[0.5]])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="gamma"):
        m.render(not_pixels, {"gamma": -1.0}, {})
    with pytest.raises(ValueError, match="gamma"):
        m.analyze(m.stages[-1].name, not_pixels, {"gamma": 99.0}, {})


@pytest.mark.parametrize("name", SPATIAL)
def test_dr19_spatial_bounds_hold_at_every_size(name: str) -> None:
    """DR-19 (5): the bounds, not a size-independent rule, keep each sigma usable: 1 x 1 to
    48 MP, 5.3K included."""
    schema = {p.name: p for p in (*C3_PARAMETERS, *ANCUTI2018_PARAMETERS)}[name]
    assert schema.minimum is not None and schema.maximum is not None
    for shape in ((1, 1), (2988, 5312), (2160, 3840), (6000, 8000)):
        for fraction in (schema.minimum, schema.maximum):
            sigma = spatial_sigma(shape, fraction)
            check_sigma(sigma)
            assert sigma > 0.0
    # the largest sigma is far inside the core bound
    assert spatial_sigma((6000, 8000), schema.maximum) * 4 < 2**23


# -- the dependency rule (plan 8.1, frame rule 5) --------------------------------------------------


def test_import_loads_nothing_forbidden() -> None:
    code = (
        "import json, sys\n"
        "import clearwater.methods\n"
        "clearwater.methods.available_methods()\n"
        "top = ['PIL', 'PySide6', 'av', 'cupy', 'cupyx']\n"
        "packages = ['clearwater.io', 'clearwater.jobs', 'clearwater.gui', 'clearwater.config',\n"
        "            'clearwater.analysis']\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in top\n"
        "             or any(m == p or m.startswith(p + '.') for p in packages))\n"
        "print(json.dumps(bad))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=False
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert json.loads(result.stdout.strip().splitlines()[-1]) == []


# -- planted wrong implementations: each check above fails on its defect, by name ------------------


class StrengthBeforeSmoothing(AncutiFusionMethod):
    """Stores the APPLIED gains (strength and clamp) in the white-balance record."""

    def analyze(self, stage: str, image: Image, params: Any, earlier: Any) -> Statistics:
        record = dict(super().analyze(stage, image, params, earlier))
        if stage == "white_balance":
            values = values_of(self, **params)
            gains, _ = applied_gains(
                record["gains"].tolist(),
                white_balance_strength=values["white_balance_strength"],
                max_white_balance_gain=values["max_white_balance_gain"],
            )
            record["gains"] = np.array(gains)
        return record


class AlphaFromSmoothedMeans(AncutiFusionMethod):
    """Re-derives alpha from the record's (smoothed) means instead of using the record's alpha."""

    def _compensate(self, backend: Any, pixels: Any, values: Any, records: Any) -> Any:
        if self.id == "ancuti2018":
            record = records["compensation"]
            updated = af._compensation_record(record["means"], record["cap_statistics"], values)
            records = {**records, "compensation": updated}
        return super()._compensate(backend, pixels, values, records)


class ClampSkipped(AncutiFusionMethod):
    """Applies the strength in render but not the D99 clamp."""

    def _white_balance(self, backend: Any, compensated: Any, values: Any, record: Any) -> Any:
        unclamped = {**values, "max_white_balance_gain": 1e9}
        return super()._white_balance(backend, compensated, unclamped, record)


class UncorrectedStage(AncutiFusionMethod):
    """Measures the later stages on the uncompensated image."""

    def _compensate(self, backend: Any, pixels: Any, values: Any, records: Any) -> Any:
        return pixels.copy()


class EarlierIgnored(AncutiFusionMethod):
    """Measures the white balance on the frame's own compensation, ignoring ``earlier``."""

    def analyze(self, stage: str, image: Image, params: Any, earlier: Any) -> Statistics:
        if stage == "white_balance" and self.id == "ancuti2018":
            earlier = {"compensation": super().analyze("compensation", image, params, {})}
        return super().analyze(stage, image, params, earlier)


def planted(cls: type[AncutiFusionMethod], method_id: str) -> AncutiFusionMethod:
    return cls("c3" if method_id == "c3" else "ancuti2018")


def test_planted_strength_or_clamp_before_smoothing_fails() -> None:
    def check(m: CorrectionMethod) -> None:
        image = as_image(scene())
        params = {"white_balance_strength": 0.3, "max_white_balance_gain": 1.0}
        earlier: dict[str, Statistics] = {}
        if m.id == "ancuti2018":
            earlier["compensation"] = m.analyze("compensation", image, params, {})
        wb = m.analyze("white_balance", image, params, earlier)
        means = wb["means"].tolist()
        target = sum(means) / 3.0
        assert wb["gains"].tolist() == [target / max(v, 1e-6) for v in means]

    for method_id in METHOD_IDS:
        check(method(method_id))
        with pytest.raises(AssertionError):
            check(planted(StrengthBeforeSmoothing, method_id))


def test_planted_alpha_from_smoothed_means_fails() -> None:
    check_render_from_supplied_records(method("ancuti2018"))
    with pytest.raises(AssertionError):
        check_render_from_supplied_records(planted(AlphaFromSmoothedMeans, "ancuti2018"))


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_planted_clamp_skipped_in_render_fails(method_id: str) -> None:
    with pytest.raises(AssertionError):
        check_render_from_supplied_records(planted(ClampSkipped, method_id))


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_planted_blend_inverted_fails(method_id: str, monkeypatch: pytest.MonkeyPatch) -> None:
    original = af.blend_with_original
    monkeypatch.setattr(af, "blend_with_original", lambda f, o, p: original(f, o, 100.0 - p))
    with pytest.raises(AssertionError):
        check_blend_direction(method(method_id))


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_planted_render_measuring_the_bounds_fails(
    method_id: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    def measuring(backend: Any, a: Any, **kwargs: Any) -> Any:
        kwargs["bounds"] = normalisation_bounds(
            backend,
            a,
            sharpen_blur_fraction=kwargs["sharpen_blur_fraction"],
            normalisation_low=0.5,
            normalisation_high=99.5,
        )
        return fusion_inputs(backend, a, **kwargs)

    m = method(method_id)
    monkeypatch.setattr(af, "fusion_inputs", measuring)
    with pytest.raises(AssertionError):
        check_render_from_supplied_records(m)
    image = as_image(scene())
    records = analyze_all(m, image, WIDE)
    counter_backend = NumpyBackend()
    monkeypatch.setattr(af, "backend_for", lambda device: counter_backend)
    counter = ReadCounter(monkeypatch, counter_backend)
    m.render(image, WIDE, records)
    assert counter.count > 0  # the read the product's render never makes


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_planted_stage_on_the_uncorrected_image_fails(method_id: str) -> None:
    with pytest.raises(AssertionError):
        check_stage_uses_supplied_earlier(planted(UncorrectedStage, method_id))


def test_planted_earlier_ignored_fails() -> None:
    with pytest.raises(AssertionError):
        check_stage_uses_supplied_earlier(planted(EarlierIgnored, "ancuti2018"))


def test_planted_schema_default_and_c3_cap_fail() -> None:
    gamma_off = tuple(
        dataclasses.replace(p, default=1.4) if p.name == "gamma" else p for p in C3_PARAMETERS
    )
    with pytest.raises(AssertionError, match="AD-8 default of gamma"):
        check_schema("c3", gamma_off)
    cap = next(p for p in ANCUTI2018_PARAMETERS if p.name == "red_gain_cap")
    with pytest.raises(AssertionError, match="c3"):
        check_schema("c3", (*C3_PARAMETERS, cap))
    neutral_off = tuple(
        dataclasses.replace(p, neutral=1.0) if p.name == "sharpen_strength" else p
        for p in C3_PARAMETERS
    )
    with pytest.raises(AssertionError, match="V9 neutral of sharpen_strength"):
        check_schema("c3", neutral_off)
    laplacian_basic = tuple(
        dataclasses.replace(p, panel="basic") if p.name == "laplacian_fraction" else p
        for p in C3_PARAMETERS
    )
    with pytest.raises(AssertionError, match="laplacian_fraction"):
        check_schema("c3", laplacian_basic)


def test_planted_closed_form_from_stale_parameters_fails() -> None:
    class Stale(AncutiFusionMethod):
        def closed_form(self, stage: str, params: Any, earlier: Any, measured: Any) -> Any:
            result = super().closed_form(stage, params, earlier, measured)
            return None if result is None else dict(measured)  # alpha not recomputed

    check_closed_form_equals_reanalysis(method("ancuti2018"))
    with pytest.raises(AssertionError):
        check_closed_form_equals_reanalysis(Stale("ancuti2018"))
