# WP4.6 report: export process isolation

Brief `docs/briefs/wp4.6-brief.md` (FINAL on CHARC `39dad78f5b10ceeb`); rulings, latest wins:
round 0 `a265489d`, R1 `e15d408ac31ce62b`, R2 `55959e2ffd95df7f` (design change (d)), the spawn
text `3ed8335fe96a8e2c`, R3 `acc0255dbda23ae2`. Ledger `docs/proofs/wp4.6-ledger.md`. Base
`b6a31b5`; product code final at `d1ba71f2`; the window ran on head `1563da2a` (ledger-only
commits above `d1ba71f2`). Built by cells 1-5 (`implementer-opus-high`).

STATUS: build complete; Reviewer A converged (rounds 1-3 and the terminating clean-up, CHARC's
cap, no round 4; the clean-up verified at the orchestrator's seat); the EXCLUSIVE window ran with
every run EXIT 0 and NO STOP. **V7 (c) and (e) pass at 4K: 39.0 ms and 48.0 ms (WP4.3: 180.0 /
181.0 and 182.0 ms).** The export wall is 226.2 s against WP4.3's 209.1-210.9 s, **+7.3 % to
+8.2 %**, under N6's 10 % STOP (but see Limit 3). Reviewer B and the gate follow.

Evidence roots: `<evidence>` = `C:\Users\rwsmy\clearwater-review-evidence\wp4.6\`; `<work>` =
the wp4.6 worktree's `work\wp4.6-window\` (the window's outputs; gitignored, not committed).

## What WP4.6 adds

- `src/clearwater/jobs/export_process.py`: `ProcessExportJobs`, an `ExportJobs` whose video jobs
  each spawn ONE worker process; photo requests go to the in-process engine unchanged (Q1 (a)).
  The job thread writes the request line, forwards the worker's progress and log lines, delivers
  the cancel on stdin, kills the worker `KILL_AFTER_CANCEL_S` (3.0 s) after the earlier of the
  cancel and the result, and returns the IF-8 `JobResult`. Three daemon threads do the blocking
  I/O (stdin, stdout lines, the 4 KiB stderr tail), so the job thread only waits on a queue for
  at most `POLL_S` (50 ms). The parent is strict: a line that is not UTF-8 JSON, has a
  wrong-typed value or an unknown key, or is over 64 KiB is logged and ignored; only an exit
  without a result fails the job. The first job of an instance sweeps `cache_dir/export/*`
  folders older than one hour.
- `src/clearwater/app/export_worker.py`: `python -m clearwater.app.export_worker`. It takes over
  its original stdout as the protocol channel before anything runs (fd 1 and `sys.stdout` then
  point at stderr), decodes ONE request line with the frozen types' own decoders
  (`ParameterSet.from_dict`, `Settings.from_json`; exit 2 with one stderr line on a malformed
  request), builds `composition.export_jobs` over its own scratch cache, runs the job and writes
  the result line. Its cancel flag is set by `{"cancel": true}` or stdin EOF. No Qt, no `cupy`
  import of its own.
- `src/clearwater/app/composition.py`: `process_export_jobs(*, photo_exports, cache_dir,
  app_version, command=None)` (Q2: the cache limit travels in each request's settings, so a
  limit changed in the settings dialog applies to the next export).
- `src/clearwater/app/main.py`: the ONE wiring line: the panels' engine is
  `process_export_jobs(photo_exports=composition.export_jobs(cache=cache),
  cache_dir=locations.cache_dir)`, wrapped by WP4.3's `GuardedExports` unchanged (the DR-62 lock,
  the journal entry, the AD-9 line and the refusal texts stay in the parent). The headless runner
  keeps the in-process engine.
- `src/clearwater/io/video/pipes.py` (docstrings only): AD-23's helper covers the Python worker.
  The spawn is `subprocess.Popen(command, stdin=PIPE, stdout=PIPE, stderr=PIPE,
  **tool_spawn_kwargs())`; no environment change (R0-STOP-2): the channel is ASCII JSON on binary
  streams, so it is encoding-proof without `PYTHONUTF8`.
- Docstrings in `app/__init__.py` and `app/activity.py`.
- Tests: `tests/test_jobs_export_process.py` (70 nodes; fake children; parallel leg),
  `tests/test_app_export_worker.py` (the real worker on the fixture clip, `slow`), the granted
  test-support module `tests/export_worker_hold.py` (a worker command that holds its sink's first
  write on marker files: R0-STOP-1 (i)) and the granted edits in `tests/test_app_v7.py` (scenario
  (e)), `tests/test_app_wiring.py` (DR-44 (c) export branch), `tests/test_app_startup.py` (the
  process form's type), `tests/test_app_deps.py`, `tests/test_io_video_spawn.py` (the AD-23 pin's
  count 7 -> 8; the rule not weakened).

## V7 of record (the EXCLUSIVE window)

The window: granted by the orchestrator, opened to CHARC 2026-11-01 08:46Z, chain 08:46:17Z to
09:08:23Z, closed 09:08:23Z. Chain `bash <evidence>\windows\window-commands.sh` (md5
`c18ba54db038b04c0dd73386ab79cac6`) from Git Bash, `PYTEST_ADDOPTS` unset, offscreen, every run
independent, no tuning, no re-run; head `1563da2a` (`src/` and `tests/` equal to `d1ba71f2`,
checked by the chain); drivers md5-checked at the start: the pinned
`clearwater-review-evidence\wp4.3\windows\s7_driver.py` (`0b9ee6cc3ebd2cf07c35dec934cfd901`) for
`v7c` and `v7d`, the WP4.6 copy `<evidence>\windows\s7_driver_wp46.py`
(`074cbb62b2a9aa8949ebcf30d803b51a`; one region differs: the `dr44c-export` hold set through the
worker command, ledger Y2b) for `v7e` and `dr44c-export`. C: 178 GB free before, 177 GB after;
RAM available 17.72 / 17.92 of 33.52 GB before / after. Logs `<work>\<run>.txt`, exits
`<work>\exits.txt`, the seat's stdout `<evidence>\windows\window-run.stdout` (`CHAIN EXIT=0`).

V7 (WP3.16's 10 ms probe; longest gap / p99, ticks; bound 100 ms), GX011627, GPU:

| Scenario | WP4.6 window (of record) | WP4.3 (of record, in-process export) |
|---|---|---|
| (c) File > Export | **39.0** / 11.0 ms, 22,616 ticks; export 226.2 s, one 86.0 MB output; analysis before the export 65.2 s. EXIT 0: **PASS** | 180.0 / 12.0 ms (5 ms switch interval), 181.0 / 12.0 ms (1 ms); export 209.1 / 210.7 s. Window 4: OPEN STOP |
| (e) a 1:1 4K render during (c) | **48.0** / 12.0 ms, 23,359 ticks; 1 render with k = 1 inside the export sink's held write; analysis before 60.9 s. EXIT 0: **PASS** | 182.0 / 12.0 ms (5 ms); 80.0 / 12.0 ms (1 ms, one sample). Window 4: OPEN STOP |
| (d) a 300-still batch (photo path, a control) | 67.0 / 53.0 ms, 1,882 ticks; 300 of 300 done in 33.7 s. EXIT 0: PASS | 56.0 / 43.0 ms, 1,855 ticks; 28.6 s. Window 5: PASS |
| DR-44 (c), export | the close ended True in 509 ms (`SHUTDOWN_TIMEOUT_S` 5.0 s), at close [True], no temporaries. EXIT 0: PASS | (WP4.3's in-process form) |

(a), (b) and (f) were not re-run: WP4.6 changes only the export path (the brief's mode list).
Every driver run printed `footage folder unchanged: True (128 files)` and `product logs naming
the footage folder: 0`. (d) is the in-process photo path unchanged by WP4.6 (Q1); its figure moved
56.0 -> 67.0 ms inside the bound, a different window and host moment (not characterised).

**DR-98** (V7 (c)/(e) at 4K export OPEN after WP4.3) closes by these figures (CHARC writes the
row). The cause WP4.3 named, in-process GIL contention between the export's compute threads and
the interface thread, is removed by construction: the compute threads now run in the worker.

## The export wall (N6 / D106)

| | Export wall | Delta |
|---|---|---|
| WP4.3 window 4 (in-process, the clip's analysis complete in the GUI cache) | 209.1-210.9 s | - |
| WP4.6 window `v7c` (of record; the driver's `export N s` line) | **226.2 s** | **+7.3 % to +8.2 %** |
| WP4.6 `v7c-measure` (NOT of record: hooks and a 250 ms sampler in the process) | 233.1 s (`JobResult.elapsed_s`; the driver's line 233.2 s) | +10.5 % to +11.5 % |

The cost is the cold analysis in the worker (Limit 3): the worker's scratch cache is empty, so
its analysis decode pass re-runs beside the render, where the in-process export hit the GUI
cache's complete entry. The figure of record is under the 10 % STOP; the margin is under two
percentage points, and the instrumented, not-of-record run was over it. `v7e-measure`'s 235.4 s
includes the scenario's held write and is not an export-wall figure.

## Spawn cost (Q8; NOT of record)

From `<work>\v7c-measure.txt`, `<work>\v7e-measure.txt`, `<work>\spawn-measure.txt` (helper
`<evidence>\windows\wp46_measure.py`, md5 `ea4d61e4add35bda793abc72234794c7`; hooks on
`export_process`, no product file changed):

| Run | `job()`'s callable start to `Popen` returned | to the worker's first protocol line |
|---|---|---|
| v7c-measure (GPU export) | 10 ms | 1,078 ms (a progress line) |
| v7e-measure (GPU export) | 7 ms | 793 ms (a progress line) |
| spawn, GPU form x3 (default settings) | 7 / 6 / 5 ms | 662 / 689 / 659 ms |
| spawn, CPU form x3 (`force_cpu`) | 3 / 6 / 34 ms | 709 / 719 / 765 ms |

All far under the brief's 10 s STOP. The first protocol line comes before the worker chooses its
device, so the two forms do not differ there (Limit 8). Every export job's `JobResult.device` was
`GPU`: no CPU fallback caused by the parent's preview pool (design item 9's STOP not reached).

## Teardown versus `KILL_AFTER_CANCEL_S` (NOT of record)

The result line to the worker's exit: 270 ms (v7c-measure) and 265 ms (v7e-measure), not killed,
exit status 0: about 9 % of the 3.0 s grace, so a GPU worker's interpreter and CUDA teardown is
not cut short. After a cancel (the spawn runs, cancelled at the first line): first line to exit
681-905 ms, result line to exit 64-78 ms, none killed.

## Memory (Q7, N4, DR-69; NOT of record)

`psutil` working set / private bytes, MiB; the worker = the python process with the most private
bytes under the spawned launcher; the tree = launcher, interpreter and the worker's FFmpeg
processes summed. Device memory is device-wide (Limit 7).

| | v7c-measure | v7e-measure |
|---|---|---|
| parent before the job | 793 / 2,343 | 986 / 2,530 |
| parent peak during | 1,064 / 2,549 | 1,179 / 3,810 |
| parent at the result / after | 891 / 2,123; 891 / 2,123 | 1,179 / 3,762; 989 / 2,472 |
| worker interpreter peak / at the result | 764 / 3,730; 668 / 2,433 | 765 / 3,603; 668 / 2,433 |
| worker tree peak (up to 9 processes) | 3,417 / 7,766 | 3,437 / 7,671 |
| device used before / peak / after | 615 / 3,307 / 257 MiB (least free 4,642) | 609 / 4,269 / 297 MiB (least free 3,680) |
| compute contexts | parent at the first line; parent and worker at the result | the same |

Two CUDA contexts are present during an export (parent and worker), as DR-69 expected. For
comparison only (WP4.3 window 4, in-process, not of record, decimal MB): the interface process at
the export's result 954.6 MB working set / 2,723.4 MB private (2,597 MiB), its FFmpeg children not
counted. With the export in the worker the parent's private bytes at the result are 2,123 MiB in
(c); the host carries the worker's tree beside it. No cap is set (brief Q7).

## The scratch folder (F8, ruling (e))

At its removal after the result, the worker's scratch folder held **61.6 MiB in 3 files**
(v7c-measure and v7e-measure; `cache_limit_bytes` 20,000,000,000): the analysis proxies of
GX011627. It lives under `cache_dir/export/<uuid4 hex>`, outside the GUI cache's accounting
(ruling (e)), for the length of one job.

## Reviewer A

Codex `gpt-6.1-sol` / high at the cell's seat (WSL, codex-cli 0.162.1). Round 1 (`7a20c7bd`):
0 critical, 8 major (5 blocking fixed: F1 F2 F3 F5 F6; F4 F8 banked pre-existing; F7 minor),
6 minor; round 2 (`f91aea96`): 0 / 2 / 3 (R2-2 blocking, closed by CHARC's design change (d));
round 3 (`cf378034`, the LAST full round): 0 / 2 / 3 (R3-1 protocol class, fixed RED-first in the
terminating clean-up: `7479f4c4` RED, `b96a6381` fix; R3-2 reopened F7, fixed `6e7caf1f`; R3-4
test-only `c8eb5988`; R3-5 `0c91dd33` RED, `a1345696` fix; R3-3 a Limit). Per-round ledger and
adjudications: `docs/proofs/wp4.6-ledger.md`, `<evidence>\r1\` .. `<evidence>\r3\`. Last targeted
run at `6e7caf1f`: `tests/test_jobs_export_process.py tests/test_app_export_worker.py
tests/test_app_deps.py tests/test_io_video_spawn.py` 361 passed; ruff, format and mypy clean.

Reviewer B (Codex at the orchestrator's seat, on `c0eedb0e`): 1 major, 2 minor, fixed RED-first
(RED `d5846415`): B-1, a progress count too large for a float is now an ignored, logged line
through one helper for every decoded number (`fc403cf3`); B-2, the clean-up covers the
conversation's whole set-up after the spawn (`1ab92604`); B-3, an overflowing `created` in the
settings' `last_parameters` is exit 2 (`aaf1f1fa`). Targeted run 365 passed. The window figures
are unaffected: the fixes change only malformed-line and malformed-request handling and the set-up
order, never a well-formed export's path.

## For CHARC at the accept (the cell writes no register row)

- DR-98: CLOSED by the window figures above.
- NEW AD-31 "export in a spawned worker process": the design above, with the window's figures and
  the export-wall delta (+7.3 % to +8.2 %).
- AD-23 extended: the Python worker through the helper (8 product spawn sites).
- DR-44 (c) re-confirmed for the process form: the close ended in 509 ms.
- DR-62 NOTE: the lock stays in the parent wrapper. DR-69 NOTE: two contexts, the device figures
  above.
- F8 and the F4 candidate (Limits 5 and 6); the remedy candidate for Limit 3.

## Limits

1. **Orphan FFmpeg on a kill (Q11).** `Popen.kill` ends the worker (killing the venv's launcher
   also ends the interpreter behind it: `<evidence>\r0\q11_launcher.py`) but NOT its FFmpeg
   grandchildren (`<evidence>\r0\q11_grandchild.py`; committed test
   `test_a_kill_leaves_the_grandchild_running`). They end on their own when their pipes break
   (decode: the reader is gone; encode: stdin EOF). A temporary left by a kill is D85's leftover
   under WP4.3's journal entry, cleaned at the next start. A kill happens only when a worker is
   still running 3.0 s after the cancel or the result; none was seen in the window.
2. **Photos stay in-process (Q1 (a)).** A photo export, and every photo item of a batch, runs in
   the interface process exactly as before WP4.6; (d) passes at 67.0 ms. A persistent warm worker
   (Q1 (b)) is banked as a follow-on candidate, not built.
3. **The cold analysis in the worker.** Every video export's analysis runs cold in the worker's
   per-job scratch cache, where the in-process export reused the GUI cache's complete entry. The
   export wall rose +7.3 % to +8.2 % (of record), and +10.5 % to +11.5 % in the instrumented,
   not-of-record run: the margin to N6's 10 % STOP is thin and load-sensitive. The remedy
   candidate (it touches `cache/`'s layout, so CHARC's ruling): seed the scratch folder with a
   copy of the GUI cache's complete entry under the clip lock. Not built.
4. **The one-hour sweep.** A scratch folder left by a kill or a crash is removed only by a later
   instance's first video job, and only once it is older than `STALE_AFTER_S` (one hour); until
   then it occupies disk outside the GUI cache's accounting (61.6 MiB for GX011627). A sweep cut
   short by a cancel (R3-2) stops before its next entry; the entries it skipped stay until
   another instance's first job.
5. **F4 (banked pre-existing).** A failure or log text the worker relays from the export engine
   can carry the full path of the file an `OSError` names: the text is the engine's own
   (`ExportEngine._describe`, `jobs/export.py`, WP3.14 `bda46fc6`), shown and logged in-process
   before WP4.6 exactly as it is now relayed. The parent adds no path and passes such a text
   unchanged; the worker's stderr tail and the parent's own start and encode errors reach the log
   only, never a failure text (CHARC `55959e2f` (d)). A register candidate; `jobs/export.py` is not
   WP4.6's.
6. **F8 (banked pre-existing, widened).** The worker's scratch cache is not checked against its
   own volume: the engine's D87 re-check charges the analysis cache's growth to the OUTPUT
   folder's volume (`jobs/export.py:916`, WP3.21 `0daab17f`). Before WP4.6 only a cold batch video
   item met this; now every video export's analysis is cold, so an export whose cache folder and
   output folder are on different volumes can fill the cache volume without D87's refusal.
   Bounded: one clip per job under `request.settings.cache_limit_bytes`, removed after the result
   (61.6 MiB measured for GX011627). CHARC writes the register row at the accept (ruled (b)).
7. **Reader threads after the drain deadline (R3-3).** After the drain deadline the worker's
   stdout and stderr reader threads, and the pipe handles they hold, stay alive until every
   process holding the pipes' write ends has exited; a descendant that inherits the worker's
   stdout or stderr keeps them alive past the job. No product spawn makes such a descendant
   (every product spawn in the worker redirects all three streams); the threads are daemons and
   end when the holder exits.
8. **Device memory per process is not measurable here.** Under WDDM `nvidia-smi` reports
   per-process device memory as N/A, so Q7's device figures are device-wide (used and free) with
   the compute-context presence of the parent's and the worker's process ids.
9. **The two spawn forms coincide.** The worker's first protocol line precedes its device
   choice, so the GPU and CPU forms' spawn cost cannot be told apart by this measure; the GPU's
   set-up time falls inside the export, after the first line.
10. **The interpreter (Q4).** The worker is `sys.executable -m clearwater.app.export_worker`; in a
    uv venv on Windows `sys.executable` is a launcher whose child is the interpreter. No `pythonw`
    or packaged launch is planned (no installer).
11. **Measurement runs are not of record.** The spawn, teardown, memory and scratch figures come
    from `wp46_measure.py` runs with hooks and a sampler in the measured process, after the runs
    of record in the same window.
