"""WP3.2: gray-world white balance and the D99 clamp (spec 6.2 step 2) against the prototype.

The references are computed here by calling the read-only ``tools/prototype`` on seeded
synthetic inputs and the WP2.3 stills; nothing is committed. Closed forms must equal the
prototype's values exactly; the render must match it bit for bit on the same device; CPU
against GPU is AD-11. Planted wrong implementations fail the checks the product passes.
"""

from __future__ import annotations

import inspect
import warnings
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, ClassVar

import numpy as np
import pytest
from PIL import Image as PILImage

from clearwater.core import CoreBackend, NumpyBackend, channel_means
from clearwater.core.backend import _probe_gpu
from clearwater.methods import white_balance
from clearwater.methods.compensation import compensate_c3
from clearwater.methods.white_balance import applied_gains, apply_white_balance, gray_world_gains
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
        image[..., 0] *= np.float32(0.4)
    return image


def grid10(seed: int, shape: tuple[int, int] = (45, 67)) -> np.ndarray:
    """A float32 image on the 10-bit ``n / 1023`` grid (V1's 10-bit input), red kept low."""
    rng = np.random.default_rng(seed)
    codes = rng.integers(0, 1024, (*shape, 3))
    codes[..., 0] = rng.integers(0, 410, shape)
    return codes.astype(np.float32) / np.float32(1023.0)


def read_still(path: Path) -> np.ndarray:
    if "png16" in path.name:
        return read_png16(path)
    with PILImage.open(path) as opened:
        return (np.asarray(opened.convert("RGB"), dtype=np.float32) / np.float32(255.0)).copy()


@pytest.fixture(params=["synthetic-0", "synthetic-1", "grid10-0", *STILLS_16, *STILLS_8])
def image(request: pytest.FixtureRequest, sample: Callable[[str], Path]) -> np.ndarray:
    name = request.param
    if name.startswith("synthetic"):
        return synthetic(int(name[-1]))
    if name.startswith("grid10"):
        return grid10(int(name[-1]))
    return read_still(sample(name))


def balance(
    backend: CoreBackend, a: Any, *, strength: float = 1.0, maximum: float = 3.0
) -> tuple[Any, tuple[float, float, float], tuple[bool, bool, bool]]:
    """Measure, closed form and render in the order WP3.4 will call them."""
    gains, clamped = applied_gains(
        gray_world_gains(channel_means(backend, a)),
        white_balance_strength=strength,
        max_white_balance_gain=maximum,
    )
    return apply_white_balance(backend, a, gains), gains, clamped


def host(backend: CoreBackend, a: Any) -> np.ndarray:
    return np.asarray(backend.to_host(a))


def assert_identical(actual: np.ndarray, expected: np.ndarray) -> None:
    assert actual.dtype == np.float32
    assert expected.dtype == np.float32
    assert actual.shape == expected.shape
    assert np.array_equal(actual, expected), f"max abs diff {np.abs(actual - expected).max()}"


def rejects(
    check: Callable[[Callable[..., Any]], None], implementation: Callable[..., Any]
) -> bool:
    """Whether ``check`` fails on ``implementation`` (a planted wrong implementation)."""
    try:
        check(implementation)
    except AssertionError:
        return True
    return False


# -- product against prototype ---------------------------------------------------------------


@pytest.mark.parametrize(("strength", "maximum"), [(1.0, 3.0), (0.5, 3.0), (1.0, 1.2), (1.7, 2.0)])
def test_measure_closed_form_and_render_match_prototype(
    backend: CoreBackend, image: np.ndarray, strength: float, maximum: float
) -> None:
    a = backend.asarray(image)
    params = Params(white_balance_strength=strength, max_white_balance_gain=maximum)
    expected, info = proto.white_balance(a, params)
    means = channel_means(backend, a)
    assert means == info.channel_means
    gray_world = gray_world_gains(means)
    assert gray_world == info.gray_world_gains
    gains, clamped = applied_gains(
        gray_world, white_balance_strength=strength, max_white_balance_gain=maximum
    )
    assert gains == info.applied_gains
    assert clamped == info.clamped
    assert_identical(host(backend, apply_white_balance(backend, a, gains)), host(backend, expected))


