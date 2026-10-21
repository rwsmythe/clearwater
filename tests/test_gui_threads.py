"""WP3.16 threading: V7's 100 ms bound, the jobs runner, AD-15 on a stub job, shutdown.

Covers brief task 8 rows "V7 bound", "AD-15 on the stub" and the planted "a render on the
interface thread"; plus no heavy call on the interface thread and close with work in flight.
"""

from __future__ import annotations

import threading
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QElapsedTimer, QTimer

import gui_support  # noqa: F401  (sets the offscreen platform first)
from clearwater.config import new_parameter_set
from clearwater.gui import AnalysisState, render_worker
from clearwater.gui.jobs import QtJobRunner
from clearwater.gui.shell import NEEDS_ANALYSIS_REASON
from clearwater.interfaces import JobResult, Progress
from gui_support import (
    LevelMethod,
    busy_numpy,
    frame,
    image,
    make_window,  # noqa: F401
    open_and_wait,
    photo_engines,
    video_engines,
    wait_idle,
)

pytestmark = pytest.mark.gui

V7_BOUND_MS = 100


def _ok(device: str = "cpu") -> JobResult:
    return JobResult(True, (), (), None, device, 0.0)


def _reporting_job(seconds: float):
    def job(progress: Progress) -> JobResult:
        end = time.perf_counter() + seconds
        done = 0
        while time.perf_counter() < end and not progress.cancelled():
            done += 1
            progress.report(done, None, "busy")
            # Release the GIL each step as a real job does (its work is NumPy or FFmpeg I/O); a
            # job spinning in pure Python starves every other Python thread, which is outside
            # the envelope (brief: V7 with a GIL-holding method is re-measured at WP4.3).
            time.sleep(0)
        return _ok()

    return job


def _probe_max_gap_ms(qtbot, start, until, timeout_ms: int = 20000) -> float:
    """Run a 10 ms QTimer on the main thread, call ``start`` from the event loop once the probe
    runs, and wait until ``until()``; return the probe's longest gap between ticks."""
    clock = QElapsedTimer()
    clock.start()
    last = [clock.elapsed()]
    worst = [0]

    def tick() -> None:
        now = clock.elapsed()
        worst[0] = max(worst[0], now - last[0])
        last[0] = now

    timer = QTimer()
    timer.setInterval(10)
    timer.timeout.connect(tick)
    timer.start()
    QTimer.singleShot(30, start)
    try:
        qtbot.wait(60)
        qtbot.waitUntil(until, timeout=timeout_ms)
    finally:
        timer.stop()
    tick()
    return float(worst[0])


def _v7_run(build, qtbot) -> tuple[float, LevelMethod]:
    """A ~2 s NumPy render in the preview worker and a high-rate job; the probe's worst gap."""
    method = LevelMethod(busy=None)
    path = Path("heavy.png")
    window = build(photo_engines({path: image(400, 600)}, methods={"level": method}))
    open_and_wait(qtbot, window, path)
    reports = [0]
    finished = []
    method.busy = busy_numpy(2.0)

    def start() -> None:
        window.jobs.run(
            _reporting_job(2.0),
            on_done=finished.append,
            on_progress=lambda done, total, message: reports.__setitem__(0, done),
        )
        window.session.set_parameters(new_parameter_set("level", {"level": 0.3}))

    worst = _probe_max_gap_ms(qtbot, start, lambda: bool(finished) and window.controller.idle())
    assert method.rendered[-1] == pytest.approx(0.3)
    assert reports[0] > 1000  # the job really reported at a high rate
    return worst, method


def test_v7_interface_never_waits_more_than_100_ms(make_window, qtbot) -> None:  # noqa: F811
    worst, method = _v7_run(make_window, qtbot)
    print(f"V7 observed maximum main-thread gap: {worst:.0f} ms")  # informational (brief row 8)
    assert worst <= V7_BOUND_MS
    assert threading.main_thread() not in method.threads


