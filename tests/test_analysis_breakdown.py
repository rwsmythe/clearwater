"""Tests of the WP3.21 task 1 instrument ``tools/analysis_breakdown.py`` (question 6).

No footage: the runs use a WP2.3 sample copied into a footage folder made under ``tmp_path``, on
the CPU. The figures themselves are taken only in an exclusive window; here the step clock's
arithmetic, the timing wrappers, the replica-against-engine equality (and that it can fail), the
record's shape, the cleanup and the refusal of an output inside the footage folder are checked.
"""

from __future__ import annotations

import json
import types
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import analysis_breakdown as bd
from clearwater.analysis.proxy import block_mean, make_proxy, proxy_factor, quantise
from local_config import LocalConfig

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

SAMPLE = "vid-hevc8-bt709-full"
FAST = (0.05, 0.5)


def test_phase_summary_sums_the_step_means_against_the_mean_wall() -> None:
    clock = bd.StepClock(lambda: None)
    for steps, wall in (({"a": 1.0, "b": 2.0}, 3.0), ({"a": 3.0}, 4.0)):
        clock.begin()
        for name, seconds in steps.items():
            clock.add(name, seconds)
        clock.end(wall)
    summary = bd.phase_summary(clock, 10.0, 17.5)
    assert summary["frames"] == 2 and summary["wall_s"] == 7.5
    assert list(summary["steps"]) == ["a", "b"]
    assert summary["steps"]["a"]["mean"] == 2.0 and summary["steps"]["a"]["total_s"] == 4.0
    assert summary["steps"]["b"]["mean"] == 1.0  # the frame without "b" counts zero
    assert summary["sum_of_means_s"] == 3.0 and summary["mean_wall_s"] == 3.5
    assert summary["residual"] == pytest.approx(0.5 / 3.5)
    assert summary["within_limit"] is False  # 14 % unattributed is a finding
    assert summary["first_wall_s"] == 3.0


def test_the_step_clock_times_a_call_and_synchronises_device_steps() -> None:
    synced: list[str] = []
    clock = bd.StepClock(lambda: synced.append("sync"))
    clock.begin()
    assert clock.time("host", lambda x, y: x + y, 2, 3) == 5
    assert synced == []
    assert clock.time("device", lambda: "done", device=True) == "done"
    assert synced == ["sync"]
    clock.end(1.0)
    assert set(clock.frames[0]) == {"host", "device", "wall"}
    assert clock.time_once("close", lambda: 7) == 7 and "close" in clock.once


def test_timed_name_wraps_the_module_name_and_restores_it() -> None:
    module = types.ModuleType("fake")

    def work(x: int) -> int:
        if x < 0:
            raise ValueError("negative")
        return 2 * x

    module.work = work  # type: ignore[attr-defined]
    timer = bd.Accumulator()
    with bd.timed_name(module, "work", timer):
        assert module.work is not work  # type: ignore[attr-defined]
        assert module.work(4) == 8  # type: ignore[attr-defined]
        with pytest.raises(ValueError, match="negative"):
            module.work(-1)  # type: ignore[attr-defined]
    assert module.work is work  # type: ignore[attr-defined]
    assert timer.calls == 2 and timer.take() >= 0 and timer.seconds == 0.0


def test_the_replicas_proxy_steps_are_make_proxy() -> None:
    rng = np.random.default_rng(3)
    pixels = rng.integers(0, 256, (1081, 1923, 3)).astype(np.float32) / np.float32(255)
    k = proxy_factor(*pixels.shape[:2])
    assert np.array_equal(quantise(block_mean(pixels, k)), make_proxy(pixels))


def test_refuse_inside_refuses_the_footage_folder_and_below(tmp_path: Path) -> None:
    footage = tmp_path / "footage"
    for inside in (footage, footage / "wp3.21" / "breakdown"):
        with pytest.raises(bd.BreakdownError, match="inside the footage folder"):
            bd.refuse_inside(inside, footage)
    bd.refuse_inside(tmp_path / "work" / "wp3.21", footage)
    bd.refuse_inside(tmp_path / "footage-other", footage)


def test_same_record_compares_dtype_shape_and_bytes() -> None:
    a = {"means": np.array([0.1, 0.2, 0.3])}
    assert bd.same_record(a, {"means": np.array([0.1, 0.2, 0.3])})
    assert not bd.same_record(a, {"means": np.array([0.1, 0.2, np.nextafter(0.3, 1)])})
    assert not bd.same_record(a, {"means": np.array([0.1, 0.2, 0.3], dtype=np.float32)})
    assert not bd.same_record(a, {"means": a["means"], "gains": a["means"]})


