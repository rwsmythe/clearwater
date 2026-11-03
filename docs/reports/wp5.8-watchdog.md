# WP5.8 encoder-progress watchdog completion report

Date: 2026-11-03 UTC. Implementer: Codex, GPT-6.1 Sol / high.
Turn-4 base: `cca85d8a` (turn-3 remediation). This report covers the implementation,
Reviewer A cleanup and cell verification; it does not claim final package acceptance.
Reviewer A round 2 returned **NO_NEW_CRITICAL_MAJOR** at the dispatcher's seat. Its two
minor findings are addressed in this turn. Reviewer B and the final gate remain with the
dispatcher. The cumulative review and verification record is
`docs/proofs/wp5.8-ledger.md`.

## Design as built

`FFmpegVideoSink` retains the existing subprocess command, default encoder stdin pipe,
encoder selection and IF-5 signatures. No dependency or settings change was made. Export
still runs in the existing worker process; no parent-process, job, batch or GUI code changed.
The existing `encoder_failed` path remains responsible for showing the failure and handling
the failed batch item. The sink attempts to stop the process and delete its partial output;
the existing job path handles the D85 journal. Batch continuation and the worker protocol
were not newly exercised in this cell turn; their serial tests are final-gate work.

At `_start`, a daemon watchdog starts beside the stderr drain. `_send` sets
`_waiting_since` under `_phase_lock` before write, keeps it set through flush, and clears
it in `finally`. Returning means write and flush returned, not that FFmpeg decoded the data.
The sentinel uses `_send`; the subsequent `stdin.close()` has a separate watched window.
There is one synchronous sender, and no pending window during rendering gaps. A new pending
timestamp resets the watcher's total even if the watcher missed the intervening idle period.
This measures the CURRENT pending operation, not individual accepted bytes within that
operation and not the interval since the renderer produced a frame.

The watcher requests a poll every `POLL_S = 0.2` seconds. It exits on its stop Event,
a non-open phase, or an ended encoder. For a live encoder with pending I/O:

1. First observation: `elapsed = min(now - waiting_since, SUSPEND_GAP_S)`.
2. Further observations of the same operation: add
   `min(now - previous_poll, SUSPEND_GAP_S)`.
3. A new operation resets the total; an idle poll clears it.
4. If the total exceeds `STALL_TIMEOUT_S = 300.0`, record `_stalled = elapsed` and call
   `process.kill()`.

`SUSPEND_GAP_S = 5.0` prevents a long suspend-sized clock jump from consuming hundreds of
seconds of the deadline at once. It estimates awake waiting time; it is not an OS suspend
detector. Shared timestamps, phase, process state and the stall record use `_phase_lock`;
the accumulated total and pending identity are watcher-local. The lock is not held across
write, flush or close. Kill errors and other watcher exceptions are logged. Cleanup signals
the stop Event and joins the watcher with a one-second timeout outside the phase lock.

A successful kill releases the blocked writer by the existing pipe-error path. `_send`
builds a `VideoEncodeError(kind="encoder_failed")`; `_fail` invokes cleanup and deletes
the output before raising to the caller. `_encoder_failed` prefers a recorded stall over
ordinary exit status and retains the shared ASCII-safe stderr tail. The message is:

```text
The video encoder (<encoder name>) stopped accepting data for <N> s; the export was stopped. <stderr tail>
```

`N` is accumulated capped time rounded to a whole second. With no stderr, the existing
shared text is `no error output`. Watchdog startup failure has its own true message,
`The video encoder (<name>) watchdog could not be started: ...`; stderr-drain startup
keeps its existing message. `FINISH_TIMEOUT_S = 1800.0` is unchanged and starts after the
sentinel send and stdin close return. It covers an encoder that accepted EOF but does not exit.

## Departures from the initial brief design

| Item | Built behavior and reason |
| --- | --- |
| R1: buffering and close | Watch write PLUS flush, and separately watch stdin close. A buffered write returning alone does not establish that Python has passed all bytes to the OS. Popen arguments are unchanged. The small-send test witnesses the flush. |
| R2: sentinel witness | Only the test appends a 36 MiB tail to the real sentinel. The fake child parses no NUT; a normal small sentinel cannot force backpressure after all frames are consumed. Production sentinel bytes are unchanged. |
| R3: pipe identity | Encoder stdin uses default `subprocess.PIPE`. AD-23's enlarged 32 MiB pipe belongs to the decoder. Neither pipe configuration changed. |
| Round-1 suspend accounting | Replace raw elapsed monotonic time with capped polling accumulation, including the first observation. On this Windows interpreter monotonic time advances during sleep; subtracting the pending timestamp on wake could kill a healthy pending operation. |
| Message | Use `stopped accepting data`, rather than `frames` or a fixed waiting-frame count, because headers, sentinel and close are also watched. Reuse `encoder_failed`; consumers need no new error-kind branch. |
| Removed state | Remove `_last_accepted`, `_bytes_in_flight`, and the unused byte member of `_stalled`. The watcher uses the current pending timestamp and accumulated seconds; the removed fields had no reader. |

