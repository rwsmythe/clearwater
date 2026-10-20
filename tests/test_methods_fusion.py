"""WP3.3: the fusion steps' own contract (spec 6.2 steps 3-5, AD-4, X-4, V1, V9, Gate 1).

The floor of N{} (AD-4 as amended, DR-14), the guards on supplied statistics, the V1 edge
cases, V9 neutrality, the weight regularisation, the DR-19 rule X-4, planted wrong
implementations, the GPU sync points and the dependency rule. The prototype comparisons are in
``test_methods_fusion_prototype.py``.
"""

from __future__ import annotations

import inspect
import json
import logging
import math
import subprocess
import sys
from collections.abc import Callable, Sequence
from typing import Any

import numpy as np
import pytest

from clearwater.core import CoreBackend, NumpyBackend, pyramid_levels
from clearwater.core.backend import _probe_gpu
from clearwater.methods import fusion
from prototype import pipeline as proto
from prototype.params import Params

DEFAULTS = Params()
WIDE = Params(
    sharpen_blur_fraction=0.05,
    laplacian_fraction=0.02,
    saliency_blur_fraction=0.03,
    pyramid_min_level_size=4,
)


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


def noise(shape: tuple[int, ...] = (40, 60, 3), seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).random(shape, dtype=np.float32)


def flat(shape: tuple[int, int] = (40, 50)) -> np.ndarray:
    return np.broadcast_to(np.array([0.3, 0.55, 0.71], np.float32), (*shape, 3)).copy()


def near_flat(shape: tuple[int, int] = (64, 96)) -> np.ndarray:
    """WP1.1's near-flat ``_synthetic`` (DR-14: an N{} range of about 0.0017 at 64 x 96)."""
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]].astype(np.float32)
    y /= max(shape[0] - 1, 1)
    x /= max(shape[1] - 1, 1)
    image = np.stack([0.05 + 0.15 * x, 0.35 + 0.35 * y, 0.45 + 0.25 * x * y], axis=2)
    disturbance = np.random.default_rng(0).normal(0.0, 0.01, image.shape)
    return np.clip(image + disturbance, 0.0, 1.0).astype(np.float32)


def host(backend: CoreBackend, a: Any) -> np.ndarray:
    return np.asarray(backend.to_host(a))


def identical(x: np.ndarray, y: np.ndarray) -> bool:
    """Bit identity as a plain bool (pytest's rewrite of a failing bytes ``==`` runs a diff
    over every byte, which on a planted defect under ``-v`` takes many minutes)."""
    return x.dtype == y.dtype and x.shape == y.shape and x.tobytes() == y.tobytes()


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


def measure_bounds(backend: CoreBackend, a: Any, params: Params) -> tuple[float, float]:
    return fusion.normalisation_bounds(
        backend,
        a,
        sharpen_blur_fraction=params.sharpen_blur_fraction,
        normalisation_low=params.normalisation_low,
        normalisation_high=params.normalisation_high,
    )


def chain(backend: CoreBackend, a: Any, params: Params) -> Any:
    """Measure, then render steps 3-5 (the order WP3.4 will run them in)."""
    input1, input2 = fusion.fusion_inputs(
        backend, a, **inputs_kw(params), bounds=measure_bounds(backend, a, params)
    )
    means = [fusion.saliency_reference(backend, x) for x in (input1, input2)]
    weights = fusion.weight_maps(
        backend, (input1, input2), **weights_kw(params), saliency_means=means
    )
    return fusion.multiscale_fusion(
        backend, (input1, input2), weights, pyramid_min_level_size=params.pyramid_min_level_size
    )


def stretched(backend: CoreBackend, a: Any, input2: Any) -> np.ndarray:
    """Recover N{} from input 2 at sharpen_strength 1: ``N = 2 S - I`` (float64)."""
    return 2.0 * host(backend, input2).astype(np.float64) - host(backend, a).astype(np.float64)


# -- the floor (AD-4 as amended, ruling 3.1; DR-14) -------------------------------------------

FusionInputs = Callable[..., tuple[Any, Any]]


def check_flat_gives_half(implementation: FusionInputs, backend: CoreBackend) -> None:
    """An exactly flat image (high-pass 0, bounds equal) stretches to 0.5, as the prototype."""
    image = flat()
    a = backend.asarray(image)
    _, input2 = implementation(backend, a, **inputs_kw(WIDE), bounds=(0.0, 0.0))
    expected = (image + np.float32(0.5)) / np.float32(2.0)
    tolerance = 0.0 if backend.name == "numpy" else 1e-5  # cupyx: a high-pass of +/- 1 ulp
    assert np.abs(host(backend, input2) - expected).max() <= tolerance


def check_near_flat_widened(implementation: FusionInputs, backend: CoreBackend) -> None:
    """Bounds 0.0017 apart are widened about their midpoint to 0.02: slope 50, not 588."""
    a = backend.asarray(near_flat())
    low, high = 0.0, 0.0017
    hp = host(backend, fusion.high_pass(backend, a, sharpen_blur_fraction=0.005)).astype(np.float64)
    mid = (low + high) / 2.0
    expected = np.clip((hp - (mid - 0.01)) / 0.02, 0.0, 1.0)
    _, input2 = implementation(backend, a, **inputs_kw(DEFAULTS), bounds=(low, high))
    assert np.abs(stretched(backend, a, input2) - expected).max() <= 2e-6


def test_floor_flat_image(backend: CoreBackend) -> None:
    check_flat_gives_half(fusion.fusion_inputs, backend)


