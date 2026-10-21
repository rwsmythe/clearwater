# WP3.10 — Video encode, mux and timing (dispatch brief, DRAFT for CHARC)

**Status:** DRAFT 2026-10-21, written by a drafting helper for the orchestrator (generation 9) at
CHARC's commission `e7745b2be6fdd55c` (tranche A). Not approved; base = the pre-dispatch main
commit named at dispatch. Owner decisions: none inside the package (a mandatory item that
cannot be met is a STOP; relaxing one is owner-reserved).
- Spec **v0.5.4** (owner-approved 2026-10-20). Architecture FINAL 1.0 section 3 IF-5, section 5
  "Encode and mux (WP3.10)"; AD-2, AD-10, AD-11, AD-12, AD-13, AD-16, AD-20, AD-22, AD-23. Frame
  `docs/briefs/wp2.4-phase3-frame.md` (sections 1, 2, 4, 5; section 5 maps "D94 reading
  (AD-22)", "D75 names and mapping" and "N1 pipe exception (AD-23)" here; section 3: "Exclusive
  timing lives only in WP3.1's and WP3.10's reports (speed rows)"). WP1.5 report
  `docs/reports/wp1.5-container-spike.md` sections 1, 4-6, 8, 9 and `tools/container_spike/`
  (`spike.py` `reencode_command`, `compare.py`) as reference reading; the prototype export loop
  `tools/prototype/clip.py` (`encode_command`, CFR-from-0 only) as reference reading. WP3.13
  report "Consumer notes"; WP3.5 report "For other packages"; WP3.7 accept "Follow-ons".
- Cell: `implementer-opus-high`. Tier **STRONG**. Plan: "WP3.10 is the largest risk in the build".
- Worktree `.worktrees/wp3.10`, branch `wp3.10` from main, base = the main commit named at dispatch.

**Why.** Every corrected video leaves through this sink: architecture section 2, "io.video.sink
(NVENC/libx265, copyts, audio+gpmd copy)". D105 makes "per-frame timing, start offset, audio sync
and display orientation" mandatory. WP1.5 proved the SIMPLE approach on a file-to-file re-encode
only ("Frame access for the correction is NOT exercised here"); the prototype's pipe encode
assumed constant rate from pts 0 (`clip.py` `_check_constant_rate`). The product must keep the
same fidelity with frames arriving from Python, on VFR and offset sources too.

| Field | Content |
|---|---|
| ID and title | WP3.10 — Video encode, mux and timing; plan section 6 Phase 3 row WP3.10 (size L); module `clearwater.io.video` (plan 8.1) |
| Goal | A class satisfying IF-5 `VideoSink` that encodes corrected frames to HEVC in MP4 through NVENC or libx265 at 8 or 10 bits and the D75 levels, with the source's tags and chroma format, audio passed through, per-frame pts, start offset, edit list (AD-22) and display orientation preserved, best-effort metadata carried where cheap, provenance embedded, and encoder capabilities reported; plus a fidelity instrument and the export speed row. |
| Spec / decision clauses | Plan bullet: "**WP3.10** is the highest-risk package. It encodes HEVC through NVENC or the software encoder at 8 or 10 bits and the named quality levels, matches the source's tags and chroma format, passes audio through unchanged, preserves per-frame timestamps, start offset, edit list and display orientation, carries best-effort metadata where cheap, and reports encoder capabilities. Its approach is the one chosen from WP1.5." 6.5 Video out: "matrix, range, primaries and transfer tags match the source (D55). Chroma subsampling and pixel format also match the source, normally 4:2:0 for GoPro footage (D114)." 7.5 "Audio passed through unchanged."; "Per-frame presentation timestamps, start offset and MP4 edit list are copied from the source, not recalculated (D94)."; "Variable-frame-rate input is processed with its original timing preserved (D95)." 8.2 "**Format:** MP4, HEVC. 10-bit when the source is 10-bit; optional 10-bit output for 8-bit sources, off by default (D76). Chroma subsampling and pixel format match the source (D114)."; "**Encoder:** NVENC or software, user-selectable. Encoder capabilities (including 10-bit support) are detected at startup; unavailable options are shown disabled with a reason (D74)."; "**Color tags** match the source (Section 6.5)."; "display orientation: the output plays in the same orientation as the source, by keeping the rotation flag or an equivalent."; "**Best-effort metadata (D105):** creation date/time, GPMF telemetry track, timecode track and camera-settings atoms are kept where the chosen video I/O approach preserves them at low cost. Items that are not preserved are documented as a known limitation."; "**Provenance:** Clearwater version and parameters embedded in metadata; on by default, can be turned off." 8.4 "On cancel or failure, the temporary file is deleted (consistent with D44)." D25 "*(amended by D76)* Video output: MP4, HEVC only; 10-bit when source is 10-bit, optionally 10-bit for 8-bit sources"; D26 "Video encoder: user choice of NVENC or software encoder"; D54; D55 "Output video color tags and range match the source"; D62; D74 "Unavailable encoder options shown disabled with a reason"; D75 "Video quality set by named levels High / Standard / Draft, mapped per encoder (provisional mapping AD-12: NVENC HEVC cq 18 / 23 / 28, libx265 crf 18 / 23 / 28; verified at WP3.10)"; D76 "Optional 10-bit output for 8-bit sources, off by default"; D91 "Clearwater version and parameters embedded in output metadata; on by default, can be turned off"; D94 "Per-frame timestamps, start offset and edit list preserved and verified. *(0.5.4 reading, AD-22)* Where only the encoder's composition-offset convention differs from the source's, "copied, not recalculated" is read by presentation effect: pts sequence, start offset, duration and first displayed frame exact; the as-written `media_time` may differ"; D95; D105 "Video fidelity priorities: per-frame timing, start offset, audio sync and display orientation are mandatory; other video metadata is best-effort"; D114 "Output video chroma subsampling and pixel format match the source"; D115. N1 (AD-23 exception), N4 ("peak RAM ≤ 16 GB"), N8 ("existing outputs never overwritten"). Feeds V4 (all of it: "mandatory: output matches source frame count, per-frame timestamps, start offset, resolution, bit depth (or the selected 10-bit option), chroma format, audio and display orientation; color tags match the source"; "best-effort: which of creation time, GPMF, timecode and camera atoms are present is recorded"; "the test set includes one variable-frame-rate sample (D115)") and V9 (the encode leg; AD-11: "V9 is measured on the decoded-RGB side with the encoder AND its 8-bit Y'CbCr 4:2:0 conversion excluded (AD-10)"). |
| Depends on | On main: WP2.2 (`b288533`), WP2.3 (`d605925`: `vid-hevc8-bt709-full`, `vid-hevc10`, `vid-untagged`, `vid-truncated`, `vid-vfr`, `vid-rotated`, `vid-hlg`, `vid-pq`), WP1.5 (`3242679`), WP2.1S (`a866f06`), WP3.7 (accept `6e3417a`: `probe`, `find_tool`, `VideoProbeError`, `inputs.ascii_text`), WP3.5 (accept `55c266d`: `encode_filter`, `encode_pix_fmt`, `rgb_pix_fmt`, `rgb_to_planes`, `ffmpeg_color_names`, `ColorError`), WP3.13 (accept `6dd5a00`: `SafeWrite`, `plan_output`, `MediaKind`, used by tests only), WP3.15 (accept `da54a47`: `clearwater.config.check_string_keys`). **WP3.9 is parallel and unmerged:** unit tests feed the sink frames from `stubs.StubVideoSource` or a test-side FFmpeg decode; the footage legs, the AD-12 check and the speed row need WP3.9's merged `frames` (question 12). |
| Files owned | `src/clearwater/io/video/encode.py` (NEW: the `VideoSink`); `src/clearwater/io/video/capability.py` (NEW: D74 detection and the encoder resolution of question 4); the pts-carrier module of question 1 (NEW, name per the round-0 table); `src/clearwater/io/video/verify.py` (NEW, question 6); `src/clearwater/io/video/__init__.py` (APPEND exports only, X-V2); `tests/test_io_video_encode*.py` (NEW); X1-style outside the module path: `tools/video_fidelity.py` (NEW: the compare instrument, DR-18) and `tools/video_io_bench.py` (NEW: the speed row), with `tests/test_video_fidelity.py`; `tools/container_spike/spike.py` ONLY for DR-26 (question 15); `docs/reports/wp3.10-video-encode.md`; `docs/proofs/wp3.10-ledger.md`. NOT owned: `src/clearwater/interfaces/`, `src/clearwater/color/`, `src/clearwater/jobs/` (including `disk_space.QUALITY_RATIO`, question 13), WP3.9's `decode.py`/`pipes.py`, WP3.7's `probe.py`/`boxes.py`/`gopro.py`/`inputs.py`, `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/fixtures/`, `pyproject.toml` (no dependency). |
| Interfaces provided | IF-5 `VideoSink` exactly as frozen: `capabilities() -> tuple[EncoderCapability, ...]`, `open(probe, out_path, *, encoder, quality, bit_depth, provenance)`, `write(frame)` ("in pts order. The sink preserves pts, start offset, edit list (AD-22), audio, gpmd, tmcd and rotation."), `close() -> SinkReport`, `abort()` ("Stop and remove the partial output (D44, D85)."). Outside the IFs: the encode error class (as WP3.9's question 3), the encoder resolution helper (question 4). |
| Interfaces consumed | IF-5 `ProbeResult` (`start_offset_s`, `video`, `audio` with `index`, `data` with `index`/`codec_tag`, `edit_list`, `faults`), `EncoderCapability`, `SinkReport`; IF-1 `Frame`. `clearwater.color`: `encode_filter(stream, *, bit_depth)`, `encode_pix_fmt(stream, *, bit_depth)`, `rgb_pix_fmt(bit_depth)`, `rgb_to_planes(a, *, bit_depth)`, `ffmpeg_color_names(color)`, `ColorError`. `clearwater.config.check_string_keys`. IF-10 `Settings.video_encoder` ("`"auto"` ... Provenance records the resolved encoder, never `"auto"`") and `quality_level` (`"high"`, `"standard"`, `"draft"`, lower-case). FFmpeg / ffprobe 9.0.2 (gyan) as subprocesses. |
| Consumers | WP3.14 (export: plans the name, opens `SafeWrite`, hands `temp_path` to `open`), WP3.20 (settings: D74 disabled options, D75 names), WP3.21 (the speed row is its baseline), WP4.2, WP5.1 (V4). Stub until this merges: `stubs.StubVideoSink` (records `opened`, `frames`). |
| Hardware flags | **EXCLUSIVE** on task 10 (timing and memory figures, plan 4.3: "Timings are taken on a full clip, not one frame"; frame rule 7: best effort, strays and clocks recorded, contaminated rows kept as spread). `gpu` on NVENC tests (skip when NVENC is unavailable). `footage` on GX011627 / GX011625 legs: read-only, through `tools/local_config.find_footage_file`; outputs under `work/` only. |
| Out of scope | Decode (WP3.9); colour arguments and sample conversion (WP3.5: consumed); naming, the temporary and the rename (WP3.13; the caller); export orchestration, progress, batch, the V16 end-to-end row (frame section 5 maps "D106 interim N6 / V16" to "WP3.14 (export timing row), WP5.2 re-measure"); any optimisation (WP3.21); chapter concatenation (v2); H.264, AV1 or 4:2:2 output; decoding, parsing or logging any `gpmd` packet (no `gpmd`, IMU or GPS data is read); reading or logging any location tag. |
| Debt and decided items | **AD-22 / DR-15** (B-frame edit list: "copied, not recalculated" read by presentation effect, media_time by convention) -- IMPLEMENTS; CLOSES DR-15 only if CHARC accepts the substitute evidence of question 7, else PARTLY (the iPhone leg waits for an owner clip). **DR-17** ("implement and test the D54 fallback (assume BT.709 limited, warn, tag the output) on a synthetic untagged clip") -- CLOSES -- on `vid-untagged`. **DR-18** (the four blind spots: "(1) the GPU sample behind an NVENC proof is not tied to the encode window, GPU UUID or FFmpeg PID; (2) AAC decoder configuration, priming and packet side data are not compared ...; (3) `build_record` has no roster invariant ...; (4) the camera record does not count frames with a missing pts") -- CLOSES -- "the product's compare instrument closes all four, or states why not" (task 9). **DR-26** (the spike resolves chapters at the footage root) -- CLOSES if question 15 is granted, else not this package's (the product instrument resolves through `find_footage_file` and never runs the spike CLI). **DR-39 (a)** ("the D76 RGB-side leg (8-bit decoded RGB to 10-bit planes) is within AD-11 ... but not separately asserted against it") -- CLOSES -- WP3.10 owns the D76 export path (task 11). **DR-39 (b)** (`rgb_to_planes` accepts a non-contiguous array) and **(d)** (bit depth `8.0` accepted) -- must not reopen -- the sink passes a C-contiguous float32 array and validates `bit_depth` as an `int` in {8, 10} at `open`; `clearwater.color` is not edited. **DR-39 (c)** -- PARTLY -- the D76 rows from limited-range (`vid-untagged`) and BT.601 sources. **DR-20 (4), (6), (7)** (product side) -- (4) CLOSES for the product: the instrument refuses `yuvj420p` with `tv` and never skips an `unknown` tag; (6) CLOSES: an error during `abort` never replaces the encode error (it is chained); (7) not this package's (the clip transaction is WP3.13's `SafeWrite` and WP3.14's). **DR-28** -- PARTLY -- (4) the encoder is polled on every write and wait; (1) the full per-frame verification is the instrument's and question 6's; (2), (3), (5) are WP3.13/WP3.14's. **AD-12** -- IMPLEMENTS and VERIFIES (task 8); a different mapping is proposed to CHARC, never applied silently. **AD-23** -- consumed per question 2. WP3.13 consumer note (b) -- IMPLEMENTS -- "WP3.10 passes FFmpeg the TEMPORARY path with `-y` (the file already exists, empty), never the final path." WP3.7 note -- "on a non-identity edit list `mvhd` and the longest-stream duration may differ, and `mvhd` is the presentation form (D94)". |
| Done | Plan 4.5; frame section 2 rules 1-11; ruff check, ruff format --check, mypy strict, full pytest green (in a granted window); every MANDATORY and REQUIRED V4 item SAME on every WP2.3 sample, the synthetic offset, B-frame and 5.3K clips and GX011627; AD-12 verified or a proposal raised; the speed row recorded in an exclusive window; DR-17, DR-18 and DR-39 (a) closed; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table and the timing spike.** Before product code:
   - the pts carrier for raw frames entering FFmpeg (question 1), chosen by a scratch spike
     under `work/wp3.10/` that encodes `vid-vfr`, a clip with a non-zero start offset and an
     empty edit, and a B-frame clip (both built under `work/` with FFmpeg, as WP1.5's unit
     tests built theirs) and compares every MANDATORY item; no candidate exact on all three is a
     STOP with the figures (plan section 10 row 6: "Gaps in mandatory items | Encode-then-repair;
     WP3.10 grows | Architect");
   - the full encode command per encoder and bit depth, each option with its reason (from WP1.5
     section 4: `-copyts`, `-fps_mode passthrough`, `-enc_time_base:v`, `-video_track_timescale`,
     `+negative_cts_offsets`, `-tag:v hvc1`, `-c:a copy`, `-c:d copy`, `-write_tmcd 1`,
     `-map_metadata`; colour tags from `ffmpeg_color_names` on the stream AND the frames, as
     `clip.py` `setparams`; the display rotation set on the raw input, sign per AD-20 "IF-5
     `rotation` is counter-clockwise positive"; `-f mp4` per question 8; `-y` on `out_path`);
   - the stream map built from `ProbeResult.audio` / `.data` indices; what is regenerated (the
     timecode track) versus copied;
   - the edit-list forms FFmpeg reproduces (identity; an empty edit then identity; media_time
     equal to the reorder delay) and the rule for any other form (STOP, not a guess);
   - `write`'s checks, the thread layout, the polling rule, `close` and `abort` (questions 3, 6);
   - the provenance carrier (question 5) and the `SinkReport` contents;
   - the answers to the other questions.

   YIELD for the dispatcher. Anything the table cannot settle is a STOP.
2. **Capabilities (D74).** `hevc_nvenc` and `libx265`, each with `bit_depths` and a user-readable
   `reason` when unavailable (not listed by the build, the test encode fails, no NVIDIA device),
   detected per question 4 and cached for the process.
3. **`open`.** Refuses, before FFmpeg starts and naming the cause: a probe with a `"refuse"`
   fault; `encoder="auto"` or an unavailable encoder; a bit depth the encoder or D76 does not
   allow (`encode_pix_fmt` raises `ColorError`); a quality other than `high`/`standard`/`draft`;
   provenance with a non-string key (`check_string_keys`). Then starts one FFmpeg process writing
   `out_path` only (`-y`: the caller's `SafeWrite` temporary exists, empty).
4. **`write`.** Checks `frame.time_base == probe.video.time_base`, pts strictly increasing,
   shape `(height, width, 3)`, float32, `device == "cpu"` (question 14); quantises at the OUTPUT
   depth (`rgb_to_planes(np.ascontiguousarray(...), bit_depth=...)`, WP3.5 note: "the float frame
   is quantised at the OUTPUT depth"); sends the frame with its exact pts (question 1). The
   encoder process is polled on every write and every blocking wait (DR-28 (4)); a dead encoder
   raises with its stderr tail (ASCII-safe), never stalls.
5. **Colour (D55, D114, D54, DR-17).** Tags from the probe's resolved `ColorDescription`
   (`ffmpeg_color_names`); an `assumed` description is tagged with the assumed values and a
   `SinkReport.warnings` line says so; chroma 4:2:0 and pixel format per `encode_pix_fmt`; NVENC
   10-bit through `p010le` (WP3.5 note; AD-12 "10-bit by `-pix_fmt p010le` / `yuv420p10le`").
6. **Timing and mux (7.5, D94, D95, D105, AD-22).** Every output pts equals the written pts;
   start offset, video duration and first displayed frame equal the source's; the video edit
   list equal as written, or by presentation effect where only the composition-offset convention
   differs (AD-22); `mvhd` duration compared as the presentation form (WP3.7 note); audio
   packets byte-identical with their pts; audio sync; the display matrix; the `gpmd` track
   stream-copied packet for packet and never opened by Clearwater's code; the timecode track
   regenerated (WP1.5 section 4: "the MP4 muxer cannot copy it"); creation time kept. A
   truncated source per question 9.
7. **`close` and `abort`.** `close` ends the stream, waits for FFmpeg, runs the question-6
   verification, and returns `SinkReport(frames_written, warnings, not_carried)`, with
   `not_carried` listing each best-effort item absent from the output (WP1.5 section 6's
   classes; the `udta` atoms per question 10). `abort` (idempotent) stops FFmpeg, deletes
   `out_path` and nothing else, and leaves the original error intact (DR-20 (6)).
8. **Quality levels (AD-12, D75).** On GX011627 (busy) and one calm Snorkel clip, each level per
   encoder at 8 bits (and NVENC High at 10 bits): output bit rate against the camera's, PSNR to
   the source as a sanity figure (WP1.5: a one-frame shift reads 18 dB). Targets: "High ≈ the
   camera's bit rate on busy scenes, Standard ≈ half, Draft ≈ a quarter." A miss is reported
   with a proposed mapping to CHARC; the mapping is not changed in code without a ruling.
9. **The fidelity instrument `tools/video_fidelity.py` (V4, DR-18).** Source against output,
   every item classed MANDATORY / REQUIRED / BEST-EFFORT as WP1.5's `compare.py` (reuse by
   import where it fits; `src/` never imports `tools/`): the full pts sequence, frame count,
   durations, start offset in every form, edit lists as written and by effect, `mvhd`, audio
   packets AND the AAC decoder configuration, priming and side data (DR-18 (2)), audio sync,
   rotation, colour tags, pixel format, chroma, bit depth, size, the best-effort rows; a roster
   invariant so a missing item fails the summary (DR-18 (3)); frames with a missing pts counted
   (DR-18 (4)); the NVENC proof tied to the encode window, GPU UUID and FFmpeg PID, or the
   report says why not (DR-18 (1)). Records under `work/`; the committed report carries, for
   the `gpmd` track, only packet counts and SAME / DIFFERENT, no payload, digest or decoded
   value, and no location value from any tag.
10. **Speed row (EXCLUSIVE, best effort; question 11).** The dispatcher grants the window; do not
   start it unasked. `tools/video_io_bench.py`: WP3.9's `frames` straight into this sink (no
   correction), per-frame and min/min figures with the strays, clocks and temperatures recorded;
   peak process-tree RSS (FFmpeg children included) and graphics memory (N4). Send
   `WINDOW RELEASED: <summary>` at the end.
11. **Tests.**
   - Every decodable WP2.3 video sample encoded (8-bit and, where allowed, 10-bit; NVENC under
     `gpu`, libx265 always) and checked by the instrument: every MANDATORY and REQUIRED item
     SAME; `vid-vfr` pts exact (D115); `vid-rotated` keeps 90; `vid-untagged` tagged BT.709
     limited with the warning (DR-17); `vid-hevc10` stays 10-bit; `vid-hlg`/`vid-pq` refused at
     `open`.
   - Synthetic clips under `tmp_path`: a non-zero start offset with an empty edit; libx264 and
     libx265 B-frame sources (AD-22: pts, start offset, duration, first displayed frame exact;
     `media_time` may differ); a short 5.3K 8:7 clip (5.2 "including 5.3K and 8:7 modes",
     `slow`).
   - Transport: the bytes FFmpeg receives equal `rgb_to_planes` of the frames (a raw capture
     in place of the encoder), and their pts equal the written pts.
   - D76: 8-bit source to 10-bit output asserted within AD-11 on the RGB side (DR-39 (a)).
   - Refusals and failures: each `open` refusal by name; a planted encoder death mid-stream
     raises promptly; `abort` after a failure leaves no file and keeps the first error.
   - Safe-write composition: `plan_output` → `with SafeWrite(plan) as w: sink.open(...,
     w.temp_path, ...)` ... `sink.close(); w.commit()`; a failure inside leaves no partial and no
     final; the source byte-identical with its mtime unchanged (N8, 8.4).
   - Provenance present and parseable when given, absent when None.
   - A planted wrong implementation fails by name: CFR assumed on `vid-vfr`; start offset
     zeroed; `media_time` copied verbatim on the B-frame clip (AD-22 alternative); colour tags
     omitted on an untagged source; range written `tv` on a `pc` source; rotation dropped; audio
     re-encoded; 8-bit written for a 10-bit source.
   - `footage`: GX011627 through WP3.9's `frames` and this sink, NVENC 8-bit Standard, the
     instrument's summary all MANDATORY and REQUIRED SAME (as WP1.5 section 5's 41 items).
   - Static: no module names a GPS or IMU key or opens a `gpmd` packet; dependency rule (plan
     8.1, frame rule 5): importing `clearwater.io.video` loads nothing from `clearwater.gui`,
     `.jobs`, `.methods`, `.core`, `.analysis`, nor `PySide6`, `cupy`.

## Declared operating envelope

Windows 11; Python 3.12; FFmpeg 9.0.2 (gyan) with `hevc_nvenc` and `libx265`; the RTX 4070 Laptop
GPU (NVENC 8- and 10-bit, WP1.5 section 2); sources inside WP3.9's envelope (MP4/MOV, HEVC or
H.264, 4:2:0, 8/10-bit, BT.709 or BT.601) with at most the HERO13 track set (video, AAC, `tmcd`,
`gpmd`); edit lists of the forms in the round-0 table; the WP2.3 samples, synthetic clips under
`tmp_path`, GX011627 and GX011625; local NTFS or exFAT output; one export at a time. Out of
envelope: other FFmpeg builds, 4:2:2/4:4:4, fragmented MP4, multi-segment or rate-other-than-1
edit lists (a STOP if met inside the envelope), several video streams, network shares, other
operating systems (portable code, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\rN\`; ledger `docs/proofs/wp3.10-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.6\r1\`
  (`run_review.sh`, `review-prompt.md`; keep the round files as there); exclude `docs/proofs`
  with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - every MANDATORY V4 item measured on the output, not inferred from the command line; pts
    exact on VFR, offset and B-frame sources; AD-22's reading applied only where the
    composition-offset convention alone differs;
  - colour tags, range and pixel format per D55/D114; the D54 output tags (DR-17);
  - audio byte-identical, sync kept; rotation kept with the right sign;
  - process lifecycle: polling, no deadlock on stdin/stderr, `abort` idempotent, nothing written
    but `out_path`, `-y` never on a final name;
  - the instrument: no MANDATORY item silently missing; the four DR-18 points;
  - quality mapping and capability reasons; refusals named;
  - no `gpmd`, IMU or GPS data read; nothing in `interfaces/` or `color/` changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: table and spike, then YIELD before product code. After each review round:
  END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating; make NO change in
  the turn that adjudicates a round. Past ~250K tokens, "REVIEW ONLY this turn" when told. Report
  `uv run python scripts/cell_depth.py <your cell name>` at every yield (~250K evaluation point,
  ~400K STOP).
- **Windows (X5).** The full suite (about 3559 tests, about 15 min) runs ONLY in a window the
  dispatcher grants, in the background with `QT_QPA_PLATFORM=offscreen` and output under `work/`.
  The EXCLUSIVE speed window is a separate grant. Send `WINDOW RELEASED: <summary>` after each.
  Never two heavy jobs at once; 4K encodes outside a window are heavy: ask.
- **Return report** = your FINAL message, under about 70 lines, delivered to your dispatcher by
  your messaging tool: the public API, the command lines, the V4 table per sample, the AD-22
  evidence, the AD-12 table, the speed row, the DR dispositions, the gates, the Reviewer A
  rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or `src/clearwater/color/`;
  a MANDATORY or REQUIRED item you cannot meet (plan section 10 row 6); a pts carrier that is not
  exact; a dependency (PyAV is not adopted, AD-2); OS-specific code; an AD-12 change; any need
  to decode a `gpmd` packet or read a location tag; any write outside `out_path` and `work/`;
  the round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with
  `git -c core.autocrlf=false commit ...`, `feat(wp3.10): ...`, with a `Co-Authored-By:` footer
  naming your model. Never `git stash` (use a WIP commit or a scratch copy). Never a bare `cd`.
  Never post to a mailbox. Footage read-only at `C:\Users\rwsmy\clearwater-footage\`; every output
  under `work/`; no footage-derived output is committed. Gates: ruff check, ruff format --check,
  mypy strict, full pytest (in a window); no harness gate. Report
  `docs/reports/wp3.10-video-encode.md` (claims, evidence paths, limits, "Not carried").
  GoPro IMU and GPS are out of scope: no `gpmd`, IMU or GPS data is read; GPMF settings come only
  from the `moov/udta` GPMF atom (AD-16), which this package does not read.

## Questions for CHARC (recommended answer first)

1. **The pts carrier on the encode pipe.** Raw video on a pipe has no timestamps; the prototype
   gave FFmpeg a frame rate and so supports only CFR from 0. Recommended: the round-0 spike
   decides among (a) a minimal NUT stream written by a stdlib framer in `io.video` (rational
   time base, so `1/30000` ticks are exact), (b) another FFmpeg-native timestamped framing the
   spike finds exact, (c) raw frames at CFR with the timing restored in a second remux pass; the
   first exact on all three spike clips and GX011627 wins; none exact = STOP. Matroska's
   nanosecond scale is not exact at 1/30000 and is excluded.
2. **X-V1 (cross-brief, as WP3.9 question 1).** Recommended: the encoder's stdin uses the default
   pipe; no OS-specific code here; encode-side buffer tuning is WP3.21's.
3. **X-V2 (cross-brief, as WP3.9 question 2).** Each appends its own exports to
   `io/video/__init__.py`; the second to merge rebases. The encode error class
   (`VideoEncodeError(kind, message)`, mirroring `VideoProbeError`) lives in `encode.py`.
4. **`"auto"` and D74 detection.** Recommended: `open` refuses `"auto"`; a public
   `resolve_encoder(setting, capabilities)` in `capability.py` returns `hevc_nvenc` when
   available, else `libx265` (G12: "NVENC when available, else the software encoder; provenance
   records the encoder actually used"); detection = the build listing plus one tiny test encode
   per encoder and bit depth to the null muxer, cached per process, under ~2 s in total.
5. **Provenance in the MP4 (D91).** Spec 8.2/D91 say "embedded"; the architecture's data flow
   line "provenance sidecar (D90, IF-9)" disagrees, and the spec wins. Recommended: one
   container tag the MP4 muxer writes without `use_metadata_tags` (the `comment` key), holding
   the AD-13 object as JSON (`allow_nan=False`, after `check_string_keys`); absent when
   `provenance` is None; the round-0 spike confirms it survives and leaves creation time intact.
6. **"Verified" (D94).** Recommended: `close` re-reads the finished output with ffprobe (bounded
   intervals only) and checks the MANDATORY items against the probe and the pts written (count,
   every pts, start offset, video edit list, rotation, audio packet count); a mismatch raises,
   so the caller's `SafeWrite` deletes the temporary. The full instrument stays a tool.
7. **AD-22 without an iPhone clip.** AD-22: "WP3.10 proves it on an iPhone clip"; the inventory
   holds none. Recommended: prove it on libx264 and libx265 B-frame clips built under `tmp_path`
   and on `Edits/compilation-20261010-1080p60.mp4` (H.264, read-only) if round 0 finds a
   non-zero video `media_time` in it; the iPhone leg waits for an owner clip (a WP3.6P-style
   follow-on), DR-15 stays OPEN for that leg only.
8. **Output container for a `.MOV` source.** WP3.13 keeps the source extension. Recommended:
   always `-f mp4` (8.2 "MP4, HEVC"), so an iPhone `.MOV` gives MP4 bytes under a `.MOV` name.
9. **A truncated source (D86).** Recommended: the copied audio and `gpmd` packets are cut at the
   end of the last written video frame (the output stays in sync; "unchanged" holds for every
   packet kept), with a `SinkReport.warnings` line.
10. **The camera's `udta` atoms.** The architecture allows "best-effort `udta` repair as a second
    box-level pass if cheap (debt otherwise)". Recommended: not attempted here; listed in
    `not_carried`; a new DR records the repair as a later option.
11. **The speed row.** Frame section 5 gives the V16 end-to-end row to WP3.14. Recommended: this
    row is the I/O floor (decode plus encode, no correction): GX011627 full clip x 3 and GX011625
    full clip x 1 with NVENC 8-bit Standard; one GX011627 run each with libx265 and NVENC 10-bit
    (D76); AD-12's encodes in the same window; memory peaks recorded.
12. **Waiting for WP3.9.** Recommended: tasks 1-9 and the synthetic tests proceed in parallel;
    the footage legs, AD-12 and the speed row wait for WP3.9's accept, then the branch rebases on
    main; if WP3.9 has not merged when they are reached, YIELD.
13. **`QUALITY_RATIO`** (`clearwater.jobs.disk_space`, "PROVISIONAL until WP3.10") is WP3.13's
    file. Recommended: the report states the measured ratios; the orchestrator or WP3.14 updates
    the constant.
14. **A frame on the GPU.** Recommended: `write` refuses `device != "cpu"` by name; the caller
    calls `backend.to_host` first (as WP3.6 question 9).
15. **DR-26.** Recommended: grant the narrow fix in `tools/container_spike/spike.py` (`_chapter`
    and the `camera` default resolve through `find_footage_file`) so DR-26 closes here, since
    the instrument reuses `compare.py`.
16. **The `gpmd` track in the output.** Spec 8.2 lists the "GPMF telemetry track" as best-effort
    and IF-5 `write` says the sink preserves `gpmd`. Recommended: stream-copied as WP1.5 did,
    never opened by Clearwater's code; compared in memory only; nothing from it committed.
17. **BT.601 sources.** WP3.5 note: primaries `smpte170m` resolve as "unexpected", so the
    output is tagged with BT.709 primaries (IF-1 has no BT.601 primaries value). Recommended:
    accept and document (out of envelope for GoPro and iPhone footage); no interface change.