The measured `io.DEFAULT_BUFFER_SIZE` is **8,192 bytes**, from the turn-2
`uv run python -c "import io; print(io.DEFAULT_BUFFER_SIZE)"` result recorded in the ledger.
This corrects the round-0 ruling's interpreter-specific 131,072-byte statement. It is not a
claim about the kernel pipe's capacity.

The default 300-second threshold remains a constant, not a setting. The supplied WP5.2
CPU-route feed interval was about 9.9 seconds per frame, roughly 30 times smaller. That
interval is not a direct measurement of a single pending `_send`. Encoder preference on
the CPU-forced and fallback routes is unchanged.

## Tests and validation

All eleven watchdog cases are unmarked parallel-leg tests, with per-test `tmp_path` outputs.
A `sys.executable -c` child uses real stdin pipe reads and counted bytes. The sink's real
lifecycle and transport remain in use; fake payload generation avoids allocating a large
float image, and fake verification avoids requiring the Python child to produce an MP4.
Each child has an independent four-second rescue timer. Stall threshold is shortened to
1.0 seconds in tests. All rescues remained unset in the successful run.

Final turn-4 call durations, from `work/c58-4-green.log` (`--durations=0`):

| Test (`test_watchdog_` prefix) | Seconds | Witness |
| --- | ---: | --- |
| stalled_frame_fails_and_removes_output | 1.03 | Live non-reader stalls on a pipe-filling frame; encoder named, output deleted, process and watcher ended. |
| healthy_slow_encoder_completes_six_frames | 1.90 | Six reads spaced by 0.3 s complete although total time exceeds the threshold. |
| stalled_sentinel_fails_before_finish_timeout | 1.24 | Artificial pipe-filling sentinel tail triggers the watchdog, not the finish deadline. |
| normal_nonzero_exit_keeps_status_and_stderr | 0.07 | Immediate exit 7 preserves exit status and stderr without stall text. |
| abort_during_wait_joins_watcher_without_thread_error | 0.17 | Abort releases the blocked writer, removes output and joins the watcher; thread-exception recorder stays empty. |
| small_send_flushes_before_another_write | 0.07 | Child receives a small header before any further write. |
| suspend_gap_does_not_count_as_awake_stall | 0.96 | A 400 s clock jump after the first pending observation is capped; subsequent awake polling still catches the stall. |
| first_observation_caps_suspend_gap | 1.01 | A 400 s jump BEFORE the first pending observation is capped; subsequent awake polling still catches the stall. |
| render_gap_between_frames_is_not_a_stall | 1.68 | A healthy encoder survives a 1.6 s gap between two frames with no pending I/O. |
| nonzero_exit_races_stall_with_one_error | 1.03 | Child exits around the deadline; exactly one error has exit-status OR stall wording, with cleanup and no thread exception. |
| start_failure_names_watchdog_and_cleans_output | 0.01 | Injected watcher-start failure reports the true cause and cleans the already-started process/output. |

Both fake-clock tests replace only `encode.time`, preserving real clocks for subprocess
waits, pytest, rescue and coordination. They shorten the suspend cap to 0.1 seconds and
poll interval to 0.02 seconds along with the one-second threshold. A production five-second
cap against a one-second test threshold would itself exhaust that shortened threshold.
The new first-observation test parks the watcher outside the phase lock before starting
the write, waits until the child has stopped reading, jumps the clock, then releases the
first poll. It checks survival immediately afterward and eventual awake-time stall detection.

Discrimination evidence:

- Turn 2, before implementation: **4 failed, 2 passed** for the six original watchdog
  cases; valid RED failures covered stalled frame, sentinel, watcher lifecycle and flush.
- Turn 3, base `5a957919`: the post-first-observation suspend test failed with
  `suspend clock jump killed a healthy pending operation`; the render-gap and delayed-exit
  controls passed. The reviewer's idle-arming mutation failed the new render-gap test.
- Turn 4: `uv run python work/c58-4-mut-probe.py` removes only the first-observation
  `min(..., SUSPEND_GAP_S)` in memory. **1 failed, 136 deselected in 0.50s**, specifically
  `test_watchdog_first_observation_caps_suspend_gap` with
  `AssertionError: uncapped first observation killed a pending operation`.
  Log: `work/c58-4-mut-red.log`. No mutated source was written or committed.

Turn-4 commands set `PYTHONPATH=scripts`. The sandbox shim is required for pytest temp
directories; cacheprovider is disabled. Only the authorized units target ran in this turn.

