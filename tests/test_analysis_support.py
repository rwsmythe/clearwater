"""Shared helpers for the WP3.11 analysis tests: frames, probes, test-local methods, counters.

Holds no tests. The methods here are test doubles with real whole-frame statistics (the stub
method's are zeros): a two-stage gray-world method, a one-stage method (D98) and an
Ancuti-like method whose first stage is source-only with a closed form (Y-1 (d), (e)).
"""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterator, Mapping, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from clearwater.analysis import AnalysisEngine
from clearwater.interfaces import (
    CacheKey,
    ColorDescription,
    Frame,
    Image,
    Parameter,
    ProbeResult,
    Stage,
    Statistics,
    VideoStreamInfo,
)
from clearwater.interfaces.stubs import StubArrayBackend, StubProgress, StubProxyCache

COLOR = ColorDescription("bt709", "bt709", "bt709", "full", 8, False, None)
KEY = CacheKey(size=1234, mtime_ns=5678, cache_version=2)
CFR_TIME_BASE = Fraction(1, 30000)
CFR_STEP = 1001
"""29.97 fps on a 1/30000 clock: 1001 ticks per frame."""


def make_frame(pixels: NDArray[Any], pts_ticks: int, time_base: Fraction, index: int) -> Frame:
    """Return an IF-1 frame of host float32 pixels."""
    return Frame(
        np.asarray(pixels, dtype=np.float32),
        "cpu",
        COLOR,
        False,
        pts=pts_ticks * time_base,
        pts_ticks=pts_ticks,
        time_base=time_base,
        index=index,
    )


def make_probe(
    time_base: Fraction = CFR_TIME_BASE,
    nb_frames: int | None = None,
    width: int = 12,
    height: int = 8,
) -> ProbeResult:
    """Return a probe result carrying the fields the engine reads."""
    video = VideoStreamInfo(
        "hevc", width, height, 8, "yuv420p", "left", COLOR, Fraction(30000, 1001), time_base,
        nb_frames, 0, False,
    )  # fmt: skip
    return ProbeResult(
        Path("clip.mp4"), "mov", Fraction(10), Fraction(0), video, (), (), (), (), None
    )


def synthetic_frames(
    count: int,
    step: int = CFR_STEP,
    time_base: Fraction = CFR_TIME_BASE,
    seed: int = 5,
    size: tuple[int, int] = (8, 12),
) -> list[Frame]:
    """Return ``count`` small frames whose colour drifts and flickers from frame to frame."""
    rng = np.random.default_rng(seed)
    base = rng.uniform(0.2, 0.8, size=(*size, 3))
    frames = []
    for index in range(count):
        tint = 1.0 + 0.15 * np.sin(index / 9.0) * np.array([1.0, -0.5, 0.3])
        tint = tint + rng.normal(0.0, 0.03, size=3)
        pixels = np.clip(base * tint, 0.0, 1.0)
        frames.append(make_frame(pixels, 7 + index * step, time_base, index))
    return frames


def frames_with_steps(steps: Sequence[int], time_base: Fraction = CFR_TIME_BASE) -> list[Frame]:
    """Return synthetic frames whose pts advance by ``steps`` in turn (a VFR clip)."""
    frames = synthetic_frames(len(steps) + 1, time_base=time_base)
    ticks = np.concatenate([[0], np.cumsum(steps)])
    return [
        make_frame(np.asarray(f.pixels), int(t), time_base, f.index)
        for f, t in zip(frames, ticks, strict=True)
    ]


def _host(image: Image) -> NDArray[np.float64]:
    """The image's pixels as float64 host values."""
    return np.asarray(image.pixels, dtype=np.float64)


