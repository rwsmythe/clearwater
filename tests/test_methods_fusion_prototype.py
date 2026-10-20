"""WP3.3: the fusion steps against the read-only prototype, and CPU against GPU (DR-19, AD-11).

The references are computed here by calling ``tools/prototype`` on seeded synthetic inputs and
on the WP2.3 stills; nothing is committed. With the same supplied statistics every function
must match the prototype bit for bit on the same device; input 2 is compared with the prototype
given the floored bounds, which equals the prototype on the bounds themselves whenever their
range is at least the floor. The measured path (bounds from ``percentile``, float32) is held
within AD-11 of the prototype's measured path.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

from clearwater.core import CoreBackend, NumpyBackend
from clearwater.core.backend import _probe_gpu
from clearwater.methods import fusion
from lookcheck.frames import read_png16
from prototype import pipeline as proto
from prototype.params import Params

STILLS = [
    "png16-uniform-none",
    "png16-gradient-none",
    "png16-lowred-none",
    "png8-uniform-none",
    "png8-gradient-none",
    "png8-lowred-none",
]
# The AD-8 defaults, and a set whose sigmas span several pixels at the test sizes (at 64 px
# the default sharpening sigma is 0.32 px, so the floor binds on most small inputs).
PARAMS = {
    "defaults": Params(),
    "wide": Params(
        sharpen_blur_fraction=0.05,
        laplacian_fraction=0.02,
        saliency_blur_fraction=0.03,
        pyramid_min_level_size=4,
    ),
}
# AD-11: CPU against GPU, absolute, per channel.
AD11_MAX = 2e-3
AD11_MEAN = 2e-4


@pytest.fixture(params=["numpy", pytest.param("cupy", marks=pytest.mark.gpu)])
def backend(request: pytest.FixtureRequest) -> CoreBackend:
    if request.param == "numpy":
        return NumpyBackend()
    gpu, reason = _probe_gpu()
    if gpu is None:
        pytest.skip(reason)
    return gpu


@pytest.fixture
def gpu() -> CoreBackend:
    backend, reason = _probe_gpu()
    if backend is None:
        pytest.skip(reason)
    return backend


def synthetic(seed: int, shape: tuple[int, int] = (45, 67)) -> np.ndarray:
    """Seeded noise in [0, 1]; odd seeds have a near-zero red channel."""
    image = np.random.default_rng(seed).random((*shape, 3), dtype=np.float32)
    if seed % 2:
        image[..., 0] *= np.float32(1e-3)
    return image


def scene(shape: tuple[int, int] = (96, 144)) -> np.ndarray:
    """A textured blue-green scene: smooth colour fields modulated by band-limited texture."""
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]].astype(np.float32)
    y /= shape[0]
    x /= shape[1]
    rgb = np.stack([0.08 + 0.1 * x, 0.4 + 0.3 * y, 0.5 + 0.2 * x * y], axis=2)
    texture = np.random.default_rng(7).random(shape, dtype=np.float32)
    texture = np.asarray(
        NumpyBackend().gaussian_blur(texture, 1.5) - np.float32(0.5), dtype=np.float32
    )
    return np.clip(rgb * (1.0 + 2.0 * texture[..., None]), 0.0, 1.0).astype(np.float32)


def white_balanced(image: np.ndarray) -> np.ndarray:
    """The prototype's 3C compensation and white balance (the steps before this package)."""
    params = Params()
    compensated, _ = proto.compensate_c3(image, params)
    balanced, _ = proto.white_balance(compensated, params)
    return balanced


def read_still(path: Path) -> np.ndarray:
    if "png16" in path.name:
        return read_png16(path)
    with PILImage.open(path) as opened:
        return (np.asarray(opened.convert("RGB"), dtype=np.float32) / np.float32(255.0)).copy()


IMAGES = ["synthetic-0", "synthetic-1", "scene", "scene-balanced", *STILLS]


@pytest.fixture(params=IMAGES)
def image(request: pytest.FixtureRequest, sample: Callable[[str], Path]) -> np.ndarray:
    name = request.param
    if name.startswith("synthetic"):
        return synthetic(int(name[-1]))
    if name == "scene":
        return scene()
    if name == "scene-balanced":
        return white_balanced(scene())
    return read_still(sample(name))


@pytest.fixture(params=sorted(PARAMS))
def params(request: pytest.FixtureRequest) -> Params:
    return PARAMS[request.param]


