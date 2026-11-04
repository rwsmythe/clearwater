# WP6.2 accept record (orchestrator generation 41, 2026-11-04)

**Package:** WP6.2, the portability audit (code only, no Mac): every site in `src/clearwater`, `tools/` and `tests/` that assumes Windows, with the macOS (Apple Silicon, CPU path, VideoToolbox) change for each, as the file-by-file table WP6.4 implements.
- **Brief:** `docs/briefs/wp6.2-brief.md` (FINAL by CHARC at main `c051306f`, on gen 40's fill `7a8f5135`).
- **Lane: CODEX**, `implementer-codex-sol-high`, two sessions, six turns (session 1 `01a1a5a7-b28f-7520-91a7-f7e251e56ee2` turns 1-2, retired at 224,070 after the report by the depth rule; session 2 `01a1a5d0-8fcc-7f61-8139-5c5249c3feae` turns 3-6, at **212,966** after turn 6). Both nets Claude (`claude -p --model opus --effort high`, through `scripts/codex_cell.py review`), the other model. A read-and-report package: no product, tool or test file changed.
- **Report:** `docs/reports/wp6.2-portability-audit.md` (1,258 lines; 172 site rows: product 74, tools 52, tests 46; Class 1 platform conditionals 42, Class 2 platform assumptions 130). **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp6.2\` (`cell` dispatches, prompts, returns, transcripts; `A\r1`, `A\r2`, `A\r3`; `B`).

**Candidate:** branch `wp6.2` at `2243da6b` (the report), merged with main as `4380d156` (`--no-ff`; main's commits since the base are docs and harness only), plus this record's commit. **Footprint** (`git diff --name-only main...wp6.2`): the report and this record. The report's blob: 0 CR, 0 non-ASCII bytes, LF.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1) | PROCEED; no Windows defect today; the grep record (commands B, W, R, A0, A, S with counts per tree), the table skeleton, Q1-Q3. |
| Turn 2 (`e734db32`) | the report, 148 rows. |
| Reviewer A round 1 (`A\r1`, all 148 citations opened) | **NEW_CRITICAL_MAJOR_FOUND**: F1 MAJOR (the frozen worker launch was already ruled in WP6.1's FINAL brief, Q5) + 7 minor (AD-25(a) not cited; four encoder sites; `AUTO_TEXT`; four line numbers; W / R counts not reproduced; `disk_space.py`; omitted container arguments) + 5 advisory. Fixed in turn 3 (`1e59f941`, fresh session 2), 157 rows. |
| Reviewer A round 2 (`A\r2`) | all F1-F13 FIXED and TRUE; **NEW_CRITICAL_MAJOR_FOUND**: N1 MAJOR (`mypy --platform darwin` fails at four sites, `pipes.py:56`, `tools/prototype/bench.py:1159` / `:1480`, `tools/spike_io/transport.py:950`, two of them marked "Retain") + N2-N4 minor + advisories. Fixed in turn 4 (`71eb2f0f`), 165 rows. |
| Reviewer A round 3 (`A\r3`) | **NO_NEW_CRITICAL_MAJOR = CONVERGED**; 3 minor + 7 advisory with exact corrections (the if / else guard form, since an early return fails the win32 target; T52 / X46 `C:x` on POSIX; P70 macOS-legal names refused at export; P71 trackpad zoom; P72 FFprobe text; the D1 displacement; DR-3's mechanism; the AD-11 tolerance; native quit paths; three citations), applied once without a fourth review by the text-round rule in turn 5 (`c8d85615`), 170 rows; R3-5 DISPUTED by the cell with code. |
| **Reviewer B** (Claude pass at the orchestrator's seat on `c8d85615`; `B\`, `is_error` false, worktree clean after) | **NO_NEW_CRITICAL_MAJOR.** The round-3 corrections applied exactly; totals equal a fresh count; all 125 rows the history never named say what they claim; the encoder section true against `encode.py` / `capability.py`; R3-5's dispute UPHELD (`decode.py:759`, every CPU / GUI caller passes false). 2 MINOR (B1 `PresetStore.rename` and POSIX `os.rename` replacing a target; B2 zero creation flags leave FFmpeg and the worker in the terminal's process group on POSIX) + 6 ADVISORY, applied in turn 6 (`2243da6b`), 172 rows; B4's "every Mac" DISPUTED with `core/backend.py:1028-1029` ("CPU: forced"). The turn-6 rows (P73, P74) were read at the seat against their cited lines. |

## Gate

GATE_CHECKS (the brief's fill): `git diff --name-only main...wp6.2` = the report (plus this record); 0 CR; no pytest leg (no code changed); the harness suite once, because a new file sits under `docs/reports/` and `docs/proofs/` (instance-surface prefixes, no registration expected). The harness result is in the merge line below.

## Dispositions (for CHARC at this accept)

- **AD rows for WP6.4** from the report's recommendations (CHARC's to write): the VideoToolbox leg (section 4: the probe, Q1's two quality controls left open for a WP6.5 Mac measurement, the AD-12 rate-rule mapping, 10-bit conversion); the per-platform pipe strategy (section 6: the OS default pipe on macOS per AD-23's fallback, Q2); the spawn policy on POSIX (P74: `start_new_session` or document); the guard form (if / else, both mypy targets, `uv run mypy --platform darwin` as a Windows-side W test, section 8's `pyproject` platform policy); AD-25(a) for a proposed macOS Library branch (XDG is today's compliant behaviour).
- **Candidate DRs (section 13):** (1) APFS queue identity through case aliases, minor; (2) the older tools' footage-containment checks through case aliases (`inventory.py:1112` / `:1155`, `lookcheck/frames.py:161`, `container_spike/compare.py:1877`, `analysis_breakdown.py:984`, `export_oracle.py:645`), MAJOR for the footage-is-read-only rule on a case-insensitive volume; (3) the Mac binary licence evidence in `spike_io/licences.py`, minor; (4) start-up test isolation when a Library resolver lands, conditional. Also B1 (preset rename on POSIX, a DR-34(a) extension or a new candidate). None is a Windows defect today.
- **Owner-reserved item:** spec G12's "auto (NVENC when available, else the software encoder)" wording on a Mac (P-row for `gui/settings_dialog.py:95`): an item for the owner through CHARC, not a text change.
- **Pending from WP6.1:** the rows marked "arriving with WP6.1" (`gpu_pack.pack_root()` Q6, the frozen PATH prepend D1, `os.add_dll_directory` D2) are cited from the brief's rulings; their file:line lands with WP6.1's accept.
- Report limits carried: no Mac; every macOS claim DOC (with its source) or REASONED; the FFmpeg VideoToolbox source claims unverified offline by both nets.

## Merge

Harness gate on `6d80c835` (this record's first commit, the report unchanged since `2243da6b`): `uv run python -m unittest discover -s tests/harness` -> Ran 423 tests, OK (skipped=40); no registration needed for the two new files. `main` fast-forwarded to `wp6.2` (the merge `4380d156` plus this record's commits) by the orchestrator. The worktree `.worktrees/wp6.2` is released after the merge (its `work/` pruned only on the owner's word; it holds only a reviewer-created `.venv`).
