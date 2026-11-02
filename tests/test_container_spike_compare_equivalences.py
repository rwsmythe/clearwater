"""WP4.4: narrow V4 equivalences with synthetic facts and real-difference controls."""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

import test_io_video_encode_units as pcm_units
import video_fidelity as vf
from clearwater.interfaces.video import Fault
from container_spike import compare

SIDE = "display orientation: display matrix (ffprobe side data)"
TKHD = "display orientation: video tkhd matrix"
GEOMETRY = "frame size and sample aspect ratio"
AUDIO = "audio streams present"
TURN = (-65536, 0, 0, 0, -65536, 0, 0, 0, 1073741824)
TRANSLATED = (*TURN[:6], 125829120, 94371840, TURN[8])
QUARTER = (0, -65536, 0, 65536, 0, 0, 0, 0, TURN[8])
MIRRORED = (65536, *TURN[1:])


def _matrix_text(matrix: tuple[int, ...]) -> str:
    """Render ffprobe's three labelled rows, including the translation row."""
    return (
        "\n"
        + "\n".join(
            f"{row:08d}: " + " ".join(f"{value:12d}" for value in matrix[row * 3 : row * 3 + 3])
            for row in range(3)
        )
        + "\n"
    )


def _facts(
    *,
    matrix: tuple[int, ...] = TURN,
    rotation: int = -180,
    video: dict[str, Any] | None = None,
    audio: dict[str, Any] | None = None,
) -> compare.Facts:
    """Build complete comparison inputs without reading files or invoking FFmpeg."""
    video_stream = {
        "index": 0,
        "id": "0x1",
        "codec_type": "video",
        "codec_name": "hevc",
        "width": 1920,
        "height": 1440,
        "pix_fmt": "yuv420p",
        "sample_aspect_ratio": "1:1",
        "time_base": "1/30",
        "start_pts": 0,
        "duration_ts": 15,
        "side_data_list": [{"rotation": rotation, "displaymatrix": _matrix_text(matrix)}],
        **(video or {}),
    }
    audio_stream = {
        "index": 1,
        "codec_type": "audio",
        "codec_name": "pcm_s16le",
        "sample_rate": "48000",
        "sample_fmt": "s16",
        "channels": 1,
        "channel_layout": "mono",
        "time_base": "1/48000",
        "start_pts": 0,
        **(audio or {}),
    }
    track = compare.Track(1, 3, "vide", "", "hvc1", (), 30, 15, matrix, None, 0)
    movie = compare.Movie((), "isom", (), 30, 0, (track,), ())
    return compare.Facts(
        Path("synthetic.mp4"),
        {"streams": [video_stream, audio_stream], "format": {"start_time": "0.000000"}},
        movie,
        0,
        [Fraction(frame, 30) for frame in range(15)],
        {},
        {0: "vide#0", 1: "soun#0"},
    )


def _item(source: compare.Facts, output: compare.Facts, name: str) -> compare.Item:
    """Get the actual item from the shared comparison entry point."""
    return next(item for item in compare.compare_facts(source, output) if item.name == name)


def test_synthetic_facts_self_comparison() -> None:
    """Keep the synthetic scaffold itself all SAME."""
    facts = _facts()
    assert all(item.status == compare.SAME for item in compare.compare_facts(facts, facts))


@pytest.mark.parametrize("name", [SIDE, TKHD], ids=["side", "tkhd"])
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_translation_is_equivalent(name: str, reverse: bool) -> None:
    """Translation alone cannot change the mandatory orientation verdict."""
    source, output = _facts(matrix=TRANSLATED), _facts()
    if reverse:
        source, output = output, source
    item = _item(source, output, name)
    assert (item.item_class, item.status) == (compare.MANDATORY, compare.SAME)


@pytest.mark.parametrize("name", [SIDE, TKHD], ids=["side", "tkhd"])
def test_translation_note_records_both_sides(name: str) -> None:
    """Keep both translations in the note without comparing them in the verdict."""
    item = _item(_facts(matrix=TRANSLATED), _facts(), name)
    assert item.status == compare.SAME
    assert "BEST-EFFORT" in item.note
    assert f"source={list(TRANSLATED[6:8])}" in item.note
    assert f"output={list(TURN[6:8])}" in item.note


