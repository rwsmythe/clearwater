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
| 0 (design) | - | - | - | - | none (no product code) | - | 263,162 at the round-0 yield (cell 1 retired; `scripts/cell_depth.py`) |
| build (tasks 3-10) | - | - | - | - | product + tests | - | 553,419 at the build yield (cell 2 retired PAST the ~400K stop: the whole build ran in one turn with no yield, so the dispatcher could not read it earlier) |
| R1 (Reviewer A, `038f02e..99da8aa`) | 0 / 5 / 11 | 16 in / 0 out (R1-5's reachability to be proven on the `main()` path) | 16 new / 0 reopened | 0 | none yet (adjudicating turn; proposed: product + tests) | WSL, codex-cli 0.162.1, `gpt-6.1-sol` high | 129,481 at the R1 yield (cell 3; `scripts/cell_depth.py`, given by the dispatcher in cell 4's dispatch) |

## CHARC round-0 ruling (`fcb2a9205c060013`, 2026-10-29 12:54:46Z, verbatim; it GOVERNS the STOP items above)

**CHARC RULING on WP4.3 round 0 (query d0a94cb7a23c5410; ledger 649483b `:199-229` read): six STOP items ruled; build goes to a FRESH cell 2 from the ledger and this post. Append this ruling to the ledger verbatim.**

**S1 the cache open: (a), the deferred-open handle, GRANTED, on five conditions.** The measured 126 ms warm and 16.4 s first open make Q4 bind, and (b) would leave the window blank for the first open, against G9/V7's intent. Grants: `composition.py` beyond Q16 (ONE class `proxy_cache_opener`-returned handle, ONE builder, the widened `cache=` type on `export_jobs`) and the Q11 signature (`default_engines(*, locations=None)`, the limit argument dropped). Conditions:
1. The handle implements IF-7 plus `key_for` by DELEGATION after open; the frozen interface is not touched, the handle lives in `app/composition.py`, and `tests/test_app_deps.py`'s rules still hold for it.
2. Every member blocks until the open completes and is called from worker threads only; an AST or monkeypatch test proves no member runs on the UI thread. If the open FAILED, every member refuses readably with the open's reason (the `_NoCacheFolder` form), never hangs or re-raises a traceback; the GUI shows that reason once (the settings dialog's existing banner or the status line), and the photo path keeps working.
3. The limit comes from the ONE settings read; `open(limit_bytes)` is called once by start-up job (i); a `set_limit_bytes` or `clear` from the settings dialog before the open completes is applied after it (queued), and a test drives that order.
4. ONE `DiskProxyCache` per process stays provable: `export_jobs(cache=<handle>)` and the adapter share the instance behind the handle; Q16's test holds through the handle, and `test_each_export_jobs_call_opens_its_own_cache` stands for the `cache_folder` form.
5. A V7 scenario with a slow open (a stub that sleeps past 100 ms) shows the UI responsive while the first job waits on the worker.

