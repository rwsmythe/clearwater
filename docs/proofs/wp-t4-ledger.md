# WP-T4 cumulative ledger

## Dispatch and scope

- Codex lane: turn 1 assigned rungs 0 and 1; turn 2 assigned the remaining
  dependency checks and rung 2's worker guard cases.
- Current package diff base: **`ba6e923`**; branch: `wp-t4`. Generation 14
  rebased the four accepted commits to `e8f30e5`, `4488d50`, `a38e680`,
  `f8b8f4b`; it reports content unchanged and patch-id `525a84c8` preserved.
  HEAD on entry to turn 5 is `f8b8f4b`, with clean git status. The new main
  includes WP3.20R (`dbb5858`), WP3.14 (`ba6e923`), harness and docs changes.
  Historical heads in the evidence below describe the runs when they occurred.
  Historical rung-0 collection base: `9753b7b4cc05bf43c25442cb87aa74e23f2b584f`.
- Initial tracked/untracked status: clean (`STATUS_COUNT=0`), recorded before
  changes in `work/wp-t4/turn1-base.txt`. The ignored local config was present;
  it was not edited.
- Q3's deterministic reproduction and mandatory cache lock were completed in
  turn 3. Generation 14's turn-5 dispatch restores FINAL ruling Q7:
  **TWO interleaved BASELINE -> PARALLEL -> SERIAL rounds**; a third only if
  the two PARALLEL+SERIAL wall-time totals differ by more than 15 percent.
  D1, D2 and D3 are diagnostics, not measurement rounds. R1/r2 are now measured
  on `dd49a15`; their P+S totals differ by <1%, so no third round is requested.
- Shared/in-flight files remain untouched, including WP-T3's `verify_generated`
  and `tests/test_fixtures.py`. No source, frozen interface, harness, product,
  or footage edit was made. All cell-authored artifacts are inside the worktree;
  no effect outside the permitted workspace/cache is claimed.
- Dispatcher-supplied `tokens used` footers: turn 1 **73,551**, turn 2 **119,645**,
  turn 3 **220,811**. The dispatcher supplied turn 4's actual session-request
  **depth_input_tokens = 284,234**, window 475,000; this is an input-depth
  reading, distinct from the earlier `tokens used` footers. Turn 5 ended at
  **depth_input_tokens = 95,253**, supplied by generation 14 after committing
  the ledger as `dd49a15`. CHARC ruled a fresh session "a choice, not a
  necessity" after the depth fell to 95K. **SESSION CHOICE: this session
  continues; no fresh session is used**, because it already holds rungs 1-3.
  The old RESUME HERE checklist was followed in turn 6 and is now updated for
  Reviewer A, final settled-head legs and the return. The dispatcher supplied
  **turn-6 depth_input_tokens = 152,531** after accepting turn 6 as `5e6a8d3`
  (three files, zero CR bytes). Turn-7 depth remains pending the driver's
  reading; no estimate or older peak is substituted for it.

- CHARC's later figure ruling `144f9735` governs the interpretation of all
  historical "not a figure of record" condition strings below: these ARE
  same-quiet-host **suite wall-time figures**, not N6/V16 product timing
  figures. Product timing and memory figures are obtained serially in their
  own windows. The report now carries that distinction and the 3849 s / 64 min
  median P+S figure for the accept-time CLAUDE pointer.

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
| Pre-commit regression variant against unlocked code (citation corrected in turn 7) | Exit 1 at historical `tests/test_fixture_cache_lock.py:131`, `assert all(record["ok"] for record in result["records"]), result`; same partial-clip verification failure and two generator calls | Serial containing pytest, basetemp `work/wp-t4/t3-regression-red`; `turn3-regression-red.log` |
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

### Rung-4 protocol and executed requests (updated turn 6)

Generation 14's turn-5 dispatch superseded the turn-4 request for three rounds.
The dispatcher has now completed **r1 and r2**, each **BASELINE, then PARALLEL,
then SERIAL**, on `dd49a15`, one quiet-host window at a time. Q7's 15-percent
drift condition is not met: no r3 is needed, requested or included. The three
r3 wrappers remain unused. `turn4-r4-plan.json` records nine available commands;
the first six were executed. No heavy leg was executed by the cell. The
executed rows and source-file-derived figures are recorded below.

The nine wrappers call `work/wp-t4/run_r4.ps1` with fixed round/leg arguments.
They resolve the worktree from their own path, set `QT_QPA_PLATFORM=offscreen`,
refuse the shim, check >=5 GiB available before each run, refuse every existing
evidence path and basetemp, record HEAD/commands/conditions, and append UTC
start/end, wall seconds and `EXIT=`. Parallel wrappers copy and hash the exact
sampler source, start it hidden, and wait for baseline readiness before pytest.
They preserve separate leg and sampler exits. Logs and sampler data stay under
`work/wp-t4/`. No extra heavy job or N change is launched automatically.

The plan uses the same marker expressions throughout. Turn-5 collection on
`f8b8f4b` replaces the old counts: **5,078** tests in BASELINE, **4,032** in
PARALLEL, **1,046** in SERIAL. Per-round passed/skipped/
failed/xfailed totals must add to BASELINE, with zero PARALLEL failures. Sampled
GPU activity remains a disclosed finding. Final figures must state the actual
start times and conditions: same quiet host, **not a figure of record**.

All nine overwrite refusals were exercised with planted run-log artifacts and
an error-only uv stub, so **no real uv/pytest command could start**. Nine of
nine refused before preflight and preserved the planted bytes; only those
planted files were removed afterwards (`turn4-wrapper-guards.log` plus per-case
logs). The common runner, nine run wrappers and E1 seat wrapper have zero
PowerShell parse errors (`turn4-wrapper-syntax.log`).

| Round / leg | Executed dispatcher wrapper | Exact pytest command (wrapper redirects to its unique log and appends EXIT) |
|---|---|---|
| 1 / baseline | `powershell -NoProfile -File work/wp-t4/run_r4_r1_baseline.ps1` | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r1-baseline-tmp` |
| 1 / parallel | `powershell -NoProfile -File work/wp-t4/run_r4_r1_parallel.ps1` | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r1-parallel-tmp` |
| 1 / serial | `powershell -NoProfile -File work/wp-t4/run_r4_r1_serial.ps1` | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r1-serial-tmp` |
| 2 / baseline | `powershell -NoProfile -File work/wp-t4/run_r4_r2_baseline.ps1` | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r2-baseline-tmp` |
| 2 / parallel | `powershell -NoProfile -File work/wp-t4/run_r4_r2_parallel.ps1` | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r2-parallel-tmp` |
| 2 / serial | `powershell -NoProfile -File work/wp-t4/run_r4_r2_serial.ps1` | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r2-serial-tmp` |

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
all required PARALLEL snapshots must match while the plan remains frozen.

## Turn 5 -- rebased collection and D2 classification

### Rebase, current partition and every changed node ID

