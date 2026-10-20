"""A minimal reader of the GoPro camera state in a chapter's GPMF data track (WP1.4b claim 2a).

GoPro cameras record a ``gpmd`` data track (handler "GoPro MET") of GPMF telemetry: a KLV
stream in which every item is a 4-character key, a 1-byte type, a 1-byte structure size and
a 2-byte big-endian repeat count, followed by ``size * repeat`` bytes of payload padded to a
multiple of 4. Type 0 marks a nested container (``DEVC``, ``STRM``) whose payload is itself
KLV. This module decodes ONLY the six camera-state keys of :data:`CAMERA_KEYS` (shutter,
sensor ISO, white-balance temperature and RGB gains, average luma, uniformity); every other
key, including the IMU and GPS keys this project never reads, is skipped by its length
without its payload being decoded. A ``SCAL`` item in the same ``STRM``, when present, divides
the values that follow it, as GPMF specifies.

The track is copied out of the chapter with FFmpeg (``-map 0:<gpmd> -codec copy -f data``)
into the working folder; it carries GPS too, so the copy is never committed or moved
elsewhere. Timing rule (:func:`nearest`): the ``N`` samples of a key spread evenly over the
data stream's duration ``D``, sample ``k`` at ``k * D / N`` seconds, and a frame at ``t``
seconds takes sample ``round(t * N / D)`` clipped to ``[0, N - 1]``. Keys recorded once per
video frame (``SHUT``, ``ISOE`` at 30000/1001 fps) then map frame ``i`` to sample ``i``.
"""

from __future__ import annotations

import struct
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import Path

CAMERA_KEYS: tuple[str, ...] = ("SHUT", "ISOE", "WBAL", "WRGB", "YAVG", "UNIF")
"""The keys decoded: shutter (s), sensor ISO, white-balance temperature (K), the camera's
white-balance R, G, B gains, average luma (0-255), image uniformity."""

_FORMATS = {"b": "b", "B": "B", "s": "h", "S": "H", "l": "i", "L": "I", "f": "f", "d": "d"}
"""GPMF type character to :mod:`struct` code, for the numeric types the six keys and
``SCAL`` use."""

_NESTED = 0


@dataclass(frozen=True)
class Item:
    """One KLV item: its key, type character, structure size, repeat count and payload.

    Attributes:
        key: The 4-character key.
        type: The type character (the NUL character for a nested container).
        size: The size in bytes of one structure (one sample).
        repeat: The number of structures.
        payload: The ``size * repeat`` payload bytes, without the padding.
    """

    key: str
    type: str
    size: int
    repeat: int
    payload: bytes


def items(data: bytes) -> Iterator[Item]:
    """Walk one level of KLV, yielding each item; padding is skipped, nothing is decoded.

    Args:
        data: The KLV bytes of one level.

    Yields:
        The items in order.

    Raises:
        ValueError: An item header or payload runs past the end of ``data``.
    """
    offset = 0
    while offset + 8 <= len(data):
        key = data[offset : offset + 4].decode("latin-1")
        type_, size = data[offset + 4], data[offset + 5]
        (repeat,) = struct.unpack(">H", data[offset + 6 : offset + 8])
        length = size * repeat
        end = offset + 8 + length
        if end > len(data):
            raise ValueError(f"GPMF item {key!r} at byte {offset} runs past the data")
        yield Item(key, chr(type_), size, repeat, data[offset + 8 : end])
        offset = end + (-length % 4)


def decode(item: Item, scale: tuple[float, ...] = ()) -> list[tuple[float, ...]]:
    """Decode one numeric item into its samples (big-endian), applying ``SCAL`` when given.

    Args:
        item: The item; its type must be one of the numeric GPMF types.
        scale: The ``SCAL`` divisors in force: one for every element, or one per element.

    Returns:
        One tuple of element values per sample.

    Raises:
        ValueError: The type is not numeric or the structure size is not a whole number of
            elements.
    """
    code = _FORMATS.get(item.type)
    if code is None:
        raise ValueError(f"GPMF key {item.key!r} has non-numeric type {item.type!r}")
    width = struct.calcsize(code)
    if item.size % width:
        raise ValueError(f"GPMF key {item.key!r}: size {item.size} is not a multiple of {width}")
    count = item.size // width
    values = struct.unpack(f">{count * item.repeat}{code}", item.payload)
    samples = []
    for start in range(0, len(values), count):
        sample = values[start : start + count]
        if scale:
            divisors = scale if len(scale) == count else scale[:1] * count
            sample = tuple(value / divisor for value, divisor in zip(sample, divisors, strict=True))
        samples.append(tuple(float(value) for value in sample))
    return samples


def read_camera_state(data: bytes) -> dict[str, list[tuple[float, ...]]]:
    """Collect every sample of the six camera-state keys from a whole ``gpmd`` track.

    Nested containers are walked; in each ``STRM`` the ``SCAL`` seen so far applies to the
    camera-state key that follows. Any other key is passed over by its length.

    Args:
        data: The track as copied out by FFmpeg (the concatenated packets).

    Returns:
        Per key of :data:`CAMERA_KEYS` that occurs, its samples in track order.
    """
    found: dict[str, list[tuple[float, ...]]] = {}

    def walk(level: bytes) -> None:
        scale: tuple[float, ...] = ()
        for item in items(level):
            if ord(item.type) == _NESTED:
                walk(item.payload)
            elif item.key == "SCAL":
                scale = tuple(value[0] for value in decode(item))
            elif item.key in CAMERA_KEYS:
                found.setdefault(item.key, []).extend(decode(item, scale))

    walk(data)
    return found


def nearest(
    samples: list[tuple[float, ...]], duration_s: float, time_s: float
) -> tuple[float, ...]:
    """Return the sample nearest in time to ``time_s`` under the module's timing rule.

    Args:
        samples: The key's samples over the whole track.
        duration_s: The data stream's duration in seconds.
        time_s: The frame's presentation time in seconds.

    Returns:
        Sample ``round(time_s * N / duration_s)``, clipped to the valid range.

    Raises:
        ValueError: There are no samples or the duration is not positive.
    """
    if not samples or duration_s <= 0.0:
        raise ValueError("no samples, or a non-positive stream duration")
    index = round(time_s * len(samples) / duration_s)
    return samples[min(max(index, 0), len(samples) - 1)]


def state_at(
    state: dict[str, list[tuple[float, ...]]], duration_s: float, time_s: float
) -> dict[str, float | list[float]]:
    """Return the six keys' values for one frame (a one-element sample becomes a number).

    Args:
        state: :func:`read_camera_state`'s result.
        duration_s: The data stream's duration in seconds.
        time_s: The frame's presentation time in seconds.

    Returns:
        Per key present, its nearest sample.
    """
    out: dict[str, float | list[float]] = {}
    for key in CAMERA_KEYS:
        if key in state:
            sample = nearest(state[key], duration_s, time_s)
            out[key] = sample[0] if len(sample) == 1 else list(sample)
    return out


def read_track(path: Path) -> dict[str, list[tuple[float, ...]]]:
    """Read a ``gpmd`` track file copied out by FFmpeg and collect the camera state.

    Args:
        path: The track file (in the working folder).

    Returns:
        :func:`read_camera_state` of its bytes.
    """
    return read_camera_state(path.read_bytes())
