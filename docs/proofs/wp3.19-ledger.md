# WP3.19 ledger (batch queue and export progress)

Cell: implementer-sonnet-high, seat 1. Worktree `.worktrees/wp3.19`, branch `wp3.19`, base `718324b`.
Brief `docs/briefs/wp3.19-brief.md` (FINAL; rulings CHARC `53d1d906e47fe2c9`). Spec v0.5.4 (G7, G8, G9;
D43-D45, D81, D83; V7, V11). Reviewer A evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp3.19\rN\`.

## Cumulative round ledger

| Round | Head | Verdict | Blocking (crit/major) | Minor | In envelope | NEW / REOPENED | Product vs test-only fixes | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|
| 0 | `d286b8d` | table only, no product code besides `export_service.py`; RULED by the dispatcher (CHARC `0e6962c39f216c86`): seam approved, C1 GRANTED, C2-C7 accepted | - | - | - | - | - | 123,884 |
| 1 | `8639afb` | NEW_CRITICAL_MAJOR_FOUND | 2 major (F1 export gate held if setup raises after try_start; F2 warnings dropped for failed/cancelled items), 0 critical | 1 (F3 current-parameters validation untested) | 3 in, 0 out | 3 NEW, 0 REOPENED | F1, F2 product + tests, F3 test (852192d, 3d01ae6, 735dd5f) | (dispatcher fills) |
| 2 | `735dd5f` | NO_NEW_CRITICAL_MAJOR (CONVERGED) | 0 critical, 0 major | 3 (F4 F1-test variant; F5 outputs-kept test; F6 seam docstring on outputs of a non-ok result) | 3 in, 0 out | 3 NEW, 0 REOPENED | R1 fixes were product (F1 export_panel, F2 batch_panel) + tests; R2 cleanup test-only plus one docstring | (dispatcher fills) |

## Round 0

### 0.1 Reading done and what it fixed

Read: dispatch recipe, brief, review gate Part 1, frame 1/2/4/5, `gui/contract.py`, `gui/jobs.py`,
`gui/sources.py`, `gui/shell.py` (`ExportAction`, `export_reason`, `attach`), `gui/messages.py`
(`clear(owner=)`), `tests/gui_support.py`, the WP3.16 and WP3.13 reports, `interfaces/jobs.py`,
`interfaces/settings.py`, `interfaces/parameters.py` (`validate_parameter_set`), `config/presets.py`
(`PresetStore.list_presets` -> `PresetEntry(name, path, parameter_set | None, error)`).
Facts that shape the design:

- `ExportAction` has ONE caller slot (`set_unavailable`), shown after the shell's reason. Two panels
  (Export, Batch) share it, so a shared gate must decide the text: `ActivityGate` below.
- `QtJobRunner.run` returns `on_done` exactly once on the main thread; an escaping exception in the job
  is already a failed `JobResult` (`failure` = `"<Type>: <msg>"`); `close()` cancels every job and
  delivers `on_done` before the settings write. A cancelled job's `JobResult` is whatever the job returns,
  so the seam fixes the cancel result (`ok` False, `failure` = `CANCELLED`).
- `MessagePresenter.clear(severity, owner=)` removes by both; the capturing test presenter keeps a
  message when EITHER filter does not match, so `clear("error", owner="export")` is exact there too.
- `sources.route(path)` returns `"photo" | "video" | Message` (a refusal for a sidecar, D83, or an
  unknown extension); it never opens the file.

### 0.2 The seam (`export_service.py`, COMMITTED at this yield, frozen; additive only until accept)

```python
CANCELLED = "cancelled"                       # JobResult.failure of a cancelled job
UNAVAILABLE_TEXT = "Export is not available in this build."

@dataclass(frozen=True)
class ExportRequest:
    source: Path                              # the file to export (a batch item need not be open)
    kind: Literal["photo", "video"]           # from sources.route
    parameters: ParameterSet                  # IF-9, resolved once
    settings: Settings                        # IF-10 snapshot

class ExportJobs(Protocol):
    def job(self, request: ExportRequest) -> Callable[[Progress], JobResult]: ...

