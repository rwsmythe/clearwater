"""The Batch panel (WP3.19, G7, G8, G9, D43-D45, D81, D83): a queue run one item after another.

The panel sequences the batch itself (CHARC ruling Q1): one IF-8 job per file from
:class:`~clearwater.gui.export_service.ExportJobs`, run through ``context.jobs`` on a worker
thread, one at a time. A failed item is marked, logged on ``clearwater.gui.batch`` and skipped
(D81); a cancel stops the whole remaining batch (D45); outputs already completed are never
touched (G8). When the run ends a report lists every item (G7). Main thread only.
"""

from __future__ import annotations

import enum
import logging
import os
from collections import Counter
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clearwater.interfaces import JobResult, ParameterSet, Settings, validate_parameter_set

from . import messages, sources
from .contract import JobHandle, Message, PanelFactory, ShellContext
from .export_service import (
    CANCELLED,
    NO_OUTPUT_TEXT,
    ActivityGate,
    ExportJobs,
    ExportRequest,
    SharedGate,
)

OWNER = "batch"
"""The ``Message.owner`` of this panel's messages (DR-44 (b))."""

CURRENT_PARAMETERS = "Current parameters"
"""The first entry of the parameter combo: the session's parameters at Start."""

_LOG = logging.getLogger("clearwater.gui.batch")


class ItemState(enum.Enum):
    """Where a queued file is in a batch run."""

    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    DONE_WITH_WARNINGS = "done with warnings"
    FAILED = "failed"
    CANCELLED = "cancelled"
    NOT_RUN = "not run"


@dataclass
class BatchItem:
    """One file of the queue and what happened to it in the latest run.

    Attributes:
        path: The file.
        kind: ``"photo"`` or ``"video"``.
        state: Where the item is.
        outputs: The files the item produced.
        warnings: The warnings its job returned.
        failure: The failure text of a failed item, or None.
        key: The file's key when it was queued (:func:`_key`); duplicate detection reads the
            path's current key instead (``add_paths``).
    """

    path: Path
    kind: sources.SourceKind
    state: ItemState = ItemState.QUEUED
    outputs: tuple[Path, ...] = ()
    warnings: tuple[str, ...] = ()
    failure: str | None = None
    key: str = field(default="", repr=False)


_stat = os.stat
"""The call that reads a queued file's identity; a test replaces it with a fake provider."""


def _path_key(path: Path) -> str:
    """Return the lexical key of a path: ``normcase`` of its absolute spelling (1.0.0's key)."""
    return "path:" + os.path.normcase(os.path.abspath(path))


def _key(path: Path) -> str:
    """Return the key every spelling of one file shares (DR-121).

    An existing file's key is its identity, the device and file number ``os.stat`` reports: one
    file under two case spellings is one item, and two distinct files whose names differ only
    by case (a case-sensitive volume) are two. A path that cannot be read, or a file system
    that reports no file number, falls back to the lexical key (:func:`_path_key`), as before.
    The identity is the file's NOW: a deleted file's number can be reused and a file replaced in
    place gets a new one, so a key is read again whenever it is compared (``add_paths``).
    """
    try:
        info = _stat(os.path.abspath(path))
    except OSError:
        info = None
    if info is None or info.st_ino == 0:
        return _path_key(path)
    return f"file:{info.st_dev}:{info.st_ino}"


def item_labels(items: list[BatchItem]) -> list[str]:
    """Return the label of each item: its file name, plus its folder when a name repeats.

    Args:
        items: The queue.

    Returns:
        One label per item, in order: ``name``, or ``name (parent folder)`` for every item whose
        file name (compared with ``normcase``: case-blind on Windows only) is shared by another.
        Two queued items are always two files (:func:`_key`), so a label never hides one.
    """
    names = [os.path.normcase(item.path.name) for item in items]
    counts = Counter(names)
    return [
        f"{item.path.name} ({item.path.parent})" if counts[name] > 1 else item.path.name
        for item, name in zip(items, names, strict=True)
    ]


