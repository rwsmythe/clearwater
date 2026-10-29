"""Video decode: an IF-5 :class:`VideoSource` over one FFmpeg process per call (WP3.9).

:meth:`FFmpegVideoSource.frames` runs one ``ffmpeg`` process (AD-2) that decodes the probed video
stream, converts it with WP3.5's filter to full-range planar RGB at the source bit depth (AD-10)
and writes the raw frames to an anonymous pipe, enlarged on Windows (AD-23, :mod:`.pipes`).
Every frame is yielded as an IF-1 :class:`~clearwater.interfaces.image.Frame` with its exact
source pts.

The pts side channel is ``showinfo``, first in the filter chain: it logs each frame's number and
pts on standard error before the frame's bytes reach the pipe. A thread drains standard error;
frame n's bytes are paired with ``showinfo`` line n. A missing, repeated or decreasing pts is an
error by name, never dropped. The colour description is the probe's (D54 included); nothing here
runs ffprobe.

A file the probe flagged ``truncated`` or ``unreadable_tail`` yields every decodable frame and
ends without raising (D86; the warning is the probe's fault). On a file the probe found clean, an
FFmpeg failure raises :class:`VideoDecodeError` after the last good frame.

Device frames (WP3.21 #2, AD-29) are opt-in at construction and off by default: a source built
with ``device_backend=<the GPU backend>`` uploads each frame's integer planes and converts them on
that backend's device for a ``frames(..., hw_decode=True)`` call. The backend is reached only
through :class:`DeviceFrameBackend`, this package's Protocol for the IF-2 device extensions; a
backend without them (the CPU backend), or None, leaves every frame on the host as before. The
caller's ``hw_decode`` states that its backend is the GPU (the export job and the analysis engine
pass ``backend.device != "cpu"``); the frames themselves are the host conversion's, bit for bit.
"""

from __future__ import annotations

import collections
import contextlib
import io
import logging
import math
import os
import queue
import re
import subprocess
import threading
import weakref
from collections.abc import Buffer, Iterator
from fractions import Fraction
from pathlib import Path
from typing import IO, Literal, Protocol, runtime_checkable

from clearwater.color import decode_filter, planes_to_rgb, rgb_frame_bytes
from clearwater.interfaces.image import Array, Frame
from clearwater.interfaces.video import ProbeResult
from clearwater.io.video.inputs import ascii_text
from clearwater.io.video.pipes import open_frame_pipe, tool_spawn_kwargs
from clearwater.io.video.probe import find_tool
from clearwater.io.video.probe import probe as probe_file

_log = logging.getLogger(__name__)

PTS_WAIT_S = 60
"""Seconds to wait for a frame's ``showinfo`` line once its bytes have arrived."""

EXIT_WAIT_S = 30
"""Seconds FFmpeg may take to exit after its output has ended."""

SHUTDOWN_WAIT_S = 10
"""Seconds to wait for a killed FFmpeg to exit and for the standard-error thread to finish."""

CUDA_CHECK_TIMEOUT_S = 30
"""Seconds the one-time CUDA availability check may run."""

TAIL_LINES = 20
"""Warning and error lines of FFmpeg's standard error kept for the log."""

_FLAGGED_KINDS = frozenset({"truncated", "unreadable_tail"})
_SHOWINFO_FRAME = re.compile(r"^\[Parsed_showinfo_0 @ [^\]]*\] \[info\] n:\s*(\d+)\s+pts:\s*(\S+)")
_SHOWINFO_CONFIG = re.compile(
    r"^\[Parsed_showinfo_0 @ [^\]]*\] \[info\] config in time_base:\s*(\d+)/(\d+)"
)
_LEVEL = re.compile(r"\[(panic|fatal|error|warning|info|verbose|debug|trace)\] ")
_PROBLEM_LEVELS = frozenset({"panic", "fatal", "error", "warning"})
_ERROR_LEVELS = frozenset({"panic", "fatal", "error"})

