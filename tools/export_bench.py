"""WP3.14 V16 export row: the product export job end to end on full clips (questions 11, 12).

Each run builds :class:`clearwater.jobs.ExportEngine` over the product collaborators (WP3.9's
source, WP3.10's sink, WP3.11's analysis, WP3.4's methods, WP3.12's cache, WP3.1's backend
selector) and runs one job the way a batch item runs it, so the figure is D106's "end to end":
probe, the whole analysis (a COLD cache: a new, empty cache folder), the per-frame render and
the encode, mux and verification. A WARM run primes the cache first with the same analysis,
untimed, and times the export with a complete entry (as File > Export after analysis): the
engine then skips the decode pass and analyses the later stages from the cached proxies.

The engine reads no clock: the instrument times what the engine reports. The phase split comes
from the engine's ``on_stage`` hook (``probe``, ``analysis``, ``open``, ``frames``, ``close``,
``committed``) and the per-frame figures from the ``Progress`` callbacks (the interval between
two successive ``Exporting`` reports: decode, upload, render, download and write of one frame),
each stamped with the instrument's own clock.

Per run the record holds: the frames, the wall time, seconds per frame and minutes of
processing per minute of footage against D106's interim 25 min/min (0.834 s/frame at
30000/1001 fps), the per-frame median / p90 / max (the first frame apart), the phase times and
the analysis share, the strays over the whole run and the conditions (strays, graphics-card
clocks and temperature, CPU) before and after, the peak resident memory of the process tree
(FFmpeg children included) and the peak graphics memory in use (N4, both from WP3.10's
:class:`~video_io_bench.Telemetry`), and the NVENC proof (DR-18 (1)). Plan 4.3 / frame rule 7:
an EXCLUSIVE run, best effort on a shared laptop; the machine's other load is recorded, never
prevented, and a contaminated row is kept as spread.

The footage is reached only through ``local_config.find_footage_file`` and only read. Every
output, cache folder and record goes under the working folder (``wp3.14/bench``); an output and
its cache folder are deleted after the run unless ``--keep`` is given (an output carries the
source's telemetry track). The record (``export-bench-<name>-<UTC stamp>.json``) is rewritten
after every run, so a run that fails keeps the runs before it. The synthetic 5.3K 8:7 clip
(:data:`SYNTHETIC`, for V15's memory peaks) is generated under the same folder on first use.
Usage::

    uv run python tools/export_bench.py run GX011627 [--runs 3] [--cache cold|warm]
        [--method c3] [--encoder auto] [--quality standard] [OPTIONS]
    uv run python tools/export_bench.py v16 [--clip STEM ...] [--dry-run] [OPTIONS]

where OPTIONS, after the subcommand, are ``--config FILE``, ``--keep``, ``--force-cpu``,
``--memory-every S`` and ``--gpu-every S``.

``v16`` runs :data:`V16_PLAN` in order, or only the legs of the clips named by ``--clip`` (each
footage window covers one clip: GX011627 first, GX011625 last). Exit status 0 when every run
finished with an ok result; 1 when a run failed (the record says which and why); 2 on a usage,
configuration, footage-lookup or disk-space error before any run.
"""

from __future__ import annotations

import argparse
import itertools
import json
import os
import shutil
import subprocess
import sys
import time
from collections.abc import Callable, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import video_fidelity as vf
from clearwater.analysis import AnalysisEngine
from clearwater.cache import DiskProxyCache, cache_key
from clearwater.core import select_backend
from clearwater.interfaces import JobResult, ParameterSet, ProbeResult, Settings, SinkReport
from clearwater.io.photo import PhotoReader, PhotoWriter
from clearwater.io.video import FFmpegVideoSource, find_tool
from clearwater.jobs import ExportEngine, effective_parameters
from clearwater.jobs.export_seam import ExportRequest
from clearwater.methods import available_methods
from local_config import LocalConfigError, find_footage_file, load_local_config
from video_io_bench import StrayWatch, Telemetry, conditions, period, rate, summarise

SUBDIR = Path("wp3.14") / "bench"
"""Where the outputs, cache folders, the synthetic clip and the records go, under the working
folder."""

D106_MIN_PER_MIN = 25.0
"""D106's interim N6 figure: minutes of processing per minute of 4K footage, end to end."""

