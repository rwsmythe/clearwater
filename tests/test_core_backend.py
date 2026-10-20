"""WP3.1: the IF-2 backends against independent references, edge cases and planted defects.

Each ``check_*`` function is one claim about a backend; the tests run it on both backends and
the planted-defect tests (bottom) prove it fails on a wrong implementation, by name.
"""

from __future__ import annotations

import inspect
import math
from collections.abc import Callable
from typing import Any

import numpy as np
import pytest
from scipy import ndimage as scipy_ndimage

import clearwater.core.backend as backend_module
from clearwater.core import CoreBackend, NumpyBackend, memory_estimate_bytes
from clearwater.core.backend import _probe_gpu
from clearwater.interfaces.backend import ArrayBackend

AD11_MAX = 2e-3
AD11_MEAN = 2e-4


def gpu_backend() -> CoreBackend:
    backend, reason = _probe_gpu()
    if backend is None:
        pytest.skip(reason)
    return backend


@pytest.fixture(params=["numpy", pytest.param("cupy", marks=pytest.mark.gpu)])
def backend(request: pytest.FixtureRequest) -> CoreBackend:
    if request.param == "numpy":
        return NumpyBackend()
    return gpu_backend()


def rng_image(shape: tuple[int, ...], seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).random(shape, dtype=np.float32)


def host(backend: CoreBackend, a: Any) -> np.ndarray:
    return np.asarray(backend.to_host(a))


# -- independent float64 references -------------------------------------------------------------


def ref_correlate(a: np.ndarray, kernel: np.ndarray, axis: int) -> np.ndarray:
    """Correlate along ``axis`` with symmetric borders (``d c b a | a b c d``), float64."""
    radius = (kernel.size - 1) // 2
    pad = [(0, 0)] * a.ndim
    pad[axis] = (radius, radius)
    padded = np.pad(a.astype(np.float64), pad, mode="symmetric")
    out = np.zeros(a.shape, dtype=np.float64)
    n = a.shape[axis]
    for i, weight in enumerate(kernel.astype(np.float64)):
        index = [slice(None)] * a.ndim
        index[axis] = slice(i, i + n)
        out += padded[tuple(index)] * weight
    return out


def ref_gaussian(a: np.ndarray, sigma: float) -> np.ndarray:
    radius = int(4.0 * sigma + 0.5)
    x = np.arange(-radius, radius + 1, dtype=np.float64)
    kernel = np.exp(-0.5 * (x / sigma) ** 2)
    kernel /= kernel.sum()
    return ref_correlate(ref_correlate(a, kernel, 0), kernel, 1)


BINOMIAL = np.array([1, 4, 6, 4, 1], dtype=np.float64) / 16.0


def ref_reduce(a: np.ndarray) -> np.ndarray:
    return ref_correlate(ref_correlate(a, BINOMIAL, 0), BINOMIAL, 1)[::2, ::2]


def ref_expand(a: np.ndarray, shape: tuple[int, int]) -> np.ndarray:
    up = np.zeros(shape + a.shape[2:], dtype=np.float64)
    up[::2, ::2] = a
    indicator = np.zeros(shape, dtype=np.float64)
    indicator[::2, ::2] = 1.0
    norm = ref_correlate(ref_correlate(indicator, BINOMIAL, 0), BINOMIAL, 1)
    blurred = ref_correlate(ref_correlate(up, BINOMIAL, 0), BINOMIAL, 1)
    return blurred / (norm[..., None] if blurred.ndim == 3 else norm)


def ref_percentile(a: np.ndarray, q: float) -> float:
    """R-7: ``h = (n - 1) q / 100``, linear between the order statistics."""
    values = np.sort(a.astype(np.float64).ravel())
    h = (values.size - 1) * q / 100.0
    low = math.floor(h)
    high = min(low + 1, values.size - 1)
    return float(values[low] + (h - low) * (values[high] - values[low]))


# -- the named checks ------------------------------------------------------------------------------


