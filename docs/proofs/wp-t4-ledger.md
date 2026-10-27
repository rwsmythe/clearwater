# WP-T4 cumulative ledger

## Dispatch and scope

- Codex lane, turn 1; assigned rungs 0 and 1 only.
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
- Dispatcher-read token depth: not supplied yet; no estimate substituted.

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
not claim a successful GNU `comm` invocation. The dispatcher can rerun
`uv run python work/wp-t4/turn1_partition.py` to complete that exact check.

Marker counts: `gpu` 579, `footage` 16, `gui` 411, `slow` 16. Their sum is
1,022, exceeding the serial union by 16 memberships. There are **12** distinct
multiply marked tests: eight with two markers and four with three markers.
Thus the brief's explanation "16 tests carry two markers" is inaccurate; its
counts and partition total are correct. The observed total matches the brief's
4,768 and is two above the 4,766 quoted by ruling `6f725eee`.

The only dependency declaration edit is the granted comment and
`"pytest-xdist>=3.6,<4",` in the dev group. Dependency installation, installed
license quotations, plugin discovery and the photo dependency-grant test remain
pending successful lock/sync; no success is claimed for them.

Final turn checks: `git diff --check` exited 0; `git diff --stat` reports only
two added lines in `pyproject.toml` (the new ledger is still untracked).
`turn1-final-state.log` records exit 0 for byte equality of `uv.lock` against
`HEAD:uv.lock`, pytest 8.4.2 in both the lock and installed environment, absence
of xdist/execnet from the unchanged lock, and LF-only bytes in both changed
files. Final status lists exactly `pyproject.toml` and this new ledger.

## Verification-loop record

| ID | Severity / class | Suspected | Independently confirmed or rejected | Fix / disposition |
|---|---|---|---|---|
| T1-1 | Minor; environment, in-envelope; NEW | GNU tools may be unavailable in this sandbox | Confirmed: `sort.exe` exits 256 with `CreateFileMapping`, Win32 error 5; Python instrument exits 1 | Standard-library sorted-set proof passed; exact GNU sort/comm check routed to dispatcher |
| T1-2 | Major; environment blocker, in-envelope; NEW | Index access may block the lock update | Confirmed by the single `uv lock` attempt: failed to fetch `https://pypi.org/simple/numpy/`, connection refused, OS error 10061, exit 2 | No retry or alternate dependency; dispatcher to run `uv lock`, then `uv sync` |
| T1-3 | Minor; brief facts, in-envelope; NEW | The overlap explanation may conflate tests with memberships | Confirmed by marker hook over all 4,768 collected items: eight double and four triple overlaps | Corrected in this ledger; no marker or test edited |
| T1-4 | Verification; rejected false positive | Partition totals might differ on the dispatched base | Rejected by three collections and independent set equality | No change needed; exact 4,768 total recorded |

The turn ends at the dependency-resolution blocker, as required by dispatch.
Rungs 2-5, test execution, lint/type gates and Reviewer A have not been attempted.
No product-code or test-code fix, revert, exception, or marker move occurred.

## Heavy-run ledger

No heavy windows requested or consumed in turn 1. Future rows will record start,
end, command, N, outcome counts, exit, available memory before, peak summed RSS,
minimum available memory and any GPU-memory change from dispatcher evidence.

## Cumulative review-round ledger

| Round | Critical / major / minor | In / out of envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Reviewer transport / version | Dispatcher-read depth | Disposition |
|---|---|---|---|---|---|---|---|---|
| Not started | N/A | N/A | N/A | 0 | 0 / 0 | Driver-owned Claude Opus high; pending | Not supplied | Yield turn 1 for lock/sync and GNU proof |

## Open handoff

1. Dispatcher: `uv lock`, without `--upgrade`, then `uv sync`, with output files
   under `work/wp-t4/`; check that only xdist and execnet are added, existing
   versions remain fixed, and pytest remains 8.4.2.
2. Dispatcher: rerun `uv run python work/wp-t4/turn1_partition.py` outside the
   sandbox restriction to obtain the two empty GNU `comm` outputs.
3. Next cell turn: consume those results, quote installed licenses, verify the
   xdist plugin and dependency-grant test, then proceed only as dispatched.
