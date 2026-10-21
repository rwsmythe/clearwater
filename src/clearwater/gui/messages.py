"""G10 messages: what is said for unsupported, damaged or untagged inputs, and how it is shown.

The classification (question 10, round-0 table section 6): a refusal (the file is not opened and
the previous source stays) is a modal message naming the file; a warning (the file is open and
the user is told) is a non-modal banner above the preview while the file stays open; an error
(an action failed) is a banner. The text builders here are pure and run on the loader worker;
:class:`DialogPresenter` and :class:`BannerWidget` are main-thread widgets. Texts are ASCII-safe
(file names are backslash-escaped) for the Windows console and the log.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from pathlib import Path

from PySide6.QtWidgets import QLabel, QMessageBox, QVBoxLayout, QWidget

from clearwater.interfaces import Fault

from .contract import Message, MessageSeverity

_LOG = logging.getLogger(__name__)

PHOTO_READ_ERROR_KINDS = frozenset({"unsupported", "unreadable"})
"""The ``kind`` values of WP3.6's photo read error (X-B2) that are shown with their own text."""


def ascii_text(text: str) -> str:
    """Return ``text`` with every non-ASCII character backslash-escaped.

    Args:
        text: Any text.

    Returns:
        ASCII-only text; ASCII input unchanged.
    """
    return text.encode("ascii", "backslashreplace").decode("ascii")


def file_name(path: Path) -> str:
    """Return the ASCII-safe file name of ``path``.

    Args:
        path: The file.

    Returns:
        The escaped name.
    """
    return ascii_text(path.name)


def refusal(path: Path, text: str) -> Message:
    """Build a refusal for ``path``.

    Args:
        path: The refused file.
        text: The message text.

    Returns:
        The message, ASCII-safe.
    """
    return Message("refusal", ascii_text(text), path)


def warning(path: Path, text: str) -> Message:
    """Build a warning for ``path``.

    Args:
        path: The open file.
        text: The message text.

    Returns:
        The message, ASCII-safe.
    """
    return Message("warning", ascii_text(text), path)


def unsupported_extension(path: Path) -> Message:
    """The refusal for a file whose extension is neither a photo's nor a video's (G1, G10).

    Args:
        path: The file.

    Returns:
        The refusal.
    """
    return refusal(path, f"{file_name(path)} is not a supported photo or video file.")


def photo_read_failure(path: Path, error: BaseException) -> Message:
    """The refusal for a photo the reader could not read (spec 5.1, 5.4, D116).

    WP3.6's read error (X-B2) carries ``kind`` ``unsupported`` (DNG and ProRAW included) or
    ``unreadable`` and a user-readable message, shown as it is; it is recognised by that
    attribute until the class can be imported by name (round-0 ruling S2). Any other exception
    is shown as unreadable with its text.

    Args:
        path: The photo.
        error: What the reader raised.

    Returns:
        The refusal.
    """
    if getattr(error, "kind", None) in PHOTO_READ_ERROR_KINDS and str(error):
        return refusal(path, str(error))
    detail = str(error) or type(error).__name__
    return refusal(path, f"{file_name(path)} could not be read: {detail}")


def fault_messages(path: Path, faults: Iterable[Fault]) -> tuple[list[Message], list[Message]]:
    """Split a probe's faults into refusals and warnings (spec 5.3, 5.4, D54, D83, D86).

    Args:
        path: The probed file.
        faults: ``ProbeResult.faults``.

    Returns:
        ``(refusals, warnings)``: ``refuse`` and ``exclude`` faults refuse the file; ``warn``
        faults warn.
    """
    refusals: list[Message] = []
    warnings: list[Message] = []
    for fault in faults:
        if fault.severity == "warn":
            warnings.append(warning(path, fault.message))
        else:
            refusals.append(refusal(path, fault.message))
    return refusals, warnings


