# WP3.14 report: export jobs and batch

Package `clearwater.jobs`: NEW `export.py` (the engine), `batch.py` (the headless batch), `provenance.py` (the D91
object); EDITED `disk_space.py` (DR-48) and `jobs/__init__.py` (exports); the V16 instrument `tools/export_bench.py`;
tests `tests/test_jobs_export.py`, `test_jobs_export_support.py`, `test_jobs_export_photo.py`,
`test_jobs_export_video.py`, `test_jobs_batch.py`, `test_jobs_disk_space.py` (edits), `test_export_bench.py`. Spec
v0.5.5 (section 8, G7, G8; D43-D45, D80, D81, D83-D87, D106, D111; N4, N6 interim; V4, V11, V16), architecture FINAL
1.0 (IF-5, IF-6, IF-8 with its "Export seam" paragraph, IF-9, IF-10; AD-4, AD-7, AD-9, AD-12, AD-13, AD-15). Base main
`9753b7b`. Rulings: brief FINAL CHARC `3c3c35d7e40b525e` (Q1-Q16, Flags (i)-(iii)); round 0 (orchestrator gen 13: O1-O4,
the video order ruling); R1 (orchestrator gen 14) and CHARC `e7d25105` (Q2 amended: the watchdog through `close`); R2
(orchestrator gen 14: G1/G2 not defects, the loop terminates). Ledger: `docs/proofs/wp3.14-ledger.md`. Nothing under
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
| photo | read -> `select_backend` -> measure (float32 block-mean proxy, stages in order: equal to `gui.imaging.measure_statistics` bit for bit) -> render -> to host -> `plan_output` + reserved-name rule -> D87 -> `SafeWrite` -> write (provenance when on) -> cancel check -> `commit`. Progress `0..4 of 4`. |
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
footage figures for GX011627 and GX011625 are recorded with the V16 rows.

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
| 2 | Cancel at each phase, during the analysis with a raising stream close, a blocked write released, before close, inside close at four timings (double) and three (product sink), before commit, after commit | E `test_cancel_at_each_phase_leaves_nothing`, `test_a_cancel_during_the_analysis_survives_a_raising_stream_close` (planted `test_planted_analysis_cancel_read_from_the_text_fails_by_name`), `test_cancel_releases_a_write_blocked_on_the_encoder`, `test_a_cancel_at_the_close_boundary_aborts_without_closing`, `test_a_cancel_during_close_is_aborted_by_the_watchdog_at_every_timing`, `test_cancel_immediately_before_commit_deletes_the_finished_temporary`, `test_a_cancel_after_commit_is_ok`, `test_the_watchdog_is_joined_before_commit`; V `test_a_cancel_mid_encode_leaves_nothing_and_keeps_earlier_outputs`, `test_a_cancel_during_the_product_sinks_close_is_aborted_and_leaves_nothing`; planted `test_planted_cancel_polled_only_between_frames_hangs_past_the_bound`, `test_planted_close_on_cancel_fails_by_name` |
| 3 | Failure keeps the original text; nothing left; disk full named; cleanup errors never the failure; leftovers warned; nothing after commit | E `test_disk_full_*` (3), `test_an_encoder_killed_mid_stream_keeps_the_original_error`, `test_a_method_error_leaves_nothing_and_never_closes`, `test_a_close_error_without_a_cancel_keeps_its_text`, `test_a_stream_close_error_never_replaces_the_original_failure`, `test_a_clean_path_stream_close_error_is_the_failure`, `test_a_temporary_*` (3), `test_a_raising_callback_after_commit_keeps_the_result_ok` (video and photo, progress and stage; planted `test_planted_unguarded_callback_after_commit_fails_by_name`), `test_nothing_is_written_after_commit_and_earlier_outputs_are_untouched`, `test_a_stop_after_close_keeps_the_sink_warnings`; planted `test_planted_every_close_error_cancelled_fails_by_name`, `test_planted_always_quiet_stream_close_fails_by_name` |
| 4 | D87 per item, re-checked after analysis, both figures; DR-48 formula, units, one constant source, no 10-bit doubling | E `test_d87_refuses_before_any_write_with_both_figures`, `test_d87_is_re_checked_after_the_analysis`, `test_d87_is_per_item_in_a_batch`; planted `test_planted_batch_wide_d87_fails_by_name`; D `test_video_*` (5), `test_high_ratio_is_the_exact_decimal` (the oracle reads the ruled decimals from text) |
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

