"""WP4.6 tests: the parent side of the export worker process (``jobs/export_process.py``).

Every child here is a FAKE: a few lines of Python written to ``tmp_path`` and run with
``sys.executable``, speaking the line protocol by hand. No clearwater import in the child, no
FFmpeg, no GPU; each test ends in well under 2 s. The real worker is tested in
``test_app_export_worker.py``.
"""

from __future__ import annotations

import json
import logging
import os
import re
import subprocess
import sys
import textwrap
import threading
import time
from collections.abc import Callable
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

import pytest

from clearwater.interfaces import JobResult, ParameterSet, Progress, Settings
from clearwater.jobs import export_process
from clearwater.jobs.export_process import (
    CANCEL_LINE,
    MAX_LINE_BYTES,
    STALE_AFTER_S,
    STDERR_TAIL_BYTES,
    WORKER_LOGGER,
    ProcessExportJobs,
)
from clearwater.jobs.export_seam import CANCELLED, ExportJobs, ExportRequest

PROCESS_LOGGER = "clearwater.jobs.export_process"
"""The module's own logger (invalid lines, kills, the sweep)."""

PRELUDE = textwrap.dedent(
    """\
    import json, os, subprocess, sys, time
    from pathlib import Path
    OUT = sys.stdout.buffer
    REQUEST_LINE = sys.stdin.buffer.readline()
    REQUEST = json.loads(REQUEST_LINE)
    ARGS = sys.argv[1:]
    def raw(data):
        OUT.write(data)
        OUT.flush()
    def send(obj):
        raw(json.dumps(obj).encode("ascii") + b"\\n")
    def result(**fields):
        body = {"ok": True, "outputs": [], "warnings": [], "failure": None,
                "device": "cpu", "elapsed_s": 1000.0}
        body.update(fields)
        send({"result": body})
    """
)
"""What every fake child runs first: read the one request line, then the protocol helpers."""

GRANDCHILD = textwrap.dedent(
    """\
    import sys, time
    from pathlib import Path
    folder = Path(sys.argv[1])
    beats = 0
    while not (folder / "stop").exists() and beats < 600:
        beats += 1
        (folder / "beat").write_text(str(beats))
        time.sleep(0.05)
    (folder / "gone").write_text("gone")
    """
)
"""A grandchild that beats a file every 50 ms until a ``stop`` file appears (at most 30 s)."""


class _Progress:
    """An IF-8 progress double: records reports, cancels on demand or after N reports."""

    def __init__(self, *, cancel_after: int | None = None, cancelled: bool = False) -> None:
        self.reports: list[tuple[int, int | None, str]] = []
        self._cancel = threading.Event()
        self._after = cancel_after
        if cancelled:
            self._cancel.set()

    def report(self, done: int, total: int | None, message: str) -> None:
        self.reports.append((done, total, message))
        if self._after is not None and len(self.reports) >= self._after:
            self._cancel.set()

    def cancelled(self) -> bool:
        return self._cancel.is_set()


class _PhotoJobs:
    """The in-process photo engine double: records requests, returns a fixed ok result."""

    def __init__(self) -> None:
        self.requests: list[ExportRequest] = []

    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]:
        self.requests.append(request)

        def run(progress: Progress) -> JobResult:
            return JobResult(True, (Path("photo_corrected.png"),), (), None, "cpu", 0.0)

        return run


def _child(tmp_path: Path, body: str, *args: str) -> list[str]:
    """Write a fake child (the prelude plus ``body``) and return its command."""
    folder = tmp_path / "children"
    folder.mkdir(exist_ok=True)
    script = folder / f"child_{len(list(folder.iterdir()))}.py"
    script.write_text(PRELUDE + textwrap.dedent(body), encoding="utf-8")
    return [sys.executable, str(script), *args]


def _request(tmp_path: Path, *, kind: str = "video", **values: object) -> ExportRequest:
    """Return a request for a source that does not exist (the job must not look)."""
    parameters = ParameterSet(
        method="c3",
        parameters={"strength": 0.5, **values},
        created=datetime(2026, 10, 30, 5, 0, tzinfo=UTC),
        app_version="test",
    )
    settings = Settings(output_folder=tmp_path / "out folder", cache_limit_bytes=123_456_789)
    return ExportRequest(
        source=tmp_path / "my clips" / "clip.mp4",
        kind=kind,  # type: ignore[arg-type]
        parameters=parameters,
        settings=settings,
    )


def _jobs(tmp_path: Path, command: list[str], photo: ExportJobs | None = None) -> ProcessExportJobs:
    return ProcessExportJobs(
        photo_exports=photo if photo is not None else _PhotoJobs(),
        cache_dir=tmp_path / "cache",
        app_version="9.9.9",
        command=command,
    )


def _run(
    tmp_path: Path, command: list[str], progress: _Progress | None = None
) -> tuple[JobResult, _Progress]:
    progress = progress if progress is not None else _Progress()
    result = _jobs(tmp_path, command).job(_request(tmp_path))(progress)
    return result, progress


def _scratch_folders(tmp_path: Path) -> list[Path]:
    folder = tmp_path / "cache" / "export"
    return sorted(folder.iterdir()) if folder.exists() else []


