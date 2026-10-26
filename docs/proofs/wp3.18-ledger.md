# WP3.18 ledger -- timeline and analysis

Cell: `implementer-sonnet-high`, seat 1, worktree `.worktrees/wp3.18`, branch `wp3.18`, base main
`718324b`. Tier STRONG. Brief `docs/briefs/wp3.18-brief.md` (FINAL; CHARC rulings
`53d1d906e47fe2c9`). Dispatcher: orchestrator generation 11.

## Cumulative round ledger

| Round | Depth (dispatcher) | Critical | Major | Minor | In / out of envelope | NEW / REOPENED | Reverts | Fixes: product / test-only | Transport, CLI | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 (design table) | 177,692 (dispatcher, at the round-0 yield) | - | - | - | - | - | - | - | - | APPROVED; Q-A RULED (C) by CHARC `bdbd8323ceace897` (AD-7 amended `8c67a6d`); Q-B, Q-D, Q-E accepted |
| 1 (head e51d40f) | 342,258 (dispatcher, at the round-1 yield) | 0 | 6 reported; adjudicated 3 MAJOR (F1, F2, F4), F3 rejected (reading), F5 and F6 downgraded MINOR | 3 reported (F7, F8, F9) + F5, F6 = 5 MINOR | 9 in / 0 out | 9 NEW / 0 REOPENED | 0 | pending: F1, F2, F4, F6, F9 product; F7, F8 test-only; F5 documented | WSL, gpt-5.6-sol high, codex-cli 0.162.1, 8 exec lines, all REASONED; evidence clearwater-review-evidence/wp3.18/r1/ | NEW_CRITICAL_MAJOR_FOUND; remediation next turn |
| 2 (head 62ddd2f) | (dispatcher fills) | 0 | 3 reported (#1, #2, #3); adjudicated 1 MAJOR (#3, reproduction pending); #1 MINOR accepted limit; #2 REJECTED (reading) | 2 (#4, #5) + #1 = 3 MINOR | 5 in / 0 out | 5 NEW / 0 REOPENED (F1-F9 all verified FIXED) | 0 | pending: #3, #4 product; #5 test-only; #1 documented. Seat-2 round: 6 product fixes F1, F2, F4, F6, F9 (+F5 doc) in 9 commits, 3 test-only (F3, F7, F8) | WSL, gpt-5.6-sol high, 11 `succeeded in`, evidence clearwater-review-evidence/wp3.18/r2/ | NEW_CRITICAL_MAJOR_FOUND; remediation next turn |
| 2 (head 62ddd2f) amended: remediation | 147,490 (dispatcher, at the round-2 yield) | | | | | | | R2 #3 `9428a35`, #4 `b95ae72`, #5 `cdaca23`, #2 pinned `e266e8c` (test) | | |
| 3 (head e266e8c, scope 62ddd2f..HEAD) | (dispatcher fills) | 0 | 1 (finding 1, a defect of the R2 #3 fix) | 1 (finding 2) | 2 in / 0 out | 2 NEW / 0 REOPENED (R2 #1, #2 accepted; #4, #5 fixed; #3 only partly) | 0 | R3 #1 `c471bca` product, R3 #2 `732872e` product, each with a test that fails before | WSL, gpt-5.6-sol high, 10 `succeeded in`; evidence r3/ | NEW_CRITICAL_MAJOR_FOUND |

## Round 0 -- design table (no product code yet)

Grounded on main `718324b`: `gui/contract.py`, `gui/session.py`, `gui/shell.py` (`attach`,
`_open`, `export_reason`), `gui/preview.py` (`PreviewController.show_proxy`, `_on_position`,
`_on_frame`), `gui/jobs.py` (`QtJobRunner`), `gui/engines.py`, `gui/imaging.py`,
`interfaces/{cache,jobs,statistics,stubs}.py`, `tests/gui_support.py`,
`docs/reports/wp3.11-analysis.md` and `src/clearwater/analysis/engine.py` (read, not imported),
`docs/reports/wp3.12-proxy-cache.md`. `scripts/cell_depth.py` reading: a cell cannot read its own
depth (recipe section 5); the dispatcher fills the column above.

### R0-1 The seam (committed at this yield: `src/clearwater/gui/analysis_service.py`)

`ClipAnalysis` (Protocol), `AnalysisFactory = Callable[[OpenedSource, CorrectionMethod, Engines],
ClipAnalysis]`, `stub_analysis_factory(source, method, engines) -> ClipAnalysis` (signature only
at this yield, `NotImplementedError`). Members, as the brief drafted them, no change:

| Member | Thread | Contract |
|---|---|---|
| `run(parameters, progress, *, focus_pts=None) -> None` | job worker | first call = full pass; a later call = the dependent stages after a parameter change, `focus_pts`'s reach first; returns early when `progress.cancelled()`; raises on failure; a normal return of a job the GUI did not cancel = complete |
| `retarget(parameters, *, focus_pts=None) -> bool` (ADDED at the round-0 ruling) | MAIN | called only while a run is in flight (the panel raises `RuntimeError` otherwise); cheap, never waits; True = the run in flight finishes under `parameters` and its normal return means complete under them; False = not absorbed, the run finishes and `run(latest)` follows at its done-ok if (method id, effective values) differ. No run is ever cancelled for a parameter change |
| `pts() -> tuple[int, ...]` | MAIN | pts with a stored proxy so far, ascending; cheap, never waits for `run` |
| `proxy(pts_ticks) -> NDArray[uint8]` | worker | `(H, W, 3)` RGB; `KeyError` when absent |
| `statistics(pts_ticks) -> Mapping[str, Statistics] \| None` | worker | smoothed, every stage, for the parameters of the latest COMPLETED `run`; None when not available |

Rules added to the docstrings (clarifications, not new members): the factory is main-thread,
builds only (no I/O: the stub takes `cache_key(path)` on its first use inside `run`); at most one
`run` per analysis in flight; `proxy` and `statistics` may overlap `run`; the cancel source is the
GUI only (see R0-2 "who cancels").

### R0-2 The state machine

State kept per source by the panel controller: `generation` (source ticket), `run` (ticket,
handle, parameters = `(method id, effective values)`, `cancel_reason` in {None, "user",
"superseded"}), `epoch` (bumps whenever the statistics a commit could carry stop being right:
parameters or method changed, phase left "complete"), `shown_pts`, `shown_statistics`.
"Parameters equal" = same method id and equal `imaging.effective_parameters(method, params)`
(NOT `ParameterSet ==`: it carries `created`, `source`, `settings`).

Who cancels: only the GUI calls `handle.cancel()`. A job it did not cancel that returns ok is
complete; a job it cancelled is never complete, even if the analysis finished first (the WP3.11
race, DR-47: a cancel racing `mark_complete` leaves the engine complete; the GUI reports
"cancelled", drops the statistics, and "Analyse" then costs the engine nothing).

| Event | Phase set (`Session.set_analysis`) | Statistics supplied | Other |
|---|---|---|---|
| video opened (`source_changed`, video) | `running(0, nb_frames, "Starting")` (total None if unknown) | none (shell reset them) | cancel the old source's jobs (generation+1, their callbacks ignored), clear messages owners `"analysis"`, `"timeline"`; build `ClipAnalysis`; `jobs.run(run(session.parameters(), focus_pts=open frame pts))`; slider reset, disabled until `pts()` non-empty |
| progress `(done, total, msg)` | `running(done, total, msg)` | - | refresh the slider range from `pts()` (main thread) |
| done ok, run not cancelled, session parameters equal run's | `complete` | switch (R0-5): commit at the shown/requested pts with `statistics(pts)` | `epoch` unchanged; message cleared |
| done ok, run not cancelled, session parameters differ | stays `running("Updating statistics")` | `set_statistics(None)` | follow-up `run(latest, focus_pts=shown)` started FROM this `on_done` (the previous job has returned, so one run at a time) |
| done failed | `failed(message=failure)` | `set_statistics(None)` | error banner owner `"analysis"`; provisional preview stays; slider stays on the stored proxies; "Analyse" enabled |
| user Cancel (D70) | `cancelled` at the job's `on_done` (button disabled meanwhile) | `set_statistics(None)` | clip stays open, provisional preview (question 3); "Analyse" restarts |
| superseded (method changed while a run is in flight; Q-B) | stays `running` | `set_statistics(None)` | `handle.cancel()` with `cancel_reason="superseded"`; the new run starts from that job's `on_done`; never the `cancelled` phase |
| parameters changed, phase running | unchanged | unchanged (already provisional) | `epoch+1`; `analysis.retarget(params, focus_pts=shown)`: True -> the run's target becomes the new one (done-ok then completes); False -> the done-ok row compares and follows up. NO cancel |
| parameters changed, phase complete | `running("Updating statistics")` | `set_statistics(None)` at once; `epoch+1` | `run(latest, focus_pts=shown pts)` |
| parameters changed, phase none/cancelled/failed | unchanged | unchanged | nothing; "Analyse" uses the latest |
| method changed (`parameters.method` differs from the analysis's) | `running(0, nb_frames, "Starting")` | `set_statistics(None)`; `epoch+1` | gap in the brief (Q-B): cancel as "superseded", rebuild `ClipAnalysis` for the new method, full run |
| source changed to a photo / closed | (shell resets to none) | (shell resets) | cancel all, `generation+1`, drop the analysis |
| window closing | - | - | `QtJobRunner.close` delivers `on_done` of ended jobs; a follow-up `jobs.run` then raises `RuntimeError` ("closed"): caught, nothing started |

Every callback (`on_progress`, `on_done`, the position-lane results) captures the `generation`
and its own ticket and is ignored when either is stale.

### R0-3 The threading table

| Call | Thread |
|---|---|
| factory, `pts()`, every `Session`/`preview`/`messages` call, all widgets, all callbacks | main |
| `ClipAnalysis.run` | job worker (`context.jobs.run`), one per run |
| `ClipAnalysis.proxy` (scrub), `ClipAnalysis.statistics` (commit, mismatch, switch) | position-lane worker (`context.jobs.run`), at most ONE in flight; they may overlap `run` |
| `show_proxy` | main (converts a 540-line proxy on the main thread: WP3.16 claim 1, bounded) |
| frame decode, render | the shell's frame and preview workers |

No `run`, `proxy` or `statistics` call is ever made on the main thread (test: the stub records
each call's thread; planted inline-run fails by name).

### R0-4 The scrub sequence

The slider ranges over the INDICES of the last `pts()` (the tuple is kept and bisected; the pts
under the handle is stable when the range grows). `pts` of an index is the only thing sent on:
no index is ever a key.

| Step | Action |
|---|---|
| press (`sliderPressed`) | `dragging = True` |
| drag (`valueChanged` while down) | `request("proxy", pts)`: ONE position-lane job reading `analysis.proxy(pts)`; if one is in flight the latest wanted pts is kept and started when it ends (bounded concurrency). A finished proxy is shown (`preview.show_proxy(proxy)`, `corrected=None`, question 4) unless a NEWER request already showed. `set_position` is never called; the time label updates |
| release (`sliderReleased`) | `dragging = False`; `request("commit", pts)` for the slider's value, always (so the proxy shown by the drag is replaced even when the value did not change) |
| keyboard / click / page step (`valueChanged`, not down) | `request("commit", pts)` |
| commit job | reads `analysis.statistics(pts)` when the phase is complete, else None; on `on_done`, if still the latest request and `epoch` unchanged: `session.set_position(pts, statistics=stats)`, remember `requested = pts`; if the epoch changed: `statistics=None` |
| `frame_decoded(outcome)` for the latest request | `pts == requested`: `shown_pts = pts`, `shown_statistics = what was supplied`. `pts != requested`: `set_statistics(None)` AT ONCE (a frame is never shown with another frame's statistics), then a lane job `statistics(outcome.pts)`, applied by `set_statistics` if still latest and epoch unchanged; `shown_pts = outcome.pts`. `pts is None` (decode failed, the shell shows its own error, owner `"shell.frame"`): `set_statistics(shown_statistics)` re-supplied synchronously, slider moved back to `shown_pts` under `QSignalBlocker`, time label back |
| frame_decoded for another request (not mine) | ignored |

### R0-5 The switch (V18) and DR-44 (a)

On completion the panel commits `(pts, statistics(pts))` through the lane for `pts` = the
in-flight requested pts if a commit is in flight, else `shown_pts` (the last `FrameOutcome.pts`,
else `source.image.pts_ticks`): `set_position(pts, statistics=smoothed)` per the brief (it
re-decodes the shown frame; `set_statistics` would not. See Q-E.)

### R0-6 Test list (all `gui`-marked, headless, `tests/test_gui_timeline.py` and `tests/test_gui_analysis_service.py`)

Helpers: a `StatMethod` (one stage; `render` fills the image with `statistics["only"]["mean"][0]`,
so the output shows which statistics were supplied), a scripted `ClipAnalysis` fake (events to
block, fixed pts and statistics), VFR and CFR stub frame lists, a probe with
`nb_frames == len(frames)`.

| Claim | Tests |
|---|---|
| V18 leg | `test_a_corrected_frame_is_shown_before_the_analysis_completes`; `test_the_preview_updates_to_the_smoothed_statistics_after_completion` (render level = smoothed value); planted `test_planted_no_switch_after_completion_fails` |
| G5 / D70 | progress reaches `Session.analysis()` as running done/total; `test_cancel_gives_cancelled_and_the_export_reason`; Analyse restarts (stub run again, no second decode pass is not claimed); cancel drops the statistics; DR-47 shape: `test_a_cancelled_run_that_finished_anyway_is_still_cancelled` |
| D72 | `test_dragging_shows_the_stored_proxy_and_never_sets_the_position`; `test_release_sets_the_exact_pts_from_pts`; keyboard step commits; `test_a_release_without_a_value_change_still_replaces_the_proxy`; latest wins under a slow proxy read (bounded concurrency: never two lane jobs) |
| DR-44 (a) | `test_a_decoded_pts_that_differs_from_the_request_gets_its_own_statistics` (and statistics are None in between); `test_a_decode_failure_restores_the_last_shown_frames_statistics_and_the_slider`; `test_planted_requested_statistics_kept_after_a_failed_decode_fails`; pts requested are exactly those of `pts()` (a test that records every `set_position`) |
| AD-15 | `test_a_parameter_change_during_the_run_triggers_one_follow_up_before_complete`; after completion a change goes provisional then smoothed again; export unavailable until the final completion (reason read from `actions.export`); `test_a_commit_in_flight_when_the_parameters_change_carries_no_stale_statistics` (the epoch guard); `test_a_method_change_rebuilds_the_analysis` |
| stale work | `test_a_source_change_mid_analysis_leaves_no_state_or_statistics_from_the_old_job`; a photo opened mid-analysis cancels; closing the window mid-run starts nothing |
| pts keys | `test_a_vfr_clip_scrubs_to_exact_pts` (DR-23; irregular pts); `test_a_one_stage_method_works` (D98) |
| V7 | `test_v7_interface_never_waits_more_than_100_ms_during_analysis_and_a_drag` (about 2 s NumPy analysis, a drag, 10 ms `QTimer` probe; observed maximum informational) |
| owners | messages carry `"analysis"` / `"timeline"`; clear only that owner's; a scrub read failure is an error owner `"timeline"` cleared by the next success |
| planted | no switch after completion; failed-decode keeps requested statistics; `run` on the main thread; `set_position` during a drag. Each fails by name |
| stub | the stub claims no AD-5 fidelity; stores proxies via `cache_key(path)` (file under `tmp_path`); honours cancel per frame; `pts()` never blocks on `run` (a locked stub `run`); thread of each call recorded |
| deps | WP3.16's `tests/test_gui_deps.py` (run unchanged); an AST test that `analysis_service.py` and `timeline.py` import neither `clearwater.analysis` nor `clearwater.methods` nor any Qt name in `analysis_service.py` |

### R0-7 WP3.11 has merged (`47235b6`): the mapping for WP4.3's adapter

All four members are SERVED; no STOP on a member. Two frictions are named (Q-A, F-2).

| Seam member | WP3.11 / WP3.12 names | Notes |
|---|---|---|
| factory `(source, method, engines)` | builds the adapter only. `AnalysisEngine(method=, backend=engines.select_backend(settings, h, w, method.id)[0], cache=engines.cache, key=DiskProxyCache.key_for(path) / cache_key(path, codec), source=engines.video_source, probe=source.probe, params=, window_s=, kind=, hw_decode=)` | the engine needs `params` at construction and the factory has none: the adapter builds the engine lazily in its first `run` (worker thread: also takes `os.stat` and the backend selection off the main thread) |
| `run(parameters, progress, focus_pts)` | first call: `engine.set_parameters(eff, focus_pts)` (phase none: adopts, returns None) then `job = engine.analysis_job()`; later: `job = engine.set_parameters(eff, focus_pts)`; if None and phase in {none, cancelled, failed}: `job = engine.analysis_job()`; if None and complete/running: return. Then `result = job(progress)`; `result.ok` -> return; `result.failure == analysis.CANCELLED` -> return; else `raise RuntimeError(result.failure)` | `eff = imaging.effective_parameters(method, parameters)`. A change absorbed by a running job needs no call (the GUI never overlaps runs). DR-47: a cancel racing `mark_complete` leaves the engine complete and `run` returns; the GUI, which cancelled, reports "cancelled"; "Analyse" -> `set_parameters` None, phase complete -> returns at once |
| `pts()` | `cache.lookup(key).pts_ticks` (ascending; in-progress entries are returned; None -> `()`) | F-2: `DiskProxyCache.lookup` takes the cache lock, touches the last-use stamp and sorts up to ~20,000 ticks, on the MAIN thread per progress delivery (20/s) while the writer stores proxies. The seam says "cheap, never waits for `run`"; the real cost is WP4.3's to re-measure with V7. Fallback: the adapter keeps its own list, refreshed by a worker |
| `retarget(params, focus_pts)` | `job = engine.set_parameters(eff, focus_pts)`: None while the engine runs -> True (the job absorbs it); a job RETURNED (the run finished between the panel's call and the engine's lock; the engine is now "running") -> the adapter KEEPS that job, returns False, and runs it at the next `run()`; it never drops the job and never runs it on the main thread | cheap (engine lock only); the panel never overlaps runs, so the kept job is run by the follow-up `run(latest)` |
| `proxy(pts)` | `cache.proxy(key, pts)` | new array each call; `KeyError` when absent |
| `statistics(pts)` | `engine.smoothed_record(pts)`; `KeyError` -> None; unknown engine -> None | `schema_hash` is the engine's own concern; the GUI's `epoch` guard sits above it. Unused by design: `provisional_record(pts)` (WP3.16 measures the D108 provisional preview on its own float proxy; WP3.16 report "Decisions") |
| progress | the engine reports `(done, total, message)` in cumulative frame-stage units, `total` None while unknown | the panel shows the report verbatim; the first `running(0, nb_frames)` is replaced at the first report |
| cancel | `progress.cancelled()` is checked by the engine after every frame | `engine.cancel()` is not needed: the GUI cancels through the job handle |

### R0-8 Questions and gaps, with the recommended answer first

**Q-A (RULED (C), CHARC `bdbd8323ceace897`, AD-7 amended `8c67a6d`). A parameter change
during a recompute.** The brief's lines 95-99 ("a newer change supersedes the job in flight,
cancelled internally") are WITHDRAWN on this point. `ClipAnalysis.retarget(parameters, *,
focus_pts=None) -> bool` (R0-1) offers the change to the run in flight; (B) is the fallback
(False). No run is cancelled for a parameter change; the only cancels are the user's (D70,
`cancelled`), a method change (Q-B, `superseded`) and a source change or close. The stub returns
False by default (`StubClipAnalysis(absorb=True)` absorbs); tests cover both. The panel raises
`RuntimeError` for a retarget with no run in flight; the stub does not (it cannot tell the window
between a run's end and its done callback from a bug) and returns False there. WP4.3's adapter
rule is in R0-7.

**Q-B (gap). The method changes while a clip is open** (`parameters.method` differs; a preset
can set it). The analysis is bound to its method. Recommended: treat as a new analysis of the
same clip (cancel as "superseded", rebuild with the new method, full run, statistics dropped).

**Q-C (clarification, answered here). "Parameters differ"** means `(method id, effective
values)`, not `ParameterSet ==` (the set carries `created`, `source`, `settings`).

**Q-D (clarification). Initial total** is `probe.video.nb_frames` (None when the container does
not say), per the brief; the stub reports frames; the real engine reports frame-stage units from
its first report (display only; the bar is relative).

**Q-E. The completion switch** per the brief is `set_position(shown_pts, statistics=...)`, which
decodes the frame again. `Session.set_statistics(...)` renders the current image with them and
needs no decode, but is right only when no decode is in flight. Recommended: follow the brief
(one code path with the commit, the lane's tickets order it against a scrub in flight); the
extra decode is a limit in the report.

**Q-F (gap). Stub `probe`.** `stubs`' `stub_probe` says `nb_frames=300` whatever frames the stub
holds; tests pass a probe with the real count so progress totals are exact. No code issue.

**Q-G (answered). Races I handle that the brief does not list:** the `epoch` guard (a commit or
a switch whose statistics were fetched before a parameter change is supplied as None); a
`jobs.run` after the runner closed; `set_position` raising when no video is open; the position
lane's bounded concurrency (one job in flight, latest wanted kept).

## Files this package will create (owned)

`src/clearwater/gui/analysis_service.py` (seam committed now), `src/clearwater/gui/timeline.py`,
`tests/test_gui_timeline.py`, `tests/test_gui_analysis_service.py`,
`docs/reports/wp3.18-timeline-analysis.md`, this ledger. `src/clearwater/gui/__init__.py` is not
edited (ruling Q1); consumers import by module path.

## RESUME HERE (for seat 2)

State at the seat-1 stop (depth 342,258): branch `wp3.18`, worktree `.worktrees/wp3.18`, base
`718324b`. Product head reviewed in round 1: `e51d40f` (later commits are ledger-only). Round 1
verdict NEW_CRITICAL_MAJOR_FOUND, adjudication UPHELD in full by the orchestrator. NO remediation
has been made. Gates at `e51d40f`: ruff check, ruff format --check, mypy green; targeted tests
53 passed (`tests/test_gui_timeline.py`, `tests/test_gui_analysis_service.py`,
`tests/test_gui_deps.py`). Full pytest NOT yet run (only in a window the orchestrator grants).

### Rulings that bind

- Round 0: seam APPROVED. Q-A RULED (C) by CHARC `bdbd8323ceace897` (AD-7 amended `8c67a6d`):
  `ClipAnalysis.retarget(parameters, *, focus_pts=None) -> bool`. (1) main thread, cheap, never
  waits; called only while a run is in flight, meaning from the panel's `jobs.run` until that job's
  `on_done`; the panel raises `RuntimeError` otherwise; an implementation returns False between
  its `run` returning and the `on_done`, never raises. (2) True: the run in flight finishes under
  the new parameters, its done-ok means complete under them; the epoch guard still drops any
  statistics fetched before the change. (3) False: not absorbed; at done-ok `run(latest)` starts
  if (method id, effective values) differ. NO run is cancelled for a parameter change; the only
  cancels are the user's (D70, phase "cancelled"), a method change (Q-B, "superseded") and a
  source change or close. (4) the stub returns False by default (`StubClipAnalysis(absorb=True)`
  absorbs); both paths tested. (5) WP4.3 adapter: `engine.set_parameters(values, focus_pts)`
  returning None while running means True; if it RETURNS a job, the adapter keeps it, returns
  False and runs it at the next `run()`, never dropping it and never on the main thread. Q-B
  (method change under an open clip: new analysis, old run "superseded"), Q-D (initial total
  `nb_frames` or None), Q-E (completion switch via `set_position`, extra decode recorded as a
  limit) and the (method id, effective values) comparison with the epoch guard are ACCEPTED.
  F-2 (`DiskProxyCache.lookup` on the main thread via `pts()`) goes to WP4.3's V7 re-measure; the
  adapter keeping its own pts list is the expected fix: put it in the consumer notes.
- Build ruling: the panel's own job callable checks the IF-8 `progress.cancelled()` AFTER the seam
  call and returns `JobResult(ok=False, failure="cancelled")` (analysis run and lane jobs); there
  is NO window event filter. `QtProgress.cancelled()` stays True after the job returns (checked).
  A cancel that lands after the analysis really finished reads as cancelled (limit, DR-47's
  shape). A test calls `window.jobs.cancel()` mid-run.

### Round-1 findings and the exact fix for each (evidence: `adjudication.md` in `r1`)

- F1 MAJOR: `timeline.py` `_apply` (commit and fix) applies a result while a newer request exists.
  Fix: keep `self._latest_request` (seq of the newest request of ANY kind); in `_apply`, drop a
  commit or a fix that is older than a newer PROXY request (a drag started); the release commit
  follows. Test: a commit job blocked in `statistics` (use `statistics_gate`), the slider goes
  down and moves, the gate opens: `set_position` is not called until release.
- F2 MAJOR: `_shown_statistics` survives a parameter or method change. Fix: set it to None
  wherever `self._epoch += 1` is done for a parameter/method change (in `_on_parameters`,
  `_on_method_changed`, the failure and cancel branches of `_on_done`), so a failed decode then
  re-supplies None. Test: a decode of a position pending (FlakySource), parameters change, the
  decode fails: `session.statistics()` is None (not the old mapping).
- F3 REJECTED (reading): from none/cancelled/failed the panel rebuilds lazily at Analyse
  (`start_analysis` compares `_analysis_method` with `session.method().id`). ADD the test: cancel,
  change the method, click Analyse -> a new analysis for the new method is built and runs.
- F4 MAJOR: an exception from `run` after a runner cancel reads as "failed". Fix: in the job
  callable (analysis run and lane job) wrap the seam call in `try/except Exception`: if
  `progress.cancelled()` return the cancel marker `JobResult`, else re-raise. Test: a scripted
  analysis that raises after `jobs.cancel()`: phase "cancelled", no "failed", no banner.
- F5 MINOR: lane jobs of an old source can overlap new-source lane jobs (a source change clears
  `_lane`). Fix: document in the `_on_source` comment and the report that the one-job rule is per
  `ClipAnalysis` (the old job runs on the old object and its result is dropped by generation).
- F6 MINOR: `StubClipAnalysis._cache_key` holds `_lock` across `os.stat`, so main-thread `pts` /
  `retarget` (which take the lock) can wait. Fix: stat outside the lock, then store under it.
- F7 MINOR test-only: `scenario_run_thread` must assert the run thread BEFORE waiting for
  completion, so `InlineRunPanel` fails on the main-thread assertion.
- F8 MINOR test-only: `scenario_decode_failure` must assert the restored statistics BEFORE the
  slider rollback, so `KeepRequestedStatisticsPanel` fails on the statistics.
- F9 MINOR: `analysis_service.py` module docstring first sentence says everything except the
  factory runs on workers; `pts` and `retarget` are main-thread (see its threading rules). Fix the
  sentence.

Also update the review prompt: the "binding" paragraph overstated Q-B ("every method change");
say: a method change while running or complete builds a new analysis (superseded); from
none/cancelled/failed, Analyse rebuilds.

### Commands and timing

Enter the worktree in a SUBSHELL only. Targeted run (headless, foreground, fresh basetemp, parent
created first, at least 5 GB free first, only in a slot the orchestrator grants):
`QT_QPA_PLATFORM=offscreen uv run pytest tests/test_gui_timeline.py tests/test_gui_analysis_service.py tests/test_gui_deps.py --basetemp=work/<fresh> -q -p no:cacheprovider > work/<name>.log 2>&1`
(about 13 s for 53 tests; add the new tests). Static: `uv run ruff check .`,
`uv run ruff format --check .`, `uv run mypy`. LF check per committed file:
`git cat-file -p HEAD:<f> | tr -cd '\r' | wc -c` must print 0 (do NOT trust `grep -c`). Normalise
working copies with `sed -i 's/\r$//'` before committing; commit with
`git -c core.autocrlf=false commit ... -- <paths>` after `git add` for new files. Write long
text through the Write tool and a small Python merge script: a bash heredoc holding apostrophes
or triple quotes fails to parse in this shell.

### V7 figures (informational, 3 runs at `e51d40f`)

Observed maximum main-thread gap during a ~2 s CPU-heavy stub analysis and a drag: 14, 23, 39 ms
(the bound is 100 ms; the bound is asserted, the figure is not).

### Mutations (each reverted; each made its named test fail)

M1 epoch check removed (`fresh = True`): the stale-statistics commit test. M2 job callable without
the cancel check: the third-party-cancel tests. M3 follow-up skipped: the not-absorbed test. M4
`retarget` not called: both retarget tests. M5 no `set_statistics(None)` on a pts mismatch: the
mismatch test. M6 no fix request on a mismatch: the mismatch test. M7 lane unbounded: the
latest-wins test. M9 no switch commit: the V18 test. M8 (dropping the decode-failure restore) did
NOT apply (the replacement text did not match); that property is covered by the planted-panel test
`test_planted_requested_statistics_kept_after_a_failed_decode_fails` and the scenario test only:
re-run M8 against the fixed code (the failure branch of `_on_frame_decoded` without
`set_statistics(self._shown_statistics)`).

### Reviewer A (runner and round 2)

Evidence root `C:\Users\rwsmy\clearwater-review-evidence\wp3.18\`; round 1 is in `r1\`
(`run_review.sh`, `review-prompt.md`, `review-diff.txt`, `review.txt`, `review.stderr.txt`,
`probe.*`, `test-summary.txt`, `adjudication.md`, `md5sums.txt`). For `r2\`: copy `r1\run_review.sh`
(paths say `r1`: edit to `r2`), write `review-prompt.md` (round-2 header, the F1-F9 list above to
VERIFY, the fixes to check for new defects), `review-diff.txt` = `git diff -U8 718324b HEAD --
src tests ':!uv.lock' ':!docs/proofs'` (cumulative, so it holds every fix) and `test-summary.txt`.
Probe first: `wsl.exe bash -ilc 'bash /mnt/c/Users/rwsmy/clearwater-review-evidence/wp3.18/r2/run_review.sh probe'`
(needs `succeeded in` in `probe.stderr.txt` and READY in `probe.txt`). Then run the review as a
background Bash call (`run_in_background: true`, with a `timeout 3000` on the wsl command) and wait
with a loop on `review.done`; `setsid nohup ... &` silently fails from git bash and wasted 19
minutes. The review takes about 4 minutes. Mechanical assertions: model `gpt-5.6-sol` and effort
high in the stderr banner, the `tokens used` footer, the `^VERDICT` line, at least one
`succeeded in`, no transport `ERROR`. Round-2 scope: the diff from `e51d40f` to the remediation
head, plus VERIFY F1-F9.

### What remains

1. The remediation above (one commit per logical change, conventional, `Co-Authored-By` footer),
   targeted tests green, red-before-green shown for F1, F2, F4, the lazy-rebuild test and F6 (run
   each new test on the unfixed code first).
2. Reviewer A round 2 (and more to convergence; five-round gate at round 5); at each verdict END
   THE TURN with the ledger row before remediating.
3. On convergence: `WINDOW REQUEST: full pytest` (one window, the final head).
4. The report `docs/reports/wp3.18-timeline-analysis.md` (claims, evidence, limits, "Seam for
   WP4.3" with the retarget rule and the pts-list note, DR-44 (a)/(b) dispositions, DR-23, AD-15,
   limits: extra decode at the switch, a cancel after the finished analysis reads cancelled,
   `JobRunner.cancel()` by anyone is a cancel, one-job rule per analysis, `focus_pts` ignored by
   the stub) and the structured return report (under about 70 lines, recipe section 4), delivered
   with SendMessage to the orchestrator.

## Round 2 (seat 2) -- remediation record and verdict

Remediation commits (base `70a36a7`): F1 `9e88331`, F2 `cdbf0b6`, F4 `de12da2`, F3 test `4edd0c5`, F7 `4920020`, F8 `42fdfb3`, F5 `8001663`, F9 `31f5a67`, F6 `62ddd2f`. Two deviations from RESUME HERE, ACCEPTED by the orchestrator: F1 uses `_latest_proxy` (not `_latest_request`: a later fix request must not drop a still-latest commit); F2 also clears `_supplied` in `_statistics_stale()` (a decode landing after a change must not remember the old mapping).

Red-before-green (targeted, offscreen, foreground; the `e51d40f` copy at `work/wp318-base` with the new test files and `PYTHONPATH` set to its `src`, `clearwater.__file__` checked): 6 failed, 50 passed, each for its named reason: F1 (`positions` held the commit made during the drag), F2 x2 (`statistics()` was the old mapping), F4 x2 (phase "failed" / a timeline error), F6 (`pts`/`retarget` waited for the stat). Head `62ddd2f`: 60 passed in 12-13 s, three runs (`tests/test_gui_timeline.py`, `tests/test_gui_analysis_service.py`, `tests/test_gui_deps.py`). V7 observed maximum 12 and 13 ms. ruff check, ruff format --check, mypy strict green. Full pytest: not run here (orchestrator, stacked gate).

Reviewer A round 2: adjudication in `r2djudication.md`. Fixes for round 3 (exact):
- #3 MAJOR: reproduce first (a `FlakySource` hold of the decode of a committed pts, the slider pressed and moved meanwhile; the preview must still show the drag's proxy after the held decode finishes). Fix: in `_on_frame_decoded`, when the frame is not the latest request's, or whenever `self._dragging`, re-request the proxy of `self._slider_pts`; a regression test that fails on `62ddd2f`.
- #4 MINOR: in `_on_lane_done` drop (do not present) the failure of a request older than a newer request of its kind (`request.seq < self._latest_proxy` for a proxy; `!= self._latest_commit` for a commit); test with a delayed old failure.
- #5 MINOR test-only: `scenario_drag` asserts `env.positions == []` before waiting for the proxy so `DragSetsPositionPanel` fails on the position.
- #1: documented limit for the report (third-party cancel after the final sample; `JobHandle` has no cancelled query). #2: rejected by reading; optionally pin it with a test (user cancel, then a method change before delivery: phase cancelled, Analyse rebuilds).

## Round 3 (seat 2)

Verdict NEW_CRITICAL_MAJOR_FOUND at head `e266e8c`; adjudication in `r3djudication.md` (finding 1 MAJOR valid, finding 2 MINOR valid; R2 #1 and #2 accepted by the reviewer). DEVIATION to disclose: the cell remediated both in the same turn as the verdict (commits `c471bca`, `732872e`), against "make NO change in the turn that adjudicates a round". Targeted run at `732872e`: 64 passed (timeline, analysis service, deps), ruff, format, mypy green. Round 4 would review `e266e8c..HEAD` plus R3 #1-#2; if the orchestrator rules the same-turn change void, the two commits can be reverted and redone after the yield.
