# WP4.2b accept record (orchestrator generation 19, 2026-10-29)

**Package:** WP4.2b, Output-name containment in jobs.naming (DR-80).
- Brief: `docs/briefs/wp4.2b-brief.md` (FINAL on CHARC `5c056d647ad9ca99`). Governing amendments, each recorded verbatim in the ledger:
  - CHARC `0c8d52528a11b714`, (A): `OutputNameError`, the one `check_outputs` branch grant, the bounded WP4.2a test edit, merge first, own window;
  - CHARC `050c52106cd8c6ad`: condition 3 extended with (c) and (d), the test-only plants;
  - CHARC `8262cd59b0d48c73`: R1 F1 (a), the one twin test.
- Lane: **CODEX**, `implementer-codex-sol-high` (gpt-6.1-sol / high).
  - Eight `codex exec` turns through `scripts/codex_cell.py`, in one session (`01a185e9-1157-75a0-b60b-8cbcf046d532`). The orchestrator committed each turn.
  - Pace at dispatch: Codex 0.459 (5.0 % used at 10.9 % of the window, 04:26:14Z) vs Claude 1.34 (53 % at 39.5 %, 04:26:24Z).
- Both nets: the CLAUDE pass (`claude-opus-5-5`, high, read-only), STRONG tier.
- Report: `docs/reports/wp4.2b-naming-guard.md`. Ledger: `docs/proofs/wp4.2b-ledger.md`.

**Turns** (`tokens used` / input depth of a 475,000 window, from the driver logs):

| Turn | Content | Tokens / depth | Commit (author branch) |
|---|---|---|---|
| 1 | round 0 (read, map, note) | 90,285 / 87,357 | `e5983bd` |
| 2 | build; STOP on the WP4.2a test conflict | 144,321 / 137,070 | `f1a6bba` (WIP) |
| 3 | ruling check; STOP 2 (condition-3 premise) | 306,885 / 167,794 | `79b60d9` |
| 4 | build under both rulings | 379,056 / 206,526 | `215817a` |
| 5 | Reviewer A R1 adjudication, no change | 413,658 / 237,641 | none |
| 6 | R1 remediation (twin test, drive-relative row, report) | 451,126 / 274,367 | `30d8d81` |
| 7 | R2 terminating docs cleanup (one `Raises:` line) | 499,899 / 59,755 (CLI compaction) | `f3c1381` |
| 8 | report FINAL, docs only | 522,822 / 81,842 | `c4db999` |

**Candidate:**
- Branch `wp4.2b-mc`: the author branch `wp4.2b` rebased onto main `f3835cc` with `git -c core.autocrlf=false`. The cell never rebased it. Main's moves since `f991254` are docs only (CHARC and orchestrator state, register).
- The gated and Reviewer-B tree is `a6910f1` (`f3c1381` rebased). On top: turn 8 (`3954aab`, docs only), then this record.
- **`git patch-id --stable` `b88eac69`** on `f991254..f3c1381` and on `f3835cc..a6910f1`.
- **Code identity with the gated tree:** `git diff a6910f1 3954aab -- src tests tools` is EMPTY.

