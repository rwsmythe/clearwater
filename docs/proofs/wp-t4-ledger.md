# WP-T4 cumulative ledger

## Dispatch and scope

- Codex lane: turn 1 assigned rungs 0 and 1; turn 2 assigned the remaining
  dependency checks and rung 2's worker guard cases.
- Current package diff base: **`2aca60e`**; branch: `wp-t4`. Generation 14
  rebased the three accepted commits to `dfb7214`, `e374e1a`, `6ac384a`;
  it reports content unchanged and patch-id `586b61a1` preserved.
  Historical rung-0 collection base: `9753b7b4cc05bf43c25442cb87aa74e23f2b584f`.
- Initial tracked/untracked status: clean (`STATUS_COUNT=0`), recorded before
  changes in `work/wp-t4/turn1-base.txt`. The ignored local config was present;
  it was not edited.
- Q3's deterministic reproduction and mandatory cache lock were completed in
  turn 3. The current measurement plan follows generation 14's explicit turn-4
  dispatch: **three interleaved BASELINE -> PARALLEL -> SERIAL rounds**.
- Shared/in-flight files remain untouched, including WP-T3's `verify_generated`
  and `tests/test_fixtures.py`. No source, frozen interface, harness, product,
  or footage edit was made. All cell-authored artifacts are inside the worktree;
  no effect outside the permitted workspace/cache is claimed.
- Dispatcher-supplied `tokens used` footers: turn 1 **73,551**, turn 2 **119,645**,
  turn 3 **220,811**. Turn-4 reading is pending; no estimate substituted.

## Turn 1 evidence: collection and dependency

All paths below are relative to `work/wp-t4/`, are ignored scratch evidence,
and are not committed. Collection used `QT_QPA_PLATFORM=offscreen` and the
project's registered strict markers. These are collection counts, not passing
test counts. No BASELINE, PARALLEL, or SERIAL execution was run by the cell.

| Check | Command | Result | Evidence |
|---|---|---|---|
| Initial environment | `uv sync` | Exit 0 | `turn1-uv-sync.log` |
| Full collection | `uv run pytest --collect-only -q` | 4,768 collected; exit 0 | `turn1-collect-all.log` |
| Parallel collection | `uv run pytest --collect-only -q -m "not gpu and not footage and not gui and not slow"` | 3,762 collected, 1,006 deselected; exit 0 | `turn1-collect-parallel.log` |
| Serial collection | `uv run pytest --collect-only -q -m "gpu or footage or gui or slow"` | 1,006 collected, 3,762 deselected; exit 0 | `turn1-collect-serial.log` |
| Marker membership | `uv run python work/wp-t4/turn1_markers.py` | 4,768 collected; exit 0 | `turn1-marker-collection.log`, `turn1-marker-counts.json` |
| GNU partition instrument | `uv run python work/wp-t4/turn1_partition.py` | Exit 1: GNU sort could not start; see finding T1-1 | `turn1-partition-proof.log` |
| Independent set proof | `.venv/Scripts/python.exe work/wp-t4/turn1_partition_native.py` | Exit 0; intersection and union symmetric difference both empty | `turn1-partition-native.log`, `turn1-partition-counts.json` |
| Dependency resolution, one attempt | `uv lock` (without `--upgrade`) | Exit 2: index connection refused; see finding T1-2 | `turn1-uv-lock.log` |

The collected node-id lists contain no duplicates. The Python proof sorts each
list, proves that parallel and serial are disjoint, and proves that their union
equals the full list: **3,762 + 1,006 = 4,768**. Its empty comparison artifacts
are `turn1-intersection.setdiff` and `turn1-union-difference.setdiff`. Input lists
are `turn1-{all,parallel,serial}.nodes.unsorted`; sorted lists carry the suffix
`.nodes.sorted-native`. This independently establishes the partition, but does
not claim a successful sandbox GNU `comm` invocation. The dispatcher ran
`uv run python work/wp-t4/turn1_partition.py` successfully at its seat; see
the completed handoff below.

Marker counts: `gpu` 579, `footage` 16, `gui` 411, `slow` 16. Their sum is
1,022, exceeding the serial union by 16 memberships. There are **12** distinct
multiply marked tests: eight with two markers and four with three markers.
Thus the brief's explanation "16 tests carry two markers" is inaccurate; its
counts and partition total are correct. The observed total matches the brief's
4,768 and is two above the 4,766 quoted by ruling `6f725eee`.

The only dependency declaration edit is the granted comment and
`"pytest-xdist>=3.6,<4",` in the dev group. At the turn-1 boundary, installation,
licenses, plugin discovery and the dependency-grant test were pending. The
dispatcher and turn-2 evidence below close those checks.

Final turn checks: `git diff --check` exited 0; `git diff --stat` reports only
two added lines in `pyproject.toml` (the new ledger is still untracked).
`turn1-final-state.log` records exit 0 for byte equality of `uv.lock` against
`HEAD:uv.lock`, pytest 8.4.2 in both the lock and installed environment, absence
of xdist/execnet from the unchanged lock, and LF-only bytes in both changed
files. Final status lists exactly `pyproject.toml` and this new ledger.

## Verification-loop record

