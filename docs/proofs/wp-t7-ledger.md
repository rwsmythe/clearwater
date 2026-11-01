# WP-T7 cumulative ledger

## Round 0: dispatch grounding

- Dispatch: session 1, turn 1; branch `wp-t7`, HEAD `facd98ee`, base main
  `c81831f9`. The worktree was clean before this turn.
- Read the dispatch recipe in full, APPLICATION.md, CLAUDE.md, pyproject.toml,
  the review/gate fill (including Part 2 GATE_CHECKS), and the model prompting
  standard. The supplied brief and turn-specific dispatch govern this rung.
- House form: no `pytester` / `runpytest` use found under `tests/`.
  `tests/test_conftest_guard.py:147` (`_run`) uses `sys.executable -m pytest`,
  copied/scrubbed environment, subprocess output capture and `check=False`.
  The new test follows this subprocess form with an independent hang ceiling.
- Inner configuration: `-c <absolute repository pyproject.toml>` retains the
  real gate options rather than copying their intended values into the test.
  `--confcutdir <inner directory>` isolates the planted tests from repository
  conftests. Each invocation gets its own directory and basetemp below the
  outer node's `tmp_path`; `PYTEST_ADDOPTS` is removed from the child environment.
  The sandbox shim is propagated only when the parent loaded it; gate-seat
  runs therefore do not load it. Inner stdout/stderr are saved under each
  invocation's directory as `pytest-output.txt`.
- One marker-free outer node runs a 0.01 s control and a 30 s planted sleep in
  separate invocations, each with `--timeout 2 -p no:cacheprovider`. Both inner
  files contain a second test that writes a sentinel. The control must pass
  both tests; the timeout must return nonzero in less than 15 s, name `Timeout`
  and the sleeping function in its output, and leave its sentinel absent.
  The subprocess ceiling also enforces 15 s. These are hang sanity bounds;
  the GREEN node's under-5 s qualification remains to be measured in turn 2.
- Reviewer A has not run; this is the required RED yield, not convergence.

## Turn 1: RED

The proving test was written before adding the dependency or any ini options.
The existing lock supplied pytest 8.4.2; the first `uv run` created this
worktree's `.venv` and installed the existing 61 packages. It ignored the
inherited main-tree `VIRTUAL_ENV`, as uv's log explicitly reports.

Command (PowerShell environment assignment is equivalent to the dispatch's
`PYTHONPATH=scripts` prefix; `PYTEST_ADDOPTS` removed):

```text
uv run pytest -q tests/test_gate_timeout.py --basetemp=work/wp-t7/tmp -p sandbox_mkdir_shim -p no:cacheprovider --durations=0
```

Evidence: `work/wp-t7/turn1-red.log`, exit 1. Summary lines:

```text
E       AssertionError: ERROR: usage: __main__.py [options] [file_or_dir] [file_or_dir] [...]
E         __main__.py: error: unrecognized arguments: --timeout .../control/test_planted.py
FAILED tests/test_gate_timeout.py::test_thread_timeout_exits_with_stack_and_under_bound_control
1.02s call tests/test_gate_timeout.py::test_thread_timeout_exits_with_stack_and_under_bound_control
1 failed in 1.13s
```

Both inner invocations returned usage exit 4 because the timeout plugin is
absent. Neither slept or reached its sentinel. The outer assertion failed on
the control's required successful exit. This is the expected missing-feature
RED, not a collection failure of the outer test. No control or timeout GREEN
claim is made this turn.

Light checks:

| Check | Observed result | Log |
| --- | --- | --- |
| `uv run ruff check tests/test_gate_timeout.py` | Exit 0, `All checks passed!` | `work/wp-t7/turn1-ruff.log` |
| `uv run ruff format --check tests/test_gate_timeout.py` | Exit 0, `1 file already formatted` | `work/wp-t7/turn1-format.log` |
| `uv run mypy` | Exit 0, `Success: no issues found in 148 source files` | `work/wp-t7/turn1-mypy.log` |

The final byte audit is recorded in `work/wp-t7/turn1-byte-audit.log`; both
new committed-path candidates have zero CR bytes. No product, dependency,
lock, ini, existing test, gate document or local configuration was changed.

