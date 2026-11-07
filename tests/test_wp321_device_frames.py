"""WP3.21 #2: frame conversions on the device, bit for bit the host's (Q-R2; ruling Q3; AD-29).

The decode's integer planes may be uploaded and converted on the GPU, and the sink may quantise a
real device array where it lies. Under AD-29 the conversions are IF-2 device extensions on the
GPU backend (``clearwater.core``), absent on the CPU backend; ``clearwater.io.video`` reaches them
only through its own ``runtime_checkable`` Protocol, :class:`DeviceFrameBackend`, by a backend
injected at construction (``device_backend=``). These tests pin: the device conversions equal the
host ones for every 8-bit and 10-bit code and on random, edge and tie values; the GPU backend
satisfies the Protocol with the same signatures and the CPU backend does not; ``None`` (the
default) or the CPU backend takes the base's host path; a device-frame decode yields the host
decode's frames on every WP2.3 sample; the sink writes the host's planes for a device frame and
still refuses a device label on host pixels (and a CuPy array labelled ``"cpu"`` or another
device); and DR-63's ``close`` / ``abort`` window.
"""

from __future__ import annotations

import inspect
from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import video_fidelity as vf
from clearwater.color import planes_to_rgb, rgb_to_planes
from clearwater.core.backend import CoreBackend, NumpyBackend, _probe_gpu
from clearwater.interfaces import SinkReport
from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource, VideoEncodeError, probe
from clearwater.io.video import decode as decode_module

SAMPLES = ("vid-hevc8-bt709-full", "vid-hevc10", "vid-vfr", "vid-rotated", "vid-truncated")
"""The WP2.3 video samples a device-frame decode is checked on (8-bit, 10-bit, VFR, rotated,
truncated)."""

EXTENSIONS = ("planes_to_rgb", "rgb_to_planes")
"""The IF-2 device extensions ``clearwater.io.video`` calls (AD-29)."""


def _gpu() -> Any:
    backend, reason = _probe_gpu()
    if backend is None:
        pytest.skip(reason)
    return backend


def _backend(kind: str) -> CoreBackend | None:
    """Return the backend a test parameter names: none, the CPU backend or the GPU backend."""
    if kind == "none":
        return None
    if kind == "cpu":
        return NumpyBackend()
    gpu: CoreBackend = _gpu()
    return gpu


BACKENDS = ["none", "cpu", pytest.param("gpu", marks=pytest.mark.gpu)]


def _bits(a: Any) -> np.ndarray:
    host = np.asarray(a.get() if not isinstance(a, np.ndarray) else a)
    return host.view(np.uint32)


def _edges(bit_depth: int) -> np.ndarray:
    """Float32 values at and around every code's tie, the clip limits, and out of range."""
    top = np.float32(2**bit_depth - 1)
    codes = np.arange(2**bit_depth, dtype=np.float32)
    ties = (codes + np.float32(0.5)) / top
    exact = codes / top
    near = np.concatenate(
        [np.nextafter(ties, np.float32(0)), ties, np.nextafter(ties, np.float32(2))]
    )
    extra = np.array([-1.0, -0.0, 0.0, 1.0, 1.5, np.inf, -np.inf], dtype=np.float32)
    return np.concatenate([exact, near, extra]).astype(np.float32)


# --- AD-29: the Protocol and the backends -------------------------------------------------------


@pytest.mark.gpu
def test_the_gpu_backend_satisfies_the_io_video_protocol_with_the_same_signatures() -> None:
    gpu = _gpu()
    protocol = decode_module.DeviceFrameBackend
    assert isinstance(gpu, protocol)
    for name in EXTENSIONS:
        assert inspect.signature(getattr(protocol, name)) == inspect.signature(
            getattr(type(gpu), name)
        ), name


def test_the_cpu_backend_has_no_device_extensions_and_does_not_satisfy_the_protocol() -> None:
    cpu = NumpyBackend()
    assert not any(hasattr(cpu, name) for name in EXTENSIONS)
    assert not isinstance(cpu, decode_module.DeviceFrameBackend)


