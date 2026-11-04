# WP6.3a - GPU pack downloader

Candidate report, 2026-11-04. Parts 1 and 2 added the installer and request
surfaces. Dispatch 5 folds Reviewer A r1 into the merged candidate at
`f00172a6`, following CHARC's rulings including the checker-cancellation grant.
Reviewer A r2, Reviewer B, the release gate and the real-download seat proof
remain with the orchestrator.

## Design as built

`gpu_pack_install.plan()` selects one compatible locked wheel per distribution
using the loader's tag rules. Each table row carries filename, sha256, exact
lock URL and byte size; the lock-equality test covers all four fields plus
distribution name/version. On this Windows/cp312 host the plan selects eleven
wheels, totaling **1,725,155,461 bytes (1,645.24 MiB)**. The largest archive is
cuBLAS at **553,162,896 bytes (527.54 MiB)**. These figures were read from the
product plan, not copied from the brief's superseded 1.2 GB estimate.

The conservative installed estimate is **2,530,213,888 bytes (2,413 MiB)**.
Required free space is `ceil((installed estimate + largest archive) * 1.1)`:
**3,391,714,463 bytes**. Each wheel is deleted after extraction, so the budget
holds the installed tree plus one archive, rather than all downloaded wheels
at once. This is an estimate, not the seat's measured installed census.

The product installer is standard-library-only. It uses the locked HTTPS
`files.pythonhosted.org` URLs, a default TLS context/system certificate store,
the Clearwater version as its user agent, a 30-second socket timeout and 1 MiB
chunks. Redirects must retain the pinned origin. Transport errors get two
retries separated by a cancellation-aware two-second pause. Retries restart
the archive and digest, while reported byte counts retain a high-water mark.
A complete body with a wrong size or SHA-256 fails without retry; a truncated
HTTP body is a transport error.

All filesystem work is beneath the calculated `pack_root()`. Before network
work, install cleans dead-process partials, accepts an already valid pack as
a successful no-op, checks free space and removes a rejected existing pack
following the user's request. Work goes into `<stamp>.partial-<uuid>/`, with
separate `downloads/` and `site-packages/` directories. Member names are
validated before extraction; traversal, absolute/drive/backslash names,
top-level `<distribution>-<version>.data/` paths, links and special members are
refused. Ordinary nested package data such as `cupy/.data/` is accepted.
Wheel RECORD bytes are
preserved; no INSTALLER, REQUESTED, direct_url.json or bytecode is generated.

Publication order is:

1. Build an in-memory manifest from the installed metadata.
2. Run the loader's full checker with that in-memory document (S1).
3. Write the manifest inside staging.
4. Run the cheap check against the manifest on disk.
5. Rename staging to the final stamp folder with `os.replace`.

Failure or cancellation removes staging; a cleanup failure is logged and
disclosed in the result. The product result carries success/failure text,
installed path and cancellation state. Removal only accepts the current stamp
under the calculated root. It renames the pack to a partial folder before
deleting any file. A rename blocked by an open file leaves the pack intact and
writes the empty `<stamp>.remove` marker for the next GUI start. Other
filesystem failures are reported. Matching plain partial folders are cleaned
under the operation lock; files, symlinks and reparse points with partial names
are skipped and logged without being followed.

`build.py` delegates its manifest construction and writer to the product
module. Its hand-filled writer retains the folder-name-equals-STAMP refusal;
`--verify` and the bundle checker were not changed. The shared checker's only
other changes are the ruled four-field filename/hash projection (S2), the
full-check lstat/link/reparse rejection (S3), the pure removal-marker path helper
and the granted optional full-check cancellation hook. The cheap startup check is
unchanged. This corrects WP6.1's report line 468: the promised reparse guard
was absent there and is implemented here under DR-128. Every Windows reparse
tag is rejected by the full check, as ruled. The optional dist-info advisory
was not tightened; it remains for 6.3b.

The frozen-only activation filter ignores only matching UserWarnings with
`CUDA path could not be detected.*` immediately before pack loading. This
turn does not set CUDA_CACHE_PATH or CUPY_CACHE_DIR (6.3b).

## Request surfaces

