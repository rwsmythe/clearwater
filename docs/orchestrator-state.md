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

- None (verify: `git worktree list` shows only the main tree). Branches `wp0.1` and `wp0.2` are
  kept on purpose: they hold the reviewed pre-rebase SHAs the accept records cite.

### Workstreams

- **WP0.1 -- ACCEPTED 2026-10-14**, main `c09f747`, record `docs/proofs/wp0.1-accept.md`
  (verify: `git log --oneline -- docs/proofs/wp0.1-accept.md`). Return report posted to CHARC;
  info-update to the operator posted. `clearwater.local.toml` created (uncommitted) with the
  owner-set paths; footage folder `C:\Users\rwsmy\clearwater-footage` did not exist yet at accept.
- **WP0.2 -- ACCEPTED 2026-10-15**, main `4863a90`, record `docs/proofs/wp0.2-accept.md`.
  Return report posted to CHARC; info-update to the operator posted. Real inventory run NOT
  done (footage folder absent at accept).
- **Next (recommended to CHARC, awaiting word):** once the footage folder exists, a mechanical
  implementer-sonnet-medium pass runs `uv run python tools/inventory.py` into `work/reports`
  and reports counts and any uncovered GoPro names; that output feeds CP1 (owner-reserved
  footage sorting).

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

- Inbox drained through msg `800be25ceb015347` (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
