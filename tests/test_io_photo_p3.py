"""Tests of the built-in Display P3 profile for nclx-only HEIC (WP3.6 round-0 item 2, D53).

Isolated so the choice can be reverted cleanly: nclx classification itself is tested in
``test_io_photo_read.py`` and does not depend on this module.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pillow_heif
import pytest

from clearwater.io.photo import icc as icc_tools
from clearwater.io.photo import png as png_tools
from clearwater.io.photo import read_photo, write_photo
from clearwater.io.photo.p3_profile import DESCRIPTION, display_p3_profile


def _nclx_heic(path: Path, primaries: int) -> Path:
    pixels = np.full((16, 16, 3), 128, dtype=np.uint8)
    nclx = {
        "color_primaries": primaries,
        "transfer_characteristics": 13,
        "matrix_coefficients": 6,
        "full_range_flag": 1,
    }
    pillow_heif.encode("RGB", (16, 16), pixels.tobytes(), str(path), quality=90, nclx_profile=nclx)
    return path


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
    assert image.color.icc_profile == display_p3_profile()
    out = tmp_path / "out.png"
    write_photo(image, meta, out, bit_depth=16)
    assert png_tools.scan_png(out.read_bytes(), "out.png").icc == display_p3_profile()
    again, _ = read_photo(out)
    assert again.color.primaries == "display-p3"


@pytest.mark.parametrize("primaries", [1, 9])
def test_other_nclx_primaries_get_no_built_in_profile(tmp_path: Path, primaries: int) -> None:
    image, _ = read_photo(_nclx_heic(tmp_path / "x.heic", primaries))
    assert image.color.icc_profile is None
    assert image.color.primaries == ("bt709" if primaries == 1 else "unknown")
    assert image.color.assumed is False


def test_the_profile_bytes_are_deterministic() -> None:
    assert display_p3_profile() == display_p3_profile()
