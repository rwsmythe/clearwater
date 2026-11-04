# WP-DR125: worker stdin isolation and shutdown

Status: cell implementation and records complete. Reviewer A, Reviewer B, the
seat frozen check and the final gate remain with the dispatcher. This report
does not itself close DR-125.

## Design as built

Product build: `6ef67a19`. Turn-6 checkout: `fd798923`, after the ruling merge.
Before-record base: `73453bdc`. Turns 4, 5 and 6 change no product file.

- `src/clearwater/app/export_worker.py:95`, `_RawStdinReader`: one remainder
  assembler uses `os.read(fd, 65536)` for request and cancel lines. No IO object
  wraps the private descriptor.
- `export_worker.py:138`, `_isolate_stdin`: duplicate descriptor 0, open the null
  device, replace descriptor 0 and close the extra null descriptor. The private
  duplicate is non-inheritable. `sys.stdin` keeps its original object.
- `export_worker.py:167`: the statement-form Win32 guard updates
  `STD_INPUT_HANDLE` with `SetStdHandle`. This is the moved N1 site.
- `export_worker.py:405`, `main`: isolate stdin after the argument check, before
  protocol takeover and the first request read. Isolation failure produces one
  stderr line and status 2; opened descriptors are cleaned up.
- `export_worker.py:320`, `_watch_stdin`: cancel on the cancel line, EOF or read
  error. `run` at line 349 accepts binary test streams and the narrow reader.
- `export_worker.py:431`: close the protocol after serving the request. Do not
  close the watcher's descriptor or join its daemon thread. Normal interpreter
  shutdown remains; `os._exit` is not used.
- `src/clearwater/__main__.py:301`: the frozen worker branch activates the GPU
  loader, imports the worker and calls it. The entry shim is deleted.
- `tools/package/README.md:120`: worker-side isolation replaces the temporary
  shim description. `gpu_pack.py` has the authorized docstring-only correction.
- `tests/test_app_export_worker.py:254`: the windowed-interpreter test starts
  `pythonw.exe` with a pipe on fd 0 and checks the Win32 input slot against the
  CRT handle after isolation. It also checks that the slot changed from the
  original pipe handle. It reports through a file, with Qt blocked, a disposable
  profile, a bounded wait and process cleanup. It skips if pythonw is absent.

A non-`OSError` from `_isolate_stdin()` escapes `main` as an uncaught traceback
before any request read or job, so it is fail-closed in effect (r1 ruling a6).

## Rulings

Round 0: R1 permits eager imports that spawn nothing, before isolation. Request
reads, probes, jobs and CuPy imports follow isolation. The zero-spawn witness
stays unchanged. The restricted-token WMI fallback is a sandbox residual.
R2 grants the named frozen-entry test edits. R3 gives absent descriptor 0 the
existing empty-request refusal: status 2, no watcher. The authorized docstring
corrections and per-test legacy slow markers are present. Darwin acceptance
means no new Darwin error, per CHARC's ruling carried by dispatch 4.

Turn-4 ruling, brief section "Turn-4 ruling", CHARC gen 16:

1. Remove buffered mode from the suite; do not skip or xfail it. Keep its
   archived sandbox observation as evidence. The raw stand-in remains in the
   parallel leg, with five runs, exit 0 and no `Fatal Python error` on stderr.
2. Run the two base records only in the sandbox, with 10 s child and 15 s worker
   bounds and kill-and-wait. Crash-report suppression is permitted and disclosed.
3. Run candidate records in the sandbox. The seat repeats the after series at
   the gate.
4. Later seat reviews must not execute the buffered before shape. Any crash
   dialog is left to the owner; no synthetic desktop input is permitted.
5. Explain WER and the two failure endings in the limits below.

## Mechanistic witness and S-1

S-1: MAJOR, confirmed, test-only. The original private `io.open` reader was not
the standard-stream crash shape. Turn 4 changed it to
`sys.stdin.buffer.readline()` and reproduced the fatal standard-buffer lock.
The process printed `result`, emitted `_enter_buffered_busy` on `<stdin>` and
remained alive at the 10 s bound. It was killed and reaped. Its forced status
1 is not counted as a natural crash status.

The durable witness is:
`C:/Users/rwsmy/clearwater-review-evidence/wp-dr125/cell/t4-standin/`.
It contains `standin-diagnostic.log`, `standin-diagnostic.record.txt`,
`standin_diagnostic.py` and `standin-diagnostic/{stdout,stderr}.log`.
The archived `short-4.log`, `modules-4.log` and `series-4-summary.log` preserve
the failed gate attempt and the passing raw/candidate observations.

