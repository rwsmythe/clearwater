"""WP3.1: ``select_backend`` reasons and the fallback rule (AD-1, AD-9, D111, N4; R0-5..R0-7).

The device is mocked by a fake ``cupy`` module served through the backend module's
``importlib``; one test at the end runs the real probe on the machine's GPU.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest

import clearwater.core.backend as backend_module
from clearwater.core import CupyBackend, NumpyBackend, memory_estimate_bytes, select_backend
from clearwater.interfaces.settings import Settings

NOT_INSTALLED = (
    backend_module.MACOS_CPU_REASON if sys.platform == "darwin" else "CPU: CuPy not installed"
)
"""The AD-9 reason for an absent CuPy on this platform (darwin's since WP6.4, AD-35)."""

MIB = 2**20
FOUR_K = (2160, 3840)


@pytest.fixture(autouse=True)
def fresh_probe() -> Iterator[None]:
    backend_module._probe_gpu.cache_clear()
    yield
    backend_module._probe_gpu.cache_clear()


class FakeDevice:
    """A CUDA device: driver free memory, pool free blocks, and failure switches."""

    def __init__(self, free: int, pool_free: int = 0, count: int = 1) -> None:
        self.free = free
        self.pool_free = pool_free
        self.count = count
        self.count_error: Exception | None = None
        self.kernel_error: Exception | None = None
        self.memory_error: Exception | None = None
        self.pool_error: Exception | None = None
        self.device_error: Exception | None = None

    def module(self) -> Any:
        device = self

        def get_device_count() -> int:
            if device.count_error is not None:
                raise device.count_error
            return device.count

        def arange(*args: Any, **kwargs: Any) -> Any:
            if device.kernel_error is not None:
                raise device.kernel_error
            return np.arange(*args, **kwargs)

        def get_device() -> int:
            if device.device_error is not None:
                raise device.device_error
            return 0

        def mem_get_info() -> tuple[int, int]:
            if device.memory_error is not None:
                raise device.memory_error
            return device.free, 8 * 1024 * MIB

        runtime = types.SimpleNamespace(
            getDeviceCount=get_device_count, getDevice=get_device, memGetInfo=mem_get_info
        )

        def pool_free_bytes() -> int:
            if device.pool_error is not None:
                raise device.pool_error
            return device.pool_free

        pool = types.SimpleNamespace(free_bytes=pool_free_bytes)
        return types.SimpleNamespace(
            __name__="cupy",
            ndarray=np.ndarray,
            float32=np.float32,
            arange=arange,
            asarray=np.asarray,
            cuda=types.SimpleNamespace(runtime=runtime),
            get_default_memory_pool=lambda: pool,
        )


def install(
    monkeypatch: pytest.MonkeyPatch,
    device: FakeDevice | None,
    error: Exception,
    ndimage_error: Exception | None = None,
) -> None:
    """Serve ``device`` as ``cupy``; with ``device=None`` importing ``cupy`` raises ``error``.

    ``ndimage_error``, when given, is raised by importing ``cupyx.scipy.ndimage``.
    """
    from scipy import ndimage

    def import_module(name: str) -> Any:
        if device is None:
            raise error
        if name == "cupy":
            return device.module()
        if name == "cupyx.scipy.ndimage":
            if ndimage_error is not None:
                raise ndimage_error
            return ndimage
        raise ImportError(name)

    monkeypatch.setattr(
        backend_module, "importlib", types.SimpleNamespace(import_module=import_module)
    )


def choose(force_cpu: bool = False, size: tuple[int, int] = FOUR_K) -> tuple[Any, str]:
    return select_backend(Settings(force_cpu=force_cpu), *size, "c3")


def test_forced(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, FakeDevice(free=8000 * MIB), ImportError())
    backend, reason = choose(force_cpu=True)
    assert reason == "CPU: forced" and isinstance(backend, NumpyBackend)


def test_cupy_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, None, ModuleNotFoundError("No module named 'cupy'", name="cupy"))
    backend, reason = choose()
    assert reason == NOT_INSTALLED and isinstance(backend, NumpyBackend)


def test_cupy_absent_from_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(__import__("sys").modules, "cupy", None)  # import raises ImportError
    backend, reason = choose()
    assert reason == NOT_INSTALLED and isinstance(backend, NumpyBackend)


def test_cupy_failed_to_load(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, None, OSError("DLL load failed"))
    assert choose()[1] == "CPU: CuPy failed to load"


def test_cupyx_failed_to_load(monkeypatch: pytest.MonkeyPatch) -> None:
    device = FakeDevice(free=8000 * MIB)
    install(monkeypatch, device, ImportError(), ndimage_error=ImportError("cupyx"))
    assert choose()[1] == "CPU: CuPy failed to load"
    backend_module._probe_gpu.cache_clear()
    install(monkeypatch, device, ImportError(), ndimage_error=OSError("nvrtc DLL"))
    assert choose()[1] == "CPU: CuPy failed to load"


def test_no_device(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, FakeDevice(free=8000 * MIB, count=0), ImportError())
    assert choose()[1] == "CPU: no CUDA device"
    backend_module._probe_gpu.cache_clear()
    device = FakeDevice(free=8000 * MIB)
    device.count_error = RuntimeError("cudaErrorNoDevice")
    install(monkeypatch, device, ImportError())
    assert choose()[1] == "CPU: no CUDA device"


