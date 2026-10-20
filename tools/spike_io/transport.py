"""WP2.1S transport instrument: decode GX011627 to NumPy through each candidate transport.

Every row decodes the same frames with the same conversion as the prototype's raw pipe
(:func:`prototype.clip.decode_command`: tag-driven ``scale`` with ``accurate_rnd`` to
``rgb24``) and ends each frame as a C-contiguous ``uint8`` array of shape ``(H, W, 3)`` in
this process. The rows (:data:`ROWS`):

- ``a``: today's pipe, ``decode_command`` as-is through CPython's default anonymous pipe,
  read with :func:`prototype.clip.read_frame` into one buffer from
  :func:`prototype.clip.frame_buffer` (``readinto`` into a preallocated frame);
- ``a-*``: row ``a`` with the FFmpeg-side knobs ``-avioflags direct`` and the pipe
  protocol's ``-blocksize``, alone and combined;
- ``b``: the same command into an anonymous pipe created with a 32 MiB buffer (``b-1m``:
  1 MiB), read the same way; ``b-cuda`` adds ``-hwaccel cuda``;
- ``b-fallback+pts``: ``b+pts`` with the large pipe forced to fail, which falls back to
  CPython's default pipe automatically (the portable path; CHARC ``871d4f17e78c10b3``);
- ``s``: the same command writing to a loopback TCP socket that this process listens on;
- ``c``: PyAV in-process decode, converted with ``VideoFrame.reformat`` to ``rgb24`` with
  the same matrix, range and swscale flag (PyAV's default threading; ``c-auto``:
  ``thread_type="AUTO"``; ``c-cuda*``: CUDA hardware decode).

A ``+pts`` suffix turns on the pts side channel of an FFmpeg-process row (``showinfo`` on
standard error, parsed after the run); PyAV rows always carry the decoder's pts.

Timing (:func:`timed_run`): the bracket opens just before the FFmpeg process is spawned
(or the PyAV container is opened) and closes when the last frame is whole in its array;
s/frame is the bracket divided by the frame count. Each frame's interval runs from the end
of the previous frame's handling to its own arrival, so the SHA-256 witness taken on every
:data:`WITNESS_EVERY`-th frame and the last (compared with row ``a``'s reference) is left
out of the bracket: the bracket is the sum of the intervals. The producer is not stopped
during a hash: FFmpeg keeps writing into a pipe or socket buffer (more than a whole frame for
the 32 MiB pipe) and PyAV's decoder threads keep decoding, so work done during a hash is out
of the bracket. The bracket is therefore a lower bound and the wall time including the
hashes (``wall_s_with_witness``) an upper bound on the decode-to-NumPy time without hashing.

Identity (:func:`identity_run`, untimed): every frame's SHA-256 and the delivered pts are
compared with the reference (row ``a``'s hashes and ffprobe's per-frame pts); a row whose
bytes differ is re-decoded in lockstep with row ``a`` for the differing-frame count, the
largest and mean absolute difference and the fraction of differing samples.

Windows (:func:`run_window`): an advisory idle gate, an opening and a closing probe (row
``a`` on its first :data:`PROBE_FRAMES` frames), a 10 s psutil stray check between runs
(the check after one run is the check before the next: nothing runs between them), the
card's state and the ambient record. A window is contaminated when the closing probe
drifts more than :data:`PROBE_DRIFT_LIMIT` from the opening one or a stray check lists a
process outside :data:`SYSTEM_PROCESSES` at :data:`STRAY_LIMIT_PERCENT` % or more of one
logical CPU.

Every FFmpeg command here writes to a pipe or a socket only; the records go under
``<working folder>/wp2.1s/transport/``. Windows-only elements (spec N1): the large pipe
buffer (``_winapi.CreatePipe``; elsewhere a plain ``os.pipe``, with ``F_SETPIPE_SZ`` where
Linux offers it), the idle gate (PowerShell) and the power-plan reading.

Run from the repository root: ``uv run python tools/spike_io/transport.py <command> ...``.
"""

from __future__ import annotations

import argparse
import contextlib
import datetime
import hashlib
import json
import os
import socket
import statistics
import subprocess
import sys
import threading
import time
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import IO, Any, cast

import numpy as np
import psutil
from numpy.typing import NDArray

if not __package__:
    # Script mode: sys.path[0] is tools/spike_io; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from container_spike.compare import run_ffprobe, tool_env
from local_config import find_footage_file, load_local_config
from prototype import bench, clip

WORK_SUBDIR = "wp2.1s"
"""The folder inside the working folder that every output of this package goes to."""

CLIP_STEM = "GX011627"
"""The only clip of this spike (CHARC ``fa9d637063376263``)."""

PROBE_FRAMES = 120
"""The window probe: row ``a`` on this many frames from the start."""

WITNESS_EVERY = 30
"""A timed run hashes every this-many-th frame and the last (outside the bracket)."""

PROBE_DRIFT_LIMIT = 0.10
"""A closing probe further than this fraction from the opening one contaminates a window."""

STRAY_LIMIT_PERCENT = 25.0
"""A non-system process at this % of one logical CPU in a stray check contaminates."""

SYSTEM_PROCESSES = frozenset(
    {
        "System",
        "Registry",
        "MemCompression",
        "smss.exe",
        "csrss.exe",
        "wininit.exe",
        "winlogon.exe",
        "services.exe",
        "lsass.exe",
        "svchost.exe",
        "dwm.exe",
        "audiodg.exe",
        "MsMpEng.exe",
        "WmiPrvSE.exe",
    }
)
"""Windows' own processes, not counted as strays (every listed process is still recorded)."""

