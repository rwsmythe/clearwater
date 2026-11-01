r"""The export job in a spawned worker process: the interface process's side (WP4.6, AD-23).

:class:`ProcessExportJobs` is an :class:`~clearwater.jobs.export_seam.ExportJobs` whose VIDEO
jobs run in a separate Python process (the worker, ``python -m clearwater.app.export_worker``),
so the export's compute threads and FFmpeg's pipes leave the interface process (V7, DR-98).
Photo jobs are handed to the in-process engine it is given. The job callable runs on the GUI
runner's worker thread as any IF-8 job does; that thread only waits on a queue, forwards small
reports and delivers the cancel.

One job, one worker. The job's run:

1. returns :data:`~clearwater.jobs.export_seam.CANCELLED` at once when the cancel was asked
   before the start (nothing is spawned, no folder is made);
2. on the instance's first run only, removes the scratch folders under ``<cache_dir>/export``
   older than :data:`STALE_AFTER_S` (a worker that was killed leaves its folder behind), then
   returns ``CANCELLED`` as in step 1 when the cancel was asked during that sweep (which stops
   before its next entry);
3. encodes the request document, creates the job's scratch folder
   ``<cache_dir>/export/<uuid4 hex>`` (the worker's own proxy cache: two processes never share
   one cache folder) and spawns the worker through AD-23's ``tool_spawn_kwargs()``;
4. writes the request on a stdin thread and reads the worker's protocol lines until the worker
   has exited and its output has ended (or stayed quiet :data:`DRAIN_AFTER_EXIT_S` after the
   exit), checking ``progress.cancelled()`` every :data:`POLL_S`;
5. removes the scratch folder (kept when the worker was killed: a grandchild may still hold a
   file in it) and returns the :class:`~clearwater.interfaces.JobResult`.

The protocol. Every line, both ways, is one JSON object written with ``ensure_ascii`` (pure
ASCII bytes, any other character as a ``\uXXXX`` escape) on the BINARY streams and ended by
``\n``; the reader decodes it strictly as UTF-8 and tolerates one ``\r`` before the ``\n``.

Parent to worker (the worker's stdin):

- the request document, once, first: ``{"format_version": 1, "source": <absolute path>,
  "kind": "video", "parameters": <ParameterSet.to_dict()>, "settings": <the Settings.to_json()
  object>, "cache_folder": <the scratch folder>, "cache_limit_bytes": <the request's settings'
  limit>, "app_version": <str>}``;
- :data:`CANCEL_LINE` once the cancel is asked, after which the parent closes the stdin; the
  end of the stdin (also when the parent dies) means cancel too.

Worker to parent (the worker's stdout; its stderr is kept only for the crash tail, which goes
to the application log, never into a failure text):

- ``{"progress": [done, total or null, message]}``: forwarded to ``progress.report`` only when
  ``0 <= done <= PROGRESS_MAX`` and ``total`` is null or ``0 <= total <= PROGRESS_MAX``; a
  ``done > total`` is forwarded as ``total`` with the message unchanged, the first such line
  in a job logged at WARNING with its counts (CHARC 89a98d58: the engine counts written frames
  against the container's declared count);
- ``{"log": {"level": <DEBUG|INFO|WARNING|ERROR|CRITICAL>, "name": <logger>, "message":
  <text>}}``: re-logged under :data:`WORKER_LOGGER` at that level as ``"<name>: <message>"``;
- ``{"result": {"ok": bool, "outputs": [str], "warnings": [str], "failure": str or null,
  "device": str, "elapsed_s": number}}``: the job's outcome, then the worker exits 0.

The parent is strict: a line that is not UTF-8, not JSON, not an object with exactly one of the
three keys, of the wrong shape or types, holds a non-finite number or an integer too large for
a float, is longer than :data:`MAX_LINE_BYTES` or has no ``\n`` at the end of the output is
IGNORED and logged by its reason (never its content); a rejected progress line is logged once
per job (CHARC bc6847dd: the process form is a trust boundary, so no worker can make the
interface thread's Qt call raise). Only the FIRST result counts (a later one is logged); a result
followed by a non-zero exit is still the result (the status is logged); a worker still running
:data:`KILL_AFTER_CANCEL_S` after its result (or after the cancel line, when that came first)
is killed (logged) and the result kept. The result's ``elapsed_s`` is the parent's own measure,
spawn included; a ``failure`` equal to
:data:`~clearwater.jobs.export_seam.CANCELLED` is returned as the constant itself.

The failure texts (ASCII, none equal to ``CANCELLED``) carry NO text of the worker's stderr
and no error message (CHARC rulings 55959e2f and 3ed8335f): the details, which may name full
paths, go to the application log at WARNING under :data:`WORKER_LOGGER`, which is local.

- :data:`ENDED_TEXT`: the worker exited without a valid result; its stderr tail (the last
  :data:`STDERR_TAIL_BYTES`, verbatim) is logged. When the tail's last line is an exception line
  (:data:`EXCEPTION_LINE`), its TYPE NAME alone follows the text after a newline; ``device`` is
  ``"unknown"``;
- :data:`KILLED_TEXT`: the worker had not exited :data:`KILL_AFTER_CANCEL_S` after the cancel
  line and was killed; ``device`` ``"unknown"``. ``Popen.kill`` ends the worker but not a
  process the worker started: an FFmpeg grandchild ends when its pipes break, and a temporary
  file left behind is the next start's leftover (D85);
- :data:`START_TEXT`: the scratch folder or the worker could not be made: the error's type name
  and its errno (when it has one); the error's own text is logged; ``device`` ``"none"``;
- :data:`ENCODE_TEXT`: the request holds a value JSON cannot carry (a non-finite number): the
  error's type name; its text is logged; nothing is spawned; ``device`` ``"none"``.

This module imports only the standard library, ``clearwater.interfaces``, the export seam and
``io/video/pipes.py``'s launch policy: no Qt and no ``clearwater.app`` module (the worker is
named by the command the composition root passes in).
"""

