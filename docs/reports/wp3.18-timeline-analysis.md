# WP3.18 -- Timeline and analysis (report)

Cell `implementer-sonnet-high`, seats 1 and 2, worktree `.worktrees/wp3.18`, branch `wp3.18`, base main
`718324b`. Brief `docs/briefs/wp3.18-brief.md` (FINAL). Ledger `docs/proofs/wp3.18-ledger.md`. Spec v0.5.4:
G4, G5, D42, D70, D72, D108, V18, V7; AD-5, AD-6, AD-7, AD-15, AD-20.

## What was built

All NEW files; no existing file is changed (`clearwater/gui/__init__.py` untouched, ruling Q1;
`interfaces/` and `contract.py` untouched).

| File | Content |
|---|---|
| `src/clearwater/gui/analysis_service.py` | The seam: `ClipAnalysis` (`run`, `retarget`, `pts`, `proxy`, `statistics`), `AnalysisFactory`, `StubClipAnalysis`, `stub_analysis_factory`. Imports no Qt, no `clearwater.analysis`, no `clearwater.methods`. |
| `src/clearwater/gui/timeline.py` | `TimelinePanel`, `install_timeline(window, analysis=None)` attaching in `Area.TIMELINE`: analysis on open, the AD-15 states, progress, Cancel, Analyse, the scrubber, the V18 switch. |
| `tests/test_gui_timeline.py`, `tests/test_gui_analysis_service.py` | Headless, `gui`-marked; with `tests/test_gui_deps.py` (run unchanged) 71 tests. |

## Claims with evidence

Targeted evidence is in `tests/test_gui_timeline.py` (T) and `tests/test_gui_analysis_service.py` (A).

