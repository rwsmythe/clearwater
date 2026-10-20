# WP3.7 ledger -- video probe and input validation

Cell: `implementer-sonnet-high`, worktree `.worktrees/wp3.7`, branch `wp3.7`, base `9735282`.
Tier STRONG. Brief `docs/briefs/wp3.7-brief.md` (FINAL; rulings 7.1-7.8, 7.3 amended).

## Round 0 -- mapping tables (no product code yet)

Grounded on the WP2.3 manifest (`tests/fixtures/manifest.json`), the sample files probed with
ffprobe 9.0.2 on this machine, and WP1.5 section 3.

### (c) The ffprobe command lines (all `-v error`, argv lists, no shell, timeout 120 s)

1. Container and streams: `ffprobe -v error -of json -show_format -show_streams <path>`.
   `side_data_list` (display matrix) is part of `-show_streams`; checked on `rotated.mp4`.
2. Video packets: `ffprobe -v error -of json -select_streams v:0 -show_entries
   packet=pts,duration,flags <path>`. Integer ticks only (`pts` is an integer in the JSON; `flags`
   carries `K` keyframe and `C` corrupt). No decode. Gives the VFR test, the readable packet count
   and the last keyframe.
3. Tail decode, only when the file is not already `truncated` (bounded to the last GOP):
   `ffprobe -v error -of json -select_streams v:0 -read_intervals <t_kf>% -show_entries
   frame=pts <path>`, where `<t_kf>` is the last keyframe's pts as a decimal rounded UP at the
   sixth place (a seek position only; no reported time is ever parsed from a decimal).
   stderr and the frame count are inspected, see `unreadable_tail`.

`ffprobe` is found by one locator in `probe.py` (`shutil.which`; absent: `VideoProbeError` with
kind `"missing_tool"` and an install hint). It also serves `ffmpeg` for WP3.9/3.10 (ruling 7.8);
it lives in `probe.py` because no separate locator file is in the brief's owned list.

Verified live: `rotated.mp4` side data `rotation: 90` with matrix `[0 -65536; 65536 0]`;
`truncated.mp4` prints `stream 0, offset 0x86a1: partial file` on stderr under `-v error`, lists
25 video packets (the 25th flagged `C`, ending exactly at EOF) against `nb_frames` 45; a copy of
`hevc8-bt709-full.mp4` with the last packet's payload overwritten decodes 44 of 45 frames and
prints `[hevc @ ...] alignment_bit_equal_to_one=0` under command 3, while the intact file prints
nothing and yields all frames of the interval.

### (a) Colour: ffprobe values to IF-1 (D54)

Absent keys, `unknown` and `unspecified` all count as MISSING. A recognised value maps; a present
but unrecognised value is UNEXPECTED. Each field is resolved on its own: missing or unexpected
takes its D54 value (BT.709 / BT.709 / BT.709 / limited), `assumed=True` if any field did, and
ONE `missing_tags` warning names the defaulted fields and says which were missing and which
unexpected.

| Field | ffprobe `color_*` value | IF-1 value |
|---|---|---|
| primaries | `bt709` | `bt709` |
| primaries | `smpte432` | `display-p3` |
| primaries | missing, or anything else (`bt2020`, `bt470bg`, `smpte170m`, `smpte431`, ...) | `bt709` (D54, assumed) |
| transfer | `bt709` | `bt709` |
| transfer | `iec61966-2-1` | `srgb` |
| transfer | `arib-std-b67` | HLG: refuse fault, `transfer="unknown"`, `assumed=False` (ruling 7.6) |
| transfer | `smpte2084` | PQ: same |
| transfer | missing, or anything else (`smpte170m`, `linear`, `gamma22`, `smpte240m`, log curves) | `bt709` (D54, assumed) |
| matrix | `bt709` | `bt709` |
| matrix | `smpte170m`, `bt470bg` | `bt601` |
| matrix | `gbr` | `identity` |
| matrix | missing, or anything else (`bt2020nc`, `bt2020c`, `smpte240m`, `ycgco`, `fcc`) | `bt709` (D54, assumed) |
| range | `pc` | `full` |
| range | `tv` | `limited` |
| range | missing and `pix_fmt` starts `yuvj` | `full`, NOT assumed, no `missing_tags` for range (ruling 7.3 amended) |
| range | missing, any other `pix_fmt` | `limited` (D54, assumed) |