def _messages(caplog: pytest.LogCaptureFixture, logger: str) -> list[str]:
    return [r.getMessage() for r in caplog.records if r.name == logger]


def _read_beat(beat: Path) -> int:
    """Return the grandchild's last beat; a read that meets the rewrite's truncation is retried.

    ``write_text`` truncates before it writes, so a read can see an empty file (R1 F13).
    """
    for _ in range(200):
        if text := beat.read_text():
            return int(text)
        time.sleep(0.005)
    raise AssertionError("the beat file stayed empty")


def _ended(status: int) -> str:
    """The fixed exit-without-result text (CHARC 55959e2f (d)), before any type name."""
    return (
        f"The export worker ended without a result (exit status {status}); "
        "details are in the application log."
    )


def _tail_records(caplog: pytest.LogCaptureFixture) -> list[logging.LogRecord]:
    """The log records that carry the worker's stderr tail."""
    return [
        r
        for r in caplog.records
        if r.name == WORKER_LOGGER and r.getMessage().startswith("export worker stderr")
    ]


class _Clock:
    """A monotonic clock that moves one unit per reading: the module's loop reads it once per
    pass (and once more for a result), so a deadline is counted in readings, not seconds."""

    def __init__(self) -> None:
        self.now = 0.0

    def monotonic(self) -> float:
        self.now += 1.0
        return self.now


@pytest.fixture
def clock(monkeypatch: pytest.MonkeyPatch) -> _Clock:
    """Replace the module's ``time.monotonic`` (only its own; the queues keep real time)."""
    fake = _Clock()
    namespace = SimpleNamespace(
        monotonic=fake.monotonic, perf_counter=time.perf_counter, time=time.time
    )
    monkeypatch.setattr(export_process, "time", namespace)
    return fake


@pytest.fixture
def quick_kill(monkeypatch: pytest.MonkeyPatch) -> float:
    """Shorten the kill grace so a kill test ends quickly."""
    monkeypatch.setattr(export_process, "KILL_AFTER_CANCEL_S", 0.3)
    return 0.3


# --- progress and the result -----------------------------------------------------------------


def test_progress_lines_are_forwarded_in_order(tmp_path: Path) -> None:
    command = _child(
        tmp_path,
        """\
        send({"progress": [0, 10, "starting"]})
        send({"progress": [5, 10, "half"]})
        send({"progress": [10, None, "done"]})
        result()
        """,
    )
    result, progress = _run(tmp_path, command)
    assert result.ok, result.failure
    assert progress.reports == [(0, 10, "starting"), (5, 10, "half"), (10, None, "done")]


def test_the_result_line_becomes_an_equal_job_result(tmp_path: Path) -> None:
    output = tmp_path / "out folder" / "clip_corrected.mp4"
    command = _child(
        tmp_path,
        """\
        result(outputs=[ARGS[0]], warnings=["one warning"], device="GPU: CUDA")
        """,
        str(output),
    )
    start = time.perf_counter()
    result, _ = _run(tmp_path, command)
    wall = time.perf_counter() - start
    expected = JobResult(True, (output,), ("one warning",), None, "GPU: CUDA", 0.0)
    assert replace(result, elapsed_s=0.0) == expected
    assert isinstance(result.outputs[0], Path)
    # the parent's own measure (spawn included), never the child's figure (1000.0)
    assert 0.0 < result.elapsed_s <= wall


def test_a_cancelled_result_returns_the_constant_itself(tmp_path: Path) -> None:
    command = _child(tmp_path, 'result(ok=False, failure="can" + "celled", device="cpu")\n')
    result, _ = _run(tmp_path, command)
    assert result.ok is False
    assert result.failure is CANCELLED


def test_trailing_carriage_returns_are_tolerated(tmp_path: Path) -> None:
    command = _child(
        tmp_path,
        """\
        raw(b'{"progress": [1, 2, "crlf"]}\\r\\n')
        raw(json.dumps({"result": {"ok": True, "outputs": [], "warnings": [], "failure": None,
            "device": "cpu", "elapsed_s": 0.5}}).encode() + b"\\r\\n")
        """,
    )
    result, progress = _run(tmp_path, command)
    assert result.ok, result.failure
    assert progress.reports == [(1, 2, "crlf")]


def test_escaped_non_ascii_text_arrives_decoded(tmp_path: Path) -> None:
    command = _child(tmp_path, 'send({"progress": [1, 1, "caf\\u00e9"]})\nresult()\n')
    _, progress = _run(tmp_path, command)
    assert progress.reports == [(1, 1, "caf\u00e9")]


# --- the request document --------------------------------------------------------------------


