# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- First orchestrator generation, session `clearwater-orchestrator-20261014-1258`
  (verify: `comms/.launch-sessions.json`). Brought up 2026-10-14.
- Bash-launch gauge at bring-up: 30 ms (PowerShell `Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`); under the 1 s flag line.

### Live cells

- None (verify: `git worktree list` shows only the main tree).

### Workstreams

- **WP0.1** -- draft brief `docs/briefs/wp0.1-brief.md` (CHARC). Not yet commissioned to
  this seat; awaiting CHARC's commission. Owner paths (footage folder, working folder)
  still open; the cell can run end to end with `--out <tmp>` without them.
- WP0.2 queued behind WP0.1; CP1 follows.

### Pending

- Inbox empty at pickup (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
