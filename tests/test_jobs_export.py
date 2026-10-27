"""WP3.14 tests: the export engine over doubles (the seam, cancel, failure, D87, settings, N8).

No FFmpeg and no GPU: the video source, sink, photo reader and writer are doubles from
``test_jobs_export_support``; the method is the analysis tests' two-stage ``GrayWorld``. The
end-to-end legs on real files are in ``test_jobs_export_video.py`` and
``test_jobs_export_photo.py``.
"""

from __future__ import annotations

import ast
import errno
import json
import logging
import os
import re
import threading
import time
from pathlib import Path
from typing import Any

import pytest

import clearwater.jobs
from clearwater.interfaces import JobResult, Settings
from clearwater.interfaces.stubs import StubProgress
from clearwater.jobs import Reservations, SafeWrite, is_reserved_device_name, run_batch
from clearwater.jobs import disk_space as disk_space_module
from clearwater.jobs import export as export_module
from clearwater.jobs import naming as naming_module
from clearwater.jobs import safe_write as safe_write_module
from clearwater.jobs.export_seam import CANCELLED, ExportJobs, ExportRequest
from test_jobs_export_support import CLOSE_GATES, FakeSink, Rig, parameter_set

BLOCK_BOUND_S = 3.0
"""A cancel during a blocked write must end the job well within this (the double blocks 5 s)."""


class CancelAt(StubProgress):
    """A progress that cancels itself at the first report whose message contains ``marker``."""

    def __init__(self, marker: str) -> None:
        super().__init__()
        self.marker = marker

    def report(self, done: int, total: int | None, message: str) -> None:
        super().report(done, total, message)
        if self.marker in message:
            self.cancel()


_FINAL_STEMS = ("clip_corrected", "shot_corrected")
"""The stems of the rig's planned finals (numbered ones included: ``clip_corrected_2.mp4``)."""


def _no_partials(rig: Rig, keep: tuple[Path, ...] = ()) -> None:
    """Assert no temporary and no final but those in ``keep`` is in the rig's folder."""
    kept = {p.name for p in keep}
    left = [
        n
        for n in rig.files()
        if naming_module.is_temporary_name(n) or (n.startswith(_FINAL_STEMS) and n not in kept)
    ]
    assert left == [], left