Tools contains **Install GPU support...** and **Remove GPU support**. Both
are hidden when the platform has no pack root. Install is disabled during
install/removal; Remove additionally requires the stamp folder to exist.
Opening Tools and job completion refresh their enabling. No download starts
when the dialog opens. The shell retains the window-modal dialog and opens it
with `open()`. Removal uses a retained window-modal Yes/No prompt, also with
`open()`, then runs the filesystem operation on the existing QtJobRunner.

The install dialog shows every distribution name/version, computed download
bytes/MiB, installed estimate and calculated destination. **Download and
install** is the explicit request. Byte progress is scaled to 0..1000 for
Qt, with the current wheel filename alongside it. Cancel, Escape and window
close request cancellation through the job handle and keep the dialog alive
until worker cleanup completes. The completion text is:

> GPU support is installed. Restart Clearwater to use it.

The licence statement is verbatim:

> GPU support downloads CuPy and NVIDIA's CUDA runtime libraries from PyPI into your user folder. The NVIDIA libraries are provided by NVIDIA under the NVIDIA Software License Agreement (the file `License.txt` inside each nvidia package after the install); CuPy is MIT. Clearwater does not redistribute them.

Worker callables are module functions holding no Qt objects. They convert the
product result to the existing IF-8 JobResult; its warnings tuple carries the
successful completion text because that frozen interface has no success-text
field. The dialog renders that text as completion, without a warning banner.
The existing runner delivers progress and completion on the interface thread.

For the specified idle reason beginning `CPU: CuPy not installed`, an available
pack root adds `Tools > Install GPU support...` to the device label's tooltip.
There is no automatic prompt. Removal says that it takes effect at the next
start; it does not unload CuPy already imported by the running application.
After a deferred removal, the shell displays `CPU: GPU pack removal pending`,
including when a source is open.

The dispatch order in `clearwater.__main__.main` is:

1. Frozen multiprocessing refusal.
2. Executable-folder PATH step.
3. Shared source/frozen `--install-gpu-pack` / `--remove-gpu-pack` row, with no
   further arguments; no loader, logging setup or Qt import on this row.
4. Existing frozen export-worker branch (WP-DR125 worker-side isolation intact).
5. Existing frozen interpreter re-entry branch.
6. Existing frozen logging setup, then GUI-only pending-removal application,
   loader activation unless the marker remains, and GUI.

The worker and frozen `-m` branches only read the marker and skip activation
when it exists; they never call the installer or delete anything. A skipped
`-m` keeps the existing "no GPU pack is loaded" refusal. Source and frozen GUI
starts apply pending removal under the operation lock. Install applies pending
removal under its already-held lock before staging or network work and refuses
an in-use pack with "GPU support is loaded by a running Clearwater; close it
and try again". Remove with an existing marker is an idempotent success.

The headless install prints one stderr line per wheel and then the product
message. Success, already-installed and remove-with-none exit 0; failure and
cancellation exit 1. Extra arguments are refused before installer work. A
windowed `Clearwater.exe` prints only when output is redirected; the guide
shows redirection for both requests. The source form can create/remove the
pack, but the loader continues to activate it only in frozen builds.

The guide deliberately describes the dialog's calculated download size rather
than storing a literal that would become stale at a lock bump. Its GPU
paragraph is the only section changed. The packaging README identifies the
downloader as normal and retains the hand-filled developer recipe. Its frozen
worker standard-input section is untouched.

## Prior build-turn validation

All pytest commands in the cell use `PYTHONPATH=scripts`,
`QT_QPA_PLATFORM=offscreen`, `-p sandbox_mkdir_shim -p no:cacheprovider` and
disposable worktree basetemps. All runner output is under `work/wp6.3a/`.
Loopback works in this sandbox. Fake-index tests use actual urllib against
synthetic wheels, not a mocked urlopen. The autouse guard refuses connections
outside the fixture's exact loopback port; teardown checks the request log.
No test fetches from the real index or activates a GPU pack.

