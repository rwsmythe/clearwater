"""Unit tests of the last frame's end (WP7.2): the track's own end wins over a sub-tick edit end.

An Insta360 Studio export writes its edit list in a 1000000 movie timescale, the segment
duration rounded UP from the video track's exact end in 1/30000 ticks, so the edit-list end lies
a fraction of a tick past the track. :func:`verify.frame_end` used to round that fraction up to
a whole extra tick, and the output's last frame lasted one tick longer than the source's. Now the
track's own end (``start_pts + duration_ts``) wins when it lies less than one tick from the
edit-list end; otherwise (no track end known, or a real tail trim) the ceil of the edit-list end
still applies. Synthetic probe results and packet tables only: no file is read.
"""

from __future__ import annotations

from dataclasses import replace
from fractions import Fraction
from pathlib import Path

import pytest

from clearwater.interfaces.image import ColorDescription
from clearwater.interfaces.video import AudioStreamInfo, EditEntry, ProbeResult, VideoStreamInfo
from clearwater.io.video import verify
from clearwater.io.video.probe import VideoProbeError
from clearwater.io.video.verify import PacketTable, SampleTable, StreamRow

TB = Fraction(1, 30000)


def _probe(edit_end: Fraction | None) -> ProbeResult:
    """A source probe whose video edit list is one media segment ending at ``edit_end`` (s)."""
    video = VideoStreamInfo(
        codec="hevc",
        width=64,
        height=48,
        bit_depth=8,
        pix_fmt="yuv420p",
        chroma_siting="left",
        color=ColorDescription("bt709", "bt709", "bt709", "limited", 8, False, None),
        frame_rate=Fraction(30000, 1001),
        time_base=TB,
        nb_frames=4,
        rotation=0,
        vfr=False,
    )
    edits = () if edit_end is None else (EditEntry(edit_end, Fraction(0), Fraction(1)),)
    return ProbeResult(
        path=Path("src.mp4"),
        container="mov,mp4",
        duration_s=edit_end or Fraction(0),
        start_offset_s=Fraction(0),
        video=video,
        audio=(AudioStreamInfo(1, "aac", 48000, 2, Fraction(0)),),
        data=(),
        edit_list=edits,
        faults=(),
        gopro=None,
    )


def _table(
    pts: tuple[int, ...],
    *,
    duration_ts: int | None,
    start_pts: int | None = 0,
    samples: bool = False,
    time_base: Fraction = TB,
) -> PacketTable:
    """A packet table listing ``pts``; with ``samples`` its sample table names the same pts."""
    video = StreamRow(0, "video", "hvc1", time_base, start_pts, duration_ts, "1:1", None, len(pts))
    return PacketTable(
        streams=(video,),
        video_index=0,
        video_pts=pts,
        video_missing_pts=0,
        video_corrupt_pts=(),
        tags={},
        samples=SampleTable(30000, pts) if samples else None,
        sample_pts=pts if samples else None,
    )


def _mixed_track() -> tuple[tuple[int, ...], int]:
    """Twelve samples, steps of 1001 with two of 1002 (as the Insta360 clip), last lasting 1001."""
    steps = (1001, 1001, 1002, 1001, 1001, 1001, 1001, 1002, 1001, 1001, 1001)
    pts = [0]
    for step in steps:
        pts.append(pts[-1] + step)
    return tuple(pts), pts[-1] + 1001


