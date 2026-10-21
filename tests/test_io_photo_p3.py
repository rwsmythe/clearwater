"""Tests of the built-in Display P3 profile for nclx-only HEIC (WP3.6 round-0 item 2, D53).

Isolated so the choice can be reverted cleanly: nclx classification itself is tested in
``test_io_photo_read.py`` and does not depend on this module.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pillow_heif
import pytest
from PIL import Image as PILImage

from clearwater.io.photo import icc as icc_tools
from clearwater.io.photo import png as png_tools
from clearwater.io.photo import read_photo, write_photo
from clearwater.io.photo.p3_profile import DESCRIPTION, display_p3_profile

DISPLAY_P3_MD5 = "ee27975c71b9ed10be950a696f6fe6f4"
"""The md5 of the built-in Display P3 profile (620 bytes); a change in the bytes is a decision."""


def _nclx_heic(path: Path, primaries: int, transfer: int = 13) -> Path:
    pixels = np.full((16, 16, 3), 128, dtype=np.uint8)
    nclx = {
        "color_primaries": primaries,
        "transfer_characteristics": transfer,
        "matrix_coefficients": 6,
        "full_range_flag": 1,
    }
    pillow_heif.encode("RGB", (16, 16), pixels.tobytes(), str(path), quality=90, nclx_profile=nclx)
    return path


def _provenance(path: Path) -> str | None:
    with PILImage.open(path) as image:
        text = image.text.get("clearwater-provenance")
    return str(text) if text is not None else None


def test_the_built_in_profile_is_valid_and_classifies_as_display_p3() -> None:
    profile = display_p3_profile()
    assert icc_tools.is_valid_profile(profile) and icc_tools.is_rgb_profile(profile)
    found = icc_tools.classify(profile)
    assert (found.primaries, found.transfer) == ("display-p3", "srgb")
    assert png_tools.profile_name(profile) == DESCRIPTION


def test_an_nclx_only_display_p3_heic_carries_the_profile_to_the_png(tmp_path: Path) -> None:
    source = _nclx_heic(tmp_path / "p3.heic", 12)
    image, meta = read_photo(source)
    assert (image.color.primaries, image.color.transfer) == ("display-p3", "srgb")
    assert image.color.assumed is False
    assert image.color.icc_profile is None, "IF-1: the file has no profile; the writer adds one"
    out = tmp_path / "out.png"
    write_photo(image, meta, out, bit_depth=16)
    assert png_tools.scan_png(out.read_bytes(), "out.png").icc == display_p3_profile()
    again, _ = read_photo(out)
    assert again.color.primaries == "display-p3"


def test_other_nclx_primaries_get_no_built_in_profile(tmp_path: Path) -> None:
    image, _ = read_photo(_nclx_heic(tmp_path / "x.heic", 9))
    assert image.color.icc_profile is None
    assert image.color.primaries == "unknown"
    assert image.color.assumed is False


def test_the_profile_bytes_are_deterministic() -> None:
    assert display_p3_profile() == display_p3_profile()


def test_the_built_in_display_p3_bytes_are_pinned() -> None:
    profile = display_p3_profile()
    assert len(profile) == 620
    assert hashlib.md5(profile).hexdigest() == DISPLAY_P3_MD5


def test_the_writer_records_the_built_in_profile_in_provenance(tmp_path: Path) -> None:
    image, meta = read_photo(_nclx_heic(tmp_path / "p3.heic", 12))
    out = tmp_path / "out.png"
    write_photo(image, meta, out, bit_depth=8, provenance={"app_version": "0"})
    text = _provenance(out)
    assert text is not None
    assert json.loads(text) == {"app_version": "0", "profile": "built-in Display P3"}


def test_provenance_off_records_nothing_and_the_profile_is_still_embedded(tmp_path: Path) -> None:
    image, meta = read_photo(_nclx_heic(tmp_path / "p3.heic", 12))
    out = tmp_path / "out.png"
    write_photo(image, meta, out, bit_depth=8, provenance=None)
    assert _provenance(out) is None
    assert png_tools.scan_png(out.read_bytes(), "out.png").icc == display_p3_profile()


def test_a_clearwater_png_read_back_copies_its_profile_and_records_none(tmp_path: Path) -> None:
    first = tmp_path / "first.png"
    image, meta = read_photo(_nclx_heic(tmp_path / "p3.heic", 12))
    write_photo(image, meta, first, bit_depth=16, provenance={"a": 1})
    again, again_meta = read_photo(first)
    assert again.color.icc_profile == display_p3_profile()
    second = tmp_path / "second.png"
    write_photo(again, again_meta, second, bit_depth=16, provenance={"a": 2})
    assert png_tools.scan_png(second.read_bytes(), "second.png").icc == display_p3_profile()
    assert json.loads(str(_provenance(second))) == {"a": 2}


def test_a_source_profile_is_copied_and_not_called_built_in(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    image, meta = read_photo(sample("heic8-gradient-display-p3"))
    assert image.color.icc_profile is not None
    assert image.color.icc_profile != display_p3_profile()
    out = tmp_path / "out.png"
    write_photo(image, meta, out, bit_depth=8, provenance={"a": 1})
    assert png_tools.scan_png(out.read_bytes(), "out.png").icc == image.color.icc_profile
    text = _provenance(out)
    assert text is not None and "profile" not in json.loads(text)


def test_a_provenance_with_its_own_profile_key_is_refused_beside_a_built_in(
    tmp_path: Path,
) -> None:
    image, meta = read_photo(_nclx_heic(tmp_path / "p3.heic", 12))
    with pytest.raises(ValueError, match="profile"):
        write_photo(image, meta, tmp_path / "out.png", bit_depth=8, provenance={"profile": "x"})


@pytest.mark.parametrize("transfer", [1, 16, 18])
def test_a_display_p3_nclx_with_another_curve_gets_no_profile(
    tmp_path: Path, transfer: int
) -> None:
    image, _ = read_photo(_nclx_heic(tmp_path / "x.heic", 12, transfer))
    assert image.color.primaries == "display-p3"
    assert image.color.icc_profile is None
