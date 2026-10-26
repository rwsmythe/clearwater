"""WP3.10 export floor row: WP3.9's decode straight into the product sink, no correction (Q11).

Every frame of a clip goes from :meth:`clearwater.io.video.FFmpegVideoSource.frames` into
:class:`clearwater.io.video.FFmpegVideoSink` with nothing in between, so the row is the floor
of an export: probe, decode, transport, encode, mux and the sink's own verification at
``close``, without the correction (the V16 / D106 export row is WP3.14's, ruling Q11).

Per run the record holds the time of each stage (probe, ``open``, the frame stream, ``close``),
the seconds per frame and minutes of processing per minute of footage (``min/min``: elapsed
seconds over ``frames / frame_rate``), and per frame the interval between the ends of two
successive writes, the wait for the decoder and the ``write`` call (each list kept whole, and
summarised). An interval is its wait plus its write plus the loop's own bookkeeping (a few
microseconds). The first frame's interval also holds the decoder's start (its FFmpeg starts at
the first frame asked for) and the encoder's first frame; the encoder's FFmpeg starts inside
``open`` and is timed there. The first interval is kept apart from the summaries.

Plan 4.3 / frame rule 7: an EXCLUSIVE run, best effort on a shared laptop. Two telemetry
threads (:class:`Telemetry`) record, each on its own schedule and without stopping the frame
loop, every sample with its time and the actual gaps beside the nominal periods:

- the resident memory of the process tree (this Python process and its FFmpeg children; the
  ``nvidia-smi`` processes the instrument itself starts are listed apart and not counted),
  every ``--memory-every`` seconds, with the peak and its members (N4);
- the graphics card (clocks, temperature, utilisation, device-wide memory in use, power and
  the active clock-event reasons) every ``--gpu-every`` seconds, with the memory peak.

The strays (:class:`StrayWatch`: the processes that used more than a quarter of one logical CPU,
each marked as the run's own or a stray) are read in the frame loop itself: primed before the
run, read after every ``--strays-every`` frames and once more after ``close``. A strays window
so covers the frames between two readings (the last one, the rest of the stream and
``close``). A reading takes seconds (every process's counter is read), so the loop pauses for
it: the pause is recorded and kept out of every frame figure and stage time. During a pause
the decoder runs ahead, by at most what its pipe holds, so the frame right after each pause is
recorded apart from the summaries, as the first frame is.

Conditions (the strays over one second, then the same graphics-card reading, the CPU load over
half a second and the CPU frequency) are recorded before and after each run. An NVENC run is
also tied to the encode window, the GPU UUID and the FFmpeg PID by
``tools/video_fidelity.py``'s ``nvidia-smi pmon`` sampler (DR-18 (1)). The machine's other
load is recorded, never prevented: a contaminated row is kept as spread.

The footage is reached only through ``local_config.find_footage_file`` and only read. Each
output is written under the working folder (``wp3.10/bench``), to a new file that must not
exist yet, and deleted after it is measured unless ``--keep`` is given (it carries the source's
telemetry track). The record (``io-bench-<name>-<UTC stamp>.json`` there) is rewritten after
every run, so a run that fails keeps the runs before it. Usage::

    uv run python tools/video_io_bench.py run GX011627 [--runs 3] [--encoder hevc_nvenc]
        [--quality standard] [--bit-depth N] [OPTIONS]
    uv run python tools/video_io_bench.py floor [--dry-run] [OPTIONS]

where OPTIONS, after the subcommand, are ``--config FILE``, ``--keep``, ``--software-decode``,
``--memory-every S``, ``--gpu-every S`` and ``--strays-every N`` (frames).

``floor`` runs :data:`FLOOR_PLAN`, ruling Q11's row set, in order. The free space is checked
for every leg before the first run and again before each run. Exit status 0 when every run
finished; 1 when a run failed or the disk filled up between runs (the record says which and
why); 2 on a usage, configuration, footage-lookup or disk-space error before any run.
"""

from __future__ import annotations

import argparse
import contextlib
import itertools
import json
import math
import os
import shutil
import statistics
import subprocess
import sys
import threading
import time
from collections.abc import Callable, Collection, Iterator, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from fractions import Fraction
from pathlib import Path
from typing import Any

import psutil

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent))