Turn 5 removes buffered mode and its parametrization entirely. The remaining
`test_shutdown_with_a_blocked_daemon_reader` checks the raw shape five times.
Its raw-reader loop, bounded waits, result assertion and daemon setup remain.
It now asserts both status 0 and stderr free of `Fatal Python error`.
No seat execution of the buffered shape was requested or performed by this cell.

Reviewer A r1's recorded seat claim-1 probe observed:

| Seat stand-in mode | Outcome |
|---|---|
| `sys.stdin.buffer.readline()` daemon | 10/10 `0xC0000005`, `_enter_buffered_busy <stdin>`, no hang |
| Raw `os.read(os.dup(0))`, fd 0 NUL, `SetStdHandle` | 10/10 exit 0 |
| Private `io.open(os.dup(0), 'rb').readline()` daemon | 10/10 exit 0 |
| No thread | 10/10 exit 0 |

Source: `C:/Users/rwsmy/clearwater-review-evidence/wp-dr125/A/r1/review.txt`,
claim 1. No crash dialog was seen at that seat. This report carries the seat's
natural exits and the unsuppressed sandbox hang as separate observations. The
turn-4 ruling stands; this cell has not rerun the buffered shape in turn 6.

Regression guards for a BufferedReader swapped back into the worker are
`test_a_worker_child_inherits_null_instead_of_the_request_pipe`,
`test_twenty_workers_exit_zero_after_their_result_with_stdin_held_open` and
`test_private_reader_has_no_io_buffer_or_instance_readline`. The structural
test checks the exact reader class, forbids an instance `readline` override,
and rejects `io.BufferedIOBase` or `io.RawIOBase` attributes. It catches the
private-buffer shell mutant that a private-buffer shutdown series alone missed.

## Matched before/after records

All four records ran once in the Codex sandbox. None was refused. The same
driver, planted CPU stub job, request and bootstrap serve both source roots.
No actual footage is read by the stub. Stdin stays open through worker exit.

| Revision | Case | Result | Fatal stderr | Worker kills at bound |
|---|---|---|---|---|
| `73453bdc` | inherited child | Child timed out at 10 s, killed and reaped; worker exit 3221225477 | 1/1 | 0 |
| `73453bdc` | 20 worker exits | 20 successful result lines; 20 exits 3221225477; 0 exits 0 | 20/20 | 0 |
| Candidate | inherited child | Child printed `0`, child and worker exit 0 | 0/1 | 0 |
| Candidate | 20 worker exits | 20 successful result lines; 20 exits 0; empty stderr | 0/20 | 0 |

3221225477 is `0xC0000005`. All workers and all spawned inheritance-test
children were reaped. The base inheritance job returned a failed result with
`child timeout`; the base exit-series jobs returned successful results before
their fatal shutdown. The candidate inheritance child had empty stderr.

The form used for ALL four records was crash-report suppression in the driver
parent before any worker spawn:
`msvcrt.SetErrorMode(SEM_NOGPFAULTERRORBOX | SEM_FAILCRITICALERRORS)`.
The mode was inherited by children. This is the permitted CPython
`test.support.SuppressCrashReport` form. The prior mode, returned as 32769,
is recorded in each summary. The figures above are natural exit statuses under
that form, not the turn-4 kill-at-bound form.

Logs: `work/wp-dr125/{before,after}-{child,exits}.log`.
Each adjacent `.record.txt` records the exact command, revision, source hash,
resolved worker path, suppression form, isolation pre-read and result summary.
Per-run protocol/stderr files are under the matching `*-runs/run-NN/` folders.
Runner summaries are `work/wp-dr125/{before,after}-{child,exits}-runner.log`.
The seat archived the turn-5 records under
`C:/Users/rwsmy/clearwater-review-evidence/wp-dr125/cell/t5-records/`.

Before EACH run, `run_record.py` ran and quoted this pre-read in its record:

`rg -n "clearwater\.__main__|export_worker|run_module|APPDATA|LOCALAPPDATA|XDG_|PySide6|shiboken6|timeout" work/wp-dr125/records.py`

The six profile variables are redirected before spawning. The GUI blocker
precedes the worker import and blocks PySide6, shiboken6 and the GUI route.
Each child inserts its selected `src` first and records `worker.__file__`.
The base resolved under `work/wp-dr125/base/src/clearwater/app/`; the candidate
resolved under `src/clearwater/app/`. The base snapshot came from read-only
`git archive 73453bdc src`. It matches the git object after CRLF normalization;
the archive's CRLF conversion is recorded in the before runner logs.
Both timeout paths kill and wait. The inherited child has a 10 s bound; the
worker has a 15 s bound. No GPU pack is activated.

