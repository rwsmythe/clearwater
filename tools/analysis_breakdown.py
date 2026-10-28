"""WP3.21 task 1: where a cold export spends its time, step by step (question 6).

The instrument drives the PRODUCT functions in the order the product runs them, with its own
clock around each call; the product carries no timer. It runs three phases on one clip, under
the job's backend and ``hw_decode`` as ``clearwater.jobs.export`` sets them:

1. **The analysis replica**: an :class:`~clearwater.analysis.AnalysisEngine` is built as the
   export job builds it, and its decode pass (``_decode``) and its later stages
   (``_run_stages``: ``_measure`` and ``_smooth_stage``) are replayed through the engine's own
   methods and collaborators, one timed call at a time: per frame the wait for the decoder's next
   frame (decode, the hardware download and the pipe), ``planes_to_rgb``, ``frame_pixels_on_host``,
   ``block_mean`` and ``quantise`` (``make_proxy``'s two steps), ``store_proxy`` (the JPEG encode
   and the write), ``proxy`` (the read back and decode), ``proxy_image`` (the float conversion and
   the upload), stage 1's ``analyze``, the store puts, the progress report and the loop's checks;
   then each later stage's per-frame steps and each stage's smoothing.
2. **The engine itself**: the real ``analysis_job()`` of a second engine on a second, empty cache,
   under the standard library's ``cProfile`` (a cross-check; its overhead is noted and its time is
   not a figure of record). The replica's raw and smoothed records and its stored proxies are then
   compared with the engine's BIT FOR BIT: the replica measures the product, not a copy.
3. **The frame path**: every frame decoded again and rendered with the engine's smoothed record,
   as ``ExportEngine._write_frames`` does, into the product sink (encoder ``auto``, Standard):
   the decode wait, ``planes_to_rgb``, ``smoothed_record``, the upload, ``render``, ``to_host``,
   ``rgb_to_planes`` and the rest of ``write`` (its checks and the pipe write), then ``close``.

``planes_to_rgb`` and ``rgb_to_planes`` run inside the frame source's ``next`` and the sink's
``write``; for the run only, the instrument puts a timing wrapper around the module names those
two calls resolve (``clearwater.io.video.decode.planes_to_rgb``,
``clearwater.io.video.encode.rgb_to_planes``) and puts the originals back afterwards. On the GPU
every timed device call is followed by a device synchronisation, so a step's time is its own.

The CHECK (CHARC ruling Q6): the sum of the per-step MEANS equals the mean per-frame wall of the
same phase within 5 %; medians are reported beside, never summed. A residual above 5 % is a
finding (unattributed time), not a failed instrument. The graphics card is sampled through the
whole run (WP3.10's :class:`~video_io_bench.Telemetry`) and its readings are summarised per
phase, so an idle card is tied to the steps of the phase it idled in.

Plan 4.3: an EXCLUSIVE run, on a full clip. The footage is reached only through
``local_config.find_footage_file`` and only read (FFmpeg maps the first video stream only: no
other track is decoded). Every cache folder, output and record goes under the working folder
(``wp3.21/breakdown``); the run folder is deleted afterwards unless ``--keep`` is given, and a
working folder inside the footage folder is refused. Usage::

    uv run python tools/analysis_breakdown.py GX011627 [--method c3] [--force-cpu]
        [--skip-profile] [--skip-frames] [--keep] [--config FILE]
        [--memory-every S] [--gpu-every S]

Exit status 0 when every phase ran and the replica equals the engine; 1 when a phase failed or
the records differ (the record says which); 2 on a usage, configuration or footage-lookup error.
"""

from __future__ import annotations

import argparse
import contextlib
import cProfile
import dataclasses
import importlib
import io
import json
import os
import pstats
import shutil
import statistics
import sys
import time
from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import UTC, datetime
from pathlib import Path
from types import ModuleType
from typing import Any, TypeVar

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import numpy as np
from numpy.typing import NDArray

import clearwater.io.video.decode as decode_module
import clearwater.io.video.encode as encode_module
from clearwater.analysis import AnalysisEngine
from clearwater.analysis.proxy import block_mean, frame_pixels_on_host, proxy_factor, quantise
from clearwater.cache import DiskProxyCache, cache_key
from clearwater.core import select_backend
from clearwater.interfaces import (
    ArrayBackend,
    CorrectionMethod,
    Frame,
    ParameterSet,
    Settings,
    Statistics,
)
from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource, resolve_encoder
from clearwater.jobs import effective_parameters
from clearwater.methods import available_methods
from local_config import LocalConfigError, find_footage_file, load_local_config
from video_io_bench import Telemetry, period, summarise

