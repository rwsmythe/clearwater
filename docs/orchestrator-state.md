# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- Generation 2, session `clearwater-orchestrator-20261018-1442` (verify:
  `comms/.launch-sessions.json`). Brought up 2026-10-19 00:42Z. Generation 1 was
  `clearwater-orchestrator-20261014-1258`.
- Bash-launch gauge at bring-up: 40 ms (PowerShell `Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`); under the 1 s flag line.

### Standing operator rulings

- Unattended operation (owner, 2026-10-14; standing per CHARC relay `132932a7b891bfa0`, in
  CLAUDE.md "Roles"):
  - Every operator-bound question goes `--to charc` (type query, recommended answer first, cue
    after posting).
  - CHARC answers in the operator's stead, except plan §3 owner-reserved items. Those come back
    as "HOLD <item>": pause that item, continue the rest.
  - Info-updates to the operator continue.
  - No AskUserQuestion from this seat.
- Spec is **v0.5.3** (owner "approved as 0.5.3" 2026-10-19, main `b3fcd86`, CHARC
  `d66e745b6a381bf3`): D16 3C default; chapter handling deferred to v2. Plan **v1.1** (WP3.8
  removed). Cite v0.5.3 in every brief from now. The prototype `Params()` default flips to c3 in
  the next brief touching `tools/prototype` (WP1.4b or the WP1.3 deep part), as a one-line owned
  change with its test update; never inside Part B.

### Live cells

- **None.** `wp12b-cell` (WP1.2 Part B) is RETIRED. Depth at retirement: 931,878 over 428 turns,
  PAST-CAP (`uv run python scripts/cell_depth.py wp12b-cell`). Do not reply to it. The full
  Part B history (stops, rulings, the depth breach) is in `docs/proofs/wp1.2b-accept.md` and
  `git log -- docs/orchestrator-state.md`.
- **Depth rule (owner catch 2026-10-19):** read `cell_depth.py <cell>` at dispatch, at every
  yield, and before sending any ruling or remediation. Record each figure with its moment. Above
  ~250K: never order a multi-finding remediation; re-seat. At ~400K: STOP and re-dispatch fresh.

### Gate inputs

- **Shallow CP2 COMPLETE** (owner 2026-10-19, CHARC `3bac4a724b1420aa`, record
  `docs/proofs/cp2-look-check.md`): c3 default (both Ancuti variants over-red; kept as options);
  no cast, halo, noise, clipping or flicker; staged vs flat no visible difference. Briefs cite
  "c3 default per CP2 2026-10-19, spec revision pending"; prototype `Params()` default stays
  ancuti2018 (not changed inside Part B). WP1.4b and the WP1.3 deep part render c3 primary with
  ancuti2018 beside it. WP1.6: method-default row c3; row 5 input in.

### Handoff -- the successor starts HERE

1. **WP-T2 ACCEPTED** 2026-10-19, main `8c9d780` (record `docs/proofs/wp-t2-accept.md`):
   0 skipped restored; DR-24 CLOSED; DR-27 opened. B's major (linked root) REJECTED with cause.
   Branches `wp-t2`, `wp-t2-b` kept. Worktrees `.worktrees/wp-t2`, `-mc` removable.
2. **CP1 COMPLETE** (owner 2026-10-19, CHARC `99f6abaf9afd829e`): folder-wise categories
   (Snorkel = shallow, SCUBA = deeper ~20 m, edits = stress case), chapter handling DEFERRED to
   v2 (spec revision pending: briefs cite "chapter handling deferred (CP1 2026-10-19; spec
   revision pending)").
3. **WP1.2 Part B ACCEPTED** 2026-10-19, main `2dd06cf` (record `docs/proofs/wp1.2b-accept.md`;
   patch-id `3c25c656`). B #1 blocking -> one remediation; B #2 `NO_NEW_CRITICAL_MAJOR` (6 minor,
   1 advisory), banked at the gate: findings 1/3/5/6/7 banked as DR-28, findings 2/4 fixed as report errata. Witness rule
   (4) GOP-start through the next I/P anchor; frame 503 NOT BLOCKING. Branches `wp1.2b`,
   `wp1.2b-b1` kept. CHARC QA CONFIRMED (`cb61a4e41f625d73`; patch-id erratum corrected; harness
   366 OK at CHARC's seat; CHARC's pytest re-gate was also killed for low memory).
   **OWED: the full re-gate on main** (pytest, `-m gpu`, harness). Claude Code stopped the
   background run for low system memory during pytest; ruff/format/mypy were green on main, and
   the candidate (= the same commit) was fully green. Re-run it when the owner clears it or
   before the next merge, whichever comes first.
