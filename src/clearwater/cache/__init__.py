"""The proxy cache (IF-7, WP3.12): analysis proxies and source-only statistics on disk.

``DiskProxyCache`` implements :class:`clearwater.interfaces.cache.ProxyCache` over a folder it
owns; ``cache_key`` derives the key of a source file from its size and modification time.
Depends only on the standard library, NumPy, :mod:`clearwater.interfaces` and
:mod:`clearwater.config.atomic` (never on the GUI, jobs, methods, io or core packages).
"""

from __future__ import annotations

from .codec import CODECS, DEFAULT_CODEC, DEFLATE, ProxyCodec
from .keys import CACHE_FORMAT_VERSION, cache_key, entry_name, parse_entry_name
from .store import DiskProxyCache

__all__ = [
    "CACHE_FORMAT_VERSION",
    "CODECS",
    "DEFAULT_CODEC",
    "DEFLATE",
    "DiskProxyCache",
    "ProxyCodec",
    "cache_key",
    "entry_name",
    "parse_entry_name",
]
