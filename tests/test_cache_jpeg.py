"""WP3.12 tests: the JPEG proxy codecs and the codec identity in the cache version (AD-5 ruling)."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest
from numpy.typing import NDArray

import clearwater.cache.codec as codec_module
from clearwater.cache import (
    CACHE_FORMAT_VERSION,
    CODECS,
    DEFAULT_CODEC,
    DEFLATE,
    JPEG_Q75_444,
    JPEG_Q80_420,
    DiskProxyCache,
    cache_key,
    codec_cache_version,
    entry_name,
    jpeg_identity,
    round_trip,
)
from clearwater.interfaces.cache import CacheKey

MAX_ERROR_SMOOTH = 8
"""Largest |decoded - stored| allowed on the smooth test picture (levels); the measured error
on real footage at q75 4:4:4 reaches 61 levels at sharp edges (ledger, measured test)."""


def scene(shape: tuple[int, int, int] = (60, 96, 3), seed: int = 0) -> NDArray[np.uint8]:
    """Return a smooth, slightly noisy picture, like an underwater proxy."""
    rng = np.random.default_rng(seed)
    y, x = np.mgrid[0 : shape[0], 0 : shape[1]]
    base = np.stack([40 + 0.5 * x, 90 + 0.6 * y, 150 + 0.3 * x + 0.3 * y], axis=-1)
    noisy = base + rng.normal(0, 1.5, shape)
    return np.clip(np.rint(noisy), 0, 255).astype(np.uint8)


def key_of(codec_version: int, n: int = 0) -> CacheKey:
    """Return a key with the given cache version."""
    return CacheKey(5000 + n, 1_700_000_000_000_000_000 + n, codec_version)


@pytest.mark.parametrize("codec", [JPEG_Q75_444, JPEG_Q80_420])
def test_the_stored_proxy_is_the_decoded_proxy_and_is_stable(tmp_path: Path, codec: object) -> None:
    folder = tmp_path / "c"
    picture = scene()
    with DiskProxyCache(folder, codec=codec) as cache:  # type: ignore[arg-type]
        key = key_of(cache.cache_version)
        cache.store_proxy(key, 0, picture)
        stored = cache.proxy(key, 0)
        again = cache.proxy(key, 0)
        assert stored.dtype == np.uint8 and stored.shape == picture.shape
        assert stored.tobytes() == again.tobytes()
        assert stored.tobytes() == round_trip(picture, codec).tobytes()  # type: ignore[arg-type]
        assert int(np.abs(stored.astype(int) - picture.astype(int)).max()) <= MAX_ERROR_SMOOTH
        assert stored.tobytes() != picture.tobytes()  # a lossy store: not the input
    reopened = DiskProxyCache(folder, codec=codec)  # type: ignore[arg-type]
    assert reopened.proxy(key, 0).tobytes() == stored.tobytes()


@pytest.mark.parametrize("shape", [(1, 1, 3), (5, 9, 3), (17, 33, 3), (540, 960, 3)])
def test_shapes_survive(shape: tuple[int, int, int]) -> None:
    picture = scene(shape)
    for codec in (JPEG_Q75_444, JPEG_Q80_420):
        assert round_trip(picture, codec).shape == shape


def test_the_default_codec_is_the_ruled_one() -> None:
    assert DEFAULT_CODEC is JPEG_Q75_444
    assert not DEFAULT_CODEC.lossless and DEFLATE.lossless
    assert CODECS[2] is JPEG_Q75_444 and CODECS[3] is JPEG_Q80_420
    assert len({c.codec_id for c in CODECS.values()}) == 3


def test_a_record_is_decoded_by_the_codec_that_wrote_it(tmp_path: Path) -> None:
    folder = tmp_path / "c"
    picture = scene()
    with DiskProxyCache(folder, codec=JPEG_Q80_420) as cache:
        key = key_of(cache.cache_version)
        cache.store_proxy(key, 0, picture)
        expected = round_trip(picture, JPEG_Q80_420).tobytes()
        assert cache.proxy(key, 0).tobytes() == expected


def test_the_identity_names_pillow_and_libjpeg() -> None:
    identity = jpeg_identity()
    assert identity.startswith("pillow=") and "libjpeg=" in identity and "turbo=" in identity


def test_a_different_decoder_identity_invalidates_the_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    folder = tmp_path / "c"
    source = tmp_path / "clip.mp4"
    source.write_bytes(b"x" * 64)
    with DiskProxyCache(folder) as first:
        key = cache_key(source)
        assert key == first.key_for(source)
        first.store_proxy(key, 0, scene())
        first.mark_complete(key)
    version_before = codec_cache_version(DEFAULT_CODEC)
    assert DiskProxyCache(folder).lookup(key) is not None  # same decoder: a hit
    monkeypatch.setattr(codec_module, "jpeg_identity", lambda: "pillow=99;libjpeg=99;turbo=99")
    assert codec_cache_version(DEFAULT_CODEC) != version_before
    assert codec_cache_version(JPEG_Q80_420) != codec_cache_version(JPEG_Q75_444)
    newer = DiskProxyCache(folder)
    assert newer.lookup(key) is None  # a miss: re-analysis
    assert not (folder / entry_name(key)).exists()  # and the stale entry is gone
    new_key = cache_key(source)
    assert new_key.cache_version != key.cache_version
    with pytest.raises(ValueError):
        newer.store_proxy(key, 0, scene())
    newer.store_proxy(new_key, 0, scene())
    found = newer.lookup(new_key)
    assert found is not None and not found.complete


def test_the_default_version_depends_on_the_codec_not_only_the_format() -> None:
    versions = {codec_cache_version(c) for c in (DEFLATE, JPEG_Q75_444, JPEG_Q80_420)}
    assert len(versions) == 3
    assert all(CACHE_FORMAT_VERSION << 48 < v < (CACHE_FORMAT_VERSION + 1) << 48 for v in versions)


def test_identities_that_collide_in_24_bits_still_give_different_versions() -> None:
    # these two collided when the identity was folded in through the low 24 bits of a CRC-32
    first = "pillow=11.49.5;libjpeg=6.0;turbo=3.1.56.1"
    second = "pillow=11.64.37;libjpeg=6.0;turbo=3.1.75.10"
    one = dataclasses.replace(JPEG_Q75_444, identity=lambda: first)
    two = dataclasses.replace(JPEG_Q75_444, identity=lambda: second)
    assert codec_cache_version(one) != codec_cache_version(two)
    assert codec_cache_version(one) == codec_cache_version(one)
    assert entry_name(key_of(codec_cache_version(one)))  # the version is storable in a name
