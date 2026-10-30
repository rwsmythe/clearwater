"""The entry point: ``python -m clearwater`` and :func:`main` (WP4.3).

The only ``clearwater.app`` module that imports ``clearwater.gui`` or loads Qt.
:func:`build_application` makes the program the owner starts, in the round-0 order as ruled
(questions 4 and 11, S1 (a), S-order):

1. The real engines from the composition root (``default_engines(locations=...)``): the photo
   legs, the methods (``"c3"`` first), the IF-2 selection, the video source and sink, and the ONE
   proxy cache, not yet open.
2. :class:`AppWindow` (the shell's ``MainWindow``): the log, the ONE settings read, the starter
   presets.
3. The leftover clean-up (D85, V11), synchronous on the interface thread before any panel
   exists, so it ends before any export or batch job can start (DR-35 (c)).
4. The panels: the parameter panels, the timeline (the analysis adapter's factory), the export
   panels (the guarded exports, sharing the one cache) and the settings dialog (WP3.10's rule,
   the start-up's encoder catalog, and the window's one closed signal, which its cache jobs'
   errors read, R2-3); then ``show()``.
5. The window's :class:`FullCollections` check, before any worker starts: from here on
   CPython's full garbage collection runs on the interface thread at an idle moment only, never
   while a job runs (V7).
6. Three start-up jobs on the window's job runner, off the interface thread: (i) the cache's
   open with the settings' limit; (ii) the encoder detection into the catalog (D74, 8.2);
   (iii) the graphics-card detection, whose AD-9 reason the status bar shows while no file is
   open (and the log records); it runs again when the settings change with no file open.
"""

from __future__ import annotations

import dataclasses
import gc
import logging
import sys
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from PySide6.QtCore import QObject, QTimer
from PySide6.QtGui import QCloseEvent
from PySide6.QtWidgets import QApplication

from clearwater.analysis import AnalysisEngine
from clearwater.config import Locations, app_locations
from clearwater.gui import MainWindow, Message, MessagePresenter
from clearwater.gui.contract import Engines, JobHandle, JobRunner
from clearwater.gui.engines import default_engines
from clearwater.gui.export_panel import install_export_panels
from clearwater.gui.parameter_panels import install_parameter_panels
from clearwater.gui.preset_panel import PresetDialogs
from clearwater.gui.settings_dialog import (
    EncoderCatalog,
    SettingsChoosers,
    install_settings_dialog,
)
from clearwater.gui.shell import FileChooser
from clearwater.gui.timeline import install_timeline
from clearwater.interfaces import JobResult, Progress
from clearwater.io.video.capability import resolve_encoder
from clearwater.jobs import LeftoverReport

from . import composition
from .activity import ClipLocks, GuardedExports
from .analysis_adapter import EngineClipAnalysis, EngineFactory, make_analysis_factory
from .composition import CACHE_NOT_OPENED, DeferredProxyCache
from .startup import WriteJournal, cache_open_job, clean_leftovers, device_probe_job

_LOG = logging.getLogger(__name__)

OWNER_STARTUP = "startup"
"""The owner of the start-up's own messages (DR-44 (b))."""

CACHE_FAILED_TEXT = "Videos cannot be analysed or exported in this session: {reason}."
"""The one warning shown when the cache's open failed (ruling S1 (a), condition 2)."""


IDLE_CHECK_MS = 1000
"""How often the interface thread looks for an idle moment to run a deferred full collection."""

_NO_AUTOMATIC_FULL_COLLECTION = 2**31 - 1
"""The third collector threshold while an application runs: never reached."""

_STARTED: list[FullCollections] = []
"""The started instances; the first saves the process's thresholds, the last restores them."""

_SAVED_THRESHOLDS: list[tuple[int, int, int]] = []
"""The process's collector thresholds from before the first start."""


