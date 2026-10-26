"""WP3.19 export panel (G8, G9, D43, D44, AD-15, DR-44 (b), V7) and the export seam.

The test-side ``StubExportJobs`` stands in for WP3.14's engine: it writes a small file under
``tmp_path`` through ``plan_output`` and ``SafeWrite`` with one ``Reservations`` per job, so the
G8 cleanup legs run through the real safe-write machinery. It can fail, raise, wait on an event,
or busy the CPU, and it records the thread of every build and every run.
"""

# The shared fixture ``make_window`` is imported from gui_support and used as a parameter.
# ruff: noqa: F401, F811

from __future__ import annotations

import subprocess
import sys
import threading
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Any

import pytest
from PySide6.QtCore import QElapsedTimer, QTimer
from PySide6.QtWidgets import QDockWidget

from clearwater.config import new_parameter_set
from clearwater.gui import AnalysisState, MainWindow, Message
from clearwater.gui import export_service as gui_export_service
from clearwater.gui.export_panel import ExportPanel, install_export_panels
from clearwater.gui.export_service import (
    RUNNING_BATCH_REASON,
    RUNNING_EXPORT_REASON,
    ActivityGate,
    SharedGate,
)
from clearwater.gui.shell import EXPORT_NOT_CONNECTED, NEEDS_ANALYSIS_REASON, NO_SOURCE_REASON
from clearwater.interfaces import JobResult, Settings
from clearwater.jobs import MediaKind, Reservations, SafeWrite, export_seam, plan_output
from clearwater.jobs.export_seam import (
    CANCELLED,
    UNAVAILABLE_TEXT,
    ExportRequest,
    unavailable_exports,
)
from gui_support import (
    busy_numpy,
    frame,
    image,
    make_window,
    open_and_wait,
    photo_engines,
    presenter_of,
    video_engines,
)

pytestmark = pytest.mark.gui

V7_BOUND_MS = 100
PHOTO = Path("photo.jpg")
CLIP = Path("clip.mp4")


class StubExportJobs:
    """A test ``ExportJobs`` that writes real files through ``plan_output`` and ``SafeWrite``.

    Attributes:
        requests: Every request, in the order ``job`` was called.
        build_threads: The thread of every ``job`` call.
        run_threads: The thread of every job run.
        reached: Per source name, set when that job reached its wait point.
        release: Set to let every waiting job go on.
        result: When set, every job returns exactly this ``JobResult`` at once.
    """

    def __init__(
        self,
        *,
        fail: tuple[str, ...] = (),
        raise_in_job: tuple[str, ...] = (),
        raise_on_build: tuple[str, ...] = (),
        wait_on: tuple[str, ...] = (),
        warn: tuple[str, ...] = (),
        busy_s: float = 0.0,
        chunks: int = 4,
        ignore_cancel: bool = False,
        warn_on_failure: bool = False,
        result: JobResult | None = None,
    ) -> None:
        self.fail = fail
        self.raise_in_job = raise_in_job
        self.raise_on_build = raise_on_build
        self.wait_on = wait_on
        self.warn = warn
        self.busy_s = busy_s
        self.chunks = chunks
        self.ignore_cancel = ignore_cancel
        self.warn_on_failure = warn_on_failure
        self.result = result
        self.requests: list[ExportRequest] = []
        self.build_threads: list[threading.Thread] = []
        self.run_threads: list[threading.Thread] = []
        self.reached: dict[str, threading.Event] = defaultdict(threading.Event)
        self.release = threading.Event()
        self.finished: list[str] = []

    def job(self, request: ExportRequest) -> Callable[[Any], JobResult]:
        self.requests.append(request)
        self.build_threads.append(threading.current_thread())
        name = request.source.name
        if name in self.raise_on_build:
            raise ValueError(f"cannot build {name}")

        def run(progress: Any) -> JobResult:
            start = time.perf_counter()
            self.run_threads.append(threading.current_thread())

            def done(ok: bool, outputs: tuple[Path, ...] = (), failure: str | None = None) -> Any:
                self.finished.append(name)
                warnings = self.warn if ok or self.warn_on_failure else ()
                return JobResult(ok, outputs, warnings, failure, "cpu", time.perf_counter() - start)

            if self.result is not None:  # a fixed result, returned as the engine's answer
                self.finished.append(name)
                return self.result
            if name in self.raise_in_job:
                raise RuntimeError(f"boom {name}")
            if name in self.fail:
                return done(False, failure=f"{name} could not be read")
            reservations = Reservations()
            plan = plan_output(
                request.source, request.settings, MediaKind(request.kind), reservations
            )
            with SafeWrite(plan, reservations) as write:
                with open(write.temp_path, "wb") as handle:
                    for step in range(self.chunks):
                        if progress.cancelled() and not self.ignore_cancel:
                            return done(False, failure=CANCELLED)
                        handle.write(b"x" * 64)
                        progress.report(step + 1, self.chunks, f"step {step + 1}")
                        if step == 0:
                            if self.busy_s:
                                busy_numpy(self.busy_s)()
                            if name in self.wait_on:
                                self.reached[name].set()
                                end = time.perf_counter() + 20.0
                                while not self.release.is_set() and time.perf_counter() < end:
                                    if progress.cancelled() and not self.ignore_cancel:
                                        return done(False, failure=CANCELLED)
                                    time.sleep(0.005)
                final = write.commit()
            return done(True, (final,))

        return run


