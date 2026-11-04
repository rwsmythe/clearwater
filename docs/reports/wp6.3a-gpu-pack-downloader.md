# WP6.3a - GPU pack downloader

Candidate build report, 2026-11-04. Part 1 is committed at `9f5b6f5b`; this
turn adds the request surfaces and their tests. Reviewer A, Reviewer B, the
release gate and the real-download seat proof remain with the orchestrator.

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
`.data` paths, links and special members are refused. Wheel RECORD bytes are
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
under the calculated root and also removes matching partial folders. It reports
filesystem errors, including locked files, rather than claiming removal.

`build.py` delegates its manifest construction and writer to the product
module. Its hand-filled writer retains the folder-name-equals-STAMP refusal;
`--verify` and the bundle checker were not changed. The shared checker's only
other changes are the ruled four-field filename/hash projection (S2) and the
full-check lstat/link/reparse rejection (S3). The cheap startup check is
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

The dispatch order in `clearwater.__main__.main` is:

1. Frozen multiprocessing refusal.
2. Executable-folder PATH step.
3. Shared source/frozen `--install-gpu-pack` / `--remove-gpu-pack` row, with no
   further arguments; no loader, logging setup or Qt import on this row.
4. Existing frozen export-worker branch (the temporary stdin shim untouched).
5. Existing frozen interpreter re-entry branch.
6. Existing frozen logging setup, then loader activation and GUI.

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

## Validation

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

No Reviewer A round has run in this turn. The dispatcher runs the Claude pass
and returns its findings for a later adjudication turn. This report is not a
review-convergence claim.

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
table support are not a proved Linux installer. No new dependency or OS API
was introduced by this turn. Footage and the owner's profiles are untouched.

The real pack's 2,701-file / 2,412.6 MiB census is an expected seat comparison,
not a cell result. Real download, frozen build, two GPU worker runs, mapped-file
proof, product removal and real-profile absence checks belong to the seat.
The cell wrote no seat/download script and ran no frozen executable. Reviewer
A convergence, Reviewer B and the final gate are pending.