SUBDIR = Path("wp3.21") / "breakdown"
"""Where the run folders and the records go, under the working folder."""

RESIDUAL_LIMIT = 0.05
"""The CHECK: the sum of the step means is within this fraction of the mean per-frame wall."""

PROFILE_LINES = 40
"""How many functions of the ``cProfile`` cross-check the record keeps (by own time)."""

_T = TypeVar("_T")


class BreakdownError(RuntimeError):
    """The run cannot start (an output inside the footage folder) or a phase cannot run."""


# --- the clock -------------------------------------------------------------------------------


class Accumulator:
    """Seconds spent in a wrapped call since the last :meth:`take`."""

    def __init__(self) -> None:
        """Start at zero."""
        self.seconds = 0.0
        self.calls = 0

    def take(self) -> float:
        """Return the seconds accumulated since the last call and reset them."""
        seconds, self.seconds = self.seconds, 0.0
        return seconds


@contextlib.contextmanager
def timed_name(module: ModuleType, name: str, accumulator: Accumulator) -> Iterator[None]:
    """Wrap ``module.name`` in a timer for the duration of the block, then restore it.

    Args:
        module: The module whose global the product call resolves.
        name: The global's name.
        accumulator: Receives the seconds of every call.

    Yields:
        Nothing; the wrapper is in place inside the block.
    """
    original = getattr(module, name)

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        began = time.perf_counter()
        try:
            return original(*args, **kwargs)
        finally:
            accumulator.seconds += time.perf_counter() - began
            accumulator.calls += 1

    setattr(module, name, wrapper)
    try:
        yield
    finally:
        setattr(module, name, original)


class StepClock:
    """Per-frame step times of one phase, taken with the instrument's clock.

    Attributes:
        frames: One ``{step: seconds}`` dict per frame, ``"wall"`` included.
        once: Steps timed once per phase (a stage's smoothing, the sink's close).
    """

    def __init__(self, synchronize: Callable[[], None]) -> None:
        """Start a phase.

        Args:
            synchronize: Waits for the device (a no-op on the CPU).
        """
        self._synchronize = synchronize
        self.frames: list[dict[str, float]] = []
        self.once: dict[str, float] = {}
        self._current: dict[str, float] | None = None

    def begin(self) -> None:
        """Start a frame."""
        self._current = {}

    def add(self, step: str, seconds: float) -> None:
        """Add seconds to a step of the current frame."""
        assert self._current is not None, "add outside a frame"
        self._current[step] = self._current.get(step, 0.0) + seconds

    def time(self, step: str, call: Callable[..., _T], *args: Any, device: bool = False) -> _T:
        """Run ``call(*args)`` as one step of the current frame and return its result.

        Args:
            step: The step's name.
            call: The product call.
            *args: Its arguments.
            device: Synchronise with the device after the call (its own device work).

        Returns:
            What ``call`` returned.
        """
        began = time.perf_counter()
        result = call(*args)
        if device:
            self._synchronize()
        self.add(step, time.perf_counter() - began)
        return result

    def end(self, wall: float) -> None:
        """End the current frame with its wall time."""
        assert self._current is not None, "end outside a frame"
        self._current["wall"] = wall
        self.frames.append(self._current)
        self._current = None

    def time_once(self, step: str, call: Callable[..., _T], *args: Any, device: bool = False) -> _T:
        """Run ``call(*args)`` as a once-per-phase step (added to any earlier time of that step)."""
        began = time.perf_counter()
        result = call(*args)
        if device:
            self._synchronize()
        self.once[step] = self.once.get(step, 0.0) + time.perf_counter() - began
        return result


def phase_summary(clock: StepClock, started: float, ended: float) -> dict[str, Any]:
    """Summarise a phase: per-step figures, the sum of the means against the mean wall.

    A step a frame did not run counts zero for that frame, so every step mean is over the
    phase's frames and the means add up to the mean wall less the unattributed time.

    Args:
        clock: The phase's clock.
        started: When the phase began.
        ended: When it ended.

    Returns:
        ``frames``, ``wall_s``, the per-frame ``steps`` (summary and total seconds each, in
        the order first seen), the per-frame ``wall`` summary and the first frame's wall apart
        (``first_wall_s``: it carries the device's first-call set-up), ``sum_of_means_s``,
        ``mean_wall_s``, ``residual`` (the unattributed fraction of the mean wall),
        ``within_limit`` and the ``once`` steps.
    """
    names: list[str] = []
    for frame in clock.frames:
        names.extend(name for name in frame if name != "wall" and name not in names)
    count = len(clock.frames)
    steps: dict[str, Any] = {}
    for name in names:
        values = [frame.get(name, 0.0) for frame in clock.frames]
        steps[name] = {**(summarise(values) or {}), "total_s": sum(values)}
    walls = [frame["wall"] for frame in clock.frames]
    mean_wall = statistics.fmean(walls) if walls else 0.0
    sum_of_means = sum(step["mean"] for step in steps.values())
    residual = (mean_wall - sum_of_means) / mean_wall if mean_wall > 0 else 0.0
    return {
        "frames": count,
        "wall_s": ended - started,
        "steps": steps,
        "wall": summarise(walls),
        "first_wall_s": walls[0] if walls else None,
        "sum_of_means_s": sum_of_means,
        "mean_wall_s": mean_wall,
        "residual": residual,
        "within_limit": abs(residual) <= RESIDUAL_LIMIT,
        "once": dict(clock.once),
    }