BIG_PIPE_BYTES = 1 << 25
"""The large pipe buffer of the ``b`` rows: 32 MiB, more than one 4K ``rgb24`` frame
(24,883,200 bytes). The one size the large-buffer transport uses (a Windows platform tuning,
spec N1). Measured on GX011627 (W4, 2026-10-20, clean): row ``b`` 16.11 ms/frame (15.98-16.46),
``b-cuda`` 12.99 ms, against 55.87 ms for row ``a`` (CPython's default pipe, W2); a 1 MiB
buffer gave 16.54 ms (``b-1m``, W1, one run). When the buffer cannot be created the transport
falls back to the default pipe (:meth:`Transport._ffmpeg_frames`; row ``b-fallback+pts``)."""

EXPLORE_PIPE_BYTES = 1 << 20
"""The 1 MiB buffer of the exploration row ``b-1m`` only."""

SOCKET_RECEIVE_BYTES = 1 << 25
"""Row ``s``'s requested socket receive buffer."""

KNOB_BLOCKSIZE = str(1 << 25)
"""The value given to the pipe protocol's ``-blocksize`` (its default is ``INT_MAX``)."""

SWS_ACCURATE_RND = 0x40000
"""swscale's ``SWS_ACCURATE_RND``: the decode chain's ``flags=accurate_rnd``, as an integer."""

AD10_FLAGS = "accurate_rnd+full_chroma_int+bitexact"
"""The swscale flags AD-10 names for the product (row ``a-ad10``: an untimed finding)."""

ACCEPT_TIMEOUT_S = 60.0
"""Seconds row ``s`` waits for FFmpeg to connect."""

_PYAV_MATRICES = {"bt709": "itu709", "smpte170m": "itu601", "bt470bg": "itu601"}
_PYAV_RANGES = {"pc": "JPEG", "tv": "MPEG"}

_STATISTICS_PREFIX = "Statistics: "


class SpikeError(Exception):
    """A run failed, delivered another number of frames, or a check refused."""


@dataclass(frozen=True)
class Row:
    """One transport candidate.

    Attributes:
        name: The row's name in the records.
        kind: ``"pipe"`` or ``"socket"`` (an FFmpeg process) or ``"pyav"`` (in-process).
        hwaccel: ``"none"`` or ``"cuda"``.
        pts: FFmpeg rows: put ``showinfo`` first in the chain (the pts side channel).
        pipe_buffer: Pipe rows: the pipe's buffer in bytes; 0 for CPython's default pipe.
        output_options: Extra FFmpeg output options, placed before ``-f rawvideo``.
        vf_flags: Replace the chain's ``flags=accurate_rnd`` with these flags.
        thread_type: PyAV rows: the decoder's ``thread_type``; ``None`` for PyAV's default.
        force_fallback: Pipe rows with a buffer: make creating the large pipe fail, to show
            the automatic fallback to the default pipe.
    """

    name: str
    kind: str
    hwaccel: str = "none"
    pts: bool = False
    pipe_buffer: int = 0
    output_options: tuple[str, ...] = ()
    vf_flags: str | None = None
    thread_type: str | None = None
    force_fallback: bool = False


def _rows() -> dict[str, Row]:
    """Build :data:`ROWS`."""
    direct = ("-avioflags", "direct")
    block = ("-blocksize", KNOB_BLOCKSIZE)
    rows = [
        Row("a", "pipe"),
        Row("a+pts", "pipe", pts=True),
        Row("a-direct", "pipe", output_options=direct),
        Row("a-blocksize", "pipe", output_options=block),
        Row("a-direct-blocksize", "pipe", output_options=direct + block),
        Row("a-direct+pts", "pipe", pts=True, output_options=direct),
        Row("a-blocksize+pts", "pipe", pts=True, output_options=block),
        Row("a-direct-blocksize+pts", "pipe", pts=True, output_options=direct + block),
        Row("a-ad10", "pipe", vf_flags=AD10_FLAGS),
        Row("b-1m", "pipe", pipe_buffer=EXPLORE_PIPE_BYTES),
        Row("b-1m+pts", "pipe", pts=True, pipe_buffer=EXPLORE_PIPE_BYTES),
        Row("b", "pipe", pipe_buffer=BIG_PIPE_BYTES),
        Row(
            "b-direct-blocksize", "pipe", pipe_buffer=BIG_PIPE_BYTES, output_options=direct + block
        ),
        Row(
            "b-direct-blocksize+pts",
            "pipe",
            pts=True,
            pipe_buffer=BIG_PIPE_BYTES,
            output_options=direct + block,
        ),
        Row("b+pts", "pipe", pts=True, pipe_buffer=BIG_PIPE_BYTES),
        Row("b-fallback+pts", "pipe", pts=True, pipe_buffer=BIG_PIPE_BYTES, force_fallback=True),
        Row("b-cuda", "pipe", hwaccel="cuda", pipe_buffer=BIG_PIPE_BYTES),
        Row("b-cuda+pts", "pipe", hwaccel="cuda", pts=True, pipe_buffer=BIG_PIPE_BYTES),
        Row("s", "socket"),
        Row("s+pts", "socket", pts=True),
        Row("c", "pyav"),
        Row("c-auto", "pyav", thread_type="AUTO"),
        Row("c-cuda", "pyav", hwaccel="cuda"),
        Row("c-cuda-auto", "pyav", hwaccel="cuda", thread_type="AUTO"),
    ]
    return {row.name: row for row in rows}


ROWS = _rows()
"""Every row by name. The ``+pts`` forms of the exploration rows (``a-direct``,
``a-blocksize``, ``a-direct-blocksize``, ``b-1m``, ``b-direct-blocksize``) are identity
rows only: they check the pts side channel under each knob, untimed."""

NULL_ROW = "n"
"""The calibration row: decode and convert to FFmpeg's ``null`` muxer (:func:`null_run`)."""