def test_render_matches_prototype_on_supplied_gains(
    backend: CoreBackend, image: np.ndarray
) -> None:
    """The clamp applies to supplied (smoothed) gains as to measured ones (6.2, AD-6)."""
    a = backend.asarray(image)
    supplied = (3.6, 0.93, 1.21)
    params = Params(white_balance_strength=0.8, max_white_balance_gain=2.5)
    expected, info = proto.white_balance(a, params, proto.Statistics(white_balance_gains=supplied))
    gains, clamped = applied_gains(supplied, white_balance_strength=0.8, max_white_balance_gain=2.5)
    assert gains == info.applied_gains
    assert clamped == info.clamped == (True, False, False)
    assert_identical(host(backend, apply_white_balance(backend, a, gains)), host(backend, expected))


def test_gray_world_on_supplied_means_matches_prototype() -> None:
    a = NumpyBackend().asarray(synthetic(0))
    supplied = (0.12, 0.45, 0.51)
    _, info = proto.white_balance(a, Params(), proto.Statistics(white_balance_means=supplied))
    assert gray_world_gains(supplied) == info.gray_world_gains


@pytest.mark.parametrize("shape", [(1, 1), (1, 7), (7, 1), (7, 5)])
def test_tiny_and_odd_sizes_match_prototype(backend: CoreBackend, shape: tuple[int, int]) -> None:
    a = backend.asarray(synthetic(8, shape))
    expected, _ = proto.white_balance(a, Params())
    assert_identical(host(backend, balance(backend, a)[0]), host(backend, expected))


def test_after_c3_matches_prototype(backend: CoreBackend, image: np.ndarray) -> None:
    """Steps 1 and 2 chained with 3C, the default method (D16)."""
    a = backend.asarray(image)
    compensated, _ = proto.compensate_c3(a, Params())
    expected, _ = proto.white_balance(compensated, Params())
    out = balance(backend, compensate_c3(backend, a, **C3))[0]
    assert_identical(host(backend, out), host(backend, expected))


# -- CPU against GPU (AD-11) and reproducibility (N10) ---------------------------------------


@pytest.mark.gpu
def test_cpu_and_gpu_agree_within_ad11(image: np.ndarray) -> None:
    gpu = gpu_backend()
    cpu = NumpyBackend()
    out_cpu, gains_cpu, _ = balance(cpu, cpu.asarray(image))
    out_gpu, gains_gpu, _ = balance(gpu, gpu.asarray(image))
    assert np.allclose(gains_cpu, gains_gpu, rtol=1e-6)
    difference = np.abs(host(cpu, out_cpu).astype(np.float64) - host(gpu, out_gpu)).reshape(-1, 3)
    assert difference.max(axis=0).max() <= AD11_MAX
    assert difference.mean(axis=0).max() <= AD11_MEAN


def test_same_device_twice_is_bit_identical(backend: CoreBackend) -> None:
    image = synthetic(6, (61, 83))
    first = balance(backend, backend.asarray(image))[0]
    second = balance(backend, backend.asarray(image))[0]
    assert_identical(host(backend, first), host(backend, second))


# -- V1 edge cases ---------------------------------------------------------------------------


def test_uniform_image_becomes_gray(backend: CoreBackend) -> None:
    image = np.empty((9, 13, 3), dtype=np.float32)
    image[...] = np.asarray([0.2, 0.6, 0.4], dtype=np.float32)
    a = backend.asarray(image)
    out, _, clamped = balance(backend, a)
    result = host(backend, out)
    assert clamped == (False, False, False)
    assert np.allclose(result, 0.4, atol=1e-6)
    expected, _ = proto.white_balance(a, Params())
    assert_identical(result, host(backend, expected))


