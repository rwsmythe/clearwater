# WP4.1 ledger (photo path end to end)

Cell 1, `implementer-opus-high`, worktree `.worktrees/wp4.1`, branch `wp4.1`, base main `3aa3c51`.
Brief `docs/briefs/wp4.1-brief.md` FINAL (rulings CHARC `2c4476d9869df056`). Reviewer A: Codex
`gpt-6.1-sol` / high, WSL; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.1\rN\`.

## Depth table (figures from the dispatcher's `scripts/cell_depth.py`)

| Yield | Moment | Depth |
|---|---|---|
| Y1 round 0 | 2026-10-28 | 140,680 |
| Y4 round 1 adjudicated | 2026-10-28 | 299,161 (past the 250K evaluation point: last bounded step in this seat) |

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

## Build log

- Task 3 root `157273a`; task 4 GUI swap `4ee4ea7`; runner `f8464f5`; runner tests (35, 2.5 s)
  committed. Light runs green: `test_app_composition` (10), `test_app_deps` (6),
  `test_gui_deps`, `test_core_deps`, `test_jobs_naming` (129 with the two above),
  `test_gui_status`, `test_gui_deps`, `test_gui_startup` (32, offscreen).

### S8 (STOP, Y3; reproduced) V9 at 8 bit from 10- and 16-bit sources

Task 6 V9: "every still, 8 and 16 bit: ... max <= 2/255, mean <= 0.2/255 (AD-11), colour
description and ICC bytes unchanged". Probe (scratch `v9_probe.py`, `v9_probe2.py`; 66 stills x
{c3, ancuti2018} x {8, 16} = 264 runner exports, `--neutral`, `force_cpu`, outputs under
`work/wp4.1-v9probe`, 4.0 s):

- 36 of 264 miss mean <= 0.2/255, ALL at 8 bit from a source above 8 bit (heic10-*, png16-*):
  worst mean 0.256/255 (`heic10-gradient-*`), max 0.499/255. That is 8-bit quantisation alone
  (a uniform rounding error has mean 1/4 step): against the source rounded to the export depth
  the error is max 0.0000/255, mean 0.0000/255 on all 264.
- 8-bit sources at either depth and every 16-bit export: max 0.0019/255, mean 0.0012/255.
- Colour description (primaries, transfer, matrix, range) equal on all 264. ICC bytes differ
  on the 10 HEIC stills without an embedded profile (`heic8/10-*-none`, `heic-ad24-*`): the
  output carries the D53 built-in profile, as V5 requires.

Recommended: V9's reference is the source quantised to the export bit depth (the user chose
the reduction; V9 tests that the neutral pipeline is the identity), bound max <= 2/255 and
mean <= 0.2/255 as AD-11 says; the raw figure against the unquantised source is recorded, and
asserted at 16 bit and for 8-bit sources. ICC: equal to the source's, or to the D53 built-in
where V5 requires it. Alternative: assert V9 at 16 bit only for sources above 8 bit.

### S8 RULED (CHARC `6c108416f38ca32a`, thread `159c14fb`, reply to `ec230a99`; relayed by the orchestrator, verbatim)

"S8 RULED by CHARC: (A), not owner-reserved. AD-11 defines V9 pre-encode, and AD-10 reads V9
"on the decoded-RGB side with the encoder excluded". The bound (max <= 2/255, mean <= 0.2/255)
is unchanged. Four conditions, all in the test: (1) assert against the source quantised to the
export depth by the writer's own rounding rule (the product's rule, so the identity shows 0/0
as your probe did); (2) record the raw error against the unquantised source, and assert it for
every 16-bit export and every 8-bit source; (3) ICC equal to the source's, or the D53 built-in
where V5 requires one; correct the brief's "ICC bytes unchanged" to that in the ledger; (4) the
planted control as briefed. CHARC is adding a dated AD-11 clarification to docs/decisions.md at
its seat; do not edit that file."

**Brief correction (condition 3):** task 6 V9's "colour description and ICC bytes unchanged"
reads, for WP4.1: colour description (primaries, transfer, matrix, range) unchanged; ICC bytes
equal to the source's, or to the D53 built-in (`io.photo.writer.built_in_profile`) where V5
requires one. Implemented in `tests/test_wp41_photo_path.py::test_v9_neutral_is_the_identity`:
reference `io.photo.png._quantise` (clip, round half to even) at the export depth; the raw error
recorded per export (`record_property`) and asserted at 16 bit and for 8-bit sources.

W1 (WP-T5 timed serial leg) opened 19:21:35Z; my light runs from that moment until the notice
reached me (the S8 probes and three light pytest runs) are recorded by the orchestrator as a
small perturbation. From the notice: no runs.

### Light runs after W1 (granted 20:08Z) and the hardware leg

- ruff check / format --check / mypy green at `755513b` (mypy: 141 source files); 8 ruff
  findings in the three new test files fixed (import order, unused `noqa`, two long lines).
- Parallel light run `work/wp4.1-light-7`: 271 passed, 1 failed (7.2 s): the V9 planted control.
  Reason, 1-parameter probe (scratch `v9_planted.py`, `jpeg-gradient-srgb`, every other
  parameter neutral, max / mean in 1/255): `c3_strength` 1.0 -> 0.000 / 0.000,
  `white_balance_strength` 1.0 -> 0.000 / 0.000, `alpha` (ancuti2018) 1.0 -> 0.000 / 0.000,
  `sharpen_strength` 1.0 -> 23.584 / 12.362, `gamma` 1.5 -> 21.682 / 12.982. A strength at its
  default changes nothing while the stage it scales is neutral, so the control is now `gamma`
  (accepted by the orchestrator); the 4 planted tests pass.
- gui-not-slow run `work/wp4.1-light-8`: 29 passed (18 s); extra `work/wp4.1-light-9`: 141 passed.
- Window (granted, 20:12:11Z-20:12:40Z, 10.7 GiB available): `-m "gpu or slow"` on
  `test_wp41_photo_path.py` + `test_wp41_v8.py`: 2 passed, 0 skipped (28.0 s). V8 (c) figures
  (1/255; bound mean <= 1, p99 <= 2 at k = 2, <= 4 at k = 4; p99.9 and max recorded only):

| Frame | k | mean | p99 | p99.9 | max |
|---|---|---|---|---|---|
| GX011625_0024.925 | 2 | 0.093 | 1.105 | 8.874 | 29.729 |
| GX011625_0024.925 | 4 | 0.266 | 3.696 | 12.850 | 28.039 |
| GX011625_0114.648 | 2 | 0.084 | 0.472 | 2.783 | 29.354 |
| GX011625_0114.648 | 4 | 0.292 | 1.363 | 4.428 | 22.683 |

## Reviewer A

Transport WSL, Codex v0.162.1, `gpt-6.1-sol` / high (STRONG). Evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp4.1\rN\` (prompt, diff, transcript, adjudication,
md5s). Probe 20:14:34Z: one `succeeded in` line, banner `gpt-6.1-sol` / high.

### Cumulative round ledger

| Round | Head | Critical | Major (blocking) | Minor | In / out envelope | New / reopened | Reverts | Fixes touch | Depth |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `ef6bf2f` | 0 | 2 (F1, F3) | 6 (F2 downgraded, F4-F8) | 8 / 0 | 8 / 0 | 0 | runner (`tools/`, F1-F4), root docstring (F6), report (F5, F7), one test (F8) | 299,161 |

### Round 1 (20:14-20:24Z) -- VERDICT NEW_CRITICAL_MAJOR_FOUND; adjudicated, NOT yet remediated

- F1 MAJOR CONFIRMED (in envelope): path privacy. The D87 refusal text names the output folder
  and reaches the record verbatim (reproduced: `"failure": "jpeg-gradient-srgb.jpg: Not enough
  free space in C:\...\work\wp4.1-r1-repro\out: need 1,085,440 bytes, 0 free."`); the usage
  refusal of a missing parameter file (OSError text) and `load_settings`'s corrupt-file WARNING
  print full paths to stderr.
