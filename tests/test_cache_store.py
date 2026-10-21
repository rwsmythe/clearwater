"""WP3.12 tests: the proxy cache store (IF-7; D71, D113; V17 cache side)."""

from __future__ import annotations

import itertools
import logging
import os
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray

import clearwater.cache.store as store_module
from clearwater.cache import (
    DEFAULT_CODEC,
    DEFLATE,
    DiskProxyCache,
    ProxyCodec,
    cache_key,
    codec_cache_version,
    entry_name,
    parse_entry_name,
)
from clearwater.interfaces.cache import CacheEntry, CacheKey, ProxyCache
from clearwater.interfaces.settings import DEFAULT_CACHE_LIMIT_BYTES

VERSION = codec_cache_version(DEFLATE)
KEY = CacheKey(1000, 1_700_000_000_000_000_000, VERSION)


def lossless_cache(
    folder: Path, limit: int = DEFAULT_CACHE_LIMIT_BYTES, **kw: Any
) -> DiskProxyCache:
    """Open a cache with the lossless codec (the store tests assume bit-identical proxies)."""
    kw.setdefault("codec", DEFLATE)
    return DiskProxyCache(folder, limit, **kw)


def other_key(n: int) -> CacheKey:
    """Return a distinct current-version key."""
    return CacheKey(1000 + n, 1_700_000_000_000_000_000 + n, VERSION)


def pixels(seed: int, shape: tuple[int, int, int] = (12, 16, 3)) -> NDArray[np.uint8]:
    """Return a reproducible noisy proxy (it compresses poorly, so sizes are predictable)."""
    return np.random.default_rng(seed).integers(0, 256, shape, dtype=np.uint8)


class Clock:
    """A controllable clock: each call returns the next integer."""

    def __init__(self) -> None:
        self._count = itertools.count(1)

    def __call__(self) -> int:
        return next(self._count)


def fill(cache: DiskProxyCache, key: CacheKey, frames: int = 4, stage: str | None = "s") -> None:
    """Store ``frames`` proxies (pts 0, 100, ...) and, if ``stage``, statistics for each."""
    for n in range(frames):
        cache.store_proxy(key, n * 100, pixels(n))
        if stage is not None:
            cache.store_source_statistics(key, stage, n * 100, {"means": np.full(3, n * 0.25)})


# --- the oracles (each is also run against a planted wrong implementation below) ---------------


def disk_bytes(folder: Path) -> int:
    """Return the bytes of every file under ``folder``."""
    return sum(p.stat().st_size for p in folder.rglob("*") if p.is_file())


def check_key_identity(folder: Path) -> None:
    """A key differing in any field finds nothing, also after a reopen (names, not memory)."""
    first = lossless_cache(folder)
    first.store_proxy(KEY, 0, pixels(1))
    first.store_source_statistics(KEY, "s", 0, {"a": np.zeros(2)})
    first.close()
    cache = lossless_cache(folder)
    assert cache.lookup(KEY) is not None
    variants = [
        CacheKey(KEY.size + 1, KEY.mtime_ns, KEY.cache_version),
        CacheKey(KEY.size, KEY.mtime_ns + 1, KEY.cache_version),
        CacheKey(KEY.size, KEY.mtime_ns, KEY.cache_version + 1),
    ]
    for variant in variants:
        assert cache.lookup(variant) is None
        with pytest.raises(KeyError):
            cache.proxy(variant, 0)
        with pytest.raises(KeyError):
            cache.source_statistics(variant, "s", 0)


def check_eviction_order(make: Callable[[], DiskProxyCache], folder: Path) -> None:
    """Lowering the limit removes the entry with the oldest last use, not the newest."""
    cache = make()
    keys = [other_key(n) for n in range(3)]
    for key in keys:
        cache.store_proxy(key, 0, pixels(1))
    for key in keys:
        assert cache.lookup(key) is not None  # refreshes the stamps in this order
    cache.set_limit_bytes(disk_bytes(folder) - 1)
    assert cache.lookup(keys[0]) is None
    assert cache.lookup(keys[1]) is not None
    assert cache.lookup(keys[2]) is not None