PLANS: dict[str, tuple[tuple[str, int], ...]] = {
    "explore": (
        ("a-direct", 1),
        ("a-blocksize", 1),
        ("a-direct-blocksize", 1),
        ("b-1m", 1),
        ("b", 1),
        ("b-direct-blocksize", 1),
    ),
    "pipes-a": ((NULL_ROW, 3), ("a", 3)),
    "pipes-apts": (("a+pts", 3),),
    "pipes-b": (("b", 3), ("b+pts", 3), ("b-cuda", 3), ("b-cuda+pts", 3)),
    "others-s": (("s", 3), ("s+pts", 3), ("c", 3)),
    "others-c": (("c-auto", 3), ("c-cuda", 3), ("c-cuda-auto", 3)),
}
"""The timed windows: (row, full-clip runs) in order; each fits in under 10 minutes."""


# --- the transports -------------------------------------------------------------------------


class _CountingReader:
    """A raw stream whose ``readinto`` records the size of every read (the observed block)."""

    def __init__(self, raw: Any) -> None:
        """Wrap ``raw`` (an unbuffered stream with ``readinto``)."""
        self._raw = raw
        self.sizes: list[int] = []

    def readinto(self, view: Any) -> int:
        """Read into ``view`` and record how many bytes came."""
        count = int(self._raw.readinto(view) or 0)
        if count:
            self.sizes.append(count)
        return count


def read_sizes(sizes: Sequence[int]) -> dict[str, Any]:
    """Summarise the sizes of the reads of a run.

    Args:
        sizes: Every read's byte count.

    Returns:
        Count, total, largest, median and the share of bytes read in blocks of 1 MiB or more.
    """
    if not sizes:
        return {"reads": 0, "bytes": 0, "largest": 0, "median": 0, "share_1mib_plus": 0.0}
    total = int(sum(sizes))
    large = int(sum(size for size in sizes if size >= 1 << 20))
    return {
        "reads": len(sizes),
        "bytes": total,
        "largest": int(max(sizes)),
        "median": float(statistics.median(sizes)),
        "share_1mib_plus": large / total,
    }


def avio_statistics(stderr: str) -> dict[str, Any] | None:
    """Return FFmpeg's output AVIO statistics (bytes written and write calls), if logged.

    FFmpeg logs ``Statistics: <n> bytes written, <s> seeks, <w> writeouts`` at ``verbose``
    level when it closes its output; ``bytes / writeouts`` is the size of its writes.

    Args:
        stderr: FFmpeg's standard error.

    Returns:
        ``{"bytes_written", "writeouts", "mean_write_bytes"}``, or ``None`` if absent.
    """
    for line in stderr.splitlines():
        if _STATISTICS_PREFIX in line and "bytes written" in line:
            words = line.split(_STATISTICS_PREFIX, 1)[1].replace(",", "").split()
            written, writeouts = int(words[0]), int(words[words.index("writeouts") - 1])
            return {
                "bytes_written": written,
                "writeouts": writeouts,
                "mean_write_bytes": written / writeouts if writeouts else None,
            }
    return None


def ffmpeg_command(row: Row, source: clip.Source, frames: int | None, verbose: bool) -> list[str]:
    """Return a row's FFmpeg command: ``decode_command`` with the row's changes.

    Args:
        row: An FFmpeg-process row.
        source: The clip.
        frames: Decode only this many frames; ``None`` for all.
        verbose: Log at ``verbose`` level (for the AVIO write statistics).

    Returns:
        The command; its output is ``pipe:1`` or, for a socket row, the placeholder
        ``tcp://127.0.0.1:{port}`` filled in when the socket is listening.

    Raises:
        SpikeError: The row is not an FFmpeg row, or its flag change found no flags.
    """
    if row.kind not in ("pipe", "socket"):
        raise SpikeError(f"row {row.name} is not an FFmpeg-process row")
    command = clip.decode_command(source, row.hwaccel, frames, showinfo=row.pts)
    if verbose:
        command[command.index("-loglevel") + 1] = "verbose"
    if row.vf_flags is not None:
        at = command.index("-vf") + 1
        if "flags=accurate_rnd" not in command[at]:
            raise SpikeError(f"no flags=accurate_rnd in {command[at]!r}")
        command[at] = command[at].replace("flags=accurate_rnd", f"flags={row.vf_flags}")
    at = command.index("-f")
    command[at:at] = list(row.output_options)
    if command[-1] != "pipe:1":
        raise SpikeError(f"decode_command no longer ends with pipe:1: {command[-1]!r}")
    if row.kind == "socket":
        command[-1] = "tcp://127.0.0.1:{port}"
    return command


def _big_pipe(size: int, force_failure: bool = False) -> tuple[int, int]:
    """Create an anonymous pipe with a ``size``-byte buffer; return (read fd, write fd).

    Windows: ``_winapi.CreatePipe`` with ``nSize`` (CPython's own pipe passes 0, the system
    default). Elsewhere a plain ``os.pipe``, enlarged with ``F_SETPIPE_SZ`` where Linux
    offers it.

    Raises:
        OSError: The pipe cannot be created (always, with ``force_failure``).
    """
    if force_failure:
        raise OSError("large pipe creation forced to fail (fallback demonstration)")
    if sys.platform == "win32":
        import _winapi
        import msvcrt

        read_handle, write_handle = _winapi.CreatePipe(None, size)
        return (
            msvcrt.open_osfhandle(read_handle, os.O_RDONLY),
            msvcrt.open_osfhandle(write_handle, 0),
        )
    else:
        import fcntl

        read_fd, write_fd = os.pipe()
        setter = getattr(fcntl, "F_SETPIPE_SZ", None)
        if setter is not None:
            with contextlib.suppress(OSError):
                fcntl.fcntl(write_fd, setter, size)
        return read_fd, write_fd