def synchronizer(backend: ArrayBackend) -> Callable[[], None]:
    """Return a callable that waits for the backend's device (a no-op on the CPU)."""
    if backend.device == "cpu":
        return lambda: None
    device: Callable[[], None] = importlib.import_module("cupy").cuda.Device().synchronize
    return device


class _Progress:
    """A Progress that never cancels and counts its reports."""

    def __init__(self) -> None:
        self.reports = 0

    def report(self, done: int, total: int | None, message: str) -> None:
        """Count a report."""
        self.reports += 1

    def cancelled(self) -> bool:
        """Never cancel."""
        return False


# --- phase 1: the analysis replica ------------------------------------------------------------


def build_analysis(
    path: Path,
    cache_folder: Path,
    method: CorrectionMethod,
    *,
    force_cpu: bool,
) -> tuple[AnalysisEngine, ArrayBackend, str]:
    """Build the analysis engine as the export job builds it (``ExportEngine._analyse``).

    Args:
        path: The source clip.
        cache_folder: A new cache folder.
        method: The correction method.
        force_cpu: ``Settings.force_cpu``.

    Returns:
        The engine, its backend and the backend selector's reason.
    """
    source = FFmpegVideoSource()
    probe = source.probe(path)
    backend, reason = select_backend(
        Settings(force_cpu=force_cpu), probe.video.height, probe.video.width, method.id
    )
    engine = AnalysisEngine(
        method=method,
        backend=backend,
        cache=DiskProxyCache(cache_folder),
        key=cache_key(path),
        source=source,
        probe=probe,
        params=effective_parameters(method, _defaults(method)),
        hw_decode=backend.device != "cpu",
    )
    return engine, backend, reason


def _defaults(method: CorrectionMethod) -> ParameterSet:
    """The method's defaults as an IF-9 parameter set (AD-8: the defaults are the row's)."""
    return ParameterSet(
        method=method.id, parameters={}, created=datetime.now(UTC), app_version="breakdown"
    )


def _store_first(engine: AnalysisEngine, pts: int, record: Statistics, schema: str) -> None:
    """The decode pass's puts of stage 1's record (and its cache copy when source-only)."""
    first = engine._stages[0]
    engine._measured.put(pts, first.name, record)
    engine._store.put(pts, first.name, record, schema_hash=schema)
    if first.source_only:
        engine._cache.store_source_statistics(engine._key, first.name, pts, record)


def _finish_pass(engine: AnalysisEngine, decoded: Sequence[int]) -> None:
    """The decode pass's end: refuse stale proxies, then ``mark_complete``."""
    entry = engine._cache.lookup(engine._key)
    stale = sorted(set(entry.pts_ticks) - set(decoded)) if entry is not None else []
    if stale:
        raise ValueError(f"the cache entry holds {len(stale)} proxies not decoded by this pass")
    engine._cache.mark_complete(engine._key)


def _next_frame(
    frames: Iterator[Frame], clock: StepClock, planes: Accumulator
) -> tuple[Frame, float] | None:
    """Take the next frame and begin its clock: the decode wait and ``planes_to_rgb`` apart.

    Returns:
        The frame and the time its frame began, or None at the end of the stream.
    """
    began = time.perf_counter()
    planes.take()
    try:
        frame = next(frames)
    except StopIteration:
        return None
    waited = time.perf_counter() - began
    clock.begin()
    converted = planes.take()
    clock.add("decode_wait", waited - converted)
    clock.add("planes_to_rgb", converted)
    return frame, began


def _close(frames: Iterator[Frame]) -> None:
    """Close a decode stream on this thread (DR-45 (a))."""
    close = getattr(frames, "close", None)
    if close is not None:
        close()


