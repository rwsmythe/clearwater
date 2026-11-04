"""The proxy cache (IF-7): a size-limited, crash-safe store in a folder the cache owns (WP3.12).

One folder per key (``e_<size>_<mtime_ns>_<version>``), each holding an append-only pack of
checked records (see :mod:`clearwater.cache.layout`). A record is appended and flushed to the
operating system; nothing is synced per record. Durability comes from the completeness marker:
``mark_complete`` syncs the pack and only then writes the marker, so an entry left by a crash or
a cancelled analysis is never complete, and a torn tail is found by length or checksum and cut
off by the next writer. Nothing in the cache folder is read, deleted or replaced unless the
cache named it.

Threads: one lock per cache instance guards the entries, indexes, the append handle, the stamps
and eviction; the bytes of a proxy or statistics record are read outside it. One store call at a
time per key: a second store (or ``mark_complete``) on a key whose store call is still running is
a ``RuntimeError``. Two processes sharing a folder are outside the envelope.

Completeness (V17): ``complete`` is True only after ``mark_complete``, durably. Storing a new or
changed PROXY into a complete entry makes it incomplete again (the marker is removed first);
storing statistics never does. WP3.11 should skip the decode pass only on a complete entry, and
should measure on the proxy as stored (``proxy``), on the first pass and on reopen alike, so
that both give the same statistics when the store form is lossy.
"""

from __future__ import annotations

import contextlib
import json
import logging
import operator
import os
import re
import struct
import threading
import time
import zlib
from collections.abc import Callable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import BinaryIO, Self, SupportsIndex

import numpy as np
from numpy.typing import NDArray

from clearwater.config.atomic import atomic_write_text
from clearwater.interfaces.cache import CacheEntry, CacheKey
from clearwater.interfaces.method import Statistics
from clearwater.interfaces.settings import DEFAULT_CACHE_LIMIT_BYTES

from .codec import CODECS, DEFAULT_CODEC, SHAPE_PREFIX_BYTES, ProxyCodec
from .keys import codec_cache_version, entry_name, parse_entry_name
from .layout import (
    CACHE_FILE_NAMES,
    KIND_PROXY,
    KIND_STATS,
    MARKER_NAME,
    META_NAME,
    PACK_HEADER_SIZE,
    PACK_NAME,
    RECORD_HEADER_SIZE,
    REMOVING_NAME,
    TEMP_SUFFIX,
    PackError,
    PackIndex,
    Rec,
    check_pack_header,
    decode_statistics,
    encode_record,
    encode_statistics,
    marker_valid,
    pack_header,
    read_marker,
    read_record,
    read_stamp,
    scan_pack,
)

_LOG = logging.getLogger("clearwater.cache")
_INT64 = 1 << 63
_TEMP_NAME = re.compile(r"^(?:data\.pack|complete|meta\.json|removing)\.[a-z0-9_]{8}\.tmp$")
"""The shape of a temporary of ``atomic_write_text`` (``tempfile`` names: 8 random characters)."""
_UNLINK_TRIES = 6
_UNLINK_PAUSE = 0.01
_READER_WAIT = 5.0


@dataclass
class _Entry:
    """One cache entry as the instance knows it."""

    key: CacheKey
    folder: Path
    pack_size: int
    aux_size: int = 0
    stamp: int = 0
    scanned: bool = False
    closing: bool = False
    complete: bool = False
    index: PackIndex = field(default_factory=PackIndex)

    @property
    def pack(self) -> Path:
        """The entry's pack file."""
        return self.folder / PACK_NAME

    @property
    def size_bytes(self) -> int:
        """Bytes the entry occupies on disk (the cache's own files)."""
        return self.pack_size + self.aux_size


def _is_cache_file(name: str) -> bool:
    """Return whether a file name in an entry folder is one the cache writes (or a temporary)."""
    return name in CACHE_FILE_NAMES or _TEMP_NAME.match(name) is not None


def _eviction_key(entry: _Entry) -> tuple[bool, int, tuple[int, int, int]]:
    """Return the sort key of eviction: entries marked for removal, then the oldest last use."""
    key = entry.key
    return not entry.closing, entry.stamp, (key.size, key.mtime_ns, key.cache_version)


def _stage_covers(proxy_pts: set[int], stage_pts: dict[int, Rec]) -> bool:
    """Return whether a stage has statistics for every pts in ``proxy_pts`` (IF-7 ``stages``)."""
    return proxy_pts <= stage_pts.keys()


