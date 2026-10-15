"""Time one sustained run of the prototype pipeline on a synthetic frame and record its memory.

Usage::

    uv run python tools/prototype/bench.py --device {cpu,gpu} --size {4k,5.3k,WxH}
        --frames N --method {ancuti2018,c3} --out DIR [--proxy S ...] [--seed N]
        [--note TEXT]

The instrument of WP1.2 Part A. It builds ONE synthetic frame (:func:`synthetic_frame`),
runs :func:`prototype.pipeline.correct` on it ``N`` times in sequence on the chosen
device, and writes one JSON record, ``<out>/bench-<device>-<size>-<method>-<stamp>.json``,
whose path it prints. The figures are SYNTHETIC: the record is labelled so, and they are
not the prototype gate's result on real footage.

Timing. Each frame's wall-clock time is ``time.perf_counter()`` around ``correct()`` on
the NumPy frame followed by ``synchronize()`` of the backend, so the time includes the
host-to-device copy of the input, every kernel, and the device-to-host copy of every array
of the result. The first frame (kernel compilation, pool growth) is discarded as warm-up
before the median and the 95th percentile; the drift is the median of the last ten frames
over the median of the first ten after the warm-up. On the GPU a second, supplementary
loop of ``N`` frames times the device-resident path a renderer would use: the input copied
to the device, ``correct()`` on the device array, and only the output copied back.

Memory. Peak RSS is the maximum of ``psutil`` samples taken by a thread every 50 ms during
the timed loop. On the GPU, CuPy's default memory pool is wrapped by a counting allocator
that records the pool's used bytes after every allocation (its high-water mark), and the
pool's reserved bytes are read after the timed loop (the pool's cache is emptied before the
loop and the pool never returns memory during it, so that is its own high-water mark).
``nvidia-smi --query-gpu=memory.used`` is read before the backend starts and the CUDA
runtime's device-wide used memory just after it starts (the CUDA context then exists);
both are read again after the timed loop, while the pool still holds its memory. The
``nvidia-smi`` per-process figure is recorded as the driver reports it (``[N/A]`` under
Windows' WDDM driver model). :func:`prototype.backend.memory_estimate_bytes` is recorded
beside them.

``--proxy S`` (repeatable) also computes the whole-frame statistics, the channel means, the
white-balance gains and the normalisation bounds, on the frame box-downscaled to short side
``S`` and records them with their relative error against the full-size ones (D60, D109).

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, on a bad
argument, an unusable device or an output that cannot be written.
"""

from __future__ import annotations

import argparse
import dataclasses
import datetime
import json
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
from collections.abc import Sequence
from pathlib import Path
from typing import Any, NoReturn

import numpy as np
import psutil
import scipy
from numpy.typing import NDArray
from PIL import Image as PILImage
from scipy import ndimage

if not __package__:
    # Script mode (``python tools/prototype/bench.py``): sys.path[0] is tools/prototype, so
    # put the tools directory first to make the ``prototype`` package importable.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from prototype.backend import Backend, memory_estimate_bytes, select_backend
from prototype.params import METHODS, Params
from prototype.pipeline import (
    compensate_ancuti2018,
    compensate_c3,
    correct,
    normalisation_bounds,
    white_balance,
)

SIZES: dict[str, tuple[int, int]] = {"4k": (2160, 3840), "5.3k": (2988, 5312)}
"""Named sizes as ``(height, width)``: UHD 4K and the GoPro 16:9 5.3K mode."""

BUDGET_30FPS_S = 0.111
"""N6 per-frame budget at 30 fps, end to end (D106: about 3.3 min per min of footage)."""

BUDGET_60FPS_S = 0.056
"""N6 per-frame budget at 60 fps, end to end."""

RSS_SAMPLE_INTERVAL_S = 0.05
"""Interval of the peak-RSS sampling thread."""

_MIB = 1024 * 1024
_SIZE_PATTERN = re.compile(r"^([1-9][0-9]*)x([1-9][0-9]*)$")


class _UsageError(Exception):
    """A bad command-line argument or an unusable device; exit status 2."""


