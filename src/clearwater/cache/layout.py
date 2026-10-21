"""The on-disk layout of one cache entry: a pack file of checked records (WP3.12).

An entry is a folder holding ``data.pack`` (a header, then append-only records), ``complete``
(the completeness marker, present only after the proxy pass was recorded) and ``meta.json``
(the last-use stamp). Each record is ``header + stage name + payload`` with a CRC-32 over all
of it, so a torn tail or a damaged record is found by length or checksum and never served.
There is no separate index file: the in-memory index is rebuilt by :func:`scan_pack`.
"""

from __future__ import annotations

import json
import struct
import zlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
from numpy.typing import NDArray

from clearwater.interfaces.cache import CacheKey
from clearwater.interfaces.method import Statistics

from .codec import CODECS, SHAPE_PREFIX_BYTES

PACK_NAME = "data.pack"
MARKER_NAME = "complete"
META_NAME = "meta.json"
REMOVING_NAME = "removing"
TEMP_SUFFIX = ".tmp"
CACHE_FILE_NAMES = frozenset({PACK_NAME, MARKER_NAME, META_NAME, REMOVING_NAME})
"""The file names the cache writes into an entry folder (plus ``*.tmp`` temporaries)."""

PACK_MAGIC = b"CWPK"
PACK_FORMAT = 2
KIND_PROXY = 1
KIND_STATS = 2
RECORD_MAGIC = b"CR"

_PACK_HEADER = struct.Struct("<4sH2xqqq")
_RECORD = struct.Struct("<2sBBH2xqII")
PACK_HEADER_SIZE = _PACK_HEADER.size
RECORD_HEADER_SIZE = _RECORD.size
_CRC_OFFSET = RECORD_HEADER_SIZE - 4


class PackError(Exception):
    """A pack file is unreadable, of another key, or damaged beyond use."""


@dataclass(frozen=True)
class Rec:
    """Where one record sits in the pack.

    Attributes:
        offset: Start of the record header.
        length: Total bytes of header, stage name and payload.
        codec_id: The codec id of a proxy record (0 for statistics).
    """

    offset: int
    length: int
    codec_id: int


@dataclass
class PackIndex:
    """What a scan of a pack found.

    Attributes:
        valid_length: The end of the last valid record (or of the header).
        records: How many valid records the pack holds (superseded ones included).
        proxies: The proxy record of each pts (the newest wins).
        stats: The statistics record of each stage and pts (the newest wins).
        shape: ``(H, W, 3)`` of the first proxy, or None before one is stored.
        records_before_marker: Valid records ending at or before the marker length asked for.
    """

    valid_length: int = PACK_HEADER_SIZE
    records: int = 0
    proxies: dict[int, Rec] = field(default_factory=dict)
    stats: dict[str, dict[int, Rec]] = field(default_factory=dict)
    shape: tuple[int, int, int] | None = None
    records_before_marker: int = 0


def pack_header(key: CacheKey) -> bytes:
    """Return the 32-byte header of a new pack of ``key``."""
    return _PACK_HEADER.pack(PACK_MAGIC, PACK_FORMAT, key.size, key.mtime_ns, key.cache_version)


def check_pack_header(raw: bytes, key: CacheKey) -> None:
    """Check that ``raw`` is the header of a pack of ``key``.

    Args:
        raw: The first bytes of the file.
        key: The key the pack must belong to.

    Raises:
        PackError: Short, wrong magic or format, or another key.
    """
    if len(raw) < PACK_HEADER_SIZE:
        raise PackError("pack header is short")
    magic, version, size, mtime_ns, cache_version = _PACK_HEADER.unpack(raw[:PACK_HEADER_SIZE])
    if magic != PACK_MAGIC or version != PACK_FORMAT:
        raise PackError("not a cache pack of this format")
    if CacheKey(size, mtime_ns, cache_version) != key:
        raise PackError("the pack belongs to another key")


def encode_record(kind: int, codec_id: int, stage: str, pts: int, payload: bytes) -> bytes:
    """Return one record: header, stage name (UTF-8) and payload, checksummed.

    Args:
        kind: :data:`KIND_PROXY` or :data:`KIND_STATS`.
        codec_id: The proxy codec id (0 for statistics).
        stage: The stage name ("" for a proxy).
        pts: The frame's pts ticks.
        payload: The record body.

    Returns:
        The bytes to append.

    Raises:
        ValueError: The stage name is longer than 65535 bytes.
    """
    name = stage.encode("utf-8")
    if len(name) > 0xFFFF:
        raise ValueError("a stage name is at most 65535 bytes")
    head = _RECORD.pack(RECORD_MAGIC, kind, codec_id, len(name), pts, len(payload), 0)
    crc = zlib.crc32(payload, zlib.crc32(name, zlib.crc32(head[:_CRC_OFFSET])))
    return head[:_CRC_OFFSET] + struct.pack("<I", crc) + name + payload