def _unlink(path: str) -> bool:
    """Delete one file, trying again briefly when it is open elsewhere.

    A reader holds a pack open only for the instant of one seek and read, but Windows refuses to
    delete a file while it is open; a few short pauses let that read finish.

    Args:
        path: The file.

    Returns:
        True when the file is gone (or was already), False when it could not be removed.
    """
    for attempt in range(_UNLINK_TRIES):
        try:
            os.unlink(path)
        except FileNotFoundError:
            return True
        except PermissionError:
            if attempt + 1 < _UNLINK_TRIES:
                time.sleep(_UNLINK_PAUSE)
        except OSError:
            return False
        else:
            return True
    return False


def _write_small(path: Path, text: str) -> bool:
    """Write a tiny file atomically, or in place when the replace is refused.

    Args:
        path: The file.
        text: Its text.

    Returns:
        False when neither way worked.
    """
    try:
        atomic_write_text(path, text)
        return True
    except OSError:
        pass
    try:
        path.write_text(text, encoding="utf-8")
        return True
    except OSError:
        return False


def _remove_files(folder: Path) -> bool:
    """Delete the files of the cache's own names in ``folder``, then the folder if it is empty.

    Only regular files are removed: a link, a directory or any file the cache did not name is
    left alone (and keeps the folder in place). The pack goes first; if it cannot be removed
    nothing else is touched.

    Args:
        folder: An entry folder.

    Returns:
        False when a cache file could not be removed (for example it is open elsewhere).
    """
    try:
        items = list(os.scandir(folder))
    except FileNotFoundError:
        return True
    except OSError:
        return False
    removed = True
    for item in sorted(items, key=lambda found: found.name != PACK_NAME):
        if not _is_cache_file(item.name):
            continue
        if item.is_symlink() or not item.is_file(follow_symlinks=False):
            continue
        if not _unlink(item.path):
            removed = False
            if item.name == PACK_NAME:
                break  # an entry whose pack stays is left whole, not half removed
    if removed:
        with contextlib.suppress(OSError):
            os.rmdir(folder)
    return removed


def _int64(value: SupportsIndex, what: str) -> int:
    """Return ``value`` as a Python int in the int64 range."""
    number = operator.index(value)
    if not -_INT64 <= number < _INT64:
        raise ValueError(f"{what} is outside the 64-bit range")
    return number


