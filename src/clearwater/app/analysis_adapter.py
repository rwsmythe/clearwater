"""The GUI's analysis: WP3.18's ``ClipAnalysis`` seam over WP3.11's ``AnalysisEngine`` (WP4.3).

The mapping is WP3.18's report, "The mapping for WP4.3", as corrected by its "Erratum at the
gate" (items 1 and 5), with WP4.3's rulings:

- The factory builds the adapter only; the engine is built in a ``run`` on the worker thread.
- Live settings by closure (erratum 5): the factory reads ``Settings`` through a provider over
  the session, so ``force_cpu`` is the one in force when a run starts.
- Backend, source and frame count (rulings Q18, S2): each run selects its backend at its START
  on the worker (DR-67's rule). The engine's frame source is ``composition.video_source`` on that
  backend (the GPU backend, or None on the CPU; the export's rule), ``hw_decode`` is True on the
  GPU, and the engine gets ``clearwater.jobs.expected_frames`` of the probe, as the export's
  does. When a run's selection differs from the engine's device, the engine is rebuilt over the
  SAME cache before the run; a run in flight keeps its backend (absorbed, never cancelled).
- Kept job priority (erratum 1): a job ``retarget`` got back from ``set_parameters`` is kept and
  run by the next ``run``, after the latest parameters were offered to it.
- Its own pts list (F-2): ``pts()`` returns a tuple the adapter refreshes on the worker; the main
  thread never calls the cache.
- ``statistics`` is None until a whole run has completed under the latest parameters.
- One activity per clip (DR-62): the engine's job runs under the clip's lock.

Threading (``clearwater.gui.analysis_service``): the factory, ``pts`` and ``retarget`` are called
on the main thread and never wait for a run (``retarget`` takes the engine lock, held only
around the engine's cheap state calls); ``run``, ``proxy`` and ``statistics`` on worker threads.
Qt-free: this module imports neither ``clearwater.gui`` nor PySide6; it meets the seam by
structure.
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import Any, Literal, Protocol

import numpy as np
from numpy.typing import NDArray

from clearwater.analysis import CANCELLED as ANALYSIS_CANCELLED
from clearwater.analysis import AnalysisEngine
from clearwater.interfaces import (
    ArrayBackend,
    CacheKey,
    CorrectionMethod,
    JobResult,
    ParameterSet,
    ProbeResult,
    Progress,
    ProxyCache,
    Settings,
    Statistics,
    VideoSource,
)
from clearwater.io.video.inputs import ascii_text
from clearwater.jobs import effective_parameters, expected_frames

from . import composition
from .activity import ClipLocks, wait_for_cache
from .composition import DeferredProxyCache

_LOG = logging.getLogger(__name__)

PTS_REFRESH_S = 0.1
"""The shortest interval between two refreshes of the pts list during a run (F-2)."""

type SelectBackend = Callable[[Settings, int, int, str], tuple[ArrayBackend, str]]
"""IF-2 ``select_backend(settings, height, width, method_id) -> (backend, reason)``."""

type EngineFactory = Callable[..., AnalysisEngine]
"""Builds an engine with :class:`~clearwater.analysis.AnalysisEngine`'s keyword arguments."""

type _Phase = Literal["idle", "pre", "engine", "post"]


class AnalysedSource(Protocol):
    """What the adapter reads of the GUI's opened source (``OpenedSource``, by structure)."""

    @property
    def path(self) -> Path:
        """The file."""
        ...

    @property
    def probe(self) -> ProbeResult | None:
        """The video's probe result, or None for a photo."""
        ...


class AnalysisEngines(Protocol):
    """What the factory reads of the GUI's engines (``Engines``, by structure)."""

    @property
    def cache(self) -> ProxyCache:
        """The application's one cache (a :class:`DeferredProxyCache` in the application)."""
        ...

    @property
    def select_backend(self) -> SelectBackend:
        """The IF-2 selection."""
        ...