def replay_decode_pass(
    engine: AnalysisEngine, clock: StepClock, planes: Accumulator, progress: _Progress
) -> None:
    """Replay ``AnalysisEngine._decode`` step by step through the engine's own collaborators.

    The order and the calls are the decode pass's; each is timed. The end of the pass (the stale
    check and ``mark_complete``) is timed once as ``finish``.

    Args:
        engine: A new engine (no job run).
        clock: The phase's clock.
        planes: The ``planes_to_rgb`` timer (wrapped around the decode module's name).
        progress: The job's progress.

    Raises:
        ValueError: As the decode pass.
    """
    pending = engine._take()
    engine._store.schema_hash = pending.schema
    engine._measured.schema_hash = pending.schema
    first = engine._stages[0]
    total = engine._probe.video.nb_frames
    units = None if total is None else total * len(engine._stages)
    frames: Iterator[Frame] = iter(
        engine._source.frames(engine._probe, hw_decode=engine._hw_decode)
    )
    decoded: list[int] = []
    last: int | None = None
    shape: tuple[int, ...] | None = None
    key, cache = engine._key, engine._cache
    try:
        while (taken := _next_frame(frames, clock, planes)) is not None:
            frame, began = taken
            clock.time("check", engine._check, progress, None)
            pts = int(frame.pts_ticks)
            if last is not None and pts <= last:
                raise ValueError(f"the frame source returned pts {pts} after pts {last}")
            pixels = clock.time(
                "frame_pixels_on_host", frame_pixels_on_host, frame, engine._backend
            )
            if shape is not None and pixels.shape != shape:
                raise ValueError(f"the frame at pts {pts} changed size")
            shape = pixels.shape
            k = proxy_factor(pixels.shape[0], pixels.shape[1])
            mean = clock.time("block_mean", block_mean, pixels, k)
            proxy = clock.time("quantise", quantise, mean)
            clock.time("store_proxy", cache.store_proxy, key, pts, proxy)
            stored = clock.time("proxy", cache.proxy, key, pts)
            image = clock.time("proxy_image", engine._image, stored, device=True)
            record = clock.time(
                "analyze", engine._method.analyze, first.name, image, pending.params, {},
                device=True,
            )  # fmt: skip
            clock.time("store_puts", _store_first, engine, pts, record, pending.schema)
            decoded.append(pts)
            last = pts
            clock.time("report", engine._report, progress, len(decoded), units, "decoding")
            clock.end(time.perf_counter() - began)
    finally:
        _close(frames)
    if not decoded:
        raise ValueError("the frame source yielded no frames")
    clock.time_once("finish", _finish_pass, engine, decoded)
    engine._decoded = True


def replay_later_stages(
    engine: AnalysisEngine, make_clock: Callable[[], StepClock], progress: _Progress
) -> dict[str, tuple[StepClock, float, float]]:
    """Replay ``AnalysisEngine._run_stages`` (no displayed frame): measure, then smooth.

    Each stage not yet smoothed gets a clock: its per-frame steps are ``_measure``'s calls (a
    stage measured in the decode pass has none) and its smoothing (``_smooth_stage``) is the
    clock's ``smooth`` once-step.

    Args:
        engine: The engine after :func:`replay_decode_pass`.
        make_clock: Makes a stage's clock.
        progress: The job's progress.

    Returns:
        Stage name -> (clock, start, end), in stage order.
    """
    pending = engine._take()
    clocks: dict[str, tuple[StepClock, float, float]] = {}
    todo = [
        index
        for index, stage in enumerate(engine._stages)
        if not engine._store.smoothed_complete(stage.name)
    ]
    done = 0
    for index in todo:
        stage = engine._stages[index]
        clock = make_clock()
        stage_began = time.perf_counter()
        earlier_stages = engine._stages[:index]
        use_closed_form: bool | None = None
        for pts in engine._store.raw_missing(stage.name):
            began = time.perf_counter()
            clock.begin()
            clock.time("check", engine._check, progress, pending.generation)
            earlier = clock.time("earlier", _earlier, engine, earlier_stages, pts, pending.schema)
            record: Statistics | None = None
            if use_closed_form is not False:
                try:
                    measured = engine._measured.raw(pts, stage.name)
                except KeyError:
                    measured = None
                if measured is not None:
                    record = clock.time(
                        "closed_form", engine._method.closed_form,
                        stage.name, pending.params, earlier, measured,
                    )  # fmt: skip
                    if use_closed_form is None:
                        use_closed_form = record is not None
            if record is None:
                stored = clock.time("proxy", engine._cache.proxy, engine._key, pts)
                image = clock.time("proxy_image", engine._image, stored, device=True)
                record = clock.time(
                    "analyze", engine._method.analyze, stage.name, image, pending.params, earlier,
                    device=True,
                )  # fmt: skip
                clock.time("measured_put", engine._measured.put, pts, stage.name, record)
            clock.time("store_put", _put, engine, pts, stage.name, record, pending.schema)
            done += 1
            clock.time("report", engine._report, progress, done, None, stage.name)
            clock.end(time.perf_counter() - began)
        clock.time_once("smooth", engine._smooth_stage, progress, pending.generation, stage)
        clocks[stage.name] = (clock, stage_began, time.perf_counter())
    return clocks


