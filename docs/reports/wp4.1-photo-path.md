# WP4.1 report: photo path end to end

**Status:** DRAFT (cell 1, 2026-10-28), branch `wp4.1` on base main `3aa3c51`. Brief
`docs/briefs/wp4.1-brief.md` FINAL (CHARC `2c4476d9869df056`); round-0 table and rulings in
`docs/proofs/wp4.1-ledger.md` (R0-1..R0-10, S1..S8).

## What WP4.1 adds

- **The composition root** `clearwater.app.composition` (new package `clearwater.app`): the one
  product place that builds the real photo engines. `photo_reader()`, `photo_writer()`,
  `correction_methods()` (`available_methods()`, `"c3"` first, D16), `backend_selector()`
  (`clearwater.core.select_backend` itself) and `export_jobs(*, app_version, reader, writer,
  methods, select_backend, on_stage) -> ExportJobs`. Every call returns fresh components;
  importing the root builds none of its components and probes no device (`clearwater.core` builds
  its module-level CPU backend on import); the module imports no `clearwater.gui`, PySide6 or CuPy
  and never resolves the app-data folder. `export_jobs()` routes a photo request to `ExportEngine` and a
  video request to `unavailable_exports().job(request)` (`UNAVAILABLE_TEXT`, nothing written);
  the engine's video collaborators are interface stubs no job reaches (question 4).
- **The GUI's photo legs:** `gui/engines.py` `default_engines()` takes `photo_source` and
  `methods` from the root; the selection stays `stub_era_select_backend` and the video legs stay
  stubs until WP4.3 (question 3). `gui/engines.py -> clearwater.app.composition` is the one
  gui-to-app edge (`tests/test_app_deps.py`).
- **The headless runner** `tools/headless_export.py` (a test tool): library API `route`,
  `requests_for`, `parameters_for`, `read_parameter_file`, `configured_footage_folder`,
  `inside`, `check_outputs`, `run`, `record_object`, `record_json`, `exit_status`,
  `summary_lines`, `main`; a CLI with the full IF-10 flag set but `last_parameters`
  (`--out | --beside-source`, `--suffix`, `--bit-depth`, `--no-provenance`, `--force-cpu`,
  `--encoder`, `--quality`, `--ten-bit`, `--cache-limit-bytes`) plus `--method`,
  `--parameters | --neutral`, `--settings-dir`, `--record`; exit 0 / 1 / 2; record schema 1.

## WP4.2 extension points

- Root: `export_jobs()` builds the real `FFmpegVideoSource`, sink factory and `DiskProxyCache`
  and passes the selected device backend to source, sink and engine there (DR-67), with new
  keyword arguments only (for example the cache folder); it then returns the `ExportEngine`
  itself and `_PhotoExports` and the stub video collaborators are deleted. No public name changes.
- Runner: `route` already sends `.mp4` to `"video"`; WP4.2 adds video-only options
  (`--cache-dir` and the like) and record fields under schema 1, never renaming or removing one.

## Claims and evidence

(Test node ids; counts and figures filled from the final runs.)