class Transport:
    """One decode of the clip through one row's transport: an iterator of whole frames.

    Use as a context manager; iterate :meth:`frames`; then call :meth:`finish` for the
    exit status, the side channel's pts and the observed block sizes.
    """

    def __init__(
        self, row: Row, source: clip.Source, frames: int | None = None, verbose: bool = False
    ) -> None:
        """Prepare the decode (nothing starts until :meth:`frames` is iterated).

        Args:
            row: The row.
            source: The clip.
            frames: Decode only this many frames; ``None`` for all.
            verbose: FFmpeg rows: log at ``verbose`` level (AVIO write statistics).
        """
        self.row, self.source, self.frames_wanted, self.verbose = row, source, frames, verbose
        self.command: list[str] | None = None
        self.pts: list[int] = []
        self._process: subprocess.Popen[bytes] | None = None
        self._stderr: list[bytes] = []
        self._drain: threading.Thread | None = None
        self._counter: _CountingReader | None = None
        self._closers: list[Any] = []
        self._container: Any = None
        self._pipe_fds: tuple[int, int] = (-1, -1)
        self.pipe_fallback: str | None = None

    def __enter__(self) -> Transport:
        """Return the transport."""
        return self

    def __exit__(self, *exc: object) -> None:
        """Stop whatever is still running."""
        self.close()

    def close(self) -> None:
        """Kill a still-running FFmpeg process and close every stream (after a failure too)."""
        if self._process is not None and self._process.poll() is None:
            self._process.kill()
            self._process.wait()
        for closer in reversed(self._closers):
            with contextlib.suppress(OSError):
                closer.close()
        self._closers.clear()
        if self._container is not None:
            self._container.close()
            self._container = None

    def frames(self) -> Iterator[NDArray[np.uint8]]:
        """Start the decode and yield every frame, whole, as a ``(H, W, 3)`` ``uint8`` array.

        FFmpeg rows yield the same buffer each time (valid until the next frame is asked
        for); PyAV rows yield a fresh array per frame.
        """
        if self.row.kind == "pyav":
            yield from self._pyav_frames()
        else:
            yield from self._ffmpeg_frames()

    def _spawn(self, command: list[str], stdout: int) -> None:
        """Start FFmpeg with standard error drained into memory by a thread."""
        self.command = command
        self._process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=stdout,
            stderr=subprocess.PIPE,
            env=tool_env(),
            bufsize=0,
        )
        stderr = self._process.stderr
        if stderr is None:  # pragma: no cover - stderr=PIPE always gives a stream
            raise SpikeError("FFmpeg has no standard error stream")
        self._drain = threading.Thread(
            target=lambda: self._stderr.append(stderr.read()), daemon=True
        )
        self._drain.start()

    def _ffmpeg_frames(self) -> Iterator[NDArray[np.uint8]]:
        """Decode through an FFmpeg process into a pipe or a socket."""
        command = ffmpeg_command(self.row, self.source, self.frames_wanted, self.verbose)
        stream: Any
        if self.row.kind == "socket":
            server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._closers.append(server)
            # Set before listen() so the accepted connection starts with this buffer.
            server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, SOCKET_RECEIVE_BYTES)
            server.bind(("127.0.0.1", 0))
            server.listen(1)
            server.settimeout(ACCEPT_TIMEOUT_S)
            command[-1] = command[-1].format(port=server.getsockname()[1])
            self._spawn(command, subprocess.DEVNULL)
            connection, _ = server.accept()
            connection.settimeout(None)
            self._closers.append(connection)
            stream = connection.makefile("rb", buffering=0)
            self._closers.append(stream)
        elif self.row.pipe_buffer and self._open_big_pipe():
            read_fd, write_fd = self._pipe_fds
            try:
                self._spawn(command, write_fd)
            finally:
                os.close(write_fd)  # the child holds its own copy
            stream = open(read_fd, "rb", buffering=0)  # noqa: SIM115 - closed in close()
            self._closers.append(stream)
        else:  # the default pipe; also the automatic fallback when the large one fails
            self._spawn(command, subprocess.PIPE)
            assert self._process is not None
            stream = self._process.stdout
            self._closers.append(stream)
        self._counter = _CountingReader(stream)
        buffer = cast(NDArray[np.uint8], clip.frame_buffer(self.source))
        reader = cast(IO[bytes], self._counter)
        while clip.read_frame(reader, buffer):
            yield buffer

    def _open_big_pipe(self) -> bool:
        """Try to create the row's large pipe; on failure record why and return False."""
        try:
            self._pipe_fds = _big_pipe(self.row.pipe_buffer, self.row.force_fallback)
        except OSError as exc:
            self.pipe_fallback = f"{type(exc).__name__}: {exc}"
            return False
        return True

    def _pyav_frames(self) -> Iterator[NDArray[np.uint8]]:
        """Decode in-process with PyAV and convert each frame as the FFmpeg chain does."""
        import av
        from av.codec.hwaccel import HWAccel

        tags = self.source.info.tags
        matrix = _PYAV_MATRICES.get(tags.color_space)
        color_range = _PYAV_RANGES.get(tags.color_range)
        if matrix is None or color_range is None:
            raise SpikeError(f"no PyAV mapping for {tags.color_space} / {tags.color_range}")
        # PyAV applies the matrix and ranges (sws_setColorspaceDetails) only when the source
        # and destination matrices or ranges differ; for an RGB destination swscale does not
        # use the destination matrix, so a different one is named to make PyAV apply them.
        other = "itu601" if matrix == "itu709" else "itu709"
        hwaccel = (
            HWAccel("cuda", allow_software_fallback=False) if self.row.hwaccel == "cuda" else None
        )
        self._container = av.open(str(self.source.path), hwaccel=hwaccel)
        stream = self._container.streams.video[0]
        if self.row.thread_type is not None:
            stream.thread_type = self.row.thread_type
        wanted = self.frames_wanted
        for frame in self._container.decode(stream):
            rgb = frame.reformat(
                format="rgb24",
                src_colorspace=matrix,
                dst_colorspace=other,
                src_color_range=color_range,
                dst_color_range="JPEG",
                interpolation=SWS_ACCURATE_RND,
            )
            array = cast(NDArray[np.uint8], rgb.to_ndarray())
            self.pts.append(int(frame.pts))
            yield array
            if wanted is not None and len(self.pts) >= wanted:
                break

    def finish(self) -> dict[str, Any]:
        """Reap the decode and return its record (status, pts source, blocks, stderr tail).

        Raises:
            SpikeError: FFmpeg failed.
        """
        record: dict[str, Any] = {"row": self.row.name, "command": self.command}
        if self.row.kind == "pyav":
            record.update(self._pyav_record())
            self.close()
            return record
        assert self._process is not None and self._drain is not None
        status = self._process.wait(timeout=clip.PROCESS_TIMEOUT_S)
        self._drain.join(timeout=clip.PROCESS_TIMEOUT_S)
        stderr = b"".join(self._stderr).decode("utf-8", errors="replace")
        self.close()
        if status != 0:
            raise SpikeError(f"FFmpeg failed (status {status}): {stderr.strip()[-400:]}")
        seen = [
            (int(match.group(1)), int(match.group(2)))
            for match in clip.SHOWINFO_PATTERN.finditer(stderr)
        ]
        self.pts = [pts for _, pts in seen]
        record.update(
            {
                "status": status,
                "pipe_buffer_requested": self.row.pipe_buffer or None,
                "pipe_fallback": self.pipe_fallback,
                "pts_source": "showinfo on standard error" if self.row.pts else None,
                "showinfo_numbers_contiguous": [n for n, _ in seen] == list(range(len(seen))),
                "reads": read_sizes(self._counter.sizes if self._counter else []),
                "avio": avio_statistics(stderr),
                "stderr_bytes": len(stderr),
            }
        )
        return record

    def _pyav_record(self) -> dict[str, Any]:
        """The PyAV decoder's settings, read back from the codec context."""
        record: dict[str, Any] = {"status": 0, "pts_source": "PyAV frame.pts (decoder)"}
        if self._container is not None:
            context = self._container.streams.video[0].codec_context
            record.update(
                {
                    "thread_type": str(context.thread_type),
                    "thread_count": int(context.thread_count),
                    "is_hwaccel": bool(getattr(context, "is_hwaccel", False)),
                }
            )
        return record


