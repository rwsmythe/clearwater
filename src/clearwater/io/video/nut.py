"""The timestamped carrier for raw frames on the encoder's input pipe (WP3.10).

Raw video on a pipe has no timestamps, so the sink frames each planar RGB frame as one packet of
a minimal NUT stream (the FFmpeg-native container with a rational time base, so a ``1/30000``
tick is exact). NUT has no per-frame duration: FFmpeg would make one up for the last frame from
the frame rate, which is wrong on a variable-frame-rate source. So the sink ends the stream with
a one-byte SENTINEL packet at the end time of the last frame, and FFmpeg reads the pipe through
:data:`INPUT_BITSTREAM_FILTER`, which sets every packet's duration to the step to the next
packet (the last real frame's step ends at the sentinel) and then drops every packet smaller
than two bytes, which removes the sentinel before the decoder.

**Invariant:** a real frame is never smaller than :data:`MIN_FRAME_BYTES`, so the drop removes
the sentinel and nothing else. :func:`frame_header` refuses a smaller payload, and a planar RGB
frame is ``3 x width x height`` samples of one or two bytes, at least 3 bytes.

The stream is: the file id, a main header (version 3, one time base: the source video's), one
rawvideo stream header (``gbrp`` or ``gbrp10le`` by codec tag), a stream INFO packet naming the
source frame rate (FFmpeg's stream probing of a 4K pipe sees about one frame and cannot estimate
a rate, and the MP4 timecode writer then fails), and per frame a syncpoint followed by a frame
header carrying the full pts and a CRC. The payload is written by the caller after the header,
so a frame is never copied into a larger buffer.

The checksums are CRC-32 with polynomial ``0x04C11DB7``, MSB first, initial value 0, stored big
endian (the NUT specification; checked against FFmpeg's own NUT bytes in the WP3.10 round-0
spike).
"""

from __future__ import annotations

import struct
from fractions import Fraction

FILE_ID = b"nut/multimedia container\x00"
"""The NUT file identification string, written once at the start."""

MIN_FRAME_BYTES = 2
"""The smallest real frame payload; anything smaller is dropped by the input filter."""

SENTINEL_PAYLOAD = b"\x00"
"""The one-byte payload of the end sentinel."""

INPUT_BITSTREAM_FILTER = (
    r"setts=duration=if(eq(NEXT_PTS\,NOPTS)\,DURATION\,NEXT_PTS-PTS),"
    r"noise=drop=lt(size\,2)"
)
"""The ``-bsf:v`` chain FFmpeg applies to the pipe input: duration = next pts - pts, then the
sentinel (the only packet under :data:`MIN_FRAME_BYTES`) is dropped."""

_MAIN = 0x7A561F5F04AD + ((ord("N") << 8 | ord("M")) << 48)
_STREAM = 0x11405BF2F9DB + ((ord("N") << 8 | ord("S")) << 48)
_INFO = 0xAB68B596BA78 + ((ord("N") << 8 | ord("I")) << 48)
_SYNC = 0xE4ADEECA4569 + ((ord("N") << 8 | ord("K")) << 48)

_FLAG_KEY = 1
_FLAG_CODED_PTS = 8
_FLAG_STREAM_ID = 16
_FLAG_SIZE_MSB = 32
_FLAG_CHECKSUM = 64

_MSB_PTS_SHIFT = 15
_LONG_HEADER = 4096
"""A packet whose forward pointer exceeds this carries a header checksum (NUT specification)."""

_TAGS = {8: b"G3\x00\x08", 10: b"G3\x00\x0a"}
"""The rawvideo codec tags of ``gbrp`` and ``gbrp10le``."""


def _crc_table() -> tuple[int, ...]:
    """Build the byte table of the MSB-first CRC-32 with polynomial ``0x04C11DB7``."""
    table = []
    for byte in range(256):
        value = byte << 24
        for _ in range(8):
            value = ((value << 1) ^ 0x04C11DB7) if value & 0x80000000 else (value << 1)
            value &= 0xFFFFFFFF
        table.append(value)
    return tuple(table)


_CRC_TABLE = _crc_table()


def crc32(data: bytes) -> int:
    """Return NUT's CRC-32 of ``data`` (MSB first, initial value 0).

    Args:
        data: The bytes to check.

    Returns:
        The 32-bit checksum.
    """
    value = 0
    for byte in data:
        value = ((value << 8) & 0xFFFFFFFF) ^ _CRC_TABLE[((value >> 24) ^ byte) & 0xFF]
    return value


def _v(value: int) -> bytes:
    """Encode an unsigned NUT variable-length integer (7 bits per byte, high bit = more)."""
    if value < 0:
        raise ValueError(f"a NUT unsigned value cannot be negative: {value}")
    out = [value & 0x7F]
    value >>= 7
    while value:
        out.append(0x80 | (value & 0x7F))
        value >>= 7
    return bytes(reversed(out))


def _s(value: int) -> bytes:
    """Encode a signed NUT variable-length integer."""
    return _v(2 * value - 1 if value > 0 else -2 * value)


