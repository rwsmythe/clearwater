r"""The export worker process: one video export job outside the interface process (WP4.6).

``python -m clearwater.app.export_worker`` reads ONE request document from its stdin, builds the
export engine through the composition root with its own proxy cache over the request's scratch
folder, runs the job and writes the result. The line protocol, the request's keys and the
parent's side are documented in :mod:`clearwater.jobs.export_process`, which spawns this module.

The worker's channel to the parent is its ORIGINAL stdout, taken over by :func:`main` before
anything else runs: file descriptor 1 and ``sys.stdout`` then point at stderr, so a stray print
reaches the crash tail, never the protocol. Every protocol line is ASCII JSON ended by ``\n``,
written whole under a lock (the engine logs from more than one thread):

- ``{"progress": [done, total, message]}`` for each report of the job;
- ``{"log": {"level", "name", "message"}}`` for each record of the ``clearwater`` loggers at
  INFO and above and of any other logger at WARNING and above;
- ``{"result": {...}}`` once, the job's :class:`~clearwater.interfaces.JobResult`; then exit 0.

The cancel: a stdin thread sets the job's cancel flag on the line ``{"cancel": true}`` or at the
end of the stdin (the parent closed it, or died). The engine stops at its next check and its
safe writing removes the temporary, as in the interface process.

A request that cannot be decoded is exit status 2 with one line on stderr and nothing on the
protocol, before any file is touched. The decoders are the frozen types' own
(``ParameterSet.from_dict``, ``Settings.from_json``): the round trip is exact (N10), with no
migration or repair. This module imports no Qt and no ``cupy``; the GPU backend is reached only
through the composition root's backend selector.
"""

from __future__ import annotations

import json
import logging
import os
import sys
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any, BinaryIO, Literal

from clearwater.app import composition
from clearwater.interfaces import ArrayBackend, JobResult, ParameterSet, Settings, VideoSink
from clearwater.jobs.export_seam import ExportRequest

EXIT_OK = 0
"""The worker wrote its result line (whatever the job's outcome)."""

EXIT_BAD_REQUEST = 2
"""The request document could not be decoded; nothing was written to the protocol."""

LOG_MESSAGE_CHARS = 8192
"""The longest log message carried; a longer one is cut (the parent ignores a line over 64 KiB)."""

_STANDARD_LEVELS = (
    (logging.CRITICAL, "CRITICAL"),
    (logging.ERROR, "ERROR"),
    (logging.WARNING, "WARNING"),
    (logging.INFO, "INFO"),
    (logging.DEBUG, "DEBUG"),
)
"""The five level names the parent accepts, highest first."""

_REQUEST_KEYS = frozenset(
    {
        "format_version",
        "source",
        "kind",
        "parameters",
        "settings",
        "cache_folder",
        "cache_limit_bytes",
        "app_version",
    }
)


@dataclass(frozen=True)
class WorkerRequest:
    """A decoded request document.

    Attributes:
        request: The export request the job runs.
        cache_folder: The job's scratch folder for its own proxy cache (the parent made it).
        cache_limit_bytes: The scratch cache's size limit.
        app_version: The version recorded in provenance.
    """

    request: ExportRequest
    cache_folder: Path
    cache_limit_bytes: int
    app_version: str


class RequestError(ValueError):
    """The request document cannot be decoded; the message says why (one line, no content)."""