# --- the conversions ------------------------------------------------------------------------------


@pytest.mark.gpu
@pytest.mark.parametrize("bit_depth", [8, 10])
def test_planes_to_rgb_on_the_device_equals_the_host_for_every_code(bit_depth: int) -> None:
    gpu = _gpu()
    dtype = np.uint8 if bit_depth == 8 else np.dtype("<u2")
    codes = np.arange(2**bit_depth, dtype=dtype)
    width = codes.size
    # Each plane holds every code once, shifted per plane so that R, G and B differ.
    planes = np.stack([np.roll(codes, shift) for shift in (0, 7, 101)]).reshape(3, 1, width)
    data = planes.tobytes()
    host = planes_to_rgb(data, width=width, height=1, bit_depth=bit_depth)
    device = gpu.planes_to_rgb(data, width=width, height=1, bit_depth=bit_depth)
    gpu.check_rgb(device)  # a float32 (H, W, 3) array of the GPU backend
    assert device.shape == host.shape and device.flags.c_contiguous
    assert np.array_equal(_bits(device), _bits(host))


@pytest.mark.gpu
@pytest.mark.parametrize("bit_depth", [8, 10])
@pytest.mark.parametrize("shape", [(37, 53), (2160, 3840)], ids=["odd", "4k"])
def test_planes_to_rgb_on_the_device_equals_the_host_on_random_planes(
    bit_depth: int, shape: tuple[int, int]
) -> None:
    gpu = _gpu()
    rng = np.random.default_rng(bit_depth * 1000 + shape[0])
    dtype = np.uint8 if bit_depth == 8 else np.dtype("<u2")
    planes = rng.integers(0, 2**bit_depth, size=(3, *shape), dtype=np.uint16).astype(dtype)
    data = bytearray(planes.tobytes())
    device = gpu.planes_to_rgb(data, width=shape[1], height=shape[0], bit_depth=bit_depth)
    host = planes_to_rgb(data, width=shape[1], height=shape[0], bit_depth=bit_depth)
    data[:] = bytes(len(data))  # the buffer is reused by the decode: the device copy is its own
    assert np.array_equal(_bits(device), _bits(host))


@pytest.mark.gpu
def test_planes_to_rgb_on_the_device_refuses_a_wrong_size_and_bit_depth() -> None:
    gpu = _gpu()
    with pytest.raises(ValueError, match="bytes"):
        gpu.planes_to_rgb(bytes(3 * 4 * 5 - 1), width=5, height=4, bit_depth=8)
    with pytest.raises(ValueError, match="bit depth"):
        gpu.planes_to_rgb(bytes(3 * 4 * 5), width=5, height=4, bit_depth=12)


@pytest.mark.gpu
@pytest.mark.parametrize("bit_depth", [8, 10])
def test_rgb_to_planes_on_the_device_equals_the_host(bit_depth: int) -> None:
    gpu = _gpu()
    edges = _edges(bit_depth)
    rng = np.random.default_rng(bit_depth)
    rand = (rng.random(3 * 4096, dtype=np.float32) * np.float32(1.2)) - np.float32(0.1)
    values = np.concatenate([edges, rand])
    values = np.concatenate([values, np.zeros((-values.size) % 3, np.float32)])
    image = values.reshape(1, -1, 3)
    host = rgb_to_planes(image, bit_depth=bit_depth)
    device = gpu.rgb_to_planes(gpu.asarray(image), bit_depth=bit_depth)
    assert isinstance(device, bytes) and device == host


@pytest.mark.gpu
def test_rgb_to_planes_on_the_device_refuses_a_nan_and_a_wrong_array() -> None:
    gpu = _gpu()
    cp = gpu.xp
    image = cp.zeros((4, 5, 3), dtype=cp.float32)
    image[2, 3, 1] = cp.nan
    with pytest.raises(ValueError, match="NaN"):
        gpu.rgb_to_planes(image, bit_depth=8)
    with pytest.raises(ValueError, match="float32"):
        gpu.rgb_to_planes(cp.zeros((4, 5, 3), dtype=cp.float64), bit_depth=8)
    with pytest.raises(TypeError, match="numpy"):
        gpu.rgb_to_planes(np.zeros((4, 5, 3), dtype=np.float32), bit_depth=8)


