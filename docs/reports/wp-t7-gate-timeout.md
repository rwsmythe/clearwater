# WP-T7: gate timeout protection

Added dev dependency `pytest-timeout>=2.3,<3`, resolved to **2.4.0** (MIT,
CHARC `97d5abbf`, N13). The uv-generated lock diff is **14 additions**:
the package entry and two dev references; no other dependency moved
(`work/wp-t7/turn2-lock-stat.log`, turn-3 lock audit).
The only new pytest ini options are `timeout_method = "thread"`,
`timeout_func_only = true`, and `faulthandler_timeout = 300`; no default
`timeout` is configured. GATE_CHECKS and CLAUDE.md carry per-leg bounds
600 / 1200 / 2400 s. The serial-isolation standing rule is recorded verbatim
with provenance. No product code or frozen interface changed.

The marker-free proving node uses the real repository config. Its control
has a **2.5 s session fixture**, a fast body, and a later-test sentinel;
the negative run sleeps 30 s under a 2 s timeout and must exit before its
later test runs. Separate subprocesses run concurrently in isolated temp
directories so the node remains under 5 s.

| Turn-4 measurement | Result | Evidence under `work/wp-t7/` |
| --- | --- | --- |
| Light proof | `1 passed in 3.16s`; node call 3.12 s; command wall 4.028 s | `turn4-green.log`, `turn4-green-result.log` |
| Parallel-leg proof (`-n 4 --timeout 600`, gate expression) | `1 passed in 4.57s`; node call **3.13 s**; command wall 5.623 s including worker startup | `turn4-parallel.log`, `turn4-parallel-result.log` |
| Parallel inner control / expired invocation | Exit 0 / 1; wall 3.125 / 2.562 s; control `2 passed in 2.52s` | `tmp-turn4-parallel/popen-gw0/test_thread_timeout_exits_with0/{control,expired}/pytest-{result,output}.txt` |
| Copied-config ablation: remove `timeout_func_only` | `FAILED tests/test_gate_timeout.py::test_thread_timeout_exits_with_stack_and_under_bound_control`; `1 failed in 2.73s`, at `assert control.returncode == 0` with a timeout in `slow_session` | `turn4-ablation.log`, `turn4-ablation/output.log` |

The real config was never edited for the ablation. Against AD-30, the
commission retains the 15 s per-subprocess timeout in this parallel node;
Reviewer B cleanup removes the redundant wall assertion that cannot run on
`TimeoutExpired`. The current expired run is 2.703 s (5.55x ceiling ratio),
and the control is 3.297 s (4.55x). These are planted-hang checks, not product
timing bounds; the current node call is 3.30 s, under 5 s. The proof now
explicitly pins thread, func-only, the 300 s diagnostic and absence of a
default timeout by parsing the real ini with `tomllib`, including where
Windows would default to thread without SIGALRM.

The three runtime facts were verified with pytest 8.4.2 / xdist 3.8.0:

- **Thread expiry exits the process.** The negative proof prints `Timeout`,
  `Stack of MainThread` and `test_planted_sleep`; its later-test sentinel is
  absent while the control's exists. Under `-n 2`, the probe prints
  `replacing crashed worker gw0`, identifies the crashed sleeper, and finishes
  `1 failed, 12 passed in 3.77s` (`turn3-probes-final/xdist/output.log`).
- **Function-only timing excludes all fixture setup and teardown.** The new
  control and ablation pin the setting. The earlier synthetic session probe
  shows `3.00s setup` and `1 passed in 3.02s` under a 2 s bound. Reviewer A's
  session/function-setup/function-teardown probe also passed: `4 passed in
  9.02s`. Installed `pytest_timeout.py:178-216` installs the function-only
  timer around `pytest_runtest_call`, outside fixture phases.
- **Faulthandler is diagnostic and coexists with thread.** A two-second test
  under `--timeout 10 -o faulthandler_timeout=1` prints `Timeout (0:00:01)!`
  and its sleeping frame yet finishes `1 passed in 2.01s`
  (`turn3-probes-final/faulthandler/output.log`). A combined xdist probe
  retains the earlier dump on stderr and finishes `1 failed, 12 passed in
  3.39s` (`turn3-probes-xdist-diagnostic/output.log`). The worker's timeout
  plugin dump was absent from the parent logs; every leg must capture stderr.

Reviewer A round 1 (Claude Opus, high) returned
**`VERDICT: NO_NEW_CRITICAL_MAJOR`**. All seven findings were accepted in
the terminating cleanup; evidence is
`C:/Users/rwsmy/clearwater-review-evidence/wp-t7/r1/review.txt`.

