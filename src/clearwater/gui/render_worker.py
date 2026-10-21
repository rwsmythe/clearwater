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


class PreviewMemo:
    """Small caches the preview worker keeps: statistics per parameter state, originals per k.

    Used from the preview worker thread; guarded by a lock so the main thread may clear it.
    """

    _SIZE = 8

    def __init__(self) -> None:
        """Create empty caches."""
        self._lock = threading.Lock()
        self._statistics: OrderedDict[tuple[Any, ...], dict[str, Statistics]] = OrderedDict()
        self._before: OrderedDict[tuple[int, int], QImage] = OrderedDict()

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

    def clear(self) -> None:
        """Drop everything."""
        with self._lock:
            self._statistics.clear()
            self._before.clear()


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
    statistics = request.statistics
    if statistics is None:
        key = (request.token, method_id, request.params_key)
        statistics = memo.statistics(key)
        if statistics is None:
            measured = measure_statistics(request.method, backend, image, request.params, check)
            memo.put_statistics(key, measured)
            statistics = measured
    check()
    small = downscale(pixels, request.k)
    check()
    corrected = render_host(request.method, backend, small, image.color, request.params, statistics)
    check()
    icc = image.color.icc_profile
    after = display_image(to_display_uint8(corrected), icc)
    before = memo.before(request.token, request.k)
    if before is None:
        before = display_image(to_display_uint8(small), icc)
        memo.put_before(request.token, request.k, before)
    return RenderResult(
        token=request.token,
        k=request.k,
        before=before,
        after=after,
        full_reason=full_reason,
        preview_reason=preview_reason,
        elapsed_s=time.perf_counter() - start,
    )
