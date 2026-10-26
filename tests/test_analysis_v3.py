"""V3 (engine side) with test-local methods (ruling Q7), on two synthetic clips (ruling V3-1).

V3 measures, in the untouched region of the output, the per-frame mean L*, a*, b* and a contrast
measure, and takes flicker as the standard deviation of their frame-to-frame differences: "pass
if flicker with smoothing <= 25% of flicker with per-frame (unsmoothed) statistics". AD-14: the
mean absolute frame-to-frame difference of the corrected output inside ``ad14-mask`` "must stay
under 0.5/255 after smoothing". Two doubles with real whole-frame statistics: gray-world gains
alone, and gains plus a percentile stretch (c3's two kinds of statistic, ``gains`` and
``bounds``). The product method's V3 is WP4.2's.

CHARC ruling V3-1 (WP3.11 ledger): the ``ad14-flicker`` disc sweeps steadily, so the whole-frame
statistics follow a smooth curve that a centred smoother must keep; there the tests assert
AD-14's bound and RECORD V3's four ratios (0.39-0.49 when ruled) without asserting them. V3's 25 %
is asserted on a clip built here: the AD-14 texture with a fixed patch whose position is re-drawn
at random each frame inside the lower third (seeded), so the statistics vary like white noise and
the ratio cannot be tuned by choosing a frequency; the measured region is the upper half, which
the patch never touches.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterable, Iterator, Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image as PILImage

from clearwater.analysis import AnalysisEngine
from clearwater.interfaces import Frame, Image, ProbeResult, Stage, Statistics
from fixtures import flicker as ad14
from test_analysis_support import CFR_STEP, CFR_TIME_BASE, GrayWorld, make_engine, make_frame

WIDTH, HEIGHT = 960, 540
TIME_BASE = Fraction(1001, 30000)
"""The clip's time base (manifest): one tick per frame at 30000/1001."""

LUMA = np.array([0.2126, 0.7152, 0.0722])


def decoded(path: Path) -> Iterator[NDArray[np.uint8]]:
    """Yield the clip's frames as rgb24, one at a time (FFmpeg, frames as stored)."""
    command = [
        "ffmpeg", "-nostdin", "-hide_banner", "-v", "error", "-i", str(path),
        "-map", "0:v:0", "-fps_mode", "passthrough", "-f", "rawvideo", "-pix_fmt", "rgb24", "-",
    ]  # fmt: skip
    size = WIDTH * HEIGHT * 3
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL) as process:
        assert process.stdout is not None
        while block := process.stdout.read(size):
            assert len(block) == size
            yield np.frombuffer(block, dtype=np.uint8).reshape(HEIGHT, WIDTH, 3)
    assert process.returncode == 0


class PipeSource:
    """A frame source that decodes the clip with FFmpeg on every pass (pts ticks 0, 1, ...)."""

    def __init__(self, path: Path) -> None:
        self._path = path

    def probe(self, path: Path) -> ProbeResult:
        raise NotImplementedError

    def frames(
        self,
        probe: ProbeResult,
        *,
        hw_decode: bool,
        start_s: Fraction | None = None,
        end_s: Fraction | None = None,
    ) -> Iterator[Frame]:
        for index, rgb in enumerate(decoded(self._path)):
            yield make_frame(rgb.astype(np.float32) / 255.0, index, TIME_BASE, index)


class GainsStretch(GrayWorld):
    """Gray-world gains, then a stretch between the 0.5th and 99.5th luma percentiles."""

    def __init__(self) -> None:
        super().__init__()
        self.stages = (
            self.stages[0],
            Stage("fusion", ("bounds",), ("bounds",), ("gamma",), ("white_balance",), False),
        )

    def analyze(
        self, stage: str, image: Image, params: Mapping[str, Any], earlier: Mapping[str, Statistics]
    ) -> Statistics:
        if stage == "white_balance":
            return super().analyze(stage, image, params, earlier)
        gains = np.asarray(earlier["white_balance"]["gains"])
        luma = np.clip(np.asarray(image.pixels, np.float64) * gains, 0, 1) @ LUMA
        return {"bounds": np.percentile(luma, [0.5, 99.5])}

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        gains = np.asarray(statistics["white_balance"]["gains"])
        low, high = statistics["fusion"]["bounds"]
        pixels = np.clip(np.asarray(image.pixels, np.float64) * gains, 0, 1)
        out = np.clip((pixels - low) / (high - low), 0, 1).astype(np.float32)
        return Image(out, image.device, image.color, image.orientation_applied)


MEASURES = ("L*", "a*", "b*", "contrast")
"""V3's per-frame measures of the untouched region: mean L*, a*, b* and a contrast measure (the
standard deviation of L* over the region)."""

_SRGB_TO_XYZ = np.array(
    [[0.4124564, 0.3575761, 0.1804375], [0.2126729, 0.7151522, 0.0721750],
     [0.0193339, 0.1191920, 0.9503041]]
)  # fmt: skip
_WHITE = np.array([0.95047, 1.0, 1.08883])