from __future__ import annotations

import contextlib
import json
import logging
import math
import queue
import re
import shutil
import subprocess
import threading
import time
import uuid
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import IO, Any, NamedTuple

from clearwater.interfaces import JobResult, ParameterSet, Progress, Settings
from clearwater.io.video.pipes import tool_spawn_kwargs
from clearwater.jobs.export_seam import CANCELLED, ExportJobs, ExportRequest

_LOG = logging.getLogger(__name__)

FORMAT_VERSION = 1
"""The request document's ``format_version``."""

SCRATCH_FOLDER = "export"
"""The folder under the cache folder that holds one scratch folder per running job."""

KILL_AFTER_CANCEL_S = 3.0
"""Seconds a worker has to exit after the cancel line or its result, whichever came first.

Under the interface's ``SHUTDOWN_TIMEOUT_S`` (5.0), so a close during an export still ends in time.
"""

POLL_S = 0.05
"""How often the job thread checks ``progress.cancelled()`` while it waits for a line."""

DRAIN_AFTER_EXIT_S = 1.0
"""How long the output may stay quiet after the worker exited before the job stops reading it.

The worker's last lines arrive after its exit; a grandchild holding the output open must not
hold the job.
"""

PROGRESS_MAX = 2**31 - 1
"""The largest progress count forwarded: Qt's int (CHARC bc6847dd, a trust boundary)."""

MAX_LINE_BYTES = 64 * 1024
"""The longest protocol line accepted, without its ``\\n``; a longer one is ignored."""

STDERR_TAIL_BYTES = 4096
"""The most of the worker's stderr kept and logged when it ends without a result."""

STALE_AFTER_S = 3600.0
"""A scratch folder older than this (by its modification time) is removed by the sweep."""

CANCEL_LINE = b'{"cancel": true}\n'
"""The line the parent writes to the worker's stdin when the job is cancelled."""

WORKER_LOGGER = "clearwater.app.export_worker"
"""The logger the worker's own log records are re-logged under, in the interface process."""