def format_report(items: list[BatchItem], *, cancelled: bool) -> str:
    """Return the end-of-run report (G7).

    Args:
        items: The queue after the run.
        cancelled: True when the run was cancelled (the header says so).

    Returns:
        The text: a header, the five counts (which partition the items), and per item its
        state, outputs, each warning and the failure text.
    """

    def count(*states: ItemState) -> int:
        return sum(1 for item in items if item.state in states)

    word = "cancelled" if cancelled else "finished"
    lines = [
        f"Batch {word}: {len(items)} items.",
        f"Succeeded {count(ItemState.DONE)}, with warnings {count(ItemState.DONE_WITH_WARNINGS)}, "
        f"failed {count(ItemState.FAILED)}, cancelled {count(ItemState.CANCELLED)}, "
        f"not run {count(ItemState.NOT_RUN, ItemState.QUEUED, ItemState.RUNNING)}.",
    ]
    for number, (item, label) in enumerate(zip(items, item_labels(items), strict=True), start=1):
        state = "FAILED" if item.state is ItemState.FAILED else item.state.value
        lines.append(f"{number}. {label} - {state}")
        lines.extend(f"   output: {output}" for output in item.outputs)
        lines.extend(f"   warning: {text}" for text in item.warnings)
        if item.failure:
            lines.append(f"   failure: {item.failure}")
    return "\n".join(lines)


def _choose_files(parent: QWidget) -> list[Path]:
    """The product file chooser: a multi-select open dialog filtered to photos and videos."""
    names, _ = QFileDialog.getOpenFileNames(parent, "Add files", "", sources.file_filter())
    return [Path(name) for name in names]