Generation 14 rebased onto `ba6e923` so rung 4 measures main's accepted WP3.14
and WP3.20R tests. The four package commits are now `e8f30e5`, `4488d50`,
`a38e680`, `f8b8f4b`; unchanged content/patch-id `525a84c8` is the dispatcher's
reported rebase assertion. Local `turn5-head.log` confirms those commits and
base; `turn5-initial-status.log` is empty. This turn changes only this ledger.

Three sandbox collections on `f8b8f4b` used `QT_QPA_PLATFORM=offscreen`,
`PYTHONPATH=<this worktree>/scripts`, `PYTEST_PLUGINS=sandbox_mkdir_shim`, and
`CUPY_CACHE_DIR=<this worktree>/work/wp-t4/cupy-cache`. Each command was
`uv run pytest --collect-only -q --strict-markers -p sandbox_mkdir_shim
-p no:cacheprovider --basetemp=work/wp-t4/t5-collect-<leg>`, with no marker
expression for all, `-m "not gpu and not footage and not gui and not slow"`
for parallel, and `-m "gpu or footage or gui or slow"` for serial. The shim
and writable CuPy cache are sandbox collection accommodations; the dispatcher's
D2 and measurement windows do not load the shim.

| Collection | Turn-4 after-E1 | Turn-5 current | Added IDs | Removed IDs | Exit / summary |
|---|---|---|---|---|---|
| All | 4889 | 5078 | 193 | 4 | 0; 5078 collected |
| Parallel | 3882 | 4032 | 154 | 4 | 0; 4032/5078, 1046 deselected |
| Serial | 1007 | 1046 | 39 | 0 | 0; 1046/5078, 4032 deselected |

All changed IDs, by file (A+/A- = all added/removed; P and S likewise):

| File under tests/ | A+ | A- | P+ | P- | S+ | S- |
|---|---|---|---|---|---|---|
| test_export_bench.py | 15 | 0 | 15 | 0 | 0 | 0 |
| test_gui_settings_dialog.py | 27 | 0 | 0 | 0 | 27 | 0 |
| test_jobs_batch.py | 4 | 0 | 4 | 0 | 0 | 0 |
| test_jobs_disk_space.py | 9 | 4 | 9 | 4 | 0 | 0 |
| test_jobs_export.py | 88 | 0 | 88 | 0 | 0 | 0 |
| test_jobs_export_photo.py | 18 | 0 | 15 | 0 | 3 | 0 |
| test_jobs_export_video.py | 32 | 0 | 23 | 0 | 9 | 0 |
| TOTAL | 193 | 4 | 154 | 4 | 39 | 0 |

The four removed IDs are all in `tests/test_jobs_disk_space.py`:

- `test_video_estimate_uses_ratio_and_margin[draft-0.25]`
- `test_video_estimate_uses_ratio_and_margin[high-1.0]`
- `test_video_estimate_uses_ratio_and_margin[standard-0.5]`
- `test_video_ten_bit_doubles_only_for_eight_bit_sources`

These are the old disk estimate oracles replaced on main by WP3.14's DR-48
ratio/ceiling rules (source `tests/test_jobs_disk_space.py:25-132`). No other
file removes a node. `test_jobs_export_support.py` contains support only and
adds zero collected IDs. Existing common IDs have **zero partition transfers**.
The new serial IDs consist of 27 GUI settings tests, three GUI photo-statistics
cases, six GPU NVENC video cases, two slow video cases, and one combined
footage/GPU/slow video case: 27+3+6+2+1 = 39. Their own marks already exclude
them from parallel; these are main's additions, not WP-T4 exceptions.

Evidence: `turn5-collect-{all,parallel,serial}.log` (all EXIT=0),
`turn5-{all,parallel,serial}.nodes`, exact corresponding `.added.nodes` /
`.removed.nodes`, and `turn5-collection-accounting.json`. The scratch verifier
compares raw node IDs including literal escapes in parameter names. An initial
path-normalization attempt also changed parameter backslashes and falsely
reported 54 extra replacements; that verifier error was corrected before
accepting any counts. Independent readback in `turn5-account-independent.log`
checks the saved raw sets, count arithmetic and zero existing-node transfers.
No duplicate ID occurs. `turn5-intersection.setdiff` and
`turn5-union-difference.setdiff` are both empty: **4032 + 1046 = 5078**, disjoint
and exhaustive. These counts replace the brief's historical 3762+1006 for the
current tree. **D2's 4031 passed + 1 skipped = 4032** selected IDs, exactly.

### D2 -- zero violators, complete GPU data, diagnostic only

Dispatcher-supplied D2 evidence was read locally: preflight, leg summary,
command/head files, sampler summary and EXIT lines. It ran at the owner's seat
outside the sandbox with no shim on `f8b8f4b`. The heavy-run row below records
its exact times, command, counts and memory. Wall time is **509.1597583 s**;
pytest reports **505.66 s**. The sole skip is the existing swscale/full-range
refusal at `tests/test_color_roundtrip.py:121`; five warnings are not failures.
Leg, sampler and wrapper all EXIT=0. There are **zero failures and zero
violators** from D2, under rung 3's failure-plus-serial-confirmation definition.
No owned or other-package test is changed or newly marked in turn 5.

There are 509 RSS observations, peak summed pytest-tree RSS **7,060,955,136 B**,
minimum available **7,007,793,152 B**, no access-denied reading, no sample below
2 GiB and no remaining child PID. Of 510 real GPU queries, none is unavailable;
GPU complete is true. Two reads are slow; longest **0.938 s**. Maximum RSS
interval is **1.485 s**, GPU observation age **1.359 s**. These successful slow
reads satisfy the corrected instrument policy; neither was fabricated or
silently omitted. Source snapshot SHA matches the unchanged turn-4 sampler.

GPU baseline **0 MiB**, sampled peak **1036 MiB**, sampled rise **1036 MiB**
establish graphics-card activity in the nominal non-GPU leg. D1's +1334 MiB
remains a lower bound because of its gaps. D2 matches the known mechanism:
`tests/test_prototype_backend.py:23` still calls `select_backend("auto")` at
module import, reaching `tools/prototype/backend.py:196-217`, including the
actual CuPy allocation/kernel at line 211. Collection imports modules before
marker deselection, in each worker. The newly added job tests use the CPU
selector double (`tests/test_jobs_export_support.py:55-66,301`), force CPU for
real photo/video/libx265 runs (`test_jobs_export_photo.py:44-47`,
`test_jobs_export_video.py:83-86`), and mark real NVENC cases GPU (`:164,708`).
Export-bench real runs force CPU (`test_export_bench.py:84,122,160,239`);
its sampler-construction assertion at :166-168 does not start an NVENC run.
Static reading identifies no new unmarked GPU execution mechanism in those
added tests. System-wide aggregate memory samples do not prove that the old
import probe is the sole contributor or attribute every MiB. **Finding remains
raised; no marker, product or tools change**. D2 is not a settled round.

### Added-test risks and complete exception list

