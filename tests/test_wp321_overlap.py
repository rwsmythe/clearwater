"""WP3.21 task 4: the analysis overlapped with the export (AD-7 as read at ruling Q2; Q-c, Q-R4).

The export job runs the clip's analysis on its own thread and renders frame i once the engine has
published i's record as final for every stage. These tests pin: the lead derived from the stage
graph (61 for c3 and 91 for ancuti2018 at 30000/1001, over pts on a VFR axis); every frame
rendered with exactly the whole-clip record; a lead short by ONE failing by name; each thread
holding one decoded frame; frames rendered in decode order; cancel at each phase; a failure in
either half; one cache writer; and no analysis thread alive at ``commit`` or after the job.
"""

from __future__ import annotations

import itertools
import threading
import time
import weakref
from collections.abc import Iterator
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.analysis import AnalysisEngine
from clearwater.analysis import engine as engine_module
from clearwater.analysis.engine import composed_reach, lead_frames
from clearwater.analysis.smoothing import DEFAULT_KIND, DEFAULT_WINDOW_S
from clearwater.interfaces import CacheKey, Frame, JobResult, ProbeResult
from clearwater.interfaces.stubs import StubProgress, StubProxyCache
from clearwater.jobs import SafeWrite
from clearwater.jobs.export_seam import CANCELLED
from clearwater.methods.ancuti_fusion import ANCUTI2018_STAGES, C3_STAGES
from test_analysis_support import CFR_STEP, CFR_TIME_BASE, ListSource
from test_jobs_export_support import CPU, FakeSink, Rig

FRAMES = 200
"""Frames in the overlap rig: well past the GrayWorld lead (61 at 30000/1001)."""

KEY = CacheKey(size=1, mtime_ns=2, cache_version=3)
"""The rig's cache key."""


def _axis(frames: int, step: int = CFR_STEP) -> np.ndarray:
    return 7 + step * np.arange(frames, dtype=np.int64)


# --- the lead (Q-c) -----------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("stages", "lead"), [(C3_STAGES, 61), (ANCUTI2018_STAGES, 91)], ids=["c3", "ancuti2018"]
)
@pytest.mark.parametrize(
    ("time_base", "step"), [(CFR_TIME_BASE, CFR_STEP), (Fraction(1, 90000), 3003)]
)
def test_the_derived_lead_at_29_97(stages: Any, lead: int, time_base: Fraction, step: int) -> None:
    ticks = _axis(600, step)
    got = lead_frames(ticks, time_base, DEFAULT_WINDOW_S, DEFAULT_KIND, len(stages), 300)
    assert got == lead


def test_the_lead_is_over_pts_on_a_vfr_axis() -> None:
    # 60 fps (500 ticks at 1/30000): the 1 s half-window holds 60 frames, the 0.05 s median 3.
    steps = np.r_[np.full(300, CFR_STEP), np.full(400, 500)]
    ticks = 7 + np.concatenate([[0], np.cumsum(steps)])
    lead = lead_frames(ticks, CFR_TIME_BASE, DEFAULT_WINDOW_S, DEFAULT_KIND, 2, 500)
    assert lead == 2 * (60 + 3) + 1
    # Brute force over pts: the last frame whose tick lies within the composed windows.
    end = 500
    for _ in range(2):
        end = int(np.searchsorted(ticks, ticks[end] + 30000, side="right")) - 1
        end = int(np.searchsorted(ticks, ticks[end] + 1500, side="right")) - 1
    assert composed_reach(ticks, CFR_TIME_BASE, DEFAULT_WINDOW_S, DEFAULT_KIND, 2, 500)[1] == end


# --- the rig ------------------------------------------------------------------------------------