DISK_MARGIN_BYTES = 4 * 1024**3
"""Free space wanted beyond the source's own size before a run starts (the output is at most
about the source's size at High; the analysis cache adds a few hundred MB)."""

SYNTHETIC = "synthetic-5k3"
"""The clip name of the generated 5.3K 8:7 clip (V15's memory peaks; WP5.2 measures V15)."""

SYNTHETIC_SIZE = (5312, 4648)
"""Width and height of the HERO13 5.3K 8:7 mode."""

SYNTHETIC_SECONDS = 5
"""Length of the synthetic clip (150 frames at 30000/1001)."""

EXPORT_PREFIX = "Exporting "
"""The engine's per-frame progress message starts with this."""


class BenchError(RuntimeError):
    """A run cannot start: the disk is too full, or the clip cannot be made or found."""


@dataclass(frozen=True)
class Leg:
    """One row of the V16 plan.

    Attributes:
        clip: The footage stem, or :data:`SYNTHETIC`.
        runs: How many times the leg runs.
        cache: ``"cold"`` (analysis included) or ``"warm"`` (the analysis primed, untimed).
        method: The correction method id (AD-8 default ``c3``).
        encoder: The video encoder setting (G12 default ``auto``).
        quality: The D75 quality level.
    """

    clip: str
    runs: int
    cache: str = "cold"
    method: str = "c3"
    encoder: str = "auto"
    quality: str = "standard"


V16_PLAN: tuple[Leg, ...] = (
    Leg("GX011627", 3),
    Leg("GX011627", 1, cache="warm"),
    Leg("GX011627", 1, method="ancuti2018"),
    Leg("GX011627", 1, encoder="libx265"),
    Leg(SYNTHETIC, 1),
    Leg("GX011625", 1),
)
"""Ruling Q12 (CHARC FINAL ``3c3c35d7``), at the defaults (c3, encoder auto, Standard, 8-bit as
the source): GX011627 x 3 cold and x 1 warm, x 1 with ``ancuti2018``, x 1 with libx265; the
synthetic 5.3K 8:7 clip's memory peaks; GX011625 x 1 cold (the sustained row), LAST."""


# --- the synthetic clip ----------------------------------------------------------------------


def synthetic_clip(folder: Path) -> Path:
    """Return the synthetic 5.3K 8:7 clip under ``folder``, generating it on first use.

    Args:
        folder: The bench folder.

    Returns:
        An 8-bit HEVC MP4 with AAC sound, :data:`SYNTHETIC_SECONDS` long at 30000/1001 fps.

    Raises:
        BenchError: FFmpeg could not make it.
    """
    path = folder / f"{SYNTHETIC}-8x7.mp4"
    if path.is_file():
        return path
    width, height = SYNTHETIC_SIZE
    partial = path.with_name(f"{path.stem}.partial.mp4")
    command = [
        str(find_tool("ffmpeg")), "-nostdin", "-hide_banner", "-v", "error", "-y",
        "-f", "lavfi", "-i",
        f"testsrc2=size={width}x{height}:rate=30000/1001:duration={SYNTHETIC_SECONDS}",
        "-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={SYNTHETIC_SECONDS}",
        "-vf", "hue=h=t*30", "-c:v", "libx265", "-preset", "ultrafast",
        "-x265-params", "log-level=error", "-pix_fmt", "yuv420p",
        "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
        "-color_range", "tv", "-c:a", "aac", str(partial),
    ]  # fmt: skip
    done = subprocess.run(command, stdin=subprocess.DEVNULL, capture_output=True, check=False)
    if done.returncode != 0:
        partial.unlink(missing_ok=True)
        tail = done.stderr.decode("utf-8", errors="replace").strip()[-400:]
        raise BenchError(f"the synthetic clip could not be made: {tail}")
    partial.replace(path)
    return path


# --- one run ---------------------------------------------------------------------------------


class _Clocked:
    """The job's Progress and stage hook: every call stamped with the instrument's clock."""

    def __init__(self, clock: Callable[[], float]) -> None:
        self._clock = clock
        self.reports: list[tuple[float, int, int | None, str]] = []
        self.stages: list[tuple[str, float]] = []

    def report(self, done: int, total: int | None, message: str) -> None:
        """Record a progress report."""
        self.reports.append((self._clock(), done, total, message))

    def cancelled(self) -> bool:
        """Never cancel."""
        return False

    def stage(self, name: str) -> None:
        """Record a phase boundary (the engine's ``on_stage`` hook)."""
        self.stages.append((name, self._clock()))


