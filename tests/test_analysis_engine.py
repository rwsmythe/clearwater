"""The analysis engine: decode pass, stages, AD-5, V17, V18, cancel, failures, threads."""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.analysis import CANCELLED, make_proxy
from clearwater.cache import DiskProxyCache
from clearwater.interfaces import CacheKey, JobResult
from clearwater.interfaces.stubs import StubProgress
from test_analysis_support import (
    KEY,
    Compensated,
    CountingCache,
    GrayWorld,
    ListSource,
    OneStage,
    make_engine,
    make_frame,
    make_probe,
    run,
    synthetic_frames,
)


class CancelAfter(StubProgress):
    """A progress that asks to cancel once ``after`` reports have arrived."""

    def __init__(self, after: int) -> None:
        super().__init__()
        self.after = after

    def report(self, done: int, total: int | None, message: str) -> None:
        super().report(done, total, message)
        if len(self.reports) >= self.after:
            self.cancel()


def _smoothed_series(engine: Any, stage: str, name: str) -> np.ndarray:
    return np.array([engine.store.smoothed(p, stage)[name] for p in engine.store.axis()])


def _raw_series(engine: Any, stage: str, name: str) -> np.ndarray:
    return np.array([engine.store.raw(p, stage)[name] for p in engine.store.axis()])


def test_a_full_analysis_completes_with_progress() -> None:
    """Decode pass then stages; done reaches total; the cache entry is marked complete once."""
    method = GrayWorld()
    frames = synthetic_frames(90)
    engine, source, cache = make_engine(method, frames)
    progress = StubProgress()
    result = run(engine, progress)
    assert isinstance(result, JobResult)
    assert result.ok and result.failure is None and result.device == "cpu"
    assert engine.state().phase == "complete" and engine.is_complete()
    assert engine.state().done == engine.state().total == 180
    done = [r[0] for r in progress.reports]
    assert done == sorted(done) and done[-1] == 180
    assert all(r[1] == 180 for r in progress.reports)
    assert source.iterations == 1 and isinstance(cache, CountingCache) and cache.marks == 1
    assert engine.store.axis() == tuple(f.pts_ticks for f in frames)
    record = engine.smoothed_record(frames[45].pts_ticks)
    assert set(record) == {"white_balance", "fusion"}


def test_stage_two_is_measured_with_stage_one_smoothed() -> None:
    """D97: the later stage sees the SMOOTHED earlier records (a planted raw would differ)."""
    method = GrayWorld()
    engine, _, _ = make_engine(method, synthetic_frames(90))
    assert run(engine).ok
    seen = _raw_series(engine, "fusion", "seen_gains")
    smoothed = _smoothed_series(engine, "white_balance", "gains")
    raw = _raw_series(engine, "white_balance", "gains")
    assert np.array_equal(seen, smoothed)
    assert np.max(np.abs(seen - raw)) > 1e-3  # the planted "raw earlier" is distinguishable


def test_a_one_stage_method_runs() -> None:
    """D98: a flat (single-stage) method is analysed and smoothed."""
    engine, _, _ = make_engine(OneStage(), synthetic_frames(40))
    assert run(engine).ok
    smoothed = _smoothed_series(engine, "flat", "means")
    raw = _raw_series(engine, "flat", "means")
    assert smoothed.shape == raw.shape == (40, 3)
    assert not np.array_equal(smoothed, raw)


def test_statistics_are_measured_on_the_stored_proxy(tmp_path: Path) -> None:
    """AD-5: every image measured is the proxy READ BACK from a lossy cache, never pre-store."""
    rng = np.random.default_rng(3)
    base = rng.uniform(0.1, 0.9, size=(48, 64, 3))
    frames = [
        make_frame(np.clip(base * (1 + 0.05 * i), 0, 1), i * 1001, Frame_TB, i) for i in range(12)
    ]
    with DiskProxyCache(tmp_path / "cache") as cache:
        key = CacheKey(1, 2, cache.cache_version)
        method = GrayWorld()
        engine, _, _ = make_engine(method, frames, cache=cache)  # type: ignore[arg-type]
        engine._key = key
        assert run(engine).ok
        stage_one = [
            img
            for (stage, _), img in zip(method.calls, method.images, strict=True)
            if stage == "white_balance"
        ]
        assert len(stage_one) == 12
        lossy = 0
        for frame, image in zip(frames, stage_one, strict=True):
            stored = cache.proxy(key, frame.pts_ticks)
            expected = (stored.astype(np.float32) / np.float32(255)).astype(np.float64)
            assert np.array_equal(image, expected)
            pre_store = make_proxy(np.asarray(frame.pixels)).astype(np.float64) / 255
            lossy += int(not np.array_equal(pre_store, expected))
        assert lossy > 0  # the codec is lossy, so a planted pre-store measurement would differ


