"""WP4.6 tests: the real export worker (``python -m clearwater.app.export_worker``) end to end.

The legacy end-to-end tests export the committed fixture clip ``hevc8-bt709-full.mp4`` on the
CPU (``force_cpu``, libx265) and remain ``slow``. Short stdin regression tests use isolated
stub jobs, raw-reader inputs or product-free shutdown stand-ins; the 20-run series is ``slow``.
The parent side is ``ProcessExportJobs`` (its protocol tests, with fake children, are in
``test_jobs_export_process.py``). Outputs, caches and scratch folders go under ``tmp_path``.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import queue
import subprocess
import sys
import threading
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from clearwater.app import composition
from clearwater.config.presets import new_parameter_set
from clearwater.interfaces import JobResult, Progress, Settings
from clearwater.io.video.probe import find_tool
from clearwater.jobs.export_process import WORKER_LOGGER, ProcessExportJobs
from clearwater.jobs.export_seam import CANCELLED, ExportRequest, unavailable_exports
from clearwater.jobs.safe_write import is_temporary_name

pytestmark = [pytest.mark.usefixtures("ffmpeg_tools")]

CLIP = Path(__file__).resolve().parent / "fixtures" / "video" / "hevc8-bt709-full.mp4"
WORKER = [sys.executable, "-m", "clearwater.app.export_worker"]
QT_ROOTS = ("PySide6", "shiboken6")

_NO_GUI = """
import importlib.abc
import sys

class NoGui(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path=None, target=None):
        if name.split('.')[0] in ('PySide6', 'shiboken6') or (
            name == 'clearwater.app.main' or name.startswith('clearwater.gui')
        ):
            raise ImportError('GUI blocked by worker test: ' + name)
        return None

sys.meta_path.insert(0, NoGui())
"""


def _profile(root: Path) -> dict[str, str]:
    environ = dict(os.environ)
    for name in (
        "APPDATA",
        "LOCALAPPDATA",
        "XDG_CONFIG_HOME",
        "XDG_CACHE_HOME",
        "XDG_DATA_HOME",
        "XDG_STATE_HOME",
    ):
        environ[name] = str(root / name.lower())
    return environ


@pytest.fixture(autouse=True)
def _isolated_profile_and_children(tmp_path, monkeypatch):
    """Protect legacy worker launches too, without changing their test bodies."""
    for name, value in _profile(tmp_path / "profile").items():
        if name in ("APPDATA", "LOCALAPPDATA") or name.startswith("XDG_"):
            monkeypatch.setenv(name, value)
    hooks = tmp_path / "hooks"
    hooks.mkdir()
    (hooks / "sitecustomize.py").write_text(_NO_GUI, encoding="utf-8")
    monkeypatch.setenv("PYTHONPATH", str(hooks) + os.pathsep + os.environ.get("PYTHONPATH", ""))
    children = []
    lock = threading.Lock()
    real_popen = subprocess.Popen

    def popen(*args, **kwargs):
        with lock:
            child = real_popen(*args, **kwargs)
            children.append(child)
            return child

    monkeypatch.setattr(subprocess, "Popen", popen)
    try:
        yield
    finally:
        with lock:
            for child in children:
                if child.poll() is None:
                    child.kill()
                child.wait(timeout=10)


def _child(code, tmp_path, *arguments):
    """Start an isolated child; the fixture always kills and waits on unfinished children."""
    import clearwater

    source = Path(clearwater.__file__).resolve().parents[1]
    bootstrap = _NO_GUI + "\nsys.path.insert(0, sys.argv.pop(1))\n" + code
    return subprocess.Popen(
        [sys.executable, "-I", "-c", bootstrap, str(source), *map(str, arguments)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=_profile(tmp_path / "child-profile"),
    )


def _line(child):
    """Read one protocol line with a bounded wait, including on a broken worker."""
    lines = queue.Queue()
    threading.Thread(target=lambda: lines.put(child.stdout.readline()), daemon=True).start()
    try:
        return json.loads(lines.get(timeout=10))
    except queue.Empty:
        pytest.fail("worker did not produce a protocol line")


def _request_to(child, tmp_path):
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    child.stdin.write(json.dumps(_document(out, tmp_path / "scratch")).encode() + b"\n")
    child.stdin.flush()


_STUB_JOB = """
import json
import logging
import os
import stat
import subprocess
import threading
from pathlib import Path
from clearwater.app import export_worker as worker
from clearwater.interfaces import JobResult
from clearwater.jobs.naming import plan_output
from clearwater.jobs.safe_write import SafeWrite

