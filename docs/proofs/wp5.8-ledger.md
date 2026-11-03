# WP5.8 encoder-progress watchdog ledger

## Round 0

Depth at turn-1 end: 145,190 of 258,400 (driver footer).

Read-only assessment on 3de1ef68. No files changed and no tests run.

| Finding | Severity | Status | Evidence / ruling |
| --- | --- | --- | --- |
| Returning from buffered stdin.write does not prove OS acceptance; close can flush outside _send. | MAJOR | NEW, in envelope, confirmed by source trace | encode.py:904 uses default Popen buffering; :1028 writes without flushing; :1066 closes before the finish deadline. |
| Reading every frame leaves room for a real, small sentinel, so that recipe cannot force sentinel backpressure. | MAJOR | NEW, in envelope, confirmed by source trace | nut.py:224-236; encode.py:1064. |
| The encoder uses the OS default pipe; the 32 MiB helper serves decode. | MINOR | NEW, in envelope, confirmed by source trace | encode.py:904-910; decode.py:331; pipes.py:98. |

CHARC rulings, commit 6f2a023a, accepted without dispute:

- R1: watch write plus flush in _send, and watch stdin.close separately. Popen arguments
  remain unchanged. Add the small-send flush witness.
- R2: test-only sentinel = real sentinel plus a 36 MiB tail. The fake encoder parses no NUT;
  explain the artificial payload in the test docstring. FINISH_TIMEOUT_S stays unchanged.
- R3: encoder stdin is the OS default subprocess.PIPE; no transport change.
- Q1 (a) encoder_failed, Q2 300 s constant, Q3 kill() confirmed.

Round-0 counts: critical 0, major 2, minor 1; in envelope 3, out 0; NEW 3, REOPENED 0;
reverts 0; no product or test fixes in turn 1. Reviewer A not yet run (dispatcher-owned).

## Turn 2

Depth at turn-2 end: 202,018 input tokens of 475,000 (driver footer, 2026-11-03 turn 2; the footer reported a 258,400 window at turn 1)

Base: 6f2a023a. One logical change: watchdog plus its regression witnesses.

### Environment and RED

- Command: `uv run python -c "import io; print(io.DEFAULT_BUFFER_SIZE)"`.
  Exit 0, value **8192**. Log: `work/c58-2-buffer.log`. This corrects the ruling text's
  interpreter-specific 131072 figure; the dispatcher's 8192 observation agrees.
- Every pytest command sets `PYTHONPATH=scripts`, loads `-p sandbox_mkdir_shim`, and disables
  cacheprovider. These sandbox-only additions preserve the dispatch's requested targets.
- Initial RED log `work/c58-2-red.log`: 6 failed, 126 deselected in 2.91s. Four failures were
  a test fixture's incorrect Frame constructor, so this was not valid regression evidence.
  Fixed the new fixture to use all frozen IF-1 fields; product code remained unchanged.
- Valid RED command:
  `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode_units.py
  -k 'test_watchdog_' --timeout 60 --basetemp=work/c58-2-red-verified`.
  Exit 1: **4 failed, 2 passed, 126 deselected in 11.53s**.
  Log: `work/c58-2-red-verified.log`. Each child has a separate four-second rescue timer.

| Test (test_watchdog_ prefix) | RED disposition | Observed failure / control |
| --- | --- | --- |
| stalled_frame_fails_and_removes_output | Expected RED | AssertionError: 'stopped accepting frames' absent from ordinary encoder exit text; rescue releases the write. |
| healthy_slow_encoder_completes_six_frames | Expected PASS | Existing sink can feed six frames at 0.3 s/read without failure. |
| stalled_sentinel_fails_before_finish_timeout | Expected RED | AssertionError: 'stopped accepting frames' absent from ordinary encoder exit text; rescue releases the sentinel write. |
| normal_nonzero_exit_keeps_status_and_stderr | Expected PASS | Existing exit status 7 and stderr-tail behavior is the preserved control. |
| abort_during_wait_joins_watcher_without_thread_error | Expected RED | AssertionError: abort must stop the started watchdog thread (no watcher exists yet). Existing abort already releases the writer. |
| small_send_flushes_before_another_write | Expected RED | AssertionError: small _send was buffered instead of readable by the encoder. |

