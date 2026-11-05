# WP6.3b release workflow: implementation record

Status: build part 1 implemented; native cleanup verification has one restricted-token
residual. This is an incremental report, not the package acceptance or an N13 verdict.
The workflow, FFmpeg lock/notices, exception hooks, cache variables, smoke, ZIP and
release-document changes are still pending their later dispatched turns.

## Round and turn ledger

Build turns and round 0 below are not Reviewer A rounds. Reviewer A is the dispatcher's
Claude pass; no review verdict is claimed here. Context depth is dispatcher-read.

| Turn / round | Work and disposition | Severity / envelope | NEW / REOPENED; reverts | Product vs test changes | Dispatcher-read depth |
| --- | --- | --- | --- | --- | --- |
| Turn 1 / round 0 | Read-only design return; no files or processes. CHARC accepted the read-back and Q2-Q4. Source-worker hook site and guide section-3 launch paragraph granted; ADV-3 corrected to a live child that times out without reporting its PID. Q1 ruled BtbN month-end autobuild `autobuild-2026-10-31-12-59`, subject to the brief's source, configuration, hash and retention conditions. | 0 critical, 1 major, 2 minor; all 3 in-envelope questions, now ruled. | 3 NEW, 0 REOPENED; no reverts. | None. | 146,885 / 475,000 at turn end, supplied in dispatch 2. |
| Turn 2 / build part 1 | ADV-1 publication outcome, ADV-3 no-PID fallback coverage/mutant, D4(d) statement guard. One native `taskkill` residual remains for the seat. | No Reviewer A findings yet; native process-control denial disclosed below. | No review reopenings. Temporary test-only kill-removal mutant restored. | Product: publication block and executable-finder guard. Tests: local wheel, fault injection, live child tree and layout/platform cases. | Turn-end figure pending dispatcher reading. |
| Turn 3 / build part 2, Group A yield | Fatal reporter, GUI notification, source-worker hook site and isolated tests. STOP on bootstrap logging's transitive NumPy dependency; Group B not started. | No Reviewer A round. Self-check: 1 MAJOR scope STOP; 1 MINOR validation-rule question; one final worker-test residual for the seat. | All new observations, no review reopenings or product reverts. Rotation and the regression fixture's logging stub corrected in-envelope. | Product: entry reporter, interpreter catch, GUI callback and the single granted worker site. Tests: new hook suite and frozen-entry regression. | Fresh session; final depth pending dispatcher reading, never estimated by the cell. |

This turn bundles the three changes explicitly commissioned by dispatch 2; the seat
commits them. No git write was performed by the cell.

## Build part 1 changes

### ADV-1: publication is retained after a later failure

Only `_install_locked`'s publication/post-publication block changed. The protected block
includes the actual rename, clearing staging ownership and optional directory syncs.
When an exception returns after a real rename, disappearance of the staging tree and
presence of the destination establish publication. A pre-publication error still reaches
the existing failure and staging-cleanup path. After publication, `Exception` and
`KeyboardInterrupt` keep the installed result and restart message. One fixed warning is
attempted; it does not stringify the failing exception, and a failing/interrupted warning
handler cannot change success. Cleanup never receives the published tree in these cases.

The regression fixture uses a real synthetic wheel from local bytes, the real unpacker,
manifest writer, validators and rename. Only transport is replaced; it opens no socket.
Faults occur after the real rename, at the post-publication directory-sync phase, and
while formatting or delivering a warning. Tests require the success/restart text, kept
destination, no cleanup, one warning where delivery works and a clean full pack check.

RED: all seven new cases failed against the original product code. GREEN: all seven
pass after the change. Existing installer cases in the requested runs also pass apart
from the separately identified native ADV-3 test.

### ADV-3: force the no-PID cleanup fallback

The existing mapped-image test's cleanup was moved unchanged to the test-only helper
`_finish_mapped_child`; the original test still calls it after releasing its child.
The new Windows test launches a real child with descendants, observes a readiness file
written by the deepest child that contains no PID, leaves the PID-report file absent and forces the helper's initial
wait to expire after 0.2 seconds. It checks launcher termination and no surviving
descendant. Independent teardown kills and waits for captured children even when the
assertion or mutant fails.

