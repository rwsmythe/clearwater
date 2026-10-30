"""WP4.4: narrow V4 equivalences with synthetic facts and real-difference controls."""

from __future__ import annotations

from fractions import Fraction
from pathlib import Path
from typing import Any

import pytest

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
def test_unset_mono_layout_is_equivalent(unset: str, reverse: bool) -> None:
    """Only a one-channel track treats absent layout as declared mono."""
    source, output = _facts(audio={"channel_layout": None}), _facts()
    if unset == "absent":
        del source.probe["streams"][1]["channel_layout"]
    if reverse:
        source, output = output, source
    item = _item(source, output, AUDIO)
    assert (item.item_class, item.status) == (compare.MANDATORY, compare.SAME)


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