import video_fidelity as vf
from clearwater.interfaces.image import Frame
from clearwater.io.video import FFmpegVideoSource, find_tool
from clearwater.io.video.decode import cuda_decode_available, decode_command
from local_config import LocalConfigError, find_footage_file, load_local_config

SUBDIR = Path("wp3.10") / "bench"
"""Where the outputs and records go, under the working folder."""

DISK_MARGIN_BYTES = 2 * 1024**3
"""Free space wanted beyond the source's own size before a run starts (the High level aims
at the camera's bit rate, so an output is about the source's size at most)."""

STRAY_CPU_PERCENT = 25.0
"""A process above this share of one logical CPU over a window is listed."""

STRAYS_EVERY_FRAMES = 300
"""The strays are read after every this many frames by default."""

_GPU_QUERY = (
    "clocks.sm,clocks.mem,clocks.video,temperature.gpu,utilization.gpu,utilization.encoder,"
    "utilization.decoder,memory.used,power.draw,clocks_event_reasons.active"
)
_SAMPLER_NAMES = frozenset({"nvidia-smi", "nvidia-smi.exe"})
_SAMPLER_JOIN_S = 30.0
"""How long a stop waits for the samplers (above ``nvidia-smi``'s own 20 s timeout)."""


class BenchError(RuntimeError):
    """A run cannot start: the output exists, the disk is too full, or the clip is unusable."""


@dataclass(frozen=True)
class Leg:
    """One row of the floor plan.

    Attributes:
        clip: The footage stem.
        encoder: ``"hevc_nvenc"`` or ``"libx265"``.
        bit_depth: The output bit depth (8, or 10 per D76); the source's when None.
        runs: How many times the leg runs.
        quality: The D75 quality level.
    """

    clip: str
    encoder: str
    bit_depth: int | None
    runs: int
    quality: str = "standard"


FLOOR_PLAN: tuple[Leg, ...] = (
    Leg("GX011627", "hevc_nvenc", 8, 3),
    Leg("GX011625", "hevc_nvenc", 8, 1),
    Leg("GX011627", "libx265", 8, 1),
    Leg("GX011627", "hevc_nvenc", 10, 1),
)
"""Ruling Q11: GX011627 full clip x 3 and GX011625 full clip x 1 with NVENC 8-bit Standard;
one GX011627 run each with libx265 and NVENC 10-bit (D76)."""


# --- conditions ----------------------------------------------------------------------------


def gpu_reading() -> dict[str, str]:
    """Return one ``nvidia-smi`` reading of the fields in ``_GPU_QUERY``.

    When ``nvidia-smi`` cannot run, exits non-zero or prints nothing, the reading is
    ``{"unavailable": <why>}``, so the record says that the telemetry is missing.
    """
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--query-gpu={_GPU_QUERY}", "--format=csv,noheader,nounits"],
            stdin=subprocess.DEVNULL,
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return {"unavailable": f"nvidia-smi did not run: {type(exc).__name__}"}
    lines = result.stdout.strip().splitlines()
    if result.returncode != 0 or not lines:
        why = (result.stderr.strip() or result.stdout.strip() or "no output")[-200:]
        return {"unavailable": f"nvidia-smi exit {result.returncode}: {why}"}
    values = [value.strip() for value in lines[0].split(",")]
    return dict(zip(_GPU_QUERY.split(","), values, strict=False))


def memory_used_mib(reading: dict[str, str]) -> float | None:
    """Return the device-wide graphics memory in use of a reading, or None when not given."""
    try:
        return float(reading["memory.used"])
    except (KeyError, ValueError):
        return None


def own_tree(root: int | None = None, *, samplers: bool = False) -> list[psutil.Process]:
    """Return a process and its descendants.

    Args:
        root: The process id; this process when None.
        samplers: Include the ``nvidia-smi`` processes the instrument starts.
    """
    top = psutil.Process(root)
    try:
        children = top.children(recursive=True)
    except psutil.Error:
        children = []
    return [top, *(c for c in children if samplers or _name(c) not in _SAMPLER_NAMES)]


def _name(process: psutil.Process) -> str:
    try:
        return str(process.name()).lower()
    except psutil.Error:
        return "?"


