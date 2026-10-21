"""The primary item's layout in a HEIF file: ``pitm``, ``ipma`` and ``ipco`` (AD-24; WP3.6).

Orientation in a HEIC (D63) depends on whether the PRIMARY item carries an ``irot`` transform,
so the layout is read the way the standard associates properties: ``meta/pitm`` names the primary
item, ``meta/iprp/ipma`` lists that item's property indices, ``meta/iprp/ipco`` holds the
properties, numbered from 1. A transform that sits in ``ipco`` but is not associated with the
primary item (a thumbnail's, an auxiliary image's) does not count (WP2.1S section 8.1, DR-33 (c)).
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field


class HeifLayoutError(ValueError):
    """The HEIF box structure is malformed or lacks what the orientation rule needs."""


@dataclass(frozen=True)
class HeifLayout:
    """What the primary item of a HEIF file carries.

    Attributes:
        primary_id: The primary item's id (``pitm``).
        item_type: The primary item's type (``"grid"``, ``"hvc1"``, ...), or None.
        irot: The primary item's ``irot`` angle in degrees anticlockwise (0, 90, 180, 270), or
            None when it has none.
        imir: The primary item's ``imir`` axis bit, or None when it has none.
        clap: The primary item's clean aperture ``(width, height)`` in pixels, or None.
        ispe: The primary item's ``ispe`` ``(width, height)`` as stored, or None.
        auxiliary_ids: Ids of items that reference another item as ``auxl`` (gain map, depth).
        thumbnail_ids: Ids of items that reference another item as ``thmb``.
    """

    primary_id: int
    item_type: str | None
    irot: int | None
    imir: int | None
    clap: tuple[int, int] | None
    ispe: tuple[int, int] | None
    auxiliary_ids: tuple[int, ...] = field(default_factory=tuple)
    thumbnail_ids: tuple[int, ...] = field(default_factory=tuple)

    @property
    def is_grid(self) -> bool:
        """True when the primary item is a grid of tiles."""
        return self.item_type == "grid"

    def expected_size(self) -> tuple[int, int] | None:
        """Return the size libheif should decode: ``ispe`` (or ``clap``), turned by ``irot``.

        Returns:
            ``(width, height)`` after the transforms, or None when the primary item has no
            ``ispe``.
        """
        size = self.clap or self.ispe
        if size is None:
            return None
        if self.irot in (90, 270):
            return (size[1], size[0])
        return size


Box = tuple[str, int, int]


def _boxes(data: bytes, start: int, end: int) -> list[Box]:
    """List the boxes in ``data[start:end]`` as ``(type, body_start, box_end)``."""
    found: list[Box] = []
    at = start
    while at + 8 <= end:
        (size,) = struct.unpack(">I", data[at : at + 4])
        kind = data[at + 4 : at + 8].decode("latin-1")
        header = 8
        if size == 1:
            if at + 16 > end:
                raise HeifLayoutError("a box header is cut short")
            (size,) = struct.unpack(">Q", data[at + 8 : at + 16])
            header = 16
        elif size == 0:
            size = end - at
        if size < header or at + size > end:
            raise HeifLayoutError(f"box {kind!r} has an impossible size")
        found.append((kind, at + header, at + size))
        at += size
    return found


def _find(data: bytes, kind: str, start: int, end: int) -> Box | None:
    for box in _boxes(data, start, end):
        if box[0] == kind:
            return box
    return None


def _uint(data: bytes, at: int, size: int) -> int:
    if at + size > len(data):
        raise HeifLayoutError("a box is cut short")
    return int.from_bytes(data[at : at + size], "big")


def _items(data: bytes, iinf: Box) -> dict[int, str]:
    """Map item ids to item types from ``iinf``/``infe`` (versions 2 and 3)."""
    body, end = iinf[1], iinf[2]
    version = data[body]
    at = body + 4 + (2 if version == 0 else 4)
    types: dict[int, str] = {}
    for kind, start, _ in _boxes(data, at, end):
        if kind != "infe":
            continue
        infe_version = data[start]
        if infe_version < 2:
            continue
        width = 2 if infe_version == 2 else 4
        item_id = _uint(data, start + 4, width)
        types[item_id] = data[start + 4 + width + 2 : start + 4 + width + 6].decode("latin-1")
    return types


def _references(data: bytes, iref: Box, wanted: str) -> list[int]:
    """Return the ids of items that hold a reference of type ``wanted`` (``auxl``, ``thmb``)."""
    body, end = iref[1], iref[2]
    width = 2 if data[body] == 0 else 4
    return [
        _uint(data, start, width)
        for kind, start, stop in _boxes(data, body + 4, end)
        if kind == wanted
    ]


def _property(kind: str, data: bytes, start: int, stop: int) -> tuple[str, object] | None:
    """Decode the properties the rule uses; others return None."""
    if kind == "irot":
        return ("irot", (data[start] & 3) * 90)
    if kind == "imir":
        return ("imir", data[start] & 1)
    if kind == "ispe":
        return ("ispe", (_uint(data, start + 4, 4), _uint(data, start + 8, 4)))
    if kind == "clap" and stop - start >= 32:
        wn, wd, hn, hd = struct.unpack(">4I", data[start : start + 16])
        if wd and hd:
            return ("clap", (round(wn / wd), round(hn / hd)))
    return None


def _associations(data: bytes, ipma: Box, primary_id: int) -> list[int]:
    """Return the primary item's property indices (1-based, in file order) from ``ipma``."""
    body = ipma[1]
    version, flags = data[body], int.from_bytes(data[body + 1 : body + 4], "big")
    wide = bool(flags & 1)
    (count,) = struct.unpack(">I", data[body + 4 : body + 8])
    at = body + 8
    id_width = 2 if version == 0 else 4
    for _ in range(count):
        item_id = _uint(data, at, id_width)
        at += id_width
        entries = _uint(data, at, 1)
        at += 1
        indices = []
        for _ in range(entries):
            if wide:
                indices.append(_uint(data, at, 2) & 0x7FFF)
                at += 2
            else:
                indices.append(_uint(data, at, 1) & 0x7F)
                at += 1
        if item_id == primary_id:
            return indices
    return []


