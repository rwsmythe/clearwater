# WP-T4 cumulative ledger

## Dispatch and scope

- Codex lane: turn 1 assigned rungs 0 and 1; turn 2 assigned the remaining
  dependency checks and rung 2's worker guard cases.
- Base: `9753b7b4cc05bf43c25442cb87aa74e23f2b584f`; branch: `wp-t4`.
- Initial tracked/untracked status: clean (`STATUS_COUNT=0`), recorded before
  changes in `work/wp-t4/turn1-base.txt`. The ignored local config was present;
  it was not edited.
- Q3 requires the deterministic cold-cache reproduction and lock in a later
  turn. Q7 requires two interleaved measurement rounds, with a third only if
  the two parallel-plus-serial times differ by more than 15 percent.
- Shared/in-flight files remain untouched, including WP-T3's `verify_generated`
  and `tests/test_fixtures.py`. No source, frozen interface, harness, product,
  or footage edit was made. All cell-authored artifacts are inside the worktree;
  no effect outside the permitted workspace/cache is claimed.
- Dispatcher-supplied turn-1 `tokens used` footer: **73,551** (generation 13's
  turn-2 dispatch). Turn-2 reading is pending; no estimate substituted.

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

Turn-2 final state: `git -c core.autocrlf=false diff --check` exited 0.
`turn2-final-state.log` exited 0 after checking that exactly this ledger and
`tests/test_conftest_guard.py` are changed, both contain LF-only bytes, and
`pyproject.toml`, `uv.lock`, `tests/conftest.py` and `tests/fixture_plugin.py`
are unchanged against turn-2 HEAD. Status and diff summary are recorded in
`turn2-final-status.log` and `turn2-diff-stat.log`.

## Heavy-run ledger

No heavy windows requested or consumed in turns 1 or 2. Future rows will record start,
end, command, N, outcome counts, exit, available memory before, peak summed RSS,
minimum available memory and any GPU-memory change from dispatcher evidence.

## Cumulative review-round ledger

| Round | Critical / major / minor | In / out of envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Reviewer transport / version | Dispatcher-read depth | Disposition |
|---|---|---|---|---|---|---|---|---|
| Not started | N/A | N/A | N/A | 0 | 0 / 0 | Driver-owned Claude Opus high; pending | Turn-1 footer 73,551; turn 2 pending | Yield turn 2 for driver review / next dispatch |

## Open handoff

1. Driver-owned Reviewer A and its assertions remain pending; no review round
   is claimed clean or counted toward convergence.
2. Rungs 3-5, the Q2 docstring paragraph, heavy-run sampler, measurement rounds,
   final report and both-leg gate remain future work, subject to dispatch.
3. No additional RUN REQUEST is needed for turn 2 unless the dispatcher wants
   to repeat these light tests without the sandbox shim at its seat.