def tree_rss(exclude: Collection[int] = ()) -> tuple[int, list[dict[str, Any]]]:
    """Return the resident bytes of this process tree and its members (name, pid, bytes).

    The ``nvidia-smi`` samplers and the processes in ``exclude`` are the instrument's, not the
    export's, and are left out; so is a member that exits between the listing and the reading.

    Args:
        exclude: Process ids to leave out.
    """
    members = []
    for process in own_tree():
        if process.pid in exclude:
            continue
        try:
            rss = int(process.memory_info().rss)
        except psutil.Error:
            continue
        members.append({"name": _name(process), "pid": process.pid, "rss": rss})
    return sum(member["rss"] for member in members), members


class StrayWatch:
    """Lists the processes above :data:`STRAY_CPU_PERCENT` of one logical CPU per window.

    Each :meth:`window` reports the CPU each process used since the previous call (or since
    the watch was created), so a sustained load shows and a one-second spike is averaged out. A
    process that appeared since the previous walk of the process list is charged the CPU it has
    used since it was created, over the time it has been alive, and marked ``new``; so a stray
    that starts inside a window is seen in that window. A process that exits before the window
    ends cannot be read and is not reported for that window (nor at all when it starts and
    exits inside one window).
    Reading every process's counter takes seconds of CPU on Windows and holds the interpreter
    lock in long stretches (measured: a 0.26 s probe took 23 s beside a watch in a thread), so
    during a run it is read between frames, with the loop paused (see the module docstring).
    """

    def __init__(self, root: int | None = None) -> None:
        """Prime every process's CPU counter.

        Args:
            root: The process whose tree is the run's own; this process when None.
        """
        self._root = os.getpid() if root is None else root
        self._processes: dict[int, psutil.Process] = {}
        self._walked_at = time.time()
        self._walk(charge=False)
        self._started = time.monotonic()

    def _walk(self, *, charge: bool) -> list[dict[str, Any]]:
        """Prime every process not yet known; charge the new ones when ``charge``.

        A process created at or after the start of the previous walk is new: it cannot have
        been primed. Its CPU since creation over its lifetime is returned when it reaches
        :data:`STRAY_CPU_PERCENT`.
        """
        previous, self._walked_at = self._walked_at, time.time()
        busy = []
        for process in psutil.process_iter(["name"]):
            if process.pid in self._processes:
                continue
            with contextlib.suppress(psutil.Error):
                if charge and process.create_time() >= previous:
                    alive = max(time.time() - process.create_time(), 1e-3)
                    times = process.cpu_times()
                    percent = 100.0 * (times.user + times.system) / alive
                    if percent >= STRAY_CPU_PERCENT and process.pid != 0:
                        busy.append(
                            {
                                "name": process.info.get("name"),
                                "pid": process.pid,
                                "cpu": round(percent, 1),
                                "new": True,
                                "alive_s": round(alive, 2),
                            }
                        )
                process.cpu_percent(None)
                self._processes[process.pid] = process
        return busy

    def window(self) -> dict[str, Any]:
        """Return the busy processes since the previous window and start the next one.

        Returns:
            The window's length in seconds and its busy processes (name, pid, percent of one
            logical CPU, ``own`` True for the root process and its descendants: FFmpeg and the
            instrument's ``nvidia-smi``; a new process also carries ``new`` and ``alive_s``),
            busiest first.
        """
        now = time.monotonic()
        busy = []
        for pid, process in list(self._processes.items()):
            try:
                percent = process.cpu_percent(None)
            except psutil.Error:
                del self._processes[pid]
                continue
            if percent >= STRAY_CPU_PERCENT and pid != 0:
                busy.append({"name": process.info.get("name"), "pid": pid, "cpu": percent})
        busy += self._walk(charge=True)
        try:
            own = {process.pid for process in own_tree(self._root, samplers=True)}
        except psutil.Error:
            own = set()
        for entry in busy:
            entry["own"] = entry["pid"] in own
        seconds = now - self._started
        self._started = now
        return {"seconds": round(seconds, 2), "busy": sorted(busy, key=lambda b: -b["cpu"])}


