# WP4.1 accept record (orchestrator generation 17, 2026-10-29)

**Package:** WP4.1, Photo path end to end.
- Brief: `docs/briefs/wp4.1-brief.md` (FINAL; Rulings CHARC `2c4476d9869df056` govern; S1-S7 ruled at the orchestrator's seat; S8 RULED by CHARC `6c108416f38ca32a`, the AD-11 clarification).
- Lane: **Claude**, `implementer-opus-high`, four seats:
  - cell 1: round 0, the build, the hardware leg and R1 with its remediation; stood down at ~336K;
  - cell 2: one report fix and the R2 preparation; stood down at 66,183;
  - cell 3: R2, R3 and the R3 minors; stood down at 238,831;
  - cell 4: R4, R5, the report FINAL and the Reviewer B remediation; stood down at 283,239.
- Both nets: the CODEX pass (gpt-6.1-sol / high, read-only).
- Report: `docs/reports/wp4.1-photo-path.md`. Ledger: `docs/proofs/wp4.1-ledger.md`.

**Candidate:**
- Branch `wp4.1-mc3`: the author branch `wp4.1` (`3b8b43b`, base `3aa3c51`, never rebased by a cell) rebased with `git -c core.autocrlf=false` onto main `4933a45` (WP-T5's accept).
- One docs-only Erratum commit `96d72c7` on top, then this record.
- **`git patch-id --stable` `8ff10e7b`** on `3aa3c51..wp4.1` and on `4933a45..0b3b466`; `96d72c7` is the Erratum on top.
- **Code identity with Reviewer B pass 2's tree** (`wp4.1-mc2` `0986b8d`): `git diff wp4.1-mc2 wp4.1-mc3` over `src`, `tools` and the six WP4.1 test files is EMPTY.
- Main's moves since the base are docs plus WP-T5's two test files, which WP4.1 does not touch.

**Footprint (checked at this seat; 12 files plus this record):**
- **Package code, new:** `src/clearwater/app/__init__.py`, `src/clearwater/app/composition.py` (the composition root); `tools/headless_export.py` (the headless runner).
- **Package code, edited:** `src/clearwater/gui/engines.py` (`default_engines()` takes its photo source and methods from the root; the one gui-to-app edge).
- **Tests, new:** `tests/test_app_composition.py`, `tests/test_headless_export.py`, `tests/test_wp41_photo_path.py`, `tests/test_wp41_v8.py`, `tests/test_wp41_gui.py`; plus `tests/test_app_deps.py`, GRANTED at round 0 (S4).
- The report and the ledger.

**Locks, all held:**
- `src/clearwater/interfaces/`, `gui/contract.py`, `jobs/`, `io/`, `methods/`, `core/`, `config/`, `pyproject.toml` and `uv.lock` are UNCHANGED against main.
- No existing test was edited.
- No new dependency.
- Every changed blob has 0 CR bytes.
- The footage folder was never written; every footage case used a stand-in under `work/` or `tmp_path`.
- Nothing footage-derived is committed; no `gpmd`, IMU, GPS or location tag was read or committed.

## Nets

| Net | Result |
|---|---|
| Reviewer A, rounds 1-5 (Codex at the cells' seats, STRONG; evidence `wp4.1\r1\`..`r5\`) | R1 `ef6bf2f` 0/2/6; R2 `dca6d1e` 0/2/5; R3 `899102d` 0/1/6 (H1 BANKED to WP4.3, CHARC `5fab48cc2a5174cb`); R4 `844b996` 0/1/4; **R5 `f17ab36` 0/0/1, `NO_NEW_CRITICAL_MAJOR`**, at the FIVE_ROUND_GATE. J1 was fixed in the terminating cleanup `23fc88b`. Start-up websocket reconnects in R2 and R5 count: the session ran to completion, VERDICT anchored. The design guard was set at R4 and did not fire at R5. |
| **Reviewer B pass 1** (Codex at this seat, on the stacked candidate `aefd563`; `wp4.1\reviewB\`) | 4 major reported / 4 minor / 1 advisory, BLOCKING. Run checks: banner gpt-6.1-sol / high; 23 `succeeded in`; only `codex_models_manager` refresh ERRORs; exclusion globs only. md5 `review-B.txt` `bc970e456fc5f11fb596c3749b2de4a6`. **B1 MAJOR, EXECUTED at this seat** (`b1_probe.py`): a `--record` given as a hard link plus stream syntax created an NTFS stream on a stand-in original. B2-B4 were adjudicated MINOR; B5-B9 MINOR/ADVISORY. CHARC `870c8ddeb64b4e12`: Q1 (A), ONE positive write-target predicate (no `:` after the prefix and no `\\?\` / `\\.\` form; every existing ancestor its own realpath; the deepest existing ancestor's realpath outside the footage folder), the residual a Limit, and the design guard CLOSES; Q2, one bounded remediation by cell 4 (`7003de7`, `b488b22`, `3b8b43b`; 8 new tests RED first, 5 regression pins). |
| **Reviewer B pass 2** (Codex at this seat, `wp4.1-mc2` `0986b8d`; `wp4.1\reviewB2\`, with a "THIS IS THE RE-RUN" section) | 1 major / 3 minor, BLOCKING. Every pass-1 remediation held. Run checks: banner gpt-6.1-sol / high; 31 `succeeded in`; the websocket reconnect came before the first turn; exclusion globs only. md5 `review-B.txt` `ab4c5c6917010bfc484ed6f73537099f`. **Adjudicated AT THE GATE** as the second blocking B, by irreversibility, and UPHELD by CHARC `80bbf403266651df`: B2-1 (stream syntax reaching a planned output FILE name through a source stored in a stream, plus a hard link in the output folder) BANKED to WP4.2 with the Limit, no seventh patch; B2-2, B2-3 and B2-4 MINOR, banked to WP4.2. Both are recorded in the report as an Erratum at the gate (`96d72c7`). |
| Hardware leg (cell 1, window, `755513b`) | gpu + V8 (c): passed, 28 s; V8 (c) inside the AD-11 bounds (the report's table). |
| Stacked gate (this seat, stack top `aefd563` = WP-T5 + `0a0a787`; WP-T5's accept) | PARALLEL 4473 passed / 1 skipped, 616.56 s; SERIAL 1126 passed / 1 skipped, 2,511.76 s; both EXIT 0. It does NOT stand for WP4.1, which took commits after it (CHARC condition 3). |
| **Own two-leg gate** (this seat, `wp4.1-mc3` `96d72c7`, main `work/` config) | PARALLEL `uv run pytest -q -rs -n 4 -m "not gpu and not footage and not gui and not slow" --basetemp=work/wp41-gate-parallel`: **4486 passed, 1 skipped**, 616.12 s, EXIT 0 (00:40:05Z-00:50:23Z); skip `test_color_roundtrip.py:121`. SERIAL `uv run pytest -q -rs -m "gpu or footage or gui or slow" --basetemp=work/wp41-gate-serial`: **1126 passed, 1 skipped, 4487 deselected**, 2,431.06 s, EXIT 0 (00:50:23Z-01:30:56Z); skip `test_photo_check.py:139`. Both skips are exactly the standard gate's. 4,486 = the stack top's 4,473 + 13 Reviewer B remediation tests. Git Bash, `PYTEST_ADDOPTS` unset, offscreen; free memory 10.7 GB before. |
| Static (this seat, candidate) | `ruff check .` all checks passed; `ruff format --check .` 259 files already formatted; `mypy` no issues in 141 source files. |
| Harness gate (this seat, candidate with this record) | `uv run python -m unittest discover -s tests/harness`: Ran 382 tests, OK (skipped=1). |

**Banked and owed (for CHARC's register at this accept):**
- **H1 -> WP4.3, BINDING** (CHARC `5fab48cc2a5174cb`, four conditions): the GUI preview of an nclx-only Display P3 photo is shown unconverted. Preview (199, 40, 60) vs (217, 0, 54) through the D53 built-in; reproduction `wp4.1\r3\`. The WP2.3 fixture gap goes in the same row. WP4.3's brief carries the test under Q12 as REQUIRED.
- **B2-1 -> WP4.2, BINDING:** apply predicate (i) to every planned output FILE path, or refuse a source path carrying stream syntax; RED test on a stand-in hard link.
- **B2-2 / B2-3 / B2-4 -> WP4.2, MINOR** (trigger: WP4.2's touch of the runner and its tests): the quoted-apostrophe redaction spelling; a symlink loop as `--out` crashing before the refusal handling; signed zero in the pre-encode checks.
- **G5 (CHARC's):** the writer's HEIC provenance `"profile"` key vs AD-13's key set. The accepted importer refuses it, as the runner does.
- **The importer `OverflowError`** (accepted `PresetStore.import_preset`, J1's twin; reproduction `wp4.1\r5\r5_repro.py`): recommended trigger WP4.3.
- **OWED** (the report): the owner HEIC V5/V9 and AD-24 legs, the 48 MP photo (V15), DR-42 (a) on real files, the viewers (WP5.1). The runner command for each is in the report.

**Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp4.1\` (`r1\`..`r5\`, `reviewB\`, `reviewB2\`, each with `md5sums.txt`). Gate logs: `.worktrees/wp4.1-mc3/work/wp41-gate-*.log`.
