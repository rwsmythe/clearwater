"""WP3.21: ``tools/export_bench.py`` writes under a chosen folder of the working folder (Q7).

It also runs a job with device frames (``--device-frames``, AD-29): the source and the sink are
built with the backend the job selects, so the GPU backend gives device frames and the CPU
backend the host path, and the record names the configuration. And it stamps the overlap
tool-side (Q-R7): the analysis thread's end and the frame loop's stall on its records.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

import export_bench as bench
from clearwater.analysis import AnalysisEngine
from clearwater.core.backend import _probe_gpu
from clearwater.interfaces.image import Frame
from export_bench import SUBDIR, _OverlapStamps, bench_folder

SAMPLE = "vid-hevc8-bt709-full"
FAST = (0.05, 0.5)


def _run(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, *, force_cpu: bool
) -> tuple[dict[str, Any], set[str]]:
    """Run one device-frame leg on the sample; return its record and the sink's frame devices."""
    monkeypatch.setattr(bench, "conditions", lambda moment: {"moment": moment})
    devices: set[str] = set()
    write = bench._BenchSink.write

    def spy(self: Any, frame: Frame) -> None:
        devices.add(frame.device)
        write(self, frame)

    monkeypatch.setattr(bench._BenchSink, "write", spy)
    leg = bench.Leg("x", 1, encoder="libx265")
    record = bench.run_once(
        sample(SAMPLE),
        tmp_path / "run-0",
        leg,
        force_cpu=force_cpu,
        keep=False,
        periods=FAST,
        device_frames=True,
    )
    return record, devices


@pytest.mark.gpu
@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_device_frame_run_gives_the_sink_device_frames(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    gpu, reason = _probe_gpu()
    if gpu is None:
        pytest.skip("CUDA unavailable for device-frame benchmark: " + reason)
    record, devices = _run(sample, tmp_path, monkeypatch, force_cpu=False)
    assert record["ok"], record["failure"]
    assert record["frames"] == 45 and record["sink_report"]["frames_written"] == 45
    assert record["device_frames"] is True
    assert record["device_backend"].startswith("CupyBackend")
    assert devices and "cpu" not in devices


def test_device_frame_gpu_benchmark_skips_without_cuda(monkeypatch: pytest.MonkeyPatch) -> None:
    """An unavailable CUDA device skips before starting a benchmark or opening a sample."""
    namespace = globals()
    if source := os.environ.get("WP65_BENCH_TEST"):
        namespace = {"__name__": "wp65_old_bench_test", "__file__": source}
        exec(compile(Path(source).read_bytes(), source, "exec"), namespace)
    monkeypatch.setitem(namespace, "_probe_gpu", lambda: (None, "CPU: no CUDA device"))

    def refused_run(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("GPU benchmark ran with no CUDA device")

    monkeypatch.setitem(namespace, "_run", refused_run)
    with pytest.raises(pytest.skip.Exception, match="CUDA unavailable for device-frame benchmark:"):
        namespace["test_a_device_frame_run_gives_the_sink_device_frames"](
            None, Path("unused"), monkeypatch
        )


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_device_frame_run_on_the_cpu_backend_takes_the_host_path(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, devices = _run(sample, tmp_path, monkeypatch, force_cpu=True)
    assert record["ok"], record["failure"]
    assert record["device"] == "CPU: forced" and record["frames"] == 45
    assert record["device_backend"].startswith("NumpyBackend")
    assert devices == {"cpu"}


def test_the_default_folder_is_unchanged(tmp_path: Path) -> None:
    assert bench_folder(tmp_path, SUBDIR) == (tmp_path / "wp3.14" / "bench").resolve()


def test_a_subdir_under_the_working_folder(tmp_path: Path) -> None:
    got = bench_folder(tmp_path, Path("wp3.21") / "bench")
    assert got == (tmp_path / "wp3.21" / "bench").resolve()


@pytest.mark.parametrize("subdir", ["..", "../elsewhere", "wp3.21/../../out"])
def test_a_subdir_leading_out_is_refused(tmp_path: Path, subdir: str) -> None:
    with pytest.raises(ValueError, match="not a folder under the working folder"):
        bench_folder(tmp_path / "work", Path(subdir))


def test_an_absolute_subdir_is_refused(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="not a folder under the working folder"):
        bench_folder(tmp_path, tmp_path / "abs")


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_run_records_the_overlap_stamps_and_restores_the_engine(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    job, record_read = AnalysisEngine.analysis_job, AnalysisEngine.smoothed_record
    record, _ = _run(sample, tmp_path, monkeypatch, force_cpu=True)
    assert record["ok"], record["failure"]
    assert record["lead_s"] == record["phases_s"]["analysis"]
    began = dict(record["stages"])["analysis"]
    assert began <= record["analysis_end_s"] <= record["wall_s"]
    assert record["record_reads"] == record["frames"] == 45
    assert 0 <= record["record_wait_max_s"] <= record["record_wait_s"]
    share = (record["lead_s"] + record["record_wait_s"]) / record["wall_s"]
    assert record["analysis_share_overlapped"] == pytest.approx(share)
    assert "lead + stall" in bench.row_line(record)
    assert AnalysisEngine.analysis_job is job and AnalysisEngine.smoothed_record is record_read


class _Clock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def test_the_stamps_time_each_record_read_and_the_job_end(monkeypatch: pytest.MonkeyPatch) -> None:
    clock = _Clock()

    def read(engine: Any, *args: Any, **kwargs: Any) -> str:
        clock.now += 2.0  # a planted stall
        return "record"

    def analysis_job(engine: Any, *args: Any, **kwargs: Any) -> Any:
        def job(progress: Any) -> str:
            clock.now += 5.0
            return "result"

        return job

    monkeypatch.setattr(AnalysisEngine, "smoothed_record", read)
    monkeypatch.setattr(AnalysisEngine, "analysis_job", analysis_job)
    stamps = _OverlapStamps(clock)
    with stamps.installed():
        engine: Any = object()
        assert AnalysisEngine.analysis_job(engine)(None) == "result"
        assert AnalysisEngine.smoothed_record(engine, 0) == "record"
        assert AnalysisEngine.smoothed_record(engine, 1) == "record"
    assert AnalysisEngine.smoothed_record is read and AnalysisEngine.analysis_job is analysis_job
    figures = stamps.figures(started=1.0, lead_s=1.5, total=10.0)
    assert figures == {
        "lead_s": 1.5,
        "analysis_end_s": 4.0,
        "record_reads": 2,
        "record_wait_s": 4.0,
        "record_wait_max_s": 2.0,
        "analysis_share_overlapped": pytest.approx(0.55),
    }


def test_the_stamps_restore_the_engine_when_the_job_raises() -> None:
    job, record_read = AnalysisEngine.analysis_job, AnalysisEngine.smoothed_record
    stamps = _OverlapStamps(_Clock())
    with pytest.raises(RuntimeError, match="planted"), stamps.installed():
        assert AnalysisEngine.smoothed_record is not record_read
        raise RuntimeError("planted")
    assert AnalysisEngine.analysis_job is job and AnalysisEngine.smoothed_record is record_read


def test_no_analysis_gives_no_end_stamp() -> None:
    figures = _OverlapStamps(_Clock()).figures(started=0.0, lead_s=None, total=3.0)
    assert figures["analysis_end_s"] is None and figures["lead_s"] is None
    assert figures["record_reads"] == 0 and figures["analysis_share_overlapped"] == 0.0