# --- the decode -----------------------------------------------------------------------------------


def test_device_frames_are_off_by_default() -> None:
    assert FFmpegVideoSource().device_backend is None
    assert FFmpegVideoSink()._device_backend is None


@pytest.mark.parametrize("kind", BACKENDS)
@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_software_decode_yields_host_frames(sample: Any, kind: str) -> None:
    source = FFmpegVideoSource(device_backend=_backend(kind))
    info = source.probe(sample("vid-hevc8-bt709-full"))
    frames = source.frames(info, hw_decode=False)
    try:
        frame = next(iter(frames))
    finally:
        frames.close()  # type: ignore[attr-defined]
    assert frame.device == "cpu" and isinstance(frame.pixels, np.ndarray)


@pytest.mark.usefixtures("ffmpeg_tools")
def test_a_cpu_backend_source_takes_the_base_host_path(sample: Any) -> None:
    path = sample("vid-hevc8-bt709-full")
    base, cpu = FFmpegVideoSource(), FFmpegVideoSource(device_backend=NumpyBackend())
    info = base.probe(path)
    expected = list(base.frames(info, hw_decode=True))
    got = list(cpu.frames(info, hw_decode=True))
    assert expected and len(got) == len(expected)
    for e, g in zip(expected, got, strict=True):
        assert g.device == "cpu" and isinstance(g.pixels, np.ndarray)
        assert g.pts_ticks == e.pts_ticks and np.array_equal(_bits(g.pixels), _bits(e.pixels))


@pytest.mark.gpu
@pytest.mark.parametrize("sample_id", SAMPLES)
def test_a_device_frame_decode_equals_the_host_decode(sample: Any, sample_id: str) -> None:
    gpu = _gpu()
    path = sample(sample_id)
    host_source, device_source = FFmpegVideoSource(), FFmpegVideoSource(device_backend=gpu)
    info = host_source.probe(path)
    host = list(host_source.frames(info, hw_decode=True))
    device = list(device_source.frames(info, hw_decode=True))
    assert host and len(device) == len(host)
    for h, d in zip(host, device, strict=True):
        assert h.device == "cpu" and d.device == gpu.device
        gpu.check_rgb(d.pixels)
        assert (d.pts_ticks, d.time_base, d.index, d.color) == (
            h.pts_ticks,
            h.time_base,
            h.index,
            h.color,
        )
        assert np.array_equal(_bits(d.pixels), _bits(h.pixels)), f"pts {h.pts_ticks}"


# --- the sink -------------------------------------------------------------------------------------


def _opened(
    source: Path, out: Path, device_backend: CoreBackend | None = None
) -> tuple[FFmpegVideoSink, list[Any]]:
    info = probe(source)
    frames = list(vf.decode_frames(source, info))
    out.write_bytes(b"")
    sink = FFmpegVideoSink(device_backend=device_backend)
    sink.open(info, out, encoder="libx265", quality="draft", bit_depth=8, provenance=None)
    return sink, frames


@pytest.mark.gpu
def test_the_sink_writes_a_device_frame_as_the_host_planes(sample: Any, tmp_path: Path) -> None:
    gpu = _gpu()
    host_sink, frames = _opened(sample("vid-vfr"), tmp_path / "host.mp4")
    device_sink, _ = _opened(sample("vid-vfr"), tmp_path / "device.mp4", gpu)
    try:
        for frame in frames[:3]:
            on_device = replace(frame, pixels=gpu.asarray(frame.pixels), device=gpu.device)
            assert device_sink._payload(on_device) == host_sink._payload(frame)
    finally:
        host_sink.abort()
        device_sink.abort()


