# WP4.3 accept record (orchestrator generation 26, 2026-10-30)

**Package:** WP4.3, Application wiring: `python -m clearwater` on the real engines, the one proxy cache per process, start-up and the leftover journal, the analysis adapter, DR-62 / DR-82, the settings dialog's DR-52 / DR-61, the preview's DR-68 / DR-75, the G-matrix, V7, V8, V11, V18.
- **Brief:** `docs/briefs/wp4.3-brief.md`, FINAL, REVISION 1 (CHARC `7c7df3dbe237ceb7`, main `101f181`; Rulings `2c4476d9869df056` govern Q1-Q13, `7c7df3dbe237ceb7` Q14-Q24). The Q14 split moved the AD-23 spawn helper, DR-58 (b), DR-81, DR-76, DR-77 and DR-85's fix to WP4.3a (accepted `649be3d`).
- **Later rulings** (each verbatim in the ledger or saved under `clearwater-review-evidence\wp4.3\`): round 0 `fcb2a9205c060013` (S1-S7, S-order); build `68d5b4c7a6a2fbc2`; R1 `d530b564a0b41b2b`; R1-13 `ace08fbbb645c856` (V8 fixture p99 recorded; DR-89); R2 `38a7c702a4cae38a` (R2-3 narrow grant on `gui/settings_dialog.py`; DR-90); R3 `d6e9abdfa16feb0e`; window 3 `1f519331`; the V7 remediation step `7b32521f060044d9` (items 1-3; the `gui/jobs.py` / `export_panel.py` grant GRANTED and NOT USED); ruling B `b9a0ce010581a296` ((f) probe from `show()`); R5 `cc0703a79f98154e`; R6 `424f573b88b5a203` (THE CAP, no R7); window 4 `921babda38ba1f3a` (item 3 REVERTED; switch interval NOT adopted; (c)/(e) OPEN; V8 video bound re-ruled); `95392965dc5f8a6c` (that re-rule is the video leg's only; the stills' `P99_BOUND` unchanged); Reviewer B `775d01481eb159b5` (B-1 REJECTED BY RULING; the cleanup's scope); the re-run `b0d679b06033a23b` (cell 13's five fixes; no third B).
- **Lane: CLAUDE**, `implementer-opus-high`, thirteen cells (seats) in sequence, each re-dispatched from the ledger's RESUME HERE. Both nets Codex `gpt-6.1-sol`/high, the other model. Per-cell work and depth readings are in the ledger. This generation's: cell 11 (the report) 138,331, cell 12 (B's cleanup) 133,481, cell 13 (the re-run's fixes) 98,187, each read at its yield.
- **Report:** `docs/reports/wp4.3-application-wiring.md`. **Ledger:** `docs/proofs/wp4.3-ledger.md`.

**Candidate:** `wp4.3-mc` `dbefb96` = the author branch `wp4.3` (`f342f9d`, base `5e3537d`) rebased onto main `d6cd877` (`d9a29c9`), plus cell 11's report commit cherry-picked (`483cb8c` -> `b64e0c1`), cell 12's thirteen commits and cell 13's seven, then rebased onto main `f78e92c` (WP-DR87's accept). `git patch-id --stable` over code and tests (excluding `docs/proofs` and `docs/reports`): `11a91ba5` before and after the last rebase. The author-branch range `5e3537d..f342f9d` and the first rebase gave `7d052cf7` on both sides.

**Footprint** (`git diff --name-only f78e92c..dbefb96`, 30 paths): `src/clearwater/__main__.py`; `src/clearwater/app/` (`__init__.py`, `activity.py`, `analysis_adapter.py`, `composition.py`, `main.py`, `startup.py`); `src/clearwater/gui/` (`engines.py`, `preview.py`, `render_worker.py`, `settings_dialog.py` under R2-3's grant, `shell.py` under S3 and R1-16); `src/clearwater/jobs/` (`__init__.py`, `export.py`: the public `expected_frames`); the tests `tests/test_app_*.py`, `tests/test_gui_settings_dialog.py`, `tests/test_gui_status.py`; `docs/reports/wp3.20-settings.md` (an erratum); the report, the ledger and this record. No `src/clearwater/interfaces/`, `gui/jobs.py`, `gui/export_panel.py`, `io/`, `config/`, `cache/`, `core/` or `tools/` change; no `pyproject.toml` or `uv.lock` change; no dependency. Every changed blob has 0 CR bytes.

## V7, V8, V18 of record (the report's section, the windows' logs)

| Scenario | Figure of record (longest / p99) | Window, head | Verdict |
|---|---|---|---|
| (a) analysis | 18.0 / 15.0 ms | 5, `8eaa897` (product `7b4c10b`) | PASS |
| (b) scrubbing during it | 19.0 / 15.0 ms | 5 | PASS |
| (c) File > Export | 180.0 / 12.0 ms (5 ms switch interval); 181.0 / 12.0 (1 ms) | 4, `b4c8561` | **OPEN STOP** (CHARC `921babda` Q3) |
| (d) 300-still batch (DR-50) | 56.0 / 43.0 ms | 5 | PASS |
| (e) 1:1 4K render during (c) | 182.0 / 12.0 ms (5 ms); 80.0 / 12.0 (1 ms, one sample) | 4 | **OPEN STOP** |
| (f) start-up from `show()`, settled 20 GB cache | 50.6 / 14.8 ms | 5 | PASS |

(c)/(e): the cause is in-process GIL contention with no single holder (windows 3-4). The follow-on is WP4.6, export process isolation (CHARC's brief). V8 video at k = 2 on GX011627: per frame mean <= 1/255, p99 <= 2.5/255 (window 3: frame 510 p99 2.011/255; window 4's 16 frames: max 1.946/255); the stills' bound is unchanged at 2/255. V18 and DR-44 (c) on GX011627: window 3 (analysis close 361 ms, export 218 ms, batch 262 ms). Driver `s7_driver.py` md5 `0b9ee6cc...`, uncommitted (S7); every window EXCLUSIVE.

## Nets

| Net | Result |
|---|---|
| Reviewer A, R1-R4 on the whole package (cells 3-6; `clearwater-review-evidence\wp4.3\r1\`..`r4\`) | R1 0/5/11, R2 0/3/6, R3 0/2/3 (after CHARC's reclassification of R3-2), each remediated under its ruling; **R4 NO_NEW_CRITICAL_MAJOR 0/0/2, converged** (R4-1, R4-2 fixed test-only). |
| Reviewer A, R5-R6 on the V7 remediation step (cells 9-10; `r5\`, `r6\`) | R5 0/3/4 (R5-2, R5-3 reclassified MINOR), all seven fixed RED-first; R6 0/1/3 (R6-1 reclassified MINOR), R6-2..4 fixed; **THE CAP** after R6 (CHARC `424f573b`: R6 was the step's last round; the remaining findings were minor). Item 3 and every R5/R6 follow-up of it were then REVERTED (`921babda` Q1). The round count, six, exceeds the fill's five because R5/R6 reviewed a new step after R1-R4 converged. |
| **Reviewer B** (my Codex pass at this seat, on `wp4.3-mc` `d9a29c9`, base `d6cd877`; neutral prompt: R4's whole-package claims, the V7 step, R5-1..7 / R6-1..4 and the revert named per `424f573b`; the report and the ledger WITHHELD; `clearwater-review-evidence\wp4.3\reviewB\`, `md5sums.txt`) | **NEW_CRITICAL_MAJOR_FOUND, 1 / 10 / 4**, probe READY, banner `gpt-6.1-sol` / high, 246,223 tokens, 32 executions, ERROR lines client-side only. **B-1 MAJOR REJECTED BY RULING** (CHARC `775d0148`: the brief's Q3 ruling, D34, D85, N8; the product has no footage-folder concept). Its three probes: the start-up clean-up admits an output or journal folder inside a stand-in originals folder; an export beside a source there; app data routed under it by the OS root (out of envelope). My prompt left Q3 out of its "Accepted by ruling" list: my slip, recorded. The minors went to cell 12 as ruled: B-7 (product, RED-first), B-3, B-4, B-5, B-6, B-15 (tests), B-9..B-12 (docs and a name), the report's Limit lines for B-2, B-8 (declined), B-13; B-2 and B-14 BANKED (CHARC's rows). |
| **Reviewer B re-run** (narrow, on cell 12's cleanup `b64e0c1..f644488`; the 15 items, their dispositions and Q3 named; `clearwater-review-evidence\wp4.3\reviewB2\`, `md5sums.txt`) | **NO_NEW_CRITICAL_MAJOR, 0 / 0 / 4 / 2**, probe READY, banner ok, 81,626 tokens, 21 executions, ERROR lines client-side only. Items 1, 3, 4, 5 and 6 FIXED by cell 13 (CHARC `b0d679b0`). Item 1: one product line, B-7 iterates once; RED `d292449` failed `[unlistable-on-iteration]` at its parent. Item 2 ACCEPTED (two facts, two lines), pinned by `[unlistable-and-journaled]`. Item 3's locked-counter form is a seat ruling, CONCURRED by CHARC. No third B (the fill's single re-run is spent and returned clean). Cell 13's diff `f644488..2407f9e` is the only code after the re-run, and it is reviewed by the gate only. |

## Gate

The ONE two-leg gate, on `dbefb96` (base `f78e92c`), run id `wp43g1`, Git Bash, `PYTEST_ADDOPTS` unset, offscreen, the local config copied. The candidate was then rebased onto CHARC's later docs-only commits on main for the merge; the code patch-id is unchanged.
- **Static:** `ruff check` clean; `ruff format --check` 287 files already formatted; `mypy` no issues in 146 source files; 0 CR bytes in every changed blob.
- **Collection:** all 7,269 = parallel 6,044 + serial 1,218 + fullclip 7; no duplicates, pairwise disjoint, union = all. Against main `9ae9bf9`'s 7,117 (which lacks WP-DR87's two tests): +158, -6. Each removed ID is a deletion the brief orders:
  - `tests/test_app_deps.py::test_no_app_module_imports_the_gui_or_qt`: Q2, only `app/main.py` loads Qt, so the rule is replaced by the ordered edit;
  - three `tests/test_gui_settings_dialog.py` interim-rule tests (`test_interim_rule_matches_the_wp310_rule` and `test_auto_is_resolved_by_a_rule_that_disagrees_with_the_interim_rule[injected-*]`): DR-52, the dialog uses WP3.10's `resolve_encoder`, so the interim rule is gone;
  - `tests/test_gui_status.py::test_default_engines_select_cpu_forced_with_the_real_selection` and `::test_stub_era_adapter_estimates_an_unknown_method_as_c3`: Q11, the stub-era selector and the two S1 stand-in tests are deleted.
- **PARALLEL:** **6,043 passed, 1 skipped** (the standing swscale refusal), EXIT 0, 857.43 s (03:41:51Z-03:56:10Z).
- **SERIAL:** **1,207 passed, 11 skipped, 0 failed**, EXIT 0, 1,931.31 s (to 04:28:24Z). The skips are the standing look-check frames (archived to D:): 10 as at WP-DR87's gate, plus `tests/test_app_v8_v18.py:134` (this package's real-sized V8 photo leg, the same absent frame). The DR-99 node passed.
- No harness gate (no harness file changed). No `fullclip` leg (a per-package gate; the brief asks for none). The V7 / V8 / V18 figures of record are the EXCLUSIVE windows' (above), not the gate's.

## For CHARC at the release

Rows and notes owed by CHARC at this accept (its consolidated list, `775d0148`):
- the brief's register table;
- DR-89 and DR-90;
- DR-44 (c) and DR-50 CLOSED;
- the R6-1 residual VOID (the policy is reverted);
- NEW DR-98 (V7 (c)/(e) OPEN, trigger WP4.6);
- NEW rows for B-2 (a source matching WP3.13's temporary pattern beside which an export ran is removed at the next start) and B-14 (`Application` keeps the last video's adapter and engine while a photo is open);
- the AD-11 note ("video at k = 2: p99 <= 2.5/255 per frame (mean <= 1/255; p99.9 and max recorded); stills unchanged at 2/255");
- the switch interval not adopted;
- the `gui/jobs.py` / `export_panel.py` grant not used;
- B-1 rejected by ruling with its probes;
- the AD-23 "applied by WP4.3" note, if not already written at WP4.3a.