@pytest.mark.parametrize("name", [SIDE, TKHD], ids=["side", "tkhd"])
@pytest.mark.parametrize(
    "matrix",
    [(*TURN[:8], 2 << 30), (*TURN[:2], 12345, *TURN[3:5], 678, *TURN[6:])],
    ids=["w", "uv"],
)
def test_nontranslation_matrix_change_control(name: str, matrix: tuple[int, ...]) -> None:
    """Keep homogeneous scale and perspective differences in both orientation items."""
    item = _item(_facts(), _facts(matrix=matrix), name)
    assert (item.item_class, item.status) == (compare.MANDATORY, compare.DIFFERENT)


@pytest.mark.parametrize("name", [SIDE, TKHD], ids=["side", "tkhd"])
@pytest.mark.parametrize(
    ("matrix", "rotation"), [(QUARTER, -90), (MIRRORED, -180)], ids=["quarter", "mirror"]
)
def test_orientation_change_control(name: str, matrix: tuple[int, ...], rotation: int) -> None:
    """A quarter turn or mirrored linear part must still be DIFFERENT."""
    item = _item(_facts(), _facts(matrix=matrix, rotation=rotation), name)
    assert (item.item_class, item.status) == (compare.MANDATORY, compare.DIFFERENT)


def test_ffprobe_rotation_change_control() -> None:
    """Compare ffprobe's rotation even if the linear matrix stays identical."""
    assert _item(_facts(), _facts(rotation=-90), SIDE).status == compare.DIFFERENT


@pytest.mark.parametrize("unset", ["absent", "null"])
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_unset_square_sar_is_equivalent(unset: str, reverse: bool) -> None:
    """Absent and null SAR both mean square pixels when compared with 1:1."""
    source, output = _facts(video={"sample_aspect_ratio": None}), _facts()
    if unset == "absent":
        del source.probe["streams"][0]["sample_aspect_ratio"]
    if reverse:
        source, output = output, source
    item = _item(source, output, GEOMETRY)
    assert (item.item_class, item.status) == (compare.REQUIRED, compare.SAME)


@pytest.mark.parametrize(
    "video",
    [{"sample_aspect_ratio": "4:3"}, {"width": 1280}, {"height": 1080}],
    ids=["nonsquare", "width", "height"],
)
def test_geometry_change_control(video: dict[str, Any]) -> None:
    """A real pixel aspect ratio or frame size change remains DIFFERENT."""
    item = _item(_facts(), _facts(video=video), GEOMETRY)
    assert (item.item_class, item.status) == (compare.REQUIRED, compare.DIFFERENT)


@pytest.mark.parametrize("unset", ["absent", "null"])
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_unset_sar_against_nonsquare_control(unset: str, reverse: bool) -> None:
    """Keep an unspecified SAR different from a non-square pixel aspect ratio."""
    source = _facts(video={"sample_aspect_ratio": None})
    output = _facts(video={"sample_aspect_ratio": "4:3"})
    if unset == "absent":
        del source.probe["streams"][0]["sample_aspect_ratio"]
    if reverse:
        source, output = output, source
    item = _item(source, output, GEOMETRY)
    assert (item.item_class, item.status) == (compare.REQUIRED, compare.DIFFERENT)


@pytest.mark.parametrize("unset", ["absent", "null"])
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_unset_mono_layout_is_equivalent(unset: str, reverse: bool) -> None:
    """Only a one-channel track treats absent layout as declared mono."""
    source, output = _facts(audio={"channel_layout": None}), _facts()
    if unset == "absent":
        del source.probe["streams"][1]["channel_layout"]
    if reverse:
        source, output = output, source
    item = _item(source, output, AUDIO)
    assert (item.item_class, item.status) == (compare.MANDATORY, compare.SAME)


