# WP6.3a - GPU pack downloader

Candidate report, 2026-11-04. Parts 1 and 2 added the installer and request
surfaces. Dispatch 5 folds Reviewer A r1 into the merged candidate at
`f00172a6`, following CHARC's rulings including the checker-cancellation grant.
Dispatch 6 folds Reviewer A r2 into `196d2380`, revising removal for mapped
images under CHARC's three-layer ruling. Reviewer A converged at r3 on
`ffb8896e` (NO_NEW_CRITICAL_MAJOR). Dispatch 7 folds all five remaining r3
findings into merged HEAD `852fcee8`; the short delta review, real-download
seat proof, Reviewer B and release gate were next at that handoff. The delta
review of `9c2bdded` also returned NO_NEW_CRITICAL_MAJOR, with two new MINOR
findings. Dispatch 8 folds both into merged HEAD `c606a895`; the seat proof,
Reviewer B (including this delta) and release gate remain with the orchestrator.
The seat subsequently recorded run 1 at `273636db`. Reviewer B r1 on that
head found one MAJOR, one MINOR and seven ADVISORY findings. Dispatch 9 folds
the ruled changes into merged HEAD `b78ed9ce`; the short delta review,
fsync-enabled seat re-run and gate remain with the orchestrator.

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

1. Flush and fsync each extracted file before closing it, then build an
   in-memory manifest from the installed metadata.
2. Run the loader's full checker with that in-memory document (S1).
3. Write, flush and fsync the manifest inside staging.
4. Run the cheap check against the manifest on disk.
5. Rename staging to the final stamp folder with `os.replace`; off win32,
   fsync that renamed staging directory and then its root directory. Windows
   has no directory fsync; the rename uses NTFS journaling.

Failure or cancellation removes staging; a cleanup failure is logged and
disclosed in the result. The product result carries success/failure text,
installed path and cancellation state. Removal only accepts the current stamp
under the calculated root. A GUI removal of this process's activated pack only
writes the marker. Other removals first write-open every DLL and `.pyd` on
Windows to detect mapped images without writing any bytes, then rename the
pack to a partial folder before deleting any file. A blocked probe or rename
leaves the pack intact and writes the empty `<stamp>.remove` marker. A delete
PermissionError after rename also returns pending, keeping the remainder for
a future partial sweep. Other filesystem failures are reported. Matching plain partial folders are cleaned
under the operation lock on GUI startup when a marker or matching partial
entry exists, and on install/remove; files,
symlinks and reparse points with partial names are skipped and logged without
being followed. The image probe uses a recursive `os.scandir` walk that skips
symlinks and all Windows reparse points, for both files and directories.
Before probing an owned read-only image it clears FILE_ATTRIBUTE_READONLY;
failure to clear means in use and defers removal with the pack intact.

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

> GPU support downloads CuPy and NVIDIA's CUDA runtime libraries from PyPI into your user folder. The NVIDIA libraries are provided by NVIDIA under the NVIDIA Software License Agreement (the file `License.txt` in each NVIDIA package's `.dist-info` folder after the install); CuPy is MIT. Clearwater does not redistribute them.

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
and try again". Under the r2 revision, Remove with an existing marker retries
the same probe: pending remains success while in use, and removal completes
after the holder exits. This enables the second headless removal in the new
seat leg.

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

