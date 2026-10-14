# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- First orchestrator generation, session `clearwater-orchestrator-20261014-1258`
  (verify: `comms/.launch-sessions.json`). Brought up 2026-10-14.
- Bash-launch gauge at bring-up: 30 ms (PowerShell `Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`); under the 1 s flag line.

### Live cells

- **wp01-cell** (implementer-sonnet-high, background subagent) -- WP0.1, worktree
  `.worktrees/wp0.1`, branch `wp0.1`, base `214f2b2`. Dispatched 2026-10-14 ~23:10Z; round 0
  (building). Depth not yet read (read with `scripts/cell_depth.py` at the round gate).
  A successor RE-DISPATCHES from the branch head + ledger; the cell dies with this generation.

### Workstreams

- **WP0.1** -- commissioned by CHARC (msg `e6c9aa020250139a`); FINAL brief
  `docs/briefs/wp0.1-brief.md` at `214f2b2`. Reviewer A = fast tier, WSL. Next: on return,
  QA + dispatch Reviewer B (a different cell, same tier), then gate + merge, accept record in
  `docs/proofs/`, report to CHARC, info-update to operator. Owner paths still open
  (CHARC posted the decision_request 22:59Z); the cell runs with `--out <tmp>`.
- WP0.2 queued behind WP0.1; CP1 follows.

### Pending

- Inbox drained through the WP0.1 commission (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
