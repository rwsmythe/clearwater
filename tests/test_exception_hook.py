"""Fatal exception reporting, with disposable profiles and no desktop windows.

Children block Qt and have bounded lifetimes. GUI checks use offscreen Qt, replace
the message presenter and process queued events without entering an event loop.
"""

from __future__ import annotations

import importlib
import io
import logging
import os
import subprocess
import sys
import threading
import time

import pytest

from clearwater.config import log as config_log
from clearwater.config.paths import app_locations

pytestmark = pytest.mark.timeout(20)

_ROOTS = (
    "APPDATA",
    "LOCALAPPDATA",
    "XDG_CONFIG_HOME",
    "XDG_CACHE_HOME",
    "XDG_DATA_HOME",
    "XDG_STATE_HOME",
    "HOME",
    "USERPROFILE",
)


@pytest.fixture(autouse=True)
def isolated(monkeypatch, tmp_path):
    """Keep every report under this test's profile and restore both interpreter hooks."""
    for variable in _ROOTS:
        monkeypatch.setenv(variable, str(tmp_path / variable.lower()))
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setattr(sys, "excepthook", sys.__excepthook__)
    monkeypatch.setattr(threading, "excepthook", threading.__excepthook__)
    config_log.shutdown_logging()
    yield
    config_log.shutdown_logging()


def _failure():
    """Return an exception with a real traceback, including non-ASCII/newline text."""
    try:
        raise RuntimeError("planted caf\u00e9\nsecond line")
    except RuntimeError:
        return sys.exc_info()


def _reporter(monkeypatch):
    """Install the real reporter, replacing only the process-exit boundary."""
    entry = importlib.import_module("clearwater.__main__")
    exits = []
    monkeypatch.setattr(os, "_exit", exits.append)
    assert hasattr(entry, "install_exception_hooks"), "fatal reporter is missing"
    reporter = entry.install_exception_hooks()
    return entry, reporter, exits


def test_startup_report_writes_traceback_flushes_and_exits_once(monkeypatch):
    """Missing early logging, multiline stderr or a returning process is a regression."""
    entry, reporter, exits = _reporter(monkeypatch)
    stderr = io.StringIO()
    monkeypatch.setattr(sys, "stderr", stderr)
    assert entry.install_exception_hooks() is reporter
    assert sys.excepthook is reporter
    sys.excepthook(*_failure())
    text = app_locations().log_file.read_text(encoding="utf-8")
    assert text.count("Traceback (most recent call last)") == 1
    assert "raise RuntimeError" in text
    assert "RuntimeError: planted caf\u00e9\nsecond line" in text
    line = stderr.getvalue()
    assert len(line.splitlines()) == 1
    assert line.isascii()
    assert str(app_locations().log_file) in line
    assert exits == [1]


@pytest.mark.parametrize("broken", [False, True])
def test_absent_or_broken_stderr_still_logs_and_terminates(monkeypatch, broken):
    """A windowed executable has no stderr; a closed pipe must not lose the log."""
    _, reporter, exits = _reporter(monkeypatch)

    class Broken:
        def write(self, _text):
            raise OSError("closed pipe")

        def flush(self):
            raise OSError("closed pipe")

    monkeypatch.setattr(sys, "stderr", Broken() if broken else None)
    reporter(*_failure())
    assert "RuntimeError: planted" in app_locations().log_file.read_text(encoding="utf-8")
    assert exits == [1]


def test_unopenable_log_names_intended_path_without_fallback(monkeypatch, capsys):
    """An unavailable log must be disclosed without writing another location."""
    _, reporter, exits = _reporter(monkeypatch)
    path = app_locations().log_file
    path.parent.parent.mkdir(parents=True)
    path.parent.write_text("not a directory", encoding="utf-8")
    reporter(*_failure())
    stderr = capsys.readouterr().err
    assert stderr.count("\n") == 1
    assert "log unavailable" in stderr
    assert str(path) in stderr
    assert not path.exists()
    assert exits == [1]


def test_recursive_reporting_does_not_duplicate_or_recurse(monkeypatch):
    """A failing output sink that re-enters the hook must still terminate once."""
    _, reporter, exits = _reporter(monkeypatch)
    writes = []

    class Recursive:
        def write(self, text):
            writes.append(text)
            reporter(*_failure())
            raise RuntimeError("broken output")

        def flush(self):
            raise RuntimeError("broken flush")

    monkeypatch.setattr(sys, "stderr", Recursive())
    reporter(*_failure())
    assert len(writes) == 1
    assert exits == [1]
    assert app_locations().log_file.read_text(encoding="utf-8").count("Traceback (") == 1


def test_thread_hook_logs_and_terminates_the_process(monkeypatch, capsys):
    """Raising SystemExit in a failed thread would leave the process alive."""
    _, reporter, exits = _reporter(monkeypatch)
    args = threading.ExceptHookArgs((*_failure(), threading.current_thread()))
    threading.excepthook(args)
    assert capsys.readouterr().err.count("\n") == 1
    assert "RuntimeError: planted" in app_locations().log_file.read_text(encoding="utf-8")
    assert exits == [1]
    assert sys.excepthook is reporter


