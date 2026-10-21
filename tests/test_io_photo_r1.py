"""Tests of the WP3.6 round-1 remediation (Reviewer A findings #1, #3, #4, #5, #9, #10).

Each test fails on the code at round-1 head ``983bff1`` (the fail-before evidence is in the
ledger) and passes on the remediated code.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from clearwater.io.photo import PhotoReadError, read_photo


def _patched(source: Path, out: Path, old: bytes, new: bytes) -> Path:
    """Copy ``source`` to ``out`` with one occurrence of ``old`` replaced by ``new`` (same length)."""
    data = source.read_bytes()
    assert len(old) == len(new)
    at = data.find(old)
    assert at >= 0, f"{old!r} not found"
    out.write_bytes(data[:at] + new + data[at + len(old) :])
    return out


# --- #1: a HEIC colour box of type rICC is a profile too ----------------------------------------


def test_a_heic_ricc_colour_box_is_carried_like_prof(
    sample: Callable[[str], Path], tmp_path: Path
) -> None:
    source = sample("heic8-uniform-display-p3")
    plain, _ = read_photo(source)
    assert plain.color.icc_profile is not None
    patched = _patched(source, tmp_path / "ricc.heic", b"colrprof", b"colrrICC")
    image, _ = read_photo(patched)
    assert image.color.icc_profile == plain.color.icc_profile
    assert (image.color.primaries, image.color.transfer) == ("display-p3", "srgb")
    assert image.color.assumed is False


def test_a_heic_with_neither_prof_nor_ricc_keeps_the_nclx_route(tmp_path: Path) -> None:
    pytest.importorskip("pillow_heif")
    import numpy as np
    import pillow_heif

    pixels = np.full((16, 16, 3), 128, dtype=np.uint8)
    nclx = {
        "color_primaries": 12,
        "transfer_characteristics": 13,
        "matrix_coefficients": 6,
        "full_range_flag": 1,
    }
    path = tmp_path / "nclx.heic"
    pillow_heif.encode("RGB", (16, 16), pixels.tobytes(), str(path), quality=90, nclx_profile=nclx)
    image, _ = read_photo(path)
    assert image.color.icc_profile is None
    assert image.color.primaries == "display-p3"


assert PhotoReadError  # imported for the tests added below