class _Streams(ListSource):
    """A list source that records, per stream, every frame it yields and the frames still held.

    Each stream yields fresh pixel arrays; before each yield the frames of that stream still
    alive (held by the consumer) are counted, so a consumer keeping two decoded frames shows.
    """

    def __init__(self, frames: list[Frame], probe: ProbeResult) -> None:
        super().__init__(frames, probe)
        self.events: list[tuple[str, int]] = []
        self.held: dict[str, int] = {}
        self.threads: dict[str, str] = {}
        self._ids = itertools.count()
        self._lock = threading.Lock()

    def frames(self, probe: ProbeResult, **options: Any) -> Iterator[Frame]:
        tag = f"stream-{next(self._ids)}"
        return self._stream(tag)

    def _stream(self, tag: str) -> Iterator[Frame]:
        self.threads[tag] = threading.current_thread().name
        alive: list[weakref.ref[np.ndarray]] = []
        for frame in self._frames:
            held = sum(1 for ref in alive if ref() is not None)
            pixels = np.array(frame.pixels)
            alive.append(weakref.ref(pixels))
            out = replace(frame, pixels=pixels)
            del pixels
            with self._lock:
                self.held[tag] = max(self.held.get(tag, 0), held)
                self.events.append((tag, out.pts_ticks))
            yield out
            del out


class _Cache(StubProxyCache):
    """The stub cache, recording the thread of every store call."""

    def __init__(self) -> None:
        super().__init__()
        self.writes: list[tuple[str, str]] = []

    def _note(self, call: str) -> None:
        self.writes.append((threading.current_thread().name, call))

    def store_proxy(self, key: CacheKey, pts_ticks: int, proxy: Any) -> None:
        self._note("store_proxy")
        super().store_proxy(key, pts_ticks, proxy)

    def mark_complete(self, key: CacheKey) -> None:
        self._note("mark_complete")
        super().mark_complete(key)


def _rig(tmp_path: Path, *, delay_s: float = 0.002) -> tuple[Rig, _Streams, _Cache]:
    """A 200-frame rig whose analysis is slower than its render (so the export waits on it)."""
    rig = Rig(tmp_path, frames=FRAMES)
    source = _Streams(rig.frames, rig.probe)
    cache = _Cache()
    rig.source = source
    rig.cache = cache
    rig.engine._video_source = source  # type: ignore[assignment]
    rig.engine._cache = cache  # type: ignore[assignment]
    renders: dict[int, Any] = {}
    real_render = rig.method.render

    def render(image: Any, params: Any, statistics: Any) -> Any:
        renders[int(image.pts_ticks)] = statistics
        return real_render(image, params, statistics)

    rig.method.render = render  # type: ignore[method-assign]
    rig.method.renders = renders  # type: ignore[attr-defined]
    rig.method.hook = lambda stage: time.sleep(delay_s)
    return rig, source, cache


def _whole_clip_records(rig: Rig) -> dict[int, Any]:
    """The records of the serial whole-clip analysis of the rig's frames (the reference)."""
    hook, rig.method.hook = rig.method.hook, None
    try:
        engine = AnalysisEngine(
            method=rig.method,
            backend=CPU,
            cache=StubProxyCache(),
            key=KEY,
            source=ListSource(rig.frames, rig.probe),
            probe=rig.probe,
            params={p.name: p.default for p in rig.method.parameters},
        )
        result = engine.analysis_job()(StubProgress())
        assert result.ok, result.failure
        return {f.pts_ticks: engine.smoothed_record(f.pts_ticks) for f in rig.frames}
    finally:
        rig.method.hook = hook


def _assert_whole_clip_records(rendered: dict[int, Any], reference: dict[int, Any]) -> None:
    assert sorted(rendered) == sorted(reference), "a frame was not rendered"
    for pts, record in reference.items():
        for stage, values in record.items():
            for name, value in values.items():
                got = rendered[pts][stage][name]
                assert got.dtype == value.dtype and np.array_equal(got, value), (
                    f"pts {pts}: {stage}.{name} differs from the whole-clip record"
                )


def _analysis_threads() -> list[threading.Thread]:
    return [t for t in threading.enumerate() if t.name == "export-analysis"]


