# WP3.16 ledger (application shell and preview)

Cell: implementer-opus-high (tier STRONG; ruling 1). Worktree `.worktrees/wp3.16`, branch
`wp3.16`, base `4b4da9b`. Spec v0.5.4, architecture FINAL 1.0. Brief `docs/briefs/wp3.16-brief.md`
(FINAL, CHARC rulings `53b752a4d7fac4fc`: every recommended answer is the ruling).

## Cumulative round ledger

| Round | Date | Blocking (crit/maj) | Minor | In/out envelope | NEW/REOPENED | Reverts | Fix kind | Transport | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 0 (design) | 2026-10-21 | n/a | n/a | n/a | n/a | n/a | n/a | n/a | 152,774 (dispatcher, 35 turns, 01:27:10Z) |
| 1 | 2026-10-21 | 0/2 (F1 full suite red by pytest-qt; F2 1:1 re-render) | 4 confirmed (F3, F4, F5; F7 out) + 1 rejected (F6) | 6 in / 1 out (F7) | 7 NEW / 0 REOPENED | 0 | planned: product (F2-F5, F7) + a ruled line outside the files owned (F1) | WSL, codex-cli 0.162.1, gpt-5.6-sol high | (dispatcher) |
| 2 | 2026-10-21 | 0/1 (R2-2 `view_factor` hang, reproduced) | 4 (R2-1 proposed down from MAJOR, R2-3, R2-4, R2-5) | 5 in / 0 out | 3 NEW (R2-2, R2-3, R2-5) / 2 REOPENED (R2-1 of F2, R2-4 of F3) | 0 | round-1 fixes: product (F2-F5, F7) + granted test line (F1); planned: product (R2-1..R2-4) + test/report (R2-5) | WSL, codex-cli 0.162.1, gpt-5.6-sol high | (dispatcher) |
| 3 | 2026-10-21 | 0/1 (R3-2 stale memoised render after an in-place statistics update) | 3 (R3-1 proposed down from MAJOR, R3-3, R3-4) | 4 in / 0 out | 2 NEW (R3-1, R3-2 major, in a round-1 fix) / 2 REOPENED (R3-3 of F3, R3-4 of F4) | 0 | round-2 fixes: product (R2-1..R2-4) + test (R2-5); planned: product (R3-2..R3-4) + an additive contract getter (R3-1, to rule) | WSL, codex-cli 0.162.1, gpt-5.6-sol high | (dispatcher) |
| 4 | 2026-10-21 | 0/0 | 3 (R4-1, R4-2, R4-3) | 3 in / 0 out | 2 NEW (R4-2, R4-3) / 1 REOPENED (R4-1 of F4) | 0 | round-3 fixes: product (R3-2..R3-4), R3-1 banked; planned cleanup: product (R4-1, R4-2) + test (R4-3) | WSL, codex-cli 0.162.1, gpt-5.6-sol high | (dispatcher) |

## Round 0: the design table (brief task 1)

Shipped with this yield: `pyproject.toml` (the two granted lines), `uv.lock` (`uv lock`),
`src/clearwater/gui/__init__.py`, `src/clearwater/gui/contract.py` (ruling 2: frozen here,
additive only until accept). No other product code before the ruling.

### 1. Anchors re-grounded at `4b4da9b`

All brief anchors hold except the two STOP items S1 and S2 below. Checked: IF-1..IF-10 as quoted;
`clearwater.config` exports `app_locations`, `Locations` (`config_dir`, `cache_dir`; properties
`presets_dir`, `log_dir`, `settings_file`, `log_file`), `load_settings(folder)`,
`save_settings(folder, settings)`, `configure_logging(folder)`, `shutdown_logging()`,
`PresetStore(folder).install_starters()`, `new_parameter_set`; `clearwater.core.select_backend`
and its seven reason strings (`core/backend.py:552`); `clearwater.io.video` exports `probe`,
`VideoProbeError(kind, message)` with kinds `unreadable`/`unsupported`/`sidecar`/`missing_tool`,
`is_sidecar`, `sidecar_fault`; the stubs of `interfaces/stubs.py` (note: the stub
`select_backend` reason is `"CPU: stub"`, or `"CPU: forced"`). `load_settings` also RAISES
`UnsupportedFormatVersionError` for a newer file (S4).

### 2. Modules

| Module | Job |
|---|---|
| `__init__.py` | Docstring; exports the contract names and `run`. WP3.17-3.20 append only. |
| `contract.py` | The attachment contract (section 3). Types and signatures, no behaviour. |
| `engines.py` | `stub_engines(...)` for tests; `default_engines()` (real `probe`, real `select_backend` per S1, stubs for the rest). |
| `session.py` | `ShellSession(Session)`: the state, setters emit synchronously. |
| `sources.py` | Routing by extension; open a photo or a video into an `OpenedSource` plus G10 messages; decode a frame at a position. Pure, run on a worker. |
| `imaging.py` | Block-mean downscale, view factor, statistics proxy, display conversion (float -> uint8 -> `QImage`, ICC -> sRGB), the V8 difference harness. |
| `render_worker.py` | `LatestWorker`: one worker thread, latest-wins requests with a generation number; the preview render job. |
| `preview.py` | `PreviewWidget`: split view, divider, zoom (fit, steps, 1:1), pan, "rendering full resolution" indicator; implements `PreviewSurface`. |
| `jobs.py` | `QtJobRunner`, `QtProgress`, `QtJobHandle` (IF-8 on worker threads, coalesced reports). |
| `messages.py` | G10 classification (exception or fault -> `Message`); `DialogPresenter` (modal `QMessageBox` + banner widget). |
| `shell.py` | `MainWindow(ShellWindow)`, `ExportAction(ReasonAction)`, start-up and close, menus, status bar, `run(engines=None, locations=None) -> int` (question 12). |

Tests: `tests/gui_support.py` (sets `QT_QPA_PLATFORM` before any PySide6 import; fixtures),
`tests/test_gui_contract.py`, `test_gui_startup.py`, `test_gui_open.py`, `test_gui_preview.py`
(V8, 1:1, latest wins, downscale rule), `test_gui_threads.py` (V7, jobs runner, shutdown),
`test_gui_status.py`, `test_gui_deps.py`.