def test_the_request_document_is_one_ascii_line_with_the_ruled_keys(tmp_path: Path) -> None:
    received = tmp_path / "received.bin"
    command = _child(
        tmp_path,
        """\
        Path(ARGS[0]).write_bytes(REQUEST_LINE)
        result()
        """,
        str(received),
    )
    request = replace(_request(tmp_path), source=tmp_path / "my clips" / "cl\u00edp.mp4")
    result = _jobs(tmp_path, command).job(request)(_Progress())
    assert result.ok, result.failure
    line = received.read_bytes()
    assert line.endswith(b"\n") and line.count(b"\n") == 1
    line.decode("ascii")  # every non-ASCII character travels as an escape
    assert b"\\u00ed" in line
    document = json.loads(line)
    assert set(document) == {
        "format_version",
        "source",
        "kind",
        "parameters",
        "settings",
        "cache_folder",
        "cache_limit_bytes",
        "app_version",
    }
    assert document["format_version"] == 1
    assert document["source"] == str(request.source.absolute())
    assert document["kind"] == "video"
    assert ParameterSet.from_dict(document["parameters"]) == request.parameters
    assert Settings.from_json(json.dumps(document["settings"])) == request.settings
    assert document["cache_limit_bytes"] == 123_456_789  # the request's own settings (Q2)
    assert document["app_version"] == "9.9.9"
    scratch = Path(document["cache_folder"])
    assert scratch.parent == tmp_path / "cache" / "export"
    assert len(scratch.name) == 32  # a uuid4 hex