def no_frame(path: Path) -> Message:
    """The refusal for a probed video from which no frame could be decoded (spec 5.4).

    Args:
        path: The video.

    Returns:
        The refusal.
    """
    return refusal(path, f"{file_name(path)}: no frame could be read.")


def assumed_colour(path: Path, kind: str) -> Message:
    """The warning for a source without a colour description (spec 6.5, D54).

    Args:
        path: The open file.
        kind: ``"photo"`` or ``"video"``.

    Returns:
        The warning.
    """
    if kind == "photo":
        text = f"{file_name(path)} has no colour description; sRGB is assumed."
    else:
        text = f"{file_name(path)} has no colour tags; BT.709 limited range is assumed."
    return warning(path, text)


def preview_failure(error: BaseException) -> Message:
    """The error banner for a preview render that raised (brief task 6).

    Args:
        error: The exception.

    Returns:
        The error; the last good preview stays on screen.
    """
    return Message("error", ascii_text(f"Preview failed: {type(error).__name__}: {error}"))


def frame_failure(error: BaseException) -> Message:
    """The error banner for a frame that could not be decoded at a position.

    Args:
        error: The exception.

    Returns:
        The error.
    """
    return Message("error", ascii_text(f"The frame could not be read: {error}"))


class BannerWidget(QWidget):
    """The non-modal message area above the preview (warnings and errors)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create an empty, hidden banner.

        Args:
            parent: The Qt parent.
        """
        super().__init__(parent)
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(4, 2, 4, 2)
        self._labels: list[tuple[MessageSeverity, QLabel]] = []
        self.setVisible(False)

    def add(self, message: Message) -> None:
        """Show a message.

        Args:
            message: A warning or an error.
        """
        label = QLabel(message.text, self)
        label.setWordWrap(True)
        colour = "#7a5a00" if message.severity == "warning" else "#8b0000"
        label.setStyleSheet(f"color: {colour};")
        self._layout.addWidget(label)
        self._labels.append((message.severity, label))
        self.setVisible(True)

    def clear(self, severity: MessageSeverity | None = None) -> None:
        """Remove messages.

        Args:
            severity: Only messages of this severity, or None for all.
        """
        kept: list[tuple[MessageSeverity, QLabel]] = []
        for kind, label in self._labels:
            if severity is None or kind == severity:
                self._layout.removeWidget(label)
                label.deleteLater()
            else:
                kept.append((kind, label))
        self._labels = kept
        self.setVisible(bool(kept))

    def texts(self) -> list[str]:
        """Return the texts shown, in order."""
        return [label.text() for _, label in self._labels]


class DialogPresenter:
    """The product presenter: refusals in a window-modal message box, the rest in the banner.

    Implements ``clearwater.gui.contract.MessagePresenter``. The message box is opened with
    ``open()`` (window-modal, never a blocking ``exec``), so the event loop keeps running.

    Args:
        parent: The window the message box belongs to.
        banner: The banner above the preview.
    """

    def __init__(self, parent: QWidget, banner: BannerWidget) -> None:
        """Create the presenter."""
        self._parent = parent
        self._banner = banner
        self._boxes: list[QMessageBox] = []

    def present(self, message: Message) -> None:
        """Show a message and log it.

        Args:
            message: The message.
        """
        _LOG.info("%s: %s", message.severity, message.text)
        if message.severity != "refusal":
            self._banner.add(message)
            return
        box = QMessageBox(self._parent)
        box.setIcon(QMessageBox.Icon.Warning)
        box.setWindowTitle("Clearwater")
        box.setText(message.text)
        box.finished.connect(lambda _code, b=box: self._closed(b))
        self._boxes.append(box)
        box.open()

    def clear(self, severity: MessageSeverity | None = None) -> None:
        """Remove banner messages.

        Args:
            severity: Only messages of this severity, or None for all.
        """
        self._banner.clear(severity)

    def _closed(self, box: QMessageBox) -> None:
        """Forget a closed message box."""
        if box in self._boxes:
            self._boxes.remove(box)
        box.deleteLater()
