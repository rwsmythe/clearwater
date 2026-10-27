# WP3.14 ledger -- export jobs and batch

Cell 1 (`implementer-opus-high`), worktree `.worktrees/wp3.14`, branch `wp3.14`, base main `9753b7b`.
Brief `docs/briefs/wp3.14-brief.md` (FINAL, CHARC `3c3c35d7e40b525e`).

| Gate | Dispatcher-read depth (`scripts/cell_depth.py`) |
|---|---|
| Dispatch | 0 (fresh seat) |

## Round 0 -- the design table (ladder item 1)

### Module split and public API

| Module | Public names | Imports (beyond stdlib, NumPy, `clearwater.interfaces`) |
|---|---|---|
| `jobs/export.py` (NEW) | `ExportEngine` (implements `ExportJobs`); `effective_parameters(method, parameter_set)` | `clearwater.jobs` (naming, safe writing, disk space, `export_seam`), `clearwater.analysis` (`AnalysisEngine`, `CANCELLED as ANALYSIS_CANCELLED`, `block_mean`, `proxy_factor`), `clearwater.io.video` (`is_sidecar`, `sidecar_fault`, `resolve_encoder`, `VideoEncodeError`) |
| `jobs/provenance.py` (NEW) | `video_provenance(...)`, `photo_provenance(...)` (Q10 key set as a JSON-native mapping) | `clearwater.interfaces` only |
| `jobs/batch.py` (NEW) | `run_batch(exports, requests, progress) -> BatchReport`; `BatchItem(request, result)`; `BatchReport(items, counts, lines())` | `clearwater.jobs.export_seam` only (runs ANY `ExportJobs`) |
| `jobs/disk_space.py` (EDIT, DR-48) | `estimate_video_bytes(source_size, settings, *, width, height, frame_rate, duration_s)` (Q7), `QUALITY_RATIO` 1.10 / 0.50 / 0.25 (Q6) | `clearwater.io.video.encode` read as a MODULE (`_encode.NVENC_BITS_PER_PIXEL` at call time, so a patch of the constant reaches the estimate: one source) |
| `jobs/__init__.py` (APPEND) | the names above; docstring line made true | -- |
| `tools/export_bench.py` (NEW) | `run`, `v16`, `--dry-run` (Q11) | `tools/video_io_bench.py` (`StrayWatch`, `Telemetry`, `conditions`, `tree_rss`, `gpu_reading`, `rate`; all present), `clearwater.methods`, `clearwater.core`, `clearwater.io.*`, `clearwater.cache` |

Verified at round 0: a fresh `-I` interpreter importing `clearwater.io.video` and `clearwater.analysis` loads no
`clearwater.gui/.methods/.core/.io.photo`, PySide6, CuPy, PIL, pillow_heif or SciPy. `jobs` never imports
`clearwater.core` or `clearwater.io.photo` (both injected), so WP3.13's import test holds unchanged.

### Constructor (Q4, everything injected; no defaults that import `core`, `methods` or `io.photo`)

```python
ExportEngine(
    *,
    methods: Mapping[str, CorrectionMethod],              # IF-3, keyed by id (WP4.3: available_methods())
    video_source: VideoSource,                            # IF-5 (FFmpegVideoSource)
    sink_factory: Callable[[], VideoSink],                # a fresh IF-5 sink per job (FFmpegVideoSink)
    photo_reader: PhotoSource,                            # IF-6 (PhotoReader)
    photo_writer: PhotoSink,                              # IF-6 (PhotoWriter)
    cache: ProxyCache,                                    # IF-7 (DiskProxyCache)
    cache_key: Callable[[Path], CacheKey],                # (cache_key from clearwater.cache)
    select_backend: Callable[[Settings, int, int, str], tuple[ArrayBackend, str]],  # IF-2 (core)
    app_version: str = clearwater.__version__,
    on_stage: Callable[[str], None] | None = None,        # Q11's "injected clock": OPEN ITEM O3
)
```

`job(request)` raises `ValueError` only for a request malformed in itself (`kind` not `"photo"`/`"video"`, `source`
not a `Path`, `parameters` not a `ParameterSet`, `settings` not a `Settings`); it builds a closure and touches no file.

