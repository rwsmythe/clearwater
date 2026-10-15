# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- First orchestrator generation, session `clearwater-orchestrator-20261014-1258`
  (verify: `comms/.launch-sessions.json`). Brought up 2026-10-14.
- Bash-launch gauge at bring-up: 30 ms (PowerShell `Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`); under the 1 s flag line.

### Standing operator rulings

- Unattended operation (owner, 2026-10-14; standing per CHARC relay `132932a7b891bfa0`, in
  CLAUDE.md "Roles"):
  - Every operator-bound question goes `--to charc` (type query, recommended answer first, cue
    after posting).
  - CHARC answers in the operator's stead, except plan §3 owner-reserved items. Those come back
    as "HOLD <item>": pause that item, continue the rest.
  - Info-updates to the operator continue.
  - No AskUserQuestion from this seat.
- Spec is **v0.5.1** (`073ca1f`, owner-approved). Cite v0.5.1 in every brief.

### Live cells

- **wp12r-cell** (implementer-sonnet-high, background): WP1.2R, the prototype remediation after
  the retroactive Reviewer B (BLOCKING; transcript md5 `dd65ac31...`, evidence
  `clearwater-review-evidence\prototype-retroB\`).
  - Brief `docs/briefs/wp1.2r-brief.md` (`fb36e00`); worktree `.worktrees/wp1.2r` (local toml
    copied in).
  - Scope: M1, M2, M3 (ruled option (a), CHARC `2b3066dac88ed847`), m5, m7.
  - Then: my seat Reviewer B re-run on the `-mc` candidate (prompt neutral, SHAs refreshed),
    gate, merge, accept.
  - Then ONE commit with:
    - the addenda to `wp1.1-accept.md` and `wp1.2-accept.md`, naming both transcripts;
    - the M4 envelope narrowing (short side above 128 px at the defaults);
    - DR-18 (the WP1.5 pass-2 minors, owner WP3.10).
- Branches `wp0.1`, `wp0.2`, `wp1.1`, `wp1.2` and `wp1.5` are kept on purpose: they hold the reviewed
  pre-rebase SHAs the accept records cite (verify: `git worktree list` shows main only).

### Workstreams

Each accepted package had its return report posted to CHARC and an info-update to the operator.

| Package | Accepted | Main | Record | CHARC QA |
|---|---|---|---|---|
| WP0.1 | 2026-10-14 | `c09f747` | `docs/proofs/wp0.1-accept.md` | STANDS |
| WP0.2 | 2026-10-15 | `4863a90` | `docs/proofs/wp0.2-accept.md` | STANDS (DR-6..DR-10) |
| WP1.1 | 2026-10-15 | `9711faf` | `docs/proofs/wp1.1-accept.md` | STANDS (DR-11..DR-13) |
| WP1.2 Part A | 2026-10-15 | `f6d998a` | `docs/proofs/wp1.2-accept.md` (`7048fd7`) | STANDS (`bac37599277c1365`) |
| WP1.5 | 2026-10-15 | `3242679` | `docs/proofs/wp1.5-accept.md` (`371f19d`) | CONFIRMED (`6d4fca629d21efe0`) |

- **WP1.2 Part A, raised to CHARC:**
  - approval of the Windows-only `_windows_power()` in `bench.py` (instrument only, guarded);
  - the NVIDIA wheel licences for WP2.1 (N13);
  - the Gate 1 signal: the GPU core is 3.5-13.5x the N6 budget.

  WP1.2 Part B comes later (after footage and WP1.5); CHARC commissions it.
- **WP1.5:** dispatched (see Live cells). The accept report must carry the comparison table, the
  capability record and the recommendation.
- **Real inventory pass:** QUEUED. It is APPROVED in principle (implementer-sonnet-medium,
  mechanical), but dispatch only on CHARC's word that the download is complete.
  - Present now: 4 shallow chapters, GX011625-GX011628.
  - Still downloading: the scuba clips and the photos.

### Practice notes (this instance)

- **Cell messages and reports:**
  - A SendMessage to a working cell may land only after it returns. Check that amendments
    landed, and re-engage the cell if not.
  - Truncated cell reports: extract the last assistant text from
    `~/.claude/projects/C--Users-rwsmy-clearwater/<session>/subagents/agent-a<name>-*.jsonl`.
- **Merging:** rebase in a `-mc` worktree, compare `git patch-id --stable`, gate there, then
  `git merge --ff-only` on main, `uv sync`, and re-gate (pytest, `-m gpu`, harness).
- **Reviewer B = MY OWN single Codex pass at this seat on the merge candidate, NEVER a cell**
  (owner catch 2026-10-15; fill corrected `30483f2`, Part 2 item 2).
  - Evidence: `B/run_review_B.sh`, `B/review-prompt-B.md`, `B/review-B.txt`, with md5s.
  - Every critical or major is dispositioned: introduced -> one remediation + one B re-run;
    pre-existing -> banked.
  - No transcript, no accept.
  - A heavy mechanical reproduction may go to a sonnet-medium cell, as QA evidence only.
- **Codex:**
  - WSL, codex-cli 0.162.1.
  - Every Codex prompt NAMES the withheld paths, and every transcript gets the
    `grep -a 'docs/proofs\|<wp>-ledger'` access assertion (lesson from WP1.1 B pass 1).
- **Exclusive bench windows:** the harness gate and pytest count as HEAVY. Run neither at this
  seat while a bench window is open (CHARC `122f9a10cf1323f5`; my 05:29Z slip).
- **Worktrees:** a `-mc` worktree holding a copied `clearwater.local.toml` needs
  `git worktree remove --force` (the copied file is untracked).
- **Process control:** the auto-mode classifier blocks `Stop-Process` at this seat. Surface such
  a step to the user and do not work around it.

### Pending

- **WP1.5 ACCEPTED** (main `3242679`, record `371f19d`). Return report and operator fyi posted
  09:27Z. Reviewer B pass 1 BLOCKING (B1-B10, DR-16/17); pass 2 NO_NEW_CRITICAL_MAJOR. Pass-2
  minors are recorded for WP3.10. Awaiting CHARC QA.
- **Retroactive Reviewer B** (CHARC `2b6dae230aa9749a`), AFTER the WP1.5 accept, not exclusive:
  - one pass on main, cwd the main tree;
  - input `git diff -U8 46a10b9..f6d998a -- tools/prototype tests/test_prototype_pipeline.py tests/test_prototype_backend.py`;
  - findings dispositioned (introduced -> fix; pre-existing -> banked);
  - an addendum to the wp1.1 and wp1.2 accept records names the transcript.
- Gate hazard: the WP0.2 test `test_real_footage_has_one_row_per_media_file` fails while the
  SCUBA download runs (its footage snapshot changes). If it fails at the gate, show the cause
  and re-run after CHARC confirms the download is complete.
- CHARC approved `_windows_power()` as instrument-only (never into `src/clearwater/` without a
  fresh ruling).
- Inbox drained through msg `2b3066dac88ed847` (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