def lab(rgb: NDArray[np.float64]) -> NDArray[np.float64]:
    """CIELAB (D65) of display-encoded RGB in [0, 1], read with the sRGB transfer, ``(N, 3)``."""
    linear = np.where(rgb <= 0.04045, rgb / 12.92, ((rgb + 0.055) / 1.055) ** 2.4)
    xyz = (linear @ _SRGB_TO_XYZ.T) / _WHITE
    f = np.where(xyz > (6 / 29) ** 3, np.cbrt(xyz), xyz / (3 * (6 / 29) ** 2) + 4 / 29)
    return np.stack(
        [116 * f[:, 1] - 16, 500 * (f[:, 0] - f[:, 1]), 200 * (f[:, 1] - f[:, 2])], axis=1
    )


def flicker(
    frames: Iterable[Frame],
    mask: NDArray[np.bool_],
    method: GrayWorld,
    params: Mapping[str, Any],
    statistics: Callable[[int], Mapping[str, Statistics] | None],
) -> tuple[float, NDArray[np.float64]]:
    """Render the frames and measure the untouched region (``mask``) of the output.

    Args:
        frames: The clip's frames, in order.
        mask: The measured region.
        method: The test-local method that renders.
        params: Its parameters.
        statistics: The record for a frame's pts ticks (smoothed or provisional).

    Returns:
        AD-14's figure (the mean absolute frame-to-frame pixel difference, in /255) and V3's
        flicker per measure of :data:`MEASURES` (the standard deviation of the frame-to-frame
        differences of each per-frame measure).
    """
    previous: NDArray[np.float64] | None = None
    differences = []
    measures = []
    for frame in frames:
        record = statistics(frame.pts_ticks)
        assert record is not None
        out = np.asarray(method.render(frame, params, record).pixels, dtype=np.float64)
        region = out[mask]
        if previous is not None:
            differences.append(float(np.mean(np.abs(region - previous))) * 255.0)
        previous = region
        values = lab(region)
        measures.append([*values.mean(axis=0), float(np.std(values[:, 0]))])
    v3 = np.std(np.diff(np.array(measures), axis=0), axis=0)
    return float(np.mean(differences)), v3


def _clip_frames(path: Path) -> Iterator[Frame]:
    """The decoded ``ad14-flicker`` frames (pts ticks 0, 1, ...)."""
    return PipeSource(path).frames(None, hw_decode=False)  # type: ignore[arg-type]


def _figures(
    unsmoothed: float,
    smoothed: float,
    v3_unsmoothed: NDArray[np.float64],
    v3_smoothed: NDArray[np.float64],
) -> str:
    """One line of figures for the test log."""
    return (
        f"AD-14 /255 unsmoothed {unsmoothed:.4f}, smoothed {smoothed:.4f}; V3 per measure "
        f"{MEASURES}: unsmoothed {np.round(v3_unsmoothed, 6).tolist()}, smoothed "
        f"{np.round(v3_smoothed, 6).tolist()}, ratio "
        f"{np.round(v3_smoothed / v3_unsmoothed, 3).tolist()}"
    )


