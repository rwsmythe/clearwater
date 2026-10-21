"""WP3.1 speed row: the IF-2 operations of the c3 and ancuti2018 paths, product vs prototype.

WP3.1 has no correction method, so the whole-core figure waits for WP3.4 (brief ruling 4).
This instrument times, per decoded frame, the "op mix": every call of a prototype array
operation that one ``pipeline.correct()`` call makes with the default parameters, made through
IF-2 and the ``clearwater.core`` helpers by the product and through the read-only prototype's
own functions, on the GPU and on the CPU (``tests/test_core_speed.py`` counts the calls of
both, and the prototype path's host reads, against a real ``correct()``):

- c3 compensation: ``rgb_to_ycbcr``; the bright-pixel mask blur (``c3_mask_smooth_fraction``);
  the Cb and Cr blurs at the c3 kernel sigma (``c3_kernel_fraction``, AD-8); the channel means
  of its record;
- ancuti2018 compensation: the channel means; the gain-cap mean of ``(1 - I_c) * I_g`` per
  compensated channel (red; blue too when ``blue_compensation`` is on);
- both methods: the two channel-mean reads of the mean added; the white-balance channel means;
  the sharpening blur and the N{} percentiles of its high-pass; per fusion input (two), the
  luma, its blur at ``laplacian_fraction`` and its Laplacian, the Lab image, its means and its
  blur at ``saliency_blur_fraction``, the saturation weight's luma, the Laplacian pyramid of
  the input and the Gaussian pyramid of a weight map; one pyramid collapse.

Host reads (device-to-host transfers, each a synchronisation on the GPU) per frame and method:
the prototype path makes the reads ``correct()`` makes -- four channel-mean triples, the
gain-cap mean of each compensated channel (ancuti2018), and the two N{} bounds -- and keeps the
saliency Lab means on the device. The product path reads what its helpers return to the host:
the same channel means and gain-cap means, plus the two Lab-mean triples (``channel_means``
returns Python floats, a ruled sync point, R0-2), while its ``percentile`` stays on the device
(IF-2 returns an array; WP3.3 reads the bounds when it forms N{}).

Not timed: the per-pixel arithmetic between these calls (gains, clipping, the weight sums),
which belongs to WP3.2-3.4, except the maps the calls take as input (the c3 mask, the
high-pass, the gain-cap shape, the weight map's absolute value), which are timed with them;
and the prototype's input validation (``_check_image`` reads the minimum and
maximum of the image at every step). Every operation runs on the decoded frame itself, not on
the intermediate images of a real correction (the same sizes, so the same work). The frame
upload is timed apart from the op mix.

Plan 4.3 / frame rule 7: an EXCLUSIVE run, one at a time, best effort on a shared laptop. GPU
clocks, temperature, utilisation and the processes using a CPU are recorded before, during
(every ``--sample-every`` frames) and after; a contaminated row is kept as spread. The GPU pass
covers the full clip; the CPU pass covers ``--cpu-frames`` frames spread evenly over the clip
(the WP1.2 Part B practice: a 4K CPU frame takes seconds per operation).

WP3.4 adds the whole-core row (``--whole``) and the memory re-check (``--memory``), written
under ``wp3.4/`` in the working folder:

- ``--whole``: per frame and method (both at the AD-8 defaults, the order alternating), the
  frame upload and the analysis-proxy upload (apart); ``analyze`` of every stage in order on
  the block-mean proxy (960 x 540 at 4K, the S3 rule of ``clearwater.gui.imaging``; built
  untimed), each stage given the frame's own raw earlier records; ``render`` at full size with
  that record; their sum, the core's share of a frame; and the prototype ``correct()`` on the
  same device frame (the gate's figure). The core's share is set against D106's interim figure
  (:data:`D106_SECONDS_PER_FRAME`) as minutes of processing per minute of footage. The render's
  per-call uploads (DR-40 b) are counted once per method and a three-value upload is timed.
- ``--memory``: on the GPU, a counting allocator in front of CuPy's default pool (the WP1.2A
  form) records the pool's used and reserved peaks, and a sampling thread the process RSS,
  while ``analyze`` (every stage, on the full frame and on its proxy) and ``render`` run at 4K
  and at 5.3K 16:9 (5312 x 2988, the 4K frame padded by reflection), both methods; each peak
  is set against ``memory_estimate_bytes`` (AD-1). The CPU ``render`` RSS is recorded too.

The GPU readings are those of the CuPy device's own ``nvidia-smi`` row, matched by PCI bus id
(DR-37 e). The footage is reached only through ``local_config.find_footage_file`` and read by
an FFmpeg decode to a pipe; nothing is written outside the working folder. Usage::

    uv run python tools/core_speed.py GX011627 [--cpu-frames 10] [--gpu-frames N]
    uv run python tools/core_speed.py GX011627 --whole [--memory] [--cpu-frames 10]
"""