ENDED_TEXT = (
    "The export worker ended without a result (exit status {status}); "
    "details are in the application log."
)
"""The failure text of a worker that exited without a valid result line."""

EXCEPTION_LINE = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*(Error|Exception|Exit|Interrupt)(: .*)?$")
"""A last stderr line whose identifier before the colon is added to :data:`ENDED_TEXT` (only it)."""

KILLED_TEXT = "The export worker did not stop after cancel and was ended."
"""The failure text of a worker killed after it ignored the cancel."""

START_TEXT = (
    "The export worker could not be started ({reason}); details are in the application log."
)
"""The failure text of a scratch folder or a worker process that could not be made.

``reason`` is the error's type name, then ``, errno N`` when it has an errno.
"""

ENCODE_TEXT = (
    "The export request could not be encoded ({reason}); details are in the application log."
)
"""The failure text of a request JSON cannot carry (nothing is spawned); ``reason`` as above."""

_LEVELS = {
    "DEBUG": logging.DEBUG,
    "INFO": logging.INFO,
    "WARNING": logging.WARNING,
    "ERROR": logging.ERROR,
    "CRITICAL": logging.CRITICAL,
}
_RESULT_KEYS = frozenset({"ok", "outputs", "warnings", "failure", "device", "elapsed_s"})
_LOG_KEYS = frozenset({"level", "name", "message"})

_WORKER_LOG = logging.getLogger(WORKER_LOGGER)


class _InvalidLineError(Exception):
    """A protocol line the parent ignores; the message is the reason (never the content)."""


class _InvalidProgressError(_InvalidLineError):
    """A ``progress`` line the parent ignores (logged once per job, CHARC bc6847dd)."""


class _ChildResult(NamedTuple):
    """A valid result line, before it becomes a :class:`JobResult`."""

    ok: bool
    outputs: tuple[str, ...]
    warnings: tuple[str, ...]
    failure: str | None
    device: str
    elapsed_s: float


class _Outcome(NamedTuple):
    """How a conversation with the worker ended."""

    result: _ChildResult | None
    killed: bool
    status: int
    stderr_tail: str


