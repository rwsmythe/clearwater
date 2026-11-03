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
