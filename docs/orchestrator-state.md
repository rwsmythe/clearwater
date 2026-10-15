# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- First orchestrator generation, session `clearwater-orchestrator-20261014-1258`
  (verify: `comms/.launch-sessions.json`). Brought up 2026-10-14.
- Bash-launch gauge at bring-up: 30 ms (PowerShell `Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`); under the 1 s flag line.

### Standing operator rulings

- Unattended operation (owner, 2026-10-14; standing per CHARC relay `132932a7b891bfa0`, in
  CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended
  answer first, cue after posting). CHARC answers in the operator's stead except plan §3
  owner-reserved items, which come back "HOLD <item>" -- pause that item, continue the rest.
  Info-updates to the operator continue. No AskUserQuestion from this seat.

### Live cells

- **wp02-cell** -- RETURNED; branch `wp0.2` head `a309046` (A converged in 2 rounds); 140K at
  return. Open question routed to CHARC (stored vs display photo dimensions).
- **wp02-reviewer-b** (background) -- Reviewer B on `a309046`, brief
  `docs/briefs/wp0.2-review-brief.md`, evidence `clearwater-review-evidence\wp0.2\B\`.
  Dispatched ~00:05Z 2026-10-15; read-only on the worktree.
- **BLOCKER for any accept:** harness gate red on main (`docs/debt-register.md` unaccounted,
  from CHARC's fe90033); routed to CHARC 00:03Z.
- Branch `wp0.1` is kept on purpose: it holds the reviewed pre-rebase SHAs the WP0.1 accept cites.

### Workstreams

- **WP0.1 -- ACCEPTED 2026-10-14**, main `c09f747`, record `docs/proofs/wp0.1-accept.md`
  (verify: `git log --oneline -- docs/proofs/wp0.1-accept.md`). Return report posted to CHARC;
  info-update to the operator posted. `clearwater.local.toml` created (uncommitted) with the
  owner-set paths; footage folder `C:\Users\rwsmy\clearwater-footage` did not exist yet at accept.
- **WP0.2** (footage inventory) -- commissioned by CHARC (`1b16f4179b32029c`); FINAL brief
  `docs/briefs/wp0.2-brief.md` at `b0287a2`. Grants: Pillow, pillow-heif (dev). Reviewer A fast/WSL.
  Next: QA the return, Reviewer B (write `docs/briefs/wp0.2-review-brief.md` on the WP0.1 model),
  gate in a `-mc` worktree, merge, accept record, report to CHARC, info-update to the operator.
  CP1 (owner sorts footage) follows WP0.2.

### Practice notes from WP0.1 (this instance)

- A SendMessage to a working cell did NOT reach it before it returned; check amendments
  landed in the return, and re-engage the cell if not.
- Cell return reports can arrive truncated; extract the full last message from the transcript
  (`~/.claude/projects/C--Users-rwsmy-clearwater/<session>/subagents/agent-a<name>-*.jsonl`).
- Rebase onto main in a separate `-mc` worktree, compare `git patch-id --stable`, gate there,
  then `git merge --ff-only` on main and re-gate.
- Codex WSL is at codex-cli 0.162.1; luna/medium banner held; its sandbox could not run
  pytest/uv/git on some rounds (findings REASONED).

### Pending

- Inbox drained through msg `1b16f4179b32029c` (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