@dataclass
class Rig:
    """A window with the panels installed on a stub engine, and its folders."""

    window: MainWindow
    stub: StubExportJobs
    out: Path
    qtbot: Any

    @property
    def action(self) -> Any:
        return self.window.context.actions.export

    @property
    def panel(self) -> ExportPanel:
        return self.window.findChildren(ExportPanel)[0]

    def outputs(self) -> list[str]:
        return sorted(p.name for p in self.out.iterdir())

    def wait_export_idle(self) -> None:
        self.qtbot.waitUntil(lambda: not self.panel.is_running(), timeout=15000)


def build_rig(
    make_window: Callable[..., MainWindow],
    qtbot: Any,
    tmp_path: Path,
    *,
    stub: StubExportJobs | None = None,
    engines: Any = None,
    open_path: Path | None = PHOTO,
    install: bool = True,
) -> Rig:
    """Build a window (a photo open unless ``open_path`` is None) with the panels installed."""
    engines = engines or photo_engines({PHOTO: image(8, 8)})
    window = make_window(engines)
    out = tmp_path / "out"
    out.mkdir()
    window.session.set_settings(replace(window.session.settings(), output_folder=out))
    stub = stub or StubExportJobs()
    if install:
        install_export_panels(window, stub)
    if open_path is not None:
        open_and_wait(qtbot, window, open_path)
    return Rig(window, stub, out, qtbot)


# The seam.


def test_the_seam_module_loads_no_pyside6() -> None:
    code = (
        "import sys\n"
        "import clearwater.jobs.export_seam\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in ('PySide6', 'shiboken6'))\n"
        "print(','.join(bad))\n"
    )
    out = subprocess.run(
        [sys.executable, "-I", "-c", code], capture_output=True, text=True, check=True, timeout=120
    )
    assert out.stdout.strip() == ""


def test_the_gui_module_re_exports_the_seam() -> None:
    for name in ("CANCELLED", "UNAVAILABLE_TEXT", "ExportRequest", "ExportJobs"):
        assert getattr(gui_export_service, name) is getattr(export_seam, name)
    assert gui_export_service.unavailable_exports is export_seam.unavailable_exports


def test_the_unavailable_default_fails_and_writes_nothing(tmp_path: Path) -> None:
    request = ExportRequest(
        tmp_path / "a.jpg",
        "photo",
        new_parameter_set("stub", {}),
        Settings(output_folder=tmp_path),
    )
    job = unavailable_exports().job(request)
    result = job(_NoProgress())
    assert (result.ok, result.outputs, result.failure) == (False, (), UNAVAILABLE_TEXT)
    assert list(tmp_path.iterdir()) == []


class _NoProgress:
    def report(self, done: int, total: int | None, message: str) -> None:
        pass

    def cancelled(self) -> bool:
        return False


