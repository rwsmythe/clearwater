"""WP3.2: channel compensation (spec 6.3.1, 6.3.2) against the read-only prototype and the spec.

The references are computed here by calling ``tools/prototype`` on seeded synthetic inputs and
the WP2.3 stills; nothing is committed. On the same device the product must match the
prototype bit for bit (the round-0 table: every operation is the prototype's); CPU against GPU
is AD-11 (max 2e-3 absolute per channel, mean 2e-4). The planted wrong implementations are
written here and must fail the same checks the product passes.
"""

from __future__ import annotations

import inspect
import json
import logging
import subprocess
import sys
import warnings
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

from clearwater.core import CoreBackend, NumpyBackend, channel_means, rgb_to_ycbcr_matrix
from clearwater.core.backend import _probe_gpu
from clearwater.methods import compensation
from clearwater.methods.compensation import (
    cap_statistics,
    compensate_ancuti2018,
    compensate_c3,
    effective_alphas,
)
from lookcheck.frames import read_png16
from prototype import pipeline as proto
from prototype.params import Params

STILLS_16 = ["png16-uniform-none", "png16-gradient-none", "png16-lowred-none"]
STILLS_8 = ["png8-uniform-none", "png8-gradient-none", "png8-lowred-none"]
AD11_MAX = 2e-3
AD11_MEAN = 2e-4
C3 = {
    "kappa": 1.0,
    "lambda_": 0.7,
    "c3_strength": 1.0,
    "c3_kernel_fraction": 0.05,
    "c3_mask_threshold": 0.85,
    "c3_mask_smooth_fraction": 0.01,
}
"""The AD-8 3C defaults, passed explicitly (the functions have no defaults, X-1 a)."""


@pytest.fixture(params=["numpy", pytest.param("cupy", marks=pytest.mark.gpu)])
def backend(request: pytest.FixtureRequest) -> CoreBackend:
    if request.param == "numpy":
        return NumpyBackend()
    return gpu_backend()


def gpu_backend() -> CoreBackend:
    gpu, reason = _probe_gpu()
    if gpu is None:
        pytest.skip(reason)
    return gpu


def synthetic(seed: int, shape: tuple[int, int] = (45, 67)) -> np.ndarray:
    image = np.random.default_rng(seed).random((*shape, 3), dtype=np.float32)
    if seed % 2:
        image[..., 0] *= np.float32(1e-3)  # near-zero red
    else:
        image[..., 0] *= np.float32(0.4)  # a red cast the compensation works on
    return image


def read_still(path: Path) -> np.ndarray:
    if "png16" in path.name:
        return read_png16(path)
    with PILImage.open(path) as opened:
        return (np.asarray(opened.convert("RGB"), dtype=np.float32) / np.float32(255.0)).copy()


@pytest.fixture(params=["synthetic-0", "synthetic-1", *STILLS_16, *STILLS_8])
def image(request: pytest.FixtureRequest, sample: Callable[[str], Path]) -> np.ndarray:
    name = request.param
    if name.startswith("synthetic"):
        return synthetic(int(name[-1]))
    return read_still(sample(name))


def ancuti_params(**changes: Any) -> Params:
    return Params(method="ancuti2018", **changes)


def ancuti_chain(
    backend: CoreBackend,
    a: Any,
    *,
    alpha: float = 1.0,
    blue_compensation: bool = False,
    red_gain_cap: float | None = 2.0,
    blue_gain_cap: float | None = 2.0,
) -> tuple[Any, tuple[float, float, float], dict[str, float]]:
    """Measure, closed form and render in the order WP3.4 will call them."""
    means = channel_means(backend, a)
    statistics = cap_statistics(backend, a, blue_compensation=blue_compensation)
    alphas = effective_alphas(
        means=means,
        cap_statistics=statistics,
        alpha=alpha,
        blue_compensation=blue_compensation,
        red_gain_cap=red_gain_cap,
        blue_gain_cap=blue_gain_cap,
    )
    return compensate_ancuti2018(backend, a, means=means, alphas=alphas), means, alphas


def host(backend: CoreBackend, a: Any) -> np.ndarray:
    return np.asarray(backend.to_host(a))


def assert_identical(actual: np.ndarray, expected: np.ndarray) -> None:
    assert actual.dtype == np.float32
    assert expected.dtype == np.float32
    assert actual.shape == expected.shape
    assert np.array_equal(actual, expected), f"max abs diff {np.abs(actual - expected).max()}"