def conditions(moment: str) -> dict[str, Any]:
    """Record the machine's conditions at ``moment``: strays over 1 s, graphics card, CPU.

    The strays window is read right after its one second, before the slower readings.

    Args:
        moment: A label such as ``"before"``.

    Returns:
        The record.
    """
    watch = StrayWatch()
    time.sleep(1.0)
    strays = watch.window()
    frequency = psutil.cpu_freq()
    return {
        "moment": moment,
        "utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "gpu": gpu_reading(),
        "cpu_total_percent": psutil.cpu_percent(interval=0.5),
        "cpu_mhz": round(frequency.current) if frequency is not None else None,
        "strays": strays,
    }


class Telemetry:
    """Samples the process tree's memory and the graphics card, each in a thread of its own.

    Each thread keeps its own schedule: a sample is due every period from the start, and one
    that takes longer than its period is followed at once by the next (no burst to catch up),
    so a slow ``nvidia-smi`` never delays the memory readings. Every sample carries its time,
    and the record holds the gaps between samples beside the nominal periods.
    """

    def __init__(self, *, memory_every: float, gpu_every: float) -> None:
        """Set the sampling periods in seconds.

        Args:
            memory_every: Between two readings of the process tree's resident memory.
            gpu_every: Between two graphics-card readings.

        Raises:
            ValueError: A period is not a finite number above zero.
        """
        if not all(math.isfinite(p) and p > 0 for p in (memory_every, gpu_every)):
            raise ValueError("every telemetry period must be a positive number of seconds")
        self._periods = (memory_every, gpu_every)
        self._stop = threading.Event()
        self._threads = {
            "memory": threading.Thread(
                target=self._loop, args=("memory", memory_every, self._sample_rss), daemon=True
            ),
            "gpu": threading.Thread(
                target=self._loop, args=("gpu", gpu_every, self._sample_gpu), daemon=True
            ),
        }
        self._started = 0.0
        self.peak_rss = 0
        self.peak_members: list[dict[str, Any]] = []
        self.peak_at_s = 0.0
        self.rss: list[tuple[float, int]] = []
        self.gpu: list[dict[str, Any]] = []
        self.errors: list[str] = []

    def start(self) -> None:
        """Start both samplers."""
        self._started = time.monotonic()
        for thread in self._threads.values():
            thread.start()

    def _elapsed(self) -> float:
        return time.monotonic() - self._started

    def _loop(self, name: str, every: float, sample: Callable[[float], None]) -> None:
        due = 0.0
        try:
            while True:
                sample(round(self._elapsed(), 3))
                due = max(due + every, self._elapsed())
                if self._stop.wait(max(due - self._elapsed(), 0.0)):
                    break
        except Exception as exc:  # telemetry never ends the run; the record says it stopped
            self.errors.append(
                f"the {name} sampler stopped at {self._elapsed():.2f} s: "
                f"{type(exc).__name__}: {exc}"
            )

    def _sample_rss(self, elapsed: float) -> None:
        total, members = tree_rss()
        self.rss.append((elapsed, total))
        if total > self.peak_rss:
            self.peak_rss, self.peak_members, self.peak_at_s = total, members, elapsed

    def _sample_gpu(self, elapsed: float) -> None:
        self.gpu.append({"t_s": elapsed, **gpu_reading()})

    def stop(self) -> dict[str, Any]:
        """Stop both samplers and return what was recorded.

        A sampler that had ended before the stop, or that does not stop within
        :data:`_SAMPLER_JOIN_S`, is recorded in the errors (it is not waited for longer).

        Returns:
            The nominal periods and the actual gaps between samples (summarised), the memory
            samples (seconds, bytes) and peak (bytes, its members, when), the graphics-card
            readings and their memory peak, and the errors, if any.
        """
        for name, thread in self._threads.items():
            if thread.ident is not None and not thread.is_alive():
                self.errors.append(f"the {name} sampler had ended before the stop")
        self._stop.set()
        deadline = time.monotonic() + _SAMPLER_JOIN_S
        for name, thread in self._threads.items():
            if thread.ident is None:
                continue
            thread.join(timeout=max(deadline - time.monotonic(), 0.0))
            if thread.is_alive():
                self.errors.append(f"the {name} sampler did not stop within {_SAMPLER_JOIN_S:g} s")
        rss, gpu = list(self.rss), list(self.gpu)  # a sampler that did not stop may still add
        used = [m for m in (memory_used_mib(r) for r in gpu) if m is not None]
        return {
            "periods_s": dict(zip(("memory", "gpu"), self._periods, strict=True)),
            "gaps_s": {
                "memory": _gaps([t for t, _ in rss]),
                "gpu": _gaps([float(r["t_s"]) for r in gpu]),
            },
            "peak_tree_rss_bytes": self.peak_rss,
            "peak_tree_rss_members": self.peak_members,
            "peak_tree_rss_at_s": round(self.peak_at_s, 2),
            "rss_samples": len(rss),
            "rss": rss,
            "peak_gpu_memory_used_mib": max(used) if used else None,
            "gpu": gpu,
            "errors": list(self.errors),
        }