| Command | Result |
| --- | --- |
| `uv run --no-sync ruff check .` | All checks passed |
| `uv run --no-sync ruff format --check .` | 327 files already formatted |
| `uv run --no-sync mypy` | Clean, 163 source files |
| `uv run --no-sync mypy --platform darwin` on the five owned product modules | Clean, 5 source files |
| Full `uv run --no-sync mypy --platform darwin` | Exactly the four ruled baseline errors, below |
| Required five-file pytest selection, `--timeout 300 --basetemp=work/c63a-3` | 385 passed in 25.94 s |
| New entry/dialog selection | 19 passed in 1.32 s |
| Final five-file selection including three additional CLI cases, `--timeout 300 --basetemp=work/c63a-3final --junitxml=work/wp6.3a/tests-3-final.xml --durations=0` | 388 passed in 25.91 s |
| All `tests/test_gui_*.py`, `-m gui --timeout 600 --basetemp=work/c63a-3gui` | Stopped at the existing source-GPU test; sandbox residual below |
| Same GUI files, `-m "gui and not gpu" --basetemp=work/c63a-3gui-nogpu` | 454 passed, 21 deselected in 63.74 s |

The final five-file selection collects as **376 parallel + 12 serial = 388**,
with no fullclip remainder. All **37** installer-module cases land in the
parallel leg; all **10** dialog cases land in the serial leg. The other two
serial cases are the existing stdin-shim checks. Collection evidence is
`collect-3-parallel.log` and `collect-3-serial.log`.

Fake-index and headless matrix, all passed. Times below are the maximum JUnit
case time in each group, including setup/teardown, from the final run (not a
download-throughput benchmark). Synthetic transport tests disable the retry
pause; they still count all three HTTP attempts where required. Full
per-test timings are in `tests-3-final.xml` and `install-matrix-3.log`.

| Cases | Count | Max case seconds |
| --- | ---: | ---: |
| Plan/tag selection and happy path/full check/unchanged RECORD | 2 | 0.170 |
| Third-wheel hash mismatch, no subsequent requests | 1 | 0.126 |
| Short body, exactly three requests, cleanup | 1 | 0.061 |
| Retry recovery and monotonic byte progress | 1 | 0.183 |
| HTTP failure, exactly three attempts | 1 | 0.078 |
| Cancel in the second wheel, cleanup | 1 | 0.107 |
| Off-origin redirect (host and port), zero second-server hits | 2 | 0.125 |
| Hostile members: traversal, absolute, drive, backslash, link, .data | 6 | 0.091 |
| Already installed: zero requests | 1 | 0.215 |
| Rejected pack replacement and dead-process partial cleanup | 1 | 0.187 |
| Low disk: zero requests; largest-wheel budget | 2 | 0.203 |
| Disk full and final rename failure: rollback | 2 | 0.188 |
| Removal: read-only file, pack/partial cleanup, outside-root refusal | 2 | 0.186 |
| Unlisted-file guard | 1 | 0.216 |
| Full-check/manifest/cheap-check/rename order and disk-manifest corruption | 2 | 0.019 |
| Unsupported platform and production URL-origin policy | 3 | 0.010 |
| Headless: progress, no-ops, failure, cancel, extra args, no stderr | 8 | 0.285 |

The four pre-existing full-Darwin errors are exactly:

- `src/clearwater/io/video/pipes.py:56`: CREATE_NO_WINDOW attribute.
- `tools/prototype/bench.py:1159`: unreachable statement.
- `tools/prototype/bench.py:1480`: getwindowsversion attribute.
- `tools/spike_io/transport.py:950`: unreachable statement.

The first concurrent win32/Darwin mypy invocation produced an internal error;
the sequential owned-module rerun passed, and the full Darwin rerun produced
only the four baseline errors. PowerShell did not expand the literal GUI
wildcard on the first attempt (no tests ran); subsequent regression commands
expand the file list explicitly.

