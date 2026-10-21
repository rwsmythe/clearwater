"""WP3.12 tests: crash safety, damaged files, threads and the dependency rule of the cache."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import clearwater.cache.store as store_module
from clearwater.cache import (
    DEFLATE,
    DiskProxyCache,
    ProxyCodec,
    codec_cache_version,
    entry_name,
)
from clearwater.interfaces.cache import CacheKey

VERSION = codec_cache_version(DEFLATE)
KEY = CacheKey(4242, 1_700_000_000_000_000_000, VERSION)


def lossless_cache(folder: Path, limit: int = 20 * 10**9, **kw: Any) -> DiskProxyCache:
    """Open a cache with the lossless codec (these tests assume bit-identical proxies)."""
    kw.setdefault("codec", DEFLATE)
    return DiskProxyCache(folder, limit, **kw)


SHAPE = (6, 8, 3)


def pixels(seed: int) -> np.ndarray:
    """Return the reproducible proxy of ``seed``."""
    return np.random.default_rng(seed).integers(0, 256, SHAPE, dtype=np.uint8)


def pack_of(folder: Path) -> Path:
    """Return the pack file of KEY's entry."""
    return folder / entry_name(KEY) / "data.pack"


def assert_consistent(cache: DiskProxyCache) -> None:
    """Every pts the cache lists reads back bit-identical (pts is the seed)."""
    found = cache.lookup(KEY)
    assert found is not None
    assert list(found.pts_ticks) == sorted(found.pts_ticks)
    for pts in found.pts_ticks:
        assert cache.proxy(KEY, pts).tobytes() == pixels(pts).tobytes()


CHILD = """
import sys, time
import numpy as np
from clearwater.cache import DEFLATE, DiskProxyCache
from clearwater.interfaces.cache import CacheKey
folder, size, mtime, version, limit = sys.argv[1:6]
key = CacheKey(int(size), int(mtime), int(version))
cache = DiskProxyCache(__import__('pathlib').Path(folder), codec=DEFLATE)
def pixels(seed):
    return np.random.default_rng(seed).integers(0, 256, (6, 8, 3), dtype=np.uint8)
n = 0
while True:
    cache.store_proxy(key, n, pixels(n))
    cache.store_source_statistics(key, 's', n, {'means': np.full(3, float(n))})
    n += 1
    if n == 6:
        print('READY', flush=True)
    if n >= int(limit):
        time.sleep(60)
"""


def run_and_kill(folder: Path, limit: int) -> None:
    """Run a child that stores frames, kill it hard once it has stored six, and wait for it."""
    child = subprocess.Popen(
        [
            sys.executable,
            "-c",
            CHILD,
            str(folder),
            str(KEY.size),
            str(KEY.mtime_ns),
            str(KEY.cache_version),
            str(limit),
        ],
        stdout=subprocess.PIPE,
        text=True,
    )
    try:
        assert child.stdout is not None
        assert child.stdout.readline().strip() == "READY"
        if limit > 1000:
            threading.Event().wait(0.3)  # let it run on, so the kill may land mid-append
    finally:
        child.kill()
        child.wait(timeout=30)


