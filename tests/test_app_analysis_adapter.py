"""WP4.3 task 4: the GUI's analysis adapter over WP3.11's REAL engine (WP3.18 mapping, Q18, S2).

The adapter (``clearwater.app.analysis_adapter``) runs ``AnalysisEngine`` on a real
``DiskProxyCache`` behind the application's cache handle, with a list frame source and a
two-stage test method: the engine is built in the first run, on the worker; the kept job of a
``retarget`` that got one back runs first at the next run and ends under the latest parameters
(erratum 1, and WP3.18 B pass 1 #1's A-B-A burst); ``statistics`` is None until a whole run
completed under the latest parameters, also against a run that starts mid-read (DR-51 (a));
``pts()`` never calls the cache; at most one run is in flight; each run selects its backend at
its start and a changed device rebuilds the engine over the same cache, reusing the complete
entry (S2, V17); the engine gets the export's ``expected_frames`` (Q18); DR-62's clip lock is
taken around the engine's job, cancellably.
"""

from __future__ import annotations

import gc
import threading
import weakref
from collections.abc import Iterator
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.analysis import AnalysisEngine
from clearwater.app import composition
from clearwater.app.activity import WAITING_TEXT, ClipLocks
from clearwater.app.analysis_adapter import EngineClipAnalysis, make_analysis_factory
from clearwater.app.composition import DeferredProxyCache
from clearwater.config import new_parameter_set
from clearwater.interfaces import Fault, Frame, ProbeResult, Settings
from clearwater.interfaces.stubs import StubArrayBackend, StubProgress
from clearwater.jobs import expected_frames
from clearwater.jobs import export as export_module
from test_analysis_support import GrayWorld, ListSource, make_probe, synthetic_frames

FRAMES = 24


class GpuStub(StubArrayBackend):
    """A host-array backend that calls itself a GPU, so the adapter treats it as one (S2)."""

    device = "cuda:0"


GPU = GpuStub()
CPU = StubArrayBackend()


class Rig:
    """One clip, one opened cache, one adapter and the knobs the tests turn."""

    def __init__(self, tmp_path: Path, frames: int = FRAMES) -> None:
        self.path = tmp_path / "clip.mp4"
        self.path.write_bytes(b"not decoded: the list source serves the frames")
        self.frames: list[Frame] = synthetic_frames(frames)
        self.probe = replace(make_probe(nb_frames=frames), path=self.path)
        self.cache = composition.proxy_cache_opener(tmp_path / "cache")
        assert self.cache.open(10**9) is None
        self.method = GrayWorld()
        self.settings = Settings(force_cpu=True)
        self.locks = ClipLocks()
        self.sources: list[ListSource] = []
        self.engines: list[AnalysisEngine] = []
        self.built_with: list[dict[str, Any]] = []
        self.hold: threading.Event | None = None
        self.held = threading.Event()

    def select(self, settings: Settings, height: int, width: int, method_id: str) -> Any:
        return (CPU, "CPU: forced") if settings.force_cpu else (GPU, "GPU")

    def source_for(self, device: Any) -> ListSource:
        source = ListSource(self.frames, self.probe)
        self.sources.append(source)
        return source

    def engine_factory(self, **kwargs: Any) -> AnalysisEngine:
        self.built_with.append(kwargs)
        engine = HeldEngine(self, **kwargs)
        self.engines.append(engine)
        return engine

    def adapter(self) -> EngineClipAnalysis:
        return EngineClipAnalysis(
            path=self.path,
            probe=self.probe,
            method=self.method,
            cache=self.cache,
            select_backend=self.select,
            settings=lambda: self.settings,
            locks=self.locks,
            engine_factory=self.engine_factory,
            source_for=self.source_for,
        )


