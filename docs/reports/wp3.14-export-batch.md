# WP3.14 report: export jobs and batch

Package `clearwater.jobs`: NEW `export.py` (the engine), `batch.py` (the headless batch), `provenance.py` (the D91
object); EDITED `disk_space.py` (DR-48) and `jobs/__init__.py` (exports); the V16 instrument `tools/export_bench.py`;
tests `tests/test_jobs_export.py`, `test_jobs_export_support.py`, `test_jobs_export_photo.py`,
`test_jobs_export_video.py`, `test_jobs_batch.py`, `test_jobs_disk_space.py` (edits), `test_export_bench.py`. Spec
v0.5.5 (section 8, G7, G8; D43-D45, D80, D81, D83-D87, D106, D111; N4, N6 interim; V4, V11, V16), architecture FINAL
1.0 (IF-5, IF-6, IF-8 with its "Export seam" paragraph, IF-9, IF-10; AD-4, AD-7, AD-9, AD-12, AD-13, AD-15). Base main
`9753b7b`. Rulings: brief FINAL CHARC `3c3c35d7e40b525e` (Q1-Q16, Flags (i)-(iii)); round 0 (orchestrator gen 13: O1-O4,
the video order ruling); R1 (orchestrator gen 14) and CHARC `e7d25105` (Q2 amended: the watchdog through `close`); R2
(orchestrator gen 14: G1/G2 not defects, the loop terminates). Ledger: `docs/proofs/wp3.14-ledger.md`. One GRANTED
edit outside the package (CHARC `d9154e06`, Reviewer B B1 (b)): `src/clearwater/analysis/engine.py` (origin WP3.11), the
decode pass's `finally` close guarded, nothing else in that module, no interface change. Otherwise nothing under
`src/clearwater/interfaces/`, `io/`, `analysis/`, `core/`, `methods/`, `cache/`, `config/`, `color/` or `gui/` was
changed; `export_seam.py`, `naming.py`, `safe_write.py` untouched; no dependency.

## Modules and public names

| Module | Public names | Imports (beyond stdlib, NumPy, `clearwater.interfaces`) |
|---|---|---|
| `jobs/export.py` | `ExportEngine` (implements `ExportJobs`), `effective_parameters`, `is_reserved_device_name`, `RESERVED_DEVICE_NAMES`, `BackendSelector` | `clearwater.jobs` (naming, safe writing, disk space, `export_seam`, provenance), `clearwater.analysis` (`AnalysisEngine`, its `CANCELLED`, `block_mean`, `proxy_factor`), `clearwater.io.video` (`is_sidecar`, `sidecar_fault`, `resolve_encoder`, the error types, `POLL_S`, `ascii_text`) |
| `jobs/batch.py` | `run_batch(exports, requests, progress) -> BatchReport`, `BatchItem`, `BatchReport` (`counts`, `lines()`) | `clearwater.jobs.export_seam` only (runs any `ExportJobs`) |
| `jobs/provenance.py` | `provenance_object`, `video_source_summary`, `photo_source_summary` | `clearwater.interfaces` only |
| `jobs/disk_space.py` | `estimate_video_bytes(source_size, settings, *, width, height, frame_rate, duration_s)`, `QUALITY_RATIO`, `MARGIN` | `clearwater.io.video.encode` read as a module at call time (one source of the constants) |

Constructor (Q4, everything injected): `ExportEngine(*, methods, video_source, sink_factory, photo_reader, photo_writer,
cache, cache_key, select_backend, app_version=clearwater.__version__, on_stage=None)`. `job(request)` raises
`ValueError` only for a request malformed in itself and touches no file. `jobs` imports nothing from
`clearwater.gui`, `clearwater.methods`, `clearwater.core` or `clearwater.io.photo`.

## Seam as implemented (WP3.19 `export_seam`)

- ok: `outputs` = the one path `commit()` returned; `warnings` = the sink's `SinkReport.warnings` (D54, D86, the
  level warning), one `"Not carried to the output: <item>"` per `not_carried`, the probe's `gp_log` warn fault, the AD-9
  CPU fallback reason, a leftover-temporary warning when one was left.
- failure: `ok` False, a readable ASCII text that starts with the file name (so never `CANCELLED`); the ORIGINAL
  error's text (a cleanup error is a log line).