DecodeErrorKind = Literal["refused", "unreadable", "pts"]

_cuda_available: bool | None = None
_cuda_lock = threading.Lock()


@runtime_checkable
class DeviceFrameBackend(Protocol):
    """The IF-2 device extensions ``clearwater.io.video`` calls (AD-29), by structure.

    NOT part of the frozen IF-2 ABC: the GPU backend provides them and the CPU backend does not.
    The names and signatures are the GPU backend's; the decode calls :meth:`planes_to_rgb` and
    the sink :meth:`rgb_to_planes`. A backend that does not satisfy this Protocol (the CPU
    backend) or None leaves the source and the sink on their host paths.

    Attributes:
        device: The device the arrays live on, ``"cuda:<n>"``.
    """

    device: str

    def planes_to_rgb(self, data: Buffer, *, width: int, height: int, bit_depth: int) -> Array:
        """Upload one planar G, B, R frame and convert it to float32 RGB on the device."""
        ...

    def rgb_to_planes(self, a: Array, *, bit_depth: int) -> bytes:
        """Quantise a float32 RGB device array to one planar G, B, R frame on the device."""
        ...


class VideoDecodeError(Exception):
    """A video cannot be decoded, or its decode failed (WP3.9).

    Attributes:
        kind: ``"refused"`` (the probe carries a ``"refuse"`` fault, for example HLG or PQ;
            FFmpeg is never started), ``"unreadable"`` (FFmpeg could not be run, failed on a file
            the probe found clean, or a frame arrived incomplete; raised after the last good
            frame) or ``"pts"``
            (a frame's pts is missing, repeated or decreasing, or a pts has no frame).
    """

    def __init__(self, kind: DecodeErrorKind, message: str) -> None:
        """Store the kind and the user-readable message.

        Args:
            kind: The reason class.
            message: A message the GUI can show (ASCII-safe).
        """
        super().__init__(message)
        self.kind: DecodeErrorKind = kind


def cuda_decode_available() -> bool:
    """Return whether FFmpeg can create a CUDA device; checked once per process.

    ``-hwaccel cuda`` makes FFmpeg 9.0.2 exit with an error, not fall back to software, when no
    CUDA device exists; FFmpeg falls back by itself only when a device exists but cannot decode
    the stream. So the device is checked once, with a tiny generated input, and the result kept.
    When it is unavailable, the reason is logged once.

    Returns:
        True when ``-hwaccel cuda`` can be used.
    """
    global _cuda_available
    with _cuda_lock:
        if _cuda_available is None:
            _cuda_available, reason = _check_cuda()
            if not _cuda_available:
                _log.warning("CUDA decode is unavailable, decoding in software: %s", reason)
        return _cuda_available


