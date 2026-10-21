"""WP3.4: the methods against the read-only prototype, CPU against GPU, N10 and V9 (AD-11).

The references are computed here by calling ``tools/prototype`` (WP3.1 ruling 6 form); nothing
is committed. On one device the product matches the prototype bit for bit, with two known,
ruled differences: each N{} bound is the prototype's float64 bound rounded to float32 (IF-2
``percentile``, WP3.3), and the N{} floor (AD-4, DR-14) widens bounds closer than 0.02 where the
prototype stretches only bounds closer than 1e-6. Where the floor binds (every still at the
defaults: their sharpening sigma is a third of a pixel) the prototype is given the floored
bounds, as WP3.3 compares input 2, and the match is exact again; the raw difference from the
unfloored prototype is the report's figure, not a test bound.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

from clearwater.core import CoreBackend, NumpyBackend
from clearwater.core.backend import _probe_gpu
from clearwater.interfaces.method import CorrectionMethod, Statistics
from clearwater.methods.fusion import NORMALISATION_RANGE_FLOOR, _floored
from lookcheck.frames import read_png16
from prototype import pipeline as proto
from prototype import temporal
from prototype.params import Params
from test_methods_assembly import WIDE, analyze_all, as_image, host, method, scene

METHOD_IDS = ("c3", "ancuti2018")
STILLS = [
    "png16-uniform-none",
    "png16-gradient-none",
    "png16-lowred-none",
    "png8-uniform-none",
    "png8-gradient-none",
    "png8-lowred-none",
]
AD11_MAX = 2e-3  # CPU against GPU, absolute
AD11_MEAN = 2e-4
V9_MAX = 2.0 / 255.0  # AD-11's V9 bound
V9_MEAN = 0.2 / 255.0
PARAM_SETS: dict[str, dict[str, Any]] = {
    "defaults": {},
    "wide": dict(WIDE),
    "wide-blue-capped-blend": {
        **WIDE,
        "blue_compensation": True,
        "red_gain_cap": 0.3,
        "blue_gain_cap": 0.2,
        "blend_with_original": 25.0,
        "gamma": 1.2,
    },
    "c3-tuned": {**WIDE, "c3_strength": 1.6, "kappa": 0.8, "c3_mask_threshold": 0.6},
}


def params_for(method_id: str, name: str) -> dict[str, Any]:
    params = dict(PARAM_SETS[name])
    names = {p.name for p in method(method_id).parameters}
    return {k: v for k, v in params.items() if k in names}


def prototype_params(m: CorrectionMethod, params: Mapping[str, Any]) -> Params:
    values = {p.name: p.default for p in m.parameters}
    values.update(params)
    values["blend_with_original"] = float(values["blend_with_original"]) / 100.0
    return Params(method="c3" if m.id == "c3" else "ancuti2018", **values)


def floor_binds(records: Mapping[str, Statistics]) -> bool:
    low, high = (float(b) for b in records["fusion"]["bounds"])
    return high - low < NORMALISATION_RANGE_FLOOR


@pytest.fixture
def gpu() -> CoreBackend:
    backend, reason = _probe_gpu()
    if backend is None:
        pytest.skip(reason)
    return backend


def read_still(path: Path) -> np.ndarray:
    if "png16" in path.name:
        return read_png16(path)
    with PILImage.open(path) as opened:
        return (np.asarray(opened.convert("RGB"), dtype=np.float32) / np.float32(255.0)).copy()


@pytest.fixture
def load(sample: Callable[[str], Path]) -> Callable[[str], np.ndarray]:
    def loader(name: str) -> np.ndarray:
        if name == "scene":
            return scene((64, 96))
        if name == "scene-large":
            return scene((180, 270), seed=3)
        return read_still(sample(name))

    return loader


IMAGES = ["scene", "scene-large", *STILLS]


def floored(bounds: Any) -> tuple[float, float]:
    """The bounds the product's ``fusion_inputs`` stretches over (AD-4's floor applied)."""
    return _floored(float(bounds[0]), float(bounds[1]))


def hook(m: CorrectionMethod, records: Mapping[str, Statistics], blue: bool) -> Any:
    """The product's records as the prototype's ``Statistics`` hook, the bounds floored."""
    fusion = records["fusion"]
    fields: dict[str, Any] = {
        "white_balance_gains": tuple(float(g) for g in records["white_balance"]["gains"]),
        "normalisation_bounds": floored(fusion["bounds"]),
        "saliency_means": tuple(tuple(map(float, row)) for row in fusion["saliency_means"]),
    }
    if m.id == "ancuti2018":
        comp = records["compensation"]
        alpha = {"red": float(comp["alpha"][0])}
        if blue:
            alpha["blue"] = float(comp["alpha"][1])
        fields["compensation_means"] = tuple(float(v) for v in comp["means"])
        fields["compensation_alpha"] = alpha
    return proto.Statistics(**fields)


# -- analyze against prototype.temporal.statistics_of ----------------------------------------------


@pytest.mark.parametrize("method_id", METHOD_IDS)
@pytest.mark.parametrize("set_name", list(PARAM_SETS))
@pytest.mark.parametrize("image_name", IMAGES)
def test_analyze_against_statistics_of(
    method_id: str, set_name: str, image_name: str, load: Callable[[str], np.ndarray]
) -> None:
    m = method(method_id)
    params = params_for(method_id, set_name)
    pixels = load(image_name)
    records = analyze_all(m, as_image(pixels), params)
    p = prototype_params(m, params)
    reference = temporal.statistics_of(pixels, p)
    if m.id == "ancuti2018":
        comp = records["compensation"]
        assert comp["means"].tolist() == list(reference.compensation_means)
        expected_alpha = dict(reference.compensation_alpha)
        assert comp["alpha"][0] == expected_alpha["red"]
        assert comp["alpha"][1] == expected_alpha.get("blue", 0.0)
        green = pixels[..., 1]
        for index, channel in ((0, 0), (1, 2)):
            shape = (1.0 - pixels[..., channel]) * green
            assert comp["cap_statistics"][index] == proto._cap_statistic(shape)
    wb = records["white_balance"]
    assert wb["means"].tolist() == list(reference.white_balance_means)
    assert wb["gains"].tolist() == list(reference.white_balance_gains)
    fusion = records["fusion"]
    assert fusion["bounds"].tolist() == [
        float(np.float32(b)) for b in reference.normalisation_bounds
    ]
    # the saliency means: the prototype's chain given the bounds the product stretches over
    given = dataclasses.replace(
        reference, normalisation_bounds=floored(fusion["bounds"]), saliency_means=None
    )
    again = temporal.measure(pixels, p, given)
    assert fusion["saliency_means"].tolist() == [list(v) for v in again.saliency_means]


# -- render against pipeline.correct with the same Statistics record -------------------------------


@pytest.mark.parametrize("method_id", METHOD_IDS)
@pytest.mark.parametrize("set_name", list(PARAM_SETS))
@pytest.mark.parametrize("image_name", IMAGES)
def test_render_against_correct_with_the_same_record(
    method_id: str, set_name: str, image_name: str, load: Callable[[str], np.ndarray]
) -> None:
    m = method(method_id)
    params = params_for(method_id, set_name)
    pixels = load(image_name)
    image = as_image(pixels)
    records = analyze_all(m, image, params)
    p = prototype_params(m, params)
    got = host(m.render(image, params, records).pixels)
    expected = proto.correct(pixels, p, statistics=hook(m, records, p.blue_compensation)).output
    assert got.tobytes() == expected.tobytes(), (image_name, floor_binds(records))


@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_render_from_a_smoothed_record_against_correct(method_id: str) -> None:
    """Records unlike the frame's own (as smoothing makes them) still give the prototype's
    output from the same hook record: the render takes every value from the record."""
    m = method(method_id)
    params = params_for(method_id, "wide-blue-capped-blend")
    pixels = scene((64, 96), seed=5)
    records = {s: dict(r) for s, r in analyze_all(m, as_image(scene((64, 96))), params).items()}
    records["white_balance"]["gains"] = np.array([3.4, 0.95, 1.1])
    if m.id == "ancuti2018":
        records["compensation"]["alpha"] = np.array([0.81, 0.33])
    p = prototype_params(m, params)
    got = host(m.render(as_image(pixels), params, records).pixels)
    expected = proto.correct(pixels, p, statistics=hook(m, records, p.blue_compensation)).output
    assert not floor_binds(records)
    assert got.tobytes() == expected.tobytes()


# -- CPU against GPU (AD-11) and the same device twice (N10) ---------------------------------------


@pytest.mark.gpu
@pytest.mark.parametrize("method_id", METHOD_IDS)
@pytest.mark.parametrize("image_name", ["scene-large", "png16-gradient-none", "png8-lowred-none"])
def test_cpu_against_gpu_within_ad11(
    method_id: str, image_name: str, gpu: CoreBackend, load: Callable[[str], np.ndarray]
) -> None:
    m = method(method_id)
    params = params_for(method_id, "wide")
    pixels = load(image_name)
    cpu_records = analyze_all(m, as_image(pixels), params)
    gpu_records = analyze_all(m, as_image(pixels, gpu), params)
    for stage in m.stages:
        for name in stage.statistics:
            a = np.asarray(cpu_records[stage.name][name])
            b = np.asarray(gpu_records[stage.name][name])
            scale = 100.0 if name == "saliency_means" else 1.0  # Lab units
            assert np.abs(a - b).max() <= AD11_MAX * scale, (stage.name, name)
    # the render on each device from the SAME records
    cpu_out = host(m.render(as_image(pixels), params, cpu_records).pixels).astype(np.float64)
    gpu_out = host(m.render(as_image(pixels, gpu), params, cpu_records).pixels).astype(np.float64)
    difference = np.abs(cpu_out - gpu_out)
    assert difference.max() <= AD11_MAX and difference.mean() <= AD11_MEAN


@pytest.mark.parametrize(
    "device", ["numpy", pytest.param("cupy", marks=pytest.mark.gpu)], ids=["cpu", "gpu"]
)
@pytest.mark.parametrize("method_id", METHOD_IDS)
def test_same_device_twice_is_bit_identical(method_id: str, device: str) -> None:
    backend: CoreBackend = NumpyBackend()
    if device == "cupy":
        found, reason = _probe_gpu()
        if found is None:
            pytest.skip(reason)
        backend = found
    m = method(method_id)
    pixels = scene((90, 120), seed=7)
    runs = []
    for _ in range(2):
        image = as_image(pixels, backend)
        records = analyze_all(m, image, WIDE)
        out = host(m.render(image, WIDE, records).pixels)
        runs.append((records, out))
    (first_records, first_out), (second_records, second_out) = runs
    for stage in m.stages:
        for name in stage.statistics:
            a, b = first_records[stage.name][name], second_records[stage.name][name]
            assert np.asarray(a).tobytes() == np.asarray(b).tobytes()
    assert first_out.tobytes() == second_out.tobytes()


# -- V9 at method level ----------------------------------------------------------------------------


def neutral(m: CorrectionMethod) -> dict[str, Any]:
    return {p.name: p.neutral for p in m.parameters}


@pytest.mark.parametrize(
    "device", ["numpy", pytest.param("cupy", marks=pytest.mark.gpu)], ids=["cpu", "gpu"]
)
@pytest.mark.parametrize("method_id", METHOD_IDS)
@pytest.mark.parametrize("image_name", [*STILLS, "scene-large"])
def test_v9_neutral_parameters_give_the_input(
    method_id: str, image_name: str, device: str, load: Callable[[str], np.ndarray]
) -> None:
    backend: CoreBackend = NumpyBackend()
    if device == "cupy":
        found, reason = _probe_gpu()
        if found is None:
            pytest.skip(reason)
        backend = found
    m = method(method_id)
    params = neutral(m)
    assert params["blend_with_original"] == 0.0  # the identity comes from the steps
    pixels = load(image_name)
    image = as_image(pixels, backend)
    out = host(m.render(image, params, analyze_all(m, image, params)).pixels)
    difference = np.abs(out.astype(np.float64) - pixels)
    assert difference.max() <= V9_MAX and difference.mean() <= V9_MEAN, (
        float(difference.max() * 255),
        float(difference.mean() * 255),
    )
    # blend 100 % returns the input exactly, whatever the other parameters
    image = as_image(pixels, backend)
    records = analyze_all(m, image, {})
    original = host(m.render(image, {"blend_with_original": 100.0}, records).pixels)
    assert original.tobytes() == pixels.tobytes()


def test_v9_planted_non_neutral_fails(load: Callable[[str], np.ndarray]) -> None:
    """V9's bound distinguishes: one control off its neutral value misses it."""
    m = method("c3")
    pixels = load("png16-lowred-none")
    image = as_image(pixels)
    for name, value in (("c3_strength", 0.3), ("gamma", 1.1), ("white_balance_strength", 0.3)):
        params = {**neutral(m), name: value}
        out = host(m.render(image, params, analyze_all(m, image, params)).pixels)
        assert np.abs(out.astype(np.float64) - pixels).max() > V9_MAX, name