def same(product: Any, reference: Any, backend: CoreBackend, what: str) -> None:
    """Assert bit identity of a product array with a prototype array."""
    p = np.asarray(backend.to_host(product))
    r = np.asarray(reference if isinstance(reference, np.ndarray) else backend.to_host(reference))
    assert p.dtype == r.dtype == np.float32, f"{what}: dtype {p.dtype} vs {r.dtype}"
    assert p.shape == r.shape, f"{what}: shape {p.shape} vs {r.shape}"
    equal = p.tobytes() == r.tobytes()  # a bool: no byte-wise diff in pytest's message
    assert equal, f"{what}: max {float(np.abs(p.astype(np.float64) - r).max()):.3g}"


def floored(bounds: tuple[float, float]) -> tuple[float, float]:
    """The ruled floor, written out here (AD-4 as amended: widen about the midpoint)."""
    low, high = bounds
    if high - low >= 0.02:
        return low, high
    mid = (low + high) / 2.0
    return mid - 0.01, mid + 0.01


def inputs_kw(params: Params) -> dict[str, float]:
    return {
        "gamma": params.gamma,
        "sharpen_strength": params.sharpen_strength,
        "sharpen_blur_fraction": params.sharpen_blur_fraction,
    }


def weights_kw(params: Params) -> dict[str, float]:
    return {
        "laplacian_fraction": params.laplacian_fraction,
        "saliency_blur_fraction": params.saliency_blur_fraction,
        "weight_delta": params.weight_delta,
    }


def test_high_pass_and_bounds(backend: CoreBackend, image: np.ndarray, params: Params) -> None:
    a = backend.asarray(image)
    hp = fusion.high_pass(backend, a, sharpen_blur_fraction=params.sharpen_blur_fraction)
    same(hp, proto.high_pass_of(a, params), backend, "high_pass")
    bounds = fusion.normalisation_bounds(
        backend,
        a,
        sharpen_blur_fraction=params.sharpen_blur_fraction,
        normalisation_low=params.normalisation_low,
        normalisation_high=params.normalisation_high,
    )
    reference = proto.normalisation_bounds(a, params)
    # R0-8: the prototype's float64 bounds rounded to float32, exactly.
    assert bounds == tuple(float(np.float32(value)) for value in reference)
    assert all(type(value) is float for value in bounds)


def test_fusion_inputs_with_supplied_bounds(
    backend: CoreBackend, image: np.ndarray, params: Params
) -> None:
    a = backend.asarray(image)
    bounds = proto.normalisation_bounds(a, params)
    input1, input2 = fusion.fusion_inputs(backend, a, **inputs_kw(params), bounds=bounds)
    statistics = proto.Statistics(normalisation_bounds=floored(bounds))
    ref1, ref2 = proto.fusion_inputs(a, params, statistics)
    same(input1, ref1, backend, "input 1")
    same(input2, ref2, backend, "input 2")
    if bounds[1] - bounds[0] >= 0.02:  # the floor does not bind: the prototype on the bounds
        same(input2, proto.fusion_inputs(a, params)[1], backend, "input 2, unfloored")


def test_saliency_reference(backend: CoreBackend, image: np.ndarray) -> None:
    a = backend.asarray(image)
    assert fusion.saliency_reference(backend, a) == proto.saliency_reference(a)


def test_weights(backend: CoreBackend, image: np.ndarray, params: Params) -> None:
    a = backend.asarray(image)
    input1, input2 = proto.fusion_inputs(a, params)
    means = (proto.saliency_reference(input1), proto.saliency_reference(input2))
    reference = proto.weight_maps((input1, input2), params, proto.Statistics(saliency_means=means))
    for k, (x, mean) in enumerate(zip((input1, input2), means, strict=True)):
        same(
            fusion.laplacian_weight(backend, x, laplacian_fraction=params.laplacian_fraction),
            reference.laplacian[k],
            backend,
            f"W_L {k}",
        )
        same(
            fusion.saliency_weight(
                backend,
                x,
                saliency_blur_fraction=params.saliency_blur_fraction,
                saliency_mean=mean,
            ),
            reference.saliency[k],
            backend,
            f"W_S {k}",
        )
        same(fusion.saturation_weight(backend, x), reference.saturation[k], backend, f"W_Sat {k}")
    normalised = fusion.weight_maps(
        backend, (input1, input2), **weights_kw(params), saliency_means=means
    )
    assert len(normalised) == 2
    for k, w in enumerate(normalised):
        same(w, reference.normalised[k], backend, f"Wbar {k}")
    # The measured means (prototype, no hook) are the means the product is given.
    measured = proto.weight_maps((input1, input2), params)
    for k, w in enumerate(normalised):
        same(w, measured.normalised[k], backend, f"Wbar {k}, measured means")