### GREEN

Implementation follows R1-R3. The daemon watcher starts beside stderr draining, waits on a
stop Event at POLL_S = 0.2 s, and checks a live process plus a pending operation older than
STALL_TIMEOUT_S = 300 s. _phase_lock guards the pending timestamp, acceptance timestamp,
bytes in flight, and stall record. Process/name publication precedes thread startup. _send
watches write plus flush; _end_stream separately watches close. The watcher records elapsed
seconds and bytes, kills the process, and leaves the writer's existing encoder_failed /
_fail / _cleanup path to delete output. One synchronous sender means the message names one
waiting frame (also used for the end sentinel). Ordinary exit status / stderr text is kept.
Watcher exceptions are logged. Normal completion, abort, and failure stop and join it.
Popen arguments, pipe size, commands, selection, and FINISH_TIMEOUT_S are unchanged.

Commands below use the sandbox plugin and PYTHONPATH described above. Every runner's stdout
and stderr went to the named worktree log; only summaries were read into the return report.
uv emits an environment-location warning about the inherited VIRTUAL_ENV; it ignores that
environment and uses this worktree's project environment. This is not a check failure.

| Check | Command | Exit / summary | Log |
| --- | --- | --- | --- |
| Initial GREEN units | `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode_units.py --timeout 120 --basetemp=work/c58-2-green --durations=0` | 0: 132 passed in 5.26s | work/c58-2-green.log |
| Final GREEN units | `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode_units.py --timeout 120 --basetemp=work/c58-2-green-final --durations=0` | 0: 132 passed in 5.50s | work/c58-2-green-final.log |
| Existing sink tests | `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode.py -m 'not gpu and not footage and not slow' --timeout 300 --basetemp=work/c58-2-enc` | 0: 115 passed, 22 deselected in 211.66s (0:03:31) | work/c58-2-enc.log |
| Ruff | `uv run ruff check src/clearwater/io/video/encode.py tests/test_io_video_encode_units.py` | 0: All checks passed! | work/c58-2-ruff-final.log |
| Format | `uv run ruff format --check src/clearwater/io/video/encode.py tests/test_io_video_encode_units.py` | 0: 2 files already formatted | work/c58-2-format-final.log |
| Mypy | `uv run mypy` | 0: Success: no issues found in 156 source files | work/c58-2-mypy-final.log |

The units file has 126 pre-existing parametrized cases, rather than the dispatch's estimate
of 64; plus six new cases = 132. A text comparison from TB through the end of the old units
file confirms the existing tests and helpers are identical. Both other encode test files are
untouched. No full-suite, hardware-marked, or parallel pytest run was made. The existing sink
run started before final formatting and the singular noun cleanup in the new stall message;
no product logic changed afterward. Final units, lint, format, and mypy were run afterward.

Final new-test call times (`--durations=0`):

| Test (test_watchdog_ prefix) | Seconds |
| --- | ---: |
| stalled_frame_fails_and_removes_output | 1.05 |
| healthy_slow_encoder_completes_six_frames | 1.92 |
| stalled_sentinel_fails_before_finish_timeout | 1.24 |
| normal_nonzero_exit_keeps_status_and_stderr | 0.10 |
| abort_during_wait_joins_watcher_without_thread_error | 0.10 |
| small_send_flushes_before_another_write | 0.10 |

All six were below 5 s with no rescue firing in GREEN. These are lightweight fake-encoder
test timings on the shared host, not exclusive product performance figures.

Stall timeline artifact:
`work/c58-2-green-final/test_watchdog_stalled_frame_fa0/timeline.json`.
Monotonic seconds as observed: pending write began 173004.671; watcher called kill at
173005.703 (+1.032 s); output deletion completed at 173005.718 (+1.047 s); the caller observed
the writer's VideoEncodeError at 173005.718. Clock granularity does not resolve deletion and
caller observation within that final tick. The child had read the stream/frame headers plus
4096 payload bytes and then stopped; the remaining 36 MiB payload forced the pending send.
The pending-window timestamp is not a separate measurement of the instant the kernel blocked.

### Verification loop

