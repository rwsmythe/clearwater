"""The frozen-build entry: the worker re-entry and the bundled-tool PATH (WP6.1, AD-34, D1).

Parallel leg, synthetic: ``sys.frozen`` and ``sys.executable`` are monkeypatched, the export
worker's ``main``, the GPU pack loader, the log set-up and the GUI's ``main`` are stubbed, so no
window opens and no real app-data folder is touched. One check runs in a fresh interpreter
(``python -I -c``), because only a fresh import graph shows what the worker branch imports. The
frozen build itself is checked by hand (the WP6.1 report).
"""

from __future__ import annotations

import importlib
import importlib.abc
import logging
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path
from types import ModuleType
from typing import Any

import pytest

from clearwater import gpu_pack
from clearwater.app import composition, export_worker
from clearwater.config import log as config_log
from clearwater.config import paths as config_paths
from clearwater.jobs.export_process import ProcessExportJobs
from clearwater.jobs.export_seam import unavailable_exports

BLOCKED = ("PySide6", "shiboken6", "clearwater.gui", "clearwater.app.main")
"""Modules the worker branch must never import (AD-31: the worker is Qt-free)."""


class _Blocker(importlib.abc.MetaPathFinder):
    """Refuse, and record, every import of a :data:`BLOCKED` module."""

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def find_spec(self, name: str, path: Any, target: Any = None) -> None:
        if any(name == b or name.startswith(b + ".") for b in BLOCKED):
            self.attempts.append(name)
            raise ImportError(f"blocked by the test: {name}")
        return None


def _fresh_entry(monkeypatch: pytest.MonkeyPatch) -> tuple[ModuleType, _Blocker]:
    """Import ``clearwater.__main__`` afresh with every :data:`BLOCKED` module unimportable.

    The blocked modules are taken out of ``sys.modules`` for the test (restored after it), so
    an import of one, at the entry's top level or on a branch, reaches the blocker.
    """
    for name in list(sys.modules):
        if name == "clearwater.__main__" or any(
            name == b or name.startswith(b + ".") for b in BLOCKED
        ):
            monkeypatch.delitem(sys.modules, name)
    blocker = _Blocker()
    monkeypatch.setattr(sys, "meta_path", [blocker, *sys.meta_path])
    entry = importlib.import_module("clearwater.__main__")
    return entry, blocker


@pytest.fixture
def calls(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> list[tuple[str, Any]]:
    """Stub every effect the entry has, recording the calls in order.

    Returns:
        The (what, argument) calls, in order.
    """
    seen: list[tuple[str, Any]] = []

    def activate() -> None:
        seen.append(("activate", None))

    def worker_main(argv: Sequence[str] | None = None) -> int:
        seen.append(("worker", argv))
        return 7

    def configure(folder: Path, **_: Any) -> Path:
        seen.append(("log", folder))
        return folder / "clearwater.log"

    def locations(**_: Any) -> config_paths.Locations:
        return config_paths.Locations(config_dir=tmp_path / "cfg", cache_dir=tmp_path / "cache")

    monkeypatch.setattr(gpu_pack, "activate", activate)
    monkeypatch.setattr(export_worker, "main", worker_main)
    monkeypatch.setattr(config_log, "configure_logging", configure)
    monkeypatch.setattr(config_paths, "app_locations", locations)
    return seen


def _fake_gui(monkeypatch: pytest.MonkeyPatch, seen: list[tuple[str, Any]]) -> None:
    """Put a stand-in ``clearwater.app.main`` in ``sys.modules`` (no Qt is imported)."""
    fake = ModuleType("clearwater.app.main")

    def gui_main(argv: Sequence[str] | None = None) -> int:
        seen.append(("gui", argv))
        return 3

    fake.main = gui_main  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "clearwater.app.main", fake)


# Q5 (a): the worker command.