def assert_within_ad11(cpu: np.ndarray, gpu: np.ndarray) -> None:
    difference = np.abs(cpu.astype(np.float64) - gpu.astype(np.float64)).reshape(-1, 3)
    assert difference.max(axis=0).max() <= AD11_MAX, difference.max(axis=0)
    assert difference.mean(axis=0).max() <= AD11_MEAN, difference.mean(axis=0)


def rejects(
    check: Callable[[Callable[..., Any]], None], implementation: Callable[..., Any]
) -> bool:
    """Whether ``check`` fails on ``implementation`` (a planted wrong implementation)."""
    try:
        check(implementation)
    except AssertionError:
        return True
    return False


# -- product against prototype (same device, bit for bit) ------------------------------------


@pytest.mark.parametrize("blue", [False, True])
def test_ancuti_measure_and_closed_form_match_prototype(
    backend: CoreBackend, image: np.ndarray, blue: bool
) -> None:
    a = backend.asarray(image)
    params = ancuti_params(blue_compensation=blue)
    _, info = proto.compensate_ancuti2018(a, params)
    means = channel_means(backend, a)
    statistics = cap_statistics(backend, a, blue_compensation=blue)
    assert means == info.channel_means
    green = a[..., 1]
    for name, index in (("red", 0), ("blue", 2)):
        if name in statistics:
            assert statistics[name] == proto._cap_statistic((1.0 - a[..., index]) * green)
    alphas = effective_alphas(
        means=means,
        cap_statistics=statistics,
        alpha=params.alpha,
        blue_compensation=blue,
        red_gain_cap=params.red_gain_cap,
        blue_gain_cap=params.blue_gain_cap,
    )
    assert alphas == info.effective
    assert set(alphas) == ({"red", "blue"} if blue else {"red"})


@pytest.mark.parametrize("blue", [False, True])
def test_ancuti_chain_matches_prototype(
    backend: CoreBackend, image: np.ndarray, blue: bool
) -> None:
    a = backend.asarray(image)
    expected, _ = proto.compensate_ancuti2018(a, ancuti_params(blue_compensation=blue))
    out, _, _ = ancuti_chain(backend, a, blue_compensation=blue)
    assert_identical(host(backend, out), host(backend, expected))


@pytest.mark.parametrize("blue", [False, True])
def test_ancuti_render_matches_prototype_on_supplied_values(
    backend: CoreBackend, image: np.ndarray, blue: bool
) -> None:
    """The render through the prototype's Statistics hook, on values no frame measured."""
    a = backend.asarray(image)
    means = (0.21, 0.55, 0.47)
    alphas = {"red": 0.83, "blue": 0.4} if blue else {"red": 0.83}
    statistics = proto.Statistics(compensation_means=means, compensation_alpha=alphas)
    expected, _ = proto.compensate_ancuti2018(a, ancuti_params(blue_compensation=blue), statistics)
    out = compensate_ancuti2018(backend, a, means=means, alphas=alphas)
    assert_identical(host(backend, out), host(backend, expected))


def test_c3_matches_prototype(backend: CoreBackend, image: np.ndarray) -> None:
    a = backend.asarray(image)
    expected, _ = proto.compensate_c3(a, Params(method="c3"))
    out = compensate_c3(backend, a, **C3)
    assert_identical(host(backend, out), host(backend, expected))


@pytest.mark.parametrize(
    "changes",
    [
        {"c3_strength": 0.6},
        {"kappa": 1.4, "lambda_": 0.2},
        {"c3_kernel_fraction": 0.2, "c3_mask_smooth_fraction": 0.05},
        {"c3_mask_threshold": 0.3},
    ],
)
def test_c3_matches_prototype_off_default(backend: CoreBackend, changes: dict[str, float]) -> None:
    a = backend.asarray(synthetic(4))
    expected, _ = proto.compensate_c3(a, Params(method="c3", **changes))
    out = compensate_c3(backend, a, **{**C3, **changes})
    assert_identical(host(backend, out), host(backend, expected))


# -- CPU against GPU (AD-11) and reproducibility (N10) ---------------------------------------