def _parse_head(raw: bytes) -> tuple[int, int, int, int, int, int]:
    """Return (kind, codec_id, stage_len, pts, payload_len, crc) of a record header."""
    magic, kind, codec_id, stage_len, pts, payload_len, crc = _RECORD.unpack(raw)
    if magic != RECORD_MAGIC or kind not in (KIND_PROXY, KIND_STATS):
        raise PackError("bad record header")
    return kind, codec_id, stage_len, pts, payload_len, crc


def decode_record(raw: bytes) -> tuple[int, int, str, int, bytes]:
    """Check and split one whole record.

    Args:
        raw: The record bytes, as read from the pack.

    Returns:
        ``(kind, codec_id, stage, pts, payload)``.

    Raises:
        PackError: The record is short, malformed or fails its checksum.
    """
    if len(raw) < RECORD_HEADER_SIZE:
        raise PackError("short record")
    kind, codec_id, stage_len, pts, payload_len, crc = _parse_head(raw[:RECORD_HEADER_SIZE])
    if len(raw) != RECORD_HEADER_SIZE + stage_len + payload_len:
        raise PackError("record length does not match its header")
    body = raw[RECORD_HEADER_SIZE:]
    if zlib.crc32(body, zlib.crc32(raw[:_CRC_OFFSET])) != crc:
        raise PackError("record checksum mismatch")
    try:
        stage = body[:stage_len].decode("utf-8")
    except UnicodeDecodeError as error:
        raise PackError("record stage name is not UTF-8") from error
    return kind, codec_id, stage, pts, body[stage_len:]


def read_record(path: Path, rec: Rec) -> tuple[int, int, str, int, bytes]:
    """Read and verify the record at ``rec`` from the pack at ``path``.

    Args:
        path: The pack file.
        rec: Where the record sits.

    Returns:
        ``(kind, codec_id, stage, pts, payload)``, as :func:`decode_record`.

    Raises:
        PackError: The record fails its checks.
        OSError: The file cannot be read.
    """
    with path.open("rb") as handle:
        handle.seek(rec.offset)
        raw = handle.read(rec.length)
    return decode_record(raw)


def scan_pack(path: Path, key: CacheKey, marker_length: int = 0) -> PackIndex:
    """Rebuild the index of a pack by walking its record headers.

    The payloads are not read, except the first bytes of the first proxy (its shape) and the
    whole of the last record, whose checksum is verified so that a torn tail is cut off. If
    that last record had replaced an earlier one for the same frame, the frame becomes a miss.

    Args:
        path: The pack file.
        key: The key the pack must belong to.
        marker_length: A completeness marker's ``valid_length``; the records ending at or before
            it are counted in :attr:`PackIndex.records_before_marker`.

    Returns:
        The index; ``valid_length`` is where the next record belongs.

    Raises:
        PackError: The header is unreadable or of another key.
        OSError: The file cannot be read.
    """
    index = PackIndex()
    last: tuple[Rec, str] | None = None
    with path.open("rb") as handle:
        handle.seek(0, 2)
        size = handle.tell()
        handle.seek(0)
        check_pack_header(handle.read(PACK_HEADER_SIZE), key)
        offset = PACK_HEADER_SIZE
        while True:
            handle.seek(offset)
            raw = handle.read(RECORD_HEADER_SIZE)
            if len(raw) < RECORD_HEADER_SIZE:
                break
            try:
                kind, codec_id, stage_len, pts, payload_len, _ = _parse_head(raw)
            except PackError:
                break
            length = RECORD_HEADER_SIZE + stage_len + payload_len
            if offset + length > size:
                break
            stage_raw = handle.read(stage_len)
            try:
                stage = stage_raw.decode("utf-8")
            except UnicodeDecodeError:
                break
            rec = Rec(offset, length, codec_id if kind == KIND_PROXY else 0)
            if kind == KIND_PROXY:
                if codec_id not in CODECS:
                    break
                if index.shape is None:
                    prefix = handle.read(min(payload_len, SHAPE_PREFIX_BYTES))
                    try:
                        index.shape = CODECS[codec_id].shape(prefix)
                    except ValueError:
                        break
                index.proxies[pts] = rec
            else:
                index.stats.setdefault(stage, {})[pts] = rec
            index.records += 1
            offset += length
            if offset <= marker_length:
                index.records_before_marker += 1
            last = (rec, stage)
        index.valid_length = offset
        if last is not None:
            rec, stage = last
            handle.seek(rec.offset)
            try:
                decode_record(handle.read(rec.length))
            except PackError:
                _drop_last(index, rec, stage, marker_length)
    return index