`bit_depth` comes from `pix_fmt` (`yuv420p`/`yuvj420p` = 8; `yuv420p10le` = 10): regex
`^yuvj?4\d\dp(\d\d)?(le|be)?$`; no digits = 8. 8 and 10 only; any other pix_fmt or depth raises
`VideoProbeError` kind `"unsupported"` (5.2 names 8 and 10). 4:2:0, 4:2:2 and 4:4:4 are all passed
through; chroma handling is WP3.9/3.5's.

HLG/PQ result: the other colour fields carry what the tags say where the vocabulary has it, else
`"unknown"` (for the manifest samples: primaries `unknown`, matrix `unknown`, transfer `unknown`,
range `limited`, `assumed=False`); the `refuse` fault is the signal and the file is never decoded.

Resolved samples (expected): `hevc8-bt709-full`, `rotated`, `vfr`, `truncated` = bt709/bt709/bt709
full, not assumed; `hevc10` = bt709 limited, not assumed; `untagged` (H.264, `pix_fmt yuv420p`, no
colour keys) = bt709/bt709/bt709 limited, `assumed=True`, one `missing_tags`.

Other `VideoStreamInfo` fields: `codec` = `codec_name` (accepted `hevc`, `h264`); `chroma_siting` =
`chroma_location` as is, missing/`unspecified` = `"unknown"`; `frame_rate` = `avg_frame_rate`
as a `Fraction` of the rational string (`0/0` falls back to `(n-1)` frames over the pts span);
`time_base` = `Fraction` of the rational string; `nb_frames` = int or None (`N/A`, absent);
`rotation` below; `width`/`height` = the stream's `width`/`height` (the display size ffprobe
reports; for the manifest samples 320x180, with `coded_height` 184 ignored).

Container and codec gate (ruling 7.2): `format_name` must contain `mp4` or `mov` (ffprobe returns
`mov,mp4,m4a,3gp,3g2,mj2` for both) and the video codec be `hevc` or `h264`; else
`VideoProbeError` kind `"unsupported"`. More than one video stream (out of envelope): the first is
used. No video stream: `"unsupported"`.

Rotation (AD-20, counter-clockwise positive): the video stream's display-matrix side data
`rotation`, as an integer, normalised `% 360`; a value that is not a multiple of 90 rounds to the
nearest multiple of 90 (QUESTION Q1 below). No side data: 0. The mirrored case of a matrix
(negative determinant) is not representable in IF-5 and is ignored (out of envelope).

### (b) Faults: detection rule and severity

| Kind | Severity | Rule | Message (user-readable, G10, ASCII) |
|---|---|---|---|
| `hlg` | refuse | video `color_transfer == "arib-std-b67"` | "This video uses HLG HDR, which Clearwater does not support. Re-record in standard (SDR) mode." |
| `pq` | refuse | video `color_transfer == "smpte2084"` | same with "PQ (HDR10)" |
| `missing_tags` | warn | any of primaries / transfer / matrix / range defaulted per table (a); also raised by the GP-Log "no transfer tag on a Protune clip" case | "The video's colour tags are missing (or unexpected): <fields>. Clearwater assumes BT.709, limited range." (field list and defaults are named) |
| `gp_log` | warn | `GoProInfo` present and (`color_profile` non-empty and not in `NATURAL`/`FLAT`/`VIBRANT`, compared upper-case) OR (`protune is True` and the transfer tag is missing) | "This looks like a GoPro Log / Protune clip (<reason>). Clearwater does not convert it; the result may look wrong." |
| `truncated` | warn | `-show_packets` run (command 2) satisfies ANY: stderr names `partial file`; the readable video packet count is below `nb_frames`; the last packet carries the `C` flag | "The file is cut short: only <n> of <m> frames are readable. Clearwater will process up to the readable part." |
| `unreadable_tail` | warn | not `truncated`, and the bounded tail decode (command 3) writes any stderr line, or yields fewer frames than packets from the last keyframe on | "The end of the file cannot be decoded. Clearwater will process up to the last readable frame." |
| `sidecar` | exclude | extension `.lrv`/`.thm` (case-insensitive); produced by the filter, never by `probe` | "<name> is a camera proxy/thumbnail file and is not used as an input." |

