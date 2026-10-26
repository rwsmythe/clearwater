"""The analysis seam of the timeline panel (WP3.18 task 2): what the GUI needs of an analysis.

``clearwater.analysis`` (WP3.11) is not imported here or anywhere in ``clearwater.gui``; WP4.3
adapts its ``AnalysisEngine`` to :class:`ClipAnalysis` and passes the adapter's factory to
``install_timeline``. The module imports no Qt object: everything in it runs on worker threads
(the factory excepted, which only builds an object). Frozen at the WP3.18 round-0 yield;
additive only until the WP3.18 accept, then a change is a CHARC ruling.

Threading rules (the stub honours them, WP4.3's adapter must):

- The factory is called on the main thread and does no I/O and no heavy work; the first thing
  :meth:`ClipAnalysis.run` does may.
- :meth:`ClipAnalysis.pts` is called on the main thread, at most once per progress delivery and
  at the start and end of a run: it must be cheap and must never wait for :meth:`ClipAnalysis.run`.
- :meth:`ClipAnalysis.run`, :meth:`ClipAnalysis.proxy` and :meth:`ClipAnalysis.statistics` are
  called on worker threads only. ``proxy`` and ``statistics`` may run while ``run`` does
  (AD-15: scrubbing during analysis), on other threads; at most one ``run`` of one analysis is
  in flight at a time.
- Nothing here touches a Qt object.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from clearwater.interfaces import CorrectionMethod, ParameterSet, Progress, Statistics

from .contract import Engines, OpenedSource


class ClipAnalysis(Protocol):
    """The analysis of one opened clip (one instance per opened clip; AD-15, D108, G5).

    Statistics are keyed by pts ticks, never by an index (AD-6, DR-23).
    """

    def run(
        self, parameters: ParameterSet, progress: Progress, *, focus_pts: int | None = None
    ) -> None:
        """Bring the smoothed statistics up to date for ``parameters`` (worker thread).

        The first call is the full pass (decode, proxies, staged statistics, smoothing); a later
        call after a parameter change recomputes the dependent stages, first for the frames
        within the smoothing reach of ``focus_pts`` (AD-7). It reports through ``progress`` and
        returns early, leaving no complete result, when ``progress.cancelled()`` becomes true.
        The caller treats a normal return of a job it did not cancel as completion.

        Args:
            parameters: The parameter set to analyse under (the method is the one the analysis
                was built for).
            progress: IF-8 progress and cancellation.
            focus_pts: The displayed frame's pts ticks, or None.

        Raises:
            Exception: Any failure; the caller shows its text.
        """
        ...

    def pts(self) -> tuple[int, ...]:
        """Return the pts ticks that have a stored proxy so far, ascending (main thread).

        Cheap and non-blocking; callable before, during and after :meth:`run`, and after a
        cancel or a failure (the proxies stored so far stay).

        Returns:
            The pts ticks, ascending; empty before the first proxy.
        """
        ...

    def proxy(self, pts_ticks: int) -> NDArray[np.uint8]:
        """Return a stored proxy, ``(H, W, 3)`` RGB uint8 (worker thread).

        Args:
            pts_ticks: A pts value from :meth:`pts`.

        Returns:
            The proxy pixels.

        Raises:
            KeyError: No proxy is stored for ``pts_ticks``.
        """
        ...

    def statistics(self, pts_ticks: int) -> Mapping[str, Statistics] | None:
        """Return the smoothed statistics of one frame, every stage (worker thread).

        Args:
            pts_ticks: The frame's pts ticks.

        Returns:
            Stage name -> statistics for every stage of the method, for the parameters of the
            latest completed :meth:`run`; None when they are not available (no completed run, a
            cancelled or failed one, or ``pts_ticks`` unknown).
        """
        ...


type AnalysisFactory = Callable[[OpenedSource, CorrectionMethod, Engines], ClipAnalysis]
"""Builds the :class:`ClipAnalysis` of an opened video (main thread; builds, does not run)."""


def stub_analysis_factory(
    source: OpenedSource, method: CorrectionMethod, engines: Engines
) -> ClipAnalysis:
    """Build the stub analysis over ``engines.video_source`` and ``engines.cache`` (tests, WP4.3).

    Claims no AD-5 or AD-3 fidelity (WP3.11's), only this seam's contract.

    Args:
        source: The opened video.
        method: The method the analysis measures with.
        engines: The engines (``video_source``, ``cache``).

    Returns:
        The analysis.
    """
    raise NotImplementedError