class _BenchSink(vf._RecordingSink):
    """The product sink, recording its encode window, the resolved encoder and its report."""

    def __init__(self) -> None:
        super().__init__()
        self.encoder: str | None = None
        self.bit_depth: int | None = None
        self.report: SinkReport | None = None

    def open(self, probe: ProbeResult, out_path: Path, **options: Any) -> None:
        """Record the encoder and bit depth the engine chose, then open."""
        self.encoder = options.get("encoder")
        self.bit_depth = options.get("bit_depth")
        super().open(probe, out_path, **options)

    def close(self) -> SinkReport:
        """Close and keep the report."""
        self.report = super().close()
        return self.report


def build_engine(
    cache_folder: Path,
    sink_factory: Callable[[], Any],
    on_stage: Callable[[str], None] | None,
) -> ExportEngine:
    """Return the export engine over the product collaborators.

    Args:
        cache_folder: The analysis cache folder of this run.
        sink_factory: Returns the run's sink.
        on_stage: The phase hook.

    Returns:
        The engine.
    """
    return ExportEngine(
        methods=available_methods(),
        video_source=FFmpegVideoSource(),
        sink_factory=sink_factory,
        photo_reader=PhotoReader(),
        photo_writer=PhotoWriter(),
        cache=DiskProxyCache(cache_folder),
        cache_key=cache_key,
        select_backend=select_backend,
        on_stage=on_stage,
    )


def prime_cache(path: Path, cache_folder: Path, settings: Settings, method_id: str) -> float:
    """Run the clip's whole analysis into ``cache_folder`` as the job would (a warm run's setup).

    Args:
        path: The source clip.
        cache_folder: The run's cache folder.
        settings: The run's settings (the backend choice).
        method_id: The method id.

    Returns:
        The seconds the priming took (recorded, never part of the row).

    Raises:
        BenchError: The analysis failed.
    """
    began = time.perf_counter()
    source = FFmpegVideoSource()
    info = source.probe(path)
    method = available_methods()[method_id]
    backend, _ = select_backend(settings, info.video.height, info.video.width, method.id)
    engine = AnalysisEngine(
        method=method,
        backend=backend,
        cache=DiskProxyCache(cache_folder),
        key=cache_key(path),
        source=source,
        probe=info,
        params=effective_parameters(method, _parameters(method_id)),
        hw_decode=backend.device != "cpu",
    )
    result = engine.analysis_job()(_Clocked(time.perf_counter))
    if not result.ok:
        raise BenchError(f"priming the cache failed: {result.failure}")
    return time.perf_counter() - began


def _parameters(method_id: str) -> ParameterSet:
    """The method's defaults as a parameter set (AD-8: the defaults are the row's)."""
    return ParameterSet(
        method=method_id, parameters={}, created=datetime.now(UTC), app_version="export-bench"
    )


def phase_times(stages: Sequence[tuple[str, float]], start: float, end: float) -> dict[str, float]:
    """Return each phase's seconds: from its boundary to the next one (the last to ``end``).

    The time from ``start`` to the first boundary is ``"setup"`` (the job's settings checks).

    Args:
        stages: ``(name, time)`` of each boundary, in order.
        start: When the job was called.
        end: When it returned.

    Returns:
        Phase name -> seconds, in order.
    """
    times = {"setup": (stages[0][1] if stages else end) - start}
    bounds = [*stages, ("", end)]
    for (name, at), (_, following) in itertools.pairwise(bounds):
        times[name] = following - at
    return times


def frame_intervals(
    reports: Sequence[tuple[float, int, int | None, str]], frames_at: float | None
) -> list[float]:
    """Return the interval of each exported frame, from the ``frames`` boundary on.

    Args:
        reports: The stamped progress reports.
        frames_at: The time of the ``frames`` boundary (None when it was not reached).

    Returns:
        One interval per ``Exporting`` report, in order.
    """
    stamps = [t for t, _, _, message in reports if message.startswith(EXPORT_PREFIX)]
    if frames_at is None or not stamps:
        return []
    return [b - a for a, b in itertools.pairwise([frames_at, *stamps])]


