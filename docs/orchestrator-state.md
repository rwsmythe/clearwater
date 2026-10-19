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

**NONE.** Generation 1 rolled over 2026-10-19 ~00:45Z at this boundary (depth 411K).

### Handoff -- the successor starts HERE

1. **WP1.4 remediation RETURNED; the gate is yours.** It returned 2026-10-19 00:36Z.
   - Branch `wp1.4` head `45fd95b`, base `9ed1a1c`; worktree `.worktrees/wp1.4`, clean. Its
     toml is copied in.
   - **History:**
     - author `wp14-cell` (opus-high), 384K, retired;
     - my seat B pass 1 on `af98ca8`: BLOCKING (M1-M4), md5 `f53b2099...`, evidence
       `clearwater-review-evidence\wp1.4\reviewB\`;
     - ONE remediation `wp14-fix` (sonnet-high), brief `docs/briefs/wp1.4-remediation-brief.md`
       (`179fab0`). It was interrupted at the 10-15 restart and resumed 10-18 by raw id
       `awp14-fix-a7f2718c31740dc1`.
   - **The cell's return** (its full report never reached the seat; it was extracted from
     `subagents/agent-awp14-fix-*.jsonl`):
     - all 12 findings closed;
     - Reviewer A r2 (`63d8422..865a054`): 2 majors (staged nested reach -> `staged_reach`; an
       optional witness) and 3 minors, all fixed. The r2 fixes were NOT re-reviewed (one round
       only);
     - records re-run: every statistic, mismatch, flicker and render figure unchanged; the 3 CP2
       clips have the same md5 (`53f8c671`, `84a0e488`, `77e6a1ac`);
     - section 7 carries CHARC's pts-keying requirement (`0da890ba5a2eb047`), applied in
       `45fd95b`.
   - **Gates at the cell:** 551 passed, **3 skipped** (see item 2); gpu 24.
   - **Your steps:**
     1. Rebuild `wp1.4-mc` with the toml and `uv sync`, and compare patch-ids.
     2. Gate it.
     3. Re-run my witness: main against the candidate with `statistics=None`; scratchpad
        `witness_r.py`; 6 cases, Ancuti blue off and on and 3C, CPU and GPU. It was
        bit-identical 6/6 before the remediation.
     4. ONE seat Reviewer B re-run. Prompt template:
        `clearwater-review-evidence\wp1.4\reviewB\review-prompt-B.md` plus a "THIS IS THE
        RE-RUN" section, as in `wp1.3\reviewB\rerun\`. A 2nd block is adjudicated at the
        gate; never a third remediation.
     5. Merge, re-gate on main, write the accept record, and bank **DR-23** (A12: VFR
        smoothing by index is a prototype limit; CHARC says IF-3 is keyed by pts).
   - **Records note:** the cell's first return quoted 0.76 for the largest staged/flat pixel;
     the records give 0.68 (GX011627) and 0.90 (GX011625).
2. **NEW BLOCKER for "0 skipped": the footage layout changed.**
   - On 2026-10-18 the owner moved the chapters into `Snorkel\` and `SCUBA\` (lowercase
     `.mp4`) and added `edits\`.
   - Three footage tests open `<footage>\GX011628.MP4` at the root and now SKIP:
     - `tests/test_container_spike.py`;
     - `tests/test_lookcheck.py`;
     - WP1.4 test 7.
   - This affects main too. `tools/lookcheck/pack.py` stills and the WP1.4 runner name root
     paths as well.
   - **Proposal:** a small package (sonnet-high) with a shared footage-locator helper (find a
     chapter by stem, case-insensitive, under the footage folder). Fix the tests to use it, then
     re-gate to 0 skipped. Raise it with CHARC first: owned files span WP1.3, WP1.5 and WP1.4
     tests.
   - **Gating WP1.4 meanwhile:** the WP1.4 accept can either wait for this fix, or record the 3
     skips as caused by the layout change and outside the package. Ask CHARC; I recommend
     fixing first, because the fix is small.
3. **Inventory DONE** (`b1fd289`): 35 videos (Snorkel 26, SCUBA 8, edits 1); no chapters;
   photos PENDING. Reported to CHARC (return_report 23:57Z).
4. **WP1.2 Part B:**
   - condition 1 is MET (download complete and the inventory);
   - condition 3 is met;
   - condition 2 waits on the WP1.4 accept.

   The brief is `docs/briefs/wp1.2b-brief.md` (EXCLUSIVE). Note: no chaptered recordings;
   photos pending; the largest clips are in SCUBA.
5. **CHARC's session is now `clearwater-charc-20261014-1303`** (`comms/.launch-sessions.json`).

- **CHARC commission `0fd7c88ad56a7083`:**
  - The owner's partial CP1 ("shallow confirmed") releases WP1.3 and WP1.4, shallow only.
  - The WP1.4 gain-cap noise test becomes WP1.4b (deep footage).
  - Sequencing:
    - inventory pass (sonnet-medium) at once on "download complete";
    - Part B (exclusive) only after WP1.3 and WP1.4 return or pause at a boundary.
- Branches `wp0.1`, `wp0.2`, `wp1.1`, `wp1.2`, `wp1.5`, `wp1.2r`, `wp1.3` and `wp-t1` are kept on purpose: they hold the reviewed
  pre-rebase SHAs the accept records cite (verify: `git worktree list` shows main and `.worktrees/wp1.4`); add `wp1.4` at its accept.

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
- Inbox drained through msg `4114159083a3f639` (generation 1, at rollover). Generation 1 STOPPED DRAINING at the rollover announcement; the successor is the only drainer (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
