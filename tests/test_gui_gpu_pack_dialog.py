"""Offscreen GPU request/dialog/menu checks; the real downloader never runs here."""

# The shared fixture is imported for pytest discovery.
# ruff: noqa: F401, F811

from __future__ import annotations

import os

os.environ["QT_QPA_PLATFORM"] = "offscreen"

import threading
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from clearwater import gpu_pack, gpu_pack_install
from clearwater.gui import gpu_pack_dialog as module
from clearwater.gui.jobs import QtProgress
from clearwater.interfaces import JobResult
from gui_support import image, make_window, open_and_wait, photo_engines, presenter_of

pytestmark = [pytest.mark.gui, pytest.mark.timeout(10)]

LICENSE = (
    "GPU support downloads CuPy and NVIDIA's CUDA runtime libraries from PyPI into your user "
    "folder. The NVIDIA libraries are provided by NVIDIA under the NVIDIA Software License "
    "Agreement (the file `License.txt` in each NVIDIA package's `.dist-info` folder after the "
    "install); CuPy is MIT. Clearwater does not redistribute them."
)


@pytest.fixture(autouse=True)
def isolated_pack(monkeypatch, tmp_path):
    for variable in (
        "APPDATA",
        "LOCALAPPDATA",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
    ):
        monkeypatch.setenv(variable, str(tmp_path / variable))
    root = tmp_path / "packs"
    monkeypatch.setattr(gpu_pack, "pack_root", lambda: root)
    monkeypatch.setattr(gpu_pack, "activation_status", lambda: None, raising=False)
    monkeypatch.setattr(gpu_pack_install, "install", lambda _: pytest.fail("real install"))
    monkeypatch.setattr(gpu_pack_install, "remove", lambda: pytest.fail("real remove"))
    return root


class ScriptedJob:
    def __init__(self):
        self.progress = QtProgress()
        self.running = True

    def cancel(self):
        self.progress.cancel()

    def is_running(self):
        return self.running


class ScriptedRunner:
    def __init__(self):
        self.calls = []

    def run(self, job, *, on_done, on_progress=None):
        handle = ScriptedJob()
        self.calls.append((job, on_done, on_progress, handle))
        return handle

    def report(self, done, total, wheel):
        self.calls[-1][2](done, total, wheel)

    def finish(self, result):
        _, callback, _, handle = self.calls[-1]
        handle.running = False
        callback(result)


def _result(ok=True, text=""):
    return JobResult(ok, (), (text,) if ok else (), None if ok else text, "unknown", 0)


def _actions(window):
    tools = next(a.menu() for a in window.menuBar().actions() if a.text() == "&Tools")
    return tools, {a.text(): a for a in tools.actions()}


def _open(window, monkeypatch):
    script = ScriptedRunner()
    monkeypatch.setattr(window.jobs, "run", script.run)
    _, actions = _actions(window)
    actions["Install GPU support..."].trigger()
    dialog = window._gpu_pack_dialog
    assert dialog.isVisible()
    assert dialog.windowModality() == Qt.WindowModality.WindowModal
    return dialog, script, actions


def test_menu_opens_explicit_request_with_computed_plan(make_window, monkeypatch, isolated_pack):
    window = make_window()
    dialog, script, _ = _open(window, monkeypatch)
    assert script.calls == []
    plan = gpu_pack_install.plan()
    text = dialog.plan_text.toPlainText()
    for wheel in plan.wheels:
        assert f"{wheel.name} {wheel.version}" in text
    assert f"{plan.download_size:,} bytes" in text
    assert f"{plan.installed_size:,} bytes" in text
    assert str(isolated_pack / plan.stamp) in text
    assert dialog.license_text.text() == LICENSE
    assert gpu_pack_install.LICENSE_TEXT == module.LICENSE_TEXT
    assert dialog.install_button.text() == "Download and install"
    dialog.reject()
    assert not dialog.isVisible()


def test_progress_cancel_and_cleanup_completion(make_window, monkeypatch):
    window = make_window()
    dialog, script, actions = _open(window, monkeypatch)
    dialog.install_button.click()
    assert len(script.calls) == 1
    assert not actions["Install GPU support..."].isEnabled()
    assert not actions["Remove GPU support"].isEnabled()
    script.report(1, 4, "wheel-two.whl")
    assert dialog.progress_bar.value() == 250
    assert dialog.current_wheel.text() == "wheel-two.whl"
    dialog.cancel_button.click()
    assert script.calls[0][3].progress.cancelled()
    assert dialog.isVisible()  # cancellation waits for worker cleanup
    assert not dialog.cancel_button.isEnabled()
    script.finish(_result(False, "GPU support installation cancelled"))
    assert dialog.status.text() == "GPU support installation cancelled"
    assert actions["Install GPU support..."].isEnabled()
    assert dialog.install_button.isEnabled()
    dialog.cancel_button.click()
    assert not dialog.isVisible()


