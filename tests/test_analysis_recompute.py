"""Recompute after a parameter change (7.3, AD-7, question 8): stages, closed form, reach."""

from __future__ import annotations

from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

import clearwater.analysis.engine as engine_module
from clearwater.analysis import CANCELLED, reach, schema_hash
from clearwater.interfaces import CacheKey
from clearwater.interfaces.stubs import StubProgress
from test_analysis_support import (
    KEY,
    Compensated,
    CountingCache,
    GrayWorld,
    make_engine,
    run,
    synthetic_frames,
)


class LoggingCache(CountingCache):
    """Logs the pts of every proxy read, in order."""

    def __init__(self) -> None:
        super().__init__()
        self.log: list[int] = []

    def proxy(self, key: CacheKey, pts_ticks: int) -> NDArray[np.uint8]:
        self.log.append(pts_ticks)
        return super().proxy(key, pts_ticks)


class Hook(StubProgress):
    """Calls ``on_report(message)`` at every report."""

    def __init__(self, on_report: Any) -> None:
        super().__init__()
        self.on_report = on_report

    def report(self, done: int, total: int | None, message: str) -> None:
        super().report(done, total, message)
        self.on_report(message)


def _records(engine: Any) -> dict[int, dict[str, dict[str, NDArray[np.float64]]]]:
    return {pts: engine.smoothed_record(pts) for pts in engine.store.axis()}


def _same(first: Any, second: Any) -> bool:
    return all(
        np.array_equal(first[pts][stage][name], second[pts][stage][name])
        for pts in first
        for stage in first[pts]
        for name in first[pts][stage]
    )


def test_a_stage_two_parameter_leaves_stage_one_untouched() -> None:
    """``gamma`` (fusion only): white balance is neither re-measured nor changed."""
    frames = synthetic_frames(80)
    method = GrayWorld()
    engine, _, _ = make_engine(method, frames)
    assert run(engine).ok
    before = {p: engine.store.raw(p, "white_balance") for p in engine.store.axis()}
    count = method.count("white_balance")
    job = engine.set_parameters({**engine.parameters, "gamma": 2.0}, frames[40].pts_ticks)
    assert job is not None and engine.state().phase == "running"
    assert job(StubProgress()).ok and engine.is_complete()
    assert method.count("white_balance") == count
    for pts, record in before.items():
        assert np.array_equal(engine.store.raw(pts, "white_balance")["gains"], record["gains"])
    fresh, _, _ = make_engine(GrayWorld(), frames, params={"gamma": 2.0})
    assert run(fresh).ok
    assert _same(_records(engine), _records(fresh))


def test_a_closed_form_stage_never_reads_a_proxy() -> None:
    """``cap`` invalidates the closed-form ``compensation``: updated without a proxy read."""
    frames = synthetic_frames(40)
    method = Compensated()
    engine, _, cache = make_engine(method, frames, params={"cap": 0.5})
    assert run(engine).ok
    assert isinstance(cache, CountingCache)
    reads = cache.proxy_reads
    analyzed = len(method.analyzed)
    job = engine.set_parameters({**engine.parameters, "cap": 0.02}, frames[20].pts_ticks)
    assert job is not None and job(StubProgress()).ok
    new_calls = method.analyzed[analyzed:]
    assert "compensation" not in new_calls
    assert new_calls.count("white_balance") == 40
    assert cache.proxy_reads - reads == 40  # white_balance only
    alpha = np.array([engine.store.raw(p, "compensation")["alpha"] for p in engine.store.axis()])
    assert np.all(alpha <= 0.02)
    fresh, _, _ = make_engine(Compensated(), frames, params={"cap": 0.02})
    assert run(fresh).ok
    assert _same(_records(engine), _records(fresh))


def _near_run(planted: str | None, monkeypatch: pytest.MonkeyPatch) -> dict[str, Any]:
    """Recompute from stage 1 around the middle frame of a 301-frame 29.97 fps clip."""
    frames = synthetic_frames(301)
    cache = LoggingCache()
    method = GrayWorld()
    engine, _, _ = make_engine(method, frames, cache=cache)
    assert run(engine).ok
    centre = frames[150].pts_ticks
    if planted == "gaussian":  # the Gaussian's reach alone (the median's frame left out)

        def gaussian_only(ticks: Any, tb: Any, window_s: Any, kind: str, lo: int, hi: int) -> Any:
            return reach(ticks, tb, window_s, "gaussian", lo, hi)

        monkeypatch.setattr(engine_module, "reach", gaussian_only)
    elif planted == "single":  # one stage's reach for every stage (not cumulative)

        def single(ticks: Any, tb: Any, window_s: Any, kind: str, lo: int, hi: int) -> Any:
            return reach(ticks, tb, window_s, kind, 150, 150)

        monkeypatch.setattr(engine_module, "reach", single)
    seen: dict[str, Any] = {"near_record": None, "missing_before": False, "complete_during": []}

    def on_report(message: str) -> None:
        if message.startswith("recomputing near"):
            try:
                engine.smoothed_record(centre)
            except KeyError:
                seen["missing_before"] = True
        elif seen["near_record"] is None:
            seen["near_record"] = engine.smoothed_record(centre)
            seen["near_log"] = list(cache.log)
        else:
            seen["complete_during"].append(engine.is_complete())

    cache.log.clear()
    job = engine.set_parameters({**engine.parameters, "strength": 0.5}, centre)
    assert job is not None
    seen["result"] = job(Hook(on_report))
    seen["engine"], seen["frames"], seen["centre"] = engine, frames, centre
    return seen