from __future__ import annotations

import argparse
import contextlib
import functools
import importlib
import json
import math
import statistics
import subprocess
import sys
import threading
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
from clearwater.interfaces.image import ColorDescription, Image
from clearwater.interfaces.method import CorrectionMethod, Statistics
from clearwater.methods import available_methods
from local_config import find_footage_file, load_local_config
from prototype import pipeline as proto
from prototype.backend import of as prototype_backend_of
from prototype.params import Params

METHODS = ("c3", "ancuti2018")
IMPLEMENTATIONS = ("product", "prototype")
OUTPUT_SUBDIR = Path("wp3.1") / "speed"
WHOLE_SUBDIR = Path("wp3.4")
_GPU_QUERY = "clocks.sm,clocks.mem,temperature.gpu,utilization.gpu,memory.used,power.draw"
FPS = 30000 / 1001
"""The frame rate of the bar (the owner's GoPro footage, 29.97 fps)."""
D106_MINUTES_PER_MINUTE = 25.0
"""D106's interim figure: about 25 minutes of processing per minute of 4K footage."""
D106_SECONDS_PER_FRAME = D106_MINUTES_PER_MINUTE * 60.0 / (60.0 * FPS)
"""D106 as seconds per frame for the whole export at :data:`FPS` (about 0.834 s)."""
STATISTICS_SHORT_SIDE = 540
"""The analysis proxy's short side (the S3 rule; ``clearwater.gui.imaging``)."""
MEMORY_SIZES = ((2160, 3840), (2988, 5312))
"""The memory re-check's frame sizes: 4K and 5.3K 16:9."""
_COLOR = ColorDescription("bt709", "bt709", "bt709", "full", 8, False, None)
_MIB = 1024 * 1024


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
    try:
        stream = (json.loads(result.stdout).get("streams") or [])[0]
        return ClipInfo(
            path, int(stream["width"]), int(stream["height"]), int(stream["nb_read_packets"])
        )
    except (ValueError, LookupError, TypeError, AttributeError) as exc:  # DR-37 d
        raise SpeedError(f"ffprobe reports no usable video stream in {path.name}") from exc


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


def compensated_channels(params: Params) -> tuple[int, ...]:
    """Return the channels the Ancuti 2018 compensation evaluates a gain cap for.

    Red always, blue when ``blue_compensation`` is on (``pipeline.compensate_ancuti2018``).

    Args:
        params: Uses ``blue_compensation``.

    Returns:
        The channel indices.
    """
    return (0, 2) if params.blue_compensation else (0,)


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
        core.channel_means(backend, image)  # the compensation record
    else:
        core.channel_means(backend, image)  # the compensation means
        for index in compensated_channels(params):
            core.mean(backend, (1.0 - image[..., index]) * image[..., 1])  # the gain-cap mean
    core.channel_means(backend, image)  # the mean added: after ...
    core.channel_means(backend, image)  # ... and before
    core.channel_means(backend, image)  # the white-balance means
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
        core.luminance(backend, image)  # the saturation weight's own luma
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
    else:
        proto._channel_means(image)
        for index in compensated_channels(params):
            proto._cap_statistic((1.0 - image[..., index]) * image[..., 1])
    proto._mean_added(image, image)
    proto._channel_means(image)
    proto._high_pass_and_bounds(image, params)  # the blur, the percentiles and their read
    levels = proto.pyramid_levels(shape, params.pyramid_min_level_size)
    bands: list[Any] = []
    for _ in range(2):
        luma = proto.luminance(image)
        laplace_sigma = proto.spatial_sigma(shape, params.laplacian_fraction)
        weight = backend.ndimage.laplace(proto._gaussian(luma, laplace_sigma), mode="reflect")
        lab = proto.srgb_to_lab(image)
        proto._lab_mean(lab)  # kept on the device, as the saliency weight keeps it
        proto._gaussian(lab, proto.spatial_sigma(shape, params.saliency_blur_fraction))
        proto.luminance(image)
        bands = proto.laplacian_pyramid(image, levels)
        proto.gaussian_pyramid(abs(weight), levels)
    proto.collapse_pyramid(bands)


