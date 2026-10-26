"""The GUI side of the export seam: re-exports it and holds the one-activity gate (WP3.19).

The seam itself (:class:`ExportRequest`, :class:`ExportJobs`, :data:`CANCELLED`,
:data:`UNAVAILABLE_TEXT`, :func:`unavailable_exports`) lives in the Qt-free
:mod:`clearwater.jobs.export_seam` and is re-exported here. :class:`ActivityGate`,
:class:`SharedGate` and the two reason strings are the GUI side; WP3.14 does not implement them.
This module imports no Qt class.
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from typing import Literal

from clearwater.jobs.export_seam import (
    CANCELLED,
    UNAVAILABLE_TEXT,
    ExportJobs,
    ExportRequest,
    unavailable_exports,
)

__all__ = [
    "CANCELLED",
    "RUNNING_BATCH_REASON",
    "RUNNING_EXPORT_REASON",
    "UNAVAILABLE_TEXT",
    "Activity",
    "ActivityGate",
    "ExportJobs",
    "ExportRequest",
    "SharedGate",
    "unavailable_exports",
]

_LOG = logging.getLogger(__name__)

RUNNING_EXPORT_REASON = "An export is running."
"""The reason on ``actions.export`` while the open source's export runs."""

RUNNING_BATCH_REASON = "A batch is running."
"""The reason on ``actions.export`` while a batch runs."""

type Activity = Literal["export", "batch"]
"""The one thing that may run at a time: the open source's export, or a batch."""


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


class SharedGate:
    """Creates the one :class:`ActivityGate` of a window when the first panel needs it.

    ``install_export_panels`` gives the same instance to the export and the batch panel
    factories; only the shell context (which holds ``actions.export``) is missing until a
    factory runs.
    """

    def __init__(self) -> None:
        """Create the holder with no gate."""
        self._gate: ActivityGate | None = None

    def get(self, apply: Callable[[str | None], None]) -> ActivityGate:
        """Return the gate, creating it with ``apply`` on the first call.

        Args:
            apply: Sets or clears the caller's reason on ``actions.export``; used by the first
                call only.

        Returns:
            The window's gate.
        """
        if self._gate is None:
            self._gate = ActivityGate(apply)
        return self._gate
