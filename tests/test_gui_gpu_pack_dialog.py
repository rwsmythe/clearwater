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
from gui_support import make_window, presenter_of

pytestmark = [pytest.mark.gui, pytest.mark.timeout(10)]

LICENSE = (
    "GPU support downloads CuPy and NVIDIA's CUDA runtime libraries from PyPI into your user "
    "folder. The NVIDIA libraries are provided by NVIDIA under the NVIDIA Software License "
    "Agreement (the file `License.txt` inside each nvidia package after the install); CuPy is "
    "MIT. Clearwater does not redistribute them."
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