## Turn 2: offline installation STOP (GREEN not reached)

The dispatcher supplied the end-of-turn-1 depth as **90,664 tokens** for
session `01a1983a-45de-7530-8ca2-8d53963ad4c7` (475,000-token window).

Added the authorized dev requirement `pytest-timeout>=2.3,<3` with the exact
commission provenance comment, and only the three authorized pytest ini
options: `timeout_method = "thread"`, `timeout_func_only = true`, and
`faulthandler_timeout = 300`. There is no default `timeout` value.

`uv lock --offline` succeeded, exit 0:

```text
Resolved 63 packages in 42ms
Added pytest-timeout v2.4.0
```

Evidence: `work/wp-t7/turn2-lock.log`. `uv.lock` was generated only by uv.
`git diff --stat -- uv.lock` reports:

```text
uv.lock | 14 ++++++++++++++
1 file changed, 14 insertions(+)
```

Evidence: `work/wp-t7/turn2-lock-stat.log`; the inspected diff adds only the
pytest-timeout dev-group reference, requirement metadata and 2.4.0 package
entry. No existing dependency version or artifact moved.

**[MAJOR, operational, in-envelope] STOP:** `uv sync --offline` failed,
exit 1. Evidence: `work/wp-t7/turn2-sync.log`. The exact error text is:

```text
Failed to download `pytest-timeout==2.4.0`
Network connectivity is disabled, but the
requested data wasn't found in the cache for:
https://files.pythonhosted.org/packages/fa/b6/3127540ecdf1464a00e5a01ee60a1b09175f6913f0644ac748494d9c4b21/pytest_timeout-2.4.0-py3-none-any.whl
```

Recommended disposition: at the dispatcher seat, make that exact locked
wheel artifact available to the cell's shared uv cache, then resume the
offline sync. Resolution metadata is now accessible, but the artifact is
not accessible to this sync. No alternative install, manual lock edit,
network attempt or cache mutation was attempted after the failure.

As explicitly directed by the turn-2 dispatch's "If it still fails, STOP"
instruction, no GREEN, behavior probe, document update, light runner or
harness gate was attempted after the sync failed. The proving test is
unchanged. The dependency/configuration work is retained for the dispatcher
to commit by pathspec. This is an incomplete installation rung, not a
completion or review-convergence claim. `git diff --check` exited 0; byte
counts for all three changed files are recorded in
`work/wp-t7/turn2-byte-audit.log` (zero CR).

## Turn 3: GREEN

The dispatcher supplied end-of-turn-2 depth **108,375 tokens** and reported
installing the locked package online at its seat. This turn began on
`53b4e4b2` with a clean worktree. Executed version checks confirm
pytest-timeout **2.4.0**, pytest **8.4.2**, and pytest-xdist **3.8.0**.
`uv sync --offline` now exits 0 (`Resolved 63 packages in 1ms`, `Audited 62
packages in 3ms`); evidence: `work/wp-t7/turn3-sync.log`. The prior
package-access STOP is RESOLVED. No further dependency or lock change was
needed. The existing lock diff remains exactly 14 additions, exclusively
pytest-timeout (turn-2 stat/diff evidence above).

### GREEN proof and parallel qualification

With `PYTHONPATH=scripts` and `PYTEST_ADDOPTS` unset:

```text
uv run pytest -q tests/test_gate_timeout.py -p sandbox_mkdir_shim -p no:cacheprovider --basetemp=work/wp-t7/tmp --durations=0
```

Exit 0; `work/wp-t7/turn3-green.log`:

```text
3.13s call tests/test_gate_timeout.py::test_thread_timeout_exits_with_stack_and_under_bound_control
1 passed in 3.16s
```

The inner control's saved output is `2 passed in 0.02s`; its later-test
sentinel exists. The expired invocation prints `Timeout`, `Stack of
MainThread`, and the `test_planted_sleep` frame. Its later-test sentinel
is absent. The committed assertions all passed, including the nonzero exit
and return in less than 15 s rather than the planted 30 s sleep.
Outputs: `work/wp-t7/tmp/test_thread_timeout_exits_with0/{control,expired}/pytest-output.txt`.

