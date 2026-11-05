"""Run bounded, headless Windows onedir checks without entering the GUI branch.

Only the commissioned refusal/worker argument sets may launch Clearwater. Each
row has fresh disposable profile roots and a System32-only PATH. A planted
import failure uses a separate copy; the shipping folder is only read. Process
supervision is not window evidence: the seat supplies the independent UIA watch.
"""

from __future__ import annotations

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
from collections.abc import Sequence
from functools import cache
from pathlib import Path
from types import ModuleType
from typing import BinaryIO, NamedTuple, cast

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
        """Refuse unproved POSIX containment; WP6.5 must supply its native proof.

        The ruled method is start_new_session=True with a process-group census
        via killpg(pgid, 0) and bounded killpg cleanup. It has not been proved
        natively here, so this Windows release tool never launches uncontained.
        """
        raise SmokeError(
            f"{name}: POSIX start_new_session/killpg containment awaits WP6.5 native proof"
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
