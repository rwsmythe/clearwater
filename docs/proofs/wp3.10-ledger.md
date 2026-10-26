# WP3.10 -- cumulative round ledger

Cell: `implementer-opus-high` (seat 1, `wp310-cell1`), worktree `.worktrees/wp3.10`, branch `wp3.10`
from main `de206e2`. Brief: `docs/briefs/wp3.10-brief.md` (FINAL, CHARC rulings `53d1d906e47fe2c9`).
Evidence root: `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\` (`r0\` = this round 0; see
`r0\md5sums.txt`). `work/` is gitignored and is NOT a record.

## Ledger

| Round | Kind | Critical | Major | Minor | In / out of envelope | NEW / REOPENED | Reverts | Product vs test-only fixes | Transport, CLI | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | design table + pts-carrier spike (no review, no product code) | -- | -- | -- | -- | -- | 0 | none (no product code) | -- | 219,455 at the round-0 yield |
| 1 | Reviewer A (seat 2) on `fd6e52d` | 0 | 11 | 2 | MAJOR: 9 in, 2 out (reviewer-tagged); MINOR: 2 in | 13 NEW, 0 REOPENED | 0 | PRODUCT and instrument (seat 3: `9785956`, `7035be6`, report `8fe963f`) | WSL, codex-cli gpt-5.6-sol high; 12 `succeeded in`; 171,804 tokens | (dispatcher) |
| 2 | Reviewer A (seat 3) on `8fe963f` | 0 | 2 + 1 self-found | 1 | reviewer MAJOR: 1 in (REJECTED with reproduction), 1 out (reviewer-tagged); MINOR: 1 out; self-found MAJOR S1: in | reviewer 2 NEW, 1 REOPENED (r1 #10); S1 NEW | 0 | PRODUCT and instrument (seat 4: S1 `3f73633`, #2 `155b691`, #3 `21059b8`) | WSL, codex-cli gpt-5.6-sol high; 20 `succeeded in`; 217,008 tokens; 1 echoed `ERROR` (sandbox subprocess, not transport) | 361K at the pause (seat 3 retired) |
| 3 | Reviewer A (seat 4) on `21059b8`, base `ac4be92` | 0 | 3 | 1 | MAJOR: 1 in (#1 ACCEPTED), 2 out (reviewer-tagged; #2 REJECTED with reproduction, #3 REJECTED with reason); MINOR: 1 in (#4 ACCEPTED, cleanup) | 4 NEW, 0 REOPENED | 0 | PRODUCT (`2f9c240`: #1 sink cleanup; #4 report) | WSL, codex-cli 0.162.1 gpt-5.6-sol high; probe 1 + review 11 `succeeded in`; 185,272 tokens; 1 echoed `ERROR` (WSL vsock, not transport) | 211,777 at the round-3 yield |
| 4 | Reviewer A (seat 4) on `2f9c240`, base `ac4be92` | 0 | 2 (reviewer) -> 0 adjudicated | 2 -> 4 adjudicated | all in envelope; MAJOR #1, #2 ACCEPTED and adjudicated MINOR (reproduction + reason; dispatcher UPHELD both: ZERO new blocking, the loop TERMINATES); MINOR #3, #4 ACCEPTED (cleanup) | 4 NEW, 0 REOPENED | 0 | PRODUCT and instrument, as the terminating round's cleanup (`4dfa96e`) | WSL, codex-cli 0.162.1 gpt-5.6-sol high; 15 `succeeded in`; 190,700 tokens; 2 `ERROR` matches = echoed source code, not transport | 248,871 at the round-4 yield; 279,801 after the round-4 cleanup |
| 5 | Reviewer A (seat 5) on `dabb204`, base `be7fe51` (SCOPED to the floor-row instrument `tools/video_io_bench.py` + its tests) | 0 | 3 (reviewer) -> 1 adjudicated | 7 -> 9 adjudicated | MAJOR #2 in (ACCEPTED, blocking); MAJOR #1, #3 in, adjudicated MINOR (reproduction / reason); MINOR #4-#9 in (ACCEPTED, cleanup); MINOR #10 OUT (reviewer-tagged; BANKED) | 10 NEW, 0 REOPENED | 0 | INSTRUMENT code and tests (`deb1765`..`fa5d939`; #7 test-only); gate: CONTINUE APPROVED | WSL, codex-cli 0.162.1 gpt-5.6-sol high; probe 1 + review 29 `succeeded in`; 98,860 tokens; 6 `ERROR` matches = echoed source code, not transport | 211,706 at the round-5 yield |
| 6 | Reviewer A (seat 5) on `fa5d939`, base `dabb204` (SCOPED to the round-5 remediation of the instrument) | 0 | 2 | 1 | all in envelope; MAJOR #1, #2 ACCEPTED (blocking, both reproduced); MINOR #3 ACCEPTED (cleanup) | 3 NEW, 0 REOPENED (#2 introduced by the round-5 #9 fix `7059dda`) | 0 | INSTRUMENT code and tests (seat 6: `609b9a3` #1, `02a0a92` #2, `5c1c949` #3 docstring) | WSL, codex-cli 0.162.1 gpt-5.6-sol high; probe 1 + review 19 `succeeded in`; 104,892 tokens; 8 `ERROR` matches = 4 echoed source, 4 reviewer tool-call parse errors (codex_core router), 1 WSL vsock; none transport | 286,315 at the round-6 yield (seat 5) |
| 7 | Reviewer A (seat 6) on `5c1c949`, base `fa5d939` (SCOPED to the round-6 remediation of the instrument) | 0 | 2 (reviewer) -> 0 adjudicated (#2 for the dispatcher: telemetry machinery, design guard) | 2 -> 4 adjudicated (#4 out) | MAJOR #1 in, adjudicated MINOR (reason); MAJOR #2 in, adjudicated MINOR (reproduction); MINOR #3 in (cleanup); MINOR #4 OUT (reviewer-tagged; BANKED again) | 3 NEW, 1 REOPENED (#4 = R5 #10) | 0 | INSTRUMENT code and tests (`98c805a` #1, `9e6a529` option B, `cb0f762` #2, `d4c08e8` docstring; #3 moot) | WSL, codex-cli 0.162.1 gpt-5.6-sol high; probe 1 + review 13 `succeeded in`; 98,804 tokens; 1 `ERROR` match = echoed source code, not transport | 116,371 at the round-7 yield (seat 6) |
| 8 | Reviewer A (seat 6) on `d4c08e8`, base `1087343` (SCOPED to the round-7 remediation and the option-B telemetry redesign) | 0 | 0 | 3 | all in envelope; MINOR #1-#3 ACCEPTED (cleanup); ZERO new blocking: the loop TERMINATES | 3 NEW, 0 REOPENED (#2 from `9e6a529`, #3 from `98c805a`) | 0 | INSTRUMENT code and tests, the terminating round's cleanup (`491ecb3` #3, `f262b75` #2, `db6f791` #1); no round 9 (ruling) | WSL, codex-cli 0.162.1 gpt-5.6-sol high; probe 1 + review 26 `succeeded in`; 107,893 tokens; 1 `ERROR` match = echoed source code, not transport | 204,725 at the round-8 yield (seat 6) |

Seat 1 stops after round 0 by the orchestrator's instruction (219K before product code; the build
is the largest in the wave). A fresh cell builds from "RESUME HERE" below.

## Round 0 -- the design table (as sent to the orchestrator)

### Q1 carrier (spike result)

Carrier = a stdlib NUT framer: main header (version 3, ONE time base = the source video time
base), one rawvideo stream (codec tag `G3\0\8` = `gbrp`, `G3\0\10` = `gbrp10le`), optional
stream INFO packet (`r_frame_rate`, see P7), then per frame a syncpoint plus a frame header with
the full coded pts and a header CRC (CRC-32, polynomial 0x04C11DB7, MSB-first, init 0, written
big-endian; verified against FFmpeg's own NUT bytes: `scripts/crccheck.py`, residue 0 on the
main, stream and info packets of an FFmpeg-written file).

- (a) PLAIN NUT FAILS (premise correction P1). NUT has no per-frame duration; lavf makes up
  `1/r_frame_rate` for the last frame. Reproduction: `uv run python work/wp3.10/spike/spike.py
  plain fx-vfr` -> `video stream duration` 1.301300 (13013/10000) vs the source's 1.334667
  (1001/750), and the video edit-list segment the same; every pts exact (`logs/r1.log`,
  `logs/r3.log`). CFR clips pass only because their last interval equals the made-up one.
- (b) THE FIX (FFmpeg-native, single pass, no repair): at `close`, one 1-byte SENTINEL packet at
  pts = end of the last written frame, and an input bitstream-filter chain on the pipe:
  `-bsf:v "setts=duration=if(eq(NEXT_PTS\,NOPTS)\,DURATION\,NEXT_PTS-PTS),noise=drop=lt(size\,2)"`
  -> every frame's duration = next pts - pts (the last included); the sentinel is dropped before
  the decoder. Transport check (`scripts/tx.py`, framemd5 of the decoded input): bytes identical,
  pts exact, durations = next pts - pts, last = sentinel - last pts, sentinel gone. Framing
  checked at 4K 10-bit (49.8 MB/frame) and 5.3K 8:7 10-bit (148 MB/frame) (`scripts/big.py`).
- Results with NUT + sentinel, libx265 AND hevc_nvenc (`logs/r2.log`, `compare/*.compare.json`):
  every timing MANDATORY item SAME -- full pts sequence, frame count, video stream duration, the
  four start-offset forms, edit-list presentation effect, audio packets byte-identical, audio
  sync, display matrix, `tmcd` regenerated identical -- on fx-vfr, fx-rotated (90 kept),
  fx-hevc10 (10-bit), fx-hevc8, fx-untagged, a synthetic 0.5 s empty edit, a VFR gap with
  offset, libx264 B-frames with offset / without offset / at 30000/1001, libx265 B-frames, a
  `tmcd` clip with offset, a drop-frame `tmcd` clip, and D76 8->10 on fx-hevc8 (both encoders).
- Expected non-timing DIFFERENTs (all handled in task 9): B-frame sources -> only "edit list as
  written" (`media_time` 1/15 vs 0) = AD-22; colour on the synthetic clips (they carry only matrix
  and range; the output gets the D54-assumed bt709 primaries/transfer); D76 rows (pix_fmt, bit
  depth follow the selected option).

### Premises that do not match (each reproduced)

- P1 Q1 as written (plain NUT) is not exact -> (a)+(b) above.
- P2 The sentinel needs the end of the last written frame; `ProbeResult` does not expose the
  per-frame pts table, so `open` re-reads it with ONE ffprobe packet listing (`packet=pts,flags`;
  no decode). Rule: end = the next source pts after the last written frame, else the source's
  presentation end (sum of the edit-list segment durations; with no edit list, video
  `start_pts + duration_ts`). On fx-truncated: 25 packets, the last flagged `C`, 24 frames decode,
  end = 24024 ticks (correct). (The spike used the edit-list sum for every clip; on fx-truncated
  that gives 45045, WRONG -- the product must use the next-pts rule.)
- P3 Edit-list forms. SAME as written: identity; empty + identity. By effect (AD-22):
  `media_time` = the reorder delay, with or without a leading empty edit. ABSENT edit list
  (`clips/noedit*.mp4`, `-use_editlist 0`): the output gains an identity list (empty + identity
  for a B-frame source) -> "as written" DIFFERENT; `-use_editlist 0` on the output is WORSE (video
  duration DIFFERENT; B-frame pts shifted to 0) (`logs/r4.log`, `logs/r5.log`). On noedit-bf pts,
  start offset and duration are SAME; compare.py's effect model reads an absent list as starting
  at the earliest composition time, so its effect row also differs. Multi-segment, rate != 1 and
  trims (first pts != the empty-edit dwell) -> refused at `open` by name. **Added seat 4 (CHARC
  ruling `26c54f1567f948e1`, round-2 #2):** a media segment whose `media_time` is not the track's
  earliest composition time (from the sample table, `stts` + `ctts`) -> refused at `open` by
  name ("an edit list whose media segment starts at X s rather than at the video's earliest
  frame (Y s)"); equal is AD-22's identity-by-effect form (the Edits compilation's 3003/60000).
- P4 Q9 (cut audio/gpmd at the video end): `-shortest` CUTS THE VIDEO (19 of 24 frames on
  fx-truncated, `logs/r7.log`) -> unusable; the end is unknown when FFmpeg starts.
- P5 `tools/container_spike/compare.py` cannot read a truncated source (`ProbeError: top-level
  box size out of range at byte 2747`, `logs/r6.log`) -> the product instrument compares against
  the readable part.
- P6 With `provenance=None`, `-map_metadata 1` inherits a source `comment` tag (for example a
  re-corrected Clearwater output); `-metadata comment=` clears it (tested, `out/noprov.mp4`).
  The provenance JSON travels in argv (Windows cap 32767 characters for the whole command line);
  a JSON round trip with quotes, a backslash, non-ASCII and a newline survived, and
  `creation_time` was kept (`scripts/prov.py`).
- P7 (found in the footage window, NEW after the table was sent) With 4K frames, FFmpeg's stream
  probing of the NUT pipe sees ~1 frame, cannot estimate a frame rate, and the MP4 muxer's
  timecode-track writer then fails: `fps 30000 is too large` / `Error writing trailer: Invalid
  argument` (`logs/r8-footage.log`; reproduced on a small clip with `-probesize 32` on the pipe,
  `logs/r10.log`). `-r` is refused with `-fps_mode passthrough` ("contradictory", `logs/r11.log`).
  FIX: a NUT stream INFO packet `r_frame_rate = <probe.video.frame_rate>` (nutdec reads it; it
  ignores values >= 1000 fps). With it every clip passes again under `-probesize 32`
  (`logs/r12.log`) and GX011627 passes (below). The product framer ALWAYS writes this packet.
- P8 (held, for the fresh cell) The framer writes sample aspect ratio 1:1; `VideoStreamInfo` has
  no SAR field. Square pixels hold for GoPro and iPhone; the instrument's REQUIRED "frame size
  and sample aspect ratio" row would catch a non-square source. Decide at build: refuse a
  non-square source at `open` (read SAR in the sink's own packet/stream ffprobe call) or carry it.
  **RULED by CHARC (relayed by the orchestrator, seat 2): REFUSED at `open`, by name, from the
  sink's own ffprobe call; a SAR that cannot be seen is treated as 1:1 (docstring); no IF field.**

### Design (stands as drafted; orchestrator ruling)

- Files: NEW `src/clearwater/io/video/nut.py` (the carrier), `encode.py` (`FFmpegVideoSink`,
  `VideoEncodeError(kind, message)`), `capability.py` (`detect_capabilities`, `resolve_encoder`),
  `verify.py`; `__init__.py` appended exports; `tests/test_io_video_encode*.py`;
  `tools/video_fidelity.py` + `tests/test_video_fidelity.py`; `tools/video_io_bench.py`;
  `tools/container_spike/spike.py` (DR-26 only, Q15); `docs/reports/wp3.10-video-encode.md`;
  this ledger; and, by STANDING GRANT, `tests/test_io_video_probe_rules.py::
  test_the_package_exists_and_has_the_expected_modules` -- add exactly this package's new module
  names to the expected set, nothing else in that file (WP3.9 adds `decode.py`, `pipes.py` the
  same way; the second to merge rebases). Name the grant in the report's owned-files list.
- Command (reason per option):
  `ffmpeg -nostdin -hide_banner -nostats -loglevel error -y` (`-y`: SafeWrite's temporary exists,
  empty; never a final name)
  `-copyts` (no shift to 0) `-noautorotate [-display_rotation <probe.video.rotation>]` (matrix
  kept, frames not turned; CCW sign verified on fx-rotated: 90 -> 90)
  `-bsf:v "<setts/noise chain above>" -f nut -i pipe:0`
  `[-to <readable video end>, truncated only, Q-B] -i <source>`
  `-map 0:v:0 -map 1:<each audio index> -map 1:<each data index except tmcd>` (the MP4 muxer
  cannot copy `tmcd`)
  `-vf "<encode_filter(stream, bit_depth=...)>,setparams=color_primaries=..:color_trc=..:colorspace=..:range=.."`
  (from `ffmpeg_color_names`; raw frames carry no tags)
  NVENC `-c:v hevc_nvenc -preset p5 -tune hq -rc vbr -b:v 0 -cq 18|23|28`; libx265
  `-c:v libx265 -preset medium -crf 18|23|28 -x265-params log-level=error` (AD-12)
  `-pix_fmt yuv420p | yuv420p10le` (`p010le` on NVENC 10-bit) `-profile:v main|main10`
  `-color_primaries/-color_trc/-colorspace/-color_range` (stream tags; D55, DR-17)
  `-tag:v hvc1 -fps_mode passthrough -enc_time_base:v demux -video_track_timescale <tb den>`
  `-c:a copy -c:d copy` (audio and gpmd untouched, never opened)
  `-map_metadata 1 -map_metadata:s:v:0 1:s:v:0` (creation time, handler, timecode tag)
  `-write_tmcd 1` (tmcd regenerated) `-metadata comment=<AD-13 JSON, ensure_ascii, allow_nan=False | empty>`
  `-movflags +negative_cts_offsets -f mp4 <out_path>`
- `write`: checks `time_base`, strictly increasing pts >= 0, shape `(h, w, 3)`, float32, device
  `"cpu"` (refused by name, Q14); `rgb_to_planes(np.ascontiguousarray(px), bit_depth=out)`; TWO
  pipe writes (NUT sync+frame header, then the payload; never concatenate the payload).
- Threads: the caller's thread writes stdin; one daemon thread drains stderr into a bounded tail
  (no stdin/stderr deadlock); stdout DEVNULL. `proc.poll()` before every write and inside every
  wait; a dead encoder makes the pipe write fail at once -> `VideoEncodeError` with an
  ASCII-safe stderr tail (DR-28 (4)).
- Failure inside `write`/`close`: kill FFmpeg, delete `out_path`, raise the ORIGINAL error; a
  cleanup failure is attached as a note, never replacing it (DR-20 (6)). `abort` is idempotent,
  never raises, deletes only `out_path`.
- `close`: sentinel, close stdin, polled wait, return-code check, then the Q6 verification: an
  ffprobe packet listing of the output (whole stream; NO open-ended `-read_intervals`, WP3.7's
  note) -> count = written, every pts = written, first pts, rotation, audio and gpmd packet counts;
  `boxes.read_movie_boxes(out)` for the video edit-list form (the output carries no GPMF atom).
  A mismatch raises.
- `SinkReport.warnings`: D54 assumed tags; truncation / unreadable tail. `not_carried`: camera
  `udta` atoms, the `firmware` tag, and any of creation time / gpmd / tmcd absent from the output.
- Capabilities: `ffmpeg -encoders` listing + 4 one-frame test encodes to the null muxer (measured
  0.37 / 0.33 / 0.20 / 0.21 s: NVENC 8, NVENC 10, x265 8, x265 10), cached per process; reasons
  from the listing, the failed test, or NVENC's "no capable device" stderr. `resolve_encoder` per
  Q4 (the ONE "auto" rule; WP3.20 and WP3.14 call it).
- `io.video` imports `clearwater.color` and `clearwater.config.keys` only (checked: nothing from
  gui / jobs / methods / core / analysis, nor PySide6, cupy).

## Round-0 rulings (orchestrator, FINAL)

- Q-A YES: NUT + the end sentinel + the setts/noise input BSF is THE carrier (exact, single pass);
  plain NUT's failure on fx-vfr is the reproduced premise correction P1.
- Q-B as stated: truncated -> `-to <readable video end>` on input 1 from the packet table (the last
  packet without the corrupt flag; end = the next pts); unreadable_tail -> audio/gpmd whole plus a
  warning.
- Q-C as recommended: an absent edit list is accepted by presentation effect; the product
  instrument models "absent" as identity from media time 0. Orchestrator informs CHARC, who may
  overrule.
- Q-D YES: refuse provenance JSON over 16 KiB at `open`.
- Q-E as recommended: instrument colour rows compare against the probe's D54-resolved description
  (raw source tag recorded beside it); D76 rows compare against the selected depth.
- Q-F YES: the GX011627 leg and Q7's Edits read in a window, test-side FFmpeg decode.
- P2-P6 accepted as described (P6's `-metadata comment=` clear included). Command and design stand.
- P7 and P8 were found after the rulings (footage window); P7's fix is inside the ruled carrier
  (an extra header packet), P8 is HELD for the fresh cell.

## Footage window (granted; not a timing run)

- GX011627 (4K, 681 frames, `yuvj420p`, tb 1/30000, tracks v/a/tmcd/gpmd) streamed through a
  test-side FFmpeg decode (`decode_filter`, gbrp) -> NUT (with the INFO packet) -> hevc_nvenc
  8-bit Standard (cq 23) -> `compare.compare_files`: **41 items; DIFFERENT by class MANDATORY 0,
  REQUIRED 0, BEST-EFFORT 8; MANDATORY+REQUIRED all SAME** -- the same eight best-effort rows as
  WP1.5 section 6 (timecode tag on audio, camera `udta` atoms, ftyp brands, container tags, stream
  tags, track layout, sample-entry boxes, non-video edit lists as written). gpmd track SAME
  (23 packets; digests redacted in the evidence copy), creation time SAME. Elapsed 49 s wall
  (informal, NOT a timing figure). Evidence: `logs/r13-footage.log`,
  `compare/GX011627-hevc_nvenc-8-sentinel.compare.redacted.json`. The first attempt without the
  INFO packet failed (P7, `logs/r8-footage.log`).
- Edits/compilation-20261010-1080p60.mp4 (box-only read, `logs/r14-edits.log`): movie timescale
  1000; video `avc1`, media timescale 60000, ONE edit (segment 179930, `media_time` 3003 = 0.05 s,
  rate 1), earliest composition time 3003 -> the AD-22 reorder-delay form: usable for Q7's
  presentation-effect proof. Audio: identity edit at 0.
- WINDOW RELEASED at the end of this round.

## RESUME HERE (current; for seat 7 -- written by seat 6 after the round-8 cleanup)

- Base `ac4be92` (main with WP3.9; the dispatcher rebased the branch at seat 4; pre-rebase branch
  `wp3.10-pre-rebase` at `98ee54a`). Reviewer A evidence `r1\`..`r8\` under
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\`. Head at handover: the commit carrying
  this section (the cleanup head is `db6f791`).
- **Reviewer A is CLOSED, rounds 1-8.** The product converged at round 4 (cleanup `4dfa96e`). The
  floor-row instrument `tools/video_io_bench.py` (built `dabb204`) went through rounds 5-8: round
  5 the five-round gate (CONTINUE APPROVED); rounds 6-7 blocking findings in the watcher process,
  hence the dispatcher's DESIGN GUARD ruling OPTION B after round 7 (the watcher, its pipe and
  all IPC removed; strays read synchronously between frames; the RSS/GPU telemetry kept, one
  thread per sampler); round 8 NO_NEW_CRITICAL_MAJOR, the loop TERMINATED. Its three MINORs were
  cleaned up (`491ecb3` #3, `f262b75` #2, `db6f791` #1; pre-fix runs `r8\cleanup\`). NO round 9:
  cleanup after a terminating round opens no round (dispatcher ruling, as at round 4). The next
  Reviewer A round would be 9 and the next five-round gate 10, should a change reopen the loop.
- **Validation at `db6f791`:** the five video modules (`test_io_video_encode.py`, `_bench`,
  `_units`, `test_io_video_probe_rules.py`, `test_video_fidelity.py`) `-m "not footage"`: 250
  passed, 2 deselected, 6 min 35 s (`r8\cleanup\five-video-modules-at-db6f791.log`); `uv run
  ruff check .`, `ruff format --check .`, `mypy` clean. The bench module now has 50 tests.
- **LF RULE (dispatcher, binding):** LF in every committed blob. Before every commit: every file
  in `git diff --name-only main..HEAD` has 0 CR bytes in its HEAD blob
  (`git show HEAD:<f> | tr -cd '\r' | wc -c`). Write files with LF only; commit with
  `git -C <worktree> -c core.autocrlf=false commit ... -- <paths>`. Seats 5 and 6 used a scratch
  helper `commit.sh` (CR check on the working files, add, commit by pathspec with the footer
  from a message file, then the main..HEAD blob check); rebuild it or check by hand.
- **Seat 7's ladder, in order** (each window from the dispatcher; ask by ending the turn with
  `WINDOW REQUEST: <...>`; send `WINDOW RELEASED: <summary>` after; a run that dies without a
  summary is reported, not restarted):
  1. FULL PYTEST (never yet run on this branch): check >= 5 GB free first; run in the
     background with `QT_QPA_PLATFORM=offscreen`, `--basetemp=work/<name>`, output to a file;
     grep the summary.
  2. FOOTAGE window: the GX011627 product leg through WP3.9's `frames` and this sink (NVENC
     8-bit Standard; the instrument's summary all MANDATORY and REQUIRED SAME; the
     `footage`-marked test); the AD-12 quality table (GX011627 busy + one calm Snorkel clip,
     each level per encoder at 8 bits and NVENC High at 10 bits; output bit rate against the
     camera's; PSNR to the source as a sanity figure; targets High ~ camera, Standard ~ 1/2,
     Draft ~ 1/4; a miss is a proposal to CHARC, no code change); the Edits compilation through
     `open` (the round-2 #2 rule must accept its 3003/60000 reorder delay). No `gpmd`, IMU or
     GPS value read; no footage-derived output committed.
  3. EXCLUSIVE window, LAST and alone: `uv run python tools/video_io_bench.py floor --dry-run`
     first, then `... floor` (options AFTER the subcommand; defaults: `--memory-every 0.25`,
     `--gpu-every 1`, `--strays-every 300` frames); the record lands under
     `work\wp3.10\bench\`. For CHARC's note: WP3.4's c3 core takes 0.4392 s/frame of D106's
     0.834 s/frame at 4K, leaving about 0.39 s/frame for decode, transport and encode; state in
     the report's speed section whether the floor row fits inside that. Read from the raw
     `per_frame_s` how many frames after each strays pause run fast (the dispatcher asked for
     this; only the first is set apart) and report it.
  4. The report `docs/reports/wp3.10-video-encode.md`: its PENDING sections (section 7 "AD-12
     quality table and the speed row", the GX011627 row of the V4 table, the `QUALITY_RATIO`
     figures for question 13), the instrument's limits and the pause/strays semantics below,
     R5 #10's mitigation note; DRAFT and PENDING removed. Its status line still says seat 4.
  5. The return report to the dispatcher by message (brief "Return report", under about 70
     lines): branch head, files, claims with evidence paths, test counts, Reviewer A rounds 1-8
     and verdicts, the footage and speed figures, limits, debt dispositions, the items below,
     anything for Reviewer B.
- **The strays and pause semantics (option B, as built; state them in the report):** the
  `StrayWatch` is primed before the run (`strays.prime_s`), read after every `--strays-every`
  frames and once more right after `close` (first thing in the `finally`, also on a failure).
  A strays window covers the frames between two readings; the first window also holds the
  run's setup before the probe; the last holds the rest of the stream and `close`. Each in-loop
  reading pauses the loop for seconds: the pause (`strays.pauses_s`, `stages_s.strays_pauses`)
  is kept out of every interval, stage and rate; the frame right after each pause is set apart
  (`after_pause_frames`, `after_pause`), as the first frame is. During a pause the decoder
  fills its output pipe AND FFmpeg's own frame buffers (not the pipe alone: the dispatcher's
  "bounded by the pipe depth" was corrected and accepted at round 8) and the encoder works
  through what it holds, so a few frames after a pause may run fast. The telemetry: one thread
  for RSS and one for the GPU, each on its own schedule (no catch-up burst), every sample timed
  (`rss` pairs, `gpu[].t_s`), `gaps_s` beside the nominal `periods_s`; `stop` records a sampler
  that ended early or did not stop within `_SAMPLER_JOIN_S` (30 s). The NVENC proof's sampler
  starts first, the telemetry right before the probe; `offsets_s` places the telemetry's zero
  and the end of the strays priming on the run's clock (negative = before the probe). The
  frame is released after its write is timed, before the next `next` (its release falls in the
  next interval's bookkeeping).
- Decided and not to be redone: round 0 (NUT + end sentinel + setts/noise BSF, INFO packet), the
  round-0 rulings, CHARC's Q-A/Q-B/Q-C/Q-D notes, P8, the S1/#2/#3 ruling, round 3's #2/#3
  rejections, round 4's two downgrades, round 5's gate ruling, downgrades and bank, round 7's
  downgrades and the option-B ruling, round 8's termination and its no-round-9 ruling.
- Return-report items already known: DR-18 (1) closes only on `tied` (an NVENC run with a
  resolved GPU UUID in the footage or speed window; the bench records `nvenc_proof` per run);
  DR-15's iPhone leg stays OPEN; the banked WP3.7 item (`probe.py` `_run_ffprobe` inherits
  `FFREPORT`); the accepted "rounded UP" limitation; the #2 refusal is not applied when the sample
  table cannot be read; R5 #10 banked (several GPUs; reopened as R7 #4 and banked again; the
  index/uuid mitigation is a note in the report); the option-B redesign and its cost; the
  pause/strays semantics above.
- Instrument limits: RSS sampled (0.25 s nominal; the actual gaps in `gaps_s`); graphics memory
  device-wide (`memory.used`; per-process reads 0/N/A under WDDM); the instrument loads the
  machine a little (`nvidia-smi` each second in its own thread, `pmon` each 0.5 s on NVENC, a
  strays reading of seconds of CPU every 300 frames with the loop paused and the pause kept out
  of the figures); no CPU temperature on Windows; a process that starts and exits between two
  strays readings is not seen; only the first frame after a pause is set apart.
- Working notes: the bench module (50 tests) takes about 2.5 min; the five video modules about
  6.5 min; targeted runs use `-m "not footage"` and `-k`. Use a fresh `--basetemp=work/wp3.10/<x>`
  per run, creating its parent folder first (a missing parent gave WinError 3). Pre-fix runs:
  `git archive <sha> | tar -x -C work\wp3.10\<x>\old-<sha>`, copy the new test file and
  `clearwater.local.toml` in, run from that folder (subshell) with `PYTHONPATH=<old>\src` and the
  worktree's `.venv\Scripts\python.exe -m pytest`; a script outside pytest needs
  `PYTHONPATH` in Windows form (`C:\...\tools;C:\...\src`). A venv's `python.exe` on Windows is a
  launcher whose child is the interpreter. The per-process CPU walk must never run in a thread
  of the measured process (it holds the interpreter lock: a 0.26 s probe took 23 s). Use
  `( cd <worktree> && ... )` subshells, never a bare `cd`. Write ledger edits as a Python script
  file with raw strings (an inline heredoc with `\U` in a non-raw string failed once).

## Seat 2 (`wp310-cell2`) -- build and round 1

- Built from RESUME HERE: `nut.py` (the round-0 framer carried, INFO packet always), `capability.py`,
  `encode.py`, `verify.py`, `__init__.py` exports, the rules-test module set, `tools/video_fidelity.py`,
  DR-26 in `tools/container_spike/spike.py`, three test modules, the report DRAFT. **P8 decided:
  a non-square sample aspect ratio is REFUSED at `open`, by name, from the sink's own ffprobe
  listing.** Q-C as upheld by CHARC: a NOTE in the instrument, listed in `summary.notes`.
- Disclosure: the round-1 pre-review test run (`r1/test-summary.txt`) included the `footage`-marked
  GX011627 test (a 4K NVENC encode through the test-side decode) outside a granted window; it
  passed. Later targeted runs deselect `footage`.

### Round 1 (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r1\`, `adjudication.md` there)

Accepted: 1 (product lists telemetry packets), 2 (location tags in the instrument record), 3 (no
`mvhd` row), 4 (cut-short edit reading too coarse), 6 (truncated audio count), 7 (NVENC window
clocks), 8 (negative pts raw `ValueError`), 9 (`FFREPORT` inherited) -- in-envelope MAJOR; 11
(header built after FFmpeg starts; out of envelope, non-blocking), 12, 13 (MINOR). Rejected with
reproduction: 5 (a wrong `media_time` fails `close` through the pts check, F5), 10 (a head trim is
refused at `open`, F10; out of envelope). Remediation follows the dispatcher's reply.

## Seat 3 (fresh seat) -- round-1 remediation and round 2

- Branch found at `01d1578` (seat 2's P8 commit, one minute after `eae4380`; consistent with the
  P8 ruling). Remediated round-1 findings 1-4, 6-9, 11-13 and the finding-5 report text, as the
  dispatcher confirmed: instrument `9785956` (2 location values withheld before any comparison,
  presence only; 3 the MANDATORY `mvhd` row, exact, readable-part aware; 4 the cut-short reading
  keeps media_time, rate and the audio effect; 7 one monotonic clock, a sample counts when its
  call overlaps the window), sink `7035be6` (1 three listings, video and audio only, data tracks
  from the stream list's sample count; 6 every audio pts checked, a cut stream exactly the
  source's packets before the cut with 2 us slack; 8 negative pts refused at open; 9 `tool_env()`
  strips `FFREPORT` from every sink and detection process; 11 header built before FFmpeg starts;
  12 strict read-back; 13 `out_path` recorded first), report `8fe963f`. Every new test fails on
  the pre-remediation code (18 failed, run on `git archive eae4380` with the new tests), and the
  F3/F4 plants read SAME by the old instrument and DIFFERENT by the new
  (`work/wp3.10/r2/oldnew.py`).
- Targeted runs at `8fe963f` (`-m "not footage"`): `test_io_video_encode.py` 92 passed; units,
  fidelity and probe modules 214 passed; ruff, format and mypy clean. Full suite not run (window).
- Banked (not this package's file): WP3.7's `probe.py` `_run_ffprobe` (`cc28699`) inherits
  `FFREPORT`.

### Round 2 (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r2\`, `adjudication.md` there)

Rejected with reproduction: 1 (ffprobe exits 0 on moov-first cut files at three cut points and
the instrument gathers them, `repro/repro_f1.*`). Non-blocking by rule: 2 (REOPENED r1 #10,
reviewer-tagged out of envelope; reproduced for a keyframe-aligned head trim, which `open`
accepts and the instrument flags DIFFERENT, `repro/repro_f2.*`; BANKED, a cheap exact refusal
proposed with S1), 3 MINOR (cleanup: `tied` needs a resolved GPU UUID). SELF-FOUND S1 (MAJOR,
in-envelope, NEW): a truncated source whose cut leaves no corrupt-flagged packet gets its last
frame extended to the whole file's presentation end (`repro/repro_f1b.*`, cut at 60 %: the
output's video edit list says 2.0 s over 1.1 s of media; caught by the instrument's
video-duration row, not by `close`). Remediation follows the dispatcher's reply.

## Seat 4 (fresh seat after the pause) -- round-2 remediation and round 3

- Started from CHARC `26c54f1567f948e1` (FINAL) on the rebased branch (`43b68ff` on `ac4be92`).
  One commit per finding, each with tests that fail on the unfixed code (run on `git archive` of
  the pre-fix head with the new tests; logs in `r3\remediation\`):
  - **S1** `3f73633`: `verify.read_sample_table` (the video track's `mdhd` + `stts` + signed
    `ctts` from `moov`, bounds-checked, at most `MAX_SAMPLES`), `_sample_pts` (composition times
    moved by the one offset the first listed packet shows, checked against EVERY listed packet,
    else absent), `PacketTable.samples` / `.sample_pts`; `frame_end` takes the next pts from the
    sample table when known; `readable_end` (refuses when the end cannot be told) is used by BOTH
    `encode._plan_tracks` and `tools/video_fidelity._readable_end`. `probe.py` untouched; no
    interface changed. Tests: the moov-first libx264 clip cut at 60 % (no corrupt packet; oracle
    = the next pts in the WHOLE file; output edit end, audio, V4) -- pre-fix: edit end 2 s where
    11/10 s (`s1-prefix-fails.log`); the sample table agrees with the listing on libx264/libx265
    B-frame and plain clips; unit tests of `readable_end` and the mapping.
  - **#2** `155b691`: `_edit_list_refusal` refuses a media segment whose `media_time` is not the
    track's earliest composition time (recorded in the round-0 table above). Tests: the
    keyframe-aligned head trim of `r2\repro\repro_f2.py` refused by name before FFmpeg starts
    (pre-fix: FFmpeg started); four unit forms (`f2-prefix-fails.log`).
  - **#3** `21059b8`: `nvenc_proof` is `tied` only with a resolved GPU UUID, else the reason names
    the index (`f3-prefix-fails.log`).
- Checked on every WP2.3 video fixture and the r2 cut files: the sample table maps (scratch
  `work\wp3.10\r3s1*.py`). Targeted run before review at `21059b8`: the five video modules
  `-m "not footage"` 213 passed, 2 deselected; ruff, format, mypy clean.

### Round 3 (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r3\`, `adjudication.md` there)

ACCEPTED: 1 (MAJOR, in envelope: `abort` / `_fail` skip deleting `out_path` when a process step of
the cleanup raises; reproduced with a planted `wait` timeout, `repro/repro_f1.*`), 4 (MINOR: stale
report status lines). REJECTED: 2 (reviewer-tagged out of envelope; an edit list ending inside the
last frame is the source's own presentation and the output keeps it, every MANDATORY and REQUIRED
item SAME, `repro/repro_f2.*`; the same script on a fractional-tick end shows the accepted
"rounded UP" limitation as a reported 1-tick DIFFERENT), 3 (reviewer-tagged out of envelope;
FFmpeg reads `stts`/`ctts` regardless of version exactly as the reader does, and the mapping is
checked against every listed packet). Remediation follows the dispatcher's reply.

- Round-3 remediation `2f9c240` (dispatcher: R3 adjudication accepted as written): #1 `_cleanup`
  deletes `out_path` in a `finally`; `abort` repeats the cleanup after a failure or an unfinished
  abort, does nothing after `close`; #4 report status lines. Three tests fail on `21059b8`
  (`r4\repro\r3f1-prefix-fails.log`). Five video modules at `2f9c240`: 216 passed.

### Round 4 (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r4\`, `adjudication.md` there)

ACCEPTED, all in envelope, all NEW: 1 (reviewer MAJOR, adjudicated MINOR: a failing stderr-thread
start leaves FFmpeg running and `out_path` with a raw exception; reproduced; the caller's `abort`
recovers both, reproduced; trigger = thread-start failure), 2 (reviewer MAJOR, adjudicated MINOR:
the NVENC window includes 0.44 s of output verification on a 1.06 s window; a false `tied` needs
PID reuse with NVENC load in that tail), 3 (MINOR: a refused `open` leaves the sink reopenable),
4 (MINOR: a stale test comment). Remediation follows the dispatcher's ruling on the downgrades.
Seat-4 slip disclosed: several early tool calls used `cd <worktree> && ...` in the tool's shell
(agent shells reset between calls; switched to subshells).

- Round-4 ruling (dispatcher, FINAL): both downgrades upheld; the loop terminates at round 4.
  Cleanup `4dfa96e`: #1 the stderr-thread start inside the failure path (`encoder_failed`); #2 the
  instrument's encode window ends at FFmpeg's exit (`_RecordingSink._end_stream`), stated in the
  report; #3 a refused `open` is final; #4 the stale comment. Three tests fail on `9e271c0`. The
  same commit restores the CRLF endings that two `sed -i` edits in `2f9c240` dropped (test module,
  report); the ledger's (dropped by `9e271c0`) are restored with this entry.
- LF correction (dispatcher): the CRLF "restoration" in `4dfa96e` / `141cde5` was itself the
  defect; `14e0425` stores all seven package files with LF (endings-only: an `--ignore-cr-at-eol`
  diff of the commit is empty). Every file in `main..HEAD` has 0 CR bytes in its HEAD blob.

## Seat 5 (fresh seat) -- the floor-row instrument and round 5

- Dispatch (orchestrator gen 10): ladder (1) tool + tests, static gates; (2) Reviewer A round 5
  scoped to the tool's diff (five-round gate); (3) full pytest in a window; (4) footage legs in a
  window; (5) EXCLUSIVE floor row, last and alone; (6) report and return report.
- Built `dabb204`: `tools/video_io_bench.py` (`run CLIP`, `floor` = `FLOOR_PLAN`, ruling Q11's
  set; WP3.9's `frames` straight into the sink; stage, per-frame, s/frame and min/min figures;
  process-tree RSS with FFmpeg children, device-wide graphics memory, clocks and temperatures;
  strays from a watcher PROCESS; the DR-18 (1) proof through the fidelity instrument's sampler)
  and `tests/test_io_video_encode_bench.py` (inside the brief's `tests/test_io_video_encode*.py`
  ownership; 21 passed, the gpu test included). Static gates clean. Found while building
  (scratch `work\wp3.10\r5\`): the per-process CPU walk in a THREAD holds the interpreter lock in
  long stretches (a 0.26 s probe took 23 s beside it), hence the separate watcher process; a
  venv's `python.exe` on Windows can be a launcher whose child is the interpreter (test helper).
- Seat-5 slip disclosed: one early tool call used `cd <worktree> && ...` (agent shells reset
  between calls; subshells used from then on).

### Round 5 (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r5\`, `adjudication.md` there)

ACCEPTED, blocking: 2 (MAJOR: the strays watch misses a process for its first window, and one that
lives under a window entirely; reproduced, `repro/repro_f2.log`). Adjudicated MINOR: 1 (the
unattributed part of a frame interval is the loop's bookkeeping, 1.51 us mean, reproduced
`repro/repro_f1.log`; raw wait/write lists to be kept), 3 (non-positive periods: reachable only by
explicit misuse; defaults used in the windows). ACCEPTED MINOR: 4-9 (conditions window text,
disk re-check per run, run options after the subcommand, NVENC test name, a failed-after-success
test, watcher start-failure cleanup). BANKED: 10 (several GPUs, out of envelope). NEW blocking
in envelope = 1, so the loop does not terminate; FIVE_ROUND_GATE: yield for approval to continue.
No change made in the adjudicating turn.
- Round-5 ruling (dispatcher, FINAL; depth 211,706 at the round-5 yield): CONTINUE APPROVED at
  the five-round gate; #1 and #3 downgrades upheld; #4-#9 cleanup; #10 banked out of envelope,
  the index/uuid mitigation noted in the report and ledger, no code.
- Round-5 remediation, one commit per finding, tests fail on the code before each
  (`r6\remediation\`: the new tests on `dabb204` 25 failed; the period tests on `56083fc` 18
  failed, for #3 alone; the disk test on `8040556` failed, for #5 alone): `deb1765` #2 (a process
  new since the previous walk is charged its CPU since creation, marked `new`); `091f7e7` #1 (raw
  wait and write lists, the interval's content stated); `56083fc` #6 (options on a parent parser
  of `run` and `floor`); `c2e8655` #3 (periods: exit 2 / `ValueError`, recorded); `8040556` #4
  (the conditions strays window read first; the docstring names the watcher process); `118307c`
  #5 + #8 (the disk re-checked before every run; a failure after a successful run keeps it);
  `7059dda` #9 (a watcher that fails to start is killed, joined, its pipe closed); `fa5d939` #7
  (test-only rename). At `fa5d939`: the bench module 45 passed; ruff, format, mypy clean.

### Round 6 (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r6\`, `adjudication.md` there)

ACCEPTED, blocking, NEW, in envelope, both reproduced: 1 (`Telemetry.stop` keeps a queued periodic
window and drops the final one sent after it, `repro/repro_r6f1.log`; present since `dabb204`), 2
(the parent keeps the watcher's pipe end, so a watcher dying mid-run is unseen, `stop` waits the
whole wait, nothing recorded, `repro/repro_r6f2.log`; introduced by the round-5 #9 fix
`7059dda`). ACCEPTED MINOR: 3 (the first interval's docstring). The loop does not terminate;
seat 5 retires per the dispatcher's seat plan; the remediation is seat 6's (RESUME HERE).

## Seat 6 (fresh seat) -- round-6 remediation and round 7

- Seat 5's round-6 depth: 286,315 (dispatcher-read at its R6 yield). Head `f3df19d` clean at
  pickup. Seat-6 slips disclosed: the first tool call began with `cd <worktree> 2>/dev/null;`
  (a bare `cd`; the shells reset between calls; subshells used from then on); `b9dcb37` carries
  only the depth figure (its ledger edit script failed before the commit helper ran; this
  section and row 7 follow in the next commit).
- Round-6 remediation, one commit per finding (pre-fix runs: `r7\remediation\`): `609b9a3` #1
  (the watcher tags its last window `final`; `stop` receives until it or the wait ends, recording
  the latter; the new tests on `fa5d939`: 4 failed); `02a0a92` #2 (the parent closes its copy of
  the watcher's end once it is primed; an ended pipe is recorded with its time and dropped while
  the sampling goes on; `stop` records a watcher not alive, exit code, no wait; the new tests on
  `fa5d939`: 2 failed, one waited the patched 30 s); `5c1c949` #3 (docstring only, no test). At
  `5c1c949`: the bench module 50 passed (`-m "not footage"`, the gpu test ran); ruff, format,
  mypy clean.

### Round 7 (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r7\`, `adjudication.md` there)

Reviewer: 2 MAJOR, 2 MINOR; the three round-6 fixes verified present. #1 (the loop holds the
previous frame during `next`) adjudicated MINOR by reason (one RGB frame, 94.9 MiB at 4K, against
N4's 16 GB, on the safe side). #2 (the recorded periods are nominal; the GPU reading is bound to
the memory loop) adjudicated MINOR by reproduction (`repro/repro_r7f2.log`: RSS mean 0.375 s
against 0.25, GPU 1.16 s against 1.0 at the defaults) -- telemetry machinery, so the dispatcher
rules and the design guard's proposal goes with the yield. #3 (a watcher dying before "ready"
costs the 60 s start wait) MINOR cleanup. #4 = R5 #10 REOPENED, OUT, banked. All but #4 present
since `dabb204`. No change in the adjudicating turn.
- Round-7 ruling (dispatcher, FINAL; depth 116,371 at the round-7 yield): #1 and #2 MINOR
  UPHELD; #3 moot under option B; #4 banked. DESIGN GUARD: OPTION B, hybrid: the strays read
  synchronously between frames, the watcher process, its pipe and all IPC removed; the RSS/GPU
  thread kept with the #2 fix (every sample timed, actual gaps beside the nominal periods, the
  GPU reads on their own schedule, a sampler that ends early or does not stop in time recorded).
- Round-7 remediation (pre-fix runs: `r8\remediation\`): `98c805a` #1 (the frame released before
  the next `next`; the test on `1087343` failed); `9e6a529` option B (strays primed before the
  run, read after every `--strays-every` frames, now a frame count, default 300, and after
  `close`; pauses recorded and kept out of every figure; the frame after a pause recorded apart;
  the watcher tests removed; the new tests on `1087343`: 9 failed, and a probe there shows the
  telemetry starting a `python.exe` child); `cb0f762` #2 (one thread per sampler on its own
  schedule; RSS samples timed; `gaps_s`; the stop records a sampler that ended early or did not
  stop within `_SAMPLER_JOIN_S` = 30 s; the tests on `9e6a529`: 4 failed, the ended-early one
  shows the GPU readings stopping with the memory sampler); `d4c08e8` docstring (a pause lets the
  decoder fill its pipe AND FFmpeg's own frame buffers, not the pipe alone; the dispatcher's
  "bounded by the pipe depth" corrected; the raw lists show how far the effect reaches, to be read
  on the footage runs). At `cb0f762`: the bench module 48 passed; ruff, format, mypy clean.

### Round 8 (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r8\`, `adjudication.md` there)

NO_NEW_CRITICAL_MAJOR: 3 MINOR, all in envelope, ACCEPTED as cleanup: #1 the telemetry origin
and the strays priming precede `started` with no offset recorded; #2 the final strays reading
comes after the samplers stop, not right after `close`; #3 `written` is read after `del frame`.
The loop TERMINATES at round 8. No change in the adjudicating turn.
- Round-8 ruling (dispatcher, FINAL; depth 204,725 at the round-8 yield): the loop terminates;
  the three MINORs are cleanup; NO round 9 (cleanup after a terminating round opens no round,
  as at round 4); seat 6's correction (the decoder runs ahead into FFmpeg's own buffers as well
  as the pipe) ACCEPTED, with `per_frame_s` after a pause to be reported from the footage runs.
- Round-8 cleanup, one commit each, tests failing first (`r8\cleanup\`): `491ecb3` #3 (the write
  timed before the frame's release; the test on `7c7a870` failed: write median 0.166 s with a
  planted 0.15 s release); `f262b75` #2 (the last strays reading first in the `finally`; the test
  on `491ecb3` failed: last window at 3.11 s against close at 2.50 s with a 0.6 s slow stop);
  `db6f791` #1 (the NVENC sampler first, the telemetry right before the probe on a
  `perf_counter` origin, `offsets_s` recorded; the test on `f262b75` failed: no `offsets_s`). At
  `db6f791`: the five video modules 250 passed (`-m "not footage"`); ruff, format, mypy clean.
- Seat 6 hands over to seat 7 (the dispatcher rolls over to a fresh generation); RESUME HERE
  rewritten for seat 7.