The same node was explicitly qualified with the parallel leg's selection
and flags, rather than relying on its serial light-run duration:

```text
uv run pytest -q -n 4 --timeout 600 -m "not gpu and not footage and not gui and not slow and not fullclip" tests/test_gate_timeout.py --basetemp=work/wp-t7/tmp-parallel-proof -p sandbox_mkdir_shim -p no:cacheprovider --durations=0
```

Exit 0; `work/wp-t7/turn3-parallel-proof.log`:

```text
3.19s call tests/test_gate_timeout.py::test_thread_timeout_exits_with_stack_and_under_bound_control
1 passed in 4.65s
```

The node remains marker-free and under 5 s in the parallel leg. This is
test-infrastructure qualification, not a product performance figure or the
final full two-leg gate. The committed test needed no further edits.

### Three facts: executed confirmation

Disposable probe runner: `work/wp-t7/run_turn3_probes.py`; final output
`work/wp-t7/turn3-probes-final.log` exits 0 with `All three behavior probes
passed their assertions.` All child runs use the real `pyproject.toml`,
isolated work directories, fresh basetemps, the sandbox shim and no cache
provider. Probe settings override only the explicitly described time bounds.
The installed source excerpts are saved in
`work/wp-t7/turn3-probes-final/installed-source.txt`.

1. **Thread exit and xdist recovery.** The committed GREEN proof executes
   the later-test sentinel control and confirms process termination on expiry.
   Installed `.venv/Lib/site-packages/pytest_timeout.py:505-542`,
   `timeout_timer`, flushes streams and calls `os._exit(1)`; `dump_stacks`
   at lines 545-558 excludes the timer thread itself.

   An inner `--timeout 2 -n 2 -v` invocation contains the planted 30 s
   sleeper and twelve sentinel-writing survivor tests. It exits 1 and
   finishes rather than hanging; all twelve survivor sentinels exist.
   Exact evidence lines from `work/wp-t7/turn3-probes-final/xdist/output.log`:

   ```text
   timeout: 2.0s
   timeout method: thread
   timeout func_only: True
   replacing crashed worker gw0
   worker 'gw0' crashed while running 'work/wp-t7/turn3-probes-final/xdist/test_probe.py::test_00_planted_sleep'
   FAILED test_probe.py::test_00_planted_sleep
   1 failed, 12 passed in 3.77s
   ```

   The subprocess wall figure is 4.391 s. The initial `-q` probe also
   finished (`1 failed, 12 passed in 3.47s`), but its disposable runner's
   assertion expecting the worker-replacement message failed: quiet mode
   suppresses that message. Increasing verbosity supplied the missing
   evidence without changing product code or gate commands. Original
   evidence remains in `work/wp-t7/turn3-probes.log` and
   `work/wp-t7/turn3-probes/xdist/output.log`.

   **Observed output limitation:** neither xdist parent log contains the
   timeout plugin's `Timeout` / `Stack of` dump. This does not contradict
   the standalone proof; the parent did not retain that worker output in
   these runs. A dedicated follow-up combining `-n 2 --timeout 2 -o
   faulthandler_timeout=1` confirms the earlier **core** dump does reach the
   parent and includes the sleeping frame, followed by the same completed
   crash/failure result. Evidence:
   `work/wp-t7/turn3-xdist-diagnostic.log` (probe assertions exit 0) and
   `work/wp-t7/turn3-probes-xdist-diagnostic/output.log`:

   ```text
   1 failed, 12 passed in 3.39s
   Timeout (0:00:01)!
   ... line 5 in test_00_planted_sleep
   ```

   Therefore preserve the earlier core dump when an xdist worker times
   out; do not interpret completion of the other nodes as a successful
   leg. The gate text records this behavior and CHARC's STOP/re-run rule.

