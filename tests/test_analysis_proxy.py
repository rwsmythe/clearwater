"""The analysis proxy rule (AD-5, ruling Q3): the twin of the GUI's block mean, quantised."""

from __future__ import annotations

import numpy as np
import pytest

from clearwater.analysis import block_mean, make_proxy, proxy_factor, quantise
from clearwater.gui import imaging

SIZES = [
    (2160, 3840),
    (2988, 5312),
    (3024, 4032),
    (6048, 8064),
    (1080, 1920),
    (540, 960),
    (541, 961),
    (1079, 1919),
    (1, 1),
    (7, 3),
]


@pytest.mark.parametrize(("height", "width"), SIZES)
def test_factor_equals_the_gui_statistics_factor(height: int, width: int) -> None:
    """``proxy_factor`` is ``gui.imaging.statistics_factor`` on every size (4K: 4, 960 x 540)."""
    assert proxy_factor(height, width) == imaging.statistics_factor(height, width)
    assert proxy_factor(width, height) == imaging.statistics_factor(width, height)
    assert proxy_factor(2160, 3840) == 4


@pytest.mark.parametrize("k", [1, 2, 3, 4, 5, 7, 11])
@pytest.mark.parametrize(("height", "width"), [(23, 37), (24, 36), (5, 9), (1, 13), (44, 44)])
def test_block_mean_cast_equals_the_gui_downscale_bit_for_bit(
    height: int, width: int, k: int
) -> None:
    """The float64 block mean, cast to float32, is ``gui.imaging.downscale`` bit for bit."""
    rng = np.random.default_rng(height * 100 + width + k)
    pixels = rng.uniform(0.0, 1.0, size=(height, width, 3)).astype(np.float32)
    ours = block_mean(pixels, k)
    assert ours.dtype == np.float64
    theirs = imaging.downscale(pixels, k)
    assert ours.shape == theirs.shape == imaging.downscale(pixels, k).shape
    assert np.array_equal(ours.astype(np.float32), theirs)


def test_quantisation_reproduces_the_integer_proxy_on_8_bit_frames() -> None:
    """On 8-bit-derived frames the proxy is ``floor((block sum + 8) / 16)`` at k = 4 (WP3.12).

    Premise P2 (WP3.11 ledger): quantising the float32 GUI mean misrounds about half the exact
    ties; the float64 mean does not. The planted float32 path is shown to fail here.
    """
    rng = np.random.default_rng(1)
    ties = planted_misses = 0
    for _ in range(40):
        levels = rng.integers(0, 256, size=(64, 64, 3), dtype=np.uint8)
        pixels = levels.astype(np.float32) / np.float32(255)
        sums = np.add.reduceat(
            np.add.reduceat(levels.astype(np.int64), np.arange(0, 64, 4), axis=0),
            np.arange(0, 64, 4),
            axis=1,
        )
        expected = ((sums + 8) // 16).astype(np.uint8)
        assert np.array_equal(quantise(block_mean(pixels, 4)), expected)
        planted = quantise(imaging.downscale(pixels, 4).astype(np.float64))
        planted_misses += int(np.count_nonzero(planted != expected))
        ties += int(np.count_nonzero(sums % 16 == 8))
    assert ties > 1000
    assert planted_misses > 0


def test_make_proxy_reduces_towards_540_and_rounds_half_up() -> None:
    """A 1080 x 1920 frame gives a 540 x 960 uint8 proxy; 0.5/255 rounds up; the range clips."""
    pixels = np.full((1080, 1920, 3), 0.5, np.float32)
    proxy = make_proxy(pixels)
    assert proxy.shape == (540, 960, 3) and proxy.dtype == np.uint8
    assert int(proxy[0, 0, 0]) == 128  # 127.5 rounds half up
    assert quantise(np.array([-0.2, 1.3, 0.5 / 255, 1.49 / 255])).tolist() == [0, 255, 1, 1]


def test_make_proxy_refuses_a_non_rgb_array() -> None:
    """A frame that is not ``(H, W, 3)`` is refused by name."""
    with pytest.raises(ValueError, match=r"\(H, W, 3\)"):
        make_proxy(np.zeros((4, 4), np.float32))
    with pytest.raises(ValueError, match="at least 1"):
        block_mean(np.zeros((4, 4, 3), np.float32), 0)
