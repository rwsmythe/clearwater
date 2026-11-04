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
the first dialog that opens, or earlier by the application's start-up through the ``catalog``
argument of :func:`install_settings_dialog` (WP4.3, DR-52). The one "auto" rule is WP3.10's
``clearwater.io.video.capability.resolve_encoder``.

Message owner: every message this module presents has owner :data:`OWNER_SETTINGS`. An error of
the clear or limit job that ends while the MAIN window is closing is logged, not presented
(WP4.3 R2-3: both jobs wait for the application's deferred cache open); the closed signal is the
caller's ``window_closing`` argument of :func:`install_settings_dialog`.
Threading: everything here runs on the interface thread except the job callables, which only
call the injected engines.
"""

from __future__ import annotations

import contextlib
import dataclasses
import logging
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
from clearwater.io.video.capability import resolve_encoder as wp310_resolve_encoder
from clearwater.jobs import validate_suffix

from .contract import Message, ShellContext, ShellWindow
from .messages import ascii_text, file_name

_LOG = logging.getLogger(__name__)

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

AUTO_TEXT = "Automatic (the hardware encoder when available)"
"""The text of the automatic encoder item (G12 v0.6.1: platform-neutral)."""

ENCODER_FAMILIES = {"hevc_nvenc": "NVENC", "hevc_videotoolbox": "VideoToolbox"}
"""The family name the automatic item's tool tip gives a hardware encoder."""

DETECTING_TEXT = "Detecting encoders..."
"""Shown while the capability job runs."""

NO_ENCODER_REASON = "No video encoder is available."
"""Why 10-bit output is disabled when "auto" resolves to nothing."""

CLEAR_BLOCKED_REASON = "The cache cannot be cleared while a clip is being analysed."
"""Why Clear cache is disabled while an analysis runs (Q4)."""

NOT_FOUND_REASON = "not found on this computer"
"""Why a stored encoder the sink does not report is shown unavailable."""

type EncoderResolver = Callable[[str, Sequence[EncoderCapability]], str]


def auto_tooltip(capabilities: Sequence[EncoderCapability]) -> str:
    """Return the automatic item's tool tip: what ``"auto"`` tries, in the roster's order.

    The capability report lists this platform's roster in preference order (NVENC on Windows,
    VideoToolbox on macOS, then libx265), so the tip names the hardware encoder of the
    platform without the dialog knowing which platform it runs on.

    Args:
        capabilities: The sink's capability report, in roster order.

    Returns:
        For example ``"Uses NVENC (hevc_nvenc) when it is available, else libx265."``; the
        empty string while nothing is reported.
    """
    hardware = [f"{ENCODER_FAMILIES.get(c.name, c.name)} ({c.name})" for c in capabilities if c.hw]
    software = [c.name for c in capabilities if not c.hw]
    if hardware and software:
        return f"Uses {', '.join(hardware)} when it is available, else {', '.join(software)}."
    if hardware or software:
        return f"Uses {', '.join(hardware or software)}."
    return ""


"""``resolve_encoder(setting, capabilities) -> name``: the one "auto" rule (WP3.10)."""


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


def _detail(error: BaseException) -> str:
    """Return an error's text for a message, never raising (DR-61 (i), (iii)).

    The exception's own text, or its type name when the text is empty or cannot be formatted
    (an injected chooser's exception whose ``__str__`` raises).
    """
    try:
        text = str(error)
    except Exception:  # the exception's own formatting failed
        text = ""
    return text or type(error).__name__


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
        window_closing: Callable[[], bool] | None = None,
    ) -> None:
        """Create the dialog on the session's current settings.

        Args:
            context: The shell context.
            choosers: The folder chooser and confirmation.
            resolve_encoder: The one "auto" rule, used for the 10-bit rule.
            catalog: The session's encoder capabilities; started here when idle.
            cache_limiter: The session's cache-limit serialiser, shared between dialogs.
            window_closing: True once the main window is closing (R2-3); never when None.
        """
        super().__init__(context.window)
        self._context = context
        self._choosers = choosers
        self._resolve = resolve_encoder
        self._catalog = catalog
        self._limiter = cache_limiter
        self._window_closing = window_closing or (lambda: False)
        self._initial = context.session.settings()
        self._folder: Path | None = self._initial.output_folder
        self._clearing = False
        self._closed = False
        self._shown_errors: set[str] = set()
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
        context.session.settings_changed.connect(self._on_session_settings)
        catalog.ready.connect(self._on_catalog_ready)
        self.finished.connect(self._on_finished)

    def _error(self, text: str, path: Path | None = None) -> None:
        """Present a settings error banner, once while it is shown (DR-61 (iii)).

        A text this dialog presented since it last cleared its banners is not presented again,
        so repeating a refused action does not stack copies of one banner.
        """
        shown = ascii_text(text)
        if shown in self._shown_errors:
            return
        self._shown_errors.add(shown)
        _present_error(self._context, shown, path)

    def _cache_job_error(self, text: str) -> None:
        """A cache job's error: logged, and presented unless the main window is closing (R2-3)."""
        if self._window_closing():
            _LOG.warning("%s (not shown: the window is closing)", ascii_text(text))
            return
        self._error(text)

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
        tip = auto_tooltip(self._catalog.capabilities())
        if tip:
            combo.setItemData(0, tip, Qt.ItemDataRole.ToolTipRole)
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

    def _on_session_settings(self, _settings: object) -> None:
        """The session's settings changed: re-evaluate what OK would apply (DR-61 (ii)).

        An unedited control applies the session's value, so a refusal that came from the
        session's value (a suffix refused at OK) is lifted when the session is corrected.
        """
        if self._closed:
            return
        self._check_suffix()
        self._update_encoder_note()
        self._update_ten_bit()
        self._refresh_ok()

    def _update_encoder_note(self, name: str | None = None) -> None:
        """Explain detection state or why the encoder to apply is refused.

        Args:
            name: The encoder to apply, or None to read the edited settings.
        """
        if name is None:
            name = self.edited_settings().video_encoder
        failure = self._catalog.failure()
        if self._catalog.detecting():
            self.encoder_note.setText(DETECTING_TEXT)
        elif self._encoder_unacceptable(name):
            capability = next((c for c in self._catalog.capabilities() if c.name == name), None)
            reason = "not available" if capability is None else capability.reason or "not available"
            reason = reason.removesuffix(".")
            self.encoder_note.setText(
                ascii_text(f"{name} is unavailable: {reason}. Choose another encoder.")
            )
        elif failure is not None:
            self.encoder_note.setText(ascii_text(f"Encoders could not be detected: {failure}"))
        else:
            self.encoder_note.setText("")
        self.encoder_combo.setToolTip(self.encoder_note.text())

    def _on_encoder_changed(self, _index: int) -> None:
        """The user chose an encoder: refresh its note, the 10-bit rule and OK."""
        self._update_encoder_note()
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

    def _encoder_unacceptable(self, name: str | None = None) -> bool:
        """Return whether the encoder to apply is refused by the capability rules.

        Selected | Sink report              | Stored?          | OK
        auto     | any                      | any              | allowed
        any      | still being read         | any              | allowed; re-evaluate on arrival
        a name   | reported, unavailable    | stored or picked | refused
        a name   | reported, available      | any              | allowed
        a name   | absent, or report failed | stored           | allowed (Q3)
        a name   | not reported             | picked           | refused

        While detection runs the encoder control is disabled. A name stored in
        the current session but missing from the report is preserved; a reported
        unavailable name is refused.

        Args:
            name: The encoder to apply, or None to read the edited settings.
        """
        if name is None:
            name = self.edited_settings().video_encoder
        if name == AUTO or self._catalog.detecting():
            return False
        capability = next((c for c in self._catalog.capabilities() if c.name == name), None)
        if capability is None:
            return name != self._context.session.settings().video_encoder
        return not capability.available

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
        self.ok_button.setDefault(self.ok_button.isEnabled())

    def _show_folder(self) -> None:
        """Show the output folder (D34)."""
        self.folder_label.setText(SAME_FOLDER_TEXT if self._folder is None else str(self._folder))

    def _on_choose_folder(self) -> None:
        """Ask for a folder; preserve it on cancellation or a reported chooser failure."""
        try:
            chosen = self._choosers.choose_folder(self._folder)
        except Exception as error:  # choosers are foreign injected code
            detail = _detail(error)
            self._error(f"The output folder could not be chosen: {detail}")
            return
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
        """Confirm safely, check again that no analysis runs, then clear in a job."""
        if self._clearing or self._analysing():
            return
        try:
            confirmed = self._choosers.confirm(
                "Remove every cached proxy and statistic? Clips are analysed again when needed."
            )
        except Exception as error:  # choosers are foreign injected code
            self._error(
                f"The cache was not cleared: the confirmation failed: {_detail(error)}",
            )
            self._update_clear_button()
            return
        if not confirmed:
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
            self._error(f"The cache could not be cleared: {_detail(error)}")
            self._update_clear_button()

    def _on_clear_done(self, result: JobResult) -> None:
        """Main thread: the clear job ended."""
        if not result.ok:
            self._cache_job_error(f"The cache could not be cleared: {result.failure}")
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
            reason = ascii_text(str(error))
            self.suffix_error.setText(reason)
            self.suffix_edit.setToolTip(reason)
            self._refresh_ok()
            detail = reason[:200]
            self._error(f"The output suffix is not valid: {detail}")
            return
        if self._encoder_unacceptable(new.video_encoder):
            self._update_encoder_note(new.video_encoder)
            self._refresh_ok()
            self._error(self.encoder_note.text())
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
            self._error(
                f"The settings could not be saved to {file_name(path)}: {_detail(error)}",
                path,
            )
        else:
            context.messages.clear(owner=OWNER_SETTINGS)
            self._shown_errors.clear()

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
                self._cache_job_error(f"The cache limit could not be set: {result.failure}")

        try:
            context.jobs.run(job, on_done=done)
        except RuntimeError as error:  # the job runner is closed: the window is shutting down
            self._error(f"The cache limit could not be set: {_detail(error)}")

    def _on_finished(self, _result: int) -> None:
        """The dialog closed: stop listening and let Qt delete it."""
        self._closed = True
        for signal, slot in (
            (self._context.session.analysis_changed, self._update_clear_button),
            (self._context.session.settings_changed, self._on_session_settings),
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
    window_closing: Callable[[], bool] | None = None,
) -> SettingsDialog:
    """Build a new settings dialog on the session's current settings.

    Args:
        context: The shell context.
        choosers: The folder chooser and confirmation; the Qt ones when None.
        resolve_encoder: The one "auto" rule; WP3.10's
            ``clearwater.io.video.capability.resolve_encoder`` when None.
        catalog: The session's encoder capabilities, shared between dialogs; a new one for this
            dialog when None.
        cache_limiter: The session's cache-limit serialiser, shared between dialogs so that the
            last accepted limit wins; a new one for this dialog when None.
        window_closing: True once the main window is closing (R2-3); never when None.

    Returns:
        The dialog; the shell opens it with ``QDialog.open()``.
    """
    return SettingsDialog(
        context,
        choosers or QtChoosers(context.window),
        resolve_encoder or wp310_resolve_encoder,
        catalog or EncoderCatalog(context.window),
        cache_limiter or CacheLimiter(),
        window_closing,
    )