class ProcessExportJobs:
    """The export engine whose video jobs run in a spawned worker process (WP4.6).

    Args:
        photo_exports: The in-process engine photo requests are handed to unchanged.
        cache_dir: The application's cache folder; each video job's scratch folder is made
            under ``cache_dir / "export"``.
        app_version: The version the worker records in provenance.
        command: The worker's command line (``[sys.executable, "-m",
            "clearwater.app.export_worker"]`` in the product; a fake in tests).

    Raises:
        ValueError: ``command`` is empty.
    """

    def __init__(
        self,
        *,
        photo_exports: ExportJobs,
        cache_dir: Path,
        app_version: str,
        command: Sequence[str],
    ) -> None:
        """Keep the engine and the folders; nothing is spawned until a video job runs."""
        if not command:
            raise ValueError("the worker command is empty")
        self._photo_exports = photo_exports
        self._cache_dir = cache_dir
        self._app_version = app_version
        self._command = tuple(command)
        self._swept = False
        self._sweep_lock = threading.Lock()

    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]:
        """Return the IF-8 job that exports ``request`` (the ``ExportJobs`` contract).

        Touches no file. A photo request is the in-process engine's job; a video request's job
        spawns the worker when it runs.

        Args:
            request: What to export.

        Returns:
            The job.

        Raises:
            ValueError: The request is malformed in itself (a kind other than ``"photo"`` or
                ``"video"``, or a field of the wrong type).
        """
        _check_request(request)
        if request.kind == "photo":
            return self._photo_exports.job(request)

        def run(progress: Progress) -> JobResult:
            return self._run(request, progress)

        return run

    # --- the video job ------------------------------------------------------------------------

    def _run(self, request: ExportRequest, progress: Progress) -> JobResult:
        """Run one video job in a worker and return its result."""
        start = time.perf_counter()
        if progress.cancelled():
            return _failed(CANCELLED, "none", start)
        self._sweep_once(progress)
        if progress.cancelled():  # asked during the sweep: still nothing spawned
            return _failed(CANCELLED, "none", start)
        scratch = self._cache_dir / SCRATCH_FOLDER / uuid.uuid4().hex
        try:
            line = self._request_line(request, scratch)
        except (ValueError, TypeError) as error:
            _log_error("the export request could not be encoded", error)
            return _failed(ENCODE_TEXT.format(reason=_reason(error)), "none", start)
        try:
            scratch.mkdir(parents=True)
            process = subprocess.Popen(
                list(self._command),
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                **tool_spawn_kwargs(),
            )
        except (OSError, ValueError) as error:
            _remove(scratch)
            _log_error("the export worker could not be started", error)
            return _failed(START_TEXT.format(reason=_reason(error)), "none", start)
        outcome = _converse(process, progress, line)
        if outcome.killed:
            _LOG.warning("export worker killed; its scratch folder %s is kept", scratch.name)
        else:
            _remove(scratch)
        if outcome.result is None:
            if outcome.killed:
                return _failed(KILLED_TEXT, "unknown", start)
            _WORKER_LOG.warning(
                "export worker stderr (the last %d bytes; it ended without a result, "
                "exit status %d):\n%s",
                STDERR_TAIL_BYTES,
                outcome.status,
                outcome.stderr_tail,
            )
            text = ENDED_TEXT.format(status=outcome.status)
            if error_type := _exception_type(outcome.stderr_tail):
                text = f"{text}\n{error_type}"
            return _failed(text, "unknown", start)
        child = outcome.result
        if outcome.status != 0 and not outcome.killed:
            _LOG.warning("export worker sent its result, then exit status %d", outcome.status)
        elapsed = time.perf_counter() - start
        _LOG.debug("export worker reported %.3f s; measured %.3f s", child.elapsed_s, elapsed)
        return JobResult(
            ok=child.ok,
            outputs=tuple(Path(output) for output in child.outputs),
            warnings=child.warnings,
            failure=CANCELLED if child.failure == CANCELLED else child.failure,
            device=child.device,
            elapsed_s=elapsed,
        )

    def _request_line(self, request: ExportRequest, scratch: Path) -> bytes:
        """Return the request document as one ASCII line.

        Raises:
            ValueError: A value is a non-finite float, or ``created`` is not timezone-aware.
            TypeError: A parameter value is not JSON-native.
        """
        document = {
            "format_version": FORMAT_VERSION,
            "source": str(request.source.absolute()),
            "kind": request.kind,
            "parameters": request.parameters.to_dict(),
            "settings": json.loads(request.settings.to_json()),
            "cache_folder": str(scratch.absolute()),
            "cache_limit_bytes": request.settings.cache_limit_bytes,
            "app_version": self._app_version,
        }
        return json.dumps(document, ensure_ascii=True, allow_nan=False).encode("ascii") + b"\n"

    def _sweep_once(self, progress: Progress) -> None:
        """Remove stale scratch folders, on this instance's first job only (logged).

        Bounded by the folder's entry count and by a cancel, which is checked before each
        entry: a removal already begun runs to its end, and the entries left by a cancel stay
        until another instance's first job.
        """
        with self._sweep_lock:
            if self._swept:
                return
            self._swept = True
        folder = self._cache_dir / SCRATCH_FOLDER
        try:
            entries = sorted(folder.iterdir())
        except FileNotFoundError:
            return
        except OSError as error:
            _LOG.warning("the export scratch folders could not be listed: %s", type(error).__name__)
            return
        cutoff = time.time() - STALE_AFTER_S
        removed = 0
        for entry in entries:
            if progress.cancelled():
                _LOG.info("the stale export scratch sweep stopped at a cancel")
                break
            try:
                if entry.is_symlink() or not entry.is_dir() or entry.stat().st_mtime >= cutoff:
                    continue
                shutil.rmtree(entry)
                removed += 1
            except OSError as error:
                _LOG.warning(
                    "the stale export scratch folder %s could not be removed: %s",
                    entry.name,
                    type(error).__name__,
                )
        if removed:
            _LOG.info("removed %d stale export scratch folder(s)", removed)