def _packet(startcode: int, content: bytes) -> bytes:
    """Frame one NUT header packet: startcode, forward pointer, content and checksum."""
    forward = len(content) + 4
    head = struct.pack(">Q", startcode) + _v(forward)
    if forward > _LONG_HEADER:
        head += struct.pack(">I", crc32(head))
    return head + content + struct.pack(">I", crc32(content))


def stream_header(
    *, width: int, height: int, bit_depth: int, time_base: Fraction, frame_rate: Fraction
) -> bytes:
    """Return the bytes that open the stream: file id, main, stream and INFO packets.

    Args:
        width: Frame width in pixels.
        height: Frame height in pixels.
        bit_depth: 8 (``gbrp``) or 10 (``gbrp10le``).
        time_base: The time base of every pts that follows (the source video's).
        frame_rate: The source's average frame rate, written as the stream's ``r_frame_rate``.

    Returns:
        The header bytes.

    Raises:
        ValueError: A size, the bit depth, the time base or the frame rate is out of range.
    """
    if width < 1 or height < 1:
        raise ValueError(f"frame size {width}x{height} is empty")
    if bit_depth not in _TAGS:
        raise ValueError(f"bit depth {bit_depth} has no rawvideo tag; supported: 8, 10")
    if time_base <= 0 or frame_rate <= 0:
        raise ValueError(f"time base {time_base} and frame rate {frame_rate} must be positive")
    flags = _FLAG_KEY | _FLAG_CODED_PTS | _FLAG_STREAM_ID | _FLAG_SIZE_MSB | _FLAG_CHECKSUM
    main = (
        _v(3)  # version
        + _v(1)  # stream count
        + _v(65536)  # max_distance
        + _v(1)  # time base count
        + _v(time_base.numerator)
        + _v(time_base.denominator)
        # One frame-code entry covering all 255 codes. Its fields: pts delta, size multiplier,
        # stream id, size lsb, reserved count, then the count of codes the entry covers.
        + _v(flags)
        + _v(6)
        + _s(0)
        + _v(1)
        + _v(0)
        + _v(0)
        + _v(0)
        + _v(255)
        + _v(0)  # header_count - 1
    )
    tag = _TAGS[bit_depth]
    stream = (
        _v(0)  # stream id
        + _v(0)  # class: video
        + _v(len(tag))
        + tag
        + _v(0)  # time base id
        + _v(_MSB_PTS_SHIFT)
        + _v(1 << 30)  # max pts distance (every frame carries a checksum anyway)
        + _v(0)  # decode delay
        + _v(0)  # stream flags
        + _v(0)  # extradata size
        + _v(width)
        + _v(height)
        + _v(1)
        + _v(1)  # sample aspect ratio 1:1 (non-square sources are refused at open)
        + _v(0)  # colourspace type
    )
    name = b"r_frame_rate"
    value = f"{frame_rate.numerator}/{frame_rate.denominator}".encode("ascii")
    info = (
        _v(1)  # stream id + 1 (this stream)
        + _s(0)  # chapter id
        + _v(0)  # chapter start
        + _v(0)  # chapter length
        + _v(1)  # count of info items
        + _v(len(name))
        + name
        + _s(-1)  # value kind -1: a UTF-8 string
        + _v(len(value))
        + value
    )
    return FILE_ID + _packet(_MAIN, main) + _packet(_STREAM, stream) + _packet(_INFO, info)


def frame_header(pts: int, size: int) -> bytes:
    """Return the syncpoint and frame header that precede one frame's payload.

    Args:
        pts: The frame's presentation time in time-base ticks (non-negative).
        size: The payload size in bytes; at least :data:`MIN_FRAME_BYTES` (the invariant).

    Returns:
        The bytes to write before the payload.

    Raises:
        ValueError: The pts is negative or the payload is smaller than a real frame can be.
    """
    if size < MIN_FRAME_BYTES:
        raise ValueError(
            f"a frame payload of {size} bytes is under {MIN_FRAME_BYTES} and would be dropped "
            "as the end sentinel"
        )
    return _header(pts, size)


def sentinel(pts: int) -> bytes:
    """Return the complete end-sentinel packet at ``pts`` (the end time of the last frame).

    Args:
        pts: The end of the last frame in time-base ticks; greater than that frame's pts.

    Returns:
        The syncpoint, frame header and one-byte payload.

    Raises:
        ValueError: The pts is negative.
    """
    return _header(pts, len(SENTINEL_PAYLOAD)) + SENTINEL_PAYLOAD


def _header(pts: int, size: int) -> bytes:
    """Build a syncpoint plus a frame header for one packet of ``size`` bytes at ``pts``."""
    if pts < 0:
        raise ValueError(f"a pts cannot be negative on the encode pipe: {pts}")
    sync = _packet(_SYNC, _v(pts) + _v(0))  # global key pts (one time base), back pointer 0
    head = bytes([0]) + _v(0) + _v(pts + (1 << _MSB_PTS_SHIFT)) + _v(size)
    return sync + head + struct.pack(">I", crc32(head))
