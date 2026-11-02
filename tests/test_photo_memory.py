"""Seat-only photo adapter boundaries and fresh default/CPU record controls."""

import importlib
import importlib.util
import json

import pytest

import photo_verify as pv
from fixtures.stills import png16_bytes, quantize, unit_content
from local_config import LocalConfig


@pytest.fixture
def adapter():
    assert importlib.util.find_spec("photo_memory") is not None, "photo adapter has not been built"
    return importlib.import_module("photo_memory")


@pytest.fixture
def configured(tmp_path, monkeypatch, adapter):
    config = LocalConfig(footage_path=tmp_path / "footage", working_path=tmp_path / "work")
    root = config.working_path / "wp5.2"
    root.mkdir(parents=True)
    source = root / "W52-2-small.png"
    source.write_bytes(png16_bytes(quantize(unit_content("lowred", 8, 6), 16), None, "sRGB"))
    monkeypatch.setattr(adapter, "load_local_config", lambda _: config)
    return config, source


@pytest.mark.parametrize("location", ["outside", "sibling", "footage", "missing", "directory"])
def test_photo_memory_refuses_input_locations(adapter, configured, tmp_path, location):
    config, source = configured
    inputs = {
        "outside": tmp_path / "outside.png",
        "sibling": config.working_path / "wp5.20/input.png",
        "footage": config.footage_path / "input.png",
        "missing": source.with_name("missing.png"),
        "directory": source.parent,
    }
    if location in {"outside", "sibling", "footage"}:
        inputs[location].parent.mkdir(parents=True, exist_ok=True)
        inputs[location].write_bytes(source.read_bytes())
    assert adapter.main(["measure", str(inputs[location]), "--name", "W52-2", "--exclusive"]) == 2
    assert not (source.parent / "photo").exists()


def test_photo_memory_refuses_non_rgb16_input(adapter, configured):
    _, source = configured
    data = bytearray(source.read_bytes())
    data[24] = 8
    source.write_bytes(data)
    assert adapter.main(["measure", str(source), "--name", "W52-2", "--exclusive"]) == 2
    assert not (source.parent / "photo").exists()


def test_photo_memory_requires_exclusive_declaration(adapter, configured):
    _, source = configured
    with pytest.raises(SystemExit) as error:
        adapter.main(["measure", str(source), "--name", "W52-2"])
    assert error.value.code == 2
    assert not (source.parent / "photo").exists()


@pytest.fixture
def memory_seam(configured, monkeypatch):
    _, source = configured
    calls = []
    facts = {"reason": "GPU", "peak": 9000, "active": 2, "exit": 0, "device": True}

    class Sampler:
        def __init__(self, process):
            pass

        def start(self):
            pass

        def stop(self):
            pass

        def record(self):
            return {
                "rss_baseline_bytes": 1000,
                "rss_tree_peak_bytes": facts["peak"],
                "os_peak_working_set_bytes": 9500,
                "device_used_baseline_bytes": 2000,
                "device_used_peak_bytes": 5000,
                "rss_samples": 3,
                "device_samples": 2,
                "rss_active_samples": facts["active"],
                "device_active_samples": 2,
                "sample_intervals_s": {"rss": 0.05, "device": 0.2},
                "sample_interval_kind": "wait-after-sample",
                "sampling_cadence_s": {"rss": {"max": 0.06}, "device": {"max": 0.21}},
                "sampler_elapsed_s": 0.25,
                "sampler_errors": [],
                "rss_scope": "tool-runner-tree-including-sampler-children",
            }

    def runner(src, out, record_path, settings_dir, *, bit_depth, force_cpu, neutral):
        assert src == source.resolve() and bit_depth == 16 and neutral is False
        assert pv._ACTIVE_GUARD.get().check(out) == out
        assert pv._ACTIVE_SAMPLER.get() is not None
        calls.append(force_cpu)
        raw = {"items": [{"device": "CPU: forced" if force_cpu else facts["reason"]}]}
        record_path.write_text(json.dumps(raw), encoding="ascii")
        return facts["exit"], raw

    monkeypatch.setattr(pv, "MemorySampler", Sampler)
    monkeypatch.setattr(pv, "launch_runner", runner)
    monkeypatch.setattr(
        pv,
        "device_memory",
        lambda: (
            {"free_bytes": 10_000_000, "total_bytes": 20_000_000, "used_bytes": 5000}
            if facts["device"]
            else None
        ),
    )
    return facts, calls


