"""Synthetic byte-level EXIF fidelity checks, independent of Pillow decoding."""

import struct
from pathlib import Path

import pytest
from PIL import Image as PilImage

from clearwater.io.photo import exif
from clearwater.io.photo.reader import read_photo
from clearwater.io.photo.writer import write_photo

_SIZES = {1: 1, 2: 1, 3: 2, 4: 4, 5: 8, 6: 1, 7: 1, 8: 2, 9: 4, 10: 8, 11: 4, 12: 8, 13: 4}
_PATHS = {(): {34665: "Exif", 34853: "GPS"}, ("Exif",): {40965: "Interop"}}


def _fixture(root=(), *, sub=None, gps=None, interop=None, order="<", thumbnail=False):
    """Build source bytes from declared raw entries; never use product helpers."""
    root = list(root)
    if interop is not None:
        sub = [*list(sub or ()), (40965, 4, 1, list(interop))]
    if sub is not None:
        root.append((34665, 4, 1, list(sub)))
    if gps is not None:
        root.append((34853, 4, 1, list(gps)))
    out = bytearray((b"II" if order == "<" else b"MM") + struct.pack(order + "HI", 42, 8))

    def emit(fields, with_thumbnail=False):
        start = len(out)
        out.extend(bytes(6 + 12 * len(fields)))
        struct.pack_into(order + "H", out, start, len(fields))
        for index, (tag, kind, count, payload) in enumerate(fields):
            record = start + 2 + 12 * index
            struct.pack_into(order + "HHI", out, record, tag, kind, count)
            if isinstance(payload, list):
                payload = struct.pack(order + "I", emit(payload))
            assert len(payload) == _SIZES[kind] * count
            if len(payload) > 4:
                struct.pack_into(order + "I", out, record + 8, len(out))
                out.extend(payload)
                if len(out) % 2:
                    out.append(0)
            else:
                out[record + 8 : record + 12] = payload.ljust(4, b"\0")
        if with_thumbnail:
            pointer = emit([(513, 4, 1, struct.pack(order + "I", 0)), (514, 4, 1, bytes(4))])
            struct.pack_into(order + "I", out, start + 2 + 12 * len(fields), pointer)
        return start

    assert emit(root, thumbnail) == 8
    return bytes(out)


def _parse(block):
    """Independently inspect TIFF entries, following only the specified EXIF tree."""
    assert block[:2] in (b"II", b"MM")
    order = "<" if block[:2] == b"II" else ">"
    assert struct.unpack_from(order + "H", block, 2)[0] == 42
    directories = {}

    def read(offset, path):
        assert 8 <= offset <= len(block) - 6
        number = struct.unpack_from(order + "H", block, offset)[0]
        assert offset + 6 + 12 * number <= len(block)
        entries = []
        directories[path] = entries
        for index in range(number):
            start = offset + 2 + index * 12
            tag, kind, count = struct.unpack_from(order + "HHI", block, start)
            length = _SIZES[kind] * count
            at = start + 8 if length <= 4 else struct.unpack_from(order + "I", block, start + 8)[0]
            assert 0 <= at <= len(block) and length <= len(block) - at
            value = block[at : at + length]
            entries.append((tag, kind, count, value))
            if tag in _PATHS.get(path, {}):
                child = struct.unpack(order + "I", value)[0]
                read(child, (*path, _PATHS[path][tag]))
        return struct.unpack_from(order + "I", block, offset + 2 + number * 12)[0]

    next_ifd = read(struct.unpack_from(order + "I", block, 4)[0], ())
    return order, directories, next_ifd


def _entry(block, path, tag):
    return next(entry for entry in _parse(block)[1][path] if entry[0] == tag)


def _same(before, after, path, tag):
    assert _entry(after, path, tag) == _entry(before, path, tag), (
        f"{path}.{tag} type/count/value changed"
    )