class GrayWorld:
    """Two stages: ``white_balance`` (means, gains) and ``fusion`` (level, seen_gains).

    ``fusion`` measures the image corrected with the ``earlier`` gains it is given and records
    those gains in ``seen_gains``, so a test can see which gains a stage was measured with.
    ``render`` multiplies by the gains raised to ``strength``.
    """

    id = "grayworld"
    label = "Gray world (test)"

    def __init__(self) -> None:
        """Create the method with its call log."""
        self.parameters = (
            Parameter("strength", "float", 1.0, 0.0, 1.0, None, "basic", "S", "", 0.0),
            Parameter("gamma", "float", 1.0, 0.1, 3.0, None, "basic", "G", "", 1.0),
            Parameter("unused", "float", 0.0, 0.0, 1.0, None, "basic", "U", "", 0.0),
        )
        self.stages = (
            Stage(
                "white_balance", ("means", "gains"), ("means", "gains"), ("strength",), (), False
            ),
            Stage(
                "fusion", ("level", "seen_gains"), ("level",), ("gamma",), ("white_balance",), False
            ),
        )
        self.calls: list[tuple[str, NDArray[np.float64]]] = []
        self.images: list[NDArray[np.float64]] = []
        self.lock = threading.Lock()
        self.fail_on: str | None = None
        self.hook: Callable[[str], None] | None = None

    def analyze(
        self,
        stage: str,
        image: Image,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
    ) -> Statistics:
        """Measure ``stage`` on ``image``."""
        if self.hook is not None:
            self.hook(stage)
        if self.fail_on == stage:
            raise RuntimeError(f"planted failure in {stage}")
        pixels = _host(image)
        means = pixels.reshape(-1, 3).mean(axis=0)
        with self.lock:
            self.calls.append((stage, means.copy()))
            self.images.append(pixels)
        if stage == "white_balance":
            gains = means.mean() / means
            return {"means": means, "gains": gains}
        if stage == "fusion":
            gains = np.asarray(earlier["white_balance"]["gains"], dtype=np.float64)
            corrected = np.clip(pixels * gains ** float(params.get("strength", 1.0)), 0, 1)
            level = np.array([float(np.mean(corrected ** float(params.get("gamma", 1.0))))])
            return {"level": level, "seen_gains": gains.copy()}
        raise ValueError(f"unknown stage {stage!r}")

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        """Multiply by the gains raised to ``strength``."""
        gains = np.asarray(statistics["white_balance"]["gains"], dtype=np.float32)
        strength = np.float32(params.get("strength", 1.0))
        pixels = np.clip(np.asarray(image.pixels) * gains**strength, 0.0, 1.0)
        return Image(
            pixels.astype(np.float32), image.device, image.color, image.orientation_applied
        )

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        """No closed form."""
        return None

    def count(self, stage: str) -> int:
        """Return how many times ``stage`` was measured."""
        with self.lock:
            return sum(1 for name, _ in self.calls if name == stage)


class OneStage:
    """A flat (single-stage) method: the channel means, smoothed (D98)."""

    id = "flat"
    label = "Flat (test)"

    def __init__(self) -> None:
        """Create the method."""
        self.parameters: tuple[Parameter, ...] = ()
        self.stages = (Stage("flat", ("means",), ("means",), (), (), False),)

    def analyze(
        self, stage: str, image: Image, params: Mapping[str, Any], earlier: Mapping[str, Statistics]
    ) -> Statistics:
        """Return the channel means."""
        return {"means": _host(image).reshape(-1, 3).mean(axis=0)}

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        """Identity."""
        return image

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        """No closed form."""
        return None


class Compensated:
    """Ancuti-like: a source-only ``compensation`` stage with a closed form, then ``white_balance``.

    ``compensation`` measures the channel means and ``alpha = min(cap, 1 - mean red)``; its
    closed form recomputes ``alpha`` from the measured means with the current ``cap``.
    ``white_balance`` measures gains of the image compensated by the smoothed alpha.
    """

    id = "compensated"
    label = "Compensated (test)"

    def __init__(self) -> None:
        """Create the method with call counters."""
        self.parameters = (
            Parameter("cap", "float", 0.5, 0.0, 1.0, None, "basic", "C", "", 0.0),
            Parameter("strength", "float", 1.0, 0.0, 1.0, None, "basic", "S", "", 0.0),
        )
        self.stages = (
            Stage("compensation", ("means", "alpha"), ("means", "alpha"), ("cap",), (), True),
            Stage("white_balance", ("gains",), ("gains",), ("strength",), ("compensation",), False),
        )
        self.analyzed: list[str] = []
        self.closed: list[str] = []
        self.lock = threading.Lock()

    def analyze(
        self, stage: str, image: Image, params: Mapping[str, Any], earlier: Mapping[str, Statistics]
    ) -> Statistics:
        """Measure ``stage``."""
        with self.lock:
            self.analyzed.append(stage)
        pixels = _host(image)
        means = pixels.reshape(-1, 3).mean(axis=0)
        if stage == "compensation":
            return {"means": means, "alpha": np.array([min(float(params["cap"]), 1 - means[0])])}
        alpha = float(earlier["compensation"]["alpha"][0])
        compensated = means * np.array([1.0 + alpha, 1.0, 1.0])
        strength = float(params["strength"])
        return {"gains": (compensated.mean() / compensated) ** strength}

    def render(
        self, image: Image, params: Mapping[str, Any], statistics: Mapping[str, Statistics]
    ) -> Image:
        """Identity."""
        return image

    def closed_form(
        self,
        stage: str,
        params: Mapping[str, Any],
        earlier: Mapping[str, Statistics],
        measured: Statistics,
    ) -> Statistics | None:
        """Recompute ``alpha`` for ``compensation``; None for ``white_balance``."""
        with self.lock:
            self.closed.append(stage)
        if stage != "compensation":
            return None
        means = np.asarray(measured["means"], dtype=np.float64)
        return {"means": means, "alpha": np.array([min(float(params["cap"]), 1 - means[0])])}