def _earlier(
    engine: AnalysisEngine, stages: Sequence[Any], pts: int, schema: str
) -> dict[str, Statistics]:
    """``_measure``'s read of the earlier stages' smoothed records for one frame."""
    return {e.name: engine._store.smoothed(pts, e.name, schema_hash=schema) for e in stages}


def _put(engine: AnalysisEngine, pts: int, stage: str, record: Statistics, schema: str) -> None:
    """``_measure``'s store put."""
    engine._store.put(pts, stage, record, schema_hash=schema)


# --- phase 2: the engine under cProfile -------------------------------------------------------


def profile_engine(engine: AnalysisEngine, stem: Path) -> dict[str, Any]:
    """Run the engine's real ``analysis_job()`` under ``cProfile``; keep the top functions.

    Args:
        engine: A new engine on an empty cache.
        stem: The path stem of the ``.prof`` file and of the text summary (``-profile.txt``).

    Returns:
        The profiled wall time, the frame and report counts, and the summary's path and top
        lines.

    Raises:
        BreakdownError: The job failed.
    """
    profiler = cProfile.Profile()
    progress = _Progress()
    job = engine.analysis_job()
    began = time.perf_counter()
    result = profiler.runcall(job, progress)
    wall = time.perf_counter() - began
    if not result.ok:
        raise BreakdownError(f"the profiled analysis failed: {result.failure}")
    profiler.dump_stats(str(stem.with_name(f"{stem.name}.prof")))
    text = io.StringIO()
    pstats.Stats(profiler, stream=text).sort_stats("tottime").print_stats(PROFILE_LINES)
    summary = stem.with_name(f"{stem.name}-profile.txt")
    summary.write_text(text.getvalue(), encoding="utf-8")
    return {
        "wall_s": wall,
        "frames": len(engine.store.axis()),
        "reports": progress.reports,
        "summary": str(summary),
        "top": [line for line in text.getvalue().splitlines() if line.strip()],
        "note": "cProfile overhead included: a cross-check, not a figure of record",
    }


def same_record(first: Mapping[str, Any], second: Mapping[str, Any]) -> bool:
    """Tell whether two records hold the same names with byte-identical arrays.

    Args:
        first: Statistic name -> array.
        second: Statistic name -> array.

    Returns:
        True when every name, dtype, shape and byte agrees.
    """
    if set(first) != set(second):
        return False
    for name, value in first.items():
        a, b = np.asarray(value), np.asarray(second[name])
        if a.dtype != b.dtype or a.shape != b.shape or a.tobytes() != b.tobytes():
            return False
    return True


def compare_analyses(replica: AnalysisEngine, engine: AnalysisEngine) -> dict[str, Any]:
    """Compare the replica's records and proxies with the engine's, bit for bit.

    Args:
        replica: The engine the replica ran through.
        engine: The engine whose real job ran.

    Returns:
        ``equal``, the frame and record counts, and the first differences found.
    """
    differences: list[str] = []
    axis = replica.store.axis()
    if axis != engine.store.axis():
        differences.append(f"axes differ: {len(axis)} against {len(engine.store.axis())} frames")
        axis = ()
    records = proxies = 0
    for pts in axis:
        for stage in replica._stages:
            if not same_record(
                replica.store.raw(pts, stage.name), engine.store.raw(pts, stage.name)
            ):
                differences.append(f"raw {stage.name} at pts {pts}")
            if not same_record(
                replica.store.smoothed(pts, stage.name), engine.store.smoothed(pts, stage.name)
            ):
                differences.append(f"smoothed {stage.name} at pts {pts}")
            records += 2
        a = replica._cache.proxy(replica._key, pts)
        b = engine._cache.proxy(engine._key, pts)
        if a.dtype != b.dtype or a.shape != b.shape or a.tobytes() != b.tobytes():
            differences.append(f"proxy at pts {pts}")
        proxies += 1
    return {
        "equal": not differences,
        "frames": len(axis),
        "records_compared": records,
        "proxies_compared": proxies,
        "differences": differences[:20],
        "difference_count": len(differences),
    }


# --- phase 3: the frame path ------------------------------------------------------------------