- cancel: `failure` IS `clearwater.jobs.export_seam.CANCELLED` (identity).
- non-ok: `outputs` lists the files committed before the stop; a job commits at most one output and nothing after its
  `commit` can fail it (a raising `committed` stage hook or final progress report is a WARNING line, Reviewer B B3), so
  the engine's non-ok results carry none; `warnings` those raised before the stop (the sink's included once `close`
  returned).
- `device` the `select_backend` reason (`"none"` before the backend is chosen); `elapsed_s` wall seconds; one INFO line
  per job naming the file, the outcome and the device.
- One fresh `Reservations` per job passed to both `plan_output` and `SafeWrite` (DR-35 (b)).

## Phases and threads (Q1, Q2 as amended, Q15)

| Kind | Phases on the job thread (cancel checked before each, and per frame) |
|---|---|
| both | settings: output folder exists, `validate_suffix`, method id known, `is_sidecar` (D83) |
| photo | read -> `select_backend` -> measure (float32 block-mean proxy, stages in order: equal to `gui.imaging.measure_statistics` bit for bit) -> render -> to host -> `plan_output` + reserved-name rule -> D87 -> "Writing" report -> cancel check -> `SafeWrite` -> write (provenance when on) -> cancel check -> `commit` (a write or commit error while `cancelled()` holds is `CANCELLED`, its text to INFO). Progress `0..4 of 4`. |
| video | probe -> refuse a `"refuse"` fault -> `select_backend` -> `resolve_encoder` (D74 refusal) -> bit depth -> `plan_output` + reserved-name rule -> D87 -> analysis (own `AnalysisEngine`, inline, AD-7/AD-15) -> D87 re-check -> `SafeWrite` -> `sink.open` -> frames (upload, render with `smoothed_record(pts)` of that frame, to host, `write`) -> cancel check -> `close` -> watchdog joined -> post-close cancel check -> `commit`. Progress: the analysis engine's own, then `(frames written, nb_frames, "Exporting <name>")`. |

Threads: the job thread does every step, one frame in flight. Beside it: WP3.9's decoder FFmpeg and WP3.10's encoder
FFmpeg with their stderr daemons, and ONE watchdog per encode, alive from after `open` until `close` has returned or
raised, then stopped and JOINED before the post-close check and `commit` (no second thread at the rename). The
watchdog polls `progress.cancelled()` every 0.2 s and calls `sink.abort()` once; it never touches a `FrameStream`; every
stream is closed on the job thread (DR-45 (a)). One `AnalysisEngine` per job, run once (DR-47 not reached).

## Cancel path (G8, D44, D45; DR-57 (b))

Before every phase and frame: `cancelled()` -> stop. Analysis: a non-ok analysis result while `cancelled()` holds (or
its own `CANCELLED`) -> the seam's `CANCELLED`, read from the flag, never the text; a different text (a cleanup error
that replaced the analysis's outcome) goes to an INFO line (Reviewer B B1). Encode and
close: the watchdog's `abort` kills FFmpeg, releasing a blocked write or a flushing `close`; the job reads the cancel
from the flag (or the watchdog having fired), never from the error text, and logs the stopped encoder's error. A cancel
after the last frame never calls `close`; `close` is never called after a partial write; the post-close check is
unconditional (an `Exception` from `close` or a report). After any stop past `open` the job calls `abort` and leaves the
`SafeWrite` block, which deletes the temporary. After `commit` the result is ok with its output: the `committed` stage
hook and the final progress report each run guarded, and an error from either is a WARNING line (Reviewer B B3).

## Failure table (every row: `ok` False, `outputs` (), the source and earlier outputs untouched, nothing on disk)

| Failure | `failure` text |
|---|---|
| malformed request | `ValueError` from `job()` (nothing built) |
| unknown method / missing folder / bad suffix | `<name>: unknown correction method '<id>'` / `<name>: the output folder does not exist: <folder>` / `<name>: <validate_suffix message>` |
| reserved device name (DR-35 (a), O1) | starts with the file name; refused before `begin` on every OS |
| sidecar (D83), missing or wrong-kind source, refused probe (HLG, PQ) | the fault's, probe's or reader's message |
| D87 short of space | `SpaceCheck.message()` (needed and free) |
| analysis or cache error | `<name>: analysis failed: <text>` |
| encoder refused / unavailable (D74) | the `VideoEncodeError` message |
| decode, encode, verify, method error | the original error (readable types shown bare, others `<Type>: <message>`) |
| disk full | `<name>: disk full while writing <final>: <original>` when `is_disk_full` holds on the error or its cause/context chain |
| temporary not deletable | the original failure plus a warning; the temporary left for D85's next-start clean-up (DR-57 (c)) |