@pytest.mark.parametrize("unset", ["absent", "null"])
@pytest.mark.parametrize("reverse", [False, True], ids=["forward", "reverse"])
def test_two_channel_mono_against_unset_layout_control(unset: str, reverse: bool) -> None:
    """Keep declared mono distinct from absent layout when both have two channels."""
    source = _facts(audio={"channels": 2, "channel_layout": "mono"})
    output = _facts(audio={"channels": 2, "channel_layout": None})
    if unset == "absent":
        del output.probe["streams"][1]["channel_layout"]
    if reverse:
        source, output = output, source
    item = _item(source, output, AUDIO)
    assert (item.item_class, item.status) == (compare.MANDATORY, compare.DIFFERENT)


@pytest.mark.parametrize(
    ("source", "output"),
    [
        ({"channel_layout": None}, {"channels": 2, "channel_layout": None}),
        ({"channels": 2, "channel_layout": "stereo"}, {"channels": 2, "channel_layout": "5.1"}),
        ({"channels": 2, "channel_layout": None}, {"channels": 2, "channel_layout": "stereo"}),
        ({"channel_layout": "mono"}, {"channel_layout": "stereo"}),
        ({}, {"sample_rate": "44100"}),
        ({}, {"codec_name": "aac"}),
    ],
    ids=["channels", "stereo-5.1", "stereo-absent", "mono-stereo", "rate", "codec"],
)
def test_audio_change_control(source: dict[str, Any], output: dict[str, Any]) -> None:
    """Keep channel counts, other layouts, sample rates and codecs exact."""
    item = _item(_facts(audio=source), _facts(audio=output), AUDIO)
    assert (item.item_class, item.status) == (compare.MANDATORY, compare.DIFFERENT)


# WP-DR113: the instrument reads its own Facts; product tables are test inputs only.
_PCM_POSITIVE = ("img6731-coalesced", "img6729-moved-boundary", "gapful-rechunked")
_PCM_D86 = ("d86-55", "d86-70", "d86-85")
_PCM_REFUSED = ("alaw", "mulaw", "bluray", "dvd", "lxf", "s24daud", "sga", "vidc", "unlisted")
_PCM_CONTROLS = (
    "one-sample-fewer",
    "presented-only",
    "stored-only",
    "rate",
    "format",
    "channels",
    "codec-aac",
    "time-base",
    "one-tick-shift",
    "swapped-packets",
    "closed-gap",
    "opened-gap",
    *(f"unknown-{codec}" for codec in _PCM_REFUSED),
)
_PCM_AGREEMENT = (
    *_PCM_POSITIVE,
    *_PCM_D86,
    "one-sample-fewer",
    "presented-only",
    "stored-only",
    "rate",
    "format",
    "channels",
    "time-base",
    "closed-gap",
    "opened-gap",
    "earlier-source-partial",
    "output-partial",
)
_PCM_COUNTS = {
    "img6731-coalesced": (100, 99),
    "img6729-moved-boundary": (133, 133),
    "gapful-rechunked": (3, 3),
    "d86-55": (39, 39),
    "d86-70": (50, 49),
    "d86-85": (61, 61),
}


