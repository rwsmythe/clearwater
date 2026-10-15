# WP-T1 — pytest temp-root footage guard (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator 2026-10-15 on CHARC's answer `5a9d76593e090e89`
(DR-21: YES, commission now, in parallel with WP1.4). Spec **v0.5.2** (N1 portability; the
footage folder is read-only: CLAUDE.md "Inputs"). Cell: `implementer-sonnet-high` (the brief
fixes the hook, the rule and the tests). Worktree `.worktrees/wp-t1`, branch `wp-t1`, base =
the main commit named in the dispatch. Not exclusive; records no timing.

| Field | Content |
|---|---|
| ID and title | WP-T1 — pytest temp-root footage guard; closes DR-21 (`docs/debt-register.md`) |
| Goal | A pytest run whose temporary root would lie inside the configured footage folder refuses to start, BEFORE pytest creates or clears any temporary folder, so that no `--basetemp`, `TMP`, `TEMP`, `TMPDIR` or `PYTEST_DEBUG_TEMPROOT` setting can make pytest delete or write inside the owner's footage. |
| Files owned | `tests/conftest.py` (the guard plus DR-9's cosmetic skip-reason fix; nothing else in it changes), `tests/test_conftest_guard.py` (NEW), `docs/reports/wp-t1-pytest-guard.md` (NEW, short), `docs/proofs/wp-t1-ledger.md` (NEW). NOTHING else: no `tools/local_config.py` change, no `pyproject.toml` change, nothing under `src/`, `tools/`, `scripts/` or `tests/harness/`. |
| Interfaces consumed | `tools/local_config.py` (`load_local_config`, `LocalConfigError`), as built. |
| Dependencies | None new. |
| Hardware flags | None (no `gpu`, no `footage` marker: the tests use a FAKE footage folder). |
| Done | Plan section 4.5; the four gates green (`uv run pytest -q -rs` 0 skipped, with the WinGet links on PATH as usual); harness gate run and green (it is cheap and `tests/` changes); the report and ledger written. |

## Claims

1. **The hook.** A `pytest_configure` hook in `tests/conftest.py`, marked `tryfirst=True`,
   raises `pytest.UsageError` (pytest exit code 4) naming the footage folder and the offending
   root when the candidate temp root is inside or equal to the configured footage folder.
   It runs before pytest's temp-path factory creates or clears anything. PROVE this ordering
   with the tests in claim 4; do not assume it.
2. **The rule (CHARC, fixed at issue).**
   - Compare FULLY RESOLVED paths (`Path.resolve()`, symlinks and junctions followed), and
     case-insensitively on Windows (`os.path.normcase`), for both the footage folder and the
     candidate.
   - "Inside or equal" means the resolved candidate equals the resolved footage folder or
     has it as an ancestor.
   - The candidate is `--basetemp` if given, resolved against the invocation directory the
     way pytest resolves it.
   - Otherwise it is pytest's default temp root, derived the way pytest derives it:
     `PYTEST_DEBUG_TEMPROOT` if set, else `tempfile.gettempdir()` (which honours
     TMPDIR/TEMP/TMP). Check the derived value, not the variables one by one.
   - Read pytest's own `TempPathFactory` source in the installed version
     (`.venv/Lib/site-packages/_pytest/tmpdir.py`) and cite the lines your derivation mirrors
     in the report.
3. **Inert without footage.** No local configuration, an invalid one, or no footage key: the
   guard does nothing and prints nothing. It must never fail a run on a machine without
   footage (N1).
4. **Tests** (`tests/test_conftest_guard.py`). Each runs pytest in a SUBPROCESS against a
   MINIATURE REPOSITORY built under `tmp_path`:
   - **The tree:** copies of `tools/local_config.py` and `tests/conftest.py` (the real files,
     read from this repository, so the test exercises the code under review); a minimal
     `pyproject.toml` with `[tool.pytest.ini_options]` `pythonpath = ["tools"]`; one trivial
     test that uses `tmp_path`; a `clearwater.local.toml` naming a FAKE footage folder and a
     FAKE working folder, both under `tmp_path`.
   - **The fake footage folder** holds planted files with known bytes, including one in a
     subfolder.
   - **The run:** `sys.executable -m pytest -p no:cacheprovider ...`.

   Cases:
   - (a) `--basetemp` equal to the fake footage folder: refused, exit code 4, the folder named
     in stderr, every planted file's bytes unchanged and no file added.
   - (b) `--basetemp` inside it (an existing subfolder, and a not-yet-existing one): refused
     as (a).
   - (c) `TEMP`, `TMP` and `TMPDIR` all set inside it (no `--basetemp`): refused as (a).
   - (d) `PYTEST_DEBUG_TEMPROOT` inside it: refused as (a).
   - (e) `--basetemp` given as a path that differs only in letter case (Windows) or through a
     symlink or junction to the footage folder: refused. Skip the link variant only where the
     OS refuses to create it, and say so in the skip reason.
   - (f) `--basetemp` inside the FAKE WORKING folder (CHARC: `work/` is a legitimate
     basetemp): PASSES, exit 0.
   - (g) A sibling folder whose name merely starts with the footage folder's name
     (`<footage>-other`): PASSES.
   - (h) No `clearwater.local.toml` in the miniature tree: the run PASSES, with no guard
     output.
   - (i) The repository's own normal run is untouched (the gate shows it).

   **Safety of the tests themselves:**
   - Every path a test sets lies under its own `tmp_path`. Assert that in a helper before each
     subprocess runs.
   - No test reads the real `clearwater.local.toml`, and none names the real footage folder.
   - Build the subprocess environment from `os.environ` with `PYTEST_ADDOPTS`, `TMP`, `TEMP`,
     `TMPDIR` and `PYTEST_DEBUG_TEMPROOT` removed, then set only the fake values.
5. **DR-9 (cosmetic).** The footage-skip reason distinguishes "not configured" from
   "configured but the folder is absent". One test.
6. **Documentation.** The conftest module docstring documents the guard: what it refuses, the
   rule, and that it is inert without footage. The report (one page) states the hook, the
   rule, the pytest lines it mirrors, the limits (for example, a pytest run whose rootdir
   does not load `tests/conftest.py`, such as `pytest` on a path outside `tests/`; say exactly
   when the conftest is loaded) and the test list. CHARC adds one line to CLAUDE.md at accept;
   do not edit CLAUDE.md.

## Declared operating envelope

Windows 11, Python 3.12, the installed pytest (`uv.lock`), NTFS, runs under `tests/` with the
repository's `pyproject.toml`. Out of envelope: other test runners (the harness's `unittest`
suite writes no temp files under pytest's control), pytest plugins that override `basetemp`,
and concurrent processes changing links mid-run.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- **Tier STRONG.** The fill has `strong` and `fast` only. This package guards against the
  one irreversible outcome in the project, so a missed finding has the largest blast radius.
- **ONE round.** Fix minors once; a new critical or major found in the round is fixed and
  stated in the return. Spelled out:
  - **Transport and flags:** WSL, codex-cli 0.162.1. Per-call flags
    `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
  - **Probe:** run one probe through the exact invocation before the round.
  - **Diff:** generated Windows-side with
    `git -C <worktree> diff -U8 <base>..HEAD -- . ':!uv.lock' ':!docs/proofs'`; WSL never runs
    git.
  - **The prompt** includes the claims, the envelope with a request to TAG out-of-envelope
    findings, and the report. It carries the EXECUTED/REASONED paragraph verbatim from
    `docs/codex-reviewer.md`, and its own paragraph: "Do NOT read `docs/proofs/` or anything
    under `clearwater-review-evidence`; those are withheld. Never read or list
    `/mnt/c/Users/rwsmy/clearwater-footage`."
  - **Assertions** (all `grep -a`):
    - the banner reads gpt-5.6-sol / high;
    - every `^ERROR` and `ERROR codex_core` line is classified by provenance;
    - the `^tokens used` footer is present;
    - an anchored VERDICT line;
    - at least one `^ succeeded in`;
    - `grep -a -n 'docs/proofs\|wp-t1-ledger'`, with every hit classified as an echo or an
      access.
  - **Evidence:** `C:\Users\rwsmy\clearwater-review-evidence\wp-t1\r1\` with md5s; ledger
    `docs/proofs/wp-t1-ledger.md`.
- **WHAT TO EXAMINE:**
  - whether the hook truly runs before any temp folder is created or cleared;
  - whether the derivation matches pytest's for every input;
  - every way a path can be inside the footage folder yet compare as outside (case, links,
    junctions, relative paths, `..`, trailing separators, 8.3 short names, UNC or `\\?\`
    forms);
  - whether the tests could touch the real footage folder;
  - whether the guard can fail a run on a machine without footage.
- Reviewer B is the orchestrator's own seat pass on the merge candidate (fill Part 2 item 2).

## Notes for the cell

- **Never run a refused case against the REAL footage folder**, not even to "check": every
  case uses the fake folder under `tmp_path`.
- **Working rules:**
  - The orchestrator copies `clearwater.local.toml` into the worktree; never edit or commit it.
  - `uv sync` in the worktree.
  - Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for pytest runs.
  - Never use a bare `cd`; never `git stash`; never post to a mailbox.
  - Commit by pathspec (`feat(wp-t1): ...`), with `Co-Authored-By:` naming the model you
    actually run as.
- **STOP for:**
  - a need to change `tools/local_config.py` or `pyproject.toml`;
  - a pytest ordering that lets a temp folder be created before any conftest hook can run
    (report it with the evidence);
  - any write outside the worktree, `tmp_path` and `work/wp-t1/`.
- **Return report:** your FINAL message, under about 50 lines:
  - per-commit changes;
  - the gate lines, including the harness gate;
  - the test list with results;
  - the pytest lines the derivation mirrors;
  - the review round and its assertions;
  - the locks;
  - deviations.
