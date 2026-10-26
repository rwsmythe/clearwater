# WP3.19 accept record (orchestrator generation 12, 2026-10-26)

**Package:** WP3.19 batch queue and export progress (`clearwater.gui.export_panel`, `batch_panel`, `export_service`;
the granted seam `clearwater.jobs.export_seam`), brief `docs/briefs/wp3.19-brief.md` (FINAL; CHARC rulings
`53d1d906e47fe2c9`; round 0 `0e6962c39f216c86`: seam approved, C1 granted, C2-C7 accepted; seam wording
`efc95f5d4e7b8456`). Two seats (implementer-sonnet-high, STRONG): seat 1 round 0 (123,884 at the round-0 yield) to R2
and cleanup (261,443 at the round-2 yield); seat 2 Reviewer B pass-1 remediation and pass-2 fixes (depth not recorded by generation 11;
"reported by the orchestrator", not in the ledger).

**Candidate:** author branch `wp3.19` (`071cb1f`, base `718324b`, 26 commits); merge candidate `wp3.19-mc` (`1be0a99`,
base `7fff7be`, 26 commits). Gate: stacked branch `stackB` = main `ccaecd7` + WP3.17 + WP3.19 + WP3.20 + WP3.18
(cherry-picked ranges, file sets disjoint; head `d71d994` at drafting); every owned file byte-identical in `stackB`,
`wp3.19-mc` and `wp3.19` (`git diff`, 0 lines). Merged: one `git merge --ff-only` of `stackB-acc` onto main; this record's own commit follows the package's last commit.

**Footprint (checked at this seat):** owned files only: `src/clearwater/gui/batch_panel.py`,
`src/clearwater/gui/export_panel.py`, `src/clearwater/gui/export_service.py`, `src/clearwater/jobs/export_seam.py`
(granted, C1), `tests/test_gui_batch_panel.py`, `tests/test_gui_export_panel.py`, the report
`docs/reports/wp3.19-batch-export.md`, the ledger. `interfaces/`, `gui/__init__.py`, `jobs/__init__.py`,
`contract.py`, `pyproject.toml`, `uv.lock` untouched; 0 CR bytes in every owned blob.

**Results:** File > Export with progress, cancel and a shared `ActivityGate`; batch queue G7/D81 (a failed item is
skipped, logged, reported), D45 cancel stops the rest, G8 outputs kept, D83 refusals, end-of-run report; the seam
loads no PySide6 (subprocess test). V7 maxima 13 ms (export), 11 ms (batch), informational. Targeted: 85 passed.

## Nets

| Net | Result |
|---|---|
| Reviewer A (cell, STRONG, WSL codex-cli / gpt-5.6-sol high) | R1 0/2/1 (F1 export gate held when setup raised after `try_start`; F2 warnings of failed/cancelled items dropped; F3 test gap) -> `852192d`, `3d01ae6`, `735dd5f`; R2 0/0/3 NO_NEW_CRITICAL_MAJOR (CONVERGED), terminated at R2; cleanup `e887043`, `d853ff7`, seam wording per CHARC `efc95f5d4e7b8456`. Tests written after the product code (disclosed; mutations and planted tests instead of a red first run). Evidence `clearwater-review-evidence\wp3.19\r1`, `r2` |
| Reviewer B pass 1 (this seat, `70c25ee`, kept as branch `wp3.19-mc1`) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 17 "succeeded in"; 143,298 tokens. 2 MAJOR (non-ok outputs/warnings dropped by Export; batch Start gate held when setup raised), 3 MINOR, 1 ADVISORY -> seat 2: `f0106f1`, `5e35f10`, `d4cd1e4`, `6fbbb05`, `9eefd83`, report; each test failing on `b12c3fd` or a planted copy; 77 passed after. md5 `review-B.txt` 052d8b3b8035... (`reviewB\md5sums.txt`) |
| Reviewer B pass 2 (this seat, `5fb6d9e`, kept as branch `wp3.19-mc2`) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 19 "succeeded in"; 134,482 tokens. 2 MAJOR (#1 ok result with empty outputs read "Saved"; #2 shared basename), 3 MINOR (#3 stale warning, #4 Clear Queue cleared errors, #5 V7 at batch size). SECOND BLOCKING PASS, ADJUDICATED AT THE GATE (generation 11), CHARC UPHELD (msg d329e80e351c3dcc): #1 downgraded, defensive text in the panel `0da4102`; #2 `f9238cf`; #3 `51fde41`; #4 `c05d5d7`; VERIFIED BY EXECUTION at the orchestrator's seat: 5 failed on `9eefd83`, 85 passed on the candidate. #5 (V7 at a few hundred items) = LIMIT. md5 `review-B.txt` ea0809e39dd0... (`reviewB2\md5sums.txt`) |
| Candidate full pytest (this seat, stack top `d71d994` = main `ccaecd7` + WP3.17 + WP3.19 + WP3.20 + WP3.18) | 4501 passed, 2 skipped, 1579 s, exit 0 (CuPy as installed, offscreen, one background process; log `.worktrees/stackB/work/g12-full.log`). This is also main's figure by code identity: main after the merge differs from `d71d994` in the four accept records only |
| Harness gate | 366 OK (1 skipped) on `d71d994`; ruff clean, 217 formatted, mypy 126 clean; CR check 0 on every changed blob |

**Debt:** DR-44 (b) ADDRESSED for this package (owners `"export"`, `"batch"`); DR-44 (a), (c), DR-35 (b), (c) not this
package's. Row by CHARC at QA: V7 with a queue of a few hundred files is unmeasured (B pass 2 #5, LIMIT; the list is
rebuilt on every item state change). For WP3.14's brief: "an ok JobResult names at least one output" (B pass 2 #1).

**Consumer notes:** WP3.14 implements `ExportJobs` (photo and video; a video's analysis inside the job), returns
`CANCELLED` itself, owns a fresh `Reservations` per job, writes through `plan_output` / `SafeWrite`, builds no Qt
object, imports the seam from `clearwater.jobs.export_seam` (no PySide6); a batch-wide D87 disk check is impossible
with one job per item (each job checks its own). WP4.3 calls `install_export_panels(window, exports)` with WP3.14's
jobs and re-measures V7 with the real engines; the panels never call `setEnabled` on `actions.export`.