## D87 and DR-48 (Q6-Q8)

Per item, inside the job, before `SafeWrite.begin` and again after the analysis: `check_free_space(plan.folder,
needed)`; short is the job's failure, nothing written, a batch continues (D81). Never batch-wide. Video: `needed =
ceil(max(QUALITY_RATIO[level] x source_size, NVENC_BITS_PER_PIXEL / NVENC_RATE_SHARE[level] x W x H x fps x duration_s /
8) x MARGIN)`, exact fractions until the ceiling, both encoders, no 10-bit doubling; `QUALITY_RATIO` High 1.10 /
Standard 0.50 / Draft 0.25 and `MARGIN` 1.25, each an exact `Fraction` (11/10, 1/2, 1/4, 5/4; a binary-float 1.10 gave
1,375,001 bytes for a 1,000,000-byte source at High, Reviewer B B4). Example (4K 29.97, 60 s, Standard): ceiling 29.8 Mb/s -> 223.7 MB x 1.25 =
279.7 MB; a busy 900 MB source -> ratio 450 MB x 1.25 = 562.5 MB (ratio wins); a calm 49 MB source -> 279.7 MB. The
footage figures: GX011627 105,909,120 B and GX011625 2,323,157,760 B at Standard (both ceiling-bound; V16 section).

**Superseded by WP3.14:** WP3.13's note "Sum the estimates per destination volume before one `check_free_space`" (and
the `check_free_space` docstring sentence "A batch sums its estimates per volume and checks once.", replaced in
`disk_space.py`) -- the check is per item (CHARC `6f725eee`).

## Provenance (D91, AD-13, IF-9)

`ParameterSet(method, effective parameters, created, app_version, source, settings).to_dict()` when
`settings.provenance`, else None. `source`: the file NAME, size, mtime; video adds container, codec, size, bit depth,
frame rate, duration, frame count, colour tags. `settings`: the RESOLVED encoder (never `"auto"`), quality, bit depth,
device (video); PNG bit depth, device (photo). No tag dictionary, no `GoProInfo`, no location, nothing from `gpmd`. The
largest parameter set's JSON stays under half of `PROVENANCE_MAX_BYTES` (16 KiB).

## Claims and evidence (tests; E = `test_jobs_export.py`, V = `_video`, P = `_photo`, B = `_batch`, D = `test_jobs_disk_space.py`, X = `test_export_bench.py`)

| # | Claim | Evidence |
|---|---|---|
| 1 | Seam: `job()` builds without touching a file; `ValueError` only for a malformed request; each result branch; `CANCELLED` by identity | E `test_job_builds_without_touching_any_file`, `test_job_raises_value_error_only_for_a_malformed_request`, `test_ok_video_names_its_committed_output_and_carries_the_sink_warnings`, `test_cancel_returns_the_seam_constant_itself`, `test_a_genuine_failure_never_equals_cancelled`; planted `test_planted_engine_returning_a_copy_of_the_string_fails_by_name` |
| 2 | Cancel at each phase, during the analysis with a raising stream close, an analysis error after a cancel, on the photo's "Writing" report and inside its writer, a blocked write released, before close, inside close at four timings (double) and three (product sink), before commit, after commit | E `test_cancel_at_each_phase_leaves_nothing`, `test_a_cancel_during_the_analysis_survives_a_raising_stream_close`, `test_an_analysis_error_after_a_cancel_is_cancelled` (planted `test_planted_analysis_cancel_read_from_the_text_fails_by_name`), `test_a_cancel_on_the_photo_writing_report_never_calls_the_writer`, `test_a_photo_writer_error_after_a_cancel_is_cancelled` (planted `test_planted_no_cancel_check_before_the_photo_write_fails_by_name`), `test_cancel_releases_a_write_blocked_on_the_encoder`, `test_a_cancel_at_the_close_boundary_aborts_without_closing`, `test_a_cancel_during_close_is_aborted_by_the_watchdog_at_every_timing`, `test_cancel_immediately_before_commit_deletes_the_finished_temporary`, `test_a_cancel_after_commit_is_ok`, `test_the_watchdog_is_joined_before_commit`; V `test_a_cancel_mid_encode_leaves_nothing_and_keeps_earlier_outputs`, `test_a_cancel_during_the_product_sinks_close_is_aborted_and_leaves_nothing`; planted `test_planted_cancel_polled_only_between_frames_hangs_past_the_bound`, `test_planted_close_on_cancel_fails_by_name` |
| 3 | Failure keeps the original text; nothing left; disk full named; cleanup errors never the failure; leftovers warned; nothing after commit | E `test_disk_full_*` (3), `test_an_encoder_killed_mid_stream_keeps_the_original_error`, `test_a_method_error_leaves_nothing_and_never_closes`, `test_a_close_error_without_a_cancel_keeps_its_text`, `test_a_stream_close_error_never_replaces_the_original_failure`, `test_a_method_failure_during_the_analysis_survives_a_raising_stream_close` (planted `test_planted_bare_analysis_stream_close_fails_by_name`), `test_a_clean_path_analysis_stream_close_error_is_a_warning` (planted `test_planted_close_guard_only_while_an_error_is_in_flight_fails_by_name`), `test_a_clean_path_stream_close_error_is_the_failure`, `test_a_temporary_*` (3), `test_a_raising_callback_after_commit_keeps_the_result_ok` (video and photo, progress and stage; planted `test_planted_unguarded_callback_after_commit_fails_by_name`), `test_nothing_is_written_after_commit_and_earlier_outputs_are_untouched`, `test_a_stop_after_close_keeps_the_sink_warnings`; planted `test_planted_every_close_error_cancelled_fails_by_name`, `test_planted_always_quiet_stream_close_fails_by_name` |
| 4 | D87 per item, re-checked after analysis, both figures; DR-48 formula, units, one constant source, no 10-bit doubling | E `test_d87_refuses_before_any_write_with_both_figures`, `test_d87_is_re_checked_after_the_analysis`, `test_d87_is_per_item_in_a_batch` (B refused by D87, by its text, before its analysis; valid stat fields); planted `test_planted_batch_wide_d87_fails_by_name`, `test_planted_no_d87_fails_the_per_item_test_by_name`; D `test_video_*` (5), `test_high_ratio_is_the_exact_decimal` (the oracle reads the ruled decimals from text) |
| 5 | Settings refusals, DR-35 (a)/(b), D111/AD-9, the one "auto" rule, provenance | E `test_a_missing_output_folder_is_a_readable_failure`, `test_an_invalid_suffix_is_a_readable_failure`, `test_an_unknown_method_is_a_readable_failure`, `test_a_sidecar_is_a_readable_failure`, `test_dr35a_*`, `test_reserved_device_names`, `test_one_fresh_reservations_per_job_reaches_plan_output_and_safe_write` (planted `test_planted_shared_registry_fails_by_name`), `test_force_cpu_and_the_fallback_reason`, `test_auto_without_nvenc_resolves_to_libx265_and_provenance_records_it`, `test_an_unavailable_explicit_encoder_fails_before_the_analysis`, `test_provenance_*` (2) |
| 6 | Photo: one sample per still family to PNG 8 and 16; statistics equal the preview's bit for bit; provenance on/off | P `test_each_still_family_exports_to_png`, `test_photo_statistics_equal_the_previews_bit_for_bit`, `test_provenance_is_absent_when_off` |
| 7 | V4 end to end, every decodable WP2.3 sample, libx265 and NVENC (`gpu`), all MANDATORY and REQUIRED SAME; refused samples write nothing; 5.3K 8:7; GX011627 (`footage`) | V `test_v4_every_decodable_sample_through_the_engine`, `test_refused_samples_fail_readably_with_nothing_written`, `test_v4_synthetic_5k3_8_7_clip`, `test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` |
| 8 | DR-28 (1): every frame rendered with its own statistics, written once, in order; controls fail by name | V `test_dr28_every_frame_is_rendered_with_its_own_statistics`, `test_dr28_planted_wrong_engines_fail_the_coverage_check` (pts +1, -1, dropped, duplicated), `test_dr28_a_planted_frame_swap_fails_the_sampled_order_check` |
| 9 | V11: encoder killed, disk full, a killed export process leaves only a temporary that `remove_leftovers` removes | V `test_v11_an_encoder_killed_mid_stream_leaves_no_partial_output`, `test_v11_a_killed_export_process_leaves_only_a_temporary_that_is_cleaned_up`; E disk-full rows |
| 10 | Batch: D81, D45, a raising job is a failed item, a cancel before the batch runs nothing | B (4 tests) |
| 11 | N8 and static: source byte-identical with mtime after success, failure, cancel; no gui/methods import; no GPS/IMU/`gpmd` name | E `test_n8_the_source_is_untouched_after_success_failure_and_cancel`, `test_no_jobs_module_imports_methods_or_gui_or_reads_gps`, `test_the_telemetry_name_guard_catches_a_planted_name`; WP3.13's `test_importing_jobs_loads_no_gui_methods_or_heavy_libraries` (run, unchanged) |
| 12 | The V16 instrument: plan per Q12, phases from stamps, per-frame intervals, D106 verdict, records under `work/wp3.14/bench/`, footage untouched, measurement order (strays, telemetry, sampler) | X (14 tests) |

V4 samples through the engine (libx265 always; NVENC under `gpu`, both ran): `vid-hevc8-bt709-full`, `vid-hevc10`,
`vid-untagged`, `vid-vfr`, `vid-rotated`, `vid-truncated` (D86 "cut short" warning): every MANDATORY and REQUIRED item
SAME, frame count equal, N8. Refused with nothing written: `vid-hlg`, `vid-pq`, the four GoPro `.LRV`/`.THM` samples.
Synthetic 5.3K 8:7 (5312x4648, 9 frames, `slow`): passed. GX011627 (NVENC 8-bit Standard, c3): passed (772 s, window of
2026-10-27 07:58Z).

## Gates

- ruff check, ruff format --check, mypy strict (136 files): clean at the final head.
- Full pytest at `7bb5d85` (granted window, 2026-10-27 08:11Z-08:50Z, offscreen): 4864 passed, 10 skipped, 17
  deselected (footage), 0 failed. The skips are not this package's: 9 in `test_methods_assembly_v8.py` (the worktree's
  `work\` has no `wp1.3\frames`; main's configuration runs them), 1 in `test_color_roundtrip.py` (skipped by design).
- After the remediation (targeted, the host shared): the engine, batch, disk-space, bench and photo files 121 passed;
  `test_jobs_export_video.py -m "not footage"` 29 passed (all its slow legs); after the R2 cleanup the engine and bench
  files 87 passed and the three product close timings 3 passed; the close and commit subsets 30 and 10 consecutive
  clean runs. The full suite on the merge candidate is the orchestrator's (stacked gate).
- Failing first: every remediation test failed by its reason on the engine before its fix (ledger, R1 and F1 (b)
  records); test-only fixes carry a planted control that fails by name.
- After the Reviewer B pass 1 remediation (cell 4, targeted, >= 11 GB free): ruff check, ruff format --check, mypy (136
  files) clean; the engine, disk-space and batch files 101 passed; the photo file and the video file's DR-28, cancel and
  product-close legs 26 passed; the bench, naming and safe-write files 175 passed. Failing first: the ten new tests
  failed on the unfixed engine (the B1 test on the close error's text, the B3 tests on the callback's failure text, B4
  on 1,375,001 bytes, the planted controls on their missing seams).
- After the granted B1 (b) edit (`analysis/engine.py`): ruff, format, mypy clean; the nine analysis files
  (`test_analysis_*`, `test_gui_analysis_service.py`) with the engine, disk-space and batch files 350 passed. Failing
  first: the B1 (b) test failed on the close error's text (`'clip.mp4: analysis failed: OSError: cleanup close
  failed'`), its planted control on the unguarded close.