class CountingCache(StubProxyCache):
    """The stub cache, counting proxy reads and completion marks."""

    def __init__(self) -> None:
        """Create an empty counting cache."""
        super().__init__()
        self.proxy_reads = 0
        self.marks = 0
        self.source_reads = 0
        self.lock = threading.Lock()

    def proxy(self, key: CacheKey, pts_ticks: int) -> NDArray[np.uint8]:
        """Count, then return the proxy."""
        with self.lock:
            self.proxy_reads += 1
        return super().proxy(key, pts_ticks)

    def source_statistics(self, key: CacheKey, stage: str, pts_ticks: int) -> Statistics:
        """Count, then return the statistics."""
        with self.lock:
            self.source_reads += 1
        return super().source_statistics(key, stage, pts_ticks)

    def mark_complete(self, key: CacheKey) -> None:
        """Count, then mark."""
        self.marks += 1
        super().mark_complete(key)


class ListSource:
    """A frame source over a list, counting the frames it yields; optional pause and failure."""

    def __init__(self, frames: Sequence[Frame], probe: ProbeResult) -> None:
        """Create the source."""
        self._frames = list(frames)
        self._probe = probe
        self.yielded = 0
        self.iterations = 0
        self.pause_after: int | None = None
        self.paused = threading.Event()
        self.resume = threading.Event()
        self.fail_after: int | None = None

    def probe(self, path: Path) -> ProbeResult:
        """Return the probe given at construction."""
        return self._probe

    def frames(
        self,
        probe: ProbeResult,
        *,
        hw_decode: bool,
        start_s: Fraction | None = None,
        end_s: Fraction | None = None,
    ) -> Iterator[Frame]:
        """Yield the frames in order."""
        self.iterations += 1
        for frame in self._frames:
            if self.fail_after is not None and self.yielded >= self.fail_after:
                raise OSError("planted read error")
            if self.pause_after is not None and self.yielded == self.pause_after:
                self.paused.set()
                self.resume.wait(10)
            self.yielded += 1
            yield frame


def make_engine(
    method: Any,
    frames: Sequence[Frame],
    *,
    cache: StubProxyCache | None = None,
    params: Mapping[str, Any] | None = None,
    time_base: Fraction = CFR_TIME_BASE,
    nb_frames: int | None = None,
    source: Any = None,
    window_s: float = 2.0,
    kind: str = "median_gaussian",
) -> tuple[AnalysisEngine, Any, StubProxyCache]:
    """Return an engine over ``frames`` with a counting cache and source."""
    probe = make_probe(time_base, nb_frames if nb_frames is not None else len(frames))
    the_source = source if source is not None else ListSource(frames, probe)
    the_cache = cache if cache is not None else CountingCache()
    defaults = {p.name: p.default for p in method.parameters}
    defaults.update(params or {})
    engine = AnalysisEngine(
        method=method,
        backend=StubArrayBackend(),
        cache=the_cache,
        key=KEY,
        source=the_source,
        probe=probe,
        params=defaults,
        window_s=window_s,
        kind=kind,
    )
    return engine, the_source, the_cache


def run(engine: AnalysisEngine, progress: StubProgress | None = None) -> Any:
    """Run a full analysis job synchronously and return its result."""
    return engine.analysis_job()(progress or StubProgress())
