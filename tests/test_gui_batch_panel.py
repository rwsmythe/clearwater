"""WP3.19 batch panel (G7, G8, D45, D81, D83, DR-44 (b), V7), against the test-side stub engine.

The stub (``StubExportJobs`` in ``test_gui_export_panel``) writes real files through
``plan_output`` and ``SafeWrite``; the batch is sequenced by the panel, one job per item.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import logging
import threading
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from clearwater.config import new_parameter_set
from clearwater.gui import AnalysisState, Message
from clearwater.gui import batch_panel as batch_module
from clearwater.gui.batch_panel import (
    CURRENT_PARAMETERS,
    BatchItem,
    BatchPanel,
    ItemState,
    format_report,
)
from clearwater.gui.export_panel import ExportPanel
from clearwater.gui.export_service import RUNNING_BATCH_REASON, RUNNING_EXPORT_REASON
from clearwater.gui.shell import NO_SOURCE_REASON
from clearwater.jobs.export_seam import CANCELLED
from gui_support import image, make_window, open_and_wait, photo_engines, presenter_of
from test_gui_export_panel import (
    PHOTO,
    V7_BOUND_MS,
    Rig,
    StubExportJobs,
    _probe_max_gap_ms,
    build_rig,
)

pytestmark = pytest.mark.gui

A, B, C = Path("a.jpg"), Path("b.mp4"), Path("c.jpg")
STATES = [ItemState.DONE, ItemState.FAILED, ItemState.DONE]


def batch_of(rig: Rig) -> BatchPanel:
    return rig.window.findChildren(BatchPanel)[0]


def states(batch: BatchPanel) -> list[ItemState]:
    return [item.state for item in batch.items()]


def wait_batch_idle(rig: Rig) -> None:
    batch = batch_of(rig)
    rig.qtbot.waitUntil(lambda: not batch.is_running(), timeout=20000)


def started(rig: Rig, paths: list[Path], **stub_kwargs: Any) -> BatchPanel:
    """A rig with no file open, ``paths`` queued; Start not pressed."""
    for name, value in stub_kwargs.items():
        setattr(rig.stub, name, value)
    batch = batch_of(rig)
    batch.add_paths(paths)
    return batch


@pytest.fixture
def rig(make_window: Any, qtbot: Any, tmp_path: Path) -> Rig:
    return build_rig(make_window, qtbot, tmp_path, open_path=None)


# G7 / D81: skip, log, continue, report.


def _run_three_with_a_failure(rig: Rig) -> BatchPanel:
    batch = started(rig, [A, B, C], fail=(B.name,))
    batch.start()
    wait_batch_idle(rig)
    return batch


def test_a_failed_item_is_skipped_logged_and_reported(
    rig: Rig, caplog: pytest.LogCaptureFixture
) -> None:
    caplog.set_level(logging.INFO, logger="clearwater.gui.batch")
    batch = _run_three_with_a_failure(rig)
    assert states(batch) == STATES
    assert len(rig.outputs()) == 2 and [r.source.name for r in rig.stub.requests] == [
        "a.jpg",
        "b.mp4",
        "c.jpg",
    ]
    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1 and "b.mp4" in warnings[0].getMessage()
    assert "could not be read" in warnings[0].getMessage()
    report = batch.report.toPlainText()
    assert "Batch finished: 3 items." in report
    assert "Succeeded 2, with warnings 0, failed 1, cancelled 0, not run 0." in report
    assert "2. b.mp4 - FAILED" in report and "failure: b.mp4 could not be read" in report
    assert report.count("output: ") == 2
    info = [r.getMessage() for r in caplog.records if r.levelno == logging.INFO]
    assert any("Batch finished: 3 items." in text for text in info)
    assert rig.action.unavailable_reason() == NO_SOURCE_REASON  # the batch's reason is gone


def test_planted_batch_that_stops_at_the_first_failure_is_detected(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = BatchPanel._record

    def stopping(self: BatchPanel, item: BatchItem, result: Any) -> None:
        original(self, item, result)
        if item.state is ItemState.FAILED:
            self._cancel_requested = True

    monkeypatch.setattr(BatchPanel, "_record", stopping)
    batch = _run_three_with_a_failure(rig)
    assert states(batch) != STATES  # the test above fails on this implementation
    assert states(batch)[2] is ItemState.NOT_RUN


def test_warnings_are_counted_and_listed_per_item(rig: Rig) -> None:
    batch = started(rig, [A, C], warn=("soft clip",))
    batch.start()
    wait_batch_idle(rig)
    assert states(batch) == [ItemState.DONE_WITH_WARNINGS] * 2
    report = batch.report.toPlainText()
    assert "Succeeded 0, with warnings 2, failed 0" in report
    assert report.count("warning: soft clip") == 2


def test_warnings_of_failed_and_cancelled_items_are_kept_and_reported(rig: Rig) -> None:
    """Round-1 F2: IF-8 allows warnings on a result that is not ok; the report lists them."""
    batch = started(rig, [A, B, C], fail=(B.name,), warn=("probe warning",), warn_on_failure=True)
    batch.start()
    wait_batch_idle(rig)
    assert [i.warnings for i in batch.items()] == [("probe warning",)] * 3
    report = batch.report.toPlainText()
    lines = report.splitlines()
    at = lines.index("2. b.mp4 - FAILED")
    assert lines[at + 1 : at + 3] == [
        "   warning: probe warning",
        "   failure: b.mp4 could not be read",
    ]
    cancelled = started(rig, [A, B, C], fail=(), wait_on=(B.name,))
    cancelled.start()
    rig.qtbot.waitUntil(lambda: rig.stub.reached[B.name].is_set(), timeout=10000)
    cancelled.cancel_button.click()
    wait_batch_idle(rig)
    assert states(cancelled) == [
        ItemState.DONE_WITH_WARNINGS,
        ItemState.CANCELLED,
        ItemState.NOT_RUN,
    ]
    assert cancelled.items()[1].warnings == ("probe warning",)
    lines = cancelled.report.toPlainText().splitlines()
    at = lines.index("2. b.mp4 - cancelled")
    assert lines[at + 1] == "   warning: probe warning"


def test_a_job_that_cannot_be_built_or_raises_fails_its_item_only(rig: Rig) -> None:
    batch = started(rig, [A, B, C], raise_on_build=(B.name,), raise_in_job=(C.name,))
    batch.start()
    wait_batch_idle(rig)
    assert states(batch) == [ItemState.DONE, ItemState.FAILED, ItemState.FAILED]
    assert "cannot build b.mp4" in batch.items()[1].failure
    assert "boom c.jpg" in batch.items()[2].failure
    assert rig.action.unavailable_reason() == NO_SOURCE_REASON


def test_a_fault_while_recording_an_item_never_leaves_the_batch_running(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    def broken(self: BatchPanel, item: BatchItem, result: Any) -> None:
        raise RuntimeError("record failed")

    monkeypatch.setattr(BatchPanel, "_record", broken)
    batch = started(rig, [A, C])
    batch.start()
    wait_batch_idle(rig)
    assert states(batch) == [ItemState.FAILED, ItemState.FAILED]
    assert not batch.is_running() and rig.action.unavailable_reason() == NO_SOURCE_REASON


def test_the_reason_is_cleared_even_when_showing_the_report_fails(
    rig: Rig, qtbot: Any, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    batch = started(rig, [A])

    def explode(text: str) -> None:
        raise RuntimeError("report failed")

    monkeypatch.setattr(batch.report, "setPlainText", explode)
    batch.start()
    wait_batch_idle(rig)
    assert "the batch loop failed" in caplog.text
    assert rig.action.unavailable_reason() == NO_SOURCE_REASON
    assert batch.add_button.isEnabled()


# One parameter set or preset for every item; snapshot at Start.


def test_one_parameter_set_and_settings_apply_to_every_item_and_are_fixed_at_start(
    rig: Rig, qtbot: Any
) -> None:
    batch = started(rig, [A, B, C], wait_on=(A.name,))
    chosen = rig.window.session.parameters()
    settings = rig.window.session.settings()
    batch.start()
    qtbot.waitUntil(lambda: rig.stub.reached[A.name].is_set(), timeout=10000)
    # Changes after Start do not reach the running batch.
    rig.window.session.set_parameters(new_parameter_set("stub", {"later": 1}))
    rig.window.session.set_settings(replace(settings, output_suffix="_later"))
    rig.stub.release.set()
    wait_batch_idle(rig)
    assert len(rig.stub.requests) == 3
    assert all(r.parameters == chosen and r.settings == settings for r in rig.stub.requests)
    assert [r.kind for r in rig.stub.requests] == ["photo", "video", "photo"]


def test_a_preset_is_applied_to_every_item(rig: Rig) -> None:
    rig.window.context.presets.save("mine", new_parameter_set("stub", {}))
    batch = started(rig, [A, C])
    batch.refresh_presets()
    labels = [batch.parameter_combo.itemText(i) for i in range(batch.parameter_combo.count())]
    assert labels[0] == CURRENT_PARAMETERS and "mine" in labels
    batch.parameter_combo.setCurrentIndex(labels.index("mine"))
    batch.start()
    wait_batch_idle(rig)
    assert states(batch) == [ItemState.DONE, ItemState.DONE]
    stored = rig.window.context.presets.load("mine")
    assert all(
        (r.parameters.method, dict(r.parameters.parameters)) == (stored.method, {})
        for r in rig.stub.requests
    )


@pytest.mark.parametrize(
    ("method", "values", "fragment"),
    [("nope", {}, "not available"), ("stub", {"bogus": 1}, "not valid")],
)
def test_a_preset_the_methods_cannot_use_refuses_the_start(
    rig: Rig, method: str, values: dict[str, Any], fragment: str
) -> None:
    rig.window.context.presets.save("bad", new_parameter_set(method, values))
    batch = started(rig, [A, C])
    batch.refresh_presets()
    batch.parameter_combo.setCurrentIndex(batch.parameter_combo.findData("bad"))
    batch.start()
    assert not batch.is_running() and rig.stub.requests == []
    (error,) = presenter_of(rig.window).of("error")
    assert error.owner == "batch" and "bad" in error.text and fragment in error.text
    assert states(batch) == [ItemState.QUEUED] * 2
    assert rig.action.unavailable_reason() == NO_SOURCE_REASON


def test_a_preset_deleted_after_it_was_chosen_refuses_the_start(rig: Rig) -> None:
    store = rig.window.context.presets
    store.save("gone", new_parameter_set("stub", {}))
    batch = started(rig, [A])
    batch.refresh_presets()
    batch.parameter_combo.setCurrentIndex(batch.parameter_combo.findData("gone"))
    store.delete("gone")
    batch.start()
    assert not batch.is_running() and rig.stub.requests == []
    (error,) = presenter_of(rig.window).of("error")
    assert "gone" in error.text and "no longer available" in error.text


def test_the_start_refusal_is_cleared_by_the_next_start(rig: Rig) -> None:
    rig.window.context.presets.save("bad", new_parameter_set("nope", {}))
    batch = started(rig, [A])
    batch.refresh_presets()
    batch.parameter_combo.setCurrentIndex(batch.parameter_combo.findData("bad"))
    batch.start()
    assert len(presenter_of(rig.window).of("error")) == 1
    batch.parameter_combo.setCurrentIndex(0)
    batch.start()
    wait_batch_idle(rig)
    assert presenter_of(rig.window).of("error") == []


# D45 / G8: cancel stops the whole remaining batch.


def _cancel_during_the_second(rig: Rig, *, click: bool = True) -> BatchPanel:
    batch = started(rig, [A, B, C], wait_on=(B.name,))
    batch.start()
    rig.qtbot.waitUntil(lambda: rig.stub.reached[B.name].is_set(), timeout=10000)
    if click:
        batch.cancel_button.click()
    else:  # the button is connected to the original method; call the (planted) one
        batch.cancel()
    wait_batch_idle(rig)
    return batch


def test_cancel_stops_the_remaining_items_and_keeps_completed_outputs(rig: Rig) -> None:
    batch = _cancel_during_the_second(rig)
    assert states(batch) == [ItemState.DONE, ItemState.CANCELLED, ItemState.NOT_RUN]
    assert [r.source.name for r in rig.stub.requests] == ["a.jpg", "b.mp4"]  # c never started
    names = rig.outputs()
    assert len(names) == 1 and names[0].startswith("a")  # a kept; b's temporary removed (G8)
    assert not any(".clearwater-partial-" in n for n in names)
    report = batch.report.toPlainText()
    assert "Batch cancelled: 3 items." in report
    assert "Succeeded 1, with warnings 0, failed 0, cancelled 1, not run 1." in report
    assert "2. b.mp4 - cancelled" in report and "3. c.jpg - not run" in report
    assert rig.action.unavailable_reason() == NO_SOURCE_REASON
    assert presenter_of(rig.window).of("error") == []


def test_planted_cancel_that_lets_the_next_item_start_is_detected(
    rig: Rig, monkeypatch: pytest.MonkeyPatch
) -> None:
    def cancel_only_the_job(self: BatchPanel) -> None:
        if self._handle is not None:
            self._handle.cancel()

    monkeypatch.setattr(BatchPanel, "cancel", cancel_only_the_job)
    monkeypatch.setattr(batch_module, "CANCELLED", "a different text")
    batch = _cancel_during_the_second(rig, click=False)
    assert [r.source.name for r in rig.stub.requests] == ["a.jpg", "b.mp4", "c.jpg"]
    assert states(batch)[2] is not ItemState.NOT_RUN  # the test above fails on this


def test_an_item_that_finishes_ok_after_the_cancel_is_done_and_the_rest_not_run(
    rig: Rig, qtbot: Any
) -> None:
    batch = started(rig, [A, B, C], wait_on=(B.name,), ignore_cancel=True)
    batch.start()
    qtbot.waitUntil(lambda: rig.stub.reached[B.name].is_set(), timeout=10000)
    batch.cancel()
    rig.stub.release.set()
    wait_batch_idle(rig)
    assert states(batch) == [ItemState.DONE, ItemState.DONE, ItemState.NOT_RUN]
    assert len(rig.outputs()) == 2


def test_a_cancelled_result_without_a_click_also_stops_the_batch(rig: Rig) -> None:
    """The runner's own cancel (window close) returns CANCELLED: no further job starts."""
    batch = started(rig, [A, B, C], wait_on=(B.name,))
    batch.start()
    rig.qtbot.waitUntil(lambda: rig.stub.reached[B.name].is_set(), timeout=10000)
    rig.window.jobs.cancel()
    wait_batch_idle(rig)
    assert states(batch) == [ItemState.DONE, ItemState.CANCELLED, ItemState.NOT_RUN]


