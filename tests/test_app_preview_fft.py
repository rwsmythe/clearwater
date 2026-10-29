"""WP4.3 task 7, DR-68 (question 6 as ruled): the preview's FFT plans released at its boundaries.

cuFFT plans are per thread, so the release runs ON the preview worker's thread
(``clearwater-preview``), as a CHORE of its latest-wins worker: never superseded, run before the
next task and before the thread ends. The boundaries: a source change or unload, the shell's
close, and before an export or batch job of the GUI process selects its backend
(``PreviewController.release_device_plans``). It goes through ONE consumer-side
``runtime_checkable`` Protocol in ``clearwater.gui`` (AD-29): ``CupyBackend`` satisfies it and
``NumpyBackend`` does not; ``clearwater.gui`` imports no CuPy (``tests/test_gui_deps.py``). The
``gpu`` test reads ``free_device_bytes()`` before a 1:1 render of a 4K frame on the FFT route,
after it, and after the boundary; a planted controller without the release fails by name.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import gui_support
from clearwater import core
from clearwater.app import composition
from clearwater.core.backend import (
    FFT_MIN_SHORT_SIDE,
    CupyBackend,
    NumpyBackend,
    backend_for,
)
from clearwater.gui.preview import PreviewController
from clearwater.gui.render_worker import LatestWorker, PreviewDeviceBackend
from clearwater.interfaces import Settings
from gui_support import image, make_window, open_and_wait, photo_engines, wait_idle

pytestmark = pytest.mark.gui


def test_the_protocol_is_the_gpu_backends_only() -> None:
    """AD-29: the same name and signature as ``CupyBackend``'s; the CPU backend lacks it."""
    assert issubclass(CupyBackend, PreviewDeviceBackend)
    assert not issubclass(NumpyBackend, PreviewDeviceBackend)
    assert not isinstance(NumpyBackend(), PreviewDeviceBackend)


# The chore: never superseded, on the worker's thread, before the next task and at stop.


def test_a_chore_runs_on_the_worker_thread_before_the_next_task_and_is_never_superseded(
    qtbot: Any,
) -> None:
    order: list[tuple[str, str]] = []
    gate = threading.Event()
    worker = LatestWorker("clearwater-test", lambda outcome: None)

    def blocking(check: Any) -> None:
        order.append(("task-1", threading.current_thread().name))
        assert gate.wait(5)

    worker.submit(blocking)
    qtbot.waitUntil(lambda: bool(order), timeout=5000)
    assert worker.run_chore(lambda: order.append(("chore", threading.current_thread().name)))
    worker.submit(lambda check: order.append(("task-2", threading.current_thread().name)))
    worker.invalidate()  # supersedes task 2, never the chore
    worker.submit(lambda check: order.append(("task-3", threading.current_thread().name)))
    gate.set()
    qtbot.waitUntil(worker.idle, timeout=5000)
    assert order == [
        ("task-1", "clearwater-test"),
        ("chore", "clearwater-test"),
        ("task-3", "clearwater-test"),
    ]
    stopped: list[str] = []
    worker.run_chore(lambda: stopped.append(threading.current_thread().name))
    assert worker.stop(5)
    assert stopped == ["clearwater-test"]  # a chore queued before stop runs before the end
    assert worker.run_chore(lambda: None) is False


# The boundaries, with a backend that records where it released.


class RecordingBackend(NumpyBackend):
    """The CPU backend plus the device extension, recording each release's thread."""

    def __init__(self) -> None:
        super().__init__()
        self.releases: list[str] = []

    def release_fft_plans(self) -> None:
        self.releases.append(threading.current_thread().name)


def _recording(backend: RecordingBackend) -> Any:
    def select(settings: Settings, height: int, width: int, method_id: str) -> Any:
        return backend, "GPU"

    return select


def test_the_release_runs_on_the_preview_thread_at_every_boundary(make_window, qtbot) -> None:
    backend = RecordingBackend()
    first, second = Path("first.png"), Path("second.png")
    engines = photo_engines(
        {first: image(60, 80), second: image(60, 80, seed=2)}, select_backend=_recording(backend)
    )
    window = make_window(engines)
    open_and_wait(qtbot, window, first)
    assert backend.releases == []  # the first source change: nothing rendered, nothing held
    open_and_wait(qtbot, window, second)
    assert backend.releases == ["clearwater-preview"]  # the source change
    assert window.controller.release_device_plans(5)  # before a job of the GUI process selects
    assert backend.releases == ["clearwater-preview"] * 2
    window.close()
    assert backend.releases == ["clearwater-preview"] * 3  # the shell's close
    assert window.controller.release_device_plans(0.5) is False  # stopped: never runs


