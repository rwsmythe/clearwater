"""Synthetic movie-tick readings (WP7.1); no media, FFmpeg, GPU or entry point."""

from dataclasses import asdict, replace
from fractions import Fraction
from pathlib import Path

import pytest

import video_fidelity as vf
from clearwater.interfaces.image import ColorDescription
from clearwater.interfaces.video import ProbeResult, VideoStreamInfo
from container_spike import compare

NON_VIDEO = "edit lists as written, non-video tracks (media_time in media seconds)"
MOVIE_ROWS = (vf.MOVIE_DURATION, vf.VIDEO_EDIT_AS_WRITTEN, vf.EDIT_EFFECT, NON_VIDEO)
READING = "movie-tick rounding of the exact track value (owner 2026-11-10, AD-22)"


def _facts(*, source: bool, exact: bool = False) -> compare.Facts:
    scale = 1_000_000 if source and not exact else 15_000
    video_ticks = 61_795_134 if source and not exact else 926_927
    audio_ticks = 61_781_333 if source and not exact else 926_720
    video = compare.Track(
        1,
        3,
        "vide",
        "",
        "hvc1",
        (),
        30_000,
        1_853_854,
        (65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824),
        (compare.Edit(video_ticks, 0, Fraction(1)),),
        0,
    )
    audio = compare.Track(
        2,
        3,
        "soun",
        "",
        "mp4a",
        (),
        48_000,
        2_966_528,
        (65536, 0, 0, 0, 65536, 0, 0, 0, 1073741824),
        (compare.Edit(audio_ticks, 1024, Fraction(1)),),
        1024,
    )
    streams = [
        {
            "index": 0,
            "id": "0x1",
            "codec_type": "video",
            "codec_name": "hevc",
            "time_base": "1/30000",
            "duration_ts": 1_853_854,
            "start_pts": 0,
            "pix_fmt": "yuv420p",
            "width": 64,
            "height": 48,
        },
        {
            "index": 1,
            "id": "0x2",
            "codec_type": "audio",
            "codec_name": "aac",
            "time_base": "1/48000",
            "duration_ts": 2_965_504,
            "start_pts": 0,
            "sample_rate": "48000",
            "channels": 2,
        },
    ]
    return compare.Facts(
        Path("source" if source else "output"),
        {"streams": streams, "format": {"duration": "61.795134", "start_time": "0.000000"}},
        compare.Movie((), "isom", (), scale, 0, (video, audio), ()),
        0,
        [Fraction(0), Fraction(1001, 30000)],
        {1: []},
        {0: "vide#0", 1: "soun#0"},
    )


def _track(facts: compare.Facts, index: int, **changes) -> compare.Facts:
    tracks = list(facts.movie.tracks)
    tracks[index] = replace(tracks[index], **changes)
    return replace(facts, movie=replace(facts.movie, tracks=tuple(tracks)))


def _rows(monkeypatch, source, output, *, movie_delta=Fraction(0), end=None):
    # Only disk reads are replaced; all comparison and reading code is real.
    durations = {Path("source"): Fraction(926927, 15000), Path("output"): Fraction(926927, 15000)}
    if source.movie.timescale == 1_000_000:
        durations[Path("source")] = Fraction(30897567, 500000)
    durations[Path("source")] += movie_delta
    monkeypatch.setattr(vf, "movie_duration", durations.__getitem__)
    monkeypatch.setattr(compare, "run_ffprobe", lambda *args: {"streams": [], "packets": []})
    monkeypatch.setattr(vf, "_readable_end", lambda *args: end)
    info = ProbeResult(
        source.path,
        "mp4",
        Fraction(926927, 15000),
        Fraction(0),
        VideoStreamInfo(
            "hevc",
            64,
            48,
            8,
            "yuv420p",
            "left",
            ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None),
            Fraction(30000, 1001),
            Fraction(1, 30000),
            2,
            0,
            False,
        ),
        (),
        (),
        (),
        (),
        None,
    )
    rows, notes = vf.fidelity_items(source, output, info=info, bit_depth=8)
    return {row.name: row for row in rows}, notes


