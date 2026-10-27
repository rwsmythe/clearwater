# WP3.14 — Export jobs and batch (dispatch brief, FINAL)

**Status:** FINAL 2026-10-27 (CHARC `3c3c35d7e40b525e`); written by a drafting helper for the orchestrator (generation 12) at
CHARC's ruling `6f725eee`. Approved; base = the main commit named in the dispatch prompt.
Owner decisions: none inside the package (a mandatory item that cannot be met is a STOP; relaxing
one is owner-reserved).
- Spec **v0.5.5** (main `a5f9245`, owner-approved 2026-10-27, the D75 erratum, text only):
  section 8, G7, G8; D43-D45, D80, D81, D83-D87, D106, D111; N4, N6 (interim, D106); V4, V11, V16. Architecture FINAL 1.0: section 2 ("video
  export (jobs)"), section 3 IF-5, IF-6, IF-8 (with its "Export seam" paragraph), IF-9, IF-10,
  section 7. AD-4, AD-5, AD-7, AD-9, AD-12 (as amended 2026-10-27), AD-13, AD-15, AD-21, AD-22,
  AD-23. Frame `docs/briefs/wp2.4-phase3-frame.md` sections 1, 2, 3 (wave 4 row), 5 ("D106
  interim N6 / V16 | WP3.14 (export timing row), WP5.2 re-measure"). Reports, consumer notes:
  WP3.13 "Consumer notes"; WP3.9 "What it does", "Limits"; WP3.10 sections 3, 7.2, 7.3, 9;
  WP3.11 "Threading model", "Consumer notes"; WP3.4 "Consumer notes"; WP3.19 "The seam",
  "Limits", "Seam for WP3.14 and WP4.3". Briefs: `docs/briefs/wp3.19-brief.md` (the seam's
  GUI side), `docs/briefs/wp3.10-brief.md` (task 10, the floor row this row is measured beside).
- Cell: `implementer-opus-high`. Tier **STRONG**, Claude lane: Reviewer A (your loop) and
  Reviewer B (the orchestrator's seat) are Codex at the pin `gpt-6.1-sol` / high.
- Worktree `.worktrees/wp3.14`, branch `wp3.14` from main, base = the main commit named at dispatch.

**Why.** Plan: "**WP3.14** runs photo export, video export (decode, render, encode as a stream,
within the memory limits of N4) and the batch queue, with progress, cancel, skip-and-log on
failure, and an end-of-run report (IF-8)." Every engine it joins is on main (decode, sink,
analysis, methods, naming and safe writing, photo I/O); the GUI's export and batch panels run
against `unavailable_exports()` until this engine exists. CHARC `6f725eee` item 1: "WP3.14's V16
end-to-end row is the before-figure the optimisation is measured against" (WP3.21 opens after
this accept).