## Reviewer A (STRONG; WSL codex-cli 0.162.1, `gpt-6.1-sol`, effort high; evidence `clearwater-review-evidence\wp3.14\r1`, `r2`)

| Round | Head | Verdict | Findings |
|---|---|---|---|
| R1 | `7bb5d85` | NEW_CRITICAL_MAJOR_FOUND | 2 MAJOR (no cancel coverage during `close`; the stream's close error replaced the original), 6 MINOR (leftover after a successful commit, sink warnings lost before commit, three vacuous or weak test guards, telemetry stop order); all confirmed and fixed; the first MAJOR through CHARC's Q2 amendment |
| R2 | `c3a2fc9` | NEW_CRITICAL_MAJOR_FOUND, adjudicated zero new blocking | 1 MAJOR ruled NOT A DEFECT (a `KeyboardInterrupt`/`SystemExit` propagates past the post-close check; reproduced: `abort` called, nothing left), 7 MINOR (one ruled not a defect with it; six fixed in the terminating round's cleanup) |

The loop TERMINATED at R2 (zero new blocking). Reviewer B is the orchestrator's seat pass on the merge candidate.
Pass 1 (`wp3.14-mc` `b830412`) BLOCKED; rulings: B1 (a) the cancel half fixed (`_check_analysis`); B1 (b) the
method-failure half GRANTED (CHARC `d9154e06`) and fixed in `src/clearwater/analysis/engine.py` (origin WP3.11; the
decode pass's `finally` close guarded, an `Exception` logged at WARNING, a `BaseException` still propagates; the ONLY
change there, no interface change); B2 (V16 owed) declined as sequencing; B3 fixed (`_after_commit`); B4 fixed (exact
fractions). Pass 2 (`99171df` = `b4259cc`) BLOCKED with 1 MAJOR (a photo cancel on the "Writing" report reached
the writer, and a writer ENOSPC after it became a disk-full failure), 2 MINOR (the per-item D87 test's fabricated stat
let B fail in provenance; this report's scope line) and 1 ADVISORY (no clean-path analysis-close discriminator);
adjudicated at the gate (no pass 3): all four fixed in one gate-fix series, verified by the orchestrator by execution.

## Limits

- One frame in flight; no frame-level parallelism or upload/download overlap (WP3.21).
- A `BaseException` that is not an `Exception` (`KeyboardInterrupt`, `SystemExit`) propagates out of a job by design and
  is never turned into a result; the sink's `abort` and the `SafeWrite` block still remove the temporary (R2 ruling).
  G1: reproduced in `clearwater-review-evidence\wp3.14\r2\f1-repro.txt` (the interrupt propagates, tail [close, abort],
  only the sources remain); WP5.1's V11 leg re-checks it.
- Windows: the F1 (b) test double's 1-in-23 flake was two unlinkers of one file (the double's `abort` and its
  stopped-encoder cleanup racing on the temporary, `PermissionError`); both were made non-raising (test-only), then 30
  consecutive clean runs.
- A genuine failure that coincides with a cancel is reported as `CANCELLED` (the cancel is read from the flag); its text
  goes to the log.
- A real encoder disk full during the encode is named by FFmpeg's own text; `is_disk_full` classifies an `OSError` chain.
- D87 per item: items that each fit but together do not fill the volume fail the later item cleanly.
- A temporary that could not be removed is a warning and is left for D85's next-start clean-up (`remove_leftovers`, a
  WP4.3 start-up call).
- The reserved-name rule (O1) is a portability guard: Windows 11 build 26300 creates `NUL.MP4` as an ordinary file.
- The job analyses the clip itself even when the GUI already has (the cache makes it cheap); serialising a GUI recompute
  against a running export is WP4.3's (a NEW DR row at the accept, Q5).
- WP3.10's sink sets `"closed"` after its finish even when an `abort` landed in between (the output is then deleted and
  `close` still returns a report); the job's post-close check cancels. CHARC banks a MINOR row against `encode.py`.
