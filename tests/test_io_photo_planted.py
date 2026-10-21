"""Planted wrong implementations fail by name (WP3.6, review-gate Part 1).

Each test swaps one behaviour for the plausible wrong one and runs the real test that guards it,
which must fail. A check that passes both ways would be worthless (dispatch recipe, section 2).
"""

from __future__ import annotations

import io
from collections.abc import Callable
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from PIL import Image as PILImage

import test_io_photo_read as read_tests
import test_io_photo_units as unit_tests
import test_io_photo_write as write_tests
from clearwater.io.photo import exif as exif_tools
from clearwater.io.photo import heif_boxes, reader
from clearwater.io.photo import png as png_tools
from spike_io import photo as spike

FAILS = (AssertionError, pytest.fail.Exception)


def test_heic_exif_always_honoured_rotates_twice(
    sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    read_tests.test_the_four_heic_layouts_rotate_exactly_once(sample, "heic-ad24-both")
    monkeypatch.setattr(reader, "heic_tag_to_apply", lambda tag, layout: tag)
    with pytest.raises(FAILS):
        read_tests.test_the_four_heic_layouts_rotate_exactly_once(sample, "heic-ad24-both")


def test_heic_exif_never_honoured_leaves_the_tag_only_file_unrotated(
    sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    read_tests.test_the_four_heic_layouts_rotate_exactly_once(sample, "heic-ad24-exif-only")
    monkeypatch.setattr(reader, "heic_tag_to_apply", lambda tag, layout: 1)
    with pytest.raises(FAILS):
        read_tests.test_the_four_heic_layouts_rotate_exactly_once(sample, "heic-ad24-exif-only")


def test_irot_read_from_ipco_without_ipma_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    unit_tests.test_irot_comes_from_the_primary_items_ipma_not_from_ipco_alone()
    monkeypatch.setattr(heif_boxes, "_associations", lambda data, ipma, primary: list(range(1, 40)))
    with pytest.raises(FAILS):
        unit_tests.test_irot_comes_from_the_primary_items_ipma_not_from_ipco_alone()


def test_ispe_not_checked_is_caught(
    sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    read_tests.test_a_primary_size_that_disagrees_with_ispe_is_refused(sample, monkeypatch)
    monkeypatch.undo()
    monkeypatch.setattr(heif_boxes.HeifLayout, "expected_size", lambda self: None)
    with pytest.raises(FAILS):
        read_tests.test_a_primary_size_that_disagrees_with_ispe_is_refused(sample, monkeypatch)


def test_a_16_bit_source_read_as_8_bit_is_caught(
    sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    real = png_tools.read_png16

    def as_8_bit(scan: Any, name: str) -> np.ndarray:
        return (real(scan, name) >> 8).astype(np.uint16) * 257

    monkeypatch.setattr(png_tools, "read_png16", as_8_bit)
    with pytest.raises(FAILS):
        read_tests.test_a_16_bit_sample_is_not_read_as_8_bit(sample, "png16-gradient-srgb")
    with pytest.raises(FAILS):
        read_tests.test_lossless_samples_read_exactly_at_their_own_precision(
            sample, "png16-gradient-srgb"
        )


def test_16_bit_written_as_8_bit_is_caught(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    write_tests.test_ihdr_states_the_depth_the_size_and_rgb(tmp_path)
    real = png_tools.write_png

    def as_8_bit(path: Path, pixels: Any, **kwargs: Any) -> None:
        kwargs["bit_depth"] = 8
        real(path, pixels, **kwargs)

    monkeypatch.setattr(png_tools, "write_png", as_8_bit)
    again = tmp_path / "again"
    again.mkdir()
    with pytest.raises(FAILS):
        write_tests.test_ihdr_states_the_depth_the_size_and_rgb(again)


def test_a_stale_orientation_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    real = exif_tools.edit

    def stale(source: bytes | None, width: int, height: int) -> bytes:
        block = exif_tools.load(real(source, width, height))
        block[exif_tools.ORIENTATION] = 6
        return exif_tools.strip_prefix(block.tobytes())

    monkeypatch.setattr(exif_tools, "edit", stale)
    with pytest.raises(FAILS):
        unit_tests.test_d63_edit_changes_exactly_the_listed_fields()


def test_a_kept_thumbnail_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    real = exif_tools.edit

    def keeps_thumbnail(source: bytes | None, width: int, height: int) -> bytes:
        buffer = io.BytesIO()
        PILImage.new("RGB", (8, 6)).save(buffer, "JPEG")
        edited = exif_tools.PREFIX + real(source, width, height)
        return exif_tools.strip_prefix(spike.add_thumbnail(edited, buffer.getvalue()))

    monkeypatch.setattr(exif_tools, "edit", keeps_thumbnail)
    with pytest.raises(FAILS):
        unit_tests.test_d63_edit_changes_exactly_the_listed_fields()


def test_a_changed_icc_byte_is_caught(
    tmp_path: Path, sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    real = png_tools.write_png

    def flips_a_byte(path: Path, pixels: Any, **kwargs: Any) -> None:
        icc = bytearray(kwargs["icc"])
        icc[-1] ^= 1
        kwargs["icc"] = bytes(icc)
        real(path, pixels, **kwargs)

    monkeypatch.setattr(png_tools, "write_png", flips_a_byte)
    with pytest.raises(FAILS):
        write_tests.test_the_iccp_profile_is_byte_identical_and_validly_named(tmp_path, sample)


def test_a_profile_name_with_a_trailing_space_accepted_is_caught(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real = png_tools.keyword_problem

    def lenient(name: str) -> str | None:
        return None if name.endswith(" ") and name.strip() else real(name)

    unit_tests.test_keyword_rule_rejects_each_violation("Display P3 ", "leading or trailing")
    monkeypatch.setattr(png_tools, "keyword_problem", lenient)
    with pytest.raises(FAILS):
        unit_tests.test_keyword_rule_rejects_each_violation("Display P3 ", "leading or trailing")


def test_a_decoder_that_ignores_the_paeth_filter_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    unit_tests.test_each_single_filter_type_alone_round_trips(4)
    real = png_tools._unfilter_wavefront

    def no_paeth(filtered: Any, types: Any, bpp: int) -> Any:
        return real(filtered, np.where(types == 4, 1, types).astype(np.uint8), bpp)

    monkeypatch.setattr(png_tools, "_unfilter_wavefront", no_paeth)
    with pytest.raises(FAILS):
        unit_tests.test_each_single_filter_type_alone_round_trips(4)


def test_a_reader_that_alters_pixel_values_is_caught(
    sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    real = reader._normalise

    def tinted(samples: np.ndarray, depth: int) -> np.ndarray:
        return (real(samples, depth) * np.float32(0.99)).astype(np.float32)

    monkeypatch.setattr(reader, "_normalise", tinted)
    with pytest.raises(FAILS):
        read_tests.test_lossless_samples_read_exactly_at_their_own_precision(
            sample, "png8-gradient-srgb"
        )
