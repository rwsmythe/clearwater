# WP4.1 — Photo path end to end (dispatch brief, FINAL)

**Status:** FINAL 2026-10-28 (CHARC `2c4476d9869df056`, rulings below, which take precedence over the text above them); DRAFT 2026-10-28, written by a drafting helper for the orchestrator (generation 16)
from CHARC's Phase 4 commission `159c14fb79ad1aae` (section 1 lanes, section 2 the WP4.1 anchor).
Base = the main commit named at dispatch (drafted on `6536f60`). CHARC rules the questions below
and approves the FINAL before dispatch. Owner decisions: none inside the package (the photo look
check, any spec text and anything relaxing a mandatory requirement are owner-reserved: a STOP).
- Spec **v0.5.5**: D16, D22, D34-D36, D44, D45, D53, D63, D81, D83-D85, D87, D91, D92, D107,
  D110, D111, D116; G7, G8, G10; N1, N3, N4, N8, N10; V5, V8, V9, V10; sections 8.1, 8.3, 8.4,
  10.1. Architecture FINAL 1.0: section 1 (modules incl. `app`), 2 ("photo" data flow), 3 (IF-1,
  IF-2, IF-3, IF-6, IF-8 with its "Export seam" paragraph, IF-9, IF-10), 6, 7. AD-4, AD-5 (the
  540 rule as the photo statistics basis), AD-8, AD-9, AD-11 (V8, V9, N10 bounds, as amended),
  AD-13, AD-19, AD-20, AD-24, AD-25 (a), AD-28, AD-29.
- Plan section 6 Phase 4 row WP4.1 (size M; depends on WP3.4, WP3.6, WP3.13, WP3.14, WP3.15;
  feeds V5, V8, V9, V10): "replaces stubs with real components for photos, and adds a headless
  runner under `tools/` so acceptance tests can drive an export without the interface. The runner
  is a test tool, not a product feature." Plan 8.1: `clearwater.app` "Entry point and start-up |
  WP4.3"; the dependency rule ("`gui` and `jobs` reach correction methods only through IF-3").