- A cancel blocked outside the encode (for example a long decode during the analysis) waits for the next check (out of
  envelope, DR-44 (c), WP4.3).
- Since the granted B1 (b) edit, an `Exception` from the analysis decode stream's `close` is a WARNING line on every path,
  including a pass that decoded every frame (the statistics are complete by then); WP3.14's own export stream keeps its
  clean-path close error as the failure (R2 G8).

## Debt dispositions

DR-48 CLOSED (the ruled formula, constants imported, no 10-bit doubling). DR-35 (b) CLOSED (one fresh registry per job
to both calls; folder and suffix validated at start); (a) a readable refusal on every OS (O1); (c), (d) not this
package's. DR-57 (a) ADDRESSED (the V4 instrument hashes audio on the engine's outputs); (b) CLOSED (the watchdog's
`abort`, now through `close`); (c) CLOSED as a stated limit (a warning). DR-28 (1) CLOSED (full coverage plus controls,
sampled order); (2) CLOSED (nothing exists before `begin`; a refused export leaves nothing); (3) CLOSED (the provenance
key set); (5) does not apply. DR-45 (a) not reached; (b) WP4.2's (the sink's `close` refuses a short frame set). DR-47
not reached. DR-20 (7) CLOSED. DR-43, DR-52, DR-16 not this package's.