Run by orchestrator generation 46 on 2026-11-04, 23:19:03Z-23:25:46Z, on the package head
`a76a7723` (turn 8; `git status` clean). The kit was `clearwater-review-evidence\wp6.3a\seat\`:
`seat63a.sh` with its helpers, all seven md5-checked against `md5-copies.txt` just before the run.
The record is `seat.summary.txt` in that folder, with one log per leg beside it. Free space on C:
was 78 GB before and 77 GB after.

All app data was redirected to `.worktrees\wp6.3a\work\wp6.3a\appdata` (LOCALAPPDATA, APPDATA,
the XDG roots). No GUI was launched and no desktop input was sent.

| Leg | Result |
| --- | --- |
| Profile before | real `%LOCALAPPDATA%\Clearwater` ABSENT; the owner log's md5 `69ed0432...` (unchanged since the WP6.1 incident) |
| 1. onedir build (`build.py --form onedir --with-ffmpeg`) | exit 0, 96 s; both PASS lines (no ZIP, no CUDA library, every module's top-level name allowed) |
| 2. Real install (`--install-gpu-pack`, frozen, through `proof4.py`) | exit 0, 248.1 s wall, no window; last line "GPU support is installed. Restart Clearwater to use it."; the eleven locked wheels, 1.725 GB, fetched from `files.pythonhosted.org` |
| 3. `build.py --verify` on the installed pack | PASS: 11 distributions; 2,679 RECORD rows, each file's sha256 and size; 2,679 files, 2,412.6 MiB |
| 4. Census | 2,679 new files, 2,412.3 MiB of RECORD; `SET_EQUAL_RECORD` true; `SET_EQUAL_HANDFILLED_MINUS_UV` true (WP6.1's hand-filled pack minus uv's 22 INSTALLER / REQUESTED files); `EXPECTED_2679` true |
| 5. Two frozen workers on the installed pack | heic: exit 0, 21.3 s, `ok` true, device GPU, 67 CUDA files mapped; video: exit 0, 12.6 s, `ok` true, device GPU, 67 CUDA files mapped; no window in either |
| 6. Remove while loaded (CHARC's A r2 leg) | A bounded SOURCE child (`python -I`, redirected roots, Qt blocked, 900 s bound) activated the pack: outcome `loaded`, CuPy imported from the pack, a GPU sum of 45, 56 pack images mapped. A frozen headless `--remove-gpu-pack` from a second process then gave exit 0 in 0.42 s with "GPU support will be removed at the next start". After it: the marker `14.2.0-cu12.remove` PRESENT, the pack PRESENT at its original path (not renamed), 0 partials |
| 6a. `--verify` after the loaded remove | exit 1, with 143 problems, ALL `__pycache__/*.pyc` files written into the pack by the seat's SOURCE child (see the note below). No listed file had a hash or size problem, and none was missing; every RECORD file was intact |
| 6b. Child exit; final remove | child exit 0. A second frozen `--remove-gpu-pack`: exit 0 in 1.22 s, "GPU support is removed; takes effect at the next start"; marker ABSENT, pack ABSENT, 0 partials, the pack root empty |
| Profile after | the owner log's md5 unchanged; real `%LOCALAPPDATA%\Clearwater` ABSENT; no Clearwater process running |

**Note on 6a (a seat-kit gap, not a product defect).** The seat's source child ran
`python.exe -I` without `-B`. CPython therefore wrote bytecode caches for every pack module it
imported, and the full check rejects those as unlisted files, as it should. The product does not
do this:
- the source product never loads the pack (`activate()` returns early when not frozen);
- the frozen interpreter does not write bytecode;
- WP6.1's hand-filled pack, used by the WP6.1 and WP-DR125 frozen GPU runs, holds 0 `.pyc`
  files today.

The leg's own claims hold:
- the frozen headless remove deferred (pending, marker written, no rename, no partial);
- every RECORD file stayed intact;
- the marker was cleared and the pack removed only after the mapping process exited.

A later seat kit that maps a pack from a source child adds `-B` (or sets
`PYTHONDONTWRITEBYTECODE`).

### Re-run after the B r1 fold

SEAT TO FILL

The seat measures the fsync-enabled install wall time and its delta against
run 1's **248.1 s** (about 248 s). Expected Windows file-fsync count:
**2,680** (2,679 installed files plus the manifest). New wall time:
**SEAT TO FILL**; delta: **SEAT TO FILL**. Rebuild from the new candidate,
retain run 1's appdata/evidence as directed, and re-run the seat proof with
the source mapping child using `-B`. These are orchestrator actions; the
cell has not measured real-pack fsync performance or written a seat script.

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
A converged at r3 and its cleanup delta review found no new critical or major
issue. Both delta MINOR findings are folded in below; Reviewer B and the final
gate are pending.

## Reviewer A r1 fold-in (dispatch 5)

All eleven findings were adjudicated against CHARC's complete ruling packet.
At the r1 handoff, Reviewer A r2 was still pending (historical).

| Finding | Classification and change | Discriminating coverage |
| --- | --- | --- |
| 1 | CRITICAL, confirmed, fixed: `.data` refusal applies only to the first path component | `test_nested_package_data_installs`, the existing top-level hostile-member case, and eleven `test_real_locked_record_member_names_are_allowed` cases reading actual installed RECORDs without importing their packages |
| 2 | MAJOR, initial r1 remediation; REOPENED by r2 F1: rename-first protects an ordinary open handle, but its premise was false for mapped images. The r2 three-layer correction below supersedes the initial loaded-pack claim | Initial open-handle/rename tests remain as non-mapped controls; r2 adds actual child-mapped DLL and `.pyd` cases |
| 3 | MINOR, confirmed, corrected: expected downloader census 2,679, excluding uv's 22 added files | Corrected census and file-set acceptance criterion above; real census 2,679, SET_EQUAL both true (the seat run) |
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

### R1 validation (historical)

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
| Removal can partially delete a loaded pack | R1 checked only a non-mapped open handle; r2 independently mapped DLL/`.pyd` images and disproved the rename premise | REOPENED by r2 F1; corrected by the three layers below |
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

| Round | C / M / minor / advisory | In / out | NEW / REOPENED | Reverts | Product-code / test-only / documentation fixes | Banked | Depth |
| --- | --- | --- | --- | --- | --- | --- | --- |
| A r1, initial fold-in; #2 reopened at r2 | 1 / 1 / 4 / 5 | 10 / 1 | 11 / 0 | 0 | 6 initial / 1 / 1 finding groups; #2 corrected below | 7, 10, 11 per CHARC | Turn-5 end: 160,597 / 475,000, supplied at dispatch 6 |
| A r2, adjudicated and folded in | 0 / 1 / 2 / 2 | 5 / 0 | 4 / 1 (#2) | 0 | 3 / 2 / 0 finding groups | No new banked finding | Turn-6 end: 229,611, supplied at dispatch 7 |
| A r3, CONVERGED; all five cleanup findings folded in | 0 / 0 / 2 / 3 | 4 / 1 (R3-5, expressly granted) | 5 / 0 | 0 | 4 / 1 / 0 finding groups; R3-3 integration corrected by delta F1 | None of r3's five left open after delta F1 | Turn-7 end: 109,576 / 475,000, supplied at dispatch 8 |
| A delta, NO_NEW_CRITICAL_MAJOR; two MINORs folded in | 0 / 0 / 2 / 1 | 3 / 0 | 3 / 0 | 0 | 2 / 0 / 0 finding groups; A1 equivalent, no change | None | Turn-8 end 137,204 / 475,000 |
| B r1, NEW_CRITICAL_MAJOR_FOUND; ruled folds complete | 0 / 1 / 1 / 7 | 7 / 2 (F5/F9 granted folds; rest banked) | 9 reported / 0 reopened; F8 follows prior rulings | 0 | 4 / 3 / 1 finding groups; F8 banked | F8 and remaining F9 notes to CHARC | DISPATCHER TO FILL |
| B-fold delta, NO_NEW_CRITICAL_MAJOR; four advisory folds | 0 / 0 / 0 / 6 | 6 / 0 | 6 reported / 0 reopened | 0 | 2 / 1 / 1 finding groups | A2/A4 to seat and CHARC; no code | Prior turn end: 198,141 / 475,000; current DISPATCHER TO FILL |

The r1 turn bundled its ruled remediation groups in one logical review
fold-in. At that handoff Reviewer A r2 and the real-download seat proof were
the next orchestrator actions. No
unowned file, interface, dependency, release workflow or worker isolation code
was changed; no git write, real download, build or desktop input occurred.

## Reviewer A r2 fold-in (dispatch 6)

The r1 removal claim was wrong for mapped images. An ordinary `open()` handle
can block renaming its parent folder, but a mapped DLL or `.pyd` does not.
Reviewer A and CHARC independently demonstrated that rename succeeds while
write-open and deletion fail. The previous held-open test therefore covered
only the non-mapped case. It remains, explicitly named
`test_real_nonmapped_open_file_defers_remove_and_pending_install`.

The revised implementation uses all three ruled layers:

1. `gpu_pack.activation_status()` returns the frozen loader's last immutable
   status from module state, with no filesystem access. For `loaded`, the GUI
   submits `_defer_remove_job`, which writes the pending marker under the
   operation lock without a probe, rename or deletion. Absent, rejected and
   never-activated states retain the normal removal job. Headless removal
   does not activate the loader or use this GUI shortcut.
2. `_pack_in_use()` runs under the operation lock before any pack rename. On
   win32 it opens each DLL and `.pyd` with `os.O_RDWR` and immediately closes
   the descriptor, writing no bytes. PermissionError means pending removal
   with the original folder untouched. Off win32 it performs no probe. The
   same `_rename_remove` path serves remove, pending-removal application,
   install-with-marker and rejected-pack replacement.
3. If a PermissionError occurs after the rename, the remainder stays under
   `.partial-*`, the marker is written and removal returns pending success.
   Pending application/installation retain their refusal outcome while a
   removal request is still pending. When the stamp folder is absent,
   pending application clears the marker after sweeping partials. A
   PermissionError on an individual partial logs one line and leaves it for
   a future sweep; it does not prevent startup or show an error dialog.

A repeated explicit remove now retries the probe even when a marker exists.
It remains pending while the holder is alive and removes the pack/marker
after the holder exits. This revises r1's marker-only early return to meet
the new seat leg's second headless-remove requirement. A race remainder still
mapped at the first sweep can remain after the absent-stamp marker is cleared;
subsequent install/remove partial sweeps retry it, as the ruled fail-safe
allows. No unowned startup cleanup path was added.

| Finding | Classification / change | Coverage |
| --- | --- | --- |
| F1 | MAJOR, REOPENED r1 #2, confirmed and corrected by all three layers | `test_activation_status_exposes_last_outcome_without_io` (loaded/absent/rejected); offscreen `test_this_process_loaded_remove_only_writes_marker` and three negative status controls; `test_write_open_probe_defers_before_any_rename` for remove, pending, install-marker and rejected replacement; actual child-mapped DLL and `.pyd`; four `test_delete_race_defers_and_locked_partial_does_not_block_start` cases |
| F2 | MINOR, confirmed pre-existing fixture defect; resolve `QApplication` and its native `instance()` call before the fresh-entry blocker removes PySide6 modules | Installer module alone: 83 passed, exit 0; no application/window constructed; entry's Qt-import blocker and disposable profile remain active |
| F3 | MINOR, confirmed and fixed in shell only; startup marker sets the pending CPU reason, which takes precedence over a later asynchronous device-probe callback | `test_startup_marker_shows_pending_reason_without_install_hint`; existing status/hint and open-source removal cases remain green |
| F4 | ADVISORY, confirmed and fixed; real RECORD validation skips with an explicit installed/locked-version reason on mismatch | `test_real_record_validator_skips_mismatched_environment` forbids reading the stale RECORD; all eleven actual locked-version RECORD validators pass here |
| F5 | ADVISORY, confirmed and fixed; rejected pack deletion uses the same write-open probe, marker and delete-race fail-safe | The `replace` cases in both four-way probe/race tests; rejected-pack happy path remains green |

The child-mapping tests copy the host interpreter's `python3.dll` and `_queue`
extension into separate synthetic packs, then use `ctypes.WinDLL` or Python's
extension loader in a child. They do not import CuPy or activate a GPU pack.
Each child has redirected APPDATA/LOCALAPPDATA/XDG roots, Qt imports blocked,
no inherited stdin, an eight-second lifetime limit and bounded parent waits.
While mapped, remove returns pending; the original folder and all file bytes
remain intact; no partial folder appears. Applying pending removal and
installing with the marker also preserve every byte. After the child exits
with status 0, applying pending removal deletes the pack and marker. The final
four-module run records **DLL 0.121 s / `.pyd` 0.155 s**, including fixtures
(`r2-tests-final.xml`, `r2-child-summary-final.log`); both passed in this sandbox.

The probe's separate test observes both image extensions (including uppercase
`.PYD`), checks every descriptor is closed, and verifies payloads and mtimes
are unchanged. The off-win32 control forbids `os.open` entirely. The delete-race
tests force a post-rename PermissionError, then a locked-partial sweep: pending
success, marker lifecycle, one log line and eventual sweep cleanup all hold.
The real-pack mapped-CuPy proof is in the seat section (leg 6).

### R2 validation and verification record

Runner files are under `work/wp6.3a/`. All pytest runs used
`PYTHONPATH=scripts`, `-p sandbox_mkdir_shim -p no:cacheprovider`, bounded
timeouts and worktree basetemps. GUI runs used `QT_QPA_PLATFORM=offscreen`;
the required sandbox shim was added to the GUI command. F3's shell test is
in the owned dialog module, so that module covers both requested GUI surfaces.

| Command | Result / log |
| --- | --- |
| `uv run --no-sync ruff check .` | All checks passed, exit 0; `r2-ruff.log` |
| `uv run --no-sync ruff format --check .` | 327 files already formatted, exit 0; `r2-format-check.log` |
| `uv run --no-sync mypy` | Clean, 163 source files, exit 0; `r2-mypy.log` |
| Full `uv run --no-sync mypy --platform darwin` | Exactly the four accepted baseline errors, exit 1; `r2-darwin.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack.py tests/test_gpu_pack_install.py tests/test_tools_package_build.py tests/test_frozen_entry.py --basetemp=work/c63a-6 --junitxml=work/wp6.3a/r2-tests.xml --durations=0` | 425 passed in 25.01 s before the final metadata-permission regression, exit 0; `r2-tests.log` |
| Same four-module command with `--basetemp=work/c63a-6final --junitxml=work/wp6.3a/r2-tests-final.xml --durations=0` | **426 passed in 21.96 s**, exit 0; `r2-tests-final.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack_install.py --basetemp=work/c63a-6mfinal` | **83 passed in 10.38 s**, exit 0; `r2-module-alone-final.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 600 tests/test_gui_gpu_pack_dialog.py --basetemp=work/c63a-6gui-verified` | **19 passed in 1.14 s**, exit 0; `r2-gui-final.log` |
| Five-module collection with the fill's parallel / serial expressions | **426 parallel + 19 serial = 445**; installer parallel, dialog serial; `r2-collect-parallel.log`, `r2-collect-serial.log` |

The full Darwin errors are exactly `src/clearwater/io/video/pipes.py:56`,
`tools/prototype/bench.py:1159`, `tools/prototype/bench.py:1480` and
`tools/spike_io/transport.py:950`. There is no new Darwin error or new skip.
No sandbox residual was encountered in the required tests or child-image
tests. The initial module-alone check passed 79 cases before the delete-race
matrix was expanded; the final 83-case run includes that expansion and the
partial-metadata PermissionError regression.
`r2-audit-final.log` confirms exactly eight changed owned files, zero CR
bytes, a passing `git diff --check`, and a disjoint 426/19 collection split.
The existing cheap/full checker and hash functions have identical ASTs to
the pre-fold-in HEAD; only the granted activation-state exposure changes the
loader outside those checks. `__main__`, worker isolation, core/backend and
app wiring have no diff this turn.

| Suspected issue | Evidence | Disposition |
| --- | --- | --- |
| Mapped images evade the r1 rename assumption | Pre-change regressions failed for actual DLL and `.pyd` children; r2 reviewer and CHARC reproduced independently | Confirmed; write-open, own-process marker and race fail-safe added |
| A replacement or pending install might delete another instance's loaded pack | Probe-denied tests prohibit any rename, record zero fake-index requests and preserve both payloads in all four entry paths | Fixed; shared removal path, no download on in-use refusal |
| A post-probe mapping race might surface as a raw removal failure or block startup | Four forced-delete-failure tests retain the partial, return pending and tolerate its locked sweep with one log line | Fixed under the ruled residual behavior |
| The GUI might always defer even without a loaded status | Three negative controls execute the captured worker job and receive normal-removal text without a marker | Rejected as a remaining defect |
| Startup's asynchronous CPU probe might hide the pending reason | New offscreen marker test exercises construction and a later `set_idle_device` call | Confirmed, fixed entirely in shell; no backend/app-wiring edit |
| The module-alone run might still crash pytest-qt | Final module-alone exit 0, 83 passes, with entry Qt blockers intact | Fixed fixture; no window or application created |
| A stale venv might validate a different RECORD | Mismatched-version control raises the explicit skip before its forbidden RECORD read | Fixed; actual eleven distributions pass |
| New GUI rename guard might catch unrelated preset/settings saves | Initial guard caught test setup/teardown, rather than pack removal | Test guard narrowed to the pack folder; 19 GUI tests pass |
| Metadata PermissionError on a partial might keep an absent pack's marker set | The late regression failed before the final fix (`r2-partial-red.log`); the per-partial handler covered deletion but not lstat | Confirmed and fixed; `test_unreadable_partial_does_not_keep_absent_pack_marker` clears the marker, leaves the inaccessible partial and logs one line |
| Final in-envelope pass | Required tests/static checks, actual child mappings, scope/default-check audit and collection partition | No further in-envelope finding |

Reviewer A r2 reported **21/21 mutants caught**, but reopened r1 #2 based on
the missing mapped-image case. That review is not convergence. The cumulative
ledger above now records r2 as **4 NEW / 1 REOPENED**, no reverts, three
product-code finding groups and two test-only groups. R1 advisories 7, 10 and
11 remain banked by CHARC. Reviewer A r3, the expanded seat run, Reviewer B and
the gate remain with the orchestrator. This turn bundles F1-F5 as commissioned;
no new dependency, real download, frozen/build run, desktop input, git write,
footage/profile write or edit to DR-125/core backend/app wiring occurred.

## Reviewer A r3 fold-in (dispatch 7)

Reviewer A r3 (`A/r3/review.txt` at the dispatcher evidence root) reported
NO_NEW_CRITICAL_MAJOR and 15/16 mutants caught. Its two MINOR and three
ADVISORY findings are confirmed; CHARC granted all five for this cleanup.
R3-5 was classified outside the original envelope by the reviewer and is
implemented under the explicit dispatch-7 grant. No item is stopped or left
half-done. This turn bundles the five commissioned cleanup findings.

| Finding | Change | Discriminating test / evidence |
| --- | --- | --- |
| R3-1 MINOR | Before a Windows image write-open, clear FILE_ATTRIBUTE_READONLY using `os.chmod`; any OSError clearing it returns in-use/pending before a rename | `test_read_only_unmapped_image_removes_cleanly`; `test_read_only_image_attribute_failure_defers_intact` for PermissionError and OSError. Actual read-only image removal failed before the fix; generic attribute OSError initially returned failure, then passed after widening the clear-failure handling |
| R3-2 MINOR, test-only | Child-mapped DLL is under `site-packages/nvidia/x/bin/`; child-loaded `.pyd` and the observed uppercase extension are under `site-packages/pkg/`. Byte/mtime snapshots cover nested files | `test_child_mapped_image_keeps_pack_intact_until_exit[dll/pyd]` and `test_probe_opens_both_image_extensions_without_writing`; all three fail the top-level-only mutant and pass the restored implementation |
| R3-3 ADVISORY | `apply_pending_removal()` sweeps partials whenever called, under the operation lock, even without a marker. Busy lock refuses immediately; per-partial PermissionError stays logged/tolerated. The missing GUI-entry call is corrected by delta F1 below | `test_startup_sweeps_leftover_partial_without_marker` and `test_startup_busy_lock_skips_partial_sweep` test the helper, not entry-point integration; delta F1 adds the real GUI-branch test |
| R3-4 ADVISORY | Menu-action refresh clears `_gpu_removal_pending` when the marker is gone, including successful install and removal completions. The label then says `CPU: GPU support changes take effect at the next start`; later ordinary device reasons work again | Offscreen `test_pending_reason_clears_after_marker_is_gone[install/remove]`; both failed before the fix. Existing startup-marker precedence test remains green |
| R3-5 ADVISORY, originally out of envelope, granted | Replace `rglob` with an iterative `os.scandir` walk; inspect entries without following links, skip symlinks/all reparse points, and recurse only into plain directories | `test_probe_never_enters_linked_images[junction/directory-symlink/file-symlink]`; actual junction and file-symlink cases failed against the old walk. All three pass here, with a guard that rejects any outside image write-open and an unchanged outside payload |

Turn 7 left the startup call in `__main__` unchanged, incorrectly assuming
that the wrapper was called on every GUI start. The delta review confirmed
that the call was marker-only, so the direct-helper tests did not prove the
product path and turn 7's every-start report claim was incorrect. Under the
dispatch-8 grant, the GUI branch now checks for a marker OR an existing root
directory with a `<STAMP>.partial-*` entry, using one glob of the root only.
It then calls the lock-held sweep; no marker is needed for a leftover partial
to be retried at a later start. A missing root causes no installer call and
no root/lock creation. Install/remove retain their own lock-held sweeps.
Child entry branches remain read-only. The shell does not activate GPU
support after any operation; a restart still applies the change.

### R3 validation

All runner output is under `work/wp6.3a/`. Every pytest command set
`PYTHONPATH=scripts` and `QT_QPA_PLATFORM=offscreen`, loaded
`-p sandbox_mkdir_shim -p no:cacheprovider`, used the stated bounded timeout
and wrote only to its disposable worktree basetemp. The required sandbox shim
was added to the dispatch's GUI command. The shell tests are in the same
dialog module; there is no second shell module to run.

| Command | Result / evidence |
| --- | --- |
| `uv run --no-sync ruff check .` | All checks passed, exit 0; `r3-ruff.log` |
| `uv run --no-sync ruff format --check .` | 327 files already formatted, exit 0; `r3-format-check.log` |
| `uv run --no-sync mypy` | No issues in 163 source files, exit 0; `r3-mypy.log` |
| `uv run --no-sync mypy --platform darwin` | Exactly 4 accepted errors in 3 files / 163 checked, exit 1; `r3-darwin.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack.py tests/test_gpu_pack_install.py tests/test_tools_package_build.py tests/test_frozen_entry.py --basetemp=work/c63a-7 --junitxml=work/wp6.3a/r3-tests.xml --durations=0` | **434 passed in 30.25 s**, exit 0; `r3-tests.log` / XML |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack_install.py --basetemp=work/c63a-7m` | **91 passed in 8.82 s**, exit 0; `r3-module-alone.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 600 tests/test_gui_gpu_pack_dialog.py --basetemp=work/c63a-7gui --junitxml=work/wp6.3a/r3-gui.xml` | **21 passed in 1.08 s**, exit 0; `r3-gui.log` / XML |
| `uv run --no-sync python work/wp6.3a/r3-mutant.py` | Expected exit 1, **3 failed in 0.45 s**; `r3-mutant.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack_install.py::test_probe_opens_both_image_extensions_without_writing tests/test_gpu_pack_install.py::test_child_mapped_image_keeps_pack_intact_until_exit --basetemp=work/c63a-7restored` | Restored code: **3 passed in 0.36 s**, exit 0; `r3-restored.log` |
| `uv run --no-sync python work/wp6.3a/r3-audit.py` (includes `git diff --name-only` and `git diff --check`) | Exactly 5 owned changed files, 0 CR bytes, clean diff check; XML confirms 434 non-GUI / 21 GUI cases and 0 failures/errors/skips, exit 0; `r3-audit.log` |

Darwin's errors are exactly `src/clearwater/io/video/pipes.py:56`,
`tools/prototype/bench.py:1159`, `tools/prototype/bench.py:1480` and
`tools/spike_io/transport.py:950`; there is no new error. No required run has a
skip, and no sandbox refusal/residual occurred: actual junctions, symlinks,
loopback and child-mapped images worked. Timings are test-run durations,
not real-pack performance measurements. In the final four-module XML, all
91 installer cases were below 10 seconds (maximum 2.198 s); the child DLL
and `.pyd` cases took 0.177 s and 0.158 s, including fixtures.

The mutation is the same top-level-only behavior as r3's surviving
`rglob`-to-`glob` mutant. With the new scanner, the in-memory mutation disables
its directory-enqueue statement. The script patches only that function in
its own process; no product file is edited. Both child-mapped tests fail at
the intact-pack assertion, and the extension test fails because the nested
`.PYD` was not probed. A fresh normal process passes all three. The scripts
and synthetic DLL copies stay ignored under `work/`; no seat or download
script was written.

### R3 verification loop and handoff

| Suspected issue | Independent confirmation / rejection | Disposition |
| --- | --- | --- |
| Read-only image can be pending forever | Actual attribute test failed against the pre-change implementation (`r3-red.log`) | Confirmed and fixed; clean removal plus two attribute-failure pending controls pass |
| Attribute-clear failure may escape as a raw failure | Explicit generic OSError control failed (`r3-attribute-red.log`: 1 failed / 1 passed) | Confirmed and fixed; clear-failure OSError is in-use, not a failed removal |
| Probe recursion remains unprotected | Equivalent in-memory M12 mutant fails three named tests | Rejected as a remaining gap; restored code passes three |
| A markerless race remainder never gets another startup sweep | New markerless and busy-lock helper cases both failed against old code, but did not cover the GUI entry call | Helper fixed at r3; real-start integration confirmed missing and corrected by delta F1 |
| Pending status remains after the marker disappears | Both install/remove GUI cases failed (`r3-gui-red.log`) | Confirmed and fixed; ordinary later device reason and tooltip work again |
| Probe can write-open outside the pack via a link | Actual junction and file-symlink regressions failed against `rglob` (`r3-red.log`) | Confirmed and fixed; all three linked-entry controls pass |
| Final in-envelope pass | 434 required non-GUI tests, 91 module-alone tests, 21 offscreen tests, restored mutant controls, static checks and owned-file audit | No further in-envelope finding |

The cumulative r3 ledger row above records 0 critical / 0 major / 2 minor /
3 advisory, 5 NEW / 0 REOPENED, 0 reverts, four product-code finding groups
and one test-only group. Depth was 109,576 / 475,000 at the end of turn 7. Reviewer A remains
converged; this handoff is for its short delta review, then the staged seat
run, Reviewer B and gate. The seat section is now filled (the seat run, 2026-11-04).

Exactly the five dispatch-7 owned files changed, with zero CR bytes and a
passing `git diff --check` (`r3-audit.log`). No new dependency, frozen
interface change, real network fetch, GPU activation, frozen run/build,
desktop input, git write, footage/profile write or edit outside the owned
files occurred. All five rulings are implemented; no deviation or open
question needs a ruling in this turn.

## Delta-review fold-in (dispatch 8)

The delta review of turn 7 (`9c2bdded` against `ffb8896e`) returned
NO_NEW_CRITICAL_MAJOR, with two new MINOR findings and one equivalent-mutant
advisory. It executed R3-1, R3-2, R3-4 and R3-5 successfully, killing 9 of 10
mutants. CHARC's complete delta ruling grants the GUI-entry condition edit
and the constructor-safe reset. Both findings are confirmed and fixed here.

| Finding | Change | Discriminating test |
| --- | --- | --- |
| F1 MINOR, missing real-start integration | One hunk in the GUI branch of `__main__.main` adds the existing-root/partial alternative to the marker condition. It uses `root.is_dir()` and one root glob; the installer is not called when the root is absent. Worker and frozen `-m` branches are unchanged | `test_gui_start_sweeps_markerless_partial_without_creating_absent_root[False/True]` in `tests/test_frozen_entry.py` covers source/frozen. Each first starts with an absent root and proves it stays absent, then plants a markerless partial and proves actual cleanup completes before the stub activation/GUI |
| F2 MINOR, constructor race | Smaller guarded-refresh option: `_update_gpu_actions()` always resets the flag and `_idle_device`, and calls `_update_status()` only when `device_label` exists. During construction the ordinary later status refresh renders that value; subsequent operation/menu refreshes still update the label immediately | Offscreen `test_marker_vanishing_during_construction_resets_without_a_status_bar` returns an existing marker on the first lookup and a missing one thereafter; window construction succeeds with the correct non-pending label and later ordinary device reasons work |
| A1 ADVISORY, equivalent mutant | No change, as ruled: ignoring a failed chmod still leaves READONLY set, so real write-open fails and returns in-use | Delta reviewer classified the surviving mutant as equivalent; no new assertion or product change added |

F1's test uses the existing `calls`, `_fresh_entry` and `_fake_gui` helpers in
`test_frozen_entry.py`. APPDATA, LOCALAPPDATA and all four XDG variables are
redirected under `tmp_path`; PySide6/shiboken6/GUI imports are blocked;
`app.main`, activation, logging and worker entry are stubbed. Both cases have
a ten-second timeout. They execute the real installer cleanup, without a
network request or pack activation. F2 uses the existing offscreen shell
fixture with disposable profiles and stubbed real install/remove operations.

The true GUI-start order is now: marker-or-root-partial check, optional
`apply_pending_removal()` under its operation lock, activation unless a marker
remains, then the GUI. A first start without a pack creates neither its root
nor `.install.lock`. No recursive scan inside the installed pack was added.
This corrects the turn-7 report's every-start claim, which its direct-helper
tests did not establish. The installer implementation itself is unchanged.

### Delta validation and turn-7 discrimination

All logs are under `work/wp6.3a/`. Every pytest run set
`PYTHONPATH=scripts` and `QT_QPA_PLATFORM=offscreen`, loaded
`-p sandbox_mkdir_shim -p no:cacheprovider`, and used the indicated bounded
timeout and disposable worktree basetemp. As in prior turns, the GUI command
includes the binding sandbox shim in addition to the dispatch's command.

| Command | Result / evidence |
| --- | --- |
| `uv run --no-sync ruff check .` | All checks passed, exit 0; `delta-ruff.log` |
| `uv run --no-sync ruff format --check .` | 327 files already formatted, exit 0; `delta-format-check.log` |
| `uv run --no-sync mypy` | No issues in 163 source files, exit 0; `delta-mypy.log` |
| `uv run --no-sync mypy --platform darwin` | Exactly 4 accepted baseline errors in 3 files / 163 checked, exit 1; `delta-darwin.log` |
| `uv run --no-sync python work/wp6.3a/delta-turn7.py entry` | Exact turn-7 entry module loaded in memory; **2 expected failures in 0.71 s**, exit 1, at `partial must be swept before activation`; `delta-turn7-entry.log` |
| `uv run --no-sync python work/wp6.3a/delta-turn7.py gui` | Exact turn-7 `_update_gpu_actions` patched in memory; **1 expected failure in 0.21 s**, exit 1, with `AttributeError: 'MainWindow' object has no attribute 'device_label'`; `delta-turn7-gui.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 600 tests/test_frozen_entry.py::test_gui_start_sweeps_markerless_partial_without_creating_absent_root tests/test_gui_gpu_pack_dialog.py::test_marker_vanishing_during_construction_resets_without_a_status_bar --basetemp=work/c63a-8green` | Fixed normal code: **3 passed in 0.75 s**, exit 0; `delta-green.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack.py tests/test_gpu_pack_install.py tests/test_tools_package_build.py tests/test_frozen_entry.py --basetemp=work/c63a-8 --junitxml=work/wp6.3a/delta-tests.xml` | **436 passed in 23.19 s**, exit 0; `delta-tests.log` / XML |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 600 tests/test_gui_gpu_pack_dialog.py --basetemp=work/c63a-8gui --junitxml=work/wp6.3a/delta-gui.xml` | **22 passed in 0.99 s**, exit 0; `delta-gui.log` / XML |
| `uv run --no-sync python work/wp6.3a/delta-audit.py` (includes `git diff --name-only` and `git diff --check`) | Exactly 5 owned files, 0 CR bytes, clean diff check, one granted `__main__` hunk, unchanged seat section, XML counts 436 / 22 with 0 failures/errors/skips; `delta-audit.log` |

The old-code probes read source at `9c2bdded` using read-only `git show` and
compile it in memory in separate processes; no product file is reverted or
committed. The entry import hook supplies the turn-7 module only to the
isolated tests, and the GUI probe replaces only the old action-refresh
method. Both still use the current test fixtures and their isolation rules.
The initial test-first runs also reproduced the same two entry failures
(`delta-entry-red.log`, 2 failed / 0.80 s) and the constructor AttributeError
(`delta-gui-red.log`, 1 failed / 0.83 s). The final full normal runs above
confirm the fixed code after the old-code probe processes exit.

Darwin's only errors are `src/clearwater/io/video/pipes.py:56`,
`tools/prototype/bench.py:1159`, `tools/prototype/bench.py:1480` and
`tools/spike_io/transport.py:950`. There is no new error, test skip or sandbox
residual. Timings describe test runs only.

| Verification-loop suspicion | Confirmation / rejection | Final disposition |
| --- | --- | --- |
| Markerless partial cleanup is unreachable from real GUI entry | Source and frozen entry tests fail against exact turn-7 code before the activation stub | Confirmed; one condition hunk fixes integration; both pass |
| Making cleanup unconditional would create a root for CPU-only users | Each new entry case first asserts the root remains absent after a no-pack start | Rejected as a remaining defect; condition guards the installer call |
| Marker disappearance can refresh a status bar that does not yet exist | Exact turn-7 action-refresh method raises the reported AttributeError | Confirmed; guarded refresh constructs and renders the correct label |
| Guarded constructor refresh could break later pending resets | Existing install/remove completion tests and the new later-device-reason check pass in the 22-case GUI run | Rejected as a remaining defect |
| Final in-envelope pass | Required static checks, 436 non-GUI tests, 22 offscreen tests and footprint/hunk/CR audit | No further in-envelope finding |

The cumulative delta ledger above records 0 critical / 0 major / 2 minor /
1 advisory, all NEW, no reverts, two product-code finding groups and A1
equivalent/no change. Turn-7 depth was 109,576 / 475,000 as supplied in
dispatch 8; this turn's depth was 137,204 / 475,000 at its end. No item is stopped and
no deviation or open question needs a ruling. The seat-run section is
filled; full Reviewer B (covering these two edits), gate
and accept remain with the orchestrator under the delta ruling.

This turn changes only the five dispatch-8 owned files, with the isolated
entry tests in `tests/test_frozen_entry.py` and no change to
`tests/test_gpu_pack_install.py`. No dependency, frozen interface, worker or
`-m` branch changed. No real fetch, GPU activation, frozen executable/build,
desktop input, git write, footage/profile write or seat/download script was
performed or created.

## Reviewer B r1 fold-in (dispatch 9)

Reviewer B r1 (`B/r1/review.txt` at the dispatcher evidence root) returned
NEW_CRITICAL_MAJOR_FOUND: one MAJOR, one MINOR and seven ADVISORY findings.
All commissioned folds are built under CHARC's complete ruling packet.
F8 and the remaining F9 notes stay with CHARC for the register/accept record.
The loader and its cheap/full acceptance rules are unchanged this turn.

| Finding | Change | Test | Mutant / historical discrimination |
| --- | --- | --- | --- |
| F1 MAJOR | Flush+fsync every extracted file and the staged manifest before close; off win32, sync the renamed staging directory then root after publication, closing both descriptors. A directory-sync failure uses the existing cleanup path against the published candidate | `test_every_extracted_file_and_manifest_are_flushed_before_publication` records all 20 synthetic installed files plus manifest before replace, checking flushed sizes. `test_posix_publication_syncs_renamed_staging_then_root` exercises directory order/closure with descriptor doubles. Two `test_fsync_failure_removes_staging_without_publishing` cases cover payload/manifest ENOSPC | All four cases fail exact turn 8; removing file-fsync calls fails the recording test. No physical power cut performed |
| F2 MINOR + F4 ADVISORY | Wrap `response.read()` alone, converting any OSError to transport URLError; retain three attempts and wheel-named errors. Disk write errors retain their separate path | Read-phase TimeoutError and plain OSError each make three real fake-index requests, name the wheel and clean staging. Write-phase ENOSPC makes one request | Plain read error fails turn 8; timeout already passed there but kills M3 on that original code. A widened write-error retry mutant fails the ENOSPC control |
| F3 ADVISORY | Synthetic wheel RECORD omits nested `lib.dll` while keeping listed `__init__.py`; the package still has top-level ownership | Improved `test_unlisted_nested_file_fails_full_verification` tests the install outcome through the full nested-file walk | M4 (staging full check downgraded to cheap) now fails this behavioral test |
| F5 ADVISORY, originally out of envelope, granted | Guard `_removal_pending` and GUI marker/root/glob probes: OSError means pending, no activation, one log line. Guard shell construction and menu-refresh probes; preserve pending CPU text and suppress repeat logs for persistent failure | Six isolated entry cases cover GUI path/exists/is_dir/glob, worker path and frozen-module path. Two offscreen shell cases cover construction and later menu refresh; each asserts one pending log | All eight fail exact turn-8 code and pass fixed code |
| F6 ADVISORY | Only section 2's GPU paragraph and README's normal-install paragraph change: cmd.exe install/remove recipes use `start /wait "" Clearwater.exe ... > ... 2>&1` and explain waiting | Documentation diff / paragraph footprint audit | No frozen run; documentation correction |
| F7 ADVISORY | Child atomically publishes its interpreter PID using `os.getpid()`; timeout cleanup sends SIGTERM to that PID, never `child.kill()` on the uv launcher. Eight-second child deadline remains | Both existing nested DLL/`.pyd` child tests pass; parent waits remain bounded | Test harness corrected; forced-timeout kill branch inspected, not forced this turn |
| F8 ADVISORY, already ruled | No code; later child loads stay on CPU after a removal request, and the export status/off-win32 lazy-load notes go to CHARC | Existing behavior follows prior removal rulings | Banked for register/accept |
| F9 ADVISORY | Add direct tests of NTFS `:` stream and same-host redirect user-info refusals. Emit the dialog's identical one-line N13 statement from the installer before requests, on stdout when available | `test_ntfs_stream_member_is_refused_by_the_member_validator`, `test_redirect_user_info_is_refused_before_a_request`, isolated `test_headless_n13_notice_precedes_the_first_request`; existing offscreen plan test asserts installer/dialog notice equality | M1 and M15 fail their new tests. Security rules already pass correct turn 8; N13 output assertion fails turn 8 |

N13 uses the verbatim dialog text already reproduced in this report.
`gpu_pack_install.install` emits it, preserving the F5-only `__main__` grant
and keeping Qt out of headless imports. It can also appear for a GUI request
when stdout exists; a windowed process with no stdout remains silent there.
The notice constants are kept equal by the offscreen assertion; the dialog
module is unchanged. No automatic request/download was added.

F9's remaining uppercase top-level `.DATA` note stays with CHARC. Extra
arguments exit **2**, correctly following AD-34's refusal status; requested
success/no-op is 0 and failure/cancel is 1. F8 and those remaining F9 notes
have no new code here. The cheap startup check is unchanged, and repair of a
pack that fails the full check remains remove/reinstall.

### B r1 validation

All logs below are under `work/wp6.3a/`. Pytest commands set
`PYTHONPATH=scripts` and `QT_QPA_PLATFORM=offscreen`, load
`-p sandbox_mkdir_shim -p no:cacheprovider`, and use bounded timeouts and
disposable worktree basetemps. The GUI command includes the binding shim.
The actual fake index and its exact-loopback network guard remain unchanged.

| Command | Result / evidence |
| --- | --- |
| `uv run --no-sync ruff check .` | All checks passed, exit 0; `b1-ruff-final.log` |
| `uv run --no-sync ruff format --check .` | 327 files formatted, exit 0; `b1-format-final.log` |
| `uv run --no-sync mypy` | No issues in 163 source files, exit 0; `b1-mypy.log` |
| `uv run --no-sync mypy --platform darwin` | Exactly 4 accepted errors in 3 files / 163 checked, exit 1; `b1-darwin.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack.py tests/test_gpu_pack_install.py tests/test_tools_package_build.py tests/test_frozen_entry.py --basetemp=work/c63a-9 --junitxml=work/wp6.3a/b1-tests.xml --durations=0` | **452 passed in 24.31 s**, exit 0; `b1-tests.log` / XML |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack_install.py --basetemp=work/c63a-9m` | **101 passed in 8.86 s**, exit 0; `b1-module-alone.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 600 tests/test_gui_gpu_pack_dialog.py --basetemp=work/c63a-9gui --junitxml=work/wp6.3a/b1-gui.xml` | **24 passed in 1.04 s**, exit 0; `b1-gui.log` / XML |
| `uv run --no-sync python work/wp6.3a/b1-probes.py turn8` | Exact turn-8 installer/entry/shell loaded in memory: **15 expected failures / 4 passing controls / 281 deselected in 2.19 s**, exit 1; `b1-turn8.log` |
| `uv run --no-sync python work/wp6.3a/b1-probes.py M1` | One expected NTFS-stream failure, 0.19 s, exit 1; `b1-M1.log` |
| Same command, `M15` | One expected user-info failure, 0.17 s, exit 1; `b1-M15.log` |
| Same command, `M4` | One expected nested-unlisted failure, 0.44 s, exit 1; `b1-M4.log` |
| Same command, `no-fsync` | One expected fsync-coverage failure, 0.36 s, exit 1; `b1-no-fsync.log` |
| Same command, `wide-write-retry` | One expected write-side retry-count failure, 0.23 s, exit 1; `b1-wide-write-retry.log` |
| Same command, `M3-turn8` | One expected timeout failure on turn-8 code with TimeoutError removed, 0.24 s, exit 1; `b1-M3-turn8.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack_install.py tests/test_frozen_entry.py tests/test_gui_gpu_pack_dialog.py -k 'every_extracted or posix_publication or fsync_failure or read_phase or write_phase or ntfs_stream or redirect_user_info or n13_notice or unreadable_removal_probes or unreadable_marker_keeps or menu_opens_explicit or unlisted_nested or child_mapped' --basetemp=work/c63a-9restored` | Fresh normal process after all probes: **22 passed / 278 deselected in 2.12 s**, exit 0; `b1-restored.log` |
| `uv run --no-sync python work/wp6.3a/b1-audit.py` | Exactly 9 owned files, F5-only entry changes, guide paragraph-only edit, loader unchanged, 0 CR bytes, clean diff check, preserved run 1 plus re-run placeholder; `b1-audit.log` |

Darwin errors are exactly `src/clearwater/io/video/pipes.py:56`,
`tools/prototype/bench.py:1159`, `tools/prototype/bench.py:1480` and
`tools/spike_io/transport.py:950`. No new error, skip or sandbox residual
occurred. The POSIX directory-sync test uses descriptor doubles on Windows;
it is not a real POSIX durability proof. The seat measures real-pack cost
against 248.1 s; the delta remains **SEAT TO FILL** (2,680 expected Windows
file fsyncs).
The final XML records all 101 installer cases below ten seconds (maximum
2.048 s). The packaging README repository blobs contained zero CR bytes both
before and after turn 9. The earlier normalization claim described working
checkout line endings, not a change in blob history; its text diff was confined
to the allowed request paragraph.

Historical probes use read-only `git show a76a7723:<path>` and an in-memory
source loader, never a tracked-file revert. Four controls already pass turn
8: read TimeoutError, write ENOSPC, NTFS-stream refusal and redirect-user-info
refusal. Their purpose is to catch broken mutants, so claiming that they
fail correct old code would be false. The improved nested-file test also
passes correct turn 8 and now fails M4. With the new wrapper, read TimeoutError
becomes URLError; removing only the outer TimeoutError arm no longer breaks
read-timeout retries. M3-turn8 therefore exercises the review's original
mutation on its original code.

### B r1 verification loop and handoff

| Suspected issue | Independent confirmation / rejection | Disposition |
| --- | --- | --- |
| No durable writes before publication | Exact turn-8 coverage/failure tests fail; no-fsync mutant fails | Confirmed, fixed; payload/manifest failure cleanup tested |
| Directory-sync order/descriptor leak | Off-win32 branch observes destination then root, with matching closes | Order/closure hold; real POSIX durability unmeasured |
| Read error bypass or write-error retry | Turn-8 plain-read failure; wide-write-retry mutant fails one-request control | Fixed at the read boundary only |
| Nested-unlisted coverage is cheap-only | Listed sibling retained; M4 now fails the actual install outcome | Confirmed coverage gap fixed |
| Startup OSError escapes or logs twice | Eight guarded entry/shell cases fail turn 8 and pass fixed code, asserting one pending log | Confirmed and fixed |
| Timeout cleanup targets launcher | Atomic interpreter PID reporting and PID-based SIGTERM; normal child cases pass | Harness corrected; forced timeout branch inspected |
| Missing security tests / headless notice | M1/M15 fail; N13 pre-request and dialog-equality assertions pass | Coverage and notice fixed |
| New lint slip | Initial lint flagged SIM105 in timeout cleanup | Fixed using `contextlib.suppress`; final lint clean |
| Final in-envelope pass | Required checks, 452 / 101 / 24 tests, restored probes and footprint audit | No further in-envelope finding |

Ledger: 0 critical / 1 major / 1 minor / 7 advisory, nine reported findings,
no reopened finding or revert; four product-code / three test-only / one
documentation finding groups, F8 banked. F5/F9 listed folds are expressly
granted despite their original envelope classification. Prior depth:
137,204 / 475,000 (dispatch 9); this turn: DISPATCHER TO FILL. No stopped item,
open question or unapproved deviation remains. Prior-correct controls are
disclosed above rather than falsely claiming all new tests fail old code.

Ready for the short Claude delta review, seat re-run and gate. Run-1 evidence
is preserved; the new measurement is not claimed. No new dependency, loader
edit, frozen-interface change, real fetch, GPU activation, frozen run/build,
desktop input, git write or footage/real-profile write occurred. Scratch
probes and synthetic artifacts stay under ignored `work/`; none is a
download/seat script.

## Delta (B r1 fold) advisories

The turn-9 delta review (`B/delta/review.txt`) returned
NO_NEW_CRITICAL_MAJOR, with all eight ruled folds holding and 10/10 mutants
killed. Four of its six ADVISORIES are folded here; A2/A4 remain seat/CHARC
register and owner items, with no code. The B r1 table's directory-fsync
cleanup description above is historical and is superseded by A1 here.

| Advisory | Change | Verification |
| --- | --- | --- |
| A1 | After publication, clear the staging cleanup reference. Any OSError in the off-win32 directory-sync block logs one warning and retains the complete pack. Keep the existing `if sys.platform != "win32"` statement form: only this branch uses directory descriptors, consistent with the already accepted guard | Extended POSIX publication test simulates EINVAL: success, original destination present, full check clean, one warning and descriptor closed. Normal directory-sync order control still passes |
| A3 | Suppress OSError/ValueError from the N13 print; retain its position before requests | New broken-stdout tests for both exceptions complete an actual fake-index installation. Existing pre-request notice and dialog-text equality tests remain green |
| A5 | If no PID was reported, attempt Windows `taskkill /T /F /PID <launcher pid>` while the tree root is still identifiable, then `child.kill()` as fallback and bounded wait. Retain the reported-interpreter-PID path and eight-second child deadline | Normal DLL/extension child cases pass; fallback inspected for bounded `taskkill` (5 s), suppressed cleanup errors and final bounded wait (10 s). The never-reporting branch was not forced this turn |
| A6 | Add the labelled PowerShell `Start-Process -Wait` recipe beside the cmd.exe recipe in the two allowed paragraphs; correct the README CR history statement above | Paragraph-only diff audit; repository README blobs before/after turn 9 both have 0 CR bytes |

A2's cross-process marker/status observation belongs with F8's register row;
A4's precise NVIDIA `.dist-info` licence location is for the owner at accept.
No licence wording or shell behavior changes in this turn. The seat re-run
section and its **SEAT TO FILL** figure remain untouched.

All command output is under `work/wp6.3a/`. Every pytest command set
`PYTHONPATH=scripts`, `QT_QPA_PLATFORM=offscreen`, loaded the sandbox shim and
disabled cacheprovider, with bounded timeouts and disposable basetemps.

| Command | Result / evidence |
| --- | --- |
| `uv run --no-sync ruff check .` | All checks passed, exit 0; `bdelta-ruff.log` |
| `uv run --no-sync ruff format --check .` | 327 files formatted, exit 0; `bdelta-format.log` |
| `uv run --no-sync mypy` | No issues in 163 source files, exit 0; `bdelta-mypy.log` |
| `uv run --no-sync mypy --platform darwin` | Exactly 4 accepted errors in 3 files / 163 checked, exit 1; `bdelta-darwin.log` |
| `uv run --no-sync python work/wp6.3a/bdelta-turn9.py` | Exact turn-9 installer loaded in memory: **3 expected failures / 1 passing control / 100 deselected in 0.59 s**, exit 1; `bdelta-turn9.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack_install.py -k 'posix_publication or broken_stdout' --basetemp=work/c63a-10green` | Fixed normal code: **4 passed / 100 deselected in 0.79 s**, exit 0; `bdelta-green.log` |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack.py tests/test_gpu_pack_install.py tests/test_tools_package_build.py tests/test_frozen_entry.py --basetemp=work/c63a-10 --junitxml=work/wp6.3a/bdelta-tests.xml` | **455 passed in 25.37 s**, exit 0; `bdelta-tests.log` / XML |
| `uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 600 tests/test_gui_gpu_pack_dialog.py --basetemp=work/c63a-10gui --junitxml=work/wp6.3a/bdelta-gui.xml` | **24 passed in 1.17 s**, exit 0; `bdelta-gui.log` / XML |
| `uv run --no-sync python work/wp6.3a/bdelta-audit.py` | Five owned files, 0 CR bytes, clean diff check, paragraph-only guide/README edits, unchanged seat section and 0-CR historical README blobs; `bdelta-audit.log` |

The exact Darwin errors remain `src/clearwater/io/video/pipes.py:56`,
`tools/prototype/bench.py:1159`, `tools/prototype/bench.py:1480` and
`tools/spike_io/transport.py:950`. No new error, skip or sandbox residual
occurred. The old-code probe compiles `git show f55175b4` in memory, never
reverts a tracked file. It fails the EINVAL case and both stdout cases;
the normal directory-sync control already passes turn 9. The initial
test-first run also recorded three failures/one pass (`bdelta-red.log`).

Verification loop: confirmed A1 via simulated EINVAL and a missing pack;
confirmed A3 via both escaping stdout exception classes; fixed both and
re-ran all requested tests/static checks. The final owned-file audit finds
no further in-envelope issue. POSIX fsync behavior is simulated on this
Windows host; the real-pack install-time delta remains for the seat.
No new dependency, unowned edit, real network fetch, GPU activation, frozen
run/build, desktop input, git write or real-profile/footage write occurred.
Prior depth is 198,141 / 475,000 (dispatch 10); current depth is DISPATCHER
TO FILL. Four commissioned advisory folds are complete; A2/A4 remain banked
as directed, with no open implementation question.

## B-fold delta ruling (A4)

| Ruling | Change | Verification |
| --- | --- | --- |
| CHARC A4 | Replace the installer/dialog N13 constants and their pinned tests with the exact corrected `.dist-info` licence location wording; update the verbatim report quote. Neither user guide nor README quotes the line, so both remain unchanged | Constants identical, exact and ASCII; source/tests have zero superseded-phrase matches. The unowned brief retains one historical quote. Ruff check clean; format check 327 files; mypy clean in 163 files; installer module **104 passed in 9.57 s**, offscreen dialog **24 passed in 1.04 s**. Five owned files changed, 0 CR bytes, clean diff check |

Evidence under `work/wp6.3a/`: `a4-ruff.log`, `a4-format.log`, `a4-mypy.log`,
`a4-tests.log`, `a4-gui.log`, `a4-audit.log`. Test commands were
`PYTHONPATH=scripts uv run --no-sync pytest -q -p sandbox_mkdir_shim -p no:cacheprovider --timeout 300 tests/test_gpu_pack_install.py --basetemp=work/c63a-11`
and the offscreen equivalent with `--timeout 600 tests/test_gui_gpu_pack_dialog.py --basetemp=work/c63a-11gui`;
the GUI run also loaded the binding sandbox shim. GNU grep was attempted
before and after but failed with `CreateFileMapping`, Win32 error 5, exit 256
(`a4-grep-final.log`). Equivalent `rg -n -F` searches recorded six initial
matches and one remaining match, solely `docs/briefs/wp6.3a-brief.md:36`
(`a4-before.log`, `a4-rg-after.log`); the brief is not owned this turn.
No real network, GPU activation, frozen/build run, desktop input, git write
or real-profile/footage write occurred. The seat re-run section is unchanged.