Two process-control modes are explicit: native `taskkill /T /F /PID`, with diagnostic
output saved as `tree-kill.log`, and a controlled boundary that validates the same command
and terminates the real captured process tree through psutil. The controlled mode proves
the fallback branch and live-child cleanup within this restricted token; it is not
reported as proof of native taskkill success.

Mutation method: a temporary local edit removed ONLY the helper's `subprocess.run`
tree-kill call, leaving launcher-only `child.kill()` in place. The controlled live-child
test failed with `no-PID cleanup left an orphan`; its independent teardown completed.
The call was restored, and the identical controlled case passed. No mutant remains.
An earlier native-mode mutant also failed, but it is not used as a discriminating proof
because this sandbox also denies the unmutated native command.

Native residual: `taskkill` prints `ERROR: Access denied` under this run's restricted
token. The original fallback then kills the launcher but leaves descendants until the
new test's independent teardown. The native assertion remains enabled and failing;
there is no new skip or claim that the native path passed. The seat must run this case
outside the cell sandbox and disposition it before acceptance.

### D4(d): explicit platform guard

`find_executable` now assigns its suffix through the AD-36 statement-form guard.
Four cases cover win32/darwin and root/nested executable layouts using injected platform
values and real temporary files. These passed before and after the refactor. There is
no functional RED for a behavior-preserving spelling change; no artificial failure is
claimed. Both requested mypy platform checks pass.

## Validation evidence

All runner output is retained under `work/c63b-2-logs/` in this worktree. Every pytest
invocation used `PYTHONPATH=scripts`, `-p sandbox_mkdir_shim`, `-p no:cacheprovider`,
offscreen Qt and a fresh worktree-local basetemp. No frozen executable, build or GUI was
launched. Existing source-entry tests retain their redirected roots and GUI blockers.

| Evidence file | Result read from the run |
| --- | --- |
| `red-adv1.log` | Exit 1: 7 failed, 104 deselected; original publication/warning behavior distinguished. |
| `red-adv3-controlled-mutant.log` | Exit 1: 1 failed, `no-PID cleanup left an orphan`; temporary tree-kill deletion. |
| `d4-before.log` | Exit 0: 4 passed, 64 deselected on the original expression guard. |
| `green-focused-restored.log` | Exit 0: 12 passed, 169 deselected; seven ADV-1 cases, controlled ADV-3 and four D4(d) cases. |
| `ruff-check-final.log` | Exit 0: `All checks passed!` on the four changed Python files. |
| `ruff-format-final.log` | Exit 0: `4 files already formatted`. |
| `mypy.log` | Exit 0: `Success: no issues found in 164 source files`. |
| `mypy-darwin.log` | Exit 0: `Success: no issues found in 164 source files`. |
| `pytest-combined.log` | Exit 1: `1 failed, 180 passed in 18.69s`; sole failure is native ADV-3 taskkill denial. Basetemp `work/c63b-2`. |
| `pytest-installer-alone.log` | Exit 1: `1 failed, 112 passed in 12.44s`; same sole failure. Basetemp `work/c63b-2m`. |
| `pytest-combined-final.log` | Exit 1: `1 failed, 180 passed in 14.46s`; same sole native failure on final Python code. Fresh basetemp `work/c63b-2-final`. |
| `pytest-installer-alone-final.log` | Exit 1: `1 failed, 112 passed in 12.55s`; same sole native failure on final Python code. Fresh basetemp `work/c63b-2m-final`. |
| `diff-check.log` | Exit 0: no whitespace errors. |

Native-command diagnostics from both required pytest runs independently contain
`ERROR: Access denied` in their native case's `tree-kill.log`. Neither run reports a
teardown error: the independent cleanup verifies that no captured descendant remains.

The inherited `VIRTUAL_ENV` names the main checkout. uv warns that it ignores that value
in favor of this worktree's `.venv`; PowerShell renders the warning as NativeCommandError
records even when the runner exits 0. This is environment noise, not a runner failure.
The native taskkill denial is the only test residual in the requested runs. The earlier
ruff import-order finding was fixed and the final lint/format checks are clean.