class DiskProxyCache:
    """The IF-7 proxy cache over a folder (:class:`clearwater.interfaces.cache.ProxyCache`).

    The folder and the limit are arguments; the cache never resolves the app-data folder itself
    (production wiring passes ``app_locations().cache_dir`` and ``Settings.cache_limit_bytes``).

    Eviction (D71): the entry with the oldest last use goes first, where a ``lookup`` hit and
    ``mark_complete`` refresh an entry's stamp. The entry of the store call in progress, the
    entry stored to last and the entry last found by ``lookup`` are never evicted; if they alone
    exceed the limit the cache keeps them, logs a warning and evicts everything else.
    """

    def __init__(
        self,
        folder: Path,
        limit_bytes: int = DEFAULT_CACHE_LIMIT_BYTES,
        *,
        codec: ProxyCodec = DEFAULT_CODEC,
        clock: Callable[[], int] = time.time_ns,
    ) -> None:
        """Open the cache over ``folder`` (created on the first store).

        Entries of another cache format version, entries whose pack cannot be read, and the
        temporaries of a crash are removed; the rest are kept and counted, and the limit is
        applied.

        Args:
            folder: The cache folder.
            limit_bytes: The size limit in bytes.
            codec: The codec new proxy records are written with.
            clock: Returns the current time in nanoseconds; tests control the eviction order.

        Raises:
            ValueError: ``limit_bytes`` is negative, or ``codec`` is not the registered codec
                of its id (an unregistered id, or another decoder, shape reader or identity:
                records are read back through :data:`CODECS`, so a codec that differs there
                would store what it cannot return).
        """
        if limit_bytes < 0:
            raise ValueError("the cache limit is not negative")
        registered = CODECS.get(codec.codec_id)
        if (
            registered is None
            or registered.decode is not codec.decode
            or registered.shape is not codec.shape
            or registered.identity is not codec.identity
        ):
            raise ValueError(
                f"codec {codec.name!r} is not the registered codec of id {codec.codec_id}"
            )
        self._folder = folder
        self._limit = limit_bytes
        self._codec = codec
        self._version = codec_cache_version(codec)
        self._clock = clock
        self._lock = threading.RLock()
        self._entries: dict[CacheKey, _Entry] = {}
        self._writing: set[CacheKey] = set()
        self._active_reads: dict[CacheKey, int] = {}
        self._idle = threading.Condition(self._lock)
        self._wentry: _Entry | None = None
        self._wfile: BinaryIO | None = None
        self._last_lookup: CacheKey | None = None
        self._last_store: CacheKey | None = None
        self._over_limit_warned = False
        with self._lock:
            self._discover()
            self._evict(set())

    # --- IF-7 -------------------------------------------------------------------------------

    def lookup(self, key: CacheKey) -> CacheEntry | None:
        """Return the entry for ``key``, or None when nothing valid is cached.

        A key that differs in size, ``mtime_ns`` or ``cache_version`` finds nothing. An entry
        still being written is returned (``complete`` False). A hit refreshes the entry's
        last-use stamp. Damaged files make the entry a miss; this never raises for them.

        Args:
            key: The source file's cache key.

        Returns:
            The entry, or None.
        """
        with self._lock:
            entry = self._entries.get(key)
            if entry is None or entry.closing or not self._ensure_scanned(entry):
                return None
            index = entry.index
            if not index.proxies and not index.stats:
                return None
            self._touch(entry)
            self._last_lookup = key
            proxy_pts = set(index.proxies)
            stages = sorted(s for s, pts in index.stats.items() if _stage_covers(proxy_pts, pts))
            return CacheEntry(
                key=key,
                pts_ticks=tuple(sorted(proxy_pts)),
                stages=tuple(stages),
                size_bytes=entry.size_bytes,
                complete=entry.complete,
            )

    def store_proxy(self, key: CacheKey, pts_ticks: int, proxy: NDArray[np.uint8]) -> None:
        """Store one frame's proxy: ``uint8``, shape ``(H, W, 3)``, as the entry's first proxy.

        Storing a proxy that is already stored byte for byte changes nothing. Storing a new or
        changed proxy into a complete entry makes it incomplete again.

        Args:
            key: The source file's cache key (current cache version).
            pts_ticks: The frame's presentation time in ticks.
            proxy: The proxy pixels.

        Raises:
            ValueError: The proxy is not uint8 ``(H, W, 3)``, differs in shape from the entry's
                first proxy, or the key is not storable.
            TypeError: ``proxy`` is not an array.
            RuntimeError: Another store call on this key is still running.
            OSError: The file cannot be written; the pack is cut back to its last whole record.
        """
        pts = _int64(pts_ticks, "pts")
        self._check_key(key)
        if not isinstance(proxy, np.ndarray):
            raise TypeError("a proxy is a numpy array")
        if proxy.dtype != np.uint8 or proxy.ndim != 3 or proxy.shape[2] != 3 or 0 in proxy.shape:
            raise ValueError(f"a proxy is uint8 (H, W, 3), got {proxy.dtype} {proxy.shape}")
        shape = (int(proxy.shape[0]), int(proxy.shape[1]), 3)
        with self._write_slot(key):
            blob = self._codec.encode(np.ascontiguousarray(proxy))
            with self._lock:
                entry = self._entry_for_write(key)
                known = entry.index.shape
                if known is not None and known != shape:
                    raise ValueError(f"proxy shape {shape} differs from the entry's {known}")
                if self._already_stored(entry, KIND_PROXY, "", pts, blob):
                    return
                self._unmark(entry)
                self._append(entry, KIND_PROXY, self._codec.codec_id, "", pts, blob)
                entry.index.shape = known or shape
                self._after_store(key)

    def proxy(self, key: CacheKey, pts_ticks: int) -> NDArray[np.uint8]:
        """Return one frame's proxy as the store promises (bit-identical for a lossless codec).

        Args:
            key: The source file's cache key.
            pts_ticks: The frame's presentation time in ticks.

        Returns:
            A new array.

        Raises:
            KeyError: Nothing valid is stored for this key and pts (including a record that
                fails its checksum, which is then forgotten).
        """
        pts = _int64(pts_ticks, "pts")
        with self._reading(key, KIND_PROXY, "", pts) as (path, rec):
            _, codec_id, _, _, payload = self._read(key, path, rec, KIND_PROXY, "", pts)
        try:
            return CODECS[codec_id].decode(payload)
        except (ValueError, KeyError, zlib.error, struct.error):
            self._forget(key, KIND_PROXY, "", pts, rec)
            raise KeyError(f"proxy {pts} of {key} is damaged") from None

    def store_source_statistics(
        self, key: CacheKey, stage: str, pts_ticks: int, stats: Statistics
    ) -> None:
        """Store one frame's source-only statistics of a stage, each array with dtype and shape.

        Storing statistics never changes whether the entry is complete.

        Args:
            key: The source file's cache key (current cache version).
            stage: The stage name: a non-empty string.
            pts_ticks: The frame's presentation time in ticks.
            stats: Named boolean, integer or floating-point arrays; nothing is pickled.

        Raises:
            ValueError: The stage name is empty or too long, a dtype is not stored, or the key
                is not storable.
            TypeError: A statistics name is not a string.
            RuntimeError: Another store call on this key is still running.
            OSError: The file cannot be written; the pack is cut back to its last whole record.
        """
        pts = _int64(pts_ticks, "pts")
        self._check_key(key)
        if not isinstance(stage, str) or not stage:
            raise ValueError("a stage name is a non-empty string")
        with self._write_slot(key):
            payload = encode_statistics(stats)
            with self._lock:
                entry = self._entry_for_write(key)
                if self._already_stored(entry, KIND_STATS, stage, pts, payload):
                    return
                self._append(entry, KIND_STATS, 0, stage, pts, payload)
                self._after_store(key)

    def source_statistics(self, key: CacheKey, stage: str, pts_ticks: int) -> Statistics:
        """Return one frame's stored source-only statistics, dtype, shape and bytes exactly.

        Args:
            key: The source file's cache key.
            stage: The stage name.
            pts_ticks: The frame's presentation time in ticks.

        Returns:
            The arrays by name (new, writable).

        Raises:
            KeyError: Nothing valid is stored for this key, stage and pts.
        """
        pts = _int64(pts_ticks, "pts")
        with self._reading(key, KIND_STATS, stage, pts) as (path, rec):
            _, _, _, _, payload = self._read(key, path, rec, KIND_STATS, stage, pts)
        try:
            return decode_statistics(payload)
        except (ValueError, TypeError, struct.error):
            self._forget(key, KIND_STATS, stage, pts, rec)
            raise KeyError(f"statistics {stage!r} at {pts} of {key} are damaged") from None

    def mark_complete(self, key: CacheKey) -> None:
        """Record that the proxy pass for the whole clip is stored (V17).

        The pack is synced, then the completeness marker is written atomically and synced, last.
        The entry's last-use stamp is refreshed. A later new or changed proxy undoes this.

        Args:
            key: The source file's cache key.

        Raises:
            KeyError: No proxy is stored for this key (statistics alone do not make a proxy
                pass), or the entry is being removed.
            RuntimeError: A store call on this key is still running.
            OSError: The pack cannot be synced or the marker cannot be written.
        """
        with self._write_slot(key), self._lock:
            entry = self._entries.get(key)
            if (
                entry is None
                or entry.closing
                or not self._ensure_scanned(entry)
                or not entry.index.proxies
            ):
                raise KeyError(f"no proxy is stored for {key}")
            if self._wentry is entry and self._wfile is not None:
                self._wfile.flush()
                os.fsync(self._wfile.fileno())
                self._close_writer()
            else:
                with entry.pack.open("r+b") as handle:
                    os.fsync(handle.fileno())
            marker = {"valid_length": entry.index.valid_length, "records": entry.index.records}
            atomic_write_text(entry.folder / MARKER_NAME, json.dumps(marker))
            entry.complete = True
            self._touch(entry)
            self._last_store = key
            self._evict({key})

    def limit_bytes(self) -> int:
        """Return the size limit in bytes (the default is ``DEFAULT_CACHE_LIMIT_BYTES``)."""
        with self._lock:
            return self._limit

    def set_limit_bytes(self, n: int) -> None:
        """Set the size limit and evict at once if the cache is over it.

        Args:
            n: The new limit in bytes.

        Raises:
            ValueError: ``n`` is negative.
        """
        if n < 0:
            raise ValueError("the cache limit is not negative")
        with self._lock:
            self._limit = n
            self._evict(set())

    def clear(self) -> None:
        """Remove every cache entry and nothing else.

        Only the files the cache named are deleted, and only as regular files; a link, a foreign
        file or anything outside the cache folder is never touched. An entry whose file is open
        elsewhere stays and is logged.
        """
        with self._lock:
            self._close_writer()
            for entry in list(self._entries.values()):
                if not self._remove_entry(entry):
                    _LOG.warning("cache entry %s could not be removed", entry.folder.name)
            self._discover(purge=True)
            self._last_lookup = None
            self._last_store = None
            self._over_limit_warned = False

    # --- extras -----------------------------------------------------------------------------

    @property
    def cache_version(self) -> int:
        """The cache version of this instance: format number and codec identity (D113)."""
        return self._version

    def key_for(self, path: str | os.PathLike[str]) -> CacheKey:
        """Return the key of a source file for this instance's codec (see ``cache_key``)."""
        info = os.stat(path)
        return CacheKey(info.st_size, info.st_mtime_ns, self._version)

    def close(self) -> None:
        """Close the append handle (the cache stays usable; the next store reopens it)."""
        with self._lock:
            self._close_writer()

    def __enter__(self) -> Self:
        """Return the cache for use in a ``with`` block."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Close the append handle."""
        self.close()

    # --- internals --------------------------------------------------------------------------

    def _check_key(self, key: CacheKey) -> None:
        """Refuse a key that cannot be stored (negative fields, or another cache version)."""
        entry_name(key)
        if key.cache_version != self._version:
            raise ValueError(
                f"cache version {key.cache_version} cannot be stored (current is {self._version})"
            )

    @contextlib.contextmanager
    def _write_slot(self, key: CacheKey) -> Iterator[None]:
        """Claim ``key`` for one store call; an overlapping second call is a RuntimeError."""
        with self._lock:
            if key in self._writing:
                raise RuntimeError(f"another store call on {key} is still running")
            self._writing.add(key)
        try:
            yield
        finally:
            with self._lock:
                self._writing.discard(key)

    def _discover(self, purge: bool = False) -> None:
        """Read the cache folder: register entries, remove those that can never match.

        Args:
            purge: Remove every entry-named folder found (used by ``clear``).
        """
        try:
            items = list(os.scandir(self._folder))
        except OSError:
            return
        for item in items:
            if item.is_symlink() or item.is_junction() or not item.is_dir(follow_symlinks=False):
                continue
            key = parse_entry_name(item.name)
            if key is None or key in self._entries:
                continue
            folder = Path(item.path)
            if purge or key.cache_version != self._version:
                self._remove_or_retain(key, folder)
                continue
            self._register(key, folder)

    def _remove_or_retain(self, key: CacheKey, folder: Path) -> None:
        """Remove an entry folder found on disk, or keep it marked for removal if that fails.

        A kept entry is counted, never served, the first to be evicted and retried like any
        other failed removal; its ``removing`` file makes the next open try again.
        """
        if _remove_files(folder):
            return
        try:
            size = (folder / PACK_NAME).stat().st_size
        except OSError:
            size = 0
        entry = _Entry(key, folder, size)
        self._entries[key] = entry
        self._mark_for_removal(entry)

    def _register(self, key: CacheKey, folder: Path) -> None:
        """Add a found entry folder to the table, or remove it when its pack is unreadable."""
        with contextlib.suppress(OSError):
            for item in os.scandir(folder):
                if item.name.endswith(TEMP_SUFFIX) and _is_cache_file(item.name):
                    with contextlib.suppress(OSError):
                        os.unlink(item.path)
        pack = folder / PACK_NAME
        try:
            with pack.open("rb") as handle:
                check_pack_header(handle.read(PACK_HEADER_SIZE), key)
            size = pack.stat().st_size
        except (PackError, OSError):
            self._remove_or_retain(key, folder)
            return
        marked = (folder / REMOVING_NAME).exists()
        if marked and _remove_files(folder):
            return
        entry = _Entry(key, folder, size, stamp=read_stamp(folder / META_NAME), closing=marked)
        entry.aux_size = self._aux_size(folder)
        self._entries[key] = entry

    @staticmethod
    def _aux_size(folder: Path) -> int:
        """Return the bytes of an entry's marker and meta files."""
        total = 0
        for name in (MARKER_NAME, META_NAME, REMOVING_NAME):
            with contextlib.suppress(OSError):
                total += (folder / name).stat().st_size
        return total

    def _ensure_scanned(self, entry: _Entry) -> bool:
        """Build the entry's index from its pack on first use; False (entry dropped) if unusable."""
        if entry.scanned:
            return True
        marker = read_marker(entry.folder / MARKER_NAME)
        marked = marker.get("valid_length") if marker else None
        try:
            index = scan_pack(entry.pack, entry.key, marked if isinstance(marked, int) else 0)
        except (PackError, OSError) as error:
            _LOG.warning("cache entry %s is unusable: %s", entry.folder.name, error)
            self._remove_entry(entry)
            return False
        entry.index = index
        entry.complete = marker is not None and marker_valid(
            marker, index.valid_length, index.records_before_marker
        )
        if marker is not None and not entry.complete:
            self._void_marker(entry)
        entry.scanned = True
        return True

    def _entry_for_write(self, key: CacheKey) -> _Entry:
        """Return an appendable entry, refusing a linked or nondirectory entry path.

        Raises:
            OSError: The entry path is a symlink, junction or existing nondirectory,
                or the entry cannot be made ready for writing. A refused path and
                its target are left untouched.
        """
        folder = self._folder / entry_name(key)
        if (
            folder.is_symlink()
            or folder.is_junction()
            or (os.path.lexists(folder) and not folder.is_dir())
        ):
            reason = f"refusing cache entry path {folder}: it is a link or not a directory"
            _LOG.warning("%s", reason)
            raise OSError(reason)
        entry = self._entries.get(key)
        if entry is not None and entry.closing and not self._remove_entry(entry):
            raise OSError(f"the cache entry of {key} is marked for removal and cannot be replaced")
        entry = self._entries.get(key)
        if entry is not None and self._ensure_scanned(entry):
            return entry
        folder.mkdir(parents=True, exist_ok=True)
        entry = _Entry(key, folder, PACK_HEADER_SIZE, scanned=True)
        self._void_stale_marks(entry)
        pack = folder / PACK_NAME
        with pack.open("wb") as handle:
            handle.write(pack_header(key))
            handle.flush()
        self._entries[key] = entry
        self._touch(entry)
        return entry

    def _void_stale_marks(self, entry: _Entry) -> None:
        """Void the marker files an earlier entry of this key left, before a new pack is made.

        A leftover ``removing`` file would get the new pack removed at the next open, and a
        leftover ``complete`` file could vouch for a pack that is not the one it described.

        Raises:
            OSError: A removal mark cannot be deleted (no pack is made under it).
        """
        if not _unlink(str(entry.folder / REMOVING_NAME)):
            raise OSError(f"the removal mark of {entry.folder.name} cannot be deleted")
        self._void_marker(entry)

    def _touch(self, entry: _Entry) -> None:
        """Refresh the entry's last-use stamp, in memory and in ``meta.json``."""
        entry.stamp = self._clock()
        try:
            atomic_write_text(entry.folder / META_NAME, json.dumps({"last_used_ns": entry.stamp}))
        except OSError as error:
            _LOG.warning("cache stamp of %s not saved: %s", entry.folder.name, error)
        entry.aux_size = self._aux_size(entry.folder)

    def _unmark(self, entry: _Entry) -> None:
        """Remove the completeness marker (before a proxy is added to a complete entry)."""
        if not entry.complete:
            return
        (entry.folder / MARKER_NAME).unlink(missing_ok=True)
        entry.complete = False
        entry.aux_size = self._aux_size(entry.folder)

    def _lose_completeness(self, entry: _Entry) -> None:
        """Make a complete entry incomplete because one of its proxies turned out to be damaged.

        The marker is removed so that a new instance does not believe it either; if it cannot be
        removed it is overwritten with one that vouches for nothing. If both fail the entry is
        still incomplete in this instance.
        """
        entry.complete = False
        self._void_marker(entry)

    def _void_marker(self, entry: _Entry) -> None:
        """Make the entry's completeness marker useless: delete it, else overwrite it with ``{}``.

        Overwriting is tried atomically and then in place (a lock that refuses the delete may
        refuse the replace too). If all three fail a warning is logged and a new instance would
        believe the marker if the pack still matches it.
        """
        marker = entry.folder / MARKER_NAME
        if not _unlink(str(marker)) and not _write_small(marker, "{}"):
            _LOG.warning("cache marker of %s could not be voided", entry.folder.name)
        entry.aux_size = self._aux_size(entry.folder)

    def _already_stored(
        self, entry: _Entry, kind: int, stage: str, pts: int, payload: bytes
    ) -> bool:
        """Return whether this exact payload is already stored for the frame (a re-store)."""
        rec = (
            entry.index.proxies.get(pts)
            if kind == KIND_PROXY
            else entry.index.stats.get(stage, {}).get(pts)
        )
        if rec is None:
            return False
        try:
            _, codec_id, _, _, old = read_record(entry.pack, rec)
        except (PackError, OSError):
            return False
        wanted = self._codec.codec_id if kind == KIND_PROXY else 0
        return old == payload and codec_id == wanted

    def _writer(self, entry: _Entry) -> BinaryIO:
        """Return the append handle for ``entry``, cutting any torn tail off first."""
        if self._wentry is entry and self._wfile is not None:
            return self._wfile
        self._close_writer()
        handle = entry.pack.open("r+b")
        try:
            handle.seek(entry.index.valid_length)
            handle.truncate()
        except OSError:
            handle.close()
            raise
        entry.pack_size = entry.index.valid_length
        self._wentry, self._wfile = entry, handle
        return handle

    def _close_writer(self) -> None:
        """Close the append handle if one is open."""
        handle, self._wfile, self._wentry = self._wfile, None, None
        if handle is not None:
            with contextlib.suppress(OSError):
                handle.close()

    def _append(
        self, entry: _Entry, kind: int, codec_id: int, stage: str, pts: int, payload: bytes
    ) -> None:
        """Append one record, flush it, and only then publish it in the index."""
        record = encode_record(kind, codec_id, stage, pts, payload)
        handle = self._writer(entry)
        offset = entry.index.valid_length
        try:
            handle.seek(offset)
            handle.write(record)
            handle.flush()
        except OSError:
            with contextlib.suppress(OSError):
                handle.seek(offset)
                handle.truncate()
            self._close_writer()
            with contextlib.suppress(OSError):
                entry.pack_size = entry.pack.stat().st_size  # a tail that stayed is counted
            raise
        rec = Rec(offset, len(record), codec_id)
        if kind == KIND_PROXY:
            entry.index.proxies[pts] = rec
        else:
            entry.index.stats.setdefault(stage, {})[pts] = rec
        entry.index.valid_length = offset + len(record)
        entry.index.records += 1
        entry.pack_size = entry.index.valid_length

    def _after_store(self, key: CacheKey) -> None:
        """Pin the entry just written and apply the limit."""
        self._last_store = key
        self._evict({key})

    @contextlib.contextmanager
    def _reading(
        self, key: CacheKey, kind: int, stage: str, pts: int
    ) -> Iterator[tuple[Path, Rec]]:
        """Yield the pack path and record of a frame, counting the caller as a reader of its entry.

        Removing the entry (eviction, ``clear``) waits for its readers, so a file that is open for
        one seek and read is never what makes a removal fail. Raises KeyError as :meth:`_find`.
        """
        with self._lock:
            found = self._find(key, kind, stage, pts)
            self._active_reads[key] = self._active_reads.get(key, 0) + 1
        try:
            yield found
        finally:
            with self._lock:
                left = self._active_reads[key] - 1
                if left:
                    self._active_reads[key] = left
                else:
                    del self._active_reads[key]
                    self._idle.notify_all()

    def _find(self, key: CacheKey, kind: int, stage: str, pts: int) -> tuple[Path, Rec]:
        """Return the pack path and record of a frame, or raise KeyError."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is not None and entry.closing:
                raise KeyError(f"the cache entry of {key} is being removed")
            if entry is None or not self._ensure_scanned(entry):
                raise KeyError(f"nothing is cached for {key}")
            rec = (
                entry.index.proxies.get(pts)
                if kind == KIND_PROXY
                else entry.index.stats.get(stage, {}).get(pts)
            )
            if rec is None:
                raise KeyError(f"nothing is cached for {key} {stage!r} at {pts}")
            return entry.pack, rec

    def _read(
        self, key: CacheKey, path: Path, rec: Rec, kind: int, stage: str, pts: int
    ) -> tuple[int, int, str, int, bytes]:
        """Read a record outside the lock; a failed checksum is forgotten and raised as KeyError."""
        try:
            got = read_record(path, rec)
        except OSError:
            raise KeyError(f"the cache file of {key} cannot be read") from None
        except PackError:
            self._forget(key, kind, stage, pts, rec)
            raise KeyError(f"a record of {key} at {pts} is damaged") from None
        if got[0] != kind or got[2] != stage or got[3] != pts:
            self._forget(key, kind, stage, pts, rec)
            raise KeyError(f"a record of {key} at {pts} is not the one indexed")
        return got

    def _forget(self, key: CacheKey, kind: int, stage: str, pts: int, rec: Rec) -> None:
        """Drop a damaged record from the index (if it is still the indexed one)."""
        with self._lock:
            entry = self._entries.get(key)
            if entry is None:
                return
            table = entry.index.proxies if kind == KIND_PROXY else entry.index.stats.get(stage, {})
            if table.get(pts) == rec:
                del table[pts]
                if kind == KIND_PROXY:
                    entry.index.shape = self._surviving_shape(entry)
                    self._lose_completeness(entry)

    @staticmethod
    def _surviving_shape(entry: _Entry) -> tuple[int, int, int] | None:
        """Return the shape the entry's remaining proxies have (None when it has none).

        The shape of a scanned entry comes from its first proxy record, whose prefix is not
        checked; once a record is forgotten the shape is read again from the first proxy that
        still reads, so that a damaged first record does not bind the shape of the next store.
        """
        for rec in sorted(entry.index.proxies.values(), key=lambda found: found.offset):
            codec = CODECS.get(rec.codec_id)
            if codec is None:
                continue
            try:
                with entry.pack.open("rb") as handle:
                    handle.seek(rec.offset + RECORD_HEADER_SIZE)  # a proxy has no stage name
                    return codec.shape(handle.read(SHAPE_PREFIX_BYTES))
            except OSError:
                return None
            except ValueError:
                continue
        return None

    def _total(self) -> int:
        """Return the bytes all entries occupy."""
        return sum(entry.size_bytes for entry in self._entries.values())

    def _remove_entry(self, entry: _Entry) -> bool:
        """Delete an entry's files and forget it; False when it could not be removed."""
        if self._wentry is entry:
            self._close_writer()
        entry.closing = True  # no new reader starts; readers already reading finish their read
        deadline = time.monotonic() + _READER_WAIT
        while self._active_reads.get(entry.key, 0) > 0:
            left = deadline - time.monotonic()
            if left <= 0:
                break
            self._idle.wait(left)
        if self._entries.get(entry.key) is not entry:
            return True  # the wait let go of the lock: another call removed or replaced the entry
        if not _remove_files(entry.folder):
            self._mark_for_removal(entry)
            return False
        self._entries.pop(entry.key, None)
        return True

    def _mark_for_removal(self, entry: _Entry) -> None:
        """Leave an entry that could not be removed marked for removal: logged, never silently kept.

        The entry is not served any more and is the first to go at the next eviction or ``clear``;
        a marker file in its folder makes the next open remove it too.
        """
        entry.closing = True
        try:
            entry.pack_size = entry.pack.stat().st_size
        except FileNotFoundError:
            entry.pack_size = 0  # the pack went and a small file stayed: do not count the pack
        except OSError:
            pass
        _LOG.warning(
            "cache entry %s could not be removed; it is marked for removal", entry.folder.name
        )
        if not _write_small(entry.folder / REMOVING_NAME, "removing"):
            _LOG.warning("removal mark of %s not written", entry.folder.name)
        entry.aux_size = self._aux_size(entry.folder)

    def _evict(self, protected: set[CacheKey]) -> None:
        """Evict oldest-first until the total fits the limit or only pinned entries remain."""
        pinned = set(protected) | self._writing
        for key in (self._last_lookup, self._last_store):
            if key is not None:
                pinned.add(key)
        if self._total() > self._limit:
            victims = sorted(
                (e for e in self._entries.values() if e.key not in pinned), key=_eviction_key
            )
            for entry in victims:
                if self._total() <= self._limit:
                    break
                self._remove_entry(entry)
        if self._total() > self._limit:
            if not self._over_limit_warned:
                _LOG.warning(
                    "the cache holds %d bytes over its limit of %d: the entry in use is kept",
                    self._total(),
                    self._limit,
                )
                self._over_limit_warned = True
        else:
            self._over_limit_warned = False