## V16 (ladder item 10)

`tools/export_bench.py v16` on `2e1dc11` (product engine end to end: probe, the clip's whole analysis, per-frame render,
encode, mux and verification), defaults c3, encoder auto, Standard, 8-bit as the source; EXCLUSIVE windows, the host
otherwise idle (CHARC holding), best effort on the shared laptop. Records under `work/wp3.14/bench/`
(`export-bench-v16-gx011627-20261027T113337Z.json`, `-synthetic-5k3-20261027T124545Z.json`,
`-gx011625-20261027T130513Z.json`); nothing footage-derived committed. D106 interim: 25 min/min = 0.834 s/frame at
30000/1001. Every run ok, every frame written, both exits 0.

| Run | Frames | s/frame | min/min (D106) | Per frame median / p90 / max (s) | Analysis share | Phases s: probe / analysis / open / frames / close->committed | Peak tree RSS | Peak GPU mem | NVENC proof |
|---|---|---|---|---|---|---|---|---|---|
| GX011627 c3 cold 1/3 | 681 | 1.0654 | 31.93 MISS | 0.740 / 0.767 / 0.888 | 30.4 % | 1.72 / 220.3 / 0.44 / 502.4 / 0.672 | 2819 MiB | 2409 MiB | tied |
| GX011627 c3 cold 2/3 | 681 | 1.0611 | 31.80 MISS | 0.739 / 0.763 / 0.850 | 30.4 % | 1.03 / 219.9 / 0.43 / 500.7 / 0.627 | 2848 MiB | 2409 MiB | tied |
| GX011627 c3 cold 3/3 | 681 | 1.0631 | 31.86 MISS | 0.743 / 0.766 / 0.872 | 30.2 % | 0.72 / 218.7 / 0.38 / 503.5 / 0.636 | 2850 MiB | 2409 MiB | tied |
| GX011627 c3 warm (cache complete at start) | 681 | 0.7743 | 23.21 meets | 0.745 / 0.773 / 0.874 | 3.6 % | 0.79 / 19.2 / 0.47 / 506.1 / 0.673 | 2852 MiB | 2409 MiB | tied |
| GX011627 ancuti2018 cold | 681 | 0.7202 | 21.58 meets | 0.423 / 0.452 / 0.583 | 40.9 % | 0.76 / 200.5 / 0.42 / 288.2 / 0.556 | 2834 MiB | 2409 MiB | tied |
| GX011627 c3 libx265 cold | 681 | 1.1877 | 35.60 MISS | 0.861 / 0.951 / 1.192 | 26.5 % | 0.75 / 214.3 / 0.41 / 579.4 / 14.026 | 4109 MiB | 1937 MiB | none (libx265) |
| synthetic 5.3K 8:7 c3 cold (5312x4648) | 150 | 4.5389 | 136.03 MISS | 3.714 / 4.006 / 4.438 | 16.6 % | 6.80 / 112.8 / 0.39 / 560.0 / 0.832 | 6354 MiB | 6104 MiB | tied |
| GX011625 c3 cold, sustained | 14,938 | 1.0429 | 31.26 MISS | 0.737 / 0.769 / 1.437 | 29.8 % | 2.64 / 4638.2 / 0.86 / 10,935.2 / 1.870 | 2903 MiB | 2450 MiB | tied |

