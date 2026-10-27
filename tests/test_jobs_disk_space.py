"""WP3.13 tests: disk-space estimate and check (spec 8.4, D87); DR-48 rule from WP3.14."""

from __future__ import annotations

import math
import shutil
from fractions import Fraction
from pathlib import Path

import pytest

from clearwater.interfaces.settings import Settings
from clearwater.io.video import encode
from clearwater.jobs import (
    MARGIN,
    PHOTO_OVERHEAD_BYTES,
    QUALITY_RATIO,
    SpaceCheck,
    check_free_space,
    estimate_photo_bytes,
    estimate_video_bytes,
)

# --- DR-48 (WP3.14): max(ratio x source, ceiling x duration) x MARGIN, no 10-bit doubling ----

FPS = Fraction(30000, 1001)
UHD = {"width": 3840, "height": 2160, "frame_rate": FPS}


def _ceiling_bytes(level: str, duration_s: Fraction) -> Fraction:
    """The AD-12 ceiling term, computed here from the encode module's constants."""
    share = encode.NVENC_RATE_SHARE[level]
    return Fraction(encode.NVENC_BITS_PER_PIXEL) / share * 3840 * 2160 * FPS * duration_s / 8


@pytest.mark.parametrize(("level", "ratio"), [("high", 1.10), ("standard", 0.50), ("draft", 0.25)])
def test_video_ratio_term_wins_on_a_high_rate_source(level: str, ratio: float) -> None:
    # 60 s at 200 Mb/s: the source-relative term is above every level's ceiling.
    duration = Fraction(60)
    size = 200_000_000 * 60 // 8
    assert QUALITY_RATIO[level] == ratio
    assert MARGIN == 1.25
    assert Fraction(ratio) * size > _ceiling_bytes(level, duration)
    got = estimate_video_bytes(size, Settings(quality_level=level), duration_s=duration, **UHD)
    assert got == math.ceil(Fraction(ratio) * size * Fraction(MARGIN))


@pytest.mark.parametrize("level", ["high", "standard", "draft"])
def test_video_ceiling_term_wins_on_a_low_rate_source(level: str) -> None:
    # 60 s at 6.58 Mb/s (GX011625's camera rate): the ceiling term binds.
    duration = Fraction(60)
    size = 6_580_000 * 60 // 8
    ceiling = _ceiling_bytes(level, duration)
    assert ceiling > Fraction(QUALITY_RATIO[level]) * size
    got = estimate_video_bytes(size, Settings(quality_level=level), duration_s=duration, **UHD)
    assert got == math.ceil(ceiling * Fraction(MARGIN))
    # bits / 8: the Standard ceiling at 4K 29.97 is about 29.83 Mb/s, so 60 s is about 223.7 MB.
    if level == "standard":
        assert 223_000_000 < ceiling < 224_000_000


def test_video_estimate_is_the_same_for_both_encoders_and_never_doubles_ten_bit() -> None:
    duration = Fraction(30)
    estimates = {
        estimate_video_bytes(
            10_000_000,
            Settings(quality_level="high", video_encoder=encoder, ten_bit_for_eight_bit=ten),
            duration_s=duration,
            **UHD,
        )
        for encoder in ("hevc_nvenc", "libx265", "auto")
        for ten in (False, True)
    }
    assert len(estimates) == 1


def test_video_estimate_reads_the_encode_constant_at_call_time(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # One source of the constant: patching the encode module changes the estimate.
    args = {"duration_s": Fraction(10), **UHD}
    doubled = math.ceil(_ceiling_bytes("standard", Fraction(10)) * 2 * Fraction(MARGIN))
    before = estimate_video_bytes(1, Settings(), **args)
    monkeypatch.setattr(encode, "NVENC_BITS_PER_PIXEL", encode.NVENC_BITS_PER_PIXEL * 2)
    after = estimate_video_bytes(1, Settings(), **args)
    assert after == doubled > before


def test_video_estimate_rounds_up_and_rejects_bad_input() -> None:
    tiny = {"width": 1, "height": 1, "frame_rate": Fraction(1), "duration_s": Fraction(0)}
    assert estimate_video_bytes(1, Settings(quality_level="draft"), **tiny) == 1
    with pytest.raises(ValueError, match="quality"):
        estimate_video_bytes(10, Settings(quality_level="ultra"), **tiny)
    with pytest.raises(ValueError, match="size"):
        estimate_video_bytes(-1, Settings(), **tiny)
    with pytest.raises(ValueError, match="duration"):
        estimate_video_bytes(1, Settings(), **{**tiny, "duration_s": Fraction(-1)})
    with pytest.raises(ValueError, match="positive"):
        estimate_video_bytes(1, Settings(), **{**tiny, "width": 0})


def test_photo_estimate() -> None:
    assert estimate_photo_bytes(4000, 3000, 16) == 4000 * 3000 * 6 + PHOTO_OVERHEAD_BYTES
    assert estimate_photo_bytes(4000, 3000, 8) == 4000 * 3000 * 3 + PHOTO_OVERHEAD_BYTES
    assert PHOTO_OVERHEAD_BYTES == 1024 * 1024


def test_photo_estimate_rejects_bad_input() -> None:
    with pytest.raises(ValueError):
        estimate_photo_bytes(0, 10, 8)
    with pytest.raises(ValueError):
        estimate_photo_bytes(10, 10, 12)


def _fake_usage(free: int) -> object:
    def usage(path: object) -> shutil._ntuple_diskusage:
        return shutil._ntuple_diskusage(total=free * 2, used=free, free=free)

    return usage


def test_insufficient_space_reports_both_figures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(shutil, "disk_usage", _fake_usage(987_654))
    check = check_free_space(tmp_path, 1_234_567)
    assert not check.ok
    assert (check.needed, check.free) == (1_234_567, 987_654)
    message = check.message()
    assert "1,234,567" in message
    assert "987,654" in message
    assert "Not enough" in message


def test_message_is_ascii_and_names_the_folder() -> None:
    message = SpaceCheck(Path("D:/out"), 2000, 1000, False).message()
    assert message.isascii()
    assert "out" in message


def test_message_is_ascii_for_a_unicode_folder() -> None:
    message = SpaceCheck(Path("D:/输出"), 2000, 1000, False).message()
    assert message.isascii()
    assert "2,000" in message
    assert "1,000" in message


def test_sufficient_space(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(shutil, "disk_usage", _fake_usage(5000))
    assert check_free_space(tmp_path, 5000).ok
    assert not check_free_space(tmp_path, 5001).ok


def test_missing_folder_measures_nearest_existing_ancestor(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    seen: list[Path] = []

    def usage(path: Path) -> shutil._ntuple_diskusage:
        seen.append(Path(path))
        return shutil._ntuple_diskusage(total=10, used=5, free=5)

    monkeypatch.setattr(shutil, "disk_usage", usage)
    check_free_space(tmp_path / "not" / "yet" / "there", 1)
    assert seen == [tmp_path]


def test_real_volume_has_positive_free_space(tmp_path: Path) -> None:
    check = check_free_space(tmp_path, 1)
    assert check.free > 0
    assert check.ok
