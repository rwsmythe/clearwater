# WP4.2a — Runner hardening (WP4.1's Reviewer B pass 2 items) (dispatch brief, FINAL)

**Status:** FINAL 2026-10-29 on CHARC `c8340144a8e87c09` (the WP4.2 Revision 1 rulings, R1-Q1,
R1-Q2, the DR-79 (b) correction and R1-Q5, carried verbatim below; they govern this brief).
Drafted by a drafting helper for the orchestrator (generation 18). Spec v0.5.6; no spec clause
changes. A test tool and tests only: no `src/` edit.

| Field | Content |
|---|---|
| ID and title | WP4.2a — Runner hardening (WP4.1's Reviewer B pass 2 items) |
| Lane | **CODEX**: `implementer-codex-sol-high` (gpt-6.1-sol / high), `codex exec` turns driven by `scripts/codex_cell.py`. Paces at dispatch (orchestrator fills): Codex `<pace>` vs Claude `<pace>` (`scripts/usage_codex.py`, `scripts/usage_claude.py`). CHARC: "the 2026-10-27 lane rule operating (well-specified, no frozen interface ...)". The cell ends every turn with a FILES CHANGED block; the orchestrator commits and runs every heavy command the cell yields (`.claude/agents/implementer-codex-sol-high.md`). |
| Tier and nets | Tier **STRONG** (the fill tiers by the blast radius of a missed finding; this is the footage folder's write guard, where WP4.1's B1 and B2-1 were MAJOR). Reviewer A = the Claude pass, `scripts/codex_cell.py review` (`claude -p --model opus --effort high`, read-only), run by the driver between turns, to convergence, five-round gate. Reviewer B = the Claude pass at the orchestrator's seat on the merge candidate. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.2a\rN\`, `reviewB\`. |
| Base, worktree | Base = main at dispatch (after the commit carrying this brief). Worktree `.worktrees/wp4.2a`, branch `wp4.2a`. |
| Goal | Close DR-78 and DR-79 (all of (a), (b), (c)) in `tools/headless_export.py` and the four WP4.1 comparison sites, before WP4.2's build touches the same file. |
| Spec / decisions | N8 ("source files never modified"); D84 (never overwrite); CHARC `870c8ddeb64b4e12` (ONE write-target predicate, `write_target_refusal` (i)/(ii)/(iii)); CHARC `80bbf403266651df` (B2-1..B2-4 banked to WP4.2); CHARC `c8340144a8e87c09` (this package). |
| Files owned | Exactly condition 1: `tools/headless_export.py` ONLY in `check_outputs`, the new (i) helper (and `write_target_refusal`'s call of it), `Redactor`'s `\'` form and the wrap of `Redactor` construction (in `main` and wherever else the runner builds one from given folders); NEW `tests/test_wp42a_runner_hardening.py`; the four comparison lines `tests/test_wp41_photo_path.py:514` and `:528`, `tests/test_wp41_v8.py:74` (`equal_statistics`) and `:162`; `docs/reports/wp4.2a-runner-hardening.md`; `docs/proofs/wp4.2a-ledger.md`. The mixed pin `tests/test_headless_export.py::test_the_record_has_schema_1_and_file_names_only` ONLY IF this package's own change needs it (expected not: it runs with the `no_footage` fixture, so `check_outputs` checks nothing there; if it is needed, the ledger says why). |
| NOT owned | Everything else, explicitly: all of `src/` (no `src/` edit; `jobs.naming` is called, never changed); every other test in `tests/test_headless_export.py`, `tests/test_app_composition.py`, `tests/test_wp41_*.py`, `tests/test_app_deps.py`; `pyproject.toml`, `uv.lock`; `tests/conftest.py`; every other part of `tools/headless_export.py` (the video legs and `--cache-dir` are WP4.2's task 5). |
| Debt | DR-78 and DR-79 CLOSE here (CHARC rewrites both rows at this accept: "DR-78 CLOSED, DR-79 CLOSED with (b)'s wording"); nothing else. |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict; the standard two-leg suite (`CLAUDE.md`) in a window the orchestrator posts, both legs green; every new test parallel-leg (no `slow`, `gpu`, `footage` or `gui` marker); every existing test unchanged except the four comparison lines (and the mixed pin only as above); Reviewer A converged; report and ledger written. No harness gate (nothing in `scripts/`, `.claude/`, the kernel docs or `tests/harness/` changes). |

## The ruling, verbatim (CHARC `c8340144a8e87c09`)

**R1-Q1 = (a), with the mechanics fixed.** Apply (i) to every planned output FILE path (`final_output_path(source, settings, kind)`, photo and video alike) in `check_outputs`. Keep ONE predicate: factor (i) out of `write_target_refusal` into a named helper (the stream-name and extended-form test on the text) that `write_target_refusal` itself calls, and apply that helper to the file path; do not duplicate the `:` / `\?\` text in a second place. (ii)/(iii) stay on the folder as decided. The RED-first test plants a source whose stem carries `:` (a stand-in name under tmp_path is enough; an alternate data stream where the OS allows, skipping otherwise). The WP4.2a report revises the Limit so "(i) refuses every stream name" is true for outputs.

**R1-Q2 = (a), the grant covers FOUR sites, not three.** `tests/test_wp41_photo_path.py:514` and `:528`, `tests/test_wp41_v8.py:74` (the `equal_statistics` helper) AND `tests/test_wp41_v8.py:162` (`np.array_equal(preview, written_pixels)`), which the packet missed and is the same class. Bit-pattern compare (dtype, shape, bytes), signed-zero control in the new hardening test file, assertions only stricter. DR-79 (c) CLOSES with all four.

**DR-79 (b), a correction to the row as the packet reads it.** At this seat, `mklink /J loop loop` then `(loop / 'x').resolve()` on the project Python RETURNS a path; it does not raise. The row's "Path.resolve() raises RuntimeError" came from a REASONED finding and is not reproduced here. WP4.2a: try to reproduce RED-first (self-loop junction, and a symlink loop where the OS allows); if nothing raises, record "not reproduced on Python 3.12 / Windows" in the report, and still wrap `Redactor` construction so any `OSError` / `RuntimeError` from a given folder becomes a usage refusal (exit 2, name only), tested with a monkeypatched `Path.resolve` that raises. (b) then CLOSES as "defensive; not reproduced".

R1-Q5 conditions 1-5:

1. WP4.2a owns `tools/headless_export.py` (`check_outputs`, the (i) helper, `Redactor` `\'` form and construction wrap), `tests/test_wp42a_runner_hardening.py`, the four comparison lines above, and the mixed-pin edit of R1-Q3 ONLY IF its own change needs it (otherwise R1-Q3 stays WP4.2's). Nothing else; no `src/` edit.
2. Nets: Reviewer A = the Claude pass (`codex_cell.py review`), Reviewer B = the Claude pass at your seat; gate = the standard two-leg suite in a posted window (every new test parallel-leg; no `slow`, no GPU, no footage). Cell depth read every turn as for WP-T5.
3. WP4.2 round 0 runs concurrently (opus-high, ledger-only commits on `wp4.2`); its build waits for WP4.2a's merge. CAP: if WP4.2a has not merged by WP4.2's round-0 yield plus 3 h, you STOP WP4.2a at a committed head, WP4.2 builds on main, and WP4.2a's remainder rebases after WP4.2's accept (its brief then shrinks to what WP4.2 did not absorb). You decide at the cap and tell me.
4. DR-78's BINDING trigger moves to WP4.2a: I rewrite the DR-78/79 trigger text at WP4.2a's accept (CLOSED by WP4.2a). WP4.2's rows read as you proposed. WP4.2's task 8 keeps the video file-path coverage through `check_outputs`.
5. WP4.2a's brief is SHORT and Codex-form, carries R1-Q1/Q2 and the DR-79 (b) correction verbatim, and names the conflict with WP4.2 task 5 as the reason for the order. Send it to me as one FYI with the FINAL brief; I do not need another ruling round for it unless it adds scope.

## Order (condition 3) and why

WP4.2's task 5 edits the same functions of `tools/headless_export.py` (`check_outputs`, `main`,
the redactor's known folders) to add `--cache-dir` and the video legs, so the two packages cannot
build concurrently. WP4.2's round 0 (ledger only) runs beside this package; WP4.2's build waits
for this merge, and the orchestrator rebases `wp4.2` onto main before granting it. The CAP:
"if WP4.2a has not merged by WP4.2's round-0 yield plus 3 h, you STOP WP4.2a at a committed head,
WP4.2 builds on main, and WP4.2a's remainder rebases after WP4.2's accept (its brief then shrinks
to what WP4.2 did not absorb)." Keep each commit whole so a stop at any committed head is clean.

## Task ladder

1. **Read and map.** `tools/headless_export.py` (`write_target_refusal`, `check_outputs`,
   `Redactor`, `_escaped_pattern`, `main`, `_main`, `RefusedRequest`); `clearwater.jobs`
   `final_output_path` and `MediaKind` (`jobs/naming.py`); WP4.1's report "Limits" (the footage
   check) and "Erratum at the gate"; `tests/test_headless_export.py` (`no_footage`, `out`, the
   footage-refusal tests) for the fixtures' pattern; the four comparison sites.
2. **Round-0 note, then YIELD.** In the ledger: the helper's name and signature; where the file
   check sits in `check_outputs`; the RED-first test list with each test's expected failure on
   the base; DR-79 (b)'s reproduction plan; the four sites' new comparison; the
   `scripts/cell_depth.py` figure. YIELD. Build nothing before the reply.
3. **DR-78** (R1-Q1). Factor (i) into the helper; `write_target_refusal` calls it (no second copy
   of the `:` / `\\?\` / `\\.\` test). In `check_outputs`, on its existing configured-footage path
   (with no footage folder it still checks nothing), apply the helper to
   `final_output_path(request.source, request.settings, MediaKind(request.kind))` for every request
   but a `RefusedRequest` (its `kind` is a placeholder and it fails unopened); a refused file path
   is a `RunnerRefusalError` naming the source by name only (exit 2, nothing run). No new exception
   type escapes `check_outputs`: a `ValueError` from `final_output_path` (an invalid suffix, which
   `main` refuses earlier) leaves that request to the engine's own refusal. RED first: a source
   whose stem carries `:` under `tmp_path` (a stand-in name), photo (`.jpg`) and video (`.mp4`), run
   through `run(..., footage_folder=<stand-in footage folder>)` and through `main` with
   `configured_footage_folder` monkeypatched; and, where the OS allows (skip otherwise), the
   register row's case: a real alternate data stream source and `<out>\carrier` a hard link to a
   stand-in original under `tmp_path`, the original's bytes and stream list unchanged after the
   refusal. A control: a planted helper that skips the file path fails the test by name.
4. **DR-79 (a).** Add the `\'` spelling to `Redactor`'s forms (every form it already builds, with
   each `'` escaped as `repr` escapes it). RED first: a known folder whose name contains `'`,
   quoted back through a refused `--suffix`, is printed and recorded by name only.
5. **DR-79 (b)** per the correction above: the reproduction attempts (a self-loop junction; a
   symlink loop where the OS allows) with their result in the ledger; the wrap; the test with a
   monkeypatched `Path.resolve` that raises `OSError` and one that raises `RuntimeError`: exit 2,
   no traceback, no full path printed.
6. **DR-79 (c).** The four sites compare dtype, shape and bytes (`tobytes()`), so `+0.0` and
   `-0.0` differ; assertions only stricter. The signed-zero control in the new file shows
   `np.array_equal` equates float32 `+0.0` and `-0.0` and the sites' comparison form does not.
7. **Report, ledger, gates.** `docs/reports/wp4.2a-runner-hardening.md`: what changed (by
   function and test node id); the Limit as revised (WP4.1's "The footage check" text with the
   target list extended to each planned output FILE path through the helper, and the residual
   sentence so "(i) refuses every stream name" is true for outputs); DR-79 (b)'s reproduction
   result ("not reproduced on Python 3.12 / Windows" if nothing raised); a "for CHARC" line with
   the DR-78 / DR-79 closure text. Ledger: rounds, depth readings, each heavy run (command,
   counts, EXIT). Then ruff, format, mypy, and `WINDOW REQUEST` for the two-leg suite.

## Envelope, notes, STOP

- Envelope: Windows 11, Python 3.12, local NTFS, Git Bash; every test under `tmp_path` with a
  stand-in footage folder; the real footage folder is never named, read or written.
- Light runs need no window: `uv run pytest -q tests/test_wp42a_runner_hardening.py
  tests/test_headless_export.py tests/test_wp41_photo_path.py tests/test_wp41_v8.py -m "not gpu and
  not footage and not slow"` (the full files: the existing runner tests must pass with the file
  check added). The two-leg suite only in the posted window (Codex lane: yield the command).
- Yields: round 0 (task 2); after each review round, end the turn once the verdict is
  adjudicated, before remediating. Depth read every turn (~250K evaluation point, ~400K STOP).
- Commits (by the orchestrator, Codex lane): `fix(wp4.2a): ...`, `test(wp4.2a): ...`,
  `docs(wp4.2a): ...`, pathspec, `-c core.autocrlf=false`, LF blobs, a `Co-Authored-By:` footer.
- STOP for: any `src/` edit; any change outside the owned functions and lines; an existing test
  that fails with the file check added (other than the mixed pin as above); a second copy of the
  (i) text; anything that would write outside `tmp_path`, the worktree and `work/`.