`truncated` and `unreadable_tail` are mutually exclusive in a result (a cut file's tail is
`truncated`). Fault order in the tuple: hlg/pq, missing_tags, gp_log, truncated/unreadable_tail.
Intact manifest samples (hevc8, hevc10, rotated, vfr, untagged beyond its `missing_tags`) must
yield no `truncated`/`unreadable_tail`: the truncated sample is the only one, and the corrupted-
last-packet copy built in the test proves `unreadable_tail`.

`probe` on a `.lrv`/`.thm` path raises `VideoProbeError` kind `"sidecar"` without running ffprobe
(ruling 7.7). Unreadable file (ffprobe nonzero exit, empty or non-JSON output, no streams, no
`moov`): `VideoProbeError` kind `"unreadable"`, message "cannot be read at all" (5.4).
`VideoProbeError` is a single class in `io.video`, with a `kind` attribute (`unreadable`,
`unsupported`, `sidecar`, `missing_tool`).

### Timing rules (exact Fractions, no float)

- `time_base`, `avg_frame_rate`: `Fraction(str)` of the rational string. Every other time =
  integer ticks x a stream time base.
- `duration_s` = max over the video and audio streams of `duration_ts x time_base` (what
  ffprobe's `format.duration` is, minus its decimal rounding); fallback `(max pts + duration of
  that packet) x time_base` from command 2. Manifest: 45045/30000 = 3003/2000 s.
- `start_offset_s` = min over the video and audio streams of `start_pts x time_base`
  (ffprobe's `format.start_time`); 0 when no stream carries one.
- `AudioStreamInfo.start_s` = `start_pts x time_base`, 0 when absent.
- `EditEntry.segment_duration_s` = segment duration ticks / movie timescale (`mvhd`);
  `media_time_s` = media time ticks / media timescale (`mdhd` of the video trak), None for
  `media_time = -1`; `media_rate` = `Fraction(int32 media_rate, 65536)` (16.16 fixed).

### VFR rule (D95)

Sort the video packets' pts (presentation order, so B-frame reordering is irrelevant), take the
successive differences in integer ticks. CFR when there are zero or one difference value (every
step the same integer tick count); VFR otherwise. The LAST frame has no following frame, so its
own duration is NOT counted as a step (a differing last-sample duration alone does not flag VFR;
timing is preserved exactly either way). Fewer than 2 frames: CFR. Manifest: `vfr.mp4` steps
{1001, 2002} = VFR, `avg_frame_rate` 22500/1001; all others CFR with step 1001.

### (d) GPMF keys decoded (`gopro.py`, from `moov/udta/GPMF` only)

`FMWR` (type `c`) -> `firmware`; `PRTN` (type `c`, `Y`/`N`) -> `protune` (`Y` True, `N` False,
other None); `PTCL` (type `c`) -> `color_profile`. Strict KLV: 4-char key, type byte, size byte,
big-endian uint16 repeat; payload = size x repeat, padded to 4; every length checked against the
enclosing bound; nesting depth capped at 8; loop makes forward progress by >= 8 bytes. Type-0
items are STRUCTURAL: the walker enters them (WP1.5 found the keys in nested streams) but a leaf
is decoded only when its key is one of the three; every other leaf is skipped by its length, its
bytes never turned into text or numbers. First occurrence of each key wins. A malformed atom
gives `gopro=None` and a note (a `VideoProbeError`-free path: the note is carried as a module-
level logger warning, since `ProbeResult` has no notes field; QUESTION Q2). A file without a
`GPMF` atom gives `gopro=None`. Never touched: the `gpmd` track payload (the probe never reads
mdat), `ACCL GYRO GRAV CORI IORI GPS*`, `HDRV`, `BITR`, serial/identifier atoms.

`boxes.py` reads only `moov`: top-level boxes are walked by size (64-bit `largesize`, size 0 =
to end of file) without reading `mdat`; `moov` is read whole (cap 512 MiB); within it
`mvhd`, `trak/tkhd`, `trak/mdia/{mdhd,hdlr}`, `trak/edts/elst`, `udta/GPMF`. Child boxes are
bounds-checked against the parent, a box smaller than its header or past the parent ends the walk
with a `BoxError`, and the walk always advances.

### Open questions (answers assumed as written unless the dispatcher rules otherwise)

- **Q1.** Display matrix rotation that is not a multiple of 90 (or a mirrored matrix): IF-5 has
  no fault kind. Assumed: round to the nearest multiple of 90 and ignore a mirror (out of
  envelope). Alternative: refuse as `"unsupported"`.
- **Q2.** `ProbeResult` has no field for "GPMF atom malformed" (brief task 5: `gopro=None` "with a
  note"). Assumed: the note goes to a `logging` warning (message names the file, no atom bytes) and
  is returned nowhere; no fault is added (no FaultKind fits).
- **Q3.** `smpte170m`/`bt470bg` matrix maps to `bt601`; primaries `smpte170m`/`bt470bg` are treated
  as unexpected (assumed BT.709) rather than mapped, as IF-1 has no SD primaries value. Confirm.
- **Q4.** The brief's `truncated` sentence (sample table points past the end of the file) is
  implemented as "packet count below `nb_frames` / `C` flag / `partial file`" from ffprobe's own
  container walk, which is the same condition without a second sample-table parser. Confirm that
  this reading satisfies ruling 4.

### Round ledger

| Round | Counts (crit/major/minor) | In-env / out | NEW / REOPENED | Reverts | Fix type | Transport / CLI | Depth |
|---|---|---|---|---|---|---|---|
| 0 (mapping tables) | -- | -- | -- | -- | -- | -- | 90,520 (cell_depth.py, 17 turns) |

### Round-0 rulings (orchestrator gen 5, applied)

- Q1 AMENDED: a rotation that is not a multiple of 90, or a mirrored matrix, is refused
  (`VideoProbeError` kind `"unsupported"`, message names the angle or says "mirrored"); no rounding.
- Q2 ACCEPTED: a malformed GPMF atom gives `gopro=None` and one structural warning on the
  `clearwater.io.video.probe` logger (no bytes, no values); no fault; GP-Log by `PTCL` is
  unavailable for that file.
- Q3 ACCEPTED as tabled. Q4 ACCEPTED, with: (i) without `nb_frames` only `partial file` and the
  `C` flag apply; (ii) the no-false-positive proof covers every intact sample (done below).
- Locator public: `clearwater.io.video.find_tool(name)`.

### Build notes (differences from the round-0 text)

- Command 1 names its fields (`-show_entries format=format_name:stream=<fields>:stream_side_data=
  rotation,displaymatrix`) instead of `-show_format -show_streams`: container and stream tags
  (identifiers, timecode, creation time) are never requested. Same JSON for every field used.
- Command 3 uses `-read_intervals <t>%+86400`, not `<t>%`. MEASURED on ffprobe 9.0.2: an
  open-ended interval returned a partial frame list with exit 0 and empty stderr about 1 run in
  50 (hevc10: 19 of 400 at `0.000000%`, 14 of 500 at `0.5%`), so the first build reported
  `unreadable_tail` on an intact sample once in 160 probes. With an explicit end: 0 of 500 on three
  samples and 0 of 400 probes of four samples. Pinned by a test on the command.
- `clearwater.io.video.probe` the function shadows the submodule attribute of the same name
  (the IF-5 name and the brief's file name collide); callers use the function, tests fetch the
  module with `importlib.import_module`.

### Verification record (own pass, before Reviewer A)

| Item | Status |
|---|---|
| Flaky `unreadable_tail` on an intact sample (open-ended read interval) | suspected by a once-failing test; confirmed by a 400-run loop; fixed (explicit end); stress 400 probes clean |
| All 35 real clips of the footage folder (read only) probed | confirmed: 0 faults, 0 errors, all CFR, rotation 0, `yuvj420p` full; 34 carry GoPro settings, the edit has none; 54.8 s total, GX011625 (14,938 frames, 4K) 1.5 s |
| Gates | ruff check, ruff format --check, mypy strict clean; own tests 131 passed (full pytest awaits a window) |

### Depth record

| Yield | Depth (dispatcher-read) |
|---|---|
| Round 0 | 90,520 (17 turns) |
| Build complete, window requested | 189,350 (68 turns) |

## Reviewer A

Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp3.7\r1\` (prompt, diff, `review.txt`, `full-transcript.txt`, `md5s.txt`).
Transport WSL, `codex-cli 0.162.1`, `gpt-5.6-sol` effort high, read-only sandbox. Green before review: full pytest on `c379284`, 1269 passed (602 s), ruff, ruff format --check, mypy strict.

### Round 1 (head c379284; diff 2278 lines, `src` and `tests` only)

Mechanical assertions: banner model and effort match STRONG; no `ERROR` line; `tokens used` footer present; VERDICT line present; 17 `succeeded in` lines; the only `docs/proofs` strings in the transcript are the prompt echo, the brief's own text and the exclusion globs in the reviewer's commands (no ledger line leaked). The sandbox had no `uv` or `ffprobe`, so findings are on in-memory files and stubbed JSON (EXECUTED) as tagged.

Verdict: `NEW_CRITICAL_MAJOR_FOUND`. Counts: critical 0, major 4, minor 2; all NEW, none REOPENED; all in envelope.

| # | Sev | Where | Finding | Adjudication |
|---|---|---|---|---|
| 1 | MAJOR | `boxes.py` `read_movie_boxes` | Reads 16 header bytes for every box: 8 bytes of an ordinary `mdat` payload are consumed; the regression test only used a 16-byte extended-size header with a loose bound | CONFIRMED real (my claim "never reads mdat" is false by 8 bytes). Fix: read 8, and 8 more only when size == 1; test with an 8-byte-header `mdat` and a read-recording check that no read reaches past the header. Product + test |
| 2 | MAJOR | `probe.py` duration | `duration_s` = max over video and audio streams (ffprobe `format.duration` semantics), not the video track duration; the fallback uses the last packet in FILE order | SPLIT. Fallback defect CONFIRMED (B-frame order): fix to the packet with the highest pts. Choice of stream is a SPEC QUESTION for the dispatcher: IF-5 says "the duration in seconds" of the file; the manifest records the video track. Recommend keeping the container duration (it is what a player shows and what WP3.10 must reproduce), and say so in the report |
| 3 | MAJOR | `probe.py` `_tail_fault` | The tail decode runs for HLG/PQ files, which ruling 7.6 says are "never decoded" | CONFIRMED. Fix: skip the tail check for a refused HDR file. Product + test (no third ffprobe call) |
| 4 | MAJOR | `probe.py` `_tail_unreadable` | Compares only the maximum pts; with B-frames a dropped last packet's frame is not the maximum | CONFIRMED. Fix: every packet from the last keyframe on must have its pts delivered. Product + test with reordered pts and a stubbed decode |
| 5 | MINOR | `boxes.py` | A non-`moov`, non-`mdat` top-level box past the file end is not rejected | Accept; fix in the terminating cleanup (a `mdat` past the end is normal for a cut file) |
| 6 | MINOR | `inputs.py`, `probe.py` | Messages interpolate the file name, which can be non-ASCII | Accept; fix in the terminating cleanup (replace non-ASCII in the name) |

Fixes pending: findings 1-4, all PRODUCT code; none applied yet (round boundary).

### Round 1 remediation (applied after the round-1 rulings; depth at round-1 yield 215,371, 86 turns)

Rulings: 1, 2a, 3, 4 accepted as planned; 2b RULED: `duration_s` is the CONTAINER duration, exact (integer `duration_ts` x `time_base`, never ffprobe's decimal `format.duration`; the code already did this); 5 and 6 fixed now.

| Finding | Product change | Test (fails on the unfixed code) |
|---|---|---|
| 1 | `read_movie_boxes` reads 8 header bytes, 8 more only for a 64-bit size | `test_the_reader_takes_exactly_the_header_bytes_of_the_media_data_box` (reads inside the `mdat` == `[(start, 8)]`), `test_a_64_bit_media_data_header_...` |
| 2a | duration fallback uses the packet with the highest pts | `test_the_duration_fallback_uses_the_packet_with_the_highest_pts` |
| 2b | no code change; documented | `test_the_container_duration_is_the_longest_stream_and_exact` (passes both ways by design: it pins the ruling) |
| 3 | `_tail_fault(..., decode_tail=False)` for HLG/PQ | `test_a_refused_file_is_never_decoded_not_even_for_the_tail` (2 calls, no `-read_intervals`) |
| 4 | tail requires a delivered frame for every packet pts >= last keyframe pts | `test_a_dropped_last_packet_is_found_when_frames_are_reordered`, `test_frames_before_the_last_keyframe_are_not_required` |
| 5 | non-`mdat` top-level box overrunning the file raises `BoxError` | `test_a_box_other_than_media_data_that_overruns_the_file_raises`, `test_media_data_that_overruns_a_cut_file_is_not_an_error` |
| 6 | `ascii_text` (backslash escapes) on file names and the profile in every message | `test_messages_are_ascii_even_for_non_ascii_names` |

Checks after the fixes: own tests 141 passed; ruff, ruff format --check, mypy strict clean; stash check: with the unfixed `probe.py`/`inputs.py` 5 new probe tests fail, with the unfixed `boxes.py` 3 new box tests fail; stress 160 probes clean; all 35 real clips again 0 faults 0 errors (52.1 s). Full pytest window requested for the head after this remediation.

| Yield | Depth (dispatcher-read) |
|---|---|
| Round 1 verdict | 215,371 (86 turns) |
| Round 1 remediation, window requested | 246,372 (111 turns) |

### Round 2 (head beb37a9; diff 2455 lines, `src` and `tests`, cumulative)

Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp3.7\r2\` (prompt with a "THIS IS ROUND 2" section, diff, `review.txt`, `full-transcript.txt`, `md5s.txt`). Green before review: full pytest on `beb37a9`, 1279 passed (525 s), exit 0; ruff, ruff format --check, mypy strict clean. Mechanical assertions: model gpt-5.6-sol and effort high, no `ERROR` line, one `tokens used` footer, VERDICT present, 12 `succeeded in` lines; the `docs/proofs` strings in the transcript are the prompt echo, the brief's text and the exclusion globs (no ledger line leaked). The sandbox had no `uv`, `pytest` or `ffprobe`; findings are on isolated pure-Python probes (EXECUTED).

Verdict: `NEW_CRITICAL_MAJOR_FOUND`. Counts: critical 0, major 1 (DISPUTED, see 1), minor 3. All four NEW, none REOPENED; none of round 1's six findings was re-reported (all six fixes accepted by the reviewer).

| # | Sev | Where | Finding | Adjudication |
|---|---|---|---|---|
| 1 | MAJOR | `boxes.py` / `probe.py` `duration_s` | `mvhd` duration is discarded; the probe always takes the longest stream duration; the reviewer reads IF-5 as "`mvhd` duration over its timescale, the longest stream only as the fallback" | DISPUTED, not upheld by the cell. IF-5 (CHARC `4174484`) and ruling 2b give the two forms as alternatives joined by "or": "`mvhd` duration over its timescale, OR the longest stream in integer ticks times its time base"; the cell takes the second form, exact. Measured on the four video samples: `mvhd` duration over timescale (360360/240000, 320320/240000) equals the stream maximum exactly, so the two forms agree on every sample. If CHARC wants the `mvhd` form as primary it is a small change (a `movie_duration` field in `MovieBoxes`, stream maximum as fallback) and the two duration tests change; the cell does NOT make it without a ruling |
| 2 | MINOR | `boxes.py` | A non-`mdat` box that overruns the file AFTER `moov` is not rejected (the reader returns at `moov`) | Accept as documented behaviour: the reader's duty ends at `moov`; a later overrun is typically a cut `mdat`. Doc sentence in the terminating cleanup, no code change |
| 3 | MINOR, OUT-OF-ENVELOPE | `gopro.py` | `MAX_DEPTH` 8 allows seven nested containers, not eight (root starts at depth 1) | Accept; fix in the terminating cleanup (start at 0, adjust the test) |
| 4 | MINOR, OUT-OF-ENVELOPE | `probe.py` `_tail_unreadable` | Required and delivered pts are sets; repeated pts are not counted | Accept; fix in the terminating cleanup (multiset compare, test with a duplicate pts) |

If finding 1 is not upheld, round 2 has ZERO new blocking findings and terminates the loop; findings 2-4 are then the terminating cleanup (non-blocking, fixed once, no further round). If CHARC upholds it, the fix is product code plus two tests and a round 3 follows. Reviewer B (the orchestrator's seat pass) follows the termination.

### Round 2 adjudication (orchestrator, depth at the round-2 yield 259,729, 126 turns) and terminating cleanup

Finding 1: NOT UPHELD as blocking; adjudicated IN-RULING. Ruling 2b and CHARC's IF-5 wording (main `4174484`) give "`mvhd` duration over its timescale, OR the longest stream in integer ticks times its time base". Evidence: on the four video samples `mvhd` duration over timescale equals the stream maximum exactly (hevc8, hevc10, untagged 360360/240000 = 3003/2000; vfr 320320/240000 = 1001/750). ADVISORY banked for WP3.10: on a source with a non-identity edit list the two forms may differ and the presentation form (`mvhd`) is what a player shows (report, consumer notes). No code change. The loop TERMINATES at round 2: zero new blocking findings; no round 3.

Cleanup (non-blocking, never opens a round):

| Finding | Change | Test (fails on the unfixed code) |
|---|---|---|
| 2 | doc sentence in `read_movie_boxes`: the walk ends at `moov` | none (documentation) |
| 3 | GPMF depth starts at 0; exactly `MAX_DEPTH` nested containers allowed | `test_nesting_is_allowed_to_exactly_the_cap_and_refused_beyond_it` |
| 4 | tail check compares pts as multisets | `test_a_repeated_pts_must_be_delivered_as_often_as_it_occurs` |

Both new tests fail with the unfixed `gopro.py` / `probe.py` (checked by stash). Own tests 142 passed; ruff, ruff format --check, mypy strict clean.

### Cumulative round ledger

| Round | Critical / major / minor | In-env / out | NEW / REOPENED | Reverts | Fix type | Transport / CLI | Depth |
|---|---|---|---|---|---|---|---|
| 0 | -- | -- | -- | -- | -- | -- | 90,520 |
| 1 | 0 / 4 / 2 | 6 / 0 | 6 / 0 | 0 | product (4 major + 2 minor) + tests | WSL, codex-cli 0.162.1, gpt-5.6-sol high | 215,371 |
| 2 | 0 / 1 (not upheld) / 3 | 2 / 2 (findings 3, 4) | 4 / 0 | 0 | product (3 minor) + tests, post-termination cleanup | same | 259,729 |
