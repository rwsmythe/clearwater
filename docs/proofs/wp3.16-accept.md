# WP3.16 — Accept record (application shell and preview: `clearwater.gui`)

**Accepted 2026-10-21 by the orchestrator** (generation 8, session
`clearwater-orchestrator-20261020-1556`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 2, tranche B; gated alone, after WP3.12 and WP3.6 merged.
- Brief approval and rulings: CHARC `53b752a4d7fac4fc` (ruling 2 the contract frozen at round 0,
  additive only until accept; ruling 3 `pytest-qt` granted). Round-0 ruling: orchestrator gen 7.
  CHARC `d06ed7c969d6249f`: S3 downscale RULED; PySide6-Essentials replaces `pyside6` (AD-18
  amended `d971ee7`). Later rulings: orchestrator gen 8 (in the ledger).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.16-brief.md` (FINAL). Spec v0.5.4, architecture FINAL 1.0, AD-18 as amended. |
| Base SHA | `4b4da9b`; REBASED by the orchestrator onto main `d0f00ee` after WP3.6 merged (the two build commits re-locked with `uv lock`, no hand merge; old head `wp3.16-pre-rebase` `b8fa742`). |
| Author head | `89d8786` (Reviewer A converged at R4; terminating cleanup with the by-name `PhotoReadError` catch; ONE Reviewer B remediation). |
| Cells and depth | `wp316-cell` (opus-high, gen 7): 152,774 / 35 at the R0 yield; 317,238 / 109 at its checkpoint (01:55Z, build complete). `wp316-cell2` (opus-high, gen 8): 68,504 / 18 at the window request (02:02Z); 130,456 / 58 at the R1 yield; 196,112 / 106 at R2; 229,009 / 122 at R3 (one bounded step granted); 266,869 / 147 at the R4 yield (stood down). `wp316-cell3` (opus-high): 138,571 / 55 at the cleanup return; 206,214 / 96 at the B-remediation return. |
| Cross-file edit | `tests/test_conftest_guard.py` (a closed WP-T1 file): `-p no:pytest-qt` on the `-p no:capture` children, granted at R1 F1 (pytest-qt 4.5.0's `pytest_configure` raises without the capture plugin); the guard's coverage of that path shown unchanged. |
| Contract | `clearwater.gui.contract` as frozen at round 0, plus the `JobRunner.run` docstring and ONE additive member, `Session.settings_refusal() -> Message | None` (Reviewer B #5; a panel must not save while it is not None). |
| Merged head | `wp3.16-mc` = `89d8786` rebased onto main `8b38d37` (`54eaafe`), plus this record, the report erratum and DR-43/DR-44; main fast-forwarded to the commit that adds this record. CHARC held main. |
| Byte identity | `git patch-id --stable`, 37 commits: sorted-set md5 `7f42009d1d83baa1bc005ee2b23eea77` on the author range and on `8b38d37..54eaafe`. No CR or NUL in any changed blob. |
| Gates on the candidate | Full pytest on `54eaafe` (`QT_QPA_PLATFORM=offscreen`): **3559 passed, 2 skipped, 2 warnings (CuPy CUDA_PATH; the planted corrupt-EXIF test), 926 s, exit 0** (basetemp `work/pt-mc`); with `cupy` and `cupyx` unimportable **3040 passed, 521 skipped, 1 warning, 633 s, exit 0**. 3559 = main 3440 + 119 GUI tests. Static: `ruff check` clean; `ruff format --check` clean (174 files); `mypy` strict clean (107 source files). |
| Gates on main | On main `a2685cb`, after `uv sync` (pyside6-essentials, shiboken6 and pytest-qt installed; `import PySide6.QtCore` OK, so main's venv did NOT need the Essentials reinstall: it never had the meta-package): harness gate **Ran 366, OK (skipped=1)**; `ruff check` clean; `ruff format --check` clean (174 files); `mypy` strict clean (107 source files); full pytest (`QT_QPA_PLATFORM=offscreen`) **3559 passed, 2 skipped, 2 warnings, 810 s, exit 0** (basetemp `work/pt-main`). |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1 0/2/4 (F6 rejected; F1 the pytest-qt guard failure, granted cross-file fix); R2 0/1/4 (`view_factor` unbounded loop); R3 0/1/3 (render cache keyed by statistics identity; R3-1 banked, consumer note); R4 0/0/3 `NO_NEW_CRITICAL_MAJOR`, CONVERGED; terminating cleanup (R4-1..3, X-B2 by-name catch). Evidence `clearwater-review-evidence\wp3.16\r1`..`r4`. Ledger `docs/proofs/wp3.16-ledger.md`. |
| Reviewer B | Pass 1 on `94c5fd0`: BLOCKING (6 major) -> ONE remediation -> pass 2 on `54eaafe`: BLOCKING (3 major), ADJUDICATED AT THE GATE. |
| Full-suite window at the cell's seat | `0e4412c` (02:02-02:28Z): 1 failed (the pytest-qt guard, R1 F1), 2993 passed; 1 failed, 2474 / 520 with CuPy unimportable. Not counted; fixed by `fa99105`. |

## Reviewer B

Pass 1 on `94c5fd0` (`clearwater-review-evidence\wp3.16\reviewB\`, md5s in `md5s.txt`): 0 `^ERROR`;
21 `succeeded in`; tokens 212,230; VERDICT anchored; withheld paths only in exclusion globs.
`NEW_CRITICAL_MAJOR_FOUND`. REMEDIATED: #1 a refused open did not invalidate the in-flight open;
#2 shutdown's short-circuit skipped the opener; #5 the contract did not expose a refused settings
file (an additive member); #6 the statistics memo ignored the backend (V8); #3 (MINOR) close
delivers ended jobs before the settings write; #7 the memo cleared on a new source; #8 the settings
refusal names the file; #9 a report sentence. #4 BANKED DR-43 (WP3.6 drops a damaged EXIF block
with a log warning only; no G10 signal). Adjudication `reviewB\adjudication-B.md`.

Pass 2 on `54eaafe` (`reviewB2\`): 0 `^ERROR`; 20 `succeeded in`; tokens 312,945; VERDICT anchored;
exclusions only. Pass-1 #1, #2, #5, #6, #7, #8 CLOSED. `NEW_CRITICAL_MAJOR_FOUND`; adjudicated at
the gate (`reviewB2\adjudication-B2.md`): #1 `set_position` commits before the decode succeeds
(WP3.18's path), #2 message clearing has no owner (WP3.17-3.20's path), #3 a job outliving
`close()` keeps its callbacks (WP4.3's path): NON-BLOCKING, banked DR-44 (a)-(c) with consumer
triggers; #4 and #5 MINOR, errata.

## Erratum at the gate

Appended to the report: close ordering as implemented; the following-dot name check; the DR-44
limits.

## Debt and consumer notes

- **DR-43** NEW (cross-package G10 gap, damaged EXIF). **DR-44** NEW ((a) WP3.18, (b) the
  WP3.17-3.20 briefs, (c) WP4.3).
- Carried: the `fda06b7` subject's "(V7)" overstates its effect (report corrected); a pure-Python
  GIL-holding job gave 216-796 ms interface gaps (out of envelope, for WP4.3's re-measure); R3-1:
  export re-measures with `imaging.measure_statistics` on `downscale(pixels, statistics_factor(H,
  W))` (WP3.14/WP4.1 consumer note); WP3.20 must honour `Session.settings_refusal()`; S1's
  `default_engines` "c3" adapter is removed by WP4.3.
- Any venv that had the `pyside6` meta-package needs `uv sync --reinstall-package
  pyside6-essentials --reinstall-package shiboken6` after this merge (Qt DLL load failure).