def test_floor_near_flat_image(backend: CoreBackend) -> None:
    check_near_flat_widened(fusion.fusion_inputs, backend)


@pytest.mark.parametrize("bounds", [(0.0, 0.02), (-0.05, 0.05), (-0.3, 0.4), (0.1, 0.2)])
def test_floor_leaves_wide_bounds_alone(backend: CoreBackend, bounds: tuple[float, float]) -> None:
    a = backend.asarray(noise())
    _, input2 = fusion.fusion_inputs(backend, a, **inputs_kw(WIDE), bounds=bounds)
    _, reference = proto.fusion_inputs(a, WIDE, proto.Statistics(normalisation_bounds=bounds))
    assert identical(host(backend, input2), host(backend, reference))


def test_floor_bounds_dr14_amplification(backend: CoreBackend) -> None:
    """DR-14 (WP1.2A F1): a perturbation of the near-flat input is amplified 1 / 0.02 at most."""
    image = near_flat()
    bounds = proto.normalisation_bounds(image, DEFAULTS)
    assert bounds[1] - bounds[0] < 0.0018
    perturbed = image.copy()
    perturbed[30:34, 40:44] += np.float32(1e-4)
    ratios = {}
    for name, implementation in (("product", fusion.fusion_inputs), ("prototype", None)):
        changes = []
        for x in (image, perturbed):
            a = backend.asarray(x)
            if implementation is None:
                statistics = proto.Statistics(normalisation_bounds=bounds)
                changes.append(
                    (
                        proto.high_pass_of(a, DEFAULTS),
                        proto.fusion_inputs(a, DEFAULTS, statistics)[1],
                        a,
                    )
                )
            else:
                changes.append(
                    (
                        fusion.high_pass(backend, a, sharpen_blur_fraction=0.005),
                        implementation(backend, a, **inputs_kw(DEFAULTS), bounds=bounds)[1],
                        a,
                    )
                )
        (hp0, s0, a0), (hp1, s1, a1) = changes
        d_hp = np.abs(host(backend, hp1).astype(np.float64) - host(backend, hp0)).max()
        d_n = np.abs(stretched(backend, a1, s1) - stretched(backend, a0, s0)).max()
        ratios[name] = d_n / d_hp
    assert ratios["product"] <= 50.0 * 1.01, ratios
    assert ratios["prototype"] > 400.0, ratios


# -- guards on supplied statistics (ruling 4, brief question 2) --------------------------------


@pytest.mark.parametrize(
    "bounds",
    [
        (math.nan, 0.1),
        (0.0, math.inf),
        (-math.inf, 0.0),
        (0.2, 0.1),
        (0.1,),
        (0.0, 0.1, 0.2),
        # finite, but not in float32, the precision they meet the data in (R1 F3)
        (1e308, 1e308),
        (-1e300, 1e300),
        (1e39, 1e39),
        (-3e38, 3e38),  # each bound in range, the range high - low not
    ],
)
def test_bounds_guard(bounds: Sequence[float]) -> None:
    check_bounds_guard(fusion.fusion_inputs, bounds)


def check_bounds_guard(implementation: FusionInputs, bounds: Sequence[float]) -> None:
    """Bad supplied bounds: one ValueError naming ``bounds``, before any array work."""
    spy, image = watched()
    with pytest.raises(ValueError, match="bounds"):
        implementation(spy, image, **inputs_kw(DEFAULTS), bounds=bounds)
    assert spy.calls == 0 and _Watched.calls == 0


def _late_guard(backend: CoreBackend, a: Any, **kw: Any) -> tuple[Any, Any]:
    """Planted: the high-pass first, then the product (whose guard then refuses)."""
    fusion.high_pass(backend, a, sharpen_blur_fraction=kw["sharpen_blur_fraction"])
    return fusion.fusion_inputs(backend, a, **kw)


def test_planted_guard_after_array_work() -> None:
    check_bounds_guard(fusion.fusion_inputs, (0.2, 0.1))
    with pytest.raises(AssertionError):
        check_bounds_guard(_late_guard, (0.2, 0.1))


@pytest.mark.parametrize("bounds", [(0.1, 0.1), (-1e38, 1e38), (3e38, 3e38)])
def test_extreme_float32_bounds_accepted(bounds: tuple[float, float]) -> None:
    """Equal bounds, and bounds whose values and range are float32-finite, give finite inputs."""
    backend = NumpyBackend()
    _, input2 = fusion.fusion_inputs(backend, noise(), **inputs_kw(DEFAULTS), bounds=bounds)
    assert np.isfinite(input2).all()


@pytest.mark.parametrize(
    ("means", "field"),
    [
        ([(50.0, 0.0, 0.0)], "saliency_means"),
        ([(50.0, 0.0, 0.0)] * 3, "saliency_means"),
        ([(50.0, 0.0), (50.0, 0.0, 0.0)], r"saliency_means\[0\]"),
        ([(50.0, 0.0, 0.0), (50.0, math.nan, 0.0)], r"saliency_means\[1\]"),
        ([(50.0, 0.0, 0.0), (math.inf, 0.0, 0.0)], r"saliency_means\[1\]"),
    ],
)
def test_saliency_means_guard(means: list[tuple[float, ...]], field: str) -> None:
    spy, image = watched()
    with pytest.raises(ValueError, match=field):
        fusion.weight_maps(spy, (image, image), **weights_kw(DEFAULTS), saliency_means=means)
    assert spy.calls == 0 and _Watched.calls == 0


