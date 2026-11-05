# WP6.3b release workflow: implementation record

Status: turn 9 implements full-text rendering, native Qt/pillow-heif details,
the notices writer/module CLI and build.py's --notices option. Ruff, format,
both mypy platforms and all 408 requested tests pass. Dispatch 9 resolves the
turn-8 GPL-3.0 wording question. A NEW MAJOR input gap remains: the interpreter
carries OpenSSL DLLs, but neither its licence file nor the root audit supplies
OpenSSL's redistributed licence/source material. Such a folder now fails closed;
the seat must supply verified material and a ruling before the OpenSSL row can
be completed. No real artifact notices, PyInstaller build or N13 acceptance is
claimed. The separate FFmpeg zvbi redistribution HOLD remains unchanged.

## Round and turn ledger

Build turns and round 0 below are not Reviewer A rounds. Reviewer A is the dispatcher's
Claude pass; no review verdict is claimed here. Context depth is dispatcher-read.

| Turn / round | Work and disposition | Severity / envelope | NEW / REOPENED; reverts | Product vs test changes | Dispatcher-read depth |
| --- | --- | --- | --- | --- | --- |
| Turn 1 / round 0 | Read-only design return; no files or processes. CHARC accepted the read-back and Q2-Q4. Source-worker hook site and guide section-3 launch paragraph granted; ADV-3 corrected to a live child that times out without reporting its PID. Q1 ruled BtbN month-end autobuild `autobuild-2026-10-31-12-59`, subject to the brief's source, configuration, hash and retention conditions. | 0 critical, 1 major, 2 minor; all 3 in-envelope questions, now ruled. | 3 NEW, 0 REOPENED; no reverts. | None. | 146,885 / 475,000 at turn end, supplied in dispatch 2. |
| Turn 2 / build part 1 | ADV-1 publication outcome, ADV-3 no-PID fallback coverage/mutant, D4(d) statement guard. One native `taskkill` residual remains for the seat. | No Reviewer A findings yet; native process-control denial disclosed below. | No review reopenings. Temporary test-only kill-removal mutant restored. | Product: publication block and executable-finder guard. Tests: local wheel, fault injection, live child tree and layout/platform cases. | Turn-end figure pending dispatcher reading. |
| Turn 3 / build part 2, Group A yield | Fatal reporter, GUI notification, source-worker hook site and isolated tests. Both STOPs now settled by CHARC's turn-3 rulings; Group B was not started in turn 3. | No Reviewer A round. Self-check: 1 MAJOR scope STOP and 1 MINOR validation-rule question, both closed; worker residual confirmed sandbox-only by the seat. | All new observations, no review reopenings or product reverts. Rotation and the regression fixture's logging stub corrected in-envelope. | Product: entry reporter, interpreter catch, GUI callback and the single granted worker site. Tests: new hook suite and frozen-entry regression. | About 157K at the Group A yield, supplied in dispatch 4. |
| Turn 4 / Group A finish and Group B yield | Closed the ruled bootstrap/QUIT_SCRIPT rows; proved lazy blocked-import behavior; added the bootloader flag and cache variables before all three activations. | No Reviewer A round; no new blocking finding. The known sandbox-only worker witness remains the sole validation failure. | No review reopenings. Temporary eager-import mutant caught twice and restored before Group B; no mutant remains. | Product: PyInstaller argument and frozen cache setup only. Tests: blocked-config/NumPy cases, argument-list cases, activation-boundary cases and environment restoration. | Turn-end figure pending dispatcher reading; no cell estimate. |
| Turn 5 / FFmpeg lock and bundle path | Pinned archive/source record, lock validation, release fetch/hash/selective extraction/version checks and CLI/build wiring. | No Reviewer A round; no new blocking issue. Eleven primary licences and five extra-source licences are explicitly UNVERIFIED for the seat audit. | No review reopenings. Build-call deletion mutant rejected and byte-restored; schema type error and raw-ZIP fixture corrected. | Product: build tool plus lock; tests: offline ZIP/file transport, real Python tool stubs, schema mutations and build integration. | Fresh session; turn-end depth pending dispatcher reading, no estimate. |
| Turn 6 / seat licence transfer, input STOP | All 103 licence slots transferred exactly; strict verified-licence validation GREEN and incompatible data retained. Generator not started: its mandatory wheel LGPL input is absent; exact MinGW source release is absent too. | No Reviewer A round. NEW MAJOR input/provenance STOP; MINOR pre-existing indirect-source limitation and root PyInstaller runtime-row discrepancy reported below. Existing zvbi STOP remains the owner's/CHARC's. | No review reopenings or reverts; no generator workaround. | Product: lock and shared validator. Tests: verified-only rejection and preservation of incompatible rows. | Dispatcher supplied about 134K at turn-5 end; turn-6 depth pending dispatcher reading, no estimate. |
| Turn 7 / notices coverage-boundary yield | New onedir inventory and notice-plan API, source-audit/uv.lock/installed-RECORD matching, material checks, coverage closure and conditional FFmpeg rows/refusal. Rendering, provenance tests and build wiring not begun. | No Reviewer A round or new blocking finding; turn-6 input STOPs ruled by CHARC. | No review reopenings or reverts. Initial typing/lint errors corrected; no product-entry or real-binary execution. | New notices planning module and synthetic coverage test module; report. No existing build/lock/test file changed. | Dispatcher supplied 171K at turn-6 yield; current depth is pending dispatcher reading, not estimated. |
| Turn 8 / input-rule STOP | Read dispatch 6 item 2, dispatch 7, the report and installed materials. Reproduced two complete GPL-3.0 copies under the required wheel-byte-copy rule; requested CHARC's rendering ruling. | No Reviewer A round. NEW MAJOR in-envelope ambiguity; existing zvbi HOLD unchanged. | 1 NEW, 0 REOPENED; no reverts. | Report only; no product or test change. | Fresh session; turn-end figure pending dispatcher reading, not estimated. |
| Turn 9 / generator and input-gap handoff | Applied dispatch-9 clarification; rendered verified texts, native details and coverage; added atomic writer, CLI and --notices wiring. OpenSSL missing redistribution material confirmed; folders carrying it are refused. | No Reviewer A round. Turn-8 MAJOR closed by seat clarification; 1 NEW MAJOR in-envelope input gap, plus the unchanged zvbi HOLD. | 1 NEW, 0 REOPENED; no reverts. | Notices generator and build option; synthetic/provenance/wiring tests; report. | Dispatcher supplied about 104K at turn-8 yield; turn-9 end pending dispatcher reading, not estimated. |

Turn 2 bundled the three changes explicitly commissioned by dispatch 2; the seat
commits each turn. No git write was performed by the cell.

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

### Turn-3 verification loop and dispositions

| Severity / suspected issue | Independent evidence | Disposition |
| --- | --- | --- |
| MAJOR: a dependency failure can make the ostensibly stdlib bootstrap reporter unable to resolve or write its product log. | `dependency-probe.py` blocks NumPy, blocks Qt, stubs `app.main` with a function that imports NumPy, redirects all product/home roots, and executes the real source entry. A second bounded run records exit 1, one line `Clearwater: unexpected error; log unavailable: Clearwater product log (path unavailable)`, and no product log. `clearwater.config.__init__` imports presets/settings/interfaces; `interfaces/image.py` imports NumPy. | **CLOSED by CHARC's turn-3 ruling, option (c), AD-38 accepted limitation.** Keep installation stdlib-only and resolve config/log lazily in the handler. Failure to import them gives one `log unavailable` stderr line, non-zero exit and no log file. Turn 4 pins both blocked-config and blocked-NumPy cases with an eager-import mutant control. No duplicated resolver, manual frozen-module loading or config initializer edit. |
| MINOR: requested legacy source-entry test conflicts with the explicit entry-point isolation rule. | `tests/test_app_startup.py`'s `QUIT_SCRIPT` executes the real GUI and event loop. It redirects profile/home roots and uses offscreen Qt, but neither blocks PySide6/shiboken6 nor stubs `app.main`. | **CLOSED by CHARC's turn-3 ruling and the owner's recorded QUIT_SCRIPT exception (`1a38c935`).** The SEAT alone runs this existing integration test in gate legs with redirected roots, offscreen Qt and a bound. The cell continues to deselect it on every revision. Other startup tests build components over supplied disposable Locations under offscreen Qt. |
| MINOR: direct crash-log append could bypass D88 rotation. | The additional rotation RED uses a real configured handler with a small limit, a previous record and the fatal traceback; the rotated file was missing. | Fixed in-envelope by reusing the owning handler's rollover/formatter with checked stream IO. All 14 hook cases pass in the final runs. |
| MINOR: the frozen-entry regression's fixture stubbed away the real log handler. | The first broad run failed only the newly strengthened pack-module exception assertion, with no log file. The existing pack fixture replaces configure_logging with a call recorder. | Test-only fix: restore the captured real configure_logging for these two cases, retain redirected profile roots, and close it in the finalizer. The 257-case focused final and final broad run pass both cases. |
| MINOR, validation residual: worker eager-import witness fails before reaching any new hook code. | Both broad runs and the isolated residual run trace unchanged `clearwater.app.__init__` -> composition -> core -> SciPy -> numpy.testing -> platform.win32_ver -> `_syscmd_ver` -> subprocess. The witness forbids Popen and raises `AssertionError: spawn before stdin isolation`. This occurs before export_worker.py's granted bottom-of-module site. | **DISPOSITIONED at the seat:** dispatch 4 records 328 passed outside the sandbox at `74ce225c`, including QUIT_SCRIPT and this witness. Sandbox-only residual; do not chase it. No edit to its test, package imports or stdin isolation. New-turn outside-sandbox verification remains the seat's. |
| MINOR, validation residual: default-settings startup never finishes GPU detection under the initial environment. | Two runs time out waiting 60 s for the device label; the independent diagnostic stack is in CuPy `_compiler_cache._write_encoded` -> tempfile `_mkstemp_inner`, reached from `_probe_gpu`. | Cleared in the final broad run with runner-only temp/cache roots under the worktree. No kernel-cache or driver write outside the worktree is claimed. Group B still must implement the frozen product settings separately. |

