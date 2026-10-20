"""WP3.1: the product backend and helpers against the read-only prototype (DR-19, ruling 6).

The references are computed here by calling ``tools/prototype`` on seeded synthetic inputs and
on the WP2.3 stills; nothing is committed. Where the product makes the prototype's call the
result must be bit-identical on the same device; ``percentile`` must equal the prototype's
float64 result cast to float32.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

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
    memory_estimate_bytes,
    pyramid_levels,
    rgb_to_lab,
    spatial_sigma,
)
from clearwater.core.backend import _probe_gpu
from lookcheck.frames import read_png16
from prototype import backend as proto_backend
from prototype import pipeline as proto
from prototype.params import Params

STILLS_16 = ["png16-uniform-none", "png16-gradient-none", "png16-lowred-none"]
STILLS_8 = ["png8-uniform-none", "png8-gradient-none", "png8-lowred-none"]


@pytest.fixture(params=["numpy", pytest.param("cupy", marks=pytest.mark.gpu)])
def backend(request: pytest.FixtureRequest) -> CoreBackend:
    if request.param == "numpy":
        return NumpyBackend()
    gpu, reason = _probe_gpu()
    if gpu is None:
        pytest.skip(reason)
    return gpu


def synthetic(seed: int, shape: tuple[int, int] = (45, 67)) -> np.ndarray:
    image = np.random.default_rng(seed).random((*shape, 3), dtype=np.float32)
    if seed % 2:
        image[..., 0] *= np.float32(1e-3)  # near-zero red
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


def same(product: Any, reference: Any, backend: CoreBackend, what: str) -> None:
    p = np.asarray(backend.to_host(product))
    r = reference if isinstance(reference, np.ndarray) else backend.to_host(reference)
    assert p.dtype == r.dtype, f"{what}: dtype {p.dtype} vs {r.dtype}"
    assert p.shape == r.shape, f"{what}: shape {p.shape} vs {r.shape}"
    assert p.tobytes() == np.asarray(r).tobytes(), (
        f"{what}: max {float(np.abs(p.astype(np.float64) - r).max()):.3g}"
    )


def test_if2_methods_bit_identical_to_prototype(backend: CoreBackend, image: np.ndarray) -> None:
    a = backend.asarray(image)
    params = Params()
    h, w = image.shape[:2]
    for fraction in (params.sharpen_blur_fraction, params.saliency_blur_fraction, 0.05):
        sigma = proto.spatial_sigma(image.shape, fraction)
        same(backend.gaussian_blur(a, sigma), proto._gaussian(a, sigma), backend, f"blur {sigma}")
    reduced = backend.pyramid_reduce(a)
    same(reduced, proto._binomial_blur(a)[::2, ::2].copy(), backend, "reduce")
    same(backend.pyramid_expand(reduced, (h, w)), proto.expand(reduced, a.shape), backend, "expand")
    luma = luminance(backend, a)
    same(backend.pyramid_reduce(luma), proto._binomial_blur(luma)[::2, ::2].copy(), backend, "map")
    ycbcr = backend.rgb_to_ycbcr(a, "bt709", "full")
    same(ycbcr, proto.rgb_to_ycbcr(a), backend, "rgb_to_ycbcr")
    same(backend.ycbcr_to_rgb(ycbcr, "bt709", "full"), proto.ycbcr_to_rgb(ycbcr), backend, "back")
    q = [params.normalisation_low, params.normalisation_high]
    high_pass = proto.high_pass_of(a, params)
    reference = backend.xp.percentile(high_pass, q, method="linear").astype(np.float32)
    same(backend.percentile(high_pass, q), reference, backend, "percentile")
    bounds = proto.normalisation_bounds(a, params)
    np.testing.assert_array_equal(
        np.asarray(backend.to_host(backend.percentile(high_pass, q))),
        np.array(bounds, dtype=np.float32),
    )


def test_helpers_bit_identical_to_prototype(backend: CoreBackend, image: np.ndarray) -> None:
    a = backend.asarray(image)
    params = Params()
    levels = pyramid_levels(image.shape, params.pyramid_min_level_size)
    assert levels == proto.pyramid_levels(image.shape, params.pyramid_min_level_size)
    for product, reference in zip(
        gaussian_pyramid(backend, a, levels), proto.gaussian_pyramid(a, levels), strict=True
    ):
        same(product, backend.xp.ascontiguousarray(reference), backend, "gaussian_pyramid")
    bands = laplacian_pyramid(backend, a, levels)
    for product, reference in zip(bands, proto.laplacian_pyramid(a, levels), strict=True):
        same(product, reference, backend, "laplacian_pyramid")
    same(collapse_pyramid(backend, bands), proto.collapse_pyramid(bands), backend, "collapse")
    same(luminance(backend, a), proto.luminance(a), backend, "luminance")
    same(rgb_to_lab(backend, a), proto.srgb_to_lab(a), backend, "rgb_to_lab")
    smoothed = backend.gaussian_blur(luminance(backend, a), 2.0)
    reference_laplace = proto_backend.of(smoothed).ndimage.laplace(smoothed, mode="reflect")
    same(laplacian(backend, smoothed), reference_laplace, backend, "laplacian")
    assert channel_means(backend, a) == proto._channel_means(a)
    assert mean(backend, luminance(backend, a)) == proto._cap_statistic(luminance(backend, a))
    for fraction in (0.005, 0.05, 0.37):
        assert spatial_sigma(image.shape, fraction) == proto.spatial_sigma(image.shape, fraction)


@pytest.mark.parametrize("size", [(1, 1), (2160, 3840), (3024, 4032), (6000, 8000), (37, 53)])
def test_memory_estimate_equals_prototype(size: tuple[int, int]) -> None:
    expected = proto_backend.memory_estimate_bytes((*size, 3), Params())
    for method_id in ("c3", "ancuti2018"):
        assert memory_estimate_bytes(*size, method_id) == expected
        assert NumpyBackend().memory_estimate_bytes(*size, method_id) == expected
