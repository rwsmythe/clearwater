# WP4.1 ledger (photo path end to end)

Cell 1, `implementer-opus-high`, worktree `.worktrees/wp4.1`, branch `wp4.1`, base main `3aa3c51`.
Brief `docs/briefs/wp4.1-brief.md` FINAL (rulings CHARC `2c4476d9869df056`). Reviewer A: Codex
`gpt-6.1-sol` / high, WSL; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.1\rN\`.

## Depth table (figures from the dispatcher's `scripts/cell_depth.py`)

| Yield | Moment | Depth |
|---|---|---|
| Y1 round 0 | 2026-10-28 | 140,680 |

## Task 1: map (main `3aa3c51`)

- `default_engines()` callers: `gui/shell.py` `run` (line 600), `gui/__init__.py` (re-export),
  `tests/test_gui_status.py` (141: `select_backend is stub_era_select_backend`; 145: the selector
  under `force_cpu` with id `"stub"`). `tests/test_gui_startup.py` passes its own engines.
- Product constructions today: `ExportEngine` nowhere in `src/`; `PhotoReader()` only in
  `io/photo/reader.py` `read_photo`, `PhotoWriter()` only in `io/photo/writer.py` `write_photo`;
  `available_methods` defined in `methods/__init__.py`, called nowhere in `src/`.
- `ExportEngine.__init__` needs video collaborators even for photos (`video_source`,
  `sink_factory`, `cache`, `cache_key`); `_photo` reads, selects, measures on `block_mean` at
  `proxy_factor`, renders, writes through `SafeWrite`; provenance via `provenance_object(...)`
  with no `created`, so `created = datetime.now(UTC)` per export (see S1).
- `gui.sources`: `PHOTO_SUFFIXES` (8, incl. `.dng`), `VIDEO_SUFFIXES` (`.mp4`); `route` refuses a
  sidecar (`io.video.inputs.sidecar_fault`) and an unknown suffix
  (`gui.messages.unsupported_extension`: "`<name>` is not a supported photo or video file.").
  `gui.messages` imports PySide6, so the runner duplicates the tables and the text, pinned equal
  by a `gui` test.
- `run_batch` logs `BatchReport.lines()` at INFO, which carries FULL output paths
  (`saved <path>`); its WARNING line carries the failure text (names only in the engine's texts
  the envelope reaches). `PhotoReader` texts carry the file name only.
- Assemblies left unchanged (Q10): `tools/export_bench.py` `build_engine`,
  `tools/export_oracle.py`, `tests/test_jobs_export_support.product_engine`.
- `uv sync` run in the worktree (no `.venv` was present).

## Round 0: design table (task 2)

### R0-1 The composition root (Q1): `src/clearwater/app/composition.py`

Module-level imports: `clearwater` (version), `clearwater.core` (`select_backend`; imports NumPy
and SciPy; CUDA is probed lazily on the first non-forced call, never at import),
`clearwater.io.photo` (`PhotoReader`, `PhotoWriter`; Pillow, pillow-heif), `clearwater.methods`
(`available_methods`), `clearwater.jobs` (`ExportEngine`, `BackendSelector`),
`clearwater.jobs.export_seam` (`ExportJobs`, `ExportRequest`, `unavailable_exports`),
`clearwater.interfaces` (+ `interfaces.stubs` for the never-reached video collaborators, Q4).
No component is built and nothing probed at import. Nothing from `clearwater.gui`, no PySide6,
no `cupy`/`cupyx`. Never resolves `app_locations()`.

| Function | Returns |
|---|---|
| `photo_reader() -> PhotoSource` | a new `PhotoReader()` |
| `photo_writer() -> PhotoSink` | a new `PhotoWriter()` |
| `correction_methods() -> dict[str, CorrectionMethod]` | `available_methods()`: new instances, `"c3"` first then `"ancuti2018"` (D16) |
| `backend_selector() -> BackendSelector` | `clearwater.core.select_backend` itself |
| `export_jobs(*, app_version=clearwater.__version__, reader=None, writer=None, methods=None, select_backend=None, on_stage=None) -> ExportJobs` | a new `_PhotoExports` router (R0-3) over a new `ExportEngine` built from the four functions above (each override, when given, replaces its default; for tests and the V8 recording sink only, Q7) |

`app/__init__.py`: docstring (WP4.1 puts the Qt-free root here; WP4.3 adds the entry point and
start-up beside it, which may import `gui`; `__init__` itself never does) and re-exports of the
five functions. Importing `clearwater.app` therefore loads `composition` (no gui, no CuPy).

### R0-2 The GUI's photo legs (Q3)

`default_engines()`: `photo_source=composition.photo_reader()`,
`methods=composition.correction_methods()`; `video_probe`, `video_source`, `video_sink`,
`cache` and `select_backend=stub_era_select_backend` unchanged; the docstrings updated.
`stub_engines`, `stub_probe`, `stub_era_select_backend`, `STUB_ERA_METHOD_ID` unchanged.
`gui/engines.py` imports `clearwater.app.composition` (the one gui-to-app edge). Kept behaviour
pinned by: `tests/test_gui_status.py:141,145` (selector identity, `"CPU: forced"`),
`tests/test_gui_deps.py` (no gui module imports `clearwater.methods`; `import clearwater.gui.shell`
loads no CuPy; one `app_locations` call), every other `gui` test (they pass their own engines).

### R0-3 Photo/video routing of the root's `ExportJobs` (Q4)

`_PhotoExports.job(request)`: `kind == "photo"` -> the `ExportEngine`'s job; `kind == "video"`
-> `unavailable_exports().job(request)` (fails with `UNAVAILABLE_TEXT`, device `"none"`, writes
nothing). Any other request -> the engine's own `ValueError` (malformed). The engine's video
collaborators are `StubVideoSource((), <minimal ProbeResult>)`, `StubVideoSink`,
`StubProxyCache()` and a `cache_key` that raises; none is reached. WP4.2 extension (DR-67):
`export_jobs()` builds the real `FFmpegVideoSource` / sink factory / `DiskProxyCache` and passes
the selected device backend to source, sink and engine inside `export_jobs()` (new keyword
arguments such as `cache_dir`, additive), then returns the `ExportEngine` itself and deletes
`_PhotoExports`; no public function is renamed.

### R0-4 The runner (Q2, Q5): `tools/headless_export.py`

Library API (imports no PySide6; `--force-cpu` runs import no CuPy):

- `PHOTO_SUFFIXES`, `VIDEO_SUFFIXES`: copies of `gui.sources`' (pinned equal by a `gui` test).
- `route(path) -> Literal["photo", "video"] | str`: as `gui.sources.route` (sidecar -> the D83
  `sidecar_fault` text; unknown suffix -> the GUI's unsupported-extension text; see S3).
- `requests_for(paths, *, parameters: ParameterSet, settings: Settings) -> list[ExportRequest]`:
  one request per path in order; a refused path gives a `RefusedRequest` (S3).
- `parameters_for(method_id, *, file=None, neutral=False) -> ParameterSet` (R0-5).
- `check_outputs(requests, footage_folder) -> None`, raising `RunnerRefusal` (R0-7).
- `run(requests, *, exports=None, progress=None, footage_folder=CONFIGURED) -> RunRecord`: the
  output check, then ONE `run_batch(exports or composition.export_jobs(), ...)` on the caller's
  thread (DR-62), refused requests failing through a wrapper; `RunRecord` holds the
  `BatchReport`, each item's route, the batch wall time.
- `record_json(record) -> str`; `exit_status(record) -> int`; `main(argv=None) -> int`.

CLI: `python tools/headless_export.py PATH [PATH ...]` with
`--out DIR | --beside-source` (exactly one required, Q9), `--suffix S`, `--bit-depth {8,16}`,
`--no-provenance`, `--force-cpu`, `--encoder NAME`, `--quality {high,standard,draft}`,
`--ten-bit`, `--cache-limit-bytes N` (S2), `--method ID` (default `c3`),
`--parameters FILE | --neutral`, `--settings-dir DIR`, `--record FILE`. A flag overrides the
loaded settings only when given. Exit 0: every item `done` / `done with warnings`; 1: any item
`failed`, `cancelled` or `not run`; 2: usage refusal, nothing run (argparse errors, a missing
`--out`, an invalid suffix, an unknown method, an unreadable parameter file, a footage refusal,
an existing `--record` file, S5). Ctrl-C: a `SIGINT` handler (`signal`, portable) sets the
batch's cancel flag; the running job returns `CANCELLED` at its next check (no partial output,
D44), later items `not run` (D45); the old handler is restored after the batch; exit 1. stdout:
the summary lines (names only); stderr: the `[i/n]` progress messages; no logging handler
installed (S6).

Record `"schema": 1` (fields additive only): `schema`, `tool` `"headless_export"`,
`app_version`, `method`, `parameters_from` (`"defaults"`/`"file"`/`"neutral"`), `settings`
(`beside_source` bool, `output_suffix`, `png_bit_depth`, `provenance`, `force_cpu`,
`video_encoder`, `quality_level`, `ten_bit_for_eight_bit`, `cache_limit_bytes`; no folder path),
`counts` (`BatchReport.counts()`), `cancelled`, `elapsed_s`, and `items`: `index`, `source`
(NAME only), `kind` (`"photo"`/`"video"`/`"refused"`), `state`, `outputs` (names), `warnings`,
`failure` (the engine's text verbatim, DR-35 (a)), `device`, `elapsed_s` (information only).
WP4.2 adds video options (`--cache-dir` and the like) and record fields, never renaming one.

### R0-5 Settings and parameters (Q6)

Settings: `config.load_settings(--settings-dir)` when given, else `Settings()`; flags overlaid
with `dataclasses.replace`; `last_parameters` ignored. The app-data folder is never resolved.
Parameters: `--parameters FILE` read as JSON, `config.migrate("preset", data)`,
`ParameterSet.from_dict`, `config.check_parameter_set_keys`, its `source`/`settings` provenance
keys dropped as `PresetStore` import drops them (S7); or `--neutral`: every IF-3 parameter of
`--method` at its `neutral`; else the method defaults (`new_parameter_set(method, {})`, defaults
filled by `effective_parameters`). Method id checked against `composition.correction_methods()`.

### R0-6 V8 (Q7)

(a) `tests/test_wp41_v8.py` (parallel): a recording wrapper of `c3` through
`export_jobs(methods=...)`; its measured statistics equal `gui.imaging.measure_statistics`
on the image `default_engines().photo_source` reads, bit for bit. Needs `gui.imaging` (PySide6),
so this test is `gui`-marked (serial leg). (b) k = 1 EXACT (`gui`): a recording writer through
`export_jobs(writer=...)`; `gui.imaging.render_host` at k = 1 equals the pre-write pixels bit for
bit; the 16-bit PNG re-read equals them within half a 16-bit step. (c) `slow` (+ `gui`): the
centre 1080 x 1920 crop of a `work/wp1.3/frames` frame (read as `tests/test_methods_assembly_v8.py`
reads it, skip without it) written as a 16-bit PNG under `tmp_path`, exported by `run()`;
`render_host(downscale(source, k))` against `downscale(re-read output, k)` at k = 2, 4: mean
<= 1/255, p99 <= 2/255 (k = 2) and <= 4/255 (k = 4); p99.9 and max recorded, never asserted.
Planted: (a) statistics of the full image differ; (b) a writer double scaling one pixel by one
16-bit step fails the k = 1 equality; (c) a preview rendered with statistics of a different
frame misses the bound.

### R0-7 Footage and output rules (Q9; DR-37 (c))

The footage folder is read from `clearwater.local.toml` (`tools/local_config.py`
`load_local_config`) when that file exists; absent file -> no folder to protect; present but
unreadable -> exit 2. Refused (exit 2, nothing run): `--out` inside it; `--beside-source` with
any source inside it; a `--record` file or `--settings-dir` inside it. Comparison on
`Path.resolve()` + `os.path.normcase`, `is_relative_to`, by the runner itself. The library
`run()` applies the same check (`footage_folder=CONFIGURED` reads the config; tests pass a
`tmp_path` folder or None). Every write goes through `ExportEngine` and `SafeWrite`; the record
file is the runner's own write.

### R0-8 Tests (markers, leg)

| File | Content | Leg |
|---|---|---|
| `tests/test_app_composition.py` | fresh instances per call; `c3` first; `backend_selector() is core.select_backend`; overrides used; photo routed to the engine (a still exported, `force_cpu`); video -> `UNAVAILABLE_TEXT`, nothing written; subprocess: `import clearwater.app` loads no PySide6/shiboken6/cupy/cupyx; static AST: only `app/composition.py` constructs `ExportEngine`/`PhotoReader`/`PhotoWriter` or calls `available_methods()` in `src/clearwater/` (`read_photo`/`write_photo` excepted by name) | parallel |
| `tests/test_app_deps.py` (ruling flag (3) names it; S4) | `gui/engines.py` is the only gui module importing `clearwater.app`; no `app` module imports `clearwater.gui`/PySide6 at module level | parallel |
| `tests/test_headless_export.py` | routing; settings/parameters sources; exit 0/1/2; record schema and no `tmp_path` string in any record; footage refusals (planted folder); subprocess: no PySide6, and no CuPy with `--force-cpu`; library cancel and Ctrl-C (`signal.raise_signal` in-process from an `on_stage` hook); DR-62 order; DR-6 truncated JPEG and HEIC -> failed items, batch continues; DR-35 (a) suffix forming `NUL`; a `.mp4` -> `UNAVAILABLE_TEXT` item | parallel |
| same file, `gui` | the suffix tables and the unsupported-extension text equal `gui.sources`/`gui.messages` | serial |
| `tests/test_wp41_photo_path.py` | V5 (every still, 8 and 16 bit, c3; planted `iCCP`-dropping writer), V9 (both methods, every still, 8 and 16 bit; planted off-neutral control), V10 (D34/D84/D35/D36/N8/D116/D83/D45 legs), N10 (S1), DR-6 | parallel, parametrised per still so each test is sub-second (timed at build; any above a few seconds marked `slow` with a reason) |
| same file, `gpu` | CPU vs GPU pre-write pixels within 2e-3 max / 2e-4 mean; `device == "GPU"`; skips without CUDA | serial |
| `tests/test_wp41_v8.py` | R0-6 (a) (b) `gui`; (c) `gui` + `slow` | serial |
| `tests/test_wp41_gui.py` | `make_window(default_engines())` opens a WP2.3 still: size label, `Device: CPU: forced` under `force_cpu` | serial (`gui`) |

### R0-9 Questions the brief and rulings leave open (STOP; recommended answer first)

- **S1 (premise mismatch, reproduced).** Task 6 N10 says two exports of one still are
  byte-identical "(same parameter set, so the provenance is equal)". They are not with provenance
  on: `ExportEngine._photo` calls `provenance_object` without `created`, so each export stamps
  `datetime.now(UTC)`. Reproduction (scratch script, `jpeg-gradient-srgb`, `force_cpu`, c3, two
  exports each): `provenance=True: byte_identical=False sizes=1895,1895`;
  `provenance=False: byte_identical=True sizes=1075,1075`. Recommended: N10 asserts byte-identical
  PNGs with `--no-provenance`, and with provenance on every PNG chunk equal except the provenance
  `iTXt`, whose JSON is equal but for `created` (N10/D92 is about pixels; `jobs/` is not owned).
- **S2.** Q5 lists nine flags but the ruling says "full IF-10 flag set"; `cache_limit_bytes` is an
  IF-10 field missing from the list. Recommended: add `--cache-limit-bytes N` now.
- **S3.** A sidecar or unknown-suffix path must be a failed item while the batch continues (V10).
  Recommended: the runner refuses it as `gui.sources.route` does (same texts, `"<name>: <text>"`),
  carried through the one `run_batch` as a `RefusedRequest` (a frozen subclass of
  `ExportRequest` with a `refusal` field, `kind="photo"` as an unused placeholder) that a wrapper
  `ExportJobs` fails at once (device `"none"`, nothing opened); the record's `kind` is
  `"refused"`. Alternative: send a sidecar to the engine as a photo request (the engine's
  `_prepare` gives the D83 text) and refuse an unknown suffix at usage (exit 2).
- **S4.** Ruling flag (3) names `tests/test_app_deps.py`, which the brief's owned list does not.
  Recommended: treat it as granted by the ruling.
- **S5.** Usage refusals not named by the brief: a `--out` that does not exist and an existing
  `--record` file. Recommended: both exit 2 (the first keeps the engine's folder-path failure
  text out of every record; the second never overwrites a file).
- **S6.** Logging. Recommended: the runner installs no logging handler, so `run_batch`'s INFO
  report (full output paths) is not emitted; Python's last-resort handler prints the WARNING
  lines (names only). Alternative: a handler filtering paths.
- **S7.** `--parameters FILE`: Recommended: the AD-13 preset or provenance JSON; `source` and
  `settings` dropped; `--method` with `--parameters` is a usage refusal (the file names its
  method).

### R0-10 Rulings on Y1 (orchestrator, 2026-10-28; CHARC informed)

Table R0-1..R0-8 APPROVED as written.

- S1 RULED (a): AD-11 defines N10 as bit-identical PRE-ENCODE; the provenance `created` stamp is
  metadata. Assert byte-identical files with provenance OFF; with provenance ON every chunk equal
  except the provenance `iTXt`, whose JSON is equal in every key but `created`; decoded pixels
  bit-identical in both. Reproduction of record (scratch `n10_repro.py`, `jpeg-gradient-srgb`,
  `force_cpu`, c3, two exports each): provenance on, sizes 1895/1895, NOT identical; provenance
  off, sizes 1075/1075, identical.
- S2 RULED: add `--cache-limit-bytes N` (the full IF-10 flag set).
- S3 RULED as recommended: `RefusedRequest` failed inside the one `run_batch`, kind
  `"refused"`, batch continues; a sidecar and an unknown suffix pinned by tests.
- S4 GRANTED: `tests/test_app_deps.py`; allows exactly `gui/engines.py ->
  clearwater.app.composition`; importing `clearwater.app` and `clearwater.app.composition`
  loads no PySide6 and no CuPy.
- S5 RULED: a missing `--out` exits 2; an existing `--record` exits 2, never overwritten.
- S6 RULED: no logging handler installed by the runner; its docstring says so.
- S7 RULED: `--parameters` takes AD-13 preset or provenance JSON, `source`/`settings` dropped
  as `PresetStore` import does; `--method` with `--parameters` exits 2 with a readable text.