@pytest.mark.gpu
def test_cpu_and_gpu_agree_within_ad11(image: np.ndarray) -> None:
    gpu = gpu_backend()
    cpu = NumpyBackend()
    for blue in (False, True):
        out_cpu, means_cpu, alphas_cpu = ancuti_chain(
            cpu, cpu.asarray(image), blue_compensation=blue
        )
        out_gpu, means_gpu, alphas_gpu = ancuti_chain(
            gpu, gpu.asarray(image), blue_compensation=blue
        )
        assert np.allclose(means_cpu, means_gpu, rtol=1e-9, atol=1e-12)
        assert alphas_cpu.keys() == alphas_gpu.keys()
        assert all(abs(alphas_cpu[k] - alphas_gpu[k]) <= 1e-6 for k in alphas_cpu)
        assert_within_ad11(host(cpu, out_cpu), host(gpu, out_gpu))
    c3_cpu = compensate_c3(cpu, cpu.asarray(image), **C3)
    c3_gpu = compensate_c3(gpu, gpu.asarray(image), **C3)
    assert_within_ad11(host(cpu, c3_cpu), host(gpu, c3_gpu))


def test_same_device_twice_is_bit_identical(backend: CoreBackend) -> None:
    image = synthetic(6, (61, 83))
    first = ancuti_chain(backend, backend.asarray(image), blue_compensation=True)[0]
    second = ancuti_chain(backend, backend.asarray(image), blue_compensation=True)[0]
    assert_identical(host(backend, first), host(backend, second))
    first = compensate_c3(backend, backend.asarray(image), **C3)
    second = compensate_c3(backend, backend.asarray(image), **C3)
    assert_identical(host(backend, first), host(backend, second))


# -- V1 edge cases ---------------------------------------------------------------------------


@pytest.mark.parametrize("shape", [(1, 1), (1, 7), (7, 1), (7, 5), (2, 3)])
def test_tiny_and_odd_sizes_match_prototype(backend: CoreBackend, shape: tuple[int, int]) -> None:
    a = backend.asarray(synthetic(8, shape))
    expected, _ = proto.compensate_ancuti2018(a, ancuti_params(blue_compensation=True))
    out, _, _ = ancuti_chain(backend, a, blue_compensation=True)
    assert_identical(host(backend, out), host(backend, expected))
    expected, _ = proto.compensate_c3(a, Params(method="c3"))
    assert_identical(host(backend, compensate_c3(backend, a, **C3)), host(backend, expected))


@pytest.mark.parametrize("colour", [(0.5, 0.5, 0.5), (0.2, 0.6, 0.5), (0.9, 0.95, 0.9)])
def test_uniform_image(backend: CoreBackend, colour: tuple[float, float, float]) -> None:
    image = np.empty((9, 13, 3), dtype=np.float32)
    image[...] = np.asarray(colour, dtype=np.float32)
    a = backend.asarray(image)
    out, _, _ = ancuti_chain(backend, a, blue_compensation=True)
    expected, _ = proto.compensate_ancuti2018(a, ancuti_params(blue_compensation=True))
    result = host(backend, out)
    assert_identical(result, host(backend, expected))
    assert np.array_equal(result, np.broadcast_to(result[0, 0], result.shape))
    if colour[0] == colour[1] == colour[2]:
        assert_identical(result, image)  # no difference of means, nothing added
    c3 = host(backend, compensate_c3(backend, a, **C3))
    expected_c3, _ = proto.compensate_c3(a, Params(method="c3"))
    assert_identical(c3, host(backend, expected_c3))
    assert np.array_equal(c3, np.broadcast_to(c3[0, 0], c3.shape))


def test_near_zero_red_cap_binds_and_none_compensates(backend: CoreBackend) -> None:
    """Red of mean ~0: the cap ``2 * mean_r`` stops the compensation; None lets it through."""
    image = synthetic(1)
    image[..., 0] = np.float32(0.0)
    a = backend.asarray(image)
    capped, means, alphas = ancuti_chain(backend, a)
    assert means[0] == 0.0
    assert alphas["red"] == 0.0
    assert_identical(host(backend, capped), image)
    free, _, free_alphas = ancuti_chain(backend, a, red_gain_cap=None)
    assert free_alphas["red"] == 1.0
    assert host(backend, free)[..., 0].min() > 0.0
    expected, _ = proto.compensate_ancuti2018(a, ancuti_params(red_gain_cap=None))
    assert_identical(host(backend, free), host(backend, expected))