@pytest.mark.parametrize("mean", [(50.0, 0.0), (50.0, 0.0, 0.0, 1.0), (50.0, math.nan, 0.0)])
def test_saliency_mean_guard(mean: tuple[float, ...]) -> None:
    spy, image = watched()
    with pytest.raises(ValueError, match="saliency_mean"):
        fusion.saliency_weight(spy, image, saliency_blur_fraction=0.003, saliency_mean=mean)
    assert spy.calls == 0 and _Watched.calls == 0


# -- input checks ---------------------------------------------------------------------------


class _ProtocolOnly:
    """Has IF-2's attributes but is not a clearwater.core backend (DR-37 b)."""

    name = "numpy"
    device = "cpu"


ARRAY_FUNCTIONS: list[tuple[str, Callable[[Any, Any], Any]]] = [
    ("high_pass", lambda b, a: fusion.high_pass(b, a, sharpen_blur_fraction=0.005)),
    ("normalisation_bounds", lambda b, a: measure_bounds(b, a, DEFAULTS)),
    (
        "fusion_inputs",
        lambda b, a: fusion.fusion_inputs(b, a, **inputs_kw(DEFAULTS), bounds=(0, 1)),
    ),
    ("saliency_reference", fusion.saliency_reference),
    ("laplacian_weight", lambda b, a: fusion.laplacian_weight(b, a, laplacian_fraction=0.001)),
    (
        "saliency_weight",
        lambda b, a: fusion.saliency_weight(
            b, a, saliency_blur_fraction=0.003, saliency_mean=(50.0, 0.0, 0.0)
        ),
    ),
    ("saturation_weight", fusion.saturation_weight),
    (
        "weight_maps",
        lambda b, a: fusion.weight_maps(
            b, (a, a), **weights_kw(DEFAULTS), saliency_means=[(50.0, 0.0, 0.0)] * 2
        ),
    ),
    (
        "multiscale_fusion",
        lambda b, a: fusion.multiscale_fusion(
            b, (a,), (a[..., 0] if a.ndim == 3 else a,), pyramid_min_level_size=16
        ),
    ),
]


@pytest.mark.parametrize(("name", "call"), ARRAY_FUNCTIONS, ids=[n for n, _ in ARRAY_FUNCTIONS])
def test_input_checks(name: str, call: Callable[[Any, Any], Any]) -> None:
    backend = NumpyBackend()
    with pytest.raises(TypeError):
        call(_ProtocolOnly(), noise())
    with pytest.raises(ValueError):
        call(backend, noise().astype(np.float64))
    with pytest.raises(ValueError):
        call(backend, noise((40, 60)))
    with pytest.raises((TypeError, ValueError)):
        call(backend, noise((40, 60, 4)))


@pytest.mark.gpu
def test_foreign_device_array_refused(gpu: CoreBackend) -> None:
    with pytest.raises(TypeError):
        fusion.saturation_weight(NumpyBackend(), gpu.asarray(noise()))
    with pytest.raises(TypeError):
        fusion.saturation_weight(gpu, noise())


def test_non_arrays_refused_with_type_error() -> None:
    """The array checks run before any shape is read (R1 F4): TypeError, not AttributeError."""
    backend = NumpyBackend()
    image = noise()
    with pytest.raises(TypeError):
        fusion.weight_maps(
            backend, [object()], **weights_kw(DEFAULTS), saliency_means=[(50.0, 0.0, 0.0)]
        )
    with pytest.raises(TypeError):
        fusion.multiscale_fusion(backend, [object()], [object()], pyramid_min_level_size=16)
    with pytest.raises(TypeError):
        fusion.multiscale_fusion(backend, [image], [object()], pyramid_min_level_size=16)


def test_shape_mismatches_refused() -> None:
    backend = NumpyBackend()
    with pytest.raises(ValueError, match="at least one"):
        fusion.weight_maps(backend, (), **weights_kw(DEFAULTS), saliency_means=[])
    with pytest.raises(ValueError, match="differ in shape"):
        fusion.weight_maps(
            backend,
            (noise(), noise((40, 61, 3))),
            **weights_kw(DEFAULTS),
            saliency_means=[(50.0, 0.0, 0.0)] * 2,
        )
    image = noise()
    weight = image[..., 0].copy()
    with pytest.raises(ValueError, match="one weight map per input"):
        fusion.multiscale_fusion(backend, (image, image), (weight,), pyramid_min_level_size=16)
    with pytest.raises(ValueError, match="differ in shape"):
        fusion.multiscale_fusion(
            backend, (image,), (weight[:, :-1].copy(),), pyramid_min_level_size=16
        )
    with pytest.raises(ValueError, match="differ in shape"):
        fusion.multiscale_fusion(backend, (image,), (image,), pyramid_min_level_size=16)


