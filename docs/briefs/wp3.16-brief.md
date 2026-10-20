# WP3.16 — Application shell and preview (dispatch brief, DRAFT)

**Status:** DRAFT (orchestrator gen 6, drafting helper), for CHARC approval. Owner decisions:
none inside the package (V2 visual review is the owner's at WP5.x, not here).
- Spec **v0.5.4**. Architecture FINAL 1.0 section 1 ("The preview renders from the proxy with
  the same statistics, so preview and export agree (V8, AD-4)"), section 2 (video preview data
  flow), section 3 IF-1, IF-2, IF-3, IF-5, IF-6, IF-8, IF-10, section 7 ("PySide6 GUI ... CPU/GPU
  shown in the status bar (AD-9), export disabled during analysis with the reason (AD-15)");
  AD-4, AD-9, AD-11, AD-15, AD-18, AD-20, AD-25 (a). Frame `docs/briefs/wp2.4-phase3-frame.md`
  (section 4 grants PySide6 here). WP3.15 report `docs/reports/wp3.15-presets-settings-logging.md`
  "Public API"; WP3.1 report `docs/reports/wp3.1-array-backend.md` "`select_backend` reasons".
- Cell: `implementer-sonnet-high` per the frame; question 1 asks whether it should be
  `implementer-opus-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.16`, branch `wp3.16`, base = the main commit named at dispatch.

**Why.** Plan Phase 3: "WP3.16 owns the main window and defines the places where the other
packages attach their widgets. Each other package owns only its own widget modules. All are
built against stubs of the engines." WP3.17-3.20 (wave 3) depend on it (plan rows "Depends on
WP3.16"), and WP4.3 wires it to the real engines. It is also where G9/V7 (work off the UI
thread) and V8 (preview against export) are first built.

| Field | Content |
|---|---|
| ID and title | WP3.16 — Application shell and preview; plan section 6 Phase 3 row WP3.16 (size L); module `clearwater.gui` (plan 8.1: "PySide6 interface", WP3.16–WP3.20) |
| Goal | The main window with file open, the split-view before/after preview with zoom including 1:1, a preview worker running off the interface thread, the G10 messages, the AD-9 status bar, start-up through the `clearwater.config` API, a Qt runner for IF-8 jobs, and an attachment contract precise enough that WP3.17-3.20 are written against it. |
| Spec / decision clauses | Plan bullet "**WP3.16:** file open, the split-view slider, zoom including 1:1, the screen-resolution preview worker running off the interface thread, and messages for unsupported, damaged or untagged inputs." G1 "Open photos and videos via file dialog."; G2 "Before/after comparison via split-view slider."; G9 "GUI stays responsive during analysis, export and batch processing (work runs off the UI thread)."; G10 "Clear messages for unsupported, damaged, or untagged inputs (Sections 5.1, 5.3, 5.4, 6.5), including ProRAW/DNG."; D27 "GUI before/after: split-view slider only (no side-by-side, no drag-and-drop)"; D28 "GUI framework: PySide6"; D41 "*(amended by D56)* Live preview at screen resolution while adjusting; closely approximates export, exact at 1:1 zoom"; 6.6 "a screen-resolution preview closely approximates the full-resolution result, and a 1:1 view is exact (verified by V8)"; D66 "V7: UI responds within 100 ms during processing"; D108 "Provisional preview: on clip open the current frame is shown at once using its own unsmoothed statistics while analysis runs in the background" (the shell shows it; the switch to smoothed is WP3.18's); D111 (the CPU fallback whose reason the status bar shows). Feeds V7 "UI responds within 100 ms during analysis, export and batch processing (D66)" and V8 "screen-resolution preview vs downsampled full-resolution output differ by less than a threshold set at design; 1:1 view exact" (AD-11 V8: "same frame, export downscaled to the preview size by area average: mean abs ≤ 1/255, max ≤ 3/255"). AD-9 "CPU/GPU use is reported in the status bar ("GPU: RTX 4070 Laptop" / "CPU") ... with the reason when the fallback engaged"; G12 "force CPU processing (Advanced; AD-9)" (the status bar follows it). AD-25 (a) (app-data locations only through `clearwater.config.paths`). DR-37 (a) (the reason string may name a broken CuPy install "CPU: CuPy not installed"; the trigger names "WP3.16's status bar showing the reason"). |
| Depends on | WP2.2 merged (IFs frozen). WP3.15 merged: `app_locations() -> Locations` (`config_dir`, `cache_dir`, `presets_dir`, `log_dir`), `load_settings(folder)`, `save_settings(folder, settings)`, `configure_logging(folder)`, `shutdown_logging()`, `PresetStore(folder).install_starters()`. WP3.1 merged: `clearwater.core.select_backend(settings, height, width, method_id) -> tuple[ArrayBackend, str]` and its reasons `"GPU"`, `"CPU: forced"`, `"CPU: CuPy not installed"`, `"CPU: CuPy failed to load"`, `"CPU: no CUDA device"`, `"CPU: CUDA device unusable"`, `"CPU: estimate 1,982 MiB exceeds free 1,200 MiB"`. WP3.7 merged: `clearwater.io.video.probe(path) -> ProbeResult` (faults with `severity` `refuse`/`warn`/`exclude` and a user-readable `message`) and `VideoProbeError(kind, message)` (`unreadable`, `unsupported`, `sidecar`, `missing_tool`). Stubs (unmerged engines): `stubs.StubPhotoSource` (WP3.6), `stubs.StubVideoSource` (frames, WP3.9), `stubs.StubCorrectionMethod` (id `"stub"`, the c3 stages, identity `render`; WP3.2-3.4), `stubs.StubProxyCache` (WP3.12), `stubs.StubVideoSink` (capabilities, WP3.10), `stubs.StubProgress`. WP3.6's read-error class arrives by X-B2 (committed at WP3.6's round 0). |
| Files owned | `src/clearwater/gui/` (NEW: `__init__.py` (docstring and exports; WP3.17-3.20 add sibling modules and may append exports, nothing else, as X1 ruled for `jobs/__init__.py`), `contract.py` (the attachment contract, task 2), and modules the round-0 table names, for example `shell.py` (main window, start-up), `engines.py` (the injected engines and their stub defaults), `preview.py` (split view, zoom, pan), `render_worker.py`, `jobs.py` (the IF-8 runner), `messages.py` (G10), `imaging.py` (downscale, display conversion)); `tests/test_gui_*.py` (NEW) and, if needed, one helper `tests/gui_support.py` (owned); `docs/reports/wp3.16-shell-preview.md`; `docs/proofs/wp3.16-ledger.md`. `pyproject.toml`: ONLY the frame section 4 grant (`PySide6` in `[project] dependencies`) plus what question 3 rules for the dev group, and `uv.lock` as `uv lock` regenerates it. NOT owned: `src/clearwater/interfaces/`, `config/`, `core/`, `io/`, `jobs/`, `tests/conftest.py`, the widget modules of WP3.17-3.20, `clearwater.app` and any entry point (WP4.3). |
| Interfaces provided | No frozen interface. `clearwater.gui.contract` (task 2) is the base WP3.17-3.20 build on; question 2 asks whether it is frozen at the round-0 yield. A Qt implementation of IF-8 `Progress` (`report`, `cancelled`) whose reports reach the main thread by signal. |
| Interfaces consumed | IF-1 `Image`, `ColorDescription` (`assumed` drives the untagged message; `icc_profile` the display conversion, question 8); IF-2 `ArrayBackend` (`asarray`, `to_host`, `device`) and `select_backend` as above; IF-3 `CorrectionMethod` (`id`, `label`, `parameters`, `stages`, `analyze`, `render`) and `Stage`; IF-5 `ProbeResult`, `Fault`, `VideoSource.frames`; IF-6 `PhotoSource.read`, `PhotoMetadata`; IF-7 `ProxyCache` (carried for WP3.18/3.20, not used here); IF-8 `Progress`, `JobResult`; IF-9 `ParameterSet`; IF-10 `Settings` (`force_cpu`, `last_parameters`). PySide6 (QtCore, QtGui, QtWidgets; QtTest in tests). |
| Wave-2 consumers | None in wave 2 builds on it. Wave 3: WP3.17 (parameter panels and presets, G3/G6), WP3.18 (timeline and analysis, G4/G5, D72, D108), WP3.19 (batch queue and export progress, G7/G8, AD-15), WP3.20 (settings, G12/G13, D74), each against `clearwater.gui.contract`. Phase 4: WP4.3 (wiring the real engines; V7, V8, V18). |
| Hardware flags | `gui` on every test that creates a Qt object; one `gpu` test runs the real `clearwater.core.select_backend` (skips without CUDA or CuPy). No `footage`. No timing FIGURE is recorded: V7's 100 ms is asserted as a bound (task 8); the observed maximum goes in the report as informational, not as a performance claim. |
| Out of scope | Parameter controls and presets UI (WP3.17); the timeline, scrubbing, analysis progress and the provisional-to-smoothed switch (WP3.18); batch, export and its progress (WP3.19); the settings dialog and clear-cache button (WP3.20); the correction method (WP3.2-3.4), photo reading (WP3.6), decode (WP3.9), the cache (WP3.12): all stubs here; `clearwater.app`, a console entry point and real-engine wiring (WP4.3); side-by-side view and drag-and-drop (D27); `QSettings` or any registry write (AD-25 (a): app data only); window-geometry persistence; colour-managed export; reading GoPro data. |
| Debt and decided items | DR-37 (a) ("`_probe_gpu` ... reports an installed CuPy whose DLL or internal module fails to import with `ImportError` as `CPU: CuPy not installed`"; trigger includes "WP3.16's status bar showing the reason") -- PARTLY (meets the trigger) -- the status bar shows the reason strings exactly as WP3.1 defines them, one test per string; the misnaming is fixed in `clearwater.core`, which this package does not touch, so the entry stays OPEN. DR-37 (b) ("the `core.ops` helpers are annotated `ArrayBackend` but `_core` accepts only a `CoreBackend`") -- must not reopen; NOT this package's -- `clearwater.gui` calls no `core.ops` helper and never touches `xp`; the typing fix lands wherever `clearwater.core` is next touched (WP3.4 or WP3.21). G12 "force CPU processing (Advanced; AD-9)" -- PARTLY (surfaced) -- the status bar follows `settings.force_cpu` (`"CPU: forced"`) through `Session.settings_changed` and a re-selection; the toggle is WP3.20's. AD-9 (status-bar device report) -- IMPLEMENTS, with the device-name limit of question 4. AD-15 ("export is unavailable until analysis of that clip completes (button disabled with the reason and the progress)") -- PARTLY (wired to a stub) -- `Session.analysis_changed` / `set_analysis` (task 2); a stub analysis job through the jobs runner disables `actions.export` with the reason and progress, completion enables it, cancel returns to unloaded (task 8); the real analysis is WP3.18's and export WP3.19's. AD-11 V8 ("mean abs ≤ 1/255, max ≤ 3/255") -- PARTLY -- the harness is built here; the bound is met with WP3.4's method at WP4.x. DR-34, DR-35 -- must not reopen -- `config` and `jobs` are consumed, not changed. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green (in a dispatcher window) with the GUI tests headless; the contract shipped and documented; V7's bound and V8's harness and 1:1 exactness shown with the stub method; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: read and table.** Before product code, write in the ledger:
   - the module list and each module's job;
   - the contract of task 2 as signatures with docstrings: COMMIT `contract.py` at this yield
     if question 2 is ruled yes;
   - the threading model (which thread owns what, how a stale preview result is dropped,
     where `select_backend` runs);
   - the preview pipeline for a photo and for a video frame (downscale rule, statistics,
     render, display conversion);
   - the G10 message table (source, severity, presentation);
   - the headless test set-up, with a one-line record that the `offscreen` platform plugin
     loads on this machine (question 3);
   - the PySide6 version locked;
   - the answers to the other open questions.

   YIELD for the dispatcher. Anything the table cannot settle is a STOP.
2. **The attachment contract (`clearwater.gui.contract`).** Types and signatures only, so a
   wave-3 brief can cite each name. As drafted (the round-0 table fixes the names):
   - `Area` (enum): `PARAMETERS` (right dock: WP3.17's Basic and Advanced panels),
     `TIMELINE` (below the preview, shown for video only: WP3.18), `JOBS` (bottom dock:
     WP3.19's queue and progress).
   - `ShellContext` (frozen dataclass) handed to every panel factory: `window`, `session`,
     `engines`, `locations` (`clearwater.config.Locations`), `presets` (`PresetStore`),
     `jobs` (the IF-8 runner), `messages` (the G10 presenter), `actions`.
   - `Session` (QObject): the shell's state, the only place panels read and change it.
     Signals: `source_changed(object)` (an `OpenedSource` or None), `parameters_changed(object)`
     (`ParameterSet`), `settings_changed(object)` (`Settings`), `position_changed(int)` (pts
     ticks, video), `statistics_changed()`, `backend_changed(str)` (the AD-9 reason),
     `analysis_changed(object)` (an `AnalysisState`: `none`, `running` with done/total,
     `complete`, `cancelled`; AD-15).
     Methods: `source`, `parameters`, `settings`, `method` (the `CorrectionMethod` for
     `parameters.method`), `analysis`, `set_parameters`, `set_settings`, `set_position`,
     `set_analysis` (WP3.18 drives it; the shell disables `actions.export` from it),
     `set_statistics(Mapping[str, Statistics] | None)` (None = the frame's own unsmoothed
     statistics, D108; WP3.18 supplies smoothed ones).
   - `OpenedSource` (frozen dataclass): `path`, `kind` (`"photo"`/`"video"`), `image` (the
     full-resolution host `Image`, or the current frame), `metadata` (`PhotoMetadata` or
     None), `probe` (`ProbeResult` or None), `warnings` (the shown G10 warnings).
   - `Engines` (frozen dataclass): `photo_source` (IF-6), `video_probe` (a
     `Callable[[Path], ProbeResult]`), `video_source` (IF-5 frames), `video_sink`
     (capabilities, D74, for WP3.20), `cache` (IF-7, for WP3.18/3.20), `methods`
     (`Mapping[str, CorrectionMethod]`, the default first), `select_backend`; a
     `stub_engines()` for tests and a `default_engines()` that uses what is merged
     (`clearwater.io.video.probe`, `clearwater.core.select_backend`) and stubs the rest.
   - Window API: `attach(area, factory: Callable[[ShellContext], QWidget], *, title)`;
     `set_settings_dialog(factory)`; `actions.open`, `actions.export` (disabled until WP3.19
     connects it; `set_unavailable(reason)` for AD-15's "button disabled with the reason"),
     `actions.settings`, `actions.quit`; `preview.show(image, statistics=None)` and
     `preview.show_proxy(NDArray[np.uint8])` for WP3.18's scrubber (D72).
   - The jobs runner: `run(job: Callable[[Progress], JobResult], *, on_done)` on a worker
     thread, reports coalesced to the main thread, `cancel()` setting `Progress.cancelled`.
3. **Start-up and window (WP3.15 API).** `locs = app_locations()` (injectable: tests pass a
   `Locations` under `tmp_path`); `configure_logging(locs.log_dir)`;
   `load_settings(locs.config_dir)`; `PresetStore(locs.presets_dir).install_starters()`;
   the parameters from `settings.last_parameters` when its method is in `engines.methods`,
   else the default method's empty set with a logged warning; menus File (Open, Export, Quit),
   View (fit, 1:1, zoom in, zoom out, reset split), Tools (Settings); the status bar. At close:
   question 9; `shutdown_logging()`.
4. **File open (G1) and G10.** A file dialog filtered to the photo and video extensions plus
   "All files"; routing by extension (photo: `.heic`, `.heif`, `.jpg`, `.jpeg`, `.png`, `.tif`,
   `.tiff`, `.dng` so the D116 refusal is shown; video: `.mp4`; a sidecar per
   `clearwater.io.video.is_sidecar`); an unknown extension is "unsupported". Messages per
   question 10, from: `VideoProbeError` (`kind`, message), `ProbeResult.faults`
   (`refuse` → refused, `warn` → banner), the WP3.6 read error (X-B2; until it merges, any
   exception from `photo_source.read` is shown as unreadable with its text),
   `ColorDescription.assumed` (untagged, 6.5 / D54). A refused file leaves the previous
   source open.
5. **Preview widget (G2, D27, D41, 6.6).** One view, split by a draggable vertical divider:
   the original on one side, the corrected on the other, both from the same downscaled input.
   Zoom: fit, steps, 1:1 (one image pixel per device pixel, `devicePixelRatio` honoured), pan.
   At 1:1 the corrected side shows the full-resolution render (question 6).
6. **Preview worker (G9, D108).** Off the interface thread; latest wins: a parameter, source
   or zoom change supersedes the job in flight, whose result is dropped when it arrives. Per
   job: `select_backend(settings, h, w, method.id)`; downscale (question 7); `asarray` to the
   backend; for each stage in `method.stages`, `analyze` with the earlier results (or the
   session's supplied statistics); `render`; `to_host`; convert for display (question 8).
   An exception becomes a message, never a crash; the last good preview stays.
7. **Status bar (AD-9).** The device text of question 4, updated after each selection and when
   `settings.force_cpu` changes; the file name, size and zoom.
8. **Tests** (headless, `gui`-marked; the real app-data folder never resolved):
   - start-up on a `tmp_path` `Locations`: log file created, starters installed once,
     settings loaded, a `last_parameters` naming an unknown method falls back with a warning;
   - open: a photo and a video through the stub engines; every G10 source of task 4 once,
     including a DNG path and a sidecar path; a refusal keeps the previous source;
   - V7 bound: while the preview worker runs a CPU-heavy stub render (NumPy, about 2 s) and
     the jobs runner runs a stub job reporting at a high rate, a `QTimer` probe on the main
     thread never waits more than 100 ms (D66);
   - latest wins: three parameter changes in quick succession display only the last result;
   - V8 harness: with the identity stub, the preview equals the full-resolution render
     downscaled by the same area rule, exactly; the harness takes any method, so WP4.x re-runs
     it with WP3.4's against AD-11's V8 bound;
   - 1:1 exact: the 1:1 corrected pixels equal the full-resolution render bit for bit;
   - status bar: every reason string of `select_backend` shown as question 4 rules, including
     `"CPU: forced"` after `force_cpu` is set; one `gpu` test with the real selection;
   - AD-15 on the stub: a stub analysis job through the jobs runner disables `actions.export`
     with the reason and the progress, completion enables it, cancel returns to unloaded;
   - the contract: a dummy panel attached to each `Area` receives a `ShellContext`, reacts to
     `parameters_changed` and calls `set_parameters`; a dummy settings dialog opens from
     `actions.settings`;
   - a planted wrong implementation fails by name: a render on the interface thread (V7
     fails), a stale render displayed, 1:1 showing scaled pixels, a refusal shown as a
     warning, a write to the real app-data folder;
   - dependency rule (plan 8.1, frame rule 5; spec 10.1 "The GUI, video and I/O layers depend
     only on this interface"): no `clearwater.gui` module imports `clearwater.methods`,
     `cupy`, `cupyx` or `CoreBackend.xp`; and a subprocess test that importing
     `clearwater.core`, `.config`, `.jobs`, `.io` still loads no `PySide6`.

## Declared operating envelope

Windows 11; Python 3.12; PySide6 as locked; one Clearwater window in one process; the owner's
laptop display (any `devicePixelRatio`); photos up to 48 MP and 4K video frames (D117) through
the stub engines; tests headless on the `offscreen` platform. Out of envelope: several windows
or processes, screen readers and accessibility (not in the spec), other operating systems
(portable, N1, not run there), V7 with a real method that holds the GIL in pure Python (WP4.3
re-measures with the real engines), a colour-managed display pipeline beyond question 8.

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.16\rN\`; ledger `docs/proofs/wp3.16-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `probe.txt`, `review-diff.txt`,
  `review.txt`, `adjudication.md`, `md5sums.txt`, `test-summary.txt` as there); the reviewer
  excludes `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - nothing heavy on the interface thread (open, probe, `select_backend`, downscale, analyze,
    render, conversion); signals across threads queued; no Qt object touched from a worker;
  - latest wins without leaks or races; a dropped result never shown; shutdown with a job in
    flight;
  - 1:1 exactness and the downscale rule (V8);
  - every G10 path, and refusal versus warning;
  - start-up and close through the `clearwater.config` API only; no `QSettings`, no write
    outside the injected `Locations`;
  - the contract complete for WP3.17-3.20 as task 2 lists, with nothing a panel must reach
    around it for;
  - the pyproject lines exactly as granted; nothing in `interfaces/` changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating. Yield
  at every round boundary; the dispatcher reads your depth (~250K evaluation point, ~400K
  stop).
- **Full-pytest windows (X5).** The full suite (about 1844 tests, 9-11 min) runs ONLY in a
  window the dispatcher grants by message, in the background with output to a file under
  `work/`; send `WINDOW RELEASED: <summary>` when it finishes and carry on. Inner loops run only
  your own tests.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the module list, the contract (every name), the threading model, the G10 table,
  the V7 bound and observed maximum, the V8 and 1:1 results, the pyproject diff, the gates, the
  Reviewer A rounds and verdict, open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20); a dependency beyond
  PySide6 and what question 3 grants; any OS-specific code (`QSettings`'s registry backend
  included); a contract change after the round-0 yield that renames or removes a name (if
  question 2 freezes it); a test that cannot run headless; the round-0 table showing a choice
  the brief left open.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.16): ...` (conventional commits
  carrying the WP id), with a `Co-Authored-By:` footer naming your model. Never a bare `cd`.
  Never post to a mailbox. Gates: ruff check, ruff format --check, mypy strict, full pytest (in
  a window); no harness gate. Report `docs/reports/wp3.16-shell-preview.md` (claims, evidence
  paths, limits, and a "Contract" section the wave-3 briefs cite). GoPro IMU/GPS data is out of
  scope everywhere.

## Rulings (CHARC, pending)

_Placeholder: CHARC's rulings on the questions below._

### Questions as drafted (recommended answer first)

1. **Cell tier.** The frame assigns `implementer-sonnet-high`. The package is size L, defines
   the contract four packages are written against, and carries the threading that V7 and V8
   rest on (latest-wins cancellation, GPU work on a worker thread, queued signals).
   Recommended: `implementer-opus-high` (`.claude/agents/implementer-opus-high.md`: "Select by
   TASK reasoning-density and leverage, not by phase").
   Alternative: sonnet-high, on the ground that this brief fixes the contract's shape in task 2.
2. **Freeze the contract at round 0.** Recommended: yes, as X2 did for `clearwater.config.paths`:
   `clearwater.gui.contract` (types, signatures, docstrings, no behaviour) committed at the
   round-0 yield; between round 0 and accept only additive changes, each named in the next
   yield; frozen at accept, after which a change is a CHARC ruling. The WP3.17-3.20 briefs are
   drafted against the round-0 commit and finalised after WP3.16 merges.
3. **Headless GUI tests and `pytest-qt` (needs a CHARC ruling before dispatch: frame section 4,
   rule 11).** `pytest-qt` is not in the `dev` group (plan 8.3 names
   it; AD-18 records its MIT licence; frame section 4 does not grant it); the `gui` marker
   exists. Recommended: CHARC grants `pytest-qt` to the `dev` group; GUI tests set
   `QT_QPA_PLATFORM=offscreen` before any PySide6 import (a module-level `os.environ.setdefault`
   in each GUI test module or `tests/gui_support.py`, since `tests/conftest.py` is not owned)
   and the round-0 table records that the plugin loads. Alternative: no grant; tests create one
   `QApplication` themselves and drive it with `QtTest.QTest`.
4. **The status-bar device text.** AD-9's example "GPU: RTX 4070 Laptop" needs a device name
   that no merged API gives (`select_backend` returns `"GPU"`), and `clearwater.gui` may not
   import CuPy. Recommended: show `Device: ` plus the reason verbatim (`GPU`, `CPU: forced`,
   `CPU: estimate ... exceeds free ...`), for the full-resolution decision (what export will
   use), with the preview-size decision in the tooltip when it differs; before a file is open,
   `Device: -`. DR-37 (a) stays open (the shell shows the string it is given). Alternative: a
   device-name accessor in `clearwater.core` (WP3.1's module; a later package).
5. **The statistics basis of the photo preview (V8).** AD-4 measures video statistics on the
   540 proxy and uses them unchanged for preview and export; nothing says what a photo's are
   measured on. Recommended: the same rule for photos (an area-averaged 540-short-side proxy,
   statistics measured once per parameter state and used unchanged at every zoom and at
   export), so V8 holds by construction as for video; this binds WP3.14 and WP4.1. WP3.16 keeps
   the basis behind one function so the ruling is a one-place change; with the stub method
   (zeros) the choice is not observable here. Alternative: full-resolution statistics for both
   (slow on a 48 MP photo for every parameter change).
6. **"Exact at 1:1".** Rendering a crop is not exact (the pyramid and blurs reach across it).
   Recommended: at 1:1 the worker renders the whole image at full resolution once per
   parameter state (latest wins), shows the screen-resolution result scaled until it arrives,
   with a "rendering full resolution" indicator, and keeps it while panning.
7. **The screen-resolution downscale.** Recommended: an integer block mean (AD-5's
   area-average kind) by the largest factor k for which the image is still at least the view's
   device-pixel size; Qt scales the last step for display only. Preview and V8 then compare at
   that size by the same rule. Alternative: an exact fractional area resample to the view size.
8. **Display colour.** A Display P3 photo shown as raw values on an sRGB screen looks wrong.
   Recommended: the display copy (never the data) is tagged with the source ICC through
   `QColorSpace.fromIccProfile` and converted to sRGB for display; untagged sources are shown
   as sRGB. Alternative: show raw display-encoded values.
9. **G13 at close.** The last-used parameters (D89) persist; WP3.20's row carries G13 but the
   shell owns the close. Recommended: the shell saves `settings` with `last_parameters` set by
   one `save_settings(locs.config_dir, ...)` at close; WP3.20 saves the fields it edits when
   its dialog is accepted. No `QSettings`, no geometry persistence.
10. **G10 presentation, and X-B2 (cross-brief, WP3.6 and WP3.16).** Recommended: a refusal
    (`VideoProbeError`, a `refuse` fault, WP3.6's `PhotoReadError` of X-B2 with kinds
    `unsupported`/`unreadable`) is a modal message naming the file; a warning (`warn` faults,
    `ColorDescription.assumed`) is a non-modal banner above the preview while the file is open;
    both go through an injectable presenter so tests capture them without a blocking dialog.
    WP3.6 commits `PhotoReadError` at its round-0 yield so this package catches it by name.
11. **X-B3 (cross-brief, WP3.6 and WP3.16): the two dependency grants.** Both edit
    `pyproject.toml` and `uv.lock` in parallel worktrees. Recommended: each adds only its own
    lines; whichever merges second rebases and regenerates `uv.lock` with `uv lock` (no hand
    merge), and says so in its report. Note for CHARC: the `PySide6` wheel set is large;
    `PySide6-Essentials` (same project and licence, QtCore/QtGui/QtWidgets) would do for v1, but
    the grant names `PySide6` and this brief does not deviate unless CHARC rules it.
12. **An entry point.** Recommended: none here (`clearwater.app` and any console script are
    WP4.3's); the shell exposes one `run(engines=None, locations=None) -> int` that WP4.3 calls.
