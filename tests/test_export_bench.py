"""Tests of the V16 export-row instrument ``tools/export_bench.py`` (WP3.14, questions 11, 12).

No footage: the runs use a WP2.3 sample copied into a footage folder made under ``tmp_path``,
on the CPU with libx265. The timing figures themselves are taken only in an exclusive window;
here the plan, the record's shape and arithmetic, the cleanup and the command line are checked.
"""

from __future__ import annotations

import json
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

import export_bench as bench
import video_fidelity as vf
from local_config import LocalConfig

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

SAMPLE = "vid-hevc8-bt709-full"
FAST = (0.05, 0.5)


def test_d106_is_0_4004_seconds_per_frame_at_29_97() -> None:
    """D106 / N6 in spec v0.5.8 sets 12 min/min, about 0.4004 s at 30000/1001 fps."""
    frames = 1000
    figures = bench.rate(0.4004 * frames, frames, Fraction(30000, 1001))
    assert figures["min_per_min"] == pytest.approx(bench.D106_MIN_PER_MIN, abs=0.01)


def test_d106_matches_spec_n6_12_minutes_per_minute() -> None:
    """Prevent the bench label drifting from the owner's spec v0.5.8 N6 figure."""
    assert bench.D106_MIN_PER_MIN == 12.0


def test_v16_plan_is_ruling_q12() -> None:
    assert [(leg.clip, leg.runs, leg.cache, leg.method, leg.encoder) for leg in bench.V16_PLAN] == [
        ("GX011627", 3, "cold", "c3", "auto"),
        ("GX011627", 1, "warm", "c3", "auto"),
        ("GX011627", 1, "cold", "ancuti2018", "auto"),
        ("GX011627", 1, "cold", "c3", "libx265"),
        (bench.SYNTHETIC, 1, "cold", "c3", "auto"),
        ("GX011625", 1, "cold", "c3", "auto"),
    ]
    assert {leg.quality for leg in bench.V16_PLAN} == {"standard"}
    assert bench.V16_PLAN[-1].clip == "GX011625"  # the sustained row runs LAST


def test_phase_times_run_from_each_boundary_to_the_next() -> None:
    stages = [("probe", 1.0), ("analysis", 1.5), ("open", 4.0), ("frames", 4.25)]
    assert bench.phase_times(stages, 0.5, 10.0) == {
        "setup": 0.5,
        "probe": 0.5,
        "analysis": 2.5,
        "open": 0.25,
        "frames": 5.75,
    }
    assert bench.phase_times([], 0.0, 2.0) == {"setup": 2.0}


def test_frame_intervals_start_at_the_frames_boundary_and_count_only_export_reports() -> None:
    reports = [
        (1.0, 1, 10, "Analysing clip: frame 1"),
        (2.0, 1, 10, "Exporting clip"),
        (2.5, 2, 10, "Exporting clip"),
        (3.25, 3, 10, "Exporting clip"),
        (4.0, 3, 10, "Saved clip"),
    ]
    assert bench.frame_intervals(reports, 1.5) == [0.5, 0.5, 0.75]
    assert bench.frame_intervals(reports, None) == []


@pytest.fixture
def quick(monkeypatch: pytest.MonkeyPatch) -> None:
    """Skip the before / after conditions (seconds each)."""
    monkeypatch.setattr(bench, "conditions", lambda moment: {"moment": moment})