def _check_cuda() -> tuple[bool, str]:
    """Run FFmpeg once with a CUDA device; return whether it worked and, if not, why."""
    command = [
        str(find_tool("ffmpeg")),
        "-nostdin",
        "-hide_banner",
        "-v",
        "error",
        "-init_hw_device",
        "cuda",
        "-f",
        "lavfi",
        "-i",
        "color=s=64x64:d=0.1",
        "-f",
        "null",
        "-",
    ]
    try:
        done = subprocess.run(
            command,
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=CUDA_CHECK_TIMEOUT_S,
            check=False,
            **tool_spawn_kwargs(),
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        return False, ascii_text(f"{type(error).__name__}: {error}")
    if done.returncode == 0:
        return True, ""
    lines = done.stderr.decode("utf-8", errors="replace").strip().splitlines()
    return False, ascii_text(lines[0] if lines else f"ffmpeg exited with {done.returncode}")


def _seek_argument(seconds: Fraction) -> str | None:
    """Format an input seek position floored to a microsecond; None when it is not positive."""
    micro = math.floor(seconds * 1_000_000)
    if micro <= 0:
        return None
    return f"{micro // 1_000_000}.{micro % 1_000_000:06d}"


def seek_position(probe: ProbeResult, start_s: Fraction) -> str | None:
    """Return FFmpeg's input ``-ss`` argument for a start time, or None for no seek.

    Under ``-copyts`` an input ``-ss`` counts from the container start, so the probe's start
    offset is subtracted. The position is one nominal frame before ``start_s`` and floored, so
    FFmpeg never discards the frame at ``start_s``; the decoder discards the frames before it by
    exact pts.

    Args:
        probe: The probe result of the file.
        start_s: The first time to yield, in seconds.

    Returns:
        The ``-ss`` argument, or None when the position is at or before the container start.
    """
    rate = probe.video.frame_rate
    margin = 1 / rate if rate > 0 else Fraction(1)
    return _seek_argument(start_s - margin - probe.start_offset_s)


def decode_command(
    probe: ProbeResult, *, ffmpeg: Path, cuda: bool, seek: str | None = None
) -> list[str]:
    """Return the FFmpeg command that decodes the probed video stream to raw RGB on stdout.

    Args:
        probe: The probe result of the file.
        ffmpeg: The ``ffmpeg`` executable.
        cuda: Decode with ``-hwaccel cuda`` (frames are downloaded before the filter).
        seek: The input ``-ss`` argument (:func:`seek_position`), or None.

    Returns:
        The command as an argument list. Only the first video stream is mapped; no audio,
        subtitle or data stream is.

    Raises:
        ColorError: The stream is outside WP3.5's supported set.
    """
    command = [
        str(ffmpeg),
        "-nostdin",
        "-hide_banner",
        "-nostats",
        "-loglevel",
        "repeat+level+info",
    ]
    if cuda:
        command += ["-hwaccel", "cuda"]
    command += ["-noautorotate", "-copyts"]
    if seek is not None:
        command += ["-ss", seek]
    command += ["-i", f"file:{probe.path.absolute()}", "-map", "0:v:0", "-an", "-sn", "-dn"]
    command += ["-vf", f"showinfo,{decode_filter(probe.video)}"]
    command += ["-fps_mode", "passthrough", "-f", "rawvideo", "pipe:1"]
    return command


class _Diagnostics:
    """What the standard-error thread collected besides the pts: the tail and error count."""

    def __init__(self) -> None:
        """Start empty."""
        self.tail: collections.deque[str] = collections.deque(maxlen=TAIL_LINES)
        self.error_lines = 0


type _Item = tuple[Literal["frame"], int, str] | tuple[Literal["time_base"], str] | None


def _drain(stream: IO[bytes], items: queue.SimpleQueue[_Item], diagnostics: _Diagnostics) -> None:
    """Read FFmpeg's standard error to its end: queue the pts lines, keep the problem lines.

    Always queues a final None, so the reader never waits for a line that cannot come.
    """
    try:
        for raw in stream:
            line = raw.decode("utf-8", errors="replace").rstrip("\r\n")
            if frame := _SHOWINFO_FRAME.match(line):
                items.put(("frame", int(frame.group(1)), frame.group(2)))
                continue
            if config := _SHOWINFO_CONFIG.match(line):
                items.put(("time_base", f"{config.group(1)}/{config.group(2)}"))
                continue
            level = _LEVEL.search(line)
            if level is not None and level.group(1) in _PROBLEM_LEVELS:
                diagnostics.tail.append(line)
                if level.group(1) in _ERROR_LEVELS:
                    diagnostics.error_lines += 1
    except (OSError, ValueError):
        pass
    finally:
        items.put(None)


class _Process:
    """The running FFmpeg process, its pipes and the standard-error thread.

    Holds no reference to the iterator, so an abandoned iterator can be collected and its
    finalizer can shut this down.
    """

    def __init__(self) -> None:
        """Start with nothing running."""
        self.process: subprocess.Popen[bytes] | None = None
        self.stdout: IO[bytes] | None = None
        self.stderr: IO[bytes] | None = None
        self.thread: threading.Thread | None = None
        self.items: queue.SimpleQueue[_Item] = queue.SimpleQueue()
        self.diagnostics = _Diagnostics()
        self._lock = threading.Lock()
        self._closed = False

    def start(self, command: list[str]) -> bool:
        """Start FFmpeg with its output on the frame pipe and its standard error drained.

        Runs under the shutdown lock, so a :meth:`shutdown` from another thread either waits for
        the start and then stops the new process, or comes first and nothing is started.

        Returns:
            True when started; False when this was already shut down (nothing is started).

        Raises:
            OSError: FFmpeg cannot be started.
        """
        with self._lock:
            if self._closed:
                return False
            self._start(command)
            return True

    def _start(self, command: list[str]) -> None:
        """Start the process and the thread (the caller holds the lock)."""
        fds = open_frame_pipe()
        if fds is not None:
            read_fd, write_fd = fds
            try:
                self.process = subprocess.Popen(
                    command,
                    stdin=subprocess.DEVNULL,
                    stdout=write_fd,
                    stderr=subprocess.PIPE,
                    bufsize=0,
                    **tool_spawn_kwargs(),
                )
            except BaseException:
                os.close(read_fd)
                raise
            finally:
                os.close(write_fd)  # the child holds its own copy
            self.stdout = open(read_fd, "rb", buffering=0)  # noqa: SIM115 - closed in shutdown()
        else:
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0,
                **tool_spawn_kwargs(),
            )
            self.stdout = self.process.stdout
        raw_stderr = self.process.stderr
        assert raw_stderr is not None  # stderr=PIPE always gives a stream
        self.stderr = io.BufferedReader(raw_stderr)  # type: ignore[type-var]
        self.thread = threading.Thread(
            target=_drain,
            args=(self.stderr, self.items, self.diagnostics),
            name="ffmpeg-stderr",
            daemon=True,
        )
        self.thread.start()

    def finish(self) -> int | None:
        """Wait for FFmpeg to exit after its output ended and for the thread to finish.

        Returns:
            The exit status, or None when FFmpeg had to be killed or the thread did not end.
        """
        status: int | None = None
        if self.process is not None:
            try:
                status = self.process.wait(timeout=EXIT_WAIT_S)
            except subprocess.TimeoutExpired:
                status = None
        self.shutdown()
        if self.thread is not None and self.thread.is_alive():
            return None
        return status

    def shutdown(self) -> None:
        """Stop FFmpeg if it still runs, close the pipes and join the thread (idempotent).

        The whole shutdown runs under the lock, so a concurrent second call returns only after
        the first has finished its cleanup.
        """
        with self._lock:
            if self._closed:
                return
            self._closed = True
            self._stop()

    def _stop(self) -> None:
        """Kill and reap FFmpeg, close the pipes and join the thread (the caller holds the lock)."""
        process = self.process
        if process is not None:
            if process.poll() is None:
                with contextlib.suppress(OSError):
                    process.kill()
            try:
                process.wait(timeout=SHUTDOWN_WAIT_S)
            except subprocess.TimeoutExpired:
                _log.warning("ffmpeg (pid %s) did not exit after being killed", process.pid)
        if self.stdout is not None:
            with contextlib.suppress(OSError):
                self.stdout.close()
        if self.thread is not None:
            self.thread.join(timeout=SHUTDOWN_WAIT_S)
        if self.stderr is not None and (self.thread is None or not self.thread.is_alive()):
            with contextlib.suppress(OSError):
                self.stderr.close()


