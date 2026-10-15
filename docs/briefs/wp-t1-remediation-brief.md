# WP-T1 — Remediation brief (Reviewer B round 1)

**Issued by the orchestrator 2026-10-15.** This is the ONE bounded remediation that
`docs/review-gate-clearwater.md` Part 2 item 2 allows after a blocking Reviewer B. The author
cell carries it, on the same branch.

| Field | Content |
|---|---|
| Worktree | `C:\Users\rwsmy\clearwater\.worktrees\wp-t1`, branch `wp-t1`, head `9dce60c`. |
| Files owned | The same four as the brief: `tests/conftest.py`, `tests/test_conftest_guard.py`, `docs/reports/wp-t1-pytest-guard.md`, `docs/proofs/wp-t1-ledger.md`. Nothing else. |
| Reviewer B evidence | `C:\Users\rwsmy\clearwater-review-evidence\wp-t1\reviewB\review-B.txt`. You may read it. |
| CHARC ruling in force | `839cce617611bf08`: the pre-conftest capture and tempfile probe files are ACCEPTED as a documented limit (DR-22). Claim 1 reads "before pytest creates or clears any temporary FOLDER; not the TEMP-variable file writes". The conftest docstring and the report must say that in the same words. |

## Findings to close (adjudicated at the gate seat)

| # | Reviewer B finding | Disposition: what to do |
|---|---|---|
| 1 | CRITICAL: `pytest-of-` is matched case-sensitively, so a mixed-case `PYTEST-OF-<USER>` junction to the footage folder is skipped while NTFS resolves pytest's lowercase name to it. | **Fix.** Check pytest's OWN child directly: build `root / f"pytest-of-{user}"` with pytest's own user derivation (cite the line), and resolve and compare it whether or not a listing finds it. Any other `pytest-of-*` match uses `normcase` on the name. Test: a mixed-case junction is refused. |
| 3 | CRITICAL: `root.iterdir()` raising `PermissionError` is swallowed as "no dangerous child" (fail open). | **Fix.** Finding 1's direct check needs no listing. If a check the guard needs cannot be made (an `OSError` while resolving pytest's own child or the candidate root), REFUSE with a usage error that says the check could not be made. Never fail open on the configured-footage path. A listing that fails while the direct check succeeded is not a refusal. Test: monkeypatch or ACL so that the listing raises; the direct child still decides. |
| 4 | MAJOR: with capture off (`-s`, `-p no:capture`), `tempfile.tempdir` is uncached and the guard checks every candidate, so a safe `TMPDIR` plus `TEMP=<footage>` is refused although CPython would pick `TMPDIR`. | **Fix.** Derive the ONE root CPython would pick: use `tempfile.tempdir` if cached; otherwise walk `tempfile._candidate_tempdir_list()` (or your mirror of it) and stop at the first existing directory that `os.access(..., os.W_OK)` accepts. CPython's real test is a write probe, which the guard must not make, so this is an approximation; document it. If any candidate BEFORE the chosen one is the footage folder, still refuse: that is the over-refuse direction, and it is safe. Tests: `-s` and `-p no:capture` with a safe `TMPDIR` and `TEMP=<fake footage>` PASS; `TMPDIR=<fake footage>` with `-s` is REFUSED. |
| 6 | MAJOR: tests are missing for ordering and derivation paths. | **Fix (add, in the subprocess miniature repo):** the `tmpdir` fixture; a session-scoped `tmp_path_factory` fixture; `-s`; `-p no:capture`; `--collect-only` with `--basetemp=<fake footage>` (refused, footage unchanged); `--cache-clear` with the cache provider ENABLED and `--basetemp=<fake footage>` (refused, unchanged). Each refused case asserts that the planted bytes are unchanged and nothing was added. |
| 2 | CRITICAL (reasoned): a configured MAPPED drive that is disconnected, while the same share is reachable as UNC. | **Banked (DR-22), no code.** The configured footage path is on the local disk (`C:`), so the scenario is outside the deployed configuration. The report's limits say that a configured footage path on a mapped or network drive is not protected against aliasing while it is unavailable, and that the guard compares lexically in that state. Remove any report sentence that claims mapped-drive coverage. |
| 5 | MAJOR: a configured but MISSING footage path still refuses a `--basetemp` at that path. | **Rejected by design (fail safe).** Claim 3 makes the guard inert for no configuration, an invalid one, or no footage key, not for a missing folder: a missing folder may be a disconnected drive. Keep the behaviour; state it in the docstring and the report, and add a test that pins it. |
| 7 | MINOR: the test safety helper turns `\\?\Volume{GUID}\...` into a relative path. | **Fix.** Resolve volume-GUID forms properly (or refuse to accept them in the helper); test the helper itself. |
| 8 | MINOR: "nothing here reads the real `clearwater.local.toml`" is false for the containing session (the real conftest's guard reads it). | **Reword:** the SUBPROCESSES never read it; the outer session's guard does, by design. |
| 9 | MINOR: the conftest-loading description is inaccurate (`--rootdir`, `--confcutdir`, `-p no:conftest` versus `--noconftest`). | **Fix the text** in the docstring and the report to match pytest 8.4.2's actual rules, citing the lines. |
| 10 | MINOR: "pytest creates or clears nothing at configure time" is false (`--cache-clear`). | **Fix the text;** finding 6's `--cache-clear` test pins the ordering. |
| 11 | MINOR: "basetemp and debug root are refused before any write" is unqualified, but is false when `TMP` also points into the footage folder. | **Fix the text** with CHARC's claim-1 wording. |
| 12 | ADVISORY: `footage_path` that is a FILE gets the "configured but absent" skip reason. | **Fix:** "configured but not an existing folder". |
| 13 | ADVISORY, out of envelope: `-c <other ini>` without `pythonpath` makes the conftest import fail. | Banked (DR-22). One sentence in the limits. |

## Then

1. **Gates:**
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run mypy`
   - `uv run pytest -q -rs` (0 skipped; WinGet links on PATH)
   - `uv run python -m unittest discover -s tests/harness`
2. **NO further Reviewer A round.** The fill allows one per package, and it is spent. Reviewer B
   re-runs at my seat on the new candidate.
3. **Commit** by pathspec (`fix(wp-t1): ...`, `docs(wp-t1): ...`), with `Co-Authored-By:`
   naming your actual model. Append a "Remediation (Reviewer B round 1)" section to the ledger.

## STOP for

- a fix that needs `pyproject.toml`, `tools/` or any file outside the four;
- any run that would point at the REAL footage folder.

## Return (your FINAL message, under about 50 lines)

- the new head and a per-commit list;
- each finding with what was done and the test that covers it;
- the gate lines;
- the locks.

**Working rules:** never use a bare `cd`; never `git stash`; never post to a mailbox.