def decode_request(line: bytes) -> WorkerRequest:
    r"""Decode one request line (the protocol of :mod:`clearwater.jobs.export_process`).

    Args:
        line: The line as read, with or without its ``\n``.

    Returns:
        The decoded request.

    Raises:
        RequestError: The line is empty, not UTF-8 JSON, not an object with exactly the request
            keys, or a value has the wrong type or is out of range.
    """
    if not line.strip():
        raise RequestError("no request document on stdin")
    try:
        data = json.loads(line.decode("utf-8"))
    except (UnicodeDecodeError, ValueError, RecursionError) as error:
        raise RequestError("the request is not UTF-8 JSON") from error
    if not isinstance(data, dict):
        raise RequestError("the request is not a JSON object")
    keys = set(data)
    if keys != _REQUEST_KEYS:
        missing, unknown = sorted(_REQUEST_KEYS - keys), sorted(keys - _REQUEST_KEYS)
        raise RequestError(f"the request's keys differ (missing {missing}, unknown {unknown})")
    if type(data["format_version"]) is not int or data["format_version"] != 1:  # not 1.0, true
        raise RequestError("the request's format_version is not 1")
    for name in ("source", "cache_folder", "app_version"):
        if not isinstance(data[name], str) or not data[name]:
            raise RequestError(f"the request's {name} is not a non-empty string")
    kind: Literal["photo", "video"]
    if data["kind"] == "video":
        kind = "video"
    elif data["kind"] == "photo":
        kind = "photo"
    else:
        raise RequestError("the request's kind is not photo or video")
    limit = data["cache_limit_bytes"]
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 0:
        raise RequestError("the request's cache_limit_bytes is not a non-negative integer")
    if not isinstance(data["parameters"], dict) or not isinstance(data["settings"], dict):
        raise RequestError("the request's parameters or settings are not objects")
    try:
        parameters = ParameterSet.from_dict(data["parameters"])
    except (ValueError, OverflowError) as error:  # R3-5: a created out of range in UTC
        raise RequestError(f"the request's parameters are not a parameter set: {error}") from error
    try:
        settings = Settings.from_json(json.dumps(data["settings"]))
    except (ValueError, OverflowError) as error:  # B-3: the same, in its last_parameters
        raise RequestError(f"the request's settings are not settings: {error}") from error
    return WorkerRequest(
        request=ExportRequest(
            source=Path(data["source"]), kind=kind, parameters=parameters, settings=settings
        ),
        cache_folder=Path(data["cache_folder"]),
        cache_limit_bytes=limit,
        app_version=data["app_version"],
    )


class _Channel:
    """The protocol stream: whole ASCII JSON lines under a lock; a lost parent means cancel."""

    def __init__(self, stream: BinaryIO, cancel: threading.Event) -> None:
        self._stream = stream
        self._cancel = cancel
        self._lock = threading.Lock()

    def send(self, message: dict[str, Any]) -> None:
        """Write one line; a parent that is gone sets the cancel flag instead of raising."""
        line = json.dumps(message, ensure_ascii=True, allow_nan=False).encode("ascii") + b"\n"
        with self._lock:
            try:
                self._stream.write(line)
                self._stream.flush()
            except (OSError, ValueError):
                self._cancel.set()


class _ProtocolProgress:
    """The job's IF-8 progress: reports become protocol lines; cancel is the stdin flag."""

    def __init__(self, channel: _Channel, cancel: threading.Event) -> None:
        self._channel = channel
        self._cancel = cancel

    def report(self, done: int, total: int | None, message: str) -> None:
        """Send one progress line."""
        self._channel.send({"progress": [done, total, message]})

    def cancelled(self) -> bool:
        """Return True once the parent asked to cancel or closed the stdin."""
        return self._cancel.is_set()


class _ProtocolHandler(logging.Handler):
    """Sends each log record as a protocol ``log`` line (the message only, cut to a bound)."""

    def __init__(self, channel: _Channel) -> None:
        super().__init__(logging.DEBUG)
        self._channel = channel

    def emit(self, record: logging.LogRecord) -> None:
        """Send the record's level, logger name and message.

        The level is the standard one at or below the record's (a custom level would be an
        unknown name to the parent, which ignores such a line).
        """
        try:
            message = record.getMessage()[:LOG_MESSAGE_CHARS]
            level = next((n for v, n in _STANDARD_LEVELS if record.levelno >= v), "DEBUG")
            self._channel.send({"log": {"level": level, "name": record.name, "message": message}})
        except Exception:
            self.handleError(record)