### Phases, threads, progress (Q1, Q15)

| Kind | Phases on the JOB thread (in order; cancel checked before each) | Progress `(done, total, message)` |
|---|---|---|
| both, start | settings: `output_folder` set and not a directory -> failure; `validate_suffix` -> failure; method id in `methods` -> else failure; `is_sidecar(source)` -> failure (D83, `sidecar_fault` text) | `(0, None, "Preparing <name>")` |
| photo | read (`photo_reader.read`; a video or a missing file fails here, by content) -> `select_backend(settings, h, w, method_id)` -> measure (`block_mean(pixels, proxy_factor(h, w)).astype(float32)` on the backend, each stage given the earlier results = `gui.imaging.measure_statistics` bit for bit) -> render -> `to_host` -> D87 (`estimate_photo_bytes(w, h, png_bit_depth)`) -> `plan_output(PHOTO, r)` -> `with SafeWrite(plan, r)`: `photo_writer.write(temp, bit_depth, provenance)` -> cancel check -> `commit()` | steps `0..4 of 4`: Reading, Measuring, Rendering, Writing, Saved |
| video | probe (`video_source.probe`; a photo or a missing file fails here: `VideoProbeError`) -> a `"refuse"` fault fails by its message -> `select_backend(settings, H, W, method_id)` -> `AnalysisEngine(method, backend, cache, cache_key(source), video_source, probe, effective params, hw_decode=backend is GPU)` and its `analysis_job()` run INLINE to completion (AD-7, AD-15) -> `is_complete()` else failure -> `sink = sink_factory()`; `encoder = resolve_encoder(settings.video_encoder, sink.capabilities())` -> bit depth 10 if source 10-bit or `ten_bit_for_eight_bit` else 8 -> `plan_output(VIDEO, r)` -> D87 on `plan.folder` -> `with SafeWrite(plan, r) as w`: `sink.open(probe, w.temp_path, encoder, quality, bit_depth, provenance)` -> watchdog start -> for each decoded frame (pts order): cancel check, upload with the backend, `render(frame, params, engine.smoothed_record(pts_ticks, schema_hash=engine.schema_hash))`, `to_host`, `sink.write(Frame on cpu)`, report -> watchdog stop (join) -> cancel check -> `sink.close()` -> cancel check -> `commit()` | analysis: the engine's own `(done, total)` passed through, message `"Analysing <name>: <engine message>"`; export: `(frames written, probe.video.nb_frames or None, "Exporting <name>")` |

