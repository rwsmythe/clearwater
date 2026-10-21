"""The Qt runner for IF-8 jobs (G9): worker threads, coalesced reports, main-thread callbacks.

Each :meth:`QtJobRunner.run` starts one daemon thread. The job's :class:`QtProgress` stores the
latest report under a lock and posts at most one queued delivery at a time, so a job reporting
at any rate costs the interface thread one event per delivery, never a backlog (V7). The last
report is always delivered before ``on_done``. The job runs on its thread and must not touch a
Qt object.
"""

from __future__ import annotations

import contextlib
import logging
import threading
import time
from collections.abc import Callable

from PySide6.QtCore import QObject, Qt, Signal

from clearwater.interfaces import JobResult, Progress

_LOG = logging.getLogger(__name__)

type ProgressCallback = Callable[[int, int | None, str], None]
"""Receives ``(done, total, message)`` on the main thread."""


class QtProgress:
    """IF-8 ``Progress`` for one job: reports coalesced to the main thread, a cancel flag."""

    def __init__(self, post: Callable[[], None]) -> None:
        """Create the progress object.

        Args:
            post: Posts one queued delivery to the main thread (called from the job thread).
        """
        self._post = post
        self._lock = threading.Lock()
        self._latest: tuple[int, int | None, str] | None = None
        self._sequence = 0
        self._delivered = 0
        self._posted = False
        self._cancel = threading.Event()

    def report(self, done: int, total: int | None, message: str) -> None:
        """Record a report; post a delivery unless one is already waiting.

        Args:
            done: Units completed so far.
            total: Total units, or None when unknown.
            message: A short status message.
        """
        with self._lock:
            self._latest = (done, total, message)
            self._sequence += 1
            if self._posted:
                return
            self._posted = True
        self._post()

    def cancelled(self) -> bool:
        """Return True once the job has been cancelled."""
        return self._cancel.is_set()

    def cancel(self) -> None:
        """Set the cancel flag."""
        self._cancel.set()

    def take(self) -> tuple[int, int | None, str] | None:
        """Main thread: return the latest undelivered report, or None; re-arm posting."""
        with self._lock:
            self._posted = False
            if self._latest is None or self._delivered == self._sequence:
                return None
            self._delivered = self._sequence
            return self._latest


class QtJobHandle:
    """The handle of one job (implements ``clearwater.gui.contract.JobHandle``)."""

    def __init__(
        self,
        progress: QtProgress,
        on_done: Callable[[JobResult], None],
        on_progress: ProgressCallback | None,
    ) -> None:
        """Create the handle.

        Args:
            progress: The job's progress object.
            on_done: The completion callback.
            on_progress: The progress callback, or None.
        """
        self.progress = progress
        self.on_done = on_done
        self.on_progress = on_progress
        self.thread: threading.Thread | None = None
        self._running = True

    def cancel(self) -> None:
        """Ask the job to stop: ``Progress.cancelled()`` returns True from now on."""
        self.progress.cancel()

    def is_running(self) -> bool:
        """Return True until ``on_done`` has been called."""
        return self._running

    def finish(self) -> None:
        """Mark the job done (main thread)."""
        self._running = False


class _Bridge(QObject):
    """Lives on the main thread; carries job events by queued connections."""

    progressed = Signal(object)
    finished = Signal(object, object)


class QtJobRunner:
    """Runs IF-8 jobs on worker threads (implements ``clearwater.gui.contract.JobRunner``)."""

    def __init__(self) -> None:
        """Create the runner (main thread)."""
        self._bridge = _Bridge()
        self._bridge.progressed.connect(self._on_progressed, Qt.ConnectionType.QueuedConnection)
        self._bridge.finished.connect(self._on_finished, Qt.ConnectionType.QueuedConnection)
        self._handles: list[QtJobHandle] = []
        self._closed = False

    def run(
        self,
        job: Callable[[Progress], JobResult],
        *,
        on_done: Callable[[JobResult], None],
        on_progress: ProgressCallback | None = None,
    ) -> QtJobHandle:
        """Start ``job`` on its own worker thread.

        Args:
            job: The job; it must not touch a Qt object.
            on_done: Receives the result on the main thread, exactly once.
            on_progress: Receives the latest ``(done, total, message)`` on the main thread.

        Returns:
            The job's handle.

        Raises:
            RuntimeError: The runner has been closed.
        """
        if self._closed:
            raise RuntimeError("the job runner is closed")
        holder: list[QtJobHandle] = []
        progress = QtProgress(lambda: self._emit_progress(holder[0]))
        handle = QtJobHandle(progress, on_done, on_progress)
        holder.append(handle)
        thread = threading.Thread(
            target=self._work, args=(handle, job), name="clearwater-job", daemon=True
        )
        handle.thread = thread
        self._handles.append(handle)
        thread.start()
        return handle

    def cancel(self) -> None:
        """Cancel every running job."""
        for handle in list(self._handles):
            handle.cancel()

    def active(self) -> int:
        """Return how many jobs have not yet delivered ``on_done``."""
        return len(self._handles)

    def wait(self, timeout_s: float) -> bool:
        """Wait for every job thread to end, at most ``timeout_s`` seconds in total.

        Args:
            timeout_s: The longest wait.

        Returns:
            True when no job thread is left running.
        """
        deadline = time.monotonic() + timeout_s
        for handle in list(self._handles):
            if handle.thread is not None:
                handle.thread.join(max(0.0, deadline - time.monotonic()))
        return all(h.thread is None or not h.thread.is_alive() for h in self._handles)

    def close(self, timeout_s: float) -> bool:
        """Cancel every job, wait for the threads, and refuse further jobs (shell close).

        Args:
            timeout_s: The longest wait.

        Returns:
            True when no job thread is left running.
        """
        self._closed = True
        self.cancel()
        return self.wait(timeout_s)

    def _emit_progress(self, handle: QtJobHandle) -> None:
        """Job thread: post one progress delivery."""
        with contextlib.suppress(RuntimeError):  # the bridge was deleted at shutdown
            self._bridge.progressed.emit(handle)

    def _work(self, handle: QtJobHandle, job: Callable[[Progress], JobResult]) -> None:
        """Job thread: run the job and post its result."""
        start = time.perf_counter()
        try:
            result = job(handle.progress)
        except Exception as exc:  # a failing job is a failed result, never a crash
            _LOG.warning("job failed: %s: %s", type(exc).__name__, exc)
            result = JobResult(
                ok=False,
                outputs=(),
                warnings=(),
                failure=f"{type(exc).__name__}: {exc}",
                device="unknown",
                elapsed_s=time.perf_counter() - start,
            )
        with contextlib.suppress(RuntimeError):  # the bridge was deleted at shutdown
            self._bridge.finished.emit(handle, result)

    def _on_progressed(self, handle: object) -> None:
        """Main thread: deliver the latest report of a job."""
        assert isinstance(handle, QtJobHandle)
        if not handle.is_running():
            return
        self._flush(handle)

    def _flush(self, handle: QtJobHandle) -> None:
        """Main thread: hand the latest undelivered report to the callback."""
        latest = handle.progress.take()
        if latest is not None and handle.on_progress is not None:
            handle.on_progress(*latest)

    def _on_finished(self, handle: object, result: object) -> None:
        """Main thread: deliver the last report, then the result."""
        assert isinstance(handle, QtJobHandle)
        assert isinstance(result, JobResult)
        self._flush(handle)
        handle.finish()
        if handle in self._handles:
            self._handles.remove(handle)
        handle.on_done(result)