def _frozen(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> str:
    """Make this process look like the frozen ``Clearwater.exe`` in ``tmp_path/dist``."""
    executable = str(tmp_path / "dist" / "Clearwater.exe")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", executable)
    return executable


def _worker_command(tmp_path: Path, command: Sequence[str] | None = None) -> tuple[str, ...]:
    """Return the worker command line ``process_export_jobs`` builds."""
    built = composition.process_export_jobs(
        photo_exports=unavailable_exports(), cache_dir=tmp_path, command=command
    )
    assert isinstance(built, ProcessExportJobs)
    return built._command


def test_a_frozen_build_re_enters_its_executable_as_the_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Frozen: ``[sys.executable, "--export-worker"]`` (no ``-m``, which the exe ignores)."""
    executable = _frozen(monkeypatch, tmp_path)
    assert _worker_command(tmp_path) == (executable, "--export-worker")


def test_a_source_run_spawns_the_worker_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not frozen: the unchanged ``python -m clearwater.app.export_worker``."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    assert _worker_command(tmp_path) == (sys.executable, "-m", "clearwater.app.export_worker")


def test_an_injected_command_wins_when_frozen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tests' own worker commands are kept as given, frozen or not."""
    _frozen(monkeypatch, tmp_path)
    fake = ("python", "-c", "pass")
    assert _worker_command(tmp_path, fake) == fake


# Q5 (b): the entry's dispatch.


def test_the_worker_flag_runs_the_worker_without_qt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """``--export-worker a b``: loader, then the worker with ``[a, b]``; no Qt, no log file."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    entry, blocker = _fresh_entry(monkeypatch)
    status = entry.main(["Clearwater.exe", "--export-worker", "a", "b"])
    assert status == 7
    assert calls == [("activate", None), ("worker", ["a", "b"])]
    assert blocker.attempts == []
    assert not [m for m in sys.modules if m.startswith(BLOCKED)]


def test_the_worker_flag_alone_passes_no_arguments(
    monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """The real spawn (``[exe, "--export-worker"]``): the worker gets ``[]``, not its flag."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    entry, _ = _fresh_entry(monkeypatch)
    monkeypatch.setattr(sys, "argv", ["Clearwater.exe", "--export-worker"])
    assert entry.main() == 7
    assert calls[-1] == ("worker", [])


@pytest.mark.parametrize(
    "argv",
    [["Clearwater.exe"], ["Clearwater.exe", "photo.heic"], ["x", "a", "--export-worker"]],
)
def test_anything_else_starts_the_gui_after_logging_and_the_loader(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[str, Any]],
    argv: list[str],
) -> None:
    """Frozen GUI branch: the log file first (D3), then the loader, then the GUI with the argv."""
    _frozen(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))  # restored after the D1 prepend
    _fake_gui(monkeypatch, calls)
    import clearwater.__main__ as entry

    assert entry.main(argv) == 3
    assert calls == [("log", tmp_path / "cfg" / "logs"), ("activate", None), ("gui", argv)]