Static evidence is in `turn5-path-port-static.log`, `turn5-selectors.log`,
`turn5-static-bounds-gpu.log` and the targeted source readings. Added export,
batch, disk-space and benchmark tests keep writable folders under `tmp_path`;
benchmark local config is replaced by a fake config at
`tests/test_export_bench.py:176-178`. Shared generated inputs use the already
locked sample provider. Video session clips/reference caches use each worker's
own `tmp_path_factory` (`test_jobs_export_video.py:154,402`), with sequential
in-worker use. GUI settings locations are under their per-test temporary root
and the whole module is GUI-marked (:44). No fixed-port binding or new shared
writable repository path was identified. This is static evidence and one
passing parallel diagnostic, not a proof against every possible interleaving.

New timing watch finding, for WP3.14's next touch: `tests/test_jobs_export.py`
sets `BLOCK_BOUND_S=3.0` (:39). `test_cancel_releases_a_write_blocked_on_the_encoder`
and its planted counterpart `test_planted_cancel_polled_only_between_frames_hangs_past_the_bound`
use `_blocked_write_cancel` / `_assert_released_within_bound` (:341-391).
`test_a_cancel_during_close_is_aborted_by_the_watchdog_at_every_timing` has
four CLOSE_GATES cases and waits up to the same bound (:427-455). These six
parallel cases all passed D2. They check cancellation responsiveness; no
failure justifies treating them as violators or adding an exception now.
Report the bounds as watch items for the owning package; do not edit or mark
its tests without CHARC's grant. GUI settings' Qt waits are already serial.
The added export-bench tests check arithmetic and relative record relationships,
not E1's tight absolute telemetry-origin bound. No new exception is demonstrated.

Complete WP-T4 exception list (one moved node, no whole file, no xdist_group):

| Test ID | Reason | Remedy / current status |
|---|---|---|
| `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` | timing bound, DR-58 (c); stays serial | Required `@pytest.mark.slow` plus exact reason comment; bound unchanged; strict collection confirms SERIAL |