class FullCollections:
    """Keeps CPython's full garbage collection off the job boundaries (V7, ruling 7b32521f item 3).

    Window 3 saw a generation-2 collection on a job's thread at each job boundary (inside the
    plan cache's release), holding the GIL while the interface waited. While started, CPython's
    automatic full collection is off (its third threshold is never reached; generations 0 and 1
    stay automatic) and the interface thread runs it instead, only at an idle moment, from a
    check every :data:`IDLE_CHECK_MS` (CHARC ruling cc0703a7 Q1 (a)). Idle means that no
    started instance's window has a job running (the policy is process-wide):

    - a check that finds a job running does nothing: no full collection runs on any thread
      while a job runs, however many younger collections are pending (that is the bound this
      policy gives; a collection's own duration has none, as CPython offers none);
    - the first check that finds no job running ends start-up: it freezes every object then
      tracked (``gc.freeze``), so no later full collection scans them;
    - a later check that finds no job running collects once more younger collections are pending
      than CPython's own third threshold.

    The cost: cyclic garbage that reaches generation 2 during a job is freed at the next idle
    moment, not before. The process's thresholds come back, and the frozen objects are unfrozen,
    when the last started instance stops (the window's close). Interface thread only.
    """

    def __init__(
        self, jobs: JobRunner, parent: QObject, *, closed: Callable[[], bool] = lambda: False
    ) -> None:
        """Create the check, not yet started.

        Args:
            jobs: The window's job runner (``active()`` tells whether a job is running).
            parent: The timer's owner (the window).
            closed: True once the window saw its close; :meth:`start` then does nothing.
        """
        self._jobs = jobs
        self._closed = closed
        self._timer = QTimer(parent)
        self._timer.setInterval(IDLE_CHECK_MS)
        self._timer.timeout.connect(self._check)
        self._frozen = False

    def start(self) -> None:
        """Turn the automatic full collection off and start the check (idempotent).

        Nothing happens once the window saw its close (its :meth:`stop` has run, or never will).
        """
        if self in _STARTED or self._closed():
            return
        if not _STARTED:
            _SAVED_THRESHOLDS[:] = [gc.get_threshold()]
            first, second, _ = _SAVED_THRESHOLDS[0]
            gc.set_threshold(first, second, _NO_AUTOMATIC_FULL_COLLECTION)
        _STARTED.append(self)
        self._frozen = False  # a new lifetime: its first idle moment freezes again (R5-4)
        self._timer.start()

    def stop(self) -> None:
        """Stop the check; the last one restores the thresholds and unfreezes (idempotent)."""
        if self not in _STARTED:
            return
        self._timer.stop()
        _STARTED.remove(self)
        if not _STARTED:
            gc.set_threshold(*_SAVED_THRESHOLDS.pop())
            gc.unfreeze()

    def _check(self) -> None:
        """At an idle moment only: freeze once after start-up, then collect when due."""
        if any(started._jobs.active() for started in _STARTED):
            return  # nothing collects while any window's job runs (R5-1, R5-2)
        if not self._frozen:
            self._frozen = True
            gc.freeze()
        elif gc.get_count()[2] > _SAVED_THRESHOLDS[0][2]:  # younger collections since a full one
            gc.collect()


class AppWindow(MainWindow):
    """The program's main window: notes its close event before the shell's shutdown runs.

    An override of ``closeEvent``, not an event filter: a Python event filter on the window is
    entered for every event the window gets (the paint, update and layout requests a job's
    progress causes), and each entry waits for the GIL behind the job's threads (V7, CHARC
    ruling 7b32521f item 1). Only the close event runs Python here.

    Attributes:
        close_seen: True once the window got its close event.
        full_collections: The window's garbage-collection check (item 3), started by
            :func:`build_application` and stopped after the shell's shutdown at close.
    """

    def __init__(
        self,
        engines: Engines,
        locations: Locations,
        *,
        presenter: MessagePresenter | None = None,
        choose_file: FileChooser | None = None,
    ) -> None:
        """Build the shell's window (``MainWindow``'s arguments)."""
        super().__init__(engines, locations, presenter=presenter, choose_file=choose_file)
        self.close_seen = False
        self.full_collections = FullCollections(self.jobs, self, closed=lambda: self.close_seen)

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 -- Qt override
        """Note the close, then the shell's shutdown and close, then stop the collection check."""
        self.close_seen = True
        try:
            super().closeEvent(event)
        finally:
            self.full_collections.stop()


