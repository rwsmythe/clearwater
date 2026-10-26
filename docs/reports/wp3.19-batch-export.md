# WP3.19 report: batch queue and export progress

Package `clearwater.gui` (`export_panel.py`, `batch_panel.py`, `export_service.py`) plus one granted new file
`clearwater.jobs.export_seam` (`src/clearwater/jobs/export_seam.py`); tests `tests/test_gui_export_panel.py`,
`tests/test_gui_batch_panel.py`. Spec v0.5.4 (G7, G8, G9; D43-D45, D81, D83; V7, V11 GUI leg), architecture FINAL 1.0
(IF-8, IF-9, IF-10; AD-15, AD-20, AD-25 (a)). Base `718324b`. Rulings: brief CHARC `53d1d906e47fe2c9`; round 0 CHARC
`0e6962c39f216c86` (seam approved, the extra file granted, C2-C7 accepted). Ledger: `docs/proofs/wp3.19-ledger.md`.
Nothing under `src/clearwater/interfaces/`, `config/`, `core/`, `io/` was changed; no existing file under
`src/clearwater/gui/` or `jobs/` was edited (`gui/__init__.py` and `jobs/__init__.py` untouched); no dependency.

## Modules and public names

| Module | Public names |
|---|---|
| `jobs/export_seam.py` (stdlib + `clearwater.interfaces` only; loads no PySide6) | `CANCELLED`, `UNAVAILABLE_TEXT`, `ExportRequest`, `ExportJobs`, `unavailable_exports` |
| `gui/export_service.py` (no Qt class) | re-exports the five seam names; `Activity`, `ActivityGate`, `SharedGate`, `RUNNING_EXPORT_REASON`, `RUNNING_BATCH_REASON` |
| `gui/export_panel.py` | `install_export_panels(window, exports=None)`, `export_panel_factory(exports, gates)`, `ExportPanel`, `OWNER`, `READY_TEXT` |
| `gui/batch_panel.py` | `batch_panel_factory(exports, gates, *, choose_files=None)`, `BatchPanel`, `BatchItem`, `ItemState`, `format_report`, `OWNER`, `CURRENT_PARAMETERS` |

`install_export_panels` attaches "Export" and "Batch" to `Area.JOBS` with one shared `ActivityGate` and, with
`exports=None`, the product default `unavailable_exports()`.

## The seam (frozen at the round-0 yield, additive only until accept)

`ExportRequest(source, kind, parameters, settings)` (frozen); `ExportJobs.job(request) -> Callable[[Progress], JobResult]`;
`CANCELLED = "cancelled"`; `unavailable_exports()`. Contract (in the `ExportJobs.job` docstring):

1. `job()` is called on the interface thread and touches no file: a missing or unreadable source is the JOB's failure,
   never an exception at build time (`ValueError` only for a request malformed in itself).
2. The callable runs on a worker thread, touches no Qt object, reports `(done, total, message)` (total None = busy bar),
   checks `progress.cancelled()` between units of work.
3. It writes through safe writing: a cancel or failure leaves no partial output and no temporary; a committed output is
   never removed (G8, D44, V11).
4. A video's analysis (AD-15) is inside the job, so a batch item needs no prior analysis.
5. Success `ok` True with `outputs` and `warnings`; failure `ok` False with the readable `failure` (`outputs` lists any file
   committed before the stop, normally none); cancel `ok` False with `failure == CANCELLED` (the constant itself; reserved: no genuine failure text equals it). Cancel and failure are told
   apart only by that string.
6. One job per source with a fresh `Reservations`: output-name collisions across batch items are caught by the
   filesystem scan at each plan (D34-D36), not by shared state.

Minor 3 of Reviewer A round 2 (wording of item 5 for `outputs` on a non-ok result): RULED by CHARC `efc95f5d4e7b8456`,
applied in `export_seam.py`: "on a non-ok result, `outputs` lists any file committed before the stop (normally none)"
(and `warnings` any warning raised before it), consistent with "an output already committed is never removed". Wording
only; no name or signature changed. The panel keeps whatever `outputs` and `warnings` a result carries.

## State tables

Export panel (`ExportPanel`):

