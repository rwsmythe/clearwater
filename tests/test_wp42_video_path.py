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

import threading
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
from clearwater.jobs.export_seam import CANCELLED, ExportRequest
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


def test_an_unreadable_tail_job_makes_no_listing_and_no_refusal(
    sample: Sample, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CHARC ``91c2c22f4b6edd18`` 1: a planted ``unreadable_tail`` probe and an early decoder end.

    The job lists no packets for its expected count and does not refuse the short decode: the
    entry is complete at the decoder's end (D86), and the sink's tail rule (none skipped up to
    the last frame written) passes the 30 frames.
    """
    from clearwater.io.video.decode import FFmpegVideoSource

    real_probe = FFmpegVideoSource.probe

    def tail_probe(self: FFmpegVideoSource, path: Path) -> ProbeResult:
        probe = real_probe(self, path)
        return replace(probe, faults=(*probe.faults, Fault("unreadable_tail", "warn", "tail")))

    listings: list[Path] = []

    def listing(path: Path) -> Any:
        listings.append(path)
        raise AssertionError("the job listed packets for an unreadable_tail clip")

    monkeypatch.setattr(FFmpegVideoSource, "probe", tail_probe)
    monkeypatch.setattr(export_module, "read_packet_table", listing)  # the job's name only
    out, cache = tmp_path / "out", tmp_path / "cache"
    out.mkdir()

    def source_for(device: ArrayBackend | None) -> Any:
        return PrefixSource(composition.video_source(device), 30)  # of 45

    exports = composition.export_jobs(cache_folder=cache, source_for=source_for)
    result = exports.job(_request(sample(CLIP), out))(StubProgress())
    assert listings == []
    assert result.ok, result.failure
    assert any("cannot be decoded" in w for w in result.warnings)  # the sink's D86 tail warning
    assert [p.name for p in out.iterdir()] == [p.name for p in result.outputs]
    assert _entry_states(cache) == [True]  # complete at the decoder's end


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


# --- DR-71: the D87 re-check takes the larger of the marginal and the entry's own rate ---------


class _Entries:
    """A cache double whose ``lookup`` answers from a list, one entry per call."""

    def __init__(self, *entries: Any) -> None:
        self.entries = list(entries)

    def lookup(self, key: Any) -> Any:
        return self.entries.pop(0)


def _entry(frames: int, size: int) -> Any:
    from clearwater.interfaces import CacheEntry

    return CacheEntry(KEY, tuple(range(frames)), (), size, False)


def _growth(before: Any, after: Any, frames: int) -> int:
    analysis = export_module._Analysis(
        None,  # type: ignore[arg-type]  # the engine is not used by the estimate
        StubArrayBackend(),
        StubProgress(),
        "clip.mp4",
        _Entries(before, after),  # type: ignore[arg-type]
        KEY,
    )
    analysis._before = analysis._cache.lookup(KEY)
    return analysis.cache_growth_bytes(frames)


def test_a_partially_extended_retry_takes_the_entrys_own_rate() -> None:
    # The entry held 100 frames in 100,000 bytes; the lead added 4 frames whose proxies took only
    # 400 bytes (100 per frame, a noisy few). 896 frames remain, at the entry's own bytes per
    # stored frame after the lead (100,400 over 104), not at the lead's 100.
    assert _growth(_entry(100, 100_000), _entry(104, 100_400), 1000) == -(-100_400 * 896 // 104)


def test_a_marginal_rate_above_the_own_rate_is_kept() -> None:
    # A fresh entry: the lead stored 10 frames in 20,000 bytes; the own rate is the same here,
    # and a growing rate above the average (larger later proxies) is not lowered.
    assert _growth(None, _entry(10, 20_000), 100) == 90 * 2000
    assert _growth(_entry(10, 10_000), _entry(20, 40_000), 100) == 80 * 3000


# --- the recording collaborators ---------------------------------------------------------------


def _host(frame: Frame) -> np.ndarray:
    """A frame's pixels on the host, as float32 (a device frame is downloaded)."""
    if frame.device == "cpu":
        return np.array(frame.pixels, dtype=np.float32, copy=True)
    from clearwater.core import backend_for

    return np.asarray(backend_for(frame.device).to_host(frame.pixels), dtype=np.float32)


class RecordingSink:
    """A real sink that keeps a host copy of every frame it receives (the pre-encode seam)."""

    def __init__(self, inner: Any) -> None:
        self.inner = inner
        self.frames: list[np.ndarray] = []
        self.devices: set[str] = set()

    def capabilities(self) -> Any:
        return self.inner.capabilities()

    def open(self, *args: Any, **kwargs: Any) -> None:
        self.inner.open(*args, **kwargs)

    def write(self, frame: Frame) -> None:
        self.devices.add(frame.device)
        self.frames.append(_host(frame))
        self.inner.write(frame)

    def close(self) -> Any:
        return self.inner.close()

    def abort(self) -> None:
        self.inner.abort()


class CountingSource:
    """A real source that counts the decodes each job's source begins."""

    def __init__(self, inner: Any, counts: list[int]) -> None:
        self.inner = inner
        self.counts = counts
        counts.append(0)

    def probe(self, path: Path) -> ProbeResult:
        return self.inner.probe(path)

    def frames(self, probe: ProbeResult, *, hw_decode: bool, **kwargs: Any) -> Iterator[Frame]:
        self.counts[-1] += 1
        return self.inner.frames(probe, hw_decode=hw_decode, **kwargs)


class Composed:
    """The composition root's engine with recording sinks and counting sources, one per job."""

    def __init__(self, cache: Path) -> None:
        self.sinks: list[RecordingSink] = []
        self.decodes: list[int] = []
        self.exports = composition.export_jobs(
            cache_folder=cache, source_for=self._source, sink_for=self._sink
        )

    def _source(self, device: ArrayBackend | None) -> Any:
        return CountingSource(composition.video_source(device), self.decodes)

    def _sink(self, device: ArrayBackend | None) -> Any:
        self.sinks.append(RecordingSink(composition.video_sink(device)))
        return self.sinks[-1]

    def run(self, request: ExportRequest, progress: Any = None) -> Any:
        return self.exports.job(request)(progress or StubProgress())


def _assert_v4(source: Path, output: Path, bit_depth: int = 8) -> dict[str, Any]:
    import video_fidelity as vf
    from container_spike import compare

    record = vf.fidelity_record(source, output, bit_depth=bit_depth)
    wrong = record["summary"]["different_items"]
    assert record["summary"]["mandatory_and_required_all_same"], (
        wrong["MANDATORY"],
        wrong[compare.REQUIRED],
    )
    items = {item["name"]: item for item in record["items"]}
    assert items[vf._ROSTER_ITEM]["status"] == "SAME"
    return items


# --- V4: one sample per backend; the refused samples -------------------------------------------


def test_v4_through_the_composition_on_the_cpu(sample: Sample, tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()
    source = sample(CLIP)
    composed = Composed(tmp_path / "cache")
    result = composed.run(_request(source, out))
    assert result.ok, result.failure
    assert result.device == "CPU: forced" and composed.sinks[0].devices == {"cpu"}
    (output,) = result.outputs
    items = _assert_v4(source, output)
    assert items["video frame count"]["output"] == 45


@pytest.mark.gpu
def test_v4_through_the_composition_on_the_gpu_with_device_frames(
    sample: Sample, tmp_path: Path
) -> None:
    from clearwater.core import backend_for

    try:
        backend_for("cuda:0")
    except Exception as exc:  # no usable CUDA device here
        pytest.skip(f"no CUDA backend: {exc}")
    out = tmp_path / "out"
    out.mkdir()
    source = sample(CLIP)
    composed = Composed(tmp_path / "cache")
    result = composed.run(_request(source, out, force_cpu=False, video_encoder="auto"))
    assert result.ok, result.failure
    assert result.device.startswith("GPU") and composed.sinks[0].devices == {"cuda:0"}
    (output,) = result.outputs
    _assert_v4(source, output)


@pytest.mark.parametrize("sample_id", ["vid-hlg", "vid-pq", "gopro-lower-gl010001-lrv"])
def test_refused_samples_fail_readably_through_the_composition(
    sample: Sample, tmp_path: Path, sample_id: str
) -> None:
    out, cache = tmp_path / "out", tmp_path / "cache"
    out.mkdir()
    source = sample(sample_id)
    composed = Composed(cache)
    result = composed.run(_request(source, out))
    assert not result.ok and result.failure is not CANCELLED and result.outputs == ()
    assert result.failure is not None and result.failure.startswith(source.name)
    assert result.failure.isascii()
    assert list(out.iterdir()) == [] and not cache.exists()
    assert all(sink.frames == [] for sink in composed.sinks)


# --- V9: neutral parameters reproduce the input (AD-11, pre-encode) ----------------------------


def _decoded(source: Path) -> list[np.ndarray]:
    from clearwater.io.video import FFmpegVideoSource

    reader = FFmpegVideoSource()
    stream = reader.frames(reader.probe(source), hw_decode=False)
    try:
        return [_host(frame) for frame in stream]
    finally:
        close = getattr(stream, "close", None)
        if close is not None:
            close()


def _v9_differences(written: list[np.ndarray], decoded: list[np.ndarray]) -> tuple[float, float]:
    assert len(written) == len(decoded)
    diff = np.abs(np.stack(written).astype(np.float64) - np.stack(decoded))
    return float(diff.max()), float(diff.mean())


@pytest.mark.parametrize("method", ["c3", "ancuti2018"])
def test_v9_neutral_parameters_reproduce_the_decoded_source(
    sample: Sample, tmp_path: Path, method: str
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    source = sample(CLIP)
    neutral = {p.name: p.neutral for p in composition.correction_methods()[method].parameters}
    request = ExportRequest(source, "video", new_parameter_set(method, neutral), _settings(out))
    composed = Composed(tmp_path / "cache")
    result = composed.run(request)
    assert result.ok, result.failure
    written = composed.sinks[0].frames
    assert len(written) == 45
    largest, mean = _v9_differences(written, _decoded(source))
    print(f"V9 {method}: max {largest * 255:.4f}/255, mean {mean * 255:.5f}/255")
    assert largest <= 2 / 255 and mean <= 0.2 / 255, (largest, mean)
    items = _assert_v4(source, result.outputs[0])
    for name in ("colour primaries", "colour transfer", "colour matrix", "colour range"):
        assert items[name]["status"] == "SAME", items[name]


def test_the_v9_bound_fails_a_planted_non_neutral_render(sample: Sample, tmp_path: Path) -> None:
    """The V9 check catches a render that is not the identity (c3 at its defaults)."""
    out = tmp_path / "out"
    out.mkdir()
    composed = Composed(tmp_path / "cache")
    assert composed.run(_request(sample(CLIP), out)).ok
    largest, _ = _v9_differences(composed.sinks[0].frames, _decoded(sample(CLIP)))
    assert largest > 2 / 255


# --- V17: a reopen skips the decode pass; another format version re-analyses ------------------


def test_v17_a_reopen_skips_the_decode_and_renders_the_same_frames(
    sample: Sample, tmp_path: Path
) -> None:
    from clearwater.cache import entry_name, parse_entry_name

    out, cache = tmp_path / "out", tmp_path / "cache"
    out.mkdir()
    source = sample(CLIP)
    first = Composed(cache)
    assert first.run(_request(source, out)).ok
    second = Composed(cache)  # a new engine over the same cache folder (a reopen)
    assert second.run(_request(source, out)).ok
    assert first.decodes == [2] and second.decodes == [1]  # only the first analysis decoded
    assert len(first.sinks[0].frames) == len(second.sinks[0].frames) == 45
    pairs = zip(first.sinks[0].frames, second.sinks[0].frames, strict=True)
    assert all(same_bits(a, b) for a, b in pairs)
    assert _entry_states(cache) == [True]

    (folder,) = [p for p in cache.iterdir() if p.is_dir()]
    key = parse_entry_name(folder.name)
    assert key is not None
    other = folder.with_name(entry_name(replace(key, cache_version=key.cache_version + 1)))
    folder.rename(other)  # an entry of another cache format version
    third = Composed(cache)  # the open removes it
    assert not other.exists()
    assert third.run(_request(source, out)).ok
    assert third.decodes == [2] and _entry_states(cache) == [True]


# --- each file its own clip (spec section 5.5) -------------------------------------------------


def test_each_file_is_its_own_clip_in_either_order(sample: Sample, tmp_path: Path) -> None:
    from clearwater.jobs import run_batch

    a, b = sample(CLIP), sample("vid-rotated")
    solo: dict[str, list[np.ndarray]] = {}
    for index, source in enumerate((a, b)):
        out = tmp_path / f"solo{index}"
        out.mkdir()
        composed = Composed(tmp_path / f"solo-cache{index}")
        assert composed.run(_request(source, out)).ok
        solo[source.name] = composed.sinks[0].frames
    for order in ((a, b), (b, a)):
        tag = "-".join(p.stem for p in order)
        out = tmp_path / f"batch-{tag}"
        out.mkdir()
        composed = Composed(tmp_path / f"batch-cache-{tag}")
        report = run_batch(composed.exports, [_request(p, out) for p in order], StubProgress())
        assert [item.state for item in report.items] == ["done", "done"]
        assert composed.decodes == [2, 2]
        for source, sink in zip(order, composed.sinks, strict=True):
            expected = solo[source.name]
            assert len(sink.frames) == len(expected)
            assert all(same_bits(x, y) for x, y in zip(sink.frames, expected, strict=True))
        assert len([p for p in (tmp_path / f"batch-cache-{tag}").iterdir() if p.is_dir()]) == 2


# --- cancel and failure on the composed engine -------------------------------------------------


class CancelOn(StubProgress):
    """Cancel when a report's message starts with ``prefix`` and its count reaches ``at``."""

    def __init__(self, prefix: str, at: int = 0) -> None:
        super().__init__()
        self.prefix = prefix
        self.at = at

    def report(self, done: int, total: int | None, message: str) -> None:
        super().report(done, total, message)
        if message.startswith(self.prefix) and done >= self.at:
            self.cancel()


def _job_threads() -> list[str]:
    names = ("export-analysis", "export-cancel")
    return [t.name for t in threading.enumerate() if t.name in names]


def _ffmpeg_children() -> list[str]:
    import psutil

    found = []
    for child in psutil.Process().children(recursive=True):
        try:
            if "ffmpeg" in child.name().lower():
                found.append(child.name())
        except psutil.Error:
            continue
    return found


@pytest.mark.parametrize(("prefix", "at"), [("Analysing", 3), ("Exporting", 10)])
def test_a_cancel_in_the_lead_or_mid_encode_leaves_nothing(
    sample: Sample, tmp_path: Path, prefix: str, at: int
) -> None:
    out = tmp_path / "out"
    out.mkdir()
    composed = Composed(tmp_path / "cache")
    result = composed.run(_request(sample(CLIP), out), CancelOn(prefix, at))
    assert result.failure is CANCELLED and result.outputs == ()
    assert list(out.iterdir()) == []  # no temporary, no final
    assert _job_threads() == [] and _ffmpeg_children() == []
    if prefix == "Exporting":
        assert 0 < len(composed.sinks[0].frames) < 45
    else:
        assert composed.sinks[0].frames == []


def test_a_failure_in_the_analysis_half_keeps_its_own_text(sample: Sample, tmp_path: Path) -> None:
    out = tmp_path / "out"
    out.mkdir()

    class Failing(CountingSource):
        def frames(self, probe: ProbeResult, *, hw_decode: bool, **kwargs: Any) -> Iterator[Frame]:
            stream = super().frames(probe, hw_decode=hw_decode, **kwargs)
            analysis = self.counts[-1] == 1  # the analysis's decode begins first

            def frames() -> Iterator[Frame]:
                try:
                    for index, frame in enumerate(stream):
                        if analysis and index == 5:
                            raise OSError("planted read error in the analysis")
                        yield frame
                finally:
                    close = getattr(stream, "close", None)
                    if close is not None:
                        close()

            return frames()

    decodes: list[int] = []
    exports = composition.export_jobs(
        cache_folder=tmp_path / "cache",
        source_for=lambda device: Failing(composition.video_source(device), decodes),
    )
    result = exports.job(_request(sample(CLIP), out))(StubProgress())
    assert not result.ok and result.failure is not CANCELLED
    assert result.failure == (
        "hevc8-bt709-full.mp4: analysis failed: OSError: planted read error in the analysis"
    )
    assert list(out.iterdir()) == [] and _job_threads() == []
