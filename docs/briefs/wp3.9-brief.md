# WP3.9 — Video decode (dispatch brief, DRAFT for CHARC)

**Status:** DRAFT 2026-10-21, written by a drafting helper for the orchestrator (generation 9) at
CHARC's commission `e7745b2be6fdd55c` (tranche A). Not approved; base = the pre-dispatch main
commit named at dispatch. Owner decisions: none inside the package.
- Spec **v0.5.4** (owner-approved 2026-10-20). Architecture FINAL 1.0 section 3 IF-1 and IF-5,
  section 5 "Decode (WP3.9)"; AD-2, AD-10, AD-11, AD-19, AD-20, AD-23. Frame
  `docs/briefs/wp2.4-phase3-frame.md` (sections 1, 2, 4, 5; section 5 maps "N1 pipe exception
  (AD-23)" to WP3.9 and WP3.10). WP2.1S report `docs/reports/wp2.1s-io-spike.md` sections 1, 4
  and 6, and `tools/spike_io/transport.py` (`BIG_PIPE_BYTES`, the fallback) as reference reading.
  WP3.7 accept `docs/proofs/wp3.7-accept.md` ("Follow-ons"); WP3.5 report
  `docs/reports/wp3.5-video-colour.md` ("For other packages").
- Cell: `implementer-opus-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.9`, branch `wp3.9` from main, base = the main commit named at dispatch.

**Why.** Both video passes start here: architecture section 2, "io.video.frames (transport AD-2)
-> Frame (IF-1, pts exact)" for the analysis pass (WP3.11) and "io.video.frames ->
method.render(...)" for export (WP3.14); the shell already decodes one frame at a position
through `VideoSource.frames` (`clearwater.gui.sources.first_frame`, WP3.16). WP2.1S closed the
transport (AD-2): "FFmpeg process writing raw frames to an anonymous pipe whose buffer is
enlarged to 32 MiB (`BIG_PIPE_BYTES`, one constant; Windows-specific, AD-23) with automatic
fallback to the default pipe".

| Field | Content |
|---|---|
| ID and title | WP3.9 — Video decode; plan section 6 Phase 3 row WP3.9 (size M); module `clearwater.io.video` (plan 8.1: "Probe, validation, chapters, decode, encode, mux", WP3.7-WP3.10) |
| Goal | A class satisfying IF-5 `VideoSource` whose `frames` runs one FFmpeg process per call, delivers every decodable frame as an IF-1 `Frame` with its exact source pts, by software or CUDA decode, over the AD-23 pipe, and stops cleanly at the readable end of a truncated file; `probe` delegates to WP3.7's `probe`. |
| Spec / decision clauses | Plan bullet: "**WP3.9** yields frames (IF-1) with their exact source timestamps, by software or hardware decode, and stops cleanly at the readable end of a truncated file." 5.2 "MP4 container, H.265/HEVC or H.264."; "8-bit and 10-bit sources handled without truncating 10-bit data."; "Constant and variable frame rate accepted; timing preserved (Section 7.5)." 5.4 "Truncated or corrupt video sources (e.g., last chapter after a battery failure) are processed up to the readable portion, with a clear warning (D86)." 6.4 "All processing in 32-bit floating point, normalized to [0, 1]; quantization only at export." 6.5 Video in: "matrix, range, primaries and transfer characteristics are read from the stream. If missing or unexpected, BT.709 with limited range is assumed and the user is warned (D54). Chroma upsampling to full resolution is performed before processing." 7.5 "Per-frame presentation timestamps, start offset and MP4 edit list are copied from the source, not recalculated (D94)."; "Variable-frame-rate input is processed with its original timing preserved (D95)." D86 "Truncated/corrupt video: process the readable portion and warn". D94 "Per-frame timestamps, start offset and edit list preserved and verified. *(0.5.4 reading, AD-22)* ..." (the edit-list reading is WP3.10's). D95 "Variable-frame-rate input processed with timing preserved; smoothing window defined in time, not frames (tested per D115)". N1 "Approved exception (0.5.4, AD-23): the enlarged anonymous-pipe buffer for frame transport on Windows, with an automatic portable fallback that yields identical frames and timestamps." N4 "frame parallelism and buffering are bounded to meet these limits." Feeds V4 ("output matches source frame count, per-frame timestamps, start offset, resolution, bit depth ..."; "the test set includes one variable-frame-rate sample (D115)": the decode leg) and V9 ("This exercises the full decode → process → encode path, including color tags and ICC handling": the decode leg; AD-11 "V9 is measured on the decoded-RGB side with the encoder AND its 8-bit Y'CbCr 4:2:0 conversion excluded (AD-10)"). |
| Depends on | On main: WP2.2 (`b288533`, IF-1/IF-5 frozen), WP2.3 (`d605925`, the video samples), WP2.1S (`a866f06`, the transport), WP3.7 (accept `6e3417a`: `clearwater.io.video.probe`, `find_tool`, `VideoProbeError`, `clearwater.io.video.inputs.ascii_text`), WP3.5 (accept `55c266d`: `clearwater.color.decode_filter`, `decode_pix_fmt`, `rgb_frame_bytes`, `planes_to_rgb`, `ColorError`). WP2.3 samples by manifest id: `vid-hevc8-bt709-full`, `vid-hevc10`, `vid-untagged`, `vid-truncated`, `vid-vfr`, `vid-rotated` (decoded), `vid-hlg`, `vid-pq` (refused); the expected values are each entry's `facts` (`facts.pts.ticks`, `facts.pts.sha256` = SHA-256 of the packet tick list joined by commas, `tools/fixtures/video.py`; `facts.decoded.frames`: 24 for `vid-truncated` against 25 packets). No stub needed: nothing this package calls is unmerged. |
| Files owned | `src/clearwater/io/video/decode.py` (NEW: the `VideoSource`; name per the round-0 table); `src/clearwater/io/video/pipes.py` (NEW: `BIG_PIPE_BYTES` and the large-pipe helper with its fallback, question 1); `src/clearwater/io/video/__init__.py` (APPEND exports only, question 2); `src/clearwater/io/video/probe.py` (ONLY the two log lines of DR-36 (a), question 9); `tests/test_io_video_decode*.py` (NEW); `docs/reports/wp3.9-video-decode.md`; `docs/proofs/wp3.9-ledger.md`. NOT owned: `src/clearwater/interfaces/`, `src/clearwater/color/`, the rest of `src/clearwater/io/video/` (WP3.10 adds `encode` and friends in parallel), `tools/` (`tools/spike_io/` and `tools/prototype/clip.py` are reference reading; `src/` never imports `tools/`), `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/fixtures/`, `pyproject.toml` (no dependency: stdlib, NumPy and the FFmpeg CLI). |
| Interfaces provided | IF-5 `VideoSource` exactly as frozen: `probe(path) -> ProbeResult` (delegates to `clearwater.io.video.probe`) and `frames(probe, *, hw_decode, start_s=None, end_s=None) -> Iterator[Frame]` ("Yield the frames of a probed file with exact pts; stops at the readable end (D86)"). Outside the IFs: the decode error class of question 3, and `pipes.BIG_PIPE_BYTES` with the pipe helper (question 1). |
| Interfaces consumed | IF-5 `ProbeResult`, `VideoStreamInfo` (`width`, `height`, `bit_depth`, `pix_fmt`, `chroma_siting`, `color`, `time_base`, `nb_frames`, `rotation`, `vfr`), `Fault` (a `"refuse"` severity means "never to be decoded", WP3.7 `probe` docstring); IF-1 `Frame` (`pixels` float32 `(H, W, 3)` RGB `[0, 1]`, `device`, `color`, `orientation_applied`, `pts`, `pts_ticks`, `time_base`, `index` "informational only, never a key"). `clearwater.color`: `decode_filter(stream)` ("The same filter serves software decode and `-hwaccel cuda` (frames downloaded to system memory first)"), `decode_pix_fmt(stream)` (`gbrp` / `gbrp10le`), `rgb_frame_bytes(width, height, bit_depth)`, `planes_to_rgb(data, *, width, height, bit_depth)`, `ColorError`. `clearwater.io.video`: `probe`, `find_tool("ffmpeg")`, `VideoProbeError`; `clearwater.io.video.inputs.ascii_text`. FFmpeg 9.0.2 (gyan) on PATH as a subprocess. |
| Consumers | Wave 3: WP3.11 builds against `stubs.StubVideoSource` and swaps in this class at WP4.2; WP3.18 (scrubber) decodes through the shell's `frame_at` / `first_frame`, which calls `frames(..., start_s=...)`, takes one frame and calls the iterator's `close()` (`src/clearwater/gui/sources.py`). Wave 4: WP3.14 export, WP3.21 (re-measure), WP4.2. WP3.10 (parallel) uses this class for its footage legs once merged (WP3.10 question 12). |
| Hardware flags | No timing or memory figure (frame section 3: exclusive timing lives in WP3.1's and WP3.10's reports), so not exclusive. `gpu` on the `hw_decode=True` tests (skip without CUDA decode). `footage` on the GX011627 test: read-only, through `tools/local_config.find_footage_file`, skipped when absent. |
| Out of scope | Probing (WP3.7: consumed, never re-done: the colour description, D54 included, is taken from the `ProbeResult` given, never re-probed); colour arguments and sample conversion (WP3.5: consumed); encode, mux, the edit-list reading of AD-22 (WP3.10); the proxy (WP3.11, AD-5); chapter grouping (v2, spec 5.5); any timing row; the encode-side pipe (WP3.10 question 2); Linux `F_SETPIPE_SZ` (AD-23: "untested (a later note)"); decoding any stream but the video stream: no audio, no `gpmd`, no `tmcd` stream is mapped, opened or read (GoPro IMU and GPS are out of scope: no `gpmd`, IMU or GPS data). |
| Debt and decided items | **AD-23** -- IMPLEMENTS -- both conditions: "automatic fallback to the default pipe with identical bytes and exact pts when the large buffer cannot be created (forced-failure row demonstrated), and the size as one named constant (`BIG_PIPE_BYTES`) with its measurement beside it." **AD-2 / AD-10** -- IMPLEMENTS -- one FFmpeg process per `frames` call, planar RGB at the source depth through WP3.5's filter. **D54** -- consumed from WP3.7's probe, never re-probed (task 4 proves it). **DR-36 (a)** ("two structural log warnings in `probe.py` interpolate `path.name` without `ascii_text`") -- CLOSES -- the two lines, question 9. **DR-36 (b)** ("the manifest test checks the VFR flag and track duration, not the packet pts sha256") -- CLOSES -- task 7 checks every decoded pts against `facts.pts.ticks` and `facts.pts.sha256`. **DR-36 (c)-(f)** -- not this package's (probe messages, box reader, `_fraction`, the tail check; out of envelope). WP3.7 consumer note ("WP3.9 never uses an open-ended `-read_intervals` for frame counts (19 partial lists in 400 runs on ffprobe 9.0.2)") -- IMPLEMENTS -- any ffprobe call this package makes uses a bounded interval (`<start>%<end>` or `%+<span>`); recommended: none at all (question 4). **DR-39 (c)** ("the FFmpeg pixel rows do not cover `yuvj420p` + BT.601 full, matched non-left sitings ...") -- PARTLY -- the decode rows of task 7 cover `yuvj420p` + BT.601 full and one non-left siting on clips built under `tmp_path`; the D76 rows are WP3.10's. DR-39 (a), (b), (d) -- not this package's (encode side, `rgb_to_planes`). **DR-20 (2)** ("duplicate or non-monotonic pts are de-duplicated") -- must not reopen -- the decoder never de-duplicates: a repeated or decreasing pts is an error by name (task 3). **DR-20 (3)** ("a `%` in a root path is expanded by FFmpeg's image-sequence muxer") and **(5)** ("`v:0` is taken without a cover-art check") -- PARTLY, for the decode command: paths reach FFmpeg as `file:` URLs and a test decodes from a folder whose name holds `%` and non-ASCII characters; the decoder maps the stream the probe described (question 5). DR-20 (4), (6), (7) are WP3.10's / 8.4's. **DR-28 (4)** ("while blocked on the decoder queue, the main loop does not poll the encoder") -- PARTLY -- the decode side: an FFmpeg failure or exit surfaces at the next `next()`, never as a stall (task 5). **DR-44 (a)** -- not this package's (WP3.18 and the shell); the start semantics of task 6 are what it relies on. |
| Done | Plan 4.5; frame section 2 rules 1-11; ruff check, ruff format --check, mypy strict, full pytest green (in a granted window); every decodable WP2.3 video sample decodes to its manifest pts; the AD-23 fallback proven identical; V4 and V9 decode legs shown by named tests; DR-36 (a) and (b) closed; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table.** Before product code, write in the ledger:
   - the exact FFmpeg command line(s) for software and CUDA decode, with each option's reason
     (expected at least: `-nostdin`, `-noautorotate`, `-copyts`, the `file:` input, `-map` of
     the probed video stream only with `-an -sn -dn`, WP3.5's `decode_filter` with the pts side
     channel first in the chain, an EXPLICIT `-fps_mode passthrough`, `-f rawvideo` to the
     pipe; never rely on the rawvideo muxer's default frame-rate mode);
   - the pts side channel (question 4) and how frame n's bytes are paired with pts n;
   - seeking for `start_s` / `end_s` and their exact semantics (question 6);
   - the pipe (question 1), the thread and queue layout with its bound in frames and bytes
     (N4), and the process lifecycle on exhaustion, `close()`, garbage collection and error;
   - the error class and its kinds (question 3), and what ends cleanly versus what raises;
   - `Frame` field values (question 7);
   - the answers to the other questions.

   YIELD for the dispatcher. Anything the table cannot settle is a STOP.
2. **The pipe (`pipes.py`, AD-23).** One named constant `BIG_PIPE_BYTES` (32 MiB, as
   `tools/spike_io/transport.py`) whose docstring carries WP2.1S's measurement (row `b` 16.1
   ms/frame against 55.9 ms on the default pipe, W4/W2). The large buffer on Windows; when it
   cannot be created (or off Windows, question 1), the default pipe, with the reason logged
   once. No other OS-specific code (N1, frame rule 11).
3. **Frames.** `frames` refuses at once, without starting FFmpeg, a probe carrying any
   `"refuse"` fault (HLG, PQ). Otherwise one FFmpeg process; each frame read whole
   (`rgb_frame_bytes`), converted by `planes_to_rgb`, and yielded as a `Frame` with
   `pts_ticks` from the side channel, `time_base = probe.video.time_base`, `pts = pts_ticks *
   time_base` (exact `Fraction`), `color = probe.video.color`, `index` in delivery order.
   Every pts is checked strictly increasing; a repeat or a decrease is an error by name (DR-20
   (2)), never dropped. 10-bit sources stay 10-bit (`gbrp10le`, 5.2).
4. **D54 consumed, never re-probed.** The filter is built from the `ProbeResult` given, so an
   untagged stream decodes as BT.709 limited and an untagged `yuvj` stream as full (DR-20
   item (1) closure, WP3.5 accept). No ffprobe run reads colour.
5. **Readable end and failure (5.4, D86).** A file the probe flagged `truncated` or
   `unreadable_tail` yields every decodable frame and ends without raising (the warning is the
   probe's fault, shown by the shell). An unexpected failure (FFmpeg exits nonzero on a file the
   probe found clean, a short read, an orphan pts line) raises the question-3 error after the
   last good frame, with FFmpeg's stderr tail in the log (ASCII-safe through `ascii_text`). No
   stall: a dead FFmpeg surfaces at the next `next()`.
6. **Seeking.** `start_s` / `end_s` per question 6; frame-exact on every sample: the first frame
   yielded is the first whose pts is at or after `start_s`, and no frame at or after `end_s` is
   yielded.
7. **Tests.**
   - Every decodable WP2.3 video sample by manifest id: frame count (`facts.decoded.frames`),
     the decoded tick list equal to `facts.pts.ticks` (its first `decoded.frames` entries for
     `vid-truncated`) and its comma-joined SHA-256 equal to `facts.pts.sha256` on the intact
     samples (DR-36 (b)); width, height, bit depth.
   - `vid-vfr`: exactly the 30 frames of `pts_ticks_intended`, none duplicated or dropped.
   - `vid-truncated`: 24 frames, then a clean end, no exception.
   - `vid-hlg`, `vid-pq`: refused before FFmpeg starts.
   - Pixels: each sample's frames equal, byte for byte, an independent FFmpeg CLI run of the
     same filter to a raw file under `tmp_path` (the transport loses, adds and shifts nothing);
     `vid-hevc10` reaches codes that an 8-bit path cannot produce.
   - Never re-probed: a `ProbeResult` with its range altered by `dataclasses.replace` changes
     the decoded pixels accordingly (a decoder that re-probes fails by name).
   - `vid-rotated`: pixels as stored (320 x 180), rotation untouched.
   - AD-23: the forced-failure path (the large pipe made to fail) gives identical bytes and pts
     on every sample and on the footage row.
   - Seeking: `start_s` at every pts of `vid-vfr` and `vid-hevc8-bt709-full`, between two pts,
     before the first and after the last; `end_s` exclusive.
   - Lifecycle: `close()` after one frame ends FFmpeg within a bounded time (no live child
     process, no thread left); an iterator dropped without `close()` is cleaned up; a planted
     FFmpeg death mid-stream raises, never hangs.
   - DR-39 (c) decode rows: `yuvj420p` + BT.601 full and a non-left siting, built under
     `tmp_path` with FFmpeg (as WP3.5 built its BT.601 clip).
   - Paths: a sample copied under a `tmp_path` folder whose name holds `%` and a non-ASCII
     character decodes identically (DR-20 (3)).
   - `gpu`: `hw_decode=True` gives the same bytes and pts as software on the samples and on the
     footage row (WP2.1S: "All 23 transport forms decode the same 681 frames to the same bytes
     as row a").
   - `footage`: GX011627 (WP2.1S: 681 frames, pts 0 to 680 x 1001 at 1/30000), every frame's
     pts and a per-frame hash against an independent FFmpeg run; read-only.
   - Static: no decode command maps an audio or data stream; `src/` does not import `tools`.
   - Dependency rule (plan 8.1, frame rule 5): importing `clearwater.io.video` loads nothing
     from `clearwater.gui`, `.jobs`, `.methods`, `.core`, `.analysis`, nor `PySide6`, `cupy`.

## Declared operating envelope

Windows 11; Python 3.12; FFmpeg 9.0.2 (gyan) on PATH; MP4/MOV with one HEVC or H.264 video
stream, 4:2:0, 8- or 10-bit, as WP3.5's supported set (`yuv420p`, `yuvj420p`, `yuv420p10le`;
BT.709 or BT.601); the HERO13 4K clips and the WP2.3 samples; local NTFS or exFAT volumes; one
Clearwater process; a CUDA-capable NVIDIA card for `hw_decode=True` (the RTX 4070 Laptop GPU).
Out of envelope: other FFmpeg builds, 4:2:2 and 4:4:4 (refused by WP3.5's `ColorError`),
multi-video-stream and cover-art files, fragmented MP4, network shares, files changed between
probe and decode, hostile files beyond FFmpeg's own checks, other operating systems (portable
through the fallback, not run there). AD-23's figure is for 8-bit 4K; a 10-bit 4K `gbrp10le`
frame (49,766,400 bytes) is larger than the 32 MiB buffer: correct either way, not re-timed here.

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.9\rN\`; ledger `docs/proofs/wp3.9-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.6\r1\`
  (`run_review.sh`, `review-prompt.md`; keep `probe.txt`, `review-diff.txt`, `review.txt`,
  `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer excludes
  `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - pts exact and paired one-to-one with frame bytes: no off-by-one under reordering, VFR,
    a truncated tail, a seek, or a side-channel line arriving late;
  - no frame dropped, duplicated or invented (`-fps_mode`), no pts de-duplicated;
  - the probe's colour description used unchanged; 10-bit never truncated;
  - the AD-23 fallback: same bytes and pts, reason logged, one constant; nothing else
    OS-specific;
  - process and thread lifecycle: `close()`, garbage collection, FFmpeg death, no deadlock on
    a full stderr or stdout pipe, buffering bounded (N4);
  - seeking exactness at and between pts;
  - clean end versus raise per 5.4 / D86;
  - no audio or data stream mapped (no `gpmd`, IMU or GPS data); nothing in `interfaces/`
    changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review round:
  END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating; make NO change
  in the turn that adjudicates a round. Past ~250K tokens, "REVIEW ONLY this turn" when told.
  Report `uv run python scripts/cell_depth.py <your cell name>` at every yield (~250K
  evaluation point, ~400K STOP).
- **Full-pytest windows (X5).** The full suite (about 3559 tests, about 15 min) runs ONLY in a
  window the dispatcher grants by message, in the background with `QT_QPA_PLATFORM=offscreen`
  and output to a file under `work/`; send `WINDOW RELEASED: <summary>` when it finishes. Never
  two heavy jobs at once. Inner loops run only your own tests.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4), delivered to your dispatcher by your messaging tool: the public API, the command
  lines, the sample table (manifest id, frames, pts check, pixels check), the AD-23 rows, the
  gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or in
  `src/clearwater/color/`; a dependency; any OS-specific code beyond AD-23's pipe; a WP2.3
  sample whose decoded facts disagree with its manifest; a pts you cannot make exact; any need
  to read an audio, `gpmd` or `tmcd` stream; any write to the footage folder; the round-0 table
  showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with
  `git -c core.autocrlf=false commit ...`, `feat(wp3.9): ...`, with a `Co-Authored-By:` footer
  naming your model. Never `git stash` (shared stack: use a WIP commit or a scratch copy). Never
  a bare `cd`. Never post to a mailbox. Footage read-only at `C:\Users\rwsmy\clearwater-footage\`;
  outputs under `work/`. Gates: ruff check, ruff format --check, mypy strict, full pytest (in a
  window); no harness gate. Report `docs/reports/wp3.9-video-decode.md` (claims, evidence paths,
  limits). GoPro IMU and GPS are out of scope: no `gpmd`, IMU or GPS data is read anywhere.

## Questions for CHARC (recommended answer first)

1. **X-V1 (cross-brief, WP3.9 and WP3.10): the pipe and who owns it.** AD-23 permits the large
   buffer "in `io.video`"; WP2.1S measured only the decode side. Recommended: WP3.9 owns
   `clearwater.io.video.pipes` (`BIG_PIPE_BYTES` and the helper); on Windows the large pipe,
   elsewhere the default pipe (the AD-23 fallback; no untested `F_SETPIPE_SZ` code in the
   product, N1); WP3.10 writes its encoder's stdin through the default pipe, and any encode-side
   tuning is WP3.21's. Alternative: WP3.9 ships `pipes.py` early to main at its round-0 yield
   so WP3.10 can import it.
2. **X-V2 (cross-brief): shared package files.** Both cells append to
   `src/clearwater/io/video/__init__.py` in parallel worktrees. Recommended (as X1 for
   `io/__init__.py`): each appends only its own export lines and one docstring sentence;
   whichever merges second rebases; no other shared file.
3. **The decode error vocabulary.** IF-5 `frames` has no warning channel. Recommended:
   `clearwater.io.video.VideoDecodeError(kind, message)` mirroring `VideoProbeError`, kinds
   `"refused"` (a probe with a `"refuse"` fault), `"unreadable"` (an unexpected failure on a
   file the probe found clean, raised after the last good frame), `"pts"` (a missing, repeated
   or decreasing pts); a missing FFmpeg is `VideoProbeError("missing_tool")` from `find_tool`;
   a probe-flagged truncation ends cleanly (its warning is the probe's `Fault`).
4. **The pts side channel.** Recommended: `showinfo` first in the filter chain, its stderr
   drained by a thread and parsed per frame (WP2.1S: "Every pts side channel delivers 681/681
   pts exactly as ffprobe lists them"; cost 0.6-1.0 ms/frame), frame n paired with line n;
   `-copyts` so the pts are the source's (a non-zero start stays non-zero); no ffprobe run in
   `frames` (the packet list is the probe's job; counts come from the stream itself).
5. **Which video stream.** `VideoStreamInfo` carries no stream index; WP3.7's probe takes the
   first `codec_type == "video"` stream. Recommended: map `0:v:0`, the same stream, and treat a
   cover-art (`attached_pic`) first stream as out of envelope (documented, DR-20 (5) stays OPEN
   for the probe side).
6. **Seek semantics.** Recommended: `start_s` = the first frame whose pts is at or after it;
   `end_s` exclusive; implemented with an input `-ss` a little before `start_s` plus `-copyts`
   (the prototype's method, `tools/prototype/clip.py` `decode_command`) and a guard in Python
   that discards any frame before `start_s` by pts, so exactness never rests on FFmpeg's seek
   alone; `start_s` past the last frame yields nothing.
7. **`Frame` field values.** Recommended: `device="cpu"` (the caller uploads, IF-2);
   `orientation_applied=False` (pixels as stored under `-noautorotate`; the display rotation is
   carried by the sink, D105; the IF-1 field is documented for photos); `color` the probe's.
8. **`hw_decode=True` without CUDA.** Recommended: `-hwaccel cuda` without
   `-hwaccel_output_format cuda`, so FFmpeg falls back to software decode by itself; the bytes
   are the same either way (test 7), and the fallback is logged once when FFmpeg reports it. The
   AD-9 force-CPU setting is the caller's (it passes `hw_decode=False`).
9. **DR-36 (a) in a WP3.7 file.** The fix is two log lines in `probe.py`. Recommended: grant
   WP3.9 exactly those two lines (`ascii_text(path.name)`), nothing else in `probe.py`, so DR-36
   (a) closes with (b) here (the register names "WP3.9's brief" as the trigger).