def test_multiscale_fusion(backend: CoreBackend, image: np.ndarray, params: Params) -> None:
    a = backend.asarray(image)
    input1, input2 = proto.fusion_inputs(a, params)
    weights = proto.weight_maps((input1, input2), params).normalised
    fused = fusion.multiscale_fusion(
        backend,
        (input1, input2),
        weights,
        pyramid_min_level_size=params.pyramid_min_level_size,
    )
    same(fused, proto.multiscale_fusion((input1, input2), weights, params), backend, "fused")


def render_all(backend: CoreBackend, a: Any, params: Params) -> dict[str, Any]:
    """The product's measure-then-render chain over steps 3-5, keeping every intermediate.

    Keys: ``"bounds"`` (two floats), ``"means"`` (two Lab triples), and the arrays
    ``"high_pass"``, ``"input 1"``, ``"input 2"``, ``"W_L k"``, ``"W_S k"``, ``"W_Sat k"``,
    ``"Wbar k"`` (k = 1, 2) and ``"fused"``.
    """
    bounds = fusion.normalisation_bounds(
        backend,
        a,
        sharpen_blur_fraction=params.sharpen_blur_fraction,
        normalisation_low=params.normalisation_low,
        normalisation_high=params.normalisation_high,
    )
    out: dict[str, Any] = {
        "bounds": bounds,
        "high_pass": fusion.high_pass(
            backend, a, sharpen_blur_fraction=params.sharpen_blur_fraction
        ),
    }
    inputs = fusion.fusion_inputs(backend, a, **inputs_kw(params), bounds=bounds)
    means = [fusion.saliency_reference(backend, x) for x in inputs]
    out["means"] = means
    for k, (x, mean) in enumerate(zip(inputs, means, strict=True), start=1):
        out[f"input {k}"] = x
        out[f"W_L {k}"] = fusion.laplacian_weight(
            backend, x, laplacian_fraction=params.laplacian_fraction
        )
        out[f"W_S {k}"] = fusion.saliency_weight(
            backend, x, saliency_blur_fraction=params.saliency_blur_fraction, saliency_mean=mean
        )
        out[f"W_Sat {k}"] = fusion.saturation_weight(backend, x)
    weights = fusion.weight_maps(backend, inputs, **weights_kw(params), saliency_means=means)
    for k, w in enumerate(weights, start=1):
        out[f"Wbar {k}"] = w
    out["fused"] = fusion.multiscale_fusion(
        backend, inputs, weights, pyramid_min_level_size=params.pyramid_min_level_size
    )
    return out


ARRAY_KEYS = [
    "high_pass",
    "input 1",
    "input 2",
    *(f"{name} {k}" for k in (1, 2) for name in ("W_L", "W_S", "W_Sat", "Wbar")),
    "fused",
]
# CPU against GPU for the measured scalars (stated here; AD-11 is a bound on image values): the
# N{} bounds in high-pass units, the saliency means in L*, a*, b* units (0-100 for L*).
BOUNDS_TOLERANCE = 1e-5
MEANS_TOLERANCE = 1e-3


def render(backend: CoreBackend, a: Any, params: Params) -> tuple[Any, Any, Any]:
    """Input 1, input 2 and the fused image of :func:`render_all`."""
    out = render_all(backend, a, params)
    return out["input 1"], out["input 2"], out["fused"]


def proto_render(a: Any, params: Params) -> tuple[Any, Any, Any]:
    """The prototype's steps 3-5 measuring everything itself (no hook)."""
    input1, input2 = proto.fusion_inputs(a, params)
    weights = proto.weight_maps((input1, input2), params).normalised
    return input1, input2, proto.multiscale_fusion((input1, input2), weights, params)


def deviation(product: Any, reference: Any, backend: CoreBackend) -> tuple[float, float]:
    """Max and largest per-channel mean absolute difference, on the host in float64."""
    p = np.asarray(backend.to_host(product), dtype=np.float64)
    r = np.asarray(backend.to_host(reference), dtype=np.float64)
    difference = np.abs(p - r)
    if difference.ndim == 3:  # an image: the largest per-channel mean
        return float(difference.max()), float(difference.reshape(-1, 3).mean(axis=0).max())
    return float(difference.max()), float(difference.mean())