def _gaps(times: Sequence[float]) -> dict[str, float] | None:
    """Summarise the gaps between successive sample times (None under two samples)."""
    return summarise([b - a for a, b in itertools.pairwise(times)])


# --- one run -------------------------------------------------------------------------------


def summarise(samples: Sequence[float]) -> dict[str, float] | None:
    """Return the count, median, 10th and 90th percentile, minimum, maximum and mean.

    Args:
        samples: Timings in seconds.

    Returns:
        The summary, or None for no samples.
    """
    if not samples:
        return None
    ordered = sorted(samples)

    def at(fraction: float) -> float:
        return ordered[min(len(ordered) - 1, math.floor(fraction * (len(ordered) - 1) + 0.5))]

    return {
        "n": len(ordered),
        "median": statistics.median(ordered),
        "p10": at(0.1),
        "p90": at(0.9),
        "min": ordered[0],
        "max": ordered[-1],
        "mean": statistics.fmean(ordered),
    }


def rate(seconds: float, frames: int, frame_rate: Fraction) -> dict[str, float]:
    """Return seconds per frame and minutes of processing per minute of footage.

    Args:
        seconds: The elapsed time.
        frames: The frames processed, at least one.
        frame_rate: The clip's frame rate (frames per second of footage).

    Returns:
        ``s_per_frame`` and ``min_per_min`` (``seconds / (frames / frame_rate)``).
    """
    footage_s = frames / frame_rate
    return {"s_per_frame": seconds / frames, "min_per_min": seconds / float(footage_s)}


class _BenchSink(vf._RecordingSink):
    """The fidelity instrument's recording sink, keeping the FFmpeg command as well."""

    def __init__(self) -> None:
        super().__init__()
        self.command: list[str] = []

    def _start(self, command: list[str]) -> None:
        self.command = list(command)
        super()._start(command)


def video_bit_rate(path: Path) -> int | None:
    """Return the video stream's bit rate as ffprobe states it, or None.

    Only the first video stream's ``bit_rate`` field is read.
    """
    command = [
        str(find_tool("ffprobe")), "-v", "error", "-select_streams", "v:0",
        "-show_entries", "stream=bit_rate", "-of", "json", f"file:{path.absolute()}",
    ]  # fmt: skip
    result = subprocess.run(
        command, stdin=subprocess.DEVNULL, capture_output=True, text=True, check=False, timeout=120
    )
    if result.returncode != 0:
        return None
    try:
        return int(json.loads(result.stdout)["streams"][0]["bit_rate"])
    except (KeyError, IndexError, TypeError, ValueError):
        return None


def check_disk(source: Path, out_dir: Path) -> None:
    """Refuse a run when the output folder has less free space than the source plus a margin.

    Raises:
        BenchError: Not enough free space.
    """
    free = shutil.disk_usage(out_dir).free
    wanted = source.stat().st_size + DISK_MARGIN_BYTES
    if free < wanted:
        raise BenchError(
            f"{free / 1024**3:.1f} GiB free under {out_dir}, {wanted / 1024**3:.1f} GiB wanted"
        )


