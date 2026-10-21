"""WP3.4: the banked core fixes and ``backend_for`` (DR-37 a, DR-38 c and d; question 2).

Each fix has a planted counterpart: the pre-fix behaviour, run on the same input, gives the
defect the register names, so each test distinguishes the fix from the code it replaced.
"""

from __future__ import annotations

import math
import sys
import types
from collections.abc import Iterator
from typing import Any

import numpy as np
import pytest

import clearwater.core as core
import clearwater.core.backend as backend_module
from clearwater.core import (
    MAX_KERNEL_RADIUS,
    CupyBackend,
    NumpyBackend,
    backend_for,
    check_sigma,
    select_backend,
)
from clearwater.interfaces.settings import Settings

REASONS = (
    "GPU",
    "CPU: forced",
    "CPU: CuPy not installed",
    "CPU: CuPy failed to load",
    "CPU: no CUDA device",
    "CPU: CUDA device unusable",
)
"""The WP3.1 report's reason list (the estimate reason aside); DR-37 (a) adds none."""


@pytest.fixture(autouse=True)
def fresh_probe() -> Iterator[None]:
    backend_module._probe_gpu.cache_clear()
    yield
    backend_module._probe_gpu.cache_clear()


def import_raising(monkeypatch: pytest.MonkeyPatch, error: Exception) -> None:
    """Make every import through the backend module's ``importlib`` raise ``error``."""

    def import_module(name: str) -> Any:
        raise error

    monkeypatch.setattr(
        backend_module, "importlib", types.SimpleNamespace(import_module=import_module)
    )


def reason() -> str:
    return select_backend(Settings(), 64, 64, "c3")[1]


def pre_fix_reason(error: Exception) -> str:
    """The WP3.1 probe's classification (``except ImportError`` -> "not installed")."""
    if isinstance(error, ImportError):
        return "CPU: CuPy not installed"
    return "CPU: CuPy failed to load"


# -- DR-37 (a) ------------------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (ModuleNotFoundError("No module named 'cupy'", name="cupy"), "CPU: CuPy not installed"),
        # an installed CuPy whose own submodule or dependency is missing, or whose DLL fails
        (ModuleNotFoundError("No module named 'cupy._core'", name="cupy._core"), "failed"),
        (ModuleNotFoundError("No module named 'fastrlock'", name="fastrlock"), "failed"),
        (ImportError("DLL load failed while importing core"), "failed"),
        (ImportError("CuPy is not correctly installed", name="cupy"), "failed"),
        (ModuleNotFoundError("hand-made, names no module"), "failed"),
        (OSError("nvrtc64_120_0.dll not found"), "failed"),
    ],
)
def test_dr37a_only_a_missing_cupy_is_not_installed(
    monkeypatch: pytest.MonkeyPatch, error: Exception, expected: str
) -> None:
    import_raising(monkeypatch, error)
    got = reason()
    want = "CPU: CuPy failed to load" if expected == "failed" else expected
    assert got == want
    assert got in REASONS


def test_dr37a_planted_pre_fix_rule_misnames_an_import_error() -> None:
    # The register's case: an installed CuPy failing with a plain ImportError. The WP3.1 rule
    # called it "not installed"; the product says "failed to load" (test above).
    assert pre_fix_reason(ImportError("DLL load failed")) == "CPU: CuPy not installed"


def test_dr37a_cupy_blocked_in_sys_modules_is_not_installed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "cupy", None)
    with pytest.raises(ModuleNotFoundError) as caught:
        __import__("cupy")
    assert caught.value.name == "cupy"
    assert reason() == "CPU: CuPy not installed"


# -- DR-38 (c): check_rgb refuses an empty spatial size ---------------------------------------------


@pytest.mark.parametrize("shape", [(0, 1, 3), (1, 0, 3), (0, 0, 3)])
def test_dr38c_check_rgb_refuses_empty(shape: tuple[int, int, int]) -> None:
    backend = NumpyBackend()
    with pytest.raises(ValueError, match="H, W >= 1"):
        backend.check_rgb(np.zeros(shape, dtype=np.float32))
    # check_spatial already refused it; the two checks now agree
    with pytest.raises(ValueError):
        backend.check_spatial(np.zeros(shape, dtype=np.float32))


