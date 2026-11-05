"""Run bounded, headless Windows onedir checks without entering the GUI branch.

Only the commissioned refusal/worker argument sets may launch Clearwater. Each
row has fresh disposable profile roots and a System32-only PATH. A planted
import failure uses a separate copy; the shipping folder is only read. Process
supervision is not window evidence: the seat supplies the independent UIA watch.
"""

from __future__ import annotations

import contextlib
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import NamedTuple, cast

import psutil


class SmokeError(RuntimeError):
    """A named smoke row failed validation, launch or bounded process cleanup."""


class SmokeRow(NamedTuple):
    """An approved entry call and its exact status, stdin and stderr contract.

    Attributes:
        name: The row's diagnostic name.
        arguments: The arguments after Clearwater.exe; an exact allowlist applies.
        stdin: The complete request stream, closed immediately after writing.
        status: Expected exit status; None requires a non-zero exit.
        stderr: The one expected stderr line, without its final newline.
    """

    name: str
    arguments: tuple[str, ...]
    stdin: str
    status: int | None
    stderr: str


_COMMAND = "Clearwater: -c is not supported"
_MODULE = "Clearwater: -m 'http.server': no GPU pack is loaded"
_MULTIPROCESSING = "Clearwater: multiprocessing children are not supported"
REFUSAL_ROWS = (
    SmokeRow("refuse-command", ("-c", "pass"), "", 2, _COMMAND),
    SmokeRow("refuse-module", ("-m", "http.server"), "", 2, _MODULE),
    SmokeRow("refuse-fork", ("--multiprocessing-fork",), "", 2, _MULTIPROCESSING),
    SmokeRow("refuse-tracker", ("--multiprocessing-resource-tracker",), "", 2, _MULTIPROCESSING),
    SmokeRow("refuse-r-command", ("-R", "-c", "pass"), "", 2, _COMMAND),
    SmokeRow("refuse-t-module", ("-t", "-m", "http.server"), "", 2, _MODULE),
    SmokeRow("refuse-cluster-command", ("-Rt", "-c", "pass"), "", 2, _COMMAND),
    SmokeRow(
        "refuse-hash-command",
        ("--check-hash-based-pycs", "always", "-c", "pass"),
        "",
        2,
        _COMMAND,
    ),
    SmokeRow(
        "refuse-hash-module",
        ("--check-hash-based-pycs", "never", "-m", "http.server"),
        "",
        2,
        _MODULE,
    ),
    SmokeRow(
        "refuse-module-fork",
        ("-m", "http.server", "--multiprocessing-fork"),
        "",
        2,
        _MULTIPROCESSING,
    ),
)
WORKER_ROWS = (
    SmokeRow(
        "worker-empty", ("--export-worker",), "", 2, "export worker: no request document on stdin"
    ),
    SmokeRow(
        "worker-malformed",
        ("--export-worker",),
        "{\n",
        2,
        "export worker: the request is not UTF-8 JSON",
    ),
)
_SAFE_ARGUMENTS = frozenset(row.arguments for row in (*REFUSAL_ROWS, *WORKER_ROWS))


