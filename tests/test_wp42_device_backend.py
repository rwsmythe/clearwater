"""DR-67: the product's video job runs its source, sink and analysis on the backend it selected.

``ExportEngine``'s per-job factories (WP4.2 question 1): ``source_for`` and ``sink_for`` are
called once per video job, right after the job's one ``select_backend`` call, with the selected
backend for a GPU job and None for a CPU job; the job's analysis engine gets the same backend
and the same per-job source. Recording doubles check the wiring (identity, not equality); three
planted wrong wirings show the check fails by name. The ``gpu`` leg exports a WP2.3 sample
through the composition root and sees the sink receive ``cuda:0`` frames.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.analysis import AnalysisEngine
from clearwater.interfaces import ArrayBackend, CacheKey, Fault, Frame, Settings
from clearwater.interfaces.stubs import StubProgress, StubProxyCache
from clearwater.jobs import ExportEngine
from clearwater.jobs import export as export_module
from clearwater.jobs.export_seam import ExportRequest
from test_analysis_support import GrayWorld, ListSource, make_probe, synthetic_frames
from test_jobs_export_support import (
    CPU,
    FakePhotoReader,
    FakePhotoWriter,
    FakeSink,
    parameter_set,
)


class GpuDouble:
    """A backend double on ``"cuda:0"`` with the AD-29 device extensions; it computes on the host.

    It satisfies ``DeviceFrameBackend``, ``AnalysisDeviceBackend`` and ``JobDeviceBackend`` by
    structure; the frames of the doubles below stay on the host, so the extensions never run.
    """

    device = "cuda:0"

    def __init__(self, name: str = "gpu") -> None:
        self.name = name
        self.releases = 0

    def __getattr__(self, attribute: str) -> Any:
        return getattr(CPU, attribute)

    def planes_to_rgb(self, data: Any, *, width: int, height: int, bit_depth: int) -> Any:
        raise AssertionError("no device decode in this double")

    def rgb_to_planes(self, a: Any, *, bit_depth: int) -> bytes:
        raise AssertionError("no device encode in this double")

    def block_sums(self, a: Any, k: int) -> None:
        return None

    def release_fft_plans(self) -> None:
        self.releases += 1


class Recording:
    """What one engine's jobs handed to the factories, the selector and the analysis engine."""

    def __init__(self, answers: list[ArrayBackend]) -> None:
        self.answers = answers
        self.selections: list[ArrayBackend] = []
        self.sources: list[tuple[object, ListSource]] = []
        self.sinks: list[tuple[object, FakeSink]] = []
        self.analysis: list[tuple[object, object]] = []

    def select(self, settings: Settings, height: int, width: int, method: str) -> Any:
        backend = self.answers[len(self.selections) % len(self.answers)]
        self.selections.append(backend)
        return backend, "GPU" if backend.device != "cpu" else "CPU: forced"


FRAMES = 6


def _engine(
    tmp_path: Path, recording: Recording, monkeypatch: pytest.MonkeyPatch
) -> tuple[ExportEngine, ListSource]:
    probe = make_probe(nb_frames=FRAMES)
    base = ListSource(synthetic_frames(FRAMES), probe)

    def source_for(device: ArrayBackend | None) -> ListSource:
        source = ListSource(synthetic_frames(FRAMES), probe)
        recording.sources.append((device, source))
        return source

    def sink_for(device: ArrayBackend | None) -> FakeSink:
        sink = FakeSink()
        recording.sinks.append((device, sink))
        return sink

    real_init = AnalysisEngine.__init__

    def recording_init(self: AnalysisEngine, **kwargs: Any) -> None:
        recording.analysis.append((kwargs["backend"], kwargs["source"]))
        real_init(self, **kwargs)

    monkeypatch.setattr(AnalysisEngine, "__init__", recording_init)
    engine = ExportEngine(
        methods={"grayworld": GrayWorld()},
        video_source=base,
        sink_factory=lambda: pytest.fail("the base sink factory was called"),
        photo_reader=FakePhotoReader(),
        photo_writer=FakePhotoWriter(),
        cache=StubProxyCache(),
        cache_key=lambda path: CacheKey(size=1, mtime_ns=2, cache_version=3),
        select_backend=recording.select,
        app_version="9.9.9",
        source_for=source_for,
        sink_for=sink_for,
    )
    return engine, base