### 3. The contract (`clearwater.gui.contract`, committed at this yield)

- `Area` (enum): `PARAMETERS` (right dock, tabbed in attach order), `TIMELINE` (below the preview,
  stacked, shown only while a video is open), `JOBS` (bottom dock, tabbed).
- `AnalysisState(phase="none", done=0, total=None, message="")`, frozen; `AnalysisPhase` =
  `"none" | "running" | "complete" | "cancelled" | "failed"` (S6: `failed` added).
- `Message(severity, text, path=None)`, frozen; `MessageSeverity` = `"refusal" | "warning" | "error"`.
- `OpenedSource(path, kind, image, metadata, probe, warnings)`, frozen; one per open, unchanged
  while open (the frame at the position is `Session.current_image()`).
- `Engines(photo_source, video_probe, video_source, video_sink, cache, methods, select_backend)`,
  frozen; `methods` first entry = default; `SelectBackend` alias = IF-2's signature.
- `Session(QObject)`. Signals: `source_changed(object)`, `parameters_changed(object)`,
  `settings_changed(object)`, `position_changed(object)` (an `int`, declared `object` because pts
  ticks can exceed a C `int`; brief said `(int)`), `statistics_changed()`, `backend_changed(str)`,
  `analysis_changed(object)`. Getters: `source()`, `parameters()`, `settings()`, `method()`,
  `analysis()`, plus (added) `statistics()`, `position()`, `backend()`, `current_image()`.
  Setters: `set_parameters(ps)` (ValueError for a method not in `Engines.methods`),
  `set_settings(s)`, `set_position(pts_ticks, *, statistics=None)` (S5), `set_analysis(state)`,
  `set_statistics(stats | None)`. Every setter emits synchronously, also for an equal value.
- `ReasonAction(QAction)`: `set_unavailable(reason | None)`, `unavailable_reason()`. Export is
  enabled only when no reason holds: the shell's (no source; a video whose analysis is not
  complete, with the progress) and the caller's (initially "Export is not available yet";
  WP3.19 clears it).
- `ShellActions(open, export, settings, quit)`, frozen.
- `PreviewSurface` (Protocol): `show(image, statistics=None)` (image becomes the current image),
  `show_proxy(proxy, corrected=None)` (uint8, shown at once, scaled, until the next result).
- `JobHandle` (Protocol): `cancel()`, `is_running()`. `JobRunner` (Protocol):
  `run(job, *, on_done, on_progress=None) -> JobHandle`, `cancel()`, `active()`, `wait(timeout_s)`.