The per-frame figures are the intervals between successive `Exporting` reports (decode, upload, render, download and
write of one frame), the first frame apart; close->committed is the stamp gap from the `close` stage to `committed`
(flush, mux, verification and the rename: the cancel-latency window the R1 F1 discussion named).

**D106 is missed on cold c3 at 4K, as measured: 31.3-31.9 min/min against 25.** The rows are recorded as WP3.21's
baseline (CHARC `7ce2b89f`: a measured figure, not a stop, not a defect).
- The split: cold c3 1.061-1.065 s/frame (GX011627) and 1.043 (GX011625) = the analysis pass (about 30 % of the wall
  time) + the frame path at about 0.74 s/frame. Warm c3 0.774 s/frame (23.2 min/min) and ancuti2018 cold 0.720 (21.6)
  meet. The frame path alone is within D106 at 4K; the cold miss is the analysis pass plus the c3 cost, consistent with
  WP3.10's floor row (I/O 0.154-0.156 s/frame) and WP3.4's c3 core (0.439 s/frame). WP3.21's targets are the analysis
  pass (overlap or device-resident) and the 3C Gaussian, as D106 lists.
- Observation for WP3.21: during GX011625's 77-minute analysis phase the GPU sat at idle clocks (median SM 210 MHz,
  5.1 W, 59 C), so the pass looks CPU- or decode-bound.
