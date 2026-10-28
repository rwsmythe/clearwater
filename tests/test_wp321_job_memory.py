"""WP3.21 task 10 (CHARC rulings `cadc39fc8a199a57`, `7f58cfc1`): the job device-wide estimate.

``core.memory.job_device_memory_estimate_bytes`` = the GPU backend's pool estimate (AD-1's base
plus the FFT bound) + the CUDA context + n NVDEC sessions + NVENC, each session
``floor + bytes per pixel x pixels`` fitted from the two measured sizes. Every device-wide peak
measured on the owner's laptop must sit at or under it (no margin beyond the rounded-up fit), and
the bench's two-instrument check reports both figures and both bounds.
"""

from __future__ import annotations

from typing import Any

import pytest

import export_bench as bench
from clearwater.core import memory
from clearwater.core.backend import NumpyBackend, fft_memory_bound_bytes

MIB = 1024**2
K53 = (4648, 5312)  # height, width: the HERO13 5.3K 8:7 mode
K4 = (2160, 3840)


def _pool_estimate(height: int, width: int) -> int:
    """The GPU backend's pool estimate (``CupyBackend.memory_estimate_bytes``), without a GPU."""
    return memory.memory_estimate_bytes(height, width, "c3") + fft_memory_bound_bytes(height, width)


def _total(size: tuple[int, int], decoders: int, nvenc: bool = True) -> float:
    height, width = size
    return (
        memory.job_device_memory_estimate_bytes(
            height, width, _pool_estimate(height, width), decoders=decoders, nvenc=nvenc
        )
        / MIB
    )


@pytest.mark.parametrize(
    ("size", "kind", "measured_mib"),
    [
        (K53, "nvdec", 1256.0),  # the overlap's rise over the frames-only plateau (max)
        (K53, "nvenc", 1192.0),  # the frames-only remainder 2,448 less one decoder
        (K4, "nvdec", 690.4),  # 3,244 - 947 - 261, split in the 5.3K proportion
        (K4, "nvenc", 655.2),
    ],
)
def test_each_session_term_covers_its_fitted_point(
    size: tuple[int, int], kind: str, measured_mib: float
) -> None:
    fitted = memory.session_bytes(kind, *size) / MIB
    assert measured_mib <= fitted <= measured_mib + 32  # rounded up, never down


@pytest.mark.parametrize(
    ("row", "size", "decoders", "nvenc", "peak_mib"),
    [
        ("5.3K attribution, device frames ON", K53, 2, True, 7921.0),
        ("5.3K attribution, device frames OFF", K53, 2, True, 7593.0),
        ("5.3K task 10 block 2", K53, 2, True, 7854.0),
        ("5.3K WP3.14 baseline, one decoder, host frames", K53, 1, True, 6104.0),
        ("4K c3 cold 1", K4, 2, True, 3244.0),
        ("4K c3 cold 2", K4, 2, True, 3142.0),
        ("4K c3 cold 3", K4, 2, True, 3130.0),
        ("4K c3 warm, complete cache: one decoder", K4, 1, True, 2601.0),
        ("4K ancuti2018 cold", K4, 2, True, 3014.0),
        ("4K libx265 cold: no NVENC", K4, 2, False, 2761.0),
        ("4K c3 cold, device frames OFF", K4, 2, True, 2925.0),
        ("4K WP3.14 baseline c3 cold (serial analysis)", K4, 1, True, 2409.0),
        ("4K WP3.14 baseline libx265 (serial analysis)", K4, 1, False, 1937.0),
    ],
)
def test_the_job_estimate_covers_every_measured_device_wide_peak(
    row: str, size: tuple[int, int], decoders: int, nvenc: bool, peak_mib: float
) -> None:
    assert peak_mib <= _total(size, decoders, nvenc), row


