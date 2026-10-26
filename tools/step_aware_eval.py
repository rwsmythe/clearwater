"""WP3.11 design task (AD-3, question 6): step-aware smoothing on the deep clip's lighting step.

Evaluates the candidate kinds of :mod:`clearwater.analysis.smoothing` (``median_gaussian_cut``,
``median_bilateral``) against the default ``median_gaussian`` 2.0 s on WP1.4b claim 10b's
excerpt of GX011600 (the step "0.90 s into the excerpt (pts 662.962 s)"), STAGED as the product
analyses: each stage measured with the smoothed earlier stages, using the read-only prototype's
``measure`` and ``render`` for ``c3`` and ``ancuti2018``, and the product's smoother over pts.

The extracted span is the original 6 s excerpt widened by ``LEAD_S`` before and ``TAIL_S``
after, so every evaluated frame is beyond the staged analysis's reach from both ends (DR-25 (3):
the span length and the edge-free frame count are recorded). Proxies are FFmpeg's 540-line
resize (as WP1.4b), quantised to uint8 with the product's rule (AD-5's stored form).

Figures per method and kind, on the original excerpt's frames (WP1.4b's measures, reused from
``tools/noise_experiments.py``): the rendered step (R, G, B, luma change across +-1 s, over the
source's), the flicker away from the step (frame steps more than 1 s from it) and over all
steps, and the peak frame step. The default does not change here (spec 7.2, owner-reserved).

Footage is read only through ``tools/local_config.find_footage_file``; outputs go under the
worktree's ``work/wp3.11/`` (never the footage folder). No GoPro data stream is read.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from collections.abc import Callable, Sequence
from fractions import Fraction
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import NDArray

from clearwater.analysis import quantise, reach, smooth_series
from local_config import find_footage_file, load_local_config
from lookcheck.frames import OutputRoots, excerpt, read_png16
from noise_experiments import detect_step, signal_steps
from prototype import temporal
from prototype.backend import Backend, select_backend
from prototype.clip import make_params
from prototype.temporal import Series

CLIP = "GX011600"
"""The deep clip (WP1.3D, WP1.4b claim 10b)."""

EXCERPT_START_S = Fraction("662.0310333333333")
"""WP1.3D's excerpt start (its record: 6 s, 179 frames, first pts 662.0614 s)."""

EXCERPT_DURATION_S = Fraction(6)
"""The original excerpt's length."""

LEAD_S = Fraction(3)
"""Seconds extracted before the excerpt (beyond Ancuti's 90-frame staged reach)."""

TAIL_S = Fraction(3)
"""Seconds extracted after the excerpt."""

WINDOW_S = 2.0
"""The window every kind is evaluated at (the AD-3 default)."""

KINDS = ("median_gaussian", "median_gaussian_cut", "median_bilateral")
"""The default first, then the step-aware candidates."""

METHODS = ("c3", "ancuti2018")
"""The methods evaluated (the prototype's parameter defaults)."""

AWAY_S = 1.0
"""Frame steps farther than this from the step count as "away from the step"."""


def default_out() -> Path:
    """The worktree's ``work/wp3.11/step-aware`` folder."""
    return Path(__file__).resolve().parents[1] / "work" / "wp3.11" / "step-aware"


