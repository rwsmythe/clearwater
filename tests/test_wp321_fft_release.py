"""WP3.21 Q-C5a condition 1: an export job releases its backend's FFT plans once, at its end.

``CupyBackend.release_fft_plans`` (an IF-2 device extension, AD-29) clears the calling thread's
cuFFT plan cache and the pool's free blocks. ``clearwater.jobs`` reaches it only through its own
``runtime_checkable`` Protocol (:class:`clearwater.jobs.export.JobDeviceBackend`) and calls it
once per job on the job's thread on every path (success, failure, cancel; video and photo),
never per frame; a video job also calls it once on the analysis thread when that thread returns
(the analysis-end boundary, CHARC ruling at task 10), so the pool's cached blocks go back to the
device for the rest of the export. A backend without it (the CPU backend) has nothing to
release, and a release that raises never replaces the job's outcome.
"""

from __future__ import annotations

import subprocess
import threading
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
from clearwater.jobs import export as export_module
from clearwater.jobs.export import JobDeviceBackend
from clearwater.jobs.export_seam import CANCELLED, ExportRequest
from clearwater.methods import available_methods
from test_jobs_export_support import FakePhotoReader, FakePhotoWriter, FakeSink, parameter_set

SAMPLE = "vid-hevc8-bt709-full"
HOLD_S = 30.0
"""DR-74's bound on each wait of its observation window (a miss fails the case)."""


class _Releasing(NumpyBackend):
    """The CPU backend plus the extension: counts releases and notes the sink's calls by then."""

    def __init__(self, error: BaseException | None = None, sink: FakeSink | None = None) -> None:
        super().__init__()
        self.releases = 0
        self.threads: list[str] = []
        self.error = error
        self.sink = sink
        self.sink_calls: list[str] = []

    def release_fft_plans(self) -> None:
        self.releases += 1
        self.threads.append(threading.current_thread().name)
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


