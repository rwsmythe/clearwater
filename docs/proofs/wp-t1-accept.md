# WP-T1 — Accept record (pytest temp-root footage guard; closes DR-21 and DR-9)

**Accepted 2026-10-15 by the orchestrator** (session `clearwater-orchestrator-20261014-1258`),
on CHARC's commission `5a9d76593e090e89` and ruling `839cce617611bf08`. Gate per
`docs/review-gate-clearwater.md` Part 2 (corrected `30483f2`).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp-t1-brief.md` (FINAL `34d2ccd`); remediation `docs/briefs/wp-t1-remediation-brief.md` (`c17b45d`). |
| Base SHA | `34d2ccd` |
| Author head | `9dce60c`; after the remediation `eacee2e` (`wpt1-cell`, implementer-sonnet-high; 142K at the first return, 196K after the remediation). |
| Merged head | `f6a34a4` (`wp-t1-mc` = `wp-t1` rebased onto main `c17b45d`; main fast-forwarded). |
| Byte identity | `git patch-id --stable` = `ebcd87bc96c87a291ae8979b7ddd1ee45cb02f08` on `34d2ccd..eacee2e`, on the candidate and on main `c17b45d..f6a34a4`. The first candidate `cd38111` was `1cb90287...` on both sides. |
| Reviewer A | Codex STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1. One counted round (a first run was void: one output file overwrote the banner; it was re-run with separate files). 1 critical (the pre-conftest capture writes, confirmed EXECUTED by the cell's audit hook), 5 major, 1 minor; three fixed, two rejected with cause, one kept by design. Ledger `docs/proofs/wp-t1-ledger.md`; evidence `clearwater-review-evidence\wp-t1\r1\`. |
| Tier | STRONG. The fill has `strong` and `fast` only; the "STANDARD" in my query and in CHARC's answer is not a fill tier. |
| Reviewer B | My own seat passes: pass 1 on `cd38111`, BLOCKING; ONE remediation by the author; re-run on `f6a34a4`, BLOCKING; the second block was adjudicated at the gate (below). |

## CHARC ruling on the residual (`839cce617611bf08`)

Pytest's output capture and CPython's `tempfile` write probe create short-lived, randomly named
files in the TMPDIR/TEMP/TMP directory before any conftest loads, so no conftest guard can
prevent them. CHARC ACCEPTED this as a documented limit, banked as DR-22, with no WP-T1b.

**Claim 1 erratum:** the guard refuses "before pytest creates or clears any temporary FOLDER;
not the TEMP-variable file writes". The conftest docstring and the report carry those words
verbatim.

## Reviewer B pass 1 (seat), on candidate `cd38111`

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp-t1\reviewB\`. Assertions:
- the banner reads gpt-5.6-sol / high;
- `^ERROR` 0; one `ERROR codex_core` hit, an echo;
- footer 1; 12 `succeeded in`;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`;
- no withheld access.

| File | md5 |
|---|---|
| prompt | `91e813d8d0c48fbe4b6793f3b9fa4b97` |
| diff | `a9ec099a2c2fc0fbce33620f5feb97ee` |
| transcript | `44c8c75b3ca0f7ae9418319533c8ba2a` |
| stderr | `cc454caf3f86abae4fd26e8aa6b3396a` |

| # | Finding | Disposition |
|---|---|---|
| C1 | `pytest-of-` matched case-sensitively; a mixed-case junction slipped through. | REMEDIATED: pytest's own child is resolved directly. |
| C3 | A listing `PermissionError` failed open. | REMEDIATED: no listing needed; a check that cannot be made refuses. |
| M4 | Uncached derivation over-refused. | REMEDIATED (`os.access` approximation; see re-run 1). |
| M6 | Missing tests for the ordering paths. | REMEDIATED (`tmpdir`, session factory, `-s`, `-p no:capture`, `--collect-only`, `--setup-plan`, `--cache-clear`). |
| 7-12 | Minors and an advisory. | REMEDIATED (text and the skip reason). |
| C2 | A disconnected mapped drive aliased by UNC. | BANKED, DR-22(2). The deployed footage path is local. |
| M5 | A configured but missing footage path still guards. | REJECTED by design (fail-safe); pinned by a test. |
| A13 | `-c` with another ini file. | BANKED, DR-22(3). |

## Reviewer B re-run (seat), on candidate `f6a34a4`

Evidence `...\wp-t1\reviewB\rerun\`. Assertions:
- the banner reads gpt-5.6-sol / high;
- `^ERROR` 0;
- footer 1; 25 `succeeded in`;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`.

`ERROR codex_core` hits:
- one echo of the prompt;
- one genuine `codex_core::session: failed to record rollout items` line, written after the
  verdict. It is Codex's own session bookkeeping, not a transport or content-filter line, so the
  pass stands.