def test_planted_render_on_the_interface_thread_fails_v7(make_window, qtbot, monkeypatch) -> None:  # noqa: F811
    def inline_submit(self, task):
        with self._lock:
            self._generation += 1
            generation = self._generation
        value = task(lambda: None)
        self._on_result(render_worker.Outcome(generation, value, None))
        return generation

    monkeypatch.setattr(render_worker.LatestWorker, "submit", inline_submit)
    worst, method = _v7_run(make_window, qtbot)
    assert worst > V7_BOUND_MS  # the V7 test above would fail on this implementation
    assert threading.main_thread() in method.threads


def test_open_and_frame_decode_run_off_the_interface_thread(make_window, qtbot) -> None:  # noqa: F811
    threads: list[threading.Thread] = []
    frames = [frame(48, 64, ticks=t * 3000, seed=t) for t in range(5)]
    engines = video_engines(frames)
    original_frames = engines.video_source.frames

    def recording_frames(*args, **kwargs):
        threads.append(threading.current_thread())
        return original_frames(*args, **kwargs)

    def recording_probe(path: Path):
        threads.append(threading.current_thread())
        from clearwater.gui.engines import stub_probe

        return stub_probe(path)

    object.__setattr__(engines.video_source, "frames", recording_frames)
    object.__setattr__(engines, "video_probe", recording_probe)
    window = make_window(engines)
    open_and_wait(qtbot, window, Path("clip.mp4"))
    window.session.set_position(9000)
    wait_idle(qtbot, window)
    assert window.session.current_image().pts_ticks == 9000
    assert len(threads) == 3 and threading.main_thread() not in threads


# The jobs runner.


def test_jobs_runner_coalesces_reports_and_delivers_the_last_before_done(qtbot) -> None:
    runner = QtJobRunner()
    seen: list[tuple[int, int | None, str]] = []
    order: list[str] = []

    def job(progress: Progress) -> JobResult:
        for i in range(1, 20001):
            progress.report(i, 20000, "step")
        return _ok()

    def on_progress(done: int, total: int | None, message: str) -> None:
        seen.append((done, total, message))
        order.append("progress")

    handle = runner.run(job, on_done=lambda r: order.append("done"), on_progress=on_progress)
    qtbot.waitUntil(lambda: not handle.is_running(), timeout=10000)
    assert seen[-1] == (20000, 20000, "step")
    assert len(seen) < 20000  # coalesced
    assert order[-1] == "done" and order.count("done") == 1
    assert [d for d, _, _ in seen] == sorted(d for d, _, _ in seen)
    assert runner.active() == 0
    assert runner.wait(1.0)


def test_jobs_runner_turns_an_exception_into_a_failed_result(qtbot) -> None:
    runner = QtJobRunner()
    results: list[JobResult] = []

    def job(progress: Progress) -> JobResult:
        raise OSError("disk gone")

    runner.run(job, on_done=results.append)
    qtbot.waitUntil(lambda: bool(results), timeout=5000)
    assert not results[0].ok and "disk gone" in (results[0].failure or "")


def test_jobs_runner_cancel_sets_progress_cancelled(qtbot) -> None:
    runner = QtJobRunner()
    results: list[JobResult] = []
    handle = runner.run(_reporting_job(30.0), on_done=results.append)
    assert runner.active() == 1
    runner.cancel()
    qtbot.waitUntil(lambda: bool(results), timeout=5000)
    assert not handle.is_running() and runner.active() == 0


def test_jobs_run_on_worker_threads(qtbot) -> None:
    runner = QtJobRunner()
    threads: list[threading.Thread] = []
    callback_threads: list[threading.Thread] = []

    def job(progress: Progress) -> JobResult:
        threads.append(threading.current_thread())
        progress.report(1, 1, "x")
        return _ok()

    runner.run(
        job,
        on_done=lambda r: callback_threads.append(threading.current_thread()),
        on_progress=lambda *a: callback_threads.append(threading.current_thread()),
    )
    qtbot.waitUntil(lambda: runner.active() == 0, timeout=5000)
    assert threads[0] is not threading.main_thread()
    assert callback_threads and all(t is threading.main_thread() for t in callback_threads)


# AD-15 on a stub analysis job.


