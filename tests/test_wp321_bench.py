"""WP3.21: ``tools/export_bench.py`` writes under a chosen folder of the working folder (Q7).

It also runs a job with device frames (``--device-frames``, AD-29): the source and the sink are
built with the backend the job selects, so the GPU backend gives device frames and the CPU
backend the host path, and the record names the configuration.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

import export_bench as bench
from clearwater.interfaces.image import Frame
from export_bench import SUBDIR, bench_folder

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
def test_a_device_frame_run_gives_the_sink_device_frames(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    record, devices = _run(sample, tmp_path, monkeypatch, force_cpu=False)
    assert record["ok"], record["failure"]
    assert record["frames"] == 45 and record["sink_report"]["frames_written"] == 45
    assert record["device_frames"] is True
    assert record["device_backend"].startswith("CupyBackend")
    assert devices and "cpu" not in devices


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