| ID | Severity / class | Suspected | Independently confirmed or rejected | Fix / disposition |
|---|---|---|---|---|
| T1-1 | Minor; environment, in-envelope; NEW | GNU tools may be unavailable in this sandbox | Confirmed: `sort.exe` exits 256 with `CreateFileMapping`, Win32 error 5; Python instrument exits 1 | CLOSED: dispatcher GNU sort/comm proof passed, both outputs empty |
| T1-2 | Major; environment blocker, in-envelope; NEW | Index access may block the lock update | Confirmed by the single `uv lock` attempt: failed to fetch `https://pypi.org/simple/numpy/`, connection refused, OS error 10061, exit 2 | CLOSED: dispatcher lock and sync exited 0; only xdist and execnet added |
| T1-3 | Minor; brief facts, in-envelope; NEW | The overlap explanation may conflate tests with memberships | Confirmed by marker hook over all 4,768 collected items: eight double and four triple overlaps | Corrected in this ledger; no marker or test edited |
| T1-4 | Verification; rejected false positive | Partition totals might differ on the dispatched base | Rejected by three collections and independent set equality | No change needed; exact 4,768 total recorded |

Turn 1 ended at the dependency-resolution blocker, as required by dispatch.
It made no product-code or test-code fix, revert, exception, or marker move.

## Completed dispatcher handoff

The dispatcher committed turn 1 as `6e2529c`, including its own lock update.
The cell read the summary and `EXIT=0` lines of all three supplied logs:

- `turn1-dispatcher-uv-lock.log`: resolved 62 packages; added execnet 2.1.2
  and pytest-xdist 3.8.0.
- `turn1-dispatcher-uv-sync.log`: installed execnet 2.1.2 and pytest-xdist 3.8.0.
- `turn1-dispatcher-partition.log`: `COMM_INTERSECTION_BYTES=0`,
  `COMM_UNION_DIFFERENCE_BYTES=0`, counts 4,768 / 3,762 / 1,006,
  `PARTITION=PASS`.

Independent turn-2 TOML comparison against `9753b7b:uv.lock` confirms exactly
those two package additions, no removals and no existing package version change;
pytest remains 8.4.2 (`turn2-dependency-evidence.log`, exit 0).
Installed metadata license quotations are:

- `.venv/Lib/site-packages/pytest_xdist-3.8.0.dist-info/METADATA:6`:
  `License-Expression: MIT`.
- `.venv/Lib/site-packages/execnet-2.1.2.dist-info/METADATA:7`:
  `License-Expression: MIT`.

## Turn 2: worker guard evidence

### Sandbox execution conditions

