# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 27** (session `clearwater-orchestrator-20261029-1830`; CHARC gen 9 `clearwater-charc-20261029-1554`; re-verify both in `comms/.launch-sessions.json`). Bash gauge at bring-up: 37 ms. **ROLLED OVER 2026-10-30 ~06:45Z at ~405K.**
- **Disk:** C: 174 GB free at 06:40Z (D: 2.4 TB). Run `df -h /c` before every window, gate and footage run. STOP below 15 GB free (20 GB for WP3.6P).
- **Paces at 06:40Z:** Codex 0.415 (11 % at 26.5 %), Claude 1.45 (80 % at 55.2 %), from `scripts/usage_codex.py` and `scripts/usage_claude.py`. The owner's lane rule: lean on Codex where task fit allows, and report the share at each commission.

#### Done by gen 27

- WP4.3: CHARC QA CONFIRMED (`39dad78f`). Worktrees `wp4.3`, `wp4.3-mc` and `wp4.3-rev` removed; branches kept.
- WP4.6 brief FINAL on main (`7eadebe` + `b6a31b5`; `7eadebe` had CRLF, `b6a31b5` restored LF; see the memory `crlf-checkout-autocrlf-override`).
- Two packages dispatched and run in parallel (details below).

#### PAUSED BY THE OWNER (binding on gen 28)

Owner, in chat to gen 27 at ~06:45Z, verbatim: "once you have rolled over, we will pause execution".

**Gen 28 starts PAUSED:**
- Bring up, read this file, drain the inbox, and post the online announce to CHARC saying PAUSED.
- Then do NOTHING else: no dispatch, no Codex turn, no Reviewer pass, no seat run, no window, no gate.
- Hold until the owner says resume, in chat to the orchestrator or relayed by CHARC with the owner's words.
- Mail may be drained and answered (fyi or status) while paused; a ruling is recorded but not acted on.

#### Live work at write (RESUME HERE, gen 28, AFTER the owner's resume)

**1. WP3.6P (Codex lane; brief `docs/briefs/wp3.6p-brief.md` FINAL; worktree `.worktrees/wp3.6p`, branch `wp3.6p`, head `081f851c`, base `c3bf602`).**
- **State:** Reviewer A round 2 is ADJUDICATED and CHARC has RULED it (`688ef40f`). Turn 7 (the R2 remediation) is NOT started.
- **NEXT:** run turn 7 with the prompt I wrote, `C:\Users\rwsmy\clearwater-review-evidence\wp3.6p\cell\prompt-7.md` (the ruling verbatim):
  `uv run python scripts/codex_cell.py turn --worktree 'C:\Users\rwsmy\clearwater\.worktrees\wp3.6p' --prompt '...\wp3.6p\cell\prompt-7.md' --evidence '...\wp3.6p\cell' --turn 7 --session 01a18b4b-e164-7ee3-9c4a-dc7411e622a7`, in the background, stdout to `cell\turn-7.driver.stdout`.
  - Fix the prompt's header line "orchestrator generation 28" if needed.
  - Then commit with `codex_cell.py commit --return-file ...\return-7.md`.
  - Then the seat checks: `ruff format --check`, `ruff check`, the light pytest with `QT_QPA_PLATFORM=offscreen`, and 0 CR per blob.
  - Then Reviewer A round 3: copy `wp3.6p\r2\review-prompt-r2.md` to `r3\review-prompt-r3.md`, change the round, head and probe folder, add `688ef40f` to "Accepted by ruling" and the R2 fixes to the context list, and run `codex_cell.py review --base c3bf602 --out ...\r3`.
- **Sessions:**
  - Codex session 1 (`01a18b14-...`) built turns 1-3 and RETIRED after GREEN at 240,970.
  - Codex session 2 (`01a18b4b-e164-7ee3-9c4a-dc7411e622a7`) is LIVE: 114,259 after turn 4, 178,999 after turn 5, 101,571 after turn 6 (its context was compacted).
  - Codex STOP line: near 250K.
- **Rulings (all verbatim in the ledger and in `comms/orchestrator/read/`):**
  - Brief `2e95deaf`.
  - Q3 RE-RULED `e40b0d7b`: the oracle is FFmpeg 9.0.2's DEFAULT decode, which composes the grid and applies `irot` itself; the fixtures show FFmpeg honours `irot` only; the thumbnail is the second witness. The 16-bit export leg is an EXCLUSIVE window.
  - R1 `d9133089`: (QA) BYTE-level kept EXIF by an independent inventory; (QB) INCONCLUSIVE and continue.
  - R2 `688ef40f`: an independent source ICC; the D63 output structure with the Software count derived.
