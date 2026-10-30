"""WP4.3 cell 9: the interface thread's load during jobs (V7; CHARC ruling 7b32521f, items 1 and 3).

Windows 1-3 traced V7 (c)'s and (e)'s stalls to in-process GIL contention: the interface thread's
own Python work during an export (each entry into Python from the event loop waits for the GIL
behind the two compute threads) and full garbage collections at the job boundaries. These are
the planted forms of the remediation:

- item 1: the window's paint, update, layout and timer events run no Python (the close watch was
  a Python event filter on the window, called for every one of them); the job runner hands the
  interface thread at most one report per job per tick, the latest (already so at ``1d96dc4``:
  pinned, not a RED);
- item 3: CPython's full (generation 2) collection never runs on a job's thread at its end, the
  path the plan cache's release takes; the app runs it on the interface thread at a moment it
  chooses, and the process's own collector settings come back at the window's close.
"""

# ``make_app`` is imported from test_app_startup and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import gc
import sys
import threading
import time
from collections import Counter
from collections.abc import Callable
from types import FrameType
from typing import Any

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QObject, QTimerEvent

from clearwater.app.main import IDLE_CHECK_MS, Application, FullCollections
from clearwater.gui.jobs import QtJobRunner
from clearwater.interfaces import JobResult, Progress
from test_app_startup import cpu_settings, make_app, wait_started

pytestmark = pytest.mark.gui

SETTLE_MS = 2500
"""Long enough for the app to see start-up over (an idle moment after the start-up jobs)."""

MIN_REPORTS = 20_000
"""The runner pin's job reports at least this often, whatever the host does to its worker."""


def _ok() -> JobResult:
    return JobResult(ok=True, outputs=(), warnings=(), failure=None, device="cpu", elapsed_s=0.0)


class _Runner:
    """A job runner stand-in for the collection policy: ``active()`` is what the test sets."""

    def __init__(self, active: int) -> None:
        self.count = active

    def active(self) -> int:
        return self.count


def _full_collections() -> tuple[list[str], Callable[[str, dict[str, int]], None]]:
    """A ``gc.callbacks`` entry recording the thread of each full (generation 2) collection."""
    full: list[str] = []

    def on_gc(phase: str, info: dict[str, int]) -> None:
        if phase == "start" and info["generation"] == 2:
            full.append(threading.current_thread().name)

    return full, on_gc


def _overdue(pending: int) -> None:
    """Make more than ``pending`` younger collections pending since the last full one."""
    while gc.get_count()[2] <= pending:
        gc.collect(1)  # each generation-1 collection counts one toward the full one


def test_the_windows_paint_update_layout_and_timer_events_run_no_python(make_app, qtbot) -> None:
    """Item 1: each such event reaches the window without entering Python (a counting profiler).

    Planted on ``1d96dc4``: the close watch's ``eventFilter`` is called for every one of them.
    """
    application = make_app(cpu_settings())
    wait_started(qtbot, application)
    window = application.window
    qtbot.wait(50)  # the layout settled
    status = window.statusBar().geometry()  # a repaint of the window, the preview untouched
    sends: list[tuple[Callable[..., Any], tuple[Any, ...]]] = [
        (window.repaint, (status,)),  # the window's paint events, delivered by Qt's own paint
        (QCoreApplication.sendEvent, (window, QEvent(QEvent.Type.UpdateRequest))),
        (QCoreApplication.sendEvent, (window, QEvent(QEvent.Type.LayoutRequest))),
        (QCoreApplication.sendEvent, (window, QTimerEvent(0x7FFF))),
    ]
    calls: list[str] = []

    def count(frame: FrameType, event: str, _arg: Any) -> None:
        if event == "call":
            caller = frame.f_back.f_code.co_qualname if frame.f_back else "-"
            calls.append(f"{frame.f_code.co_qualname} <- {caller}")

    for send, args in sends:  # a C call each: only Python that Qt itself enters is counted
        sys.setprofile(count)
        try:
            send(*args)
        finally:
            sys.setprofile(None)
    assert calls == [], Counter(calls).most_common(10)