2. **Function-only timing leaves fixture setup un-timed.** A session
   fixture sleeps 3 s under `--timeout 2`; its fast test passes. The output
   `work/wp-t7/turn3-probes-final/session-fixture/output.log` shows:

   ```text
   3.00s setup work/wp-t7/turn3-probes-final/session-fixture/test_probe.py::test_fast_body
   1 passed in 3.02s
   ```

   Installed `pytest_timeout.py:178-199`, `pytest_runtest_protocol`, starts
   the whole-protocol timer only for `func_only is False`; the call hook
   at lines 202-216 wraps only the body for `func_only is True`. This
   source and the synthetic fixture prove the session-trim setup is outside
   this timer without invoking either footage fixture.

3. **Faulthandler dumps without failing or interfering with thread.** An
   inner two-second test uses `--timeout 10 -o faulthandler_timeout=1 -s`.
   It exits 0; `work/wp-t7/turn3-probes-final/faulthandler/output.log` shows:

   ```text
   1 passed in 2.01s
   Timeout (0:00:01)!
   ... line 4 in test_diagnostic_sleep
   ```

   Installed `_pytest/faulthandler.py:75-88` schedules the core watchdog
   with `dump_traceback_later(timeout, file=stderr)` and cancels it after
   the protocol, retaining the API's `exit=False` default. The same
   mechanic uses the configured 300 s in gate runs; no 300 s sleep was
   needed. The combined xdist probe above independently confirms that
   this earlier dump coexists with the later thread timeout. It also
   covers fixture setup diagnostically without imposing a fixture bound.

### Gate documentation and light checks

`CLAUDE.md` changes only the Tests convention line: parallel 600 s,
serial 1200 s, fullclip 2400 s. GATE_CHECKS changes the three commands
only by their `--timeout N` flags, retains every selection expression,
adds the observed process/worker behavior and STOP/re-run sentence, and
copies CHARC item 3's standing rule and scheduling sentence verbatim.
Neither the fullclip suite nor any footage/GUI/GPU node was run.

| Check | Observed result | Evidence |
| --- | --- | --- |
| `uv run ruff check .` | Exit 0, `All checks passed!` | `work/wp-t7/turn3-ruff.log` |
| `uv run ruff format --check .` | Exit 0, `293 files already formatted` | `work/wp-t7/turn3-format.log` |
| `uv run mypy` | Exit 0, `Success: no issues found in 148 source files` | `work/wp-t7/turn3-mypy.log` |
| `uv run python -m unittest discover -s tests/harness` | Exit 1; 382 tests, 4 failures, 125 errors, 4 skips | `work/wp-t7/turn3-harness.log` |
| Same harness command, work-local temp plus existing mkdir shim | Exit 1; 382 tests, 3 failures, no errors, 1 skip | `work/wp-t7/turn3-harness-sandbox.log` |

**[MAJOR, out-of-envelope harness/environment finding]** The required
harness gate is NOT GREEN at this seat. The plain run fails extensively
on restricted-token 0o700 temp-directory permissions. For the second run,
TMP/TEMP/TMPDIR point to `work/wp-t7/harness-temp`; a disposable
`work/wp-t7/harness-runtime/sitecustomize.py` imports the existing
`sandbox_mkdir_shim`, with that directory and `scripts` on PYTHONPATH.
No harness test, script or site-packages file was edited. The remaining
three named failures are:

- `test_subprocess_no_site_packages_runs_core`: its `python -S` child
  disables site initialization, creates its own 0o700 temp directory, and
  fails with `PermissionError [WinError 5]` under that directory.
- `test_bash_cc_preflight_refusal_positive_control`: expected
  `CLAUDE_CODE_GIT_BASH_PATH target not found: Z:\definitely-missing\bash-cc.exe`
  is missing from launcher stdout, which stops after the Claude CLI check.
- `test_resolve_main_checkout_root_falls_back_when_git_unavailable_or_fails`:
  the deliberately work-local `not-a-git-repo-*` temp directory is actually
  inside this repository; git resolves the main checkout rather than the
  expected unchanged temp path. This failure is specific to the adapted
  temp-root conditions, not evidence of a new launcher defect.

These failures are outside the owned-file envelope. **Disposition: STOP
and route the harness gate to the dispatcher seat**, using its ordinary
non-sandbox temp context; do not change existing harness code or weaken
assertions. The named failures and logs are the cheap reproduction.
Reviewer A/B and the final two-leg/fullclip-collection gate remain pending
at the dispatcher seat; this turn makes no full-package completion claim.

