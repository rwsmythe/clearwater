# WP-H1 — `cell_depth.py` second pass: swing's selectors (dispatch brief, DRAFT, HELD)

**Status:** DRAFT 2026-11-03 by CHARC (generation 13). **HOLD LIFTED 2026-11-04 ~02:45Z by CHARC (generation 14): Phase 5 CLOSED at the WP5.5 accept (main `40d2ce04`); the orchestrator fills the dispatch section when the 1.0.0 tag is applied and nothing else runs, CHARC marks it FINAL on that fill. Was: HELD until Phase 5 CLOSES (the WP5.5 accept): the owner commissioned this "after phase 5 closes" (2026-11-02, verbatim: "commission the second pass after phase 5 closes").** The orchestrator fills the dispatch section at that time; CHARC marks it FINAL. Harness-side package: it runs the HARNESS suite (`uv run python -m unittest discover -s tests/harness`), not the product gate. No product file is touched. No spec clause. Owner decisions inside the package: none.

| Field | Content |
|---|---|
| ID and title | WP-H1 — `scripts/cell_depth.py` gains swing's three selectors (`--sessions`, `--live HOURS` with the parked-cell rule, `--agent ID`) on the Clearwater lineage's reader, with swing's tests as the base; then upstreamed to the template by the re-port method (`docs/proofs/harness-upstream-2026-11-02.md`, swing MAJOR 1) |
| Lane | **CODEX**: `implementer-codex-sol-high` (a merge of a known 365-line sibling into a 551-line reader with 47 tests; stdlib only; well-specified by both sources). Reviewer A = the Claude pass at the cell's seat; Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp-h1\`. |
| Tier and size | STANDARD. Size S-M (one script, one test module; a template re-port as the second half). Codex evaluate at about 200K, STOP near 250K. |
| Base | main after WP5.5's accept (Phase 5 closed). Worktree `.worktrees/wp-h1`, branch `wp-h1`. |
| Goal | A seat that must roll can read ITS OWN depth (`--sessions`: the main session transcripts, not the cells), the orchestrator can take the in-flight census (`--live H`: every cell written in the last H hours PLUS every older cell whose parent session transcript is that fresh, flagged `parked`), and the round-gate read of one named cell at any age (`--agent ID`, repeatable, never with `--live`); all three behave as swing's tests specify, on the Clearwater reader's discovery rules (named and anonymous cells, `--project` / `--session`, the exit-code contract 0-4, PEAK versus current, the request folding by `message.id`), which stay exactly as they are. |
| Sources | Clearwater `scripts/cell_depth.py` (551 lines; functions `default_project_dir`, `cell_name_from_filename`, `read_transcript`, `discover_cells`, `_build_parser`, `main`) and `tests/harness/test_cell_depth.py` (850 lines, 47 tests); swing `C:\Users\rwsmy\swing-trading\scripts\cell_depth.py` (365 lines: `scan(sessions=)`, `find_agents`, `session_transcript_path`, `session_transcript_age_hours`, `select_live`, the parser's mutually exclusive `--live` / `--all` / `--agent` group and `--sessions`) and `tests\scripts\test_cell_depth.py` (471 lines, 29 tests, of which the selector tests: `test_live_filter_selects_by_transcript_age`, `test_sessions_mode_reads_main_transcripts_and_excludes_cells`, `test_agent_*` (4), `test_r3_*` (6)). Swing's commits `b09bbc02` (`--agent`; `--live` by mtime), `d4986324` (R-3 parked cells), `4e412db9` (TOCTOU: one guarded `stat`). READ-ONLY sources: nothing in `swing-trading` is modified. |
| Files owned | `scripts/cell_depth.py`; `tests/harness/test_cell_depth.py` (new tests appended; the 47 existing tests unchanged and green); `docs/dispatch-recipe.md` ONLY where it names the depth read (section 5, the line "your depth from your transcript (`scripts/cell_depth.py`)": the precondition and the round-gate read gain the exact commands, one paragraph); `docs/orchestrator-context.md` does not name the reader today and is NOT edited; `docs/proofs/harness-upstream-2026-11-02.md` item "Open for the owner" 2 marked DONE at the accept (CHARC's edit, not the cell's). |
| NOT owned | Every other script and hook; `tests/harness/genericity_lists.py` (the reader stays application-agnostic: no new vocabulary, so no list change; if a test needs a word there, STOP); the template clone (the re-port is the orchestrator's act at the accept, below); `swing-trading`. |
| Locks | STDLIB ONLY (no third-party import). READ-ONLY on transcripts (never create, delete or modify one; tests build their own under `tmp_path`). The existing exit-code contract is unchanged: 0 clean, 1 no cells, 2 PEAK over cap, 3 incomplete, 4 usage error (`--agent` with `--live`, `--agent` with `--sessions`, an unknown agent id = 4, NOT swing's 1 / 2 which belong to swing's contract: map and document). ASCII output. No application vocabulary. |
| Markers | Harness suite only (`unittest`). Every new test runs under a second on a synthetic `tmp_path` project tree. |
| Hardware flags | None. |
| Out of scope | Changing the depth arithmetic, the cap default, the folding rule or the discovery of named / anonymous cells; a JSON output mode; reading Codex transcripts (the Codex cell's depth is read from its own `codex exec` footer, `scripts/codex_cell.py`); the hook that prints `[ctx]`. |
| Debt and decided items | At the accept CHARC writes: the upstream record's item 2 DONE; a note in `docs/orchestrator-context.md` "Comms routing" is NOT touched; the template re-port recorded (branch, PR, merge) in a new section of the upstream record. |
| Done | The harness suite green (`unittest discover -s tests/harness`: 382 + the new tests); the 47 existing tests unchanged; the three selectors exercised by the ported tests AND by one live read at the orchestrator's seat (`--sessions --live 24` lists the running CHARC and orchestrator sessions with their peak depths; `--live 6` lists the cells of the day; recorded in the report); ruff / format clean on the script (mypy covers `src/clearwater` and `tools` only, `pyproject.toml` `[tool.mypy] files`, so it is not run on `scripts/`: state it); the report; Reviewer A converged; Reviewer B clean or its single remediation done. |

## The design (fixed; the cell merges, it does not redesign)

1. **Selectors as a group.** `--live HOURS`, `--all` (the default) and `--agent ID` (repeatable) are mutually exclusive; `--sessions` is a mode flag combinable with `--live` and `--all` but not `--agent` (usage error, exit 4). The positional `cell` substring filter and `--project` / `--session` stay and compose with every selector (`--session` restricts the directories scanned; `--live` then filters by age inside them).
2. **`--sessions`.** Reads `<project>/<session-id>.jsonl` (the MAIN transcripts) instead of `<session-id>/subagents/agent-*.jsonl`; the row's name is the session id; the same folding and PEAK / current arithmetic; the same cap rule.
3. **`--live H`.** Age = now minus the transcript's mtime in hours (one guarded `stat`, swing `4e412db9`). A cell is listed when its own age is within H, OR (cells only, not sessions) when its parent session transcript (`session_transcript_path`: the sibling `<session-id>.jsonl` derived from the cell's OWN path, never crossing project directories) is within H: flagged `parked`. The flag column reads `OVER,parked` when both apply (swing `test_r3_over_cap_and_parked_flag_form_is_OVER_comma_parked`).
4. **`--agent ID`.** Finds `agent-a<ID>*.jsonl` under the scanned session directories at any age; an id matching nothing is a usage error (exit 4) naming the searched pattern; repeatable; the cap applies.
5. **Rows.** The existing row format gains the `age` column (hours, one decimal) and the flag column's `parked` value; the existing columns keep their order and width so any seat script that parses them (none is known: check `scripts/` and the kernel docs with a grep and state the result) still reads.
6. **Tests.** Port swing's 12 selector tests onto the Clearwater fixture style (named and anonymous cells, `--project`); add one test per exit-code mapping difference; keep the 47.

## Questions (CHARC's recommended answers)

- **Q1 exit codes.** Recommended: Clearwater's contract wins (4 for every usage error, including the unknown `--agent` id; swing exits 2 there). The report's table maps swing's codes to Clearwater's for the record.
- **Q2 `--sessions --live`.** Recommended: plain mtime filter, no parked logic (swing's rule; a session has no parent).
- **Q3 the re-port.** Recommended: the orchestrator applies the delta to the template clone by the upstream record's method at the accept (`git diff template/main HEAD -- scripts/cell_depth.py tests/harness/test_cell_depth.py docs/orchestrator-context.md docs/dispatch-recipe.md`, `git apply --index` in `C:\Users\rwsmy\harness-template`, LF working tree, a branch `clearwater-upstream-<date>`), runs the TEMPLATE's own harness suite there, and pushes the branch; the PR and merge are the owner's (as PR #1 was). Nothing is pushed without the owner's word.

## Completion report (`docs/reports/wp-h1-cell-depth.md`)

What was ported from where (commit by commit); the exit-code map; the row-format diff; the live reads at the seat; the harness-suite figures before and after; the re-port delta's file list; limits (Codex cells are not covered; the parked rule depends on the parent transcript's mtime, which a quiet parent does not move).

## Yields and depth

Turn 1 = round 0 (read both readers and both test modules; the merge plan function by function; the exit-code map; any Q dispute = STOP) and YIELD; turn 2 = tests ported RED, then GREEN, the docs paragraphs, committed, YIELD for Reviewer A; the report; the nets; the re-port at the accept (the orchestrator's act).

## Orchestrator dispatch fill (for CHARC to finalise, after the WP5.5 accept)

- Lane paces at dispatch; base commit; worktree; evidence folder; the template clone's state (`origin/master` and `refs/remotes/template/main` equal) checked before the re-port.
- GATE_CHECKS: the harness suite on the final candidate (not the product gate; `scripts/` changed, so the harness gate is the rule in CLAUDE.md); `git diff --name-only main` holds only the owned paths.

## Dispatch fill (orchestrator gen 40, 2026-11-04 ~05:50Z; after the tag)

Fills the section above. Where it differs from the table, the design or the questions, this fill governs once CHARC marks it FINAL. Corrections to the brief's text are marked **[corr]**.

- **Precondition met.** The tag `v1.0.0` (annotated) is on `40d2ce04`, applied 05:45:31Z on the owner's word relayed by CHARC (`d1af354bc5607d86`); no push. Nothing runs: no cell, no gate, no pytest.
- **Base, worktree and evidence.** Base = main at dispatch (`d62eb37e`, CHARC's release record, plus this fill's commit). Worktree `.worktrees/wp-h1`, branch `wp-h1`. No `clearwater.local.toml` is needed: the package reads no footage or config. Evidence goes to `C:\Users\rwsmy\clearwater-review-evidence\wp-h1\`, with folders `cell\`, `A\`, `B\` and `gate\`. Disk: C: 37 GB free. The harness suite is the only job, so the 25 GB gate floor is met with room.
- **Lane paces at 05:46Z.**
  - Codex: 22 % used, pace 0.226. The window resets 2026-11-04 10:07Z, so a long package may cross the reset; it does not affect the lane.
  - Claude: 19 % used, pace 0.729.
  - Codex has the lower pace, and it is the brief's lane: CODEX (`implementer-codex-sol-high`, a FRESH session).
  - Reviewer A = a Claude pass at the orchestrator's seat each round (`scripts/codex_cell.py review`).
  - Reviewer B = a Claude pass at the orchestrator's seat on the final candidate. It is the other model in both nets.
- **Sources verified at the seat (05:47Z).**
  - Clearwater `scripts/cell_depth.py`: 551 lines. `tests/harness/test_cell_depth.py`: 850 lines, 47 tests. The harness suite: 382 OK.
  - Swing `scripts\cell_depth.py`: 365 lines. `tests\scripts\test_cell_depth.py`: 471 lines, 29 tests. Both files are clean in swing's working tree; the last commit on the reader is `4e412db9`. All three named commits resolve: `b09bbc02`, `d4986324` and `4e412db9`.
  - The Codex sandbox reads `C:\Users\rwsmy\swing-trading\` but must never write there (READ-ONLY, as in the brief).
- **[corr] Swing has 15 selector tests, not 12.** All 15 are ported, so the done count is 382 + 15 + the exit-map tests:
  - `test_live_filter_selects_by_transcript_age`
  - `test_sessions_mode_reads_main_transcripts_and_excludes_cells`
  - four `test_agent_*`:
    - `reads_a_parked_cell_older_than_the_live_window`
    - `is_repeatable_and_applies_the_cap`
    - `unknown_id_exits_2_naming_the_searched_glob`
    - `with_live_is_a_usage_error`
  - NINE `test_r3_*`, not six:
    - `a_old_cell_with_a_fresh_parent_is_listed_and_flagged_parked`
    - `b_old_cell_with_an_old_parent_is_not_listed`
    - `c_a_fresh_cell_is_listed_not_flagged_parked`
    - `d_a_parked_cell_over_the_cap_exits_1`
    - `a_missing_parent_transcript_does_not_crash`
    - `toctou_deletion_between_check_and_stat_does_not_crash`
    - `session_transcript_path_never_crosses_project_dirs`
    - `sessions_mode_with_live_is_unaffected_by_parked_logic`
    - `over_cap_and_parked_flag_form_is_OVER_comma_parked`
- **The exit-code map in full (Q1 extended).** Read from both `main()`s:

  | Case | Swing | Clearwater |
  |---|---|---|
  | over the cap | 1 | **2** |
  | no transcript discovered | 2 | **1**, with the LOUD `NO CELLS FOUND` line on stderr |
  | unknown `--agent` id | 2 | **4** |
  | argparse usage error (`parser.error`) | 2 | **4** (Clearwater's `_ConfigError`) |
  | `--live` window empty after a non-empty discovery | 0 (stdout "nothing to check") | **see Q4** |

  So the ported tests change their asserted codes as follows. `test_agent_unknown_id_exits_2...` asserts 4, and `test_r3_d_..._exits_1` asserts 2; renaming both to the Clearwater code is part of the port. One test per mapped row.
- **Q4 (new, the orchestrator's; CHARC to rule at FINAL).** What does `--live H` (or `--sessions --live H`) return when discovery found transcripts but none falls in the window?
  - **Recommended: exit 0**, with swing's stdout line `no cells written in the last <H>h (cap <N>); nothing to check` (`sessions` for `--sessions`).
  - Discovery-empty stays exit 1 with the loud line. The loud 1 exists against a glob that missed `subagents/`. A non-empty discovery disproves that, so an empty window is a clean negative: at a quiet seat the census correctly lists no live cell.
  - The alternative is exit 1 for both. That makes every quiet-seat census read as a discovery failure.
- **Q5 (new; CHARC to rule at FINAL): the brief's ruff line cannot be met as written.**
  - `pyproject.toml` `[tool.ruff] extend-exclude` lists `scripts` and `tests/harness`, as upstream scaffold. So `uv run ruff check .` and `ruff format --check .` never see the script.
  - Run on the explicit path, `uv run ruff check scripts/cell_depth.py` reports **25 pre-existing findings** at main. They are the docstring layout (D205/D209), import order, `N818`, `D103` on `main`, and so on.
  - Clearing them would reformat a file the template shares, which is out of scope and makes the re-port delta larger.
  - **Recommended:**
    - The gate is the project's own `ruff check .` and `ruff format --check .`, clean as at main.
    - The explicit-path count is recorded before and after in the report, for information. New code follows the file's existing style, and no NEW rule code appears in the explicit-path run.
    - mypy is not run on `scripts/` (as the brief says).
- **Row parsers: none known.**
  - `scripts/` names the reader only in a comment, `launch_role.ps1:226`.
  - The kernel docs name it at `docs/dispatch-recipe.md:108` (owned, the paragraph) and `docs/model-prompting-standard.md:116` (not owned, no command).
  - The cells name it at `.claude/agents/implementer-opus-high.md:72` and `implementer-sonnet-high.md:68` (not owned, no command).
  - Nothing parses a row. The cell re-greps in round 0 and states the result; the `age` column is still APPENDED, so existing columns keep their order and width.
- **Files owned, added:** `docs/reports/wp-h1-cell-depth.md` (the report, the cell's) and `docs/proofs/wp-h1-ledger.md` (the orchestrator's). Both are under prefixes that are already instance surface, so `tests/harness/genericity_lists.py` stays NOT owned. If the harness's manifest accounting refuses either, that is a STOP to me, not an edit.
- **The template clone** `C:\Users\rwsmy\harness-template` at 05:47Z:
  - local `master` = `origin/master` = Clearwater's `refs/remotes/template/main` = `4335ff6` (PR #1's merge); working tree clean (0 porcelain lines).
  - Today's delta `git diff template/main HEAD -- scripts/cell_depth.py tests/harness/test_cell_depth.py` is 1 line in the reader, which the re-port carries along.
  - All three are re-checked before the re-port. If they are unequal, STOP to CHARC.
- **The re-port (Q3, the orchestrator's act at the accept).**
  - In the template clone: a branch `clearwater-upstream-2026-11-04` (date of the act), `git apply --index`, LF working tree, and the TEMPLATE's own harness suite green.
  - **No push.** The branch waits for the owner's word, then the PR and merge are the owner's, as PR #1 was.
- **Turns and depth.**
  - Turn 1 = round 0, read-only: both readers and both test modules; the merge plan function by function; the exit map above; the row grep; any Q1-Q5 dispute = STOP. Then YIELD.
  - Turn 2 = the 15 tests plus the mapping tests ported RED, then GREEN; the `docs/dispatch-recipe.md` paragraph. The orchestrator commits by `codex_cell.py commit`. YIELD for Reviewer A.
  - Turn 3 = Reviewer A's fixes, then the report with the live reads filled from the seat (below).
  - Codex depth: evaluate at about 200K, STOP near 250K, re-seat fresh from the ledger.
- **The live reads are the seat's.** The Codex sandbox does not read `~\.claude\projects` for this. The orchestrator runs at its seat on the package head and records the output, with its exact command, in `wp-h1\gate\live-reads.txt` for the report:
  - `--sessions --live 24` (expect the CHARC and orchestrator sessions);
  - `--live 6` (cells of the day; at a quiet seat this exercises Q4's answer);
  - `--agent <one Claude cell id from this phase>`.
- **GATE_CHECKS** (the orchestrator's seat, on the final candidate after Reviewer B):
  - the harness suite `uv run python -m unittest discover -s tests/harness` (382 + the new tests, 0 failures);
  - `git diff main...wp-h1 -- tests/harness/test_cell_depth.py` removes no existing line inside the 47 tests, except where a shared helper gains a parameter. Any changed assertion in the 47 = STOP;
  - the project's `ruff check .` and `ruff format --check .` (Q5);
  - every changed blob 0 CR;
  - `git diff --name-only main...wp-h1` holds only the owned paths: `scripts/cell_depth.py`, `tests/harness/test_cell_depth.py`, `docs/dispatch-recipe.md`, the report, the ledger and the accept record.
  - No pytest leg: no product file changes.
- **Harness gate early (gen-40 lesson).** The harness suite runs on the package head at every yield, before Reviewer A, and again before Reviewer B. It is not run only at the gate.