# --- the conversation with one worker ---------------------------------------------------------


def _converse(
    process: subprocess.Popen[bytes], progress: Progress, request_line: bytes
) -> _Outcome:
    """Send the request, forward the worker's lines and deliver the cancel until it has ended.

    Three daemon threads do the blocking I/O (stdin writes, stdout lines, the stderr tail), so
    this thread only waits on a queue for at most :data:`POLL_S` at a time. An exception that
    escapes (a ``progress.report`` that raises, a failure while the conversation is set up, or
    a thread that cannot start) kills the worker first: it never outlives its job. A pipe whose
    thread never started is closed here.
    """
    stdin, stdout, stderr = process.stdin, process.stdout, process.stderr
    assert stdin is not None and stdout is not None and stderr is not None  # all three are PIPE
    started = 0  # the I/O threads started, in pipe order; each closes its own pipe from then on
    try:
        lines: queue.Queue[tuple[str, Any]] = queue.Queue()
        writes: queue.Queue[bytes | None] = queue.Queue()
        tail = _Tail()
        result: _ChildResult | None = None
        result_at: float | None = None
        cancel_at: float | None = None
        quiet_since: float | None = None  # the worker has exited: when its output last moved
        ended = killed = progress_warned = False
        for target, args, name in (
            (_write_lines, (stdin, writes), "export-worker-stdin"),
            (_read_lines, (stdout, lines), "export-worker-stdout"),
            (tail.drain, (stderr,), "export-worker-stderr"),
        ):
            threading.Thread(target=target, args=args, name=name, daemon=True).start()
            started += 1
        writes.put(request_line)
        while True:
            kind: str | None
            try:
                kind, payload = lines.get(timeout=POLL_S)
            except queue.Empty:
                kind, payload = None, None
            if kind == "end":
                ended = True
            elif kind == "invalid":
                _LOG.warning("export worker line ignored: %s", payload)
            elif kind == "invalid progress" and not progress_warned:
                progress_warned = True  # once per job (CHARC bc6847dd)
                _LOG.warning(
                    "export worker progress line ignored: %s (later ones in this job unlogged)",
                    payload,
                )
            elif kind == "progress":
                progress.report(*payload)
            elif kind == "log":
                level, name, message = payload
                _WORKER_LOG.log(level, "%s: %s", name, message)
            elif kind == "result" and result is None:
                result, result_at = payload, time.monotonic()
                writes.put(None)
            elif kind == "result":
                _LOG.warning("export worker sent a second result; ignored")
            now = time.monotonic()
            if result is None and cancel_at is None and progress.cancelled():
                writes.put(CANCEL_LINE)
                writes.put(None)
                cancel_at = now
            status = process.poll()
            if status is None:
                # The grace runs from the EARLIER trigger: a cancel line is only ever sent
                # before a result, so a result after the cancel never restarts it.
                trigger, grace_from = (
                    ("cancel", cancel_at) if cancel_at is not None else ("result", result_at)
                )
                if grace_from is None or now - grace_from < KILL_AFTER_CANCEL_S:
                    continue
                process.kill()
                status = process.wait()
                killed = True
                _LOG.warning(
                    "export worker killed: still running %.1f s after its %s",
                    KILL_AFTER_CANCEL_S,
                    trigger,
                )
            if ended:
                break
            if quiet_since is None or kind is not None:
                quiet_since = now
            elif now - quiet_since >= DRAIN_AFTER_EXIT_S:
                _LOG.warning("export worker output still open after its exit; no longer waited for")
                break
    except BaseException:
        process.kill()
        process.wait()
        if started:  # the stdin thread runs: it closes the pipe on the None
            writes.put(None)
        for stream in (stdin, stdout, stderr)[started:]:
            with contextlib.suppress(OSError, ValueError):
                stream.close()
        raise
    writes.put(None)
    # One drain window for both outputs (R2-1): the stderr gets what the stdout's wait left of it
    drain_from = quiet_since if quiet_since is not None else time.monotonic()
    tail.wait(max(0.0, drain_from + DRAIN_AFTER_EXIT_S - time.monotonic()))
    return _Outcome(result, killed, status, tail.text())