@pytest.mark.parametrize("cache", ["cold", "warm"])
def test_run_once_records_the_row_and_deletes_its_folder(
    sample: Any, tmp_path: Path, quick: None, cache: str
) -> None:
    """Record the measured rate against D106 and leave the source unchanged."""
    source = sample(SAMPLE)
    before = (source.read_bytes(), source.stat().st_mtime_ns)
    run_dir = tmp_path / "bench" / "run-0"
    leg = bench.Leg("x", 1, cache=cache, encoder="libx265")
    record = bench.run_once(source, run_dir, leg, force_cpu=True, keep=False, periods=FAST)

    assert record["ok"], record["failure"]
    assert record["frames"] == record["source_frames"] == 45
    assert record["encoder"] == "libx265" and record["bit_depth"] == 8
    assert record["device"] == "CPU: forced"
    assert [name for name, _ in record["stages"]] == [
        "probe",
        "analysis",
        "open",
        "frames",
        "close",
        "committed",
    ]
    assert sum(record["phases_s"].values()) == pytest.approx(record["wall_s"])
    assert 0 < record["analysis_share"] < 1
    assert record["per_frame"]["n"] == 44 and len(record["per_frame_s"]) == 45
    assert record["total"]["s_per_frame"] == pytest.approx(record["wall_s"] / 45)
    assert record["meets_d106"] == (record["total"]["min_per_min"] <= bench.D106_MIN_PER_MIN)
    assert record["telemetry"]["peak_tree_rss_bytes"] > 0
    assert record["nvenc_proof"]["tied"] is False
    assert record["sink_report"]["frames_written"] == 45
    assert record["output_bytes"] > 0
    assert record["analysis_reports"] > 0
    if cache == "warm":
        assert record["prime_s"] > 0 and record["cache_complete_at_start"] is True
    else:
        assert "prime_s" not in record and record["cache_complete_at_start"] is False
    assert not run_dir.exists()  # the output and the cache went with the folder
    assert (source.read_bytes(), source.stat().st_mtime_ns) == before
    assert bench.row_line(record).startswith(f"ROW {source.name} c3 libx265 {cache}: 45 frames")


def test_run_once_keeps_the_folder_when_asked_and_never_reuses_one(
    sample: Any, tmp_path: Path, quick: None
) -> None:
    run_dir = tmp_path / "run-0"
    leg = bench.Leg("x", 1, encoder="libx265")
    record = bench.run_once(sample(SAMPLE), run_dir, leg, force_cpu=True, keep=True, periods=FAST)
    assert Path(record["run_dir"]) == run_dir
    assert [p.suffix for p in (run_dir / "out").iterdir()] == [".mp4"]
    with pytest.raises(bench.BenchError, match="never reuses"):
        bench.run_once(sample(SAMPLE), run_dir, leg, force_cpu=True, keep=False, periods=FAST)
    assert (run_dir / "out").is_dir()  # left as it was


def test_telemetry_stops_at_the_end_of_the_export(
    sample: Any, tmp_path: Path, quick: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # R1 F8 / R2 G4-G5: the stray window is read first (a quick snapshot at the export's end),
    # then the memory telemetry is stopped (its join can take seconds), then the GPU sampler.
    order: list[str] = []

    class Sampler:
        def start(self) -> None:
            order.append("sampler start")

        def stop(self) -> list[Any]:
            order.append("sampler")
            return []

    class Telemetry(bench.Telemetry):
        def stop(self) -> Any:
            order.append("telemetry")
            return super().stop()

    class StrayWatch(bench.StrayWatch):
        def window(self) -> Any:
            order.append("strays")
            return super().window()

    monkeypatch.setattr(bench, "Telemetry", Telemetry)
    monkeypatch.setattr(bench, "StrayWatch", StrayWatch)
    monkeypatch.setattr(bench, "_gpu_sampler", lambda leg: Sampler())
    leg = bench.Leg("x", 1, encoder="libx265")
    record = bench.run_once(
        sample(SAMPLE), tmp_path / "run-0", leg, force_cpu=True, keep=False, periods=FAST
    )
    assert record["ok"], record["failure"]
    assert order == ["sampler start", "strays", "telemetry", "sampler"]


def test_the_gpu_sampler_runs_for_nvenc_legs_only() -> None:
    assert bench._gpu_sampler(bench.Leg("x", 1, encoder="libx265")) is None
    assert isinstance(bench._gpu_sampler(bench.Leg("x", 1, encoder="hevc_nvenc")), vf._Sampler)


# --- the command line ------------------------------------------------------------------------


@pytest.fixture
def folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, quick: None) -> LocalConfig:
    config = LocalConfig(footage_path=tmp_path / "footage", working_path=tmp_path / "work")
    config.footage_path.mkdir()
    monkeypatch.setattr(bench, "load_local_config", lambda path=None: config)
    return config