| Check | Command | Result / evidence |
| --- | --- | --- |
| Units | `uv run pytest -q -p sandbox_mkdir_shim -p no:cacheprovider tests/test_io_video_encode_units.py --timeout 120 --basetemp=work/c58-4-green --durations=0` | Exit 0: **137 passed in 9.95s**; `work/c58-4-green.log`. The extra option reports durations only. |
| Ruff | `uv run ruff check src/clearwater/io/video/encode.py tests/test_io_video_encode_units.py` | Exit 0: **All checks passed!**; `work/c58-4-ruff.log`. |
| Format | `uv run ruff format --check src/clearwater/io/video/encode.py tests/test_io_video_encode_units.py` | Exit 0: **2 files already formatted**; `work/c58-4-format.log`. |
| Mypy | `uv run mypy` | Exit 0: **Success: no issues found in 156 source files**; `work/c58-4-mypy.log`. |

Prior turn-3 evidence, not rerun in turn 4: units **136 passed in 9.02s**; four-worker units
**136 passed in 4.93s**; existing `tests/test_io_video_encode.py`, excluding gpu/footage/slow,
**115 passed, 22 deselected in 184.37s**. Logs and exact commands are in the ledger.
Turn 4 changes no executable product logic. The original 126 units cases and the separate
existing encode/bench tests remain unchanged. Serial worker/process tests, full-suite
collection identity, Reviewer B and the final gate remain dispatcher work.

Disk before turn-4 testing: **82.57 GiB free**, above the 25 GiB stop line;
`work/c58-4-disk.log`. These are lightweight fake-encoder timings on a shared Windows
host, not exclusive product-performance measurements. No real export, hardware-marked
suite, footage access or dependency sync was run in this turn.

## Fake-encoder stall timeline

Fresh artifact:
`work/c58-4-green/test_watchdog_stalled_frame_fa0/timeline.json`.
The child reads the stream header, first frame header, and 4,096 payload bytes, then sleeps
without reading. The remaining 36 MiB payload forces the write to wait.

| Event | Monotonic seconds | Relative to pending start |
| --- | ---: | ---: |
| Pending payload window began (`_waiting_since`) | 175442.546 | 0.000 s |
| Watcher called `process.kill()` | 175443.562 | 1.016 s |
| `_remove` returned after deleting output | 175443.562 | 1.016 s |
| Caller observed the writer's `VideoEncodeError` | 175443.562 | 1.016 s |

The timestamp marks entry to the pending window, not an independently instrumented instant
of kernel blocking. The non-reader, oversized payload and pending write establish real
backpressure. Clock granularity does not distinguish kill, deletion and caller observation
within the final tick. Source order is kill, pipe failure/error construction, cleanup and
deletion, then error raised to the caller. The writer's internal first exception timestamp
was not separately recorded. The rescue did not fire; output was absent and the process
and watcher were ended at the test assertions.

## W52-2 evidence against the new path

This is a re-reading of the supplied evidence and ledger, not a new hardware reproduction
or a read of outside-worktree evidence. W52-2 had a live encoder spinning in user mode,
zero I/O and a blocked worker write for about 35 minutes. With the new code, a pending
operation is armed by `_send` (`encode.py:1139`), accumulated by `_watch_encoder`
(`encode.py:999-1013`), and after more than 300 capped polling seconds the watcher records
the stall and calls kill (`encode.py:1014-1018`). The released writer uses `_encoder_failed`
(`encode.py:1115`) and `_fail` / `_cleanup` (`encode.py:1285`, `encode.py:1295`) to report
the encoder and remove output. Final close is also watched (`encode.py:1215`).

With normal awake scheduling, the nominal bound is about 300 seconds from the pending
operation's start, plus up to one requested poll interval (0.2 s), host scheduling and
existing error/cleanup time. It is not a hard real-time bound. If that pending start was
the supplied progress stop at 17:02:57Z, the nominal kill would be about 17:07:57Z.
The supplied counters do not establish that start instant. Suspend and watcher starvation
can extend wall-clock detection as described below.

Supplied 17:38Z counters:

| Process counter | Bytes |
| --- | ---: |
| Worker WriteTransferCount | 16,711,513,769 |
| Encoder ReadTransferCount | 16,678,523,010 |
| Difference | 32,990,759 |
| Decoder WriteTransferCount | 16,705,557,397 |

The roughly 33 MB difference is **unexplained by the counters**. Windows process transfer
counters aggregate different I/O sets: worker writes include scratch/cache and protocol
output; encoder reads include both the NUT pipe and source-file reads for copied audio/data.
These are not paired counters for a single channel, and a shared reset or atomic snapshot
was not established. Therefore the difference cannot be assigned to pending frames,
kernel pipe occupancy, Python buffering, FFmpeg buffering, or scratch/source I/O.

