"""The composition root: the one product place that builds the real engines (WP4.1).

Each function returns a fresh real component. Importing this module builds none of the root's
components and probes no device (``clearwater.core`` builds its module-level CPU backend when it
is imported and probes CUDA on the first selection that is not forced).
WP4.1 builds the photo legs: the IF-6 reader and writer of :mod:`clearwater.io.photo`, the IF-3
methods of :mod:`clearwater.methods` (``"c3"`` first, D16), the IF-2 selection of
:mod:`clearwater.core` and the export engine of :mod:`clearwater.jobs` behind the WP3.19
``ExportJobs`` seam. WP4.2 adds the video legs: the IF-5 source and sink of
:mod:`clearwater.io.video`, built per video job on the backend the job selected (DR-67), and the
IF-7 proxy cache of :mod:`clearwater.cache` over a folder the caller passes in.

This module imports nothing from ``clearwater.gui``, no PySide6 and no ``cupy``/``cupyx``
(AD-29), and never resolves the app-data folder: the caller passes settings in.
"""

from __future__ import annotations

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
    """The IF-7 cache of an :func:`export_jobs` built without a cache folder: every use refuses.

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
    first.
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

    Returns:
        The export engine.
    """
    cache: ProxyCache
    key: Callable[[Path], CacheKey]
    if cache_folder is None:
        refusing = _NoCacheFolder()
        cache, key = refusing, refusing.key_for
    else:
        disk = proxy_cache(cache_folder, cache_limit_bytes)
        cache, key = disk, disk.key_for
    return ExportEngine(
        methods=correction_methods() if methods is None else methods,
        video_source=video_source(),
        sink_factory=video_sink,
        photo_reader=photo_reader() if reader is None else reader,
        photo_writer=photo_writer() if writer is None else writer,
        cache=cache,
        cache_key=key,
        select_backend=backend_selector() if select_backend is None else select_backend,
        app_version=app_version,
        on_stage=on_stage,
        source_for=video_source if source_for is None else source_for,
        sink_for=video_sink if sink_for is None else sink_for,
    )
