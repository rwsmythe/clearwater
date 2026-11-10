"""Run bounded, headless onedir / ``.app`` checks without entering the GUI branch.

Only the commissioned refusal/worker argument sets may launch Clearwater. Each
row has fresh disposable profile roots and a system-only PATH (System32 on
Windows; ``/usr/bin:/bin`` on macOS, WP6.5). A planted
import failure uses a separate copy; the shipping folder is only read. Process
supervision is not window evidence: the seat supplies the independent UIA watch.
"""

from __future__ import annotations

import contextlib
import ctypes
import importlib.util
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from collections.abc import Callable, Sequence
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import BinaryIO, NamedTuple, Protocol, cast

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
    if sys.platform == "win32":
        system_root = env.get("SYSTEMROOT", "")
        if not system_root or not Path(system_root).is_absolute():
            raise SmokeError("environment: SystemRoot must name an absolute Windows directory")
        env["PATH"] = str(Path(system_root) / "System32")
    else:
        # macOS (WP6.5): the temporary root is TMPDIR; PATH holds the system tools only.
        env["TMPDIR"] = env["TEMP"]
        env["PATH"] = os.pathsep.join(_POSIX_PATH)
    env["QT_QPA_PLATFORM"] = "offscreen"  # defense in depth; approved rows never reach Qt
    return env


_POSIX_PATH = ("/usr/bin", "/bin")
"""The macOS smoke rows' PATH: system tools only, no Homebrew."""

_GROUP_CLEANUP_SECONDS = 5.0
"""How long the macOS cleanup waits for a killed process group to empty."""


class _KillGroup(Protocol):
    def __call__(self, pgid: int, signal: int, /) -> None: ...


class GroupMember(NamedTuple):
    """One process in a row's process group, as the census lists it (WP6.5 run 2).

    Attributes:
        pid: The process id.
        stat: Its ``ps`` state; a first letter ``Z`` is a zombie (dead, not yet reaped).
        comm: Its command name.
    """

    pid: int
    stat: str
    comm: str


_PS = "/bin/ps"
"""The macOS ``ps`` (absolute: the smoke's PATH is not consulted)."""


def _group_census(
    pgid: int, run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run
) -> list[GroupMember]:
    """List the members of process group ``pgid`` with their state (macOS ``ps``).

    ``ps -A -o pid=,pgid=,stat=,comm=`` lists every process; the rows of ``pgid`` are kept.
    A zombie stays listed (stat ``Z...``) until its parent reaps it.

    Args:
        pgid: The process group.
        run: ``subprocess.run`` (a stub in tests).

    Returns:
        The group's members, zombies included, in ``ps`` order.

    Raises:
        SmokeError: ``ps`` failed or printed a line that is not ``pid pgid stat [comm]``.
    """
    try:
        listed = run(
            [_PS, "-A", "-o", "pid=,pgid=,stat=,comm="],
            capture_output=True,
            text=True,
            errors="replace",
            timeout=10,
            check=False,
        )
    except (OSError, subprocess.SubprocessError) as error:
        raise SmokeError(f"group census: {_PS} failed: {error}") from error
    if listed.returncode != 0:
        raise SmokeError(f"group census: {_PS} exited {listed.returncode}: {listed.stderr!r}")
    members: list[GroupMember] = []
    for line in listed.stdout.splitlines():
        if not line.strip():
            continue
        fields = line.split(None, 3)
        try:
            pid, group = int(fields[0]), int(fields[1])
            stat = fields[2]
        except (IndexError, ValueError):
            raise SmokeError(f"group census: unreadable {_PS} line {line!r}") from None
        if group == pgid:
            members.append(GroupMember(pid, stat, fields[3].strip() if len(fields) > 3 else ""))
    return members


def _live(members: Sequence[GroupMember]) -> list[GroupMember]:
    """The members that are not zombies: containment means no LIVE process (WP6.5 run 2)."""
    return [member for member in members if not member.stat.startswith("Z")]


def _listing(members: Sequence[GroupMember]) -> str:
    """The census for a message: ``pid stat comm`` per member, or ``no member listed``."""
    if not members:
        return "no member listed"
    return ", ".join(f"pid {m.pid} {m.stat} {m.comm}".rstrip() for m in members)


