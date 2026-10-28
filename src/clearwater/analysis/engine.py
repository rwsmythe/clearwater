"""The analysis engine of one clip: decode pass, staged statistics, smoothing, recompute (7.2, 7.3).

:class:`AnalysisEngine` turns a clip into smoothed per-frame statistics:

1. **Decode pass** (7.2 item 1, D70, D86): every frame once; its uint8 proxy (AD-5) is stored in
   the cache and READ BACK, and the first stage is measured on the read-back proxy (it has no
   earlier stage). ``mark_complete`` follows the last frame, never a failure and never after a
   cancel the job has seen; a cancel during or after ``mark_complete`` leaves a complete entry.
   A complete cache entry skips the pass (V17); a source-only first stage is then read back
   with ``source_statistics`` and passed through ``closed_form`` (Y-1 (e)).
2. **Staged statistics** (7.2 item 2, D97, D57): each later stage is measured on every STORED
   proxy with the SMOOTHED records of all earlier stages, then smoothed over pts.
3. **Recompute** (7.3, AD-7): a parameter change invalidates from the first stage that depends
   on a changed parameter; a stage whose ``closed_form`` answers is updated without reading a
   proxy; the others are re-measured first over the displayed frame's cumulative reach, then
   over the rest of the clip. ``"complete"`` is reported only when every stage is smoothed for
   every frame under the current parameters (AD-15: export waits for it).

Threading: the jobs this engine returns run on one worker thread at a time (the only writer of
the store and the only caller of the cache's store methods); ``state``, ``smoothed_record``,
``provisional_record`` and ``is_complete`` may be called from any thread.

**Streamed analysis** (WP3.21; AD-7 as read at ruling Q2): ``analysis_job(stream=True)`` runs the
same passes, but every :data:`STREAM_STEP` or more first-stage records it measures and smooths
each later stage as far as its records are FINAL, and publishes how many frames from the clip's
start hold a final record of every stage. ``smoothed_record`` then waits for a frame's record to
be final, so an export can render beside the analysis with exactly the whole-clip records. A
record is final once the first stage's raw records cover the composed reach of every stage
(:func:`composed_reach`) and, on a decoded prefix, one more frame follows that reach (the
``at_end`` margin, :func:`lead_frames`).
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass, replace
from fractions import Fraction
from typing import Any, Literal

import numpy as np
from numpy.typing import NDArray

from clearwater.interfaces import (
    ArrayBackend,
    CacheKey,
    CorrectionMethod,
    Frame,
    Image,
    JobResult,
    ProbeResult,
    Progress,
    ProxyCache,
    Stage,
    Statistics,
    VideoSource,
)

from .proxy import frame_pixels_for_proxy, make_proxy, proxy_image
from .smoothing import DEFAULT_KIND, DEFAULT_WINDOW_S, KINDS, LOCAL_KINDS, exact_window, reach
from .store import AnalysisStore, SchemaMismatchError, same_value, schema_hash

_LOG = logging.getLogger(__name__)

type Phase = Literal["none", "running", "complete", "cancelled", "failed"]
"""The phase of a clip's analysis; the values of ``gui.contract.AnalysisPhase`` (AD-15)."""

CANCELLED = "cancelled"
"""The ``JobResult.failure`` of a cancelled job."""

SMOOTH_CHUNK = 2048
"""Frames per chunk when a stage is smoothed for the whole clip; a cancel is checked between
chunks (task 8), so it waits for one chunk, not the stage (0.3-0.7 s per statistic at 107,892
frames when smoothed whole)."""

STREAM_STEP = 16
"""Fewest new first-stage records between two advances of a streamed analysis; an advance also
waits for 1/:data:`STREAM_SHARE` of the records in, so the store's whole-axis copies in
``smooth_at`` cost O(n log n) over a clip rather than O(n^2)."""

STREAM_SHARE = 64
"""See :data:`STREAM_STEP`."""

STREAM_WAIT_S = 1.0
"""How long a read of a streamed record waits between two looks when no publication wakes it."""


@dataclass(frozen=True)
class AnalysisSnapshot:
    """The engine's state, with the fields of ``gui.contract.AnalysisState`` (AD-15).

    Attributes:
        phase: ``"none"`` (no job yet), ``"running"``, ``"complete"``, ``"cancelled"`` (the
            unloaded state) or ``"failed"``.
        done: Frame-stage units done in the running job.
        total: The job's total units, or None while unknown.
        message: The pass being run, or the failure message when ``"failed"``.
    """

    phase: Phase = "none"
    done: int = 0
    total: int | None = None
    message: str = ""


class RenderBeforeFinalError(RuntimeError):
    """A streamed record was about to be read before it is final (the overlap's guard, WP3.21)."""


