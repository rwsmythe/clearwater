"""The frozen-build entry: the worker re-entry and the bundled-tool PATH (WP6.1, AD-34, D1).

Parallel leg, synthetic, in this process: ``sys.frozen`` and ``sys.executable`` are
monkeypatched, the export worker's ``main``, the GPU pack loader, the log set-up and the GUI's
``main`` are stubbed, so nothing is spawned, no window opens and no real app-data folder is
touched. The frozen build itself is checked by hand (the WP6.1 report).
"""

from __future__ import annotations

import importlib
import importlib.abc
import os
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


def test_a_frozen_build_re_enters_its_executable_as_the_worker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Frozen: ``[sys.executable, "--export-worker"]`` (no ``-m``, which the exe ignores)."""
    executable = _frozen(monkeypatch, tmp_path)
    built = composition.process_export_jobs(photo_exports=object(), cache_dir=tmp_path)
    assert built._command == (executable, "--export-worker")


def test_a_source_run_spawns_the_worker_module(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Not frozen: the unchanged ``python -m clearwater.app.export_worker``."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    built = composition.process_export_jobs(photo_exports=object(), cache_dir=tmp_path)
    assert built._command == (sys.executable, "-m", "clearwater.app.export_worker")


def test_an_injected_command_wins_when_frozen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Tests' own worker commands are kept as given, frozen or not."""
    _frozen(monkeypatch, tmp_path)
    fake = ("python", "-c", "pass")
    built = composition.process_export_jobs(
        photo_exports=object(), cache_dir=tmp_path, command=fake
    )
    assert built._command == fake


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
    """GUI branch: the log file first (D3), then the loader, then the GUI with the argv."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    _fake_gui(monkeypatch, calls)
    import clearwater.__main__ as entry

    assert entry.main(argv) == 3
    assert calls == [("log", tmp_path / "cfg" / "logs"), ("activate", None), ("gui", argv)]


def test_a_log_folder_failure_does_not_stop_the_gui(
    monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """The shell reports a log failure itself; the entry carries on to the loader and GUI."""
    monkeypatch.delattr(sys, "frozen", raising=False)
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