def _watch_stdin(stdin: BinaryIO, cancel: threading.Event) -> None:
    """Set ``cancel`` at the cancel line or at the end of the stdin."""
    try:
        while line := stdin.readline():
            try:
                message = json.loads(line.decode("ascii"))
            except (UnicodeDecodeError, ValueError):
                continue
            if message == {"cancel": True}:
                break
    except (OSError, ValueError):
        pass
    cancel.set()


def _result_message(result: JobResult) -> dict[str, Any]:
    """Return the protocol's ``result`` object of a job result."""
    return {
        "result": {
            "ok": result.ok,
            "outputs": [str(output) for output in result.outputs],
            "warnings": list(result.warnings),
            "failure": result.failure,
            "device": result.device,
            "elapsed_s": result.elapsed_s,
        }
    }


def run(
    stdin: BinaryIO,
    protocol: BinaryIO,
    *,
    cancel: threading.Event | None = None,
    sink_for: Callable[[ArrayBackend | None], VideoSink] | None = None,
) -> int:
    """Serve one request: decode it, run the job, send its lines and its result.

    Args:
        stdin: The parent's stream: the request line, then the cancel line or its end.
        protocol: The stream the protocol lines go to.
        cancel: The job's cancel flag, set by the stdin thread; a new one when None (a test
            worker passes its own to watch it).
        sink_for: Builds the video sink from the job's backend; the composition root's
            ``video_sink`` when None (a test worker wraps it).

    Returns:
        :data:`EXIT_OK` once the result line is written, or :data:`EXIT_BAD_REQUEST` (one line
        on stderr, nothing on ``protocol``).
    """
    try:
        decoded = decode_request(stdin.readline())
    except RequestError as error:
        text = str(error).encode("ascii", "backslashreplace").decode("ascii")
        sys.stderr.write(f"export worker: {text.splitlines()[0] if text else 'bad request'}\n")
        sys.stderr.flush()
        return EXIT_BAD_REQUEST
    flag = cancel if cancel is not None else threading.Event()
    channel = _Channel(protocol, flag)
    threading.Thread(
        target=_watch_stdin, args=(stdin, flag), name="export-worker-cancel", daemon=True
    ).start()
    handler = _ProtocolHandler(channel)
    root, package = logging.getLogger(), logging.getLogger("clearwater")
    saved = root.level, package.level
    root.addHandler(handler)
    root.setLevel(logging.WARNING)
    package.setLevel(logging.INFO)
    try:
        options: dict[str, Any] = {} if sink_for is None else {"sink_for": sink_for}
        engine = composition.export_jobs(
            app_version=decoded.app_version,
            cache_folder=decoded.cache_folder,
            cache_limit_bytes=decoded.cache_limit_bytes,
            **options,
        )
        result = engine.job(decoded.request)(_ProtocolProgress(channel, flag))
        channel.send(_result_message(result))
    finally:
        root.removeHandler(handler)
        root.setLevel(saved[0])
        package.setLevel(saved[1])
    return EXIT_OK


def main(argv: Sequence[str] | None = None) -> int:
    """Run the worker as a process: take over stdout for the protocol, then serve one request.

    Args:
        argv: The arguments after the module name; the worker takes none.

    Returns:
        The exit status: :data:`EXIT_OK` or :data:`EXIT_BAD_REQUEST`.
    """
    arguments = list(sys.argv[1:] if argv is None else argv)
    if arguments:
        sys.stderr.write("export worker: takes no arguments\n")
        return EXIT_BAD_REQUEST
    sys.stdout.flush()
    protocol = os.fdopen(os.dup(sys.stdout.fileno()), "wb")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    sys.stdout = sys.stderr
    try:
        return run(sys.stdin.buffer, protocol)
    finally:
        protocol.close()


if __name__ == "__main__":
    sys.exit(main())
