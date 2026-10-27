"""A headless batch over export jobs (G7, G8; D45, D81; WP3.14 question 9).

:func:`run_batch` runs one job per request, in order, on the caller's thread, with the same
per-item semantics as the GUI's batch panel (WP3.19): a failed item is logged and the batch
continues (D81); a cancel stops the running item and the rest are not run (D45); completed outputs
are kept (G8). The GUI keeps its own sequencing and does not call this; WP4.1's headless runner,
the tests and the V16 instrument do.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from dataclasses import dataclass

from clearwater.interfaces import JobResult, Progress
from clearwater.io.video.inputs import ascii_text

from .export_seam import CANCELLED, ExportJobs, ExportRequest

_LOG = logging.getLogger(__name__)


@dataclass(frozen=True)
class BatchItem:
    """One batch item and its outcome.

    Attributes:
        request: The item's export request.
        result: The job's result, or None when the item was not run (a cancel came first).
    """

    request: ExportRequest
    result: JobResult | None

    @property
    def state(self) -> str:
        """``"done"``, ``"done with warnings"``, ``"failed"``, ``"cancelled"`` or ``"not run"``."""
        result = self.result
        if result is None:
            return "not run"
        if result.ok:
            return "done with warnings" if result.warnings else "done"
        return "cancelled" if result.failure == CANCELLED else "failed"


@dataclass(frozen=True)
class BatchReport:
    """The end-of-run report of a batch (G7).

    Attributes:
        items: Every item, in the order given.
    """

    items: tuple[BatchItem, ...]

    def counts(self) -> dict[str, int]:
        """Return the number of items in each state (every state present, zero included)."""
        states = ("done", "done with warnings", "failed", "cancelled", "not run")
        counts = dict.fromkeys(states, 0)
        for item in self.items:
            counts[item.state] += 1
        return counts

    def lines(self) -> list[str]:
        """Return the report text, ASCII-safe: a count line, then one line per item.

        Each item line names the source and its state, then its outputs, warnings and failure.
        """
        counts = self.counts()
        lines = [
            f"Batch of {len(self.items)}: "
            + ", ".join(f"{n} {state}" for state, n in counts.items() if n)
        ]
        for index, item in enumerate(self.items, start=1):
            lines.append(f"{index}. {ascii_text(item.request.source.name)}: {item.state}")
            result = item.result
            if result is None:
                continue
            lines.extend(f"   saved {ascii_text(str(path))}" for path in result.outputs)
            lines.extend(f"   warning: {ascii_text(w)}" for w in result.warnings)
            if result.failure is not None and result.failure != CANCELLED:
                lines.append(f"   failure: {ascii_text(result.failure)}")
        return lines


class _ItemProgress:
    """The progress one item's job sees: messages prefixed ``[i/n]``, the batch's cancel flag."""

    def __init__(self, progress: Progress, index: int, count: int) -> None:
        self._progress = progress
        self._prefix = f"[{index}/{count}] "

    def report(self, done: int, total: int | None, message: str) -> None:
        """Pass the report on with the item prefix."""
        self._progress.report(done, total, self._prefix + message)

    def cancelled(self) -> bool:
        """Return the batch's cancel flag."""
        return self._progress.cancelled()


def run_batch(
    exports: ExportJobs, requests: Sequence[ExportRequest], progress: Progress
) -> BatchReport:
    """Run one export job per request, in order (G7; D45, D81).

    A job that fails, or a ``job()`` or job call that raises, is logged and the next item runs
    (D81). A job that returns :data:`~clearwater.jobs.export_seam.CANCELLED`, or a cancel seen
    between items, ends the batch: the remaining items are not run (D45). Completed outputs are
    never touched (G8). The report is logged at INFO.

    Args:
        exports: The export engine (any :class:`~clearwater.jobs.export_seam.ExportJobs`).
        requests: The items, in order.
        progress: The batch's progress; each job reports through it with an ``[i/n]`` prefix
            and sees its cancel flag.

    Returns:
        The report: one item per request, in order.
    """
    items: list[BatchItem] = []
    count = len(requests)
    stopped = False
    for index, request in enumerate(requests, start=1):
        if stopped or progress.cancelled():
            stopped = True
            items.append(BatchItem(request, None))
            continue
        name = ascii_text(request.source.name)
        try:
            result = exports.job(request)(_ItemProgress(progress, index, count))
        except Exception as exc:  # D81: a job that raises is a failed item; the batch goes on
            result = JobResult(
                ok=False,
                outputs=(),
                warnings=(),
                failure=f"{name}: {type(exc).__name__}: {ascii_text(str(exc))}",
                device="none",
                elapsed_s=0.0,
            )
        if result.failure == CANCELLED:
            stopped = True
        elif not result.ok:
            _LOG.warning("batch item %d of %d failed: %s", index, count, result.failure)
        items.append(BatchItem(request, result))
    report = BatchReport(tuple(items))
    _LOG.info("%s", "\n".join(report.lines()))
    return report
