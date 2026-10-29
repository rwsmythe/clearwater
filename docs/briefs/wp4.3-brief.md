# WP4.3 — Application wiring (dispatch brief, FINAL; REVISION 1)

**Status:** FINAL (CHARC `7c7df3dbe237ceb7`, main `101f181`), with the Q14 split applied: the
AD-23 spawn helper with DR-58 (b), DR-81 (a)(b)(c), DR-76, DR-77 and DR-85's fix are WP4.3a's
(`docs/briefs/wp4.3a-brief.md`, Codex lane). RULED 2026-10-28 (CHARC `2c4476d9869df056`, governing
Questions 1-13) and 2026-10-29 (CHARC `7c7df3dbe237ceb7`, governing Questions 14-24); both rulings
sections are at the end and take precedence over the text above them. DRAFT 2026-10-28, written by a drafting helper
for the orchestrator (generation 16) from CHARC's commission `159c14fb79ad1aae` (section 2, the
WP4.3 bullet: the RULED bounds), drafted on main `6536f60`. Revision 1 is the one pass the draft
owed against WP4.1's and WP4.2's accepts (CHARC status `014ec135d9d64a3e`). Base = the main commit
named at dispatch. Owner decisions: none inside the package. The look check, V2, any spec text and
anything that relaxes a mandatory requirement (D85 among them) are owner-reserved: each is a STOP,
never done here.

**Revision 1 (gen 20, main `cde1cd9`):**
1. Re-based on main `cde1cd9`. The records of WP4.1, WP4.2, WP4.2a, WP4.2b and WP-T5 were
   added. Every "(as proposed in WP4.1's draft; final per its accept)" and every WP4.2-draft hedge in the body
   is now the merged name, with file:line. The merged code matches the drafts. The same hedges
   inside the ruled Questions 2 and 11 are left verbatim and are resolved by this item.
2. Why: the stub state is restated from the merged `gui/engines.py:156-175`.
3. Goal, Depends on, Interfaces: the root's eight builders and `export_jobs`'s keyword-only cache,
   source and sink parameters (`app/composition.py:48-253`); WP4.2a's runner guards and WP4.2b's
   `OutputNameError`.
4. Files owned:
   - `tests/test_app_deps.py` moves from NEW to EDIT. WP4.1's file exists and pins the app module
     set and a no-Qt rule that ruled Q2 contradicts (`tests/test_app_deps.py:89-101`; Q15).
   - New grants: `tests/test_app_composition.py` (DR-84); the third `stub_era_select_backend` test
     in `tests/test_gui_status.py` (Q15); `config/presets.py`, `config/settings_store.py`, their
     tests, `tools/headless_export.py` and one new runner test file (DR-76, DR-77, the start-up
     sibling, DR-81); one additive public name in `jobs/export.py` and `jobs/__init__.py` (Q18).
   - `app/composition.py` is re-grounded (Q16). `gui/__init__.py` is "never", as ruled.
   - The NOT-owned list is extended.
5. Register re-based on `cde1cd9`:
   - Added: DR-75 (REQUIRED test), DR-76, DR-77, DR-81 (a)(b)(c), DR-82, DR-84.
   - DR-52, DR-62, DR-68 and DR-69 were re-read: unchanged since `cffd243`.
   - DR-58 (b)'s 2026-10-29 re-sighting is folded in. DR-47's note is updated for (a), now CLOSED.
   - DR-67, DR-64, DR-65, DR-71, DR-73 and DR-74 leave the table (CLOSED).
   - DR-46 and DR-83 join NOT REACHED. A DR-34 note covers the `config/` touch.
6. NEW finding, executed at the drafting seat on `cde1cd9`: `config/settings_store.py:71` lets
   the same `OverflowError` as DR-77 escape `load_settings`. A `settings.json` whose
   `last_parameters.created` is `0001-01-01T00:00:00+01:00` therefore stops `MainWindow`'s
   `start_up` (`gui/shell.py:148`): the program cannot start. Carried as Q21, with a row for
   CHARC.
