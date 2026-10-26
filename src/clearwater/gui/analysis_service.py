"""The analysis seam of the timeline panel (WP3.18 task 2): what the GUI needs of an analysis.

``clearwater.analysis`` (WP3.11) is not imported here or anywhere in ``clearwater.gui``; WP4.3
adapts its ``AnalysisEngine`` to :class:`ClipAnalysis` and passes the adapter's factory to
``install_timeline``. The module imports no Qt object: everything in it runs on worker threads
(the factory excepted, which only builds an object). Frozen at the WP3.18 round-0 yield;
additive only until the WP3.18 accept, then a change is a CHARC ruling.

Threading rules (the stub honours them, WP4.3's adapter must):

- The factory is called on the main thread and does no I/O and no heavy work; the first thing
  :meth:`ClipAnalysis.run` does may.
- :meth:`ClipAnalysis.pts` and :meth:`ClipAnalysis.retarget` are called on the main thread:
  ``pts`` at most once per progress delivery and at the start and end of a run, ``retarget`` when
  the parameters change while a run is in flight. Both must be cheap and must never wait for
  :meth:`ClipAnalysis.run`.
- :meth:`ClipAnalysis.run`, :meth:`ClipAnalysis.proxy` and :meth:`ClipAnalysis.statistics` are
  called on worker threads only. ``proxy`` and ``statistics`` may run while ``run`` does
  (AD-15: scrubbing during analysis), on other threads; at most one ``run`` of one analysis is
  in flight at a time.
- Nothing here touches a Qt object.
"""

from __future__ import annotations

import bisect
import threading
from collections.abc import Callable, Mapping
from typing import Protocol

import numpy as np
from numpy.typing import NDArray

from clearwater.cache import cache_key
from clearwater.interfaces import (
    CacheKey,
    CorrectionMethod,
    Image,
    ParameterSet,
    Progress,
    Statistics,
)
from clearwater.interfaces.stubs import StubStatisticsStore

