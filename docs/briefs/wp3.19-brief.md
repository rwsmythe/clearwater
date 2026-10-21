# WP3.19 — Batch queue and export progress (dispatch brief, DRAFT for CHARC)

**Status:** DRAFT 2026-10-21 for CHARC (orchestrator generation 9, wave 3 tranche B; drafted
against main `9364f8f` plus the DR-44 pre-dispatch contract members); base = the pre-dispatch
main commit named at dispatch. Owner decisions: none inside the package (chapter grouping
review, G11, is deferred to v2 by the owner, v0.5.3).
- Spec **v0.5.4** (approved by the owner 2026-10-20). Architecture FINAL 1.0 section 3 IF-8,
  IF-9, IF-10, section 7 ("export and batch queue with progress and cancel (IF-8; WP3.19 is
  batch queue and export progress only, v0.5.3)"); AD-15, AD-20, AD-25 (a). Frame
  `docs/briefs/wp2.4-phase3-frame.md` sections 1, 2, 4, 5. WP3.16 report
  `docs/reports/wp3.16-shell-preview.md` "Contract"; WP3.13 report
  `docs/reports/wp3.13-naming-safe-writing.md` (`plan_output`, `SafeWrite`, used by tests).
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.19`, branch `wp3.19`, base = the main commit named at dispatch.

**Why.** Plan Phase 3: "WP3.16 owns the main window and defines the places where the other
packages attach their widgets. Each other package owns only its own widget modules. All are
built against stubs of the engines." This package connects File > Export, shows export
progress with cancel (G8), and gives the batch queue with its end-of-run report (G7). The
export and batch ENGINE is WP3.14's (wave 4); here the GUI side is built against a seam.

**Wave-3 GUI file map (the same table is in all four briefs).** Each package creates only its
own modules and tests; none edits an existing file.

| Package | Product modules (NEW, `src/clearwater/gui/`) | Tests (NEW) | Attaches | Message owners |
|---|---|---|---|---|
| WP3.17 | `parameter_panels.py`, `preset_panel.py` | `tests/test_gui_parameter_panels.py`, `tests/test_gui_preset_panel.py` | `Area.PARAMETERS` x3 ("Basic", "Advanced", "Presets") by `install_parameter_panels(window)` | `"parameters"`, `"presets"` |
| WP3.18 | `timeline.py`, `analysis_service.py` | `tests/test_gui_timeline.py`, `tests/test_gui_analysis_service.py` | `Area.TIMELINE` ("Timeline") by `install_timeline(window, analysis=None)` | `"timeline"`, `"analysis"` |
| WP3.19 | `export_panel.py`, `batch_panel.py`, `export_service.py` | `tests/test_gui_export_panel.py`, `tests/test_gui_batch_panel.py` | `Area.JOBS` ("Export", "Batch") by `install_export_panels(window, exports=None)` | `"export"`, `"batch"` |
| WP3.20 | `settings_dialog.py` | `tests/test_gui_settings_dialog.py` | `ShellWindow.set_settings_dialog` by `install_settings_dialog(window)` | `"settings"` |

| Field | Content |
|---|---|
| ID and title | WP3.19 — Batch queue and export progress; plan section 6 Phase 3 row WP3.19 (size M, depends on WP3.16, spec "G7, G8", feeds V7, V11); module `clearwater.gui` |
| Goal | File > Export connected to an export job for the open source, with progress and cancel; a batch panel that queues several files, applies one parameter set or preset, runs the items one after another unattended, skips and logs a failed item, stops the remaining items on cancel, and reports per item at the end. |
| Spec / decision clauses | Plan bullet "**WP3.19:** the batch queue, export progress and cancel, and the end-of-run report. The chapter grouping review (G11) is deferred to v2 with WP3.8." G7 "Batch queue: add multiple files; apply one parameter set or preset; run unattended; report per-item success, warnings and failures at the end. A failed item is skipped and logged, and the batch continues (D80, D81)." G8 "Export and batch show progress with a cancel control:" "cancel deletes the in-progress temporary output;" "completed files are kept;" "in batch mode, cancel stops the whole remaining batch." G9 "GUI stays responsive during analysis, export and batch processing (work runs off the UI thread)." D43 "Progress indicator with cancel, and non-blocking GUI"; D44 "On cancel, the partial output file is deleted; completed files kept"; D45 "Cancel during batch stops the whole remaining batch"; D81 "Batch failure: skip the failed item, log it, continue, report at end"; D80 is "*(deferred to v2, 0.5.3)*"; D83 ".LRV/.THM sidecars excluded from input" (refused when added to the queue). AD-15 "export is unavailable until analysis of that clip completes" (the shell's reason on `actions.export`; this package never overrides it). Feeds V7 "UI responds within 100 ms during analysis, export and batch processing (D66)." and V11 "cancel and simulated failures (crash, disk full) leave no partial outputs; leftover temporaries removed on next start." (plan: V11 built in WP3.13, WP3.14; this package's GUI leg only). |
| Depends on | WP3.16 merged (accept `a2685cb`): `clearwater.gui.contract` as frozen plus the DR-44 pre-dispatch members (`Message.owner`, `MessagePresenter.clear(..., owner=)`; sha named at dispatch); `ShellActions.export` is a `ReasonAction` that starts with "Export is not available yet." (WP3.19 clears that reason). WP3.15 merged (accept `da54a47`): `PresetStore.list_presets`/`load` (read only here). WP3.13 merged (accept `6dd5a00`): `clearwater.jobs.plan_output`, `SafeWrite`, `MediaKind`, `Reservations` (used ONLY by the test-side export stub, so the G8 cleanup legs run through the real safe-write machinery). UNMERGED, behind the seam of task 2: WP3.14 (export and batch jobs, wave 4; question 1). |
| Files owned | NEW: `src/clearwater/gui/export_panel.py`, `src/clearwater/gui/batch_panel.py`, `src/clearwater/gui/export_service.py`, `tests/test_gui_export_panel.py`, `tests/test_gui_batch_panel.py`, `docs/reports/wp3.19-batch-export.md`, `docs/proofs/wp3.19-ledger.md`. NOT owned: every existing file under `src/clearwater/gui/` (WP3.16's, including `contract.py`, `__init__.py`, `jobs.py`), `tests/gui_support.py` (imported read-only), WP3.16's tests, the WP3.17/3.18/3.20 files of the map, `src/clearwater/interfaces/`, `src/clearwater/jobs/` (WP3.13's; WP3.14 adds export and batch there), `src/clearwater/config/`, `pyproject.toml`, `uv.lock`, `tests/conftest.py`. |
| Interfaces provided | No frozen interface. The export seam of task 2 (`ExportRequest`, `ExportJobs`, `unavailable_exports`), frozen at this package's round-0 yield and additive only until accept (question 2); `install_export_panels(window: ShellWindow, exports: ExportJobs | None = None) -> None` (WP4.3 calls it with WP3.14's jobs) and the two `PanelFactory`s it attaches. |
| Interfaces consumed | Contract: `ShellContext` (`session`, `presets`, `jobs`, `messages`, `actions`, `engines.methods`), `Session` (`source`, `parameters`, `settings`, `analysis`, `source_changed`), `ReasonAction.set_unavailable`/`unavailable_reason`, `JobRunner.run(job, *, on_done, on_progress)`, `JobHandle.cancel`/`is_running`, `Area.JOBS`, `Message`. IF-8 `Progress`, `JobResult` (`ok`, `outputs`, `warnings`, `failure`, `device`, `elapsed_s`); IF-9 `ParameterSet`, `validate_parameter_set`; IF-10 `Settings`. WP3.16 helpers `sources.route`, `sources.file_filter` (question 3). |
| Hardware flags | `gui` on every test that creates a Qt object; no `gpu`, no `footage`. No timing FIGURE: V7's 100 ms is asserted as a bound (task 5); the observed maximum is informational. |
| Out of scope | The export itself: decode, render, encode, analysis of batch videos before their export, naming, disk-space estimate (D87), provenance, the per-device log line (WP3.14, WP3.10, WP3.6, WP3.13); start-up removal of leftovers (WP4.3; DR-35 (c)); the chapter grouping review (G11, D80, V12: deferred to v2); drag-and-drop onto the queue (D27 rules it out for the preview; not asked for here); saving a queue between sessions; parallel export of several items; the export settings themselves (WP3.20); any edit to WP3.16's files. |
| Debt and decided items | DR-44 (b) -- ADDRESSES (b) for this package -- owners `"export"` and `"batch"` on every present and clear; a test that another owner's error survives this package's success. DR-44 (a), (c) -- not this package's (WP3.18; WP4.3). DR-35 (b) ("`Reservations` record no owner ...") -- not this package's (WP3.14: "one `Reservations` passed to both `plan_output` and `SafeWrite`"); the test stub follows that rule. DR-35 (c) (`remove_leftovers` while a job runs) -- not this package's (WP4.3 start-up). AD-15 -- must hold: export is enabled only when neither the shell's reason nor this package's holds; this package calls `set_unavailable`, never `setEnabled`. DR-43 -- not this package's. V12 -- deferred to v2. `Session.settings_refusal()` -- not used: this package writes no settings. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green (in a dispatcher window) with the GUI tests headless; every G7 and G8 clause and D81/D45 shown by a named test; V7's bound asserted; the seam documented in the report; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: read and table.** Before product code, write in the ledger: the seam of
   task 2 as signatures with docstrings (COMMIT `export_service.py` at this yield, question 2);
   the export state table (idle, running, cancelling; how `actions.export`'s reason follows);
   the batch item states (queued, running, done, done with warnings, failed, cancelled, not
   run) and the transitions; the end-of-run report layout; the test list; the answers to the
   open questions; the `scripts/cell_depth.py` reading. YIELD for the dispatcher. A choice the
   brief leaves open is a STOP.
2. **The export seam (`export_service.py`).** As drafted (the round-0 table fixes names):
   - `ExportRequest` (frozen dataclass): `source: Path`, `kind: Literal["photo", "video"]`,
     `parameters: ParameterSet`, `settings: Settings`.
   - `ExportJobs` (protocol): `job(request) -> Callable[[Progress], JobResult]`. The returned
     callable runs on a worker thread, touches no Qt object, honours `progress.cancelled()`,
     writes through safe writing so a cancel or failure leaves no partial output (G8, D44,
     V11), and returns a `JobResult` (`ok` False with `failure` on failure; on cancel `ok`
     False and `failure` "cancelled"). A video's analysis before export (AD-15) is inside the
     job.
   - `unavailable_exports()`: the product default until WP4.3: every job returns `ok` False
     with failure "Export is not available in this build." and writes nothing.
3. **Export of the open source (`export_panel.py`, G8).** An "Export" panel in `Area.JOBS`:
   status line, `QProgressBar`, Cancel button, the last result.
   - At install: connect `actions.export.triggered`; `actions.export.set_unavailable(None)`
     (the shell's own reasons, no source and AD-15, still hold).
   - Triggered: an `ExportRequest` from `session.source()`, `session.parameters()`,
     `session.settings()` (a snapshot); `set_unavailable("An export is running.")`; run the
     job through `context.jobs` with `on_progress` driving the bar (total None: busy bar).
   - Done: `set_unavailable(None)` unless a batch runs; `ok` -> "Saved <file names>" and
     `messages.clear("error", owner="export")`; each `JobResult.warnings` item a warning with
     owner `"export"`; a failure an error with owner `"export"` naming the file; after the
     user's cancel, "Export cancelled." and no error.
   - While a batch runs, export is unavailable with "A batch is running.".
4. **The batch queue (`batch_panel.py`, G7, G8).** A "Batch" panel in `Area.JOBS`.
   - Queue: Add files (a multi-select open dialog with `sources.file_filter()`; each path
     through `sources.route`: a refusal (sidecar D83, unsupported extension) is a warning with
     owner `"batch"` and the file is not queued; a path already queued is not queued twice),
     Remove selected, Clear. Each row shows the file name and its state.
   - Parameters: a combo of "Current parameters" and every readable preset of
     `context.presets.list_presets()`, refreshed when the panel is shown and at Start. At
     Start the choice is resolved once: a preset whose method is not in `engines.methods`, or
     that fails `validate_parameter_set`, refuses the start with an error; the settings are
     `session.settings()` at Start. Later changes do not affect the running batch.
   - Run: Start (disabled while the queue is empty or an export or batch runs; export becomes
     unavailable with "A batch is running."). Items run one at a time, one job each through
     `context.jobs`; an overall "item i of n" line and the current item's progress bar; queue
     editing disabled while running.
   - Failure (D81): the item is marked failed with `JobResult.failure`, logged with
     `logging.getLogger("clearwater.gui.batch").warning(...)`, and the next item starts.
   - Cancel (D45): the running item's handle is cancelled; when its `on_done` arrives the item
     is "cancelled" and every remaining item "not run"; no further job starts. Completed
     items' outputs are untouched (G8).
   - End-of-run report (G7): when the run ends (all done or cancelled), the panel shows the
     counts (succeeded, with warnings, failed, cancelled, not run) and per item the outputs,
     each warning and the failure text, in a read-only text view that stays until the next
     Start; the same summary is logged at INFO. The queue keeps its rows so a failed item can be
     re-run by Start (question 4).
5. **Tests** (headless, `gui`-marked, through `tests/gui_support` helpers; a TEST-SIDE
   `ExportJobs` that writes a small file under `tmp_path` through `plan_output` and `SafeWrite`
   with one `Reservations` per run, and can be told to fail, to wait on an event, or to busy
   the CPU):
   - export: triggered from `actions.export`; progress reaches the bar; success, warnings,
     failure and cancel each shown as task 3 says; the reason while running; AD-15: with a
     video whose analysis is running, clearing this package's reason leaves export disabled
     with the shell's reason;
   - G8: cancel mid-write leaves no temporary and no final file for that item (the stub's
     `SafeWrite` aborts); outputs already completed are kept;
   - G7/D81: a queue of three where the second fails: the first and third succeed, the
     failure is logged (caplog) and reported; one parameter set or preset applied to every
     item (the requests carry it); a preset with an unknown method refuses the start;
   - D45: cancel during the second of three: the third is "not run", the first's output kept;
   - D83: a `.LRV` and an unknown extension are refused when added; duplicates not queued;
   - V7 bound: while a CPU-heavy stub export (NumPy, about 2 s, releasing the GIL) and then a
     batch run, a `QTimer` probe on the main thread never waits more than 100 ms (D66);
   - DR-44 (b): an error with owner `"shell.preview"` survives a successful export;
   - planted wrong implementations fail by name: a batch that stops at the first failure; a
     cancel that lets the next item start; `actions.export.setEnabled(True)` during analysis;
     an export job run on the main thread;
   - dependency rule: WP3.16's `tests/test_gui_deps.py` covers the new modules (run it, do
     not change it); no import of `clearwater.methods`.

## Declared operating envelope

Windows 11; Python 3.12; PySide6-Essentials and pytest-qt as locked; one Clearwater window;
one export activity at a time (the open source's export or one batch); a batch of up to a few
hundred files; outputs on local NTFS or exFAT volumes (the stub writes only under `tmp_path`);
tests headless on `offscreen`. Out of envelope: WP3.14's real export speed and memory (WP3.14,
WP5.2); a job that blocks past cancellation (DR-44 (c), WP4.3); a job that holds the GIL in
pure Python (WP4.3 re-measures V7); several windows; other operating systems (portable, N1,
not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.19\rN\`; ledger `docs/proofs/wp3.19-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r4\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - G7/G8/D45/D81 exactly: no item started after a cancel; a failure never ends the batch;
    every item reported; nothing deleted that completed;
  - `actions.export` only through `set_unavailable`; AD-15's shell reason never overridden;
    the reason always cleared again after a run, including after an exception in a callback;
  - nothing heavy on the interface thread; no Qt object touched from a job; one activity at a
    time;
  - the seam's contract (cancel, failure, no partial output) stated and honoured by the test
    stub; the product default writes nothing;
  - message owners (DR-44 (b)); nothing in WP3.16's files, `jobs/` or `interfaces/` changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating ("make
  NO change in the turn that adjudicates a round"). Report the `scripts/cell_depth.py` reading
  at every yield; ~250K is the evaluation point (past it, "REVIEW ONLY this turn" when told),
  ~400K STOP.