- Suspected test fixture mismatch: confirmed by Frame's frozen dataclass fields; fixed only
  the new helper, then repeated RED successfully.
- All existing test function bodies remain unchanged. No product changes before valid RED.
- No Reviewer A round yet. No reverts or reopened findings.
- Initial lint/format found import ordering, two overlong lines, and new-test layout issues;
  corrected those and re-ran both to green. Logs: work/c58-2-ruff.log and c58-2-format.log.
- Final pass checked the six discriminating/control cases, lifecycle/lock order, thread-start
  failure cleanup, stderr retention, ordinary exits, and file ownership. No new in-envelope
  issue found. The healthy control additionally checks a created watcher is joined at close.
- The three changed files are ASCII-only and were normalized to LF. git diff --check is clean.
- No dependencies, frozen interfaces, encoder choice/command/pipe tuning, or non-owned product
  files changed. No footage was read or written. No writes were directed outside this worktree.
- Full gate, serial worker tests, Reviewer A/B, and completion report remain dispatcher/later
  turn work; this turn ends at the requested RED/GREEN boundary.

Turn-2 ledger disposition: round-0 R1/R2 implemented and witnessed; R3 already corrected by
CHARC in the brief. New review findings 0 (critical 0, major 0, minor 0); REOPENED 0, out of
envelope 0, reverts 0; product-code fix YES, test changes YES. This is build verification,
not a substitute for the dispatcher's independent Reviewer A round.

### W52-2 transfer counters

Supplied 2026-11-02 17:38Z counters (no outside-worktree evidence read): worker WriteTransferCount
16,711,513,769 B; encoder ReadTransferCount 16,678,523,010 B; difference 32,990,759 B.
Decoder WriteTransferCount 16,705,557,397 B. The dispatcher reports Windows counts all file
and pipe I/O per process, not only the worker-to-encoder channel.

From color/samples.py:23-45, :86-114 and FFmpegVideoSink._payload, one 3840 x 2160 frame
is 3 x 3840 x 2160 = **24,883,200 B** at 8-bit (gbrp), or **49,766,400 B** at 10-bit
(gbrp10le uses 16-bit samples). There is no YUV420-sized payload on this pipe: the encoder
performs that conversion after reading planar RGB.

NUT overhead is small. By nut._header (:239-245), define V(n) as the number of seven-bit
variable-integer bytes. For an 8-bit 4K payload, V(size) = 4 and the per-frame header is
**24 + V(pts) + V(pts + 32768) bytes** (syncpoint, header and CRCs included). At pts 0 it is
28 B; for the example cadence pts = index * 1001 through 681 frames it is 28-30 B/frame.
The sentinel uses one payload byte and a small corresponding header; stream headers are
written once. The example cadence is illustrative, not an inference of the source time base
from these counters. None of this framing contributes megabytes of queued data.

encode._start uses subprocess.PIPE and no explicit enlarged pipe. The enlarged 32 MiB pipe
is decode's stdout transport (decode.py:331); it is not this encoder stdin. The measured Python
buffer is 8,192 B. Therefore **32,990,759 B cannot be the contents of the default encoder pipe
plus Python's buffer alone**. An application-held 24,883,200 B frame that is being written is
also distinct from kernel pipe occupancy or proof of OS acceptance.

The counter difference is **unexplained by the counters**. It subtracts totals for different
sets of I/O: worker writes include its scratch cache and protocol output; encoder reads include
the NUT pipe AND its source-file input (audio/data copying, with demuxer reads). They are not
paired per-channel byte counters, nor is a shared start/reset or atomic snapshot established.
We cannot assign the 32,990,759 B remainder to pipe backlog, Python buffering, FFmpeg's internal
buffers, scratch writes, source-file reads, or a precise number of pending frames. The decoder
write total divided by the 8-bit frame size is 671.3588846 frame-equivalents; it is likewise an
aggregate process counter, not an independently established complete-frame count at the sink.

