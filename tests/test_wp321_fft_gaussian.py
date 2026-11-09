"""WP3.21 task 6: the FFT Gaussian behind CHARC's Q-R1 gate, on both backends.

``gaussian_blur`` takes the FFT route only when ``min(H, W) >= 1080`` and ``sigma >= 32``
(:func:`clearwater.core.backend.fft_route`). Pinned here: (a) a tripwire deriving the largest
analysis-proxy short side from ``analysis/proxy.py``'s own rule and asserting it is below the
gate, so no statistic ever meets the route; (b) a planted analysis-sized blur bit-identical to
the direct filter; (c) the FFT route within 1e-5 (CHARC Q3) of the direct filter at 1080p, 4K
and 5.3K, on step edges at every border, with repeated reflection, and on a real 4K frame;
deterministic on repeat. The direct reference is the call ``gaussian_blur`` made before task 6.
CHARC ruling (A): the route runs in batches of 512 lines, the last batch the final lines, and is
bit-identical to one batch per axis at 1080p, 4K and 5.3K on line counts that are not multiples
of 512; Q-C5a condition 2: the measured peak, plans and pool cleared first, is under the bound
the GPU backend's ``memory_estimate_bytes`` adds.
"""

from __future__ import annotations

import math
from typing import Any

import numpy as np
import pytest

import clearwater.core.backend as backend_module
from clearwater.analysis.proxy import block_mean, proxy_factor
from clearwater.core import backend_for, memory_estimate_bytes
from clearwater.core.backend import (
    FFT_BOUND_BYTES_PER_SAMPLE,
    FFT_MIN_SHORT_SIDE,
    FFT_MIN_SIGMA,
    GAUSSIAN_TRUNCATE,
    CoreBackend,
    fft_batch_starts,
    fft_memory_bound_bytes,
    fft_route,
    gaussian_kernel,
    reflect_index,
)

BOUND = 1e-5
"""CHARC Q3: max abs against the direct filter on [0, 1] float32 data."""

CPU = backend_for("cpu")


def _gpu() -> CoreBackend:
    try:
        return backend_for("cuda:0")
    except Exception as error:  # no CuPy or no device
        pytest.skip(f"no GPU backend: {error}")


def _direct(backend: CoreBackend, a: Any, sigma: float) -> Any:
    """The pre-task-6 ``gaussian_blur``: ``ndimage.gaussian_filter``, reflect, 4-sigma."""
    sigmas = (sigma, sigma) + (0.0,) * (a.ndim - 2)
    return backend.ndimage.gaussian_filter(a, sigma=sigmas, mode="reflect", truncate=4.0)


def _max_abs(backend: CoreBackend, a: Any, b: Any) -> float:
    return float(np.max(np.abs(backend.to_host(a) - backend.to_host(b))))


def _steps(shape: tuple[int, ...], seed: int = 5) -> np.ndarray:
    """[0, 1] noise with step edges at every border and corner (R0.4)."""
    rng = np.random.default_rng(seed)
    a = rng.random(shape, dtype=np.float32) * np.float32(0.5)
    a[:7] = 1.0
    a[-3:] = 0.0
    a[:, :11] = 1.0
    a[:, -1:] = 0.0
    a[:40, -40:] = 1.0
    a[-40:, :40] = 1.0
    a[100:101] = 1.0  # a one-pixel line inside the reach of the top border
    return a


# --- the gate -----------------------------------------------------------------------------


def test_the_gate_is_q_r1() -> None:
    assert (FFT_MIN_SHORT_SIDE, FFT_MIN_SIGMA) == (1080, 32.0)
    assert fft_route(1080, 1920, 32.0) and fft_route(1920, 1080, 32.0)
    assert fft_route(2160, 3840, 108.0) and fft_route(4648, 5312, 232.4)
    assert not fft_route(1079, 1920, 1000.0)
    assert not fft_route(1920, 1079, 1000.0)
    assert not fft_route(1080, 1920, math.nextafter(32.0, 0.0))
    assert not fft_route(2160, 3840, 21.6)  # c3's mask blur at 4K stays direct


@pytest.mark.parametrize(
    ("shape", "sigma", "routed"),
    [
        ((1080, 1920), 32.0, True),
        ((1080, 1920, 3), 54.0, True),
        ((1079, 1920), 270.0, False),
        ((1080, 1920), 31.5, False),
    ],
)
def test_gaussian_blur_takes_the_route_by_the_gate(
    monkeypatch: pytest.MonkeyPatch, shape: tuple[int, ...], sigma: float, routed: bool
) -> None:
    calls: list[int] = []
    correlate = CoreBackend._fft_correlate

    def spy(self: CoreBackend, a: Any, weights: Any, axis: int) -> Any:
        calls.append(axis)
        return correlate(self, a, weights, axis)

    monkeypatch.setattr(CoreBackend, "_fft_correlate", spy)
    a = CPU.asarray(np.zeros(shape, dtype=np.float32))
    CPU.gaussian_blur(a, sigma)
    assert calls == ([0, 1] if routed else [])


