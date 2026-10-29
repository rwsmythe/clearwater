# WP4.2a accept record (orchestrator generation 18, 2026-10-29)

**Package:** WP4.2a, Runner hardening (WP4.1's Reviewer B pass 2 items: DR-78, DR-79).
- Brief: `docs/briefs/wp4.2a-brief.md` (FINAL on CHARC `c8340144a8e87c09`; four helper choices concurred, CHARC `22ad3fe6122c2883`).
- Split from WP4.2 by CHARC's R1-Q5 under the 2026-10-27 lane rule, with a CAP at WP4.2's round-0 yield + 3 h (05:33:37Z). The package merged inside the CAP.
- Lane: **CODEX**, `implementer-codex-sol-high` (gpt-6.1-sol / high), six `codex exec` turns through `scripts/codex_cell.py` in one session (`01a18576-cc76-7621-847a-2a92cc6a5323`), each committed by the orchestrator. Pace at dispatch: Codex 0.414 (4.0 % used at 9.7 % of the window, 02:21:08Z) vs Claude 1.331 (51 % at 38.3 %, 02:21:19Z).
- Both nets: the CLAUDE pass (`claude-opus-5-5`, high, read-only), STRONG tier.
- Report: `docs/reports/wp4.2a-runner-hardening.md`. Ledger: `docs/proofs/wp4.2a-ledger.md`.

**Turns** (`tokens used` / input depth of a 475,000 window, from the driver logs):

| Turn | Content | Tokens / depth | Commit (author branch) |
|---|---|---|---|
| 1 | round 0 (read, map, note) | 77,213 / 88,453 | `933e33e` |
| 2 | tasks 3-6 RED-first, report DRAFT; STOP on three UNC nodes (sandbox only: 4 passed and the light set 340 passed at the orchestrator's seat) | 127,137 / 134,393 | `d5c9ae3` |
| 3 | ruff format and line length, no behaviour change | 140,058 / 146,457 | `a05c13e` |
| 4 | Reviewer A R1 adjudication | 298,255 / 163,961 | `52e00c0` |
| 5 | R1 remediation | 344,071 / 190,250 | `7addc2b` |
| 6 | R2 terminating cleanup | 440,250 / 68,343 | `952f31a` |

**Candidate:**
- Branch `wp4.2a-mc`: the author branch `wp4.2a` (`952f31a`, base `aa4761b`, never rebased by the cell) rebased with `git -c core.autocrlf=false` onto main `32099ae`. Main's moves since `aa4761b` are docs only (CHARC and orchestrator state, DR-80).
- On top: the docs-only Erratum `318e8de`, then this record.
- **`git patch-id --stable` `9ca7ffa4`** on `aa4761b..wp4.2a`, on the gated candidate `d5d4b00..c4eab41`, and on `32099ae..d8b991c`.
- **Code identity with the gated and Reviewer-B tree `c4eab41`:** `git diff c4eab41 d8b991c -- src tests tools` is EMPTY (0 lines).

**Footprint (checked at this seat; 6 files plus this record):**
- **Edited:**
  - `tools/headless_export.py`: `_write_form_refusal`, `write_target_refusal`'s call of it, `check_outputs` (the file check and the planned-parent guard), `Redactor`'s `\'` forms, the four construction wraps, and `main`'s argument-error redaction fallback;
  - the one top-level import line, GRANTED at turn 2.
- **Tests:**
  - NEW `tests/test_wp42a_runner_hardening.py` (53 cases);
  - the four GRANTED comparison sites (R1-Q2): `tests/test_wp41_photo_path.py:514`/`:528`, `tests/test_wp41_v8.py:74`/`:162`. Each is now dtype, shape and bytes equal AND `np.array_equal`, so strictly stronger, and the diff shows nothing else changed in either file.
- The report and the ledger.

**Locks, all held:**
- `src/` is UNCHANGED against main (`interfaces`, `jobs`, `app` 0 lines), as are `pyproject.toml`, `uv.lock` and `tests/conftest.py`.
- `tests/test_headless_export.py` is unedited: the mixed pin stays WP4.2's (R1-Q3).
- No new dependency.
- Every changed blob has 0 CR bytes.
- Every link, junction, ADS and stand-in footage folder was under `tmp_path` or `work/`; the footage folder was never named or written.
- No `gpmd`, IMU, GPS or location tag was read or committed.

## Nets

| Net | Result |
|---|---|
| Reviewer A R1 (Claude pass, `a05c13e`; evidence `wp4.2a\r1\`) | 0 critical / 1 major / 1 minor / 5 advisory, `NEW_CRITICAL_MAJOR_FOUND`. F1 MAJOR, EXECUTED: a `<letter>:<rest>` stream source made `jobs/naming.py` `OutputPlan.path` drive-relative. Through `main` with cwd = a stand-in footage folder, it exited 0 and wrote into the stand-in. Remediated by the planned-parent guard (RED-first). F2 (NaN) fixed; F5 fixed; F3/F4/F7 documented; F6 DECLINED (per-request order, as designed). md5 `review.txt` `36f0ed68fd4e935b70b7e668498b9323`. |
| **Reviewer A R2** (Claude pass, `7addc2b`; `wp4.2a\r2\`) | 0 / 0 / 3 minor / 2 advisory, **`NO_NEW_CRITICAL_MAJOR`**, terminating. The reviewer ran 127 tests, UNC included. For F1 it loaded the `a05c13e` runner against the new tests: 9 failed / 13 passed; green at head; a probe matrix with no escape. Terminating cleanup: N2 (argument-discovery redaction, RED-first on base and head) and N3 fixed, N4 documented, N1 and N5 BANKED (pre-existing, origins WP4.1 `f7e7442` and `715fd08`). md5 `review.txt` `3ef4cca179eddcba490f90cb0262ad3f`. |
| **Reviewer B** (Claude pass at this seat, `wp4.2a-mc` `c4eab41`, base `d5d4b00`; `wp4.2a\reviewB\`) | **`NO_NEW_CRITICAL_MAJOR`**, 30 turns. All seven claims hold. Base vs head probes: `carrier:` and `z:` sources pass on base and are refused at head; the apostrophe leaks on base and is hidden at head; a 216-combination redaction fuzz found 0 leaks; the package light set ran 126 passed. Findings: F1 MINOR (pre-existing: a raising footage-folder resolution escapes `main` raw; the report sentence was REPLACED in the Erratum; banked with N1); F2-F5 ADVISORY (observation test counted in 53; `str` source `AttributeError` in `--out` mode, `run` raised it on base; the same-drive one-letter name drops the stream syntax safely; log location). md5 `review.txt` `c4e0f9e373f2bac34c290e64150804e6`. |
| **Two-leg gate** (this seat, `wp4.2a-mc` `c4eab41`, main `work/` config; Git Bash, `PYTEST_ADDOPTS` unset, offscreen; free memory 11.5 GB before) | PARALLEL `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp4.2a-parallel`: **4539 passed, 1 skipped** (`test_color_roundtrip.py:121`), 644.49 s, EXIT 0 (03:19:09Z-03:30:02Z). SERIAL `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp4.2a-serial`: **1126 passed, 1 skipped** (`test_photo_check.py:139`), 2,540.97 s, EXIT 0 (-04:12:26Z). 4539 = WP4.1's gate 4486 + 53. Both skips are the standard gate's. |
| Static (this seat) | `ruff check .` all checks passed; `ruff format --check .` 260 files already formatted; `mypy` no issues in 141 source files (`a05c13e`; re-run on the candidate with this record below). |

**Banked and owed (for CHARC's register at this accept):**
- **DR-78 CLOSED** and **DR-79 CLOSED** with (b)'s wording ("defensive; not reproduced on Python 3.12 / Windows"). The closure texts are in the report's "For CHARC".
- **N1 + Reviewer B F1** (pre-existing runner redaction gaps): a mixed-separator spelling is not redacted in argparse's text (origin WP4.1 `f7e7442`, reproduced on `aa4761b`); a raising footage-folder resolution escapes `main` raw (unchanged from `aa4761b`). Row candidate; trigger: the runner's next redaction touch.
- **N5** (pre-existing): `equal_statistics`' scalar branch equates float32 `0.0` and `-0.0`. It is unreachable today (the statistics are dicts of `ndarray`); origin WP4.1 `715fd08`.
- **DR-80** (already registered, CHARC `0f138ff`): F1's root cause in `jobs/naming.py`; the fix is WP4.2b (Codex lane). The runner's parent guard stays as defence in depth.

**Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp4.2a\` (`cell\` prompts, returns and driver logs for turns 1-6; `r1\`, `r2\`, `reviewB\`, each with `md5sums.txt`). The cell's run logs are copied to `work\wp4.2a\cell-logs\` (48 files), the gate logs to `work\wp4.2a\gate-logs\`.