@pytest.mark.gpu
def test_the_analysis_end_boundary_frees_the_pools_cached_blocks(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    try:
        gpu = backend_for("cuda:0")
    except Exception as error:  # no CuPy or no device
        pytest.skip(f"no GPU backend: {error}")
    pool = gpu.xp.get_default_memory_pool()
    release = export_module._release_fft_plans
    seen: list[tuple[str, int, int]] = []

    def spied(backend: object) -> None:
        if threading.current_thread().name == "export-analysis":
            planted = gpu.asarray(np.zeros((4096, 4096), dtype=np.float32))  # 64 MiB
            del planted  # its block stays in the pool, cached
        before = pool.total_bytes() - pool.used_bytes()
        release(backend)
        seen.append(
            (threading.current_thread().name, before, pool.total_bytes() - pool.used_bytes())
        )

    monkeypatch.setattr(export_module, "_release_fft_plans", spied)
    sink = FakeSink()
    result = _video(tmp_path, sample(SAMPLE), gpu, sink)
    assert result.ok, result.failure
    assert len(sink.frames) == 45
    assert [name for name, _, _ in seen] == _both_boundaries()
    _, before, after = seen[0]
    assert before >= 64 * 1024**2 and after < before


@pytest.mark.gpu
@pytest.mark.slow  # a 1080p clip longer than c3's lead, generated and exported on the GPU
def test_the_analysis_end_release_frees_the_pool_while_frames_render(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """DR-74 (WP4.2): at a gated resolution, longer than c3's derived lead (61 frames)."""
    try:
        gpu = backend_for("cuda:0")
    except Exception as error:  # no CuPy or no device
        pytest.skip(f"no GPU backend: {error}")
    frames = 90
    source = tmp_path / "gated-1080p.mp4"
    subprocess.run(
        [
            "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-y", "-f", "lavfi", "-i",
            f"testsrc2=size=1920x1080:rate=30:duration={frames / 30}", "-vf", "hue=h=t*60",
            "-bf", "0", "-c:v", "libx265", "-preset", "ultrafast", "-x265-params",
            "log-level=error", "-pix_fmt", "yuv420p", "-color_primaries", "bt709",
            "-color_trc", "bt709", "-colorspace", "bt709", "-color_range", "tv", str(source),
        ],
        check=True,
        capture_output=True,
    )  # fmt: skip
    pool = gpu.xp.get_default_memory_pool()
    release = export_module._release_fft_plans
    sink = FakeSink()
    seen: list[tuple[str, int, int, list[str], int, int]] = []
    # The observation window by construction, each wait bounded (a miss fails, never hangs):
    # the analysis-end release waits for the first written frame, and the sink holds the next
    # write until that release's pool drop is recorded.
    first_written, dropped = threading.Event(), threading.Event()
    write = sink.write

    def held_write(frame: Any) -> None:
        if len(sink.frames) == 1 and not dropped.wait(HOLD_S):
            raise TimeoutError(
                f"DR-74: no analysis-end pool drop within {HOLD_S} s of the first frame"
            )
        write(frame)
        first_written.set()

    def spied(backend: object) -> None:
        analysis_end = threading.current_thread().name == "export-analysis"
        if analysis_end:
            planted = gpu.asarray(np.zeros((4096, 4096), dtype=np.float32))  # 64 MiB
            del planted  # its block stays in the pool, cached
            first_written.wait(HOLD_S)  # a miss shows as started == 0 below
        calls, started = list(sink.calls), len(sink.frames)
        before = pool.total_bytes() - pool.used_bytes()
        release(backend)
        after = pool.total_bytes() - pool.used_bytes()
        remaining = frames - len(sink.frames)  # sampled once the pool drop is observed
        seen.append((threading.current_thread().name, before, after, calls, started, remaining))
        if analysis_end:
            dropped.set()

    monkeypatch.setattr(sink, "write", held_write)
    monkeypatch.setattr(export_module, "_release_fft_plans", spied)
    result = _video(tmp_path, source, gpu, sink)
    assert result.ok, result.failure
    assert len(sink.frames) == frames
    assert [name for name, *_ in seen] == _both_boundaries()
    _, before, after, calls, started, remaining = seen[0]
    assert "open" in calls and "close" not in calls  # the encode was under way
    assert started >= 1, f"rendering had not started within {HOLD_S} s of the analysis end"
    assert remaining > 0, remaining  # frames still to render once the pool dropped
    assert before >= 64 * 1024**2 and after < before  # the pool's cached blocks went back


def _both_boundaries() -> list[str]:
    """The release threads of a video job: the analysis thread's return, then the job's end."""
    return ["export-analysis", threading.current_thread().name]


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_video_job_releases_twice_at_the_analysis_end_and_at_the_job_end(
    sample: Any, tmp_path: Path
) -> None:
    sink = FakeSink()
    backend = _Releasing(sink=sink)
    result = _video(tmp_path, sample(SAMPLE), backend, sink)
    assert result.ok, result.failure
    assert backend.threads == _both_boundaries() and len(sink.frames) == 45
    assert backend.sink_calls == sink.calls and sink.calls[-1] == "close"  # after the last frame


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_failed_video_job_releases_at_both_boundaries(sample: Any, tmp_path: Path) -> None:
    backend, sink = _Releasing(), FakeSink()
    sink.fail_at = 10
    result = _video(tmp_path, sample(SAMPLE), backend, sink)
    assert not result.ok and result.failure is not CANCELLED
    assert backend.threads == _both_boundaries()


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_cancelled_video_job_releases_at_both_boundaries(sample: Any, tmp_path: Path) -> None:
    backend, sink = _Releasing(), FakeSink()
    result = _video(tmp_path, sample(SAMPLE), backend, sink, progress=_CancelAt(10))
    assert result.failure is CANCELLED and result.outputs == ()
    assert backend.threads == _both_boundaries()


def test_a_job_that_fails_before_choosing_a_backend_releases_nothing(tmp_path: Path) -> None:
    backend, sink = _Releasing(), FakeSink()
    result = _video(tmp_path, tmp_path / "missing.mp4", backend, sink)
    assert not result.ok and backend.releases == 0


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_raising_release_keeps_the_jobs_outcome(sample: Any, tmp_path: Path) -> None:
    backend, sink = _Releasing(error=RuntimeError("planted release failure")), FakeSink()
    result = _video(tmp_path, sample(SAMPLE), backend, sink)
    assert result.ok, result.failure
    assert backend.threads == _both_boundaries()  # the analysis thread's raise is logged too


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