def test_success_and_menu_presence(make_window, monkeypatch, isolated_pack):
    window = make_window()
    dialog, script, actions = _open(window, monkeypatch)
    dialog.install_button.click()
    (isolated_pack / gpu_pack.STAMP).mkdir(parents=True)
    script.report(4, 4, "last.whl")
    script.finish(_result(True, "GPU support is installed. Restart Clearwater to use it."))
    assert dialog.status.text() == "GPU support is installed. Restart Clearwater to use it."
    assert dialog.progress_bar.value() == 1000
    assert not dialog.install_button.isEnabled()
    assert dialog.cancel_button.text() == "Close"
    assert actions["Install GPU support..."].isEnabled()
    assert actions["Remove GPU support"].isEnabled()


def test_close_while_running_requests_cancel(make_window, monkeypatch):
    window = make_window()
    dialog, script, _ = _open(window, monkeypatch)
    dialog.install_button.click()
    dialog.close()
    assert script.calls[0][3].progress.cancelled()
    assert dialog.isVisible()
    script.finish(_result(False, "cancelled"))
    dialog.close()


def test_remove_confirms_then_uses_runner(make_window, monkeypatch, isolated_pack):
    (isolated_pack / gpu_pack.STAMP).mkdir(parents=True)
    window = make_window()
    script = ScriptedRunner()
    monkeypatch.setattr(window.jobs, "run", script.run)
    tools, actions = _actions(window)
    actions["Remove GPU support"].trigger()
    prompt = window._gpu_remove_prompt
    assert prompt.isVisible() and "next start" in prompt.text()
    assert script.calls == []
    prompt.button(QMessageBox.StandardButton.No).click()
    assert script.calls == []
    actions["Remove GPU support"].trigger()
    window._gpu_remove_prompt.button(QMessageBox.StandardButton.Yes).click()
    assert len(script.calls) == 1
    assert not actions["Install GPU support..."].isEnabled()
    assert not actions["Remove GPU support"].isEnabled()
    (isolated_pack / gpu_pack.STAMP).rmdir()
    script.finish(_result(True, "GPU support is removed; takes effect at the next start"))
    assert "next start" in window.statusBar().currentMessage()
    assert actions["Install GPU support..."].isEnabled()
    assert not actions["Remove GPU support"].isEnabled()
    # Refresh also sees a pack created outside this window.
    (isolated_pack / gpu_pack.STAMP).mkdir()
    tools.aboutToShow.emit()
    assert actions["Remove GPU support"].isEnabled()


def test_remove_failure_is_readable(make_window, monkeypatch, isolated_pack):
    (isolated_pack / gpu_pack.STAMP).mkdir(parents=True)
    window = make_window()
    script = ScriptedRunner()
    monkeypatch.setattr(window.jobs, "run", script.run)
    _, actions = _actions(window)
    actions["Remove GPU support"].trigger()
    window._gpu_remove_prompt.button(QMessageBox.StandardButton.Yes).click()
    script.finish(_result(False, "folder is locked"))
    assert presenter_of(window).of("error")[-1].text == "folder is locked"
    assert actions["Remove GPU support"].isEnabled()


@pytest.mark.parametrize("supported", [False, True])
def test_platform_visibility_and_idle_hint(make_window, monkeypatch, isolated_pack, supported):
    if not supported:
        monkeypatch.setattr(gpu_pack, "pack_root", lambda: None)
    window = make_window()
    _, actions = _actions(window)
    for name in ("Install GPU support...", "Remove GPU support"):
        assert actions[name].isVisible() == supported
    assert not actions["Remove GPU support"].isEnabled()
    window.set_idle_device("CPU: CuPy not installed (test)")
    assert ("Tools > Install GPU support..." in window.device_label.toolTip()) == supported
    window.set_idle_device("CPU: another reason")
    assert window.device_label.toolTip() == ""


