"""Tests of the built-in sRGB profile and of the four colour-source classes (WP3.6 round-0 item 2).

The classes: a source ICC profile (copied byte-identical), nclx Display P3 (built-in Display P3),
nclx BT.709/sRGB (built-in sRGB), and an untagged or out-of-set source (no ``iCCP``). Isolated like
``test_io_photo_p3.py`` so the sRGB leg can be reverted on its own.
"""

from __future__ import annotations

import hashlib
import io
import json
from collections.abc import Callable
from pathlib import Path

import numpy as np
import pillow_heif
import pytest
from PIL import Image as PILImage

from clearwater.interfaces.image import ColorDescription
from clearwater.io.photo import icc as icc_tools
from clearwater.io.photo import png as png_tools
from clearwater.io.photo import read_photo, write_photo
from clearwater.io.photo.p3_profile import display_p3_profile
from clearwater.io.photo.srgb_profile import DESCRIPTION, srgb_profile
from clearwater.io.photo.writer import built_in_profile

SRGB_MD5 = "ca34a0279325928fc9fd3fc7eff99eb9"
"""The md5 of the built-in sRGB profile (608 bytes); a change in the bytes is a decision."""


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


def _written(source: Path, out: Path, provenance: dict[str, int] | None = None) -> bytes:
    image, meta = read_photo(source)
    write_photo(image, meta, out, bit_depth=16, provenance=provenance)
    return out.read_bytes()


def _provenance(path: Path) -> dict[str, object] | None:
    with PILImage.open(path) as image:
        text = image.text.get("clearwater-provenance")
    return None if text is None else dict(json.loads(str(text)))


def test_the_built_in_srgb_profile_is_valid_and_classifies_as_srgb() -> None:
    profile = srgb_profile()
    assert icc_tools.is_valid_profile(profile) and icc_tools.is_rgb_profile(profile)
    found = icc_tools.classify(profile)
    assert (found.primaries, found.transfer) == ("bt709", "srgb")
    assert png_tools.profile_name(profile) == DESCRIPTION
    assert profile != display_p3_profile()


def test_the_built_in_srgb_bytes_are_pinned() -> None:
    profile = srgb_profile()
    assert len(profile) == 608
    assert hashlib.md5(profile).hexdigest() == SRGB_MD5
    assert srgb_profile() == profile


def test_the_writers_table_chooses_by_description() -> None:
    def color(
        primaries: str, transfer: str, *, assumed: bool, icc: bytes | None
    ) -> ColorDescription:
        return ColorDescription(primaries, transfer, "identity", "full", 8, assumed, icc)

    chosen = built_in_profile(color("bt709", "srgb", assumed=False, icc=None))
    assert chosen == ("sRGB", srgb_profile())
    chosen = built_in_profile(color("display-p3", "srgb", assumed=False, icc=None))
    assert chosen == ("Display P3", display_p3_profile())
    assert built_in_profile(color("bt709", "srgb", assumed=True, icc=None)) is None
    assert built_in_profile(color("bt709", "srgb", assumed=False, icc=b"x")) is None
    assert built_in_profile(color("display-p3", "bt709", assumed=False, icc=None)) is None
    assert built_in_profile(color("unknown", "srgb", assumed=False, icc=None)) is None


# --- the four classes -----------------------------------------------------------------------