def _pcm_pair(
    shape: str,
) -> tuple[pcm_units._PcmPacketTable, pcm_units._PcmPacketTable, Fraction | None]:
    """Reuse WP-D112's planted tables, with each additional mutation named explicitly."""
    if shape == "img6731-coalesced":
        # test_io_video_encode_units.py:837-848, presented/stored = 100720/100812.
        source = pcm_units._pcm_table(
            (1024,) * 70 + (508,) + (1024,) * 23 + (736,) + (1024,) * 4 + (148,),
            last_stored_samples=240,
        )
        output = pcm_units._pcm_table(
            (1024,) * 70 + (508,) + (1024,) * 27 + (884,), last_stored_samples=976
        )
        return source, output, None
    if shape == "img6729-moved-boundary":
        # test_io_video_encode_units.py:851-879, presented/stored = 134400/134414.
        source = pcm_units._pcm_table(
            (1024,) * 70
            + (541,)
            + (1024,) * 23
            + (736,)
            + (1024,) * 23
            + (736,)
            + (1024,) * 13
            + (291,),
            last_stored_samples=305,
        )
        output = pcm_units._pcm_table(
            (1024,) * 70
            + (541,)
            + (1024,) * 23
            + (736,)
            + (1024,) * 24
            + (736,)
            + (1024,) * 12
            + (291,),
            last_stored_samples=305,
        )
        return source, output, None
    if shape == "gapful-rechunked":
        # test_io_video_encode_units.py:1137-1143, runs [0,1532], [2048,3072].
        source = replace(pcm_units._pcm_table((1024, 508, 1024)), audio_pts={1: (0, 1024, 2048)})
        output = replace(pcm_units._pcm_table((1532, 512, 512)), audio_pts={1: (0, 2048, 2560)})
        return source, output, None
    if shape in _PCM_D86 or shape in ("earlier-source-partial", "output-partial"):
        percent = int(shape.removeprefix("d86-")) if shape in _PCM_D86 else 70
        source, output, end, _ = pcm_units._truncated_pcm_pair(percent)
        if shape == "earlier-source-partial":
            source = replace(source, audio_sizes={1: (2047, *source.audio_sizes[1][1:])})
        elif shape == "output-partial":
            output = replace(output, audio_sizes={1: (*output.audio_sizes[1][:-1], 1803)})
        return source, output, end

    source = pcm_units._pcm_table()
    output = source
    if shape == "one-sample-fewer":
        output = pcm_units._pcm_table((1024,) * 6 + (1023,))
    elif shape == "presented-only":
        output = pcm_units._pcm_table((1024,) * 6 + (1023,), last_stored_samples=1024)
    elif shape == "stored-only":
        output = pcm_units._pcm_table(last_stored_samples=1023)
    elif shape in ("rate", "format", "channels", "codec-aac", "time-base"):
        changes = {
            "rate": {"sample_rate": 44100},
            "format": {"sample_fmt": "s32"},
            "channels": {"channels": 2},
            "codec-aac": {"codec_name": "aac"},
            "time-base": {"time_base": Fraction(1, 96000)},
        }[shape]
        output = replace(source, streams=(source.video, replace(source.streams[1], **changes)))
    elif shape in ("one-tick-shift", "swapped-packets"):
        pts = list(source.audio_pts[1])
        if shape == "one-tick-shift":
            assert pts[3] is not None
            pts[3] += 1
        else:
            pts[2], pts[3] = pts[3], pts[2]
        output = replace(source, audio_pts={1: tuple(pts)})
    elif shape in ("closed-gap", "opened-gap"):
        # Preserve the run mutations at test_io_video_encode_units.py:1113-1134.
        source = pcm_units._pcm_table(((1024,) * 23 + (472,)) * 3)
        pts = source.audio_pts[1]
        assert all(p is not None for p in pts)
        shifted = tuple(p if i <= 30 else p + 1024 for i, p in enumerate(pts))
        if shape == "closed-gap":
            output = source
            source = replace(source, audio_pts={1: shifted})
        else:
            gapful = tuple(p if i <= 10 else p + 512 for i, p in enumerate(pts))
            source = replace(source, audio_pts={1: gapful})
            output = replace(
                source,
                audio_pts={1: tuple(p if i <= 30 else p + 1024 for i, p in enumerate(gapful))},
            )
    elif shape.startswith("unknown-") and shape.removeprefix("unknown-") in _PCM_REFUSED:
        stream = replace(source.streams[1], codec_name=f"pcm_{shape.removeprefix('unknown-')}")
        source = replace(source, streams=(source.video, stream))
        output = source  # Even identical packet rows cannot establish an unknown PCM width.
    else:
        raise AssertionError(f"unknown PCM test shape: {shape}")
    return source, output, None