class AnalysisStoppedError(RuntimeError):
    """A streamed analysis stopped (cancelled or failed) before the record asked for was final."""


def composed_reach(
    ticks: Sequence[int] | NDArray[np.int64],
    time_base: Fraction,
    window_s: float | Fraction | str,
    kind: str,
    stages: int,
    index: int,
) -> tuple[int, int]:
    """Return the first stage's raw records that the last of ``stages`` stages reads for one frame.

    The engine measures every later stage with the SMOOTHED records of ALL earlier stages
    (``_measure``), so the stage graph it runs is a chain whatever ``depends_on_stages``
    declares: the last stage's record of frame ``index`` reads that stage's raw records over
    :func:`~clearwater.analysis.smoothing.reach`, each of which reads the earlier stage's
    smoothed record, and so on to the first stage (ruling Q2 (a), Q-c). Over pts, so VFR holds.

    Args:
        ticks: The axis's pts ticks, strictly ascending.
        time_base: Seconds per tick.
        window_s: The smoothing window in seconds.
        kind: The smoothing kind.
        stages: The number of stages (at least 1).
        index: The frame's index on the axis.

    Returns:
        ``(first, last)`` indices of the first stage's raw records read, inclusive.

    Raises:
        ValueError: No stage, or what :func:`~clearwater.analysis.smoothing.reach` refuses.
    """
    if stages < 1:
        raise ValueError(f"a method has at least one stage, got {stages}")
    span = (index, index)
    for _ in range(stages):
        span = reach(ticks, time_base, window_s, kind, *span)
    return span


def lead_frames(
    ticks: Sequence[int] | NDArray[np.int64],
    time_base: Fraction,
    window_s: float | Fraction | str,
    kind: str,
    stages: int,
    index: int,
) -> int:
    """Return how many frames after ``index`` must be decoded before its record is final.

    The composed reach's end (:func:`composed_reach`) less ``index``, plus ONE: on a decoded
    prefix ``smooth_series`` sets ``at_end`` when a reach ends on the prefix's last frame, which
    it cannot tell from the clip's last, so one more frame must follow (Q-c). At 30000/1001 with
    the default 2 s ``median_gaussian`` each smoothing reads 29 + 1 frames, so the lead is 61 for
    two stages (c3) and 91 for three (ancuti2018). It is derived at run time from the axis, so a
    VFR clip gives its own figure; give the whole clip's axis (near the end the reach is clipped).

    Args:
        ticks: The clip's pts ticks, strictly ascending.
        time_base: Seconds per tick.
        window_s: The smoothing window in seconds.
        kind: The smoothing kind.
        stages: The number of stages.
        index: The frame's index on the axis.

    Returns:
        The lead in frames.
    """
    return composed_reach(ticks, time_base, window_s, kind, stages, index)[1] - index + 1


def _usable_end(raw: int, known: int, whole: bool) -> int:
    """Return the last first-stage index a final record's reach may end on (-1 when none).

    ``raw`` first-stage records are in, from the start of an axis of ``known`` frames; on a
    decoded prefix (``whole`` False) one more frame must follow the reach (the ``at_end`` margin).
    """
    return raw - 1 if whole else min(raw, known - 1) - 1


@dataclass(frozen=True)
class _Published:
    """What a streamed analysis has published for its readers (under the stream's condition).

    Attributes:
        ticks: The axis as known: the decoded prefix, or the whole clip (a complete cache entry).
        raw: First-stage raw records in, from the axis's start.
        whole: True when ``ticks`` is the whole clip.
        final: Frames from the axis's start that hold a final record of every stage.
        state: ``"running"``, ``"complete"`` (every record final) or ``"stopped"``.
    """

    ticks: NDArray[np.int64]
    raw: int
    whole: bool
    final: int
    state: Literal["running", "complete", "stopped"]


class _Stream:
    """A streamed job's state: the counts the analysis thread owns and what it has published.

    Attributes:
        cond: Guards ``published``; notified at every publication.
        published: The latest publication.
        raw: Per stage, the raw records measured from the axis's start.
        smoothed: Per stage, the outputs smoothed (final) from the axis's start.
        advanced: First-stage records in at the last advance.
        closed: Per stage, whether ``closed_form`` answers (``_measure``'s memo across calls).
    """

    def __init__(self, stages: int) -> None:
        self.cond = threading.Condition()
        self.published = _Published(np.zeros(0, dtype=np.int64), 0, False, 0, "running")
        self.raw = [0] * stages
        self.smoothed = [0] * stages
        self.advanced = 0
        self.closed: dict[str, bool | None] = {}


class _CancelledError(Exception):
    """The user cancelled the job."""


class _SupersededError(Exception):
    """The parameters changed; the job restarts its stage loop under the new ones."""


