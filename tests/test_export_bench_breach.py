"""DR-72 controls: persist a memory breach and stop both V16 plan loops."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

import export_bench as bench
from local_config import LocalConfig


@pytest.mark.parametrize("breach_at", [0, 1, 2])
def test_v16_stops_on_memory_breach_and_keeps_records(tmp_path, monkeypatch, breach_at):
    calls, records, status = _plan(tmp_path, monkeypatch, breach_at=breach_at)
    assert status == 3
    assert calls == ["first", "first", "later"][: breach_at + 1]
    assert [r["ordinal"] for r in records] == list(range(breach_at + 1))
    assert records[-1]["memory_check"]["passes"] is False


@pytest.mark.parametrize(
    "memory_check", [{"applies": True, "passes": True}, {"applies": False}, None]
)
def test_v16_continues_without_a_memory_breach(tmp_path, monkeypatch, memory_check):
    calls, records, status = _plan(tmp_path, monkeypatch, memory_check=memory_check)
    assert status == 0
    assert calls == ["first", "first", "later", "last"]
    assert len(records) == 4


def test_v16_preserves_job_failure_status(tmp_path, monkeypatch):
    calls, records, status = _plan(tmp_path, monkeypatch, failed=True)
    assert status == 1
    assert calls == ["first"]
    assert records[0]["failure"] == "planted job failure"


def test_v16_stops_when_device_peak_is_unmeasured(tmp_path, monkeypatch, capsys):
    check = bench.memory_check(
        {
            "leg": {"method": "c3"},
            "telemetry": {"peak_gpu_memory_used_mib": None},
        },
        SimpleNamespace(memory_estimate_bytes=lambda *_: 1024),
        SimpleNamespace(video=SimpleNamespace(height=6, width=8)),
        512,
    )
    calls, records, status = _plan(tmp_path, monkeypatch, memory_check=check)
    assert status == 3 and calls == ["first"]
    assert records[0]["memory_check"]["device_peak_mib"] is None
    assert (
        "memory check failed (a breach, or the device peak unmeasured)" in capsys.readouterr().out
    )


def test_v16_preserves_failure_when_memory_check_also_fails(tmp_path, monkeypatch):
    calls, _, status = _plan(tmp_path, monkeypatch, breach_at=0, failed=True)
    assert status == 3 and calls == ["first"]
    path = next((tmp_path / "work/wp5.2/bench").glob("*.json"))
    assert json.loads(path.read_text())["failed"] == {
        "leg": {
            "clip": "first",
            "runs": 2,
            "cache": "cold",
            "method": "c3",
            "encoder": "auto",
            "quality": "standard",
        },
        "error": "planted job failure",
    }


def test_run_subcommand_stops_after_memory_check_failure(tmp_path, monkeypatch):
    calls, records, status = _plan(tmp_path, monkeypatch, breach_at=0, command="run")
    assert status == 3 and calls == ["first"] and len(records) == 1


def _plan(tmp_path, monkeypatch, *, breach_at=None, memory_check=..., failed=False, command="v16"):
    config = LocalConfig(footage_path=tmp_path / "footage", working_path=tmp_path / "work")
    calls = []
    monkeypatch.setattr(bench, "load_local_config", lambda _: config)
    monkeypatch.setattr(bench, "find_footage_file", lambda stem, _: tmp_path / f"{stem}.mp4")
    monkeypatch.setattr(bench, "check_disk", lambda *_: None)
    monkeypatch.setattr(bench, "row_line", lambda _: "ROW planted")
    monkeypatch.setattr(
        bench, "V16_PLAN", (bench.Leg("first", 2), bench.Leg("later", 1), bench.Leg("last", 1))
    )

    def run_once(path: Path, folder: Path, leg: bench.Leg, **kwargs):
        ordinal = len(calls)
        calls.append(leg.clip)
        return {
            "ok": not failed,
            "failure": "planted job failure" if failed else None,
            "ordinal": ordinal,
            "memory_check": memory_check
            if memory_check is not ...
            else {"applies": True, "passes": ordinal != breach_at},
        }

    monkeypatch.setattr(bench, "run_once", run_once)
    args = [command, "--subdir", "wp5.2/bench"]
    if command == "run":
        args += ["first", "--runs", "3"]
    status = bench.main(args)
    paths = list((config.working_path / "wp5.2/bench").glob("*.json"))
    assert len(paths) == 1
    return calls, json.loads(paths[0].read_text(encoding="utf-8"))["runs"], status