## Frozen-entry test transfer

These entry-shim tests were deleted; their worker-side replacements follow:

| Deleted test in `test_frozen_entry.py` | Replacement in `test_app_export_worker.py` |
|---|---|
| `test_a_child_of_the_frozen_worker_branch_inherits_nul_not_the_request_pipe` | `test_a_worker_child_inherits_null_instead_of_the_request_pipe` |
| `test_the_frozen_worker_reads_its_request_and_the_cancel_line_through_the_private_fd` | `test_cancel_and_eof_reach_the_private_reader_and_remove_the_partial[cancel]` |
| `test_the_end_of_the_request_pipe_reaches_the_workers_reader_through_the_shim` | `test_cancel_and_eof_reach_the_private_reader_and_remove_the_partial[eof]` |
| `test_a_failed_stdin_isolation_ends_the_frozen_worker_before_anything_else` | `test_isolation_fails_closed_without_leaking_descriptors` |

Worker refusal now precedes protocol takeover, not loader activation.
`test_the_frozen_worker_flag_runs_the_shim_the_loader_then_the_worker_without_qt`
became `test_the_frozen_worker_flag_runs_the_loader_then_the_worker_without_qt`.
`test_the_frozen_worker_flag_alone_passes_no_arguments` became
`test_the_frozen_worker_flag_runs_the_loader_then_the_worker_with_no_arguments`.
The source-to-GUI assertion is retained. `_stub_shim` and its callers are gone.
Evidence: `git diff 73453bdc 6ef67a19 -- tests/test_frozen_entry.py`.

Under the widened r1 ownership, turn 6 also deletes
`_SPAWN_BEFORE_THE_PROBE`, `_within`, `_CANCEL_THROUGH_THE_SHIM`,
`_EOF_THROUGH_THE_SHIM`, `_PARENT_THAT_DIES`, `_SHIM_FAILURE` (all modes), and
`test_a_process_without_a_standard_input_runs_the_worker_branch_on`.
The worker-side missing-stdin test retains EBADF coverage. All seven deleted
names have zero remaining references in the frozen-entry test, as checked by
`rg -n` and the AST audit: `work/wp-dr125/deleted-name-search-6.log` and
`work/wp-dr125/audit-6.log`. The retained `_NO_GUI_PRELUDE` was not named in
the deletion grant. The module, section comment and source-to-GUI docstring
now describe the tested behavior. Unused imports were removed as a consequence.

## Reviewer A r1 adjudication

Review source: `C:/Users/rwsmy/clearwater-review-evidence/wp-dr125/A/r1/review.txt`.
It reviewed `6ef67a19` and returned NEW_CRITICAL_MAJOR_FOUND. Product code met
the contract. The brief's r1 ruling grants these test/doc-only fixes.

| Finding | Disposition and evidence |
|---|---|
| M1 MAJOR, in envelope, REASONED | Confirmed: `/proc/self/fd` is not portable to macOS. POSIX count now uses `psutil.Process().num_fds()`. No Mac execution is claimed. |
| M2 MAJOR, in envelope, EXECUTED | Confirmed: console CRT behavior masks a missing/wrong Win32 slot update. New pythonw witness passes on the candidate and fails both slot mutants. |
| m3 MINOR, in envelope, EXECUTED | Confirmed: add a one-write request-plus-cancel witness. It passes on the candidate and fails guarded pre-read. |
| m4 MINOR, in envelope, EXECUTED | Confirmed: add exact-type and no-buffer/no-instance-method assertions. The buffered-shell mutant fails. |
| m5 MINOR, in envelope, EXECUTED | Confirmed: remove the authorized dead helpers and vacuous shim test; correct stale text. |
| a6 ADVISORY, REASONED | No code change (ruling a6, concur): fail-closed in effect; the request-read OSError behaviour predates this package. |
| a7 ADVISORY, in envelope | Fixed: README stdin paragraph wrapped to the surrounding width. |
| a8 ADVISORY, in envelope | Resolved by the report added in turn 5, after the reviewed head. |
| a9 ADVISORY, EXECUTED | No defect established; no change. The process-global os.read monkeypatch is restored by pytest. The reviewer observed a clean parallel run. |

Four mutation runs used disposable `src` copies, with the existing isolated
child bootstrap, bounded waits and cleanup. No product checkout was edited.