def _tiff_fixture(fields=(), **options):
    source = bytearray(
        _fixture(
            [
                (256, 4, 1, struct.pack("<I", 1)),
                (257, 4, 1, struct.pack("<I", 1)),
                (258, 3, 1, struct.pack("<H", 8)),
                (259, 3, 1, struct.pack("<H", 1)),
                (262, 3, 1, struct.pack("<H", 1)),
                (273, 4, 1, bytes(4)),
                (277, 3, 1, struct.pack("<H", 1)),
                (278, 4, 1, struct.pack("<I", 1)),
                (279, 4, 1, struct.pack("<I", 1)),
                *fields,
            ],
            **options,
        )
    )
    struct.pack_into("<I", source, 8 + 2 + 5 * 12 + 8, len(source))
    source.append(128)
    return bytes(source)


@pytest.mark.parametrize("order", ["<", ">"])
@pytest.mark.parametrize(
    ("tag", "value", "path"),
    [
        (42036, bytes(range(128, 256)) + b"\0", ("Exif",)),
        (271, bytes(16), ()),
        (272, b"\0A\0\0B\0\0\0", ()),
        (315, b"caf\xe9\0", ()),
        (270, b"caf\xc3\xa9\0", ()),
        (33432, b"synthetic copyright\0", ()),
        (65000, b"abcd", ()),
        (65000, b"abcde", ()),
        (65000, b"x\x80\0", ("GPS",)),
        (65000, b"x\x80\0", ("Exif", "Interop")),
    ],
)
def test_ascii_type_count_and_value_bytes_survive(tmp_path, order, tag, value, path):
    fields = [(tag, 2, len(value), value)]
    options = {
        (): {"root": fields},
        ("Exif",): {"sub": fields},
        ("GPS",): {"gps": fields},
        ("Exif", "Interop"): {"interop": fields},
    }
    source = _fixture(order=order, **options[path])
    (tmp_path / "synthetic.exif").write_bytes(source)
    output = exif.edit(source, 4, 3)
    assert _parse(output)[0] == order, "source byte order changed"
    _same(source, output, path, tag)


