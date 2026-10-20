"""WP3.5: planar integer samples to IF-1 float32 RGB and back (D39, spec 5.2)."""

from __future__ import annotations

import numpy as np
import pytest

from clearwater.color import ColorError, planes_to_rgb, rgb_frame_bytes, rgb_to_planes


def planar(g: np.ndarray, b: np.ndarray, r: np.ndarray, bit_depth: int) -> bytes:
    """Build a G, B, R planar frame from three integer planes."""
    dtype = np.uint8 if bit_depth == 8 else np.dtype("<u2")
    return b"".join(p.astype(dtype).tobytes() for p in (g, b, r))


@pytest.mark.parametrize("bit_depth", [8, 10])
def test_every_code_round_trips_exactly(bit_depth: int) -> None:
    top = 2**bit_depth - 1
    codes = np.arange(top + 1)
    # Three planes holding the codes shifted against each other, so every code appears in each.
    g, b, r = (np.roll(codes, k).reshape(1, -1) for k in (0, 1, 2))
    data = planar(g, b, r, bit_depth)
    rgb = planes_to_rgb(data, width=top + 1, height=1, bit_depth=bit_depth)
    assert rgb.dtype == np.float32 and rgb.shape == (1, top + 1, 3)
    assert rgb.min() == 0.0 and rgb.max() == 1.0
    assert rgb_to_planes(rgb, bit_depth=bit_depth) == data


@pytest.mark.parametrize("bit_depth", [8, 10])
def test_random_frame_round_trips_exactly(bit_depth: int) -> None:
    rng = np.random.default_rng(3)
    top = 2**bit_depth - 1
    g, b, r = (rng.integers(0, top + 1, (37, 53)) for _ in range(3))
    data = planar(g, b, r, bit_depth)
    rgb = planes_to_rgb(data, width=53, height=37, bit_depth=bit_depth)
    assert rgb_to_planes(rgb, bit_depth=bit_depth) == data


def test_plane_order_is_g_b_r() -> None:
    g, b, r = (np.full((2, 3), v) for v in (10, 20, 30))
    rgb = planes_to_rgb(planar(g, b, r, 8), width=3, height=2, bit_depth=8)
    assert np.allclose(rgb[0, 0], np.array([30, 10, 20], np.float32) / 255)
    # And back: RGB (30, 10, 20) is written as the planes G=10, B=20, R=30.
    assert rgb_to_planes(rgb, bit_depth=8) == planar(g, b, r, 8)


def test_ten_bit_is_never_truncated() -> None:
    g = np.array([[1, 2, 3, 1023]])
    data = planar(g, g, g, 10)
    assert len(data) == rgb_frame_bytes(4, 1, 10) == 24
    rgb = planes_to_rgb(data, width=4, height=1, bit_depth=10)
    assert rgb[0, :, 0].tolist() == pytest.approx([1 / 1023, 2 / 1023, 3 / 1023, 1.0], abs=1e-7)
    # An 8-bit view of the same data would lose the low bits; the 10-bit codes survive.
    assert rgb_to_planes(rgb, bit_depth=10) == data
    # Little-endian 16-bit words: 1023 is 0xFF 0x03.
    assert data[6:8] == bytes([0xFF, 0x03])


def test_quantisation_rounds_half_to_even_and_clips() -> None:
    values = np.array([[[-0.5, 0.5 / 255, 1.5 / 255], [2.5 / 255, 3.5 / 255, 2.0]]], np.float32)
    out = np.frombuffer(rgb_to_planes(values, bit_depth=8), np.uint8).reshape(3, 1, 2)
    # R plane is channel 0 (plane index 2), G channel 1 (plane 0), B channel 2 (plane 1).
    assert out[2, 0].tolist() == [0, 2]  # R: clip(-0.5) = 0; 2.5 -> 2 (half to even)
    assert out[0, 0].tolist() == [0, 4]  # G: 0.5 -> 0; 3.5 -> 4
    assert out[1, 0].tolist() == [2, 255]  # B: 1.5 -> 2; clip(2.0) = 255


def test_input_is_not_modified_and_no_float_drift_in_the_way_in() -> None:
    g = np.arange(12).reshape(3, 4)
    rgb = planes_to_rgb(planar(g, g, g, 8), width=4, height=3, bit_depth=8)
    copy = rgb.copy()
    rgb_to_planes(rgb, bit_depth=8)
    assert np.array_equal(rgb, copy)
    # The way in is a plain division by 255: float32(k / 255) exactly.
    assert np.array_equal(rgb[..., 0], (g / 255).astype(np.float32))


def test_accepts_bytes_bytearray_and_memoryview() -> None:
    data = bytes(range(12))
    base = planes_to_rgb(data, width=2, height=2, bit_depth=8)
    for buffer in (bytearray(data), memoryview(data)):
        assert np.array_equal(planes_to_rgb(buffer, width=2, height=2, bit_depth=8), base)


def test_refusals_are_named() -> None:
    with pytest.raises(ColorError, match="bit depth 12"):
        planes_to_rgb(bytes(12), width=2, height=2, bit_depth=12)
    with pytest.raises(ColorError, match="is 12 bytes, not 11"):
        planes_to_rgb(bytes(11), width=2, height=2, bit_depth=8)
    with pytest.raises(ColorError, match="is 24 bytes, not 12"):
        planes_to_rgb(bytes(12), width=2, height=2, bit_depth=10)
    with pytest.raises(ColorError, match="float32"):
        rgb_to_planes(np.zeros((2, 2, 3), np.float64), bit_depth=8)  # type: ignore[arg-type]
    with pytest.raises(ColorError, match="float32"):
        rgb_to_planes(np.zeros((2, 2, 4), np.float32), bit_depth=8)
    with pytest.raises(ColorError, match="NaN"):
        rgb_to_planes(np.full((2, 2, 3), np.nan, np.float32), bit_depth=8)
    with pytest.raises(ColorError, match="bit depth 16"):
        rgb_to_planes(np.zeros((2, 2, 3), np.float32), bit_depth=16)
    assert rgb_frame_bytes(3840, 2160, 8) == 3 * 3840 * 2160


def test_planted_defects_in_the_conversion_are_distinguishable() -> None:
    # The planted wrong readings: planes taken as R, G, B; 10-bit scaled by 255.
    g, b, r = (np.full((1, 2), v) for v in (100, 500, 900))
    data = planar(g, b, r, 10)
    rgb = planes_to_rgb(data, width=2, height=1, bit_depth=10)
    assert rgb[0, 0].tolist() == pytest.approx([900 / 1023, 100 / 1023, 500 / 1023], abs=1e-7)
    assert not np.allclose(rgb[0, 0], np.array([100, 500, 900]) / 1023)  # R, G, B order
    assert (np.array([100, 500, 900]) / 255).max() > 1  # scaled by 255: out of [0, 1]
