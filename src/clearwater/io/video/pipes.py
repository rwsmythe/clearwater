"""The frame-transport pipe: an enlarged anonymous pipe with a portable fallback (WP3.9, AD-23).

FFmpeg writes raw frames to an anonymous pipe. On Windows the pipe's buffer is enlarged to
:data:`BIG_PIPE_BYTES` (AD-2, AD-23: the one approved exception to N1); when the large pipe
cannot be created, or on any other operating system, :func:`open_frame_pipe` returns None and the
caller uses the default pipe (``subprocess.PIPE``), which carries the same bytes more slowly.
The reason for the fallback is logged once per process.
"""

from __future__ import annotations

import logging
import os
import sys
import threading

_log = logging.getLogger(__name__)

BIG_PIPE_BYTES = 1 << 25
"""The enlarged pipe buffer: 32 MiB, more than one 8-bit 4K planar RGB frame (24,883,200 bytes).

Measured by WP2.1S on GX011627 (W4, 2026-10-20, clean): 16.11 ms per frame through a 32 MiB
pipe (row ``b``) against 55.87 ms through CPython's default pipe (row ``a``, W2). A 10-bit 4K
frame (49,766,400 bytes) is larger than the buffer; the transport is correct either way.
"""

_fallback_logged = False
_fallback_lock = threading.Lock()


def _create_pipe(size: int) -> tuple[int, int]:
    """Create an anonymous pipe with a ``size``-byte buffer and return (read fd, write fd).

    Raises:
        OSError: The pipe cannot be created, or the platform has no way to size it.
    """
    if sys.platform == "win32":
        import _winapi
        import msvcrt

        read_handle, write_handle = _winapi.CreatePipe(None, size)
        try:
            read_fd = msvcrt.open_osfhandle(read_handle, os.O_RDONLY)
        except OSError:
            _winapi.CloseHandle(read_handle)
            _winapi.CloseHandle(write_handle)
            raise
        try:
            write_fd = msvcrt.open_osfhandle(write_handle, 0)
        except OSError:
            os.close(read_fd)
            _winapi.CloseHandle(write_handle)
            raise
        return read_fd, write_fd
    raise OSError(f"the pipe buffer cannot be enlarged on {sys.platform}")


def _log_fallback(reason: str) -> None:
    """Log the reason for using the default pipe, the first time only."""
    global _fallback_logged
    with _fallback_lock:
        if _fallback_logged:
            return
        _fallback_logged = True
    _log.warning("using the default frame pipe: %s", reason)


def open_frame_pipe(size: int = BIG_PIPE_BYTES) -> tuple[int, int] | None:
    """Create the enlarged frame pipe, or return None for the default pipe (AD-23).

    The caller passes the write end to the child process as its standard output, closes its own
    copy of the write end once the child has started, and reads from the read end. Both ends are
    plain file descriptors owned by the caller.

    Args:
        size: The buffer size in bytes.

    Returns:
        ``(read_fd, write_fd)``, or None when the large pipe cannot be created (the reason is
        logged once per process) and the caller must use the default pipe.
    """
    try:
        return _create_pipe(size)
    except OSError as error:
        _log_fallback(f"{type(error).__name__}: {error}")
        return None