def install_settings_dialog(
    window: ShellWindow,
    *,
    choosers: SettingsChoosers | None = None,
    resolve_encoder: EncoderResolver | None = None,
    catalog: EncoderCatalog | None = None,
    window_closing: Callable[[], bool] | None = None,
) -> None:
    """Register the settings dialog with the window (Tools > Settings).

    The encoder capabilities are read once and shared by every dialog: by the first dialog that
    opens, or earlier when the caller starts ``catalog`` itself (the application's start-up
    detection, DR-52); so is the serialiser of the cache-limit calls.

    Args:
        window: The main window.
        choosers: The folder chooser and confirmation; the Qt ones when None.
        resolve_encoder: The one "auto" rule; WP3.10's
            ``clearwater.io.video.capability.resolve_encoder`` when None.
        catalog: The session's encoder capabilities (the start-up's); a new one when None.
        window_closing: True once the main window is closing: a clear or limit job's error is
            then logged, not presented (R2-3; the application's ``Application.closed``). Never
            closing when None.
    """
    catalog = catalog if catalog is not None else EncoderCatalog(window)
    cache_limiter = CacheLimiter()

    def factory(context: ShellContext) -> SettingsDialog:
        return settings_dialog(
            context,
            choosers=choosers,
            resolve_encoder=resolve_encoder,
            catalog=catalog,
            cache_limiter=cache_limiter,
            window_closing=window_closing,
        )

    window.set_settings_dialog(factory)