def _smoothed(engine: AnalysisEngine, pts: int, schema: str) -> dict[str, Statistics]:
    """``_write_frames``' read of the frame's smoothed record under the job's schema."""
    return engine.smoothed_record(pts, schema_hash=schema)


def _upload(frame: Frame, backend: ArrayBackend) -> Frame:
    """``_write_frames``' upload: the frame's pixels as float32 on the backend's device."""
    return dataclasses.replace(
        frame, pixels=backend.asarray(frame.pixels, np.float32), device=backend.device
    )


def _download(rendered: Any, backend: ArrayBackend) -> NDArray[np.float32]:
    """``_write_frames``' download of the rendered pixels."""
    return np.asarray(backend.to_host(rendered.pixels), dtype=np.float32)


def _write(sink: FFmpegVideoSink, frame: Frame, host: NDArray[np.float32]) -> None:
    """``_write_frames``' sink write of the host frame."""
    sink.write(dataclasses.replace(frame, pixels=host, device="cpu"))


def replay_frame_path(
    engine: AnalysisEngine,
    backend: ArrayBackend,
    method: CorrectionMethod,
    out_path: Path,
    clock: StepClock,
    planes: Accumulator,
    quantised: Accumulator,
) -> dict[str, Any]:
    """Replay ``ExportEngine._write_frames`` and the close, step by step, into the product sink.

    The encoder is ``auto`` resolved as the job resolves it, at Standard and the source's bit
    depth. The cancel watchdog the job runs beside the encode (a thread polling the cancel flag
    every ``POLL_S``) is not started: it touches nothing per frame.

    Args:
        engine: A complete analysis engine.
        backend: The job's backend.
        method: The correction method.
        out_path: The output file (made empty first, as the job's temporary is).
        clock: The phase's clock.
        planes: The ``planes_to_rgb`` timer.
        quantised: The ``rgb_to_planes`` timer (wrapped around the encode module's name).

    Returns:
        The encoder, the bit depth and the sink's frame count.
    """
    probe = engine._probe
    video = probe.video
    params = engine.parameters
    sink = FFmpegVideoSink()
    encoder = resolve_encoder("auto", sink.capabilities())
    bit_depth = 10 if video.bit_depth == 10 else 8
    out_path.write_bytes(b"")
    sink.open(
        probe, out_path, encoder=encoder, quality="standard", bit_depth=bit_depth, provenance=None
    )
    schema = engine.schema_hash
    progress = _Progress()
    frames: Iterator[Frame] = engine._source.frames(probe, hw_decode=backend.device != "cpu")
    written = 0
    try:
        while (taken := _next_frame(frames, clock, planes)) is not None:
            frame, began = taken
            record = clock.time("smoothed_record", _smoothed, engine, frame.pts_ticks, schema)
            on_device = clock.time("upload", _upload, frame, backend, device=True)
            rendered = clock.time("render", method.render, on_device, params, record, device=True)
            host = clock.time("to_host", _download, rendered, backend)
            quantised.take()
            clock.time("sink_write", _write, sink, frame, host)
            planar = quantised.take()
            clock.add("sink_write", -planar)
            clock.add("rgb_to_planes", planar)
            written += 1
            clock.time("report", progress.report, written, video.nb_frames, "Exporting")
            clock.end(time.perf_counter() - began)
    except BaseException:
        sink.abort()
        _close(frames)
        raise
    _close(frames)
    report = clock.time_once("close", sink.close)
    return {"encoder": encoder, "bit_depth": bit_depth, "frames_written": report.frames_written}


# --- the run ---------------------------------------------------------------------------------

GPU_FIELDS = (
    "clocks.sm",
    "utilization.gpu",
    "utilization.decoder",
    "utilization.encoder",
    "power.draw",
    "temperature.gpu",
    "memory.used",
)
"""The graphics-card readings summarised per phase."""


def gpu_by_phase(
    telemetry: Mapping[str, Any], spans: Mapping[str, tuple[float, float]]
) -> dict[str, Any]:
    """Summarise the graphics-card readings inside each phase: their count and medians.

    Args:
        telemetry: :meth:`Telemetry.stop`'s record (readings stamped from its origin).
        spans: Phase name -> (start, end) seconds from the same origin.

    Returns:
        Phase name -> ``readings`` and the median of each of :data:`GPU_FIELDS` (None when no
        reading of the phase gives it).
    """
    summary: dict[str, Any] = {}
    for name, (lo, hi) in spans.items():
        rows = [row for row in telemetry.get("gpu", []) if lo <= float(row["t_s"]) <= hi]
        values: dict[str, Any] = {"readings": len(rows)}
        for field in GPU_FIELDS:
            numbers: list[float] = []
            for row in rows:
                with contextlib.suppress(KeyError, ValueError):
                    numbers.append(float(row[field]))
            values[field] = statistics.median(numbers) if numbers else None
        summary[name] = values
    return summary