def run_once(
    path: Path,
    output: Path,
    *,
    encoder: str,
    quality: str,
    bit_depth: int | None,
    hw_decode: bool,
    keep: bool,
    periods: tuple[float, float] = (0.25, 1.0),
    strays_every: int = STRAYS_EVERY_FRAMES,
) -> dict[str, Any]:
    """Decode ``path`` with WP3.9's source and write every frame through the product sink.

    The output is created new first (it must not exist, as the caller's ``SafeWrite``
    temporary is new), measured, and deleted unless ``keep``. On any failure the sink's
    ``abort`` stops the encoder, the decode is closed and the output is deleted (``keep`` or
    not) before the error propagates.

    Args:
        path: The source clip (read only).
        output: The output file, which must not exist yet.
        encoder: ``"hevc_nvenc"`` or ``"libx265"``.
        quality: The D75 quality level.
        bit_depth: The output bit depth; the source's when None.
        hw_decode: Ask WP3.9's source for a CUDA decode (software when unavailable).
        keep: Keep the output instead of deleting it.
        periods: The telemetry periods (memory, graphics card) in seconds.
        strays_every: Read the strays after every this many frames.

    Returns:
        The run's record.

    Raises:
        BenchError: The output exists already (it is left as it was).
        ValueError: ``strays_every`` is below one.
    """
    if strays_every < 1:
        raise ValueError("strays_every must be a positive number of frames")
    output.parent.mkdir(parents=True, exist_ok=True)
    try:
        with output.open("xb"):
            pass
    except FileExistsError as error:
        raise BenchError(f"{output} exists; a run never overwrites a file") from error
    finished = False
    try:
        record = _measure(
            path, output, encoder, quality, bit_depth, hw_decode, periods, strays_every
        )
        finished = True
    finally:
        if not (finished and keep):
            output.unlink(missing_ok=True)
    if keep:
        record["output"] = str(output)
    return record


def _measure(
    path: Path,
    output: Path,
    encoder: str,
    quality: str,
    bit_depth: int | None,
    hw_decode: bool,
    periods: tuple[float, float],
    strays_every: int,
) -> dict[str, Any]:
    """Run :func:`run_once`'s decode-encode loop into the existing, empty ``output``."""
    record: dict[str, Any] = {"before": conditions("before")}
    telemetry = Telemetry(memory_every=periods[0], gpu_every=periods[1])
    source = FFmpegVideoSource()
    sink = _BenchSink()
    sampler = vf._Sampler() if encoder == "hevc_nvenc" else None
    intervals: list[float] = []
    waits: list[float] = []
    writes: list[float] = []
    pauses: list[float] = []
    after_pause: list[int] = []
    windows: list[dict[str, Any]] = []
    stream: Iterator[Frame] | None = None
    began = time.perf_counter()
    watch = StrayWatch()
    strays: dict[str, Any] = {"every_frames": strays_every, "prime_s": time.perf_counter() - began}
    started = time.perf_counter()  # set again below; here for the last reading on a failure
    try:
        telemetry.start()
        if sampler is not None:
            sampler.start()
        started = time.perf_counter()
        info = source.probe(path)
        probed = time.perf_counter()
        depth = bit_depth if bit_depth is not None else info.video.bit_depth
        sink.open(info, output, encoder=encoder, quality=quality, bit_depth=depth, provenance=None)
        opened = previous = time.perf_counter()
        stream = source.frames(info, hw_decode=hw_decode)
        while True:
            before = time.perf_counter()
            frame = next(stream, None)
            if frame is None:
                break
            decoded = time.perf_counter()
            sink.write(frame)
            del frame  # one frame held at a time: released before the next is decoded
            written = time.perf_counter()
            waits.append(decoded - before)
            writes.append(written - decoded)
            intervals.append(written - previous)
            previous = written
            if len(intervals) % strays_every == 0:
                windows.append(_strays_window(watch, len(intervals), written - started))
                previous = time.perf_counter()
                pauses.append(previous - written)
                after_pause.append(len(intervals))  # the index of the next frame
        streamed = time.perf_counter()
        report = sink.close()
        closed = time.perf_counter()
    except BaseException:
        sink.abort()
        raise
    finally:
        close = getattr(stream, "close", None)
        if callable(close):
            close()
        if not sink.ended:  # FFmpeg's exit was not seen: the run failed first
            sink.ended = vf._clock()
        samples = sampler.stop() if sampler is not None else None
        record["telemetry"] = telemetry.stop()
        windows.append(_strays_window(watch, len(intervals), time.perf_counter() - started))
        record["strays"] = {**strays, "pauses_s": pauses, "windows": windows}
    count = report.frames_written
    paused = sum(pauses)
    apart = {0, *after_pause}
    kept = [i for i in range(len(intervals)) if i not in apart]
    cuda = hw_decode and cuda_decode_available()
    record.update(
        {
            "clip": path.name,
            "encoder": encoder,
            "quality": quality,
            "bit_depth": depth,
            "size": [info.video.height, info.video.width],
            "frame_rate": str(info.video.frame_rate),
            "frames": count,
            "decode": {
                "hw_decode_asked": hw_decode,
                "cuda": cuda,
                "command": decode_command(info, ffmpeg=find_tool("ffmpeg"), cuda=cuda),
            },
            "encode_command": sink.command,
            "stages_s": {
                "probe": probed - started,
                "open": opened - probed,
                "stream": streamed - opened - paused,
                "close": closed - streamed,
                "total": closed - started - paused,
                "strays_pauses": paused,
            },
            "total": rate(closed - started - paused, count, info.video.frame_rate),
            "stream": rate(streamed - opened - paused, count, info.video.frame_rate),
            "first_frame_s": intervals[0] if intervals else None,
            "after_pause_frames": [i for i in after_pause if i < len(intervals)],
            "after_pause": summarise([intervals[i] for i in after_pause if i < len(intervals)]),
            "per_frame": summarise([intervals[i] for i in kept]),
            "decode_wait": summarise([waits[i] for i in kept]),
            "write": summarise([writes[i] for i in kept]),
            "per_frame_s": [round(value, 5) for value in intervals],
            "decode_wait_s": [round(value, 5) for value in waits],
            "write_s": [round(value, 5) for value in writes],
            "output_bytes": output.stat().st_size,
            "output_video_bit_rate": video_bit_rate(output),
            "source_video_bit_rate": video_bit_rate(path),
            "sink_report": {
                "frames_written": report.frames_written,
                "warnings": list(report.warnings),
                "not_carried": list(report.not_carried),
            },
            "nvenc_proof": vf.nvenc_proof(
                vf.EncodeRun(report, encoder, depth, sink.pid, sink.started, sink.ended, samples)
            ),
            "python_peak_wset_bytes": getattr(psutil.Process().memory_info(), "peak_wset", None),
            "after": conditions("after"),
        }
    )
    return record


