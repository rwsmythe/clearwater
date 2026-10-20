"""WP3.1: ``select_backend`` reasons and the fallback rule (AD-1, AD-9, D111, N4; R0-5..R0-7).

The device is mocked by a fake ``cupy`` module served through the backend module's
``importlib``; one test at the end runs the real probe on the machine's GPU.
"""

from __future__ import annotations

import types
from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest

import clearwater.core.backend as backend_module
from clearwater.core import CupyBackend, NumpyBackend, memory_estimate_bytes, select_backend
from clearwater.interfaces.settings import Settings

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

        runtime = types.SimpleNamespace(
            getDeviceCount=get_device_count,
            getDevice=lambda: 0,
            memGetInfo=lambda: (device.free, 8 * 1024 * MIB),
        )
        pool = types.SimpleNamespace(free_bytes=lambda: device.pool_free)
        return types.SimpleNamespace(
            __name__="cupy",
            ndarray=np.ndarray,
            float32=np.float32,
            arange=arange,
            asarray=np.asarray,
            cuda=types.SimpleNamespace(runtime=runtime),
            get_default_memory_pool=lambda: pool,
        )


def install(monkeypatch: pytest.MonkeyPatch, device: FakeDevice | None, error: Exception) -> None:
    """Serve ``device`` as ``cupy``; with ``device=None`` importing ``cupy`` raises ``error``."""
    from scipy import ndimage

    def import_module(name: str) -> Any:
        if device is None:
            raise error
        if name == "cupy":
            return device.module()
        if name == "cupyx.scipy.ndimage":
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
    install(monkeypatch, None, ModuleNotFoundError("No module named 'cupy'"))
    backend, reason = choose()
    assert reason == "CPU: CuPy not installed" and isinstance(backend, NumpyBackend)


def test_cupy_absent_from_sys_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setitem(__import__("sys").modules, "cupy", None)  # import raises ImportError
    backend, reason = choose()
    assert reason == "CPU: CuPy not installed" and isinstance(backend, NumpyBackend)


def test_cupy_failed_to_load(monkeypatch: pytest.MonkeyPatch) -> None:
    install(monkeypatch, None, OSError("DLL load failed"))
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