def refuse_inside(folder: Path, footage: Path) -> None:
    """Refuse an output folder that is, or lies inside, the footage folder.

    Args:
        folder: The output folder.
        footage: The footage folder.

    Raises:
        BreakdownError: It does.
    """
    out = Path(os.path.normcase(os.path.abspath(folder)))
    root = Path(os.path.normcase(os.path.abspath(footage)))
    if out == root or root in out.parents:
        raise BreakdownError(f"{folder} lies inside the footage folder; nothing is written there")


def run(
    path: Path,
    run_dir: Path,
    method_id: str,
    *,
    force_cpu: bool,
    profile: bool,
    frames: bool,
    periods: tuple[float, float] = (0.25, 1.0),
    record: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run the phases on one clip into ``run_dir`` and return the record.

    Args:
        path: The source clip (read only).
        run_dir: A new folder for the caches and the output.
        method_id: The method id.
        force_cpu: ``Settings.force_cpu``.
        profile: Run phase 2 (the engine under ``cProfile``) and the equality check.
        frames: Run phase 3 (the frame path; it renders with phase 2's engine).
        periods: The telemetry periods (memory, graphics card) in seconds.
        record: The record to fill (a new one when None); a phase that raises leaves what
            the phases before it recorded, and the telemetry.

    Returns:
        The record.

    Raises:
        BreakdownError: ``run_dir`` exists, or a phase failed.
    """
    try:
        run_dir.mkdir(parents=True)
    except FileExistsError as error:
        raise BreakdownError(f"{run_dir} exists; a run never reuses a folder") from error
    method = available_methods()[method_id]
    replica, backend, reason = build_analysis(
        path, run_dir / "cache-replica", method, force_cpu=force_cpu
    )
    synchronize = synchronizer(backend)
    video = replica._probe.video
    record = {} if record is None else record
    record.update(
        {
            "clip": path.name,
            "method": method_id,
            "device": reason,
            "hw_decode": backend.device != "cpu",
            "size": [video.height, video.width],
            "frame_rate": str(video.frame_rate),
            "source_frames": video.nb_frames,
        }
    )
    telemetry = Telemetry(memory_every=periods[0], gpu_every=periods[1])
    telemetry.start()
    origin = telemetry.origin if telemetry.origin is not None else time.perf_counter()
    spans: dict[str, tuple[float, float]] = {}
    phases: dict[str, Any] = {}
    planes, quantised = Accumulator(), Accumulator()
    progress = _Progress()

    def span(name: str, began: float) -> float:
        ended = time.perf_counter()
        spans[name] = (began - origin, ended - origin)
        return ended

    try:
        with (
            timed_name(decode_module, "planes_to_rgb", planes),
            timed_name(encode_module, "rgb_to_planes", quantised),
        ):
            clock = StepClock(synchronize)
            began = time.perf_counter()
            replay_decode_pass(replica, clock, planes, progress)
            phases["decode_pass"] = phase_summary(clock, began, span("decode_pass", began))
            began = time.perf_counter()
            stage_clocks = replay_later_stages(replica, lambda: StepClock(synchronize), progress)
            ended = span("later_stages", began)
            phases["later_stages"] = {
                name: phase_summary(*timed) for name, timed in stage_clocks.items()
            }
            phases["later_stages_wall_s"] = ended - began
            if profile:
                engine, _, _ = build_analysis(
                    path, run_dir / "cache-engine", method, force_cpu=force_cpu
                )
                began = time.perf_counter()
                record["profile"] = profile_engine(engine, run_dir)
                span("engine_profiled", began)
                record["equality"] = compare_analyses(replica, engine)
                if frames:
                    clock = StepClock(synchronize)
                    began = time.perf_counter()
                    record["sink"] = replay_frame_path(
                        engine, backend, method, run_dir / "out.mp4", clock, planes, quantised
                    )
                    phases["frame_path"] = phase_summary(clock, began, span("frame_path", began))
    finally:
        record["telemetry"] = telemetry.stop()
        record["phases"] = phases
        record["phase_spans_s"] = spans
        record["timer_calls"] = {"planes_to_rgb": planes.calls, "rgb_to_planes": quantised.calls}
    record["gpu_by_phase"] = gpu_by_phase(record["telemetry"], spans)
    return record


def summary_lines(record: Mapping[str, Any]) -> list[str]:
    """Return the record's summary lines (``PHASE``, ``STEP``, ``ONCE``, ``CHECK``, ``GPU``).

    Args:
        record: A run's record.

    Returns:
        The lines, ASCII.
    """
    lines: list[str] = []
    phases = record.get("phases", {})
    tables: list[tuple[str, Mapping[str, Any]]] = []
    if "decode_pass" in phases:
        tables.append(("decode_pass", phases["decode_pass"]))
    for name, table in phases.get("later_stages", {}).items():
        tables.append((f"stage:{name}", table))
    if "frame_path" in phases:
        tables.append(("frame_path", phases["frame_path"]))
    for name, table in tables:
        lines.append(
            f"PHASE {name}: {table['frames']} frames, {table['wall_s']:.2f} s; mean wall "
            f"{table['mean_wall_s']:.5f} s/frame; sum of step means {table['sum_of_means_s']:.5f}"
            f"; residual {100 * table['residual']:.2f} % "
            f"({'within' if table['within_limit'] else 'OVER'} {100 * RESIDUAL_LIMIT:g} %)"
        )
        for step, figures in table["steps"].items():
            lines.append(
                f"STEP {name} {step}: mean {figures.get('mean', 0.0):.5f} median "
                f"{figures.get('median', 0.0):.5f} p90 {figures.get('p90', 0.0):.5f} "
                f"total {figures['total_s']:.2f} s"
            )
        for step, seconds in table["once"].items():
            lines.append(f"ONCE {name} {step}: {seconds:.3f} s")
    equality = record.get("equality")
    if equality is not None:
        lines.append(
            f"CHECK replica equals engine: {'yes' if equality['equal'] else 'NO'} "
            f"({equality['records_compared']} records, {equality['proxies_compared']} proxies)"
        )
    if "profile" in record:
        lines.append(f"PROFILE engine wall {record['profile']['wall_s']:.2f} s (cProfile on)")
    for name, gpu in record.get("gpu_by_phase", {}).items():
        lines.append(
            f"GPU {name}: {gpu['readings']} readings; median SM {gpu['clocks.sm']} MHz, "
            f"util {gpu['utilization.gpu']} %, dec {gpu['utilization.decoder']} %, "
            f"enc {gpu['utilization.encoder']} %, {gpu['power.draw']} W"
        )
    return lines


def _save(path: Path, record: Mapping[str, Any]) -> None:
    path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the breakdown on one clip and write its record under the working folder.

    Args:
        argv: The command-line arguments (``sys.argv[1:]`` when None).

    Returns:
        The exit status.
    """
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    parser.add_argument("clip", help="footage stem, for example GX011627")
    parser.add_argument("--method", default="c3", choices=tuple(available_methods()))
    parser.add_argument("--force-cpu", action="store_true", help="force the CPU backend")
    parser.add_argument("--skip-profile", action="store_true", help="no phase 2 (nor 3)")
    parser.add_argument("--skip-frames", action="store_true", help="no phase 3")
    parser.add_argument("--keep", action="store_true", help="keep the caches and the output")
    parser.add_argument("--config", type=Path, help="local configuration file to read")
    parser.add_argument("--memory-every", type=period, default=0.25, help="seconds")
    parser.add_argument("--gpu-every", type=period, default=1.0, help="seconds")
    args = parser.parse_args(argv)
    try:
        config = load_local_config(args.config)
        out_dir = config.working_path / SUBDIR
        refuse_inside(out_dir, config.footage_path)
        path = find_footage_file(args.clip, config.footage_path)
        out_dir.mkdir(parents=True, exist_ok=True)
    except (LocalConfigError, ValueError, OSError, BreakdownError) as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    name = f"breakdown-{args.clip}-{args.method}-{stamp}"
    record_path = out_dir / f"{name}.json"
    run_dir = out_dir / name
    record: dict[str, Any] = {
        "argv": list(sys.argv[1:] if argv is None else argv),
        "pid": os.getpid(),
    }
    status = 0
    try:
        run(
            path,
            run_dir,
            args.method,
            force_cpu=args.force_cpu,
            profile=not args.skip_profile,
            frames=not (args.skip_profile or args.skip_frames),
            periods=(args.memory_every, args.gpu_every),
            record=record,
        )
        if record.get("equality", {}).get("equal") is False:
            status = 1
    except Exception as error:
        record["failed"] = f"{type(error).__name__}: {error}"
        print(f"FAILED {record['failed']}", file=sys.stderr)
        status = 1
    finally:
        if not args.keep:
            shutil.rmtree(run_dir, ignore_errors=True)
        _save(record_path, record)
    for line in summary_lines(record):
        print(line)
    print(f"RECORD {record_path}")
    return status


if __name__ == "__main__":
    sys.exit(main())
