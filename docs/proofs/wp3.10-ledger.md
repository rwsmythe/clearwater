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
| 2 | Reviewer A (seat 3) on `8fe963f` | 0 | 2 + 1 self-found | 1 | reviewer MAJOR: 1 in (REJECTED with reproduction), 1 out (reviewer-tagged); MINOR: 1 out; self-found MAJOR S1: in | reviewer 2 NEW, 1 REOPENED (r1 #10); S1 NEW | 0 | pending (adjudication turn: no change) | WSL, codex-cli gpt-5.6-sol high; 20 `succeeded in`; 217,008 tokens; 1 echoed `ERROR` (sandbox subprocess, not transport) | (dispatcher) |

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

## RESUME HERE (current; seat 3 paused by the orchestrator at `b18d7cc` + this ledger commit)

- **Round 1: fully remediated.** All accepted findings (1-4, 6-9, 11-13) and the finding-5 report
  text are fixed and tested (`9785956` instrument, `7035be6` sink, `8fe963f` report); 5 and 10
  stay rejected with their reproductions. Nothing of round 1 remains.
- **Round 2 HAS RUN and is ADJUDICATED** (on `8fe963f`, before the pause reached this seat;
  evidence `r2\`, section "Round 2" below). Pending the dispatcher's ruling, NO remediation
  started:
  - **S1** (self-found MAJOR, in envelope, blocking): a truncated source cut at a packet
    boundary (no corrupt-flagged packet) has no "next pts" after its last readable frame;
    `verify.frame_end` falls back to the whole file's presentation end, so the last frame and the
    audio cut run to it. Proposed fix: the next pts from the source's own video sample table
    (`stts` + `ctts` in the intact `moov`, mapped through the edit list), used by the sink's
    `_plan_tracks`/`frame_end` and the instrument's `_readable_end`; a regression test on a
    moov-first file cut at 60 % (`r2\repro\repro_f1b.py`), failing on the current code.
  - **#2** (REOPENED r1 #10, out of envelope, banked): a keyframe-aligned head trim passes `open`.
    Proposed with S1: refuse a media segment whose `media_time` is not the track's earliest
    composition time (the same sample-table read); test from `r2\repro\repro_f2.py`.
  - **#3** (MINOR cleanup): `nvenc_proof` must not say `tied` without a resolved GPU UUID.
  - Then Reviewer A round 3 on that remediation (recommended: product-code change), then a
    full-pytest WINDOW request.
- Still waiting for WP3.9 on main: the GX011627 product leg, the AD-12 quality table, the export
  FLOOR speed row (`tools/video_io_bench.py`, EXCLUSIVE window), the report's PENDING sections.
- Decided and not to be redone: round 0 (NUT + end sentinel + setts/noise BSF, INFO packet), the
  round-0 rulings, CHARC's Q-A/Q-B/Q-C/Q-D notes, P8 (stated non-square SAR refused; an unseen
  SAR is 1:1, `01d1578`).
- Working notes: targeted runs use `-m "not footage"`; the e2e module takes about 3.5 min, the
  unit, fidelity and probe modules about 35 s. Scratch scripts are under `work\wp3.10\r2\`
  (gitignored). Test-file edits with non-ASCII must use escapes.

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
