# WP3.16 report: application shell and preview

Package `clearwater.gui` (`src/clearwater/gui/`), tests `tests/test_gui_*.py` and
`tests/gui_support.py`. Spec v0.5.4 (G1, G2, G9, G10; D27, D28, D41, D66, D108, D111; 6.6; V7, V8),
architecture FINAL 1.0 (IF-1..IF-3, IF-5, IF-6, IF-8, IF-10; AD-4, AD-9, AD-11, AD-15, AD-18, AD-25 (a)).
Base `4b4da9b`. Nothing under `src/clearwater/interfaces/`, `config/`, `core/`, `io/` or `jobs/`
was changed. Rulings: brief CHARC `53b752a4d7fac4fc`; round-0 ruling (orchestrator gen 7) on
S1-S7. Ledger: `docs/proofs/wp3.16-ledger.md`.

## Contract (`clearwater.gui.contract`; the names the WP3.17-3.20 briefs cite)

Frozen at the round-0 commit `795e57f`, additive only until accept (ruling 2). Exported from
`clearwater.gui`.

| Name | What it is |
|---|---|
| `Area` | `PARAMETERS` (right dock, tabbed in attach order), `TIMELINE` (below the preview, stacked, visible only while a video is open), `JOBS` (bottom dock, tabbed) |
| `ShellContext` | frozen: `window`, `session`, `engines`, `locations`, `presets`, `jobs`, `messages`, `actions` |
| `PanelFactory`, `SettingsDialogFactory` | `Callable[[ShellContext], QWidget]`, `Callable[[ShellContext], QDialog]` |
| `ShellWindow(QMainWindow)` | `preview` (property), `attach(area, factory, *, title) -> QWidget`, `set_settings_dialog(factory)` (opened with `QDialog.open()`, window-modal) |
| `ShellActions` | frozen: `open`, `export` (`ReasonAction`), `settings`, `quit` |
| `ReasonAction(QAction)` | `set_unavailable(reason or None)`, `unavailable_reason()`; export starts with "Export is not available yet." (WP3.19 clears it); the shell adds its own reason (nothing open; a video whose analysis is not complete, with `done/total`) |
| `Session(QObject)` | signals `source_changed(object)`, `parameters_changed(object)`, `settings_changed(object)`, `position_changed(object)` (an int; see deviations), `statistics_changed()`, `backend_changed(str)`, `analysis_changed(object)`; getters `source`, `parameters`, `settings`, `method`, `analysis`, `statistics`, `position`, `backend`, `current_image`; setters `set_parameters` (ValueError for an unknown method), `set_settings`, `set_position(pts_ticks, *, statistics=None)`, `set_analysis`, `set_statistics` |
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
| 1 | Nothing heavy on the interface thread: open/probe/decode on the open and frame workers; `select_backend`, downscale, analyze, render, `to_host`, display conversion on the preview worker; jobs on their own threads. | `test_open_and_frame_decode_run_off_the_interface_thread`, `test_v7_...` (method threads exclude the main thread), `test_preview_reason_goes_to_the_tooltip_when_it_differs` (selection threads) |
| 2 | V7 bound: a 10 ms `QTimer` probe never waits > 100 ms while a ~2 s NumPy render runs and a job reports at a high rate (> 1000 reports). Observed maximum **11-12 ms** (2026-10-21, three runs; informational, not a performance figure). | `test_v7_interface_never_waits_more_than_100_ms`; planted inline render fails it: `test_planted_render_on_the_interface_thread_fails_v7` |
| 3 | Latest wins: three quick parameter changes display only the last; a superseded result is dropped on the main thread by generation. | `test_latest_wins_three_quick_changes_show_only_the_last`; planted no-drop worker: `test_planted_stale_result_displayed_fails` |
| 4 | V8 harness: with the identity stub the preview equals the full-resolution render downscaled by the same rule, exactly (mean 0, max 0 at k = 1, 2, 3, 7, and in the window); the harness takes any method and detects a resolution-dependent one. | `test_v8_harness_with_the_identity_stub_is_exact`, `test_preview_equals_the_export_downscaled_by_the_same_rule`, `test_v8_harness_detects_a_resolution_dependent_method` |
| 5 | 1:1 exact: the grabbed device pixels right of the divider equal the full-resolution render bit for bit; the scaled result shows with "Rendering full resolution" until it arrives. | `test_one_to_one_corrected_pixels_equal_the_full_resolution_render`, `test_one_to_one_shows_the_scaled_result_with_an_indicator_until_full_arrives`; planted k = 2 at 1:1 fails: `test_planted_one_to_one_with_scaled_pixels_fails` |
| 6 | Every G10 path of the round-0 table, refusal versus warning, a refusal keeps the previous source. | `tests/test_gui_open.py` (unknown extension, sidecar, DNG via the reader's `unsupported` kind, `unreadable` kind, other exception, each `VideoProbeError` kind, `refuse`/`exclude` faults, no frame, each `warn` fault, untagged photo and video once); planted refusal-as-warning fails |
| 7 | Start-up and close through the `clearwater.config` API only; nothing written outside the injected `Locations`; no `QSettings`; one `save_settings` at close with `last_parameters`; a newer settings file refused and left untouched (S4). | `tests/test_gui_startup.py`; planted `app_locations()` start-up writes under the sentinel: `test_planted_write_to_the_real_app_data_folder_fails`; AST scan `test_no_gui_module_uses_qsettings_or_resolves_app_data_itself` |
| 8 | AD-9 status bar: every `select_backend` reason verbatim as `Device: <reason>`, `Device: -` before a file, the preview reason in the tool tip when it differs, `CPU: forced` after `force_cpu`; the real selection shows `GPU` on this laptop. | `tests/test_gui_status.py` (7 reasons; `gpu` test ran, not skipped) |
| 9 | AD-15 on a stub analysis job: export disabled with the reason and `3/10`, enabled on completion, back to "needs the clip's analysis" on cancel; a photo needs none. | `test_ad15_stub_analysis_disables_export_with_reason_and_progress`, `test_ad15_photo_needs_no_analysis_and_failed_analysis_says_why` |
| 10 | The contract: a dummy panel in each `Area` gets a `ShellContext`, sees `parameters_changed`, drives `set_parameters`; the settings dialog opens from `actions.settings`. | `tests/test_gui_contract.py` |
| 11 | Dependency rule: no `clearwater.gui` module imports `clearwater.methods`, `cupy`, `cupyx` or touches `.xp`; `clearwater.core`, `.config`, `.jobs`, `.io` load no PySide6. | `tests/test_gui_deps.py` |

GUI tests: 90 passed in about 14 s, headless (`offscreen`). Full-suite figures: see the ledger.

## Decisions and deviations

- `position_changed` is `Signal(object)`, not `(int)`: pts ticks can exceed a C `int` (checked
  with `2**40`). Accepted at the round-0 ruling.
- S1: `default_engines()` uses `stub_era_select_backend`, which asks `clearwater.core` for the
  `"c3"` estimate when the method id is unknown to `core.METHOD_IDS` (the merged stub is
  `"stub"`). WP4.3 removes it. `clearwater.core` is unchanged.
- S2: WP3.6's read error is recognised by its `kind` (`unsupported`, `unreadable`) until it can
  be imported by name (rebase onto WP3.6 or WP4.3); the tests use a stand-in class.
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

- `default_engines()` refuses every photo and every video frame (stubs hold none) until WP4.3.
- `show_proxy` converts the given proxy on the main thread (a 540-line frame; bounded).
- A frame that cannot be decoded at a position leaves the previous frame shown; the statistics
  passed with that `set_position` stay supplied.
- `MessagePresenter.clear("error")` after a good preview clears every error banner, not only the
  preview's.
- Close waits at most 5 s per worker; the threads are daemons, so an uninterruptible render cannot
  hang the exit.

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