- F2 MAJOR reported, CONFIRMED as MINOR: `--record` named as a planned output PNG -> export
  committed, then `FileExistsError` escapes `main` (reproduced). Contrived argument; nothing harmed.
- F3 MAJOR CONFIRMED (in envelope): a settings file with `format_version` 99 ->
  `UnsupportedFormatVersionError` escapes `main` instead of exit 2 (reproduced).
- F4 MINOR CONFIRMED: a loaded `output_suffix` is not validated at usage.
- F5 MINOR CONFIRMED: `load_settings` may rename a corrupt `settings.json`; docstring and the
  report's DR-34 line say read-only.
- F6 MINOR CONFIRMED: importing `clearwater.core` builds its module-level `NumpyBackend`; the
  root's "nothing is built" is too wide.
- F7 MINOR CONFIRMED: DR-43 limit text (the output keeps a minimal EXIF block; the source fields
  are lost).
- F8 MINOR CONFIRMED (test-only): the N10 chunk filter matches a keyword prefix.
- Mechanical: VERDICT anchored; 32 `succeeded in`; `tokens used` 171,507; two start-up ERROR lines
  from offline network connectors (not the exec channel), the rest echoed source: round COUNTS.

### Round 1 remediation (orchestrator GO at Y4; adjudication APPROVED as written)

Orchestrator condition on F1: one redaction helper applied at every exit point (record fields,
stdout, stderr); plant BOTH a D87 refusal and a corrupt-settings WARNING; assert no `tmp_path`
string in the record or the captured output.

- Failing first: five new tests in `tests/test_headless_export.py` (`test_f1_*` x2, `test_f2_*`,
  `test_f3_*`, `test_f4_*`) ran RED on `c6aabc0` (`work/wp4.1-r1fix-red.log`: 5 failed, each for
  its finding: the D87 text with `C:\...\out`, the WARNING with the settings path,
  `UnsupportedFormatVersionError` escaping, `FileExistsError` escaping, exit 1 for a loaded
  `a/b` suffix), then GREEN.