class FrameStream(Iterator[Frame]):
    """The frames of one decode, in pts order; an iterator with :meth:`close`.

    FFmpeg starts at the first :func:`next`. The iterator stops at the end of the file, at
    ``end_s``, after :meth:`close`, or after raising; dropping it without :meth:`close` stops
    FFmpeg when it is garbage-collected.
    """

    def __init__(
        self,
        probe: ProbeResult,
        command: list[str],
        *,
        start_s: Fraction | None,
        end_s: Fraction | None,
        device_backend: DeviceFrameBackend | None = None,
    ) -> None:
        """Prepare the decode; nothing runs yet.

        Args:
            probe: The probe result of the file.
            command: The FFmpeg command (:func:`decode_command`).
            start_s: The first time to yield, or None.
            end_s: The time to stop before, or None.
            device_backend: The backend that converts each frame on its device, or None for
                host frames.
        """
        video = probe.video
        self._device_backend = device_backend
        self._probe = probe
        self._command = command
        self._start_s = start_s
        self._end_s = end_s
        self._time_base = video.time_base
        self._frame_bytes = rgb_frame_bytes(video.width, video.height, video.bit_depth)
        self._buffer = bytearray(self._frame_bytes)
        self._flagged = any(fault.kind in _FLAGGED_KINDS for fault in probe.faults)
        self._name = ascii_text(probe.path.name)
        self._process = _Process()
        self._close = weakref.finalize(self, self._process.shutdown)
        self._return_lock = threading.Lock()
        self._started = False
        self._done = start_s is not None and end_s is not None and end_s <= start_s
        self._stderr_ended = False
        self._next_n = 0
        self._last_pts: int | None = None
        self._index = 0

    def __iter__(self) -> FrameStream:
        """Return the iterator itself."""
        return self

    def __next__(self) -> Frame:
        """Return the next frame.

        Raises:
            StopIteration: At the readable end, at ``end_s``, or after :meth:`close`.
            VideoDecodeError: The decode failed (see the class docstring of the error); FFmpeg
                could not be started (``"unreadable"``).
        """
        if self._done:
            raise StopIteration
        try:
            if not self._started:
                self._started = True
                try:
                    started = self._process.start(self._command)
                except OSError as error:
                    raise VideoDecodeError(
                        "unreadable", ascii_text(f"ffmpeg could not be run: {error}")
                    ) from error
                if not started:  # closed from another thread before FFmpeg started
                    raise StopIteration
            while True:
                pts = self._read_frame()
                if pts is None:
                    if self._done:  # closed from another thread while reading
                        raise StopIteration
                    self._end()
                    raise StopIteration
                time = pts * self._time_base
                if self._start_s is not None and time < self._start_s:
                    continue
                if self._end_s is not None and time >= self._end_s:
                    raise StopIteration
                frame = self._frame(pts)
                with self._return_lock:
                    # close() sets _done under this lock, so no frame is returned once close()
                    # has returned, even when it is called from another thread.
                    if self._done:
                        raise StopIteration
                    self._index += 1
                    return frame
        except StopIteration:
            self.close()
            raise
        except BaseException as error:
            if self._done:  # closed from another thread: what failed was the shutdown
                raise StopIteration from None
            self.close()
            if isinstance(error, VideoDecodeError) and error.kind == "pts":
                self._log_tail("gave wrong frame timing")
            raise

    def close(self) -> None:
        """Stop FFmpeg and release the pipes and the thread; later calls do nothing.

        Safe to call from another thread: no frame is returned after it has returned.
        """
        with self._return_lock:
            self._done = True
        self._close()

    def _frame(self, pts: int) -> Frame:
        """Build the IF-1 frame from the buffer and its pts."""
        video = self._probe.video
        backend = self._device_backend
        if backend is None:
            pixels = planes_to_rgb(
                self._buffer, width=video.width, height=video.height, bit_depth=video.bit_depth
            )
            device = "cpu"
        else:
            pixels = backend.planes_to_rgb(
                self._buffer, width=video.width, height=video.height, bit_depth=video.bit_depth
            )
            device = backend.device
        return Frame(
            pixels=pixels,
            device=device,
            color=video.color,
            orientation_applied=False,
            pts=pts * self._time_base,
            pts_ticks=pts,
            time_base=self._time_base,
            index=self._index,
        )

    def _read_frame(self) -> int | None:
        """Read one whole frame into the buffer and return its pts; None at a clean end.

        Raises:
            VideoDecodeError: The frame is incomplete (``"unreadable"``) or its pts is wrong.
        """
        stream = self._process.stdout
        assert stream is not None
        view = memoryview(self._buffer)
        got = 0
        while got < self._frame_bytes:
            count = stream.readinto(view[got:])  # type: ignore[attr-defined]
            if not count:
                break
            got += count
        view.release()
        if got == 0:
            return None
        if got < self._frame_bytes:
            self._process.finish()
            self._log_tail("ended inside a frame")
            raise VideoDecodeError(
                "unreadable",
                f"The decode of {self._name} stopped in the middle of a frame "
                f"(frame {self._next_n}, {got} of {self._frame_bytes} bytes).",
            )
        return self._next_pts()

    def _next_pts(self) -> int:
        """Take the next frame's pts from the side channel and check it.

        Raises:
            VideoDecodeError: With kind ``"pts"`` when the pts is missing, not an integer,
                out of sequence, repeated or decreasing, or the time base differs.
        """
        while True:
            if self._stderr_ended:
                item: _Item = None
            else:
                try:
                    item = self._process.items.get(timeout=PTS_WAIT_S)
                except queue.Empty:
                    raise self._pts_error(
                        f"no timestamp arrived for frame {self._next_n} within {PTS_WAIT_S} s"
                    ) from None
            if item is None:
                self._stderr_ended = True
                raise self._pts_error(f"frame {self._next_n} has no timestamp")
            if item[0] == "time_base":
                self._check_time_base(item[1])
                continue
            _, number, token = item
            if number != self._next_n:
                raise self._pts_error(
                    f"timestamp line {number} arrived where line {self._next_n} was expected"
                )
            try:
                pts = int(token)
            except ValueError:
                raise self._pts_error(
                    f"frame {number} has no usable timestamp ({ascii_text(token)})"
                ) from None
            if self._last_pts is not None and pts <= self._last_pts:
                word = "repeats" if pts == self._last_pts else "goes back from"
                raise self._pts_error(f"frame {number}'s pts {pts} {word} pts {self._last_pts}")
            self._next_n += 1
            self._last_pts = pts
            return pts

    def _check_time_base(self, text: str) -> None:
        """Check the filter's input time base against the probe's.

        Raises:
            VideoDecodeError: With kind ``"pts"`` when they differ.
        """
        numerator, denominator = (int(part) for part in text.split("/"))
        if denominator == 0 or Fraction(numerator, denominator) != self._time_base:
            raise self._pts_error(
                f"the decoder's time base {text} is not the stream's {self._time_base}"
            )

    def _pts_error(self, detail: str) -> VideoDecodeError:
        """Build a ``"pts"`` error for this file."""
        return VideoDecodeError("pts", f"The frame timing of {self._name} is wrong: {detail}.")

    def _end(self) -> None:
        """Handle the end of the output: the exit status, then any orphan pts (D86).

        A pts line without a frame is an error only when FFmpeg finished normally: a process
        that died had frames in flight between the filter and the pipe, and its death is the
        failure to report.

        Raises:
            VideoDecodeError: FFmpeg failed on a file the probe found clean (``"unreadable"``),
                or it finished normally with a pts line left over (``"pts"``).
        """
        status = self._process.finish()
        orphans = 0
        while not self._stderr_ended:
            try:
                item = self._process.items.get_nowait()
            except queue.Empty:
                break
            if item is None:
                self._stderr_ended = True
            elif item[0] == "frame":
                orphans += 1
        if status == 0:
            if orphans:
                raise self._pts_error(f"{orphans} timestamp lines have no frame")
            if self._process.diagnostics.error_lines:
                level = logging.INFO if self._flagged else logging.WARNING
                self._log_tail("reported errors but finished", level=level)
            return
        if self._flagged:
            self._log_tail(f"ended with status {status} at the readable end", level=logging.INFO)
            return
        self._log_tail(f"failed with status {status}")
        raise VideoDecodeError(
            "unreadable",
            f"{self._name} could not be decoded to its end; "
            f"{self._index} frames were delivered before the failure.",
        )

    def _log_tail(self, what: str, level: int = logging.WARNING) -> None:
        """Log FFmpeg's last warning and error lines, ASCII-safe."""
        try:
            lines = list(self._process.diagnostics.tail)
        except RuntimeError:  # the thread outlived its join and appended meanwhile
            lines = ["(the message tail was still being written)"]
        tail = " | ".join(lines) or "(no message)"
        _log.log(level, "ffmpeg %s on %s: %s", what, self._name, ascii_text(tail))