class _Parser(argparse.ArgumentParser):
    """An argument parser that raises :class:`_UsageError` instead of exiting."""

    def error(self, message: str) -> NoReturn:
        """Raise the parse error instead of printing usage and exiting.

        Args:
            message: The parser's error message.

        Raises:
            _UsageError: Always.
        """
        raise _UsageError(message)


def synthetic_frame(height: int, width: int, seed: int = 0) -> NDArray[np.float32]:
    """Build the seeded synthetic test frame: a blue-green cast over texture and noise.

    The frame is ``clip(base * (1 + 0.3 * texture) + noise, 0, 1)``, with ``x`` and ``y``
    running over [0, 1] across the frame:

    - ``base``, the cast: red ``0.05 + 0.15 x``, green ``0.35 + 0.35 y``, blue
      ``0.45 + 0.25 x y`` (weak red, strong green and blue, as at depth);
    - ``texture``, a band-limited pattern: uniform noise smoothed by a Gaussian of sigma
      0.004 of the short side and rescaled to [-1, 1], so the pattern scales with the frame;
    - ``noise``, per-pixel, per-channel Gaussian noise of standard deviation 0.01 (a sensor
      noise floor, which does not scale with the frame).

    Args:
        height: Frame height in pixels.
        width: Frame width in pixels.
        seed: Seed of the NumPy random generator.

    Returns:
        The frame, float32, shape ``(height, width, 3)``, values in [0, 1].
    """
    rng = np.random.default_rng(seed)
    y = np.linspace(0.0, 1.0, height, dtype=np.float32)[:, None]
    x = np.linspace(0.0, 1.0, width, dtype=np.float32)[None, :]
    base = np.empty((height, width, 3), dtype=np.float32)
    base[..., 0] = 0.05 + 0.15 * x
    base[..., 1] = 0.35 + 0.35 * y
    base[..., 2] = 0.45 + 0.25 * x * y
    field: NDArray[np.float32] = ndimage.gaussian_filter(
        rng.random((height, width), dtype=np.float32), 0.004 * min(height, width)
    )
    low, high = float(field.min()), float(field.max())
    texture = np.asarray(2.0 * (field - low) / max(high - low, 1e-12) - 1.0, dtype=np.float32)
    frame = base * (1.0 + 0.3 * texture[..., None])
    frame += rng.normal(0.0, 0.01, frame.shape).astype(np.float32)
    return np.clip(frame, 0.0, 1.0).astype(np.float32, copy=False)


def proxy_frame(frame: NDArray[np.float32], short_side: int) -> NDArray[np.float32]:
    """Downscale a frame to the given short side by area averaging (Pillow's BOX filter).

    Args:
        frame: The full-size frame, float32, ``(H, W, 3)``.
        short_side: The proxy's short side in pixels; the aspect ratio is kept (the long
            side is rounded to the nearest pixel).

    Returns:
        The proxy, float32, ``(h, w, 3)``; the frame itself when ``short_side`` is its own.
    """
    height, width = frame.shape[0], frame.shape[1]
    if short_side == min(height, width):
        return frame
    scale = short_side / min(height, width)
    size = (max(1, round(width * scale)), max(1, round(height * scale)))
    channels = [
        np.asarray(
            PILImage.fromarray(np.ascontiguousarray(frame[..., c])).resize(
                size, PILImage.Resampling.BOX
            ),
            dtype=np.float32,
        )
        for c in range(3)
    ]
    return np.clip(np.stack(channels, axis=2), 0.0, 1.0).astype(np.float32, copy=False)