# --- runs -------------------------------------------------------------------------------------


def witness_indices(count: int) -> set[int]:
    """Return the frames a timed run hashes: every :data:`WITNESS_EVERY`-th and the last."""
    return set(range(0, count, WITNESS_EVERY)) | {count - 1}


def _check_frame(array: NDArray[Any], source: clip.Source) -> None:
    """Refuse an array that is not a whole C-contiguous ``uint8`` ``(H, W, 3)`` frame."""
    shape = (source.info.height, source.info.width, 3)
    if array.shape != shape or array.dtype != np.uint8 or not array.flags.c_contiguous:
        raise SpikeError(
            f"frame arrived as {array.shape} {array.dtype} "
            f"(C-contiguous: {array.flags.c_contiguous}); wanted {shape} uint8 C-contiguous"
        )


def _sha256(array: NDArray[Any]) -> str:
    """The SHA-256 of a frame's bytes."""
    return hashlib.sha256(memoryview(array).cast("B")).hexdigest()


def summary(values: Sequence[float]) -> dict[str, float]:
    """Return min, median and max of ``values``."""
    return {
        "min": float(min(values)),
        "median": float(statistics.median(values)),
        "max": float(max(values)),
    }


def pts_check(delivered: Sequence[int], reference: Sequence[int]) -> dict[str, Any]:
    """Compare a row's delivered pts with ffprobe's per-frame list.

    Args:
        delivered: The pts the row delivered, in arrival order (empty: no side channel).
        reference: ffprobe's per-frame pts for the decoded frames.

    Returns:
        ``{"delivered", "exact", "first_mismatch"}``; ``exact`` is None with no side channel.
    """
    if not delivered:
        return {"delivered": 0, "exact": None, "first_mismatch": None}
    mismatch = next(
        (i for i, (got, want) in enumerate(zip(delivered, reference, strict=False)) if got != want),
        None,
    )
    if mismatch is None and len(delivered) != len(reference):
        mismatch = min(len(delivered), len(reference))
    return {
        "delivered": len(delivered),
        "exact": mismatch is None,
        "first_mismatch": None
        if mismatch is None
        else {
            "index": mismatch,
            "got": delivered[mismatch] if mismatch < len(delivered) else None,
            "want": reference[mismatch] if mismatch < len(reference) else None,
        },
    }


def timed_run(
    row: Row,
    source: clip.Source,
    reference: Mapping[str, Any],
    frames: int | None = None,
) -> dict[str, Any]:
    """Decode through ``row`` once, timing each frame's arrival as a whole array.

    Args:
        row: The row.
        source: The clip.
        reference: The reference record (:func:`build_reference`): hashes and pts.
        frames: Only the first this many frames (a probe); ``None`` for the whole clip.

    Returns:
        The run's record: bracket, s/frame, per-frame intervals, witness and pts checks.

    Raises:
        SpikeError: The decode failed or delivered another number of frames or bad arrays.
    """
    expected = source.frame_count if frames is None else min(frames, source.frame_count)
    witness = witness_indices(expected)
    hashes: dict[int, str] = {}
    intervals: list[float] = []
    witness_s = 0.0
    gpu_start = bench._gpu_state()
    with Transport(row, source, frames) as transport:
        started = time.perf_counter()
        mark = started
        arrived = started
        for index, array in enumerate(transport.frames()):
            arrived = time.perf_counter()
            intervals.append(arrived - mark)
            _check_frame(array, source)
            if index in witness:
                hashes[index] = _sha256(array)
                mark = time.perf_counter()
                witness_s += mark - arrived
            else:
                mark = arrived
        wall_s = arrived - started
        record = transport.finish()
        delivered = list(transport.pts)
    if len(intervals) != expected:
        raise SpikeError(f"row {row.name} delivered {len(intervals)} frames; wanted {expected}")
    want = reference["sha256"]
    bad = sorted(index for index, digest in hashes.items() if digest != want[index])
    bracket = float(sum(intervals))
    record.update(
        {
            "frames": len(intervals),
            "bracket_s": bracket,
            "s_per_frame": bracket / len(intervals),
            "wall_s_with_witness": wall_s,
            "witness_s": witness_s,
            "first_frame_s": intervals[0],
            "steady_s_per_frame": float(sum(intervals[1:])) / max(1, len(intervals) - 1),
            "per_frame_s": summary(intervals),
            "intervals_s": intervals,
            "witness": {
                "checked": len(hashes),
                "mismatched": bad,
                "same": not bad,
            },
            "pts": pts_check(
                delivered[: len(intervals)], reference["pts_ffprobe"][: len(intervals)]
            ),
            # showinfo prints one frame more than -frames:v keeps on a partial decode.
            "side_channel_extra_entries": max(0, len(delivered) - len(intervals)),
            "gpu_state_start": gpu_start,
            "gpu_state_end": bench._gpu_state(),
        }
    )
    return record


