"""The entry point: ``python -m clearwater`` and :func:`main` (WP4.3).

The only ``clearwater.app`` module that imports ``clearwater.gui`` or loads Qt.
:func:`build_application` makes the program the owner starts, in the round-0 order as ruled
(questions 4 and 11, S1 (a), S-order):

1. The real engines from the composition root (``default_engines(locations=...)``): the photo
   legs, the methods (``"c3"`` first), the IF-2 selection, the video source and sink, and the ONE
   proxy cache, not yet open.
2. ``MainWindow``: the log, the ONE settings read, the starter presets.
3. The leftover clean-up (D85, V11), synchronous on the interface thread before any panel
   exists, so it ends before any export or batch job can start (DR-35 (c)).
4. The panels: the parameter panels, the timeline (the analysis adapter's factory), the export
   panels (the guarded exports, sharing the one cache) and the settings dialog (WP3.10's rule,
   the start-up's encoder catalog); then ``show()``.
5. Three start-up jobs on the window's job runner, off the interface thread: (i) the cache's
   open with the settings' limit; (ii) the encoder detection into the catalog (D74, 8.2);
   (iii) the graphics-card detection, whose AD-9 reason the status bar shows while no file is
   open (and the log records); it runs again when the settings change with no file open.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import Sequence
from dataclasses import dataclass

from PySide6.QtWidgets import QApplication

from clearwater.analysis import AnalysisEngine
from clearwater.config import Locations, app_locations
from clearwater.gui import MainWindow, Message, MessagePresenter
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
from clearwater.interfaces import JobResult
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

PLAN_RELEASE_TIMEOUT_S = 10.0
"""The longest wait of a job for the preview's FFT plan release (DR-68)."""


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

    window: MainWindow
    cache: DeferredProxyCache
    exports: GuardedExports
    catalog: EncoderCatalog
    journal: WriteJournal
    locks: ClipLocks
    leftovers: LeftoverReport
    analysis: EngineClipAnalysis | None = None
    _probe_generation: int = 0

    def start_jobs(self) -> None:
        """Start the three start-up jobs (interface thread)."""
        window = self.window
        limit = window.session.settings().cache_limit_bytes
        try:
            window.jobs.run(cache_open_job(self.cache, limit), on_done=self._on_cache_open)
        except RuntimeError as error:  # the runner is closed: the window is closing
            self.cache.fail(str(error))
        self.catalog.start(window.context)
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
        try:
            window.jobs.run(job, on_done=lambda result: self._on_probe(generation, result))
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
        if self.window.session.source() is None:
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
    window = MainWindow(engines, locations, presenter=presenter, choose_file=choose_file)
    journal = WriteJournal(locations.config_dir)
    leftovers = clean_leftovers(window.session.settings(), journal)
    locks = ClipLocks()
    controller = window.controller

    def release_device_plans() -> None:
        if not controller.release_device_plans(PLAN_RELEASE_TIMEOUT_S):
            _LOG.warning("the preview's FFT plans were not released in time")

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
        window, choosers=choosers, resolve_encoder=resolve_encoder, catalog=catalog
    )
    window.show()
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