class FFmpegVideoSource:
    """The IF-5 video source: WP3.7's probe and an FFmpeg decode per :meth:`frames` call."""

    def __init__(self, *, device_backend: object | None = None) -> None:
        """Choose where the frames of a ``hw_decode`` decode are converted.

        Args:
            device_backend: The job's backend. When it satisfies :class:`DeviceFrameBackend`
                (the GPU backend), the frames of a ``frames(..., hw_decode=True)`` call are
                converted on its device and yielded there. None (the default) or a backend
                without the device extensions (the CPU backend) yields every frame on the host;
                a call with ``hw_decode=False`` always does.
        """
        self.device_backend = device_backend

    def probe(self, path: Path) -> ProbeResult:
        """Probe a file (delegates to :func:`clearwater.io.video.probe`).

        Args:
            path: The video file.

        Returns:
            What the probe found.

        Raises:
            VideoProbeError: As :func:`clearwater.io.video.probe`.
        """
        return probe_file(path)

    def frames(
        self,
        probe: ProbeResult,
        *,
        hw_decode: bool,
        start_s: Fraction | None = None,
        end_s: Fraction | None = None,
    ) -> Iterator[Frame]:
        """Yield the frames of a probed file with exact pts; stops at the readable end (D86).

        The checks run at once: a probe carrying a ``"refuse"`` fault is refused before FFmpeg
        starts. FFmpeg itself starts at the first :func:`next`.

        Args:
            probe: The probe result of the file; its colour description is used unchanged.
            hw_decode: Decode with CUDA when a CUDA device is available (otherwise in software,
                with the same frames; the reason is logged once). With a ``device_backend`` that
                satisfies :class:`DeviceFrameBackend` it also states that the caller's backend
                is the GPU: the frames are converted and yielded on that backend's device.
            start_s: The first frame yielded is the first whose pts is at or after this time;
                None for the start.
            end_s: No frame whose pts is at or after this time is yielded; None for the end.

        Returns:
            A :class:`FrameStream` over the frames in pts order.

        Raises:
            VideoDecodeError: With kind ``"refused"`` for a refused probe (HLG, PQ).
            VideoProbeError: With kind ``"missing_tool"`` when ``ffmpeg`` is not on the PATH.
            ColorError: The stream is outside WP3.5's supported set.
        """
        refusals = [fault for fault in probe.faults if fault.severity == "refuse"]
        if refusals:
            raise VideoDecodeError(
                "refused",
                f"{ascii_text(probe.path.name)} is not decoded: {refusals[0].message}",
            )
        ffmpeg = find_tool("ffmpeg")
        cuda = hw_decode and cuda_decode_available()
        seek = seek_position(probe, start_s) if start_s is not None else None
        command = decode_command(probe, ffmpeg=ffmpeg, cuda=cuda, seek=seek)
        backend = self.device_backend
        if hw_decode and isinstance(backend, DeviceFrameBackend):
            return FrameStream(probe, command, start_s=start_s, end_s=end_s, device_backend=backend)
        return FrameStream(probe, command, start_s=start_s, end_s=end_s)
