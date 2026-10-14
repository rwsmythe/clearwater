# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- First orchestrator generation, session `clearwater-orchestrator-20261014-1258`
  (verify: `comms/.launch-sessions.json`). Brought up 2026-10-14.
- Bash-launch gauge at bring-up: 30 ms (PowerShell `Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`); under the 1 s flag line.

### Standing operator rulings

- 2026-10-14 ~23:12Z, owner in chat to the orchestrator, verbatim: "Intent is for you to run
  unattended today. Send all operator questions to CHARC for answering. CHARC will answer
  and/or pause execution for my response." So: no AskUserQuestion and no direct operator asks
  from this seat today; every question goes `--to charc`. Info-updates to the operator continue.
- SUPERSEDED in scope by the owner's word to CHARC (relayed msg `132932a7b891bfa0`, now in
  CLAUDE.md "Roles"): standing, not day-scoped. Every operator-bound question goes `--to charc`
  (type query, recommended answer first, cue after posting); CHARC answers in the operator's
  stead except plan §3 owner-reserved items, which come back "HOLD <item>" -- pause that item,
  continue everything else.

### Live cells

- **wp01-cell** -- RETURNED (converged in 2 rounds, Reviewer A fast/WSL); branch `wp0.1` head
  `ad1acd5` (report_version amendment in 0fa8315, no extra round per CHARC). Depth 82K at return.
- **wp01-reviewer-b** -- RETURNED BLOCKING on `ad1acd5` (F1 major: UTF-16 config ->
  uncaught UnicodeDecodeError in load_local_config/footage_available; F2-F5 minor). Evidence
  `clearwater-review-evidence\wp0.1\B\`. Codex pass luna/medium, VERDICT BLOCKING.
- **wp01-cell** re-engaged ~23:28Z to fix F1-F5 + one Reviewer A round 3 on the delta.
  Next: B re-check pass on the fixed head (same B brief, B's transcript must cover the merged
  tree), then gate + merge.

### Workstreams

- **WP0.1** -- commissioned by CHARC (msg `e6c9aa020250139a`); FINAL brief
  `docs/briefs/wp0.1-brief.md` at `214f2b2`. Reviewer A = fast tier, WSL. Next: on return,
  QA + dispatch Reviewer B (a different cell, same tier), then gate + merge, accept record in
  `docs/proofs/`, report to CHARC, info-update to operator. Owner paths still open
  (CHARC posted the decision_request 22:59Z); the cell runs with `--out <tmp>`.
- WP0.2 queued behind WP0.1; CP1 follows.

### Pending

- **At the WP0.1 accept (CHARC msg `4fb4fa87dd7edbab`):** create the uncommitted
  `clearwater.local.toml` in the main tree from the merged template with footage
  `C:\Users\rwsmy\clearwater-footage\` and working `C:\Users\rwsmy\clearwater\work\` (both
  owner-set 2026-10-14, recorded in CLAUDE.md); confirm `load_local_config()` accepts it; tell
  the operator to run `uv run python tools/environment_report.py`. Then WP0.2 can be commissioned
  (inventory must treat an in-progress footage download as a read-only snapshot).
- Brief amendment sent to the cell: `report_version: 1` first JSON key (CHARC advisory).
- Inbox drained through msg `4fb4fa87dd7edbab` (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
