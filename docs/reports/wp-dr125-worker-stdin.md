# WP-DR125: worker stdin isolation and shutdown

Status: cell implementation and records complete. Reviewer A, Reviewer B, the
seat frozen check and the final gate remain with the dispatcher. This report
does not itself close DR-125.

## Design as built

Product build: `6ef67a19`. Turn-5 checkout: `48915f42`, after the ruling merge.
Before-record base: `73453bdc`. Turns 4 and 5 change no product file.

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

## Validation and collection

| Turn-5 check | Result | Log under `work/wp-dr125/` |
|---|---|---|
| `uv run --no-sync ruff check .` | Passed | `ruff-5.log` |
| `uv run --no-sync ruff format --check .` | 323 files already formatted | `format-5.log` |
| `uv run --no-sync mypy` | Clean, 161 source files | `mypy-5.log` |
| Short worker tests, R1 deselected | 17 passed, 25 deselected | `short-5.log` |
| Full worker module, R1 deselected | 41 passed, 1 deselected | `modules-5.log` |
| Parallel collection | 18/42 nodes | `collect-parallel-5.log` |
| Serial collection | 24/42 nodes | `collect-serial-5.log` |

Both execution runs used `PYTHONPATH=scripts`, `-p sandbox_mkdir_shim`,
`-p no:cacheprovider`, `--timeout 300` and
`--deselect tests/test_app_export_worker.py::test_eager_imports_and_isolation_spawn_nothing_and_import_no_cupy`.
Their basetemps were `work/cdr-5-short` and `work/cdr-5`. The short run added
`-m 'not slow'`. The raw stand-in's full-module record shows five exits 0 with
empty stderr; the full-module worker series shows 20 successful results and
20 exits 0 with empty stderr. Evidence: `work/wp-dr125/series-5-summary.log`.

The earlier three-module run passed 283 nodes with R1 deselected once:
`work/wp-dr125/modules-3.log`. The Win32 mypy result in turn 3 was clean on
161 source files: `work/wp-dr125/mypy-3.log`.
`uv run --no-sync mypy --platform darwin src/clearwater/app/export_worker.py src/clearwater/__main__.py`
was clean on two source files: `work/wp-dr125/mypy-darwin-3.log`.
This test/doc-only turn does not change the Darwin product surface.

Turn-3 collection was 19 parallel and 24 serial nodes. Removing buffered mode
subtracts one parallel node; all 23 pre-existing nodes and the 20-run slow
series stay in the serial leg. Turn-5 collect logs below confirm the new split.

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
No further in-scope issue was found in the final verification pass. Reviewer A
and B verdicts remain separate seat work; none is claimed here.

## Limits

The buffered before shape is evidence rather than a gate test because its
fatal abort enters Windows Error Reporting and can wait for a crash dialog.
The frozen `0xC0000005` and source `_enter_buffered_busy` abort are one
buffered-reader lock with two ends, as ruled by CHARC.

The unsuppressed turn-4 record shows the fatal message plus a kill at the
bound; it does not supply a natural crash status. The suppressed base records
show natural `0xC0000005` exits after the same fatal message. The raw stand-in
and source series do not prove absence of an intermittent frozen failure.
These tiny CPU-stub jobs are shutdown/protocol witnesses, not full export or
performance measurements. The seat repeats the candidate series at the gate.
The frozen check and both review verdicts still must be supplied by the seat.

The footage folder and owner profile were untouched. No frozen build/run,
GPU-pack activation, GUI launch, network fetch, synthetic desktop input or git
write occurred. Every old-worker execution in this turn was inside the sandbox.
Only the owned stand-in, this report and ignored `work/wp-dr125/` scratch changed.

## Frozen check (seat)

SEAT TO FILL