class _Reporter:
    """The engine's progress, refreshing the adapter's pts list at most every 100 ms."""

    def __init__(self, progress: Progress, refresh: Callable[[], None]) -> None:
        self._progress = progress
        self._refresh = refresh
        self._last = time.monotonic()

    def report(self, done: int, total: int | None, message: str) -> None:
        self._progress.report(done, total, message)
        now = time.monotonic()
        if now - self._last >= PTS_REFRESH_S:
            self._last = now
            self._refresh()

    def cancelled(self) -> bool:
        return self._progress.cancelled()


class EngineClipAnalysis:
    """The ``ClipAnalysis`` of one opened clip over WP3.11's engine (the module docstring).

    Args:
        path: The clip.
        probe: Its probe result.
        method: The correction method the analysis measures with.
        cache: The application's one cache.
        select_backend: The IF-2 selection.
        settings: Returns the settings in force (the session's; read at each run's start).
        locks: The per-clip locks shared with the export wrapper (DR-62).
        engine_factory: Builds the engine (``AnalysisEngine``; tests hold a run with it).
        source_for: Builds the engine's frame source from its device backend
            (``composition.video_source``).

    Attributes:
        devices: The AD-9 reason of each run's selection, in order (the log line's).
    """

    def __init__(
        self,
        *,
        path: Path,
        probe: ProbeResult,
        method: CorrectionMethod,
        cache: DeferredProxyCache,
        select_backend: SelectBackend,
        settings: Callable[[], Settings],
        locks: ClipLocks,
        engine_factory: EngineFactory = AnalysisEngine,
        source_for: Callable[[ArrayBackend | None], VideoSource] = composition.video_source,
    ) -> None:
        """Create the adapter; nothing is read, selected or built until ``run`` (main thread)."""
        self._path = path
        self._probe = probe
        self._method = method
        self._cache = cache
        self._select = select_backend
        self._settings = settings
        self._locks = locks
        self._engine_factory = engine_factory
        self._source_for = source_for
        self._name = ascii_text(path.name)
        self._lock = threading.Lock()
        self._engine_lock = threading.Lock()
        self._phase: _Phase = "idle"
        self._target: dict[str, Any] = {}
        self._focus: int | None = None
        self._key: CacheKey | None = None
        self._pts: tuple[int, ...] = ()
        self._engine: AnalysisEngine | None = None
        self._device: str | None = None
        self._expected: tuple[int | None] | None = None
        self._kept: Callable[[Progress], JobResult] | None = None
        self._complete = False
        self._generation = 0
        self.devices: list[str] = []

    # --- the seam -----------------------------------------------------------------------------

    def run(
        self, parameters: ParameterSet, progress: Progress, *, focus_pts: int | None = None
    ) -> None:
        """Bring the smoothed statistics up to date for ``parameters`` (worker thread).

        Args:
            parameters: The parameter set to analyse under.
            progress: IF-8 progress and cancellation.
            focus_pts: The displayed frame's pts ticks, or None.

        Raises:
            RuntimeError: Another run is in flight, or the engine's job failed (its text).
            OSError: The clip cannot be examined for its cache key.
        """
        values = effective_parameters(self._method, parameters)
        with self._lock:
            if self._phase != "idle":
                raise RuntimeError("a run of this analysis is already in flight")
            self._phase = "pre"
            self._complete = False
            self._generation += 1
            self._target, self._focus = values, focus_pts
        try:
            self._run(progress)
        finally:
            with self._lock:
                self._phase = "idle"
            self._refresh_pts()

    def retarget(self, parameters: ParameterSet, *, focus_pts: int | None = None) -> bool:
        """Offer new parameters to the run in flight (main thread; never waits for the run).

        Args:
            parameters: The new parameter set.
            focus_pts: The displayed frame's pts ticks, or None.

        Returns:
            True when the run in flight finishes under ``parameters``; False when it does not
            (a job the engine returned is then kept for the next ``run``).
        """
        values = effective_parameters(self._method, parameters)
        with self._lock:
            if self._phase == "pre":  # the engine's job has not started: it starts with these
                self._target, self._focus = values, focus_pts
                return True
            if self._phase != "engine":
                self._complete = False
                return False
        with self._engine_lock:
            with self._lock:
                self._target, self._focus = values, focus_pts
                engine = self._engine
                in_flight = self._phase == "engine"
            assert engine is not None
            job = engine.set_parameters(values, focus_pts)
            if job is not None:
                with self._lock:
                    self._kept = job
                    self._complete = False
                return False
        if not in_flight:
            with self._lock:
                self._complete = False
        return in_flight

    def pts(self) -> tuple[int, ...]:
        """Return the pts ticks stored so far, ascending (main thread; never calls the cache)."""
        with self._lock:
            return self._pts

    def proxy(self, pts_ticks: int) -> NDArray[np.uint8]:
        """Return a stored proxy (worker thread).

        Args:
            pts_ticks: A pts value from :meth:`pts`.

        Returns:
            The proxy pixels.

        Raises:
            KeyError: No proxy is stored for ``pts_ticks`` (or the clip's key is not known yet).
        """
        with self._lock:
            key = self._key
        if key is None:
            raise KeyError(pts_ticks)
        return self._cache.proxy(key, pts_ticks)

    def statistics(self, pts_ticks: int) -> Mapping[str, Statistics] | None:
        """Return the smoothed statistics of one frame, or None (worker thread).

        None until a whole run has completed under the latest parameters, and when a run
        started while this read was under way (the generation is read before and after).

        Args:
            pts_ticks: The frame's pts ticks.

        Returns:
            Stage name -> statistics, or None.
        """
        with self._lock:
            if not self._complete or self._engine is None:
                return None
            generation, engine = self._generation, self._engine
        try:
            record = engine.smoothed_record(pts_ticks)
        except KeyError:
            return None
        with self._lock:
            if generation != self._generation or not self._complete:
                return None
        return record

    # --- the run ------------------------------------------------------------------------------

    def _run(self, progress: Progress) -> None:
        """The run's body (worker thread): cache, key, selection, lock, engine, job."""
        if not wait_for_cache(self._cache, progress):
            return
        key = self._key_once()
        self._refresh_pts()
        video = self._probe.video
        backend, reason = self._select(self._settings(), video.height, video.width, self._method.id)
        self.devices.append(reason)
        _LOG.info("analysis %s: device %s", self._name, reason)
        if not self._locks.acquire(key, progress):
            return
        try:
            engine = self._engine_for(backend, key)
            with self._engine_lock:
                with self._lock:
                    values, focus = self._target, self._focus
                    self._phase = "engine"
                job = self._next_job(engine, values, focus)
                if job is None:  # complete under the latest parameters already
                    with self._lock:
                        self._phase = "post"
                        self._complete = self._kept is None
                    return
            result = job(_Reporter(progress, self._refresh_pts))
            with self._engine_lock, self._lock:
                # Published with the phase, so a retarget after this point (phase "post")
                # clears it and nothing later sets it again from a stale snapshot (R1-7).
                self._phase = "post"
                self._complete = result.ok and self._kept is None
        finally:
            self._locks.release(key)
        if result.ok:
            return
        if result.failure == ANALYSIS_CANCELLED:
            return
        raise RuntimeError(result.failure or "the analysis failed")

    def _key_once(self) -> CacheKey:
        """Take the clip's cache key once (``os.stat``, on the worker)."""
        with self._lock:
            key = self._key
        if key is None:
            key = self._cache.key_for(self._path)
            with self._lock:
                self._key = key
        return key

    def _engine_for(self, backend: ArrayBackend, key: CacheKey) -> AnalysisEngine:
        """Return the engine on ``backend``'s device, building or rebuilding it (ruling S2).

        A rebuilt engine drops the old one's kept job: its first job runs under the latest
        parameters anyway. Construction is light (no device work until a job runs); the frame
        count may list the packets of a ``truncated`` clip once.
        """
        if self._engine is not None and self._device == backend.device:
            return self._engine
        if self._expected is None:
            self._expected = (expected_frames(self._probe),)
        with self._lock:
            values = self._target
        engine = self._engine_factory(
            method=self._method,
            backend=backend,
            cache=self._cache,
            key=key,
            source=self._source_for(None if backend.device == "cpu" else backend),
            probe=self._probe,
            params=values,
            hw_decode=backend.device != "cpu",
            expected_frames=self._expected[0],
        )
        with self._engine_lock, self._lock:
            self._engine = engine
            self._device = backend.device
            self._kept = None
        return engine

    def _next_job(
        self, engine: AnalysisEngine, values: dict[str, Any], focus: int | None
    ) -> Callable[[Progress], JobResult] | None:
        """Return the job this run executes, or None when complete (under the engine lock).

        A kept job first (erratum 1), after the latest parameters were offered to it; else the
        first call's ``analysis_job``; else the recompute ``set_parameters`` returns, or a new
        ``analysis_job`` after a cancel or a failure.
        """
        with self._lock:
            kept, self._kept = self._kept, None
        if kept is not None:
            engine.set_parameters(values, focus)  # the kept job is running: it absorbs them
            return kept
        if engine.state().phase == "none":
            engine.set_parameters(values, focus)  # adopted for the first job
            return engine.analysis_job()
        job = engine.set_parameters(values, focus)
        if job is not None:
            return job
        if engine.state().phase in ("none", "cancelled", "failed"):
            return engine.analysis_job()
        return None

    def _refresh_pts(self) -> None:
        """Re-read the stored pts from the cache (worker thread only)."""
        with self._lock:
            key = self._key
        if key is None:
            return
        try:
            entry = self._cache.lookup(key)
        except (OSError, RuntimeError):
            return
        ticks = () if entry is None else tuple(entry.pts_ticks)
        with self._lock:
            self._pts = ticks