# The queue (D83), locking, the one-activity rule.


def test_refused_files_are_warned_about_and_duplicates_are_not_queued(rig: Rig) -> None:
    batch = batch_of(rig)
    ok = Path("ok.mp4")
    batch.add_paths([Path("cam.LRV"), Path("notes.xyz"), ok, ok, Path("sub") / ".." / "ok.mp4"])
    assert [i.path for i in batch.items()] == [ok]
    warnings = presenter_of(rig.window).of("warning")
    assert len(warnings) == 2 and {w.owner for w in warnings} == {"batch"}
    assert any("cam.LRV" in w.text for w in warnings)
    assert [batch.queue.item(i).text() for i in range(batch.queue.count())] == ["ok.mp4 - queued"]


def test_the_add_remove_and_clear_buttons(rig: Rig) -> None:
    batch = batch_of(rig)
    batch._choose_files = lambda parent: [A, B, C]
    batch.add_button.click()
    assert [i.path for i in batch.items()] == [A, B, C]
    batch.queue.item(1).setSelected(True)
    assert batch.remove_button.isEnabled()
    batch.remove_button.click()
    assert [i.path for i in batch.items()] == [A, C]
    presenter_of(rig.window).present(Message("warning", "queue warning", None, "batch"))
    batch.clear_button.click()
    assert batch.items() == [] and not batch.start_button.isEnabled()
    assert presenter_of(rig.window).of("warning") == []  # Clear removes this panel's messages