### Turn 3 verification loop

| Suspected | Independent confirmation | Disposition |
| --- | --- | --- |
| Plugin still unavailable after dispatcher install | Version query, clean offline sync, GREEN proof | REJECTED; access STOP resolved |
| Thread expiry permits later tests in the same process | Control sentinel present; expired sentinel absent; installed `os._exit(1)` | CONFIRMED termination; required assertions pass |
| Xdist cannot finish after a timeout | Worker replacement message and all twelve survivor sentinels | REJECTED; exit 1 with 12 passes |
| Xdist quiet output must announce replacement | First probe assertion fails; verbose probe prints it | REJECTED; disposable probe corrected, no committed test change |
| Timeout worker's dump is guaranteed in parent output | Both parent logs omit it; earlier core dump reaches parent in combined probe | CONFIRMED limitation; gate wording names it and preserves core dump |
| Session setup is timed despite function-only setting | 3.00 s setup passes with 2 s timeout, call-hook source agrees | REJECTED |
| Core diagnostic dump fails or conflicts with the test timeout | Standalone diagnostic test passes; combined xdist run dumps then times out | REJECTED |
| Harness failures might be introduced by timeout/doc changes | Temp permission traces, `-S` child, launcher stdout and nested-repo fixture explain named failures; owned harness paths unchanged | ROUTED; ordinary dispatcher-seat gate required |
| Changed fill's working-copy line endings violate the LF lock | Byte audit found CRLF in the checked-out fill | FIXED by LF normalization; final byte and text-difference audits repeated |

A full final source/assertion review found no further in-envelope issue.
Ruff/format/mypy and the requested proof are green; the harness exception
above remains explicit. Final diff/lock/byte audit evidence is saved under
`work/wp-t7/turn3-{scope-audit,byte-audit,diff-check}.log`; all this turn's
changed files have zero CR bytes. No frozen interface, product code,
existing test, marker, footage path or local configuration was changed.

## Turn 1 facts research (historical: source-confirmed then, execution pending then)

Research date: 2026-11-01. The primary sources below were inspected this turn.
Plugin facts concern the published 2.4.0 source, **not an installed or
uv-resolved plugin**; the package-access finding below prevents that claim.