## Verification-loop record and limits

| Suspected issue | Independent confirmation | Disposition |
| --- | --- | --- |
| A failure after a real rename reports failure/cancellation or attempts staging cleanup. | Seven-case RED run, including both exception types at the rename boundary and sync phase. | Fixed in the owned publication block; focused tests and required installer runs confirm the new cases pass. |
| Warning formatting/handlers can undo publication success. | Unprintable OSError and raising/interrupted warning handler controls. | Fixed by one fixed-message best-effort warning; controls pass. |
| The no-PID fallback could silently lose its tree kill. | Removing only that call leaves real descendants and fails the controlled case. | Regression coverage added; mutant restored; controlled GREEN observed. Native verification remains a seat residual. |
| A readiness signal from the parent could precede creation of the deepest interpreter, making the descendant census incomplete. | Traced the Windows launcher/Popen sequence during final inspection. | Moved readiness signaling into the deepest child; repeated both requested module runs on fresh basetemps. Counts and the sole native residual are unchanged. |
| Platform-guard refactoring could lose a release layout or suffix. | Four independent file-layout/platform cases before and after the edit; native and Darwin mypy. | Rejected as a regression: behavior preserved. |

The final inspection found no further issue within these three commissioned items.
No frozen interfaces, dependencies or entry modules changed. No external network fetch,
git write, tag, push, workflow action, synthetic desktop input, footage access or write
to the owner's real application profile was performed. The remaining package work is
not claimed complete. The report will gain action SHAs, FFmpeg component/source rows,
artifact notices coverage, smoke/ZIP figures and seat V4 evidence in later turns.

## Turn 3: Group A implementation and scope STOP

This is the dispatch-3 Group A yield, not a completion claim for Group A or the
work package. Group B (bootloader flag and frozen cache variables) is untouched.
The seat commits; the cell performed no git write. Reviewer A has not yet run.

### What changed

`src/clearwater/__main__.py` now imports only the standard library at module
level. Its script bootstrap and `main()` install the same process-wide fatal
reporter before the GPU-loader/product imports. Installation also sets
`threading.excepthook`, and importing the canonical module after script execution
reuses the reporter through its hook identity marker. The interpreter-option
catch uses the reporter instead of printing a multiline traceback; explicit
`SystemExit` still passes through unchanged.

The first unhandled exception is guarded against concurrent/recursive reporting.
Where the configuration modules are importable (the STOP below qualifies this),
the reporter resolves AD-25's log, configures/reuses its rotating handler, writes
one full traceback using that handler's formatter and rollover policy, and
flushes it. It writes directly through the owning handler's stream rather than
`emit()` or logger propagation: IO errors can then be detected without logging's
own stderr traceback or the worker protocol receiving a second report. Missing,
closed or recursively failing stderr does not prevent termination. The summary
is one ASCII-safe line; an unopenable log names its intended path and says
`log unavailable`. There is no fallback file outside product locations.

Fatal termination uses `os._exit(1)` so an unhandled thread failure ends the
process, including a process with other live threads. Normal worker protocol
errors, stdin isolation, the DR-125 status-2 path and normal AD-34 refusal codes
are unchanged. `export_worker.py` changes only its granted `__main__` site: import
and call the shared hook installer immediately before its existing `main()` call.

`app/main.py` installs/reuses the reporter before QApplication construction and
enables its callback immediately after QApplication exists, before
`build_application`. A QObject signal marshals thread failures to Qt's owning
thread. The actual presenter creates one plain-text message box containing the
log summary, with no traceback. The reporting thread waits at most 30 seconds
for presentation; an event loop that cannot process events cannot keep the
failed process alive indefinitely. Headless entry paths never enable this
presenter. Tests replace presentation and termination, use offscreen Qt and
`processEvents`, and never enter a Qt/application/dialog `exec()`.

### RED and GREEN evidence

