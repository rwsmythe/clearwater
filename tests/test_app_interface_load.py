"""WP4.3 cell 9: the interface thread's load during jobs (V7; CHARC ruling 7b32521f, item 1).

Windows 1-3 traced V7 (c)'s and (e)'s stalls to in-process GIL contention: the interface thread's
own Python work during an export (each entry into Python from the event loop waits for the GIL
behind the two compute threads). These are item 1's planted forms: the window's paint, update,
layout and timer events run no Python (the close watch was a Python event filter on the window,
called for every one of them); the job runner hands the interface thread at most one report per
job per tick, the latest (already so at ``1d96dc4``: pinned, not a RED).
"""

# ``make_app`` is imported from test_app_startup and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import re
import sys
import threading
from collections import Counter
from collections.abc import Callable
from types import FrameType
from typing import Any

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QTimerEvent

from clearwater.gui.jobs import QtJobRunner
from clearwater.interfaces import JobResult, Progress
from test_app_startup import cpu_settings, make_app, wait_started

pytestmark = pytest.mark.gui

MIN_REPORTS = 20_000
"""The runner pin's job reports this many times in each of its two bursts."""

HANG_CEILING_S = 60.0
"""The runner pin's holds give up after this long: a hang ceiling, never a timing (B-6)."""


def _ok() -> JobResult:
    return JobResult(ok=True, outputs=(), warnings=(), failure=None, device="cpu", elapsed_s=0.0)


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

    prior = sys.getprofile()  # a host's profiler, restored after each send (B-15)
    for send, args in sends:  # a C call each: only Python that Qt itself enters is counted
        sys.setprofile(count)
        try:
            send(*args)
        finally:
            sys.setprofile(prior)
    assert calls == [], Counter(calls).most_common(10)


def test_the_runner_delivers_at_most_one_report_per_tick_and_the_latest(qtbot, monkeypatch) -> None:
    """Item 1's delivery rule, pinned per tick (green at base; R5-5, R5-6).

    Each poll of the runner's timer and its final delivery before ``on_done`` are marked with the
    count the job had produced by then; no stretch between two marks may carry more than one
    report (a burst fails), a mark that had a newer report to hand delivers one no older than
    that count (the latest, B-5), and at least one poll must deliver one before the final
    delivery (R6-3).

    Holds, not a clock (B-6): the first poll waits until the job has made its first burst of
    :data:`MIN_REPORTS` reports, so that poll has a burst to coalesce; the job then waits until
    an observed poll has run before its second burst, so a poll delivers before the final
    delivery however the host schedules either thread. The waits are hang ceilings only. The
    count advances before its report, both under one lock a mark also takes, so a mark is the
    exact count published (Reviewer B re-run, item 3).
    """
    events: list[tuple[str, int]] = []
    real_poll, real_finished = QtJobRunner._poll, QtJobRunner._on_finished
    produced = {"done": 0}
    gate = threading.Lock()  # a count and its report, made together
    burst = threading.Event()  # the job's first burst is made
    polled = threading.Event()  # a poll has run since: the job may go on

    def poll(self: QtJobRunner) -> None:
        assert burst.wait(HANG_CEILING_S)
        with gate:
            events.append(("tick", produced["done"]))
        real_poll(self)
        polled.set()

    def finished(self: QtJobRunner, handle: object, result: object) -> None:
        events.append(("end", produced["done"]))
        real_finished(self, handle, result)

    monkeypatch.setattr(QtJobRunner, "_poll", poll)  # before the runner connects its slots
    monkeypatch.setattr(QtJobRunner, "_on_finished", finished)
    runner = QtJobRunner()

    def reports(progress: Progress) -> None:
        for _ in range(MIN_REPORTS):
            with gate:
                produced["done"] += 1  # before the report: a mark never lags one made
                progress.report(produced["done"], None, "step")

    def job(progress: Progress) -> JobResult:
        reports(progress)
        burst.set()
        assert polled.wait(HANG_CEILING_S)
        reports(progress)
        return _ok()

    handle = runner.run(
        job,
        on_done=lambda _r: events.append(("done", 0)),
        on_progress=lambda d, _t, _m: events.append(("report", d)),
    )
    qtbot.waitUntil(lambda: not handle.is_running(), timeout=HANG_CEILING_S * 1000)
    _assert_delivered_per_tick(events, 2 * MIN_REPORTS)


def _assert_delivered_per_tick(events: list[tuple[str, int]], reports: int) -> None:
    """The runner pin's postconditions over its marked event list and the job's report count.

    A mark is ``("tick", produced)`` or ``("end", produced)``: the count of reports the job had
    made when the poll or the final delivery began.
    """
    seen = [d for kind, d in events if kind == "report"]
    assert seen and seen[-1] == reports  # the last report was delivered,
    assert events.index(("report", reports)) < events.index(("done", 0))  # before the result
    assert seen == sorted(set(seen))  # each delivery later than the one before, none repeated
    marks: list[tuple[int, list[int]]] = []  # (produced at the mark, the reports it delivered)
    for kind, value in events:
        if kind in ("tick", "end"):
            marks.append((value, []))
        elif kind == "report":
            assert marks, events[:5]  # a report only from a poll or the final delivery
            marks[-1][1].append(value)
    assert max(len(delivered) for _, delivered in marks) <= 1, marks
    latest = 0
    for produced, delivered in marks:
        if produced > latest:  # a newer report was there to hand: the mark delivers the latest
            assert delivered and delivered[0] >= produced, (produced, delivered)
        if delivered:
            latest = delivered[0]
    assert len(seen) < reports  # fewer deliveries than reports: the rest were dropped
    polled = events[: next(i for i, (kind, _) in enumerate(events) if kind == "end")]
    assert any(kind == "report" for kind, _ in polled), events[:5]  # a tick delivered (R6-3)


def test_the_runner_pin_rejects_a_run_whose_polls_delivered_nothing() -> None:
    """R6-3: a run where only the final delivery carried a report never exercised a tick.

    Planted on ``74586d4``: that event list passes every postcondition of the pin.
    """
    vacuous = [("end", MIN_REPORTS), ("report", MIN_REPORTS), ("done", 0)]
    with pytest.raises(AssertionError):
        _assert_delivered_per_tick(vacuous, MIN_REPORTS)


def test_the_runner_pin_rejects_stale_deliveries_at_a_poll() -> None:
    """B-5: a runner draining old reports one per poll delivers ``1, 2`` while thousands exist.

    Reviewer B's sequence: deliveries ``1, 2, 20000``, one per mark, increasing, the last before
    the result. Without the produced count at each mark it passes every other postcondition.
    """
    stale = [
        ("tick", MIN_REPORTS // 2),
        ("report", 1),
        ("tick", MIN_REPORTS),
        ("report", 2),
        ("end", MIN_REPORTS),
        ("report", MIN_REPORTS),
        ("done", 0),
    ]
    with pytest.raises(AssertionError, match=re.escape(str((MIN_REPORTS // 2, [1])))):
        _assert_delivered_per_tick(stale, MIN_REPORTS)