@pytest.mark.gpu
def test_a_device_frame_export_closes_and_verifies(sample: Any, tmp_path: Path) -> None:
    gpu = _gpu()
    sink, frames = _opened(sample("vid-vfr"), tmp_path / "out.mp4", gpu)
    try:
        for frame in frames:
            sink.write(replace(frame, pixels=gpu.asarray(frame.pixels), device=gpu.device))
        report = sink.close()
    except BaseException:
        sink.abort()
        raise
    assert report.frames_written == len(frames)


@pytest.mark.gpu
@pytest.mark.parametrize("label", ["cpu", "cuda:7"], ids=["labelled-cpu", "another-device"])
def test_the_sink_refuses_a_device_array_under_a_wrong_label(
    sample: Any, tmp_path: Path, label: str
) -> None:
    gpu = _gpu()
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out, gpu)
    with pytest.raises(VideoEncodeError) as caught:
        sink.write(replace(frames[0], pixels=gpu.asarray(frames[0].pixels), device=label))
    assert caught.value.kind == "frame"
    assert not out.exists()
    sink.abort()


@pytest.mark.gpu
def test_the_sink_refuses_a_float64_device_frame(sample: Any, tmp_path: Path) -> None:
    gpu = _gpu()
    sink, frames = _opened(sample("vid-vfr"), tmp_path / "out.mp4", gpu)
    pixels = gpu.xp.asarray(frames[0].pixels, dtype=gpu.xp.float64)
    with pytest.raises(VideoEncodeError, match="float32") as caught:
        sink.write(replace(frames[0], pixels=pixels, device=gpu.device))
    assert caught.value.kind == "frame"
    sink.abort()


@pytest.mark.parametrize("kind", BACKENDS)
@pytest.mark.usefixtures("ffmpeg_tools")
def test_the_sink_still_refuses_a_device_label_on_host_pixels(
    sample: Any, tmp_path: Path, kind: str
) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out, _backend(kind))
    with pytest.raises(VideoEncodeError, match="to_host") as caught:
        sink.write(replace(frames[0], device="cuda:0"))
    assert caught.value.kind == "frame"
    assert not out.exists()
    sink.abort()


@pytest.mark.gpu
@pytest.mark.parametrize("kind", ["none", "cpu"])
def test_a_sink_without_device_extensions_refuses_a_device_frame(
    sample: Any, tmp_path: Path, kind: str
) -> None:
    gpu = _gpu()
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out, _backend(kind))
    with pytest.raises(VideoEncodeError, match="to_host") as caught:
        sink.write(replace(frames[0], pixels=gpu.asarray(frames[0].pixels), device=gpu.device))
    assert caught.value.kind == "frame"
    assert not out.exists()
    sink.abort()


# --- DR-63: an abort inside close's window ----------------------------------------------------


@pytest.mark.usefixtures("ffmpeg_tools")
def test_an_abort_during_close_survives_it(
    sample: Any, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)
    for frame in frames:
        sink.write(frame)
    real_finish = sink._finish
    cleanups: list[int] = []
    real_cleanup = sink._cleanup

    def finish() -> SinkReport:
        report = real_finish()
        sink.abort()  # another thread's abort, landing after the last check inside close
        return report

    def cleanup() -> None:
        cleanups.append(1)
        real_cleanup()

    monkeypatch.setattr(sink, "_finish", finish)
    monkeypatch.setattr(sink, "_cleanup", cleanup)
    sink.close()
    assert sink._phase == "aborted", "close overwrote the abort that landed in its window"
    assert not out.exists() and cleanups == [1]
    sink.abort()  # tries the cleanup again: the phase is not "closed"
    assert cleanups == [1, 1]


@pytest.mark.usefixtures("ffmpeg_tools")
def test_an_abort_after_a_clean_close_does_nothing(sample: Any, tmp_path: Path) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)
    for frame in frames:
        sink.write(frame)
    sink.close()
    assert sink._phase == "closed"
    sink.abort()
    assert out.exists()