def read_layout(data: bytes) -> HeifLayout:
    """Read the primary item's layout from a HEIF file's ``meta`` box.

    Args:
        data: The file's bytes.

    Returns:
        The layout. ``irot``, ``imir``, ``clap`` and ``ispe`` come only from the properties the
        primary item's ``ipma`` entry names.

    Raises:
        HeifLayoutError: ``meta``, ``pitm``, ``iprp``, ``ipco`` or ``ipma`` is missing or the
            boxes are malformed.
    """
    try:
        return _read_layout(data)
    except (struct.error, IndexError) as error:
        raise HeifLayoutError(f"the box structure is cut short ({error})") from error


def _int(value: object) -> int | None:
    return value if isinstance(value, int) else None


def _pair(value: object) -> tuple[int, int] | None:
    return (value[0], value[1]) if isinstance(value, tuple) else None


def _read_layout(data: bytes) -> HeifLayout:
    meta = _find(data, "meta", 0, len(data))
    if meta is None:
        raise HeifLayoutError("there is no meta box")
    inner = (meta[1] + 4, meta[2])  # meta is a full box
    pitm = _find(data, "pitm", *inner)
    if pitm is None:
        raise HeifLayoutError("there is no primary item (pitm) box")
    primary_id = _uint(data, pitm[1] + 4, 2 if data[pitm[1]] == 0 else 4)
    iprp = _find(data, "iprp", *inner)
    ipco = _find(data, "ipco", iprp[1], iprp[2]) if iprp else None
    ipma = _find(data, "ipma", iprp[1], iprp[2]) if iprp else None
    if ipco is None or ipma is None:
        raise HeifLayoutError("there is no property association (ipco/ipma)")
    properties = _boxes(data, ipco[1], ipco[2])
    found: dict[str, object] = {}
    for index in _associations(data, ipma, primary_id):
        if 1 <= index <= len(properties):
            kind, start, stop = properties[index - 1]
            decoded = _property(kind, data, start, stop)
            if decoded is not None:
                found[decoded[0]] = decoded[1]
    iinf = _find(data, "iinf", *inner)
    types = _items(data, iinf) if iinf else {}
    iref = _find(data, "iref", *inner)
    return HeifLayout(
        primary_id=primary_id,
        item_type=types.get(primary_id),
        irot=_int(found.get("irot")),
        imir=_int(found.get("imir")),
        clap=_pair(found.get("clap")),
        ispe=_pair(found.get("ispe")),
        auxiliary_ids=tuple(_references(data, iref, "auxl")) if iref else (),
        thumbnail_ids=tuple(_references(data, iref, "thmb")) if iref else (),
    )
