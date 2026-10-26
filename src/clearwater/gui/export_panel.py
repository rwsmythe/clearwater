"""The Export panel (WP3.19, G8, G9, D43, D44, AD-15): File > Export of the open source.

The panel sits in ``Area.JOBS``. ``actions.export.triggered`` starts one export job for the open
source through ``context.jobs`` (a worker thread); the status line, a progress bar and a Cancel
button follow it. The action's availability is only ever changed through
``actions.export.set_unavailable`` (through the
:class:`~clearwater.gui.export_service.ActivityGate`), so the shell's own reasons (no source
open, the AD-15 analysis state) always hold as well. :func:`install_export_panels` attaches this
panel and the batch panel.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clearwater.interfaces import JobResult

from . import messages
from .batch_panel import batch_panel_factory
from .contract import Area, JobHandle, Message, PanelFactory, ShellContext, ShellWindow
from .export_service import (
    CANCELLED,
    ActivityGate,
    ExportJobs,
    ExportRequest,
    SharedGate,
    unavailable_exports,
)

OWNER = "export"
"""The ``Message.owner`` of this panel's messages (DR-44 (b))."""

READY_TEXT = "Ready."
"""The status line while nothing has run."""


class ExportPanel(QWidget):
    """Export of the open source with progress and cancel (main thread only).

    Attributes:
        status: The line naming the running export, or the last result.
        bar: The progress bar; busy (range 0 to 0) while the job reports no total.
        cancel_button: Asks the running job to stop.
    """

    def __init__(self, context: ShellContext, exports: ExportJobs, gate: ActivityGate) -> None:
        """Create the panel and connect ``actions.export``.

        Args:
            context: The shell context.
            exports: The export engine.
            gate: The window's one-activity gate (created with ``actions.export.set_unavailable``,
                which clears the "not available yet" reason).
        """
        super().__init__()
        self._context = context
        self._exports = exports
        self._gate = gate
        self._running = False
        self._cancel_requested = False
        self._handle: JobHandle | None = None
        self.status = QLabel(READY_TEXT)
        self.status.setObjectName("export-status")
        self.bar = QProgressBar()
        self.bar.setObjectName("export-bar")
        self.bar.setRange(0, 1)
        self.bar.setValue(0)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setObjectName("export-cancel")
        self.cancel_button.setEnabled(False)
        self.cancel_button.clicked.connect(self.cancel)
        row = QHBoxLayout()
        row.addWidget(self.bar, 1)
        row.addWidget(self.cancel_button)
        layout = QVBoxLayout(self)
        layout.addWidget(self.status)
        layout.addLayout(row)
        layout.addStretch(1)
        context.actions.export.triggered.connect(self._on_triggered)

    def is_running(self) -> bool:
        """Return True from the start of an export until its result has been shown."""
        return self._running

    def cancel(self) -> None:
        """Ask the running export to stop (the Cancel button)."""
        handle = self._handle
        if not self._running or self._cancel_requested or handle is None:
            return
        self._cancel_requested = True
        self.cancel_button.setEnabled(False)
        self.status.setText("Cancelling...")
        handle.cancel()

    def _on_triggered(self, *_: object) -> None:
        """Start an export of the open source (the action is enabled only when it may run)."""
        source = self._context.session.source()
        if source is None or self._running or not self._gate.try_start("export"):
            return
        self._running = True
        self._cancel_requested = False
        self._handle = None
        path = source.path
        try:  # everything after the gate is taken is guarded, so a fault releases it again
            request = ExportRequest(
                source=path,
                kind=source.kind,
                parameters=self._context.session.parameters(),
                settings=self._context.session.settings(),
            )
            self._context.messages.clear("warning", owner=OWNER)
            self.bar.setRange(0, 0)
            self.cancel_button.setEnabled(True)
            self.status.setText(f"Exporting {messages.file_name(path)}...")
            job = self._exports.job(request)
            handle = self._context.jobs.run(
                job, on_done=lambda result: self._done(path, result), on_progress=self._progress
            )
            if self._running:  # a runner that completes synchronously has finished already
                self._handle = handle
        except Exception as error:  # an export that cannot even start is a failed export
            if not self._running:  # the result was already handled; the fault is later
                raise
            detail = str(error) or type(error).__name__
            self._done(path, JobResult(False, (), (), detail, "none", 0.0))

    def _progress(self, done: int, total: int | None, message: str) -> None:
        """Show a progress report (main thread)."""
        if not self._running:
            return
        if total is None or total <= 0:
            self.bar.setRange(0, 0)
        else:
            self.bar.setRange(0, total)
            self.bar.setValue(max(0, min(done, total)))
        if message and not self._cancel_requested:
            self.status.setText(messages.ascii_text(message))

    def _done(self, path: Path, result: JobResult) -> None:
        """Show the result and make export available again (main thread).

        The panel's own state and the gate are released before anything is presented, so a
        failing presenter cannot leave the export reason set.
        """
        self._running = False
        self._handle = None
        self._cancel_requested = False
        self.cancel_button.setEnabled(False)
        self.bar.setRange(0, 1)
        self.bar.setValue(1 if result.ok else 0)
        self._gate.finish("export")
        name = messages.file_name(path)
        if result.ok:
            saved = ", ".join(messages.file_name(p) for p in result.outputs) or name
            self.status.setText(f"Saved {saved}")
            self._context.messages.clear("error", owner=OWNER)
            for text in result.warnings:
                self._context.messages.present(
                    Message("warning", messages.ascii_text(text), path, OWNER)
                )
        elif result.failure == CANCELLED:
            self.status.setText("Export cancelled.")
        else:
            reason = messages.ascii_text(result.failure or "the export failed")
            self.status.setText(f"Export of {name} failed.")
            self._context.messages.present(Message("error", f"{name}: {reason}", path, OWNER))


def export_panel_factory(exports: ExportJobs, gates: SharedGate) -> PanelFactory:
    """Return the factory of the Export panel.

    Args:
        exports: The export engine.
        gates: The window's shared gate holder.

    Returns:
        A ``PanelFactory`` for ``ShellWindow.attach``.
    """

    def build(context: ShellContext) -> QWidget:
        gate = gates.get(context.actions.export.set_unavailable)
        return ExportPanel(context, exports, gate)

    return build


def install_export_panels(window: ShellWindow, exports: ExportJobs | None = None) -> None:
    """Attach the Export and Batch panels to ``Area.JOBS`` and connect File > Export.

    Args:
        window: The main window.
        exports: The export engine (WP3.14's, wired by WP4.3), or None for the build without
            one: every export then fails with "Export is not available in this build."
    """
    engine = exports if exports is not None else unavailable_exports()
    gates = SharedGate()
    window.attach(Area.JOBS, export_panel_factory(engine, gates), title="Export")
    window.attach(Area.JOBS, batch_panel_factory(engine, gates), title="Batch")