def test_near_frames_cover_the_cumulative_reach_first(monkeypatch: pytest.MonkeyPatch) -> None:
    """AD-7 with premise P1: stage 1 over +-60 frames, stage 2 over +-30, then the rest."""
    seen = _near_run(None, monkeypatch)
    assert seen["result"].ok
    frames, engine, centre = seen["frames"], seen["engine"], seen["centre"]
    ticks = [f.pts_ticks for f in frames]
    near_log = seen["near_log"]
    assert near_log[:121] and set(near_log[:121]) == set(ticks[90:211])  # stage 1: 121 frames
    assert set(near_log[121:182]) == set(ticks[120:181])  # stage 2: 61 frames
    assert len(near_log) == 121 + 61 + 1  # captured at the first background frame's report
    assert seen["missing_before"]
    final = engine.smoothed_record(centre)
    for stage, record in final.items():
        for name, value in record.items():
            assert np.array_equal(seen["near_record"][stage][name], value)
    assert seen["complete_during"] and not any(seen["complete_during"])
    assert engine.is_complete()


@pytest.mark.parametrize("planted", ["gaussian", "single"])
def test_a_planted_short_reach_fails(planted: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """A Gaussian-only or a single-stage reach misses frames the near values read: refused."""
    seen = _near_run(planted, monkeypatch)
    assert not seen["result"].ok
    assert "not stored" in str(seen["result"].failure)


def test_complete_only_after_the_background_part() -> None:
    """``complete`` is published only when every stage is smoothed for every frame (AD-15)."""
    frames = synthetic_frames(120)
    engine, _, _ = make_engine(GrayWorld(), frames)
    assert run(engine).ok
    phases: list[str] = []
    job = engine.set_parameters({**engine.parameters, "strength": 0.3}, frames[60].pts_ticks)
    assert job is not None
    assert job(Hook(lambda message: phases.append(engine.state().phase))).ok
    assert phases and set(phases) == {"running"}
    assert engine.state().phase == "complete"


def test_the_initial_analysis_stays_running_through_the_staged_part() -> None:
    """B4, AD-15: a first analysis is ``running`` at every callback, ``complete`` only after."""
    frames = synthetic_frames(60)
    engine, _, _ = make_engine(GrayWorld(), frames)
    seen: list[tuple[str, str]] = []
    job = engine.analysis_job()
    assert job(Hook(lambda message: seen.append((engine.state().phase, message)))).ok
    assert {phase for phase, _ in seen} == {"running"}
    assert any(message == "decoding" for _, message in seen)
    assert any(message.startswith("stage fusion") for _, message in seen)  # the staged part
    assert engine.state().phase == "complete"


def test_a_change_during_a_running_job_is_absorbed() -> None:
    """Choice 5: the running job takes the change; the result is a fresh analysis's."""
    frames = synthetic_frames(90)
    method = GrayWorld()
    engine, _, _ = make_engine(method, frames)
    calls: list[Any] = []

    def change_once(stage: str) -> None:
        if stage == "fusion" and not calls:
            calls.append(engine.set_parameters({**engine.parameters, "strength": 0.4}, None))

    method.hook = change_once
    assert run(engine).ok
    assert calls == [None]
    fresh, _, _ = make_engine(GrayWorld(), frames, params={"strength": 0.4})
    assert run(fresh).ok
    assert engine.schema_hash == fresh.schema_hash
    assert _same(_records(engine), _records(fresh))


def test_a_change_during_the_decode_pass_re_measures_stage_one() -> None:
    """A change arriving in the decode pass invalidates the first stage measured there."""
    frames = synthetic_frames(30)
    engine, source, _ = make_engine(GrayWorld(), frames)
    calls: list[Any] = []

    def change(done: int, total: int | None, message: str) -> None:
        if message == "decoding" and done == 5 and not calls:
            calls.append(engine.set_parameters({**engine.parameters, "strength": 0.2}, None))

    progress = StubProgress()
    progress.report = change  # type: ignore[method-assign]
    assert run(engine, progress).ok and calls == [None]
    fresh, _, _ = make_engine(GrayWorld(), frames, params={"strength": 0.2})
    assert run(fresh).ok
    assert _same(_records(engine), _records(fresh))
    assert source.iterations == 1


def test_a_parameter_no_stage_depends_on_changes_nothing() -> None:
    """A non-shaping parameter: no job, the hash unchanged, the statistics kept."""
    engine, _, _ = make_engine(GrayWorld(), synthetic_frames(20))
    assert run(engine).ok
    before = engine.schema_hash
    assert engine.set_parameters({**engine.parameters, "unused": 0.9}, None) is None
    assert engine.schema_hash == before and engine.is_complete()
    assert engine.parameters["unused"] == 0.9


def test_an_equal_value_of_another_number_type_keeps_the_helper_hash() -> None:
    """B2: ``1.0`` -> ``1`` is no change, and the helper's hash still reads the statistics."""
    frames = synthetic_frames(20)
    method = GrayWorld()
    engine, _, _ = make_engine(method, frames, params={"strength": 1.0})
    assert run(engine).ok
    assert engine.set_parameters({**engine.parameters, "strength": 1}, None) is None
    assert engine.is_complete() and type(engine.parameters["strength"]) is int
    helper = schema_hash(method, engine.parameters, "median_gaussian", 2.0)
    assert helper == engine.schema_hash
    assert engine.smoothed_record(frames[5].pts_ticks, schema_hash=helper)


def test_a_bool_for_a_number_is_a_change_and_an_equal_number_is_not() -> None:
    """``1`` -> ``True`` recomputes under a new hash; ``1`` -> ``1.0`` stays no change."""
    frames = synthetic_frames(20)
    method = GrayWorld()
    engine, _, _ = make_engine(method, frames, params={"strength": 1})
    assert run(engine).ok
    assert engine.set_parameters({**engine.parameters, "strength": 1.0}, None) is None
    old = engine.schema_hash
    job = engine.set_parameters({**engine.parameters, "strength": True}, None)
    assert job is not None and engine.schema_hash != old
    helper = schema_hash(method, engine.parameters, "median_gaussian", 2.0)
    assert helper == engine.schema_hash
    assert job(StubProgress()).ok
    assert engine.smoothed_record(frames[5].pts_ticks, schema_hash=helper)


def test_a_change_before_any_analysis_is_used_by_the_next_job() -> None:
    """Phase none: no job is returned; the analysis then runs under the new values."""
    frames = synthetic_frames(20)
    engine, _, _ = make_engine(GrayWorld(), frames)
    assert engine.set_parameters({**engine.parameters, "gamma": 1.5}, None) is None
    assert run(engine).ok
    fresh, _, _ = make_engine(GrayWorld(), frames, params={"gamma": 1.5})
    assert run(fresh).ok
    assert _same(_records(engine), _records(fresh))


def test_cancel_during_a_recompute_unloads_and_reanalysis_does_not_redecode() -> None:
    """Choice 6: back to the unloaded state; the proxies stay cached, so no decode pass again."""
    frames = synthetic_frames(60)
    engine, source, cache = make_engine(GrayWorld(), frames)
    assert run(engine).ok
    job = engine.set_parameters({**engine.parameters, "strength": 0.5}, frames[30].pts_ticks)
    assert job is not None
    progress = StubProgress()
    progress.report = lambda done, total, message: progress.cancel()  # type: ignore[method-assign]
    result = job(progress)
    assert result.failure == CANCELLED and engine.state().phase == "cancelled"
    assert engine.store.axis() == ()
    entry = cache.lookup(KEY)
    assert entry is not None and entry.complete
    assert run(engine).ok and source.iterations == 1
    fresh, _, _ = make_engine(GrayWorld(), frames, params={"strength": 0.5})
    assert run(fresh).ok
    assert _same(_records(engine), _records(fresh))


def test_smoothed_record_checks_the_schema() -> None:
    """A render under another hash is refused; during a recompute the old records are not served."""
    from clearwater.analysis import SchemaMismatchError

    frames = synthetic_frames(20)
    engine, _, _ = make_engine(GrayWorld(), frames)
    assert run(engine).ok
    old = engine.schema_hash
    pts = frames[5].pts_ticks
    assert engine.smoothed_record(pts, schema_hash=old)
    job = engine.set_parameters({**engine.parameters, "strength": 0.1}, None)
    assert job is not None and engine.schema_hash != old
    with pytest.raises(SchemaMismatchError):
        engine.smoothed_record(pts, schema_hash=old)
    with pytest.raises(KeyError, match="being recomputed"):
        engine.smoothed_record(pts)
    assert job(StubProgress()).ok
    assert engine.smoothed_record(pts, schema_hash=engine.schema_hash)