def test_cap_binding_not_binding_and_none() -> None:
    means = (0.05, 0.5, 0.4)
    statistics = {"red": 0.4, "blue": 0.3}
    common = {"means": means, "cap_statistics": statistics, "blue_compensation": True}
    # red: added per alpha 0.45 * 0.4 = 0.18 > cap 2 * 0.05 = 0.1 -> alpha 0.1 / 0.18
    binding = effective_alphas(**common, alpha=1.0, red_gain_cap=2.0, blue_gain_cap=2.0)
    assert binding["red"] == pytest.approx(2.0 * 0.05 / (0.45 * 0.4), rel=1e-15)
    assert binding["red"] < 1.0
    # blue: 0.1 * 0.3 = 0.03 <= 2 * 0.4 -> not binding
    assert binding["blue"] == 1.0
    loose = effective_alphas(**common, alpha=1.0, red_gain_cap=10.0, blue_gain_cap=2.0)
    assert loose["red"] == 1.0
    none = effective_alphas(**common, alpha=1.0, red_gain_cap=None, blue_gain_cap=None)
    assert none == {"red": 1.0, "blue": 1.0}
    # green below the channel: nothing is added per alpha, the cap never applies
    reverse = effective_alphas(
        means=(0.6, 0.5, 0.4),
        cap_statistics=statistics,
        alpha=1.0,
        blue_compensation=False,
        red_gain_cap=0.0,
        blue_gain_cap=0.0,
    )
    assert reverse == {"red": 1.0}


def test_capped_render_is_capped_on_the_pixels(backend: CoreBackend) -> None:
    """DR-19 (5): the blue cap shows in the rendered blue pixels, not only in the alphas."""
    image = synthetic(0)
    image[..., 2] *= np.float32(0.05)
    a = backend.asarray(image)
    capped, means, alphas = ancuti_chain(backend, a, blue_compensation=True, blue_gain_cap=0.1)
    free, _, _ = ancuti_chain(backend, a, blue_compensation=True, blue_gain_cap=None)
    assert alphas["blue"] < 1.0
    added_capped = float(host(backend, capped)[..., 2].mean() - image[..., 2].mean())
    added_free = float(host(backend, free)[..., 2].mean() - image[..., 2].mean())
    assert added_capped < added_free
    assert added_capped <= 0.1 * means[2] * (1 + 1e-5)
    expected, _ = proto.compensate_ancuti2018(
        a, ancuti_params(blue_compensation=True, blue_gain_cap=0.1)
    )
    assert_identical(host(backend, capped), host(backend, expected))


def test_blue_off_leaves_blue_and_green_unchanged(backend: CoreBackend) -> None:
    image = synthetic(2)
    a = backend.asarray(image)
    off, _, alphas = ancuti_chain(backend, a, blue_compensation=False)
    assert set(alphas) == {"red"}
    result = host(backend, off)
    assert np.array_equal(result[..., 1:], image[..., 1:])
    assert not np.array_equal(result[..., 0], image[..., 0])
    on, _, alphas_on = ancuti_chain(backend, a, blue_compensation=True)
    assert set(alphas_on) == {"red", "blue"}
    result_on = host(backend, on)
    assert np.array_equal(result_on[..., 1], image[..., 1])
    assert np.array_equal(result_on[..., 0], result[..., 0])
    assert not np.array_equal(result_on[..., 2], image[..., 2])


def mask_image() -> tuple[np.ndarray, float]:
    """A 3 x 3 bluish image whose top row is below, middle row at and bottom row above a
    threshold, which is the float32 mean of the middle row (so ``>`` is decided exactly)."""
    image = np.empty((3, 3, 3), dtype=np.float32)
    image[0] = np.asarray([0.30, 0.60, 0.80], dtype=np.float32)
    image[1] = np.asarray([0.70, 0.85, 0.95], dtype=np.float32)
    image[2] = np.asarray([0.85, 0.95, 1.00], dtype=np.float32)
    threshold = float(image[1:2].mean(axis=2, dtype=np.float32)[0, 0])
    return image, threshold


def test_c3_mask_below_at_and_above_threshold(backend: CoreBackend) -> None:
    image, threshold = mask_image()
    a = backend.asarray(image)
    # a mask sigma under 1/8 px keeps the kernel [1]: M is exactly 0 or 1 per pixel
    changes = {"c3_mask_threshold": threshold, "c3_mask_smooth_fraction": 0.1 / 3}
    out = host(backend, compensate_c3(backend, a, **{**C3, **changes}))
    assert not np.array_equal(out[0], image[0])  # below: compensated
    assert not np.array_equal(out[1], image[1])  # at: not bright, compensated
    assert np.array_equal(out[2], image[2])  # above: M = 0, bit-identical
    expected, _ = proto.compensate_c3(a, Params(method="c3", **changes))
    assert_identical(out, host(backend, expected))


# -- V9 neutrality ---------------------------------------------------------------------------


def test_alpha_zero_is_identity(backend: CoreBackend, image: np.ndarray) -> None:
    a = backend.asarray(image)
    out, _, alphas = ancuti_chain(backend, a, alpha=0.0, blue_compensation=True)
    assert alphas == {"red": 0.0, "blue": 0.0}
    assert_identical(host(backend, out), image)