- `bf4b837` (runner): `Redactor` (every known folder, as given and resolved, backslash,
  doubled-backslash and forward-slash spellings, case-insensitive, shown by its NAME) applied to
  record `failure`/`warnings`, the stderr refusal and progress lines and, through a filter on
  `logging.lastResort` for the duration of `main` (no handler installed), every WARNING printed;
  `folders_of(requests)` + the settings, record and parameter folders; `RunRecord.folders`;
  `run(..., known_folders=())`. F3: `load_settings` errors (`OSError`, `ValueError` incl.
  `UnsupportedFormatVersionError`) are a usage refusal (exit 2). F2: `--record` must end in
  `.json` (exit 2); a record file appearing during the run is not written (message, exit 1). F4:
  the effective suffix is validated after the overlay. F5: the docstring states the loader's
  rename (D89).
- `d22f1aa`: F6 root docstring ("builds none of the root's components and probes no device";
  core's module-level CPU backend named); F8 N10 filter matches the keyword plus NUL and asserts
  exactly one chunk set aside; F5 report DR-34 line; F7 report DR-43 limit (the minimal D63 block
  is written; the source fields are lost).
- Light runs on `d22f1aa`: ruff check, ruff format --check (259 files), mypy (141 files) green;
  `-n 4 -m "not gpu and not footage and not slow"` over the six WP4.1 test files plus
  `test_gui_deps` and `test_gui_status`: 306 passed (18.7 s, `work/wp4.1-r1fix-light.log`).

## RESUME HERE (cell 2, after cell 1)

**State at hand-over (2026-10-28, cell 1 at depth 299,161):** head `d22f1aa` on branch `wp4.1`
(base main `3aa3c51`; NO rebase, never merge). Worktree clean apart from this ledger commit.
Every committed blob LF, 0 CR. `.venv` present (`uv sync` done).

**Done:** round-0 table (R0-1..R0-10) and rulings S1-S8 above; tasks 3-7 built: the root
(`src/clearwater/app/`), the GUI swap (`gui/engines.py`), the runner (`tools/headless_export.py`),
the tests (`tests/test_app_composition.py`, `tests/test_app_deps.py`,
`tests/test_headless_export.py`, `tests/test_wp41_photo_path.py`, `tests/test_wp41_v8.py`,
`tests/test_wp41_gui.py`), the report draft (`docs/reports/wp4.1-photo-path.md`). The hardware
leg (gpu + v8c) ran in its window on `755513b` (figures above); it has NOT re-run since the
round-1 fixes (they touch no hardware-marked test; the full gate covers it). Reviewer A round 1
adjudicated, approved and remediated.

**Round table so far:** round 1 on `ef6bf2f`: 0 critical, 2 major blocking (F1, F3), 6 minor
(F2 downgraded, F4-F8), all new and in envelope, 0 reverts; fixes in the runner (tool code),
the root's docstring, the report and one test. Remediated in `bf4b837`, `d22f1aa`.

**Next (cell 2):**
1. Reviewer A **round 2** on the remediated head (`d22f1aa` or later): copy
   `C:\Users\rwsmy\clearwater-review-evidence\wp4.1\r1\run_review.sh` and `review-prompt.md` to
   `...\wp4.1\r2\`; set the HEAD sha and "round 2"; scope the diff either to the whole package
   (`git diff -U8 3aa3c51..HEAD -- . ':(exclude)docs/proofs/**'`) or to `c6aabc0..HEAD` with the
   round-1 findings named as remediated (prior rounds WITHHELD: name them in the prompt as
   history, not as files); refresh `test-summary.txt`; probe first (one `succeeded in` line,
   banner `gpt-6.1-sol` / high); run with a background start and a foreground `until [ -f
   .../review.done ]` poll; adjudicate; yield (Y4) before remediating; five-round gate at
   round 5.
2. Ask for the **two-leg suite window** (CLAUDE.md commands, fresh `--basetemp` per leg under
   `work/wp4.1-<run>-*`, 5 GiB check, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`).
3. Fill the report's figures and counts (`docs/reports/wp4.1-photo-path.md`: both legs' counts
   and skip lines, the V8 (c) table, the V9 raw figures, the Reviewer A rounds) and mark it FINAL.
4. The **return report** (recipe section 4, under about 60-70 lines) to the orchestrator by
   SendMessage as the final message.

**Notes for cell 2:** the runner's footage check reads `clearwater.local.toml` via
`tools/local_config.py`; tests use `no_footage` / `footage_folder=None`. V9 follows CHARC S8
(`6c108416f38ca32a`); CHARC adds the AD-11 clarification to `docs/decisions.md` (not ours). The
V9 planted control is `gamma` (probe above). WP-T5 runs beside us and owns
`tests/test_jobs_export_video.py` and `tests/test_io_video_encode.py`; its serial-leg windows are
exclusive (no runs while open).
