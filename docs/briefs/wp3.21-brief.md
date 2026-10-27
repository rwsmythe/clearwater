# WP3.21 — Optimisation package (dispatch brief, FINAL)

**Status:** FINAL 2026-10-27 (CHARC `b16da9c25ddfb8c8`, rulings below, which take precedence over the text
above them); DRAFT `84b793c` written by a drafting helper for the
orchestrator from CHARC's rulings of 2026-10-27 (the V16 baseline, the first question, D106's
list, the re-measure, visual equality, the lane). Base = the main commit named at
dispatch (drafted on `0228bcd`). Owner decisions: none inside the package (an output change
beyond the tolerance below, or relaxing D106, is owner-reserved: a STOP, never done here).
- Spec **v0.5.5**: D106, D31, D68, D69, D92, D107, D109 (reserve, out of scope), D110, D111;
  N3, N4, N6 (interim per D106; the body text is DR-64's owner erratum, not this package's),
  N10; V4, V8, V9, V15, V16; section 10.2, section 11. Architecture FINAL 1.0: section 1, 2
  ("video analysis", "video export (jobs)"), 3 (IF-1, IF-2, IF-3, IF-5, IF-7, IF-8), 4
  ("Performance"), 5. AD-1, AD-2, AD-5, AD-7, AD-11, AD-15, AD-20, AD-21, AD-23, AD-28.