def test_a_release_asked_from_a_job_thread_runs_after_the_render_in_flight(
    make_window, qtbot
) -> None:
    backend = RecordingBackend()
    path = Path("p.png")
    window = make_window(photo_engines({path: image(60, 80)}, select_backend=_recording(backend)))
    open_and_wait(qtbot, window, path)
    box: dict[str, bool] = {}

    def job() -> None:
        box["ok"] = window.controller.release_device_plans(5)

    window.session.set_parameters(window.session.parameters())  # a render is submitted
    thread = threading.Thread(target=job, name="clearwater-job")
    thread.start()
    thread.join(10)
    wait_idle(qtbot, window)
    assert box == {"ok": True} and backend.releases[-1] == "clearwater-preview"


# DR-68's gpu test: the device reading returns to its pre-preview figure after the boundary.

ONE_POOL_BLOCK = 2 * 1024**2
"""The tolerance of the device reading: one pool block (CuPy rounds blocks up; the driver's
free figure moves by its own page size)."""


def _gpu() -> CupyBackend:
    pytest.importorskip("cupy")
    _, reason = core.select_backend(Settings(), 64, 64, "c3")
    if reason != "GPU":
        pytest.skip(f"no usable CUDA device: {reason}")
    gpu = backend_for("cuda:0")
    assert isinstance(gpu, CupyBackend)
    return gpu


def _preview_plans(window: Any) -> int:
    """The preview thread's cuFFT plan count, read on that thread by a chore."""
    box: list[int] = []
    done = threading.Event()

    def read() -> None:
        import cupy

        box.append(cupy.fft.config.get_plan_cache().get_curr_size())
        done.set()

    window.controller._renderer.run_chore(read)
    assert done.wait(30)
    return box[0]


def _plans_scenario(make_window: Any, qtbot: Any, gpu: CupyBackend) -> dict[str, int]:
    """Render a 4K photo at 1:1 on the GPU's FFT route, then cross a boundary; return readings.

    Raises:
        AssertionError: "the preview's FFT plans were not released at the boundary" when the
            reading or the plan count does not come back.
    """
    warm = gpu.asarray(np.zeros((FFT_MIN_SHORT_SIDE, 1920), dtype=np.float32))
    gpu.gaussian_blur(warm, 54.0)  # cuFFT loaded in this process, so the reading is stable
    del warm
    gpu.release_fft_plans()
    big, small = Path("uhd.png"), Path("small.png")
    engines = photo_engines(
        {big: image(2160, 3840, seed=3), small: image(60, 80)},
        methods=composition.correction_methods(),
        select_backend=core.select_backend,
    )
    window = make_window(engines, size=(900, 700))

    def one_to_one() -> None:
        open_and_wait(qtbot, window, big, timeout_ms=120000)
        window.view_actions["one_to_one"].trigger()
        wait_idle(qtbot, window, timeout_ms=120000)
        assert window.preview_widget.shown_factor() == 1  # the 1:1 render, k = 1

    # A first pass loads the method's kernels on the device (a one-time cost of the process,
    # not the plans'), so the pre-preview figure is the warmed process's.
    one_to_one()
    open_and_wait(qtbot, window, small, timeout_ms=60000)
    before = int(gpu.free_device_bytes() or 0)
    one_to_one()
    plans_after_render = _preview_plans(window)
    after_render = int(gpu.free_device_bytes() or 0)
    open_and_wait(qtbot, window, small, timeout_ms=60000)  # the boundary: a source change
    plans_after_boundary = _preview_plans(window)
    after_boundary = int(gpu.free_device_bytes() or 0)
    readings = {
        "before": before,
        "after_render": after_render,
        "after_boundary": after_boundary,
        "plans_after_render": plans_after_render,
        "plans_after_boundary": plans_after_boundary,
    }
    assert plans_after_render > 0, f"the 1:1 4K render made no FFT plan: {readings}"
    released = plans_after_boundary == 0 and abs(after_boundary - before) <= ONE_POOL_BLOCK
    assert released, f"the preview's FFT plans were not released at the boundary: {readings}"
    assert after_render < before - ONE_POOL_BLOCK, f"the plans held no device memory: {readings}"
    return readings


@pytest.mark.gpu
def test_the_device_reading_returns_after_the_boundary(make_window, qtbot) -> None:
    gpu = _gpu()
    readings = _plans_scenario(make_window, qtbot, gpu)
    print(f"DR-68 readings: {readings}")  # shown with -rP: the three device figures
    assert readings["plans_after_boundary"] == 0


@pytest.mark.gpu
def test_a_planted_controller_without_the_release_fails_by_name(
    make_window, qtbot, monkeypatch
) -> None:
    gpu = _gpu()
    monkeypatch.setattr(PreviewController, "_release_plans", lambda self: None)
    with pytest.raises(AssertionError, match="FFT plans were not released at the boundary"):
        _plans_scenario(make_window, qtbot, gpu)
    # The planted controller left the plans on the preview thread; the window's close joins it.