def test_no_partials_catches_a_leaked_final_and_a_temporary(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    (tmp_path / "earlier_corrected.mp4").write_bytes(b"an earlier output is not a leak")
    _no_partials(rig)
    for name in ("clip_corrected.mp4", "clip_corrected_2.mp4", "shot_corrected.png"):
        leaked = tmp_path / name
        leaked.write_bytes(b"x")
        with pytest.raises(AssertionError, match=name):
            _no_partials(rig)
        _no_partials(rig, keep=(leaked,))
        leaked.unlink()
    temporary = naming_module.temporary_path(tmp_path / "other.mp4", naming_module.new_token())
    assert naming_module.is_temporary_name(temporary.name)
    temporary.write_bytes(b"x")
    with pytest.raises(AssertionError, match=temporary.name):
        _no_partials(rig)


# --- the seam -------------------------------------------------------------------------------


def test_job_builds_without_touching_any_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    touched: list[str] = []
    for name in ("stat", "open", "listdir", "scandir"):
        real = getattr(os, name)

        def spy(*args: Any, _real: Any = real, _name: str = name, **kwargs: Any) -> Any:
            touched.append(_name)
            return _real(*args, **kwargs)

        monkeypatch.setattr(os, name, spy)
    job = rig.engine.job(rig.request("photo", source=tmp_path / "missing.png"))
    monkeypatch.undo()
    assert callable(job) and touched == []
    result = job(StubProgress())
    assert not result.ok and result.failure != CANCELLED
    assert result.failure.startswith("missing.png: FileNotFoundError: ")
    assert result.outputs == () and result.device == "none"


def test_job_raises_value_error_only_for_a_malformed_request(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    good = rig.request()
    for bad in (
        ExportRequest(good.source, "audio", good.parameters, good.settings),  # type: ignore[arg-type]
        ExportRequest(str(good.source), "video", good.parameters, good.settings),  # type: ignore[arg-type]
        ExportRequest(good.source, "video", {}, good.settings),  # type: ignore[arg-type]
        ExportRequest(good.source, "video", good.parameters, {}),  # type: ignore[arg-type]
    ):
        with pytest.raises(ValueError):
            rig.engine.job(bad)
    engine: ExportJobs = rig.engine
    assert callable(engine.job(good))


def test_ok_video_names_its_committed_output_and_carries_the_sink_warnings(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    progress = StubProgress()
    result = rig.run(rig.request(), progress)
    assert result.ok and result.failure is None, result.failure
    assert result.outputs == (tmp_path / "clip_corrected.mp4",)
    assert result.outputs[0].read_bytes() == b"H" + b"f" * 6
    assert result.warnings == ("sink warning", "Not carried to the output: timecode track")
    assert result.device == "GPU" and result.elapsed_s >= 0
    assert rig.sink.calls == ["capabilities", "open", *["write"] * 6, "close"]
    assert [f.pts_ticks for f in rig.sink.frames] == [f.pts_ticks for f in rig.frames]
    exporting = [r for r in progress.reports if r[2].startswith("Exporting")]
    assert exporting == [(i, 6, "Exporting clip.mp4") for i in range(1, 7)]
    assert any(r[2].startswith("Analysing clip.mp4: ") for r in progress.reports)
    _no_partials(rig, keep=result.outputs)


def test_ok_photo_reports_four_steps(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    progress = StubProgress()
    result = rig.run(rig.request("photo"), progress)
    assert result.ok, result.failure
    assert result.outputs == (tmp_path / "shot_corrected.png",)
    assert [r[:2] for r in progress.reports] == [(0, 4), (1, 4), (2, 4), (3, 4), (4, 4)]


def test_cancel_returns_the_seam_constant_itself(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    progress = StubProgress()
    progress.cancel()
    result = rig.run(rig.request(), progress)
    assert result.failure is CANCELLED and not result.ok and result.outputs == ()


def _assert_cancel_contract(result: JobResult) -> None:
    """The cancel contract: the constant ITSELF (a copy of the string fails here, by name)."""
    assert not result.ok
    assert result.failure is CANCELLED, f"failure is not the CANCELLED constant: {result.failure!r}"


def test_planted_engine_returning_a_copy_of_the_string_fails_by_name() -> None:
    copied = "".join(["cancel", "led"])
    planted = JobResult(False, (), (), copied, "cpu", 0.0)
    with pytest.raises(AssertionError, match="not the CANCELLED constant"):
        _assert_cancel_contract(planted)


def test_a_genuine_failure_never_equals_cancelled(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.method.render = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("cancelled"))  # type: ignore[method-assign]
    result = rig.run(rig.request())
    assert result.failure == "clip.mp4: RuntimeError: cancelled"
    assert result.failure != CANCELLED


# --- cancel at each phase (G8, D44, Q2) -------------------------------------------------------


@pytest.mark.parametrize("marker", ["Preparing", "Analysing", "Exporting"])
def test_cancel_at_each_phase_leaves_nothing(tmp_path: Path, marker: str) -> None:
    rig = Rig(tmp_path)
    earlier = tmp_path / "earlier_corrected.mp4"
    earlier.write_bytes(b"kept")
    result = rig.run(rig.request(), CancelAt(marker))
    _assert_cancel_contract(result)
    assert result.outputs == ()
    assert earlier.read_bytes() == b"kept"
    _no_partials(rig)
    if rig.sinks and "open" in rig.sink.calls:
        assert "abort" in rig.sink.calls and "close" not in rig.sink.calls


def test_cancel_immediately_before_commit_deletes_the_finished_temporary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    progress = StubProgress()
    real_close = FakeSink.close

    def close_then_cancel(self: FakeSink) -> Any:
        report = real_close(self)
        progress.cancel()
        return report

    monkeypatch.setattr(FakeSink, "close", close_then_cancel)
    result = rig.run(rig.request(), progress)
    _assert_cancel_contract(result)
    calls = rig.sink.calls
    after = calls[calls.index("close") + 1 :]  # the watchdog may also see the flag before it stops
    assert after and set(after) == {"abort"}, calls
    _no_partials(rig)


def test_a_stop_after_close_keeps_the_sink_warnings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # R1 F4: the SinkReport's warnings were copied only after commit, so a stop between
    # close and commit lost them (the seam: a non-ok result carries the warnings raised before).
    expected = ("sink warning", "Not carried to the output: timecode track")
    rig = Rig(tmp_path)
    progress = StubProgress()
    real_close = FakeSink.close

    def close_then_cancel(self: FakeSink) -> Any:
        report = real_close(self)
        progress.cancel()
        return report

    monkeypatch.setattr(FakeSink, "close", close_then_cancel)
    result = rig.run(rig.request(), progress)
    _assert_cancel_contract(result)
    assert result.warnings == expected
    monkeypatch.setattr(FakeSink, "close", real_close)

    def refuse(self: SafeWrite) -> Path:
        raise PermissionError(13, "planted commit failure")

    monkeypatch.setattr(SafeWrite, "commit", refuse)
    (tmp_path / "second").mkdir()
    second = Rig(tmp_path / "second")
    result = second.run(second.request())
    assert result.failure == "clip.mp4: PermissionError: [Errno 13] planted commit failure"
    assert result.warnings == expected


def test_a_cancel_at_the_close_boundary_aborts_without_closing(tmp_path: Path) -> None:
    # R1 F1 (a): a cancel seen after the last frame and before close() must not finish the
    # output; the job checks immediately before close (Q2 "between phases").
    progress = StubProgress()
    rig = Rig(tmp_path, on_stage=lambda s: progress.cancel() if s == "close" else None)
    result = rig.run(rig.request(), progress)
    _assert_cancel_contract(result)
    assert "close" not in rig.sink.calls and rig.sink.calls[-1] == "abort"
    assert result.outputs == ()
    _no_partials(rig)


def test_a_cancel_after_commit_is_ok(tmp_path: Path) -> None:
    progress = StubProgress()
    rig = Rig(tmp_path, on_stage=lambda s: progress.cancel() if s == "committed" else None)
    result = rig.run(rig.request(), progress)
    assert result.ok and result.outputs == (tmp_path / "clip_corrected.mp4",)
    assert result.outputs[0].exists()


def _blocked_write_cancel(rig: Rig) -> tuple[JobResult, float]:
    """Cancel while a write is blocked on the encoder; return the result and the seconds taken."""
    progress = StubProgress()
    rig.next_sink = lambda: _blocking_sink()
    box: dict[str, Any] = {}
    thread = threading.Thread(target=lambda: box.update(r=rig.run(rig.request(), progress)))
    thread.start()
    deadline = time.monotonic() + 10
    while not rig.sinks or not rig.sink.blocked.is_set():
        assert time.monotonic() < deadline, "the write never blocked"
        time.sleep(0.01)
    start = time.monotonic()
    progress.cancel()
    thread.join(15)
    return box["r"], time.monotonic() - start


def _blocking_sink() -> FakeSink:
    sink = FakeSink()
    sink.block_at = 2
    return sink


def _assert_released_within_bound(result: JobResult, seconds: float) -> None:
    assert seconds < BLOCK_BOUND_S, f"cancel not released within the bound: {seconds:.1f} s"
    _assert_cancel_contract(result)


def test_cancel_releases_a_write_blocked_on_the_encoder(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    result, seconds = _blocked_write_cancel(rig)
    _assert_released_within_bound(result, seconds)
    assert "abort" in rig.sink.calls and "close" not in rig.sink.calls
    _no_partials(rig)


def test_planted_cancel_polled_only_between_frames_hangs_past_the_bound(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(export_module._Watchdog, "start", lambda self: None)
    rig = Rig(tmp_path)
    result, seconds = _blocked_write_cancel(rig)
    with pytest.raises(AssertionError, match="not released within the bound"):
        _assert_released_within_bound(result, seconds)


def _assert_never_closed_after_a_cancel(sink: FakeSink) -> None:
    assert "close" not in sink.calls, "close called after a cancel"


def test_planted_close_on_cancel_fails_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    real = export_module.ExportEngine._write_frames

    def planted(self: Any, *args: Any) -> None:
        try:
            real(self, *args)
        except export_module._CancelledError:
            args[6].close()  # the sink: a wrong implementation finishing the partial output
            raise

    monkeypatch.setattr(export_module.ExportEngine, "_write_frames", planted)
    rig = Rig(tmp_path)
    rig.run(rig.request(), CancelAt("Exporting"))
    with pytest.raises(AssertionError, match="close called after a cancel"):
        _assert_never_closed_after_a_cancel(rig.sink)


# --- cancel during close (Q2 as amended, CHARC `e7d25105`) ------------------------------------


def _commit_spy(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Record each commit with the cancel watchdogs alive at that moment (none may be)."""
    commits: list[list[str]] = []
    real = SafeWrite.commit
    earlier = set(threading.enumerate())  # only this test's jobs count

    def commit(self: SafeWrite) -> Path:
        alive = [t for t in threading.enumerate() if t not in earlier]
        commits.append([t.name for t in alive if t.name == "export-cancel"])
        return real(self)

    monkeypatch.setattr(SafeWrite, "commit", commit)
    return commits


@pytest.mark.parametrize("gate", CLOSE_GATES)
def test_a_cancel_during_close_is_aborted_by_the_watchdog_at_every_timing(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    gate: str,
) -> None:
    # The watchdog stays alive through close(): abort before the flush, during it, after the
    # finish but before the sink marks itself closed, and after that mark each end CANCELLED
    # with nothing on disk, and close is never followed by commit.
    caplog.set_level(logging.INFO, logger="clearwater.jobs.export")
    commits = _commit_spy(monkeypatch)
    rig = Rig(tmp_path)
    sink = FakeSink()
    sink.close_gate = gate
    rig.next_sink = lambda: sink
    progress = StubProgress()
    box: dict[str, Any] = {}
    thread = threading.Thread(target=lambda: box.update(r=rig.run(rig.request(), progress)))
    thread.start()
    assert sink.at_gate.wait(10), "close never reached the gate"
    progress.cancel()
    aborted = sink.aborted_in_close.wait(BLOCK_BOUND_S)
    sink.release.set()
    thread.join(15)
    assert not thread.is_alive(), "the job did not end"
    assert aborted, "the watchdog never aborted during close"
    _assert_cancel_contract(box["r"])
    assert box["r"].outputs == ()
    assert commits == [], "close was followed by commit"
    assert sink.calls.count("close") == 1
    assert sink.calls.index("abort") > sink.calls.index("close")
    if gate in ("before_flush", "flush"):  # close raised: its error is a log line, not the failure
        assert "the stopped encoder reported RuntimeError: encoder_failed" in caplog.text
    _no_partials(rig)


def test_the_watchdog_is_joined_before_commit(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    commits = _commit_spy(monkeypatch)
    rig = Rig(tmp_path)
    assert rig.run(rig.request()).ok
    assert commits == [[]], "a cancel watchdog was alive at the rename"


# --- failure (V11, D87, DR-57 (c), DR-20 (7)) --------------------------------------------------


def test_disk_full_from_the_sink_is_named_and_leaves_nothing(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    sink = FakeSink()
    sink.fail_at = 3
    rig.next_sink = lambda: sink
    result = rig.run(rig.request())
    assert not result.ok and result.outputs == ()
    assert result.failure.startswith("clip.mp4: disk full while writing clip_corrected.mp4: ")
    assert "No space left on device" in result.failure
    assert "close" not in sink.calls and "abort" in sink.calls
    _no_partials(rig)


def test_disk_full_from_the_photo_writer_is_named_and_leaves_nothing(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.writer.error = OSError(errno.ENOSPC, "No space left on device")
    result = rig.run(rig.request("photo"))
    assert result.failure.startswith("shot.png: disk full while writing shot_corrected.png")
    _no_partials(rig)


def test_disk_full_is_found_through_the_cause_chain(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    sink = FakeSink()
    sink.fail_at = 1
    wrapped = RuntimeError("encoder_failed: the write failed")
    wrapped.__cause__ = OSError(errno.ENOSPC, "No space left on device")
    sink.fail_error = wrapped
    rig.next_sink = lambda: sink
    result = rig.run(rig.request())
    assert "disk full while writing" in result.failure
    assert result.failure.endswith("RuntimeError: encoder_failed: the write failed")


def test_an_encoder_killed_mid_stream_keeps_the_original_error(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    sink = FakeSink()
    sink.fail_at = 2
    sink.fail_error = BrokenPipeError("the encoder ended early")
    rig.next_sink = lambda: sink
    result = rig.run(rig.request())
    assert result.failure == "clip.mp4: BrokenPipeError: the encoder ended early"
    _no_partials(rig)


def test_a_method_error_leaves_nothing_and_never_closes(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.method.render = lambda *a, **k: (_ for _ in ()).throw(ValueError("bad gains"))  # type: ignore[method-assign]
    result = rig.run(rig.request())
    assert result.failure == "clip.mp4: ValueError: bad gains"
    assert "close" not in rig.sink.calls and "abort" in rig.sink.calls
    _no_partials(rig)


def test_a_temporary_that_cannot_be_deleted_is_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    sink = FakeSink()
    sink.fail_at = 1
    sink._delete = lambda: None  # type: ignore[method-assign]
    rig.next_sink = lambda: sink
    real_unlink = Path.unlink

    def refuse(self: Path, missing_ok: bool = False) -> None:
        if naming_module.is_temporary_name(self.name):
            raise PermissionError(13, "in use")
        real_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(Path, "unlink", refuse)
    result = rig.run(rig.request())
    assert result.failure.startswith("clip.mp4: disk full while writing")
    assert len(result.warnings) == 1
    assert "could not be removed; it is removed at the next start" in result.warnings[0]


_LEFTOVER = "could not be removed; it is removed at the next start"


def test_a_temporary_left_after_a_successful_commit_is_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # R1 F3: commit() links the final and then removes the temporary; when that removal fails
    # the job is ok but the leftover must still be reported (DR-57 (c), D85).
    monkeypatch.setattr(safe_write_module, "_unlink_quietly", lambda path: None)
    rig = Rig(tmp_path)
    result = rig.run(rig.request())
    assert result.ok and result.outputs == (tmp_path / "clip_corrected.mp4",), result.failure
    assert [w for w in result.warnings if _LEFTOVER in w] != [], result.warnings
    assert any(naming_module.is_temporary_name(n) for n in rig.files())


def test_a_temporary_left_by_a_failed_begin_is_a_warning(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # R1 F3: when SafeWrite's begin fails after creating the temporary and its abort cannot
    # remove it, the leftover must reach the result (the write was not yet the job's).
    real_begin = SafeWrite.begin

    def begin_then_fail(self: SafeWrite) -> Path:
        real_begin(self)
        raise OSError(5, "planted begin failure")

    real_unlink = Path.unlink

    def refuse(self: Path, missing_ok: bool = False) -> None:
        if naming_module.is_temporary_name(self.name):
            raise PermissionError(13, "in use")
        real_unlink(self, missing_ok=missing_ok)

    monkeypatch.setattr(SafeWrite, "begin", begin_then_fail)
    monkeypatch.setattr(Path, "unlink", refuse)
    for kind in ("video", "photo"):
        folder = tmp_path / kind
        folder.mkdir()
        rig = Rig(folder)
        result = rig.run(rig.request(kind))
        assert result.failure.endswith("OSError: [Errno 5] planted begin failure"), result.failure
        assert [w for w in result.warnings if _LEFTOVER in w] != [], (kind, result.warnings)


class _CloseRaises:
    """A decode iterator whose ``close`` raises (a cleanup error)."""

    def __init__(self, frames: Any) -> None:
        self._frames = iter(frames)

    def __iter__(self) -> _CloseRaises:
        return self

    def __next__(self) -> Any:
        return next(self._frames)

    def close(self) -> None:
        raise OSError("cleanup close failed")


def test_a_stream_close_error_never_replaces_the_original_failure(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    # R1 F2: the decode stream's close ran unguarded in a finally, so its error replaced the
    # render error (ladder 5: "a cleanup error is a log line or a warning, never the failure").
    stages: list[str] = []
    rig = Rig(tmp_path, on_stage=stages.append)
    real_frames = rig.source.frames

    def frames(*args: Any, **kwargs: Any) -> Any:
        stream = real_frames(*args, **kwargs)
        return _CloseRaises(stream) if "frames" in stages else stream

    rig.source.frames = frames  # type: ignore[method-assign]
    rig.method.render = lambda *a, **k: (_ for _ in ()).throw(ValueError("ORIGINAL render failed"))  # type: ignore[method-assign]
    with caplog.at_level(logging.WARNING, logger="clearwater.jobs.export"):
        result = rig.run(rig.request())
    assert result.failure == "clip.mp4: ValueError: ORIGINAL render failed"
    assert "cleanup close failed" in caplog.text
    assert "close" not in rig.sink.calls and "abort" in rig.sink.calls
    _no_partials(rig)


def test_a_stop_after_commit_still_lists_the_committed_file(tmp_path: Path) -> None:
    def stop(stage: str) -> None:
        if stage == "committed":
            raise RuntimeError("planted stop after commit")

    rig = Rig(tmp_path, on_stage=stop)
    result = rig.run(rig.request())
    assert not result.ok and result.failure == "clip.mp4: RuntimeError: planted stop after commit"
    assert result.outputs == (tmp_path / "clip_corrected.mp4",) and result.outputs[0].exists()


def test_nothing_is_written_after_commit_and_earlier_outputs_are_untouched(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    taken = tmp_path / "clip_corrected.mp4"
    taken.write_bytes(b"an earlier export")
    stamp = taken.stat().st_mtime_ns
    snapshot: dict[str, bytes] = {}
    rig.engine._on_stage = lambda s: (  # type: ignore[assignment]
        snapshot.update({p.name: p.read_bytes() for p in tmp_path.iterdir()})
        if s == "committed"
        else None
    )
    result = rig.run(rig.request())
    assert result.outputs == (tmp_path / "clip_corrected_2.mp4",)
    assert taken.read_bytes() == b"an earlier export" and taken.stat().st_mtime_ns == stamp
    assert {p.name: p.read_bytes() for p in tmp_path.iterdir()} == snapshot


# --- D87 and DR-48 ---------------------------------------------------------------------------


def _free(monkeypatch: pytest.MonkeyPatch, free: int) -> None:
    usage = type("Usage", (), {"total": free, "used": 0, "free": free})
    monkeypatch.setattr(disk_space_module.shutil, "disk_usage", lambda path: usage)


@pytest.mark.parametrize("kind", ["video", "photo"])
def test_d87_refuses_before_any_write_with_both_figures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    rig = Rig(tmp_path)
    _free(monkeypatch, 10)
    result = rig.run(rig.request(kind))
    assert not result.ok
    assert "Not enough free space" in result.failure and "10 free" in result.failure
    assert rig.files() == ["clip.mp4", "shot.png"]
    if kind == "video":
        assert "open" not in rig.sink.calls and rig.source.iterations == 0  # before analysis


def test_d87_is_re_checked_after_the_analysis(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = Rig(tmp_path)
    calls: list[int] = []

    def usage(path: Path) -> Any:
        calls.append(1)
        free = 10**12 if len(calls) == 1 else 10
        return type("Usage", (), {"total": free, "used": 0, "free": free})

    monkeypatch.setattr(disk_space_module.shutil, "disk_usage", usage)
    result = rig.run(rig.request())
    assert "Not enough free space" in result.failure and len(calls) == 2
    assert rig.source.iterations == 1 and "open" not in rig.sink.calls


def _three_item_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, exports: Any) -> list[str]:
    rig = Rig(tmp_path)
    sources = []
    for name, size in (("a.mp4", 10), ("b.mp4", 10**9), ("c.mp4", 10)):
        path = tmp_path / name
        path.write_bytes(b"x" * min(size, 10))
        sources.append(path)
    real_stat = os.stat

    def stat(path: Any, *args: Any, **kwargs: Any) -> Any:
        info = real_stat(path, *args, **kwargs)
        if Path(path).name == "b.mp4":
            return os.stat_result((info.st_mode, 0, 0, 0, 0, 0, 10**9, 0, 0, 0))
        return info

    monkeypatch.setattr(export_module.os, "stat", stat)
    rig_probe_rate = rig.probe  # tiny frames: the ceiling term is small
    assert rig_probe_rate.video.width == 12
    _free(monkeypatch, 5 * 10**8)
    engine = exports(rig)
    requests = [rig.request(source=s) for s in sources]
    report = run_batch(engine, requests, StubProgress())
    return [item.state for item in report.items]


def test_d87_is_per_item_in_a_batch(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    states = _three_item_batch(tmp_path, monkeypatch, lambda rig: rig.engine)
    assert states == ["done with warnings", "failed", "done with warnings"]


class _BatchWideCheck:
    """A planted wrong implementation: one D87 check over the sum of every item's estimate."""

    def __init__(self, rig: Rig) -> None:
        self.rig = rig
        self.refused = False

    def job(self, request: ExportRequest) -> Any:
        if not self.refused:
            sizes = sum(os.stat(p).st_size for p in self.rig.folder.glob("[abc].mp4"))
            check = disk_space_module.check_free_space(self.rig.folder, sizes)
            self.refused = not check.ok
        if self.refused:
            return lambda progress: JobResult(False, (), (), "batch refused", "none", 0.0)
        return self.rig.engine.job(request)


def test_planted_batch_wide_d87_fails_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    states = _three_item_batch(tmp_path, monkeypatch, _BatchWideCheck)
    assert states != ["done with warnings", "failed", "done with warnings"]


# --- settings, DR-35, D111/AD-9, provenance ------------------------------------------------


def test_a_missing_output_folder_is_a_readable_failure(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    result = rig.run(rig.request(output_folder=tmp_path / "gone"))
    assert result.failure.startswith("clip.mp4: the output folder does not exist: ")
    assert rig.sinks == [] and rig.source.iterations == 0


def test_an_invalid_suffix_is_a_readable_failure(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    result = rig.run(rig.request(output_suffix="a/b"))
    assert result.failure.startswith("clip.mp4: output suffix ")
    assert rig.files() == ["clip.mp4", "shot.png"]


def test_an_unknown_method_is_a_readable_failure(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    request = rig.request()
    request = ExportRequest(request.source, "video", parameter_set("nope"), request.settings)
    result = rig.run(request)
    assert result.failure == "clip.mp4: unknown correction method 'nope'"


@pytest.mark.parametrize("name", ["GX010001.LRV", "GX010001.thm"])
def test_a_sidecar_is_a_readable_failure(tmp_path: Path, name: str) -> None:
    rig = Rig(tmp_path)
    (tmp_path / name).write_bytes(b"sidecar")
    result = rig.run(rig.request(source=tmp_path / name))
    assert result.failure.startswith(f"{name}: {name} is a camera proxy or thumbnail file")
    assert rig.sinks == []


def test_dr35a_a_reserved_device_name_is_refused_with_nothing_written(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    source = tmp_path / "NU.MP4"
    source.write_bytes(b"video")
    result = rig.run(rig.request(source=source, output_suffix="L"))
    assert result.failure == (
        "NU.MP4: the output name NUL.MP4 is a reserved device name on Windows; "
        "change the output suffix."
    )
    assert rig.files() == ["NU.MP4", "clip.mp4", "shot.png"]
    assert "open" not in rig.sink.calls


@pytest.mark.parametrize(
    ("name", "reserved"),
    [
        ("NUL.MP4", True),
        ("nul.mp4", True),
        ("CON.png", True),
        ("com1.x.mp4", True),
        ("LPT9 .png", True),
        ("AUX..png", True),
        ("NULL.MP4", False),
        ("CONSOLE.png", False),
        ("COM10.mp4", False),
        ("NUL_2.MP4", False),
        ("NUL2.MP4", False),
        ("CONSOLE.MP4", False),
        (".NUL", False),
    ],
)
def test_reserved_device_names(name: str, reserved: bool) -> None:
    assert is_reserved_device_name(name) is reserved


def _registries_of_two_jobs(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> list[tuple[str, Reservations | None]]:
    """Run two video jobs and return each (call, registry) seen by plan_output and SafeWrite.

    The registries themselves are held (not their ``id``), so a freed one's id cannot be
    reused by the next job's and pass for a fresh registry.
    """
    seen: list[tuple[str, Reservations | None]] = []
    real_plan = export_module.plan_output
    real_init = SafeWrite.__init__

    def plan(source: Path, settings: Settings, kind: Any, reservations: Reservations) -> Any:
        seen.append(("plan", reservations))
        return real_plan(source, settings, kind, reservations)

    def init(self: SafeWrite, plan: Any, reservations: Reservations | None = None) -> None:
        seen.append(("write", reservations))
        real_init(self, plan, reservations)

    monkeypatch.setattr(export_module, "plan_output", plan)
    monkeypatch.setattr(SafeWrite, "__init__", init)
    rig = Rig(tmp_path)
    assert rig.run(rig.request()).ok and rig.run(rig.request()).ok
    return seen


def _assert_one_fresh_registry_per_job(seen: list[tuple[str, Reservations | None]]) -> None:
    assert [s[0] for s in seen] == ["plan", "write", "plan", "write"]
    assert seen[0][1] is seen[1][1] and seen[2][1] is seen[3][1], "plan and write differ"
    assert seen[0][1] is not None
    assert seen[0][1] is not seen[2][1], "a registry was reused across jobs"


def test_one_fresh_reservations_per_job_reaches_plan_output_and_safe_write(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _assert_one_fresh_registry_per_job(_registries_of_two_jobs(tmp_path, monkeypatch))


def test_planted_shared_registry_fails_by_name(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    # R1 F7: a single registry reused by every job must fail the per-job property.
    shared = Reservations()
    monkeypatch.setattr(export_module, "Reservations", lambda: shared)
    seen = _registries_of_two_jobs(tmp_path, monkeypatch)
    with pytest.raises(AssertionError, match="a registry was reused across jobs"):
        _assert_one_fresh_registry_per_job(seen)


def test_force_cpu_and_the_fallback_reason(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    rig = Rig(tmp_path)
    forced = rig.run(rig.request(force_cpu=True))
    assert forced.device == "CPU: forced" and "Processed on the CPU" not in " ".join(
        forced.warnings
    )
    reason = "CPU: estimate 1,982 MiB exceeds free 1,200 MiB"
    (tmp_path / "x").mkdir()
    rig2 = Rig(tmp_path / "x", reason=reason)
    with caplog.at_level(logging.INFO, logger="clearwater.jobs.export"):
        fallback = rig2.run(rig2.request("photo"))
    assert fallback.device == reason
    assert f"Processed on the CPU ({reason})." in fallback.warnings
    line = [r.getMessage() for r in caplog.records if "shot.png" in r.getMessage()]
    assert line and "ok" in line[0] and reason in line[0]


def test_auto_without_nvenc_resolves_to_libx265_and_provenance_records_it(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    result = rig.run(rig.request(video_encoder="auto"))
    assert result.ok, result.failure
    assert rig.sink.open_kwargs["encoder"] == "libx265"
    provenance = rig.sink.open_kwargs["provenance"]
    assert provenance["settings"] == {
        "encoder": "libx265",
        "quality": "standard",
        "bit_depth": 8,
        "device": "GPU",
    }


def test_an_unavailable_explicit_encoder_fails_before_the_analysis(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    result = rig.run(rig.request(video_encoder="hevc_nvenc"))
    assert result.failure == (
        "clip.mp4: the encoder hevc_nvenc is not available here: no NVIDIA encoder here"
    )
    assert rig.source.iterations == 0 and rig.files() == ["clip.mp4", "shot.png"]


def test_provenance_key_set_name_not_path_and_off_when_disabled(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    rig.run(rig.request())
    provenance = rig.sink.open_kwargs["provenance"]
    assert set(provenance) == {
        "format_version", "method", "parameters", "created", "app_version", "source", "settings",
    }  # fmt: skip
    assert provenance["app_version"] == "9.9.9" and provenance["method"] == "grayworld"
    assert provenance["parameters"] == {"strength": 1.0, "gamma": 1.0, "unused": 0.0}
    source = provenance["source"]
    assert source["name"] == "clip.mp4" and str(tmp_path) not in json.dumps(provenance)
    assert set(source) == {
        "name", "size", "mtime", "container", "codec", "width", "height", "bit_depth",
        "frame_rate", "duration_s", "nb_frames", "color",
    }  # fmt: skip
    rig.run(rig.request(provenance=False))
    assert rig.sink.open_kwargs["provenance"] is None
    rig.run(rig.request("photo"))
    assert rig.writer.provenance is not None
    assert rig.writer.provenance["settings"] == {"png_bit_depth": 16, "device": "GPU"}


def test_provenance_stays_well_under_the_sink_limit() -> None:
    from clearwater.io.video.encode import PROVENANCE_MAX_BYTES, provenance_comment
    from clearwater.jobs.provenance import provenance_object
    from clearwater.methods import available_methods

    parameters: dict[str, Any] = {}
    for method in available_methods().values():
        for p in method.parameters:
            parameters[p.name] = -1.2345678901234567e-300 if p.type == "float" else p.default
    obj = provenance_object(
        method="ancuti2018",
        parameters=parameters,
        app_version="0.0.0+" + "x" * 64,
        source={"name": "N" * 255, "size": 2**62, "mtime": "2026-10-27T00:00:00+00:00",
                "container": "mov,mp4,m4a,3gp,3g2,mj2", "codec": "hevc", "width": 5312,
                "height": 4648, "bit_depth": 10, "frame_rate": "30000/1001",
                "duration_s": "123456789/1000", "nb_frames": 10**9,
                "color": {"primaries": "bt709", "transfer": "bt709", "matrix": "bt709",
                          "range": "limited"}},
        settings={"encoder": "hevc_nvenc", "quality": "standard", "bit_depth": 10,
                  "device": "CPU: estimate 99,999,999 MiB exceeds free 99,999,999 MiB"},
    )  # fmt: skip
    assert len(provenance_comment(obj).encode()) < PROVENANCE_MAX_BYTES // 2


def test_n8_the_source_is_untouched_after_success_failure_and_cancel(tmp_path: Path) -> None:
    rig = Rig(tmp_path)
    before = (rig.video.read_bytes(), rig.video.stat().st_mtime_ns)
    rig.run(rig.request())
    sink = FakeSink()
    sink.fail_at = 1
    rig.next_sink = lambda: sink
    rig.run(rig.request())
    rig.next_sink = FakeSink
    rig.run(rig.request(), CancelAt("Exporting"))
    assert (rig.video.read_bytes(), rig.video.stat().st_mtime_ns) == before


# --- static ----------------------------------------------------------------------------------


_TELEMETRY_NAMES = re.compile(
    r"(?<![a-z])(gpmd|gpmf|gps|imu|latitude|longitude)(?![a-z])", re.IGNORECASE
)
"""A GPS, IMU or GoPro telemetry name, standing alone or as a part of an identifier
(``read_gps_fix``, ``IMU``), but not inside a longer word (``minimum``)."""


def test_the_telemetry_name_guard_catches_a_planted_name() -> None:
    # R1 F6: the guard's pattern once carried literal backspace bytes where word boundaries
    # were meant, so it matched nothing; this control keeps the pattern honest.
    planted = 'track = "gpmd"\ndef read_gps_fix(): ...\nIMU_RATE = 200\nlatitude = 0\n'
    broken = "\x08(gpmd|gpmf|gps|imu|latitude|longitude)\x08"
    assert re.findall(broken, planted, re.IGNORECASE) == []
    assert [m.lower() for m in _TELEMETRY_NAMES.findall(planted)] == [
        "gpmd",
        "gps",
        "imu",
        "latitude",
    ]
    assert _TELEMETRY_NAMES.findall("the minimum simulated gpsx value") == []


def test_no_jobs_module_imports_methods_or_gui_or_reads_gps() -> None:
    folder = Path(clearwater.jobs.__file__).parent
    for path in sorted(folder.glob("*.py")):
        text = path.read_text()
        tree = ast.parse(text)
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for name in names:
                assert not name.startswith(("clearwater.methods", "clearwater.gui")), (path, name)
        found = _TELEMETRY_NAMES.findall(text)
        assert found == [], (path.name, found)