def run_once(
    path: Path,
    run_dir: Path,
    leg: Leg,
    *,
    force_cpu: bool,
    keep: bool,
    periods: tuple[float, float] = (0.25, 1.0),
) -> dict[str, Any]:
    """Run one export job of ``path`` into ``run_dir`` and measure it.

    ``run_dir`` must not exist yet: it is made for the run and holds the output and the cache
    folder. It is deleted after the run unless the run finished and ``keep`` is given (a failed
    job has already removed its own partial output; the folder goes all the same).

    Args:
        path: The source clip (read only).
        run_dir: The run's new folder under the bench folder.
        leg: The leg.
        force_cpu: Force the CPU backend (``Settings.force_cpu``).
        keep: Keep the output and the cache folder.
        periods: The telemetry periods (memory, graphics card) in seconds.

    Returns:
        The run's record.

    Raises:
        BenchError: ``run_dir`` exists, or a warm run's priming failed.
    """
    try:
        run_dir.mkdir(parents=True)
    except FileExistsError as error:
        raise BenchError(f"{run_dir} exists; a run never reuses a folder") from error
    finished = False
    try:
        record = _measure(path, run_dir, leg, force_cpu, periods)
        finished = True
    finally:
        if not (finished and keep):
            shutil.rmtree(run_dir, ignore_errors=True)
    if keep:
        record["run_dir"] = str(run_dir)
    return record


def _gpu_sampler(leg: Leg) -> Any | None:
    """Return the NVENC-proof GPU sampler for an NVENC leg, None for a libx265 leg."""
    return vf._Sampler() if leg.encoder != "libx265" else None


def _measure(
    path: Path, run_dir: Path, leg: Leg, force_cpu: bool, periods: tuple[float, float]
) -> dict[str, Any]:
    """Run :func:`run_once`'s job and build its record."""
    out_dir, cache_dir = run_dir / "out", run_dir / "cache"
    out_dir.mkdir()
    settings = Settings(
        output_folder=out_dir,
        video_encoder=leg.encoder,
        quality_level=leg.quality,
        force_cpu=force_cpu,
    )
    record: dict[str, Any] = {"leg": asdict(leg), "clip": path.name, "force_cpu": force_cpu}
    if leg.cache == "warm":
        record["prime_s"] = prime_cache(path, cache_dir, settings, leg.method)
    entry = DiskProxyCache(cache_dir).lookup(cache_key(path))
    record["cache_complete_at_start"] = entry is not None and entry.complete
    record["before"] = conditions("before")
    clocked = _Clocked(time.perf_counter)
    sinks: list[_BenchSink] = []

    def sink() -> _BenchSink:
        sinks.append(_BenchSink())
        return sinks[-1]

    engine = build_engine(cache_dir, sink, clocked.stage)
    request = ExportRequest(path, "video", _parameters(leg.method), settings)
    telemetry = Telemetry(memory_every=periods[0], gpu_every=periods[1])
    sampler = _gpu_sampler(leg)
    watch = StrayWatch()
    if sampler is not None:
        sampler.start()
    telemetry.start()
    job = engine.job(request)
    started = time.perf_counter()
    try:
        result: JobResult = job(clocked)
    finally:
        ended = time.perf_counter()
        strays = watch.window()  # a quick snapshot: the stray window ends with the export
        record["telemetry"] = telemetry.stop()  # next: its join may take seconds
        if telemetry.origin is not None:
            record["telemetry_origin_s"] = telemetry.origin - started
        samples = sampler.stop() if sampler is not None else None
    try:
        info: ProbeResult | None = FFmpegVideoSource().probe(path)
    except Exception:  # the job has already reported why the clip is unusable
        info = None
    bench_sink = sinks[-1] if sinks else None
    intervals = frame_intervals(clocked.reports, dict(clocked.stages).get("frames"))
    frames = len(intervals)
    phases = phase_times(clocked.stages, started, ended)
    total = ended - started
    figures = rate(total, frames, info.video.frame_rate) if frames and info else None
    record.update(
        {
            "ok": result.ok,
            "failure": result.failure,
            "warnings": list(result.warnings),
            "device": result.device,
            "encoder": bench_sink.encoder if bench_sink is not None else None,
            "bit_depth": bench_sink.bit_depth if bench_sink is not None else None,
            "size": None if info is None else [info.video.height, info.video.width],
            "frame_rate": None if info is None else str(info.video.frame_rate),
            "source_frames": None if info is None else info.video.nb_frames,
            "frames": frames,
            "wall_s": total,
            "total": figures,
            "d106_min_per_min": D106_MIN_PER_MIN,
            "meets_d106": None if figures is None else figures["min_per_min"] <= D106_MIN_PER_MIN,
            "phases_s": phases,
            "analysis_share": phases.get("analysis", 0.0) / total if total > 0 else None,
            "stages": [[name, round(at - started, 4)] for name, at in clocked.stages],
            "first_frame_s": intervals[0] if intervals else None,
            "per_frame": summarise(intervals[1:]),
            "per_frame_s": [round(value, 5) for value in intervals],
            "analysis_reports": sum(
                1 for _, _, _, message in clocked.reports if message.startswith("Analysing ")
            ),
            "strays": strays,
            "output_bytes": result.outputs[0].stat().st_size if result.outputs else None,
            "source_bytes": path.stat().st_size,
        }
    )
    report = bench_sink.report if bench_sink is not None else None
    if bench_sink is not None and report is not None and bench_sink.encoder is not None:
        run = vf.EncodeRun(
            report,
            bench_sink.encoder,
            bench_sink.bit_depth or 8,
            bench_sink.pid,
            bench_sink.started,
            bench_sink.ended,
            samples,
        )
        record["nvenc_proof"] = vf.nvenc_proof(run)
        record["sink_report"] = {
            "frames_written": report.frames_written,
            "warnings": list(report.warnings),
            "not_carried": list(report.not_carried),
        }
    else:
        record["nvenc_proof"] = {"tied": False, "reason": "the encode did not finish"}
    record["after"] = conditions("after")
    return record