| Claim | Test (named) |
|---|---|
| V18 leg: a corrected frame is shown before the analysis completes, then updates to the smoothed statistics | T `test_a_corrected_frame_is_shown_before_the_analysis_completes_and_then_updates`; planted `test_planted_no_switch_after_completion_fails` |
| G5 / D70: progress reaches the session; Cancel gives "cancelled", drops the statistics, keeps the clip open, Analyse restarts; export names the reason | T `test_progress_reaches_the_session_and_export_names_it`, `test_cancel_gives_cancelled_drops_statistics_and_analyse_restarts` |
| Whoever cancels, the result is "cancelled", never complete (DR-47's shape); an exception after a cancel is a cancel | T `test_a_cancelled_run_that_finished_anyway_is_still_cancelled`, `test_a_cancel_by_a_third_party_is_never_a_completion`, `test_an_exception_after_a_third_party_cancel_is_a_cancel_not_a_failure`, `test_a_scrub_read_that_fails_after_a_cancel_shows_no_error` |
| Failure: state "failed", error owner `"analysis"`, provisional preview stays | T `test_a_failed_analysis_says_why_keeps_the_preview_and_clears_on_analyse` |
| D72 / G4: stored proxy while the slider is down, `set_position` never called; release commits the exact pts | T `test_dragging_shows_the_stored_proxy_and_never_sets_the_position`, `test_release_sets_the_exact_pts_with_the_smoothed_statistics`, `test_a_keyboard_step_commits_the_next_pts`, `test_a_release_without_a_value_change_still_replaces_the_proxy`, `test_latest_wins_runs_one_proxy_read_at_a_time` |
| The drag rule (latest intent) holds over every order of press, move, release, lane results and decodes | T `test_the_latest_intent_wins_over_every_seeded_interleaving` (200 seeds x 28 steps) and five planted panels, each failing by its own reason (`test_planted_lane_orderings_fail_the_interleaving_by_name`) |
| DR-44 (a): every frame is shown with its own pts's statistics; a failed decode restores the last shown frame's | T `test_a_decoded_pts_that_differs_from_the_request_gets_its_own_statistics`, `test_a_decode_failure_restores_the_last_shown_frames_statistics_and_the_slider`, `test_a_failed_decode_after_a_parameter_change_restores_no_statistics`, `test_a_frame_decoded_after_a_parameter_change_is_not_remembered_with_old_statistics`, `test_only_pts_from_the_analysis_are_requested`; planted `test_planted_requested_statistics_kept_after_a_failed_decode_fails` |
| DR-23 / AD-6: pts keys, a VFR clip scrubs to exact pts; D98 a one-stage method | T `test_a_vfr_clip_scrubs_to_exact_pts_with_their_own_statistics`; A `test_a_three_stage_method_and_a_one_stage_method_both_complete` |
| AD-15: a change during the run is offered with `retarget` (absorbed: complete once under the new values; not absorbed: one follow-up run before "complete"); after completion a change goes provisional, then smoothed; export unavailable until the final completion | T `test_a_change_during_the_run_not_absorbed_triggers_one_follow_up_before_complete`, `test_a_change_during_the_run_that_is_absorbed_completes_once_under_the_new_values`, `test_after_completion_a_change_goes_provisional_then_smoothed_again`, `test_a_commit_in_flight_when_the_parameters_change_carries_no_stale_statistics` |
| Q-B: a method change while running or complete builds a new analysis (superseded, never "cancelled"); during a user cancel it stays "cancelled"; Analyse rebuilds | T `test_a_method_change_while_running_rebuilds_the_analysis_as_superseded`, `test_a_method_change_after_completion_analyses_again`, `test_a_method_change_during_a_user_cancel_stays_cancelled_and_analyse_rebuilds`, `test_analyse_after_a_cancel_and_a_method_change_builds_the_new_methods_analysis` |
| Reviewer B pass 1 (#1): an A-B-A burst in the window between the run's return and its `on_done`, with a stub that retains the recompute job, never completes under the kept job; a follow-up `run` runs it | T `test_a_burst_in_the_window_before_on_done_never_completes_under_a_kept_job` (5 bursts), `test_a_burst_that_the_run_in_flight_absorbs_needs_no_follow_up` |
| Reviewer B pass 1 (#2): the progress label is the reported text (ASCII-escaped), the run's label when empty | T `test_the_reported_progress_text_is_the_label`, `test_an_empty_progress_text_keeps_the_runs_label`, `test_a_non_ascii_progress_text_is_escaped` |
| Reviewer B pass 1 (#4): a closed runner ends a superseded run's rebuild, or a recompute, in `cancelled` | T `test_closing_the_runner_during_a_superseded_run_leaves_a_terminal_phase`, `test_a_change_after_the_runner_closed_leaves_a_terminal_phase` |
| Stale work: a source change or a photo mid-analysis leaves nothing of the old job; closing starts nothing | T `test_a_source_change_mid_analysis_leaves_no_state_or_statistics_from_the_old_job`, `test_a_photo_opened_mid_analysis_cancels_the_run`, `test_closing_the_window_mid_analysis_does_not_report_a_completion` |
| Threads: `run`, `proxy`, `statistics` never on the main thread | T `test_run_proxy_and_statistics_run_off_the_interface_thread`; planted `test_planted_analysis_run_on_the_interface_thread_fails` |
| V7: the interface never waits more than 100 ms during a ~2 s NumPy analysis and a drag | T `test_v7_interface_never_waits_more_than_100_ms_during_analysis_and_a_drag`; observed maxima 14, 23, 39 ms (seat 1) and 12, 13 ms (seat 2), informational; the bound is asserted |
| Message owners `"analysis"`, `"timeline"` (DR-44 (b)) | T `test_scrub_failures_are_owned_by_the_timeline_and_cleared_by_the_next_success`, the failed-analysis test |
| The stub honours the seam: thread rules, cancel, `pts`/`retarget` never wait (also for the file system), retarget True/False | A `test_pts_and_statistics_never_wait_for_a_run_in_flight`, `test_pts_and_retarget_never_wait_for_the_file_system`, `test_retarget_false_...`, `test_retarget_true_...`, `test_a_second_concurrent_run_is_refused` |
| Dependency rule | `tests/test_gui_deps.py` (unchanged); A `test_the_new_modules_import_neither_the_analysis_engine_nor_the_methods`, `test_the_seam_module_imports_no_qt` |

## The seam and `retarget`

`ClipAnalysis` (one instance per opened clip; statistics keyed by pts ticks, never an index):

| Member | Thread | Contract |
|---|---|---|
| `run(parameters, progress, *, focus_pts=None) -> None` | job worker | First call: the full pass. Later calls: the dependent stages after a parameter change, `focus_pts`'s reach first (AD-7). Returns early when `progress.cancelled()`; raises on failure. A normal return of a job the GUI did not cancel is a completion. At most one `run` per analysis in flight. |
| `retarget(parameters, *, focus_pts=None) -> bool` | main | Added at the round-0 ruling (CHARC `bdbd8323ceace897`, AD-7 amended `8c67a6d`); the five-point contract below. |
| `pts() -> tuple[int, ...]` | main | The pts with a stored proxy so far, ascending; cheap, never waits for `run`. |
| `proxy(pts_ticks) -> NDArray[uint8]` | worker | `(H, W, 3)` RGB; `KeyError` when absent. May overlap `run`. |
| `statistics(pts_ticks) -> Mapping[str, Statistics] \| None` | worker | Smoothed, every stage, for the parameters of the latest COMPLETED `run`; None otherwise. May overlap `run`. |

The factory `AnalysisFactory = Callable[[OpenedSource, CorrectionMethod, Engines], ClipAnalysis]` is called on the
main thread and only builds. The seam was frozen at the round-0 yield and changed only by the `retarget` ruling.

**`retarget`, the five-point contract (CHARC ruling).** (1) Main thread, cheap, never waits; called only while a
run is in flight (from the panel's `jobs.run` until that job's `on_done`); the panel raises `RuntimeError`
otherwise; an implementation returns False between its `run` returning and the `on_done`, never raises. (2) True:
the run in flight finishes under the new parameters and its done-ok means complete under them; the epoch guard
still drops any statistics fetched before the change. (3) False: not absorbed; at done-ok a follow-up
`run(latest)` starts if (method id, effective values) differ, and ALWAYS once any `retarget` of that run returned False
(the analysis may hold a job for the refused values; Reviewer B pass 1, #1). No run is cancelled for a parameter change; the
only cancels are the user's (D70, phase "cancelled"), a method change (Q-B, "superseded") and a source change or
close. (4) The stub returns False by default (`StubClipAnalysis(absorb=True)` absorbs); both paths are tested.
(5) WP4.3's adapter: `engine.set_parameters(values, focus_pts)` returning None while the engine runs means True;
if it RETURNS a job, the adapter keeps it, returns False and runs it at the next `run()`, never dropping it and
never on the main thread.

"Parameters differ" means (method id, `imaging.effective_parameters`), not `ParameterSet ==` (the set carries
`created`, `source`, `settings`).

## The state machine (AD-15)

| Event | Phase set | Statistics |
|---|---|---|
| video opened | `running(0, nb_frames or None)` | none |
| progress | `running(done, total, msg)` | - |
| done ok, run not cancelled, parameters equal the run's and no `retarget` of the run returned False | `complete` | switch: commit the shown pts with `statistics(pts)` |
| done ok, parameters differ, or any `retarget` of the run returned False (even if the parameters are back at the run's own) | stays `running("Updating statistics")` | `None`; follow-up `run(latest)` from `on_done` |
| done failed | `failed(message)`, error owner `"analysis"` | `None` |
| user Cancel (or any cancel) | `cancelled` at the job's `on_done` | `None` |
| method change while running | stays `running`; the run is cancelled as "superseded", the new analysis starts from its `on_done` | `None` |
| parameters changed, running | unchanged; `retarget` | unchanged |
| parameters changed, complete | `running("Updating statistics")` | `None` at once; `run(latest, focus_pts=shown)` |
| source changed | the panel drops the old run (cancelled by the generation bump) and starts the new source's analysis | all callbacks of the old generation are ignored |
| runner closed (window close) | the runner cancels every job and delivers its `on_done`: `cancelled`; a run that cannot start because the runner is closed (a superseded run's rebuild, an Analyse, a recompute) ends in `cancelled` too, never `running` with no job | `None` |

## The drag rule (the latest-intent invariant, in plain words)

Every user event takes the next number from one sequence: pressing the slider, changing its value, releasing it,
and the switch at completion; the newest is the "intent". A fix (the statistics of a frame the shell decoded at
another pts) and the re-show of the drag's proxy take numbers too but are not intents. A result from the
position lane is used only if it still belongs to the newest intent: a commit if it IS the newest intent, a fix if
the commit it repairs is, a proxy if the slider is still down in the drag it was asked for and the handle is on
its value. So while the slider is down the handle belongs to the hand and nothing moves it; each value shows the
stored proxy of its pts (never `set_position`); pressing, even without moving, asks for the proxy under the hand
and drops any commit still in flight; a frame the shell decodes meanwhile only makes the same proxy be shown again
(the shell would otherwise paint that older frame over it). On release the panel always commits `pts()[value]`,
with the smoothed statistics when the phase is complete, and a decode that lands at another pts, or fails, is
paired with its own statistics or the last shown frame's. At most one lane job is in flight, the latest request
is kept, and a failure of a superseded request is dropped, not presented. The code in `timeline.py` (`_take_intent`,
`_current`, `_reshow_proxy`, `_on_pressed`, `_on_released`, `_follow`) is this rule and nothing else; the
module docstring states it.

## The mapping for WP4.3 (WP3.11 and WP3.12 as merged; all members are served, no STOP)

| Seam member | WP3.11 / WP3.12 names | Notes |
|---|---|---|
| factory `(source, method, engines)` | builds the adapter only. The engine is `AnalysisEngine(method=, backend=engines.select_backend(settings, h, w, method.id)[0], cache=engines.cache, key=DiskProxyCache.key_for(path) / cache_key(path, codec), source=engines.video_source, probe=source.probe, params=, window_s=, kind=, hw_decode=)` | The engine needs `params` at construction and the factory has none: the adapter builds the engine lazily in its first `run` (a worker thread: also takes `os.stat` and the backend selection off the main thread). |
| `run(parameters, progress, focus_pts)` | First call: `engine.set_parameters(eff, focus_pts)` (phase none: adopts, returns None), then `job = engine.analysis_job()`. Later: `job = engine.set_parameters(eff, focus_pts)`; if None and phase in {none, cancelled, failed}: `job = engine.analysis_job()`; if None and complete/running: return. Then `result = job(progress)`; `result.ok` -> return; `result.failure == analysis.CANCELLED` -> return; else `raise RuntimeError(result.failure)` | `eff = imaging.effective_parameters(method, parameters)`. DR-47: a cancel racing `mark_complete` leaves the engine complete and `run` returns; the GUI, which cancelled, reports "cancelled"; "Analyse" -> `set_parameters` None, phase complete -> returns at once. |
| `pts()` | `cache.lookup(key).pts_ticks` (ascending; in-progress entries are returned; None -> `()`) | **F-2 (CHARC point 5).** `DiskProxyCache.lookup` takes the cache lock, touches the last-use stamp and sorts up to ~20,000 ticks, on the MAIN thread, once per progress delivery (20/s) while the writer stores proxies. The seam says "cheap, never waits for `run`"; the real cost is WP4.3's to re-measure with V7. Expected fix: the adapter keeps its own pts list, refreshed by a worker. |
| `retarget(params, focus_pts)` | `job = engine.set_parameters(eff, focus_pts)`: None while the engine runs -> True (the job absorbs it); a job RETURNED (the run finished between the panel's call and the engine's lock) -> the adapter KEEPS that job, returns False, and runs it at the next `run()`; it never drops the job and never runs it on the main thread | Cheap (engine lock only); the panel never overlaps runs, and since `retarget` returned False the run's `on_done` ALWAYS starts a follow-up `run(latest)` (even when the parameters were changed back to the run's own, A-B-A), so the kept job is run by it and the panel never declares complete while the engine holds a job. |
| `proxy(pts)` | `cache.proxy(key, pts)` | A new array each call; `KeyError` when absent. |
| `statistics(pts)` | `engine.smoothed_record(pts)`; `KeyError` -> None; unknown engine -> None; **and None until a full `run` of the adapter has completed under the latest parameters** (Reviewer B pass 1, #3) | WP3.11 serves a frame's smoothed record after the recompute near-phase, while the whole run is still running, and while it holds a kept recompute job; the seam says "None while no completed run", so the adapter gates on its own completed-run state (set when `run` returns ok, cleared at the start of any `run`, and whenever it keeps a job). A direct `engine.smoothed_record` mapping would break the seam. `schema_hash` is the engine's own concern; the GUI's epoch guard sits above it. Unused by design: `provisional_record(pts)` (WP3.16 measures the D108 provisional preview on its own float proxy). |
| progress | the engine reports `(done, total, message)` in cumulative frame-stage units, `total` None while unknown | The panel's label is the reported text (non-ASCII backslash-escaped), or the run's own label ("Analysing the clip", "Updating statistics") for an empty text; the first `running(0, nb_frames)` is replaced at the first report. |
| cancel | `progress.cancelled()` is checked by the engine after every frame | `engine.cancel()` is not needed: the GUI cancels through the job handle. |

## Limits

- **Late cancel (R2 #1).** A third-party `jobs.cancel()` or `close()` that lands after the job callable's last
  `progress.cancelled()` check but before `on_done` is delivered reads as complete. The data is complete at that
  moment, and `contract.JobHandle` (frozen, WP3.16) has no cancelled query to close the window. The GUI's own
  cancels (user, method change, source change) are tracked by `run.reason` and the source generation and never
  reach it. Beside it, the reverse reading is accepted (DR-47's shape): a cancel that lands after the analysis
  really finished, but before the callable's check, reads as "cancelled", and "Analyse" then costs the engine
  nothing.
- **Q-E extra decode.** The completion switch is `set_position(shown_pts, statistics=...)`, which decodes the shown
  frame again (one code path with the commit; the lane orders it against a scrub in flight). `set_statistics`
  would avoid the decode but is right only when none is in flight.
- **One job per `ClipAnalysis`.** The lane's one-job rule is per analysis object: after a source change a lane
  job of the old source may still run on the old object while the new source's first lane job starts on the new
  one. The old job is cancelled and its result is dropped by the generation check; it never reaches the session
  (F5; commented in `_on_source`).
- **`JobRunner.cancel()` by anyone is a cancel**, whatever its reason: the panel's result is "cancelled" (and the
  window close does the same).
- **A proxy is shown only for the handle's value.** While the hand moves faster than one proxy read, the preview
  shows nothing new until it pauses for one read (option S of the round-5 ruling); a read takes a few ms.
- **Stub only.** The stub claims no AD-5 or AD-3 fidelity, ignores `focus_pts`, returns False from `retarget`
  unless `absorb=True`, and does not raise for a retarget with no run in flight (it cannot tell the window after a
  run's end from a bug; the panel raises).
- **Interleaving test scope and timing.** `scenario_interleave` covers the drag/commit/decode lane only (press,
  move, release, lane results and decodes in any order; decode as requested, at another pts, or failed; the
  statistics passed to `set_position` and `set_statistics` are checked to be None or the frame's own). The
  completion switch, parameter and method changes, cancel, source change and read failure have dedicated tests.
  200 seeds x 28 steps run in about 0.2 s (the planted panels about 0.15 s each, failing at seeds 0 to 17), with
  the lane jobs run by hand (`ManualRunner`) so the order is deterministic.
- **V7** is asserted for the stub on this laptop with a NumPy analysis that releases the GIL; a method holding the
  GIL in pure Python, and the real engine, are out of envelope and WP4.3 re-measures (with F-2).
- Out of scope: the analysis engine (WP3.11), the corrected scrub proxy (a later enhancement if V2 asks),
  GoPro data, chapters (v2).

## Debt and decided items (brief)

| Item | Disposition |
|---|---|
| DR-44 (a) | ADDRESSED (consumer side): only pts from `ClipAnalysis.pts()` are requested; every `frame_decoded` pairs the shown frame with its own statistics (re-supplied at another pts, restored after a failure, `None` after a parameter or method change); a test per path. |
| DR-44 (b) | ADDRESSED for this package: owners `"timeline"` and `"analysis"` on every present and clear. |
| DR-44 (c) | Not this package's (WP4.3). |
| DR-23 / AD-6 | Not reopened: no index is ever a key; a VFR clip test. |
| AD-15 | IMPLEMENTED on the GUI side (states through `Session.set_analysis`; the shell derives the export reason). |
| AD-5, DR-25 | Not this package's (WP3.11); the stub claims no fidelity. |
| D98 | A one-stage method works (test). |
| DR-47 | The late-cancel reading above. |
| DR-43, V12 | Not this package's / deferred to v2. |
| F-2 (`DiskProxyCache.lookup` on the main thread) | Routed to WP4.3's V7 re-measure; the expected fix is in the mapping table. |

## Review

Reviewer A (STRONG, WSL, `gpt-5.6-sol` high, five rounds, evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.18\r1`
to `r5`): round 1 found F1, F2, F4 (MAJOR) and six minors (F3 rejected by reading); round 2 found R2 #3 (MAJOR),
#4, #5 (#1 downgraded to a documented limit, #2 rejected by reading and CONFIRMED by the orchestrator); round 3
found R3 #1 (MAJOR, a defect of the R2 #3 fix) and #2; round 4 found R4 (MAJOR, a press without a move). After four
rounds of ordering defects in the same lane the orchestrator ordered a design guard: the lane was restructured to
the one latest-intent rule and a seeded interleaving test added. Round 5 found one invariant discrepancy (an older
proxy of the same drag shown for one read), ruled MINOR by effect and closed by option S (the proxy counts only
for the handle's value) with three test-side items; the five-round gate ended the loop there with no blocking
finding open. Every product fix has a test that fails on the code before it (shown on an `e51d40f`, `62ddd2f`,
`e266e8c`, `732872e` or `fa0fa7d` copy).

**Procedural breach, disclosed.** In the round-3 verdict turn the cell adjudicated the round and also remediated its
two findings (`c471bca`, `732872e`), against "make NO change in the turn that adjudicates a round". The
orchestrator noted the breach and did not void the change (each fix was reproduced first and has a test that fails
on the old code). Rounds 4 and 5 kept the rule: the verdict turns changed nothing but the ledger.

**Reviewer B pass 1** (the orchestrator's Codex pass at its seat, on the merge candidate `44ef658`, all findings
REASONED, verdict NEW_CRITICAL_MAJOR_FOUND): #1 MAJOR (an A-B-A burst between the run's return and its `on_done`
declared complete while the engine held B's job), #2, #3, #4 MINOR. Remediated by seat 3 in `a49c36a` (#1: a run
whose `retarget` returned False always follows up in `on_done`; the test stub models the retained job, so a premature
complete is observable; three of five bursts failed on `579321a`), `6f5fd11` (#2: the progress label is the reported
text, ASCII-escaped, the run's label when empty), `f50aee0` (#4: `_start_run` meeting a closed runner sets
`cancelled`; two tests failed on `579321a`), and this report (#3: the adapter returns None until its own full `run`
completed; no code, the mapping row says it; `analysis_service.py` holds the seam text only, which already says
"the latest completed run"). `bd2d70b` wraps a docstring line. The interleaving oracle covers the position lane
only; the burst window is covered by its own parametrised test.

## Gates

- `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy` (strict, 119 source files): green at the
  final head.
- Targeted pytest (`tests/test_gui_timeline.py`, `tests/test_gui_analysis_service.py`, `tests/test_gui_deps.py`,
  headless, foreground): 82 passed in about 16 s at `bd2d70b` (71 at `579321a`), repeated runs.
- Full pytest: run by the orchestrator on the merge candidate (stacked gate).
- No harness gate (no `scripts/`, `.claude/` or kernel doc changed). Footage folder not used.