def test_the_runner_delivers_at_most_one_report_per_tick_and_the_latest(qtbot, monkeypatch) -> None:
    """Item 1's delivery rule, pinned per tick (green at base; R5-5, R5-6).

    Each poll of the runner's timer and its final delivery before ``on_done`` are marked, and no
    stretch between two marks may carry more than one report (a burst fails). The job reports at
    least :data:`MIN_REPORTS` times and for at least a second, so a host that pauses its worker
    still leaves reports to coalesce.
    """
    events: list[tuple[str, int]] = []
    real_poll, real_finished = QtJobRunner._poll, QtJobRunner._on_finished

    def poll(self: QtJobRunner) -> None:
        events.append(("tick", 0))
        real_poll(self)

    def finished(self: QtJobRunner, handle: object, result: object) -> None:
        events.append(("end", 0))
        real_finished(self, handle, result)

    monkeypatch.setattr(QtJobRunner, "_poll", poll)  # before the runner connects its slots
    monkeypatch.setattr(QtJobRunner, "_on_finished", finished)
    runner = QtJobRunner()
    last = {"done": 0}

    def job(progress: Progress) -> JobResult:
        done = 0
        ends = time.monotonic() + 1.0
        while done < MIN_REPORTS or time.monotonic() < ends:
            done += 1
            progress.report(done, None, "step")
        last["done"] = done
        return _ok()

    handle = runner.run(
        job,
        on_done=lambda _r: events.append(("done", 0)),
        on_progress=lambda d, _t, _m: events.append(("report", d)),
    )
    qtbot.waitUntil(lambda: not handle.is_running(), timeout=10000)
    seen = [d for kind, d in events if kind == "report"]
    assert seen and seen[-1] == last["done"]  # the last report was delivered,
    assert events.index(("report", last["done"])) < events.index(("done", 0))  # before the result
    assert seen == sorted(set(seen))  # each delivery later than the one before, none repeated
    per_mark: list[int] = []
    for kind, _ in events:
        if kind in ("tick", "end"):
            per_mark.append(0)
        elif kind == "report":
            assert per_mark, events[:5]  # a report only from a poll or the final delivery
            per_mark[-1] += 1
    assert max(per_mark) <= 1, per_mark
    assert len(seen) < last["done"]  # fewer deliveries than reports: the rest were dropped


def test_a_planted_full_collection_load_at_a_job_boundary_runs_no_full_collection_there(
    make_app, qtbot
) -> None:
    """Item 3: the job's end allocates enough long-lived objects for a full collection.

    The load is as many container objects as the collector tracks (at least 300,000), kept
    alive: on ``1d96dc4`` CPython's automatic full collection then runs on the job's own thread,
    holding the GIL, as window 3 saw at the plan cache's release. After the remediation none runs
    there, and the deferred one runs on the interface thread once no job is running.
    """
    application = make_app(cpu_settings())
    wait_started(qtbot, application)
    qtbot.wait(SETTLE_MS)  # start-up over: the boundary below is a later job's
    load = max(300_000, len(gc.get_objects()))
    full: list[str] = []
    kept: list[list[int]] = []

    def on_gc(phase: str, info: dict[str, int]) -> None:
        if phase == "start" and info["generation"] == 2:
            full.append(threading.current_thread().name)

    def job(_progress: Progress) -> JobResult:
        kept.extend([i] for i in range(load))  # the boundary's long-lived garbage-to-be
        return _ok()

    gc.callbacks.append(on_gc)
    try:
        application.window.jobs.run(job, on_done=lambda _r: full.append("on_done"))
        qtbot.waitUntil(lambda: "on_done" in full, timeout=60000)
        at_boundary = full[: full.index("on_done")]
        assert "clearwater-job" not in at_boundary, full
        main = threading.main_thread().name
        qtbot.waitUntil(lambda: main in full[len(at_boundary) + 1 :], timeout=10000)
    finally:
        gc.callbacks.remove(on_gc)
        kept.clear()


def test_the_collection_policy_holds_while_the_window_is_open_and_ends_at_its_close(
    make_app, qtbot
) -> None:
    """Item 3: start-up's objects frozen, no automatic full collection; both undone at close."""
    before, frozen_before = gc.get_threshold(), gc.get_freeze_count()  # the interpreter's own
    application = make_app(cpu_settings())
    wait_started(qtbot, application)
    qtbot.waitUntil(lambda: gc.get_freeze_count() > frozen_before, timeout=10000)
    first, second, third = gc.get_threshold()
    assert (first, second) == before[:2]
    assert third > 1_000_000  # no automatic full collection while the window is open
    application.window.close()
    assert gc.get_threshold() == before
    assert gc.get_freeze_count() <= frozen_before