def test_class_source_icc_is_copied_byte_identical(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    for sample_id in ("heic8-gradient-srgb", "heic8-gradient-display-p3", "png16-gradient-srgb"):
        image, _ = read_photo(sample(sample_id))
        source = image.color.icc_profile
        assert source is not None
        assert source not in (srgb_profile(), display_p3_profile())
        out = tmp_path / f"{sample_id}.png"
        _written(sample(sample_id), out, {"a": 1})
        assert png_tools.scan_png(out.read_bytes(), out.name).icc == source
        assert _provenance(out) == {"a": 1}


def test_class_nclx_display_p3_gets_the_built_in_display_p3(tmp_path: Path) -> None:
    out = tmp_path / "out.png"
    data = _written(_nclx_heic(tmp_path / "p3.heic", 12), out, {"a": 1})
    assert png_tools.scan_png(data, "out.png").icc == display_p3_profile()
    assert _provenance(out) == {"a": 1, "profile": "built-in Display P3"}


def test_class_nclx_srgb_gets_the_built_in_srgb(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    for name, source in (
        ("fixture", sample("heic8-gradient-none")),
        ("encoded", _nclx_heic(tmp_path / "s.heic", 1)),
    ):
        image, _ = read_photo(source)
        assert (image.color.primaries, image.color.transfer) == ("bt709", "srgb")
        assert image.color.assumed is False
        assert image.color.icc_profile is None, "IF-1: the file has no profile"
        out = tmp_path / f"{name}.png"
        data = _written(source, out, {"a": 1})
        assert png_tools.scan_png(data, out.name).icc == srgb_profile()
        assert _provenance(out) == {"a": 1, "profile": "built-in sRGB"}
        again, _ = read_photo(out)
        assert (again.color.primaries, again.color.transfer) == ("bt709", "srgb")


def test_a_png_with_an_srgb_chunk_gets_the_built_in_srgb(tmp_path: Path) -> None:
    # Not an nclx source: the chunk is explicit sRGB (assumed False, no ICC), so the writer
    # states the colour space it declares. Disclosed in the report.
    pixels = np.full((4, 4, 3), 100, dtype=np.uint8)
    buffer = io.BytesIO()
    PILImage.fromarray(pixels).save(buffer, format="PNG", optimize=False)
    data = buffer.getvalue()
    split = data.index(b"IDAT") - 4
    source = tmp_path / "chunk.png"
    source.write_bytes(data[:split] + png_tools.chunk(b"sRGB", b"\x00") + data[split:])
    image, _ = read_photo(source)
    assert (image.color.assumed, image.color.icc_profile) == (False, None)
    out = tmp_path / "out.png"
    assert png_tools.scan_png(_written(source, out, {"a": 1}), "out.png").icc == srgb_profile()
    assert _provenance(out) == {"a": 1, "profile": "built-in sRGB"}


@pytest.mark.parametrize(
    ("primaries", "transfer"),
    [(9, 13), (9, 1), (9, 16), (9, 18), (1, 1), (1, 16), (1, 18), (12, 18)],
    ids=lambda value: str(value),
)
def test_class_nclx_outside_the_set_gets_no_iccp(
    tmp_path: Path, primaries: int, transfer: int
) -> None:
    out = tmp_path / "out.png"
    image, _ = read_photo(_nclx_heic(tmp_path / "x.heic", primaries, transfer))
    assert image.color.icc_profile is None
    data = _written(tmp_path / "x.heic", out, {"a": 1})
    assert png_tools.scan_png(data, "out.png").icc is None
    assert _provenance(out) == {"a": 1}


@pytest.mark.parametrize(
    "sample_id", ["jpeg-uniform-none", "png8-uniform-none", "tiff8-uniform-none"]
)
def test_class_untagged_keeps_question_3_and_gets_no_iccp(
    sample: Callable[[str], Path], tmp_path: Path, sample_id: str
) -> None:
    image, _ = read_photo(sample(sample_id))
    assert (image.color.primaries, image.color.transfer) == ("bt709", "srgb")
    assert image.color.assumed is True and image.color.icc_profile is None
    out = tmp_path / "out.png"
    data = _written(sample(sample_id), out, {"a": 1})
    assert png_tools.scan_png(data, "out.png").icc is None
    assert _provenance(out) == {"a": 1}


def test_a_provenance_off_write_still_embeds_the_srgb_profile(tmp_path: Path) -> None:
    out = tmp_path / "out.png"
    data = _written(_nclx_heic(tmp_path / "s.heic", 1), out)
    assert png_tools.scan_png(data, "out.png").icc == srgb_profile()
    assert _provenance(out) is None