| Field | Content |
|---|---|
| ID and title | WP3.14 — Export jobs and batch; plan section 6 Phase 3 row WP3.14 (size L, depends on WP3.13, spec "§8, G7, G8; D43–D45, D80, D81, D111", feeds "V4, V11, V16"); module `clearwater.jobs` (plan 8.1: "Naming, safe writing, export, batch") |
| Goal | An implementation of the WP3.19 `ExportJobs` seam whose jobs export one photo or one video each (a video's analysis included) through `plan_output` and `SafeWrite`, with progress, cancel through the sink's `abort`, a per-item D87 check on DR-48's estimate, provenance, and a readable `JobResult`; a headless batch over the same jobs (question 9); and the V16 end-to-end export row in an EXCLUSIVE window. |
| Spec / decision clauses | G7 "Batch queue: add multiple files; apply one parameter set or preset; run unattended; report per-item success, warnings and failures at the end. A failed item is skipped and logged, and the batch continues (D80, D81)." G8 "Export and batch show progress with a cancel control:" "cancel deletes the in-progress temporary output;" "completed files are kept;" "in batch mode, cancel stops the whole remaining batch." D43 "Progress indicator with cancel, and non-blocking GUI"; D44 "On cancel, the partial output file is deleted; completed files kept"; D45 "Cancel during batch stops the whole remaining batch"; D80 "*(deferred to v2, 0.5.3)*"; D81 "Batch failure: skip the failed item, log it, continue, report at end"; D83 ".LRV/.THM sidecars excluded from input"; D84 "Photo name clashes across formats resolved by collision numbering"; D85 "Outputs written to a temporary name and renamed on success; leftovers cleaned on next start"; D86 "Truncated/corrupt video: process the readable portion and warn"; D87 "Disk space estimated before export; out-of-space during export fails cleanly"; D111 "Automatic CPU fallback when an image or frame is estimated not to fit in graphics memory; no tiled processing in v1". 8.3 "existing files are never overwritten"; "Source files are never modified." 8.4 "Outputs are written to a temporary name and renamed to the final name only on success (D85)."; "On cancel or failure, the temporary file is deleted"; "Before export, required disk space is estimated and the user warned if insufficient; running out of space during export fails cleanly without leaving a partial output (D87)." 8.1/8.2 "**Provenance:** Clearwater version and parameters embedded in metadata; on by default, can be turned off". N4 "peak RAM ≤ 16 GB, for video (including 5.3K 8:7)"; "frame parallelism and buffering are bounded to meet these limits." D106 "interim, about 25 minutes of processing per minute of 4K footage on the owner's laptop ... end to end". V4 "mandatory: output matches source frame count, per-frame timestamps, start offset, resolution, bit depth (or the selected 10-bit option), chroma format, audio and display orientation; color tags match the source". V11 "cancel and simulated failures (crash, disk full) leave no partial outputs; leftover temporaries removed on next start." V16 "export meets the N6 target at 4K in the owner's recording modes (interim 25 min/min per D106; re-set after the Phase 3 optimisation package at WP5.2)." AD-15 "export is unavailable until analysis of that clip completes"; AD-7 "Export waits for the whole clip's recompute"; AD-9 CPU/GPU "in each job's log line, with the reason when the fallback engaged". |
| Depends on | On main: WP3.13 (accept `6dd5a00`: `plan_output`, `SafeWrite`, `Reservations`, `MediaKind`, `validate_suffix`, `is_disk_full`, `check_free_space`, `estimate_photo_bytes`), WP3.19 (accept `f6e1687`: `clearwater.jobs.export_seam` — `ExportRequest`, `ExportJobs`, `CANCELLED`, `UNAVAILABLE_TEXT`, `unavailable_exports`), WP3.10 (accept `47bc6d6`: `FFmpegVideoSink`, `VideoEncodeError`, `detect_capabilities`, `resolve_encoder`, `NVENC_BITS_PER_PIXEL`, `NVENC_RATE_SHARE`, `PROVENANCE_MAX_BYTES`; `tools/video_fidelity.py`, `tools/video_io_bench.py`), WP3.9 (accept `09ab408`: `FFmpegVideoSource`), WP3.11 (accept `47235b6`: `AnalysisEngine`, `proxy_factor`, `block_mean`, `schema_hash`), WP3.4 (accept `ad15ab4`: `available_methods`, `backend_for`), WP3.1 (`select_backend`), WP3.6 (`PhotoReader`, `PhotoWriter`), WP3.7 (`probe`, `is_sidecar`), WP3.12 (`DiskProxyCache`, `cache_key`). Nothing unmerged. |
| Files owned | NEW: `src/clearwater/jobs/export.py` (the engine) and at most two further NEW modules under `src/clearwater/jobs/` named in the round-0 table (for example `batch.py`, `provenance.py`); `tests/test_jobs_export*.py`, `tests/test_jobs_batch.py`; `tools/export_bench.py` and `tests/test_export_bench.py` (the V16 instrument, question 11); `docs/reports/wp3.14-export-batch.md`; `docs/proofs/wp3.14-ledger.md`. EDIT (granted for DR-48, CHARC `6f725eee` item 3): `src/clearwater/jobs/disk_space.py` (`QUALITY_RATIO` values, `estimate_video_bytes`, the module and function docstrings) and `tests/test_jobs_disk_space.py` (the ratio and 10-bit tests). APPEND: `src/clearwater/jobs/__init__.py` (exports, and its docstring's "WP3.14 adds export and batch beside them" made true). NOT owned: `src/clearwater/jobs/export_seam.py` (the frozen seam; a change is a CHARC ruling), `naming.py`, `safe_write.py`, `tests/test_jobs_naming.py`, `tests/test_jobs_safe_write.py`; `src/clearwater/interfaces/`; `src/clearwater/io/`, `analysis/`, `core/`, `methods/`, `cache/`, `config/`, `color/`, `gui/`; `tools/video_io_bench.py`, `tools/video_fidelity.py` (imported, not edited); `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/fixtures/`; `pyproject.toml`, `uv.lock`. |
| Interfaces provided | The WP3.19 seam's `ExportJobs` protocol, implemented exactly as `export_seam.py` states it (task 2); the engine's constructor (question 4); the headless batch (question 9); `estimate_video_bytes` per DR-48 (question 7). No frozen interface changes. |
| Interfaces consumed | IF-8 `Progress`, `JobResult`; IF-5 `ProbeResult`, `VideoSource`, `VideoSink`, `SinkReport`, `EncoderCapability`; IF-6 `PhotoSource`, `PhotoSink`; IF-3 `CorrectionMethod` (`stages`, `analyze`, `render`); IF-2 `ArrayBackend` (`asarray`, `to_host`); IF-7 `ProxyCache`; IF-9 `ParameterSet`; IF-10 `Settings` (`output_folder`, `output_suffix`, `png_bit_depth`, `video_encoder`, `quality_level`, `ten_bit_for_eight_bit`, `provenance`, `force_cpu`); IF-1 `Image`, `Frame`. The seam names from `clearwater.jobs.export_seam` (never through `clearwater.gui`). |
| Consumers | WP4.3 (`install_export_panels(window, exports)` with this engine; start-up `remove_leftovers`), WP4.1 (the headless runner, V5, V8, V9, V10), WP4.2 (V4, V12), WP3.21 (this package's V16 row is its baseline), WP5.1 (V11), WP5.2 (V15, V16 re-measure). |
| Hardware flags | **EXCLUSIVE** on task 10 (plan 4.3: "Timings are taken on a full clip, not one frame"; frame rule 7: best effort, strays and clocks recorded, contaminated rows kept as spread); last, alone, OPEN/CLOSE posted by the orchestrator to CHARC. `gpu` on NVENC and CuPy legs (skip when absent). `footage` on GX011627 / GX011625 legs: read-only, through `tools/local_config.find_footage_file`; outputs under `work/` only. `slow` on the 5.3K synthetic leg. |
| Out of scope | WP3.21's optimisation (device-resident pipeline, upload/download overlap, faster 3C kernels, any frame-level parallelism beyond question 1); WP4.x wiring (start-up detection, `remove_leftovers` at start-up, the CREATE_NO_WINDOW spawn helper of AD-23, the GUI's `install_export_panels` call); the GUI (WP3.19's panels and `ActivityGate`); DR-52's `resolve_encoder` swap in `settings_dialog.py` (WP4.3); chapter concatenation and D80's grouping review (v2); any change to `src/clearwater/interfaces/`; decoding, parsing or logging any `gpmd` packet, IMU or GPS data; reading or logging any location tag. |
| Debt and decided items | **DR-48** (RULED 2026-10-27) -- CLOSES -- "estimated bytes = max(`QUALITY_RATIO[level]` x source size, AD-12 pixel-rate ceiling for the level x duration) x `MARGIN`, both encoders; the ceiling is `NVENC_BITS_PER_PIXEL` / `NVENC_RATE_SHARE[level]` x width x height x fps from `clearwater.io.video.encode` (FINAL constants) ... Drop the 10-bit doubling ... the message states the figure" (task 6, questions 6-8). **DR-35** -- (b) CLOSES for the engine ("one `Reservations` passed to both `plan_output` and `SafeWrite`; folder and suffix validated at export start"); (a) the reserved-name case is a readable job failure (a test), nothing overwritten; (c) not this package's (WP4.3 start-up); (d) not this package's. **DR-57** -- (a) ADDRESSED by tests: the V4 instrument (which hashes audio payloads) runs on this engine's outputs, not in the product job (question 13); (b) CLOSES: the cancel watchdog (question 2) calls `abort` from its own thread, which releases a blocked stdin write; (c) CLOSES as a stated limit: a temporary `abort` could not delete is reported as a `JobResult` warning and left for D85's next-start clean-up. **DR-28** -- (1) CLOSES by task 9's full-coverage verification and controls (question 16); (2) CLOSES by construction (no temporary exists before `SafeWrite.begin`; a refused export leaves nothing; a test); (3) CLOSES by the provenance key set (question 10); (4) closed by WP3.10; (5) does not apply (the product takes the request's path; no stem resolver). **DR-45** -- (a) must not be reached: no thread but the job's own closes a `FrameStream` (WP3.11's pattern); (b) not this package's (WP4.2), but the sink's `close` refuses a short frame set, so a strict-prefix decode fails the job rather than committing. **DR-47** -- not reached: one `AnalysisEngine` per job, its job callable run once on the job's thread (one writer). **DR-43** -- not this package's (question 14). **DR-20 (7)** -- CLOSES for the product: nothing is written after `commit()` and no earlier output is removed (a test). **DR-16** -- does not apply (WP3.13's rename; AD-25 (b)). **DR-52** -- not this package's (WP4.3); this package calls `resolve_encoder` itself. |
| Done | Plan 4.5; frame section 2 rules 1-11; ruff check, ruff format --check, mypy strict, full pytest green (in a granted window); every seam clause and every ruling line below shown by a named test; V4 SAME on every decodable WP2.3 video sample through the engine; V11's legs; DR-48, DR-35 (b), DR-57 (b) (c), DR-28 (1)-(3), DR-20 (7) closed; the V16 row recorded in an exclusive window; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the design table.** Before product code, in the ledger:
   - the engine's constructor and what is injected (question 4), and the module split;
   - the job's phases per kind and the thread layout (question 1); the progress units and
     messages per phase (question 15);
   - the cancel path: the watchdog, the order of the last cancel check, `close`, `commit` and the
     watchdog's stop (question 2); "committed before the stop" per kind (question 3);
   - the D87 estimate and refusal (questions 6-8), the provenance object (question 10);
   - the failure table: each failure (refused request, missing folder, bad suffix, refused probe,
     sidecar, decode error, encode error, disk full, cache error, method error) with its
     `JobResult.failure` text and what is left on disk (nothing);
   - the test list, the answers to the questions, the `scripts/cell_depth.py` figure your
     dispatcher gives you.

   YIELD for the dispatcher. A choice the brief leaves open is a STOP.
2. **The seam, exactly** (`export_seam.py` docstring, the WP3.19 report "The seam" items 1-6).
   `job(request)` builds the callable on the interface thread and touches no file ("a missing or
   unreadable source is the JOB's failure"; `ValueError` only for a request malformed in itself).
   The callable touches no Qt object, imports nothing from `clearwater.gui`, reports through
   `progress.report(done, total, message)`, checks `progress.cancelled()` between units of work,
   writes only through `SafeWrite` with a fresh `Reservations` per job passed to BOTH
   `plan_output` and `SafeWrite` (DR-35 (b)), and returns a `JobResult`:
   - ok: `ok` True, `outputs` naming AT LEAST ONE file (the path `commit()` returned), the
     warnings (the sink's `SinkReport.warnings`, D86, D54, the AD-9 fallback reason);
   - failure: `ok` False, `failure` a readable ASCII-safe reason that never equals `CANCELLED`;
   - cancel: `ok` False, `failure` IS `clearwater.jobs.export_seam.CANCELLED` (the constant
     itself; never `clearwater.analysis.CANCELLED`, never a copy of the string);
   - non-ok: `outputs` lists the files committed before the stop (question 3), `warnings` any
     raised before it;
   - `device` the backend reason of `select_backend` (`"GPU"`, `"CPU: forced"`, ...), `elapsed_s`
     wall seconds. A job that finishes ok after the cancel click is ok (WP3.19 state table).
   At job start: the output folder (when set) must exist and the suffix pass `validate_suffix`
   (WP3.13 consumer note (a): `MissingFolderError` is "the last net, not the first"); a sidecar
   (`is_sidecar`, D83) and a `kind` that does not match the file are readable failures.
3. **Photo job (8.1, IF-6).** Read (`PhotoReader`); method from the injected IF-3 mapping by
   `parameters.method`; backend by `select_backend(settings, h, w, method_id)` (D111, AD-9);
   statistics measured on the float32 block-mean proxy exactly as the preview measures them
   (`block_mean(pixels, proxy_factor(h, w))` cast to float32, each stage given the earlier
   results; equal bit for bit to `clearwater.gui.imaging.measure_statistics`, AD-4 "used unchanged
   for preview and export", V8); render; to host; D87 check (`estimate_photo_bytes` at
   `settings.png_bit_depth`); `plan_output(..., MediaKind.PHOTO, reservations)`; `with
   SafeWrite(plan, reservations) as w:` write to `w.temp_path` with provenance when
   `settings.provenance`; `commit()`. Cancel checked between every step and immediately before
   `commit`.
4. **Video job (8.2, data flow "video export (jobs)").** Probe; refuse a `"refuse"` fault by name
   (nothing written); backend by `select_backend`; an `AnalysisEngine` per job on the injected
   cache and source (question 5), its `analysis_job()` run to completion on the job's thread with
   the job's progress (AD-15: "a batch item needs no prior analysis"; AD-7: export waits for the
   whole clip); `resolve_encoder(settings.video_encoder, sink.capabilities())` (the ONE "auto"
   rule; an unavailable explicit encoder is the sink's D74 refusal, a readable failure, never a
   silent fall-back); bit depth 10 for a 10-bit source or `ten_bit_for_eight_bit`, else 8 (D76);
   D87 check (task 6); `plan_output(..., MediaKind.VIDEO, reservations)`; `with SafeWrite(...) as
   w: sink.open(probe, w.temp_path, encoder=..., quality=settings.quality_level, bit_depth=...,
   provenance=...)`; for every decoded frame in pts order: upload with the backend, `render(frame,
   params, engine.smoothed_record(pts, schema_hash=engine.schema_hash))`, to host, `sink.write`;
   then `sink.close()` and `commit()`. Every decoded frame is written (the sink's `close` refuses
   anything but the source's whole readable video: WP3.10 report section 3). The `SinkReport`
   warnings and `not_carried` items become `JobResult.warnings` (D86's warning included).
5. **Cancel and failure (G8, D44, V11; CHARC `6f725eee`).**
   - Cancel goes through the sink's `abort`: a watchdog (question 2) calls `sink.abort()` when
     `progress.cancelled()` turns True during the encode, so a write blocked on FFmpeg's stdin is
     released (DR-57 (b)); the job thread then sees the sink's `encoder_failed`, recognises the
     cancel, leaves the `SafeWrite` block (its `abort` tolerates the missing temporary) and returns
     `CANCELLED`.
   - The job never calls `close` after a cancel or a partial write: "a `close` after a partial
     write is refused by design" (the sink's `verify_failed`, "The video is incomplete").
   - A failure anywhere leaves no temporary and no final; the source and every earlier output are
     untouched (N8); the ORIGINAL error's readable text is the `failure` (a cleanup error is a
     log line or a warning, never the failure). Disk full is classified with `is_disk_full` and
     named (D87 "fails cleanly"). A temporary that could not be deleted is a warning (DR-57 (c)).
   - Nothing is written after `commit()` (DR-20 (7)).
6. **D87 and DR-48 (`disk_space.py`).** Per item, inside the job, before `SafeWrite.begin`, on the
   planned output's folder: `check_free_space(folder, needed)`; not enough is the job's failure
   with `SpaceCheck.message()` (it states both figures), nothing written (question 8). NEVER
   batch-wide (CHARC `6f725eee`: "per-item D87 check, no batch-wide"; this supersedes WP3.13's note
   "Sum the estimates per destination volume before one `check_free_space`" and the
   `check_free_space` docstring sentence "A batch sums its estimates per volume and checks once.",
   which this package replaces). The video estimate per DR-48: `max(QUALITY_RATIO[level] x
   source_size, ceiling_bits_per_s x duration_s / 8) x MARGIN`, with `ceiling_bits_per_s =
   NVENC_BITS_PER_PIXEL / NVENC_RATE_SHARE[level] x width x height x frame_rate` imported from
   `clearwater.io.video.encode` (never copied), the same for both encoders, no 10-bit doubling;
   `QUALITY_RATIO` values per question 6; the docstrings cite WP3.10 report 7.2 and DR-48 and drop
   "PROVISIONAL until WP3.10".
7. **Provenance (D91, AD-13, IF-9).** Built per question 10 when `settings.provenance`, None
   otherwise; the encoder recorded is the RESOLVED one (IF-10: "Provenance records the resolved
   encoder, never `"auto"`"); under `PROVENANCE_MAX_BYTES` (16 KiB: "the sink refuses over it")
   with headroom at the largest parameter set; no location value and no `gpmd`-derived value.
8. **Headless batch (question 9).** Items in order, one job each from the same engine; a failure
   is logged and the next item runs (D81); a cancel stops the running item (`CANCELLED`) and
   marks the rest not run (D45); completed outputs kept (G8); per-item results returned in order.
9. **Tests.**
   - Seam: `job()` on a missing source returns a callable and touches no file; each `JobResult`
     branch of task 2, `failure is CANCELLED` by identity; an ok result names at least one
     existing output; a planted engine returning `"cancelled"` built at run time fails by name.
   - Photo: one sample of each WP2.3 family (`jpeg-*`, `heic8-*`, `heic10-*`, `png8-*`,
     `png16-*`, `tiff8-*`, `jpeg-orient-port-o6`) to PNG at 8 and 16 bits; statistics equal
     `measure_statistics` (`gui`); provenance present and parseable when on, absent when off.
   - Video, V4 end to end: `vid-hevc8-bt709-full`, `vid-hevc10`, `vid-untagged`, `vid-vfr`,
     `vid-rotated`, `vid-truncated` through the engine (libx265 always, NVENC under `gpu`) and
     `tools/video_fidelity.py compare`: every MANDATORY and REQUIRED item SAME (DR-57 (a));
     `vid-truncated` warns (D86); `vid-hlg`, `vid-pq` and the `gopro-*-lrv` / `-thm` sidecars are
     readable failures with nothing written; a synthetic 5.3K 8:7 clip under `tmp_path` (`slow`).
   - DR-28 (1) per question 16: full coverage of every frame before encode; planted ±1
     statistics pts, a dropped frame and a duplicated frame each fail by name; a sampled
     decode-and-compare that a planted frame swap fails.
   - Cancel at each phase (before start, during analysis, mid-encode with a write blocked until
     `abort`, immediately before `commit`): `CANCELLED`, no temporary, no final, earlier outputs
     kept, `abort` called, `close` never; a cancel after `commit` is ok. Planted wrong
     implementations fail by name: `close` called on cancel; cancel polled only between frames
     (the blocked-write leg hangs past a bound); a batch-wide D87 check; the 10-bit doubling kept.
   - V11: an encoder killed mid-stream and a simulated disk full (an `ENOSPC` `OSError` from a
     sink or writer double) leave no partial output with a readable failure; a subprocess export
     killed mid-encode leaves only a temporary-shaped file that `remove_leftovers` removes, the
     source and earlier outputs untouched.
   - D87: needed above free (patched `shutil.disk_usage`) refuses before any write with both
     figures; a three-item batch whose second item does not fit: first and third ok, second
     failed. DR-48: the ratio term wins on a high-rate source, the ceiling term on a low-rate one;
     both encoders the same; bits/8; patching `NVENC_BITS_PER_PIXEL` changes the estimate (one
     source of the constant).
   - Settings: missing output folder, invalid suffix and DR-35 (a)'s reserved name are readable
     failures; one `Reservations` reaches both calls (a spy); D111/AD-9: `force_cpu` gives
     `device` "CPU: forced", a patched free memory under the estimate gives the CPU with its
     reason, the job's log line names both; `"auto"` without NVENC resolves to `libx265` and
     provenance records it.
   - Batch: D81 (the second of three fails: first and third ok, the failure logged); D45 (cancel
     during the second: third not run, first kept).
   - N8: the source byte-identical with its mtime unchanged after success, failure and cancel.
   - `footage` (`gpu`, `slow`, in a footage window): GX011627 through the engine, c3 defaults,
     NVENC 8-bit Standard, the instrument's summary all MANDATORY and REQUIRED SAME.
   - Static: importing `clearwater.jobs` loads no `clearwater.gui`, `clearwater.methods`,
     PySide6 or CuPy (WP3.13's `test_importing_jobs_loads_no_gui_methods_or_heavy_libraries`
     covers the new modules: run it, do not change it); no module under `jobs/` imports
     `clearwater.methods` or `clearwater.gui`; no module names a GPS or IMU key or opens a `gpmd`
     packet.
10. **V16 export row (EXCLUSIVE, LAST, best effort; questions 11 and 12).** The dispatcher grants
    the window after every other task, the review loop and the full suite; do not start it
    unasked. `tools/export_bench.py` runs the product engine end to end on full clips and records
    per run: frames, wall s/frame, min/min against D106's 25 min/min (0.834 s/frame at 30000/1001
    fps), the per-frame median / p90 / max, the analysis share, the strays, clocks and
    temperatures, peak process-tree RSS (FFmpeg children included) and peak graphics memory (N4),
    the NVENC proof, as WP3.10's floor row (report 7.3) did; records under `work/wp3.14/bench/`,
    nothing footage-derived committed. Send `WINDOW RELEASED: <summary>` at the end.

## Declared operating envelope

Windows 11; Python 3.12; FFmpeg 9.0.2 (gyan) with `hevc_nvenc` and `libx265`; the RTX 4070 Laptop
GPU or the CPU fallback; video sources inside WP3.9's and WP3.10's envelopes (MP4/MOV, HEVC or
H.264, 4:2:0, 8/10-bit, BT.709 or BT.601, the reproduced edit-list forms, at most the HERO13 track
set); photo sources inside WP3.6's (HEIC, JPEG, PNG, TIFF); the WP2.3 samples, synthetic clips
under `tmp_path`, GX011627 and GX011625; local NTFS or exFAT output; ONE export activity at a time
(the open source's export or one batch), one job per source in sequence; no other writer on the
same cache key while a job runs (question 5). Out of envelope: several concurrent jobs, network
shares, two processes sharing the cache folder, a job blocking past cancellation outside the
encode (DR-44 (c), WP4.3), other operating systems (portable code, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (Codex `-m gpt-6.1-sol -c model_reasoning_effort=high`, WSL transport, probe
  first), run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.14\rN\`; ledger `docs/proofs/wp3.14-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.10\r10\`
  (`run_review.sh`, `review-prompt.md`; keep the round files as there) and CHANGE its `-m` from the
  old pin `gpt-5.6-sol` to `gpt-6.1-sol` (pin moved 2026-10-27; the banner must read it); exclude
  `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - every seam clause and every ruling line below, against the running code;
  - cancel: no path ends in `close` after a partial write; a blocked write released by `abort`;
    `CANCELLED` the constant; nothing left on disk; a cancel after `commit` ok;
  - failure: the original error's text kept; no partial, no temporary; the source and earlier
    outputs untouched; nothing written after `commit`;
  - D87 per item, DR-48's formula and units, the constants imported, no 10-bit doubling;
  - statistics paired with the frame's own pts; every frame written; photo statistics as the
    preview measures them;
  - provenance size and content; `resolve_encoder` the only "auto" rule;
  - threads: one writer per cache key, no `FrameStream` closed from another thread, no Qt;
  - no `gpmd`, IMU or GPS data read; nothing in `interfaces/` or other packages changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate (Codex, the same pin).

## Notes for the cell

- **Yields.** Round 0: the table, then YIELD before product code. After each review round: END
  YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating; make NO change in the
  turn that adjudicates a round. Your dispatcher gives you the `scripts/cell_depth.py` figure at
  every gate: put it in the ledger; ~250K is the evaluation point ("REVIEW ONLY this turn" when
  told), ~400K STOP.
- **Windows (X5).** The full suite (about 4,766 tests, 27-45 min) runs ONLY in a window the
  dispatcher grants, in the background with `QT_QPA_PLATFORM=offscreen` and output under `work/`,
  kept company by foreground poll-wait calls on its done marker (a reaped run is not a result).
  Footage legs and the EXCLUSIVE V16 window are separate grants. Send `WINDOW RELEASED: <summary>`
  after each. Never two heavy jobs at once; 4K exports outside a window are heavy: ask.
- **Return report** = your FINAL message, under about 70 lines, delivered to your dispatcher by
  your messaging tool: the public API, the phase and thread table, the failure table, the cancel
  path, the D87 figures, the V4 table per sample, the V11 legs, the V16 row with its conditions,
  the DR dispositions, the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20), in `export_seam.py`, or
  in a file not owned (including WP3.9's `decode.py` for DR-45 (a), `io.photo` for DR-43); a
  dependency; OS-specific code; a seam clause the engine cannot honour; a V4 MANDATORY item lost
  end to end; any need to decode a `gpmd` packet or read a location tag; any write outside the
  planned temporary and `work/`; the round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with `git -c
  core.autocrlf=false commit -m "feat(wp3.14): ..." -- <paths>`, with a `Co-Authored-By:` footer
  naming your model; every committed blob LF. Never `git stash` (a WIP commit or a scratch copy).
  Never a bare `cd`. Never post to a mailbox. No dependency is added without CHARC. Footage
  read-only at `C:\Users\rwsmy\clearwater-footage\`; every output under `work/`. Gates: ruff check,
  ruff format --check, mypy strict, full pytest (in a window); no harness gate. Report
  `docs/reports/wp3.14-export-batch.md` (claims, evidence paths, limits, "Seam as implemented").
  GoPro IMU and GPS are out of scope: nothing from a `gpmd` track, IMU or GPS is committed, and no
  committed record carries a location tag.

## Rulings (CHARC `6f725eee`, 2026-10-27, item 3, and earlier rulings this brief carries)

Binding as written; where a ruling and the ladder or a question differ, the ruling governs.

- "an ok `JobResult` names at least one output; per-item D87 check, no batch-wide; `CANCELLED`
  returned as the constant; non-ok outputs list the files committed before the stop;
  QUALITY_RATIO figures from the WP3.10 report 7.2 with DR-48's rule (max(ratio x source, ceiling
  x duration) x margin, no 10-bit doubling); cancel goes through `abort`; a `close` after a
  partial write is refused by design; provenance under 16 KiB; `resolve_encoder` is the ONE
  "auto" rule (DR-52 swap at WP4.3)."
- The brief carries "WP3.19 seam items, DR-35, DR-48 as ruled, DR-57 (a)-(c), the WP3.10 consumer
  notes, the V16 row".
- WP3.10 rulings (CHARC `53d1d906e47fe2c9`): "`resolve_encoder` (Q4) is the ONE "auto" rule;
  WP3.20 and WP3.14 call it"; Q11 "BOTH rows: the export FLOOR row here ... and the V16/D106
  export row in WP3.14."
- WP3.19: the `ExportJobs` seam frozen at WP3.19's round 0, additive only until its accept (now a
  CHARC ruling to change); the seam moved to `clearwater.jobs.export_seam` (CHARC 2026-10-26,
  architecture IF-8); the non-ok `outputs` wording (CHARC `efc95f5d4e7b8456`). WP3.19 question 1:
  the GUI sequences its batch; WP3.14 supplies the per-item job.

### FINAL rulings on the questions (CHARC FINAL `3c3c35d7e40b525e` (2026-10-27 06:33Z, replying to `4b2d7b2e92048eaf`))

Approved: opus-high, Claude lane, Codex A/B at `gpt-6.1-sol`/high. The answers below govern the
"Questions for CHARC" section.

- Q1 threading: ADOPTED (one frame in flight, one watchdog per encode; overlap is WP3.21's; `hw_decode` True unless the backend is the CPU).
- Q2 cancel granularity: ADOPTED (per frame, between phases, immediately before `commit`; watchdog 0.2 s calls `abort` once; never touches the FrameStream).
- Q3 committed before the stop: ADOPTED (held by construction; the planted stop-after-commit test lists the file).
- Q4 engine dependencies: ADOPTED (injected methods mapping, source, sink factory, photo reader/writer, cache + key function, backend selector; `jobs` never imports `clearwater.methods`).
- Q5 analysis in the job: ADOPTED (own `AnalysisEngine` per job on the injected cache; a cache `RuntimeError` is a readable failure; GUI-recompute-during-export serialisation becomes a NEW DR row at the accept, WP4.3 trigger).
- Q6 QUALITY_RATIO: ADOPTED High 1.10 / Standard 0.50 / Draft 0.25, MARGIN 1.25 (busy libx265 1.07 measured; the ceiling term bounds NVENC).
- Q7 `estimate_video_bytes` signature: ADOPTED in place (`source_size, settings, *, width, height, frame_rate, duration_s`; `source_bit_depth` dropped with the doubling).
- Q8 D87 warn or refuse: ADOPTED REFUSE before writing, batch continues (D81). Reading of record: 8.4's "warned" is satisfied by the refusal message the user sees (the panel's error, the batch report); a refusal is stricter than the text, not a relaxation, so no owner decision. In a headless batch there is no one to warn, which settles it. WP4.3 may add a proceed-anyway confirmation in the GUI if the owner asks at CP5; the engine's rule stays refuse.
- Q9 headless `run_batch`: ADOPTED (small; D81 skip-and-log, D45 stop, per-item results, count summary; the GUI keeps its own sequencing).
- Q10 provenance key set: ADOPTED, file NAME not path. RULED and applied (the pre-dispatch commit, main `ba28175`: IF-9 docstring amended, AD-13 amended). No `GoProInfo`, no tag dictionary, no location value.
- Q11 V16 instrument `tools/export_bench.py`: ADOPTED (imports from `tools/video_io_bench.py`, `run`/`v16`/`--dry-run`; cold-cache figure of record, warm beside it; stage split from Progress callbacks and an injected clock, no product timers).
- Q12 footage rows: ADOPTED IN FULL, GX011625 KEPT (the sustained row is what N6 measures and it is WP3.21's baseline; the WP3.10 floor used the same clip). Order: GX011627 rows first, GX011625 LAST, each its own OPEN/CLOSE; if the GX011625 window cannot be granted within the package's life, the row is recorded OWED in the accept record and taken before WP3.21 dispatches, never dropped.
- Q13 DR-57 (a): ADOPTED (instrument-side hash on the engine's outputs, not in the product job).
- Q14 DR-43: ADOPTED, not this package's (stays WP3.6P / `io.photo`).
- Q15 progress units: ADOPTED.
- Q16 DR-28 (1): ADOPTED (full-coverage digest before encode plus controls; sampled order criterion after encode).
- Flag (i) spec 10.2 N6 body "about 3.3 minutes per minute" vs D106/V16's interim 25 min/min: an OWNER text erratum like D75; CHARC carries it (v0.5.6 candidate); nothing blocks.
- Flag (ii) WP3.13's per-volume batch-sum note and the `check_free_space` docstring sentence: superseded; the cell edits the docstring sentence as an owned file (`disk_space.py`); the WP3.13 report is NOT edited (a one-line "superseded by WP3.14" note goes in WP3.14's report).
- Flag (iii) the copied WP3.10 runner's old pin: the cell changes `-m` to `gpt-6.1-sol` before the first round; a round whose banner reads 5.6 is void.

## Questions for CHARC (recommended answer first)

1. **Threading model.** Recommended: one job runs on the caller's worker thread, sequentially
   decode -> upload -> render -> to host -> encode, one frame in flight (FFmpeg's decoder and
   encoder already run concurrently with Python through their pipes); plus one watchdog thread
   per video encode (question 2). No frame-level parallelism or overlap: that is WP3.21's ("upload/
   download overlap"), and this row is its baseline; N4's bound holds by construction (WP3.10's
   floor peaked at 2,065 MiB tree RSS with NVENC, 3,519 MiB with libx265). `hw_decode` True
   unless the backend is the CPU (WP3.9 falls back to software itself without CUDA).
2. **Cancel granularity.** Recommended: `progress.cancelled()` checked before each frame, between
   analysis and encode, between photo steps and immediately before `commit`; during the encode a
   watchdog thread polls it every 0.2 s (WP3.10's `POLL_S`) and calls `sink.abort()` once (WP3.10
   report 9: "A cancel from another thread should call `abort`"); the analysis phase cancels
   through the progress the engine already checks; the watchdog never touches the `FrameStream`
   (DR-45 (a)); the job thread closes its decode iterator in a `finally`. The watchdog stops before
   `close`; a cancel seen after that and before `commit` aborts; after `commit` the result is ok.
3. **"Committed before the stop".** Recommended: one job = one source = at most one output, and a
   file is committed only by `SafeWrite.commit()`'s rename; nothing fallible runs after it, so a
   non-ok result has `outputs` `()` in practice for both kinds, and the rule is held by
   construction plus a test that a stop raised after `commit` (planted) still lists the file. In
   the headless batch each item's result lists its own output; the batch keeps completed items'.
4. **Engine dependencies.** `jobs` may not import `clearwater.methods` (plan 8.1: "`gui` and
   `jobs` reach correction methods only through IF-3"; WP3.13's import test). Recommended: the
   engine is constructed with injected `methods: Mapping[str, CorrectionMethod]`, a video source,
   a sink factory (one `VideoSink` per job), a photo reader and writer, the proxy cache with its
   key function, and the backend selector (default `select_backend`); WP4.3 wires the real ones,
   tests and `tools/export_bench.py` pass real or double instances.
5. **Analysis inside the job and the cache.** Recommended: each video job builds its own
   `AnalysisEngine` on the injected cache (a complete entry skips the decode pass, V17) and never
   shares the GUI's engine. `DiskProxyCache` allows "One store call at a time per key", so a GUI
   recompute of the same clip during its export is outside this envelope: a cache `RuntimeError`
   becomes a readable failure with nothing written, and serialising the two is recorded as a WP4.3
   note (a new DR) rather than built here.
6. **`QUALITY_RATIO` values** (`src/clearwater/jobs/disk_space.py`, owned here for DR-48).
   Recommended: High **1.10**, Standard **0.50**, Draft **0.25**, `MARGIN` 1.25 unchanged. Reason:
   the ceiling term bounds NVENC by construction, so the ratio term binds only for libx265 (no
   ceiling) on high-rate sources; WP3.10 report 7.2 measured busy libx265 file ratios about 1.07 /
   0.486 / 0.25 (rounded up to 0.05); the calm ratios (1.19 / 0.54 / 0.28) sit far under the
   ceiling term. Alternative: keep 1.0 / 0.5 / 0.25 (`MARGIN` already covers every measured row).
7. **`estimate_video_bytes`' signature.** DR-48 needs width, height, frame rate and duration; the
   function's only caller is its own test. Recommended: change it in place to
   `estimate_video_bytes(source_size, settings, *, width, height, frame_rate, duration_s)` (the
   source's coded size, `probe.video.frame_rate` as `nvenc_rate` uses, `probe.duration_s`),
   dropping `source_bit_depth` with the doubling. Alternative: a second function beside it (two
   rules for one estimate).
8. **D87: warn or refuse.** 8.4 says "the user warned if insufficient"; DR-48 speaks of "D87's
   refusal". Recommended: the job refuses before writing (`ok` False, `failure` =
   `SpaceCheck.message()`), which IS the warning the user sees (the panel's error, the batch
   report), and the batch continues (D81). Alternative: proceed with a warning and rely on the
   clean disk-full failure.
9. **A headless batch in `clearwater.jobs`.** WP3.19 question 1 (ruled) left it optional ("if it
   wants a headless batch for WP4.1's runner, the same semantics on its side"); the plan row gives
   WP3.14 "the batch queue ... and an end-of-run report". Recommended: yes, small: `run_batch`
   (items in order, D81 skip-and-log, D45 stop, per-item `JobResult`s, a count summary) for
   tests, the V16 tool and WP4.1's runner; the GUI keeps its own sequencing and does not call it.
   Alternative: no engine-side batch; WP4.1 loops itself.
10. **Provenance key set (DR-28 (3)).** Recommended: AD-13's object (`format_version`, `method`,
    `parameters`, `created`, `app_version`) plus `source` (file name, size, mtime and a probe
    summary: container, codec, width, height, bit depth, frame rate, duration, frame count, colour
    description; no tag dictionary, no `GoProInfo`) and `settings` (resolved encoder, quality, bit
    depth, device); for photos the same minus the video fields. The source's file NAME, not its
    full path (IF-9 says "path"; a full path carries the owner's folder names into every shared
    file). Alternative: the full path as IF-9 reads.
11. **The V16 instrument.** Recommended: `tools/export_bench.py` (owned here, X1-style as WP3.10's
    floor row), importing `StrayWatch`, `Telemetry`, `conditions`, `tree_rss`, `gpu_reading` and
    `rate` from `tools/video_io_bench.py` (not edited), with `run` and `v16` subcommands and a
    `--dry-run`; the figure of record is the export job as a batch item runs it (cold cache:
    analysis included, D106 "end to end"), with a warm-cache run (complete entry, as File > Export
    after analysis) beside it; the per-stage split comes from timing the Progress callbacks and an
    optional injected clock (None in the product), never from product-code timers.
12. **The footage and the window.** The owner records one mode (inventory: "3840x2160 @ 29.97
    hevc 8-bit 4:2:0: 34"). Recommended rows, all at the defaults (AD-8 method c3; G12 encoder
    auto = NVENC, quality Standard; 8-bit as the source): GX011627 full clip x 3 cold, x 1 warm;
    GX011627 x 1 with `ancuti2018` and x 1 with libx265; GX011625 full clip (14,938 frames) x 1
    cold, the sustained row; the synthetic
    5.3K 8:7 clip's memory peaks recorded for V15 (WP5.2 measures). Estimate at about 0.6-0.7
    s/frame (WP3.4 core 0.439 + WP3.10 floor 0.155): about 45 min for the GX011627 rows and 2.5-3
    h for GX011625. Alternative: drop the GX011625 row (about 1 h window).
13. **DR-57 (a), the audio hash.** Recommended: not in the product job; the V4 instrument (which
    hashes audio packets) runs on this engine's outputs in the V4 tests and on the V16 outputs
    (DR-57 (a) "may run the V4 hash as an opt-in check").
14. **DR-43** (a damaged EXIF block dropped with a log line only). Recommended: not this
    package's: the register says "A fix needs a reader-side signal (an IF-6 field or a warnings
    channel)", and `io.photo` is not owned; the row stays with WP3.6P. Alternative: the photo job
    turns `clearwater.io.photo` WARNING records logged on its thread into `JobResult.warnings`.
15. **Progress units.** Recommended: analysis passes the engine's own `(done, total, message)`
    through with "Analysing <name>"; the export phase reports frames written of
    `probe.video.nb_frames` (total None when absent) with "Exporting <name>"; a photo reports
    steps 0..4 of 4.
16. **DR-28 (1), the verification shape.** Recommended: in tests on a short synthetic clip, a
    recording sink wrapper digests every corrected frame before encode and compares it with an
    independent render of the same pts with `smoothed_record(pts)` (full coverage); controls for
    ±1 statistics pts, a drop and a duplicate; after encode, sampled frames decoded and each
    checked closer to its own corrected frame than to its ±1 neighbours (an order criterion, so
    the lossy encode needs no pixel tolerance). The sink's own `close` already checks count and
    every pts (D94).

## Return report

Your FINAL message, under about 70 lines, to your dispatcher by your messaging tool (never a
mailbox): the public API and module list; the phase, thread and cancel table; the failure table;
`QUALITY_RATIO` and the estimate for a busy and a calm 4K clip; the V4 table per sample;
the V11 legs; the V16 rows with their conditions and moments; every ruling line above as
honoured-on-disk; the DR dispositions; the gates with their summary lines; the Reviewer A rounds,
ledger and verdict; deviations and open items.
