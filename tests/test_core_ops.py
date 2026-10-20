"""WP3.1: the helper operations of ``clearwater.core.ops`` (ruling 1, R0-2)."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

import numpy as np
import pytest

from clearwater.core import (
    CoreBackend,
    NumpyBackend,
    channel_means,
    collapse_pyramid,
    gaussian_pyramid,
    laplacian,
    laplacian_pyramid,
    luminance,
    mean,
    pyramid_levels,
    rgb_to_lab,
    spatial_sigma,
)
from clearwater.core.backend import _probe_gpu
from clearwater.interfaces.stubs import StubArrayBackend


@pytest.fixture(params=["numpy", pytest.param("cupy", marks=pytest.mark.gpu)])
def backend(request: pytest.FixtureRequest) -> CoreBackend:
    if request.param == "numpy":
        return NumpyBackend()
    gpu, reason = _probe_gpu()
    if gpu is None:
        pytest.skip(reason)
    return gpu


def rng_image(shape: tuple[int, ...], seed: int = 0) -> np.ndarray:
    return np.random.default_rng(seed).random(shape, dtype=np.float32)


def test_spatial_sigma_and_levels() -> None:
    assert spatial_sigma((2160, 3840, 3), 0.05) == pytest.approx(108.0)
    assert spatial_sigma((3840, 2160), 0.005) == pytest.approx(10.8)
    assert pyramid_levels((2160, 3840, 3), 16) == 8  # 2160 -> 1080 ... -> 17
    assert pyramid_levels((1, 1, 3), 16) == 1
    assert pyramid_levels((5, 9), 1) == 4  # 5 -> 3 -> 2 -> 1
    with pytest.raises(ValueError, match="min_level_size"):
        pyramid_levels((10, 10), 0)


@pytest.mark.parametrize("shape", [(45, 67, 3), (33, 20), (1, 1, 3)])
def test_pyramid_round_trip(backend: CoreBackend, shape: tuple[int, ...]) -> None:
    image = rng_image(shape, seed=1)
    a = backend.asarray(image)
    levels = pyramid_levels(shape, 4)
    gaussian = gaussian_pyramid(backend, a, levels)
    assert len(gaussian) == levels and gaussian[0] is a
    bands = laplacian_pyramid(backend, a, levels)
    assert [band.shape for band in bands] == [level.shape for level in gaussian]
    back = np.asarray(backend.to_host(collapse_pyramid(backend, bands)))
    assert float(np.abs(back - image).max()) < 1e-6
    with pytest.raises(ValueError, match="levels"):
        gaussian_pyramid(backend, a, 0)
    with pytest.raises(ValueError, match="at least one level"):
        collapse_pyramid(backend, [])


def test_flat_maps(backend: CoreBackend) -> None:
    flat = backend.asarray(np.full((9, 13), 0.4, dtype=np.float32))
    assert np.all(np.asarray(backend.to_host(laplacian(backend, flat))) == 0.0)
    gray = backend.asarray(np.full((4, 5, 3), 0.5, dtype=np.float32))
    np.testing.assert_allclose(np.asarray(backend.to_host(luminance(backend, gray))), 0.5, 1e-6)
    lab = np.asarray(backend.to_host(rgb_to_lab(backend, gray)))
    # A neutral gray has a*, b* near 0; not exactly, as the 4-digit IEC matrix rows sum to
    # 0.9505 and 1.0890 against the D65 white 0.95047 and 1.08883 (b* about -0.006).
    np.testing.assert_allclose(lab[..., 1:], 0.0, atol=0.02)
    white = backend.asarray(np.ones((1, 1, 3), dtype=np.float32))
    lab_white = np.asarray(backend.to_host(rgb_to_lab(backend, white)))[0, 0]
    np.testing.assert_allclose(lab_white, [100.0, 0.0, 0.0], atol=0.05)


def test_means(backend: CoreBackend) -> None:
    image = rng_image((17, 19, 3), seed=2)
    image[..., 0] *= np.float32(1e-4)
    a = backend.asarray(image)
    means = channel_means(backend, a)
    assert all(isinstance(value, float) for value in means)
    np.testing.assert_allclose(means, image.astype(np.float64).mean(axis=(0, 1)), rtol=1e-12)
    assert mean(backend, a) == pytest.approx(float(image.astype(np.float64).mean()), rel=1e-12)
    with pytest.raises(ValueError, match="empty"):
        mean(backend, backend.asarray(np.zeros((0, 3), np.float32)))


HELPERS: dict[str, Callable[[Any, Any], Any]] = {
    "luminance": luminance,
    "rgb_to_lab": rgb_to_lab,
    "laplacian": lambda b, a: laplacian(b, a[..., 0]),
    "channel_means": channel_means,
    "mean": mean,
    "gaussian_pyramid": lambda b, a: gaussian_pyramid(b, a, 2),
}


@pytest.mark.parametrize("name", sorted(HELPERS))
def test_helpers_refuse_bad_inputs(backend: CoreBackend, name: str) -> None:
    helper = HELPERS[name]
    with pytest.raises(TypeError, match=r"clearwater.core backend"):
        helper(StubArrayBackend(), np.zeros((4, 4, 3), np.float32))
    with pytest.raises(ValueError, match="float32"):
        helper(backend, backend.xp.zeros((4, 4, 3), dtype=np.float64))


def test_shape_refusals(backend: CoreBackend) -> None:
    four = backend.asarray(np.zeros((3, 3, 4), np.float32))
    for helper in (luminance, rgb_to_lab, channel_means):
        with pytest.raises(ValueError, match="shape"):
            helper(backend, four)
    with pytest.raises(ValueError, match=r"\(H, W\) map"):
        laplacian(backend, backend.asarray(np.zeros((3, 3, 3), np.float32)))


@pytest.mark.gpu
def test_gpu_helpers_return_device_arrays() -> None:
    gpu, reason = _probe_gpu()
    if gpu is None:
        pytest.skip(reason)
    cupy = gpu.xp
    a = gpu.asarray(rng_image((9, 11, 3)))
    outputs: dict[str, Any] = {
        "luminance": luminance(gpu, a),
        "rgb_to_lab": rgb_to_lab(gpu, a),
        "laplacian": laplacian(gpu, luminance(gpu, a)),
        "collapse_pyramid": collapse_pyramid(gpu, laplacian_pyramid(gpu, a, 3)),
    }
    for index, level in enumerate(gaussian_pyramid(gpu, a, 3)):
        outputs[f"gaussian_pyramid[{index}]"] = level
    for index, level in enumerate(laplacian_pyramid(gpu, a, 3)):
        outputs[f"laplacian_pyramid[{index}]"] = level
    for name, out in outputs.items():
        assert isinstance(out, cupy.ndarray), f"{name} returned {type(out).__name__}"
        assert out.dtype == np.float32, f"{name} returned {out.dtype}"