def test_the_kernel_is_scipys() -> None:
    from scipy.ndimage._filters import _gaussian_kernel1d  # the weights gaussian_filter uses

    for sigma in (0.7, 32.0, 54.0, 108.0, 232.4):
        radius = int(GAUSSIAN_TRUNCATE * sigma + 0.5)
        expected = _gaussian_kernel1d(sigma, 0, radius)[::-1]
        assert np.array_equal(gaussian_kernel(sigma), expected)


def test_reflect_index_is_numpys_symmetric_pad() -> None:
    for n, radius in ((5, 2), (5, 5), (5, 13), (1, 4), (8, 30)):
        line = np.arange(n)
        assert np.array_equal(reflect_index(n, radius), np.pad(line, radius, mode="symmetric"))


# --- (a) the tripwire: no analysis proxy reaches the gate -----------------------------------


def test_a_no_proxy_short_side_reaches_the_gate() -> None:
    # proxy.py's rule: factor k = max(1, S // 540) on the short side S; the proxy's short side is
    # ceil(S / k) (block_mean keeps the partial last block). Its maximum over every S is 1079.
    largest = max(math.ceil(s / proxy_factor(s, s)) for s in range(1, 200_001))
    assert largest == 1079 < FFT_MIN_SHORT_SIDE
    # The rule as block_mean applies it, at the worst source sizes (S = 1079 and 1619).
    for s in (1079, 1619):
        proxy = block_mean(np.zeros((s, s + 7, 1), dtype=np.float32), proxy_factor(s, s + 7))
        assert min(proxy.shape[:2]) == math.ceil(s / proxy_factor(s, s + 7)) < FFT_MIN_SHORT_SIDE


# --- (b) an analysis-sized blur is the direct filter, bit for bit --------------------------


def _analysis_sized(backend: CoreBackend) -> None:
    a = backend.asarray(_steps((1079, 1920, 3)))
    for sigma in (54.0, 270.0):  # c3_kernel_fraction at its default and its maximum
        assert np.array_equal(
            backend.to_host(backend.gaussian_blur(a, sigma)),
            backend.to_host(_direct(backend, a, sigma)),
        )


def test_b_an_analysis_sized_blur_is_the_direct_filter_cpu() -> None:
    _analysis_sized(CPU)


@pytest.mark.gpu
def test_b_an_analysis_sized_blur_is_the_direct_filter_gpu() -> None:
    _analysis_sized(_gpu())


# --- (c) the FFT route within the bound ------------------------------------------------------

CASES_1080 = [((1080, 1920), 54.0), ((1080, 1920, 3), 32.0), ((1080, 1920), 300.0)]
"""1080p: the c3 render's Cb / Cr blur, the gate's floor on RGB, and a radius (1200) beyond the
short axis (repeated reflection)."""

CASES_4K = [((2160, 3840), 108.0), ((2160, 3840, 3), 32.0)]


def _within_bound(backend: CoreBackend, shape: tuple[int, ...], sigma: float) -> None:
    a = backend.asarray(_steps(shape))
    out = backend.gaussian_blur(a, sigma)
    error = _max_abs(backend, out, _direct(backend, a, sigma))
    assert error <= BOUND, f"{shape} sigma {sigma}: max abs {error:.3e}"
    assert np.array_equal(backend.to_host(backend.gaussian_blur(a, sigma)), backend.to_host(out))
    assert out.dtype == np.float32 and out.shape == a.shape


@pytest.mark.parametrize(("shape", "sigma"), CASES_1080)
def test_c_1080p_within_the_bound_cpu(shape: tuple[int, ...], sigma: float) -> None:
    _within_bound(CPU, shape, sigma)


@pytest.mark.slow  # reason: the CPU direct reference at 4K takes seconds per case
@pytest.mark.parametrize(("shape", "sigma"), CASES_4K)
def test_c_4k_within_the_bound_cpu(shape: tuple[int, ...], sigma: float) -> None:
    _within_bound(CPU, shape, sigma)


@pytest.mark.gpu
@pytest.mark.parametrize(("shape", "sigma"), CASES_1080 + CASES_4K + [((4648, 5312), 232.4)])
def test_c_within_the_bound_gpu(shape: tuple[int, ...], sigma: float) -> None:
    _within_bound(_gpu(), shape, sigma)


