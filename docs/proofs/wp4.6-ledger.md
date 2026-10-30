# WP4.6 ledger -- export process isolation (cell 1, implementer-opus-high)

Brief `docs/briefs/wp4.6-brief.md` FINAL on CHARC `39dad78f5b10ceeb`; base `b6a31b5` (main
`94717423` plus the brief's FINAL commits). Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.6\`.

## Cumulative round ledger

| Round | Date | Transport / CLI | Critical | Major | Minor | In-env / out | NEW / REOPENED | Reverts | Fixes: product / test-only | Depth (dispatcher) |
|---|---|---|---|---|---|---|---|---|---|---|
| 0 | 2026-10-30 | (no review: round-0 note) | - | - | - | - | - | - | - | 194,313 (cell 1, retired at round 0) |
| Y1 (build) | 2026-10-30 | (no review: tasks 3-4, cell 2) | - | - | - | - | - | - | - | 171,586 (cell 2 at Y1, 05:08Z) |
| Y2a (build) | 2026-10-30 | (no review: tasks 5-6, cell 2) | - | - | - | - | - | - | - | (dispatcher fills: cell 2 at Y2a) |

## Round 0 (task 2): the design restated, the Questions, the stops

No product code. Probes and logs: `clearwater-review-evidence\wp4.6\r0\` (md5s in `MD5SUMS`
there): `q9_determinism.py` + `q9.log`, `q11_grandchild.py`, `q11_launcher.py`,
`design8_pin.py`, `r0_shape_plugin.py` + `r0_shape.log` + `r0_shape_v7.log`.

### R0-STOP-1 (finding, reproduced): three existing tests and two pinned-driver modes reach into the in-process engine

The brief's premise "`tests/test_app_v7.py`: the scenario functions (c) and (e) need no change
by design" is false for (e), and two tests the brief does not own break the same way. After the
Q6 wiring, `application.exports._engine` is the `ProcessExportJobs`, not an `ExportEngine`:

1. `tests/test_app_v7.py:302-304, :322, :347` (scenario (e)) reads and swaps
   `application.exports._engine._sink_for` to hold the export's first sink write (the
   `k1_renders_during_a_sink_write` witness). The sink now lives in the child.
2. `tests/test_app_wiring.py:749-760` (`test_dr44c_a_real_job_ends_within_the_shutdown_timeout_at_close[export]`)
   swaps `engine._sink_for` for `_ProgressSink` to hold mid-encode before the close.
3. `tests/test_app_startup.py:212-213` asserts `isinstance(exports, ExportEngine) and
   exports._cache is application.cache` (WP4.3 ruling Q16: every export shares the one cache;
   by this design a VIDEO export no longer does, design item 7).
4. The pinned driver `s7_driver.py` (md5 `0b9ee6cc3ebd2cf07c35dec934cfd901`): mode
   `dr44c-export` swaps `exports._engine._sink_for` (`s7_driver.py:979-989`) and mode `v7e`
   runs scenario (e) above. Modes `v7c` and `v7d` touch no engine internal and run unchanged.

**Reproduction** (no repository file changed): `r0_shape_plugin.py` makes `build_application`
get an export engine of the process form's SHAPE (an `ExportJobs` with `job` only). Results:
`test_the_applications_engines_are_wholly_real` FAILS at `test_app_startup.py:213`
(`isinstance(<_ProcessShaped>, ExportEngine)` False); `dr44c[export]` FAILS at
`test_app_wiring.py:750` (`AttributeError: '_ProcessShaped' object has no attribute
'_sink_for'`); `test_v7_c_e_export_and_a_full_render_during_it` passes (c) and FAILS at
`test_app_v7.py:303` (same `AttributeError`). Logs `r0_shape.log`, `r0_shape_v7.log`.

**Recommended answer (CHARC rules):** grant, as owned files, (i) a NEW test-support module
`tests/export_worker_hold.py`: a worker command for tests (`[sys.executable, <that file>]`)
that runs `clearwater.app.export_worker`'s public run function with a `sink_for` wrapper whose
first `write` creates a `writing` marker file in a folder named by an environment variable,
then waits until a `release` marker exists or the child's cancel flag is set, then writes
`returned`; (ii) the minimal edits in `tests/test_app_v7.py` scenario (e) (the hold set on
`application.exports`' process form through its command and the marker folder; the witness
name and meaning unchanged: a `k == 1` render delivered while the export's first sink write is
held), in `tests/test_app_wiring.py` (the `export` branch of the dr44c test, same hook), and in
`tests/test_app_startup.py:212-213` (the process form's type, and its photo leg an
`ExportEngine` sharing the one cache); (iii) a WP4.6 copy of the driver for the window whose
`v7e` and `dr44c-export` modes use the same hook (new md5 supplied at the window; `v7c`, `v7d`
run on the pinned driver unchanged). Alternative: keep the GUI's exports in-process (no wiring)
-- declined, it is the package's goal. Scenario (c) itself needs no change (reproduced: it
passes on the process shape).

### R0-STOP-2 (finding, reproduced): design item 8's environment extension fails the AD-23 pin

Design item 8 says the spawn "adds `PYTHONIOENCODING=utf-8` and `PYTHONUTF8=1`" to the helper's
environment. The pin `tests/test_io_video_spawn.py:224-233` requires each product spawn call to
carry `**tool_spawn_kwargs()` as a direct call AND no `env=`/`creationflags=` keyword.
`design8_pin.py` applies that rule: "extend a helper copy" (`kwargs = tool_spawn_kwargs();
kwargs["env"][...] = ...; Popen(..., **kwargs)`) is an OFFENDER (`uses_helper=False`); "`env=`
beside the helper" is an OFFENDER (`overrides_policy=True`); "helper only" passes. The helper
does return a fresh dict per call (`io/video/pipes.py:52-55`), but no extension form passes the
pin without weakening it, and `pipes.py` is docstring-only here.

**Recommended answer:** no environment change. The channel is made encoding-proof instead: both
directions are JSON with `ensure_ascii=True` (pure ASCII bytes) written to and read from the
BINARY streams (`sys.stdin.buffer`, a dup of the original stdout fd), each line `\n`-terminated
with no newline translation; the parent decodes bytes as UTF-8 strictly. Non-ASCII file names
travel as `\uXXXX` escapes. The call is `subprocess.Popen(command, stdin=PIPE, stdout=PIPE,
stderr=PIPE, **tool_spawn_kwargs())`; `test_io_video_spawn.py:235`'s count goes 7 -> 8 (the
owned edit the brief allows); the rule is not weakened.

### Questions

- **Q1 (which jobs spawn): AGREE (a).** `kind == "video"` spawns; `"photo"` delegates to
  `photo_exports.job(request)` with no spawn and no file touched.
- **Q2 (the builder): AGREE in form, DISPUTE one parameter (minor).**
  `composition.process_export_jobs(*, photo_exports, cache_dir, app_version=clearwater.__version__,
  command=None) -> ExportJobs`. Recommended: DROP `cache_limit_bytes`; the child's scratch cache
  takes `request.settings.cache_limit_bytes` (`ExportRequest.settings` is "the settings at the
  time of the request", `jobs/export_seam.py:44-46`). A builder argument read once at
  `build_application` (`main.py:192`'s form) goes stale when the settings dialog changes the
  limit (G12; `test_app_wiring.py` G12 sets it to 3 GB mid-session). The request document keeps
  its `cache_limit_bytes` key, filled from the request.
- **Q3 (the child's cache): AGREE**, with one clarification: the stale `export/*` sweep runs in
  the FIRST JOB'S RUN on the worker thread, not in `job()` (`ExportJobs.job` "touches no file",
  `export_seam.py:61-62`, and runs on the interface thread). The GUI cache never touches
  `export/`: its open and `clear` act only on entry-named folders (`cache/store.py:562-582`,
  `cache/keys.py:89-101`).
- **Q4 (N1, the helper's reach): AGREE.** `sys.executable` is the venv's `python.exe`, which on
  this machine is a LAUNCHER (`q11_launcher.py`: `Popen.pid` 76772, interpreter pid 76108,
  `sys._base_executable` the uv CPython); the report states it.
- **Q5 (decoding): AGREE, no STOP.** The existing public text readers are the frozen types' own:
  `ParameterSet.from_json` / `from_dict` (`interfaces/parameters.py:239-253`, `:164-226`) and
  `Settings.from_json` (`interfaces/settings.py:113-162`), each with `from_json(s.to_json()) ==
  s`. Used as they are; no method added. Not the preset store or `load_settings`: those read
  FILES and apply migration and value repair (`config/settings_store.py:112-160`), which would
  change a request's values; the round trip must be exact (N10).
- **Q6 (wiring): AGREE, names cited.** `src/clearwater/app/main.py:282` (inside `:281-287`)
  becomes `composition.process_export_jobs(photo_exports=composition.export_jobs(cache=cache),
  cache_dir=locations.cache_dir)`, `locations` the parameter of `build_application` (`:244`);
  with Q2's dispute ruled the other way it gains `cache_limit_bytes=window.session.settings().
  cache_limit_bytes` (`:192`'s form). Nothing else in `main.py`. The offscreen smoke exists:
  `tests/test_app_startup.py:175` `test_python_m_clearwater_starts_the_shell_and_exits_0`
  (unchanged; it now builds the process form).
- **Q7 (memory): AGREE**, measured in the window.
- **Q8 (spawn cost): AGREE.** Development witness (not of record): a child importing
  `clearwater.app.composition` and `clearwater.jobs.export` took 1.20 / 0.79 / 0.77 s (CPU, no
  CuPy). Far under 10 s.
- **Q9 (N10 across the boundary): AGREE, the frame form is feasible.** `q9_determinism.py`: two
  in-process CPU libx265 exports of `hevc8-bt709-full.mp4`, same parameters: file md5s DIFFER
  (`b67809dc...` / `dd54e2df...`, the container's metadata), decoded framemd5 IDENTICAL over 45
  frames. The test compares the in-process and child outputs' decoded framemd5 (count and every
  frame), not file bytes; the frame count stands for the `SinkReport` count (not visible outside
  the engine).
- **Q10 (texts): AGREE**, fixed ASCII texts as written. The spawn-failure text carries the
  `OSError`'s text redacted to names (the interpreter path holds the user's folder names).
- **Q11 (grandchildren on a kill): ANSWERED by probe.** `q11_grandchild.py`: `Popen.kill` of a
  child leaves its sleeping grandchild ALIVE on Windows (the probe then ended it).
  `q11_launcher.py`: killing the venv launcher DOES end the interpreter behind it (the launcher's
  job object). So a kill ends the worker but not its FFmpeg grandchildren; they end on their own
  when their pipes break (decode: the reader is gone; encode: stdin EOF, FFmpeg finishes its
  temporary and exits). The temporary is D85's leftover under WP4.3's journal entry (kept because
  `holds_leftovers` sees it, `app/activity.py:259-271`). Report Limit; the committed test plants
  the fake child + grandchild form.

### The design in my words (with the lines it rests on)

- **Boundary.** `GuardedExports` (`app/activity.py:143-257`) keeps steps 1-6 in the parent: the
  name check (`:204-211`), the journal entry (`:212-222`), the clip lock on the GUI cache's key
  (`:239-247`), the DR-68 release (`:249-250`), the AD-9 line (`:255-256`), the journal removal
  (`:225-227`, `:259-271`). Its `inner(progress)` (`:251`) becomes `ProcessExportJobs`' job.
  The runner's thread (`gui/jobs.py:152-160`, `:209-226`) runs it; `QtProgress.report` keeps
  the latest (`gui/jobs.py:45-55`), so forwarding every child progress line is bounded on the
  interface thread.
- **`ProcessExportJobs.job(request)`** (interface thread): the engine's own malformed-request
  checks (`jobs/export.py:617-626`: `ValueError`), then photo -> `photo_exports.job(request)`;
  video -> a callable. Touches no file, encodes nothing that can fail on a valid request.
- **The video callable** (worker thread): cancelled already -> `CANCELLED` (the constant), no
  spawn; first run -> the bounded stale sweep; create `cache_dir/export/<uuid4 hex>`; encode the
  request line (design item 3 keys; `parameters` = `ParameterSet.to_dict()`, `settings` = the
  object of `Settings.to_json()`; a `ValueError` there (a non-finite value) is a failed result,
  nothing spawned); spawn (design item 8 as amended by R0-STOP-2); write the request line; start
  two daemon reader threads (stdout lines -> a queue; stderr -> a 4 KiB tail deque); loop
  `queue.get(timeout=0.05)` checking `progress.cancelled()` each pass; on cancel write
  `{"cancel": true}\n`, close stdin, and kill after `KILL_AFTER_CANCEL_S` = 3.0. Reader-thread
  form chosen (the job thread never blocks in a read, so the 50 ms poll is exact).
- **Child** (`python -m clearwater.app.export_worker`): fd 1 duplicated for the protocol, then fd
  1 and `sys.stdout` pointed at stderr (a stray print or an inheriting grandchild never reaches
  the channel; today every spawn site sets its stdout: `capability.py:89`, `decode.py:171,
  :335, :350`, `encode.py:886`, `probe.py:128`, `verify.py:225`); read ONE request line from
  `sys.stdin.buffer`, decode (Q5) -> exit 2 with one stderr line on failure; a stdin thread sets
  the cancel flag on `{"cancel": true}` or EOF; install the protocol `logging.Handler` (root at
  WARNING, `clearwater` at INFO, so the engine's INFO outcome line travels); build
  `composition.export_jobs(app_version=..., cache_folder=<scratch>, cache_limit_bytes=...)`
  (`app/composition.py:351-428`, `:412-414`); run the job with the protocol `Progress`; write
  the result line; exit 0. No `cupy` import of its own.
- **The child's analysis runs cold** (design item 7): a COMPLETE GUI cache entry skips the decode
  pass in-process (`analysis/engine.py:11`); WP4.3's window export wall (209.1-210.9 s) was taken
  after the clip's analysis (`s7_driver.py` `analysed()` before `scenario_c_export`), i.e. on a
  cache hit. In the child the decode pass re-runs beside the render (`jobs/export.py:906-916`).
  **RISK to N6's 10 % STOP**, measured only in the window. Should it trip, the remedy candidate
  (CHARC's ruling, it touches `cache/`'s layout) is seeding the scratch folder with a copy of
  the GUI cache's complete entry under the clip lock; not built.
- **Parent strictness and results**: per design item 4, plus: a line is `\n`-terminated ASCII
  JSON (a trailing `\r` tolerated); the FIRST valid result is kept, a later one ignored and
  logged; a result whose fields have the wrong types is an invalid line (ignored, logged), so the
  job then ends as exit-without-result; a valid result followed by a non-zero exit is returned
  (status logged); a child still alive `KILL_AFTER_CANCEL_S` after its result line is killed
  (logged) and the result returned; `JobResult.elapsed_s` is the PARENT's measure (spawn
  included; the child's figure is logged); `outputs` become `Path`s; `failure == "cancelled"`
  returns `export_seam.CANCELLED` itself.
- **Redaction** (crash tail, spawn failure): the exact strings of the known folders (the source's
  folder, the output folder, the scratch folder, the cwd, `sys.prefix`, `sys.base_prefix`, the
  home folder) are replaced first (names with spaces included), then any remaining absolute path
  token (drive or UNC or `/`-rooted) by its last component.
- **Layering**: `jobs/export_process.py` imports the standard library, `clearwater.interfaces`,
  `clearwater.jobs.export_seam` and `clearwater.io.video.pipes` only. The jobs telemetry-name
  guard (`tests/test_jobs_export.py:1430-1444`) reads every `jobs/*.py`: the new module's text
  avoids those names.

### Test list (and the base each fails on)

On base `b6a31b5` both new files fail at import (`ModuleNotFoundError` for
`clearwater.jobs.export_process` / `clearwater.app.export_worker`); per test, the right way:

- `tests/test_jobs_export_process.py` (parallel leg; fake children `sys.executable -c`, each
  under 2 s): progress lines forwarded in order, latest kept; result -> equal `JobResult`;
  `CANCELLED` is the constant; cancel delivered (fake echoes and exits); cancelled before spawn
  -> no spawn, no scratch folder; kill after `KILL_AFTER_CANCEL_S` with the fixed text, scratch
  kept; exit without result (status 1, 2, 0, and a traceback naming a planted absolute path) with
  the tail redacted to names; a non-JSON line, an unknown key, a wrong-typed result, an over-long
  line (> 64 KiB), a non-UTF-8 line: each ignored and logged; two result lines -> the first; a
  result then exit 3 -> the result; a child alive after its result -> killed, result kept; stderr
  flood (1 MiB) does not block; stdin EOF seen by the child's flag; spawn failure (missing
  executable) -> the fixed text, redacted; scratch folder created before spawn and removed after
  the result; the stale sweep (an old folder removed, a fresh one kept, logged, once per
  instance); photo requests delegated without a spawn; `job()` touches no file and raises
  `ValueError` for a malformed request; the child's log records re-logged under
  `clearwater.app.export_worker` at their level; the kill leaves a grandchild (Q11 shown; the
  test ends the grandchild itself).
- `tests/test_app_export_worker.py` (`slow`; one `gpu` form): the real worker on
  `hevc8-bt709-full.mp4` with `force_cpu`: `ok`, one output, provenance present, scratch gone;
  cancel at the first progress line: no output, no temporary, `CANCELLED`; a malformed request:
  exit 2, one stderr line, nothing on stdout; Q9's identity (decoded framemd5, every frame);
  `python -m clearwater.app.export_worker` imports no PySide6.
- Edited: `tests/test_app_deps.py` `APP_MODULES` + `export_worker.py` (fails on base: the
  list); `tests/test_io_video_spawn.py:235` 7 -> 8 (fails on base: the count).
- If R0-STOP-1 is granted: the three edits named there; on base they pass, and on the wired
  head unedited they fail as reproduced.

### Other notes for CHARC (no stop)

- `app/activity.py:147`'s docstring ("`composition.export_jobs(cache=...)`") goes stale (not
  owned; flagged). May `app/composition.py`'s MODULE docstring gain one sentence naming the new
  builder (the brief says "nothing else")? Recommended: yes.
- Serial-leg cost: every GUI test that exports a VIDEO now spawns a worker (about 1-2 s more
  each, on the video items of the export and batch triggers in `tests/test_app_*.py`).
- The GUI cache's size accounting does not see `export/<uuid>` (its folder grows by up to one
  clip's proxies during an export, then is removed): a report Limit.

## Y1 (cell 2, implementer-opus-high): tasks 3-4, the parent side

Cell 1 retired at round 0, depth 194,313 (dispatcher's figure). Cell 2 dispatched fresh on CHARC's
ruling `a265489d371695e2` (STOP-1 granted with its exact scope, STOP-2 no environment change, Q2
as proposed, grants (b) and (c)). Cell 2 depth at Y1: 171,586 (dispatcher, 05:08Z).

### Commits

- `61ceef55` test(wp4.6): RED. `tests/test_jobs_export_process.py` (new) and the spawn pin
  `tests/test_io_video_spawn.py:235` 7 -> 8, "the eight ruled product spawn sites" (R0-STOP-2's
  owned line). RED lines: `ImportError: cannot import name 'export_process' from
  'clearwater.jobs'`; `AssertionError: expected the eight ruled product spawn sites, found 7`.
- `baffd2d2` feat(wp4.6): `src/clearwater/jobs/export_process.py` (`ProcessExportJobs`), plus two
  verification-loop tests and the formatter's pass over the test file.
- `8f5dadc1` test(wp4.6): the redaction sibling-prefix regression test.

Green (targeted, the worktree): `tests/test_jobs_export_process.py` + `tests/test_io_video_spawn.py`
+ the jobs import/telemetry guard: `316 passed in 11.56s`; the file alone `52 passed in 9.22s`
(slowest call 1.02 s, the Q11 grandchild test). `ruff check`: All checks passed; `ruff format
--check`: already formatted; `mypy src/clearwater/jobs/export_process.py`: no issues. No full
suite, no window, no footage, no GPU.

### Built as ruled, and the choices the ruling left to the cell (stated, for review)

- Constructor `ProcessExportJobs(*, photo_exports, cache_dir, app_version, command)`; `command`
  is REQUIRED here (the builder in `app/composition.py` supplies the product default at Y2, so
  `jobs` never names an `app` module in code); an empty command is `ValueError`.
- Spawn: `subprocess.Popen(list(command), stdin=PIPE, stdout=PIPE, stderr=PIPE,
  **tool_spawn_kwargs())`, no `env=` (R0-STOP-2). Request: one ASCII line, `json.dumps(...,
  ensure_ascii=True, allow_nan=False)`, `source` = `request.source.absolute()`, `settings` = the
  object of `Settings.to_json()`, `cache_limit_bytes` = the request's settings' (Q2).
- `device`: `"none"` when no worker ran (cancel before the start, encode failure, start
  failure: the engine's own pre-start value, `jobs/export.py:186`); `"unknown"` when a worker ran
  and gave no result (exit without a result, a kill), design item 6.
- ONE failure text beyond Q10's three: `ENCODE_TEXT` "The export request could not be encoded:
  <error>" (a non-finite parameter or a non-JSON value; nothing spawned, nothing made), the
  round-0 note's "failed result, nothing spawned" given a fixed form. A scratch-folder `mkdir`
  failure uses Q10's start text.
- I/O on three daemon threads: a stdin WRITER (queue-fed; `None` closes), the stdout line
  reader, the stderr tail drain; the job thread only waits on the line queue for `POLL_S` = 0.05
  s. Each stream is closed only by the thread that reads or writes it. After the worker's exit
  the job reads until the end of the output, or until the output has been quiet
  `DRAIN_AFTER_EXIT_S` = 1.0 s (the timer restarts at each line, so a lagging reader never loses
  the result line, and a grandchild holding the output cannot hold the job).
- The kill grace `KILL_AFTER_CANCEL_S` = 3.0 s runs from the cancel line, or from the result
  line (design item 4 / round-0 note). The scratch folder is KEPT on ANY kill (a grandchild may
  still hold a file in it) and removed otherwise; a later instance's first-job sweep removes it
  after `STALE_AFTER_S` = 3600 s.
- Line strictness: content over `MAX_LINE_BYTES` (65,536, without the `\n`; one `\r` tolerated)
  ignored and its remainder skipped; an unterminated last line ignored; non-UTF-8, non-JSON,
  `NaN`/`Infinity` and numbers that overflow to infinity, a non-object, not exactly one key, an
  unknown key, wrong shapes or types (including a `bool` for an int, an unknown log level, a
  result missing or adding a field) ignored. Each is logged at WARNING by its REASON only
  ("export worker line ignored: ..."), never its content.
- Redaction (the crash tail and the start and encode texts): known folders first, matched
  exactly and case-insensitively in three spellings (native, repr-doubled backslashes, forward
  slashes) and only where the folder's name ENDS (a lookahead); the folder plus its following
  components becomes the last component. Then any remaining absolute path (a drive, a UNC root,
  or a `/` root not after a word character) likewise. A component may contain spaces; it ends at
  a separator, a quote or a line end. Known folders: the source's folder, the output folder, the
  scratch folder, the cache folder, the interpreter's folder, `sys.prefix`, `sys.base_prefix`,
  the cwd, the home folder. The tail keeps the last 4,096 bytes, drops a cut first line, redacts,
  escapes non-ASCII, and keeps the last 4,096 characters.

### Verification loop (Y1)

| # | Suspected | Confirmed how | Outcome |
|---|---|---|---|
| 1 | The request write could block the job thread (a worker that never reads, a request over the pipe buffer), so a cancel could never be checked | `test_a_worker_that_never_reads_its_stdin_is_still_cancelled` on the first form: 30.1 s, `assert (... - ...) < 10` failed | FIXED: the stdin writer thread (`baffd2d2`) |
| 2 | An exception escaping the loop (a `progress.report` that raises) left the worker running | `test_an_exception_from_the_progress_kills_the_worker` on the first form: the worker's heartbeat went on (`'11' == '3'`) | FIXED: the loop kills and reaps the worker before re-raising (`baffd2d2`) |
| 3 | A fixed 1 s window after the exit could drop the result line if the reader lags under load | By reading (not reproduced: needs a starved reader thread) | FIXED: the quiet timer restarts at every line (`baffd2d2`) |
| 4 | A known folder matched as a PREFIX of a sibling (`my clips` in `my clips2`) leaked the sibling's name | The extended redaction test with the lookahead removed: `assert 'my clips' not in ...` failed | FIXED (code `baffd2d2`, test `8f5dadc1`) |
| 5 | Closing a pipe from the job thread while a reader is blocked in it can deadlock on Windows | Design review | REJECTED for this code: every stream is closed only by the thread using it |

Product fixes 4, test-only 0, reverts 0 (all before the first green commit, except #4's test).

### Q11 (shown by the committed test)

`test_a_kill_leaves_the_grandchild_running` passes on this machine: after `Popen.kill` of the
fake worker (the venv launcher `sys.executable`, which takes its interpreter with it), a
grandchild the worker started keeps beating its file; the test then ends it through a `stop`
file. Note on cell 1's probe `r0\q11_grandchild.py`: its `alive()` used `os.kill(pid, 0)`, which
on Windows TERMINATES the process (`TerminateProcess` with exit code 0) rather than testing it;
its "alive" verdict still held (the call succeeded, so the process existed at that moment), but
the probe itself ended the grandchild. The committed test uses a heartbeat file instead.

### Open for Y2 / the window (no stop)

- A real GPU worker's teardown after its result line (interpreter exit, a CUDA context) longer
  than `KILL_AFTER_CANCEL_S` = 3.0 s would be killed: the result is still returned, the scratch
  folder is kept until a later instance's sweep. Measure the result-to-exit time in the window
  beside Q8's spawn figures; a figure near 3 s comes to CHARC.
- The worker's log records are re-logged as `"<child logger name>: <message>"` under
  `clearwater.app.export_worker`, so the engine's INFO outcome line reaches the parent's log once,
  in that form.

## Y2a (cell 2): tasks 5-6, the worker

Dispatched after Y1 was accepted, with depth 171,586 at the Y1 yield (05:08Z). Y2 was SPLIT for
depth: Y2a covers tasks 5-6 plus the `APP_MODULES` line; Y2b is listed below. Cell 2 depth at
Y2a: (dispatcher fills).

### Commits

- `214d2624` test(wp4.6): RED. Adds `tests/test_app_export_worker.py` (new; module-level `slow`
  with the brief's reason, plus `usefixtures("ffmpeg_tools")`) and `tests/test_app_deps.py`
  (`APP_MODULES` gains `"export_worker.py"`; its docstring now says "WP4.1's two, WP4.3's four
  and WP4.6's worker"). The Y1 depth is also filled in this ledger. RED lines: the worker
  tests fail with `No module named clearwater.app.export_worker` (the malformed cases on
  `assert 1 == 2`; the process-jobs cases on "The export worker ended without a result (exit
  status 1)", whose tail is already redacted to `python.exe: No module named ...`); the deps
  test fails on the module list. `15 failed, 5 passed`.
- `5c060d44` feat(wp4.6): `src/clearwater/app/export_worker.py`. Two test changes ride with
  it: the no-Qt probe now pops its own argument (`main` refuses arguments), and a new
  level-mapping test, which failed for levels 5, 25 and 60 before the fix (see the loop below).
- (this commit) test(wp4.6): the Q9 test prints the two file md5s (recorded, not asserted), plus
  this entry.

Green (targeted, in the worktree, CPU fixture only): `tests/test_app_export_worker.py` +
`tests/test_app_deps.py` gave `25 passed in 43.55s`. Adding the Y1 files
(`test_jobs_export_process.py`, `test_io_video_spawn.py`) gave `340 passed in 54.72s` (run
before the md5 print was added). Slowest calls: Q9 16.9 s (two exports), the ok export 8.5 s,
no-Qt 7.4 s, cancel 1.5 s, each malformed case under 1 s. `ruff check` passed on all touched
files; `ruff format --check` reported them already formatted; `mypy
src/clearwater/app/export_worker.py src/clearwater/jobs/export_process.py` found no issues. No
GPU, no footage, no window, no full suite.

Q9 of record (`clearwater-review-evidence\wp4.6\y2a\q9_identity.log`): `45 decoded frames equal;
file md5 in-process 56a7d4676fa1c7774df0e3d11639c9bb, worker 1df16348f1ba1d5ce432590ff1f3baf7`.
The decoded frames are identical and the files differ, as the round-0 probe found.

### The worker as built (`src/clearwater/app/export_worker.py`)

- Public surface: `main(argv=None) -> int`; `run(stdin, protocol, *, cancel=None,
  sink_for=None) -> int`; `decode_request(line) -> WorkerRequest`; `RequestError(ValueError)`;
  `EXIT_OK` 0, `EXIT_BAD_REQUEST` 2, `LOG_MESSAGE_CHARS` 8192.
- `main` refuses any argument (exit 2, one stderr line). It then takes over stdout: it dups fd
  1 as the binary protocol stream, `dup2`s stderr onto fd 1, sets `sys.stdout = sys.stderr`, and
  calls `run(sys.stdin.buffer, protocol)`.
- `run`:
  1. Decodes the first stdin line. A failure writes one line `export worker: <reason>` to stderr
     and returns 2; nothing goes to the protocol and no file is touched.
  2. Starts the stdin watcher, which sets the cancel flag on `{"cancel": true}` or at EOF and
     ignores other lines.
  3. Installs the protocol log handler on the root logger (root at WARNING, `clearwater` at
     INFO; both restored in a `finally`).
  4. Builds `composition.export_jobs(app_version=..., cache_folder=<scratch>,
     cache_limit_bytes=<request>, [sink_for=...])`, runs the job, sends the result line, and
     returns 0.
  5. An exception that escapes the engine propagates (a traceback on stderr, exit 1), so the
     parent reports an exit without a result, with the redacted tail.
- **For the Y2b hold worker:** `run(..., cancel=<its own Event>, sink_for=<a wrapper over
  composition.video_sink>)`. Its sink can wait on "`release` marker exists or
  `cancel.is_set()`". `run` uses the caller's Event as the stdin watcher's flag.
- `decode_request` requires:
  - exactly the eight keys and `format_version` 1 (not a bool);
  - `source`, `cache_folder` and `app_version` as non-empty strings;
  - `kind` "video" or "photo" (the engine's own kinds; the parent sends only "video");
  - `cache_limit_bytes` as an int >= 0 (not a bool);
  - `parameters` decoded by `ParameterSet.from_dict` and `settings` by
    `Settings.from_json(json.dumps(obj))` (Q5; no migration or repair).
- Protocol lines are sent whole under a lock as `json.dumps(ensure_ascii=True,
  allow_nan=False)` + `\n`, flushed per line. A write that fails (the parent is gone) sets the
  cancel flag instead of raising.
- Log lines carry the message only (`record.getMessage()`, cut to 8,192 characters; no exception
  text, so no path travels). The level becomes the standard one at or below the record's.

### Verification loop (Y2a)

| # | Suspected | Confirmed how | Outcome |
|---|---|---|---|
| 1 | After the takeover, a stray print, a raw fd-1 write or a grandchild started WITHOUT a stdout argument could reach the protocol | Probe `clearwater-review-evidence\wp4.6\y2a\stray_probe.py` (+ `.log`) on win32: `MARK-print`, `MARK-fd1` and `MARK-grandchild` all reached stderr; only `MARK-protocol` reached the protocol | REJECTED: the takeover covers all three on this machine (the UCRT `dup2` also moves the standard handle a grandchild inherits) |
| 2 | A record at a custom level (e.g. 25) travels as `Level 25`, which the parent ignores as an unknown level | `test_a_log_record_carries_a_level_the_parent_accepts` failed for 5, 25 and 60 before the fix | FIXED (`5c060d44`): the standard level at or below the record's |
| 3 | `python -m` with an argument (the no-Qt probe's `runpy` path) | The probe test failed by design once `main` refused arguments | Test changed (the probe pops its argument), product kept strict |
| 4 | An engine exception escaping the job leaves no result | By reading: the traceback goes to stderr and the parent's exit-without-result path redacts it (Y1 tests) | Accepted as designed: no product change |

Product fixes 1, test-only 1, reverts 0.

### Y2b: what remains (for this cell or a fresh one; nothing below is started)

1. **Builder** `composition.process_export_jobs(*, photo_exports, cache_dir, app_version=
   clearwater.__version__, command=None) -> ExportJobs` in `src/clearwater/app/composition.py`
   (Q2 as ruled: no `cache_limit_bytes`). `command` None = `[sys.executable, "-m",
   "clearwater.app.export_worker"]`. It returns `ProcessExportJobs(...)`. Grant (c): ONE sentence
   in composition's module docstring naming the builder; nothing else in that file.
2. **Wiring** `src/clearwater/app/main.py:282` (inside `:281-287`): the first argument of
   `GuardedExports(...)` becomes `composition.process_export_jobs(photo_exports=composition.
   export_jobs(cache=cache), cache_dir=locations.cache_dir)`, where `locations` is
   `build_application`'s parameter (`:244`). Nothing else in `main.py`.
3. **Docstrings:**
   - `src/clearwater/io/video/pipes.py`: the module and helper docstrings say "every product
     FFmpeg, ffprobe AND Python worker launch" (no code change).
   - `src/clearwater/app/__init__.py`: name the new module.
   - Grant (b): the one sentence at `src/clearwater/app/activity.py:147` names the process form.
4. **The three granted test edits (R0-STOP-1, the EXACT scope):**
   - (i) NEW `tests/export_worker_hold.py`: a worker command for tests that calls
     `export_worker.run` with its own cancel Event and a `sink_for` wrapper. The sink's first
     `write` creates `writing` in a folder named by an environment variable, waits for `release`
     or the cancel, then writes `returned`.
   - (ii) Scenario (e) in `tests/test_app_v7.py:302-304, :322, :347`: the hold is set through the
     process form's command and the marker folder. The witness `k1_renders_during_a_sink_write`
     keeps its name and meaning.
   - (ii) The `export` branch of `tests/test_app_wiring.py:749-760` (dr44c), same hook.
   - (ii) `tests/test_app_startup.py:212-213`: the process form's type; its PHOTO leg is an
     `ExportEngine` whose `_cache is application.cache`. The Q16 rule now reads "one GUI cache
     per process, shared by the GUI and the photo export leg; the video worker has its per-job
     scratch", and the report says so.
   - The hold command needs a way in: `ProcessExportJobs`' `command` is set at construction, so
     the test reaches it through the builder's `command=` or by replacing the instance's command.
     **CHECK before building:** how the scenario/dr44c tests build the application (do they call
     `build_application` with injectable engines?). If the hold cannot be set without a
     `main.py` or `composition` change beyond items 1-2, that is a STOP.
5. **Driver copy (iii):** a WP4.6 copy of `clearwater-review-evidence\wp4.3\windows\s7_driver.py`
   (pinned md5 `0b9ee6cc3ebd2cf07c35dec934cfd901`). Its modes `v7e` and `dr44c-export`
   (`s7_driver.py:979-989` swaps `exports._engine._sink_for`) use the same hook. `v7c` and `v7d`
   run on the pinned driver unchanged. Its md5 is recorded at the window.
6. **Task 8, the verification loop:** over the whole diff, then the targeted tests and markers
   (the app tests touched by the wiring run serial-leg-sized; the dispatcher names which), ruff,
   format, mypy.
7. **Open for the window and the report (carried):**
   - teardown versus `KILL_AFTER_CANCEL_S` after the result;
   - the re-logged form `"<logger>: <message>"`;
   - the cold analysis in the child versus N6's 10 % (ruling (a));
   - (e) of the ruling: the GUI cache's accounting does not see `export/<uuid>`;
   - (d) of the ruling: the serial-leg cost per GUI video-export test.
8. **Unbuilt by choice:** the `gpu` form of the worker test. The brief makes it optional and
   this dispatch said nothing on the GPU, so it is offered for the window, not built.
