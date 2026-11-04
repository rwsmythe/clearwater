"""The export engine: one job per photo or video, behind the WP3.19 seam (WP3.14; IF-8).

:class:`ExportEngine` implements :class:`~clearwater.jobs.export_seam.ExportJobs`. A job reads one
source, corrects it with the injected IF-3 method and writes one output through
:func:`~clearwater.jobs.naming.plan_output` and :class:`~clearwater.jobs.safe_write.SafeWrite`
with a fresh :class:`~clearwater.jobs.naming.Reservations` (DR-35 (b)). A video's analysis runs
inside the job (AD-7, AD-15), so a batch item needs no prior analysis.

Threads: the job runs on the caller's worker thread, one frame in flight. A video's analysis
runs on its own thread beside the export (WP3.21; AD-7 as read at ruling Q2): it iterates and
closes its own decode stream (DR-45 (a)), is the only caller of the cache's store methods (one
writer per key, DR-62 not widened) and never calls the job's ``report`` (its reports are passed
on by the job's thread until the export starts, Q-R3). The job renders frame i once the engine
has published i's record as final for every stage (``smoothed_record`` waits), so every frame
renders with exactly the whole-clip record; each thread holds one decoded frame at a time. The
analysis thread has ended before the sink's ``close`` and is joined on every path out of the job.
When the analysis thread returns, on every path, it releases the device pool's free blocks once
through the backend's ``release_fft_plans`` (CHARC ruling, WP3.21 task 10): the blocks the
analysis half grew the pool by go back to the device for the rest of the export, and the
render thread's FFT plans are untouched (the plan cache is per thread; the analysis thread
builds none). The job's end releases again on its own thread (Q-C5a).
During a video encode, from after the sink's ``open`` until its ``close`` has returned, one
watchdog thread polls ``progress.cancelled()`` and calls the sink's ``abort`` once, which
releases a write blocked on FFmpeg's input (DR-57 (b)) or a ``close`` still flushing; it touches
nothing else, and it is joined before the post-close cancel check and ``commit``.

Every collaborator is injected (plan 8.1: ``jobs`` reaches correction methods only through IF-3),
so this module imports nothing from ``clearwater.gui``, ``clearwater.methods``,
``clearwater.core`` or ``clearwater.io.photo``.
"""

from __future__ import annotations

import dataclasses
import logging
import math
import os
import threading
import time
from collections.abc import Callable, Iterator, Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Protocol, runtime_checkable

import numpy as np

import clearwater
from clearwater.analysis import CANCELLED as ANALYSIS_CANCELLED
from clearwater.analysis import AnalysisEngine, block_mean, proxy_factor
from clearwater.analysis.engine import AnalysisStoppedError
from clearwater.interfaces import (
    ArrayBackend,
    CacheEntry,
    CacheKey,
    CorrectionMethod,
    Frame,
    Image,
    JobResult,
    ParameterSet,
    PhotoSink,
    PhotoSource,
    ProbeResult,
    Progress,
    ProxyCache,
    Settings,
    SinkReport,
    VideoSink,
    VideoSource,
)
from clearwater.io.video import (
    VideoDecodeError,
    VideoEncodeError,
    VideoProbeError,
    is_sidecar,
    resolve_encoder,
    sidecar_fault,
)
from clearwater.io.video.encode import POLL_S
from clearwater.io.video.inputs import ascii_text
from clearwater.io.video.verify import read_packet_table, readable_video_pts

from .disk_space import check_free_space, estimate_photo_bytes, estimate_video_bytes
from .export_seam import CANCELLED, ExportRequest
from .naming import MediaKind, OutputPlan, Reservations, plan_output, validate_suffix
from .provenance import photo_source_summary, provenance_object, video_source_summary
from .safe_write import SafeWrite, SafeWriteError, is_disk_full

_LOG = logging.getLogger(__name__)

RESERVED_DEVICE_NAMES = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{i}" for i in range(1, 10)}
    | {f"LPT{i}" for i in range(1, 10)}
)
"""Windows device names no output may take (DR-35 (a); a portable rule applied on every OS)."""

WATCHDOG_JOIN_S = 60.0
"""How long the job waits for the cancel watchdog to end after it is told to stop."""

ANALYSIS_JOIN_S = 60.0
"""How long the job waits for its analysis thread to end after it is told to stop (the thread
looks at its cancel once per frame)."""

BackendSelector = Callable[[Settings, int, int, str], tuple[ArrayBackend, str]]
"""IF-2 ``select_backend``: settings, height, width, method id -> backend and reason."""

_READABLE_ERRORS = (VideoProbeError, VideoDecodeError, VideoEncodeError, SafeWriteError)
"""Errors whose message is already written for the user (shown without the type name)."""


def is_reserved_device_name(name: str) -> bool:
    """Tell whether a file name is a Windows device name (``NUL.MP4``, ``con.png``, ``COM1 .x``).

    The part before the first dot, with trailing spaces and dots stripped, is compared without
    regard to case. Windows 11 build 26300 creates ``NUL.MP4`` as an ordinary file, but older
    Windows versions and copies onto other volumes do not, so every OS refuses the name.

    Args:
        name: A file name (no folder).

    Returns:
        True when the name is reserved.
    """
    return name.split(".", 1)[0].rstrip(" .").upper() in RESERVED_DEVICE_NAMES