def test_editing_is_locked_while_running_and_export_is_unavailable(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path)  # a photo is open: export would be available
    batch = started(rig, [A, C], wait_on=(A.name,))
    assert rig.action.isEnabled()
    batch.start()
    assert batch.is_running()
    assert rig.action.unavailable_reason() == RUNNING_BATCH_REASON and not rig.action.isEnabled()
    assert not any(
        w.isEnabled()
        for w in (
            batch.add_button,
            batch.remove_button,
            batch.clear_button,
            batch.parameter_combo,
            batch.start_button,
        )
    )
    assert batch.cancel_button.isEnabled()
    batch.add_paths([B])  # ignored while running
    batch.clear_queue()
    assert [i.path for i in batch.items()] == [A, C]
    assert batch.overall.text() == "Item 1 of 2: a.jpg"
    rig.action.trigger()  # disabled: no export starts
    assert rig.stub.requests[0].source == A and len(rig.stub.requests) == 1
    rig.stub.release.set()
    wait_batch_idle(rig)
    assert rig.action.unavailable_reason() is None and rig.action.isEnabled()
    assert batch.add_button.isEnabled() and batch.start_button.isEnabled()
    assert not batch.cancel_button.isEnabled()


def test_start_is_unavailable_while_an_export_runs(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(wait_on=(PHOTO.name,)))
    batch = batch_of(rig)
    batch.add_paths([A])
    assert batch.start_button.isEnabled()
    rig.action.trigger()
    assert rig.action.unavailable_reason() == RUNNING_EXPORT_REASON
    assert (
        not batch.start_button.isEnabled() and batch.start_button.toolTip() == RUNNING_EXPORT_REASON
    )
    batch.start()
    assert not batch.is_running()
    rig.stub.release.set()
    rig.wait_export_idle()
    assert batch.start_button.isEnabled()


