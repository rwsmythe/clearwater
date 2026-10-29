# WP4.3 ledger (cell 1, implementer-opus-high; base main `038f02e`)

Brief: `docs/briefs/wp4.3-brief.md` (FINAL; Rulings `2c4476d9869df056` govern Q1-Q13, `7c7df3dbe237ceb7`
govern Q14-Q24). Round-0 evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\r0\`
(`r0_startup_timings.py` md5 `1b86ba2c`, `r0-base.txt` `a405108f`, `r0-detect.txt` `7b099e4f`,
`r0-gpu.txt` `171526fd`, `r0-window.txt` `bc2e9aaf`).

## Round 0 (brief task 1 and task 2)

### Task 1: the stubs on the product path at `038f02e` (confirmed by reading)

- `gui/engines.py:170-174`: `StubVideoSource`, `StubVideoSink`, `StubProxyCache` and
  `select_backend=stub_era_select_backend` (`:101-121`; `STUB_ERA_METHOD_ID` `:42`).
- `gui/export_panel.py:218`: `unavailable_exports()` when `install_export_panels` gets no engine.
- `gui/timeline.py:799`: `stub_analysis_factory` when `install_timeline` gets no factory.
- `gui/settings_dialog.py:109` `interim_resolve_encoder`, the default at `:872` (and `:892`'s text).
- Nothing calls the four installs; `shell.run` (`gui/shell.py:589`) shows a window with no panel.

### Measured start-up steps (this laptop, 2026-10-29, not exclusive: WP-T6 may have held the host)

| Step | Thread | Measured |
|---|---|---|
| imports (PySide6 + `clearwater.gui.shell`), fresh process | main | 1,458 ms |
| `QApplication` | main | 11.8 ms |
| `app_locations()` | main | 0.01 ms median (n=20) |
| `load_settings(config_dir)` (with `last_parameters`) | main (inside `MainWindow`) | 0.11 ms median, 7.0 ms max (n=20) |
| `default_engines()` (today's form) | main | 0.12 ms |
| `MainWindow(engines, locations)` incl. `start_up` (log, settings, starter presets) | main | 13.8 ms |
| `show()` + first `processEvents` | main | 3.4 ms |
| leftover scan, `remove_leftovers` over 6 folders / 750 files | main (see S-order) | 0.81 ms median, 1.12 ms max |
| `DiskProxyCache` open, 20 GB = 309 entries x 64.6 MB (a real GX011627 entry is 64,598,686 B) | see S1 | **117.6 / 126.5 / 16,372.8 ms** (min / median / max, n=5; the max is the FIRST open after the packs were written) |
| `DiskProxyCache` open, stress 2,000 x 10 MB (20.0 GB) | see S1 | **657.9 / 765.6 / 33,144.6 ms** (first open again the max) |
| `detect_capabilities()`, fresh process | job worker | 550 ms (+202 ms import); cached call 4.9 ms; both encoders available, 8 and 10 bit |
| GPU probe: `import clearwater.core` (fresh process; already loaded in the app) | job worker | 1,034 ms |
| GPU probe: first `select_backend(Settings(), 1, 1, "c3")` (CuPy import, device, test kernel) | job worker | 946.9 ms -> `"GPU"`; a later 4K selection 0.03 ms; forced 0.005 ms |

Cache method: entries created through `DiskProxyCache` itself, each pack then made sparse and
extended by `truncate` (the open reads only each pack's header, its size and three small files,
`cache/store.py:600-620`, so pack content does not change the open's cost). The first-open cause
was not isolated (consistent with on-access scanning of freshly written files); warm opens are
over 100 ms in both shapes, so Q4's rule "moves off the interface thread if it is over 100 ms"
applies: see **S1**.

### The design table

**1. Module layout and import rule (Q2 as ruled; Q15).**
- `app/__init__.py` (docstring only: names the four modules; `__all__` unchanged), `app/composition.py`
  (Q16 only, plus S1 if granted), `app/main.py` (`main(argv=None) -> int`, `build_application(...)`
  used by `main` and the tests; the ONLY Qt module), `app/startup.py` (journal, leftover set, cleanup,
  start-up job callables), `app/analysis_adapter.py` (`ClipAnalysis` adapter + factory),
  `app/activity.py` (`ClipLocks`, the `ExportJobs` wrapper). `src/clearwater/__main__.py` imports
  `clearwater.app.main` only.
- The three Qt-free modules satisfy the gui seams STRUCTURALLY: `OpenedSource`, `Engines` live in
  `gui/contract.py`, which imports PySide6, so the adapter declares its own small Protocols for the
  members it reads (`path`, `probe`; `select_backend`, `cache`).
- `tests/test_app_deps.py` edit: `:91` module set -> `["__init__.py", "activity.py",
  "analysis_adapter.py", "composition.py", "main.py", "startup.py"]`; the gui/PySide6/shiboken6 ban
  exempts `main.py` alone; the cupy/cupyx ban stays for all six; docstring `:1-7` restated;
  `:77-86` and `:104-128` unchanged.

**2. Start-up sequence (Q4, Q5, Q11 as ruled; S1 and S-order pending).**
1. `main`: `QApplication` (main) -> `app_locations()` (main; AD-25 (a), nothing else reads the
   environment for a folder).
2. Engines (main): `default_engines(locations=locations)` -> real photo legs, methods (`"c3"`
   first), `composition.backend_selector()`, `composition.video_source()`,
   `composition.video_sink()`, and the ONE cache (S1).
3. `MainWindow(engines, locations)` (main): its `start_up` configures the log, reads the
   settings (the ONLY settings read in the process), installs the starter presets.
4. Leftover cleanup (main, synchronous, before `show()`; S-order): folder set of item 3 below;
   removed and failed files logged (N9) - the log is configured by step 3, so this is the first
   point where the folder set is known (`Settings.output_folder`) AND the log exists.
5. Installs (main), in this order: `install_parameter_panels(window)`; `install_timeline(window,
   adapter_factory)`; `install_export_panels(window, guarded_exports)`;
   `install_settings_dialog(window, resolve_encoder=capability.resolve_encoder, catalog=catalog)`;
   then `window.show()`.
6. Start-up jobs on `window.jobs` (worker threads, parallel): (i) the cache open with
   `session.settings().cache_limit_bytes` read on the main thread when the job is made (S1);
   (ii) `catalog.start(window.context)`, the first `EncoderCatalog.start` (detection 550 ms);
   (iii) the GPU probe `select_backend(session.settings(), 1, 1, <default method id>)`, its reason
   to the status bar as `Device: <reason>` while no file is open (S3) and to the log (AD-9).
   `session.settings_changed` with no file open re-runs (iii) so `CPU: forced` follows G12.
7. `app.exec()`.
- Q17: `default_engines()` with no `locations` keeps today's stub video legs (`gui/engines.py:170-172`),
  real photo legs and methods, and the root's `backend_selector()`; it opens no cache and writes
  nothing under app data; `tests/test_wp41_gui.py:28-44` and `tests/test_wp41_v8.py:104-112` run
  unchanged. A test pins `build_application`'s engines wholly real.

**3. Leftover folder set and journal (Q3 as ruled).**
- Journal `config_dir/write-journal.json`, written with `config.atomic.atomic_write_text`:
  `{"format_version": 1, "entries": [{"id": "<uuid4 hex>", "folder": "<absolute folder>"}]}`; one
  process-local lock around read-modify-write.
- The wrapper adds the entry on the worker immediately before the engine's job runs (so before any
  temporary exists) and removes it in `finally` (commit, failure, cancel). The folder is
  `final_output_path(source, settings, kind).parent` (the planner's own folder: D34's source folder
  or `Settings.output_folder`).
- Start-up set = `{Settings.output_folder}` (when set) U {every journal folder}; `remove_leftovers`
  (unchanged) over it; then the scanned entries are removed from the journal. Never a folder because
  a source lies there; a journal folder that is a source folder is scanned (D85 kept). The cache root
  is cleaned only by `DiskProxyCache`'s own open.
- A journal that fails to decode: S6.

**4. The analysis adapter (WP3.18 mapping as corrected by errata 1 and 5; Q18).**

| Seam member | Adapter |
|---|---|
| factory `(source, method, engines)` (main) | `make_analysis_factory(settings=lambda: window.session.settings(), engine_factory=AnalysisEngine)` returns the factory; it builds the adapter only (no I/O). `engine_factory` is the injection point of the V18 test hook (Q24). |
| `run` (worker) | First: wait for the cache (S1); `key = cache.key_for(path)`; `backend, reason = engines.select_backend(settings(), h, w, method.id)`; `source = composition.video_source(None if backend.device == "cpu" else backend)`; `expected = jobs.expected_frames(probe)`; `AnalysisEngine(method, backend, cache, key, source, probe, params=eff, hw_decode=backend.device != "cpu", expected_frames=expected)` with the export's defaults for window and kind (the same as `jobs/export.py:979-989`, so V17 reuse holds). Then under the DR-62 lock (item 5): a KEPT job takes priority: `engine.set_parameters(eff_latest, focus)` then run the kept job and clear it; else the "First call" / "Later" rule. `result.ok` -> complete; `analysis.CANCELLED` -> return; other -> `RuntimeError(result.failure)`. A test against the real engine shows a kept job ends under the latest parameters; if not, one more job. |
| `retarget` (main) | engine not built yet (first run waiting for the cache or the lock): store the latest target, return True (the engine is built with it); built: `set_parameters` None while running -> True; a job returned -> keep it, clear completion, return False. Cheap: engine lock only. |
| `pts` (main) | the adapter's own tuple under a small lock; refreshed on the worker from `cache.lookup(key).pts_ticks` at run start, at most every 100 ms from the progress wrapper, and at run end (F-2). Never a cache call on the main thread. |
| `proxy` (worker) | `cache.proxy(key, pts)`; `KeyError` when absent or before the key is known. |
| `statistics` (worker) | None until a full `run` completed under the latest parameters (flag set at ok-return with no kept job and no un-absorbed retarget, cleared at run start and on a kept job); a generation read before and after `engine.smoothed_record(pts)` returns None when a run started in between (DR-51 (a) race test). |
| progress / cancel | `progress.report` passed through (plus the "Waiting for the other job on this clip" text while waiting); cancel through the job handle. |

The backend is chosen once, at the adapter's first run (the engine holds it): S2.

**5. DR-62 (Q8, WAIT), DR-82 (Q22), DR-68 (Q6), DR-44 (c).**
- `activity.ClipLocks`: one process-local lock per `CacheKey`, acquired by the adapter around its
  engine job and by the wrapper around a VIDEO export's engine job (a photo has no analysis; no
  lock). Acquire polls every 50 ms, reports "Waiting for the other job on this clip", and returns
  False on `progress.cancelled()` (the adapter returns early; the wrapper returns `JobResult(False,
  (), (), CANCELLED, "none", t)`; nothing written). The key is computed on the worker; an `OSError`
  there leaves the job to the engine's own text. Never nested, so no lock order.
- Wrapper job callable, on the worker, in order: (1) DR-82: `final_output_path(source, settings,
  kind)`; `OutputNameError` -> failed result `"<name>: this file name cannot be used for an output
  file; rename the file."` (`ascii_text`), before any read or probe; `ValueError`/`OSError` -> left
  to the engine (no journal entry: no plan, no temporary); (2) video: the DR-62 lock; (3) DR-68:
  the preview's plan release (below); (4) journal add; (5) the engine's job; (6) the AD-9 log line
  naming `JobResult.device`; (7) journal remove, lock release (`finally`).