def test_no_full_collection_runs_while_a_job_runs_however_far_overdue(qtbot) -> None:
    """R5-1 (CHARC cc0703a7 Q1 (a)): while a job runs, no full collection runs on any thread.

    Before the start-up freeze (no idle moment yet) and however many younger collections are
    pending (here 20 times the interpreter's own third threshold): the collection waits for an
    idle moment. Planted on ``28c4ece``: the busy check collects on the interface thread.
    """
    own = gc.get_threshold()[2]
    owner = QObject()  # the timer's parent, alive for the test
    policy = FullCollections(_Runner(active=1), owner)
    full, on_gc = _full_collections()
    policy.start()
    gc.callbacks.append(on_gc)
    try:
        _overdue(20 * own)
        qtbot.wait(int(2.5 * IDLE_CHECK_MS))  # two checks, each with a job running
        assert full == []
    finally:
        gc.callbacks.remove(on_gc)
        policy.stop()


def test_an_idle_window_neither_freezes_nor_collects_while_another_windows_job_runs(qtbot) -> None:
    """R5-2 (CHARC cc0703a7 Q2): idle means no started window has a job running.

    Window B idles while window A's job runs: B's checks must not freeze A's working heap nor
    collect. Once A's job ends, the next check freezes (the positive control). Planted on
    ``e1a8599``: B's check reads only B's runner and freezes.
    """
    frozen_before = gc.get_freeze_count()
    owner = QObject()  # the timers' parent, alive for the test
    a_jobs = _Runner(active=1)
    a, b = FullCollections(a_jobs, owner), FullCollections(_Runner(active=0), owner)
    full, on_gc = _full_collections()
    a.start()
    b.start()
    gc.callbacks.append(on_gc)
    try:
        qtbot.wait(int(2.5 * IDLE_CHECK_MS))  # two checks of each, A's job running throughout
        assert (gc.get_freeze_count(), full) == (frozen_before, [])
        a_jobs.count = 0
        qtbot.waitUntil(lambda: gc.get_freeze_count() > frozen_before, timeout=5000)
    finally:
        gc.callbacks.remove(on_gc)
        a.stop()
        b.stop()
    assert gc.get_freeze_count() <= frozen_before


def test_the_collection_policy_starts_before_the_start_up_workers(
    make_app, qtbot, monkeypatch
) -> None:
    """R5-3: no start-up worker runs before the automatic full collection is off.

    Planted on ``d13f84b``: ``build_application`` starts the jobs, then the policy.
    """
    seen: list[int] = []
    real = Application.start_jobs

    def start_jobs(self: Application) -> None:
        seen.append(gc.get_threshold()[2])  # the third threshold as the workers start
        real(self)

    monkeypatch.setattr(Application, "start_jobs", start_jobs)
    application = make_app(cpu_settings())
    wait_started(qtbot, application)
    assert len(seen) == 1 and seen[0] > 1_000_000, seen


def test_a_closed_windows_collection_policy_does_not_start(make_app, qtbot) -> None:
    """R5-3: once the window saw its close, starting its policy changes nothing.

    Planted on ``d13f84b``: ``start()`` registers the closed window's policy, so the automatic
    full collection stays off after the close.
    """
    before = gc.get_threshold()
    application = make_app(cpu_settings())
    wait_started(qtbot, application)
    window = application.window
    window.close()
    assert window.close_seen and gc.get_threshold() == before
    try:
        window.full_collections.start()
        assert gc.get_threshold() == before
    finally:
        window.full_collections.stop()


def test_a_restarted_collection_policy_freezes_again(qtbot) -> None:
    """R5-4: a policy started again after its stop freezes again at its first idle moment.

    Planted on ``4611ed6``: the instance keeps its frozen flag across the stop (which unfroze the
    process), so the restarted policy never freezes.
    """
    frozen_before = gc.get_freeze_count()
    owner = QObject()  # the timer's parent, alive for the test
    policy = FullCollections(_Runner(active=0), owner)
    try:
        policy.start()
        qtbot.waitUntil(lambda: gc.get_freeze_count() > frozen_before, timeout=5000)
        policy.stop()
        assert gc.get_freeze_count() <= frozen_before
        policy.start()
        qtbot.waitUntil(lambda: gc.get_freeze_count() > frozen_before, timeout=5000)
    finally:
        policy.stop()