def unavailable_exports() -> ExportJobs       # every job: ok False, failure UNAVAILABLE_TEXT, writes nothing
```

Contract of `ExportJobs.job` (stated in its docstring; WP3.14's brief cites it):
1. `job(request)` is called on the INTERFACE thread: it only builds the callable (no file access, no
   decode) and may raise `ValueError` for a request it can never run (the panel shows that as the item's
   failure and goes on).
2. The callable runs on a worker thread, touches no Qt object, reports `progress.report(done, total,
   message)` (total None = busy), checks `progress.cancelled()` at least between units of work.
3. Safe writing: a cancel or failure leaves no partial output and no temporary (G8, D44, V11); a file
   already committed is never removed.
4. A video's analysis (AD-15) is inside the job: a batch item needs no prior analysis. (For the open
   source, WP3.18's finished analysis may already be in the cache; the job decides, the panel does not
   care.)
5. Result: success `ok` True, `outputs` = committed files, `warnings` (ASCII-safe strings), `failure` None;
   failure `ok` False, `outputs` empty, `failure` the user-readable reason; cancel `ok` False, `outputs`
   empty, `failure == CANCELLED`. Cancel and failure are distinguished ONLY by `failure == CANCELLED`.
6. One job per source file (the GUI sequences a batch, ruling Q1): every job owns a fresh `Reservations`
   (an item is committed before the next plans), so WP3.14 needs no cross-job reservation state.

GUI-side, in the same module, NOT part of what WP3.14 implements (additive; named so it is not mistaken
for the seam): `Activity = Literal["export","batch"]`, `RUNNING_EXPORT_REASON` ("An export is running."),
`RUNNING_BATCH_REASON` ("A batch is running."), `ActivityGate(apply)` with `current`, `reason()`,
`subscribe(cb)`, `try_start(activity) -> bool`, `finish(activity)`. It imports no Qt (the `apply` callable
is `actions.export.set_unavailable`); `finish` applies the reason BEFORE it calls subscribers and a
raising subscriber is logged and skipped, so the reason cannot stay set after a callback exception.

Other public names (modules `export_panel`, `batch_panel`; not seam):
`install_export_panels(window, exports=None) -> None` (attaches "Export" and "Batch" to `Area.JOBS`,
one gate shared); `export_panel_factory(exports, gate) -> PanelFactory`, `batch_panel_factory(exports,
gate, *, choose_files=None) -> PanelFactory`; classes `ExportPanel(QWidget)`, `BatchPanel(QWidget)`
(`choose_files: Callable[[QWidget], list[Path]] | None` is the injectable file dialog for tests, like the
shell's `choose_file`); `ItemState` (batch item states), `BatchItem`, `format_report(...)`.

### 0.3 Export state table (`ExportPanel`)

| State | Status line | Bar | Cancel | Gate / `actions.export` caller reason |
|---|---|---|---|---|
| idle (initial) | last result, or "Ready." | hidden or 0 | disabled | None, unless a batch runs (then "A batch is running." from the gate); the shell's own reasons (no source, AD-15) show through `unavailable_reason()` regardless |
| running | "Exporting <file>..." plus the job's message | determinate when the job reports a total, busy (0,0) when `total` is None | enabled | "An export is running." |
| cancelling | "Cancelling..." | as running | disabled | "An export is running." |

Transitions:
- install: `gate = ActivityGate(actions.export.set_unavailable)` clears the "not available yet" reason.
- idle -> running: `actions.export.triggered` (the action is disabled while any reason holds, so this
  needs source + AD-15 ok + no activity). Handler re-checks `session.source()` is not None and
  `gate.try_start("export")`; else ignores. Builds `ExportRequest(source.path, source.kind,
  session.parameters(), session.settings())`, `clear("warning", owner="export")` (choice C3), then
  `jobs.run(exports.job(request), on_done, on_progress)`.
- running -> cancelling: Cancel button -> `handle.cancel()`.
- running/cancelling -> idle: `on_done(result)`; inside `try/finally`, `gate.finish("export")` runs
  first (reason cleared even if presenting raises). Then: `ok` -> status "Saved <names>" (names ASCII
  escaped), `clear("error", owner="export")`, each warning presented as `Message("warning", text, path,
  "export")`; not ok and `failure == CANCELLED` -> "Export cancelled.", no error; not ok otherwise ->
  `Message("error", "<file>: <failure>", path, "export")`. A cancel requested but the job finished `ok`
  is reported as saved (the output is kept, G8).
- A synchronous failure of `exports.job(request)` or `jobs.run(...)` is shown as the same error, and the
  gate is finished again.
- The open source changing or closing while running does nothing to the export (ruling Q5).

### 0.4 Batch item states (`BatchPanel`)

States: `queued`, `running`, `done`, `done with warnings`, `failed`, `cancelled`, `not run`.

| From | Event | To |
|---|---|---|
| (absent) | Add files (route ok, not a duplicate) | queued |
| any row | Start (gate acquired; whole queue re-run, ruling Q4) | queued (all rows reset, report cleared) |
| queued | previous item ended, no cancel requested | running |
| queued | previous item ended, cancel requested | not run |
| running | `on_done` ok, no warnings | done |
| running | `on_done` ok with warnings | done with warnings |
| running | `on_done` not ok, `failure != CANCELLED` (D81) | failed, then the NEXT item starts (unless cancel was requested) |
| running | `on_done` not ok, `failure == CANCELLED` | cancelled; every remaining queued -> not run |
| running | `exports.job()` or `jobs.run()` raises | failed (text = exception), next item starts |
| running | Cancel clicked | handle.cancel(); the row stays running until its `on_done`; a result `ok` still counts done (kept, G8) |

The run ends when no row is queued or running: `gate.finish("batch")`, report built, shown, logged at INFO.
Rows are kept (Start re-runs the whole queue). Remove/Clear/Add/Start/parameter combo are disabled while
the run is in progress; Cancel is enabled only while it is. Start is disabled while the queue is empty, or
`gate.current` is not None (an export runs).

### 0.5 End-of-run report layout (read-only `QPlainTextEdit`, kept until the next Start; same text at INFO)

```
Batch finished: 5 items.                         (or "Batch cancelled: 5 items.")
Succeeded 1, with warnings 1, failed 1, cancelled 1, not run 1.
1. clipA.mp4 - done
   output: D:\out\clipA_corrected.mp4