7. Tasks:
   - 1: the merged stub list.
   - 2: round-0 items for Q14-Q24.
   - 3: the root's names and the one shared cache.
   - 4: the per-run source on the selected backend (DR-67's pattern) and `expected_frames`.
   - 5: DR-82's pre-plan check in the `ExportJobs` wrapper.
   - 6: DR-76, DR-77 and the sibling.
   - 7: DR-75 at the display call sites.
   - 8: DR-81 (c) at its source and (a)(b) in the runner.
   - 10: DR-75's REQUIRED test, DR-84, the deps edit, V18 under AD-30.
   - 11 and 12: the gate order.
8. Done, Hardware flags, Review loop and Notes follow the current fill:
   - the cell runs its touched files and markers;
   - Reviewer A is Codex `gpt-6.1-sol` / high at the cell's seat;
   - Reviewer B is Codex at the orchestrator's seat;
   - then the ONE two-leg gate runs on the final candidate (fill Part 2, Order, 2026-10-29), as
     GATE_CHECKS at dispatch, which WP-T6 (AD-30's `fullclip`) may amend before dispatch;
   - the runner shape is copied from `wp4.2\r2\`.
9. Questions 14-24 added, each with its recommended answer first. Questions 1-13 and the Rulings
   are verbatim.
10. Lane: stays `implementer-opus-high` with Codex nets. One Codex-eligible sibling is named
    (Q14, recommended).

- Spec **v0.5.6** (v0.5.5's clauses unchanged here; 0.5.6 is the N6 text, DR-64): G1-G13 (G11
  deferred to v2, 0.5.3), D27, D34, D41, D53, D66, D70-D72, D74, D85, D88-D91, D107, D108, D111,
  D113; section 8.2 (encoder line), 8.3, 8.4; N1, N3, N4, N8, N9; V7, V8, V11 (the "leftover
  temporaries removed on next start" leg), V17, V18. Architecture FINAL 1.0: section 1 (modules,
  `app`), 2 ("video preview", "Parameter change (AD-7)"), 3 (IF-2, IF-5, IF-7, IF-8 with its
  "Export seam" paragraph, IF-9, IF-10), 7. AD-1, AD-7 (with its two amendments), AD-9, AD-11
  (V8, as amended 2026-10-21), AD-13, AD-15, AD-20, AD-23 (extended 2026-10-21), AD-25 (a),
  AD-28, AD-29, AD-30.
- Plan row WP4.3 (section 6, Phase 4, size L, depends on "WP4.2, WP3.16–WP3.20", feeds "V7, V8,
  V18"); the bullet "**WP4.3** connects the interface to the engines, adds start-up work (encoder
  and graphics-card detection, leftover cleanup), and shows the user whether CPU or GPU is in
  use"; module table 8.1 "`clearwater.app` | Entry point and start-up | WP4.3".
- Records and reports, consumer notes:
  - **WP4.1** accept (`docs/proofs/wp4.1-accept.md`, "Banked and owed": H1, G5, the importer
    `OverflowError`) and report (`docs/reports/wp4.1-photo-path.md`: "What WP4.1 adds", the GUI
    preview of an nclx-only P3 photo, the importer items).
  - **WP4.2** accept (`docs/proofs/wp4.2-accept.md`, "Owed to CHARC's register") and report
    (`docs/reports/wp4.2-video-path.md`: "What WP4.2 adds", "Limits", "For WP4.3 (Reviewer B
    B7)").
  - **WP4.2a** and **WP4.2b** accepts (DR-81, DR-82 and the B-A3 note).
  - WP3.16 accept ("Debt and consumer notes"), report sections on `default_engines` and DR-44;
    WP3.17 accept "Consumer notes"; WP3.18 accept "Consumer notes", report "The mapping for WP4.3"
    and "Erratum at the gate" items 1 and 5; WP3.19 accept and report "Seam for WP3.14 and WP4.3";
    WP3.20 accept "Consumer notes", report "Public API"; WP3.20R accept (DR-61).
  - WP3.10 accept "Consumer notes" (`resolve_encoder`, the CREATE_NO_WINDOW spawn helper), report
    section 9; WP3.9 report "Limits" (CREATE_NO_WINDOW); WP3.12 report "Public API"; WP3.13
    report "Consumer notes" and brief question 3 (RULED by `871a371855bb1630`: "the start-up
    wiring (WP4.3) passes the configured output folder plus the folders of a small journal of
    in-flight writes"); WP3.14 report "Limits"; WP3.21 accept "IF-8 reporting deviation" and "Debt
    and owed rows", report "Limits" (cuFFT plans).
- Cell: `implementer-opus-high` (commission section 1: a composition package across every
  frozen-interface consumer, design choices at round 0). Tier **STRONG**, Claude lane: Reviewer A
  (your loop, at your seat) and Reviewer B (the orchestrator's seat) are Codex at the pin
  `gpt-6.1-sol` / high.
- **Lane and WP4.3a (Q14, RULED: split).** The package stays `implementer-opus-high` with Codex
  nets. WP4.3a (`implementer-codex-sol-high`, the Claude pass as both nets, STRONG; brief
  `docs/briefs/wp4.3a-brief.md`) takes the AD-23 spawn helper with DR-58 (b) (questions 9 and 13),
  DR-81 (a)(b)(c) (Q23), and DR-76, DR-77 and DR-85 (Q20, Q21), with their files. The files are
  disjoint. WP4.3 dispatches now and does not wait; the merge order is whichever is ready first,
  and the other rebases and re-proves its patch-id (ruling Q14). WP4.3 adds no OS-specific code.
- Worktree `.worktrees/wp4.3`, branch `wp4.3` from main, base = the main commit named at dispatch.

**Why.** After WP4.1 and WP4.2 the photo and video paths run end to end headless
(`tools/headless_export.py` over `clearwater.app.composition`). The application a user starts
still runs partly on stubs:
- `gui/engines.py` `default_engines()` takes the real photo reader and methods from the root, but
  keeps the S1 stand-in `stub_era_select_backend` and the stub video legs (`StubVideoSource`,
  `StubVideoSink`, `StubProxyCache`; `gui/engines.py:167-175`), so a video is refused with a G10
  message;
- the export panels fall back to `unavailable_exports()` (`gui/export_panel.py:218`) and the
  timeline to `stub_analysis_factory` (`gui/timeline.py:799`);
- nothing calls `install_parameter_panels`, `install_timeline`, `install_export_panels` or
  `install_settings_dialog`;
- `shell.run` is "what WP4.3 calls; this package has no entry point" (`gui/shell.py:5-6`).

This package builds the program the owner starts, does the start-up work, and proves V7, V8, V18
and G1-G13 on the running shell with the real engines.

| Field | Content |
|---|---|
| ID and title | WP4.3 — Application wiring; plan section 6 Phase 4 row WP4.3 |
| Goal | One entry point (`clearwater.app.main`, `python -m clearwater`) that builds the real engines through the composition root `clearwater.app.composition` (WP4.1, extended by WP4.2: `photo_reader`, `photo_writer`, `correction_methods`, `backend_selector`, `video_source(device_backend)`, `video_sink(device_backend)`, `proxy_cache(folder, limit_bytes)`, `export_jobs(*, ..., cache_folder, cache_limit_bytes, source_for, sink_for) -> ExportEngine`; `app/composition.py:48-253`), with ONE proxy cache per process shared by the GUI and the export engine (Q16); builds the main window; attaches every Phase 3 panel and the settings dialog to the real engines (the GUI's video source, sink and cache swapped from the stubs here, with the analysis adapter: WP4.2 left `gui/` unchanged, its accept "Locks"); runs the start-up work (leftover cleanup before any job, encoder detection into the settings dialog's catalog, graphics-card detection shown in the status bar per AD-9); and runs the event loop. Also: the GUI's analysis on WP3.11's engine through the WP3.18 mapping, on the backend it selected (DR-67's pattern) with the frame-count check (Q18); a GUI recompute serialised against a running export of the same clip (DR-62); the preview's FFT plans released at a preview boundary (DR-68) and an nclx-only photo's display copy tagged with the D53 built-in (DR-75); the failed-item text of a refused output name readable (DR-82); the program started over a settings file that fails to decode (the DR-85 test, `xfail(strict)` until WP4.3a's fix is on main, Q21); V7 re-measured with the real engines in an EXCLUSIVE window; V8 and V18 shown on the running shell; G1-G13 each checked against the running shell. |
| Spec / decision clauses | Plan bullet (above). G9 "GUI stays responsive during analysis, export and batch processing (work runs off the UI thread)"; V7/D66 "UI responds within 100 ms during analysis, export and batch processing"; V8 "screen-resolution preview vs downsampled full-resolution output differ by less than a threshold set at design; 1:1 view exact", AD-11 as amended 2026-10-21 (ruled addendum (1)); V18 "on opening a clip, a corrected frame is shown before analysis completes, and it updates to the smoothed statistics afterwards"; D85 "Outputs written to a temporary name and renamed on success; leftovers cleaned on next start", 8.4 "Leftover temporary files from a crash are cleaned up on the next start", V11 "leftover temporaries removed on next start"; D34 "Output location: source folder by default"; D53 (the built-in profile for a tagged source without ICC); 8.2 "Encoder capabilities (including 10-bit support) are detected at startup; unavailable options are shown disabled with a reason (D74)"; AD-9 "CPU/GPU use is reported in the status bar ("GPU: RTX 4070 Laptop" / "CPU") and in each job's log line, with the reason when the fallback engaged"; AD-15 "export is unavailable until analysis of that clip completes"; AD-7 amendment 2026-10-26 "a parameter change while an analysis or recompute job is in flight is ABSORBED by that job, never cancelled"; AD-23 extended (the shared CREATE_NO_WINDOW spawn helper is WP4.3a's, ruling Q14; WP4.3 spawns nothing itself); AD-25 (a) app-data locations "resolved in one place, `clearwater.config.paths`"; AD-29 "Each lower consumer ... declares ONE small `runtime_checkable` Protocol in its own package"; AD-30 (gate tests sized by their property; full-clip forms behind a marker both legs exclude); N1 "no OS-specific code without the architect's approval"; N4 (memory); N8 "source files never modified". |
| Depends on | On main at dispatch: WP4.2 (accept `ff234ee` record, the video legs of the root, `ExportEngine`'s per-job device hook `source_for` / `sink_for`, `AnalysisEngine(expected_frames=...)`), WP4.2a (the runner's write-target and file-form guards) and WP4.2b (`jobs.naming.OutputNameError`), WP4.1 (the composition root `src/clearwater/app/composition.py`, `src/clearwater/app/__init__.py` re-exporting the eight builders, `app/__init__.py:12-32`; the headless runner `tools/headless_export.py`; `default_engines()`'s photo legs), WP3.16 (`clearwater.gui.shell`, `contract`, `preview`, `jobs`), WP3.17 (`install_parameter_panels`), WP3.18 (`install_timeline`, the `ClipAnalysis` seam), WP3.19 (`install_export_panels`, `clearwater.jobs.export_seam`), WP3.20/WP3.20R (`install_settings_dialog`), WP3.10 (`detect_capabilities`, `resolve_encoder`, `tool_env`), WP3.11 (`AnalysisEngine`), WP3.12 (`DiskProxyCache`), WP3.13 (`remove_leftovers`), WP3.14/WP3.21 (`ExportEngine`, `release_fft_plans`), WP3.15 (`PresetStore`, `load_settings`). WP4.3a (Codex, concurrent) is not a dependency: the merge order is whichever is ready first, and the DR-85 start-up test is `xfail(strict)` until its fix is on main (Q21). WP-T6 (AD-30) may merge before dispatch; if it does, the gate expressions and the GX011627 trim fixture are its (Q24). |
| Files owned (question 1 and Q15: grants; question 2: the new modules) | **NEW** (Q2, GRANTED): `src/clearwater/app/main.py` (`main(argv=None) -> int`; the only Qt-loading module), `src/clearwater/app/startup.py` (leftover cleanup, the write journal, detection), `src/clearwater/app/analysis_adapter.py` (the `ClipAnalysis` adapter over `AnalysisEngine` and its factory), `src/clearwater/app/activity.py` (the per-clip activity guard and the `ExportJobs` wrapper: journal, DR-62, DR-82's pre-plan check, AD-9 log line), `src/clearwater/__main__.py` (`python -m clearwater`, importing `clearwater.app.main`). Tests NEW: `tests/test_app_startup.py` (with the DR-85 case, Q21), `tests/test_app_leftovers.py`, `tests/test_app_analysis_adapter.py`, `tests/test_app_activity.py`, `tests/test_app_preview_fft.py`, `tests/test_app_wiring.py` (the G-matrix), `tests/test_app_v7.py`, `tests/test_app_v8_v18.py`. `docs/reports/wp4.3-application-wiring.md`; `docs/proofs/wp4.3-ledger.md`. **EDIT, origin WP4.1 (extended by WP4.2):** `src/clearwater/app/__init__.py` (docstring only, naming the WP4.3 modules; Qt-free; never an import of `gui` or `clearwater.app.main`; `__all__` unchanged unless Q16's builder joins it, and then `tests/test_app_composition.py::test_the_package_exports_the_root` (`:93-106`) changes with it); `src/clearwater/app/composition.py` (Q16 only: the additive keyword-only `cache=` on `export_jobs`, and nothing else); `tests/test_app_deps.py` (Q15: the app module set and the Qt rule, `:89-101`, and the module docstring `:1-7`; the one-edge pin `:77-86` and the load checks `:104-128` unchanged); `tests/test_app_composition.py` (DR-84: the import-time witness `:183-202`; Q16's case). **EDIT, granted per question 1:** `src/clearwater/gui/settings_dialog.py` (WP3.20/WP3.20R: DR-52, the `catalog` argument, DR-61), `tests/test_gui_settings_dialog.py` (WP3.20: DR-52's deletion `:778` and the default-rule tests), `src/clearwater/gui/engines.py` (WP3.16, EDITED by WP4.1: `default_engines()` (`:156-175`) takes `photo_source` and `methods` from the root and keeps `stub_era_select_backend` (`:101-121`) and the stub video legs (`:170-172`); here the S1 stand-in is removed and the video members are swapped, question 11 as ruled, Q17), `tests/test_gui_status.py` (WP3.16: the two S1 tests `:128-146`, and Q15's third test `:148-162`), `src/clearwater/gui/preview.py` and `src/clearwater/gui/render_worker.py` (WP3.16: DR-68, question 6; DR-75, Q19), `docs/reports/wp3.20-settings.md` (an erratum appended, DR-52). **EDIT, granted per Q18:** `src/clearwater/jobs/export.py` and `src/clearwater/jobs/__init__.py` (WP3.14, extended by WP4.2: one additive public `expected_frames(probe)` carrying the body of the private `_expected_frames`, `jobs/export.py:435-451`, which then delegates; nothing else). **EDIT only if the round-0 table names the need and the dispatcher grants it:** `src/clearwater/gui/shell.py` (WP3.16: the Q5 device text only), `src/clearwater/gui/jobs.py` (WP3.16: DR-44 (c), only if measured, question 8), `src/clearwater/gui/batch_panel.py` (WP3.19: DR-50's per-row update, only on a failed re-measure). `src/clearwater/gui/__init__.py`: never (question 11 as ruled). **NOT owned:** `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN), `gui/contract.py` and `gui/analysis_service.py` (frozen seams; a change is a CHARC ruling), `jobs/` (`export_seam.py`, `naming.py`, `safe_write.py`, and `export.py` beyond Q18's one additive name; DR-82 is met in the app wrapper, Q22), `analysis/` (DR-47 (b)(c)), `cache/` (DR-83), `core/`, `methods/`, `color/`, `io/photo/` (DR-75 calls `built_in_profile` unchanged, Q19), the other `gui/` modules (`timeline.py`, `parameter_panels.py`, `preset_panel.py`, `export_panel.py`, `export_service.py`, `imaging.py`, `messages.py`, `session.py`, `sources.py`); **WP4.3a's files** (ruling Q14): `src/clearwater/io/video/` (`pipes.py`, `capability.py`, `decode.py`, `encode.py`, `probe.py`, `verify.py`, and the rest of the package), `src/clearwater/config/` (`presets.py`, `settings_store.py`, and the rest), `tools/headless_export.py`, `tests/test_io_video_spawn.py`, `tests/test_wp43_runner_redaction.py`, `tests/test_config_presets.py`, `tests/test_config_settings.py`; `tools/`; `tests/conftest.py` (WP-T6's), `tests/fixture_plugin.py`, `tests/fixtures/` (DR-75's sample is built under `tmp_path`, Q19), `tests/gui_support.py`; `tests/test_wp42_composition.py` (its `test_each_export_jobs_call_opens_its_own_cache`, `:228-232`, stands for the `cache_folder` form), `tests/test_wp41_*.py`, `tests/test_wp42*_*.py`; every existing test file not named above; `pyproject.toml`, `uv.lock` (question 2). |
| Interfaces provided | `clearwater.app.main`; `python -m clearwater`. No frozen interface changes; the `ClipAnalysis` and `ExportJobs` seams are implemented, not changed. Additive only: `install_settings_dialog(..., catalog=None)` (DR-52's "start-up detection gets a catalog argument"); `default_engines(*, locations=None, cache_limit_bytes=...)` (question 11 as ruled; Q17); `composition.export_jobs(..., cache=None)` (Q16). |
| Interfaces consumed | IF-2 (`select_backend`, `free_device_bytes`, `memory_estimate_bytes`; the AD-29 device extension `release_fft_plans` through a consumer-side Protocol), IF-5 (`VideoSource`, `VideoSink.capabilities`), IF-6, IF-7 (`DiskProxyCache`: `key_for`, `lookup`, `proxy`, `set_limit_bytes`, `clear`, its crash clean-up at open), IF-8 (`Progress`, `JobResult.device`), IF-9, IF-10 (`Settings.output_folder`, `cache_limit_bytes`, `force_cpu`, `video_encoder`); the composition root's builders (above); `jobs.naming.final_output_path` and `OutputNameError` (`jobs/naming.py:53`, `:303-305`, `:314`; DR-82); `clearwater.io.photo.writer.built_in_profile` (`io/photo/writer.py:36-57`; DR-75); the gui contract (`ShellWindow`, `ShellContext`, `Engines`, `Session`), the `ClipAnalysis` seam, the export seam. |
| Consumers | WP5.1 (the acceptance suite drives the shell; G and V legs), WP5.3 (the visual review pack runs the application), the owner (the program). |
| Hardware flags | **EXCLUSIVE** for the V7 re-measure (timing figures, plan 4.3) and the footage legs (V18 and V8 on GX011627 through `tools/local_config.find_footage_file`, read-only; under AD-30, Q24). The full two-leg gate is the orchestrator's ONE gate on the final candidate (fill Part 2, Order), not a cell window. `gui` (offscreen), `gpu`, `footage`, `slow` as their tests need. At least 5 GB free before a heavy run; one heavy job at a time; a figure from an ungranted or a parallel-worker run is not a figure of record (AD-28). |
| Out of scope | Changes to `interfaces/`, the gui contract or the seams (AD-20: a STOP); the composition of the photo and video paths themselves (WP4.1, WP4.2); a device-wide memory figure in the GUI (question 7); a persistent encoder-capability cache (question 4); chapter grouping and G11 (v2); N6 and any timing of the export (WP5.2); an installer, a packaged executable or a CI service; the look check and V2 (owner, WP5.3); decoding, parsing or logging any `gpmd` packet, IMU or GPS data; reading or logging any location tag. |
| Debt and decided items | Register on main `101f181` (table below): CLOSES DR-52, DR-62, DR-68, DR-75 (REQUIRED test), DR-82, DR-84, DR-35 (c), DR-44 (c), DR-61, DR-51 (a), DR-50 (by measurement, or the per-row fix); CONSUMER NOTE DR-35 (a), DR-47, DR-45 (a), DR-34; a Question DR-69 (7); MOVED to WP4.3a (ruling Q14) DR-58 (b), DR-76, DR-77, DR-81 (a)(b)(c) and DR-85's fix, with DR-85's start-up test kept here (Q21); NOT REACHED the rest listed. Decided items carried in: the WP3.18 mapping notes (task 4), WP3.17's "keep `"c3"` first in `engines.methods`", WP3.20's "create the real `DiskProxyCache` with `Settings.cache_limit_bytes`", WP3.16's S1 removal (question 11), WP3.19's "the panels never call `setEnabled` on `actions.export`", WP4.2's DR-41 note (the cache's own `key_for`). |
| Done | Plan 4.5. ruff check, ruff format --check and mypy strict are clean, and the cell's touched test files and the markers they need are green. Every existing test is unchanged, or changed only as this brief or a CHARC ruling names. `uv run python -m clearwater` starts the shell on the real engines (smoke test under `QT_QPA_PLATFORM=offscreen`, the event loop ended by a timer). Every G row of the G-matrix is checked on the running shell. V7 is re-measured with the real engines in an EXCLUSIVE window: every scenario is at or under 100 ms, or the failing scenario is a STOP with its figure. V8 is within AD-11 as amended, with DR-75's REQUIRED test, and V18 is shown on the running shell. The DR-85 start-up test is green, or `xfail(strict)` with DR-85's id while WP4.3a's fix is not on main. The footage-absence test is green, and each register row is disposed as the table says. Reviewer A converged, and Reviewer B returned (clean, or its one remediation and re-run done). Then the ONE two-leg gate per the fill's GATE_CHECKS at dispatch is green at the orchestrator's seat on the final candidate (WP-T6 may amend the expressions before dispatch). |

### Register rows (main `101f181`)

Re-based on `cde1cd9`, re-read on `101f181` (DR-85 added). Since `cffd243` these rows CLOSED and leave the table:
- DR-67, closed at WP4.2's accept `ff234ee` (the per-job device hook);
- DR-71, DR-73 and DR-74, closed at WP4.2's accept;
- DR-64, closed by spec v0.5.6;
- DR-65, closed at WP-T5's accept `4933a45`;
- DR-80, closed at WP4.2b's accept `3cedac6`. Its trigger had said "at the latest WP4.3".

The GUI route keeps WP4.2b's rule, and DR-82 is that route's wording.

| Row | Signal / trigger naming this package or its files | Disposition and ground |
|---|---|---|
| DR-52 | "WP4.3: replace the stand-in with WP3.10's function, delete the stand-in and its mirror test; start-up detection gets a catalog argument"; amended: the report errata "WP4.3's swap fixes all three" (unchanged since `cffd243`) | **CLOSES**: `interim_resolve_encoder` (`gui/settings_dialog.py:109`) deleted, `capability.resolve_encoder` the default of `settings_dialog` and `install_settings_dialog` (`:878-883`), `test_interim_rule_matches_the_wp310_rule` (`tests/test_gui_settings_dialog.py:778`) deleted, the `catalog` argument added, the erratum (the four candidate SHAs `262d24f`, `5d34e9e`, `1171731`, `639101c`; `cache_limiter=None` in the public API) appended to `docs/reports/wp3.20-settings.md`; a test that the dialog surfaces WP3.10's `VideoEncodeError("unavailable")` as the D74 reason. |
| DR-62 | "WP4.3 (the export panels and the GUI sequencing): serialise a recompute against a running export of the same clip (refuse, queue or wait, AD-7 / AD-15), with a test that drives both" (unchanged) | **CLOSES** by task 5 (question 8 as ruled: WAIT); the test drives a real export and a GUI recompute of one clip in both orders. With Q16's one cache the two activities share one `DiskProxyCache`, whose per-key store guard (`cache/store.py:11-14`) then also holds across them. |
| DR-68 | BINDING: "WP4.3's brief: release plans at a preview boundary (clip change / unload) and count them in the GUI's memory reading; a test shows the pool returns to its pre-preview figure after the boundary" (unchanged) | **CLOSES** by task 7 (question 6 as ruled); `gpu` test. |
| DR-69 | BINDING: "WP4.3: if the GUI shows a job's device-wide total, an IF-8 or IF-2 extension is a CHARC decision at that brief (AD-20 STOP); otherwise the figure stays bench-only and this row stays open as the record of the gap" (unchanged) | **Question 7, RULED**: the GUI does not show it; NOT REACHED, the row stays OPEN as the record. |
| DR-75 | BINDING: "WP4.3's V8 photo leg (REQUIRED test under its Q12): tag the display copy of a no-ICC source with a tagged colour description with the D53 built-in at the display call sites; a chromatic nclx-only P3 sample built under tmp_path or an nclx-only fixture added by WP4.3 at round 0." | **CLOSES** by task 7 and the REQUIRED V8 photo test (task 10, question 12; Q19 picks the rule's source and the sample): the display copies at `gui/preview.py:441-444` and `gui/render_worker.py:423`, `:450` (today `icc_profile` only) get the D53 built-in when the source has no ICC profile and a tagged description; the test is RED on the base and its expected colour is derived independently of the production chooser. |
| DR-76 | The writer's `"profile"` vs `PresetStore.import_preset` (trigger verbatim in WP4.3a's brief) | **Moved to WP4.3a (ruling 7c7df3db Q14).** |
| DR-77 | `import_preset`'s `OverflowError` (trigger verbatim in WP4.3a's brief) | **Moved to WP4.3a (ruling 7c7df3db Q14).** |
| DR-81 | (a)(b)(c), the runner's redaction gaps and the ffprobe timeout text (trigger verbatim in WP4.3a's brief) | **Moved to WP4.3a (ruling 7c7df3db Q14).** N5: NOT REACHED in either package. |
| DR-82 | "WP4.3 (GUI wiring; the export panel's failed-item text and, if cheap, a pre-plan name check on the engine route before the read / probe): the item text names the source and says 'rename the file'; one test per route." | **CLOSES** under Q22 in the app's `ExportJobs` wrapper (`app/activity.py`). On the worker, before the engine's read or probe, `jobs.naming.final_output_path` raises `OutputNameError` (`jobs/naming.py:303-305`, reached today only in `_plan`, `jobs/export.py:707-719`). The failed item then names the source and says to rename the file. One test per route: photo and video, single and batch. F2 (`..`) is recorded only. `jobs/` is unedited. |
| DR-84 | "WP4.3's touch of `test_app_composition.py` (the GUI wiring): extend the witness to the three video constructors." | **CLOSES**: `test_importing_the_root_builds_nothing_and_loads_no_qt_or_cupy` (`tests/test_app_composition.py:183-202`) also instruments `FFmpegVideoSource`, `FFmpegVideoSink` and `DiskProxyCache`, with a planted import-time construction that fails it. |
| DR-85 | "WP4.3a (Codex, Q21 as ruled): `OverflowError` joins the decode-failure tuple at `settings_store.py:71` (file set aside, defaults used) and at `presets.py:577` (DR-77); failing-first tests; WP4.3's `tests/test_app_startup.py` starts the program over such a file (xfail strict with this row's id until WP4.3a is on main)." | The fix is WP4.3a's (ruling Q14, Q21). **Here:** `tests/test_app_startup.py` starts the program over a `settings.json` whose `last_parameters.created` is `0001-01-01T00:00:00+01:00` and requires the window to come up with the file set aside. While WP4.3a's fix is not on main the test is `pytest.mark.xfail(strict=True, reason="DR-85: ...")`; once it is, the marker is removed in the same rebase. |
| DR-35 (c) | "`remove_leftovers` deletes a live job's temporary if called while a job runs ... (c) stays with WP4.3's start-up clean-up before any job" | **CLOSES**: the cleanup ends before any job can start (task 3; a test that no export or batch job starts while it runs). |
| DR-35 (a) | "Trigger for (a): WP4.3 shows the refusal text" | **CONSUMER NOTE**: a G10 leg shows the reserved-name refusal (`NUL` stem) as the export panel's readable message through the real engine; renumbering stays the owner's word. |
| DR-44 (c) | "(c): WP4.3 real-engine wiring or any job that blocks past cancellation" | **CLOSES** by task 9 (question 8 as ruled): measured with the real jobs at close; fixed in `gui/jobs.py` only if a real job outlives `SHUTDOWN_TIMEOUT_S` (`gui/shell.py:74`, 5.0 s). |
| DR-50 | "WP4.3's V7 re-measure with the real engines and a queue of a few hundred items; a per-row update if it fails" | **CLOSES** by the task 12 scenario (300 items); a per-row update in `batch_panel.py` only if it fails. |
| DR-51 | "WP4.3 (the real adapter replaces the stub; the oracle gains an intermediate-state check if the drag lane is touched again)" | (a) **CLOSES** for the product path: the real adapter's `statistics` gates on its own completed-run state (WP3.18 mapping), with a reader-versus-new-`run` race test on the real adapter; (b) NOT REACHED (`timeline.py` is not touched). |
| DR-61 | "The next settings-dialog touch (WP4.3): format the detail with a fallback, re-evaluate OK on `set_settings`, de-duplicate banners" | **CLOSES** in the same touch as DR-52, with a test each for (i)-(iii). |
| DR-58 (b) | `FFREPORT` inherited by the probe and the decoder (trigger and re-sighting verbatim in WP4.3a's brief) | **Moved to WP4.3a (ruling 7c7df3db Q14).** (a) several GPUs: NOT REACHED (owner hardware, one GPU). |
| DR-47 | "WP3.18 (the GUI's cancel wiring) and WP4.2 (end-to-end cancel)"; (a) CLOSED at WP4.2's accept (the one-shot guard, `analysis/engine.py`); (b)(c) OPEN, "trigger the next `analysis/engine.py` touch" | **CONSUMER NOTE**: the engine's own guard now refuses a retained job run twice. The adapter still runs each job at most once and never two at once (a test). `analysis/engine.py` is not owned, so (b) and (c) are NOT REACHED. |
| DR-45 (a) | "the first consumer that closes a stream from another thread" ((b) CLOSED at WP4.2's accept) | **CONSUMER NOTE**: every stream the adapter or the preview's frame worker opens is iterated and closed by one thread (a test); not reached. |
| DR-34 | "WP3.17 or WP3.20, whichever first touches `presets.py`, `settings_store.py` or `log.py`" | **CONSUMER NOTE.** WP4.3 touches no `config/` file: the Q20 and Q21 edits are WP4.3a's (ruling Q14), and that brief disposes (a) and (b). For (c), `configure_logging` is called once per process (the shell's `start_up`), and the app adds no second call. |
| DR-43, DR-46, DR-49, DR-56, DR-57 (d), DR-36, DR-2, DR-70, DR-72, DR-83 | Their triggers name other modules or packages: `io.photo`, the Y-2 checkers, a method schema, an owner audio report, none, another ffprobe build, a second GPU, WP5.2's N6 re-measure, `export_bench.py`, the next `cache/` touch. | **NOT REACHED**: no file of theirs is touched here (`probe.py`'s spawn kwargs are not DR-36's parse). DR-49's ground is checked on the running shell: c3 and ancuti2018 resolve at 6 decimals or fewer. DR-83: the GUI's cache folder is app data under `locations.cache_dir`; a link planted inside it stays out of envelope until the next `cache/` touch. |

## Task ladder

1. **Read and rebase.** `uv sync`. Read WP4.1's, WP4.2's, WP4.2a's and WP4.2b's accept records and
   the root (`app/composition.py`), then confirm what is still a stub in the product path on the
   base. On `cde1cd9` it is:
   - `default_engines()`'s selector `stub_era_select_backend` and its three stub video members
     (`gui/engines.py:170-174`);
   - the export panels' `unavailable_exports()` (`gui/export_panel.py:218`);
   - the timeline's `stub_analysis_factory` (`gui/timeline.py:799`);
   - `install_settings_dialog`'s `interim_resolve_encoder` (`gui/settings_dialog.py:109`, `:872`).

   No product code yet.
2. **Round 0 yield: the design table**, in the ledger, before product code:
   - the module layout of `clearwater.app` (question 2 as ruled) and its import rule, with the
     `tests/test_app_deps.py` edit (Q15);
   - the start-up sequence step by step, with the thread of each step and each step's duration
     measured on this laptop:
     - `app_locations()`;
     - the settings read;
     - `DiskProxyCache` open through `composition.proxy_cache` on a 20 GB cache (crash clean-up
       and eviction, WP3.12);
     - the leftover scan;
     - `detect_capabilities()` (about 2 s);
     - the GPU probe (CuPy import, `_probe_gpu` through `select_backend`).

     Also show how the ONE cache (Q16) gets `Settings.cache_limit_bytes` when `MainWindow`'s
     `start_up` reads the settings, and what `default_engines()` gives without `locations` (Q17);
   - the leftover folder set and the journal's shape (question 3 as ruled);
   - the analysis adapter's mapping, row by row against WP3.18's table and errata 1 and 5, with
     its backend, its per-run source and its `expected_frames` (task 4, Q18);
   - the DR-62 design (question 8), the DR-68 boundary (question 6), the DR-44 (c) measurement
     (question 8);
   - the DR-75 display change and its sample (Q19); the DR-82 check (Q22); the DR-85 start-up
     test and its `xfail(strict)` form (Q21);
   - the panel install order; the G-matrix; the V7 scenarios (question 10); the V8 and V18 legs
     (question 12, Q24);
   - every existing test the plan changes or deletes, with its reason. On `cde1cd9` these are:
     - `tests/test_gui_status.py:128-162`, three tests;
     - `tests/test_gui_settings_dialog.py:778`;
     - `tests/test_app_deps.py:89-101`;
     - `tests/test_app_composition.py:183-202`.

     `tests/test_gui_status.py:53-55` (`Device: -` before a file is open) stays if Q5's start-up
     text is set only by the app's probe job. `tests/test_wp41_gui.py:28-44` and
     `tests/test_wp41_v8.py:104-112` call `default_engines()` with no arguments and stay
     unchanged under Q17;
   - the `scripts/cell_depth.py` figure your dispatcher gives you.
   YIELD. Any choice the brief leaves open is a STOP.
3. **Entry point and start-up.** `main()` creates one `QApplication`, then calls `app_locations()`
   (AD-25 (a); nothing else reads the environment for a folder). It builds the real engines with
   `default_engines(locations=locations, cache_limit_bytes=...)` (question 11 as ruled), then
   `MainWindow(engines, locations)`.
   - The GUI's `Engines` are wholly real. The photo legs are as WP4.1 composed them. `video_source`
     and `video_sink` come from `composition.video_source()` and `composition.video_sink()`. The
     cache is ONE `composition.proxy_cache(locations.cache_dir, Settings.cache_limit_bytes)` with
     its registered codec, keyed by its own `key_for` (DR-41). They are swapped HERE together
     with the analysis adapter.
   - The export engine is `composition.export_jobs(cache=engines.cache)` (Q16), so the GUI, the
     adapter and every export share one cache instance.
   - Then the panels, in this order:
     - `install_parameter_panels(window)`, with `"c3"` first in `engines.methods` (WP3.17);
     - `install_timeline(window, <adapter factory>)`;
     - `install_export_panels(window, <guarded exports>)`;
     - `install_settings_dialog(window, resolve_encoder=resolve_encoder, catalog=<the start-up
       catalog>)`;
     - then `show()` (question 11 as ruled).
   - Then the start-up work (question 4):
     - (a) **leftover cleanup** (D85, V11) over the folder set of question 3 and the cache root.
       The cache's own crash clean-up is its constructor's; never a folder outside the set. It
       completes before any export or batch job can start (DR-35 (c)), and the removed and failed
       files are logged (N9);
     - (b) **encoder detection** into the catalog off the interface thread, so the first settings
       dialog opens on a known result;
     - (c) **graphics-card detection** off the interface thread. Its reason reaches the status
       bar (AD-9, question 5) and the log.

   CHECK: `python -m clearwater` under offscreen QPA reaches the event loop and exits 0. V7 holds
   during start-up. Nothing in start-up writes outside app data, the cache root, the journal's
   folders and the log. A `settings.json` that fails to decode is set aside and start-up goes on
   (Q21; the DR-85 test, `xfail(strict)` until WP4.3a's fix is on main).
4. **The analysis adapter** (`ClipAnalysis` over `AnalysisEngine`, WP3.18 report "The mapping for
   WP4.3" as corrected by "Erratum at the gate"):
   - The factory builds the adapter only; the engine is built lazily in the first `run` on the
     worker thread.
   - **Live settings by closure**: the factory reads `Settings` (`force_cpu`) through a provider
     over the session (erratum 5; the seam is unchanged).
   - **Backend, source and frame count (Q18)**: the adapter selects its backend on the worker with
     `engines.select_backend`. It builds its frame source with `composition.video_source(<the GPU
     backend, or None on the CPU>)`, the rule of `jobs/export.py:728-734` (DR-67's pattern), with
     `hw_decode = backend.device != "cpu"`. It passes `AnalysisEngine` (`analysis/engine.py:258-272`)
     the export's `expected_frames` for the clip, so a short decode never marks the shared entry
     complete (DR-45 (b)'s analysis half, `jobs/export.py:435-451`).
   - **Kept job priority**: when `retarget` gets a job back from `set_parameters`, the adapter
     keeps it and returns False. The next `run` offers the latest parameters, then runs the kept
     job and clears it (erratum 1). A test against the REAL engine shows that the kept job ends
     under the latest parameters; if it does not, the adapter runs one more job.
   - **Its own pts list** (F-2): `pts()` returns a list the adapter keeps, refreshed off the main
     thread, never `DiskProxyCache.lookup` on the main thread.
   - `statistics` stays None until a full `run` completes under the latest parameters.
   - Cancel goes through the job handle; `analysis.CANCELLED` returns; other failures raise with
     the engine's text.

   CHECK: the WP3.18 seam rules (the threading list in `analysis_service.py`) hold on the real
   adapter. The A-B-A burst of WP3.18 B pass 1 #1 never completes under a kept job. A GUI
   analysis's complete entry is reused by the export's analysis (V17: one decode pass). V18
   (task 10).
5. **DR-62: one activity per clip; DR-82: the pre-plan name check.**
   - **DR-62.** Per cache key, a GUI analysis or recompute and an export (single or batch item) of
     the same clip never run their engines at once (question 8 as ruled: WAIT). The guard lives
     in `clearwater.app`, shared by the adapter and the `ExportJobs` wrapper; no `jobs/` or
     `analysis/` change. The key is computed on the worker, since `ExportJobs.job` builds the
     callable only (`jobs/export_seam.py:58-64`). AD-15 is unchanged, and the gate stays the
     panels' (`ActivityGate`, `gui/export_service.py:53`).
   - **DR-82 (Q22).** The wrapper's job callable first calls `jobs.naming.final_output_path`. An
     `OutputNameError` becomes a failed `JobResult` that names the source and says to rename the
     file, before the engine reads or probes.

   CHECK:
   - one test drives both orders with the real engines on a fixture clip;
   - a cancel while waiting returns CANCELLED (or the panel's cancelled state) with nothing
     written;
   - the cache entry stays complete and consistent (V17 reopen skips the decode pass);
   - the DR-82 test per route.
6. **Settings dialog: DR-52 and DR-61** (the rows' text is the specification). The config readers
   (DR-76, DR-77, DR-85's fix) are WP4.3a's (ruling Q14). CHECK: WP3.20's and WP3.20R's tests pass,
   except the one deletion DR-52 orders; the DR-61 cases fail on the base.
7. **The preview: DR-68's FFT plans and DR-75's display profile.**
   - cuFFT plans are per thread, so the release runs ON the preview worker's thread
     (`clearwater-preview`) at the boundary of question 6. It goes through ONE consumer-side
     `runtime_checkable` Protocol in `clearwater.gui` (AD-29: "same names and signatures as
     `CupyBackend`'s, with a test that `CupyBackend` satisfies it and `NumpyBackend` does not";
     precedent `jobs/export.py:146-168`). `clearwater.gui` still imports no `cupy` and touches no
     `.xp`.
   - **DR-75 (Q19):** at both display call sites (`gui/preview.py:441-444`;
     `gui/render_worker.py:423`, `:450`), a source with no ICC profile and a tagged description is
     shown through the profile the writer embeds (`built_in_profile`, D53). A source with an ICC
     profile, an untagged source and video frames are unchanged.

   CHECK:
   - the `gpu` test reads the reading of question 6 at three points: before a 1:1 render of a 4K
     frame (short side ≥ `FFT_MIN_SHORT_SIDE`, sigma ≥ `FFT_MIN_SIGMA`; `core/backend.py:76`,
     `:79`), after it, and after the boundary. It is back at its pre-preview figure after the
     boundary. A planted controller without the release fails by name;
   - DR-75's REQUIRED test (task 10).
8. **Moved to WP4.3a (ruling 7c7df3db Q14):** the AD-23 spawn helper (questions 9 and 13, DR-58
   (b)) and DR-81 (Q23). WP4.3 edits no `io/video/` and no `tools/` file; start-up's
   `detect_capabilities()` runs through whatever spawn path is on main.
9. **DR-44 (c): close with real jobs.** Measure how long each real job takes to end after cancel,
   from close: an analysis mid-decode, an export mid-encode, a batch item. If every one ends
   within `SHUTDOWN_TIMEOUT_S` (5 s), DR-44 (c) closes as measured (the figures in the report).
   If not, `gui/jobs.py` detaches the callbacks of a job still running at close (question 8),
   with a test.
10. **Tests and the V legs.**
    - The G-matrix (`tests/test_app_wiring.py`): one or more tests per G row, on the running shell
      that `main`'s own builder makes over tmp app-data and the WP2.3 fixtures
      (`tests/fixtures/stills/*`, `tests/fixtures/video/*.mp4`, `tests/fixtures/files/dng`):
      - G1 open; G2 split; G3 the c3 schema's panels, live preview;
      - G4 scrub proxies, then full resolution on release; G5 progress and cancel; G6 presets;
      - G7 batch skip-and-log; G8 progress and cancel with no partial output; G9 with V7;
      - G10 the HLG/PQ refusal, truncated, untagged, DNG refusal, DR-35 (a), DR-82's refused
        name;
      - G11 v2 (named, no test); G12 every setting, force CPU giving `CPU: forced`; G13
        persistence over two window lifetimes.
    - **V11** leftover leg: a planted temporary in a journal folder and in the output folder is
      removed at the next start; a non-matching file is kept.
    - **The footage-absence test** (question 3): with the sources in a stand-in footage folder
      under `tmp_path` and the outputs elsewhere, start-up never scans that folder (a `scandir`
      spy) and a planted temporary-pattern file there survives. When `clearwater.local.toml`
      names the real footage folder, the computed folder set contains no path inside it; that
      folder is never scanned or written.
    - V8 and V18 (question 12 as ruled, Q24). **DR-75's REQUIRED test** is part of the V8 photo
      leg: a chromatic nclx-only Display P3 HEIC built under `tmp_path` (Q19) is previewed by the
      shell and compared with its export.
    - **Layering.** `tests/test_app_deps.py` (EDIT, Q15) pins five things:
      - `gui/engines.py` -> `clearwater.app.composition` stays the ONE gui-to-app edge
        (`:77-86`, ruled flag (3));
      - `app/` holds exactly `__init__.py`, `composition.py` and the four Q2 modules;
      - no `clearwater.app` module but `main.py` imports `clearwater.gui`, PySide6 or `shiboken6`;
      - no `clearwater.app` module imports `cupy` or `cupyx`;
      - importing `clearwater.app` or `clearwater.app.composition` loads no PySide6 and no CuPy
        (`:104-128`, unchanged).

      `tests/test_gui_deps.py` still passes unchanged. DR-84's witness extension goes in
      `tests/test_app_composition.py`.
11. **Review loop** (below) to convergence, the V7 window (task 12), then hand the final
    candidate to the dispatcher. Reviewer B, then the ONE two-leg gate, are the orchestrator's
    (fill Part 2, Order). Before them, you run only your touched files and the markers they need;
    a full-suite run of yours is development evidence and gets no window.
12. **The V7 re-measure (EXCLUSIVE, LAST of your work; question 10 as ruled).** The dispatcher
    grants each window after Reviewer A converges; do not start it unasked. Each scenario's
    longest main-thread gap, its p99 and its tick count go in the report beside the stub-era
    figures (WP3.16; WP3.18 12-39 ms; WP3.19 11-13 ms). Send `WINDOW RELEASED: <summary>` at the
    end.

## Declared operating envelope

Windows 11; Python 3.12; PySide6-Essentials 6.12 as locked; FFmpeg 9.0.2 (gyan) with
`hevc_nvenc` and `libx265`; the RTX 4070 Laptop GPU (8 GB) or the CPU fallback; the Ryzen 9
7940HS, 32 GB RAM.
- ONE application process per app-data folder, and ONE `DiskProxyCache` instance per process
  (Q16). Two processes, or two instances over one folder, are outside WP3.12's envelope
  (`cache/store.py:11-14`).
- One export activity at a time (the panels' `ActivityGate`) plus the open clip's analysis.
- Inputs within WP3.6's, WP3.7's and WP3.9's envelopes.
- Tests run with `QT_QPA_PLATFORM=offscreen` over app data under `tmp_path`, never the real
  `%APPDATA%`.

Out of envelope: several GUI processes, a second GPU, other operating systems (portable code, not
run there), a pure-Python method holding the GIL (WP3.16's 216-796 ms figure stays out of
envelope), and a link planted inside the cache folder (DR-83).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**: Codex `-m gpt-6.1-sol -c model_reasoning_effort=high`, WSL transport, probe
  first. You run it at your seat to convergence, under the five-round gate.
  - Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\rN\`. Ledger:
    `docs/proofs/wp4.3-ledger.md`.
  - Copy the runner and the prompt shape from `...\wp4.2\r2\` (`run_review.sh`,
    `review-prompt.md`, with its probe).
  - The banner must read `gpt-6.1-sol`; a round with another pin is void.
  - Exclude `docs/proofs` with `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - wiring: every Phase 3 panel attached once, to the real engines; no stub left on a product
    path; `"c3"` first; ONE cache instance shared by the GUI, the adapter and the export engine;
    nothing reads app-data folders except through `clearwater.config`;
  - start-up: the order, the thread of each step, and no job before the cleanup ends; the
    cleanup's folder set (never a source folder as such, never the footage path); the journal
    written before a temporary exists and cleared after commit or abort; what a crash at each
    step leaves; a settings file that fails to decode (Q21);
  - the analysis adapter against the WP3.18 seam's threading rules and mapping (kept-job
    priority, its own pts list, live settings, `statistics` gating, no job run twice or
    concurrently), its backend and source (DR-67's pattern) and its `expected_frames`;
  - DR-62 in both orders; cancel while waiting; the cache entry after each order; DR-82's text
    and its position before the read or probe;
  - DR-68: the release on the right thread at every boundary; the Protocol (AD-29); no `cupy`
    in `gui` or `app`. DR-75: every display call site, and no change for an ICC source;
  - DR-52 and DR-61 against their rows' text; the DR-85 test's `xfail(strict)` form;
  - close: no callback after the window is gone (DR-44 (c));
  - nothing in `interfaces/`, the contract, the seams or unowned files changed; no `gpmd`, IMU,
    GPS or location data read; no write to the footage folder.
- Reviewer B is the orchestrator's seat pass on the merge candidate (Codex, the same pin, WSL),
  after your loop converges. Then comes the ONE two-leg gate, per the fill's GATE_CHECKS at
  dispatch (fill Part 2, Order).

## Notes for the cell

- **Yields.**
  - Task 2 (round 0): the table, then YIELD before product code. Question 2's module names and
    question 3's journal shape are GRANTED as ruled. Your dispatcher still copies the table to
    CHARC for Q14-Q24 as ruled.
  - After each review round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE
    remediating. Make NO change in the turn that adjudicates a round.
  - Your dispatcher gives you the `scripts/cell_depth.py` figure at every yield; record it in the
    ledger. ~250K is the evaluation point ("REVIEW ONLY this turn" when told); STOP at ~400K.
- **Windows (X5, AD-28).** Heavy work runs ONLY in a window the dispatcher grants: the V7
  re-measure, the footage legs, and any `gpu` run of more than your own targeted tests. Ask for
  each with `WINDOW REQUEST: <what, how long>`. One heavy job at a time; at least 5 GB free
  before a run. Background runs use `QT_QPA_PLATFORM=offscreen`, output under `work/`, with
  foreground poll-wait calls on the done marker (a reaped run is not a result).
  - The full two-leg gate is NOT yours. It is the orchestrator's ONE gate on the final candidate,
    after Reviewer A converged and Reviewer B returned (fill Part 2, Order, 2026-10-29), as the
    fill's GATE_CHECKS at dispatch.
  - Today that gate is, from Git Bash with `PYTEST_ADDOPTS` unset:
    `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/<run>-parallel`,
    then `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/<run>-serial`.
  - WP-T6 (AD-30) may amend both expressions with `and not fullclip` before dispatch.
  - A new wall-clock bound in a parallel-leg test is `slow` with a reason (GATE_CHECKS). Timing
    figures come only from serial runs. Send `WINDOW RELEASED: <summary>` after each window.
- **Footage.** Read-only at `C:\Users\rwsmy\clearwater-footage\`, only through
  `tools/local_config.find_footage_file` (or WP-T6's session trim, if it has merged; Q24). Never
  a basetemp, an output folder, a journal entry or a cleanup target there. Every output goes
  under `work/` or `tmp_path`.
- **Return report** = your FINAL message to your dispatcher by your messaging tool, under about
  70 lines:
  - the start-up sequence with its measured steps;
  - the wiring table (panel, engine, test) and the G-matrix;
  - V7 per scenario beside the stub-era figures; the V8 and V18 figures;
  - the DR dispositions;
  - the static checks and the light runs;
  - the Reviewer A rounds and verdict;
  - open items.
- **STOP for:**
  - any change needed in `src/clearwater/interfaces/` (AD-20), `gui/contract.py`,
    `gui/analysis_service.py`, `jobs/export_seam.py` or a file not owned or granted;
  - a dependency;
  - any OS-specific code (the AD-23 helper is WP4.3a's), or an edit of a WP4.3a file;
  - a V7 scenario over 100 ms that the owned files cannot fix; V8 outside AD-11;
  - a cleanup target outside question 3's set or inside the footage folder;
  - anything that relaxes D85, D74 or AD-15 (owner-reserved);
  - a need to show the job's device-wide memory (DR-69, AD-20);
  - any need to decode a `gpmd` packet or read a location tag;
  - a second `DiskProxyCache` instance over the app's cache folder in one process (Q16);
  - the round-0 table showing a choice the brief left open.
- **Working rules:**
  - Commit inside the worktree by pathspec with `git -c core.autocrlf=false commit -m
    "feat(wp4.3): ..." -- <paths>`, with a `Co-Authored-By:` footer naming your model. Every
    committed blob is LF.
  - Never `git stash`; never a bare `cd`; never post to a mailbox; never `git clean -x`.
  - Your gates: ruff check, ruff format --check, mypy strict, and your touched files plus the
    markers they need. The full two-leg gate is the orchestrator's (above). No harness gate: no
    `scripts/`, `.claude/`, kernel doc or `tests/harness/` change.
  - Report: `docs/reports/wp4.3-application-wiring.md` (claims, evidence paths, limits, the V7
    figures beside the stub-era figures).
- **Layering tests in every light run (AD-29):** `tests/test_core_deps.py`,
  `tests/test_color_deps.py`, `tests/test_io_video_decode_rules.py`,
  `tests/test_analysis_deps.py`, `tests/test_gui_deps.py`, `tests/test_app_deps.py`,
  `tests/test_app_composition.py`, `tests/test_wp42_composition.py`.

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

### Revision 1 questions (main `cde1cd9`; recommended answer first)

14. **Lane: one Codex-eligible sibling.** Recommended: split **WP4.3a** onto the Codex lane
    (`implementer-codex-sol-high`, the Claude pass as both nets; STRONG):
    - the spawn helper (questions 9 and 13 as ruled; `io/video/pipes.py`, `capability.py`,
      `decode.py`, `encode.py`, `probe.py`, `verify.py`, `tests/test_io_video_spawn.py`; DR-58 (b));
    - DR-81 (a)(b)(c) (Q23; `tools/headless_export.py`, `tests/test_wp43_runner_redaction.py`);
    - DR-76 and DR-77 with the start-up sibling (Q20, Q21; `config/presets.py`,
      `config/settings_store.py`, `tests/test_config_presets.py`, `tests/test_config_settings.py`).

    Ground: none of it touches a frozen interface, `gui/` or `app/`. Every rule is written: the
    ruled Q9 and Q13, the rows' text and Q20/Q21 as ruled. Its files are disjoint from WP4.3's, so
    it can run concurrently with WP4.3's round 0 and build, and it shrinks an L package that WP4.1
    and WP4.2 needed four cells each to land. Cost: one more gate (about 52 min), and AD-23's
    "applied by" note moves to WP4.3a's accept. It also serves the owner's 2026-10-29 lane
    balance.
    Alternative: keep all of it in WP4.3: one gate, a larger review surface.
15. **Grants added by Revision 1** (recommended: grant now, each named with its origin package):
    - `tests/test_app_deps.py` (WP4.1). `test_no_app_module_imports_the_gui_or_qt`
      (`:89-101`) pins `app/` to `["__init__.py", "composition.py"]` and bans `clearwater.gui` and
      PySide6 in every app module, which ruled Q2 (`main.py`, the only Qt-loading module)
      contradicts. The module set gains the four Q2 modules; the gui and Qt ban exempts
      `main.py` alone; the cupy ban stays for all; `:77-86` and `:104-128` are unchanged.
    - `tests/test_app_composition.py` (WP4.1, extended by WP4.2): DR-84's witness, and Q16's case.
    - `tests/test_gui_status.py` (WP3.16): beyond the two S1 tests, also
      `test_real_selection_through_the_shell_shows_gpu` (`:148-162`, `gpu`). It calls
      `stub_era_select_backend` with method `"stub"` (`:152`, `:156`), so deleting the stand-in
      breaks it. It is edited to use `core.select_backend` with the real methods (`c3`), with its
      assertions unchanged.
    - `config/presets.py`, `config/settings_store.py` and the new tests in
      `tests/test_config_presets.py` and `tests/test_config_settings.py` (WP3.15; Q20, Q21).
    - `tools/headless_export.py` (WP4.1; extended by WP4.2, WP4.2a, WP4.2b) for Q20's key set
      and DR-81 (a)(b) only, with the NEW `tests/test_wp43_runner_redaction.py`.

    Under Q14's split the last two bullets go to WP4.3a.
    Alternative: grant at round 0 on a named need.
16. **One proxy cache per GUI process.** `composition.export_jobs(cache_folder=...)` opens its
    OWN `DiskProxyCache` (`app/composition.py:238`; pinned by
    `tests/test_wp42_composition.py:228-232`). The GUI's `engines.cache` would be a second
    instance over the same folder. WP3.12's lock and its "one store call at a time per key" guard
    are per instance (`cache/store.py:11-14`), eviction is not shared, and the settings dialog's
    `set_limit_bytes` / `clear` (`gui/settings_dialog.py:716`, `:817`) would reach only the GUI's
    instance.
    Recommended:
    - add an additive keyword-only `cache: DiskProxyCache | None = None` to `export_jobs`. It is
      mutually exclusive with `cache_folder` (both given is a `ValueError`) and is keyed by that
      cache's own `key_for` (DR-41);
    - `app.main` passes `engines.cache`, so the GUI, the adapter and every export share one
      instance, and the export reuses the GUI analysis's complete entry (V17);
    - test it in `tests/test_app_composition.py`, with `test_each_export_jobs_call_opens_its_own_cache`
      unchanged.

    Alternative: two instances, with DR-62's lock as the only serialisation and the dialog's
    limit and clear forwarded to both. Eviction by one instance could still remove an entry the
    other is using.
17. **`default_engines()` without `locations`** (question 11 as ruled makes `locations`
    keyword-only and defaulted; the default is unstated). Recommended:
    - with `locations=None` the video legs stay today's stubs (`gui/engines.py:170-172`), so a
      caller without app data (`tests/test_wp41_gui.py:28-44`, `tests/test_wp41_v8.py:104-112`,
      `shell.run()` with no engines, `gui/shell.py:600`) opens no real cache, writes nothing under
      `%APPDATA%` and holds no real clip's proxies (N4; ruled flag (1)), and a video is refused
      with the G10 message as on main;
    - with `locations` given, all three video legs are real (task 3);
    - the selector is the root's `backend_selector()` in both forms, so the S1 stand-in goes
      entirely;
    - a test pins that `clearwater.app.main`'s engines are wholly real.

    Alternative: real legs over a refusing cache (the root's `_NoCacheFolder` made public). That
    changes what the WP4.1 GUI tests run on, and the settings dialog's limit call then refuses.
18. **The GUI analysis's device source and frame count.**
    - **Source.** Recommended: the adapter follows WP4.2's export rule:
      - it selects on the worker with `engines.select_backend`;
      - its source is `composition.video_source(<the GPU backend or None>)`, the rule of
        `jobs/export.py:728-734`, with `hw_decode = backend.device != "cpu"`;
      - it passes `AnalysisEngine` (`analysis/engine.py:271`) the export's `expected_frames`.
    - **Frame count.** That count comes from a private function (`jobs/export.py:435-451`).
      Recommended: one additive public name in `clearwater.jobs` (`expected_frames(probe)`, the
      private function's body; a grant of `jobs/export.py` and `jobs/__init__.py`, additive
      only), so the rule has one copy (the DR-52 lesson). A test shows the adapter and the export
      pass the same count for a clean, a `truncated` and an `unreadable_tail` probe.

    Alternative: the adapter passes `expected_frames=None`. Then a short GUI decode marks the
    shared entry complete and the export reuses it (V17), held only by the sink's
    `missing_frames` rule (WP4.2 report, Limits).
19. **DR-75: the rule's source and the sample.**
    - **Rule.** Recommended: the display sites take the writer's own D53 choice,
      `clearwater.io.photo.writer.built_in_profile(color, metadata.source_format)`
      (`io/photo/writer.py:36-57`; public, not re-exported by `clearwater.io.photo`), when
      `color.icc_profile is None`. That is one rule, no copy, and `io/photo/` is unchanged.
      `preview.py` reads `session.source().metadata`; `render_worker.py` gets the chosen bytes in
      its `RenderRequest` (round 0 names the field).
    - **Sample.** It is built at test time under `tmp_path` from WP4.1 R3's recipe
      (`clearwater-review-evidence\wp4.1\r3\r3_repro.py`: a 16x16 chromatic nclx-only Display P3
      HEIC), with no fixture-set change.
    - **Expected colour.** It is derived independently of `built_in_profile`, from the exported
      PNG's embedded profile read back (WP4.1 R3 H6's lesson).

    Alternative: an nclx-only fixture added at round 0 (a `tests/fixtures/`, manifest and recipe
    grant).
20. **DR-76: which side.** Recommended: the IMPORTER side.
    - `config/presets.py:69` adds `"profile"` to the provenance keys that are dropped (reported in
      `dropped_keys`, so the panel's existing "carried provenance (...); it was not kept" warning
      names it, `gui/preset_panel.py:395-406`).
    - The runner's copy (`tools/headless_export.py:143`) moves in step.
    - The writer (`io/photo/writer.py:23`, `:79-81`) is unchanged, so every PNG already written
      stays importable. CHARC adds an AD-13 note naming `"profile"` as a writer provenance key.
    - Test: export a tagged nclx HEIC through the real engine, write its provenance text to a
      file, import it: OK, `profile` dropped.

    Alternative: rename the writer's key into AD-13's set. That is an `io/photo` grant and a
    change of the D91 provenance shape, and files already written keep the old key.
21. **DR-77 and its start-up sibling.** EXECUTED at the drafting seat on `cde1cd9`:
    - a `settings.json` whose `last_parameters.created` is `0001-01-01T00:00:00+01:00` makes
      `load_settings` raise `OverflowError` ("date value out of range"), because
      `config/settings_store.py:71` maps only `(ValueError, RecursionError)`;
    - the shell's `start_up` (`gui/shell.py:148`) does not catch it, so the program cannot start
      until the user deletes the file;
    - `PresetStore.import_preset` raises the same (DR-77); the root cause is
      `interfaces/parameters.py:211` (`astimezone(UTC)`, FROZEN IF-9; not touched).

    Recommended:
    - add `OverflowError` to the decode-failure mapping at `config/presets.py:577` (import, load
      and list all refuse readably as `FormatError`) and at `config/settings_store.py:71` (the
      file is set aside, defaults are used, the existing path);
    - each fix gets a failing-first test, and `tests/test_app_startup.py` starts the program over
      such a file;
    - CHARC registers a row for the sibling (closed by this touch).

    Alternative: widen `gui/preset_panel.py:47` `_FAILURES` (WP3.17). That covers only the
    panel, and start-up still fails.
22. **DR-82's form.** Recommended: in the app's `ExportJobs` wrapper.
    - Its job callable, on the worker (`ExportJobs.job` must touch no file,
      `jobs/export_seam.py:58-64`), calls `jobs.naming.final_output_path(source, settings,
      kind)` first.
    - An `OutputNameError` returns a failed `JobResult` reading "<name>: this file name cannot be
      used for an output file; rename the file." (`ascii_text`), before the engine's read or
      probe.
    - Every other error is left to the engine's own text. `jobs/` is unedited, and the rule is the
      planner's own.
    - "One test per route" is read as photo and video, each single and as a batch item, through
      the panels.

    Alternative: change `OutputNameError`'s text in `jobs/naming.py:303-305` (WP4.2b; a grant).
    That fixes every caller's wording but saves no read or probe.
23. **DR-81 (a)(b)(c).** Recommended:
    - (c) at its SOURCE: the timeout text at `io/video/verify.py:233-234` names the file and the
      120 s limit, not the ffprobe command, so the GUI's failed item is clean too. `verify.py` is
      already a spawn-site edit;
    - (a): the `Redactor` matches a known folder under any mix of `\` and `/`;
    - (b): a raising footage-folder resolution in `main` becomes a redacted usage refusal (exit
      2);
    - each fix gets a RED-first test in `tests/test_wp43_runner_redaction.py`; N5 is NOT REACHED.

    Alternative for (c): add the tool folder to the `Redactor`'s known folders (runner only; the
    GUI's text keeps the path).
24. **V18 and the footage legs under AD-30.** Recommended:
    - The gate form of V18 runs on `tests/fixtures/video/hevc8-bt709-full.mp4`, with the
      analysis held by a test hook so that "before analysis completes" is deterministic.
    - The GX011627 V18 leg and every V7 scenario on GX011627 are EXCLUSIVE window evidence, not
      gate tests.
    - If WP-T6 has merged at dispatch, any test form on the whole clip carries `fullclip`, and a
      gate test whose subject is the real container uses WP-T6's session trim (never the footage
      folder for output).

    Alternative: V18 on GX011627 as a `footage` gate test. It costs serial-leg minutes in every
    gate, against AD-30.

## Rulings (CHARC `2c4476d9869df056`, 2026-10-28, verbatim; they GOVERN the Questions section above)

PRIMARY: orchestrator. Thread `159c14fb79ad1aae`, reply to `8c3c624c224c263e` (+ `56e00cce74e65b5c`, `528b3db814b6d2c5`). **RULING PACKET: all four drafts APPROVED with the rulings below; every helper recommendation ADOPTED except where a line says otherwise. Write the rulings verbatim into each brief, commit on `briefs-p4`, ff main; dispatch WP4.1 (opus-high) and WP-T5 (by pace) now; WP4.2 and WP4.3 stay DRAFT until their predecessor's accept plus one revision pass, then FINAL on my word.** Tripwire passes (new package `clearwater.app`, the WP4.3 modules, `python -m clearwater`, the leftover journal) are all GRANTED here.

**Flags.** (1) WP4.2 Q3 narrowing ACCEPTED (N4 ground: the stub analysis over a real source stores ~23 GB for GX011625; the GUI's video legs swap in WP4.3 with the adapter). (2) withdrawn; see 43-Q13. (3) tripwires GRANTED as listed; the `gui/engines.py -> clearwater.app.composition` edge is the ONE gui-to-app edge, pinned by `tests/test_app_deps.py`. (4) the two S1 tests go in WP4.3 (43-Q11); WP-T5's three bodies as T5-Q2/Q3/Q4. (5) noted; my "~30 min" is CORRECTED to the helper's ~12 min projection, W1 replaces it.

**Addendum.** (1) WP4.3's V8 legs cite AD-11 AS AMENDED 2026-10-21 (k = 1 EXACT; k > 1 mean <= 1/255, p99 <= 2/255 at k = 2 and <= 4/255 at k = 4, max recorded never asserted), the same text as WP4.1 line 301. (2) 41-Q3 + 43-Q11 ruled together as recommended: `default_engines()` stays, takes its photo legs and methods from the root in WP4.1, its selector and video legs in WP4.3; `shell.run` and `gui/__init__.py` unedited. (3) WP4.2's DR-35 clause STRUCK.

**WP4.3 (L, opus-high, Codex nets; FINAL after WP4.2's accept + one revision).** Q1 grants as recommended now; `shell.py` (Q5 device text only), `gui/__init__.py` (never, under Q11 as ruled), `gui/jobs.py` (DR-44 (c) only if measured), `gui/batch_panel.py` (DR-50 only on a failed re-measure) at round 0 on a named need. Q2 GRANTED: `app/main.py` (the only Qt-loading module), `startup.py`, `analysis_adapter.py`, `activity.py`, `src/clearwater/__main__.py`; `uv run python -m clearwater`; NO `[project.scripts]` entry, no `pyproject.toml` edit. Q3 GRANTED, persistent-data shape = the leftover JOURNAL: JSON in `config_dir` via `config.atomic`, `format_version` 1, one entry per job (destination folder) added before the job and removed after; start-up scans `Settings.output_folder` plus the journal's folders with WP3.13's `remove_leftovers` unchanged, then clears the scanned entries; never a folder merely because a source lies there, never the footage folder (the footage-absence test proves it); a journal folder that is a source folder under D34's default IS scanned (D85 kept; narrowing it would be the owner's). (B) and (C) not taken. Q4 as recommended (synchronous cleanup before `show()`, measured at round 0, over 100 ms = a gated first job; cache open timed on a full 20 GB cache; detection as two start-up jobs; NO persistent capability cache). Q5 as recommended (verbatim reason, `Device: <reason>` before a file is open, job log line names `JobResult.device`, no GPU name, no core change). Q6 as recommended (boundaries = source change / unload, shell close, before an export or batch job of the GUI process selects; release on the preview worker's thread as an undroppable task shown at round 0; test asserts `free_device_bytes()` back to the pre-preview figure within one pool block). Q7: the GUI does NOT show the device-wide total; no IF-8 / IF-2 extension; DR-69 NOT REACHED, stays OPEN as the record. Q8 DR-62 = WAIT as recommended (one process-local lock per cache key in `clearwater.app`, the waiter cancellable, "Waiting for the other job on this clip"; test drives both orders); DR-44 (c) measure first, `gui/jobs.py` only if a real job outlives `SHUTDOWN_TIMEOUT_S`. Q9 `io/video/pipes.py` as recommended (helper returns the spawn keyword arguments; `tool_env` delegates; the five spawn sites edited; no new `io/video` module; DR-58 (b) CLOSES). Q10 all six scenarios (a)-(f), longest gap and p99 each, bound 100 ms, EXCLUSIVE; a failing scenario = STOP with its figure. Q11 as recommended with 41-Q3 (addendum 2): delete `stub_era_select_backend`, `STUB_ERA_METHOD_ID` and the two S1 tests; `default_engines()` keyword-only `locations` and cache limit; `app.main` attaches panels before `show()`. Q12 as recommended with the AMENDED AD-11 bounds (addendum 1); V8 video pre-encode via `imaging.preview_export_difference`; V18 on GX011627 (footage, EXCLUSIVE) and `hevc8-bt709-full`. Q13 CONFIRMED: AD-23's 2026-10-21 extension IS the N1 approval for this one helper, no new AD row, on the three conditions as written (one place, `subprocess.CREATE_NO_WINDOW` on `win32` else 0; every other OS the same call with `creationflags=0` and the same `FFREPORT`-free environment; both branches tested + an AST pin that no spawn site sets `creationflags`). I add a dated "applied by WP4.3" note to AD-23 at the accept.

**Cost restated:** unchanged from the commission except WP-T5's saving (~12 min per gate, not ~30) and one extra short window for it.

## Rulings, Revision 1 (CHARC `7c7df3dbe237ceb7`, 2026-10-29 12:20:47Z, verbatim; they GOVERN Questions 14-24)

**CHARC RULING on WP4.3 brief REVISION 1 (query 48f440de35ca09b6; `brief-wp4.3-rev` efeb4bf, 854 lines, 0 CR; header, fields, register table and Q14-Q24 read in full, the drafter's return read): FINAL on this post, with the Q14 split applied. Append this ruling verbatim under Rulings (it governs Q14-Q24 as 2c4476d9 governs Q1-Q13), carve WP4.3a out as below, ff main, dispatch WP4.3.**

**Q14 split WP4.3a to the Codex lane: CONCUR.** WP4.3a = the AD-23 spawn helper with DR-58 (b) (Q9/Q13 as ruled: `io/video/pipes.py`, `capability.py`, `decode.py`, `encode.py`, `probe.py`, `verify.py`, NEW `tests/test_io_video_spawn.py`); DR-81 (a)(b)(c) (Q23: (c) at its source in `verify.py`, (a)(b) in `tools/headless_export.py`, NEW `tests/test_wp43_runner_redaction.py`); DR-76 and DR-77 with the start-up sibling (Q20, Q21: `config/presets.py`, `config/settings_store.py`, the two config test files, the runner's key set at `headless_export.py:143`). No frozen interface, no `gui/`, no `app/`; every rule written; files disjoint from WP4.3. Lane `implementer-codex-sol-high`, Claude pass as both nets, tier STRONG (product code). SEQUENCING: the Codex lane is ONE cell and WP-T6 holds it; WP4.3a dispatches when WP-T6's cell stands down (its gate may still be running at your seat), from a SHORT brief your helper carves from this one's ruled text (the rows above, Q9/Q13/Q20/Q21/Q23 verbatim, locks, a Done, its own ladder) for a quick ruling of mine. WP4.3 (opus-high) dispatches NOW on this FINAL and does not wait. Merge order = whichever is ready first; the other rebases, patch-id re-proved. AD-23's "applied by" note moves to WP4.3a's accept (mine). WP4.3's text keeps a one-line pointer per moved row ("WP4.3a") so its register table stays complete. Codex-built packages would become 7 of the accepts with it.

**Q15 grants: CONCUR, all, granted now** with their origin packages as listed: `tests/test_app_deps.py` (the module set gains the four Q2 modules; the gui/Qt ban exempts `main.py` ALONE, `src/clearwater/__main__.py` is outside the app set; the cupy ban stays for all; `:77-86` and `:104-128` unchanged), `tests/test_app_composition.py` (DR-84, Q16's case), the third `tests/test_gui_status.py` test (edited to `core.select_backend` with the real methods, assertions unchanged); the `config/` and runner grants go to WP4.3a. STOP candidates 1 and 4 are closed by this.

**Q16 one proxy cache per GUI process: CONCUR.** Additive keyword-only `cache: DiskProxyCache | None = None` on `export_jobs`, mutually exclusive with `cache_folder` (`ValueError` when both), keyed by that cache's own `key_for` (DR-41); `app.main` passes `engines.cache`; the test lands in `tests/test_app_composition.py`; `test_each_export_jobs_call_opens_its_own_cache` stands for the `cache_folder` form. STOP candidate 3 closed.

**Q17 `default_engines(locations=None)` keeps the stub video legs: CONCUR**; the selector is the root's `backend_selector()` in both forms; one test pins that `clearwater.app.main`'s engines are wholly real.

**Q18 the GUI analysis's source and count: CONCUR**, both parts: the adapter selects on the worker and builds `composition.video_source(<GPU backend or None>)` by the export's rule; ONE additive public `clearwater.jobs.expected_frames(probe)` carrying the private body (grant of `jobs/export.py` and `jobs/__init__.py`, additive only; the private name delegates); the test shows adapter and export agree for a clean, a `truncated` and an `unreadable_tail` probe.

**Q19 DR-75: CONCUR** (the writer's `built_in_profile` at the display sites when `icc_profile is None`; the sample built under `tmp_path` from WP4.1 R3's recipe; the expected colour derived independently from the exported PNG's profile). The helper did not verify `r3_repro.py`'s contents: the cell reads it at round 0, and if the recipe does not rebuild a 16x16 chromatic nclx-only Display P3 HEIC, round 0 asks for the fixture alternative (a `tests/fixtures/` + manifest grant) rather than inventing one.

**Q20 DR-76 importer side: CONCUR** (`config/presets.py:69` drops `"profile"` reported in `dropped_keys`; the runner's copy in step; the writer unchanged so every PNG already written stays importable). The AD-13 note naming `"profile"` as a writer provenance key is mine at WP4.3a's accept. (Moves to WP4.3a.)

**Q21 DR-77 and the start-up sibling: CONCUR** (`OverflowError` joins both decode-failure tuples; failing-first tests; `tests/test_app_startup.py` in WP4.3 starts the program over such a file once WP4.3a's fix is on main, or carries the test `xfail(strict)` with the DR-85 reason until it is). **NEW ROW DR-85** written now at my commit named in the cue: pre-existing start-up crash, reproduced by the drafting seat and by you on `cde1cd9`; closes at WP4.3a's accept. STOP candidate 2 closed. (Fix moves to WP4.3a; the start-up test stays in WP4.3.)

**Q22 DR-82 in the app's `ExportJobs` wrapper: CONCUR** (`final_output_path` first on the worker; `OutputNameError` -> a failed `JobResult` "<name>: this file name cannot be used for an output file; rename the file."; every other error left to the engine; one test per route = photo and video, single and batch; `jobs/` unedited; F2 recorded only).

**Q23 DR-81: CONCUR** ((c) at its source in `verify.py:233-234`, naming the file and the 120 s limit; (a) mixed separators; (b) a raising resolution -> redacted usage refusal exit 2; RED-first tests; N5 NOT REACHED). (Moves to WP4.3a.)

**Q24 V18 under AD-30: CONCUR** (gate form on `hevc8-bt709-full` with the analysis held by a test hook; the GX011627 V18 leg and every V7 scenario are EXCLUSIVE window evidence; if WP-T6 has merged at dispatch, whole-clip test forms carry `fullclip` and a real-container gate test uses the session trim). The cell's windows are evidence windows under the fill's Order bullet; the ONE gate is yours on the final candidate.

**Unverified citations:** none blocks FINAL. AD-11's amended bounds and the WP3.x section names are read by the cell at round 0 from the records themselves; DR-58 (b)'s two WP4.2 test launches are named by line in WP4.3a's round 0; the gate wall figure is whatever the fill says at dispatch (WP-T6 changes it); the stub-era V7 figures are the baseline the re-measure compares with and are quoted from the WP3.16 record.

**Owed by me:** DR-85 now; at WP4.3a's accept AD-13 note, AD-23 note, DR-58 (b)/DR-76/DR-77/DR-81/DR-85 closures; at WP4.3's accept the rest of its table. Main is at cde1cd9 + my state commits; free. WP-T6 continues on the Codex lane meanwhile.
