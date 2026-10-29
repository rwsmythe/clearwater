"""WP4.3 cell 9: the interface thread's load during jobs (V7; CHARC ruling 7b32521f, items 1 and 3).

Windows 1-3 traced V7 (c)'s and (e)'s stalls to in-process GIL contention: the interface thread's
own Python work during an export (each entry into Python from the event loop waits for the GIL
behind the two compute threads) and full garbage collections at the job boundaries. These are
the planted forms of the remediation:

- item 1: the window's paint, update, layout and timer events run no Python (the close watch was
  a Python event filter on the window, called for every one of them); the job runner hands the
  interface thread at most one report per job per tick, the latest (already so at ``1d96dc4``:
  pinned, not a RED).
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

from clearwater.gui.jobs import PROGRESS_INTERVAL_MS, QtJobRunner
from clearwater.interfaces import JobResult, Progress
from test_app_startup import cpu_settings, make_app, wait_started

pytestmark = pytest.mark.gui


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


def test_the_runner_delivers_at_most_one_report_per_tick_and_the_latest(qtbot) -> None:
    """Item 1's delivery rule, pinned: a job reporting far faster than the tick (green at base)."""
    runner = QtJobRunner()
    seen: list[int] = []
    last = {"done": 0}
    span_s = 1.0

    def job(progress: Progress) -> JobResult:
        done = 0
        ends = time.monotonic() + span_s
        while time.monotonic() < ends:
            done += 1
            progress.report(done, None, "step")
        last["done"] = done
        return _ok()

    began = time.monotonic()
    handle = runner.run(job, on_done=lambda _r: None, on_progress=lambda d, _t, _m: seen.append(d))
    qtbot.waitUntil(lambda: not handle.is_running(), timeout=10000)
    elapsed_ms = (time.monotonic() - began) * 1000
    assert seen[-1] == last["done"]  # the last report, delivered before the result
    assert seen == sorted(set(seen))  # each delivery later than the one before, none repeated
    assert len(seen) <= elapsed_ms / PROGRESS_INTERVAL_MS + 2, (len(seen), elapsed_ms)
    assert last["done"] > 100 * len(seen)  # far faster than the tick: the rest were dropped