@pytest.mark.parametrize("red", [0.0, 1e-9, 1e-7])
def test_near_zero_red_hits_the_floor_and_the_clamp(backend: CoreBackend, red: float) -> None:
    image = synthetic(2)
    image[..., 0] = np.float32(red)
    a = backend.asarray(image)
    means = channel_means(backend, a)
    assert means[0] < 1e-6
    gray_world = gray_world_gains(means)
    assert gray_world[0] == pytest.approx(sum(means) / 3.0 / 1e-6, rel=1e-12)  # the 1e-6 floor
    out, gains, clamped = balance(backend, a)
    assert gains[0] == 3.0
    assert clamped[0] is True
    assert np.isfinite(host(backend, out)).all()
    expected, _ = proto.white_balance(a, Params())
    assert_identical(host(backend, out), host(backend, expected))


def test_clamp_binds_as_d99_says() -> None:
    gains, clamped = applied_gains(
        (5.0, 1.0, 0.25), white_balance_strength=1.0, max_white_balance_gain=3.0
    )
    assert gains == (3.0, 1.0, 0.25)
    assert clamped == (True, False, False)
    gains, clamped = applied_gains(
        (2.9, 1.0, 0.25), white_balance_strength=1.0, max_white_balance_gain=3.0
    )
    assert gains == (2.9, 1.0, 0.25)
    assert clamped == (False, False, False)


# -- V9 neutrality ---------------------------------------------------------------------------


def test_strength_zero_is_identity(backend: CoreBackend, image: np.ndarray) -> None:
    a = backend.asarray(image)
    out, gains, clamped = balance(backend, a, strength=0.0)
    assert gains == (1.0, 1.0, 1.0)
    assert clamped == (False, False, False)
    assert_identical(host(backend, out), image)


# -- supplied values and inputs (S-1, S-3) ---------------------------------------------------


@pytest.mark.parametrize("values", [(1.0, 2.0), (1.0, 2.0, 3.0, 4.0), (1.0, float("nan"), 1.0)])
def test_bad_supplied_values_are_refused(values: tuple[float, ...]) -> None:
    backend = NumpyBackend()
    a = backend.asarray(synthetic(0, (4, 4)))
    with pytest.raises(ValueError, match=r"^means"):
        gray_world_gains(values)
    with pytest.raises(ValueError, match=r"^gray_world"):
        applied_gains(values, white_balance_strength=1.0, max_white_balance_gain=3.0)
    with pytest.raises(ValueError, match=r"^gains"):
        apply_white_balance(backend, a, values)


class _ProtocolOnly:
    name = "numpy"
    device = "cpu"


def test_inputs_are_checked() -> None:
    backend = NumpyBackend()
    with pytest.raises(ValueError, match="float32"):
        apply_white_balance(backend, np.zeros((4, 4, 3)), (1.0, 1.0, 1.0))
    with pytest.raises(ValueError, match=r"\(H, W, 3\)"):
        apply_white_balance(backend, np.zeros((4, 4), dtype=np.float32), (1.0, 1.0, 1.0))
    with pytest.raises(TypeError, match=r"clearwater.core backend"):
        apply_white_balance(
            _ProtocolOnly(),
            backend.asarray(synthetic(0, (4, 4))),
            (1.0, 1.0, 1.0),
        )


@pytest.mark.gpu
def test_host_array_on_gpu_backend_is_refused() -> None:
    with pytest.raises(TypeError):
        apply_white_balance(gpu_backend(), synthetic(0, (4, 4)), (1.0, 1.0, 1.0))


def test_signatures() -> None:
    for function in (applied_gains,):
        for parameter in list(inspect.signature(function).parameters.values())[1:]:
            assert parameter.kind is inspect.Parameter.KEYWORD_ONLY
            assert parameter.default is inspect.Parameter.empty


# -- planted wrong implementations (brief task 5) --------------------------------------------


def check_clamp_after_strength(implementation: Callable[..., Any]) -> None:
    gains, clamped = implementation(
        (4.0, 1.0, 0.5), white_balance_strength=0.5, max_white_balance_gain=3.0
    )
    assert gains == (2.5, 1.0, 0.75)  # 1 + 0.5 * (4 - 1) = 2.5, under the clamp
    assert clamped == (False, False, False)


