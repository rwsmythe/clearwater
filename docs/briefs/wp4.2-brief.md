# WP4.2 — Video path end to end (dispatch brief, DRAFT, RULED)

**Status:** DRAFT, RULED 2026-10-28 (CHARC `2c4476d9869df056`, rulings below, which take precedence over the text above them); FINAL only after WP4.1's accept plus one revision pass, on CHARC's word. DRAFT 2026-10-28, written by a drafting helper for the orchestrator (generation 16) from
CHARC's Phase 4 commission `159c14fb79ad1aae` (section 1 lanes, section 2 the WP4.2 bounds). Base =
the main commit named at dispatch (drafted on `6536f60`). **This draft is revised once against
WP4.1's accept record before FINAL** (commission section 1: "the WP4.2 and WP4.3 drafts are revised
once against their predecessor's accept record"). Every WP4.1 name below is (as proposed in WP4.1's draft; final per its accept), from
`docs/briefs/wp4.1-brief.md` questions 1-6, 9 and 10: the root `src/clearwater/app/composition.py`
in a new Qt-free `clearwater.app` package, with `export_jobs(*, app_version, reader, writer,
methods, select_backend, on_stage) -> ExportJobs` (its question 4: `kind == "video"` routes to
`unavailable_exports().job(request)`) and the builders `photo_reader()`, `photo_writer()`,
`correction_methods()`, `backend_selector()`; the runner `tools/headless_export.py` (its
question 5: `requests_for`, `run`, `record_json`, `main`; every IF-10 field a flag; exit 0 / 1 /
2; record `"schema": 1`, additive only; its question 9: the footage-folder refusals).
Owner decisions: none inside the package. A V3 failure of the product method
(D96), any change to the 25 % threshold, and anything relaxing a mandatory V4 item are
owner-reserved: a STOP, never done here.
- Spec **v0.5.5**: section 5.5 ("In v1 every input file is its own clip: smoothing starts and ends
  within the file"); V3, V4, V9, V12 (deferred to v2), V17; D54, D55, D71, D76, D83, D86, D87, D94,
  D95, D96, D105, D107, D111, D112, D113, D114, D115; N3, N4, N8, N10. Architecture FINAL 1.0:
  sections 1, 2 ("video analysis", "video export (jobs)"), 3 (IF-1, IF-2, IF-5, IF-7, IF-8 with its
  "Export seam" paragraph, IF-10), 5. AD-2, AD-3, AD-5, AD-7 (READING 2026-10-27), AD-9, AD-11,
  AD-14, AD-15, AD-19, AD-20, AD-21, AD-22, AD-28, AD-29.
- Plan section 6 Phase 4 row WP4.2 (size L; depends on "WP4.1, WP3.5, WP3.7–WP3.12"; feeds "V3,
  V4, V9, V12, V17"; "joins probe, decode, analysis, cache, render and encode; every input file is
  its own clip (no cross-chapter smoothing in v1)"); section 7 rows V3, V4, V9, V17 ("Built in ...
  WP4.2", completed in WP5.1).
- Accept records and reports, Phase-4 notes: WP3.21 accept (`docs/proofs/wp3.21-accept.md`, "Debt
  and owed rows") and report "Design as built", "V4 SAME", "Limits"; WP3.14 accept "Debt and owed
  rows" and report "Debt dispositions" (DR-45 (b) "WP4.2's (the sink's `close` refuses a short
  frame set)"); WP3.11 accept "Results" and report "V3 ratios on steadily moving content
  (information for CP5 / WP4.2)", "Consumer notes" ("WP4.2 (end to end): V3 with the product
  method; V17 holds by construction"); WP3.12 report "Public API", "Differences between the stub
  and the product"; WP3.10 accept "Consumer notes"; WP3.9 accept "Consumer notes".
- Cell: `implementer-opus-high` (commission section 1: a composition package across every
  frozen-interface consumer, L-sized, design choices at round 0). Tier **STRONG**, Claude lane:
  Reviewer A (your loop) and Reviewer B (the orchestrator's seat) are Codex at the pin
  `gpt-6.1-sol` / high.
- Worktree `.worktrees/wp4.2`, branch `wp4.2` from main, base = the main commit named at dispatch
  (after WP4.1's accept).

**Why.** Every video component is on main (probe WP3.7, colour WP3.5, decode WP3.9, sink WP3.10,
analysis WP3.11, cache WP3.12, the export engine WP3.14 as optimised by WP3.21), but no PRODUCT
code builds them together: the WP3.21 report says "No product code constructs the real source
yet: the GUI's path is the stubs' until WP4.2", and the V16 figures of record (9.57-9.92 min/min at
4K) were measured through `tools/export_bench.py` with device frames ON. DR-67: "a job built
without it silently runs the OFF row (17.25 min/min at 4K against 9.6 with it)". This package makes
the product's composition build the video path, with the GPU job's source, sink and analysis on the
selected backend, and proves V3, V4, V9 and V17 through it.

| Field | Content |
|---|---|
| ID and title | WP4.2 — Video path end to end; plan section 6 Phase 4 row WP4.2 |
| Goal | Extend WP4.1's composition root (`clearwater.app.composition` (as proposed in WP4.1's draft; final per its accept)) and headless runner (`tools/headless_export.py` (as proposed in WP4.1's draft; final per its accept)) with the video path, replacing `export_jobs()`'s video router to `unavailable_exports()` with the real engine: probe -> decode -> analysis -> cache -> render -> encode through the real `FFmpegVideoSource`, `AnalysisEngine`, `DiskProxyCache`, the IF-3 methods and `FFmpegVideoSink`, one job (one clip) per input file. The GPU job's source and sink are built with `device_backend=<the backend the job selected>` and its analysis engine gets that backend; the CPU job passes None (DR-67). Prove through the product composition: V4 (every MANDATORY and REQUIRED item SAME; GX011627 in ONE exclusive window), V9 (neutral parameters, AD-11's bound), V17 (reopen skips the decode pass; a version mismatch re-analyses), V3 with the product method, and the own-clip rule. V16 is NOT re-measured (WP5.2, AD-21). |
| Spec / decision clauses | Section 5.5 "every input file is its own clip: smoothing starts and ends within the file". V3 "pass if flicker with smoothing ≤ 25% of flicker with per-frame (unsmoothed) statistics"; AD-14 "must stay under 0.5/255 after smoothing", extended: "V3's 25 % RATIO is not met on it ... and is not asserted on it; the figures are recorded"; "V3 on real footage is V2's (D112, WP4.2); the 25 % threshold stays tunable and the owner's". V4 "output matches source frame count, per-frame timestamps, start offset, resolution, bit depth (or the selected 10-bit option), chroma format, audio and display orientation; color tags match the source"; D115 "One variable-frame-rate sample". V9 "every stage set to its neutral value ... output matches the input within a small color-difference tolerance ... including color tags"; AD-11 "V9 identity round trip (neutral parameters, pre-encode): max abs diff ≤ 2/255, mean ≤ 0.2/255", "measured on the decoded-RGB side with the encoder AND its 8-bit Y'CbCr 4:2:0 conversion excluded". V12 "(deferred to v2, 0.5.3)". V17 "reopening an unchanged clip skips the decode pass; a cache format version mismatch triggers re-analysis"; D113 "Cache key includes a cache format version". D86 "Truncated/corrupt video: process the readable portion and warn". D96 "Weight-map temporal smoothing is conditional: added to v1 if V3 fails" (owner, CP5). N3/D107 "the same code runs on CPU or GPU"; D111 "Automatic CPU fallback"; N4 "frame parallelism and buffering are bounded"; N8 "source files never modified". AD-29 "Device extensions of IF-2 by consumer-side Protocols; CuPy only in `core`". AD-21: V16 "re-run at WP5.2". |
| Depends on | WP4.1 (its accept: `clearwater.app.composition` `export_jobs()` and its builders `photo_reader()`, `photo_writer()`, `correction_methods()`, `backend_selector()`; `tools/headless_export.py`; the photo legs; every name (as proposed in WP4.1's draft; final per its accept)). On main: WP3.21 (`7e228fb`: the overlap, device frames, `DeviceFrameBackend` in `io/video/decode.py`, `AnalysisDeviceBackend` in `analysis/proxy.py`, `JobDeviceBackend` in `jobs/export.py`), WP3.14 (`ba6e923`: `ExportEngine`, `run_batch`), WP3.11 (`47235b6`: `AnalysisEngine`), WP3.10 (`47bc6d6`: `FFmpegVideoSink`, `tools/video_fidelity.py`), WP3.9 (`09ab408`: `FFmpegVideoSource`), WP3.12 (`DiskProxyCache`, `cache_key`), WP3.7 (`probe`, `filter_inputs`), WP3.5 (`clearwater.color`), WP3.4 (`available_methods`), WP3.1 (`core.select_backend`). WP3.8 is removed (AD-19). |
| Debt and decided items | The table "Register rows" below (every row whose Signal or trigger names WP4.2, WP4.x, or a module this package touches). BINDING (commission section 2): **DR-67** CLOSES; **DR-71** CLOSES; **DR-73 (a)** per question 2; **DR-74** CLOSES (question 8). **Information for CP5:** the WP3.11 V3 ratio figures go into the accept record and the report, beside this package's product-method figures (task 7). |
| Files owned (questions 1, 2, 11) | NEW: `tests/test_wp42_device_backend.py` (DR-67), `tests/test_wp42_composition.py` (the video legs of the root), `tests/test_wp42_video_path.py` (V4 small set, V9, V17, own clip, DR-45 (b), cancel and failure through the composition), `tests/test_wp42_v3_product.py` (V3 with c3 and ancuti2018), `tests/test_wp42_runner_video.py` (the runner's video legs); `docs/reports/wp4.2-video-path.md`; `docs/proofs/wp4.2-ledger.md`. (Test file names are proposals; round 0 may merge them.) EDIT: `src/clearwater/app/composition.py` (WP4.1; replace the `kind == "video"` router with the real engine, add the video builders; the photo builders and WP4.1's tests unchanged) and `tools/headless_export.py` (WP4.1; video-specific options and additive record fields only, `"schema": 1` kept); both EXTEND, never rewrite, names (as proposed in WP4.1's draft; final per its accept). WP4.1's tests pass unchanged EXCEPT those that pin the video router (WP4.1 task 5 CHECK "a video path in WP4.1 yields the question-4 failure as a failed item", and any test asserting the `unavailable_exports()` routing): they must change when the router goes, so round 0 lists each by node id for a ruling (question 2); `src/clearwater/jobs/export.py` (WP3.14/WP3.21; the per-job device-backend hook, question 1, and DR-71); `src/clearwater/core/backend.py` DOCSTRING ONLY at `block_sums` (DR-73 (a), question 2); `tests/test_wp321_fft_release.py` (question 8: DR-74's case and DR-73 (b)'s rename only). EDIT only by a round-0 grant: `src/clearwater/analysis/engine.py` (WP3.11; question 7's frame-count check, question 6's DR-47 items). NOT owned: `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN, AD-20), `jobs/export_seam.py`, `jobs/naming.py`, `safe_write.py`, `disk_space.py`, `batch.py`; `io/video/` (every module), `color/`, `cache/`, `methods/`, `config/`, `analysis/proxy.py`, `analysis/store.py`, `analysis/smoothing.py`, `core/` except the docstring; `gui/` including `gui/engines.py` (question 3); `tools/export_bench.py`, `tools/export_oracle.py`, `tools/video_fidelity.py`, `tools/video_io_bench.py` and `tests/test_jobs_export_support.py` `product_engine` (imported or run, never edited; question 11, WP4.1 question 10); WP4.1's static "one place" test (`tests/test_app_composition.py`, WP4.1 task 3) is not edited: WP4.2's own static test adds `FFmpegVideoSource`, `FFmpegVideoSink` and `DiskProxyCache` to the constructors only the root may call in `src/clearwater/`; `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/fixtures/`; every other existing test file; `pyproject.toml`, `uv.lock`. |
| Interfaces provided | None frozen. `ExportEngine` gains only ADDITIVE, keyword-only, defaulted constructor parameters (question 1), so every existing caller (`export_bench.py`, `export_oracle.py`, the WP3.14 and WP3.21 tests) is unchanged; the root's video builder and the runner's video options per round 0. |
| Interfaces consumed | IF-1 `Frame` (`device` `"cuda:0"`), IF-2 `ArrayBackend` plus the AD-29 device extensions by Protocol, IF-3 (`available_methods()`, `Parameter.neutral`), IF-4 (through the engine), IF-5 `VideoSource` / `VideoSink` / `ProbeResult`, IF-7 `ProxyCache` / `CacheKey`, IF-8 `Progress` / `JobResult`, IF-9, IF-10 `Settings` (`output_folder`, `video_encoder`, `quality_level`, `ten_bit_for_eight_bit`, `force_cpu`, `cache_limit_bytes`); the seam `ExportRequest`, `ExportJobs`, `CANCELLED`. |
| Consumers | WP4.3 (wires the GUI to the same root; DR-62, DR-68, DR-69; the GUI's video legs, question 3), WP5.1 (completes V3, V4, V9, V17 through the runner), WP5.2 (V15, V16 through the product composition), WP5.3 (the review pack's video exports). |
| Hardware flags | `gpu`, `footage`, `slow` as WP3.14 and WP3.21. **EXCLUSIVE** for task 10 (the GX011627 V4 leg) and the full suite: plan 4.3 "one at a time, nothing else heavy running"; at least 5 GiB free before a run; GX011627 read only through `tools/local_config.find_footage_file`; every output under `work/`; a run from an ungranted or a parallel-worker window is not a figure of record (AD-28). |
| Out of scope | V16 and every speed figure of record (WP5.2, AD-21; the window's elapsed is information only); the analysis speed (DR-70); the GUI wiring and the GUI's video engines (WP4.3, question 3); DR-62's serialisation; DR-68, DR-69; chapter grouping and V12 (v2); D109; any change to what the statistics are (AD-3, AD-5) or to the encoder mapping (AD-12); any change in `src/clearwater/interfaces/`; decoding, parsing or logging any `gpmd` packet, IMU or GPS data; reading or logging any location tag. |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict, the full suite per the fill's GATE_CHECKS at dispatch (the two-leg command) green in a granted window, every existing test unchanged except as ruled (question 8); the DR-67 test on main; V4 SAME through the product composition on the small set (suite) and on GX011627 plus the WP2.3 set (task 10, one EXCLUSIVE window); V9, V17, own-clip, DR-45 (b), cancel and failure tests; V3 with the product method asserted where AD-14 asserts it and recorded where it records; DR-71 and DR-74 closed, DR-73 per question 2 and question 8; the WP3.11 V3 ratios and this package's in the report and the accept record; V12 recorded as deferred; the new serial-leg cost within question 9's budget; Reviewer A converged. |

### Register rows (commission section 2 register rule)

Found by greps on `WP4.2`, `WP4.x` and every owned or edited path (`jobs/export.py`, `io/video`,
`analysis/`, `cache/`, `core/backend.py`, `gui/engines.py`, `tools/export_bench.py`,
`test_wp321_fft_release.py`) in `docs/debt-register.md` at `6536f60` (register `cffd243`).

| Row | Disposition | Ground |
|---|---|---|
| DR-67 | **CLOSES** (binding) | Trigger "a test asserts the product job passes the selected GPU backend to source, sink and engine, and that the CPU-backend job passes `None`; closes when that test is on main". Task 2, question 1. |
| DR-71 | **CLOSES** (binding) | Trigger "The next touch of `jobs/export.py` (WP4.2 or WP5.2): take the larger of the marginal and the own rate, with a test on a partially extended retry". Task 2 touches `export.py`; task 8. |
| DR-73 | (a) **CLOSES** if question 2 grants the docstring line, else NOT REACHED; (b) per question 8 | (a) "WP4.2's touch of `core/backend.py`": `block_sums` docstring "38 bits at k = 8" holds for 8-bit, 10-bit needs 40. (b) "the next touch of `test_wp321_fft_release.py`": the rename of `test_a_video_job_releases_at_the_analysis_end_and_after_every_frame` (asserts two releases). |
| DR-74 | **CLOSES** (binding) | Trigger "WP4.2 or WP5.2: one case longer than the lead at a gated resolution, asserting the pool drop during rendering" (c3's derived lead is 61 frames; the gate is `min(H, W) >= 1080`, `sigma >= 32`). Task 8, question 8. |
| DR-45 | (a) NOT REACHED; (b) **CLOSES** (question 7) | (a) every `FrameStream` is iterated and closed by one thread (WP3.21's design, `jobs/export.py` module docstring; the cancel watchdog calls the sink's `abort`, never a stream's `close`); WP4.2 adds no cross-thread close. (b) trigger "WP4.2's end-to-end frame-count check": the export half is held by the sink (`close` refuses a short frame set, WP3.14 report); the analysis half is question 7. |
| DR-47 | NOT REACHED, CONSUMER NOTE (question 6) | Trigger names "WP4.2 (end-to-end cancel)". The export builds one fresh `AnalysisEngine` per job and runs its job callable once (`_Analysis.start`), so (a)'s retained callable is not reached; (b)/(c) are stated limits; end-to-end cancel tests through the composition (task 6). |
| DR-46 | NOT REACHED | "The next touch of the Y-2 checkers (WP4.2 or a methods change)": `methods/ancuti_fusion.py` `_checked_record` and `analysis/store.py` `put` are not owned or touched; reachable only by a hand-made record. |
| DR-41 | CONSUMER NOTE | The composition passes `DiskProxyCache` its registered `DEFAULT_CODEC` and keys with `cache_key(path)` / `key_for` of the same codec; a test pins it (task 3). Stays open (test-hook codecs only). |
| DR-62 | NOT REACHED | WP4.3's (GUI recompute vs export). The runner runs one activity at a time by construction; nothing here widens it (the export half never writes the cache, WP3.21 Q2 (b)). |
| DR-56 | NOT REACHED | "WP4.x if an owner clip shows an audible tail difference": an owner listening check, not this package; the window's compare records the audio items as they are. |
| DR-65 | CONSUMER NOTE | WP-T5's (the four export tests); WP4.2 edits none of them and keeps its own serial-leg cost within question 9's budget. |
| DR-68, DR-69 | NOT REACHED | WP4.3's rows; WP4.2 shows nothing in the GUI and leaves the GUI's video engines as they are (question 3), so the preview's FFT-plan case is not opened before WP4.3. |
| DR-70 | NOT REACHED | Trigger "An owner wish below ~9.5 min/min at 4K, or WP5.2's N6 re-measure". |
| DR-72 | NOT REACHED | `tools/export_bench.py` is not touched (question 11). |
| DR-35 | NOT REACHED | (a) refusal text and (c) start-up `remove_leftovers` are WP4.3's (the clause on WP4.1's runner is STRUCK, CHARC addendum (3): WP4.1's runner never calls `remove_leftovers`). |
| DR-36 (c)-(f), DR-58 (a)(b), DR-57 (d) | NOT REACHED | `io/video/` is not edited; out of envelope (another ffprobe build, several GPUs) or unreachable (DR-57 (d)). |
| DR-27 | CONSUMER NOTE | Footage tests through `find_footage_file` inherit (1) (an unreadable folder skips); task 10's record states GX011627 was found, not skipped. |
| DR-15, DR-40 (b), DR-25 (3), DR-20 | NOT REACHED | AD-22 ruled the B-frame case (no iPhone clip in this set); DR-40 (b) measured negligible, `methods/` not owned; DR-25 (3) is WP5.2's; DR-20's open items are `tools/lookcheck` instrument items. |

## Task ladder

1. **Read and map.** WP4.1's accept record, its composition root and runner; `jobs/export.py`
   (`ExportEngine.__init__`, `_video`, `_analyse`, `_write_frames`, `_Analysis`), `io/video/decode.py`
   (`FFmpegVideoSource(device_backend=...)`, `DeviceFrameBackend`), `io/video/encode.py`
   (`FFmpegVideoSink(device_backend=...)`, `_payload`'s device rule), `analysis/proxy.py`
   (`AnalysisDeviceBackend`), `analysis/engine.py` (`_decode`, `mark_complete`), `cache/`
   ("Differences between the stub and the product"), `gui/engines.py` and
   `gui/analysis_service.py` (`StubClipAnalysis`, question 3), and the hand compositions in
   `tools/export_bench.py` `build_engine` / `_measure` and `tools/export_oracle.py`, which are the
   patterns the product root replaces for the product (not edits).
2. **Round 0 yield: the design table.** In the ledger, before product code: the per-job
   device-backend hook (question 1: names, the call order after `select_backend`, which source the
   probe and the analysis use, every existing caller unchanged); the root's video builder and the
   runner's video options (question 12), with WP4.1's names; the GUI's video legs (question 3); the
   test list with each test's markers and its expected serial-leg seconds against question 9's
   budget; the V3 measurement point (question 5); the DR-45 (b) analysis-half finding (question
   7); the register dispositions above, confirmed or corrected; every grant asked for; the
   `scripts/cell_depth.py` figure your dispatcher gives you. **YIELD.** A choice the brief leaves
   open is a STOP. A new module, a new dependency or a persistent-data shape in the table is a
   tripwire: the dispatcher copies the table to CHARC (commission section 4).
3. **DR-67: the GPU job on its backend** (question 1). In `jobs/export.py`, after the job's
   `select_backend`: a GPU job builds its source and sink with `device_backend=<that backend>`
   (identity, not a second selection), a CPU job with None; the job's `AnalysisEngine` receives the
   selected backend and the same per-job source, so the analysis takes the device block sums
   (`AnalysisDeviceBackend`) and the render the device frames. `hw_decode = backend.device !=
   "cpu"` stays (the WP3.21 Limits: "A CPU backend with a hardware decoder is not a supported
   combination"). Without the new parameters the engine behaves exactly as today. CHECK: the DR-67
   test with recording factories (the GPU leg on a backend double that satisfies the Protocols, and
   a real `gpu` leg on a WP2.3 sample whose sink receives `cuda:0` frames); planted wrong wirings
   fail by name: a GPU job whose source or sink gets None (the silent OFF row), a CPU job that
   gets the GPU backend, a second `select_backend` call whose answer differs from the job's.
4. **The composition root's video legs** (EXTEND `clearwater.app.composition`: `export_jobs()`'s
   video branch stops routing to `unavailable_exports()` and the router goes). The real `FFmpegVideoSource`,
   `FFmpegVideoSink` per job through the question 1 factories, `DiskProxyCache(<cache folder>,
   settings.cache_limit_bytes)` with its default registered codec, `cache_key`, `core.select_backend`
   (never `stub_era_select_backend`), `available_methods()`. CHECK: `tests/test_wp42_composition.py`
   pins each collaborator's class and the codec (DR-41); `export_jobs()` gains only additive
   keyword-only parameters (the cache folder for video, test overrides for the question 1
   factories), its photo builders unchanged; the root still never resolves `app_locations()`
   (WP4.1 question 6); WP4.1's photo tests pass unchanged;
   `clearwater.jobs` still loads no `clearwater.gui`, `clearwater.methods`, PySide6 or CuPy at
   import (WP3.13's test, run, not changed).
5. **The runner's video legs** (EXTEND `tools/headless_export.py`; question 12). WP4.1 already
   carries every IF-10 flag (`--out`, `--beside-source`, `--encoder`, `--quality`, `--ten-bit`,
   `--force-cpu`, ...), `--method`, `--parameters`, `--neutral`, `--record`; WP4.2 adds only
   video-specific options and additive record fields. Video inputs through
   `filter_inputs` (sidecars excluded, D83), one `ExportRequest` per file through `run_batch` (each
   file its own clip: D81 skip-and-log, D45 stop), `--cache-dir`; WP4.1 question 9's refusals
   (`--out` inside the footage folder, `--beside-source` for a source inside it) apply to video
   unchanged, and `--cache-dir` inside it is refused the same way. CHECK: a CPU run on
   `vid-hevc8-bt709-full` through `main`; the refusals on video paths; the exit statuses; a
   two-file run gives two outputs and two cache entries; with `--force-cpu` a video run loads no
   CuPy (WP4.1 task 5's subprocess check, extended to video); the record keeps source NAMES only.
6. **End to end through the composition** (question 4 sets the split between the suite and task 10).
   - V4 small set: `vid-hevc8-bt709-full` on the CPU (always) and the GPU with device frames
     (`gpu`), compared in-test by `tools/video_fidelity.py`'s comparison: every MANDATORY and
     REQUIRED item SAME; `vid-truncated` warns (D86); `vid-hlg`, `vid-pq` and a sidecar are
     readable failures with nothing written.
   - V9: every V9 parameter at `Parameter.neutral` (c3 and ancuti2018), the frames the sink
     receives against the decoded source frames: max abs ≤ 2/255, mean ≤ 0.2/255 (AD-11, encoder
     excluded); the colour tags SAME on the output.
   - V17: a second export of the unchanged clip over the same cache folder never iterates the
     analysis's decode (a counting source) and gives bit-identical pre-encode frames (N10, AD-11
     tier: same device); an entry of another cache format version is removed at open and the
     next export re-analyses.
   - Own clip (section 5.5): two files in one batch; each output's pre-encode frames equal that
     file's export run alone (bit for bit), in either order; no record of one file is read by the
     other's job.
   - DR-45 (b) (question 7): a planted decoder that yields a strict prefix and ends cleanly.
   - Cancel and failure through the composition: a cancel during the analysis lead and one
     mid-encode give `CANCELLED`, no temporary, no final, every thread joined; a failure in the
     analysis half gives the job's failure with its own text (WP3.14 and WP3.21 guarantees, now
     on the composed engine).
7. **V3 with the product method** (question 5). On the AD-14 clip (`ad14-flicker`, with
   `ad14-mask`) and on WP3.11's jittering-patch clip (built in-test as `test_analysis_v3.py`
   builds it), through the composed engine with c3 and ancuti2018 at their defaults: assert
   AD-14's bound (mean abs frame-to-frame difference in the mask under 0.5/255 after smoothing) on
   `ad14-flicker` and RECORD its four V3 ratios; assert V3's 25 % ratio on the jittering-patch
   clip. A product-method miss of either assertion is a STOP to the dispatcher with the figures
   (D96 is owner-reserved; the threshold is the owner's). The report's heading "V3 ratios
   (information for CP5)" carries WP3.11's table (`ad14-flicker` GrayWorld 0.475 / 0.447 / 0.488 /
   0.476, GainsStretch 0.387 / 0.482 / 0.455 / 0.400; WP1.4 real footage 0.35-0.45) beside this
   package's c3 and ancuti2018 figures; the accept record copies it.
8. **Debt at the touch.** DR-71: `_Analysis.cache_growth_bytes` takes the larger of the marginal
   rate (growth over the lead per frame stored) and the entry's own bytes per stored frame, with a
   test on a partially extended retry (the F5 fallback test unchanged). DR-74: a `gpu`, `slow` case
   longer than c3's derived lead at a gated resolution (short side ≥ 1080), asserting the pool's
   drop WHILE frames render (question 8). DR-73 (a) per question 2; (b) per question 8.
9. **Tests and static.** Every new test file above; every existing test passes unchanged (except
   question 8's one rename). Every light run includes `tests/test_core_deps.py`,
   `tests/test_color_deps.py`, `tests/test_io_video_decode_rules.py`, `tests/test_analysis_deps.py`
   (AD-29; plan 8.1 frame rule 5: nothing outside `clearwater.core` imports `cupy`/`cupyx` or reads
   `.xp`). No module opens a `gpmd` packet. Then the review loop (below), then the full two-leg
   suite in a granted window.
10. **The GX011627 V4 SAME leg (EXCLUSIVE, LAST; question 10).** The dispatcher grants ONE window
    after every other task, the review loop and the full suite; do not start it unasked. The
    runner exports GX011627 through the product composition (c3 defaults, encoder auto -> NVENC,
    Standard, 8-bit, the GPU job with device frames), outputs under `work\wp4.2\v4\`; then `uv run
    python tools/video_fidelity.py compare SOURCE OUTPUT --out <under work\wp3.10\wp4.2-v4\>` (the
    tool refuses an `--out` outside its own `wp3.10` root). In the same window, the WP2.3 V4 set
    through the runner on the GPU and with `--force-cpu` (question 10). The record names
    `JobResult.device`, the sink's frame device (`cuda:0`), the job's `device_backend`, the
    encoder, and the elapsed (information only, never a V16 row). Nothing footage-derived is
    committed; the kept outputs are not deleted without a grant naming them. Send `WINDOW
    RELEASED: <summary>` at the end.

## Declared operating envelope

Windows 11; Python 3.12; FFmpeg 9.0.2 (gyan) with `hevc_nvenc` and `libx265`; the RTX 4070 Laptop
GPU (8 GB) or the CPU fallback; the Ryzen 9 7940HS, 32 GB RAM; video sources inside WP3.9's and
WP3.10's envelopes (MP4/MOV, HEVC or H.264, 4:2:0, 8/10-bit, BT.709 or BT.601, the reproduced
edit-list forms, at most the HERO13 track set); the WP2.3 samples, the AD-14 clip, synthetic clips
under `tmp_path`, GX011627 (task 10 only); the headless runner and the tests as the only product
entry points (the GUI's video engines are WP4.3's, question 3); ONE export activity at a time, one
job per file in sequence, one writer per cache key; a cache folder and an output folder under
`work/` or `tmp_path`; local NTFS. Out of envelope: several concurrent runners on one cache folder,
a GUI recompute during an export (DR-62), network shares, a second GPU (DR-58 (a)), a CPU backend
with a hardware decoder (WP3.21 Limits), chaptered recordings (v2), other operating systems
(portable code, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (Codex `-m gpt-6.1-sol -c model_reasoning_effort=high`, WSL transport, probe
  first, one `^ succeeded in` line before round 1), run by you at your seat to convergence;
  five-round gate. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.2\rN\`; ledger
  `docs/proofs/wp4.2-ledger.md`. Copy the runner and prompt shape from WP3.21's last round folder
  (`...\wp3.21\r2\`); the banner must read `gpt-6.1-sol` (a round with another pin is void);
  exclude `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - DR-67: on every path the GPU job's source, sink and analysis engine receive the backend the
    job selected (identity), the CPU job None; the probe and any early failure before selection
    build nothing on a device; no second selection that can disagree;
  - the composition: the real classes, the registered codec (DR-41), `core.select_backend`, no stub
    on a product video leg; the cache and output folders never inside the footage folder;
  - each file its own clip: no state carried between jobs (engine, store, key, source);
  - V17: a complete entry skips the decode pass; a version mismatch re-analyses; a prefix decode
    cannot leave a complete entry for a clip it did not fully decode (question 7);
  - cancel and failure on the composed engine: `CANCELLED` or the original text, nothing on disk,
    every thread and FFmpeg process ended, WP3.14's and WP3.21's orders unchanged;
  - DR-71's rate rule and the F5 fallback; DR-74's case really observes a drop during rendering;
  - the V3, V9 and V4 assertions measure what the spec and AD-11 / AD-14 name (pre- or post-encode
    as question 5 rules), and a planted failure of each is shown;
  - nothing in `interfaces/`, the seam or an unowned file changed; layering (frame rule 5;
    `jobs` imports no `core`, `methods` or `gui`); no `gpmd`, IMU or GPS data read.
- Reviewer B is the orchestrator's seat pass on the merge candidate (Codex, the same pin).

## Notes for the cell

- **Yields.** Task 2 (round 0): the table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating; make NO
  change in the turn that adjudicates a round. Your dispatcher gives you the
  `scripts/cell_depth.py` figure at every yield: put it in the ledger; ~250K is the evaluation
  point ("REVIEW ONLY this turn" when told), ~400K STOP.
- **Windows (plan 4.3, AD-28).** Heavy work runs ONLY in a window the dispatcher grants: every
  `footage` test, task 10, the full suite. Send `WINDOW REQUEST: <what, how long>` and wait for the
  grant; one heavy job at a time; at least 5 GiB free before a run (`uv run python -c "import
  psutil; assert psutil.virtual_memory().available >= 5*2**30"`); send `WINDOW RELEASED:
  <summary>` after each. Figures come only from serial runs.
- **The suite** = the two-leg gate from `CLAUDE.md`, from Git Bash with `PYTEST_ADDOPTS` unset and
  `QT_QPA_PLATFORM=offscreen`, each leg with its own fresh basetemp under `work/`:
  `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp4.2-<run>-parallel`
  then `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp4.2-<run>-serial`.
  Run in the background with foreground poll-wait calls on its done marker (a reaped run is not a
  result). A new wall-clock bound in a parallel-leg test is `slow` with a reason.
- **Footage.** Read-only at `C:\Users\rwsmy\clearwater-footage\`, reached only through
  `find_footage_file`; never written, renamed in or deleted from; never a temp root, cache folder or
  output folder; every output under `work/`. No `gpmd` packet decoded, no IMU, GPS or location
  tag read or logged.
- **Return report** = your FINAL message, under about 70 lines, to your dispatcher by your
  messaging tool: the round-0 decisions as ruled; the DR-67 wiring and its test; V4 (suite and
  window, per sample), V9 figures, V17, own clip, V3 table (WP3.11's beside yours); the DR
  dispositions; the gates; the Reviewer A rounds and verdict; open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20), the seam, `io/video/`,
  `cache/`, `methods/` or any file not owned or granted; a V4 MANDATORY or REQUIRED item DIFFERENT;
  a V3 or V9 assertion missed by the product method (owner-reserved where D96 or a threshold is
  concerned); a dependency; OS-specific code beyond AD-23; any need to decode a `gpmd` packet or
  read a location tag; any write outside `work/`, `tmp_path` and the planned temporary; the
  round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with `git -c
  core.autocrlf=false commit -m "feat(wp4.2): ..." -- <paths>`, with a `Co-Authored-By:` footer
  naming your model; every committed blob LF. Never `git stash`. Never a bare `cd`. Never post
  to a mailbox. Gates: ruff check, ruff format --check, mypy strict, the two-leg suite (in a
  window); no harness gate. Report `docs/reports/wp4.2-video-path.md` (claims, evidence paths,
  limits, the V3 information heading).

## Questions for CHARC (recommended answer first)

1. **The per-job device-backend hook (DR-67).** `ExportEngine` takes ONE `video_source` and a
   no-argument `sink_factory`, but selects the backend per job inside `_video`; `export_bench.py`
   works round this by selecting the backend BEFORE the job (`_measure`: "The backend the job will
   select for this clip (the same call)"), and `select_backend` reads free memory on every call, so
   a second call can disagree. Recommended: two ADDITIVE keyword-only `ExportEngine` parameters
   (names at round 0, e.g. `source_for` and `sink_for`, each `Callable[[object | None], ...]`),
   called once per video job right after `select_backend` with the selected backend for a GPU job
   and None for a CPU job; the per-job source serves both the analysis engine and the frame loop;
   the base `video_source` still probes. Absent, the engine is today's (every caller unchanged). The root's `export_jobs()` passes them when it builds the one `ExportEngine` that replaces its video router (WP4.1 question 4).
   Alternatives: (b) a recording `select_backend` wrapper in the root that the factories read
   (no `jobs` edit, hidden coupling, one job at a time assumed); (c) setting
   `FFmpegVideoSource.device_backend` per job on a shared instance (mutable shared state).
2. **Grants.** Recommended now: `jobs/export.py` (question 1, DR-71); `app/composition.py` and
   `tools/headless_export.py` (EXTEND), with a ruling on the WP4.1 tests that pin the video
   router (listed by node id at round 0; their replacement asserts the real video job)
   (EXTEND); `core/backend.py` docstring line only (DR-73 (a) CLOSES; no code change);
   `tests/test_wp321_fft_release.py` per question 8. At round 0 only, on the table's evidence:
   `analysis/engine.py` (question 7, question 6). Alternative: no `core/backend.py` touch (DR-73
   (a) stays open; "WP4.2's touch" is never met).
3. **The GUI's video engines (`gui/engines.py` `default_engines()`).** The commission says
   WP4.1's root replaces the stub wiring "for the PHOTO legs only; video stubs stay until WP4.2".
   Recommended (a NARROWING, so flagged): WP4.2 wires the video legs for the product's JOB path
   (`export_jobs()`'s video branch, used by the runner and by WP4.3), and leaves
   `default_engines()`'s `video_source`, `video_sink` and `cache` on the stubs for WP4.3 to swap
   together with the real analysis adapter (WP3.18's mapping); this matches WP4.1 question 3 ("video members stay stubs"). Ground: the shell's timeline
   defaults to `stub_analysis_factory` (`gui/timeline.py` line ~799), whose `StubClipAnalysis`
   decodes the whole clip through `engines.video_source` and stores every proxy in
   `engines.cache`; with a real source over the dict-backed `StubProxyCache` a 4K clip holds
   960 x 540 x 3 B per frame (GX011625: about 14,938 x 1.56 MB = 23 GB, above N4's 16 GB); over a
   real `DiskProxyCache` it writes non-AD-5 proxies under the product key into the product
   cache; and a real preview source opens DR-68's FFT-plan case before WP4.3's fix. Alternatives:
   (b) swap `video_source` and `video_sink` only, keep `StubProxyCache` (still the N4 case); (c)
   swap all three plus the analysis adapter here (WP4.3's scope).
4. **What runs in the suite and what in task 10's window** (suite cost, DR-65). Recommended: the
   suite carries the composition-identity tests (the composed engine is the engine WP3.14's and
   WP3.21's engine-level V4 tests already cover), ONE end-to-end V4 sample per backend
   (`vid-hevc8-bt709-full`, CPU always, GPU under `gpu`), V9, V17, own clip, DR-45 (b), cancel and
   V3 on small clips; the full WP2.3 V4 set and GX011627 run through the runner in task 10's
   window as recorded instrument runs, not suite tests. Alternative: every WP2.3 sample through
   the composition in the suite (duplicates WP3.14's legs; more serial time).
5. **V3 with the product method: where it is measured.** Recommended: on the frames the sink
   receives (pre-encode) from an export through the composed engine, the clip itself decoded
   from an encoded file (so decode, analysis, smoothing and render are the product's); the
   encoded output's figures recorded beside as characterisation. AD-14's bound asserted and its
   ratios recorded on `ad14-flicker`; V3's 25 % asserted on the jittering-patch clip; c3 and
   ancuti2018 at defaults. A miss is a STOP (D96 and the threshold are the owner's; CP5).
   Alternative: measure on the decoded output (the encoder's quantisation joins the flicker).
6. **DR-47 (its trigger names "WP4.2 (end-to-end cancel)").** Recommended: NOT REACHED with a
   CONSUMER NOTE: one fresh `AnalysisEngine` per export job, its job callable started once by
   `_Analysis.start`, so (a)'s retained callable is unreachable on the product job path; (b) and
   (c) stay stated limits; WP4.2's end-to-end cancel tests (task 6) are the evidence; the row's
   trigger moves to WP4.3 (the GUI's retained engine). Alternative: grant `analysis/engine.py` and
   close (a) and (c) here.
7. **DR-45 (b), the analysis half.** Helper reading, NOT executed: `AnalysisEngine._decode`
   (`analysis/engine.py` about lines 702-762) marks the entry complete after the last yielded
   frame with no comparison against `probe.video.nb_frames` or the readable count, so a decoder
   that yields a strict prefix and exits 0 could leave a COMPLETE entry for a part of the clip;
   the export half then fails at the sink's check (no bad output), but every later export reuses
   the entry (V17). Recommended: task 6 drives it; if the test shows a complete entry after a
   prefix, the round-0 table asks for the `analysis/engine.py` grant: a frame-count check before
   `mark_complete` (the probe's count, or the readable count for a D86 `truncated` /
   `unreadable_tail` source), a readable failure, the entry left incomplete; DR-45 (b) then CLOSES
   on both halves. Alternative: close (b) on the export half only and open a new row for the
   analysis half.
8. **DR-74's case and DR-73 (b).** Recommended: add DR-74's case to
   `tests/test_wp321_fft_release.py` and, in the same touch, rename
   `test_a_video_job_releases_at_the_analysis_end_and_after_every_frame` to a name that says two
   releases (assertion unchanged); both rows close at one touch; the rename is the one existing-test
   change, ruled here. Alternative: DR-74's case in a new WP4.2 file, DR-73 (b) left open.
9. **Serial-leg cost budget.** Recommended: the new `gpu` / `footage` / `slow` / `gui` tests add at
   most about 5 minutes to the serial leg (from the gate's `--durations`), each test's expected
   seconds in the round-0 table; GX011627 is never a suite test here. Alternative: no budget
   (WP-T5 is trying to shorten the same leg).
10. **Task 10's window.** Recommended: one EXCLUSIVE window holding GX011627 (the commission's
    required leg) plus the WP2.3 V4 set through the runner on the GPU and with `--force-cpu`
    (WP3.21 ran 13 compares in about 7 minutes); records as above. Alternative: GX011627 only
    (the WP2.3 set then rests on the suite's one sample per backend).
11. **New modules and the three existing assemblies** (WP4.1 question 10 leaves them to WP4.2
    "when it binds DR-67"). Recommended: no new product module (WP4.2 extends WP4.1's root and
    runner); the five test files, the report and the ledger as named; `export_bench.py`,
    `export_oracle.py` and `tests/test_jobs_export_support.product_engine` keep their own hand
    compositions unchanged: the bench and the oracle already pass `device_backend` themselves
    (`_measure`, `--device-frames`), so DR-67 is about the PRODUCT job and closes in the root and
    `jobs/export.py`; re-pointing the bench at the product root is WP5.2's, where V16 is
    re-measured and DR-72 rides. Alternative: re-point the bench and the oracle here (touches
    WP3.21's measured instruments; DR-72 then triggered).
12. **The runner's video legs and the cache folder.** Recommended: video files accepted through
    `filter_inputs` in `requests_for`'s `kind="auto"`; one request per file through `run`
    (`run_batch`); WP4.1's IF-10 flags and question 9 refusals reused unchanged; ONE new option,
    `--cache-dir`, REQUIRED when any item is a video (exit 2 otherwise, nothing run), refused
    inside the configured footage folder; additive record fields (the job's device, the sink's
    frame device, whether the cache entry was complete at start). The root takes the cache folder
    as an `export_jobs()` argument and never resolves app data (WP4.1 question 6; WP4.3's entry
    point passes `app_locations().cache_dir` and `Settings.cache_limit_bytes`, WP3.12 report).
    Alternative: a default cache folder under the working folder named in `clearwater.local.toml`
    (convenient for acceptance runs; the runner then depends on the machine's local config,
    against WP4.1 question 6's isolation rule).

## Rulings (CHARC `2c4476d9869df056`, 2026-10-28, verbatim; they GOVERN the Questions section above)

PRIMARY: orchestrator. Thread `159c14fb79ad1aae`, reply to `8c3c624c224c263e` (+ `56e00cce74e65b5c`, `528b3db814b6d2c5`). **RULING PACKET: all four drafts APPROVED with the rulings below; every helper recommendation ADOPTED except where a line says otherwise. Write the rulings verbatim into each brief, commit on `briefs-p4`, ff main; dispatch WP4.1 (opus-high) and WP-T5 (by pace) now; WP4.2 and WP4.3 stay DRAFT until their predecessor's accept plus one revision pass, then FINAL on my word.** Tripwire passes (new package `clearwater.app`, the WP4.3 modules, `python -m clearwater`, the leftover journal) are all GRANTED here.

**Flags.** (1) WP4.2 Q3 narrowing ACCEPTED (N4 ground: the stub analysis over a real source stores ~23 GB for GX011625; the GUI's video legs swap in WP4.3 with the adapter). (2) withdrawn; see 43-Q13. (3) tripwires GRANTED as listed; the `gui/engines.py -> clearwater.app.composition` edge is the ONE gui-to-app edge, pinned by `tests/test_app_deps.py`. (4) the two S1 tests go in WP4.3 (43-Q11); WP-T5's three bodies as T5-Q2/Q3/Q4. (5) noted; my "~30 min" is CORRECTED to the helper's ~12 min projection, W1 replaces it.

**Addendum.** (1) WP4.3's V8 legs cite AD-11 AS AMENDED 2026-10-21 (k = 1 EXACT; k > 1 mean <= 1/255, p99 <= 2/255 at k = 2 and <= 4/255 at k = 4, max recorded never asserted), the same text as WP4.1 line 301. (2) 41-Q3 + 43-Q11 ruled together as recommended: `default_engines()` stays, takes its photo legs and methods from the root in WP4.1, its selector and video legs in WP4.3; `shell.run` and `gui/__init__.py` unedited. (3) WP4.2's DR-35 clause STRUCK.

**WP4.2 (L, opus-high, Codex nets; FINAL after WP4.1's accept + one revision).** Q1 (a): two ADDITIVE keyword-only defaulted `ExportEngine` factory parameters, called once per video job right after `select_backend` (backend for GPU, None for CPU); names at round 0; every existing caller unchanged. Q2 grants as recommended NOW: `jobs/export.py` (Q1 + DR-71), root and runner (EXTEND), `core/backend.py` DOCSTRING line (DR-73 (a) CLOSES), `tests/test_wp321_fft_release.py` (Q8); the WP4.1 tests pinning the video router are listed by node id at round 0 and replaced by assertions on the real video job (ruled here, no further ask); `analysis/engine.py` at round 0 only, on the table's evidence (Q7, and Q6 below). Q3 narrowing ACCEPTED (flag 1). Q4 as recommended (one V4 sample per backend in the suite; the WP2.3 set and GX011627 in the window through the runner). Q5 as recommended (pre-encode at the sink seam; AD-14 bound asserted, ratios recorded; 25 % asserted on the jittering-patch clip; a miss = STOP, D96 is the owner's). Q6 DR-47: NOT REACHED with the consumer note; AMENDED: IF the Q7 `analysis/engine.py` grant is exercised, the one-shot guard (a) is closed in the SAME touch (cheap, same file); otherwise the row stays OPEN with trigger = the next `analysis/engine.py` touch (WP4.3's consumer note stands; the trigger does not move to WP4.3, which does not own the file). Q7 as recommended: task 6 drives it; a complete entry after a prefix = the round-0 grant for a frame-count check before `mark_complete` (probe count, or the readable count for D86 sources), entry left incomplete, readable failure; DR-45 (b) closes on both halves. Q8 as recommended (DR-74 case + DR-73 (b) rename in one touch; the rename is the one existing-test change, ruled). Q9 budget: new serial-leg tests <= ~5 min, expected seconds per test in the round-0 table. Q10 ONE window: GX011627 + the WP2.3 set through the runner, GPU and `--force-cpu`; elapsed = information, never V16. Q11 as recommended (no new product module; bench and oracle untouched; re-pointing = WP5.2, DR-72 rides). Q12 as recommended (`--cache-dir` REQUIRED for any video item, refused inside footage; additive record fields; root takes the cache folder as an argument). T5-Q7's note: WP4.2 adds NO GX011627 suite test (Q4/Q9 already); whether its product-composition leg later supersedes `test_gx011627_through_the_engine_...` is WP5.1's, not WP4.2's.

**Cost restated:** unchanged from the commission except WP-T5's saving (~12 min per gate, not ~30) and one extra short window for it.
