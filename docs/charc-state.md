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
section 6). Second CHARC generation, `clearwater-charc-20261014-1257`, the first
launched through `scripts/launch_role.ps1` (fable/medium). Bootstrap steps 1-4 were
done by the first generation; this generation re-verified comms (CHARC-side
round-trip 2026-10-14T22:57Z, both hooks import clean) and executed step 5.
Repository local + mirrored to private GitHub `rwsmythe/clearwater` (verify:
`git -C C:\Users\rwsmy\clearwater remote -v`; `git status -sb`).

**Bash-launch gauge (bootstrap step 2):** 47 ms for one `bash-cc.exe -c true`
(2026-10-14; re-measure with PowerShell
`Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`). Under the 1 s flag.

### Live workstreams

- **Orchestrator generation** `clearwater-orchestrator-20261014-1258` (opus/high/auto,
  confirmed by the owner; verify: `comms/.launch-sessions.json`, `ListAgents`).
- **WP0.1 ACCEPTED and merged** (main c09f747, accept record `docs/proofs/wp0.1-accept.md`,
  ledger `docs/proofs/wp0.1-ledger.md`). CHARC QA 2026-10-14T23:45Z: four gates + harness
  gate re-run green at this seat; `clearwater.local.toml` (uncommitted) loads with the two
  owner paths; `footage_available()` False until the download lands. Branch `wp0.1` kept.
- **WP0.2 commissioned** 2026-10-14T23:45Z (draft brief `docs/briefs/wp0.2-brief.md`,
  main b415faf; cell `implementer-sonnet-high`; tripwire pass: dev-group grants Pillow +
  pillow-heif). **DISPATCHED 2026-10-14T23:47Z**: cell `implementer-sonnet-high` in
  `.worktrees/wp0.2` (branch `wp0.2`, base b0287a2); seven brief decisions ruled accepted
  by CHARC at ~23:50Z. That worktree is OCCUPIED until the orchestrator records the
  cell's return. Verify: `git worktree list`, `docs/orchestrator-state.md`.
- Debt register opened: `docs/debt-register.md` (DR-1..DR-5).
- No authority granted by `SendMessage` this generation (cues only).

### Pending items

1. **Owner decision request 2026-10-14T23:45Z** (`comms/operator/inbox/...-c4281ff7.md`):
   spec text amendments recording the measured CPU/GPU (D117, section 12, 14.2, Q1).
   Recommended: approve as written; CHARC applies as a docs(spec) commit. Debt register DR-5.
2. **Next harness act:** QA the WP0.2 accept when it lands; then CP1 (owner sorts the
   inventory into categories: owner-reserved, decision_request). Phase 1 commissions
   follow CP1 (WP1.1 can start before CP1: it needs one image, not the inventory).
3. Main is ~36 commits ahead of `origin/main`, unpushed; the owner has not asked for a push.
4. Footage download in progress into `C:\Users\rwsmy\clearwater-footage\` (owner).

### Standing delegation (owner, 2026-10-14, chat to CHARC, verbatim)

"intent is for this development to run as unattended as possible. orchestrator
will send you operator related questions. Answer for operator unless the question
truly requires my input." Standing, not day-scoped (it superseded the ~23:12Z
"today" ruling given to the orchestrator). Recorded in CLAUDE.md "Roles". CHARC
answers in the operator's stead; the plan section 3 owner-reserved list is the
only trigger for a `decision_request` (the orchestrator HOLDS that item, continues
the rest). Read every answer back to the owner in the turn's recap so they can
override.

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
- Review gate: `docs/review-gate-clearwater.md` (Codex via WSL, tiers `strong` for
  product code, `fast` for docs/tools); the orchestrator runs it, CHARC QAs the
  orchestrator's product at the phase audit.
- Owner-reserved decisions (plan section 3) go to the operator as
  `decision_request`; put the recommended option FIRST, read the owner's word
  back verbatim with its time, and end every turn with the open owner decisions.
- Roll this seat only after ~400K context at a boundary (charter 5.1); commit
  this file by pathspec first; the outgoing seat stops draining (peek only).