On a recurrence with a blocked encoder write/flush or final close, _watch_encoder now reaches
encode.py:964-967 after more than 300 s of that pending window and calls kill. Expected polling
overshoot is up to POLL_S (0.2 s), plus host scheduling and existing error/cleanup time; it is
not a hard real-time deadline. If that pending operation began at the supplied 17:02:57Z progress
stop, the nominal kill would be about 17:07:57Z; the counters do not establish that exact start.
The brief's roughly 9.9 s/frame CPU-route feed interval is about 30 times below the threshold,
but is not a direct measurement of one _send's duration. No real-hardware recurrence was run.
FINISH_TIMEOUT_S still governs an encoder that has accepted EOF but then does not finish.

## Turn 3 (fresh session; Reviewer A round 1 remediation)

Depth at turn-3 end: 93,669 input tokens of 258,400 (driver footer; FRESH session 01a1a049-871e-7ab2-a47e-aab7fd77055d, 2026-11-03)

Base: `5a957919`, verified on arrival with a clean worktree. Reviewer A is the dispatcher's
Claude pass on that head, verdict **NEW_CRITICAL_MAJOR_FOUND**. The eleven findings and
their dispositions below are the binding packet supplied in the turn-3 dispatch; no review
transcript or other evidence outside this worktree was read. Durable reviewer evidence is
dispatcher-owned under `C:\Users\rwsmy\clearwater-review-evidence\wp5.8\` (exact round path,
transport, model/version and mechanical assertions to be filled by the dispatcher).

### Round 1 adjudication and changes

| ID | Severity | Disposition | Evidence / change |
| --- | --- | --- | --- |
| 1 | MAJOR | Confirmed, fixed | `_watch_encoder` no longer subtracts the pending timestamp from the current clock on every poll. It accumulates capped poll deltas, resets on a new pending timestamp, and clears on an idle poll. `SUSPEND_GAP_S = 5.0` caps suspend-sized gaps. The injected-clock test fails on the base and passes on the fix. |
| 2 | MINOR | Confirmed, fixed (test coverage) | Ported `test_render_gap_real_code` from the authorized reviewer probe into `test_watchdog_render_gap_between_frames_is_not_a_stall`. A 1.6 s render gap with a 1.0 s threshold passes the real watcher and fails the reviewer's idle-arming mutation. |
| 3 | MINOR | Confirmed, fixed (test coverage) | Added `test_watchdog_nonzero_exit_races_stall_with_one_error`: the child stops consuming and exits 7 after 1.0 s, near the 1.0 s threshold. Exactly one writer error must contain either exit status 7 or the stall wording, exclusively; no thread exception, output deleted, process and watcher ended. The quick-exit test remains. |
| 4 | ADVISORY | Already satisfied, retained | The existing abort test installs `threading.excepthook` and asserts its recorder is empty. Source inspection confirmed both before edits; the test passed in both final unit runs. No duplicate recorder added. |
| 5 | ADVISORY | Fixed | The abort and small-send tests now call `_watchdog_wait(..., timeout=3.0)`, below the independent four-second rescue. |
| 6 | ADVISORY | Fixed | Stall text is now `The video encoder (<name>) stopped accepting data for <N> s; the export was stopped.` This applies truthfully to header, payload, sentinel and close. The existing shared stderr-tail construction, including `no error output`, is unchanged. The earlier watchdog assertions now expect `data`. |
| 7 | ADVISORY | Accepted limit, no change | A pending write that raises while the process remains alive can reach the stall deadline during `_exit_status()`'s bounded wait. The stall text can replace the eventual status text; the export fails and removes output either way. |
| 8 | ADVISORY | Accepted limit, no change | A failed kill while the process remains alive, or a process that does not end after kill (for example a stuck driver call), can leave the writer blocked after the watcher returns. Exceptions are logged. The supplied W52-2 user-mode spin is the case kill ends; no real recurrence was run here. |
| 9 | ADVISORY | Fixed | Removed unread `_last_accepted`, `_bytes_in_flight`, and the unused byte member of `_stalled`. The stall record now holds only accumulated seconds. The threshold applies to the CURRENT pending I/O, with awake time estimated by capped polling; renderer time never counts. |
| 10 | ADVISORY | Confirmed, fixed | `_start` now chooses a watchdog-specific startup message before creating/starting that thread, separately from the stderr-drain message. Added an injected thread-start failure test proving `encoder_failed`, the true message, a dead child, and deleted output. |
| 11 | ADVISORY | Accepted pre-existing limit, no change | Abort may close stdin between write and flush, producing `ValueError` for I/O on a closed file. The pre-existing header/payload gap has the same class of race. The caller's cancel state decides the outcome; no new exception policy is introduced. |

The implementation follows the required capped-poll design. Each loop samples monotonic time
under `_phase_lock`. For an already-observed pending operation it adds
`min(now - previous_poll, SUSPEND_GAP_S)`. A newly observed pending timestamp starts a new
total of `min(now - waiting_since, SUSPEND_GAP_S)`, accounting for the first partial poll
interval while also capping a suspend before the first observation. Every poll, including an
idle poll, advances `previous_poll`; an idle poll clears the pending identity and total.
The accumulated total and pending identity are watcher-local; shared timestamps, process
state, and the stall record use the existing lock. The thread still waits on the stop Event.

The timing boundary is the start of the CURRENT pending I/O (design item 2). For the
single-writer sink this is the brief's acceptance boundary: completed sends have returned
from write AND flush before the next send starts. Time spent rendering between those sends
is excluded. Partial kernel acceptance inside an outstanding write is not observable here;
the watcher tracks the pending operation, not per-byte transport progress. No command,
encoder preference, pipe size, finish timeout, dependency, or frozen interface changes.

The suspend test uses a real non-reading Python child and replaces ONLY `encode.time` with
a small namespace around a controlled monotonic clock (pytest, subprocess waits, timer and
test coordination retain real time). After the watcher observes the pending write, the test
adds 400 s to that clock, checks that the write and process survive the jump, then checks
that continued awake polling produces the stall error and deletes output. Because the test
threshold is shortened from 300 s to 1 s, it also shortens the suspend cap from 5 s to 0.1 s
and the poll interval to 0.02 s. Keeping the production 5 s cap against a 1 s test threshold
would intentionally exhaust the test deadline in a single capped jump.

### RED evidence

All pytest runs set `PYTHONPATH=scripts`, load `-p sandbox_mkdir_shim`, and disable the
cacheprovider. These sandbox additions are required by the dispatch protocol. Outputs go
only to the named `work/c58-3-*` files. Base product code was unchanged for both RED runs.

1. Command: `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider
   tests/test_io_video_encode_units.py -k 'suspend_gap or render_gap_between or nonzero_exit_races'
   --timeout 120 --basetemp=work/c58-3-red`.
   Exit 1: **1 failed, 2 passed, 132 deselected in 3.60s**.
   Log: `work/c58-3-red.log`. RED line:
   `FAILED ...::test_watchdog_suspend_gap_does_not_count_as_awake_stall`,
   `AssertionError: suspend clock jump killed a healthy pending operation`.
   The new render-gap and near-threshold exit tests pass against the base, as expected:
   findings 2 and 3 concern coverage, not a confirmed failure in those paths.
2. Command: `uv run python work/c58-3-mut-probe.py` (same PYTHONPATH).
   Exit 1: **1 failed, 134 deselected in 1.85s**.
   Log: `work/c58-3-mut-red.log`. RED line:
   `FAILED ...::test_watchdog_render_gap_between_frames_is_not_a_stall`, with
   `VideoEncodeError: The video encoder (libx265) stopped accepting frames ...`.
   The one-off script ports the reviewer's `idle_watch` mutation into an autouse pytest
   plugin, replaces `_watch_encoder` in memory only, and selects the new render-gap test.
   It arms from `_last_accepted` even when no I/O is pending. No mutation was applied to a
   source file or committed. The probe file is an untracked/ignored work artifact, not a
   deliverable. The base watcher without this mutation passed that test in command 1.

### GREEN evidence

| Check | Command (with PYTHONPATH as above) | Exit / summary | Log |
| --- | --- | --- | --- |
| Initial units | `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode_units.py --timeout 120 --basetemp=work/c58-3-green` | 0: 136 passed in 9.30s | work/c58-3-green.log |
| Final units | `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode_units.py --timeout 120 --basetemp=work/c58-3-green-final` | 0: 136 passed in 9.02s | work/c58-3-green-final.log |
| Four-worker units | `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode_units.py --timeout 120 -n 4 --basetemp=work/c58-3-n4` | 0: 136 passed in 4.93s | work/c58-3-n4.log |
| Existing encoder tests | `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode.py -m 'not gpu and not footage and not slow' --timeout 300 --basetemp=work/c58-3-enc` | 0: 115 passed, 22 deselected in 184.37s (0:03:04) | work/c58-3-enc.log |
| Ruff | `uv run ruff check src/clearwater/io/video/encode.py tests/test_io_video_encode_units.py` | 0: All checks passed! | work/c58-3-ruff-final.log |
| Format | `uv run ruff format --check src/clearwater/io/video/encode.py tests/test_io_video_encode_units.py` | 0: 2 files already formatted | work/c58-3-format-final.log |
| Mypy | `uv run mypy` | 0: Success: no issues found in 156 source files | work/c58-3-mypy-final.log |

The existing encoder test run completed normally, with log progress observed at 62 percent
before its final summary; no five-minute stall interval occurred. No other pytest run was
started while it ran. Only the three turn-owned paths are modified. `git diff --check`
is clean. `git diff --exit-code` confirms no edits to `tests/test_io_video_encode.py`,
`tests/test_io_video_encode_bench.py`, `tests/test_app_export_worker.py`, or
`tests/test_jobs_export_process.py`. The latter two were not run in this turn; their serial
gate remains the dispatcher's task. No footage path was read or written, and no writes
were directed outside this worktree.

Free disk was checked before the RED run (81.93 GiB), before four-worker units (81.90 GiB),
and before the existing encoder run (81.90 GiB), all above the dispatch's 25 GiB stop line.
Logs: `work/c58-3-disk.log`, `work/c58-3-disk-n4.log`, `work/c58-3-disk-enc.log`.
No whole-suite, GPU/footage/gui/slow, sync, or real-hardware export was run. Unit timings
are fake-encoder safety checks on the shared host, not exclusive product performance data.
uv's inherited `VIRTUAL_ENV` warning is emitted on stderr (PowerShell labels that stream
`NativeCommandError`); the native process exit status and actual pytest summaries above
are the reported outcomes, not that wrapper label.

### Verification loop and round ledger

- Suspected suspend false positive: independently confirmed by the injected-clock RED on
  the base; fixed with capped deltas and confirmed GREEN in both unit modes.
- Suspected render-gap coverage hole: confirmed by the planted idle-arming mutation;
  the real watcher passes the new witness. No product change for finding 2.
- Suspected lack of a near-deadline exit witness: confirmed by the original child script's
  immediate exit; added the delayed child. Both immediate and delayed cases pass.
- Suspected missing abort exception recorder: rejected as already satisfied by source
  inspection and the passing test. No removal or weakening of that assertion.
- Startup-failure wording: inspected the shared exception handler and confirmed it named
  stderr even after stderr startup succeeded; separated the text and injected the watcher
  startup failure to verify both error routing and cleanup.
- Initial lint found one SIM117 in the new start-failure test. Combined the context
  managers, then repeated units, ruff, format and mypy successfully. Product logic did not
  change after the first GREEN run.
- Final source pass checked reset-on-new-pending, idle exclusion, capped first observation,
  stop/join paths, stderr-tail retention, lock order and removal of all unused progress
  fields. No additional in-envelope finding. The three disclosed limits (7, 8, 11) remain
  accepted for this turn and must be carried into the later completion report.

| Round | Critical | Major | Minor | Advisory | In / out | NEW / REOPENED | Reverts | Product / tests | Status |
| --- | ---: | ---: | ---: | ---: | --- | --- | ---: | --- | --- |
| 0 (carried) | 0 | 2 | 1 | 0 | 3 / 0 | 3 / 0 | 0 | fixed in turn 2 / yes | R1-R3 ruled and built |
| A1 | 0 | 1 | 2 | 8 | 11 / 0 | 11 / 0 | 0 | yes / yes | 7 fixed, 1 already satisfied, 3 accepted limits; YIELD for A2 |

No finding was reclassified, reopened or routed out of the envelope. Reviewer A convergence,
the completion report, Reviewer B and the final gate remain later/dispatcher work; this turn
does not claim package acceptance. One logical remediation change is offered to the dispatcher;
no git writes or commits were attempted.
