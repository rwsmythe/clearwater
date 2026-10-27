"""The settings dialog behind Tools > Settings (WP3.20; G12, G13, D74, D71, AD-9).

``install_settings_dialog(window)`` registers :func:`settings_dialog` with
``ShellWindow.set_settings_dialog``; the shell opens a new dialog, window-modally, each time the
action is triggered. The dialog edits every G12 setting starting from ``session.settings()``,
shows an unavailable encoder disabled with its reason (D74), validates the output suffix on
every edit (D36), saves through ``clearwater.config.save_settings`` unless the session refused
the settings file (G13, S4), applies the result with ``session.set_settings`` and sets the cache
limit and clears the cache in jobs, never on the interface thread (D71).

A control that is still at the value it first displayed does not overwrite its field, so a stored
value the control cannot show exactly (a cache limit that is not a whole number of gigabytes, an
encoder this computer no longer reports) is written back unchanged unless the user edits it, and
``last_parameters`` stays as the session holds it.

Encoder capabilities are read once per session through the injected sink, in a job started by
the first dialog that opens (the contract gives ``install_settings_dialog`` no context to start
it earlier); start-up detection is WP4.3's.

Message owner: every message this module presents has owner :data:`OWNER_SETTINGS`.
Threading: everything here runs on the interface thread except the job callables, which only
call the injected engines.
"""

from __future__ import annotations

import contextlib
import dataclasses
import threading
import time
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Any, Protocol, cast

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from clearwater.config import SETTINGS_FILE_NAME, save_settings
from clearwater.interfaces import (
    EncoderCapability,
    FormatError,
    JobResult,
    Progress,
    ProxyCache,
    Settings,
)
from clearwater.jobs import validate_suffix

from .contract import Message, ShellContext, ShellWindow
from .messages import ascii_text, file_name

OWNER_SETTINGS = "settings"
"""The owner of every message this dialog presents (DR-44 (b))."""

AUTO = "auto"
"""The stored value of the automatic encoder choice (IF-10)."""

GB = 10**9
"""One gigabyte in bytes: the SI unit of ``DEFAULT_CACHE_LIMIT_BYTES``."""

MIN_CACHE_GB = 1
"""The smallest cache limit the dialog offers."""

MAX_CACHE_GB = 100_000
"""The largest cache limit the dialog offers (100 TB)."""

SAME_FOLDER_TEXT = "Same folder as the source"
"""What the output folder control shows for ``output_folder`` None (D34)."""

AUTO_TEXT = "Automatic (NVENC when available)"
"""The text of the automatic encoder item."""

DETECTING_TEXT = "Detecting encoders..."
"""Shown while the capability job runs."""

NO_ENCODER_REASON = "No video encoder is available."
"""Why 10-bit output is disabled when "auto" resolves to nothing."""

CLEAR_BLOCKED_REASON = "The cache cannot be cleared while a clip is being analysed."
"""Why Clear cache is disabled while an analysis runs (Q4)."""

NOT_FOUND_REASON = "not found on this computer"
"""Why a stored encoder the sink does not report is shown unavailable."""

_HARDWARE_ENCODER = "hevc_nvenc"
_SOFTWARE_ENCODER = "libx265"

type EncoderResolver = Callable[[str, Sequence[EncoderCapability]], str]
"""``resolve_encoder(setting, capabilities) -> name``: the one "auto" rule (WP3.10)."""


def interim_resolve_encoder(setting: str, capabilities: Sequence[EncoderCapability]) -> str:
    """Stand in for WP3.10's ``resolve_encoder`` until that package is on main.

    It has WP3.10's signature and rule: ``"auto"`` becomes ``hevc_nvenc`` when it is available,
    else ``libx265`` when it is available; any other setting is returned unchanged. When WP3.10
    is on main, this function is deleted and ``resolve_encoder`` of
    ``clearwater.io.video.capability`` becomes the default of the ``resolve_encoder`` parameters
    of :func:`settings_dialog` and :func:`install_settings_dialog`.

    Args:
        setting: ``"auto"`` or an encoder name.
        capabilities: The sink's capability report.

    Returns:
        The encoder name, never ``"auto"``.

    Raises:
        LookupError: The setting is ``"auto"`` and neither encoder is available.
    """
    if setting != AUTO:
        return setting
    available = {c.name for c in capabilities if c.available}
    for name in (_HARDWARE_ENCODER, _SOFTWARE_ENCODER):
        if name in available:
            return name
    raise LookupError("no HEVC encoder is available")