Threads: the job thread (the caller's worker: `JobRunner.run` in the GUI, the caller in `run_batch`) does every step
above; one frame in flight; no frame-level parallelism (WP3.21's). Beside it: WP3.9's decoder FFmpeg and its stderr
daemon (two streams: the analysis pass when the cache is not complete, then the export pass); WP3.10's encoder FFmpeg
and its stderr daemon; and ONE watchdog thread per encode, alive from after `sink.open` returns to before `sink.close`.
The watchdog touches only `progress.cancelled()` and `sink.abort()`; it never touches a `FrameStream` (DR-45 (a)).
Every `FrameStream` is closed on the job thread in a `finally` (the analysis engine does its own the same way).
One `AnalysisEngine` per job, its job callable run once on the job thread (one writer, DR-47 not reached).

### Cancel path (Q2, Q3; G8, D44, D45; DR-57 (b))

1. Before every phase and every frame: `progress.cancelled()` -> stop (`_Cancelled`).
2. Analysis: the engine checks the same `progress`; its `JobResult.failure == analysis.CANCELLED` -> this job's
   `CANCELLED` (the `export_seam` constant itself, never the analysis one).
3. Encode: the watchdog polls every 0.2 s (`POLL_S`); on `cancelled()` it records `fired` and calls `sink.abort()`
   ONCE, which kills FFmpeg and releases a write blocked on stdin; the job thread then sees `VideoEncodeError`
   (`encoder_failed`/`state`) and, `fired` being set, classifies it as the cancel.
4. On ANY stop or failure after `sink.open`: the job calls `sink.abort()` (idempotent) and NEVER `sink.close()`;
   leaving the `with SafeWrite` block aborts the temporary (tolerates the one `abort` already deleted).
5. End of the frames: watchdog stopped and joined -> cancel check (abort if set) -> `close()` -> cancel check (the
   temporary is complete but uncommitted: abort deletes it) -> `commit()`. After `commit()` the result is ok whatever
   `cancelled()` says (WP3.19 state table).
6. "Committed before the stop" (Q3): one job = at most one output, committed only by `commit()`'s rename; the
   committed path is recorded the moment `commit()` returns, and every later exception returns it in `outputs`
   (a planted stop after `commit` -- `on_stage("committed")` raising -- lists the file). Nothing is written after
   `commit()` and no earlier output is touched (DR-20 (7)).

### D87 and DR-48 (Q6-Q8)

- Per item, inside the job, before `SafeWrite.begin`, on `plan.folder`: `check_free_space(folder, needed)`; not ok ->
  failure `SpaceCheck.message()` (both figures), nothing written, the batch continues (D81). Never batch-wide.
- Video: `needed = ceil(max(QUALITY_RATIO[level] x source_size, ceiling_bits_per_s x duration_s / 8) x MARGIN)`,
  `ceiling_bits_per_s = NVENC_BITS_PER_PIXEL / NVENC_RATE_SHARE[level] x width x height x frame_rate` (exact
  `Fraction` arithmetic until the final `ceil`); `source_size` = the source file's size, `width`/`height` =
  `probe.video` coded size, `frame_rate` = `probe.video.frame_rate`, `duration_s` = `probe.duration_s`. Same for both
  encoders; no 10-bit doubling. `QUALITY_RATIO` High 1.10 / Standard 0.50 / Draft 0.25, `MARGIN` 1.25.
  Example (4K 29.97, 60 s): ceiling Standard 29.8 Mb/s -> 223.7 MB x 1.25 = 279.7 MB; a busy 120 Mb/s source
  (900 MB) gives the ratio term 450 MB x 1.25 = 562.5 MB (ratio wins); a calm 6.58 Mb/s source (49 MB) gives the
  ceiling (279.7 MB). Real figures for GX011627/GX011625 go in the report.
- Docstrings: the module's "PROVISIONAL until WP3.10" goes; WP3.10 report 7.2 and DR-48 cited; the
  `check_free_space` sentence "A batch sums its estimates per volume and checks once." REPLACED by the per-item rule.

### Provenance (Q10; D91, AD-13 amended, IF-9)

`ParameterSet(method, parameters=<effective values>, created=<export moment, UTC>, app_version, source=..., settings=...)
.to_dict()` when `settings.provenance`, else None. `source`: `name` (file NAME only), `size`, `mtime` (ISO-8601 UTC
from `st_mtime_ns`); video adds `container`, `codec`, `width`, `height`, `bit_depth`, `frame_rate` (string
`"30000/1001"`), `duration_s` (string fraction), `nb_frames`, `color` (primaries, transfer, matrix, range). No tag
dictionary, no `GoProInfo`, no location value, nothing from `gpmd`. `settings`: video `encoder` (RESOLVED, never
`"auto"`), `quality`, `bit_depth`, `device` (the backend reason); photo `png_bit_depth`, `device`. Size: a test builds
the largest parameter set (every parameter of every method, longest names, a 255-character file name) and asserts the
JSON under half of `PROVENANCE_MAX_BYTES`.

### Failure table (every row: `ok` False, `outputs` (), the source and every earlier output untouched)

| Failure | `JobResult.failure` (ASCII-escaped; always starts with the file name, so never equals `CANCELLED`) | Left on disk |
|---|---|---|
| malformed request | -- (`ValueError` from `job()`, nothing built) | nothing |
| unknown method id | `<name>: unknown correction method '<id>'` | nothing |
| missing output folder | `<name>: the output folder does not exist: <folder>` | nothing |
| invalid suffix | `<name>: <validate_suffix message>` | nothing |
| reserved device name (DR-35 (a)) | OPEN ITEM O1 (premise does not hold on this OS build) | -- |
| sidecar (D83) | `sidecar_fault(source).message` (prefixed) | nothing |
| missing/unreadable source, wrong kind | the probe's or reader's message (`VideoProbeError`, `PhotoReadError`) | nothing |
| refused probe (HLG, PQ) | the fault's message | nothing |
| D87 short of space | `SpaceCheck.message()` (needed and free) | nothing (refused before `begin`) |
| cache error / analysis failure | `<name>: analysis failed: <analysis failure text>` | nothing (no temporary yet) |
| encoder refused / unavailable (D74) | the `VideoEncodeError` message | nothing (`SafeWrite` aborts the empty temporary) |
| decode error mid-encode | the `VideoDecodeError` message | nothing (`sink.abort` + `SafeWrite` abort) |
| encode error / verify failed | the `VideoEncodeError` message (FFmpeg's tail) | nothing (the sink deleted it; `SafeWrite` tolerates) |
| method (render) error | `<name>: <ExcType>: <message>` | nothing |
| disk full | `<name>: disk full while writing <final name>: <original error>` when `is_disk_full` holds on the error or its cause chain (OPEN ITEM O2) | nothing |
| temporary not deletable | the original failure, plus WARNING `the temporary <name> could not be removed; it is removed at the next start` (DR-57 (c)) | that temporary only (D85 next-start clean-up) |
| cancel | `CANCELLED` (identity) | nothing |

A cleanup error is a log line or a warning, never the failure. `device` is the `select_backend` reason, or `"none"`
for a stop before the backend is chosen (the seam stub's value). The INFO log line per job names the file, the outcome,
the device and the reason; AD-9: an ok result carries the fallback reason as a warning when the reason is a CPU reason
other than `"CPU: forced"` (the user's own choice).

### Warnings on an ok video result

`SinkReport.warnings` (D54 assumed tags, D86 truncated / unreadable tail, the level warning) + one
`"Not carried to the output: <item>"` per `not_carried` item + the probe's `gp_log` warn fault (AD-16; the only warn
fault the sink does not restate) + the AD-9 fallback reason.

### Headless batch (Q9)

`run_batch(exports: ExportJobs, requests: Sequence[ExportRequest], progress: Progress) -> BatchReport`: items in
order, `exports.job(request)(item_progress)` each; a non-ok non-cancel result (or an exception from `job()`/the job)
is logged at WARNING and the next item runs (D81); a `CANCELLED` result, or `progress.cancelled()` between items,
marks every remaining item NOT RUN (`result` None, D45); completed outputs are never touched (G8). `BatchReport`:
per-item `BatchItem(request, result | None)` in order, counts (done, done with warnings, failed, cancelled, not run),
`lines()` the end-of-run report text (ASCII-safe), logged at INFO. The item progress prefixes `"[i/n] "`.

### Test list (ladder item 9; files `tests/test_jobs_export.py`, `tests/test_jobs_export_video.py`, `tests/test_jobs_batch.py`, `tests/test_jobs_disk_space.py` edits, `tests/test_export_bench.py`)

- Seam: `job()` on a missing source returns a callable, touches no file (a filesystem spy); `ValueError` on a
  malformed request; each `JobResult` branch; `failure is CANCELLED`; ok names an existing output; control: a planted
  engine returning `"".join(["cancel", "led"])` fails by name.
- Photo: one sample per family (`jpeg-*`, `heic8-*`, `heic10-*`, `png8-*`, `png16-*`, `tiff8-*`,
  `jpeg-orient-port-o6`) to PNG 8 and 16; statistics equal `measure_statistics` (`gui`); provenance parseable when
  on, absent when off.
- Video V4 (`video_fidelity` compare, every MANDATORY and REQUIRED SAME): `vid-hevc8-bt709-full`, `vid-hevc10`,
  `vid-untagged`, `vid-vfr`, `vid-rotated`, `vid-truncated` (warns D86); libx265 always, NVENC under `gpu`;
  `vid-hlg`, `vid-pq`, `gopro-*-lrv`, `gopro-*-thm` readable failures, nothing written; synthetic 5.3K 8:7 (`slow`).
- DR-28 (1): recording sink wrapper digests every frame before encode against an independent render of the same pts
  (full coverage); controls: statistics pts +1 and -1, a dropped frame, a duplicated frame each fail by name; sampled
  decode after encode, each frame nearer its own corrected frame than its neighbours; control: a planted swap fails.
- Cancel: before start, during analysis, mid-encode with a write blocked until `abort` (bound 10 s), immediately
  before `commit`: `CANCELLED`, no temporary, no final, earlier outputs kept, `abort` called, `close` never; cancel
  after `commit` ok. Controls (planted, fail by name): `close` on cancel; cancel polled only between frames (the
  blocked-write leg exceeds the bound); a batch-wide D87; the 10-bit doubling kept.
- V11: encoder killed mid-stream; ENOSPC `OSError` from a sink double and from a writer double; a subprocess export
  killed mid-encode leaves only a temporary-shaped file that `remove_leftovers` removes; source and earlier outputs
  untouched.
- D87 and DR-48: needed above free (patched `shutil.disk_usage`) refuses before any write with both figures; batch of
  three with the second not fitting; ratio term wins high-rate, ceiling term low-rate; both encoders equal; bits / 8;
  a patched `NVENC_BITS_PER_PIXEL` changes the estimate.
- Settings: missing folder, invalid suffix, DR-35 (a) (per O1); one `Reservations` reaches both calls (spy);
  `force_cpu` -> `"CPU: forced"`; patched free memory -> CPU with reason; the log line names both; `"auto"` without
  NVENC -> `libx265`, recorded in provenance.
- Batch: D81 (second of three fails); D45 (cancel in the second: third not run, first kept).
- N8: source byte-identical, mtime unchanged after success, failure and cancel.
- `footage` (`gpu`, `slow`, window): GX011627 through the engine, c3 defaults, NVENC 8-bit Standard: all MANDATORY and
  REQUIRED SAME.
- Static: WP3.13's import test unchanged and green; no `jobs` module imports `clearwater.methods`/`clearwater.gui`;
  no `jobs` module names a GPS or IMU key or opens a `gpmd` packet.

### Answers to the questions

Q1-Q16 as ADOPTED by CHARC `3c3c35d7`; applied as above. Q11's "optional injected clock" is read as O3.

### OPEN ITEMS for the dispatcher (round-0 STOP list)

- **O1 (STOP: a premise does not match, reproduced).** DR-35 (a) says `NU.MP4` + suffix `L` -> `NUL.MP4` "export
  fails, nothing is overwritten"; the brief asks for "a readable job failure (a test)". On this laptop (Windows
  10.0.26300.9711) it does NOT fail: `plan_output` -> `NUL.MP4`, `SafeWrite` creates
  `NUL.clearwater-partial-<token>.MP4`, writes, and `commit()` returns `...\NUL.MP4`; `os.listdir` then shows a real
  file `NUL.MP4` (reproduction: a 15-line script against `clearwater.jobs` in `work/`, removed after). Nothing is
  overwritten, but there is no failure to test. Recommended: (A) the engine refuses, at job start, a planned final
  name whose part before the first dot is a Windows reserved device name (`CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`,
  `LPT1`-`LPT9`, case-insensitive, trailing spaces ignored), on every OS -- a portable name rule (N1: no OS branch),
  in `export.py` (owned), a readable failure, nothing written; such a file breaks on older Windows and on copy.
  Alternative (B): no rule; DR-35 (a) closes as "not reproducible on Windows 11 26300; the export succeeds as
  `NUL.MP4`, nothing overwritten" with a test that nothing is overwritten.
- **O2 (a choice the brief leaves open).** "Disk full is classified with `is_disk_full` and named." A photo writer's
  `ENOSPC` is an `OSError` (`is_disk_full` holds). FFmpeg's own disk full reaches the job as `VideoEncodeError`
  (`encoder_failed`) whose message carries FFmpeg's stderr tail ("No space left on device"); no `OSError` with
  `ENOSPC` is raised in Python. Recommended: name disk full when `is_disk_full` holds on the error or anything in its
  `__cause__`/`__context__` chain (covers the writer and sink doubles of V11); a real FFmpeg disk full stays the
  sink's `encoder_failed` text unchanged (it already names the cause); no text matching on FFmpeg output.
- **O3 (reading of Q11).** "an optional injected clock (None in the product)": built as `on_stage: Callable[[str],
  None] | None` called at each phase boundary (`probe`, `analysis`, `open`, `frames`, `close`, `committed`) and
  never otherwise; the bench timestamps the calls with its own clock; per-frame times come from the Progress
  callbacks. Alternative: a `clock: Callable[[], float]` the engine reads into a stage dict the bench reads back.
- **O4 (small, stated choices; confirm or correct).** (a) An unknown method id is a job failure, not a `ValueError`
  (the request is well formed; the engine lacks the method). (b) Provenance records the EFFECTIVE parameter values
  (defaults overlaid, as rendered) and `created` = the export moment. (c) `device` `"none"` for a stop before the
  backend is chosen. (d) The AD-9 warning appears for every CPU reason except `"CPU: forced"`.
- Order note (no question): the brief's video order (analysis BEFORE `resolve_encoder` and D87) is followed, so an
  unavailable explicit encoder or a full disk is reported after the analysis pass.

### Round-0 rulings (orchestrator gen 13; depth at this yield 164,553, 51 turns)

| Gate | Dispatcher-read depth |
|---|---|
| Round-0 yield | 164,553 (51 turns) |

- O1 ADOPT (A): `export.py` refuses a planned FINAL name whose part before the first dot (case-insensitive, trailing
  spaces and dots stripped) is `CON`, `PRN`, `AUX`, `NUL`, `COM1`-`COM9`, `LPT1`-`LPT9`; portable rule on every OS, on
  the plan before `SafeWrite.begin`, readable failure starting with the file name, nothing written. Tests: `NU.MP4` +
  `L` refused, nothing on disk; `NULL.MP4`, `CONSOLE.png` accepted. Reproduction of record: Windows 10.0.26300
  creates `NUL.MP4` as an ordinary file, so DR-35 (a)'s "export fails" premise does not hold on this build; the rule
  is a portability guard.
- O2 ADOPT: `is_disk_full` over the error and its cause/context chain; FFmpeg's own disk-full message kept verbatim
  (no text matching); the report states a real encoder disk full is named by FFmpeg's text.
- O3 ADOPT: `on_stage: Callable[[str], None] | None = None`, called at phase boundaries; the engine reads no clock.
- O4 (a)-(d) CONFIRMED.
- ORDER RULING (video): probe -> refuse faults -> `select_backend` -> `resolve_encoder` (D74 refusal) ->
  `plan_output` + reserved-name rule -> D87 check -> analysis -> D87 RE-CHECK immediately before `SafeWrite.begin`
  -> open/encode. Nothing is written before `begin` in either position. Photo: read -> backend -> measure ->
  render -> plan + reserved-name rule -> D87 -> write.

## RESUME HERE (cell 2, end of build turn 1)

Cell 2 (`implementer-opus-high`, fresh seat after cell 1's planned re-seat at `db4498c`; dispatch depth 0).

| Gate | Dispatcher-read depth |
|---|---|
| Cell 2 dispatch | 0 (fresh seat) |
| Cell 2 build yield (window request) | 207,998 (78 turns) |

Window plan CONFIRMED (orchestrator gen 13): footage window `tests/test_jobs_export_video.py -m footage` (GX011627 V4
leg) first, then full window `uv run pytest -m "not footage"` (offscreen, basetemp under `work/`, the 5.3K leg
inside it), then Reviewer A round 1. Each grant arrives as its own message; nothing heavy before it. A
multi-finding remediation after round 1 goes to a fresh seat.

**Done (committed on `wp3.14`), RESUME "Next" items 1-3 of cell 1:**
- `20f0ac3` `tests/test_jobs_export_photo.py`: one WP2.3 sample per still family (`jpeg-gradient-srgb`,
  `heic8-gradient-srgb`, `heic10-gradient-display-p3`, `png8-gradient-srgb`, `png16-gradient-srgb`,
  `tiff8-gradient-srgb`, `jpeg-orient-port-o6`) to PNG 8 and 16 through the product engine (CPU forced): IHDR
  bit depth, decoded size, provenance (`iTXt`) parseable with the file NAME only, absent when off, N8. Statistics
  equal `gui.imaging.measure_statistics` bit for bit (`gui`) on two samples (factor 1) and a 1131 x 1700 synthetic
  PNG (factor 2, partial last block row) with a full-image control that the comparison tells apart. Support:
  `product_engine(...)` in `tests/test_jobs_export_support.py`. O1 near-miss names `NUL2.MP4`, `CONSOLE.MP4`,
  `.NUL` added (accepted).
- `e7d9092` `tests/test_jobs_export_video.py`: V4 through the engine and `video_fidelity.fidelity_record` on
  `vid-hevc8-bt709-full`, `vid-hevc10`, `vid-untagged`, `vid-vfr`, `vid-rotated`, `vid-truncated` (D86 "cut
  short" warning), libx265 and NVENC (`gpu`), all MANDATORY and REQUIRED SAME, frame count, N8; `vid-hlg`,
  `vid-pq` and the four GoPro `.LRV`/`.THM` samples readable failures, nothing written, no cache; DR-28 (1): a
  digest of every frame handed to the sink against an independent decode + analysis (own cache) + render of a
  4 s synthetic clip with a turning cast (120 frames; the 2 s window varies per frame), plus a sampled decode of
  the output (each sampled frame nearest its own corrected frame); controls fail BY NAME: statistics pts +1 and -1
  ("differ from their own render"), dropped frame ("no frame was written"), duplicated ("written twice"), a
  pixel swap of frames 40/41 ("output frame 40 is nearer corrected frame 41"). V11 with the product sink: encoder
  killed after frame 5 (readable failure, nothing left, earlier output and source untouched); a cancel mid-encode
  (`CANCELLED`, nothing left); a subprocess export killed after 10 frames leaves only temporary-shaped files that
  `remove_leftovers` removes (`slow`). Written, NOT yet run (window): the 5.3K 8:7 synthetic leg (`slow`) and the
  GX011627 leg (`footage`, `gpu`, `slow`; NVENC 8-bit Standard, c3 defaults).
- `3a723cc` `tools/export_bench.py` + `tests/test_export_bench.py` (Q11/Q12): `run` / `v16 [--clip STEM]
  [--dry-run]`, `V16_PLAN` = GX011627 x3 cold, x1 warm, x1 ancuti2018, x1 libx265; synthetic 5.3K 8:7 x1;
  GX011625 x1 LAST. Phases from `on_stage` stamps, per-frame intervals from the `Exporting` progress reports;
  D106 verdict (0.834 s/frame = 25 min/min at 30000/1001); conditions, whole-run strays, Telemetry peaks, NVENC
  proof from WP3.10's helpers; `cache_complete_at_start` recorded (a warm run skips the decode pass only: the
  later stages are analysed again from the cached proxies, the product's V17 behaviour). Records under
  `work/wp3.14/bench/`; run folders (output + cache) deleted unless `--keep`.
- Gates at `3a723cc`: ruff check clean, ruff format --check clean, mypy clean (136 files); targeted pytest:
  `test_jobs_export_photo.py` 18 passed; `test_jobs_export.py` + `test_jobs_batch.py` + photo 77 passed;
  `test_jobs_export_video.py -m "not slow and not footage"` 26 passed (NVENC legs ran); the killed-process leg
  1 passed (64 s); `test_export_bench.py` 13 passed. Every committed blob in `9753b7b..HEAD` LF.

**Next:** WINDOW REQUEST full (+ the 5.3K synthetic leg inside it) and a footage window for the GX011627 V4 leg;
then Reviewer A round 1 (runner from `wp3.10/r10`, `-m gpt-6.1-sol`).
