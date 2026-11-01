# WP5.1 accept record (orchestrator generation 32, 2026-11-01)

**Package:** WP5.1, the acceptance suite: every spec section 11 test that plan section 7 completes in WP5.1 (V1, V3-V11, V13, V17, V18; N10 / D91 / D92) has a committed, passing node or a cited figure of record, traced in `tests/test_v51_traceability.py`.
- **Brief:** `docs/briefs/wp5.1-brief.md` (FINAL on CHARC `05533fa6`; every later ruling folded on the branch: round 0 `cdeefe5f`, T2-1 `755ef1b0`, T3-1 `da72ec04`, T4-1 `8276adb5`, T6-1 `3a1497d6`, T6-2 `2bd14e3a`, R1 `f6252e0b`, R1 F3 `c39cc00d`).
- **Lane: CODEX**, `implementer-codex-sol-high`, six sessions, fifteen turns (session 6 `01a19886-ba62-7931-85d1-286dff762225` at 102,897 after turn 15). Both nets Claude (`claude -p --model opus --effort high`), the other model.
- **Report:** `docs/reports/wp5.1-acceptance.md` (every former `(gate)` cell filled in this commit from the gate below). **Ledger:** `docs/proofs/wp5.1-ledger.md`. **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp5.1\` (`cell`, `r1`, `r2`, `B`, the rulings).

**Candidate:** branch `wp5.1`, gated as **`232e4af5`** on main `f1733802`, then rebased with this record onto the current main (main's later commits touch only CHARC's and the orchestrator's docs, the register, the decisions and the prune record; no file this package owns or reads). `git patch-id --stable`: the 19 package commits carry the same 19 patch ids on the author branch (`88850ad2`), on `a31797cd`, on `232e4af5` and on the merged head.

**Footprint** (`git log --name-only main..wp5.1`, 8 paths plus this record): NEW `tests/acceptance_support.py`, `tests/test_v51_photo_acceptance.py`, `tests/test_v51_video_acceptance.py`, `tests/test_v51_shell_acceptance.py`, `tests/test_v51_traceability.py`; `docs/reports/wp5.1-acceptance.md`, `docs/proofs/wp5.1-ledger.md`, `docs/briefs/wp5.1-brief.md`. No `src/` file, no frozen interface, no existing test, no dependency, no fixture. Every changed blob has 0 CR bytes.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | 4 MAJOR disputes, all STOPs to CHARC, ruled `cdeefe5f`; the build turns T2-T9 carried four more CHARC rulings (T2-1, T3-1, T4-1, T6-1 / T6-2). |
| Reviewer A round 1 (`r1`) | NEW_CRITICAL_MAJOR_FOUND: 1 MAJOR, 2 MINOR, 5 ADVISORY; CHARC `f6252e0b`; remediated in turn 12 (tests and support only); F3 closed by CHARC `c39cc00d` (`8276adb5` governs). |
| Reviewer A round 2 (`r2`) | **NO_NEW_CRITICAL_MAJOR**, CONVERGED: 2 MINOR, 5 ADVISORY; terminating clean-up turn 13. |
| **Reviewer B** (Claude pass at the orchestrator's seat on `7ab7bd39`; `clearwater-review-evidence\wp5.1\B\`) | **NO_NEW_CRITICAL_MAJOR**, 41 turns, `is_error` false, worktree clean; EXECUTED: `34 passed, 2 deselected` first (the crash node passed); four in-process product mutants (SafeWrite.abort a no-op; orientation dropped; 6/8 swapped; D63 Orientation kept) each FAIL the node claiming the clause; the crash child is the real interpreter. 2 MINOR (B-2 the `-I` crash child ignores PYTHONUTF8; B-3 a 10 s writer wait under load raised instead of retrying) and 6 ADVISORY; B-2..B-7 fixed in turn 15 (`88850ad2`, a FRESH session 6), all fail-loud test fixes; B-1 no change (CHARC `f6252e0b` lists "case-insensitive" among the defects); B-8 (the D85 node's `os.link` needs NTFS) a Limit. The cell's 15 isolated crash runs all reached clean-up (ledger C15). No second B (test-only, fail-loud fixes). |

## Gate

The ONE gate the brief asks (parallel + serial + ONE fullclip leg), WITH WP-T7's flags and redirects (`work/orch-g32/gate.sh`), on `232e4af5`, run id `g32-w51`, Git Bash, `PYTEST_ADDOPTS` unset, `QT_QPA_PLATFORM=offscreen`; no EXCLUSIVE window open and no WP5.3 build piece running during any leg; C: 162 GB free at the start; logs `work/orch-g32/gate-w51/`, `gate-w51s/`, `gate-w51f/`; junits `work/g32-w51-parallel.xml`, `work/g32-w51s-serial.xml`, `work/g32-w51f-fullclip.xml` in the worktree.
- **Static:** `ruff check` passed; `ruff format --check` 300 files already formatted; `mypy` no issues in 149 source files; 0 CR in every changed blob.
- **Collection:** all **7,543** = parallel 6,271 + serial 1,265 + fullclip 7; no duplicates; union identical to collect-all.
- **PARALLEL** (`-n 4 --timeout 600`, stall-watched): **6,270 passed, 1 skipped**, EXIT 0, 491 s (20:42Z-20:51Z). The skip is the standing swscale refusal (`test_color_roundtrip.py:123`). WP5.3's Codex turn 11 (a light pytest) overlapped it. Log md5 `8f5e8668ab45b6a4b72657d56a83b4ad`.
- **SERIAL** (`--timeout 1200`, ALONE on the host, stall-watched; no stall reported): **1,254 passed, 11 skipped, 0 failed**, EXIT 0, 2,039 s (20:58:26Z-21:32:26Z). The 11 skips are the standing look-check frames archived to D: (`test_app_v8_v18.py:134` 1, `test_methods_assembly_v8.py:44` 5 + 4, `test_wp41_v8.py:193` 1). The DR-99 node passed. No timeout fired. Log md5 `ddccc653709a2a0cd79ac732bb898243`. The package's 23 serial nodes sum to 271.7 s of junit time; the leg is +216 s over WP3.6P's serial leg on main (1,823 s, the same host the same evening), within the 300 s allowance (CHARC `2bd14e3a`).
- **FULLCLIP** (`--timeout 2400`, ALONE, stall-watched at 15 min): **7 passed**, EXIT 0, 1,607 s (21:32:46Z-21:59:33Z). The 300 s faulthandler dump fired once on a long node (WP-T7's documented behaviour; the node passed). Log md5 `d93535c811072abc25cb1c3f9be8edd5`.
- **Harness gate:** not run (no harness file changed).

## Dispositions (CHARC's at this accept)

- The plan section 7 completion pointer; AD-11 NOTE (the runner's post-encode bound 3.5/255, `2bd14e3a`); AD-30 NOTE (committed fixtures unchanged); the serial-leg delta above; the G2 creation-time Limit if not yet documented.
- Limits carried in the report: B-8 (`os.link` needs NTFS); the crash oracle's "not observable at this size" skip (never observed).

## Merge

`main` fast-forwarded to the rebased package plus this record's commit, by the orchestrator. The worktree `.worktrees/wp5.1` is kept until CHARC's accept-side commit lands.
