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
| 6 | Reviewer A (seat 5) on `fa5d939`, base `dabb204` (SCOPED to the round-5 remediation of the instrument) | 0 | 2 | 1 | all in envelope; MAJOR #1, #2 ACCEPTED (blocking, both reproduced); MINOR #3 ACCEPTED (cleanup) | 3 NEW, 0 REOPENED (#2 introduced by the round-5 #9 fix `7059dda`) | 0 | pending: seat 6 remediates (instrument code) | WSL, codex-cli 0.162.1 gpt-5.6-sol high; probe 1 + review 19 `succeeded in`; 104,892 tokens; 8 `ERROR` matches = 4 echoed source, 4 reviewer tool-call parse errors (codex_core router), 1 WSL vsock; none transport | 286,315 at the round-6 yield (seat 5) |

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

## RESUME HERE (current; for seat 6 -- seat 5 retires after round 6)

- Base `ac4be92` (main with WP3.9; the dispatcher rebased the branch at seat 4; pre-rebase branch
  `wp3.10-pre-rebase` at `98ee54a`). Reviewer A evidence `r1\`..`r6\` under
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\`.
- **Reviewer A on the product CONVERGED at round 4** (both MAJOR->MINOR adjudications upheld;
  cleanup `4dfa96e`). **The floor-row instrument** `tools/video_io_bench.py` (built `dabb204`) is
  under rounds 5-6: round 5 = the five-round gate, CONTINUE APPROVED by the dispatcher (R5 #2 new,
  in envelope, blocking, and it changes the instrument's result-bearing contamination record);
  R5 downgrades #1 and #3 UPHELD; R5 #10 BANKED out of envelope (several GPUs: the index/uuid
  mitigation is NOTED in the report and here, no code). Round-5 remediation `deb1765`..`fa5d939`
  (one commit per finding, tests fail on the code before each: `r6\remediation\`).
- **Round 6 (`dabb204..fa5d939`): 2 NEW blocking, in envelope, both reproduced** (`r6\repro\`):
  R6 #1 `Telemetry.stop` keeps a queued periodic window and drops the final window sent after it;
  R6 #2 the parent keeps the watcher's pipe end (`_their_end`, introduced by `7059dda`), so a
  watcher dying mid-run is never seen, `stop` waits the whole `_WATCHER_WAIT_S` and records
  nothing. R6 #3 MINOR: the module docstring says the first interval holds the FFmpeg start-up
  "on both sides"; the encoder process starts inside `sink.open`.
- **LF RULE (dispatcher, binding):** LF in every committed blob. Before every commit: every file
  in `git diff --name-only main..HEAD` has 0 CR bytes in its HEAD blob
  (`git show HEAD:<f> | tr -cd '\r' | wc -c`). Write files with LF only; commit with
  `git -C <worktree> -c core.autocrlf=false commit ... -- <paths>`. Seat 5 used a helper
  (scratchpad `commit.sh`: CR check on the working files, add, commit by pathspec with the
  footer, then the main..HEAD blob check); rebuild it or check by hand.
- **Full pytest:** NOT yet run on this branch (seat 4's window was cancelled; the dispatcher
  told seat 5 not to start it). It needs a WINDOW.
- **Seat 6's ladder, in order:**
  1. Remediate R6 #1 (the watcher tags its final window; `stop` receives until it has the final
     one or the wait ends, and records the latter as an error), R6 #2 (the parent closes its copy
     of the watcher's end once the watcher has started; an EOF in `_receive` records "the strays
     watcher ended" with its time and drops the connection without ending the memory and GPU
     sampling; `stop` records a watcher that is no longer alive and does not wait on it), R6 #3
     (docstring: the first interval holds the decoder's start and the encoder's first frame; the
     encoder process starts in `open`). One commit per finding, each with a test that fails on
     `fa5d939` (the round-6 repro scripts are ready-made shapes: a scripted pipe for #1; kill the
     watcher pid for #2, with `_WATCHER_WAIT_S` patched short). Then Reviewer A ROUND 7 scoped to
     `fa5d939..HEAD` (copy `r6\run_review.sh` and `r6\mkprompt.py`; build from `r6\review-prompt.md`:
     round, base, HEAD, the round-6 findings section). YIELD at its verdict, no change in that turn.
  2. WINDOW REQUEST: full pytest (background, `QT_QPA_PLATFORM=offscreen`,
     `--basetemp=work/<name>`, output to a file, >= 5 GB free first, grep the summary;
     `WINDOW RELEASED: <summary>`).
  3. FOOTAGE window: the GX011627 product leg through WP3.9's `frames` and this sink (NVENC 8-bit
     Standard; the instrument's summary all MANDATORY and REQUIRED SAME; the `footage`-marked
     test); the AD-12 quality table (GX011627 busy + one calm Snorkel clip, each level per encoder
     at 8 bits and NVENC High at 10 bits; output bit rate against the camera's; PSNR to the source
     as a sanity figure; targets High ~ camera, Standard ~ 1/2, Draft ~ 1/4; a miss is a proposal
     to CHARC, no code change); the Edits compilation through `open` (the round-2 #2 rule must
     accept its 3003/60000 reorder delay). No `gpmd`, IMU or GPS value read; no footage-derived
     output committed.
  4. EXCLUSIVE window, LAST and alone: `uv run python tools/video_io_bench.py floor --dry-run`
     first, then `... floor` (options go AFTER the subcommand); the record lands under
     `work\wp3.10\bench\`. `WINDOW RELEASED: <summary>` after. For CHARC's note at WP3.4's accept:
     WP3.4's c3 core takes 0.4392 s/frame of D106's 0.834 s/frame at 4K, leaving about 0.39
     s/frame for decode, transport and encode; the floor row says whether that holds -- state the
     comparison in the report's speed section.
  5. The report's PENDING sections (section 7 "AD-12 quality table and the speed row", the
     GX011627 row of the V4 table, the `QUALITY_RATIO` figures for question 13; the instrument's
     limits below; R5 #10's mitigation note), DRAFT removed; then the return report (brief
     "Return report", under about 70 lines, by message).
- Decided and not to be redone: round 0 (NUT + end sentinel + setts/noise BSF, INFO packet), the
  round-0 rulings, CHARC's Q-A/Q-B/Q-C/Q-D notes, P8, the S1/#2/#3 ruling, round 3's #2/#3
  rejections, round 4's two downgrades, round 5's gate ruling and its downgrades and bank.
- Return-report items already known: DR-18 (1) closes only on `tied` (an NVENC run with a
  resolved GPU UUID in the footage or speed window; the bench records `nvenc_proof` per run);
  DR-15's iPhone leg stays OPEN; the banked WP3.7 item (`probe.py` `_run_ffprobe` inherits
  `FFREPORT`); the accepted "rounded UP" limitation; the #2 refusal is not applied when the sample
  table cannot be read; R5 #10 banked (several GPUs). Instrument limits: RSS sampled (0.25 s);
  graphics memory device-wide (`memory.used`; per-process reads 0/N/A under WDDM); the instrument
  loads the machine a little (`nvidia-smi` each second, `pmon` each 0.5 s on NVENC, about 2.5 s of
  CPU per strays window in the watcher); no CPU temperature on Windows; a process that starts and
  exits inside one strays window is not seen.
- Working notes: the bench module (`tests/test_io_video_encode_bench.py`, 45 tests) takes about
  2.5 min; the five video modules about 4-5 min; targeted runs use `-m "not footage"` and `-k`.
  Use a fresh `--basetemp=work/wp3.10/rN/<name>` per run (re-using one failed once with WinError
  3). Pre-fix runs: `git archive <sha> | tar -x -C work\wp3.10\rN\old-<sha>`, copy the new test
  file and `clearwater.local.toml` in, run from that folder (subshell) with
  `PYTHONPATH=<old>\src` and the worktree's `.venv\Scripts\python.exe -m pytest`. A venv's
  `python.exe` on Windows is a launcher whose child is the interpreter (the tests' `_tree`). The
  per-process CPU walk must never run in a thread of the measured process (it holds the
  interpreter lock: a 0.26 s probe took 23 s). Use `( cd <worktree> && ... )` subshells, never a
  bare `cd`. Python heredocs with a quoted delimiter work for edits; avoid `\U` inside a bash -c
  string.

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