| Mutant | Dedicated witness | Result |
|---|---|---|
| M2: SetStdHandle slot -11 | `test_windowed_worker_updates_the_win32_stdin_slot` | Failed: Win32 slot differs from CRT fd 0 |
| M2: SetStdHandle call removed | Same | Failed: Win32 slot differs from CRT fd 0 |
| m3: guarded buffered request pre-read, request retained in raw remainder | `test_a_coalesced_request_and_cancel_reach_the_private_reader` | Failed: no complete protocol result within the bound |
| m4: BufferedReader.readline stored in the raw-reader shell | `test_private_reader_has_no_io_buffer_or_instance_readline` | Failed: instance readline override |

Each mutation returned pytest status 1 with one failed dedicated test. The
candidate's same three tests passed together. Logs:
`work/wp-dr125/new-6.log`, `work/wp-dr125/mutations-6.log`, and
`work/wp-dr125/mutations-6/<mutant>/{pytest.log,record.txt}`.

The cumulative round row, also staged in `work/wp-dr125/review-ledger.md` for
the dispatcher's after-B ledger commit, is:

| Round | Counts | Envelope | NEW / REOPENED | Reverts | Fix surface | Transport / depth |
|---|---|---|---|---|---|---|
| A r1 | 0 critical, 2 major, 3 minor, 4 advisory | All 5 formal findings in; a6 no change (ruling: fail-closed in effect); 3 other advisories in | 9 / 0 | 0 | Tests and docs only; 0 product changes | Seat Claude process, read-only; CLI version and depth dispatcher-supplied, not available to cell |

All r1 findings are dispositioned. This fold-in does not claim convergence;
the next independent reviewer pass remains with the dispatcher.

Reviewer A r2 / Reviewer B: A r2 returned NO_NEW_CRITICAL_MAJOR with three
advisories, all folded in turn 7: remove the dead prelude, collect windowed
stderr before checking status, and correct the a6 wording. Reviewer B returned
NO_NEW_CRITICAL_MAJOR; its MINOR exit-comment finding is folded in turn 7.
The comment now names the Windows close-under-pending-read hang. No product
code changed. B's remaining advisory list is being re-collected at the seat.

## Validation and collection

| Turn-6 check | Result | Log under `work/wp-dr125/` |
|---|---|---|
| `uv run --no-sync ruff check .` | Passed | `ruff-6.log` |
| `uv run --no-sync ruff format --check .` | 323 files already formatted | `format-6.log` |
| `uv run --no-sync mypy` | Clean, 161 source files | `mypy-6.log` |
| Darwin-target mypy on worker and entry | Clean, 2 source files | `mypy-darwin-6.log` |
| Three new dedicated witnesses | 3 passed, 42 deselected | `new-6.log` |
| All three requested modules, R1 deselected | 284 passed, 1 deselected; no skips | `modules-6.log` |
| Parallel collection | 21/45 nodes | `collect-parallel-6.log` |
| Serial collection | 24/45 nodes | `collect-serial-6.log` |

Execution used `PYTHONPATH=scripts`, `-p sandbox_mkdir_shim`,
`-p no:cacheprovider`, `--timeout 300` and `--basetemp=work/cdr-6`:

`uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_app_export_worker.py tests/test_frozen_entry.py tests/test_jobs_export_process.py --deselect tests/test_app_export_worker.py::test_eager_imports_and_isolation_spawn_nothing_and_import_no_cupy --basetemp=work/cdr-6`

The exact Darwin command was:
`uv run --no-sync mypy --platform darwin src/clearwater/app/export_worker.py src/clearwater/__main__.py`.
The windowed test ran successfully in the sandbox; no seat fallback is needed
for that test. macOS execution remains WP6.4's work.

The final three-module raw stand-in record shows five exits 0 with empty
stderr. Its worker series shows 20 successful results and 20 exits 0 with
empty stderr. Evidence: `work/wp-dr125/series-6-summary.log`.
All 23 pre-existing worker nodes and the 20-run slow series remain serial.
The new pythonw, coalesced-cancel and structural witnesses are parallel nodes.

R1 remains unchanged and deselected in the sandbox. The stdlib WMI fallback
caused its sandbox failure: `work/wp-dr125/import.log`. The dispatcher reports
the unchanged witness passed once at the seat. This handoff is recorded in
`C:/Users/rwsmy/clearwater-review-evidence/wp-dr125/cell/return-3.md` and
dispatch 4's carried ruling; the original seat runner log was not supplied.

`rg -n isolate_worker_stdin src tests tools docs` finds only historical
decision/report/proof records and briefs. It has no matches in `src`, `tests`
or `tools`. Evidence: `work/wp-dr125/shim-search-5.log` and
`work/wp-dr125/shim-search-summary-5.log`. The old AD-34 text remains for the
architect's accept-time amendment.