def frame_statistics(
    frame: NDArray[np.float32], params: Params, backend: Backend
) -> dict[str, Any]:
    """Compute the pipeline's whole-frame statistics of one frame on ``backend``.

    Args:
        frame: The frame, float32, ``(H, W, 3)``, on the host.
        params: The parameter set (its method selects the compensation).
        backend: Where to compute.

    Returns:
        The input channel means, the channel means after compensation (the white
        balance's input), the applied white-balance gains and the normalisation bounds.
    """
    work = backend.to_device(frame)
    compensate = compensate_c3 if params.method == "c3" else compensate_ancuti2018
    compensated, compensation = compensate(work, params)
    balanced, balance = white_balance(compensated, params)
    low, high = normalisation_bounds(balanced, params)
    return {
        "input_means": list(compensation.channel_means),
        "compensated_means": list(balance.channel_means),
        "white_balance_gains": list(balance.applied_gains),
        "normalisation_bounds": [low, high],
    }


def main(argv: Sequence[str] | None = None) -> int:
    """Run the benchmark and write its JSON record.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 on success; 2 on a bad argument, an unusable device or an unwritable output,
        with a one-line error on standard error.
    """
    try:
        args = _parse(argv)
        height, width = _parse_size(args.size)
        if args.frames < 1:
            raise _UsageError(f"--frames must be at least 1, got {args.frames}")
        for side in args.proxy:
            if not 1 <= side <= min(height, width):
                raise _UsageError(
                    f"--proxy must lie in [1, {min(height, width)}] for this size, got {side}"
                )
        ambient_gpu = _nvidia_smi_gpu()
        cuda_before = None
        backend = select_backend(args.device)
    except (_UsageError, RuntimeError) as exc:
        print(f"error: {_one_line(exc)}", file=sys.stderr)
        return 2

    params = Params(method=args.method)
    tracker = _PoolTracker(backend) if backend.name == "gpu" else None
    if tracker is not None:
        cuda_before = tracker.cuda_used_bytes()
    frame = synthetic_frame(height, width, args.seed)
    process = psutil.Process()
    rss_baseline = int(process.memory_info().rss)

    sampler = _PeakRssSampler(process)
    sampler.start()
    try:
        times = _timed_loop(frame, params, backend, args.frames)
    finally:
        sampler.stop()
        if tracker is not None:
            tracker.close()

    memory = _memory_record(rss_baseline, sampler.peak, process)
    if tracker is not None:
        memory |= tracker.record(ambient_gpu, cuda_before)
    resident = (
        _timing_record(_resident_loop(frame, params, backend, args.frames))
        if backend.name == "gpu"
        else None
    )
    estimate = memory_estimate_bytes(frame.shape, params)
    record: dict[str, Any] = {
        "label": "SYNTHETIC",
        "tool": "tools/prototype/bench.py",
        "created": datetime.datetime.now().astimezone().isoformat(timespec="seconds"),
        "device": args.device,
        "backend": backend.name,
        "size": args.size,
        "shape": list(frame.shape),
        "method": args.method,
        "frames": args.frames,
        "seed": args.seed,
        "generator": "synthetic_frame(): blue-green cast, band-limited texture, pixel noise",
        "params": dataclasses.asdict(params),
        "timing": _timing_record(times),
        "device_resident": resident,
        "memory": memory,
        "estimate": _estimate_record(estimate, memory),
        "proxy": _proxy_record(frame, params, backend, args.proxy),
        "versions": _versions(backend),
        "machine": _machine(ambient_gpu),
        "ambient": _ambient(ambient_gpu, args.note),
    }
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    path = args.out / f"bench-{backend.name}-{args.size}-{args.method}-{stamp}.json"
    try:
        args.out.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    except OSError as exc:
        print(f"error: cannot write to {args.out}: {_one_line(exc)}", file=sys.stderr)
        return 2
    print(path)
    return 0


def _parse(argv: Sequence[str] | None) -> argparse.Namespace:
    """Parse the command line.

    Raises:
        _UsageError: A missing or malformed argument.
    """
    parser = _Parser(description="Time the WP1.1 pipeline on a synthetic frame (WP1.2 Part A).")
    parser.add_argument("--device", choices=("cpu", "gpu"), required=True)
    parser.add_argument("--size", required=True, help="4k, 5.3k or WIDTHxHEIGHT")
    parser.add_argument("--frames", type=int, required=True, help="frames in the timed run")
    parser.add_argument("--method", choices=METHODS, required=True)
    parser.add_argument("--out", type=Path, required=True, help="folder for the JSON record")
    parser.add_argument(
        "--proxy", type=int, action="append", default=[], metavar="S", help="proxy short side"
    )
    parser.add_argument("--seed", type=int, default=0, help="seed of the synthetic frame")
    parser.add_argument("--note", default="", help="free text stored with the ambient record")
    return parser.parse_args(argv)