def test_device_unusable(monkeypatch: pytest.MonkeyPatch) -> None:
    device = FakeDevice(free=8000 * MIB)
    device.kernel_error = RuntimeError("nvrtc: cannot open source file")
    install(monkeypatch, device, ImportError())
    assert choose()[1] == "CPU: CUDA device unusable"


def test_device_acquisition_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    # Round 1 F3: CuPy and cupyx loaded and a device is counted, but the backend cannot bind
    # the current device: that is an unusable device, not a CuPy that failed to load.
    device = FakeDevice(free=8000 * MIB)
    device.device_error = RuntimeError("cudaErrorDevicesUnavailable")
    install(monkeypatch, device, ImportError())
    backend, reason = choose()
    assert reason == "CPU: CUDA device unusable" and isinstance(backend, NumpyBackend)


def test_free_memory_failure_after_the_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    # Round 1 F2: the probe is cached, free memory is read on every call; a driver failure
    # there (a TDR, a lost context) falls back to the CPU instead of escaping.
    device = FakeDevice(free=4000 * MIB)
    install(monkeypatch, device, ImportError())
    assert choose()[1] == "GPU"
    device.memory_error = RuntimeError("cudaErrorLaunchFailure")
    backend, reason = choose()
    assert reason == "CPU: CUDA device unusable" and isinstance(backend, NumpyBackend)
    device.memory_error = None
    assert choose()[1] == "GPU"  # read again on the next call


def test_pool_failure_after_the_probe(monkeypatch: pytest.MonkeyPatch) -> None:
    device = FakeDevice(free=4000 * MIB)
    install(monkeypatch, device, ImportError())
    assert choose()[1] == "GPU"
    device.pool_error = RuntimeError("cudaErrorIllegalAddress")
    assert choose()[1] == "CPU: CUDA device unusable"


def test_fits(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, FakeDevice(free=4000 * MIB), ImportError())
    backend, reason = choose()
    assert reason == "GPU" and isinstance(backend, CupyBackend)
    assert backend.name == "cupy" and backend.device == "cuda:0"


def test_does_not_fit_reason_exactly(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, FakeDevice(free=1200 * MIB + MIB // 2), ImportError())
    backend, reason = choose()
    assert reason == "CPU: estimate 1,982 MiB exceeds free 1,200 MiB"  # IF-2's own example
    assert isinstance(backend, NumpyBackend)


def test_boundary_is_strict(monkeypatch: pytest.MonkeyPatch) -> None:
    estimate = memory_estimate_bytes(*FOUR_K, "c3")
    device = FakeDevice(free=estimate)
    install(monkeypatch, device, ImportError())
    assert choose()[1] == "CPU: estimate 1,982 MiB exceeds free 1,981 MiB"
    device.free = estimate + 1  # free memory is read on every call; the probe is cached
    assert choose()[1] == "GPU"


def test_second_frame_stays_on_gpu(monkeypatch: pytest.MonkeyPatch) -> None:
    # Frame 1 leaves its working set in CuPy's pool: the driver now counts it as used.
    estimate = memory_estimate_bytes(*FOUR_K, "c3")
    device = FakeDevice(free=estimate + 300 * MIB)
    install(monkeypatch, device, ImportError())
    assert choose()[1] == "GPU"
    device.free -= estimate
    device.pool_free = estimate
    assert choose()[1] == "GPU"
    device.pool_free = 0  # without the pool's free blocks the frame would have fallen back
    assert choose()[1].startswith("CPU: estimate")


def test_planted_driver_only_free_flips_frame_two(monkeypatch: pytest.MonkeyPatch) -> None:
    # R0-7 positive control: an implementation that ignores the pool's free blocks sends the
    # second same-size frame to the CPU; the product's keeps it on the GPU.
    estimate = memory_estimate_bytes(*FOUR_K, "c3")
    device = FakeDevice(free=estimate + 300 * MIB)
    install(monkeypatch, device, ImportError())
    assert choose()[1] == "GPU"  # frame 1
    device.free -= estimate  # frame 1's blocks are back in the pool, used for the driver
    device.pool_free = estimate
    assert choose()[1] == "GPU"  # frame 2, product

    def driver_only(self: CupyBackend) -> int:
        free, _total = self.xp.cuda.runtime.memGetInfo()
        return int(free)

    monkeypatch.setattr(CupyBackend, "free_device_bytes", driver_only)
    assert choose()[1] == "CPU: estimate 1,982 MiB exceeds free 300 MiB"  # frame 2, planted


def test_unknown_method_and_bad_size_refused(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, FakeDevice(free=8000 * MIB), ImportError())
    with pytest.raises(ValueError, match="no memory estimate"):
        select_backend(Settings(force_cpu=True), 10, 10, "unknown")
    with pytest.raises(ValueError, match="at least 1"):
        select_backend(Settings(), 0, 10, "c3")


def test_interface_level_select_backend_unchanged() -> None:
    from clearwater.interfaces import backend as interface

    with pytest.raises(NotImplementedError, match=r"WP3.1"):
        interface.select_backend(Settings(), 10, 10, "c3")


@pytest.mark.gpu
def test_real_device_small_frame_selects_gpu() -> None:
    backend, reason = select_backend(Settings(), 720, 1280, "c3")
    if reason != "GPU":
        pytest.skip(reason)
    assert isinstance(backend, CupyBackend)
    huge = select_backend(Settings(), 60000, 60000, "ancuti2018")[1]
    assert huge.startswith("CPU: estimate ") and huge.endswith(" MiB")