def test_activity_gate_allows_one_activity_and_survives_a_failing_subscriber(
    caplog: pytest.LogCaptureFixture,
) -> None:
    reasons: list[str | None] = []
    gate = ActivityGate(reasons.append)
    assert reasons == [None] and gate.current is None
    seen: list[Any] = []
    gate.subscribe(lambda current: (_ for _ in ()).throw(RuntimeError("bad subscriber")))
    gate.subscribe(seen.append)
    assert gate.try_start("export") is True
    assert gate.try_start("batch") is False
    assert reasons[-1] == RUNNING_EXPORT_REASON == gate.reason()
    gate.finish("batch")  # not the holder: ignored
    assert gate.current == "export"
    gate.finish("export")
    assert reasons[-1] is None and gate.current is None
    assert seen == ["export", None]  # the second subscriber still ran after the first raised
    assert gate.try_start("batch") and gate.reason() == RUNNING_BATCH_REASON


def test_shared_gate_creates_one_gate() -> None:
    calls: list[str | None] = []
    shared = SharedGate()
    first = shared.get(calls.append)
    assert shared.get(lambda reason: None) is first and calls == [None]


# The export panel.


def test_install_clears_the_not_available_reason(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, install=False)
    assert rig.action.unavailable_reason() == EXPORT_NOT_CONNECTED and not rig.action.isEnabled()
    install_export_panels(rig.window, rig.stub)
    assert rig.action.unavailable_reason() is None and rig.action.isEnabled()
    names = [d.objectName() for d in rig.window.findChildren(QDockWidget)]
    assert "jobs:Export" in names and "jobs:Batch" in names


def test_the_shells_reasons_still_hold_after_install(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, open_path=None)
    assert rig.action.unavailable_reason() == NO_SOURCE_REASON and not rig.action.isEnabled()
    rig.action.trigger()  # disabled: nothing starts
    assert rig.stub.requests == []


def test_triggering_exports_the_open_source_with_a_snapshot_request(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path)
    before = rig.window.session.parameters()
    settings = rig.window.session.settings()
    rig.stub.wait_on = (PHOTO.name,)
    rig.action.trigger()
    qtbot.waitUntil(lambda: rig.stub.reached[PHOTO.name].is_set(), timeout=10000)
    # The request was made at trigger time; later changes do not reach it.
    rig.window.session.set_settings(replace(settings, output_suffix="_later"))
    rig.stub.release.set()
    rig.wait_export_idle()
    (request,) = rig.stub.requests
    assert (request.source, request.kind) == (PHOTO, "photo")
    assert request.parameters == before and request.settings == settings
    assert request.settings.output_suffix != "_later"
    assert len(rig.outputs()) == 1
    assert rig.panel.status.text().startswith("Saved ")


def test_progress_reaches_the_bar_and_a_missing_total_is_a_busy_bar(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(wait_on=(PHOTO.name,)))
    rig.action.trigger()
    qtbot.waitUntil(lambda: rig.stub.reached[PHOTO.name].is_set(), timeout=10000)
    qtbot.waitUntil(lambda: rig.panel.bar.maximum() == 4, timeout=5000)
    assert rig.panel.bar.value() >= 1
    rig.panel._progress(0, None, "busy")
    assert (rig.panel.bar.minimum(), rig.panel.bar.maximum()) == (0, 0)
    rig.stub.release.set()
    rig.wait_export_idle()


def test_the_reason_while_running_and_after(make_window: Any, qtbot: Any, tmp_path: Path) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(wait_on=(PHOTO.name,)))
    rig.action.trigger()
    assert rig.action.unavailable_reason() == RUNNING_EXPORT_REASON
    assert not rig.action.isEnabled() and rig.panel.cancel_button.isEnabled()
    rig.action.trigger()  # a second trigger while running changes nothing
    rig.stub.release.set()
    rig.wait_export_idle()
    assert rig.action.unavailable_reason() is None and rig.action.isEnabled()
    assert len(rig.stub.requests) == 1


def test_the_reason_is_cleared_even_when_the_presenter_raises(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(warn=("a warning",)))

    def explode(message: Message) -> None:
        raise RuntimeError("presenter failed")

    rig.window.presenter.present = explode  # type: ignore[method-assign]
    with qtbot.capture_exceptions() as caught:
        rig.action.trigger()
        qtbot.waitUntil(lambda: bool(caught), timeout=10000)
    assert any("presenter failed" in str(e[1]) for e in caught)
    assert rig.action.unavailable_reason() is None and rig.action.isEnabled()
    assert not rig.panel.is_running()