class _UnlessClosed:
    """The window's job runner whose completions are dropped once the window is closing.

    The start-up jobs cannot all be cancelled (the cache's first open took 16 s; the encoder
    detection's probes have their own timeouts), so one may end after the shell's close: the
    runner then delivers its ``on_done`` during the close (a thread that ended) or later, while
    an event loop still runs. Either way nothing of it reaches the closed window (DR-44 (c),
    R1-5, ruling d530b564).
    """

    def __init__(self, inner: JobRunner, closed: Callable[[], bool]) -> None:
        self._inner = inner
        self._closed = closed

    def run(
        self,
        job: Callable[[Progress], JobResult],
        *,
        on_done: Callable[[JobResult], None],
        on_progress: Callable[[int, int | None, str], None] | None = None,
    ) -> JobHandle:
        """Start ``job`` on the window's runner; its callbacks run only while it is open."""

        def done(result: JobResult) -> None:
            if not self._closed():
                on_done(result)

        def progress(done_: int, total: int | None, message: str) -> None:
            if on_progress is not None and not self._closed():
                on_progress(done_, total, message)

        return self._inner.run(
            job, on_done=done, on_progress=None if on_progress is None else progress
        )

    def cancel(self) -> None:
        """Cancel every running job."""
        self._inner.cancel()

    def active(self) -> int:
        """Return how many jobs have not yet delivered ``on_done``."""
        return self._inner.active()

    def wait(self, timeout_s: float) -> bool:
        """Wait for every job thread to end, at most ``timeout_s`` seconds in total."""
        return self._inner.wait(timeout_s)


@dataclass
class Application:
    """The running program: the window and what start-up built around it.

    Attributes:
        window: The main window.
        cache: The one proxy cache (opened by start-up job (i)).
        exports: The export engine behind the per-job guards (the panels' ``ExportJobs``).
        catalog: The session's encoder capabilities (start-up job (ii)).
        journal: The write journal (D85).
        locks: The per-clip locks (DR-62).
        leftovers: What the start-up clean-up removed and could not remove.
        analysis: The analysis adapter the timeline built last, or None; the earlier ones are
            not kept (R1-8).
    """

    window: AppWindow
    cache: DeferredProxyCache
    exports: GuardedExports
    catalog: EncoderCatalog
    journal: WriteJournal
    locks: ClipLocks
    leftovers: LeftoverReport
    analysis: EngineClipAnalysis | None = None
    _probe_generation: int = 0

    def closed(self) -> bool:
        """Return True once the window got its close event (the start-up callbacks stop)."""
        return self.window.close_seen

    def start_jobs(self) -> None:
        """Start the three start-up jobs (interface thread), their callbacks guarded by close.

        Every start-up callback, the encoder catalog's completion included, runs only while the
        window is open (R1-5): the jobs run on the window's runner through :class:`_UnlessClosed`.
        """
        window = self.window
        jobs = _UnlessClosed(window.jobs, self.closed)
        limit = window.session.settings().cache_limit_bytes
        try:
            jobs.run(cache_open_job(self.cache, limit), on_done=self._on_cache_open)
        except RuntimeError as error:  # the runner is closed: the window is closing
            self.cache.fail(str(error))
        self.catalog.start(dataclasses.replace(window.context, jobs=jobs))
        self.probe_device()
        window.session.settings_changed.connect(self._on_settings)

    def keep_analysis(self, analysis: EngineClipAnalysis) -> None:
        """Keep the timeline's latest analysis adapter, dropping the one before (R1-8)."""
        self.analysis = analysis

    def probe_device(self) -> None:
        """Run the graphics-card detection off the interface thread (AD-9, question 5)."""
        window = self.window
        self._probe_generation += 1
        generation = self._probe_generation
        method_id = next(iter(window.context.engines.methods))
        job = device_probe_job(
            window.context.engines.select_backend, window.session.settings(), method_id
        )
        jobs = _UnlessClosed(window.jobs, self.closed)
        try:
            jobs.run(job, on_done=lambda result: self._on_probe(generation, result))
        except RuntimeError as error:  # the runner is closed: the window is closing
            _LOG.info("device detection not started: %s", error)

    def _on_probe(self, generation: int, result: JobResult) -> None:
        """Main thread: show the latest detection's reason while no file is open."""
        if generation != self._probe_generation:
            return
        if result.ok:
            self.window.set_idle_device(result.device)
        else:
            _LOG.warning("device detection failed: %s", result.failure)

    def _on_settings(self, _settings: object) -> None:
        """Main thread: a settings change with no file open detects again (``force_cpu``)."""
        if self.window.session.source() is None and not self.closed():
            self.probe_device()

    def _on_cache_open(self, result: JobResult) -> None:
        """Main thread: show the cache's open failure once; the photo path keeps working."""
        if result.ok:
            return
        reason = CACHE_NOT_OPENED.format(reason=self.cache.failure() or result.failure)
        text = CACHE_FAILED_TEXT.format(reason=reason)
        self.window.presenter.present(Message("warning", text, None, OWNER_STARTUP))