def _edit(track_end: int, movie_timescale: int, *, up: bool) -> Fraction:
    """The track end in seconds, rounded up or down to a whole movie tick."""
    exact = Fraction(track_end, 30000) * movie_timescale
    ticks = -(-exact.numerator // exact.denominator) if up else exact.numerator // exact.denominator
    return Fraction(ticks, movie_timescale)


def test_an_edit_list_rounded_up_to_the_movie_tick_ends_at_the_track_end() -> None:
    pts, track_end = _mixed_track()
    edit = _edit(track_end, 500000, up=True)
    assert track_end < edit / TB < track_end + 1  # the case: a fraction of a tick past the track
    table = _table(pts, duration_ts=track_end, samples=True)
    assert verify.frame_end(_probe(edit), table, pts[-1]) == pts[-1] + 1001 == track_end
    assert verify.frame_end(_probe(edit), table, pts[3]) == pts[4]  # a next pts: unchanged


def test_an_edit_list_rounded_down_to_the_movie_tick_ends_at_the_track_end() -> None:
    pts, track_end = _mixed_track()
    edit = _edit(track_end, 500000, up=False)
    assert track_end - 1 < edit / TB < track_end  # GoPro-like: a fraction of a tick short
    table = _table(pts, duration_ts=track_end, samples=True)
    assert verify.frame_end(_probe(edit), table, pts[-1]) == track_end


@pytest.mark.parametrize(
    ("last_pts", "track_end", "segment_us", "edit_ticks"),
    [
        (1852853, 1853854, 61795134, Fraction(92692701, 50)),  # 62 s, V4-D and A2b
        (13166166, 13167167, 438905567, Fraction(1316716701, 100)),  # 439 s, V4-E
    ],
    ids=["insta360-62s", "insta360-439s"],
)
def test_the_insta360_clips_end_at_their_track_end(
    last_pts: int, track_end: int, segment_us: int, edit_ticks: Fraction
) -> None:
    probe = _probe(Fraction(segment_us, 1_000_000))
    assert verify.presentation_end(probe, _table((0, last_pts), duration_ts=None)) == edit_ticks
    table = _table((0, last_pts), duration_ts=track_end)
    assert verify.presentation_end(probe, table) == edit_ticks  # unchanged: the edit-list end
    assert verify.frame_end(probe, table, last_pts) == track_end  # was track_end + 1


def test_without_a_track_end_a_fractional_edit_end_still_rounds_up() -> None:
    probe = _probe(Fraction(4004, 30000) + Fraction(1, 90000))  # 4004 and 1/3 ticks
    assert verify.frame_end(probe, _table((0, 1001, 2002, 3003), duration_ts=None), 3003) == 4005
    insta = _probe(Fraction(61795134, 1_000_000))
    assert verify.frame_end(insta, _table((0, 1852853), duration_ts=None), 1852853) == 1853855
    other_ticks = _table((0, 1001, 2002, 3003), duration_ts=4004, time_base=Fraction(1, 90000))
    assert verify.frame_end(probe, other_ticks, 3003) == 4005  # a track end in other ticks: unused
    short = _table((0, 1001, 2002, 3003), duration_ts=3003)  # malformed: ends at the last pts
    edge = _probe(Fraction(3003, 30000) + Fraction(1, 90000))
    assert verify.frame_end(edge, short, 3003) == 3004  # never an end at or before the last pts


def test_an_edit_end_within_one_tick_of_a_known_track_end_gives_the_track_end() -> None:
    table = _table((0, 2002, 1001, 3003), duration_ts=4004)
    assert verify.frame_end(_probe(Fraction(4004, 30000) + Fraction(1, 90000)), table, 3003) == 4004
    assert verify.frame_end(_probe(Fraction(4004, 30000) - Fraction(1, 90000)), table, 3003) == 4004
    assert verify.frame_end(_probe(Fraction(4004, 30000)), table, 3003) == 4004
    started = _table((900, 1901, 2902), duration_ts=3003, start_pts=900)  # end = 900 + 3003
    later = _probe(Fraction(3903, 30000) + Fraction(1, 90000))
    assert verify.frame_end(later, started, 2902) == 3903


@pytest.mark.parametrize(
    ("edit_ticks", "expected"),
    [
        (Fraction(3503), 3503),  # a tail trim inside the last frame
        (Fraction(7007, 2), 3504),  # a fractional tail trim: rounds up
        (Fraction(4003), 4003),  # exactly one tick short: a trim, not rounding
        (Fraction(4005), 4005),  # exactly one tick past the media
        (Fraction(4005) + Fraction(1, 3), 4006),  # more than a tick past the media
    ],
    ids=["trim-500", "trim-fractional", "trim-1-tick", "past-1-tick", "past-4-thirds"],
)
def test_an_edit_end_a_tick_or_more_from_the_track_end_keeps_the_ceil(
    edit_ticks: Fraction, expected: int
) -> None:
    table = _table((0, 2002, 1001, 3003), duration_ts=4004, samples=True)
    assert verify.frame_end(_probe(edit_ticks * TB), table, 3003) == expected


def test_a_cut_files_readable_end_takes_the_track_end_for_its_last_sample() -> None:
    # D86: the cut file's listing stops at 1001; its sample table runs to 3003.
    probe = _probe(Fraction(4004, 30000) + Fraction(1, 90000))
    cut = replace(
        _table((0, 1001), duration_ts=4004),
        samples=SampleTable(30000, (0, 1001, 2002, 3003)),
        sample_pts=(0, 1001, 2002, 3003),
    )
    assert verify.readable_end(probe, cut, 1001) == 2002  # the next sample pts, exact
    assert verify.readable_end(probe, cut, 3003) == 4004  # the track's own end
    with pytest.raises(VideoProbeError, match="cut short"):
        verify.readable_end(probe, _table((0, 1001), duration_ts=4004), 1001)
