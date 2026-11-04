"""The split-view preview (G2, D27, D41, 6.6) and its controller (G9, D108).

:class:`PreviewWidget` paints one view split by a draggable vertical divider: the original on
the left, the corrected image on the right, both from the same downscaled input. Zoom is fit,
steps, or 1:1 (one image pixel per device pixel, ``devicePixelRatio`` honoured); a drag away from
the divider pans. :class:`PreviewController` implements the contract's ``PreviewSurface``: it
turns session changes into latest-wins render requests on the preview worker and decodes video
frames on the frame worker, so nothing heavy runs on the interface thread.

WP4.3: the preview worker's FFT plans are released on its own thread at each preview boundary
(a source change, the shell's close, and :meth:`PreviewController.release_device_plans` before a
job of the GUI process selects its backend; DR-68), and a photo with no ICC profile but a tagged
colour description is displayed through the D53 built-in profile the writer embeds (DR-75).
"""

from __future__ import annotations

import logging
import math
import threading
import time
from collections.abc import Callable, Mapping

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import QObject, QPointF, QRectF, Qt, Signal
from PySide6.QtGui import (
    QColor,
    QImage,
    QMouseEvent,
    QPainter,
    QPaintEvent,
    QPen,
    QResizeEvent,
    QWheelEvent,
)
from PySide6.QtWidgets import QWidget

from clearwater.interfaces import Frame, Image, Statistics
from clearwater.io.photo.writer import built_in_profile

from . import messages, sources
from .contract import Engines, FrameOutcome, Message, MessagePresenter, OpenedSource
from .imaging import display_image, effective_parameters, view_factor
from .render_worker import (
    LatestWorker,
    Outcome,
    PreviewDeviceBackend,
    PreviewMemo,
    RenderError,
    RenderRequest,
    RenderResult,
    render_preview,
)
from .session import ShellSession

_LOG = logging.getLogger(__name__)

ZOOM_STEPS: tuple[float, ...] = (1 / 16, 1 / 8, 1 / 4, 1 / 3, 1 / 2, 2 / 3, 1.0, 2.0, 4.0, 8.0)
"""The zoom steps, in device pixels per image pixel (1.0 is 1:1)."""

_DIVIDER_GRAB_PX = 6
_BACKGROUND = QColor(32, 32, 32)


def display_profile(source: OpenedSource | None) -> bytes | None:
    """Return the ICC profile a source's display copies are tagged with (DR-75, D53).

    The source's own profile when it has one; for a photo without one, the built-in profile the
    writer embeds for its colour description (``built_in_profile``, the writer's own choice: a
    tagged HEIC with BT.709 or Display P3 primaries and the sRGB curve); else None (an untagged
    photo, a video frame), so the display is unchanged.

    Args:
        source: The open source, or None.

    Returns:
        The profile's bytes, or None.
    """
    if source is None:
        return None
    color = source.image.color
    if color.icc_profile is not None or source.metadata is None:
        return color.icc_profile
    chosen = built_in_profile(color, source.metadata.source_format)
    return None if chosen is None else chosen[1]


WHEEL_STEP_UNITS = 120
"""``angleDelta`` units per zoom step: one mouse-wheel notch (Qt's eighths of a degree x 15)."""


