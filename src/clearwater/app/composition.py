"""The composition root: the one product place that builds the real engines (WP4.1).

Each function returns a fresh real component. Importing this module builds none of the root's
components and probes no device (``clearwater.core`` builds its module-level CPU backend when it
is imported and probes CUDA on the first selection that is not forced).
WP4.1 builds the photo legs: the IF-6 reader and writer of :mod:`clearwater.io.photo`, the IF-3
methods of :mod:`clearwater.methods` (``"c3"`` first, D16), the IF-2 selection of
:mod:`clearwater.core` and the export engine of :mod:`clearwater.jobs` behind the WP3.19
``ExportJobs`` seam. WP4.2 adds the video legs: the IF-5 source and sink of
:mod:`clearwater.io.video`, built per video job on the backend the job selected (DR-67), and the
IF-7 proxy cache of :mod:`clearwater.cache` over a folder the caller passes in. WP4.3 adds the
application's one cache, opened later by a start-up job (:func:`proxy_cache_opener`), and lets
:func:`export_jobs` share a cache instead of opening its own.

This module imports nothing from ``clearwater.gui``, no PySide6 and no ``cupy``/``cupyx``
(AD-29), and never resolves the app-data folder: the caller passes settings in.
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Mapping
from pathlib import Path
from typing import NoReturn

import numpy as np
from numpy.typing import NDArray

import clearwater
from clearwater import core
from clearwater.cache import DiskProxyCache
from clearwater.interfaces import (
    DEFAULT_CACHE_LIMIT_BYTES,
    ArrayBackend,
    CacheEntry,
    CacheKey,
    CorrectionMethod,
    PhotoSink,
    PhotoSource,
    ProxyCache,
    Statistics,
    VideoSink,
    VideoSource,
)
from clearwater.io.photo import PhotoReader, PhotoWriter
from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource
from clearwater.jobs import BackendSelector, ExportEngine
from clearwater.methods import available_methods


def photo_reader() -> PhotoSource:
    """Return a new photo reader (IF-6 ``PhotoSource``; HEIC, JPEG, PNG, TIFF; D116 refusals).

    Returns:
        A :class:`~clearwater.io.photo.PhotoReader`.
    """
    return PhotoReader()


def photo_writer() -> PhotoSink:
    """Return a new photo writer (IF-6 ``PhotoSink``; PNG at 8 or 16 bit, ICC, EXIF, provenance).

    Returns:
        A :class:`~clearwater.io.photo.PhotoWriter`.
    """
    return PhotoWriter()


def correction_methods() -> dict[str, CorrectionMethod]:
    """Return new instances of the registered correction methods, the default first (D16).

    Returns:
        Method id -> method: ``"c3"`` then ``"ancuti2018"``.
    """
    return available_methods()


def backend_selector() -> BackendSelector:
    """Return the IF-2 backend selection (AD-1, AD-9, D111).

    Returns:
        ``clearwater.core.select_backend`` itself.
    """
    return core.select_backend


VIDEO_NEEDS_A_CACHE = "video export needs a cache folder; none was given"
"""The failure of a video job from :func:`export_jobs` built without a cache folder."""


class _NoCacheFolder:
    """The IF-7 cache of an :func:`export_jobs` built without a cache folder.

    Every operation that needs a cache folder refuses with :data:`VIDEO_NEEDS_A_CACHE`;
    :meth:`limit_bytes` returns 0.

    The video job asks for its cache key (:meth:`key_for`) before any cache method, so a video
    request that reaches the cache fails there, after its probe and before its analysis or any
    write. An earlier refusal (the encoder, output planning, the disk-space check) may be
    reported first; either way nothing is written. A photo job never reaches the cache.
    """

    def _refuse(self) -> NoReturn:
        raise RuntimeError(VIDEO_NEEDS_A_CACHE)

    def key_for(self, path: Path) -> CacheKey:
        """Refuse: there is no cache folder."""
        self._refuse()

    def lookup(self, key: CacheKey) -> CacheEntry | None:
        """Refuse: there is no cache folder."""
        self._refuse()

    def store_proxy(self, key: CacheKey, pts_ticks: int, proxy: NDArray[np.uint8]) -> None:
        """Refuse: there is no cache folder."""
        self._refuse()

    def proxy(self, key: CacheKey, pts_ticks: int) -> NDArray[np.uint8]:
        """Refuse: there is no cache folder."""
        self._refuse()

    def store_source_statistics(
        self, key: CacheKey, stage: str, pts_ticks: int, stats: Statistics
    ) -> None:
        """Refuse: there is no cache folder."""
        self._refuse()

    def source_statistics(self, key: CacheKey, stage: str, pts_ticks: int) -> Statistics:
        """Refuse: there is no cache folder."""
        self._refuse()

    def mark_complete(self, key: CacheKey) -> None:
        """Refuse: there is no cache folder."""
        self._refuse()

    def limit_bytes(self) -> int:
        """Return zero: there is no cache folder."""
        return 0

    def set_limit_bytes(self, n: int) -> None:
        """Refuse: there is no cache folder."""
        self._refuse()

    def clear(self) -> None:
        """Refuse: there is no cache folder."""
        self._refuse()


def video_source(device_backend: ArrayBackend | None = None) -> VideoSource:
    """Return a new video source (IF-5; WP3.9 probe and FFmpeg decode).

    Args:
        device_backend: The video job's GPU backend, whose ``hw_decode`` frames are then
            converted and yielded on its device (DR-67, AD-29); None for a CPU job or a probe.

    Returns:
        A :class:`~clearwater.io.video.FFmpegVideoSource`.
    """
    return FFmpegVideoSource(device_backend=device_backend)


def video_sink(device_backend: ArrayBackend | None = None) -> VideoSink:
    """Return a new, unopened video sink (IF-5; WP3.10 FFmpeg encode and verification).

    Args:
        device_backend: The video job's GPU backend, on whose device a device frame is then
            quantised (DR-67, AD-29); None for a CPU job.

    Returns:
        A :class:`~clearwater.io.video.FFmpegVideoSink`.
    """
    return FFmpegVideoSink(device_backend=device_backend)


def proxy_cache(folder: Path, limit_bytes: int = DEFAULT_CACHE_LIMIT_BYTES) -> DiskProxyCache:
    """Return the proxy cache over ``folder`` with its registered default codec (IF-7; DR-41).

    Opening it removes the entries of another cache format version (D113) and applies the
    limit (D71); the folder is created on the first store.

    Args:
        folder: The cache folder; the caller's (the root never resolves the app-data folder).
        limit_bytes: The size limit in bytes (``Settings.cache_limit_bytes``).

    Returns:
        A :class:`~clearwater.cache.DiskProxyCache`; its ``key_for`` is the key of a source.
    """
    return DiskProxyCache(folder, limit_bytes)


CACHE_NOT_OPENED = "the analysis cache could not be opened: {reason}"
"""The refusal of every :class:`DeferredProxyCache` member after a failed open."""


class DeferredProxyCache:
    """The application's one proxy cache, opened later by a start-up job (WP4.3, ruling S1 (a)).

    It implements IF-7 (``ProxyCache``) plus ``key_for`` by DELEGATION to the
    :class:`~clearwater.cache.DiskProxyCache` that :meth:`open` creates over the folder, so the
    window can appear before the cache's crash clean-up and eviction have run (a first open of
    a full cache took 16 s on the owner's laptop) and the limit comes from the one settings read.
    Every member waits until the open has ended and is meant for worker threads only (the GUI's
    jobs, the analysis and the export). After a failed open every member refuses with
    :data:`CACHE_NOT_OPENED` naming the open's reason, except :meth:`limit_bytes`, which returns
    0 (the refusing cache's form); :meth:`fail` ends the wait when the opening job cannot run,
    so nothing waits for ever. A call made while the open runs (the settings dialog's limit or
    clear) is applied after it.

    Args:
        folder: The cache folder (the caller's: ``app_locations().cache_dir``).
    """

    def __init__(self, folder: Path) -> None:
        """Create the handle; nothing is read until :meth:`open`."""
        self._folder = folder
        self._lock = threading.Lock()
        self._ended = threading.Event()
        self._started = False
        self._cache: DiskProxyCache | None = None
        self._failure: str | None = None

    @property
    def folder(self) -> Path:
        """The cache folder."""
        return self._folder

    def open(self, limit_bytes: int) -> str | None:
        """Open the cache over the folder with ``limit_bytes`` (once, on a worker thread).

        Args:
            limit_bytes: The size limit (``Settings.cache_limit_bytes`` of the one settings
                read).

        Returns:
            None when the cache opened; else the reason it could not, which every member then
            refuses with.

        Raises:
            RuntimeError: The handle was opened or failed before.
        """
        self._start()
        try:
            self._cache = proxy_cache(self._folder, limit_bytes)
        except Exception as exc:  # any failure is the reason every member refuses with
            self._failure = str(exc) or type(exc).__name__
        finally:
            self._ended.set()
        return self._failure

    def fail(self, reason: str) -> None:
        """End the wait without opening: every member refuses with ``reason`` (no open ran).

        Args:
            reason: Why the cache was not opened.

        Raises:
            RuntimeError: The handle was opened or failed before.
        """
        self._start()
        self._failure = reason
        self._ended.set()

    def wait_open(self, timeout_s: float | None = None) -> bool:
        """Wait until the open has ended (opened or failed).

        Args:
            timeout_s: The longest wait, or None to wait until it ends.

        Returns:
            True when the open has ended.
        """
        return self._ended.wait(timeout_s)

    def failure(self) -> str | None:
        """Return why the open failed, or None (also while it has not ended)."""
        return self._failure if self._ended.is_set() else None

    def opened(self) -> DiskProxyCache | None:
        """Return the cache behind the handle once it opened, else None (never waits)."""
        return self._cache if self._ended.is_set() else None

    def _start(self) -> None:
        """Claim the one open."""
        with self._lock:
            if self._started:
                raise RuntimeError("the analysis cache is opened once")
            self._started = True

    def _target(self) -> DiskProxyCache:
        """Wait for the open; return the cache, or refuse with the open's reason."""
        self._ended.wait()
        if self._cache is None:
            raise RuntimeError(CACHE_NOT_OPENED.format(reason=self._failure))
        return self._cache

    def key_for(self, path: Path) -> CacheKey:
        """Return the cache key of a source file (the cache's own ``key_for``, DR-41)."""
        return self._target().key_for(path)

    def lookup(self, key: CacheKey) -> CacheEntry | None:
        """Return the entry for ``key`` (IF-7)."""
        return self._target().lookup(key)

    def store_proxy(self, key: CacheKey, pts_ticks: int, proxy: NDArray[np.uint8]) -> None:
        """Store one frame's proxy (IF-7)."""
        self._target().store_proxy(key, pts_ticks, proxy)

    def proxy(self, key: CacheKey, pts_ticks: int) -> NDArray[np.uint8]:
        """Return one stored proxy (IF-7)."""
        return self._target().proxy(key, pts_ticks)

    def store_source_statistics(
        self, key: CacheKey, stage: str, pts_ticks: int, stats: Statistics
    ) -> None:
        """Store one frame's source-only statistics (IF-7)."""
        self._target().store_source_statistics(key, stage, pts_ticks, stats)

    def source_statistics(self, key: CacheKey, stage: str, pts_ticks: int) -> Statistics:
        """Return one frame's source-only statistics (IF-7)."""
        return self._target().source_statistics(key, stage, pts_ticks)

    def mark_complete(self, key: CacheKey) -> None:
        """Mark an entry complete (IF-7)."""
        self._target().mark_complete(key)

    def limit_bytes(self) -> int:
        """Return the size limit (IF-7); 0 after a failed open."""
        self._ended.wait()
        return 0 if self._cache is None else self._cache.limit_bytes()

    def set_limit_bytes(self, n: int) -> None:
        """Set the size limit (IF-7); a call made during the open is applied after it."""
        self._target().set_limit_bytes(n)

    def clear(self) -> None:
        """Remove every entry (IF-7); a call made during the open is applied after it."""
        self._target().clear()


def proxy_cache_opener(folder: Path) -> DeferredProxyCache:
    """Return the application's one proxy cache over ``folder``, not yet open (ruling S1 (a)).

    Args:
        folder: The cache folder; the caller's (the root never resolves the app-data folder).

    Returns:
        A :class:`DeferredProxyCache`; one start-up job calls its ``open`` with the limit.
    """
    return DeferredProxyCache(folder)


def export_jobs(
    *,
    app_version: str = clearwater.__version__,
    reader: PhotoSource | None = None,
    writer: PhotoSink | None = None,
    methods: Mapping[str, CorrectionMethod] | None = None,
    select_backend: BackendSelector | None = None,
    on_stage: Callable[[str], None] | None = None,
    cache_folder: Path | None = None,
    cache_limit_bytes: int = DEFAULT_CACHE_LIMIT_BYTES,
    source_for: Callable[[ArrayBackend | None], VideoSource] | None = None,
    sink_for: Callable[[ArrayBackend | None], VideoSink] | None = None,
    cache: DiskProxyCache | DeferredProxyCache | None = None,
) -> ExportEngine:
    """Return a new export engine for photos and videos (the WP3.19 ``ExportJobs`` seam).

    A photo is read with :func:`photo_reader`, rendered with :func:`correction_methods` on the
    backend :func:`backend_selector` picks and written with :func:`photo_writer` through
    ``clearwater.jobs.SafeWrite``. A video is probed by :func:`video_source`; each video job then
    builds its own source and sink with :func:`video_source` and :func:`video_sink` on the
    backend it selected (DR-67), analyses through :func:`proxy_cache` over ``cache_folder`` and
    encodes through ``SafeWrite``; each input file is its own clip (spec section 5.5). Without
    ``cache_folder`` a video request fails before any write, with :data:`VIDEO_NEEDS_A_CACHE`
    unless an earlier refusal (the encoder, output planning, the disk-space check) is reported
    first. Given ``cache`` instead, the engine analyses through that cache, keyed by its own
    ``key_for`` (DR-41), and opens none: the application passes its one cache, so the GUI's
    analysis and every export share one instance (WP4.3, ruling Q16).
    The overrides exist for tests and instruments only.

    Args:
        app_version: The version recorded in provenance (D91).
        reader: The photo reader; :func:`photo_reader` when None.
        writer: The photo writer; :func:`photo_writer` when None.
        methods: The methods by id, default first; :func:`correction_methods` when None.
        select_backend: The backend selection; :func:`backend_selector` when None.
        on_stage: The engine's phase hook (the V16 instrument's); none when None.
        cache_folder: The analysis cache folder (the caller's: ``app_locations().cache_dir`` in
            the application); None for an engine without video.
        cache_limit_bytes: The cache size limit (``Settings.cache_limit_bytes``).
        source_for: Builds a video job's frame source from its device backend;
            :func:`video_source` when None.
        sink_for: Builds a video job's sink from its device backend; :func:`video_sink` when
            None.
        cache: The cache to analyse through (the application's one cache); None to open one
            over ``cache_folder``.

    Returns:
        The export engine.

    Raises:
        ValueError: Both ``cache`` and ``cache_folder`` are given.
    """
    shared: ProxyCache
    key: Callable[[Path], CacheKey]
    if cache is not None:
        if cache_folder is not None:
            raise ValueError("give the export engine a cache or a cache folder, not both")
        shared, key = cache, cache.key_for
    elif cache_folder is None:
        refusing = _NoCacheFolder()
        shared, key = refusing, refusing.key_for
    else:
        disk = proxy_cache(cache_folder, cache_limit_bytes)
        shared, key = disk, disk.key_for
    return ExportEngine(
        methods=correction_methods() if methods is None else methods,
        video_source=video_source(),
        sink_factory=video_sink,
        photo_reader=photo_reader() if reader is None else reader,
        photo_writer=photo_writer() if writer is None else writer,
        cache=shared,
        cache_key=key,
        select_backend=backend_selector() if select_backend is None else select_backend,
        app_version=app_version,
        on_stage=on_stage,
        source_for=video_source if source_for is None else source_for,
        sink_for=video_sink if sink_for is None else sink_for,
    )
