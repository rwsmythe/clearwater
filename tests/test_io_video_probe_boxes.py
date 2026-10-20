"""Tests of the box reader and the GPMF settings decoder (WP3.7) on synthetic data.

The boxes and KLV items are built here, byte by byte, so every malformed case is known.
"""

from __future__ import annotations

import contextlib
import struct
from fractions import Fraction
from pathlib import Path
from typing import BinaryIO

import pytest

from clearwater.io.video import boxes, gopro
from clearwater.io.video.boxes import BoxError, RawEdit, parse_moov, read_movie_boxes

# --- builders -----------------------------------------------------------------------------------


def box(kind: str, payload: bytes = b"") -> bytes:
    return struct.pack(">I4s", 8 + len(payload), kind.encode()) + payload


def header_box(kind: str, scale: int, version: int = 0) -> bytes:
    """An ``mvhd`` or ``mdhd``: creation and modification times, time scale, duration."""
    if version == 1:
        body = struct.pack(">BxxxQQIQ", 1, 0, 0, scale, 99) + b"\0" * 20
    else:
        body = struct.pack(">BxxxIIII", 0, 0, 0, scale, 99) + b"\0" * 20
    return box(kind, body)


def hdlr(handler: str) -> bytes:
    return box("hdlr", b"\0" * 8 + handler.encode() + b"\0" * 12)


def elst(entries: list[tuple[int, int, int, int]], version: int = 0) -> bytes:
    body = struct.pack(">BxxxI", version, len(entries))
    for duration, media_time, rate_int, rate_frac in entries:
        form = ">QqhH" if version == 1 else ">IihH"
        body += struct.pack(form, duration, media_time, rate_int, rate_frac)
    return box("elst", body)


def trak(handler: str, scale: int, edits: bytes | None = None) -> bytes:
    mdia = box("mdia", header_box("mdhd", scale) + hdlr(handler))
    return box("trak", (box("edts", edits) if edits else b"") + mdia)


def moov(*children: bytes) -> bytes:
    return box("moov", b"".join(children))


def klv(key: str, kind: str, value: bytes, size: int = 1, repeat: int | None = None) -> bytes:
    count = len(value) // size if repeat is None else repeat
    item = key.encode() + kind.encode() + bytes([size]) + count.to_bytes(2, "big") + value
    return item + b"\0" * (-len(value) % 4)


def nested(key: str, *children: bytes) -> bytes:
    payload = b"".join(children)
    return key.encode() + b"\0" + bytes([1]) + len(payload).to_bytes(2, "big") + payload


def write(tmp_path: Path, *top: bytes) -> Path:
    path = tmp_path / "movie.mp4"
    path.write_bytes(b"".join(top))
    return path


FTYP = box("ftyp", b"isom\0\0\2\0isomiso2")
MDAT = box("mdat", b"\xaa" * 64)
SETTINGS = klv("FMWR", "c", b"H24.01") + klv("PRTN", "c", b"Y") + klv("PTCL", "c", b"NATURAL")


# --- edit list ----------------------------------------------------------------------------------


def test_an_identity_edit_is_read_with_both_time_scales(tmp_path: Path) -> None:
    video = trak("vide", 30000, elst([(45045, 0, 1, 0)]))
    path = write(tmp_path, FTYP, MDAT, moov(header_box("mvhd", 30000), video))
    result = read_movie_boxes(path)
    assert (result.movie_timescale, result.video_timescale) == (30000, 30000)
    assert result.edits == (RawEdit(45045, 0, Fraction(1)),)
    assert result.gpmf is None


def test_an_empty_edit_keeps_media_time_minus_one(tmp_path: Path) -> None:
    video = trak("vide", 600, elst([(1000, -1, 1, 0), (2000, 512, 1, 0)]))
    result = parse_moov(moov(header_box("mvhd", 1000), video)[8:])
    assert result.edits == (RawEdit(1000, -1, Fraction(1)), RawEdit(2000, 512, Fraction(1)))
    assert (result.movie_timescale, result.video_timescale) == (1000, 600)


def test_a_version_1_edit_list_and_headers(tmp_path: Path) -> None:
    mdia = box("mdia", header_box("mdhd", 90000, version=1) + hdlr("vide"))
    video = box("trak", box("edts", elst([(2**33, 2**34, 1, 0)], version=1)) + mdia)
    result = parse_moov(moov(header_box("mvhd", 1000, version=1), video)[8:])
    assert result.edits == (RawEdit(2**33, 2**34, Fraction(1)),)
    assert (result.movie_timescale, result.video_timescale) == (1000, 90000)


