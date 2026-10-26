"""The Presets panel (WP3.17, G6, D37, D38, D90).

A list of the presets in the user's preset folder and the six operations of G6: load, save as,
rename, delete, import from a file and export to a file, all through
:class:`~clearwater.config.PresetStore`. The panel decides nothing the store decides: it asks for
a name or a file through the injectable :class:`PresetDialogs` (so a test never blocks on a modal
dialog), asks the user to confirm before anything is replaced or deleted, and turns every store
failure into an error message with the owner :data:`OWNER_PRESETS`. A preset is applied to the
session only after its method is known and :func:`~clearwater.interfaces.validate_parameter_set`
finds no problem with it. The panel never saves the settings.
"""

from __future__ import annotations

import os
import unicodedata
from collections.abc import Callable
from pathlib import Path
from typing import Protocol, TypeVar

from PySide6.QtCore import Qt
from PySide6.QtGui import QShowEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from clearwater.config import PresetError, validate_preset_name
from clearwater.interfaces import FormatError, validate_parameter_set

from .contract import Message, ShellContext
from .messages import ascii_text, file_name

OWNER_PRESETS = "presets"
"""The :attr:`Message.owner` of every message this panel presents."""

_FILTER = "Preset files (*.json)"
_T = TypeVar("_T")
_FAILURES = (PresetError, FormatError, OSError, ValueError)
"""What a store call or a session call may raise; every one becomes an error message."""


class PresetDialogs(Protocol):
    """The questions the panel asks the user; a test passes a scripted fake."""

    def ask_name(self, title: str, initial: str) -> str | None:
        """Ask for a preset name.

        Args:
            title: The dialog title.
            initial: The name offered first.

        Returns:
            The name, or None when the user cancelled.
        """
        ...

    def confirm(self, text: str) -> bool:
        """Ask a yes-or-no question (the answer to offer first is no).

        Args:
            text: The question.

        Returns:
            True when the user said yes.
        """
        ...

    def open_file(self) -> Path | None:
        """Ask for a preset file to import (``*.json``).

        Returns:
            The file, or None when the user cancelled.
        """
        ...

    def save_file(self, initial_name: str) -> Path | None:
        """Ask for the file to export to.

        Args:
            initial_name: The file name offered first.

        Returns:
            The file (it may exist: the panel asks before replacing it), or None on cancel.
        """
        ...


