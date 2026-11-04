"""The frozen-build entry: the worker re-entry and the bundled-tool PATH (WP6.1, AD-34, D1).

Parallel leg, synthetic: ``sys.frozen`` and ``sys.executable`` are monkeypatched, the export
worker's ``main``, the GPU pack loader, the log set-up and the GUI's ``main`` are stubbed, so no
window opens and no real app-data folder is touched. One check runs in a fresh interpreter
(``python -I -c``), because only a fresh import graph shows what the worker branch imports. The
frozen build itself is checked by hand (the WP6.1 report).
"""

from __future__ import annotations

import ast
import contextlib
import importlib
import importlib.abc
import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Iterator, Sequence
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

    for variable in ("APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(variable, str(tmp_path / variable.lower()))  # never the user's
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


def test_a_source_run_sends_the_worker_flag_to_the_gui_as_1_0_0_did(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """Reviewer A r3 #1: not frozen, ``--export-worker a b`` reaches ``app.main`` (1.0.0).

    The GUI is a stand-in (the real one is unimportable here) and the app data is under
    ``tmp_path`` (the ``calls`` fixture): the 1.0.0 behaviour, pinned without a window.
    """
    monkeypatch.delattr(sys, "frozen", raising=False)
    entry, blocker = _fresh_entry(monkeypatch)
    _fake_gui(monkeypatch, calls)
    argv = ["python -m clearwater", "--export-worker", "a", "b"]
    assert entry.main(argv) == 3
    assert calls == [("activate", None), ("gui", argv)]
    assert blocker.attempts == []


def _stub_shim(monkeypatch: pytest.MonkeyPatch, entry: ModuleType, seen: list[Any]) -> None:
    """Record the F-E shim's call instead of re-pointing THIS process's standard input."""
    monkeypatch.setattr(
        entry, "isolate_worker_stdin", lambda: seen.append(("shim", None)), raising=False
    )


def test_the_frozen_worker_flag_runs_the_shim_the_loader_then_the_worker_without_qt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """Frozen ``--export-worker a b``: the shim, the loader, the worker with ``[a, b]``; no Qt."""
    _frozen(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))  # restored after the D1 prepend
    entry, blocker = _fresh_entry(monkeypatch)
    _stub_shim(monkeypatch, entry, calls)
    status = entry.main(["Clearwater.exe", "--export-worker", "a", "b"])
    assert status == 7
    assert calls == [("shim", None), ("activate", None), ("worker", ["a", "b"])]
    assert blocker.attempts == []
    assert not [m for m in sys.modules if m.startswith(BLOCKED)]


def test_the_frozen_worker_flag_alone_passes_no_arguments(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """The real spawn (``[exe, "--export-worker"]``): the worker gets ``[]``, not its flag."""
    _frozen(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
    entry, _ = _fresh_entry(monkeypatch)
    _stub_shim(monkeypatch, entry, calls)
    monkeypatch.setattr(sys, "argv", ["Clearwater.exe", "--export-worker"])
    assert entry.main() == 7
    assert calls[-1] == ("worker", [])


# CHARC's ruling on Reviewer A r3 #3: a frozen multiprocessing re-entry is refused first.


@pytest.mark.parametrize(
    "argv",
    [
        ["X", "--multiprocessing-resource-tracker", "5"],
        ["X", "--export-worker", "--multiprocessing-fork", "parent_pid=1"],
        ["X", "-m", "cuda.pathfinder", "--multiprocessing-fork"],
        ["X", "-c", "pass", "--multiprocessing-fork"],
    ],
    ids=["resource-tracker", "after-the-worker-flag", "after-dash-m", "after-dash-c"],
)
def test_a_frozen_multiprocessing_re_entry_is_refused_before_every_branch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[str, Any]],
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
) -> None:
    """Any argument naming a multiprocessing child: status 2, one line; nothing else runs.

    Reviewer A r4 #5: not even the D1 ``PATH`` change (the executable's folder is NOT put
    first); every recorded effect is absent.
    """
    executable = _frozen(monkeypatch, tmp_path)
    path = os.pathsep.join(["/x", "/y"])
    monkeypatch.setenv("PATH", path)
    entry, blocker = _fresh_entry(monkeypatch)
    _fake_gui(monkeypatch, calls)
    _stub_shim(monkeypatch, entry, calls)
    assert entry.main([executable, *argv[1:]]) == 2
    assert capsys.readouterr().err == "Clearwater: multiprocessing children are not supported\n"
    assert calls == []  # no shim, no loader, no worker, no log file, no GUI
    assert os.environ["PATH"] == path  # no PATH processing either (A r4 #5)
    assert blocker.attempts == []


def test_the_real_multiprocessing_spawn_command_line_is_refused_when_frozen(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[str, Any]],
    capsys: pytest.CaptureFixture[str],
) -> None:
    """``multiprocessing.spawn.get_command_line()`` of a frozen process: refused, no GUI."""
    import multiprocessing.spawn

    executable = _frozen(monkeypatch, tmp_path)
    path = os.pathsep.join(["/x", "/y"])
    monkeypatch.setenv("PATH", path)
    command = multiprocessing.spawn.get_command_line(parent_pid=123, pipe_handle=456)
    assert command[:2] == [executable, "--multiprocessing-fork"]
    entry, blocker = _fresh_entry(monkeypatch)
    _fake_gui(monkeypatch, calls)
    _stub_shim(monkeypatch, entry, calls)
    assert entry.main(command) == 2
    assert capsys.readouterr().err == "Clearwater: multiprocessing children are not supported\n"
    assert calls == []
    assert os.environ["PATH"] == path
    assert blocker.attempts == []