@pytest.mark.gpu
@pytest.mark.footage
def test_c_a_real_4k_frame_within_the_bound() -> None:
    from clearwater.io.video import FFmpegVideoSource
    from local_config import FootageLookupError, find_footage_file, load_local_config

    try:
        path = find_footage_file("GX011627", load_local_config().footage_path)
    except (FootageLookupError, OSError) as error:
        pytest.skip(f"no footage: {error}")
    source = FFmpegVideoSource()
    frames = source.frames(source.probe(path), hw_decode=False)
    try:
        frame = next(frames)
    finally:
        frames.close()  # type: ignore[attr-defined]
    gpu = _gpu()
    rgb = gpu.asarray(frame.pixels)
    for a, sigma in ((rgb[..., 1].copy(), 108.0), (rgb, 32.0)):
        error = _max_abs(gpu, gpu.gaussian_blur(a, sigma), _direct(gpu, a, sigma))
        assert error <= BOUND, f"sigma {sigma}: max abs {error:.3e}"


# --- the batches (CHARC ruling (A)) -------------------------------------------------------


def test_the_batches_cover_every_line_with_one_length() -> None:
    assert fft_batch_starts(300, 512) == [0]
    assert fft_batch_starts(1024, 512) == [0, 512]
    assert fft_batch_starts(1081, 512) == [0, 512, 569]  # the last is the final 512 lines
    for lines in (512, 513, 1080, 1920, 2160, 3840, 4648, 5312):
        starts = fft_batch_starts(lines, 512)
        covered = set().union(*(range(s, s + 512) for s in starts))
        assert covered == set(range(lines)) and starts[-1] == lines - 512


BATCHED = [
    ((1080, 1920), 54.0),
    ((1081, 1923, 3), 32.0),
    ((2160, 3840), 108.0),
    ((2161, 3843, 3), 32.0),
    ((4648, 5312), 232.4),
    ((4649, 5313), 1162.0),
]
"""Line counts that are not multiples of 512 along both axes, at 1080p, 4K and 5.3K 8:7."""


def _batched_is_unbatched(
    backend: CoreBackend, monkeypatch: pytest.MonkeyPatch, shape: tuple[int, ...], sigma: float
) -> None:
    a = backend.asarray(np.random.default_rng(9).random(shape, dtype=np.float32))
    batched = backend.to_host(backend.gaussian_blur(a, sigma))
    monkeypatch.setattr(backend_module, "FFT_BATCH_LINES", 10**9)  # one batch per axis
    unbatched = backend.to_host(backend.gaussian_blur(a, sigma))
    assert np.array_equal(batched, unbatched)


@pytest.mark.gpu
@pytest.mark.parametrize(("shape", "sigma"), BATCHED)
def test_the_batched_route_is_the_unbatched_one_bit_for_bit_gpu(
    monkeypatch: pytest.MonkeyPatch, shape: tuple[int, ...], sigma: float
) -> None:
    _batched_is_unbatched(_gpu(), monkeypatch, shape, sigma)


CONTROL_BATCH_LINES = 516
"""The diagnostic's control batch: 172 RGB positions = 516 lines, a multiple of 4 (WP6.5 C16)."""


def _batch_mismatch_report(
    monkeypatch: pytest.MonkeyPatch,
    a: Any,
    sigma: float,
    batched: np.ndarray,
    unbatched: np.ndarray,
) -> str:
    """What CHARC rules C16 on (WP6.5 G3): the size and place of a batched / unbatched
    difference, the library versions, the AD-11 tier-2 bound, and a control at 516 lines.

    Only the constant is patched for the control (inside this test); the product is untouched.
    """
    import scipy

    batch_lines = backend_module.FFT_BATCH_LINES
    diff = np.abs(batched.astype(np.float64) - unbatched.astype(np.float64))
    nonzero = np.argwhere(diff != 0)
    first = [tuple(int(i) for i in position) for position in nonzero[:12]]
    monkeypatch.setattr(backend_module, "FFT_BATCH_LINES", CONTROL_BATCH_LINES)
    control = CPU.to_host(CPU.gaussian_blur(a, sigma))
    control_diff = np.abs(control.astype(np.float64) - unbatched.astype(np.float64))
    return "\n".join(
        [
            f"C16 diagnostic: batched (FFT_BATCH_LINES={batch_lines}) vs unbatched, "
            f"shape {batched.shape}, sigma {sigma}",
            f"  numpy {np.__version__}, scipy {scipy.__version__}",
            f"  max abs {diff.max():.9g}, p99 {np.percentile(diff, 99):.9g}, "
            f"nonzero {len(nonzero)} of {diff.size}",
            f"  first positions (row, col[, channel]): {first}",
            f"  inside the AD-11 tier-2 FFT bound {BOUND:g}: {bool(diff.max() <= BOUND)}",
            f"  control FFT_BATCH_LINES={CONTROL_BATCH_LINES} vs unbatched: max abs "
            f"{control_diff.max():.9g}, nonzero {int(np.count_nonzero(control_diff))}, "
            f"bit-identical {bool(np.array_equal(control, unbatched))}",
        ]
    )


