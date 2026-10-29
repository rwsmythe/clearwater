"""The main window: start-up, menus, file open, the attachment areas, status bar and close.

Start-up and close go through the ``clearwater.config`` API only (AD-25 (a)): the log, the
settings and the presets live in the injected :class:`~clearwater.config.Locations`; nothing is
written anywhere else and no ``QSettings`` is used. The program's entry point is
``python -m clearwater`` (:func:`clearwater.app.main.main`, WP4.3), which builds this window over
the real engines with every panel attached; :func:`run` shows the window alone, with no panel.
"""

from __future__ import annotations

import dataclasses
import logging
import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QCloseEvent, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QDockWidget,
    QFileDialog,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)

from clearwater.config import (
    Locations,
    PresetError,
    PresetStore,
    app_locations,
    configure_logging,
    load_settings,
    new_parameter_set,
    save_settings,
    shutdown_logging,
)
from clearwater.interfaces import (
    FormatError,
    ParameterSet,
    Settings,
    UnsupportedFormatVersionError,
)

from . import messages, sources
from .contract import (
    AnalysisState,
    Area,
    Engines,
    Message,
    MessagePresenter,
    OpenedSource,
    PanelFactory,
    PreviewSurface,
    ReasonAction,
    SettingsDialogFactory,
    ShellActions,
    ShellContext,
    ShellWindow,
)
from .engines import default_engines
from .jobs import QtJobRunner
from .messages import BannerWidget, DialogPresenter
from .preview import PreviewController, PreviewWidget
from .render_worker import LatestWorker, Outcome
from .session import ShellSession

_LOG = logging.getLogger(__name__)

SHUTDOWN_TIMEOUT_S = 5.0
"""The longest wait for each worker at close; worker threads are daemons, so exit never hangs."""

EXPORT_NOT_CONNECTED = "Export is not available yet."
"""The caller's initial reason on ``actions.export``; WP3.19 clears it when it connects."""

NO_SOURCE_REASON = "Open a photo or video to export."
"""The shell's reason on ``actions.export`` while nothing is open."""

NEEDS_ANALYSIS_REASON = "Export needs the clip's analysis."
"""The shell's reason for a video whose analysis has not run or was cancelled (AD-15)."""

SETTINGS_FORMAT_TEXT = (
    "The settings file {path} is in a format this Clearwater does not read ({error}). Defaults "
    "are used for this session and the file is left as it is."
)
"""The start-up message for a settings file whose ``format_version`` is refused (S4, R4-2).

Neutral on purpose: ``UnsupportedFormatVersionError`` is raised for a newer version and for an
older one with no migration step; the error text in the braces says which.
"""

type FileChooser = Callable[[QWidget], Path | None]
"""Asks the user for a file to open; returns None when cancelled."""


@dataclass(frozen=True)
class StartUp:
    """What start-up produced (brief task 3).

    Attributes:
        settings: The loaded settings, or ``Settings()``.
        parameters: The parameter set to begin with.
        presets: The preset store over ``locations.presets_dir``.
        problems: Messages to show once the window exists.
        settings_refusal: The refusal of the settings file, or None when it may be written this
            session (S4; ``Session.settings_refusal``).
    """

    settings: Settings
    parameters: ParameterSet
    presets: PresetStore
    problems: tuple[Message, ...]
    settings_refusal: Message | None

    @property
    def save_at_close(self) -> bool:
        """False when the settings file must be left untouched (S4)."""
        return self.settings_refusal is None