def test_a_source_run_sends_a_multiprocessing_flag_to_the_gui_as_before(
    monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """Not frozen: no refusal branch (1.0.0); the arguments reach ``app.main``."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    entry, _ = _fresh_entry(monkeypatch)
    _fake_gui(monkeypatch, calls)
    argv = ["python -m clearwater", "--multiprocessing-fork"]
    assert entry.main(argv) == 3
    assert calls == [("activate", None), ("gui", argv)]


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
    """Reviewer A r2 #10: the PySide6 hook's prepends never make a duplicate entry.

    The parent prepends the folder; the frozen child inherits that ``PATH``, and before its
    entry runs, PyInstaller's PySide6 run-time hook prepends the bundle folder and PySide6's
    start-up its package folder. The child's entry then moves the folder back to the front
    (ruling 4: move-to-front with dedupe) and it still appears once; the hook's entries keep
    their order. A trailing-separator spelling of the folder counts as the folder.
    """
    executable = _frozen(monkeypatch, tmp_path)
    folder = os.path.dirname(executable)
    import clearwater.__main__ as entry

    environ = {"PATH": os.pathsep.join(["/a", "/b"])}
    assert entry.prepend_executable_folder(environ) is True  # the GUI process
    bundle = os.path.join(folder, "_internal")
    pyside = os.path.join(bundle, "PySide6")
    environ["PATH"] = pyside + os.pathsep + bundle + os.pathsep + environ["PATH"]
    assert entry.prepend_executable_folder(environ) is True  # the worker process
    assert environ["PATH"] == os.pathsep.join([folder, pyside, bundle, "/a", "/b"])
    assert environ["PATH"].split(os.pathsep).count(folder) == 1
    assert entry.prepend_executable_folder(environ) is False  # first and once: unchanged
    trailing = {"PATH": os.pathsep.join(["/a", folder + os.sep])}
    assert entry.prepend_executable_folder(trailing) is True  # the same folder, spelt with /
    assert trailing["PATH"] == os.pathsep.join([folder, "/a"])
    first_spelt_so = {"PATH": os.pathsep.join([folder + os.sep, "/a"])}
    assert entry.prepend_executable_folder(first_spelt_so) is False


def test_a_path_listing_the_folder_behind_another_ffmpeg_puts_it_first_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Ruling 4 on #10: the folder behind another FFmpeg folder comes out first, once.

    The other entries keep their original order (an empty entry included); every spelling
    of the folder is dropped from behind; only the given environment changes.
    """
    executable = _frozen(monkeypatch, tmp_path)
    folder = os.path.dirname(executable)
    import clearwater.__main__ as entry

    other_ffmpeg = str(tmp_path / "other-ffmpeg" / "bin")
    environ = {
        "PATH": os.pathsep.join(
            [other_ffmpeg, "/a", folder, "", "/b", folder.upper() + os.sep, "/c"]
        )
    }
    assert entry.prepend_executable_folder(environ) is True
    expected = [folder, other_ffmpeg, "/a", "", "/b", "/c"]
    if os.path.normcase("A") != "a":  # a case-sensitive platform: the upper-case one is another
        expected = [folder, other_ffmpeg, "/a", "", "/b", folder.upper() + os.sep, "/c"]
    assert environ["PATH"].split(os.pathsep) == expected
    assert entry.prepend_executable_folder(environ) is False


def test_a_quoted_spelling_of_the_folder_is_dropped_from_behind(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Reviewer A r3 #6: ``x;"<folder>"`` becomes ``<folder>;x`` (the quoted copy dropped)."""
    executable = _frozen(monkeypatch, tmp_path)
    folder = os.path.dirname(executable)
    import clearwater.__main__ as entry

    environ = {"PATH": os.pathsep.join(["/x", f'"{folder}"'])}
    assert entry.prepend_executable_folder(environ) is True
    assert environ["PATH"].split(os.pathsep) == [folder, "/x"]
    quoted_first = {"PATH": os.pathsep.join([f'"{folder}"', "/x"])}
    assert entry.prepend_executable_folder(quoted_first) is True  # shutil.which keeps quotes
    assert quoted_first["PATH"].split(os.pathsep) == [folder, "/x"]
    assert entry.prepend_executable_folder(quoted_first) is False


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
    # in-process and frozen: the F-E shim must not re-point THIS process's standard input
    monkeypatch.setattr(entry, "isolate_worker_stdin", lambda: False, raising=False)
    entry.main([executable, "--export-worker"])
    first = os.environ["PATH"].split(os.pathsep)[0]
    assert first == os.path.dirname(executable)


# CHARC's F-E ruling: the frozen worker reads its request pipe privately; children get NUL.
# TEMPORARY with the shim itself (DR-125's package moves the isolation into the worker).

_NO_GUI_PRELUDE = """
import importlib.abc
import json
import subprocess
import sys
from pathlib import Path


class NoGui(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name.split(".")[0] in ("PySide6", "shiboken6") or name == "clearwater.app.main" or (
            name == "clearwater.gui" or name.startswith("clearwater.gui.")
        ):
            raise ImportError("blocked by the test: " + name)
        return None


sys.meta_path.insert(0, NoGui())  # no window can open, whatever branch runs, on any revision
sys.path.insert(0, sys.argv[1])
sys.frozen = True
import clearwater.__main__ as entry
from clearwater import gpu_pack
"""
"""What each F-E child runs first: the GUI unimportable, the entry imported as frozen."""

_SPAWN_BEFORE_THE_PROBE = (
    _NO_GUI_PRELUDE
    + """
set_std_handle = []
if sys.platform == "win32":
    import ctypes

    kernel32 = ctypes.windll.kernel32
    real = kernel32.SetStdHandle

    def counting(*args):
        set_std_handle.append(1)
        return real(*args)

    kernel32.SetStdHandle = counting


def spawn_first():
    early = sorted(
        m for m in sys.modules if m.split(".")[0] == "cupy" or m == "clearwater.app.export_worker"
    )
    try:
        done = subprocess.run(
            [sys.executable, "-I", "-c", "import sys; print(len(sys.stdin.buffer.read()))"],
            capture_output=True,
            text=True,
            timeout=float(sys.argv[2]),
        )
        child = done.stdout.strip()
    except subprocess.TimeoutExpired:
        child = "timeout"
    import os

    print(json.dumps({
        "child_read": child,
        "early": early,
        "set_std_handle": len(set_std_handle),
        "stdin_fd": sys.stdin.fileno(),
        "stdin_inheritable": os.get_inheritable(sys.stdin.fileno()),
    }), flush=True)
    raise SystemExit(0)


gpu_pack.activate = spawn_first  # the branch's first call after the shim: before any probe
entry.main(["Clearwater.exe", "--export-worker"])
"""
)
"""The frozen worker branch, whose loader call is replaced by a spawn: a child with
``stdin=None`` reads its standard input to the end and prints how many bytes it got."""


def _app_data_environ(root: Path) -> dict[str, str]:
    """This environment with every app-data variable under ``root`` (never the user's)."""
    environ = dict(os.environ)
    for variable in (
        "APPDATA",
        "LOCALAPPDATA",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
    ):
        environ[variable] = str(root / variable.lower())
    return environ


def test_a_child_of_the_frozen_worker_branch_inherits_nul_not_the_request_pipe(
    tmp_path: Path,
) -> None:
    """F-E (i): spawned from the branch BEFORE the loader and the probe, a child reads EOF.

    The worker process's standard input is a pipe this test holds open and never writes to,
    as the parent holds the request pipe during a job. A child spawned with ``stdin=None``
    that inherited it would block until its 10 s bound; with the shim it inherits the null
    device and reads 0 bytes at once. At the spawn, neither the worker module nor CuPy is
    imported yet; the worker's own ``sys.stdin`` is the private descriptor, not 0, and that
    descriptor is NOT inheritable (Reviewer A r4 #3: the child's EOF alone cannot show it, since
    ``subprocess`` passes only the standard handles); on Windows ``SetStdHandle`` was called once.
    """
    import clearwater

    src_root = Path(clearwater.__file__).resolve().parents[1]
    process = subprocess.Popen(
        [sys.executable, "-I", "-c", _SPAWN_BEFORE_THE_PROBE, str(src_root), "10"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_app_data_environ(tmp_path),
    )
    try:
        status = process.wait(timeout=60)
    except subprocess.TimeoutExpired:
        process.kill()
        raise
    finally:
        assert process.stdin is not None
        process.stdin.close()
    assert process.stdout is not None and process.stderr is not None
    out, err = process.stdout.read().decode(), process.stderr.read().decode()
    assert status == 0, err
    seen = json.loads(out.strip().splitlines()[-1])
    assert seen["child_read"] == "0"
    assert seen["early"] == []
    assert seen["stdin_fd"] != 0
    assert seen["stdin_inheritable"] is False
    assert seen["set_std_handle"] == (1 if sys.platform == "win32" else 0)


_CANCEL_THROUGH_THE_SHIM = (
    _NO_GUI_PRELUDE
    + """
from clearwater.app import export_worker

gpu_pack.activate = lambda: None


def run(stdin, protocol):
    def send(obj):
        protocol.write(json.dumps(obj).encode("ascii") + b"\\n")
        protocol.flush()

    request = json.loads(stdin.readline())
    send({"progress": [1, 100, "working"]})
    cancel = stdin.readline()
    import os

    Path(sys.argv[2]).write_text(json.dumps({
        "fd": stdin.fileno(),
        "inheritable": os.get_inheritable(stdin.fileno()),
        "request_keys": sorted(request),
        "cancel": cancel.decode("ascii"),
    }), encoding="utf-8")
    send({"result": {"ok": False, "outputs": [], "warnings": [], "failure": "cancelled",
                     "device": "cpu", "elapsed_s": 1.0}})
    return 0


export_worker.run = run  # the real main: stdout taken over, then run(sys.stdin.buffer, ...)
raise SystemExit(entry.main(["Clearwater.exe", "--export-worker"]))
"""
)
"""The frozen worker branch with the real ``export_worker.main`` and a stand-in ``run`` that
reads the request, reports once, reads the parent's cancel line, records both, and ends."""


def test_the_frozen_worker_reads_its_request_and_the_cancel_line_through_the_private_fd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F-E (ii): ``test_cancel_is_delivered_on_stdin_and_the_child_ends``, re-pointed.

    The same parent (``ProcessExportJobs`` and its progress double from
    ``test_jobs_export_process``, cancelling after the first report), with the child running
    the frozen worker branch instead of a fake script: the request and the
    ``{"cancel": true}`` line still arrive, through the private descriptor (not 0).
    """
    process_tests = importlib.import_module("test_jobs_export_process")
    import clearwater
    from clearwater.jobs.export_process import CANCEL_LINE
    from clearwater.jobs.export_seam import CANCELLED

    for variable, value in _app_data_environ(tmp_path / "app-data").items():
        if variable.startswith(("APPDATA", "LOCALAPPDATA", "XDG_")):
            monkeypatch.setenv(variable, value)  # the child inherits these
    src_root = Path(clearwater.__file__).resolve().parents[1]
    seen = tmp_path / "seen.json"
    command = [sys.executable, "-I", "-c", _CANCEL_THROUGH_THE_SHIM, str(src_root), str(seen)]
    result, _ = process_tests._run(tmp_path, command, process_tests._Progress(cancel_after=1))
    assert result.failure is CANCELLED
    record = json.loads(seen.read_text(encoding="utf-8"))
    assert record["cancel"].encode("ascii") == CANCEL_LINE == b'{"cancel": true}\n'
    assert "format_version" in record["request_keys"]
    assert record["fd"] != 0
    assert record["inheritable"] is False  # Reviewer A r4 #3


_EOF_THROUGH_THE_SHIM = (
    _NO_GUI_PRELUDE
    + """
import os
import threading
import time

from clearwater.app import export_worker

gpu_pack.activate = lambda: None


def run(stdin, protocol):
    request = stdin.readline()
    eof = threading.Event()
    threading.Thread(target=export_worker._watch_stdin, args=(stdin, eof), daemon=True).start()
    start = time.monotonic()
    seen = eof.wait(float(sys.argv[3]))
    Path(sys.argv[2]).write_text(json.dumps({
        "fd": stdin.fileno(),
        "inheritable": os.get_inheritable(stdin.fileno()),
        "request": request.decode("ascii"),
        "eof": seen,
        "waited_s": round(time.monotonic() - start, 3),
    }), encoding="utf-8")
    return 0


export_worker.run = run  # the real main, then the real _watch_stdin on the private reader
raise SystemExit(entry.main(["Clearwater.exe", "--export-worker"]))
"""
)
"""The frozen worker branch with the real ``export_worker.main``; a stand-in ``run`` reads the
request line, then runs the REAL cancel watcher (``_watch_stdin``) on the private reader and
records whether the end of the stream reached it (no cancel line is ever sent)."""

_PARENT_THAT_DIES = """
import subprocess
import sys
import time

worker = subprocess.Popen(
    [sys.executable, "-I", "-c", sys.argv[1], sys.argv[2], sys.argv[3], "30"],
    stdin=subprocess.PIPE,
    stdout=subprocess.DEVNULL,
    stderr=subprocess.DEVNULL,
)
worker.stdin.write(b'{"request": 1}\\n')
worker.stdin.flush()
print(worker.pid, flush=True)
time.sleep(120)  # killed by the test long before this ends
"""
"""A parent that spawns the worker, writes its request, reports the worker's PID and is then
killed by the test while still holding the request pipe's write end."""


@pytest.mark.parametrize("ending", ["parent-closes", "parent-dies"])
def test_the_end_of_the_request_pipe_reaches_the_workers_reader_through_the_shim(
    tmp_path: Path, ending: str
) -> None:
    """Reviewer A r4 #3: the pipe's end (closed, or its parent killed) reaches the cancel watcher.

    The worker runs the frozen branch (the shim moves the pipe to the private descriptor) and
    the REAL ``export_worker._watch_stdin`` reads that descriptor. When the parent closes its
    end, or dies holding it, the watcher sees the end of the stream at once (well inside its 30
    s bound), through the private descriptor (not 0, not inheritable).
    """
    import clearwater

    src_root = Path(clearwater.__file__).resolve().parents[1]
    record = tmp_path / "eof.json"
    environ = _app_data_environ(tmp_path / "app-data")
    if ending == "parent-closes":
        worker = subprocess.Popen(
            [sys.executable, "-I", "-c", _EOF_THROUGH_THE_SHIM, str(src_root), str(record), "30"],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.PIPE,
            env=environ,
        )
        assert worker.stdin is not None
        worker.stdin.write(b'{"request": 1}\n')
        worker.stdin.close()  # the parent's end goes: the worker must see the end of the stream
        _, err = worker.communicate(timeout=60)
        assert worker.returncode == 0, err.decode("utf-8", "replace")
    else:
        parent = subprocess.Popen(
            [
                sys.executable,
                "-I",
                "-c",
                _PARENT_THAT_DIES,
                _EOF_THROUGH_THE_SHIM,
                str(src_root),
                str(record),
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            env=environ,
        )
        assert parent.stdout is not None
        worker_pid = int(parent.stdout.readline())
        parent.kill()  # dies holding the request pipe's write end
        parent.wait(timeout=60)
        for _ in range(600):  # up to 60 s for the worker's record
            if record.exists() and record.stat().st_size:
                break
            time.sleep(0.1)
        else:
            with contextlib.suppress(OSError):
                os.kill(worker_pid, 9)
            pytest.fail("the worker never saw the end of its request pipe")
    seen = json.loads(record.read_text(encoding="utf-8"))
    assert seen["request"] == '{"request": 1}\n'
    assert seen["eof"] is True
    assert seen["waited_s"] < 20
    assert seen["fd"] != 0
    assert seen["inheritable"] is False


_SHIM_FAILURE = (
    _NO_GUI_PRELUDE
    + """
import errno
import io
import os


class NoWorker(importlib.abc.MetaPathFinder):
    attempts = []

    def find_spec(self, name, path, target=None):
        if name == "clearwater.app.export_worker":
            NoWorker.attempts.append(name)
            raise ImportError("blocked by the test: " + name)
        return None


sys.meta_path.insert(0, NoWorker())  # the worker module is never imported for real
ran = []
gpu_pack.activate = lambda: ran.append("activate")
entry._start_logging = lambda: ran.append("log")


def open_fds():
    found = []
    for fd in range(256):
        try:
            os.fstat(fd)
        except OSError:
            continue
        found.append(fd)
    return found


def raiser(error):
    def fail(*args, **kwargs):
        raise error

    return fail


mode = sys.argv[2]
if mode == "open-null":
    os.open = raiser(OSError(errno.EACCES, "injected by the test"))
elif mode == "dup2":
    os.dup2 = raiser(OSError(errno.EBADF, "injected by the test"))
elif mode == "set-std-handle":
    import ctypes

    ctypes.windll.kernel32.SetStdHandle = lambda *args: 0
elif mode == "reader-open":
    entry.open = raiser(ValueError("injected by the test"))
elif mode == "reader-wrap":
    io.TextIOWrapper = raiser(TypeError("injected by the test"))
elif mode == "dup-emfile":
    os.dup = raiser(OSError(errno.EMFILE, "injected by the test"))
elif mode == "dup-ebadf":
    os.dup = raiser(OSError(errno.EBADF, "injected by the test"))
before = open_fds()
try:
    status, escaped = entry.main(["Clearwater.exe", "--export-worker"]), None
except ImportError as error:
    status, escaped = None, type(error).__name__
print(json.dumps({
    "status": status,
    "escaped": escaped,
    "ran": ran,
    "worker_imports": NoWorker.attempts,
    "fds_before": before,
    "fds_after": open_fds(),
}), flush=True)
"""
)
"""The frozen worker branch with one step of the shim made to fail (``sys.argv[2]``); the
loader, the log set-up and the worker import are recorded, never run for real."""


@pytest.mark.parametrize(
    ("mode", "kind"),
    [
        ("open-null", "PermissionError"),  # OSError(EACCES, ...) is a PermissionError
        ("dup2", "OSError"),
        pytest.param(
            "set-std-handle",
            "OSError",
            marks=pytest.mark.skipif(sys.platform != "win32", reason="the Win32 slot only"),
        ),
        ("reader-open", "ValueError"),
        ("reader-wrap", "TypeError"),
        ("dup-emfile", "OSError"),
    ],
)
def test_a_failed_stdin_isolation_ends_the_frozen_worker_before_anything_else(
    tmp_path: Path, mode: str, kind: str
) -> None:
    """Reviewer A r4 #4: fail closed. Status 2, one stderr line, no loader / log / worker import,
    and every descriptor the shim opened is closed again (the open set is unchanged).

    ``dup-emfile``: ``os.dup(0)`` failing for a reason other than ``EBADF`` is such a failure
    too, not the "no standard input" case.
    """
    import clearwater

    src_root = Path(clearwater.__file__).resolve().parents[1]
    done = subprocess.run(
        [sys.executable, "-I", "-c", _SHIM_FAILURE, str(src_root), mode],
        stdin=subprocess.PIPE,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=_app_data_environ(tmp_path),
    )
    assert done.returncode == 0, done.stderr
    seen = json.loads(done.stdout.strip().splitlines()[-1])
    assert seen["status"] == 2
    assert done.stderr == f"Clearwater: worker stdin isolation failed: {kind}\n"
    assert seen["ran"] == []
    assert seen["worker_imports"] == []
    assert seen["escaped"] is None
    assert seen["fds_after"] == seen["fds_before"]


def test_a_process_without_a_standard_input_runs_the_worker_branch_on(tmp_path: Path) -> None:
    """Reviewer A r4 #4: only ``os.dup(0)`` failing with ``EBADF`` is "nothing to move".

    The branch goes on: the loader runs and the worker import is attempted (the test's blocker
    refuses it), no refusal line is written, and no descriptor is opened.
    """
    import clearwater

    src_root = Path(clearwater.__file__).resolve().parents[1]
    done = subprocess.run(
        [sys.executable, "-I", "-c", _SHIM_FAILURE, str(src_root), "dup-ebadf"],
        stdin=subprocess.PIPE,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=_app_data_environ(tmp_path),
    )
    assert done.returncode == 0, done.stderr
    seen = json.loads(done.stdout.strip().splitlines()[-1])
    assert seen["status"] is None
    assert seen["escaped"] == "ImportError"
    assert seen["ran"] == ["activate"]
    assert seen["worker_imports"] == ["clearwater.app.export_worker"]
    assert "isolation failed" not in done.stderr
    assert seen["fds_after"] == seen["fds_before"]


def test_the_worker_branch_moves_no_standard_input_when_not_frozen(
    monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """F-E (iii): the 1.0.0 lock. A source run duplicates nothing and calls no ``SetStdHandle``.

    Since Reviewer A r3 #1 a source ``--export-worker`` reaches the GUI (a stand-in here), as
    in 1.0.0; the shim is never reached on that path either.
    """
    monkeypatch.delattr(sys, "frozen", raising=False)
    entry, _ = _fresh_entry(monkeypatch)
    _fake_gui(monkeypatch, calls)
    dups: list[int] = []
    set_std_handle: list[object] = []

    def no_dup(fd: int) -> int:
        dups.append(fd)
        raise AssertionError("the source worker branch duplicated a descriptor")

    monkeypatch.setattr(os, "dup", no_dup)
    if sys.platform == "win32":
        import ctypes

        def counting(*args: object) -> int:
            set_std_handle.append(args)
            return 1

        monkeypatch.setattr(ctypes.windll.kernel32, "SetStdHandle", counting, raising=False)
    stdin = sys.stdin
    assert entry.main(["python -m clearwater", "--export-worker"]) == 3
    assert calls == [("activate", None), ("gui", ["python -m clearwater", "--export-worker"])]
    assert entry.isolate_worker_stdin() is False  # called directly: still nothing when not frozen
    assert dups == []
    assert set_std_handle == []
    assert sys.stdin is stdin


# Reviewer A r2 #11: the worker branch's import graph, in a fresh interpreter.

_WORKER_IMPORT_PROBE = """
import importlib.abc
import sys


class NoGui(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name in ("clearwater.app.main", "clearwater.gui") or name.startswith("clearwater.gui."):
            raise ImportError("the GUI is blocked by the test: " + name)
        return None


sys.meta_path.insert(0, NoGui())  # no window can open, whatever the entry does
sys.path.insert(0, sys.argv[1])
sys.frozen = True  # the worker branch is frozen-only (Reviewer A r3 #1)
import clearwater.__main__ as entry
from clearwater.app import export_worker
export_worker.main = lambda argv=None: 0
status = entry.main(["Clearwater.exe", "--export-worker"])
loaded = sorted(m for m in sys.modules if m.startswith(tuple(sys.argv[2:])))
print("status", status, "loaded", ",".join(loaded) or "-")
"""
"""Import the entry and the worker afresh, run the worker branch (its ``main`` stubbed), and
print which :data:`BLOCKED` modules are then loaded. The GUI modules cannot be imported in the
child at all (an attempt fails the probe), so no window opens on any code revision."""


def _probe_worker_imports(src_root: Path, app_data: Path) -> str:
    """Run :data:`_WORKER_IMPORT_PROBE` on the ``clearwater`` under ``src_root``.

    Args:
        src_root: The folder holding the ``clearwater`` package to import.
        app_data: Where the child's app-data variables point (never the user's folders).

    Returns:
        The probe's output line.
    """
    environ = dict(os.environ)
    for variable in ("APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        environ[variable] = str(app_data / variable.lower())
    done = subprocess.run(
        [sys.executable, "-I", "-c", _WORKER_IMPORT_PROBE, str(src_root), *BLOCKED],
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
        env=environ,
    )
    assert done.returncode == 0, done.stderr
    return done.stdout.strip()


def test_the_worker_branch_imports_no_qt_in_a_fresh_interpreter(tmp_path: Path) -> None:
    """The real import graph of ``__main__`` and ``export_worker``: no PySide6, no shiboken6."""
    import clearwater

    src_root = Path(clearwater.__file__).resolve().parents[1]
    assert _probe_worker_imports(src_root, tmp_path) == "status 0 loaded -"


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
    line = _probe_worker_imports(tmp_path / "src", tmp_path / "app-data")
    assert line.startswith("status 0 loaded PySide6")
    assert "shiboken6" in line


# CHARC's F-D ruling: a frozen ``-m`` runs a GPU pack module only; ``-c`` and the rest refuse.

PROBE_BODY = """
import sys
from pathlib import Path
Path(sys.argv[1]).write_text(repr((__name__, sys.argv[2:], __file__)), encoding="utf-8")
"""
"""A pack module that records its ``__name__``, its arguments and its file, then returns."""

PROBE_SYS_BODY = """
import sys
from pathlib import Path
main = getattr(sys.modules.get("__main__"), "__file__", None)
Path(sys.argv[1]).write_text(
    repr((__name__, sys.argv[2:], __file__, sys.argv[0], main)), encoding="utf-8"
)
"""
""":data:`PROBE_BODY` that also records ``sys.argv[0]`` and ``sys.modules["__main__"]``'s file."""


def _package(root: Path, name: str, *, init: bool = True, body: str = "") -> Path:
    """Write a package ``name`` under ``root`` (a regular one when ``init``) with ``probe.py``."""
    folder = root / name
    folder.mkdir(parents=True)
    if init:
        (folder / "__init__.py").write_text("", encoding="utf-8")
    (folder / "probe.py").write_text(body or PROBE_BODY, encoding="utf-8")
    return folder


def _no_real_app_data(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, seen: list[tuple[str, Any]]
) -> None:
    """App data under ``tmp_path`` and the log set-up stubbed (recorded), whatever runs."""
    for variable in ("APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        monkeypatch.setenv(variable, str(tmp_path / variable.lower()))

    def configure(folder: Path, **_: Any) -> Path:
        seen.append(("log", folder))
        return folder / "clearwater.log"

    monkeypatch.setattr(config_log, "configure_logging", configure)


def _drop_modules(prefix: str) -> None:
    """Forget every test package imported under ``prefix`` (the synthetic pack modules)."""
    for name in [m for m in sys.modules if m == prefix or m.startswith(prefix)]:
        del sys.modules[name]
    importlib.invalidate_caches()


@pytest.fixture
def pack(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[tuple[Path, list[tuple[str, Any]]]]:
    """A loaded synthetic pack: the frozen entry, a fake GUI, ``activate`` returning ``loaded``.

    The stand-in loader puts ``tmp_path/pack/site-packages`` first on ``sys.path`` (as the real
    one does) and records its call. ``sys.argv`` and ``sys.path`` are restored after the test
    and every ``packmod_*`` module is forgotten.

    Yields:
        The pack's ``site-packages`` and the recorded calls.
    """
    site = tmp_path / "pack" / "site-packages"
    site.mkdir(parents=True)
    seen: list[tuple[str, Any]] = []

    def activate() -> gpu_pack.PackStatus:
        seen.append(("activate", None))
        sys.path.insert(0, str(site))
        return gpu_pack.PackStatus(gpu_pack.STAMP, "loaded", site_packages=site)

    _frozen(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
    monkeypatch.setattr(sys, "argv", list(sys.argv))
    monkeypatch.setattr(sys, "path", list(sys.path))
    monkeypatch.setattr(gpu_pack, "activate", activate)
    _fake_gui(monkeypatch, seen)
    _no_real_app_data(monkeypatch, tmp_path, seen)
    yield site, seen
    _drop_modules("packmod_")


def test_a_frozen_dash_m_runs_a_pack_module_after_the_loader_without_qt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pack: tuple[Path, list[tuple[str, Any]]]
) -> None:
    """``<exe> -m <pack module> a b``: loader first, then the module as ``__main__``, no Qt."""
    site, seen = pack
    _package(site, "packmod_run", body=PROBE_SYS_BODY)
    record = tmp_path / "ran.txt"
    entry, blocker = _fresh_entry(monkeypatch)
    status = entry.main(["Clearwater.exe", "-m", "packmod_run.probe", str(record), "a", "b"])
    assert status == 0
    name, args, file, argv0, main_file = ast.literal_eval(record.read_text(encoding="utf-8"))
    assert (name, args) == ("__main__", ["a", "b"])
    assert Path(file) == site / "packmod_run" / "probe.py"
    # Reviewer A r3 #10: what alter_sys=True gives, as CPython's -m does
    assert argv0 == file  # not "Clearwater.exe"
    assert main_file == file  # sys.modules["__main__"] is the module while it runs
    assert seen == [("activate", None)]  # the loader ran; the GUI did not
    assert blocker.attempts == []
    assert not [m for m in sys.modules if m.startswith(BLOCKED)]


@pytest.mark.parametrize(
    ("argv", "line"),
    [
        (["Clearwater.exe", "-m", "http.server"], "-m 'http.server': not a GPU pack module"),
        (["Clearwater.exe", "-m", "json.tool", "x"], "-m 'json.tool': not a GPU pack module"),
        (["Clearwater.exe", "-m", "clearwater"], "-m 'clearwater': not a GPU pack module"),
        (["Clearwater.exe", "-m", "no_such_module_x"], "not a GPU pack module"),
        (["Clearwater.exe", "-m", ".relative"], "not a GPU pack module"),
        (["Clearwater.exe", "-m"], "-m needs a module name"),
        (["Clearwater.exe", "-m", ""], "-m needs a module name"),
        (["Clearwater.exe", "-c", "print(1)"], "-c is not supported"),
        (["Clearwater.exe", "-c"], "-c is not supported"),
    ],
)
def test_a_frozen_dash_m_of_anything_else_and_dash_c_refuse_with_one_line(
    pack: tuple[Path, list[tuple[str, Any]]],
    capsys: pytest.CaptureFixture[str],
    argv: list[str],
    line: str,
) -> None:
    """Refused: exit 2, ONE stderr line, nothing on stdout, no GUI; ``-c`` before the loader."""
    _, seen = pack
    import clearwater.__main__ as entry

    assert entry.main(argv) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err.count("\n") == 1
    assert err.startswith("Clearwater: ")
    assert line in err
    loader_first = argv[1] == "-m" and len(argv) > 2 and argv[2] != ""
    assert seen == ([("activate", None)] if loader_first else [])


@pytest.mark.parametrize("outcome", ["absent", "rejected"])
def test_a_frozen_dash_m_refuses_when_no_pack_is_loaded(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    outcome: gpu_pack.Outcome,
) -> None:
    """An absent or rejected pack: no ``-m`` target resolves from it, even one on ``sys.path``."""
    _frozen(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
    seen: list[tuple[str, Any]] = []
    _fake_gui(monkeypatch, seen)
    _no_real_app_data(monkeypatch, tmp_path, seen)
    site = tmp_path / "site"
    _package(site, "packmod_absent")
    monkeypatch.syspath_prepend(str(site))

    def activate() -> gpu_pack.PackStatus:
        return gpu_pack.PackStatus(gpu_pack.STAMP, outcome, reason="x")

    monkeypatch.setattr(gpu_pack, "activate", activate)
    import clearwater.__main__ as entry

    try:
        assert entry.main(["Clearwater.exe", "-m", "packmod_absent.probe", "f"]) == 2
        assert "no GPU pack is loaded" in capsys.readouterr().err
        assert seen == []
        assert "packmod_absent" not in sys.modules
    finally:
        _drop_modules("packmod_")


def test_a_name_in_the_bundle_and_the_pack_is_judged_by_the_first_on_sys_path(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, pack: tuple[Path, list[tuple[str, Any]]]
) -> None:
    """The bundle copy first: not from the pack. The pack first: from it, and its copy runs."""
    site, _ = pack
    bundle = tmp_path / "bundle"
    _package(site, "packmod_shared")
    _package(bundle, "packmod_shared")
    sys.path.insert(0, str(bundle))
    sys.path.insert(1, str(site))
    importlib.invalidate_caches()
    assert not gpu_pack.module_from_pack("packmod_shared.probe", site)
    sys.path.remove(str(site))
    sys.path.insert(0, str(site))
    importlib.invalidate_caches()
    assert gpu_pack.module_from_pack("packmod_shared.probe", site)
    import clearwater.__main__ as entry

    record = tmp_path / "ran.txt"
    # The stand-in loader puts the pack first (again), ahead of the bundle's copy.
    assert entry.main(["Clearwater.exe", "-m", "packmod_shared.probe", str(record)]) == 0
    _, _, file = ast.literal_eval(record.read_text(encoding="utf-8"))
    assert Path(file) == site / "packmod_shared" / "probe.py"


def test_a_namespace_package_is_from_the_pack_only_when_every_portion_is(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """``cuda`` is a namespace package: one portion outside the pack refuses the name."""
    site = tmp_path / "site"
    other = tmp_path / "other"
    _package(site, "packmod_ns", init=False)
    monkeypatch.setattr(sys, "path", [str(site), *sys.path])
    importlib.invalidate_caches()
    try:
        assert gpu_pack.module_from_pack("packmod_ns.probe", site)
        (other / "packmod_ns").mkdir(parents=True)
        sys.path.insert(1, str(other))
        importlib.invalidate_caches()
        assert not gpu_pack.module_from_pack("packmod_ns.probe", site)
    finally:
        _drop_modules("packmod_")


def test_built_in_stdlib_and_bundle_modules_are_not_from_the_pack(tmp_path: Path) -> None:
    """A built-in (``sys``), the stdlib, the bundle's own packages: never pack modules."""
    for name in ("sys", "os", "http.server", "clearwater.app.export_worker", "numpy"):
        assert not gpu_pack.module_from_pack(name, tmp_path)


@pytest.mark.parametrize(
    ("body", "status"), [("raise SystemExit(5)", 5), ("raise RuntimeError('boom')", 1)]
)
def test_a_pack_modules_exit_passes_and_its_exception_is_printed_not_raised(
    capsys: pytest.CaptureFixture[str],
    pack: tuple[Path, list[tuple[str, Any]]],
    body: str,
    status: int,
) -> None:
    """``SystemExit`` keeps its code; any other exception is printed, status 1 (no dialog)."""
    site, _ = pack
    name = f"packmod_exit{status}"
    _package(site, name, body=body)
    import clearwater.__main__ as entry

    result: object
    try:
        result = entry.main(["Clearwater.exe", "-m", f"{name}.probe"])
    except SystemExit as stop:
        result = stop.code
    assert result == status
    err = capsys.readouterr().err
    assert ("RuntimeError: boom" in err) == (status == 1)


@pytest.mark.parametrize(
    "argv", [["clearwater", "-m", "x"], ["clearwater", "-c", "print(1)"], ["clearwater", "-m"]]
)
def test_a_source_run_sends_dash_m_and_dash_c_to_the_gui_as_before(
    monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]], argv: list[str]
) -> None:
    """Not frozen: no new branch; ``python -m clearwater -m x`` reaches the GUI as on 1.0.0."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    _fake_gui(monkeypatch, calls)
    import clearwater.__main__ as entry

    assert entry.main(argv) == 3
    assert calls == [("activate", None), ("gui", argv)]


_PATHFINDER_PROBE = """
import importlib.abc
import sys
import types
from pathlib import Path


class NoQt(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name.split(".")[0] in ("PySide6", "shiboken6"):
            raise ImportError("blocked by the test: " + name)
        return None


sys.meta_path.insert(0, NoQt())  # no window can open, whatever branch runs
gui = types.ModuleType("clearwater.app.main")
gui.main = lambda argv=None: print("gui reached") or 9
sys.modules["clearwater.app.main"] = gui
sys.path.insert(0, sys.argv[1])
sys.frozen = True
import clearwater.__main__ as entry
from clearwater import gpu_pack
site = Path(sys.argv[2])
gpu_pack.activate = lambda: gpu_pack.PackStatus(gpu_pack.STAMP, "loaded", site_packages=site)
try:
    status = entry.main(["Clearwater.exe", "-m", sys.argv[3], "canary", "nvrtc"])
except SystemExit as stop:
    status = stop.code
loaded = sorted(m for m in sys.modules if m.startswith(("PySide6", "shiboken6")))
print("status", status, "qt", ",".join(loaded) or "-")
"""
"""Run the real ``cuda.pathfinder`` canary module through the frozen ``-m`` branch."""


def test_the_real_pathfinder_canary_module_runs_through_the_frozen_dash_m(
    tmp_path: Path,
) -> None:
    """``cuda.pathfinder``'s probe module (the F-D re-entry), from where it is installed.

    A fresh interpreter (``-I``) plays the frozen executable; its loaded "pack" is the
    ``site-packages`` that holds ``cuda.pathfinder`` here. The probe prints its JSON payload
    (``ok`` or ``not-found``: either proves it ran), exits 0, and no PySide6 is imported.
    Fail-safe on any code: PySide6 is unimportable in the child, the GUI's ``main`` is a
    stand-in that prints ``gui reached``, and the app-data variables point under ``tmp_path``.
    """
    import clearwater

    spec = importlib.util.find_spec("cuda.pathfinder")
    if spec is None or not spec.submodule_search_locations:
        pytest.skip("cuda.pathfinder is not installed (the gpu extra)")
    site = Path(next(iter(spec.submodule_search_locations))).parents[1]
    module = "cuda.pathfinder._dynamic_libs.dynamic_lib_subprocess"
    src_root = Path(clearwater.__file__).resolve().parents[1]
    environ = dict(os.environ)
    for variable in ("APPDATA", "LOCALAPPDATA", "XDG_CONFIG_HOME", "XDG_CACHE_HOME"):
        environ[variable] = str(tmp_path / variable.lower())
    done = subprocess.run(
        [sys.executable, "-I", "-c", _PATHFINDER_PROBE, str(src_root), str(site), module],
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=environ,
    )
    assert done.returncode == 0, done.stderr
    lines = done.stdout.strip().splitlines()
    assert lines[-1] == "status 0 qt -"
    assert '"status": ' in lines[-2]
    assert '"abs_path": ' in lines[-2]


# CHARC's widening of F-D (gen 15): every CPython spelling of -m / -c is a re-entry.


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["x", "-m", "a.b", "c"], ["-m", "a.b", "c"]),
        (["x", "-mfoo", "c"], ["-m", "foo", "c"]),
        (["x", "-I", "-m", "a"], ["-m", "a"]),
        (["x", "-Im", "a"], ["-m", "a"]),
        (["x", "-X", "utf8", "-m", "a"], ["-m", "a"]),
        (["x", "-I", "-s", "-X", "utf8", "-W", "ignore", "-E", "-m", "a"], ["-m", "a"]),
        (["x", "-c"], ["-c"]),
        (["x", "-cCODE"], ["-c", "CODE"]),
        (["x", "-I", "-c", "CODE"], ["-c", "CODE"]),
        (["x", "-qmljsdebugger=port:1234"], ["-m", "ljsdebugger=port:1234"]),
        (["x", "-m"], ["-m"]),
        (["x"], None),
        (["x", "-I"], None),
        (["x", "-I", "photo.heic"], None),
        (["x", "-X", "utf8"], None),
        (["x", "-X"], None),
        (["x", "-platform", "offscreen"], None),
        (["x", "-style", "fusion"], None),
        (["x", "-reverse"], None),
        (["x", "-widgetcount"], None),
        (["x", "photo.heic", "-m", "a"], None),
        (["x", "--other"], None),
        # Reviewer A r3 #2: clusters without m / c, and -X / -W values attached
        (["x", "-Xutf8", "-m", "a"], ["-m", "a"]),
        (["x", "-Wignore", "-m", "a"], ["-m", "a"]),
        (["x", "-Wignore", "-cpass"], ["-c", "pass"]),
        (["x", "-OO", "-m", "a"], ["-m", "a"]),
        (["x", "-Es", "-m", "a"], ["-m", "a"]),
        (["x", "-IIs", "-m", "a"], ["-m", "a"]),
        (["x", "-bb", "-m", "a"], ["-m", "a"]),
        (["x", "-IXutf8", "-m", "a"], ["-m", "a"]),
        (["x", "-IW", "ignore", "-m", "a"], ["-m", "a"]),
        (["x", "-IIm", "a"], ["-m", "a"]),
        (["x", "-E", "-s", "-m", "a"], ["-m", "a"]),
        (["x", "-movie.mp4"], ["-m", "ovie.mp4"]),
        # Reviewer A r4 #1: the letters and the long option CPython 3.12 accepts (by execution)
        (["x", "-R", "-m", "x"], ["-m", "x"]),
        (["x", "-t", "-m", "x"], ["-m", "x"]),
        (["x", "-Rt", "-c", "pass"], ["-c", "pass"]),
        (["x", "-tRIm", "x"], ["-m", "x"]),
        (["x", "--check-hash-based-pycs", "always", "-m", "x"], ["-m", "x"]),
        (["x", "--check-hash-based-pycs", "never", "-c", "pass"], ["-c", "pass"]),
        (["x", "--check-hash-based-pycs", "default", "-I", "-m", "x"], ["-m", "x"]),
        (["x", "-I", "--check-hash-based-pycs", "always", "-Xutf8", "-m", "x"], ["-m", "x"]),
        # ... and what CPython refuses or answers by printing: the GUI, as before
        (["x", "--check-hash-based-pycs=always", "-m", "x"], None),
        (["x", "--check-hash-based-pycs"], None),
        (["x", "--check-hash-based-pycs", "-m", "x"], None),
        (["x", "--check-hash-based-pycs", "bogus", "-m", "x"], None),
        (["x", "--check-hash", "always", "-m", "x"], None),
        (["x", "--help", "-m", "x"], None),
        (["x", "--help-env", "-m", "x"], None),
        (["x", "--help-xoptions", "-m", "x"], None),
        (["x", "--help-all", "-m", "x"], None),
        (["x", "--version", "-m", "x"], None),
        (["x", "-a", "-m", "x"], None),
        (["x", "-Rp", "-m", "x"], None),
        # still not re-entries: they go to the GUI as before
        (["x", "-X"], None),
        (["x", "-Xutf8"], None),
        (["x", "-h"], None),
        (["x", "-V"], None),
        (["x", "-?"], None),
        (["x", "-hm", "a"], None),
        (["x", "--version"], None),
        (["x", "-"], None),
        (["x", "--"], None),
        (["x", "--", "-m", "a"], None),
        (["x", ""], None),
        (["x", "é"], None),
        (["x", "-style=fusion"], None),
    ],
)
def test_interpreter_reentry_follows_cpythons_grammar(
    argv: list[str], expected: list[str] | None
) -> None:
    """Flags dropped, attached operands split; Qt's word options and files are not re-entries."""
    import clearwater.__main__ as entry

    assert entry.interpreter_reentry(argv) == expected


def _cpython(*args: str) -> tuple[int, str]:
    """Run this interpreter (the dev one; no product code) with ``args``; (exit, stdout)."""
    environ = {k: v for k, v in os.environ.items() if not k.upper().startswith("PYTHON")}
    done = subprocess.run(
        [sys.executable, "-B", *args],
        stdin=subprocess.DEVNULL,
        capture_output=True,
        text=True,
        timeout=60,
        check=False,
        env=environ,
    )
    return done.returncode, done.stdout


def test_the_option_letters_are_cpythons_by_execution() -> None:
    """Reviewer A r4 #1: :data:`FLAG_LETTERS` / :data:`VALUE_LETTERS` equal what CPython does.

    For every ASCII letter but ``m`` / ``c``: ``-<L> -c pass`` exiting 0 silently is a flag;
    exiting 0 with output (help, version) is informational; otherwise ``-<L> x -c pass``
    exiting 0 is a value letter; otherwise CPython refuses it. The interpreter is this test's
    own (the bundle's version); only ``-c pass`` runs.
    """
    import string

    import clearwater.__main__ as entry

    flags, values = set(), set()
    for letter in string.ascii_letters:
        if letter in "mc":
            continue
        code, out = _cpython(f"-{letter}", "-c", "pass")
        if code == 0:
            if not out:
                flags.add(letter)
            continue
        if _cpython(f"-{letter}", "x", "-c", "pass")[0] == 0:
            values.add(letter)
    assert flags == set(entry.FLAG_LETTERS)
    assert values == set(entry.VALUE_LETTERS)


def test_the_long_options_are_cpythons_by_execution() -> None:
    """Reviewer A r4 #1: ``--check-hash-based-pycs`` takes the next argument, one of its three
    values; CPython refuses the ``=`` spelling, a missing or unknown value and an abbreviation."""
    import clearwater.__main__ as entry

    option = "--check-hash-based-pycs"
    for value in sorted(entry.LONG_VALUE_OPTIONS[option]):
        assert _cpython(option, value, "-c", "pass") == (0, "")
    assert set(entry.LONG_VALUE_OPTIONS) == {option}
    for refused in (
        [f"{option}=always", "-c", "pass"],
        [option, "bogus", "-c", "pass"],
        [option, "-c", "pass"],
        [option],
        ["--check-hash", "always", "-c", "pass"],
        ["--other", "-c", "pass"],
    ):
        assert _cpython(*refused)[0] != 0, refused
    for informational in ("--help", "--help-env", "--help-xoptions", "--help-all", "--version"):
        code, out = _cpython(informational, "-c", "pass")
        assert code == 0 and out, informational  # it prints and exits: not a re-entry


def test_cpythons_own_interpreter_flags_prefix_is_a_re_entry() -> None:
    """Reviewer A r3 #2: ``subprocess._args_from_interpreter_flags()`` + ``-m x`` re-enters.

    The flags come from a child started with ``-OO -Wignore -Xutf8`` (as CHARC asked) and from
    this test process; either prefix before ``-m x`` must be judged a re-entry. The child runs
    no product code.
    """
    import clearwater.__main__ as entry

    done = subprocess.run(
        [
            sys.executable,
            "-OO",
            "-Wignore",
            "-Xutf8",
            "-c",
            "import json, subprocess; print(json.dumps(subprocess._args_from_interpreter_flags()))",
        ],
        capture_output=True,
        text=True,
        timeout=60,
        check=True,
    )
    flags = json.loads(done.stdout)
    assert "-OO" in flags and "-Wignore" in flags  # a repeated cluster, an attached value
    assert flags[flags.index("-X") + 1] == "utf8"  # -X comes as a separate value
    assert entry.interpreter_reentry(["x", *flags, "-m", "x"]) == ["-m", "x"]
    own = subprocess._args_from_interpreter_flags()  # type: ignore[attr-defined]
    assert entry.interpreter_reentry(["x", *own, "-m", "x"]) == ["-m", "x"]


@pytest.mark.parametrize(
    "prefix",
    [
        ["-mpackmod_run.probe"],
        ["-I", "-m", "packmod_run.probe"],
        ["-Im", "packmod_run.probe"],
        ["-X", "utf8", "-m", "packmod_run.probe"],
        ["-I", "-W", "ignore", "-sm", "packmod_run.probe"],
        ["-Xutf8", "-m", "packmod_run.probe"],
        ["-Wignore", "-m", "packmod_run.probe"],
        ["-OO", "-m", "packmod_run.probe"],
        ["-Es", "-m", "packmod_run.probe"],
        ["-R", "-m", "packmod_run.probe"],
        ["-t", "-m", "packmod_run.probe"],
        ["--check-hash-based-pycs", "always", "-m", "packmod_run.probe"],
    ],
)
def test_every_spelling_of_dash_m_runs_a_pack_module(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    pack: tuple[Path, list[tuple[str, Any]]],
    prefix: list[str],
) -> None:
    """Attached, after flags, after ``-X`` / ``-W`` values: the pack module runs, no Qt."""
    site, seen = pack
    _package(site, "packmod_run")
    record = tmp_path / "ran.txt"
    entry, blocker = _fresh_entry(monkeypatch)
    assert entry.main(["Clearwater.exe", *prefix, str(record), "a"]) == 0
    name, args, _ = ast.literal_eval(record.read_text(encoding="utf-8"))
    assert (name, args) == ("__main__", ["a"])
    assert seen == [("activate", None)]
    assert blocker.attempts == []


@pytest.mark.parametrize(
    ("args", "line"),
    [
        (["-cCODE"], "-c is not supported"),
        (["-I", "-c", "CODE"], "-c is not supported"),
        (["-Ic", "CODE"], "-c is not supported"),
        (["-mhttp.server"], "-m 'http.server': not a GPU pack module"),
        (["-I", "-m", "http.server"], "-m 'http.server': not a GPU pack module"),
        (["-X", "utf8", "-m", "json.tool"], "-m 'json.tool': not a GPU pack module"),
        (["-qmljsdebugger=port:1234"], "not a GPU pack module"),
        (["-I", "-m"], "-m needs a module name"),
        (["-Rt", "-c", "pass"], "-c is not supported"),
        (["--check-hash-based-pycs", "never", "-c", "pass"], "-c is not supported"),
    ],
)
def test_every_spelling_of_dash_c_and_of_a_foreign_dash_m_refuses(
    pack: tuple[Path, list[tuple[str, Any]]],
    capsys: pytest.CaptureFixture[str],
    args: list[str],
    line: str,
) -> None:
    """Refused: exit 2, one stderr line, no GUI (``-qmljsdebugger`` is the named collateral)."""
    _, seen = pack
    import clearwater.__main__ as entry

    assert entry.main(["Clearwater.exe", *args]) == 2
    out, err = capsys.readouterr()
    assert out == ""
    assert err.count("\n") == 1
    assert line in err
    assert not [call for call in seen if call[0] == "gui"]


@pytest.mark.parametrize(
    "args",
    [
        ["-platform", "offscreen"],
        ["-style", "fusion"],
        ["-reverse"],
        ["-widgetcount"],
        ["-I"],
        ["-X", "utf8"],
        ["photo.heic", "-m", "x"],
        ["--check-hash-based-pycs=always", "-m", "x"],
        ["--check-hash-based-pycs"],
    ],
)
def test_qt_options_and_non_reentries_reach_the_gui_as_before_when_frozen(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]], args: list[str]
) -> None:
    """Frozen: anything that is not a re-entry still reaches the GUI with its argv unchanged."""
    _frozen(monkeypatch, tmp_path)
    monkeypatch.setenv("PATH", os.environ.get("PATH", ""))
    _fake_gui(monkeypatch, calls)
    import clearwater.__main__ as entry

    argv = ["Clearwater.exe", *args]
    assert entry.main(argv) == 3
    assert calls == [("log", tmp_path / "cfg" / "logs"), ("activate", None), ("gui", argv)]


@pytest.mark.parametrize(
    "args",
    [
        ["-mfoo"],
        ["-I", "-m", "x"],
        ["-Im", "x"],
        ["-X", "utf8", "-m", "x"],
        ["-cCODE"],
        ["-I", "-c", "CODE"],
        ["-qmljsdebugger=port:1"],
    ],
)
def test_a_source_run_sends_every_spelling_to_the_gui_as_before(
    monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]], args: list[str]
) -> None:
    """Not frozen: no re-entry branch on any form (1.0.0's behaviour)."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    _fake_gui(monkeypatch, calls)
    import clearwater.__main__ as entry

    argv = ["clearwater", *args]
    assert entry.main(argv) == 3
    assert calls == [("activate", None), ("gui", argv)]
