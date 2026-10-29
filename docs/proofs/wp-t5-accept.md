# WP-T5 accept record (orchestrator generation 17, 2026-10-29)

**Package:** WP-T5, suite cost (DR-65).
- Brief: `docs/briefs/wp-t5-brief.md` (FINAL; Rulings CHARC `2c4476d9869df056`; comparability ruling `2548bd27b24909b8`).
- Lane: **Codex**, `implementer-codex-sol-high` (gpt-6.1-sol / high).
  - `codex exec` turns through `scripts/codex_cell.py`, one session `01a183e8-501b-7cd1-8948-3914c4afcb1b`, turns 1-6.
  - Dispatch pace: Codex 0.188 vs Claude 1.355.
- Both nets: the **Claude pass** (`codex_cell.py review`, `claude -p --model opus --effort high`, read-only), the OTHER model from the implementer.
- Report: `docs/reports/wp-t5-suite-cost.md` (FINAL). Ledger: `docs/proofs/wp-t5-ledger.md`.

**Candidate:**
- Branch `wp-t5-mc`: the author branch `wp-t5` (`5d6bca7`, base `3aa3c51`) rebased with `git -c core.autocrlf=false` onto main `446dec4`.
  - Code head `7e8ca05`. This record and the report's FINAL edit are one docs commit on top.
- **`git patch-id --stable` `2f1173a5`** on `3aa3c51..wp-t5` and on `446dec4..7e8ca05`.
- Main's moves since the base touch no code: `git diff --stat 3aa3c51 446dec4 -- src tests tools pyproject.toml uv.lock` prints nothing.
- **SHA map** (author -> main, Reviewer B F1):

| Author commit | On main | Content |
|---|---|---|
| `a9abb8d` | `737378d` | rung 0 evidence (docs) |
| `b17b2d4` | `8665365` | W1 timing, round-0 table (docs) |
| `045d622` | `7341c73` | the test change (3 frames + `nb_frames == 3`; the `gx011627_standard_encode` fixture) |
| `259a219` | `7c42596` | W2 record, W2b/W3 scripts (ledger only); the W3 head |
| `6467e54` | `cb1e859` | report and ledger |
| `5d6bca7` | `7e8ca05` | R1 cleanup (docs) |

**Footprint (checked at this seat):** 4 files, plus this record.
- `tests/test_jobs_export_video.py`: the 5.3K 8:7 clip at `duration="0.1"`, plus the precondition `assert probe(source).video.nb_frames == 3`.
- `tests/test_io_video_encode.py`: the module-local, session-scoped `gx011627_standard_encode` fixture, and the sink test and the levels test's `standard` leg rewired to it.
- `docs/reports/wp-t5-suite-cost.md` and `docs/proofs/wp-t5-ledger.md`.
- Nothing under `src/` or `tools/`, and no other test, `conftest.py`, `pyproject.toml` or `uv.lock`.
- Every changed blob has 0 CR bytes.
- Nothing footage-derived is committed. No `gpmd`, IMU, GPS or location data was read or recorded.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (the Claude pass, run by me between cell turns, `wp-t5\r1\`) | Head `6467e54`. **0 / 0 / 2 / 5** (critical / major / minor / advisory), `VERDICT: NO_NEW_CRITICAL_MAJOR`. All six claims hold. Assertion map EXECUTED: one added assert, none removed. `--setup-plan` EXECUTED. Run checks: `modelUsage` `claude-opus-5-5`; `is_error` false; 34 turns; worktree clean; 7 permission denials (FFmpeg probes, and one git command that carried a `:!docs/proofs` exclusion). md5 `review.txt` `d1f4dda4fd864ae438b2c4beefdba32a`. Zero new blocking findings, so the loop TERMINATED: one round plus the single cleanup (turn 6). Both minors were report wording: R1-1, the NVENC tie is held by the one call and not asserted; R1-2, the attributable 405.273 s is stated beside the whole-leg 536.966 s. |
| **Reviewer B** (the Claude pass at this seat, on the candidate `c5a5654` = `7e8ca05`'s code on `51f0e5e`, `wp-t5\reviewB\`) | **0 / 0 / 1 / 5**, `VERDICT: NO_NEW_CRITICAL_MAJOR`. Run checks: `modelUsage` `claude-opus-5-5`; `is_error` false; 25 turns; worktree clean; 4 permission denials; no withheld path read. md5 `review.txt` `55e16d691254490c43935ea52b637eda`. F1 (the report cites author SHAs) is answered by the SHA map above. F2 (setup ERROR, not FAIL, on a fixture failure) is an Erratum at the gate in the report. F3-F6 agree with the report's limits. |
| Comparison windows (W1 BEFORE, W3 AFTER; exclusive; W1's config: the worktree's own `work/`, no V8 frames, like for like) | W1 SERIAL: 1104 passed / 10 skipped, **2,798.380 s**. W3 PARALLEL: 4174 / 1, 509.951 s. W3 SERIAL: 1104 / 10, **2,261.414 s**. W1's skip lines are identical in W3, and both collections are identical (5,289 / 1,114). **Saving 536.966 s (19.19 %)**, of which 405.273 s is attributable to the three changed tests. Both are above Q5's 110 s bar. W2 and W2b are development evidence: both controls were caught by name. |
| **Standard gate: the STACKED two legs** (this seat, stack top `aefd563` = WP-T5 `7e8ca05` + WP4.1 `0a0a787` rebased, main `work/` config; 23:41:38Z-00:33:51Z; free memory 11.2 GB before) | PARALLEL `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/stack-p4a-parallel`: **4473 passed, 1 skipped**, 616.56 s, EXIT 0; skip `test_color_roundtrip.py:121`. SERIAL `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/stack-p4a-serial`: **1126 passed, 1 skipped, 4474 deselected**, 2,511.76 s, EXIT 0; skip `test_photo_check.py:139`. Both skips are exactly WP3.21's gate skips. 1,126 = WP3.21's 1,113 + 13 WP4.1 serial tests; 4,473 = 4,174 + 299 WP4.1 parallel tests. |
| Static (this seat, candidate with this record) | `ruff check .` all checks passed; `ruff format --check .` 250 files already formatted; `mypy` no issues in 138 source files. |
| Harness gate (this seat, candidate with this record) | `uv run python -m unittest discover -s tests/harness`: Ran 382 tests, OK (skipped=1). |

**The stack ruling.** CHARC approved the stacked form (`6be5d8cdcc500129`). WP4.1 was then PULLED at its own Reviewer B (BLOCKING), so WP-T5 merges ALONE on the stack top's figures (CHARC `870c8ddeb64b4e12` Q3). WP4.1 touches no WP-T5 file and no shared fixture or `conftest.py`, so the stack top's suite is a superset of WP-T5's. WP4.1 gates on its own candidate after this merge.

**For CHARC's register:**
- DR-65 CLOSED: the closure text is the report's "For CHARC" paragraph.
- The CLAUDE.md serial-leg figure is 2,511.76 s on the stack top, or 2,261.41 s as the like-for-like comparison wall.
- R1-1 is a pre-existing gap: no test asserts `nvenc_proof.tied`.
- R1-3 is a limit: at 3 frames the `ctts` path may not be reached at 5.3K, and the longer libx265 tests still reach it.

**Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-t5\` (`cell\` prompts and returns 1-6, `r1\`, `reviewB\`, each with `md5sums.txt`). The run logs are in `.worktrees/wp-t5/work/wp-t5/` (W1, W2, W2b, W3) and `.worktrees/wp4.1-mc/work/stack-p4a-*.log` (the gate).
