# WP4.6 — Export process isolation (dispatch brief, DRAFT by CHARC)

**Status:** DRAFT 2026-10-30 by CHARC (generation 9, session `clearwater-charc-20261029-1554`),
the architecture pass of plan section 3 done in this text (tripwire: a new standing process shape
and two new modules). The orchestrator dispatches it AFTER WP4.3's accept on main (WP4.3's
`app/main.py`, `app/activity.py`, `app/startup.py`, `tests/test_app_v7.py` are this package's
base); it names the base commit and fills the two `<at dispatch>` marks. The Questions below carry
CHARC's recommended answers; the cell's round-0 note may dispute any of them with evidence, and a
dispute is a STOP to CHARC. Spec v0.5.7; no spec clause changes. Owner decisions: none inside the
package. **V7 is a mandatory requirement (D66): relaxing it is owner-reserved and is NOT proposed;
this package is CHARC's recommendation over any relaxation.**

| Field | Content |
|---|---|
| ID and title | WP4.6 — Export process isolation: the export job runs in a spawned worker process; the interface process keeps progress, cancel and the result (V7 (c)/(e); DR-98) |
| Lane | **CLAUDE**: `implementer-opus-high` (design scope, STRONG). Reviewer A = Codex `gpt-6.1-sol` / high at the cell's seat, to convergence, five-round gate. Reviewer B = the Codex pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.6\rN\`, `reviewB\`, `windows\`. |
| Tier and size | STRONG. Size M (two new modules, one builder, one wiring change, the protocol tests, one EXCLUSIVE window). Cell depth discipline per `docs/model-prompting-standard.md`: ~250K evaluation point, STOP at ~400K; the dispatcher names mid-build yields. |
| Base | main `<at dispatch>` (after WP4.3's accept). Worktree `.worktrees/wp4.6`, branch `wp4.6`. |
| Goal | A File > Export (and a batch's video items) from the running shell does its probe, analysis, render, encode and safe write in a SEPARATE Python process spawned through AD-23's helper, so the two compute threads and FFmpeg's pipes leave the interface process; the interface process runs one lightweight thread per job that forwards IF-8 progress, delivers cancel and returns the IF-8 `JobResult`. V7 scenarios (c) and (e) (WP4.3 brief Q10) are re-measured OF RECORD on the final code in one EXCLUSIVE window and pass at or under 100 ms, or STOP with figures. The `ExportJobs` seam, IF-8 and every frozen interface are unchanged; the headless runner and every existing test keep the in-process engine. |
| Spec / decision clauses | V7 / D66 "UI responds within 100 ms during analysis, export and batch processing"; G9 (work off the UI thread); G8 / D44 / V11 (cancel leaves no partial output, no temporary); D45 (a cancelled batch stops); D81 (a failed item is logged, the batch goes on); D85 / 8.4 (leftovers cleaned next start); N1 (OS-specific code only with approval: this brief, through AD-23's helper); N4 (memory: two processes, see Q7); N6 / D106 (export wall: the window records it; a cost over 10 % is a STOP to CHARC, not a failure); N8 (sources never modified); N10 (same device, inputs, parameters: bit-identical pre-encode; the child runs the same engine, so unchanged by construction, shown by Q9's test); AD-9 (the job's device and reason in `JobResult.device` and the log line); AD-15 (export unavailable until the clip's analysis completes: unchanged, a parent-side rule); AD-20 (frozen interfaces: a change is a STOP); AD-23 (every product child process goes through `io/video/pipes.py`'s helper: extended by this brief to the Python worker, Q4); AD-25 (a) (app-data folders resolved in one place: the parent resolves and passes them); AD-28 / AD-30 (test sizing and markers); DR-62 (the per-clip activity lock stays in the parent wrapper); DR-67 (the GPU job's source and sink built with the device backend: unchanged, in the child); DR-68 (FFT plans released per job: in the child, by the job); spec 7 (the proxy cache: `cache/store.py:14` "Two processes sharing a folder are outside the envelope", Q3). |
| Files owned | **NEW:** `src/clearwater/jobs/export_process.py` (the parent side: `ProcessExportJobs`, the line protocol codec, the forwarder; imports only the standard library, `clearwater.interfaces`, `clearwater.jobs.export_seam` and `io/video/pipes.py`'s helper; NO Qt, NO `app`); `src/clearwater/app/export_worker.py` (the child's entry: `main(argv) -> int`, builds the root and runs ONE job; Qt-free; `python -m clearwater.app.export_worker`); `tests/test_jobs_export_process.py` (the protocol tests, parallel-leg); `tests/test_app_export_worker.py` (the end-to-end child tests, see Markers); `docs/reports/wp4.6-export-process.md`; `docs/proofs/wp4.6-ledger.md`. **EDIT:** `src/clearwater/app/composition.py` (ONE additive builder `process_export_jobs(...)`, Q2; nothing else); `src/clearwater/app/main.py` (the wiring: the panels' `ExportJobs` becomes WP4.3's guard wrapper OVER the process form, Q1 and Q6; nothing else); `src/clearwater/app/__init__.py` (docstring: the new module named); `src/clearwater/io/video/pipes.py` (docstring and the helper's docstring only: "every product FFmpeg, ffprobe AND Python worker launch", Q4; no code change); `tests/test_app_deps.py` (`APP_MODULES` gains `export_worker.py`; the Qt and CuPy rules apply to it unchanged); `tests/test_io_video_spawn.py` (ONLY if its product-spawn enumeration must name the new spawn site; the rule "every product spawn uses the helper" is NOT weakened); `tests/test_app_v7.py` (ONLY the scenario functions (c) and (e) need no change by design; an edit here is a STOP first); the register is CHARC's. **A grant, if round 0 names the need (Q5):** `src/clearwater/config/settings_store.py` and `src/clearwater/interfaces/parameters.py` are NOT edited; if no public decode exists for `Settings.to_json()` / `ParameterSet.to_json()`, the cell says so in round 0 and CHARC rules where the decode lives (IF-9/IF-10 are FROZEN: a method on them is AD-20's STOP). |
| NOT owned | `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN); `jobs/export_seam.py` (the seam: a change is a CHARC ruling), `jobs/export.py`, `jobs/batch.py`, `jobs/naming.py`, `jobs/safe_write.py`; `app/activity.py`, `app/startup.py`, `app/analysis_adapter.py` (WP4.3's; the wrapper is used, not changed, Q6); `gui/` whole (`jobs.py`'s runner, `export_panel.py`, `batch_panel.py`: unchanged by design, the seam hides the process); `cache/` (Q3 takes no `cache/` change); `io/video/` beyond the two docstrings; `tools/headless_export.py` (keeps the in-process engine); `tests/conftest.py`, `tests/fixtures/`, `tests/gui_support.py`; every existing test file not named above; `pyproject.toml`, `uv.lock` (no dependency). |
| Locks | No frozen interface. No dependency. No Qt in either new module. No write under the footage folder; every test writes under `tmp_path`. **Privacy:** the child's log lines and the parent's failure texts carry file NAMES as the engine already does (AD-13's rule), never a new full path; no EXIF, GPS or location content is logged. **Protocol:** one channel (the child's stdout, JSON lines, UTF-8, `\n`-terminated) carries progress, log records and the one result; the child's stderr is captured for the crash tail only; the parent sends cancel on the child's stdin. Nothing else in the child may write to its stdout (the FFmpeg grandchildren have their own pipes; Python logging goes through the protocol handler). |
| Markers | `tests/test_jobs_export_process.py`: parallel-leg (no marker; fake children are `sys.executable -c` scripts of a few lines, each under 2 s). `tests/test_app_export_worker.py`: the real worker on `tests/fixtures/video/hevc8-bt709-full.mp4` with `force_cpu` = `slow` with the reason "spawns a Python worker that imports clearwater (several seconds)"; a GPU form = `gpu`. The V7 re-measure is a WINDOW, not a test (AD-28). |
| Hardware flags | **EXCLUSIVE** for the V7 window (timing figures, plan 4.3) on GX011627 through `tools/local_config.find_footage_file` (read-only). One window, requested after Reviewer A converged on the final code; the orchestrator grants it; the driver of record is WP4.3's `s7_driver.py` from `C:\Users\rwsmy\clearwater-review-evidence\wp4.3\windows\` (md5 `0b9ee6cc...` per WP4.3's record; the orchestrator supplies the path), run from the wp4.6 worktree, modes `v7c`, `v7e`, `dr44c-export`, plus `v7d` (Q1's photo path unchanged: a control). At least 5 GB free; one heavy job at a time; a figure from an ungranted or parallel-worker run is not of record (AD-28). |
| Out of scope | Any change to the in-process engine (`jobs/export.py`); the GUI's own analysis (scenarios (a)/(b) passed in-process: 18 ms); a persistent warm worker or a worker pool (Q1 alternative (b), banked as a follow-on candidate); photos in the child (Q1); a layered or read-through proxy cache (Q3); V7 relaxation (owner-reserved, not proposed); N6 tuning (WP5.2); the look check and V2 (owner); chapters (v2); an installer or `pythonw` launch (noted only, Q4). |
| Debt and decided items | At the accept CHARC writes: **DR-98** (V7 (c)/(e) at 4K export OPEN after WP4.3; trigger WP4.6) CLOSED by the window figures, or its STOP recorded; **NEW AD-31** "export in a spawned worker process" (the design below, with the window's figures and the export-wall delta); AD-23 extended (the Python worker through the helper); DR-44 (c) re-confirmed for the process form (`dr44c-export`: the close ends within `SHUTDOWN_TIMEOUT_S`); DR-62 NOTE (the lock stays in the parent); DR-69 NOTE (two CUDA contexts: Q7's measured figures). The cell writes no register row. |
| Done | Plan 4.5. ruff check, ruff format --check, mypy strict clean; the touched tests and markers green; every existing test unchanged or changed only as this brief names; `uv run python -m clearwater` starts the shell on the process form (offscreen smoke, the loop ended by a timer) and exports the fixture clip through the child (the `slow` test); Reviewer A converged; the EXCLUSIVE window run with (c) and (e) at or under 100 ms (or a STOP with figures) and the export wall recorded against WP4.3's window-4 figure (209.1-210.9 s); Reviewer B returned (clean, or its one remediation and re-run); then the ONE two-leg gate at the orchestrator's seat on the final candidate per the fill's GATE_CHECKS at dispatch. Report and ledger written. |

## Why

WP4.3's four EXCLUSIVE windows measured V7 with the real engines (windows 1-4, 2026-10-29/30,
GX011627 4K, GPU, driver `s7_driver.py`). Scenarios (a), (b), (d) and (f) pass (18 / 21 / 65 /
47.5 ms longest gap; (b) and (f) regressed under an idle-gc policy that WP4.3 reverted). Scenarios
(c) "a File > Export of GX011627" and (e) "a 1:1 4K preview render during (c)" STOP at 182 / 196
ms before remediation and 180 / 181 / 182 ms after it (switch interval 5 and 1 ms; (e) at 1 ms
passed once at 80 ms, one sample). Window 3's characterisation (out-of-process heartbeat, py-spy
`--gil`, call wrappers) found the cause: **in-process GIL contention with no single holder** (the
export's two compute threads `clearwater-job` and `export-analysis` alternate on the GIL while the
interface thread's own Python work, progress delivery and the event filter, stretches to 30-55 ms
because each callback must win the GIL back; `rgb_to_planes` 148-177 ms per frame at p50; the
heartbeat never exceeded 16.3 ms, so it is not the host and not paging). WP4.3's remediation step
(the Python event filter removed from the paint/timer path, 101 -> 31 ms development witness; the
gc policy, reverted) did not move (c)/(e). CHARC ruled on window 3 (post `7b32521f`): "if (c) or
(e) still STOPs after this step, the remaining class is the spawned export process = DESIGN SCOPE,
a new package I brief, with the V7 owner flag carried". This is that package. The interface
process cannot be made responsive while two compute threads share its interpreter: the remedy is
to take them out of the interpreter.

## The design (CHARC's architecture pass; the cell builds this unless round 0 disputes it)

```
interface process (PySide6)                          worker process (Qt-free)
---------------------------                          -------------------------
ExportPanel / BatchPanel  --ExportJobs.job()-->      python -m clearwater.app.export_worker
  GuardedExports (WP4.3: DR-62 lock, journal)          reads ONE request document on stdin
    ProcessExportJobs (NEW, jobs/export_process.py)    builds composition.export_jobs(...) with
      spawn via tool_spawn_kwargs() (AD-23)              its OWN scratch cache folder (Q3)
      job thread: read stdout lines ---------------<--  Progress -> {"progress": [done,total,msg]}
        progress.report(...)                              logging  -> {"log": {level,name,msg}}
        poll progress.cancelled() every 50 ms  ------>    stdin line {"cancel": true}; stdin EOF
        last line {"result": JobResult} -> JobResult   exits 0 after the result line
        exit without result / bad exit -> failed result (crash tail from stderr, redacted)
```

1. **Where the boundary sits.** Exactly at the `ExportJobs` seam, UNDER WP4.3's `GuardedExports`
   wrapper: the DR-62 lock, the journal entry, the AD-9 line and the refusal texts stay in the
   parent unchanged; the wrapper is handed a `ProcessExportJobs` instead of `composition.
   export_jobs(cache=...)`. The panels and `QtJobRunner` see an ordinary IF-8 job: the job
   callable runs on the runner's worker thread as today, but that thread only blocks on a pipe
   read (no GIL held while blocked) and forwards small reports.
2. **One child per job** (`job()` builds the callable; the callable spawns). A video job is
   minutes; the spawn and import cost (a Python process importing `clearwater`, NumPy and, for a
   GPU job, CuPy) is seconds and is MEASURED in the window (Q8). Photos stay in-process (Q1).
3. **The request document** (parent -> child, stdin, one JSON object, then the cancel line or
   EOF): `{"format_version": 1, "source": <absolute path>, "kind": "video", "parameters":
   <ParameterSet.to_json() object>, "settings": <Settings.to_json() object>, "cache_folder":
   <the child's scratch folder>, "cache_limit_bytes": <int>, "app_version": <str>}`. The parent
   RESOLVES every folder (AD-25 (a)); the child reads no environment for a location. A document
   the child cannot decode is exit status 2 with one stderr line; the parent turns it into a
   failed result.
4. **The protocol** (child -> parent, stdout, JSON lines): `{"progress": [done, total|null,
   message]}` at most as often as the engine reports (the parent keeps the latest, as
   `QtProgress` does); `{"log": {"level": "WARNING", "name": "clearwater.jobs.export",
   "message": "..."}}` from a `logging.Handler` the child installs on the root logger (the
   parent re-logs each under logger `clearwater.app.export_worker` at the carried level, so the
   AD-9 line and the engine's warnings reach the parent's log file once); the LAST line
   `{"result": {"ok": bool, "outputs": [paths], "warnings": [str], "failure": str|null,
   "device": str, "elapsed_s": float}}`; then exit 0. The parent is strict: an unknown key, a
   non-JSON line or a line over 64 KiB is logged and IGNORED (never trusted), and the job ends
   as failed only on exit-without-result (Q10 names the texts). `CANCELLED` is carried as the
   constant: the parent returns `export_seam.CANCELLED` itself when the child's failure equals
   it (the seam's rule: the constant, not a copy).
5. **Cancel.** The parent polls `progress.cancelled()` every 50 ms on the job thread (between
   reads: the read uses a short timeout or a reader thread with a queue, the cell's choice,
   stated); on cancel it writes `{"cancel": true}\n` to the child's stdin and closes it. The
   child's `Progress.cancelled()` is a flag set by its stdin reader thread (also set on stdin
   EOF: a parent that died takes its children with it, D44). The engine stops at its next check
   and `SafeWrite` removes the temporary as today. If the child has not exited
   `KILL_AFTER_CANCEL_S` (3.0 s, one named constant; under `SHUTDOWN_TIMEOUT_S` 5.0) after the
   cancel line, the parent kills it (`Popen.kill`; on Windows this also ends its FFmpeg
   grandchildren only if the cell shows it does: state what happens to them, Q11), logs it, and
   returns a failed result naming the kill; a temporary left by a kill is D85's leftover and the
   journal entry WP4.3's wrapper holds makes the next start clean it (a test plants that case).
6. **Crash and exit.** Exit status without a result line: `ok` False, failure = one fixed
   sentence plus the status and the last stderr lines after redaction (file names only; the
   engine's own texts are already name-only), `device` "unknown", `elapsed_s` measured in the
   parent. The child's stderr is drained by a thread into a bounded deque (last 4 KiB), never
   left to fill a pipe.
7. **The child's cache (Q3).** `cache/store.py:14`: two processes on one folder are outside the
   envelope. The child opens its OWN `DiskProxyCache` on a per-job scratch folder the parent
   creates under `Locations.cache_dir / "export" / <uuid4>` and REMOVES after the result (and at
   the next start, Q3's leftover rule). The export's analysis therefore runs cold in the child
   (as every batch item's does today); its `_Analysis` thread overlaps the encode by design
   (`jobs/export.py:841-960`), so the wall cost is bounded and measured in the window. The GUI's
   cache is never touched by the child. The disk-space check already adds the analysis cache's
   growth (`analysis.cache_growth_bytes`, CHARC Q-R6), now against the scratch folder's volume.
8. **The spawn.** `[sys.executable, "-m", "clearwater.app.export_worker"]` with
   `**tool_spawn_kwargs()` (CREATE_NO_WINDOW on Windows, so a terminal's Ctrl-C reaches the
   parent only; `FFREPORT` dropped), `stdin=PIPE`, `stdout=PIPE`, `stderr=PIPE`, `cwd` = the
   parent's cwd unchanged, `close_fds` default. The child inherits the environment the helper
   returns; it adds `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1` for the protocol channel (the
   cell confirms the helper's dict copy is extended per call, not mutated). The AST pin
   `tests/test_io_video_spawn.py::test_every_product_spawn_uses_the_helper` must pass with the
   new site; the helper stays the single `creationflags` setter.
9. **The child's device.** The child runs the same `backend_selector()` (D111, AD-9): it sees
   the device memory the parent's preview pool has left. Q7 measures both; if the child falls
   back to CPU on GX011627 because of the parent's pool, that is a STOP to CHARC (the parent's
   pool release at the job boundary is a design choice, not the cell's).

## Questions (recommended answer first; a dispute in round 0 is a STOP to CHARC)

1. **Which jobs spawn.** Recommended **(a)**: `kind == "video"` jobs run in the child; photo jobs
   run in-process through the existing engine (scenario (d), 300 stills, passed at 65 ms; a
   per-photo spawn would add seconds per item to a batch that takes 29 s). `ProcessExportJobs`
   takes the in-process `ExportJobs` for photos and delegates by `request.kind`. (b) a persistent
   warm worker serving every job: better for photo batches, more lifetime design (idle GPU
   memory, shutdown, crash recovery); banked as a follow-on candidate, not built. (c) every job
   spawns: simplest code, the batch regression: declined.
2. **The builder.** Recommended: `composition.process_export_jobs(*, photo_exports: ExportJobs,
   cache_dir: Path, cache_limit_bytes: int, app_version: str = clearwater.__version__,
   command: Sequence[str] | None = None) -> ExportJobs` in `app/composition.py`; `command` None
   = `[sys.executable, "-m", "clearwater.app.export_worker"]`; tests pass a fake command.
   `ProcessExportJobs` itself lives in `jobs/export_process.py` and knows no `app` module (the
   layering test's rule: `jobs` never imports `app`).
3. **The child's cache.** Recommended (design item 7): a per-job scratch folder under
   `cache_dir / "export"`, removed by the parent after the result; at start-up, WP4.3's leftover
   clean-up is NOT edited (not owned): instead `ProcessExportJobs` removes stale `export/*`
   folders older than one hour when it builds its first job (a bounded, logged sweep; a test).
   Alternative: the child reads the GUI's cache read-only (outside `cache/`'s envelope; declined).
4. **N1 and the helper's reach.** Recommended: AD-23's helper covers the Python worker by the
   docstring edit named in Files owned; CHARC extends AD-23 at the accept (no new AD row for the
   N1 part; AD-31 is the design row). `pythonw` or a packaged launch is not planned (CLAUDE.md:
   no installer); `sys.executable` is the venv's interpreter; the report states the assumption.
5. **Decoding the request.** `ParameterSet.to_json()` and `Settings.to_json()` exist (IF-9 /
   IF-10). Recommended: the child decodes with the EXISTING public readers (the cell names them
   in round 0: the preset importer's parse for a ParameterSet, `clearwater.config.settings_store`'s
   loader form for Settings); if either has no public text-level entry, STOP in round 0 with the
   exact names and CHARC rules (an additive public function in `config/`, never a method on a
   frozen type).
6. **Wiring in `app/main.py`.** Recommended: the ONE line that builds the panels' engine changes
   from `composition.export_jobs(cache=cache)` to `composition.process_export_jobs(photo_exports=
   composition.export_jobs(cache=cache), cache_dir=locations.cache_dir, cache_limit_bytes=
   settings.cache_limit_bytes)` (names per WP4.3's merged `main.py`; the cell cites the line);
   `GuardedExports` wraps it unchanged. The headless runner keeps `composition.export_jobs`.
7. **Memory (N4, DR-69).** Recommended: the window records the parent's and the child's working
   set and the device's free memory before, during and after (c) and (e); two CUDA contexts (272
   MiB each per DR-69's estimate) are expected; a child CPU fallback on GX011627 is a STOP (design
   item 9). No cap is set here.
8. **Spawn cost.** Recommended: measured, not bounded: time from `job()`'s callable start to the
   child's first protocol line, CPU and GPU forms, in the report; a cost over 10 s is a STOP.
9. **N10 across the boundary.** Recommended: ONE test exports the fixture clip in-process and
   through the child with `force_cpu`, same parameters, and compares the two outputs'
   `SinkReport` frame count and the decoded first/middle/last frames byte-equal (the encoder is
   deterministic on CPU for libx265 at one preset? if not, compare pre-encode is impossible from
   outside: then the test compares the PNG photo path instead and the report says why).
   Alternative: no cross-boundary identity test; declined (the whole claim is "the same engine").
10. **Failure texts.** Recommended, fixed and ASCII: "The export worker ended without a result
    (exit status N)." with the redacted stderr tail appended after a newline (at most 4 KiB);
    "The export worker did not stop after cancel and was ended." for the kill path; "The export
    worker could not be started: <OSError text>" for a spawn failure. None equals `CANCELLED`.
11. **The FFmpeg grandchildren on a kill.** Recommended: the cell SHOWS (a test with a fake child
    that spawns a sleeping grandchild) whether `Popen.kill` on Windows ends the grandchild; if
    not, the child itself owns the clean-up (its `SafeWrite`/`sink.abort()` path on cancel is the
    normal route; the kill is the abnormal one) and the report records the orphan risk as a
    Limit with the leftover rule covering the temporary. No job object or process group API
    beyond the standard library.

## Task ladder

1. **Read.** `uv sync`. This brief; the WP4.3 record and report (the V7 tables, window 3's
   characterisation, the revert); `jobs/export_seam.py` whole; `jobs/export.py:529-700` and
   `:841-960`; `gui/jobs.py` whole; `app/composition.py`, `app/main.py`, `app/activity.py`,
   `app/startup.py` (merged); `io/video/pipes.py`; `cache/store.py:1-30`; `tests/test_app_deps.py`,
   `tests/test_io_video_spawn.py`; `tests/test_app_v7.py` (scenario functions (c), (e), (d));
   AD-9, AD-20, AD-23, AD-25, AD-28, AD-30, DR-44, DR-62, DR-67, DR-68, DR-69, DR-98.
2. **Round 0 note (turn 1, no product code), in the ledger:** the design restated in your words
   with every file:line it depends on; each Question answered or disputed with evidence; the
   decode entry points (Q5); the exact `main.py` line (Q6); the test list with the base each fails
   on; the protocol's edge cases you will test. YIELD; the orchestrator relays disputes to CHARC.
3. **RED first, `tests/test_jobs_export_process.py`** (fake children, parallel-leg): progress
   lines forwarded in order and the latest kept; the result line becomes an equal `JobResult`;
   `CANCELLED` returned as the constant; cancel delivered (the fake child echoes it and exits);
   kill after `KILL_AFTER_CANCEL_S` with the fixed text; exit without result (status 1, 2, and a
   Python traceback on stderr) with the tail redacted to names; a non-JSON line, an unknown key,
   an over-long line ignored and logged; stderr flood (1 MiB) does not block; stdin EOF seen by
   the child's flag (a fake child that reports cancelled when its stdin closes); a spawn failure
   (`command` = a missing executable); the scratch folder created before spawn and removed after
   the result, kept on a kill; the stale sweep (Q3); photo requests delegated to `photo_exports`
   without a spawn; `job()` touches no file.
4. **Build `jobs/export_process.py`** to green. Docstrings Google-style; the protocol documented
   in the module docstring with every line form and every failure text.
5. **RED first, `tests/test_app_export_worker.py`** (`slow`; `gpu` form optional): the real worker
   on the fixture clip with `force_cpu`: result `ok`, one output, provenance present, the scratch
   folder gone; cancel at the first progress line: no output, no temporary, `CANCELLED`; a
   malformed request document: exit 2, one stderr line; Q9's identity test.
6. **Build `app/export_worker.py`** to green: `main(argv)` reads stdin, decodes, builds
   `composition.export_jobs(...)` with the scratch cache (Q3) and the standard builders, installs
   the protocol logging handler, runs the job with the protocol `Progress`, writes the result,
   exits 0. CuPy is imported only through the backend selector's normal path (the deps test's
   rule: the module itself imports no `cupy`).
7. **Wire** `composition.process_export_jobs` (Q2) and `app/main.py` (Q6); the docstring edits
   (`pipes.py`, `app/__init__.py`); `tests/test_app_deps.py`'s `APP_MODULES`. The offscreen smoke
   (`uv run python -m clearwater` reaches the loop and exits 0 by a timer) is a committed test
   only if WP4.3 left one; otherwise a report figure.
8. **Verification loop** (plan 4.5): suspect, confirm independently, fix, repeat until a full
   pass finds nothing new; the touched tests and markers green; ruff, format, mypy.
9. **Review loop (Reviewer A)** to convergence on the final code.
10. **WINDOW REQUEST** (EXCLUSIVE): modes `v7c`, `v7e`, `v7d`, `dr44c-export` of record with WP4.3's
    driver from the wp4.6 worktree, plus the working-set and device-memory samples (Q7) and the
    spawn cost (Q8); nothing else runs on the host. Figures recorded as the driver prints them;
    no tuning between runs. A STOP on (c) or (e) comes to CHARC with the figures and the
    characterisation you can offer without a second window.
11. **Report** `docs/reports/wp4.6-export-process.md`: claims with evidence paths; the V7 table
    beside WP4.3's; the export wall beside 209.1-210.9 s and the delta in percent; spawn cost;
    memory; Limits (Q11's orphan risk, Q1's photo path, the cold analysis in the child, the
    one-hour sweep). Then hand the final candidate to the orchestrator for Reviewer B and the gate.

## Declared operating envelope

In: the owner's clips as spec 5.2 admits them, one export or batch at a time (the parent's
gate), the laptop's one GPU, Windows 11 (and portable code elsewhere: `tool_spawn_kwargs` returns
zero flags; the pipe protocol is plain). Out: two interface processes sharing one cache dir
(outside `cache/`'s envelope already); a child outliving the parent (stdin EOF stops it); `pythonw`
and packaged launches; hostile protocol input beyond the strict-ignore rule (the child is ours).

## Notes for the cell

- **Read `scripts/cell_depth.py` at every yield**; ~250K is the evaluation point, STOP at ~400K.
- **Windows (AD-28).** Heavy work ONLY in the window the dispatcher grants (task 10). The fixture
  tests are not windows. Never run the full suite in the worktree: the orchestrator's gate is the
  ONE suite run on the final candidate.
- **The footage folder is read-only** and never named in a committed file or a printed line.
- **STOP for:** a frozen-interface or seam change; a `cache/`, `jobs/export.py` or `gui/` edit; a
  Question disputed; a V7 (c)/(e) figure over 100 ms in the window; a child CPU fallback caused by
  the parent's pool; an export-wall cost over 10 %; a spawn cost over 10 s; an edit to
  `tests/test_app_v7.py`.
- **Report:** claims, evidence paths (`clearwater-review-evidence\wp4.6\`), Limits, the register
  rows you propose (CHARC writes them).

## For the orchestrator at dispatch

Fill the base commit and the worktree; confirm WP4.3's accept is on main and its `main.py` line
(Q6) by file:line; supply the driver's path and md5; name the mid-build yields; GATE_CHECKS per the
fill at dispatch (WP-T6's `fullclip` marker excluded from both legs). Lane share line per CLAUDE.md
(this is a Claude-built package; nets Codex). Disputes and STOPs route to CHARC with a recommended
answer first.