def test_a_killed_writer_leaves_an_incomplete_entry_that_can_be_finished(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    run_and_kill(folder, limit=6)
    cache = lossless_cache(folder)
    found = cache.lookup(KEY)
    assert found is not None
    assert found.complete is False
    assert found.pts_ticks == (0, 1, 2, 3, 4, 5)
    assert_consistent(cache)
    on_disk = sum(p.stat().st_size for p in (folder / entry_name(KEY)).iterdir())
    assert found.size_bytes == on_disk  # the partial entry's bytes are counted
    for pts in range(6, 9):  # a fresh store to the same key carries on and completes it
        cache.store_proxy(KEY, pts, pixels(pts))
    cache.mark_complete(KEY)
    cache.close()
    finished = lossless_cache(folder).lookup(KEY)
    assert finished is not None and finished.complete
    assert finished.pts_ticks == tuple(range(9))


def test_a_writer_killed_at_any_moment_never_breaks_the_reader(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    run_and_kill(folder, limit=10**9)
    cache = lossless_cache(folder)
    found = cache.lookup(KEY)
    assert found is not None and found.complete is False
    assert len(found.pts_ticks) >= 6
    assert_consistent(cache)
    pack = pack_of(folder)
    cache.store_proxy(KEY, 10**6, pixels(10**6 % 997))  # appending cuts any torn tail off first
    cache.close()
    assert lossless_cache(folder).lookup(KEY) is not None
    assert pack.stat().st_size > 0


def test_a_torn_tail_is_cut_off_and_the_next_store_follows_the_last_whole_record(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "c"
    with lossless_cache(folder) as first:
        for n in range(4):
            first.store_proxy(KEY, n, pixels(n))
    pack = pack_of(folder)
    pack.write_bytes(pack.read_bytes()[:-10])
    cache = lossless_cache(folder)
    found = cache.lookup(KEY)
    assert found is not None and found.pts_ticks == (0, 1, 2)
    assert_consistent(cache)
    cache.store_proxy(KEY, 3, pixels(3))
    cache.close()
    again = lossless_cache(folder)
    assert_consistent(again)
    assert again.lookup(KEY).pts_ticks == (0, 1, 2, 3)  # type: ignore[union-attr]


def test_a_damaged_record_is_a_miss_not_a_wrong_picture(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    with lossless_cache(folder) as first:
        for n in range(3):
            first.store_proxy(KEY, n, pixels(n))
    pack = pack_of(folder)
    raw = bytearray(pack.read_bytes())
    raw[len(raw) // 2] ^= 0xFF
    pack.write_bytes(bytes(raw))
    cache = lossless_cache(folder)
    assert cache.lookup(KEY) is not None
    missing = [n for n in range(3) if _raises_key_error(cache, n)]
    assert len(missing) == 1
    found = cache.lookup(KEY)
    assert found is not None and missing[0] not in found.pts_ticks
    cache.store_proxy(KEY, missing[0], pixels(missing[0]))
    assert cache.proxy(KEY, missing[0]).tobytes() == pixels(missing[0]).tobytes()


def _raises_key_error(cache: DiskProxyCache, pts: int) -> bool:
    try:
        got = cache.proxy(KEY, pts)
    except KeyError:
        return True
    assert got.tobytes() == pixels(pts).tobytes()
    return False


def test_damaged_files_never_raise_from_lookup(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    with lossless_cache(folder) as first:
        for n in range(3):
            first.store_proxy(KEY, n, pixels(n))
        first.mark_complete(KEY)
    entry = folder / entry_name(KEY)
    (entry / "complete").write_text("{not json", encoding="utf-8")
    (entry / "meta.json").write_text("[]", encoding="utf-8")
    cache = lossless_cache(folder)
    found = cache.lookup(KEY)
    assert found is not None and found.complete is False
    pack_of(folder).write_bytes(b"\x00" * 7)
    broken = lossless_cache(folder)
    assert broken.lookup(KEY) is None
    cache2 = lossless_cache(folder)
    pack_of(folder).unlink(missing_ok=True)
    assert cache2.lookup(KEY) is None
    cache2.store_proxy(KEY, 0, pixels(0))
    assert_consistent(cache2)


def test_a_marker_that_disagrees_with_the_pack_is_ignored(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    with lossless_cache(folder) as first:
        for n in range(3):
            first.store_proxy(KEY, n, pixels(n))
        first.mark_complete(KEY)
    marker = folder / entry_name(KEY) / "complete"
    data = json.loads(marker.read_text(encoding="utf-8"))
    marker.write_text(json.dumps({**data, "records": data["records"] + 1}), encoding="utf-8")
    found = lossless_cache(folder).lookup(KEY)
    assert found is not None and found.complete is False


def test_mark_complete_syncs_the_pack_before_it_writes_the_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    order: list[str] = []
    real_fsync = os.fsync
    real_write = store_module.atomic_write_text

    def fsync(fd: int) -> None:
        order.append("fsync")
        real_fsync(fd)

    def write(path: Path, text: str) -> None:
        order.append(path.name)
        real_write(path, text)

    monkeypatch.setattr(store_module.os, "fsync", fsync)
    monkeypatch.setattr(store_module, "atomic_write_text", write)
    cache = lossless_cache(tmp_path / "c")
    cache.store_proxy(KEY, 0, pixels(0))  # creates the entry (and its stamp file)
    order.clear()
    for n in range(1, 6):
        cache.store_proxy(KEY, n, pixels(n))
        cache.store_source_statistics(KEY, "s", n, {"a": np.zeros(1)})
    assert order == []  # no sync and no temporary file per record
    cache.mark_complete(KEY)
    assert order[:2] == ["fsync", "complete"]  # the pack is synced, then the marker written


def test_an_unreadable_stamp_makes_the_entry_the_first_to_go(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    keys = [CacheKey(100 + n, 5, VERSION) for n in range(2)]
    clock = iter(range(1, 100))
    with lossless_cache(folder, clock=lambda: next(clock)) as first:
        for key in keys:
            first.store_proxy(key, 0, pixels(1))
    (folder / entry_name(keys[1]) / "meta.json").write_text("garbage", encoding="utf-8")
    cache = lossless_cache(folder)
    total = sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())
    cache.set_limit_bytes(total - 1)
    assert cache.lookup(keys[1]) is None
    assert cache.lookup(keys[0]) is not None


# --- threads -------------------------------------------------------------------------------------


def test_readers_see_whole_records_while_one_writer_stores(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    done = threading.Event()
    errors: list[BaseException] = []

    def writer() -> None:
        try:
            for n in range(150):
                cache.store_proxy(KEY, n, pixels(n))
                cache.store_source_statistics(KEY, "s", n, {"x": np.full(2, float(n))})
            cache.mark_complete(KEY)
        except BaseException as error:
            errors.append(error)
        finally:
            done.set()

    def reader() -> None:
        try:
            while not done.is_set():
                found = cache.lookup(KEY)
                if found is None:
                    continue
                for pts in found.pts_ticks[-5:]:
                    assert cache.proxy(KEY, pts).tobytes() == pixels(pts).tobytes()
                    assert float(cache.source_statistics(KEY, "s", pts)["x"][0]) == float(pts)
        except KeyError:
            pass  # a statistics record not yet stored for the newest proxy is a miss
        except BaseException as error:
            errors.append(error)

    threads = [threading.Thread(target=reader) for _ in range(3)]
    threads.append(threading.Thread(target=writer))
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=120)
    assert errors == []
    found = cache.lookup(KEY)
    assert found is not None and found.complete and len(found.pts_ticks) == 150


def test_a_second_store_on_a_key_that_is_still_being_stored_is_a_runtime_error(
    tmp_path: Path,
) -> None:
    entered, release = threading.Event(), threading.Event()

    def slow_encode(proxy: np.ndarray) -> bytes:
        entered.set()
        assert release.wait(30)
        return DEFLATE.encode(proxy)

    slow = ProxyCodec(DEFLATE.codec_id, "slow", True, slow_encode, DEFLATE.decode, DEFLATE.shape)
    cache = lossless_cache(tmp_path / "c", codec=slow)
    first = threading.Thread(target=lambda: cache.store_proxy(KEY, 0, pixels(0)))
    first.start()
    assert entered.wait(30)
    with pytest.raises(RuntimeError):
        cache.store_proxy(KEY, 1, pixels(1))
    with pytest.raises(RuntimeError):
        cache.store_source_statistics(KEY, "s", 1, {"a": np.zeros(1)})
    with pytest.raises(RuntimeError):
        cache.mark_complete(KEY)
    release.set()
    first.join(timeout=30)
    cache.store_proxy(KEY, 1, pixels(1))  # the slot is free again
    found = cache.lookup(KEY)
    assert found is not None and found.pts_ticks == (0, 1)


# --- the dependency rule (plan 8.1, frame rule 5) ---------------------------------------------


def test_importing_the_cache_loads_nothing_forbidden() -> None:
    code = (
        "import json, sys\n"
        "import clearwater.cache\n"
        "top = {'PIL', 'av', 'PySide6', 'cupy', 'cupyx'}\n"
        "packages = ('clearwater.gui', 'clearwater.jobs', 'clearwater.methods',\n"
        "            'clearwater.io', 'clearwater.core')\n"
        "bad = sorted(m for m in sys.modules if m.split('.')[0] in top\n"
        "             or any(m == p or m.startswith(p + '.') for p in packages))\n"
        "print(json.dumps(bad))\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code], capture_output=True, text=True, timeout=120, check=False
    )
    assert result.returncode == 0, result.stderr[-2000:]
    assert json.loads(result.stdout.strip().splitlines()[-1]) == []