def _pcm_facts(table: pcm_units._PcmPacketTable, *, output: bool = False) -> compare.Facts:
    """Adapt the same literal tick/byte table to the independent instrument's Facts."""
    audio = table.of_type("audio")[0]
    base = audio.time_base
    assert base is not None
    facts = _facts(
        audio={
            "codec_name": audio.codec_name,
            "time_base": str(base),
            "sample_rate": str(audio.sample_rate),
            "channels": audio.channels,
            "sample_fmt": audio.sample_fmt,
        }
    )
    packets = []
    for pts, duration, size in zip(
        table.audio_pts[1], table.audio_durations[1], table.audio_sizes[1], strict=True
    ):
        assert pts is not None and duration is not None and size is not None
        packets.append(
            compare.Packet(
                pts * base, duration * base, size, f"MD5:planted-{pts}-{duration}-{size}"
            )
        )
    return replace(facts, path=Path("output.mp4" if output else "source.mov"), packets={1: packets})


def _pcm_audio_items(items: list[compare.Item]) -> list[compare.Item]:
    """Select the real audio-presence and keyed-packet verdicts, excluding unrelated video."""
    return [i for i in items if i.name == AUDIO or i.name.startswith(vf.AUDIO_PACKETS)]


def _pcm_note(before: int, after: int) -> str:
    """State the commissioned disclosure independently of the instrument implementation."""
    return f"PCM: compared by sample extent and timeline runs; packets {before} -> {after}"


def _pcm_fidelity_reading(
    monkeypatch: pytest.MonkeyPatch,
    source: compare.Facts,
    output: compare.Facts,
    end: Fraction | None = None,
    *,
    side_change: str | None = None,
) -> tuple[list[compare.Item], list[str]]:
    """Run the real V4 pipeline with only file-boundary probes supplied synthetically."""
    info = pcm_units._probe()
    if end is not None:
        info = replace(info, faults=(Fault("truncated", "warn", "cut short"),))
    # Readable-end discovery otherwise opens a nonexistent synthetic file's video table.
    monkeypatch.setattr(vf, "_readable_end", lambda path, probe, facts: end)
    # mvhd is an unrelated file read; audio comparisons still consume the real Facts.
    monkeypatch.setattr(vf, "movie_duration", lambda path: Fraction(1, 2))

    def ffprobe(arguments: Any) -> dict[str, Any]:
        facts = {str(source.path): source, str(output.path): output}[str(arguments[-1])]
        entries = arguments[arguments.index("-show_entries") + 1]
        if entries == "packet=pts,flags:packet_side_data":
            base = Fraction(facts.probe["streams"][1]["time_base"])
            packets = [{"pts": int(p.pts / base), "flags": "K_"} for p in facts.packets[1]]
            if facts is output and side_change == "discard":
                packets[2]["flags"] = "KD"
            elif facts is output and side_change == "side-data":
                packets[2]["side_data_list"] = [
                    {
                        "side_data_type": "Skip Samples",
                        "skip_samples": 1,
                        "discard_padding": 0,
                    }
                ]
            return {"packets": packets}
        assert entries == "stream=index,profile,initial_padding,extradata_size,extradata_hash"
        return {"streams": [{"index": 1}]}

    monkeypatch.setattr(compare, "run_ffprobe", ffprobe)
    return vf.fidelity_items(source, output, info=info, bit_depth=8)


