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

## Cumulative round ledger (Reviewer A)

| Round | Head | Transport, CLI, banner | CRIT | MAJOR | MINOR | In / out of envelope | NEW / REOPENED | Reverts | Fixes change | Verdict | Depth (dispatcher-read) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| R1 | `7bb5d85` | WSL, codex-cli 0.162.1, `gpt-6.1-sol` / high | 0 | 2 | 6 | 8 / 0 | 8 / 0 | 0 | product (F1 (a), F2, F3, F4: `095a345`), tool (F8: `02324a7`), test-only (F5, F6, F7: `095a345`); F1 (b) held for CHARC | NEW_CRITICAL_MAJOR_FOUND (counts: every assertion met) | 123,184 (59 turns) |
| R2 | `c3a2fc9` | WSL, codex-cli 0.162.1, `gpt-6.1-sol` / high | 0 | 1 | 7 | 8 / 0 | 8 / 0 | 0 | cleanup only: tool (G4: `756da22`), test-only (G3, G5-G8: `756da22`, `04822ef`); G1, G2 ruled NOT A DEFECT | NEW_CRITICAL_MAJOR_FOUND (counts: every assertion met); adjudicated ZERO new blocking -> loop TERMINATED | 255,161 (143 turns) |

R1 findings and adjudication (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.14\r1\`, md5s there):

| # | Sev | Finding | Adjudication |
|---|---|---|---|
| F1 | MAJOR | No cancel coverage while `sink.close()` flushes and verifies (watchdog stopped before close); no check between `_stage("close")` and `close()` | CONFIRMED; CONFORMS TO RULED Q2 ("The watchdog stops before `close`"); the end state stays right (post-close check, SafeWrite deletes the temporary, CANCELLED) but the cancel waits for close. STOP: needs a ruling. Recommended: keep the watchdog alive through `close` (+ a check right before it). |
| F2 | MAJOR | `frames.close()` unguarded in `finally` replaces the original error | CONFIRMED (code; ladder 5). The shipped decoder's close suppresses its OSErrors, so the product wiring rarely reaches it; accepted MAJOR. Product fix. |
| F3 | MINOR | Leftover temporary after a successful `commit()` (and after a failed `begin`) not reported | CONFIRMED. Product fix. |
| F4 | MINOR | SinkReport warnings dropped on a stop after `close` | CONFIRMED. Product fix. |
| F5 | MINOR | `_no_partials` matches `"_out"`, not the `*_corrected.*` finals | CONFIRMED. Test fix. |
| F6 | MINOR | Telemetry-name guard regex carries literal 0x08 bytes (vacuous) | CONFIRMED (`od -c`); property holds today. Test fix. |
| F7 | MINOR | Fresh `Reservations` per job not tested across jobs | CONFIRMED. Test fix. |
| F8 | MINOR | `export_bench` stops telemetry after the stray window and sampler stop | CONFIRMED. Tool fix. |

R1 rulings (orchestrator gen 14, FINAL): F2-F8 adjudication ACCEPTED as classified, each fixed failing test first. F1 (a)
(a cancel check immediately before `sink.close()`) is inside Q2's "between phases": done now. F1 (b) (the watchdog alive
THROUGH `close()`) needs a CHARC amendment of Q2; the orchestrator recommended yes on condition of one deterministic test
per abort timing (a sink double that blocks in `close`), one product-sink cancel during a real `close`, and the post-close
cancel check kept as mandatory. Not built until the ruling is relayed. Round 2 waits for (b) and reviews the whole
remediation.

R1 remediation (cell 3), failing tests first: on the unfixed product 6 of the new tests failed by their reason (F4
`() == ('sink warning', ...)`, F1 (a) `'close' not in calls`, F3 x2 no leftover warning, F2 `OSError: cleanup close failed`
in place of the render error, F8 `['strays', 'telemetry']`); F5, F6, F7 are test-only, each with a control that the
broken form fails (F5 a leaked `clip_corrected*.mp4` / temporary raises; F6 the 0x08 pattern finds nothing in a planted
text the real one catches; F7 a planted shared registry fails "a registry was reused across jobs").
- `095a345` `export.py`: `_check_cancel` before `sink.close()`; the sink's warnings copied right after `close` (inside
  the abort guard); `run.write` assigned before `with` (a failed `begin` reaches the result); the leftover warning on any
  outcome; `_close_stream(frames, quietly=...)` (quiet = a WARNING log line while another error propagates; on the clean
  path its error is the job's own). `tests/test_jobs_export.py`: the eight tests and controls above.
- `02324a7` `tools/export_bench.py`: telemetry stopped first, then the stray window and the sampler;
  `tests/test_export_bench.py`: the order test.
- Gates at `02324a7`: ruff check, ruff format --check, mypy (136 files) clean; targeted: `test_jobs_export.py`,
  `test_jobs_batch.py`, `test_jobs_disk_space.py`, `test_export_bench.py`, `test_jobs_export_photo.py` 116 passed;
  `test_jobs_export_video.py -m "not slow and not footage"` 26 passed (NVENC legs ran); the killed-subprocess V11 leg
  1 passed (63 s); WP3.13's import test 1 passed. >= 10 GB free before each run.

R1 rulings, F1 (b) (CHARC `e7d25105`, relayed FINAL): Q2 AMENDED -- check before `close()`; the watchdog alive THROUGH
`close()`, stopped and JOINED after it and before the unconditional post-close check and `commit`; the cancel read from
`cancelled()`, the original error to the log line; conditions: one deterministic test per abort timing on a double
whose `close` blocks, one libx265 product-sink test cancelling during a real `close`, `io/video/encode.py` NOT edited
(CHARC banks a MINOR row: `close` should set `"closed"` only from `"open"`), poll and single `abort` unchanged, the V16
stamps `close` and `committed` kept; F2 keeps the ORIGINAL error.
- `c3a2fc9` `export.py`: `_encode` owns the watchdog from after `open` through `close`; the frame loop moved to
  `_write_frames`; inner `finally` stops and joins; `except Exception` -> `CANCELLED` when `fired` or `cancelled()`, the
  error logged at INFO; post-close `_check_cancel`. Tests: `FakeSink` close gates (`CLOSE_GATES`: before_flush, flush,
  finished, closed), the four timing tests, the joined-before-commit test, the product-sink test
  (`_CancelInCloseSink`, libx265). On `716feaa`'s engine the four timing tests and the product test failed "the watchdog
  never aborted during close". The double's `abort` and stopped-encoder cleanup made non-raising after a 1-in-23 flake
  (a concurrent unlink on Windows raised PermissionError in the double); then 30 consecutive clean runs.
- Gates at `c3a2fc9`: ruff, format, mypy clean; targeted 121 passed (jobs, batch, disk space, bench, photo);
  `test_jobs_export_video.py -m "not footage"` 29 passed (17.5 min on the busy host; this run included the slow 5.3K
  synthetic leg through a mistyped `--deselect` -- a deviation from "short targeted runs", 9 frames, >= 8.8 GB free);
  the product-sink close test 3 of 3.
- Skips question (dispatcher): the 10 full-run skips are environmental (9) and by design (1). `test_methods_assembly_v8.py`
  x9: "look-check frame absent: C:\Users\rwsmy\clearwater\.worktrees\wp3.14\work\wp1.3\frames\GX011625_0024.925.png"
  (5) and "...GX011625_0114.648.png" (4) -- the worktree's working folder has no `wp1.3/frames` (the main tree's
  `work/` has them). `test_color_roundtrip.py` x1: "swscale reads a yuvj format as full whatever in_range says
  (refused instead)" -- the code skips that case by design.

R2 findings and adjudication (evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.14\r2\`, md5s there; reproduction
`f1-repro.py` / `.txt`):

| # | Sev | Finding | Adjudication |
|---|---|---|---|
| G1 | MAJOR | (a) a non-Exception `BaseException` (KeyboardInterrupt, SystemExit) from frames/close bypasses the post-close check; (b) `fired or cancelled()` short-circuits the flag read | (a) CONFIRMED, reproduced: the interrupt propagates, `abort` called, only the sources remain. RECOMMEND NOT A DEFECT (no non-Exception BaseException becomes a result anywhere in the engine; converting would swallow an interrupt). (b) NOT A DEFECT (`fired` is set only after `cancelled()` read True; sticky flag; same outcome). RULING ASKED. |
| G2 | MINOR | `_close_stream(quietly=True)` suppresses only `Exception` | CONFIRMED; same principle as G1 (a); RECOMMEND NOT A DEFECT, rides on that ruling. |
| G3 | MINOR | `FakeSink.abort` signals `aborted_in_close` before its effects | CONFIRMED. Test fix (signal last). |
| G4 | MINOR | the stray window now includes the telemetry join | CONFIRMED. Tool fix (strays at `ended`, then telemetry, then the sampler). |
| G5 | MINOR | the order test has no sampler | CONFIRMED. Test fix. |
| G6 | MINOR | the product-sink test covers one timing | CONFIRMED as scope (condition 2 = one); two more product timings reachable from the subclass. Test addition. |
| G7 | MINOR | the commit-leftover test assumes `os.link` works | CONFIRMED. Test fix. |
| G8 | MINOR | no control for a close error without a cancel, nor a clean-path stream-close error | CONFIRMED. Tests to add. |

R2 rulings (orchestrator gen 14, FINAL): G1 (a) and G2 NOT DEFECTS -- "whether `close` raised" in the amended Q2 means an
`Exception`; a `KeyboardInterrupt` or `SystemExit` is meant to propagate and the engine never turns a `BaseException`
into a result; the reproduction (`r2\f1-repro.txt`: the interrupt propagates, tail [close, abort], only the sources
remain) shows the cleanup holds; one line in the report's limits; CHARC told (a reopen would come from CHARC). G1 (b)
NOT A DEFECT (`fired` is set only after `cancelled()` read True). R2 has ZERO new blocking: the loop TERMINATES, no R3.
G3-G8 fixed once as the terminating round's cleanup.

R2 cleanup (cell 3), controls first where one applies:
- `756da22` (G4, G5) `tools/export_bench.py`: the stray window read at the export's end, then the telemetry stop, then
  the GPU sampler; the sampler built by `_gpu_sampler(leg)`; `tests/test_export_bench.py`: the order test with a sampler
  double (failed on the previous order: strays after telemetry) and `test_the_gpu_sampler_runs_for_nvenc_legs_only`.
- `04822ef` (G3, G6-G8) tests only: `FakeSink.abort` signals `aborted_in_close` after its effects; the product-sink close
  test parametrised over `before_finish`, `after_finish`, `after_closed` (libx265, the 4 s 160x96 clip, 3 passed in
  14 s); the commit-leftover test controls `_install` (no `os.link` assumption); a close error without a cancel keeps its
  text (planted every-error-is-a-cancel engine fails by name); a clean-path stream-close error is the failure (planted
  always-quiet close fails by name).
- Gates at `04822ef`: ruff check, ruff format --check, mypy (136 files) clean; `test_jobs_export.py` +
  `test_export_bench.py` 87 passed; the product close timings 3 passed; the close/commit subset 10 consecutive clean
  runs. No product code changed in the cleanup. No test was run after `04822ef` (the host goes to exclusive windows).
- Report `docs/reports/wp3.14-export-batch.md` written (its V16 section OWED, replaced by cell 4).

## Reviewer B pass 1 remediation (cell 4)

Reviewer B (orchestrator seat, `wp3.14-mc` `b830412` = `dc76d92` on main `dbb5858`; evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp3.14\reviewB\review-B.txt`) BLOCKED. Rulings (orchestrator gen 14,
FINAL): B1 MAJOR, the cancel half this cell's (a non-ok analysis result while `cancelled()` is True becomes `CANCELLED`,
its text to an INFO line), the method-failure half BANKED (`analysis/engine.py:494-497`, WP3.11's, not edited; a Limits
line, trigger the next touch of that module); B2 MAJOR (V16 owed) DECLINED as sequencing; B3 MINOR fix (a raising
progress or stage callback after `commit` is a WARNING, the result stays ok); B4 ADVISORY fix (exact `Fraction` ratios,
an independent oracle). Granted: `export.py`, `disk_space.py`, owned tests; no V16.