- `MessagePresenter` (Protocol): `present(message)`, `clear(severity=None)`.
- `ShellWindow(QMainWindow)`: property `preview`; `attach(area, factory, *, title) -> QWidget`;
  `set_settings_dialog(factory)` (opened window-modally with `QDialog.open()`, never a blocking
  `exec`). The actions are on `ShellContext.actions`, not on the window (`QWidget.actions()` is
  Qt's own method).
- `ShellContext(window, session, engines, locations, presets, jobs, messages, actions)`, frozen.
- `PanelFactory = Callable[[ShellContext], QWidget]`; `SettingsDialogFactory =
  Callable[[ShellContext], QDialog]`.

Brief task 2 named every one of these; the additions beyond its list are the four `Session`
getters, the keyword `statistics` of `set_position`, `corrected` of `show_proxy`, the `failed`
phase, `Message`/`MessageSeverity`, `JobHandle`, `JobRunner.active`/`wait`, and the type aliases.
No name the brief lists is renamed, except `position_changed`'s declared type (above).

### 4. Threading model

- **Main thread:** every `QObject`/`QWidget`/`QPixmap`, the `Session`, the menus, the dialogs, the
  painting, the status bar. It never calls `read`, `probe`, `frames`, `select_backend`, a
  downscale, `analyze`, `render` or a colour conversion.
- **Loader worker** (one thread, `LatestWorker`): file open (`photo_source.read` or
  `video_probe` + the first frame of `video_source.frames`) and the frame at a position.
- **Preview worker** (one thread, `LatestWorker`): per request `select_backend` twice (full size:
  the status-bar reason, what export uses; preview size: the backend it renders on), the
  downscale, the statistics, `render`, `to_host`, conversion to a display `QImage` (a value class
  Qt documents as usable outside the GUI thread; no `QObject` is touched).
- **Job threads** (one per `JobRunner.run`): the IF-8 jobs of WP3.18/3.19.
- **Latest wins:** each request carries a generation number taken on the main thread; a new
  parameter, settings, source, statistics, position or zoom-factor change bumps it. The worker
  keeps only the newest pending request, checks the generation between stages and abandons a
  superseded one; a result is delivered by a queued signal to a main-thread bridge object and
  DROPPED there when its generation is not current, so a stale result is never shown. An
  exception in a request becomes a message; the last good preview stays.
- **Reports:** a job's `report` stores the latest triple under a lock and posts at most one
  queued delivery; the main thread takes the latest.
- **Close:** cancel all jobs, bump the generations, stop both workers, wait up to 5 s each; the
  threads are daemon threads, and emission from a worker into a deleted bridge is guarded, so a
  render that cannot be interrupted mid-NumPy call does not hang or crash the exit.

### 5. Preview pipeline

- **Photo:** loader reads `(Image, PhotoMetadata)` (host, float32). Preview request: (a)
  statistics: the supplied ones, else measured once per (source, parameter state) on the
  statistics proxy (question 5: block mean to a short side near 540, S3), each stage of
  `method.stages` in order with the earlier results; (b) view factor k (question 7, S3): the
  largest integer k whose block-mean size still covers the displayed size in device pixels
  (`view size x devicePixelRatio`); k = 1 at 1:1 or larger; (c) `asarray` the k-downscaled image
  on the preview backend, `render` with the statistics, `to_host`; (d) display: clip to [0, 1],
  `round(x * 255)` to uint8, `QImage` RGB888, tagged with `QColorSpace.fromIccProfile` when the
  source has an ICC profile and converted to sRGB (question 8; untagged shown as sRGB); the
  "before" side is the same k-downscaled input through the same conversion. Qt scales the last
  step for display only.
- **1:1 (question 6):** k = 1: the whole image is rendered at full resolution once per parameter
  state; until it arrives the screen-resolution result is shown scaled with a "Rendering full
  resolution" indicator; kept while panning. The widget draws it with
  `QImage.setDevicePixelRatio(dpr)` so one image pixel is one device pixel.
- **Video frame:** loader probes, refuses on a `refuse` fault, decodes the first frame
  (`frames(probe, hw_decode=False)`, S7); then as a photo, with the frame's own unsmoothed
  statistics (D108) until WP3.18 supplies smoothed ones. `set_position` decodes the first frame
  at or after the pts on the loader worker (S5).
- **V8 harness:** `imaging.preview_export_difference(method, backend, image, params, statistics,
  k)` -> mean and max absolute difference between `render(downscale(image, k))` and
  `downscale(render(image), k)`; the preview calls the same `downscale`. With the identity stub
  both are 0 exactly; WP4.x re-runs it with WP3.4's method against AD-11.

### 6. G10 message table (question 10)

| Source | Severity | Presentation |
|---|---|---|
| Unknown extension (not a photo or `.mp4` one) | refusal | modal, "<name> is not a supported photo or video file"; previous source kept |
| Sidecar (`is_sidecar`) | refusal | modal, `sidecar_fault(path).message` |
| `VideoProbeError` (any kind, incl. `missing_tool`) | refusal | modal, its message |
| `ProbeResult.faults` with severity `refuse` (HLG, PQ) or `exclude` | refusal | modal, the fault message |
| `ProbeResult.faults` with severity `warn` (truncated, unreadable tail, missing tags, GP-Log) | warning | banner while open, one per fault |
| No frame decodable from a probed video | refusal | modal, "<name>: no frame could be read" |
| WP3.6 read error, kind `unsupported` (incl. DNG/ProRAW, D116) or `unreadable` | refusal | modal, its message (S2) |
| Any other exception from `photo_source.read` | refusal | modal, "<name> could not be read: <text>" |
| `ColorDescription.assumed` (photo) | warning | banner, "<name> has no colour description; sRGB is assumed" |
| `ColorDescription.assumed` (video frame) | warning | banner only when the probe gave no `missing_tags` fault (one warning, not two) |
| Preview job exception | error | banner "Preview failed: ..."; cleared at the next good preview; last good preview stays |
| `load_settings` raising `UnsupportedFormatVersionError` | refusal-style modal at start-up | S4 |

All texts pass through `ascii_text`-style escaping of file names (ASCII-safe console rule).

### 7. Headless set-up (question 3, ruling 3)

`tests/gui_support.py` runs `os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")` at import;
every `test_gui_*.py` imports it before PySide6; `pytest-qt`'s `qtbot`/`qapp` fixtures drive the
event loop; dialogs are injected (file chooser callable, capturing presenter), never a blocking
`exec`. **Record (2026-10-21, this machine):** `QT_QPA_PLATFORM=offscreen` ->
`QApplication.platformName() == "offscreen"`, `devicePixelRatio 1.0`, PySide6 6.12.0, Qt 6.12.0.
`pytest-qt` 4.5.0 loads as a plugin in every pytest run; `tests/test_interfaces.py` and
`tests/test_core_select.py` pass with it installed (65 passed). Existing PySide6-absence tests
are subprocess-based and unaffected.

### 8. Versions locked

`pyproject.toml` lines (mine, X-B3): `"pyside6>=6.12,<7",` in `[project] dependencies` and
`"pytest-qt>=4.5,<5",` in `dev`, each with a one-line grant comment. `uv lock` added pyside6
6.12.0, pyside6-essentials 6.12.0, pyside6-addons 6.12.0, shiboken6 6.12.0, pyside6-pdf and
pyside6-webengine 6.12.0.140 (pulled by the `PySide6` meta-package; question 11's note on the
large wheel set stands), pytest-qt 4.5.0.

### 9. Answers to the other questions (rulings applied)

Q4 status bar: `Device: <reason verbatim>` for the full-resolution selection, the preview-size
reason in the tool tip when it differs, `Device: -` before a file is open; then the file name,
`W x H` and the zoom. Q5/Q7: as section 5, with S3. Q6: as section 5. Q8: as section 5. Q9: one
`save_settings(locs.config_dir, replace(settings, last_parameters=session.parameters()))` at
close, then `shutdown_logging()`; a save error is logged, never raised. Q10: section 6. Q12:
`run(engines=None, locations=None) -> int`, no entry point. Start-up `last_parameters`: used when
its method is in `engines.methods`; else `new_parameter_set(<default id>, {})` with a logged
WARNING (unknown method) or nothing logged (None, first run).

### 10. STOP items (recommended answer first)

- **S1 (with reproduction). The real `select_backend` refuses the stub method id.**
  `clearwater.core.select_backend(Settings(), 100, 100, "stub")` raises `ValueError: no memory
  estimate for method 'stub'; known: c3, ancuti2018` (`core/memory.py:51`), and no real IF-3
  method is merged (WP3.4). So `default_engines()` (real selection + stub method) and the brief's
  "one `gpu` test with the real selection" cannot work as written. Recommended: `default_engines()`
  wraps `clearwater.core.select_backend` so a method id outside `clearwater.core.METHOD_IDS` is
  estimated as the default method `"c3"` (D16), one documented adapter removed at WP4.3 when real
  methods register; the `gpu` test uses it. Alternative A: a stub subclass with `id = "c3"`
  (also makes the starter presets and `last_parameters` resolve, but a stub masquerades as c3).
  Alternative B: `default_engines()` keeps the stub selection; the `gpu` test calls the real
  selection with `"c3"` directly.
- **S2. X-B2's `PhotoReadError` is not on the base.** WP3.6's branch has no commit yet, so the
  class cannot be imported by name. Recommended: classify a photo-read exception by its `kind`
  attribute (`unsupported`/`unreadable`) and its message, with any other exception shown as
  unreadable with its text (brief task 4); the `except PhotoReadError` by name lands when the
  dispatcher rebases this branch on WP3.6 (or in WP4.3). Tests use a local stand-in class with
  `kind`.
- **S3. The downscale rule for sizes the factor does not divide (questions 5 and 7).** A 12 MP
  iPhone photo is 4032x3024 (3024/540 = 5.6); 5.3K video is 5312x2988. Recommended: one
  `downscale(image, k)` block mean where the last row and column of blocks average only the
  pixels they cover (output `ceil(H/k) x ceil(W/k)`), used by the preview, the 1:1 path (k = 1)
  and V8; the statistics proxy uses k = max(1, short_side // 540) (short side 540..1079;
  ERRATUM at the ruling: the figures are 4K 3840x2160 k=4 -> 960x540; 5.3K 5312x2988 k=5 ->
  1063x598; 12 MP 4032x3024 k=5 -> 807x605 (not 604); 48 MP 8064x6048 k=11 -> 734x550). Alternative: an exact fractional area resample to a
  540 short side (NumPy, separable), for the statistics proxy only. This binds WP3.14 and WP4.1
  as question 5 says.
- **S4. Start-up with a settings file from a newer Clearwater.** `load_settings` raises
  `UnsupportedFormatVersionError` and leaves the file untouched. Recommended: a modal message
  ("settings are from a newer Clearwater; defaults are used for this session and the file is
  left as it is"), run on `Settings()`, and do NOT save at close in that session.
- **S5. Who decodes the frame at a position.** Recommended: the shell, on `set_position`
  (loader worker, latest wins), with the frame's statistics passed atomically in
  `set_position(..., statistics=...)` so a new frame is never rendered with the previous frame's
  smoothed statistics; WP3.18 then never decodes for display (it may still call
  `preview.show(frame, statistics)` with a frame it holds).
- **S6. The AD-15 states.** Recommended: add `"failed"` to the brief's four phases (export stays
  unavailable with the failure text); read "cancel returns to unloaded" as: after `cancelled`
  export is unavailable exactly as before the analysis ("Export needs the clip's analysis").
- **S7. `hw_decode` for preview frames.** No setting carries it. Recommended: `hw_decode=False`
  for the single frames the shell decodes (open and position); WP3.18's analysis pass chooses
  its own.

## Round-0 ruling (orchestrator gen 7, 2026-10-21)

Table and the frozen contract ACCEPTED as committed (`795e57f`), including the
`position_changed = Signal(object)` deviation (stated in the report). S1 RECOMMENDED: a stub-era
adapter in `default_engines` estimates an id outside `core.METHOD_IDS` as `"c3"` (D16), WP4.3
removes it; `clearwater.core` is never changed. S2 RECOMMENDED. S3 RECOMMENDED PROVISIONALLY
(goes to CHARC; kept in one function, `imaging.statistics_factor`/`downscale`, so a different
ruling is a one-place change). Exact rule: output `ceil(H/k) x ceil(W/k)`, each block the mean of
the pixels it covers; statistics k = `max(1, min(H, W) // 540)`; figures in S3 above (12 MP is
807x605). S4-S7 RECOMMENDED. `pyside6>=6.12,<7` kept as granted; a possible switch to
`PySide6-Essentials` is with CHARC, made only on the dispatcher's relay.

## Build (tasks 2-8), 2026-10-21

Commits: `5fa8648` preview pipeline; `f2cccbe` window, session, sources, messages, job runner,
engines; `fda06b7` job progress by a 50 ms main-thread poll (+ `JobRunner.run` docstring
clarified, no name changed); `93b0e54`, `82a8697` tests; `d8eb6f4` idle counts undelivered
outcomes, backend reason reset on open. Report `docs/reports/wp3.16-shell-preview.md`.

Contract additions since round 0: none (names). Docstring change: `JobRunner.run` coalescing
sentence ("at most once per job per delivery interval (the shell's runner: 50 ms)").

Gates at `d8eb6f4`: ruff check (repo) 0, ruff format --check 0, mypy strict 0 (87 files); GUI
tests 90 passed (about 14 s, offscreen), run three times. Full pytest: pending a window.

### Verification loop record (own loop, before Reviewer A)

| # | Suspected | Confirmed / rejected | Fix |
|---|---|---|---|
| V-1 | V7 probe started after the planted inline render had already run, so the planted check saw nothing | confirmed (planted test got 10 ms) | probe now triggers the load from its own event loop (`_probe_max_gap_ms(start=...)`) |
| V-2 | V7 worst gap 55-87 ms near the bound | confirmed; cause measured: a pure-Python spinning stub job starves the GIL (scratch probe: 28 ms raw spin; 55-62 ms in the window with either runner) | stub job yields the GIL each report (real jobs spend time in NumPy/FFmpeg); now 11-12 ms. Polling runner kept as a bounded-work design, not as the V7 fix (report corrected) |
| V-3 | Lock contention between the reporting job and the main thread | rejected (lock-free variant measured the same, 66-79 ms) | reverted |
| V-4 | `idle()` true while an outcome is queued but undelivered (test races under load) | confirmed by reading `LatestWorker` | `_undelivered` counter (`d8eb6f4`) |
| V-5 | Device label keeps the previous file's reason until the first render | confirmed | reset to `-` on open (`d8eb6f4`) |
| V-6 | Tab-ified docks report empty before events are processed | confirmed (scratch) | test waits for the layout |
| V-7 | Real `select_backend` with the stub id | handled by S1 adapter; `gpu` test ran (not skipped): `Device: GPU` | - |

## State at the orchestrator gen-7 rollover -- resume here

- **Head:** `614fc5d` on `wp3.16` (before this section's commit), working tree clean, nothing WIP.
- **Done commits (base `4b4da9b`):**
  - `d754a98` build: deps.
  - `795e57f` contract, frozen at round 0.
  - `3de47f8` and `a655769`: round-0 ledger and ruling.
  - `5fa8648` preview pipeline.
  - `f2cccbe` window, session, sources, messages, jobs, engines.
  - `fda06b7` 50 ms polled job progress.
  - `93b0e54` and `82a8697` tests.
  - `d8eb6f4` idle/undelivered fix and backend reset.
  - `614fc5d` report and ledger build section.
- **Own tests at that head:** `tests/test_gui_*.py`, 90 passed (about 14 s, offscreen, run three times). ruff check (repo), ruff format --check and mypy strict all clean.
- **Next:**
  1. The full pytest run. It was requested (WINDOW REQUEST sent), but no window was granted and none was run.
  2. Then Reviewer A round 1, STRONG tier, at the cell's seat. Runner and prompt come from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`. Evidence goes to `C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r1\`. Exclude `docs/proofs` and supply the diff and HEAD sha in the prompt.
  3. Yield after adjudicating the round, before remediating.
- **Open questions:** (S3 and the Essentials switch were ruled after this rollover; see the next section.)
  - X-B2: the by-name `PhotoReadError` catch lands at the rebase onto WP3.6.
  - Report items to carry: the `fda06b7` subject's "(V7)" overstates its effect (report corrected), and the GIL-starvation observation (216-796 ms) goes to WP4.3.

## CHARC rulings applied (orchestrator gen 8, 2026-10-21)

CHARC `d06ed7c969d6249f` (FINAL, 2026-10-21 01:32Z; AD-18 amended on main `d971ee7`), relayed by
the gen-8 dispatch:

- **PySide6-Essentials replaces the `pyside6` meta-package.** `pyproject.toml` now carries
  `"pyside6-essentials>=6.12,<7",`; `uv lock` removed pyside6, pyside6-addons, pyside6-pdf and
  pyside6-webengine (59 packages resolved). Everything the shell imports (QtCore, QtGui,
  QtWidgets; QtTest in tests) is in Essentials. Environment note: `uv sync` uninstalling the
  meta-package from this venv removed files Essentials shares (`ImportError: DLL load failed
  while importing QtCore`); `uv sync --reinstall-package pyside6-essentials --reinstall-package
  shiboken6` repaired it. Any venv that had the meta-package (main's) needs the same at merge.
  Commit `9c6efcb`.
- **S3 RULED** (no longer provisional): integer block mean, k = max(1, short // 540), the last
  row and column averaging only the pixels they cover, output ceil(H/k) x ceil(W/k); 540 at 4K,
  605 at 12 MP, 598 at 5.3K. One function, one owner (`imaging.downscale`); WP3.14/WP4.1 cite it
  and V8's area average uses it. The `imaging` module docstring and the report say RULED.
- S1, S2, S4-S7 and `position_changed = Signal(object)` upheld as ruled.

Gates at `9c6efcb` (+ the RULED docstring): GUI tests 90 passed (14.4 s, offscreen; the `gpu`
test ran, not skipped), ruff check (repo) 0, ruff format --check 0 (140 files), mypy strict 0
(87 files). Full pytest: run in the gen-8 window, see "Round 1" below.

## Full-suite window (gen 8, granted 02:02Z) and Reviewer A round 1

**Full pytest at `0e4412c`** (the two runs one after the other, output under the worktree's
`work/`):

- Normal (`work/full-pytest.txt`, 02:02:05Z-02:17:20Z): `1 failed, 2993 passed, 1 skipped,
  1 warning in 913.39s`, exit 1.
- CuPy unimportable (`work/pytest_nocupy.py`, `sys.modules["cupy"] = sys.modules["cupyx"] =
  None`; `work/full-nocupy.txt`, 02:18:16Z-02:28:27Z): `1 failed, 2474 passed, 520 skipped in
  609.45s`, exit 1; skips without a CuPy/CUDA reason: 1 (`test_color_roundtrip.py:121`, swscale).
- The one failure in both runs is
  `tests/test_conftest_guard.py::test_uncached_tempdir_checks_the_one_root_cpython_would_pick[no-capture-plugin]`:
  INTERNALERROR in `pytestqt/plugin.py` `pytest_configure`, `ValueError: no option named
  'capture'` (pytest-qt 4.5.0 with `-p no:capture`). Reproduced outside the suite (exit 3);
  `-p no:pytest-qt` or `--no-qt-log` cures it (exit 0). It is Reviewer A's F1.

**Reviewer A round 1** (STRONG, at the cell's seat). Evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r1\` (probe, prompt, diff, review.txt,
review.stderr.txt, adjudication.md, test-summary.txt, md5sums.txt). Probe READY with one
`succeeded in`. Assertions passed (banner gpt-5.6-sol/high, 12 `succeeded in`, tokens 142,748,
VERDICT at column 0, ERROR matches all echoed content); withheld paths respected. Verdict
`NEW_CRITICAL_MAJOR_FOUND`.

| # | Sev | Verdict | In env | Planned fix |
|---|---|---|---|---|
| F1 | MAJOR | CONFIRMED (reproduced) | yes | RULING NEEDED, outside the files owned: one line in WP-T1's `tests/test_conftest_guard.py` `_run` adding `-p no:pytest-qt` (recommended) or the same in `_MINI_PYPROJECT` addopts |
| F2 | MAJOR | CONFIRMED (read) | yes | memoise the corrected display image per state and factor; a re-entered 1:1 shows it without `render`; render-count test + planted no-memo |
| F3 | MINOR | CONFIRMED (read) | yes | clear "Rendering full resolution" when a k > 1 request or result supersedes the full render; test |
| F4 | MINOR | CONFIRMED (read) | yes | a refusal names the file when its text does not (real `missing_tool` / timeout texts); test |
| F5 | MINOR | CONFIRMED (read) | yes | a failed render still reports the reasons it obtained to the status bar; test |
| F6 | MINOR | REJECTED | -- | brief binds `gui` only on tests creating a Qt object; `test_gui_deps.py` creates none (prompt paraphrase corrected next round) |
| F7 | MINOR | CONFIRMED (read) | OUT | tag the untagged display copy as sRGB (cleanup, non-blocking) |

Remediation NOT started (yield at the round boundary).

## Round-1 rulings (orchestrator gen 8, FINAL, 02:39Z) and remediation

Rulings: F1 GRANTED as a cross-file, test-only edit in `tests/test_conftest_guard.py` (WP-T1,
closed; outside the owned set): `-p no:pytest-qt` in the two `-p no:capture` child invocations,
with a comment, nothing else; no global `addopts` or `conftest.py` change. F2-F5 as planned (F2's
planted no-cache version must fail). F6 rejection upheld. F7 fixed now. No second full-suite
window: the orchestrator runs the full suite on the rebased candidate.

Commits: `fa99105` F1 (test only, the granted file); `f334ee2` F4; `9afa115` F2, F3, F5, F7 (one
commit: the four share `preview.py`, `render_worker.py` and `tests/test_gui_preview.py` hunks that
pathspec commits cannot split).

F1 proof:
- With pytest-qt installed, `tests/test_conftest_guard.py` 44 passed; both `[no-capture-plugin]`
  cases PASSED (`-k no-capture-plugin`: 2 passed). Before the edit the uncached case failed
  with the INTERNALERROR (full-suite runs above).
- The case still runs without the capture plugin: `pytest --trace-config` with no flags registers
  `_pytest.capture` and `CaptureManager` (1 and 1 lines) and pytest-qt (2); with
  `-p no:capture -p no:pytest-qt` it registers neither (0 capture lines, 0 pytestqt lines). The
  refusal case (`test_refused_before_any_fixture_or_mode_touches_a_temp_folder[no-capture-plugin]`)
  passes before and after; the uncached case's refusal sub-checks (TMPDIR or a later candidate
  naming the footage) still refuse.

Red/green (the new tests run against the four product files restored from `fa99105`, then put
back): 6 failed (F4 `test_refusals_whose_text_omits_the_file_name_it`; F7
`test_every_display_copy_is_tagged_srgb`; F3
`test_leaving_one_to_one_before_the_full_render_clears_the_indicator`; F2
`test_full_resolution_is_rendered_once_per_parameter_state` and the planted
`test_planted_preview_without_the_render_memo_fails` (no `after` to plant on old code); F5
`test_a_failed_render_still_reports_the_device`); `test_supplied_statistics_are_not_served_another_states_render`
passes both ways (it guards the memo key, not the defect). On the fixed code the planted no-memo
test sees 3 renders where the once-per-state test requires 2.

Gates at `9afa115`: GUI tests 97 passed (15.5 s), with `tests/test_conftest_guard.py` 141 passed
(53.7 s); ruff check (repo) 0; ruff format --check 0 (140 files); mypy strict 0 (87 files).

## Reviewer A round 2

Head reviewed `32314d8`. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r2\`
(probe, prompt with "THIS IS ROUND 2" and the corrected item-11 paraphrase, diff, review.txt,
review.stderr.txt, adjudication.md, test-summary.txt, md5sums.txt). Probe READY. Assertions
passed (banner gpt-5.6-sol/high, 15 `succeeded in`, tokens 405,414, VERDICT at column 0; the one
non-echo ERROR is the reviewer's WSL attempt to start the Windows python, subprocess provenance).
Withheld paths respected. The reviewer could not execute Python; all findings REASONED. Verdict
`NEW_CRITICAL_MAJOR_FOUND`. Round-1 F1, F4, F5, F7 verified; F6 rejection not contested.

| # | Sev | Verdict | In env | NEW/REOPENED | Planned fix |
|---|---|---|---|---|---|
| R2-1 | MINOR (reviewer MAJOR; proposed down: a superseded render is the latest-wins cancellation the question-6 ruling sanctions) | CONFIRMED (read) | yes | REOPENED (F2) | memoise the converted render before the post-render `check()`; test; report claim 5 exact |
| R2-2 | MAJOR | CONFIRMED, REPRODUCED (three `view_factor` calls with both shown sizes <= 1 px run until `timeout` kills them, exit 124) | yes | NEW | bound `view_factor`; boundary tests; timeout-guarded planted unbounded version |
| R2-3 | MINOR | CONFIRMED (read) | yes | NEW | clear the frame-decode error banner on the next decoded frame; test |
| R2-4 | MINOR | CONFIRMED (read) | yes | REOPENED (F3) | `show_proxy` clears the full-resolution indicator; test |
| R2-5 | MINOR | CONFIRMED (read) | yes | NEW | add `sidecar` to the `VideoProbeError` test loop (claim 6 then true) |

Remediation NOT started (yield at the round boundary).

## Round-2 rulings (orchestrator gen 8, FINAL, 03:00Z) and remediation

Rulings: R2-2 MAJOR remediate (bounded loop; boundary tests at 0, 1 and 2 device pixels per axis
and a degenerate image; a timeout-guarded planted unbounded version must fail). R2-1 remediate,
the downgrade to MINOR ACCEPTED (a re-render, not a wrong result). R2-3, R2-4, R2-5 as planned.

Commits: `93a3f25` R2-5 (test only: `sidecar` added to the `VideoProbeError` loop); `df0da40`
R2-1..R2-4 (shared hunks in `preview.py` and `tests/test_gui_preview.py`).

- R2-2: `view_factor` caps k at `max(1, H, W)`. Boundary test: five images (1x1, 1x7, 16x16,
  4000x6000, 6048x8064) by shown sizes {0, 0.5, 1, 2} on each axis (80 cases) in a child process
  with a 10 s timeout, each equal to a brute-force largest covering factor (1 for an empty
  displayed size); `view_factor(0, 0, 1, 1) == 1`. The planted unbounded version (the round-1
  code) raises `TimeoutExpired`.
- R2-1: the corrected image is converted and memoised before the post-render `check()`.
- R2-3: `_frame_error_shown` set on a frame failure; the next decoded frame clears `error`.
- R2-4: `PreviewWidget.set_proxy` clears the indicator.

Red/green: against the three product files restored from `4ab99e2`, 4 failed (the boundary
test, the superseded-render test, the show_proxy test, the frame-banner test); the planted
unbounded test and the sidecar loop pass both ways (the first plants its own code; the second
guards a path the round-1 code already handled, it makes claim 6 true).

Gates at `df0da40`: GUI tests 102 passed (37.5 s), with `tests/test_conftest_guard.py` 146
passed (64.1 s); ruff check (repo) 0; ruff format --check 0 (140 files); mypy strict 0 (87 files).

## Reviewer A round 3

Head reviewed `a6d838d` (product code as `df0da40`). Evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r3\` (probe, prompt with "THIS IS ROUND 3"
listing R1 and R2 with their fixes, diff, review.txt, review.stderr.txt, adjudication.md,
test-summary.txt, md5sums.txt). Probe READY. Assertions passed (banner gpt-5.6-sol/high, 20
`succeeded in`, tokens 220,598, VERDICT at column 0, ERROR matches all echo). Withheld paths
respected. No execution (WSL has no Python); all REASONED. Verdict `NEW_CRITICAL_MAJOR_FOUND`.
Round-2 fixes verified.

| # | Sev | Verdict | In env | NEW/REOPENED | Planned fix |
|---|---|---|---|---|---|
| R3-1 | MINOR (reviewer MAJOR; proposed down: a re-measure by the same public function gives identical values, nothing wrong at run time) | CONFIRMED (read) as a contract gap | yes | NEW | ADDITIVE contract getter `Session.effective_statistics()` + `RenderResult.statistics`, if the dispatcher agrees |
| R3-2 | MAJOR | CONFIRMED (read) | yes | NEW (in the F2 fix) | a session statistics revision in the request and the memo key; test + planted identity-only memo |
| R3-3 | MINOR | CONFIRMED (read) | yes | REOPENED (F3) | the indicator tracks a k = 1 render in flight on every path; tests |
| R3-4 | MINOR | CONFIRMED (read) | yes | REOPENED (F4) | the name must stand alone; `assert_refused` checks the full name; test |

Remediation NOT started (yield at the round boundary).

## Round-3 rulings (orchestrator gen 8, FINAL, 03:22Z) and remediation

Rulings: one bounded step (this remediation and round 4, then yield; any later remediation to a
fresh cell). R3-1 MINOR, BANKED, no contract change: a consumer note for WP3.14/WP4.1 in the
report and a Limits line. R3-2 MAJOR remediate (statistics revision in the request and the memo
key; test + planted identity-only memo). R3-3, R3-4 remediate. R3-2 counts as REOPENED from F2's
family.

Commit `211ec88` (R3-2, R3-3, R3-4; shared `preview.py` and test hunks):
- R3-2: `ShellSession.statistics_revision()` (shell-internal, not contract) bumped by
  `_set_statistics` from `set_statistics`, `set_position`, `_open`, `_show`;
  `RenderRequest.statistics_revision`; `AfterKey` gains it.
- R3-3: `request` sets the indicator to `k == 1 and an image is shown` (so a change at 1:1 shows
  it, a k > 1 request clears it); `_on_position` clears it when it invalidates the renderer.
- R3-4: `messages.refusal` accepts the name only standing alone
  (`(?<![\w.-])name(?![\w-])`); `assert_refused` checks the full escaped name.

Red/green: against the four product files restored from `09a7e77`, 5 failed (the in-place
statistics test; the planted identity-only test (no `statistics_revision` to plant on old code);
the indicator-at-1:1 test; the position-change indicator test; the standalone-name test). On the
fixed code the planted identity-only memo shows the stale 51 where 204 is required.

Gates at `211ec88`: GUI tests 107 passed (28 s), with `tests/test_conftest_guard.py` 151 passed
(58 s); ruff check (repo) 0; ruff format --check 0 (140 files); mypy strict 0 (87 files).

## Reviewer A round 4 -- CONVERGED

Head reviewed `f04694b` (product code as `211ec88`). Evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp3.16\r4\` (probe, prompt with "THIS IS ROUND 4"
listing R1-R3 with fixes and the banked R3-1, diff, review.txt, review.stderr.txt,
adjudication.md, test-summary.txt, md5sums.txt). Probe READY. Assertions passed (banner
gpt-5.6-sol/high, 15 `succeeded in`, tokens 196,551, VERDICT at column 0, ERROR matches all
echo). Withheld paths respected. All REASONED. Verdict **`NO_NEW_CRITICAL_MAJOR`**: zero new
blocking, so the loop terminates at round 4. Round-3 fixes verified.

| # | Sev | Verdict | In env | NEW/REOPENED | Planned cleanup fix |
|---|---|---|---|---|---|
| R4-1 | MINOR | CONFIRMED (read): an exception escaping `sources.open_source` becomes a refusal with no file name (`shell.py` `_on_opened`) | yes | REOPENED (F4) | the open task catches and returns `(path, messages.refusal(path, ...))`; test |
| R4-2 | MINOR | CONFIRMED (read): every `UnsupportedFormatVersionError` is called "from a newer Clearwater", but `config/migration.py` raises it also for an older version with no migration | yes | NEW | neutral text (or "newer" only when it is); test with a version-0 file |
| R4-3 | MINOR | CONFIRMED (read): the 1:1 exactness test runs only at DPR 1 | yes | NEW | test only: a child process with `QT_SCALE_FACTOR=2` asserting DPR 2 and exact 1:1 device pixels; planted DPR-ignoring draw fails |

Per the fill, these minors are fixed once in the terminating round's cleanup and open no further
round.

## State for a successor (written at the round-4 yield, 2026-10-21)

- **Head:** the commit of this section on `wp3.16` (on top of `f04694b`); tree clean, nothing WIP.
  Base `4b4da9b`. Product code as `211ec88`.
- **Review:** Reviewer A CONVERGED at round 4 (`NO_NEW_CRITICAL_MAJOR`). Round ledger above.
  Banked: R3-1 MINOR (measured photo statistics not exposed; consumer note in the report), F7
  out of envelope (fixed anyway).
- **Open (cleanup, no further round):** R4-1, R4-2, R4-3 as in the table above, with the planned
  fixes. Files: `src/clearwater/gui/shell.py` (R4-1, R4-2), `tests/test_gui_startup.py` (R4-2),
  `tests/test_gui_open.py` (R4-1), `tests/test_gui_preview.py` or a new child-process helper in
  `tests/gui_support.py` (R4-3). Each with a test failing on the current code.
- **Gates at `211ec88`:** GUI tests 107 passed; with `tests/test_conftest_guard.py` 151 passed;
  ruff, format, mypy clean. Full suite: run by the orchestrator on the merge candidate (the last
  full run was at `0e4412c`, before round 1, with F1's failure since fixed in `fa99105`).
- **Carried to the accept report:** the `fda06b7` subject's "(V7)" overstates (report
  corrected); the GIL-starvation observation (216-796 ms) goes to WP4.3; the by-name
  `PhotoReadError` catch lands at the rebase onto WP3.6; main's venv needs
  `uv sync --reinstall-package pyside6-essentials --reinstall-package shiboken6` after the
  Essentials switch; `tests/test_conftest_guard.py` is changed outside the owned set under the
  round-1 F1 grant.

## Terminating cleanup after R4 (fresh cell, orchestrator gen 8, 2026-10-21)

No further Reviewer A round; Reviewer B at the orchestrator's seat covers it. Started at
`6a65145` (the dispatcher's rebase onto main after WP3.12 and WP3.6; merge base `d0f00ee`, which
differs from main `4ec835d` only in `docs/proofs/wp3.6-accept.md`). `uv sync` clean; Qt 6.12.0
imported without the reinstall.

| Item | Commit | Fail before (test run on the old code) | After |
|---|---|---|---|
| X-B2 by-name catch: `messages.photo_read_failure` catches `PhotoReadError`; `PHOTO_READ_ERROR_KINDS` (the S2 adapter) removed; tests use the real class | `92cf05d` (+ `125b1ac`, ruff N818 rename in the test) | `test_only_a_photo_read_error_by_name_is_shown_with_its_own_text` FAILED (look-alike shown as its own text); the real-reader truncated-JPEG test passed before too (expected: kind matched) | `tests/test_gui_open.py` 28 passed |
| R4-1: `shell._open_task` catches an escaping exception, refusal "<name> could not be opened: <text>" | `7f137f6` | `test_an_exception_escaping_the_open_task_is_a_refusal_naming_the_file` FAILED ("The file could not be opened: engine fault", no name) | passed |
| R4-2: neutral `SETTINGS_FORMAT_TEXT` (was `NEWER_SETTINGS_TEXT`); version-99 test asserts the error's "newer" | `f79b8bb` | `test_an_older_settings_file_without_a_migration_is_not_called_newer` FAILED ("from a newer Clearwater (no migration ... version 0 to 1)") | `tests/test_gui_startup.py` 10 passed |
| R4-3: child process at `QT_SCALE_FACTOR=2`: DPR 2, grab in device pixels, 1:1 corrected pixels exact; planted `devicePixelRatioF -> 1.0` | `2f85c9a` | test only; the planted widget gives EXACT True at DPR 1 (the old test cannot see it) and EXACT False at DPR 2 | both new tests passed |

Gates at `2f85c9a`: `tests/test_gui_*.py` 113 passed (32 s, offscreen); with
`tests/test_conftest_guard.py` 157 passed; `tests/test_io_photo_*.py` 433 passed (1 PIL
corrupt-EXIF warning from WP3.6's own fixtures); ruff check 0; ruff format --check 0 (174
files); mypy strict 0 (107 files). Full suite: run by the orchestrator on the candidate.
Locks on disk against main: nothing under `interfaces/`, `config/`, `core/`, `io/`, `jobs/`,
`tests/conftest.py` changed; `contract.py` touched only by `ca9d7c6` (round 0) and `ecf3085`
(the `JobRunner.run` docstring); `pyproject.toml` adds only `pyside6-essentials>=6.12,<7` and
`pytest-qt>=4.5,<5`; `tests/test_conftest_guard.py` changed only under the round-1 F1 grant.
Not done (scope "nothing else"): `default_engines()` still uses `StubPhotoSource`; WP4.3 wires
WP3.6's `PhotoReader`.

## Reviewer B remediation (orchestrator gen 8, 2026-10-21)

Reviewer B at the orchestrator's seat on `wp3.16-mc` (`475cf12` rebased onto main):
`NEW_CRITICAL_MAJOR_FOUND`. Evidence and adjudication:
`C:\Users\rwsmy\clearwater-review-evidence\wp3.16\reviewB\` (`review-B.txt`, `adjudication-B.md`).
One remediation; no Reviewer A round. Cell depth at the yield: 138,571 / 55 turns (dispatcher).

| # | Adjudicated | Fix | Commit | Fail before |
|---|---|---|---|---|
| 1 | MAJOR | `open_path` invalidates the opener on a routed refusal | `bf0ae2c` | slow A shown after B's refusal |
| 2 | MAJOR | `shutdown` stops both workers, then checks (no short-circuit) | `bf0ae2c` | open worker alive after a 0.05 s preview overrun |
| 3 | MINOR | DELIVER: `QtJobRunner.close` calls `on_done` of every ended job before returning (handle keeps `result`; the queued duplicate is ignored); order documented in `shutdown()` | `bf0ae2c` | `on_done` not called before the save (`assert 0 == 1`) |
| 5 | MAJOR | `Session.settings_refusal() -> Message or None` ADDED to the contract (additive, ruling 2); `ShellSession` and `StartUp` carry it | `bf0ae2c` | `AttributeError` (no member) |
| 6 | MAJOR | statistics memo key + `backend.device` + preview reason | `3d0d800` | `analysed` 1, not 2, after `force_cpu` |
| 7 | MINOR | `_on_source` replaces `PreviewMemo` | `3d0d800` | memo held the previous token |
| 8 | MINOR | settings refusal via `messages.refusal(settings_file, ...)`, text carries the path | `bf0ae2c` | (with #5's test) |
| 9 | ADVISORY | report claim 1 corrected (`show_proxy` converts on the interface thread) | report | - |
| 4 | banked DR-43 | Limits line only | report | - |

Also `232f813`: a stray `import os` that `2f85c9a`'s sed put into the planted `_UNBOUNDED`
child string is removed (no behaviour change). The fixes are grouped in two commits because
`shell.py` carries five of them (no interactive staging here).

Gates at the remediation head: `tests/test_gui_*.py` 119 passed (offscreen); with
`tests/test_conftest_guard.py` 163 passed; `tests/test_io_photo_*.py` 433 passed; ruff check 0;
ruff format --check 0 (174 files); mypy strict 0 (107 files). Full suite: the orchestrator's,
on the candidate. `contract.py` diff is the one added method (docstring + `raise
NotImplementedError`).
