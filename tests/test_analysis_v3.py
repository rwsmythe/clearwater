"""V3 (engine side) on the AD-14 flicker clip, with test-local methods (ruling Q7).

V3: "pass if flicker with smoothing <= 25% of flicker with per-frame (unsmoothed) statistics";
AD-14: the mean absolute frame-to-frame difference of the corrected output inside
``ad14-mask`` "must stay under 0.5/255 after smoothing". Two doubles with real whole-frame
statistics: gray-world gains alone, and gains plus a percentile stretch (c3's two kinds of
statistic, ``gains`` and ``bounds``). The product method's V3 is WP4.2's.

Finding (WP3.11 ledger, V3-1): on this clip the disc's linear sweep makes the whole-frame
statistics DRIFT smoothly, which a centred filter keeps, so smoothing leaves 55-64 % of the
per-frame flicker, not <= 25 %; AD-14's absolute bound is met by two orders of magnitude.
"""

from __future__ import annotations

import subprocess
from collections.abc import Callable, Iterator, Mapping
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
import pytest
from numpy.typing import NDArray
from PIL import Image as PILImage

from clearwater.analysis import AnalysisEngine
from clearwater.interfaces import Frame, Image, ProbeResult, Stage, Statistics
from test_analysis_support import GrayWorld, make_engine, make_frame

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


def flicker(
    path: Path,
    mask: NDArray[np.bool_],
    method: GrayWorld,
    params: Mapping[str, Any],
    statistics: Callable[[int], Mapping[str, Statistics] | None],
) -> float:
    """Mean absolute frame-to-frame difference (in /255) of the rendered output inside ``mask``."""
    previous: NDArray[np.float64] | None = None
    differences = []
    for index, rgb in enumerate(decoded(path)):
        frame = make_frame(rgb.astype(np.float32) / 255.0, index, TIME_BASE, index)
        record = statistics(index)
        assert record is not None
        out = np.asarray(method.render(frame, params, record).pixels, dtype=np.float64)
        region = out[mask] * 255.0
        if previous is not None:
            differences.append(float(np.mean(np.abs(region - previous))))
        previous = region
    return float(np.mean(differences))


def _measure(sample: Callable[[str], Path], method: GrayWorld) -> tuple[float, float]:
    """Analyse the clip; return (unsmoothed, smoothed) flicker inside the mask."""
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
    smoothed = flicker(clip, mask, method, params, engine.smoothed_record)
    unsmoothed = flicker(clip, mask, method, params, engine.provisional_record)
    print(
        f"{method.__class__.__name__}: flicker /255 unsmoothed {unsmoothed:.4f}, "
        f"smoothed {smoothed:.4f}"
    )
    return unsmoothed, smoothed


@pytest.mark.parametrize("make_method", [GrayWorld, GainsStretch])
def test_ad14_smoothed_flicker_stays_under_half_a_level(
    sample: Callable[[str], Path], make_method: Callable[[], GrayWorld]
) -> None:
    """AD-14: under 0.5/255 after smoothing; smoothing reduces the per-frame flicker."""
    unsmoothed, smoothed = _measure(sample, make_method())
    assert 0.0 < smoothed < unsmoothed
    assert smoothed < 0.5


@pytest.mark.xfail(
    strict=True,
    reason="V3-1 (WP3.11 ledger): the AD-14 sweep drifts smoothly; awaiting a ruling",
)
@pytest.mark.parametrize("make_method", [GrayWorld, GainsStretch])
def test_v3_ratio_on_the_ad14_clip(
    sample: Callable[[str], Path], make_method: Callable[[], GrayWorld]
) -> None:
    """V3's ratio: smoothed flicker <= 25 % of the per-frame flicker."""
    unsmoothed, smoothed = _measure(sample, make_method())
    assert smoothed <= 0.25 * unsmoothed


class _Progress:
    """A progress that is never cancelled."""

    def report(self, done: int, total: int | None, message: str) -> None:
        """Ignore."""

    def cancelled(self) -> bool:
        """Never."""
        return False