2. photoB.jpg - done with warnings
   output: D:\out\photoB_corrected.png
   warning: <text>
3. clipC.mp4 - FAILED
   failure: <text>
4. clipD.mp4 - cancelled
5. clipE.mp4 - not run
```
The five counts partition the items. File names are shown as the path's name (Qt text); the INFO log line
and every presenter message go through `messages.ascii_text`. A failed item is also logged at WARNING on
`clearwater.gui.batch` (D81) when it ends.

### 0.6 Test list (all `gui`-marked, headless; test-side `StubExportJobs` writes a small file under
`tmp_path` through `plan_output` + `SafeWrite` with ONE `Reservations` per job; it can fail by name, wait
on an event, busy NumPy, and records the thread and the request)

`tests/test_gui_export_panel.py`:
1. install clears "not available yet"; the shell's no-source reason still shows; disabled with the shell's
   reason during a running video analysis (AD-15 hold; also a planted `setEnabled(True)` fails by name).
2. triggered -> request carries path, kind, parameters, settings (snapshot: a later `set_parameters` does not
   change it).
3. progress reaches the bar (determinate; busy when total None).
4. success: "Saved ...", `error`/owner `export` cleared; DR-44 (b): a `shell.preview` error survives.
5. warnings presented with owner `export`; failure -> error naming the file, owner `export`.
6. cancel -> "Export cancelled.", no error; G8: stub `SafeWrite` aborted, no temporary and no final file.
7. reason "An export is running." while running, cleared after, also after a presenter that raises.
8. a second trigger while running is ignored (gate); export unavailable while a batch runs.
9. the job runs on a worker thread (planted main-thread run fails by name); source change does not cancel.
10. `unavailable_exports()` -> failure text, nothing written.
11. V7: 10 ms probe never waits > 100 ms during a ~2 s NumPy stub export (informational max recorded).
12. `ActivityGate` unit tests (single activity, subscriber exception).

`tests/test_gui_batch_panel.py`:
13. G7/D81: three items, the second fails: first and third done, failure logged (caplog), reported.
14. one parameter set / preset applied to every item (requests); "Current parameters" resolved once at Start
    (a later change does not reach the run); settings snapshot at Start.
15. preset whose method is not in `engines.methods`, or failing `validate_parameter_set`, or unreadable:
    Start refused with an error (owner `batch`), nothing runs.
16. D45: cancel during the second of three: second cancelled, third not run, first's output kept (G8);
    planted "cancel lets the next start" and planted "stops at the first failure" fail by name.
17. D83: `.LRV` and unknown extension refused with a warning (owner `batch`) and not queued; duplicates
    (case/normalisation) not queued; Remove selected, Clear.
18. queue editing disabled while running; Start disabled when empty / export running; export reason "A batch
    is running." during and cleared after (also after cancel, after an exception in a callback).
19. report: counts, per-item outputs/warnings/failure, stays until the next Start, INFO log; re-run (Q4).
20. job build/run raising -> item failed, batch continues.
21. DR-44 (b): an error with owner `shell.preview` survives a batch's start and end.
22. V7: probe during a batch of CPU-heavy items.
23. `tests/test_gui_deps.py` run, not changed.

### 0.7 Answers to the brief's open questions (rulings Q1-Q6 are adopted as written)

Q1 GUI sequences the batch; Q2 seam frozen here; Q3 `sources.route`/`file_filter` used read-only,
`gui/__init__.py` untouched; Q4 Start re-runs the whole queue; Q5 snapshot request, source change does
not cancel; Q6 STRONG, five-round gate.

### 0.8 Choices the brief leaves open (STOP; my recommended answer first)

- **C1 (consumer-visible): where the seam lives.** `clearwater.gui.export_service` is in the `gui`
  package, whose `__init__` imports PySide6, so WP3.14 (in `clearwater.jobs`) or WP4.1's headless runner
  importing `ExportRequest` loads PySide6 and breaks the "`.jobs` loads no PySide6" rule in spirit (the
  test only imports `clearwater.jobs`). Recommended: PROCEED AS BRIEFED (seam in `gui/export_service.py`,
  module itself Qt-free), and WP3.14's brief decides: import it (its engine is wired in the GUI process
  anyway; a headless runner would not) or, preferably, CHARC grants ONE NEW file
  `src/clearwater/jobs/export_seam.py` (PySide-free) now, holding the seam names, with
  `gui/export_service.py` re-exporting them. I proceed with the brief's layout unless told otherwise; the
  move is mechanical (names unchanged).
- **C2: `ActivityGate`** (one shared gate for the one `ReasonAction` caller slot) lives in
  `export_service.py` and is GUI-side, additive. Recommended: yes (no further file; no import cycle between
  `export_panel` and `batch_panel`).
- **C3: stale messages.** Brief: an export that succeeds clears the export's own `error`s. Reading I
  will implement unless told otherwise: at trigger the panel also clears its own `warning`s
  (`clear("warning", owner="export")`) so warnings do not pile up across exports; errors stay until the
  next success (G10). Batch route warnings and start-refusal errors (owner `batch`) are cleared at Start
  and by the Clear button.
- **C4: Batch and AD-15.** The shell's export reason (no source, analysis) does not apply to the batch (a
  batch item's analysis is inside its job); Start needs only a non-empty queue and no other activity.
  Recommended: yes.
- **C5: duplicates** compared by `os.path.normcase(os.path.abspath(path))`; no filesystem access.
- **C6: a batch-wide D87 disk-space check** (WP3.13 note: sum estimates per volume) is impossible with one
  job per item; each job checks its own item. Not this package; recorded for WP3.14's brief.
- **C7: extra `batch_panel_factory(..., choose_files=None)`** keyword for tests; `install_export_panels`
  keeps the briefed signature.

### 0.9 Depth reading

`scripts/cell_depth.py` is the dispatcher's instrument (a cell cannot read its own transcript depth,
recipe section 5); the figure is filled by the dispatcher at this yield.

### 0.10 Round-0 ruling (CHARC `0e6962c39f216c86`, relayed by the orchestrator)

- C1 GRANTED: ONE NEW file `src/clearwater/jobs/export_seam.py` (owned by this package; stdlib and
  `clearwater.interfaces` only) holds `CANCELLED`, `UNAVAILABLE_TEXT`, `ExportRequest`, `ExportJobs`,
  `unavailable_exports`; `gui/export_service.py` re-exports them and keeps `ActivityGate`, `SharedGate`
  and the two reason strings. `jobs/__init__.py` is NOT edited. One test asserts the seam module loads no
  PySide6 (subprocess, in `tests/test_gui_export_panel.py`).
- Docstring notes adopted in `ExportJobs.job` / `CANCELLED`: a missing source is the JOB's failure, never a
  build-time `ValueError`; `CANCELLED` is reserved and returned as the constant; output-name collisions
  across batch items are caught by the filesystem scan at each plan (D34-D36), not by shared state.
- C2-C7 accepted as recommended. `SharedGate` (additive, GUI side) is the holder that creates the one
  gate when the first panel's factory runs.
- Host: pytest hold ON at this point (CHARC's main suite); build is static-gates only until lifted.

## Round 1 (Reviewer A, head `8639afb`; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.19\r1\`)

Targeted tests before the round (own modules + test_gui_deps): 53 passed, 11 s, `work/t1-r1.txt`.
Mutation check of the new tests (script `work/mut.py`, each mutation reverted): batch stops at first
failure -> `test_a_failed_item_is_skipped_logged_and_reported` fails; cancelled result not stopping the
rest -> `test_a_cancelled_result_without_a_click_also_stops_the_batch`; export clears every owner's
errors -> `test_success_clears_only_the_export_errors_and_presents_warnings`; no gate release in
`_done` -> `test_the_reason_while_running_and_after`; duplicates / sidecars not refused ->
`test_refused_files_are_warned_about_and_duplicates_are_not_queued`; live session parameters instead of
the Start snapshot -> `test_one_parameter_set_and_settings_apply_to_every_item_and_are_fixed_at_start`.
Equivalent mutant: dropping `or self._gate.current is not None` in `start()` (the following
`try_start` is the real guard). The planted-wrong tests assert the wrong behaviour is detectable.
The first run was green; "failing before the fix" is shown by the mutations above, not by a red first run
(tests were written after the product code; disclosed).

Findings: see `adjudication.md` in the evidence folder. F1 MAJOR confirmed by a scratch repro; F2 MAJOR
confirmed by reading; F3 MINOR accepted. No change made in the adjudicating turn.

## Round 2 (Reviewer A, head `735dd5f`, diff `8639afb..735dd5f`; evidence `...\wp3.19\r2\`)

Order used: the R1 regression tests were run on the UNFIXED code first (before the 19:38Z slot end):
`r2\regression-on-8639afb.txt` -- `test_the_reason_is_cleared_when_setup_raises_after_the_gate_is_taken`
(F1) and `test_warnings_of_failed_and_cancelled_items_are_kept_and_reported` (F2) FAIL; the F3 test passes
on the unfixed code (the product already validated the current set; it is a coverage gap), its planted
version `test_planted_current_parameters_without_validation_are_detected` shows the check distinguishes.
Then the fixes (one commit per finding: F1 `852192d`, F2 `3d01ae6`, F3 `735dd5f`; the F2 stub flag
`warn_on_failure` rides in F1's commit with the shared test file), then 57 passed (own modules + deps,
`work/t1-r2c.txt`), then Reviewer A round 2 (the Codex pass ran after the tests, within the slot).
Verdict `NO_NEW_CRITICAL_MAJOR`; 3 minors accepted (`adjudication.md`). Terminating cleanup pending:
F4 test (request construction raising), F5 test (outputs of a non-ok result kept), F6 seam docstring
(`outputs` on a non-ok result = files committed before the stop, normally none; wording only).

## RESUME HERE (if re-seated)

- Worktree `.worktrees/wp3.19`, branch `wp3.19`, head `735dd5f` plus this ledger commit. Base `718324b`.
- Rulings: CHARC `53d1d906e47fe2c9` (brief), `0e6962c39f216c86` (round 0: seam approved, C1 granted:
  `jobs/export_seam.py`, C2-C7 accepted). Round 1 adjudication upheld by the dispatcher.
- Done: round 0, build, R1 (2 major fixed), R2 CONVERGED.
- Remains: (1) terminating cleanup F4/F5 (tests) and F6 (seam docstring), no further Reviewer A round;
  (2) `WINDOW REQUEST: full pytest` on the final head; (3) report `docs/reports/wp3.19-batch-export.md`
  (claims, evidence paths, limits, "Seam for WP3.14 and WP4.3"); (4) the structured return report.
- Gates now: ruff, format, mypy green; targeted 57 passed. Observed V7 maxima: see the V7 test prints
  (`work/t1-r2c.txt`, run with -s to read); no full suite run yet.
- Notes for the report: tests were written after the product code (disclosed); mutation checks in
  `work/mut.py`; equivalent mutant on `start()`'s second gate guard; stub `warn_on_failure` option.

## Round-2 rulings and cleanup

- Dispatcher: round 2 UPHELD, Reviewer A terminates at round 2; minors 1 and 2 are test-only (commits `e887043`,
  `d853ff7`, targeted runs after the WP3.10 suite); no own full pytest (stacked gate on the merge candidate).
- Minor 3 RULED by CHARC `efc95f5d4e7b8456`: seam wording "on a non-ok result, `outputs` lists any file committed
  before the stop (normally none)" applied in `export_seam.py` (wording only). Depth at the round-2 yield: 261,443.

## Final targeted run (2026-10-26 20:21Z)

61 passed (own modules + test_gui_deps, headless, `work/t1-final.txt`); V7 observed maxima 13 ms (export), 11 ms
(batch). The minor-1/minor-2 tests and their planted versions pass; the first run showed two teardown errors in the
minor-1 helper (a patched `session.parameters` used by the window's close), fixed in the test helper. Full pytest: run by
the orchestrator on the merge candidate (stacked gate). Reviewer A terminated at round 2.

## Reviewer B pass 1 remediation (seat 2)

Pass 1 (orchestrator's seat, merge candidate `wp3.19-mc` `70c25ee`): 0 critical, 2 major, 3 minor, 1 advisory, all
REASONED. Seat-2 cell, fixes on `wp3.19` from head `b12c3fd` (base `718324b`); targeted runs only (own modules plus
`tests/test_gui_deps.py`, headless, fresh `--basetemp`), the host busy with WP3.10's suite. "Before" = the new tests run
against `git archive b12c3fd` extracted to `work/old1` with `PYTHONPATH` set to its `src` (`clearwater.__file__` checked:
`work/old1/src/clearwater/__init__.py`); for the test-only items the "before" is a copy with the named defect planted.

| # | Commit | Test(s) | Before | After |
|---|---|---|---|---|
| 1 MAJOR export non-ok outputs/warnings | `f0106f1` | `test_outputs_and_warnings_of_a_non_ok_result_are_named_and_presented[failed\|cancelled]` (+ no-outputs case, + planted drop) | 2 failed, 3 passed (`work/b1.txt`) | 5 passed (`work/h1.txt`) |
| 2 MAJOR batch Start setup guard | `5e35f10` | `test_the_gate_is_released_when_setup_raises_after_it_is_taken` (+ planted unguarded Start) | 1 failed, 1 passed (`work/b2.txt`) | 2 passed (`work/h2.txt`) |
| 3 MINOR errors kept until a Start succeeds | `d4cd1e4` | `test_a_refusal_is_kept_by_the_next_refusal_and_cleared_by_a_successful_start` (+ planted clear-at-trigger, + the old refusal test) | 1 failed, 2 passed (`work/b3.txt`) | 3 passed (`work/h3.txt` interrupted, see below; module 34 passed `work/h5.txt`) |
| 4 MINOR (test) report lists non-ok outputs | `6fbbb05` | `test_the_report_lists_the_outputs_of_a_failed_or_cancelled_item[failed\|cancelled]` (+ planted omitting `format_report`) | 2 failed, 1 passed against a product with `output:` lines omitted for non-ok items (`work/b4.txt`) | 3 passed (`work/h7.txt`) |
| 5 MINOR (test) closed runner | `9eefd83` | `test_a_closed_runner_fails_the_export_and_releases_the_gate`, `test_a_closed_runner_fails_every_item_and_releases_the_gate` (+ 2 planted leaks) | 2 failed, 2 passed against a product that does not release the gate when the failure text contains "closed" (`work/b5.txt`) | 4 passed (`work/h9.txt`) |
| 6 ADVISORY report text | this commit | n/a | n/a | n/a |

Final head targeted run: 77 passed in 11 s (`work/tfinal2.txt`; three repeats of the 70-test run before the last two
test commits: 70 passed each, 11 s). Gates on the final head: ruff check, ruff format --check (207 files), mypy (121
source files) green; LF check (`git cat-file -p HEAD:<f> | tr -cd '\r' | wc -c`) 0 for every file changed since
`718324b`.

Disclosures: (a) one run of the whole batch module (`work/h3.txt`, run while the commit for item 3 was chained after it)
stalled after 12 tests for over 4 minutes under host load and was stopped by killing its own pytest PIDs; item 3's commit
`d4cd1e4` was created by the chained command after that kill, so it was not preceded by a green full-module run. The module
was then run in full (34 passed, 4.6 s; later 37 and 70 and 77 passed, four repeats in total), and the stall did not
reproduce; cause not established (host contention suspected). (b) The tests for item 2 assert the
gate directly (`batch._gate.current`) because the shell's no-source reason masks the batch reason in the rig. (c) The
failed-item error text for a Start whose setup raised is "The batch could not start: <detail>" (owner `"batch"`). (d) The
seam is untouched. Depth at this yield: reported by the orchestrator from the transcript (the cell cannot read it).