def _parse_size(text: str) -> tuple[int, int]:
    """Return ``(height, width)`` for a named size or ``WIDTHxHEIGHT``.

    Raises:
        _UsageError: The size is neither.
    """
    if text in SIZES:
        return SIZES[text]
    match = _SIZE_PATTERN.match(text)
    if match is None:
        raise _UsageError(f"--size must be 4k, 5.3k or WIDTHxHEIGHT, got {text!r}")
    return int(match.group(2)), int(match.group(1))


def _timed_loop(
    frame: NDArray[np.float32], params: Params, backend: Backend, frames: int
) -> list[float]:
    """Run ``correct()`` on the host frame ``frames`` times; return each frame's seconds."""
    times: list[float] = []
    for _ in range(frames):
        start = time.perf_counter()
        result = correct(frame, params, backend)
        backend.synchronize()
        times.append(time.perf_counter() - start)
        del result
    return times


def _resident_loop(
    frame: NDArray[np.float32], params: Params, backend: Backend, frames: int
) -> list[float]:
    """Time the device-resident path: input to the device, output alone back to the host."""
    times: list[float] = []
    for _ in range(frames):
        start = time.perf_counter()
        result = correct(backend.to_device(frame), params)
        output = backend.to_host(result.output)
        backend.synchronize()
        times.append(time.perf_counter() - start)
        del result, output
    return times


def _timing_record(times: list[float]) -> dict[str, Any]:
    """Summarise per-frame times: all of them, then statistics without the warm-up frame."""
    steady = times[1:]
    record: dict[str, Any] = {
        "method": "perf_counter() around correct() and synchronize(); first frame is warm-up",
        "per_frame_s": times,
        "warmup_discarded": 1,
        "median_s": None,
        "p95_s": None,
        "first10_median_s": None,
        "last10_median_s": None,
        "drift": None,
        "budget_share_30fps": None,
        "budget_share_60fps": None,
    }
    if not steady:
        return record
    median = float(np.median(steady))
    first = float(np.median(steady[:10]))
    last = float(np.median(steady[-10:]))
    record |= {
        "median_s": median,
        "p95_s": float(np.percentile(steady, 95.0, method="linear")),
        "first10_median_s": first,
        "last10_median_s": last,
        "drift": last / first - 1.0,
        "budget_share_30fps": median / BUDGET_30FPS_S,
        "budget_share_60fps": median / BUDGET_60FPS_S,
    }
    return record


def _memory_record(rss_baseline: int, rss_peak: int, process: Any) -> dict[str, Any]:
    """The host memory figures, in MiB."""
    info = process.memory_info()
    peak_wset = getattr(info, "peak_wset", None)  # reported by psutil on some systems only
    return {
        "unit": "MiB",
        "rss_sampling": f"psutil RSS, thread sampling every {RSS_SAMPLE_INTERVAL_S * 1000:.0f} ms",
        "rss_baseline_mb": rss_baseline / _MIB,
        "rss_peak_mb": rss_peak / _MIB,
        "os_peak_working_set_mb": None if peak_wset is None else int(peak_wset) / _MIB,
    }


def _estimate_record(estimate: int, memory: dict[str, Any]) -> dict[str, Any]:
    """The working-set estimate and its ratio to each measured peak."""
    estimate_mb = estimate / _MIB
    record: dict[str, Any] = {
        "bytes": estimate,
        "mb": estimate_mb,
        "ratio_to_rss_peak": estimate_mb / memory["rss_peak_mb"],
        "ratio_to_gpu_pool_reserved": None,
        "ratio_to_gpu_pool_peak_used": None,
    }
    if memory.get("gpu_pool_reserved_mb"):
        record["ratio_to_gpu_pool_reserved"] = estimate_mb / memory["gpu_pool_reserved_mb"]
        record["ratio_to_gpu_pool_peak_used"] = estimate_mb / memory["gpu_pool_peak_used_mb"]
    return record