The first four findings concern this implementation/validation envelope. CHARC's
turn-3 rulings settle both STOPs; turn 4 supplies the required regression proof.
The worker-import residual is on unchanged pre-hook code and is confirmed
sandbox-only by the seat, never fixed beyond the grant. There is no Reviewer A
verdict or five-round review gate to report yet.

### Handoff and remaining work

Turn 3 yielded both STOPs to CHARC. Dispatch 4 supplies their rulings and the
seat's worker-witness verification; its implementation and validation are
recorded in the turn-4 section below. The remaining release workflow/FFmpeg/
notices/smoke/zip/documentation work from the main brief stays commissioned to
later turns, unchanged.

No workflow/network fetch, frozen executable, package build, desktop GUI launch,
synthetic input, git write, push, tag or workflow dispatch was performed. Only
the granted entry/test files and this report were edited. Tests constructed
offscreen Qt objects or windows only with disposable Locations; no cell-written
hook check entered the real GUI event loop. No write to footage or to the owner's
real application profile is claimed; all observed evidence is inside the
worktree. New test file MD5 at the final run:
`56CBC2C37D3E03A335B345DC5287D033` (`tests/test_exception_hook.py`).

## Turn 4: Group A finished; Group B built and validated

Both dispatch-4 groups are complete under CHARC's turn-3 rulings. The turn-3
verification-loop dispositions above are closed, including the seat's 328-test
outside-sandbox pass at `74ce225c` supplied in dispatch 4. This is a build-group
yield; it is not acceptance of the whole release work package. No Reviewer A
round has run yet, and the seat commits this turn's six changed files.

### Group A: lazy reporting and its accepted limitation

The reporter's imports are already lazy: `__main__.py:91` imports `config.paths`
inside `_ExceptionReporter.__call__`, and `:94` imports `config.log` only after
resolving the path. `install_exception_hooks` at `:160-173` imports neither;
module-level imports are standard library only. No production hook change was
needed for CHARC's ruling, and no configuration initializer or resolver was
edited.