**S2 the adapter's backend: the ALTERNATIVE, rebuild at a run.** Selection happens at the START of each analysis or recompute run on the worker (DR-67's rule); an in-flight job keeps its backend (the AD-7 amendment's spirit: absorbed, never cancelled); when the selection differs from the engine's, the adapter rebuilds the `AnalysisEngine` over the SAME cache instance before the run (construction is light: no device work until a run). Ground: a user who sets force-CPU and presses recompute must see CPU in the AD-9 status on THAT run, not after a clip change; the cache entry is keyed independent of the backend (V4 CPU/GPU SAME, WP4.2 task 10), so a rebuilt engine reuses the entry. Test: toggle force-CPU between two runs of one clip; the second run's `JobResult.device` and the status line say CPU; the first run's statistics are reused.

**S3 `gui/shell.py` grant: GRANTED as named**: one additive `MainWindow.set_idle_device(reason)`, `Device: <reason>` while no file is open, `Device: -` until set; no other shell change.

**S6 a journal that fails to decode: CONCUR**, renamed aside as `write-journal.json.bad-<UTC stamp>` (the `settings_store` form), logged, treated as empty, the output folder still scanned; one test.

**S7 the V7 / GX011627 window driver: CONCUR**, an UNCOMMITTED driver in the evidence folder (md5 and command in the ledger and report) importing the committed `tests/test_app_v7.py` helpers; no environment switch in a committed test (the WP4.2 B1/B2 lesson); outputs under `work/`; no footage path in any log, record or report.

**S-order: CONFIRMED.** Leftover cleanup runs after `MainWindow(...)` (it needs `Settings.output_folder` and the log from `start_up`) and before the installs and `show()`; no job can start before it ends, and a test proves it (DR-35 (c)'s closure).

**Seat: FRESH cell 2 for the build, CONCUR** (cell 1 at 262,719 is past the evaluation point and the build is the main load). Cell 1's final report lands, then its STAND-DOWN. Cell 2 reads the ledger, this ruling and the brief, and builds tasks 3-12 with the round-0 names.

Start-up figures noted for the report: imports 1.46 s, capabilities 550 ms fresh / 4.9 ms cached, first `select_backend` 947 ms plus `import clearwater.core` 1.03 s on the worker, leftover cleanup 0.8 ms over 750 files. All measured under WP-T6's windows, so they are shape evidence; the V7 figures of record come from the exclusive window.

## RESUME HERE (cell 2; written by the dispatcher, generation 20, 2026-10-29)

- Cell 1 (`wp43-cell1`) did tasks 1 and 2 (round 0, `649483b`) and retired at 263,162 by the evaluation rule; its full report is `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\cell1-round0-return.md`; round-0 evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\r0\`.
- Cell 2 builds tasks 3-12 with the round-0 design table above AS RULED: S1 = (a) the deferred-open handle with its FIVE conditions; S2 = the ALTERNATIVE (select at each run start, rebuild the engine over the same cache); S3, S6, S7 and the order as recommended. No product code exists yet.
- Windows (V7 exclusive, the GX011627 legs) are requested by `WINDOW REQUEST`; the ONE two-leg gate is the orchestrator's after Reviewer A converged and Reviewer B returned.

## Build (cell 2, brief tasks 3-10; 2026-10-29)

Built on `49abe57` per the round-0 table AS RULED (S1 (a) with its five conditions, S2 rebuild at
a run, S3, S6, S7, S-order). Commits (all LF, ASCII, pathspec):

| Commit | Content |
|---|---|
| `b52b24a` | DR-52, DR-61: settings dialog on `resolve_encoder`, `catalog=`, erratum to the WP3.20 report |
| `802354c` | S1/Q16/Q11/Q17/DR-84: `DeferredProxyCache`, `export_jobs(cache=)`, `default_engines(*, locations=None)`, S1 stand-in deleted |
| `778d279` | Q18/Q3/Q8/Q22/S2/S6: `jobs.expected_frames`, `app/startup.py`, `app/activity.py`, `app/analysis_adapter.py` |
| `5fcb673` | DR-68/DR-75: worker chores, the plan release on `clearwater-preview`, `RenderRequest.display_icc` |
| `ab973c3` | Q2/Q4/Q5/S3/S-order/DR-35 (c)/DR-85 test: `app/main.py`, `__main__.py`, `set_idle_device`, `test_app_deps` |
| `426662f` | the G-matrix (`tests/test_app_wiring.py`) |
| `3a109de` | V8 and V18 on the shell; DR-75's REQUIRED test |
| `1681d43` | V7 gate forms (a)-(f); DR-44 (c) at close |
| `1a41abc` | DR-49's ground; the dialog's limit and clear queued behind the open |
| `8daaee7` | report draft |

Red-first: the DR-61 and DR-52 cases were run on the base dialog (6 failed, 3 passed by design);
DR-75's base rule is a permanent planted control (`test_dr75_the_base_display_rule_fails_the_required_test`);
DR-84's planted constructions; DR-68's planted controller without the release; the new modules
fail to import on the base.

Light run (touched files, their markers, the layering tests; NOT the gate; shared host):
`567 passed, 1 xfailed in 341.74s` (`C:\Users\rwsmy\clearwater-review-evidence\wp4.3\build\light1.txt`,
md5 `84b688123374d6f3c87d7f2b8cd51d60`); the xfail is DR-85's strict marker. ruff check, ruff
format --check, mypy strict (146 files): clean.

Decisions inside the ruled shapes (for Reviewer A to challenge):
- A journal that cannot be written is logged and the export goes on; the output folder is
  always scanned at start.
- DR-61 (iii): one dialog never presents the same error text twice until its save clears its
  banners (a per-window rule would break `test_every_message_of_the_dialog_is_ascii`).
- The cache-open failure is one `warning` (owner `startup`); every member then refuses with
  `the analysis cache could not be opened: <reason>`.
- The device probe selects for a 1 x 1 frame with the default method's estimate.
- The shared GUI fixture `make_app` lives in `tests/test_app_startup.py` (no unowned helper).
- DR-82's single routes use an NTFS stream source (Windows; skipped elsewhere), as WP4.2b did.
- DR-68's pre-preview figure is read after a warm pass (kernel loads are a one-time process
  cost); tolerance 2 MiB.

Flags: `gui/shell.py`'s module and `run` docstrings still say WP4.3 calls `run` (grant: the
device text only). The export panel prefixes a failure with the file name, so DR-82's banner
reads `<name>: <name>: this file name cannot be used ...` (the panel's form for every failure).
Two node IDs renamed with their edits: `test_app_deps.py::test_no_app_module_imports_the_gui_or_qt`
-> `::test_no_app_module_but_main_imports_the_gui_or_qt_and_none_imports_cupy`;
`test_gui_settings_dialog.py::test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule`
-> `::..._default_rule`.

## RESUME HERE (cell 3; written by the dispatcher, generation 20, 2026-10-29 ~14:05Z)

- Cell 2 (`wp43-cell2`) built brief tasks 3-10 (`b52b24a`..`307d1e6`, above) and retired at 553,419, past the ~400K stop. Its full build report: `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\cell2-build-return.md`; light run log `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\build\light1.txt`.
- Dispatcher QA at `307d1e6`: 11 commits, 29 files, 0 CR bytes in every changed blob; no file under `interfaces/`, `gui/contract.py`, `gui/analysis_service.py`, `jobs/export_seam.py`, `io/video/` or `config/` changed; `ruff check` clean, `ruff format --check` 280 formatted.
- Cell 3 runs the REVIEWER A loop (Codex `gpt-6.1-sol` / high, WSL, probe first; runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp4.2\r2\`; evidence `...\wp4.3\rN\`) to convergence under the five-round gate, yielding at every verdict BEFORE remediating. After it converges: the window requests (V7 (a)-(f) of record via the S7 driver, the GX011627 V18 leg, DR-44 (c) and DR-50 on real footage), the report's final figures, then the orchestrator's Reviewer B and the ONE gate.
- Cell 2's flags stand for Reviewer A to weigh: stale `gui/shell.py` docstrings (not granted); the doubled `<name>: <name>:` DR-82 banner (the panel's form); the two renamed node IDs.

## Reviewer A round 1 (cell 3, 2026-10-29; adjudicated, NOT remediated)

- Reviewed `038f02e..99da8aa` minus `docs/proofs` (28 files, 6,704 diff lines); probe first
  (`READY`, one `succeeded in`). Codex v0.162.1, `gpt-6.1-sol` / high, WSL, read-only; tokens
  206,419; 38 `succeeded in`; one VERDICT line. ERROR lines are client-side (model-list refresh
  timeouts, the MCP connector, a websocket connect with HTTP fallback), as in WP4.2 r1/B/B2.
  Withheld access checked on every command line: clean.
- Static checks at `99da8aa`: ruff check, ruff format --check (280), mypy strict (146): clean.
- **Verdict `NEW_CRITICAL_MAJOR_FOUND`: 0 critical, 5 major, 11 minor.**
  - R1-1 MAJOR: an invalid-UTF-8 journal escapes S6's set-aside (`startup.py:124`). Confirmed.
  - R1-2 MAJOR: the export runs when its journal entry cannot be recorded (`activity.py:226`);
    relaxes D85. Confirmed; proposed fix: fail the export readably.
  - R1-3 MAJOR: the entry is removed while a temporary remains, at the job's end
    (`activity.py:212`) and at start-up after a failed removal (`startup.py:230`). Confirmed.
  - R1-4 MAJOR: a CPU render overwrites the remembered GPU backend, so the boundary release skips
    the GPU plans (`preview.py:557`, DR-68). Confirmed.
  - R1-5 MAJOR (REASONED): start-up jobs (16.4 s first cache open, encoder detection) can outlive
    `SHUTDOWN_TIMEOUT_S`; their callbacks have no closed guard (DR-44 (c)). Reachability on the
    real `main()` path to be reproduced before the fix.
  - R1-6..R1-16 MINOR: chore/task ordering (6), a late retarget undone at publication (7), every
    adapter retained (8), `limit_bytes()` not refusing after a failed open (9), `idle()` during a
    chore (10), export after a release timeout (11), V7 workloads unwitnessed (12), V8 video leg
    without p99 (13), the S-order witness (14), the doubled DR-82 banner (15, ruling needed), the
    stale shell docstrings (16, ruling needed).
- Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\r1\` (prompt, diff, runner,
  test summary, static, probe, transcript, adjudication, `md5sums.txt`): review.txt
  `0af6db0a2fb4a1a8aa4c898832ace5fe`, review.stderr.txt `3896b453ffe47a788029022d8872cba8`,
  adjudication.md `365768b1d2d149c8cd0974014d761162`.
- Per-finding dispositions: `adjudication.md` in the evidence folder. Yielded to the dispatcher
  BEFORE any remediation.

## CHARC build ruling (`68d5b4c7a6a2fbc2`, 2026-10-29, verbatim; it GOVERNS cell 2's decisions and flags, items R1-15 and R1-16)


**CHARC on WP4.3 BUILD DONE and the depth breach (status d80c3b9be52d68c3): build evidence noted; the breach remedy is ADOPTED as a standing rule; five items for cell 3's Reviewer A loop and the single cleanup.**

**Depth breach, 553,419 in one turn.** Owned rightly by you, and the product's QA stands. The remedy is adopted as STANDING for every build dispatch from now: a build prompt names a yield after each task GROUP (three groups for an L package, two for an M), never "yield only at a window request or the end", so a depth reading falls inside the build and the ~250K evaluation and ~400K stop can act. I add one sentence to `docs/dispatch-recipe.md` (harness gate run) at my commit named in the cue; the ledger keeps the figure with its moment.

**Cell 2's decisions: CONCUR on all five** (journal write failure logged and the export proceeds; DR-61 (iii) per dialog; a failed cache open = one warning then refusals with the reason, as S1 condition 2 says; `make_app` in the test file; NTFS-stream sources for the DR-82 single-export tests) with ONE addition: the DR-82 route also gets a PORTABLE form, a monkeypatched `final_output_path` raising `OutputNameError`, so the wrapper's branch is proved on every OS and not only where NTFS streams exist (N1; the Windows form stays as the real-name proof).

**Cell 2's flags, dispositions:**
1. `gui/shell.py` module and `run` docstrings stale: GRANTED, docstrings only, in the cleanup (the text "this package has no entry point" is false once `app/main.py` exists).
2. The DR-82 banner `<name>: <name>: ...`: the wrapper's failed-item text drops the leading name, because the panel prefixes it; the test asserts the panel's final text once. Cleanup.
3. Two renamed node IDs: fine; the report's collection diff explains each removed ID (fill GATE_CHECKS), as WP-T6 does.
4. The early bare-cd slip: acknowledged, no action.

**Sequencing confirmed:** cell 3 Reviewer A R1 (Codex) on `038f02e..HEAD`, yield at the verdict; after convergence the windows (V7 of record via the S7 driver, the GX011627 V18 leg, DR-44 (c) / DR-50 on footage); Reviewer B; the ONE gate. The two gates (WP-T6, WP4.3) queue one at a time at your seat; WP-T6's first, since it changes the gate expressions WP4.3's gate should run under.


## CHARC R1 ruling (`d530b564a0b41b2b`, 2026-10-29, verbatim; it GOVERNS R1's dispositions)

**CHARC RULING on WP4.3 Reviewer A R1 (gen 20's rollover post 067199bfbdc95cad; verdict 0/5/11 on 038f02e..99da8aa, r1 md5 0af6db0a; ledger b4e5f17): major 2 REVERSED to fail-readably; majors 1, 3, 4, 5 as cell 3 proposes; the minors FIX; fresh cell 4 with mid-remediation yields. For gen 21.**

- **Major 2 (`activity.py:226`, the journal write failure): REVERSED.** My earlier concurrence (68d5b4c7) stands corrected by the reviewer's case: with no output folder set, an export whose journal entry could not be written leaves, on a crash, a temporary in the source's folder that no start-up scans, and D85 ("leftovers cleaned on next start") is then relaxed by the app's own choice. The export FAILS readably with nothing written, before any read or probe: the failed item names the journal's folder and says the export was not started because its clean-up record could not be written. A tightening, no owner item. Test: an unwritable journal folder (a file in its place under `tmp_path`) -> failed `JobResult` with that text, no temporary, no output; and the photo route the same.
- **Major 1 (`startup.py:124`, invalid-UTF-8 journal): FIX, test first**, inside S6's set-aside (the `.bad-<UTC>` rename covers decode AND encoding errors; the error class joins the tuple).
- **Major 3 (`activity.py:212` / `startup.py:230`, the entry dropped while a temporary remains): FIX as proposed**: the entry stays until that folder's cleanup has succeeded; a test crashes after the temporary is written and shows the next start removes it.
- **Major 4 (`preview.py:557`, force-CPU render overwrites the remembered GPU backend): FIX as proposed**, with the GPU -> CPU -> boundary test asserting the GPU plans release (DR-68's closure depends on it; `gpu` test).
- **Major 5 (`main.py:97`, start-up jobs outliving `SHUTDOWN_TIMEOUT_S`): as proposed**: reproduce on the real `main()` path first (a slow cache open plus an immediate close); then a closed-flag guard in `app/main.py`; `gui/jobs.py` is touched ONLY if a late delivery or an exit hang is shown, under the brief's conditional grant (question 8), and the report says which.
- **Minors 6-14: FIX** as cell 3 proposes; 15 and 16 are already ruled (68d5b4c7).
- **Seat:** fresh cell 4 from the ledger, with yields after each remediation group (the standing rule at e831448); the ledger carries fcb2a920, 68d5b4c7 and this post verbatim; then R2.

Gen 20's two late slips (bare cd into the memory folder; a heredoc CR caught before commit) acknowledged, no action. WP-T6 next = `w2b.sh` at gen 21's seat, then B, then its gate; WP4.3's gate after it; WP4.3a queued behind WP-T6's Codex cell.


## Remediation of R1 (cell 4, implementer-opus-high; 2026-10-29)

One line per finding: the finding, the commit, the test. Groups per the dispatch: A (journal and
start-up: R1-1, R1-2, R1-3, R1-9), B (preview and render: R1-4, R1-6, R1-7, R1-8, R1-10), C (the rest).

### Group A (the journal and start-up)

Red first on `ad855ed` (8 failed the right way: the `UnicodeDecodeError` escape, the dropped
entries, the export that ran, the 0 limit); green after. Targeted runs: `tests/test_app_leftovers.py`,
`test_app_activity.py`, `test_app_composition.py`, `test_app_startup.py`, `test_app_wiring.py`,
`test_app_analysis_adapter.py`, `test_app_preview_fft.py`, `test_app_v8_v18.py` and the layering
tests: 69 passed 1 xfailed (DR-85's strict marker) and 92 passed. ruff check, ruff format --check
(280), mypy strict (146): clean.

- R1-1 MAJOR, `1d0a3eb`: the journal is read as bytes and decoded inside S6's set-aside;
  `UnicodeDecodeError` joins the tuple. Test
  `test_app_leftovers.py::test_an_undecodable_journal_is_set_aside_and_read_as_empty[not-utf8]`
  and `[latin1-inside]` (the parameter became bytes; the five old ids kept).
- R1-2 MAJOR (REVERSED, d530b564), `c8574c9`: the journal entry is now step 2, right after DR-82's
  plan and before the cache wait, the key (a read of the source), the lock, the release and the
  engine; an `OSError` returns a failed `JobResult` "the export was not started because its
  clean-up record could not be written in <config_dir> (<reason>)." with nothing read or
  written. Test `test_app_activity.py::test_an_unwritable_journal_fails_the_export_before_any_read_or_probe[photo]`
  and `[video]` (default placement, a file in the config folder's place).
- R1-3 MAJOR, `1d0a3eb` (start-up) and `c8574c9` (job end): new `startup.holds_leftovers(folder)`
  (a temporary-named regular file present, or the folder unlistable; a missing folder holds
  none). The job's entry is removed only when its folder holds none; `clean_leftovers` drops only
  the entries of folders it left clean, and logs each one kept. Tests
  `test_app_activity.py::test_an_entry_stays_while_its_folder_holds_a_temporary[crash]` (a
  `BaseException` after the temporary is written) and `[locked]` (the job returns with its
  temporary left), each followed by the next start with no output folder removing it;
  `test_app_leftovers.py::test_a_folder_whose_clean_up_failed_keeps_its_entry_until_it_succeeds`.
- R1-9 MINOR, `80d7adf`: `DeferredProxyCache.limit_bytes` goes through `_target`, so it refuses
  like every member (no product caller reads it). Test
  `test_app_composition.py::test_a_failed_open_refuses_every_member_readably`; and
  `test_app_wiring.py::test_s1_a_limit_and_a_clear_from_the_dialog_during_the_open_apply_after_it`
  now checks the product's threads BEFORE its own main-thread limit read (that read now passes
  the `_target` spy).

Decisions for Reviewer A to challenge: a folder that no longer exists counts as clean (its entry
is dropped; an unplugged drive whose path then reads as missing loses its entry, and a temporary
on it stays until that folder is next an output folder); an unlistable folder keeps its entry.
The step order in `activity.py`'s docstring moved (journal before the lock and the release) as
the ruling's "before any read or probe" needs; the lock is now released before the entry is
removed. Slip: one bare `cd` at the end of a test-writing command (harmless no-op `true`), not
repeated.

Depth at the Group A yield: 140,559 (`scripts/cell_depth.py`, 47 turns; given by the dispatcher,
gen 21). Dispatcher QA at its seat: 5 commits, 0 CR bytes, owned files only; the wiring-test edit
accepted as test-only in an owned file. The report's Limits now carry the missing-folder rule and
its D85 meaning on a drive that comes back (dispatcher's request).

### Group B (the preview and render path)

Red first against the base product files (a scratch copy of the new ones, restored after): all
seven new tests failed the right way (the CPU render overwrote the device backend: no release;
`["task", "chore"]`; `idle()` True during a chore; the release queued after the new source's
render; the GPU plan count 6 after the boundary; the statistics of the old parameters; the first
adapter alive). Targeted run (`test_app_preview_fft` with its `gpu` tests, `test_app_analysis_adapter`,
`test_app_startup`, `test_app_activity`, `test_app_wiring`, `test_gui_preview`, `test_gui_threads`,
the layering and composition tests): 170 passed 1 xfailed, and 10 passed. ruff check, ruff format
--check (280), mypy strict (146): clean. Shared host (WP-T6's parallel leg running, no `gpu`).

- R1-4 MAJOR, `7f41d14`: `PreviewController._note_backend` remembers only a backend with the
  device extension, so a CPU render leaves the GPU one for the next boundary. Tests
  `test_app_preview_fft.py::test_a_cpu_render_after_a_device_render_keeps_the_device_plans_released`
  (recording backend, every OS) and `::test_force_cpu_after_a_gpu_render_still_releases_the_gpu_plans`
  (`gpu`: 1:1 4K on the FFT route, force CPU, CPU render, source change; readings plans 6 -> 6 -> 0,
  free 7,338,095,616 -> 7,388,270,080 bytes).
- R1-6 MINOR, `7f41d14`: `LatestWorker._run` takes the chores and the task in ONE critical
  section, chores first; the controller queues the release from `request()` on a source change
  (`_release_for_source`, once per source; `_on_source` calls it too for an unload), so it precedes
  the new source's first render although the session emits `image_changed` first. Tests
  `::test_a_chore_queued_after_the_worker_looked_still_runs_before_the_task` (a hooked condition
  queues a chore when the worker leaves a section with the task still waiting: red `["task",
  "chore"]` on the two-section loop; on the one-section loop no such exit occurs) and
  `::test_a_source_change_queues_the_release_before_the_new_sources_render`.
- R1-7 MINOR, `7a5828c`: `_complete` is set with `_phase = "post"` under the same locks, from the
  result, so a retarget after that point is not undone. Test
  `test_app_analysis_adapter.py::test_a_retarget_after_the_job_returned_is_not_undone_at_publication`
  (the run parked at the clip lock's release).
- R1-8 MINOR, `7a5828c`: `make_analysis_factory(on_built=)` replaces `built=`; `Application.analysis`
  (the latest adapter only, `keep_analysis`) replaces the `analyses` list; `Application` is now built
  before the installs (no side effect; the S-order is unchanged). Tests
  `test_app_startup.py::test_the_application_keeps_only_the_latest_analysis` (two clips, weakref
  dead after gc) and `test_app_analysis_adapter.py::test_the_factory_keeps_no_adapter_without_on_built`.
- R1-10 MINOR, `7f41d14`: `_busy` is True while chores run. Test
  `test_app_preview_fft.py::test_the_worker_is_busy_while_a_chore_runs`.

Line endings: `preview.py` and `render_worker.py` were CRLF in this worktree's checkout
(`core.autocrlf=true`); the edits normalised them to LF before the `autocrlf=false` commits; every
committed blob checked 0 CR, 0 non-ASCII.

Depth at the Group B yield: 219,999 (`scripts/cell_depth.py`, 96 turns, stable over two readings
70 s apart; given by the dispatcher, gen 21). Dispatcher QA: 3 commits, 0 CR, owned files only;
both deviations accepted.

### Group C (shutdown and the rest)

- R1-5 MAJOR, `24b3d87`. REPRODUCED FIRST on the real `main()` path (uncommitted driver
  `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\major5\repro_major5.py`, md5 `d94edd78767d30b2279bca3b3fb76de8`;
  a 12 s cache open, the close 0.3 s after the show; runs and `notes.txt` in that folder with
  `md5sums.txt`): the close returned after the 5 s `SHUTDOWN_TIMEOUT_S` wait, `app.exec()` with
  it, the process ended 0.33 s later (the open's daemon thread abandoned): NO exit hang past the
  timeout, NO late delivery after the loop; the probe's `on_done` was delivered INSIDE the close
  (the runner's designed delivery of ended jobs). So `gui/jobs.py` is NOT touched. Fix in
  `app/main.py`: `_CloseWatch` (an event filter noting the window's close event before the
  shell's shutdown) and `_UnlessClosed` (the window's runner whose `on_done`/`on_progress` are
  dropped once closed) carry all three start-up jobs, the catalog's completion included
  (`dataclasses.replace(window.context, jobs=...)`); `_on_settings` does not re-probe after the
  close. Test `test_app_startup.py::test_no_start_up_callback_reaches_the_window_after_its_close`
  (close wait made 0.2 s; red on the unguarded main: both callbacks delivered, the open's late
  through the test's running loop).
- R1-11 MINOR, `34cc899`: `PreviewController.release_device_plans(timeout_s | None, *,
  cancelled=)` queues the release once and waits in 50 ms slices; the wrapper's
  `release_device_plans(progress) -> bool` waits with no deadline and returns `CANCELLED` unwritten
  on a cancel, never selecting first (a stopped preview worker counts as released: it released at
  its stop). `PLAN_RELEASE_TIMEOUT_S` removed. Tests
  `test_app_activity.py::test_a_job_cancelled_while_waiting_for_the_plan_release_never_runs` and
  `test_app_preview_fft.py::test_the_release_wait_has_no_deadline_but_ends_on_a_cancel` (red on the
  base: the engine ran; the API had no cancel).
- R1-12 MINOR (test-only), `75a3e7a`: `Figures.witness`; (b) counts scrub moves during the analysis
  (37), (f) counts an analysis wait that began before the open ended and returned after it (1),
  (e) counts 1:1 renders of the photo while the export runs. (e) was 0 as written: the fixture
  export ended before the 4K render (the reviewer's point CONFIRMED), so (e) now ARRANGES the
  overlap (the export's encode waits for the 1:1 request; its job returns after a 1:1 render
  arrived): witness 1.
- R1-13 MINOR (test-only), `75a3e7a`: the video leg computes p99 at k = 2 beside the harness's
  mean (asserted equal): **p99 0.0392 (10/255) on the 320 x 180 fixture, OVER the 2/255 bound.**
  Cell 3's proposed fix ("assert p99 <= 2/255") cannot hold at fixture size: RECORDED and printed,
  NOT asserted; ruling asked at this yield. The report's V8 paragraph and Limits carry it.
- R1-14 MINOR (test-only), `75a3e7a`:
  `test_app_startup.py::test_the_cleanup_ends_before_any_panel_or_job` records `MainWindow`,
  the clean-up's start AND end, the four installs, `show`, then the three jobs.
- R1-15 MINOR (68d5b4c7 item 2), `0238c47`: `RENAME_TEXT` carries no name; the single test asserts
  the panel's final text `"<name>: this file name ...; rename the file."` exactly once; batch
  items carry the bare text under their label.
- Portable DR-82 form (68d5b4c7), `0238c47`:
  `test_app_wiring.py::test_g10_dr82_the_wrappers_refusal_on_every_os[photo]` and `[video]`
  (`activity.final_output_path` planted to raise `OutputNameError`; the engine never runs; nothing
  written); the NTFS-stream tests stay as the Windows real-name proof.
- R1-16 MINOR (68d5b4c7 item 1), `8ace451`: `gui/shell.py` module and `run` docstrings name
  `python -m clearwater` / `clearwater.app.main.main` as the entry point; docs only.
- The report's collection diff (68d5b4c7 item 3): a "Collection diff against `038f02e`" section
  lists the five removed node IDs (two renamed, three deleted) with reasons.

Targeted runs (shared host, after WP-T6's serial leg): `test_app_startup` 9 passed 1 xfailed;
activity/preview_fft/startup/wiring/deps 70 passed 1 xfailed (not gpu); V7/V8/startup 20 tests,
the two red cases above fixed or recorded, then 4 passed on the reworked cases; DR-82 9 passed;
gui/app deps, activity, wiring 54 passed. ruff check, ruff format --check (280), mypy strict
(146): clean at every commit.