def test_dr38c_check_rgb_still_accepts_one_pixel_and_refuses_other_shapes() -> None:
    backend = NumpyBackend()
    backend.check_rgb(np.zeros((1, 1, 3), dtype=np.float32))
    for shape in ((2, 2), (2, 2, 4), (2, 2, 3, 1)):
        with pytest.raises(ValueError):
            backend.check_rgb(np.zeros(shape, dtype=np.float32))
    with pytest.raises(ValueError, match="float32"):
        backend.check_rgb(np.zeros((1, 1, 3), dtype=np.float64))
    with pytest.raises(TypeError):
        backend.check_rgb([[[0.0, 0.0, 0.0]]])


def test_dr38c_planted_pre_fix_check_accepts_empty() -> None:
    a = np.zeros((0, 1, 3), dtype=np.float32)
    assert a.ndim == 3 and a.shape[2] == 3  # the WP3.1 condition: nothing refused it


def test_dr38c_channel_means_refuses_empty() -> None:
    with pytest.raises(ValueError, match="H, W >= 1"):
        core.channel_means(NumpyBackend(), np.zeros((0, 4, 3), dtype=np.float32))


# -- DR-38 (d): check_sigma raises ValueError, never OverflowError -------------------------------------


@pytest.mark.parametrize("sigma", [1e308, sys.float_info.max, 4.5e307])
def test_dr38d_overflowing_radius_is_a_value_error(sigma: float) -> None:
    assert math.isinf(4.0 * sigma)  # the radius int(4 * sigma + 0.5) cannot be formed
    with pytest.raises(ValueError, match="radius beyond"):
        check_sigma(sigma)
    with pytest.raises(OverflowError):  # the pre-fix expression
        int(4.0 * sigma + 0.5)


def test_dr38d_bound_and_messages_unchanged() -> None:
    check_sigma(MAX_KERNEL_RADIUS / 4.0 - 0.2)  # radius exactly 2 ** 23 is accepted
    with pytest.raises(ValueError, match="radius beyond"):
        check_sigma((MAX_KERNEL_RADIUS + 1) / 4.0)
    for bad in (0.0, -1.0, math.nan, math.inf):
        with pytest.raises(ValueError, match="finite and positive"):
            check_sigma(bad)


# -- question 2: backend_for ------------------------------------------------------------------------


def test_backend_for_cpu_is_the_process_numpy_backend() -> None:
    backend = backend_for("cpu")
    assert isinstance(backend, NumpyBackend)
    assert backend is backend_for("cpu")
    assert backend is select_backend(Settings(force_cpu=True), 8, 8, "c3")[0]


def test_backend_for_cpu_does_not_probe_the_gpu(monkeypatch: pytest.MonkeyPatch) -> None:
    import_raising(monkeypatch, AssertionError("cpu must not import cupy"))
    assert backend_for("cpu").device == "cpu"


@pytest.mark.parametrize("device", ["", "CPU", "gpu", "cuda", "cuda:7", "cpu:0"])
def test_backend_for_refuses_other_devices(device: str) -> None:
    with pytest.raises(ValueError, match="no backend for device"):
        backend_for(device)


def test_backend_for_without_gpu_names_the_reason(monkeypatch: pytest.MonkeyPatch) -> None:
    import_raising(monkeypatch, ModuleNotFoundError("No module named 'cupy'", name="cupy"))
    with pytest.raises(ValueError, match=r"'cuda:0'; available: cpu \(CPU: CuPy not installed\)"):
        backend_for("cuda:0")


@pytest.mark.gpu
def test_backend_for_gpu_is_the_probed_backend() -> None:
    gpu, why = backend_module._probe_gpu()
    if gpu is None:
        pytest.skip(why)
    backend = backend_for(gpu.device)
    assert isinstance(backend, CupyBackend) and backend is gpu
    settings = Settings()
    chosen, chosen_reason = select_backend(settings, 64, 64, "c3")
    if chosen_reason == "GPU":
        assert chosen is backend


def test_backend_for_exported() -> None:
    assert "backend_for" in core.__all__
