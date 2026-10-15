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

- **wp11-cell** (implementer-opus-high, idle) -- WP1.1, worktree `.worktrees/wp1.1`, branch
  `wp1.1`, base `46a10b9`, author head `8e149db` (verify: `git -C .worktrees/wp1.1 log -1`).
  Reviewer A STRONG converged r3. Informal 4K run done (both methods exit 0, 8 levels, coarsest
  17 px; ~14 s / ~26 s informal). Depth 267K at first return.
- **wp11-reviewer-b** (implementer-opus-high, background) -- Reviewer B on `8e149db`, brief
  `docs/briefs/wp1.1-review-brief.md`; evidence `clearwater-review-evidence\wp1.1\B\`.
- Branches `wp0.1` and `wp0.2` are kept on purpose: they hold the reviewed pre-rebase SHAs the
  accept records cite.

### Workstreams

- **WP0.1 -- ACCEPTED 2026-10-14**, main `c09f747`, record `docs/proofs/wp0.1-accept.md`
  (verify: `git log --oneline -- docs/proofs/wp0.1-accept.md`). Return report posted to CHARC;
  info-update to the operator posted. `clearwater.local.toml` created (uncommitted) with the
  owner-set paths; footage folder `C:\Users\rwsmy\clearwater-footage` did not exist yet at accept.
- **WP0.2 -- ACCEPTED 2026-10-15**, main `4863a90`, record `docs/proofs/wp0.2-accept.md`.
  Return report posted to CHARC; info-update to the operator posted. Real inventory run NOT
  done (footage folder absent at accept).
- WP0.2 accept QA'd and STANDS at CHARC (`1822a661d2cbf031`); banked items are DR-6..DR-10.
- **Real inventory pass:** APPROVED in principle (implementer-sonnet-medium, mechanical, no code
  changes) but DISPATCH ONLY ON CHARC'S WORD, posted when the owner reports the download complete.
- **WP1.1** (reference pipeline prototype) -- commissioned (`3f7c2f997b58c6d5`); FINAL brief
  `docs/briefs/wp1.1-brief.md` at `46a10b9`. Grants numpy, scipy (dev). Reviewer A and B STRONG
  (`gpt-5.6-sol` / high); Reviewer B = an independent implementer-opus-high cell. Accept report
  to CHARC must name the ledger, the evidence folder and the two `docs/reports/wp1.1-*.md` docs.

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

- WP1.1 CHARC rulings `ad686b8b65a71061`: Laplacian LoG form ACCEPTED; Q2/Q3 banked DR-11/DR-12;
  the three report edits it required are in `8e149db`. Next: B return -> gate -> merge -> accept.
- Inbox drained through msg `ad686b8b65a71061` (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