- **Seat runs done:**
  - R0-O and R0-E (ledger).
  - My extra FFmpeg probes: R0 evidence in `.worktrees/wp3.6p/work/wp3.6p/r0/`.
  - **5a** `photo_check --name wp3.6p-io`: EXIT 0, 309 s, 73/73 read, 0 refused, 0 round-trip problems, GPS and MakerNote kept 73/73. Output `work/wp3.6/photo-check/wp3.6p-io/`.
- **Class map:** `work/wp3.6p/class-map.json`, md5 `07ef683ee2b5a5275a31cdc2597f2fbd`, written by `clearwater-review-evidence\wp3.6p\r0-run\write_class_map.py`.
- **Still to come after convergence:** RUN REQUESTs for 5b (orientation over 62 HEICs), the Q4 `footage` node, 5c-16 (the 73-photo 16-bit export, about 45 min, EXCLUSIVE window, OPEN and CLOSE to CHARC, WP4.6 holds), 5c-8 (seven at 8 bits), and 5d (memory, EXCLUSIVE). Then the report, Reviewer B (the Claude pass at my seat, by hand without the report, as `clearwater-review-evidence\wp-dr87\reviewB\run_review_B.py` does), and the two-leg gate.

**2. WP4.6 (Claude `implementer-opus-high`; brief FINAL; worktree `.worktrees/wp4.6`, branch `wp4.6`).**
- **Where it stands (head `305355a6`, worktree clean, 07:02Z).** Cell 4 finished the R2 remediation under (d) and the spawn rule, then ran **R3 (the LAST full round, per the cap)** before my stop order reached it, and adjudicated it. It was STOOD DOWN for the owner's pause at depth 327,017; it dies with my session.
- **R2 remediation:**
  - `4b54beca` restores F9 and F10.
  - `5b7e04ed` is the RED: 20 failed.
  - `3bc6ffff` is the fix: the stderr tail goes to the log; failure, spawn and scratch texts carry the type name and errno only; the redaction is deleted.
    - Cell 4's own choice: the ENCODE failure follows the same rule. Tell CHARC.
  - R2-1 shared drain, R2-4 no `exc_info`, and R2-5 the clock test, shown by a mutation run.
  - Runs: 66/66 on the parent file three times; the four-file set gave 356 passed.
  - Ledger `cf378034`.
