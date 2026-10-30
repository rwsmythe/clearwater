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
| R2 (Reviewer A, `038f02e..362a8b2`) | 0 / 3 / 6 | 9 in / 0 out | 8 new / 1 reopened (R2-9 = R1-12; the reviewer also tagged R2-1 as R1-3 and R2-3 as R1-5, adjudicated NEW: distinct paths, the R1 fixes hold) | 0 | R1 remediation (groups A-C): product + tests; R2 remediation (cell 5, groups A-C): product (startup, adapter, preview, render worker, main, settings_dialog under the 38a7c702 grant) + tests; R2-9 test-only | WSL, codex-cli 0.162.1, `gpt-6.1-sol` high | 316,716 at the Group C yield (cell 4, 156 turns; `scripts/cell_depth.py`); seat retired at 355,066 (cell 4 stood down after the R2 yield) |
| R3 (Reviewer A, `038f02e..028bc4f`) | 0 / 2 / 3 | 5 in / 0 out | 3 new / 2 reopened (R3-3, R3-4 = R1-12; the reviewer also tagged R3-1 as R2-2 and R3-2 as R1-3, adjudicated NEW: distinct routes, the earlier fixes hold) | 0 | R3 remediation (cell 6, groups A-B): product (`app/startup.py`: R3-1 `13c96f7`, R3-2 `099893a`) + tests; R3-3, R3-4, R3-5 test-only (`065f5f0`, `a0f43cd`) + the report's V7 rows and DR-44 (c) sentence | WSL, codex-cli 0.162.1, `gpt-6.1-sol` high | 222,999 at the Group C yield (cell 5, 109 turns; `scripts/cell_depth.py`); R3 adjudicated in the same seat; seat retired at 271,612 (cell 5 yielded R3 there and stood down). CHARC `d6e9abdf`: R3-2 RECLASSIFIED MINOR (counts now 0 / 1 / 4) |
| R4 (Reviewer A, `038f02e..5d8e0df`) | 0 / 0 / 2 | 2 in / 0 out | 1 new / 1 reopened (R4-1 = R3-5) | 0 | terminating-round cleanup (cell 6): test-only (R4-1 `a4b2d5a`, R4-2 `67a285a`) + the report's DR-44 (c) sentence and V8 paragraph | WSL, codex-cli 0.162.1, `gpt-6.1-sol` high (a websocket DNS failure before the model's first output: client-side, NOT disqualifying, the dispatcher's ruling, gen 22) | 110,453 at the Group A yield (cell 6, 45 turns), 172,926 at the Group B yield (88 turns; `scripts/cell_depth.py`, given by the dispatcher); R4 adjudicated in the same seat; 213,877 at the R4 yield (117 turns). CONVERGED: zero new blocking |
| R5 (Reviewer A, `1d96dc4..28c4ece`: the V7 remediation step, cell 9) | 0 / 3 / 4 | 6 in / 2 out (R5-2, R5-4 out of the one-window envelope) (cell dispositions; proposed RECLASSIFY R5-2 and R5-3 to MINOR, pending ruling) | 7 new / 0 reopened | 0 | NONE yet (blocking verdict: no change in the verdict turn); proposed: R5-1..R5-4 product (`app/main.py`), R5-5/R5-6 test-only, R5-7 docs-only | WSL, codex-cli, `gpt-6.1-sol` high, 85,061 tokens, clean | (dispatcher) |
| R6 (Reviewer A, `175a8e8..987681c`: the R5 remediation, cell 10; THE RE-RUN) | 0 / 1 / 3 | 3 in / 1 out (R6-1 out of V7's states, cell disposition, pending ruling) | 3 new / 1 reopened (R6-3 = R5-5; the reviewer tagged R6-1 as R5-1, adjudicated NEW: a distinct route, R5-1's fix holds for runner jobs) | 0 | R5 remediation (cell 10): product (`app/main.py`: R5-1 `e1a8599`, R5-2 `d13f84b`, R5-3 `4611ed6`, R5-4 `83af26f`, each after its RED) + test-only (R5-5/R5-6 `a3e73b5`, `987681c`) + docs (R5-7 `f9ea560`); R6 fixes NONE yet (blocking verdict: no change in the verdict turn) | WSL, codex-cli, `gpt-6.1-sol` high, 77,380 tokens, clean | (dispatcher) |

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

## Reviewer A round 2 (cell 4, 2026-10-29; adjudicated, NOT remediated)