def test_real_runner_adapter_is_qt_free_on_worker(make_window, monkeypatch, qtbot, isolated_pack):
    window = make_window()
    threads = []

    def install(progress):
        threads.append(threading.current_thread())
        progress.report(10, 10, "synthetic.whl")
        return gpu_pack_install.PackResult(
            True, "GPU support is installed. Restart Clearwater to use it."
        )

    monkeypatch.setattr(gpu_pack_install, "install", install)
    _, actions = _actions(window)
    actions["Install GPU support..."].trigger()
    dialog = window._gpu_pack_dialog
    dialog.install_button.click()
    qtbot.waitUntil(
        lambda: dialog.status.text().startswith("GPU support is installed"), timeout=3000
    )
    assert len(threads) == 1 and threads[0] is not threading.current_thread()
    assert dialog.current_wheel.text() == "synthetic.whl"
    assert dialog.progress_bar.value() == 1000


def test_gui_paths_have_no_blocking_dialog_exec():
    root = Path(__file__).parents[1] / "src/clearwater/gui"
    for name in ("gpu_pack_dialog.py", "shell.py"):
        # shell.run's QApplication.exec is the application's existing event loop.
        text = (root / name).read_text()
        assert ".exec(" not in text.replace("app.exec(", "application_event_loop(")


def test_rejected_pack_plan_warns_before_request(make_window, monkeypatch, isolated_pack):
    (isolated_pack / gpu_pack.STAMP).mkdir(parents=True)
    dialog, script, _ = _open(make_window(), monkeypatch)
    assert (
        "An existing GPU pack is not usable and will be replaced" in dialog.plan_text.toPlainText()
    )
    assert script.calls == []


def test_operation_in_progress_is_shown_by_dialog(make_window, monkeypatch):
    dialog, script, _ = _open(make_window(), monkeypatch)
    dialog.install_button.click()
    script.finish(_result(False, "another GPU pack operation is in progress"))
    assert dialog.status.text() == "another GPU pack operation is in progress"
    assert dialog.install_button.isEnabled()


@pytest.mark.parametrize("source_open", [False, True])
def test_deferred_remove_updates_cpu_reason(
    make_window, monkeypatch, isolated_pack, qtbot, source_open
):
    (isolated_pack / gpu_pack.STAMP).mkdir(parents=True)
    path = Path("synthetic.png")
    window = make_window(photo_engines({path: image(20, 30)}))
    if source_open:
        open_and_wait(qtbot, window, path)
    window.set_idle_device("GPU")
    script = ScriptedRunner()
    monkeypatch.setattr(window.jobs, "run", script.run)
    _, actions = _actions(window)
    actions["Remove GPU support"].trigger()
    window._gpu_remove_prompt.button(QMessageBox.StandardButton.Yes).click()
    (isolated_pack / (gpu_pack.STAMP + ".remove")).touch()
    script.finish(_result(True, "GPU support will be removed at the next start"))
    assert window.statusBar().currentMessage() == "GPU support will be removed at the next start"
    assert window.device_label.text() == "Device: CPU: GPU pack removal pending"


def test_startup_marker_shows_pending_reason_without_install_hint(make_window, isolated_pack):
    isolated_pack.mkdir()
    (isolated_pack / (gpu_pack.STAMP + ".remove")).touch()
    window = make_window()
    assert window.device_label.text() == "Device: CPU: GPU pack removal pending"
    assert window.device_label.toolTip() == ""
    # The asynchronous startup probe's ordinary missing-CuPy reason cannot hide the marker.
    window.set_idle_device("CPU: CuPy not installed")
    assert window.device_label.text() == "Device: CPU: GPU pack removal pending"
    assert window.device_label.toolTip() == ""


@pytest.mark.parametrize("completion", ["install", "remove"])
def test_pending_reason_clears_after_marker_is_gone(
    make_window, monkeypatch, isolated_pack, completion
):
    (isolated_pack / gpu_pack.STAMP).mkdir(parents=True)
    marker = isolated_pack / (gpu_pack.STAMP + ".remove")
    marker.touch()
    window = make_window()
    assert window.device_label.text() == "Device: CPU: GPU pack removal pending"
    if completion == "install":
        dialog, script, _ = _open(window, monkeypatch)
        dialog.install_button.click()
        marker.unlink()
        script.finish(_result(True, "GPU support is installed. Restart Clearwater to use it."))
        assert dialog.status.text() == "GPU support is installed. Restart Clearwater to use it."
    else:
        script = ScriptedRunner()
        monkeypatch.setattr(window.jobs, "run", script.run)
        _, actions = _actions(window)
        actions["Remove GPU support"].trigger()
        window._gpu_remove_prompt.button(QMessageBox.StandardButton.Yes).click()
        marker.unlink()
        (isolated_pack / gpu_pack.STAMP).rmdir()
        script.finish(_result(True, "GPU support is removed; takes effect at the next start"))
    assert "removal pending" not in window.device_label.text()
    window.set_idle_device("CPU: CuPy not installed")
    assert window.device_label.text() == "Device: CPU: CuPy not installed"
    assert window.device_label.toolTip() == "Tools > Install GPU support..."