Frame_TB = make_probe().video.time_base


def test_a_complete_entry_skips_the_decode_pass_and_gives_the_same_statistics() -> None:
    """V17 (analysis side): reopening reads the proxies; the frame source is never iterated."""
    frames = synthetic_frames(60)
    engine, _, cache = make_engine(GrayWorld(), frames)
    assert run(engine).ok
    again, source2, _ = make_engine(GrayWorld(), frames, cache=cache)
    assert run(again).ok
    assert source2.iterations == 0 and source2.yielded == 0
    for pts in engine.store.axis():
        for stage in ("white_balance", "fusion"):
            first, second = engine.smoothed_record(pts)[stage], again.smoothed_record(pts)[stage]
            assert all(np.array_equal(first[n], second[n]) for n in first)


def test_an_incomplete_entry_runs_the_decode_pass() -> None:
    """Only ``complete`` skips the decode pass (AD-20 amendment, WP3.12 consumer note)."""
    frames = synthetic_frames(30)
    cache = CountingCache()
    cache.store_proxy(KEY, frames[0].pts_ticks, make_proxy(np.asarray(frames[0].pixels)))
    engine, source, _ = make_engine(GrayWorld(), frames, cache=cache)
    assert run(engine).ok
    assert source.iterations == 1 and source.yielded == 30
    assert cache.marks == 1


def test_stale_proxies_of_an_incomplete_entry_are_never_marked_complete() -> None:
    """IF-7: proxies the pass did not store (an earlier, longer pass's tail) fail by name."""
    frames = synthetic_frames(20)
    cache = CountingCache()
    stale = frames[-1].pts_ticks + 1001
    cache.store_proxy(KEY, stale, make_proxy(np.asarray(frames[0].pixels)))
    engine, source, _ = make_engine(GrayWorld(), frames, cache=cache)
    result = run(engine)
    assert not result.ok and str(stale) in str(result.failure), result.failure
    assert "not decoded by this pass" in str(result.failure)
    assert source.yielded == 20 and cache.marks == 0
    entry = cache.lookup(KEY)
    assert entry is not None and not entry.complete


def test_a_source_only_stage_is_read_back_and_passed_through_closed_form() -> None:
    """Y-1 (e): the cached record is used only through ``closed_form`` with the current params."""
    frames = synthetic_frames(30)
    first_method = Compensated()
    engine, _, cache = make_engine(first_method, frames, params={"cap": 0.5})
    assert run(engine).ok
    assert first_method.analyzed.count("compensation") == 30
    entry = cache.lookup(KEY)
    assert entry is not None and entry.complete and entry.stages == ("compensation",)
    method = Compensated()
    again, source, _ = make_engine(method, frames, cache=cache, params={"cap": 0.01})
    assert isinstance(cache, CountingCache)
    reads = cache.source_reads
    assert run(again).ok
    assert source.iterations == 0
    assert cache.source_reads - reads == 30
    assert "compensation" not in method.analyzed
    assert method.closed.count("compensation") == 30
    alpha = _raw_series(again, "compensation", "alpha")
    assert np.all(alpha <= 0.01)


def test_reopen_progress_counts_each_frame_stage_once() -> None:
    """Progress units: reading cached statistics adds no units; 2 stages x 30 frames = 60."""
    frames = synthetic_frames(30)
    engine, _, cache = make_engine(Compensated(), frames)
    assert run(engine).ok
    again, _, _ = make_engine(Compensated(), frames, cache=cache)
    progress = StubProgress()
    assert run(again, progress).ok
    assert again.state().done == again.state().total == 60
    done = [r[0] for r in progress.reports]
    assert done == sorted(done) and done[-1] == 60
    assert {r[1] for r in progress.reports} <= {None, 60}


def test_cancel_stops_within_one_frame_and_unloads() -> None:
    """D70, AD-15: cancel stops within one frame, never marks complete, drops the statistics."""
    frames = synthetic_frames(50)
    engine, source, cache = make_engine(GrayWorld(), frames)
    result = run(engine, CancelAfter(5))
    assert not result.ok and result.failure == CANCELLED
    assert source.yielded == 6
    assert isinstance(cache, CountingCache) and cache.marks == 0
    assert engine.state().phase == "cancelled"
    assert engine.store.axis() == () and engine.store.all_pts() == []
    entry = cache.lookup(KEY)
    assert entry is not None and not entry.complete
    with pytest.raises(KeyError):
        engine.smoothed_record(frames[0].pts_ticks)
    # The engine's own cancel works too, and a new job starts again from the unloaded state.
    hooked = StubProgress()
    hooked.report = lambda done, total, message: engine.cancel()  # type: ignore[method-assign]
    assert run(engine, hooked).failure == CANCELLED
    assert run(engine).ok and engine.is_complete()