def test_c3_strength_zero_is_identity(backend: CoreBackend, image: np.ndarray) -> None:
    a = backend.asarray(image)
    out = compensate_c3(backend, a, **{**C3, "c3_strength": 0.0})
    assert_identical(host(backend, out), image)


# -- X-4: derived values (DR-19 items 1 and 2) -----------------------------------------------


@pytest.mark.parametrize("name", ["c3_kernel_fraction", "c3_mask_smooth_fraction"])
@pytest.mark.parametrize("fraction", [0.0, -0.01, float("nan"), float("inf")])
def test_unusable_fraction_raises_one_error_naming_it(
    backend: CoreBackend,
    name: str,
    fraction: float,
    capsys: pytest.CaptureFixture[str],
    caplog: pytest.LogCaptureFixture,
) -> None:
    a = backend.asarray(synthetic(0, (10, 12)))
    caplog.set_level(logging.DEBUG)
    with pytest.raises(ValueError) as caught:
        compensate_c3(backend, a, **{**C3, name: fraction})
    message = str(caught.value)
    assert message.startswith(f"{name}={fraction!r} gives a sigma of ")
    assert "px at the short side 10 px; " in message
    assert isinstance(caught.value.__cause__, ValueError)
    assert capsys.readouterr() == ("", "")
    assert caplog.records == []


@pytest.mark.parametrize("name", ["c3_kernel_fraction", "c3_mask_smooth_fraction"])
def test_support_bound_depends_on_the_short_side(name: str) -> None:
    """DR-19 (5): a size-independent rule fails here. 400 x the short side is a usable sigma
    at 10 px and beyond the core's radius bound (2 ** 23 px) at 48 MP (6000 px)."""
    backend = NumpyBackend()
    small = backend.asarray(synthetic(0, (10, 12)))
    assert compensate_c3(backend, small, **{**C3, name: 400.0}).shape == (10, 12, 3)
    # a read-only broadcast view: the error must come before any array work
    large = np.broadcast_to(np.zeros((1, 1, 3), dtype=np.float32), (6000, 8000, 3))
    with pytest.raises(
        ValueError,
        match=rf"^{name}=400\.0 gives a sigma of 2\.4e\+06 px at the "
        r"short side 6000 px; .*radius beyond",
    ):
        compensate_c3(backend, large, **{**C3, name: 400.0})


def test_validation_is_method_scoped() -> None:
    """Ancuti steps take no spatial fraction; 3C takes no gain cap (D49) and no alpha."""
    for function in (cap_statistics, effective_alphas, compensate_ancuti2018):
        names = set(inspect.signature(function).parameters)
        assert not any(name.endswith("_fraction") for name in names), function.__name__
    c3_names = set(inspect.signature(compensate_c3).parameters)
    assert c3_names == {"backend", "a", *C3}
    for function in (cap_statistics, effective_alphas, compensate_ancuti2018, compensate_c3):
        for parameter in inspect.signature(function).parameters.values():
            if parameter.name not in ("backend", "a"):
                assert parameter.kind is inspect.Parameter.KEYWORD_ONLY, parameter.name
                assert parameter.default is inspect.Parameter.empty, parameter.name


# -- supplied values and inputs (S-1, S-3) ---------------------------------------------------


@pytest.mark.parametrize(
    ("means", "alphas", "argument"),
    [
        ((0.1, 0.2), {"red": 1.0}, "means"),
        ((0.1, float("nan"), 0.3), {"red": 1.0}, "means"),
        ((0.1, 0.2, 0.3), {"blue": 1.0}, "alphas"),
        ((0.1, 0.2, 0.3), {"red": 1.0, "green": 1.0}, "alphas"),
        ((0.1, 0.2, 0.3), {"red": float("inf")}, "alphas"),
    ],
)
def test_render_refuses_bad_supplied_values(
    means: tuple[float, ...], alphas: dict[str, float], argument: str
) -> None:
    backend = NumpyBackend()
    a = backend.asarray(synthetic(0, (4, 4)))
    with pytest.raises(ValueError, match=rf"^{argument}"):
        compensate_ancuti2018(backend, a, means=means, alphas=alphas)


