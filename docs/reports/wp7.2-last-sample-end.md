# WP7.2 -- last-sample end on sources whose edit list is rounded to the movie tick (cell report)

Cell `wp72-cell1` (implementer-opus-high), worktree `.worktrees/wp7.2`, base `83d7c9ed`.
Brief `docs/briefs/wp7.2-brief.md` (FINAL, `61c1aae3`).

## Round 0

Read-only inputs: the V4-D, A2b and V4-E compare records under
`.worktrees/wp7.1/work/wp7.1/v4/{v4-bench-hevc62q,v4-hevc62c,v4-bench-hevc439b}/wp3.10/`, and the
62 s source `Insta360/SCUBA vids2.mp4` read with the product's own readers
(`boxes.read_movie_boxes`, `probe.probe`, `verify.read_packet_table`; nothing written).

### Item 1 -- the +1 tick reproduces (from the numbers)

| | 62 s (`SCUBA vids2.mp4`; V4-D and A2b) | 439 s (V4-E record) |
|---|---|---|
| movie timescale (`mvhd`) | 1000000 (brief: 500000 -- the reduced fraction) | 1000000 |
| video edit segment duration | 61795134 (= 30897567/500000 s) | 438905567 |
| track timescale | 30000 | 30000 |
| track `start_pts` / `duration_ts` | 0 / 1853854 | 0 / 13167167 (record: 13167167/30000) |
| frames, pts steps | 1852; 1849 x 1001, 2 x 1002; last pts 1852853 | -- |
| `presentation_end` (`verify.py:652`) | 92692701/50 = 1853854.02 ticks | 1316716701/100 = 13167167.01 |
| `frame_end(last pts)` today (`verify.py:697-701`, ceil) | **1853855** | **13167168** |
| track's own end (`start + duration_ts` = last pts + 1001) | 1853854 | 13167167 |
| output video stream duration (record) | 1853855/30000 (+1 tick) | 13167168/30000 (+1 tick) |

The source muxer (Lavf60.3.100) wrote the video edit in whole microseconds, ROUNDED UP from the
exact track end (61795133.33 us -> 61795134; 438905566.67 us -> 438905567). `frame_end` reads that
as 0.02 / 0.01 tick past the track and rounds up to a whole extra tick. Reproduced on all three
records (A2b's values are identical to V4-D's).

### Item 2 -- callers

| Caller | Function | Wants | Effect of a `frame_end`-only fix |
|---|---|---|---|
| `encode.py:576` `_edit_list_refusal` | `presentation_end` | the EDIT-LIST end (a tail trim is `edit end <= last pts`) | none: `presentation_end` stays the edit-list end |
| `verify.py:697` `frame_end` | `presentation_end` | (the fix site) | -- |
| `encode.py:1312` `_end_stream` | `frame_end` | the last frame's end (the sentinel) | the fix's purpose |
| `verify.py:730` `readable_end` | `frame_end` | the last readable frame's end (D86) | only when the sample table shows no later frame: the track end instead of ceil(edit end) when they agree to under a tick |
| `encode.py:999` `_plan_tracks` | `readable_end` | as above | as above |
| `tools/video_fidelity.py:877` `_readable_end` | `readable_end` | the sink's own rule (shared, so the instrument and sink agree) | follows the sink, unchanged in shape |
| `tests/test_io_video_encode_units.py:624-646` | `frame_end`, `readable_end` | unit pins | `:631-632` pins ceil(edit end) = 4005 over a KNOWN track end 4004 (edit 1/3 tick longer) -- the defect class itself; it would be re-pointed at the no-duration case |

No caller besides `_edit_list_refusal` uses `presentation_end`, and it must keep the edit-list end:
so the fix belongs in `frame_end`, not in `presentation_end`.

### Item 3 -- the fix shape

`frame_end`, last-frame branch only: the track's own end in ticks (`start_pts + duration_ts` from
the packet table's video row) wins when it differs from the edit-list end by LESS than one tick;
otherwise, or when no track end is known, today's ceil of `presentation_end`. Note:
`SampleTable` stores composition times only (`verify.py:72-83`, `:476-499`), not the last `stts`
delta, so "last pts + last sample duration from the sample table" needs `duration_ts` (or a new
`SampleTable` field); `duration_ts` gives 1853854 here, exact.