def test_a_request_that_cannot_be_encoded_fails_without_a_spawn(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    marker = tmp_path / "spawned"
    command = _child(tmp_path, "Path(ARGS[0]).write_text('x')\nresult()\n", str(marker))
    request = _request(tmp_path, strength=float("nan"))
    result = _jobs(tmp_path, command).job(request)(_Progress())
    assert result.ok is False
    # the same rule as the spawn's (CHARC 3ed8335f): the type name; the full text to the log
    # (the frozen ParameterSet refuses the NaN itself: IF-9's FormatError, a ValueError)
    assert result.failure == (
        "The export request could not be encoded (FormatError); details are in the application log."
    )
    logged = [r for r in caplog.records if r.name == WORKER_LOGGER]
    assert len(logged) == 1 and "FormatError" in logged[0].getMessage()
    assert result.device == "none"
    assert not marker.exists()
    assert _scratch_folders(tmp_path) == []


# --- cancel ----------------------------------------------------------------------------------


def test_cancel_is_delivered_on_stdin_and_the_child_ends(tmp_path: Path) -> None:
    seen = tmp_path / "seen.bin"
    command = _child(
        tmp_path,
        """\
        send({"progress": [1, 100, "working"]})
        line = sys.stdin.buffer.readline()
        Path(ARGS[0]).write_bytes(line)
        result(ok=False, failure="cancelled")
        """,
        str(seen),
    )
    result, _ = _run(tmp_path, command, _Progress(cancel_after=1))
    assert result.failure is CANCELLED
    assert seen.read_bytes() == CANCEL_LINE == b'{"cancel": true}\n'


def test_stdin_is_closed_after_the_cancel_line(tmp_path: Path) -> None:
    command = _child(
        tmp_path,
        """\
        send({"progress": [1, 100, "working"]})
        while sys.stdin.buffer.readline():
            pass  # ignores the cancel line itself; stops only at end of input
        result(ok=False, failure="cancelled")
        """,
    )
    result, _ = _run(tmp_path, command, _Progress(cancel_after=1))
    assert result.failure is CANCELLED


def test_cancelled_before_the_start_spawns_nothing(tmp_path: Path) -> None:
    marker = tmp_path / "spawned"
    command = _child(tmp_path, "Path(ARGS[0]).write_text('x')\nresult()\n", str(marker))
    result, _ = _run(tmp_path, command, _Progress(cancelled=True))
    assert result.ok is False
    assert result.failure is CANCELLED
    assert result.device == "none"
    assert not marker.exists()
    assert _scratch_folders(tmp_path) == []


def test_a_cancel_during_the_sweep_spawns_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R1 F7: the cancel is checked again after the first job's sweep, before the spawn."""
    marker = tmp_path / "spawned"
    command = _child(tmp_path, "Path(ARGS[0]).write_text('x')\nresult()\n", str(marker))
    progress = _Progress()
    monkeypatch.setattr(ProcessExportJobs, "_sweep_once", lambda self: progress._cancel.set())
    result, _ = _run(tmp_path, command, progress)
    assert result.failure is CANCELLED
    assert result.device == "none"
    assert not marker.exists()
    assert _scratch_folders(tmp_path) == []


def test_a_child_that_ignores_cancel_is_killed(
    tmp_path: Path, quick_kill: float, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(
        tmp_path,
        """\
        send({"progress": [1, 100, "working"]})
        time.sleep(30)
        """,
    )
    result, _ = _run(tmp_path, command, _Progress(cancel_after=1))
    assert result.ok is False
    assert result.failure == "The export worker did not stop after cancel and was ended."
    assert result.device == "unknown"
    assert len(_scratch_folders(tmp_path)) == 1  # kept on a kill: the next sweep removes it
    assert any("killed" in m for m in _messages(caplog, PROCESS_LOGGER))


def test_a_kill_leaves_the_grandchild_running(tmp_path: Path, quick_kill: float) -> None:
    """Q11: ``Popen.kill`` ends the worker, not a grandchild it started (FFmpeg's place)."""
    beats = tmp_path / "beats"
    beats.mkdir()
    grandchild = tmp_path / "grandchild.py"
    grandchild.write_text(GRANDCHILD, encoding="utf-8")
    command = _child(
        tmp_path,
        """\
        subprocess.Popen([sys.executable, ARGS[0], ARGS[1]], stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        while not (Path(ARGS[1]) / "beat").exists():
            time.sleep(0.01)
        send({"progress": [1, 100, "working"]})
        time.sleep(30)
        """,
        str(grandchild),
        str(beats),
    )
    try:
        result, _ = _run(tmp_path, command, _Progress(cancel_after=1))
        assert result.failure == "The export worker did not stop after cancel and was ended."
        before = _read_beat(beats / "beat")
        time.sleep(0.5)
        after = _read_beat(beats / "beat")
        assert after > before, "the grandchild stopped with the worker"
        assert not (beats / "gone").exists()
    finally:
        (beats / "stop").write_text("stop")  # the test ends the grandchild itself
        deadline = time.monotonic() + 10
        while not (beats / "gone").exists() and time.monotonic() < deadline:
            time.sleep(0.05)
    assert (beats / "gone").exists()


# --- exit without a result -------------------------------------------------------------------


@pytest.mark.parametrize("status", [1, 2, 0])
def test_an_exit_without_a_result_is_a_failed_result(tmp_path: Path, status: int) -> None:
    command = _child(
        tmp_path,
        """\
        send({"progress": [1, 100, "working"]})
        sys.stderr.write("something went wrong\\n")
        sys.exit(int(ARGS[0]))
        """,
        str(status),
    )
    result, _ = _run(tmp_path, command)
    assert result.ok is False
    assert result.outputs == ()
    assert result.device == "unknown"
    # CHARC 55959e2f (d): no stderr content in the text; the last line is no exception line
    assert result.failure == _ended(status)
    assert _scratch_folders(tmp_path) == []  # nothing is left running: removed


def test_the_stderr_tail_goes_to_the_log_and_the_text_names_only_the_exception_type(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """CHARC 55959e2f (d): the tail is logged verbatim; the text carries the type name only."""
    caplog.set_level(logging.DEBUG)
    command = _child(
        tmp_path,
        """\
        sys.stderr.write("noise line\\n" * 50)
        raise FileNotFoundError(2, "No such file", ARGS[0])
        """,
        str(tmp_path / "Owner's hidden folder" / "clip.mp4"),
    )
    result, _ = _run(tmp_path, command)
    assert result.failure == _ended(1) + "\nFileNotFoundError"
    (logged,) = _tail_records(caplog)
    assert logged.levelno == logging.WARNING
    assert "Traceback (most recent call last)" in logged.getMessage()
    assert repr(str(tmp_path / "Owner's hidden folder" / "clip.mp4")) in logged.getMessage()


@pytest.mark.parametrize(
    "last_line",
    [
        "something went wrong",
        "C:\\Owner\\FooError: no",  # a path before the colon is not a type name
        "Error",  # the pattern needs a name before the suffix
        "a b Error: x",
    ],
)
def test_a_last_line_that_is_no_exception_line_adds_nothing(tmp_path: Path, last_line: str) -> None:
    command = _child(tmp_path, "sys.stderr.write(ARGS[0] + '\\n')\nsys.exit(1)\n", last_line)
    result, _ = _run(tmp_path, command)
    assert result.failure == _ended(1)


def test_the_failure_text_contains_no_path_component_from_a_planted_hostile_folder_name(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """R1 F5 and R2-2 under CHARC 55959e2f (d): their planted folder names, as controls.

    The worker's stderr names them plain and as ``repr`` (spaces, apostrophes, a leading space,
    non-ASCII) and ends with an exception line whose MESSAGE holds one: the failure text carries
    none of them; the application log carries them all, verbatim.
    """
    caplog.set_level(logging.DEBUG)
    known = tmp_path / "my clips"  # the source's folder
    unknown_root = Path("D:\\owner home") if sys.platform == "win32" else Path("/home/owner_home")
    paths = [
        f"{known} Archive{os.sep}hiddenA{os.sep}a.mp4",  # F5: a name continuing a known folder
        str(known / "Diver's hiddenB" / "b.mp4"),  # F5: an apostrophe inside a name
        str(known / "'Tis hiddenC" / "c.mp4"),
        str(unknown_root / "Owner's hiddenD" / "d.mp4"),
        str(known / "Divers' hiddenE" / "e.mp4"),
        str(known / "Tauchg\u00e4nge hiddenF" / "f.mp4"),  # non-ASCII (CHARC e15d408a)
        str(unknown_root / "Plong\u00e9e \u00e9t\u00e9 hiddenG" / "g.mp4"),
        str(unknown_root / " privateH" / "h.mp4"),  # R2-2: a leading space
        str(unknown_root / "' privateI" / "i.mp4"),  # R2-2: an apostrophe, then a space
    ]
    command = _child(
        tmp_path,
        """\
        for path in ARGS:
            for shown in (path, repr(path)):
                sys.stderr.buffer.write(("could not open " + shown + "\\n").encode("utf-8"))
        sys.stderr.flush()
        raise OSError(2, "No such file", ARGS[-1])
        """,
        *paths,
    )
    result, _ = _run(tmp_path, command)
    assert result.failure == _ended(1) + "\nFileNotFoundError"
    for planted in (
        *("Archive", "hidden", "Diver", "Tis", "Owner", "owner", "Tauchg", "Plong", "private"),
        *("my clips", tmp_path.name, ".mp4"),
    ):
        assert planted not in result.failure, planted
    (logged,) = _tail_records(caplog)
    assert str(known / "Tauchg\u00e4nge hiddenF" / "f.mp4") in logged.getMessage()  # verbatim
    assert repr(paths[-1]) in logged.getMessage()


def test_a_stderr_flood_neither_blocks_nor_overflows_the_log(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(
        tmp_path,
        """\
        sys.stderr.buffer.write(b"x" * (1 << 20) + b"\\n")
        sys.stderr.buffer.write(b"the last line\\n")
        sys.stderr.flush()
        sys.exit(1)
        """,
    )
    result, _ = _run(tmp_path, command)
    assert result.failure == _ended(1)
    (logged,) = _tail_records(caplog)
    tail = logged.getMessage().partition("\n")[2]
    assert tail.endswith("the last line\n")
    assert len(tail.encode()) <= STDERR_TAIL_BYTES


def test_a_stderr_flood_before_a_result_does_not_block(tmp_path: Path) -> None:
    command = _child(
        tmp_path,
        """\
        sys.stderr.buffer.write(b"y" * (1 << 20))
        sys.stderr.flush()
        result()
        """,
    )
    result, _ = _run(tmp_path, command)
    assert result.ok, result.failure


def test_a_spawn_failure_names_the_error_type_and_errno_only(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """CHARC 3ed8335f: a planted hostile interpreter path leaves no component in the text."""
    caplog.set_level(logging.DEBUG)
    missing = tmp_path / "Owner's hidden folder" / " private" / "missing-interpreter"
    result, _ = _run(tmp_path, [str(missing)])
    assert result.ok is False
    assert result.failure == (
        "The export worker could not be started (FileNotFoundError, errno 2); "
        "details are in the application log."
    )
    assert result.device == "none"
    assert _scratch_folders(tmp_path) == []
    logged = [r for r in caplog.records if r.name == WORKER_LOGGER]
    assert len(logged) == 1 and logged[0].levelno == logging.WARNING
    assert "FileNotFoundError" in logged[0].getMessage()  # the full OSError text


def test_a_scratch_folder_that_cannot_be_made_names_the_error_type_only(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """CHARC 3ed8335f: the same rule for the scratch folder's creation."""
    caplog.set_level(logging.DEBUG)
    hostile = tmp_path / "Owner's hidden folder" / " private"
    hostile.mkdir(parents=True)
    (hostile / "cache").write_text("a file where the cache folder should be")
    jobs = ProcessExportJobs(
        photo_exports=_PhotoJobs(),
        cache_dir=hostile / "cache",
        app_version="9.9.9",
        command=_child(tmp_path, "result()\n"),
    )
    result = jobs.job(_request(tmp_path))(_Progress())
    assert result.failure is not None
    assert re.fullmatch(
        r"The export worker could not be started \([A-Za-z]+Error(, errno \d+)?\); "
        r"details are in the application log\.",
        result.failure,
    ), result.failure
    for planted in ("Owner", "hidden", "private", "cache", tmp_path.name):
        assert planted not in result.failure, planted
    logged = [r for r in caplog.records if r.name == WORKER_LOGGER]
    assert len(logged) == 1 and logged[0].levelno == logging.WARNING


# --- strictness: ignored lines ---------------------------------------------------------------


@pytest.mark.parametrize(
    ("line", "why"),
    [
        (b"not json at all", "not JSON"),
        (b"[1, 2, 3]", "not an object"),
        (b'{"bogus": 1}', "unknown key"),
        (b'{"progress": [1, 2, "a"], "log": {}}', "two keys"),
        (b'{"progress": [1, 2]}', "progress shape"),
        (b'{"progress": [true, 2, "a"]}', "progress done a bool"),
        (b'{"progress": [1, 2, "a\xff"]}', "not UTF-8"),
        (b'{"progress": [1, NaN, "a"]}', "a non-finite constant"),
        (b'{"log": {"level": "LOUD", "name": "x", "message": "m"}}', "unknown level"),
        (b'{"log": {"level": "INFO", "name": "x"}}', "log shape"),
        (b'{"log": {"level": ["x"], "name": "x", "message": "m"}}', "a list level (R1 F2)"),
        pytest.param(
            b'{"result": {"ok": true, "outputs": [], "warnings": [], "failure": null,'
            b' "device": "cpu", "elapsed_s": 1' + b"0" * 400 + b"}}",
            "an elapsed_s too large for a float (R1 F3)",
            id="elapsed_s-overflow",
        ),
    ],
)
def test_an_invalid_line_is_ignored_and_logged(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, line: bytes, why: str
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(
        tmp_path,
        """\
        raw(bytes.fromhex(ARGS[0]) + b"\\n")
        send({"progress": [3, 4, "valid"]})
        result()
        """,
        line.hex(),
    )
    result, progress = _run(tmp_path, command)
    assert result.ok, (why, result.failure)
    assert progress.reports == [(3, 4, "valid")], why
    assert any("ignored" in m for m in _messages(caplog, PROCESS_LOGGER)), why


def test_an_unknown_key_is_logged_by_its_length_and_first_8_characters(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """R1 F6 (CHARC e15d408a): the key's length and at most its first 8 characters, no more."""
    caplog.set_level(logging.DEBUG)
    command = _child(
        tmp_path,
        'send({"C:\\\\Owner\\\\Private\\\\GPS": 1})\nresult()\n',
    )
    result, _ = _run(tmp_path, command)
    assert result.ok, result.failure
    ignored = [m for m in _messages(caplog, PROCESS_LOGGER) if "ignored" in m]
    assert ignored == [
        "export worker line ignored: an unknown key of 20 characters, first 'C:\\\\Owner'"
    ]
    assert "Private" not in ignored[0]


def test_any_error_decoding_one_line_ignores_that_line_only(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """R1 F2: no exception from one line's decode ends the reader; the later lines arrive."""
    caplog.set_level(logging.DEBUG)
    decode = export_process._decode_line
    calls: list[bytes] = []

    def first_one_raises(content: bytes) -> tuple[str, object]:
        calls.append(content)
        if len(calls) == 1:
            raise LookupError("an error the decoder did not foresee")
        return decode(content)

    monkeypatch.setattr(export_process, "_decode_line", first_one_raises)
    command = _child(tmp_path, 'send({"progress": [1, 2, "first"]})\nresult(device="kept")\n')
    result, progress = _run(tmp_path, command)
    assert result.ok and result.device == "kept", result.failure
    assert progress.reports == []  # the first line was ignored
    ignored = [m for m in _messages(caplog, PROCESS_LOGGER) if "ignored" in m]
    assert ignored == ["export worker line ignored: a line that could not be decoded (LookupError)"]


def test_a_line_over_the_limit_is_ignored_and_one_at_it_is_kept(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(
        tmp_path,
        """\
        limit = int(ARGS[0])
        head, tail = b'{"progress": [1, 2, "', b'"]}'
        raw(head + b"a" * (limit + 1 - len(head) - len(tail)) + tail + b"\\n")
        raw(head + b"b" * (limit - len(head) - len(tail)) + tail + b"\\n")
        raw(head + b"c" * (5 * limit) + tail + b"\\n")
        send({"progress": [2, 2, "after"]})
        result()
        """,
        str(MAX_LINE_BYTES),
    )
    result, progress = _run(tmp_path, command)
    assert result.ok, result.failure
    assert [(d, t, m[:1]) for d, t, m in progress.reports] == [(1, 2, "b"), (2, 2, "a")]
    assert len(progress.reports[0][2]) == MAX_LINE_BYTES - len('{"progress": [1, 2, ""]}')
    ignored = [m for m in _messages(caplog, PROCESS_LOGGER) if "ignored" in m]
    assert len(ignored) == 2
    assert all(len(m) < 400 for m in ignored)  # the line itself is never logged whole


@pytest.mark.parametrize(
    "body",
    [
        '{"ok": "yes", "outputs": [], "warnings": [], "failure": null, "device": "cpu",'
        ' "elapsed_s": 1.0}',
        '{"ok": true, "outputs": [1], "warnings": [], "failure": null, "device": "cpu",'
        ' "elapsed_s": 1.0}',
        '{"ok": true, "outputs": [], "warnings": [], "failure": null, "device": "cpu"}',
        '{"ok": true, "outputs": [], "warnings": [], "failure": null, "device": "cpu",'
        ' "elapsed_s": 1.0, "extra": 1}',
        '{"ok": true, "outputs": [], "warnings": [], "failure": null, "device": "cpu",'
        ' "elapsed_s": true}',
    ],
)
def test_a_wrong_typed_result_is_ignored_and_the_job_ends_without_one(
    tmp_path: Path, caplog: pytest.LogCaptureFixture, body: str
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(tmp_path, 'raw(b\'{"result": \' + ARGS[0].encode() + b"}\\n")\n', body)
    result, _ = _run(tmp_path, command)
    assert result.ok is False
    assert result.failure == _ended(0)
    assert any("ignored" in m for m in _messages(caplog, PROCESS_LOGGER))


def test_an_unterminated_last_line_is_ignored(tmp_path: Path) -> None:
    command = _child(
        tmp_path,
        """\
        raw(json.dumps({"result": {"ok": True, "outputs": [], "warnings": [], "failure": None,
            "device": "cpu", "elapsed_s": 0.5}}).encode())
        """,
    )
    result, _ = _run(tmp_path, command)
    assert result.failure == _ended(0)


def test_the_first_result_is_kept_and_a_second_one_ignored(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(tmp_path, 'result(device="first")\nresult(ok=False, failure="second")\n')
    result, _ = _run(tmp_path, command)
    assert result.ok and result.device == "first"
    assert any("second result" in m for m in _messages(caplog, PROCESS_LOGGER))


def test_a_result_followed_by_a_bad_exit_is_returned(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(tmp_path, "result()\nsys.exit(3)\n")
    result, _ = _run(tmp_path, command)
    assert result.ok, result.failure
    assert any("exit status 3" in m for m in _messages(caplog, PROCESS_LOGGER))


def test_a_child_alive_after_its_result_is_killed_and_the_result_kept(
    tmp_path: Path, quick_kill: float, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(tmp_path, 'result(device="kept")\ntime.sleep(30)\n')
    result, _ = _run(tmp_path, command)
    assert result.ok and result.device == "kept"
    assert any("killed" in m for m in _messages(caplog, PROCESS_LOGGER))


def test_a_result_after_the_cancel_does_not_restart_the_kill_grace(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    """R1 F1: the grace runs from the cancel line, the earlier of the two triggers."""
    monkeypatch.setattr(export_process, "KILL_AFTER_CANCEL_S", 1.0)
    caplog.set_level(logging.DEBUG)
    command = _child(
        tmp_path,
        """\
        send({"progress": [1, 100, "working"]})
        sys.stdin.buffer.readline()  # the cancel line
        result(ok=False, failure="cancelled")
        time.sleep(30)
        """,
    )
    result, _ = _run(tmp_path, command, _Progress(cancel_after=1))
    assert result.failure is CANCELLED  # the result is kept
    killed = [m for m in _messages(caplog, PROCESS_LOGGER) if "killed:" in m]
    assert killed == ["export worker killed: still running 1.0 s after its cancel"]


def test_the_kill_deadline_counts_from_the_cancel_not_from_a_later_result(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    """R2-5: on the controlled clock the kill falls at the cancel's deadline (no wall clock)."""
    grace = 40.0
    monkeypatch.setattr(export_process, "KILL_AFTER_CANCEL_S", grace)
    command = _child(
        tmp_path,
        """\
        send({"progress": [1, 100, "working"]})
        sys.stdin.buffer.readline()  # the cancel line
        time.sleep(0.5)  # several of the parent's passes go by before the result
        result(ok=False, failure="cancelled")
        time.sleep(30)
        """,
    )
    cancel_at: list[float] = []
    kill_at: list[float] = []

    class _Recording(_Progress):
        def cancelled(self) -> bool:
            answer = super().cancelled()
            if answer and not cancel_at:
                cancel_at.append(clock.now)  # the pass's reading, taken just before
            return answer

    real_kill = subprocess.Popen.kill

    def kill(process: subprocess.Popen[bytes]) -> None:
        kill_at.append(clock.now)
        real_kill(process)

    monkeypatch.setattr(subprocess.Popen, "kill", kill)
    result, _ = _run(tmp_path, command, _Recording(cancel_after=1))
    assert result.failure is CANCELLED  # the result arrived inside the grace and is kept
    (killed,) = kill_at
    # the first pass at or past the cancel's deadline (the result's reading may add one);
    # timed from the result instead, the kill would come several passes later
    assert grace <= killed - cancel_at[0] <= grace + 1, (cancel_at, kill_at)


def test_the_two_drains_after_a_kill_share_one_window(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, clock: _Clock
) -> None:
    """R2-1: with a grandchild holding both pipes, the stderr tail gets only what is left."""
    monkeypatch.setattr(export_process, "KILL_AFTER_CANCEL_S", 3.0)
    monkeypatch.setattr(export_process, "DRAIN_AFTER_EXIT_S", 4.0)
    waits: list[float] = []
    real_wait = export_process._Tail.wait

    def wait(self: export_process._Tail, timeout: float) -> None:
        waits.append(timeout)
        real_wait(self, timeout)

    monkeypatch.setattr(export_process._Tail, "wait", wait)
    command = _child(
        tmp_path,
        """\
        subprocess.Popen([sys.executable, "-c", "import time; time.sleep(3)"])  # inherits both
        send({"progress": [1, 100, "working"]})
        time.sleep(30)
        """,
    )
    result, _ = _run(tmp_path, command, _Progress(cancel_after=1))
    assert result.failure == "The export worker did not stop after cancel and was ended."
    assert waits == [0.0]  # the stdout's quiet wait used the whole window


def test_a_worker_that_never_reads_its_stdin_is_still_cancelled(
    tmp_path: Path, quick_kill: float
) -> None:
    """The request is written by a thread: a worker that never reads cannot block the job."""
    command = [sys.executable, "-c", "import time; time.sleep(30)"]
    request = _request(tmp_path, padding="p" * (4 << 20))  # far larger than any pipe buffer

    class _CancelInTheConversation(_Progress):
        """Cancels from the 5th check: the 1st and 2nd are ``_run``'s, before the spawn (F11)."""

        calls = 0

        def cancelled(self) -> bool:
            self.calls += 1
            return self.calls >= 5

    result = _jobs(tmp_path, command).job(request)(_CancelInTheConversation())
    assert result.failure == "The export worker did not stop after cancel and was ended."


def test_an_exception_from_the_progress_kills_the_worker(tmp_path: Path) -> None:
    beat = tmp_path / "beat"
    command = _child(
        tmp_path,
        """\
        Path(ARGS[0]).write_text("0")  # the first beat before the progress that raises (F12)
        send({"progress": [1, 100, "working"]})
        for n in range(1, 600):
            Path(ARGS[0]).write_text(str(n))
            time.sleep(0.05)
        """,
        str(beat),
    )

    class _Raising(_Progress):
        def report(self, done: int, total: int | None, message: str) -> None:
            raise RuntimeError("the interface went away")

    with pytest.raises(RuntimeError, match="went away"):
        _run(tmp_path, command, _Raising())
    time.sleep(0.2)
    before = _read_beat(beat)
    time.sleep(0.4)
    assert _read_beat(beat) == before  # the worker is gone, not left running


# --- the child's log records -----------------------------------------------------------------


def test_the_childs_log_records_are_relogged_at_their_level(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    command = _child(
        tmp_path,
        """\
        send({"log": {"level": "WARNING", "name": "clearwater.jobs.export", "message": "careful"}})
        send({"log": {"level": "INFO", "name": "clearwater.jobs.export", "message": "export ok"}})
        result()
        """,
    )
    result, _ = _run(tmp_path, command)
    assert result.ok, result.failure
    records = [r for r in caplog.records if r.name == WORKER_LOGGER]
    assert [(r.levelno, r.getMessage()) for r in records] == [
        (logging.WARNING, "clearwater.jobs.export: careful"),
        (logging.INFO, "clearwater.jobs.export: export ok"),
    ]
    assert WORKER_LOGGER == "clearwater.app.export_worker"


# --- the scratch folder and the sweep --------------------------------------------------------


def test_the_scratch_folder_exists_during_the_job_and_is_removed_after(tmp_path: Path) -> None:
    command = _child(
        tmp_path,
        """\
        folder = Path(REQUEST["cache_folder"])
        (folder / "proxy.bin").write_bytes(b"x" * 100)
        result(warnings=[str(folder.is_dir())])
        """,
    )
    result, _ = _run(tmp_path, command)
    assert result.ok and result.warnings == ("True",)
    assert _scratch_folders(tmp_path) == []
    assert (tmp_path / "cache" / "export").is_dir()


def test_the_stale_sweep_runs_once_in_the_first_jobs_run(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.DEBUG)
    export_folder = tmp_path / "cache" / "export"
    old, fresh = export_folder / "old", export_folder / "fresh"
    for folder in (old, fresh):
        folder.mkdir(parents=True)
        (folder / "proxy.bin").write_bytes(b"x")
    stale = time.time() - STALE_AFTER_S - 600
    os.utime(old, (stale, stale))
    jobs = _jobs(tmp_path, _child(tmp_path, "result()\n"))
    job = jobs.job(_request(tmp_path))
    assert old.exists()  # job() touches no file: the sweep is the run's
    assert job(_Progress()).ok
    assert not old.exists()
    assert fresh.exists()
    assert any("stale" in m for m in _messages(caplog, PROCESS_LOGGER))
    old.mkdir()
    os.utime(old, (stale, stale))
    assert jobs.job(_request(tmp_path))(_Progress()).ok
    assert old.exists()  # once per instance


# --- job(): photos, malformed requests, no file touched --------------------------------------


def test_a_photo_request_is_delegated_without_a_spawn(tmp_path: Path) -> None:
    marker = tmp_path / "spawned"
    command = _child(tmp_path, "Path(ARGS[0]).write_text('x')\nresult()\n", str(marker))
    photo = _PhotoJobs()
    request = _request(tmp_path, kind="photo")
    result = _jobs(tmp_path, command, photo).job(request)(_Progress())
    assert result.outputs == (Path("photo_corrected.png"),)
    assert photo.requests == [request]
    assert not marker.exists()
    assert not (tmp_path / "cache").exists()


def test_job_touches_no_file(tmp_path: Path) -> None:
    marker = tmp_path / "spawned"
    command = _child(tmp_path, "Path(ARGS[0]).write_text('x')\nresult()\n", str(marker))
    before = sorted(tmp_path.rglob("*"))
    _jobs(tmp_path, command).job(_request(tmp_path))
    assert sorted(tmp_path.rglob("*")) == before
    assert not marker.exists()


@pytest.mark.parametrize("field", ["request", "kind", "source", "parameters", "settings"])
def test_job_raises_value_error_for_a_malformed_request(tmp_path: Path, field: str) -> None:
    request = _request(tmp_path)
    bad: object = {
        "request": "not a request",
        "kind": replace(request, kind="audio"),  # type: ignore[arg-type]
        "source": replace(request, source=str(request.source)),  # type: ignore[arg-type]
        "parameters": replace(request, parameters={}),  # type: ignore[arg-type]
        "settings": replace(request, settings={}),  # type: ignore[arg-type]
    }[field]
    photo = _PhotoJobs()
    with pytest.raises(ValueError):
        _jobs(tmp_path, [sys.executable, "-c", "pass"], photo).job(bad)  # type: ignore[arg-type]
    assert photo.requests == []


def test_the_module_imports_no_qt_and_no_app_module() -> None:
    import ast

    tree = ast.parse(Path(export_process.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.add(node.module)
    clearwater = {name for name in imported if name.startswith("clearwater")}
    assert clearwater <= {
        "clearwater.interfaces",
        "clearwater.jobs.export_seam",
        "clearwater.io.video.pipes",
    }, clearwater
    assert not any(name.startswith(("PySide6", "shiboken6", "cupy")) for name in imported)