class BatchPanel(QWidget):
    """The batch queue with its parameter choice, progress, cancel and end-of-run report.

    Attributes:
        queue: The list of files with their states.
        parameter_combo: "Current parameters" and every readable preset.
        start_button: Starts the run (disabled while the queue is empty or an activity runs).
        cancel_button: Cancels the running item and the rest of the batch.
        overall: The "Item i of n" line.
        bar: The current item's progress bar.
        report: The read-only end-of-run report.
    """

    def __init__(
        self,
        context: ShellContext,
        exports: ExportJobs,
        gate: ActivityGate,
        *,
        choose_files: Callable[[QWidget], list[Path]] | None = None,
    ) -> None:
        """Create the panel.

        Args:
            context: The shell context.
            exports: The export engine.
            gate: The window's one-activity gate.
            choose_files: The multi-select file dialog; None for the product's.
        """
        super().__init__()
        self._context = context
        self._exports = exports
        self._gate = gate
        self._choose_files = choose_files or _choose_files
        self._items: list[BatchItem] = []
        self._running = False
        self._cancel_requested = False
        self._handle: JobHandle | None = None
        self._current: BatchItem | None = None
        self._request_template: tuple[ParameterSet, Settings] | None = None
        self.queue = QListWidget()
        self.queue.setObjectName("batch-queue")
        self.queue.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)
        self.add_button = QPushButton("Add files...")
        self.remove_button = QPushButton("Remove selected")
        self.clear_button = QPushButton("Clear")
        self.parameter_combo = QComboBox()
        self.parameter_combo.setObjectName("batch-parameters")
        self.start_button = QPushButton("Start")
        self.cancel_button = QPushButton("Cancel")
        self.overall = QLabel("")
        self.overall.setObjectName("batch-overall")
        self.bar = QProgressBar()
        self.bar.setObjectName("batch-bar")
        self.bar.setRange(0, 1)
        self.bar.setValue(0)
        self.report = QPlainTextEdit()
        self.report.setObjectName("batch-report")
        self.report.setReadOnly(True)
        for button, name in (
            (self.add_button, "add"),
            (self.remove_button, "remove"),
            (self.clear_button, "clear"),
            (self.start_button, "start"),
            (self.cancel_button, "cancel"),
        ):
            button.setObjectName(f"batch-{name}")
        edit_row = QHBoxLayout()
        for widget in (self.add_button, self.remove_button, self.clear_button):
            edit_row.addWidget(widget)
        edit_row.addStretch(1)
        run_row = QHBoxLayout()
        run_row.addWidget(QLabel("Parameters:"))
        run_row.addWidget(self.parameter_combo, 1)
        run_row.addWidget(self.start_button)
        run_row.addWidget(self.cancel_button)
        left = QVBoxLayout()
        left.addLayout(edit_row)
        left.addWidget(self.queue, 1)
        right = QVBoxLayout()
        right.addLayout(run_row)
        right.addWidget(self.overall)
        right.addWidget(self.bar)
        right.addWidget(self.report, 1)
        layout = QHBoxLayout(self)
        layout.addLayout(left, 1)
        layout.addLayout(right, 2)
        self.add_button.clicked.connect(self._on_add)
        self.remove_button.clicked.connect(self.remove_selected)
        self.clear_button.clicked.connect(self.clear_queue)
        self.start_button.clicked.connect(self.start)
        self.cancel_button.clicked.connect(self.cancel)
        self.queue.itemSelectionChanged.connect(self._update_buttons)
        gate.subscribe(lambda _current: self._update_buttons())
        self.refresh_presets()
        self._update_buttons()

    # --- queue editing -------------------------------------------------------------------

    def items(self) -> list[BatchItem]:
        """Return a copy of the queue (the items themselves are shared)."""
        return list(self._items)

    def is_running(self) -> bool:
        """Return True from Start until the report is shown."""
        return self._running

    def add_paths(self, paths: list[Path]) -> None:
        """Queue files (the Add dialog's result); refused ones are told, not queued (D83).

        Each path goes through ``sources.route``: a refusal (a sidecar, an unsupported
        extension) is presented as a warning with owner ``"batch"`` and the file is not queued;
        a path already queued is not queued twice. A file is a duplicate when its path's
        lexical key (:func:`_path_key`) matches a queued item's, or when its identity
        (:func:`_key`) matches the CURRENT identity of a queued item's path: every queued path is
        read again here, and a queued file that no longer exists contributes no identity
        (Reviewer B finding 1: an identity cached at add time outlives its file). Ignored while
        a batch runs.

        Args:
            paths: The chosen files.
        """
        if self._running:
            return
        known_paths = {_path_key(item.path) for item in self._items}
        known_files = {_key(item.path) for item in self._items} - known_paths
        for path in paths:
            kind = sources.route(path)
            if isinstance(kind, Message):
                self._context.messages.present(Message("warning", kind.text, path, OWNER))
                continue
            lexical, key = _path_key(path), _key(path)
            if lexical in known_paths or key in known_files:
                continue
            known_paths.add(lexical)
            if key != lexical:
                known_files.add(key)
            self._items.append(BatchItem(path, kind, key=key))
        self._refresh_rows()

    def remove_selected(self) -> None:
        """Remove the selected rows from the queue (not while a batch runs)."""
        if self._running:
            return
        rows = {index.row() for index in self.queue.selectedIndexes()}
        self._items = [item for row, item in enumerate(self._items) if row not in rows]
        self._refresh_rows()

    def clear_queue(self) -> None:
        """Empty the queue and clear this panel's warnings (not while a batch runs).

        Errors are kept until the next successful Start (C3).
        """
        if self._running:
            return
        self._items = []
        self._context.messages.clear("warning", owner=OWNER)
        self._refresh_rows()

    def refresh_presets(self) -> None:
        """Reload the parameter combo from the preset store, keeping the choice if it exists."""
        chosen = self.parameter_combo.currentData()
        self.parameter_combo.clear()
        self.parameter_combo.addItem(CURRENT_PARAMETERS, None)
        for entry in self._context.presets.list_presets():
            if entry.parameter_set is not None:
                self.parameter_combo.addItem(entry.name, entry.name)
        index = self.parameter_combo.findData(chosen) if chosen is not None else 0
        self.parameter_combo.setCurrentIndex(max(0, index))

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802 (Qt override)
        """Refresh the preset list when the panel is shown (not while a batch runs)."""
        super().showEvent(event)
        if not self._running:
            self.refresh_presets()

    # --- the run -------------------------------------------------------------------------

    def start(self) -> None:
        """Start the batch: resolve the parameters once, then run the items one at a time.

        Refused with an error (owner ``"batch"``) when the chosen preset's method is not
        available or the set fails validation. The settings are ``session.settings()`` now;
        later changes do not reach the run. Every row is reset to queued, so a previous run is
        run again in full; the previous report is cleared.
        This panel's warnings are cleared at every trigger; its errors are kept until a Start
        succeeds.
        """
        if self._running or not self._items or self._gate.current is not None:
            return
        self._context.messages.clear("warning", owner=OWNER)  # errors stay until a Start succeeds
        chosen = self.parameter_combo.currentData()
        self.refresh_presets()
        resolved = self._resolve_parameters(chosen)
        if isinstance(resolved, str):
            self._context.messages.present(
                Message("error", messages.ascii_text(resolved), None, OWNER)
            )
            return
        if not self._gate.try_start("batch"):
            return
        try:  # everything after the gate is taken is guarded, so a fault releases it again
            self._request_template = (resolved, self._context.session.settings())
            self._running = True
            self._cancel_requested = False
            self._handle = None
            for item in self._items:
                item.state = ItemState.QUEUED
                item.outputs = ()
                item.warnings = ()
                item.failure = None
            self.report.clear()
            self._refresh_rows()
            self._context.messages.clear("error", owner=OWNER)  # this Start succeeded
        except Exception as error:  # a batch that cannot even start is refused, not left running
            _LOG.exception("the batch could not be started")
            self._abandon_start()
            detail = str(error) or type(error).__name__
            self._context.messages.present(
                Message(
                    "error",
                    messages.ascii_text(f"The batch could not start: {detail}"),
                    None,
                    OWNER,
                )
            )
            return
        self._advance_safely()

    def _abandon_start(self) -> None:
        """Undo a Start that failed in its setup: release the gate and reset the run state."""
        self._running = False
        self._handle = None
        self._current = None
        self._cancel_requested = False
        self._request_template = None
        self._gate.finish("batch")
        try:
            self.bar.setRange(0, 1)
            self.bar.setValue(0)
            self._update_buttons()
        except Exception:
            _LOG.exception("refreshing the batch panel after a failed start failed")

    def cancel(self) -> None:
        """Cancel the running item; the rest of the batch will not run (D45)."""
        if not self._running or self._cancel_requested:
            return
        self._cancel_requested = True
        handle = self._handle
        if handle is not None:
            handle.cancel()
        self._update_buttons()

    def _resolve_parameters(self, name: str | None) -> ParameterSet | str:
        """Return the parameter set the run uses, or why the run cannot start.

        Args:
            name: The chosen preset, or None for the current parameters.
        """
        session = self._context.session
        if name is None:
            chosen = session.parameters()
            label = "The current parameters"
        else:
            entry = next((e for e in self._context.presets.list_presets() if e.name == name), None)
            if entry is None:
                return f"Preset {name!r} is no longer available."
            if entry.parameter_set is None:
                return f"Preset {name!r} cannot be read: {entry.error}"
            chosen = entry.parameter_set
            label = f"Preset {name!r}"
        method = self._context.engines.methods.get(chosen.method)
        if method is None:
            return f"{label} use method {chosen.method!r}, which is not available."
        problems = validate_parameter_set(chosen, method.id, method.parameters)
        if problems:
            return f"{label} are not valid for {method.label}: {problems[0].message}"
        return chosen

    def _advance(self) -> None:
        """Start the next queued item, or end the run when none is left (main thread)."""
        while self._running:
            item = next((i for i in self._items if i.state is ItemState.QUEUED), None)
            if item is None:
                self._end_run()
                return
            if self._cancel_requested:
                self._mark_remaining_not_run()
                continue
            item.state = ItemState.RUNNING
            self._current = item
            total = len(self._items)
            number = self._items.index(item) + 1
            label = item_labels(self._items)[number - 1]
            self.overall.setText(f"Item {number} of {total}: {messages.ascii_text(label)}")
            self.bar.setRange(0, 0)
            self._refresh_rows()
            assert self._request_template is not None
            parameters, settings = self._request_template
            request = ExportRequest(item.path, item.kind, parameters, settings)

            try:
                job = self._exports.job(request)
                handle = self._context.jobs.run(
                    job, on_done=self._done_for(item), on_progress=self._progress
                )
            except Exception as error:  # a job that cannot start fails its item, not the batch
                detail = str(error) or type(error).__name__
                self._record(item, JobResult(False, (), (), detail, "none", 0.0))
                continue
            if item.state is ItemState.RUNNING:  # a runner that completes synchronously is done
                self._handle = handle
            return

    def _done_for(self, item: BatchItem) -> Callable[[JobResult], None]:
        """Return the completion callback of ``item``'s job."""

        def done(result: JobResult) -> None:
            self._item_done(item, result)

        return done

    def _progress(self, done: int, total: int | None, message: str) -> None:
        """Show the running item's progress (main thread)."""
        if not self._running:
            return
        if total is None or total <= 0:
            self.bar.setRange(0, 0)
        else:
            self.bar.setRange(0, total)
            self.bar.setValue(max(0, min(done, total)))

    def _item_done(self, item: BatchItem, result: JobResult) -> None:
        """An item's job ended: record it and go on, or stop (main thread)."""
        if not self._running or item is not self._current:
            return
        self._handle = None
        try:
            self._record(item, result)
        except Exception as error:  # an internal fault fails this item, not the batch
            _LOG.exception("recording a batch item failed")
            item.state = ItemState.FAILED
            item.failure = f"internal error: {type(error).__name__}: {error}"
        self._advance_safely()

    def _advance_safely(self) -> None:
        """Run :meth:`_advance`; if it fails, end the run so the gate is never left held."""
        try:
            self._advance()
        except Exception:
            _LOG.exception("the batch loop failed; the run is ended")
            self._mark_remaining_not_run()
            if self._running:
                self._end_run()

    def _record(self, item: BatchItem, result: JobResult) -> None:
        """Set the item's final state from its result (D81); a cancel stops the rest (D45)."""
        item.outputs = tuple(result.outputs)  # whatever the outcome: the report lists what exists
        item.warnings = tuple(result.warnings)  # IF-8 allows warnings on a result that is not ok
        if result.ok:
            if not result.outputs:  # an ok result names a file by contract; say so if it does not
                item.warnings += (NO_OUTPUT_TEXT,)
            item.failure = None
            item.state = ItemState.DONE_WITH_WARNINGS if item.warnings else ItemState.DONE
        elif result.failure == CANCELLED:
            item.failure = None
            item.state = ItemState.CANCELLED
            self._cancel_requested = True
        else:
            item.failure = result.failure or "the export failed"
            item.state = ItemState.FAILED
            _LOG.warning(
                "batch item failed: %s: %s",
                messages.ascii_text(str(item.path)),
                messages.ascii_text(item.failure),
            )
        self._refresh_rows()

    def _mark_remaining_not_run(self) -> None:
        """Mark every item that has not run as "not run" (D45)."""
        for item in self._items:
            if item.state in (ItemState.QUEUED, ItemState.RUNNING):
                item.state = ItemState.NOT_RUN
        self._refresh_rows()

    def _end_run(self) -> None:
        """Release the gate, then show and log the report (main thread)."""
        cancelled = any(
            item.state in (ItemState.CANCELLED, ItemState.NOT_RUN) for item in self._items
        )
        self._running = False
        self._handle = None
        self._current = None
        self._cancel_requested = False
        self.bar.setRange(0, 1)
        self.bar.setValue(0)
        self._gate.finish("batch")
        text = format_report(self._items, cancelled=cancelled)
        self.report.setPlainText(text)
        self.overall.setText(text.splitlines()[0])
        _LOG.info("%s", messages.ascii_text(text))
        self._update_buttons()

    # --- widgets -------------------------------------------------------------------------

    def _on_add(self) -> None:
        """The Add button: choose files and queue them."""
        self.add_paths(self._choose_files(self))

    def _refresh_rows(self) -> None:
        """Rebuild the list from the items, keeping the selection by row."""
        selected = {index.row() for index in self.queue.selectedIndexes()}
        self.queue.clear()
        for item, label in zip(self._items, item_labels(self._items), strict=True):
            self.queue.addItem(f"{label} - {item.state.value}")
        for row in selected:
            if row < self.queue.count():
                self.queue.item(row).setSelected(True)
        if not self._running and not self._items:
            self.overall.setText("")
        self._update_buttons()

    def _update_buttons(self) -> None:
        """Enable each control for the current state (queue editing is locked while running)."""
        idle = not self._running
        for widget in (self.add_button, self.clear_button, self.parameter_combo):
            widget.setEnabled(idle)
        self.remove_button.setEnabled(idle and bool(self.queue.selectedIndexes()))
        blocked = self._gate.reason()
        self.start_button.setEnabled(idle and bool(self._items) and blocked is None)
        self.start_button.setToolTip(blocked or "")
        self.cancel_button.setEnabled(self._running and not self._cancel_requested)


def batch_panel_factory(
    exports: ExportJobs,
    gates: SharedGate,
    *,
    choose_files: Callable[[QWidget], list[Path]] | None = None,
) -> PanelFactory:
    """Return the factory of the Batch panel.

    Args:
        exports: The export engine.
        gates: The window's shared gate holder.
        choose_files: The multi-select file dialog (tests inject one), or None.

    Returns:
        A ``PanelFactory`` for ``ShellWindow.attach``.
    """

    def build(context: ShellContext) -> QWidget:
        gate = gates.get(context.actions.export.set_unavailable)
        return BatchPanel(context, exports, gate, choose_files=choose_files)

    return build
