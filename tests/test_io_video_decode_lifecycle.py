"""Video decode (WP3.9): process lifecycle, failure handling, the AD-23 pipe and the CUDA check.

- ``close()`` after one frame, and an iterator dropped without ``close()``, leave no FFmpeg
  process and no thread; a planted FFmpeg death mid-stream raises, never hangs.
- Planted side channels (a stand-in FFmpeg) show every pts fault raised by name, never dropped
  (DR-20 (2)), and the clean-end versus raise table of spec 5.4 / D86.
- AD-23: the large pipe is used on Windows; when it cannot be created the default pipe gives the
  same bytes and pts on every sample, with the reason logged once.
- Q8 (corrected at round 0): with CUDA hidden, ``hw_decode=True`` decodes in software, the same
  frames, with the reason logged once.
"""

from __future__ import annotations

import dataclasses
import gc
import json
import logging
import os
import sys
import threading
import time
from collections.abc import Callable, Iterator
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

from clearwater.color import rgb_to_planes
from clearwater.interfaces.image import Frame
from clearwater.interfaces.video import Fault, ProbeResult
from clearwater.io.video import FFmpegVideoSource, VideoDecodeError, pipes, probe
from clearwater.io.video import decode as decode_module

pytestmark = pytest.mark.usefixtures("ffmpeg_tools")

SOURCE = FFmpegVideoSource()
DECODABLE = [
    "vid-hevc8-bt709-full",
    "vid-hevc10",
    "vid-untagged",
    "vid-truncated",
    "vid-vfr",
    "vid-rotated",
]
BOUND_S = 15.0
"""Seconds a shutdown or a failure may take to surface (generous; it is normally milliseconds)."""


def frame_record(frames: Iterator[Frame]) -> list[tuple[int, bytes]]:
    """Each frame's pts and integer planes."""
    return [
        (frame.pts_ticks, rgb_to_planes(frame.pixels, bit_depth=frame.color.bit_depth))
        for frame in frames
    ]


@pytest.fixture
def force_default_pipe(monkeypatch: pytest.MonkeyPatch) -> None:
    """Make the large pipe fail to be created (the AD-23 fallback)."""

    def fail(size: int) -> tuple[int, int]:
        raise OSError(f"forced failure of the {size}-byte pipe")

    monkeypatch.setattr(pipes, "_create_pipe", fail)
    monkeypatch.setattr(pipes, "_fallback_logged", False)


# --- lifecycle on real FFmpeg -------------------------------------------------------------------


def test_close_after_one_frame_ends_ffmpeg_and_the_thread(sample: Callable[[str], Path]) -> None:
    stream = SOURCE.frames(probe(sample("vid-hevc8-bt709-full")), hw_decode=False)
    assert isinstance(stream, decode_module.FrameStream)
    first = next(stream)
    assert first.pts_ticks == 0
    process, thread = stream._process.process, stream._process.thread
    assert process is not None and thread is not None
    began = time.monotonic()
    stream.close()
    assert time.monotonic() - began < BOUND_S
    assert process.poll() is not None
    assert not thread.is_alive()
    with pytest.raises(StopIteration):
        next(stream)
    stream.close()  # idempotent


def test_an_iterator_dropped_without_close_is_cleaned_up(
    sample: Callable[[str], Path], force_default_pipe: None
) -> None:
    # The default pipe keeps FFmpeg blocked on its output, so it is still running when dropped.
    stream = SOURCE.frames(probe(sample("vid-hevc8-bt709-full")), hw_decode=False)
    next(stream)
    process, thread = stream._process.process, stream._process.thread
    assert process is not None and thread is not None
    assert process.poll() is None
    del stream
    gc.collect()
    process.wait(timeout=BOUND_S)
    thread.join(timeout=BOUND_S)
    assert not thread.is_alive()


def test_an_iterator_never_iterated_starts_nothing(sample: Callable[[str], Path]) -> None:
    stream = SOURCE.frames(probe(sample("vid-vfr")), hw_decode=False)
    assert isinstance(stream, decode_module.FrameStream)
    assert stream._process.process is None
    stream.close()
    with pytest.raises(StopIteration):
        next(stream)


def test_a_planted_ffmpeg_death_mid_stream_raises_and_never_hangs(
    sample: Callable[[str], Path], force_default_pipe: None
) -> None:
    stream = SOURCE.frames(probe(sample("vid-hevc8-bt709-full")), hw_decode=False)
    next(stream)
    process = stream._process.process
    assert process is not None and process.poll() is None
    process.kill()
    began = time.monotonic()
    with pytest.raises(VideoDecodeError) as caught:
        for _ in stream:
            pass
    assert time.monotonic() - began < BOUND_S
    assert caught.value.kind == "unreadable"
    assert stream._process.thread is not None and not stream._process.thread.is_alive()


