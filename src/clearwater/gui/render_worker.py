"""Latest-wins worker threads and the preview render job (G9, D108, V7).

A :class:`LatestWorker` owns one worker thread. The main thread submits tasks; each submit takes
a new generation number and replaces any task still waiting, so at most one task waits and one
runs. A running task calls its ``check`` between steps and stops (:class:`Superseded`) once a
newer generation exists. Results come back through a queued signal to a bridge object that lives
on the main thread, which drops any result whose generation is not the current one, so a stale
result is never delivered. Worker threads touch no ``QObject`` except emitting that signal.
"""

from __future__ import annotations

import logging
import threading
import time
from collections import OrderedDict
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QImage

from clearwater.interfaces import CorrectionMethod, Image, Settings, Statistics

from .contract import SelectBackend
from .imaging import (
    Check,
    display_image,
    downscale,
    downscaled_size,
    measure_statistics,
    render_host,
    to_display_uint8,
)

_LOG = logging.getLogger(__name__)


class Superseded(Exception):  # noqa: N818 -- a control-flow signal, not an error
    """Raised by a task's ``check`` when a newer task has been submitted."""


class RenderError(Exception):
    """A preview render that failed after both backend selections succeeded.

    Carries the reasons so the status bar still follows the selection (AD-9) when the render
    itself fails.

    Attributes:
        cause: What the render raised.
        token: The image token of the request.
        full_reason: The AD-9 reason of the full-resolution selection.
        preview_reason: The reason of the preview-size selection.
    """

    def __init__(self, cause: Exception, token: int, full_reason: str, preview_reason: str) -> None:
        """Wrap ``cause`` with the selection reasons.

        Args:
            cause: What the render raised.
            token: The image token of the request.
            full_reason: The full-resolution reason.
            preview_reason: The preview-size reason.
        """
        super().__init__(str(cause))
        self.cause = cause
        self.token = token
        self.full_reason = full_reason
        self.preview_reason = preview_reason


@dataclass(frozen=True)
class Outcome:
    """What a task produced, delivered on the main thread.

    Attributes:
        generation: The generation the task was submitted under.
        value: The task's return value, or None when it raised.
        error: The exception the task raised, or None.
    """

    generation: int
    value: object
    error: BaseException | None


class _Bridge(QObject):
    """Lives on the main thread; carries outcomes from the worker by a queued connection."""

    delivered = Signal(object)


class LatestWorker:
    """One worker thread running the latest submitted task (main-thread API).

    Args:
        name: The thread name.
        on_result: Called on the main thread with each outcome of the CURRENT generation.
    """

    def __init__(self, name: str, on_result: Callable[[Outcome], None]) -> None:
        """Create the worker and start its thread."""
        self._on_result = on_result
        self._lock = threading.Condition()
        self._generation = 0
        self._pending: tuple[int, Callable[[Check], object]] | None = None
        self._stopping = False
        self._busy = False
        self._undelivered = 0
        self._bridge = _Bridge()
        self._bridge.delivered.connect(self._deliver, Qt.ConnectionType.QueuedConnection)
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._thread.start()

    @property
    def generation(self) -> int:
        """The current generation number."""
        with self._lock:
            return self._generation

    def submit(self, task: Callable[[Check], object]) -> int:
        """Queue ``task`` as the latest, superseding any waiting or running task.

        Args:
            task: Called on the worker thread with a ``check`` callable.

        Returns:
            The task's generation.
        """
        with self._lock:
            self._generation += 1
            self._pending = (self._generation, task)
            self._lock.notify_all()
            return self._generation

    def invalidate(self) -> None:
        """Supersede the waiting and running task without submitting a new one."""
        with self._lock:
            self._generation += 1
            self._pending = None

    def idle(self) -> bool:
        """Return True when no task waits or runs and no outcome is still on its way."""
        with self._lock:
            return self._pending is None and not self._busy and self._undelivered == 0

    def stop(self, timeout_s: float) -> bool:
        """Stop the thread: supersede everything and wait for it to end.

        Args:
            timeout_s: The longest wait.

        Returns:
            True when the thread has ended.
        """
        with self._lock:
            self._stopping = True
            self._generation += 1
            self._pending = None
            self._lock.notify_all()
        self._thread.join(timeout_s)
        return not self._thread.is_alive()

    def _run(self) -> None:
        """The worker loop."""
        while True:
            with self._lock:
                while self._pending is None and not self._stopping:
                    self._lock.wait()
                if self._stopping:
                    return
                assert self._pending is not None
                generation, task = self._pending
                self._pending = None
                self._busy = True

            def check(generation: int = generation) -> None:
                with self._lock:
                    if generation != self._generation or self._stopping:
                        raise Superseded

            value: object = None
            error: BaseException | None = None
            try:
                value = task(check)
            except Superseded:
                with self._lock:
                    self._busy = False
                continue
            except Exception as exc:  # any failure of a task becomes a message, never a crash
                error = exc
            with self._lock:
                self._busy = False
                if generation != self._generation or self._stopping:
                    continue
                self._undelivered += 1
            try:
                self._bridge.delivered.emit(Outcome(generation, value, error))
            except RuntimeError:  # the bridge was deleted at shutdown
                return

    def _deliver(self, outcome: object) -> None:
        """Main thread: pass on an outcome of the current generation, drop a stale one."""
        assert isinstance(outcome, Outcome)
        with self._lock:
            self._undelivered -= 1
            current = outcome.generation == self._generation
        if current:
            self._on_result(outcome)