@pytest.mark.parametrize("name", MOVIE_ROWS)
def test_insta360_opposite_rounding_reads_same_with_disclosed_figures(monkeypatch, name):
    rows, notes = _rows(monkeypatch, _facts(source=True), _facts(source=False))
    row = rows[name]
    assert row.status == compare.SAME
    assert READING in row.note and row.note in notes
    assert "source" in row.note and "output" in row.note
    assert "1/1000000" in row.note and "1/15000" in row.note
    assert "926927/15000" in row.note or "23168/375" in row.note


@pytest.mark.parametrize("name", MOVIE_ROWS)
def test_two_microseconds_past_the_source_rounding_still_differs(monkeypatch, name):
    source, output = _facts(source=True), _facts(source=False)
    index = 1 if name == NON_VIDEO else 0
    edit = source.movie.tracks[index].edits[0]
    if name != vf.MOVIE_DURATION:
        source = _track(
            source, index, edits=(replace(edit, segment_duration=edit.segment_duration + 2),)
        )
    rows, _ = _rows(
        monkeypatch,
        source,
        output,
        movie_delta=Fraction(2, 1_000_000) if name == vf.MOVIE_DURATION else Fraction(0),
    )
    assert rows[name].status == compare.DIFFERENT
    assert READING not in rows[name].note


@pytest.mark.parametrize("name", MOVIE_ROWS)
def test_different_exact_track_values_are_not_rounding(monkeypatch, name):
    source, output = _facts(source=True), _facts(source=False)
    index = 1 if name == NON_VIDEO else 0
    output = _track(output, index, media_duration=output.movie.tracks[index].media_duration + 1)
    rows, _ = _rows(monkeypatch, source, output)
    assert rows[name].status == compare.DIFFERENT


def test_exact_gopro_like_durations_keep_the_existing_verdict_without_a_note(monkeypatch):
    rows, notes = _rows(monkeypatch, _facts(source=True, exact=True), _facts(source=False))
    for name in MOVIE_ROWS:
        assert rows[name].status == compare.SAME
        assert READING not in rows[name].note
    assert not any(READING in note for note in notes)


@pytest.mark.parametrize("index", [0, 1])
def test_a_mid_list_media_segment_keeps_its_exact_duration(monkeypatch, index):
    source, output = _facts(source=True), _facts(source=False)
    # The first segment is deliberately one microsecond longer on the source grid.
    source = _track(
        source,
        index,
        edits=(compare.Edit(1_000_001, 0, Fraction(1)), source.movie.tracks[index].edits[0]),
    )
    output = _track(
        output,
        index,
        edits=(compare.Edit(15_000, 0, Fraction(1)), output.movie.tracks[index].edits[0]),
    )
    rows, _ = _rows(monkeypatch, source, output)
    assert rows[vf.VIDEO_EDIT_AS_WRITTEN if index == 0 else NON_VIDEO].status == compare.DIFFERENT
    assert rows[vf.EDIT_EFFECT].status == compare.DIFFERENT


@pytest.mark.parametrize("index", [0, 1])
def test_a_trimmed_tail_or_nonunit_rate_keeps_the_existing_verdict(monkeypatch, index):
    source, output = _facts(source=True), _facts(source=False)
    # A full second short cannot be a rounding of the media end.
    track = source.movie.tracks[index]
    source = _track(source, index, edits=(replace(track.edits[0], segment_duration=60_000_000),))
    rows, _ = _rows(monkeypatch, source, output)
    assert rows[vf.VIDEO_EDIT_AS_WRITTEN if index == 0 else NON_VIDEO].status == compare.DIFFERENT
    source = _facts(source=True)
    source = _track(source, index, edits=(replace(track.edits[0], rate=Fraction(2)),))
    rows, _ = _rows(monkeypatch, source, output)
    assert rows[vf.VIDEO_EDIT_AS_WRITTEN if index == 0 else NON_VIDEO].status == compare.DIFFERENT