class PreviewWidget(QWidget):
    """The split view. Main thread only; it paints ``QImage`` results it is given.

    Signals:
        view_changed(): the zoom or the widget size changed (the needed factor may differ).
    """

    view_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        """Create an empty preview.

        Args:
            parent: The Qt parent.
        """
        super().__init__(parent)
        self.setMinimumSize(160, 120)
        self.setMouseTracking(True)
        self._size: tuple[int, int] | None = None
        self._before: QImage | None = None
        self._after: QImage | None = None
        self._k = 1.0
        self._split = 0.5
        self._zoom: float | None = None
        self._center = (0.0, 0.0)
        self._pending_full = False
        self._drag: str | None = None
        self._drag_from = QPointF()
        self._drag_center = (0.0, 0.0)
        self._wheel_units = 0

    # State.

    def set_source_size(self, height: int, width: int, *, reset: bool) -> None:
        """Set the full-resolution size of the image shown.

        Args:
            height: Height in pixels.
            width: Width in pixels.
            reset: Return to fit and the centre (a new source).
        """
        changed = self._size != (height, width)
        self._size = (height, width)
        if reset or changed:
            self._zoom = None
            self._center = (width / 2, height / 2)
            self._before = self._after = None
            self._pending_full = False
        self.update()
        self.view_changed.emit()

    def clear(self) -> None:
        """Show nothing."""
        self._size = None
        self._before = self._after = None
        self._pending_full = False
        self.update()

    def set_result(self, before: QImage, after: QImage, k: int) -> None:
        """Show a rendered pair at downscale factor ``k``.

        Args:
            before: The original at that factor.
            after: The corrected image at that factor.
            k: The factor (1 = full resolution).
        """
        self._before, self._after = before, after
        self._k = self._image_scale(after, float(k))
        if k == 1:
            self._pending_full = False
        self.update()

    def set_proxy(self, before: QImage, after: QImage) -> None:
        """Show a scrub proxy pair, scaled to the full-resolution geometry (D72).

        Args:
            before: The original proxy.
            after: The corrected proxy, or the same as ``before``.
        """
        self._before, self._after = before, after
        self._k = self._image_scale(after, 1.0)
        self._pending_full = False  # the proxy supersedes any full render on its way
        self.update()

    def set_pending_full(self, pending: bool) -> None:
        """Show or hide the "Rendering full resolution" indicator (question 6).

        Args:
            pending: True while a full-resolution render for 1:1 is on its way.
        """
        self._pending_full = pending
        self.update()

    def pending_full(self) -> bool:
        """Return True while the full-resolution indicator is shown."""
        return self._pending_full

    def shown_factor(self) -> float:
        """Return the factor of the images shown (full-resolution pixels per image pixel)."""
        return self._k

    def after_image(self) -> QImage | None:
        """Return the corrected image shown, or None."""
        return self._after

    def before_image(self) -> QImage | None:
        """Return the original image shown, or None."""
        return self._before

    def _image_scale(self, image: QImage, fallback: float) -> float:
        """Full-resolution pixels per pixel of ``image``."""
        if self._size is None or image.width() <= 0:
            return fallback
        return self._size[1] / image.width()

    # Zoom, pan and split.

    def scale(self) -> float:
        """Return the zoom in device pixels per full-resolution image pixel."""
        if self._zoom is not None:
            return self._zoom
        if self._size is None:
            return 1.0
        dpr = self.devicePixelRatioF()
        height, width = self._size
        return min(self.width() * dpr / width, self.height() * dpr / height)

    def is_fit(self) -> bool:
        """Return True in fit mode."""
        return self._zoom is None

    def needed_factor(self) -> int:
        """Return the downscale factor the current zoom needs (question 7)."""
        if self._size is None:
            return 1
        height, width = self._size
        s = self.scale()
        if s >= 1.0:
            return 1
        return view_factor(height, width, height * s, width * s)

    def zoom_text(self) -> str:
        """Return the zoom for the status bar, for example ``"Fit (23%)"`` or ``"100%"``."""
        percent = f"{self.scale() * 100:.0f}%"
        return f"Fit ({percent})" if self._zoom is None else percent

    def fit(self) -> None:
        """Fit the whole image in the view."""
        self._set_zoom(None)

    def one_to_one(self) -> None:
        """Show one image pixel per device pixel (1:1)."""
        self._set_zoom(1.0)

    def zoom_in(self) -> None:
        """Go to the next larger zoom step."""
        s = self.scale()
        larger = [z for z in ZOOM_STEPS if z > s * 1.0001]
        self._set_zoom(larger[0] if larger else ZOOM_STEPS[-1])

    def zoom_out(self) -> None:
        """Go to the next smaller zoom step."""
        s = self.scale()
        smaller = [z for z in ZOOM_STEPS if z < s / 1.0001]
        self._set_zoom(smaller[-1] if smaller else ZOOM_STEPS[0])

    def reset_split(self) -> None:
        """Put the divider back in the middle."""
        self.set_split(0.5)

    def set_split(self, fraction: float) -> None:
        """Place the divider.

        Args:
            fraction: Its position across the view, 0 (all corrected) to 1 (all original).
        """
        self._split = min(1.0, max(0.0, fraction))
        self.update()

    def split(self) -> float:
        """Return the divider position across the view, 0 to 1."""
        return self._split

    def divider_x(self) -> float:
        """Return the divider position in logical pixels."""
        return self._split * self.width()

    def _set_zoom(self, zoom: float | None) -> None:
        """Set the zoom mode and tell the controller."""
        self._zoom = zoom
        self._clamp_center()
        self.update()
        self.view_changed.emit()

    def _clamp_center(self) -> None:
        """Keep the view centre inside the image."""
        if self._size is None:
            return
        height, width = self._size
        cx, cy = self._center
        self._center = (min(max(cx, 0.0), float(width)), min(max(cy, 0.0), float(height)))

    def image_origin(self) -> tuple[float, float]:
        """Return the image's top-left corner in device pixels (whole pixels at 1:1)."""
        assert self._size is not None
        height, width = self._size
        dpr = self.devicePixelRatioF()
        s = self.scale()
        view_w, view_h = self.width() * dpr, self.height() * dpr
        shown_w, shown_h = width * s, height * s
        cx, cy = self._center
        ox = (view_w - shown_w) / 2 if shown_w <= view_w else view_w / 2 - cx * s
        oy = (view_h - shown_h) / 2 if shown_h <= view_h else view_h / 2 - cy * s
        if shown_w > view_w:
            ox = min(0.0, max(view_w - shown_w, ox))
        if shown_h > view_h:
            oy = min(0.0, max(view_h - shown_h, oy))
        return float(math.floor(ox)), float(math.floor(oy))

    # Qt events.

    def paintEvent(self, event: QPaintEvent) -> None:  # noqa: N802 -- Qt override
        """Paint the original left of the divider and the corrected image right of it."""
        painter = QPainter(self)
        painter.fillRect(self.rect(), _BACKGROUND)
        if self._size is None or self._before is None or self._after is None:
            painter.setPen(QColor(200, 200, 200))
            text = "Open a photo or video" if self._size is None else "Rendering..."
            painter.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, text)
            painter.end()
            return
        dpr = self.devicePixelRatioF()
        height, width = self._size
        s = self.scale()
        ox, oy = self.image_origin()
        target = QRectF(ox / dpr, oy / dpr, width * s / dpr, height * s / dpr)
        divider = self.divider_x()
        sides = (
            (self._before, QRectF(0, 0, divider, self.height())),
            (self._after, QRectF(divider, 0, self.width() - divider, self.height())),
        )
        for image, clip in sides:
            painter.save()
            painter.setClipRect(clip)
            self._draw(painter, image, target, s, dpr)
            painter.restore()
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.drawLine(QPointF(divider, 0), QPointF(divider, self.height()))
        if self._pending_full:
            painter.setPen(QColor(255, 255, 0))
            painter.drawText(
                self.rect().adjusted(8, 8, -8, -8),
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom,
                "Rendering full resolution",
            )
        painter.end()

    def _draw(self, painter: QPainter, image: QImage, target: QRectF, s: float, dpr: float) -> None:
        """Draw one side; a full-resolution image at 1:1 is drawn pixel for pixel."""
        if image.width() == (self._size or (0, 0))[1] and s == 1.0:
            exact = QImage(image)
            exact.setDevicePixelRatio(dpr)
            painter.drawImage(target.topLeft(), exact)
            return
        upscaling = s * self._k > 1.0
        painter.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, not upscaling)
        painter.drawImage(target, image, QRectF(image.rect()))

    def resizeEvent(self, event: QResizeEvent) -> None:  # noqa: N802 -- Qt override
        """Tell the controller: in fit mode the needed factor follows the size."""
        super().resizeEvent(event)
        self.view_changed.emit()

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 -- Qt override
        """Start dragging the divider (near it) or panning (elsewhere)."""
        if event.button() != Qt.MouseButton.LeftButton:
            return
        x = event.position().x()
        self._drag = "split" if abs(x - self.divider_x()) <= _DIVIDER_GRAB_PX else "pan"
        self._drag_from = event.position()
        self._drag_center = self._center

    def mouseMoveEvent(self, event: QMouseEvent) -> None:  # noqa: N802 -- Qt override
        """Move the divider or pan."""
        x = event.position().x()
        near = abs(x - self.divider_x()) <= _DIVIDER_GRAB_PX
        cursor = (
            Qt.CursorShape.SplitHCursor
            if near or self._drag == "split"
            else Qt.CursorShape.ArrowCursor
        )
        self.setCursor(cursor)
        if self._drag == "split" and self.width() > 0:
            self.set_split(x / self.width())
        elif self._drag == "pan" and self._size is not None:
            s = self.scale() / self.devicePixelRatioF()
            delta = event.position() - self._drag_from
            cx, cy = self._drag_center
            self._center = (cx - delta.x() / s, cy - delta.y() / s)
            self._clamp_center()
            self.update()

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:  # noqa: N802 -- Qt override
        """End a drag."""
        self._drag = None

    def wheelEvent(self, event: QWheelEvent) -> None:  # noqa: N802 -- Qt override
        """Zoom one step per :data:`WHEEL_STEP_UNITS` of accumulated vertical wheel movement.

        A mouse notch is one step, as before. A trackpad or precision touchpad sends smaller
        deltas; they add up until a step's worth (P71), and a change of direction starts the
        count again.
        """
        delta = event.angleDelta().y()
        if delta == 0:
            return
        if self._wheel_units != 0 and (delta > 0) != (self._wheel_units > 0):
            self._wheel_units = 0
        self._wheel_units += delta
        while self._wheel_units >= WHEEL_STEP_UNITS:
            self._wheel_units -= WHEEL_STEP_UNITS
            self.zoom_in()
        while self._wheel_units <= -WHEEL_STEP_UNITS:
            self._wheel_units += WHEEL_STEP_UNITS
            self.zoom_out()


