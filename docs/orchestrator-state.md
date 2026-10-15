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

- None (verify: `git worktree list` shows only main).
- Branches `wp0.1`, `wp0.2` and `wp1.1` are kept on purpose: they hold the reviewed pre-rebase
  SHAs the accept records cite.

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

- **WP1.1 -- ACCEPTED 2026-10-15**, main `9711faf`, record `docs/proofs/wp1.1-accept.md` (2e09203).
  Return report posted to CHARC (raised: W_L near-inert at defaults, a WP1.3 calibration point);
  operator fyi posted. Awaiting CHARC QA and the next commission.
- Lesson carried forward: every Reviewer B brief's Codex prompt must NAME the withheld paths in
  its own paragraph, plus a transcript `grep -a 'docs/proofs\|<wp>-ledger'` access assertion
  (WP1.1 B pass 1 Codex read the ledger).
- Inbox drained through msg `ad686b8b65a71061` (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