def test_one_tick_video_stream_difference_and_other_nonmovie_rows_stay_exact(monkeypatch):
    source, output = _facts(source=True), _facts(source=False)
    output.probe["streams"][0]["duration_ts"] += 1
    baseline = {row.name: row for row in compare.compare_facts(source, output)}
    rows, _ = _rows(monkeypatch, source, output)
    assert rows[vf.VIDEO_DURATION].status == compare.DIFFERENT
    names = [
        name
        for name in baseline
        if name.startswith(
            (
                "video per-frame",
                "start offset:",
                "audio packets",
                "display orientation:",
                "container duration",
            )
        )
    ] + [vf.VIDEO_DURATION]
    for name in names:
        assert asdict(rows[name]) == asdict(baseline[name])


def test_d86_movie_reading_does_not_apply_to_a_cut_short_source(monkeypatch):
    rows, notes = _rows(monkeypatch, _facts(source=True), _facts(source=False), end=Fraction(1))
    for name in MOVIE_ROWS:
        assert READING not in rows[name].note
    assert not any(READING in note for note in notes)


@pytest.mark.parametrize("side", ["source", "output"])
@pytest.mark.parametrize("name", MOVIE_ROWS)
def test_exactly_one_tick_is_outside_the_reading_on_either_grid(monkeypatch, side, name):
    source, output = _facts(source=True, exact=True), _facts(source=False)
    index = 1 if name == NON_VIDEO else 0
    facts = source if side == "source" else output
    edit = facts.movie.tracks[index].edits[0]
    if name == vf.MOVIE_DURATION:
        monkeypatch.setattr(
            vf,
            "movie_duration",
            lambda path: (
                Fraction(926927, 15000) + (Fraction(1, 15000) if path == Path(side) else 0)
            ),
        )
        row = vf.movie_duration_item(source, output, end=None, cut=False)
    else:
        facts = _track(
            facts, index, edits=(replace(edit, segment_duration=edit.segment_duration + 1),)
        )
        source, output = (facts, output) if side == "source" else (source, facts)
        rows, _ = _rows(monkeypatch, source, output)
        row = rows[name]
    assert row.status == compare.DIFFERENT
    assert READING not in row.note


def test_a_missing_track_cannot_be_excused_as_movie_rounding(monkeypatch):
    source, output = _facts(source=True), _facts(source=False)
    output = replace(output, movie=replace(output.movie, tracks=output.movie.tracks[:1]))
    rows, _ = _rows(monkeypatch, source, output)
    for name in (vf.MOVIE_DURATION, vf.EDIT_EFFECT, NON_VIDEO):
        assert rows[name].status == compare.DIFFERENT


def test_empty_edits_count_exactly_in_the_longest_presentation(monkeypatch):
    source, output = _facts(source=True), _facts(source=False)
    source = _track(
        source, 0, edits=(compare.Edit(1_000_000, -1, Fraction(1)), source.movie.tracks[0].edits[0])
    )
    output = _track(
        output, 0, edits=(compare.Edit(15_000, -1, Fraction(1)), output.movie.tracks[0].edits[0])
    )
    rows, _ = _rows(monkeypatch, source, output, movie_delta=Fraction(1))
    # Output mvhd is deliberately NOT extended: equal track ends alone cannot excuse it.
    assert rows[vf.MOVIE_DURATION].status == compare.DIFFERENT
    assert rows[vf.VIDEO_EDIT_AS_WRITTEN].status == compare.SAME
    assert rows[vf.EDIT_EFFECT].status == compare.SAME
    monkeypatch.setattr(
        vf,
        "movie_duration",
        lambda path: (
            Fraction(1)
            + (Fraction(30897567, 500000) if path == Path("source") else Fraction(926927, 15000))
        ),
    )
    row = vf.movie_duration_item(source, output, end=None, cut=False)
    assert row.status == compare.SAME and READING in row.note


def test_rounding_cannot_hide_a_one_sided_composition_offset_convention(monkeypatch):
    source, output = _facts(source=True), _facts(source=False)
    source = _track(source, 0, earliest_composition=100)
    track = output.movie.tracks[0]
    output = _track(
        output,
        0,
        earliest_composition=100,
        media_duration=track.media_duration + 100,
        edits=(replace(track.edits[0], media_time=100),),
    )
    rows, _ = _rows(monkeypatch, source, output)
    assert rows[vf.VIDEO_EDIT_AS_WRITTEN].status == compare.DIFFERENT