@dataclass(frozen=True)
class RenderRequest:
    """A snapshot of everything one preview render needs, taken on the main thread.

    Attributes:
        token: Identifies the current image (changes with every new image).
        image: The full-resolution host image.
        method: The correction method.
        params: The effective parameter values.
        params_key: A hashable form of ``params`` for the statistics memo.
        settings: The settings (``force_cpu``).
        statistics: The supplied statistics, or None to measure the image's own (D108).
        statistics_revision: The session's statistics revision (bumped by every update, also to
            the same object), part of the render memo's key.
        k: The preview downscale factor.
        select_backend: IF-2 selection.
    """

    token: int
    image: Image
    method: CorrectionMethod
    params: Mapping[str, Any]
    params_key: tuple[tuple[str, Any], ...]
    settings: Settings
    statistics: Mapping[str, Statistics] | None
    statistics_revision: int
    k: int
    select_backend: SelectBackend


@dataclass(frozen=True)
class RenderResult:
    """A finished preview render.

    Attributes:
        token: The image token of the request.
        k: The downscale factor of ``before`` and ``after``.
        before: The original at that factor, for display.
        after: The corrected image at that factor, for display.
        full_reason: The AD-9 reason of the full-resolution selection (what export uses).
        preview_reason: The reason of the selection the preview rendered with.
        elapsed_s: Wall-clock seconds of the job.
    """

    token: int
    k: int
    before: QImage
    after: QImage
    full_reason: str
    preview_reason: str
    elapsed_s: float


AfterKey = tuple[int, int, str, tuple[tuple[str, Any], ...], str, int]
"""``(token, k, method id, params_key, preview reason, statistics revision)``: what a corrected
display image is of."""


class PreviewMemo:
    """Small caches the preview worker keeps.

    Statistics per parameter state and device, originals per factor, and corrected display
    images per parameter state and factor, so a factor already rendered for the current state (a
    return to 1:1 above all, question 6: "once per parameter state") is shown without
    ``render``. At most
    one full-resolution (``k == 1``) corrected image is kept. Used from the preview worker thread;
    guarded by a lock so the main thread may clear it.
    """

    _SIZE = 8

    def __init__(self) -> None:
        """Create empty caches."""
        self._lock = threading.Lock()
        self._statistics: OrderedDict[tuple[Any, ...], dict[str, Statistics]] = OrderedDict()
        self._before: OrderedDict[tuple[int, int], QImage] = OrderedDict()
        self._after: OrderedDict[AfterKey, tuple[object, object, QImage]] = OrderedDict()

    def statistics(self, key: tuple[Any, ...]) -> dict[str, Statistics] | None:
        """Return the memoised statistics for a key, or None."""
        with self._lock:
            return self._statistics.get(key)

    def put_statistics(self, key: tuple[Any, ...], value: dict[str, Statistics]) -> None:
        """Memoise statistics, keeping the newest few."""
        with self._lock:
            self._statistics[key] = value
            while len(self._statistics) > self._SIZE:
                self._statistics.popitem(last=False)

    def before(self, token: int, k: int) -> QImage | None:
        """Return the memoised display original, or None."""
        with self._lock:
            return self._before.get((token, k))

    def put_before(self, token: int, k: int, image: QImage) -> None:
        """Memoise a display original, keeping the newest few."""
        with self._lock:
            self._before[token, k] = image
            while len(self._before) > self._SIZE:
                self._before.popitem(last=False)

    def after(
        self, key: AfterKey, method: object, statistics: Mapping[str, Statistics] | None
    ) -> QImage | None:
        """Return the memoised corrected display image, or None.

        Args:
            key: What the image is of.
            method: The method object; a hit needs the same object.
            statistics: The supplied statistics (None = measured); a hit needs the same object.

        Returns:
            The image, or None.
        """
        with self._lock:
            entry = self._after.get(key)
        if entry is None or entry[0] is not method or entry[1] is not statistics:
            return None
        return entry[2]

    def put_after(
        self,
        key: AfterKey,
        method: object,
        statistics: Mapping[str, Statistics] | None,
        image: QImage,
    ) -> None:
        """Memoise a corrected display image, keeping the newest few and one full resolution.

        Args:
            key: What the image is of.
            method: The method object it was rendered with.
            statistics: The supplied statistics it was rendered with (None = measured).
            image: The image.
        """
        with self._lock:
            if key[1] == 1:
                for old in [old for old in self._after if old[1] == 1]:
                    del self._after[old]
            self._after[key] = (method, statistics, image)
            while len(self._after) > self._SIZE:
                self._after.popitem(last=False)

    def clear(self) -> None:
        """Drop everything."""
        with self._lock:
            self._statistics.clear()
            self._before.clear()
            self._after.clear()


