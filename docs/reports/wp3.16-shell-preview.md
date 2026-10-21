# WP3.16 report: application shell and preview

Package `clearwater.gui` (`src/clearwater/gui/`), tests `tests/test_gui_*.py` and
`tests/gui_support.py`. Spec v0.5.4 (G1, G2, G9, G10; D27, D28, D41, D66, D108, D111; 6.6; V7, V8),
architecture FINAL 1.0 (IF-1..IF-3, IF-5, IF-6, IF-8, IF-10; AD-4, AD-9, AD-11, AD-15, AD-18, AD-25 (a)).
Base `4b4da9b`; rebased by the dispatcher onto main after WP3.12 and WP3.6 merged (merge base
`d0f00ee`; the two build commits re-resolved by `uv lock`). Nothing under `src/clearwater/interfaces/`, `config/`, `core/`, `io/` or `jobs/`
was changed. One file outside the owned set was changed under a dispatcher grant (round-1
F1, test only): `tests/test_conftest_guard.py` (WP-T1), whose two `-p no:capture` child
invocations also pass `-p no:pytest-qt`. Rulings: brief CHARC `53b752a4d7fac4fc`; round-0 ruling
(orchestrator gen 7) on S1-S7; round-1 to round-3 rulings (orchestrator gen 8). Ledger:
`docs/proofs/wp3.16-ledger.md`.

## Contract (`clearwater.gui.contract`; the names the WP3.17-3.20 briefs cite)