def test_a_close_landing_between_read_and_return_returns_no_frame(
    sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    # Stands in for close() called from another thread after a frame was read but before
    # next() returned it: next() must end, not hand the frame out after close() returned.
    stream = SOURCE.frames(probe(sample("vid-vfr")), hw_decode=False)
    assert isinstance(stream, decode_module.FrameStream)
    next(stream)
    build = stream._frame

    def build_then_close(pts: int) -> Frame:
        frame = build(pts)
        stream.close()
        return frame

    monkeypatch.setattr(stream, "_frame", build_then_close)
    with pytest.raises(StopIteration):
        next(stream)


# --- planted side channels: a stand-in FFmpeg ----------------------------------------------------

FAKE_FFMPEG = """
import json, sys
spec = json.loads(sys.argv[1])
err, out = sys.stderr.buffer, sys.stdout.buffer
for kind, value in spec["actions"]:
    if kind == "line":
        err.write(value.encode("utf-8") + b"\\n"); err.flush()
    elif kind == "frame":
        out.write(bytes([value % 256]) * spec["size"]); out.flush()
    elif kind == "bytes":
        out.write(b"\\0" * value); out.flush()
sys.exit(spec["exit"])
"""
CONFIG = "[Parsed_showinfo_0 @ 0000] [info] config in time_base: 1/30000, frame_rate: 30000/1001"


def info(n: int, pts: object) -> list[Any]:
    """A ``showinfo`` frame line action."""
    return ["line", f"[Parsed_showinfo_0 @ 0000] [info] n: {n:3d} pts: {pts!s:>6} pts_time:0"]


@pytest.fixture
def planted(
    sample: Callable[[str], Path], tmp_path: Path
) -> Callable[..., decode_module.FrameStream]:
    """Return ``planted(actions, exit=0, flagged=False)``: a stream over a stand-in FFmpeg."""
    script = tmp_path / "fake_ffmpeg.py"
    script.write_text(FAKE_FFMPEG, encoding="ascii")
    result = probe(sample("vid-hevc8-bt709-full"))
    size = 320 * 180 * 3

    def make(
        actions: list[list[Any]], exit: int = 0, flagged: bool = False
    ) -> decode_module.FrameStream:
        given: ProbeResult = result
        if flagged:
            cut = Fault("truncated", "warn", "cut short")
            given = dataclasses.replace(result, faults=(cut,))
        spec = json.dumps({"actions": actions, "size": size, "exit": exit})
        command = [sys.executable, "-I", str(script), spec]
        return decode_module.FrameStream(given, command, start_s=None, end_s=None)

    return make


def frames_then(stream: decode_module.FrameStream) -> tuple[list[int], BaseException | None]:
    """Collect pts until the stream ends or raises; return them and the exception, if any."""
    got: list[int] = []
    try:
        for frame in stream:
            got.append(frame.pts_ticks)
    except VideoDecodeError as error:
        return got, error
    return got, None


def three_frames() -> list[list[Any]]:
    """A good side channel and three frames."""
    return [
        ["line", CONFIG],
        info(0, 0),
        ["frame", 0],
        info(1, 1001),
        ["frame", 1],
        info(2, 2002),
        ["frame", 2],
    ]


def test_a_planted_good_stream_yields_its_frames(planted: Callable[..., Any]) -> None:
    got, error = frames_then(planted(three_frames()))
    assert (got, error) == ([0, 1001, 2002], None)


@pytest.mark.parametrize(
    ("second", "third", "words"),
    [
        (info(1, 1001), info(2, 1001), "repeats"),
        (info(1, 3003), info(2, 2002), "goes back"),
        (info(1, 1001), info(2, "NOPTS"), "no usable timestamp"),
        (info(1, 1001), info(3, 2002), "line 3 arrived where line 2"),
    ],
    ids=["repeated", "decreasing", "nopts", "number-gap"],
)
def test_a_bad_pts_is_an_error_by_name_after_the_good_frames(
    planted: Callable[..., Any], second: list[Any], third: list[Any], words: str
) -> None:
    actions = [["line", CONFIG], info(0, 0), ["frame", 0], second, ["frame", 1], third]
    got, error = frames_then(planted([*actions, ["frame", 2]]))
    assert got == [0, int(second[1].split("pts:")[1].split()[0])]
    assert isinstance(error, VideoDecodeError) and error.kind == "pts"
    assert words in str(error)


def test_a_frame_without_a_pts_line_is_an_error(planted: Callable[..., Any]) -> None:
    actions = [["line", CONFIG], info(0, 0), ["frame", 0], ["frame", 1]]
    got, error = frames_then(planted(actions))
    assert got == [0]
    assert isinstance(error, VideoDecodeError) and error.kind == "pts"


def test_an_orphan_pts_line_is_an_error_with_the_tail_logged(
    planted: Callable[..., Any], caplog: pytest.LogCaptureFixture
) -> None:
    actions = [*three_frames(), ["line", "[hevc @ 0000] [error] late \u00e9 noise"], info(3, 3003)]
    with caplog.at_level(logging.WARNING, logger=decode_module.__name__):
        got, error = frames_then(planted(actions))
    messages = [record.getMessage() for record in caplog.records]
    assert any("late \\xe9 noise" in message for message in messages)
    assert all(message.isascii() for message in messages)
    assert got == [0, 1001, 2002]
    assert isinstance(error, VideoDecodeError) and error.kind == "pts"
    assert "1 timestamp lines have no frame" in str(error)


def test_an_orphan_pts_line_after_a_failure_is_the_failure(planted: Callable[..., Any]) -> None:
    # A dying FFmpeg can log frames that never reach the pipe; the failure is what is reported.
    got, error = frames_then(planted([*three_frames(), info(3, 3003)], exit=1))
    assert got == [0, 1001, 2002]
    assert isinstance(error, VideoDecodeError) and error.kind == "unreadable"


def test_a_time_base_other_than_the_probes_is_an_error(planted: Callable[..., Any]) -> None:
    actions = three_frames()
    actions[0] = ["line", CONFIG.replace("1/30000", "1/90000")]
    got, error = frames_then(planted(actions))
    assert got == []
    assert isinstance(error, VideoDecodeError) and error.kind == "pts"


@pytest.mark.parametrize("flagged", [False, True])
def test_a_short_read_is_unreadable_even_on_a_flagged_file(
    planted: Callable[..., Any], flagged: bool
) -> None:
    actions = [["line", CONFIG], info(0, 0), ["frame", 0], info(1, 1001), ["bytes", 100]]
    got, error = frames_then(planted(actions, flagged=flagged))
    assert got == [0]
    assert isinstance(error, VideoDecodeError) and error.kind == "unreadable"


def test_a_failure_on_a_clean_file_raises_after_the_last_good_frame(
    planted: Callable[..., Any], caplog: pytest.LogCaptureFixture
) -> None:
    actions = [*three_frames(), ["line", "[hevc @ 0000] [error] broken \u00e9 data"]]
    with caplog.at_level(logging.WARNING, logger=decode_module.__name__):
        got, error = frames_then(planted(actions, exit=1))
    assert got == [0, 1001, 2002]
    assert isinstance(error, VideoDecodeError) and error.kind == "unreadable"
    assert str(error).isascii()
    messages = [record.getMessage() for record in caplog.records]
    assert any("broken \\xe9 data" in message for message in messages)
    assert all(message.isascii() for message in messages)


def test_a_failure_on_a_flagged_file_ends_cleanly(planted: Callable[..., Any]) -> None:
    got, error = frames_then(planted(three_frames(), exit=1, flagged=True))
    assert (got, error) == ([0, 1001, 2002], None)


def test_errors_with_a_clean_exit_are_logged_once_not_raised(
    planted: Callable[..., Any], caplog: pytest.LogCaptureFixture
) -> None:
    actions = [*three_frames(), ["line", "[hevc @ 0000] [error] concealed \u00e9 error"]]
    with caplog.at_level(logging.WARNING, logger=decode_module.__name__):
        got, error = frames_then(planted(actions))
    assert (got, error) == ([0, 1001, 2002], None)
    warnings = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(warnings) == 1 and "concealed \\xe9 error" in warnings[0]


def test_info_lines_never_reach_the_logged_tail(
    planted: Callable[..., Any], caplog: pytest.LogCaptureFixture
) -> None:
    actions = [
        ["line", "[info]   Metadata: location +12.3456-078.9012/"],
        *three_frames(),
        ["line", "[hevc @ 0000] [error] the error"],
    ]
    with caplog.at_level(logging.WARNING, logger=decode_module.__name__):
        frames_then(planted(actions, exit=1))
    text = " ".join(record.getMessage() for record in caplog.records)
    assert "the error" in text and "Metadata" not in text


# --- AD-23: the pipe and its fallback -------------------------------------------------------------


def test_the_pipe_size_is_one_named_constant_of_32_mib() -> None:
    assert pipes.BIG_PIPE_BYTES == 32 * 1024 * 1024


@pytest.mark.skipif(sys.platform != "win32", reason="the enlarged pipe exists on Windows only")
def test_the_large_pipe_holds_16_mib_without_a_reader() -> None:
    fds = pipes.open_frame_pipe()
    assert fds is not None
    read_fd, write_fd = fds
    chunk = b"\0" * (16 * 1024 * 1024)
    writer = threading.Thread(target=os.write, args=(write_fd, chunk), daemon=True)
    try:
        writer.start()
        writer.join(timeout=BOUND_S)
        assert not writer.is_alive(), "a 16 MiB write blocked: the buffer is not enlarged"
    finally:
        os.close(write_fd)
        with open(read_fd, "rb") as reader:
            assert len(reader.read()) == len(chunk)


@pytest.mark.skipif(sys.platform != "win32", reason="the enlarged pipe exists on Windows only")
def test_the_decoder_uses_the_large_pipe_on_windows(
    sample: Callable[[str], Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    sizes: list[int] = []
    real = pipes._create_pipe

    def spy(size: int) -> tuple[int, int]:
        sizes.append(size)
        return real(size)

    monkeypatch.setattr(pipes, "_create_pipe", spy)
    assert len(list(SOURCE.frames(probe(sample("vid-vfr")), hw_decode=False))) == 30
    assert sizes == [pipes.BIG_PIPE_BYTES]


def test_off_windows_the_default_pipe_is_used_and_said_once(
    monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    monkeypatch.setattr(pipes.sys, "platform", "linux")
    monkeypatch.setattr(pipes, "_fallback_logged", False)
    with caplog.at_level(logging.INFO, logger=pipes.__name__):
        assert pipes.open_frame_pipe() is None
        assert pipes.open_frame_pipe() is None
    assert len(caplog.records) == 1 and "linux" in caplog.records[0].getMessage()


def test_the_forced_fallback_gives_the_same_bytes_and_pts_on_every_sample(
    sample: Callable[[str], Path],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    results = {sample_id: probe(sample(sample_id)) for sample_id in DECODABLE}
    large = {
        sample_id: frame_record(SOURCE.frames(result, hw_decode=False))
        for sample_id, result in results.items()
    }

    def fail(size: int) -> tuple[int, int]:
        raise OSError("forced failure")

    monkeypatch.setattr(pipes, "_create_pipe", fail)
    monkeypatch.setattr(pipes, "_fallback_logged", False)
    with caplog.at_level(logging.WARNING, logger=pipes.__name__):
        default = {
            sample_id: frame_record(SOURCE.frames(result, hw_decode=False))
            for sample_id, result in results.items()
        }
    assert default == large
    assert [len(record) for record in default.values()] == [45, 45, 45, 24, 30, 45]
    assert [r.getMessage() for r in caplog.records] == [
        "using the default frame pipe: OSError: forced failure"
    ]


# --- Q8: hw_decode without CUDA -----------------------------------------------------------------


def test_hw_decode_without_cuda_decodes_in_software_and_says_so_once(
    sample: Callable[[str], Path],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setenv("CUDA_VISIBLE_DEVICES", "-1")
    monkeypatch.setattr(decode_module, "_cuda_available", None)
    for sample_id in ("vid-hevc8-bt709-full", "vid-hevc10"):
        result = probe(sample(sample_id))
        with caplog.at_level(logging.WARNING, logger=decode_module.__name__):
            hidden = SOURCE.frames(result, hw_decode=True)
            assert isinstance(hidden, decode_module.FrameStream)
            assert "-hwaccel" not in hidden._command
            hw = frame_record(hidden)
        assert hw == frame_record(SOURCE.frames(result, hw_decode=False))
        assert len(hw) == 45
    unavailable = [r for r in caplog.records if "CUDA decode is unavailable" in r.getMessage()]
    assert len(unavailable) == 1
    assert unavailable[0].getMessage().isascii()


def test_a_seek_does_not_start_before_the_given_time(sample: Callable[[str], Path]) -> None:
    result = probe(sample("vid-vfr"))
    stream = SOURCE.frames(result, hw_decode=False, start_s=Fraction(1))
    assert isinstance(stream, decode_module.FrameStream)
    assert "-ss" in stream._command
    assert all(frame.pts >= 1 for frame in stream)


def test_an_ffmpeg_that_cannot_be_run_is_unreadable(sample: Callable[[str], Path]) -> None:
    result = probe(sample("vid-vfr"))
    stream = decode_module.FrameStream(
        result, ["no-such-ffmpeg-program-wp39"], start_s=None, end_s=None
    )
    with pytest.raises(VideoDecodeError) as caught:
        next(stream)
    assert caught.value.kind == "unreadable" and str(caught.value).isascii()
    with pytest.raises(StopIteration):
        next(stream)


def test_close_from_another_thread_ends_the_reader_without_an_error(
    sample: Callable[[str], Path], force_default_pipe: None
) -> None:
    stream = SOURCE.frames(probe(sample("vid-hevc8-bt709-full")), hw_decode=False)
    assert isinstance(stream, decode_module.FrameStream)
    next(stream)
    closer = threading.Timer(0.2, stream.close)
    closer.start()
    count = 0
    for _ in stream:
        count += 1
        time.sleep(0.05)
    closer.join()
    assert count < 44