def _strays_window(watch: StrayWatch, frames: int, at_s: float) -> dict[str, Any]:
    """Read ``watch`` after ``frames`` frames, ``at_s`` seconds into the run, timing the read."""
    began = time.perf_counter()
    window = watch.window()
    return {
        "after_frame": frames,
        "at_s": round(at_s, 2),
        **window,
        "read_s": round(time.perf_counter() - began, 3),
    }


# --- the command line ----------------------------------------------------------------------


def row_line(record: dict[str, Any]) -> str:
    """Return the one-line summary of a run's record."""
    total, per_frame = record["total"], record["per_frame"] or {}
    peak = record["telemetry"]["peak_tree_rss_bytes"] / 1024**2
    gpu = record["telemetry"]["peak_gpu_memory_used_mib"]
    return (
        f"ROW {record['clip']} {record['encoder']} {record['bit_depth']}-bit {record['quality']}: "
        f"{record['frames']} frames, {total['s_per_frame']:.4f} s/frame, "
        f"{total['min_per_min']:.2f} min/min (per frame median {per_frame.get('median', 0):.4f}, "
        f"p90 {per_frame.get('p90', 0):.4f}, max {per_frame.get('max', 0):.4f}); peak tree RSS "
        f"{peak:.0f} MiB; peak GPU memory {gpu} MiB; tied {record['nvenc_proof'].get('tied')}"
    )


def period(text: str) -> float:
    """Parse a telemetry period: a finite number of seconds above zero.

    Raises:
        argparse.ArgumentTypeError: Anything else (a zero or negative period would make the
            telemetry loop spin and distort the run it measures).
    """
    try:
        seconds = float(text)
    except ValueError:
        seconds = math.nan
    if not (math.isfinite(seconds) and seconds > 0):
        raise argparse.ArgumentTypeError(f"a period must be a positive number of seconds: {text}")
    return seconds


def frame_count(text: str) -> int:
    """Parse a number of frames: a whole number above zero.

    Raises:
        argparse.ArgumentTypeError: Anything else.
    """
    try:
        frames = int(text)
    except ValueError:
        frames = 0
    if frames < 1:
        raise argparse.ArgumentTypeError(f"a frame count must be a positive whole number: {text}")
    return frames