Every pytest invocation used `PYTHONPATH=scripts`, `-p sandbox_mkdir_shim`,
`-p no:cacheprovider`, offscreen Qt, `--timeout 300` and its own fresh basetemp
under `work/`. Hook tests additionally have a 20-second test bound; their source
children block Qt and have a 12-second subprocess bound. All new entry calls
redirect APPDATA, LOCALAPPDATA, the XDG roots, HOME and USERPROFILE, or use the
existing frozen-entry fixture's disposable roots and GUI stand-in/blocker.

| File under `work/c63b-3-logs/` | Observed result |
| --- | --- |
| `red-hook.log` | Exit 1: 13 failed against the original code; the installer/reporting API and effects were absent. |
| `red-reentry.log` | Exit 1: 1 failed, 1 passed, 173 deselected. The exception printed 9 stderr lines; the explicit `SystemExit(5)` control already passed. |
| `green-hook1.log` | Exit 0: 188 passed before the rotation regression was added. |
| `red-rotation.log` | Exit 1: 1 failed, 13 deselected. Direct append did not produce the expected rotated log. |
| `pytest-groupa-final.log` | Exit 0: 257 passed in 10.16 s (14 hook cases, 175 frozen-entry cases and 68 packaging-tool cases). |
| `ruff-check.log` | Exit 0: `All checks passed!` for the repository. |
| `ruff-format.log` | Exit 0: `331 files already formatted`. |
| `mypy.log` | Exit 0: `Success: no issues found in 164 source files`. |
| `mypy-darwin.log` | Exit 0: `Success: no issues found in 164 source files`. |
| `pytest-requested-safe.log` | Exit 1: 3 failed, 324 passed, 1 deselected, 1 warning in 143.05 s. One owned regression-fixture mock was corrected; the other two failures were isolated below. |
| `pytest-residual.log` | Exit 1: 2 failed, 1 warning in 66.45 s. Reproduced the worker import witness and GPU-probe timeout, with a 20-second diagnostic stack dump. |
| `pytest-final-safe.log` | Exit 1: 1 failed, 326 passed, 1 deselected, 1 warning in 79.35 s. Only the worker import witness remains after runner cache/temp redirection. |
| `dependency-probe-summary.log` | Bounded isolated child: exit 1, 1 stderr line, 0 product logs. Confirms the MAJOR scope STOP below. |
| `diff-check.log`, `desktop-input-grep.log` | No whitespace errors; no synthetic desktop-input API matches in the changed entry/GUI code or new tests. |

The final broad command is the dispatch's six-module pytest command with
`-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'` and basetemp
`work/c63b-3-final`. The exclusion is explicit and requires the ruling below;
the exact unfiltered requested command was not run. Its runner environment also
sets TEMP, TMP, TMPDIR, CUPY_CACHE_DIR and CUDA_CACHE_PATH beneath
`work/c63b-3-runner/`. These are validation-environment settings only, not Group B
product code. The warning is CuPy's existing `CUDA path could not be detected`.
The inherited VIRTUAL_ENV mismatch warning is also retained in runner files;
uv explicitly uses this worktree's `.venv`.

The new hook cases cover early failure before normal logging; unavailable log;
absent/broken stderr; recursive reporting; process-wide thread termination;
explicit SystemExit; module re-import; post-Qt presentation on Qt's thread once
for main/thread exceptions; rotating-log preservation; and three real source
children (startup, source-worker escape from `main()`, unhandled Python thread).
Children report once, exit non-zero, and never import Qt. The source-worker
child plants its exception with a trace callback at the call to the worker's
`main()`, after the granted hook-install site, without changing the worker's
protocol, stdin handling or product code for fault injection.

### Verification loop, findings and rulings requested