def _drop_last(index: PackIndex, rec: Rec, stage: str, marker_length: int) -> None:
    """Remove the torn last record from a scanned index."""
    index.valid_length = rec.offset
    index.records -= 1
    if rec.offset + rec.length <= marker_length:
        index.records_before_marker -= 1
    for pts, found in list(index.proxies.items()):
        if found == rec:
            del index.proxies[pts]
    if not index.proxies:
        index.shape = None  # no proxy is left to bind the shape of the next
    for pts, found in list(index.stats.get(stage, {}).items()):
        if found == rec:
            del index.stats[stage][pts]
            if not index.stats[stage]:
                del index.stats[stage]


def marker_valid(marker: Mapping[str, object], valid_length: int, records_before: int) -> bool:
    """Return whether a completeness marker still describes the pack.

    The pack must reach the marked length and hold exactly the marked number of records up to it.

    Args:
        marker: The parsed marker (``valid_length`` and ``records``).
        valid_length: The valid length found by the scan.
        records_before: The valid records found ending at or before the marked length.

    Returns:
        True when the marker can be believed.
    """
    marked = marker.get("valid_length")
    count = marker.get("records")
    if not isinstance(marked, int) or not isinstance(count, int):
        return False
    return marked <= valid_length and records_before == count


def read_marker(path: Path) -> dict[str, object] | None:
    """Return the parsed completeness marker, or None when absent or unreadable."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


def read_stamp(path: Path) -> int:
    """Return the last-use stamp from ``meta.json``, or 0 when absent or unreadable."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        stamp = data["last_used_ns"]
    except (OSError, ValueError, KeyError, TypeError):
        return 0
    return stamp if isinstance(stamp, int) and not isinstance(stamp, bool) else 0


# --- statistics records ---------------------------------------------------------------------------

_KINDS = "biuf"


def encode_statistics(stats: Statistics) -> bytes:
    """Encode named arrays exactly: name, ``dtype.str``, shape and the raw C-order bytes.

    Args:
        stats: The statistics.

    Returns:
        The record payload. Nothing is pickled.

    Raises:
        TypeError: A name is not a string.
        ValueError: A dtype is not boolean, integer or floating point, or a name is too long.
    """
    if len(stats) > 0xFFFF:
        raise ValueError("a statistics record holds at most 65535 arrays")
    parts = [struct.pack("<H", len(stats))]
    for name, value in stats.items():
        if not isinstance(name, str):
            raise TypeError("statistics names are strings")
        array = np.asarray(value, order="C")
        if array.dtype.kind not in _KINDS:
            raise ValueError(f"statistics {name!r}: dtype {array.dtype} is not stored")
        raw_name = name.encode("utf-8")
        dtype = array.dtype.str.encode("ascii")
        if len(raw_name) > 255 or array.ndim > 255:
            raise ValueError(f"statistics {name!r}: name or rank too long")
        parts.append(struct.pack("<B", len(raw_name)) + raw_name)
        parts.append(struct.pack("<B", len(dtype)) + dtype)
        parts.append(struct.pack("<B", array.ndim) + struct.pack(f"<{array.ndim}Q", *array.shape))
        parts.append(array.tobytes())
    return b"".join(parts)


def decode_statistics(payload: bytes) -> dict[str, NDArray[np.generic]]:
    """Invert :func:`encode_statistics`: owned arrays of the stored dtype and shape.

    Args:
        payload: A record payload.

    Returns:
        The arrays by name, in stored order.

    Raises:
        ValueError: The payload is malformed.
    """
    view = memoryview(payload)
    position = 0

    def take(count: int) -> memoryview:
        nonlocal position
        if position + count > len(view):
            raise ValueError("statistics record is truncated")
        chunk = view[position : position + count]
        position += count
        return chunk

    (count,) = struct.unpack("<H", take(2))
    result: dict[str, NDArray[np.generic]] = {}
    for _ in range(count):
        name = bytes(take(struct.unpack("<B", take(1))[0])).decode("utf-8")
        dtype = np.dtype(bytes(take(struct.unpack("<B", take(1))[0])).decode("ascii"))
        if dtype.kind not in _KINDS:
            raise ValueError("statistics record names an unsupported dtype")
        (ndim,) = struct.unpack("<B", take(1))
        shape = struct.unpack(f"<{ndim}Q", take(8 * ndim))
        items = 1
        for dim in shape:
            items *= dim
        raw = take(items * dtype.itemsize)
        result[name] = np.frombuffer(raw, dtype=dtype).reshape(shape).copy()
    if position != len(view):
        raise ValueError("statistics record has trailing bytes")
    return result