def check_gaussian_reference(backend: CoreBackend) -> None:
    """Gaussian: the radius rule int(4 sigma + 0.5) and symmetric borders, against float64.

    sigma 1.1 (radius 4; a ceil rule gives 5) and 1.15 (radius 5; a floor rule gives 4); the
    border band is where a wrap or constant border differs.
    """
    image = rng_image((23, 31, 3), seed=1)
    for sigma in (1.1, 1.15, 3.0):
        out = host(backend, backend.gaussian_blur(backend.asarray(image), sigma))
        difference = float(np.abs(out - ref_gaussian(image, sigma)).max())
        assert difference < 1e-6, f"check_gaussian_reference: sigma {sigma}, max {difference:.3g}"


def check_reduce_reference(backend: CoreBackend) -> None:
    """pyramid_reduce against a float64 [1 4 6 4 1]/16 with symmetric borders, odd sizes."""
    for shape in ((23, 31, 3), (8, 6), (5, 1, 3), (1, 1)):
        image = rng_image(shape, seed=2)
        out = host(backend, backend.pyramid_reduce(backend.asarray(image)))
        assert out.shape == ((shape[0] + 1) // 2, (shape[1] + 1) // 2, *shape[2:])
        difference = float(np.abs(out - ref_reduce(image)).max())
        assert difference < 1e-6, f"check_reduce_reference: {shape}, max {difference:.3g}"


def check_expand_reference(backend: CoreBackend) -> None:
    """pyramid_expand against the float64 zero-insert, filter, normalise; odd targets."""
    for target, channels in (((23, 31), (3,)), ((8, 6), ()), ((5, 1), (3,)), ((1, 1), ())):
        coarse_shape = ((target[0] + 1) // 2, (target[1] + 1) // 2, *channels)
        coarse = rng_image(coarse_shape, seed=3)
        out = host(backend, backend.pyramid_expand(backend.asarray(coarse), target))
        assert out.shape == (*target, *channels)
        difference = float(np.abs(out - ref_expand(coarse, target)).max())
        assert difference < 1e-6, f"check_expand_reference: {target}, max {difference:.3g}"


BT709_ROWS = np.array(
    [[0.2126, 0.7152, 0.0722], [-0.1145722, -0.3854278, 0.5], [0.5, -0.4541529, -0.0458471]]
)
BT601_ROWS = np.array(
    [[0.299, 0.587, 0.114], [-0.1687359, -0.3312641, 0.5], [0.5, -0.4186876, -0.0813124]]
)


def check_ycbcr_matrices(backend: CoreBackend) -> None:
    """Each row of each matrix, read through unit RGB inputs, against the published values."""
    eye = backend.asarray(np.eye(3, dtype=np.float32).reshape(1, 3, 3))
    for matrix, rows in (("bt709", BT709_ROWS), ("bt601", BT601_ROWS)):
        full = host(backend, backend.rgb_to_ycbcr(eye, matrix, "full"))[0]
        # full[i] is the YCbCr of the i-th unit colour, so its transpose is the matrix.
        np.testing.assert_allclose(
            full.T, rows, atol=1e-6, err_msg=f"check_ycbcr_matrices: {matrix} full"
        )
        limited = host(backend, backend.rgb_to_ycbcr(eye, matrix, "limited"))[0].T
        expected = rows * np.array([[219 / 255], [224 / 255], [224 / 255]])
        np.testing.assert_allclose(
            limited - np.array([[16 / 255], [0.0], [0.0]]),
            expected,
            atol=1e-6,
            err_msg=f"check_ycbcr_matrices: {matrix} limited",
        )


def check_percentile_reference(backend: CoreBackend) -> None:
    """R-7 over the whole array (all channels jointly), float32 out, on the device."""
    image = rng_image((9, 7, 3), seed=4)
    q = [0.0, 0.5, 25.0, 33.3, 50.0, 99.5, 100.0]
    out = backend.percentile(backend.asarray(image), q)
    assert isinstance(out, backend.xp.ndarray), "check_percentile_reference: left the device"
    assert out.dtype == np.float32, f"check_percentile_reference: dtype {out.dtype}"
    values = host(backend, out)
    expected = np.array([ref_percentile(image, value) for value in q], dtype=np.float32)
    np.testing.assert_array_equal(values, expected, err_msg="check_percentile_reference")


def check_percentile_cast_point(backend: CoreBackend) -> None:
    """R0-8 (CHARC): R-7 at the native precision, cast to float32 once, at the return.

    The result must equal ``float32(xp.percentile(a, q))`` (float64 on NumPy and CuPy) bit for
    bit at every q; an interpolation done in float32 rounds differently at some of them.
    """
    image = backend.asarray(rng_image((31, 29, 3), seed=12))
    q = [float(value) for value in np.linspace(0.0, 100.0, 401)]
    native = backend.xp.percentile(image, q, method="linear")
    assert native.dtype == np.float64, f"check_percentile_cast_point: native {native.dtype}"
    expected = host(backend, native.astype(np.float32))
    got = host(backend, backend.percentile(image, q))
    mismatches = int(np.count_nonzero(got != expected))
    assert mismatches == 0, f"check_percentile_cast_point: {mismatches} of {len(q)} differ"


def check_float32_out(backend: CoreBackend) -> None:
    """Every IF-2 image method returns float32."""
    image = backend.asarray(rng_image((9, 11, 3), seed=5))
    outputs = {
        "asarray": image,
        "gaussian_blur": backend.gaussian_blur(image, 1.5),
        "pyramid_reduce": backend.pyramid_reduce(image),
        "pyramid_expand": backend.pyramid_expand(backend.pyramid_reduce(image), (9, 11)),
        "rgb_to_ycbcr": backend.rgb_to_ycbcr(image, "bt709", "limited"),
        "ycbcr_to_rgb": backend.ycbcr_to_rgb(image, "bt601", "limited"),
        "percentile": backend.percentile(image, [1.0, 99.0]),
    }
    for name, out in outputs.items():
        assert out.dtype == np.float32, f"check_float32_out: {name} returned {out.dtype}"


# -- the checks on both backends ------------------------------------------------------------------


def test_gaussian_matches_reference(backend: CoreBackend) -> None:
    check_gaussian_reference(backend)


def test_reduce_matches_reference(backend: CoreBackend) -> None:
    check_reduce_reference(backend)


def test_expand_matches_reference(backend: CoreBackend) -> None:
    check_expand_reference(backend)


def test_ycbcr_matrices(backend: CoreBackend) -> None:
    check_ycbcr_matrices(backend)


def test_percentile_matches_r7(backend: CoreBackend) -> None:
    check_percentile_reference(backend)


def test_percentile_cast_point(backend: CoreBackend) -> None:
    check_percentile_cast_point(backend)


def test_float32_out(backend: CoreBackend) -> None:
    check_float32_out(backend)


# -- behaviour and edge cases (V1) ---------------------------------------------------------------


def test_identity_and_names() -> None:
    cpu = NumpyBackend()
    assert (cpu.name, cpu.device) == ("numpy", "cpu")
    assert isinstance(cpu, ArrayBackend)
    assert cpu.free_device_bytes() is None


@pytest.mark.gpu
def test_gpu_identity_and_free_memory() -> None:
    gpu = gpu_backend()
    assert gpu.name == "cupy"
    assert gpu.device.startswith("cuda:")
    assert isinstance(gpu, ArrayBackend)
    free = gpu.free_device_bytes()
    assert isinstance(free, int) and free > 0


def test_asarray_refuses_other_dtypes(backend: CoreBackend) -> None:
    for dtype in (np.float64, np.float16, np.uint16):
        with pytest.raises(ValueError, match="float32"):
            backend.asarray([1.0, 2.0], dtype=dtype)
    out = backend.asarray(np.array([[1, 2]], dtype=np.uint16))
    assert out.dtype == np.float32 and isinstance(out, backend.xp.ndarray)


IMAGE_METHODS: dict[str, Callable[[CoreBackend, Any], Any]] = {
    "gaussian_blur": lambda b, a: b.gaussian_blur(a, 1.0),
    "pyramid_reduce": lambda b, a: b.pyramid_reduce(a),
    "pyramid_expand": lambda b, a: b.pyramid_expand(a, (2 * a.shape[0], 2 * a.shape[1])),
    "rgb_to_ycbcr": lambda b, a: b.rgb_to_ycbcr(a, "bt709", "full"),
    "ycbcr_to_rgb": lambda b, a: b.ycbcr_to_rgb(a, "bt709", "full"),
    "percentile": lambda b, a: b.percentile(a, [50.0]),
    "to_host": lambda b, a: b.to_host(a),  # round 1 F5: the way out checks float32 too
}


@pytest.mark.parametrize("method", sorted(IMAGE_METHODS))
def test_methods_refuse_non_float32(backend: CoreBackend, method: str) -> None:
    leaked = backend.xp.asarray(rng_image((4, 6, 3)), dtype=np.float64)
    with pytest.raises(ValueError, match="float32"):
        IMAGE_METHODS[method](backend, leaked)


@pytest.mark.gpu
@pytest.mark.parametrize("method", sorted(IMAGE_METHODS))
def test_methods_refuse_the_other_device(method: str) -> None:
    gpu = gpu_backend()
    cpu = NumpyBackend()
    image = rng_image((4, 6, 3))
    with pytest.raises(TypeError, match="cupy arrays"):
        IMAGE_METHODS[method](gpu, image)
    with pytest.raises(TypeError, match="numpy arrays"):
        IMAGE_METHODS[method](cpu, gpu.asarray(image))
    with pytest.raises(TypeError):
        cpu.to_host(gpu.asarray(image))
    with pytest.raises(TypeError):
        gpu.to_host(image)
    with pytest.raises(TypeError, match="does not download"):
        cpu.asarray(gpu.asarray(image))


def test_tiny_sigma_is_identity_and_refusals(backend: CoreBackend) -> None:
    image = backend.asarray(rng_image((7, 5, 3), seed=6))
    for sigma in (1e-6, 0.1, 0.124):  # radius int(4 sigma + 0.5) == 0: the kernel [1]
        out = host(backend, backend.gaussian_blur(image, sigma))
        assert out.tobytes() == host(backend, image).tobytes(), sigma
    # From 1/8 px the radius is 1; the outer taps only matter once they reach float32 size.
    out = host(backend, backend.gaussian_blur(image, 0.3))
    assert out.tobytes() != host(backend, image).tobytes()
    for bad in (0.0, -1.0, math.nan, math.inf, (2**23 + 1) / 4.0):
        with pytest.raises(ValueError, match="sigma"):
            backend.gaussian_blur(image, bad)
    backend_module.check_sigma(2**23 / 4.0 - 0.2)  # radius exactly 2 ** 23 is accepted


def test_uniform_image_stays_uniform(backend: CoreBackend) -> None:
    for value in (0.0, 0.37, 1.0):
        image = backend.asarray(np.full((13, 9, 3), value, dtype=np.float32))
        for out in (
            backend.gaussian_blur(image, 2.5),
            backend.pyramid_reduce(image),
            backend.pyramid_expand(backend.pyramid_reduce(image), (13, 9)),
        ):
            assert float(np.abs(host(backend, out) - value).max()) < 1e-6
        p = host(backend, backend.percentile(image, [0.5, 50.0, 99.5]))
        assert np.all(p == np.float32(value))


def test_edge_inputs_stay_finite_and_shaped(backend: CoreBackend) -> None:
    near_zero_red = rng_image((11, 17, 3), seed=7)
    near_zero_red[..., 0] *= 1e-4
    sixteen_bit = (np.random.default_rng(8).integers(0, 65536, (5, 3, 3)) / 65535.0).astype(
        np.float32
    )
    for image in (near_zero_red, sixteen_bit, rng_image((1, 1, 3)), rng_image((1, 7, 3))):
        a = backend.asarray(image)
        h, w = image.shape[:2]
        outputs = [
            backend.gaussian_blur(a, 5.0),
            backend.pyramid_expand(backend.pyramid_reduce(a), (h, w)),
            backend.ycbcr_to_rgb(backend.rgb_to_ycbcr(a, "bt709", "full"), "bt709", "full"),
        ]
        for out in outputs:
            values = host(backend, out)
            assert values.shape == image.shape and np.all(np.isfinite(values))
        assert float(np.abs(host(backend, outputs[2]) - image).max()) < 1e-5


def test_maps_and_images(backend: CoreBackend) -> None:
    image = rng_image((10, 7, 3), seed=9)
    a = backend.asarray(image)
    m = backend.asarray(np.ascontiguousarray(image[..., 1]))
    blur_image = host(backend, backend.gaussian_blur(a, 1.7))
    blur_map = host(backend, backend.gaussian_blur(m, 1.7))
    np.testing.assert_array_equal(blur_map, blur_image[..., 1])  # spatial axes only
    reduced = host(backend, backend.pyramid_reduce(m))
    np.testing.assert_array_equal(reduced, host(backend, backend.pyramid_reduce(a))[..., 1])
    coarse = backend.pyramid_reduce(m)
    assert host(backend, backend.pyramid_expand(coarse, (10, 7))).shape == (10, 7)
    for bad in (np.zeros((3,), np.float32), np.zeros((2, 2, 2, 2), np.float32)):
        with pytest.raises(ValueError, match="shape"):
            backend.gaussian_blur(backend.asarray(bad), 1.0)


def test_expand_refuses_a_mismatched_shape(backend: CoreBackend) -> None:
    coarse = backend.asarray(rng_image((5, 4, 3)))
    for shape in ((11, 8), (8, 8), (10, 6)):
        with pytest.raises(ValueError, match="does not expand"):
            backend.pyramid_expand(coarse, shape)
    backend.pyramid_expand(coarse, (9, 7))
    backend.pyramid_expand(coarse, (10, 8))


@pytest.mark.parametrize("matrix", ["bt709", "bt601"])
@pytest.mark.parametrize("range_", ["full", "limited"])
def test_ycbcr_round_trip(backend: CoreBackend, matrix: str, range_: str) -> None:
    image = rng_image((16, 12, 3), seed=10)
    a = backend.asarray(image)
    there = backend.rgb_to_ycbcr(a, matrix, range_)
    back = host(backend, backend.ycbcr_to_rgb(there, matrix, range_))
    assert float(np.abs(back - image).max()) < 2e-6


def test_ycbcr_limited_landmarks(backend: CoreBackend) -> None:
    colours = np.array([[[1, 1, 1], [0, 0, 0], [0.5, 0.5, 0.5], [1, 0, 0]]], dtype=np.float32)
    for matrix in ("bt709", "bt601"):
        out = host(backend, backend.rgb_to_ycbcr(backend.asarray(colours), matrix, "limited"))
        np.testing.assert_allclose(out[0, 0], [235 / 255, 0, 0], atol=1e-6)
        np.testing.assert_allclose(out[0, 1], [16 / 255, 0, 0], atol=1e-6)
        np.testing.assert_allclose(out[0, 2, 1:], [0, 0], atol=1e-6)
        np.testing.assert_allclose(out[0, 3, 2], 112 / 255, atol=1e-6)  # red: Cr' = 224/255 * 0.5


def test_ycbcr_refuses_unknown_names(backend: CoreBackend) -> None:
    a = backend.asarray(rng_image((2, 2, 3)))
    for matrix in ("identity", "unknown", "bt2020", "BT709"):
        with pytest.raises(ValueError, match="matrix"):
            backend.rgb_to_ycbcr(a, matrix, "full")
        with pytest.raises(ValueError, match="matrix"):
            backend.ycbcr_to_rgb(a, matrix, "full")
    for range_ in ("pc", "tv", "FULL"):
        with pytest.raises(ValueError, match="range"):
            backend.rgb_to_ycbcr(a, "bt709", range_)
    with pytest.raises(ValueError, match="shape"):
        backend.rgb_to_ycbcr(backend.asarray(rng_image((2, 2, 4))), "bt709", "full")


def test_percentile_refusals(backend: CoreBackend) -> None:
    a = backend.asarray(rng_image((3, 3, 3)))
    for bad in (-0.1, 100.1, math.nan, math.inf):
        with pytest.raises(ValueError, match="percentiles"):
            backend.percentile(a, [bad])
    with pytest.raises(ValueError, match="empty"):
        backend.percentile(backend.asarray(np.zeros((0, 3, 3), np.float32)), [50.0])


def test_memory_estimate() -> None:
    four_k = memory_estimate_bytes(2160, 3840, "c3")
    assert -(-four_k // 2**20) == 1982  # AD-1: 1,982 MiB at 4K
    exact = 601 * 5 * 2160 * 3840 // 12  # 50 1/12 planes x 1.25 x 4 bytes, an integer at 4K
    assert four_k - 2**20 in (exact, exact + 1)  # ceil of the float product (as the prototype)
    assert memory_estimate_bytes(2160, 3840, "ancuti2018") == four_k
    for backend in (NumpyBackend(),):
        assert backend.memory_estimate_bytes(1, 1, "c3") == memory_estimate_bytes(1, 1, "c3")
    with pytest.raises(ValueError, match="no memory estimate"):
        memory_estimate_bytes(10, 10, "ancuti2018-blue")
    with pytest.raises(ValueError, match="at least 1"):
        memory_estimate_bytes(0, 10, "c3")


@pytest.mark.parametrize("seed", [0, 1])
def test_same_device_twice_is_bit_identical(backend: CoreBackend, seed: int) -> None:
    image = rng_image((33, 47, 3), seed=seed)

    def run() -> list[bytes]:
        a = backend.asarray(image)
        outs = [
            backend.gaussian_blur(a, 4.3),
            backend.pyramid_reduce(a),
            backend.pyramid_expand(backend.pyramid_reduce(a), (33, 47)),
            backend.rgb_to_ycbcr(a, "bt709", "full"),
            backend.ycbcr_to_rgb(a, "bt601", "limited"),
            backend.percentile(a, [0.5, 99.5]),
        ]
        return [host(backend, out).tobytes() for out in outs]

    assert run() == run()


# -- CPU against GPU (AD-11) ----------------------------------------------------------------------


def all_methods(backend: CoreBackend, image: np.ndarray) -> dict[str, np.ndarray]:
    a = backend.asarray(image)
    h, w = image.shape[:2]
    out = {
        "gaussian_blur sharpen": backend.gaussian_blur(a, 0.005 * min(h, w) + 0.5),
        "gaussian_blur c3": backend.gaussian_blur(a, 0.05 * min(h, w)),
        "pyramid_reduce": backend.pyramid_reduce(a),
        "pyramid_expand": backend.pyramid_expand(backend.pyramid_reduce(a), (h, w)),
        "percentile": backend.percentile(a, [0.5, 50.0, 99.5]),
    }
    for matrix in ("bt709", "bt601"):
        for range_ in ("full", "limited"):
            out[f"rgb_to_ycbcr {matrix} {range_}"] = backend.rgb_to_ycbcr(a, matrix, range_)
            out[f"ycbcr_to_rgb {matrix} {range_}"] = backend.ycbcr_to_rgb(a, matrix, range_)
    return {name: host(backend, value) for name, value in out.items()}


@pytest.mark.gpu
@pytest.mark.parametrize("shape", [(120, 200, 3), (37, 53, 3), (1, 1, 3)])
def test_cpu_against_gpu_within_ad11(shape: tuple[int, ...]) -> None:
    gpu = gpu_backend()
    image = rng_image(shape, seed=11)
    cpu_out = all_methods(NumpyBackend(), image)
    gpu_out = all_methods(gpu, image)
    for name, cpu_value in cpu_out.items():
        difference = np.abs(cpu_value.astype(np.float64) - gpu_out[name])
        assert float(difference.max()) <= AD11_MAX, name
        assert float(difference.mean()) <= AD11_MEAN, name


# -- Gate 1: results stay on the device -----------------------------------------------------------


def array_returning_methods() -> set[str]:
    names = set()
    for name, member in inspect.getmembers(ArrayBackend, inspect.isfunction):
        if not name.startswith("_") and member.__annotations__.get("return") == "Array":
            names.add(name)
    return names


@pytest.mark.gpu
def test_gpu_methods_return_device_arrays() -> None:
    gpu = gpu_backend()
    cupy = gpu.xp
    image = gpu.asarray(rng_image((9, 11, 3)))
    calls: dict[str, Callable[[], Any]] = {
        "asarray": lambda: gpu.asarray(rng_image((2, 2, 3))),
        "gaussian_blur": lambda: gpu.gaussian_blur(image, 1.2),
        "pyramid_reduce": lambda: gpu.pyramid_reduce(image),
        "pyramid_expand": lambda: gpu.pyramid_expand(gpu.pyramid_reduce(image), (9, 11)),
        "rgb_to_ycbcr": lambda: gpu.rgb_to_ycbcr(image, "bt709", "limited"),
        "ycbcr_to_rgb": lambda: gpu.ycbcr_to_rgb(image, "bt601", "full"),
        "percentile": lambda: gpu.percentile(image, [1.0, 99.0]),
    }
    assert set(calls) == array_returning_methods()  # a new IF-2 method must be added here
    for name, call in calls.items():
        out = call()
        assert isinstance(out, cupy.ndarray), f"{name} returned {type(out).__name__}"


# -- planted defects: each named check fails on a wrong implementation ---------------------------


class CeilRadius(NumpyBackend):
    def gaussian_blur(self, a: Any, sigma_px: float) -> Any:
        radius = math.ceil(4.0 * sigma_px)
        return scipy_ndimage.gaussian_filter(
            a, sigma=(sigma_px, sigma_px, 0.0), mode="reflect", radius=(radius, radius, 0)
        )


class WrapBorder(NumpyBackend):
    def gaussian_blur(self, a: Any, sigma_px: float) -> Any:
        return scipy_ndimage.gaussian_filter(
            a, sigma=(sigma_px, sigma_px, 0.0), mode="wrap", truncate=4.0
        )


class WrapReduce(NumpyBackend):
    def pyramid_reduce(self, a: Any) -> Any:
        k = backend_module._BINOMIAL_5
        rows = scipy_ndimage.correlate1d(a, k, axis=0, mode="wrap")
        return scipy_ndimage.correlate1d(rows, k, axis=1, mode="wrap")[::2, ::2]


class EarlyCast(NumpyBackend):
    """R-7 interpolated in float32: the cast made before the return, not at it."""

    def percentile(self, a: Any, q: Any) -> Any:
        values = np.sort(a.ravel())
        out = []
        for value in q:
            h = np.float32(values.size - 1) * np.float32(value) / np.float32(100.0)
            low = int(np.floor(h))
            high = min(low + 1, values.size - 1)
            out.append(values[low] + (h - np.float32(low)) * (values[high] - values[low]))
        return np.array(out, dtype=np.float32)


class Float64Leak(NumpyBackend):
    def percentile(self, a: Any, q: Any) -> Any:
        return np.percentile(a, list(q), method="linear")


class UnnormalisedExpand(NumpyBackend):
    def pyramid_expand(self, a: Any, shape: tuple[int, int]) -> Any:
        up = np.zeros(shape + a.shape[2:], dtype=np.float32)
        up[::2, ::2] = a
        return (4.0 * self._binomial_blur(up)).astype(np.float32)


def test_planted_wrong_radius_rule_fails() -> None:
    with pytest.raises(AssertionError, match="check_gaussian_reference"):
        check_gaussian_reference(CeilRadius())


def test_planted_wrap_border_fails() -> None:
    with pytest.raises(AssertionError, match="check_gaussian_reference"):
        check_gaussian_reference(WrapBorder())
    with pytest.raises(AssertionError, match="check_reduce_reference"):
        check_reduce_reference(WrapReduce())


def test_planted_early_cast_fails() -> None:
    with pytest.raises(AssertionError, match="check_percentile_cast_point"):
        check_percentile_cast_point(EarlyCast())


def test_planted_float64_leak_fails() -> None:
    with pytest.raises(AssertionError, match="check_percentile_reference: dtype"):
        check_percentile_reference(Float64Leak())
    with pytest.raises(AssertionError, match="check_float32_out: percentile"):
        check_float32_out(Float64Leak())


def test_planted_unnormalised_expand_fails() -> None:
    with pytest.raises(AssertionError, match="check_expand_reference"):
        check_expand_reference(UnnormalisedExpand())


def test_planted_wrong_matrix_row_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    original = backend_module.rgb_to_ycbcr_matrix

    def wrong_rows(matrix: str) -> np.ndarray:
        return original(matrix)[[0, 2, 1]]  # Cb and Cr swapped

    monkeypatch.setattr(backend_module, "rgb_to_ycbcr_matrix", wrong_rows)
    backend_module._conversion.cache_clear()
    try:
        with pytest.raises(AssertionError, match="check_ycbcr_matrices: bt709 full"):
            check_ycbcr_matrices(NumpyBackend())
    finally:
        monkeypatch.undo()
        backend_module._conversion.cache_clear()