def render_preview(request: RenderRequest, memo: PreviewMemo, check: Check) -> RenderResult:
    """Run one preview render on the worker thread (brief task 6).

    ``select_backend`` for the full size (the status bar) and for the preview size (the render);
    the downscale; the statistics (supplied, memoised, or measured stage by stage on the
    statistics proxy); ``render``; ``to_host``; the display conversion of both sides.

    Args:
        request: The snapshot.
        memo: The worker's caches.
        check: Raises :class:`Superseded` when a newer request exists.

    Returns:
        The result.
    """
    start = time.perf_counter()
    image = request.image
    pixels = np.asarray(image.pixels, dtype=np.float32)
    height, width = pixels.shape[0], pixels.shape[1]
    method_id = request.method.id
    _, full_reason = request.select_backend(request.settings, height, width, method_id)
    small_h, small_w = downscaled_size(height, width, request.k)
    backend, preview_reason = request.select_backend(request.settings, small_h, small_w, method_id)
    check()
    try:
        after_key: AfterKey = (
            request.token,
            request.k,
            method_id,
            request.params_key,
            preview_reason,
            request.statistics_revision,
        )
        after = memo.after(after_key, request.method, request.statistics)
        small = None
        if after is None:
            statistics = request.statistics
            if statistics is None:
                # The device is in the key: statistics measured on one backend are not reused
                # on another (a force_cpu change measures again, as export would).
                key = (request.token, method_id, request.params_key, backend.device, preview_reason)
                statistics = memo.statistics(key)
                if statistics is None:
                    measured = measure_statistics(
                        request.method, backend, image, request.params, check
                    )
                    memo.put_statistics(key, measured)
                    statistics = measured
            check()
            small = downscale(pixels, request.k)
            check()
            corrected = render_host(
                request.method, backend, small, image.color, request.params, statistics
            )
            # Memoised before the check: a render superseded while it ran is not thrown away,
            # so a return to this state shows it without rendering again (question 6).
            after = display_image(to_display_uint8(corrected), image.color.icc_profile)
            memo.put_after(after_key, request.method, request.statistics, after)
            check()
        before = _before_image(memo, request, pixels, small)
    except Superseded:
        raise
    except Exception as exc:
        raise RenderError(exc, request.token, full_reason, preview_reason) from exc
    return RenderResult(
        token=request.token,
        k=request.k,
        before=before,
        after=after,
        full_reason=full_reason,
        preview_reason=preview_reason,
        elapsed_s=time.perf_counter() - start,
    )


def _before_image(
    memo: PreviewMemo, request: RenderRequest, pixels: NDArray[np.float32], small: Any
) -> QImage:
    """Return the display original at the request's factor, memoised per image and factor."""
    before = memo.before(request.token, request.k)
    if before is None:
        if small is None:
            small = downscale(pixels, request.k)
        before = display_image(to_display_uint8(small), request.image.color.icc_profile)
        memo.put_before(request.token, request.k, before)
    return before
