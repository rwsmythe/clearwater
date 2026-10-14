# CHARC -- Current State (the read-me-FIRST pointer)

> **Convention (CHARC-authored harness-architecture).** This file is the SINGLE
> current-state pointer for the director (CHARC). It is **OVERWRITTEN each
> session** -- it always reflects only the live now, never accumulated history.
> Narrative lives in `git log -- docs/charc-state.md`. **The bootstrap reads THIS
> file FIRST**, then the charter. Every fact below carries the method that
> re-verifies it; a successor re-runs the method rather than inheriting the fact.

---

### Phase / state

Phase 0 of the implementation plan (`docs/clearwater-implementation-plan.md`
section 6). Harness bootstrapped 2026-10-14 by the first CHARC generation
(hand-launched session `clearwater-9b`), which ROLLED OVER at ~423K context after
the owner's launch-default correction; the successor is the first generation
launched through `scripts/launch_role.ps1` (fable/medium). The repository is
initialized locally and mirrored to the private GitHub repository
`rwsmythe/clearwater` (verify: `git -C C:\Users\rwsmy\clearwater remote -v`;
`git -C C:\Users\rwsmy\clearwater status -sb`).

### Live workstreams

- None dispatched. No orchestrator generation has been brought up yet (bootstrap
  step 5 pending; verify: `comms/.launch-sessions.json` has no orchestrator entry
  and `ListAgents` shows no `clearwater-orchestrator-*`).
- No cell, no worktree (verify: `git -C C:\Users\rwsmy\clearwater worktree list`).
- No authority was granted by `SendMessage` in the outgoing generation; the two
  sibling CHARCs' replies (comms lessons) are folded into the docs, nothing owed.

### Pending items

1. **Owner inputs still open** (CLAUDE.md "Inputs the owner still has to supply"):
   the footage folder path (read-only) and the working folder location. WP0.1's
   local configuration template needs both for the real run. Do not guess them.
2. **Owner rulings recorded 2026-10-14:** CHARC launches at fable/medium (launcher
   seam-4 table, `scripts/launch_role.ps1`), verbatim "The harness should launch
   CHARC as fable medium." The orchestrator default (opus/high) and the three cell
   tiers under `.claude/agents/` have NOT been explicitly confirmed; raise them
   once with the recommended option first.
3. **Next harness act:** bring up the orchestrator (`powershell -NoProfile -File
   scripts/launch_role.ps1 -Role orchestrator`), run the post-step-5 round-trip
   (`--to orchestrator` lands in `comms/orchestrator/inbox` and the generation
   drains it), then commission **WP0.1** from the draft brief
   `docs/briefs/wp0.1-brief.md` (the orchestrator issues the final brief) and
   WP0.2 (footage inventory) behind it; CP1 follows.

### Behavioral pointers

- Port **8775** is Clearwater's comms-UI port (`scripts/comms_ui.py` DEFAULT_PORT);
  the sibling harnesses (`coa-chess`, `swing-trading`) default to 8765 and one of
  them is usually listening there. psmux session name derives from the repo
  basename: `clearwater`; claude session names mint `clearwater-<role>-<stamp>`
  (read the live name from `comms/.launch-sessions.json` before any cue).
- The harness core here is the coa-chess lineage of the template (singular inboxes
  for every role, two hooks, depth-printing prompt hook, psmux launcher,
  `cell_depth.py`), with the second-director role removed. Comms changes route
  through CHARC's architecture pass; keep the core stdlib-only (the harness suite
  enforces it: `uv run python -m unittest discover -s tests/harness`, 366 tests).
- Clearwater's application toolchain is uv + Python 3.12 (`uv sync`, then
  `uv run pytest` / `ruff` / `mypy`); the harness suite is NOT run by pytest
  (`norecursedirs` excludes `tests/harness`). FFmpeg is not installed yet (WP0.1).
- Owner-reserved decisions (plan section 3) go to the operator as
  `decision_request`; put the recommended option FIRST, read the owner's word
  back verbatim with its time, and end every turn with the open owner decisions.
- Roll this seat only after ~400K context at a boundary (charter 5.1); commit
  this file by pathspec first; the outgoing seat stops draining (peek only).
