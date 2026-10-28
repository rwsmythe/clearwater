# WP4.3 — Application wiring (dispatch brief, DRAFT, RULED)

**Status:** DRAFT, RULED 2026-10-28 (CHARC `2c4476d9869df056`, rulings below, which take precedence over the text above them); FINAL only after WP4.2's accept plus one revision pass, on CHARC's word. DRAFT 2026-10-28, written by a drafting helper for the orchestrator (generation 16)
from CHARC's commission `159c14fb79ad1aae` (section 2, the WP4.3 bullet: the RULED bounds),
drafted on main `6536f60`. **This draft is revised once against WP4.2's accept record (and
WP4.1's) before FINAL** (commission section 1), so the composition-root names, the headless
runner and the state of `gui/engines.py` follow what WP4.1 and WP4.2 merged. Base = the main
commit named at dispatch, after WP4.2's accept. Owner decisions: none inside the package. The
look check, V2, any spec text and anything that relaxes a mandatory requirement (D85 among them)
are owner-reserved: each is a STOP, never done here.
- Spec **v0.5.5**: G1-G13 (G11 deferred to v2, 0.5.3), D27, D34, D41, D66, D70-D72, D74, D85,
  D88, D89, D107, D108, D111, D113; section 8.2 (encoder line), 8.3, 8.4; N1, N3, N4, N8, N9; V7, V8, V11 (the
  "leftover temporaries removed on next start" leg), V18. Architecture FINAL 1.0: section 1
  (modules, `app`), 2 ("video preview", "Parameter change (AD-7)"), 3 (IF-2, IF-5, IF-7, IF-8
  with its "Export seam" paragraph, IF-10), 7. AD-1, AD-7 (with its two amendments), AD-9,
  AD-11 (V8), AD-15, AD-20, AD-23 (extended 2026-10-21), AD-25 (a), AD-28, AD-29.