@dataclass
class _Pending:
    """What one pass of the job's loop works under (taken from the engine under its lock)."""

    generation: int
    params: dict[str, Any]
    schema: str
    first_invalid: int | None
    around_pts: int | None


class AnalysisEngine:
    """Analysis of one clip against one method, cache entry and frame source (WP3.11)."""

    def __init__(
        self,
        *,
        method: CorrectionMethod,
        backend: ArrayBackend,
        cache: ProxyCache,
        key: CacheKey,
        source: VideoSource,
        probe: ProbeResult,
        params: Mapping[str, Any],
        window_s: float = DEFAULT_WINDOW_S,
        kind: str = DEFAULT_KIND,
        hw_decode: bool = False,
    ) -> None:
        """Create the engine; nothing runs until a job from :meth:`analysis_job` runs.

        Args:
            method: The correction method (IF-3).
            backend: Where statistics are measured (IF-2).
            cache: The proxy cache (IF-7).
            key: The clip's cache key.
            source: The frame source (IF-5).
            probe: The clip's probe result (time base, frame count, colour).
            params: The effective parameter values.
            window_s: The smoothing window in seconds (AD-3 default 2.0, PROVISIONAL).
            kind: The smoothing kind (AD-3 default ``"median_gaussian"``).
            hw_decode: Passed to the frame source.

        Raises:
            ValueError: The method has no stage, an unknown kind or an unusable window.
        """
        if not method.stages:
            raise ValueError(f"method {method.id!r} declares no stage")
        if kind not in KINDS:
            raise ValueError(f"unknown smoothing kind {kind!r}")
        exact_window(window_s)
        self._method = method
        self._stages: tuple[Stage, ...] = tuple(method.stages)
        self._backend = backend
        self._cache = cache
        self._key = key
        self._source = source
        self._probe = probe
        self._time_base = probe.video.time_base
        self._window_s = window_s
        self._kind = kind
        self._hw_decode = hw_decode
        self._lock = threading.Lock()
        self._params: dict[str, Any] = dict(params)
        self._hash = schema_hash(method, self._params, kind, window_s)
        self._store = AnalysisStore(self._stages, self._hash, self._time_base)
        self._measured = AnalysisStore(self._stages, self._hash, self._time_base)
        self._state = AnalysisSnapshot()
        self._running = False
        self._generation = 0
        self._first_invalid: int | None = None
        self._around: int | None = None
        self._decoded = False
        self._cancel = threading.Event()
        self._stream: _Stream | None = None

    # --- public API ---------------------------------------------------------------------------

    @property
    def store(self) -> AnalysisStore:
        """The clip's statistics store (IF-4)."""
        return self._store

    @property
    def schema_hash(self) -> str:
        """The schema hash of the current parameters and smoother (question 5)."""
        with self._lock:
            return self._hash

    @property
    def parameters(self) -> dict[str, Any]:
        """A copy of the current parameter values."""
        with self._lock:
            return dict(self._params)

    def state(self) -> AnalysisSnapshot:
        """Return the current state (phase, progress, message)."""
        with self._lock:
            return self._state

    def is_complete(self) -> bool:
        """Return True when every stage is smoothed for every frame under the current parameters."""
        with self._lock:
            return self._state.phase == "complete"

    def analysis_job(self, *, stream: bool = False) -> Callable[[Progress], JobResult]:
        """Return the IF-8 job that analyses the clip to completion; the phase becomes running.

        The job runs the decode pass (unless the cache entry is complete), then every stage not
        yet smoothed under the current parameters; parameter changes that arrive while it runs
        are absorbed by it. Cancel (the progress's or :meth:`cancel`) returns to the unloaded
        state.

        Args:
            stream: Publish each frame's record once it is final, while the job runs, and make
                :meth:`smoothed_record` wait for it (WP3.21; an export's own engine). Only an
                engine's first job streams, and its parameters are then fixed.

        Returns:
            A callable for ``JobRunner.run``.

        Raises:
            RuntimeError: A job of this engine is already running, or ``stream`` is asked of
                an engine that has run a job.
        """
        with self._lock:
            if self._running:
                raise RuntimeError("an analysis job of this clip is already running")
            if stream:
                if self._state.phase != "none":
                    raise RuntimeError("only an engine's first analysis job can stream")
                self._stream = _Stream(len(self._stages))
            self._running = True
            self._cancel.clear()
            self._state = AnalysisSnapshot("running", 0, None, "starting")
        return self._job

    def set_parameters(
        self, params: Mapping[str, Any], around_pts: int | None
    ) -> Callable[[Progress], JobResult] | None:
        """Apply new parameter values (7.3, AD-7).

        A value is changed when it differs as ``schema_hash`` hashes it (numbers by their float
        value, a ``bool`` distinct from ``1``), so change detection and the hash agree. The
        first invalidated stage is the first whose ``depends_on_parameters`` names a
        changed value; it and every later stage are recomputed, first for the frames within the
        cumulative smoothing reach of ``around_pts``, then for the rest of the clip.

        Args:
            params: The new effective parameter values.
            around_pts: The displayed frame's pts ticks, or None.

        Returns:
            A job to run when the change needs a recompute and no job is running; None when a
            running job absorbs the change, when no stage depends on a changed value, or when
            the clip is not analysed (phase none, cancelled or failed: the next
            :meth:`analysis_job` uses the new values).

        Raises:
            RuntimeError: The engine streams (its parameters are fixed).
        """
        new = dict(params)
        with self._lock:
            if self._stream is not None:
                raise RuntimeError("the parameters of a streamed analysis are fixed")
            old = self._params
            changed = {
                name
                for name in set(old) | set(new)
                if (name in old) != (name in new) or not same_value(old.get(name), new.get(name))
            }
            first = next(
                (
                    index
                    for index, stage in enumerate(self._stages)
                    if changed.intersection(stage.depends_on_parameters)
                ),
                None,
            )
            if first is None:
                self._params = new
                return None
            new_hash = schema_hash(self._method, new, self._kind, self._window_s)
            self._params = new
            self._hash = new_hash
            self._generation += 1
            self._first_invalid = (
                first if self._first_invalid is None else min(first, self._first_invalid)
            )
            self._around = around_pts
            if self._running:
                return None
            if self._state.phase != "complete":
                self._first_invalid = None
                self._around = None
                return None
            self._running = True
            self._cancel.clear()
            self._state = AnalysisSnapshot("running", 0, None, "recomputing")
        return self._job

    def cancel(self) -> None:
        """Ask the running job to stop; it returns to the unloaded state within one frame.

        The job checks for a cancel after every frame and every smoothing, and once more under
        the engine's lock before it publishes ``"complete"``; a cancel after that is too late
        and leaves the analysis complete.
        """
        self._cancel.set()

    def smoothed_record(
        self, pts_ticks: int, *, schema_hash: str | None = None
    ) -> dict[str, Statistics]:
        """Return every stage's smoothed statistics for one frame, for render (7.2 item 3).

        Available for a frame once its values are final under the current parameters: after
        the whole analysis, or after a recompute's near phase for the displayed frame. On a
        streamed engine the call WAITS until the frame's record is final (or the analysis has
        stopped) and checks finality against the composed reach before it reads (WP3.21).

        Args:
            pts_ticks: The frame's pts ticks.
            schema_hash: When given, the hash the caller renders under.

        Returns:
            Stage name -> statistics, in stage order.

        Raises:
            SchemaMismatchError: ``schema_hash`` is not the current parameters' hash.
            KeyError: The frame's smoothed statistics are not (yet) available.
            AnalysisStoppedError: A streamed analysis stopped before the record was final.
            RenderBeforeFinalError: A streamed analysis published the frame as final while its
                composed reach says it is not (the overlap's guard).
        """
        stream = self._stream
        if stream is None:
            return self._read(pts_ticks, schema_hash)
        with stream.cond:
            while True:
                published = stream.published
                if published.state == "stopped":
                    raise AnalysisStoppedError(
                        f"the analysis stopped before the record of pts {pts_ticks} was final"
                    )
                if published.state == "complete" or self._is_final(published, int(pts_ticks)):
                    # Read under the condition: a stopping analysis publishes "stopped" under
                    # it BEFORE it clears the store, so this read never meets a cleared store.
                    return self._read(pts_ticks, schema_hash)
                stream.cond.wait(STREAM_WAIT_S)

    def streamed(self) -> tuple[int, bool]:
        """Return a streamed analysis's final frames from the clip's start and whether it ended.

        Returns:
            ``(final, ended)``; ``(0, False)`` before the first publication, and for an engine
            that does not stream.
        """
        stream = self._stream
        if stream is None:
            return 0, False
        with stream.cond:
            published = stream.published
        return published.final, published.state != "running"

    def _is_final(self, published: _Published, pts: int) -> bool:
        """Tell whether ``pts`` may be read under ``published``; the guard raises otherwise."""
        index = int(np.searchsorted(published.ticks, pts))
        if index >= published.final:
            return False
        if int(published.ticks[index]) != pts:
            return True  # not on the axis inside the final part: the read raises KeyError
        last = composed_reach(
            published.ticks, self._time_base, self._window_s, self._kind, len(self._stages), index
        )[1]
        usable = _usable_end(published.raw, len(published.ticks), published.whole)
        if last > usable:
            raise RenderBeforeFinalError(
                f"pts {pts} (frame {index}) was published final, but its record reads the first "
                f"stage's raw records out to frame {last} and {published.raw} of "
                f"{len(published.ticks)} known frames are in"
                + ("" if published.whole else ", with one more needed after its reach")
                + f": {published.raw - 1 - index} frames after it, lead "
                f"{last - index + 1} (render before final)"
            )
        return True

    def _read(self, pts_ticks: int, schema_hash: str | None) -> dict[str, Statistics]:
        """Read every stage's smoothed record of one frame (see :meth:`smoothed_record`)."""
        with self._lock:
            current = self._hash
        if schema_hash is not None and schema_hash != current:
            raise SchemaMismatchError(
                f"statistics asked for under schema {schema_hash[:12]}..., "
                f"the current schema is {current[:12]}..."
            )
        try:
            return {
                stage.name: self._store.smoothed(pts_ticks, stage.name, schema_hash=current)
                for stage in self._stages
            }
        except SchemaMismatchError:
            raise KeyError(f"the statistics of pts {pts_ticks} are being recomputed") from None

    def provisional_record(self, pts_ticks: int) -> dict[str, Statistics] | None:
        """Return a frame's own unsmoothed chain on its STORED proxy (D108, V18; question 4).

        Each stage is measured with that frame's own unsmoothed earlier records, under the
        current parameters, on the caller's thread. Nothing is stored.

        Args:
            pts_ticks: The frame's pts ticks.

        Returns:
            Stage name -> statistics, or None while the frame's proxy is not stored.
        """
        try:
            stored = self._cache.proxy(self._key, pts_ticks)
        except KeyError:
            return None
        params = self.parameters
        image = self._image(stored)
        results: dict[str, Statistics] = {}
        for stage in self._stages:
            results[stage.name] = self._method.analyze(stage.name, image, params, dict(results))
        return results

    # --- the job ------------------------------------------------------------------------------

    def _job(self, progress: Progress) -> JobResult:
        """Run the state machine to completion (IF-8)."""
        start = time.perf_counter()
        failure: str | None = None
        completed = False
        try:
            self._drive(progress)
            completed = True
        except _CancelledError:
            failure = CANCELLED
            self._end_stream(completed=False)  # before the store is cleared (smoothed_record)
            self._unload(AnalysisSnapshot("cancelled", 0, None, "analysis cancelled"))
        except Exception as exc:  # a failure is a failed result with its message
            failure = f"{type(exc).__name__}: {exc}"
            self._end_stream(completed=False)
            self._unload(AnalysisSnapshot("failed", 0, None, failure))
        finally:
            self._end_stream(completed=completed)
        return JobResult(
            ok=failure is None,
            outputs=(),
            warnings=(),
            failure=failure,
            device=self._backend.device,
            elapsed_s=time.perf_counter() - start,
        )

    def _unload(self, state: AnalysisSnapshot) -> None:
        """Drop every in-memory statistic and end the job in ``state`` (no mark_complete)."""
        with self._lock:
            self._store.clear()
            self._measured.clear()
            self._store.schema_hash = self._hash
            self._measured.schema_hash = self._hash
            self._decoded = False
            self._first_invalid = None
            self._around = None
            self._state = state
            self._running = False

    def _end_stream(self, *, completed: bool) -> None:
        """Publish a streamed job's end once: every record final, or stopped (readers wake)."""
        stream = self._stream
        if stream is None:
            return
        with stream.cond:
            if stream.published.state != "running":
                return
            if completed:
                ticks = np.asarray(self._store.axis(), dtype=np.int64)
                stream.published = _Published(ticks, len(ticks), True, len(ticks), "complete")
            else:
                stream.published = replace(stream.published, state="stopped")
            stream.cond.notify_all()

    def _take(self) -> _Pending:
        """Take the current parameters and the pending invalidation."""
        with self._lock:
            pending = _Pending(
                self._generation, dict(self._params), self._hash, self._first_invalid, self._around
            )
            self._first_invalid = None
            self._around = None
            return pending

    def _check(self, progress: Progress, generation: int | None) -> None:
        """Raise when cancelled, or (given a generation) when the parameters have changed."""
        if self._cancel.is_set() or progress.cancelled():
            raise _CancelledError
        if generation is not None and self._generation != generation:
            raise _SupersededError

    def _report(self, progress: Progress, done: int, total: int | None, message: str) -> None:
        """Publish progress to the state and to the job's progress."""
        with self._lock:
            self._state = replace(self._state, done=done, total=total, message=message)
        progress.report(done, total, message)

    def _drive(self, progress: Progress) -> None:
        """Loop: apply pending changes, decode if needed, run the stages; end when settled."""
        counter: list[Any] = [0, None]  # frame-stage units done, total (None while unknown)
        while True:
            pending = self._take()
            # Invalidate BEFORE re-hashing: until the store holds the new hash a reader's hash
            # mismatches (KeyError), and by then the old records of the changed stages are gone.
            if pending.first_invalid is not None:
                self._store.invalidate_from(self._stages[pending.first_invalid].name)
            self._store.schema_hash = pending.schema
            self._measured.schema_hash = pending.schema
            if not self._decoded:
                self._load(progress, pending, counter)
                self._decoded = True
            try:
                self._run_stages(progress, pending, counter)
            except _SupersededError:
                continue
            self._check(progress, None)
            with self._lock:
                if self._cancel.is_set():
                    raise _CancelledError
                if self._generation != pending.generation:
                    continue
                self._state = AnalysisSnapshot(
                    "complete", counter[0], counter[0], "analysis complete"
                )
                self._running = False
                return

    # --- decode pass and reopen ---------------------------------------------------------------

    def _image(self, stored: NDArray[np.uint8]) -> Image:
        """The float image of a stored proxy, as every statistic is measured on (AD-5)."""
        return proxy_image(stored, self._backend, self._probe.video.color, True)

    def _load(self, progress: Progress, pending: _Pending, counter: list[Any]) -> None:
        """Run the decode pass, or read a complete cache entry (V17)."""
        entry = self._cache.lookup(self._key)
        if entry is not None and entry.complete:
            if not entry.pts_ticks:
                raise ValueError("the complete cache entry holds no frames")
            self._store.ensure_axis(entry.pts_ticks)
            self._measured.ensure_axis(entry.pts_ticks)
            first = self._stages[0]
            if first.source_only and first.name in entry.stages:
                # Reading the cache adds no units: the stage's closed form counts each frame once.
                for pts in entry.pts_ticks:
                    self._check(progress, None)
                    record = self._cache.source_statistics(self._key, first.name, pts)
                    self._measured.put(pts, first.name, record)
                    self._report(progress, counter[0], None, "reading cached statistics")
            return
        self._decode(progress, pending, counter)

    def _decode(self, progress: Progress, pending: _Pending, counter: list[Any]) -> None:
        """The decode pass: proxies stored and read back, the first stage measured on them."""
        first = self._stages[0]
        total = self._probe.video.nb_frames
        later = len(self._stages) - 1
        counter[1] = None if total is None else counter[0] + total * (1 + later)
        frames: Iterator[Frame] = iter(self._source.frames(self._probe, hw_decode=self._hw_decode))
        decoded: list[int] = []
        last: int | None = None
        shape: tuple[int, ...] | None = None
        try:
            for frame in frames:
                self._check(progress, None)
                pts = int(frame.pts_ticks)
                if last is not None and pts <= last:
                    raise ValueError(
                        f"the frame source returned pts {pts} after pts {last}: frames out of "
                        "order or duplicated"
                    )
                pixels = frame_pixels_for_proxy(frame, self._backend)  # a GPU frame stays there
                if shape is not None and pixels.shape != shape:
                    raise ValueError(
                        f"the frame at pts {pts} is {pixels.shape}, earlier frames {shape}: "
                        "the frame size changed within the clip"
                    )
                shape = pixels.shape
                proxy = make_proxy(pixels, self._backend)
                self._cache.store_proxy(self._key, pts, proxy)
                stored = self._cache.proxy(self._key, pts)
                record = self._method.analyze(first.name, self._image(stored), pending.params, {})
                self._measured.put(pts, first.name, record)
                self._store.put(pts, first.name, record, schema_hash=pending.schema)
                if first.source_only:
                    self._cache.store_source_statistics(self._key, first.name, pts, record)
                decoded.append(pts)
                last = pts
                counter[0] += 1
                self._report(progress, counter[0], counter[1], "decoding")
                if self._stream is not None:
                    self._advance(progress, pending, counter, len(decoded), whole=False)
        finally:
            close = getattr(frames, "close", None)
            if close is not None:
                try:
                    close()
                except Exception as exc:  # a cleanup error is a log line, never the pass's outcome
                    _LOG.warning("the decode stream's close raised %s: %s", type(exc).__name__, exc)
        if not decoded:
            raise ValueError("the frame source yielded no frames")
        self._check(progress, None)  # a cancel raised by the last frame's report
        entry = self._cache.lookup(self._key)
        stale = sorted(set(entry.pts_ticks) - set(decoded)) if entry is not None else []
        if stale:
            # IF-7 offers no delete, so an entry holding frames this pass did not decode (the
            # tail of an earlier, longer pass) is left incomplete rather than marked complete.
            raise ValueError(
                f"the cache entry holds {len(stale)} proxies not decoded by this pass (first at "
                f"pts {stale[0]}): it cannot be marked complete"
            )
        self._check(progress, None)  # a cancel that arrived during the lookup
        self._cache.mark_complete(self._key)

    # --- stages -------------------------------------------------------------------------------

    def _run_stages(self, progress: Progress, pending: _Pending, counter: list[Any]) -> None:
        """Bring every stage to smoothed-for-every-frame, near frames first after a change."""
        generation = pending.generation
        axis = self._store.axis()
        todo = [
            index
            for index, stage in enumerate(self._stages)
            if not self._store.smoothed_complete(stage.name)
        ]
        if not todo:
            return
        counter[1] = counter[0] + sum(
            len(self._store.raw_missing(self._stages[i].name)) for i in todo
        )
        if pending.around_pts is not None:
            self._near_phase(progress, pending, todo[0], axis, counter)
        stream = self._stream
        if stream is not None and len(self._store.raw_missing(self._stages[0].name)) == len(axis):
            self._stream_stored(progress, pending, counter, axis)
        memo = None if stream is None else stream.closed
        for index in todo:
            stage = self._stages[index]
            message = f"stage {stage.name} ({index + 1} of {len(self._stages)})"
            self._measure(
                progress,
                pending,
                stage,
                self._store.raw_missing(stage.name),
                counter,
                message,
                memo,
            )
            self._smooth_stage(progress, generation, stage)
            self._check(progress, generation)

    def _smooth_stage(self, progress: Progress, generation: int, stage: Stage) -> None:
        """Smooth a stage for every frame, in chunks of outputs with a cancel check between.

        ``smooth_at`` over consecutive chunks equals ``smooth`` over the whole clip (each output
        reads its own windows). A step-aware kind reads the whole series, so it is smoothed in
        one call (limit: a cancel then waits for the stage's smoothing). A streamed job starts
        after the outputs it has already smoothed (they are final).
        """
        if self._kind not in LOCAL_KINDS:
            self._check(progress, generation)
            self._store.smooth(stage.name, stage.smoothed, self._window_s, self._kind)
            return
        axis = self._store.axis()
        start = 0 if self._stream is None else self._stream.smoothed[self._stages.index(stage)]
        for lo in range(start, len(axis), SMOOTH_CHUNK):
            self._check(progress, generation)
            hi = min(lo + SMOOTH_CHUNK, len(axis)) - 1
            self._store.smooth_at(
                stage.name, stage.smoothed, self._window_s, self._kind, axis[lo], axis[hi]
            )

    def _near_phase(
        self,
        progress: Progress,
        pending: _Pending,
        first: int,
        axis: tuple[int, ...],
        counter: list[Any],
    ) -> None:
        """Re-measure the displayed frame's cumulative reach first (AD-7).

        With ``R_last = reach({p})`` and ``R_s = reach(R_{s+1})``, stage ``s`` is measured on
        ``R_s`` and smoothed on ``R_{s+1}`` (the last stage on ``p`` alone), so ``p``'s smoothed
        statistics are final when the phase ends.
        """
        assert pending.around_pts is not None
        centre = int(np.clip(np.searchsorted(axis, pending.around_pts), 0, len(axis) - 1))
        outputs: list[tuple[int, int]] = [(centre, centre)] * len(self._stages)
        needed: list[tuple[int, int]] = [(centre, centre)] * len(self._stages)
        span = (centre, centre)
        for index in range(len(self._stages) - 1, first - 1, -1):
            outputs[index] = span
            span = reach(axis, self._time_base, self._window_s, self._kind, *span)
            needed[index] = span
        for index in range(first, len(self._stages)):
            stage = self._stages[index]
            lo, hi = needed[index]
            wanted = set(axis[lo : hi + 1])
            missing = [pts for pts in self._store.raw_missing(stage.name) if pts in wanted]
            message = f"recomputing near the displayed frame: {stage.name}"
            self._measure(progress, pending, stage, missing, counter, message)
            self._check(progress, pending.generation)
            out_lo, out_hi = outputs[index]
            self._store.smooth_at(
                stage.name, stage.smoothed, self._window_s, self._kind, axis[out_lo], axis[out_hi]
            )
            self._check(progress, pending.generation)

    def _measure(
        self,
        progress: Progress,
        pending: _Pending,
        stage: Stage,
        frames: list[int],
        counter: list[Any],
        message: str,
        memo: dict[str, bool | None] | None = None,
    ) -> None:
        """Measure ``stage`` for ``frames``: closed form when the method gives one, else analyze.

        ``memo`` carries whether the closed form answers from one call to the next (a streamed
        job measures a stage in several calls; one call over every frame is the same).
        """
        earlier_stages = self._stages[: self._stages.index(stage)]
        use_closed_form = None if memo is None else memo.get(stage.name)
        for pts in frames:
            self._check(progress, pending.generation)
            earlier = {
                e.name: self._store.smoothed(pts, e.name, schema_hash=pending.schema)
                for e in earlier_stages
            }
            record: Statistics | None = None
            if use_closed_form is not False:
                try:
                    measured = self._measured.raw(pts, stage.name)
                except KeyError:
                    measured = None
                if measured is not None:
                    record = self._method.closed_form(stage.name, pending.params, earlier, measured)
                    if use_closed_form is None:
                        use_closed_form = record is not None
                        if memo is not None:
                            memo[stage.name] = use_closed_form
            if record is None:
                stored = self._cache.proxy(self._key, pts)
                record = self._method.analyze(
                    stage.name, self._image(stored), pending.params, earlier
                )
                self._measured.put(pts, stage.name, record)
            self._store.put(pts, stage.name, record, schema_hash=pending.schema)
            counter[0] += 1
            self._report(progress, counter[0], counter[1], message)

    # --- streamed job (WP3.21) ----------------------------------------------------------------

    def _stream_stored(
        self, progress: Progress, pending: _Pending, counter: list[Any], axis: tuple[int, ...]
    ) -> None:
        """Measure the first stage frame by frame over a complete cache entry, advancing.

        Args:
            progress: The job's progress.
            pending: The job's parameters.
            counter: The job's unit counter.
            axis: The whole clip's axis.
        """
        first = self._stages[0]
        assert self._stream is not None
        message = f"stage {first.name} (1 of {len(self._stages)})"
        for count, pts in enumerate(axis, start=1):
            self._measure(progress, pending, first, [pts], counter, message, self._stream.closed)
            self._advance(progress, pending, counter, count, whole=True)

    def _advance(
        self, progress: Progress, pending: _Pending, counter: list[Any], raw: int, *, whole: bool
    ) -> None:
        """Bring every stage as far as its records are final and publish the final frames.

        Runs on the analysis thread once :data:`STREAM_STEP` (and 1/:data:`STREAM_SHARE` of the
        axis) more first-stage records are in. Stage by stage, the outputs whose reach ends on a
        record that is in (and, on a decoded prefix, not on its last frame) are final: they are
        smoothed, and the next stage is measured on them (it reads every earlier stage's
        smoothed record). A step-aware kind reads the whole series, so it publishes only at the
        end.

        Args:
            progress: The job's progress (the cancel check).
            pending: The job's parameters.
            counter: The job's unit counter.
            raw: First-stage raw records in, from the axis's start.
            whole: True when the axis is the whole clip (a complete cache entry).
        """
        stream = self._stream
        assert stream is not None
        if self._kind not in LOCAL_KINDS or raw - stream.advanced < max(
            STREAM_STEP, raw // STREAM_SHARE
        ):
            return
        stream.advanced = raw
        stream.raw[0] = raw
        axis = self._store.axis()
        ticks = np.asarray(axis, dtype=np.int64)
        ends: list[int] = []
        usable = _usable_end(raw, len(ticks), whole)
        for index in range(len(self._stages)):
            usable = self._final_end(ticks, stream.smoothed[index], usable)
            ends.append(usable)
        for index, stage in enumerate(self._stages):
            if index > 0 and ends[index - 1] >= stream.raw[index]:
                frames = list(axis[stream.raw[index] : ends[index - 1] + 1])
                message = f"stage {stage.name} ({index + 1} of {len(self._stages)})"
                self._measure(progress, pending, stage, frames, counter, message, stream.closed)
                stream.raw[index] = ends[index - 1] + 1
            if ends[index] >= stream.smoothed[index]:
                self._store.smooth_at(
                    stage.name,
                    stage.smoothed,
                    self._window_s,
                    self._kind,
                    axis[stream.smoothed[index]],
                    axis[ends[index]],
                )
                stream.smoothed[index] = ends[index] + 1
        with stream.cond:
            stream.published = _Published(ticks, raw, whole, self._final_count(stream), "running")
            stream.cond.notify_all()

    def _final_end(self, ticks: NDArray[np.int64], lo: int, usable: int) -> int:
        """Return the last output from ``lo`` whose reach ends at or before ``usable``.

        Reach ends do not decrease along the axis, so the search halves. ``lo - 1`` when none.
        """
        best = lo - 1
        low, high = lo, usable
        while low <= high:
            mid = (low + high) // 2
            if reach(ticks, self._time_base, self._window_s, self._kind, mid, mid)[1] <= usable:
                best, low = mid, mid + 1
            else:
                high = mid - 1
        return best

    def _final_count(self, stream: _Stream) -> int:
        """The frames from the axis's start whose every stage is final: the last stage's count."""
        return stream.smoothed[-1]