@pytest.mark.parametrize("shape", _PCM_POSITIVE)
def test_pcm_sample_extent_equivalence(shape: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Faithful boundary changes preserve both target items and disclose their PCM reading."""
    source_table, output_table, _ = _pcm_pair(shape)
    source, output = _pcm_facts(source_table), _pcm_facts(output_table, output=True)
    item = _item(source, output, f"{vf.AUDIO_PACKETS} [soun#0]")
    note = _pcm_note(*_PCM_COUNTS[shape])
    assert (item.item_class, item.status) == (compare.MANDATORY, compare.SAME)
    assert item.note == note
    items, notes = _pcm_fidelity_reading(monkeypatch, source, output)
    side = next(i for i in items if i.name == "audio priming and packet side data")
    assert side.status == compare.SAME and note in side.note
    assert note in notes
    assert items[-1].name == vf._ROSTER_ITEM and items[-1].status == compare.SAME


@pytest.mark.parametrize("shape", _PCM_CONTROLS)
def test_pcm_difference_control(shape: str) -> None:
    """Refuse damaged extents, changed format/timeline, and unavailable packed-width evidence."""
    before, after, _ = _pcm_pair(shape)
    items = _pcm_audio_items(
        compare.compare_facts(_pcm_facts(before), _pcm_facts(after, output=True))
    )
    assert any(i.status == compare.DIFFERENT for i in items), items
    if shape.startswith("unknown-"):
        packet = next(i for i in items if i.name.startswith(vf.AUDIO_PACKETS))
        assert packet.status == compare.DIFFERENT
        assert f"pcm_{shape.removeprefix('unknown-')}" in packet.note


@pytest.mark.parametrize("shape", _PCM_AGREEMENT)
def test_pcm_instrument_agrees_with_product(shape: str, monkeypatch: pytest.MonkeyPatch) -> None:
    """Both independent readings must agree AND match the hand-specified expected verdict."""
    source, output, end = _pcm_pair(shape)
    expected = shape in (*_PCM_POSITIVE, *_PCM_D86)
    problems = pcm_units._pcm_check(monkeypatch, source, output, end, truncated=end is not None)
    assert (not problems) == expected, problems
    before, after = _pcm_facts(source), _pcm_facts(output, output=True)
    items = compare.compare_facts(before, after)
    if end is not None:
        items = vf._cut_items(items, before, after, end, True)
    audio = _pcm_audio_items(items)
    instrument_same = all(i.status == compare.SAME for i in audio)
    assert instrument_same == (not problems), (audio, problems)
    assert instrument_same == expected


@pytest.mark.parametrize("shape", ["compressed-intact", "compressed-rechunked", "mixed", "absent"])
def test_pcm_compressed_and_absent_paths_unchanged(shape: str) -> None:
    """Keep compressed packet bytes/timing strict, including alongside PCM and without audio."""
    facts = _facts(audio={"codec_name": "aac"})
    a = compare.Packet(Fraction(0), Fraction(1024, 48000), 128, "MD5:compressed-a")
    b = compare.Packet(Fraction(1024, 48000), Fraction(1024, 48000), 96, "MD5:compressed-b")
    source = replace(facts, packets={1: [a, b]})
    output = source
    if shape == "absent":
        source = replace(
            source, probe={"streams": [facts.probe["streams"][0]]}, keys={0: "vide#0"}, packets={}
        )
        item = _item(source, source, vf.AUDIO_PACKETS)
        assert (item.source, item.output, item.status, item.note) == (
            "absent",
            "absent",
            compare.SAME,
            "",
        )
        return
    if shape == "compressed-rechunked":
        output = replace(
            source, packets={1: [compare.Packet(a.pts, a.duration + b.duration, 224, "MD5:joined")]}
        )
    elif shape == "mixed":
        pcm = {**facts.probe["streams"][1], "index": 2, "codec_name": "pcm_s16le"}
        source = replace(
            source,
            probe={"streams": [*facts.probe["streams"], pcm]},
            keys={**facts.keys, 2: "soun#1"},
            packets={
                **source.packets,
                2: [compare.Packet(Fraction(0), Fraction(1, 48000), 2, "MD5:pcm")],
            },
        )
        output = replace(source, packets={**source.packets, 1: [a, replace(b, md5="MD5:changed")]})
    item = _item(source, output, f"{vf.AUDIO_PACKETS} [soun#0]")
    assert item.status == (compare.SAME if shape == "compressed-intact" else compare.DIFFERENT)
    assert item.source == compare._packets_summary(compare._packet_rows([a, b]))
    assert item.output == compare._packets_summary(compare._packet_rows(output.packets[1]))
    assert item.note == (
        ""
        if shape == "compressed-intact"
        else compare._first_difference(
            compare._packet_rows([a, b]), compare._packet_rows(output.packets[1])
        )
    )