# --- the command line ------------------------------------------------------------------------


def row_line(record: dict[str, Any]) -> str:
    """Return the one-line summary of a run's record."""
    leg = record["leg"]
    head = f"ROW {record['clip']} {leg['method']} {record['encoder']} {leg['cache']}"
    if not record["ok"]:
        return f"{head}: FAILED {record['failure']}"
    total, per_frame = record["total"], record["per_frame"] or {}
    peak = record["telemetry"]["peak_tree_rss_bytes"] / 1024**2
    gpu = record["telemetry"]["peak_gpu_memory_used_mib"]
    verdict = "meets" if record["meets_d106"] else "misses"
    return (
        f"{head}: {record['frames']} frames, {total['s_per_frame']:.4f} s/frame, "
        f"{total['min_per_min']:.2f} min/min ({verdict} D106 {D106_MIN_PER_MIN:g}); per frame "
        f"median {per_frame.get('median', 0):.4f}, p90 {per_frame.get('p90', 0):.4f}, "
        f"max {per_frame.get('max', 0):.4f}; analysis {100 * record['analysis_share']:.1f} %; "
        f"peak tree RSS {peak:.0f} MiB; peak GPU memory {gpu} MiB; "
        f"tied {record['nvenc_proof'].get('tied')}"
    )


def check_disk(source: Path, out_dir: Path) -> None:
    """Refuse a run when the bench folder has less free space than the source plus a margin.

    Raises:
        BenchError: Not enough free space.
    """
    free = shutil.disk_usage(out_dir).free
    wanted = source.stat().st_size + DISK_MARGIN_BYTES
    if free < wanted:
        raise BenchError(
            f"{free / 1024**3:.1f} GiB free under {out_dir}, {wanted / 1024**3:.1f} GiB wanted"
        )


def _write(path: Path, record: dict[str, Any]) -> None:
    path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")


def _describe(leg: Leg) -> str:
    return f"{leg.clip} x{leg.runs} {leg.method} {leg.encoder} {leg.quality} {leg.cache}"


def bench_folder(working: Path, subdir: Path) -> Path:
    """Return the records' folder: ``subdir`` under the working folder, never outside it.

    Args:
        working: The working folder (local configuration).
        subdir: A relative folder (WP3.21 writes ``wp3.21/bench``; the default is WP3.14's).

    Returns:
        The folder.

    Raises:
        ValueError: ``subdir`` is absolute or leads out of the working folder.
    """
    folder = (working / subdir).resolve()
    if subdir.is_absolute() or not folder.is_relative_to(working.resolve()):
        raise ValueError(f"--subdir {subdir} is not a folder under the working folder {working}")
    return folder