## Verification loop

S-1 was confirmed against the original source. The corrected turn-4 shape
independently reproduced the standard-buffer lock. Ruling 1 then removed
buffered mode from the suite instead of suppressing its failure.
The final raw test still waits with stdin open through process exit.

The records independently discriminate the old and new product: old children
inherit the blocked pipe and old workers abort after their result; candidate
children read EOF and candidate workers exit 0. Record audit checked source
paths, result counts, natural statuses, fatal messages, suppression mode,
profile/GUI isolation and reaping. The initial base byte comparison detected
archive CRLF conversion; LF-normalized comparison confirmed the requested
revision before any old-worker execution. No product workaround was added.

Final footprint and ASCII/LF checks are in `work/wp-dr125/footprint-5.log`;
diff whitespace checking is in `work/wp-dr125/diff-check-5.log`.
Turn-6 final footprint, preserved-AST and evidence audits are in
`work/wp-dr125/footprint-6.log` and `work/wp-dr125/audit-6.log`; whitespace
checking is in `work/wp-dr125/diff-check-6.log`. The final verification pass
found no further in-scope issue. Reviewer A r1 is dispositioned above;
convergence and Reviewer B remain separate seat work.

## Limits

The buffered before shape is evidence rather than a gate test because its
fatal abort enters Windows Error Reporting and can wait for a crash dialog.
The frozen `0xC0000005` and source `_enter_buffered_busy` abort are one
buffered-reader lock with two ends, as ruled by CHARC.

The unsuppressed turn-4 record shows the fatal message plus a kill at the
bound; it does not supply a natural crash status. CHARC rules that hang
sandbox-specific; the prior Reviewer A seat probe exited without hanging.
The suppressed base records show natural `0xC0000005` exits after the same
fatal message. The raw stand-in
and source series do not prove absence of an intermittent frozen failure.
These tiny CPU-stub jobs are shutdown/protocol witnesses, not full export or
performance measurements. The seat repeats the candidate series at the gate.
The frozen check, Reviewer A convergence and Reviewer B remain with the seat.

The footage folder and owner profile were untouched. No frozen build/run,
GPU-pack activation, GUI launch, network fetch, synthetic desktop input or git
write occurred. Every old-worker execution in turn 5 was inside the sandbox;
none ran in turn 6. Turn 6 changes only the two owned test files, README, this
report and ignored `work/wp-dr125/` scratch. No product file changed.

## Frozen check (seat)

Filled by the orchestrator (gen 45) from gen 44's seat run, 2026-11-04
18:33-18:35Z. Evidence is in
`clearwater-review-evidence\wp-dr125\frozen\` (md5: `handler-check.json`
`422aa005`, `run12.summary.txt` `55a863eb`, `proof-dr125.jsonl` `81d879f8`).

- **Build.** This is a onedir build of `1ea45021` from this worktree
  (`work/wp6.1/build-onedir-dr125.log`): 668.3 MiB. Both the hidden-import
  check (61 modules) and the bundle check PASS.
- **Handler check: PASS.** The entry script `__main__`, `gpu_pack` and
  `export_worker` in the bundle are bytecode- and constant-equal to the
  source (every function equal: 9/9 in `__main__`, 26/26 in the worker).
  `isolate_worker_stdin` is ABSENT, and `main` does not name it.
- **Pack bracket.** The hand-filled pack under
  `.worktrees/wp6.1/work/wp6.1/t3c/` was used read-only in place. `--verify`
  PASSES before and after: 11 distributions, 2,701 RECORD rows, 2,701 files,
  2,412.6 MiB.
- **Twelve frozen `--export-worker` runs** (6 heic + 6 video, alternating,
  through WP6.1's `proof4.py` re-targeted by `patch_paths.py`) with the pack
  present. Every run exits 0 with `ok: true`, device GPU, no failure and no
  warnings. Wall times are 1.7-20.8 s; the first run is cold. In every run:
  0 window hits, 0 timeout kills and no process left alive. The CUDA files
  mapped in every run are 59 from the pack, 8 from the Windows driver and
  0 from anywhere else. There were no crash exit codes: no `0xC0000005`, no
  WER abort.
- **Isolation.** The real `%LOCALAPPDATA%\Clearwater` is ABSENT before and
  after. The owner log's md5 is unchanged (`69ed0432...`). No
  `Clearwater.exe` is left running. No GUI or desktop input was used, and
  the DR-125 before shape was not run at the seat.