def test_closed_form_refuses_bad_supplied_values() -> None:
    common = {"alpha": 1.0, "red_gain_cap": 2.0, "blue_gain_cap": 2.0}
    with pytest.raises(ValueError, match=r"^cap_statistics has no 'blue'"):
        effective_alphas(
            means=(0.1, 0.2, 0.3), cap_statistics={"red": 0.1}, blue_compensation=True, **common
        )
    with pytest.raises(ValueError, match=r"^cap_statistics\['red'\] must be finite"):
        effective_alphas(
            means=(0.1, 0.2, 0.3),
            cap_statistics={"red": float("nan")},
            blue_compensation=False,
            **common,
        )
    with pytest.raises(ValueError, match=r"^means needs 3 values"):
        effective_alphas(
            means=(0.1,), cap_statistics={"red": 0.1}, blue_compensation=False, **common
        )
    # extra keys are ignored (WP3.4 may cache both channels, AD-7)
    assert set(
        effective_alphas(
            means=(0.1, 0.2, 0.3),
            cap_statistics={"red": 0.1, "blue": 0.2},
            blue_compensation=False,
            **common,
        )
    ) == {"red"}


class _ProtocolOnly:
    name = "numpy"
    device = "cpu"


def test_inputs_are_checked() -> None:
    backend = NumpyBackend()
    double = np.zeros((4, 4, 3), dtype=np.float64)
    flat = np.zeros((4, 4), dtype=np.float32)
    good = backend.asarray(synthetic(0, (4, 4)))
    calls: list[Callable[[Any, Any], Any]] = [
        lambda b, a: cap_statistics(b, a, blue_compensation=True),
        lambda b, a: compensate_ancuti2018(b, a, means=(0.1, 0.2, 0.3), alphas={"red": 1.0}),
        lambda b, a: compensate_c3(b, a, **C3),
    ]
    for call in calls:
        with pytest.raises(ValueError, match="float32"):
            call(backend, double)
        with pytest.raises(ValueError, match=r"\(H, W, 3\)"):
            call(backend, flat)
        with pytest.raises(TypeError, match=r"clearwater.core backend"):
            call(_ProtocolOnly(), good)


@pytest.mark.gpu
def test_host_array_on_gpu_backend_is_refused() -> None:
    gpu = gpu_backend()
    image = synthetic(0, (4, 4))
    with pytest.raises(TypeError):
        compensate_ancuti2018(gpu, image, means=(0.1, 0.2, 0.3), alphas={"red": 1.0})
    with pytest.raises(TypeError):
        compensate_c3(gpu, image, **C3)
    with pytest.raises(TypeError):
        cap_statistics(gpu, image, blue_compensation=False)


# -- planted wrong implementations (brief task 5; DR-19 item 5) ------------------------------


def check_separate_caps(implementation: Callable[..., dict[str, float]]) -> None:
    alphas = implementation(
        means=(0.05, 0.5, 0.05),
        cap_statistics={"red": 0.4, "blue": 0.4},
        alpha=1.0,
        blue_compensation=True,
        red_gain_cap=2.0,
        blue_gain_cap=None,
    )
    assert alphas["red"] < 1.0
    assert alphas["blue"] == 1.0  # blue's own cap (None) decides, not red's (D52)


def test_planted_one_cap_shared_by_red_and_blue() -> None:
    def shared(**kwargs: Any) -> dict[str, float]:
        return effective_alphas(**{**kwargs, "blue_gain_cap": kwargs["red_gain_cap"]})

    check_separate_caps(effective_alphas)
    assert rejects(check_separate_caps, shared)


def check_c3_has_no_cap(implementation: Callable[..., Any]) -> None:
    backend = NumpyBackend()
    image = synthetic(1)  # near-zero red: an Ancuti cap of 0.1 would bind hard
    a = backend.asarray(image)
    params = Params(method="c3", red_gain_cap=0.1, blue_gain_cap=0.1)
    expected, _ = proto.compensate_c3(a, params)
    out = implementation(backend, a, **C3)
    assert np.array_equal(out, expected)
    assert not any("cap" in name for name in inspect.signature(compensate_c3).parameters)


def test_planted_cap_applied_to_c3() -> None:
    def capped(backend: CoreBackend, a: Any, **kwargs: float) -> Any:
        means = channel_means(backend, a)
        statistic = cap_statistics(backend, a, blue_compensation=False)["red"]
        added_per_alpha = (means[1] - means[0]) * statistic
        scale = min(1.0, 0.1 * means[0] / added_per_alpha)
        return compensate_c3(backend, a, **{**kwargs, "c3_strength": scale})

    check_c3_has_no_cap(compensate_c3)
    assert rejects(check_c3_has_no_cap, capped)