| State | Status | Bar | Cancel | Caller reason on `actions.export` |
|---|---|---|---|---|
| idle | last result or "Ready." | 0 of 1 | disabled | None (or "A batch is running." while a batch runs) |
| running | "Exporting <file>..." then the job's message | determinate, busy when total is None | enabled | "An export is running." |
| cancelling | "Cancelling..." | as running | disabled | "An export is running." |

Result: ok -> "Saved <names>", the panel's errors cleared (owner `"export"`), each warning a warning with owner
`"export"`; `failure == CANCELLED` -> "Export cancelled." and no error; otherwise an error naming the file (owner
`"export"`). A job that finishes ok after the click is saved (the output is kept). At trigger the panel's earlier warnings
are cleared. Everything after the gate is taken is inside one guarded block; the panel's state and the gate are released
before anything is presented.

Batch item states (`ItemState`): queued, running, done, done with warnings, failed, cancelled, not run.

| From | Event | To |
|---|---|---|
| (absent) | Add (route ok, not a duplicate) | queued |
| any | Start (all rows reset, report cleared) | queued |
| queued | previous item ended, no cancel | running |
| queued | previous item ended after a cancel | not run |
| running | ok, no warnings / ok with warnings | done / done with warnings |
| running | not ok, `failure != CANCELLED` (D81) | failed; the next item starts |
| running | not ok, `failure == CANCELLED` (click or the runner's own cancel) | cancelled; the rest not run (D45) |
| running | `job()` or `run()` raises | failed (text = the exception); the next item starts |
| running | a fault while recording | failed ("internal error: ..."); the next item starts |

The run ends when no row is queued or running: the gate is released first, then the report is built, shown and logged at
INFO. Warnings and outputs are kept for every outcome.

## Report layout (read-only text view, kept until the next Start; same text at INFO)

```
Batch finished: 5 items.            (or "Batch cancelled: ...", when any item is cancelled or not run)
Succeeded 1, with warnings 1, failed 1, cancelled 1, not run 1.
1. a.mp4 - done
   output: <path>
2. b.jpg - done with warnings
   output: <path>
   warning: <text>
3. c.mp4 - FAILED
   failure: <text>
4. d.mp4 - cancelled
5. e.mp4 - not run
```

The five counts partition the items. Layout is asserted by `test_the_report_layout`.

## Claims and evidence

| # | Claim | Evidence (tests; `test_gui_export_panel.py` = EP, `test_gui_batch_panel.py` = BP) |
|---|---|---|
| 1 | File > Export starts one job for the open source with a snapshot request; progress reaches the bar (busy for no total); success, warnings, failure, cancel shown as above | EP `test_triggering_exports_the_open_source_with_a_snapshot_request`, `test_progress_reaches_the_bar_and_a_missing_total_is_a_busy_bar`, `test_success_clears_only_the_export_errors_and_presents_warnings`, `test_failure_is_an_error_naming_the_file_with_owner_export`, `test_a_job_that_raises_is_a_failed_export`, `test_a_job_that_cannot_be_built_is_a_failed_export`, `test_cancel_shows_cancelled_and_leaves_no_partial_output`, `test_a_job_that_finishes_ok_after_a_cancel_keeps_its_output` |
| 2 | `actions.export` only through `set_unavailable`; the shell's reasons (no source, AD-15) always hold; the reason is cleared after every run, also after a presenter fault, a setup fault, a job that cannot be built | EP `test_install_clears_the_not_available_reason`, `test_the_shells_reasons_still_hold_after_install`, `test_ad15_clearing_this_packages_reason_leaves_the_shells_reason`, `test_the_reason_while_running_and_after`, `test_the_reason_is_cleared_even_when_the_presenter_raises`, `test_the_reason_is_cleared_when_setup_raises_after_the_gate_is_taken`, `test_the_reason_is_cleared_when_building_the_request_raises`; planted: `test_planted_set_enabled_during_analysis_is_detected`, `test_planted_request_built_outside_the_guard_holds_the_gate` |
| 3 | G7/D81: a failed item is skipped, logged and reported; the rest run | BP `test_a_failed_item_is_skipped_logged_and_reported`, `test_a_job_that_cannot_be_built_or_raises_fails_its_item_only`, `test_a_fault_while_recording_an_item_never_leaves_the_batch_running`; planted `test_planted_batch_that_stops_at_the_first_failure_is_detected` |
| 4 | One parameter set or preset for every item, resolved once at Start; settings snapshot at Start; an unavailable-method, invalid or vanished preset, or an invalid current set, refuses the start | BP `test_one_parameter_set_and_settings_apply_to_every_item_and_are_fixed_at_start`, `test_a_preset_is_applied_to_every_item`, `test_a_preset_the_methods_cannot_use_refuses_the_start` (2 cases), `test_a_preset_deleted_after_it_was_chosen_refuses_the_start`, `test_the_current_parameters_are_validated_too`, `test_the_start_refusal_is_cleared_by_the_next_start`; planted `test_planted_current_parameters_without_validation_are_detected` |
| 5 | D45/G8: cancel stops the whole remaining batch; no job starts after it; completed outputs are kept and the cancelled item leaves no temporary | BP `test_cancel_stops_the_remaining_items_and_keeps_completed_outputs`, `test_an_item_that_finishes_ok_after_the_cancel_is_done_and_the_rest_not_run`, `test_a_cancelled_result_without_a_click_also_stops_the_batch`; planted `test_planted_cancel_that_lets_the_next_item_start_is_detected` |
| 6 | D83: sidecars and unsupported extensions are refused with a `"batch"` warning; duplicates (normcase of abspath) are not queued; Add, Remove selected, Clear | BP `test_refused_files_are_warned_about_and_duplicates_are_not_queued`, `test_the_add_remove_and_clear_buttons` |
| 7 | One activity at a time; queue editing locked while running; Start unavailable while an export runs; the batch needs no open source and ignores AD-15 | BP `test_editing_is_locked_while_running_and_export_is_unavailable`, `test_start_is_unavailable_while_an_export_runs`, `test_the_batch_needs_no_open_source_and_no_analysis`; EP `test_activity_gate_allows_one_activity_and_survives_a_failing_subscriber`, `test_shared_gate_creates_one_gate` |
| 8 | The end-of-run report lists counts, outputs, warnings (also of failed and cancelled items) and failures; stays until the next Start; Start re-runs the whole queue | BP `test_the_report_layout`, `test_the_report_stays_until_the_next_start_and_start_runs_the_whole_queue_again`, `test_warnings_of_failed_and_cancelled_items_are_kept_and_reported`, `test_outputs_committed_before_a_failure_or_cancel_are_kept_and_reported`, `test_warnings_are_counted_and_listed_per_item`; planted `test_planted_record_that_clears_outputs_of_a_non_ok_result_is_detected` |
| 9 | DR-44 (b): every message carries an owner; another owner's error survives | EP `test_success_clears_only_the_export_errors_and_presents_warnings`; BP `test_another_owners_error_survives_the_batch` |
| 10 | Nothing heavy or Qt on the wrong thread: jobs run on worker threads; `job()` is built on the main thread; V7 bound | EP `test_the_export_job_runs_on_a_worker_thread`, planted `test_planted_export_run_on_the_main_thread_is_detected`, `test_v7_interface_never_waits_more_than_100_ms_during_an_export`; BP `test_v7_interface_never_waits_more_than_100_ms_during_a_batch` |
| 11 | The product default fails with "Export is not available in this build." and writes nothing; the seam loads no PySide6 | EP `test_the_unavailable_default_fails_and_writes_nothing`, `test_the_product_default_reports_that_export_is_unavailable`, `test_the_seam_module_loads_no_pyside6`, `test_the_gui_module_re_exports_the_seam`; `tests/test_gui_deps.py` (run, unchanged) |
| 12 | A source change does not cancel a running export (ruling Q5) | EP `test_the_open_source_changing_does_not_cancel_the_export` |

The test-side `StubExportJobs` writes through the real `plan_output` and `SafeWrite` with one `Reservations` per job, so
the G8 cleanup legs (no temporary, no final file after a cancel) run through the real safe-write machinery.

## V7 (D66)

The bound (a 10 ms `QTimer` probe never waits more than 100 ms) is asserted while a ~2 s NumPy export, and while a batch of
two ~1 s NumPy items, run. Observed maxima (informational, not a performance figure; one run on the shared laptop, 2026-10-26 20:21Z, nothing
else heavy running): 13 ms during the export, 11 ms during the batch.

## Gates

- ruff check, ruff format --check, mypy strict: green on the final head (see the ledger for the commands' last lines).
- Own modules plus `tests/test_gui_deps.py`, headless (`QT_QPA_PLATFORM=offscreen`), final head: 61 passed in 10 s
  (`work/t1-final.txt`). The two round-2 cleanup tests first errored at teardown (the window's close saves
  `session.parameters`, which the test had left patched); fixed in the test helper, then green.
- full pytest: run by the orchestrator on the merge candidate (stacked gate).
- Mutation checks of the new tests (`work/mut.py`, each mutation reverted): the batch stopping at the first failure, a
  cancelled result not stopping the rest, an export clearing every owner's errors, no gate release in the export result,
  duplicates or sidecars not refused, live parameters instead of the Start snapshot: each makes a named test fail
  (ledger, round 1). One equivalent mutant: `start()`'s own `gate.current` guard (the `try_start` after it is the real one).
- Deviation, disclosed: the tests were written after the product code, so there is no red-first run; the evidence that
  each check distinguishes is the planted tests and the mutations above; the round-1 regression tests were shown failing
  on the unfixed head `8639afb` (`clearwater-review-evidence\wp3.19\r2\regression-on-8639afb.txt`).

## Reviewer A (STRONG; WSL codex-cli, gpt-5.6-sol, effort high; evidence `clearwater-review-evidence\wp3.19\r1`, `r2`)

| Round | Head | Verdict | Findings |
|---|---|---|---|
| 1 | `8639afb` | NEW_CRITICAL_MAJOR_FOUND | 2 major, 1 minor: F1 the export gate stayed held when setup after `try_start` raised (fixed, confirmed by a scratch repro); F2 warnings of failed and cancelled items dropped (fixed); F3 the current parameters' validation untested (test added) |
| 2 | `735dd5f` | NO_NEW_CRITICAL_MAJOR | 3 minor: request-construction variant of F1's test (added), outputs of a non-ok result kept (test added), seam wording on `outputs` of a non-ok result (see above) |

Terminated at round 2 by the dispatcher's ruling (zero new blocking). Reviewer B: the orchestrator's seat pass on the
merge candidate.

## Limits

- The engine is WP3.14's (wave 4): every test runs against the test-side stub; the product default writes nothing until
  WP4.3 wires the real jobs. The open source's export re-reads the file by path (it does not reuse the preview's image).
- A batch-wide disk-space check (D87, WP3.13's "sum the estimates per volume") is impossible with one job per item: each
  job checks its own item. For WP3.14's brief.
- A job that blocks past cancellation keeps the gate held until its `on_done` arrives (DR-44 (c), WP4.3). A job that holds
  the GIL in pure Python can break V7 (WP4.3 re-measures with the real engines).
- A batch of a few hundred files rebuilds the list widget on every item state change (bounded; not measured).
- Warnings are ASCII-escaped in banners; the report view shows file names and paths as Qt text, the INFO log line is
  ASCII-escaped.
- Chapter grouping review (G11, D80, V12) is deferred to v2; no drag-and-drop onto the queue; the queue is not saved
  between sessions; no parallel export.

## Seam for WP3.14 and WP4.3

- WP3.14 implements `ExportJobs` (photo and video; a video's analysis inside the job) and returns `CANCELLED` itself on a
  cancel; it may import the seam from `clearwater.jobs.export_seam` without loading PySide6. It owns a fresh
  `Reservations` per job, plans and writes through `plan_output` and `SafeWrite`, and must not build any Qt object. A
  headless batch for WP4.1's runner can reuse the same per-item semantics.
- WP4.3 calls `install_export_panels(window, exports)` with WP3.14's jobs, and re-measures V7 with the real engines.
- The panels never call `setEnabled` on `actions.export`; the shell's reason (AD-15) stays authoritative.

## Debt dispositions

DR-44 (b) ADDRESSED for this package (owners `"export"`, `"batch"` on present and clear; tests above). DR-44 (a), (c):
not this package's (WP3.18; WP4.3). DR-35 (b) not this package's (WP3.14; the test stub follows "one `Reservations` per
job"). DR-35 (c) not this package's (WP4.3 start-up). AD-15 holds. V12 deferred to v2.