class QtPresetDialogs:
    """The Qt implementation of :class:`PresetDialogs`, parented to the main window."""

    def __init__(self, parent: QWidget | None) -> None:
        """Create the dialogs.

        Args:
            parent: The window the dialogs belong to.
        """
        self._parent = parent

    def ask_name(self, title: str, initial: str) -> str | None:
        """Ask for a name with an input dialog."""
        text, accepted = QInputDialog.getText(self._parent, title, "Preset name:", text=initial)
        return text if accepted else None

    def confirm(self, text: str) -> bool:
        """Ask with a message box whose default answer is No."""
        answer = QMessageBox.question(
            self._parent,
            "Clearwater",
            text,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        return answer == QMessageBox.StandardButton.Yes

    def open_file(self) -> Path | None:
        """Ask for a ``*.json`` file to import."""
        chosen, _ = QFileDialog.getOpenFileName(self._parent, "Import preset", "", _FILTER)
        return Path(chosen) if chosen else None

    def save_file(self, initial_name: str) -> Path | None:
        """Ask for the export file; ``.json`` is added when the name has no suffix."""
        chosen, _ = QFileDialog.getSaveFileName(
            self._parent,
            "Export preset",
            initial_name,
            _FILTER,
            options=QFileDialog.Option.DontConfirmOverwrite,
        )
        if not chosen:
            return None
        path = Path(chosen)
        return path if path.suffix else path.with_name(path.name + ".json")


def _name_key(name: str) -> str:
    """Return the key under which the store counts two names as the same preset."""
    return unicodedata.normalize("NFC", name).casefold()


class PresetPanel(QWidget):
    """The Presets panel: the list and its buttons.

    Attributes:
        list: The preset list (an unreadable preset is a disabled item).
        status: The label under the list holding the text of the last success.
        buttons: The buttons by name: ``"load"``, ``"save"``, ``"rename"``, ``"delete"``,
            ``"import"``, ``"export"``.
    """

    def __init__(self, context: ShellContext, dialogs: PresetDialogs) -> None:
        """Create the panel and fill the list.

        Args:
            context: The shell context.
            dialogs: The questions to ask the user.
        """
        super().__init__()
        self._context = context
        self._session = context.session
        self._store = context.presets
        self._dialogs = dialogs
        self.list = QListWidget()
        self.status = QLabel("")
        self.status.setWordWrap(True)
        layout = QVBoxLayout(self)
        layout.addWidget(self.list, 1)
        layout.addWidget(self.status)
        self.buttons: dict[str, QPushButton] = {}
        rows = (QHBoxLayout(), QHBoxLayout())
        for row in rows:
            layout.addLayout(row)
        actions: tuple[tuple[str, str, Callable[[], None]], ...] = (
            ("load", "Load", self.load),
            ("save", "Save as...", self.save_as),
            ("rename", "Rename...", self.rename),
            ("delete", "Delete", self.delete),
            ("import", "Import...", self.import_file),
            ("export", "Export...", self.export),
        )
        for index, (key, text, slot) in enumerate(actions):
            button = QPushButton(text)
            button.clicked.connect(lambda _checked=False, slot=slot: slot())
            self.buttons[key] = button
            rows[index // 3].addWidget(button)
        self.list.itemSelectionChanged.connect(self._update_buttons)
        self.refresh()

    # The list.

    def refresh(self) -> None:
        """List the presets again, keeping the selection when its preset is still there."""
        keep = self.selected()
        self.list.clear()
        try:
            entries = self._store.list_presets()
        except OSError as error:
            self._fail("Cannot list the presets", error)
            entries = []
        for entry in entries:
            item = QListWidgetItem(entry.name)
            item.setData(Qt.ItemDataRole.UserRole, entry.name)
            if entry.error is not None or entry.parameter_set is None:
                item.setFlags(
                    item.flags() & ~(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsSelectable)
                )
                item.setToolTip(
                    "Made by a newer Clearwater and left untouched."
                    if entry.unsupported_version
                    else ascii_text(entry.error or "Unreadable.")
                )
            else:
                item.setToolTip(f"Method: {entry.parameter_set.method}")
            self.list.addItem(item)
            if entry.name == keep and item.flags() & Qt.ItemFlag.ItemIsSelectable:
                self.list.setCurrentItem(item)
        self._update_buttons()

    def selected(self) -> str | None:
        """Return the name of the selected (readable) preset, or None."""
        item = self.list.currentItem()
        if item is None or not item.isSelected():
            return None
        name = item.data(Qt.ItemDataRole.UserRole)
        return name if isinstance(name, str) else None

    def select(self, name: str) -> None:
        """Select the preset called ``name`` when it is listed and readable."""
        for index in range(self.list.count()):
            item = self.list.item(index)
            if item.data(Qt.ItemDataRole.UserRole) == name and (
                item.flags() & Qt.ItemFlag.ItemIsSelectable
            ):
                self.list.setCurrentItem(item)
                return

    def _update_buttons(self) -> None:
        """Enable the buttons that act on a preset only while one is selected."""
        has = self.selected() is not None
        for key in ("load", "rename", "delete", "export"):
            self.buttons[key].setEnabled(has)

    def showEvent(self, event: QShowEvent) -> None:  # noqa: N802  (Qt override)
        """List the presets again whenever the panel is shown."""
        self.refresh()
        super().showEvent(event)

    # Messages.

    def _fail(self, what: str, error: BaseException, path: Path | None = None) -> None:
        """Present ``error`` as an error message of this panel."""
        text = ascii_text(f"{what}: {error}")
        self._context.messages.present(Message("error", text, path, owner=OWNER_PRESETS))

    def _succeed(self, text: str) -> None:
        """Clear this panel's earlier messages and show ``text`` under the list."""
        self._context.messages.clear("error", owner=OWNER_PRESETS)
        self._context.messages.clear("warning", owner=OWNER_PRESETS)
        self.status.setText(ascii_text(text))

    def _attempt(
        self, action: Callable[[], _T], what: str, path: Path | None = None
    ) -> tuple[bool, _T | None]:
        """Run ``action``; a failure becomes an error message and ``(False, None)``."""
        try:
            return True, action()
        except _FAILURES as error:
            self._fail(what, error, path)
            return False, None

    # The six operations.

    def load(self) -> None:
        """Apply the selected preset to the session, after checking it against its method."""
        name = self.selected()
        if name is None:
            return

        def action() -> None:
            parameter_set = self._store.load(name)
            method = self._context.engines.methods.get(parameter_set.method)
            if method is None:
                known = ", ".join(self._context.engines.methods) or "none"
                raise PresetError(
                    f"it is for method {parameter_set.method!r}, which is not available "
                    f"(available: {known})"
                )
            problems = validate_parameter_set(
                parameter_set, parameter_set.method, method.parameters
            )
            if problems:
                raise PresetError(
                    f"it does not match method {method.id!r}: "
                    + "; ".join(problem.message for problem in problems)
                )
            self._session.set_parameters(parameter_set)

        ok, _ = self._attempt(action, f"Cannot load preset {name!r}")
        if ok:
            self._succeed(f"Loaded {name!r}.")

    def save_as(self) -> None:
        """Save the session's parameters as a preset, asking before replacing one."""
        name = self._dialogs.ask_name("Save preset", self.selected() or "")
        if name is None:
            return
        what = "Cannot save the preset"

        def exists() -> bool:
            validate_preset_name(name)
            key = _name_key(name)
            return any(
                _name_key(entry.name) == key and entry.error is None
                for entry in self._store.list_presets()
            )

        ok, replaces = self._attempt(exists, what)
        if not ok:
            return
        if replaces and not self._dialogs.confirm(
            f"A preset named {name!r} already exists. Replace it?"
        ):
            return
        saved, _ = self._attempt(
            lambda: self._store.save(name, self._session.parameters(), overwrite=bool(replaces)),
            what,
        )
        self.refresh()
        if saved:
            self.select(name)
            self._succeed(f"Saved {name!r}.")

    def rename(self) -> None:
        """Rename the selected preset."""
        old = self.selected()
        if old is None:
            return
        new = self._dialogs.ask_name("Rename preset", old)
        if new is None or new == old:
            return
        ok, _ = self._attempt(lambda: self._store.rename(old, new), f"Cannot rename {old!r}")
        self.refresh()
        if ok:
            self.select(new)
            self._succeed(f"Renamed {old!r} to {new!r}.")

    def delete(self) -> None:
        """Delete the selected preset after the user confirmed."""
        name = self.selected()
        if name is None or not self._dialogs.confirm(f"Delete preset {name!r}?"):
            return
        ok, _ = self._attempt(lambda: self._store.delete(name), f"Cannot delete {name!r}")
        self.refresh()
        if ok:
            self._succeed(f"Deleted {name!r}.")

    def import_file(self) -> None:
        """Import a preset file, checked against the schemas of the available methods."""
        path = self._dialogs.open_file()
        if path is None:
            return
        schemas = {
            method_id: method.parameters
            for method_id, method in self._context.engines.methods.items()
        }
        ok, result = self._attempt(
            lambda: self._store.import_preset(path, schemas),
            f"Cannot import {file_name(path)}",
            path,
        )
        self.refresh()
        if not ok or result is None:
            return
        self.select(result.name)
        if result.name == path.stem:
            self._succeed(f"Imported {result.name!r}.")
        else:
            self._succeed(f"Imported as {result.name!r}.")
        if result.provenance_dropped:
            keys = ", ".join(result.dropped_keys)
            self._context.messages.present(
                Message(
                    "warning",
                    ascii_text(
                        f"{file_name(path)} carried provenance ({keys}); it was not kept in "
                        f"the preset {result.name!r}."
                    ),
                    path,
                    owner=OWNER_PRESETS,
                )
            )

    def export(self) -> None:
        """Export the selected preset to a file, asking before replacing one."""
        name = self.selected()
        if name is None:
            return
        target = self._dialogs.save_file(f"{name}.json")
        if target is None:
            return
        replaces = os.path.lexists(target)
        if replaces and not self._dialogs.confirm(
            f"{file_name(target)} already exists. Replace it?"
        ):
            return
        ok, _ = self._attempt(
            lambda: self._store.export_preset(name, target, overwrite=replaces),
            f"Cannot export {name!r}",
            target,
        )
        if ok:
            self._succeed(f"Exported {name!r} to {file_name(target)}.")


def preset_panel(context: ShellContext, *, dialogs: PresetDialogs | None = None) -> QWidget:
    """Build the Presets panel (a :data:`~clearwater.gui.contract.PanelFactory`).

    Args:
        context: The shell context.
        dialogs: The questions to ask the user; the Qt dialogs parented to the window when None.

    Returns:
        The :class:`PresetPanel`.
    """
    return PresetPanel(context, dialogs if dialogs is not None else QtPresetDialogs(context.window))