@cache
def _load_sibling(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        f"_clearwater_smoke_{name}", Path(__file__).with_name(f"{name}.py")
    )
    if spec is None or spec.loader is None:
        raise SmokeError(f"inputs: cannot load {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _build_tool() -> ModuleType:
    return _load_sibling("build")


def _notices_tool() -> ModuleType:
    return _load_sibling("notices")


def _environment(root: Path) -> dict[str, str]:
    env = {key.upper(): value for key, value in os.environ.items()}
    # Clear inherited overrides that could load a user's pack/cache or Python modules.
    for key in tuple(env):
        if key.upper().startswith(("PYTHON", "XDG_")) or key.upper() in {
            "CUDA_CACHE_PATH",
            "CUPY_CACHE_DIR",
            "QT_PLUGIN_PATH",
            "QT_QPA_PLATFORM_PLUGIN_PATH",
        }:
            del env[key]
    for key, leaf in {
        "APPDATA": "appdata",
        "LOCALAPPDATA": "localappdata",
        "XDG_CONFIG_HOME": "xdg-config",
        "XDG_CACHE_HOME": "xdg-cache",
        "XDG_DATA_HOME": "xdg-data",
        "XDG_STATE_HOME": "xdg-state",
        "XDG_RUNTIME_DIR": "xdg-runtime",
        "HOME": "home",
        "USERPROFILE": "home",
        "TEMP": "temp",
        "TMP": "temp",
    }.items():
        path = root / leaf
        path.mkdir(parents=True, exist_ok=True)
        env[key] = str(path)
    system_root = env.get("SYSTEMROOT", "")
    if not system_root or not Path(system_root).is_absolute():
        raise SmokeError("environment: SystemRoot must name an absolute Windows directory")
    env["PATH"] = str(Path(system_root) / "System32")
    env["QT_QPA_PLATFORM"] = "offscreen"  # defense in depth; approved rows never reach Qt
    return env


def _live(processes: Sequence[psutil.Process]) -> list[psutil.Process]:
    alive = []
    for process in processes:
        try:
            if process.is_running() and process.status() != psutil.STATUS_ZOMBIE:
                alive.append(process)
        except psutil.NoSuchProcess:
            pass
    return alive


def _snapshot_children(pid: int, started: float, tracked: dict[int, psutil.Process]) -> None:
    # Unlike Process.children(), a PPID snapshot also finds direct children after
    # a fast parent has exited. Retain all observed ancestor IDs, not just live
    # ones, and reject older processes (PID reuse). Windows keeps inherited PPIDs.
    processes = list(psutil.process_iter(["pid", "ppid", "create_time"]))
    parents = {pid, *tracked}
    while True:
        found = False
        for child in processes:
            if child.pid in parents:
                continue
            info = child.info
            if (
                info["ppid"] in parents
                and info["create_time"] is not None
                and info["create_time"] >= started
            ):
                parents.add(child.pid)
                tracked[child.pid] = child
                found = True
        if not found:
            return


def _cleanup(
    process: subprocess.Popen[str],
    parent: psutil.Process | None,
    tracked: list[psutil.Process],
    name: str,
) -> None:
    if parent is not None:
        with contextlib.suppress(psutil.NoSuchProcess):
            tracked.extend(parent.children(recursive=True))
    # Kill descendants before the root; Process objects guard against PID reuse.
    for child in reversed(tracked):
        with contextlib.suppress(psutil.NoSuchProcess):
            child.kill()
    if process.poll() is None:
        process.kill()
    process.wait(timeout=5)
    _, alive = psutil.wait_procs(tracked, timeout=5)
    if _live(alive):
        raise SmokeError(f"{name}: process left after cleanup")


def _process(
    executable: Path,
    arguments: Sequence[str],
    *,
    stdin: str,
    root: Path,
    timeout: float,
    name: str,
) -> subprocess.CompletedProcess[str]:
    flags = 0
    if sys.platform == "win32":
        flags = subprocess.CREATE_NO_WINDOW
    tracked: dict[int, psutil.Process] = {}
    started = time.time()
    try:
        with subprocess.Popen(
            [str(executable), *arguments],
            cwd=executable.parent,
            env=_environment(root),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            creationflags=flags,
        ) as process:
            parent = None
            try:
                # A fast refusal may exit before the process snapshot.
                with contextlib.suppress(psutil.NoSuchProcess):
                    parent = psutil.Process(process.pid)
                deadline = time.monotonic() + timeout
                request: str | None = stdin
                while True:
                    try:
                        for child in [] if parent is None else parent.children(recursive=True):
                            tracked[child.pid] = child
                    except psutil.NoSuchProcess:
                        pass
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        raise SmokeError(f"{name}: timeout after {timeout:g} s")
                    try:
                        stdout, stderr = process.communicate(request, timeout=min(0.05, remaining))
                        break
                    except subprocess.TimeoutExpired:
                        request = None
                _snapshot_children(process.pid, started, tracked)
                if _live(list(tracked.values())):
                    raise SmokeError(f"{name}: process left after parent exit")
                return subprocess.CompletedProcess(process.args, process.returncode, stdout, stderr)
            finally:
                try:
                    _snapshot_children(process.pid, started, tracked)
                finally:
                    _cleanup(process, parent, list(tracked.values()), name)
    except (OSError, psutil.Error, subprocess.TimeoutExpired) as error:
        raise SmokeError(f"{name}: process supervision failed: {error}") from error


def run_row(executable: Path, row: SmokeRow, *, root: Path, timeout: float = 60) -> None:
    """Run one allowlisted Clearwater row under disposable roots, or fail by name.

    Args:
        executable: The onedir executable (possibly in the planted-failure copy).
        row: The exact refusal/worker contract; GUI-routed sets are refused.
        root: This row's disposable profile and temporary-file root.
        timeout: Positive bounded wait, at most 60 seconds.

    Raises:
        SmokeError: Arguments are unsafe, supervision fails or output differs.
    """
    if row.arguments not in _SAFE_ARGUMENTS:
        raise SmokeError(f"{row.name}: unsafe arguments; possible GUI route refused")
    if not 0 < timeout <= 60:
        raise SmokeError(f"{row.name}: timeout must be in (0, 60] seconds")
    done = _process(
        executable, row.arguments, stdin=row.stdin, root=root, timeout=timeout, name=row.name
    )
    if (row.status is None and done.returncode == 0) or (
        row.status is not None and done.returncode != row.status
    ):
        raise SmokeError(f"{row.name}: exit {done.returncode}; expected {row.status or 'non-zero'}")
    if done.stderr.splitlines() != [row.stderr]:
        raise SmokeError(f"{row.name}: stderr must be exactly one expected line: {done.stderr!r}")
    if done.stdout:
        raise SmokeError(f"{row.name}: unexpected stdout: {done.stdout!r}")
    print(f"{row.name}: PASS (exit {done.returncode}; one stderr line; process reaped)")


def _static_checks(folder: Path, executable: Path) -> None:
    build = _build_tool()
    try:
        bad = build.forbidden_paths(folder) + build.forbidden_entries(executable)
        if bad:
            raise ValueError("; ".join(bad))
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        raise SmokeError(f"bundle: {error}") from error
    print("bundle: PASS (folder and executable archives re-read)")
    try:
        sources = build.pack_sources()
        scan = build.scan_stdlib_imports(sources)
        if scan.unparsable:
            raise ValueError("; ".join(scan.unparsable))
        wanted = build.hidden_imports(scan)
        missing = build.missing_hidden_imports(executable, wanted)
        if missing:
            raise ValueError("; ".join(missing))
    except (OSError, ImportError, ValueError) as error:
        raise SmokeError(f"hidden-imports: {error}") from error
    print(f"hidden-imports: PASS ({len(wanted)} modules re-read from built folder)")
    try:
        tool = _notices_tool()
        path = folder / "THIRD_PARTY_NOTICES.md"
        if not path.is_file():
            raise ValueError("THIRD_PARTY_NOTICES.md is missing")
        plan = tool.plan_notices(folder)
        expected = tool.render_notices(plan)
        if path.read_bytes() != expected:
            raise ValueError("document differs from generator plan/expected row count")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        raise SmokeError(f"notices: {error}") from error
    print(f"notices: PASS ({len(plan.entries)} entries; {len(plan.rows)} component rows)")


def _ffmpeg_checks(folder: Path, run_root: Path, timeout: float) -> None:
    if not any((folder / name).exists() for name in ("ffmpeg.exe", "ffprobe.exe")):
        print("FFmpeg: SKIP (not bundled)")
        return
    lock = _build_tool().load_ffmpeg_lock()
    for tool in ("ffmpeg", "ffprobe"):
        name = f"{tool}-version"
        done = _process(
            folder / f"{tool}.exe",
            ["-version"],
            stdin="",
            root=run_root / name,
            timeout=timeout,
            name=name,
        )
        lines = done.stdout.splitlines()
        if done.returncode or done.stderr:
            raise SmokeError(f"{name}: exit {done.returncode} or unexpected stderr")
        if not lines or lines[0].split()[:3] != [tool, "version", lock["version"]]:
            raise SmokeError(f"{name}: version differs from lock")
        if [line for line in lines if line.startswith("configuration:")] != [
            lock["configure_line"]
        ]:
            raise SmokeError(f"{name}: configure line differs from lock")
        print(f"{name}: PASS ({lines[0]})")
    name = "ffmpeg-encoders"
    done = _process(
        folder / "ffmpeg.exe",
        ["-hide_banner", "-encoders"],
        stdin="",
        root=run_root / name,
        timeout=timeout,
        name=name,
    )
    encoders = {fields[1] for line in done.stdout.splitlines() if len(fields := line.split()) >= 2}
    if done.returncode or done.stderr or not {"hevc_nvenc", "libx265"} <= encoders:
        raise SmokeError(f"{name}: bundled binary must offer hevc_nvenc and libx265 without errors")
    print(f"{name}: PASS (hevc_nvenc; libx265)")


def _run_windows_smoke(folder: Path, *, out: Path, timeout: float) -> None:
    """Verify a Windows onedir folder headlessly, preserving its shipping bytes.

    Args:
        folder: The release folder or its parent wrapper.
        out: Output root; fresh evidence/profile/copy roots go under ``smoke/``.
        timeout: Per-process bound in seconds, positive and no greater than 60.

    Raises:
        SmokeError: A named static or process row fails; no GUI row is launched.
        OSError: A required artifact/input cannot be read or evidence written.
    """
    if not 0 < timeout <= 60:
        raise SmokeError("inputs: timeout must be in (0, 60] seconds")
    build = _build_tool()
    executable = cast(Path, build.find_executable(folder.resolve()))
    folder = executable.parent
    if not (folder / "_internal").is_dir():
        raise SmokeError("inputs: smoke requires onedir with _internal")
    smoke_root = out.resolve() / "smoke"
    if smoke_root.is_relative_to(folder) or folder.is_relative_to(smoke_root):
        raise SmokeError("inputs: smoke output and shipping folder must be disjoint")
    _static_checks(folder, executable)
    smoke_root.mkdir(parents=True, exist_ok=True)
    run_root = Path(tempfile.mkdtemp(prefix="run-", dir=smoke_root))
    print(f"smoke evidence: {run_root}")
    for row in (*REFUSAL_ROWS, *WORKER_ROWS):
        run_row(executable, row, root=run_root / row.name, timeout=timeout)

    # The native SciPy callback is required on the worker composition-import path,
    # but is not needed by config.paths/log (which need NumPy). Removing NumPy
    # would trigger the accepted 'log unavailable' limit rather than prove a log.
    name = "planted-exception"
    targets = sorted((folder / "_internal/scipy/_lib").glob("_ccallback_c*.pyd"))
    if len(targets) != 1:
        raise SmokeError(f"{name}: expected one required scipy._lib._ccallback_c native import")
    copy = run_root / "planted/Clearwater"
    shutil.copytree(folder, copy, symlinks=True)
    (copy / targets[0].relative_to(folder)).unlink()
    root = run_root / name
    log = root / "appdata/Clearwater/logs/clearwater.log"
    line = "Clearwater: unexpected error; see log: " + str(log).encode(
        "ascii", "backslashreplace"
    ).decode("ascii")
    run_row(
        copy / executable.name,
        SmokeRow(name, ("--export-worker",), "", None, line),
        root=root,
        timeout=timeout,
    )
    if not log.is_file():
        raise SmokeError(f"{name}: product log was not written under redirected root")
    text = log.read_text(encoding="utf-8")
    if (
        text.count("Unhandled exception") != 1
        or "Traceback (most recent call last):" not in text
        or "_ccallback_c" not in text
    ):
        raise SmokeError(f"{name}: expected one traceback for the unavailable worker import")
    print(f"{name}-log: PASS ({log})")
    _ffmpeg_checks(folder, run_root, timeout)
    print(f"total: {build.tree_size(folder)} bytes under {folder}")
    print("largest entries:")
    for path, size in build.size_by_top_level(executable)[:10]:
        print(f"  {size:12d} bytes  {path}")
    print("smoke: PASS (headless process checks; seat UIA watch supplies window evidence)")


def run_smoke(folder: Path, *, out: Path, timeout: float = 60) -> None:
    """Check a Windows onedir artifact with isolated, bounded headless rows.

    Args:
        folder: The release folder or its parent wrapper.
        out: Evidence root; disposable folders are created under ``smoke/``.
        timeout: Per-process bound, positive and no greater than 60 seconds.

    Raises:
        SmokeError: A check fails, or the host is not Windows.
        OSError: Artifact/input reads or evidence writes fail.
    """
    if sys.platform == "win32":
        _run_windows_smoke(folder, out=out, timeout=timeout)
    else:
        raise SmokeError("platform: smoke requires the Windows onedir artifact")