| Finding | Severity | Disposition |
| --- | --- | --- |
| F1: control did not pin func-only | Minor | Added slow session fixture, concurrent inner runs, method-fallback comment; ablation now fails |
| F2: thread timeout needs the GIL | Minor | Qualified timeout behavior and documented the diagnostic/stall-watch fallback |
| F3: stderr capture omitted | Minor | Every leg command now carries its own log redirect with `2>&1` (CHARC `823921b8`); CHARC records F2 as a LIMIT in DR-109's close |
| F4: all fixtures are un-timed | Advisory | Documented session/function setup and teardown scope |
| F5: long nodes produce diagnostic noise | Advisory | Documented that a dump alone is neither failure nor STOP |
| F6: standing-rule provenance | Advisory | Appended `(CHARC 97d5abbf, 2026-11-01)` without altering the quoted rule |
| F7: 15 s bound against AD-30 | Advisory | Retained authorized bounds; recorded measured margins above |

Limits: a timer thread needs the GIL. Reviewer A's Windows native
GIL-holding probe (`PyDLL` Sleep 8 s, then Python sleep; timeout 2 s,
diagnostic interval 1 s) exited 1 after **8.5 s**; the timer fired only after
the native call returned, while faulthandler dumped on time. A native
GIL-holding deadlock therefore relies on the 300 s dump and the stall watch
for STOP, rather than automatic timeout termination. Fixture hangs likewise
remain outside the function timeout. Legitimate fullclip/slow-trim dumps
are diagnostic noise and do not alone justify STOP. These accepted limits
are explicit in GATE_CHECKS; the GIL probe figures are Reviewer A's executed
evidence, not a new cell-side OS-specific probe.

Under xdist, the worker terminal-writer timeout dump IS absent; correlate
the parent's `worker 'gwN' crashed while running '<node>'` line with the
core stack on stderr, which has no node ID and fires once 300 s after setup
starts, so a later hang can have only a stack of earlier normal work.
Collection/import, session hooks, interpreter exit and controller shutdown
waits are outside the timed protocol: only the stall watch catches those
hangs. On Windows `os._exit` leaves spawned export-worker/FFmpeg children
alive; identify and end that run's leftovers before rerunning with a fresh
basetemp. The terminated process loses summary/durations/JUnit output and
exits 1 like an ordinary failure: use its `+++ Timeout +++` signature or the
xdist crash line; the xdist controller can still finish with its own summary.
The stall watch investigates unchanged logs after 5 minutes (15 for
fullclip), checks node/CPU/file progress, and stops only after a further
5 minutes without progress; diagnostic noise alone is not STOP.

## Reviewer B

Claude Opus / high on `1d541378` returned **`VERDICT: NO_NEW_CRITICAL_MAJOR`**;
claims 1-5 HOLD. Its collection-only commands with flags and redirects exit
0 and partition 7,377 nodes (6,129 parallel + 1,241 serial + 7 fullclip).
Evidence: `C:/Users/rwsmy/clearwater-review-evidence/wp-t7/B/review.txt`.
Five minor and five advisory findings received the dispatcher's binding
dispositions:

| Finding | Severity | Disposition |
| --- | --- | --- |
| F1: undefined stall watch | Minor | Accepted; thresholds, progress checks and investigation/STOP distinction defined |
| F2: xdist dump availability and timing | Minor | Accepted; terminal-writer loss, crash-line correlation and one-shot 300 s dump documented |
| F3: out-of-protocol hangs | Minor | Accepted; collection/hooks/exit/controller limits documented |
| F4: surviving children | Minor | Accepted; run-specific cleanup and fresh basetemp required before rerun |
| F5: remaining ini facts unpinned | Minor | Accepted; real-config assertions pin all three values and no default timeout |
| F6: weak stack match | Advisory | Accepted; expired output must contain `Stack of` and the sleeping function |
| F7: unreachable elapsed assertion | Advisory | Accepted; removed it, retained 15 s subprocess timeout and ratios above |
| F8: fullclip isolation | Advisory | Accepted; appended CHARC's fullclip extension without changing the verbatim rule |
| F9: lost timeout output | Advisory | Accepted; documented terminated-process losses/signature; xdist controller may retain a summary |
| F10: sandbox shim branch | Advisory | Declined by dispatcher; required for the cell and inert at the gate |

Turn-6 light proof: `1 passed in 3.35s`, 3.30 s call
(`work/wp-t7/turn6-green.log`); ruff/format/mypy pass. No harness run was
made in the sandbox this turn.

Light proof, parallel qualification, ruff, format and mypy pass. The
dispatcher reported the ordinary-seat harness run on `e4938910`:
`Ran 382 tests ... OK (skipped=1)`; the sandbox harness STOP is resolved and
was not re-run this turn. Final scope/byte audits record only owned paths
and zero CR bytes. Reviewer B has returned and its bounded cleanup is
complete; the final candidate gate remains at the dispatcher seat. This
report contains no final gate figures.
