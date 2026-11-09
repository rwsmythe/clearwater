# WP7.2 -- last-sample end on coarse-edit-list sources (cell report)

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

No build in this turn (dispatch gate after round 0).
