# WP3.18 ledger -- timeline and analysis

Cell: `implementer-sonnet-high`, seat 1, worktree `.worktrees/wp3.18`, branch `wp3.18`, base main
`718324b`. Tier STRONG. Brief `docs/briefs/wp3.18-brief.md` (FINAL; CHARC rulings
`53d1d906e47fe2c9`). Dispatcher: orchestrator generation 11.

## Cumulative round ledger

| Round | Depth (dispatcher) | Critical | Major | Minor | In / out of envelope | NEW / REOPENED | Reverts | Fixes: product / test-only | Transport, CLI | Verdict |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 (design table) | (dispatcher fills) | - | - | - | - | - | - | - | - | awaiting the orchestrator's reply |

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
| superseded (method changed while a run is in flight; see Q-A) | stays `running` | `set_statistics(None)` | `handle.cancel()` with `cancel_reason="superseded"`; the new run starts from that job's `on_done`; never the `cancelled` phase |
| parameters changed, phase running | unchanged | unchanged (already provisional) | marks "dirty" implicitly: the done-ok row compares parameters |
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
| `proxy(pts)` | `cache.proxy(key, pts)` | new array each call; `KeyError` when absent |
| `statistics(pts)` | `engine.smoothed_record(pts)`; `KeyError` -> None; unknown engine -> None | `schema_hash` is the engine's own concern; the GUI's `epoch` guard sits above it. Unused by design: `provisional_record(pts)` (WP3.16 measures the D108 provisional preview on its own float proxy; WP3.16 report "Decisions") |
| progress | the engine reports `(done, total, message)` in cumulative frame-stage units, `total` None while unknown | the panel shows the report verbatim; the first `running(0, nb_frames)` is replaced at the first report |
| cancel | `progress.cancelled()` is checked by the engine after every frame | `engine.cancel()` is not needed: the GUI cancels through the job handle |

### R0-8 Questions and gaps, with the recommended answer first

**Q-A (STOP: the brief and WP3.11 disagree on supersession). A parameter change during a recompute.**
Brief task 3: "a newer change supersedes the job in flight (cancelled internally)". On the
real engine that is expensive and wrong in shape: a cancel makes the engine `_unload` (drop ALL
statistics), and the next job then re-measures every stage for every frame from the stored
proxies (the decode is skipped; a JPEG proxy decode per frame is still the cost, about a minute
at 20,000 frames) instead of recomputing only the dependent stages near-first. Three options:
(A) the brief as written; (B) RECOMMENDED: a parameter change NEVER cancels; a run in flight
finishes, and at its done-ok the follow-up `run(latest)` starts if the parameters differ (the
rule the brief already has for a change during the FIRST run, applied to every run), so a burst
of changes costs at most one extra recompute; the only internal cancels left are source change
and method change; (C) an additive seam member `retarget(parameters, focus_pts) -> bool` so the
engine absorbs the change in flight (cost: the stub must implement absorption). B changes no
seam name. The table above and the tests follow B; A is the fallback if you rule it.

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