def null_run(source: clip.Source) -> dict[str, Any]:
    """Time the decode and conversion with no transport: FFmpeg's ``null`` muxer (row ``n``).

    The calibration of Part B's "decoding to NUL" (16.2 ms/frame), written with ``-f null``
    so that no output is opened at all. s/frame is the process's wall time (spawn to exit)
    divided by the frame count.

    Args:
        source: The clip.

    Returns:
        The run's record (no frames reach Python, so no witness and no pts).

    Raises:
        SpikeError: FFmpeg failed.
    """
    command = clip.decode_command(source)
    if command[-3:] != ["-f", "rawvideo", "pipe:1"]:
        raise SpikeError(f"decode_command no longer ends with -f rawvideo pipe:1: {command[-3:]}")
    command[-3:] = ["-f", "null", "-"]
    gpu_start = bench._gpu_state()
    started = time.perf_counter()
    result = subprocess.run(
        command, stdin=subprocess.DEVNULL, capture_output=True, env=tool_env(), check=False
    )
    wall = time.perf_counter() - started
    if result.returncode != 0:
        tail = result.stderr.decode("utf-8", errors="replace").strip()[-400:]
        raise SpikeError(f"FFmpeg failed (status {result.returncode}): {tail}")
    return {
        "row": NULL_ROW,
        "command": command,
        "status": result.returncode,
        "frames": source.frame_count,
        "bracket_s": wall,
        "s_per_frame": wall / source.frame_count,
        "witness": {"checked": 0, "mismatched": [], "same": None},
        "pts": {"delivered": 0, "exact": None, "first_mismatch": None},
        "gpu_state_start": gpu_start,
        "gpu_state_end": bench._gpu_state(),
    }


def identity_run(
    row: Row, source: clip.Source, reference: Mapping[str, Any] | None
) -> dict[str, Any]:
    """Decode the whole clip through ``row`` untimed, hashing every frame.

    Args:
        row: The row.
        source: The clip.
        reference: The reference record; ``None`` while building it (row ``a`` itself).

    Returns:
        The record: every hash, the delivered pts and, against the reference, the
        frame-count, hash and pts verdicts (and a lockstep difference if bytes differ).

    Raises:
        SpikeError: The decode failed.
    """
    hashes: list[str] = []
    with Transport(row, source, verbose=row.kind != "pyav") as transport:
        for array in transport.frames():
            _check_frame(array, source)
            hashes.append(_sha256(array))
        record = transport.finish()
        delivered = list(transport.pts)
    record.update({"frames": len(hashes), "sha256": hashes, "pts_delivered": delivered})
    if reference is not None:
        want = reference["sha256"]
        differing = [i for i, digest in enumerate(hashes) if i >= len(want) or digest != want[i]]
        same = len(hashes) == len(want) and not differing
        record["identity"] = {
            "frame_count_equal": len(hashes) == len(want),
            "differing_frames": len(differing),
            "first_differing": differing[:5],
            "same_work": same,
        }
        record["pts"] = pts_check(delivered[: len(hashes)], reference["pts_ffprobe"])
        record["side_channel_extra_entries"] = max(0, len(delivered) - len(hashes))
        if not same:
            record["difference"] = lockstep_difference(row, source)
    return record


def lockstep_difference(row: Row, source: clip.Source) -> dict[str, Any]:
    """Decode ``row`` and row ``a`` side by side and measure how their frames differ.

    Returns:
        Differing frames, the largest and the mean absolute sample difference (over every
        sample of the clip) and the fraction of differing samples.
    """
    differing_frames = differing_samples = samples = largest = total = 0
    with Transport(ROWS["a"], source) as reference, Transport(row, source) as candidate:
        pairs = zip(reference.frames(), candidate.frames(), strict=True)
        for want, got in pairs:
            changed = int(np.count_nonzero(want != got))
            samples += want.size
            if changed:
                differing_frames += 1
                differing_samples += changed
                diff = np.abs(want.astype(np.int16) - got.astype(np.int16))
                largest = max(largest, int(diff.max()))
                total += int(diff.sum(dtype=np.int64))
        reference.finish()
        candidate.finish()
    return {
        "differing_frames": differing_frames,
        "max_abs_difference": largest,
        "mean_abs_difference": total / samples if samples else None,
        "fraction_differing_samples": differing_samples / samples if samples else None,
    }


def ffprobe_frame_pts(source: clip.Source) -> list[int]:
    """Return ffprobe's per-frame pts of the clip's first video stream (decoded frames)."""
    document = run_ffprobe(
        ["-select_streams", "v:0", "-show_entries", "frame=pts", str(source.path)]
    )
    values = [frame.get("pts") for frame in document.get("frames", [])]
    if not values or not all(isinstance(value, int) for value in values):
        raise SpikeError("ffprobe gave a frame without an integer pts")
    return [int(value) for value in values]