def test_a_cancel_at_the_last_decode_report_never_marks_complete() -> None:
    """D70, IF-7: a cancel raised by the last frame's report stops before ``mark_complete``."""
    frames = synthetic_frames(12)
    engine, source, cache = make_engine(GrayWorld(), frames)
    result = run(engine, CancelAfter(len(frames)))
    assert not result.ok and result.failure == CANCELLED
    assert source.yielded == len(frames)
    assert isinstance(cache, CountingCache) and cache.marks == 0
    entry = cache.lookup(KEY)
    assert entry is not None and not entry.complete


def test_a_cancel_during_the_last_smooth_is_not_published_as_complete() -> None:
    """D70, AD-15: a cancel that arrives while the last stage is smoothed still unloads."""
    frames = synthetic_frames(30)
    engine, _, _ = make_engine(GrayWorld(), frames)
    smooth = engine.store.smooth

    def cancelling_smooth(stage: str, *args: Any) -> None:
        smooth(stage, *args)
        if stage == "fusion":
            engine.cancel()

    engine.store.smooth = cancelling_smooth  # type: ignore[method-assign]
    result = run(engine)
    assert not result.ok and result.failure == CANCELLED
    assert engine.state().phase == "cancelled" and not engine.is_complete()
    with pytest.raises(KeyError):
        engine.smoothed_record(frames[0].pts_ticks)


def test_a_reader_never_gets_old_records_under_the_new_schema() -> None:
    """DR-25 (4): while a change is taken up, a reader gets KeyError, never the old records."""
    frames = synthetic_frames(60)
    engine, _, _ = make_engine(GrayWorld(), frames)
    assert run(engine).ok
    pts = frames[30].pts_ticks
    seen: list[str] = []
    invalidate = engine.store.invalidate_from
    rehash = type(engine.store).schema_hash

    def read() -> None:
        try:
            engine.smoothed_record(pts)
            seen.append("served")
        except KeyError:
            seen.append("KeyError")

    def reading_invalidate(stage: str) -> None:
        read()  # before the invalidation
        invalidate(stage)
        read()  # after it

    class Store(type(engine.store)):  # type: ignore[misc]
        @property
        def schema_hash(self) -> str:
            return rehash.fget(self)  # type: ignore[no-any-return]

        @schema_hash.setter
        def schema_hash(self, value: str) -> None:
            read()  # before the store is switched to ``value``
            rehash.fset(self, value)
            read()  # after it

    engine.store.__class__ = Store
    engine.store.invalidate_from = reading_invalidate  # type: ignore[method-assign]
    job = engine.set_parameters({**engine.parameters, "gamma": 2.0}, pts)
    assert job is not None
    seen.clear()
    assert job(StubProgress()).ok
    assert len(seen) >= 4 and set(seen[:4]) == {"KeyError"}, seen
    assert engine.smoothed_record(pts)["fusion"]["level"] is not None


def test_a_failing_analyze_gives_failed_with_its_message() -> None:
    """A failure carries its message; nothing is marked complete; statistics are dropped."""
    method = GrayWorld()
    method.fail_on = "white_balance"
    engine, _, cache = make_engine(method, synthetic_frames(20))
    result = run(engine)
    assert not result.ok and result.failure == "RuntimeError: planted failure in white_balance"
    state = engine.state()
    assert state.phase == "failed" and state.message == result.failure
    assert isinstance(cache, CountingCache) and cache.marks == 0
    assert engine.store.axis() == ()


def test_a_read_error_fails_and_an_early_end_does_not() -> None:
    """A source error fails; a source that stops before ``nb_frames`` (D86) completes."""
    frames = synthetic_frames(20)
    engine, source, cache = make_engine(GrayWorld(), frames)
    source.fail_after = 7
    result = run(engine)
    assert not result.ok and result.failure is not None and "planted read error" in result.failure
    assert isinstance(cache, CountingCache) and cache.marks == 0
    short, _, short_cache = make_engine(GrayWorld(), frames[:12], nb_frames=20)
    assert run(short).ok and len(short.store.axis()) == 12
    assert isinstance(short_cache, CountingCache) and short_cache.marks == 1


def test_no_frames_fails() -> None:
    """A source that yields nothing is a failure, not an empty analysis."""
    engine, _, _ = make_engine(GrayWorld(), [])
    result = run(engine)
    assert not result.ok and result.failure == "ValueError: the frame source yielded no frames"