| # | Sev | Failing first (unfixed engine) | Fix |
|---|---|---|---|
| B1 | MAJOR | `test_a_cancel_during_the_analysis_survives_a_raising_stream_close`: `'clip.mp4: analysis failed: OSError: cleanup close failed'` is not `CANCELLED`; planted text-only `_check_analysis` fails by name | `_check_analysis(result, progress, name)`: `cancelled()` (or the analysis's own `CANCELLED`) -> `_CancelledError`, a different text to INFO |
| B3 | MINOR | `test_a_raising_callback_after_commit_keeps_the_result_ok` x4 (video/photo x progress/stage): `'clip.mp4: RuntimeError: planted callback failure after commit'`; planted unguarded `_after_commit` x2 fails by name | `_after_commit(name, call)` runs the `committed` hook and the final report each guarded, WARNING with the error's type and text; the old `test_a_stop_after_commit_still_lists_the_committed_file` (it asserted the failure B3 removes) replaced |
| B4 | ADVISORY | `test_high_ratio_is_the_exact_decimal`: `1375001 == 1375000`; `test_video_ratio_term_wins_on_a_high_rate_source[high-1.10]` (oracle from the decimal text) | `QUALITY_RATIO` 11/10, 1/2, 1/4 and `MARGIN` 5/4 as `Fraction` |

Gates: ruff check, ruff format --check, mypy (136 files) clean; targeted (>= 11 GB free): engine, disk-space, batch 101
passed; photo file plus the video DR-28, cancel and product-close legs 26 passed; bench, naming, safe-write 175 passed. A
first combined run of all six files was cut off by its own 900 s `timeout` at 43 % (exit 124, no failure shown); it
is NOT counted. Report updated (seam non-ok line, cancel path, D87 constants, claims rows 2-4, Limits, Gates, Reviewer B).

**B1 (b) GRANTED (CHARC `d9154e06`, addendum to the rulings above):** the method-failure half is fixed, not banked.
GRANTED edit: `src/clearwater/analysis/engine.py` (origin WP3.11), the decode pass's `finally` block ONLY (the bare
`close()` wrapped: an `Exception` logged at WARNING with its type and text, the original outcome kept, a `BaseException`
still propagates; `logging` imported inside the block so the hunk stays the only change; no docstring describes the
close, so none changed; no interface change). The banked Limits line was dropped; a Limits line records that a
clean-path analysis close error is now a WARNING too.