The requested `-m gui` command also selects the existing GPU-marked
`test_gui_status.py::test_real_selection_through_the_shell_shows_gpu`. Its
five-minute faulthandler dump shows `core/backend.py:964` calling CuPy's
`arange`, CUDA compilation/cache save and finally `tempfile._mkstemp_inner`
at line 256, while trying to create a compiler-cache temporary file outside
the writable worktree. `CUPY_CACHE_DIR` is unset in the runner environment;
the installed CuPy's `_compiler_cache.py:27,93` defaults to
`~/.cupy/kernel_cache`, and line 140 passes that directory to NamedTemporaryFile.
It remained stuck there; no Python OSError was reported before termination.
This is a sandbox residual, not a failed assertion in the changed shell.
`gui-regression-3-expanded.log` holds the stack. Only this invocation's pytest
process was terminated, after verifying its executable argument and exact
`--basetemp=work/c63a-3gui` through psutil. The preliminary CIM lookup was
denied (`0x80041003`); psutil provided the task identity without an elevation.

The safe regression rerun excludes GPU-marked tests and leaves the source-GPU
check to the seat. The broad command did enter an existing source GPU probe;
that is disclosed rather than counted as a hardware proof. No downloaded GPU
pack was activated, no cache-path product change or workaround was added, and
the installer fake-index transport was not substituted.

## Verification loop

| Suspected issue | Confirmation or rejection | Disposition |
| --- | --- | --- |
| Install/remove requests could fall through to the GUI | New isolated entry checks failed on the unchanged branch: 9 failures, with GUI/Qt blocked | Confirmed; shared Qt-free row added; tests pass |
| Dialog and menu request surface absent | Offscreen test collection failed on the missing module | Confirmed; dialog and Tools actions added; tests pass |
| Opening the dialog could start work automatically | Scripted runner records zero calls until the request button | Rejected as a remaining defect |
| Cancel/window close could lose worker cleanup or permit overlapping jobs | Scripted cancel and active-close checks retain the dialog; both actions stay disabled until completion | Rejected as a remaining defect |
| Large download byte counts could overflow a Qt progress integer | Byte reports are scaled to 0..1000; quarter/full progress and final delivery checked | Rejected as a remaining defect |
| Removal could run before confirmation or on the interface thread | No/Yes scripted checks and module-level worker adapter; install adapter's actual runner test records a non-main thread | Rejected as a remaining defect |
| CLI removal failure or absent windowed stderr could break the result contract | Explicit outcome/status checks and no-stderr progress/completion checks | Tests added for both paths |
| Files edited through Windows tools retained CR bytes | Byte census found CRLF in five existing owned files | Confirmed; all nine changed files normalized to LF |
| Broad GUI run hung in new product code | Five-minute stack located the existing source-CuPy compiler-cache write, not downloader/dialog code | Rejected as introduced; sandbox residual retained for the seat |
| Final in-envelope pass | Static checks, 388 target tests, 454 non-GPU offscreen GUI tests, source/diff inspection and 376+12 collection partition | No new in-envelope finding |

The build turn above preceded Reviewer A. The dispatch-5 fold-in and its fresh
validation are recorded below; this report is not a review-convergence claim.

Source grep finds no dialog `.exec(` call. The only `.exec(` in the two GUI
files is the existing `shell.run` application's `app.exec()` event loop.
The after-run, read-only profile existence check found real
`%LOCALAPPDATA%/Clearwater` absent. `%APPDATA%/Clearwater` exists; it was not
inspected or edited. The cell has no before-run profile census in this fresh
turn. The seat must still perform its required before/after checks.

## The seat run

SEAT TO FILL

## Limits and remaining handoff

There is no resume across sessions; retry means a fresh transaction. Proxy
support is urllib's system/environment handling, with no proxy dialog. PyPI
availability and throughput are external. macOS has no pack; Linux root and
table support are not a proved Linux installer. No dependency was added.
The ruled operation lock uses Windows held-open-file semantics and guarded
`fcntl.flock` off win32. Footage and the owner's profiles are untouched.

The downloader pack's expected census is **2,679 files**, versus the hand-filled
pack's 2,701: uv added 22 `INSTALLER` / `REQUESTED` files (two per distribution)
that the downloader deliberately does not create. Its bytes are the sum of the
eleven wheel RECORDs' sizes (about 2,412.3-2,412.6 MiB), to be measured at the
seat. The seat's acceptance criterion is file-set equality with those RECORDs
and a passing `--verify`, rather than equality with uv's extra files. These are
expectations, not cell results. Real download, frozen build, two GPU worker runs, mapped-file
proof, product removal and real-profile absence checks belong to the seat.
The cell wrote no seat/download script and ran no frozen executable. Reviewer
A convergence, Reviewer B and the final gate are pending.