def load_proxies(
    out: Path, footage_root: Path, log: Callable[[str], None]
) -> tuple[NDArray[np.uint8], NDArray[np.int64], Fraction]:
    """Extract the widened span as uint8 540-line proxies (cached as ``proxies.npy``).

    Returns:
        The proxies ``(frames, H, W, 3)`` (memory-mapped), their pts ticks and the time base.
    """
    cache = out / "proxies.npy"
    meta = out / "proxies.json"
    if cache.exists() and meta.exists():
        record = json.loads(meta.read_text(encoding="utf-8"))
        ticks = np.array(record["pts_ticks"], dtype=np.int64)
        return np.load(cache, mmap_mode="r"), ticks, Fraction(record["time_base"])
    video = find_footage_file(CLIP, footage_root)
    roots = OutputRoots(allowed=out, footage=footage_root)
    start = EXCERPT_START_S - LEAD_S
    duration = LEAD_S + EXCERPT_DURATION_S + TAIL_S
    log(f"extracting {float(duration):g} s of {video.name} from {float(start):.4f} s")
    frames = excerpt(video, float(start), float(duration), out / "png", short_side=540, roots=roots)
    first = read_png16(frames[0].path)
    proxies = np.lib.format.open_memmap(
        cache, mode="w+", dtype=np.uint8, shape=(len(frames), *first.shape)
    )
    for index, frame in enumerate(frames):
        proxies[index] = quantise(read_png16(frame.path).astype(np.float64))
        frame.path.unlink()
    proxies.flush()
    meta.write_text(
        json.dumps(
            {
                "source": video.name,
                "start_s": str(start),
                "duration_s": str(duration),
                "pts_ticks": [frame.pts_ticks for frame in frames],
                "time_base": str(frames[0].time_base),
                "command": list(frames[0].command) if frames[0].command else None,
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    ticks = np.array([frame.pts_ticks for frame in frames], dtype=np.int64)
    return np.load(cache, mmap_mode="r"), ticks, frames[0].time_base


def staged_reach(
    ticks: NDArray[np.int64], time_base: Fraction, stages: int, lo: int, hi: int
) -> tuple[int, int]:
    """The input frames a staged analysis of ``stages`` stages reads for outputs ``lo..hi``."""
    for _ in range(stages):
        lo, hi = reach(ticks, time_base, WINDOW_S, "median_gaussian", lo, hi)
    return lo, hi


def image(proxies: NDArray[np.uint8], index: int) -> NDArray[np.float32]:
    """Frame ``index`` as the float32 image every statistic is measured on (stored / 255)."""
    stored = np.asarray(proxies[index], dtype=np.float32)
    return (stored / np.float32(255)).astype(np.float32)


def staged(
    proxies: NDArray[np.uint8],
    ticks: NDArray[np.int64],
    time_base: Fraction,
    method: str,
    kind: str,
    backend: Backend,
    log: Callable[[str], None],
) -> tuple[Series, Series]:
    """STAGED analysis (D97) with the product's smoother over pts.

    Returns:
        The smoothed series of every stage, and the raw series the stages measured.
    """
    params = make_params(method, neutral=False)
    smoothed: Series = {}
    raw: Series = {}
    for stage in temporal.STAGES[method]:
        log(f"  {method} {kind}: stage {stage.name}")
        records = [
            temporal.measure(
                image(proxies, index),
                params,
                temporal.at(smoothed, index) if smoothed else None,
                backend,
            )
            for index in range(len(ticks))
        ]
        series = {
            name: values
            for name, values in temporal.stack(records).items()
            if name.split(".", 1)[0] in stage.fields
        }
        raw.update(series)
        for name, values in series.items():
            smoothed[name] = smooth_series(ticks, time_base, values, WINDOW_S, kind)
    return smoothed, raw


def render_signals(
    proxies: NDArray[np.uint8],
    indices: Sequence[int],
    method: str,
    statistics: Callable[[int], Any],
    backend: Backend,
) -> NDArray[np.float64]:
    """Render ``indices`` with ``statistics(index)``; return their frame signals."""
    params = make_params(method, neutral=False)
    return np.array(
        [
            temporal.frame_signals(
                np.asarray(
                    backend.to_host(
                        temporal.render(image(proxies, i), params, statistics(i), backend)
                    )
                )
            )
            for i in indices
        ]
    )


def reference_statistics(
    proxies: NDArray[np.uint8], indices: Sequence[int], method: str, backend: Backend
) -> Any:
    """The flicker reference's constant record, as WP1.4b claim 10b computes it.

    The mean, over the excerpt's frames, of each frame's own raw (unsmoothed, unstaged)
    statistics (``temporal.statistics_of``), so the reference does not depend on the kind under
    test (``tools/noise_experiments.py``: ``constant_statistics(raw)``).
    """
    params = make_params(method, neutral=False)
    own_raw = [temporal.statistics_of(image(proxies, i), params, backend) for i in indices]
    return temporal.constant_statistics(temporal.stack(own_raw))


def _constant(record: Any) -> Callable[[int], Any]:
    """The same record for every frame."""

    def same(index: int) -> Any:
        return record

    return same


def _at(series: Series) -> Callable[[int], Any]:
    """Frame ``index`` of ``series`` as a record."""

    def record(index: int) -> Any:
        return temporal.at(series, index)

    return record


def evaluate(out: Path, device: str, log: Callable[[str], None]) -> dict[str, Any]:
    """Run the evaluation; return the record (also written to ``out/step-aware.json``)."""
    config = load_local_config()
    out.mkdir(parents=True, exist_ok=True)
    proxies, ticks, time_base = load_proxies(out, config.footage_path, log)
    rate = Fraction(1) / (Fraction(int(ticks[1] - ticks[0])) * time_base)
    end_s = EXCERPT_START_S + EXCERPT_DURATION_S
    inside = [i for i, tick in enumerate(ticks) if EXCERPT_START_S <= int(tick) * time_base < end_s]
    lo, hi = inside[0], inside[-1]
    indices = list(range(lo, hi + 1))
    backend = select_backend(device)
    source = np.array([temporal.frame_signals(image(proxies, i)) for i in indices])
    step, step_size = detect_step(source[:, 3], rate)
    step_pts_s = float(ticks[lo + step] * time_base)
    away = round(AWAY_S * float(rate))
    away_steps = [k for k in range(len(indices) - 1) if k + 1 < step - away or k >= step + away]
    record: dict[str, Any] = {
        "clip": CLIP,
        "window_s": WINDOW_S,
        "span_frames": len(ticks),
        "span_s": float((ticks[-1] - ticks[0]) * time_base),
        "excerpt_frames": len(indices),
        "step_index_in_excerpt": step,
        "step_pts_s": step_pts_s,
        "step_luma_change_8bit": step_size * 255.0,
        "away_from_step_steps": len(away_steps),
        "backend": backend.name,
        "methods": {},
    }
    for method in METHODS:
        stages = len(temporal.STAGES[method])
        lo_reach, hi_reach = staged_reach(ticks, time_base, stages, lo, hi)
        edge_free = 0
        for i in indices:
            first, last = staged_reach(ticks, time_base, stages, i, i)
            edge_free += int(first > 0 and last < len(ticks) - 1)
        per_kind: dict[str, Any] = {}
        series_by_kind: dict[str, Series] = {}
        for kind in KINDS:
            started = time.perf_counter()
            series_by_kind[kind], _ = staged(proxies, ticks, time_base, method, kind, backend, log)
            log(f"  {method} {kind}: analysed in {time.perf_counter() - started:.0f} s")
        constant = reference_statistics(proxies, indices, method, backend)
        reference = render_signals(proxies, indices, method, _constant(constant), backend)
        for kind in KINDS:
            series = series_by_kind[kind]
            signals = render_signals(proxies, indices, method, _at(series), backend)
            measured = temporal.flicker(signals, reference)
            away_value = float(measured.per_step[away_steps].mean())
            steps = signal_steps(signals, source, step, rate)
            per_kind[kind] = {
                "flicker_all": measured.value,
                "flicker_away_from_step": away_value,
                "flicker_peak_step_8bit": float(measured.per_step.max()),
                "rendered_step": steps,
            }
            log(
                f"  {method} {kind}: flicker away {away_value:.3f}, all {measured.value:.3f}, "
                f"luma step / source {steps['luma']['change_over_source']}"
            )
        record["methods"][method] = {
            "stages": stages,
            "reach_frames": [lo - lo_reach, hi_reach - hi],
            "edge_free_frames": edge_free,
            "kinds": per_kind,
        }
    (out / "step-aware.json").write_text(json.dumps(record, indent=1), encoding="utf-8")
    return record


def table(record: dict[str, Any]) -> str:
    """The report's table: one row per method and kind."""
    lines = [
        "| Method | Kind | Flicker away from step | Flicker all | Peak step | "
        "R / source | G / source | B / source | luma / source |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for method, data in record["methods"].items():
        for kind, figures in data["kinds"].items():
            ratios = [
                figures["rendered_step"][signal]["change_over_source"]
                for signal in ("R", "G", "B", "luma")
            ]
            cells = [f"{r:.2f}x" if r is not None else "-" for r in ratios]
            lines.append(
                f"| {method} | {kind} | {figures['flicker_away_from_step']:.3f} | "
                f"{figures['flicker_all']:.3f} | {figures['flicker_peak_step_8bit']:.2f} | "
                + " | ".join(cells)
                + " |"
            )
    return "\n".join(lines)


def main(argv: Sequence[str] | None = None) -> int:
    """Command line: ``uv run python tools/step_aware_eval.py [--out DIR] [--device auto]``."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, default=default_out())
    parser.add_argument("--device", default="auto", choices=("auto", "cpu", "gpu"))
    args = parser.parse_args(argv)

    def log(text: str) -> None:
        print(text, flush=True)

    record = evaluate(args.out, args.device, log)
    text = table(record)
    (args.out / "step-aware.md").write_text(text + "\n", encoding="utf-8")
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
