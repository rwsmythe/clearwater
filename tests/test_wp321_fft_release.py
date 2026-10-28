"""WP3.21 Q-C5a condition 1: an export job releases its backend's FFT plans once, at its end.

``CupyBackend.release_fft_plans`` (an IF-2 device extension, AD-29) clears the calling thread's
cuFFT plan cache and the pool's free blocks. ``clearwater.jobs`` reaches it only through its own
``runtime_checkable`` Protocol (:class:`clearwater.jobs.export.JobDeviceBackend`) and calls it
once per job on every path (success, failure, cancel; video and photo), never per frame; a
backend without it (the CPU backend) has nothing to release, and a release that raises never
replaces the job's outcome.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import pytest

from clearwater.cache import DiskProxyCache, cache_key
from clearwater.core import backend_for
from clearwater.core.backend import NumpyBackend
from clearwater.interfaces import Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.io.video import FFmpegVideoSource
from clearwater.jobs import ExportEngine
from clearwater.jobs.export import JobDeviceBackend
from clearwater.jobs.export_seam import CANCELLED, ExportRequest
from clearwater.methods import available_methods
from test_jobs_export_support import FakePhotoReader, FakePhotoWriter, FakeSink, parameter_set

SAMPLE = "vid-hevc8-bt709-full"


class _Releasing(NumpyBackend):
    """The CPU backend plus the extension: counts releases and notes the sink's calls by then."""

    def __init__(self, error: BaseException | None = None, sink: FakeSink | None = None) -> None:
        super().__init__()
        self.releases = 0
        self.error = error
        self.sink = sink
        self.sink_calls: list[str] = []

    def release_fft_plans(self) -> None:
        self.releases += 1
        if self.sink is not None:
            self.sink_calls = list(self.sink.calls)
        if self.error is not None:
            raise self.error


class _CancelAt:
    """Raises the cancel flag once ``frames`` frames have been exported."""

    def __init__(self, frames: int) -> None:
        self._frames = frames
        self._cancelled = False

    def report(self, done: int, total: int | None, message: str) -> None:
        if message.startswith("Exporting") and done >= self._frames:
            self._cancelled = True

    def cancelled(self) -> bool:
        return self._cancelled


def _engine(cache: Path, backend: Any, sink: FakeSink) -> ExportEngine:
    return ExportEngine(
        methods=available_methods(),
        video_source=FFmpegVideoSource(),
        sink_factory=lambda: sink,
        photo_reader=FakePhotoReader(),
        photo_writer=FakePhotoWriter(),
        cache=DiskProxyCache(cache),
        cache_key=cache_key,
        select_backend=lambda settings, h, w, m: (backend, "GPU"),
    )


def _video(tmp_path: Path, source: Path, backend: Any, sink: FakeSink, progress: Any = None) -> Any:
    out = tmp_path / "out"
    out.mkdir(exist_ok=True)
    settings = Settings(output_folder=out, video_encoder="libx265")
    request = ExportRequest(source, "video", parameter_set("c3"), settings)
    return _engine(tmp_path / "cache", backend, sink).job(request)(progress or StubProgress())


def test_the_protocol_is_the_gpu_backends_only() -> None:
    assert not isinstance(backend_for("cpu"), JobDeviceBackend)
    assert isinstance(_Releasing(), JobDeviceBackend)


@pytest.mark.gpu
def test_the_gpu_backend_satisfies_the_protocol_and_releases() -> None:
    try:
        gpu = backend_for("cuda:0")
    except Exception as error:  # no CuPy or no device
        pytest.skip(f"no GPU backend: {error}")
    assert isinstance(gpu, JobDeviceBackend)
    cupy = gpu.xp
    a = gpu.asarray(np.zeros((1080, 1920), dtype=np.float32))
    gpu.gaussian_blur(a, 54.0)  # the FFT route: plans cached on this thread
    cache = cupy.fft.config.get_plan_cache()
    assert cache.get_curr_size() > 0
    pool = cupy.get_default_memory_pool()
    held = pool.total_bytes()
    gpu.release_fft_plans()
    assert cache.get_curr_size() == 0 and cache.get_curr_memsize() == 0
    assert pool.total_bytes() < held  # the plans' work areas went back to the device


def test_a_video_job_releases_once_after_every_frame(sample: Any, tmp_path: Path) -> None:
    sink = FakeSink()
    backend = _Releasing(sink=sink)
    result = _video(tmp_path, sample(SAMPLE), backend, sink)
    assert result.ok, result.failure
    assert backend.releases == 1 and len(sink.frames) == 45
    assert backend.sink_calls == sink.calls and sink.calls[-1] == "close"  # after the last frame


def test_a_failed_video_job_releases_once(sample: Any, tmp_path: Path) -> None:
    backend, sink = _Releasing(), FakeSink()
    sink.fail_at = 10
    result = _video(tmp_path, sample(SAMPLE), backend, sink)
    assert not result.ok and result.failure is not CANCELLED
    assert backend.releases == 1


def test_a_cancelled_video_job_releases_once(sample: Any, tmp_path: Path) -> None:
    backend, sink = _Releasing(), FakeSink()
    result = _video(tmp_path, sample(SAMPLE), backend, sink, progress=_CancelAt(10))
    assert result.failure is CANCELLED and result.outputs == ()
    assert backend.releases == 1


def test_a_job_that_fails_before_choosing_a_backend_releases_nothing(tmp_path: Path) -> None:
    backend, sink = _Releasing(), FakeSink()
    result = _video(tmp_path, tmp_path / "missing.mp4", backend, sink)
    assert not result.ok and backend.releases == 0


def test_a_raising_release_keeps_the_jobs_outcome(sample: Any, tmp_path: Path) -> None:
    backend, sink = _Releasing(error=RuntimeError("planted release failure")), FakeSink()
    result = _video(tmp_path, sample(SAMPLE), backend, sink)
    assert result.ok, result.failure
    assert backend.releases == 1


class _CancelOn(StubProgress):
    """Raises the cancel flag on the first report whose message starts with ``prefix``."""

    def __init__(self, prefix: str) -> None:
        super().__init__()
        self._prefix = prefix

    def report(self, done: int, total: int | None, message: str) -> None:
        super().report(done, total, message)
        if message.startswith(self._prefix):
            self.cancel()


@pytest.mark.parametrize("cancel_on", [None, "Writing"])
def test_a_photo_job_releases_once(tmp_path: Path, cancel_on: str | None) -> None:
    backend = _Releasing()
    photo = tmp_path / "photo.png"
    photo.write_bytes(b"not read: the reader is a double")
    out = tmp_path / "out"
    out.mkdir()
    request = ExportRequest(photo, "photo", parameter_set("c3"), Settings(output_folder=out))
    progress = StubProgress() if cancel_on is None else _CancelOn(cancel_on)
    result = _engine(tmp_path / "cache", backend, FakeSink()).job(request)(progress)
    if cancel_on is None:
        assert result.ok, result.failure
    else:  # cancelled after the render
        assert result.failure is CANCELLED
    assert backend.releases == 1