RELEASE_POLL_S = 0.05
"""How often a job waiting for the preview's plan release looks at its cancel flag (R1-11)."""


class PreviewController(QObject):
    """Drives the preview from the session (implements ``contract.PreviewSurface``).

    Owns the preview worker (render) and the frame worker (video frames at a position). The
    session's changes become render requests; a result is shown only when it is the latest.

    Signals:
        rendered(object): a :class:`~clearwater.gui.render_worker.RenderResult` was shown.

    Args:
        session: The shell session.
        engines: The engines.
        widget: The preview widget.
        presenter: Where errors go.
    """

    rendered = Signal(object)

    def __init__(
        self,
        session: ShellSession,
        engines: Engines,
        widget: PreviewWidget,
        presenter: MessagePresenter,
    ) -> None:
        """Create the controller and its two worker threads."""
        super().__init__(widget)
        self._session = session
        self._engines = engines
        self._widget = widget
        self._presenter = presenter
        self._memo = PreviewMemo()
        self._renderer = LatestWorker("clearwater-preview", self._on_render)
        self._framer = LatestWorker("clearwater-frame", self._on_frame)
        self._frame_pending = False
        self._frame_requested = 0
        self._submitted_k: int | None = None
        self._error_shown = False
        self._frame_error_shown = False
        self._frame_source: object = None
        self._profile_source: OpenedSource | None = None
        self._profile: bytes | None = None
        self._device_lock = threading.Lock()
        self._device_backend: object = None
        self._plans_source: object = None
        session.parameters_changed.connect(self.request)
        session.settings_changed.connect(self.request)
        session.statistics_changed.connect(self.request)
        session.image_changed.connect(self._on_image)
        session.source_changed.connect(self._on_source)
        session.position_changed.connect(self._on_position)
        widget.view_changed.connect(self._on_view)

    # PreviewSurface.

    def show(self, image: Image, statistics: Mapping[str, Statistics] | None = None) -> None:
        """Make ``image`` the current image and render it (latest wins).

        Args:
            image: A full-resolution host image.
            statistics: The statistics to render with, or None for its own (D108).
        """
        self._framer.invalidate()
        self._frame_pending = False
        self._session._show(image, statistics)

    def show_proxy(
        self, proxy: NDArray[np.uint8], corrected: NDArray[np.uint8] | None = None
    ) -> None:
        """Show a scrub proxy at once until the next rendered result (D72).

        Args:
            proxy: ``(H, W, 3)`` uint8, the original side.
            corrected: The corrected side, or None to show ``proxy`` on both.
        """
        self._renderer.invalidate()
        icc = self._display_profile()
        before = display_image(proxy, icc)
        after = before if corrected is None else display_image(corrected, icc)
        self._widget.set_proxy(before, after)

    # Requests.

    def request(self, *_: object) -> None:
        """Submit a render of the current image with the current state (latest wins)."""
        image = self._session.current_image()
        if image is None or self._frame_pending:
            return
        self._release_for_source()  # a new source's first render follows the release (R1-6)
        method = self._session.method()
        params = effective_parameters(method, self._session.parameters())
        k = self._widget.needed_factor()
        snapshot = RenderRequest(
            token=self._session.image_token(),
            image=image,
            method=method,
            params=params,
            params_key=tuple(sorted(params.items())),
            settings=self._session.settings(),
            statistics=self._session.statistics(),
            statistics_revision=self._session.statistics_revision(),
            k=k,
            select_backend=self._engines.select_backend,
            display_icc=self._display_profile(),
        )
        memo = self._memo
        note = self._note_backend
        self._submitted_k = k
        # The indicator means "a full-resolution render replacing what is shown is in flight";
        # a k > 1 request supersedes any full render, which then never arrives.
        self._widget.set_pending_full(k == 1 and self._widget.after_image() is not None)
        self._renderer.submit(lambda check: render_preview(snapshot, memo, check, on_backend=note))

    def idle(self) -> bool:
        """Return True when no render or frame decode waits or runs."""
        return self._renderer.idle() and self._framer.idle()

    def release_device_plans(
        self, timeout_s: float | None, *, cancelled: Callable[[], bool] | None = None
    ) -> bool:
        """Release the preview thread's FFT plans and wait for it (DR-68; any thread but it).

        The release runs on the preview worker's thread as a chore, after the render in flight
        and before the next one; it is never superseded. The release is queued once; the wait
        looks at ``cancelled`` every :data:`RELEASE_POLL_S` seconds (R1-11).

        Args:
            timeout_s: The longest wait, or None to wait until the release ran or ``cancelled``.
            cancelled: Ends the wait early when it returns True (the waiting job's cancel).

        Returns:
            True when the release ran; False when the worker has stopped, the wait was
            cancelled, or ``timeout_s`` passed first.
        """
        done = threading.Event()

        def chore() -> None:
            try:
                self._release_plans()
            finally:
                done.set()

        if not self._renderer.run_chore(chore):
            return False
        deadline = None if timeout_s is None else time.monotonic() + timeout_s
        while not done.wait(RELEASE_POLL_S):
            if cancelled is not None and cancelled():
                return False
            if deadline is not None and time.monotonic() >= deadline:
                return False
        return True

    def stop(self, timeout_s: float) -> bool:
        """Stop both workers (shell close); the preview thread releases its FFT plans first.

        Args:
            timeout_s: The longest wait per worker.

        Returns:
            True when both threads have ended.
        """
        self._renderer.run_chore(self._release_plans)
        first = self._renderer.stop(timeout_s)
        second = self._framer.stop(timeout_s)
        return first and second

    def _note_backend(self, backend: object) -> None:
        """Preview thread: remember the latest device backend a render ran on (DR-68).

        A render on a backend without the device extension (the CPU after force CPU) leaves the
        remembered one, so the next boundary still releases the plans the device renders left
        on this thread (R1-4, ruling d530b564).
        """
        if not isinstance(backend, PreviewDeviceBackend):
            return
        with self._device_lock:
            self._device_backend = backend

    def _release_for_source(self) -> None:
        """Main thread: queue the plan release once per source change, before its first render.

        Called from :meth:`request` (the session emits ``image_changed`` before
        ``source_changed``) and from ``_on_source`` (an unload has no render), so the release is
        queued before the new source's first render either way (R1-6).
        """
        source = self._session.source()
        if source is self._plans_source:
            return
        self._plans_source = source
        self._renderer.run_chore(self._release_plans)

    def _release_plans(self) -> None:
        """Preview thread: release its FFT plans through the device extension (AD-29, DR-68)."""
        with self._device_lock:
            backend = self._device_backend
        if not isinstance(backend, PreviewDeviceBackend):
            return
        try:
            backend.release_fft_plans()
        except Exception as exc:  # for example a CUDA error at teardown; never ends the worker
            _LOG.warning(
                "releasing the preview's FFT plans failed: %s: %s", type(exc).__name__, exc
            )

    def _display_profile(self) -> bytes | None:
        """The open source's display profile, chosen once per source (main thread; DR-75)."""
        source = self._session.source()
        if source is not self._profile_source:
            self._profile_source = source
            self._profile = display_profile(source)
        return self._profile

    def _on_view(self) -> None:
        """Render again when the zoom or size needs another factor."""
        if self._session.current_image() is None:
            return
        if self._widget.needed_factor() != self._submitted_k:
            self.request()

    def _on_image(self) -> None:
        """A new current image: set the geometry and render."""
        image = self._session.current_image()
        if image is None:
            self._widget.clear()
            return
        height, width = image.pixels.shape[0], image.pixels.shape[1]
        self._widget.set_source_size(height, width, reset=False)
        self.request()

    def _on_source(self, source: object) -> None:
        """A new source: drop any frame decode and the memo of the old one, reset, render.

        The memo is replaced, not cleared, so a job still running for the old source writes
        into the discarded one; nothing of the old source stays resident. A render of the old
        source still waiting is dropped (an unload submits none to replace it, R2-6), and the
        preview thread's FFT plans are released before the new source's first render (DR-68).
        """
        self._renderer.invalidate()
        self._widget.set_pending_full(False)  # the invalidated render never arrives
        self._release_for_source()
        self._memo = PreviewMemo()
        self._framer.invalidate()
        self._frame_pending = False
        self._frame_source = source
        image = self._session.current_image()
        if image is not None:
            height, width = image.pixels.shape[0], image.pixels.shape[1]
            self._widget.set_source_size(height, width, reset=True)
        self.request()

    def _on_position(self, pts_ticks: object) -> None:
        """Decode the frame at a position on the frame worker (S5)."""
        source = self._session.source()
        if source is None or source.probe is None or not isinstance(pts_ticks, int):
            return
        probe = source.probe
        engines = self._engines
        self._frame_pending = True
        self._frame_requested = pts_ticks
        self._frame_source = source
        self._renderer.invalidate()
        self._widget.set_pending_full(False)  # the invalidated render never arrives
        self._framer.submit(lambda check: (source, sources.frame_at(engines, probe, pts_ticks)))

    def _on_frame(self, outcome: Outcome) -> None:
        """Main thread: show a decoded frame, or say why there is none."""
        if outcome.error is not None:
            self._frame_pending = False
            message = messages.frame_failure(outcome.error)
            self._presenter.present(message)
            self._frame_error_shown = True
            self._session.frame_decoded.emit(
                FrameOutcome(self._frame_requested, None, message.text)
            )
            return
        value = outcome.value
        assert isinstance(value, tuple)
        source, frame = value
        if source is not self._session.source():
            return
        self._frame_pending = False
        if not isinstance(frame, Frame):
            text = "No frame could be read at this position."
            self._presenter.present(Message("error", text, owner=messages.OWNER_FRAME))
            self._frame_error_shown = True
            self._session.frame_decoded.emit(FrameOutcome(self._frame_requested, None, text))
            return
        if self._frame_error_shown:  # the next success of that action clears its banner
            self._presenter.clear("error", owner=messages.OWNER_FRAME)
            self._frame_error_shown = False
        self._session._set_image(frame)
        self._session.frame_decoded.emit(FrameOutcome(self._frame_requested, frame.pts_ticks))

    def _on_render(self, outcome: Outcome) -> None:
        """Main thread: show the latest result, or the error with the last good preview kept."""
        if outcome.error is not None:
            error = outcome.error
            if isinstance(error, RenderError):
                if error.token == self._session.image_token():
                    self._session._set_backend(error.full_reason, error.preview_reason)
                error = error.cause
            _LOG.warning("preview failed: %s", error)
            self._widget.set_pending_full(False)
            self._presenter.present(messages.preview_failure(error))
            self._error_shown = True
            return
        result = outcome.value
        assert isinstance(result, RenderResult)
        if result.token != self._session.image_token():
            return
        self._widget.set_result(result.before, result.after, result.k)
        self._session._set_backend(result.full_reason, result.preview_reason)
        if self._error_shown:
            self._presenter.clear("error", owner=messages.OWNER_PREVIEW)
            self._error_shown = False
        self.rendered.emit(result)