def _write(path: Path, record: dict[str, Any]) -> None:
    path.write_text(json.dumps(record, indent=2, default=str), encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Run the floor row (or one leg) and write its record under the working folder.

    Args:
        argv: The command-line arguments (``sys.argv[1:]`` when None).

    Returns:
        The exit status.
    """
    options = argparse.ArgumentParser(add_help=False)
    options.add_argument("--config", type=Path, help="local configuration file to read")
    options.add_argument("--keep", action="store_true", help="keep the outputs")
    options.add_argument("--software-decode", action="store_true", help="decode without CUDA")
    options.add_argument("--memory-every", type=period, default=0.25, help="seconds")
    options.add_argument("--gpu-every", type=period, default=1.0, help="seconds")
    options.add_argument(
        "--strays-every", type=frame_count, default=STRAYS_EVERY_FRAMES, help="frames"
    )
    parser = argparse.ArgumentParser(description=(__doc__ or "").splitlines()[0])
    commands = parser.add_subparsers(dest="command", required=True)
    one = commands.add_parser("run", help="one leg", parents=[options])
    one.add_argument("clip", help="footage stem, for example GX011627")
    one.add_argument("--runs", type=int, default=1)
    one.add_argument("--encoder", default="hevc_nvenc", choices=("hevc_nvenc", "libx265"))
    one.add_argument("--quality", default="standard", choices=("high", "standard", "draft"))
    one.add_argument("--bit-depth", type=int, choices=(8, 10), help="the source's when omitted")
    floor = commands.add_parser("floor", help="the ruled row set (FLOOR_PLAN)", parents=[options])
    floor.add_argument("--dry-run", action="store_true", help="list the runs and stop")
    args = parser.parse_args(argv)
    if args.command == "run":
        if args.runs < 1:
            parser.error("--runs must be at least 1")
        legs: tuple[Leg, ...] = (
            Leg(args.clip, args.encoder, args.bit_depth, args.runs, args.quality),
        )
        name = args.clip
    else:
        legs, name = FLOOR_PLAN, "floor"
    try:
        config = load_local_config(args.config)
        paths = {leg.clip: find_footage_file(leg.clip, config.footage_path) for leg in legs}
        out_dir = config.working_path / SUBDIR
        out_dir.mkdir(parents=True, exist_ok=True)
        for leg in legs:
            check_disk(paths[leg.clip], out_dir)
    except (LocalConfigError, ValueError, OSError, BenchError) as error:
        print(f"ERROR {type(error).__name__}: {error}", file=sys.stderr)
        return 2
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    if getattr(args, "dry_run", False):
        for leg in legs:
            print(f"PLAN {leg.clip} x{leg.runs} {leg.encoder} {leg.bit_depth}-bit {leg.quality}")
        return 0
    record_path = out_dir / f"io-bench-{name}-{stamp}.json"
    record: dict[str, Any] = {"plan": [asdict(leg) for leg in legs], "pid": os.getpid(), "runs": []}
    for leg in legs:
        for number in range(1, leg.runs + 1):
            depth = "src" if leg.bit_depth is None else str(leg.bit_depth)
            output = out_dir / f"{leg.clip}-{leg.encoder}-{depth}-{stamp}-{len(record['runs'])}.mp4"
            print(f"RUN {leg.clip} {leg.encoder} {depth} {leg.quality} ({number}/{leg.runs})")
            try:
                check_disk(paths[leg.clip], out_dir)  # again: kept outputs add up
                run = run_once(
                    paths[leg.clip],
                    output,
                    encoder=leg.encoder,
                    quality=leg.quality,
                    bit_depth=leg.bit_depth,
                    hw_decode=not args.software_decode,
                    keep=args.keep,
                    periods=(args.memory_every, args.gpu_every),
                    strays_every=args.strays_every,
                )
            except Exception as error:
                record["failed"] = {
                    "clip": leg.clip,
                    "encoder": leg.encoder,
                    "bit_depth": leg.bit_depth,
                    "error": f"{type(error).__name__}: {error}",
                }
                _write(record_path, record)
                print(f"FAILED {type(error).__name__}: {error}", file=sys.stderr)
                print(f"RECORD {record_path}")
                return 1
            record["runs"].append(run)
            _write(record_path, record)
            print(row_line(run), flush=True)
    print(f"RECORD {record_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