def _request(tmp_path: Path, kind: str = "video", **settings: Any) -> ExportRequest:
    source = tmp_path / ("clip.mp4" if kind == "video" else "shot.png")
    source.write_bytes(b"source bytes")
    values: dict[str, Any] = {"video_encoder": "libx265", "output_folder": tmp_path, **settings}
    return ExportRequest(source, kind, parameter_set(), Settings(**values))  # type: ignore[arg-type]


def wiring_problems(recording: Recording, base: ListSource) -> list[str]:
    """Name every way one video job's wiring departs from DR-67 (empty when it is right)."""
    problems = []
    if len(recording.selections) != 1:
        problems.append(f"select_backend called {len(recording.selections)} times, not once")
    if not recording.selections:
        return problems
    selected = recording.selections[0]
    expected = selected if selected.device != "cpu" else None
    for what, calls in (("source", recording.sources), ("sink", recording.sinks)):
        if len(calls) != 1:
            problems.append(f"the {what} factory was called {len(calls)} times, not once")
            continue
        given = calls[0][0]
        if expected is None and given is not None:
            problems.append(f"the CPU job's {what} got a device backend ({given!r})")
        elif expected is not None and given is None:
            problems.append(f"the GPU job's {what} got None: the silent OFF row")
        elif given is not expected:
            problems.append(f"the GPU job's {what} got another backend than the job selected")
    if len(recording.analysis) != 1:
        problems.append(f"{len(recording.analysis)} analysis engines, not one")
    else:
        backend, source = recording.analysis[0]
        if backend is not selected:
            problems.append("the analysis engine got another backend than the job selected")
        if not recording.sources or source is not recording.sources[0][1]:
            problems.append("the analysis engine reads another source than the job's")
    if base.iterations:
        problems.append("the base video source decoded frames (it only probes)")
    if recording.sources and recording.sources[0][1].iterations != 2:
        problems.append("the job's source was not decoded once for the analysis and once to render")
    return problems


@pytest.mark.parametrize("on_gpu", [True, False], ids=["gpu-job", "cpu-job"])
def test_a_video_job_hands_its_selected_backend_to_source_sink_and_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, on_gpu: bool
) -> None:
    gpu = GpuDouble()
    recording = Recording([gpu if on_gpu else CPU])
    engine, base = _engine(tmp_path, recording, monkeypatch)

    result = engine.job(_request(tmp_path))(StubProgress())

    assert result.ok, result.failure
    assert wiring_problems(recording, base) == []
    assert recording.sinks[0][1].calls[-1] == "close"
    assert len(recording.sinks[0][1].frames) == FRAMES
    if on_gpu:
        assert recording.sources[0][0] is gpu and recording.sinks[0][0] is gpu
        assert gpu.releases == 2  # the analysis end and the job end (WP3.21), on that backend
    else:
        assert recording.sources[0][0] is None and recording.sinks[0][0] is None


def test_a_photo_job_calls_no_video_factory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recording = Recording([GpuDouble()])
    engine, _base = _engine(tmp_path, recording, monkeypatch)
    result = engine.job(_request(tmp_path, "photo"))(StubProgress())
    assert result.ok, result.failure
    assert recording.sources == [] and recording.sinks == [] and recording.analysis == []


