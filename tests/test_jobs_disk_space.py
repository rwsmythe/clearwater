"""WP3.13 tests: disk-space estimate and check (spec 8.4, D87)."""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from clearwater.interfaces.settings import Settings
from clearwater.jobs import (
    MARGIN,
    PHOTO_OVERHEAD_BYTES,
    QUALITY_RATIO,
    SpaceCheck,
    check_free_space,
    estimate_photo_bytes,
    estimate_video_bytes,
)


@pytest.mark.parametrize(("level", "ratio"), [("high", 1.0), ("standard", 0.5), ("draft", 0.25)])
def test_video_estimate_uses_ratio_and_margin(level: str, ratio: float) -> None:
    settings = Settings(quality_level=level)
    assert QUALITY_RATIO[level] == ratio
    assert estimate_video_bytes(1_000_000, settings, 8) == int(1_000_000 * ratio * 1.25)
    assert MARGIN == 1.25


def test_video_ten_bit_doubles_only_for_eight_bit_sources() -> None:
    settings = Settings(quality_level="high", ten_bit_for_eight_bit=True)
    assert estimate_video_bytes(1_000_000, settings, 8) == 2_500_000
    assert estimate_video_bytes(1_000_000, settings, 10) == 1_250_000
    off = Settings(quality_level="high")
    assert estimate_video_bytes(1_000_000, off, 8) == 1_250_000


def test_video_estimate_rounds_up_and_rejects_bad_input() -> None:
    assert estimate_video_bytes(1, Settings(quality_level="draft"), 8) == 1
    with pytest.raises(ValueError, match="quality"):
        estimate_video_bytes(10, Settings(quality_level="ultra"), 8)
    with pytest.raises(ValueError, match="size"):
        estimate_video_bytes(-1, Settings(), 8)


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