def check_round_trip(cache: DiskProxyCache) -> None:
    """The lossless store gives every proxy back bit for bit."""
    frames = {n * 7: pixels(n, (5, 9, 3)) for n in range(4)}
    for pts, frame in frames.items():
        cache.store_proxy(KEY, pts, frame)
    for pts, frame in frames.items():
        got = cache.proxy(KEY, pts)
        assert got.dtype == np.uint8 and got.shape == frame.shape
        assert got.tobytes() == frame.tobytes()


def check_clear_spares_foreign(cache: DiskProxyCache, folder: Path) -> None:
    """``clear`` removes entries and leaves a file the cache did not name."""
    cache.store_proxy(KEY, 0, pixels(1))
    foreign = folder / entry_name(KEY) / "notes.txt"
    foreign.write_text("mine", encoding="utf-8")
    cache.clear()
    assert foreign.read_text(encoding="utf-8") == "mine"
    assert cache.lookup(KEY) is None


def check_torn_entry_not_complete(cache: DiskProxyCache, folder: Path) -> None:
    """A pack cut shorter than its completeness marker is not reported complete."""
    for n in range(3):
        cache.store_proxy(KEY, n, pixels(n))
    cache.mark_complete(KEY)
    cache.close()
    pack = folder / entry_name(KEY) / "data.pack"
    pack.write_bytes(pack.read_bytes()[:-40])
    found = lossless_cache(folder).lookup(KEY)
    assert found is not None
    assert not found.complete


def check_stages_cover(cache: DiskProxyCache) -> None:
    """``stages`` lists a stage only when it covers every stored pts."""
    for pts in (1, 2, 3):
        cache.store_proxy(KEY, pts, pixels(pts))
    for pts in (1, 2):
        cache.store_source_statistics(KEY, "partial", pts, {"a": np.zeros(1)})
    for pts in (1, 2, 3):
        cache.store_source_statistics(KEY, "full", pts, {"a": np.zeros(1)})
    found = cache.lookup(KEY)
    assert found is not None
    assert found.stages == ("full",)


# --- IF-7 behaviour ----------------------------------------------------------------------------


def test_conforms_to_the_protocol(tmp_path: Path) -> None:
    cache: ProxyCache = lossless_cache(tmp_path / "c")
    assert isinstance(cache, ProxyCache)