- Plan row WP3.21 (section 6, size M, depends on WP3.4, WP3.9, WP3.10, WP3.14; spec "D106, N6;
  gate report Result 1"; feeds "V16 (re-run at WP5.2)").
- Reports: WP1.6 gate Result 1 and 2; WP1.2A section 6 note and section 7; WP1.2B section 10
  (claim 7, the candidate table); WP3.4 "Speed row", "Consumer notes" (WP3.21 item); WP3.9 "What
  it does"; WP3.10 sections 3, 7.3, 9; WP3.11 "Threading model", claim 7, "Limits"; WP3.14
  "Phases and threads", "Cancel path", "Limits", "V16" (the baseline).
- Cell: `implementer-opus-high` (reasoning-dense; touches the backend). Tier **STRONG**, Claude
  lane: Reviewer A (your loop) and Reviewer B (the orchestrator's seat) are Codex at the pin
  `gpt-6.1-sol` / high.
- Worktree `.worktrees/wp3.21`, branch `wp3.21` from main, base = the main commit named at dispatch.

**Why.** Gate 1 option C (owner, 2026-10-20; AD-21): an interim 25 min/min at 4K now, and "a
named Phase 3 optimisation package (device-resident pipeline, upload/download overlap, FFT or
recursive Gaussian for 3C ...) targets about 10 min/min and the figure is re-set from the WP5.2
re-measure" (D106). WP3.14's V16 rows MISS the interim on cold c3 at 4K (31.3-31.9 min/min);
CHARC ruled the miss "WP3.21 DATA, not a stop, not a defect". This package makes the export
faster without changing what it outputs.

| Field | Content |
|---|---|
| ID and title | WP3.21 — Optimisation package; plan section 6 Phase 3 row WP3.21 |
| Goal | Find where the cold export spends its time (the analysis pass first), then apply D106's list in the order of measured gain, so that cold c3 at 4K meets D106's interim 25 min/min (0.834 s/frame at 30000/1001) end to end, aiming at about 10 min/min (0.334 s/frame); every output equal to the pre-optimisation engine's within the tolerance of question 3; the V16 rows re-measured before against after in EXCLUSIVE windows. |
| Spec / decision clauses | D106 "interim, about 25 minutes of processing per minute of 4K footage on the owner's laptop ... end to end; a named Phase 3 optimisation package (device-resident pipeline, upload/download overlap, FFT or recursive Gaussian for 3C; the large-buffer transport is already in the build) targets about 10 min/min and the figure is re-set from the WP5.2 re-measure ... 5.3K is supported but best-effort on speed". V16 "export meets the N6 target at 4K in the owner's recording modes (interim 25 min/min per D106; re-set after the Phase 3 optimisation package at WP5.2)". N4 "peak RAM ≤ 16 GB, for video (including 5.3K 8:7)"; "graphics memory is measured and treated as a second limit"; "frame parallelism and buffering are bounded to meet these limits". N3/D107 "the same code runs on CPU or GPU". N10/D92 "same inputs and parameters give output identical within a defined tolerance"; AD-11 "the same device ... bit-identical output pre-encode; CPU vs GPU within 2e-3 absolute per channel ... max, 2e-4 mean". AD-7 "Export waits for the whole clip's recompute" (question 2). D109 "Sparse analysis ... is held in reserve" (out of scope). |
| Baseline (cited, not re-derived) | WP3.14 report "V16", `tools/export_bench.py v16` on `2e1dc11`, c3 defaults, encoder auto (NVENC), Standard, 8-bit: GX011627 c3 cold **1.061-1.065 s/frame (31.8-31.9 min/min)**; GX011625 c3 cold, sustained, **1.043 (31.26)**; GX011627 c3 warm **0.774 (23.2)**; ancuti2018 cold **0.720 (21.6)**; c3 libx265 cold 35.6 (the fallback path, not a target); synthetic 5.3K 8:7 c3 cold 136 min/min, 6.2 GiB tree RSS / 6.0 GiB graphics memory peak, first frame 10.6 s (best effort). Split: the analysis pass is about 30 % of the wall time (~0.31 s/frame: GX011627 about 220 s for 681 frames, GX011625 4,638 s for 14,938); the frame path about 0.74 s/frame. Beside it: WP3.4's c3 core 0.439 s/frame (render 0.410), WP3.10's I/O floor 0.154-0.156 s/frame (decode plus NVENC encode, no correction). Evidence: through GX011625's 77-minute analysis phase the GPU sat at idle clocks (median SM 210 MHz, 5.1 W, 59 C), so the pass is not GPU-bound. |
| Depends on | On main: WP3.14 (accept `ba6e923`: `ExportEngine`, `tools/export_bench.py`), WP3.11 (`47235b6`: `AnalysisEngine`), WP3.10 (`47bc6d6`: the sink, `tools/video_io_bench.py`, `tools/video_fidelity.py`), WP3.9 (`09ab408`: `FFmpegVideoSource`), WP3.4 (`ad15ab4`: the methods, `tools/core_speed.py`), WP3.1 (`clearwater.core`), WP3.12 (`DiskProxyCache`). Nothing unmerged. |
| Files owned (question 1: proposed grants) | NEW: `tools/analysis_breakdown.py` (task 1; name per round 0) and `tools/export_oracle.py` (task 2) with `tests/test_analysis_breakdown.py`, `tests/test_export_oracle.py`; `tests/test_wp321_*.py`; `docs/reports/wp3.21-optimisation.md`; `docs/proofs/wp3.21-ledger.md`. EDIT, granted per question 1: `src/clearwater/analysis/engine.py` (WP3.11), `src/clearwater/analysis/proxy.py` (WP3.11; a device proxy path only if bit-identical), `src/clearwater/jobs/export.py` (WP3.14), `src/clearwater/core/backend.py` (WP3.1; `gaussian_blur`, question 4), `tools/export_bench.py` (WP3.14; an output-folder option and the stamps the overlap needs, question 7). EDIT only if the round-0 table names the need and the dispatcher grants it: `src/clearwater/io/video/decode.py` (WP3.9), `src/clearwater/io/video/encode.py` (WP3.10; then DR-63 rides along), `src/clearwater/color/samples.py` (WP3.5), `src/clearwater/core/ops.py`, `src/clearwater/core/memory.py` (AD-1's estimate: a CHARC ruling, question 9). NOT owned: `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN), `jobs/export_seam.py`, `naming.py`, `safe_write.py`, `disk_space.py`, `methods/`, `cache/`, `config/`, `gui/`; `tools/video_io_bench.py`, `tools/video_fidelity.py`, `tools/core_speed.py` (imported, not edited); `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/fixtures/`; every existing test file (question 4); `pyproject.toml`, `uv.lock`. |
| Interfaces provided | None new. `ExportEngine`, `AnalysisEngine`, the `ArrayBackend` implementations and the sink keep their public behaviour; any change in a public signature is named in the round-0 table. No frozen interface changes. |
| Interfaces consumed | IF-1 `Frame` (`device` may be `"cuda:0"`), IF-2 `ArrayBackend` (`gaussian_blur`: "symmetric borders, 4-sigma truncation"; `asarray`, `to_host`, `memory_estimate_bytes`), IF-3, IF-4, IF-5 `VideoSource`/`VideoSink`, IF-7, IF-8 `Progress`/`JobResult`, IF-10 `Settings`; the WP3.19 seam names from `clearwater.jobs.export_seam`. |
| Consumers | WP4.3 (wires the engine), WP4.1 (headless runner), WP5.2 (V15, V16 re-measure; N6 set there, AD-21). |
| Hardware flags | **EXCLUSIVE** on task 1 (the breakdown), every interim timing, and task 10 (the re-measure, LAST): plan 4.3 "Timings are taken on a full clip, not one frame"; one heavy job at a time; at least 5 GB free memory before a run; a figure from an ungranted or a parallel-worker run is not a figure of record (AD-28). `gpu`, `footage` (GX011627, GX011625 read-only through `tools/local_config.find_footage_file`; outputs under `work/` only), `slow` as WP3.14. Task 2's reference run is heavy (a 4K export): a granted window. |
| Out of scope | D109 sparse analysis and any change to what the statistics are (proxy size, codec, quality, smoothing kind or window: AD-3, AD-5); AD-12's encoder mapping or presets (they change the output); N6's final figure (WP5.2) and the spec text (DR-64, owner); a recursive Gaussian that departs from IF-2's truncated kernel beyond question 3's bound; the GUI and the preview path's own scheduling (WP4.3); libx265 speed; 5.3K speed beyond recording it; chapter handling (v2); any change in `src/clearwater/interfaces/`; decoding, parsing or logging any `gpmd` packet, IMU or GPS data; reading or logging any location tag. |
| Debt and decided items | **WP3.11 style debt** (CHARC at the WP3.14 gate): the in-block `import logging` in `analysis/engine.py`'s decode-pass `finally` (line ~500, "here: this block is the module's one granted edit (WP3.14)") moves to the module header with a module logger; CLOSES at this touch. **DR-63** (`encode.py` `close` sets `"closed"` unconditionally): CLOSES only if this package touches `encode.py` ("`close` sets `"closed"` only from `"open"` ... and `abort`'s docstring names the window"); else not this package's. **DR-40 (b)** (per-call constant uploads, 0.2 % of the c3 core as measured by WP3.4): question 8. **DR-62** (GUI recompute vs export): not this package's (WP4.3), but the overlap must not widen it (one writer per cache key). **DR-47**: not reached (one engine per job, one writer). **DR-45 (a)**: must not be reached: every `FrameStream` is iterated and closed by one thread only. **DR-64**: not this package's. |
| Done | Plan 4.5; frame section 2 rules; ruff check, ruff format --check, mypy strict, the full suite per the fill's GATE_CHECKS at dispatch green (in a granted window), with every existing test unchanged or changed only by a CHARC ruling (question 4); the equality oracle passes on every leg (task 2, question 3); V4 SAME on the WP2.3 samples and GX011627 through the optimised engine; N4 held (the 5.3K row); the re-measure recorded before against after in EXCLUSIVE windows; cold c3 at 4K at or under 25 min/min on GX011627 and GX011625, or question 5's path taken; Reviewer A converged. |

## Task ladder

1. **The first question: where does the cold analysis pass spend its ~0.31 s/frame?** Before any
   device-resident work. Build the breakdown instrument (question 6) and run it in an EXCLUSIVE
   window on GX011627 (full clip, c3 defaults, the job's backend and `hw_decode` as
   `jobs/export.py` sets them). Time, per frame, every step of `AnalysisEngine._decode` as the
   product runs it: the wait for the decoder's next frame (decode, the hardware download, the
   pipe), `planes_to_rgb` (host float32), `frame_pixels_on_host`, `make_proxy` (`block_mean` in
   float64 on the host: WP3.11 "Limits" "The proxy block mean of a 4K frame runs on the host
   (Q9; no timing in this package)"), `quantise`, `store_proxy` (JPEG q75 4:4:4 encode and the
   write, AD-5), `proxy` (read back and decode), the upload, stage-1 `analyze`, the store puts,
   the Python loop; then the later stages and smoothing. In the same window, the same breakdown
   for the frame path (decode wait, upload, `render`, `to_host`, `rgb_to_planes`, the pipe
   write), since its 0.74 s/frame exceeds the core (0.439) plus the floor (0.155).
   CHECK: the per-step medians sum to the instrument's own per-frame wall time within 5 %; the
   replica's statistics equal the engine's bit for bit (it measures the product, not a copy);
   the GPU-idle observation is explained by a named step. The figures go in the ledger and the
   report; they ORDER tasks 4-6.
2. **The equality reference, on the base, before any product change** (question 3). With
   `tools/export_oracle.py`, on unchanged code: for each oracle clip (WP2.3 `vid-hevc8-bt709-full`,
   `vid-hevc10`, `vid-vfr`, `vid-rotated`, `vid-truncated`; a synthetic 4K clip under `tmp_path`;
   GX011627 c3 and ancuti2018), record a SHA-256 digest of every pre-encode frame the sink
   receives, the smoothed record of every stage at every pts, the cache entry's proxy bytes, and
   the full float32 pre-encode frames at one frame per second (GX011627: 23 frames, about 2.3 GB)
   and every frame of the short clips, under `work/wp3.21/oracle/` (nothing committed). Then
   a CONTROL: the base run twice gives identical digests (N10 on this device). CHECK: the
   control holds; if it does not, STOP with the differing frames (the oracle's tier 1 is void).
3. **Round 0 yield: the design table.** In the ledger, before product code: the breakdown's
   table; the candidates in the order of measured gain, each with its expected saving, its
   oracle tier (question 3), the modules and grants it needs and the tests that pin it; the
   overlap design (question 2: the lead, threads, queues and their bounds, cancel and failure
   paths, the one writer per cache key, which thread iterates and closes each stream); the
   memory budget against N4 and AD-1's estimate (question 9); the 3C Gaussian route (question
   4); the test list; every existing test the plan would change, with its reason; the
   `scripts/cell_depth.py` figure your dispatcher gives you. YIELD. A choice the brief leaves
   open is a STOP.
4. **Overlap the analysis with the export** (default first: the figures say it could recover most
   of the 30 %; warm c3 at 0.774 s/frame is the export without it). Within one job, render frame
   i once its smoothed record is FINAL for every stage, the analysis running ahead by at least
   the staged reach (WP3.11 claim 7: c3 stage 1 ±60 and stage 2 ±30 frames at 29.97 fps; reach
   is over pts, so VFR holds). Every frame still renders with exactly the record the
   whole-clip analysis gives (`smooth_at` over chunks equals `smooth`, WP3.11 claim 9).
   Unchanged: the cache entry is marked complete only after the whole pass (V17); a cancel
   anywhere returns `CANCELLED` with nothing on disk; a failure in either half fails the job
   with the original error's text; the watchdog, `close`, the post-close check and `commit`
   keep WP3.14's order. Bounded queues (N4); the CPU backend runs the same code (D107).
   CHECK: oracle tier 1 (bit-identical digests and records) on every clip; WP3.14's cancel,
   failure, D87 and V11 tests pass unchanged; a planted "render before final" fails by name.
5. **Device-resident frame path and upload/download overlap** (as task 1 ranks them): move
   host conversions and copies off the critical path (for example the 8/10-bit planes uploaded
   and converted on the device, the output converted to planes on the device, copies on their
   own CUDA stream with the next frame's upload and the last frame's download overlapping the
   render), and the analysis pass's host work where task 1 finds it (a device block mean only
   if bit-identical: the uint8 proxy must equal today's byte for byte, or V17, V8 and
   `gui.imaging.downscale`'s equality break). IF-1 permits a `Frame` on `"cuda:0"`; the sink's
   rule "`write` refuses `device != "cpu"`" (WP3.10 Q14) changes only with the `encode.py` grant.
   CHECK: tier 1 where the arithmetic is unchanged; tier 2 where a conversion moves device;
   the CPU fallback (`force_cpu`, D111) gives the base's output; frames still in pts order.
6. **The 3C Gaussian** (question 4): an FFT (or overlap-add) convolution with the SAME truncated
   kernel (radius `int(4 * sigma + 0.5)`) and symmetric padding, used above a sigma threshold
   set in round 0, through `cupyx.scipy.fft` / `scipy.fft` (no new dependency), both backends.
   CHECK: against the current `gaussian_blur` on real 4K frames, 5.3K and synthetic step edges
   at every border, within question 3's filter bound; the end-to-end oracle within tier 2;
   deterministic on repeat; the memory peak re-read (question 9).
7. **Debt at the touch.** The `import logging` move (`engine.py`); DR-63 if `encode.py` is
   touched; DR-40 (b) per question 8.
8. **Tests.** Every existing test passes unchanged (or as ruled, question 4). New: the oracle
   legs as `footage`/`gpu`/`slow` tests reading the task-2 reference (skipped without it); the
   overlap's lead, bound and order (a planted short lead, an unbounded queue and an out-of-order
   render each fail by name); cancel at each phase of the overlapped job (before start, during
   the lead, mid-encode with a write blocked until `abort`, immediately before `commit`); a
   failure injected in the analysis half mid-export; the CPU path; the Gaussian bound; the
   breakdown and oracle tools (dry runs, record shape, refusal of a footage-folder output).
   Static: `clearwater.jobs` still loads no `clearwater.gui`, `clearwater.methods`, PySide6 or
   CuPy at import (WP3.13's test, run, not changed); no module opens a `gpmd` packet.
9. **Review loop** (below), then the full suite in a granted window.
10. **The re-measure (EXCLUSIVE, LAST, best effort; question 7).** The dispatcher grants each
    window after every other task, the review loop and the full suite; do not start it unasked.
    `tools/export_bench.py v16` on the final commit, the same `V16_PLAN` legs and conditions as
    the baseline (GX011627 rows first, GX011625 LAST, each block its own OPEN/CLOSE), records
    under `work/wp3.21/bench/`, nothing footage-derived committed. The report's table puts every
    row beside its baseline row (s/frame, min/min against 25 and 10, per-frame median / p90 /
    max, analysis share or overlap stamps, peak tree RSS, peak graphics memory, the NVENC proof,
    clocks, temperatures, strays). Send `WINDOW RELEASED: <summary>` at the end of each window.

## Declared operating envelope

Windows 11; Python 3.12; FFmpeg 9.0.2 (gyan) with `hevc_nvenc` and `libx265`; the RTX 4070 Laptop
GPU (8 GB) or the CPU fallback; the Ryzen 9 7940HS (8C/16T), 32 GB RAM; video inside WP3.9's and
WP3.10's envelopes; the owner's recording mode (3840x2160 at 29.97, HEVC 8-bit 4:2:0) for the
figures of record, 5.3K 8:7 for memory; ONE export job at a time, one writer per cache key; the
host otherwise idle in an EXCLUSIVE window (best effort; strays recorded, contaminated rows kept as
spread). Out of envelope: several concurrent jobs, a second GPU, a GUI recompute of the same clip
during its export (DR-62), other operating systems (portable code, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (Codex `-m gpt-6.1-sol -c model_reasoning_effort=high`, WSL transport, probe
  first), run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.21\rN\`; ledger `docs/proofs/wp3.21-ledger.md`.
  Copy the runner and prompt shape from WP3.14's last round folder (`...\wp3.14\r2\`); the banner
  must read `gpt-6.1-sol` (a round whose banner reads another pin is void); exclude
  `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - equality: every path that renders, converts or measures gives the base's output within its
    tier; no frame renders before its record is final; the proxy bytes unchanged;
  - concurrency: queue bounds, thread ownership of each stream, one cache writer, the GIL and
    CUDA stream synchronisation (a download read before its copy completes), shutdown on every
    path;
  - cancel and failure: WP3.14's guarantees on every phase of the overlapped job; no orphaned
    FFmpeg process or thread;
  - memory: N4 bounds by construction; AD-1's estimate still at or above the measured peak;
  - the CPU path (D107) and the Gaussian bound at every border;
  - nothing in `interfaces/`, the seam or unowned files changed; no `gpmd`, IMU or GPS data read.
- Reviewer B is the orchestrator's seat pass on the merge candidate (Codex, the same pin).

## Notes for the cell

- **Yields.** Task 3 (round 0): the table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating; make NO
  change in the turn that adjudicates a round. Your dispatcher gives you the
  `scripts/cell_depth.py` figure at every yield: put it in the ledger; ~250K is the evaluation
  point ("REVIEW ONLY this turn" when told), ~400K STOP.
- **Windows (X5, AD-28).** Heavy work runs ONLY in a window the dispatcher grants: the breakdown,
  every interim timing, the oracle reference and its legs, footage tests, the full suite, the
  re-measure. Ask for each; one heavy job at a time; at least 5 GB free before a run. The suite
  runs in the background with `QT_QPA_PLATFORM=offscreen`, output under `work/`, with foreground
  poll-wait calls on its done marker (a reaped run is not a result). Timing and memory figures
  come only from serial runs. Send `WINDOW RELEASED: <summary>` after each.
- **Return report** = your FINAL message, under about 70 lines, to your dispatcher by your
  messaging tool: the breakdown table; what was applied in which order with each step's measured
  gain; the oracle results per clip and tier; the re-measure beside the baseline; N4 peaks; the
  DR dispositions; the gates; the Reviewer A rounds and verdict; open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20), the seam, or a file
  not owned or granted; an output outside question 3's tolerance (owner-reserved if visible); a
  change to what the statistics are (D109, AD-3, AD-5); a dependency; OS-specific code beyond
  AD-23; AD-1's estimate below a measured peak; the base control of task 2 failing; any need to
  decode a `gpmd` packet or read a location tag; any write outside `work/` and the planned
  temporary; the round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with `git -c
  core.autocrlf=false commit -m "perf(wp3.21): ..." -- <paths>`, with a `Co-Authored-By:` footer
  naming your model; every committed blob LF. Never `git stash`. Never a bare `cd`. Never post
  to a mailbox. Footage read-only at `C:\Users\rwsmy\clearwater-footage\`; every output under
  `work/`. Gates: ruff check, ruff format --check, mypy strict, full suite (in a window); no
  harness gate. Report `docs/reports/wp3.21-optimisation.md` (claims, evidence paths, limits,
  the baseline beside the result).

## Questions for CHARC (recommended answer first)

1. **Ownership grants.** Recommended: grant now the EDITs of `analysis/engine.py`,
   `analysis/proxy.py`, `jobs/export.py`, `core/backend.py` and `tools/export_bench.py` (each
   module's origin package is accepted; no interface changes); grant `io/video/decode.py`,
   `io/video/encode.py`, `color/samples.py`, `core/ops.py` at round 0 only if task 1's figures
   need them, the dispatcher deciding from the table; `core/memory.py` only by CHARC (question 9).
   Alternative: grant all now (wider review surface, fewer yields).
2. **Overlap and AD-7 ("Export waits for the whole clip's recompute").** Recommended: an
   AD-7 READING recorded by CHARC: inside an export job, "waits" means every exported frame
   renders with its FINAL smoothed record (the one the whole-clip analysis gives, bit for bit),
   so the job may render frame i once the analysis has passed i plus the staged reach; AD-15
   (the GUI's export button disabled during analysis) is unchanged. Two decoders (the analysis
   ahead, the export behind; NVDEC and the decode floor of 13-16 ms/frame make a second stream
   cheap) rather than one decode feeding a ring of 4K frames (about 25 MB each as 8-bit planes;
   a 60-frame lead holds about 1.5 GB). Alternative: no reading; overlap only the analysis's
   host work with its own decode (smaller gain).
3. **The equality oracle and its tolerance** (D92, N10, AD-11). Recommended: two tiers against
   the base's recorded reference (task 2), pre-encode, on the same device. **Tier 1,
   bit-identical** digests, statistics records and proxy bytes, for every change that keeps the
   arithmetic (overlap, threading, queues, copies, stream order). **Tier 2, AD-11's CPU-vs-GPU
   bound** (max 2e-3 absolute per channel, mean 2e-4), for a change that alters the arithmetic
   (a conversion moved to the device, the FFT Gaussian), with the statistics records unchanged
   unless the change reaches the analysis path (then within AD-5's 1e-3 relative on means and
   gains). The Gaussian alone: max abs 1e-5 against the current filter on [0, 1] data (about
   1/400 of an 8-bit level; a PROPOSED figure, not measured). No owner look check inside tier 2:
   AD-11 already treats outputs within it as the same output (half an 8-bit level, under the
   encoder's quantisation). Outside tier 2 is a STOP: a visible change is owner-reserved. After
   encode: V4 SAME through `tools/video_fidelity.py`. Alternative: a PSNR criterion on decoded
   outputs (weaker; the encoder masks small errors).
4. **The 3C Gaussian route.** IF-2 states `gaussian_blur` as "symmetric borders, 4-sigma
   truncation". Recommended: FFT or overlap-add of the SAME truncated kernel with symmetric
   padding (the contract kept, the result equal to rounding), above a sigma threshold chosen in
   round 0 so that the product-against-prototype bit-for-bit tests (`test_methods_compensation.py`,
   `test_core_prototype.py` and the like) stay unchanged where they can; any test that must move
   to a tolerance is listed in the round-0 table for a ruling, never edited silently. A recursive
   (IIR) Gaussian approximates an untruncated kernel with other borders: excluded unless it meets
   tier 2, and then an IF-2 reading by CHARC. Alternative: allow the IIR route now (faster,
   larger error, an AD-20 matter).
5. **If cold c3 still misses 25 min/min after the ladder.** Recommended: the cell YIELDs with the
   measured figures and the next candidates (WP1.2B #2 fewer materialised intermediates, the
   residual of the frame path); CHARC chooses between a follow-on package and recording the
   figure for WP5.2, where D106 says N6 is re-set; relaxing D106 is the owner's. D109's sparse
   analysis is not a fallback here (it changes the statistics: owner). Missing the ~10 min/min
   aim is not a failure: it is a target, recorded with the figure. Alternative: the package
   cannot accept until the interim is met.
6. **The breakdown instrument.** WP3.14 Q11 ruled "never from product-code timers".
   Recommended: `tools/analysis_breakdown.py` drives the product functions in the decode pass's
   order with its own clock around each call (as `tools/core_speed.py` does for the core) and
   checks its records equal the engine's; plus one stdlib `cProfile` run of the real
   `analysis_job()` as a cross-check (overhead noted, not a figure of record). No product timers;
   no dependency. Alternative: a timing hook injected into `AnalysisEngine` (product surface).
7. **The re-measure set.** Recommended: the whole `V16_PLAN` as the baseline ran it (GX011627
   cold x3, warm, ancuti2018, libx265; synthetic 5.3K; GX011625 sustained), so every row has its
   before and the 5.3K row re-checks N4 under the overlap; `tools/export_bench.py` gains an
   output-folder option (default unchanged, `wp3.14/bench`) so records land under
   `work/wp3.21/bench/`. The baseline took about 84 min (block 1) and 260 min (block 2).
   Alternative: the c3 cold rows and 5.3K only (about 3 h shorter if GX011625 is dropped; but
   the plan row names GX011625).
8. **DR-40 (b)** (constant uploads per render call). Recommended: not this package's code
   (`methods/` is not owned; WP3.4 measured 0.75 ms per c3 frame, 0.2 % of the core); CHARC
   records the row as measured-negligible or keeps it OPEN. Alternative: grant
   `methods/compensation.py` and `white_balance.py` for a cached-constant fix.
9. **Memory under the overlap and the FFT** (N4, AD-1, D111). Two decoders, a lead and FFT
   buffers raise the peaks. Recommended: the round-0 table budgets them; the 5.3K and 4K rows
   re-measure them; `memory_estimate_bytes` (AD-1: "1.16x the pool's reserved peak at 4K") must
   stay at or above the measured reserved peak, and a change to its formula is a CHARC ruling
   (STOP to ask), so D111's CPU switch keeps its meaning. Alternative: no FFT above 4K (5.3K
   stays on the direct filter).
10. **Interim timings during the build.** Recommended: each candidate's gain is measured on
    GX011627 cold c3 (one run, about 12 min) in a short EXCLUSIVE window the dispatcher grants,
    so the order of tasks 4-6 follows figures; these rows are development evidence, the task-10
    rows are the figures of record. Alternative: measure only at task 10 (no evidence for the
    order).

## Rulings (CHARC `b16da9c25ddfb8c8`, 2026-10-27, verbatim; FINAL)

AD-7 reading and the oracle recorded in `docs/decisions.md` (`1cd46fd`).

**Q1 grants: RECOMMENDED.** Now: `analysis/engine.py`, `analysis/proxy.py`, `jobs/export.py`, `core/backend.py`, `tools/export_bench.py`. At round 0 from the table, dispatcher's grant: `io/video/decode.py`, `io/video/encode.py` (DR-63 then CLOSES in the same touch, mandatory), `color/samples.py`, `core/ops.py`. `core/memory.py` only by my ruling (Q9). `methods/` not owned (Q8).

**Q2 AD-7 READING: YES, recorded.** Inside an export job, "export waits for the whole clip's recompute" means every exported frame renders with its FINAL smoothed record, bit for bit the record the whole-clip analysis gives; the job may render frame i once the analysis is final for i. AD-15 (the GUI's export disabled until analysis completes) is unchanged; the reading is for the job's own pass, not for the GUI. Two decoders, each iterated and closed by ONE thread (DR-45 (a)), rather than a frame ring. Two conditions: (a) **the lead is the COMPOSED reach over the stage dependency chain**, not the larger of the two: where stage 2's raw input depends on stage 1's SMOOTHED value, frame i's stage-2 record is final only when stage 1 is final out to i + reach2, i.e. raw stage-1 statistics present to i + reach1 + reach2 (c3: 90 frames at 29.97, over pts so VFR holds); the round-0 table derives the lead from `depends_on_parameters` / the stage graph and the planted "render before final" test plants a lead short by ONE frame at the composed bound; (b) the cache entry's `mark_complete` stays after the whole pass (V17) and the export half never writes the cache (one writer per key, DR-62 not widened).

**Q3 oracle: RECOMMENDED with one tightening.** Tier 1 (bit-identical digests, records, proxy bytes) for every change that keeps the arithmetic; tier 2 (AD-11: max 2e-3 absolute per channel, mean 2e-4, pre-encode, same device) for a change that alters the render arithmetic. **Tightening: the statistics records (raw AND smoothed) and the proxy bytes are tier 1 ALWAYS.** The analysis cache is shared with the GUI (V8, V17, `downscale` equality) and with every later export; a device block mean or any analysis-path change is admitted only bit-identical, otherwise it is a STOP, never a tolerance. The brief's "unless the change reaches the analysis path (then within AD-5's 1e-3)" is struck. **Gaussian bound CONFIRMED: max abs 1e-5 against the current filter on [0, 1] float32 data** (1/400 of an 8-bit level; the float32 FFT of a 4K plane carries roundoff of order 1e-6, so this is a ceiling, not a target); measured in round 0 on 4K frames, 5.3K and step edges at every border, reported as the figure, a measured exceedance is a round-0 STOP with the figure. No owner look check inside tier 2 (AD-11 treats it as the same output); outside tier 2 a STOP (owner-reserved). After encode V4 SAME through `tools/video_fidelity.py`. Helper flag: the 1 fps float-frame sample (23 frames, ~2.3 GB under `work/`, nothing committed) CONFIRMED; disk has room.

**Q4 Gaussian route: RECOMMENDED.** FFT or overlap-add of the SAME truncated kernel (radius `int(4 sigma + 0.5)`) with padding that reproduces scipy's `mode="reflect"` exactly (edge pixel duplicated: d c b a | a b c d | d c b a), both backends, float32 only (no float64 FFT), above a sigma threshold set in round 0 so the product-against-prototype bit-for-bit tests stay unchanged where they can; any test that must move to a tolerance is in the round-0 table for my ruling, never edited. IIR EXCLUDED this package (an IF-2 reading would be mine, and it is not needed to meet 25).

**Q5 if cold c3 still misses 25: RECOMMENDED.** The cell YIELDs with the figures and the next candidates; I choose between a follow-on package and recording the figure for WP5.2 (where D106 says N6 is re-set); relaxing D106 is the owner's; D109 is NOT a fallback (it changes the statistics). Missing the ~10 min/min aim is not a failure. The accept does not wait on the interim.

**Q6 breakdown instrument: RECOMMENDED** (a tool driving the product functions in the pass's order with its own clock, records checked equal to the engine's bit for bit; one `cProfile` cross-check of the real `analysis_job()`, overhead noted, not a figure of record; no product timers, no dependency). Helper flag, the 5 % sum CHECK, CONFIRMED in this form: the SUM of per-step MEANS equals the mean per-frame wall of the same run within 5 % (medians are reported beside, not summed); a residual above 5 % is itself a finding named in the table (unattributed time), not a failed instrument.

**Q7 re-measure set: RECOMMENDED, the whole `V16_PLAN`** (GX011625 is in the plan row; the 5.3K row re-checks N4 under the overlap and the FFT). `export_bench.py` gains the output-folder option, default unchanged.

**Q8 DR-40 (b): not this package's; stays OPEN.** If task 1's frame-path breakdown shows per-call constant uploads above 1 % of the render, the round-0 table asks for `methods/compensation.py` and `white_balance.py`; otherwise I record the row as measured-negligible at the next `methods/` touch.

**Q9 memory: RECOMMENDED.** The round-0 table budgets the two decoders, the lead and the FFT buffers against N4 (16 GB RAM, the 8 GB card); the 4K and 5.3K rows re-measure peaks; `memory_estimate_bytes` stays at or above the measured reserved peak; a formula change is a STOP to me. If the FFT buffers break the 5.3K budget, the alternative (direct filter above 4K) is the fallback, decided in round 0 or by a STOP.

**Q10 interim timings: RECOMMENDED** (one GX011627 cold c3 run per candidate in a short EXCLUSIVE window you grant; development evidence, not of record; OPEN/CLOSE to me as every window).

Two notes for the cell text: (i) in the Done clause, "every existing test unchanged or changed only by a CHARC ruling" includes WP3.14's cancel / failure / D87 / V11 tests and WP3.11's `smooth_at` tests by name; (ii) the fill's GATE_CHECKS line will be the two-leg command once WP-T4 lands, so the brief says "the full suite per the fill's GATE_CHECKS at dispatch" (it does; keep it).
