"""Cache keys and entry-folder names (IF-7; D71, D113).

A key is the source file's size and modification time plus the cache format version. The
folder name of an entry carries all three fields, so an entry of another size, another
modification time or another version can never be found by a lookup.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

from clearwater.interfaces.cache import CacheKey

CACHE_FORMAT_VERSION = 1
"""The cache format version (D113). Entries of any other version are removed when a cache opens."""

_NAME = re.compile(r"^e_(\d+)_(-?\d+)_(\d+)$")


def cache_key(path: str | os.PathLike[str]) -> CacheKey:
    """Return the cache key of a source file: its size, modification time and the format version.

    The file is not opened; only its metadata is read. Two different files with the same size
    and modification time share a key (D71's definition; a stated limit of the cache).

    Args:
        path: The source file.

    Returns:
        The key, with ``cache_version`` set to :data:`CACHE_FORMAT_VERSION`.

    Raises:
        OSError: The file cannot be examined.
    """
    info = os.stat(path)
    return CacheKey(
        size=info.st_size, mtime_ns=info.st_mtime_ns, cache_version=CACHE_FORMAT_VERSION
    )


def entry_name(key: CacheKey) -> str:
    """Return the folder name of a key's entry: ``e_<size>_<mtime_ns>_<version>``.

    Args:
        key: The cache key.

    Returns:
        The name; it holds every key field.

    Raises:
        ValueError: The size or the version is negative.
    """
    if key.size < 0 or key.cache_version < 0:
        raise ValueError(f"a cache key has a non-negative size and version, got {key}")
    return f"e_{key.size}_{key.mtime_ns}_{key.cache_version}"


def parse_entry_name(name: str) -> CacheKey | None:
    """Return the key an entry-folder name stands for, or None when it is not an entry name.

    Args:
        name: A folder name found in the cache folder.

    Returns:
        The key, or None for a name the cache did not give.
    """
    found = _NAME.match(name)
    if found is None:
        return None
    return CacheKey(int(found.group(1)), int(found.group(2)), int(found.group(3)))


def is_link(path: Path) -> bool:
    """Return True for a symbolic link or a Windows junction (never followed by the cache)."""
    return path.is_symlink() or os.path.isjunction(path)