def test_marker_vanishing_during_construction_resets_without_a_status_bar(
    make_window, monkeypatch, isolated_pack
):
    isolated_pack.mkdir()
    present = isolated_pack / (gpu_pack.STAMP + ".remove")
    present.touch()
    missing = isolated_pack / "already-removed"
    calls = 0

    def changing_marker():
        nonlocal calls
        calls += 1
        return present if calls == 1 else missing

    monkeypatch.setattr(gpu_pack, "pending_removal_path", changing_marker)
    window = make_window()
    assert calls >= 2
    assert window.device_label.text() == (
        "Device: CPU: GPU support changes take effect at the next start"
    )
    assert window.device_label.toolTip() == ""
    window.set_idle_device("CPU: CuPy not installed")
    assert window.device_label.text() == "Device: CPU: CuPy not installed"


@pytest.mark.parametrize("stage", ["construction", "menu"])
def test_unreadable_marker_keeps_pending_cpu_reason(make_window, monkeypatch, caplog, stage):
    window = make_window() if stage == "menu" else None

    def denied():
        raise PermissionError("synthetic marker probe denied")

    monkeypatch.setattr(gpu_pack, "pending_removal_path", denied)
    if window is None:
        window = make_window()
    else:
        window._update_gpu_actions()
    assert window.device_label.text() == "Device: CPU: GPU pack removal pending"
    assert window.device_label.toolTip() == ""
    assert len([r for r in caplog.records if "GPU pack removal pending" in r.message]) == 1


def test_this_process_loaded_remove_only_writes_marker(make_window, monkeypatch, isolated_pack):
    folder = isolated_pack / gpu_pack.STAMP
    folder.mkdir(parents=True)
    (folder / "keep").write_bytes(b"intact")
    monkeypatch.setattr(
        gpu_pack, "activation_status", lambda: gpu_pack.PackStatus(gpu_pack.STAMP, "loaded")
    )
    monkeypatch.setattr(
        gpu_pack_install, "_pack_in_use", lambda _: pytest.fail("this-process probe"), raising=False
    )
    window = make_window()
    original_replace = os.replace

    def checked_replace(source, target):
        if Path(source) == folder:
            pytest.fail("loaded pack renamed")
        return original_replace(source, target)

    monkeypatch.setattr(os, "replace", checked_replace)
    script = ScriptedRunner()
    monkeypatch.setattr(window.jobs, "run", script.run)
    _, actions = _actions(window)
    actions["Remove GPU support"].trigger()
    window._gpu_remove_prompt.button(QMessageBox.StandardButton.Yes).click()
    job, _, _, handle = script.calls[-1]
    script.finish(job(handle.progress))
    assert (isolated_pack / (gpu_pack.STAMP + ".remove")).read_bytes() == b""
    assert (folder / "keep").read_bytes() == b"intact"
    assert not list(isolated_pack.glob("*.partial-*"))
    assert window.statusBar().currentMessage() == "GPU support will be removed at the next start"


@pytest.mark.parametrize("outcome", [None, "absent", "rejected"])
def test_without_loaded_status_gui_uses_normal_remove(
    make_window, monkeypatch, isolated_pack, outcome
):
    (isolated_pack / gpu_pack.STAMP).mkdir(parents=True)
    activation = None if outcome is None else gpu_pack.PackStatus(gpu_pack.STAMP, outcome)
    monkeypatch.setattr(gpu_pack, "activation_status", lambda: activation)
    monkeypatch.setattr(
        gpu_pack_install, "remove", lambda: gpu_pack_install.PackResult(True, "normal removal")
    )
    window = make_window()
    script = ScriptedRunner()
    monkeypatch.setattr(window.jobs, "run", script.run)
    _, actions = _actions(window)
    actions["Remove GPU support"].trigger()
    window._gpu_remove_prompt.button(QMessageBox.StandardButton.Yes).click()
    job, _, _, handle = script.calls[-1]
    script.finish(job(handle.progress))
    assert window.statusBar().currentMessage() == "normal removal"
    assert not (isolated_pack / (gpu_pack.STAMP + ".remove")).exists()