Cases that legitimately differ by a tick or more, kept as today and to be tested:
- an edit list that trims the tail inside the last frame (edit end = last pts + 500, track end =
  last pts + 1001): `_edit_list_refusal` accepts it (edit end > last pts); today `frame_end` =
  ceil(edit end) = last pts + 500, the last frame is shortened to the edit -- kept;
- an edit list running a tick or more past the media: today ceil(edit end) -- kept.

### Item 4 -- the movie-level rows do NOT clear with the video end (STOP)

The fix brings the output video TRACK to the source's track end. The other three MANDATORY rows
compare movie-timescale values exactly (`tools/container_spike/compare.py:725` `exact`,
`_edits_as_written`, `edit_effect`; `tools/video_fidelity.py:1107` `movie_duration_item`), and
the output's movie grid represents track ticks exactly (today its edit list is 370771/6000 =
1853855/30000, its track end; audio 23168/375 = 2965504/48000). After the fix the output writes
the exact track end, while the source wrote the end rounded to 1 us:

| Row (62 s) | source | output after a `verify.py` fix | difference |
|---|---|---|---|
| video stream duration | 926927/15000 | 926927/15000 | SAME |
| mvhd (presentation form, exact) | 30897567/500000 | 926927/15000 | 1/1500000 s |
| edit list, video, as written | 30897567/500000 | 926927/15000 | 1/1500000 s |
| edit effect: vide | 30897567/500000 | 926927/15000 | 1/1500000 s |
| edit effect: soun (TODAY too) | 61781333/1000000 | 23168/375 | 1/3000000 s |

439 s: video 438905567/1000000 vs 13167167/30000 (1/3000000 s); audio 219445333/500000 vs
164584/375 (1/1500000 s). The audio row differs TODAY and is independent of the video end: the
source wrote the exact audio end ROUNDED DOWN to 1 us (61781333.33 -> 61781333;
438890666.67 -> 438890666), the video ROUNDED UP. The brief's out-of-scope clause asks for a STOP
with the numbers when the audio row does not clear with the video end; three of the four rows
cannot clear by a change inside `verify.py`: clearing them needs the instrument's comparison
(`tools/video_fidelity.py` / `compare.py`, not owned, "a finding there is a STOP") or the
output's movie timescale and its rounding (`encode.py`, not owned), or a ruling on AD-22.

No build in turn 1 (dispatch gate after round 0); the build followed CHARC's ruling below.

## Ruling (CHARC, mail `708c3a6b`; dispatch 2)

Q1 (a) granted: build the `frame_end` fix; `presentation_end` unchanged. Q1 (b), the movie-level
reading, is held for the owner and out of this package. The brief's Done line is amended: the
video stream duration SAME on the re-run; the three movie-level rows per the Q1 (b) ruling.

## The fix

`verify.py` `frame_end`, last-frame branch only (no next pts in the sample table or listing):
the track's own end `_track_end` = `start_pts + duration_ts` (None without a duration, or when
the stream's time base is not the probe's video time base) is returned when it ends after
`last_pts` and lies LESS than one tick from `presentation_end`; otherwise the ceil of
`presentation_end` as before. `presentation_end`, `readable_end` and every signature and
caller are unchanged. Arithmetic is exact (`Fraction` against `int`).