def test_planted_clamp_before_strength() -> None:
    def early(
        gray_world: Any, *, white_balance_strength: float, max_white_balance_gain: float
    ) -> Any:
        clamped = tuple(min(g, max_white_balance_gain) for g in gray_world)
        gains = tuple(1.0 + white_balance_strength * (g - 1.0) for g in clamped)
        return gains, tuple(g > max_white_balance_gain for g in gray_world)

    check_clamp_after_strength(applied_gains)
    assert rejects(check_clamp_after_strength, early)


def check_no_lower_clamp(implementation: Callable[..., Any]) -> None:
    gains, clamped = implementation(
        (0.25, 1.0, 0.5), white_balance_strength=1.0, max_white_balance_gain=3.0
    )
    assert gains == (0.25, 1.0, 0.5)  # D99 limits the maximum only
    assert clamped == (False, False, False)


def test_planted_gains_clamped_below_one() -> None:
    def floor_at_one(gray_world: Any, **kwargs: float) -> Any:
        gains, clamped = applied_gains(gray_world, **kwargs)
        return tuple(max(g, 1.0) for g in gains), clamped

    def symmetric(gray_world: Any, **kwargs: float) -> Any:
        gains, clamped = applied_gains(gray_world, **kwargs)
        low = 1.0 / kwargs["max_white_balance_gain"]
        return tuple(max(g, low) for g in gains), clamped

    check_no_lower_clamp(applied_gains)
    assert rejects(check_no_lower_clamp, floor_at_one)
    assert rejects(check_no_lower_clamp, symmetric)


def check_float32_output(implementation: Callable[..., Any]) -> None:
    backend = NumpyBackend()
    a = backend.asarray(synthetic(0))
    gains = (np.float64(1.7), np.float64(0.8), np.float64(1.1))
    out = implementation(backend, a, gains)
    assert out.dtype == np.float32
    expected, _ = proto.white_balance(
        a, Params(), proto.Statistics(white_balance_gains=(1.7, 0.8, 1.1))
    )
    assert np.array_equal(out, expected)


def test_planted_float64_leak() -> None:
    def leaky(backend: CoreBackend, a: Any, gains: Any) -> Any:
        return (a * np.asarray(gains, dtype=np.float64)).clip(0.0, 1.0)

    check_float32_output(apply_white_balance)
    assert rejects(check_float32_output, leaky)


def clipping_image() -> np.ndarray:
    """Weak red with a few bright-red pixels: the red gain pushes them past 1 (the clip binds)."""
    image = synthetic(0)
    image[:4, :, 0] = np.float32(0.9)
    return image


def check_measured_on_input(chain: Callable[[CoreBackend, Any], Any]) -> None:
    backend = NumpyBackend()
    a = backend.asarray(clipping_image())
    expected, info = proto.white_balance(a, Params())
    out, means = chain(backend, a)
    assert means == info.channel_means
    assert np.array_equal(out, expected)


def test_planted_means_taken_after_clipping() -> None:
    backend = NumpyBackend()
    a = backend.asarray(clipping_image())
    gains, _ = applied_gains(
        gray_world_gains(channel_means(backend, a)),
        white_balance_strength=1.0,
        max_white_balance_gain=3.0,
    )
    assert (a * np.float32(gains[0]) > 1.0).any()  # the clip binds on this image

    def right(backend: CoreBackend, a: Any) -> Any:
        means = channel_means(backend, a)
        return balance(backend, a)[0], means

    def after_clipping(backend: CoreBackend, a: Any) -> Any:
        means = channel_means(backend, balance(backend, a)[0])  # the clipped output's means
        gains, _ = applied_gains(
            gray_world_gains(means), white_balance_strength=1.0, max_white_balance_gain=3.0
        )
        return apply_white_balance(backend, a, gains), means

    check_measured_on_input(right)
    assert rejects(check_measured_on_input, after_clipping)


# -- Gate 1 ----------------------------------------------------------------------------------


@contextmanager
def no_device_sync() -> Iterator[None]:
    import cupyx

    with warnings.catch_warnings():
        warnings.simplefilter("ignore", UserWarning)  # allow_synchronize is deprecated
        with cupyx.allow_synchronize(False):
            yield