class HeldEngine(AnalysisEngine):
    """The real engine; with ``rig.hold`` set, each job waits after it ran, before it returns."""

    def __init__(self, rig: Rig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._rig = rig

    def _once(self) -> Any:
        job = super()._once()
        rig = self._rig

        def held(progress: Any) -> Any:
            result = job(progress)
            if rig.hold is not None:
                rig.held.set()
                assert rig.hold.wait(10)
            return result

        return held


def same_record(a: Any, b: Any) -> bool:
    """Stage-by-stage equality of two statistics records (their values may be arrays)."""
    if a is None or b is None or list(a) != list(b):
        return False
    return all(
        list(a[stage]) == list(b[stage])
        and all(np.array_equal(a[stage][k], b[stage][k]) for k in a[stage])
        for stage in a
    )


def params(**values: float) -> Any:
    return new_parameter_set("grayworld", values)


def run_in_thread(adapter: EngineClipAnalysis, parameters: Any, progress: Any = None) -> Any:
    box: dict[str, Any] = {}
    progress = progress or StubProgress()

    def body() -> None:
        try:
            adapter.run(parameters, progress)
        except Exception as exc:
            box["error"] = exc

    thread = threading.Thread(target=body, daemon=True)
    thread.start()
    return thread, box


# Q18: one copy of the frame-count rule.


@pytest.mark.usefixtures("ffmpeg_tools")
def test_the_public_frame_count_is_the_exports_rule(sample: Any) -> None:
    clean = make_probe(nb_frames=10)
    tail = replace(clean, faults=(Fault("unreadable_tail", "warn", "tail"),))
    from clearwater.io.video import probe as probe_file

    truncated = probe_file(sample("vid-truncated"))
    assert {f.kind for f in truncated.faults} >= {"truncated"}
    for probe in (clean, tail, truncated):
        assert expected_frames(probe) == export_module._expected_frames(probe)
    assert [expected_frames(p) for p in (clean, tail, truncated)] == [10, None, 24]


@pytest.mark.parametrize("kind", ["clean", "unreadable_tail", "truncated"])
def test_the_adapter_gives_the_engine_the_exports_frame_count(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    rig = Rig(tmp_path)
    if kind != "clean":
        rig.probe = replace(rig.probe, faults=(Fault(kind, "warn", kind),))
    counted: list[ProbeResult] = []

    def count(probe: ProbeResult) -> int | None:
        counted.append(probe)
        return 7 if kind == "truncated" else expected_frames(probe)

    monkeypatch.setattr("clearwater.app.analysis_adapter.expected_frames", count)
    adapter = rig.adapter()
    adapter.run(params(), StubProgress())
    assert counted == [rig.probe]
    expected = {"clean": FRAMES, "unreadable_tail": None, "truncated": 7}[kind]
    assert rig.built_with[0]["expected_frames"] == expected


# The mapping: build lazily, statistics, pts, proxy.


def test_the_factory_builds_only_and_the_first_run_completes(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    adapter = rig.adapter()
    assert rig.engines == [] and adapter.pts() == () and adapter.statistics(7) is None
    progress = StubProgress()
    adapter.run(params(strength=0.5), progress)
    engine = rig.engines[0]
    assert engine.is_complete() and engine.parameters["strength"] == 0.5
    ticks = adapter.pts()
    assert ticks == tuple(f.pts_ticks for f in rig.frames)
    assert same_record(adapter.statistics(ticks[3]), engine.smoothed_record(ticks[3]))
    assert adapter.proxy(ticks[0]).dtype.name == "uint8"
    with pytest.raises(KeyError):
        adapter.proxy(123456789)
    assert adapter.statistics(123456789) is None
    assert rig.built_with[0]["cache"] is rig.cache  # the ONE cache instance
    assert rig.built_with[0]["hw_decode"] is False and rig.built_with[0]["backend"] is CPU


def test_pts_never_calls_the_cache(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    rig = Rig(tmp_path)
    adapter = rig.adapter()
    adapter.run(params(), StubProgress())
    calls: list[str] = []
    monkeypatch.setattr(DeferredProxyCache, "_target", lambda self: calls.append("x"))
    assert len(adapter.pts()) == FRAMES and calls == []


def test_a_second_run_in_flight_is_refused(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.hold = threading.Event()
    adapter = rig.adapter()
    thread, _ = run_in_thread(adapter, params())
    assert rig.held.wait(10)
    with pytest.raises(RuntimeError, match="already in flight"):
        adapter.run(params(), StubProgress())
    rig.hold.set()
    thread.join(10)


# retarget and the kept job (WP3.18 five-point contract (5); erratum 1).


def test_a_retarget_while_the_engine_runs_is_absorbed(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    progress = StubProgress()
    source_pause = threading.Event()  # the source pauses mid-decode: the engine is running

    def source_for(device: Any) -> ListSource:
        source = ListSource(rig.frames, rig.probe)
        source.pause_after = 5
        source.resume = source_pause
        rig.sources.append(source)
        return source

    rig.source_for = source_for  # type: ignore[method-assign]
    adapter = rig.adapter()
    thread, box = run_in_thread(adapter, params(strength=0.2), progress)
    for _ in range(200):
        if rig.sources and rig.sources[0].paused.is_set():
            break
        thread.join(0.05)
    assert rig.sources[0].paused.is_set()
    assert adapter.retarget(params(strength=0.9)) is True
    source_pause.set()
    thread.join(10)
    assert box == {}
    engine = rig.engines[0]
    assert engine.parameters["strength"] == 0.9 and engine.is_complete()
    assert adapter.statistics(rig.frames[0].pts_ticks) is not None


def test_a_job_returned_to_retarget_is_kept_and_ends_under_the_latest_parameters(
    tmp_path: Path,
) -> None:
    """The A-B-A burst: B's kept job runs first at the next run, which offers A, and ends at A."""
    rig = Rig(tmp_path)
    adapter = rig.adapter()
    adapter.run(params(strength=0.2), StubProgress())  # A, complete
    adapter.run(params(strength=0.2), StubProgress())  # unchanged: complete at once, no job
    assert adapter.statistics(rig.frames[0].pts_ticks) is not None
    rig.hold = threading.Event()
    thread, _ = run_in_thread(adapter, params(strength=0.4))  # a recompute job, held at its end
    assert rig.held.wait(10)
    engine = rig.engines[0]
    assert engine.is_complete() and engine.parameters["strength"] == 0.4
    assert adapter.retarget(params(strength=0.7)) is False  # B: the engine returned a job
    rig.hold.set()
    thread.join(10)
    assert adapter.statistics(rig.frames[0].pts_ticks) is None  # holds a kept job: not complete
    rig.hold = None
    adapter.run(params(strength=0.2), StubProgress())  # the follow-up offers the latest, A
    assert engine.parameters["strength"] == 0.2 and engine.is_complete()
    assert len(rig.engines) == 1  # the kept job ran on the same engine; no other was built
    pts = rig.frames[0].pts_ticks
    assert same_record(adapter.statistics(pts), engine.smoothed_record(pts))


def test_retarget_after_the_run_returned_is_false_and_clears_completion(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    adapter = rig.adapter()
    adapter.run(params(), StubProgress())
    assert adapter.statistics(rig.frames[0].pts_ticks) is not None
    assert adapter.retarget(params(strength=0.3)) is False
    assert adapter.statistics(rig.frames[0].pts_ticks) is None


def test_a_retarget_after_the_job_returned_is_not_undone_at_publication(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """R1-7: a retarget between the job's return and the run's end leaves no statistics."""
    rig = Rig(tmp_path)
    parked, resume = threading.Event(), threading.Event()
    real_release = rig.locks.release

    def release(key: Any) -> None:  # the run's last step before it publishes
        parked.set()
        assert resume.wait(10)
        real_release(key)

    monkeypatch.setattr(rig.locks, "release", release)
    adapter = rig.adapter()
    thread, box = run_in_thread(adapter, params())
    assert parked.wait(30)
    assert adapter.retarget(params(strength=0.3)) is False  # the job has returned
    resume.set()
    thread.join(30)
    assert box == {} and not thread.is_alive()
    assert adapter.statistics(rig.frames[0].pts_ticks) is None


def test_the_factory_keeps_no_adapter_without_on_built(tmp_path: Path) -> None:
    """R1-8: the factory holds no adapter it built; the caller decides what it keeps."""
    rig = Rig(tmp_path)

    class Source:
        path = rig.path
        probe = rig.probe

    class Engines:
        cache = rig.cache
        select_backend = staticmethod(rig.select)

    factory = make_analysis_factory(lambda: rig.settings, locks=rig.locks)
    ref = weakref.ref(factory(Source(), rig.method, Engines()))
    gc.collect()
    assert ref() is None


def test_a_retarget_before_the_engine_job_starts_is_absorbed(tmp_path: Path) -> None:
    """While the run waits for the clip's lock the change is taken: the run starts with it."""
    rig = Rig(tmp_path)
    adapter = rig.adapter()
    key = rig.cache.key_for(rig.path)
    rig.locks.acquire(key, StubProgress())
    progress = StubProgress()
    thread, box = run_in_thread(adapter, params(strength=0.1), progress)
    while (0, None, WAITING_TEXT) not in progress.reports:
        thread.join(0.02)
    assert adapter.retarget(params(strength=0.8)) is True
    rig.locks.release(key)
    thread.join(10)
    assert box == {} and rig.engines[0].parameters["strength"] == 0.8


def test_a_cancel_while_waiting_for_the_clip_returns_without_running(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    adapter = rig.adapter()
    key = rig.cache.key_for(rig.path)
    rig.locks.acquire(key, StubProgress())
    progress = StubProgress()
    thread, box = run_in_thread(adapter, params(), progress)
    while (0, None, WAITING_TEXT) not in progress.reports:
        thread.join(0.02)
    progress.cancel()
    thread.join(10)
    assert box == {} and rig.engines == []
    assert rig.locks.held(key)  # still the other activity's
    rig.locks.release(key)


# DR-51 (a): statistics against a run that starts mid-read.


def test_statistics_read_while_a_new_run_starts_is_none(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    adapter = rig.adapter()
    adapter.run(params(), StubProgress())
    engine = rig.engines[0]
    pts = rig.frames[2].pts_ticks
    real = engine.smoothed_record
    started = threading.Event()
    rig.hold = threading.Event()

    def racing(pts_ticks: int, **kwargs: Any) -> Any:
        record = real(pts_ticks, **kwargs)
        thread, _ = run_in_thread(adapter, params(strength=0.6))  # a new run starts mid-read
        assert rig.held.wait(10)
        started.set()
        racing.thread = thread  # type: ignore[attr-defined]
        return record

    engine.smoothed_record = racing  # type: ignore[method-assign]
    assert adapter.statistics(pts) is None
    assert started.is_set()
    rig.hold.set()
    racing.thread.join(10)  # type: ignore[attr-defined]


# S2: the selection at each run's start; a changed device rebuilds over the same cache.


def test_force_cpu_between_two_runs_rebuilds_the_engine_and_reuses_the_entry(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path)
    rig.settings = Settings(force_cpu=False)
    adapter = rig.adapter()
    adapter.run(params(), StubProgress())
    assert rig.sources[0].yielded == FRAMES  # the decode pass ran once, on the "GPU"
    assert rig.built_with[0]["backend"] is GPU and rig.built_with[0]["hw_decode"] is True
    rig.settings = Settings(force_cpu=True)
    adapter.run(params(strength=0.3), StubProgress())
    assert adapter.devices == ["GPU", "CPU: forced"]
    assert len(rig.engines) == 2 and rig.built_with[1]["backend"] is CPU
    assert rig.built_with[1]["cache"] is rig.cache
    assert rig.sources[1].yielded == 0  # V17: the complete entry is reused, no decode pass
    assert rig.engines[1].is_complete()
    assert adapter.statistics(rig.frames[0].pts_ticks) is not None


def test_an_in_flight_run_keeps_its_backend(tmp_path: Path) -> None:
    """A force-CPU change during a run applies from the next run (absorbed, never cancelled)."""
    rig = Rig(tmp_path)
    rig.settings = Settings(force_cpu=False)
    rig.hold = threading.Event()
    adapter = rig.adapter()
    thread, _ = run_in_thread(adapter, params())
    assert rig.held.wait(10)
    rig.settings = Settings(force_cpu=True)
    rig.hold.set()
    thread.join(10)
    assert len(rig.engines) == 1 and rig.built_with[0]["backend"] is GPU


# DR-45 (a): every stream is iterated and closed by one thread.


class ThreadSource(ListSource):
    """A list source recording the threads that iterate and close each stream."""

    def __init__(self, frames: Any, probe: ProbeResult) -> None:
        super().__init__(frames, probe)
        self.threads: list[tuple[str, threading.Thread]] = []

    def frames(self, probe: ProbeResult, **kwargs: Any) -> Iterator[Frame]:
        def stream() -> Iterator[Frame]:
            try:
                for frame in super(ThreadSource, self).frames(probe, **kwargs):
                    self.threads.append(("next", threading.current_thread()))
                    yield frame
            finally:
                self.threads.append(("close", threading.current_thread()))

        return stream()


def test_the_decode_stream_is_iterated_and_closed_by_one_thread(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    sources: list[ThreadSource] = []

    def source_for(device: Any) -> ThreadSource:
        source = ThreadSource(rig.frames, rig.probe)
        sources.append(source)
        return source

    rig.source_for = source_for  # type: ignore[method-assign]
    adapter = rig.adapter()
    thread, box = run_in_thread(adapter, params())
    thread.join(10)
    assert box == {}
    seen = {t for _, t in sources[0].threads}
    assert seen == {thread} and sources[0].threads[-1][0] == "close"


# The factory (main thread; builds only).


def test_the_factory_reads_live_settings_and_needs_the_applications_cache(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path)
    live = {"settings": Settings(force_cpu=True)}

    class Source:
        path = rig.path
        probe = rig.probe

    class Engines:
        cache = rig.cache
        select_backend = staticmethod(rig.select)

    built: list[EngineClipAnalysis] = []
    factory = make_analysis_factory(
        lambda: live["settings"],
        locks=rig.locks,
        engine_factory=rig.engine_factory,
        source_for=rig.source_for,
        on_built=built.append,
    )
    adapter = factory(Source(), rig.method, Engines())
    assert built == [adapter] and rig.engines == []
    live["settings"] = Settings(force_cpu=False)
    adapter.run(params(), StubProgress())
    assert adapter.devices == ["GPU"]  # the settings in force when the run started

    class Stubbed(Engines):
        cache = object()

    with pytest.raises(TypeError, match="application's cache"):
        factory(Source(), rig.method, Stubbed())

    class Photo(Source):
        probe = None

    with pytest.raises(ValueError, match="video"):
        factory(Photo(), rig.method, Engines())


def test_the_time_base_of_the_fixture_probe_is_cfr() -> None:
    assert make_probe().video.time_base == Fraction(1, 30000)
