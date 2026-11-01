# WP-T7 accept record (orchestrator generation 31, 2026-11-01)

**Package:** WP-T7, gate hygiene: a per-test timeout on every gate leg (closes DR-109; commissioned by CHARC `97d5abbf` after gate `g30-wpd54`'s serial leg hung 6 h with no stack, DR-108).
- **Brief:** `docs/briefs/wp-t7-brief.md` (commission `97d5abbf`; thread-method ruling `97d7981b`; Reviewer A round 1 concurrence `823921b8`, F3 = every leg command captures stderr; all folded on the branch).
- **Lane: CODEX**, `implementer-codex-sol-high`, one session (`01a1983a-45de-7530-8ca2-8d53963ad4c7`), six turns; depth after turn 6: 197,641 of 475,000. Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp-t7-gate-timeout.md`. **Ledger:** `docs/proofs/wp-t7-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-t7\` (`cell`, `r1`, `B`, the rulings).

**Candidate:** branch `wp-t7` rebased onto main `4cda288b` = **`660630f8`** plus this record. The gate ran on the same patch rebased onto `15bb2b93` (`46f86cfe`); main's later commits (`9efbf18f`, `4cda288b`) touch only `docs/charc-state.md`. `git patch-id --stable` over the package diff: **`32fe931df27a`** on the author branch (`c81831f9..51b3f9a0`), on `46f86cfe` and on `660630f8`.

**Footprint** (`git diff --name-only main..660630f8`, 8 paths): `pyproject.toml` (the `dev` group gains `pytest-timeout>=2.3,<3` with its provenance comment; `[tool.pytest.ini_options]` gains `timeout_method = "thread"`, `timeout_func_only = true`, `faulthandler_timeout = 300`, no default `timeout`), `uv.lock` (pytest-timeout 2.4.0 only), `tests/test_gate_timeout.py` (NEW, the proof), `docs/review-gate-clearwater.md` (GATE_CHECKS: the three legs' `--timeout 600 / 1200 / 2400` and `> work/<log> 2>&1`; the STANDING RULE verbatim with its fullclip extension; the STALL WATCH defined; the timeout, xdist, out-of-protocol and orphan-child limits), `CLAUDE.md` (the "Tests:" line's three commands: the flags and the redirects only), the brief, the ledger, the report; plus this record. No product file. Every changed blob has 0 CR bytes (8 of 8 checked).

## Nets

| Net | Result |
|---|---|
| Reviewer A round 1 (Claude pass on `e4938910`, `clearwater-review-evidence\wp-t7\r1\`) | **NO_NEW_CRITICAL_MAJOR**, converged in one round; executed first (1 passed, 3.10 s). 3 MINOR (F1 `timeout_func_only` unpinned; F2 a GIL-holding hang defers the thread timer; F3 under `-n 4` the only stack is on stderr) and 4 ADVISORY, all ACCEPTED; the terminating clean-up `e78d9bfb` (author id) and, per CHARC `823921b8`, the redirect in every leg command `1d541378`. |
| **Reviewer B** (Claude pass at my seat on `1d541378`, base `c81831f9`; ledger and report WITHHELD; `clearwater-review-evidence\wp-t7\B\`) | **NO_NEW_CRITICAL_MAJOR**; `claude-opus-5-5`, `is_error` false, 29 turns, worktree clean; executed first (`1 passed in 3.29s`). Claims 1-5 HOLD; claim 4 EXECUTED: each GATE_CHECKS command collection-only with the flag and the redirect exits 0, 6,129 + 1,241 + 7 = 7,377 = all, no "unrecognized arguments". 5 MINOR + 4 ADVISORY fixed in turn 6 (`51b3f9a0`): F1 the stall watch DEFINED in GATE_CHECKS (CHARC's "standing in GATE_CHECKS"), F2 the xdist worker's timeout dump IS absent, F3 out-of-protocol hangs, F4 orphaned Windows children before a re-run, F5 the ini facts pinned by `tomllib`, F6 "Stack of" asserted, F7 the dead elapsed assertion removed, F8 the fullclip extension, F9 the timed-out leg's signature; F10 (the sandbox shim branch) DECLINED. No B re-run (test-assertion and doc-only turn; the gate below exercises the node). |

## Gate

The ONE two-leg gate WITH the package's own flags and redirects (`work/orch-g31/gate.sh`), on `46f86cfe`, run id `t7`, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`, C: 166 GB free at the start; logs `work/orch-g31/gate-t7/`.
- **Static:** `ruff check` passed; `ruff format --check` 293 files already formatted; `mypy` no issues in 148 source files; 0 CR in every changed blob.
- **Collection:** all **7,382** = parallel 6,134 + serial 1,241 + fullclip 7; no duplicates; union identical to collect-all.
- **Harness gate** (CLAUDE.md and a fill doc changed): `Ran 382 tests ... OK (skipped=1)`.
- **PARALLEL** (`-n 4 --timeout 600`, stall-watched): **6,133 passed, 1 skipped**, EXIT 0, 476 s (19:10:42Z-19:18:40Z). The skip is the standing swscale refusal. Log md5 `f55e7f0dd169d6bfaa67e91fcf6c2f3b`. Two Codex turns (WP5.3 t10, WP5.1 t15) and Claude review passes overlapped it.
- **SERIAL** (`--timeout 1200`, ALONE on the host per the standing rule, stall-watched; no stall reported): **1,230 passed, 11 skipped, 0 failed**, EXIT 0, 1,723 s (19:27:42Z-19:56:27Z). The 11 skips are the standing look-check frames archived to D: (`test_app_v8_v18.py:134` 1, `test_methods_assembly_v8.py:44` 5 + 4, `test_wp41_v8.py:193` 1), the same 11 as WP-D54's gate. The DR-99 node passed. No timeout fired. Log md5 `4a93b36e524611797b3092a1f3929d96`; junit `work/g31-t7-serial.xml` in the worktree.
- **FULLCLIP:** not run (the brief asks none); its command's flag and redirect checked by collection only (7 nodes, above).

## Dispositions

- **CHARC's at this accept:** DR-109 CLOSED (with F2's GIL limit recorded in its close, per `823921b8`).
- Limits carried in the report and GATE_CHECKS: a GIL-holding native hang defers the thread timer (only the faulthandler dump and the stall watch catch it); `timeout_func_only` leaves fixtures un-timed; hangs outside the test protocol get neither timer nor dump; under xdist only the parent's faulthandler stderr dump survives; `os._exit` orphans Windows children.
- From this merge on, every gate runs the three commands as GATE_CHECKS now writes them (a worktree branched before this merge needs a rebase onto it, or `uv sync` of the dev group, before its gate).

## Merge

`main` fast-forwarded to `660630f8` plus this record's commit, by the orchestrator. The worktree `.worktrees/wp-t7` is kept until CHARC's accept-side commit lands.