def effective_parameters(method: CorrectionMethod, parameters: ParameterSet) -> dict[str, Any]:
    """Return the method defaults overlaid with the set's values (IF-9 sets may be partial).

    The same rule as the preview's (``clearwater.gui.imaging.effective_parameters``), so an
    export renders with the values the preview showed.

    Args:
        method: The method whose schema applies.
        parameters: The parameter set.

    Returns:
        Parameter name -> value.
    """
    values: dict[str, Any] = {p.name: p.default for p in method.parameters}
    values.update(parameters.parameters)
    return values


@runtime_checkable
class JobDeviceBackend(Protocol):
    """The IF-2 device extension ``clearwater.jobs`` calls (AD-29, WP3.21 Q-C5a), by structure.

    The GPU backend provides it and the CPU backend does not; a job whose backend lacks it has
    nothing to release. A video job calls it twice: once on the analysis thread when that
    thread returns, once on the job's thread at the job's end.
    """

    def release_fft_plans(self) -> None:
        """Free the calling thread's FFT plans and the device pool's free blocks."""
        ...


def _release_fft_plans(backend: object) -> None:
    """Release a job backend's FFT plans and free pool blocks (Q-C5a); never raises.

    Called at the job's end and when a video's analysis thread returns. A failure to release is
    logged and never replaces the job's own outcome.
    """
    if not isinstance(backend, JobDeviceBackend):
        return
    try:
        backend.release_fft_plans()
    except Exception as exc:  # for example a CUDA error at teardown
        _LOG.warning("releasing the FFT plans failed: %s: %s", type(exc).__name__, exc)


class _CancelledError(Exception):
    """The job stopped because ``progress.cancelled()`` was True."""


class _FailureError(Exception):
    """A readable failure; the message is the ``JobResult.failure`` text."""


@dataclass
class _Run:
    """The state of one running job, read when its result is built."""

    name: str
    device: str = "none"
    warnings: list[str] = field(default_factory=list)
    outputs: list[Path] = field(default_factory=list)
    write: SafeWrite | None = None
    final_name: str | None = None
    backend: object | None = None
    """The job's backend once selected (its FFT plans are released at the job's end)."""


class _Relabel:
    """A :class:`Progress` that prefixes each message (the analysis phase's progress)."""

    def __init__(self, progress: Progress, prefix: str) -> None:
        self._progress = progress
        self._prefix = prefix

    def report(self, done: int, total: int | None, message: str) -> None:
        """Pass the report on with the prefix."""
        self._progress.report(done, total, f"{self._prefix}: {message}")

    def cancelled(self) -> bool:
        """Return the wrapped progress's cancel flag."""
        return self._progress.cancelled()


class _Watchdog:
    """Polls the cancel flag during an encode and calls the sink's ``abort`` once (Q2)."""

    def __init__(self, progress: Progress, sink: VideoSink) -> None:
        self._progress = progress
        self._sink = sink
        self._stop = threading.Event()
        self.fired = False
        self._thread = threading.Thread(target=self._watch, name="export-cancel", daemon=True)

    def start(self) -> None:
        """Start polling."""
        self._thread.start()

    def stop(self) -> None:
        """Stop polling and wait for the thread (it never runs past this call's return)."""
        self._stop.set()
        self._thread.join(WATCHDOG_JOIN_S)
        if self._thread.is_alive():  # pragma: no cover - abort is bounded by the sink
            _LOG.warning("the export cancel watchdog did not end within %s s", WATCHDOG_JOIN_S)

    def _watch(self) -> None:
        while True:
            try:
                cancelled = self._progress.cancelled()
            except Exception:  # a broken progress object must not kill the watchdog silently
                _LOG.exception("progress.cancelled() raised in the export watchdog")
                cancelled = False
            if cancelled:
                self.fired = True
                self._sink.abort()
                return
            if self._stop.wait(POLL_S):
                return


class _Fold:
    """The analysis thread's :class:`Progress` (WP3.21, Q-R3).

    ``report`` never reaches the job's progress from the analysis thread: until the export
    starts its reports are kept, in order, for the job's thread to pass on; after that they are
    dropped (the job reports its frames). ``cancelled`` reads the job's flag, as the cancel
    watchdog does from its thread.
    """

    def __init__(self, progress: Progress) -> None:
        self._progress = progress
        self._cond = threading.Condition()
        self._kept: list[tuple[int, int | None, str]] = []
        self._keeping = True
        self._ended = False

    def report(self, done: int, total: int | None, message: str) -> None:
        """Keep the report for the job's thread (until the export starts)."""
        with self._cond:
            if self._keeping:
                self._kept.append((done, total, message))
                self._cond.notify_all()

    def cancelled(self) -> bool:
        """Return the job's cancel flag."""
        return self._progress.cancelled()

    def end(self) -> None:
        """Mark the analysis thread's job as returned (wakes :meth:`take`)."""
        with self._cond:
            self._ended = True
            self._cond.notify_all()

    def take(self, timeout: float) -> tuple[list[tuple[int, int | None, str]], bool]:
        """Wait up to ``timeout`` for a report or the end; return the kept reports and the end."""
        with self._cond:
            if not self._kept and not self._ended:
                self._cond.wait(timeout)
            kept, self._kept = self._kept, []
            return kept, self._ended

    def stop_keeping(self) -> None:
        """Drop every later report (the export has started)."""
        with self._cond:
            self._keeping = False
            self._kept = []