1. **Thread expiry terminates the process.** In the pinned
   [pytest-timeout 2.4.0 source](https://github.com/pytest-dev/pytest-timeout/blob/2.4.0/pytest_timeout.py#L284),
   `pytest_timeout_set_timer` (lines 284-314) starts a `threading.Timer`.
   `timeout_timer` (lines 471-507) prints captured output and thread stacks,
   flushes streams, then calls `os._exit(1)` in `finally`. `dump_stacks`
   (lines 509-523) walks current frames, excluding the timer thread itself.
   Thus later tests and normal teardown in that process do not run. The
   committed proof asserts the absent later-test sentinel; execution awaits
   turn 2. The [plugin documentation](https://pypi.org/project/pytest-timeout/)
   agrees under Timeout Methods / thread.
   Installed xdist's `.venv/Lib/site-packages/xdist/dsession.py` names
   `worker_errordown` at line 238, `handle_crashitem` at line 432, and worker
   replacement at line 264. These are the follow-up probe anchors; actual
   `-n 4` crash reporting, restart and completion remain UNVERIFIED until
   turn 2. The CHARC thread-method ruling governs interpretation: a timed-out
   leg is a STOP with node and stacks, followed by a rerun after its fix.
2. **Function-only timing excludes fixture setup and teardown.** In that
   same pinned plugin source, `pytest_runtest_protocol` (lines 167-181) starts
   a timer only when `func_only is False`; `pytest_runtest_call` (lines
   189-202) starts/cancels it around the call when `func_only is True`.
   `get_env_settings` reads the ini value at line 350. Therefore unmarked
   session-fixture setup, including the named session trims, falls outside
   this plugin timer. Marker overrides can change this behavior. Installed
   source confirmation awaits turn 2; no footage fixture was invoked.
3. **Core faulthandler dumps without failing.** Installed pytest 8.4.2's
   `.venv/Lib/site-packages/_pytest/faulthandler.py:75-88`,
   `pytest_runtest_protocol`, calls `faulthandler.dump_traceback_later(timeout,
   file=stderr)` and cancels it after the test protocol. It neither raises
   a test failure nor passes `exit=True`. The [Python 3.12 API documentation](https://docs.python.org/3.12/library/faulthandler.html#faulthandler.dump_traceback_later)
   specifies the default `exit=False` and watchdog implementation; this is
   distinct from the plugin's `threading.Timer`. Core covers setup/call/
   teardown, so even long setup can receive a diagnostic dump while remaining
   un-timed by pytest-timeout. A configured value 300 schedules this dump
   after 300 s. Coexistence with the installed timeout plugin will be checked
   in turn 2 using a shortened diagnostic interval, without a 300 s sleep.

## Turn 1 package-access finding (historical; resolved in turn 3)

**[MAJOR, operational, in-envelope]** Make pytest-timeout available to uv
before the dependency/GREEN rung. Recommended: restore the existing uv
package connection, or arrange a verified package in its writable cache.
No dependency was added or installed by this research.

- `uv pip index versions pytest-timeout`: exit 2; this installed uv has no
  `pip index` subcommand. Evidence: `work/wp-t7/turn1-index.log`.
- Fallback `uv pip install --dry-run pytest-timeout`: exit 2 after three
  retries; fetching `https://pypi.org/simple/pytest-timeout/` failed with a
  tunnel/connect error, ending in `os error 10061`. Evidence:
  `work/wp-t7/turn1-resolve.log`.
- `uv pip install --dry-run --offline pytest-timeout`: exit 1; no solution
  because pytest-timeout was not found in the cache. Evidence:
  `work/wp-t7/turn1-resolve-offline.log`.
- The accessible [PyPI metadata and release history](https://pypi.org/project/pytest-timeout/#history)
  list 2.4.0 (MIT, Python >=3.7; published 2025-05-05) as the latest release.
  Its tagged source was used above. This establishes a candidate compatible
  with Python 3.12 / pytest 8.4.2, not what uv has resolved. Final resolution
  and installed-source checks are deferred to turn 2.

## Turn 1 verification-loop record (historical)

| Suspected | Independent confirmation | Disposition |
| --- | --- | --- |
| Gate timeout support is absent | Both child runs reject `--timeout`, exit 4 | CONFIRMED; intentionally RED; fix commissioned for turn 2 |
| Thread expiry stops the whole invocation | Tagged source calls `os._exit(1)`; official docs agree | SOURCE-CONFIRMED; executed sentinel proof pending |
| Function-only timer would include trim setup | Call hook and protocol hook have mutually exclusive `func_only` conditions | REJECTED in the unmarked fixture path; installed check pending |
| Diagnostic timer fails a test or shares the timeout timer | Installed pytest calls the core API without `exit=True`; distinct plugin timer | REJECTED by source; coexistence execution pending |
| uv could obtain the package this turn | Online dry-run fails connection; offline dry-run misses cache | CONFIRMED access blocker for next rung; disclosed |

One source/assertion pass found no additional test-code issue. GREEN,
Reviewer A, Reviewer B and the final gate remain explicitly outstanding.

## Cumulative review rounds

| Round | Critical / major / minor | In / out | NEW / REOPENED | Reverts | Product / tests | Reviewer transport | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 (grounding, no review) | 0 / 0 / 0 review findings | N/A | N/A | 0 | No product; new test only | Not run | RED rung recorded; yield |

The operational package-access finding above is not a Reviewer A finding
and does not open or count a review round.

## Dispatcher-read depth

| Session / turn | Depth supplied by dispatcher | Boundary |
| --- | --- | --- |
| 1 / 1 | 90,664 tokens (dispatcher supplied at turn 2) | RED yield; evaluate near 200K, re-seat boundary near 250K |
| 1 / 2 | 108,375 tokens (dispatcher supplied at turn 3) | Offline sync STOP; remaining GREEN rung held |
| 1 / 3 | Pending dispatcher fill; no estimate | GREEN proof/facts yield; harness gate routed to dispatcher seat |