The cell read the supplied uncommitted `work/sandbox/sandbox_mkdir_shim.py`
and did not edit it. It maps `os.mkdir` mode 0o700 to 0o777 to avoid the
diagnosed Windows sandbox owner-only ACL failure. Gate runs at the dispatcher's
seat do not load this shim. All containing pytest invocations used a fresh
basetemp under `work/wp-t4/`, with:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
$env:PYTHONPATH = (Resolve-Path work/sandbox).Path
$env:PYTEST_PLUGINS = 'sandbox_mkdir_shim'
```

Containing pytest commands load `-p sandbox_mkdir_shim -p no:cacheprovider`.
The absolute PYTHONPATH and PYTEST_PLUGINS also reach miniature child pytest
processes, whose cwd differs. No sandbox-specific propagation code was added
to `_run`. It still disables the child's cache provider by default; the existing
explicit cache-enabled test retains its intended coverage. No shim file is
part of the deliverable.

The first `-n 2` run used the scratch probe
`work/wp-t4/test_turn2_shim_probe.py`: two items passed, recording both `gw0`
and `gw1` with the shim registered and an accessible mode-0o700 directory
(`turn2-shim-gw0.json`, `turn2-shim-gw1.json`). The cell did not repeat the
unshimmed ACL failure; that diagnosis is dispatcher-supplied evidence.

### Installed source mechanics and order

Source anchors below refer to installed pytest-xdist 3.8.0 / pytest 8.4.2:

- `.venv/Lib/site-packages/xdist/workermanage.py:333` takes the controller's
  invocation arguments. `WorkerController.setup` at lines 337-341 calls the
  controller temp factory's `getbasetemp()` and forms `<basetemp>/popen-gwN`;
  line 349 sends the options to the worker.
- `.venv/Lib/site-packages/xdist/remote.py:416` sets the worker environment;
  lines 420-424 prepare config, call `setup_config`, and install workerinput.
  `setup_config` sets `config.option.basetemp` at line 400. Line 427 enters
  `pytest_cmdline_main` after that assignment.
- `.venv/Lib/site-packages/_pytest/main.py:285` runs `_do_configure()` before
  `pytest_sessionstart` at line 287. `_do_configure` calls `pytest_configure`
  at `.venv/Lib/site-packages/_pytest/config/__init__.py:1119`.
- `tests/conftest.py:253` marks the guard `tryfirst`; `pytest_configure`
  starts at line 254. The controller therefore refuses unsafe roots before
  `.venv/Lib/site-packages/xdist/dsession.py:83` starts workers in
  `pytest_sessionstart` (node creation at line 90). On workers the guard sees
  the already assigned worker basetemp when configure runs.

### Added cases and observed behavior

Only `tests/test_conftest_guard.py` changed test behavior. The original nine
basetemp target values and IDs are shared, unchanged, with the new worker cases.
Every miniature's configured footage, work, temp roots and output records lie
under that test's `tmp_path`; none names or reads real footage.

- w1: one guard-less `-n 2` control demonstrates deletion of both planted files.
  Its initial, deliberately false unchanged-bytes assertion failed at
  `tests/test_conftest_guard.py:213` (`assert _snapshot(mini.footage) == before`),
  with exit 1, after the child itself exited 0. This is the positive control
  (`turn2-positive-control-red.log`). The final control asserts a changed
  snapshot and absence of both files; it passes.
- w2: nine cases cover equal, trailing separator, existing subfolder, missing
  subfolder, missing nested folder, dotdot inside, relative inside, relative
  equal, and ancestor. All observe child exit 4, `footage guard`, the fake
  folder named in stderr, identical planted bytes and no `popen-gw*` entry
  under fake footage.
- w3: five cases cover `PYTEST_DEBUG_TEMPROOT`, each of TMPDIR, TEMP and TMP
  in isolation, and all three temp variables together, inside fake footage.
  Each observes the same refusal and unchanged tree as w2.
- w4: the child exits 0. Both `gw0` and `gw1` record their worker environment,
  `config.option.basetemp`, and the guard module registered in the worker
  plugin manager. Each basetemp is the expected `popen-gwN` child of the safe
  controller basetemp inside fake work. Fake footage bytes remain unchanged.

### Light-run record

Every log is under `work/wp-t4/` and has an `EXIT=` footer. Define the common
containing command prefix as `uv run pytest -q -rs -p sandbox_mkdir_shim
-p no:cacheprovider`; case runs append a unique `--basetemp` and the named node.
`turn2-case-index.txt` records the exact node ID for each individually run case.

| Run | Command suffix / distinction | Result | Log |
|---|---|---|---|
| Version | `uv run pytest -p sandbox_mkdir_shim -p no:cacheprovider --basetemp=work/wp-t4/t2-version --version` | pytest 8.4.2; exit 0 | `turn2-pytest-version.log` |
| Plugin listing | Same version command, basetemp `t2-version-plugins`, with `--version --version` | Lists xdist 3.8.0 plugin and looponfail; exit 0 | `turn2-pytest-plugins.log` |
| Shim workers | `-n 2 --basetemp=work/wp-t4/t2-shim-n2 work/wp-t4/test_turn2_shim_probe.py` | 2 passed; exit 0 | `turn2-shim-n2.log` |
| Grant / child propagation | `--basetemp=work/wp-t4/t2-grant-and-child tests/test_io_photo_rules.py::test_the_dependency_lines_are_the_wp36_grant tests/test_conftest_guard.py::test_basetemp_in_working_folder_passes` | 2 passed; exit 0 | `turn2-grant-and-child.log` |
| Positive control, red | `--basetemp=work/wp-t4/t2-positive-red tests/test_conftest_guard.py::test_workers_without_the_guard_wipe_the_footage` | 1 deliberately failed at byte assertion; exit 1 | `turn2-positive-control-red.log` |
| Each new case alone | `--basetemp=work/wp-t4/t2-case-NN <node from index>` | All 16 runs: 1 passed, exit 0 | `turn2-case-01.log` through `turn2-case-16.log` |
| Whole guard file | `--basetemp=work/wp-t4/t2-whole-guard tests/test_conftest_guard.py` | 60 passed, no skips; exit 0 | `turn2-whole-guard.log` |
| Lint | `uv run ruff check .` | All checks passed; exit 0 | `turn2-ruff-check.log` |
| Format | `uv run ruff format --check .` | 227 files already formatted; exit 0 | `turn2-ruff-format.log` |
| Types | `uv run mypy` | No issues in 132 source files; exit 0 | `turn2-mypy.log` |

Plain `--version` reports only pytest's version; repeated `--version` actually
lists installed plugins. No dependency test was weakened for the grant check.
All case runs use the outer serial controller and real `-n 2` miniature children;
no full-suite heavy leg was run.

### Turn-2 verification loop

| ID | Severity / class | Suspected | Confirmed / rejected evidence | Fix / disposition |
|---|---|---|---|---|
| T2-1 | Verification; rejected false positive | Guard might fail to protect worker startup | Nine CLI and five environment cases refuse unchanged; safe case records both worker guard plugins and temp roots | No guard code change needed; `tests/conftest.py` untouched |
| T2-2 | Verification; positive control | Guard-less worker run might not demonstrate deletion | Confirmed by exit-1 failure on the planted unchanged-bytes assertion at line 213, following child exit 0 | Final w1 asserts changed snapshot and both planted files absent; passes |
| T2-3 | Minor; environment adaptation | Child pytest might need committed shim propagation logic | Rejected by the existing safe-child case and all new subprocess cases with inherited absolute PYTHONPATH / PYTEST_PLUGINS | No test-helper or shim edit required |

No product code, marker meaning, exception, or in-flight file changed. No guard
failure or new pre-existing test failure was found. The final scoped pass found
no further issue after the individual cases, whole file and lint/type checks.
Independent Reviewer A remains pending with the driver.

The turn-3 dispatcher also supplied an independent, unshimmed run of the
committed guard file: **60 passed in 49.64s, EXIT=0**. Its log path was not
supplied. This confirms that the committed cases do not depend on the shim.

Turn-2 final state: `git -c core.autocrlf=false diff --check` exited 0.
`turn2-final-state.log` exited 0 after checking that exactly this ledger and
`tests/test_conftest_guard.py` are changed, both contain LF-only bytes, and
`pyproject.toml`, `uv.lock`, `tests/conftest.py` and `tests/fixture_plugin.py`
are unchanged against turn-2 HEAD. Status and diff summary are recorded in
`turn2-final-status.log` and `turn2-diff-stat.log`.

## Turn 3: static pass and mandatory cold-cache lock

Turn scope is rung 3 parts 1-2, then the first diagnostic full PARALLEL request.
No full leg or measurement round was executed by the cell. Sandbox pytest uses
absolute `PYTHONPATH=(Resolve-Path scripts).Path`, `PYTEST_PLUGINS=sandbox_mkdir_shim`,
`-p sandbox_mkdir_shim -p no:cacheprovider`, offscreen Qt and fresh basetemps.
The old `work/sandbox/` was left alone.

### Static inventory

The broad scratch search produced 672 candidate lines, including harness hits.
The refined product-only search excludes `tests/harness/**` and produced 135
rows (`turn3-static-shared-paths.txt`); the port search produced zero candidate
lines (`turn3-static-ports.txt`). This is a risk inventory, not a claim that
the unexecuted full leg has no violators.

| Candidate | Evidence / classification | Disposition |
|---|---|---|
| Shared generated fixture | `tests/fixture_plugin.py` originally had one `GENERATED_DIR` at line 41 and an unlocked verify/generate sequence in `SampleProvider.path` | Confirmed by the two-process reproduction below; fixed in owned code |
| Local config / real work | Config-backed bench tests inject fake config rooted in `tmp_path` (`tests/test_io_video_encode_bench.py:615`); look-check helpers use their passed temp root; inventory's real scan is footage-marked (`tests/test_inventory.py:1125`) | No additional shared writer confirmed; runtime window remains necessary |
| Module/session state | `synthetic_pack` (`tests/test_lookcheck.py:554`) and `deep_pack` (`tests/test_lookcheck_deep.py:564`) allocate with `tmp_path_factory.mktemp`; generated samples are the confirmed cross-worker exception | Temp roots are worker-specific; no order dependency proved |
| Process checks / fixed names | `_ffmpeg_children` (`tests/test_io_video_encode_bench.py:35`) examines descendants of the current worker, rather than every worker; fixed output names examined live beneath per-test or per-module temp roots | No process-count or filename violator confirmed; telemetry timing remains a watch item |
| Fixed listeners | No product-test socket/localhost/bind/listen candidates in the focused search | No fixed port confirmed; harness matches excluded |
| Mandatory E1 | `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output`, bound at line 321 | Pending rung 3.4: `@pytest.mark.slow`, comment `timing bound, DR-58 (c); stays serial`; bound unchanged |
| GUI service timing | `tests/test_gui_analysis_service.py::test_pts_and_statistics_never_wait_for_a_run_in_flight`, 0.2-second bound at line 199 | Watch only; no failure confirmed and no edit made |
| Collection GPU probe | `tests/test_prototype_backend.py:23` selects auto backend during import; see diagnostic below | Pre-existing, raised; no marker or product/tool change made |

No in-flight-owned test was edited. `tests/test_fixtures.py` was read and four
of its provider tests were executed, but its bytes were not changed. The
`verify_generated` function and its surrounding writable-dir block remain
unchanged. The only fixture-plugin edits are necessary imports, the owned
`SampleProvider.path` body/docstring, and a helper placed after the class.

### Deterministic reproduction and regression

`tests/test_fixture_cache_lock.py` runs two spawned Python processes with real
providers and real manifest/FFmpeg verification. A wrapper performs the real
initial missing-file check, then synchronizes those two cold misses. A delayed
generator wrapper sleeps two seconds. With competing generators, one produces
the real clip while the other holds a deliberately incomplete file at the same
path until the first provider's real final verification returns; it then
regenerates the clip normally. This makes the partial-write window deterministic.
It does not change `verify_generated` on disk or replace its verification result.

The scratch `turn3_cold_probe.py` resolves the actual worktree target
`work/fixtures/generated`, asserts both exact equality and containment within
the resolved worktree before calling `shutil.rmtree`, and invokes that same
two-process harness. It deletes no other directory.

| Run | Result | Evidence under `work/wp-t4/` |
|---|---|---|
| Actual cold cache, unlocked | Both child processes exited 0; two generator calls; one provider recorded `Failed: regenerated sample 'ad14-flicker' does not match the manifest ... cannot probe ... KeyError('streams')`; harness exit 1 | `uv run python work/wp-t4/turn3_cold_probe.py`; `turn3-cold-probe-red.log` |
| Committed regression against unlocked code | Exit 1 at `tests/test_fixture_cache_lock.py:131`, `assert all(record["ok"] for record in result["records"]), result`; same partial-clip verification failure and two generator calls | Serial containing pytest, basetemp `work/wp-t4/t3-regression-red`; `turn3-regression-red.log` |
| New file, locked | 4 passed; exit 0 | Serial containing pytest, basetemp `work/wp-t4/t3-lock-green`; `turn3-lock-green.log` |
| Actual cold cache, locked | Two successful providers, one generator call, no timeout; exit 0 | `uv run python work/wp-t4/turn3_cold_probe.py --phase after-lock`; `turn3-cold-probe-green.log` |
| Worker integration | 8 passed at `-n 4`; exit 0 | Basetemp `work/wp-t4/t3-lock-workers`; `turn3-lock-workers.log` |

The worker integration's exact test selection is the whole new
`tests/test_fixture_cache_lock.py` plus these unchanged `tests/test_fixtures.py`
nodes: `test_plugin_regenerates_a_stale_clip_and_verifies_it`,
`test_plugin_fails_when_regeneration_cannot_match`,
`test_plugin_skips_a_generated_sample_when_ffmpeg_is_absent`, and
`test_plugin_hands_out_committed_samples_without_ffmpeg`. Its command was
`uv run pytest -q -rs -n 4 -p sandbox_mkdir_shim -p no:cacheprovider
--basetemp=work/wp-t4/t3-lock-workers` followed by that selection.

### Lock policy and limits

`SampleProvider.path` (`tests/fixture_plugin.py:170`, acquisition at line 202)
re-verifies after entering `_generated_cache_lock` (line 217), so another
process's completed generation is reused. The helper uses exclusive creation
of `.<cache-name>.lock` beside the cache, records the owner PID, waits at most
180 monotonic seconds with 50 ms polling, and releases in `finally`, including
when generation or verification raises. An existing lock aged at least 900
seconds causes an immediate suspected-stale error with instructions to confirm
the owner has stopped before removing it. Age does not authorize stealing the
lock; there is no unsafe age-only unlink race or OS-specific PID-liveness code.
This is the explicit stale-lock rule. A killed process therefore requires
owner-confirmed cleanup, rather than automatic lock stealing.

The new tests cover the two-process cold miss, an occupied lock's bounded wait,
the conservative stale-lock rule and exception release/reacquisition. No new
dependency, OS-specific implementation or product/frozen-interface edit was made.

### Optional collection diagnostic

An optional full parallel-partition collection unexpectedly spun in the sandbox
before producing node IDs. After observing 205 seconds of CPU use, the cell
verified its unique basetemp argument and stopped only that collection's uv
process tree (`turn3-collection-processes.log`, `turn3-stop-collection.log`;
the original runner ended with `EXIT=15`). A bounded 10-second faulthandler
reproduction exited 1 and identified this stack:
`test_prototype_backend.py:23` -> `select_backend` -> `_probe_gpu` -> CuPy
`arange` -> CUDA compiler cache -> `tempfile.NamedTemporaryFile`.
Evidence: `turn3-collection-trace.log`, `turn3-collection-trace.txt`.

The installed CuPy cache code reads `CUPY_CACHE_DIR` at
`.venv/Lib/site-packages/cupy/cuda/_compiler_cache.py:93`. Setting only that
variable to this worktree's `work/wp-t4/cupy-cache` made the same collection
finish: **3,782 / 4,788 collected, 1,006 deselected, exit 0**
(`turn3-collection-local-cache.log`, 30-second bound not reached).
No product code or marker changed. The successful cache writes are inside the
worktree; no successful default-cache write outside it is claimed.

The collection GPU probe predates this package: blame identifies `fedb8c9a`
for line 23, and the `git log -S select_backend` evidence also predates the
package (`turn3-collection-provenance.log`). Marker selection occurs after
module import, so excluding GPU-marked execution does not prevent that probe.
GPU-memory rise during the requested full leg is not yet measured; if observed
it must be reported, with marker semantics left out of scope.

### Sampler and first full-leg request

Uncommitted instrument: `work/wp-t4/monitor_pytest.py` (stdlib plus existing
psutil). Start it before pytest with the matching basetemp and launcher PID/file.
It finds the topmost pytest launcher/interpreter among that launcher's
descendants, excluding the uv wrapper, and samples once per second: summed
tree RSS, system available bytes, and per-GPU used MiB through `nvidia-smi`
when available. It records UTC timestamps, process IDs, query errors, peak RSS,
minimum available memory, GPU baseline/peak/rise, and remaining child PIDs.
A sample below 2 GiB, inaccessible RSS or an incomplete present-GPU reading
makes the sampler nonzero. It does not lower N or kill the pytest run.

The first smoke test's host-wide command-line search missed the short workload
and exited 3 (`turn3-sampler-smoke.log`). Replacing that search with the explicit
launcher's descendant tree passed: six samples, maximum six observed tree
processes including both workers, positive RSS, complete GPU readings, no
remaining children; exit 0 (`turn3-sampler-smoke-02.log`,
`turn3-sampler-smoke-02.jsonl`). The smoke pytest itself passed two items.
These are instrument checks, not N=4 memory figures or figures of record.

The dispatcher-ready scratch script `work/wp-t4/run_parallel_01.ps1` has a
zero-error PowerShell parse (`turn3-runner-syntax.log`). It checks >=5 GiB
available before starting, refuses a shim-enabled environment, starts the
sampler hidden, and executes exactly:

```powershell
$env:QT_QPA_PLATFORM = 'offscreen'
uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/t3-parallel-01 > work/wp-t4/turn3-parallel-01.log 2>&1
```

It appends UTC start/end, wall seconds and `EXIT=` to the leg log. Its sampler
command is `uv run python work/wp-t4/monitor_pytest.py --basetemp
work/wp-t4/t3-parallel-01 --launcher-pid-file
work/wp-t4/turn3-parallel-01-launcher.pid --out
work/wp-t4/turn3-parallel-01-memory.jsonl`; stdout/stderr and exit status also
go to files under `work/wp-t4/`. No shim is loaded at the dispatcher's seat.
The first leg is diagnostic: E1 is still unmarked on this turn's head and will
receive its mandated slow mark in the next rung-3.4 scope. No test was moved
out in this turn, and no settled round is claimed.

### Turn-3 verification loop and checks

| ID | Severity / class | Suspected / confirmed / rejected | Fix / disposition |
|---|---|---|---|
| T3-1 | Major, introduced concurrency exposure; in envelope | Confirmed shared-cache race with two real processes, actual cold worktree cache and failing standalone regression | Fixed in test infrastructure with the lock and post-acquisition re-verification; real-cache and 8-test worker checks pass |
| T3-2 | Minor, scratch instrument | First sampler discovery missed its short target; confirmed exit 3 | Fixed with explicit launcher ancestry; six-sample smoke passes |
| T3-3 | Minor, style | Initial checks found one long line and one non-raw regex; format check failed | Fixed in the new test file only; final lint/format green |
| T3-4 | Major nominal, pre-existing environment/marker issue; not a new blocking review finding | Bounded trace confirms collection GPU probe stalls at default CuPy cache creation; local-cache environment completes the same collection | Sandbox cache redirected only for that diagnostic; GPU import access raised to dispatcher, no product/tool/marker edit |
| T3-5 | Verification, rejected false positives | Other shared config paths, module fixtures and worker-local process checks examined; no further violator confirmed | Runtime classification awaits the full-leg output; no speculative test edits |

Final code checks: `uv run ruff check .` all checks passed,
`uv run ruff format --check .` 228 files already formatted, and
`uv run mypy` no issues in 132 source files; all exit 0. Logs are
`turn3-ruff-check.log`, `turn3-ruff-format.log`, `turn3-mypy.log`.

Final state checks (`turn3-final-state.log`, exit 0) confirm exactly the three
owned changed paths, LF-only bytes, byte identity of `verify_generated` and
its surrounding writable-dir block, unchanged session-fixture tail and other
SampleProvider methods, and placement of the helper after the class. Product,
tools, scripts, harness, conftest, in-flight fixture tests and dependency files
have no turn-3 diff. `git diff --check` also exited 0. After all checks, the
cell again resolved and asserted the exact worktree cache target, verified its
sibling lock absent, and removed only `work/fixtures/generated`; the requested
first full leg will therefore start **cold**. Logs, test temp roots and the
worktree-local CuPy cache were retained as evidence.

## Turn 4: rung-3 classification, E1 and the measurement-window handoff

### Diagnostic full leg and collection reconciliation

The cell read the diagnostic leg, preflight and sampler summaries supplied by
generation 14. The PowerShell leg log is UTF-16; sampler JSONL is UTF-8.
The pytest leg itself exited **0**, while the sampler and wrapper exited **4**.
There were **zero failures/errors and zero violators from this run**. Its one
skip is `tests/test_color_roundtrip.py:121`, reason:
`swscale reads a yuvj format as full whatever in_range says (refused instead)`.
The five warnings are not outcome failures.

Fresh collection on base `2aca60e`, before adding E1's marker, produced:
**4,889 all; 3,883 parallel; 1,006 serial**, all exit 0. Therefore the executed
leg's **3,882 passed + 1 skipped = 3,883** accounts for every selected node.
Compared with turn 3's old-base parallel collection, the exact node-set change
is **103 added and two removed**, all in `tests/test_fixtures.py`, for a net
increase of 101. This was measured, not inferred from the rebase description.
The changed-ID lists are `turn4-rebase-added.nodes` and
`turn4-rebase-removed.nodes` under `work/wp-t4/`.

After E1's marker, explicit `--strict-markers` collection produced:
**4,889 all; 3,882 parallel; 1,007 serial**, all exit 0. The sorted node sets
prove disjoint legs whose union equals the full suite; the full node set did
not change, and E1 is the only node transferred from parallel to serial.
Evidence: `turn4-before-e1-collect-{all,parallel,serial}.log`,
`turn4-after-e1-collect-{all,parallel,serial}.log`, `turn4-partition.log`,
`turn4-partition.json`, and `turn4-{before,after}-{all,parallel,serial}.nodes`.
All these are scratch files under `work/wp-t4/`. Collection used the committed
sandbox shim and a worktree-local CUPY_CACHE_DIR, as diagnosed in turn 3.

### Complete exception and violator lists

**Confirmed full-leg violators: none.** No speculative concurrency remedy or
xdist grouping was added. No in-flight-owned test was edited.

| Test ID | Reason | Remedy / status |
|---|---|---|
| `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` | `timing bound, DR-58 (c); stays serial` | Added exactly that comment and `@pytest.mark.slow`; body and `-0.05` bound unchanged |

This is the complete moved-test exception list: **one test**, no whole file,
no marker meaning changed, no `xdist_group` or `--dist loadgroup` used. `slow`
was already registered; strict collection confirms the marker is accepted.

**Dispatch fact correction:** the GUI service watch node
`tests/test_gui_analysis_service.py::test_pts_and_statistics_never_wait_for_a_run_in_flight`
is actually **in the parallel leg**, and absent from serial, both before and
after E1. `turn4-watch-membership.log` and the collected node lists establish
this. The source has no applicable gui marker. The diagnostic full leg passed
it (its only skip was the different color-roundtrip node). The instruction to
say this watch item is excluded by `not gui` contradicts measured membership;
no gui marker was added or its meaning changed to make that statement true.

### Existing E1 serial timing failure, raised without relaxing it

A light serial sandbox run of E1 with `--strict-markers`, a fresh basetemp and
the shim failed its existing bound at line 323:
`assert -0.05 < offsets["telemetry_origin"] <= 0`, observed
`offsets["telemetry_origin"] = -0.06995480007026345`.
Result: **1 failed, exit 1**, `work/wp-t4/turn4-e1-serial.log`.
The test body is unchanged by this package; only its marker/comment changed.
The preceding full diagnostic leg passed E1. This is a raised, existing timing
failure in the serial sandbox environment, **not a parallel violator**. Its
environmental cause is not claimed established. The bound was not widened,
the test was not skipped, and a rerun-until-green was not substituted for the
failure. Quiet-seat reproduction is requested before the long round windows:

```powershell
powershell -NoProfile -File work/wp-t4/run_e1_seat_probe.ps1
```

That unshimmed wrapper runs exactly
`uv run pytest -q -rs --strict-markers --basetemp=work/wp-t4/turn4-e1-seat-tmp tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output`,
redirects both streams to `work/wp-t4/turn4-e1-seat.log` and appends `EXIT=`.
It refuses existing evidence. A repeat failure at the quiet seat needs a
dispatcher/architect disposition; this cell has no grant to relax the bound.

### GPU gaps, negative timeout and corrected scratch sampler

The diagnostic JSONL has 360 RSS samples and five missing GPU readings. Four
GPU errors say timeout 0.8 seconds; one says approximately -0.013 seconds.
The inspected old sampler supplied a **fixed positive `timeout=0.8`** to
`subprocess.run`; its scheduling tick only computed a sleep duration.
CPython 3.12.13 `Lib/subprocess.py:1228` passes `self._remaining_time(endtime)`
from `communicate` into `wait`, and the Windows `_wait` at line 1593 includes
that timeout argument in `TimeoutExpired`. Once the communicate deadline is
exhausted, the reported remaining duration can be negative. The observed
negative value is consistent with this CPython path; it does not demonstrate
a sampler timeout derived from the sampling tick.
Evidence: `turn4-sampler-diagnostic.log` and the inspected stdlib source.

The five gaps leave the GPU series incomplete: **1457 MiB is an observed peak
and the +1334 MiB rise is an observed lower bound**, not a certified complete
sampled GPU peak. The rise itself is established and is raised as graphics-card
use in the nominal non-GPU leg, as required by the brief. The previously traced
module-import GPU probe remains an identified pre-existing mechanism; no
marker/product/tool fix was made. The leg's wall time and complete RSS/available
memory series remain valid diagnostic evidence, with no memory-floor breach.
**D1 does not count as a settled rung-4 round**: GPU data have gaps, it predates
E1's partition change, and it has no paired baseline/serial measurements.

`work/wp-t4/monitor_pytest.py` now uses a fixed positive **5-second** GPU-query
timeout and a separate GPU-reading thread. Main-thread RSS and available-memory
polls keep their one-second schedule. Every real GPU query records its own
completion time, sequence, elapsed duration and slow-read flag. RSS records
carry the latest GPU observation with its timestamp and explicit age; reused
readings are not represented as fresh queries. Baseline readiness is signaled
before pytest starts. Genuine query failures still make `gpu_complete=false`
and sampler exit nonzero; slow successful reads remain measured observations.
Summary fields also expose query/error counts, longest read, maximum observation
age and maximum RSS polling interval. No gap is filled by an invented value.

A controlled smoke check injected a two-second delay before every successful
real GPU query. It passed: **8 RSS samples, 5 GPU queries, 5 slow successful
reads, GPU complete, longest read 2.2040 s, maximum RSS interval 1.0310 s**;
sampler exit 0 and the two-worker pytest workload passed. Evidence:
`turn4-sampler-smoke.log`, `turn4-sampler-smoke.jsonl`, and its monitor/pytest
logs. These are instrument checks, not measurement figures for N=4.

For rung 4, a usable full PARALLEL measurement needs the intended one-second
RSS series, complete real GPU query results when nvidia-smi is present, explicit
latencies/ages for slow observations, sampler exit 0 and no available-memory
sample below 2 GiB. A real GPU query failure requires a fresh measurement window
after the instrument issue is resolved; the cell will not silently validate
missing observations, lower N or alter marker meaning. The medians additionally
need matching frozen heads, matching sampler snapshots, green legs and matching
per-round outcome totals.

### Rung-4 requests: three interleaved rounds, one wrapper per window

Generation 14's turn-4 dispatch explicitly requests three rounds. Each round
runs **BASELINE, then PARALLEL, then SERIAL**, one granted quiet-host window at
a time, on the frozen post-E1 head. No rung-4 window has been run by the cell.
Commands, collected counts and logs are recorded in `turn4-r4-plan.json`.

The nine wrappers call `work/wp-t4/run_r4.ps1` with fixed round/leg arguments.
They resolve the worktree from their own path, set `QT_QPA_PLATFORM=offscreen`,
refuse the shim, check >=5 GiB available before each run, refuse every existing
evidence path and basetemp, record HEAD/commands/conditions, and append UTC
start/end, wall seconds and `EXIT=`. Parallel wrappers copy and hash the exact
sampler source, start it hidden, and wait for baseline readiness before pytest.
They preserve separate leg and sampler exits. Logs and sampler data stay under
`work/wp-t4/`. No extra heavy job or N change is launched automatically.

The plan uses the same marker expressions throughout: all **4,889** tests in
BASELINE, **3,882** in PARALLEL, **1,007** in SERIAL. Per-round passed/skipped/
failed/xfailed totals must add to BASELINE, with zero PARALLEL failures. Sampled
GPU activity remains a disclosed finding. Final figures must state the actual
start times and conditions: same quiet host, **not a figure of record**.

All nine overwrite refusals were exercised with planted run-log artifacts and
an error-only uv stub, so **no real uv/pytest command could start**. Nine of
nine refused before preflight and preserved the planted bytes; only those
planted files were removed afterwards (`turn4-wrapper-guards.log` plus per-case
logs). The common runner, nine run wrappers and E1 seat wrapper have zero
PowerShell parse errors (`turn4-wrapper-syntax.log`).

| Round / leg | Dispatcher RUN REQUEST | Exact pytest command (wrapper redirects to its unique log and appends EXIT) |
|---|---|---|
| 1 / baseline | `powershell -NoProfile -File work/wp-t4/run_r4_r1_baseline.ps1` | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r1-baseline-tmp` |
| 1 / parallel | `powershell -NoProfile -File work/wp-t4/run_r4_r1_parallel.ps1` | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r1-parallel-tmp` |
| 1 / serial | `powershell -NoProfile -File work/wp-t4/run_r4_r1_serial.ps1` | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r1-serial-tmp` |
| 2 / baseline | `powershell -NoProfile -File work/wp-t4/run_r4_r2_baseline.ps1` | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r2-baseline-tmp` |
| 2 / parallel | `powershell -NoProfile -File work/wp-t4/run_r4_r2_parallel.ps1` | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r2-parallel-tmp` |
| 2 / serial | `powershell -NoProfile -File work/wp-t4/run_r4_r2_serial.ps1` | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r2-serial-tmp` |
| 3 / baseline | `powershell -NoProfile -File work/wp-t4/run_r4_r3_baseline.ps1` | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r3-baseline-tmp` |
| 3 / parallel | `powershell -NoProfile -File work/wp-t4/run_r4_r3_parallel.ps1` | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r3-parallel-tmp` |
| 3 / serial | `powershell -NoProfile -File work/wp-t4/run_r4_r3_serial.ps1` | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r3-serial-tmp` |

### Turn-4 verification loop

| ID | Severity / class | Confirmed / rejected evidence | Disposition |
|---|---|---|---|
| T4-1 | Verification, count reconciliation | 103 added and 2 removed fixture-test IDs explain the net +101 selected tests; 3882+1 matches the executed leg | Report corrected by measured node sets; no test edit needed |
| T4-2 | Minor, scratch measurement instrument | Five GPU gaps; old code fixed timeout 0.8; CPython remaining-deadline path explains the negative message | Fixed scratch instrument with 5-second queries, asynchronous GPU reads and explicit latency/age; slow-read smoke passes |
| T4-3 | Minor, dispatch fact correction | Watch node appears in parallel and not serial in both collections | Raised with proof; no marker edit |
| T4-4 | Major nominal, existing serial timing failure | E1 fails the unchanged -0.05 bound with -0.0699548 in a serial sandbox run | Not a violator; raised for quiet-seat check; no bound relaxation or skip |
| T4-5 | Verification, exception budget | Strict marker collection accepts E1; one node transfers and all-suite node set is identical | One mandated slow exception, within the 20-test limit; no grouping |

Final lint/type checks all exit 0: ruff check passes, ruff format reports 228
files already formatted, and mypy reports no issues in 132 source files.
Evidence: `turn4-ruff-check.log`, `turn4-ruff-format.log`, `turn4-mypy.log`.
The single E1 timing failure is disclosed above; an all-tests-green claim is
not made for the current head. Independent reviewer rounds remain pending.

Final turn-4 state checks (`turn4-final-state.log`, exit 0) confirm exactly two
owned changed paths, LF-only bytes, and an exact two-line test-file change:
the required reason comment plus `@pytest.mark.slow`. The entire remaining
file, including E1's body and bound, is byte-identical to HEAD. Protected source,
tools, scripts, fixture infrastructure, in-flight fixture tests and dependency
files have no turn-4 diff. All nine ordered wrappers exist, no rung-4 measurement
log exists, and the command table matches the plan JSON. `git diff --check`
exited 0. The corrected sampler's current SHA-256 is
`64a57c731a09a7eca1e4c6f5b882975888ca0233434cc02b2c69e0dbc7ee0854`;
the three actual PARALLEL snapshots must match while the plan remains frozen.

## Heavy-run ledger

The dispatcher ran D1 after turn-3 yield. No heavy leg was executed by the cell.

| Run / head | Start UTC | End UTC | Command / log under work/wp-t4 | N | Counts | Leg / sampler / wrapper exit | Free before | Peak summed RSS | Minimum available | GPU / qualification |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 diagnostic / `6ac384a`, before E1 | 2026-10-27 08:51:03.9259564Z | 2026-10-27 08:57:03.4570794Z | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/t3-parallel-01`; `turn3-parallel-01.log` | 4 | 3882 passed, 1 skipped, 0 failed, 0 xfailed; 5 warnings | 0 / 4 / 4 | 11.899719 GiB | 6,821,711,872 B | 6,184,673,280 B | Baseline 123 MiB, observed peak 1457 MiB, rise 1334 MiB; 5/360 GPU gaps; diagnostic only |

D1 wall time: **359.5270566 seconds** (pytest's own duration 358.33 seconds).
Its 360 RSS samples have no access-denied reading, no <2 GiB sample and no
remaining child PID. Rung-4 rows will be added from actual window results,
including per-round counts, frozen HEAD and sampler hash, not estimated figures.

## Cumulative review-round ledger

| Round | Critical / major / minor | In / out of envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Reviewer transport / version | Dispatcher-read depth | Disposition |
|---|---|---|---|---|---|---|---|---|
| Not started | N/A | N/A | N/A | 0 | 0 / 0 | Driver-owned Claude Opus high; pending | Turn-3 footer 220,811; turn 4 pending | End-of-rung-3 yield; E1 quiet-seat check, then requested measurement windows |

## Open handoff

1. Driver-owned Reviewer A and its assertions remain pending; no review round
   is claimed clean or counted toward convergence.
2. Quiet-seat E1 probe requested first, because the light serial sandbox run
   failed its unchanged timing bound. A seat failure needs a disposition before
   the long measurement sequence; this cell will not relax the bound.
3. Rung 3 classification and E1's mandatory slow mark are complete. Violator
   list empty; exception list contains E1 only. Three interleaved measurement
   rounds are requested through the nine wrappers above, one window at a time.
4. The Q2 docstring paragraph, final report, reviewer rounds, measurement-based
   N rationale and final both-leg gate remain future work. The watch node's
   actual parallel membership and the observed GPU rise remain disclosed.