def pci_key(bus_id: str) -> tuple[int, ...] | None:
    """Return a PCI bus id as numbers, so CuPy's and ``nvidia-smi``'s spellings compare.

    CuPy writes ``0000:01:00.0`` and ``nvidia-smi`` ``00000000:01:00.0``: (domain, bus,
    device, function) in hexadecimal.

    Args:
        bus_id: The bus id text.

    Returns:
        The four numbers, or None when the text is not a bus id.
    """
    try:
        domain, bus, rest = bus_id.strip().split(":")
        device, function = rest.split(".")
        return int(domain, 16), int(bus, 16), int(device, 16), int(function, 16)
    except ValueError:
        return None


def gpu_snapshot(bus_id: str | None = None) -> dict[str, str]:
    """Return one ``nvidia-smi`` reading of the fields in ``_GPU_QUERY``.

    With ``bus_id`` (the CuPy device's PCI bus id) the reading is that device's row (DR-37 e);
    without it, the first row (the WP3.1 op-mix row). When ``nvidia-smi`` cannot run, exits
    non-zero, prints nothing or has no row for ``bus_id``, the run goes on and the reading is
    ``{"unavailable": <why>}``, so the record says that the telemetry is missing.
    """
    query = _GPU_QUERY if bus_id is None else f"pci.bus_id,{_GPU_QUERY}"
    try:
        result = subprocess.run(
            ["nvidia-smi", f"--query-gpu={query}", "--format=csv,noheader,nounits"],
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
    rows = [[value.strip() for value in line.split(",")] for line in lines]
    if bus_id is None:
        return dict(zip(_GPU_QUERY.split(","), rows[0], strict=False))
    wanted = pci_key(bus_id)
    for row in rows:
        if wanted is not None and pci_key(row[0]) == wanted:
            return dict(zip(query.split(","), row, strict=False))
    return {"unavailable": f"nvidia-smi has no row for PCI bus {bus_id}"}


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


def conditions(moment: str, bus_id: str | None = None) -> dict[str, Any]:
    """Record the machine's conditions at ``moment`` (GPU reading and busy processes).

    Args:
        moment: A label such as ``"before"``.
        bus_id: The CuPy device's PCI bus id, to read that device's row (DR-37 e).

    Returns:
        The record.
    """
    return {
        "moment": moment,
        "utc": datetime.now(UTC).isoformat(timespec="seconds"),
        "gpu": gpu_snapshot(bus_id),
        "busy_processes": busy_processes(),
        "cpu_total_percent": psutil.cpu_percent(interval=0.5),
    }


def timed(run: Callable[[], object], synchronize: Callable[[], None]) -> float:
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


# -- WP3.4: the whole-core row and the memory re-check ------------------------------------------


def proxy_of(frame: NDArray[np.float32]) -> NDArray[np.float32]:
    """Return the analysis proxy: the block mean by ``max(1, short side // 540)`` (S3 rule).

    The arithmetic of ``clearwater.gui.imaging.downscale`` and ``statistics_factor`` (not
    imported: that module needs Qt): 960 x 540 for a 4K frame.

    Args:
        frame: float32 ``(H, W, 3)`` host frame.

    Returns:
        The proxy, float32.
    """
    height, width = frame.shape[0], frame.shape[1]
    k = max(1, min(height, width) // STATISTICS_SHORT_SIDE)
    if k == 1:
        return frame
    rows = np.arange(0, height, k)
    cols = np.arange(0, width, k)
    summed = np.add.reduceat(frame, rows, axis=0, dtype=np.float64)
    summed = np.add.reduceat(summed, cols, axis=1)
    counts = (
        np.minimum(k, height - rows).astype(np.float64)[:, None, None]
        * np.minimum(k, width - cols).astype(np.float64)[None, :, None]
    )
    return np.asarray(summed / counts, dtype=np.float32)


def as_image(backend: CoreBackend, pixels: Any) -> Image:
    """Wrap an array of ``backend`` as an IF-1 image on its device."""
    return Image(pixels=pixels, device=backend.device, color=_COLOR, orientation_applied=True)


def analyze_timed(
    method: CorrectionMethod, image: Image, synchronize: Callable[[], None]
) -> tuple[dict[str, Statistics], dict[str, float]]:
    """Run ``analyze`` of every stage in order (the frame's own raw earlier records), timed.

    Args:
        method: The method, at its defaults.
        image: The image to measure (the proxy).
        synchronize: Waits for the device.

    Returns:
        The records by stage, and the seconds of each stage.
    """
    records: dict[str, Statistics] = {}
    seconds: dict[str, float] = {}
    for stage in method.stages:
        synchronize()
        start = time.perf_counter()
        records[stage.name] = method.analyze(stage.name, image, {}, dict(records))
        synchronize()
        seconds[stage.name] = time.perf_counter() - start
    return records, seconds


def minutes_per_minute(seconds_per_frame: float, fps: float = FPS) -> float:
    """Return the minutes of processing per minute of footage at ``fps`` (D106's unit).

    Args:
        seconds_per_frame: The processing time of one frame.
        fps: The footage frame rate.

    Returns:
        ``seconds_per_frame * fps``: one minute holds ``60 * fps`` frames.
    """
    return seconds_per_frame * fps


def count_render_uploads(method: CorrectionMethod, image: Image, records: Any) -> int:
    """Count the ``asarray`` calls (host-to-device uploads) one ``render`` makes (DR-40 b).

    The backend instrumented is the one the method renders on, ``backend_for(image.device)``.
    Constants cached by ``CoreBackend.constant`` are uploaded once per backend and are not
    counted.

    Args:
        method: The method, at its defaults.
        image: The image.
        records: The statistics of every stage.

    Returns:
        The number of uploads.
    """
    backend = core.backend_for(image.device)
    original = backend.asarray
    calls = [0]

    def counting(*args: Any, **kwargs: Any) -> Any:
        calls[0] += 1
        return original(*args, **kwargs)

    setattr(backend, "asarray", counting)  # noqa: B010 -- an instance attribute, removed below
    try:
        method.render(image, {}, records)
    finally:
        delattr(backend, "asarray")
    return calls[0]


def time_small_upload(
    backend: CoreBackend, synchronize: Callable[[], None], repeats: int = 200
) -> dict[str, float]:
    """Time the upload of three float32 values (the white-balance gains' size), DR-40 b.

    Args:
        backend: The backend.
        synchronize: Waits for the device.
        repeats: The number of uploads.

    Returns:
        The summary of the timings in seconds.
    """
    values = (1.0, 1.0, 1.0)
    return summarise([timed(lambda: backend.asarray(values), synchronize) for _ in range(repeats)])


def synchronizer(backend: CoreBackend) -> Callable[[], None]:
    """Return a function that waits for the backend's device (a no-op on the CPU)."""
    if backend.name == "cupy":
        device: Callable[[], None] = importlib.import_module("cupy").cuda.Device().synchronize
        return device
    return lambda: None


def run_whole(
    clip: ClipInfo,
    backend: CoreBackend,
    frames: Sequence[int],
    sample_every: int,
    record: dict[str, Any],
    bus_id: str | None,
) -> dict[str, list[float]]:
    """Time the whole core per frame on one device: analyze, render, and prototype correct.

    Both methods at the AD-8 defaults; the method order alternates from frame to frame and the
    product / prototype order every two frames, so a drift in clocks or load is shared. The
    first frame is a warm-up and is not kept; on it the render's uploads are counted.

    Args:
        clip: The clip.
        backend: The device's backend.
        frames: The frame indices.
        sample_every: Record the conditions every this many frames.
        record: The run record; ``"during"`` readings and the upload counts are added to it.
        bus_id: The CuPy device's PCI bus id (None on a machine without one).

    Returns:
        The timings in seconds by ``"<method> <part>"``, ``"upload"`` and ``"proxy upload"``.
    """
    methods = available_methods()
    synchronize = synchronizer(backend)
    times: dict[str, list[float]] = {"upload": [], "proxy upload": []}
    for done, (index, host_frame) in enumerate(decode(clip, frames)):
        proxy_host = proxy_of(host_frame)
        synchronize()
        start = time.perf_counter()
        frame = backend.asarray(host_frame)
        synchronize()
        upload = time.perf_counter() - start
        start = time.perf_counter()
        proxy = backend.asarray(proxy_host)
        synchronize()
        proxy_upload = time.perf_counter() - start
        full_image, proxy_image = as_image(backend, frame), as_image(backend, proxy)
        frame_times: dict[str, float] = {}
        method_order = METHODS if index % 2 == 0 else METHODS[::-1]
        parts = ("product", "prototype") if (index // 2) % 2 == 0 else ("prototype", "product")
        for method_id in method_order:
            method = methods[method_id]
            for part in parts:
                if part == "prototype":
                    params = Params(method="c3" if method_id == "c3" else "ancuti2018")
                    frame_times[f"{method_id} prototype correct"] = timed(
                        functools.partial(proto.correct, frame, params), synchronize
                    )
                    continue
                records, stage_seconds = analyze_timed(method, proxy_image, synchronize)
                render_seconds = timed(
                    functools.partial(method.render, full_image, {}, records), synchronize
                )
                for stage, seconds in stage_seconds.items():
                    frame_times[f"{method_id} analyze {stage}"] = seconds
                analyze_seconds = sum(stage_seconds.values())
                frame_times[f"{method_id} analyze"] = analyze_seconds
                frame_times[f"{method_id} render"] = render_seconds
                frame_times[f"{method_id} core"] = analyze_seconds + render_seconds
                if done == 0:
                    uploads = record.setdefault("render_uploads", {}).setdefault(backend.device, {})
                    uploads[method_id] = count_render_uploads(method, full_image, records)
        if done > 0:
            times["upload"].append(upload)
            times["proxy upload"].append(proxy_upload)
            for key, value in frame_times.items():
                times.setdefault(key, []).append(value)
        if sample_every and done % sample_every == 0:
            record["during"].append(
                {"device": backend.device, "frame": index, **conditions("during", bus_id)}
            )
        print(f"{backend.device} frame {index} ({done + 1}/{len(frames)})", flush=True)
    record.setdefault("three_value_upload", {})[backend.device] = time_small_upload(
        backend, synchronize
    )
    return times


class PoolTracker:
    """The high-water marks of CuPy's default pool, through a counting allocator (WP1.2A).

    Attributes:
        peak_used: The most bytes the pool's arrays held at once.
        peak_reserved: The most bytes the pool held from the driver at once.
    """

    def __init__(self, cupy: Any) -> None:
        """Empty the pool's cache and install the counting allocator in front of it.

        Args:
            cupy: The ``cupy`` module.
        """
        self._cupy = cupy
        self._pool = cupy.get_default_memory_pool()
        self._pool.free_all_blocks()
        self.peak_used = int(self._pool.used_bytes())
        self.peak_reserved = int(self._pool.total_bytes())
        cupy.cuda.set_allocator(self._malloc)

    def _malloc(self, size: int) -> Any:
        """Allocate from the pool and update both high-water marks."""
        memory = self._pool.malloc(size)
        self.peak_used = max(self.peak_used, int(self._pool.used_bytes()))
        self.peak_reserved = max(self.peak_reserved, int(self._pool.total_bytes()))
        return memory

    def close(self) -> None:
        """Hand allocation back to the pool directly."""
        self._cupy.cuda.set_allocator(self._pool.malloc)


class RssSampler:
    """The peak resident set size of this process, sampled by a thread."""

    def __init__(self, interval: float = 0.005) -> None:
        """Start sampling every ``interval`` seconds.

        Args:
            interval: The sampling interval.
        """
        self._process = psutil.Process()
        self.baseline = int(self._process.memory_info().rss)
        self.peak = self.baseline
        self._interval = interval
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        """Sample until stopped."""
        while not self._stop.is_set():
            self.peak = max(self.peak, int(self._process.memory_info().rss))
            self._stop.wait(self._interval)

    def stop(self) -> int:
        """Stop sampling and return the peak above the baseline, in bytes."""
        self._stop.set()
        self._thread.join()
        self.peak = max(self.peak, int(self._process.memory_info().rss))
        return self.peak - self.baseline


def fit_frame(frame: NDArray[np.float32], height: int, width: int) -> NDArray[np.float32]:
    """Return ``frame`` cropped or padded by reflection to ``height`` x ``width``.

    Args:
        frame: The host frame.
        height: The wanted height.
        width: The wanted width.

    Returns:
        The frame at the wanted size, float32, contiguous.
    """
    cropped = frame[:height, :width]
    pad = ((0, height - cropped.shape[0]), (0, width - cropped.shape[1]), (0, 0))
    return np.ascontiguousarray(np.pad(cropped, pad, mode="reflect"), dtype=np.float32)


def memory_leg(host_frame: NDArray[np.float32], gpu: CoreBackend) -> list[dict[str, Any]]:
    """Measure the pool and RSS peaks of ``analyze`` and ``render`` against the estimate.

    Per size of :data:`MEMORY_SIZES` and method: ``analyze`` of every stage on the proxy and on
    the full frame, and ``render`` of the full frame from the proxy's records, each on a pool
    emptied first, the frame's upload included; then the CPU ``render``'s RSS.

    Args:
        host_frame: A decoded 4K frame.
        gpu: The CuPy backend.

    Returns:
        One row per size, method, device and operation.
    """
    cupy = importlib.import_module("cupy")
    synchronize = synchronizer(gpu)
    methods = available_methods()
    rows: list[dict[str, Any]] = []
    for height, width in MEMORY_SIZES:
        frame = fit_frame(host_frame, height, width)
        proxy = proxy_of(frame)
        for method_id in METHODS:
            method = methods[method_id]
            estimate = core.memory_estimate_bytes(height, width, method_id)
            records, _ = analyze_timed(method, as_image(gpu, gpu.asarray(proxy)), synchronize)
            for operation in ("analyze proxy", "analyze full", "render"):
                synchronize()
                tracker = PoolTracker(cupy)
                sampler = RssSampler()
                try:  # the upload of the measured image is inside the measurement
                    if operation == "render":
                        method.render(as_image(gpu, gpu.asarray(frame)), {}, records)
                    else:
                        source = proxy if operation == "analyze proxy" else frame
                        analyze_timed(method, as_image(gpu, gpu.asarray(source)), synchronize)
                    synchronize()
                finally:
                    rss = sampler.stop()
                    tracker.close()
                rows.append(
                    {
                        "size": [height, width],
                        "method": method_id,
                        "device": gpu.device,
                        "operation": operation,
                        "pool_peak_used_mib": tracker.peak_used / _MIB,
                        "pool_peak_reserved_mib": tracker.peak_reserved / _MIB,
                        "rss_peak_above_baseline_mib": rss / _MIB,
                        "estimate_mib": estimate / _MIB,
                        "reserved_over_estimate": tracker.peak_reserved / estimate,
                        "exceeds_estimate": tracker.peak_reserved > estimate,
                    }
                )
                print(f"MEMORY {height}x{width} {method_id} {operation} done", flush=True)
            cpu = core.backend_for("cpu")
            sampler = RssSampler()
            try:
                method.render(as_image(cpu, cpu.asarray(frame)), {}, records)
            finally:
                rss = sampler.stop()
            rows.append(
                {
                    "size": [height, width],
                    "method": method_id,
                    "device": "cpu",
                    "operation": "render",
                    "rss_peak_above_baseline_mib": rss / _MIB,
                    "estimate_mib": estimate / _MIB,
                }
            )
    cupy.get_default_memory_pool().free_all_blocks()
    return rows


def whole_main(args: argparse.Namespace, clip: ClipInfo, working_path: Path) -> int:
    """Run the ``--whole`` and ``--memory`` legs and write their record.

    Args:
        args: The parsed arguments.
        clip: The clip.
        working_path: The working folder.

    Returns:
        The exit status.
    """
    out_dir = working_path / WHOLE_SUBDIR
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    cupy = importlib.import_module("cupy")
    index = int(cupy.cuda.runtime.getDevice())
    try:  # the methods render on the process's probed backend: time that one
        gpu = core.backend_for(f"cuda:{index}")
    except ValueError as exc:
        raise SpeedError(f"the GPU is not usable: {exc}") from exc
    bus_id = str(cupy.cuda.Device(index).pci_bus_id)
    record: dict[str, Any] = {
        "clip": clip.path.name,
        "size": [clip.height, clip.width],
        "frames_in_clip": clip.frames,
        "pci_bus_id": bus_id,
        "bar": {
            "d106_minutes_per_minute": D106_MINUTES_PER_MINUTE,
            "fps": FPS,
            "d106_seconds_per_frame": D106_SECONDS_PER_FRAME,
        },
        "before": conditions("before", bus_id),
        "during": [],
    }
    if args.memory:
        _, first = next(decode(clip, [0]))
        record["memory"] = memory_leg(first, gpu)
    if args.whole:
        results: dict[str, Any] = {}
        count = clip.frames if args.gpu_frames is None else min(args.gpu_frames, clip.frames)
        gpu_times = run_whole(clip, gpu, range(count), args.sample_every, record, bus_id)
        results["gpu"] = {key: summarise(value) for key, value in gpu_times.items() if value}
        if args.cpu_frames > 0:
            step = clip.frames / args.cpu_frames
            cpu_frames = sorted(
                {min(clip.frames - 1, int(i * step)) for i in range(args.cpu_frames + 1)}
            )
            cpu_times = run_whole(clip, core.backend_for("cpu"), cpu_frames, 1, record, bus_id)
            results["cpu"] = {key: summarise(value) for key, value in cpu_times.items() if value}
            record["cpu_frames"] = cpu_frames
        record["results"] = results
    record["after"] = conditions("after", bus_id)
    path = out_dir / f"core-whole-{clip.path.stem}-{stamp}.json"
    path.write_text(json.dumps(record, indent=2), encoding="utf-8")
    for row in record.get("memory", []):
        used = row.get("pool_peak_used_mib")
        print(
            f"MEMORY {row['size'][0]}x{row['size'][1]} {row['method']} {row['device']} "
            f"{row['operation']}: pool used {used if used is None else round(used)} MiB, "
            f"reserved {round(row.get('pool_peak_reserved_mib') or 0)} MiB, RSS +"
            f"{round(row['rss_peak_above_baseline_mib'])} MiB, estimate "
            f"{round(row['estimate_mib'])} MiB"
        )
    for device, rows in record.get("results", {}).items():
        for key, summary in rows.items():
            print(
                f"ROW {device} {key}: median {summary['median']:.4f} s, p10 "
                f"{summary['p10']:.4f}, p90 {summary['p90']:.4f}, n {summary['n']}"
            )
        for method_id in METHODS:
            core_row = rows.get(f"{method_id} core")
            if core_row is not None:
                print(
                    f"BAR {device} {method_id}: core median {core_row['median']:.4f} s/frame = "
                    f"{minutes_per_minute(core_row['median']):.2f} min/min; D106 "
                    f"{D106_SECONDS_PER_FRAME:.3f} s/frame (whole export)"
                )
    print(f"RECORD {path}")
    return 0


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
    parser.add_argument("--whole", action="store_true", help="the WP3.4 whole-core row")
    parser.add_argument("--memory", action="store_true", help="the WP3.4 memory re-check")
    args = parser.parse_args(argv)
    config = load_local_config(args.config)
    clip = probe_clip(find_footage_file(args.clip, config.footage_path))
    if args.whole or args.memory:
        return whole_main(args, clip, config.working_path)
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