| Claim | Evidence |
|---|---|
| The root builds fresh real components; `c3` first; selection is `core.select_backend` | `tests/test_app_composition.py` |
| Importing `clearwater.app` / `.composition` builds nothing, loads no PySide6 / CuPy / gui | `tests/test_app_composition.py::test_importing_the_root_builds_nothing_and_loads_no_qt_or_cupy`, `tests/test_app_deps.py::test_importing_the_app_loads_no_pyside6_and_no_cupy` |
| Only the root constructs `ExportEngine` / `PhotoReader` / `PhotoWriter` / calls `available_methods()` in `src/clearwater` (planted control) | `tests/test_app_composition.py::test_only_the_root_constructs_the_real_photo_engines`, `...::test_the_static_check_reports_a_planted_construction` |
| One gui-to-app edge (planted control) | `tests/test_app_deps.py` |
| The shell on `default_engines()` opens a still with the real reader, `Device: CPU: forced` | `tests/test_wp41_gui.py` |
| Runner: routing equal to `gui.sources` (sidecar and unknown suffix refused, batch continues) | `tests/test_headless_export.py::test_the_routing_tables_and_texts_equal_the_interfaces`, `...::test_refused_items_fail_and_the_batch_continues` |
| Runner: exit 0/1/2, record schema 1 with names only, footage refusals, no PySide6 / CuPy, cancel and Ctrl-C, DR-62 order, DR-6, DR-35 (a), video unavailable | `tests/test_headless_export.py` |
| Runner (Reviewer A round 2): footage refusals through the `\\?\` and `\\?\UNC\` spellings; no full path for a non-ASCII folder, an `argparse` refusal, a record field or a record that cannot be written; no EXIF tag value printed | `tests/test_headless_export.py::test_g1_*` to `::test_g7_*` |
| V5 on every WP2.3 still at 8 and 16 bit (planted `iCCP`-dropping writer) | `tests/test_wp41_photo_path.py::test_v5_*` |
| V9 neutral identity, both methods, every still, 8 and 16 bit (planted off-neutral control) | `tests/test_wp41_photo_path.py::test_v9_*` |
| V10: D84, D35, D36, N8, D116, D83, D45 | `tests/test_wp41_photo_path.py::test_v10_*` |
| N10 per S1 | `tests/test_wp41_photo_path.py::test_n10_the_same_still_twice_is_identical` |
| CPU vs GPU within AD-11 | `tests/test_wp41_photo_path.py::test_gpu_export_reports_gpu_and_matches_the_cpu` |
| V8 (a) (b) (c) | `tests/test_wp41_v8.py` |

## Limits

- **DR-42 (a):** a `cICP`-only PNG source is exported without `iCCP` (`io.photo` not owned).
- **DR-43:** a photo exported from a damaged-EXIF source loses the source's EXIF fields (the
  output carries only the minimal D63 block: Orientation, Software, the pixel dimensions) and the
  job reports no warning (a reader-side signal needs an IF-6 decision, AD-20).
- **Small-still domain:** the WP2.3 stills are 96 x 64; V8 k > 1 is shown only on the 1080 x 1920
  look-check crop (skipped without `work/wp1.3/frames`); sizes up to 48 MP are OWED (V15, WP5.2).
- **V9 at 8 bit from 10- and 16-bit sources** (S8): see the ledger for the ruling.
- **N10 with provenance on** (S1): files differ only in the provenance `created` stamp.
- **Runner texts:** the record and every printed line carry the engine's texts with each folder
  the run knows (the output folder, each source's folder, the settings, record and parameter
  folders) shown by its name only, in every spelling the runner can name (as given, resolved,
  without an extended-length prefix, escaped as `ascii_text` escapes it, quoted as `repr` quotes
  it; `tools/headless_export.py` `Redactor`, R1 F1, R2 G2-G4, G6); an `argparse` refusal is
  redacted against the paths its arguments name (R2 G3). A path the run does not know (a drive
  root, or a folder no request, flag or file names) would be printed as the engine gives it. No
  EXIF tag value is printed: a WARNING from `clearwater.io.photo.exif`, and any `%r` argument,
  is shown with `...` in its place (R2 G7).
- **Footage check spellings:** the runner compares paths resolved, without the `\\?\` and
  `\\?\UNC\` prefixes and, where the footage folder exists, by file identity (a share of the
  same drive, a short 8.3 name) (R2 G1). A file system without file identities (`st_ino` 0)
  falls back to the text comparison.
- **`--parameters` and photo provenance (OPEN ITEM, owned by CHARC):** the runner reads the
  forms `PresetStore.import_preset` reads (an AD-13 preset; a preset with only `source` and
  `settings` added). The provenance text `PhotoWriter` embeds for a HEIC given a built-in profile
  carries `"profile"` (WP3.6 `7624f5c`), which both the runner and the accepted importer refuse
  (`unknown keys: profile`, exit 2; R2 G5). The writer-versus-AD-13 key set is banked with CHARC.

## OWED (not limits of the code)

- V5 and V9 on the owner's iPhone HEIC (AD-24 provisional until an owner photo is read), and V5
  "in multiple viewers" (WP5.1's V-table leg).
- The largest photo for N4/D110 (V15, WP5.2).
- DR-42 (a) on real files (WP3.6P).
- The command WP3.6P or WP5.1 would run (outputs under `work/`, never beside a footage source):
  `uv run python tools/headless_export.py <photo> [...] --out work/wp3.6p/out --bit-depth 16 --record work/wp3.6p/record.json`
  and, for V9, the same with `--neutral`.
- No photo look check (owner-reserved).

## Register rows (main `cffd243`)

| Row | Disposition |
|---|---|
| DR-62 | CONSUMER NOTE: the runner runs one `run_batch` on the caller's thread, one job at a time (`tests/test_headless_export.py::test_jobs_run_one_at_a_time_in_order_on_the_callers_thread`); photos use no cache; serialising GUI recompute stays WP4.3's. |
| DR-6 | CONSUMER NOTE: pixels are read only through `io.photo`'s full decode; a truncated JPEG and HEIC are failed items with a readable reason and the batch continues (`...::test_damaged_photos_are_failed_items_and_the_batch_continues`). OPEN (the inventory's). |
| DR-43 | NOT REACHED (question 8); limit stated above. |
| DR-42 | NOT REACHED (`io.photo` not owned); limit (a) stated above. |
| DR-31 | NOT REACHED (`io/photo/png.py` not owned). |
| DR-35 | NOT REACHED: (a) the record shows the refusal text verbatim (`...::test_a_suffix_forming_a_device_name_is_refused_verbatim`); (c) the runner never calls `remove_leftovers`; (d) unchanged. |
| DR-44 | NOT REACHED (WP4.3's). CONSUMER NOTE: a manual run's photo open and preview now run the real reader and method on the shell's workers; `QtJobRunner` unchanged. |
| DR-68 | NOT REACHED (WP4.3's). CONSUMER NOTE: with real methods in `default_engines()`, a manual run's photo preview with short side >= 1080 and sigma >= 32 meets the FFT gate in the GUI process; the export job releases in `_run`'s `finally`; the runner's process ends after its batch. |
| DR-67 | NOT REACHED; CONSUMER NOTE: the root's video leg passes the selected backend inside `export_jobs()` (see "WP4.2 extension points"). |
| DR-69 | NOT REACHED: the runner records `JobResult.device` only. |
| DR-71 | NOT REACHED (`jobs/export.py` not edited). |
| DR-37 (c), DR-1, DR-27 | NOT REACHED (`tools/local_config.py` imported, not edited). CONSUMER NOTE for DR-37 (c): the runner checks outputs, beside-source sources, `--record` and `--settings-dir` against the configured footage folder itself (`...::test_main_refuses_the_configured_footage_folder`). |
| DR-34 | NOT REACHED (`load_settings` and `migrate` used, not edited; `load_settings` renames a corrupt `settings.json` in a `--settings-dir` beside itself, D89, which the runner's docstring states). |
| DR-40 (b), DR-46 | NOT REACHED (`methods/` not owned). |
| DR-73 | NOT REACHED (`core/` not edited). |
| DR-45, DR-47, DR-56, DR-74 | NOT REACHED (video). |
| DR-50, DR-51, DR-52, DR-61 | NOT REACHED (WP4.3). |
| DR-65 | NOT REACHED; CONSUMER NOTE: WP4.1's new tests are small (stills, test-built inputs); the V8 k > 1 leg is `slow`. |
| DR-59 | NOT REACHED (the fixtures generator is not touched). |