def test_run_records_every_phase_and_the_replica_equals_the_engine(
    sample: Any, tmp_path: Path
) -> None:
    source = sample(SAMPLE)
    before = (source.read_bytes(), source.stat().st_mtime_ns)
    run_dir = tmp_path / "run-0"
    record = bd.run(source, run_dir, "c3", force_cpu=True, profile=True, frames=True, periods=FAST)
    assert record["device"] == "CPU: forced" and record["hw_decode"] is False
    phases = record["phases"]
    decode = phases["decode_pass"]
    assert decode["frames"] == 45
    assert list(decode["steps"]) == [
        "decode_wait",
        "planes_to_rgb",
        "check",
        "frame_pixels_on_host",
        "block_mean",
        "quantise",
        "store_proxy",
        "proxy",
        "proxy_image",
        "analyze",
        "store_puts",
        "report",
    ]
    assert "finish" in decode["once"]
    assert list(phases["later_stages"]) == ["white_balance", "fusion"]
    assert phases["later_stages"]["white_balance"]["frames"] == 0  # measured in the pass
    assert phases["later_stages"]["fusion"]["frames"] == 45
    assert all("smooth" in table["once"] for table in phases["later_stages"].values())
    frame_path = phases["frame_path"]
    assert frame_path["frames"] == 45 and "close" in frame_path["once"]
    assert {"render", "upload", "to_host", "rgb_to_planes", "sink_write"} <= set(
        frame_path["steps"]
    )
    for table in (decode, phases["later_stages"]["fusion"], frame_path):
        assert table["sum_of_means_s"] <= table["mean_wall_s"] * 1.000001
    assert record["equality"]["equal"], record["equality"]
    assert record["equality"]["proxies_compared"] == 45
    assert record["equality"]["records_compared"] == 45 * 2 * 2
    assert record["sink"]["frames_written"] == 45
    assert record["timer_calls"] == {"planes_to_rgb": 45 * 3, "rgb_to_planes": 45}
    assert record["profile"]["frames"] == 45
    assert Path(record["profile"]["summary"]).is_file()
    assert set(record["gpu_by_phase"]) == {
        "decode_pass",
        "later_stages",
        "engine_profiled",
        "frame_path",
    }
    assert (source.read_bytes(), source.stat().st_mtime_ns) == before
    with pytest.raises(bd.BreakdownError, match="never reuses"):
        bd.run(source, run_dir, "c3", force_cpu=True, profile=False, frames=False)


def test_the_equality_check_fails_when_the_replica_differs(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A planted difference in the replica's stage-1 records must be reported, not absorbed.
    original = bd._store_first

    def perturbed(engine: Any, pts: int, record: Any, schema: str) -> None:
        changed = dict(record)
        changed["means"] = np.asarray(record["means"]) + 1e-12
        original(engine, pts, changed, schema)

    monkeypatch.setattr(bd, "_store_first", perturbed)
    record = bd.run(
        sample(SAMPLE), tmp_path / "run", "c3", force_cpu=True, profile=True, frames=False,
        periods=FAST,
    )  # fmt: skip
    assert record["equality"]["equal"] is False
    assert record["equality"]["differences"][0].startswith("raw white_balance at pts ")


# --- the command line ------------------------------------------------------------------------


@pytest.fixture
def folders(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> LocalConfig:
    config = LocalConfig(footage_path=tmp_path / "footage", working_path=tmp_path / "work")
    config.footage_path.mkdir()
    monkeypatch.setattr(bd, "load_local_config", lambda path=None: config)
    return config


def test_main_writes_the_record_and_deletes_the_run_folder(
    folders: LocalConfig, sample: Any, capsys: pytest.CaptureFixture[str]
) -> None:
    clip = folders.footage_path / "Snorkel" / "GX000001.mp4"
    clip.parent.mkdir()
    clip.write_bytes(sample(SAMPLE).read_bytes())
    footage = (clip.read_bytes(), clip.stat().st_mtime_ns)
    assert bd.main(["GX000001", "--force-cpu", "--memory-every", "0.05"]) == 0
    out = capsys.readouterr().out
    assert "CHECK replica equals engine: yes" in out
    path = Path(out.strip().splitlines()[-1].removeprefix("RECORD "))
    assert path.parent == folders.working_path / bd.SUBDIR
    record = json.loads(path.read_text(encoding="utf-8"))
    assert record["equality"]["equal"] and "failed" not in record
    left = sorted(p.name for p in path.parent.iterdir())
    assert left == sorted([path.name, f"{path.stem}.prof", f"{path.stem}-profile.txt"])
    assert (clip.read_bytes(), clip.stat().st_mtime_ns) == footage
    assert sorted(p.name for p in folders.footage_path.rglob("*")) == ["GX000001.mp4", "Snorkel"]


def test_main_refuses_a_working_folder_inside_the_footage_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    footage = tmp_path / "footage"
    footage.mkdir()
    (footage / "GX000001.mp4").write_bytes(b"x")
    config = LocalConfig(footage_path=footage, working_path=footage / "work")
    monkeypatch.setattr(bd, "load_local_config", lambda path=None: config)
    assert bd.main(["GX000001"]) == 2
    assert "inside the footage folder" in capsys.readouterr().err
    assert [p.name for p in footage.iterdir()] == ["GX000001.mp4"]


def test_a_missing_clip_is_a_usage_error(
    folders: LocalConfig, capsys: pytest.CaptureFixture[str]
) -> None:
    assert bd.main(["GX099999"]) == 2
    assert "not in the footage folder" in capsys.readouterr().err
    assert not folders.working_path.exists()