def test_v16_dry_run_lists_the_plan_and_writes_nothing(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    for stem in ("GX011627", "GX011625"):
        (folders.footage_path / f"{stem}.MP4").write_bytes(b"")
    assert bench.main(["v16", "--dry-run"]) == 0
    plan = [line for line in capsys.readouterr().out.splitlines() if line.startswith("PLAN")]
    assert plan == [
        "PLAN GX011627 x3 c3 auto standard cold",
        "PLAN GX011627 x1 c3 auto standard warm",
        "PLAN GX011627 x1 ancuti2018 auto standard cold",
        "PLAN GX011627 x1 c3 libx265 standard cold",
        f"PLAN {bench.SYNTHETIC} x1 c3 auto standard cold",
        "PLAN GX011625 x1 c3 auto standard cold",
    ]
    assert not folders.working_path.exists()


def test_v16_clip_selects_one_window(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    (folders.footage_path / "GX011625.MP4").write_bytes(b"")
    assert bench.main(["v16", "--clip", "gx011625", "--dry-run"]) == 0
    plan = [line for line in capsys.readouterr().out.splitlines() if line.startswith("PLAN")]
    assert plan == ["PLAN GX011625 x1 c3 auto standard cold"]
    with pytest.raises(SystemExit) as stop:
        bench.main(["v16", "--clip", "GX099999", "--dry-run"])
    assert stop.value.code == 2


def test_a_missing_clip_is_a_usage_error(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    assert bench.main(["v16", "--dry-run"]) == 2
    assert "not in the footage folder" in capsys.readouterr().err


def test_too_little_disk_is_a_usage_error(
    folders: LocalConfig, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (folders.footage_path / "GX000001.mp4").write_bytes(b"x" * 1000)

    def usage(path: Any) -> Any:
        return type("Usage", (), {"free": bench.DISK_MARGIN_BYTES})()

    monkeypatch.setattr(bench.shutil, "disk_usage", usage)
    assert bench.main(["run", "GX000001"]) == 2
    assert "BenchError" in capsys.readouterr().err


def test_run_writes_the_record_and_leaves_the_footage_alone(
    folders: LocalConfig, sample: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    clip = folders.footage_path / "Snorkel" / "GX000001.mp4"
    clip.parent.mkdir()
    clip.write_bytes(sample(SAMPLE).read_bytes())
    footage = (clip.read_bytes(), clip.stat().st_mtime_ns)
    argv = ["run", "GX000001", "--encoder", "libx265", "--runs", "2", "--force-cpu"]
    assert bench.main([*argv, "--memory-every", "0.05"]) == 0
    out = capsys.readouterr().out
    rows = [line for line in out.splitlines() if line.startswith("ROW GX000001.mp4 c3 libx265")]
    assert len(rows) == 2
    path = Path(out.strip().splitlines()[-1].removeprefix("RECORD "))
    assert path.parent == folders.working_path / bench.SUBDIR
    record = json.loads(path.read_text(encoding="utf-8"))
    assert len(record["runs"]) == 2 and "failed" not in record
    assert all(run["force_cpu"] for run in record["runs"])
    assert [p.suffix for p in path.parent.iterdir()] == [".json"]  # run folders deleted
    assert (clip.read_bytes(), clip.stat().st_mtime_ns) == footage


def test_a_failed_job_keeps_the_record_and_exits_1(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    (folders.footage_path / "GX000002.mp4").write_bytes(b"\x00" * 64)
    assert bench.main(["run", "GX000002", "--encoder", "libx265", "--force-cpu"]) == 1
    captured = capsys.readouterr()
    path = Path(captured.out.strip().splitlines()[-1].removeprefix("RECORD "))
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["failed"]["leg"]["clip"] == "GX000002"
    assert [p.suffix for p in path.parent.iterdir()] == [".json"]