def test_measured_path_within_ad11(backend: CoreBackend, params: Params) -> None:
    """Measured bounds are float32 (R0-8): the chain matches the prototype within AD-11.

    Only the scene, whose range is above the floor at both parameter sets, isolates the
    float32-bounds deviation; where the floor binds the difference is the floor itself.
    """
    a = backend.asarray(scene((192, 288)))
    low, high = proto.normalisation_bounds(a, params)
    assert high - low >= 0.02
    for name, product, reference in zip(
        ("input 1", "input 2", "fused"),
        render(backend, a, params),
        proto_render(a, params),
        strict=True,
    ):
        largest, mean = deviation(product, reference, backend)
        assert largest <= AD11_MAX and mean <= AD11_MEAN, f"{name}: {largest:.3g} / {mean:.3g}"
        if name == "input 1":
            assert largest == 0.0


@pytest.mark.gpu
@pytest.mark.parametrize("name", ["synthetic-0", "synthetic-1", "scene", "near-flat", "1x1", "odd"])
def test_cpu_against_gpu_within_ad11(gpu: CoreBackend, name: str) -> None:
    """Every intermediate of steps 3-5, each device measuring its own statistics."""
    host = {
        "synthetic-0": synthetic(0),
        "synthetic-1": synthetic(1),
        "scene": scene(),
        "near-flat": near_flat(),
        "1x1": synthetic(0, (1, 1)),
        "odd": synthetic(1, (37, 53)),
    }[name]
    cpu = NumpyBackend()
    for params in PARAMS.values():
        on_cpu = render_all(cpu, cpu.asarray(host), params)
        on_gpu = render_all(gpu, gpu.asarray(host), params)
        assert set(on_cpu) == {"bounds", "means", *ARRAY_KEYS}
        for key in ARRAY_KEYS:
            largest, mean = deviation(on_cpu[key], gpu.to_host(on_gpu[key]), cpu)
            assert largest <= AD11_MAX and mean <= AD11_MEAN, f"{key}: {largest:.3g}/{mean:.3g}"
        gap = np.abs(np.subtract(on_cpu["bounds"], on_gpu["bounds"])).max()
        assert gap <= BOUNDS_TOLERANCE, f"bounds: {gap:.3g}"
        gap = np.abs(np.subtract(on_cpu["means"], on_gpu["means"])).max()
        assert gap <= MEANS_TOLERANCE, f"saliency means: {gap:.3g}"


def near_flat(shape: tuple[int, int] = (64, 96)) -> np.ndarray:
    """WP1.1's near-flat ``_synthetic`` (the DR-14 case: an N{} range of about 0.0017)."""
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]].astype(np.float32)
    y /= max(shape[0] - 1, 1)
    x /= max(shape[1] - 1, 1)
    image = np.stack([0.05 + 0.15 * x, 0.35 + 0.35 * y, 0.45 + 0.25 * x * y], axis=2)
    noise = np.random.default_rng(0).normal(0.0, 0.01, image.shape)
    return np.clip(image + noise, 0.0, 1.0).astype(np.float32)


@pytest.mark.gpu
def test_floor_bounds_the_dr14_gap(gpu: CoreBackend) -> None:
    """DR-14: on the near-flat input the floor shrinks the CPU/GPU gap of input 2.

    Without the floor (the prototype) the 1.2e-7 high-pass gap is amplified by 1 / 0.0017; with
    it, by at most 1 / 0.02.
    """
    host = near_flat()
    params = Params()
    cpu = NumpyBackend()
    bounds = proto.normalisation_bounds(host, params)
    assert bounds[1] - bounds[0] < 0.0018
    unfloored = deviation(
        proto.fusion_inputs(host, params)[1],
        gpu.to_host(proto.fusion_inputs(gpu.asarray(host), params)[1]),
        cpu,
    )
    on_cpu = fusion.fusion_inputs(cpu, cpu.asarray(host), **inputs_kw(params), bounds=bounds)[1]
    on_gpu = fusion.fusion_inputs(gpu, gpu.asarray(host), **inputs_kw(params), bounds=bounds)[1]
    with_floor = deviation(on_cpu, gpu.to_host(on_gpu), cpu)
    assert with_floor[0] <= AD11_MAX and with_floor[1] <= AD11_MEAN
    assert with_floor[0] < unfloored[0] / 5, (with_floor, unfloored)


def test_same_device_twice_bit_identical(backend: CoreBackend, params: Params) -> None:
    a = backend.asarray(scene())
    first = render_all(backend, a, params)
    second = render_all(backend, a, params)
    assert first["bounds"] == second["bounds"] and first["means"] == second["means"]
    for key in ARRAY_KEYS:
        same(first[key], second[key], backend, f"twice: {key}")