- Reports and accepts: WP3.4 "Consumer notes" (WP3.14 item: `render` returns a new `Image` on the
  image's device) and claim 10 (V9 at method level: neutral gives max 0, mean 0); WP3.6 "Limits"
  and question 11 (WP3.6P, "not a blocker for WP3.6's accept or WP4.1"); WP3.13 "Consumer notes";
  WP3.14 "Limits" and its brief Q9 (`run_batch` "for WP4.1's runner"); WP3.15 "Callers"; WP3.16
  accept "Debt and consumer notes" (R3-1 photo statistics basis, "S1's `default_engines` c3
  adapter is removed by WP4.3"); WP3.16 brief question 5 (the photo statistics basis "binds WP3.14
  and WP4.1"); WP3.17 accept (keep `"c3"` first in `engines.methods`); WP3.21 accept (FFT gate,
  `release_fft_plans` in the job's `finally`).
- Cell: `implementer-opus-high` (commission section 1: a composition package across every
  frozen-interface consumer, design choices at round 0). Tier **STRONG**, Claude lane: Reviewer A
  (your loop) and Reviewer B (the orchestrator's seat) are Codex at the pin `gpt-6.1-sol` / high.
- Worktree `.worktrees/wp4.1`, branch `wp4.1` from main, base = the main commit named at dispatch.
- May run CONCURRENTLY with WP-T5 (DR-65; disjoint files: the four export tests DR-65 names and
  their shared fixture). Neither edits the other's files.

**Why.** Every photo component is on main and WP3.14's engine already exports a photo through the
real reader, method and writer, but only tests and tools assemble them (`tools/export_bench.py`
`build_engine`, `tools/export_oracle.py`, `tests/test_jobs_export_support.product_engine`); no
product module does, and the shell's `default_engines()` still serves `StubPhotoSource({})` and
`{"stub": StubCorrectionMethod()}`. WP4.1 makes ONE product place that builds the real photo
engines, points the GUI's photo legs at it, and gives acceptance tests a headless way to drive an
export (WP5.1 builds on it; WP4.2 extends it for video).

| Field | Content |
|---|---|
| ID and title | WP4.1 — Photo path end to end; plan section 6 Phase 4 row WP4.1 |
| Goal | (1) The **composition root**: a new Qt-free product module (question 1: `clearwater.app.composition`) that is the ONE place building the real engines for photos — `io.photo` `PhotoReader` and `PhotoWriter`, `methods.available_methods()` (`c3` first, then `ancuti2018`), `core.select_backend`, `config` (injected `Locations`, settings and parameter loading per question 6) and `jobs.ExportEngine` behind the `ExportJobs` seam for photos. Video legs are NOT built here (question 4; WP4.2). (2) `gui/engines.py` `default_engines()` takes its photo legs and methods from the root (question 3); `stub_engines()` and the video stubs unchanged. (3) A **headless runner** under `tools/` (question 2: `tools/headless_export.py`), a test tool, whose library API and CLI drive a photo export or batch through the root and `clearwater.jobs.run_batch` without loading PySide6, designed so WP4.2 extends it without rewriting (question 5). (4) The photo legs of V5, V9, V10 and the WP4.1 part of V8 shown through the runner on the WP2.3 stills and test-built inputs; the owner-photo leg recorded OWED. |
| Spec / decision clauses | Section 8.1 "PNG, user-selectable 8-bit or 16-bit, with an embedded ICC profile matching the source primaries"; "all EXIF preserved except fields made invalid by processing (D63)"; "Provenance ... on by default, can be turned off (D91)". 8.3 "same folder as the source by default"; "Photos change extension to `.png`"; "existing files are never overwritten; a number is appended ... cross-format photo clashes such as `IMG_1234.HEIC` and `IMG_1234.JPG` (D84)". 8.4 "written to a temporary name and renamed ... only on success (D85)". V5 "EXIF preserved except D63 fields; orientation correct for rotated and portrait sources in multiple viewers; ICC profile present and matching; selected bit depth honored". V8 "screen-resolution preview vs downsampled full-resolution output differ by less than a threshold set at design; 1:1 view exact" (threshold: AD-11 as amended 2026-10-21, "k = 1 is EXACT"; k > 1 "on real-sized content (at least 1080p)" mean ≤ 1/255, p99 ≤ 2/255 at k = 2, ≤ 4/255 at k = 4; "Small stills and synthetic noise are outside V8's domain"). V9 "with every stage set to its neutral value ... the output matches the input within a small color-difference tolerance for photos ... including color tags and ICC handling" (AD-11: max ≤ 2/255, mean ≤ 0.2/255). V10 "collision numbering, cross-format photo clashes, and no source or existing output ever overwritten". G7 "apply one parameter set or preset; run unattended; report per-item success, warnings and failures at the end ... (D80, D81)"; D45 "Cancel during batch stops the whole remaining batch". D116 "ProRAW/DNG ... refused with a clear message in v1". D111 "Automatic CPU fallback ..."; AD-9 the device reason in each job's log. N10/D92 + AD-11 "the same device ... bit-identical output pre-encode; CPU vs GPU within 2e-3 ... max, 2e-4 mean". N8 "source files never modified; existing outputs never overwritten". Spec 10.1 / plan 8.1 dependency rule. AD-29 "nothing outside `clearwater.core` imports `cupy`/`cupyx`". |
| Depends on | On main: WP3.4 (accept `ad15ab4`: `clearwater.methods.available_methods`, `AncutiFusionMethod`, `Parameter.neutral`), WP3.6 (`d0f00ee`/`4ec835d`: `clearwater.io.photo` `PhotoReader`, `PhotoWriter`, `PhotoReadError`), WP3.13 (`6dd5a00`: `plan_output`, `SafeWrite`, `Reservations`), WP3.14 (`ba6e923`: `ExportEngine`, `effective_parameters`, `run_batch`, `BatchReport`), WP3.15 (`da54a47`: `clearwater.config` `Locations`, `load_settings`, `PresetStore`, `migrate`), WP3.1 (`f4acbd0`: `clearwater.core.select_backend`, `backend_for`), WP3.19 (`f6e1687`: `clearwater.jobs.export_seam`), WP3.16 (`0c41615`: `gui/engines.py`, `gui/contract.Engines`), WP2.3 (`d605925`: the stills in `tests/fixtures/stills/`, the `sample` fixture), WP3.21 (`7e228fb`: the FFT gate and `release_fft_plans`). Nothing unmerged. |
| Debt and decided items | Every register row (main `cffd243`) whose Signal / trigger names WP4.1, "WP4.x", or a module this package touches or composes; dispositions in the table below. Decided: the S1 adapter `stub_era_select_backend` is removed by WP4.3, not here (WP3.16 accept); `"c3"` stays first in `engines.methods` (WP3.17 accept); the photo statistics basis is the 540 block mean, `gui.imaging.measure_statistics` = `ExportEngine._photo` (WP3.16 Q5, R3-1; already pinned bit for bit by `tests/test_jobs_export_photo.py::test_photo_statistics_equal_the_previews_bit_for_bit`). |
| Files owned | NEW (names per questions 1, 2): `src/clearwater/app/__init__.py` (docstring and the root's exports only; imports nothing from `clearwater.gui`, so WP4.3's entry point can live beside it without a cycle), `src/clearwater/app/composition.py` (the root); `tools/headless_export.py` (the runner); `tests/test_app_composition.py`, `tests/test_headless_export.py`, `tests/test_wp41_photo_path.py` (the V5, V8, V9, V10 legs; split further by round 0 if useful, every new file `tests/test_wp41_*.py` or the two above); `docs/reports/wp4.1-photo-path.md`; `docs/proofs/wp4.1-ledger.md`. EDIT: `src/clearwater/gui/engines.py` (WP3.16; `default_engines()` photo legs and methods from the root, the module docstring; `stub_engines`, `stub_probe`, `stub_era_select_backend` and `STUB_ERA_METHOD_ID` unchanged, question 3). NOT owned: `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN, AD-20); `src/clearwater/gui/contract.py` (frozen contract; `Engines` unchanged) and every other `gui/` module (`shell.py` keeps `run(engines or default_engines(), ...)`); `src/clearwater/jobs/` (incl. `export.py`, `export_seam.py`, `batch.py`); `io/`, `methods/`, `core/`, `config/`, `analysis/`, `cache/`, `color/`; `tools/export_bench.py`, `tools/export_oracle.py`, `tools/photo_check.py` (WP3.6P's instrument), `tools/local_config.py` (imported, not edited); `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/gui_support.py`, `tests/fixtures/`; every existing test file (they pass unchanged; a needed change is a STOP for a ruling); `pyproject.toml`, `uv.lock` (no new dependency). |
| Interfaces provided | The root's public functions (round 0 fixes the names; proposed: `photo_reader()`, `photo_writer()`, `correction_methods()`, `backend_selector()`, `export_jobs(*, app_version=..., reader=None, writer=None, methods=None, select_backend=None, on_stage=None) -> ExportJobs`), each returning a fresh real component; the overrides exist for tests and the V8 recording sink only (question 7). The runner's library API and CLI and its record schema 1 (question 5). No frozen interface changes; `gui.contract` unchanged; the seam unchanged. |
| Interfaces consumed | IF-1 `Image`; IF-2 `select_backend` (AD-1, AD-9, D111) and `ArrayBackend` (`asarray`, `to_host`); IF-3 `CorrectionMethod` (`id`, `parameters` incl. `neutral`, `stages`); IF-6 `PhotoSource`, `PhotoSink`, `PhotoMetadata`; IF-8 `Progress`, `JobResult`; IF-9 `ParameterSet` (`from_json`); IF-10 `Settings`; the seam `ExportRequest`, `ExportJobs`, `CANCELLED`, `UNAVAILABLE_TEXT`, `unavailable_exports`; `clearwater.jobs` `ExportEngine`, `run_batch`, `BatchReport`; `clearwater.config` `Locations`, `load_settings`, `migrate`, `check_parameter_set_keys`. |
| Consumers | WP4.2 (extends the root with the video legs, DR-67, and the runner with the video kind); WP4.3 (the entry point in `clearwater.app` passes the root's engines to `shell.run` and `install_export_panels(window, exports)`; removes the S1 adapter); WP5.1 (the acceptance suite drives V5, V8, V9, V10, V11 through the runner); WP3.6P (may run the runner on the owner's photos); WP5.2 (V15's photo leg, the largest photo). |
| Hardware flags | No EXCLUSIVE timing window: WP4.1 records no figure of record (the runner's `elapsed_s` is information only). The full suite runs in a GRANTED window (two legs, AD-28). `gpu` (one CPU-vs-GPU leg), `gui` (the `default_engines` leg), `slow` (the V8 k > 1 leg, question 7) are serial-leg tests; everything else runs in the parallel leg on the CPU (`force_cpu=True`). No `footage` read: the V8 crop is a working-folder file (`work/wp1.3/frames`, as `tests/test_methods_assembly_v8.py` reads it) and the test skips without it. |
| Out of scope | Every video leg (WP4.2: probe, decode, analysis, cache, render, encode; `device_backend`, DR-67); the GUI wiring of panels, start-up detection, `remove_leftovers` at start-up, the S1 adapter's removal, the shell's device line wording (WP4.3); V7, V18; V11 beyond what WP3.14 proved (WP5.1); V15 and the largest-photo memory figure (WP5.2, N4/D110); real owner photos (WP3.6P, OWED here); the photo look check (owner-reserved); any change to `io.photo`, `methods`, `core`, `jobs`, `config` or the interfaces; GPMF, IMU, GPS or any location tag (never read, decoded or logged; the fixtures carry none: manifest `has_gps: false`). |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict (the new package and the runner included), the full suite per the fill's GATE_CHECKS at dispatch (the two-leg gate) green in a granted window, every existing test unchanged (incl. `tests/test_gui_status.py`, `tests/test_gui_deps.py`, `tests/test_jobs_naming.py::test_importing_jobs_loads_no_gui_methods_or_heavy_libraries`, `tests/test_jobs_export_photo.py`); the root is the only product module that constructs the real photo engines (a static test); the runner exports every WP2.3 still family at 8 and 16 bit with V5, V9, V10 shown and the WP4.1 V8 legs (question 7) shown, each with a planted control that fails by name; the owner-photo leg recorded OWED in the report and the accept; every register row below dispositioned in the report; Reviewer A converged. |

**Register rows (main `cffd243`).**

| Row | Why it is cited | Disposition |
|---|---|---|
| DR-62 | Trigger names WP4.1: "the headless runner (WP4.1) runs one activity at a time by construction". | CONSUMER NOTE: the runner runs one `run_batch` on the caller's thread, one job at a time; a test pins the order (job i+1 starts after job i returned). Photos use no cache; WP4.2's video leg keeps the property. Serialising GUI recompute stays WP4.3's. |
| DR-6 | "any package that reads photo pixels (it must validate the file itself)". | CONSUMER NOTE: pixels are read only through `io.photo`'s reader (full decode); a truncated JPEG and HEIC built under `tmp_path` go through the runner as FAILED items with a readable reason, nothing written, the batch continuing (D81). The row is the inventory's; it stays OPEN. |
| DR-43 | Damaged EXIF dropped with a log warning only; trigger "WP3.14 (export) or the next touch of `io.photo`". | NOT REACHED (question 8): a user-visible warning needs a reader-side signal (IF-6, AD-20, or `io.photo`, not owned). The report's limits state that a photo exported from a damaged-EXIF source carries no EXIF and the job reports no warning. |
| DR-42 | `io/photo/` colour descriptions; trigger WP3.6P. | NOT REACHED (`io.photo` not owned; WP3.6P's). The report's limits carry (a) for the export path (a `cICP`-only PNG is exported without `iCCP`). |
| DR-31 | (1) the PNG keyword rule "if the stdlib writer is adopted". | NOT REACHED (`io/photo/png.py` not owned; the root only constructs `PhotoWriter`). |
| DR-35 | `src/clearwater/jobs/`: (a) device-name refusal, (c) `remove_leftovers`, (d) NumPy at import. | NOT REACHED: (a) the runner's record shows the refusal text verbatim (a test with a suffix forming `NUL`); the GUI text is WP4.3's. (c) the runner never calls `remove_leftovers` (WP4.3 start-up). (d) unchanged. |
| DR-44 | (c) "WP4.3 real-engine wiring". | NOT REACHED (WP4.3's). CONSUMER NOTE: after the swap a manual run's photo open and preview run the real reader and method on the shell's workers; `QtJobRunner` is unchanged. |
| DR-68 | cuFFT plans per thread; "the GUI preview is the product case". | NOT REACHED (WP4.3's binding row). CONSUMER NOTE: with real methods in `default_engines()`, a manual run's photo preview with short side ≥ 1080 and sigma ≥ 32 meets the FFT gate in the GUI process; the export job releases in `_run`'s `finally`; the runner's process ends after its batch. |
| DR-67 | BINDING for WP4.2 (`device_backend` on source, sink, engine). | NOT REACHED here; CONSUMER NOTE: the round-0 table names where the root's video leg will pass the selected backend, so WP4.2 adds it without reshaping the root. |
| DR-69 | Job device-wide estimate not reportable (IF-8 frozen). | NOT REACHED: the runner records `JobResult.device` only. |
| DR-71 | "The next touch of `jobs/export.py`". | NOT REACHED (`jobs/export.py` not edited). |
| DR-37 (c), DR-1, DR-27 | `tools/local_config.py`. | NOT REACHED (imported, not edited). CONSUMER NOTE for DR-37 (c): the runner's footage refusal (question 9) checks the output folder against the configured footage folder itself and does not rely on `local_config`'s one-way nesting check. |
| DR-34 | `config/` next touch of `presets.py`, `settings_store.py`, `log.py`. | NOT REACHED (read-only use of `load_settings` and `migrate`). |
| DR-40 (b), DR-46 | `methods/`. | NOT REACHED (`methods/` not owned). |
| DR-73 | `core/backend.py` (WP4.2's touch). | NOT REACHED (`core/` not edited). |
| DR-45, DR-47, DR-56, DR-74 | "WP4.2" / "WP4.x" video triggers. | NOT REACHED (video). |
| DR-50, DR-51, DR-52, DR-61 | "WP4.3" GUI triggers. | NOT REACHED (WP4.3). |
| DR-65 | Suite cost (WP-T5, concurrent). | NOT REACHED; CONSUMER NOTE: WP4.1's new tests stay small (stills, test-built inputs); any test above a few seconds is `slow` with a reason. |
| DR-59 | `tools/fixtures/stills.py` XMP scan. | NOT REACHED (the fixtures generator is not touched; WP4.1's PNG outputs are not samples). |

## Task ladder

1. **Read and map.** `gui/engines.py`, `gui/contract.py` (`Engines`, `SelectBackend`),
   `gui/sources.py` (`route`, `PHOTO_SUFFIXES`, `VIDEO_SUFFIXES`, `open_photo`),
   `gui/imaging.py` (`downscale`, `statistics_factor`, `measure_statistics`, `render_host`,
   `preview_export_difference`), `jobs/export.py` (`ExportEngine.__init__`, `_run`, `_photo`),
   `jobs/export_seam.py`, `jobs/batch.py`, `io/photo/__init__.py`, `methods/__init__.py`,
   `core/backend.py` (`select_backend`), `config/__init__.py`, `config/settings_store.py`,
   `config/presets.py`; the three existing assemblies (`tools/export_bench.py` `build_engine`,
   `tools/export_oracle.py`, `tests/test_jobs_export_support.py` `product_engine`). List every
   caller of `default_engines` (today: `gui/shell.py` `run`, `tests/test_gui_status.py`).
2. **Round 0 yield: the design table.** In the ledger, before product code: the root's module
   path and public functions with signatures (question 1), what each returns and what it imports
   at module level versus inside the function (nothing that probes CUDA or builds a component at
   import); how `default_engines()` takes the photo legs (question 3) and which existing test
   pins each kept behaviour; the photo/video routing of the root's `ExportJobs` (question 4);
   the runner's library API, CLI flags, exit statuses, record schema and the WP4.2 extension
   points (question 5); settings and parameter sources (question 6); the V8 legs (question 7);
   the footage and output rules (question 9); the test list with markers and expected leg; the
   `scripts/cell_depth.py` figure your dispatcher gives you. YIELD. A choice the brief leaves
   open is a STOP.
3. **The composition root.** Build it per the ruled table. Each call returns fresh instances;
   `correction_methods()` is `available_methods()` (`c3` first, D16); `backend_selector()` is
   `clearwater.core.select_backend` itself; `export_jobs()` builds `ExportEngine` with the real
   photo reader, writer, methods and selector and `clearwater.__version__` as `app_version`
   (D91), and routes video requests per question 4. Never resolves `app_locations()` and never
   reads the real app-data folder (question 6). CHECK: importing `clearwater.app.composition`
   loads no PySide6/shiboken6 and no `cupy`/`cupyx` (subprocess, as `tests/test_gui_deps.py`
   does); no module under `src/clearwater/` other than the root constructs `ExportEngine`,
   `PhotoReader`, `PhotoWriter` or calls `available_methods()` (static AST test; the defining
   modules' own `read_photo`/`write_photo` conveniences excepted by name).
4. **The GUI's photo legs.** `default_engines()`: `photo_source` and `methods` from the root;
   everything else unchanged (question 3). CHECK: `tests/test_gui_status.py` and every `gui`
   test pass unchanged; `tests/test_gui_deps.py` passes unchanged (no `gui` module imports
   `clearwater.methods`; importing `clearwater.gui.shell` loads no CuPy); a new `gui` test opens a
   WP2.3 still through `default_engines()` in the shell (`make_window`) and shows its size and
   `Device: CPU: forced` under `force_cpu`; a new static test: `gui/engines.py` is the only
   `gui` module importing `clearwater.app`.
5. **The headless runner.** Per question 5: requests built from paths (kind by suffix, tables
   equal to `gui.sources`' by a `gui`-marked test), settings and parameters per question 6, one
   `run_batch` over the root's `export_jobs()`, a JSON record per run and per item (source NAME
   only, never a full path, as AD-13 rules for provenance; kind; state; output names; warnings;
   failure; `device`; `elapsed_s`), a cancel through an injected `Progress` (library) and Ctrl-C
   (CLI: the job's cancel flag set, the batch stops per D45, nothing partial left per D44).
   CHECK: the runner process loads no PySide6 (subprocess `sys.modules` check) and, with
   `--force-cpu`, no CuPy; refusals per question 9; a video path in WP4.1 yields the question-4
   failure as a failed item; exit statuses as ruled.
6. **The photo legs through the runner** (CPU, `force_cpu=True`, both methods where cheap; every
   output under `tmp_path`; committed samples read only):
   - **V5** on every WP2.3 still (`jpeg-*`, `heic8-*`, `heic10-*`, `png8-*`, `png16-*`,
     `tiff8-*`, `jpeg-orient-{land,port}-o{1,3,6,8}`, `heic-ad24-*`) at 8 and 16 bit: IHDR bit
     depth equals the setting (D22); `iCCP` equals the source's ICC bytes (manifest `icc_md5`) or
     the D53 built-in for a tagged HEIC without one (`io.photo.writer.built_in_profile`), none for
     an untagged source; EXIF per D63 (Orientation normal, no thumbnail, dimensions updated,
     Software Clearwater; every other field of the fixture preserved); orientation: output pixels
     against an independent decode of the source (Pillow `ImageOps.exif_transpose` for JPEG; the
     manifest's AD-24 expectation for each `heic-ad24-*`). "In multiple viewers" is WP5.1's leg
     (V-table); this package records it as such. Provenance present and parseable when on, absent
     when off (D91). Planted: a writer double that drops `iCCP` fails the ICC assertion by name.
   - **V9**: every parameter at its IF-3 `neutral` (the runner's `--neutral`), both methods, every
     still, 8 and 16 bit: the output re-read through `PhotoReader` against the source read the
     same way, max ≤ 2/255, mean ≤ 0.2/255 (AD-11), colour description and ICC bytes unchanged.
     Planted: one control off neutral misses the bound.
   - **V10** as a runner batch in a `tmp_path` source folder (D34 default and the output-folder
     setting both): `IMG_1234.HEIC` and `IMG_1234.JPG` give `IMG_1234_corrected.png` and
     `IMG_1234_corrected_2.png` (D84); a planted existing output is byte-identical afterwards and
     the new one numbered (D35); a custom suffix (D36); every source's bytes and mtime unchanged
     (N8); a DNG (`dng-by-extension`, `dng-by-tag`) and a `.THM` sidecar are failed items with the
     D116 / D83 text while the batch continues (D81); a cancel after item 1 leaves item 1's output
     and runs no later item (D45, G8).
   - **V8** per question 7.
   - **N10**: the same still exported twice on the same device gives byte-identical PNGs (same
     parameter set, so the provenance is equal).
   - **GPU** (`gpu`, skips without a usable CUDA device): a still exported without `force_cpu`
     reports `device == "GPU"` and its pre-write pixels are within AD-11's CPU-vs-GPU bound of the
     CPU export's.
7. **Owner-photo leg: OWED.** The report and the accept list it as owed rows, not limits of the
   code: V5 and V9 on the owner's iPhone HEIC (AD-24 provisional until an owner photo is read),
   the largest photo for N4/D110 (V15, WP5.2), DR-42 (a) on real files; the runner command
   WP3.6P or WP5.1 would run is written out. No photo look check (owner-reserved).
8. **Review loop** (below), then the full suite in a granted window.

## Declared operating envelope

Windows 11; Python 3.12; the CPU backend (`force_cpu=True`) for every parallel-leg test; the RTX
4070 Laptop GPU (8 GB) for the one `gpu` leg; the WP2.3 stills (≤ 2 MB each, small sizes such as
96 x 64) and test-built inputs under `tmp_path` (up to the 1131 x 1700 PNG of
`tests/test_jobs_export_photo.py` and the 1080 x 1920 V8 crop); ONE export job at a time, one
runner process at a time; outputs only under `tmp_path` (tests) or a `work/` folder (manual runs);
the GUI headless on `offscreen`. Out of envelope: owner photos and their sizes up to 48 MP (OWED),
several concurrent runners, a source folder the user cannot write when outputs go beside the
source, other operating systems (portable code, not run there), video (WP4.2).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (Codex `-m gpt-6.1-sol -c model_reasoning_effort=high`, WSL transport, probe
  first, one `^ succeeded in` line before round 1), run by you at your seat to convergence;
  five-round gate. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.1\rN\`; ledger
  `docs/proofs/wp4.1-ledger.md`. Copy the runner and prompt shape from WP3.21's last round folder
  (`...\wp3.21\r2\`); the banner must read `gpt-6.1-sol` (a round whose banner reads another pin is
  void); exclude `docs/proofs` with `--glob '!docs/proofs/**'`; prior rounds WITHHELD.
- **WHAT TO EXAMINE:**
  - composition: the root is the ONE product place building the real photo engines; every call
    returns fresh components; nothing is built or probed at import; the GUI and the runner take
    theirs from it; no real video component is built in WP4.1;
  - layering: `clearwater.app.composition` Qt-free and CuPy-free at import; no `gui` module but
    `engines.py` imports `clearwater.app`; no `gui` module imports `clearwater.methods`;
    `clearwater.jobs` unchanged and still loads no `gui`, `methods`, PySide6 or CuPy; no cycle
    once WP4.3 adds an entry point under `clearwater.app`;
  - the runner: no PySide6; outputs never inside the footage folder and never beside a footage
    source (question 9); every write through `ExportEngine` and `SafeWrite`; exit statuses and the
    record match its docstring; kind routing equals `gui.sources`; a video request fails readably;
    cancel per D44/D45; no full path, EXIF content, GPS or location tag in any record or log line;
  - the V legs assert what the spec and AD-11 say, on the claimed samples, each planted control
    failing for the stated reason;
  - GUI: every existing `gui` test unchanged and green; `default_engines()` real photo open and
    preview; `"c3"` first;
  - nothing in `interfaces/`, `gui/contract.py`, the seam or an unowned file changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate (Codex, the same pin).

## Notes for the cell

- **Yields.** Task 2 (round 0): the table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating; make NO
  change in the turn that adjudicates a round. Your dispatcher gives you the
  `scripts/cell_depth.py` figure at every yield: put it in the ledger; ~250K is the evaluation
  point ("REVIEW ONLY this turn" when told), ~400K STOP.
- **Windows (plan 4.3, AD-28).** No timing window is needed. The full suite and the `gpu` leg run
  ONLY in a window the dispatcher grants: ask with `WINDOW REQUEST: <what, expected duration>`;
  one heavy job at a time; at least 5 GiB free before a leg
  (`uv run python -c "import psutil; assert psutil.virtual_memory().available >= 5*2**30"`);
  send `WINDOW RELEASED: <summary>` after each. The suite runs in the background from Git Bash
  with `QT_QPA_PLATFORM=offscreen` and `PYTEST_ADDOPTS` unset, output under `work/`, with
  foreground poll-wait calls on its done marker (a reaped run is not a result):
  `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp4.1-<run>-parallel`
  then `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp4.1-<run>-serial`.
  Light runs between: the files you touch plus `tests/test_gui_deps.py`, `tests/test_core_deps.py`,
  `tests/test_jobs_naming.py`, `tests/test_gui_status.py`, `tests/test_jobs_export_photo.py`.
- **Footage and data rules.** The footage folder `C:\Users\rwsmy\clearwater-footage\` is
  read-only and this package does not need it; never point a temp root, an output folder or the
  runner at it. Every output under `tmp_path` or `work/`. No GPMF packet, IMU, GPS or location tag
  is read, decoded or logged.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20), `gui/contract.py`, the
  seam, `jobs/`, `io/`, `methods/`, `core/`, `config/` or another unowned file; an existing test
  that would have to change; a defect found in an accepted component (report it with a
  reproduction; do not patch it); a new dependency; OS-specific code; any write outside
  `tmp_path`/`work/`; the round-0 table showing a choice the brief left open; an owner-reserved
  item (the photo look check, spec text).
- **Working rules:** `uv sync`. Commit inside the worktree by pathspec with `git -c
  core.autocrlf=false commit -m "feat(wp4.1): ..." -- <paths>`, conventional commits carrying
  the package id, a `Co-Authored-By:` footer naming your model; every committed blob LF. Never
  `git stash`; never `git clean -x`. Never a bare `cd`. Never post to a mailbox. Gates: ruff
  check, ruff format --check, mypy strict, the two-leg suite (in a window); no harness gate.
  Google docstrings on every public module, class and function; `clearwater/app/__init__.py`
  says what WP4.1 put there and what WP4.3 adds.
- **Return report** = your FINAL message, under about 60 lines, to your dispatcher by your
  messaging tool: the root's surface; the GUI swap; the runner's surface and the WP4.2 extension
  points; each V leg with samples and result; the DR dispositions; the OWED rows; the gates with
  both legs' counts and skip lines; the Reviewer A rounds and verdict; open items.
- **Report** `docs/reports/wp4.1-photo-path.md`: claims with evidence (test node ids), the root
  and runner surfaces, the WP4.2 extension notes, limits (DR-42 (a), DR-43, the small-still
  domain of the fixtures), the OWED rows, the register table.

## Questions for CHARC (recommended answer first)

1. **The composition root's module (a new package: CHARC's pass).** Recommended:
   `src/clearwater/app/composition.py` in a NEW package `clearwater.app` (plan 8.1 already names
   `clearwater.app`, "Entry point and start-up | WP4.3"; architecture section 1 lists `app`).
   WP4.1 creates the package with the Qt-free root only; WP4.3 adds the entry point and start-up
   beside it; `app/__init__.py` never imports a GUI module. Alternatives: a single module
   `src/clearwater/app.py` (WP4.3 must then turn it into a package); `src/clearwater/composition.py`
   at top level (a thirteenth module plan 8.1 does not name).
2. **The runner's path and name.** Recommended: `tools/headless_export.py` (says what it does;
   sits beside `export_bench.py`/`export_oracle.py`; importable by tests through
   `pythonpath = ["tools"]`). Alternatives: `tools/run_export.py`; `tools/headless.py`.
3. **How `gui/engines.py` takes the photo legs.** Recommended: `default_engines()` calls the root
   for `photo_source` and `methods`; `select_backend` stays `stub_era_select_backend` (identical
   to `core.select_backend` for `c3`/`ancuti2018`; WP3.16's accept gives its removal to WP4.3, and
   `tests/test_gui_status.py` pins `default_engines().select_backend is stub_era_select_backend`);
   video members stay stubs. This makes `gui/engines.py -> clearwater.app.composition` the one
   GUI-to-app edge (pinned by a test); the methods arrive as IF-3 objects, so plan 8.1's rule
   holds and `tests/test_gui_deps.py` passes unchanged. Alternative: the root builds `Engines`
   itself (`clearwater.app.gui_engines()`, importing `gui.contract` lazily) and `shell.run`'s
   default switches to it (edits `shell.py`, not owned; leaves `default_engines()` a stub).
4. **Video requests reaching WP4.1's `ExportJobs`.** Recommended: the root's `export_jobs()`
   routes `kind == "photo"` to the `ExportEngine` and `kind == "video"` to
   `unavailable_exports().job(request)` (fails with `UNAVAILABLE_TEXT`, writes nothing); the
   engine's video collaborators are the interface stubs and are never reached; WP4.2 replaces the
   video branch with the real engine and removes the router. Alternative: one `ExportEngine` over
   the stubs, letting a video job fail inside `StubVideoSource` (a less readable failure, and a
   stub on a product path).
5. **The runner's surface and WP4.2's extension.** Recommended: a library API
   (`requests_for(paths, *, kind="auto", parameters, settings) -> list[ExportRequest]`,
   `run(requests, *, exports=None, progress=None) -> RunRecord`, `record_json(record) -> str`,
   `main(argv) -> int`) over `run_batch` and the root; a CLI with EVERY IF-10 field except
   `last_parameters` as a flag now (`--out`, `--beside-source`, `--suffix`, `--bit-depth`,
   `--no-provenance`, `--force-cpu`, `--encoder`, `--quality`, `--ten-bit`), plus `--method`,
   `--parameters FILE`, `--neutral`, `--record FILE`; exit 0 when every item is done (with or
   without warnings), 1 when any item failed, was cancelled or not run, 2 for a usage refusal;
   record `"schema": 1`, fields additive only. WP4.2 then changes the root's video branch and adds
   only video-specific options (`--cache-dir` and the like) and record fields, never renaming or
   removing one. Alternative: photo flags only now; WP4.2 adds the video flags.
6. **Settings and parameters.** Recommended: settings = `Settings()` defaults overlaid by the
   flags; `--settings-dir DIR` optionally loads `config.load_settings(DIR)` first (tests pass a
   `tmp_path` folder); the real app-data folder is never resolved by the root or the runner (the
   WP3.15 isolation rule; WP4.3's entry point resolves `app_locations()` and passes it in);
   parameters = `--parameters FILE` (an IF-9 / exported-preset JSON per AD-13, read through
   `config`'s migration and `check_parameter_set_keys`), or `--neutral` (every parameter at its
   IF-3 `neutral`, V9), or the method defaults for `--method` (default `c3`, D16). Alternative:
   the runner reads the user's app-data settings by default (breaks test isolation and makes
   acceptance runs depend on the machine).
7. **V8 in WP4.1 (owner-reserved? no: AD-11 sets the bound).** Recommended three legs: (a) the
   statistics the root's photo job measures equal `gui.imaging.measure_statistics` on the photo
   `default_engines()` reads, bit for bit (the WP3.14 test's assertion through the product
   composition); (b) k = 1 EXACT: the GUI's `render_host` at k = 1 equals the job's pre-write
   pixels bit for bit (a recording writer passed through the root's test override), and the
   written 16-bit PNG equals them within half a 16-bit step; (c) k > 1 on real-sized content: the
   centre 1080 x 1920 crop of a WP1.3 look-check frame (as `tests/test_methods_assembly_v8.py`
   reads it) written as a 16-bit PNG under `tmp_path`, exported through the runner, preview
   against the downscaled output within AD-11's amended bound at k = 2 and 4 (mean ≤ 1/255, p99
   ≤ 2/255 and ≤ 4/255; p99.9 and max recorded), `slow`, skipping without the frames. The leg
   through the running shell is WP4.3's. Alternative: (a) and (b) only (the WP2.3 stills are
   outside V8's k > 1 domain, so k > 1 would wait for WP4.3 or WP5.1).
8. **DR-43 (damaged EXIF lost silently on export).** Recommended: NOT REACHED here; a warning
   needs a reader-side signal (an IF-6 field: AD-20, a STOP; or an `io.photo` change: not owned);
   the report states the limit and the row stays OPEN for WP3.6P or a CHARC-commissioned IF-6
   decision. Alternative: grant `io/photo/reader.py` an additive non-IF warnings attribute and have
   the root fold it into `JobResult.warnings` (needs a `jobs/export.py` grant as well; wider).
9. **Outputs and the footage folder.** D34's default writes beside the source, so a runner given
   a footage source would write INTO the footage folder. Recommended: the runner requires `--out`
   (a folder outside the configured footage folder) unless `--beside-source` is given, and
   refuses (exit 2, nothing run) `--beside-source` for any source inside the configured footage
   folder and any `--out` inside it, checking the resolved paths itself when
   `clearwater.local.toml` exists (DR-37 (c)); the library API applies the same check; tests use
   `tmp_path` sources for the D34 leg. Alternative: always require `--out` (D34's default then
   untestable through the runner).
10. **The three existing assemblies.** `tools/export_bench.py`, `tools/export_oracle.py` and
    `tests/test_jobs_export_support.product_engine` build their own engines. Recommended: leave
    them unchanged (not owned; they are instruments and fixtures, and the static "one place" test
    covers `src/clearwater/` only); WP4.2 decides whether the bench builds through the root when
    it binds DR-67. Alternative: grant WP4.1 the bench and the oracle to build through the root
    now (touches WP3.21's measured instruments; no gain for photos).

## Rulings (CHARC `2c4476d9869df056`, 2026-10-28, verbatim; they GOVERN the Questions section above)

PRIMARY: orchestrator. Thread `159c14fb79ad1aae`, reply to `8c3c624c224c263e` (+ `56e00cce74e65b5c`, `528b3db814b6d2c5`). **RULING PACKET: all four drafts APPROVED with the rulings below; every helper recommendation ADOPTED except where a line says otherwise. Write the rulings verbatim into each brief, commit on `briefs-p4`, ff main; dispatch WP4.1 (opus-high) and WP-T5 (by pace) now; WP4.2 and WP4.3 stay DRAFT until their predecessor's accept plus one revision pass, then FINAL on my word.** Tripwire passes (new package `clearwater.app`, the WP4.3 modules, `python -m clearwater`, the leftover journal) are all GRANTED here.

**Flags.** (1) WP4.2 Q3 narrowing ACCEPTED (N4 ground: the stub analysis over a real source stores ~23 GB for GX011625; the GUI's video legs swap in WP4.3 with the adapter). (2) withdrawn; see 43-Q13. (3) tripwires GRANTED as listed; the `gui/engines.py -> clearwater.app.composition` edge is the ONE gui-to-app edge, pinned by `tests/test_app_deps.py`. (4) the two S1 tests go in WP4.3 (43-Q11); WP-T5's three bodies as T5-Q2/Q3/Q4. (5) noted; my "~30 min" is CORRECTED to the helper's ~12 min projection, W1 replaces it.

**Addendum.** (1) WP4.3's V8 legs cite AD-11 AS AMENDED 2026-10-21 (k = 1 EXACT; k > 1 mean <= 1/255, p99 <= 2/255 at k = 2 and <= 4/255 at k = 4, max recorded never asserted), the same text as WP4.1 line 301. (2) 41-Q3 + 43-Q11 ruled together as recommended: `default_engines()` stays, takes its photo legs and methods from the root in WP4.1, its selector and video legs in WP4.3; `shell.run` and `gui/__init__.py` unedited. (3) WP4.2's DR-35 clause STRUCK.

**WP4.1 (M, opus-high, Codex nets).** Q1 GRANTED: new package `clearwater.app` with `__init__.py` (Qt-free exports only, never imports `gui`) and `composition.py`; plan 8.1 already names `app`. Q2 `tools/headless_export.py`. Q3 as recommended (S1 selector stays until WP4.3). Q4 as recommended (video -> `unavailable_exports().job(request)`; WP4.2 removes the router). Q5 as recommended: full IF-10 flag set now, exit 0/1/2, record `schema: 1` additive only. Q6 as recommended (no app-data resolution in root or runner; `--settings-dir` optional). Q7 three legs (a)(b)(c); (c) `slow`, skips without `work/wp1.3/frames`. Q8 DR-43 NOT REACHED (an IF-6 field is an AD-20 decision; not now). Q9 as recommended (`--out` required unless `--beside-source`; both refused for the footage folder or a source inside it; tests on `tmp_path`). Q10 as recommended (bench, oracle, `product_engine` unchanged). WP3.6P owner-photo leg OWED in report and record.

**Cost restated:** unchanged from the commission except WP-T5's saving (~12 min per gate, not ~30) and one extra short window for it.
