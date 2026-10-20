"""IF-8: jobs.

Analysis, export and batch share these types; the GUI runs jobs on a worker thread and
marshals ``report`` to the main thread.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class Progress(Protocol):
    """Progress reporting and cancellation for a running job (IF-8)."""

    def report(self, done: int, total: int | None, message: str) -> None:
        """Report progress.

        Args:
            done: Units completed so far.
            total: Total units, or None when unknown.
            message: A short status message.
        """
        ...

    def cancelled(self) -> bool:
        """Return True once the user has asked to cancel."""
        ...


@dataclass(frozen=True)
class JobResult:
    """The outcome of one job (IF-8).

    Attributes:
        ok: True when the job completed.
        outputs: The files the job produced.
        warnings: Warnings raised while running.
        failure: The failure message, or None on success.
        device: The device the job ran on.
        elapsed_s: Wall-clock seconds.
    """

    ok: bool
    outputs: tuple[Path, ...]
    warnings: tuple[str, ...]
    failure: str | None
    device: str
    elapsed_s: float