- **R3** (Codex at the cell's seat, `cf378034`, evidence `clearwater-review-evidence\wp4.6\r3\`): VERDICT NEW_CRITICAL_MAJOR_FOUND, with these findings:
  - **R3-1**, MAJOR, in envelope, PROTOCOL class: the I/O threads start before `_converse`'s clean-up `try`, so a failed second thread start leaves the worker running. By the CAP it is fixed RED-first in the terminating clean-up, with no R4.
  - **R3-2**, reviewer-rated MAJOR, housekeeping class, REOPENED from R1 F7: no cancel check while the sweep deletes. Cell 4 keeps it MINOR (R1 adjudicated it MINOR, and `e15d408a` fixed it "as adjudicated"). **Routing call owed:** my recommendation is MINOR, fixed in the clean-up (correct the docstring's "bounded"; add a cancel check between entries). Tell CHARC in the resume post, since the cap sends a non-protocol NEW major to CHARC.
  - **R3-3** (out of envelope, a Limit sentence), **R3-4** (test-only; freeze the clock), **R3-5** (out of envelope; an `OverflowError` in `decode_request` -> a RequestError, exit 2).
- **NEXT (after resume):** a FRESH cell 5 does the TERMINATING CLEAN-UP from the ledger at `305355a6`: R3-1 RED-first, R3-4, R3-5, R3-2 as routed, and the R3-3 Limit; then the targeted runs and the clean-up ledger entry. I verify R3-1's fix at my seat. Its tight reading list:
  - the brief;
  - the four ruling files in `clearwater-review-evidence\wp4.6\` (`r0-ruling-a265489d.md`, `r1-ruling.md`, `r2-ruling.md`, `r2-spawn-ruling.md`);
  - `r3\adjudication.md`;
  - the ledger's R3 section;
  - the code it cites.
  Prompt forms: `clearwater-review-evidence\wp4.6\prompt-wp4.6-cell{1..4}.md`.
- **Then** the V7 WINDOW, the report, Reviewer B and the gate.
- **Rulings, LATEST WINS:**
  - `a265489d` (round 0: STOP-1 granted, an exact test-edit scope plus `tests/export_worker_hold.py` plus the driver copy; STOP-2 no env change; Q2; grants (b) and (c)).
  - `e15d408a` (R1: F8 a DR row plus a Limit; F2, F3 and F6 in envelope; the F1 and F5 forms; F4 a candidate row).
  - `55959e2f` (R2 design change (d): the stderr tail goes to the LOG only; the failure text is a fixed sentence plus the exit status plus at most the exception TYPE NAME; the redaction helper and its tests are DELETED; R2-2 and R2-3 close by removal; F9 and F10 fixes KEPT; F1's form confirmed; CAP: R3 is the LAST full round, a new protocol-class major at R3 is fixed RED-first in the clean-up with no R4, anything else comes to CHARC).
  - `3ed8335f` (the spawn-failure and every parent-side OSError text = type name plus errno plus "details are in the application log", the full text to the log, and a hostile-interpreter-path absence test).
- **Cells:**
  - Cell 1: round 0, retired at 195,061.
  - Cell 2: Y1 and Y2a, retired at 230,050.
  - Cell 3: Y2b and R1, retired at 231,402.
  - Cell 4: R1 remediation, R2, R2 remediation and R3; 199,451 at R2, 327,017 at stand-down.
- **Ledger depth cells owed:** cell 4's "R2 remediation" and "R3" rows. Fill them with 327,017 (one reading at stand-down, 07:02Z), and say so.
- **Seat run:** the four app files whole on `7a20c7bd`, 72 passed in 147.77 s.
- **Driver copy:** `clearwater-review-evidence\wp4.6\windows\s7_driver_wp46.py`, md5 `074cbb62b2a9aa8949ebcf30d803b51a`; the pinned driver is `0b9ee6cc3ebd2cf07c35dec934cfd901`.
- **Still to come:**
  - Convergence.
  - The V7 WINDOW (EXCLUSIVE: modes `v7c` and `v7d` on the pinned driver, `v7e` and `dr44c-export` on the copy; Q7 memory, Q8 spawn cost, the export wall against 209.1-210.9 s, a cache-hit figure, the 10 % STOP; the scratch size for F8; the teardown versus `KILL_AFTER_CANCEL_S`).
  - The report.
  - Reviewer B (Codex at my seat).
  - The gate.
- **For CHARC at the accept:** `_HeldSink` and `_ProgressSink` STAY until the accept; the F4 and F8 rows.

**Kept worktrees:** `wp3.6p`, `wp4.6` (both LIVE); `brief-dr87`, `brief-wp3.6p`, `brief-wp4.4`, `orch-state-g21..g27`.

**Gen-27 practice and slips:**
- **Bare-`cd` slips: three.** Two moved the shared cwd while a WP4.6 cell was live; I warned the cell and restored the cwd. Use `( cd <wt> && ... )` subshells or `git -C`, ALWAYS, including for one-off probes.
- **CRLF:** checkouts here are CRLF (system `core.autocrlf=true`). An Edit of a checked-out file keeps CRLF, and `-c core.autocrlf=false` then commits CR. Commit with the default autocrlf, or `sed -i 's/\r$//'` first, and blob-check before any ff to main. Codex-written files are LF.
- **Crossed messages:** a cell may act on a ruling relayed earlier while a later one is in its inbox. When rulings stack, send one consolidation message naming the precedence (latest wins).
- **CHARC posts can be refused for subject length** (more than 120 characters) while the cue still arrives. If the inbox is empty after a cue, re-list once before asking.
- **The re-seat practice that worked:** a cell at ~200-230K with a multi-finding remediation ahead goes to a fresh cell from its ledger. Send an explicit STAND DOWN first, wait for "stood down", confirm the clean worktree, then dispatch.
- **The seat-run scripts from a cell's ledger needed one fix** (`psutil.disk_usage(str(...))`). Extract the snippets with `sed -n` into the evidence folder and run them from the worktree in a subshell.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). CHARC answers in the operator's stead except the plan section 3 owner-reserved items. Info-updates (`--type fyi`) go to the operator after each accept. No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE.** Nothing from a `gpmd` track, IMU or GPS is ever COMMITTED, and location tags never reach a committed record. The WP3.6P privacy lock is BINDING: format facts only, photo names relative to `Phone/`.
- **Cell depth:** read `uv run python scripts/cell_depth.py <cell>` at dispatch, at every yield and before any ruling. ~250K is an evaluation point; ~400K is a STOP. For Codex: evaluate at ~200K, STOP near 250K, as read from the turn footer `depth_input_tokens`.
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree's working copy. Every edit goes in a worktree on its own branch, then `git merge --ff-only`.
- **Line endings (CHARC, 2026-10-26):** every committed blob is LF. At every gate: for each file in `git diff --name-only <base>..<cand>`, `git cat-file -p <cand>:<f> | tr -cd '\r' | wc -c` must be 0.
- **DR-99** (CHARC `fbbab0bf`): at a gate, `tests/test_io_video_encode_bench.py::test_run_once_records_the_row_and_deletes_the_output` failing on `telemetry_origin` the same way AND alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