def test_the_rate_is_a_16_16_fixed_point_fraction() -> None:
    video = trak("vide", 600, elst([(10, 0, 0, 0x8000), (10, 0, 2, 0)]))
    result = parse_moov(moov(header_box("mvhd", 1000), video)[8:])
    assert [e.media_rate for e in result.edits] == [Fraction(1, 2), Fraction(2)]


def test_only_the_video_tracks_edit_list_is_read() -> None:
    audio = trak("soun", 48000, elst([(7, 5, 1, 0)]))
    video = trak("vide", 600, elst([(10, 0, 1, 0)]))
    result = parse_moov(moov(header_box("mvhd", 1000), audio, video)[8:])
    assert result.edits == (RawEdit(10, 0, Fraction(1)),)
    assert result.video_timescale == 600


def test_a_video_track_without_an_edit_list_has_none() -> None:
    result = parse_moov(moov(header_box("mvhd", 1000), trak("vide", 600))[8:])
    assert result.edits == ()


def test_the_probe_converts_edits_to_exact_seconds() -> None:
    from clearwater.io.video.probe import _edit_list

    movie = boxes.MovieBoxes(1000, 30000, (RawEdit(1502, 0, Fraction(1)), RawEdit(5, -1, 1)), None)
    first, second = _edit_list(movie)
    assert (first.segment_duration_s, first.media_time_s) == (Fraction(751, 500), 0)
    assert (second.segment_duration_s, second.media_time_s) == (Fraction(1, 200), None)
    with pytest.raises(BoxError):
        _edit_list(boxes.MovieBoxes(None, 30000, (RawEdit(1, 0, Fraction(1)),), None))


# --- the settings atom is found -----------------------------------------------------------------


def test_the_settings_atom_payload_is_returned(tmp_path: Path) -> None:
    udta = box("udta", box("free", b"\0" * 12) + box("GPMF", SETTINGS) + box("free"))
    path = write(tmp_path, FTYP, moov(header_box("mvhd", 1000), udta), MDAT)
    assert read_movie_boxes(path).gpmf == SETTINGS


def test_a_quicktime_zero_terminator_after_the_last_child_is_tolerated() -> None:
    udta = box("udta", box("GPMF", SETTINGS) + b"\0\0\0\0")
    assert parse_moov(moov(header_box("mvhd", 1000), udta)[8:]).gpmf == SETTINGS


def test_a_64_bit_box_size_and_a_size_to_the_end_are_read(tmp_path: Path) -> None:
    body = moov(header_box("mvhd", 1000), trak("vide", 600, elst([(3, 0, 1, 0)])))[8:]
    large = struct.pack(">I4sQ", 1, b"moov", 16 + len(body)) + body
    path = write(tmp_path, FTYP, struct.pack(">I4s", 0, b"mdat") + b"\xaa" * 40)
    assert read_movie_boxes(path) == boxes.MovieBoxes(None, None, (), None)  # mdat ran to the end
    path = write(tmp_path, FTYP, MDAT, large)
    assert read_movie_boxes(path).edits == (RawEdit(3, 0, Fraction(1)),)


def test_no_moov_gives_an_empty_result(tmp_path: Path) -> None:
    assert read_movie_boxes(write(tmp_path, FTYP, MDAT)) == boxes.MovieBoxes(None, None, (), None)


class _Counting:
    """A file wrapper that records the position and size of every read."""

    def __init__(self, handle: BinaryIO, reads: list[tuple[int, int]]) -> None:
        self._handle, self._reads = handle, reads

    def __enter__(self) -> _Counting:
        return self

    def __exit__(self, *exc: object) -> None:
        self._handle.close()

    def read(self, size: int = -1) -> bytes:
        self._reads.append((self._handle.tell(), size))
        return self._handle.read(size)

    def seek(self, offset: int, whence: int = 0) -> int:
        return self._handle.seek(offset, whence)

    def tell(self) -> int:
        return self._handle.tell()


def _reads_inside(path: Path, monkeypatch: pytest.MonkeyPatch) -> list[tuple[int, int]]:
    """Run the reader and return the ``(position, size)`` of every read it made."""
    reads: list[tuple[int, int]] = []
    monkeypatch.setattr(
        Path,
        "open",
        lambda self, mode="r": _Counting(open(self, mode), reads),  # noqa: SIM115
    )
    assert read_movie_boxes(path).movie_timescale == 1000
    return reads