**AD-38 limitation (CHARC's turn-3 ruling): a failure before `clearwater.config`
can import, such as broken NumPy or a broken install, gives one `log unavailable`
stderr line and a non-zero exit, but no log file.**

TEST A is now
`test_unimportable_log_dependencies_still_report_and_exit`, parameterized over
blocked `clearwater.config` and blocked `numpy`. Each fresh child redirects all
product/home roots, blocks Qt, has a 12-second subprocess timeout, imports the
entry and installs its hooks, verifies that installation imported none of
config/NumPy/Qt, prints a flushed installation canary, then raises a planted
RuntimeError. The parent requires the canary, a non-zero exit, exactly one
ASCII-safe stderr line containing `log unavailable`, and no `clearwater.log`
anywhere under the disposable root. The canary prevents an earlier import
failure from being mistaken for the intended post-install fatal failure.

RED control: a temporary eager `from clearwater.config.paths import
app_locations` was inserted at the start of `install_exception_hooks`. Both
cases failed because the installation canary was absent. The original entry
was restored from its byte backup and SHA-256 equality was checked before any
Group B product edit. The two cases then passed with the other hook and frozen
tests. No mutant remains.

TEST B already exists, so no duplicate was added:
`test_uncaught_source_failures_exit_without_qt_and_report_once[startup]` runs the
actual source entry with a planted GPU-loader import failure while config is
available. It asserts non-zero exit, no stdout, one ASCII stderr line naming
the redirected product log, exactly one full `Traceback (most recent call last)`
in that log, `RuntimeError: planted startup failure`, and no Qt-blocker failure.
`test_startup_report_writes_traceback_flushes_and_exits_once` additionally checks
the source `raise RuntimeError` frame and the full multiline/Unicode exception
text in the log, along with the single stderr line and termination call. Both
cases pass in the Group A run and final validation.

QUIT_SCRIPT remains excluded from every cell run collecting startup tests. The
owner's recorded exception permits only the seat to run it in a gate leg; it
was not executed this turn. The cell did not chase or change the worker witness
that the seat has confirmed passes outside the sandbox.

### Group B: bootloader flag and frozen GPU cache roots

`tools/package/build.py:338` adds `--disable-windowed-traceback` to the shared
PyInstaller argument list. A two-case regression checks that exactly one such
argument is present for both forms. It calls only `pyinstaller_args`; no build,
PyInstaller process or frozen executable was run.

`__main__.py` adds `_configure_gpu_caches` at `:304`, with a frozen-only guard
and an activation-time lazy resolver import at `:311`. It uses
`os.environ.setdefault` with `app_locations().cache_dir` for
`CUDA_CACHE_PATH = <cache>/nvidia-compute-cache` and
`CUPY_CACHE_DIR = <cache>/cupy-kernel-cache`. It creates no folder itself.
The calls immediately precede every loader activation: `:410-411` for the
allowed module attempt, `:501-502` for the frozen worker and `:528-529` for the
GUI branch. A source call leaves both settings alone. Missing/pending packs and
refusal statuses retain their existing control flow; the module branch's
conditional expression became a statement block to put configuration before
activation.

Eighteen activation-boundary cases cover each variable on each branch with a
frozen default, source mode and an explicit frozen value. The assertion runs
inside the stand-in loader, so moving setup after activation fails the test.
The fixture supplies a cache root under the redirected disposable profile;
Qt is blocked and the GUI entry is a stand-in. Tests assert the final value and
branch status as well as exactly one activation. The frozen-entry autouse
fixture now restores both cache environment values at teardown, alongside its
existing hook restoration, so product setup cannot leak into subsequent tests.

RED: six frozen-default cases and both argument-list cases failed; the twelve
source/explicit-value controls already passed. GREEN: all twenty Group B cases
passed. The final six-module validation also passes all these cases.

### Turn-4 validation

Runner files are under `work/c63b-4-logs/`. All pytest runs used
`PYTHONPATH=scripts`, `-p sandbox_mkdir_shim`, `-p no:cacheprovider`, offscreen Qt
and fresh worktree-local basetemps. No invocation ran QUIT_SCRIPT. The final
command is the dispatch's exact six-module selection and exclusion, with
basetemp `work/c63b-4`; runner TEMP/TMP/TMPDIR, CUPY_CACHE_DIR and CUDA_CACHE_PATH
are under `work/c63b-4-runner/`, retaining turn 3's environment isolation.

| Evidence file | Observed summary |
| --- | --- |
| `red-a-mutant.log` | Exit 1: `2 failed, 14 deselected in 0.73s`; eager-import mutant rejected for both blocked dependencies. |
| `green-a.log` | Exit 0: `191 passed in 13.35s`; 16 hook and 175 pre-Group-B frozen-entry cases. |
| `red-b.log` | Exit 1: `8 failed, 12 passed, 243 deselected in 1.07s`; missing frozen defaults and bootloader flag distinguished. |
| `green-b.log` | Exit 0: `20 passed, 243 deselected in 0.70s`. |
| `ruff-check.log` | Exit 0: `All checks passed!` for the repository. |
| `ruff-format.log` | Exit 0: `331 files already formatted`. |
| `mypy.log` | Exit 0: `Success: no issues found in 164 source files`. |
| `mypy-darwin.log` | Exit 0: `Success: no issues found in 164 source files`. |
| `pytest-validation.log` | Exit 1: `1 failed, 348 passed, 1 deselected, 1 warning in 85.66s (0:01:25)`. |
| `diff-check.log`, `desktop-input-grep.log` | No whitespace errors or synthetic desktop-input API matches; Git's LF-to-CRLF working-copy warnings are retained. |

The sole final failure is
`tests/test_app_export_worker.py::test_eager_imports_and_isolation_spawn_nothing_and_import_no_cupy`:
the unchanged SciPy/NumPy import chain reaches `platform.win32_ver`'s subprocess
fallback, and the witness raises `AssertionError: spawn before stdin isolation`.
Dispatch 4 explicitly confirms it as sandbox-only from the seat's outside run;
there is no new skip or fix for it. All other selected cases pass, including all
16 hook, 193 frozen-entry and 70 packaging-tool cases. The one deselection is
QUIT_SCRIPT, as required. The warning is CuPy's existing CUDA-path warning; uv's
inherited-VIRTUAL_ENV warning is also retained in the files and does not change
the worktree environment it selects.

### Turn-4 verification loop and handoff

| Suspected issue | Confirmation | Disposition |
| --- | --- | --- |
| Config import might occur at module/install time. | Read the handler/installer sites; the new children require an installation canary with both config and NumPy unavailable, and reject the eager-import mutant. | Confirmed lazy installation; no product change needed. AD-38's unavailable-log limitation pinned and recorded. |
| A healthy config import might still fail to produce the full traceback. | Existing source-startup child and direct full-traceback test in both Green A and final validation. | Rejected; existing coverage is sufficient, with no duplicate test. |
| Bootloader dialog suppression or a frozen activation site could be missed. | The new eight-case RED and twenty-case GREEN; final six-module run. | Fixed in the shared argument list and at all three activation sites. |
| In-process entry calls could leak cache values between tests. | Product `setdefault` writes directly to os.environ, while the previous fixture restored hooks only. | Test teardown now snapshots/restores both variables; the final combined run covers the resulting test order. |
| The worker witness might represent a product regression. | Same pre-hook failure chain in final validation; dispatcher reports its outside-sandbox pass at the turn-3 head. | Known sandbox-only residual, carried for the seat's new-head rerun; not changed. |

The final inspection found no new in-envelope issue. Both turn-3 STOPs are
settled; no new scope question remains. Reviewer A and new-head outside-sandbox
validation remain the dispatcher's gates. Later commissioned turns still own
the FFmpeg lock, notices, smoke/ZIP, workflow, checklist and guide; none was
started here. No network fetch, frozen run, build, desktop GUI launch, synthetic
input, footage/profile write, git write, tag, push, gh command or workflow
dispatch was performed. No dependency, frozen interface, app/main code or
export-worker code changed this turn. Depth at this Group B yield is for the
dispatcher to read and fill; the cell supplies no estimate.

## Turn 5: FFmpeg lock and offline fetch/verify/extract path

Dispatch 5's two items are implemented. The only changed files are the lock,
`tools/package/build.py`, the existing build tests, the new FFmpeg tool tests
and this report. No optional helper module was needed. This turn intentionally
bundles the lock/validator and their build consumer, as the dispatch commissions.
No Reviewer A round has run; the dispatcher commits and then owns that review.

### Pin and source record

The lock records BtbN/FFmpeg-Builds tag `autobuild-2026-10-31-12-59`, build
repository commit `5031c6f1082414e53688d39e521849905071070d`, asset
`ffmpeg-n9.0.2-39-g7adfbe40dc-win64-gpl-9.0.zip` (195,110,184 bytes), FFmpeg
commit `7adfbe40dc`, printed version `n9.0.2-39-g7adfbe40dc-20261031`, the
verbatim printed configure line (including its `configuration:` prefix),
GPL-3.0-or-later combined terms, and both independently supplied sha256 readings:
`693f3e224bc184b40524a62ca47526cfebaf2504414021b92fe75f677ad868b9`.
The archive URL is the exact dated GitHub release asset URL. These are facts
from the seat's `ffmpeg-fetch.md`, `version.txt`, `ffprobe-version.txt`,
`listing.txt` and `checksums.sha256`; the cell performed no live verification.

There is one component row per source-pinned BUILT stage: **98 rows**, comprising
92 commit pins, four tag pins and two SVN revision pins. Names distinguish the
two FreeType stages. Five extra repositories are recorded: gnulib, the OpenCL
ICD loader, Vulkan-Headers and two alternate nv-codec-headers commits. Only the
first nv-codec-headers commit is built at FFVER 900; both alternates are marked
`downloaded-not-built`. The exclusions block has 36 rows: five BUILT
SCRIPT_SKIP stages, one ENTRY and 30 not-built stages (23 directory-gated,
six disabled and one unreachable). No excluded stage becomes a component row.

The source facts come from the seat's `scriptsd-5031c6f1.md` and TSV, together
with read-only inspection of configure functions in the already-unpacked build
source tree. No source script was executed. A separate cross-check reconstructs
the source/exclusion sets from the TSV, compares every primary/extra repository
and pin and the binary identity/configuration against the seat records, and
passes (`work/c63b-5-logs/source-crosscheck.log`). Lock file sha256:
`bda8597304d2d7202a378f46815df5c30eb4073c04b1679f7df70c01e930682b`.

`validate_ffmpeg_lock` validates the complete schema, equal 64-hex hashes,
required GPL/version3/x265 flags, forbidden nonfree/fdk flags, exact extraction
list, unique stages/names, source pin kinds and two-way configure coverage.
`configure_flag` is null for a dependency or a list because a stage may contribute
multiple switches (opencore-amr contributes two; ffnvcodec contributes its own
switch plus cuda-llvm). All enabled switches except gpl/version3/schannel map to
source stages; those three select licence/system facilities. Every mapped
switch must also be present in the printed configuration. A licence without a
confident reading is null with basis UNVERIFIED; other readings have basis
`cell-read`. This is not a seat-verified licence verdict.

**Retention limit:** this month-end asset is retained about two years. Re-pin
before about **2028-10**; the checklist step is commissioned for turn 8 and
CHARC's dated register row remains an accept-time action. Mutable upstream tag
pins, the static source-stage reconstruction and the accepted 9.0-branch
provenance remain the seat record's caveats. The bundled-binary V4 and NVENC
proof remain pending the seat build.

### Offline licence read, by component

The SPDX expressions below are the cell's offline readings, not retrievals of
licence files at these future pins. The seat must verify EVERY row at its pin
before accept, including rows already marked cell-read and any subcomponent
terms. No known GPL-3.0-incompatible component was identified. For an OR
expression, compatibility means the compatible option can be selected. Unknown
aggregate or pin terms remain unverified; none was guessed into the lock.

| Component / build stage name | SPDX reading | GPL-3.0-compatible |
| --- | --- | --- |
| mingw-std-threads | BSD-2-Clause | yes |
| mingw | UNVERIFIED (null) | unverified |
| libiconv | LGPL-2.1-or-later | yes |
| zlib | Zlib | yes |
| fftw3 | GPL-2.0-or-later | yes |
| fribidi | LGPL-2.1-or-later | yes |
| gmp | LGPL-3.0-or-later OR GPL-2.0-or-later | yes |
| libogg | BSD-3-Clause | yes |
| libpng | Libpng-2.0 | yes |
| libxml2 | MIT | yes |
| openssl | Apache-2.0 | yes |
| xz | UNVERIFIED (null) | unverified |
| brotli | MIT | yes |
| freetype-bootstrap | UNVERIFIED (null) | unverified |
| fontconfig | MIT | yes |
| harfbuzz | MIT | yes |
| freetype | UNVERIFIED (null) | unverified |
| lcms2 | MIT | yes |
| libffi | MIT | yes |
| libsamplerate | BSD-2-Clause | yes |
| libudfread | LGPL-2.1-or-later | yes |
| libunibreak | Zlib | yes |
| libvorbis | BSD-3-Clause | yes |
| opencl | Apache-2.0 | yes |
| pcre2 | BSD-3-Clause | yes |
| pixman | MIT | yes |
| vmaf | BSD-2-Clause-Patent | yes |
| xxhash | BSD-2-Clause | yes |
| vulkan-headers | Apache-2.0 | yes |
| vulkan-loader | UNVERIFIED (null) | unverified |
| shaderc | Apache-2.0 | yes |
| spirv-cross | Apache-2.0 | yes |
| spirv-headers | MIT | yes |
| amf | MIT | yes |
| aom | UNVERIFIED (null) | unverified |
| avisynth | GPL-2.0-or-later | yes |
| chromaprint | LGPL-2.1-or-later | yes |
| dav1d | BSD-2-Clause | yes |
| davs2 | GPL-2.0-or-later | yes |
| libdvdcss | GPL-2.0-or-later | yes |
| libdvdread | GPL-2.0-or-later | yes |
| libdvdnav | GPL-2.0-or-later | yes |
| ffnvcodec | MIT | yes |
| frei0r | GPL-2.0-or-later | yes |
| gme | LGPL-2.1-or-later | yes |
| kvazaar | BSD-3-Clause | yes |
| lcevcdec | UNVERIFIED (null) | unverified |
| libaribb24 | LGPL-3.0-or-later | yes |
| libaribcaption | ISC | yes |
| libass | ISC | yes |
| libbluray | LGPL-2.1-or-later | yes |
| libjxl | UNVERIFIED (null) | unverified |
| libmp3lame | LGPL-2.0-or-later | yes |
| libopus | BSD-3-Clause | yes |
| libplacebo | LGPL-2.1-or-later | yes |
| mbedtls | Apache-2.0 OR GPL-2.0-or-later | yes |
| librist | BSD-2-Clause | yes |
| glib | LGPL-2.1-or-later | yes |
| cairo | LGPL-2.1-only OR MPL-1.1 | yes |
| pango | LGPL-2.1-or-later | yes |
| librsvg | LGPL-2.1-or-later | yes |
| libssh | LGPL-2.1-or-later | yes |
| libtheora | BSD-3-Clause | yes |
| libvpx | BSD-3-Clause | yes |
| libwebp | BSD-3-Clause | yes |
| libzmq | UNVERIFIED (null) | unverified |
| lv2 | ISC | yes |
| serd | ISC | yes |
| zix | ISC | yes |
| sord | ISC | yes |
| sratom | ISC | yes |
| lilv | ISC | yes |
| onevpl | MIT | yes |
| openal | LGPL-2.0-or-later | yes |
| openapv | BSD-3-Clause | yes |
| opencore-amr | Apache-2.0 | yes |
| openh264 | BSD-2-Clause | yes |
| openjpeg | BSD-2-Clause | yes |
| openmpt | BSD-3-Clause | yes |
| rav1e | BSD-2-Clause | yes |
| rubberband | GPL-2.0-or-later | yes |
| sdl | Zlib | yes |
| snappy | BSD-3-Clause | yes |
| soxr | LGPL-2.1-or-later | yes |
| srt | MPL-2.0 | yes |
| svtav1 | UNVERIFIED (null) | unverified |
| twolame | LGPL-2.1-or-later | yes |
| uavs3d | BSD-3-Clause | yes |
| libva | MIT | yes |
| vapoursynth | LGPL-2.1-or-later | yes |
| vidstab | GPL-2.0-or-later | yes |
| vvenc | UNVERIFIED (null) | unverified |
| x264 | GPL-2.0-or-later | yes |
| x265 | GPL-2.0-or-later | yes |
| xavs2 | GPL-2.0-or-later | yes |
| xvid | GPL-2.0-or-later | yes |
| zimg | WTFPL | yes |
| zvbi | LGPL-2.1-or-later | yes |

Extra repositories have their own uncertainty recorded, including the two
alternates that are downloaded but not built:

| Stage / extra repository | Pin | Build use | SPDX / compatibility |
| --- | --- | --- | --- |
| libiconv / https://git.savannah.gnu.org/git/gnulib.git | `5df606bbd0ef54a8f150c3303c870b9381a661f0` | built | UNVERIFIED / unverified |
| opencl / https://github.com/KhronosGroup/OpenCL-ICD-Loader.git | `5192c84f8059e5f703e5452929b613f9487f6e4c` | built | UNVERIFIED / unverified |
| vulkan-loader / https://github.com/KhronosGroup/Vulkan-Headers.git | `v1.4.366` | built | UNVERIFIED / unverified |
| ffnvcodec / https://github.com/FFmpeg/nv-codec-headers.git | `ced4f8eba3ba5dd431932cba17928f0dffdaeb2b` | downloaded-not-built | UNVERIFIED / unverified |
| ffnvcodec / https://github.com/FFmpeg/nv-codec-headers.git | `833faee5f7b8d3f56444347c587f4aed11ee213f` | downloaded-not-built | UNVERIFIED / unverified |

Primary UNVERIFIED list: **mingw, xz, freetype-bootstrap, freetype,
vulkan-loader, aom, lcevcdec, libjxl, libzmq, svtav1, vvenc**. All five extra
repository licence fields are also UNVERIFIED: gnulib, OpenCL-ICD-Loader,
Vulkan-Headers and the two downloaded-not-built nv-codec-headers alternatives.
The existing GPL-3.0-or-later combined FFmpeg licence is the seat's verified
archive/configuration fact, distinct from these per-component readings.

### Bundle path and offline tests

The paired `--ffmpeg-from` / `--ffmpeg-sha256` arguments reach `build` and are
mutually exclusive with `--with-ffmpeg`, whose help says "not for release".
Unpaired/ill-formed values and FFmpeg options without `--form` fail parsing.
The build rejects an unpinned URL/hash before scanning or running PyInstaller.

`bundle_ffmpeg` loads/validates the lock, downloads to `<out>/ffmpeg/` through a
partial file, bounds bytes by the locked size, checks the argument against the
lock and the computed hash against both readings, then publishes the checked
archive. It inspects every ZIP member before extracting any: absolute, traversal,
drive/ADS, backslash/control-character, trailing-dot/space, link/special-file,
missing and case-insensitive duplicate members fail closed. Only `bin/ffmpeg.exe`,
`bin/ffprobe.exe` and `LICENSE.txt` under the exact archive root are copied, as
`ffmpeg.exe`, `ffprobe.exe` and `ffmpeg-LICENSE.txt` beside Clearwater.exe.
`ffmpeg-BUILD.txt` records provider, tag, asset, hash, version, FFmpeg/build
commits, source-record pointer and the verbatim configure line.

Each copied tool runs with `-version`, its own folder as cwd and the sole PATH
entry, stdin closed, a 120-second bound and CREATE_NO_WINDOW on Windows. Both
printed versions and the single configure line must exactly match the lock.
Any extraction/download/check failure returns a failed build before the bundle
success summary. The PATH-copy spike remains available.

All fetch tests use small synthetic ZIPs through `file://` and a disposable
synthetic lock. The transport, ZIP inspection, hashing and extraction are real.
The text .exe stubs run as real Python child scripts; the native-loader adapter
only prefixes the absolute current Python executable (Windows cannot execute a
text .exe). The scripts write observed cwd/PATH/arguments; the test checks the
resulting files and provenance. No socket, real FFmpeg, product entry point or
PyInstaller build is used by these new tests. Existing synthetic CArchive writers
and stand-in PyInstaller calls test build integration. The existing frozen-entry
module retains its redirected profile/XDG roots, Qt blockers/stubs and bounds;
QUIT_SCRIPT is neither selected nor run.

### RED, GREEN and final validation

All pytest runs use `PYTHONPATH=scripts`, the sandbox mkdir shim,
`-p no:cacheprovider`, a 300-second runner timeout and fresh worktree-local
basetemps. Runner output is file-backed under `work/c63b-5-logs/`.

| Evidence file | Observed result |
| --- | --- |
| `red-lock.log` | Exit 1: 19 failed; the new lock was absent. |
| `red-validator.log` | Exit 1: 19 failed after writing the lock; the validator API was absent. |
| `green-lock.log` | Exit 0: 19 passed. |
| `red-fetch.log` | Exit 5: 118 deselected by an overbroad selection; no test ran. Corrected immediately in the next run. |
| `red-fetch2.log` | Exit 1: 24 failed, 24 passed; bundle API and CLI routing absent. Five parser-rejection controls and the 19 lock cases already passed. |
| `green-fetch.log` | Exit 1: 1 failed, 117 passed; Windows ZIP writer normalized the backslash fixture before the reader saw it. |
| `green-fetch2.log` | Exit 0: 118 passed after preserving the raw member name in the synthetic ZIP. |
| `red-types.log` | Exit 1: 1 failed, 4 passed; a list-valued pin kind leaked TypeError instead of ValueError. |
| `green-types.log` | Exit 0: 5 passed after explicit type validation. |
| `red-build-wiring-mutant.log` | Exit 1: 2 failed; deleting only the release bundle call loses the provenance file and wrongly reports success after a planted rejection. |
| `wiring-mutant2.log` | Mutant returned 1 and original bytes were restored, sha256 `c2fbea1284247f427626b98ab3f39c64b3ee6968a3a48131819f6e689d6b51d1`. The first script attempt failed before mutation on CRLF matching; the normalized-text attempt supplied this RED. |
| `green-wiring2.log` | Exit 0: 2 passed after byte restoration. |
| `ruff-check-final.log` | Exit 0: All checks passed! |
| `ruff-format-final.log` | Exit 0: 332 files already formatted. |
| `mypy-final.log` | Exit 0: Success: no issues found in 164 source files. |
| `mypy-darwin-final.log` | Exit 0: Success: no issues found in 164 source files. |
| `pytest-validation.log` | Exit 0: 321 passed in 10.36 s. |
| `source-crosscheck.log` | All 98 main pins, five extra pins, 36 exclusions, archive identity and binary version/configuration match the seat records. |
| `diff-check.log` | Exit 0, no whitespace errors; Git's LF/CRLF warnings retained where present. |

The requested final pytest command is exactly the three commissioned modules:
`tests/test_tools_package_build.py tests/test_frozen_entry.py
tests/test_tools_package_ffmpeg.py`, with basetemp `work/c63b-5` and
`QT_QPA_PLATFORM=offscreen`. The 321 cases comprise 78 build, 193 frozen-entry
and 50 FFmpeg cases (also confirmed by `collection.log`). There is **no sandbox-only residual in this turn's requested
set**. The inherited VIRTUAL_ENV warning says uv selects the worktree .venv;
it is retained in the logs. Initial lint formatting findings and a redundant
mypy cast were corrected before the final checks. The seat's broader gate,
standalone installer run and real-artifact proof remain separate work.

### Verification loop and handoff

| Severity / suspected issue | Independent check | Disposition |
| --- | --- | --- |
| MINOR: source-stage omissions, mistaken pin kinds or lost extra repositories. | Separate TSV-set reconstruction and field-by-field cross-check, plus committed-lock validation. | Rejected: 98 primary pins, all five extras and exclusions match the seat. No source script or archive binary was executed. |
| MINOR: a backslash unsafe-path case might test normalized input. | The initial GREEN attempt failed that case; inspecting ZipInfo's writer boundary explained normalization. | Test-only fix preserves the raw name; the real archive reader rejects it before any release file is written. |
| MINOR: malformed source types could escape the validation error contract. | Five-case type RED; list-valued pin kind raised TypeError. | Fixed with explicit type checks (also for extra-source status); all type cases pass. |
| MAJOR: a correct helper might never be called by the build, or rejection might be ignored. | Temporary deletion of only the integration block; both provenance/failure cases fail. | Rejected on restored code: both pass. Original bytes verified before continuing; no mutant remains. |
| MAJOR: wrong archive/tool could be accepted despite safe extraction. | Argument/lock/download hash failures, wrong versions/configurations for each tool, non-zero exit, OSError and timeout controls, all through the real bundle consumer. | Rejected by the offline checks; final test set green. Real-binary equivalence remains the seat's V4/NVENC proof. |
| N13 audit uncertainty at future pins. | Offline confidence assessment, null/basis validation and explicit table above. | Eleven primary and five extra-source readings stay UNVERIFIED for the seat; no incompatible component confirmed, no N13 acceptance claimed. |

The final code/data inspection found no new in-envelope issue. The only data
representation choice is list-valued `configure_flag` to preserve multi-switch
stages; no frozen product interface changed. No new dependency or unowned file
was changed. No network fetch, opening/extraction/execution of the real FFmpeg
archive, frozen run, PyInstaller build, desktop GUI launch, synthetic input,
footage/profile write, git write, push, tag, gh command or workflow dispatch
was performed. All observed writes and runner outputs are inside the worktree.

Next commissioned turns: notices generator/audit data (turn 6), smoke and ZIP
(turn 7), workflow/checklist/guide (turn 8). The seat owns verification of every
licence at its pin, the actual build and bundled-binary checks, actionlint and
Reviewer A/B. The real workflow run remains the release step. No new ruling is
requested by this build-group return. Depth is for the dispatcher to read;
none is estimated here.

## Turn 6: verified licence lock GREEN; generator input/provenance STOP

This is an item-1 build-group return with a reproduced STOP before item 2,
not a completed notices generator or acceptance. Dispatch 6 reports the seat's
outside-sandbox turn-5 result: 321 passed, exit 0, at `30cb8460`.

### Item 1: every source slot is seat-verified

All 98 primary components and five extra repositories now have the seat table's
`licence`, `licence_basis: "seat-verified"`, `gpl3_compatible` (yes/no) and
`licence_note`. Notes were copied without shortening or changing meaning.
There are no null, UNVERIFIED or cell-read licence rows left in the current lock.
The prior turn-5 table documents the historical offline reads; the verified
lock and corrections below are the current facts. The table transfer matches
`licences-5031c6f1.tsv` on all 103 SPDX/compatibility/note triples, independently
cross-checked in `work/c63b-6-logs/licence-crosscheck.log`. Totals from the seat:
80 same, 16 filled, seven corrected.

`FFmpegComponent` / `FFmpegSource` and `_ffmpeg_source` in build.py now require
a nonempty seat-verified licence, explicit yes/no compatibility and a nonempty
note. Null/UNVERIFIED/cell-read or missing compatibility is rejected for primary
AND extra source rows. **A no row is accepted as data.** The generator/release
refusal is a separate consumer and has NOT been built at this STOP. No bypass or
other resolution of the zvbi issue was added. The shared validator edit is the
one explicitly required by dispatch 6 item 1; no other build/notices wiring was
changed.

#### The seven corrected offline readings

| Component | Turn-5 reading | Seat-verified reading | Seat reason |
| --- | --- | --- | --- |
| harfbuzz | MIT | MIT-Modern-Variant | COPYING: 'Old MIT' licence (cell read MIT: corrected identifier) |
| vulkan-headers | Apache-2.0 | Apache-2.0 OR MIT | LICENSE.md + every header SPDX 'Apache-2.0 OR MIT' (cell read Apache-2.0) |
| chromaprint | LGPL-2.1-or-later | MIT AND LGPL-2.1-or-later | LICENSE.md: own code MIT, includes FFmpeg LGPL-2.1 parts; 'as a whole LGPL 2.1' |
| libaribcaption | ISC | MIT | LICENSE: MIT (cell read ISC: CORRECTED) |
| pango | LGPL-2.1-or-later | LGPL-2.0-or-later | COPYING is the GNU Library GPL 2 text (cell read LGPL-2.1-or-later; sources not sampled; either is GPL-3.0-compatible) |
| vidstab | GPL-2.0-or-later | LGPL-2.1-or-later | LICENSE at the pin: relicensed to LGPL-2.1-or-later after v1.1.2 (cell read GPL-2.0-or-later: CORRECTED) |
| zvbi | LGPL-2.1-or-later | GPL-2.0-or-later AND LGPL-2.0-or-later AND LGPL-2.1-or-later AND GPL-2.0-only AND MIT AND BSD-2-Clause | COPYING.md: src/* LGPL-2+, BUT src/pdc.* and src/packet-830.* 'GPL-2' = GPL-2.0-only (their headers: 'GNU General Public License version 2 as published'); both in libzvbi_la_SOURCES; packet.c calls into packet-830.c; see the STOP section |

The zvbi row remains **no**; the other 102 repository slots are yes. This is
CHARC/the owner's existing redistribution STOP, not a policy decision by the
cell. The lock truthfully records it; the new regression explicitly accepts
incompatible rows with verified provenance.

### STOP: the generator's mandatory licence inputs do not exist in the wheels

**[MAJOR, in-envelope input/provenance STOP]** Dispatch 6 item 2(d) requires
"the LGPL-3 text from the wheel" and its full-text rule says the full texts are
copied from installed wheel licence files and the folder's FFmpeg licence.
Read-only installed RECORD/licence-file inspection proves:

| Installed distribution | Licence files in its RECORD | Result |
| --- | --- | --- |
| pyside6-essentials 6.12.0 | `pyside6_essentials-6.12.0.dist-info/licenses/LicenseRef-Qt-Commercial.txt` | Only commercial Qt terms; no LGPL text. |
| shiboken6 6.12.0 | `shiboken6-6.12.0.dist-info/licenses/LicenseRef-Qt-Commercial.txt` | Only commercial Qt terms; no LGPL text. |
| pillow-heif 1.8.1 | `pillow_heif-1.8.1.dist-info/licenses/LICENSE.txt`, `LICENSES_bundled.txt` | BSD wrapper text and a component manifest with upstream links; no full LGPL text. |

The cheap reproduction is `work/c63b-6-logs/wheel-input-probe.py`, its summary
`wheel-input-probe.log`, and `wheel-inputs.json` (paths, exact byte counts,
sha256 values, commercial/full-LGPL text checks and the MinGW manifest section).
The read-only script imports only standard library metadata/path/hash/json
modules, reads the installed licence inputs and writes evidence under work/.
It confirms one / one / two licence files respectively and no full LGPL-3 text
in any of them. No product, GUI, binary or source repository code is executed.
`LICENSES_bundled.txt` links libheif v1.23.6, libde265 v1.1.3 and x265 4.3,
but contains only their licence labels and links, not their full texts.

The already-audited root notices preserve an LGPL-3 text as text-36, from
`https://raw.githubusercontent.com/qt/qtbase/v6.12.0/LICENSES/LGPL-3.0-only.txt`,
sha256 `da7eabb7bafdf7d3ae5e9f223aa5bdc1eece45ac569dc21b3b037520b4464768`,
7,651 UTF-8/LF bytes. The root also preserves x265/libheif/libde265 and MinGW
texts/headers as texts 37-44. Those are explicitly audited UPSTREAM texts, not
wheel files. Copying them under a claim of wheel provenance would be false;
no such fallback was implemented without a ruling.

**Proposed ruling:** permit the generator to reuse those audited root full-text
blocks when the installed wheel contains only a manifest/commercial text. Require
the generator to verify each stored SHA-256/byte count, retain the original source
URL/version and identify the input as the root's audited upstream copy. Continue
to copy actual wheel licence files whenever present; do not rely on or reproduce
the commercial Qt licence. This needs CHARC's explicit provenance-rule amendment,
so the cell yields under the binding dispatch protocol instead of guessing.

**[MINOR, existing indirect-source limitation]** Item 2(e)'s exact source-release
read is also unavailable for pillow-heif's MinGW/libstdc++ runtime: the manifest
names `libgcc_s_seh-1.dll`, `libstdc++-6.dll` and `libwinpthread-1.dll` but no
MinGW-w64/compiler version. Its source pointer is unversioned
`https://sourceforge.net/p/mingw-w64/mingw-w64/ci/master/tree/COPYING`.
This was already disclosed in the root audit and turn-5 context. The cell cannot
turn it into an exact source-release claim. CHARC must either supply exact
matching source provenance or explicitly carry the brief's indirect-source debt
and prescribe the artifact wording. No version was invented.

**[MINOR, unowned root-audit discrepancy]** The installed PyInstaller 6.22.3
`COPYING.txt` distinguishes the GPL-2.0-or-later bootloader/Bootloader Exception
from **Apache-2.0 Run-time Hooks and Additional Run-time Modules**. The root
PyInstaller row groups bootloader and embedded run-time hooks under its GPL /
exception licence. The generator must use the installed COPYING terms for each
kind. No root notice edit is made: this turn does not own that file. Route the
wording disposition to CHARC for the later limited root-notices update or a
narrow grant if required. The Bootloader Exception bytes themselves are available
in the installed COPYING and are not an input blocker.

### RED, GREEN and validation at this STOP

| File under `work/c63b-6-logs/` | Observed result |
| --- | --- |
| `red-licences.log` | Exit 1: 8 failed, 2 passed, 50 deselected against the old lock/validator. Old licence bases were accepted or the new verified schema rejected; preservation and rejection cases discriminate. |
| `green-lock.log` | Exit 0: 60 passed after the lock and validator update. |
| `licence-crosscheck.log` | All 103 SPDX/compatibility/note triples match the seat table; only zvbi is no. |
| `wheel-input-probe.log`, `wheel-inputs.json` | No full LGPL-3 wheel text; MinGW source release absent. Reproduces the STOP without network or product entry points. |
| `ruff-check.log` | Exit 0: All checks passed! |
| `ruff-format.log` | Exit 0: 332 files already formatted. |
| `mypy.log` | Exit 0: Success: no issues found in 164 source files. |
| `mypy-darwin.log` | Exit 0: Success: no issues found in 164 source files. |
| `pytest-lock-validation.log` | Exit 0: 331 passed in 10.73 s. |
| `diff-check.log` | Exit 0: no whitespace errors. |

The final pytest run uses `PYTHONPATH=scripts`, `-p sandbox_mkdir_shim`,
`-p no:cacheprovider`, `--timeout 300`, offscreen Qt and the fresh basetemp
`work/c63b-6-lock`. It selects the three existing commissioned test modules:
FFmpeg (60), build (78) and frozen entry (193). **The dispatch's four-module
command is not claimed:** `tests/test_tools_package_notices.py` does not exist
because the generator has not been started. No source startup/QUIT_SCRIPT test
is selected. Existing frozen-entry redirection/blockers remain in place.
No sandbox-only residual occurs in this set. uv's inherited VIRTUAL_ENV warning
remains in logs and explicitly selects this worktree's environment.

### Verification loop and remaining work

| Suspected issue / severity | Independent evidence | Disposition |
| --- | --- | --- |
| MAJOR: incompatible source truth might be rejected or silently normalized. | New no-row acceptance case and the current real zvbi lock row, plus source-table cross-check. | Rejected: no is preserved and accepted; release policy was not weakened or implemented early. |
| MINOR: extra repositories might retain old uncertainty or drop notes. | Primary/extra rejection cases and all-103 triple comparison against the seat TSV. | Fixed: every source slot has the exact verified licence, compatibility and note. |
| MAJOR: mandated LGPL wheel text might be missing. | Installed metadata/RECORD inventory and direct file contents; machine-readable probe records hashes. | Confirmed STOP; no root-text substitution or fabricated provenance. |
| MINOR: wheel manifest might identify a MinGW/libstdc++ source release. | Exact manifest section in wheel-inputs.json; only an unversioned COPYING pointer. | Confirmed existing limitation; ruling/input requested. |
| MINOR: run-time hooks might share the bootloader's licence. | Installed COPYING's explicit Run-time Hooks/Additional Run-time Modules sections. | Rejected; Apache-2.0 is explicit. Root wording is unowned and reported, not changed. |

No generator, notices test module, `--notices` option or synthetic coverage row
table exists yet; all of item 2 remains for the resumed turn after the ruling.
The requested synthetic row table is therefore **not available**, rather than
an empty table misrepresented as coverage. Full-text provenance tests have not
run. The two firm depth yield points remain applicable to resumed work; depth
at this STOP is dispatcher-read, not estimated by the cell.

The only edits are the FFmpeg lock, the shared validator in build.py, its FFmpeg
tests and this report. No network fetch, real FFmpeg archive access, frozen run,
PyInstaller build, desktop GUI launch, synthetic input, footage/profile write,
git write, push, tag, gh command or workflow dispatch occurred. The seat commits.
No release refusal, N13 acceptance or resolution of the owner's zvbi STOP is
claimed. Next action: CHARC rules the input/provenance question, then the cell
resumes item 2 with RED coverage tests followed by the prescribed yield.

## Turn 7: notices inventory/coverage GREEN; firm boundary yield

Read CHARC's complete Turn-6 rulings in the main-tree brief at `2258e5ab`
before writing. The seat's dispatch records turn 6 committed as `817a31b2`, zero
licence-table mismatches and 331 tests passing outside the sandbox. No earlier
protocol or report document was re-read into context. This turn implements the
coverage group and yields **before text-provenance tests**, as commissioned, so
the dispatcher can read depth before authorizing/resuming the next group. It
is not a completed artifact notices generator or a completed WP6.3b package.

### Rulings folded into the design

- Actual wheel licence files are the preferred inputs. Qt's commercial file is
  excluded from the planner's text references. For Qt/Shiboken's unavailable
  LGPL text, the planner references the root's `text-36`; it does not copy it.
  The renderer still MUST verify the recorded SHA-256 AND byte count and emit
  the exact granted label "the 1.0.0 audit's upstream copy", true URL and version.
  The same verified root reuse applies to pillow-heif texts 37-44. None of those
  reuse paths has yet been copied or provenance-tested.
- PyInstaller bootloader and run-time hooks get separate rows, respectively
  GPL-2.0-or-later WITH Bootloader Exception and Apache-2.0. Their installed
  COPYING inputs are references now; exact per-kind byte copying remains in the
  rendering/provenance group. No root-audit wording was changed.
- **Accepted MinGW limit:** the wheel does not name the toolchain release.
  The final artifact notices must name libgcc_s_seh-1.dll, libstdc++-6.dll and
  libwinpthread-1.dll, GPL-3.0 with GCC Runtime Library Exception / MIT-BSD terms,
  and the unversioned source pointer. CHARC opens the register row at accept.

### What is implemented

`tools/package/notices.py` exposes `plan_notices` and `validate_coverage`, with
small immutable rows carrying source URLs, version/licence, entry labels and
real licence-input references. It never renders a success artifact yet.

The inventory uses the existing build tool's executable finder and PyInstaller
archive reader, reads every on-disk file beside the executable (including
`_internal`), every embedded archive entry and every PYZ module, and inventories
standard-library ZIP members. No built executable or product entry is invoked.
Synthetic tests use PyInstaller's archive WRITERS to create genuine CArchive/PYZ
containers, not a build. The readers and metadata machinery execute as tooling;
no bundled runtime package is imported.

The runtime table is parsed from the root audit, not duplicated into a new
hard-coded distribution table. Installed metadata/RECORD paths determine module,
file and unambiguous flattened-native-basename ownership. Selected distributions
must match BOTH uv.lock and the source-install audit. Standard-library modules
and interpreter binary names are attributed to Python. Unknown/ambiguous data,
unknown PYZ modules and unrecorded native files even beneath a known package fail
closed. Licence material must exist and be nonempty, and selected rows need source
URLs. Only selected components get redistributed rows; user-obtained statements
are separate, so they cannot conceal uncovered binary entries.

`validate_coverage` rejects a missing entry, duplicate row, row with no entries,
row claiming an absent entry, or row without source/licence evidence. A file can
support multiple real components: the Clearwater executable supports both the
application and PyInstaller's bootloader. This is intentional many-to-one
coverage, not an invented additional file.

FFmpeg is conditional on the actual adjacent executables. No tools means no
FFmpeg rows, and the explicit "user-obtained, not redistributed" statement.
A partial executable/provenance/licence set fails. With FFmpeg present, the
shared verified-lock validator runs; EVERY no row, including an extra repository,
is named in a single-line GPL-3.0-incompatible refusal. There is no override.
For a compatible synthetic lock, the BUILD record's provider/tag/asset/hash,
FFmpeg/build commits, source pointer, version and configure line must match;
component rows retain repository-at-pin sources and the licence/patent notes.
Downloaded-not-built alternatives are not emitted as redistributed components.
The real lock's zvbi HOLD is untouched; the compatible fixture is not a ruling
that permits redistributing the real binary.

### Synthetic row table at this boundary

The baseline fixture contains a fake `_internal`, a real synthetic PYZ/CArchive,
fake distribution metadata/RECORDs, small placeholder licence inputs and a minimal
source-audit/uv.lock fixture. No binary or runtime package is executed. Its native
extension and interpreter are inert bytes. The baseline passes with no FFmpeg
against an incompatible lock as well as against the compatible fixture.

Evidence: `work/c63b-7/test_inventory_selects_only_bu0/coverage-plan.json`.

| Component row | Version | Licence | Inventory labels supporting the row |
| --- | --- | --- | --- |
| Clearwater | 1.0.0 | GPL-2.0-or-later | `archive:__main__`; `file:Clearwater.exe`; `pyz:clearwater` |
| numpy | 2.5.4 | BSD-3-Clause | `file:_internal/numpy/_core/test.pyd`; `pyz:numpy`; `pyz:numpy.linalg` |
| PyInstaller bootloader | 6.22.3 | GPL-2.0-or-later WITH Bootloader Exception | `archive:PYZ.pyz`; `archive:pyimod01_archive`; `file:Clearwater.exe` |
| PyInstaller run-time hooks | 6.22.3 | Apache-2.0 | `archive:pyi_rth_inspect` |
| Python | 3.12.13 | PSF-2.0 | `file:_internal/python312.dll`; `pyz:json` |

The baseline has **11 unique inventory entries and 5 rows**; all entries are covered, every row has actual entry evidence and every verdict
is "Redistributed in this artifact". There are twelve attribution edges because
the executable supports both Clearwater and the bootloader. GPU pack and FFmpeg
are explicitly user-obtained, outside this redistributed row table.

The compatible FFmpeg variant adds four files and two rows: `FFmpeg / ffprobe`
and `FFmpeg component: x265`; both cite those four files. A wrong BUILD version
fails. The incompatible variant names the main x265 row and an extra repository
in one refusal line. Removing either tool, BUILD or licence material fails.

### RED, GREEN and final validation

All pytest output is file-backed, with `PYTHONPATH=scripts`, the sandbox mkdir
shim, `-p no:cacheprovider`, a 300-second runner timeout and fresh worktree-local
basetemps. The final run sets offscreen Qt, retains the existing frozen-entry
root redirection/blockers and never selects QUIT_SCRIPT.

| File under `work/c63b-7-logs/` | Observed result |
| --- | --- |
| `red-coverage.log` | Exit 1: 14 failed; the new module was a docstring scaffold and the planning API was absent. |
| `green-coverage.log` | Exit 0: 14 passed after the coverage implementation. |
| `ruff-edit.log`, `ruff-check-initial.log` | Initial import/format, long-line, regex-intent and conditional-style findings; fixed before final validation. |
| `mypy-initial.log` | Six errors: metadata SimplePath conversion and reuse of inferred variable names for different types; fixed with explicit Path conversion and distinct names. |
| `ruff-check-final.log` | Exit 0: All checks passed! |
| `ruff-format-final.log` | Exit 0: 334 files already formatted. |
| `mypy-final.log` | Exit 0: Success: no issues found in 165 source files. |
| `mypy-darwin-final.log` | Exit 0: Success: no issues found in 165 source files. |
| `pytest-validation.log` | Exit 0: 345 passed in 11.04 s. |
| `diff-check.log` | Exit 0: no whitespace errors. |

The final pytest command is the exact four-module dispatch selection with
basetemp `work/c63b-7`: notices (14), FFmpeg (60), build (78), frozen entry (193).
**No sandbox-only residual** occurs in this requested set. uv's inherited
VIRTUAL_ENV warning is retained and explicitly selects the worktree environment.
The only post-test source edit clarified a docstring: PyInstaller's tooling is
imported, while artifact/runtime code is not. No executable logic changed after
the final test run.

### Verification loop

| Suspected issue / severity | Independent evidence | Disposition |
| --- | --- | --- |
| MAJOR: a known package directory could conceal an unrecorded binary/data file. | Unknown .dll and .dat under the synthetic numpy directory each fail; real RECORD paths still pass. | Rejected by exact ownership matching; no directory-wide native allowlist. |
| MAJOR: a row could claim an absent file, or an unlisted module could be silently omitted. | Absent-entry row and unknown PYZ module controls through the real coverage validator/inventory. | Rejected; every inventory label has row support and every row has present entries. |
| MAJOR: optional FFmpeg absence or incompatibility could be misrepresented. | Same incompatible lock succeeds with no FFmpeg rows/statements; adjacent tools fail naming main/extra rows on one line; partial sets fail. | Required conditional/refusal behavior is green. No owner HOLD resolution or override. |
| MINOR: audit/locked version or required material could drift. | Independent synthetic audit/lock/installed metadata versions; wrong lock, removed licence and missing source controls. | Drift and missing material rejected; native-specific material completion remains below. |
| MINOR: PyInstaller tooling execution could be confused with artifact code execution. | Inspected actual CArchive writer/reader path and metadata-only planner; no process-launch call. | Clarified module/function docstrings; no product code or binary executed. |

### Exact continuation state

This is the commissioned **coverage-boundary yield before text-provenance tests**.
The dispatcher reads depth; the cell neither estimates it nor starts another
implementation group while that checkpoint is pending. `notices.py` is a planning
API, not yet a runnable notices generator. Specifically still undone:

1. Finish native/component detail for actual Qt/Shiboken, pillow-heif's embedded
   libheif/libde265/x265/MinGW, NumPy/SciPy/Pillow aggregates and OpenSSL/Python.
   Supply the exact Qt release source and LGPL replacement rights, the accepted
   MinGW limitation, and preserve native attribution terms from the audit.
2. Render the complete notices header, per-component/source table, full licence
   bytes and patent notes. Byte-copy the installed PyInstaller per-kind terms /
   Bootloader Exception, verify SHA-256 AND byte count for each root reuse, label
   true provenance/version, deduplicate repeated texts and never copy commercial
   Qt terms. The current root references are not yet reused or verified.
3. Add the explicitly deferred provenance tests: Bootloader Exception equality,
   every root-block reuse path, altered digest/byte-count failures, labels,
   commercial-text omission, and deterministic repeated output.
4. Implement the notices writer/CLI and `build.py --notices` wiring plus its
   tests. Existing build.py and test_tools_package_build.py were not edited.
5. Re-run the requested validation and deliver the completed generator report;
   real built-folder generation, reviews and broader gates remain the seat's.

The firm boundary permits this partial return; no completion of rendering,
source-delivery obligations or N13 acceptance is claimed. Later smoke/ZIP and
workflow/checklist/guide/root notices remain turn 8 and turn 9 as re-split.
Only the two new planning/test modules and this report changed. No network,
real FFmpeg archive access, frozen run, PyInstaller build, desktop GUI launch,
synthetic input, footage/profile write, git write, push, tag, gh command or
workflow dispatch was performed. The seat commits these paths.

## Turn 8: NEW MAJOR rendering-rule STOP (2026-11-05)

### Confirmed conflict and requested ruling

Dispatch 8 item 2 requires both "wheel licence files are byte-copied when
present" and "the GPL-3.0 text appears ONCE, from the folder's
ffmpeg-LICENSE.txt when FFmpeg is carried". Dispatch 6 item 2 also requires
NumPy/SciPy's installed full licence texts. Both installed aggregate files
contain a complete GPL-3.0 text, including the terms and application appendix.
Thus byte-copying just these two required files already emits TWO full copies,
before any FFmpeg licence is rendered. Whole-file content deduplication cannot
resolve this: their other component notices differ, and even their GPL-3.0
tails differ in upstream HTTP/HTTPS URLs and a final newline.

This is an in-envelope MAJOR ambiguity, not a licence-incompatibility claim.
The brief's plan-4.5 no-assumptions rule requires a ruling before choosing which
text requirement to relax. No renderer, tests or wiring were written around it.

**Requested CHARC ruling (recommended):** preserve the installed wheel files
byte-for-byte, allowing their embedded GPL-3.0 copies; interpret ONCE as one
dedicated FFmpeg GPL-3.0 block, shared by all FFmpeg component rows. This avoids
editing any publisher's aggregate text. Alternatively, explicitly authorize
splitting wheel aggregates into verbatim slices and replacing their embedded
GPL-3.0 text with references to a shared block, with a rule for differing
upstream text variants and the no-FFmpeg case. The cell has chosen neither.

### Cheap reproduction (read-only inputs; no product entry point)

All probe output is under `work/c63b-8-evidence/`, inside this worktree:

| Evidence file | Observed result |
| --- | --- |
| `gpl3-byte-copy-conflict.log` | Exit 0; NumPy aggregate 45,831 bytes, GPL-3.0 starts at byte 10,681; SciPy aggregate 45,881 bytes, GPL-3.0 starts at byte 10,734. Each contains one full GPL-3.0 heading followed by the terms and application appendix. Concatenating byte-exact inputs yields `BYTE_COPY_BOTH_GPL3_COUNT: 2`. |
| `gpl3-equivalence.log` | Exit 0; whitespace-normalized tails differ too, so an exact-content deduplicator cannot merge them. |
| `gpl3-tail-diff.log` | Exit 0; independent line diff identifies the HTTP/HTTPS URL variants, a different why-not-lgpl URL and the final-newline difference. |

The probes only read the installed NumPy/SciPy licence files. They do not open,
extract or execute the real FFmpeg archive, invoke PyInstaller, import product
entry points, or reach the network. The separate interpreter-material inventory
is saved at `work/c63b8-interpreter-inputs.log`; no new ruling is requested on it
in this turn.

### Turn-8 item disposition and validation

| Commissioned item | RED / GREEN and current state |
| --- | --- |
| Native-component details and header | Not implemented this turn; prior planner retained. |
| Full-text rendering and provenance tests | Blocked before implementation by the confirmed rule conflict above; no RED/GREEN unit-test cycle claimed. |
| Determinism | Deferred with rendering; no result claimed. |
| Writer / CLI / build `--notices` wiring | Deferred; no build or tool-test changes. |
| Synthetic bundled-entry vs row table, with and without FFmpeg | No new rendered table produced. Turn 7's inventory/coverage evidence remains historical evidence, not a turn-8 rerun. |
| Per-text provenance labels | Not rendered yet; turn-6's audited-block SHA-256/byte-count and truthful upstream-copy rules remain binding. |
| ruff / format / mypy / darwin mypy / four-module pytest | Not run: input-rule STOP before any code or test change. The turn-7 results are not represented as current validation. |

MinGW limit carried unchanged: the pillow-heif wheel does not name the toolchain
release; libgcc_s_seh-1.dll and libstdc++-6.dll use GPL-3.0 with the GCC Runtime
Library Exception, and libwinpthread-1.dll uses MIT/BSD, with the disclosed
unversioned source pointers. CHARC's tracking row remains due at accept.

### Verification-loop record and handoff

Suspected MAJOR conflict -> independently confirmed from both installed files,
heading counts and a tail diff -> no guessed resolution or product fix -> yield
to CHARC. No Reviewer A round occurred. The FFmpeg zvbi HOLD remains unchanged.
This is one logical report-only turn; the seat commits only this report.

No network fetch, real FFmpeg archive access, frozen run, PyInstaller build,
desktop GUI launch/input, footage/profile write, QUIT_SCRIPT test, git write,
push, tag, gh invocation or workflow dispatch occurred. No files outside the
owned report and ignored worktree evidence were changed. The next dispatch
needs the rendering ruling before the four commissioned implementation items
can continue. Depth is pending the dispatcher's reading; no estimate is offered.

## Turn 9: rendering, writer, wiring and an OpenSSL input STOP (2026-11-05)

GPL-3.0 'once' = one FFmpeg block; wheel aggregates keep their embedded copies verbatim (seat clarification, dispatch 9).

### Built this turn

- `render_notices` validates coverage, emits the component/source table and
  supported entry labels, and renders referenced full-text blocks. Raw wheel
  bytes, including CRLF and embedded GPL texts, are unchanged. Copied Markdown
  uses a fence longer than any backtick run in its content.
- Every reused upstream block (root texts 36-44) is checked against BOTH its
  recorded SHA-256 and UTF-8/LF byte count before use. Provenance includes the
  using component/version, true upstream URL/release and the exact words
  "the 1.0.0 audit's upstream copy". Commercial Qt terms are excluded from
  selection and rejected even if explicitly supplied to the renderer.
- Qt/Shiboken rows name the installed 6.12.0 release's Qt/binding sources,
  dynamic redistribution, replacement/relinking and debugging/reverse-engineering
  rights. A wheel's actual LGPL text wins over upstream fallback. An upstream
  source version that differs from the installed component fails generation.
- Native pillow-heif rows come from the installed wheel manifest and only
  appear for supported native file entries: libheif 1.23.6, libde265 1.1.3,
  x265 4.3 and the unversioned MinGW runtime. Header/copyright and licence
  blocks are retained; LGPL replacement rights and the accepted MinGW limit
  are explicit. NumPy/SciPy/Pillow native aggregate texts are redistributed.
- PyInstaller bootloader is GPL-2.0-or-later WITH Bootloader Exception;
  run-time hooks are Apache-2.0. Both rows reference the installed COPYING.txt,
  which is copied once in full, including the exception, per-kind sections
  and full licence texts. Tests also compare the exception/hooks slices.
- The header states Clearwater's GPL-2.0-or-later terms and corresponding-source
  pointers. When FFmpeg is present it states the combined GPL-3.0 terms permitted
  by the or-later grant. The existing incompatible-FFmpeg refusal is retained;
  component patent-only notes are rendered from the lock's licence_note fields.
- `write_notices` validates before changing output, includes the generated file
  in Clearwater's coverage, and writes through a flushed/fsynced temporary file
  outside the artifact folder, then os.replace. Existing notices survive a
  validation/publication error; first-write reservations and temporary files
  are cleaned on failure. Repeated successful writes have identical bytes.
- `python -m tools.package.notices FOLDER` runs the generator; optional --audit,
  --uv-lock and --ffmpeg-lock select local input records. Failures return 1 with
  one ASCII-safe stderr line. Invalid CArchive input is normalized to that path.
- `build.py --form onedir --notices` invokes the generator after the FFmpeg
  step and bundle/hidden-import checks. A notices failure fails the build.
  --notices with onefile or pack-only operations is refused at argument parsing.

No new dependency, runtime/product entry change, frozen-interface change,
network fetch or real build was needed. This turn bundles the four generator
items explicitly commissioned together by dispatch 9.

### Synthetic bundled-entry vs row table (both variants)

The complete fixture uses synthetic DLL/PYD bytes and real PyInstaller archive
writers for a non-executable CArchive/PYZ. It does not launch an executable.
Installed NumPy/SciPy/Pillow texts and pillow-heif's manifest are the licence
inputs; PyInstaller's installed COPYING is separately byte-tested. The fake
FFmpeg variant uses the existing compatible one-component lock fixture, NOT the
real locked zvbi-containing bundle.

`work/c63b-9-final/test_complete_native_fixture_h0/` has 22 inventory entries,
14 rows, 17 full-text blocks and a 262,154-byte generated document. The `h1/`
variant has FFmpeg: 26 entries, 16 rows, 18 text blocks and 263,305 bytes. The
documents are in each fixture's `release/THIRD_PARTY_NOTICES.md`; sibling
`rendered-plan.json` records every row, entry, licence, version and source.
An entry may support both a distribution row and its native-component row.
The unions equal the complete inventory in both variants; no row claims an
absent entry. Here `file:` and `_internal/` prefixes are omitted for readability:

| Row | Supported entries (without FFmpeg) | With FFmpeg |
| --- | --- | --- |
| Clearwater | Clearwater.exe; THIRD_PARTY_NOTICES.md; archive:__main__; pyz:clearwater | Same |
| Python 3.12.13 | python312.dll; pyz:json | Same |
| numpy 2.5.4 | numpy/_core/test.pyd; pyz:numpy | Same |
| scipy 1.18.1 | scipy/synthetic.pyd | Same |
| pillow 12.3.0 | PIL/synthetic.pyd; pyz:PIL | Same |
| pillow-heif 1.8.1 | The six native DLLs in the next four rows | Same |
| pillow-heif / libheif 1.23.6 | libheif-abc.dll | Same |
| pillow-heif / libde265 1.1.3 | libde265-0-abc.dll | Same |
| pillow-heif / x265 4.3 | libx265-217-abc.dll | Same |
| pillow-heif / MinGW runtime | libgcc_s_seh-1-abc.dll; libstdc++-6-abc.dll; libwinpthread-1-abc.dll | Same |
| pyside6-essentials 6.12.0 | PySide6/Qt6Core.dll | Same |
| shiboken6 6.12.0 | shiboken6/Qt6Core.dll (synthetic ownership fixture) | Same |
| PyInstaller bootloader 6.22.3 | Clearwater.exe; archive:pyimod01_archive; archive:PYZ.pyz | Same |
| PyInstaller run-time hooks 6.22.3 | archive:pyi_rth_inspect | Same |
| FFmpeg / ffprobe | Absent; user-obtained statement | ffmpeg.exe; ffprobe.exe; ffmpeg-BUILD.txt; ffmpeg-LICENSE.txt |
| FFmpeg component: x265 | Absent | Same four FFmpeg entries |

Both variants state that the GPU pack is user-obtained, not redistributed.
Without FFmpeg there are zero FFmpeg rows/blocks and its user-obtained statement;
with it there is exactly one dedicated FFmpeg block shared by its two rows.

### Per-text provenance

`work/c63b-9-evidence/final-fixture-provenance.log` records every emitted label.
Direct inputs are labelled `Build source: Clearwater 1.0.0; LICENSE`,
`Build source: Python 3.12.13; LICENSE.txt`, or `Installed wheel: <component>
<version>; <dist-info relative path>`. The wheel paths are NumPy LICENSE.txt,
SciPy LICENSE.txt, Pillow LICENSE, pillow-heif LICENSE.txt and
LICENSES_bundled.txt, and PyInstaller COPYING.txt. Tests on the REAL installed
NumPy/SciPy/PyInstaller files require exact raw-byte inclusion, not normalized
text. The fixture labels identify their fixture-wheel copies truthfully.

Every fallback label contains "the 1.0.0 audit's upstream copy" and its true
source URL. These are the root blocks used, each rendered once even if shared:

| Root block | True upstream source/release |
| --- | --- |
| text-36 | qt/qtbase v6.12.0, LICENSES/LGPL-3.0-only.txt (shared LGPL text) |
| text-37 | Multicorewareinc/x265 4.3, COPYING |
| text-38 | Multicorewareinc/x265 4.3, source/x265.h copyright/source grant |
| text-39 | strukturag/libheif v1.23.6, COPYING |
| text-40 | strukturag/libde265 v1.1.3, COPYING |
| text-41 | mingw-w64/mingw-w64 master, COPYING; explicitly unversioned |
| text-42 | strukturag/libheif v1.23.6, libheif/api/libheif/heif.h |
| text-43 | strukturag/libde265 v1.1.3, libde265/de265.h |
| text-44 | mingw-w64/mingw-w64 master, mingw-w64-libraries/winpthreads/COPYING; explicitly unversioned |

FFmpeg's additional label is `Bundled FFmpeg: <locked version>;
ffmpeg-LICENSE.txt`, under the single heading `Bundled FFmpeg GPL-3.0`.
No wheel licence file is cut or rewritten to remove embedded GPL text.

MinGW limitation: **the wheel does not name the toolchain release** for
libgcc_s_seh-1.dll, libstdc++-6.dll and libwinpthread-1.dll; terms are GPL-3.0
with the GCC Runtime Library Exception for libgcc/libstdc++, MIT / BSD for
winpthreads; source pointers remain explicitly unversioned. CHARC's accept-time
tracking row remains due.

### RED -> GREEN and final validation

All runner output is in `work/c63b-9-evidence/`:

| Item / log | Result |
| --- | --- |
| `red-render.log` | 42 failed, 14 passed: renderer absent; every new provenance/rendering control failed before implementation. |
| `green-render.log` | 56 passed: nine reuse paths, each body/hash/size tamper, verbatim installed wheels, commercial exclusion, header, FFmpeg block and rendering determinism. |
| `red-native.log` | 7 failed, 57 passed: native rows/Qt rights/wheel preference/source-version checks absent. |
| `green-native-2.log` | 64 passed. First green attempt also exposed a fixture expectation using LF despite write_text producing CRLF; expectation corrected to actual input bytes. |
| `red-writer.log` | 8 failed, 141 passed: writer/CLI/build flag absent. |
| `green-writer-2.log` | 149 passed. Initial build stub only made onefile layout; replaced within the new test with a --distpath-driven synthetic archive writer. |
| `red-openssl.log` | 1 failed, 68 deselected: a synthetic libcrypto DLL was incorrectly accepted under Python's PSF row. |
| `red-archive.log` | 1 actual invalid-CArchive failure, plus 2 fixture assertions incorrectly counting duplicate provenance URL occurrences; assertions corrected to count actual LGPL text blocks. |
| `green-archive.log` | 3 passed, 69 deselected: both complete native fixtures and malformed-archive refusal. |
| `ruff-check-final.log` | Exit 0, All checks passed! |
| `ruff-format-final.log` | Exit 0, 334 files already formatted. |
| `mypy-final.log` | Exit 0, Success: no issues found in 165 source files. |
| `mypy-darwin-final.log` | Exit 0, Success: no issues found in 165 source files. |
| `pytest-validation-final.log` | Exit 0, 408 passed in 12.50 s (74 notices, 60 FFmpeg, 81 build, 193 frozen-entry). |
| `cli-help.log` | Exit 0, actual `python -m tools.package.notices --help` invocation. |

The final pytest command is dispatch 9's exact four-module selection with
`PYTHONPATH=scripts`, `-p sandbox_mkdir_shim -p no:cacheprovider`, timeout 300
and fresh basetemp `work/c63b-9-final`. The initial requested basetemp
`work/c63b-9` run passed 403 before the final integration/error-path additions.
**No sandbox-only residual** remains in this selection. Earlier uv logs retain
the inherited VIRTUAL_ENV warning; final validation explicitly selects the
worktree's .venv. Initial lint long lines/import ordering and one mypy tuple
inference error were fixed before the final checks. Final source code was
already in place for both mypy runs; subsequent edits only added/formatted tests
and this report.

### NEW MAJOR input STOP: OpenSSL redistribution material

`work/c63b-9-evidence/openssl-materials.log` is a bounded, read-only stdlib probe:
the build interpreter reports `OpenSSL 3.5.5 27 Jan 2026`; both
`DLLs/libcrypto-3-x64.dll` and `DLLs/libssl-3-x64.dll` exist. At its root/DLLs
there is only Python's LICENSE.txt, with ZERO OpenSSL/Apache License mentions.
The root notices have no separate OpenSSL row or full-text heading. Their Python
source-install row merely names the DLLs and points indirectly to
python-build-standalone, explicitly disclaiming redistribution.

The RED synthetic libcrypto case independently confirms the consequence:
the previous planner assigned it Python's PSF terms and generated no OpenSSL
row/text. The corrected guard refuses a folder with these interpreter OpenSSL
DLLs with `OpenSSL missing redistributed licence/source material`; it cannot
silently claim a binary audit is complete. This is an input failure covered by
the commissioned missing-material refusal, not a new licence policy or network
workaround. The synthetic fixtures that do not carry OpenSSL still succeed.

**Ruling/material requested:** the seat supplies the verified OpenSSL 3.5.5
copyright/licence text and exact source/build record and authorizes its input
surface (for example the already commissioned per-binary audit data file, which
is not owned by dispatch 9, or a specifically granted audited upstream block).
Then the OpenSSL component row can be completed and the guard replaced by real
material validation. No source URL, full text or exemption was invented.
The real built-folder per-binary audit must also check Python/wheel platform
runtimes against the source audit's stated MSVC/Mesa/other-native conditions;
the synthetic fixture is not evidence that those obligations are closed.

### Verification loop, limits and next handoff

| Suspect / severity | Independent confirmation | Disposition |
| --- | --- | --- |
| MAJOR: upstream fallback could copy tampered text or claim wheel provenance | All nine real audited blocks; each independently altered body, digest and length; label checks | Fixed/green; both integrity fields checked, true upstream labels retained. |
| MAJOR: wheel licence rewriting or commercial Qt leakage | Raw installed NumPy/SciPy/PyInstaller byte comparisons; two Qt-wheel branches plus direct commercial-input control | Fixed/green; wheel bytes unchanged, commercial material never copied. |
| MAJOR: rows might assert absent native binaries or wrong source release | Native-free wrapper, manifest version mutation, full native variants with coverage union | Fixed/green; rows supported by entries, incompatible source versions refused. |
| MAJOR: failed writer could damage prior notices or leave a phantom file | Unknown-file validation and injected os.replace failure, with/without previous output | Green; previous content retained and temporary/reservation files removed. |
| MINOR: invalid archive bypasses CLI one-line failure | Actual invalid CArchive fixture, without launching it | Confirmed and fixed by normalizing reader RuntimeError to ValueError. |
| MAJOR: Python's source-install terms hide redistributed OpenSSL | Interpreter material inventory and RED synthetic libcrypto control | Confirmed; fails closed, verified material/ruling still owed by seat. |
| MINOR: repeated provenance URL implied duplicate text | Compared full shared LGPL block count independently | False positive; heading and Source label repeat the URL, actual text appears once. |

The final pass over implemented rendering/writer/wiring requirements found no
additional issue; the explicitly open OpenSSL item prevents claiming the full
generator/native audit done. No Reviewer A pass occurred in this turn; the
dispatcher owns that Claude review. The separate zvbi HOLD is unchanged.
Real artifact generation, smoke/ZIP, workflow/checklist/guide/root-notices edits,
actionlint and seat V4/encoder evidence have not run here and remain future work.

All changes are in this turn's four owned code/test files and this report.
No new dependency, network fetch, real FFmpeg archive access, PyInstaller build,
frozen executable run, desktop GUI/input, footage/profile write, QUIT_SCRIPT test,
git write, push, tag, gh invocation, workflow dispatch or mailbox post occurred.
Depth remains dispatcher-read; the last supplied figure was about 104K, not a
current estimate. The seat commits these five paths as one generator turn.