def test_the_estimate_adds_the_pool_context_decoders_and_nvenc() -> None:
    height, width = K4
    pool = _pool_estimate(height, width)
    nvdec, nvenc = (memory.session_bytes(k, height, width) for k in ("nvdec", "nvenc"))
    got = memory.job_device_memory_estimate_bytes(height, width, pool, decoders=2, nvenc=True)
    assert got == pool + memory.CUDA_CONTEXT_BYTES + 2 * nvdec + nvenc
    without = memory.job_device_memory_estimate_bytes(height, width, pool, decoders=0, nvenc=False)
    assert without == pool + memory.CUDA_CONTEXT_BYTES


def test_1080p_is_the_same_line_extrapolated() -> None:
    assert memory.session_bytes("nvdec", 1080, 1920) == (
        memory.NVDEC_FLOOR_BYTES + memory.NVDEC_BYTES_PER_PIXEL * 1920 * 1080
    )


@pytest.mark.parametrize(
    "call",
    [
        lambda: memory.session_bytes("nvjpeg", 10, 10),
        lambda: memory.session_bytes("nvdec", 0, 10),
        lambda: memory.job_device_memory_estimate_bytes(10, 10, -1, decoders=1, nvenc=True),
        lambda: memory.job_device_memory_estimate_bytes(10, 10, 0, decoders=-1, nvenc=True),
    ],
)
def test_bad_inputs_are_refused(call: Any) -> None:
    with pytest.raises(ValueError):
        call()


class _Probe:
    class video:  # noqa: N801 - the ProbeResult attribute's name
        height, width = K53


class _GpuLike:
    device = "cuda:0"

    def memory_estimate_bytes(self, height: int, width: int, method_id: str) -> int:
        return _pool_estimate(height, width)


def _record(cache_complete: bool, encoder: str, device_peak: float) -> dict[str, Any]:
    return {
        "leg": {"method": "c3"},
        "cache_complete_at_start": cache_complete,
        "encoder": encoder,
        "telemetry": {"peak_gpu_memory_used_mib": device_peak},
        "before": {"gpu": {"memory.used": "248"}},
    }


def test_the_bench_check_reports_both_instruments_and_both_bounds() -> None:
    pool_peak = 4427 * MIB
    check = bench.memory_check(
        _record(False, "hevc_nvenc", 7921.0), _GpuLike(), _Probe(), pool_peak
    )  # type: ignore[arg-type]
    assert check["applies"] and check["decoders"] == 2 and check["nvenc"]
    assert check["job_estimate_mib"] == pytest.approx(_total(K53, 2), abs=0.1)
    assert check["pool_estimate_mib"] == pytest.approx(_pool_estimate(*K53) / MIB, abs=0.1)
    assert check["idle_before_mib"] == 248.0 and check["pool_peak_mib"] == 4427.0
    assert check["device_ok"] and check["pool_ok"] and check["passes"]
    line = bench._check_text(check)
    assert "device 7921.0 /" in line and "pool 4427.0 /" in line and "OVER" not in line


def test_the_bench_check_fails_on_either_instrument() -> None:
    over_device = bench.memory_check(_record(True, "libx265", 99999.0), _GpuLike(), _Probe(), 0)  # type: ignore[arg-type]
    assert over_device["decoders"] == 1 and not over_device["nvenc"]
    assert not over_device["device_ok"] and over_device["pool_ok"] and not over_device["passes"]
    over_pool = bench.memory_check(
        _record(False, "hevc_nvenc", 1.0),
        _GpuLike(),
        _Probe(),
        _pool_estimate(*K53) + 1,  # type: ignore[arg-type]
    )
    assert over_pool["device_ok"] and not over_pool["pool_ok"] and not over_pool["passes"]
    assert "OVER" in bench._check_text(over_pool)


def test_the_check_does_not_apply_without_a_pool() -> None:
    peak = bench._PoolPeak(NumpyBackend())
    peak.start()
    assert peak.stop() is None
    check = bench.memory_check(_record(False, "hevc_nvenc", 1.0), NumpyBackend(), _Probe(), None)  # type: ignore[arg-type]
    assert check == {"applies": False} and bench._check_text(check) == ""