def test_signatures_are_x1_form() -> None:
    """Backend first, the arrays next, keyword-only parameters without defaults (X-1).

    No step takes a compensation or white-balance parameter (X-4: validation is
    method-scoped by construction).
    """
    expected = {
        "high_pass": (["backend", "a"], {"sharpen_blur_fraction"}),
        "normalisation_bounds": (
            ["backend", "a"],
            {"sharpen_blur_fraction", "normalisation_low", "normalisation_high"},
        ),
        "fusion_inputs": (
            ["backend", "a"],
            {"gamma", "sharpen_strength", "sharpen_blur_fraction", "bounds"},
        ),
        "saliency_reference": (["backend", "a"], set()),
        "laplacian_weight": (["backend", "a"], {"laplacian_fraction"}),
        "saliency_weight": (["backend", "a"], {"saliency_blur_fraction", "saliency_mean"}),
        "saturation_weight": (["backend", "a"], set()),
        "weight_maps": (
            ["backend", "inputs"],
            {"laplacian_fraction", "saliency_blur_fraction", "weight_delta", "saliency_means"},
        ),
        "multiscale_fusion": (["backend", "inputs", "weights"], {"pyramid_min_level_size"}),
    }
    public = {
        name
        for name, value in vars(fusion).items()
        if inspect.isfunction(value) and value.__module__ == fusion.__name__ and name[0] != "_"
    }
    assert public == set(expected)
    for name, (positional, keywords) in expected.items():
        parameters = inspect.signature(getattr(fusion, name)).parameters.values()
        assert [p.name for p in parameters if p.kind is p.POSITIONAL_OR_KEYWORD] == positional
        assert {p.name for p in parameters if p.kind is p.KEYWORD_ONLY} == keywords
        assert all(p.default is p.empty for p in parameters), name
    assert fusion.NORMALISATION_RANGE_FLOOR == 0.02


# -- input 1 (ruling 1: clipped, a no-op on [0, 1] data) ---------------------------------------


@pytest.mark.parametrize("gamma", [0.0, 0.5, 1.0, 1.5, 3.0])
def test_input1_clip_is_a_no_op(backend: CoreBackend, gamma: float) -> None:
    image = noise()
    image[0, 0] = 0.0
    image[0, 1] = 1.0
    a = backend.asarray(image)
    input1, _ = fusion.fusion_inputs(
        backend, a, gamma=gamma, sharpen_strength=1.0, sharpen_blur_fraction=0.005, bounds=(0, 1)
    )
    unclipped = a ** np.float32(gamma)
    assert identical(host(backend, input1), host(backend, unclipped))


# -- V1 edge cases ---------------------------------------------------------------------------

EDGE_SHAPES = [(1, 1), (1, 7), (5, 1), (2, 3), (30, 45), (31, 45), (33, 47), (64, 96)]


def edge_image(kind: str, shape: tuple[int, int]) -> np.ndarray:
    rng = np.random.default_rng(3)
    if kind == "uniform":
        return flat(shape)
    if kind == "near-zero-red":
        image = rng.random((*shape, 3), dtype=np.float32)
        image[..., 0] *= np.float32(1e-3)
        return image
    if kind == "16-bit":
        return (rng.integers(0, 65536, (*shape, 3)) / 65535.0).astype(np.float32)
    if kind == "10-bit":
        return (rng.integers(0, 1024, (*shape, 3)) / 1023.0).astype(np.float32)
    raise AssertionError(kind)


@pytest.mark.parametrize("kind", ["uniform", "near-zero-red", "16-bit", "10-bit"])
@pytest.mark.parametrize("shape", EDGE_SHAPES, ids=[f"{h}x{w}" for h, w in EDGE_SHAPES])
def test_v1_edge_cases(backend: CoreBackend, kind: str, shape: tuple[int, int]) -> None:
    image = edge_image(kind, shape)
    for params in (DEFAULTS, WIDE):
        fused = host(backend, chain(backend, backend.asarray(image), params))
        assert fused.dtype == np.float32 and fused.shape == image.shape
        assert np.isfinite(fused).all() and fused.min() >= 0.0 and fused.max() <= 1.0
        if kind == "uniform":
            assert np.ptp(fused.reshape(-1, 3), axis=0).max() <= 1e-6


def test_pyramid_depth_changes_with_size() -> None:
    """At the default minimum of 16 px the depth steps at 31 px (to 2) and 61 px (to 3)."""
    assert [pyramid_levels((n, 200), 16) for n in (30, 31, 60, 61)] == [1, 2, 2, 3]


@pytest.mark.parametrize("shape", [(30, 45), (31, 45), (60, 80), (61, 80)])
def test_fusion_across_depth_changes_matches_prototype(
    backend: CoreBackend, shape: tuple[int, int]
) -> None:
    a = backend.asarray(noise((*shape, 3)))
    b = backend.asarray(noise((*shape, 3), seed=1))
    weight = backend.asarray(noise(shape, seed=2))
    weights = (weight, 1.0 - weight)
    fused = fusion.multiscale_fusion(backend, (a, b), weights, pyramid_min_level_size=16)
    reference = proto.multiscale_fusion((a, b), weights, DEFAULTS)
    assert identical(host(backend, fused), host(backend, reference))


# -- V9 neutrality ---------------------------------------------------------------------------

V9_MAX = 2.0 / 255.0
V9_MEAN = 0.2 / 255.0


@pytest.mark.parametrize("bounds", [(0.0, 0.0), (-0.1, 0.1)])
def test_v9_neutral_inputs_are_identity(backend: CoreBackend, bounds: tuple[float, float]) -> None:
    image = noise()
    a = backend.asarray(image)
    input1, input2 = fusion.fusion_inputs(
        backend, a, gamma=1.0, sharpen_strength=0.0, sharpen_blur_fraction=0.005, bounds=bounds
    )
    assert identical(host(backend, input1), image)
    assert identical(host(backend, input2), image)


@pytest.mark.parametrize("params", [DEFAULTS, WIDE], ids=["defaults", "wide"])
def test_v9_fusing_identical_inputs_returns_the_input(backend: CoreBackend, params: Params) -> None:
    image = near_flat((96, 144))
    a = backend.asarray(image)
    means = [fusion.saliency_reference(backend, a)] * 2
    weights = fusion.weight_maps(backend, (a, a), **weights_kw(params), saliency_means=means)
    fused = fusion.multiscale_fusion(
        backend, (a, a), weights, pyramid_min_level_size=params.pyramid_min_level_size
    )
    difference = np.abs(host(backend, fused).astype(np.float64) - image)
    assert difference.max() <= V9_MAX
    assert difference.reshape(-1, 3).mean(axis=0).max() <= V9_MEAN