@pytest.mark.gpu
def test_gpu_render_stays_on_device_without_reading_back() -> None:
    gpu = gpu_backend()  # skips before cupy is imported when it is unavailable
    import cupy

    a = gpu.asarray(synthetic(0))
    with no_device_sync():
        out = apply_white_balance(gpu, a, (1.4, 0.9, 1.1))
    assert isinstance(out, cupy.ndarray)
    assert out.dtype == np.float32


def test_render_reads_no_whole_frame_value() -> None:
    """The module holds no reduction helper: the render cannot measure (AD-4, preview = export)."""
    assert {"channel_means", "mean"}.isdisjoint(vars(white_balance))


class UfuncSpy(np.ndarray):
    """A NumPy array that records every ufunc reduction made on it or on arrays derived from it
    (``<ufunc>.reduce`` with ``axis`` normalised into the keywords; R1-3)."""

    log: ClassVar[list[tuple[str, str, int, Any]]] = []

    def __array_ufunc__(self, ufunc: Any, method: str, *inputs: Any, **kwargs: Any) -> Any:
        ndim = max(getattr(x, "ndim", 0) for x in inputs)
        UfuncSpy.log.append((ufunc.__name__, method, ndim, kwargs.get("axis", 0)))
        args = [x.view(np.ndarray) if isinstance(x, UfuncSpy) else x for x in inputs]
        if "out" in kwargs:
            kwargs["out"] = tuple(
                o.view(np.ndarray) if isinstance(o, UfuncSpy) else o for o in kwargs["out"]
            )
        result = getattr(ufunc, method)(*args, **kwargs)
        return result.view(UfuncSpy) if isinstance(result, np.ndarray) else result


def check_render_never_measures(render: Callable[[CoreBackend, Any, Any], Any]) -> None:
    backend = NumpyBackend()
    UfuncSpy.log = []
    out = render(backend, synthetic(0).view(UfuncSpy), (1.4, 0.9, 1.1))
    assert isinstance(out, np.ndarray)
    assert UfuncSpy.log, "the spy saw no ufunc call: the instrument is not live"
    assert [e for e in UfuncSpy.log if e[1] in ("reduce", "accumulate", "reduceat")] == []


def test_render_never_measures_a_whole_frame_value() -> None:
    """R1-3: the white-balance render makes no reduction at all."""
    check_render_never_measures(apply_white_balance)

    def measuring(backend: CoreBackend, a: Any, gains: Any) -> Any:
        means = channel_means(backend, a)
        return apply_white_balance(
            backend,
            a,
            applied_gains(
                gray_world_gains(means), white_balance_strength=1.0, max_white_balance_gain=3.0
            )[0],
        )

    assert rejects(check_render_never_measures, measuring)


# -- NumPy-scalar and int parameters of the closed form (the audit's item 2) ------------------

GAIN_PARAMS = ("white_balance_strength", "max_white_balance_gain", "gray_world")


@pytest.mark.parametrize("name", [*GAIN_PARAMS, "all"])
@pytest.mark.parametrize("scalar", [np.float64, np.float32, int])
def test_applied_gains_scalar_parameters_equal_python_floats(scalar: type, name: str) -> None:
    """The strength, the clamp and the gains as np.float64, np.float32 or int act as floats."""

    def as_scalar(value: float) -> Any:
        return max(1, round(value)) if scalar is int else scalar(value)

    names = GAIN_PARAMS if name == "all" else (name,)
    base: dict[str, Any] = {
        "white_balance_strength": 0.93,
        "max_white_balance_gain": 2.3,
        "gray_world": (1.3, 0.9, 3.4),
    }
    typed = {
        k: (tuple(as_scalar(g) for g in v) if k == "gray_world" else as_scalar(v))
        if k in names
        else v
        for k, v in base.items()
    }
    gray_world = typed.pop("gray_world")
    plain = {k: float(v) for k, v in typed.items()}
    expected = applied_gains(tuple(float(g) for g in gray_world), **plain)
    actual = applied_gains(gray_world, **typed)
    assert actual == expected
    assert all(type(g) is float for g in actual[0])