4. **Next:** the deep parts (WP1.3 deep cases, WP1.4b gain-cap noise test) on SCUBA/; the order
   is mine (CHARC). Render c3 primary with ancuti2018 beside it. The first brief touching
   `tools/prototype` flips `Params()` to c3 (one owned line plus its test); cite spec v0.5.3.
   Then WP1.6 (gate report; smoothing row "2 s provisional, re-measure per DR-25(3)"; Gate 1
   and Gate 2 rest on Part B's figures with the "shared non-idle laptop, upper bound" caveat;
   N6 not met, about 2.3x combined; photo leg PENDING).

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
| WP-T1 | 2026-10-15 | `f6a34a4` | `docs/proofs/wp-t1-accept.md` (`3f40a85`); 2nd B adjudicated at the gate; DR-9 and DR-21 closed, DR-22 opened | CONFIRMED (`3501648bc8844468`) |
| WP1.4 | 2026-10-19 | `91f5775` | `docs/proofs/wp1.4-accept.md`; 2nd B adjudicated at the gate; DR-23..DR-26 | CONFIRMED (`6c5d88685e64a37c`; finding 3 upheld; DR-26 stays banked) |
| WP-T2 | 2026-10-19 | `8c9d780` | `docs/proofs/wp-t2-accept.md`; DR-24 closed, DR-27 | CONFIRMED (`d40217a81696cc03`; B rejection upheld; suite re-run deferred past Part B) |
| WP1.2 Part B | 2026-10-19 | `2dd06cf` | `docs/proofs/wp1.2b-accept.md`; B #2 non-blocking, banked; DR-28; depth breach recorded | CONFIRMED (`cb61a4e41f625d73`; patch-id erratum) |

- **WP1.2 Part A, raised to CHARC:**
  - approval of the Windows-only `_windows_power()` in `bench.py` (instrument only, guarded);
  - the NVIDIA wheel licences for WP2.1 (N13);
  - the Gate 1 signal: the GPU core is 3.5-13.5x the N6 budget.

  WP1.2 Part B comes later (after footage and WP1.5); CHARC commissions it.
- **WP1.5:** accepted (see the table). The recommendation is SIMPLE; Gate 6 is CHARC's at WP1.6.
- **Real inventory pass: DONE.** On main at `b1fd289` (`docs/reports/inventory-2026-10-18.md`).
  The return report went to CHARC 2026-10-18 23:57Z.
  - Counts: 35 videos (Snorkel 26, SCUBA 8, `edits` 1 lowercase); 0 errors.
  - No chaptered recordings. Photos are PENDING.
  - Counts re-derived from the CSV at my seat; the CSV and summary md5s verified.
  - The WP0.2 footage test passes and is stable.
  - **WP1.2 Part B:** condition 1 is MET and condition 3 is met. Condition 2 waits on the
    WP1.4 accept.

### Practice notes (this instance)

- **No commit on main while a B candidate is under review** (gen 2 slip, WP1.4): my state
  commit moved main, so the merged head differed from the B-reviewed SHA by the state files
  (recorded in the accept). Hold state edits uncommitted until the merge.
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

- **Kernel-doc touch owed (CHARC `cb61a4e41f625d73`):** put the depth thresholds (no
  multi-finding remediation above ~250K; STOP and re-dispatch at ~400K; read depth at dispatch,
  every yield and before any ruling) into `docs/orchestrator-context.md` at the next kernel-doc
  change, with the harness gate.
- **WP1.6 gate report** (CHARC `6c5d88685e64a37c`): the smoothing-default row reads "2 s
  provisional, re-measure per DR-25(3)", never a settled 2 s.
- **WP1.5 ACCEPTED and CONFIRMED.**
- **Retroactive Reviewer B: CLOSED via WP1.2R** (accepted at 10:25Z, return report and operator
  fyi posted).
  - The 2nd-B major (method-agnostic C3 validation) was adjudicated NOT BLOCKING at the gate
    and banked as DR-19.
  - DR-18 (the WP1.5 pass-2 minors) is in the debt register.
  - The WP1.1 envelope is narrowed to a short side above 128 px.
  - CHARC QA: CONFIRMED; adjudication upheld.
- Spec is v0.5.3 (see Standing operator rulings). WP1.2 Part B is DONE (Handoff item 3).
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
- Inbox drained through msg `4114159083a3f639` (generation 1, at rollover). Generation 1 STOPPED DRAINING at the rollover announcement; the successor is the only drainer (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