## Reviewer A r1 fold-in (dispatch 5)

All eleven findings were adjudicated against CHARC's complete ruling packet.
The candidate does not claim Reviewer A convergence until the seat runs r2.

| Finding | Classification and change | Discriminating coverage |
| --- | --- | --- |
| 1 | CRITICAL, confirmed, fixed: `.data` refusal applies only to the first path component | `test_nested_package_data_installs`, the existing top-level hostile-member case, and eleven `test_real_locked_record_member_names_are_allowed` cases reading actual installed RECORDs without importing their packages |
| 2 | MAJOR, confirmed, fixed: rename before deleting; a blocked rename writes the empty marker and preserves every pack file; pending removal is retried only at GUI startup or an explicit install | `test_remove_renames_before_deleting`, `test_remove_in_use_defers_intact_and_is_idempotent`, the real Windows held-open-file test, `test_pending_removal_retries_and_clears_marker`, both install-with-marker cases, all three entry sites and the deferred-removal status test with and without an open source |
| 3 | MINOR, confirmed, corrected: expected downloader census 2,679, excluding uv's 22 added files | Corrected census and file-set acceptance criterion above; real census is SEAT TO FILL |
| 4 | MINOR, confirmed, fixed: rejected-pack notice in the dialog before the request and on stderr before headless installation | `test_rejected_pack_plan_warns_before_request`, `test_headless_replacement_notice` |
| 5 | MINOR, confirmed coverage gap, fixed: oversized body test observes each actual `.part` write, no retry and full cleanup | `test_oversized_body_never_writes_past_locked_size_or_retries`; executed m2b mutation fails on 2,955 written bytes versus the 128-byte locked limit |
| 6 | MINOR, confirmed, fixed: one held-open root lock covers install, removal, pending-removal application and every partial sweep, including failure cleanup | Three `test_operation_lock_refuses_second_operation` cases, `test_stale_operation_lock_is_broken`, two isolated headless lock-refusal/exit-1 cases |
| 7 | ADVISORY, banked by CHARC: malformed/missing Content-Length handling | No change; accept register handoff |
| 8 | ADVISORY, confirmed, fixed under the turn-4 grant: optional full-check cancel before each listed payload hash, cancellation re-raised instead of converted, unpack activity reported per member | Three checker-hook cases and `test_cancel_during_full_check_cleans_without_manifest`, which observes exactly one payload hash and forbids manifest writing; `test_unpack_reports_work_after_download` |
| 9 | ADVISORY, confirmed, fixed: skip and log non-directory/linked partial names | `test_partial_file_is_skipped_and_logged`, symlink and real NTFS junction cases in `test_partial_link_is_never_followed`; outside payload stays byte-identical |
| 10 | ADVISORY, out of envelope, banked by CHARC: hostile-wheel/local-attacker extraction hardening | No change; accept register handoff |
| 11 | ADVISORY, banked by CHARC: dialog lifetime, duplicate tooling tag parser, Linux estimate, path length | No change; accept register handoff |

`<root>/.install.lock` is exclusively created and held open throughout each
operation. On Windows, inability to unlink an existing held-open lock refuses
the operation; an unheld stale file can be removed. Off win32, nonblocking
`fcntl.flock` distinguishes a live owner from a stale file. The creator checks
the inode after taking that lock so it cannot enter the operation with an
orphaned lock if a stale-lock contender won first. An install applies pending
removal through the shared internal routine while retaining its lock, avoiding
a nested acquisition. All partial sweeps occur under that same lock.

Successful deferred removal says exactly:

> GPU support will be removed at the next start

The marker helper in `gpu_pack` only calculates a path. The installer performs
all writes and deletions. `apply_pending_removal()` logs one failure line and
keeps the marker on failure. The GUI start then skips activation; children
only test marker existence, log `GPU pack removal pending`, and skip activation.
The pending-marker install refusal precedes any network request. The GUI's
completion status uses the same product text, and updates the device label to
`CPU: GPU pack removal pending` even with an open photo. The licence statement
and successful install completion text above are unchanged.

