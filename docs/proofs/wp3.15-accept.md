# WP3.15 — Accept record (presets, settings and logging: `clearwater.config`)

**Accepted 2026-10-20 by the orchestrator** (generation 5, session
`clearwater-orchestrator-20261020-0802`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 1 of Phase 3 (frame `docs/briefs/wp2.4-phase3-frame.md`).
- Brief approval and rulings: CHARC `871a371855bb1630`. Round-0 rulings (orchestrator) upheld
  with one addition (the import result NAMES the dropped provenance keys): CHARC `799b83d4fe11bed8`.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.15-brief.md` (FINAL `e357e56`). Spec v0.5.4, architecture FINAL 1.0. |
| Base SHA | `9735282` |
| Author heads | `51c0e9e` (Reviewer A converged at R2, cleanup, report); `21c5c04` (the ONE Reviewer B remediation). |
| Cell and depth | **`wp315-cell`** (implementer-sonnet-high): 0 at dispatch; 83,816 / 15 turns at the R0 yield; 145,492 / 34 at the build yield; 176,725 / 57 at the R1 yield; 205,539 / 75 at the R1-remediation yield; 217,080 / 87 at the R2 yield; 237,714 / 101 when the Reviewer B remediation was ordered; 245,842 / ~105 while remediating. Never past 250K at an order. |
| Merged head | `wp3.15-mc` = `21c5c04` rebased onto main `4f122ec` (`6a3ba24`), first of a three-package stack (WP3.15 -> WP3.13 -> WP3.7); plus this record, the report erratum and DR-34. Main fast-forwarded. CHARC held main from the stacked gate to the merges. |
| Byte identity | `git patch-id --stable` = `b9f94b87b16e...` on `9735282..21c5c04` and on `4f122ec..6a3ba24`. (Pass-1 candidate `b051c3d`: `a39f42559f8b...` on both ranges.) |
| Gates on the candidate | `ruff check` clean; `ruff format --check` 78 files; `mypy` strict 54 files clean (on `6a3ba24`). Full pytest on the stack top `d898157` (which contains this package unchanged): **1671 passed, 1 warning (CuPy CUDA_PATH), 599 s, exit 0** (basetemp `work/pt-stack` in `.worktrees/wp3.7-mc`). Harness gate not required (no harness path touched). |
| Gates on main | Main is gated ONCE, at the stack's final head, after all three fast-forwards and accept commits: see `docs/proofs/wp3.7-accept.md` "Gates on main" (the intermediate heads each carried this candidate gate; CHARC `99e73cf967e2d559` accepted the stacked form). |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1 on `703f7d9`: 2 major / 3 minor, all REASONED (no uv in the sandbox), all reproduced by the cell, fixed in `01591af` (10 regression tests fail on the unfixed source). R2 on `01591af`: `NO_NEW_CRITICAL_MAJOR`, 4 minor, fixed as cleanup in `9410d6a`. No reverts. Evidence `clearwater-review-evidence\wp3.15\r1`, `r2`. Full pytest at the cell's seat: 1320 (`703f7d9`), 1336 (`01591af`), 1341 (`51c0e9e`). |
| Reviewer B | Pass 1 on `b051c3d`: `NEW_CRITICAL_MAJOR_FOUND` (2 major, 3 minor); ONE remediation `21c5c04`. Re-run on `6a3ba24`: `NEW_CRITICAL_MAJOR_FOUND` (2 major, 1 minor), the second blocking B, adjudicated at the gate NOT BLOCKING (below; DR-34). |

## The package

`src/clearwater/config/` (`paths`, `atomic`, `keys`, `migration`, `settings_store`, `presets`,
`log`) and `tests/test_config_*.py`; report `docs/reports/wp3.15-presets-settings-logging.md`
(the public API table for WP3.12, WP3.14, WP3.16, WP3.17, WP3.20). Stdlib only; nothing in
`src/clearwater/interfaces/` or `pyproject.toml` changed. X2 met: `config.paths` committed at the
round-0 yield (`cde09a2`). DR-32 CLOSED at the config boundary (every entry point tested with a
NaN key and an int key at depth); residual: a direct `ParameterSet.from_dict` caller.

Rulings applied (orchestrator, upheld by CHARC): extra file `config/atomic.py`; provenance keys
`source`/`settings` stripped on preset save and import and NAMED in `dropped_keys`, every other
unknown key refused; 1 MiB preset cap; macOS on the XDG branch; no developer override; preset
name cap 237 UTF-8 bytes (the cell's correction of "255": 255 less `.json` less the atomic
temporary's 13-byte tail).

## Reviewer B

**Pass 1** (on `b051c3d`). `clearwater-review-evidence\wp3.15\reviewB\review-B.txt` md5
`ac10f64e719ef23da504f4bc5307000d`; stderr `5f1ac6fc`; prompt `2566f526`; diff `8127c205`;
`md5s.txt` beside them. Assertions: banner gpt-5.6-sol / high; `^ERROR` 0; `tokens used` footer;
12 `succeeded in`; VERDICT anchored (line 67); ledger mentions are path text only (diff, brief).
- B#2 MAJOR, UPHELD (introduced, in envelope, EXECUTED): `save` wrote a preset above the 1 MiB
  read cap, which every later read refused (stranded preset).
- B#1 MAJOR as classed, DOWNGRADED to minor: export with `overwrite=True` to a caller-chosen path
  is the GUI's confirmed "save as" (intended); the real defect was `Path.exists()` treating a
  dangling symlink as free.
- B#3, B#4, B#5 minor: a decoder `ValueError`/`RecursionError` escaping recovery; a non-dict
  migration step; C1 controls in names.
- ONE remediation `21c5c04`: one serialiser refuses an over-cap preset before any write (save,
  overwrite, import, starters, export); `os.path.lexists`; the decoder errors take the normal
  corrupt-file paths; `FormatError` for a non-dict step; the whole Unicode Cc category refused.
  14 new tests fail with `src/` stashed and pass on the fix.

**Re-run** (on `6a3ba24`). `...\wp3.15\reviewB2\review-B.txt` md5
`aaef405375051bcfdf34c3e334c79eec`; stderr `17172079`; prompt `b72d8c27`; diff `c3d32089`.
Assertions: banner gpt-5.6-sol / high; ONE `^ERROR` line, `Reconnecting... 2/5`, at stderr line
3372, BEFORE the model's first output, after which the session ran in full -- classified a
recovered transport retry, the pass is complete; `tokens used` footer; 10 `succeeded in`; VERDICT
anchored; ledger mentions are path text only.
Adjudicated at the gate by irreversibility (fill Part 2: no third remediation):
- **B2#1 MAJOR (REASONED), NOT UPHELD -- refuted by execution at this seat.** The claim: NTFS
  case folding differs from Python `casefold()` (dotless i U+0131 vs `I`) and 8.3 aliases, so
  `save`/import with `overwrite=False` could `os.replace` an existing preset. On this machine's
  NTFS `C:` (scratchpad probe): with `ı.json` present, `os.path.exists("I.json")` is False,
  and `os.replace(tmp, "I.json")` left both files intact. 8.3 short names are enabled
  (`longpresetname.json` answers to `LONGPR~1.JSO`), but `LONGPR~1.json` does not resolve, and the
  store always appends `.json`, which no 8.3 alias ends in. Residual advisory banked (DR-34 a).
- **B2#2 MAJOR (REASONED), DOWNGRADED to minor and BANKED (DR-34 b).** A corrupt settings file
  whose set-aside fails (a dangling symlink at the stamped `.bad` name, or a transient rename
  failure) is replaced by the next save. The trigger needs a symlink at a timestamped name
  (privileged on Windows) or a transient failure; the report states the limit; the loss is a
  corrupt settings file, recreatable from the panel. Not blocking.
- **B2#3 MINOR (EXECUTED), BANKED (DR-34 c)** with an erratum at the gate in the report.

## Erratum at the gate

Appended to the report as "Erratum at the gate (orchestrator)": "at most six files" holds per
configuration; a second same-folder `configure_logging` call keeps the first call's
`max_bytes`/`backup_count` (B2#3).

## Follow-ons

- DR-34 (a)-(c) BANKED; owner CHARC; trigger: WP3.17 (the preset panel) or WP3.20 (settings
  panel), whichever first touches `presets.py` / `settings_store.py` / `log.py`.
- Consumer API: the report's table; WP3.12 depends on this merge (X2).
- Starter values `ParameterSet("c3", {})` until the owner sees them at CP5 (AD-13).