# -- weight regularisation (spec 6.2 step 4) ---------------------------------------------------

WeightMaps = Callable[..., tuple[Any, ...]]


def check_regularisation(implementation: WeightMaps, backend: CoreBackend, count: int) -> None:
    """Sum to 1, and ``(W_k + delta) / (sum W + K delta)`` with K the input count, in float64."""
    images = [backend.asarray(noise(seed=seed)) for seed in range(count)]
    means = [fusion.saliency_reference(backend, x) for x in images]
    delta = 0.1
    normalised = implementation(
        backend,
        images,
        laplacian_fraction=0.02,
        saliency_blur_fraction=0.03,
        weight_delta=delta,
        saliency_means=means,
    )
    assert len(normalised) == count
    raw = [
        (
            host(backend, fusion.laplacian_weight(backend, x, laplacian_fraction=0.02)).astype(
                np.float64
            )
            + host(
                backend,
                fusion.saliency_weight(backend, x, saliency_blur_fraction=0.03, saliency_mean=m),
            )
            + host(backend, fusion.saturation_weight(backend, x))
        )
        for x, m in zip(images, means, strict=True)
    ]
    total = sum(raw) + count * delta
    for w, r in zip(normalised, raw, strict=True):
        assert host(backend, w).dtype == np.float32
        assert np.abs(host(backend, w) - (r + delta) / total).max() <= 1e-6
    assert np.abs(sum(host(backend, w).astype(np.float64) for w in normalised) - 1.0).max() <= (
        count * 1.2e-7
    )


@pytest.mark.parametrize("count", [1, 2, 3])
def test_regularisation(backend: CoreBackend, count: int) -> None:
    check_regularisation(fusion.weight_maps, backend, count)


# -- DR-19 under X-4 -------------------------------------------------------------------------


class _Watched(np.ndarray):
    """An ndarray that counts every ufunc applied to it (array work)."""

    calls = 0

    def __array_ufunc__(self, ufunc: Any, method: str, *inputs: Any, **kwargs: Any) -> Any:
        _Watched.calls += 1
        plain = tuple(np.asarray(x) if isinstance(x, _Watched) else x for x in inputs)
        return getattr(ufunc, method)(*plain, **kwargs)


class _Spy(NumpyBackend):
    """A core backend counting its array methods."""

    def __init__(self) -> None:
        super().__init__()
        self.calls = 0

    def gaussian_blur(self, a: Any, sigma_px: float) -> Any:
        self.calls += 1
        return super().gaussian_blur(a, sigma_px)

    def percentile(self, a: Any, q: Sequence[float]) -> Any:
        self.calls += 1
        return super().percentile(a, q)

    def asarray(self, a: Any, dtype: Any = np.float32) -> Any:
        self.calls += 1
        return super().asarray(a, dtype)


def watched() -> tuple[_Spy, np.ndarray]:
    """A fresh counting backend and a counted 40 x 60 image (counters at 0)."""
    _Watched.calls = 0
    return _Spy(), noise((40, 60, 3)).view(_Watched)


def x4_calls(parameter: str, value: float) -> list[Callable[[Any, Any], Any]]:
    """Every public step that derives a sigma from ``parameter``, called with ``value``."""
    sharpen = {**inputs_kw(DEFAULTS), "sharpen_blur_fraction": value}
    weights = {**weights_kw(DEFAULTS), parameter: value}
    means = [(50.0, 0.0, 0.0)] * 2
    if parameter == "sharpen_blur_fraction":
        return [
            lambda b, a: fusion.high_pass(b, a, sharpen_blur_fraction=value),
            lambda b, a: fusion.normalisation_bounds(
                b, a, sharpen_blur_fraction=value, normalisation_low=0.5, normalisation_high=99.5
            ),
            lambda b, a: fusion.fusion_inputs(b, a, **sharpen, bounds=(0.0, 1.0)),
        ]
    single: Callable[[Any, Any], Any]
    if parameter == "laplacian_fraction":
        single = lambda b, a: fusion.laplacian_weight(b, a, laplacian_fraction=value)  # noqa: E731
    else:
        single = lambda b, a: fusion.saliency_weight(  # noqa: E731
            b, a, saliency_blur_fraction=value, saliency_mean=means[0]
        )
    return [
        single,
        lambda b, a: fusion.weight_maps(b, (a, a), **weights, saliency_means=means),
    ]


X4_PARAMETERS = ["sharpen_blur_fraction", "laplacian_fraction", "saliency_blur_fraction"]