def make_analysis_factory(
    settings: Callable[[], Settings],
    *,
    locks: ClipLocks,
    engine_factory: EngineFactory = AnalysisEngine,
    source_for: Callable[[ArrayBackend | None], VideoSource] = composition.video_source,
    on_built: Callable[[EngineClipAnalysis], None] | None = None,
) -> Callable[[AnalysedSource, CorrectionMethod, AnalysisEngines], EngineClipAnalysis]:
    """Return the GUI's analysis factory over WP3.11's engine (``install_timeline``'s argument).

    Args:
        settings: Returns the settings in force (the session's ``settings``).
        locks: The per-clip locks shared with the export wrapper.
        engine_factory: Builds each engine (tests hold a run with it).
        source_for: Builds an engine's frame source from its device backend.
        on_built: When given, called with each adapter the factory builds (the application
            keeps the latest one only, for its tests and the V7 driver; R1-8).

    Returns:
        The factory: ``(source, method, engines) -> EngineClipAnalysis``. It builds only (main
        thread) and raises ``ValueError`` for a source without a probe and ``TypeError`` when
        ``engines.cache`` is not the application's cache.
    """

    def factory(
        source: AnalysedSource, method: CorrectionMethod, engines: AnalysisEngines
    ) -> EngineClipAnalysis:
        probe = source.probe
        if probe is None:
            raise ValueError("the analysis needs a video source")
        cache = engines.cache
        if not isinstance(cache, DeferredProxyCache):
            raise TypeError("the analysis needs the application's cache")
        analysis = EngineClipAnalysis(
            path=source.path,
            probe=probe,
            method=method,
            cache=cache,
            select_backend=engines.select_backend,
            settings=settings,
            locks=locks,
            engine_factory=engine_factory,
            source_for=source_for,
        )
        if on_built is not None:
            on_built(analysis)
        return analysis

    return factory
