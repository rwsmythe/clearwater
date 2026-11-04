# WP-H1 accept record (orchestrator generation 40, 2026-11-04)

## Package

WP-H1 is the `scripts/cell_depth.py` second pass. It adds swing's three selectors to the Clearwater reader, with swing's tests as the base:
- `--sessions`: the seat reads its own main transcripts.
- `--live HOURS` with the parked-cell rule: the in-flight census.
- `--agent ID`: the exact round-gate read at any age.

The re-port to the template follows at this accept.

**Brief:** `docs/briefs/wp-h1-brief.md`. FINAL at `d799ba4a` on gen 40's fill `3823b645`, with these rulings:
- Q4: an empty window exits 0.
- Q5: the project ruff gate.
- Round-0 ruling (A) at `0d26e240`: re-pin the one anchored row regex; 46 tests byte-unchanged; one row format in every mode.
- F3 ruling at `fe6486ec`: `--agent` is an exact match.

**Lane: CODEX** (`implementer-codex-sol-high`, GPT-6.1 Sol / high). One session `01a1a51b`, six turns. It compacted once, in turn 5, and ended at 84,621. Both nets are Claude (`claude-opus-5-5`, high), the other model, run read-only at the orchestrator's seat.

**Paces:**

| When | Codex | Claude |
|---|---|---|
| Dispatch | 22 % / 0.226 | 19 % / 0.729 |
| First yield | 22 % / 0.225 | 19 % / 0.723 |

