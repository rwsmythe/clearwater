"""WP3.21 #3: the analysis proxy's block mean on the device, bit for bit the host's (AD-29; Q3).

A decoded frame on the GPU keeps its pixels on the device for the analysis proxy: the GPU backend
takes the block sums there (``CoreBackend.block_sums``, an IF-2 device extension, absent on the
CPU backend) and ``clearwater.analysis`` reaches it only through its own Protocol,
:class:`AnalysisDeviceBackend`. The division and the quantisation stay the host's. These tests
pin: the GPU backend satisfies the Protocol with the same signature and the CPU backend does not;
the device block mean equals the host's bit for bit (so the uint8 proxy byte for byte) at 4K,
both 5.3K shapes, an odd size with partial edge blocks and a small ``k = 1`` frame, 8 and 10 bit;
a value the exactness bound refuses (NaN, infinity, above 1, too small) returns None and the
host reduction gives the same values; the bound's edge; and the frame routing (a GPU frame stays
on its device, a host frame and the CPU backend take the host path as before).
"""

from __future__ import annotations

import inspect
from fractions import Fraction
from typing import Any

import numpy as np
import pytest

from clearwater.analysis import proxy as proxy_module
from clearwater.analysis.proxy import block_mean, make_proxy, proxy_factor
from clearwater.core.backend import NumpyBackend, _probe_gpu
from clearwater.interfaces import ColorDescription, Frame


def _gpu() -> Any:
    backend, reason = _probe_gpu()
    if backend is None:
        pytest.skip(reason)
    return backend


def _decoded_like(shape: tuple[int, int], bit_depth: int, seed: int) -> np.ndarray:
    """Float32 frame values as the decode gives them: ``code / (2**n - 1)``, edges included."""
    rng = np.random.default_rng(seed)
    top = 2**bit_depth - 1
    codes = rng.integers(0, top + 1, size=(*shape, 3))
    codes[0, :, :] = top  # full-scale and zero rows: the largest and smallest sums
    codes[-1, :, :] = 0
    return (codes.astype(np.float32) / np.float32(top)).astype(np.float32)


def _same(got: np.ndarray, want: np.ndarray) -> bool:
    return got.dtype == want.dtype and got.shape == want.shape and got.tobytes() == want.tobytes()


def _frame(pixels: Any, device: str) -> Frame:
    """A minimal IF-1 frame around ``pixels``."""
    color = ColorDescription("bt709", "bt709", "bt709", "full", 8, False, None)
    return Frame(
        pixels=pixels,
        device=device,
        color=color,
        orientation_applied=False,
        pts=Fraction(0),
        pts_ticks=0,
        time_base=Fraction(1, 30000),
        index=0,
    )


# --- AD-29: the Protocol, both directions -------------------------------------------------------


@pytest.mark.gpu
def test_the_gpu_backend_satisfies_the_analysis_protocol_with_the_same_signature() -> None:
    gpu = _gpu()
    protocol = proxy_module.AnalysisDeviceBackend
    assert isinstance(gpu, protocol)
    assert inspect.signature(protocol.block_sums) == inspect.signature(type(gpu).block_sums)


def test_the_cpu_backend_has_no_block_sums_and_does_not_satisfy_the_analysis_protocol() -> None:
    cpu = NumpyBackend()
    assert not hasattr(cpu, "block_sums")
    assert not isinstance(cpu, proxy_module.AnalysisDeviceBackend)


# --- the device block mean ------------------------------------------------------------------------


@pytest.mark.gpu
@pytest.mark.parametrize("bit_depth", [8, 10])
@pytest.mark.parametrize(
    "shape",
    [(2160, 3840), (2988, 5312), (4648, 5312), (1081, 1923), (37, 53)],
    ids=["4k-k4", "5.3k-16x9-k5", "5.3k-8x7-k8", "odd-k2-edges", "small-k1"],
)
def test_the_device_block_mean_equals_the_host_bit_for_bit(
    bit_depth: int, shape: tuple[int, int]
) -> None:
    gpu = _gpu()
    host = _decoded_like(shape, bit_depth, seed=shape[0] + bit_depth)
    k = proxy_factor(*shape)
    device = gpu.asarray(host)
    if k > 1:
        sums = gpu.block_sums(device, k)  # a decoded frame always meets the bound
        assert sums is not None and sums.dtype == np.float64
    got = proxy_module.frame_block_mean(device, k, gpu)
    assert _same(got, block_mean(host, k))
    assert _same(make_proxy(device, gpu), make_proxy(host))


