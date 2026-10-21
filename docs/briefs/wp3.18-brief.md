# WP3.18 — Timeline and analysis (dispatch brief, FINAL)

**Status:** DRAFT 2026-10-21 for CHARC (orchestrator generation 9, wave 3 tranche B; drafted
against main `9364f8f` plus the DR-44 pre-dispatch contract members); base = the pre-dispatch
main commit named at dispatch. Owner decisions: none inside the package (V2 visual review is
the owner's at WP5.x).
- Spec **v0.5.4** (approved by the owner 2026-10-20). Architecture FINAL 1.0 section 2 (the
  "video preview" line of the data-flow block: "cache.proxy(pts) + StatisticsStore.smoothed(pts)
  -> method.render -> gui (provisional first, D108, AD-15)"), section 3 IF-3, IF-4, IF-5, IF-7,
  IF-8, section 5 (the Analysis (WP3.11) bullet); AD-5, AD-6, AD-7, AD-15, AD-20. Frame
  `docs/briefs/wp2.4-phase3-frame.md` sections 1, 2, 4, 5. WP3.16 report
  `docs/reports/wp3.16-shell-preview.md` "Contract", "Decisions and deviations", "Limits";
  WP3.12 report `docs/reports/wp3.12-proxy-cache.md` "Public API" and "Differences between the
  stub and the product (WP3.11 consumer notes)".
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.18`, branch `wp3.18`, base = the main commit named at dispatch.

**Why.** Plan Phase 3: "WP3.16 owns the main window and defines the places where the other
packages attach their widgets. Each other package owns only its own widget modules. All are
built against stubs of the engines." This package starts the analysis when a clip opens (G5),
drives AD-15's states, gives the scrubber (G4, D72), and switches the preview from provisional
to smoothed statistics (D108, V18). It is the consumer DR-44 (a) was banked for.

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
| ID and title | WP3.18 — Timeline and analysis; plan section 6 Phase 3 row WP3.18 (size M, depends on WP3.16, spec "G4, G5; D70, D72, D108", feeds V7, V18); module `clearwater.gui` |
| Goal | A timeline panel for an open video: analysis started on open in the background with progress and cancel, the AD-15 states set on the session, a scrubber that shows stored proxies while dragging and the full-resolution corrected frame when stopped, and the switch from the provisional to the smoothed preview, each frame paired with its own statistics. |
| Spec / decision clauses | Plan bullet "**WP3.18:** the scrubber showing proxy frames while dragging and the full-resolution frame when stopped; analysis progress and cancel; the switch from provisional to smoothed preview." G4 "Video: timeline scrubber. While dragging, proxy frames are shown; when stopped, the full-resolution corrected frame is shown (D72). Preview uses temporally smoothed statistics once analysis has produced them, and the provisional preview before that (D108)." G5 "Analysis runs in the background on clip open, shows progress and can be cancelled." D70 "Analysis pass has a cancel control"; D72 "Timeline scrubbing shows proxy frames while dragging, full-resolution corrected frame when stopped"; D108 "Provisional preview: on clip open the current frame is shown at once using its own unsmoothed statistics while analysis runs in the background"; D42 "Video preview uses temporally smoothed statistics once analysis has produced them, and a provisional per-frame preview before that; analysis runs on clip open". Spec 7.2 item 1 "Runs in the background when a clip is opened, shows progress, and can be cancelled (cancel returns to an unloaded state)." AD-15 "scrubbing shows the provisional preview (the frame's own unsmoothed statistics, D108), parameter changes apply to the provisional preview at once and restart the dependent stages when analysis completes" and "(button disabled with the reason and the progress). Cancel returns to the unloaded state."; AD-7 "a parameter change re-measures from the first stage it invalidates, first for the frames within the displayed frame's smoothing reach (±29 frames at 2.0 s, 29.97 fps), then the rest of the clip in the background" and "Export waits for the whole clip's recompute."; AD-6 "Statistics are keyed by pts, never by index." Feeds V18 "on opening a clip, a corrected frame is shown before analysis completes, and it updates to the smoothed statistics afterwards." and V7 "UI responds within 100 ms during analysis, export and batch processing (D66)." |
| Depends on | WP3.16 merged (accept `a2685cb`): `clearwater.gui.contract` as frozen plus the DR-44 pre-dispatch members (`FrameOutcome(requested, pts, error)`, `Session.frame_decoded`, `Message.owner`, `MessagePresenter.clear(..., owner=)`; sha named at dispatch). WP3.12 merged (accept `3aaf395`): `clearwater.cache.cache_key(path, codec=DEFAULT_CODEC)`, `DiskProxyCache` (used only through IF-7 here). WP2.2: `stubs.StubVideoSource`, `stubs.StubProxyCache`, `stubs.StubStatisticsStore`, `stubs.StubCorrectionMethod`, `stubs.C3_STAGES`. UNMERGED, behind the seam of task 2: WP3.11 (the analysis engine, tranche A; question 1) and WP3.9 (decode; the shell decodes through `Engines.video_source`). |
| Files owned | NEW: `src/clearwater/gui/timeline.py`, `src/clearwater/gui/analysis_service.py`, `tests/test_gui_timeline.py`, `tests/test_gui_analysis_service.py`, `docs/reports/wp3.18-timeline-analysis.md`, `docs/proofs/wp3.18-ledger.md`. NOT owned: every existing file under `src/clearwater/gui/` (WP3.16's, including `contract.py`, `__init__.py`, `preview.py`, `session.py`), `tests/gui_support.py` (imported read-only), WP3.16's tests, the WP3.17/3.19/3.20 files of the map, `src/clearwater/interfaces/`, `src/clearwater/cache/`, the future `clearwater.analysis` (WP3.11), `pyproject.toml`, `uv.lock`, `tests/conftest.py`. |
| Interfaces provided | No frozen interface. The analysis seam of task 2 (`ClipAnalysis` protocol, `AnalysisFactory`, `stub_analysis_factory`), frozen at this package's round-0 yield and additive only until accept (question 2); `install_timeline(window: ShellWindow, analysis: AnalysisFactory | None = None) -> None` (WP4.3 calls it with the adapter over WP3.11) and the `PanelFactory` it attaches. |
| Interfaces consumed | Contract: `ShellContext` (`session`, `engines`, `jobs`, `messages`, `window`), `Session` (`source`, `parameters`, `method`, `settings`, `analysis`, `position`, `set_position(pts_ticks, *, statistics=None)`, `set_statistics`, `set_analysis`, signals `source_changed`, `parameters_changed`, `frame_decoded`), `AnalysisState`/`AnalysisPhase`, `FrameOutcome`, `OpenedSource` (`kind`, `probe`, `image`: a `Frame` for a video), `PreviewSurface.show_proxy(proxy, corrected=None)`, `JobRunner.run(job, *, on_done, on_progress)`, `JobHandle.cancel`, `Area.TIMELINE`. IF-1 `Frame` (`pts_ticks`), IF-3 `CorrectionMethod`/`Stage`, IF-4 `StatisticsStore` (the stub), IF-5 `ProbeResult` (`video.nb_frames`, `video.time_base`), IF-7 `ProxyCache`/`CacheKey`, IF-8 `Progress`, `JobResult`, IF-9 `ParameterSet`. |
| Hardware flags | `gui` on every test that creates a Qt object; no `gpu`, no `footage`. No timing FIGURE: V7's 100 ms is asserted as a bound (task 6); the observed maximum is informational. |
| Out of scope | The analysis engine itself: the decode pass, proxies, staged statistics, smoothing, the step-aware variant, the AD-7 recompute scheme, V17's cache skip (WP3.11; here only the seam and a stub); frame decoding and the preview render (WP3.16's shell); a corrected scrub proxy (question 4); export (WP3.19); the settings dialog and clear-cache (WP3.20); wiring the real engines (WP4.3); chapter grouping and cross-file smoothing (deferred to v2; V12 deferred); any edit to WP3.16's files. |
| Debt and decided items | DR-44 (a) ("`set_position` commits the position and supplied statistics before the decode succeeds; after a decode error a later render pairs the shown frame with the new pts's statistics ..., and a pts between frames shows the next frame while `position()` keeps the request"; trigger "WP3.18's brief (request exact frame pts; an additive decode-completion signal)") -- ADDRESSES (a)'s consumer side -- requests only pts from `ClipAnalysis.pts()`; on every `frame_decoded` pairs the statistics with `FrameOutcome.pts` (re-supplies them when it differs from `requested`, restores the last shown frame's after a failure); a test per path. DR-44 (b) -- ADDRESSES (b) for this package -- owners `"timeline"`, `"analysis"` on every present and clear. DR-44 (c) -- not this package's (WP4.3). DR-23 ("statistics are keyed by pts and smoothing windows are defined in seconds over pts") -- must not reopen -- no index is ever a key here; a VFR stub clip test. AD-15 -- IMPLEMENTS the GUI side (states set through `Session.set_analysis`; the shell disables export from them). AD-5 (the analysis measures on the stored proxy) and DR-25 -- not this package's (WP3.11); the stub does not claim AD-5 fidelity. D98 (a single-stage method) -- must work: a one-stage test method. DR-43 -- not this package's. V12 -- deferred to v2. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green (in a dispatcher window) with the GUI tests headless; V18's GUI leg, D72, G5, AD-15 and DR-44 (a) shown by named tests; V7's bound asserted; the seam documented in the report; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: read and table.** Before product code, write in the ledger: the seam of
   task 2 as signatures with docstrings (COMMIT `analysis_service.py`'s protocol at this
   yield, question 2); the state machine (events: video opened, progress, done ok, done
   failed, user cancel, superseded, parameters changed while running / while complete, source
   changed) -> `AnalysisState` set and statistics supplied; the threading table (which seam
   call runs on which thread); the scrub sequence (press, drag, release, keyboard step,
   `frame_decoded`); the test list; the answers to the open questions; whether WP3.11 has
   merged and, if so, the mapping from each seam member to WP3.11's names (question 1); the
   `scripts/cell_depth.py` reading. YIELD for the dispatcher. A choice the brief leaves open
   is a STOP.
2. **The analysis seam (`analysis_service.py`).** As drafted (the round-0 table fixes names):
   - `ClipAnalysis` (protocol), one per opened clip: `run(parameters, progress, *, focus_pts=None)
     -> None` (brings the smoothed statistics up to date for `parameters`: the full pass on the
     first call, the dependent stages after a parameter change, `focus_pts`'s smoothing reach
     first (AD-7); returns early when `progress.cancelled()`; raises on failure);
     `pts() -> tuple[int, ...]` (the pts ticks with a stored proxy so far, ascending; cheap and
     non-blocking, callable on the main thread); `proxy(pts_ticks) -> NDArray[np.uint8]`;
     `statistics(pts_ticks) -> Mapping[str, Statistics] | None` (smoothed, every stage, for
     the parameters of the latest completed `run`, or None when not available). `run`,
     `proxy` and `statistics` are called only on worker threads, and `proxy`/`statistics` may
     run while `run` does (AD-15: scrubbing during analysis).
   - `AnalysisFactory = Callable[[OpenedSource, CorrectionMethod, Engines], ClipAnalysis]`.
   - `stub_analysis_factory`: a `ClipAnalysis` over `engines.video_source.frames(probe,
     hw_decode=False)`; per frame a proxy by `imaging.downscale(pixels,
     imaging.statistics_factor(H, W))` quantised to uint8 and stored in
     `engines.cache.store_proxy(cache_key(source.path), ...)` (`cache_key` stats the file, so
     tests create the clip path as a small file under `tmp_path`; `stubs.StubProxyCache`),
     statistics by `method.analyze` stage by stage on that proxy into a
     `stubs.StubStatisticsStore` keyed by `pts_ticks`, `smooth` the stub's copy; reports
     `progress.report(done, probe.video.nb_frames, ...)`; honours cancel per frame. It claims
     no AD-5/AD-3 fidelity (WP3.11's), only the seam's contract.
3. **Analysis driving and AD-15 (`timeline.py`).**
   - On `source_changed` to a video: cancel this package's jobs of the previous source; build
     the `ClipAnalysis`; start `run(session.parameters(), ...)` through `context.jobs`;
     `set_analysis(AnalysisState("running", 0, nb_frames))`; each `on_progress` sets the
     running state with done/total/message. Every callback carries the source generation it
     was started for and is ignored when the source has changed since.
   - Done ok: if `session.parameters()` differs from the run's, start a follow-up `run` with
     the latest (AD-15 "restart the dependent stages when analysis completes"; the phase stays
     running); else `set_analysis(AnalysisState("complete"))` and the switch of task 5.
   - Failure: `set_analysis(AnalysisState("failed", message=...))` and an error with owner
     `"analysis"`; the provisional preview stays.
   - User cancel (D70): `handle.cancel()`; on its `on_done`, `AnalysisState("cancelled")` and
     `session.set_statistics(None)` (question 3 reads "unloaded"); an "Analyse" button
     restarts.
   - Parameters changed while running: no restart (the preview is already provisional); while
     complete: `set_statistics(None)` at once (the shown frame goes provisional, AD-15) and a
     `run(params, focus_pts=shown pts)` with the phase running and the message "Updating
     statistics"; a newer change supersedes the job in flight (cancelled internally: never the
     "cancelled" phase).
   - Source changed to a photo or closed: cancel; the shell resets the state.
4. **The scrubber (G4, D72).** A slider over the indices of `ClipAnalysis.pts()` (refreshed on
   progress; disabled until a proxy exists), a time label from `pts_ticks *
   probe.video.time_base`, the progress bar with Cancel and Analyse.
   - While the slider is down: each value submits a latest-wins job reading `proxy(pts)`; its
     `on_done` calls `window.preview.show_proxy(proxy)` unless superseded (question 4).
     `set_position` is never called while dragging.
   - On release, or a value change not by dragging (keys, clicks): a job reading
     `statistics(pts)` when the phase is complete (None otherwise: AD-15 provisional), then
     `session.set_position(pts, statistics=...)`; remember the request.
5. **Pairing frames and statistics (DR-44 (a), V18).** On `frame_decoded(outcome)` for the
   latest request: `outcome.pts == outcome.requested` -> nothing more; a different `pts` ->
   fetch `statistics(outcome.pts)` (complete phase) and `set_statistics` them; `pts is None`
   (decode failed; the shell shows the error, owner `"shell.frame"`) -> re-supply the
   statistics of the last shown pts with `set_statistics` and move the slider back to it under
   `QSignalBlocker`. The switch to smoothed on completion is `set_position(shown_pts,
   statistics=statistics(shown_pts))`, where `shown_pts` is the last `FrameOutcome.pts`, else
   the open frame's `source.image.pts_ticks`.
6. **Tests** (headless, `gui`-marked, through `tests/gui_support` helpers and stub engines
   with several frames; a test method whose `render` output depends on the supplied
   statistics):
   - V18 leg: open a clip whose stub analysis blocks on an event; a corrected frame is shown
     (provisional) before completion; after release the preview updates to the smoothed
     statistics;
   - G5/D70: progress reaches the session as running done/total; cancel gives "cancelled" and
     the export reason the shell derives from it; Analyse restarts;
   - D72: while dragging, `show_proxy` is called with the stored proxy and `set_position` is
     not; on release `set_position` with the exact pts from `pts()`;
   - DR-44 (a): a stub source whose frame pts differs from the request -> statistics of the
     shown pts; a decode failure -> the last shown frame's statistics restored, slider back;
   - AD-15: a parameter change during the run applies provisionally and triggers one
     follow-up run before "complete"; after completion a change goes provisional, then smoothed
     again; export stays unavailable until then;
   - stale work: a source change mid-analysis -> no state or statistics from the old job;
   - pts keys: a VFR stub clip (irregular pts) scrubs to exact pts (DR-23); a one-stage method
     works (D98);
   - V7 bound: during a CPU-heavy stub analysis (NumPy, about 2 s, releasing the GIL) and a
     scrub drag, a `QTimer` probe on the main thread never waits more than 100 ms (D66);
   - planted wrong implementations fail by name: no switch after completion; statistics of
     the requested pts kept after a failed decode; the analysis run on the main thread;
     `set_position` during a drag;
   - dependency rule: WP3.16's `tests/test_gui_deps.py` covers the new modules (run it, do
     not change it); no import of `clearwater.methods`.

## Declared operating envelope

Windows 11; Python 3.12; PySide6-Essentials and pytest-qt as locked; one Clearwater window;
one open clip at a time; clips of a few minutes (D117), constant or variable frame rate (D95),
up to about 20,000 frames in the scrubber; the stub analysis and stub frames in tests
(headless, `offscreen`). Out of envelope: the real WP3.11 engine's speed and fidelity (WP4.2,
WP4.3); a method that holds the GIL in pure Python (WP4.3 re-measures V7); several windows;
other operating systems (portable, N1, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.18\rN\`; ledger `docs/proofs/wp3.18-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r4\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - every frame shown with its own pts's statistics after every path (DR-44 (a)); never an
    index as a key;
  - the AD-15 state machine: every event, stale callbacks after a source change, a superseded
    run never reported as the user's cancel, export never enabled before the final
    completion;
  - nothing heavy on the interface thread (`run`, `proxy`, `statistics` on workers); no Qt
    object touched from a job;
  - the seam's thread rules documented and honoured by the stub;
  - message owners (DR-44 (b)); nothing in WP3.16's files or `interfaces/` changed.
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
- **Known shell behaviour you build on** (WP3.16 report): `set_position` emits
  `position_changed` then `statistics_changed`; the shell resets the analysis state,
  statistics, position and backend reason when a source opens; `show_proxy` converts on the
  interface thread (bounded, a 540-line frame); the provisional statistics are measured by the
  preview on its own float proxy of the frame.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the module list, the seam (every name), the state machine, the threading table,
  the scrub sequence, the V7 bound and observed maximum, the gates, the Reviewer A rounds and
  verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or in
  `clearwater.gui.contract`; a change to any existing file; a dependency; WP3.11's merged API
  unable to serve a seam member (question 1); any OS-specific code; a test that cannot run
  headless; the round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with
  `git -c core.autocrlf=false commit -m "feat(wp3.18): ..." -- <paths>`, with a
  `Co-Authored-By:` footer naming your model; never `git stash` (use a WIP commit or a scratch
  copy). Never a bare `cd`. Never post to a mailbox. Gates: ruff check, ruff format --check,
  mypy strict, full pytest (in a window); no harness gate. Report
  `docs/reports/wp3.18-timeline-analysis.md` (claims, evidence paths, limits, and a "Seam for
  WP4.3" section mapping each seam member to what WP3.11 must supply). The footage folder is not
  used. GoPro data is out of scope: no `gpmd`, IMU or GPS data.

## Rulings (CHARC `53d1d906e47fe2c9`, 2026-10-21)

Approved as drafted: every recommended answer below is the ruling, with these amendments and readings. Where a ruling here and the task ladder or a question differ, the ruling governs.

- **The `ClipAnalysis` seam** is frozen at round 0, additive only until accept (like `gui.contract`).
- **DR-44 members** as landed on main (the pre-dispatch commit).

## Questions for CHARC (recommended answer first)

1. **Where the analysis engine comes from.** `Engines` (frozen) has no analysis member and
   WP3.11 is in tranche A. Recommended: this package defines the GUI-side seam of task 2 with
   a stub and never imports `clearwater.analysis`; WP4.3 adapts WP3.11's engine to it. If
   WP3.11 has merged by this package's round 0, the round-0 table maps each seam member to
   WP3.11's names so WP4.3's adapter is mechanical, and a member WP3.11 cannot serve is a STOP.
   Alternative: wait for WP3.11 and consume it directly (blocks tranche B on WP3.11's accept).
2. **Freezing the seam.** Recommended: as WP3.16 ruling 2 did for the contract:
   `ClipAnalysis` and `AnalysisFactory` committed at the round-0 yield, additive only until
   accept, a CHARC ruling after; WP3.11's and WP4.3's briefs cite it.
3. **"Cancel returns to an unloaded state" (7.2, AD-15).** Recommended: the clip stays open
   with the provisional preview; the analysis results are dropped (`AnalysisState("cancelled")`,
   `set_statistics(None)`), export stays unavailable, and Analyse restarts (the reading WP3.16
   already implements for "cancelled"). Alternative: cancel closes the clip.
4. **What the "after" side shows while dragging.** `PreviewSurface.show_proxy(proxy,
   corrected=None)` takes an optional corrected proxy. Recommended: `corrected=None` (the
   stored proxy on both sides while the slider is down; the corrected full-resolution frame
   on release, D72; G4 says "While dragging, proxy frames are shown; when stopped, the
   full-resolution corrected frame is shown"); a corrected scrub proxy is a later enhancement if
   V2 asks for it. Alternative: the scrub job also renders the proxy at its own size with
   WP3.16's `imaging.effective_parameters`, `engines.select_backend` and `imaging.render_host`
   (smoothed statistics when complete, else `imaging.measure_statistics` on the proxy) and
   passes `imaging.to_display_uint8` of it as `corrected` (more work per drag step; V7 must
   still hold).
5. **Cross-brief items** (the same in WP3.17-3.20): `clearwater/gui/__init__.py` is not edited
   (X-W3a); read-only use of WP3.16's pure helpers `imaging.downscale` and
   `imaging.statistics_factor` and the test helpers (X-W3b); the capturing test presenter
   already takes `owner` (the DR-44 pre-dispatch commit). Recommended as in
   the WP3.17 brief, questions 1 and 3.
6. **Reviewer tier.** Recommended: STRONG, five-round gate.
