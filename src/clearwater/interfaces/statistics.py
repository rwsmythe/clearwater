"""IF-4: the statistics store.

Keys are pts ticks (D95); a constant-frame-rate series is the special case. There are no group
breaks in v1 (spec v0.5.3 section 5.5).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Protocol, runtime_checkable

from .method import Statistics


@runtime_checkable
class StatisticsStore(Protocol):
    """Per-frame statistics of one clip, raw and smoothed, keyed by pts ticks (IF-4).

    Attributes:
        schema_hash: The method id and the parameters that shaped the statistics (DR-25
            erratum), so a stale record is not rendered under another schema.
    """

    def put(self, pts_ticks: int, stage: str, raw: Statistics) -> None:
        """Store the raw statistics of one stage for one frame.

        Args:
            pts_ticks: The frame's presentation time in ticks.
            stage: The stage name.
            raw: The measured statistics.
        """
        ...

    def raw(self, pts_ticks: int, stage: str) -> Statistics:
        """Return the raw statistics of one stage for one frame.

        Args:
            pts_ticks: The frame's presentation time in ticks.
            stage: The stage name.

        Returns:
            The raw statistics.

        Raises:
            KeyError: No statistics are stored for that frame and stage.
        """
        ...

    def smoothed(self, pts_ticks: int, stage: str) -> Statistics:
        """Return the smoothed statistics of one stage for one frame.

        Args:
            pts_ticks: The frame's presentation time in ticks.
            stage: The stage name.

        Returns:
            The smoothed statistics.
        """
        ...

    def smooth(self, stage: str, names: Sequence[str], window_s: float, kind: str) -> None:
        """Smooth the named statistics of a stage over pts (AD-3).

        Args:
            stage: The stage name.
            names: The statistic names to smooth.
            window_s: The smoothing window in seconds, defined over pts (D95).
            kind: The smoothing filter kind.
        """
        ...

    def invalidate_from(self, stage: str) -> None:
        """Drop the statistics of ``stage`` and every later stage (AD-7).

        Args:
            stage: The first stage to invalidate.
        """
        ...

    def pts_range(self) -> tuple[int, int]:
        """Return the first and last stored pts ticks."""
        ...

    def all_pts(self) -> Sequence[int]:
        """Return every stored pts ticks value."""
        ...

    schema_hash: str