mode = sys.argv[1]
state = {}
original_stdin = sys.stdin
isolate = worker._isolate_stdin
watch = worker._watch_stdin

def isolated():
    reader = isolate()
    state['reader'] = reader
    state['private'] = reader._fd != 0 and not os.get_inheritable(reader._fd)
    state['same_stdin'] = sys.stdin is original_stdin
    return reader

def watching(reader, flag):
    assert reader is state['reader']
    watch(reader, flag)

worker._isolate_stdin = isolated
worker._watch_stdin = watching

class Engine:
    def job(self, request):
        def run(progress):
            null = os.open(os.devnull, os.O_RDONLY)
            try:
                same_null = os.path.samestat(os.fstat(0), os.fstat(null))
                same_null = same_null and stat.S_ISCHR(os.fstat(0).st_mode)
            finally:
                os.close(null)
            logging.getLogger('clearwater.stdin-test').info(json.dumps({
                'fd0_null': same_null, 'private': state['private'],
                'same_stdin': state['same_stdin'],
            }))
            if mode == 'inherit':
                child = subprocess.Popen(
                    [sys.executable, '-I', '-c',
                     'import sys; print(len(sys.stdin.buffer.read()))'],
                    stdin=None, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                )
                try:
                    out, err = child.communicate(timeout=10)
                    assert child.returncode == 0, err
                    assert out.strip() == b'0', out
                finally:
                    if child.poll() is None:
                        child.kill()
                    child.wait(timeout=10)
                logging.getLogger('clearwater.stdin-test').info('child_read=0')
            if mode in ('cancel', 'eof'):
                with SafeWrite(plan_output(request.source, request.settings, 'video')) as write:
                    write.temp_path.write_bytes(b'partial')
                    progress.report(1, 2, 'partial created')
                    deadline = threading.Event()
                    for _ in range(1000):
                        if progress.cancelled():
                            break
                        deadline.wait(0.005)
                    else:
                        raise AssertionError('cancel did not reach the private reader')
                return JobResult(False, (), (), 'cancelled', 'CPU: stub', 0.0)
            return JobResult(True, (), (), None, 'CPU: stub', 0.0)
        return run

worker.composition.export_jobs = lambda **kwargs: Engine()
raise SystemExit(worker.main([]))
"""


def _result(child):
    messages = []
    while True:
        message = _line(child)
        messages.append(message)
        if "result" in message:
            return messages


def test_a_worker_child_inherits_null_instead_of_the_request_pipe(tmp_path):
    child = _child(_STUB_JOB, tmp_path, "inherit")
    _request_to(child, tmp_path)
    messages = _result(child)
    assert child.wait(timeout=10) == 0, child.stderr.read()
    assert messages[-1]["result"]["ok"] is True
    assert any(m.get("log", {}).get("message") == "child_read=0" for m in messages)


@pytest.mark.parametrize("ending", ["cancel", "eof"])
def test_cancel_and_eof_reach_the_private_reader_and_remove_the_partial(tmp_path, ending):
    child = _child(_STUB_JOB, tmp_path, ending)
    _request_to(child, tmp_path)
    identity = json.loads(_line(child)["log"]["message"])
    assert identity == {"fd0_null": True, "private": True, "same_stdin": True}
    assert _line(child)["progress"] == [1, 2, "partial created"]
    assert len(list((tmp_path / "out").iterdir())) == 1
    if ending == "cancel":
        child.stdin.write(b'{"cancel": true}\n')
        child.stdin.flush()
    else:
        child.stdin.close()
    assert _result(child)[-1]["result"]["failure"] == "cancelled"
    assert child.wait(timeout=10) == 0, child.stderr.read()
    assert list((tmp_path / "out").iterdir()) == []


_IMPORT_WITNESS = """
import json
import os
import subprocess

