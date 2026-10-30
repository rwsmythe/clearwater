"""A test export worker whose video sink holds its first write (WP4.6, ruling R0-STOP-1 (i)).

The process form runs a video export in a worker process, so a test can no longer wrap the
engine's sink in the interface process. This worker is the product worker
(:func:`clearwater.app.export_worker.run`) with one change: its sink's FIRST ``write`` writes the
frame, creates the marker ``writing`` in the marker folder, and then waits until the marker
``release`` exists or the job's cancel flag is set; it creates ``returned`` as the call returns.
Every other call goes to the real sink.

The parent side (a test, or the WP4.6 copy of the V7 driver) points the application's
``ProcessExportJobs`` at :func:`command` and reads the markers with :func:`in_write` and
:func:`release`. Run as ``python tests/export_worker_hold.py <marker folder>``; it takes over its
stdout exactly as the product worker's ``main`` does.
"""

from __future__ import annotations

import os
import sys
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from clearwater.app import composition, export_worker

WRITING = "writing"
RELEASE = "release"
RETURNED = "returned"
HOLD_S = 120.0
"""The longest the first write is held before it fails the export."""

_POLL_S = 0.02


def command(markers: Path) -> tuple[str, ...]:
    """The worker command that holds the first sink write on the markers in ``markers``."""
    return (sys.executable, str(Path(__file__).resolve()), str(markers))


def fresh(markers: Path) -> Path:
    """Create ``markers`` if needed and remove any marker an earlier hold left; return it."""
    markers.mkdir(parents=True, exist_ok=True)
    for name in (WRITING, RELEASE, RETURNED):
        (markers / name).unlink(missing_ok=True)
    return markers


def in_write(markers: Path) -> bool:
    """The first write has begun (its frame written) and has not returned."""
    return (markers / WRITING).exists() and not (markers / RETURNED).exists()


def release(markers: Path) -> None:
    """Let the held write return."""
    (markers / RELEASE).touch()


class _HoldSink:
    """The real sink, its first ``write`` held on the markers or the cancel flag."""

    def __init__(self, inner: Any, markers: Path, cancel: threading.Event) -> None:
        self._inner = inner
        self._markers = markers
        self._cancel = cancel
        self._writes = 0

    def __getattr__(self, name: str) -> Any:
        return getattr(self._inner, name)

    def write(self, frame: Any) -> None:
        self._inner.write(frame)
        self._writes += 1
        if self._writes != 1:
            return
        (self._markers / WRITING).touch()
        try:
            deadline = time.monotonic() + HOLD_S
            while not (self._markers / RELEASE).exists():
                if self._cancel.wait(_POLL_S):
                    return
                if time.monotonic() > deadline:
                    raise TimeoutError("the held sink write was not released")
        finally:
            (self._markers / RETURNED).touch()


def main(argv: Sequence[str] | None = None) -> int:
    """Serve one request as the product worker does, the sink's first write held."""
    (folder,) = list(sys.argv[1:] if argv is None else argv)
    markers = Path(folder)
    sys.stdout.flush()
    protocol = os.fdopen(os.dup(sys.stdout.fileno()), "wb")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    sys.stdout = sys.stderr
    cancel = threading.Event()

    def sink_for(device: Any) -> Any:
        return _HoldSink(composition.video_sink(device), markers, cancel)

    try:
        return export_worker.run(sys.stdin.buffer, protocol, cancel=cancel, sink_for=sink_for)
    finally:
        protocol.close()


if __name__ == "__main__":
    sys.exit(main())