- DR-68: `LatestWorker` (`render_worker.py`) gains an undroppable chore queue: chores run before
  the next pending task and before the thread exits on `stop`, never superseded. One gui Protocol
  `PreviewDeviceBackend` (`release_fft_plans()`, `render_worker.py`, AD-29; test: `CupyBackend`
  satisfies it, `NumpyBackend` does not). The controller remembers the last render backend (set on
  the worker); the chore calls its `release_fft_plans()` on `clearwater-preview`. Boundaries: source
  change or unload (`_on_source`), shell close (`stop`), and before a GUI export or batch job selects:
  `PreviewController.release_device_plans(timeout_s) -> bool` (thread-safe: queues the chore, waits on
  an event), passed to the wrapper by `main` as a plain callable. `gpu` test: `free_device_bytes()`
  before a 1:1 4K FFT-route render, after it, and after the boundary, back within one pool block; a
  planted controller without the release fails by name.
- DR-44 (c): measured first (task 9): from `close()`, the end time of a real analysis mid-decode, an
  export mid-encode and a batch item, on `hevc8-bt709-full.mp4` in the light run and on GX011627 in
  the window; `gui/jobs.py` is touched only if one exceeds `SHUTDOWN_TIMEOUT_S` (5 s).

**6. DR-75 (Q19), DR-85 (Q21), DR-52 / DR-61.**
- DR-75: `RenderRequest` gains `display_icc: bytes | None`; the controller computes it once per source
  on the main thread: `color.icc_profile` when present, else `built_in_profile(color,
  metadata.source_format)[1]` when not None, else None (video: no metadata -> `icc_profile`, unchanged).
  `render_worker.py:423` and `:450` and `preview.py:442-444` use it. The Q19 condition is MET:
  `wp4.1\r3\r3_repro.py:17-21` rebuilds a 16x16 (200, 40, 60) nclx-only Display P3 HEIC with
  `pillow_heif.encode(..., nclx_profile={primaries 12, transfer 13, matrix 6, full range})`; its
  output records the preview (199, 40, 60) vs (217, 0, 54) through the built-in. The REQUIRED test
  builds it under `tmp_path`; the expected colour comes from the exported PNG's embedded profile read
  back, never from `built_in_profile`; RED on the base.