@pytest.mark.parametrize("parameter", X4_PARAMETERS)
@pytest.mark.parametrize("value", [0.0, -0.01, math.nan, math.inf, 1e300])
def test_x4_unusable_sigma_names_the_parameter(
    parameter: str,
    value: float,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    """One ValueError naming the parameter, its value and the short side; nothing before it."""
    caplog.set_level(logging.DEBUG)
    for call in x4_calls(parameter, value):
        spy = _Spy()
        image = noise((40, 60, 3)).view(_Watched)
        _Watched.calls = 0
        with pytest.raises(ValueError) as raised:
            call(spy, image)
        message = str(raised.value)
        assert message.startswith(f"{parameter}={value!r} gives a sigma of "), message
        assert "at the short side 40 px; sigma " in message, message
        assert isinstance(raised.value.__cause__, ValueError)
        assert str(raised.value.__cause__) in message  # check_sigma's reason, not restated
        assert spy.calls == 0 and _Watched.calls == 0  # nothing ran before the refusal
    assert capsys.readouterr() == ("", "")
    assert caplog.records == []


@pytest.mark.parametrize("parameter", X4_PARAMETERS)
def test_x4_sigma_near_the_float_maximum(parameter: str) -> None:
    """1e308 of a 1 px short side: a finite sigma whose ``4 * sigma`` overflows in the core's
    radius rule (OverflowError there) is refused as the same X-4 ValueError (as WP3.2)."""
    for call in x4_calls(parameter, 1e308):
        spy, image = _Spy(), np.full((1, 1, 3), 0.5, np.float32).view(_Watched)
        _Watched.calls = 0
        with pytest.raises(ValueError) as raised:
            call(spy, image)
        message = str(raised.value)
        assert message.startswith(f"{parameter}=1e+308 gives a sigma of 1e+308 px"), message
        assert "at the short side 1 px; " in message, message
        assert isinstance(raised.value.__cause__, OverflowError)
        assert spy.calls == 0 and _Watched.calls == 0


@pytest.mark.parametrize("parameter", X4_PARAMETERS)
def test_x4_support_bound_depends_on_the_image_size(parameter: str) -> None:
    """350 of the short side: refused at 48 MP (radius over 2 ** 23 px), accepted at 1 x 1.

    The 48 MP image is a broadcast view (no memory); it is refused before any array work.
    At 5.3K (short side 2988 px) the same fraction is inside the bound.
    """
    large = np.broadcast_to(np.zeros((1, 1, 3), np.float32), (6000, 8000, 3))
    for call in x4_calls(parameter, 350.0):
        with pytest.raises(ValueError, match=f"{parameter}=350.0 .* short side 6000 px"):
            call(NumpyBackend(), large)
        call(NumpyBackend(), np.full((1, 1, 3), 0.5, np.float32))
    assert fusion._derived_sigma(parameter, 350.0, (2988, 5312, 3)) == 350.0 * 2988


# -- planted wrong implementations (brief task 6, DR-19 item 5) --------------------------------


def _planted_inputs(stretch: Callable[[Any, Any, float, float], Any]) -> FusionInputs:
    """A fusion_inputs whose N{} is ``stretch(backend, a, low, high)``; otherwise the product."""

    def implementation(
        backend: CoreBackend,
        a: Any,
        *,
        gamma: float,
        sharpen_strength: float,
        sharpen_blur_fraction: float,
        bounds: Sequence[float],
    ) -> tuple[Any, Any]:
        input1 = (a ** np.float32(gamma)).clip(0.0, 1.0)
        n = stretch(backend, a, float(bounds[0]), float(bounds[1]))
        sharpened = (a + n) / 2.0
        return input1, (a + sharpen_strength * (sharpened - a)).clip(0.0, 1.0)

    return implementation


def _hp(backend: CoreBackend, a: Any) -> Any:
    return fusion.high_pass(backend, a, sharpen_blur_fraction=0.005)


def _no_floor(backend: CoreBackend, a: Any, low: float, high: float) -> Any:
    if high - low < 1e-6:
        return a * 0.0 + 0.5
    return ((_hp(backend, a) - low) / (high - low)).clip(0.0, 1.0)


def _plain_max(backend: CoreBackend, a: Any, low: float, high: float) -> Any:
    return ((_hp(backend, a) - low) / max(high - low, 0.02)).clip(0.0, 1.0)


def _measured_inside(backend: CoreBackend, a: Any, low: float, high: float) -> Any:
    low, high = measure_bounds(backend, a, DEFAULTS)
    return ((_hp(backend, a) - low) / max(high - low, 1e-6)).clip(0.0, 1.0)


def check_supplied_bounds_used(implementation: FusionInputs, backend: CoreBackend) -> None:
    """The render uses the supplied bounds, whatever the image would measure (AD-4)."""
    a = backend.asarray(noise())
    hp = host(backend, _hp(backend, a)).astype(np.float64)
    _, input2 = implementation(backend, a, **inputs_kw(DEFAULTS), bounds=(-0.3, 0.3))
    expected = np.clip((hp + 0.3) / 0.6, 0.0, 1.0)
    assert np.abs(stretched(backend, a, input2) - expected).max() <= 2e-6


def test_planted_no_floor(backend: CoreBackend) -> None:
    check_near_flat_widened(fusion.fusion_inputs, backend)
    with pytest.raises(AssertionError):
        check_near_flat_widened(_planted_inputs(_no_floor), backend)


def test_planted_floor_as_plain_max(backend: CoreBackend) -> None:
    check_flat_gives_half(fusion.fusion_inputs, backend)
    with pytest.raises(AssertionError):
        check_flat_gives_half(_planted_inputs(_plain_max), backend)


def test_planted_bounds_measured_inside_the_render(backend: CoreBackend) -> None:
    check_supplied_bounds_used(fusion.fusion_inputs, backend)
    with pytest.raises(AssertionError):
        check_supplied_bounds_used(_planted_inputs(_measured_inside), backend)


def _per_channel_bounds(
    backend: CoreBackend,
    a: Any,
    *,
    sharpen_blur_fraction: float,
    normalisation_low: float,
    normalisation_high: float,
) -> tuple[float, float]:
    hp = fusion.high_pass(backend, a, sharpen_blur_fraction=sharpen_blur_fraction)
    lows, highs = [], []
    for c in range(3):
        channel = backend.percentile(hp[..., c], [normalisation_low, normalisation_high])
        low, high = host(backend, channel).tolist()
        lows.append(low)
        highs.append(high)
    return float(np.mean(lows)), float(np.mean(highs))


def check_joint_bounds(
    implementation: Callable[..., tuple[float, float]], backend: CoreBackend
) -> None:
    """The bounds are percentiles over all pixels AND channels (AD-4), R-7 cast to float32."""
    image = noise()
    image[..., 2] *= np.float32(0.2)  # channels of different contrast
    a = backend.asarray(image)
    hp = host(backend, _hp(backend, a)).astype(np.float64).ravel()
    expected = tuple(float(np.float32(v)) for v in np.percentile(hp, [0.5, 99.5]))
    bounds = implementation(
        backend, a, sharpen_blur_fraction=0.005, normalisation_low=0.5, normalisation_high=99.5
    )
    assert bounds == expected


def test_planted_per_channel_bounds(backend: CoreBackend) -> None:
    check_joint_bounds(fusion.normalisation_bounds, backend)
    with pytest.raises(AssertionError):
        check_joint_bounds(_per_channel_bounds, backend)


def _planted_weights(numerator_only: bool, k: int | None) -> WeightMaps:
    def implementation(
        backend: CoreBackend, inputs: Sequence[Any], *, weight_delta: float, **kw: Any
    ) -> tuple[Any, ...]:
        means = kw.pop("saliency_means")
        aggregated = [
            fusion.laplacian_weight(backend, x, laplacian_fraction=kw["laplacian_fraction"])
            + fusion.saliency_weight(
                backend, x, saliency_blur_fraction=kw["saliency_blur_fraction"], saliency_mean=m
            )
            + fusion.saturation_weight(backend, x)
            for x, m in zip(inputs, means, strict=True)
        ]
        total = sum(aggregated[1:], aggregated[0])
        count = len(inputs) if k is None else k
        denominator = total if numerator_only else total + count * weight_delta
        return tuple((w + weight_delta) / denominator for w in aggregated)

    return implementation


def test_planted_delta_in_numerator_only(backend: CoreBackend) -> None:
    check_regularisation(fusion.weight_maps, backend, 2)
    with pytest.raises(AssertionError):
        check_regularisation(_planted_weights(numerator_only=True, k=None), backend, 2)


def test_planted_k_fixed_at_one(backend: CoreBackend) -> None:
    check_regularisation(fusion.weight_maps, backend, 2)
    with pytest.raises(AssertionError):
        check_regularisation(_planted_weights(numerator_only=False, k=1), backend, 2)


Fusion = Callable[..., Any]


def check_fusion(implementation: Fusion, backend: CoreBackend) -> None:
    """The blend equals the prototype's pyramid blend at two sizes and two minimum sizes."""
    for shape, minimum in (((64, 96), 16), ((64, 96), 4), ((37, 53), 16), ((200, 120), 16)):
        a = backend.asarray(noise((*shape, 3)))
        b = backend.asarray(noise((*shape, 3), seed=1))
        weight = backend.asarray(noise(shape, seed=2))
        weights = (weight, 1.0 - weight)
        params = Params(pyramid_min_level_size=minimum)
        reference = proto.multiscale_fusion((a, b), weights, params)
        fused = implementation(backend, (a, b), weights, pyramid_min_level_size=minimum)
        assert identical(host(backend, fused), host(backend, reference))


def _full_resolution(
    backend: CoreBackend, inputs: Sequence[Any], weights: Sequence[Any], **_: Any
) -> Any:
    total = sum((w[..., None] * x for x, w in zip(inputs, weights, strict=True)), 0.0 * inputs[0])
    return total.clip(0.0, 1.0)


def _fixed_depth(
    backend: CoreBackend, inputs: Sequence[Any], weights: Sequence[Any], **_: Any
) -> Any:
    from clearwater.core import collapse_pyramid, gaussian_pyramid, laplacian_pyramid

    fused: list[Any] = []
    for x, w in zip(inputs, weights, strict=True):
        pairs = zip(gaussian_pyramid(backend, w, 3), laplacian_pyramid(backend, x, 3), strict=True)
        blended = [g[..., None] * band for g, band in pairs]
        fused = blended if not fused else [f + b for f, b in zip(fused, blended, strict=True)]
    return collapse_pyramid(backend, fused).clip(0.0, 1.0)


def test_planted_weights_not_pyramided(backend: CoreBackend) -> None:
    check_fusion(fusion.multiscale_fusion, backend)
    with pytest.raises(AssertionError):
        check_fusion(_full_resolution, backend)


def test_planted_fixed_pyramid_depth(backend: CoreBackend) -> None:
    check_fusion(fusion.multiscale_fusion, backend)
    with pytest.raises(AssertionError):
        check_fusion(_fixed_depth, backend)


def _unblurred_saliency(
    backend: CoreBackend, a: Any, *, saliency_blur_fraction: float, saliency_mean: Sequence[float]
) -> Any:
    from clearwater.core import rgb_to_lab

    lab = rgb_to_lab(backend, a)
    reference = backend.asarray(list(saliency_mean))
    return (((lab - reference) ** 2).sum(axis=2)) ** 0.5 / np.float32(100.0)


def check_saliency(implementation: Callable[..., Any], backend: CoreBackend) -> None:
    """W_S equals the prototype's: distance to the BLURRED Lab image."""
    a = backend.asarray(noise())
    mean = proto.saliency_reference(a)
    reference = proto._saliency_weight(a, WIDE, mean)
    weight = implementation(backend, a, saliency_blur_fraction=0.03, saliency_mean=mean)
    assert identical(host(backend, weight), host(backend, reference))


def test_planted_saliency_against_unblurred_lab(backend: CoreBackend) -> None:
    check_saliency(fusion.saliency_weight, backend)
    with pytest.raises(AssertionError):
        check_saliency(_unblurred_saliency, backend)


def _float64_leak(backend: CoreBackend, a: Any, *, gamma: float, **kw: Any) -> tuple[Any, Any]:
    _, input2 = fusion.fusion_inputs(backend, a, gamma=1.0, **kw)
    return a ** np.float64(gamma), input2


def check_float32(implementation: FusionInputs, backend: CoreBackend) -> None:
    """NumPy float64 scalars as parameters still give float32 results (D39, no silent leak)."""
    a = backend.asarray(noise())
    numpy_scalars = {key: np.float64(value) for key, value in inputs_kw(DEFAULTS).items()}
    outputs = implementation(backend, a, **numpy_scalars, bounds=(np.float64(-0.1), 0.1))
    weights = fusion.weight_maps(
        backend,
        outputs,
        laplacian_fraction=np.float64(0.001),
        saliency_blur_fraction=np.float64(0.003),
        weight_delta=np.float64(0.1),
        saliency_means=[tuple(np.float64(v) for v in (50.0, 1.0, -1.0))] * 2,
    )
    fused = fusion.multiscale_fusion(backend, outputs, weights, pyramid_min_level_size=16)
    for array in (*outputs, *weights, fused):
        assert array.dtype == np.float32


def test_planted_float64_leak(backend: CoreBackend) -> None:
    check_float32(fusion.fusion_inputs, backend)
    with pytest.raises((AssertionError, ValueError)):
        check_float32(_float64_leak, backend)


# -- Gate 1: device-resident on the GPU, the sync points only ---------------------------------


@pytest.mark.gpu
def test_gpu_results_stay_on_the_device(gpu: CoreBackend) -> None:
    import cupy

    a = gpu.asarray(noise())
    for name, call in ARRAY_FUNCTIONS:
        out = call(gpu, a)
        if name in ("normalisation_bounds", "saliency_reference"):
            assert all(type(value) is float for value in out), name
            continue
        arrays = out if isinstance(out, tuple) else (out,)
        for array in arrays:
            assert isinstance(array, cupy.ndarray), f"{name} returned {type(array).__name__}"
            assert array.dtype == np.float32, name


@pytest.mark.gpu
@pytest.mark.filterwarnings("ignore:cupyx.allow_synchronize will be removed")
def test_gpu_sync_points_are_the_documented_ones(
    gpu: CoreBackend, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The render reads nothing back; the measures read only through the two sync points.

    ``cupyx.allow_synchronize`` flags the explicit device-to-host copies (``tolist``,
    ``float``, ``asnumpy``); CuPy deprecates it because it cannot see every implicit
    synchronisation, so this pins the host reads, not every stall.
    """
    import cupyx

    a = gpu.asarray(noise((64, 96, 3)))
    bounds = measure_bounds(gpu, a, DEFAULTS)
    input1, input2 = fusion.fusion_inputs(gpu, a, **inputs_kw(DEFAULTS), bounds=bounds)
    means = [fusion.saliency_reference(gpu, x) for x in (input1, input2)]
    with cupyx.allow_synchronize(False):
        rendered = fusion.fusion_inputs(gpu, a, **inputs_kw(DEFAULTS), bounds=bounds)
        weights = fusion.weight_maps(gpu, rendered, **weights_kw(DEFAULTS), saliency_means=means)
        fusion.multiscale_fusion(gpu, rendered, weights, pyramid_min_level_size=16)
        for name, call in ARRAY_FUNCTIONS:
            if name not in ("normalisation_bounds", "saliency_reference"):
                call(gpu, a)
    # Unwrapped, each measure synchronises (it really reads the device) ...
    for measure in (
        lambda: measure_bounds(gpu, a, DEFAULTS),
        lambda: fusion.saliency_reference(gpu, a),
    ):
        with cupyx.allow_synchronize(False), pytest.raises(cupyx.DeviceSynchronized):
            measure()
    # ... and only at the documented sync points.
    allowed = {"count": 0}

    def permitted(function: Callable[..., Any]) -> Callable[..., Any]:
        def wrapped(*args: Any) -> Any:
            allowed["count"] += 1
            with cupyx.allow_synchronize(True):
                return function(*args)

        return wrapped

    monkeypatch.setattr(gpu, "to_host", permitted(gpu.to_host))
    monkeypatch.setattr(fusion, "channel_means", permitted(fusion.channel_means))
    with cupyx.allow_synchronize(False):
        assert measure_bounds(gpu, a, DEFAULTS) == bounds
        assert fusion.saliency_reference(gpu, input1) == means[0]
    assert allowed["count"] == 2


# -- the dependency rule (plan 8.1, frame rule 5) ----------------------------------------------


def test_import_loads_nothing_forbidden() -> None:
    code = (
        "import json, sys\n"
        "import clearwater.methods.fusion\n"
        "top = ['PIL', 'PySide6', 'av', 'cupy', 'cupyx']\n"
        "packages = ['clearwater.io', 'clearwater.jobs', 'clearwater.gui', 'clearwater.config']\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in top\n"
        "             or any(m == p or m.startswith(p + '.') for p in packages))\n"
        "print(json.dumps(bad))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=False
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert json.loads(result.stdout.strip().splitlines()[-1]) == []