**Records:**
- Report: `docs/reports/wp-h1-cell-depth.md`.
- Ledger: `docs/proofs/wp-h1-ledger.md`.
- Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp-h1\`:
  - `cell\`: dispatches, prompts and returns 1-6;
  - `A\r1`, `A\r2`, `B\`;
  - `gate\`: the live reads and the harness logs.

## Candidate

Package commits on branch `wp-h1`:

| Commit | What |
|---|---|
| `b4e6a19e` | the build and the recipe paragraph |
| `6bd5fb99` | A r1 fixes |
| `411ce22f` | A r2 tidy and the report |
| `f6b53883` | the ledger |
| `3dba892b` | B remediation |

- Main was merged INTO the branch `--no-ff` as `d427d223` (round-0 ruling) and `4a107a00` (F3 ruling), so every cited hash stays reachable.
- Main has not moved since `fe6486ec`. **The merge to main is a fast-forward.**

**Footprint** (`git diff --name-only d427d223..wp-h1`, beyond the docs-only merge files `CLAUDE.md`, the brief and `docs/charc-state.md`):
- `scripts/cell_depth.py`
- `tests/harness/test_cell_depth.py`
- `docs/dispatch-recipe.md` (section 5's paragraph only)
- NEW: the report, the ledger and this record

The test module removes exactly ONE line against the base: the re-pinned pattern. Every changed blob is 0 CR and ASCII.

## Result

- **Selectors.**
  - **Exit map:** over the cap 2; no transcripts 1, LOUD; unknown `--agent` 4; usage 4; empty window 0 (Q4); `--live` negative or NaN 4; an empty `--agent` 4; a listing failure under `--agent` 3.
  - **Parked rule:** an old cell whose parent transcript is fresh is listed, flagged `parked` (`OVER,parked` when over the cap). One guarded stat.
  - **Selection:** `--sessions --live` is a plain mtime filter. `--agent` is an exact cell name or the full `agent-a<ID>` stem. A name reused within one session, or across sessions, prints a stderr NOTE.
  - **Row:** one row in every mode: `<existing fields>  [PAST-CAP]  age=<h>.<d>h  flag=ok|OVER|parked|OVER,parked`.
- **Tests:** the reader module 47 → 88 (15 ported from swing with the two renamed codes, 5 exit-map tests, and the review rounds' pins). The harness suite 382 → **423 OK** (1 skipped).
- **Static:**
  - Project `ruff check .` clean; `ruff format --check .` 317 clean.
  - The explicit path on the script stays at 25 → 25 with the same codes (Q5; the pre-existing findings were not cleared).
  - mypy does not cover `scripts/`.
- **Live reads at the seat** (`gate\live-reads.txt`):
  - `--sessions --live 24`: 7 sessions, 3 over the cap, exit 2.
  - `--live 6`: quiet, exit 0 (the Q4 witness).
  - `--agent`: exact rows at any age, through both the name and the stem.
  - Prefix id, empty id and `--live -1`: each exits 4.

## Nets

| Net | Result |
|---|---|
| Round 0 (turn 1, read-only) | STOP: the brief's age column against its 47-test lock. CHARC ruled (A). |
| Build (turns 2-3) | The doc guard bans the literal `--session ` (with a space); the orchestrator ruled the `=` form (its own dispatch's spelling). |
| **Reviewer A r1** (`A\r1\`, on `b4e6a19e`) | **NEW_CRITICAL_MAJOR_FOUND**. F1 MAJOR: no test pinned the in-window error guard (three mutations survived; the code was correct). F2-F5 MINOR; F3 was ruled by CHARC (exact match). F6-F8 ADVISORY. Fixed in `6bd5fb99`. |
| **Reviewer A r2** (`A\r2\`, on `6bd5fb99`) | **NO_NEW_CRITICAL_MAJOR = CONVERGED**. F1-F6 FIXED, verified by mutation. MINOR 1 (a name reused in a session) and advisories, tidied in `411ce22f`. |
| **Reviewer B** (`B\`, on `f6b53883`) | **NO_NEW_CRITICAL_MAJOR**. No false-clean path; 14 of 16 mutations killed. MINORs: B1 (a stale private identifier the re-port would have put back into the template), B2 (cross-session note), B3 (`is_file` failure untested), B4 (report). **The single remediation** `3dba892b`, verified at the seat (no further round). |

## Gate

The harness gate is the package's gate (`scripts/` changed; no product file changed, so no pytest leg). On the final head `3dba892b`:
- `uv run python -m unittest discover -s tests/harness` **423 OK (1 skipped), 19.6 s**, unshimmed;
- the project ruff and format clean;
- 0 CR.

The log is `gate\harness-final.txt`. C: has 35 GB free.

## Re-port (the orchestrator's act at this accept; Q3)

The delta is `git diff template/main HEAD -- scripts/cell_depth.py tests/harness/test_cell_depth.py docs/dispatch-recipe.md`: 3 files, +810 / -27.
- It was scanned for instance vocabulary (clearwater, a work-package id, swing, charc, codex, footage, gpu, seed, v17, a user path) and has 0 hits.
- It is applied in `C:\Users\rwsmy\harness-template` on a local branch `clearwater-upstream-2026-11-04`, after checking that `master` = `origin/master` = `refs/remotes/template/main`, with the template's own harness suite run.
- **No push** without the owner's word.

The branch and the template suite result are recorded in CHARC's re-port section of the upstream record.

## Dispositions (for CHARC at this accept)

- **The upstream record** `docs/proofs/harness-upstream-2026-11-02.md`: item 2 is DONE, and the re-port section is CHARC's.
- **Limits carried by the report:**
  - Codex cells are not covered.
  - The parked rule depends on the parent transcript's mtime.
  - Any project-level `*.jsonl` reads as a session.
  - A reused name gives several rows (a NOTE is printed).
  - A 16-hex name can also match an anonymous hash.
  - On Windows, `--session` matches case-insensitively in cell mode but not in `--sessions` mode (B5).
  - The test module must run with `discover -s` (the `_loader` sibling import).
- **Seat lessons:**
  - A reviewer's mutation probes find untested guards that a green suite hides. Both nets did it here.
  - A re-port diff can carry a hunk that predates the package; diff against the template and scan the delta before the accept.

## Merge

`main` is fast-forwarded to the branch head (this record's commit) by the orchestrator. The worktree `.worktrees/wp-h1` is kept until the owner's word.