- DR-85: `tests/test_app_startup.py` builds the application over `settings.json` with
  `last_parameters.created` = `0001-01-01T00:00:00+01:00`; requires the window up, the file set aside
  (`settings.json.bad-*`), defaults in the session; `pytest.mark.xfail(strict=True, reason="DR-85:
  OverflowError escapes load_settings until WP4.3a's fix is on main")`.
- DR-52: `interim_resolve_encoder` deleted; `capability.resolve_encoder` the default of both
  functions; `install_settings_dialog(..., catalog=None)`; a test that `VideoEncodeError("unavailable")`
  surfaces as the D74 reason; the erratum appended to `docs/reports/wp3.20-settings.md`. DR-61 (i)-(iii)
  each with a RED-first test.

**7. G-matrix (`tests/test_app_wiring.py`, on `build_application` over tmp app data and WP2.3 fixtures).**
G1 open photo/video/DNG refusal routing; G2 split; G3 the c3 schema's panels, live preview; G4 scrub
proxies then full resolution on release (real adapter); G5 analysis progress and cancel; G6 presets
save/load/import; G7 batch skip-and-log; G8 export progress and cancel with no partial output; G9 with
V7; G10 HLG/PQ refusal, truncated, untagged, DNG, DR-35 (a) `NUL` stem through the real engine,
DR-82's refused name; G11 v2 (named, no test); G12 every setting, force CPU giving `CPU: forced`;
G13 persistence over two window lifetimes. Plus V11's leftover leg, the footage-absence test (a
`scandir` spy; a stand-in footage folder under `tmp_path`; with `clearwater.local.toml` the real folder
appears in no computed set) and the import-time witness extension (DR-84).

