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
- Spec is **v0.5.2** (`9042ae0`, D60 closed, owner-approved). Cite v0.5.2 in every brief.

### Live cells

- **wp14-cell** (implementer-opus-high, background): WP1.4, the statistics experiments
  (shallow part). Dispatched ~13:27Z.
  - FINAL brief `docs/briefs/wp1.4-brief.md` (`9ed1a1c`); worktree `.worktrees/wp1.4` (local toml
    copied in); base `9ed1a1c`; outputs `work\wp1.4\`.
  - At the gate:
    - my seat Reviewer B on the `-mc` candidate;
    - re-run the WP1.2R bit-identity witness on `correct()` with `statistics=None` (Ancuti
      blue off and on, and 3C; CPU and GPU; scratchpad `witness_r.py` pattern);
    - gate, merge, accept.
- **wpt1-cell** (implementer-sonnet-high, background): WP-T1, the pytest temp-root footage
  guard; closes DR-21. CHARC YES `5a9d76593e090e89`.
  - FINAL brief `docs/briefs/wp-t1-brief.md` (`34d2ccd`); worktree `.worktrees/wp-t1`; base
    `34d2ccd`. Dispatched ~13:31Z.
  - Tier STRONG (the fill has no STANDARD); one Reviewer A round; then my seat B.
  - At the gate:
    - the harness gate runs (`tests/` changes);
    - check that no test names the real footage folder.

  CHARC adds the CLAUDE.md line at accept.
- **CHARC commission `0fd7c88ad56a7083`:**
  - The owner's partial CP1 ("shallow confirmed") releases WP1.3 and WP1.4, shallow only.
  - The WP1.4 gain-cap noise test becomes WP1.4b (deep footage).
  - Sequencing:
    - inventory pass (sonnet-medium) at once on "download complete";
    - Part B (exclusive) only after WP1.3 and WP1.4 return or pause at a boundary.
- Branches `wp0.1`, `wp0.2`, `wp1.1`, `wp1.2`, `wp1.5`, `wp1.2r` and `wp1.3` are kept on purpose: they hold the reviewed
  pre-rebase SHAs the accept records cite (verify: `git worktree list` shows main, `.worktrees/wp1.4` and `.worktrees/wp-t1`).

### Workstreams

Each accepted package had its return report posted to CHARC and an info-update to the operator.

| Package | Accepted | Main | Record | CHARC QA |
|---|---|---|---|---|
| WP0.1 | 2026-10-14 | `c09f747` | `docs/proofs/wp0.1-accept.md` | STANDS |
| WP0.2 | 2026-10-15 | `4863a90` | `docs/proofs/wp0.2-accept.md` | STANDS (DR-6..DR-10) |
| WP1.1 | 2026-10-15 | `9711faf` | `docs/proofs/wp1.1-accept.md` | STANDS (DR-11..DR-13) |
| WP1.2 Part A | 2026-10-15 | `f6d998a` | `docs/proofs/wp1.2-accept.md` (`7048fd7`) | STANDS (`bac37599277c1365`) |
| WP1.5 | 2026-10-15 | `3242679` | `docs/proofs/wp1.5-accept.md` (`371f19d`) | CONFIRMED (`6d4fca629d21efe0`) |
| WP1.2R | 2026-10-15 | `996274e` | `docs/proofs/wp1.2r-accept.md` (`aac4674`); WP1.1/1.2 addenda | CONFIRMED (`60dc8ad66427bb15`) |
| WP1.3 | 2026-10-15 | `7178540` | `docs/proofs/wp1.3-accept.md` (`bc97a19`); 2nd B adjudicated at the gate; DR-20, DR-21 | CONFIRMED (`09057ee4b3979fa4`) |

- **WP1.2 Part A, raised to CHARC:**
  - approval of the Windows-only `_windows_power()` in `bench.py` (instrument only, guarded);
  - the NVIDIA wheel licences for WP2.1 (N13);
  - the Gate 1 signal: the GPU core is 3.5-13.5x the N6 budget.

  WP1.2 Part B comes later (after footage and WP1.5); CHARC commissions it.
- **WP1.5:** accepted (see the table). The recommendation is SIMPLE; Gate 6 is CHARC's at WP1.6.
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

- **WP1.5 ACCEPTED and CONFIRMED.**
- **Retroactive Reviewer B: CLOSED via WP1.2R** (accepted at 10:25Z, return report and operator
  fyi posted).
  - The 2nd-B major (method-agnostic C3 validation) was adjudicated NOT BLOCKING at the gate
    and banked as DR-19.
  - DR-18 (the WP1.5 pass-2 minors) is in the debt register.
  - The WP1.1 envelope is narrowed to a short side above 128 px.
  - CHARC QA: CONFIRMED; adjudication upheld.
- **Spec is v0.5.2** (`9042ae0`; D60 CLOSED). WP1.2 Part B cites v0.5.2 and measures decode
  only.
- **WP1.2 Part B:** draft `docs/briefs/wp1.2b-brief.md` (CHARC `dc733650e60ac026`;
  opus-high, STRONG, EXCLUSIVE). Dispatch only when all three hold:
  1. "download complete" AND the inventory report;
  2. WP1.3 and WP1.4 merged or paused at a boundary;
  3. WP1.5 merged (done).

  The gate-report template is `docs/reports/wp1.6-gate-report.md`.
- **No .LRV/.THM exist** (owner; CHARC `93c5af007a3a8ba8`).
  - WP1.2 Part B drops the LRV analysis-speed leg (two columns: software decode and hardware
    decode).
  - In the inventory pass, the LRV column is all-absent: one line, not a gap.
  - D60 stays OPEN pending CHARC's spec proposal.
- Gate hazard: the WP0.2 test `test_real_footage_has_one_row_per_media_file` fails while the
  SCUBA download runs (its footage snapshot changes). If it fails at the gate, show the cause
  and re-run after CHARC confirms the download is complete.
- CHARC approved `_windows_power()` as instrument-only (never into `src/clearwater/` without a
  fresh ruling).
- Inbox drained through msg `09057ee4b3979fa4` (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