def test_default_limit_is_the_settings_default(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    assert cache.limit_bytes() == DEFAULT_CACHE_LIMIT_BYTES


def test_limit_setters_refuse_negative(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        lossless_cache(tmp_path / "c", -1)
    cache = lossless_cache(tmp_path / "c")
    with pytest.raises(ValueError):
        cache.set_limit_bytes(-5)
    cache.set_limit_bytes(123)
    assert cache.limit_bytes() == 123


def test_nothing_resolves_the_app_data_folder(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def spy(*_: object, **__: object) -> object:
        calls.append("called")
        raise AssertionError("the cache must not resolve the app-data folder")

    import clearwater.config
    import clearwater.config.paths

    monkeypatch.setattr(clearwater.config.paths, "app_locations", spy)
    monkeypatch.setattr(clearwater.config, "app_locations", spy)
    with lossless_cache(tmp_path / "c") as cache:
        fill(cache, KEY)
        cache.mark_complete(KEY)
        assert cache.lookup(KEY) is not None
        cache.clear()
    assert calls == []


def test_v17_reopen_finds_the_complete_entry(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    with lossless_cache(folder) as first:
        fill(first, KEY, frames=5)
        first.mark_complete(KEY)
    second = lossless_cache(folder)
    found = second.lookup(KEY)
    assert isinstance(found, CacheEntry)
    assert found.complete is True
    assert found.key == KEY
    assert found.pts_ticks == (0, 100, 200, 300, 400)
    assert found.stages == ("s",)
    for n in range(5):
        assert second.proxy(KEY, n * 100).tobytes() == pixels(n).tobytes()
    assert found.size_bytes == sum(
        p.stat().st_size for p in (folder / entry_name(KEY)).iterdir() if p.is_file()
    )


def test_v17_without_mark_complete_the_entry_is_not_complete(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    first = lossless_cache(folder)
    fill(first, KEY, frames=3)
    before = first.lookup(KEY)
    assert before is not None and before.complete is False
    first.close()
    found = lossless_cache(folder).lookup(KEY)
    assert found is not None
    assert found.complete is False
    assert found.pts_ticks == (0, 100, 200)


def test_key_identity(tmp_path: Path) -> None:
    check_key_identity(tmp_path / "c")


def test_cache_key_follows_the_file(tmp_path: Path) -> None:
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"x" * 100)
    first = cache_key(source)
    assert first.size == 100
    assert first.cache_version == codec_cache_version(DEFAULT_CODEC)
    assert cache_key(source, DEFLATE).cache_version == VERSION
    assert cache_key(source) == first
    stat = source.stat()
    os.utime(source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 2_000_000_000))
    touched = cache_key(source)
    assert touched.mtime_ns != first.mtime_ns and touched.size == first.size
    source.write_bytes(b"x" * 101)
    assert cache_key(source).size == 101


def test_entry_names_hold_every_field() -> None:
    key = CacheKey(12, -34, 5)
    assert entry_name(key) == "e_12_-34_5"
    assert parse_entry_name(entry_name(key)) == key
    for bad in ("e_1_2", "x_1_2_3", "e_1_2_3_4", "e_-1_2_3", "e_1_2_3.tmp", ""):
        assert parse_entry_name(bad) is None
    with pytest.raises(ValueError):
        entry_name(CacheKey(-1, 0, 1))


def test_proxy_round_trip_is_bit_identical(tmp_path: Path) -> None:
    check_round_trip(lossless_cache(tmp_path / "c"))


def test_proxy_edge_shapes_round_trip(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    flat = np.zeros((1, 1, 3), dtype=np.uint8)
    cache.store_proxy(KEY, 0, flat)
    assert cache.proxy(KEY, 0).tobytes() == flat.tobytes()
    other = other_key(1)
    wide = pixels(3, (3, 40, 3))
    cache.store_proxy(other, 5, np.asfortranarray(wide))
    assert cache.proxy(other, 5).tobytes() == wide.tobytes()
    assert cache.proxy(other, 5).flags.writeable


def test_store_proxy_refuses_wrong_input(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    cache.store_proxy(KEY, 0, pixels(1))
    with pytest.raises(ValueError):
        cache.store_proxy(KEY, 1, pixels(1).astype(np.float32))  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        cache.store_proxy(KEY, 1, pixels(1)[:, :, 0])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        cache.store_proxy(KEY, 1, pixels(1, (12, 16, 4)))
    with pytest.raises(ValueError):
        cache.store_proxy(KEY, 1, pixels(1, (12, 17, 3)))  # shape of the first proxy is kept
    with pytest.raises(TypeError):
        cache.store_proxy(KEY, 1, [[1]])  # type: ignore[arg-type]
    with pytest.raises(ValueError):
        cache.store_proxy(CacheKey(1, 1, VERSION + 1), 0, pixels(1))
    with pytest.raises(ValueError):
        cache.store_proxy(CacheKey(-1, 1, VERSION), 0, pixels(1))
    found = cache.lookup(KEY)
    assert found is not None and found.pts_ticks == (0,)


def test_absent_proxy_and_statistics_raise_key_error(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    with pytest.raises(KeyError):
        cache.proxy(KEY, 0)
    fill(cache, KEY, frames=2)
    with pytest.raises(KeyError):
        cache.proxy(KEY, 5)
    with pytest.raises(KeyError):
        cache.source_statistics(KEY, "nope", 0)
    with pytest.raises(KeyError):
        cache.source_statistics(KEY, "s", 5)
    assert cache.lookup(other_key(9)) is None


def test_statistics_round_trip_exactly(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    stats = {
        "zeta": np.array([0.1, -0.0, np.nan, np.inf, 5e-324]),
        "alpha": np.arange(6, dtype=np.int32).reshape(2, 3),
        "flags": np.array([True, False]),
        "be": np.array([1.5, 2.5], dtype=">f4"),
        "scalar": np.array(3.25),
        "none": np.zeros((0, 3)),
        "u": np.array([255], dtype=np.uint8),
        "view": np.arange(12.0).reshape(3, 4)[:, ::2],
    }
    cache.store_source_statistics(KEY, "stage-é", -7, stats)
    got = cache.source_statistics(KEY, "stage-é", -7)
    assert list(got) == list(stats)
    for name, value in stats.items():
        assert got[name].dtype == value.dtype, name
        assert got[name].shape == value.shape, name
        assert got[name].tobytes() == np.ascontiguousarray(value).tobytes(), name
    got["alpha"][0, 0] = 99
    assert cache.source_statistics(KEY, "stage-é", -7)["alpha"][0, 0] == 0


def test_statistics_refuse_unstorable_values(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    with pytest.raises(ValueError):
        cache.store_source_statistics(KEY, "s", 0, {"o": np.array(["x"], dtype=object)})
    with pytest.raises(ValueError):
        cache.store_source_statistics(KEY, "s", 0, {"c": np.array([1j])})
    with pytest.raises(ValueError):
        cache.store_source_statistics(KEY, "", 0, {"a": np.zeros(1)})
    with pytest.raises(TypeError):
        cache.store_source_statistics(KEY, "s", 0, {1: np.zeros(1)})  # type: ignore[dict-item]


def test_stages_cover_every_pts(tmp_path: Path) -> None:
    check_stages_cover(lossless_cache(tmp_path / "c"))


def test_stages_are_sorted_and_pts_ascending(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    for pts in (30, 10, 20):
        cache.store_proxy(KEY, pts, pixels(pts))
    for stage in ("b", "a"):
        for pts in (10, 20, 30):
            cache.store_source_statistics(KEY, stage, pts, {"x": np.zeros(1)})
    found = cache.lookup(KEY)
    assert found is not None
    assert found.pts_ticks == (10, 20, 30) and found.stages == ("a", "b")


def test_mark_complete_of_unknown_key_is_a_key_error(tmp_path: Path) -> None:
    with pytest.raises(KeyError):
        lossless_cache(tmp_path / "c").mark_complete(KEY)


def test_a_new_proxy_makes_a_complete_entry_incomplete_but_statistics_do_not(
    tmp_path: Path,
) -> None:
    folder = tmp_path / "c"
    cache = lossless_cache(folder)
    fill(cache, KEY, frames=2)
    cache.mark_complete(KEY)
    cache.store_source_statistics(KEY, "late", 0, {"a": np.zeros(1)})
    cache.store_proxy(KEY, 0, pixels(0))  # byte-identical: nothing changes
    found = cache.lookup(KEY)
    assert found is not None and found.complete
    cache.store_proxy(KEY, 500, pixels(5))
    found = cache.lookup(KEY)
    assert found is not None and not found.complete
    cache.close()
    reopened = lossless_cache(folder).lookup(KEY)
    assert reopened is not None and not reopened.complete
    assert not (folder / entry_name(KEY) / "complete").exists()


def test_restoring_the_same_frame_adds_nothing_and_a_changed_one_replaces(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    cache.store_proxy(KEY, 0, pixels(1))
    size = cache.lookup(KEY).size_bytes  # type: ignore[union-attr]
    cache.store_proxy(KEY, 0, pixels(1))
    assert cache.lookup(KEY).size_bytes == size  # type: ignore[union-attr]
    cache.store_proxy(KEY, 0, pixels(2))
    assert cache.proxy(KEY, 0).tobytes() == pixels(2).tobytes()
    assert cache.lookup(KEY).size_bytes > size  # type: ignore[union-attr]


def test_a_stored_proxy_is_readable_before_the_entry_completes(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c")
    cache.store_proxy(KEY, 0, pixels(1))
    assert cache.proxy(KEY, 0).tobytes() == pixels(1).tobytes()
    other = lossless_cache(tmp_path / "c")
    assert other.proxy(KEY, 0).tobytes() == pixels(1).tobytes()


# --- limit and eviction (D71) --------------------------------------------------------------------


def make_with_clock(tmp_path: Path) -> Callable[[], DiskProxyCache]:
    clock = Clock()
    return lambda: lossless_cache(tmp_path / "c", clock=clock)


def test_eviction_removes_the_oldest_last_use_first(tmp_path: Path) -> None:
    check_eviction_order(make_with_clock(tmp_path), tmp_path / "c")


def test_a_lookup_hit_refreshes_the_stamp(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c", clock=Clock())
    keys = [other_key(n) for n in range(3)]
    for key in keys:
        cache.store_proxy(key, 0, pixels(1))
    for key in keys:
        cache.lookup(key)
    cache.lookup(keys[0])  # A is now newer than B
    cache.lookup(keys[2])  # pin C so only the stamps decide between A and B
    cache.set_limit_bytes(disk_bytes(tmp_path / "c") - 1)
    assert cache.lookup(keys[1]) is None
    assert cache.lookup(keys[0]) is not None


def test_a_store_evicts_older_entries_but_never_the_one_written(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c", clock=Clock())
    first, second = other_key(1), other_key(2)
    cache.store_proxy(first, 0, pixels(1))
    one = disk_bytes(tmp_path / "c")
    cache.set_limit_bytes(one + 10)
    cache.store_proxy(second, 0, pixels(2))
    assert cache.lookup(first) is None
    assert cache.lookup(second) is not None
    assert disk_bytes(tmp_path / "c") <= one + 10 + 200


def test_the_total_stays_under_the_limit_across_many_stores(tmp_path: Path) -> None:
    cache = lossless_cache(tmp_path / "c", clock=Clock())
    cache.store_proxy(other_key(0), 0, pixels(0))
    limit = disk_bytes(tmp_path / "c") * 3
    cache.set_limit_bytes(limit)
    for n in range(1, 12):
        cache.store_proxy(other_key(n), 0, pixels(n))
        assert disk_bytes(tmp_path / "c") <= limit + 200  # the limit plus one small file


def test_one_entry_over_the_limit_is_kept_with_a_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    cache = lossless_cache(tmp_path / "c", clock=Clock())
    cache.store_proxy(other_key(1), 0, pixels(1))
    with caplog.at_level(logging.WARNING, logger="clearwater.cache"):
        cache.set_limit_bytes(10)
        cache.store_proxy(other_key(2), 0, pixels(2))
        cache.store_proxy(other_key(2), 1, pixels(3))
    assert cache.lookup(other_key(1)) is None
    found = cache.lookup(other_key(2))
    assert found is not None and found.pts_ticks == (0, 1)
    assert sum("over its limit" in r.message for r in caplog.records) == 1
    cache.set_limit_bytes(10**9)
    assert cache.lookup(other_key(2)) is not None


def test_opening_applies_the_limit(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    with lossless_cache(folder, clock=Clock()) as first:
        for n in range(3):
            first.store_proxy(other_key(n), 0, pixels(n))
    small = lossless_cache(folder, 1, clock=Clock())
    assert [small.lookup(other_key(n)) is not None for n in range(3)].count(True) == 0


# --- clear, version clean-up, foreign files ------------------------------------------------------


def test_clear_removes_every_entry_and_spares_foreign_files(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    cache = lossless_cache(folder)
    for n in range(3):
        fill(cache, other_key(n), frames=2)
    (folder / "readme.txt").write_text("foreign", encoding="utf-8")
    (folder / "other-dir").mkdir()
    (folder / "other-dir" / "x.bin").write_bytes(b"1")
    check_clear_spares_foreign(cache, folder)
    cache.clear()
    assert all(cache.lookup(other_key(n)) is None for n in range(3))
    assert (folder / "readme.txt").read_text(encoding="utf-8") == "foreign"
    assert (folder / "other-dir" / "x.bin").read_bytes() == b"1"
    assert not list(folder.rglob("data.pack"))
    fill(cache, KEY, frames=1)  # still usable
    assert cache.lookup(KEY) is not None


def test_clear_never_follows_a_link(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "data.pack").write_bytes(b"precious")
    (outside / "keep.txt").write_bytes(b"precious")
    folder.mkdir()
    link = folder / entry_name(other_key(7))
    try:
        os.symlink(outside, link, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symbolic links are not available here")
    cache = lossless_cache(folder)
    fill(cache, KEY, frames=2)
    # a symlink named like a cache file inside a real entry folder
    victim = tmp_path / "victim.txt"
    victim.write_text("precious", encoding="utf-8")
    os.symlink(victim, folder / entry_name(KEY) / "meta.json.ab12cd34.tmp")  # a name cleanup owns
    cache.clear()
    assert (outside / "data.pack").read_bytes() == b"precious"
    assert (outside / "keep.txt").read_bytes() == b"precious"
    assert victim.read_text(encoding="utf-8") == "precious"
    assert (folder / entry_name(KEY) / "meta.json.ab12cd34.tmp").is_symlink()  # left alone
    assert link.is_symlink()


def test_other_versions_and_unreadable_entries_are_removed_when_opening(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    with lossless_cache(folder) as first:
        fill(first, KEY, frames=2)
    old = folder / entry_name(CacheKey(5, 5, VERSION + 7))
    old.mkdir()
    (old / "data.pack").write_bytes(b"old format")
    (old / "keep.txt").write_text("foreign", encoding="utf-8")
    garbage = folder / entry_name(other_key(3))
    garbage.mkdir()
    (garbage / "data.pack").write_bytes(b"not a pack at all, no header here......")
    empty = folder / entry_name(other_key(4))
    empty.mkdir()
    (folder / "scratch").mkdir()
    (folder / "scratch" / "data.pack").write_bytes(b"not ours")
    reopened = lossless_cache(folder)
    assert not (old / "data.pack").exists()
    assert (old / "keep.txt").exists()
    assert not garbage.exists() and not empty.exists()
    assert (folder / "scratch" / "data.pack").read_bytes() == b"not ours"
    assert reopened.lookup(KEY) is not None
    assert reopened.lookup(CacheKey(5, 5, VERSION + 7)) is None


def test_a_pack_that_belongs_to_another_key_is_never_served(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    with lossless_cache(folder) as first:
        fill(first, KEY, frames=1)
    moved = folder / entry_name(other_key(1))
    (folder / entry_name(KEY)).rename(moved)
    reopened = lossless_cache(folder)
    assert reopened.lookup(other_key(1)) is None
    assert reopened.lookup(KEY) is None


# --- planted wrong implementations: each oracle above must fail by name --------------------------


def test_planted_key_that_ignores_mtime_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store_module, "entry_name", lambda k: f"e_{k.size}_0_{k.cache_version}")
    with pytest.raises(AssertionError):
        check_key_identity(tmp_path / "c")


def test_planted_newest_first_eviction_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    original = store_module._eviction_key

    def newest_first(entry: object) -> tuple[bool, int, tuple[int, int, int]]:
        marked, stamp, key = original(entry)  # type: ignore[arg-type]
        return marked, -stamp, key

    monkeypatch.setattr(store_module, "_eviction_key", newest_first)
    with pytest.raises(AssertionError):
        check_eviction_order(make_with_clock(tmp_path), tmp_path / "c")


def test_planted_lossy_round_trip_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    lossy = ProxyCodec(
        DEFLATE.codec_id,
        "lossy",
        True,
        DEFLATE.encode,
        lambda blob: DEFLATE.decode(blob) ^ np.uint8(1),
        DEFLATE.shape,
    )
    monkeypatch.setattr(store_module, "CODECS", {lossy.codec_id: lossy})
    with pytest.raises(AssertionError):
        check_round_trip(lossless_cache(tmp_path / "c", codec=lossy))


def test_planted_clear_that_deletes_foreign_files_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store_module, "_is_cache_file", lambda name: True)
    folder = tmp_path / "c"
    with pytest.raises((AssertionError, FileNotFoundError)):
        check_clear_spares_foreign(lossless_cache(folder), folder)


def test_planted_marker_that_is_always_believed_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store_module, "marker_valid", lambda *a, **k: True)
    with pytest.raises(AssertionError):
        check_torn_entry_not_complete(lossless_cache(tmp_path / "c"), tmp_path / "c")


def test_planted_partial_stage_listing_is_caught(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(store_module, "_stage_covers", lambda proxy_pts, stage_pts: True)
    with pytest.raises(AssertionError):
        check_stages_cover(lossless_cache(tmp_path / "c"))


def test_the_oracles_pass_on_the_real_implementation(tmp_path: Path) -> None:
    folder = tmp_path / "torn"
    check_torn_entry_not_complete(lossless_cache(folder), folder)
