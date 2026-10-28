"""WP3.21 #2: frame conversions on the device, bit for bit the host's (Q-R2; ruling Q3 tier 1).

The decode's integer planes may be uploaded and converted on the GPU (an opt-in of
``FFmpegVideoSource``, off by default), and the sink may quantise a real device array where it
lies. These tests pin: the device conversions equal the host ones for every 8-bit and 10-bit code
and on random, edge and tie values; a device-frame decode yields the host decode's frames on
every WP2.3 sample; the default and every ``hw_decode=False`` call stay on the host; the sink
writes the host's planes for a device frame and still refuses a device label on host pixels
(and a CuPy array labelled ``"cpu"`` or another device); and DR-63's ``close`` / ``abort`` window.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pytest

import video_fidelity as vf
from clearwater.color import ColorError, planes_to_rgb, rgb_to_planes
from clearwater.core.backend import _probe_gpu
from clearwater.interfaces import SinkReport
from clearwater.io.video import FFmpegVideoSink, FFmpegVideoSource, VideoEncodeError, probe

SAMPLES = ("vid-hevc8-bt709-full", "vid-hevc10", "vid-vfr", "vid-rotated", "vid-truncated")
"""The WP2.3 video samples a device-frame decode is checked on (8-bit, 10-bit, VFR, rotated,
truncated)."""


def _cupy() -> Any:
    backend, reason = _probe_gpu()
    if backend is None:
        pytest.skip(reason)
    return backend.xp


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


# --- the conversions ------------------------------------------------------------------------------


@pytest.mark.gpu
@pytest.mark.parametrize("bit_depth", [8, 10])
def test_planes_to_rgb_on_the_device_equals_the_host_for_every_code(bit_depth: int) -> None:
    cp = _cupy()
    dtype = np.uint8 if bit_depth == 8 else np.dtype("<u2")
    codes = np.arange(2**bit_depth, dtype=dtype)
    width = codes.size
    # Each plane holds every code once, shifted per plane so that R, G and B differ.
    planes = np.stack([np.roll(codes, shift) for shift in (0, 7, 101)]).reshape(3, 1, width)
    data = planes.tobytes()
    host = planes_to_rgb(data, width=width, height=1, bit_depth=bit_depth)
    device = planes_to_rgb(data, width=width, height=1, bit_depth=bit_depth, xp=cp)
    assert isinstance(device, cp.ndarray) and device.dtype == np.float32
    assert device.shape == host.shape and device.flags.c_contiguous
    assert np.array_equal(_bits(device), _bits(host))


@pytest.mark.gpu
@pytest.mark.parametrize("bit_depth", [8, 10])
@pytest.mark.parametrize("shape", [(37, 53), (2160, 3840)], ids=["odd", "4k"])
def test_planes_to_rgb_on_the_device_equals_the_host_on_random_planes(
    bit_depth: int, shape: tuple[int, int]
) -> None:
    cp = _cupy()
    rng = np.random.default_rng(bit_depth * 1000 + shape[0])
    dtype = np.uint8 if bit_depth == 8 else np.dtype("<u2")
    planes = rng.integers(0, 2**bit_depth, size=(3, *shape), dtype=np.uint16).astype(dtype)
    data = bytearray(planes.tobytes())
    device = planes_to_rgb(data, width=shape[1], height=shape[0], bit_depth=bit_depth, xp=cp)
    host = planes_to_rgb(data, width=shape[1], height=shape[0], bit_depth=bit_depth)
    data[:] = bytes(len(data))  # the buffer is reused by the decode: the device copy is its own
    assert np.array_equal(_bits(device), _bits(host))


@pytest.mark.gpu
@pytest.mark.parametrize("bit_depth", [8, 10])
def test_rgb_to_planes_on_the_device_equals_the_host(bit_depth: int) -> None:
    cp = _cupy()
    edges = _edges(bit_depth)
    rng = np.random.default_rng(bit_depth)
    rand = (rng.random(3 * 4096, dtype=np.float32) * np.float32(1.2)) - np.float32(0.1)
    values = np.concatenate([edges, rand])
    values = np.concatenate([values, np.zeros((-values.size) % 3, np.float32)])
    image = values.reshape(1, -1, 3)
    host = rgb_to_planes(image, bit_depth=bit_depth)
    device = rgb_to_planes(cp.asarray(image), bit_depth=bit_depth)
    assert isinstance(device, bytes) and device == host


@pytest.mark.gpu
def test_rgb_to_planes_on_the_device_refuses_a_nan_and_a_wrong_array() -> None:
    cp = _cupy()
    image = cp.zeros((4, 5, 3), dtype=cp.float32)
    image[2, 3, 1] = cp.nan
    with pytest.raises(ColorError, match="NaN"):
        rgb_to_planes(image, bit_depth=8)
    with pytest.raises(ColorError, match="float32"):
        rgb_to_planes(cp.zeros((4, 5, 3), dtype=cp.float64), bit_depth=8)


# --- the decode -----------------------------------------------------------------------------------


def test_device_frames_are_off_by_default() -> None:
    assert FFmpegVideoSource().device_frames is False


@pytest.mark.parametrize("device_frames", [False, True])
def test_a_software_decode_yields_host_frames(sample: Any, device_frames: bool) -> None:
    source = FFmpegVideoSource(device_frames=device_frames)
    info = source.probe(sample("vid-hevc8-bt709-full"))
    frames = source.frames(info, hw_decode=False)
    try:
        frame = next(iter(frames))
    finally:
        frames.close()  # type: ignore[attr-defined]
    assert frame.device == "cpu" and isinstance(frame.pixels, np.ndarray)


@pytest.mark.gpu
@pytest.mark.parametrize("sample_id", SAMPLES)
def test_a_device_frame_decode_equals_the_host_decode(sample: Any, sample_id: str) -> None:
    cp = _cupy()
    path = sample(sample_id)
    host_source, device_source = FFmpegVideoSource(), FFmpegVideoSource(device_frames=True)
    info = host_source.probe(path)
    host = list(host_source.frames(info, hw_decode=True))
    device = list(device_source.frames(info, hw_decode=True))
    assert host and len(device) == len(host)
    for h, d in zip(host, device, strict=True):
        assert h.device == "cpu" and d.device == f"cuda:{cp.cuda.runtime.getDevice()}"
        assert isinstance(d.pixels, cp.ndarray)
        assert (d.pts_ticks, d.time_base, d.index, d.color) == (
            h.pts_ticks,
            h.time_base,
            h.index,
            h.color,
        )
        assert np.array_equal(_bits(d.pixels), _bits(h.pixels)), f"pts {h.pts_ticks}"


# --- the sink -------------------------------------------------------------------------------------


def _opened(source: Path, out: Path) -> tuple[FFmpegVideoSink, list[Any]]:
    info = probe(source)
    frames = list(vf.decode_frames(source, info))
    out.write_bytes(b"")
    sink = FFmpegVideoSink()
    sink.open(info, out, encoder="libx265", quality="draft", bit_depth=8, provenance=None)
    return sink, frames


@pytest.mark.gpu
def test_the_sink_writes_a_device_frame_as_the_host_planes(sample: Any, tmp_path: Path) -> None:
    cp = _cupy()
    device = f"cuda:{cp.cuda.runtime.getDevice()}"
    host_sink, frames = _opened(sample("vid-vfr"), tmp_path / "host.mp4")
    device_sink, _ = _opened(sample("vid-vfr"), tmp_path / "device.mp4")
    try:
        for frame in frames[:3]:
            on_device = replace(frame, pixels=cp.asarray(frame.pixels), device=device)
            assert device_sink._payload(on_device) == host_sink._payload(frame)
    finally:
        host_sink.abort()
        device_sink.abort()


@pytest.mark.gpu
def test_a_device_frame_export_closes_and_verifies(sample: Any, tmp_path: Path) -> None:
    cp = _cupy()
    device = f"cuda:{cp.cuda.runtime.getDevice()}"
    sink, frames = _opened(sample("vid-vfr"), tmp_path / "out.mp4")
    try:
        for frame in frames:
            sink.write(replace(frame, pixels=cp.asarray(frame.pixels), device=device))
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
    cp = _cupy()
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)
    with pytest.raises(VideoEncodeError) as caught:
        sink.write(replace(frames[0], pixels=cp.asarray(frames[0].pixels), device=label))
    assert caught.value.kind == "frame"
    assert not out.exists()
    sink.abort()


@pytest.mark.gpu
def test_the_sink_refuses_a_float64_device_frame(sample: Any, tmp_path: Path) -> None:
    cp = _cupy()
    device = f"cuda:{cp.cuda.runtime.getDevice()}"
    sink, frames = _opened(sample("vid-vfr"), tmp_path / "out.mp4")
    pixels = cp.asarray(frames[0].pixels, dtype=cp.float64)
    with pytest.raises(VideoEncodeError, match="float32") as caught:
        sink.write(replace(frames[0], pixels=pixels, device=device))
    assert caught.value.kind == "frame"
    sink.abort()


def test_the_sink_still_refuses_a_device_label_on_host_pixels(sample: Any, tmp_path: Path) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)
    with pytest.raises(VideoEncodeError, match="to_host") as caught:
        sink.write(replace(frames[0], device="cuda:0"))
    assert caught.value.kind == "frame"
    assert not out.exists()
    sink.abort()


# --- DR-63: an abort inside close's window ----------------------------------------------------


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


def test_an_abort_after_a_clean_close_does_nothing(sample: Any, tmp_path: Path) -> None:
    out = tmp_path / "out.mp4"
    sink, frames = _opened(sample("vid-vfr"), out)
    for frame in frames:
        sink.write(frame)
    sink.close()
    assert sink._phase == "closed"
    sink.abort()
    assert out.exists()