def build_application(
    locations: Locations,
    *,
    presenter: MessagePresenter | None = None,
    choose_file: FileChooser | None = None,
    preset_dialogs: PresetDialogs | None = None,
    choosers: SettingsChoosers | None = None,
    engine_factory: EngineFactory = AnalysisEngine,
) -> Application:
    """Build, show and start the application over ``locations`` (the module docstring's order).

    Args:
        locations: The app-data folders (``app_locations()`` in the program; tests pass folders
            under ``tmp_path``).
        presenter: The G10 presenter; the dialog-and-banner one when None (tests inject one).
        choose_file: The file chooser; a ``QFileDialog`` when None (tests inject one).
        preset_dialogs: The Presets panel's dialogs; the Qt ones when None.
        choosers: The settings dialog's folder chooser and confirmation; the Qt ones when None.
        engine_factory: Builds each analysis engine (``AnalysisEngine``; a test hook holds one).

    Returns:
        The application, its window shown and its start-up jobs started.
    """
    engines = default_engines(locations=locations)
    cache = engines.cache
    assert isinstance(cache, DeferredProxyCache)  # default_engines with locations builds it
    window = AppWindow(engines, locations, presenter=presenter, choose_file=choose_file)
    journal = WriteJournal(locations.config_dir)
    leftovers = clean_leftovers(window.session.settings(), journal)
    locks = ClipLocks()
    controller = window.controller

    def release_device_plans(progress: Progress) -> bool:
        """Wait for the preview's release, cancellably; True lets the job select (R1-11)."""
        if controller.release_device_plans(None, cancelled=progress.cancelled):
            return True
        return not progress.cancelled()  # the preview worker had stopped: released at its stop

    exports = GuardedExports(
        composition.export_jobs(cache=cache),
        cache=cache,
        locks=locks,
        journal=journal,
        release_device_plans=release_device_plans,
    )
    catalog = EncoderCatalog(window)
    application = Application(
        window=window,
        cache=cache,
        exports=exports,
        catalog=catalog,
        journal=journal,
        locks=locks,
        leftovers=leftovers,
    )
    factory = make_analysis_factory(
        window.session.settings,
        locks=locks,
        engine_factory=engine_factory,
        on_built=application.keep_analysis,
    )
    install_parameter_panels(window, dialogs=preset_dialogs)
    install_timeline(window, factory)
    install_export_panels(window, exports)
    install_settings_dialog(
        window,
        choosers=choosers,
        resolve_encoder=resolve_encoder,
        catalog=catalog,
        window_closing=application.closed,  # the start-up callbacks' one closed signal (R2-3)
    )
    window.show()
    window.full_collections.start()  # before any worker; the freeze waits for start-up's end
    application.start_jobs()
    return application


def main(argv: Sequence[str] | None = None) -> int:
    """Run Clearwater until its window closes (``python -m clearwater``).

    Args:
        argv: The command line for Qt; ``sys.argv`` when None.

    Returns:
        The Qt event loop's exit code.
    """
    existing = QApplication.instance()
    app = (
        existing if existing is not None else QApplication(list(sys.argv if argv is None else argv))
    )
    _running = build_application(app_locations())  # held: the window lives while this does
    return int(app.exec())