spawns = []
def forbidden(*args, **kwargs):
    spawns.append('spawn')
    raise AssertionError('spawn before stdin isolation')

subprocess.Popen = forbidden
for name in dir(os):
    if name.startswith(('spawn', 'posix_spawn')):
        setattr(os, name, forbidden)
from clearwater.app import export_worker as worker
order = [['import', len(spawns), 'cupy' in sys.modules]]
before = sys.stdin
reader = worker._isolate_stdin()
order.append(['isolation', len(spawns), 'cupy' in sys.modules])
assert sys.stdin is before
assert reader._fd != 0 and not os.get_inheritable(reader._fd)
reader.close()
print(json.dumps(order))
"""


def test_eager_imports_and_isolation_spawn_nothing_and_import_no_cupy(tmp_path):
    child = _child(_IMPORT_WITNESS, tmp_path)
    out, err = child.communicate(timeout=10)
    (tmp_path / "import-witness-stderr.txt").write_bytes(err)
    assert child.returncode == 0, err.decode("utf-8", "replace")
    assert json.loads(out) == [["import", 0, False], ["isolation", 0, False]]


def test_missing_stdin_follows_the_empty_request_refusal(tmp_path):
    child = _child(
        """
import os
from clearwater.app import export_worker as worker
def forbidden(*args, **kwargs):
    raise AssertionError('empty request reached the watcher or engine')
worker._watch_stdin = forbidden
worker.composition.export_jobs = forbidden
os.close(0)
raise SystemExit(worker.main([]))
""",
        tmp_path,
    )
    out, err = child.communicate(timeout=10)
    assert child.returncode == 2, err
    assert out == b""
    assert err.decode().splitlines() == ["export worker: no request document on stdin"]


_ISOLATION_FAILURE = """
import errno
import json
import os
from pathlib import Path
from clearwater.app import export_worker as worker
if sys.platform == 'win32':
    import ctypes
    import msvcrt
    import psutil
    process = psutil.Process()
    def count():
        return process.num_handles()
else:
    def count():
        return len(os.listdir('/proc/self/fd'))

fd = os.open(sys.argv[2], os.O_RDONLY)
os.dup2(fd, 0)
os.close(fd)
opened = set()
real_dup, real_open, real_close = os.dup, os.open, os.close
mode = sys.argv[1]
def dup(fd):
    if mode == 'dup':
        raise OSError(errno.EMFILE, 'injected')
    new = real_dup(fd)
    opened.add(new)
    return new
def opening(*args, **kwargs):
    if mode == 'open':
        raise OSError(errno.EACCES, 'injected')
    new = real_open(*args, **kwargs)
    opened.add(new)
    return new
def closing(fd):
    real_close(fd)
    opened.remove(fd)
def broken_dup2(*args, **kwargs):
    raise OSError(errno.EBADF, 'injected')
os.dup, os.open, os.close = dup, opening, closing
if mode == 'dup2':
    os.dup2 = broken_dup2
if mode == 'handle':
    ctypes.windll.kernel32.SetStdHandle = lambda *args: 0
def forbidden(*args, **kwargs):
    raise AssertionError('isolation failure reached protocol takeover or engine')
worker.composition.export_jobs = forbidden
worker.os.fdopen = forbidden
before = count()
status = worker.main([])
after = count()
print(json.dumps({'status': status, 'opened': sorted(opened),
                  'before': before, 'after': after}))
