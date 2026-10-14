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
(session `clearwater-9b`, launched by hand, not through the launcher). The
repository is initialized locally and mirrored to the private GitHub repository
`rwsmythe/clearwater` (verify: `git -C C:\Users\rwsmy\clearwater remote -v`;
`gh repo view rwsmythe/clearwater --json visibility`).

### Live workstreams

- None dispatched. No orchestrator generation has been brought up yet (bootstrap
  step 5 pending; verify: `comms/.launch-sessions.json` absent or without an
  orchestrator entry, and `ListAgents` shows no `clearwater-orchestrator-*`).
- No cell, no worktree (verify: `git -C C:\Users\rwsmy\clearwater worktree list`).

### Pending items

1. **Owner inputs still open** (CLAUDE.md "Inputs the owner still has to supply"):
   the footage folder path (read-only) and the working folder location. WP0.1's
   local configuration template needs both. Do not guess them.
2. **Owner to confirm** the seam-4 launch defaults (`scripts/launch_role.ps1`:
   CHARC fable/high, orchestrator opus/high, permission-mode auto) and the three
   implementer tiers under `.claude/agents/`.
3. **Next harness act:** bring up the orchestrator (`powershell -NoProfile -File
   scripts/launch_role.ps1 -Role orchestrator`), run the post-step-5 round-trip
   (`--to orchestrator` lands in `comms/orchestrator/inbox` and the generation
   drains it), then commission **WP0.1** (repository scaffolding and
   `tools/environment_report.py`; the brief draft is `docs/briefs/wp0.1-brief.md`
   once written) and WP0.2 (footage inventory) behind it; CP1 follows.
4. **Relaunch CHARC through the launcher** at the next rollover so the hooks see
   `HARNESS_ROLE=charc` natively (the bootstrap session wrote its role-recovery
   record by hand; verify: `comms/roles/<session_id>` holds `charc`).

### Behavioral pointers

- Port **8775** is Clearwater's comms-UI port (`scripts/comms_ui.py` DEFAULT_PORT);
  the sibling harnesses (`coa-chess`, `swing-trading`) default to 8765 and one of
  them is usually listening there. psmux session name derives from the repo
  basename: `clearwater`; claude session names mint `clearwater-<role>-<stamp>`.
- The harness core here is the coa-chess lineage of the template (singular inboxes
  for every role, two hooks, depth-printing prompt hook, psmux launcher,
  `cell_depth.py`), with the second-director role removed. Comms changes route
  through CHARC's architecture pass; keep the core stdlib-only (the harness suite
  enforces it: `uv run python -m unittest discover -s tests/harness`).
- Clearwater's application toolchain is uv + Python 3.12 (`uv sync`, then
  `uv run pytest` / `ruff` / `mypy`); the harness suite is NOT run by pytest
  (`norecursedirs` excludes `tests/harness`).
- Owner-reserved decisions (plan section 3) go to the operator as
  `decision_request`; put the recommended option FIRST, read the owner's word
  back verbatim with its time, and end every turn with the open owner decisions.
- Roll this seat only after ~400K context at a boundary (charter 5.1); commit
  this file by pathspec first.