| Severity / suspected issue | Independent evidence | Disposition |
| --- | --- | --- |
| MAJOR: a dependency failure can make the ostensibly stdlib bootstrap reporter unable to resolve or write its product log. | `dependency-probe.py` blocks NumPy, blocks Qt, stubs `app.main` with a function that imports NumPy, redirects all product/home roots, and executes the real source entry. A second bounded run records exit 1, one line `Clearwater: unexpected error; log unavailable: Clearwater product log (path unavailable)`, and no product log. `clearwater.config.__init__` imports presets/settings/interfaces; `interfaces/image.py` imports NumPy. | **STOP, scope ruling requested.** The currently owned entry files cannot normally import `config.paths` without executing the unowned eager package initializer. Request a narrow grant/design ruling for a stdlib-only route to the existing AD-25 resolver/log support, or an explicit accepted limitation. No duplicate per-OS resolver or manual loading of frozen modules was invented as a workaround. Group A is not complete. |
| MINOR: requested legacy source-entry test conflicts with the explicit entry-point isolation rule. | `tests/test_app_startup.py`'s `QUIT_SCRIPT` executes the real GUI and event loop. It redirects profile/home roots and uses offscreen Qt, but neither blocks PySide6/shiboken6 nor stubs `app.main`. | **STOP, validation ruling requested.** This test was deselected, never executed by this cell. The file is outside this turn's grant. The seat can commission a compliant replacement or give an explicit exception for this existing integration test. Other startup tests build components over supplied disposable Locations under offscreen Qt. |
| MINOR: direct crash-log append could bypass D88 rotation. | The additional rotation RED uses a real configured handler with a small limit, a previous record and the fatal traceback; the rotated file was missing. | Fixed in-envelope by reusing the owning handler's rollover/formatter with checked stream IO. All 14 hook cases pass in the final runs. |
| MINOR: the frozen-entry regression's fixture stubbed away the real log handler. | The first broad run failed only the newly strengthened pack-module exception assertion, with no log file. The existing pack fixture replaces configure_logging with a call recorder. | Test-only fix: restore the captured real configure_logging for these two cases, retain redirected profile roots, and close it in the finalizer. The 257-case focused final and final broad run pass both cases. |
| MINOR, validation residual: worker eager-import witness fails before reaching any new hook code. | Both broad runs and the isolated residual run trace unchanged `clearwater.app.__init__` -> composition -> core -> SciPy -> numpy.testing -> platform.win32_ver -> `_syscmd_ver` -> subprocess. The witness forbids Popen and raises `AssertionError: spawn before stdin isolation`. This occurs before export_worker.py's granted bottom-of-module site. | Seat re-run outside the restricted token required. No edit was made to `tests/test_app_export_worker.py`, app package imports or the worker's isolation logic. This is an observed environmental/import-path residual; outside-sandbox success is not claimed. |
| MINOR, validation residual: default-settings startup never finishes GPU detection under the initial environment. | Two runs time out waiting 60 s for the device label; the independent diagnostic stack is in CuPy `_compiler_cache._write_encoded` -> tempfile `_mkstemp_inner`, reached from `_probe_gpu`. | Cleared in the final broad run with runner-only temp/cache roots under the worktree. No kernel-cache or driver write outside the worktree is claimed. Group B still must implement the frozen product settings separately. |

The first four findings concern this implementation/validation envelope. The
worker-import residual is on unchanged pre-hook code and remains a seat check;
it is not silently fixed beyond the grant. There is no Reviewer A verdict or
five-round review gate to report yet. The new major observation stops the build
before a claim that the required stdlib-only bootstrap failure coverage is met.

### Handoff and remaining work

Request CHARC's ruling on the two STOP rows above. Then finish the bootstrap
logging requirement within its granted scope, re-run the hook/frozen tests and
resume Group B: `--disable-windowed-traceback` plus its argument-list regression,
and both frozen-only cache variables before all three activation sites with the
specified default/source/explicit-value tests. The seat must disposition the
worker-import residual and the legacy excluded source-entry test. The remaining
release workflow/FFmpeg/notices/smoke/zip/documentation work from the main brief
is still commissioned to later turns, unchanged.

No workflow/network fetch, frozen executable, package build, desktop GUI launch,
synthetic input, git write, push, tag or workflow dispatch was performed. Only
the granted entry/test files and this report were edited. Tests constructed
offscreen Qt objects or windows only with disposable Locations; no cell-written
hook check entered the real GUI event loop. No write to footage or to the owner's
real application profile is claimed; all observed evidence is inside the
worktree. New test file MD5 at the final run:
`56CBC2C37D3E03A335B345DC5287D033` (`tests/test_exception_hook.py`).