def test_a_source_run_starts_the_gui_as_1_0_0_did(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reviewer A r2 #6: not frozen, no log folder exists before the GUI starts (1.0.0).

    The real ``app_locations`` and ``configure_logging`` run, with the app-data folders
    redirected under ``tmp_path``; only the GUI is a stand-in, which looks for the log folder.
    """
    monkeypatch.delattr(sys, "frozen", raising=False)
    for variable in ("APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(variable, str(tmp_path / variable.lower()))
    log_dir = config_paths.app_locations().log_dir
    assert log_dir.is_relative_to(tmp_path)
    seen: list[tuple[str, Any]] = []
    _fake_gui(monkeypatch, seen)
    logger = logging.getLogger(config_log.LOGGER_NAME)
    handlers = list(logger.handlers)
    import clearwater.__main__ as entry

    try:
        assert entry.main(["python -m clearwater"]) == 3
        assert seen == [("gui", ["python -m clearwater"])]
        assert not log_dir.exists()
        assert logger.handlers == handlers
    finally:
        for handler in [h for h in logger.handlers if h not in handlers]:
            logger.removeHandler(handler)
            handler.close()


def test_a_log_folder_failure_does_not_stop_the_gui(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """Frozen: the shell reports a log failure itself; the entry carries on to loader and GUI."""
    _frozen(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
    _fake_gui(monkeypatch, calls)

    def refuse(folder: Path, **_: Any) -> Path:
        raise PermissionError("no")

    monkeypatch.setattr(config_log, "configure_logging", refuse)
    import clearwater.__main__ as entry

    assert entry.main(["Clearwater.exe"]) == 3
    assert [what for what, _ in calls] == ["activate", "gui"]


# D1: the executable's folder first on PATH when frozen.


def test_frozen_puts_the_executable_folder_first_on_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Frozen: ``dirname(sys.executable)`` + ``os.pathsep`` + the old PATH, once."""
    executable = _frozen(monkeypatch, tmp_path)
    folder = os.path.dirname(executable)
    import clearwater.__main__ as entry

    environ = {"PATH": os.pathsep.join(["/a", "/b"])}
    assert entry.prepend_executable_folder(environ) is True
    assert environ["PATH"] == os.pathsep.join([folder, "/a", "/b"])
    assert entry.prepend_executable_folder(environ) is False  # a spawned worker: not twice
    assert environ["PATH"] == os.pathsep.join([folder, "/a", "/b"])
    empty: dict[str, str] = {}
    assert entry.prepend_executable_folder(empty) is True
    assert empty == {"PATH": folder}


def test_a_worker_whose_path_was_changed_by_pyside6_does_not_add_the_folder_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reviewer A r2 #10: membership, not position, decides (no duplicate entry).

    The parent prepends the folder; the frozen child inherits that ``PATH``, and before its
    entry runs, PyInstaller's PySide6 run-time hook prepends the bundle folder and PySide6's
    start-up its package folder. The child's entry must then leave ``PATH`` as it is.
    """
    executable = _frozen(monkeypatch, tmp_path)
    folder = os.path.dirname(executable)
    import clearwater.__main__ as entry

    environ = {"PATH": os.pathsep.join(["/a", "/b"])}
    assert entry.prepend_executable_folder(environ) is True  # the GUI process
    bundle = os.path.join(folder, "_internal")
    pyside = os.path.join(bundle, "PySide6")
    environ["PATH"] = pyside + os.pathsep + bundle + os.pathsep + environ["PATH"]
    inherited = environ["PATH"]
    assert entry.prepend_executable_folder(environ) is False  # the worker process
    assert environ["PATH"] == inherited
    assert environ["PATH"].split(os.pathsep).count(folder) == 1
    trailing = {"PATH": os.pathsep.join(["/a", folder + os.sep])}
    assert entry.prepend_executable_folder(trailing) is False  # the same folder, spelt with /


def test_a_source_run_leaves_path_alone(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Not frozen: PATH is not touched."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    import clearwater.__main__ as entry

    environ = {"PATH": "/a"}
    assert entry.prepend_executable_folder(environ) is False
    assert environ == {"PATH": "/a"}


def test_the_entry_sets_path_before_either_branch(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """Frozen ``main()``: ``os.environ["PATH"]`` starts with the executable's folder."""
    executable = _frozen(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", os.pathsep.join(["/x", "/y"]))
    entry, _ = _fresh_entry(monkeypatch)
    entry.main([executable, "--export-worker"])
    first = os.environ["PATH"].split(os.pathsep)[0]
    assert first == os.path.dirname(executable)


# Reviewer A r2 #11: the worker branch's import graph, in a fresh interpreter.

_WORKER_IMPORT_PROBE = """
import sys
sys.path.insert(0, sys.argv[1])
import clearwater.__main__ as entry
from clearwater.app import export_worker
export_worker.main = lambda argv=None: 0
status = entry.main(["Clearwater.exe", "--export-worker"])
loaded = sorted(m for m in sys.modules if m.startswith(tuple(sys.argv[2:])))
print("status", status, "loaded", ",".join(loaded) or "-")
"""
"""Import the entry and the worker afresh, run the worker branch (its ``main`` stubbed), and
print which :data:`BLOCKED` modules are then loaded."""


def _probe_worker_imports(src_root: Path) -> str:
    """Run :data:`_WORKER_IMPORT_PROBE` on the ``clearwater`` under ``src_root``.

    Args:
        src_root: The folder holding the ``clearwater`` package to import.

    Returns:
        The probe's output line.
    """
    done = subprocess.run(
        [sys.executable, "-I", "-c", _WORKER_IMPORT_PROBE, str(src_root), *BLOCKED],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def test_the_worker_branch_imports_no_qt_in_a_fresh_interpreter() -> None:
    """The real import graph of ``__main__`` and ``export_worker``: no PySide6, no shiboken6."""
    import clearwater

    src_root = Path(clearwater.__file__).resolve().parents[1]
    assert _probe_worker_imports(src_root) == "status 0 loaded -"


def test_the_fresh_interpreter_probe_sees_a_top_level_qt_import(tmp_path: Path) -> None:
    """The probe distinguishes: a copy whose ``export_worker`` imports PySide6 is caught."""
    import clearwater

    package = Path(clearwater.__file__).resolve().parent
    copy = tmp_path / "src" / "clearwater"
    shutil.copytree(package, copy, ignore=shutil.ignore_patterns("__pycache__"))
    worker = copy / "app" / "export_worker.py"
    worker.write_text(
        worker.read_text(encoding="utf-8") + "\nimport PySide6  # the test's mutation\n",
        encoding="utf-8",
    )
    line = _probe_worker_imports(tmp_path / "src")
    assert line.startswith("status 0 loaded PySide6")
    assert "shiboken6" in line
