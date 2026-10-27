"""WP3.14 tests: the headless batch (G7, G8; D45, D81) over the export engine's doubles."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pytest

from clearwater.interfaces import JobResult
from clearwater.interfaces.stubs import StubProgress
from clearwater.jobs import run_batch
from clearwater.jobs.export_seam import CANCELLED, ExportRequest
from test_jobs_export_support import FakeSink, Rig


def _sources(rig: Rig) -> list[Path]:
    paths = []
    for name in ("a.mp4", "b.mp4", "c.mp4"):
        path = rig.folder / name
        path.write_bytes(b"video")
        paths.append(path)
    return paths


def test_d81_a_failed_item_is_logged_and_the_batch_continues(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    rig = Rig(tmp_path)
    made = iter([FakeSink(), FakeSink(), FakeSink()])

    def next_sink() -> FakeSink:
        sink = next(made)
        if len(rig.sinks) == 1:
            sink.fail_at = 2
            sink.fail_error = BrokenPipeError("encoder died")
        return sink

    rig.next_sink = next_sink
    requests = [rig.request(source=p) for p in _sources(rig)]
    with caplog.at_level(logging.INFO, logger="clearwater.jobs.batch"):
        report = run_batch(rig.engine, requests, StubProgress())
    assert [i.state for i in report.items] == ["done with warnings", "failed", "done with warnings"]
    assert report.items[1].result is not None
    assert report.items[1].result.failure == "b.mp4: BrokenPipeError: encoder died"
    assert (tmp_path / "a_corrected.mp4").exists() and (tmp_path / "c_corrected.mp4").exists()
    assert not (tmp_path / "b_corrected.mp4").exists()
    assert any("item 2 of 3 failed" in r.getMessage() for r in caplog.records)
    assert report.counts() == {
        "done": 0, "done with warnings": 2, "failed": 1, "cancelled": 0, "not run": 0,
    }  # fmt: skip
    text = report.lines()
    assert text[0] == "Batch of 3: 2 done with warnings, 1 failed"
    assert "   failure: b.mp4: BrokenPipeError: encoder died" in text


def test_d45_cancel_during_the_second_item_stops_the_rest_and_keeps_the_first(
    tmp_path: Path,
) -> None:
    rig = Rig(tmp_path)
    progress = StubProgress()
    requests = [rig.request(source=p) for p in _sources(rig)]
    real_report = progress.report

    def report(done: int, total: int | None, message: str) -> None:
        real_report(done, total, message)
        if message.startswith("[2/3] Exporting") and done == 3:
            progress.cancel()

    progress.report = report  # type: ignore[method-assign]
    batch = run_batch(rig.engine, requests, progress)
    assert [i.state for i in batch.items] == ["done with warnings", "cancelled", "not run"]
    assert batch.items[1].result is not None and batch.items[1].result.failure is CANCELLED
    assert batch.items[2].result is None
    assert (tmp_path / "a_corrected.mp4").exists()
    assert sorted(p.name for p in tmp_path.iterdir()) == [
        "a.mp4", "a_corrected.mp4", "b.mp4", "c.mp4", "clip.mp4", "shot.png",
    ]  # fmt: skip
    assert len(rig.sinks) == 2


def test_a_job_that_raises_is_a_failed_item(tmp_path: Path) -> None:
    class Raising:
        def __init__(self) -> None:
            self.calls = 0

        def job(self, request: ExportRequest) -> Any:
            self.calls += 1
            if self.calls == 1:
                raise ValueError("malformed")
            return lambda progress: JobResult(True, (), (), None, "cpu", 0.0)

    rig = Rig(tmp_path)
    requests = [rig.request(source=p) for p in _sources(rig)[:2]]
    report = run_batch(Raising(), requests, StubProgress())
    assert [i.state for i in report.items] == ["failed", "done"]
    assert report.items[0].result is not None
    assert report.items[0].result.failure == "a.mp4: ValueError: malformed"


def test_a_cancel_before_the_batch_runs_nothing(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    progress = StubProgress()
    progress.cancel()
    report = run_batch(rig.engine, [rig.request(source=p) for p in _sources(rig)], progress)
    assert [i.state for i in report.items] == ["not run"] * 3 and rig.sinks == []