def test_the_reason_is_cleared_when_setup_raises_after_the_gate_is_taken(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    """Round-1 F1: a fault between ``try_start`` and the job must not hold the gate."""
    rig = build_rig(make_window, qtbot, tmp_path)

    def explode(severity: str | None = None, *, owner: str | None = None) -> None:
        raise RuntimeError("clear failed")

    rig.window.presenter.clear = explode  # type: ignore[method-assign]
    rig.action.trigger()
    assert not rig.panel.is_running()
    assert rig.action.unavailable_reason() is None and rig.action.isEnabled()
    (error,) = presenter_of(rig.window).of("error")
    assert "clear failed" in error.text and error.owner == "export"
    assert rig.stub.requests == [] and not rig.panel.cancel_button.isEnabled()


def _trigger_with_failing_parameters(rig: Rig, monkeypatch: pytest.MonkeyPatch) -> None:
    """Make ``session.parameters`` raise, then call the panel's trigger handler directly."""

    def explode() -> None:
        raise RuntimeError("parameters failed")

    original = rig.window.session.parameters
    monkeypatch.setattr(rig.window.session, "parameters", explode)
    try:
        rig.panel._on_triggered()
    finally:  # the window's close (fixture teardown) saves the parameters: restore them first
        monkeypatch.setattr(rig.window.session, "parameters", original)


def test_the_reason_is_cleared_when_building_the_request_raises(
    make_window: Any, qtbot: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Round-2 minor 1: request construction is inside the guarded block too."""
    rig = build_rig(make_window, qtbot, tmp_path)
    _trigger_with_failing_parameters(rig, monkeypatch)
    assert not rig.panel.is_running()
    assert rig.action.unavailable_reason() is None and rig.action.isEnabled()
    (error,) = presenter_of(rig.window).of("error")
    assert "parameters failed" in error.text and error.owner == "export"


def test_planted_request_built_outside_the_guard_holds_the_gate(
    make_window: Any, qtbot: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def unguarded(self: ExportPanel, *_: object) -> None:
        source = self._context.session.source()
        assert source is not None and self._gate.try_start("export")
        self._running = True
        ExportRequest(
            source.path, source.kind, self._context.session.parameters(), Settings()
        )  # raises before any guard

    rig = build_rig(make_window, qtbot, tmp_path)
    monkeypatch.setattr(ExportPanel, "_on_triggered", unguarded)
    with pytest.raises(RuntimeError, match="parameters failed"):
        _trigger_with_failing_parameters(rig, monkeypatch)
    # The test above fails on this implementation: the reason stays set with nothing running.
    assert rig.action.unavailable_reason() == RUNNING_EXPORT_REASON


def test_success_clears_only_the_export_errors_and_presents_warnings(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(warn=("w1", "w2")))
    presenter = presenter_of(rig.window)
    presenter.present(Message("error", "preview failed", None, "shell.preview"))
    presenter.present(Message("error", "earlier export failed", None, "export"))
    rig.action.trigger()
    rig.wait_export_idle()
    errors = [m.owner for m in presenter.of("error")]
    assert errors == ["shell.preview"]  # DR-44 (b): another owner's error survives
    warnings = presenter.of("warning")
    assert [(m.text, m.owner) for m in warnings] == [("w1", "export"), ("w2", "export")]
    rig.action.trigger()  # a new export clears this panel's earlier warnings first
    rig.wait_export_idle()
    assert len(presenter.of("warning")) == 2


def test_failure_is_an_error_naming_the_file_with_owner_export(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(fail=(PHOTO.name,)))
    rig.action.trigger()
    rig.wait_export_idle()
    (error,) = presenter_of(rig.window).of("error")
    assert (
        error.owner == "export" and PHOTO.name in error.text and "could not be read" in error.text
    )
    assert rig.outputs() == [] and rig.action.isEnabled()


def test_a_job_that_raises_is_a_failed_export(make_window: Any, qtbot: Any, tmp_path: Path) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(raise_in_job=(PHOTO.name,)))
    rig.action.trigger()
    rig.wait_export_idle()
    (error,) = presenter_of(rig.window).of("error")
    assert "boom" in error.text and error.owner == "export"
    assert rig.action.unavailable_reason() is None


def test_a_job_that_cannot_be_built_is_a_failed_export(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(raise_on_build=(PHOTO.name,)))
    rig.action.trigger()
    assert not rig.panel.is_running()
    (error,) = presenter_of(rig.window).of("error")
    assert "cannot build" in error.text
    assert rig.action.unavailable_reason() is None


def test_cancel_shows_cancelled_and_leaves_no_partial_output(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    """G8, D44: the stub's SafeWrite aborts, so no temporary and no final file remain."""
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(wait_on=(PHOTO.name,)))
    rig.action.trigger()
    qtbot.waitUntil(lambda: rig.stub.reached[PHOTO.name].is_set(), timeout=10000)
    assert any(".clearwater-partial-" in n for n in rig.outputs())  # a temporary exists now
    rig.panel.cancel_button.click()
    assert rig.panel.status.text() == "Cancelling..." and not rig.panel.cancel_button.isEnabled()
    rig.wait_export_idle()
    assert rig.panel.status.text() == "Export cancelled."
    assert presenter_of(rig.window).of("error") == []
    assert rig.outputs() == []
    assert rig.action.unavailable_reason() is None


def test_a_job_that_finishes_ok_after_a_cancel_keeps_its_output(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    """G8: completed files are kept; the result, not the click, decides what is shown."""
    stub = StubExportJobs(wait_on=(PHOTO.name,), ignore_cancel=True)
    rig = build_rig(make_window, qtbot, tmp_path, stub=stub)
    rig.action.trigger()
    qtbot.waitUntil(lambda: stub.reached[PHOTO.name].is_set(), timeout=10000)
    rig.panel.cancel_button.click()
    stub.release.set()
    rig.wait_export_idle()
    assert rig.panel.status.text().startswith("Saved ")
    assert len(rig.outputs()) == 1 and presenter_of(rig.window).of("error") == []


KEPT = (Path("saved-1.png"), Path("saved-2.png"))
NOT_OK_RESULTS = {
    "failed": JobResult(False, KEPT, ("probe warning", "second warning"), "disk full", "cpu", 0.0),
    "cancelled": JobResult(False, KEPT, ("probe warning", "second warning"), CANCELLED, "cpu", 0.0),
}


@pytest.mark.parametrize("kind", ["failed", "cancelled"])
def test_outputs_and_warnings_of_a_non_ok_result_are_named_and_presented(
    make_window: Any, qtbot: Any, tmp_path: Path, kind: str
) -> None:
    """Reviewer B pass 1 major: IF-8 allows both on a result that is not ok; neither is dropped."""
    stub = StubExportJobs(result=NOT_OK_RESULTS[kind])
    rig = build_rig(make_window, qtbot, tmp_path, stub=stub)
    rig.action.trigger()
    rig.wait_export_idle()
    status = rig.panel.status.text()
    assert "Saved before the stop: saved-1.png, saved-2.png" in status
    assert status.startswith("Export cancelled." if kind == "cancelled" else "Export of photo.jpg")
    presenter = presenter_of(rig.window)
    assert [(m.text, m.owner) for m in presenter.of("warning")] == [
        ("probe warning", "export"),
        ("second warning", "export"),
    ]
    errors = presenter.of("error")
    if kind == "failed":
        (error,) = errors
        assert error.owner == "export" and "disk full" in error.text
    else:
        assert errors == []
    assert rig.action.unavailable_reason() is None


def test_a_non_ok_result_without_outputs_adds_no_saved_line(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    result = JobResult(False, (), (), CANCELLED, "cpu", 0.0)
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(result=result))
    rig.action.trigger()
    rig.wait_export_idle()
    assert rig.panel.status.text() == "Export cancelled."
    assert presenter_of(rig.window).of("warning") == []


@pytest.mark.parametrize("kind", ["failed", "cancelled"])
def test_planted_done_that_drops_outputs_and_warnings_of_a_non_ok_result_is_detected(
    make_window: Any, qtbot: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, kind: str
) -> None:
    original = ExportPanel._done

    def dropping(self: ExportPanel, path: Path, result: JobResult) -> None:
        original(self, path, result if result.ok else replace(result, outputs=(), warnings=()))

    monkeypatch.setattr(ExportPanel, "_done", dropping)
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(result=NOT_OK_RESULTS[kind]))
    rig.action.trigger()
    rig.wait_export_idle()
    # The test above fails on this implementation.
    assert "Saved before the stop" not in rig.panel.status.text()
    assert presenter_of(rig.window).of("warning") == []


NO_OUTPUT = "Export finished, but no output file was reported."


def test_an_ok_result_without_outputs_is_not_reported_as_saved(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    """Reviewer B pass 2: never claim "Saved <source>" when no output file was reported."""
    result = JobResult(True, (), (), None, "cpu", 0.0)
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(result=result))
    rig.action.trigger()
    rig.wait_export_idle()
    assert rig.panel.status.text() == NO_OUTPUT
    presenter = presenter_of(rig.window)
    assert [(m.text, m.owner) for m in presenter.of("warning")] == [(NO_OUTPUT, "export")]
    assert presenter.of("error") == [] and rig.action.unavailable_reason() is None


def test_planted_done_that_shows_the_source_name_for_an_ok_result_without_outputs(
    make_window: Any, qtbot: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = ExportPanel._done

    def guessing(self: ExportPanel, path: Path, result: JobResult) -> None:
        original(self, path, result)
        if result.ok and not result.outputs:
            self.status.setText(f"Saved {path.name}")

    monkeypatch.setattr(ExportPanel, "_done", guessing)
    rig = build_rig(
        make_window,
        qtbot,
        tmp_path,
        stub=StubExportJobs(result=JobResult(True, (), (), None, "cpu", 0.0)),
    )
    rig.action.trigger()
    rig.wait_export_idle()
    # The test above fails on this implementation.
    assert rig.panel.status.text() == "Saved photo.jpg"


def _close_the_runner(rig: Rig) -> None:
    """Close the window's job runner, as the shell does at close: ``run`` then raises."""
    assert rig.window.context.jobs.close(5.0)  # type: ignore[attr-defined]


def test_a_closed_runner_fails_the_export_and_releases_the_gate(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    """Reviewer B pass 1 minor: ``QtJobRunner.run`` raises once the runner is closed."""
    rig = build_rig(make_window, qtbot, tmp_path)
    _close_the_runner(rig)
    rig.action.trigger()
    assert not rig.panel.is_running()
    (error,) = presenter_of(rig.window).of("error")
    assert error.owner == "export" and "the job runner is closed" in error.text
    assert rig.panel.status.text().startswith("Export of photo.jpg failed.")
    assert rig.panel._gate.current is None
    assert rig.action.unavailable_reason() is None and rig.action.isEnabled()
    assert not rig.panel.cancel_button.isEnabled()


def test_planted_gate_leak_on_a_closed_runner_is_detected(
    make_window: Any, qtbot: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = ActivityGate.finish

    def leaking(self: ActivityGate, activity: Any) -> None:
        if rig.window.context.jobs._closed:  # type: ignore[attr-defined]
            return  # the leak: a closed runner's failure never releases the gate
        original(self, activity)

    rig = build_rig(make_window, qtbot, tmp_path)
    _close_the_runner(rig)
    monkeypatch.setattr(ActivityGate, "finish", leaking)
    rig.action.trigger()
    # The test above fails on this implementation: the gate still holds "export".
    assert rig.panel._gate.current == "export"
    assert not rig.panel.is_running()
    monkeypatch.undo()
    rig.panel._gate.finish("export")  # let the fixture teardown see a free gate


def test_the_open_source_changing_does_not_cancel_the_export(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    other = Path("other.jpg")
    engines = photo_engines({PHOTO: image(8, 8), other: image(8, 8, seed=1)})
    rig = build_rig(
        make_window, qtbot, tmp_path, stub=StubExportJobs(wait_on=(PHOTO.name,)), engines=engines
    )
    rig.action.trigger()
    qtbot.waitUntil(lambda: rig.stub.reached[PHOTO.name].is_set(), timeout=10000)
    open_and_wait(qtbot, rig.window, other)
    rig.stub.release.set()
    rig.wait_export_idle()
    assert rig.panel.status.text().startswith("Saved ")
    assert len(rig.outputs()) == 1 and rig.outputs()[0].startswith("photo")


def test_the_product_default_reports_that_export_is_unavailable(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    window = make_window(photo_engines({PHOTO: image(8, 8)}))
    (tmp_path / "out").mkdir()
    install_export_panels(window)  # no engine: unavailable_exports()
    open_and_wait(qtbot, window, PHOTO)
    window.context.actions.export.trigger()
    panel = window.findChildren(ExportPanel)[0]
    qtbot.waitUntil(lambda: not panel.is_running(), timeout=10000)
    (error,) = presenter_of(window).of("error")
    assert UNAVAILABLE_TEXT in error.text
    assert list((tmp_path / "out").iterdir()) == []


def test_the_export_job_runs_on_a_worker_thread(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path)
    rig.action.trigger()
    rig.wait_export_idle()
    assert rig.stub.run_threads and threading.main_thread() not in rig.stub.run_threads
    assert rig.stub.build_threads == [threading.main_thread()]


def test_planted_export_run_on_the_main_thread_is_detected(
    make_window: Any, qtbot: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path)

    class Handle:
        def cancel(self) -> None:
            pass

        def is_running(self) -> bool:
            return False

    def inline_run(job: Any, *, on_done: Any, on_progress: Any = None) -> Handle:
        on_done(job(_NoProgress()))
        return Handle()

    monkeypatch.setattr(rig.window.jobs, "run", inline_run)
    rig.action.trigger()
    rig.wait_export_idle()
    # The check of the test above fails on this implementation.
    assert threading.main_thread() in rig.stub.run_threads


# AD-15.


def _ad15_scenario(
    make_window: Any, qtbot: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch | None = None
) -> Rig:
    """A video whose analysis is running, then the panels installed; returns the rig."""
    engines = video_engines([frame(8, 8, ticks=0)])
    rig = build_rig(make_window, qtbot, tmp_path, engines=engines, open_path=CLIP, install=False)
    rig.window.session.set_analysis(AnalysisState("running", 3, 10, ""))
    if monkeypatch is not None:  # the planted panel enables the action itself
        action = rig.action
        monkeypatch.setattr(
            SharedGate,
            "get",
            lambda self, apply: ActivityGate(lambda r: action.setEnabled(r is None)),
        )
    install_export_panels(rig.window, rig.stub)
    return rig


def test_ad15_clearing_this_packages_reason_leaves_the_shells_reason(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = _ad15_scenario(make_window, qtbot, tmp_path)
    assert not rig.action.isEnabled()
    assert (
        rig.action.unavailable_reason() == "Export is available when the analysis completes: 3/10."
    )
    rig.window.session.set_analysis(AnalysisState("complete", 10, 10, ""))
    assert rig.action.isEnabled() and rig.action.unavailable_reason() is None
    rig.window.session.set_analysis(AnalysisState("cancelled"))
    assert rig.action.unavailable_reason() == NEEDS_ANALYSIS_REASON


def test_planted_set_enabled_during_analysis_is_detected(
    make_window: Any, qtbot: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    rig = _ad15_scenario(make_window, qtbot, tmp_path, monkeypatch)
    # The AD-15 check of the test above ("not enabled during the analysis") fails here.
    assert rig.action.isEnabled()


# V7 (D66): the interface never waits more than 100 ms while an export runs.


def _probe_max_gap_ms(qtbot: Any, start: Callable[[], None], until: Callable[[], bool]) -> float:
    """Run a 10 ms QTimer on the main thread, call ``start`` once it runs; the longest gap."""
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
        qtbot.waitUntil(until, timeout=30000)
    finally:
        timer.stop()
    tick()
    return float(worst[0])


def test_v7_interface_never_waits_more_than_100_ms_during_an_export(
    make_window: Any, qtbot: Any, tmp_path: Path
) -> None:
    rig = build_rig(make_window, qtbot, tmp_path, stub=StubExportJobs(busy_s=2.0))
    worst = _probe_max_gap_ms(
        qtbot, rig.action.trigger, lambda: bool(rig.stub.finished) and not rig.panel.is_running()
    )
    print(f"V7 export: observed maximum main-thread gap {worst:.0f} ms")  # informational
    assert worst <= V7_BOUND_MS
    assert threading.main_thread() not in rig.stub.run_threads