Cancellation during the final full check takes effect at the next file
boundary, at most one file's hash. CHARC's supplied laptop estimate is a
527.54 MiB cuBLAS file taking about 1-2 seconds; the cell did not measure a
real-pack hash latency. There is no per-block callback in the loader's hash
routine. `activate()`, `check_pack()`, `_file_digest()` and `file_sha256()` have
identical ASTs to HEAD before this fold-in (`r1-footprint.log`). A cheap check
with a predicate that would fail if called never consults it; default full
results and explicit-None results match.

### Current validation

All runner outputs are worktree files under `work/wp6.3a/`. Pytest commands
used `PYTHONPATH=scripts`, `-p sandbox_mkdir_shim -p no:cacheprovider`, bounded
timeouts and disposable worktree basetemps. GUI tests additionally used
`QT_QPA_PLATFORM=offscreen`. The specified GUI command was augmented with the
required sandbox shim. No test activated the GPU pack, reached a real package
index, ran a frozen executable or touched the owner's profile. Loopback and
the real Windows held-open-file/junction tests worked; no sandbox residual or
new skip occurred in these runs.

| Command | Result and evidence |
| --- | --- |
| `uv run --no-sync ruff check .` | All checks passed; `r1-ruff-final.log` |
| `uv run --no-sync ruff format --check .` | 327 files already formatted; `r1-format-final.log` |
| `uv run --no-sync mypy` | No issues in 163 source files; `r1-mypy-final.log` |
| `uv run --no-sync mypy --platform darwin src/clearwater/gpu_pack.py src/clearwater/gpu_pack_install.py src/clearwater/gui/gpu_pack_dialog.py src/clearwater/gui/shell.py src/clearwater/__main__.py` | No issues in 5 source files; `r1-darwin-final.log` |
| Full `uv run --no-sync mypy --platform darwin` | Exactly the four pre-existing errors listed above at `pipes.py:56`, `bench.py:1159`, `bench.py:1480`, `transport.py:950`; `r1-darwin-full.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack.py tests/test_gpu_pack_install.py tests/test_tools_package_build.py tests/test_frozen_entry.py --basetemp=work/c63a-4` | 406 passed in 20.43 s before two extra partial-link checks; `r1-tests.log` |
| Same four-module selection, `--basetemp=work/c63a-5final --durations=0 --junitxml=work/wp6.3a/r1-tests-final.xml` | **408 passed in 20.12 s**; `r1-tests-final.log` / XML |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 600 tests/test_gui_gpu_pack_dialog.py --basetemp=work/c63a-4gui` | **14 passed in 0.75 s**; `r1-gui.log` |
| Five-module collection, parallel expression | 408 selected / 422 total, including all 68 installer cases; `r1-collect-parallel.log` |
| Five-module collection, serial expression | 14 selected / 422 total, exactly the dialog cases; `r1-collect-serial.log` |

Collection uses the fill's expressions `not gpu and not footage and not gui
and not slow and not fullclip` and `(gpu or footage or gui or slow) and not
fullclip`. The sets are disjoint and their union is the 422 target cases.
This is the package selection, not the orchestrator's full release gate.
`r1-audit-final.log` verifies disjoint collection sets, exactly the eleven
owned changed files, zero CR bytes and a passing `git diff --check`.

The current synthetic/metadata regression timings, including setup and
teardown, come from the final JUnit file (`r1-matrix.log`). These are test
durations rather than product throughput figures:

| Added installer cases | Count | Max seconds |
| --- | ---: | ---: |
| Nested package data / real installed RECORD names | 12 | 1.646 |
| Oversized body / no excessive write / no retry | 1 | 0.057 |
| Partial file, symlink and junction | 3 | 0.142 |
| Rename-first, simulated in-use, real Windows open handle, pending retry | 4 | 0.015 |
| Install applies marker: blocked and deletable | 2 | 0.156 |
| Live lock refuses all three operations / stale lock broken | 4 | 0.010 |
| Full-check cancel / unpack reporting | 2 | 0.157 |
| Headless replacement / headless lock refusal | 3 | 0.169 |

All 68 installer cases and all eleven real-distribution metadata cases passed;
the latter read installed metadata only. Every installer case was below the
10-second per-case envelope (maximum 1.646 s).

### Mutant dispositions

- **m2a: EQUIVALENT.** Removing the final byte-count comparison is covered by
  SHA-256 equality; a different-length body cannot match the pinned digest
  within this integrity model.
- **m2b: CAUGHT.** `test_oversized_body_never_writes_past_locked_size_or_retries`
  failed at its maximum-write assertion when only the in-loop size limit was
  disabled in memory. The probe retained the actual urllib fake index and
  network guard (`r1-m2b.log`, 1 expected failure). The normal test passes.
- **m4a: MASKED / unobservable alone for traversal.** Removing the explicit
  `..` component rule leaves the trailing-dot rule and resolved containment
  rule rejecting the same traversal members; the supplied attack has no
  distinct externally observable success for this single mutation.
- **m4b: MASKED / unobservable alone for traversal.** Removing resolved
  containment still leaves the explicit `..` and trailing-dot rules, plus
  absolute/drive/root refusal. An escaping symlink would need a separate
  local-attacker premise (banked finding 10). The combined m4c remains caught
  by the existing hostile-member test, as Reviewer A recorded.

### Verification loop and cumulative round ledger

| Suspected issue | Independent confirmation / rejection | Disposition |
| --- | --- | --- |
| Nested package data is rejected | New synthetic install and actual CuPy RECORD names failed before the change (`r1-red.log`) | Confirmed, fixed, all eleven real RECORD validators pass |
| Removal can partially delete a loaded pack | Before-change rename-first and held-open-file regressions fail; after-change real Windows handle preserves both payloads | Confirmed, fixed by rename and pending marker |
| Lock, pending startup and cancel contracts are missing | Initial group: 19 expected failures / 11 passes; entry/dialog group: 8 expected failures / 1 pass (`r1-redentry.log`) | Confirmed, implemented and green |
| Size test might miss m2b | In-memory mutation writes 2,955 bytes against 128 and fails the named assertion | Rejected as a remaining coverage gap |
| Full-check cancellation test might cancel too early | First combined run: 351 passed / 1 failed; traced four hashes to manifest RECORD construction | Test corrected to cancel on the first payload hash; final install has exactly one such hash, no manifest, no pack or staging |
| Deferred status could fail when a source is open | New source-open case failed with `Device: CPU: stub` (`r1-status-red.log`: 1 failed / 1 passed) | Confirmed, fixed in the one removal-completion update; 14 dialog cases pass |
| Partial sweep might follow a junction or symlink | Actual linked-directory tests keep the outside sentinel unchanged through install and remove | Rejected as a remaining defect |
| Checker default path or DR-125 was inadvertently changed | AST identity of the four unchanged loader/hash functions, all 167 entry tests, diff inspection limited to granted sites | Rejected; worker-side isolation untouched |
| Final in-envelope pass | 408 non-GUI tests, 14 offscreen tests, static checks, collection and owned-path/CR audit | No further in-envelope finding |

The cumulative row is kept in this owned report; the dispatch's owned-file
list does not grant a separate `docs/proofs/wp6.3a-ledger.md` edit. The
dispatcher can transfer this row to its proof ledger without widening this
cell's footprint. Depth is supplied by the dispatcher's driver, not estimated.

| Round | New C / M / minor / advisory | In / out | NEW / REOPENED | Reverts | Product-code / test-only / documentation fixes | Banked | Depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A r1, adjudicated and folded in | 1 / 1 / 4 / 5 | 10 / 1 | 11 / 0 | 0 | 6 / 1 / 1 finding groups | 7, 10, 11 per CHARC | DISPATCHER TO FILL |

This turn bundles the ruled r1 remediation groups in one logical review
fold-in, as commissioned. No further scope ruling is requested. Reviewer A r2
and the real-download seat proof are the next orchestrator actions. No
unowned file, interface, dependency, release workflow or worker isolation code
was changed; no git write, real download, build or desktop input occurred.