@pytest.mark.gpu
@pytest.mark.parametrize(
    "plant",
    [np.nan, np.inf, 1.5, 1e-30, 1e-12],
    ids=["nan", "inf", "above-one", "subnormal-scale", "too-small-for-the-bound"],
)
def test_a_frame_whose_sums_may_be_inexact_takes_the_host_path_with_the_same_values(
    plant: float,
) -> None:
    gpu = _gpu()
    host = _decoded_like((64, 96), 8, seed=3)
    host[5, 7, 1] = np.float32(plant)
    device = gpu.asarray(host)
    assert gpu.block_sums(device, 4) is None
    got = proxy_module.frame_block_mean(device, 4, gpu)
    assert _same(got, block_mean(host, 4))
    if np.isfinite(plant):
        assert _same(make_proxy(device, gpu), make_proxy(host))


@pytest.mark.gpu
def test_the_exactness_bound_admits_decoded_values_and_refuses_values_past_its_edge() -> None:
    gpu = _gpu()
    cp = gpu.xp
    assert gpu.block_sums(cp.zeros((8, 8, 3), dtype=cp.float32), 4) is not None
    assert gpu.block_sums(cp.full((8, 8, 3), 1 / 1023, dtype=cp.float32), 8) is not None
    # k=5: sums below 2**5; 2**-25 is a multiple of 2**-48, so 5 + 48 = 53 bits: the last admitted.
    assert gpu.block_sums(cp.full((8, 8, 3), 2.0**-25, dtype=cp.float32), 5) is not None
    assert gpu.block_sums(cp.full((8, 8, 3), 2.0**-26, dtype=cp.float32), 5) is None
    # Negative values within [-1, 1] are bounded the same way (the sums are exact either sign).
    signed = cp.asarray(_decoded_like((40, 60), 8, seed=9) - np.float32(0.5))
    assert _same(gpu.block_sums(signed, 4), _sums(cp.asnumpy(signed), 4))


def _sums(pixels: np.ndarray, k: int) -> np.ndarray:
    rows, cols = np.arange(0, pixels.shape[0], k), np.arange(0, pixels.shape[1], k)
    summed = np.add.reduceat(pixels, rows, axis=0, dtype=np.float64)
    out: np.ndarray = np.add.reduceat(summed, cols, axis=1)
    return out


@pytest.mark.gpu
def test_block_sums_refuses_a_wrong_array_and_factor() -> None:
    gpu = _gpu()
    cp = gpu.xp
    with pytest.raises(ValueError, match="at least 1"):
        gpu.block_sums(cp.zeros((4, 4, 3), dtype=cp.float32), 0)
    with pytest.raises(ValueError, match="float32"):
        gpu.block_sums(cp.zeros((4, 4, 3), dtype=cp.float64), 2)
    with pytest.raises(ValueError, match="shape"):
        gpu.block_sums(cp.zeros((4, 4), dtype=cp.float32), 2)
    with pytest.raises(TypeError, match="numpy"):
        gpu.block_sums(np.zeros((4, 4, 3), dtype=np.float32), 2)


# --- the routing ----------------------------------------------------------------------------------


@pytest.mark.gpu
def test_a_gpu_frame_stays_on_the_device_for_the_proxy() -> None:
    gpu = _gpu()
    pixels = gpu.asarray(np.zeros((4, 4, 3), np.float32))
    frame = _frame(pixels, gpu.device)
    assert proxy_module.frame_pixels_for_proxy(frame, gpu) is pixels
    host = _frame(np.zeros((4, 4, 3), np.float32), "cpu")
    assert isinstance(proxy_module.frame_pixels_for_proxy(host, gpu), np.ndarray)
    with pytest.raises(TypeError):  # the CPU backend never reads a device frame (as before)
        proxy_module.frame_pixels_for_proxy(frame, NumpyBackend())


def test_host_pixels_take_the_base_path_with_any_backend() -> None:
    host = _decoded_like((2160, 3840), 8, seed=1)
    want = make_proxy(host)
    for backend in (None, NumpyBackend()):
        assert _same(make_proxy(host, backend), want)
        assert _same(proxy_module.frame_block_mean(host, 4, backend), block_mean(host, 4))
    frame = _frame(host, "cpu")
    assert _same(np.asarray(proxy_module.frame_pixels_for_proxy(frame, NumpyBackend())), host)