def _assert_overlapped(source: _Streams) -> None:
    """The export's first frame came before the analysis's last (the halves overlapped)."""
    tags = list(dict.fromkeys(tag for tag, _ in source.events))
    assert len(tags) == 2, f"expected two decode streams, got {tags}"
    analysis, export = tags
    first_export = next(i for i, (tag, _) in enumerate(source.events) if tag == export)
    last_analysis = max(i for i, (tag, _) in enumerate(source.events) if tag == analysis)
    assert first_export < last_analysis, "the export started only after the whole analysis"


# --- equality, overlap and order ----------------------------------------------------------------


def test_every_frame_renders_with_the_whole_clip_record_while_the_analysis_runs(
    tmp_path: Path,
) -> None:
    rig, source, _ = _rig(tmp_path)
    result = rig.run(rig.request())
    assert result.ok, result.failure
    _assert_overlapped(source)
    _assert_whole_clip_records(rig.method.renders, _whole_clip_records(rig))  # type: ignore[attr-defined]
    assert [f.pts_ticks for f in rig.sink.frames] == [f.pts_ticks for f in rig.frames]
    assert _analysis_threads() == []


def test_the_threads_are_the_analysis_and_the_job(tmp_path: Path) -> None:
    rig, source, _ = _rig(tmp_path)
    box: dict[str, Any] = {}
    job = threading.Thread(target=lambda: box.update(r=rig.run(rig.request())), name="the-job")
    job.start()
    job.join(60)
    assert box["r"].ok, box["r"].failure
    assert sorted(source.threads.values()) == ["export-analysis", "the-job"]


def test_a_planted_lead_short_by_one_fails_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Q-c: the stream publishes one frame more than is final, i.e. it would render frame k when
    # only k + 60 frames are decoded, one short of the derived lead of 61.
    real = engine_module.AnalysisEngine._final_count

    def short(self: AnalysisEngine, stream: Any) -> int:
        final: int = real(self, stream)
        return final + 1 if 0 < final < stream.raw[0] else final  # past the start's clipping

    monkeypatch.setattr(engine_module.AnalysisEngine, "_final_count", short)
    rig, _, _ = _rig(tmp_path)
    result = rig.run(rig.request())
    assert not result.ok
    assert "RenderBeforeFinalError" in result.failure and "render before final" in result.failure
    assert "60 frames after it, lead 61" in result.failure, result.failure
    assert result.outputs == () and "abort" in rig.sink.calls and "close" not in rig.sink.calls
    assert _analysis_threads() == []


def _assert_one_frame_held(source: _Streams) -> None:
    for tag, held in source.held.items():
        assert held <= 1, f"{tag} held {held} decoded frames while it asked for the next"


def test_each_thread_holds_one_decoded_frame(tmp_path: Path) -> None:
    rig, source, _ = _rig(tmp_path)
    assert rig.run(rig.request()).ok
    assert len(source.held) == 2
    _assert_one_frame_held(source)


def test_planted_second_held_frame_fails_by_name(tmp_path: Path) -> None:
    rig, source, _ = _rig(tmp_path)
    real = source._stream

    def prefetching(tag: str) -> Iterator[Frame]:
        stream = real(tag)
        ahead = next(stream, None)
        for frame in stream:  # a one-frame read-ahead: an unbounded queue of length one
            current, ahead = ahead, frame
            yield current  # type: ignore[misc]
        if ahead is not None:
            yield ahead

    source._stream = prefetching  # type: ignore[method-assign]
    assert rig.run(rig.request()).ok
    with pytest.raises(AssertionError, match="held 2 decoded frames"):
        _assert_one_frame_held(source)


def _assert_rendered_in_decode_order(sink: FakeSink, frames: list[Frame]) -> None:
    assert [f.pts_ticks for f in sink.frames] == [f.pts_ticks for f in frames], (
        "frames rendered out of decode order"
    )