**8. V7, V8, V18.**
- V7 (Q10, EXCLUSIVE window, LAST): (a) GX011627 GPU analysis with the timeline updating (F-2);
  (b) scrubbing during it; (c) File > Export of GX011627; (d) a 300-still batch under `tmp_path`
  (DR-50); (e) a 1:1 4K preview render during (c); (f) start-up over a planted 20 GB cache. The
  WP3.16 10 ms `QTimer` probe; longest gap, p99 and tick count each; bound 100 ms; beside the
  stub-era 11-12 ms (WP3.16), 12-39 ms (WP3.18), 11-13 ms (WP3.19). Gate forms on fixtures in
  `tests/test_app_v7.py` (`gui`, `slow`). Window driver: S7.
- V8 (Q12, AD-11 as amended): photo at fit (k > 1: 2 and 4) and 1:1 against the exported 16-bit PNG
  read back and `imaging.downscale`d by the same k, DR-75's sample included; video pre-encode
  through `imaging.preview_export_difference` on the real method and backend.
- V18 (Q24): gate form on `hevc8-bt709-full.mp4` with the analysis held by the `engine_factory` hook
  (corrected frame shown before completion; after it the shown statistics equal
  `engine.smoothed_record(pts)`); GX011627 in the window.

**9. Existing tests changed or deleted.**
- `tests/test_gui_status.py:128-141` `test_stub_era_adapter_estimates_an_unknown_method_as_c3` and
  `:144-146` `test_default_engines_select_cpu_forced_with_the_real_selection`: DELETED (the S1
  stand-in goes, Q11); the import at `:18` follows.
