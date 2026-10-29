# WP4.1 report: photo path end to end

**Status:** FINAL (cell 4, 2026-10-28), branch `wp4.1` on base main `3aa3c51`. Brief
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
  `inside`, `write_target_refusal`, `check_outputs`, `run`, `record_object`, `record_json`, `exit_status`,
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

(Test node ids.)

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
| Runner (Reviewer A round 4): every write target (each output folder as the export plans it, the record, the settings folder and file) checked by the real path of its nearest existing path, so a file link, a folder link or a dangling link into the footage folder is refused; a local-configuration refusal names no full path; `--parameters` validated against the method schema and capped at 1 MiB, as the importer does | `tests/test_headless_export.py::test_i1_*` to `::test_i4_*` |
| Runner (Reviewer B at the gate): one write-target predicate refusing every class found (text spelling, `\\?\`, `\\.\`, file link, junction, folder link elsewhere, hard link plus stream, another case); a non-ASCII folder hidden in any case; an overflowing `settings.json` stamp a usage refusal; Ctrl-C in the last commit and during the record write give status 1 | `tests/test_headless_export.py::test_b1_*`, `::test_b2_*`, `::test_b4_*`, `::test_b5_*`, `::test_b6_*` |
| N10 pre-encode: the writer's incoming pixels bit-identical across the four runs (Reviewer B B7) | `tests/test_wp41_photo_path.py::test_n10_the_same_still_twice_is_identical` |
| Runner (Reviewer A round 5): a parameter file whose `created` stamp overflows in UTC is a usage refusal | `tests/test_headless_export.py::test_j1_a_created_stamp_out_of_range_is_a_usage_refusal` |
| V5 on every WP2.3 still at 8 and 16 bit (planted `iCCP`-dropping writer); the Interop IFD kept on a test-built JPEG (no WP2.3 still carries one; planted drop) | `tests/test_wp41_photo_path.py::test_v5_*` |
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
  folders, the local configuration's folder (R4 I2)) shown by its name only, in every spelling the runner can name (as given, resolved,
  without an extended-length prefix, escaped as `ascii_text` escapes it, quoted as `repr` quotes
  it, each escape in any letter case of its character (Reviewer B B2); `tools/headless_export.py`
  `Redactor`, R1 F1, R2 G2-G4, G6); an `argparse` refusal is
  redacted against the paths its arguments name (R2 G3). A path the run does not know (a drive
  root, or a folder no request, flag or file names) would be printed as the engine gives it. No
  EXIF tag value from the EXIF module's own WARNINGs is printed: each argument of a WARNING from
  `clearwater.io.photo.exif`, and any `%r` argument, is shown with `...` in its place (R2 G7).
  The library `run()` applies the same filter while its batch runs (R3 H3).
- **EXIF content in failure texts (Reviewer B B3):** the runner adds no EXIF content and no
  location tag of its own, but the record carries the engine's failure texts verbatim apart from
  folder redaction (DR-35 (a)), and a reader failure text (`clearwater.io.photo`, not owned; for
  example a malformed TIFF Orientation) may quote the malformed tag's value; so may the summary
  line and the batch WARNING carrying the same text. It is not a location tag.
- **Host logging (R3 H4):** a process that installs its own logging handlers (a host program,
  pytest) receives the engine's records as they are logged, full paths and tag values included
  (`run_batch`'s INFO report and WARNINGs, the photo modules' WARNINGs). The runner redacts what
  it prints and records, not another program's logging.
- **GUI preview of an nclx-only Display P3 photo (R3 H1, BANKED to WP4.3 by CHARC
  `5fab48cc2a5174cb`):** the GUI preview of an nclx-only P3 photo is shown unconverted until
  WP4.3; the export is correct (it embeds the D53 built-in Display P3 profile). The `gui` display
  path passes only the source's ICC profile to `display_image` (WP3.16), and the real reader the
  WP4.1 swap installs gives such a photo no ICC profile. The WP2.3 P3 stills carry ICC profiles,
  so the shipped fixtures do not reach it.
- **The footage check (Reviewer B B1, CHARC Q1):** one predicate,
  `write_target_refusal`, decides every write the run plans, before anything runs, when a
  footage folder is configured: each output folder as `jobs.naming` plans it (`--out`, or the
  source's own folder beside a source), the record file, the `--settings-dir` folder and its
  `settings.json`. A target passes only if (i) after its drive or UNC prefix it has no `:` (no
  NTFS stream name) and is not a `\\?\` or `\\.\` path; (ii) every existing path on the way
  down is its own real path (no symbolic link, junction or other reparse point, and no short
  8.3 name, so a link or short name is refused even when it leads elsewhere); (iii) the real path
  of the deepest existing one is outside the footage folder (compared resolved, prefix-free,
  case-normalised and, where the footage folder exists, by file identity; a file system without
  file identities falls back to the text comparison). **Residual:** a hard link to a footage
  file placed outside the footage folder cannot be told apart by its path; the runner never
  writes over an existing file (D84), so only a stream name could reach the original, and (i)
  refuses every stream name. A link created after the check (during the run) is not seen.
- **Ctrl-C (Reviewer B B5, B6):** a Ctrl-C after the last item's last check (in its commit)
  keeps that output and still gives status 1 with `"cancelled": true` (the runner reads the
  cancel flag when the batch ends); the SIGINT handler stays installed until the record is
  written, so a Ctrl-C then leaves the record whole and gives status 1. A record that cannot be
  written is removed only if this run created it, absent a concurrent replacement of the path
  by another process (B9, out of envelope).
- **GUI test scope (Reviewer B B8):** `tests/test_wp41_gui.py` asserts that the shell opens the
  real reader's image with the real methods and the forced CPU; the corrected preview's pixels
  are asserted by the export legs, not there.
- **`--parameters` and photo provenance (OPEN ITEM, owned by CHARC):** the runner reads the
  forms `PresetStore.import_preset` reads (an AD-13 preset; a preset with only `source` and
  `settings` added), with its 1 MiB cap and its method-schema validation (R4 I3, I4). The provenance text `PhotoWriter` embeds for a HEIC given a built-in profile
  carries `"profile"` (WP3.6 `7624f5c`), which both the runner and the accepted importer refuse
  (`unknown keys: profile`, exit 2; R2 G5). The writer-versus-AD-13 key set is banked with CHARC.
- **Importer `OverflowError` (accepted component, banked, R5 J1):** a preset whose `created`
  stamp overflows when normalised to UTC (`0001-01-01T00:00:00+01:00`) escapes the accepted
  `PresetStore.import_preset` as `OverflowError` (`ParameterSet.from_dict`; not owned). The
  runner refuses it (exit 2); the importer's behaviour is an item for the orchestrator
  (reproduction `C:\Users\rwsmy\clearwater-review-evidence\wp4.1\r5\r5_repro.py`).

## OWED (not limits of the code)

- V5 and V9 on the owner's iPhone HEIC (AD-24 provisional until an owner photo is read), and V5
  "in multiple viewers" (WP5.1's V-table leg).
- The largest photo for N4/D110 (V15, WP5.2).
- DR-42 (a) on real files (WP3.6P).
- The command WP3.6P or WP5.1 would run (outputs under `work/`, never beside a footage source):
  `uv run python tools/headless_export.py <photo> [...] --out work/wp3.6p/out --bit-depth 16 --record work/wp3.6p/record.json`
  and, for V9, the same with `--neutral`.
- No photo look check (owner-reserved).

## Figures

**V8 (c)** (`tests/test_wp41_v8.py`, `slow`, on the 1080 x 1920 look-check crops; 1/255; AD-11
as amended 2026-10-21: mean <= 1, p99 <= 2 at k = 2 and <= 4 at k = 4; p99.9 and max recorded,
never asserted). From the hardware leg on `755513b` (`-m "gpu or slow"` on
`test_wp41_photo_path.py` + `test_wp41_v8.py`: 2 passed, 0 skipped, RTX 4070 Laptop):

| Frame | k | mean | p99 | p99.9 | max |
|---|---|---|---|---|---|
| GX011625_0024.925 | 2 | 0.093 | 1.105 | 8.874 | 29.729 |
| GX011625_0024.925 | 4 | 0.266 | 3.696 | 12.850 | 28.039 |
| GX011625_0114.648 | 2 | 0.084 | 0.472 | 2.783 | 29.354 |
| GX011625_0114.648 | 4 | 0.292 | 1.363 | 4.428 | 22.683 |

**V9 raw figures** (CHARC ruling S8; from the S8 probe recorded in the ledger, before
`755513b`: 66 stills x {c3, ancuti2018} x {8, 16} = 264 runner exports, `--neutral`, CPU):
against the source quantised to the export depth by the writer's rule, max 0.0000/255 and mean
0.0000/255 on all 264; against the unquantised source, 8-bit sources at either depth and every
16-bit export max 0.0019/255, mean 0.0012/255; 8-bit exports of 10- and 16-bit sources worst
mean 0.256/255, max 0.499/255 (8-bit quantisation alone; recorded, not asserted, per S8). The V9
test records the raw error of every export (`record_property`). The stacked candidate gate
re-runs both: the GPU and V8 (c) legs in its serial leg, V9 (with the pinned built-in ICC oracle
of R3 H6) in its parallel leg.

## Gates

- ruff check, ruff format --check (259 files), mypy strict (141 source files): green on
  `23fc88b`; the WP4.1 files plus `test_gui_deps`, `test_gui_status`, `test_core_deps`,
  `test_jobs_naming`, `test_jobs_export_photo` (`-n 4 -m "not gpu and not footage and not
  slow"`): 465 passed, 0 skipped.
- The two-leg suite: run by the orchestrator's stacked candidate gate; counts and skip lines in
  `docs/proofs/wp4.1-accept.md`.

## Reviewer A

STRONG tier (Codex `gpt-6.1-sol` / high, WSL, codex-cli 0.162.1), whole-package diff from
`3aa3c51` each round, prior rounds withheld; evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp4.1\r1\` to `r5\`; ledger
`docs/proofs/wp4.1-ledger.md`.

| Round | Head | Critical | Major | Minor | Verdict |
|---|---|---|---|---|---|
| 1 | `ef6bf2f` | 0 | 2 (F1 path privacy, F3 settings version) | 6 | NEW_CRITICAL_MAJOR_FOUND; fixed |
| 2 | `dca6d1e` | 0 | 2 (G1 extended-path footage check, G2 non-ASCII folder) | 5 | NEW_CRITICAL_MAJOR_FOUND; fixed |
| 3 | `899102d` | 0 | 1 (H1 GUI preview, accepted code: BANKED to WP4.3) | 6 | NEW_CRITICAL_MAJOR_FOUND; minors fixed |
| 4 | `844b996` | 0 | 1 (I1 linked source beside-source) | 4 | NEW_CRITICAL_MAJOR_FOUND; fixed (I1 broadened to every write target) |
| 5 | `f17ab36` | 0 | 0 | 1 (J1) | NO_NEW_CRITICAL_MAJOR; J1 fixed in the cleanup (`23fc88b`) |
| Reviewer B (gate) + remediation | `aefd563` (stacked candidate = `0a0a787` rebased) | 0 | 1 (B1 hard link plus stream; B2-B4 MAJOR reported, MINOR as adjudicated) | 8 (B2-B9; B9 out of envelope) | BLOCKING; remediated per CHARC `870c8ddeb64b4e12` (one predicate, B1; B2, B4-B7 fixed; B3, B8, B9 narrowed) |

The Reviewer A loop terminated at round 5, the five-round gate, on a round with zero new
blocking findings; the orchestrator's Reviewer B at the gate then found B1, remediated in one
bounded turn (the design guard closes with the single predicate).

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
