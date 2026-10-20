"""WP3.1 speed row: the IF-2 operations of the c3 and ancuti2018 paths, product vs prototype.

WP3.1 has no correction method, so the whole-core figure waits for WP3.4 (brief ruling 4).
This instrument times, per decoded frame, the array operations one ``correct()`` call makes
through IF-2 and the ``clearwater.core`` helpers (the "op mix"), once through the product and
once through the read-only prototype making the same calls, on the GPU and on the CPU:

- c3 only: ``rgb_to_ycbcr``; the bright-pixel mask blur (``c3_mask_smooth_fraction``); the Cb
  and Cr blurs at the c3 kernel sigma (``c3_kernel_fraction``, AD-8);
- both methods: the white-balance channel means; the sharpening blur and the N{} percentiles of
  its high-pass; per fusion input (two), the luma, its blur at ``laplacian_fraction`` and its
  Laplacian, the Lab image, its blur at ``saliency_blur_fraction`` and its means, the Laplacian
  pyramid of the input and the Gaussian pyramid of a weight map; one pyramid collapse.

The per-pixel arithmetic between these calls (gains, clipping, the weight sums) is not timed:
it belongs to WP3.2-3.4. The frame upload is timed apart from the op mix.

Plan 4.3 / frame rule 7: an EXCLUSIVE run, one at a time, best effort on a shared laptop. GPU
clocks, temperature, utilisation and the processes using a CPU are recorded before, during
(every ``--sample-every`` frames) and after; a contaminated row is kept as spread. The GPU pass
covers the full clip; the CPU pass covers ``--cpu-frames`` frames spread evenly over the clip
(the WP1.2 Part B practice: a 4K CPU frame takes seconds per operation).

The footage is reached only through ``local_config.find_footage_file`` and read by an FFmpeg
decode to a pipe; nothing is written outside the working folder. Usage::

    uv run python tools/core_speed.py GX011627 [--cpu-frames 10] [--gpu-frames N]
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import json
import math
import statistics
import subprocess
import sys
import time
from collections.abc import Callable, Iterator, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import numpy as np
import psutil
from numpy.typing import NDArray

from clearwater import core
from clearwater.core import CoreBackend, CupyBackend, NumpyBackend
from local_config import find_footage_file, load_local_config
from prototype import pipeline as proto
from prototype.backend import of as prototype_backend_of
from prototype.params import Params

METHODS = ("c3", "ancuti2018")
IMPLEMENTATIONS = ("product", "prototype")
OUTPUT_SUBDIR = Path("wp3.1") / "speed"
_GPU_QUERY = "clocks.sm,clocks.mem,temperature.gpu,utilization.gpu,memory.used,power.draw"


class SpeedError(RuntimeError):
    """The clip cannot be probed or decoded, or the GPU is not usable."""


@dataclass(frozen=True)
class ClipInfo:
    """The decoded geometry of a clip.

    Attributes:
        path: The video file.
        width: Frame width in pixels.
        height: Frame height in pixels.
        frames: The number of video frames.
    """

    path: Path
    width: int
    height: int
    frames: int


def probe_clip(path: Path) -> ClipInfo:
    """Read the frame size and count of the first video stream with ffprobe.

    Args:
        path: The video file.

    Returns:
        The clip geometry.

    Raises:
        SpeedError: ffprobe fails or reports no usable stream.
    """
    command = [
        "ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
        "-show_entries", "stream=width,height,nb_read_packets", "-of", "json", str(path),
    ]  # fmt: skip
    result = subprocess.run(command, capture_output=True, text=True, check=False, timeout=600)
    if result.returncode != 0:
        raise SpeedError(f"ffprobe failed on {path.name}: {result.stderr.strip()[-300:]}")
    stream = json.loads(result.stdout)["streams"][0]
    return ClipInfo(
        path, int(stream["width"]), int(stream["height"]), int(stream["nb_read_packets"])
    )


def decode(clip: ClipInfo, wanted: Sequence[int]) -> Iterator[tuple[int, NDArray[np.float32]]]:
    """Decode the clip once and yield the wanted frames as float32 RGB in [0, 1].

    FFmpeg converts to 16-bit RGB (``rgb48le``); the frames not wanted are read and dropped, so
    the indices are presentation order.

    Args:
        clip: The clip.
        wanted: The frame indices to yield, ascending.

    Yields:
        The frame index and the frame, shape ``(H, W, 3)``.

    Raises:
        SpeedError: FFmpeg ends before the last wanted frame.
    """
    frame_bytes = clip.width * clip.height * 6
    command = [
        "ffmpeg", "-v", "error", "-nostdin", "-i", str(clip.path), "-map", "0:v:0",
        "-f", "rawvideo", "-pix_fmt", "rgb48le", "pipe:1",
    ]  # fmt: skip
    targets = set(wanted)
    last = max(targets)
    with subprocess.Popen(command, stdout=subprocess.PIPE, bufsize=32 * 1024 * 1024) as decoder:
        assert decoder.stdout is not None
        try:
            for index in range(last + 1):
                data = decoder.stdout.read(frame_bytes)
                if len(data) != frame_bytes:
                    raise SpeedError(f"{clip.path.name} ended at frame {index}")
                if index in targets:
                    raw = np.frombuffer(data, dtype="<u2").reshape(clip.height, clip.width, 3)
                    yield index, (raw.astype(np.float32) / np.float32(65535.0))
        finally:
            decoder.kill()


def dark_mask(image: Any, params: Params) -> Any:
    """Return the c3 mask, 1 where the pixel mean is at most ``c3_mask_threshold`` (float32).

    The same values as the prototype's ``where(bright, 0, 1)``, by array methods only.

    Args:
        image: The frame (NumPy or CuPy).
        params: Uses ``c3_mask_threshold``.

    Returns:
        The mask, shape ``(H, W)``.
    """
    return (image.mean(axis=2, dtype=np.float32) <= params.c3_mask_threshold).astype(np.float32)


def op_mix_product(backend: CoreBackend, image: Any, method: str, params: Params) -> None:
    """Run the op mix through the product (IF-2 and ``clearwater.core`` helpers).

    Args:
        backend: The backend ``image`` lives on.
        image: The frame on that backend.
        method: ``"c3"`` or ``"ancuti2018"``.
        params: The parameters (the prototype's defaults).
    """
    shape = image.shape
    if method == "c3":
        ycbcr = backend.rgb_to_ycbcr(image, "bt709", "full")
        mask = dark_mask(image, params)
        backend.gaussian_blur(mask, core.spatial_sigma(shape, params.c3_mask_smooth_fraction))
        sigma = core.spatial_sigma(shape, params.c3_kernel_fraction)
        backend.gaussian_blur(ycbcr[..., 1], sigma)
        backend.gaussian_blur(ycbcr[..., 2], sigma)
    core.channel_means(backend, image)
    high_pass = image - backend.gaussian_blur(
        image, core.spatial_sigma(shape, params.sharpen_blur_fraction)
    )
    backend.percentile(high_pass, [params.normalisation_low, params.normalisation_high])
    levels = core.pyramid_levels(shape, params.pyramid_min_level_size)
    bands = []
    for _ in range(2):
        luma = core.luminance(backend, image)
        laplace_sigma = core.spatial_sigma(shape, params.laplacian_fraction)
        weight = core.laplacian(backend, backend.gaussian_blur(luma, laplace_sigma))
        lab = core.rgb_to_lab(backend, image)
        core.channel_means(backend, lab)
        backend.gaussian_blur(lab, core.spatial_sigma(shape, params.saliency_blur_fraction))
        bands = core.laplacian_pyramid(backend, image, levels)
        core.gaussian_pyramid(backend, abs(weight), levels)
    core.collapse_pyramid(backend, bands)


def op_mix_prototype(image: Any, method: str, params: Params) -> None:
    """Run the op mix through the prototype's functions, the same calls as the product's.

    Args:
        image: The frame (NumPy or CuPy).
        method: ``"c3"`` or ``"ancuti2018"``.
        params: The parameters.
    """
    shape = image.shape
    backend = prototype_backend_of(image)  # the prototype's own namespace, not clearwater.core's
    if method == "c3":
        ycbcr = proto.rgb_to_ycbcr(image)
        mask = dark_mask(image, params)
        proto._gaussian(mask, proto.spatial_sigma(shape, params.c3_mask_smooth_fraction))
        sigma = proto.spatial_sigma(shape, params.c3_kernel_fraction)
        proto._gaussian(ycbcr[..., 1], sigma)
        proto._gaussian(ycbcr[..., 2], sigma)
    proto._channel_means(image)
    high_pass = proto.high_pass_of(image, params)
    bounds = [params.normalisation_low, params.normalisation_high]
    backend.xp.percentile(high_pass, bounds, method="linear")  # the prototype's namespace
    levels = proto.pyramid_levels(shape, params.pyramid_min_level_size)
    bands: list[Any] = []
    for _ in range(2):
        luma = proto.luminance(image)
        laplace_sigma = proto.spatial_sigma(shape, params.laplacian_fraction)
        weight = backend.ndimage.laplace(proto._gaussian(luma, laplace_sigma), mode="reflect")
        lab = proto.srgb_to_lab(image)
        proto._lab_mean(lab).tolist()
        proto._gaussian(lab, proto.spatial_sigma(shape, params.saliency_blur_fraction))
        bands = proto.laplacian_pyramid(image, levels)
        proto.gaussian_pyramid(abs(weight), levels)
    proto.collapse_pyramid(bands)


def gpu_snapshot() -> dict[str, str]:
    """Return one ``nvidia-smi`` reading of the fields in ``_GPU_QUERY`` (empty on failure)."""
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--query-gpu={_GPU_QUERY}", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            check=False,
            timeout=20,
        )
    except (OSError, subprocess.TimeoutExpired):
        return {}
    values = [value.strip() for value in result.stdout.strip().splitlines()[0].split(",")]
    return dict(zip(_GPU_QUERY.split(","), values, strict=False))


def busy_processes(threshold: float = 25.0, interval: float = 1.0) -> list[dict[str, Any]]:
    """Return the processes above ``threshold`` percent of one logical CPU over ``interval`` s.

    Args:
        threshold: The percentage of one logical CPU.
        interval: The measuring window in seconds.

    Returns:
        Name, pid and CPU percent of each busy process, busiest first.
    """
    processes = list(psutil.process_iter(["name", "pid"]))
    for process in processes:
        with contextlib.suppress(psutil.Error):
            process.cpu_percent(None)
    time.sleep(interval)
    busy = []
    for process in processes:
        try:
            percent = process.cpu_percent(None)
        except psutil.Error:
            continue
        if percent >= threshold and process.pid != 0:
            busy.append({"name": process.info["name"], "pid": process.pid, "cpu": percent})
    return sorted(busy, key=lambda entry: -float(entry["cpu"]))


def conditions(moment: str) -> dict[str, Any]:
    """Record the machine's conditions at ``moment`` (GPU reading and busy processes).

    Args:
        moment: A label such as ``"before"``.

    Returns:
        The record.
    """
    return {
        "moment": moment,
        "utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "gpu": gpu_snapshot(),
        "busy_processes": busy_processes(),
        "cpu_total_percent": psutil.cpu_percent(interval=0.5),
    }


def timed(run: Callable[[], None], synchronize: Callable[[], None]) -> float:
    """Return the seconds ``run`` takes, synchronised with the device on both sides.

    Args:
        run: The work.
        synchronize: Waits for the device (a no-op on the CPU).

    Returns:
        The elapsed time.
    """
    synchronize()
    start = time.perf_counter()
    run()
    synchronize()
    return time.perf_counter() - start


def summarise(samples: Sequence[float]) -> dict[str, float]:
    """Return the count, median, 10th and 90th percentile, minimum, maximum and mean.

    Args:
        samples: The timings in seconds, at least one.

    Returns:
        The summary.
    """
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


def run_device(
    clip: ClipInfo,
    backend: CoreBackend,
    frames: Sequence[int],
    sample_every: int,
    record: dict[str, Any],
) -> dict[str, list[float]]:
    """Time the op mix on every wanted frame on one device, both implementations, both methods.

    The order of the implementations alternates from frame to frame so that a drift in clocks
    or load is shared between them. The first frame is a warm-up and is not kept.

    Args:
        clip: The clip.
        backend: The device's backend.
        frames: The frame indices.
        sample_every: Record the conditions every this many frames.
        record: The run record; ``"during"`` readings are appended to it.

    Returns:
        The timings in seconds by ``"<implementation> <method>"`` and ``"upload"``.
    """
    params = Params()
    synchronize: Callable[[], None] = (
        importlib.import_module("cupy").cuda.Device().synchronize
        if backend.name == "cupy"
        else lambda: None
    )
    times: dict[str, list[float]] = {"upload": []}
    for done, (index, host_frame) in enumerate(decode(clip, frames)):
        synchronize()
        start = time.perf_counter()
        image = backend.asarray(host_frame)
        synchronize()
        upload = time.perf_counter() - start
        order = IMPLEMENTATIONS if index % 2 == 0 else IMPLEMENTATIONS[::-1]
        frame_times: dict[str, float] = {}
        for implementation in order:
            for method in METHODS:
                if implementation == "product":
                    work = lambda m=method, a=image: op_mix_product(backend, a, m, params)  # noqa: E731
                else:
                    work = lambda m=method, a=image: op_mix_prototype(a, m, params)  # noqa: E731
                frame_times[f"{implementation} {method}"] = timed(work, synchronize)
        if done > 0:
            times["upload"].append(upload)
            for key, value in frame_times.items():
                times.setdefault(key, []).append(value)
        if sample_every and done % sample_every == 0:
            record["during"].append(
                {"device": backend.device, "frame": index, **conditions("during")}
            )
        print(f"{backend.device} frame {index} ({done + 1}/{len(frames)})", flush=True)
    return times


def main(argv: Sequence[str] | None = None) -> int:
    """Run the speed row and write its record under the working folder.

    Args:
        argv: The command-line arguments (``sys.argv[1:]`` when None).

    Returns:
        The exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("clip", help="footage stem, for example GX011627")
    parser.add_argument("--config", type=Path, help="local configuration file to read")
    parser.add_argument("--gpu-frames", type=int, help="only the first N frames on the GPU")
    parser.add_argument("--cpu-frames", type=int, default=10, help="frames on the CPU (0: none)")
    parser.add_argument("--sample-every", type=int, default=100, help="conditions every N frames")
    args = parser.parse_args(argv)
    config = load_local_config(args.config)
    clip = probe_clip(find_footage_file(args.clip, config.footage_path))
    out_dir = config.working_path / OUTPUT_SUBDIR
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    record: dict[str, Any] = {
        "clip": clip.path.name,
        "size": [clip.height, clip.width],
        "frames_in_clip": clip.frames,
        "before": conditions("before"),
        "during": [],
    }
    results: dict[str, Any] = {}
    gpu = CupyBackend()
    gpu_count = clip.frames if args.gpu_frames is None else min(args.gpu_frames, clip.frames)
    gpu_times = run_device(clip, gpu, range(gpu_count), args.sample_every, record)
    results["gpu"] = {key: summarise(value) for key, value in gpu_times.items() if value}
    if args.cpu_frames > 0:
        step = clip.frames / args.cpu_frames
        cpu_frames = sorted(
            {min(clip.frames - 1, int(i * step)) for i in range(args.cpu_frames + 1)}
        )
        cpu_times = run_device(clip, NumpyBackend(), cpu_frames, 1, record)
        results["cpu"] = {key: summarise(value) for key, value in cpu_times.items() if value}
        record["cpu_frames"] = cpu_frames
    record["after"] = conditions("after")
    record["results"] = results
    path = out_dir / f"core-speed-{clip.path.stem}-{stamp}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    for device, rows in results.items():
        for key, row in rows.items():
            print(
                f"ROW {device} {key}: median {row['median']:.4f} s, p10 {row['p10']:.4f}, "
                f"p90 {row['p90']:.4f}, n {row['n']}"
            )
    print(f"RECORD {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
