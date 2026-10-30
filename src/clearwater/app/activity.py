"""One activity per clip (DR-62) and the application's export wrapper (WP4.3).

:class:`ClipLocks` is one process-local lock per cache key: the GUI's analysis or recompute of a
clip and an export of the same clip (single, or a batch item) never run their engines at once.
The second WAITS on its own worker thread, cancellably, reporting :data:`WAITING_TEXT`
(question 8 as ruled), so neither is refused and no statistics are lost. :class:`GuardedExports`
implements the WP3.19 ``ExportJobs`` seam over the export engine; its job callable, on the
worker, in this order:

1. DR-82: ``jobs.naming.final_output_path`` for the source. An ``OutputNameError`` is a failed
   result saying to rename the file (the panel names the source), before any read or probe;
   any other error is left to the engine's own text.
2. The journal entry of the destination folder (D85), before any temporary can exist. A journal
   that cannot be written fails the export readably, before the engine reads or probes and
   with nothing written (R1-2, ruling d530b564): an export whose leftovers no start-up would
   find never starts.
3. A video: the clip's lock (the key is computed here, on the worker: ``ExportJobs.job`` builds
   the callable only).
4. DR-68: the preview's FFT plans are released before the job selects its backend; the job
   waits for the release with no deadline, and a cancel while waiting ends it unwritten
   (R1-11).
5. The engine's job; then the AD-9 log line naming ``JobResult.device``.
6. Always: the lock released, and the journal entry removed unless its folder still holds a
   temporary output (the engine could not remove one, or the job died mid-write); the next
   start then removes it (R1-3, ruling d530b564).

Qt-free; nothing here touches a Qt object.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from pathlib import Path

from clearwater.interfaces import CacheKey, JobResult, Progress
from clearwater.io.video.inputs import ascii_text
from clearwater.jobs import MediaKind, OutputNameError, final_output_path
from clearwater.jobs.export_seam import CANCELLED, ExportJobs, ExportRequest

from .composition import DeferredProxyCache
from .startup import WriteJournal, holds_leftovers

_LOG = logging.getLogger(__name__)

WAITING_TEXT = "Waiting for the other job on this clip"
"""What a job waiting for another activity on the same clip reports (DR-62, question 8)."""

OPENING_CACHE_TEXT = "Opening the analysis cache"
"""What a video job waiting for the start-up's cache open reports (ruling S1 (a))."""

RENAME_TEXT = "this file name cannot be used for an output file; rename the file."
"""The failed item's text for a source whose name gives no portable output name (DR-82, Q22).

The panels name the source beside it (the export panel prefixes ``<name>: ``, the batch report
lists the item), so the text carries no name of its own (ruling 68d5b4c7, item 2)."""

JOURNAL_FAILED_TEXT = (
    "the export was not started because its clean-up record could not be written in {folder} "
    "({reason})."
)
"""The failed item's text when the journal entry cannot be written (R1-2, ruling d530b564)."""

POLL_S = 0.05
"""How often a waiting job looks at its cancel flag."""


class ClipLocks:
    """One process-local lock per cache key (DR-62); thread-safe, never nested by its users."""

    def __init__(self) -> None:
        """Create the locks with none held."""
        self._condition = threading.Condition()
        self._held: set[CacheKey] = set()

    def acquire(self, key: CacheKey, progress: Progress) -> bool:
        """Take the clip's lock, waiting (cancellably) while another activity holds it.

        Args:
            key: The clip's cache key.
            progress: The waiting job's progress: it reports :data:`WAITING_TEXT` once and is
                looked at every :data:`POLL_S` seconds for a cancel.

        Returns:
            True when the lock is taken; False when the job was cancelled while waiting (the
            lock is not taken).
        """
        with self._condition:
            if key not in self._held:
                self._held.add(key)
                return True
        progress.report(0, None, WAITING_TEXT)
        with self._condition:
            while key in self._held:
                if progress.cancelled():
                    return False
                self._condition.wait(POLL_S)
            self._held.add(key)
            return True

    def release(self, key: CacheKey) -> None:
        """Release the clip's lock.

        Args:
            key: The clip's cache key.
        """
        with self._condition:
            self._held.discard(key)
            self._condition.notify_all()

    def held(self, key: CacheKey) -> bool:
        """Return True while some activity holds the clip's lock."""
        with self._condition:
            return key in self._held


def wait_for_cache(cache: DeferredProxyCache, progress: Progress) -> bool:
    """Wait (cancellably) for the start-up's cache open to end, reporting why.

    Args:
        cache: The application's cache handle.
        progress: The waiting job's progress.

    Returns:
        True when the open has ended (opened or failed); False when cancelled first.
    """
    if cache.wait_open(0):
        return True
    progress.report(0, None, OPENING_CACHE_TEXT)
    while not cache.wait_open(POLL_S):
        if progress.cancelled():
            return False
    return True