def _proxy_record(
    frame: NDArray[np.float32], params: Params, backend: Backend, sides: list[int]
) -> list[dict[str, Any]]:
    """The whole-frame statistics at each proxy short side against the full-size ones."""
    if not sides:
        return []
    full_side = min(frame.shape[0], frame.shape[1])
    full = frame_statistics(frame, params, backend)
    records = []
    for side in [full_side, *sorted(set(sides) - {full_side}, reverse=True)]:
        proxy = proxy_frame(frame, side)
        stats = full if side == full_side else frame_statistics(proxy, params, backend)
        errors = {
            key: [_relative_error(p, f) for p, f in zip(stats[key], full[key], strict=True)]
            for key in full
        }
        records.append(
            {"short_side": side, "shape": list(proxy.shape), **stats, "relative_error": errors}
        )
    return records


def _relative_error(value: float, reference: float) -> float | None:
    """``|value - reference| / |reference|``; ``None`` for a zero reference."""
    if reference == 0.0:
        return None
    return abs(value - reference) / abs(reference)


def _versions(backend: Backend) -> dict[str, Any]:
    """Library and driver versions."""
    versions: dict[str, Any] = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "scipy": scipy.__version__,
        "cupy": None,
        "cuda_runtime": None,
        "cuda_driver_api": None,
    }
    if backend.name == "gpu":
        runtime = backend.xp.cuda.runtime
        versions |= {
            "cupy": backend.xp.__version__,
            "cuda_runtime": _cuda_version(int(runtime.runtimeGetVersion())),
            "cuda_driver_api": _cuda_version(int(runtime.driverGetVersion())),
        }
    return versions


def _machine(gpu: dict[str, str] | None) -> dict[str, Any]:
    """The machine: operating system, processor, memory and graphics card."""
    return {
        "platform": platform.platform(),
        "processor": _cpu_brand(),
        "logical_cpus": os.cpu_count(),
        "ram_total_mb": int(psutil.virtual_memory().total) / _MIB,
        "gpu_name": None if gpu is None else gpu.get("name"),
        "gpu_memory_total_mb": None if gpu is None else _float(gpu.get("memory.total")),
        "nvidia_driver": None if gpu is None else gpu.get("driver_version"),
    }


def _ambient(gpu: dict[str, str] | None, note: str) -> dict[str, Any]:
    """The conditions of the run: graphics memory in use before it, power source, a note."""
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    return {
        "nvidia_smi_used_before_mb": None if gpu is None else _float(gpu.get("memory.used")),
        "power_plugged": None if battery is None else bool(battery.power_plugged),
        "battery_percent": None if battery is None else float(battery.percent),
        "note": note,
    }


class _PeakRssSampler:
    """A thread that samples the process's RSS every :data:`RSS_SAMPLE_INTERVAL_S`."""

    def __init__(self, process: Any) -> None:
        """Prepare the sampler; :meth:`start` begins sampling."""
        self._process = process
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self.peak = int(process.memory_info().rss)

    def start(self) -> None:
        """Start sampling."""
        self._thread.start()

    def stop(self) -> None:
        """Stop sampling, after one last sample."""
        self._stop.set()
        self._thread.join()
        self._sample()

    def _run(self) -> None:
        while not self._stop.wait(RSS_SAMPLE_INTERVAL_S):
            self._sample()

    def _sample(self) -> None:
        self.peak = max(self.peak, int(self._process.memory_info().rss))