def main(argv: Sequence[str] | None = None) -> int:
    """Run the V16 row (or one leg) and write its record under the working folder.

    Args:
        argv: The command-line arguments (``sys.argv[1:]`` when None).

    Returns:
        The exit status.
    """
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument("--config", type=Path, help="local configuration file to read")
    options.add_argument("--keep", action="store_true", help="keep the outputs and caches")
    options.add_argument("--force-cpu", action="store_true", help="force the CPU backend")
    options.add_argument("--memory-every", type=period, default=0.25, help="seconds")
    options.add_argument("--gpu-every", type=period, default=1.0, help="seconds")
    options.add_argument(
        "--subdir",
        type=Path,
        default=SUBDIR,
        help=f"records and outputs under this folder of the working folder (default {SUBDIR})",
    )
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("run", help="one leg", parents=[options])
    one.add_argument("clip", help=f"footage stem, for example GX011627, or {SYNTHETIC}")
    one.add_argument("--runs", type=int, default=1)
    one.add_argument("--cache", default="cold", choices=("cold", "warm"))
    one.add_argument("--method", default="c3", choices=tuple(available_methods()))
    one.add_argument("--encoder", default="auto", choices=("auto", "hevc_nvenc", "libx265"))
    one.add_argument("--quality", default="standard", choices=("high", "standard", "draft"))
    v16 = commands.add_parser("v16", help="the ruled row set (V16_PLAN)", parents=[options])
    v16.add_argument("--clip", action="append", help="run only this clip's legs (repeatable)")
    v16.add_argument("--dry-run", action="store_true", help="list the runs and stop")
    args = parser.parse_args(argv)
    if args.command == "run":
        if args.runs < 1:
            parser.error("--runs must be at least 1")
        legs: tuple[Leg, ...] = (
            Leg(args.clip, args.runs, args.cache, args.method, args.encoder, args.quality),
        )
        name = args.clip
    else:
        chosen = {c.casefold() for c in args.clip or ()}
        legs = tuple(leg for leg in V16_PLAN if not chosen or leg.clip.casefold() in chosen)
        if not legs:
            parser.error(f"no V16 leg for {', '.join(args.clip)}")
        name = "v16" if not chosen else "v16-" + "-".join(sorted(chosen))
    dry_run = getattr(args, "dry_run", False)
    try:
        config = load_local_config(args.config)
        out_dir = bench_folder(config.working_path, args.subdir)
        footage = {
            leg.clip: find_footage_file(leg.clip, config.footage_path)
            for leg in legs
            if leg.clip != SYNTHETIC
        }
        if not dry_run:
            out_dir.mkdir(parents=True, exist_ok=True)
            for clip in footage.values():
                check_disk(clip, out_dir)
    except (LocalConfigError, ValueError, OSError, BenchError) as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    if dry_run:
        for leg in legs:
            print(f"PLAN {_describe(leg)}")
        return 0
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    record_path = out_dir / f"export-bench-{name}-{stamp}.json"
    record: dict[str, Any] = {"plan": [asdict(leg) for leg in legs], "pid": os.getpid(), "runs": []}
    for leg in legs:
        for number in range(1, leg.runs + 1):
            print(f"RUN {_describe(leg)} ({number}/{leg.runs})", flush=True)
            try:
                path = footage.get(leg.clip) or synthetic_clip(out_dir)
                check_disk(path, out_dir)  # again: kept outputs add up
                run = run_once(
                    path,
                    out_dir / f"run-{stamp}-{len(record['runs'])}",
                    leg,
                    force_cpu=args.force_cpu,
                    keep=args.keep,
                    periods=(args.memory_every, args.gpu_every),
                )
            except Exception as error:
                record["failed"] = {"leg": asdict(leg), "error": f"{type(error).__name__}: {error}"}
                _write(record_path, record)
                print(f"FAILED {type(error).__name__}: {error}", file=sys.stderr)
                print(f"RECORD {record_path}")
                return 1
            record["runs"].append(run)
            _write(record_path, record)
            print(row_line(run), flush=True)
            if not run["ok"]:
                record["failed"] = {"leg": asdict(leg), "error": run["failure"]}
                _write(record_path, record)
                print(f"RECORD {record_path}")
                return 1
    print(f"RECORD {record_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