def test_the_reader_takes_exactly_the_header_bytes_of_the_media_data_box(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    mdat = box("mdat", b"PAYLOAD-" * 8)
    path = write(tmp_path, FTYP, mdat, moov(header_box("mvhd", 1000)))
    start = len(FTYP)
    reads = _reads_inside(path, monkeypatch)
    inside = [(pos, size) for pos, size in reads if start <= pos < start + len(mdat)]
    assert inside == [(start, 8)]  # the 8-byte header and nothing of the payload
    assert sum(size for pos, size in inside) == 8


def test_a_64_bit_media_data_header_is_read_as_two_headers_and_no_payload(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    big = struct.pack(">I4sQ", 1, b"mdat", 16 + 5_000_000) + bytes(5_000_000)
    path = write(tmp_path, FTYP, big, moov(header_box("mvhd", 1000)))
    start = len(FTYP)
    reads = _reads_inside(path, monkeypatch)
    inside = [(pos, size) for pos, size in reads if start <= pos < start + len(big)]
    assert inside == [(start, 8), (start + 8, 8)]


# --- malformed boxes ----------------------------------------------------------------------------


@pytest.mark.parametrize(
    "bad",
    [
        # a trak whose size runs past the moov
        struct.pack(">I4s", 9999, b"trak") + b"\0" * 8,
        # a child smaller than its own header (would loop forever if the walk did not advance)
        struct.pack(">I4s", 4, b"trak") + b"\0" * 8,
        # a 64-bit size marker with no room for the size
        struct.pack(">I4s", 1, b"trak"),
        # trailing bytes that are not a zero terminator
        b"\0\0\1",
    ],
)
def test_malformed_children_raise_box_error(bad: bytes) -> None:
    with pytest.raises(BoxError):
        parse_moov(header_box("mvhd", 1000) + bad)


def test_an_edit_list_count_past_the_box_raises() -> None:
    body = struct.pack(">BxxxI", 0, 1000) + struct.pack(">IihH", 1, 0, 1, 0)
    video = box(
        "trak", box("edts", box("elst", body)) + box("mdia", header_box("mdhd", 1) + hdlr("vide"))
    )
    with pytest.raises(BoxError):
        parse_moov(moov(header_box("mvhd", 1000), video)[8:])


def test_a_zero_time_scale_raises() -> None:
    with pytest.raises(BoxError):
        parse_moov(header_box("mvhd", 0))


def test_a_short_header_box_raises() -> None:
    with pytest.raises(BoxError):
        parse_moov(box("mvhd", b"\0\0\0\0\0\0"))


def test_an_unknown_elst_version_raises() -> None:
    video = trak("vide", 600, box("elst", struct.pack(">BxxxI", 7, 0)))
    with pytest.raises(BoxError):
        parse_moov(moov(header_box("mvhd", 1000), video)[8:])


def test_a_moov_past_the_end_of_the_file_raises(tmp_path: Path) -> None:
    path = write(tmp_path, FTYP, moov(header_box("mvhd", 1000))[:-5])
    with pytest.raises(BoxError):
        read_movie_boxes(path)


def test_a_cut_top_level_header_raises(tmp_path: Path) -> None:
    with pytest.raises(BoxError):
        read_movie_boxes(write(tmp_path, FTYP, b"\0\0\0"))


def test_a_top_level_box_smaller_than_its_header_raises(tmp_path: Path) -> None:
    with pytest.raises(BoxError):
        read_movie_boxes(write(tmp_path, FTYP, struct.pack(">I4s", 3, b"free") + b"\0" * 8))


def test_an_oversized_moov_is_refused(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(boxes, "MAX_MOOV_BYTES", 16)
    with pytest.raises(BoxError):
        read_movie_boxes(write(tmp_path, FTYP, moov(header_box("mvhd", 1000))))


def test_every_truncation_of_a_real_looking_file_ends_without_a_hang(tmp_path: Path) -> None:
    udta = box("udta", box("GPMF", SETTINGS))
    whole = (
        FTYP + moov(header_box("mvhd", 1000), trak("vide", 600, elst([(10, 0, 1, 0)])), udta) + MDAT
    )
    for cut in range(len(whole)):
        path = tmp_path / "cut.mp4"
        path.write_bytes(whole[:cut])
        with contextlib.suppress(BoxError):
            read_movie_boxes(path)


# --- GPMF settings ------------------------------------------------------------------------------


def test_the_three_keys_are_decoded() -> None:
    info = gopro.parse_settings(SETTINGS)
    assert (info.firmware, info.protune, info.color_profile) == ("H24.01", True, "NATURAL")


def test_the_keys_are_found_in_nested_containers() -> None:
    payload = nested("DEVC", nested("STRM", klv("PTCL", "c", b"FLAT")), klv("FMWR", "c", b"H1"))
    info = gopro.parse_settings(payload)
    assert (info.firmware, info.protune, info.color_profile) == ("H1", None, "FLAT")


def test_an_unrelated_key_is_skipped_by_length_and_never_decoded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    decoded: list[bytes] = []
    real = gopro._text

    def spy(raw: bytes) -> str:
        decoded.append(raw)
        return real(raw)

    monkeypatch.setattr(gopro, "_text", spy)
    payload = (
        klv("SERI", "c", b"C3555555555555")
        + klv("FMWR", "c", b"H24")
        + klv("ACCL", "s", struct.pack(">hhh", 1, 2, 3), size=2, repeat=3)
        + klv("PRTN", "c", b"N")
        + nested("MINF", klv("UNKN", "c", b"secret"))
        + klv("PTCL", "c", b"VIBRANT")
    )
    info = gopro.parse_settings(payload)
    assert (info.firmware, info.protune, info.color_profile) == ("H24", False, "VIBRANT")
    assert decoded == [b"H24", b"N", b"VIBRANT"]


def test_protune_values_other_than_y_and_n_are_none() -> None:
    assert gopro.parse_settings(klv("PRTN", "c", b"?")).protune is None


def test_a_wanted_key_of_another_type_is_not_decoded() -> None:
    info = gopro.parse_settings(klv("PTCL", "L", struct.pack(">I", 7), size=4, repeat=1))
    assert info.color_profile is None


def test_the_first_occurrence_of_a_key_wins() -> None:
    info = gopro.parse_settings(klv("FMWR", "c", b"A") + klv("FMWR", "c", b"B"))
    assert info.firmware == "A"


def test_an_empty_atom_gives_all_none() -> None:
    assert gopro.parse_settings(b"") == gopro.GoProInfo(None, None, None)


@pytest.mark.parametrize(
    ("payload", "reason"),
    [
        (b"FMWRc\x01", "item header past atom end"),
        (b"FMWRc\x01\x00\xff" + b"abcd", "item length past atom end"),
        (b"FMWRc\x01\x00\x03" + b"abc", "item length past atom end"),  # padding byte missing
        (b"UNKNc\x01\x00\x05" + b"abcde\0\0", "item length past atom end"),  # short padding
        (klv("FMWR", "c", b"H1") + b"\0\0\0", "item header past atom end"),  # trailing bytes
        (nested("DEVC", b"FMWRc\x01\x00\xff"), "item length past atom end"),  # inside a container
        (b"DEVC\0\x01\x00\x40" + b"\0" * 8, "item length past atom end"),  # container too long
    ],
)
def test_malformed_klv_is_refused_with_a_structural_reason(payload: bytes, reason: str) -> None:
    with pytest.raises(gopro.GPMFError, match=reason):
        gopro.parse_settings(payload)


def test_nesting_deeper_than_the_cap_is_refused() -> None:
    payload = klv("FMWR", "c", b"H1")
    for _ in range(gopro.MAX_DEPTH):
        payload = nested("DEVC", payload)
    with pytest.raises(gopro.GPMFError, match="nested too deeply"):
        gopro.parse_settings(payload)
    inside = klv("FMWR", "c", b"H1")
    for _ in range(gopro.MAX_DEPTH - 1):
        inside = nested("DEVC", inside)
    assert gopro.parse_settings(inside).firmware == "H1"


def test_the_error_message_carries_no_payload_bytes() -> None:
    secret = b"SERIAL-C3455"
    with pytest.raises(gopro.GPMFError) as caught:
        gopro.parse_settings(b"FMWRc\x01\x00\xff" + secret)
    assert secret.decode() not in str(caught.value)


def test_every_truncation_of_a_settings_atom_ends_without_a_hang() -> None:
    payload = nested("DEVC", SETTINGS + klv("ACCL", "s", b"\0" * 6, size=2, repeat=3))
    for cut in range(len(payload) + 1):
        with contextlib.suppress(gopro.GPMFError):
            gopro.parse_settings(payload[:cut])


def test_a_box_other_than_media_data_that_overruns_the_file_raises(tmp_path: Path) -> None:
    overrun = struct.pack(">I4s", 100, b"free")
    with pytest.raises(BoxError):
        read_movie_boxes(write(tmp_path, FTYP, overrun, moov(header_box("mvhd", 1000))))


def test_media_data_that_overruns_a_cut_file_is_not_an_error(tmp_path: Path) -> None:
    cut_mdat = struct.pack(">I4s", 10_000, b"mdat") + b"\xaa" * 20
    assert read_movie_boxes(write(tmp_path, FTYP, cut_mdat)).movie_timescale is None
    path = write(tmp_path, FTYP, moov(header_box("mvhd", 1000)), cut_mdat)
    assert read_movie_boxes(path).movie_timescale == 1000