def build_reference(source: clip.Source) -> dict[str, Any]:
    """Build the reference: ffprobe's per-frame pts and row ``a``'s per-frame SHA-256.

    Returns:
        ``{"pts_ffprobe", "sha256", "row_a"}`` (``row_a`` is row ``a``'s identity record).
    """
    pts = ffprobe_frame_pts(source)
    row_a = identity_run(ROWS["a"], source, None)
    if row_a["frames"] != len(pts) or len(pts) != source.frame_count:
        raise SpikeError(
            f"row a gave {row_a['frames']} frames, ffprobe {len(pts)} frames, "
            f"the packets {source.frame_count}"
        )
    return {
        "clip": source.identity(),
        "pts_ffprobe": pts,
        "pts_ffprobe_equals_packet_pts": pts == list(source.pts_ticks),
        "sha256": row_a["sha256"],
        "row_a": {key: value for key, value in row_a.items() if key != "sha256"},
    }


# --- windows ----------------------------------------------------------------------------------


def _local_now() -> str:
    """The local time, to the second, with its offset."""
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def strays(check: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Return the processes in a stray check that contaminate (non-system, at the limit)."""
    return [
        dict(entry)
        for entry in check
        if str(entry.get("name")) not in SYSTEM_PROCESSES
        and float(entry.get("cpu_percent", 0.0)) >= STRAY_LIMIT_PERCENT
    ]


def _ambient() -> dict[str, Any]:
    """Power plan and overlay, AC power and battery, and the card's state now."""
    battery = psutil.sensors_battery() if hasattr(psutil, "sensors_battery") else None
    return {
        "local": _local_now(),
        **bench._windows_power(),
        "power_plugged": None if battery is None else bool(battery.power_plugged),
        "battery_percent": None if battery is None else float(battery.percent),
        "gpu_state": bench._gpu_state(),
    }


def idle_gate(script: Path, out: Path) -> dict[str, Any]:
    """Run the advisory idle gate (Part B's PowerShell script) and return its verdict line."""
    if sys.platform != "win32" or not script.is_file():
        return {"ran": False, "reason": "not Windows or no gate script"}
    result = subprocess.run(
        ["powershell", "-NoProfile", "-File", str(script), "-Out", str(out)],
        capture_output=True,
        text=True,
        timeout=600,
        check=False,
    )
    lines = [line for line in result.stdout.splitlines() if line.strip().startswith("{")]
    return {
        "ran": True,
        "status": result.returncode,
        "record": json.loads(lines[-1]) if lines else None,
        "stderr_tail": result.stderr.strip()[-300:],
    }


def run_window(
    label: str,
    plan: Sequence[tuple[str, int]],
    source: clip.Source,
    reference: Mapping[str, Any],
    out: Path,
    gate_script: Path | None,
) -> dict[str, Any]:
    """Run one timed window and write its record to ``out`` after every step.

    Args:
        label: The window's name (``W1``...).
        plan: (row, runs) in order.
        source: The clip.
        reference: The reference record.
        out: The record file (rewritten after each step, so a crash keeps what ran).
        gate_script: Part B's idle-gate script (copied into the working folder), or None.

    Returns:
        The window record, with its contamination verdict.
    """
    record: dict[str, Any] = {
        "window": label,
        "tool": "tools/spike_io/transport.py",
        "head": bench.head_record(),
        "plan": [list(step) for step in plan],
        "probe": {"row": "a", "frames": PROBE_FRAMES},
        "contamination_rule": {
            "probe_drift_limit": PROBE_DRIFT_LIMIT,
            "stray_limit_percent": STRAY_LIMIT_PERCENT,
            "system_processes": sorted(SYSTEM_PROCESSES),
        },
        "runs": [],
        "stray_checks": [],
    }

    def save() -> None:
        out.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")

    def stray_check(after: str) -> None:
        check = bench.stray_processes()
        record["stray_checks"].append(
            {"after": after, "local": _local_now(), "processes": check, "strays": strays(check)}
        )
        save()

    if gate_script is not None:
        record["idle_gate"] = idle_gate(gate_script, out.parent / "gate.jsonl")
    record["ambient_start"] = _ambient()
    started = time.perf_counter()
    stray_check("window start")
    record["probe_open"] = _probe_record(source, reference)
    stray_check("opening probe")
    for name, runs in plan:
        for attempt in range(1, runs + 1):
            run = null_run(source) if name == NULL_ROW else timed_run(ROWS[name], source, reference)
            run.update({"attempt": attempt, "end_local": _local_now()})
            record["runs"].append(run)
            stray_check(f"{name} run {attempt}")
    record["probe_close"] = _probe_record(source, reference)
    stray_check("closing probe")
    record["ambient_end"] = _ambient()
    record["machine_s"] = time.perf_counter() - started
    opened = record["probe_open"]["s_per_frame"]
    closed = record["probe_close"]["s_per_frame"]
    drift = closed / opened - 1.0
    stray_hits = [check for check in record["stray_checks"] if check["strays"]]
    record["verdict"] = {
        "probe_drift": drift,
        "drift_contaminated": abs(drift) > PROBE_DRIFT_LIMIT,
        "stray_contaminated": bool(stray_hits),
        "contaminated": abs(drift) > PROBE_DRIFT_LIMIT or bool(stray_hits),
    }
    save()
    return record


def _probe_record(source: clip.Source, reference: Mapping[str, Any]) -> dict[str, Any]:
    """Run the window probe (row ``a``, first :data:`PROBE_FRAMES` frames) and trim it."""
    run = timed_run(ROWS["a"], source, reference, frames=PROBE_FRAMES)
    run.pop("intervals_s", None)
    run["local"] = _local_now()
    return run


# --- summary ----------------------------------------------------------------------------------


def summarise(windows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """Collect every timed run per row: median and spread of s/frame, the run of record.

    The run of record is the run with the median s/frame (the lower middle of an even
    count). Each row carries the windows its runs came from and their verdicts, and the
    wall time including the witness hashes per frame (the upper bound, :func:`timed_run`).

    Args:
        windows: Window records.

    Returns:
        ``{row: {...}}``.
    """
    by_row: dict[str, list[tuple[Mapping[str, Any], Mapping[str, Any]]]] = {}
    for window in windows:
        for run in window["runs"]:
            by_row.setdefault(run["row"], []).append((window, run))
    rows: dict[str, Any] = {}
    for name, entries in by_row.items():
        ordered = sorted(entries, key=lambda entry: float(entry[1]["s_per_frame"]))
        window, record = ordered[(len(ordered) - 1) // 2]
        values = [float(run["s_per_frame"]) for _, run in entries]
        walls = [
            float(run["wall_s_with_witness"]) / int(run["frames"])
            for _, run in entries
            if "wall_s_with_witness" in run  # the null row has no frames, so no witness
        ]
        rows[name] = {
            "runs": len(entries),
            "s_per_frame": summary(values),
            "values": values,
            "wall_with_witness_s_per_frame": summary(walls) if walls else None,
            "run_of_record": {
                "window": window["window"],
                "attempt": record["attempt"],
                "s_per_frame": record["s_per_frame"],
                "per_frame_s": record.get("per_frame_s"),
                "first_frame_s": record.get("first_frame_s"),
                "steady_s_per_frame": record.get("steady_s_per_frame"),
                "reads": record.get("reads"),
            },
            "witness_same": sorted({str(run["witness"]["same"]) for _, run in entries}),
            "pts_exact": sorted({str(run["pts"]["exact"]) for _, run in entries}),
            "windows": sorted({str(w["window"]) for w, _ in entries}),
            "contaminated": sorted(
                {f"{w['window']}={w['verdict']['contaminated']}" for w, _ in entries}
            ),
        }
    return rows


# --- command line -----------------------------------------------------------------------------


def _work_folder(config_path: Path | None) -> tuple[Path, Path]:
    """Return (the footage folder, ``<working folder>/wp2.1s/transport``), refusing overlap."""
    config = load_local_config(config_path)
    work = config.working_path / WORK_SUBDIR / "transport"
    footage = config.footage_path.resolve()
    resolved = work.resolve()
    if resolved == footage or footage in resolved.parents:
        raise SpikeError(f"{work} is inside the footage folder")
    work.mkdir(parents=True, exist_ok=True)
    return config.footage_path, work


def _load(path: Path) -> dict[str, Any]:
    """Read a JSON record."""
    return cast(dict[str, Any], json.loads(path.read_text(encoding="utf-8")))


def _write(path: Path, record: Mapping[str, Any]) -> None:
    """Write a JSON record and print its path."""
    path.write_text(json.dumps(record, indent=1) + "\n", encoding="utf-8")
    print(path)


def window_label(text: str) -> str:
    """Accept a window label only if it names a file inside the records folder.

    Args:
        text: The label from the command line.

    Returns:
        The label.

    Raises:
        argparse.ArgumentTypeError: The label has anything but letters, digits, ``-`` and
            ``_`` (so no path separator and no ``..``), or starts with neither.
    """
    if not text or not text[0].isalnum() or not all(c.isalnum() or c in "-_" for c in text):
        raise argparse.ArgumentTypeError(f"label {text!r}: letters, digits, '-' and '_' only")
    if not text.isascii():
        raise argparse.ArgumentTypeError(f"label {text!r}: ASCII only")
    return text


def main(argv: Sequence[str] | None = None) -> int:
    """Run the instrument.

    Commands: ``reference`` (ffprobe pts and row ``a``'s hashes, untimed); ``identity
    ROW...`` (untimed full-clip identity per row); ``window LABEL PLAN`` (a timed window);
    ``run ROW [--frames N]`` (one timed run, a development check); ``summary WINDOW...``.

    Args:
        argv: The arguments (``None`` for ``sys.argv[1:]``).

    Returns:
        The exit status.
    """
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    parser.add_argument("--config", type=Path, default=None, help="local configuration file")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("reference", help="ffprobe pts and row a's per-frame SHA-256")
    identity = commands.add_parser("identity", help="untimed identity runs")
    identity.add_argument("rows", nargs="+", choices=sorted(ROWS))
    window = commands.add_parser("window", help="one timed window")
    window.add_argument("label", type=window_label)
    window.add_argument("plan", choices=sorted(PLANS))
    window.add_argument("--gate", type=Path, default=None, help="the idle-gate script")
    single = commands.add_parser("run", help="one timed run (development check)")
    single.add_argument("row", choices=sorted(ROWS))
    single.add_argument("--frames", type=int, default=None)
    summary_parser = commands.add_parser("summary", help="summarise window records")
    summary_parser.add_argument("windows", nargs="+", type=Path)
    args = parser.parse_args(argv)

    footage, work = _work_folder(args.config)
    if args.command == "summary":
        _write(work / "summary.json", summarise([_load(path) for path in args.windows]))
        return 0
    source = clip.open_source(find_footage_file(CLIP_STEM, footage))
    reference_path = work / "reference.json"
    if args.command == "reference":
        _write(reference_path, build_reference(source))
        return 0
    reference = _load(reference_path)
    if reference["clip"]["size_bytes"] != source.size_bytes:
        raise SpikeError("the reference belongs to another file")
    if args.command == "identity":
        for name in args.rows:
            record = identity_run(ROWS[name], source, reference)
            record["local"] = _local_now()
            _write(work / f"identity-{name}.json", record)
        return 0
    if args.command == "window":
        gate = None if args.gate is None else args.gate.resolve()
        out = work / f"{args.label}.json"
        if out.resolve().parent != work.resolve():
            raise SpikeError(f"{out} is not inside {work}")
        result = run_window(args.label, PLANS[args.plan], source, reference, out, gate)
        print(json.dumps(result["verdict"]))
        return 0
    run = timed_run(ROWS[args.row], source, reference, frames=args.frames)
    run.pop("intervals_s", None)
    _write(work / f"dev-{args.row}.json", run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