def test_the_batch_needs_no_open_source_and_no_analysis(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    from gui_support import frame, video_engines

    rig = build_rig(
        make_window,
        qtbot,
        tmp_path,
        engines=video_engines([frame(8, 8, ticks=0)]),
        open_path=Path("clip.mp4"),
    )
    rig.window.session.set_analysis(AnalysisState("running", 1, 10, ""))
    assert not rig.action.isEnabled()  # AD-15 holds for the open clip's export
    batch = started(rig, [A])
    batch.start()
    wait_batch_idle(rig)
    assert states(batch) == [ItemState.DONE]
    assert not rig.action.isEnabled()  # still the shell's reason, nothing of the batch's left


# The report and re-running.


def test_the_report_stays_until_the_next_start_and_start_runs_the_whole_queue_again(
    rig: Rig, qtbot: Any
) -> None:
    batch = started(rig, [A, B, C], fail=(B.name,))
    batch.start()
    wait_batch_idle(rig)
    first = batch.report.toPlainText()
    assert first and states(batch) == STATES
    assert batch.start_button.isEnabled() and len(batch.items()) == 3  # the rows are kept
    rig.stub.fail = ()
    rig.stub.wait_on = (A.name,)
    batch.start()
    qtbot.waitUntil(lambda: rig.stub.reached[A.name].is_set(), timeout=10000)
    assert batch.report.toPlainText() == ""  # cleared at Start
    assert states(batch) == [ItemState.RUNNING, ItemState.QUEUED, ItemState.QUEUED]
    rig.stub.release.set()
    wait_batch_idle(rig)
    assert states(batch) == [ItemState.DONE] * 3
    assert "Succeeded 3" in batch.report.toPlainText()
    assert len(rig.stub.requests) == 6


def test_the_report_layout(rig: Rig) -> None:
    items = [
        BatchItem(Path("a.mp4"), "video", ItemState.DONE, (Path("out/a_c.mp4"),)),
        BatchItem(
            Path("b.jpg"), "photo", ItemState.DONE_WITH_WARNINGS, (Path("out/b_c.png"),), ("w",)
        ),
        BatchItem(Path("c.mp4"), "video", ItemState.FAILED, failure="bad"),
        BatchItem(Path("d.mp4"), "video", ItemState.CANCELLED),
        BatchItem(Path("e.mp4"), "video", ItemState.NOT_RUN),
    ]
    text = format_report(items, cancelled=True)
    assert text.splitlines() == [
        "Batch cancelled: 5 items.",
        "Succeeded 1, with warnings 1, failed 1, cancelled 1, not run 1.",
        "1. a.mp4 - done",
        f"   output: {Path('out/a_c.mp4')}",
        "2. b.jpg - done with warnings",
        f"   output: {Path('out/b_c.png')}",
        "   warning: w",
        "3. c.mp4 - FAILED",
        "   failure: bad",
        "4. d.mp4 - cancelled",
        "5. e.mp4 - not run",
    ]


# DR-44 (b).


def test_another_owners_error_survives_the_batch(rig: Rig) -> None:
    presenter = presenter_of(rig.window)
    presenter.present(Message("error", "preview failed", None, "shell.preview"))
    presenter.present(Message("warning", "export warning", None, "export"))
    batch = started(rig, [A, C])
    batch.add_paths([Path("x.LRV")])
    batch.start()
    wait_batch_idle(rig)
    assert [m.owner for m in presenter.of("error")] == ["shell.preview"]
    assert [m.owner for m in presenter.of("warning")] == ["export"]  # batch warnings cleared


# V7 (D66).


def test_v7_interface_never_waits_more_than_100_ms_during_a_batch(rig: Rig, qtbot: Any) -> None:
    batch = started(rig, [A, C], busy_s=1.0)
    worst = _probe_max_gap_ms(
        qtbot, batch.start, lambda: not batch.is_running() and len(rig.stub.finished) == 2
    )
    print(f"V7 batch: observed maximum main-thread gap {worst:.0f} ms")  # informational
    assert worst <= V7_BOUND_MS
    assert threading.main_thread() not in rig.stub.run_threads
    assert states(batch) == [ItemState.DONE, ItemState.DONE]
