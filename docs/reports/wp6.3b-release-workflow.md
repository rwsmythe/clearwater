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