class _PoolTracker:
    """Counts the high-water mark of CuPy's default memory pool through its allocator."""

    def __init__(self, backend: Backend) -> None:
        """Empty the default pool's cache and install a counting allocator in front of it."""
        self._cupy = backend.xp
        self._pool = self._cupy.get_default_memory_pool()
        self._pool.free_all_blocks()
        self.peak_used = int(self._pool.used_bytes())
        self._cupy.cuda.set_allocator(self._malloc)

    def _malloc(self, size: int) -> Any:
        memory = self._pool.malloc(size)
        self.peak_used = max(self.peak_used, int(self._pool.used_bytes()))
        return memory

    def close(self) -> None:
        """Hand allocation back to the pool directly (the pool keeps its memory)."""
        self._cupy.cuda.set_allocator(self._pool.malloc)

    def cuda_used_bytes(self) -> int:
        """Device memory in use on the whole card, from the CUDA runtime."""
        free, total = self._cupy.cuda.runtime.memGetInfo()
        return int(total) - int(free)

    def record(self, gpu_before: dict[str, str] | None, cuda_before: int | None) -> dict[str, Any]:
        """The graphics memory figures, in MiB, read now (the pool still holds its memory)."""
        after = _nvidia_smi_gpu()
        cuda_after = self.cuda_used_bytes()
        return {
            "gpu_pool_peak_used_mb": self.peak_used / _MIB,
            "gpu_pool_reserved_mb": int(self._pool.total_bytes()) / _MIB,
            "gpu_pool_method": "counting allocator over cupy's default pool; reserved at end",
            "nvidia_smi_used_before_mb": None
            if gpu_before is None
            else _float(gpu_before.get("memory.used")),
            "nvidia_smi_used_after_mb": None if after is None else _float(after.get("memory.used")),
            "nvidia_smi_process_mb": _nvidia_smi_process_mb(),
            "cuda_used_before_mb": None if cuda_before is None else cuda_before / _MIB,
            "cuda_used_after_mb": cuda_after / _MIB,
        }


def _nvidia_smi_gpu() -> dict[str, str] | None:
    """Read name, driver and memory of the first GPU from ``nvidia-smi``; None if absent."""
    fields = ("name", "driver_version", "memory.total", "memory.used")
    lines = _nvidia_smi([f"--query-gpu={','.join(fields)}", "--format=csv,noheader,nounits"])
    if not lines:
        return None
    values = [value.strip() for value in lines[0].split(",")]
    if len(values) != len(fields):
        return None
    return dict(zip(fields, values, strict=True))


def _nvidia_smi_process_mb() -> float | str | None:
    """This process's graphics memory as ``nvidia-smi`` reports it (a string if not a number)."""
    lines = _nvidia_smi(["--query-compute-apps=pid,used_memory", "--format=csv,noheader,nounits"])
    if lines is None:
        return None
    for line in lines:
        pid, _, used = (value.strip() for value in line.partition(","))
        if pid == str(os.getpid()):
            number = _float(used)
            return used if number is None else number
    return "not listed"


def _nvidia_smi(arguments: list[str]) -> list[str] | None:
    """Run ``nvidia-smi`` with ``arguments``; its output lines, or None if it cannot run."""
    executable = shutil.which("nvidia-smi")
    if executable is None:
        return None
    try:
        completed = subprocess.run(
            [executable, *arguments], capture_output=True, text=True, timeout=20, check=True
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return [line for line in completed.stdout.splitlines() if line.strip()]


def _cpu_brand() -> str:
    """The processor's name (py-cpuinfo), or ``platform.processor()`` if that fails."""
    try:
        import cpuinfo

        return str(cpuinfo.get_cpu_info().get("brand_raw", "")) or platform.processor()
    except Exception:  # py-cpuinfo is best effort on an unusual system
        return platform.processor()


def _cuda_version(code: int) -> str:
    """A CUDA version code (``1000 * major + 10 * minor``) as ``major.minor``."""
    return f"{code // 1000}.{code % 1000 // 10}"


def _float(text: str | None) -> float | None:
    """``text`` as a float, or None if it is not a number."""
    try:
        return None if text is None else float(text)
    except ValueError:
        return None


def _one_line(exc: BaseException) -> str:
    """The exception's message on one line (its class name when the message is empty)."""
    return " ".join(str(exc).split()) or type(exc).__name__


if __name__ == "__main__":
    raise SystemExit(main())
