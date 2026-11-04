"""The frozen-build entry: the worker re-entry and the bundled-tool PATH (WP6.1, AD-34, D1).

Parallel leg, synthetic: ``sys.frozen`` and ``sys.executable`` are monkeypatched, the export
worker's ``main``, the GPU pack loader, the log set-up and the GUI's ``main`` are stubbed, so no
window opens and no real app-data folder is touched. One check runs in a fresh interpreter
(``python -I -c``), because only a fresh import graph shows what the worker branch imports. The
frozen build itself is checked by hand (the WP6.1 report).
"""

from __future__ import annotations

import ast
import importlib
import importlib.abc
import importlib.util
import json
import logging
import os
import shutil
import subprocess
import sys
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
    print(json.dumps({
        "child_read": child,
        "early": early,
        "set_std_handle": len(set_std_handle),
        "stdin_fd": sys.stdin.fileno(),
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
    imported yet; the worker's own ``sys.stdin`` is the private descriptor, not 0; on Windows
    ``SetStdHandle`` was called once.
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
    Path(sys.argv[2]).write_text(json.dumps({
        "fd": stdin.fileno(),
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


def test_the_worker_branch_moves_no_standard_input_when_not_frozen(
    monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, Any]]
) -> None:
    """F-E (iii): the 1.0.0 lock. A source run duplicates nothing and calls no ``SetStdHandle``."""
    monkeypatch.delattr(sys, "frozen", raising=False)
    entry, _ = _fresh_entry(monkeypatch)
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
    assert entry.main(["python -m clearwater", "--export-worker"]) == 7
    assert calls == [("activate", None), ("worker", [])]
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
    _package(site, "packmod_run")
    record = tmp_path / "ran.txt"
    entry, blocker = _fresh_entry(monkeypatch)
    status = entry.main(["Clearwater.exe", "-m", "packmod_run.probe", str(record), "a", "b"])
    assert status == 0
    name, args, file = ast.literal_eval(record.read_text(encoding="utf-8"))
    assert (name, args) == ("__main__", ["a", "b"])
    assert Path(file) == site / "packmod_run" / "probe.py"
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
    ],
)
def test_interpreter_reentry_follows_cpythons_grammar(
    argv: list[str], expected: list[str] | None
) -> None:
    """Flags dropped, attached operands split; Qt's word options and files are not re-entries."""
    import clearwater.__main__ as entry

    assert entry.interpreter_reentry(argv) == expected


@pytest.mark.parametrize(
    "prefix",
    [
        ["-mpackmod_run.probe"],
        ["-I", "-m", "packmod_run.probe"],
        ["-Im", "packmod_run.probe"],
        ["-X", "utf8", "-m", "packmod_run.probe"],
        ["-I", "-W", "ignore", "-sm", "packmod_run.probe"],
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
