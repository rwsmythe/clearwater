"""WP3.16 status bar (AD-9, question 4, G12 surfaced, DR-37 (a) trigger) and the S1 adapter.

Covers the task-8 row "status bar": every reason string of ``select_backend`` shown verbatim,
``"CPU: forced"`` after ``force_cpu`` is set, and one ``gpu`` test with the real selection.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import threading
from pathlib import Path

import pytest

import gui_support
from clearwater.gui.engines import STUB_ERA_METHOD_ID, default_engines, stub_era_select_backend
from clearwater.interfaces import Settings
from clearwater.interfaces.stubs import StubArrayBackend
from gui_support import (
    LevelMethod,
    image,
    make_window,
    open_and_wait,
    photo_engines,
    presenter_of,
    wait_idle,
)

pytestmark = pytest.mark.gui

REASONS = (
    "GPU",
    "CPU: forced",
    "CPU: CuPy not installed",
    "CPU: CuPy failed to load",
    "CPU: no CUDA device",
    "CPU: CUDA device unusable",
    "CPU: estimate 1,982 MiB exceeds free 1,200 MiB",
)


def _fixed(full: str, preview: str | None = None, calls: list | None = None):
    def select(settings: Settings, height: int, width: int, method_id: str):
        if calls is not None:
            calls.append((threading.current_thread(), height, width, method_id))
        big = height * width >= 600 * 800
        return StubArrayBackend(), full if big or preview is None else preview

    return select


def test_device_is_a_dash_before_a_file_is_open(make_window) -> None:
    window = make_window()
    assert window.device_label.text() == "Device: -"


def test_a_failed_render_still_reports_the_device(make_window, qtbot) -> None:
    # Round-1 F5: the selection succeeded, the render failed; the status bar follows the selection.
    path = Path("p.png")
    method = LevelMethod()

    def explode() -> None:
        raise RuntimeError("boom")

    method.busy = explode
    engines = photo_engines({path: image(40, 60)}, methods={method.id: method})
    window = make_window(engines)
    open_and_wait(qtbot, window, path)
    wait_idle(qtbot, window)
    assert presenter_of(window).of("error")
    assert window.device_label.text() == "Device: CPU: stub"
    window.session.set_settings(Settings(force_cpu=True))
    wait_idle(qtbot, window)
    assert window.device_label.text() == "Device: CPU: forced"


@pytest.mark.parametrize("reason", REASONS)
def test_every_select_backend_reason_is_shown_verbatim(make_window, qtbot, reason: str) -> None:
    path = Path("p.png")
    window = make_window(photo_engines({path: image(40, 60)}, select_backend=_fixed(reason)))
    open_and_wait(qtbot, window, path)
    assert window.device_label.text() == f"Device: {reason}"
    assert window.session.backend() == reason


def test_preview_reason_goes_to_the_tooltip_when_it_differs(make_window, qtbot) -> None:
    path = Path("p.png")
    calls: list = []
    select = _fixed("CPU: estimate 1,982 MiB exceeds free 1,200 MiB", "GPU", calls)
    window = make_window(
        photo_engines({path: image(600, 800)}, select_backend=select), size=(300, 250)
    )
    open_and_wait(qtbot, window, path)
    assert window.device_label.text().startswith("Device: CPU: estimate")
    assert window.device_label.toolTip() == "Preview: GPU"
    sizes = {(h, w) for _, h, w, _ in calls}
    assert (600, 800) in sizes  # the full-resolution decision (what export uses)
    assert all(t is not threading.main_thread() for t, _, _, _ in calls)
    assert all(m == "stub" for _, _, _, m in calls)


def test_force_cpu_shows_cpu_forced(make_window, qtbot) -> None:
    path = Path("p.png")
    window = make_window(photo_engines({path: image(40, 60)}))
    open_and_wait(qtbot, window, path)
    assert window.device_label.text() == "Device: CPU: stub"
    window.session.set_settings(Settings(force_cpu=True))
    wait_idle(qtbot, window)
    assert window.device_label.text() == "Device: CPU: forced"
    window.session.set_settings(Settings())
    wait_idle(qtbot, window)
    assert window.device_label.text() == "Device: CPU: stub"


def test_status_bar_shows_file_size_and_zoom(make_window, qtbot) -> None:
    path = Path("reef.png")
    window = make_window(photo_engines({path: image(300, 400)}))
    open_and_wait(qtbot, window, path)
    assert window.file_label.text() == "reef.png"
    assert window.size_label.text() == "400 x 300"
    assert window.zoom_label.text().startswith("Fit (")
    window.view_actions["one_to_one"].trigger()
    assert window.zoom_label.text() == "100%"


def test_stub_era_adapter_estimates_an_unknown_method_as_c3(monkeypatch) -> None:
    from clearwater import core

    seen: list[str] = []

    def fake(settings: Settings, height: int, width: int, method_id: str):
        seen.append(method_id)
        return StubArrayBackend(), "CPU: forced"

    monkeypatch.setattr(core, "select_backend", fake)
    stub_era_select_backend(Settings(), 10, 10, "stub")
    stub_era_select_backend(Settings(), 10, 10, "ancuti2018")
    assert seen == [STUB_ERA_METHOD_ID, "ancuti2018"]
    assert default_engines().select_backend is stub_era_select_backend


def test_default_engines_select_cpu_forced_with_the_real_selection() -> None:
    backend, reason = default_engines().select_backend(Settings(force_cpu=True), 100, 100, "stub")
    assert reason == "CPU: forced" and backend.device == "cpu"


@pytest.mark.gpu
def test_real_selection_through_the_shell_shows_gpu(make_window, qtbot) -> None:
    pytest.importorskip("cupy")
    _, probe_reason = stub_era_select_backend(Settings(), 64, 64, "stub")
    if probe_reason != "GPU":
        pytest.skip(f"no usable CUDA device: {probe_reason}")
    path = Path("p.png")
    engines = photo_engines({path: image(120, 160)}, select_backend=stub_era_select_backend)
    window = make_window(engines)
    open_and_wait(qtbot, window, path, timeout_ms=60000)
    assert window.device_label.text() == "Device: GPU"
    window.session.set_settings(Settings(force_cpu=True))
    wait_idle(qtbot, window)
    assert window.device_label.text() == "Device: CPU: forced"