Accesses: one `rg --files` carrying a `!docs/proofs/**` exclusion; no withheld access.

| File | md5 |
|---|---|
| prompt | `df643a8ff3617aee8180dfcee0228aae` |
| diff | `6bcc69745c97c761f7025b56af41b20f` |
| transcript | `e1af93fa84699fcaed18fa7b081bf10f` |
| stderr | `11c90f42aaedecb03d15a11cb1ace1e8` |

This is the package's SECOND blocking B, so it is adjudicated at the gate by irreversibility,
with no third remediation. **Common ground for findings 1-4:**
- Each needs a deliberately constructed state that names or aliases the footage folder:
  - a special DACL on a temp candidate, with capture off;
  - a junction with denied resolution in the configured footage path;
  - the footage folder placed inside pytest's own `pytest-of-<user>` tree under a volume-GUID
    root;
  - an explicit `-o cache_dir=<footage> --cache-clear`.
- The deployed footage path (`C:\Users\rwsmy\clearwater-footage`) is a plain local folder,
  with none of these.
- The package only removes risk. Before it, every one of these paths, and the plain
  `--basetemp=<footage>` case, was open; none is opened by the guard.

| # | Finding | Disposition |
|---|---|---|
| 1 | CRITICAL (reasoned): `os.access` can accept a candidate that CPython's real write probe rejects, so the guard stops early and misses the root CPython picks. This needs capture off and a deny-create ACL. | **NOT BLOCKING.** It needs a crafted ACL; with capture on (the normal run), the real cached `tempfile.tempdir` is checked. DR-22(4); the report's "never missed" sentence is corrected (erratum). |
| 2 | CRITICAL (reasoned): non-strict `resolve()` and ignored `samefile` errors fail open for a footage path behind a resolution-denied junction. | **NOT BLOCKING.** The configured footage path has no junction. DR-22(5). |
| 3 | CRITICAL (reasoned): footage inside `<root>/pytest-of-<user>/pytest-0` under a volume-GUID temp root is not matched. | **NOT BLOCKING.** The footage would have to sit inside pytest's own temp tree. DR-22(6). |
| 4 | MAJOR (reasoned): `--cache-clear -o cache_dir=<footage>` deletes the `d`/`v` subfolders; the report claimed `.pytest_cache` only. | **NOT BLOCKING.** It is an explicit command naming the footage, of the same class as `rm -rf`, and outside DR-21's temp-root scope. DR-22(7); report erratum. |
| 5 | MINOR: a stale `pytest-of-unknown` link over-refuses. | BANKED, DR-22(8) (fail-safe direction). |
| 6 | MINOR: the TMP sentence overstates the limit. | Report ERRATUM; the docstring wording goes to DR-22(9). |
| 7 | ADVISORY: the test module docstring says every test is a subprocess. | Report erratum (41 subprocess and 3 in-process tests); docstring DR-22(9). |

**Errata at the gate (report only, text).** The TMP sentence, the `cache_dir` sentence, the
`os.access` sentence, a new "Accepted at the gate" limits entry, and the test count. The
conftest docstring is code-adjacent and reviewed, so it is left unchanged; its two imprecise
sentences are DR-22(9).

## Verification QA (orchestrator seat)

**Gate checks**, on candidate `f6a34a4`, with the WinGet links on PATH:

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 83 files already formatted
uv run mypy                    -> Success: no issues found in 16 source files
uv run pytest -q -rs           -> 539 passed, 1 warning (0 skipped)
uv run pytest -q -m gpu        -> 21 passed, 518 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

The first candidate `cd38111` was also green: 525 passed, gpu 21, harness 366.

**Re-gate on main** `f6a34a4` after `uv sync`: identical (logs `work\wp-t1-main-gate\`).

**Witness, legitimate root on the real configuration.** On the candidate, with the real local
configuration (the real footage folder configured), `--basetemp` under
`work\wp-t1-qa\bt` ran `tests/test_lookcheck.py -k "range or roots"`: **6 passed, exit 0**.
The guard does not refuse a working-folder basetemp. The refused cases are proved only on the
fake folders under `tmp_path` in the 44 tests; by design, none is run against the real folder.

**Locks:**
- Only the four owned files changed.
- `local_config.py`, `pyproject.toml`, `tools/`, `src/`, `scripts/` and `CLAUDE.md` are untouched.
- No test names the real footage folder (grep of the test file).

## Follow-ons

- **DR-21 CLOSED; DR-9 CLOSED; DR-22 opened** with the limits above.
- **CHARC adds the CLAUDE.md "Conventions" line** (per its answer).