def test_explicit_system_exit_is_not_reported(monkeypatch, capsys):
    """Explicit status codes are not fatal exception notifications."""
    _, reporter, exits = _reporter(monkeypatch)
    reporter(SystemExit, SystemExit(7), None)
    assert exits == []
    assert not app_locations().log_file.exists()
    assert capsys.readouterr().err == ""


def test_a_reimport_reuses_the_active_reporter(monkeypatch):
    """Script/canonical module identities must not replace the reporter or Qt callback."""
    entry, reporter, _ = _reporter(monkeypatch)
    reloaded = importlib.reload(entry)
    assert reloaded.install_exception_hooks() is reporter


def test_fatal_record_keeps_the_existing_log_rotation(monkeypatch, capsys):
    """A crash must not bypass D88's rotation or propagate a second stderr traceback."""
    _, reporter, exits = _reporter(monkeypatch)
    path = app_locations().log_file
    config_log.configure_logging(path.parent, max_bytes=64)
    logging.getLogger("clearwater").info("previous log record")
    reporter(*_failure())
    assert "previous log record" in path.with_name("clearwater.log.1").read_text(encoding="utf-8")
    assert "RuntimeError: planted" in path.read_text(encoding="utf-8")
    assert capsys.readouterr().err.count("\n") == 1
    assert exits == [1]


@pytest.mark.parametrize("threaded", [False, True])
def test_post_qt_failure_presents_once_on_qt_thread_before_exit(monkeypatch, threaded):
    """The GUI enables its plain log-path box before build_application can fail."""
    from PySide6.QtCore import QThread
    from PySide6.QtWidgets import QApplication

    _, reporter, exits = _reporter(monkeypatch)
    gui = importlib.import_module("clearwater.app.main")
    app = QApplication.instance() or QApplication([])
    presented = []

    def present(text):
        assert QThread.currentThread() == app.thread()
        assert exits == []
        presented.append(text)

    monkeypatch.setattr(gui, "_present_exception", present, raising=False)

    def fail(_locations):
        raise RuntimeError("post-Qt planted failure")

    monkeypatch.setattr(gui, "build_application", fail)
    with pytest.raises(RuntimeError, match="post-Qt planted"):
        gui.main(["clearwater"])
    info = _failure()
    if threaded:
        thread = threading.Thread(
            target=lambda: threading.excepthook(threading.ExceptHookArgs((*info, None)))
        )
        thread.start()
        deadline = time.monotonic() + 5
        while thread.is_alive() and time.monotonic() < deadline:
            app.processEvents()
            thread.join(0.01)
        thread.join(0.1)
        assert not thread.is_alive()
    else:
        reporter(*info)
    reporter(*info)  # a second callback must not open another box
    assert len(presented) == 1
    assert str(app_locations().log_file) in presented[0]
    assert "Traceback" not in presented[0]
    assert "RuntimeError" not in presented[0]
    assert exits == [1]


_CHILD_PREFIX = r"""
import importlib.abc
import sys
import threading
import runpy

class BlockQt(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in ('PySide6', 'shiboken6') or name == 'clearwater.app.main':
            raise ImportError('GUI blocked by fatal-hook test')
        return None

sys.meta_path.insert(0, BlockQt())
"""


def _child(tmp_path, body):
    """Run isolated source code with Qt blocked and a hard process timeout."""
    script = tmp_path / "probe.py"
    script.write_text(_CHILD_PREFIX + body, encoding="utf-8")
    return subprocess.run(
        [sys.executable, str(script)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=12,
        check=False,
        env=dict(os.environ),
    )


@pytest.mark.parametrize("branch", ["startup", "worker", "thread"])
def test_uncaught_source_failures_exit_without_qt_and_report_once(tmp_path, branch):
    """Exercise real top-level/thread hooks, including the source worker's own entry."""
    bodies = {
        "startup": r"""
class BreakPack(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name == 'clearwater.gpu_pack':
            raise RuntimeError('planted startup failure')
        return None
sys.meta_path.insert(0, BreakPack())
runpy.run_module('clearwater', run_name='__main__')
""",
        "worker": r"""
def planted(frame, event, arg):
    if (event == 'call' and frame.f_code.co_name == 'main'
            and frame.f_globals.get('__name__') == '__main__'):
        sys.settrace(None)
        raise RuntimeError('planted worker failure')
    return planted
sys.settrace(planted)
sys.argv[:] = ['clearwater.app.export_worker']
runpy.run_module('clearwater.app.export_worker', run_name='__main__')
""",
        "thread": r"""
from clearwater.__main__ import install_exception_hooks
install_exception_hooks()
def fail():
    raise RuntimeError('planted thread failure')
threading.Thread(target=fail).start()
threading.Event().wait(60)  # only a process-wide exit can complete within the bound
""",
    }
    done = _child(tmp_path, bodies[branch])
    assert done.returncode != 0
    assert done.stdout == ""
    assert done.stderr.count("\n") == 1, done.stderr
    assert done.stderr.isascii()
    assert str(app_locations().log_file) in done.stderr
    text = app_locations().log_file.read_text(encoding="utf-8")
    assert text.count("Traceback (most recent call last)") == 1
    assert f"RuntimeError: planted {branch} failure" in text
    assert "GUI blocked" not in text