"""


@pytest.mark.parametrize(
    "mode",
    [
        "dup",
        "open",
        "dup2",
        pytest.param("handle", marks=pytest.mark.skipif(sys.platform != "win32", reason="Win32")),
    ],
)
def test_isolation_fails_closed_without_leaking_descriptors(tmp_path, mode):
    source = tmp_path / "stdin"
    source.write_bytes(b"request\n")
    child = _child(_ISOLATION_FAILURE, tmp_path, mode, source)
    out, err = child.communicate(timeout=10)
    assert child.returncode == 0, err
    record = json.loads(out)
    assert record["status"] == 2
    assert record["opened"] == []
    assert record["before"] == record["after"]
    kind = "PermissionError" if mode == "open" else "OSError"
    assert err.decode().splitlines() == [f"export worker: stdin isolation failed: {kind}"]


def test_source_and_frozen_use_the_same_isolation_function():
    import inspect

    from clearwater.app import export_worker

    assert "frozen" not in inspect.getsource(export_worker._isolate_stdin)


_SHUTDOWN_STANDIN = """
import io
import os
import threading
import time

fd = os.dup(0)
mode = sys.argv[1]
reader = io.open(fd, 'rb') if mode == 'buffered' else None
started = threading.Event()
def watch():
    started.set()
    if reader is not None:
        reader.readline()
    else:
        os.read(fd, 65536)