- **Full-pytest windows.** The full suite (about 3559 tests, about 15 min) runs ONLY in a
  window the dispatcher grants by message, in the background with `QT_QPA_PLATFORM=offscreen`
  and output to a file under `work/`; send `WINDOW RELEASED: <summary>` when it finishes. Never
  two heavy jobs at once. Inner loops run only your own tests and `tests/test_gui_deps.py`.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the module list, the seam (every name), the export and batch state tables, the
  report layout, the V7 bound and observed maximum, the gates, the Reviewer A rounds and
  verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or in
  `clearwater.gui.contract`; a change to any existing file (including `clearwater.jobs`); a
  dependency; any OS-specific code; a test writing outside `tmp_path`/`work/`; a test that
  cannot run headless; the round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with
  `git -c core.autocrlf=false commit -m "feat(wp3.19): ..." -- <paths>`, with a
  `Co-Authored-By:` footer naming your model; never `git stash` (use a WIP commit or a scratch
  copy). Never a bare `cd`. Never post to a mailbox. Gates: ruff check, ruff format --check,
  mypy strict, full pytest (in a window); no harness gate. Report
  `docs/reports/wp3.19-batch-export.md` (claims, evidence paths, limits, and a "Seam for WP3.14
  and WP4.3" section). The footage folder is never used. GoPro data is out of scope: no
  `gpmd`, IMU or GPS data.

## Questions for CHARC (recommended answer first)

1. **Who runs the batch loop (plan "WP3.14 runs ... the batch queue" vs this row's "the batch
   queue ... and the end-of-run report").** IF-8's `JobResult` describes one job, and G7 asks
   for a per-item report. Recommended: the GUI sequences the batch (one IF-8 job per item from
   the seam, skip-and-log, cancel stops the rest, the report from the per-item results);
   WP3.14 supplies the per-item job (photo or video, a video's analysis included) and, if it
   wants a headless batch for WP4.1's runner, the same semantics on its side. WP3.14's brief
   cites this seam. Alternative: WP3.14 owns one batch job with a per-item report type it
   defines; this package then waits for, or stubs, that type.
2. **Freezing the seam.** Recommended: as WP3.16 ruling 2 did for the contract: `ExportRequest`
   and `ExportJobs` committed at the round-0 yield, additive only until accept, a CHARC ruling
   after; WP3.14's and WP4.3's briefs cite it.
3. **Cross-brief items** (the same in WP3.17-3.20): `clearwater/gui/__init__.py` is not edited
   (X-W3a); read-only use of WP3.16's pure helpers `sources.route` and `sources.file_filter`
   (X-W3b; the queue then refuses exactly what File > Open refuses); the capturing test
   presenter already takes `owner` (the DR-44 pre-dispatch commit). Recommended as in the WP3.17 brief,
   questions 1 and 3.
4. **Re-running failed items.** Recommended: the queue keeps every row after a run; Start runs
   the whole queue again (the user removes what succeeded); no "retry failed" button (not in
   G7). Alternative: Start runs only the rows not marked done.
5. **Export of a photo or video while its source changes.** Recommended: the request is a
   snapshot at trigger time; changing or closing the open source does not cancel the export.
   Alternative: a source change cancels the running export.
6. **Reviewer tier.** Recommended: STRONG, five-round gate.