def start_up(locations: Locations, engines: Engines) -> StartUp:
    """Start the application's persistent state through the ``clearwater.config`` API.

    ``configure_logging(log_dir)``, ``load_settings(config_dir)``,
    ``PresetStore(presets_dir).install_starters()``, then the parameters from
    ``settings.last_parameters`` when its method is one of ``engines.methods``, else the default
    method's empty set (with a logged warning when a stored set names an unknown method).

    Args:
        locations: The app-data folders (tests pass folders under ``tmp_path``).
        engines: The engines (``methods``; the first is the default).

    Returns:
        The start-up state.
    """
    problems: list[Message] = []
    try:
        configure_logging(locations.log_dir)
    except OSError as error:
        text = messages.ascii_text(f"No log file: {error}")
        problems.append(Message("warning", text, owner=messages.OWNER_START))
    settings_refusal: Message | None = None
    try:
        settings = load_settings(locations.config_dir)
    except UnsupportedFormatVersionError as error:
        _LOG.warning("settings refused: %s", error)
        settings = Settings()
        path = locations.settings_file
        text = SETTINGS_FORMAT_TEXT.format(path=path, error=error)
        settings_refusal = dataclasses.replace(
            messages.refusal(path, text), owner=messages.OWNER_START
        )
        problems.append(settings_refusal)
    presets = PresetStore(locations.presets_dir)
    try:
        installed = presets.install_starters()
    except (OSError, PresetError) as error:
        _LOG.warning("starter presets not installed: %s", error)
    else:
        if installed:
            _LOG.info("installed starter presets: %s", ", ".join(installed))
    default_id = next(iter(engines.methods))
    last = settings.last_parameters
    if last is not None and last.method in engines.methods:
        parameters = last
    else:
        if last is not None:
            _LOG.warning(
                "last-used parameters name method %r, which is not available; using %r",
                last.method,
                default_id,
            )
        parameters = new_parameter_set(default_id, {})
    return StartUp(settings, parameters, presets, tuple(problems), settings_refusal)


class ExportAction(ReasonAction):
    """``actions.export``: enabled only while neither the shell nor the caller has a reason."""

    def __init__(self, text: str, parent: QWidget) -> None:
        """Create the action with the caller's initial reason.

        Args:
            text: The menu text.
            parent: The Qt parent.
        """
        super().__init__(text, parent)
        self._caller: str | None = EXPORT_NOT_CONNECTED
        self._shell: str | None = NO_SOURCE_REASON
        self._refresh()

    def set_unavailable(self, reason: str | None) -> None:
        """Set or clear the caller's reason (WP3.19).

        Args:
            reason: Why export is unavailable, or None.
        """
        self._caller = reason
        self._refresh()

    def unavailable_reason(self) -> str | None:
        """Return the reason shown now (the shell's first), or None when enabled."""
        return self._shell or self._caller

    def set_shell_reason(self, reason: str | None) -> None:
        """Set the shell's own reason (no source; AD-15 analysis state).

        Args:
            reason: The reason, or None.
        """
        self._shell = reason
        self._refresh()

    def _refresh(self) -> None:
        """Apply the effective reason to the enabled state and the tips."""
        reason = self.unavailable_reason()
        self.setEnabled(reason is None)
        tip = reason or "Export the corrected file"
        self.setToolTip(tip)
        self.setStatusTip(tip)


def export_reason(source: OpenedSource | None, state: AnalysisState) -> str | None:
    """Return the shell's reason export is unavailable (AD-15), or None.

    Args:
        source: The open source.
        state: Its analysis state.

    Returns:
        None for a photo or an analysed video; else the reason, with the progress while the
        analysis runs.
    """
    if source is None:
        return NO_SOURCE_REASON
    if source.kind == "photo" or state.phase == "complete":
        return None
    if state.phase == "running":
        total = "?" if state.total is None else str(state.total)
        return f"Export is available when the analysis completes: {state.done}/{total}."
    if state.phase == "failed":
        return messages.ascii_text(f"The analysis failed: {state.message}")
    return NEEDS_ANALYSIS_REASON


def _open_task(
    path: Path, kind: sources.SourceKind, engines: Engines
) -> tuple[Path, sources.OpenOutcome]:
    """Open a routed path on the loader worker; an exception escaping it refuses the file.

    Args:
        path: The file.
        kind: What :func:`sources.route` returned.
        engines: The engines.

    Returns:
        ``(path, outcome)``; the outcome is a refusal naming the file when opening raised.
    """
    try:
        return path, sources.open_source(path, kind, engines)
    except Exception as error:  # the per-kind catches missed it: still a refusal (round-4 R4-1)
        detail = str(error) or type(error).__name__
        text = f"{messages.file_name(path)} could not be opened: {detail}"
        return path, sources.OpenOutcome(None, (messages.refusal(path, text),))