@pytest.mark.parametrize("order", ["<", ">"])
@pytest.mark.parametrize("kind", [4, 5, 7, 8, 9, 10, 11, 12])
@pytest.mark.parametrize("path", [(), ("Exif",), ("GPS",), ("Exif", "Interop")])
def test_non_ascii_source_types_and_raw_values_survive(tmp_path, order, kind, path):
    values = {
        4: struct.pack(order + "I", 7),
        5: struct.pack(order + "II", 1234, 100),
        7: b"\x00\x80\xff\x01\x02",
        8: struct.pack(order + "h", -12),
        9: struct.pack(order + "i", -1234),
        10: struct.pack(order + "ii", -1234, 100),
        11: struct.pack(order + "I", 0x7FC01234),
        12: struct.pack(order + "d", 1.25),
    }
    value = values[kind]
    fields = [(65001, kind, len(value) // _SIZES[kind], value)]
    options = {
        (): {"root": fields},
        ("Exif",): {"sub": fields},
        ("GPS",): {"gps": fields},
        ("Exif", "Interop"): {"interop": fields},
    }
    source = _fixture(order=order, **options[path])
    (tmp_path / "synthetic.exif").write_bytes(source)
    _same(source, exif.edit(source, 4, 3), path, 65001)


def test_makernote_and_synthetic_gps_bytes_survive(tmp_path):
    maker = b"synthetic\x00\x80\xff"
    source = _fixture(
        sub=[(37500, 7, len(maker), maker)],
        gps=[
            (1, 2, 2, b"N\0"),
            (2, 5, 3, struct.pack("<6I", 1234, 100, 5678, 100, 9000, 100)),
            (3, 2, 2, b"E\0"),
        ],
    )
    (tmp_path / "gps.exif").write_bytes(source)
    output = exif.edit(source, 4, 3)
    for path, tag in [(("Exif",), 37500), (("GPS",), 1), (("GPS",), 2), (("GPS",), 3)]:
        _same(source, output, path, tag)


@pytest.mark.parametrize("source_kind,width,want_kind", [(3, 640, 3), (3, 65536, 4), (4, 640, 4)])
def test_d63_replaces_fields_and_drops_thumbnail(tmp_path, source_kind, width, want_kind):
    fmt = "H" if source_kind == 3 else "I"
    source = _fixture(
        [(274, 3, 1, struct.pack("<H", 6)), (305, 2, 4, b"old\0")],
        sub=[
            (40962, source_kind, 1, struct.pack("<" + fmt, 12)),
            (40963, source_kind, 1, struct.pack("<" + fmt, 9)),
        ],
        thumbnail=True,
    )
    (tmp_path / "dimensions.exif").write_bytes(source)
    output = exif.edit(source, width, 480)
    assert _entry(output, (), 274) == (274, 3, 1, b"\1\0")
    assert _entry(output, (), 305) == (305, 2, 11, b"Clearwater\0")
    fmt = "H" if want_kind == 3 else "I"
    assert _entry(output, ("Exif",), 40962) == (40962, want_kind, 1, struct.pack("<" + fmt, width))
    assert _entry(output, ("Exif",), 40963) == (
        40963,
        source_kind,
        1,
        struct.pack("<" + ("H" if source_kind == 3 else "I"), 480),
    )
    assert _parse(output)[2] == 0, "IFD1 was retained"


@pytest.mark.parametrize("sub", [None, [], [(36864, 7, 4, b"0230")]])
def test_d63_inserts_missing_entries(tmp_path, sub):
    source = _fixture([(271, 2, 4, b"abc\0")], sub=sub)
    (tmp_path / "insert.exif").write_bytes(source)
    output = exif.edit(source, 30, 20)
    assert _entry(output, (), 274) == (274, 3, 1, b"\1\0")
    assert _entry(output, ("Exif",), 40962) == (40962, 4, 1, struct.pack("<I", 30))
    assert _entry(output, ("Exif",), 40963) == (40963, 4, 1, struct.pack("<I", 20))
    assert [row[0] for row in _parse(output)[1][()]] == [271, 274, 305, 34665]


def test_none_source_has_only_the_four_d63_fields(tmp_path):
    output = exif.edit(None, 30, 20)
    (tmp_path / "minimal.exif").write_bytes(output)
    order = _parse(output)[0]
    assert [row[0] for row in _parse(output)[1][()]] == [274, 305, 34665]
    assert _parse(output)[1][("Exif",)] == [
        (40962, 4, 1, struct.pack(order + "I", 30)),
        (40963, 4, 1, struct.pack(order + "I", 20)),
    ]


def test_kept_entry_order_is_preserved(tmp_path):
    source = _fixture([(400, 7, 1, b"x"), (271, 2, 2, b"M\0"), (270, 2, 2, b"D\0")])
    (tmp_path / "order.exif").write_bytes(source)
    output = exif.edit(source, 4, 3)
    kept = [row[0] for row in _parse(output)[1][()] if row[0] in (400, 271, 270)]
    assert kept == [400, 271, 270], "kept entry order changed"


@pytest.mark.parametrize("bad", ["offset", "table", "payload"])
@pytest.mark.parametrize("pointer,path", [(34665, ()), (34853, ()), (40965, ("Exif",))])
def test_damaged_child_is_dropped_alone(tmp_path, caplog, bad, pointer, path):
    source = bytearray(
        _fixture(
            [(271, 2, 4, b"abc\0")],
            sub=[(36864, 7, 4, b"0230")],
            gps=[(1, 2, 2, b"N\0")],
            interop=[(1, 2, 4, b"R98\0")],
        )
    )
    root = 8
    if path:
        rows = struct.unpack_from("<H", source, root)[0]
        root = next(
            struct.unpack_from("<I", source, root + 10 + i * 12)[0]
            for i in range(rows)
            if struct.unpack_from("<H", source, root + 2 + i * 12)[0] == 34665
        )
    rows = struct.unpack_from("<H", source, root)[0]
    record = next(
        root + 2 + i * 12
        for i in range(rows)
        if struct.unpack_from("<H", source, root + 2 + i * 12)[0] == pointer
    )
    child = struct.unpack_from("<I", source, record + 8)[0]
    if bad == "offset":
        struct.pack_into("<I", source, record + 8, len(source) + 100)
    elif bad == "table":
        struct.pack_into("<H", source, child, 65535)
    else:
        struct.pack_into("<HHII", source, child + 2, 65000, 7, 100, len(source) + 100)
    (tmp_path / "damaged.exif").write_bytes(source)
    output = exif.edit(bytes(source), 4, 3)
    assert _entry(output, (), 271) == (271, 2, 4, b"abc\0")
    if pointer == 34665:
        assert [row[0] for row in _parse(output)[1][("Exif",)]] == [40962, 40963]
    else:
        assert pointer not in [row[0] for row in _parse(output)[1][path]]
        assert _entry(output, ("Exif",), 36864) == (36864, 7, 4, b"0230")
    assert "cannot be read" in caplog.text, "damaged child was not reported"


@pytest.mark.parametrize("bad", [b"garbage", b"II*\0\xff\xff\xff\xff", b"II*\0\x08\0\0\0\xff\xff"])
def test_damaged_root_raises_and_sanitise_drops(tmp_path, bad):
    (tmp_path / "bad.exif").write_bytes(bad)
    with pytest.raises((ValueError, struct.error, SyntaxError)):
        exif.edit(bad, 4, 3)
    assert exif.sanitise(bad, "synthetic") is None


def test_oversized_root_value_is_rejected(tmp_path):
    source = bytearray(_fixture([(271, 2, 4, b"abc\0")]))
    struct.pack_into("<I", source, 14, 0xFFFFFFFF)
    (tmp_path / "huge.exif").write_bytes(source)
    with pytest.raises(ValueError):
        exif.edit(bytes(source), 4, 3)


def test_other_ifd_values_are_dropped_with_warning(tmp_path, caplog):
    source = _fixture(
        [
            (330, 4, 1, struct.pack("<I", 8)),
            (65000, 13, 1, struct.pack("<I", 8)),
            (271, 2, 4, b"abc\0"),
        ]
    )
    (tmp_path / "subifd.exif").write_bytes(source)
    output = exif.edit(source, 4, 3)
    assert not {330, 65000}.intersection(row[0] for row in _parse(output)[1][()]), (
        "unsupported IFD retained"
    )
    assert "dropped" in caplog.text


@pytest.mark.parametrize("kind", ["png", "jpeg"])
def test_write_photo_preserves_bytes_through_png_exif(tmp_path: Path, kind):
    source = _fixture(sub=[(42036, 2, 6, b"ab\x80cd\0")])
    path = tmp_path / ("source." + kind)
    PilImage.new("RGB", (4, 3), (20, 40, 60)).save(path, exif=b"Exif\0\0" + source)
    image, meta = read_photo(path)
    assert meta.exif is not None
    _same(source, meta.exif, ("Exif",), 42036)
    output = tmp_path / "written.png"
    write_photo(image, meta, output, bit_depth=16)
    _, written = read_photo(output)
    assert written.exif is not None
    _same(source, written.exif, ("Exif",), 42036)


def test_from_tiff_preserves_raw_ascii_and_filters_structure(tmp_path):
    source = _tiff_fixture(
        [(315, 2, 6, b"ab\x80cd\0")], sub=[(33434, 5, 1, struct.pack("<II", 1234, 100))]
    )
    (tmp_path / "source.tiff").write_bytes(source)
    output = exif.from_tiff(source)
    assert output is not None, "TIFF metadata was lost"
    _same(source, output, (), 315)
    _same(source, output, ("Exif",), 33434)
    assert not {256, 257}.intersection(row[0] for row in _parse(output)[1][()])
    _same(source, exif.edit(output, 4, 3), (), 315)


def test_from_tiff_without_metadata_returns_none(tmp_path):
    source = _tiff_fixture()
    (tmp_path / "empty.tiff").write_bytes(source)
    assert exif.from_tiff(source) is None


def test_bigtiff_is_not_carried(tmp_path, caplog):
    source = b"II" + struct.pack("<HHHQ", 43, 8, 0, 16) + bytes(16)
    (tmp_path / "big.tiff").write_bytes(source)
    assert exif.from_tiff(source) is None
    assert "BigTIFF" in caplog.text, "unsupported BigTIFF was not reported"
    assert exif.sanitise(source, "synthetic") is None