def test_planted_out_of_order_render_fails_by_name(tmp_path: Path) -> None:
    rig, source, _ = _rig(tmp_path)
    real = source._stream

    def swapped(tag: str) -> Iterator[Frame]:
        frames = list(real(tag))
        if tag != "stream-0":  # the export's stream
            frames[100], frames[101] = frames[101], frames[100]
        return iter(frames)

    source._stream = swapped  # type: ignore[method-assign]
    rig.run(rig.request())
    with pytest.raises(AssertionError, match="out of decode order"):
        _assert_rendered_in_decode_order(rig.sink, rig.frames)


# --- one writer, the cache entry -----------------------------------------------------------------


def test_only_the_analysis_thread_writes_the_cache_and_marks_it_complete_last(
    tmp_path: Path,
) -> None:
    rig, _, cache = _rig(tmp_path)
    assert rig.run(rig.request()).ok
    assert {thread for thread, _ in cache.writes} == {"export-analysis"}
    assert [call for _, call in cache.writes].count("store_proxy") == FRAMES
    assert cache.writes[-1][1] == "mark_complete"
    entry = cache.lookup(KEY)
    assert entry is not None and entry.complete


def test_a_warm_cache_entry_streams_the_stages_from_the_stored_proxies(tmp_path: Path) -> None:
    rig, source, _ = _rig(tmp_path)
    assert rig.run(rig.request()).ok
    first = dict(rig.method.renders)  # type: ignore[attr-defined]
    rig.method.renders.clear()  # type: ignore[attr-defined]
    source.events.clear()
    exported_at_analyze: list[int] = []

    def hook(stage: str) -> None:
        exported_at_analyze.append(len(source.events))
        time.sleep(0.002)

    rig.method.hook = hook
    result = rig.run(rig.request())
    assert result.ok, result.failure
    assert [tag for tag, _ in source.events] == ["stream-2"] * FRAMES  # no decode pass
    assert max(exported_at_analyze) > 0, "the export started only after the warm analysis"
    _assert_whole_clip_records(rig.method.renders, first)  # type: ignore[attr-defined]


# --- cancel at each phase -------------------------------------------------------------------------


def _assert_cancelled_and_clean(rig: Rig, result: JobResult, cache: _Cache) -> None:
    assert result.failure is CANCELLED and result.outputs == ()
    assert sorted(p.name for p in rig.folder.iterdir()) == ["clip.mp4", "shot.png"]
    entry = cache.lookup(KEY)
    assert entry is None or not entry.complete, "a cancelled analysis marked the cache complete"
    assert _analysis_threads() == [], "the analysis thread outlived the job"
    if rig.sinks and "open" in rig.sink.calls:
        assert "abort" in rig.sink.calls and "close" not in rig.sink.calls


def test_cancel_before_start(tmp_path: Path) -> None:
    rig, source, cache = _rig(tmp_path)
    progress = StubProgress()
    progress.cancel()
    _assert_cancelled_and_clean(rig, rig.run(rig.request(), progress), cache)
    assert source.events == []


def test_cancel_during_the_lead(tmp_path: Path) -> None:
    rig, source, cache = _rig(tmp_path)
    progress = StubProgress()

    def hook(stage: str) -> None:
        time.sleep(0.002)
        if len(source.events) >= 30:  # inside the 61-frame lead
            progress.cancel()

    rig.method.hook = hook
    result = rig.run(rig.request(), progress)
    _assert_cancelled_and_clean(rig, result, cache)
    assert rig.sinks == [] or "open" not in rig.sink.calls  # the lead never ended


def test_cancel_mid_encode_with_a_write_blocked_until_abort(tmp_path: Path) -> None:
    rig, _, cache = _rig(tmp_path)
    progress = StubProgress()

    def blocking() -> FakeSink:
        sink = FakeSink()
        sink.block_at = 2
        return sink

    rig.next_sink = blocking
    box: dict[str, Any] = {}
    job = threading.Thread(target=lambda: box.update(r=rig.run(rig.request(), progress)))
    job.start()
    deadline = time.monotonic() + 20
    while not rig.sinks or not rig.sink.blocked.is_set():
        assert time.monotonic() < deadline, "the write never blocked"
        time.sleep(0.01)
    assert _analysis_threads(), "the analysis had already ended: nothing overlapped"
    start = time.monotonic()
    progress.cancel()
    job.join(15)
    assert time.monotonic() - start < 3.0
    _assert_cancelled_and_clean(rig, box["r"], cache)