from .contract import Engines, OpenedSource
from .imaging import downscale, effective_parameters, statistics_factor, to_display_uint8


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

    def retarget(self, parameters: ParameterSet, *, focus_pts: int | None = None) -> bool:
        """Offer new parameters to the run in flight (main thread; added at the round-0 ruling).

        Called only while the GUI has a run in flight (from its submission to its done
        callback), cheap, never waiting for :meth:`run`. The GUI enforces the condition and
        raises ``RuntimeError`` itself when asked to retarget with no run in flight; an
        implementation need not prove it, and in the window where its run has already ended
        returns False. No run is ever cancelled for a parameter change.

        Args:
            parameters: The new parameter set (same method as the run's).
            focus_pts: The displayed frame's pts ticks, or None.

        Returns:
            True when the run in flight absorbed the change: it finishes under ``parameters``,
            and its normal return means complete under them. False when it did not: the run
            finishes under the old parameters and the caller starts :meth:`run` again with
            the latest ones. An implementation that holds a recompute job started by this
            call keeps it and runs it at the next :meth:`run`; it returns False.
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


STUB_SMOOTHING_S = 2.0
"""The window the stub passes to ``StubStatisticsStore.smooth`` (which ignores it)."""


class StubClipAnalysis:
    """A :class:`ClipAnalysis` over ``engines.video_source`` and ``engines.cache`` (tests, WP4.3).

    The decode pass stores, per frame, the statistics proxy (``downscale`` by
    ``statistics_factor``, quantised to uint8) in ``engines.cache`` under ``cache_key`` of the
    file, and reports ``(done, nb_frames)``. The measurement pass runs ``method.analyze`` stage
    by stage on each STORED proxy into a ``StubStatisticsStore`` keyed by pts ticks and
    publishes it, smoothed (a copy: the stub store ignores the window), only when the pass ends
    uncancelled. It claims no AD-5 or AD-3 fidelity. ``focus_pts`` is accepted and ignored
    (frames are measured in pts order). A later ``run`` skips the decode pass once one has
    completed. ``statistics`` is None from the start of a ``run`` until it completes, like the
    WP3.11 engine after a cancel or while it recomputes.

    Args:
        source: The opened video (``probe`` and ``path`` are used).
        method: The correction method.
        engines: The engines (``video_source``, ``cache``).
        absorb: What ``retarget`` returns while a run is in flight: True makes the measurement
            pass restart under the new parameters (the run then completes under them); False
            (the default) leaves the run as it is.

    Attributes:
        calls: ``(member name, thread)`` for every call, so tests can check where each ran.
    """

    def __init__(
        self,
        source: OpenedSource,
        method: CorrectionMethod,
        engines: Engines,
        *,
        absorb: bool = False,
    ) -> None:
        """Create the analysis; nothing is read or measured until ``run``."""
        if source.probe is None:
            raise ValueError("the stub analysis needs a video source")
        self._source = source
        self._method = method
        self._engines = engines
        self._absorb = absorb
        self._lock = threading.Lock()
        self._key: CacheKey | None = None
        self._pts: list[int] = []
        self._pts_tuple: tuple[int, ...] = ()
        self._decoded = False
        self._active = False
        self._target: ParameterSet | None = None
        self._target_generation = 0
        self._published: StubStatisticsStore | None = None
        self.calls: list[tuple[str, threading.Thread]] = []

    def _note(self, name: str) -> None:
        """Record a call and its thread."""
        with self._lock:
            self.calls.append((name, threading.current_thread()))

    def run(
        self, parameters: ParameterSet, progress: Progress, *, focus_pts: int | None = None
    ) -> None:
        """Decode (once), then measure and smooth under the latest target parameters.

        Args:
            parameters: The parameter set to analyse under.
            progress: Progress and cancellation.
            focus_pts: Accepted and ignored.

        Raises:
            RuntimeError: Another ``run`` of this analysis is in flight.
            OSError: The source file cannot be examined for its cache key.
        """
        self._note("run")
        with self._lock:
            if self._active:
                raise RuntimeError("a run of this analysis is already in flight")
            self._active = True
            self._target = parameters
            self._target_generation += 1
            self._published = None
        try:
            key = self._cache_key()
            if not self._decoded and not self._decode(progress, key):
                return
            self._measure(progress, key)
        finally:
            with self._lock:
                self._active = False

    def retarget(self, parameters: ParameterSet, *, focus_pts: int | None = None) -> bool:
        """Absorb ``parameters`` into the run in flight when constructed with ``absorb=True``.

        Args:
            parameters: The new parameter set.
            focus_pts: Ignored.

        Returns:
            True when absorbed; False when ``absorb`` is off or no run is in flight (including
            the window where it has just ended or has not yet started).
        """
        self._note("retarget")
        with self._lock:
            if not self._active or not self._absorb:
                return False
            self._target = parameters
            self._target_generation += 1
            return True

    def pts(self) -> tuple[int, ...]:
        """Return the pts ticks stored so far, ascending (never waits for ``run``)."""
        self._note("pts")
        with self._lock:
            return self._pts_tuple

    def proxy(self, pts_ticks: int) -> NDArray[np.uint8]:
        """Return a stored proxy.

        Args:
            pts_ticks: A stored pts.

        Returns:
            The proxy.

        Raises:
            KeyError: Nothing is stored for ``pts_ticks``.
        """
        self._note("proxy")
        with self._lock:
            key = self._key
        if key is None:
            raise KeyError(pts_ticks)
        return self._engines.cache.proxy(key, pts_ticks)

    def statistics(self, pts_ticks: int) -> Mapping[str, Statistics] | None:
        """Return the published smoothed statistics of one frame, or None.

        Args:
            pts_ticks: The frame's pts ticks.

        Returns:
            Stage name -> statistics, or None while no run has completed or ``pts_ticks`` is
            unknown.
        """
        self._note("statistics")
        with self._lock:
            store = self._published
        if store is None:
            return None
        try:
            return {
                stage.name: store.smoothed(pts_ticks, stage.name) for stage in self._method.stages
            }
        except KeyError:
            return None

    def _cache_key(self) -> CacheKey:
        """Take the file's cache key once (``os.stat``: on the job thread, never the main one)."""
        with self._lock:
            if self._key is None:
                self._key = cache_key(self._source.path)
            return self._key

    def _decode(self, progress: Progress, key: CacheKey) -> bool:
        """Store a proxy per frame; return False when cancelled before the end."""
        probe = self._source.probe
        assert probe is not None
        total = probe.video.nb_frames
        done = 0
        frames = self._engines.video_source.frames(probe, hw_decode=False)
        try:
            for frame in frames:
                if progress.cancelled():
                    return False
                pixels = np.asarray(frame.pixels, dtype=np.float32)
                factor = statistics_factor(pixels.shape[0], pixels.shape[1])
                proxy = to_display_uint8(downscale(pixels, factor))
                self._engines.cache.store_proxy(key, frame.pts_ticks, proxy)
                with self._lock:
                    if frame.pts_ticks not in self._pts:
                        bisect.insort(self._pts, frame.pts_ticks)
                        self._pts_tuple = tuple(self._pts)
                done += 1
                progress.report(done, total, "Analysing")
        finally:
            close = getattr(frames, "close", None)
            if callable(close):
                close()
        progress.report(done, done, "Decoded")
        self._decoded = True
        return True

    def _measure(self, progress: Progress, key: CacheKey) -> None:
        """Measure every stored proxy, smooth, publish; restart when the target changed."""
        probe = self._source.probe
        assert probe is not None
        stages = self._method.stages
        while True:
            with self._lock:
                target = self._target
                generation = self._target_generation
                ticks = self._pts_tuple
            assert target is not None
            values = effective_parameters(self._method, target)
            store = StubStatisticsStore([stage.name for stage in stages])
            restart = False
            for tick in ticks:
                if progress.cancelled():
                    return
                with self._lock:
                    restart = generation != self._target_generation
                if restart:
                    break
                stored = self._engines.cache.proxy(key, tick)
                pixels = stored.astype(np.float32) / np.float32(255.0)
                image = Image(pixels, "cpu", probe.video.color, True)
                earlier: dict[str, Statistics] = {}
                for stage in stages:
                    measured = self._method.analyze(stage.name, image, values, earlier)
                    store.put(tick, stage.name, measured)
                    earlier[stage.name] = measured
            if restart:
                continue
            for stage in stages:
                store.smooth(stage.name, stage.statistics, STUB_SMOOTHING_S, "median_gaussian")
            if progress.cancelled():
                return
            with self._lock:
                if generation != self._target_generation:
                    continue
                self._published = store
                self._active = False
            return


def stub_analysis_factory(
    source: OpenedSource, method: CorrectionMethod, engines: Engines
) -> ClipAnalysis:
    """Build the stub analysis over ``engines.video_source`` and ``engines.cache`` (tests, WP4.3).

    Claims no AD-5 or AD-3 fidelity (WP3.11's), only this seam's contract; ``retarget`` returns
    False (use :class:`StubClipAnalysis` with ``absorb=True`` to absorb).

    Args:
        source: The opened video.
        method: The method the analysis measures with.
        engines: The engines (``video_source``, ``cache``).

    Returns:
        The analysis.
    """
    return StubClipAnalysis(source, method, engines)