**Footprint (checked at this seat; 8 files plus this record):**
- `src/clearwater/jobs/naming.py`:
  - `OutputNameError(ValueError)`;
  - the composed-name check in `_base_plan` (no `/`, `\` or `:`; `Path(name).name == name`; no drive);
  - the two `Raises:` lines.
- `src/clearwater/jobs/__init__.py`: the additive export.
- `tools/headless_export.py`: the import, the ONE granted `except OutputNameError` branch (exit 2, before jobs), and its one `Raises:` docstring line (ruled part of the branch grant; CHARC concurred).
- Tests:
  - `tests/test_jobs_naming.py`: new tests, including the 696 WP2.3 fixture-name controls;
  - NEW `tests/test_wp42b_naming_guard.py`: ONE test, three rows, `[engine]`, `[before-jobs]` and the seat-granted `[engine-drive-relative]`;
  - `tests/test_wp42a_runner_hardening.py`: the 22 listed edits under condition 3 (a)-(d), plus the ONE granted twin `test_output_file_form_check_refuses_planted_stream_before_jobs[run|main]`.
- The report and the ledger.

**Locks, all held:**
- `src/clearwater/interfaces/` is unchanged, as are `src/clearwater/jobs/export.py`, `pyproject.toml`, `uv.lock` and `tests/conftest.py`. Every WP4.2 file is untouched.
- WP4.2a's parent guard and file-form check stay as written (defence in depth). Each is pinned by a mutation that reds its tests.
- No new dependency. Every changed blob has 0 CR bytes.
- Every stream, link and stand-in footage folder was under `tmp_path` or `work/`. The footage folder was never named or written.
- No `gpmd`, IMU, GPS or location tag was read or committed.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (Claude pass, `215817a`; `wp4.2b\r1\`) | 0 critical / 0 major / 1 minor / 4 advisory, `NO_NEW_CRITICAL_MAJOR`. **F1 MINOR, EXECUTED:** after the WP4.2a edits, deleting the runner's file-form check (M1) broke no test. Fixed by the CHARC-granted twin, which is RED under M1. F2 (`..` passes) and F5 (cosmetic) banked; F3 (runner-test deviation) stated in the report, plus the `[engine-drive-relative]` row; F4 one report sentence. md5 `review.txt` `e459925b4e409a65254fe27f4ab51fc7`. |
| **Reviewer A R2** (Claude pass, `30d8d81`; `wp4.2b\r2\`) | 0 / 0 / 0 / 5 advisory, **`NO_NEW_CRITICAL_MAJOR`**, nothing reopened; CONVERGED. Mutations: M1 reds exactly the twin's two rows; M3 (the base rule) reds 26, and `[engine-drive-relative]` writes `cwd/input_corrected.png` on the base; M4 reds 15; M5 (parent guard off) reds exactly the 8 drive-relative cases; M7 reds 18. Terminating docs cleanup in turn 7. md5 `review.txt` `48c380f529fe205dc6f0034848ab5135`. |
| **Reviewer B** (Claude pass at this seat, `wp4.2b-mc` `a6910f1`, base `f3835cc`; `wp4.2b\reviewB\`) | **`NO_NEW_CRITICAL_MAJOR`**, 45 turns. All claims were re-derived. Rebase identity: an empty diff over `src`, `tools`, `tests` and `docs/reports`. 348 base-versus-head fixture comparisons gave 0 differences. Both runner routes were probed on real ADS sources: exit 1 with a failed item when no footage is configured; exit 2 before jobs with the stand-in. Non-ASCII and control characters are escaped. M1, M3 (26) and M2 (15) all go RED. Advisories: B-A1 a stale report sentence and B-A2 the POSIX `\` note, both fixed in turn 8; B-A3 the engine order (a refused name pays for read and render first), recorded for WP4.3; B-A4 = F2. md5 `review.txt` `bc9b165b5c8493994b987d27a535bfac`. |
| **Two-leg gate** (this seat, `wp4.2b-mc` `a6910f1`, main `work/` config; Git Bash, `PYTEST_ADDOPTS` unset, offscreen; 10.3 GiB free before; OWN window, not stacked) | PARALLEL `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp4.2b-parallel`: **5250 passed, 1 skipped** (`test_color_roundtrip.py:121`), 660.85 s, EXIT 0 (06:27:30Z-06:38:43Z). SERIAL `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp4.2b-serial`: **1126 passed, 1 skipped** (`test_photo_check.py:139`), 2,558.54 s, EXIT 0 (-07:21:24Z). 5250 = WP4.2a's 4539 + 711. Both skips are the standard gate's. |
| Static (this seat, on `a6910f1`) | `ruff check .` all checks passed; `ruff format --check .` 261 files already formatted; `mypy` no issues in 141 source files. |

**Banked and owed (for CHARC's register at this accept):**
- **DR-80 CLOSES.** The closure text is in the report's "for CHARC" line. It includes: the runner refuses an `OutputNameError` before jobs (exit 2).
- **B-A3** (candidate WP4.3 row): on the engine route with no footage preflight (the GUI), a refused output name still pays for the photo read and render, or the video probe and encoder resolution, before `_plan` raises (`export.py:711-753`, `:808-837`). Nothing is written.
- **F2 / B-A4:** a source named `..` passes the rule. Unreachable (no such file; a request needs a media suffix); recorded only.
- **WP4.3 wording:** on POSIX a real source name with `:` or `\` is now refused, and the failed item does not tell the user to rename it.

**Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp4.2b\` (`cell\` prompts, returns and driver logs for turns 1-8; `r1\`, `r2\`, `reviewB\`, each with `md5sums.txt`). The cell's run logs are copied to `work\wp4.2b\cell-logs\` (69 files), and the gate logs to `work\wp4.2b\gate-logs\` (5 files).
