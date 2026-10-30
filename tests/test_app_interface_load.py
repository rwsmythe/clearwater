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

import sys
import time
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
"""The runner pin's job reports at least this often, whatever the host does to its worker."""


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
    stretch between two marks may carry more than one report (a burst fails), and at least one
    poll must deliver one before the final delivery (R6-3). The job reports at
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
    _assert_delivered_per_tick(events, last["done"])


def _assert_delivered_per_tick(events: list[tuple[str, int]], reports: int) -> None:
    """The runner pin's postconditions over its marked event list and the job's report count."""
    seen = [d for kind, d in events if kind == "report"]
    assert seen and seen[-1] == reports  # the last report was delivered,
    assert events.index(("report", reports)) < events.index(("done", 0))  # before the result
    assert seen == sorted(set(seen))  # each delivery later than the one before, none repeated
    per_mark: list[int] = []
    for kind, _ in events:
        if kind in ("tick", "end"):
            per_mark.append(0)
        elif kind == "report":
            assert per_mark, events[:5]  # a report only from a poll or the final delivery
            per_mark[-1] += 1
    assert max(per_mark) <= 1, per_mark
    assert len(seen) < reports  # fewer deliveries than reports: the rest were dropped
    polled = events[: events.index(("end", 0))]
    assert any(kind == "report" for kind, _ in polled), events[:5]  # a tick delivered (R6-3)


def test_the_runner_pin_rejects_a_run_whose_polls_delivered_nothing() -> None:
    """R6-3: a run where only the final delivery carried a report never exercised a tick.

    Planted on ``74586d4``: that event list passes every postcondition of the pin.
    """
    vacuous = [("end", 0), ("report", MIN_REPORTS), ("done", 0)]
    with pytest.raises(AssertionError):
        _assert_delivered_per_tick(vacuous, MIN_REPORTS)