class _Analysis:
    """A video job's analysis on its own thread beside the export (WP3.21; AD-7 as read at Q2).

    The thread runs the engine's streamed job (``analysis_job(stream=True)``). The job's thread
    waits for the LEAD (the first frame final, or the analysis ended), reads each frame's record
    through the engine's ``smoothed_record`` (which waits until the record is final), and
    :meth:`finish` joins the thread and turns its result into the job's outcome with
    :func:`_check_analysis`, as the serial analysis did. When the thread returns (on every path)
    it releases the backend's free pool blocks once, the analysis-end boundary.

    Attributes:
        engine: The clip's analysis engine.
    """

    def __init__(
        self,
        engine: AnalysisEngine,
        backend: ArrayBackend,
        progress: Progress,
        name: str,
        cache: ProxyCache,
        key: CacheKey,
    ) -> None:
        self.engine = engine
        self._backend = backend
        self._progress = progress
        self._name = name
        self._cache = cache
        self._key = key
        self._before: CacheEntry | None = None
        self._fold = _Fold(progress)
        self._result: JobResult | None = None
        self._job: Callable[[Progress], JobResult] | None = None
        self._thread = threading.Thread(target=self._run, name="export-analysis", daemon=True)

    def start(self) -> None:
        """Size the clip's cache entry, then start the analysis thread."""
        self._before = self._cache.lookup(self._key)
        self._job = self.engine.analysis_job(stream=True)
        self._thread.start()

    def cache_growth_bytes(self, frames: int) -> int:
        """Extrapolate the cache entry's growth over the lead to the frames still to store.

        The D87 re-check runs after the lead (CHARC ruling Q-R6), while the analysis goes on
        storing proxies on a volume the output may share. The entry's growth since :meth:`start`,
        per frame stored in that time (the marginal rate), and the entry's own bytes per stored
        frame are each scaled to the frames the entry does not hold yet, and the larger is taken
        (DR-71): on a retry whose lead extends an incomplete entry by a few frames the marginal
        rate rests on those few. When the lead stored nothing new (a retry over an incomplete
        entry that already holds the lead's frames: a byte-identical proxy adds nothing), only
        the entry's own rate is defined (Reviewer A round 1, F5).

        Args:
            frames: The clip's frame count.

        Returns:
            The estimated bytes the entry still grows by; 0 for a complete or empty entry, or when
            the entry already holds every frame.
        """
        after = self._cache.lookup(self._key)
        if after is None or after.complete:
            return 0
        remaining = frames - len(after.pts_ticks)
        if remaining <= 0:
            return 0
        before = self._before
        grown = after.size_bytes - (0 if before is None else before.size_bytes)
        stored = len(after.pts_ticks) - (0 if before is None else len(before.pts_ticks))
        marginal = -(-grown * remaining // stored) if grown > 0 and stored > 0 else 0
        held = len(after.pts_ticks)
        own = -(-after.size_bytes * remaining // held) if held > 0 and after.size_bytes > 0 else 0
        return max(marginal, own)

    def _run(self) -> None:
        try:
            assert self._job is not None
            self._result = self._job(self._fold)
        finally:
            # The analysis-end boundary: free the pool blocks the analysis half grew it by, once.
            _release_fft_plans(self._backend)
            self._fold.end()

    def lead(self) -> None:
        """Pass the analysis's reports on until its first frame is final or it has ended.

        An analysis that ends within its lead (a clip shorter than the lead) is checked here,
        before anything is written, exactly as the serial analysis was.

        Raises:
            _CancelledError: The analysis stopped and the cancel was asked.
            _FailureError: The analysis failed or did not complete.
        """
        relabel = _Relabel(self._progress, f"Analysing {self._name}")
        try:
            while True:
                kept, ended = self._fold.take(POLL_S)
                for done, total, message in kept:
                    relabel.report(done, total, message)
                if ended:
                    self.finish()
                    return
                if self._progress.cancelled():
                    self.engine.cancel()  # the thread also sees the flag at its next frame
                elif self.engine.streamed()[0] >= 1:
                    return
        except BaseException:
            self.stop()
            raise
        finally:
            self._fold.stop_keeping()

    def finish(self) -> None:
        """Wait for the analysis thread and raise unless the analysis completed.

        Raises:
            _CancelledError: The analysis stopped and the cancel was asked.
            _FailureError: The analysis failed or did not complete.
        """
        while self._thread.is_alive():
            if self._progress.cancelled():
                self.engine.cancel()
            self._thread.join(POLL_S)
        result = self._result or JobResult(
            False, (), (), "the analysis thread ended without a result", "none", 0.0
        )
        _check_analysis(result, self._progress, self._name)
        if not self.engine.is_complete():
            raise _FailureError(f"{self._name}: analysis did not complete")

    def stop(self) -> None:
        """Stop the analysis if it still runs and join its thread (never raises)."""
        if not self._thread.is_alive():
            return
        self.engine.cancel()
        self._thread.join(ANALYSIS_JOIN_S)
        if self._thread.is_alive():  # pragma: no cover - the thread checks its cancel per frame
            _LOG.warning("the export's analysis thread did not end within %s s", ANALYSIS_JOIN_S)


def expected_frames(probe: ProbeResult) -> int | None:
    """Return the frames a whole decode of the probed clip yields, when it is known (DR-45 (b)).

    The probe's count for a clip with no D86 fault; for a ``truncated`` clip the readable count,
    from one packet listing (``readable_video_pts``, the set the sink's check also uses); None
    for an ``unreadable_tail`` clip (its decodable end is known only by decoding; CHARC
    ``91c2c22f4b6edd18``) or an unknown count. With None, a decode of an ``unreadable_tail`` clip
    that ends early is marked complete at the decoder's end, as D86 intends, and no packet listing
    is made; the export half is still held by the sink's ``missing_frames`` rule (every readable
    frame up to the last one written, none skipped). Public (WP4.3, ruling Q18) so the GUI's
    analysis passes the same count as the export's: one copy of the rule.

    Args:
        probe: The clip's probe result.

    Returns:
        The frame count, or None when it is not known before decoding.
    """
    kinds = {fault.kind for fault in probe.faults}
    if "unreadable_tail" in kinds:
        return None
    if "truncated" in kinds:
        return len(readable_video_pts(probe, read_packet_table(probe.path)))
    return probe.video.nb_frames


def _expected_frames(probe: ProbeResult) -> int | None:
    """Return :func:`expected_frames` of ``probe`` (the export's own name for the one rule)."""
    return expected_frames(probe)


def _close_stream(frames: Iterator[Frame], *, quietly: bool) -> None:
    """Close a decode stream on the job's thread (DR-45 (a)).

    Args:
        frames: The stream; one without ``close`` is left alone.
        quietly: True while another error is being handled: a close error is then a log line,
            never the failure (task 5); False lets it raise as the job's own failure.
    """
    close = getattr(frames, "close", None)
    if close is None:
        return
    try:
        close()
    except Exception as exc:
        if not quietly:
            raise
        _LOG.warning(
            "closing the decode stream failed after an earlier error: %s: %s",
            type(exc).__name__,
            ascii_text(str(exc)),
        )


def _check_analysis(result: JobResult, progress: Progress, name: str) -> None:
    """Raise for a non-ok analysis result: a cancel when one was asked, else its failure.

    A cancel is read from ``progress.cancelled()``, never from the result's text (Q2 as amended):
    a cleanup error during the stop (the decode stream's ``close``) can replace the analysis's
    own outcome, so that text goes to the log, not the result.

    Raises:
        _CancelledError: The analysis stopped and the cancel was asked.
        _FailureError: The analysis failed with no cancel asked.
    """
    if result.ok:
        return
    if progress.cancelled() or result.failure == ANALYSIS_CANCELLED:
        if result.failure != ANALYSIS_CANCELLED:
            _LOG.info(
                "export %s: cancelled; the stopped analysis reported %s",
                name,
                ascii_text(str(result.failure)),
            )
        raise _CancelledError
    raise _FailureError(f"{name}: analysis failed: {ascii_text(str(result.failure))}")


def _after_commit(name: str, call: Callable[[], None]) -> None:
    """Run one callback after ``commit``; its error is a WARNING, never the job's failure.

    The output is committed by then, so the result stays ok with it (Reviewer B B3).
    """
    try:
        call()
    except Exception as exc:
        _LOG.warning(
            "export %s: a callback after the commit raised %s: %s; the output is kept",
            name,
            type(exc).__name__,
            ascii_text(str(exc)),
        )


def _caused_by_disk_full(exc: BaseException) -> bool:
    """Tell whether ``exc`` or anything in its cause or context chain is a disk full (D87)."""
    seen: set[int] = set()
    current: BaseException | None = exc
    while current is not None and id(current) not in seen:
        if is_disk_full(current):
            return True
        seen.add(id(current))
        current = current.__cause__ or current.__context__
    return False


class ExportEngine:
    """The export engine (IF-8 jobs behind the WP3.19 ``ExportJobs`` seam).

    Each call of :meth:`job` builds one job for one source. Jobs share nothing but the injected
    collaborators; one export activity runs at a time (the GUI's gate, or :func:`run_batch`).
    """

    def __init__(
        self,
        *,
        methods: Mapping[str, CorrectionMethod],
        video_source: VideoSource,
        sink_factory: Callable[[], VideoSink],
        photo_reader: PhotoSource,
        photo_writer: PhotoSink,
        cache: ProxyCache,
        cache_key: Callable[[Path], CacheKey],
        select_backend: BackendSelector,
        app_version: str = clearwater.__version__,
        on_stage: Callable[[str], None] | None = None,
        source_for: Callable[[ArrayBackend | None], VideoSource] | None = None,
        sink_for: Callable[[ArrayBackend | None], VideoSink] | None = None,
    ) -> None:
        """Store the collaborators; nothing runs until a job runs.

        Args:
            methods: The correction methods by id (IF-3).
            video_source: The video source (IF-5) every video job probes with; without
                ``source_for`` it also decodes the job's frames and is given to its analysis.
            sink_factory: Returns a fresh, unopened video sink (IF-5) for each video job; not
                called when ``sink_for`` is given.
            photo_reader: The photo source (IF-6).
            photo_writer: The photo sink (IF-6).
            cache: The proxy cache each video job's analysis engine uses (IF-7).
            cache_key: The cache key of a source file.
            select_backend: The backend selector (IF-2; D111, AD-9).
            app_version: The version recorded in provenance.
            on_stage: Called with a phase name at each phase boundary (the V16 instrument's
                hook: ``"probe"``, ``"analysis"``, ``"open"``, ``"frames"``, ``"close"`` for a
                video; ``"read"``, ``"measure"``, ``"render"``, ``"write"`` for a photo; then
                ``"committed"``). None in the product; the engine reads no clock of its own.
            source_for: Returns the frame source of one video job, called once per video job
                right after its one ``select_backend`` call with the selected backend for a GPU
                job and None for a CPU job (DR-67); that source decodes the job's analysis and
                its render. None: ``video_source`` decodes.
            sink_for: Returns the fresh, unopened sink of one video job, called once per video
                job with the same argument as ``source_for`` (DR-67). None: ``sink_factory``.
        """
        self._methods = dict(methods)
        self._video_source = video_source
        self._sink_factory = sink_factory
        self._photo_reader = photo_reader
        self._photo_writer = photo_writer
        self._cache = cache
        self._cache_key = cache_key
        self._select_backend = select_backend
        self._app_version = app_version
        self._on_stage = on_stage
        self._source_for = source_for
        self._sink_for = sink_for

    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]:
        """Return the IF-8 job that exports ``request`` (the ``ExportJobs`` contract).

        Touches no file: a missing or unreadable source is the job's failure.

        Args:
            request: What to export.

        Returns:
            The job.

        Raises:
            ValueError: The request is malformed in itself (a kind other than ``"photo"`` or
                ``"video"``, or a field of the wrong type).
        """
        if not isinstance(request, ExportRequest):
            raise ValueError(f"not an export request: {type(request).__name__}")
        if request.kind not in ("photo", "video"):
            raise ValueError(f"unknown export kind {request.kind!r}")
        if not isinstance(request.source, Path):
            raise ValueError(f"the source must be a Path, got {type(request.source).__name__}")
        if not isinstance(request.parameters, ParameterSet):
            raise ValueError("the parameters must be a ParameterSet")
        if not isinstance(request.settings, Settings):
            raise ValueError("the settings must be a Settings")

        def run(progress: Progress) -> JobResult:
            return self._run(request, progress)

        return run

    # --- the job ------------------------------------------------------------------------------

    def _run(self, request: ExportRequest, progress: Progress) -> JobResult:
        """Run one job and turn its outcome into a :class:`JobResult`."""
        start = time.perf_counter()
        run = _Run(name=ascii_text(request.source.name) or ascii_text(str(request.source)))
        failure: str | None = None
        try:
            self._check_cancel(progress)
            method = self._prepare(request, run)
            if request.kind == "photo":
                self._photo(request, method, progress, run)
            else:
                self._video(request, method, progress, run)
        except _CancelledError:
            failure = CANCELLED
        except _FailureError as exc:
            failure = str(exc)
        except Exception as exc:  # every other error is a failed result with its own text
            failure = self._describe(run, exc)
        finally:  # once per job on every path, never per frame (Q-C5a)
            _release_fft_plans(run.backend)
        if run.write is not None and run.write.temp_leftover:  # also after an ok commit (D85)
            run.warnings.append(
                f"The temporary file {ascii_text(run.write.temp_path.name)} could not be removed; "
                "it is removed at the next start."
            )
        result = JobResult(
            ok=failure is None,
            outputs=tuple(run.outputs),
            warnings=tuple(run.warnings),
            failure=failure,
            device=run.device,
            elapsed_s=time.perf_counter() - start,
        )
        outcome = "ok" if failure is None else ("cancelled" if failure is CANCELLED else "failed")
        _LOG.info(
            "export %s: %s; device %s%s",
            run.name,
            outcome,
            run.device,
            "" if failure is None or failure is CANCELLED else f"; {failure}",
        )
        return result

    def _describe(self, run: _Run, exc: Exception) -> str:
        """Return the readable failure text of an unexpected error (its ORIGINAL text)."""
        text = str(exc) if isinstance(exc, _READABLE_ERRORS) else f"{type(exc).__name__}: {exc}"
        text = ascii_text(text)
        if _caused_by_disk_full(exc):
            target = run.final_name or run.name
            return f"{run.name}: disk full while writing {ascii_text(target)}: {text}"
        return f"{run.name}: {text}"

    def _stage(self, name: str) -> None:
        """Call the phase hook, when one is injected."""
        if self._on_stage is not None:
            self._on_stage(name)

    @staticmethod
    def _check_cancel(progress: Progress) -> None:
        """Stop with :class:`_CancelledError` once the cancel was asked."""
        if progress.cancelled():
            raise _CancelledError

    def _prepare(self, request: ExportRequest, run: _Run) -> CorrectionMethod:
        """Check the settings, the method and the sidecar rule (job start; DR-35 (b), D83)."""
        settings = request.settings
        folder = settings.output_folder
        if folder is not None and not folder.is_dir():
            raise _FailureError(
                f"{run.name}: the output folder does not exist: {ascii_text(str(folder))}"
            )
        try:
            validate_suffix(settings.output_suffix)
        except ValueError as exc:
            raise _FailureError(f"{run.name}: {ascii_text(str(exc))}") from exc
        method = self._methods.get(request.parameters.method)
        if method is None:
            raise _FailureError(
                f"{run.name}: unknown correction method {ascii_text(request.parameters.method)!r}"
            )
        if is_sidecar(request.source):
            raise _FailureError(f"{run.name}: {sidecar_fault(request.source).message}")
        return method

    def _plan(
        self, request: ExportRequest, kind: MediaKind, reservations: Reservations, run: _Run
    ) -> OutputPlan:
        """Plan the final name and refuse a Windows device name (DR-35 (a))."""
        plan = plan_output(request.source, request.settings, kind, reservations)
        run.final_name = plan.path.name
        if is_reserved_device_name(plan.path.name):
            reservations.release(plan.path)
            raise _FailureError(
                f"{run.name}: the output name {ascii_text(plan.path.name)} is a reserved device "
                "name on Windows; change the output suffix."
            )
        return plan

    @staticmethod
    def _check_space(run: _Run, folder: Path, needed: int) -> None:
        """Refuse the item when its estimate does not fit (D87; per item, never batch-wide)."""
        check = check_free_space(folder, needed)
        if not check.ok:
            raise _FailureError(f"{run.name}: {check.message()}")

    @staticmethod
    def _job_device(backend: ArrayBackend) -> ArrayBackend | None:
        """Return the backend a video job's source and sink are built with (DR-67).

        The job's own GPU backend (identity, never a second selection), or None for a CPU job.
        """
        return None if backend.device == "cpu" else backend

    def _note_device(self, run: _Run, reason: str) -> None:
        """Record the backend reason and the AD-9 fallback warning."""
        run.device = reason
        if reason.startswith("CPU") and reason != "CPU: forced":
            run.warnings.append(f"Processed on the CPU ({reason}).")

    # --- photo (8.1, IF-6) --------------------------------------------------------------------

    def _photo(
        self, request: ExportRequest, method: CorrectionMethod, progress: Progress, run: _Run
    ) -> None:
        """Read, measure, render and write one photo."""
        settings = request.settings
        progress.report(0, 4, f"Reading {run.name}")
        self._stage("read")
        image, meta = self._photo_reader.read(request.source)
        stat = os.stat(request.source)
        pixels = np.asarray(image.pixels, dtype=np.float32)
        height, width = pixels.shape[0], pixels.shape[1]
        self._check_cancel(progress)
        backend, reason = self._select_backend(settings, height, width, method.id)
        run.backend = backend
        self._note_device(run, reason)
        params = effective_parameters(method, request.parameters)

        progress.report(1, 4, f"Measuring {run.name}")
        self._stage("measure")
        proxy_pixels = block_mean(pixels, proxy_factor(height, width)).astype(np.float32)
        proxy = Image(
            pixels=backend.asarray(proxy_pixels, np.float32),
            device=backend.device,
            color=image.color,
            orientation_applied=True,
        )
        statistics: dict[str, Any] = {}
        for stage in method.stages:
            self._check_cancel(progress)
            statistics[stage.name] = method.analyze(stage.name, proxy, params, dict(statistics))

        progress.report(2, 4, f"Rendering {run.name}")
        self._stage("render")
        self._check_cancel(progress)
        on_device = Image(
            pixels=backend.asarray(pixels, np.float32),
            device=backend.device,
            color=image.color,
            orientation_applied=True,
        )
        rendered = method.render(on_device, params, statistics)
        host = dataclasses.replace(
            rendered,
            pixels=np.asarray(backend.to_host(rendered.pixels), dtype=np.float32),
            device="cpu",
        )
        self._check_cancel(progress)

        reservations = Reservations()
        plan = self._plan(request, MediaKind.PHOTO, reservations, run)
        self._check_space(
            run, plan.folder, estimate_photo_bytes(width, height, settings.png_bit_depth)
        )
        provenance = (
            provenance_object(
                method=method.id,
                parameters=params,
                app_version=self._app_version,
                source=photo_source_summary(request.source, stat, width, height),
                settings={"png_bit_depth": settings.png_bit_depth, "device": reason},
            )
            if settings.provenance
            else None
        )
        progress.report(3, 4, f"Writing {run.name}")
        self._stage("write")
        self._check_cancel(progress)  # a cancel asked on the "Writing" report never writes
        run.write = SafeWrite(plan, reservations)  # held first: a failed begin may leave one
        try:
            with run.write as write:
                self._photo_writer.write(
                    host,
                    meta,
                    write.temp_path,
                    bit_depth=settings.png_bit_depth,
                    provenance=provenance,
                )
                self._check_cancel(progress)
                final = write.commit()
        except _CancelledError:
            raise
        except Exception as exc:
            if progress.cancelled():  # read from the flag, never the error's text (Q2 as amended)
                _LOG.info(
                    "export %s: cancelled; the stopped write reported %s: %s",
                    run.name,
                    type(exc).__name__,
                    ascii_text(str(exc)),
                )
                raise _CancelledError from exc
            raise
        run.outputs.append(final)
        _after_commit(run.name, lambda: self._stage("committed"))
        _after_commit(run.name, lambda: progress.report(4, 4, f"Saved {ascii_text(final.name)}"))

    # --- video (8.2; data flow "video export (jobs)") ----------------------------------------

    def _video(
        self, request: ExportRequest, method: CorrectionMethod, progress: Progress, run: _Run
    ) -> None:
        """Probe, analyse, render and encode one video."""
        settings = request.settings
        progress.report(0, None, f"Preparing {run.name}")
        self._stage("probe")
        probe = self._video_source.probe(request.source)
        for fault in probe.faults:
            if fault.severity == "refuse":
                raise _FailureError(f"{run.name}: {ascii_text(fault.message)}")
        for fault in probe.faults:
            if fault.kind == "gp_log" and fault.severity == "warn":
                run.warnings.append(ascii_text(fault.message))
        self._check_cancel(progress)
        video = probe.video
        backend, reason = self._select_backend(settings, video.height, video.width, method.id)
        run.backend = backend
        self._note_device(run, reason)

        device = self._job_device(backend)
        source = self._video_source if self._source_for is None else self._source_for(device)
        sink = self._sink_factory() if self._sink_for is None else self._sink_for(device)
        capabilities = sink.capabilities()
        encoder = resolve_encoder(settings.video_encoder, capabilities)
        bit_depth = 10 if video.bit_depth == 10 or settings.ten_bit_for_eight_bit else 8
        capability = next((c for c in capabilities if c.name == encoder), None)
        if capability is None or not capability.available:
            if capability is None:  # a saved known encoder outside this platform's roster (D26)
                why = ": not offered on this platform"
            else:
                why = "" if capability.reason is None else f": {capability.reason}"
            raise _FailureError(f"{run.name}: the encoder {encoder} is not available here{why}")
        if bit_depth not in capability.bit_depths:
            raise _FailureError(
                f"{run.name}: the encoder {encoder} cannot write {bit_depth}-bit video"
            )

        reservations = Reservations()
        plan = self._plan(request, MediaKind.VIDEO, reservations, run)
        stat = os.stat(request.source)
        needed = estimate_video_bytes(
            stat.st_size,
            settings,
            width=video.width,
            height=video.height,
            frame_rate=video.frame_rate,
            duration_s=probe.duration_s,
        )
        self._check_space(run, plan.folder, needed)
        self._check_cancel(progress)

        params = effective_parameters(method, request.parameters)
        hw_decode = backend.device != "cpu"
        analysis = self._analyse(
            request, method, backend, probe, params, hw_decode, progress, run, source
        )
        try:
            # After the lead: the analysis cache may share the volume, and on a clip longer than
            # the lead it goes on growing during the export, so its extrapolated growth is
            # added to the item's estimate (CHARC ruling Q-R6).
            frames = video.nb_frames
            if frames is None:
                frames = math.ceil(probe.duration_s * video.frame_rate)
            self._check_space(run, plan.folder, needed + analysis.cache_growth_bytes(frames))
            self._check_cancel(progress)

            provenance = (
                provenance_object(
                    method=method.id,
                    parameters=params,
                    app_version=self._app_version,
                    source=video_source_summary(probe, stat),
                    settings={
                        "encoder": encoder,
                        "quality": settings.quality_level,
                        "bit_depth": bit_depth,
                        "device": reason,
                    },
                )
                if settings.provenance
                else None
            )
            run.write = SafeWrite(plan, reservations)  # held first: a failed begin may leave one
            with run.write as write:
                try:
                    self._stage("open")
                    sink.open(
                        probe,
                        write.temp_path,
                        encoder=encoder,
                        quality=settings.quality_level,
                        bit_depth=bit_depth,
                        provenance=provenance,
                    )
                    report = self._encode(
                        probe,
                        method,
                        backend,
                        analysis,
                        params,
                        hw_decode,
                        sink,
                        progress,
                        run,
                        source,
                    )
                except BaseException:
                    sink.abort()  # never close after a stop: kill FFmpeg, delete the temporary
                    raise
                final = write.commit()
        finally:
            analysis.stop()  # joined on every path (on the clean path it ended before close)
        run.outputs.append(final)
        saved = f"Saved {ascii_text(final.name)}"
        _after_commit(run.name, lambda: self._stage("committed"))
        _after_commit(
            run.name, lambda: progress.report(report.frames_written, video.nb_frames, saved)
        )

    def _analyse(
        self,
        request: ExportRequest,
        method: CorrectionMethod,
        backend: ArrayBackend,
        probe: ProbeResult,
        params: Mapping[str, Any],
        hw_decode: bool,
        progress: Progress,
        run: _Run,
        source: VideoSource,
    ) -> _Analysis:
        """Start the clip's analysis on its own thread and wait for its lead (AD-7 as read at Q2).

        Returns:
            The running (or, for a clip within its lead, finished) analysis.
        """
        self._stage("analysis")
        key = self._cache_key(request.source)
        engine = AnalysisEngine(
            method=method,
            backend=backend,
            cache=self._cache,
            key=key,
            source=source,
            probe=probe,
            params=params,
            hw_decode=hw_decode,
            expected_frames=_expected_frames(probe),
        )
        analysis = _Analysis(engine, backend, progress, run.name, self._cache, key)
        analysis.start()
        analysis.lead()
        return analysis

    def _encode(
        self,
        probe: ProbeResult,
        method: CorrectionMethod,
        backend: ArrayBackend,
        analysis: _Analysis,
        params: Mapping[str, Any],
        hw_decode: bool,
        sink: VideoSink,
        progress: Progress,
        run: _Run,
        source: VideoSource,
    ) -> SinkReport:
        """Write every frame and close the sink, under the cancel watchdog (Q2 as amended).

        The watchdog runs from after ``open`` until ``close`` has returned or raised, so a cancel
        during the flush and verification also reaches ``abort``. It is stopped and joined before
        the post-close cancel check, which is unconditional, and before ``commit``: no second
        thread is alive at the rename. A cancel is read from ``progress.cancelled()``, never
        from an error's text; the stopped encoder's error then goes to the log, not the result.

        Returns:
            The sink's report (its warnings and ``not_carried`` items are already the job's).
        """
        watchdog = _Watchdog(progress, sink)
        watchdog.start()
        try:
            try:
                self._write_frames(
                    probe, method, backend, analysis, params, hw_decode, sink, progress, run, source
                )
                self._stage("close")
                self._check_cancel(progress)  # a cancel after the last frame never closes
                report = sink.close()
                # The sink's warnings are the job's from here, so a stop before commit keeps them.
                run.warnings.extend(ascii_text(w) for w in report.warnings)
                run.warnings.extend(
                    f"Not carried to the output: {ascii_text(item)}" for item in report.not_carried
                )
            finally:
                watchdog.stop()
        except _CancelledError:
            raise
        except Exception as exc:
            if watchdog.fired or progress.cancelled():
                _LOG.info(
                    "export %s: cancelled; the stopped encoder reported %s: %s",
                    run.name,
                    type(exc).__name__,
                    ascii_text(str(exc)),
                )
                raise _CancelledError from exc
            raise
        self._check_cancel(progress)  # mandatory, whatever close returned
        return report

    def _write_frames(
        self,
        probe: ProbeResult,
        method: CorrectionMethod,
        backend: ArrayBackend,
        analysis: _Analysis,
        params: Mapping[str, Any],
        hw_decode: bool,
        sink: VideoSink,
        progress: Progress,
        run: _Run,
        source: VideoSource,
    ) -> None:
        """Render and write every decoded frame in pts order; close the stream on this thread.

        Each frame's record is read once it is final (``smoothed_record`` waits for the
        analysis); after the last frame the analysis thread is joined and its outcome checked.
        A host frame is rendered and handed to the sink on the host, as before; a frame the
        source yielded on the device stays there and the sink quantises it on the device.
        """
        engine = analysis.engine
        schema = engine.schema_hash
        total = probe.video.nb_frames
        message = f"Exporting {run.name}"
        self._stage("frames")
        frames: Iterator[Frame] = source.frames(probe, hw_decode=hw_decode)
        try:
            for written, frame in enumerate(frames, start=1):
                self._check_cancel(progress)
                try:
                    statistics = engine.smoothed_record(frame.pts_ticks, schema_hash=schema)
                except AnalysisStoppedError:
                    analysis.finish()  # raises the analysis's own outcome
                    raise
                on_device = dataclasses.replace(
                    frame,
                    pixels=backend.asarray(frame.pixels, np.float32),
                    device=backend.device,
                )
                rendered = method.render(on_device, params, statistics)
                if frame.device == "cpu":
                    out = dataclasses.replace(
                        frame,
                        pixels=np.asarray(backend.to_host(rendered.pixels), dtype=np.float32),
                        device="cpu",
                    )
                else:  # a device-frame source (WP3.21 #2): the sink quantises on the device
                    out = dataclasses.replace(frame, pixels=rendered.pixels, device=rendered.device)
                sink.write(out)
                progress.report(written, total, message)
        except BaseException:
            _close_stream(frames, quietly=True)  # the earlier error stays the failure
            raise
        _close_stream(frames, quietly=False)
        analysis.finish()
