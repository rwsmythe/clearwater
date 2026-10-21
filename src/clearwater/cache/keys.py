"""Cache keys and entry-folder names (IF-7; D71, D113).

A key is the source file's size and modification time plus the cache format version. The
folder name of an entry carries all three fields, so an entry of another size, another
modification time or another version can never be found by a lookup.
"""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path

from clearwater.interfaces.cache import CacheKey

from .codec import CODECS, DEFAULT_CODEC, ProxyCodec

CACHE_FORMAT_VERSION = 2
"""The cache format number (D113). A key's version also carries the codec identity."""

_NAME = re.compile(r"^e_(\d+)_(-?\d+)_(\d+)$")


def codec_cache_version(codec: ProxyCodec = DEFAULT_CODEC) -> int:
    """Return the cache version of entries written with ``codec`` (D113, AD-5 ruling).

    The version folds the format number and the codec identity (the JPEG library versions, read
    now), so a different decoder gives a different version and the old entries can never match:
    ``format number << 48 | the first 48 bits of the SHA-256 of the codec id and identity``.

    A codec whose encoder is not the registered one for its id (a test hook, a variant) gets a
    version of its own, bound to this process: whatever it writes can never be served to the
    registered codec, nor to another process.

    Args:
        codec: The store codec.

    Returns:
        A positive integer that fits the pack header.
    """
    text = f"{codec.codec_id}:{codec.identity()}"
    registered = CODECS.get(codec.codec_id)
    if registered is None or registered.encode is not codec.encode:
        text += f":own-encoder:{os.getpid()}:{id(codec.encode):x}"
    digest = hashlib.sha256(text.encode()).digest()
    return (CACHE_FORMAT_VERSION << 48) | int.from_bytes(digest[:6], "big")


def cache_key(path: str | os.PathLike[str], codec: ProxyCodec = DEFAULT_CODEC) -> CacheKey:
    """Return the cache key of a source file: its size, modification time and the cache version.

    The file is not opened; only its metadata is read. Two different files with the same size
    and modification time share a key (D71's definition; a stated limit of the cache).

    Args:
        path: The source file.
        codec: The store codec whose version the key carries (the cache's default codec).

    Returns:
        The key, with ``cache_version`` set to :func:`codec_cache_version`.

    Raises:
        OSError: The file cannot be examined.
    """
    info = os.stat(path)
    return CacheKey(
        size=info.st_size, mtime_ns=info.st_mtime_ns, cache_version=codec_cache_version(codec)
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