| # | Sev | Failing first | Fix |
|---|---|---|---|
| B1 (b) | MAJOR | `test_a_method_failure_during_the_analysis_survives_a_raising_stream_close`: `'clip.mp4: analysis failed: OSError: cleanup close failed'` != the method's `ValueError` text; planted `test_planted_bare_analysis_stream_close_fails_by_name` (rebuilds `_decode` from its source with the bare close) failed on the missing guard | the guarded `finally` in `engine.py` |
| B1 (a) re-pointed | MAJOR | with B1 (b) fixed the analysis keeps its own `CANCELLED` under a raising close, so the close scenario no longer reaches `_check_analysis`: it stays as the ruled test (CANCELLED, nothing on disk, the close error in the analysis engine's WARNING), and the flag-versus-text rule moved to `test_an_analysis_error_after_a_cancel_is_cancelled` (the method asks the cancel, then raises; INFO line); the planted text-only control now runs that scenario and fails by name | test-only |

Gates after B1 (b): ruff check, ruff format --check, mypy (136 files) clean; the nine analysis files with the engine,
disk-space and batch files 350 passed.

## Reviewer B pass 2 gate fix (cell 4)

Reviewer B pass 2 (orchestrator seat, `wp3.14-mc` `99171df` = `b4259cc` on main; evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp3.14\reviewB2\review-B.txt`) BLOCKED with 1 MAJOR. A second blocking B is
adjudicated at the gate (no pass 3; the orchestrator verifies the fix by execution). Ruling (orchestrator gen 14, FINAL):
fix all four in one gate-fix series, failing test or control first; `engine.py` stays as it is; no V16.

| # | Sev | Failing first | Fix |
|---|---|---|---|
| 1 | MAJOR | `test_a_cancel_on_the_photo_writing_report_never_calls_the_writer`: `the photo writer ran after a cancel: [...shot_corrected.clearwater-partial-....png]`; `test_a_photo_writer_error_after_a_cancel_is_cancelled`: `failure is not the CANCELLED constant: 'shot.png: disk full while writing shot_corrected.png: OSError: [Errno 28] No space left on device'` | `export.py` photo: (a) `_check_cancel` after the "Writing" report and stage, before `SafeWrite`; (b) the `SafeWrite` block (begin, writer, commit) wrapped: an `Exception` while `cancelled()` holds -> `CANCELLED`, its text to INFO; planted `test_planted_no_cancel_check_before_the_photo_write_fails_by_name` (no check from the "Writing" stage on) |
| 2 | MINOR | reproduced first (scratch test, uncommitted): the OLD oracle passed with `_check_space` planted out (`1 passed`) | test-only: `_SizedStat` keeps every real stat field but `st_size`; B asserted by its failure text (`b.mp4: Not enough free space in ...`) and absent from the analysed names (the `_cache_key` the analysis uses); planted `test_planted_no_d87_fails_the_per_item_test_by_name` fails by name |
| 3 | ADVISORY | control first: `test_planted_close_guard_only_while_an_error_is_in_flight_fails_by_name` (rebuilds `_decode` with `except BaseException:` guarded + `else:` bare close) fails the clean-path assertion by name | test-only: `test_a_clean_path_analysis_stream_close_error_is_a_warning` (ok, output committed, the close error a WARNING from `clearwater.analysis.engine`) |
| 4 | MINOR | the report's scope line said nothing under `analysis/` changed | report: the granted `engine.py` edit named there |

Gates: ruff check, ruff format --check, mypy (136 files) clean; `test_jobs_export.py`, `test_jobs_batch.py`,
`test_jobs_disk_space.py`, `test_jobs_export_photo.py` 128 passed (>= 11 GB free).

## V16 rows (cell 4; ladder item 10, Q11, Q12)

Two EXCLUSIVE windows on `2e1dc11`, granted by the orchestrator (gen 14), CHARC holding; records under
`work/wp3.14/bench/` (not committed); every run ok, exits 0.
- Block 1, 2026-10-27 11:33:36Z-12:57:47Z, free memory 11.72 / 11.87 GB: GX011627 c3 cold x3 1.0654 / 1.0611 / 1.0631
  s/frame (31.93 / 31.80 / 31.86 min/min, MISS), warm 0.7743 (23.21, meets), ancuti2018 cold 0.7202 (21.58, meets),
  libx265 cold 1.1877 (35.60, MISS; close 14.0 s); synthetic 5.3K 8:7 cold 4.5389 (136.03, MISS; peaks 6354 MiB RSS,
  6104 MiB GPU). NVENC proof tied on every NVENC run.
- Block 2, 13:05:12Z-17:25:11Z, free memory 11.7 GB, disk 46.7 GB: GX011625 c3 cold sustained, 14,938 frames, 1.0429
  s/frame (31.26, MISS), analysis 29.8 %, close->committed 1.870 s, peaks 2903 MiB / 2450 MiB, tied; no thermal
  degradation (first hour 0.7549, last hour 0.7263 s/frame median; GPU peak 93 C); GPU at idle clocks through the
  77-minute analysis phase.
- CHARC `7ce2b89f`: the D106 miss on cold c3 is a measured figure for WP3.21 (not a stop, not a defect); the report's
  V16 section carries the split, libx265, 5.3K, the two "Not carried" warnings and the thermals as ruled. D87 at
  Standard: GX011627 105,909,120 B, GX011625 2,323,157,760 B (both ceiling-bound; each covers its output). CHARC
  `5cedff17` Limits notes added (the F1 (b) Windows flake, the G1 line).

## RESUME HERE -- CLOSED (cell 4 completed the V16 rows and the FINAL return; nothing owed)

Cell 3 stood down at a clean commit after the review loop TERMINATED at R2 (planned re-seat: V16 is several long
exclusive windows). Cell 4 is a FRESH seat.

| Gate | Dispatcher-read depth |
|---|---|
| Cell 3 dispatch | 0 (fresh seat) |
| Cell 3 R1 yield | 123,184 (59 turns) |
| Cell 3 R1-remediation yield | not read (the F1 (b) ruling arrived in the same turn) |
| Cell 3 R2 yield | 255,161 (143 turns) |
| Cell 4 dispatch | 0 (fresh seat) |
| Cell 4 window request (dry run) | 38,603 (12 turns) |
| Cell 4 B1 (b) yield | 146,307 |
| Cell 4 gate-fix yield (Reviewer B pass 2) | 183,062 (93 turns) |
| Cell 4 V16 block 1 release | 202,398 |
| Cell 4 V16 block 2 release | 218,272 |
| Cell 4 FINAL return | read by the dispatcher at the return |

**State:** the product, its tests, the instrument and the report are done and committed on `wp3.14` (head after this
ledger commit). Reviewer A converged (R1, R2; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.14\r1\`, `r2\`).
Last full suite: `7bb5d85`, 4864 passed / 0 failed (the remediation since is in this package's files only; the merge
candidate's full suite is the orchestrator's). Do NOT reopen the review, re-run the suite, or edit product code; a defect
found during the V16 runs is a STOP with a reproduction.

**Work order (ladder item 10, Q11, Q12; EXCLUSIVE, best effort; each window granted by the dispatcher, one at a time,
>= 5 GB free, nothing else heavy):**
1. Before any window: `uv run python tools/export_bench.py v16 --dry-run` (writes nothing) to list the plan; read
   `tools/export_bench.py`'s module docstring for the record's fields. No other preparation is needed.
2. WINDOW REQUEST per clip, in this order, each its own window:
   (a) `v16 --clip GX011627` -- 3 cold, 1 warm, 1 `ancuti2018`, 1 libx265 (6 runs);
   (b) `v16 --clip synthetic-5k3` -- the generated 5.3K 8:7 clip (150 frames), memory peaks (N4, V15 for WP5.2);
   (c) `v16 --clip GX011625` -- 1 cold, the sustained row, LAST. If (c) cannot be granted within the package's life it is
       recorded OWED in the accept record and taken before WP3.21 dispatches, never dropped (Q12).
   Run each in the foreground with its output to a file under `work\`; wait inside one tool call; the record is
   `work\wp3.14\bench\export-bench-*.json` (rewritten after every run). Exit 0 = every run ok; 1 = a run failed (the
   record says why: report it, do not re-run without the dispatcher); 2 = usage, config, footage or disk error.
   Send `WINDOW RELEASED: <rows, durations, exit>` at the yield after each window.
3. Replace the report's "V16 (ladder item 10)" section with the rows: per run frames, wall s/frame, min/min against
   D106's 25 min/min (0.834 s/frame at 30000/1001; verdict), per-frame median / p90 / max, the analysis share, the phase
   split from the stamps (probe, analysis, open, frames, close, committed -- the close-to-committed time is the
   cancel-latency figure the R1 F1 discussion named), strays, clocks and temperatures before/after, peak process-tree
   RSS (N4 16 GB) and peak graphics memory, the NVENC proof, `cache_complete_at_start`; the moment and conditions of
   each window; and the D87 estimate for GX011627 and GX011625 at Standard (`estimate_video_bytes` from each clip's
   probe; state the figure and its two terms). Nothing footage-derived committed; no location tag in any committed
   record.
4. FINAL: END YOUR TURN with the structured return report (the brief's "Return report", under about 70 lines): public
   API, phase and thread table, failure table, cancel path, D87 figures, V4 table per sample, V11 legs, the V16 rows
   with their conditions, DR dispositions, gates, Reviewer A rounds (R1, R2 TERMINATED) and verdict, open items
   (below), and the one-line "superseded by WP3.14" note for WP3.13's batch-sum sentence (Flag (ii); it is in the
   report's D87 section).

**Open items for the accept (carry into the return report):** a NEW DR row for serialising a GUI recompute against a
running export (Q5, WP4.3 trigger); CHARC's MINOR row against `io/video/encode.py` (`close` sets `"closed"` only from
`"open"`, condition 3 of `e7d25105`); Flag (i) (spec 10.2's N6 body vs D106, CHARC's v0.5.6 candidate); the 9
`test_methods_assembly_v8` skips are the worktree's own `work\` lacking `wp1.3\frames` (main's configuration runs
them).