def _choose_file(parent: QWidget) -> Path | None:
    """The product file chooser (G1): a file dialog filtered to photos and videos."""
    name, _ = QFileDialog.getOpenFileName(parent, "Open", "", sources.file_filter())
    return Path(name) if name else None


class MainWindow(ShellWindow):
    """The Clearwater main window (implements ``clearwater.gui.contract.ShellWindow``).

    Args:
        engines: The engines (stubs until WP4.3).
        locations: The app-data folders; never resolved here.
        presenter: The G10 presenter; the dialog-and-banner one when None (tests inject one).
        choose_file: The file chooser; a ``QFileDialog`` when None (tests inject one).
    """

    def __init__(
        self,
        engines: Engines,
        locations: Locations,
        *,
        presenter: MessagePresenter | None = None,
        choose_file: FileChooser | None = None,
    ) -> None:
        """Start up and build the window."""
        super().__init__()
        self.setWindowTitle("Clearwater")
        self.resize(1280, 800)
        startup = start_up(locations, engines)
        self._engines = engines
        self._locations = locations
        self._save_at_close = startup.save_at_close
        self._choose = choose_file or _choose_file
        self._closed = False
        self._idle_device = "-"
        self.session = ShellSession(
            engines,
            startup.settings,
            startup.parameters,
            self,
            settings_refusal=startup.settings_refusal,
        )

        central = QWidget(self)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.banner = BannerWidget(central)
        self.preview_widget = PreviewWidget(central)
        self._timeline = QWidget(central)
        self._timeline_layout = QVBoxLayout(self._timeline)
        self._timeline_layout.setContentsMargins(0, 0, 0, 0)
        self._timeline.setVisible(False)
        layout.addWidget(self.banner)
        layout.addWidget(self.preview_widget, 1)
        layout.addWidget(self._timeline)
        self.setCentralWidget(central)

        self.presenter: MessagePresenter = presenter or DialogPresenter(self, self.banner)
        self.jobs = QtJobRunner()
        self.shell_actions = self._build_actions()
        self._docks: dict[Area, list[QDockWidget]] = {Area.PARAMETERS: [], Area.JOBS: []}
        self._settings_factory: SettingsDialogFactory | None = None
        self._settings_dialog: QDialog | None = None
        self.context = ShellContext(
            window=self,
            session=self.session,
            engines=engines,
            locations=locations,
            presets=startup.presets,
            jobs=self.jobs,
            messages=self.presenter,
            actions=self.shell_actions,
        )
        self.controller = PreviewController(
            self.session, engines, self.preview_widget, self.presenter
        )
        self._opener = LatestWorker("clearwater-open", self._on_opened)
        self._build_status_bar()

        self.session.source_changed.connect(self._on_source_changed)
        self.session.analysis_changed.connect(self._update_export)
        self.session.backend_changed.connect(self._update_status)
        self.preview_widget.view_changed.connect(self._update_status)
        self._update_export()
        self._update_status()
        for problem in startup.problems:
            self.presenter.present(problem)

    # ShellWindow.

    @property
    def preview(self) -> PreviewSurface:
        """The split-view preview."""
        return self.controller

    def attach(self, area: Area, factory: PanelFactory, *, title: str) -> QWidget:
        """Create a panel with ``factory(context)`` and place it in ``area``.

        Args:
            area: Where the panel goes.
            factory: Builds the panel.
            title: The dock title (PARAMETERS, JOBS) or the panel's object name (TIMELINE).

        Returns:
            The panel.
        """
        panel = factory(self.context)
        if area is Area.TIMELINE:
            panel.setObjectName(title)
            self._timeline_layout.addWidget(panel)
            return panel
        dock = QDockWidget(title, self)
        dock.setObjectName(f"{area.value}:{title}")
        dock.setWidget(panel)
        where = (
            Qt.DockWidgetArea.RightDockWidgetArea
            if area is Area.PARAMETERS
            else Qt.DockWidgetArea.BottomDockWidgetArea
        )
        self.addDockWidget(where, dock)
        existing = self._docks[area]
        if existing:
            self.tabifyDockWidget(existing[-1], dock)
        existing.append(dock)
        return panel

    def set_settings_dialog(self, factory: SettingsDialogFactory) -> None:
        """Register the settings dialog; ``actions.settings`` opens it window-modally.

        Args:
            factory: Builds a new dialog each time.
        """
        self._settings_factory = factory
        self.shell_actions.settings.setEnabled(True)
        self.shell_actions.settings.setToolTip("Settings")

    # File open (G1, G10).

    def open_file(self) -> None:
        """Ask for a file and open it (File > Open)."""
        path = self._choose(self)
        if path is not None:
            self.open_path(path)

    def open_path(self, path: Path) -> None:
        """Open a file off the interface thread; a refusal keeps the previous source.

        Args:
            path: The file.
        """
        kind = sources.route(path)
        if isinstance(kind, Message):
            self._opener.invalidate()  # an earlier open still in flight is never shown
            self.presenter.present(kind)
            return
        engines = self._engines
        self.statusBar().showMessage(f"Opening {messages.file_name(path)}...", 3000)
        self._opener.submit(lambda check: _open_task(path, kind, engines))

    def opening(self) -> bool:
        """Return True while a file is being opened."""
        return not self._opener.idle()

    def _on_opened(self, outcome: Outcome) -> None:
        """Main thread: show the opened source and its warnings, or the refusal."""
        if outcome.error is not None:  # not reached: _open_task turns an exception into a refusal
            text = messages.ascii_text(f"The file could not be opened: {outcome.error}")
            self.presenter.present(Message("refusal", text, owner=messages.OWNER_OPEN))
            return
        value = outcome.value
        assert isinstance(value, tuple)
        _, result = value
        assert isinstance(result, sources.OpenOutcome)
        if result.source is None:
            for message in result.messages:
                self.presenter.present(message)
            return
        for owner in messages.SHELL_OWNERS:  # the shell's own; a panel's messages are its own
            self.presenter.clear(owner=owner)
        self.session._open(result.source)
        for message in result.messages:
            self.presenter.present(message)

    # Actions, export, status.

    def _build_actions(self) -> ShellActions:
        """Build the menus (File, View, Tools) and return the contract's actions."""
        open_action = QAction("&Open...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_file)
        export = ExportAction("&Export...", self)
        self._export = export
        quit_action = QAction("&Quit", self)
        quit_action.setShortcut(QKeySequence.StandardKey.Quit)
        quit_action.triggered.connect(self.close)
        settings = QAction("&Settings...", self)
        settings.setEnabled(False)
        settings.setToolTip("Settings are not available yet.")
        settings.triggered.connect(self._open_settings)
        file_menu = self.menuBar().addMenu("&File")
        file_menu.addAction(open_action)
        file_menu.addAction(export)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)
        view_menu = self.menuBar().addMenu("&View")
        widget = self.preview_widget
        self.view_actions = {
            "fit": self._view_action(view_menu, "&Fit", "Ctrl+0", widget.fit),
            "one_to_one": self._view_action(view_menu, "&1:1", "Ctrl+1", widget.one_to_one),
            "zoom_in": self._view_action(view_menu, "Zoom &in", "Ctrl++", widget.zoom_in),
            "zoom_out": self._view_action(view_menu, "Zoom &out", "Ctrl+-", widget.zoom_out),
            "reset_split": self._view_action(
                view_menu, "&Reset split", "Ctrl+R", widget.reset_split
            ),
        }
        tools_menu = self.menuBar().addMenu("&Tools")
        tools_menu.addAction(settings)
        return ShellActions(open=open_action, export=export, settings=settings, quit=quit_action)

    def _view_action(
        self, menu: QMenu, text: str, shortcut: str, slot: Callable[[], None]
    ) -> QAction:
        """Add one View menu action."""
        action = QAction(text, self)
        action.setShortcut(QKeySequence(shortcut))
        action.triggered.connect(slot)
        menu.addAction(action)
        return action

    def _open_settings(self) -> None:
        """Open the registered settings dialog window-modally (never a blocking ``exec``)."""
        if self._settings_factory is None:
            return
        dialog = self._settings_factory(self.context)
        self._settings_dialog = dialog
        dialog.open()

    def _build_status_bar(self) -> None:
        """Add the status bar fields: device (AD-9), file, size, zoom."""
        bar = self.statusBar()
        self.device_label = QLabel(bar)
        self.file_label = QLabel(bar)
        self.size_label = QLabel(bar)
        self.zoom_label = QLabel(bar)
        for label in (self.file_label, self.size_label, self.zoom_label, self.device_label):
            bar.addPermanentWidget(label)

    def _on_source_changed(self, source: object) -> None:
        """A new source: show the timeline for a video, update export and the status bar."""
        self._timeline.setVisible(isinstance(source, OpenedSource) and source.kind == "video")
        self._update_export()
        self._update_status()

    def _update_export(self, *_: object) -> None:
        """Apply AD-15 to ``actions.export``."""
        reason = export_reason(self.session.source(), self.session.analysis())
        self._export.set_shell_reason(reason)

    def set_idle_device(self, reason: str) -> None:
        """Show the start-up's AD-9 reason while no file is open (WP4.3, ruling S3).

        Until it is called the status bar shows ``Device: -`` before a file is open; once a file
        is open it shows the full-resolution selection's reason, as before.

        Args:
            reason: The reason of the application's graphics-card detection.
        """
        self._idle_device = reason
        self._update_status()

    def _update_status(self, *_: object) -> None:
        """Refresh the status bar (AD-9 device text, question 4)."""
        source = self.session.source()
        full = self.session.backend()
        preview = self.session.preview_backend()
        if source is None:
            self.device_label.setText(f"Device: {self._idle_device}")
            self.device_label.setToolTip("")
            self.file_label.setText("")
            self.size_label.setText("")
        else:
            self.device_label.setText(f"Device: {full}")
            differs = preview not in ("-", full)
            self.device_label.setToolTip(f"Preview: {preview}" if differs else "")
            self.file_label.setText(messages.file_name(source.path))
            height, width = source.image.pixels.shape[0], source.image.pixels.shape[1]
            self.size_label.setText(f"{width} x {height}")
        self.zoom_label.setText(self.preview_widget.zoom_text() if source is not None else "")

    # Close (question 9).

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 -- Qt override
        """Shut down, then close."""
        self.shutdown()
        event.accept()

    def shutdown(self) -> None:
        """Stop every worker, save the settings with the last parameters once, close the log.

        The order: the jobs are cancelled and joined, and the ``on_done`` of every job that
        ended is DELIVERED here, before the settings write, so a change it makes is saved (a job
        still running after the timeout delivers nothing before the write). Then every worker
        is stopped, each even when another overran its timeout. Then the save.

        Idempotent. A save error is logged, never raised; after a settings file was refused at
        start-up (a format version this Clearwater does not read) nothing is saved (S4).
        """
        if self._closed:
            return
        self._closed = True
        if not self.jobs.close(SHUTDOWN_TIMEOUT_S):
            _LOG.warning("a job was still running at close")
        stopped = [
            self.controller.stop(SHUTDOWN_TIMEOUT_S),
            self._opener.stop(SHUTDOWN_TIMEOUT_S),
        ]
        if not all(stopped):
            _LOG.warning("a preview or open worker was still running at close")
        if self._save_at_close:
            settings = dataclasses.replace(
                self.session.settings(), last_parameters=self.session.parameters()
            )
            try:
                save_settings(self._locations.config_dir, settings)
            except (OSError, FormatError, ValueError) as error:
                _LOG.warning("settings were not saved: %s", error)
        _LOG.info("Clearwater closed")
        shutdown_logging()


def run(engines: Engines | None = None, locations: Locations | None = None) -> int:
    """Show the main window alone, with no panel attached, until it closes.

    The program does not call this: ``python -m clearwater`` runs
    :func:`clearwater.app.main.main`, which attaches the panels and the start-up jobs (WP4.3).

    Args:
        engines: The engines; :func:`~clearwater.gui.engines.default_engines` when None.
        locations: The app-data folders; ``clearwater.config.app_locations()`` when None.

    Returns:
        The Qt event loop's exit code.
    """
    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow(engines or default_engines(), locations or app_locations())
    window.show()
    return int(app.exec())