Frozen at the round-0 commit `795e57f`, additive only until accept (ruling 2). Exported from
`clearwater.gui`. One ADDITION since round 0 (Reviewer B #5): `Session.settings_refusal()`.

| Name | What it is |
|---|---|
| `Area` | `PARAMETERS` (right dock, tabbed in attach order), `TIMELINE` (below the preview, stacked, visible only while a video is open), `JOBS` (bottom dock, tabbed) |
| `ShellContext` | frozen: `window`, `session`, `engines`, `locations`, `presets`, `jobs`, `messages`, `actions` |
| `PanelFactory`, `SettingsDialogFactory` | `Callable[[ShellContext], QWidget]`, `Callable[[ShellContext], QDialog]` |
| `ShellWindow(QMainWindow)` | `preview` (property), `attach(area, factory, *, title) -> QWidget`, `set_settings_dialog(factory)` (opened with `QDialog.open()`, window-modal) |
| `ShellActions` | frozen: `open`, `export` (`ReasonAction`), `settings`, `quit` |
| `ReasonAction(QAction)` | `set_unavailable(reason or None)`, `unavailable_reason()`; export starts with "Export is not available yet." (WP3.19 clears it); the shell adds its own reason (nothing open; a video whose analysis is not complete, with `done/total`) |
| `Session(QObject)` | signals `source_changed(object)`, `parameters_changed(object)`, `settings_changed(object)`, `position_changed(object)` (an int; see deviations), `statistics_changed()`, `backend_changed(str)`, `analysis_changed(object)`; getters `source`, `parameters`, `settings`, `method`, `analysis`, `statistics`, `position`, `backend`, `current_image`, `settings_refusal` (ADDED after round 0: a `Message` when start-up refused the settings file, None when it may be written this session; a panel, WP3.20's dialog above all, must not save the settings while it is not None); setters `set_parameters` (ValueError for an unknown method), `set_settings`, `set_position(pts_ticks, *, statistics=None)`, `set_analysis`, `set_statistics` |
| `AnalysisState`, `AnalysisPhase` | frozen `(phase, done, total, message)`; phases `none`, `running`, `complete`, `cancelled`, `failed` |
| `OpenedSource` | frozen `(path, kind, image, metadata, probe, warnings)`, one per open |
| `Engines`, `SelectBackend` | frozen `(photo_source, video_probe, video_source, video_sink, cache, methods, select_backend)`; `methods` first entry = default |
| `PreviewSurface` | `show(image, statistics=None)`, `show_proxy(proxy, corrected=None)` |
| `JobRunner`, `JobHandle` | `run(job, *, on_done, on_progress=None) -> JobHandle`, `cancel()`, `active()`, `wait(timeout_s)`; handle `cancel()`, `is_running()` |
| `MessagePresenter`, `Message`, `MessageSeverity` | `present(message)`, `clear(severity=None)`; `Message(severity, text, path=None)`; `refusal`/`warning`/`error` |

Rules a panel follows: read and change state only through `Session`; never call `setEnabled` on
`actions.export`; the job callable runs on a worker thread and touches no Qt object; callbacks
arrive on the main thread. `set_position` emits `position_changed` then `statistics_changed`; the
shell decodes the frame and renders it with the statistics passed (S5). The shell resets the
analysis state, statistics, position and backend reason when a source opens.

## Modules

`contract` (above); `engines` (`stub_engines`, `default_engines`, `stub_probe`,
`stub_era_select_backend`); `session` (`ShellSession`); `sources` (routing, open, frame decode);
`imaging` (downscale, statistics proxy, display conversion, V8 harness); `render_worker`
(`LatestWorker`, the render job); `preview` (`PreviewWidget`, `PreviewController`); `jobs`
(`QtJobRunner`); `messages` (G10 texts, `DialogPresenter`, `BannerWidget`); `shell`
(`MainWindow`, `start_up`, `run(engines=None, locations=None) -> int`).

## Claims and evidence

| # | Claim | Evidence |
|---|---|---|
| 1 | Nothing heavy on the interface thread: open/probe/decode on the open and frame workers; `select_backend`, downscale, analyze, render, `to_host`, display conversion of rendered results on the preview worker; jobs on their own threads. Exception: `preview.show_proxy` (WP3.18's scrubber) makes its one or two owned `QImage` copies and any ICC conversion of the given 540-line proxy on the interface thread (Reviewer B #9; no V7 claim either way for it). | `test_open_and_frame_decode_run_off_the_interface_thread`, `test_v7_...` (method threads exclude the main thread), `test_preview_reason_goes_to_the_tooltip_when_it_differs` (selection threads) |
| 2 | V7 bound: a 10 ms `QTimer` probe never waits > 100 ms while a ~2 s NumPy render runs and a job reports at a high rate (> 1000 reports). Observed maximum **11-12 ms** (2026-10-21, three runs; informational, not a performance figure). | `test_v7_interface_never_waits_more_than_100_ms`; planted inline render fails it: `test_planted_render_on_the_interface_thread_fails_v7` |
| 3 | Latest wins: three quick parameter changes display only the last; a superseded result is dropped on the main thread by generation. | `test_latest_wins_three_quick_changes_show_only_the_last`; planted no-drop worker: `test_planted_stale_result_displayed_fails` |
| 4 | V8 harness: with the identity stub the preview equals the full-resolution render downscaled by the same rule, exactly (mean 0, max 0 at k = 1, 2, 3, 7, and in the window); the harness takes any method and detects a resolution-dependent one. | `test_v8_harness_with_the_identity_stub_is_exact`, `test_preview_equals_the_export_downscaled_by_the_same_rule`, `test_v8_harness_detects_a_resolution_dependent_method` |
| 5 | 1:1 exact: the grabbed device pixels right of the divider equal the full-resolution render bit for bit; the scaled result shows with "Rendering full resolution" until it arrives (cleared when a k > 1 view supersedes it); the full resolution is rendered once per parameter state: a corrected display image is memoised per image, factor, method, parameters, preview device and supplied statistics (at most one full resolution), so a return to 1:1 or to fit shows it without `render`, also after a render the user superseded while it ran (it is memoised before the job's supersession check). | `test_one_to_one_corrected_pixels_equal_the_full_resolution_render`, `test_one_to_one_shows_the_scaled_result_with_an_indicator_until_full_arrives`, `test_leaving_one_to_one_before_the_full_render_clears_the_indicator`, `test_full_resolution_is_rendered_once_per_parameter_state`, `test_a_full_render_superseded_while_it_runs_is_not_rendered_again`, `test_show_proxy_clears_the_full_resolution_indicator`; at `devicePixelRatio` 2 (a child process with `QT_SCALE_FACTOR=2`, round-4 R4-3): `test_one_to_one_is_exact_in_device_pixels_at_device_pixel_ratio_two`, planted widget ignoring the ratio fails: `test_planted_one_to_one_ignoring_the_device_pixel_ratio_fails`; planted k = 2 at 1:1 fails: `test_planted_one_to_one_with_scaled_pixels_fails`; planted no-memo fails: `test_planted_preview_without_the_render_memo_fails` |
| 6 | Every G10 path of the round-0 table, refusal versus warning, a refusal keeps the previous source. | `tests/test_gui_open.py` (unknown extension, sidecar, DNG via WP3.6's `PhotoReadError` `unsupported`, `PhotoReadError` `unreadable`, a truncated JPEG through the real `PhotoReader` (X-B2), a look-alike exception with a `kind` shown as unreadable, other exception, an exception escaping the open task refused naming the file (R4-1), each `VideoProbeError` kind, `refuse`/`exclude` faults, no frame, each `warn` fault, untagged photo and video once); planted refusal-as-warning fails |
| 7 | Start-up and close through the `clearwater.config` API only; nothing written outside the injected `Locations`; no `QSettings`; one `save_settings` at close with `last_parameters`; a settings file whose format version this Clearwater does not read (newer, or older with no migration step) refused with neutral text and left untouched (S4, R4-2). | `tests/test_gui_startup.py`; planted `app_locations()` start-up writes under the sentinel: `test_planted_write_to_the_real_app_data_folder_fails`; AST scan `test_no_gui_module_uses_qsettings_or_resolves_app_data_itself` |
| 8 | AD-9 status bar: every `select_backend` reason verbatim as `Device: <reason>`, `Device: -` before a file, the preview reason in the tool tip when it differs, `CPU: forced` after `force_cpu`; the real selection shows `GPU` on this laptop. | `tests/test_gui_status.py` (7 reasons; `gpu` test ran, not skipped) |
| 9 | AD-15 on a stub analysis job: export disabled with the reason and `3/10`, enabled on completion, back to "needs the clip's analysis" on cancel; a photo needs none. | `test_ad15_stub_analysis_disables_export_with_reason_and_progress`, `test_ad15_photo_needs_no_analysis_and_failed_analysis_says_why` |
| 10 | The contract: a dummy panel in each `Area` gets a `ShellContext`, sees `parameters_changed`, drives `set_parameters`; the settings dialog opens from `actions.settings`. | `tests/test_gui_contract.py` |
| 11 | Dependency rule: no `clearwater.gui` module imports `clearwater.methods`, `cupy`, `cupyx` or touches `.xp`; `clearwater.core`, `.config`, `.jobs`, `.io` load no PySide6. | `tests/test_gui_deps.py` |

GUI tests on the final head: 119 passed in about 32 s, headless (`offscreen`; the planted
unbounded `view_factor` waits out its 10 s child-process timeout); with
`tests/test_conftest_guard.py` 163 passed; WP3.6's `tests/test_io_photo_*.py` 433 passed. Full suite at `0e4412c` (before round 1): 1 failed, 2993 passed, 1 skipped (normal);
1 failed, 2474 passed, 520 skipped (CuPy unimportable); the failure was Reviewer A F1, fixed in
`fa99105`. Full suite on the final head: run by the orchestrator on the candidate.

## Decisions and deviations

- `position_changed` is `Signal(object)`, not `(int)`: pts ticks can exceed a C `int` (checked
  with `2**40`). Accepted at the round-0 ruling.
- S1: `default_engines()` uses `stub_era_select_backend`, which asks `clearwater.core` for the
  `"c3"` estimate when the method id is unknown to `core.METHOD_IDS` (the merged stub is
  `"stub"`). WP4.3 removes it. `clearwater.core` is unchanged.
- S2 (closed at the rebase onto WP3.6): `messages.photo_read_failure` catches
  `clearwater.io.photo.PhotoReadError` by name and shows its message (G10 wording unchanged); the
  stub-era recognition by `kind` and its `PHOTO_READ_ERROR_KINDS` constant are removed, and the
  tests use the real class.
- S3 (RULED, CHARC `d06ed7c969d6249f`, 2026-10-21): `imaging.downscale(pixels, k)` is a block mean with output
  `ceil(H/k) x ceil(W/k)`, edge blocks averaging only the pixels they cover; the statistics proxy
  uses `imaging.statistics_factor` = `max(1, min(H, W) // 540)`: 4K 960x540, 5.3K 1063x598, 12 MP
  807x605, 48 MP 734x550. One function, one owner: WP3.14 and WP4.1 cite it and V8's area
  average uses it.
- Job progress (after the round-0 freeze; the contract docstring of `JobRunner.run` was
  clarified, no name changed): reports reach the main thread by a 50 ms main-thread poll, not one
  queued event per delivery, so the interface thread's work is bounded at 20 deliveries per
  second per job whatever the report rate. This is a design choice, NOT what makes V7 pass:
  measured 2026-10-21, both runners give 11-12 ms worst gaps with the V7 stub job, and both give
  55-62 ms with a job that spins in pure Python (the `fda06b7` subject's "(V7)" overstates it).
- The V7 stub job calls `time.sleep(0)` after each report (it releases the GIL as a real job's
  NumPy or FFmpeg work does). A job spinning in pure Python starves every Python thread (55-87 ms
  gaps with the preview render running too; up to 796 ms when it yields only every 50 or 200
  reports); that is outside the envelope with the GIL-holding method (brief), to be re-measured
  at WP4.3 with the real engines.
- Preview statistics for the D108 provisional video frame are measured on the in-memory float
  statistics proxy of the frame, not on the stored JPEG proxy (AD-5's ruling governs WP3.18's
  analysis, not this provisional preview).

## Limits

- A photo whose damaged EXIF block WP3.6's reader drops opens with no G10 warning: the reader
  only logs it, so the shell has no signal (Reviewer B #4, banked by the orchestrator as DR-43;
  a reader-side signal is needed, outside this package's files).
- `default_engines()` refuses every photo and every video frame (stubs hold none) until WP4.3.
  WP3.6's `PhotoReader` is merged but not wired there: the post-round-4 cleanup was scoped to the
  by-name catch only; WP4.3 wires the real engines.
- `show_proxy` converts the given proxy on the main thread (a 540-line frame; bounded).
- A frame that cannot be decoded at a position leaves the previous frame shown; the statistics
  passed with that `set_position` stay supplied.
- `MessagePresenter.clear("error")` after a good preview clears every error banner, not only the
  preview's.
- Close waits at most 5 s per worker; the threads are daemons, so an uninterruptible render cannot
  hang the exit.
- A user running `pytest -p no:capture` must also pass `-p no:pytest-qt`: pytest-qt 4.5.0's
  `pytest_configure` raises `ValueError: no option named 'capture'` without the capture plugin.
- A refusal whose text does not contain the file name is shown as `"<name>: <text>"`.
- Photo statistics measured by the preview are not exposed by the contract (round-3 R3-1,
  banked): `Session.statistics()` returns only supplied statistics. See the consumer note.
- `imaging.view_factor` is at most `max(H, W)`: a displayed size of one device pixel or less on
  both axes is covered by every factor, and the 1 x 1 image is shown.
- The supplied-statistics render memo is keyed by the session's statistics revision (every
  `set_statistics`, `set_position(..., statistics=)`, open and `preview.show` bumps it), so a
  mapping changed in place and set again renders again.
- A frame-decode error banner clears at the next decoded frame; as with the preview's, the
  clear removes every `error` banner.
- A preview render that fails after the backend selections still updates the status bar (AD-9);
  a selection that itself raises does not (the real `select_backend` never raises).

## Review and terminating cleanup

Reviewer A (STRONG, at the cell's seat): round 1 2 major (F1, F2) and 4 minor; round 2 1 major
(R2-2) and 4 minor; round 3 1 major (R3-2) and 3 minor; round 4 `NO_NEW_CRITICAL_MAJOR` with 3
minor (R4-1..R4-3), so the loop terminated at round 4. The terminating cleanup (no further
Reviewer A round; Reviewer B at the orchestrator's seat covers it): R4-1 the open task catches
an escaping exception and refuses naming the file (`shell._open_task`); R4-2 the start-up text
for a refused settings format version is neutral (`shell.SETTINGS_FORMAT_TEXT`, was
`NEWER_SETTINGS_TEXT`), the error it carries says "newer" when it is; R4-3 the 1:1 exactness
test at `devicePixelRatio` 2. Each new test failed on the code before its fix (R4-3: the planted
ratio-ignoring widget passes at ratio 1 and fails at 2).

## Reviewer B remediation (orchestrator's seat, candidate `wp3.16-mc`)

Reviewer B returned `NEW_CRITICAL_MAJOR_FOUND`; one remediation, each fix with a test that failed
on the code before it:

- #1 (MAJOR) a refusal at routing invalidates the open in flight, so the earlier file is never
  shown: `test_a_routed_refusal_invalidates_the_open_in_flight`.
- #2 (MAJOR) shutdown stops every worker even when one overruns its timeout:
  `test_shutdown_stops_every_worker_when_one_overruns_its_timeout`.
- #3 (MINOR) close DELIVERS the ended jobs' `on_done` before the settings write
  (`QtJobRunner.close`; the queued duplicate is ignored; `shutdown()` documents the order):
  `test_a_cancelled_jobs_completion_is_delivered_before_the_settings_write`.
- #5 (MAJOR) `Session.settings_refusal()` added to the contract (additive):
  `test_the_session_says_whether_settings_may_be_written` (version-99 start-up).
- #6 (MAJOR) the statistics memo key carries the backend device and reason, so a `force_cpu`
  change measures again: `test_a_force_cpu_change_measures_the_statistics_again`.
- #7 (MINOR) a new source replaces the preview memo:
  `test_a_new_source_drops_the_previous_sources_memo`.
- #8 (MINOR) the settings refusal names the file and its path through `messages.refusal`
  (same test as #5).
- #9 (ADVISORY) the claim about the display conversion corrected (claim 1).
- #4 banked as DR-43 (Limits).

## Consumer note for WP3.14 and WP4.1 (photo statistics, question 5)

When the session holds no supplied statistics (a photo; a video frame before WP3.18 supplies
smoothed ones), the preview measures them with
`clearwater.gui.imaging.measure_statistics(method, backend, image, params)`, which downscales
the full-resolution image by `clearwater.gui.imaging.downscale(pixels,
clearwater.gui.imaging.statistics_factor(H, W))` and runs each stage of `method.stages` in
order with the earlier results. The values are kept private to the preview (round-3 R3-1,
banked; the contract is frozen). An export re-measures with the same call on the same image
and parameters and gets identical values on the same backend (within AD-11 between CPU and
GPU), so V8's preview-against-export agreement holds.

## Dependencies (X-B3)

Mine: `"pyside6-essentials>=6.12,<7",` in `[project] dependencies` (CHARC `d06ed7c969d6249f`,
AD-18 amended on main `d971ee7`: Essentials replaces the `pyside6` meta-package) and
`"pytest-qt>=4.5,<5",` in the `dev` group, each with a grant comment; `uv.lock` regenerated by
`uv lock` (pyside6-essentials 6.12.0, shiboken6 6.12.0, pytest-qt 4.5.0; the meta-package's
Addons, PDF and WebEngine wheels removed). The shell uses QtCore, QtGui, QtWidgets and the tests
QtTest, all in Essentials. Note for any venv that had the meta-package: `uv sync` uninstalling
it removed files Essentials shares (`ImportError: DLL load failed while importing QtCore`);
`uv sync --reinstall-package pyside6-essentials --reinstall-package shiboken6` repaired it. The
dispatcher re-locks at the second of the WP3.6/WP3.12/WP3.16 merges.

## Debt

DR-37 (a) stays OPEN (the status bar shows the string WP3.1 gives). DR-37 (b), DR-34, DR-35 not
reopened. G12 force CPU surfaced (status bar), its toggle is WP3.20's. AD-11 V8 bound: harness
built, the bound is met with WP3.4's method at WP4.x.

## Erratum at the gate (orchestrator, Reviewer B pass 2)

- **Close ordering:** `QtJobRunner.close` delivers `on_done` for the jobs it finds ended when it
  samples them, once. A job that ends while another job's `on_done` runs is delivered later through
  the queue (after the settings write). A job still running when `close()` times out keeps its
  callbacks. Banked as DR-44 (c); trigger WP4.3.
- **Refusal names:** the stand-alone-name check accepts a following dot, so `a.mp4` inside
  `a.mp4.bak` counts as naming the file.
- **Limits, added:** `set_position` commits the position and supplied statistics before the decode
  succeeds (DR-44 (a), for WP3.18). Clearing a message clears every message of its severity,
  whichever panel raised it (DR-44 (b), before the WP3.17-3.20 briefs freeze). Both are stated in
  the Limits above in part; DR-44 is their record.