def test_out_of_order_pts_and_size_changes_are_refused() -> None:
    """The envelope: out-of-order or duplicate pts and a frame size change are refused by name."""
    frames = synthetic_frames(6)
    swapped = [frames[0], frames[2], frames[1], *frames[3:]]
    engine, _, _ = make_engine(GrayWorld(), swapped)
    result = run(engine)
    assert result.failure is not None and "out of order or duplicated" in result.failure
    duplicate = [frames[0], frames[0]]
    engine, _, _ = make_engine(GrayWorld(), duplicate)
    assert "out of order or duplicated" in str(run(engine).failure)
    bigger = make_frame(np.zeros((10, 12, 3)), frames[3].pts_ticks + 5000, Frame_TB, 9)
    engine, _, _ = make_engine(GrayWorld(), [*frames[:4], bigger])
    assert "frame size changed" in str(run(engine).failure)


def test_a_frame_size_change_with_an_equal_proxy_shape_is_refused() -> None:
    """Task 2: a frame size change is refused even when both sizes give one proxy shape."""
    first = np.full((1082, 1100, 3), 0.5, dtype=np.float32)
    second = np.full((1081, 1100, 3), 0.5, dtype=np.float32)
    assert make_proxy(first).shape == make_proxy(second).shape == (541, 550, 3)
    frames = [
        make_frame(first, 0, Frame_TB, 0),
        make_frame(first, 1001, Frame_TB, 1),
        make_frame(second, 2002, Frame_TB, 2),
    ]
    engine, _, cache = make_engine(GrayWorld(), frames)
    failure = str(run(engine).failure)
    assert "frame size changed" in failure and "(1081, 1100, 3)" in failure, failure
    assert "(1082, 1100, 3)" in failure
    assert isinstance(cache, CountingCache) and cache.marks == 0


def test_provisional_statistics_come_before_the_smoothed_ones() -> None:
    """V18 (engine side): a frame's own chain while the analysis runs, smoothed after."""
    frames = synthetic_frames(60)
    method = GrayWorld()
    engine, source, _ = make_engine(method, frames)
    source.pause_after = 10
    job = engine.analysis_job()
    results: list[JobResult] = []
    worker = threading.Thread(target=lambda: results.append(job(StubProgress())))
    worker.start()
    try:
        assert source.paused.wait(10)
        pts = frames[3].pts_ticks
        assert engine.state().phase == "running"
        provisional = engine.provisional_record(pts)
        assert provisional is not None and set(provisional) == {"white_balance", "fusion"}
        assert engine.provisional_record(frames[30].pts_ticks) is None  # not stored yet
        with pytest.raises(KeyError):
            engine.smoothed_record(pts)
    finally:
        source.resume.set()
        worker.join(30)
    assert results and results[0].ok
    smoothed = engine.smoothed_record(pts)
    assert not np.array_equal(
        smoothed["white_balance"]["gains"], provisional["white_balance"]["gains"]
    )
    # The provisional chain is the frame's own: its fusion stage saw its own unsmoothed gains.
    assert np.array_equal(
        provisional["fusion"]["seen_gains"], provisional["white_balance"]["gains"]
    )


def test_a_second_job_while_one_runs_is_refused() -> None:
    """One writer at a time."""
    engine, _, _ = make_engine(GrayWorld(), synthetic_frames(5))
    engine.analysis_job()
    with pytest.raises(RuntimeError, match="already running"):
        engine.analysis_job()


def test_readers_on_other_threads_while_the_job_writes() -> None:
    """One analysis thread writing while readers call ``smoothed_record``, ``state``, the store."""
    frames = synthetic_frames(150)
    engine, _, _ = make_engine(GrayWorld(), frames)
    stop = threading.Event()
    errors: list[BaseException] = []
    seen_phases: set[str] = set()

    def reader() -> None:
        try:
            while not stop.is_set():
                seen_phases.add(engine.state().phase)
                for frame in frames[::37]:
                    try:
                        record = engine.smoothed_record(frame.pts_ticks)
                        assert set(record) == {"white_balance", "fusion"}
                    except KeyError:
                        pass
                    engine.provisional_record(frame.pts_ticks)
                engine.store.all_pts()
        except BaseException as exc:
            errors.append(exc)

    job = engine.analysis_job()
    readers = [threading.Thread(target=reader) for _ in range(3)]
    for thread in readers:
        thread.start()
    try:
        result = job(StubProgress())
    finally:
        stop.set()
        for thread in readers:
            thread.join(30)
    assert result.ok and not errors
    assert "running" in seen_phases


def test_the_engine_needs_a_stage_and_a_known_smoother() -> None:
    """Construction refuses a stage-less method and an unknown kind."""
    method = OneStage()
    method.stages = ()
    with pytest.raises(ValueError, match="declares no stage"):
        make_engine(method, [])
    with pytest.raises(ValueError, match="unknown smoothing kind"):
        make_engine(GrayWorld(), [], kind="box")
    probe = make_probe()
    assert isinstance(ListSource([], probe).probe(Path("x")), type(probe))
