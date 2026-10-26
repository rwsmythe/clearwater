"""The export seam between the GUI and the export engine (WP3.19, IF-8).

WP3.14 (wave 4) builds the export and batch engine; the GUI panels (``clearwater.gui.export_panel``
and ``clearwater.gui.batch_panel``) are written against :class:`ExportJobs`, and
:func:`unavailable_exports` is the product default until WP4.3 wires the engine. Frozen at the
WP3.19 round-0 yield; additive only until the WP3.19 accept, then a change is a CHARC ruling.

This module imports only the standard library and ``clearwater.interfaces``, so a headless
runner shares the seam types without loading PySide6 (CHARC ruling on WP3.19 round 0, C1).
"""

from __future__ import annotations

import time
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from clearwater.interfaces import JobResult, ParameterSet, Progress, Settings

CANCELLED = "cancelled"
"""The ``JobResult.failure`` of a job that stopped because ``Progress.cancelled()`` was True.

Reserved: no genuine failure text may equal it, and an engine returns this constant itself, not
a copy of the string.
"""

UNAVAILABLE_TEXT = "Export is not available in this build."
"""The failure text of every job of :func:`unavailable_exports`."""


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

        This method is called on the interface thread: it only builds the callable and touches no
        file (no existence check, no decode), so a missing or unreadable source is the JOB's
        failure (``ok`` False with a readable reason), never an exception here. It may raise
        ``ValueError`` only for a request that is malformed in itself. The returned callable is
        what ``JobRunner.run`` runs on a worker thread. It:

        - touches no Qt object;
        - reports through ``progress.report(done, total, message)`` and checks
          ``progress.cancelled()`` at least between units of work;
        - writes through safe writing (``clearwater.jobs.SafeWrite``): a cancel or a failure
          leaves no partial output and no temporary file (G8, D44, V11), and an output already
          committed is never removed;
        - for a video, includes the analysis the export needs (AD-15), so a batch item needs no
          prior analysis;
        - returns a :class:`~clearwater.interfaces.JobResult`: ``ok`` True with ``outputs`` (the
          committed files) and ``warnings``; or ``ok`` False with ``failure`` the user-readable
          reason; on a cancel ``ok`` False and ``failure`` equal to :data:`CANCELLED`. On a non-ok
          result, ``outputs`` lists any file committed before the stop (normally none), and
          ``warnings`` any warning raised before it. An exception it lets escape becomes a
          failed result in the runner.
          :data:`CANCELLED` is reserved: a genuine failure text never equals it, and an engine
          returns the constant itself, not a copy of the string.

        One job exports one source and owns a fresh ``Reservations``: the GUI runs a batch as one
        job per item in sequence and each item is committed before the next is planned, so an
        output-name collision between batch items is caught by the filesystem scan at each plan
        (D34-D36), not by state shared between jobs.

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