threading.Thread(target=watch, daemon=True).start()
assert started.wait(2)
time.sleep(0.05)  # permit the daemon to enter its blocking call before finalization
print('result', flush=True)
"""


@pytest.mark.parametrize("mode", ["buffered", "raw"])
def test_shutdown_with_a_blocked_daemon_reader(tmp_path, mode):
    records = []
    for _ in range(5):
        child = _child(_SHUTDOWN_STANDIN, tmp_path, mode)
        # Do not communicate(): it closes stdin and would release the blocked daemon.
        status = child.wait(timeout=10)
        out, err = child.communicate(timeout=10)
        assert out.splitlines() == [b"result"], err
        records.append({"status": status, "stderr": err.decode("utf-8", "replace")})
        if mode == "raw":
            assert status == 0, err
    (tmp_path / f"standin-{mode}.json").write_text(json.dumps(records), encoding="utf-8")


@pytest.mark.slow  # serial-leg wall series of record, DR-125
def test_twenty_workers_exit_zero_after_their_result_with_stdin_held_open(tmp_path):
    records = []
    for _ in range(20):
        child = _child(_STUB_JOB, tmp_path, "success")
        _request_to(child, tmp_path)
        result = _result(child)[-1]["result"]
        status = child.wait(timeout=10)  # leave the watcher blocked through shutdown
        err = child.stderr.read().decode("utf-8", "replace")
        records.append({"status": status, "result": result, "stderr": err})
        assert result["ok"] is True
        assert status == 0, err
    (tmp_path / "exit-series.json").write_text(json.dumps(records), encoding="utf-8")


class _Progress:
    """An IF-8 progress double: records reports, cancels after N reports when asked."""

    def __init__(self, *, cancel_after: int | None = None) -> None:
        self.reports: list[tuple[int, int | None, str]] = []
        self._cancel = threading.Event()
        self._after = cancel_after

    def report(self, done: int, total: int | None, message: str) -> None:
        self.reports.append((done, total, message))
        if self._after is not None and len(self.reports) >= self._after:
            self._cancel.set()

    def cancelled(self) -> bool:
        return self._cancel.is_set()


def _request(out: Path) -> ExportRequest:
    parameters = new_parameter_set("c3", {}, now=datetime(2026, 10, 30, tzinfo=UTC))
    settings = Settings(output_folder=out, force_cpu=True, video_encoder="libx265", provenance=True)
    return ExportRequest(source=CLIP, kind="video", parameters=parameters, settings=settings)


def _process_jobs(tmp_path: Path, command: list[str] = WORKER) -> ProcessExportJobs:
    return ProcessExportJobs(
        photo_exports=unavailable_exports(),
        cache_dir=tmp_path / "cache",
        app_version="9.9.9",
        command=command,
    )


def _export(tmp_path: Path, progress: Progress, command: list[str] = WORKER) -> JobResult:
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    return _process_jobs(tmp_path, command).job(_request(out))(progress)


def _comment(path: Path) -> Any:
    done = subprocess.run(
        [
            str(find_tool("ffprobe")),
            *("-v", "error", "-of", "json", "-show_entries", "format_tags=comment"),
            str(path),
        ],
        capture_output=True,
        check=True,
    )
    return json.loads(done.stdout).get("format", {}).get("tags", {}).get("comment")


def _framemd5(path: Path) -> list[str]:
    done = subprocess.run(
        [
            str(find_tool("ffmpeg")),
            *("-v", "error", "-i", str(path)),
            *("-map", "0:v", "-f", "framemd5", "pipe:1"),
        ],
        capture_output=True,
        check=True,
        text=True,
    )
    return [line for line in done.stdout.splitlines() if not line.startswith("#")]


def _scratch(tmp_path: Path) -> list[Path]:
    folder = tmp_path / "cache" / "export"
    return sorted(folder.iterdir()) if folder.exists() else []


def _document(out: Path, scratch: Path, **changes: Any) -> dict[str, Any]:
    """A sound request document, by the protocol (``jobs/export_process.py``'s docstring)."""
    request = _request(out)
    document: dict[str, Any] = {
        "format_version": 1,
        "source": str(CLIP),
        "kind": "video",
        "parameters": request.parameters.to_dict(),
        "settings": json.loads(request.settings.to_json()),
        "cache_folder": str(scratch),
        "cache_limit_bytes": request.settings.cache_limit_bytes,
        "app_version": "9.9.9",
    }
    document.update(changes)
    return document


@pytest.mark.slow
def test_the_worker_exports_the_fixture_clip(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO)
    progress = _Progress()
    result = _export(tmp_path, progress)
    assert result.ok, result.failure
    assert result.device.startswith("CPU"), result.device
    (output,) = result.outputs
    assert output.parent == tmp_path / "out" and output.is_file()
    assert sorted(p.name for p in (tmp_path / "out").iterdir()) == [output.name]
    assert not any(is_temporary_name(p.name) for p in (tmp_path / "out").iterdir())
    provenance = json.loads(_comment(output))
    assert provenance["app_version"] == "9.9.9"
    assert provenance["source"]["name"] == CLIP.name
    assert progress.reports, "no progress reached the parent"
    assert _scratch(tmp_path) == []  # the scratch folder is gone
    relogged = [r.getMessage() for r in caplog.records if r.name == WORKER_LOGGER]
    assert any(m.startswith("clearwater.jobs.export: export ") for m in relogged), relogged


@pytest.mark.slow
def test_a_cancel_at_the_first_progress_leaves_nothing(tmp_path: Path) -> None:
    result = _export(tmp_path, _Progress(cancel_after=1))
    assert result.failure is CANCELLED
    assert result.outputs == ()
    assert list((tmp_path / "out").iterdir()) == []  # no output and no temporary
    assert _scratch(tmp_path) == []


@pytest.mark.slow
@pytest.mark.parametrize(
    "case",
    [
        "empty input",
        "not JSON",
        "not one line of ASCII JSON",
        "a missing key",
        "an unknown key",
        "format_version 2",
        "format_version 1.0",
        "bad parameters",
        "bad settings",
        "a source that is not a string",
        "a negative cache limit",
        "a created that overflows",
        "a created that overflows in the settings' last parameters",
    ],
)
def test_a_malformed_request_exits_2_with_one_stderr_line(tmp_path: Path, case: str) -> None:
    out, scratch = tmp_path / "out", tmp_path / "scratch"
    sound = _document(out, scratch)
    missing = dict(sound)
    del missing["app_version"]
    overflow = {**sound["parameters"], "created": "0001-01-01T00:00:00+01:00"}  # R3-5
    nested = {**sound["settings"], "last_parameters": overflow}  # B-3
    line = {
        "empty input": b"",
        "not JSON": b"{not json\n",
        "not one line of ASCII JSON": b'{"format_version": 1, "s\xffource"}\n',
        "a missing key": json.dumps(missing).encode() + b"\n",
        "an unknown key": json.dumps({**sound, "extra": 1}).encode() + b"\n",
        "format_version 2": json.dumps({**sound, "format_version": 2}).encode() + b"\n",
        "format_version 1.0": json.dumps({**sound, "format_version": 1.0}).encode() + b"\n",
        "bad parameters": json.dumps({**sound, "parameters": {"method": 3}}).encode() + b"\n",
        "bad settings": json.dumps({**sound, "settings": {"format_version": 1}}).encode() + b"\n",
        "a source that is not a string": json.dumps({**sound, "source": 7}).encode() + b"\n",
        "a negative cache limit": json.dumps({**sound, "cache_limit_bytes": -1}).encode() + b"\n",
        "a created that overflows": json.dumps({**sound, "parameters": overflow}).encode() + b"\n",
        "a created that overflows in the settings' last parameters": (
            json.dumps({**sound, "settings": nested}).encode() + b"\n"
        ),
    }[case]
    done = subprocess.run(WORKER, input=line, capture_output=True, timeout=120)
    assert done.returncode == 2, (case, done.stderr)
    assert done.stdout == b"", case
    lines = done.stderr.decode("ascii").splitlines()
    assert len(lines) == 1 and lines[0].startswith("export worker: "), (case, lines)
    assert not out.exists() and not scratch.exists()


@pytest.mark.slow
def test_the_worker_imports_no_qt(tmp_path: Path) -> None:
    modules = tmp_path / "modules.txt"
    probe = (
        "import atexit, runpy, sys\n"
        "target = sys.argv.pop(1)  # the worker itself takes no arguments\n"
        "def record():\n"
        "    with open(target, 'w') as f:\n"
        "        f.write('\\n'.join(sorted(sys.modules)))\n"
        "atexit.register(record)\n"
        "runpy.run_module('clearwater.app.export_worker', run_name='__main__', alter_sys=True)\n"
    )
    command = [sys.executable, "-c", probe, str(modules)]
    result = _export(tmp_path, _Progress(), command)
    assert result.ok, result.failure
    loaded = modules.read_text().splitlines()
    assert "clearwater.jobs.export" in loaded  # the probe saw a whole job
    assert [m for m in loaded if m.split(".")[0] in QT_ROOTS] == []


@pytest.mark.slow
def test_q9_the_worker_and_the_in_process_engine_encode_the_same_frames(tmp_path: Path) -> None:
    """N10 across the boundary: decoded frames equal (the file bytes differ between runs)."""
    inside_out = tmp_path / "inside"
    inside_out.mkdir()
    engine = composition.export_jobs(app_version="9.9.9", cache_folder=tmp_path / "inside-cache")
    inside = engine.job(_request(inside_out))(_Progress())
    child = _export(tmp_path, _Progress())
    assert inside.ok and child.ok, (inside.failure, child.failure)
    assert inside.device == child.device
    (a,), (b,) = inside.outputs, child.outputs
    frames_a, frames_b = _framemd5(a), _framemd5(b)
    assert len(frames_a) == len(frames_b) > 0
    assert frames_a == frames_b
    # recorded, not asserted: the container's bytes may differ between two libx265 runs (Q9)
    files = [hashlib.md5(path.read_bytes()).hexdigest() for path in (a, b)]
    print(f"Q9: {len(frames_a)} decoded frames equal; file md5s (in-process, worker) {files}")


@pytest.mark.slow
@pytest.mark.parametrize(
    ("levelno", "name"),
    [
        (5, "DEBUG"),
        (logging.INFO, "INFO"),
        (25, "INFO"),
        (logging.WARNING, "WARNING"),
        (60, "CRITICAL"),
    ],
)
def test_a_log_record_carries_a_level_the_parent_accepts(levelno: int, name: str) -> None:
    """A custom level travels as the standard level at or below it (the parent's five)."""
    import io

    from clearwater.app import export_worker

    stream = io.BytesIO()
    handler = export_worker._ProtocolHandler(export_worker._Channel(stream, threading.Event()))
    handler.emit(logging.LogRecord("clearwater.x", levelno, __file__, 1, "m %s", ("a",), None))
    (line,) = stream.getvalue().splitlines()
    assert json.loads(line) == {"log": {"level": name, "name": "clearwater.x", "message": "m a"}}


@pytest.mark.slow
def test_the_builder_spawns_the_worker_module_and_keeps_the_photo_engine(tmp_path: Path) -> None:
    """Q2 as ruled: ``process_export_jobs`` takes no cache limit; its default is the worker."""
    import clearwater

    photo = unavailable_exports()
    built = composition.process_export_jobs(photo_exports=photo, cache_dir=tmp_path / "cache")
    assert isinstance(built, ProcessExportJobs)
    assert built._command == tuple(WORKER)
    assert built._photo_exports is photo
    assert built._cache_dir == tmp_path / "cache"
    assert built._app_version == clearwater.__version__
    fake = ("python", "-c", "pass")
    given = composition.process_export_jobs(
        photo_exports=photo, cache_dir=tmp_path, app_version="9.9.9", command=fake
    )
    assert isinstance(given, ProcessExportJobs)
    assert (given._command, given._app_version) == (fake, "9.9.9")
    assert not (tmp_path / "cache").exists()  # building touches no folder


@pytest.mark.parametrize(
    ("chunks", "lines"),
    [
        ([b'request\n{"cancel": true}\n', b""], [b"request\n", b'{"cancel": true}\n', b""]),
        ([b"first", b"\nsecond", b"\n", b""], [b"first\n", b"second\n", b""]),
        ([b"x" * 65536, b"tail\n", b""], [b"x" * 65536 + b"tail\n", b""]),
        ([b"last", b""], [b"last", b""]),
        ([b""], [b"", b""]),
    ],
)
def test_raw_reader_preserves_lines_and_read_ahead(monkeypatch, chunks, lines) -> None:
    """Dropping the remainder or treating a short read as EOF loses request/cancel bytes."""
    from clearwater.app import export_worker

    remaining = iter(chunks)
    reads = []

    def read(fd, size):
        reads.append((fd, size))
        return next(remaining)

    monkeypatch.setattr(os, "read", read)
    reader = export_worker._RawStdinReader(123)
    assert [reader.readline() for _ in lines] == lines
    assert reader.readline() == b""
    assert reads and set(reads) == {(123, 65536)}


def test_raw_read_error_cancels_the_watcher(monkeypatch) -> None:
    """A broken private pipe must cancel, rather than strand the job."""
    from clearwater.app import export_worker

    def broken(fd, size):
        raise OSError("broken pipe")

    monkeypatch.setattr(os, "read", broken)
    cancel = threading.Event()
    export_worker._watch_stdin(export_worker._RawStdinReader(123), cancel)
    assert cancel.is_set()


def test_raw_reader_close_owns_only_its_private_descriptor(monkeypatch) -> None:
    from clearwater.app import export_worker

    closed = []
    monkeypatch.setattr(os, "close", closed.append)
    reader = export_worker._RawStdinReader(123)
    reader.close()
    reader.close()
    assert closed == [123]
    assert reader.readline() == b""