- Plan row WP4.3 (section 6, Phase 4, size L, depends on "WP4.2, WP3.16–WP3.20", feeds "V7, V8,
  V18"); the bullet "**WP4.3** connects the interface to the engines, adds start-up work (encoder
  and graphics-card detection, leftover cleanup), and shows the user whether CPU or GPU is in
  use"; module table 8.1 "`clearwater.app` | Entry point and start-up | WP4.3".
- Records and reports, consumer notes: WP3.16 accept ("Debt and consumer notes"), report sections
  on `default_engines` and DR-44; WP3.17 accept "Consumer notes"; WP3.18 accept "Consumer notes",
  report "The mapping for WP4.3" and "Erratum at the gate" items 1 and 5; WP3.19 accept and report
  "Seam for WP3.14 and WP4.3"; WP3.20 accept "Consumer notes", report "Public API"; WP3.20R
  accept (DR-61); WP3.10 accept "Consumer notes" (`resolve_encoder`, the CREATE_NO_WINDOW spawn
  helper), report section 9; WP3.9 report "Limits" (CREATE_NO_WINDOW); WP3.12 report "Public
  API"; WP3.13 report "Consumer notes" and brief question 3 (RULED by `871a371855bb1630`: "the
  start-up wiring (WP4.3) passes the configured output folder plus the folders of a small journal
  of in-flight writes"); WP3.14 report "Limits"; WP3.21 accept "IF-8 reporting deviation" and
  "Debt and owed rows", report "Limits" (cuFFT plans).
- Cell: `implementer-opus-high` (commission section 1: a composition package across every
  frozen-interface consumer, design choices at round 0). Tier **STRONG**, Claude lane: Reviewer A
  (your loop) and Reviewer B (the orchestrator's seat) are Codex at the pin `gpt-6.1-sol` / high.
- Worktree `.worktrees/wp4.3`, branch `wp4.3` from main, base = the main commit named at dispatch.

**Why.** After WP4.1 and WP4.2 the photo and video paths run end to end headless, but the
application a user starts still runs on stubs: `gui/engines.py` `default_engines()` "refuses
every photo and every video frame" (WP3.16 report), the export panels run against
`unavailable_exports()`, the timeline against `stub_analysis_factory`, and nothing calls
`install_parameter_panels`, `install_timeline`, `install_export_panels` or
`install_settings_dialog`. `shell.run` is "what WP4.3 calls; this package has no entry point".
This package builds the program the owner starts, does the start-up work, and proves V7, V8, V18
and G1-G13 on the running shell with the real engines.

| Field | Content |
|---|---|
| ID and title | WP4.3 — Application wiring; plan section 6 Phase 4 row WP4.3 |
| Goal | One entry point (`clearwater.app`) that builds the real engines (through WP4.1/WP4.2's composition root `clearwater.app.composition` (as proposed in WP4.1's draft; final per its accept)), builds the main window, attaches every Phase 3 panel and the settings dialog to the real engines (the GUI's video source, sink and cache swapped from the stubs here, with the analysis adapter: WP4.2 draft question 3), runs the start-up work (leftover cleanup before any job, encoder detection into the settings dialog's catalog, graphics-card detection shown in the status bar per AD-9), and runs the event loop; the GUI's analysis on WP3.11's engine through the WP3.18 mapping; a GUI recompute serialised against a running export of the same clip (DR-62); the preview's FFT plans released at a preview boundary (DR-68); every FFmpeg and ffprobe child spawned with CREATE_NO_WINDOW through one helper (AD-23 extended); V7 re-measured with the real engines in an EXCLUSIVE window; V8 and V18 shown on the running shell; G1-G13 each checked against the running shell. |
| Spec / decision clauses | Plan bullet (above). G9 "GUI stays responsive during analysis, export and batch processing (work runs off the UI thread)"; V7/D66 "UI responds within 100 ms during analysis, export and batch processing"; V8 "screen-resolution preview vs downsampled full-resolution output differ by less than a threshold set at design; 1:1 view exact", AD-11 "V8 preview vs export (same frame, export downscaled to the preview size by area average): mean abs ≤ 1/255, max ≤ 3/255"; V18 "on opening a clip, a corrected frame is shown before analysis completes, and it updates to the smoothed statistics afterwards"; D85 "Outputs written to a temporary name and renamed on success; leftovers cleaned on next start", 8.4 "Leftover temporary files from a crash are cleaned up on the next start", V11 "leftover temporaries removed on next start"; D34 "Output location: source folder by default"; 8.2 "Encoder capabilities (including 10-bit support) are detected at startup; unavailable options are shown disabled with a reason (D74)"; AD-9 "CPU/GPU use is reported in the status bar ("GPU: RTX 4070 Laptop" / "CPU") and in each job's log line, with the reason when the fallback engaged"; AD-15 "export is unavailable until analysis of that clip completes"; AD-7 amendment 2026-10-26 "a parameter change while an analysis or recompute job is in flight is ABSORBED by that job, never cancelled"; AD-23 extended "FFmpeg and ffprobe child processes are spawned with the Windows CREATE_NO_WINDOW creation flag (a no-op elsewhere) ... implemented once in a shared spawn helper by WP4.3 (real-engine wiring), used by every spawn site"; AD-25 (a) app-data locations "resolved in one place, `clearwater.config.paths`"; AD-29 "Each lower consumer ... declares ONE small `runtime_checkable` Protocol in its own package"; N1 "no OS-specific code without the architect's approval"; N8 "source files never modified". |
| Depends on | On main at dispatch: WP4.2 (accept, the video path and its composition) and WP4.1 (the composition root `src/clearwater/app/composition.py` and the headless runner `tools/headless_export.py` (as proposed in WP4.1's draft; final per its accept)), WP3.16 (`clearwater.gui.shell`, `contract`, `preview`, `jobs`), WP3.17 (`install_parameter_panels`), WP3.18 (`install_timeline`, the `ClipAnalysis` seam), WP3.19 (`install_export_panels`, `clearwater.jobs.export_seam`), WP3.20/WP3.20R (`install_settings_dialog`), WP3.10 (`detect_capabilities`, `resolve_encoder`, `tool_env`), WP3.11 (`AnalysisEngine`), WP3.12 (`DiskProxyCache`), WP3.13 (`remove_leftovers`), WP3.14/WP3.21 (`ExportEngine`, `release_fft_plans`). |
| Files owned (question 1: proposed grants; question 2: the new modules) | NEW (names proposed, question 2): `src/clearwater/app/main.py` (`main(argv=None) -> int`), `src/clearwater/app/startup.py` (leftover cleanup, the write journal, detection), `src/clearwater/app/analysis_adapter.py` (the `ClipAnalysis` adapter over `AnalysisEngine` and its factory), `src/clearwater/app/activity.py` (the per-clip activity guard and the `ExportJobs` wrapper: journal, DR-62, AD-9 log line), `src/clearwater/__main__.py` (`python -m clearwater`, importing `clearwater.app.main`). EDIT (origin WP4.1): `src/clearwater/app/__init__.py` (as proposed in WP4.1's draft; final per its accept): Qt-free exports only, never an import of `gui` or `clearwater.app.main`. EDIT only if round 0 names the need (origin WP4.1, extended by WP4.2): `src/clearwater/app/composition.py` (as proposed in WP4.1's draft; final per its accept), with the builders `photo_reader()`, `photo_writer()`, `correction_methods()`, `backend_selector()` and `export_jobs(...)`, only to add a Qt-free builder for the GUI's video source, sink and cache if WP4.2 left none (round 0 names it). Tests: `tests/test_app_startup.py`, `tests/test_app_leftovers.py`, `tests/test_app_analysis_adapter.py`, `tests/test_app_activity.py`, `tests/test_app_preview_fft.py`, `tests/test_app_wiring.py` (the G-matrix), `tests/test_app_v7.py`, `tests/test_app_v8_v18.py`, `tests/test_app_deps.py`, `tests/test_io_video_spawn.py`. `docs/reports/wp4.3-application-wiring.md`; `docs/proofs/wp4.3-ledger.md`. EDIT, granted per question 1: `src/clearwater/gui/settings_dialog.py` (WP3.20/WP3.20R: DR-52, the `catalog` argument, DR-61), `tests/test_gui_settings_dialog.py` (WP3.20: DR-52's deletion and the default-rule tests), `src/clearwater/gui/engines.py` (WP3.16, EDITED by WP4.1 (as proposed in WP4.1's draft; final per its accept): `default_engines()` takes `photo_source` and `methods` from the root, keeps `stub_era_select_backend` for WP4.3 and keeps the video members on stubs, which WP4.2 draft question 3 leaves to WP4.3. Here the S1 stand-in is removed and the video members swapped, question 11), `tests/test_gui_status.py` (WP3.16: the two S1 tests, question 11), and any WP4.1 or WP4.2 test that pins `default_engines()`'s stub video members or its `stub_era_select_backend` (changed with that reason, listed at round 0), `src/clearwater/gui/preview.py` and `src/clearwater/gui/render_worker.py` (WP3.16: DR-68, question 6), `src/clearwater/io/video/pipes.py` (WP3.9, the AD-23 module: the spawn helper, question 9) and its call sites `capability.py`, `encode.py`, `verify.py` (WP3.10), `decode.py` (WP3.9), `probe.py` (WP3.7; DR-58 (b)), `docs/reports/wp3.20-settings.md` (an erratum appended, DR-52). EDIT only if the round-0 table names the need and the dispatcher grants it: `src/clearwater/gui/shell.py` (WP3.16: the start-up device text, question 5; panels attached before `show()` if `run` gives no hook) and `src/clearwater/gui/__init__.py` (only under question 11's alternative), `src/clearwater/gui/jobs.py` (WP3.16: DR-44 (c), question 8), `src/clearwater/gui/batch_panel.py` (WP3.19: DR-50's per-row update, only if the re-measure fails). NOT owned: `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN), `gui/contract.py` and `gui/analysis_service.py` (frozen seams; a change is a CHARC ruling), `jobs/export_seam.py`, `jobs/export.py`, `jobs/safe_write.py`, `analysis/`, `cache/`, `config/`, `core/`, `methods/`, `color/`, `io/photo/`, the other `gui/` modules (`timeline.py`, `parameter_panels.py`, `preset_panel.py`, `export_panel.py`, `export_service.py`, `imaging.py`, `messages.py`, `session.py`, `sources.py`); WP4.1's composition root and headless runner (consumed; EDIT only by grant, question 2); `tools/`; `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/fixtures/`, `tests/gui_support.py`; every existing test file not named above; `pyproject.toml`, `uv.lock` (question 2). |
| Interfaces provided | `clearwater.app.main`; `python -m clearwater`. No frozen interface changes; the `ClipAnalysis` and `ExportJobs` seams are implemented, not changed. The one additive gui signature is `install_settings_dialog(..., catalog=None)` (DR-52's "start-up detection gets a catalog argument"). |
| Interfaces consumed | IF-2 (`select_backend`, `free_device_bytes`, `memory_estimate_bytes`; the AD-29 device extension `release_fft_plans` through a consumer-side Protocol), IF-5 (`VideoSource`, `VideoSink.capabilities`), IF-6, IF-7 (`DiskProxyCache`: `lookup`, `proxy`, `set_limit_bytes`, its crash clean-up at open), IF-8 (`Progress`, `JobResult.device`), IF-9, IF-10 (`Settings.output_folder`, `cache_limit_bytes`, `force_cpu`, `video_encoder`); the gui contract (`ShellWindow`, `ShellContext`, `Engines`, `Session`), the `ClipAnalysis` seam, the export seam. |
| Consumers | WP5.1 (the acceptance suite drives the shell; G and V legs), WP5.3 (the visual review pack runs the application), the owner (the program). |
| Hardware flags | **EXCLUSIVE** for the V7 re-measure (timing figures, plan 4.3), the footage legs (V18 and V8 on GX011627 through `tools/local_config.find_footage_file`, read-only), and the full suite. `gui` (offscreen), `gpu`, `footage`, `slow` as their tests need. At least 5 GB free before a heavy run; one heavy job at a time; a figure from an ungranted or a parallel-worker run is not a figure of record (AD-28). |
| Out of scope | Changes to `interfaces/`, the gui contract or the seams (AD-20: a STOP); the composition of the photo and video paths themselves (WP4.1, WP4.2; DR-67's `device_backend` test is WP4.2's); a device-wide memory figure in the GUI (question 7); a persistent encoder-capability cache (question 4); chapter grouping and G11 (v2); N6 and any timing of the export (WP5.2); an installer, a packaged executable or a CI service; the look check and V2 (owner, WP5.3); decoding, parsing or logging any `gpmd` packet, IMU or GPS data; reading or logging any location tag. |
| Debt and decided items | Register on main `cffd243` (table below): CLOSES DR-52, DR-62, DR-68, DR-35 (c), DR-44 (c), DR-61, DR-51 (a), DR-58 (b) (with question 9's touch), DR-50 (by measurement, or the per-row fix); CONSUMER NOTE DR-35 (a), DR-47, DR-45 (a), DR-67, DR-34 (c); a Question DR-69 (7); NOT REACHED the rest listed. Decided items carried in: the WP3.18 mapping notes (task 4), WP3.17's "keep `"c3"` first in `engines.methods`", WP3.20's "create the real `DiskProxyCache` with `Settings.cache_limit_bytes`", WP3.16's S1 removal (question 11), WP3.19's "the panels never call `setEnabled` on `actions.export`". |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict and the full suite per the fill's GATE_CHECKS at dispatch (the two-leg gate) green in a granted window, every existing test unchanged or changed only as named in this brief or by a CHARC ruling; `uv run python -m clearwater` starts the shell on the real engines (smoke test under `QT_QPA_PLATFORM=offscreen`, the event loop ended by a timer); every G row of the G-matrix checked on the running shell; V7 re-measured with the real engines in an EXCLUSIVE window, every scenario at or under 100 ms or the failing scenario a STOP with its figure; V8 within AD-11 and V18 shown on the running shell; the footage-absence test green; each register row disposed as the table says; Reviewer A converged. |

### Register rows (main `cffd243`)

| Row | Signal / trigger naming this package or its files | Disposition and ground |
|---|---|---|
| DR-52 | "WP4.3: replace the stand-in with WP3.10's function, delete the stand-in and its mirror test; start-up detection gets a catalog argument"; amended: the report errata "WP4.3's swap fixes all three" | **CLOSES**: `interim_resolve_encoder` deleted, `capability.resolve_encoder` the default of `settings_dialog` and `install_settings_dialog`, `test_interim_rule_matches_the_wp310_rule` deleted, the `catalog` argument added, the erratum (the four candidate SHAs `262d24f`, `5d34e9e`, `1171731`, `639101c`; `cache_limiter=None` in the public API) appended to `docs/reports/wp3.20-settings.md`; a test that the dialog surfaces WP3.10's `VideoEncodeError("unavailable")` as the D74 reason. |
| DR-62 | "WP4.3 (the export panels and the GUI sequencing): serialise a recompute against a running export of the same clip (refuse, queue or wait, AD-7 / AD-15), with a test that drives both" | **CLOSES** by task 5 (question 8 picks the form); the test drives a real export and a GUI recompute of one clip in both orders. |
| DR-68 | BINDING: "WP4.3's brief: release plans at a preview boundary (clip change / unload) and count them in the GUI's memory reading; a test shows the pool returns to its pre-preview figure after the boundary" | **CLOSES** by task 7 (question 6 defines the boundary and the reading); `gpu` test. |
| DR-69 | BINDING: "WP4.3: if the GUI shows a job's device-wide total, an IF-8 or IF-2 extension is a CHARC decision at that brief (AD-20 STOP); otherwise the figure stays bench-only and this row stays open" | **Question 7** (recommended: the GUI does not show it; then NOT REACHED, the row stays OPEN as the record of the gap). |
| DR-35 (c) | "`remove_leftovers` deletes a live job's temporary if called while a job runs ... (c) stays with WP4.3's start-up clean-up before any job" | **CLOSES**: the cleanup ends before any job can start (task 3; a test that no export or batch job starts while it runs). |
| DR-35 (a) | "Trigger for (a): WP4.3 shows the refusal text" | **CONSUMER NOTE**: a G10 leg shows the reserved-name refusal (`NUL` stem) as the export panel's readable message through the real engine; renumbering stays the owner's word. |
| DR-44 (c) | "(c): WP4.3 real-engine wiring or any job that blocks past cancellation" | **CLOSES** by task 8 (question 8): measured with the real jobs at close; fixed in `gui/jobs.py` only if a real job outlives `SHUTDOWN_TIMEOUT_S`. |
| DR-50 | "WP4.3's V7 re-measure with the real engines and a queue of a few hundred items; a per-row update if it fails" | **CLOSES** by the task 10 scenario (300 items); a per-row update in `batch_panel.py` only if it fails. |
| DR-51 | "WP4.3 (the real adapter replaces the stub; the oracle gains an intermediate-state check if the drag lane is touched again)" | (a) **CLOSES** for the product path: the real adapter's `statistics` gates on its own completed-run state (WP3.18 mapping), with a reader-versus-new-`run` race test on the real adapter; (b) NOT REACHED (`timeline.py` is not touched). |
| DR-61 | "The next settings-dialog touch (WP4.3): format the detail with a fallback, re-evaluate OK on `set_settings`, de-duplicate banners" | **CLOSES** in the same touch as DR-52, with a test each for (i)-(iii). |
| DR-58 (b) | "WP3.7's `probe.py` inherits `FFREPORT` ... (b) WP3.7's next touch clears `FFREPORT` for the probe" | **CLOSES** if question 9's touch of `probe.py` is granted: the spawn helper carries `tool_env()`'s environment; a test with `FFREPORT` set. (a) several GPUs: NOT REACHED (owner hardware, one GPU). |
| DR-47 | "WP3.18 (the GUI's cancel wiring) and WP4.2 (end-to-end cancel): (a) a one-shot guard on the job callable" | **CONSUMER NOTE**: the adapter runs each job the engine returns at most once and never two at once (a test); `analysis/engine.py` is not owned, so (a)-(c) stay with WP4.2. |
| DR-45 (a) | "the first consumer that closes a stream from another thread" | **CONSUMER NOTE**: every stream the adapter or the preview's frame worker opens is iterated and closed by one thread (a test); not reached. |
| DR-67 | WP4.2's binding row (`device_backend` on source, sink and engine) | **CONSUMER NOTE**: the GUI's exports and analysis go through WP4.2's composition unchanged; WP4.2's test stands. |
| DR-34 (c) | "a second same-folder `configure_logging` call updates only the level" | **CONSUMER NOTE**: `configure_logging` is called once per process (the shell's `start_up`); the app adds no second call. |
| DR-43, DR-49, DR-56, DR-57 (d), DR-36, DR-2, DR-64, DR-65, DR-70, DR-71, DR-72, DR-73, DR-74 | Their triggers name other modules or packages (`io.photo`, a method schema, an owner audio report, `jobs/export.py`, `export_bench.py`, `core/backend.py`, the N6 text, the suite cost) | **NOT REACHED**: none of their files is touched here. DR-49's ground is checked on the running shell: c3 and ancuti2018 resolve at 6 decimals or fewer. |

## Task ladder

1. **Read and rebase.** `uv sync`. Read WP4.1's and WP4.2's accept records and their composition
   root, then list what is still a stub in the product path after them (Engines members, the
   S1 stand-in, the export panels' engine, the timeline's factory). No product code yet.
2. **Round 0 yield: the design table**, in the ledger, before product code:
   - the module layout of `clearwater.app` (question 2) and its import rule;
   - the start-up sequence step by step, with the thread of each step and each step's duration
     measured on this laptop: `app_locations()`, the settings read, `DiskProxyCache` open on a
     20 GB cache (crash clean-up and eviction, WP3.12), the leftover scan, `detect_capabilities()`
     (about 2 s), the GPU probe (CuPy import, `_probe_gpu` through `select_backend`). Also how
     the cache gets `Settings.cache_limit_bytes` when `MainWindow`'s `start_up` reads the settings;
   - the leftover folder set and the journal's shape (question 3: a persistent-data shape, so
     copy to CHARC);
   - the analysis adapter's mapping, row by row against WP3.18's table and errata 1 and 5
     (task 4);
   - the DR-62 design (question 8), the DR-68 boundary (question 6), the DR-44 (c) measurement
     (question 8);
   - the spawn helper and every spawn site in `src/` (question 9);
   - the panel install order; the G-matrix; the V7 scenarios (question 10); the V8 and V18 legs
     (question 12);
   - every existing test the plan changes or deletes, with its reason;
   - the `scripts/cell_depth.py` figure your dispatcher gives you.
   YIELD. Any choice the brief leaves open is a STOP.
3. **Entry point and start-up.** `main()`: one `QApplication`, `app_locations()` (AD-25 (a);
   nothing else reads the environment for a folder), the real engines from WP4.1/WP4.2's root,
   `MainWindow(engines, locations)`. The GUI's `Engines` are wholly real: the photo legs as WP4.1
   composed them, and `video_source`, `video_sink` and `cache` swapped HERE together with the
   analysis adapter (WP4.2 draft question 3 leaves them on the stubs for WP4.3). The cache is the
   real `DiskProxyCache` at `locations.cache_dir` with `Settings.cache_limit_bytes` (WP3.20 note)
   and the registered codec, keyed as the root keys it (DR-41 note in WP4.2). Then `install_parameter_panels(window)` with `"c3"` first in
   `engines.methods` (WP3.17); `install_timeline(window, <adapter factory>)`;
   `install_export_panels(window, <guarded exports>)`; `install_settings_dialog(window,
   resolve_encoder=resolve_encoder, catalog=<the start-up catalog>)`. Then the start-up work
   (question 4):
   - (a) **leftover cleanup** (D85, V11) over the folder set of question 3 and the cache root.
     The cache's own crash clean-up is its constructor's; never a folder outside the set. It
     completes before any export or batch job can start (DR-35 (c)), and the removed and failed
     files are logged (N9);
   - (b) **encoder detection** into the catalog off the interface thread, so the first settings
     dialog opens on a known result;
   - (c) **graphics-card detection** off the interface thread. Its reason reaches the status bar
     (AD-9, question 5) and the log.
   CHECK: `python -m clearwater` under offscreen QPA reaches the event loop and exits 0; V7 holds
   during start-up; nothing in start-up writes outside app data, the cache root, the journal's
   folders and the log.
4. **The analysis adapter** (`ClipAnalysis` over `AnalysisEngine`, WP3.18 report "The mapping for
   WP4.3" as corrected by "Erratum at the gate"):
   - The factory builds the adapter only; the engine is built lazily in the first `run` on the
     worker thread.
   - **Live settings by closure**: the factory reads `Settings` (`force_cpu`) through a provider
     over the session (erratum 5; the seam is unchanged).
   - **Kept job priority**: when `retarget` gets a job back from `set_parameters`, the adapter
     keeps it and returns False. The next `run` offers the latest parameters, then runs the kept
     job and clears it (erratum 1). A test against the REAL engine shows that the kept job ends
     under the latest parameters; if it does not, the adapter runs one more job.
   - **Its own pts list** (F-2): `pts()` returns a list the adapter keeps, refreshed off the main
     thread, never `DiskProxyCache.lookup` on the main thread.
   - `statistics` stays None until a full `run` completes under the latest parameters.
   - Cancel goes through the job handle; `analysis.CANCELLED` returns; other failures raise with
     the engine's text.
   CHECK: the WP3.18 seam rules (threading list in `analysis_service.py`) hold on the real
   adapter; the A-B-A burst of WP3.18 B pass 1 #1 never completes under a kept job; V18 (task 10).
5. **DR-62: one activity per clip.** Per cache key, a GUI analysis or recompute and an export
   (single or batch item) of the same clip never run their engines at once (question 8 picks wait
   or refuse). The guard lives in `clearwater.app` (the adapter and the `ExportJobs` wrapper share
   it); no `jobs/` or `analysis/` change. AD-15 is unchanged, and the gate stays the panels'
   (`ActivityGate`). CHECK: one test drives both orders with the real engines on a fixture clip;
   a cancel while waiting returns CANCELLED (or the panel's cancelled state) with nothing written;
   the cache entry stays complete and consistent (V17 reopen skips the decode pass).
6. **Settings dialog: DR-52 and DR-61** (the rows' text is the specification). CHECK: WP3.20's
   and WP3.20R's tests pass, except the deletion DR-52 orders; the DR-61 cases fail on the base.
7. **DR-68: the preview's FFT plans.** cuFFT plans are per thread, so the release runs ON the
   preview worker's thread (`clearwater-preview`) at the boundary of question 6. It goes through
   ONE consumer-side `runtime_checkable` Protocol in `clearwater.gui` (AD-29: "same names and
   signatures as `CupyBackend`'s, with a test that `CupyBackend` satisfies it and `NumpyBackend`
   does not"); `clearwater.gui` still imports no `cupy` and touches no `.xp`. CHECK: the `gpu`
   test reads the reading of question 6 before a 1:1 render of a 4K frame (short side ≥
   `FFT_MIN_SHORT_SIDE`, sigma ≥ `FFT_MIN_SIGMA`), after it, and after the boundary; it is back
   at its pre-preview figure after the boundary; a planted controller without the release fails
   by name.
8. **The spawn helper (AD-23 extended; Windows-specific code under N1, question 13).**
   One helper used by every `subprocess.run`/`Popen` site
   in `src/clearwater` (today: `capability.py` 89, `decode.py` 171, 330, 344, `encode.py` 879,
   `probe.py` 127, `verify.py` 225). It sets `creationflags=CREATE_NO_WINDOW` on Windows (0
   elsewhere) and the `FFREPORT`-free environment of `tool_env()` (DR-58 (b)). CHECK: an AST
   test finds every spawn call in `src/` and requires the helper; a Windows test asserts the
   flag; WP3.7, WP3.9 and WP3.10 tests pass unchanged. The `io/video` module-set pin
   (`test_io_video_probe_rules.py`) is unchanged, so no new module there.
9. **DR-44 (c): close with real jobs.** Measure how long each real job takes to end after cancel,
   from close: an analysis mid-decode, an export mid-encode, a batch item. If every one ends
   within `SHUTDOWN_TIMEOUT_S` (5 s), DR-44 (c) closes as measured (the figures in the report).
   If not, `gui/jobs.py` detaches the callbacks of a job still running at close (question 8),
   with a test.
10. **Tests and the V legs.**
    - The G-matrix (`tests/test_app_wiring.py`): one or more tests per G row on the running
      shell built by `main`'s own builder over tmp app-data and the WP2.3 fixtures
      (`tests/fixtures/stills/*`, `tests/fixtures/video/*.mp4`, `tests/fixtures/files/dng`). G1
      open; G2 split; G3 the c3 schema's panels, live preview; G4 scrub proxies, then full
      resolution on release; G5 progress and cancel; G6 presets; G7 batch skip-and-log; G8
      progress and cancel with no partial output; G9 with V7; G10 the HLG/PQ refusal,
      truncated, untagged, DNG refusal, DR-35 (a); G11 v2 (named, no test); G12 every setting,
      force CPU giving `CPU: forced`; G13 persistence over two window lifetimes.
    - **V11** leftover leg: a planted temporary in a journal folder and in the output folder is
      removed at the next start; a non-matching file is kept.
    - **The footage-absence test** (question 3): with the sources in a stand-in footage folder
      under `tmp_path` and the outputs elsewhere, start-up never scans that folder (a `scandir`
      spy) and a planted temporary-pattern file there survives. When `clearwater.local.toml`
      names the real footage folder, the computed folder set contains no path inside it; that
      folder is never scanned or written.
    - V8 and V18 (question 12); `tests/test_app_deps.py`: `clearwater.app` is the only package
      that imports `clearwater.gui` and `clearwater.methods` or `clearwater.analysis`; the one
      edge into it from below is `gui/engines.py` -> `clearwater.app.composition` (as proposed in WP4.1's draft; final per its accept), pinned by WP4.1's static test;
      importing `clearwater.app` or `clearwater.app.composition` loads no PySide6 (only
      `clearwater.app.main` and modules it alone imports may); `clearwater.app` imports no
      `cupy`/`cupyx`; `tests/test_gui_deps.py` still passes unchanged.
11. **Review loop** (below), then the full suite in a granted window.
12. **The V7 re-measure (EXCLUSIVE, LAST; question 10).** The dispatcher grants each window after
    the review loop; do not start it unasked. Each scenario's longest main-thread gap, its p99
    and its tick count go in the report beside the stub-era figures (WP3.16, WP3.18 12-39 ms,
    WP3.19 11-13 ms). Send `WINDOW RELEASED: <summary>` at the end.

## Declared operating envelope

Windows 11; Python 3.12; PySide6-Essentials 6.12 as locked; FFmpeg 9.0.2 (gyan) with
`hevc_nvenc` and `libx265`; the RTX 4070 Laptop GPU (8 GB) or the CPU fallback; the Ryzen 9
7940HS, 32 GB RAM. ONE application process per app-data folder (two processes sharing the cache
are outside WP3.12's envelope); one export activity at a time (the panels' `ActivityGate`) plus
the open clip's analysis; inputs within WP3.6's, WP3.7's and WP3.9's envelopes. Tests run with
`QT_QPA_PLATFORM=offscreen` over app data under `tmp_path`, never the real `%APPDATA%`. Out of
envelope: several GUI processes, a second GPU, other operating systems (portable code, not run
there), a pure-Python method holding the GIL (WP3.16's 216-796 ms figure stays out of
envelope).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (Codex `-m gpt-6.1-sol -c model_reasoning_effort=high`, WSL transport, probe
  first), run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\rN\`; ledger `docs/proofs/wp4.3-ledger.md`.
  Copy the runner and prompt shape from `...\wp3.21\r2\` (`run_review.sh`, `review-prompt.md`).
  The banner must read `gpt-6.1-sol`; a round with another pin is void. Exclude `docs/proofs`
  with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - wiring: every Phase 3 panel attached once, to the real engines; no stub left on a product
    path; `"c3"` first; nothing reads app-data folders except through `clearwater.config`;
  - start-up: the order, the thread of each step, and no job before the cleanup ends; the
    cleanup's folder set (never a source folder as such, never the footage path); the journal
    written before a temporary exists and cleared after commit or abort; what a crash at each
    step leaves;
  - the analysis adapter against the WP3.18 seam's threading rules and mapping (kept-job
    priority, its own pts list, live settings, `statistics` gating, no job run twice or
    concurrently);
  - DR-62 in both orders; cancel while waiting; the cache entry after each order;
  - DR-68: the release on the right thread at every boundary; the Protocol (AD-29); no `cupy`
    in `gui` or `app`;
  - the spawn helper at every spawn site; DR-52 and DR-61 against their rows' text;
  - close: no callback after the window is gone (DR-44 (c));
  - nothing in `interfaces/`, the contract, the seams or unowned files changed; no `gpmd`, IMU,
    GPS or location data read; no write to the footage folder.
- Reviewer B is the orchestrator's seat pass on the merge candidate (Codex, the same pin).

## Notes for the cell

- **Yields.** Task 2 (round 0): the table, then YIELD before product code; question 2's module
  names and question 3's journal shape are CHARC tripwires, so your dispatcher copies the table
  to CHARC. After each review round: END YOUR TURN as soon as round N's verdict is adjudicated,
  BEFORE remediating; make NO change in the turn that adjudicates a round. Your dispatcher gives
  you the `scripts/cell_depth.py` figure at every yield; record it in the ledger. ~250K is the
  evaluation point ("REVIEW ONLY this turn" when told); STOP at ~400K.
- **Windows (X5, AD-28).** Heavy work runs ONLY in a window the dispatcher grants: the V7
  re-measure, the footage legs, the full suite, any `gpu` run of more than your own targeted
  tests. Ask for each with `WINDOW REQUEST: <what, how long>`. One heavy job at a time; at least
  5 GB free before a run. The suite runs in the background with `QT_QPA_PLATFORM=offscreen`,
  output under `work/`, with foreground poll-wait calls on its done marker (a reaped run is not a
  result). The two-leg gate (from Git Bash, `PYTEST_ADDOPTS` unset):
  `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/<run>-parallel`
  then `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/<run>-serial`.
  Timing figures come only from serial runs. Send `WINDOW RELEASED: <summary>` after each window.
- **Footage.** Read-only at `C:\Users\rwsmy\clearwater-footage\`, only through
  `tools/local_config.find_footage_file`. Never a basetemp, an output folder, a journal entry or
  a cleanup target there. Every output goes under `work/` or `tmp_path`.
- **Return report** = your FINAL message to your dispatcher by your messaging tool, under about
  70 lines: the start-up sequence with its measured steps; the wiring table (panel, engine,
  test); the G-matrix; V7 per scenario beside the stub-era figures; V8 and V18 figures; the DR
  dispositions; the gates; the Reviewer A rounds and verdict; open items.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20), `gui/contract.py`,
  `gui/analysis_service.py`, `jobs/export_seam.py` or a file not owned or granted; a dependency;
  OS-specific code beyond AD-23's extension; a V7 scenario over 100 ms that the owned files
  cannot fix; V8 outside AD-11; a cleanup target outside question 3's set or inside the footage
  folder; anything that relaxes D85, D74 or AD-15 (owner-reserved); a need to show the job's
  device-wide memory (DR-69, AD-20); any need to decode a `gpmd` packet or read a location tag;
  the round-0 table showing a choice the brief left open.
- **Working rules:** commit inside the worktree by pathspec with `git -c core.autocrlf=false
  commit -m "feat(wp4.3): ..." -- <paths>`, with a `Co-Authored-By:` footer naming your model;
  every committed blob LF. Never `git stash`; never a bare `cd`; never post to a mailbox; never
  `git clean -x`. Gates: ruff check, ruff format --check, mypy strict, the full suite (in a
  window); no harness gate (no `scripts/`, `.claude/`, kernel doc or `tests/harness/` change).
  Report `docs/reports/wp4.3-application-wiring.md` (claims, evidence paths, limits, the V7
  figures beside the stub-era figures).
- **Layering tests in every light run (AD-29):** `tests/test_core_deps.py`,
  `tests/test_color_deps.py`, `tests/test_io_video_decode_rules.py`,
  `tests/test_analysis_deps.py`, `tests/test_gui_deps.py`, plus your `tests/test_app_deps.py`.

## Questions for CHARC (recommended answer first)

1. **Ownership grants.** Recommended: grant now the EDITs of `gui/settings_dialog.py` and
   `tests/test_gui_settings_dialog.py` (DR-52, DR-61), `gui/engines.py` and
   `tests/test_gui_status.py` (question 11), `gui/preview.py` and `gui/render_worker.py`
   (DR-68), `io/video/pipes.py` with the five spawn-site files (question 9), and the erratum to
   `docs/reports/wp3.20-settings.md`. Grant `gui/shell.py`, `gui/__init__.py`, `gui/jobs.py`
   and `gui/batch_panel.py` at round 0 only for a named need (questions 5 and 11, DR-44 (c),
   DR-50).
   Alternative: grant everything now (a wider review surface, fewer yields).
2. **New modules (tripwire).** Recommended: the package `clearwater.app` (plan 8.1, "Entry point
   and start-up"), with `main.py`, `startup.py`, `analysis_adapter.py` and `activity.py`, plus
   `src/clearwater/__main__.py` so `uv run python -m clearwater` starts the program. The adapter
   cannot live in `clearwater.gui`: "`clearwater.analysis` (WP3.11) is not imported here or
   anywhere in `clearwater.gui`" (`analysis_service.py`), and `test_gui_deps.py` forbids
   `clearwater.methods` there. This matches WP4.1's draft (WP4.1 creates `clearwater.app` with `__init__.py` and
   `composition.py`, Qt-free, `__init__.py` never importing `gui`; the runner
   `tools/headless_export.py`; as proposed in WP4.1's draft; final per its accept). So `app/__init__.py` is an EDIT here, and
   `main.py` is the only module that loads Qt, `analysis_adapter.py`, `activity.py` and
   `startup.py` are Qt-free (they satisfy the gui seams structurally), and `__main__.py` imports
   `clearwater.app.main`, never through `app/__init__.py`. No `[project.scripts]` entry and no
   `pyproject.toml` edit: no installer or packaged executable is planned (CLAUDE.md).
   Alternative: a console script `clearwater = "clearwater.app:main"` (a `pyproject.toml` grant;
   no dependency).
3. **The leftover folder set and the journal (tripwire: a persistent-data shape).** WP3.13 Q3 is
   RULED: "the configured output folder plus the folders of a small journal of in-flight writes".
   Recommended:
   - The journal is a JSON file in `config_dir` (`clearwater.config` paths; written with
     `config.atomic`'s atomic write, `format_version` 1). It holds one entry per job: the
     destination folder, which is `Settings.output_folder`, or the source's folder under D34's
     default.
   - The app's `ExportJobs` wrapper adds the entry BEFORE the job runs and removes it after the
     job returns. A crash leaves the entry.
   - Start-up scans `Settings.output_folder` (the commission's "working folder") and the
     journal's folders with WP3.13's `remove_leftovers` (unchanged), then clears the scanned
     entries. The cache root is cleaned by `DiskProxyCache`'s own open.
   - It never scans a folder only because a source lies there, and never the developer footage
     folder. Tests never export into it, and the footage-absence test (task 10) proves that.
   - A journal folder that is a source folder under default settings is still scanned: that is
     D85 for the owner's own exports, and refusing it would relax D85 (owner-reserved).
   Alternatives: (B) the output folder only, with no journal. That misses every default-location
   crash: D85 relaxed, so it is the owner's call. (C) The journal records exact temporary paths,
   and only those files are deleted. That is tighter, but it is a second deletion rule beside
   WP3.13's.
4. **Start-up threading and caching.** Recommended:
   - The cleanup runs synchronously before `window.show()`, so "before any job" holds by
     construction. Its scan is a few `scandir` calls; the round 0 measures it, and over 100 ms it
     becomes a gated first job instead.
   - The `DiskProxyCache` open is timed in round 0 on a full 20 GB cache, and moves off the
     interface thread if it is over 100 ms.
   - Encoder detection and the GPU probe run as two start-up jobs in `window.jobs`. The catalog's
     job is the first `EncoderCatalog.start`.
   - NO persistent capability cache: detection runs per process, about 2 s, off the interface
     thread, so no new persistent file.
   Alternative: a capability cache in app data keyed by the FFmpeg path and mtime. That is a
   second persistent shape, for a 2 s saving.
5. **The AD-9 device text.** WP3.16's question 4 ruled "show `Device: ` plus the reason verbatim
   ... a device-name accessor in `clearwater.core` (WP3.1's module; a later package)".
   Recommended:
   - Keep the verbatim reason (`GPU`, `CPU: forced`, `CPU: estimate ... exceeds free ...`) with
     no core change. Before a file is open, the start-up probe's reason shows as `Device: <reason>`
     in place of `Device: -`, which needs the conditional `shell.py` grant (question 1).
   - Each export job's log line names `JobResult.device` (the app wrapper logs it).
   - The GPU's name ("RTX 4070 Laptop") is NOT added.
   Alternative: an additive read-only `device_name` on `CupyBackend` (an AD-29 device extension,
   a `core/backend.py` grant, a consumer Protocol in `app`) and "GPU: <name>" in the status bar
   only, never in provenance.
6. **DR-68's boundary and "the GUI's memory reading".** The GUI has no memory display. Its memory
   reading is the free-device figure `select_backend` reads on every call (`free_device_bytes`:
   the driver's free plus the pool's free blocks). Plan bytes held by the preview's thread lower
   that figure for the next selection in the same process (an export, a batch item, the next
   clip).
   Recommended:
   - The boundaries are a source change or unload, the shell's close, and before an export or a
     batch job of the GUI process selects its backend.
   - The release runs on the preview worker's thread as a task the latest-wins worker cannot drop
     (round 0 shows how).
   - The test asserts `free_device_bytes()` back at its pre-preview figure, within one pool block,
     after the boundary.
   Alternative: release after every FFT-route render (simpler; it rebuilds plans on each 1:1
   render, a V7 cost).
7. **DR-69 (BINDING Question).** Recommended: the GUI does NOT show a job's device-wide memory
   total. No G row or AD asks for it; AD-9 asks for CPU/GPU and the fallback reason, which the
   status bar and the job log line give. So no IF-8 or IF-2 extension: DR-69 NOT REACHED, and it
   stays OPEN as the record of the gap, the figure bench-only. Alternative: show it. That is an
   IF-8 `JobResult` (or IF-2) extension, an AD-20 STOP for CHARC's decision before dispatch.
8. **DR-62's form and DR-44 (c).** Recommended for DR-62: WAIT.
   - The second activity on a clip waits on its own worker thread for the first to end. It is
     cancellable and reports "Waiting for the other job on this clip", so neither is refused and
     no statistics are lost; this is AD-7's "absorbed, never cancelled" spirit.
   - The guard is one lock per cache key in `clearwater.app`.
   Alternative: REFUSE the second with a readable G10 message (simpler; the user retries).
   For DR-44 (c), recommended: measure first (task 9); edit `gui/jobs.py` (detach the callbacks
   of a job still running at close and log it) only if a real job outlives 5 s.
9. **The spawn helper's place (AD-23 extended).** Recommended: `io/video/pipes.py`.
   - It is the AD-23 module, it imports nothing from the package, and `probe.py` cannot import
     `capability.py` without a cycle (`capability.py` imports `probe.find_tool`).
   - The helper returns the `Popen`/`run` keyword arguments (`creationflags`, `env` without
     `FFREPORT`). `capability.tool_env` stays as a name and delegates to it.
   - No new `io/video` module, so the module-set pin is unchanged.
   Alternative: a new `io/video/spawn.py`, which changes `test_io_video_probe_rules.py`'s pinned
   set (a test change to rule).
   The flag itself is Windows-specific code: question 13.
10. **The V7 scenarios (EXCLUSIVE, real engines, the WP3.16 10 ms probe).** Recommended:
    - (a) GX011627 analysis on the GPU while the timeline updates (F-2 included);
    - (b) scrubbing during that analysis;
    - (c) a File > Export of GX011627;
    - (d) a batch of 300 small synthetic stills under `tmp_path` (DR-50);
    - (e) a 1:1 4K preview render (the FFT route) during (c);
    - (f) start-up.
    Each figure is the longest gap with its p99, bound 100 ms. Alternative: (a) to (d) only
    (shorter; no start-up or FFT-route figure).
11. **The stub era's removal.** WP3.16 accept: "S1's `default_engines` "c3" adapter is removed
    by WP4.3". Recommended:
    WP4.1's draft (question 3) has `default_engines()` call the root for `photo_source` and
    `methods`. It keeps `stub_era_select_backend`, pinned by
    `default_engines().select_backend is stub_era_select_backend` in `tests/test_gui_status.py`,
    and leaves the video members on stubs (as proposed in WP4.1's draft; final per its accept). WP4.2's draft question 3 leaves the GUI's video
    source, sink and cache to WP4.3.
    - Delete `stub_era_select_backend` and `STUB_ERA_METHOD_ID`; `default_engines()` uses the
      root's `backend_selector()` (the methods are real, so the stand-in has no job).
    - `default_engines()` gets its video source, sink and cache from the root too, with
      `locations` and the cache limit passed in (keyword-only, defaulted). `clearwater.app.main`
      builds the engines through it, then `MainWindow(engines, locations)`, the installs and
      `show()` itself, as `shell.run` does but with the panels attached before `show()`; so
      `shell.run` and `gui/__init__.py` are not edited.
    - Delete `tests/test_gui_status.py`'s two S1 tests
      (`test_stub_era_adapter_estimates_an_unknown_method_as_c3`,
      `test_default_engines_select_cpu_forced_with_the_real_selection`); keep `stub_engines`
      for tests. The removed node IDs are explained by the diff (GATE_CHECKS).
    Alternative: delete `default_engines` and make `shell.run`'s `engines` required (the
    `shell.py` and `gui/__init__.py` grants; no gui-to-app edge at all).
12. **The V8 and V18 legs on the running shell.** Recommended:
    - V8, photo: the preview the shell shows (fit, k > 1, and 1:1) against the exported 16-bit
      PNG read back and `imaging.downscale`d by the same k, within AD-11 AS AMENDED 2026-10-21 (k = 1 EXACT; k > 1 mean <= 1/255, p99 <= 2/255 at
      k = 2 and <= 4/255 at k = 4, max recorded, never asserted; CHARC addendum (1)).
    - V8, video: the shell's rendered frame at a pts against `downscale(render(full frame))`
      with the engine's smoothed record at that pts. That is pre-encode, through
      `imaging.preview_export_difference` on the real method and backend; the encoded file is
      V4's, not V8's.
    - V18: GX011627 (footage, EXCLUSIVE) and `tests/fixtures/video/hevc8-bt709-full.mp4`. A
      corrected frame is shown before the analysis completes, and after it the shown statistics
      equal `engine.smoothed_record(pts)`.
    Alternative: video V8 against the decoded encoded output (the encoder masks small errors;
    weaker).
13. **N1: CREATE_NO_WINDOW is Windows-specific code.** N1: "no OS-specific code without the
    architect's approval".
    - Ground: WP3.10 accept line 93 ("**WP4.3:** the shared CREATE_NO_WINDOW spawn helper");
      WP3.9 accept ("CREATE_NO_WINDOW banked to WP4.3 (AD-23 extended by CHARC, `df21ab0`)");
      AD-23's extension ("spawned with the Windows CREATE_NO_WINDOW creation flag (a no-op
      elsewhere) ... implemented once in a shared spawn helper by WP4.3").
    - Recommended: CHARC CONFIRMS that AD-23's 2026-10-21 extension is the N1 approval for this
      one helper, with no new AD row, on three conditions:
      - the flag is set in ONE place (the helper), as `subprocess.CREATE_NO_WINDOW` when
        `sys.platform == "win32"`, else `0`;
      - the fallback on every other OS is `creationflags=0` (subprocess's own default), so the
        same call runs unchanged with the same `FFREPORT`-free environment;
      - tests cover both branches (the Windows value asserted on this laptop, the other branch
        by a monkeypatched platform) and an AST test pins that no spawn site sets
        `creationflags` itself.
    - Alternative: a new AD row recording the approval separately (more paperwork, the same
      code). Without approval: no flag, and a console may flash under the GUI on Windows (the
      WP3.9 limit stays).

## Rulings (CHARC `2c4476d9869df056`, 2026-10-28, verbatim; they GOVERN the Questions section above)

PRIMARY: orchestrator. Thread `159c14fb79ad1aae`, reply to `8c3c624c224c263e` (+ `56e00cce74e65b5c`, `528b3db814b6d2c5`). **RULING PACKET: all four drafts APPROVED with the rulings below; every helper recommendation ADOPTED except where a line says otherwise. Write the rulings verbatim into each brief, commit on `briefs-p4`, ff main; dispatch WP4.1 (opus-high) and WP-T5 (by pace) now; WP4.2 and WP4.3 stay DRAFT until their predecessor's accept plus one revision pass, then FINAL on my word.** Tripwire passes (new package `clearwater.app`, the WP4.3 modules, `python -m clearwater`, the leftover journal) are all GRANTED here.

**Flags.** (1) WP4.2 Q3 narrowing ACCEPTED (N4 ground: the stub analysis over a real source stores ~23 GB for GX011625; the GUI's video legs swap in WP4.3 with the adapter). (2) withdrawn; see 43-Q13. (3) tripwires GRANTED as listed; the `gui/engines.py -> clearwater.app.composition` edge is the ONE gui-to-app edge, pinned by `tests/test_app_deps.py`. (4) the two S1 tests go in WP4.3 (43-Q11); WP-T5's three bodies as T5-Q2/Q3/Q4. (5) noted; my "~30 min" is CORRECTED to the helper's ~12 min projection, W1 replaces it.

**Addendum.** (1) WP4.3's V8 legs cite AD-11 AS AMENDED 2026-10-21 (k = 1 EXACT; k > 1 mean <= 1/255, p99 <= 2/255 at k = 2 and <= 4/255 at k = 4, max recorded never asserted), the same text as WP4.1 line 301. (2) 41-Q3 + 43-Q11 ruled together as recommended: `default_engines()` stays, takes its photo legs and methods from the root in WP4.1, its selector and video legs in WP4.3; `shell.run` and `gui/__init__.py` unedited. (3) WP4.2's DR-35 clause STRUCK.

**WP4.3 (L, opus-high, Codex nets; FINAL after WP4.2's accept + one revision).** Q1 grants as recommended now; `shell.py` (Q5 device text only), `gui/__init__.py` (never, under Q11 as ruled), `gui/jobs.py` (DR-44 (c) only if measured), `gui/batch_panel.py` (DR-50 only on a failed re-measure) at round 0 on a named need. Q2 GRANTED: `app/main.py` (the only Qt-loading module), `startup.py`, `analysis_adapter.py`, `activity.py`, `src/clearwater/__main__.py`; `uv run python -m clearwater`; NO `[project.scripts]` entry, no `pyproject.toml` edit. Q3 GRANTED, persistent-data shape = the leftover JOURNAL: JSON in `config_dir` via `config.atomic`, `format_version` 1, one entry per job (destination folder) added before the job and removed after; start-up scans `Settings.output_folder` plus the journal's folders with WP3.13's `remove_leftovers` unchanged, then clears the scanned entries; never a folder merely because a source lies there, never the footage folder (the footage-absence test proves it); a journal folder that is a source folder under D34's default IS scanned (D85 kept; narrowing it would be the owner's). (B) and (C) not taken. Q4 as recommended (synchronous cleanup before `show()`, measured at round 0, over 100 ms = a gated first job; cache open timed on a full 20 GB cache; detection as two start-up jobs; NO persistent capability cache). Q5 as recommended (verbatim reason, `Device: <reason>` before a file is open, job log line names `JobResult.device`, no GPU name, no core change). Q6 as recommended (boundaries = source change / unload, shell close, before an export or batch job of the GUI process selects; release on the preview worker's thread as an undroppable task shown at round 0; test asserts `free_device_bytes()` back to the pre-preview figure within one pool block). Q7: the GUI does NOT show the device-wide total; no IF-8 / IF-2 extension; DR-69 NOT REACHED, stays OPEN as the record. Q8 DR-62 = WAIT as recommended (one process-local lock per cache key in `clearwater.app`, the waiter cancellable, "Waiting for the other job on this clip"; test drives both orders); DR-44 (c) measure first, `gui/jobs.py` only if a real job outlives `SHUTDOWN_TIMEOUT_S`. Q9 `io/video/pipes.py` as recommended (helper returns the spawn keyword arguments; `tool_env` delegates; the five spawn sites edited; no new `io/video` module; DR-58 (b) CLOSES). Q10 all six scenarios (a)-(f), longest gap and p99 each, bound 100 ms, EXCLUSIVE; a failing scenario = STOP with its figure. Q11 as recommended with 41-Q3 (addendum 2): delete `stub_era_select_backend`, `STUB_ERA_METHOD_ID` and the two S1 tests; `default_engines()` keyword-only `locations` and cache limit; `app.main` attaches panels before `show()`. Q12 as recommended with the AMENDED AD-11 bounds (addendum 1); V8 video pre-encode via `imaging.preview_export_difference`; V18 on GX011627 (footage, EXCLUSIVE) and `hevc8-bt709-full`. Q13 CONFIRMED: AD-23's 2026-10-21 extension IS the N1 approval for this one helper, no new AD row, on the three conditions as written (one place, `subprocess.CREATE_NO_WINDOW` on `win32` else 0; every other OS the same call with `creationflags=0` and the same `FFREPORT`-free environment; both branches tested + an AST pin that no spawn site sets `creationflags`). I add a dated "applied by WP4.3" note to AD-23 at the accept.

**Cost restated:** unchanged from the commission except WP-T5's saving (~12 min per gate, not ~30) and one extra short window for it.