def test_ad15_stub_analysis_disables_export_with_reason_and_progress(make_window, qtbot) -> None:  # noqa: F811
    frames = [frame(48, 64, ticks=0)]
    window = make_window(video_engines(frames))
    export = window.shell_actions.export
    export.set_unavailable(None)  # WP3.19 has connected
    open_and_wait(qtbot, window, Path("clip.mp4"))
    assert not export.isEnabled() and export.unavailable_reason() == NEEDS_ANALYSIS_REASON
    session = window.session
    release = threading.Event()

    def analysis(progress: Progress) -> JobResult:
        for i in range(1, 4):
            progress.report(i, 10, "analysing")
        release.wait(10)
        if progress.cancelled():
            return JobResult(False, (), (), "cancelled", "cpu", 0.0)
        progress.report(10, 10, "analysing")
        return _ok()

    def on_progress(done: int, total: int | None, message: str) -> None:
        session.set_analysis(AnalysisState("running", done, total, message))

    def on_done(result: JobResult) -> None:
        session.set_analysis(AnalysisState("complete" if result.ok else "cancelled"))

    window.jobs.run(analysis, on_done=on_done, on_progress=on_progress)
    qtbot.waitUntil(lambda: session.analysis().done == 3, timeout=5000)
    assert not export.isEnabled()
    assert "3/10" in (export.unavailable_reason() or "") and "3/10" in export.toolTip()
    release.set()
    qtbot.waitUntil(lambda: session.analysis().phase == "complete", timeout=5000)
    assert export.isEnabled() and export.unavailable_reason() is None

    release.clear()
    handle = window.jobs.run(analysis, on_done=on_done, on_progress=on_progress)
    qtbot.waitUntil(lambda: session.analysis().phase == "running", timeout=5000)
    handle.cancel()
    release.set()
    qtbot.waitUntil(lambda: session.analysis().phase == "cancelled", timeout=5000)
    assert not export.isEnabled() and export.unavailable_reason() == NEEDS_ANALYSIS_REASON


def test_ad15_photo_needs_no_analysis_and_failed_analysis_says_why(
    make_window,  # noqa: F811
    qtbot,
    tmp_path: Path,
) -> None:
    path = Path("p.png")
    window = make_window(photo_engines({path: image(30, 40)}))
    export = window.shell_actions.export
    assert export.unavailable_reason() is not None and not export.isEnabled()
    export.set_unavailable(None)
    assert not export.isEnabled()  # nothing open yet
    open_and_wait(qtbot, window, path)
    assert export.isEnabled()
    export.set_unavailable("Busy with a batch.")
    assert not export.isEnabled() and export.unavailable_reason() == "Busy with a batch."
    export.set_unavailable(None)
    window2 = make_window(video_engines([frame(48, 64, ticks=0)]), where=tmp_path / "w2")
    window2.shell_actions.export.set_unavailable(None)
    open_and_wait(qtbot, window2, Path("clip.mp4"))
    window2.session.set_analysis(AnalysisState("failed", message="decoder crashed"))
    assert "decoder crashed" in (window2.shell_actions.export.unavailable_reason() or "")


# Shutdown.


def test_close_with_a_render_and_a_job_in_flight_is_prompt(make_window, qtbot) -> None:  # noqa: F811
    method = LevelMethod()
    path = Path("p.png")
    window = make_window(photo_engines({path: image(200, 300)}, methods={"level": method}))
    open_and_wait(qtbot, window, path)
    method.busy = busy_numpy(1.0)
    window.session.set_parameters(new_parameter_set("level", {"level": 0.7}))
    results: list[JobResult] = []
    window.jobs.run(_reporting_job(30.0), on_done=results.append)
    qtbot.wait(100)
    start = time.perf_counter()
    window.close()
    elapsed = time.perf_counter() - start
    assert elapsed < 4.0
    assert window.jobs.active() in (0, 1)
    assert window.controller.idle()
    with pytest.raises(RuntimeError, match="closed"):
        window.jobs.run(_reporting_job(0.0), on_done=results.append)
    qtbot.wait(50)
    window.close()  # a second close is harmless