def c3_reference(
    backend: CoreBackend, a: Any, *, matrix: str = "bt709", invert_mask: bool = False, **kw: float
) -> Any:
    """A test-side 3C with two knobs, to plant the BT.601 and inverted-mask defects."""
    forward = rgb_to_ycbcr_matrix(matrix)
    to_rgb = backend.asarray(np.linalg.inv(forward).astype(np.float32))
    ycbcr = backend.rgb_to_ycbcr(a, matrix, "full")
    bright = a.mean(axis=2, dtype=np.float32) > kw["c3_mask_threshold"]
    keep = bright if invert_mask else ~bright
    shape = a.shape
    mask = backend.gaussian_blur(
        keep.astype(np.float32), kw["c3_mask_smooth_fraction"] * min(shape[0], shape[1])
    )
    sigma = kw["c3_kernel_fraction"] * min(shape[0], shape[1])
    kappa = kw["c3_strength"] * kw["kappa"]
    lambda_ = kw["c3_strength"] * kw["lambda_"]
    delta_cb = -lambda_ * mask * backend.gaussian_blur(ycbcr[..., 1], sigma)
    delta_cr = -kappa * mask * backend.gaussian_blur(ycbcr[..., 2], sigma)
    delta = delta_cb[..., None] * to_rgb[:, 1] + delta_cr[..., None] * to_rgb[:, 2]
    return (a + delta).clip(0.0, 1.0).astype(np.float32, copy=False)


def check_c3_against_prototype(implementation: Callable[..., Any]) -> None:
    backend = NumpyBackend()
    image = synthetic(3)
    image[:10] = np.float32(0.95)  # a bright band the mask protects
    a = backend.asarray(image)
    expected, _ = proto.compensate_c3(a, Params(method="c3"))
    assert np.array_equal(implementation(backend, a, **C3), expected)


def test_planted_bt601_in_c3() -> None:
    check_c3_against_prototype(compensate_c3)
    check_c3_against_prototype(c3_reference)  # the knob-free reference is the product
    assert rejects(
        check_c3_against_prototype, lambda b, a, **kw: c3_reference(b, a, matrix="bt601", **kw)
    )


def test_planted_mask_threshold_inverted() -> None:
    assert rejects(
        check_c3_against_prototype, lambda b, a, **kw: c3_reference(b, a, invert_mask=True, **kw)
    )


def check_float32_output(implementation: Callable[..., Any]) -> None:
    backend = NumpyBackend()
    a = backend.asarray(synthetic(0))
    out = implementation(
        backend, a, means=(np.float64(0.2), 0.5, 0.4), alphas={"red": np.float64(0.9)}
    )
    assert out.dtype == np.float32
    expected, _ = proto.compensate_ancuti2018(
        a,
        ancuti_params(),
        proto.Statistics(compensation_means=(0.2, 0.5, 0.4), compensation_alpha={"red": 0.9}),
    )
    assert np.array_equal(out, expected)


def test_planted_float64_leak() -> None:
    def leaky(backend: CoreBackend, a: Any, *, means: Any, alphas: Any) -> Any:
        out = a.astype(np.float64)
        shape = (1.0 - a[..., 0]) * a[..., 1]
        strength = np.float64(alphas["red"]) * np.float64(means[1] - means[0])
        out[..., 0] = (a[..., 0] + strength * shape).clip(0.0, 1.0)
        return out

    check_float32_output(compensate_ancuti2018)
    assert rejects(check_float32_output, leaky)


def clipping_image() -> np.ndarray:
    """Red above green on average, with dark-red, bright-green pixels: the compensation
    (``mean_g - mean_r < 0``) pushes those pixels below 0, so the clip binds. (With alpha <= 1
    and values in [0, 1] it can never push a pixel above 1.)"""
    image = synthetic(0)
    image[..., 0] = np.float32(0.95)
    image[..., 1] = np.float32(0.05)
    image[:5, :, 0] = np.float32(0.0)
    image[:5, :, 1] = np.float32(1.0)
    return image


def check_measured_on_input(chain: Callable[[CoreBackend, Any], Any]) -> None:
    backend = NumpyBackend()
    image = clipping_image()
    a = backend.asarray(image)
    params = ancuti_params(blue_compensation=True, red_gain_cap=None, blue_gain_cap=None)
    expected, info = proto.compensate_ancuti2018(a, params)
    out, means = chain(backend, a)
    assert means == info.channel_means
    assert np.array_equal(out, expected)