- `tests/test_gui_status.py:148-162` `test_real_selection_through_the_shell_shows_gpu`: EDITED to
  `core.select_backend` with the real methods (`c3`), assertions unchanged (Q15).
- `tests/test_gui_settings_dialog.py:778-785` `test_interim_rule_matches_the_wp310_rule`: DELETED
  (DR-52); `:768` in `test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule` EDITED to
  compare with `capability.resolve_encoder` (one of "the default-rule tests" of the grant).
- `tests/test_app_deps.py:1-7`, `:89-101`: EDITED (item 1).
- `tests/test_app_composition.py:183-202`: EXTENDED (DR-84), plus Q16's case.
- `tests/test_gui_status.py:53-55` stays (S3 text is set only by the app's probe job).

### STOP items (choices the brief leaves open; recommended answer first)

- **S1 (the cache open; Q4 vs Q11/Q16/Q17 as ruled).** Q11/Q17 have `default_engines(locations=,
  cache_limit_bytes=)` open the cache when the engines are built, which is BEFORE `MainWindow` reads
  the settings, and on the main thread; Q4 moves the open off the interface thread when it is over
  100 ms, and it is (126 ms median warm; 16.4 s first open). **Recommended (a):** a deferred-open
  handle built by the root, `composition.proxy_cache_opener(folder)` (IF-7 plus `key_for`; every
  member waits for the open and is called on worker threads only; `open(limit_bytes)` once, by start-up
  job (i), with `session.settings().cache_limit_bytes`). `default_engines(*, locations=None)` uses it
  (the limit argument is dropped: the limit comes from the one settings read); `export_jobs(cache=)`
  accepts the handle or a `DiskProxyCache`; ONE `DiskProxyCache` per process. Grants: `composition.py`
  beyond Q16 (one class, one builder, the widened `cache=` type) and the Q11 signature change.
  **(b):** the open stays synchronous on the main thread before the window, as ruled; the limit from
  a second `load_settings` in `startup.py` before `MainWindow` (a corrupt file is then set aside before
  the log exists, so its warning misses the log file); the window appears after the open.
- **S2 (the adapter's backend).** Recommended: chosen once, at the adapter's first run (the engine
  holds it, WP3.18 mapping); a later force-CPU change applies from the next source or method change;
  every export selects its own. Alternative: rebuild the engine when the selection changes at a run.
- **S3 (`gui/shell.py` grant, Q5's named need).** One additive `MainWindow.set_idle_device(reason)`:
  `_update_status` shows `Device: <reason>` while no file is open (`Device: -` until it is set). No
  other shell change.
- **S6 (a journal that fails to decode).** Recommended: renamed aside as `write-journal.json.bad-<UTC
  stamp>` (as `settings_store` does), logged, treated as empty; the output folder is still scanned.
  Alternative: delete and recreate it.
- **S7 (the V7 / GX011627 window driver).** Recommended: an uncommitted driver in the evidence folder
  (md5 in the report) that imports the committed `tests/test_app_v7.py` helpers; no environment
  switch in a committed test (WP4.2 Reviewer B B1/B2 came from such a switch). Alternative: committed
  `footage` + `slow` tests, which the serial gate leg would run (against Q24).
- **S-order (Q4's "before `show()`").** The cleanup runs after `MainWindow(...)` (the folder set
  needs `Settings.output_folder` and the log needs `start_up`) and before the installs and `show()`;
  no job can start before it ends. Confirm.

### Ledger

| Round | Crit / maj / min | In-env / out | New / reopened | Reverts | Product vs test fixes | Transport, CLI | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|
| 0 (design) | - | - | - | - | none (no product code) | - | (to be given) |
