"""The export seam of the GUI (WP3.19, IF-8) and the one-activity gate of the export panels.

WP3.14 (wave 4) builds the export and batch engine; the panels of this package are written
against :class:`ExportJobs`, and ``unavailable_exports`` is the product default until WP4.3 wires
the engine. Frozen at the WP3.19 round-0 yield; additive only until the WP3.19 accept, then a
change is a CHARC ruling. The seam is :class:`ExportRequest`, :class:`ExportJobs`,
:data:`CANCELLED`, :data:`UNAVAILABLE_TEXT` and :func:`unavailable_exports`.
:class:`ActivityGate` and its constants are the GUI side (not part of what WP3.14 implements).

This module imports no Qt class and no ``clearwater.gui`` module, so a headless runner can share
the seam types (importing the ``clearwater.gui`` package still loads PySide6 through its
``__init__``; the round-0 report names that for WP3.14's brief).
"""

from __future__ import annotations

import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from clearwater.interfaces import JobResult, ParameterSet, Progress, Settings

_LOG = logging.getLogger(__name__)

CANCELLED = "cancelled"
"""The ``JobResult.failure`` of a job that stopped because ``Progress.cancelled()`` was True."""

UNAVAILABLE_TEXT = "Export is not available in this build."
"""The failure text of every job of :func:`unavailable_exports`."""

RUNNING_EXPORT_REASON = "An export is running."
"""The reason on ``actions.export`` while the open source's export runs."""

RUNNING_BATCH_REASON = "A batch is running."
"""The reason on ``actions.export`` while a batch runs."""

type Activity = Literal["export", "batch"]
"""The one thing that may run at a time: the open source's export, or a batch."""


@dataclass(frozen=True)
class ExportRequest:
    """What one export job is asked to do: one source file, one parameter set, the settings.

    A snapshot taken on the interface thread: later changes to the open source, the parameters
    or the settings do not reach a request already made.

    Attributes:
        source: The file to export. A batch item need not be the open source; the job reads it
            itself.
        kind: ``"photo"`` or ``"video"`` (what ``clearwater.gui.sources.route`` decided).
        parameters: The parameter set to render with (IF-9).
        settings: The settings at the time of the request (IF-10): output folder, suffix,
            encoder, quality, provenance, force CPU.
    """

    source: Path
    kind: Literal["photo", "video"]
    parameters: ParameterSet
    settings: Settings


class ExportJobs(Protocol):
    """The export engine as the panels use it (implemented by WP3.14; stub until WP4.3)."""

    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]:
        """Return the IF-8 job that exports ``request``.

        This method is called on the interface thread: it only builds the callable (no file
        access, no decode) and may raise ``ValueError`` for a request it can never run. The
        returned callable is what ``JobRunner.run`` runs on a worker thread. It:

        - touches no Qt object;
        - reports through ``progress.report(done, total, message)`` and checks
          ``progress.cancelled()`` at least between units of work;
        - writes through safe writing (``clearwater.jobs.SafeWrite``): a cancel or a failure
          leaves no partial output and no temporary file (G8, D44, V11), and an output already
          committed is never removed;
        - for a video, includes the analysis the export needs (AD-15), so a batch item needs no
          prior analysis;
        - returns a :class:`~clearwater.interfaces.JobResult`: ``ok`` True with ``outputs`` (the
          committed files) and ``warnings``; or ``ok`` False with ``outputs`` empty and
          ``failure`` the user-readable reason; on a cancel ``ok`` False and ``failure`` equal to
          :data:`CANCELLED`. An exception it lets escape becomes a failed result in the runner.

        Args:
            request: What to export.

        Returns:
            The job.
        """
        ...


class _UnavailableExports:
    """The product default: every job fails with :data:`UNAVAILABLE_TEXT` and writes nothing."""

    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]:
        """Return a job that fails at once.

        Args:
            request: Ignored.

        Returns:
            A job returning ``ok`` False with :data:`UNAVAILABLE_TEXT`; it opens no file.
        """

        def run(progress: Progress) -> JobResult:
            start = time.perf_counter()
            return JobResult(
                ok=False,
                outputs=(),
                warnings=(),
                failure=UNAVAILABLE_TEXT,
                device="none",
                elapsed_s=time.perf_counter() - start,
            )

        return run


def unavailable_exports() -> ExportJobs:
    """Return the export engine of a build without one (until WP4.3 wires WP3.14's).

    Returns:
        An :class:`ExportJobs` whose jobs fail with :data:`UNAVAILABLE_TEXT` and write nothing.
    """
    return _UnavailableExports()


class ActivityGate:
    """Lets one activity run at a time and keeps the reason on ``actions.export`` in step.

    Used on the interface thread only, shared by the export panel and the batch panel. The
    reason is applied through ``apply`` (``actions.export.set_unavailable``) before any
    subscriber is told, and a subscriber that raises is logged and skipped, so a failing
    callback cannot leave the reason set.
    """

    def __init__(self, apply: Callable[[str | None], None]) -> None:
        """Create the gate with no activity running and clear the caller's reason.

        Args:
            apply: Sets or clears the caller's reason on ``actions.export``.
        """
        self._apply = apply
        self._current: Activity | None = None
        self._subscribers: list[Callable[[Activity | None], None]] = []
        self._apply(None)

    @property
    def current(self) -> Activity | None:
        """The running activity, or None."""
        return self._current

    def reason(self) -> str | None:
        """Return why no other activity may start now, or None when none runs."""
        if self._current == "export":
            return RUNNING_EXPORT_REASON
        if self._current == "batch":
            return RUNNING_BATCH_REASON
        return None

    def subscribe(self, callback: Callable[[Activity | None], None]) -> None:
        """Call ``callback(current)`` after every change of the running activity.

        Args:
            callback: Receives the running activity, or None.
        """
        self._subscribers.append(callback)

    def try_start(self, activity: Activity) -> bool:
        """Mark ``activity`` running when nothing else runs.

        Args:
            activity: The activity that wants to start.

        Returns:
            True when it may start (the reason is set); False when an activity already runs.
        """
        if self._current is not None:
            return False
        self._current = activity
        self._changed()
        return True

    def finish(self, activity: Activity) -> None:
        """Mark ``activity`` finished; a call by an activity that is not running is ignored.

        Args:
            activity: The activity that ended.
        """
        if self._current != activity:
            return
        self._current = None
        self._changed()

    def _changed(self) -> None:
        """Apply the reason, then tell the subscribers (a failing subscriber is logged)."""
        self._apply(self.reason())
        for callback in list(self._subscribers):
            try:
                callback(self._current)
            except Exception:  # a panel's refresh must never leave the reason set
                _LOG.exception("an activity subscriber failed")