@pytest.mark.parametrize(("shape", "sigma"), BATCHED[:2])
def test_the_batched_route_is_the_unbatched_one_bit_for_bit_cpu(
    monkeypatch: pytest.MonkeyPatch, shape: tuple[int, ...], sigma: float
) -> None:
    """Tier 1 (bit-identity) on the CPU route; on a mismatch the C16 diagnostic prints first.

    WP6.5 G3 (CHARC's C16 ruling, measurement first): the darwin arm64 runner failed
    ``[shape1-32.0]``. The bound is unchanged (the test still FAILS on any difference); the
    report says how large the difference is and whether a 516-line batch removes it.
    """
    a = CPU.asarray(np.random.default_rng(9).random(shape, dtype=np.float32))
    batched = CPU.to_host(CPU.gaussian_blur(a, sigma))
    with monkeypatch.context() as patch:
        patch.setattr(backend_module, "FFT_BATCH_LINES", 10**9)  # one batch per axis
        unbatched = CPU.to_host(CPU.gaussian_blur(a, sigma))
    if not np.array_equal(batched, unbatched):
        report = _batch_mismatch_report(monkeypatch, a, sigma, batched, unbatched)
        print(report, flush=True)
        pytest.fail(report)


def test_the_c16_diagnostic_reports_a_planted_difference(monkeypatch: pytest.MonkeyPatch) -> None:
    """The diagnostic itself, on every host: a planted one-ulp-scale difference is measured,
    placed, judged against the tier-2 bound, and the control runs; the constant is restored."""
    shape, sigma = BATCHED[1]
    a = CPU.asarray(np.random.default_rng(9).random(shape, dtype=np.float32))
    unbatched = CPU.to_host(CPU.gaussian_blur(a, sigma))
    planted = unbatched.copy()
    planted[7, 11, 2] = np.nextafter(planted[7, 11, 2], np.float32(2.0))
    with monkeypatch.context() as patch:
        report = _batch_mismatch_report(patch, a, sigma, planted, unbatched)
    assert backend_module.FFT_BATCH_LINES != CONTROL_BATCH_LINES
    assert "nonzero 1 of" in report
    assert "first positions (row, col[, channel]): [(7, 11, 2)]" in report
    assert f"inside the AD-11 tier-2 FFT bound {BOUND:g}: True" in report
    assert "scipy " in report and "numpy " in report
    assert f"control FFT_BATCH_LINES={CONTROL_BATCH_LINES} vs unbatched" in report


# --- the memory bound (Q-C5a condition 2) ----------------------------------------------------


def test_the_bound_is_zero_below_the_gate_and_the_cpu_estimate_is_unchanged() -> None:
    assert fft_memory_bound_bytes(1079, 1920) == 0
    assert fft_memory_bound_bytes(1080, 1920) == FFT_BOUND_BYTES_PER_SAMPLE * 512 * 4096
    assert CPU.memory_estimate_bytes(2160, 3840, "c3") == memory_estimate_bytes(2160, 3840, "c3")


@pytest.mark.gpu
@pytest.mark.parametrize("size", [(1080, 1920), (2160, 3840), (4648, 5312)])
def test_the_measured_peak_is_under_the_bound_the_gpu_estimate_adds(
    size: tuple[int, int],
) -> None:
    gpu = _gpu()
    cupy = gpu.xp
    pool, plans = cupy.get_default_memory_pool(), cupy.fft.config.get_plan_cache()
    bound = fft_memory_bound_bytes(*size)
    assert gpu.memory_estimate_bytes(*size, "c3") == memory_estimate_bytes(*size, "c3") + bound
    peak = [0]

    def tracking(nbytes: int) -> Any:
        block = pool.malloc(nbytes)
        peak[0] = max(peak[0], pool.used_bytes())
        return block

    cupy.cuda.set_allocator(tracking)
    try:
        for fraction in (0.05, 0.25):  # c3_kernel_fraction: the default and the maximum
            for channels in (1, 3):
                shape = size if channels == 1 else (*size, channels)
                a = gpu.asarray(np.random.default_rng(2).random(shape, dtype=np.float32))
                plans.clear()  # the binding method: plans and pool cleared before each peak
                pool.free_all_blocks()
                base = pool.used_bytes()
                peak[0] = base
                out = gpu.gaussian_blur(a, fraction * min(size))
                cupy.cuda.Device().synchronize()
                # Over the input: the two passes' full-size outputs (as the direct filter's)
                # and the FFT's own plans and batch buffers, which the bound covers.
                own = peak[0] - base - 2 * a.nbytes
                assert own <= bound, f"{shape} {fraction}: {own / 2**20:.0f} MiB"
                del out, a
    finally:
        cupy.cuda.set_allocator(pool.malloc)
        plans.clear()
        pool.free_all_blocks()