def test_a_refused_probe_builds_nothing_per_job(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    recording = Recording([GpuDouble()])
    engine, base = _engine(tmp_path, recording, monkeypatch)
    refused = replace(make_probe(nb_frames=FRAMES), faults=(Fault("hlg", "refuse", "no"),))
    monkeypatch.setattr(base, "probe", lambda path: refused)
    result = engine.job(_request(tmp_path))(StubProgress())
    assert not result.ok
    assert recording.selections == [] and recording.sources == [] and recording.sinks == []


def test_without_the_factories_the_engine_is_unchanged(tmp_path: Path) -> None:
    probe = make_probe(nb_frames=FRAMES)
    base = ListSource(synthetic_frames(FRAMES), probe)
    sinks: list[FakeSink] = []

    def sink() -> FakeSink:
        sinks.append(FakeSink())
        return sinks[-1]

    engine = ExportEngine(
        methods={"grayworld": GrayWorld()},
        video_source=base,
        sink_factory=sink,
        photo_reader=FakePhotoReader(),
        photo_writer=FakePhotoWriter(),
        cache=StubProxyCache(),
        cache_key=lambda path: CacheKey(size=1, mtime_ns=2, cache_version=3),
        select_backend=lambda *a: (CPU, "CPU: forced"),
    )
    result = engine.job(_request(tmp_path))(StubProgress())
    assert result.ok, result.failure
    assert base.iterations == 2 and len(sinks) == 1 and len(sinks[0].frames) == FRAMES


# --- planted wrong wirings: the check above fails each by name --------------------------------


PLANTS: dict[str, tuple[Callable[[Any, ArrayBackend], Any], str, str]] = {
    "gpu-gets-none": (lambda self, backend: None, "gpu", "got None: the silent OFF row"),
    "cpu-gets-gpu": (
        lambda self, backend: PLANTED_GPU,
        "cpu",
        "the CPU job's source got a device backend",
    ),
    "second-selection": (
        lambda self, backend: self._select_backend(Settings(), 8, 12, "grayworld")[0],
        "gpu",
        "select_backend called 2 times",
    ),
}
PLANTED_GPU = GpuDouble("planted")


@pytest.mark.parametrize("plant", sorted(PLANTS))
def test_a_planted_wrong_wiring_fails_the_check_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, plant: str
) -> None:
    wrong, job, name = PLANTS[plant]
    first = GpuDouble("first") if job == "gpu" else CPU
    recording = Recording([first, GpuDouble("second")])
    engine, base = _engine(tmp_path, recording, monkeypatch)
    monkeypatch.setattr(export_module.ExportEngine, "_job_device", wrong)
    engine.job(_request(tmp_path))(StubProgress())
    problems = wiring_problems(recording, base)
    assert any(name in problem for problem in problems), problems


# --- the real GPU leg through the composition root -------------------------------------------


@pytest.mark.gpu
@pytest.mark.usefixtures("ffmpeg_tools")
def test_the_composed_gpu_job_sends_device_frames_to_the_sink(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    from clearwater.app import composition
    from clearwater.core import backend_for

    try:
        backend_for("cuda:0")
    except Exception as exc:  # no usable CUDA device here
        pytest.skip(f"no CUDA backend: {exc}")
    source = sample("vid-hevc8-bt709-full")
    seen: dict[str, Any] = {"devices": set(), "given": []}

    def sink_for(device: ArrayBackend | None) -> Any:
        sink = composition.video_sink(device)
        seen["given"].append(device)
        write = sink.write

        def recording_write(frame: Frame) -> None:
            seen["devices"].add(frame.device)
            write(frame)

        sink.write = recording_write  # type: ignore[method-assign]
        return sink

    out = tmp_path / "out"
    out.mkdir()
    exports = composition.export_jobs(cache_folder=tmp_path / "cache", sink_for=sink_for)
    settings = Settings(output_folder=out, video_encoder="auto")
    result = exports.job(ExportRequest(source, "video", parameter_set("c3"), settings))(
        StubProgress()
    )
    assert result.ok, result.failure
    assert result.device.startswith("GPU"), result.device
    (given,) = seen["given"]
    assert given is not None and given.device == "cuda:0"
    assert seen["devices"] == {"cuda:0"}
    assert np.all([p.exists() for p in result.outputs])