`tests/test_gui_analysis_service.py::test_pts_and_statistics_never_wait_for_a_run_in_flight`
remains PARALLEL (unmarked GUI module), confirmed again by turn-5 sets; it
passed D2. No fresh failure or exception is claimed. The previous E1 serial
sandbox failure is not erased by D2 because E1 was deselected from D2; no
quiet-seat E1 result has been supplied yet. New WP3.14/WP3.20R violations,
if later demonstrated, are findings for those packages' next touch, never
in-envelope code changes by this cell (CHARC's binding condition).

### Wrappers and measurement readiness

No runner or sampler was edited in this turn. All nine fixed wrapper files
match the turn-4 templates exactly. Comparing `run_r4.ps1` to the successfully
executed `run_turn5_diag.ps1` yields only its stated diagnostic header and
evidence-prefix substitutions; executable logic is otherwise identical.
`turn5-wrapper-check.log` records this comparison, 9/9 template matches,
zero existing rung-4 log artifacts and the unchanged sampler SHA. Current
byte hashes of the common runner, nine wrappers and sampler are retained in
`turn5-wrapper-hashes.json`. All ten PowerShell runner files parse with **zero
errors** (`turn5-wrapper-syntax.log`). The prior dynamic overwrite-refusal
proof (9/9) remains in `turn4-wrapper-guards.log`; it was not rerun as a suite.
Readback confirms >=5 GiB preflight, refusal of every existing evidence/temp
path, and sampler snapshot/hash/readiness beside every PARALLEL run. D2 used
that same runner logic with its unique prefix. No R4 evidence was overwritten.
The six active RUN REQUESTS are in the active table above. R3 wrappers are
retained solely for Q7's conditional third round; D2 never substitutes for r1.

### Turn-5 verification loop

| ID | Severity / class | Suspected / confirmed / rejected evidence | Disposition |
|---|---|---|---|
| T5-1 | Verification, collection accounting | 193 added / 4 removed IDs; per-file table and raw sets; no existing transfers; D2 matches 4032 | Confirmed; replace active count expectations with 4032+1046=5078 |
| T5-2 | Minor, scratch verifier only | Path normalization altered parameter escapes and invented 54 ID replacements | Confirmed verifier defect; fixed before accepting proof, independently rechecked raw sets |
| T5-3 | Verification, D2 classification | 4031 passed / 1 skipped / zero failures; all three exits 0 | Confirmed zero violators; diagnostic only, not a round |
| T5-4 | Major nominal, marker/collection finding outside scope | Complete GPU series rises 1036 MiB; old import probe still present; new job paths CPU or GPU-marked | Confirmed sampled rise; sole attribution unproved; raised, no fix or new marker |
| T5-5 | Minor nominal, other-package timing watch | Six added WP3.14 cancellation cases use a three-second bound; all passed D2 | Risk identified; no confirmed violator/exception; report for next touch, no edit |
| T5-6 | Verification, measurement readiness | 9/9 wrapper templates; common runner matches diagnostic copy except header/prefix; 10 parsers clean; sampler hash unchanged | Confirmed; six r1/r2 windows requested, r3 conditional only |

No tests were executed by the cell in turn 5: three collections and static
checks only. No final-suite-green, completed measurement, median, review-round
or package-completion claim is made. Final turn-5 evidence checks are recorded
in `turn5-final-check.log`; handoff remains pending actual dispatcher windows.

## Turn 6 -- rung 4 measured, report and Reviewer A handoff

### Session and evidence provenance

Generation 14 accepted turn 5 as `dd49a15`, ledger only, and supplied
**depth_input_tokens 95,253**. CHARC's session ruling is recorded at the top:
a fresh session was optional, this one continues because rungs 1-3 are already
in context. The old RESUME HERE checklist was followed in this session.
`turn6-collection-head.txt` confirms marker collection ran on `dd49a15`, before
this turn's conftest docstring edit. The source/package diff base is `ba6e923`.

The dispatcher performed all six r1/r2 windows and D3. Cell readback decoded
PowerShell UTF-16 logs, verified summary AND EXIT plus recorded command/head/
free-before data, and parsed UTF-8 sampler JSONL. `turn6-run-data.json` and
`turn6-run-readback.log` preserve the extracted values. The prompt's summary
was a cross-check, not the measurement source. This matters at rounding: r1
P+S is 3832.6676705 s, hence **3832.67** rounded, not the prompt's 3832.66.
No heavy run or test execution was performed by the cell in turn 6; only four
marker collections, file parsing/static checks and gates.

### Count reconciliation, times, saving and N=4

For BOTH rounds independently: **4031+1036=5067 passed; 1+10=11 skipped**;
failed/errors/xfailed/xpassed all **0+0=0**. Selected totals are
**4032+1046=5078**. All six leg exits, two sampler exits and wrapper exits are
zero. Head files all record `dd49a15d4659f2eb42acee24e5f3eac4e1c05272`.
Commands, individual start/end times, N, counts, free-before, wall seconds and
parallel memory/GPU completeness are in the heavy-run table below. Per-run
pytest elapsed strings are retained in readback JSON; figures use wrapper wall.

| Round | BASELINE s | PARALLEL s | SERIAL s | P+S s | Saving s | Saving % | SERIAL / BASELINE |
|---|---|---|---|---|---|---|---|
| 1 | 4564.80 | 497.30 | 3335.36 | 3832.67 | 732.13 | 16.04% | 73.07% |
| 2 | 4349.92 | 493.54 | 3372.59 | 3866.13 | 483.78 | 11.12% | 77.53% |
| Median | 4457.36 | 495.42 | 3353.98 | 3849.40 | retain per-round figures | retain per-round figures | retain per-round figures |

Savings differ by **248.3433344 s / 4.9168798 percentage points**. BASELINE
fell **4.7072446%** (r1 denominator), while P+S rose only **0.8732105%**
(r1 denominator) / **0.8656515%** (r2 denominator), an absolute **33.4672558 s**.
This baseline drift is disclosed, not averaged into one savings claim. No
third round is required under Q7; D3 is never a threshold input. Same quiet
host; **not a figure of record**. The serial set bounds the speedup: SERIAL
is 73.07% / 77.53% of BASELINE. Offscreen gui and slow cases without a device
are possible owner follow-ons by caution, never marker changes in WP-T4.

Every free-before reading is >=5 GiB. Across required parallel windows, peak
summed pytest-tree RSS is **6,967,926,784 B (6.49 GiB)** and minimum available
**7,047,557,120 B (6.56 GiB)**, comfortably above 2 GiB. N=4 is AD-28's cap,
not a guessed optimum; measured whole-suite saving of 11.12-16.04% and those
memory observations justify the chosen cap on this host. No N=2 or N>4 run
was performed. R1/r2 have 498/494 RSS samples, 499/495 GPU queries and no gaps,
access-denied RSS, <2 GiB samples or remaining child PID. Both sampler copies
match SHA `64a57c731a09a7eca1e4c6f5b882975888ca0233434cc02b2c69e0dbc7ee0854`.
Independent `turn6-sample-verification.log` recomputes maxima/minima and query
counts from raw rows, verifies floor/access/error flags and snapshot bytes.

### D3 serial breakdown, overlap and privacy

D3 is a separate diagnostic, with explicit dispatcher/CHARC approval; not a
round and never included in medians or the 15-percent rule. Its exact command,
start/end, wall and free-before are in the heavy-run row. `d3-serial.log`
EXIT=0; 1036 passed, 10 skipped, 4032 deselected. JUnit has exactly the same
1046 unique IDs as the serial collection, with no failure/error testcase.

Four collections on dd49a15 use `uv run pytest --collect-only -q
--strict-markers -p sandbox_mkdir_shim -p no:cacheprovider
--basetemp=work/wp-t4/t6-collect-<marker> -m <marker>` for gpu, footage, gui and
slow, all EXIT=0. Sandbox env: QT_QPA_PLATFORM=offscreen, absolute worktree
scripts in PYTHONPATH, PYTEST_PLUGINS=sandbox_mkdir_shim, and work-local
CUPY_CACHE_DIR. Exact marker IDs are `turn6-{gpu,footage,gui,slow}.nodes`.
JUnit classname/name keys map one-to-one to raw IDs, including parameters
and classes. Every marker union ID appears in D3 and vice versa. JUnit's
configured/default total time includes setup, call and teardown.

| Marker | IDs (skipped) | Sum of JUnit testcase seconds |
|---|---|---|
| gpu | 586 (4) | 1843.366 |
| footage | 17 (1) | 2001.211 |
| gui | 441 (0) | 67.769 |
| slow | 20 (5) | 2931.947 |
| Of which in two or more markers (counted once here) | 13 | 2011.870 |
| De-duplicated SERIAL total | 1046 (10) | 3326.963 |

The 13 overlapping cases are **8 two-marker and 5 three-marker** cases.
Marker rows sum to **6844.293 s** and repeat **3517.330 s** of memberships;
unique time is **3326.963 s**. The overlap line itself counts each overlapping
case once (2011.870 s), so subtracting it once from marker rows is incorrect.
D3 wall **3331.3104851 s** minus de-duplicated cases leaves **4.3474851 s
(0.13050375%)**. This is unassigned launch/collection/session-hook/reporting/
teardown overhead plus timing precision, not an extra independently timed
fixture bucket. Test-attributed module/session fixture times are already
inside JUnit cases. `turn6-analysis.json` and its log hold exact arithmetic.

| Rank / node ID | Markers | JUnit total s | Setup s | Call s | Teardown s | Cost |
|---|---|---|---|---|---|---|
| 1. `tests/test_jobs_export_video.py::test_v4_synthetic_5k3_8_7_clip` | slow | 870.740 | 0.01 | 870.73 | <0.005 (hidden) | Body |
| 2. `tests/test_jobs_export_video.py::test_gx011627_through_the_engine_keeps_every_mandatory_and_required_item` | gpu, footage, slow | 725.154 | <0.005 (hidden) | 725.15 | <0.005 (hidden) | Body |
| 3. `tests/test_io_video_encode.py::test_gx011627_nvenc_levels_give_distinct_sizes` | gpu, footage, slow | 472.503 | <0.005 (hidden) | 472.50 | <0.005 (hidden) | Body |
| 4. `tests/test_io_video_encode.py::test_gx011627_through_the_sink_keeps_every_mandatory_and_required_item` | gpu, footage, slow | 207.834 | 0.01 | 207.83 | <0.005 (hidden) | Body |
| 5. `tests/test_color_roundtrip.py::test_pair_round_trip_on_the_owners_main_case` | footage, slow | 161.405 | 0.01 | 161.40 | <0.005 (hidden) | Body |
| 6. `tests/test_io_video_decode_hw.py::test_the_real_clip_decodes_to_its_pts_and_the_reference_bytes` | footage, slow | 140.412 | 41.90 | 98.51 | <0.005 (hidden) | Body + module-fixture setup |
| 7. `tests/test_io_video_decode_hw.py::test_the_real_clip_through_the_forced_default_pipe_is_identical` | footage, slow | 126.265 | <0.005 (hidden) | 126.26 | <0.005 (hidden) | Body |
| 8. `tests/test_io_video_decode_hw.py::test_the_real_clip_through_cuda_decode_is_identical` | gpu, footage, slow | 94.030 | <0.005 (hidden) | 94.03 | <0.005 (hidden) | Body |
| 9. `tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory` | gpu | 59.999 | <0.005 (hidden) | 60.00 | <0.005 (hidden) | Body |
| 10. `tests/test_prototype_clip.py::test_bench_whole_clip_modes_record_their_pass` | gpu | 58.139 | 0.01 | 58.13 | <0.005 (hidden) | Body |

All ten are dominated by call/body cost. Case 6 also includes **41.90 s setup**
from the phase log, associated with the first use of module-scoped footage
and reference fixtures (`tests/test_io_video_decode_hw.py:75-107`), including
independent FFmpeg hash generation. Fixture-scope/placement is an owner question;
the fixture is already module-scoped, not repeatedly rebuilt per case. Its
98.51 s call remains body cost. The other top setups are <=0.01 s and all top
teardowns are hidden below 0.005 s. `--durations=0` still hides those phases
without -vv; do not invent zero/exact values or infer precision beyond the
printed two decimals. JUnit totals have three decimals, so rounded phase
sums need not match exactly. No new heavy -vv rerun was requested.

`turn6-privacy-check.log` EXIT=0: the ten node IDs fit an ASCII test-name
grammar and contain no absolute path, coordinates or location tokens. The
only embedded clip name is gx011627, confirmed already in committed reports
by `git grep -i gx011627 HEAD -- docs/reports`. The report has no hostname,
absolute footage path or raw XML. JUnit and the full durations text stay only
under work; only requested aggregate tables, ten IDs and phase values are
copied. No new footage-derived output, image, location or metadata is committed.

### E1 closure, environment skips and GPU finding

The initial sandbox E1 timing failure remains historical evidence, with its
bound untouched. `turn6-scope-e1.log` independently confirms E1 membership in
all/serial, four exhaustive green quiet-seat outcomes and complete skip lists
that exclude E1. The quiet -q logs contain no individual PASS line: the proof
uses their totals and complete skips, not a fabricated per-node line. D3
explicitly has a passing E1 testcase (19.306 s) and a 19.30 s call duration.
**T4-4 is resolved by quiet-seat results; no bound relaxation, skip or fix.**

Nine of eleven BASELINE skips are missing look-check frames under ignored
work/wp1.3, at test_methods_assembly_v8.py:44. The other two are the known
swscale/full-range refusal and no-photo skip (test_color_roundtrip.py:121,
test_photo_check.py:139). Parallel has the first, serial the other ten; both
rounds and D3 agree. Dispatcher says main has the look-check frames and shows
two skips; the cell did not run main or copy footage-derived frames. This
worktree's measurement retains and discloses the nine environment skips.

The raised GPU activity reproduces with complete series in D2/r1/r2 at peaks
**1036/1037/1049 MiB**, rises **1036/903/911 MiB**, baselines **0/134/138 MiB**.
The traced mechanism remains module import at test_prototype_backend.py:23,
select_backend -> _probe_gpu -> CuPy allocation/kernel at prototype/backend.py:211,
before marker deselection in each worker. New job CPU paths/GPU marks are
unchanged. System-wide samples do not exclusively attribute every MiB to that
probe. **Finding remains raised; marker meaning is out of scope.** No new
violator or exception was found; E1 remains the only WP-T4 moved node.

### Q2, report and static gates

Q2 adds ONE module-docstring paragraph to tests/conftest.py describing the
controller-first order and derived popen-gwN child root, with installed xdist
source anchors. `turn6-conftest-ast.log` EXIT=0 compares `ast.dump` of each
module after removing its module-docstring node; results are identical, SHA
`ccb362b5189b7daa23d6a3e65d7291f6d92f69fd1a655ea4e6c358d7c09de23e`.
The removed/added docstring text differs by exactly the one paragraph. No
executable guard or other product/interface/tool code changed in turn 6.

NEW docs/reports/wp-t4-parallel-tests.md contains claims and limits, dependency
MIT quotations and lock check, current partition/rebase accounting, guard
source/positive control, deterministic cache red/green and lock policy,
complete exception/violator list, figures/medians/saving spread/N rationale,
D3 breakdown/top ten/privacy, resolved E1 and raised GPU findings, and exact
executed commands plus proposed gate replacement/CLAUDE pointer. Neither the
fill nor CLAUDE.md is edited; docs/testing.md is not created. The dispatcher
owns those accept-time edits. No deviation beyond recorded sandbox collection
accommodations and the explicitly superseded round/session choices is hidden.

Static gates on final Python content all EXIT=0: **ruff check passes; ruff
format reports 238 files already formatted; mypy finds no issues in 136 source
files**. Logs: turn6-ruff-check.log, turn6-ruff-format.log, turn6-mypy.log.
UV warns it ignores the inherited VIRTUAL_ENV in favor of this project's
.venv; that warning is not a failing check. Only report/ledger documentation
is updated after those checks; final verification rechecks the AST/scope and
static gate result files. `git diff --check` and final evidence checks are
recorded in turn6-final-check.log. Final two-leg gates remain pending Reviewer A.

### Turn-6 verification loop

| ID | Severity / class | Confirmed / rejected evidence | Disposition |
|---|---|---|---|
| T6-1 | Verification, figure provenance / counts | Six logs and command/head/free files read; raw sampler extrema recomputed; both outcomes add | Confirmed measured r1/r2 only; no third; per-round saving retained |
| T6-2 | Minor nominal, serial-set follow-on outside scope | D3 1046 cases map exactly; marker sums/weighted overlap reconcile; serial is 73-77% of baseline | Raised owner follow-on; no marker or body/fixture change |
| T6-3 | Verification, phase precision / fixture attribution | Durations hide <0.005 phases and round others; 41.90 setup appears on module-fixture first use | Hidden values disclosed, not invented; separate fixture/body costs |
| T6-4 | Verification, resolved historical T4-4 | Quiet-seat B/S r1/r2 have no E1 skip/failure; D3 JUnit explicit pass | CLOSED by quiet-seat results; unchanged bound |
| T6-5 | Major nominal, existing GPU/marker finding outside scope | Complete D2/r1/r2 peaks 1036/1037/1049; traced import mechanism remains | Raised; no fix, marker meaning out of scope |
| T6-6 | Verification, docstring-only ownership | AST minus module docstring identical; exact one-paragraph delta | Confirmed Q2 within envelope |
| T6-7 | Verification, report privacy / gates | ASCII/location checks and prior committed clip name; static gates all 0 | Confirmed; ready for driver-owned Reviewer A, no final-gate claim |

## Turn 7 -- Reviewer A round 1 and single cleanup

### Reviewer provenance, assertions and terminal policy

Generation 14 accepted turn 6 as `5e6a8d3`, with zero CR bytes, and supplied
**depth_input_tokens 152,531**. This session continues under CHARC's already
recorded choice. Package base remains `ba6e923`. Reviewer A ran on `5e6a8d3`
via `codex_cell.py review`, `claude -p --model opus --effort high`, read-only.
The permitted review file was read in full; its MD5 is locally verified as
**f6626815a4690d9a752465ad1afec7fe** (`turn7-review-md5.log`). Evidence is the
external driver-owned `wp-t4/r1/review.txt`; nothing is written there by the
cell and no withheld folder is read/listed by the cell.

Dispatcher-reported transport assertions: modelUsage **claude-opus-5-5**;
high effort by invocation; is_error false; 63 turns; worktree clean afterwards;
one anchored VERDICT line; all findings labelled EXECUTED or REASONED. Twelve
permission denials were the reviewer's own scratch writes, redirects and git
show-to-file attempts refused by read-only policy, none touching a withheld
path. They are execution limitations, not test failures or unclassified denials.
The brief's FAST tier mentions Sonnet medium, but FINAL Q6 / the driver model
check / RESUME HERE pin **Opus high**. The dispatcher ran that stronger tier,
never less rigor; no improvised Sonnet invocation was used.

Verdict: **VERDICT: NO_NEW_CRITICAL_MAJOR**. All seven CLAIMS_FIRST checks
hold. Reviewer executed complementary collections, exact lock/dependency/MIT
and marker checks; **4 lock tests passed** and **60 guard tests passed under
-n 2** (including nested worker execution), and checked installed source
anchors. Sharing and arithmetic findings are reasoned/static as labelled.
**Zero new blocking terminates the loop per the fill. No round 2.** This is
the one cleanup allowed by CHARC's recommended one-round-plus-cleanup cap.
No clean second round, overall acceptance or Reviewer B verdict is claimed.

### Every finding adjudicated

All eleven findings are **NEW**, none REOPENED. Accepted severity: six Minor,
five Advisory; zero Critical/Major. In/out classification below refers to
WP-T4's fix envelope: ten are in-envelope documentation/limit dispositions;
a3's test changes would be outside the owned fix envelope (watch/report only).
Optional code changes for m2/a2 were deliberately not taken: no test/plugin
or product code changes, no added tests, and the 180 s / 900 s rules remain.

| ID | Accepted severity | Review evidence / cell confirmation | State | Envelope | Disposition |
|---|---|---|---|---|---|
| m1 | Minor | REASONED in review; now EXECUTED: byte-exact base plugin plus byte-identical committed race test fails at line 132 all-ok assertion; turn7-m1-red.log EXIT=1 | NEW | In, report accuracy | FIXED: report cites 132 and distinguishes historical pre-commit variant's 131; red/green both logged |
| m2 | Minor | REASONED; lock helper's 180 s wait / 900 s stale path and error strings confirm hard-kill residue and omitted PID/age | NEW | In, recovery limit | LIMIT recorded: killed-owner lock requires owner-confirmed cleanup; PID/age not printed; optional diagnostics/liveness not added; thresholds unchanged |
| m3 | Minor | REASONED; sampler is uncommitted scratch and xdist -q summary omits deselected count; new three collections and raw sets confirm runnable check inputs | NEW | In, gate text | FIXED: optional where-sampler-available floor, explicit all/P/S collect commands, duplicate/intersection/union/count and outcome requirements using committed pytest/psutil |
| m4 | Minor | EXECUTED grep plus cell AST confirms three top-level calls at backend:23, clip:41, temporal:47; turn7-collection-probe-proof.log | NEW | In, report attribution; marker fix out of scope | FIXED: name all three probes, keep GPU finding raised; no marker/tool change |
| m5 | Minor | EXECUTED reading: w2/w3 controller refuses before workers; w4 records registration/root; local popen root is a fresh guarded controller child | NEW | In, coverage statement | LIMIT recorded: independent worker refusal is untested and worker-only unsafe root unreachable in envelope; report no longer claims it is tested; no planted out-of-envelope test |
| m6 | Minor | REASONED; measured commands include basetemp while old quoted gate sentence omitted it | NEW | In, gate text | FIXED: quoted executions AND collections require separate fresh work/ roots, concrete RUN-labelled commands |
| a1 | Advisory | REASONED; ready readers hold no read lease while two transient verification failures can trigger in-place regeneration | NEW | In, concurrency limit | LIMIT recorded: rare unlocked-reader/rewrite hazard; disposition only, no publication or reader-lifetime change |
| a2 | Advisory | REASONED; finally lock.unlink can raise FileNotFoundError after incorrect live-holder deletion and mask prior result | NEW | In, recovery limit | LIMIT recorded: cleanup only after confirming stopped owner; optional tolerant unlink not added |
| a3 | Advisory | REASONED; unmarked GUI service <0.2 s and WP3.14 three-second cancellation bounds remain parallel and passed measured rounds | NEW | Out for test edits; watch/report allowed | LIMIT / WATCH for owning packages' next touch; no edits or marks |
| a4 | Advisory | REASONED; race regression also passes safe re-verify-under-lock / final-verify-outside variant | NEW | In, regression coverage limit | LIMIT recorded: test pins observed one-generation safety, not lexical final-verify lock scope; disposition only |
| a5 | Advisory | REASONED; release relies on Windows 11 NTFS POSIX-style delete while waiter stat may hold a handle | NEW | In, declared operating envelope | LIMIT recorded: older delete-pending filesystem PermissionError behavior not supported; no portability promise or code change |

Cumulative disposition counts: **4 FIXED documentation findings (m1,m3,m4,m6)**,
**7 LIMIT/WATCH**; 11 adjudicated, zero unclassified. No revert; product-code
fixes 0, test-code fixes 0, docs finding fixes 4 across report/ledger. m5's
coverage wording is corrected while the absent independent refusal remains an
explicit limit. A limit is not counted as a secretly fixed code issue.

### m1 re-established red and current green

`turn7_stage_red.py` writes only under work/wp-t4/turn7-unlocked. Staged
fixture_plugin.py is byte-for-byte `ba6e923:tests/fixture_plugin.py`, SHA-256
`6c82e2734ab0e60aae856d357d2426ec8b42b05b0e6500974c32f0788821f2db`.
The staged test copy is byte-identical to the committed test, SHA-256
`0466cddc286173a8be1d26aff50e0d6dcd7ce663833ca3de8cdbcf5294cd2361`;
its manifest is copied into the fake repository. No tracked plugin is swapped
or edited, no real generated cache is deleted or read, and no footage is used.

Sandbox red command: `uv run pytest -q -rs -p sandbox_mkdir_shim
-p no:cacheprovider -p fixture_plugin --basetemp=work/wp-t4/t7-m1-red
work/wp-t4/turn7-unlocked/tests/test_fixture_cache_lock.py::test_two_processes_share_one_verified_cold_cache_generation`.
PYTHONPATH puts that scratch tests directory before the worktree scripts/tools;
PYTEST_PLUGINS=sandbox_mkdir_shim propagates to child pytest where needed.
Red is **1 failed, EXIT=1 at line 132**,
`assert all(record["ok"] for record in result["records"]), result`.
Both spawned exit codes are 0, two result records exist, two writers generate,
and one record contains the real partial Matroska stream verification failure.
This is the required assertion failure, not import, fixture setup or a timeout.

The historical `turn3-regression-red.log` really reports the all-ok assertion
at 131, whereas the committed file has len(records)==2 at 131 and all-ok at
132. That old run used an earlier pre-commit variant; its exact old bytes are
not retained, so no unsupported claim about the reason for the offset is made.
The report's carry-forward citation was wrong for the committed test and is
corrected. Scratch staging hashes and line readback are in turn7-m1-stage.log.

With normal scripts-only sandbox PYTHONPATH restored, the current committed
file ran `uv run pytest -q -rs -p sandbox_mkdir_shim -p no:cacheprovider
--basetemp=work/wp-t4/t7-lock-green tests/test_fixture_cache_lock.py`:
**4 passed in 11.29 s**, EXIT=0 (`turn7-lock-green.log`). No code change or
rerun of a heavy leg was needed. There are no changed test files this turn;
report and ledger are the only owned changes.

### Figure ruling and cleanup scope

CHARC `144f9735`: suite saving is P+S versus BASELINE of the SAME round:
**-16.0% / -11.1%**, spread **4.9 percentage points**; baseline moved **4.7%**
while P+S moved under **1%**. Median P+S **3849.40 s / 64.16 min** is the
one-line accept-time CLAUDE Conventions figure (about 3849 s, 64 min).
PARALLEL is stable/fast **493.54-497.30 s**; SERIAL is the floor
**3335.36-3372.59 s**. The report now calls these same-quiet-host **suite
wall-time figures**, NOT N6/V16 product timing figures. Product timing and
memory figures are obtained serially in their own windows. This supersedes
the broader historical "not a figure of record" strings without editing old
measurement logs or pretending those records were originally worded otherwise.

The proposed quoted gate sentence now includes fresh work/ basetemps for both
execution legs, all three explicit collection commands, raw node filtering and
duplicate/disjoint/union/count/outcome arithmetic, plus available-memory
preflight via committed psutil. Sampling below 2 GiB is conditional **where a
sampler is available**; no uncommitted helper becomes a future gate dependency.
The per-test tmp_path / slow-with-reason rule and product figures-from-serial
rule remain. CLAUDE pointer carries the median suite figure; actual fill and
CLAUDE files remain untouched. No docs/testing.md, dependency or code change.

All three verified module-import GPU probes are named; GPU activity remains
raised and marker meaning out of scope. m5 records controller-level refusal
versus worker registration/static order precisely. Lock recovery/reader/
regression/Windows 11 NTFS delete limits are explicit, with unchanged rules.
Other-package timing bounds stay WATCH. Four largest export CALL phases sum
to **2276.21 s / about 68.3% of D3 wall**; their size is the follow-on lever.
CHARC owns D3's register row at accept; this report does not claim it exists.

### Cleanup checks and final two-leg request

All three strict collections EXIT=0: **5078 / 4032 / 1046**. Saved raw node
sets `turn7-{all,parallel,serial}.nodes` equal turn-5 sets exactly (literal
parameter escapes preserved); no duplicates, empty intersection and union
symmetric difference. `turn7-collection-probe-proof.log` confirms the count
and all three top-level GPU-probe line anchors. Thus the docs-only cleanup
introduces no new test ID, exception, marker or test behavior.

Scratch `run_final.ps1` copies run_r4.ps1's protocol with only final-prefix,
header and conditions wording substitutions; `run_final_parallel.ps1` and
`run_final_serial.ps1` are the two entrypoints. They refuse every existing
artifact/basetemp, enforce >=5 GiB available before each leg, record actual
committed HEAD/command/conditions/start/end/wall/EXIT, and snapshot/hash/start
the sampler beside PARALLEL with readiness and separate exits. Prefixes are
work/wp-t4/final-parallel and final-serial, with matching -tmp roots. No final
leg has run. Two planted existing-log refusals preserved bytes and called no
real uv (an error-only uv stub made heavy execution impossible), then removed
only the planted worktree files. Three files parse with zero PowerShell errors;
turn7-final-wrapper-refusals.log / -syntax.log / -hashes.json record the checks.
Sampler remains SHA 64a57c731a09a7eca1e4c6f5b882975888ca0233434cc02b2c69e0dbc7ee0854.

Turn-7 static gates all EXIT=0: `uv run ruff check .` passes; `uv run ruff
format --check .` reports **238 files already formatted**; `uv run mypy`
reports **no issues in 136 source files**. Logs: turn7-ruff-check.log,
turn7-ruff-format.log, turn7-mypy.log. Only documentation changes in this turn;
no changed executable/test file needs a new per-file suite. The four current
lock tests ran green for m1 and all three strict collections ran green.
Final scope/raw-set/probe/Markdown/privacy/runner checks and git diff --check
are recorded in turn7-final-check.log. No final heavy-leg result is claimed.

Final RUN REQUEST, one window at a time after the dispatcher commits this
cleanup (wrappers record that actual HEAD; they do not pin 5e6a8d3):

1. `powershell -NoProfile -File work/wp-t4/run_final_parallel.ps1`
   runs `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/final-parallel-tmp`
   to final-parallel.log with parallel sampler evidence under that prefix.
2. `powershell -NoProfile -File work/wp-t4/run_final_serial.ps1`
   runs `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/final-serial-tmp`
   to final-serial.log. Both append EXIT and refuse evidence reuse.

No BASELINE, r3 or review round 2 is requested. Final gates are not yet
claimed green; Reviewer B/accept remain driver/CHARC work.

## Heavy-run ledger

The dispatcher ran D1, D2, both settled rounds and D3. D1/D2/D3 are
diagnostic only, not rounds. R1/R2 are the only measured rounds; all six
windows and D3 ran on `dd49a15`, outside the sandbox without the shim, in
quiet windows acknowledged by CHARC. No heavy leg was executed by the cell.

| Run / head | Start UTC | End UTC | Command / log under work/wp-t4 | N | Counts | Leg / sampler / wrapper exit | Free before | Peak summed RSS | Minimum available | GPU / qualification |
|---|---|---|---|---|---|---|---|---|---|---|
| D1 diagnostic / `6ac384a`, before E1 | 2026-10-27 08:51:03.9259564Z | 2026-10-27 08:57:03.4570794Z | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/t3-parallel-01`; `turn3-parallel-01.log` | 4 | 3882 passed, 1 skipped, 0 failed, 0 xfailed; 5 warnings | 0 / 4 / 4 | 11.899719 GiB | 6,821,711,872 B | 6,184,673,280 B | Baseline 123 MiB, observed peak 1457 MiB, rise 1334 MiB; 5/360 GPU gaps; diagnostic only |
| D2 diagnostic / `f8b8f4b`, base `ba6e923`, after E1 | 2026-10-27 18:50:09.8062115Z | 2026-10-27 18:58:38.9712187Z | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/turn5-diag-parallel-tmp`; `turn5-diag-parallel.log` | 4 | 4031 passed, 1 skipped, 0 failed, 0 xfailed; 5 warnings | 0 / 0 / 0 | 12.59000015258789 GiB | 7,060,955,136 B | 7,007,793,152 B | Baseline 0 MiB, peak 1036 MiB, rise 1036 MiB; 510 queries, zero unavailable; diagnostic only, not a round |
| R1 baseline / `dd49a15` | 2026-10-27T19:09:09.9423940Z | 2026-10-27T20:25:14.7409654Z | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r1-baseline-tmp`; `r4-r1-baseline.log`; wall 4564.7952512 s | 1 | 5067 passed, 11 skipped, 0 failed, 0 xfailed | 0 / N/A / 0 | 12.454143524 GiB | not sampled | not sampled | not sampled |
| R1 parallel / `dd49a15` | 2026-10-27T20:25:16.5545092Z | 2026-10-27T20:33:33.8627916Z | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r1-parallel-tmp`; `r4-r1-parallel.log`; wall 497.3035847 s | 4 | 4031 passed, 1 skipped, 0 failed, 0 xfailed | 0 / 0 / 0 | 12.627063751 GiB | 6,967,926,784 B | 7,047,557,120 B | Complete; 499 queries; baseline 134, peak 1037, rise 903 MiB; zero gaps |
| R1 serial / `dd49a15` | 2026-10-27T20:33:35.5773853Z | 2026-10-27T21:29:10.9443000Z | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r1-serial-tmp`; `r4-r1-serial.log`; wall 3335.3640858 s | 1 | 1036 passed, 10 skipped, 0 failed, 0 xfailed | 0 / N/A / 0 | 12.748401642 GiB | not sampled | not sampled | not sampled |
| R2 baseline / `dd49a15` | 2026-10-27T21:30:32.8419642Z | 2026-10-27T22:43:02.7659107Z | `uv run pytest -q -rs --basetemp=work/wp-t4/r4-r2-baseline-tmp`; `r4-r2-baseline.log`; wall 4349.9191726 s | 1 | 5067 passed, 11 skipped, 0 failed, 0 xfailed | 0 / N/A / 0 | 12.545288086 GiB | not sampled | not sampled | not sampled |
| R2 parallel / `dd49a15` | 2026-10-27T22:43:03.8385947Z | 2026-10-27T22:51:17.3838295Z | `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp-t4/r4-r2-parallel-tmp`; `r4-r2-parallel.log`; wall 493.5412374 s | 4 | 4031 passed, 1 skipped, 0 failed, 0 xfailed | 0 / 0 / 0 | 12.853286743 GiB | 6,854,651,904 B | 7,504,404,480 B | Complete; 495 queries; baseline 138, peak 1049, rise 911 MiB; zero gaps |
| R2 serial / `dd49a15` | 2026-10-27T22:51:18.9534591Z | 2026-10-27T23:47:31.5505229Z | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp-t4/r4-r2-serial-tmp`; `r4-r2-serial.log`; wall 3372.5936889 s | 1 | 1036 passed, 10 skipped, 0 failed, 0 xfailed | 0 / N/A / 0 | 12.952400208 GiB | not sampled | not sampled | not sampled |
| D3 diagnostic SERIAL / `dd49a15`, not a round | 2026-10-27T23:47:41.3884587Z | 2026-10-28T00:43:12.7028183Z | `uv run pytest -q -rs -m "gpu or footage or gui or slow" --durations=0 --junitxml=work/wp-t4/d3-serial-junit.xml --basetemp=work/wp-t4/d3-serial-tmp`; `d3-serial.log`; wall 3331.3104851 s | 1 | 1036 passed, 10 skipped, 0 failed, 0 xfailed; 4032 deselected | 0 / N/A / 0 | 12.675758362 GiB | not sampled | not sampled | not sampled; diagnostic only |

D1 wall time: **359.5270566 seconds** (pytest's own duration 358.33 seconds).
Its 360 RSS samples have no access-denied reading, no <2 GiB sample and no
remaining child PID. Rung-4 rows above come from actual window files,
including per-round counts, frozen HEAD and sampler hashes; none is estimated.

## Cumulative review-round ledger

| Round | Critical / major / minor / advisory | In / out of fix envelope | NEW / REOPENED | Reverts | Product / test-code / docs finding fixes | Reviewer transport / version | Dispatcher-read depth | Disposition |
|---|---|---|---|---|---|---|---|---|
| A1 | 0 / 0 / 6 / 5 | 10 / 1 (a3 watch; test edits not owned) | 11 / 0 | 0 | 0 / 0 / 4 | codex_cell.py review; Claude Opus high; modelUsage claude-opus-5-5; driver assertions above | Turn 6 depth_input_tokens 152,531; turn 7 pending | NO_NEW_CRITICAL_MAJOR; all seven claims hold; zero new blocking terminates; one cleanup, no A2 |

Cumulative: eleven findings adjudicated, four documentation fixes and seven
limits/watch dispositions; no unclassified issue, reopening or revert. The
transport's twelve denials are classified read-only scratch-write refusals,
not findings against product code. Reviewer B remains pending at the driver.

## RESUME HERE -- final two legs, then Reviewer B and accept

1. Latest supplied depth: turn 6 **152,531 input tokens**; record turn 7's next
   driver-read figure without estimating it. This session continues by CHARC
   choice. Package base `ba6e923`; A1 reviewed `5e6a8d3`; turn 7 changes only
   report/ledger. Dispatcher commits; cell never writes .git or a mailbox.
2. Reviewer A **TERMINATED after round 1**, zero new blocking, seven claims
   hold. All m1-m6/a1-a5 are adjudicated above: 4 docs fixes, 7 recorded
   limits/watch items. This is the single cleanup; **do not request A round 2**.
   Record the distinction between accepted suite wall-time figures and N6/V16
   product figures (serial in their own windows). No source/test/plugin code
   changed in cleanup; report records actual committed-red line 132.
3. **Next: final PARALLEL then SERIAL** using run_final_parallel.ps1 and
   run_final_serial.ps1, after committing cleanup, one dispatcher-granted
   quiet window each, outside sandbox without shim. Fresh final-* evidence
   names, >=5 GiB preflight, unchanged sampler beside parallel. No BASELINE,
   no r3 (measured drift <1%), no N change. D1/D2/D3 never become rounds.
4. Read final head/command/free/start/end/wall/EXIT and parallel sampler data;
   confirm same committed head, both legs green, 4032+1046=5078 collection and
   expected counts/skips (or explicitly account for any authorized change).
   Preserve the measured r1/r2 figures as the suite record; final gate legs
   are acceptance checks, not replacement rounds. Stop/report if sampled
   available memory <2 GiB; do not lower N. Keep GPU finding and all limits.
5. After final gates, deliver the return/report update with actual outcomes,
   reviewer A adjudication and any final evidence; no acceptance claim before
   required evidence. **Reviewer B runs at the orchestrator's seat next**, then
   CHARC/orchestrator accept. Fill/CLAUDE pointer and D3 register row are theirs
   to write at accept; no claim that those changes/row already exist. No test
   marker, other-package test, product/src/tools/frozen-interface or conftest
   executable edit is owned. No docs/testing.md or footage-derived artifacts.
6. Final return under about 70 lines plus FILES CHANGED and COMMIT. The
   package is not complete merely because A1 terminated: final gates, Reviewer
   B and owner accept remain. Maintain severity/envelope/evidence records for
   any subsequent seat findings; do not silently expand ownership.
