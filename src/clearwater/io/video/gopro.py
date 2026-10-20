"""Decoder of the three GoPro settings Clearwater uses (WP3.7, AD-16).

The payload is the ``moov/udta/GPMF`` settings atom, a key-length-value stream. Exactly three
keys are decoded: ``FMWR`` (firmware), ``PRTN`` (Protune on or off) and ``PTCL`` (colour
profile). Every other item is skipped by its stated length and its bytes are never turned into
text or numbers. Items of type 0 are containers; they are entered only to reach the keys inside
them. The camera's telemetry track is never read, and no sensor, location or identifier key is
decoded.
"""

from __future__ import annotations

from clearwater.interfaces.video import GoProInfo

_FIRMWARE = b"FMWR"
_PROTUNE = b"PRTN"
_PROFILE = b"PTCL"
_WANTED = frozenset({_FIRMWARE, _PROTUNE, _PROFILE})
_TEXT_TYPE = ord("c")
_NESTED_TYPE = 0
_HEADER = 8
MAX_DEPTH = 8
"""The deepest container nesting that is entered."""


class GPMFError(ValueError):
    """The settings atom is not well-formed KLV; the message names only the structural reason."""


def _text(raw: bytes) -> str:
    """Decode a character-valued setting: up to the first NUL, stripped, Latin-1."""
    return raw.split(b"\0", 1)[0].decode("latin-1").strip()


def _walk(data: bytes, start: int, end: int, depth: int, found: dict[bytes, str]) -> None:
    """Walk the KLV items in ``data[start:end]``, collecting the wanted text keys.

    Args:
        data: The atom payload.
        start: Where the first item begins.
        end: Where the enclosing item (or the atom) ends.
        depth: The container nesting depth of this level.
        found: Receives ``{key: text}`` for the first occurrence of each wanted key.

    Raises:
        GPMFError: If an item header or value runs past ``end``, an item is not padded to four
            bytes, or the nesting is too deep.
    """
    if depth > MAX_DEPTH:
        raise GPMFError("containers nested too deeply")
    pos = start
    while pos < end:
        if end - pos < _HEADER:
            raise GPMFError("item header past atom end")
        key = data[pos : pos + 4]
        kind = data[pos + 4]
        length = data[pos + 5] * int.from_bytes(data[pos + 6 : pos + 8], "big")
        value_start = pos + _HEADER
        padded = (length + 3) // 4 * 4
        if value_start + padded > end:
            raise GPMFError("item length past atom end")
        if kind == _NESTED_TYPE:
            _walk(data, value_start, value_start + padded, depth + 1, found)
        elif key in _WANTED and kind == _TEXT_TYPE and key not in found:
            found[key] = _text(data[value_start : value_start + length])
        pos = value_start + padded


def parse_settings(payload: bytes) -> GoProInfo:
    """Decode firmware, Protune and colour profile from a ``GPMF`` settings atom payload.

    Args:
        payload: The bytes after the ``GPMF`` atom header.

    Returns:
        The three settings; a setting the atom does not carry is None. ``protune`` is True for
        ``Y``, False for ``N`` and None for any other value.

    Raises:
        GPMFError: If the payload is not well-formed KLV (sizes, padding or nesting).
    """
    found: dict[bytes, str] = {}
    _walk(payload, 0, len(payload), 1, found)
    protune = found.get(_PROTUNE)
    return GoProInfo(
        firmware=found.get(_FIRMWARE) or None,
        protune={"Y": True, "N": False}.get((protune or "").upper()),
        color_profile=found.get(_PROFILE) or None,
    )