def _cancelled(started: float) -> JobResult:
    """The result of a job cancelled before its engine ran: nothing was written."""
    return JobResult(False, (), (), CANCELLED, "none", time.perf_counter() - started)


class GuardedExports:
    """The application's ``ExportJobs``: the export engine behind the per-job guards above.

    Args:
        engine: The export engine (the application's ``composition.process_export_jobs(...)``:
            video jobs in a worker process, photos on ``composition.export_jobs(cache=...)``).
        cache: The application's one cache (the clip's key and the open's wait).
        locks: The per-clip locks shared with the GUI's analysis.
        journal: The write journal.
        release_device_plans: Releases the preview's FFT plans on the preview's thread and
            waits for it, cancellably (DR-68, R1-11); False means the job was cancelled while
            waiting, and it then ends before it selects. None when there is no preview.
    """

    def __init__(
        self,
        engine: ExportJobs,
        *,
        cache: DeferredProxyCache,
        locks: ClipLocks,
        journal: WriteJournal,
        release_device_plans: Callable[[Progress], bool] | None = None,
    ) -> None:
        """Store the collaborators; nothing runs until a job runs."""
        self._engine = engine
        self._cache = cache
        self._locks = locks
        self._journal = journal
        self._release = release_device_plans

    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]:
        """Return the guarded IF-8 job for ``request`` (the ``ExportJobs`` contract).

        Touches no file: the guards run in the job, on the worker.

        Args:
            request: What to export.

        Returns:
            The job.

        Raises:
            ValueError: The request is malformed in itself (the engine's check).
        """
        inner = self._engine.job(request)

        def run(progress: Progress) -> JobResult:
            return self._run(request, inner, progress)

        return run

    def _run(
        self,
        request: ExportRequest,
        inner: Callable[[Progress], JobResult],
        progress: Progress,
    ) -> JobResult:
        """Run the guards and the engine's job (the module docstring's order)."""
        started = time.perf_counter()
        name = ascii_text(request.source.name) or ascii_text(str(request.source))
        kind = MediaKind.PHOTO if request.kind == "photo" else MediaKind.VIDEO
        folder: Path | None
        try:
            folder = final_output_path(request.source, request.settings, kind).parent
        except OutputNameError:
            failure = RENAME_TEXT
            _LOG.info("export %s: refused before reading; %s", name, failure)
            return JobResult(False, (), (), failure, "none", time.perf_counter() - started)
        except (ValueError, OSError):
            folder = None  # the engine refuses the same request with its own text, unwritten
        entry: str | None = None
        if folder is not None:
            try:
                entry = self._journal.add(folder)
            except OSError as error:
                failure = JOURNAL_FAILED_TEXT.format(
                    folder=ascii_text(str(self._journal.path.parent)),
                    reason=ascii_text(str(error)),
                )
                _LOG.warning("export %s: refused before reading; %s", name, failure)
                return JobResult(False, (), (), failure, "none", time.perf_counter() - started)
        try:
            return self._guarded(request, inner, progress, name, started)
        finally:
            if entry is not None and folder is not None:
                self._journal_remove(entry, folder)

    def _guarded(
        self,
        request: ExportRequest,
        inner: Callable[[Progress], JobResult],
        progress: Progress,
        name: str,
        started: float,
    ) -> JobResult:
        """Run steps 3 to 5 of the module docstring's order (the journal entry is held)."""
        key: CacheKey | None = None
        if request.kind == "video":
            if not wait_for_cache(self._cache, progress):
                return _cancelled(started)
            try:
                key = self._cache.key_for(request.source)
            except (OSError, RuntimeError):
                key = None  # a missing source or a failed cache: the engine's own text follows
            if key is not None and not self._locks.acquire(key, progress):
                return _cancelled(started)
        try:
            if self._release is not None and not self._release(progress):
                return _cancelled(started)  # never selects before the release (R1-11)
            result = inner(progress)
        finally:
            if key is not None:
                self._locks.release(key)
        outcome = "ok" if result.ok else ("cancelled" if result.failure is CANCELLED else "failed")
        _LOG.info("export job %s: %s; device %s", name, outcome, result.device)
        return result

    def _journal_remove(self, entry: str, folder: Path) -> None:
        """Remove a journal entry unless its folder still holds a temporary (logged when kept).

        A journal that cannot be written is logged; the entry stays and the next start scans
        its folder.
        """
        if holds_leftovers(folder):
            _LOG.warning("the write journal keeps %s until its clean-up succeeds", folder)
            return
        try:
            self._journal.remove(entry)
        except OSError as error:
            _LOG.warning("the write journal entry could not be removed: %s", error)
