"""WP4.2 task 6: the video path end to end through the composition root.

DR-45 (b) (question 7, CHARC ``881cc956f1335e7e`` B): a decode that ends cleanly after a strict
prefix leaves no complete cache entry: the export job gives the analysis the frames a whole
decode yields (the probe's count, or the readable count of a ``truncated`` source from one packet
listing; none for ``unreadable_tail``), and a shorter pass fails readably with the entry left
incomplete. DR-47 (a): an analysis job callable runs once. V4 on one sample per backend through
``tools/video_fidelity.py``'s comparison; D86's warning; the refused samples; V9 at neutral
parameters (AD-11, pre-encode); V17 (a reopen skips the decode pass; another cache format version
re-analyses); each file its own clip (spec section 5.5); cancel and failure on the composed
engine. Every bit-identity assertion compares bit patterns (dtype, shape and bytes; DR-79 (c)).
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.analysis import AnalysisEngine
from clearwater.app import composition
from clearwater.config import new_parameter_set
from clearwater.interfaces import ArrayBackend, Fault, Frame, ProbeResult, Settings
from clearwater.interfaces.stubs import StubArrayBackend, StubProgress
from clearwater.jobs import export as export_module
from clearwater.jobs.export_seam import ExportRequest
from test_analysis_support import (
    KEY,
    CountingCache,
    GrayWorld,
    ListSource,
    make_engine,
    make_probe,
    run,
    synthetic_frames,
)

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

Sample = Callable[[str], Path]
CLIP = "vid-hevc8-bt709-full"


def same_bits(a: Any, b: Any) -> bool:
    """Bit-pattern equality: dtype, shape and bytes (``+0.0`` and ``-0.0`` differ; DR-79 (c))."""
    a, b = np.asarray(a), np.asarray(b)
    return a.dtype == b.dtype and a.shape == b.shape and a.tobytes() == b.tobytes()


def test_same_bits_tells_signed_zeros_apart() -> None:
    zero = np.zeros(3, dtype=np.float32)
    assert np.array_equal(zero, -zero) and not same_bits(zero, -zero)
    assert same_bits(zero, zero.copy()) and not same_bits(zero, zero.astype(np.float64))


def _settings(out: Path, **values: Any) -> Settings:
    values.setdefault("force_cpu", True)
    values.setdefault("video_encoder", "libx265")
    return Settings(output_folder=out, **values)


def _request(source: Path, out: Path, method: str = "c3", **values: Any) -> ExportRequest:
    return ExportRequest(source, "video", new_parameter_set(method, {}), _settings(out, **values))


def _entry_states(cache: Path) -> list[bool]:
    """Whether each entry folder in ``cache`` is marked complete (its marker file present)."""
    from clearwater.cache import DiskProxyCache

    opened = DiskProxyCache(cache)
    states = []
    for folder in sorted(p for p in cache.iterdir() if p.is_dir()):
        from clearwater.cache import parse_entry_name

        key = parse_entry_name(folder.name)
        assert key is not None
        entry = opened.lookup(key)
        states.append(entry is not None and entry.complete)
    opened.close()
    return states


# --- DR-45 (b): a strict prefix leaves no complete entry ------------------------------------------


class PrefixSource:
    """A frame source that yields only the first ``keep`` frames of the real decode, then ends."""

    def __init__(self, inner: Any, keep: int) -> None:
        self.inner = inner
        self.keep = keep

    def probe(self, path: Path) -> ProbeResult:
        return self.inner.probe(path)

    def frames(self, probe: ProbeResult, *, hw_decode: bool, **kwargs: Any) -> Iterator[Frame]:
        stream = self.inner.frames(probe, hw_decode=hw_decode, **kwargs)
        try:
            for index, frame in enumerate(stream):
                if index >= self.keep:
                    return
                yield frame
        finally:
            stream.close()


def test_a_strict_prefix_decode_fails_the_job_and_leaves_the_entry_incomplete(
    sample: Sample, tmp_path: Path
) -> None:
    out, cache = tmp_path / "out", tmp_path / "cache"
    out.mkdir()

    def source_for(device: ArrayBackend | None) -> Any:
        return PrefixSource(composition.video_source(device), 30)  # of 45

    exports = composition.export_jobs(cache_folder=cache, source_for=source_for)
    result = exports.job(_request(sample(CLIP), out))(StubProgress())
    assert not result.ok and result.outputs == ()
    assert result.failure is not None and "ended after 30 of the clip's 45 frames" in (
        result.failure
    )
    assert list(out.iterdir()) == []
    assert _entry_states(cache) == [False]  # stored, never marked complete


def _counted_engine(
    frames: list[Frame], nb_frames: int, expected: int | None
) -> tuple[AnalysisEngine, CountingCache]:
    method = GrayWorld()
    probe = make_probe(nb_frames=nb_frames)
    cache = CountingCache()
    engine = AnalysisEngine(
        method=method,
        backend=StubArrayBackend(),
        cache=cache,
        key=KEY,
        source=ListSource(frames, probe),
        probe=probe,
        params={p.name: p.default for p in method.parameters},
        expected_frames=expected,
    )
    return engine, cache


def test_the_analysis_checks_the_expected_count_only_when_given() -> None:
    frames = synthetic_frames(12)
    short, cache = _counted_engine(frames[:8], 12, None)
    assert run(short).ok and cache.marks == 1  # no expectation: the engine's own behaviour

    engine, cache = _counted_engine(frames[:8], 12, 12)
    result = run(engine)
    assert not result.ok and cache.marks == 0
    assert result.failure == (
        "ValueError: the frame source ended after 8 of the clip's 12 frames; the cache entry is "
        "left incomplete"
    )
    assert cache.lookup(KEY) is not None and not cache.lookup(KEY).complete
    whole, cache = _counted_engine(frames, 12, 12)
    assert run(whole).ok and cache.marks == 1


def test_the_export_job_expects_the_probe_count_or_the_readable_count(
    sample: Sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The three cases CHARC B names: normal, truncated with its listing, and none."""
    expected: list[int | None] = []
    real = AnalysisEngine.__init__

    def recording(self: AnalysisEngine, **kwargs: Any) -> None:
        expected.append(kwargs.get("expected_frames"))
        real(self, **kwargs)

    monkeypatch.setattr(AnalysisEngine, "__init__", recording)
    exports = composition.export_jobs(cache_folder=tmp_path / "cache")
    (tmp_path / "out").mkdir()
    normal = exports.job(_request(sample(CLIP), tmp_path / "out"))(StubProgress())
    truncated = exports.job(_request(sample("vid-truncated"), tmp_path / "out"))(StubProgress())
    assert normal.ok and truncated.ok, (normal.failure, truncated.failure)
    assert any("cut short" in w for w in truncated.warnings)  # D86
    assert expected == [45, 24]  # the probe's nb_frames; the listing's readable count


def test_an_unreadable_tail_source_is_not_given_a_count() -> None:
    probe = make_probe(nb_frames=10)
    assert export_module._expected_frames(probe) == 10
    tail = replace(probe, faults=(Fault("unreadable_tail", "warn", "tail"),))
    assert export_module._expected_frames(tail) is None  # knowable only by decoding (verify)
    missing = replace(probe, faults=(Fault("missing_tags", "warn", "assumed"),))
    assert export_module._expected_frames(missing) == 10
    assert export_module._expected_frames(make_probe(nb_frames=None)) is None


# --- DR-47 (a): a job callable runs once ---------------------------------------------------------


def test_an_analysis_job_callable_runs_once() -> None:
    engine, source, cache = make_engine(GrayWorld(), synthetic_frames(6))
    job = engine.analysis_job()
    assert job(StubProgress()).ok
    iterations, marks = source.iterations, cache.marks
    again = job(StubProgress())
    assert (again.ok, again.failure) == (False, "this analysis job has already run")
    assert (source.iterations, cache.marks) == (iterations, marks)  # nothing touched
    assert engine.is_complete()