def _measure(
    sample: Callable[[str], Path], method: GrayWorld
) -> tuple[float, float, NDArray[np.float64], NDArray[np.float64]]:
    """Analyse ``ad14-flicker``; return AD-14's (unsmoothed, smoothed) and V3's per measure."""
    clip = sample("ad14-flicker")
    with PILImage.open(sample("ad14-mask")) as image:
        mask = np.asarray(image.convert("L")) > 127
    assert mask.shape == (HEIGHT, WIDTH) and mask.any() and not mask[HEIGHT // 2 :].any()
    engine: AnalysisEngine
    engine, _, _ = make_engine(
        method, [], source=PipeSource(clip), time_base=TIME_BASE, nb_frames=90
    )
    result = engine.analysis_job()(_Progress())
    assert result.ok, result.failure
    assert len(engine.store.axis()) == 90
    params = engine.parameters
    smoothed, v3_smoothed = flicker(
        _clip_frames(clip), mask, method, params, engine.smoothed_record
    )
    unsmoothed, v3_unsmoothed = flicker(
        _clip_frames(clip), mask, method, params, engine.provisional_record
    )
    name = method.__class__.__name__
    print(f"ad14-flicker {name}: {_figures(unsmoothed, smoothed, v3_unsmoothed, v3_smoothed)}")
    return unsmoothed, smoothed, v3_unsmoothed, v3_smoothed


@pytest.mark.parametrize("make_method", [GrayWorld, GainsStretch])
def test_ad14_smoothed_flicker_stays_under_half_a_level(
    sample: Callable[[str], Path],
    make_method: Callable[[], GrayWorld],
    record_property: Callable[[str, object], None],
) -> None:
    """AD-14: under 0.5/255 after smoothing; V3's four ratios RECORDED, not asserted (V3-1)."""
    unsmoothed, smoothed, v3_unsmoothed, v3_smoothed = _measure(sample, make_method())
    assert 0.0 < smoothed < unsmoothed
    assert smoothed < 0.5
    ratios = v3_smoothed / v3_unsmoothed
    assert np.all(np.isfinite(ratios))
    record_property("v3_ratios", dict(zip(MEASURES, np.round(ratios, 3).tolist(), strict=True)))


# --- the jittering-patch clip (ruling V3-1) -------------------------------------------------

JITTER_WIDTH, JITTER_HEIGHT = 480, 270
"""The AD-14 texture at half size (the stub cache holds every proxy in memory)."""

JITTER_FRAMES = 90
"""As many frames as ``ad14-flicker`` (3 s at 30000/1001)."""

JITTER_SEED = 14
"""The positions' seed (fixed before the first run)."""

PATCH_SIDE = 60
"""The patch's side in pixels: a fixed size; the lower third is 90 rows."""

PATCH_COLOUR = ad14.DISC_COLOUR
"""The patch's colour: a fixed brightness, the AD-14 disc's."""

BAND_TOP = JITTER_HEIGHT - JITTER_HEIGHT // 3
"""The first row of the lower third; the patch lies wholly in rows ``BAND_TOP`` and below."""

REGION_ROWS = JITTER_HEIGHT // 2
"""The measured region is the upper half, rows ``0 .. REGION_ROWS - 1``."""


def jitter_clip() -> tuple[NDArray[np.uint8], list[NDArray[np.uint8]], list[tuple[int, int]]]:
    """Return the still, the frames and each frame's patch corner (row, column).

    The patch's corner is drawn uniformly at random every frame, independently, inside the
    lower-third band, so the whole-frame statistics change like white noise from frame to frame.
    """
    still = ad14.texture(JITTER_WIDTH, JITTER_HEIGHT)
    rng = np.random.default_rng(JITTER_SEED)
    frames: list[NDArray[np.uint8]] = []
    corners: list[tuple[int, int]] = []
    for _ in range(JITTER_FRAMES):
        row = int(rng.integers(BAND_TOP, JITTER_HEIGHT - PATCH_SIDE + 1))
        column = int(rng.integers(0, JITTER_WIDTH - PATCH_SIDE + 1))
        frame = still.copy()
        frame[row : row + PATCH_SIDE, column : column + PATCH_SIDE] = PATCH_COLOUR
        frames.append(frame)
        corners.append((row, column))
    return still, frames, corners


def _as_frames(images: list[NDArray[np.uint8]]) -> list[Frame]:
    """IF-1 frames at 30000/1001 (1001 ticks on a 1/30000 clock)."""
    return [
        make_frame(image.astype(np.float32) / 255.0, index * CFR_STEP, CFR_TIME_BASE, index)
        for index, image in enumerate(images)
    ]


def test_the_jittering_patch_never_touches_the_measured_region() -> None:
    """The patch lies in the lower third in every frame; the upper half is the still's, exactly."""
    still, frames, corners = jitter_clip()
    assert len(frames) == JITTER_FRAMES and len(set(corners)) == JITTER_FRAMES
    for frame, (row, _) in zip(frames, corners, strict=True):
        changed = np.flatnonzero(np.any(frame != still, axis=2).any(axis=1))
        assert changed.size > 0 and changed.min() >= BAND_TOP >= REGION_ROWS
        assert row >= BAND_TOP and row + PATCH_SIDE <= JITTER_HEIGHT
        assert np.array_equal(frame[:REGION_ROWS], still[:REGION_ROWS])
    assert np.array_equal(
        ad14.region_mask(JITTER_WIDTH, JITTER_HEIGHT).any(axis=1),
        np.arange(JITTER_HEIGHT) < REGION_ROWS,
    )


@pytest.mark.parametrize("make_method", [GrayWorld, GainsStretch])
def test_v3_ratio_on_the_jittering_patch_clip(
    make_method: Callable[[], GrayWorld], record_property: Callable[[str, object], None]
) -> None:
    """V3: per measure (L*, a*, b*, contrast), the smoothed flicker <= 25 % of the per-frame."""
    method = make_method()
    _, images, _ = jitter_clip()
    frames = _as_frames(images)
    engine, _, _ = make_engine(method, frames)
    result = engine.analysis_job()(_Progress())
    assert result.ok, result.failure
    mask = ad14.region_mask(JITTER_WIDTH, JITTER_HEIGHT)
    params = engine.parameters
    smoothed, v3_smoothed = flicker(frames, mask, method, params, engine.smoothed_record)
    unsmoothed, v3_unsmoothed = flicker(frames, mask, method, params, engine.provisional_record)
    name = method.__class__.__name__
    print(f"jitter {name}: {_figures(unsmoothed, smoothed, v3_unsmoothed, v3_smoothed)}")
    ratios = v3_smoothed / v3_unsmoothed
    record_property("v3_ratios", dict(zip(MEASURES, np.round(ratios, 3).tolist(), strict=True)))
    assert np.all(v3_unsmoothed > 0)
    assert np.all(v3_smoothed <= 0.25 * v3_unsmoothed), ratios


class _Progress:
    """A progress that is never cancelled."""

    def report(self, done: int, total: int | None, message: str) -> None:
        """Ignore."""

    def cancelled(self) -> bool:
        """Never."""
        return False