def test_cancel_immediately_before_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rig, _, cache = _rig(tmp_path)
    progress = StubProgress()
    real_close = FakeSink.close

    def close_then_cancel(self: FakeSink) -> Any:
        report = real_close(self)
        progress.cancel()
        return report

    monkeypatch.setattr(FakeSink, "close", close_then_cancel)
    result = rig.run(rig.request(), progress)
    assert result.failure is CANCELLED and result.outputs == ()
    assert sorted(p.name for p in rig.folder.iterdir()) == ["clip.mp4", "shot.png"]
    assert _analysis_threads() == []
    calls = rig.sink.calls
    assert set(calls[calls.index("close") + 1 :]) == {"abort"}, calls
    entry = cache.lookup(KEY)
    assert entry is not None and entry.complete  # the analysis had completed before close


def test_no_analysis_thread_is_alive_at_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig, _, _ = _rig(tmp_path)
    seen: list[list[str]] = []
    real = SafeWrite.commit

    def commit(self: SafeWrite) -> Path:
        seen.append([t.name for t in _analysis_threads()])
        return real(self)

    monkeypatch.setattr(SafeWrite, "commit", commit)
    assert rig.run(rig.request()).ok
    assert seen == [[]]


# --- a failure in either half --------------------------------------------------------------------


def test_an_analysis_failure_mid_export_keeps_its_own_text(tmp_path: Path) -> None:
    rig, _, cache = _rig(tmp_path)
    exported = [0]
    real_render = rig.method.render

    def render(image: Any, params: Any, statistics: Any) -> Any:
        exported[0] += 1
        return real_render(image, params, statistics)

    def hook(stage: str) -> None:
        time.sleep(0.002)
        if exported[0] >= 5:
            raise ValueError("ORIGINAL analysis failure mid-export")

    rig.method.render = render  # type: ignore[method-assign]
    rig.method.hook = hook
    result = rig.run(rig.request())
    assert result.failure == (
        "clip.mp4: analysis failed: ValueError: ORIGINAL analysis failure mid-export"
    ), result.failure
    assert exported[0] >= 5 and "abort" in rig.sink.calls and "close" not in rig.sink.calls
    entry = cache.lookup(KEY)
    assert entry is None or not entry.complete
    assert _analysis_threads() == []
    assert sorted(p.name for p in rig.folder.iterdir()) == ["clip.mp4", "shot.png"]


def test_an_export_failure_stops_and_joins_the_analysis(tmp_path: Path) -> None:
    rig, source, cache = _rig(tmp_path)
    real_render = rig.method.render
    count = [0]

    def render(image: Any, params: Any, statistics: Any) -> Any:
        count[0] += 1
        if count[0] == 3:
            raise RuntimeError("ORIGINAL render failure")
        return real_render(image, params, statistics)

    rig.method.render = render  # type: ignore[method-assign]
    result = rig.run(rig.request())
    assert result.failure == "clip.mp4: RuntimeError: ORIGINAL render failure"
    assert _analysis_threads() == []
    entry = cache.lookup(KEY)
    assert entry is None or not entry.complete, "the stopped analysis marked the cache complete"
    analysis = [pts for tag, pts in source.events if tag == "stream-0"]
    assert len(analysis) < FRAMES, "the analysis ran on to the end after the export failed"


# --- the CPU path (D107) --------------------------------------------------------------------------


def test_the_cpu_path_overlaps_on_the_numpy_backend(tmp_path: Path) -> None:
    rig, source, _ = _rig(tmp_path)
    result = rig.run(rig.request(force_cpu=True))
    assert result.ok, result.failure
    assert result.device == "CPU: forced"
    _assert_overlapped(source)
    _assert_whole_clip_records(rig.method.renders, _whole_clip_records(rig))  # type: ignore[attr-defined]