- libx265 (cold 35.6 min/min, MISS; its close 14.0 s against 0.6-0.7 s with NVENC): the CPU encode is the fallback
  path, not the measured mode. Recorded; no action.
- 5.3K 8:7 cold: 136 min/min, peak 6.2 GiB tree RSS and 6.0 GiB graphics memory: "supported, best-effort on speed"
  (D106); N4's 16 GB respected. Its first frame took 10.6 s (the first 4K frame about 1 s).
- Every output carries two warnings, "Not carried to the output: camera firmware tag" and "...: camera settings atoms
  (moov/udta)": D86 and WP3.10's sink behaviour as designed, not a regression.
- GX011625 thermals: no degradation. Frames phase first hour median 0.7549 s/frame (p90 0.7775), last hour 0.7263 (p90
  0.7475); GPU median 82 C / 1590 MHz SM / 51.7 W in the first hour, 79 C / 1620 MHz / 51.9 W in the last; peak 93 C.
  Twelve intervals exceeded 1.0 s (max 1.437 s).

Conditions and moments (UTC, 2026-10-27; GPU clocks and temperature from `nvidia-smi` before and after each run):

| Window | Runs | Before / after |
|---|---|---|
| Block 1, 11:33:36Z-12:57:47Z (free memory 11.72 GB, then 11.87 GB before the 5.3K row; the GX011627 legs ran back to back in one invocation) | GX011627 cold 1/3 11:33:43-11:46:02, 2/3 11:46:08-11:58:24, 3/3 11:58:31-12:10:47, warm 12:14:27-12:23:27, ancuti2018 12:23:34-12:31:56, libx265 12:32:02-12:45:42; 5.3K 12:46:08-12:57:46 | idle clocks before (SM 210 MHz; 1980 MHz before runs 1 and 7), 60-70 C before, 68-72 C after; CPU 1-11 % before; strays: none foreign during any run (the runner's `bash.exe`, 32 % for 0.5 s, before run 1 only) |
| Block 2, 13:05:12Z-17:25:11Z (free memory 11.7 GB, disk 46.7 GB) | GX011625 13:05:18-17:25:09 | SM 210 MHz, 54 C, CPU 2.2 % before; SM 210 MHz, 70 C, CPU 2.4 % after; no foreign stray over 15,579 s |

Telemetry errors: 0 on every run. Outputs: GX011627 85,975,154 B (NVENC c3), 85,727,426 B (ancuti2018), 123,813,667 B
(libx265); GX011625 1,794,336,305 B; each under its D87 estimate below.

D87 at Standard from each clip's probe (`estimate_video_bytes`; ceil(max(0.50 x source, ceiling) x 1.25)):
GX011627 (3840x2160 at 29.970, 22.72 s, source 158,509,660 B): ratio term 79,254,830 B, ceiling term 84,727,296 B,
estimate 105,909,120 B (ceiling wins). GX011625 (3840x2160 at 29.970, 498.43 s, source 425,926,523 B): ratio term
212,963,262 B, ceiling term 1,858,526,208 B, estimate 2,323,157,760 B (ceiling wins).