class SettingsChoosers(Protocol):
    """The modal questions the dialog asks, injectable so tests never block on one."""

    def choose_folder(self, initial: Path | None) -> Path | None:
        """Ask for an output folder.

        Args:
            initial: The folder to start in, or None.

        Returns:
            The chosen folder, or None when the user cancelled.
        """
        ...

    def confirm(self, text: str) -> bool:
        """Ask a yes/no question.

        Args:
            text: The question.

        Returns:
            True when the user confirmed.
        """
        ...


class QtChoosers:
    """The Qt implementation of :class:`SettingsChoosers`."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create the choosers.

        Args:
            parent: The widget the modal dialogs belong to.
        """
        self._parent = parent

    def choose_folder(self, initial: Path | None) -> Path | None:
        """Ask for a folder with the native folder dialog.

        Args:
            initial: The folder to start in, or None.

        Returns:
            The chosen folder, or None when cancelled.
        """
        chosen = QFileDialog.getExistingDirectory(
            self._parent, "Output folder", "" if initial is None else str(initial)
        )
        return Path(chosen) if chosen else None

    def confirm(self, text: str) -> bool:
        """Ask a yes/no question with a message box.

        Args:
            text: The question.

        Returns:
            True when the user chose Yes.
        """
        answer = QMessageBox.question(
            self._parent,
            "Clearwater",
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes


def _done(started: float) -> JobResult:
    """Return the successful result of a job that started at ``started``."""
    return JobResult(True, (), (), None, "cpu", time.perf_counter() - started)


def _present_error(context: ShellContext, text: str, path: Path | None = None) -> None:
    """Present an error banner owned by this dialog."""
    context.messages.present(Message("error", ascii_text(text), path, OWNER_SETTINGS))


class EncoderCatalog(QObject):
    """The encoder capabilities of the session, read once through the sink (D74).

    The first :meth:`start` runs ``engines.video_sink.capabilities()`` in a job; later calls do
    nothing, so the result is cached for the session. ``ready`` is emitted on the interface
    thread when the job ends.
    """

    ready = Signal()

    def __init__(self, parent: QObject | None = None) -> None:
        """Create an idle catalog.

        Args:
            parent: The owner (the main window), or None.
        """
        super().__init__(parent)
        self._state = "idle"
        self._capabilities: tuple[EncoderCapability, ...] = ()
        self._failure: str | None = None

    def start(self, context: ShellContext) -> None:
        """Start the capability job unless it was started before.

        Args:
            context: The shell context (the sink and the job runner).
        """
        if self._state != "idle":
            return
        self._state = "detecting"
        sink = context.engines.video_sink
        found: list[tuple[EncoderCapability, ...]] = []

        def job(progress: Progress) -> JobResult:
            started = time.perf_counter()
            found.append(tuple(sink.capabilities()))
            return _done(started)

        def done(result: JobResult) -> None:
            if result.ok and found:
                self._capabilities = found[0]
            else:
                self._failure = result.failure or "no capability report"
            self._state = "ready"
            self.ready.emit()

        try:
            context.jobs.run(job, on_done=done)
        except RuntimeError as error:  # the job runner is closed: the window is shutting down
            self._failure = str(error)
            self._state = "ready"

    def detecting(self) -> bool:
        """Return True from :meth:`start` until the job has ended."""
        return self._state == "detecting"

    def capabilities(self) -> tuple[EncoderCapability, ...]:
        """Return the sink's report, empty before it arrives or after a failure."""
        return self._capabilities

    def failure(self) -> str | None:
        """Return why the report could not be read, or None."""
        return self._failure


class CacheLimiter:
    """Serialises the cache-limit calls so that the last accepted limit wins (D71).

    Every accepted limit change runs ``cache.set_limit_bytes`` in its own job, and jobs may run in
    any order. :meth:`want` (interface thread) records the newest limit; each job calls
    :meth:`apply` (worker thread), which takes the call lock and applies the newest recorded
    limit, whichever job it belongs to. So the cache always ends at the last accepted value, and
    two calls never overlap. :meth:`want` takes only the short value lock, never the call lock, so
    the interface thread never waits for a call in progress.
    """

    def __init__(self) -> None:
        """Create a limiter that has no limit wanted yet."""
        self._latest: int | None = None
        self._value_lock = threading.Lock()
        self._call_lock = threading.Lock()

    def want(self, limit_bytes: int) -> None:
        """Record the newest accepted limit.

        Args:
            limit_bytes: The limit in bytes.
        """
        with self._value_lock:
            self._latest = limit_bytes

    def apply(self, cache: ProxyCache) -> None:
        """Set the newest recorded limit on the cache, one call at a time (worker thread).

        Args:
            cache: The proxy cache (IF-7).
        """
        with self._call_lock:
            with self._value_lock:
                limit = self._latest
            if limit is not None:
                cache.set_limit_bytes(limit)


class SettingsDialog(QDialog):
    """The settings dialog (G12); build one with :func:`settings_dialog`."""

    def __init__(
        self,
        context: ShellContext,
        choosers: SettingsChoosers,
        resolve_encoder: EncoderResolver,
        catalog: EncoderCatalog,
        cache_limiter: CacheLimiter,
    ) -> None:
        """Create the dialog on the session's current settings.

        Args:
            context: The shell context.
            choosers: The folder chooser and confirmation.
            resolve_encoder: The one "auto" rule, used for the 10-bit rule.
            catalog: The session's encoder capabilities; started here when idle.
            cache_limiter: The session's cache-limit serialiser, shared between dialogs.
        """
        super().__init__(context.window)
        self._context = context
        self._choosers = choosers
        self._resolve = resolve_encoder
        self._catalog = catalog
        self._limiter = cache_limiter
        self._initial = context.session.settings()
        self._folder: Path | None = self._initial.output_folder
        self._clearing = False
        self._closed = False
        self.setWindowTitle("Settings")
        self.setObjectName("settings_dialog")
        catalog.start(context)
        self._build()
        self._shown = self._current()
        self._update_encoder_note()
        self._update_ten_bit()
        self._check_suffix()
        self._update_clear_button()
        context.session.analysis_changed.connect(self._update_clear_button)
        catalog.ready.connect(self._on_catalog_ready)
        self.finished.connect(self._on_finished)

    # Construction.

    def _build(self) -> None:
        """Create the widgets and the layout, in G12 order."""
        initial = self._initial
        layout = QVBoxLayout(self)
        self.refusal_label = QLabel(self)
        self.refusal_label.setWordWrap(True)
        refusal = self._context.session.settings_refusal()
        if refusal is None:
            self.refusal_label.setVisible(False)
        else:
            name = SETTINGS_FILE_NAME if refusal.path is None else file_name(refusal.path)
            self.refusal_label.setText(
                f"Changes apply to this session only; {name} was left unchanged.\n{refusal.text}"
            )
        layout.addWidget(self.refusal_label)

        form = QFormLayout()
        layout.addLayout(form)

        self.folder_label = QLabel(self)
        self.choose_folder_button = QPushButton("Choose...", self)
        self.use_source_button = QPushButton("Use source folder", self)
        folder_row = QHBoxLayout()
        folder_row.addWidget(self.folder_label, 1)
        folder_row.addWidget(self.choose_folder_button)
        folder_row.addWidget(self.use_source_button)
        form.addRow("Output folder:", folder_row)
        self._show_folder()
        self.choose_folder_button.clicked.connect(self._on_choose_folder)
        self.use_source_button.clicked.connect(self._on_use_source)

        self.suffix_edit = QLineEdit(initial.output_suffix, self)
        self.suffix_error = QLabel(self)
        self.suffix_error.setWordWrap(True)
        suffix_box = QVBoxLayout()
        suffix_box.addWidget(self.suffix_edit)
        suffix_box.addWidget(self.suffix_error)
        form.addRow("Output suffix:", suffix_box)
        self.suffix_edit.textChanged.connect(self._check_suffix)

        self.png_combo = QComboBox(self)
        self.png_combo.addItem("16-bit", 16)
        self.png_combo.addItem("8-bit", 8)
        self._select(self.png_combo, initial.png_bit_depth)
        form.addRow("PNG bit depth:", self.png_combo)

        self.encoder_combo = QComboBox(self)
        self.encoder_note = QLabel(self)
        self.encoder_note.setWordWrap(True)
        encoder_box = QVBoxLayout()
        encoder_box.addWidget(self.encoder_combo)
        encoder_box.addWidget(self.encoder_note)
        form.addRow("Video encoder:", encoder_box)
        self._populate_encoders(initial.video_encoder)
        self.encoder_combo.currentIndexChanged.connect(self._on_encoder_changed)

        self.quality_combo = QComboBox(self)
        self.quality_combo.addItem("High", "high")
        self.quality_combo.addItem("Standard", "standard")
        self.quality_combo.addItem("Draft", "draft")
        self._select(self.quality_combo, initial.quality_level)
        form.addRow("Video quality:", self.quality_combo)

        self.ten_bit_check = QCheckBox("Write 10-bit video from 8-bit sources", self)
        self.ten_bit_check.setChecked(initial.ten_bit_for_eight_bit)
        self.ten_bit_note = QLabel(self)
        self.ten_bit_note.setWordWrap(True)
        ten_bit_box = QVBoxLayout()
        ten_bit_box.addWidget(self.ten_bit_check)
        ten_bit_box.addWidget(self.ten_bit_note)
        form.addRow("10-bit output:", ten_bit_box)

        self.provenance_check = QCheckBox("Embed Clearwater version and parameters", self)
        self.provenance_check.setChecked(initial.provenance)
        form.addRow("Provenance:", self.provenance_check)

        self.cache_spin = QSpinBox(self)
        self.cache_spin.setRange(MIN_CACHE_GB, MAX_CACHE_GB)
        self.cache_spin.setSuffix(" GB")
        # Integer arithmetic: a float division overflows for a huge stored int.
        shown_gb = (initial.cache_limit_bytes + GB // 2) // GB
        self.cache_spin.setValue(min(MAX_CACHE_GB, max(MIN_CACHE_GB, shown_gb)))
        form.addRow("Cache size limit:", self.cache_spin)

        self.clear_button = QPushButton("Clear cache", self)
        self.cache_note = QLabel(self)
        self.cache_note.setWordWrap(True)
        clear_row = QHBoxLayout()
        clear_row.addWidget(self.clear_button)
        clear_row.addWidget(self.cache_note, 1)
        form.addRow("Cache:", clear_row)
        self.clear_button.clicked.connect(self._on_clear_clicked)

        advanced = QGroupBox("Advanced", self)
        advanced_layout = QVBoxLayout(advanced)
        self.force_cpu_check = QCheckBox("Force CPU processing", advanced)
        self.force_cpu_check.setChecked(initial.force_cpu)
        advanced_layout.addWidget(self.force_cpu_check)
        layout.addWidget(advanced)

        self.buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self
        )
        self.buttons.accepted.connect(self.accept)
        self.buttons.rejected.connect(self.reject)
        layout.addWidget(self.buttons)
        self.ok_button = self.buttons.button(QDialogButtonBox.StandardButton.Ok)

    @staticmethod
    def _select(combo: QComboBox, data: object) -> None:
        """Select the item holding ``data`` when there is one; else leave the first."""
        index = combo.findData(data)
        if index >= 0:
            combo.setCurrentIndex(index)

    # Encoders (D74).

    def _populate_encoders(self, selected: str) -> None:
        """Fill the encoder list from the catalog and select ``selected``.

        Unavailable items are disabled with their reason; a stored encoder the sink does not
        report is added as a disabled item (its reason is the detection failure when the report
        could not be read); while the report is being read the control is disabled.
        """
        combo = self.encoder_combo
        combo.blockSignals(True)
        combo.clear()
        combo.addItem(AUTO_TEXT, AUTO)
        reported = {c.name for c in self._catalog.capabilities()}
        for capability in self._catalog.capabilities():
            if capability.available:
                combo.addItem(capability.name, capability.name)
            else:
                reason = capability.reason or "not available"
                combo.addItem(f"{capability.name} (unavailable: {reason})", capability.name)
                self._disable_item(combo.count() - 1, reason)
        if selected != AUTO and selected not in reported:
            if self._catalog.detecting():
                combo.addItem(selected, selected)
            else:
                reason = NOT_FOUND_REASON
                if self._catalog.failure() is not None:
                    reason = ascii_text(
                        f"encoders could not be detected: {self._catalog.failure()}"
                    )
                combo.addItem(f"{selected} (unavailable: {reason})", selected)
                self._disable_item(combo.count() - 1, reason)
        self._select(combo, selected)
        combo.setEnabled(not self._catalog.detecting())
        combo.blockSignals(False)

    def _disable_item(self, index: int, reason: str) -> None:
        """Make encoder item ``index`` unselectable, with ``reason`` as its tool tip."""
        model = cast(QStandardItemModel, self.encoder_combo.model())
        item = model.item(index)
        assert isinstance(item, QStandardItem)
        item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
        item.setToolTip(reason)

    def _on_catalog_state(self) -> None:
        """Show the encoder list for the catalog's state (detecting, ready or failed)."""
        current = self.encoder_combo.currentData()
        self._populate_encoders(self._initial.video_encoder if current is None else str(current))
        self._update_encoder_note()
        self._update_ten_bit()
        self._refresh_ok()

    def _on_catalog_ready(self) -> None:
        """The capability job ended: refresh the encoder control."""
        if not self._closed:
            self._on_catalog_state()

    def _update_encoder_note(self) -> None:
        """Say why the encoder control is limited: detecting, or the detection failure."""
        failure = self._catalog.failure()
        if self._catalog.detecting():
            self.encoder_note.setText(DETECTING_TEXT)
        elif failure is not None:
            self.encoder_note.setText(ascii_text(f"Encoders could not be detected: {failure}"))
        else:
            self.encoder_note.setText("")
        self.encoder_combo.setToolTip(self.encoder_note.text())

    def _on_encoder_changed(self, _index: int) -> None:
        """The user chose an encoder: re-evaluate the 10-bit rule and OK."""
        self._update_ten_bit()
        self._refresh_ok()

    def _selected_capability(self) -> EncoderCapability | None:
        """Return the capability of the selected (or, for "auto", resolved) encoder, or None."""
        name = str(self.encoder_combo.currentData())
        capabilities = self._catalog.capabilities()
        if name == AUTO:
            try:
                name = self._resolve(AUTO, capabilities)
            except Exception:  # any failure of the rule means "unresolved"
                return None
        return next((c for c in capabilities if c.name == name), None)

    def _update_ten_bit(self) -> None:
        """Enable the 10-bit option or disable it with the reason (D76); keep its value."""
        name = str(self.encoder_combo.currentData())
        if self._catalog.detecting():
            self.ten_bit_check.setEnabled(False)
            self.ten_bit_check.setToolTip(DETECTING_TEXT)
            self.ten_bit_note.setText(DETECTING_TEXT)
            return
        capability = self._selected_capability()
        if capability is None:
            reason = NO_ENCODER_REASON if name == AUTO else f"{name} cannot write 10-bit video."
        elif not capability.available or 10 not in capability.bit_depths:
            reason = f"{capability.name} cannot write 10-bit video."
        else:
            reason = ""
        self.ten_bit_check.setEnabled(not reason)
        self.ten_bit_check.setToolTip(reason)
        self.ten_bit_note.setText(reason)

    def _encoder_unacceptable(self) -> bool:
        """Return True when the encoder was changed to one the sink reports as unavailable."""
        name = self.encoder_combo.currentData()
        if name == self._initial.video_encoder or name == AUTO or self._catalog.detecting():
            return False
        capability = next((c for c in self._catalog.capabilities() if c.name == name), None)
        return capability is None or not capability.available

    # Suffix, folder.

    def _check_suffix(self, *_: object) -> None:
        """Validate the suffix (D36, DR-35): show the error beside the field, gate OK."""
        try:
            validate_suffix(self.suffix_edit.text())
        except ValueError as error:
            self.suffix_error.setText(ascii_text(str(error)))
            self.suffix_edit.setToolTip(self.suffix_error.text())
        else:
            self.suffix_error.setText("")
            self.suffix_edit.setToolTip("")
        self._refresh_ok()

    def _refresh_ok(self) -> None:
        """Enable OK only while the suffix and the encoder choice are acceptable."""
        self.ok_button.setEnabled(not self.suffix_error.text() and not self._encoder_unacceptable())

    def _show_folder(self) -> None:
        """Show the output folder (D34)."""
        self.folder_label.setText(SAME_FOLDER_TEXT if self._folder is None else str(self._folder))

    def _on_choose_folder(self) -> None:
        """Ask for an output folder; a cancel changes nothing."""
        chosen = self._choosers.choose_folder(self._folder)
        if chosen is not None:
            self._folder = chosen
            self._show_folder()

    def _on_use_source(self) -> None:
        """Go back to writing next to the source."""
        self._folder = None
        self._show_folder()

    # The cache (D71).

    def _analysing(self) -> bool:
        """Return True while the open clip is being analysed."""
        return self._context.session.analysis().phase == "running"

    def _update_clear_button(self, *_: object) -> None:
        """Set the Clear cache button for the analysis phase and its own job."""
        if self._closed:
            return
        if self._clearing:
            self.clear_button.setText("Clearing...")
            self.clear_button.setEnabled(False)
            self.clear_button.setToolTip("")
        elif self._analysing():
            self.clear_button.setText("Clear cache")
            self.clear_button.setEnabled(False)
            self.clear_button.setToolTip(CLEAR_BLOCKED_REASON)
            self.cache_note.setText(CLEAR_BLOCKED_REASON)
        else:
            self.clear_button.setText("Clear cache")
            self.clear_button.setEnabled(True)
            self.clear_button.setToolTip("")
            if self.cache_note.text() == CLEAR_BLOCKED_REASON:
                self.cache_note.setText("")

    def _on_clear_clicked(self) -> None:
        """Confirm, check again that no analysis runs, then clear the cache in a job."""
        if self._clearing or self._analysing():
            return
        if not self._choosers.confirm(
            "Remove every cached proxy and statistic? Clips are analysed again when needed."
        ):
            return
        # The confirmation runs a nested event loop: an analysis may have started, or the dialog
        # may have closed, while it was open.
        if self._closed:
            return
        if self._analysing():
            self._update_clear_button()
            return
        self._clearing = True
        self.cache_note.setText("")
        self._update_clear_button()
        cache = self._context.engines.cache

        def job(progress: Progress) -> JobResult:
            started = time.perf_counter()
            cache.clear()
            return _done(started)

        context = self._context
        try:
            context.jobs.run(job, on_done=self._on_clear_done)
        except RuntimeError as error:  # the job runner is closed: the window is shutting down
            self._clearing = False
            _present_error(context, f"The cache could not be cleared: {error}")
            self._update_clear_button()

    def _on_clear_done(self, result: JobResult) -> None:
        """Main thread: the clear job ended."""
        if not result.ok:
            _present_error(self._context, f"The cache could not be cleared: {result.failure}")
        if self._closed:
            return
        self._clearing = False
        self.cache_note.setText("Cache cleared." if result.ok else "")
        self._update_clear_button()

    # Accept (G13).

    def _current(self) -> dict[str, Any]:
        """Return the value each control shows now, keyed by ``Settings`` field."""
        return {
            "output_folder": self._folder,
            "output_suffix": self.suffix_edit.text(),
            "png_bit_depth": self.png_combo.currentData(),
            "video_encoder": self.encoder_combo.currentData(),
            "quality_level": self.quality_combo.currentData(),
            "ten_bit_for_eight_bit": self.ten_bit_check.isChecked(),
            "provenance": self.provenance_check.isChecked(),
            "cache_limit_bytes": self.cache_spin.value(),
            "force_cpu": self.force_cpu_check.isChecked(),
        }

    def edited_settings(self) -> Settings:
        """Return the session's settings with only the edited controls applied.

        Returns:
            The settings OK would apply; ``last_parameters`` is the session's.
        """
        changes = {
            field: value for field, value in self._current().items() if value != self._shown[field]
        }
        if "cache_limit_bytes" in changes:
            changes["cache_limit_bytes"] = int(changes["cache_limit_bytes"]) * GB
        return dataclasses.replace(self._context.session.settings(), **changes)

    def accept(self) -> None:
        """Validate settings to apply, save unless refused, apply, set the cache limit, close."""
        new = self.edited_settings()
        try:
            validate_suffix(new.output_suffix)
        except ValueError as error:
            self._check_suffix()
            detail = ascii_text(str(error))[:200]
            _present_error(self._context, f"The output suffix is not valid: {detail}")
            return
        if self._encoder_unacceptable():
            return
        context = self._context
        session = context.session
        old = session.settings()
        if session.settings_refusal() is None:
            self._save(new)
        session.set_settings(new)
        if new.cache_limit_bytes != old.cache_limit_bytes:
            self._set_cache_limit(new.cache_limit_bytes)
        super().accept()

    def _save(self, settings: Settings) -> None:
        """Save through ``save_settings``; a failure is an error banner, a success clears them."""
        context = self._context
        path = context.locations.settings_file
        try:
            save_settings(context.locations.config_dir, settings)
        except (FormatError, ValueError, OSError) as error:
            _present_error(
                context,
                f"The settings could not be saved to {file_name(path)}: {error}",
                path,
            )
        else:
            context.messages.clear(owner=OWNER_SETTINGS)

    def _set_cache_limit(self, limit_bytes: int) -> None:
        """Set the cache limit in a job (it may evict on disk); the newest accepted limit wins."""
        context = self._context
        cache = context.engines.cache
        limiter = self._limiter
        limiter.want(limit_bytes)

        def job(progress: Progress) -> JobResult:
            started = time.perf_counter()
            limiter.apply(cache)
            return _done(started)

        def done(result: JobResult) -> None:
            if not result.ok:
                _present_error(context, f"The cache limit could not be set: {result.failure}")

        try:
            context.jobs.run(job, on_done=done)
        except RuntimeError as error:  # the job runner is closed: the window is shutting down
            _present_error(context, f"The cache limit could not be set: {error}")

    def _on_finished(self, _result: int) -> None:
        """The dialog closed: stop listening and let Qt delete it."""
        self._closed = True
        for signal, slot in (
            (self._context.session.analysis_changed, self._update_clear_button),
            (self._catalog.ready, self._on_catalog_ready),
        ):
            with contextlib.suppress(RuntimeError, TypeError):
                signal.disconnect(slot)
        self.deleteLater()


def settings_dialog(
    context: ShellContext,
    *,
    choosers: SettingsChoosers | None = None,
    resolve_encoder: EncoderResolver | None = None,
    catalog: EncoderCatalog | None = None,
    cache_limiter: CacheLimiter | None = None,
) -> SettingsDialog:
    """Build a new settings dialog on the session's current settings.

    Args:
        context: The shell context.
        choosers: The folder chooser and confirmation; the Qt ones when None.
        resolve_encoder: The one "auto" rule; :func:`interim_resolve_encoder` when None.
        catalog: The session's encoder capabilities, shared between dialogs; a new one for this
            dialog when None.
        cache_limiter: The session's cache-limit serialiser, shared between dialogs so that the
            last accepted limit wins; a new one for this dialog when None.

    Returns:
        The dialog; the shell opens it with ``QDialog.open()``.
    """
    return SettingsDialog(
        context,
        choosers or QtChoosers(context.window),
        resolve_encoder or interim_resolve_encoder,
        catalog or EncoderCatalog(context.window),
        cache_limiter or CacheLimiter(),
    )


def install_settings_dialog(
    window: ShellWindow,
    *,
    choosers: SettingsChoosers | None = None,
    resolve_encoder: EncoderResolver | None = None,
) -> None:
    """Register the settings dialog with the window (Tools > Settings).

    The encoder capabilities are read once, by the first dialog that opens, and shared by every
    later one; so is the serialiser of the cache-limit calls.

    Args:
        window: The main window.
        choosers: The folder chooser and confirmation; the Qt ones when None.
        resolve_encoder: The one "auto" rule; :func:`interim_resolve_encoder` when None.
    """
    catalog = EncoderCatalog(window)
    cache_limiter = CacheLimiter()

    def factory(context: ShellContext) -> SettingsDialog:
        return settings_dialog(
            context,
            choosers=choosers,
            resolve_encoder=resolve_encoder,
            catalog=catalog,
            cache_limiter=cache_limiter,
        )

    window.set_settings_dialog(factory)