def _group_contained_process(
    executable: Path,
    arguments: Sequence[str],
    *,
    stdin: str,
    root: Path,
    timeout: float,
    name: str,
    killpg: _KillGroup,
    kill_signal: int,
    own_group: int,
    census: Callable[[int], list[GroupMember]],
    popen: Callable[..., subprocess.Popen[bytes]] = subprocess.Popen,
) -> subprocess.CompletedProcess[str]:
    """Run one row in its own session and process group; census and kill the group.

    The macOS containment (AD-37; WP6.5): ``start_new_session=True`` makes the root a
    session and group leader (pgid = its pid) before it executes, so every descendant that
    does not start its own session stays in that group. After the root exits and its pipes
    reach EOF, the group is probed with ``killpg(pgid, 0)`` and listed by ``census``: a group
    with a LIVE member at the deadline has SURVIVORS and the row fails. Cleanup always sends
    ``killpg(pgid, SIGKILL)`` and waits a bounded time for the group to hold no live member.
    The group is never this process's own (checked before any signal).

    The probe's outcomes (WP6.5 run 2, CHARC's ruling): ``ProcessLookupError`` = an empty
    group; ``PermissionError`` (EPERM; read as macOS answering so for a group of zombies, a
    hypothesis until the runner's census confirms it) = the census decides: no live member is
    contained (the listing printed), a live member is the named failure "has a member this
    process may not signal"; any other exception propagates. A zombie is not a survivor: only
    members whose state is not ``Z`` count. Every SURVIVORS / EPERM message carries the
    listing.

    Args:
        executable: The program to run.
        arguments: Its arguments.
        stdin: Text written to its standard input, then closed.
        root: The row's disposable profile and temporary root.
        timeout: The bound for the root and its pipes, in seconds.
        name: The row name for messages.
        killpg: ``os.killpg`` (a stub in tests).
        kill_signal: ``signal.SIGKILL``.
        own_group: This process's group (``os.getpgrp()``), never signalled.
        census: Lists a group's members with their state (``_group_census``; a stub in
            tests).
        popen: ``subprocess.Popen`` (a stub in tests).

    Returns:
        The finished row (exit status and decoded output).

    Raises:
        SmokeError: Timeout, survivors, a group that will not die, a live member this
            process may not signal, or an unsafe group.
        OSError: The probe failed in a way not named above (propagated, never a pass).
    """
    env = _environment(root)
    argv = _command(executable, arguments, env)
    process: subprocess.Popen[bytes] | None = None
    pgid = 0
    members: list[GroupMember] = []

    def group_alive() -> bool:
        """True while the group holds a LIVE member; ``members`` keeps the last listing."""
        nonlocal members
        try:
            killpg(pgid, 0)
        except ProcessLookupError:
            members = []
            return False
        except PermissionError as error:
            members = census(pgid)
            if _live(members):
                raise SmokeError(
                    f"{name}: process group {pgid} has a member this process may not signal "
                    f"(EPERM; members: {_listing(members)})"
                ) from error
            print(
                f"{name}: process group {pgid} answers EPERM with no live member "
                f"(members: {_listing(members)}): contained",
                flush=True,
            )
            return False
        members = census(pgid)
        return bool(_live(members))

    try:
        process = popen(
            argv,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            cwd=str(executable.parent),
            start_new_session=True,
        )
        pgid = process.pid
        if pgid <= 1 or pgid == own_group:
            raise SmokeError(f"{name}: unsafe process group {pgid} (own group {own_group})")
        deadline = time.monotonic() + timeout
        try:
            stdout, stderr = process.communicate(stdin.encode("utf-8"), timeout=timeout)
        except subprocess.TimeoutExpired:
            if process.poll() is None:
                raise SmokeError(
                    f"{name}: timeout after {timeout:g} s (root still alive)"
                ) from None
            if group_alive():
                raise SmokeError(
                    f"{name}: SURVIVORS (process group {pgid} holds the pipes after root exit; "
                    f"members: {_listing(members)})"
                ) from None
            raise SmokeError(f"{name}: timeout waiting for pipe EOF after root exit") from None
        while group_alive():
            if time.monotonic() >= deadline:
                raise SmokeError(
                    f"{name}: SURVIVORS (process left in group {pgid}; "
                    f"members: {_listing(members)})"
                )
            time.sleep(0.01)
        print(f"{name}: group census PASS (0 live processes; new session; group {pgid})")
        return subprocess.CompletedProcess(
            argv,
            process.returncode,
            stdout.decode("utf-8", "replace"),
            stderr.decode("utf-8", "replace"),
        )
    except (SmokeError, OSError) as error:
        message = str(error).encode("ascii", "backslashreplace").decode("ascii")
        print(f"{name}: FAIL ({message})", flush=True)
        raise
    finally:
        if process is not None and pgid > 1 and pgid != own_group:
            cleanup_deadline = time.monotonic() + _GROUP_CLEANUP_SECONDS
            with contextlib.suppress(ProcessLookupError):
                killpg(pgid, kill_signal)
            try:
                process.wait(max(0.0, cleanup_deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                raise SmokeError(f"{name}: root did not terminate after killpg") from None
            while group_alive():
                if time.monotonic() >= cleanup_deadline:
                    raise SmokeError(
                        f"{name}: process group {pgid} did not terminate after killpg "
                        f"(members: {_listing(members)})"
                    )
                time.sleep(0.01)
            for stream in (process.stdin, process.stdout, process.stderr):
                if stream is not None:
                    stream.close()


def _command(executable: Path, arguments: Sequence[str], env: dict[str, str]) -> list[str]:
    # The native loader boundary is replaced by Python stubs in tool tests only.
    return [str(executable), *arguments]


if sys.platform == "win32":
    import msvcrt
    from ctypes import wintypes as w

    class _BasicLimit(ctypes.Structure):
        _fields_ = [
            ("process_time", ctypes.c_longlong),
            ("job_time", ctypes.c_longlong),
            ("flags", w.DWORD),
            ("minimum_working_set", ctypes.c_size_t),
            ("maximum_working_set", ctypes.c_size_t),
            ("active_process_limit", w.DWORD),
            ("affinity", ctypes.c_size_t),
            ("priority_class", w.DWORD),
            ("scheduling_class", w.DWORD),
        ]

    class _IoCounters(ctypes.Structure):
        _fields_ = [
            (name, ctypes.c_ulonglong)
            for name in (
                "read_operations",
                "write_operations",
                "other_operations",
                "read_bytes",
                "write_bytes",
                "other_bytes",
            )
        ]

    class _ExtendedLimit(ctypes.Structure):
        _fields_ = [
            ("basic", _BasicLimit),
            ("io", _IoCounters),
            ("process_memory", ctypes.c_size_t),
            ("job_memory", ctypes.c_size_t),
            ("peak_process_memory", ctypes.c_size_t),
            ("peak_job_memory", ctypes.c_size_t),
        ]

    class _SecurityAttributes(ctypes.Structure):
        _fields_ = [("length", w.DWORD), ("descriptor", ctypes.c_void_p), ("inherit", w.BOOL)]

    class _StartupInfo(ctypes.Structure):
        _fields_ = [
            ("cb", w.DWORD),
            ("reserved", w.LPWSTR),
            ("desktop", w.LPWSTR),
            ("title", w.LPWSTR),
            ("x", w.DWORD),
            ("y", w.DWORD),
            ("width", w.DWORD),
            ("height", w.DWORD),
            ("x_chars", w.DWORD),
            ("y_chars", w.DWORD),
            ("fill", w.DWORD),
            ("flags", w.DWORD),
            ("show", w.WORD),
            ("reserved_size", w.WORD),
            ("reserved_bytes", ctypes.c_void_p),
            ("stdin", w.HANDLE),
            ("stdout", w.HANDLE),
            ("stderr", w.HANDLE),
        ]

    class _StartupInfoEx(ctypes.Structure):
        _fields_ = [("startup", _StartupInfo), ("attributes", ctypes.c_void_p)]

    class _ProcessInfo(ctypes.Structure):
        _fields_ = [("process", w.HANDLE), ("thread", w.HANDLE), ("pid", w.DWORD), ("tid", w.DWORD)]

    @cache
    def _kernel32() -> ctypes.WinDLL:
        api = ctypes.WinDLL("kernel32", use_last_error=True)
        signatures = {
            "CreateJobObjectW": ([ctypes.c_void_p, w.LPCWSTR], w.HANDLE),
            "SetInformationJobObject": ([w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD], w.BOOL),
            "QueryInformationJobObject": (
                [w.HANDLE, ctypes.c_int, ctypes.c_void_p, w.DWORD, ctypes.c_void_p],
                w.BOOL,
            ),
            "CloseHandle": ([w.HANDLE], w.BOOL),
            "CreatePipe": (
                [
                    ctypes.POINTER(w.HANDLE),
                    ctypes.POINTER(w.HANDLE),
                    ctypes.POINTER(_SecurityAttributes),
                    w.DWORD,
                ],
                w.BOOL,
            ),
            "SetHandleInformation": ([w.HANDLE, w.DWORD, w.DWORD], w.BOOL),
            "InitializeProcThreadAttributeList": (
                [ctypes.c_void_p, w.DWORD, w.DWORD, ctypes.POINTER(ctypes.c_size_t)],
                w.BOOL,
            ),
            "UpdateProcThreadAttribute": (
                [
                    ctypes.c_void_p,
                    w.DWORD,
                    ctypes.c_size_t,
                    ctypes.c_void_p,
                    ctypes.c_size_t,
                    ctypes.c_void_p,
                    ctypes.c_void_p,
                ],
                w.BOOL,
            ),
            "DeleteProcThreadAttributeList": ([ctypes.c_void_p], None),
            "CreateProcessW": (
                [
                    w.LPCWSTR,
                    w.LPWSTR,
                    ctypes.c_void_p,
                    ctypes.c_void_p,
                    w.BOOL,
                    w.DWORD,
                    ctypes.c_void_p,
                    w.LPCWSTR,
                    ctypes.c_void_p,
                    ctypes.POINTER(_ProcessInfo),
                ],
                w.BOOL,
            ),
            "IsProcessInJob": ([w.HANDLE, w.HANDLE, ctypes.POINTER(w.BOOL)], w.BOOL),
            "ResumeThread": ([w.HANDLE], w.DWORD),
            "WaitForSingleObject": ([w.HANDLE, w.DWORD], w.DWORD),
            "GetExitCodeProcess": ([w.HANDLE, ctypes.POINTER(w.DWORD)], w.BOOL),
            "OpenProcess": ([w.DWORD, w.BOOL, w.DWORD], w.HANDLE),
            "QueryFullProcessImageNameW": (
                [w.HANDLE, w.DWORD, w.LPWSTR, ctypes.POINTER(w.DWORD)],
                w.BOOL,
            ),
        }
        for name, (arguments, result) in signatures.items():
            function = getattr(api, name)
            function.argtypes = arguments
            function.restype = result
        return api

    def _win_error(name: str, operation: str) -> SmokeError:
        code = ctypes.get_last_error()
        return SmokeError(
            f"{name}: {operation}: WinError {code}: {ctypes.FormatError(code).strip()}"
        )

    def _job_pids(api: ctypes.WinDLL, job: int, name: str) -> list[int]:
        capacity = 32
        while capacity <= 100_000:
            data = ctypes.create_string_buffer(8 + capacity * ctypes.sizeof(ctypes.c_size_t))
            result = api.QueryInformationJobObject(job, 3, data, len(data), None)
            assigned = ctypes.c_uint32.from_buffer(data).value
            listed = ctypes.c_uint32.from_buffer(data, 4).value
            if result and assigned <= listed <= capacity:
                pids = (ctypes.c_size_t * listed).from_buffer(data, 8)
                return list(pids)
            if not result and ctypes.get_last_error() != 234:  # ERROR_MORE_DATA
                raise _win_error(name, "QueryInformationJobObject(process list)")
            capacity = max(capacity * 2, assigned + 16)
        raise SmokeError(f"{name}: job process census exceeds 100000 entries")

    def _image(api: ctypes.WinDLL, pid: int) -> str:
        handle = api.OpenProcess(0x1000, False, pid)  # QUERY_LIMITED_INFORMATION
        if handle:
            try:
                size = w.DWORD(32768)
                text = ctypes.create_unicode_buffer(size.value)
                if api.QueryFullProcessImageNameW(handle, 0, text, ctypes.byref(size)):
                    return text.value
            finally:
                api.CloseHandle(handle)
        try:
            return cast(str, psutil.Process(pid).name())
        except psutil.Error:
            return "<image unavailable>"

    def _contained_process(
        executable: Path,
        arguments: Sequence[str],
        *,
        stdin: str,
        root: Path,
        timeout: float,
        name: str,
    ) -> subprocess.CompletedProcess[str]:
        """Create a suspended root atomically inside a non-breakaway, kill-on-close job.

        PROC_THREAD_ATTRIBUTE_JOB_LIST (Windows 10+) makes assignment part of
        CreateProcessW: failure leaves no unassigned suspended root to terminate.
        The root's membership is checked before its retained thread is resumed.
        Readers/writer are daemon threads; census/waits remain bounded even when
        an orphan holds a pipe. Only closing this job kills its process tree.
        """
        api = _kernel32()
        job = 0
        handles: set[int] = set()
        streams: list[BinaryIO] = []
        workers: list[threading.Thread] = []
        info = _ProcessInfo()
        attributes_ready = False
        attribute_memory = None
        output = [b"", b""]
        io_errors: list[str] = []
        argv: list[str] = []

        def check(result: object, operation: str) -> None:
            if not result:
                raise _win_error(name, operation)

        def close_handle(handle: int) -> None:
            check(api.CloseHandle(handle), "CloseHandle")
            handles.discard(handle)

        def pipe() -> tuple[int, int]:
            read, write = w.HANDLE(), w.HANDLE()
            security = _SecurityAttributes(ctypes.sizeof(_SecurityAttributes), None, True)
            check(
                api.CreatePipe(ctypes.byref(read), ctypes.byref(write), ctypes.byref(security), 0),
                "CreatePipe",
            )
            assert read.value is not None and write.value is not None
            handles.update((read.value, write.value))
            return read.value, write.value

        def stream_for(handle: int, mode: str) -> BinaryIO:
            access = os.O_WRONLY if mode == "wb" else os.O_RDONLY
            descriptor = msvcrt.open_osfhandle(handle, os.O_BINARY | access)
            handles.discard(handle)  # the descriptor now owns the Win32 handle
            stream = cast(BinaryIO, os.fdopen(descriptor, mode, buffering=0))
            streams.append(stream)
            return stream

        def read_pipe(stream: BinaryIO, index: int) -> None:
            try:
                output[index] = stream.read()
            except OSError as error:
                io_errors.append(str(error))

        def write_pipe(stream: BinaryIO) -> None:
            try:
                stream.write(stdin.encode("utf-8"))
            except BrokenPipeError:
                pass  # refusal may exit without consuming input, as with communicate()
            except OSError as error:
                io_errors.append(str(error))
            finally:
                stream.close()  # request EOF is part of the worker protocol

        try:
            env = _environment(root)
            argv = _command(executable, arguments, env)
            job = api.CreateJobObjectW(None, None)
            check(job, "CreateJobObjectW")
            limits = _ExtendedLimit()
            limits.basic.flags = 0x2000  # KILL_ON_JOB_CLOSE; both BREAKAWAY flags absent
            check(
                api.SetInformationJobObject(job, 9, ctypes.byref(limits), ctypes.sizeof(limits)),
                "SetInformationJobObject(limits)",
            )
            child_in, parent_in = pipe()
            parent_out, child_out = pipe()
            parent_err, child_err = pipe()
            for handle in (parent_in, parent_out, parent_err):
                check(api.SetHandleInformation(handle, 1, 0), "SetHandleInformation(no inherit)")
            size = ctypes.c_size_t()
            api.InitializeProcThreadAttributeList(None, 2, 0, ctypes.byref(size))
            check(size.value, "InitializeProcThreadAttributeList(size)")
            attribute_memory = ctypes.create_string_buffer(size.value)
            check(
                api.InitializeProcThreadAttributeList(attribute_memory, 2, 0, ctypes.byref(size)),
                "InitializeProcThreadAttributeList",
            )
            attributes_ready = True
            job_list = (w.HANDLE * 1)(job)
            check(
                api.UpdateProcThreadAttribute(
                    attribute_memory, 0, 0x2000D, job_list, ctypes.sizeof(job_list), None, None
                ),
                "UpdateProcThreadAttribute(atomic job assignment)",
            )
            handle_list = (w.HANDLE * 3)(child_in, child_out, child_err)
            check(
                api.UpdateProcThreadAttribute(
                    attribute_memory,
                    0,
                    0x20002,
                    handle_list,
                    ctypes.sizeof(handle_list),
                    None,
                    None,
                ),
                "UpdateProcThreadAttribute(pipe handles)",
            )
            startup = _StartupInfoEx()
            startup.startup.cb = ctypes.sizeof(startup)
            startup.startup.flags = 0x100  # STARTF_USESTDHANDLES
            startup.startup.stdin, startup.startup.stdout, startup.startup.stderr = (
                child_in,
                child_out,
                child_err,
            )
            startup.attributes = ctypes.addressof(attribute_memory)
            command_line = ctypes.create_unicode_buffer(subprocess.list2cmdline(argv))
            environment = ctypes.create_unicode_buffer(
                "\0".join(f"{key}={value}" for key, value in sorted(env.items())) + "\0\0"
            )
            # SUSPENDED | NO_WINDOW | UNICODE_ENVIRONMENT | EXTENDED_STARTUPINFO_PRESENT.
            check(
                api.CreateProcessW(
                    argv[0],
                    command_line,
                    None,
                    None,
                    True,
                    0x08080404,
                    environment,
                    str(executable.parent),
                    ctypes.byref(startup),
                    ctypes.byref(info),
                ),
                "CreateProcessW(atomic job assignment)",
            )
            handles.update((info.process, info.thread))
            for handle in (child_in, child_out, child_err):
                close_handle(handle)
            inside = w.BOOL()
            check(
                api.IsProcessInJob(info.process, job, ctypes.byref(inside)),
                "IsProcessInJob(before resume)",
            )
            if not inside.value:
                raise SmokeError(f"{name}: suspended root is not in its row job")
            write_stream = stream_for(parent_in, "wb")
            read_streams = [stream_for(parent_out, "rb"), stream_for(parent_err, "rb")]
            workers = [
                threading.Thread(target=read_pipe, args=(stream, index), daemon=True)
                for index, stream in enumerate(read_streams)
            ]
            workers.append(threading.Thread(target=write_pipe, args=(write_stream,), daemon=True))
            for worker in workers:
                worker.start()
            deadline = time.monotonic() + timeout
            previous = api.ResumeThread(info.thread)
            if previous == 0xFFFFFFFF:
                raise _win_error(name, "ResumeThread")
            if previous != 1:
                raise SmokeError(f"{name}: unexpected initial thread suspend count {previous}")
            while True:
                wait = api.WaitForSingleObject(info.process, 0)
                if wait == 0xFFFFFFFF:
                    raise _win_error(name, "WaitForSingleObject(root)")
                pids = _job_pids(api, job, name) if wait == 0 else []
                if wait == 0 and not pids and not any(worker.is_alive() for worker in workers):
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    if wait != 0:
                        raise SmokeError(f"{name}: timeout after {timeout:g} s (root still alive)")
                    if pids:
                        census = "; ".join(f"pid={pid} image={_image(api, pid)}" for pid in pids)
                        raise SmokeError(f"{name}: SURVIVORS (process left in job): {census}")
                    raise SmokeError(f"{name}: timeout waiting for pipe EOF after root exit")
                time.sleep(min(0.01, remaining))
            status = w.DWORD()
            check(api.GetExitCodeProcess(info.process, ctypes.byref(status)), "GetExitCodeProcess")
            if io_errors:
                raise SmokeError(f"{name}: pipe IO failed: {'; '.join(io_errors)}")
            print(
                f"{name}: job census PASS (0 processes; assigned before resume; breakaway denied)"
            )
            return subprocess.CompletedProcess(
                argv,
                status.value,
                output[0].decode("utf-8", "replace"),
                output[1].decode("utf-8", "replace"),
            )
        except (SmokeError, OSError) as error:
            # The survivor census/error is recorded while the job still owns it.
            message = str(error).encode("ascii", "backslashreplace").decode("ascii")
            print(f"{name}: FAIL ({message})", flush=True)
            raise
        finally:
            waiting: list[int] = []
            try:
                if job:
                    for pid in _job_pids(api, job, name):
                        handle = api.OpenProcess(
                            0x101000, False, pid
                        )  # SYNCHRONIZE | QUERY_LIMITED
                        if handle:
                            waiting.append(handle)
            finally:
                if job:
                    # No TerminateProcess / PID kill path: close kills this entire job.
                    check(api.CloseHandle(job), "CloseHandle(job; kill tree)")
                cleanup_deadline = time.monotonic() + 5
                try:
                    for handle in ([info.process] if info.process else []) + waiting:
                        milliseconds = max(0, int((cleanup_deadline - time.monotonic()) * 1000))
                        if api.WaitForSingleObject(handle, milliseconds) != 0:
                            raise SmokeError(
                                f"{name}: job process did not terminate after job close"
                            )
                    for worker in workers:
                        worker.join(max(0, cleanup_deadline - time.monotonic()))
                    if any(worker.is_alive() for worker in workers):
                        raise SmokeError(f"{name}: pipe thread did not end after job close")
                finally:
                    for handle in waiting:
                        api.CloseHandle(handle)
                    for stream in streams:
                        if not any(worker.is_alive() for worker in workers):
                            stream.close()
                    for handle in handles:
                        api.CloseHandle(handle)
                    if attributes_ready:
                        api.DeleteProcThreadAttributeList(attribute_memory)

elif sys.platform == "darwin":
    import signal

    def _contained_process(
        executable: Path,
        arguments: Sequence[str],
        *,
        stdin: str,
        root: Path,
        timeout: float,
        name: str,
    ) -> subprocess.CompletedProcess[str]:
        """Contain a row in its own process group (:func:`_group_contained_process`)."""
        return _group_contained_process(
            executable,
            arguments,
            stdin=stdin,
            root=root,
            timeout=timeout,
            name=name,
            killpg=os.killpg,
            kill_signal=signal.SIGKILL,
            own_group=os.getpgrp(),
            census=_group_census,
        )

else:

    def _contained_process(
        executable: Path,
        arguments: Sequence[str],
        *,
        stdin: str,
        root: Path,
        timeout: float,
        name: str,
    ) -> subprocess.CompletedProcess[str]:
        """Refuse containment off Windows and macOS: Linux is not a supported build host."""
        raise SmokeError(
            f"{name}: process containment is proved on Windows and macOS only "
            "(Linux is not a supported build host)"
        )


def _process(
    executable: Path,
    arguments: Sequence[str],
    *,
    stdin: str,
    root: Path,
    timeout: float,
    name: str,
) -> subprocess.CompletedProcess[str]:
    try:
        return _contained_process(
            executable, arguments, stdin=stdin, root=root, timeout=timeout, name=name
        )
    except OSError as error:
        raise SmokeError(f"{name}: native containment failed: {error}") from error


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


_SMOKE_ENCODERS = {
    "win32": ("hevc_nvenc", "libx265"),
    "darwin": ("hevc_videotoolbox", "libx265"),
}
"""The -encoders row's expected names: ``io/video/capability.py``'s roster per platform."""


def _ffmpeg_checks(folder: Path, run_root: Path, timeout: float) -> None:
    suffix = ".exe" if sys.platform == "win32" else ""
    if sys.platform == "win32":
        if not any((folder / name).exists() for name in ("ffmpeg.exe", "ffprobe.exe")):
            print("FFmpeg: SKIP (not bundled)")
            return
        lock = _build_tool().load_ffmpeg_lock()
    else:
        # macOS (WP6.5): the smoke runs only on a release bundle, so FFmpeg is required.
        tools = [folder / name for name in ("ffmpeg", "ffprobe")]
        if any(not path.is_file() or path.is_symlink() for path in tools):
            raise SmokeError(
                "FFmpeg: the macOS bundle must carry ffmpeg and ffprobe in Contents/MacOS"
            )
        lock = _build_tool().load_macos_ffmpeg_lock()
    for tool in ("ffmpeg", "ffprobe"):
        name = f"{tool}-version"
        done = _process(
            folder / f"{tool}{suffix}",
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
        folder / f"ffmpeg{suffix}",
        ["-hide_banner", "-encoders"],
        stdin="",
        root=run_root / name,
        timeout=timeout,
        name=name,
    )
    encoders = {fields[1] for line in done.stdout.splitlines() if len(fields := line.split()) >= 2}
    hardware, software = _SMOKE_ENCODERS[sys.platform]
    if done.returncode or done.stderr or not {hardware, software} <= encoders:
        raise SmokeError(
            f"{name}: bundled binary must offer {hardware} and {software} without errors"
        )
    print(f"{name}: PASS ({hardware}; {software})")


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


def _macos_log_file(root: Path) -> Path:
    """The product's macOS log under a row's redirected HOME (``config.paths``, darwin)."""
    library = root / "home" / "Library"
    return library / "Application Support" / "Clearwater" / "logs" / "clearwater.log"


def _macos_static_checks(bundle: Path, executable: Path) -> None:
    """The Windows static rows on the ``.app``.

    No GPU pack is scanned (AD-33: ``build()`` scans none on darwin) and the notices are
    read from ``Contents/Resources`` (``Contents/MacOS`` holds only code under the seal;
    WP6.5 part 3 generates them there).
    """
    build = _build_tool()
    try:
        bad = build.forbidden_paths(bundle) + build.forbidden_entries(executable)
        if bad:
            raise ValueError("; ".join(bad))
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        raise SmokeError(f"bundle: {error}") from error
    print("bundle: PASS (bundle and executable archives re-read)")
    try:
        wanted = build.hidden_imports(build.scan_stdlib_imports([]))
        missing = build.missing_hidden_imports(executable, wanted)
        if missing:
            raise ValueError("; ".join(missing))
    except (OSError, ImportError, ValueError) as error:
        raise SmokeError(f"hidden-imports: {error}") from error
    print(f"hidden-imports: PASS ({len(wanted)} modules re-read from built bundle)")
    try:
        tool = _notices_tool()
        path = bundle / "Contents" / "Resources" / "THIRD_PARTY_NOTICES.md"
        if not path.is_file() or path.is_symlink():
            raise ValueError("THIRD_PARTY_NOTICES.md is missing from Contents/Resources")
        plan = tool.plan_notices(executable.parent)
        if path.read_bytes() != tool.render_notices(plan):
            raise ValueError("document differs from generator plan/expected row count")
    except (OSError, ValueError, KeyError, zipfile.BadZipFile) as error:
        raise SmokeError(f"notices: {error}") from error
    print(f"notices: PASS ({len(plan.entries)} entries; {len(plan.rows)} component rows)")


def _run_macos_smoke(folder: Path, *, out: Path, timeout: float) -> None:
    """Verify a macOS ``Clearwater.app`` headlessly, preserving its shipping bytes (WP6.5).

    The Windows rows in the same order, each contained in its own process group
    (:func:`_group_contained_process`); the planted exception removes the ``.so``
    analogue of ``_ccallback_c*.pyd`` from a COPY of the bundle and expects the product
    log under the row's redirected HOME; the FFmpeg rows are required and expect the
    macOS encoder roster.

    Args:
        folder: The release folder holding ``Clearwater.app``, or its ``Contents/MacOS``.
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
    bundle = folder.parent.parent
    if (
        folder.name != "MacOS"
        or folder.parent.name != "Contents"
        or bundle.suffix != ".app"
        or not (bundle / "Contents" / "Frameworks").is_dir()
    ):
        raise SmokeError(
            "inputs: the macOS smoke requires the Clearwater.app bundle "
            "(Contents/MacOS and Contents/Frameworks)"
        )
    smoke_root = out.resolve() / "smoke"
    if smoke_root.is_relative_to(bundle) or bundle.is_relative_to(smoke_root):
        raise SmokeError("inputs: smoke output and shipping bundle must be disjoint")
    _macos_static_checks(bundle, executable)
    smoke_root.mkdir(parents=True, exist_ok=True)
    run_root = Path(tempfile.mkdtemp(prefix="run-", dir=smoke_root))
    print(f"smoke evidence: {run_root}")
    for row in (*REFUSAL_ROWS, *WORKER_ROWS):
        run_row(executable, row, root=run_root / row.name, timeout=timeout)

    # As on Windows: the native SciPy callback is required on the worker's composition
    # import path; on macOS it is a regular .so in Contents/Frameworks.
    name = "planted-exception"
    targets = sorted((bundle / "Contents/Frameworks/scipy/_lib").glob("_ccallback_c*.so"))
    if (
        len(targets) != 1
        or targets[0].is_symlink()
        or not targets[0].resolve().is_relative_to(bundle.resolve())
    ):
        raise SmokeError(
            f"{name}: expected one required scipy._lib._ccallback_c native import "
            "(a regular .so in Contents/Frameworks)"
        )
    copy = run_root / "planted" / bundle.name
    shutil.copytree(bundle, copy, symlinks=True)
    planted = copy / targets[0].relative_to(bundle)
    if planted.is_symlink() or not planted.resolve().is_relative_to(copy.resolve()):
        raise SmokeError(f"{name}: the copied native import is not a file inside the copy")
    planted.unlink()
    root = run_root / name
    log = _macos_log_file(root)
    line = "Clearwater: unexpected error; see log: " + str(log).encode(
        "ascii", "backslashreplace"
    ).decode("ascii")
    run_row(
        copy / "Contents" / "MacOS" / executable.name,
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
    print(f"total: {build.tree_size(bundle)} bytes under {bundle}")
    print("largest entries:")
    for path, size in build.size_by_top_level(executable)[:10]:
        print(f"  {size:12d} bytes  {path}")
    print("smoke: PASS (headless process checks in contained process groups)")


def run_smoke(folder: Path, *, out: Path, timeout: float = 60) -> None:
    """Check a Windows onedir artifact or a macOS ``.app`` with bounded headless rows.

    Args:
        folder: The release folder or its parent wrapper.
        out: Evidence root; disposable folders are created under ``smoke/``.
        timeout: Per-process bound, positive and no greater than 60 seconds.

    Raises:
        SmokeError: A check fails, or the host is neither Windows nor macOS.
        OSError: Artifact/input reads or evidence writes fail.
    """
    if sys.platform == "win32":
        _run_windows_smoke(folder, out=out, timeout=timeout)
    elif sys.platform == "darwin":
        _run_macos_smoke(folder, out=out, timeout=timeout)
    else:
        raise SmokeError(
            "platform: the smoke runs on Windows and macOS only "
            "(Linux is not a supported build host)"
        )