def _write_lines(stdin: IO[bytes], writes: queue.Queue[bytes | None]) -> None:
    """Write each queued line to the worker's stdin; ``None`` closes it and ends the thread.

    A worker that has already gone is not an error here: its exit is reported instead.
    """
    try:
        while (data := writes.get()) is not None:
            stdin.write(data)
            stdin.flush()
    except (OSError, ValueError) as error:
        _LOG.debug("the export worker's stdin is gone: %s", _reason(error))
    finally:
        try:
            stdin.close()
        except (OSError, ValueError) as error:
            _LOG.debug("the export worker's stdin could not be closed: %s", _reason(error))


def _read_lines(stream: IO[bytes], lines: queue.Queue[tuple[str, Any]]) -> None:
    """Read the worker's stdout into ``lines`` until it ends, then put ``("end", None)``.

    A line whose decode fails in any way is put as ``("invalid", reason)``; it never ends the
    reading, so a valid line after it still arrives. A progress line with ``done > total`` is
    put with ``done`` clamped to ``total`` and its message unchanged; the first in the job is
    logged at WARNING with its counts (CHARC 89a98d58).
    """
    limit = MAX_LINE_BYTES + 2  # room for the "\r\n" of a line at the limit
    clamp_warned = False  # one reader per job: the clamp's own once-per-job WARNING
    try:
        while chunk := stream.readline(limit):
            if not chunk.endswith(b"\n"):
                if len(chunk) < limit:  # the output ended inside the line
                    lines.put(("invalid", f"an unterminated last line of {len(chunk)} bytes"))
                    continue
                while (rest := stream.readline(limit)) and not rest.endswith(b"\n"):
                    pass  # skip the rest of the over-long line
                lines.put(("invalid", f"a line longer than {MAX_LINE_BYTES} bytes"))
                continue
            content = chunk[:-1].removesuffix(b"\r")
            if len(content) > MAX_LINE_BYTES:
                lines.put(("invalid", f"a line longer than {MAX_LINE_BYTES} bytes"))
                continue
            try:
                kind, payload = _decode_line(content)
                if kind == "progress" and payload[1] is not None and payload[0] > payload[1]:
                    done, total, message = payload  # bounded already: the clamp comes after
                    if not clamp_warned:
                        clamp_warned = True  # once per job (CHARC 89a98d58)
                        _LOG.warning(
                            "export worker progress done %d > total %d clamped to %d"
                            " (later ones in this job unlogged)",
                            done,
                            total,
                            total,
                        )
                    payload = (total, total, message)
                lines.put((kind, payload))
            except _InvalidProgressError as error:
                lines.put(("invalid progress", str(error)))
            except _InvalidLineError as error:
                lines.put(("invalid", str(error)))
            except Exception as error:  # one line never ends the reader: no later line is lost
                reason = f"a line that could not be decoded ({type(error).__name__})"
                lines.put(("invalid", reason))
    except (OSError, ValueError) as error:
        lines.put(("invalid", f"the output could not be read: {type(error).__name__}"))
    finally:
        lines.put(("end", None))
        with contextlib.suppress(OSError):
            stream.close()


def _reject_constant(name: str) -> float:
    """Refuse the JSON extensions ``NaN``, ``Infinity`` and ``-Infinity``."""
    raise _InvalidLineError(f"a non-finite number ({name})")


def _finite_float(text: str) -> float:
    """Parse a JSON number, refusing one too large for a finite float."""
    value = float(text)
    if not math.isfinite(value):
        raise _InvalidLineError("a non-finite number")
    return value