## Reviewer A (STRONG; WSL codex-cli 0.162.1, `gpt-6.1-sol`, effort high; evidence `clearwater-review-evidence\wp3.14\r1`, `r2`)

| Round | Head | Verdict | Findings |
|---|---|---|---|
| R1 | `7bb5d85` | NEW_CRITICAL_MAJOR_FOUND | 2 MAJOR (no cancel coverage during `close`; the stream's close error replaced the original), 6 MINOR (leftover after a successful commit, sink warnings lost before commit, three vacuous or weak test guards, telemetry stop order); all confirmed and fixed; the first MAJOR through CHARC's Q2 amendment |
| R2 | `c3a2fc9` | NEW_CRITICAL_MAJOR_FOUND, adjudicated zero new blocking | 1 MAJOR ruled NOT A DEFECT (a `KeyboardInterrupt`/`SystemExit` propagates past the post-close check; reproduced: `abort` called, nothing left), 7 MINOR (one ruled not a defect with it; six fixed in the terminating round's cleanup) |

The loop TERMINATED at R2 (zero new blocking). Reviewer B is the orchestrator's seat pass on the merge candidate.
Pass 1 (`wp3.14-mc` `b830412`) BLOCKED; rulings: B1 the cancel half fixed (`_check_analysis`), the method-failure half
BANKED (Limits); B2 (V16 owed) declined as sequencing; B3 fixed (`_after_commit`); B4 fixed (exact fractions).

## Limits

- One frame in flight; no frame-level parallelism or upload/download overlap (WP3.21).
- A `BaseException` that is not an `Exception` (`KeyboardInterrupt`, `SystemExit`) propagates out of a job by design and
  is never turned into a result; the sink's `abort` and the `SafeWrite` block still remove the temporary (R2 ruling).
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
- A method failure during the cold analysis's decode pass whose decode stream's `close` then raises is reported with
  the close error's text, not the method's: `analysis/engine.py` (WP3.11's module, lines 494-497) closes the stream
  unguarded in a `finally`. The product decoder suppresses its own close errors, so only an injected source reaches it.
  BANKED (Reviewer B B1, the method-failure half); trigger: the next touch of `analysis/engine.py`.

## Debt dispositions

DR-48 CLOSED (the ruled formula, constants imported, no 10-bit doubling). DR-35 (b) CLOSED (one fresh registry per job
to both calls; folder and suffix validated at start); (a) a readable refusal on every OS (O1); (c), (d) not this
package's. DR-57 (a) ADDRESSED (the V4 instrument hashes audio on the engine's outputs); (b) CLOSED (the watchdog's
`abort`, now through `close`); (c) CLOSED as a stated limit (a warning). DR-28 (1) CLOSED (full coverage plus controls,
sampled order); (2) CLOSED (nothing exists before `begin`; a refused export leaves nothing); (3) CLOSED (the provenance
key set); (5) does not apply. DR-45 (a) not reached; (b) WP4.2's (the sink's `close` refuses a short frame set). DR-47
not reached. DR-20 (7) CLOSED. DR-43, DR-52, DR-16 not this package's.

## V16 (ladder item 10)

OWED: the export rows (GX011627 x3 cold, x1 warm, x1 ancuti2018, x1 libx265; synthetic 5.3K 8:7; GX011625 LAST), each
in its own EXCLUSIVE window, taken by the next cell with `tools/export_bench.py`; this section is replaced with the rows,
their conditions and the D87 footage figures.