def _records(source):
    records = [
        json.loads(p.read_text(encoding="ascii"))
        for p in sorted((source.parent / "photo").glob("W52-2-*/*record.json"))
    ]
    assert len(records) == 2
    return sorted(records, key=lambda r: r["force_cpu"])


def test_photo_memory_two_legs_have_5d_keys(adapter, configured, memory_seam):
    _, source = configured
    before = source.read_bytes()
    _, calls = memory_seam
    assert adapter.main(["measure", str(source), "--name", "W52-2", "--exclusive"]) == 0
    assert calls == [False, True]
    records = _records(source)
    for record, reason in zip(records, ["GPU", "CPU: forced"], strict=True):
        assert record["schema"] == 1 and record["command"] == "memory"
        assert record["stored_size"] == [8, 6] and record["method"] == "c3"
        assert record["file"] == source.name and record["class"] == "synthetic-png16"
        assert record["force_cpu"] == record["forced_cpu"] == (reason == "CPU: forced")
        assert record["exclusive"] is True and record["device_reason"] == reason
        assert record["rss_tree_peak_bytes"] == 9000 and record["device_used_peak_bytes"] == 5000
        assert record["ram_limit_bytes"] == 16_000_000_000
        assert record["device_limit_bytes"] == 8188 * 2**20
        assert record["runner_exit"] == 0 and record["read_ok"] is True
        assert record["failed_checks"] == []
        assert record["ram_within_limit"] is True and record["device_within_limit"] is True
        assert record["estimate_bytes"] > 0 and record["estimate_fits_free_before"] is True
        assert record["estimate_exceeds_free_before"] is False
        assert record["device_free_before_bytes"] == 10_000_000
        assert record["device_total_bytes"] == 20_000_000
        assert record["automatic_fallback"] is False and record["memory_capacity_fallback"] is False
        assert record["sampling_cadence_s"]["rss"]["max"] == 0.06
        assert record["sampler_errors"] == [] and record["measured_at_utc"]
    assert source.read_bytes() == before
    assert pv._ACTIVE_GUARD.get() is None and pv._ACTIVE_SAMPLER.get() is None


@pytest.mark.parametrize(
    "defect,expected",
    [
        ("peak", "memory_ram_limit"),
        ("active", "memory_rss_measurement"),
        ("device", "memory_device_measurement"),
        ("exit", "runner_failed"),
    ],
)
def test_photo_memory_does_not_pass_incomplete_or_breached_measurements(
    adapter, configured, memory_seam, defect, expected
):
    _, source = configured
    facts, calls = memory_seam
    facts[defect] = {"peak": 16_000_000_001, "active": 0, "device": False, "exit": 1}[defect]
    assert adapter.main(["measure", str(source), "--name", "W52-2", "--exclusive"]) == 1
    assert calls == [False, True]
    assert all(expected in r["failed_checks"] for r in _records(source))


def test_photo_memory_reports_capacity_fallback(adapter, configured, memory_seam):
    _, source = configured
    facts, _ = memory_seam
    facts["reason"] = "CPU: estimate 12,000 MiB exceeds free 7,000 MiB"
    assert adapter.main(["measure", str(source), "--name", "W52-2", "--exclusive"]) == 0
    default, cpu = _records(source)
    assert default["device_reason"] == facts["reason"]
    assert default["automatic_fallback"] is True and default["memory_capacity_fallback"] is True
    assert cpu["automatic_fallback"] is False and cpu["memory_capacity_fallback"] is False