def _decode_line(content: bytes) -> tuple[str, Any]:
    r"""Return ``(kind, payload)`` for one protocol line without its ``\n``.

    Raises:
        _InvalidLineError: The line is not a valid protocol line (the message says why).
    """
    try:
        text = content.decode("utf-8")
    except UnicodeDecodeError as error:
        raise _InvalidLineError("not UTF-8") from error
    try:
        data = json.loads(text, parse_constant=_reject_constant, parse_float=_finite_float)
    except (ValueError, RecursionError) as error:
        raise _InvalidLineError("not JSON") from error
    if not isinstance(data, dict) or len(data) != 1:
        raise _InvalidLineError("not an object with exactly one key")
    ((key, value),) = data.items()
    if key == "progress":
        return key, _decode_progress(value)
    if key == "log":
        return key, _decode_log(value)
    if key == "result":
        return key, _decode_result(value)
    # CHARC e15d408a (F6): the key's length and at most its first 8 characters, never more
    raise _InvalidLineError(f"an unknown key of {len(key)} characters, first {_ascii(key[:8])!r}")


def _is_int(value: object) -> bool:
    """Whether ``value`` is a JSON integer (``bool`` is not)."""
    return isinstance(value, int) and not isinstance(value, bool)


def _float_safe(value: int | float) -> float:
    """Return a JSON number as a float; an integer too large for one makes the line invalid.

    The one rule for every number the parent decodes (CHARC e15d408a: such a line is ignored and
    logged by its reason; R1 F3 for ``elapsed_s``, B-1 for the progress counts).
    """
    try:
        return float(value)
    except OverflowError as error:
        raise _InvalidLineError("an integer too large for a float") from error


def _is_texts(value: object) -> bool:
    """Whether ``value`` is a JSON array of strings."""
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def _decode_progress(value: object) -> tuple[int, int | None, str]:
    """Check a ``progress`` payload: ``[done, total or null, message]`` within the bound.

    ``done > total`` passes unchanged; the reader clamps it (CHARC 89a98d58).

    Raises:
        _InvalidProgressError: The payload is malformed, a count is not float-convertible, or
            ``0 <= done <= PROGRESS_MAX`` fails, or ``0 <= total <= PROGRESS_MAX`` fails for a
            ``total`` that is not null.
    """
    if not isinstance(value, list) or len(value) != 3:
        raise _InvalidProgressError("a progress line that is not [done, total, message]")
    done, total, message = value
    if not _is_int(done) or not (total is None or _is_int(total)) or not isinstance(message, str):
        raise _InvalidProgressError("a progress line with a value of the wrong type")
    try:
        _float_safe(done)
        if total is not None:
            _float_safe(total)
    except _InvalidLineError as error:
        raise _InvalidProgressError(str(error)) from error
    if not 0 <= done <= PROGRESS_MAX or not (total is None or 0 <= total <= PROGRESS_MAX):
        raise _InvalidProgressError(f"a progress count outside 0 <= count <= {PROGRESS_MAX}")
    return done, total, message


def _decode_log(value: object) -> tuple[int, str, str]:
    """Check a ``log`` payload and return ``(level number, logger name, message)``."""
    if not isinstance(value, dict) or set(value) != _LOG_KEYS:
        raise _InvalidLineError("a log line without exactly level, name and message")
    level, name, message = value["level"], value["name"], value["message"]
    if (
        not isinstance(name, str)
        or not isinstance(message, str)
        or not isinstance(level, str)  # first: a list or an object cannot be looked up
        or level not in _LEVELS
    ):
        raise _InvalidLineError("a log line with a value of the wrong type or level")
    return _LEVELS[level], name, message


def _decode_result(value: object) -> _ChildResult:
    """Check a ``result`` payload: exactly the six :class:`JobResult` fields, each typed."""
    if not isinstance(value, dict) or set(value) != _RESULT_KEYS:
        raise _InvalidLineError("a result line without exactly the six result fields")
    ok, outputs, warnings = value["ok"], value["outputs"], value["warnings"]
    failure, device, elapsed = value["failure"], value["device"], value["elapsed_s"]
    if (
        not isinstance(ok, bool)
        or not _is_texts(outputs)
        or not _is_texts(warnings)
        or not (failure is None or isinstance(failure, str))
        or not isinstance(device, str)
        or isinstance(elapsed, bool)
        or not isinstance(elapsed, int | float)
    ):
        raise _InvalidLineError("a result line with a value of the wrong type")
    seconds = _float_safe(elapsed)
    return _ChildResult(ok, tuple(outputs), tuple(warnings), failure, device, seconds)