One 8-bit 3840 x 2160 planar RGB payload is **24,883,200 bytes**; 10-bit planes use 16-bit
samples and **49,766,400 bytes**. NUT headers add tens of bytes per frame, not megabytes.
An application-held frame undergoing a write is distinct from kernel pipe contents.
The encoder's default pipe plus the measured 8,192-byte Python buffer does not explain
32,990,759 bytes as pipe contents. Decoder's enlarged 32 MiB pipe is a different channel.
The decoder counter divided by the 8-bit frame size is about 671.36 frame-equivalents,
also not an independently established sink frame count. No precise backlog can be inferred.

## Limits and test notes

- **R1 advisory 7, retained:** if a write raises while the encoder remains alive, the
  watchdog can reach its threshold during `_exit_status()`'s bounded wait. Stall wording
  may replace the eventual status wording; the export fails and cleans output either way.
- **R1 advisory 8, retained:** if kill raises while the encoder lives, or the process cannot
  end after kill (for example in a stuck driver call), the watcher returns and the writer
  may stay blocked. Exceptions are logged; the watchdog does not retry or restart.
  W52-2's reported user-mode spin is the kind of process kill ends.
- **R1 advisory 11, retained:** abort can close stdin between write and flush, producing a
  pre-existing `ValueError` class for closed-file I/O. The header/payload gap already had
  that class of race. Caller cancel state decides the outcome; no exception policy changed.
- **R2 advisory 3, exit-race coverage:** timing a child exit at 1.0 s against a 1.0 s
  threshold does not deterministically force either race order, or guarantee both orders
  across runs. The test requires exactly one permitted message and no thread exception;
  it does not prove exhaustive race coverage. Separate non-reader and immediate-exit tests
  deterministically witness the stall and ordinary-error behaviors.
- **R2 advisory 4, starvation:** capped polling estimates awake time. A gap of G seconds
  longer than five contributes five, so repeated such gaps can slow detection by roughly
  G / 5 relative to elapsed time. A long suspend likewise contributes up to five seconds,
  not zero. Continued polls of a still-pending operation continue accumulating; no
  hard wall-clock deadline or exact sleep subtraction is claimed.
- **R2 advisory 5, message:** the message says `data`, carries no waiting-frame/byte count,
  and reports rounded capped seconds, not full wall time including suspend. It uses
  `encoder_failed` and the existing stderr-tail fallback `no error output`. Per-byte
  acceptance during a pending write and actual encoding progress are not observed.
- **R2 advisory 6, timing margins:** tests use a one-second threshold, a four-second rescue,
  three-second file-readiness margins in abort/flush witnesses, and bounded thread joins.
  They can fail under extreme host scheduling delay; the measured call times above are
  not a guarantee under arbitrary contention. All eleven calls were under five seconds
  in this run. The outer pytest timeout is 120 seconds.
- The intermittent real-hardware stall cannot be provoked on demand. No real CPU-forced
  export or recurrence was run for this package; a recurrence is the remaining real witness.
  The default preference for NVENC on the CPU route is unchanged by owner direction.
- **POSIX is untested.** The implementation uses portable stdlib operations; the real-pipe
  and kill-release evidence in this cell is Windows evidence only.
- An encoder that accepts EOF and then hangs is covered by the unchanged finish deadline,
  not by a pending-I/O window. Renderer, analysis and decoder stalls are outside this scope.

## Verification loop and handoff

The loop confirmed buffered-write and close gaps in round 0, implemented and witnessed
R1-R3 in turn 2, then confirmed the suspend false positive on base code and the idle-arming
coverage hole with a planted mutation in turn 3. The abort exception-recorder concern was
rejected as already satisfied. Turn 4 confirmed the first-observation coverage hole with
the cap-removal mutation and corrected the affected docstrings. The executable watchdog
logic did not need another change in turn 4. Final units, lint, format and types passed;
the final docstring/source and scope pass found no additional in-envelope issue.

Reviewer A1: 0 critical, 1 major, 2 minor, 8 advisory. Reviewer A2:
**NO_NEW_CRITICAL_MAJOR**, 2 minor, 4 advisory. The two A2 minors are fixed here;
advisories and retained limits are disclosed above. Exact reviewer transcript, transport
and mechanical assertions remain dispatcher-owned, not independently re-verified by this
cell. No reverts, reopened findings, new dependency or frozen-interface changes occurred.

Owned paths for this turn are `encode.py` (sink docstrings/constants only), the units file,
the cumulative ledger and this report. Existing encode/bench and worker/process tests,
job code, GUI, interfaces and transport code outside the sink were not edited. No footage
was accessed and no output was directed outside this worktree. Test outputs remain under
their `tmp_path` inside `work/c58-4-*`. The dispatcher owns the commit, Reviewer B, final
gate, merge, and the architect's DR-115 / AD-32 register updates. This report transfers the
built candidate and cell evidence for those remaining acceptance steps.