Where the result changes: only when the edit-list end lies strictly within one tick ABOVE the
track end (`track < end < track + 1`): today `track + 1`, now `track`. An end within a tick
below the track (rounded down) already gave `track` by the ceil; an end a whole tick or more
away (a tail trim, or an edit past the media) and an end with no track end known keep the
ceil. GoPro: a source whose edit-list end is a whole number of ticks (its movie timescale
divides the track's) is unchanged by construction; the seat's serial leg (`footage` tests:
`tests/test_video_fidelity.py`, `tests/test_v51_video_acceptance.py`) is the proof on footage.

D86: `readable_end` calls `frame_end`; on a cut file the next pts still comes from the sample
table (exact, unchanged); only its last sample takes the track end under the same rule.

## Tests

New `tests/test_io_video_verify_end.py` (synthetic; no file read). The existing
`tests/test_io_video_encode_units.py:631-632` case (edit 4004 + 1/3 tick over a known track end
4004, which pinned 4005) is re-pointed to a table without a stream duration (ruling (a)); the
within-one-tick rule is pinned in the new file.

RED on the base code (`83d7c9ed`'s `verify.py`; `work/t2-red.log`): 5 failed, 8 passed.

| Test | Base | Fix |
|---|---|---|
| `test_an_edit_list_rounded_up_to_the_movie_tick_ends_at_the_track_end` (500000, mixed 1001/1002) | FAIL 12015 != 12014 | PASS |
| `test_an_edit_list_rounded_down_to_the_movie_tick_ends_at_the_track_end` | pass | PASS |
| `test_the_insta360_clips_end_at_their_track_end[insta360-62s]` | FAIL 1853855 != 1853854 | PASS |
| `test_the_insta360_clips_end_at_their_track_end[insta360-439s]` | FAIL 13167168 != 13167167 | PASS |
| `test_without_a_track_end_a_fractional_edit_end_still_rounds_up` (4005; 1853855) | pass | PASS |
| `test_an_edit_end_within_one_tick_of_a_known_track_end_gives_the_track_end` | FAIL 4005 != 4004 | PASS |
| `test_an_edit_end_a_tick_or_more_from_the_track_end_keeps_the_ceil` (5 cases) | pass | PASS |
| `test_a_cut_files_readable_end_takes_the_track_end_for_its_last_sample` (D86) | FAIL 4005 != 4004 | PASS |
| `test_io_video_encode_units.py::test_frame_end_is_the_next_source_pts_else_the_presentation_end` | pass | PASS |

GREEN: `test_io_video_verify_end.py`, `test_io_video_encode_units.py` (whole module) and
`test_container_spike_compare_equivalences.py`: 243 passed. D86 / cut-short selection of
`test_io_video_encode.py` (`-k "truncated or cut or readable or tail"`, unmarked only): 12
passed, among them `test_a_truncated_source_cuts_audio_at_the_readable_end` and
`test_a_source_cut_at_a_packet_boundary_ends_at_its_last_readable_frame`. ruff, ruff format
and mypy clean.

## Movie-level rows

The fix clears the video stream duration row only. The three movie-level rows compare
movie-timescale values exactly and the source wrote them rounded to 1 us (Item 4 above);
predicted on the 62 s re-run:

| Row | source | output after the fix | difference |
|---|---|---|---|
| video stream duration | 926927/15000 | 926927/15000 | SAME |
| mvhd (presentation form, exact) | 30897567/500000 | 926927/15000 | 1/1500000 s |
| edit list, video, as written | 30897567/500000 | 926927/15000 | 1/1500000 s |
| edit effect: vide | 30897567/500000 | 926927/15000 | 1/1500000 s |
| edit effect: soun (today too) | 61781333/1000000 | 23168/375 | 1/3000000 s |

These three rows are judged per CHARC's Q1 (b) ruling, held for the owner. This report makes no
claim that they clear.

## Reviewer A (Codex, at the cell's seat; evidence `clearwater-review-evidence/wp7.2/A/`)

| Round | Diff | Banner | Findings | Verdict | Disposition |
|---|---|---|---|---|---|
| r1 | `83d7c9ed..74a1dbf2` | gpt-6.1-sol, high | 1 NIT: `verify.py:685`, `:708` called a 1000000 movie timescale "coarser" than 30000 (it is finer; it cannot hold the exact end) | NO_NEW_CRITICAL_MAJOR | FIX (wording, docstring and comment; report title) |
| r2 | `74a1dbf2..b772f63d` (delta) | gpt-6.1-sol, high | none | NO_NEW_CRITICAL_MAJOR | converged |