class _Tail:
    """The last :data:`STDERR_TAIL_BYTES` of the worker's stderr, drained by its own thread."""

    def __init__(self) -> None:
        self._data = bytearray()
        self._lock = threading.Lock()
        self._done = threading.Event()

    def drain(self, stream: IO[bytes]) -> None:
        """Read ``stream`` to its end, keeping only the tail, so the pipe never fills."""
        read = getattr(stream, "read1", stream.read)
        try:
            while chunk := read(65536):
                with self._lock:
                    self._data += chunk
                    if len(self._data) > 2 * STDERR_TAIL_BYTES:
                        del self._data[:-STDERR_TAIL_BYTES]
        except (OSError, ValueError) as error:
            _LOG.debug("the export worker's stderr could not be read: %s", _reason(error))
        finally:
            with contextlib.suppress(OSError):
                stream.close()
            self._done.set()

    def wait(self, timeout: float) -> None:
        """Wait up to ``timeout`` seconds for the stderr to end (a grandchild may hold it)."""
        self._done.wait(timeout)

    def text(self) -> str:
        """Return the tail as text, verbatim (undecodable bytes replaced): it goes to the log."""
        with self._lock:
            data = bytes(self._data[-STDERR_TAIL_BYTES:])
        return data.decode("utf-8", "replace")


# --- helpers ----------------------------------------------------------------------------------


def _check_request(request: ExportRequest) -> None:
    """Raise ``ValueError`` for a request malformed in itself (the in-process engine's rules)."""
    if not isinstance(request, ExportRequest):
        raise ValueError(f"not an export request: {type(request).__name__}")
    if request.kind not in ("photo", "video"):
        raise ValueError(f"unknown export kind {request.kind!r}")
    if not isinstance(request.source, Path):
        raise ValueError(f"the source must be a Path, got {type(request.source).__name__}")
    if not isinstance(request.parameters, ParameterSet):
        raise ValueError("the parameters must be a ParameterSet")
    if not isinstance(request.settings, Settings):
        raise ValueError("the settings must be a Settings")


def _failed(failure: str, device: str, start: float) -> JobResult:
    """Return a failed result with nothing written."""
    return JobResult(
        ok=False,
        outputs=(),
        warnings=(),
        failure=failure,
        device=device,
        elapsed_s=time.perf_counter() - start,
    )


def _remove(folder: Path) -> None:
    """Remove a scratch folder; a failure is logged by the folder's name and left to the sweep."""
    try:
        shutil.rmtree(folder)
    except FileNotFoundError:
        pass
    except OSError as error:
        _LOG.warning(
            "the export scratch folder %s could not be removed: %s",
            folder.name,
            type(error).__name__,
        )


def _ascii(text: str) -> str:
    """Return ``text`` with every non-ASCII character as a backslash escape."""
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _reason(error: BaseException) -> str:
    """Return the error's type name, then ``, errno N`` when it has one (never its message)."""
    errno = getattr(error, "errno", None)
    name = type(error).__name__
    return f"{name}, errno {errno}" if isinstance(errno, int) else name


def _log_error(what: str, error: BaseException) -> None:
    """Log ``error``'s own text (which may name full paths) under :data:`WORKER_LOGGER`."""
    _WORKER_LOG.warning("%s: %s: %s", what, type(error).__name__, error)


def _exception_type(tail: str) -> str | None:
    """Return the exception's type name when the tail's last line is an exception line."""
    lines = tail.splitlines()
    match = EXCEPTION_LINE.match(lines[-1]) if lines else None
    return match.group(0).partition(":")[0] if match else None
