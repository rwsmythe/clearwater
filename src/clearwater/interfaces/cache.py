"""IF-7: the proxy cache.

Holds the analysis proxies and the source-only statistics, keyed by the source file's size and
modification time and a cache format version (D71, D113). The reader of the statistics and the
completeness marker were added by the AD-20 amendment of 2026-10-20 (WP3.12 brief).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable

import numpy as np
from numpy.typing import NDArray

from .method import Statistics


@dataclass(frozen=True)
class CacheKey:
    """Identifies one source file's cached results (IF-7; D71, D113).

    Attributes:
        size: The source file size in bytes.
        mtime_ns: The source file modification time in nanoseconds.
        cache_version: The cache format version.
    """

    size: int
    mtime_ns: int
    cache_version: int


@dataclass(frozen=True)
class CacheEntry:
    """What the cache holds for one key (IF-7).

    Attributes:
        key: The key the entry was looked up with.
        pts_ticks: The pts ticks (D95) of the stored proxies, ascending.
        stages: The stages whose stored source-only statistics (D113) cover every pts in
            ``pts_ticks``; a stage with statistics for only some frames is not listed.
        size_bytes: The bytes the entry occupies in the cache.
        complete: True only once the proxy pass for the whole clip is stored
            (:meth:`ProxyCache.mark_complete`); V17 skips the decode pass only on a complete
            entry (AD-20 amendment 2026-10-20).
    """

    key: CacheKey
    pts_ticks: tuple[int, ...]
    stages: tuple[str, ...]
    size_bytes: int
    complete: bool


@runtime_checkable
class ProxyCache(Protocol):
    """A size-limited store of analysis proxies and source-only statistics (IF-7)."""

    def lookup(self, key: CacheKey) -> CacheEntry | None:
        """Return the entry for ``key``, or None when nothing is cached.

        Args:
            key: The source file's cache key.

        Returns:
            The entry, or None.
        """
        ...

    def store_proxy(self, key: CacheKey, pts_ticks: int, proxy: NDArray[np.uint8]) -> None:
        """Store one frame's proxy: uint8, 540 short side (AD-5).

        Args:
            key: The source file's cache key.
            pts_ticks: The frame's presentation time in ticks.
            proxy: The proxy pixels.
        """
        ...

    def proxy(self, key: CacheKey, pts_ticks: int) -> NDArray[np.uint8]:
        """Return one frame's proxy.

        Args:
            key: The source file's cache key.
            pts_ticks: The frame's presentation time in ticks.

        Returns:
            The proxy pixels.
        """
        ...

    def store_source_statistics(
        self, key: CacheKey, stage: str, pts_ticks: int, stats: Statistics
    ) -> None:
        """Store one frame's source-only statistics of a stage (D113).

        Args:
            key: The source file's cache key.
            stage: The stage name.
            pts_ticks: The frame's presentation time in ticks.
            stats: The statistics.
        """
        ...

    def source_statistics(self, key: CacheKey, stage: str, pts_ticks: int) -> Statistics:
        """Return one frame's stored source-only statistics of a stage (D113; AD-7).

        Args:
            key: The source file's cache key.
            stage: The stage name.
            pts_ticks: The frame's presentation time in ticks.

        Returns:
            The statistics.

        Raises:
            KeyError: Nothing is stored for this key, stage and pts.
        """
        ...

    def mark_complete(self, key: CacheKey) -> None:
        """Record that the proxy pass for the whole clip is stored (V17).

        Args:
            key: The source file's cache key.
        """
        ...

    def limit_bytes(self) -> int:
        """Return the size limit in bytes (default 20 GB, oldest removed first; D71)."""
        ...

    def set_limit_bytes(self, n: int) -> None:
        """Set the size limit.

        Args:
            n: The new limit in bytes.
        """
        ...

    def clear(self) -> None:
        """Remove everything from the cache."""
        ...