def test_planted_means_taken_after_clipping() -> None:
    image = clipping_image()
    a = NumpyBackend().asarray(image)
    green = image[..., 1]
    unclipped = (
        image[..., 0]
        + (channel_means(NumpyBackend(), a)[1] - image[..., 0].mean())
        * (1.0 - image[..., 0])
        * green
    )
    assert (unclipped < 0.0).any()  # the clip binds on this image

    def right(backend: CoreBackend, a: Any) -> Any:
        out, means, _ = ancuti_chain(
            backend, a, blue_compensation=True, red_gain_cap=None, blue_gain_cap=None
        )
        return out, means

    def after_clipping(backend: CoreBackend, a: Any) -> Any:
        first, _, _ = ancuti_chain(
            backend, a, blue_compensation=True, red_gain_cap=None, blue_gain_cap=None
        )
        means = channel_means(backend, first)  # measured on the clipped output
        statistics = cap_statistics(backend, first, blue_compensation=True)
        alphas = effective_alphas(
            means=means,
            cap_statistics=statistics,
            alpha=1.0,
            blue_compensation=True,
            red_gain_cap=None,
            blue_gain_cap=None,
        )
        return compensate_ancuti2018(backend, a, means=means, alphas=alphas), means

    check_measured_on_input(right)
    assert rejects(check_measured_on_input, after_clipping)


# -- Gate 1: results on the device, sync points only where documented ------------------------


@contextmanager
def no_device_sync() -> Iterator[None]:
    import cupyx

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # allow_synchronize is deprecated
        with cupyx.allow_synchronize(False):
            yield


@pytest.mark.gpu
def test_gpu_renders_stay_on_device_without_reading_back() -> None:
    gpu = gpu_backend()  # skips before cupy is imported when it is unavailable
    import cupy

    a = gpu.asarray(synthetic(0))
    means = channel_means(gpu, a)
    with no_device_sync():
        outs = [
            compensate_ancuti2018(gpu, a, means=means, alphas={"red": 0.9, "blue": 0.5}),
            compensate_c3(gpu, a, **C3),
        ]
    for out in outs:
        assert isinstance(out, cupy.ndarray)
        assert out.dtype == np.float32
    with no_device_sync(), pytest.raises(Exception, match="synchroniz"):
        cap_statistics(gpu, a, blue_compensation=False)  # the instrument sees a real read


def test_sync_points_are_the_documented_ones(
    backend: CoreBackend, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``cap_statistics`` reads one scalar per channel; the renders read none."""
    calls: list[str] = []
    real_mean = compensation.mean

    def counted(core: CoreBackend, a: Any) -> float:
        calls.append("mean")
        return real_mean(core, a)

    monkeypatch.setattr(compensation, "mean", counted)
    a = backend.asarray(synthetic(0))
    cap_statistics(backend, a, blue_compensation=False)
    assert calls == ["mean"]
    cap_statistics(backend, a, blue_compensation=True)
    assert calls == ["mean"] * 3
    calls.clear()
    compensate_ancuti2018(backend, a, means=(0.2, 0.5, 0.4), alphas={"red": 1.0, "blue": 1.0})
    compensate_c3(backend, a, **C3)
    assert calls == []
    assert {"channel_means"}.isdisjoint(vars(compensation))  # no means helper in the module


# -- dependency rule (plan 8.1, frame rule 5) ------------------------------------------------


def test_import_loads_nothing_forbidden() -> None:
    code = (
        "import json, sys\n"
        "import clearwater.methods.compensation, clearwater.methods.white_balance\n"
        "top = ['PIL', 'PySide6', 'av', 'cupy', 'cupyx']\n"
        "packages = ('clearwater.io', 'clearwater.jobs', 'clearwater.gui', 'clearwater.config')\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in top\n"
        "             or any(m == p or m.startswith(p + '.') for p in packages))\n"
        "print(json.dumps(bad))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=False
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert json.loads(result.stdout.strip().splitlines()[-1]) == []


# -- Reviewer A round 1 cleanup --------------------------------------------------------------


def test_mixed_type_keys_raise_the_value_error() -> None:
    """R1-1: a non-string key gives the S-3 ValueError, not a TypeError from sorting."""
    backend = NumpyBackend()
    a = backend.asarray(synthetic(0, (4, 4)))
    with pytest.raises(ValueError, match=r"^alphas must name"):
        compensate_ancuti2018(backend, a, means=(0.1, 0.2, 0.3), alphas={"red": 1.0, 7: 1.0})
    with pytest.raises(ValueError, match=r"^cap_statistics has no 'blue'"):
        effective_alphas(
            means=(0.1, 0.2, 0.3),
            cap_statistics={"red": 0.1, 7: 0.2},
            alpha=1.0,
            blue_compensation=True,
            red_gain_cap=2.0,
            blue_gain_cap=2.0,
        )