- Reviewed `038f02e..362a8b2` minus `docs/proofs` (28 files, 7,625 diff lines) with a "THIS IS
  ROUND 2" section listing R1's 16 items and dispositions; probe first (`READY`, one `succeeded
  in`). Codex v0.162.1, `gpt-6.1-sol` / high, WSL, read-only; tokens 229,253; 76 `succeeded in`;
  one VERDICT line. ERROR lines client-side (model-list refresh timeouts, the MCP transport) plus
  one echoed source line. Withheld access checked on all 79 command lines: clean.
- Before the round: light run at `362a8b2` (the twelve touched test files with their markers,
  `gpu`/`gui`/`slow` included, plus the layering, thread and preview tests): 345 passed 1 xfailed
  in 215 s; ruff check, ruff format --check (280), mypy strict (146): clean.
- **Verdict `NEW_CRITICAL_MAJOR_FOUND`: 0 critical, 3 major, 6 minor.**
  - R2-1 MAJOR (EXEC): a journal READ `OSError` reads as empty and the next `add`/`drop` overwrites
    every retained entry (`startup.py` `_read`). Confirmed. FIX: no write after a failed read.
  - R2-2 MAJOR (EXEC): a journal folder containing a NUL character passes `_decode`; `os.scandir`
    raises `ValueError` and start-up crashes. Confirmed. FIX: reject it in `_decode` (S6 set-aside).
  - R2-3 MAJOR (REAS): the settings dialog's clear and limit jobs wait on the deferred open and can
    deliver an error to the closing window (`settings_dialog.py:737`, `:838`). Confirmed by reading.
    NEEDS A GRANT for `gui/settings_dialog.py` beyond Q1's items (STOP item), or BANK as narrow.
  - R2-4..R2-9 MINOR: Clear during an export fails the export (4, BANK recommended: WP3.20 gating);
    the adapter after Clear cannot recompute (5); unload leaves an old pending render to recreate
    plans (6); a chore accepted at the worker's exit is stranded (7); a second retarget reports
    True with a kept job pending (8); V7 (f)'s witness can race on a busy host (9, REOPENED R1-12).
- Per-finding table with the proposed fix and test for each: `adjudication.md`.
- Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\r2\` (prompt, diff, runner, test
  summary, static, probe, transcript, commands, adjudication, `md5sums.txt`): review.txt
  `d26c201b52231c3c675a2df9dc2225ea`, review.stderr.txt `8327bb308e5a865387571bbe88a81055`,
  adjudication.md `01d9e373cdf0f0fc64a5e6454232ef38`, review-prompt.md
  `b84174484ba220b8c7419e9271f7a3b7`, review-diff.txt `7eb9f5530b759cbda1eafdf7bce2916d`.
- Yielded to the dispatcher BEFORE any remediation (review-only turn). Remediation goes to a fresh
  cell from this ledger (cell 4 at 316,716 is past the evaluation point).

## CHARC R1-13 ruling (`ace08fbbb645c856`, 2026-10-29, verbatim; it GOVERNS R1-13 and the D85 missing-folder Limit, DR-89)

PRIMARY: CHARC. Ruling on query 60a471ec3c0db163 (WP4.3 R1-13), plus the D85 residual you flagged.

**R1-13 = (a). RULED.** AD-11 as amended 2026-10-21 says it outright: the k > 1 bound (p99 within 2/255 at k = 2) is set "on real-sized content (at least 1080p)", and "small stills and synthetic noise are outside V8's domain (a preview is a downscale of a real-sized image)". A 320x180 fixture frame is outside the domain, so a p99 of 10/255 there is a characterisation, not a V8 result, and asserting the bound on it would be asserting the wrong thing. Conditions:
1. The figure of record for the V8 VIDEO leg is the GX011627 window leg (already in WP4.3's window list): mean abs within 1/255 AND p99 within 2/255 at k = 2 ASSERTED there, on the real-size frame, with the figures in the report; p99.9 and max RECORDED.
2. The fixture-size p99 stays recorded and printed, and the report's V8 paragraph and Limits cite AD-11's domain sentence as the reason it is not asserted (not "the fixture is small", which invites a later reviewer to assert it anyway).
3. The accept record carries that sentence.
(b) is DECLINED for the reason you gave and the same AD-11 clause: a 1080p synthetic frame is still outside the domain, so a pass proves nothing and a failure is noise. No test after R2.

**D85 residual (the missing-folder rule) = Limit + register row, mine at the accept.** Reading: a folder that has vanished at start-up counts as clean and its journal entry is dropped; a temporary on a drive that was unplugged at that start is not removed when the drive returns, unless the folder is the output folder or a later export's destination; it stays visible as `.clearwater-partial`. That is a narrow residual of D85 / spec 8.4 ("leftover temporary files from a crash are cleaned up on the next start"), bounded (removable media, exactly one start without the drive), fail-safe (nothing deleted on a path whose folder cannot be proved, which is the right side of the N8 line), and user-visible by the suffix. ACCEPTED as a Limit for WP4.3; the alternative (keeping the entry until the folder is seen again) is major 3's keep-until-cleanup-succeeds rule extended to a missing folder, and I do not want it decided inside a remediation cell. R2 is asked to challenge it; if R2 shows a route where the folder is PRESENT and the entry is still dropped, that is a finding, not this Limit. Register row (DR-89, mine at the accept): trigger = the next touch of the leftover journal, or an owner report of a stale `.clearwater-partial`.

Noted and concurred: major 5 reproduced on the real main() path (delivery inside close(), 5 s shutdown timeout honoured, no exit hang), fix in app/main.py only, gui/jobs.py untouched; R1-11 cancellable release wait with the constant removed; R1-12 (e) rearranged to one witness; item 15 and the portable DR-82 form; the collection diff against 038f02e. R2 review-only in cell 4 at 316K, any remediation to a fresh cell: concurred.

FYI for your rebases: main moved by one docs-only commit of mine, 5e1fe8f (charc state), after your gate; nothing of yours is held. HOLD when you ask.

Owner-pending inputs: photos (WP3.6P), the iPhone clip (DR-15). Open owner decisions: none.


## CHARC R2 ruling (`38a7c702a4cae38a`, 2026-10-29, verbatim; it GOVERNS R2's dispositions)

PRIMARY: CHARC. Ruling on query 1e67098be8629740 (WP4.3 R2: R2-3 grant, R2-4 bank). Read at this seat on `wp4.3` 832360d: `gui/settings_dialog.py` `_on_clear_done` (:744-747) presents `_error` BEFORE its `_closed` check, and the limit job's `done` (:838-840) presents unconditionally; both block behind the S1 deferred open, which is this package's. The reading stands.

**QUERY 1 (R2-3, major) = GRANT, narrow. RULED.** `gui/settings_dialog.py` is already in the brief's question-1 grant for DR-52 / `catalog` / DR-61; this extends it by exactly ONE mechanism:
1. The two cache-job DONE callbacks (clear, limit) drop their error presentation when the MAIN window is closing, read from ONE closed signal the dialog can observe (the same signal R1-5's start-up callbacks read, not a second flag); the job itself still runs to its end and the result is still logged.
2. No other change to the dialog: Q1's gating (:730), `_clearing`, `_update_clear_button`, the RuntimeError branches stay as they are.
3. Test in R1-5's form in `tests/test_gui_settings_dialog.py`: a clear AND a limit queued behind a slow, FAILING open, the main window closed inside the wait, no error box presented, both results logged; RED before the fix. One further case: the same two jobs with the window NOT closing still present their error (the fix must not swallow the normal path).
4. Introduced-here is agreed (the wait is S1's handle), so it is not banked; it counts toward this package's remediation, not WP3.20's.

**QUERY 2 (R2-4, minor) = BANK. RULED.** A Clear during another clip's export fails that export readably with nothing partial written (D85/N8 hold); the alternative gates the dialog on the export and batch panels' state, which crosses files the brief does not own and is a design change to WP3.20's gating, not a remediation. Register row DR-90, MINE at WP4.3's accept: trigger = the next touch of the dialog's Clear gating (:730) or of the export/batch panels' cache coupling; remedy sketch = the activity guard (`app/activity.py`) exposes "an export is running" and the dialog refuses Clear while it is true. The report carries it as a Limit with the readable-failure sentence.

R2-1, R2-2 (majors) FIX as proposed, each RED-first; R2-1's "read failure makes add/drop raise with NO write" is the right side of D85 (never overwrite retained entries on a doubtful read). R2-5..R2-8 FIX in owned files; R2-9 FIX test-only. Concurred.

Cell 5 prompt also carries, as you listed: R1-13 condition 2 (the report's V8 paragraph and Limits cite AD-11's domain sentence) and the D85 missing-folder Limit with DR-89. Yields per task group (dispatch-recipe). Then R3 (round 3 of 5). Cell 4 stands down at 355K: concurred.

Owner-pending inputs: photos (WP3.6P), the iPhone clip (DR-15). Open owner decisions: none.


## Remediation of R2 (cell 5, implementer-opus-high; 2026-10-29)

One line per finding: the finding, the commit, the test. Groups per the dispatch: A (start-up and the
journal: R2-1, R2-2), B (the adapter, the preview and the worker: R2-5..R2-9), C (R2-3 under the grant,
R2-4 as banked, the report's R1-13 / AD-11 wording).

### Group A (start-up and the journal)

The two rulings went into this ledger verbatim first (`d49a25a`), before any code. Red first on
`d49a25a` (5 failed the right way: `add` returned with no raise over a locked journal; start-up
logged "could not be read" and never "could not be cleared"; the export's journal entry was
written over the retained one; the NUL folder decoded as an entry; `clean_leftovers` raised
`ValueError: scandir: embedded null character in path`); green after. Targeted run
(`test_app_leftovers`, `test_app_activity`, `test_app_startup`, `test_app_wiring` and the eight
layering tests): 140 passed 1 xfailed (DR-85's strict marker). ruff check, ruff format --check
(280), mypy strict (146): clean. Every committed blob 0 CR, 0 NUL, ASCII.

- R2-1 MAJOR, `b6ee84a`: `WriteJournal._read` raises an `OSError` other than the file's absence;
  `add` and `drop` (so `remove`) raise with NOTHING written; the export then fails readably with
  R1-2's text (its existing `OSError` branch, the reason naming the read error); start-up's
  `entries()` logs "could not be read" and reads empty, its `drop` raises and is logged "could not
  be cleared", and the file is kept byte for byte. Tests
  `test_app_leftovers.py::test_a_journal_that_cannot_be_read_is_never_overwritten`,
  `::test_a_start_up_over_an_unreadable_journal_logs_and_keeps_it` and
  `test_app_activity.py::test_a_journal_that_cannot_be_read_fails_the_export_and_keeps_its_entries`
  (a planted `Path.read_bytes` denial of the journal path only).
- R2-2 MAJOR, `b6ee84a`: `_decode` rejects a folder the operating system refuses as a path
  (`_is_path`: a NUL character; also a string `os.fsencode` cannot encode, which is POSIX's other
  `ValueError` from `os.scandir` on a lone surrogate; on Windows that string is a missing path, so
  only the NUL case is executable here), so S6 sets the file aside; `holds_leftovers` catches
  `ValueError` beside `OSError` (unlistable: the entry stays). Tests
  `test_app_leftovers.py::test_an_undecodable_journal_is_set_aside_and_read_as_empty[nul-folder]`
  and `::test_a_journal_folder_the_os_refuses_lets_the_start_up_proceed` (the output folder still
  scanned; the file set aside; `holds_leftovers` True on the NUL path).

Decision for Reviewer A to challenge: R2-1 and R2-2 share one commit (one file, one read path).
A set-aside rename that itself fails still lets `add` write a fresh journal over the undecodable
file (S6's "treated as empty", unchanged). Slips: one bare `cd` into the session temp folder in a
probe command (a no-op for the repo; not repeated); one heredoc collapsed `\x00` to a literal NUL
byte in `startup.py`, caught by a NUL-byte check before any commit and repaired by a script
written with the Write tool.

Depth at the Group A yield: 108,533 (`scripts/cell_depth.py`, 40 turns; given by the dispatcher,
gen 21). Dispatcher QA: 3 commits, owned files only, 0 CR and 0 NUL in every blob; the shared
R2-1/R2-2 commit accepted; both slips noted with their fixes.

### Group B (the adapter, the preview and the worker)

Red first on `6773070` (the four product tests failed the right way: the second retarget returned
True with a kept job waiting; the recompute after `cache.clear()` raised `RuntimeError: KeyError:
'nothing is cached for CacheKey(...)'`; `run_chore` returned True at the worker's exit point; the
unload ran the old render after the release, order `['release', 'render']`); green after.
Targeted run (`test_app_analysis_adapter`, `test_app_preview_fft` with its `gpu` tests,
`test_gui_preview`, `test_gui_threads`, `test_app_startup`, `test_app_activity`, `test_app_wiring`,
`test_app_leftovers` and the eight layering tests): 237 passed 1 xfailed, 0 skipped; V7 (f) alone:
1 passed, then 3 more passes of it 3.6 s each (witness 1; longest 57.0 ms, p99 11.0 ms on a shared
host, shape only). ruff check, ruff format --check (280), mypy strict (146): clean. Every committed
blob 0 CR, 0 NUL, ASCII.

- R2-5 MINOR, `ca76904`: `_engine_for` also rebuilds when the engine has run (phase not `none`)
  and `cache.lookup(key)` is None or not complete (`_entry_lost`; a cache read error is not taken
  as a loss); logged. Test
  `test_app_analysis_adapter.py::test_a_recompute_after_the_cache_was_cleared_decodes_again`
  (the second engine decodes all 24 frames, completes at the new strength; a third run over the
  complete entry builds no engine).
- R2-8 MINOR, `ca76904`: `retarget` returns False and clears completion whenever a kept job waits
  after `set_parameters` (the kept job still absorbs the parameters). Test
  `::test_a_second_retarget_while_a_kept_job_waits_is_false` (the next run ends at the second
  retarget's strength).
- R2-6 MINOR, `7ed51ab`: `PreviewController._on_source` invalidates the renderer and clears the
  full-render indicator before it queues the release. Test
  `test_app_preview_fft.py::test_an_unload_drops_the_old_sources_pending_render` (a render waits
  behind a blocked task; `session._open(None)`; order `['release']`). Note: no product path
  unloads today (`shell._on_opened` never opens None); the test drives the session as the
  reviewer's probe did.
- R2-7 MINOR, `7ed51ab`: `LatestWorker._ended` is set in the section that decides the end (and in
  a `finally` around the loop, `_run` -> `_loop`); `run_chore` refuses when it is set (it replaces
  `_stopping and not is_alive()`). Test
  `::test_a_chore_offered_after_the_worker_decided_to_end_is_refused` (`_ExitHold` parks the
  worker just after it leaves its last section; `run_chore` then returns False, nothing stranded).
- R2-9 MINOR (test-only, REOPENED R1-12), `7f7d60b`: the stub open waits on an event the
  witnessed wait sets (cap 30 s), then sleeps 150 ms, so the wait is real and over 100 ms. Red
  proof of the old form (uncommitted scratch test, the analysis's run planted 2 s late): old form
  FAILED with witness 0, new form passed. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\c5-r2-9\` (`test_zz_c5_r29_scratch.py` md5
  `2896a6104102517d2a56836f10f55109`, `r29-red.txt` `3c9cb7d71a553cd5a5de2ecd58b16da4`); the scratch
  file was removed from `tests/` after the run.

Decisions for Reviewer A to challenge: R2-5 also rebuilds after a cancelled or failed decode (the
entry incomplete; the old engine would have started a fresh `analysis_job` anyway, so the result
is the same); R2-9 sleeps AFTER the event rather than before it, so the analysis's wait itself is
longer than 100 ms (the adjudication's "after a >= 150 ms sleep" read for both properties).

Depth at the Group B yield: 168,297 (`scripts/cell_depth.py`, 78 turns; given by the dispatcher,
gen 21). Dispatcher QA: 4 commits, owned files only, 0 CR and 0 NUL in every blob; the three
choices for R3 to challenge noted.

### Group C (R2-3 under the grant, R2-4 as banked, the report's wording)

Red first on `9831074`: `test_gui_settings_dialog.py::test_cache_job_errors_are_not_presented_once_the_main_window_closes[window-closing]`
failed the right way (both errors presented on the closed window: "The cache could not be
cleared: RuntimeError: the analysis cache could not be opened: the cache volume is not mounted"
and the limit's), `[window-open]` (the control) passed; both green after. Targeted run
(`test_gui_settings_dialog`, `test_app_startup`, `test_app_wiring`, `test_app_leftovers` and the
eight layering tests): 218 passed 1 xfailed, 0 skipped. ruff check, ruff format --check (280),
mypy strict (146): clean. Every committed blob 0 CR, 0 NUL, ASCII.

- R2-3 MAJOR (GRANT, narrow, 38a7c702), `be73495`: the ONE closed signal is
  `Application.closed` (the `_CloseWatch` the start-up callbacks read, R1-5). It reaches the dialog
  within the grant: `install_settings_dialog(..., window_closing=)` -> `settings_dialog` ->
  `SettingsDialog` (one optional argument, never closing when None), and `build_application`
  (owned `app/main.py`) now creates the watch before the dialog's install and passes
  `application.closed`; `start_jobs` keeps the watch it finds. In the dialog, ONLY the clear's
  `_on_clear_done` and the limit's `done` changed: their error goes through `_cache_job_error`,
  which logs it (`"<text> (not shown: the window is closing)"`, WARNING, `clearwater.gui.settings_dialog`)
  and presents nothing while the window is closing, else presents it as before. The jobs still
  run to their end (the runner also logs "job failed"). Q1's gating, `_clearing`,
  `_update_clear_button` and the RuntimeError branches are unchanged. Test (R1-5's form, the real
  `build_application`): a slow FAILING open, a Clear (confirmed) and a limit change (OK) queued
  behind it, `SHUTDOWN_TIMEOUT_S` 0.2 s; `[window-closing]` closes the main window inside the
  wait: no settings error presented, both texts in the log; `[window-open]`: both errors presented.
- R2-4 MINOR, BANKED as DR-90 (38a7c702; CHARC writes the row at the accept): the report's
  Limits carry "A Clear during another clip's export fails that export readably, with nothing
  partial written", and the DR table names DR-90. No code.
- R1-13 condition 2 (ace08fbb), `e3d8901`: the report's V8 paragraph and Limits cite AD-11's
  domain sentence ("on real-sized content (at least 1080p)"; "small stills and synthetic noise are
  outside V8's domain") as the reason the fixture-frame p99 is recorded, not asserted, and name
  the GX011627 window leg as the asserted figure of record; the "ruling asked" phrase is gone.
- DR-89 confirmed: the D85 missing-folder Limit names DR-89 with its trigger; the DR table names
  DR-89 and DR-90 as CHARC's rows at the accept. The report's Limits also gained R2-1's read
  failure and R2-3's close behaviour.

Slip: an empty `python - <<'EOF'` left a stray interpreter waiting on stdin (moved to the
background by the tool's timeout); I killed that one process (my own, PID-checked; the WP4.3a
Codex turn untouched). A heredoc with nested quotes failed to parse; the edit script was written
with the Write tool instead (nothing applied by the failed command).

Depth at the Group C yield: 222,999 (`scripts/cell_depth.py`, 109 turns; given by the dispatcher,
gen 21). Dispatcher QA: 3 commits, 0 CR and 0 NUL; the `settings_dialog.py` diff within the narrow
grant; the process kill noted.

## Reviewer A round 3 (cell 5, 2026-10-29; adjudicated, NOT remediated)

- Reviewed `038f02e..028bc4f` minus `docs/proofs` (28 files, 8,077 diff lines) with a "THIS IS
  ROUND 3" section listing R1's 16 and R2's 9 items with their dispositions and the rulings
  `d530b564`, `ace08fbb`, `38a7c702`; probe first (`READY`, one `succeeded in`). Codex v0.162.1,
  `gpt-6.1-sol` / high, WSL, read-only; tokens 219,702; 25 `succeeded in` (28 exec blocks); one
  VERDICT line. ERROR lines client-side (model-list refresh timeouts, the MCP transport) plus two
  echoed source lines. Withheld access checked on all 28 command lines and the whole transcript:
  clean (`docs/proofs` only inside the matching `'!docs/proofs/**'` glob).
- Before the round: light run at `028bc4f` (the twelve touched test files with their markers plus
  the layering, thread and preview tests): 356 passed 1 xfailed in 230 s; ruff check, ruff format
  --check (280), mypy strict (146): clean.
- **Verdict `NEW_CRITICAL_MAJOR_FOUND`: 0 critical, 2 major, 3 minor.**
  - R3-1 MAJOR (EXEC): a settings file whose `output_folder` holds a NUL loads, and start-up's
    `clean_leftovers` raises `ValueError` before `show()`: the program cannot start. CONFIRMED on
    the Windows side by the cell's probe. FIX in `app/startup.py` (skip and log a folder `_is_path`
    refuses); FLAG for CHARC: the settings store accepts it at its source (`config/`, WP4.3a's).
  - R3-2 MAJOR (EXEC): two journal entries with one id; a failed clean-up of one folder still drops
    both (`drop` by id). CONFIRMED by probe (entries `()` after "keeps ...\a"). Reachable only via a
    journal the program did not write (uuid4 ids); impact a lost record (a stale visible
    `.clearwater-partial`, the DR-89 class); MAJOR kept under R2-2's corrupt-journal precedent unless
    CHARC reclassifies. FIX: entry-level removal (recommended) or reject duplicate ids under S6.
  - R3-3 MINOR (EXEC, REOPENED R1-12): V7 (e)'s witness proves the wrapper running, not the encode
    overlapping a k = 1 render. FIX test-only.
  - R3-4 MINOR (REAS, REOPENED R1-12): V7 (b) counts slider moves, not proxies shown. FIX test-only.
  - R3-5 MINOR (REAS): the DR-44 (c) close test's predicates do not prove "mid-decode" /
    "mid-encode"; the report sentence overstates them. FIX test-only plus one report sentence.
- Per-finding table with each fix and test: `adjudication.md`.
- Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\r3\` (prompt, diff, runner, test
  summary, static, probe, transcript, commands, adjudication, the cell's probes, `md5sums.txt`):
  review.txt `21392d7604318b6bd4f884b0d99d00d6`, review.stderr.txt
  `7572c24ad1d58099c0c9446502cd9998`, adjudication.md `abf49f67be7f00be20f2b52df287bdd4`,
  review-prompt.md `154fed6b2262ec8ad8e9ebfe1d5839ce`, review-diff.txt
  `846af4619ce41919d263948d70e3b7e2`.
- Five-round gate: round 3 of 5; two NEW in-envelope majors whose fixes change product code, so
  the loop continues after remediation (R4). Yielded BEFORE any remediation (review-only turn).

## CHARC R3 ruling (`d6e9abdfa16feb0e`, 2026-10-29 17:03:59Z, item 1 verbatim; it GOVERNS R3's dispositions)

**1. WP4.3 R3 (round 3 of 5).**
- **R3-1 MAJOR = FIX in BOTH places, RULED.** (i) WP4.3 cell 6, `app/startup.py`: `clean_leftovers` skips and logs any folder `_is_path` refuses (the output folder included) and never raises before `show()`; RED-first on a NUL `output_folder`. This is defence in depth and stays whatever the source does. (ii) **Scope addition to WP4.3a, GRANTED:** in `config/settings_store.py`, an `output_folder` (and any other path-valued field) that cannot be a path (NUL, or `Path()` raising `ValueError`) is treated like an out-of-range field by the EXISTING per-field rule (`_clamp`, :129: replaced by its default with one warning), NOT a whole-file set-aside: the file is well-formed, one value is unusable, and the user's other settings survive. One decode check + one RED-first test in `tests/test_config_settings.py` (owned). Codex seat 2 folds it into the R1 remediation turn; it is the DR-85 sibling in spirit ("a settings file cannot stop the program from starting") and the brief's register table gains one line. Banking it is DECLINED: the startup skip alone leaves a silently ignored output folder with no warning at the source.
- **R3-2 = FIX by the (id, folder) pair, RULED; severity MINOR.** Reachable only through a journal the program did not write (uuid4 ids); R2-2's precedent was a CRASH on a foreign journal, this is a lost record on one; the work is the same. The adjudication table records the reclassification and why.
- **R3-3, R3-4 (reopened R1-12) = FIX test-only:** V7 (e)'s witness must prove an encode OVERLAPS a 1:1 render and check `result.k`; V7 (b) counts proxies shown during the analysis, not slider moves. This is the second reopen of R1-12: cell 6's prompt quotes the V7 scenario text verbatim beside each witness so the witness is derived from the scenario, not the implementation.
- **R3-5 = FIX test-only** + the report sentence at `:100`; "mid-decode" / "mid-encode" are proved by a predicate on the source's or sink's progress at the close, not by timing.
- Seat: fresh cell 6 from the ledger; Group A (R3-1, R3-2) yield, Group B (R3-3..R3-5) yield, then R4 review-only. Concurred. R4 is round 4 of 5; if R4 finds a NEW major, the fill's re-seat line applies and I want the R4 verdict before any Group is dispatched.

Item 2 of the same post rules WP4.3a's R1 (F1-F9, the F4 grant); it exists and is not this cell's.

## Remediation of R3 (cell 6, implementer-opus-high; 2026-10-29)

One line per finding: the finding, the commit, the test. Groups per the dispatch: A (start-up and the
journal: R3-1, R3-2), B (the witnesses: R3-3, R3-4, R3-5 and the report sentence at `:100`).

### Group A (start-up and the journal)

The ruling went into this ledger verbatim first (`314dc92`), before any code. Red first on
`314dc92` (3 failed the right way: `clean_leftovers` and `make_app` raised `ValueError: scandir:
embedded null character in path` from `safe_write.py:354`; the duplicate-id journal read `()`
after "keeps ...locked"); green after. Targeted run (`test_app_leftovers`, `test_app_activity`,
`test_app_startup`, `test_app_wiring` and the eight layering tests, `gui` included): 143 passed
1 xfailed (DR-85's strict marker) in 90 s. ruff check, ruff format --check (280), mypy strict
(146): clean. Every committed blob 0 CR, 0 NUL, ASCII. Logs under `work/wp4.3-c6/`.

- R3-1 MAJOR, `13c96f7`: `clean_leftovers` skips every folder `_is_path` refuses (the output
  folder included) with one warning naming it (`%r`, so the NUL prints as `\x00`), and the
  journal's folders are still scanned and cleared; nothing raises before `show()`. Tests
  `test_app_leftovers.py::test_an_output_folder_the_os_refuses_is_skipped_and_logged` (the bad
  `Settings` built directly) and `::test_a_settings_file_with_an_output_folder_the_os_refuses_still_starts`
  (`gui`: a saved settings file edited to a NUL `output_folder`, start-up through `make_app`; it
  asserts only what holds under either store: the window shows, the journal's planted temporary is
  removed, the journal is cleared).
- R3-2 MINOR (reclassified, CHARC `d6e9abdf`: reachable only through a journal the program did
  not write, uuid4 ids; a lost record, not a crash), `099893a`: `WriteJournal.drop` takes the
  `(id, folder)` pairs `entries()` returns; `remove(entry_id)` keeps the by-id rule (one private
  `_keep_only` under the lock for both). Test
  `test_app_leftovers.py::test_entries_sharing_an_id_are_cleared_folder_by_folder` (the probe's
  form, the first folder's unlink refused by a planted `os.unlink`, portable): the locked folder's
  entry remains, the clean folder's goes. The R2-1 test's `drop` call now passes a pair.

Decision for Reviewer A to challenge: `drop`'s argument changed from ids to pairs (its only
product caller is `clean_leftovers`). R3-1 and R3-2 are two commits (the shared file split by
content). Slip: one bare `cd` into the worktree at the start of a ledger-edit command (the tool
resets its directory; `pwd` checked afterwards: the main tree); not repeated. A second slip: the ledger
commit `031379a` carried one NUL byte (a heredoc collapsed a doubled backslash), caught by a
post-commit check and replaced by its escape text in the next commit (a Write-tool script).

Depth at the Group A yield: 110,453 (`scripts/cell_depth.py`, 45 turns; given by the dispatcher,
gen 22). Dispatcher QA on `badece4`: the `startup.py` diff read (pair `drop` consistent with
`entries()`, `remove` by id via `_keep_only`, the skip before `remove_leftovers`); every changed
blob since `21ba03f` 0 CR and 0 NUL; the R3 row reads 0 / 1 / 4.

### Group B (the witnesses)

Test-only, each witness derived from the scenario text quoted verbatim in its docstring (spec V7,
spec section 487; brief question 10 (b), (e) with (a), (c)). Each new witness was shown to
distinguish by an UNCOMMITTED mutation run (temporary file `tests/test_zz_cell6_mutation.py`,
deleted after the run; log `work/wp4.3-c6/mut.txt`): (b) with `EngineClipAnalysis.proxy` refusing
every pts, the witness read 0 and `_within` failed; (e) with the preview never asking for k = 1
(`needed_factor` held at 2 or more), no k = 1 render arrived, the held write's guard failed the
export ("no 1:1 render arrived during the sink's write") and the scenario timed out. R3-5's
predicates: the same test with no hold and a 5 s wait before the close read `at close [False]`
for the analysis and the export, which failed (`dr44-mut.txt`). Targeted run (`test_app_v7`,
`test_app_wiring`, the eight layering tests; `gui` and `slow` included): 99 passed in 144 s.
ruff check, ruff format --check (280), mypy strict (146): clean. Every committed blob 0 CR, 0 NUL,
ASCII.

- R3-3 MINOR (REOPENED R1-12, second reopen), `065f5f0`: V7 (e)'s export sink (`_HeldSink`, put in
  through the engine's `_sink_for`) holds its first `write` in progress after the frame is
  written until a render of the photo with `result.k == 1` has been delivered; the 1:1 view is
  asked for only once that write has begun; `k1_renders_during_a_sink_write` counts only k = 1
  renders delivered while that write has not returned. Gate form: 57.0 / 24.0 ms, 1,491 ticks,
  witness 1. Test `test_app_v7.py::test_v7_c_e_export_and_a_full_render_during_it`.
- R3-4 MINOR (REOPENED R1-12, second reopen), `065f5f0`: V7 (b) counts the proxies the preview
  widget displays (`set_proxy`, an instance wrapper calling the real method) while the analysis
  phase is `running`; the slider moves only drive the scrub. Gate form: 22.0 / 18.0 ms, 256
  ticks, `proxies_shown_during_analysis` 62. Test
  `test_app_v7.py::test_v7_a_b_analysis_and_scrubbing`.
- R3-5 MINOR, `a0f43cd`: the DR-44 (c) close test wraps the analysis's frame source (through
  `build_application`'s `engine_factory`) and the export's sink (`_sink_for`); each holds its job
  after the first frame until the first job runner's `close` begins, where the predicate is read
  and asserted: the iterator has advanced and not ended (analysis); the sink is open, has written
  a frame, and neither its close nor its abort has begun (export). The batch item's state is
  printed, not asserted (unchanged scope). Figures: analysis 46 ms, export 18 ms, batch 28 ms
  (were 17 / 10 / 23 ms unheld). The report sentence (`:100`, now `:104-109`) states exactly what
  the predicates prove. Test `test_app_wiring.py::test_dr44c_a_real_job_ends_within_the_shutdown_timeout_at_close`.

Beyond the named sentence: the report's V7 table rows (a), (b), (c), (e) and the witness paragraph
were also updated (`065f5f0`), since rows (b) and (e) named the old witnesses ("scrub moves", "1
render at 1:1 during the export") and the paragraph described the old arrangement; (d) and (f)
keep cell 4's figures. Open for the window: the S7 driver (not yet written; ruling S7) will import
these scenario functions; the witness keys they return are now
`proxies_shown_during_analysis` and `k1_renders_during_a_sink_write`.

Decision for Reviewer A to challenge: the holds (V7 (e)'s write, R3-5's frame and write) are
deterministic arrangements, released by the delivered render or by the close itself, never by a
timer; the R3-5 hold shifts the measured close figures (the job resumes from its hold as the
close begins), and the figures of record stay the exclusive window's.

Depth at the Group B yield: 172,926 (`scripts/cell_depth.py`, 88 turns; given by the dispatcher,
gen 22). Dispatcher QA on `5d8e0df`: `badece4..HEAD` touches only `tests/test_app_v7.py`,
`tests/test_app_wiring.py`, the report and the ledger (no product code); 0 CR in every blob; both
V7 docstrings carry the spec V7 and Q10 (b)/(e) text verbatim; the mutation runs stand as the
distinguishing evidence. The report's V7 rows (a), (b), (c), (e) and the witness paragraph:
APPROVED by the dispatcher (in scope: the report stays true to the witnesses).

## Reviewer A round 4 (cell 6, 2026-10-29; adjudicated, NOT remediated)

- Reviewed `038f02e..5d8e0df` minus `docs/proofs` (28 files, 8,359 diff lines) with a "THIS IS
  ROUND 4" section listing R1's 16, R2's 9 and R3's 5 items with their dispositions (R3-2 MINOR per
  `d6e9abdf`), the round-3 remediation decisions (the `drop` signature from ids to pairs; the
  deterministic holds) and the report's updated V7 rows named for checking; probe first (`READY`,
  one `succeeded in`). Codex v0.162.1, `gpt-6.1-sol` / high, WSL, read-only; tokens 311,492; 23
  `succeeded in` (23 exec blocks, 0 exited); one VERDICT line. ERROR lines client-side: two
  model-list refresh timeouts, the MCP transport, and NEW in this arc one websocket connect failure
  (DNS lookup) at 17:40:58Z before the model's first output, after which the session ran to its end
  (classified not disqualifying; flagged to the dispatcher). Withheld access checked on all 23
  command lines and the transcript: clean (`docs/proofs` only inside the matching
  `'!docs/proofs/**'` glob; the only evidence file read is `r4/test-summary.txt`).
- Before the round: light run at `5d8e0df` (the twelve touched test files with their markers plus
  the layering, thread and preview tests): 359 passed 1 xfailed in 315 s; ruff check, ruff format
  --check (280), mypy strict (146): clean.
- **Verdict `NO_NEW_CRITICAL_MAJOR`: 0 critical, 0 major, 2 minor.**
  - R4-1 MINOR (EXEC, REOPENED R3-5): `_ProgressSource.ended` is set only on normal exhaustion, so
    an iterator the engine closes after frame 1 (a processing failure) still reads `mid_decode()`
    True. CONFIRMED by the cell's probe (`r4_probe.txt`: `ended: False`, `mid_decode ... True`).
    Introduced by `a0f43cd`. FIX test-only: `ended` in a `finally`, plus the analysis phase
    `running` in the predicate; a pure-Python unit test of the helper.
  - R4-2 MINOR (REAS, NEW): the V8 photo legs omit AD-11's p99.9 characterisation ("p99.9 and max
    are RECORDED as characterisation, never a V8 bound"); `_v8_photo` returns mean, p99, max only
    and the report has no p99.9. CONFIRMED by reading. FIX test-only plus the report's V8 paragraph;
    the GX011627 window leg records p99.9 too (open item for the window driver). Result-bearing:
    named in the accept record.
- Per-finding table with each fix and test: `adjudication.md`.
- Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\r4\` (prompt, diff, runner, test
  summary, static, probe, transcript, commands, adjudication, the cell's probe, `md5sums.txt`):
  review.txt `d1a9182d3c66b1a5bc51b02c038a2139`, review.stderr.txt
  `c0100aa66cb4e615f2b477a0b8993cf9`, adjudication.md `738ad81bcd556d4b90acaa760df9ae0c`,
  review-prompt.md `d1a61609381fbead69ac767bcbb74c6a`, review-diff.txt
  `3fe4f0cc7954472e042ad7fef9cc741b`.
- Five-round gate: round 4 of 5. ZERO new blocking findings: by the fill's CONVERGENCE_CRITERION
  Reviewer A's loop TERMINATES here; R4-1 and R4-2 are fixed once in the terminating round's
  cleanup and open no further round. Yielded BEFORE any remediation (review-only turn).

Depth at the R4 yield: 213,877 (`scripts/cell_depth.py`, 117 turns; given by the dispatcher, gen
22). Dispatcher ruling on R4: ACCEPTED as adjudicated, Reviewer A CONVERGED at round 4 (0 / 0 / 2);
the 17:40:58Z websocket DNS failure CONFIRMED client-side and not disqualifying (before the model's
first output; the session ran to completion: 23 executions, the token footer, one VERDICT). R4-1
and R4-2 FIX in the terminating round's cleanup, one turn, no further round.

### Terminating-round cleanup (R4-1, R4-2)

Test-only plus the report. Targeted run (`test_app_wiring`, `test_app_v8_v18`, the eight layering
tests; `gui`, `slow` and `gpu` markers they carry included; a stacked accept gate was running on
the host): 103 passed in 188 s. ruff check, ruff format --check (280), mypy strict (146): clean.
Every committed blob 0 CR, 0 NUL, ASCII. Logs under `work/wp4.3-c6/` (`red-c.txt`, `green-c.txt`,
`v8.txt`, `static-c.txt`).

- R4-1 MINOR (REOPENED R3-5), `a4b2d5a`: `_ProgressSource.frames` sets `ended` in a `finally` (run
  out, closed or raised); the analysis predicate also requires the session's analysis phase to be
  `running` when the close begins. RED first: the new pure-Python unit test
  `test_app_wiring.py::test_the_progress_source_has_ended_once_its_iterator_closes_or_runs_out`
  failed on the old helper (`assert not True` from `mid_decode()` after `close()`), green after
  (it carries the module's `gui` marker; it starts no window). The close test
  `::test_dr44c_a_real_job_ends_within_the_shutdown_timeout_at_close` passes with the new
  predicate: analysis 52 ms, export 33 ms, batch 39 ms, `at close [True]` (shared host, the gate
  running); the report's DR-44 (c) sentence names the phase and these figures.
- R4-2 MINOR (NEW), `67a285a`: `_v8_photo` returns (mean, p99, p99.9, max); p99.9 and max are
  printed, never asserted (AD-11 as amended). Figures: smooth scene k = 2 p99.9 0.00796, k = 4
  0.0108; the look-check crop k = 2 0.0350, k = 4 0.0507 (mean, p99 and max unchanged from the
  report's earlier figures). The report's V8 paragraph carries them. Tests
  `test_app_v8_v18.py::test_v8_photo_preview_at_1_1_and_k_2_and_4_against_the_downscaled_export`
  and `::test_v8_photo_k_above_1_on_real_sized_content`. RESULT-BEARING: the dispatcher names it
  in the accept record.

**Reviewer A: TERMINAL.** Converged at round 4 of 5 (R1 0/5/11, R2 0/3/6, R3 0/1/4 after the
reclassification, R4 0/0/2); every item fixed or ruled (R1-13 recorded per `ace08fbb`; R2-4 banked
as DR-90); the terminating round's cleanup done at `67a285a`. No further Reviewer A round.

Open items for the EXCLUSIVE windows (granted by the dispatcher after WP4.3a's gate):
- V7 (a)-(f) of record via the S7 driver (NOT YET WRITTEN; ruling S7: uncommitted, in the
  evidence folder, importing the committed `tests/test_app_v7.py` scenario functions); the witness
  keys those functions return are `proxies_shown_during_analysis` (b) and
  `k1_renders_during_a_sink_write` (e).
- The GX011627 V18 / V8 video leg: p99 at k = 2 ASSERTED (AD-11's real-sized domain) and p99.9
  RECORDED beside mean and max (R4-2's characterisation, never asserted).
- DR-44 (c) and DR-50 on footage.

## RESUME HERE (successor of cell 6; written by cell 6, 2026-10-29)

- State: branch `wp4.3`, base main `038f02e`, head after this ledger commit. Reviewer A CONVERGED
  at R4 and its cleanup is done (above). No product change is pending.
- NEXT, in order (the dispatcher's word, gen 22): the EXCLUSIVE windows after WP4.3a's gate (the
  three open items above, each by `WINDOW REQUEST`; outputs under `work/`, no footage path in any
  record); the report's final figures from those windows (V7 table "Window" column, the GX011627
  V8/V18 figures with p99.9, DR-44 (c)/DR-50 on footage); then the orchestrator's Reviewer B; then
  the ONE gate, with DR-85's `xfail(strict)` dropped after rebasing onto WP4.3a.
- Read first: this ledger's Round 0 design table, the CHARC rulings it carries, the R3 and R4
  sections; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\r4\`; ruling S7 (Round 0) for
  the V7 window driver, which is still to be written.
- Disciplines that bit this arc: never a bare `cd` (the orchestrator shares the process); write
  backslash-bearing text with the Write tool (a heredoc collapsed `\x00` to a NUL byte twice in
  this arc, and a third collapse broke a script before it wrote); check every committed blob for
  CR and NUL.

## Cell 7 (implementer-opus-high, 2026-10-29): DR-85's xfail, the S7 driver, the EXCLUSIVE windows

Base main `5e3537d` (the orchestrator, gen 24, rebased the branch onto it: WP4.3a, WP4.5 and the
inventory refresh merged; all 54 commits patch-identical, the old head kept as
`wp4.3-pre-rebase` at `99cc84c`). The "base main `038f02e`" lines above are history.

### Step 0: DR-85's xfail dropped

- `300731d` `test(wp4.3): drop DR-85's xfail now that WP4.3a's fix is on main`: the
  `xfail(strict=True, raises=OverflowError)` on
  `test_a_settings_file_that_fails_to_decode_is_set_aside_and_start_up_goes_on` removed; the module
  docstring's DR-85 sentence now reads "(DR-85, fixed by WP4.3a on main)". LF, 0 CR, ruff clean.
- Light run `uv run pytest -q -rs tests/test_app_startup.py --basetemp=work/wp4.3-c7-startup`
  (offscreen): 10 passed in 23 s, EXIT 0 (`work/wp4.3-c7/startup.txt`).

### The S7 driver (uncommitted; ruling S7)

Folder `C:/Users/rwsmy/clearwater-review-evidence/wp4.3/windows/` (`md5sums.txt` lists every
file below and every copied log):

| File | md5 | What |
|---|---|---|
| `s7_driver.py` | `0b9ee6cc3ebd2cf07c35dec934cfd901` | the driver of record for window 2 (window 1 ran `a1fb597b2ecc10cf995e244a38a159bf`; the later version only ADDS `v7c-char` and ruling B's (f) reading) |
| `window-commands.sh` | `404c6fa85a8a6023f070b297ac7594d0` | window 1's chain |
| `window2-commands.sh` | `fff719c6e95ce703a80eb657d6ca4800` | window 2's chain |
| `f_build_profile.py` | `051a2061f3b7c6d89dfddb40e5134489` | the (f) build reproduction (finding B) |

Form: imports the committed `tests/test_app_v7.py`, `test_app_v8_v18.py`, `test_app_wiring.py`
and `test_app_startup.py` helpers; pytest-qt's own `QtBot.wait`/`waitUntil` (a subclass with no
pytest request); the real engines with default `Settings` (GPU, the `auto` encoder) and
`output_folder` under `<work>/<mode>/out`; GX011627 through `find_footage_file`; every printed
line redacted; a footage-folder digest before and after each run (count and digest only, never a
path) and a scan of the product logs under the work folder for the footage folder. One mode per
process: `QT_QPA_PLATFORM=offscreen uv run python s7_driver.py <mode> <work> [--dry-run-fixture]`.
Exit 0 PASS, 1 STOP, 2 error. Modes: `v7a`..`v7f`, `plant-f` + `v7f-settled`, `v7c-char`,
`v8v18`, `dr44c-analysis|export|batch`. Dry runs on the committed fixture clip (NOT of record):
`windows/dry/`, `windows/dry2/`.

### Findings at preparation

- **B ((f) over 100 ms, pre-show).** Dry (f) on the fixture: 158 / 651 ms (planted in-process),
  157 ms (settled). The longest gap is the synchronous `build_application` on the interface
  thread before the window exists: 126 ms settled, 609 ms just after planting; fresh process
  without a cache 55 / 37 ms (first / second build), right after 20 GB of writes 933 / 771 ms
  (`f_build_profile.py`; fsync 191 ms, `menuBar` 107 ms: the host busy). CHARC RULING B
  (`b9a0ce010581a296`, verbatim in the dispatcher's relay): "V7 (f)'s probe starts at show() ...
  build_application's wall time is RECORDED beside the (f) figure as a start-up figure, cold and
  warm, and is never asserted against 100 ms." Consequences (2) and (3) are OPEN (RESUME HERE).
- **C (round 0's plant is NOT sparse; a record correction).** Round 0's recipe (`fsutil sparse
  setflag`, then `truncate` to 64,598,686 B) allocates every pack: on Windows `truncate` extends
  through the C runtime's `_chsize_s`, which WRITES the zeros (`fsutil sparse queryrange`: one
  range, 0 to 0x3d9b29e). So round 0's "made sparse and extended by truncate" (Measured start-up
  steps, above) is wrong: its 20 GB cache-open figures are from 19.96 GB of ALLOCATED packs, which
  is what a real full cache is. Each plant costs 19.96 GB of disk; the dispatcher deleted the
  dry-run plants (C: 87 -> 179 GB free, then dry2's 19 GB likewise).
- **A (the GX011627 V18/V8 leg's form).** RULED by the dispatcher (CHARC concurred): a DRIVER STEP
  (`v8v18`), not a committed test; mean <= 1/255 AND p99 <= 2/255 at k = 2 ASSERTED at frame
  indices 10, n/4, n/2, 3n/4; p99.9 and max RECORDED (ace08fbb condition 1).

### Window 1 (granted 22:14Z; `window-commands.sh`; host exclusive; disk 179 GB before and after)

| Run | EXIT | Figures (longest / p99 / ticks) |
|---|---|---|
| v7a (a) GX011627 analysis | 0 | 18.0 / 15.0 ms / 7,172; analysis 71.7 s, 681 frames, GPU |
| v7b (b) scrubbing during it | 0 | 21.0 / 16.0 ms / 6,852; 1,400 proxies shown during the analysis |
| v7c (c) File > Export | **1 STOP** | **182.0** / 12.0 ms / 20,963; export 210.2 s, one 86.0 MB output |

The chain stopped at v7c. CHARC RULING on (c) (`805376769abe4177`, 22:23:44Z): (a), the (c)
figure of record STANDS at 182.0 ms, a STOP; not re-run as a run of record; a characterisation
run ordered. Logs: `windows/win1/`.

### Window 2 (granted ~22:33Z; `window2-commands.sh`; host exclusive; disk 179 GB before/after)

| Run | EXIT | Figures (longest / p99 / ticks) |
|---|---|---|
| v7c-char (c) CHARACTERISATION, NOT of record | 0 | 177.0 / 12.0 ms / 20,682; gaps over 50 ms: 135.8 ms at +22.29 s and 176.5 ms at +73.37 s after the trigger |
| v7d (d) 300-still batch (DR-50) | 0 | 66.0 / 55.0 ms / 1,887; batch 32.4 s, 300 of 300 done |
| v7e (e) 1:1 4K render during the export | **1 STOP** | **196.0** / 12.0 ms / 20,969; 1 render with k = 1 inside the sink's write; analysis before 61.6 s |

The chain stopped at v7e (of record). NOT RUN: v8v18, dr44c-analysis, dr44c-export,
dr44c-batch, plant-f, v7f-settled. Logs: `windows/win2/` (`v7c-char.txt`, `char-events.json`).

**v7c-char finding (where (c)'s gaps fall).** The export's phases (relative to the trigger):
`exports.job` on the interface thread 0.01 ms; preview release +3..+40 ms (worker); source and
sink built +1,142 ms; sink open (encoder spawn) +2,498..+3,278 ms; first frame +3,652 ms; first
write +4,204..+4,237 ms; 681 frames to +206,228 ms; sink close (finalise/mux)
+206,228..+207,101 ms; `on_done` on the interface thread +207,155 ms. Both long gaps fall
MID-ENCODE (+22.3 s, +73.4 s), with NO phase event, log record, job-runner callback or gc
collection within 1 s of either (gc: gen0 22, gen1 0, gen2 5, longest 38.1 ms, none overlapping;
the gen-2 passes were at +35 ms, +109.7 s and +207.1 s). The watchdog (10 ms poll, samples at 60
and 150 ms late) took its FIRST sample of each gap only at 135 and 175 ms late, i.e. the
watchdog thread itself could not run for the gap's length. Both samples show the interface
thread IDLE inside Qt's event loop (`qt_compat.py:160 exec` under `qtbot.wait`), no Python work
of its own; the two compute threads were each at a device-to-host sync point:
`clearwater-job` in `core/backend.py:666` `rgb_to_planes` (`xp.asnumpy(planes)`, via
`io/video/encode.py:975 _payload` <- `:717 write`) and `export-analysis` in `core/ops.py:284`
`channel_means` (`.tolist()`; via `methods/ancuti_fusion.py` `analyze` <- `analysis/engine.py`
`_measure`). Reading (cell 7's, for CHARC to rule): NOT interface-thread work and NOT gc; a
worker thread holding the GIL for about 135-175 ms, most likely across a CuPy device-to-host
synchronisation on the export path (the encoder's `rgb_to_planes` or the export analysis's
`channel_means`), which starves every other Python thread, the interface thread's probe slot
included. The stacks name the two candidates; they do not prove which one held it.

Depth: 188,424 at the first window request; 194,057 at window 1's release; 228,587 at window 2's
grant (given by the dispatcher, gen 24).

## RESUME HERE (successor of cell 7; written by cell 7, 2026-10-29)

- State: branch `wp4.3`, base main `5e3537d`, head = this ledger commit (after `300731d`). No
  product change pending; the report `docs/reports/wp4.3-application-wiring.md` is NOT yet
  updated with any window figure.
- OPEN with CHARC: the CAUSE of (c)'s 182.0 ms and (e)'s 196.0 ms STOPs (both of record), on the
  v7c-char finding above. Do not re-run (c) or (e) as runs of record; do not tune.
- NOT YET RUN (window evidence still owed, each by a WINDOW REQUEST; chain form in
  `window2-commands.sh` minus the runs done): `v8v18` (ruling A), `dr44c-analysis`,
  `dr44c-export`, `dr44c-batch`, `plant-f` then `v7f-settled` (ruling B reading built into the
  driver at md5 `0b9ee6cc...`: post-show longest OF RECORD, pre-show and cold/warm build
  recorded). Whether these run before or after CHARC's (c)/(e) ruling is the dispatcher's call.
- Post-window code step (ruling B consequence 2, a FRESH step): move
  `tests/test_app_v7.py::scenario_f_start_up`'s probe start to `show()`, RED-first on the planted
  form (a planted post-show stall must still fail; the pre-show build no longer counts); the test
  records no build figure (the driver does).
- The report (ruling B consequence 3 and the windows): one sentence stating (f)'s rule; the
  start-up figures 55 / 37 ms cold process, 933 / 771 ms right after 20 GB of writes
  (disk-cache eviction, report-only), 158 / 157 ms planted / settled in-process; the V7 table's
  "Window" column (a) 18.0 / 15.0, (b) 21.0 / 16.0, (c) 182.0 / 12.0 STOP, (d) 66.0 / 55.0,
  (e) 196.0 / 12.0 STOP, (f) pending; DR-50 = (d)'s 300-item figure (66.0 ms, within); DR-85 now
  closed by WP4.3a (the xfail dropped at `300731d`); every figure names its run (driver md5,
  command, EXIT); the round-0 "sparse" correction (C).
- Disciplines: never a bare `cd`; backslash-bearing text by the Write tool; LF, 0 CR, 0 NUL in
  every blob; a plant costs 19.96 GB of real disk (check free space; dry-run plants are deleted
  only on the dispatcher's word).

## Cell 8 (implementer-opus-high, 2026-10-29): window 3 (the V7 stall characterisation + the six owed runs)

Dispatch: orchestrator gen 24, `prompt-wp4.3-cell8.md`; CHARC ruling `62cd31f1fdf39406` (verbatim
in the dispatch): (a) one more characterisation step, driver-side, no product change, three
discriminators, then the six owed runs of record in the same EXCLUSIVE window 3, each INDEPENDENT.
Head at start `990b778`, worktree clean.

### Preparation (no window)

New uncommitted files in `C:/Users/rwsmy/clearwater-review-evidence/wp4.3/windows/` (all LF,
0 NUL; `md5sums.txt` updated). `s7_driver.py` is UNCHANGED (`0b9ee6cc3ebd2cf07c35dec934cfd901`) and
drives the six runs of record.

| File | md5 | What |
|---|---|---|
| `s7_char3.py` | `5b39ac085424257d5003d29568f75112` | sibling driver: imports `s7_driver` unchanged; modes `v7c-char3` (s7's v7c-char) and `v7e-char` (s7's `run_v7("e")` with the probe readings, watchdog, gc, log and job-runner stamps); exit 0 on completion (characterisation, never of record) |
| `heartbeat.py` | `3b8a0551fb88bcc8be3e07981f38bc54` | discriminator 2: stdlib child, `perf_counter_ns` every 10 ms held in memory, written at stdin EOF |
| `memwatch.py` | `e3520470f70b4c2fdaf664ecf58daee0` | beside it (psutil, in the venv already): the product process's working set, private bytes, page faults, CPU time and host available memory every 20 ms, out of process |
| `char3_post.py` | `7d1817ddfc956864bc3356888900adee` | after each characterisation run: per probe gap over 50 ms, the wrapped calls in flight / spanning, the heartbeat's and memwatch's overlap, py-spy's change points; verdict line; privacy scan |
| `window3-commands.sh` | `58478c4d0940bb008dbbcd66578e0925` | the chain: v7c-char3 (+post), v7e-char (+post), then v8v18, dr44c-analysis, dr44c-export, dr44c-batch, plant-f, v7f-settled; no exit stops it; `dry` argument = the same chain on the fixture |

Discriminator 1, the call wrappers (start, end, thread, frame index, enclosing wrapped call), all
installed before the build. REACHED: `CupyBackend.rgb_to_planes`, `cupy.asnumpy` (every caller),
`FFmpegVideoSink._payload`, `.write`, `._send` (the pipe writes), `channel_means` (every module
binding), `AncutiFusionMethod.analyze` (the analysis frame index), `gui.imaging.render_host`,
CuPy pool `malloc` (`cupy.cuda.set_allocator`), `CupyBackend.release_fft_plans` and inside it
`pool.free_all_blocks` and `plan_cache.clear` (timing proxies from `cupy.get_default_memory_pool`
and `cupy.fft.config.get_plan_cache`). NOT REACHABLE (C-type methods): `host.tobytes()` (derived
as `rgb_to_planes`'s tail after its `asnumpy`) and `channel_means`'s `.tolist()` (inside the
`channel_means` wrapper).

Discriminator 3, py-spy: `uvx py-spy@0.4.2 record --gil --native --threads --idle -r 200 -p <pid>
-f chrometrace -o <disc>/pyspy-trace.json`, attached just before the scenario's probe starts
(V7's `measured`), stopped right after it. py-spy VERSION 0.4.2 (MIT; uvx only, NOT in
`pyproject.toml` / `uv.lock`). Findings at preparation:
- `--native` attaches and works on this host, but `python312.dll` has no symbols: native frame
  names are nearest exports (e.g. `PyFloat_FormatAdvancedWriter` under `PyEval_AcquireThread`) and
  are NOT to be read as call names; the Python frames are right.
- py-spy pins to the INTERPRETER's pid (`os.getpid()`), not the venv launcher's (attaching to the
  launcher fails "Failed to find python version").
- Left sampling to the target's exit, py-spy panicked ("Failed to resume process: Access is
  denied") and wrote nothing (first dry run); so the driver stops it with CTRL_BREAK (new process
  group) and waits for "Wrote chrome trace".
- The chrometrace form: per sample only the GIL holder; a thread's frames are emitted only when its
  stack CHANGES. So events inside a gap name a holder; NO events inside a gap is ambiguous (an
  unchanged holder, or none); the post prints the last change before and the first after.
- Clock: a 60 ms GIL-holding marker on the interface thread after the attach and before the stop;
  the two markers agreed within 0.6-17 ms in the dry runs (one sample interval).
- Achieved rate about 50-105 samples/s, not 200 (native unwinding); py-spy suspends the process
  per sample, so it PERTURBS the figures (dry (c) longest 72-213 ms with py-spy against 43 ms
  without on the fixture). The heartbeat is out of process and unaffected by that suspension.

Dry runs (fixture, NOT of record; `work/wp4.3-c8/dry*`, logs copied to `windows/dry3/`):
`bash window3-commands.sh dry` ran the whole chain: v7c-char3 0 (+post 0), v7e-char 0 (+post 0),
v8v18 1 (expected: the fixture is outside AD-11's domain, as cell 7's dry), dr44c-analysis 0,
dr44c-export 0, dr44c-batch 0, plant-f 0, v7f-settled 0; about 1.5 min. Heartbeat clock check
(one QPC clock) True for both children; footage folder unchanged (128 files); product logs naming
it 0; the privacy scan of every discriminator record and `char-events.json` 0 hits. The dry plant
(19 GB) deleted under the dispatcher's grant; C: 179 GB free after.

### Window 3 (granted ~23:13Z by the orchestrator, gen 24; `window3-commands.sh` md5 `58478c4d`; host exclusive)

Chain 23:14:16Z-23:28:55Z, CHAIN-DONE, every run independent. RAM available 9.61 of 33.52 GB before;
C: 179 GB free before, 159 GB after (the plant-f cache, 19.96 GB, kept under
`work/wp4.3-c8-win3/v7f` on the dispatcher's word). py-spy 0.4.2. Logs and records copied to
`windows/win3/` (35 files, md5s in `md5sums.txt`); privacy: 0 hits for the footage folder in any
file there (grep, and the post's scan of every discriminator record); footage folder unchanged
(128 files) in every run; product logs naming it 0.

**The six runs OF RECORD** (`s7_driver.py` `0b9ee6cc...`, unchanged):

| Run | EXIT | Figures |
|---|---|---|
| v8v18 | **1 STOP** | V18: first render with the analysis running, statistics None, corrected side True; after completion shown statistics == `smoothed_record(pts)` True (analysis 68.7 s, 681 frames). V8 video at k = 2, 3840x2160, GPU: frame 10 mean 0.000488 / p99 0.007203; 170 0.000330 / 0.003579; 340 0.000185 / 0.002301 (within); **frame 510 mean 0.000315 (within), p99 0.007885 > 2/255 = 0.007843: OVER** by 0.000042; p99.9 0.027003, max 0.101342 (recorded). Shown == harness preview at all four (max diff 0) |
| dr44c-analysis | 0 | ended True in 361 ms, at close [True], no temporaries |
| dr44c-export | 0 | ended True in 218 ms, at close [True], no temporaries (analysis before 63.8 s) |
| dr44c-batch | 0 | ended True in 262 ms, at close [True], no temporaries |
| plant-f | 0 | 309 entries, 19.96 GB; settling opens 4,515.5 ms then 96.5 ms |
| v7f-settled | 0 | ruling B, OF RECORD: from show() longest **47.5 ms**, p99 15.1 ms, 6,179 gaps (PASS). Recorded only: before show() longest 78.7 ms; one 104.7 ms gap SPANS show() (78.7 ms before it, 26.0 ms after); build_application cold 85.9 ms, warm 40.0 ms; cache open 223.8 ms; analysis found it pending [False]; the committed probe from before the build 105.0 ms / p99 15.0 ms |

**The two characterisations (NOT of record; py-spy and the wrappers perturb them):**

| Run | Figures | Gaps over 50 ms |
|---|---|---|
| v7c-char3 | longest 412.0 ms, p99 26.0 ms, 21,410 ticks; export 681 frames; analysis before 60.5 s | 48 (window 2's v7c-char: 2) |
| v7e-char | longest 161.0 ms, p99 27.0 ms, 21,934 ticks; witness k1 renders during a sink write 1 | 45 |

What each discriminator answered (`windows/win3/*-post.txt`, `gapsum.txt`, `callstats.txt`):
- **(2) heartbeat: answered, unambiguous.** Over both probes the out-of-process heartbeat's longest
  interval was 16.3 ms (p99 11.6 ms, none over 30 ms); every one of the 93 gaps has the heartbeat's longest overlapping interval at
  10.2-14.6 ms. memwatch: host available 6.5-9.8 GB, working set 0.29-1.58 GB. The stall
  is INSIDE the product process; not the host, not paging.
- **(3) py-spy: answered.** Inside the gaps the GIL was sampled with `clearwater-job` (35 of 48 /
  32 of 45 gaps), `export-analysis` (19 / 19) and the INTERFACE THREAD itself (20 / 15), mostly at
  `jobs.py:239 _flush` -> on_progress -> `export_panel.py:145-147 _progress` -> (Qt) ->
  `app/main.py:78 eventFilter`. No single thread holds the GIL across a gap: it passes among the
  two compute threads and the interface thread.
- **(1) call wrappers: answered (negatively for the copies).** No device-to-host call is a holder:
  `rgb_to_planes` (p50 148-177 ms per frame, of which `asnumpy` about 5 ms) spans 1 / 2 gaps, each
  time together with `export-analysis`'s `channel_means` (both at GPU syncs, GIL released);
  `pool.malloc` p99 0.01-0.02 ms; `sink._send` max 29.6-33.5 ms. `method.analyze [export-analysis]`
  spans 15 / 15 gaps (a long per-frame call). s7's runner stamps: the interface thread's progress
  delivery (`on_progress`) took 30-55 ms in most mid-export gaps (39 / 49 interface-thread runner stamps over 5 ms, on_progress and poll).
  At the job boundaries (the preview release before the export, the export analysis's end, the
  export's end) `release_fft_plans` -> `plan_cache.clear` (weakref finalizers) with a gen-2 gc on
  the same thread spans the gap: 405 / 72.5 / 147.7 ms (c), 117 / 101.6 / 145.2 ms (e) gc; window 2
  saw gen-2 passes at the same three moments at 38.1 ms at most, so these lengths are inflated by
  the instrumentation (660k call records live in the process; py-spy suspensions).

Cell 8's reading (for CHARC to rule): IN-PROCESS GIL contention, no single holder and nothing
below Python. The two compute threads alternate on the GIL; the interface thread's own Python work
during the export (progress delivery through `ExportPanel._progress` and the window's Python event
filter, one GIL re-acquisition per callback, each up to the 5 ms switch interval behind the
workers) stretches to 30-55 ms; at job boundaries `plan_cache.clear` + a gen-2 gc on a worker
holds the GIL. The perturbation (48 gaps here against 2 in window 2) means the figures are not
comparable with (c) 182.0 ms and (e) 196.0 ms of record; the mechanism, not the size, is the
evidence.

## Cell 9 (implementer-opus-high, 2026-10-29/30): the V7 remediation step, the (f) probe move, window 4 preparation, R5

Dispatch: orchestrator gen 25, `prompt-wp4.3-cell9.md`. Governing ruling: CHARC `7b32521f060044d9`
(2026-10-29 23:35:47Z; verbatim in the dispatch): query 1 (a) ONE bounded remediation step,
RED-first, then (c) and (e) re-runs of record in window 4 at the default 5 ms and at 1 ms switch
interval; query 2 (ii) the 16-frame V8 characterisation at k = 2. **GRANT (item 1, msg
`7b32521f060044d9`): `src/clearwater/gui/jobs.py` (`_flush` rate) and
`src/clearwater/gui/export_panel.py` (`_progress` cost only), tests in WP4.3's own test files or
the panels' existing test files for new cases only. NOT USED: neither file changed (below).**
Ruling B (`b9a0ce010581a296`) consequence 2 (the (f) probe move). Head at start `1d96dc4`, clean.

### The step (commits, each RED alone and shown failing at its parent)

| Pair | RED | What it plants | At the parent | GREEN | After |
|---|---|---|---|---|---|
| item 1 | `6c06e54` | `tests/test_app_interface_load.py`: a counting profiler (`sys.setprofile`, Python `call` events) around a status-bar `window.repaint(rect)` and `QCoreApplication.sendEvent` of UpdateRequest, LayoutRequest and a `QTimerEvent` to the window | 5 `_CloseWatch.eventFilter` entries (+ the enum conversion's Python): FAIL | `6dd9f19`: `AppWindow(MainWindow)` notes the close in `closeEvent` before the shell's shutdown; `_CloseWatch` gone; the start-up order test spies on `AppWindow` | 0 Python calls: PASS |
| item 1 pin | (same commit) | `test_the_runner_delivers_at_most_one_report_per_tick_and_the_latest` | PASS (the rule already held at `1d96dc4`: a pin, NOT a RED) | none (`gui/jobs.py` unchanged) | PASS |
| item 3 | `4639bd8` (an amend of `1c21702`, mine, unshared: the first form planted before start-up's end and the GREEN's first idle check froze the load) | after a 2.5 s settle, a job's end allocates max(300,000, tracked objects) small lists kept alive; `gc.callbacks` records the thread of each generation-2 start; and the policy test (freeze above the interpreter's own 377 after start-up, third threshold raised, both undone at close) | 3 full collections on `clearwater-job`: FAIL; no freeze: FAIL | `3e2db4d` (+ `2124390`, a docstring rewrap: `3e2db4d` was committed with an E501 the chained check printed; my slip, fixed in the next commit): `FullCollections` (below) | none on the job's thread before `on_done`, one on the main thread at an idle check: PASS |
| (f) | `838b665` | `test_v7_f_a_planted_pre_show_build_cost_is_not_counted` (0.4 s in `install_settings_dialog`, before `show()`); `test_v7_f_a_planted_post_show_stall_still_fails` (0.4 s at `Application.start_jobs`, after `show()`, asserted >= 390 ms) | pre-show 459.0 ms: FAIL; post-show 446.0 ms: PASS | `28c4ece`: `measured()` takes a caller-started probe; `scenario_f_start_up` starts it in a wrapped `MainWindow.show` (restored, or deleted when inherited); signature unchanged | pre-show 27.0 ms PASS; post-show 415.0 ms PASS; the slow-cache-open gate form 18.0 ms |

Item 1's RED was first committed with a synthetic `QPaintEvent` sent to the window; QMainWindow
painted outside the paint system and pytest-qt's Python message handler counted 312 calls on the
GREEN too, so the RED commit was amended (`6c06e54`) to a real `window.repaint(rect)` over the
status bar, re-shown failing at `1d96dc4` (main.py from `1d96dc4` restored into the tree for the
run, the GREEN copy put back after; no stash).

Why `gui/jobs.py` and `gui/export_panel.py` did not change (item 1's grant was permission): the
runner already delivers at most one report per job per 50 ms tick, the latest, the last before
`on_done` (pinned). Host probes (development, scratch, NOT of record): PySide6 setters do not
release the GIL (a `setValue` cost 0.5 ms with or without two Python spinner threads) and Qt
returns early on unchanged values, so `_progress` skipping unchanged calls saves nothing; the
cost per report was the Python event filter entered by each paint / update / layout event the
setters cause (a bare window: 27 ms per report without a filter, 57-68 ms with one, under two
spinners). On the REAL window (`build_application`, `ExportPanel._progress` + `processEvents`,
alternating the export's and the analysis's messages, two spinners, 120 reports): `1d96dc4`'s
`main.py` median 101.3 ms / max 264.0 ms per report; `6dd9f19` median 31.2 ms / max 111.4 ms
(the remaining one GIL re-acquisition per Python entry is item 2's subject).

Item 3's form (`FullCollections`, `app/main.py`, owned by `AppWindow`, started at the end of
`build_application`, stopped in `closeEvent` after the shutdown): CPython's automatic generation-2
collection off while started (third threshold 2**31 - 1; generations 0 and 1 automatic); a 1 s
`QTimer`: the first idle tick freezes (`gc.freeze`, no collection first), later idle ticks
collect past the process's own third threshold, busy ticks past 10x it; the last stop restores the
thresholds and unfreezes. `core/` and `release_fft_plans` untouched: the app-layer form keeps the
collection off the job's thread (no STOP needed). Host figures: a full collection over 2M objects
74.6 ms, 0.003 ms after a freeze; the freeze 8.0 ms. `gc.freeze()` resets the collection counts
(observed: (6, 0, 43) -> (1, 0, 0)).

Targeted tests at `28c4ece` (offscreen, shared host): `tests/test_app_*.py` (every marker, the V7
gate forms included) + `tests/test_gui_threads.py` + `tests/test_gui_export_panel.py`: **201
passed, 1 skipped** (`tests/test_app_v8_v18.py:133`, the look-check frame absent: pre-existing) in
198.8 s. `uv run ruff check .` exit 0; `uv run ruff format --check .` 285 files formatted; `uv run
mypy` (strict) no issues in 146 files. Every committed blob LF, 0 CR, 0 NUL.

### Window 4 preparation (no window; files in `C:/Users/rwsmy/clearwater-review-evidence/wp4.3/windows/`, uncommitted, LF, 0 NUL)

| File | md5 | What |
|---|---|---|
| `s7_driver.py` | `0b9ee6cc3ebd2cf07c35dec934cfd901` | UNCHANGED, the driver of record |
| `s7_switch.py` | `bd19cbbae614bc3a067d798dc5d23c59` | item 2 toggle: `sys.setswitchinterval(<ms>/1000)` first, checks the driver's md5, then `runpy.run_path(s7_driver.py, run_name="__main__")`; its one addition prints the export wall time at the Export panel's result (`JobResult.elapsed_s` and trigger-to-result); both 5 ms and 1 ms runs use it |
| `s7_v8char.py` | `60ab95a2a69355f8ccd134f2d64a0348` | query 2 (ii): imports `s7_driver` unchanged; `run_v8v18`'s per-frame steps at 16 frames `int((i + 0.5) * n / 16)`, mean / p99 / p99.9 / max and the shown-vs-harness-preview max diff each, a TABLE and a SUMMARY; no bound asserted; exit 0 on completion |
| `window4-commands.sh` | `b2ec4f483949ea60e93849c34705f5e3` | the chain: v7c 5 ms, v7c 1 ms, v7e 5 ms, v7e 1 ms (`s7_switch.py`, work folders `sw5/` and `sw1/`), then `s7_v8char.py`; every run independent, every exit recorded; disk and RAM before and after, driver md5s, HEAD; `dry` = the same on the fixture into `work/wp4.3-c9/dry-chain/` |

Dry run (fixture, NOT of record, 2026-10-30 00:11:18Z-00:12:09Z, 51 s; logs copied to
`windows/dry4/`, md5s in `md5sums.txt`): v7c-sw5 0 (longest 12.0 ms, p99 11.0, export job 3.1 s),
v7c-sw1 0 (13.0 / 11.0, 3.0 s), v7e-sw5 0 (18.0 / 12.2, witness k1 1, 3.8 s), v7e-sw1 0 (19.0 /
13.1, witness 1, 3.9 s), v8char 0 (45 frames, 16 rows, p99 about 10/255 on every row: the fixture
is outside AD-11's domain as in every earlier dry run; shown-vs-preview max diff 0 on all 16).
Each run printed `switch interval 5.000 / 1.000 ms` and the driver md5 `0b9ee6cc...`. Footage folder
unchanged (128 files), product logs naming it 0, a grep of every dry output for the footage folder
0 hits. C: 177 GB free before and after; RAM available 8.67 of 33.52 GB.

### Reviewer A round 5 (`1d96dc4..28c4ece` minus `docs/proofs`; R4's form)

Runner `r5/run_review.sh` (R4's, unchanged), prompt `r5/review-prompt.md`, diff
`r5/review-diff.txt`, transcript `r5/review.stderr.txt`, verdict `r5/review.txt`, adjudication
`r5/adjudication.md`, md5s `r5/md5sums.txt` (all under
`C:/Users/rwsmy/clearwater-review-evidence/wp4.3/r5/`). Codex `gpt-6.1-sol` / high, WSL, 85,061
tokens, exit 0 at 00:25:06Z, no transport error, every search excluded `docs/proofs/**`.
**VERDICT: NEW_CRITICAL_MAJOR_FOUND (0 / 3 / 4).** Dispositions (cell; for the ruling):

- R5-1 MAJOR CONFIRMED, blocking: the busy-time `gc.collect()` (`main.py:147-149`) runs on the
  interface thread for as long as the unfrozen heap takes (reviewer's synthetic 8M objects 163.6
  ms; and before start-up's first idle moment it scans the whole heap). Proposed: drop the busy
  collection, collect only at idle (the ruling's own option); measure the memory cost in window 4.
- R5-2 MAJOR CONFIRMED as a defect, proposed RECLASSIFY MINOR: one window's idle freezes another
  window's working heap; OUT of envelope (the program builds one window); fix cheaply (idle = no
  started window has an active job).
- R5-3 MAJOR, first half CONFIRMED (the policy starts after `start_jobs()`'s workers), second half
  NOT REACHABLE (no event is processed between the two calls); proposed RECLASSIFY MINOR; fix:
  start before `start_jobs()`, and guard `start()` with `close_seen`.
- R5-4 MINOR CONFIRMED (`_frozen` not reset on restart; not reachable in the program).
- R5-5, R5-6 MINOR CONFIRMED, test-only (the runner pin asserts an average; a descheduled worker
  can starve its 1 s budget).
- R5-7 MINOR CONFIRMED, docs-only (`AppWindow.__init__` without Args).

Per the dispatch, NO change was made after the verdict; the cell yields `R5 VERDICT:`.

### Notes for the record

- The window driver's `v7f` / `v7f-settled` modes still import `scenario_f_start_up` (signature
  unchanged), but with the probe now starting at `show()` their "the committed probe, from before
  the build" result line and their "before show()" figure (about 0 ms by construction) are stale
  labels. Neither mode is in window 4.
- Disk at the R5 yield: C: 166 GB free (another lane's use since the dry run's 177 GB).

## Cell 10 (implementer-opus-high, 2026-10-30): the R5 remediation, R6

Dispatch: orchestrator gen 25, `prompt-wp4.3-cell10.md`. Governing ruling: CHARC
`cc0703a79f98154e` (2026-10-30T00:30:08Z, verbatim in the dispatch and in
`clearwater-review-evidence/wp4.3/r5-ruling-cc0703a7.md`): Q1 (a) DROP the busy-time collection,
full collections only at an idle moment (no started window has an active job), the memory cost
MEASURED in window 4, a heap-size cap DECLINED; Q2 (a) R5-2 and R5-3 RECLASSIFIED MINOR, all
seven fixed, product items RED-first; Q3 cell 9 stood down at 282,316, fresh cell 10. Head at
start `175a8e8`, clean. Record note (CHARC's, for the accept): this step's round count exceeds the
fill's five because R5 and R6 review a NEW step after R1-R4 converged on the main build.

### The R5 remediation (each RED committed alone and shown failing at its parent)

All new tests are in `tests/test_app_interface_load.py`; product changes only in
`src/clearwater/app/main.py`; `core/`, `gui/` untouched.

| Finding | RED | What it plants | At the parent | GREEN | After |
|---|---|---|---|---|---|
| R5-1 | `f1ab586` | `test_no_full_collection_runs_while_a_job_runs_however_far_overdue`: a bare `FullCollections` over a stand-in runner (`active()` 1), `gc.collect(1)` until 20x the interpreter's own third threshold is pending, two checks, `gc.callbacks` records generation-2 starts | `['MainThread']`: FAIL | `e1a8599`: the busy branch and `BUSY_COLLECTION_FACTOR` dropped; the docstring states the bound (no full collection while a job runs; a collection's duration has none) and the cost | `[]`: PASS |
| R5-2 | `00ca290` | `test_an_idle_window_neither_freezes_nor_collects_while_another_windows_job_runs`: A active, B idle, two checks; then A idles and a freeze must follow | freeze count 377 -> 87,040: FAIL | `d13f84b`: idle = no started instance's runner active | PASS |
| R5-3 | `2b7e30b` | `test_the_collection_policy_starts_before_the_start_up_workers` (spies `Application.start_jobs` for the third threshold); `test_a_closed_windows_collection_policy_does_not_start` | 10 (not raised): FAIL; 2147483647 after a post-close start: FAIL | `4611ed6`: `start()` before `start_jobs()`; `FullCollections(..., closed=)`, `AppWindow` passes `lambda: self.close_seen`; `start()` does nothing once closed | PASS |
| R5-4 | `f3757f1` | `test_a_restarted_collection_policy_freezes_again` | the wait for the second freeze timed out (5 s): FAIL | `83af26f`: `start()` resets `_frozen` | PASS |
| R5-5, R5-6 | test-only `a3e73b5` | the runner pin: class-level marks on `QtJobRunner._poll` and `_on_finished` (set before construction); at most one report between two marks; the job reports at least 20,000 times and for at least 1 s; "fewer deliveries than reports" replaces the ratio | (pin: green at base) | a local mutation (the poll delivering twice per tick) FAILS it (`max(per_mark)` 2) | PASS |
| R5-5 follow-up | test-only `987681c` | `a3e73b5` asserted the final delivery itself carried the last report; the first targeted run failed it (`('end', 0)` before `done`: a poll had delivered the last report already); the property kept is the order (the last report precedes `on_done`) | - | 5/5 local runs PASS | PASS |
| R5-7 | docs `f9ea560` | `AppWindow.__init__` Args section (checked against `MainWindow`'s own) | - | - | - |

Targeted tests at `987681c` (offscreen, shared host): `tests/test_app_*.py` (every marker) +
`tests/test_gui_threads.py` + `tests/test_gui_export_panel.py`: **206 passed, 1 skipped**
(`tests/test_app_v8_v18.py:133`, the look-check frame absent: pre-existing) in 239.9 s (the run
before `987681c`, at `f9ea560`: 1 failed (the pin, above), 205 passed, 1 skipped in 233.2 s). `uv
run ruff check .` exit 0; `uv run ruff format --check .` 285 files formatted; `uv run mypy`
(strict) no issues in 146 files. Every committed blob LF, 0 CR, 0 NUL.

### Reviewer A round 6 (`175a8e8..987681c` minus `docs/proofs`; R4/R5's form, THE RE-RUN)

Runner `r6/run_review.sh` (R5's, unchanged, md5 `ee1de28c...`), prompt `r6/review-prompt.md`
(R5's form plus R5's findings and their dispositions), diff `r6/review-diff.txt`, transcript
`r6/review.stderr.txt`, commands `r6/commands.txt` (26, every search excluding `docs/proofs/**`),
verdict `r6/review.txt`, adjudication `r6/adjudication.md`, the cell's R6-1 reproduction
`r6/r6_1_repro.py` / `.txt`, md5s `r6/md5sums.txt` (all under
`C:/Users/rwsmy/clearwater-review-evidence/wp4.3/r6/`). Codex `gpt-6.1-sol` / high, WSL, 77,380
tokens, probe READY, review exit 0 at 00:55:18Z, no transport error.
**VERDICT: NEW_CRITICAL_MAJOR_FOUND (0 / 1 / 3).** Dispositions (cell; for the ruling):

- R6-1 MAJOR (reviewer: REOPENED R5-1) CONFIRMED by the cell's reproduction (a real
  `LatestWorker` holding a task, an idle runner: froze while the worker was busy `[True]`;
  generation-2 starts `[('MainThread', True)]`): the idle test does not see the window's three
  `LatestWorker` threads (opener, preview renderer, framer). Adjudicated NEW (a distinct route;
  R5-1's fix holds for runner jobs). Proposed RECLASSIFY MINOR: out of V7's states (analysis,
  export and batch are runner jobs; in (a)-(e) a job is active whenever a render or a frame fetch
  runs; in (f) the first idle check beside the opener freezes, it does not collect). Options for
  CHARC: (A, recommended) keep the ruled definition, the docstring states the bound exactly, a DR
  names the residual with window 4's working-set figures as evidence; (B) widen idle to the
  `LatestWorker`s: a grant on `gui/render_worker.py`, `gui/shell.py`, `gui/preview.py`, a RED, and
  new unreviewed code (R7 on that diff alone).
- R6-2 MINOR CONFIRMED, docs-only: the docstring's "freed at the next idle moment" is false for
  garbage present at the first idle check (frozen until the last stop) and ignores the threshold.
- R6-3 MINOR CONFIRMED, test-only, REOPENED R5-5: the pin passes vacuously when no poll runs.
- R6-4 MINOR CONFIRMED, docs-only: "before any worker starts" is false (`AppWindow`'s
  construction starts the three `LatestWorker` threads); "before the start-up jobs".

Cap proposal: R6-1 per (A); then R6-2/R6-4 (docs) and R6-3 (test-only, shown passing on the
vacuous event list at the parent's assertions and failing after) with NO R7, read by the gate's
Reviewer B; then window 4 as ordered (the working-set readings: preparation after the ruling).
Per the dispatch, NO change was made after the verdict; the cell yields `R6 VERDICT:`.

### Notes for the record

- Scratch outputs under `work/wp4.3-c10*` (not of record).
- At the R6 yield, window 4's preparation (dispatch step 3) had not started (it follows R6); done
  after the ruling, below.

### CHARC's R6 ruling (`424f573b88b5a203`, 2026-10-30T01:02:33Z; saved verbatim at `clearwater-review-evidence/wp4.3/r6-ruling-424f573b.md`)

Q1 (A): R6-1 RECLASSIFIED MINOR (the LatestWorkers are not jobs; V7's states are runner jobs); the
docstring states the bound exactly; a MINOR register row is CHARC's at the accept (the cell
touches no register); (B) DECLINED. Q2 (a), THE CAP: R6-2 / R6-4 (docs) and R6-3 (test-only,
RED-shaped) with NO R7; Reviewer B on the final candidate reads them. Q3 (a): window 4 also
re-runs (a), (b), (d), plant-f then v7f-settled OF RECORD on the final code, after the (c) / (e)
pairs and the 16-frame V8, each independent; the pre-remediation figures stay here as history;
the plant is deleted after v7f-settled (grant).

**CAP: R6 was this step's last Reviewer A round; the remaining findings (R6-1..R6-4) were minor.**

### The R6 fixes

| Finding | Commits | What |
|---|---|---|
| R6-3 (test-only) | RED `43dccd4`, GREEN `779b66f` | the pin's postconditions moved unchanged into `_assert_delivered_per_tick`; `test_the_runner_pin_rejects_a_run_whose_polls_delivered_nothing` feeds it the vacuous list `[end, report 20000, done]`: at `74586d4`'s assertions DID NOT RAISE (FAIL); after, the helper requires a poll-delivered report before the `end` mark (PASS; the real pin 3/3 local runs PASS) |
| R6-1, R6-2, R6-4 (docs) | `86ba69a` | `FullCollections`: the bound is "no full collection while any window's runner job runs", and its only one (the opener / renderer / framer `LatestWorker`s are not jobs; a collection's own duration unbounded); garbage present at the first idle check is frozen until the last stop, later garbage waits for a due idle check (R6-2); module step 5 and the `start()` comment say "before the start-up jobs" (R6-4) |

Targeted tests at `86ba69a` (offscreen, shared host): **207 passed, 1 skipped**
(`test_app_v8_v18.py:133`, pre-existing) in 311.0 s; `ruff check .` exit 0; `ruff format --check
.` 285 files formatted; `mypy` (strict) no issues in 146 files. Every committed blob LF, 0 CR.

### Window 4 preparation (no window; `C:/Users/rwsmy/clearwater-review-evidence/wp4.3/windows/`, uncommitted, LF, 0 CR)

| File | md5 | What |
|---|---|---|
| `s7_driver.py` | `0b9ee6cc3ebd2cf07c35dec934cfd901` | UNCHANGED, the driver of record |
| `s7_switch.py` | `5457aca801849b2008b82baec82c8386` | cell 9's (`bd19cbba`) plus, at each export's trigger and result, the process's working set and private bytes (`psutil`, one `memory_info()` read; in the venv, no new dependency), and at the result `gc.get_count()`, `len(gc.garbage)`, `gc.get_freeze_count()`, `gc.get_threshold()` and the working-set growth trigger-to-result (NOT of record) |
| `s7_v8char.py` | `60ab95a2a69355f8ccd134f2d64a0348` | unchanged (cell 9's) |
| `window4-commands.sh` | `fb94390453f25decd082421d171cc7ea` | the chain as ruled: v7c 5 / 1 ms, v7e 5 / 1 ms (`s7_switch.py`, `sw5/`, `sw1/`), v8char, then v7a, v7b, v7d (`s7_driver.py`, `rec/`), a free-disk check (>= 40 GB, else both (f) runs SKIPPED and recorded), plant-f, v7f-settled (`rec/`), `rm -rf rec/v7f/cache` (the plant; config and log kept); every exit recorded; disk / RAM before and after, disk before the plant and with it; `dry` = the fixture into `work/wp4.3-c10/dry-chain/` |

Dry run of the WHOLE chain (fixture, NOT of record, 2026-10-30 01:05:58Z-01:08:50Z, 172 s, chain
exit 0; logs in `windows/dry5/`, md5s in `md5sums.txt`), each run at HEAD `86ba69a`, driver md5
`0b9ee6cc...` printed:

| Run | EXIT | Longest / p99 (ms) | Export wall (job / trigger-to-result) | Working set trigger -> result (growth) | Private bytes trigger -> result | At the result: count, garbage, freeze count |
|---|---|---|---|---|---|---|
| v7c 5 ms | 0 | 14.0 / 11.0 | 3.0 / 3.0 s | 671.5 -> 673.3 MB (+1.8) | 1929.9 -> 1931.4 MB | (37, 0, 0), 0, 89,193 |
| v7c 1 ms | 0 | 11.0 / 11.0 | 3.2 / 3.2 s | 671.4 -> 672.8 MB (+1.3) | 1931.8 -> 1932.6 MB | (37, 0, 0), 0, 89,126 |
| v7e 5 ms | 0 | 16.0 / 14.0 (witness 1) | 4.0 / 4.0 s | 674.1 -> 1004.1 MB (+330.1) | 1924.5 -> 2837.8 MB | (41, 0, 0), 0, 89,240 |
| v7e 1 ms | 0 | 15.0 / 12.0 (witness 1) | 4.0 / 4.0 s | 675.7 -> 1004.6 MB (+328.9) | 1925.2 -> 2835.6 MB | (41, 0, 0), 0, 89,239 |
| v8char | 0 | 16 rows; p99 about 10/255 (fixture outside AD-11's domain); shown-vs-preview max diff 0 | - | - | - | - |
| v7a | 0 | 13.0 / 11.9 (analysis 2.1 s, 45 frames) | - | - | - | - |
| v7b | 0 | 12.0 / 11.9 (witness 15) | - | - | - | - |
| v7d | 0 | 69.0 / 58.0 (batch 39.5 s, 300 done) | - | - | - | - |
| plant-f | 0 | settling opens 5476.3 / 150.7 ms | - | - | - | - |
| v7f-settled | 0 | from show() 39.3 / 18.3 (of-record form); build_application 189.4 ms | - | - | - | - |

The third threshold read 2147483647 at every export result (the policy active). (e)'s working-set
growth includes the 1:1 4K preview render's own buffers (the scenario renders a 4K photo during
the export), so CHARC's 512 MB reading applies to (c) cleanly and to (e) with that included.
Plant deleted ("plant deleted: yes"); C: 175 GB free before, 165 GB before the plant (another
lane's use meanwhile), 146 GB with it, 164 GB after. RAM available 8.20 then 4.80 of 33.52 GB
(shared host). Footage folder unchanged (128 files) in every run; product logs naming it 0; a grep
of every dry output for the footage folder: 0 hits. Stale labels (cell 9's note) still print in
v7f-settled ("the committed probe, from before the build"; "before show() ... 0.0 ms"): the line
of record is "from show() (ruling B, OF RECORD)".

### Window 4 (EXCLUSIVE, granted by orchestrator gen 25 at ~01:24Z; runs OF RECORD except where marked)

Command: `bash /c/Users/rwsmy/clearwater-review-evidence/wp4.3/windows/window4-commands.sh` (md5
`fb943904...`), once, foreground (the tool moved the call to the background at its 600 s cap; the
cell then waited in the foreground on `exits.txt` until `CHAIN-DONE`), 2026-10-30 ~01:24Z-01:48:34Z.
HEAD `b4c8561` (product code = `86ba69a`); drivers `s7_driver.py` `0b9ee6cc...` (unchanged),
`s7_switch.py` `5457aca8...`, `s7_v8char.py` `60ab95a2...`. GX011627 (158.5 MB) located
read-only; device GPU in every run. Logs copied to `windows/win4/` (md5s in `md5sums.txt`;
`exits.txt` `71221c11...`). No tuning, no re-run.

| Run | Switch | EXIT | Longest / p99 (ms) | Export wall (job / trigger-to-result) | Working set trigger -> result (growth) | Private bytes | At the result: count, garbage, freeze count, third threshold |
|---|---|---|---|---|---|---|---|
| v7c | 5 ms | 1 STOP | **180.0** / 12.0 (20,897 ticks) | 209.1 / 209.1 s (86.0 MB out) | 853.4 -> 954.5 MB (+101.1) | 2534.7 -> 2724.5 MB | (37, 0, 0), 0, 89,132, 2147483647 |
| v7c | 1 ms | 1 STOP | **181.0** / 12.0 (21,025) | 210.7 / 210.7 s | 853.6 -> 954.6 MB (+101.1) | 2531.6 -> 2723.4 MB | (39, 0, 0), 0, 89,149, 2147483647 |
| v7e | 5 ms | 1 STOP | **182.0** / 12.0 (21,080; witness 1) | 210.9 / 211.2 s | 991.5 -> 1238.7 MB (+247.2) | 2844.6 -> 3069.9 MB | (42, 0, 0), 0, 89,121, 2147483647 |
| v7e | 1 ms | 0 PASS | 80.0 / 12.0 (21,102; witness 1) | 210.8 / 211.0 s | 1002.4 -> 1239.4 MB (+237.0) | 2843.3 -> 3060.8 MB | (42, 0, 0), 0, 89,233, 2147483647 |
| v8char (NOT of record) | 5 ms | 0 | 16 frames, table below | - | - | - | - |
| v7a | 5 ms | 0 PASS | 18.0 / 15.0 (analysis 62.7 s, 681 frames) | - | - | - | - |
| v7b | 5 ms | 1 STOP | **195.0** / 15.0 (6,550 ticks; witness 1,339) | - | - | - | - |
| v7d | 5 ms | 0 PASS | 65.0 / 47.0 (batch 29.3 s, 300 done) | - | - | - | - |
| plant-f | 5 ms | 0 | settling opens 4473.3 / 104.4 ms | - | - | - | - |
| v7f-settled | 5 ms | 1 STOP | from show() (ruling B, OF RECORD) **395.4** / 14.9 (5,978 gaps); cache open 188.2 ms; build_application cold 94.9 ms | - | - | - | - |

Against history (pre-remediation, windows 1-3): (a) 18.0 -> 18.0; (b) 21.0 PASS -> **195.0 STOP**
(NEW); (c) 182.0 -> 180.0 / 181.0 (unchanged); (d) 66.0 -> 65.0; (e) 196.0 -> 182.0 (5 ms) / 80.0
(1 ms, one sample); (f) settled 47.5 PASS -> **395.4 STOP** (NEW). Memory (CHARC cc0703a7 Q1): (c)
+101.1 MB per 4K export at both intervals, (e) +247.2 / +237.0 MB including the 1:1 4K render; all
under 512 MB; `len(gc.garbage)` 0 and `gc.get_count()` at most (42, 0, 0) at every result; no
within-export trend readable from two points per export.

16-frame V8 (k = 2, 3840x2160, GPU, NOT of record; values x 1/255): p99 median 1.169, max 1.946
(frame 276); frames over p99 2/255: 0; mean max 0.132 (frame 63); p99.9 2.744-6.679; max
15.758-40.848 (frame 659); shown-vs-preview max diff 0 on all 16. Full table in
`windows/win4/v8char.txt`.

Disk: C: 173 GB free before, 172 GB before the plant, 153 GB with it, 171 GB after (plant
deleted: yes). RAM available 8.50 then 8.43 of 33.52 GB. Footage folder unchanged (128 files) in
every run; product logs naming it 0; a grep of every window output for the footage folder: 0
hits. Kept outputs 850 MB in `work/wp4.3-c10-win4/`.

Cell's reading (REASONED, not measured; for CHARC): (b) and (f) are new STOPs on the remediated
code. Candidate cause: `FullCollections`' idle-time `gc.collect()` on the interface thread. It
fires once `gc.get_count()[2]` exceeds 10 (the saved third threshold) and so skips CPython's own
rule that an automatic full collection waits until the pending long-lived objects exceed 25 % of
the long-lived total; after the start-up freeze, the objects the first open / analysis creates
(module imports of the core and CuPy on the worker, 1.03 s + 947 ms of import at round 0) are
unfrozen, and the next idle check (the opener's `LatestWorker` beside it counts as idle, R6-1)
scans them on the interface thread inside (b)'s and (f)'s probes. Not verified: a
characterisation run with `gc.callbacks` stamps (thread, duration, object counts) against the
probe's gap times would confirm or refute it. (c) and (e) did not move with items 1 and 3.

### CHARC's window-4 ruling (`921babda38ba1f3a`, 2026-10-30T01:53:17Z; saved verbatim at `clearwater-review-evidence/wp4.3/win4-ruling-921babda.md`)

Q1 (a): REVERT item 3 (the gc policy) and its R5 / R6 follow-ups, keeping item 1 and the (f) probe
move; no new design, no new review round; window 5 re-runs (a), (b), (d), plant-f + v7f-settled on
the reverted head; (c) / (e) not re-run (their window-4 figures of record stand); the gc
characterisation DECLINED. Q2 (a): `sys.setswitchinterval` NOT adopted, the default stays; the
report records both intervals' figures. Q3 (a): WP4.3 closes after window 5 (report, Reviewer B,
gate); (c) and (e) are OPEN STOPs of record (CHARC writes DR-98 and briefs WP4.6 export process
isolation). Q4: V8 at k = 2 per frame mean <= 1/255, p99 <= 2.5/255, p99.9 and max recorded only
(CHARC's AD-11 note); window 3's frame 510 (p99 2.011/255) is within the re-ruled bound; v8v18 is
NOT re-run (the 16-frame characterisation is the evidence). Depth at the window-4 yield 231,467
(dispatcher). The CAP stands.

### Item 3's epitaph (the reverted gc policy)

`FullCollections` (cell 9 `3e2db4d`, remediated by cell 10 through R5 / R6) kept CPython's full
collection off the job boundaries: automatic generation 2 off while a window was open, a freeze at
the first idle check, a collection at later idle checks once 10 younger collections were pending.
Window 4 measured it: (c) 180.0 / 181.0 ms and (e) 182.0 ms longest (vs 182.0 / 196.0 before):
nothing measurable bought; (b) 195.0 ms and (f) settled 395.4 ms were NEW STOPs where the policy
acts (an idle-time collection on the interface thread beside the opener worker; the cell's
reading, not characterised: the gc characterisation was declined). Its memory readings, kept for
the record: working set +101.1 MB per 4K export ((c), both intervals), +247.2 / +237.0 MB in (e)
with the 1:1 4K render; `len(gc.garbage)` 0 and `gc.get_count()` at most (42, 0, 0) at every
export result.

### The revert (`7b4c10b`)

One hand-made revert commit (the gc lines interleave with item 1's in `app/main.py`):
`src/clearwater/app/main.py` is item 1's GREEN (`6dd9f19`) plus R5-7's Args section on
`AppWindow` (its "and its collection check" wording dropped); `tests/test_app_interface_load.py`
loses every gc test and helper (`_Runner`, `_full_collections`, `_overdue`, `SETTLE_MS`, item 3's
two tests, the R5-1..R5-4 tests). Reverted in effect: `4639bd8`, `3e2db4d`, `2124390`, `e1a8599`,
`d13f84b`, `4611ed6`, `83af26f`, `86ba69a` and the gc tests of `f1ab586`, `00ca290`, `2b7e30b`,
`f3757f1`. Kept: item 1 (`6c06e54` / `6dd9f19`, the paint test, `test_app_startup.py`'s spy on
`AppWindow`), the runner pin with R5-5 / R5-6 / R6-3 (`a3e73b5`, `987681c`, `43dccd4`,
`779b66f`), R5-7's Args section, the (f) probe move (`838b665`, `28c4ece`). `git diff
1d96dc4..7b4c10b -- src/`: `app/main.py` only, 134 lines, item 1's lines only (`_CloseWatch` ->
`AppWindow.closeEvent`, `Application.window: AppWindow`, `closed()` reads `close_seen`, module
step 2's wording, the imports). No `FullCollections`, `full_collections`, `IDLE_CHECK_MS` or
`BUSY_COLLECTION_FACTOR` left in `src/`, `tests/` or `tools/`.

Targeted tests at `7b4c10b` (offscreen, shared host): `tests/test_app_*.py` (every marker) +
`tests/test_gui_threads.py` + `tests/test_gui_export_panel.py`: **200 passed, 1 skipped**
(`test_app_v8_v18.py:133`, pre-existing) in 191.3 s (207 before the revert, less the 7 gc tests);
`ruff check .` exit 0; `ruff format --check .` 285 files formatted; `mypy` (strict) no issues in 146
files. Every committed blob LF, 0 CR.

### Window 5 preparation (no window)

`windows/window5-commands.sh` md5 `5b14d9812ec4259c7c00004d07aea523` (uncommitted, LF, 0 CR):
v7a, v7b, v7d, then the free-disk check (>= 40 GB, else both (f) runs SKIPPED and recorded),
plant-f, v7f-settled, `rm -rf rec/v7f/cache`; every run on `s7_driver.py` `0b9ee6cc...`
(unchanged) at the default switch interval; outputs `work/wp4.3-c10-win5/`; `dry` = the fixture
into `work/wp4.3-c10/dry5-chain/`.

Dry run (fixture, NOT of record, HEAD `7b4c10b`, 2026-10-30 ~01:59Z-02:01:13Z, chain exit 0; logs
in `windows/dry6/`, md5s in `md5sums.txt`): v7a 0 (12.0 / 11.0 ms), v7b 0 (12.0 / 11.0, witness
14), v7d 0 (92.0 / 46.0, 300 done), plant-f 0 (settling opens 4377.5 / 105.1 ms), v7f-settled 0
(from show() 46.7 / 11.7 ms; build_application 147.5 ms); plant deleted: yes. C: 174 GB free
before, 154 GB with the plant, 173 GB after; RAM available 7.63 / 7.80 of 33.52 GB. Footage folder
unchanged (128 files), product logs naming it 0, a grep of the dry outputs for it 0 hits.
