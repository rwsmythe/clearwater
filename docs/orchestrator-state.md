# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 46** (session `clearwater-orchestrator-20261104-1246`), LIVE 2026-11-04 22:47Z, ROLLED at the 400K cap at ~00:50Z on 2026-11-05. The roll was clean: nothing it started is still running (see the board).
- CHARC is **gen 16, `clearwater-charc-20261104-0738`**. Re-verify both names in `comms/.launch-sessions.json` before every cue.
- Seat folder `work/orch-g46/`: `gate.sh`, `watch2.sh`, drains 1-7, the posts, the fill scripts. Copy `gate.sh` and `watch2.sh` with `sed 's#orch-g46#orch-g47#g'`.
- Bash gauge at bring-up: 38 ms.
- State worktree: `.worktrees/orch-state-g46`. The successor removes it and adds its own.
- **Disk:** C: 73 GB free at 00:45Z (65 GB at 00:34Z; it dipped from 78 GB during the session; the two seat runs' folders, about 3.4 GB each, and the reviewers' probe folders account for most of it). Run `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB is needed before any window or gate.
- **Paces at 22:47Z (2026-11-04):**
  - Codex 4 % / 0.531 (resets 2026-11-11 10:07Z);
  - Claude 47 % / 1.299 (resets 2026-11-09 10:00Z).

  Re-read them at the first dispatch.
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch. The text is in `clearwater-review-evidence\wp6.4\cell\dispatch-7.md`.
  - A cell-written GUI or proof script is reviewed at the seat: grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow.
  - Such a script is RUN AT THE SEAT FROM md5-CHECKED COPIES.
- **WP-DR125 turn-4 ruling, point 4 (CHARC):** NO seat or review run may execute the DR-125 "before" shape: a daemon blocked on `sys.stdin.buffer` at interpreter exit, or the OLD worker at `73453bdc`. Every review prompt says so.
- **EVERY CLAUDE REVIEW PROMPT BANS `run_in_background`.** `codex_cell.py review` keeps only the reviewer's LAST message. Check that `review.txt` is a full report before acting.
- **Launch a Codex turn or review ONLY with the Bash tool's `run_in_background`, never a shell `&`.**
- **ROLLOVER TIMING (OWNER-RULED).** Below 400K a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary after 400K with nothing it started still running. At or past the cap, dispatch nothing new.
- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02).**
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time (gate, build, seat run).
- **TWO CODEX SESSIONS ARE ALLOWED** (CHARC `a6934b58`), on disjoint files. Gen 46 ran a Codex cell and a Codex reviewer at once without trouble.
- **Codex turns:**
  - Run a turn with `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session=<id>] > <dir>\turn-N.driver.stdout 2>&1`, with run_in_background.
  - Commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`.
  - Depth = the footer's `depth_input_tokens`; evaluate at about 200K, STOP near 250K.
  - FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, with `tr -d '\r'`.
  - A RESUMED session's prompt = `dispatch-N.md` alone, with `tr -d '\r'`.
  - **Never send the Write of a dispatch and the turn that reads it in ONE parallel batch.** Gen 46 did it once and had to `cmp` the prompt afterwards.
- **Claude cells (Agent tool):**
  - Read depth with `uv run --no-sync python scripts/cell_depth.py --live 3 <name>` at dispatch, at every yield and before any ruling.
  - About 250K = evaluate; about 400K = STOP.
  - A Claude cell's reviewer is CODEX:
    - Reviewer A: `cat review-prompt.md review-diff.txt | tr -d '\r' | codex exec -p strong -s read-only --skip-git-repo-check -o review.txt - > review.out 2>&1`, run from the DETACHED copy (`( cd <copy> && ... )`).
    - Reviewer B: the WSL form `clearwater-review-evidence\wp6.4\B\run_review_B.sh probe|review`.
    - Run the assertions: banner `gpt-6.1-sol` / `high`, `grep -ac '^ERROR'` = 0, `grep -ac '^tokens used'` = 1, the verdict, and 0 NUL for B.
- **Claude review of a Codex cell:**
  - Run `codex_cell.py review --worktree <DETACHED copy> --base <sha> --prompt <p> --out <dir>`, in the background at the seat.
  - Forms: `wp6.3a\B\r1\review-prompt-B.md` (full B), `wp6.3a\B\delta2\review-prompt-delta2.md` (a delta).
- **Gates:** `bash work/<seat>/gate.sh <worktree> <run-id> <legs...>` (background), plus a Monitor on `watch2.sh <run-id> <summary line count>`. Re-arm the Monitor at its 30-minute expiry.
- **Backslash-bearing Python is written with the Write tool**, never a heredoc.
- **A bare `cd` moves the session's cwd.** Use ONLY `( cd X && ... )`, `git -C` and absolute paths. Gen 46 slipped once, with a cell live, and restored it in the next call.

### Live board (RESUME HERE)

**Nothing running** at the roll:
- `wp64-cell7` returned; its last reply was at 00:41Z.
- Every review and seat run ended.
- Gate p63a's legs static, collect, parallel and harness ENDED (see item 1).
- No Codex turn is live.

1. **WP6.3a (the GPU pack downloader): PRODUCT FINAL at `eb80136a`; branch `wp6.3a` at `7a82ce11` (main `aaa8fc92` merged, docs only).**
   - **Every net is done:**
     - Reviewer A converged at r3;
     - delta 1 (turns 7-8) and Reviewer B r1 (Claude, full pass) found F1, no fsync before the rename (MAJOR), plus F2 and the advisories, all folded in turns 9-11;
     - delta 2 (turns 10-11): NO_NEW_CRITICAL_MAJOR, with ADV-1..3 recommended to BANK into 6.3b (CHARC has not objected so far).
   - **Seat run of record = the RE-RUN on `eb80136a`**, filled in the report at `fb22270e`:
     - install 123.6 s, network-dominated; the corrected N13 line on stdout;
     - census 2,679 with SET_EQUAL both true;
     - GPU workers;
     - loaded remove pending, then clean;
     - the profile untouched;
     - the known 143 seat-child `.pyc` files.

     Run 1 is kept in `seat\run1\`. The worktree folders `work\wp6.3a\appdata-run1` and `frozen-runs-run1` belong to the owed prune.
   - **Gate p63a on `7a82ce11`:**
     - static: ruff 0, format 327, mypy 0 / 163;
     - collect: 8,590 = 7,285 + 1,298 + 7, identity 0 / 0;
     - parallel: exit 0, 649 s, 7,284 passed / 1 skipped;
     - harness: 423 OK (skipped 1); the gate ended at 00:45:12Z with 73 GB free;
     - **THE SERIAL LEG IS OWED**, not started: gen 46 was past the cap. Run `bash work/orch-g47/gate.sh wp6.3a p63a-s serial` (background, plus watch2) on the SAME head, with no other pytest running. If main has moved, merge it first, re-run harness, and use a new run id.
   - **NEXT:**
     1. Run the serial leg.
     2. Write the accept record `docs/proofs/wp6.3a-accept.md` (form: `docs/proofs/wp-dr125-accept.md`). Cite every net, both seat runs, the gate legs, and the depths: Codex sessions `01a1a842` retired at 229,611 and `01a1a8c0` retired at 226,196.
     3. Note the headless exit 2 on extra args (CHARC's F9 ruling) and the owner's N13 text.
     4. Commit it in the package worktree, then ff main.
     5. Post to CHARC. Its accept adds: DR-128 CLOSED; the AD-33 / AD-34 amendments; the F8 register row with A2's case; showing the owner the N13 text.
     6. Then 6.3b's FILL, with the ADV-1..3 bank and `build.py:645`.
2. **WP6.4 (macOS adaptation): branch `wp6.4` at `740910e4`.**
   - **Turns 4-7 are done:**
     - turn 4 (cell4): S-B1, the M-TOOL fix, P30, the report;
     - turn 5 (cell5): the A r2 fold;
     - turn 6 (cell6): the A r3 test-helper fold;
     - turn 7 (cell7): the Reviewer B fold, head `54456365`, plus the depth fill `740910e4`.
   - Reviewer A has CONVERGED at r3 (`wp6.4\A\r3\review.txt`).
   - Reviewer B (Codex WSL) on `d55573f1` returned NEW_CRITICAL_MAJOR: queue identity, darwin env tests, the bind mount. The rulings are at `aaa8fc92` and turn 7 folded them:
     - B1: `add_paths` re-stats the queued paths;
     - B2: the third edit, which also fixed a FIFTH darwin-failing test, `test_psutil_failures_degrade`; a deviation within the grant, in the ledger;
     - B4: a `lexists` recheck before the fallback rename;
     - B5: an explicit case-insensitive image;
     - B6: the guide notice in section 7;
     - B7: the tests;
     - B3 banked.
   - Static at `61aacbc0`: darwin mypy 0 / 162. Counts: W 168 + 17, M 205 + 19, env 19, batch 47, presets 121, preset panel 46.
   - **The cell's full return was truncated in the notice. Read the ledger's "Reviewer B fold-in (turn 7)" section for the rest.**
   - **NEXT:**
     1. A Codex DELTA review on turns 6 + 7 (`d55573f1..740910e4`, src tests tools docs/user-guide.md), from the detached `.worktrees/wp6.4-rA` moved to `740910e4`. Use the form `wp6.4\A\r3\review-prompt.md` and tell it that item 7, the banked rows and B3 are SETTLED.
     2. Any fold goes to a fresh cell (`wp64-cell8`).
     3. The gate: static (plus `mypy --platform darwin`), collect, parallel, serial, harness.
     4. The accept record, ff, post.
   - **The user-guide merge:** 6.3a's guide edits are in section 2, 6.4's in section 7. **Whichever accepts SECOND merges the guide** (CHARC). 6.3a is likely first.
   - At the accept, CHARC adds: DR-121 / 122 / 124 CLOSED; AD-35..37 BUILT; the register rows (the partial rows; the banked M work; B3 bind mount; the `test_prototype_clip` order dependence); the cell3 incident note (W-GUI with offscreen unset).
3. **WP6.3b:** the brief is DRAFT on main, for your fill after 6.3a's accept. It has CHARC's additions (`--disable-windowed-traceback` plus a product exception hook) and `build.py:645`. ADD the 6.3a ADV-1..3 bank: the post-publication non-OSError reporting, the PowerShell recipe's `install.err` and remove form, and the A5 fallback that has never run.
4. **Push:** main is ahead of `origin/main`. CHARC batches the owner's push.
5. **Worktrees:**
   - main;
   - `orch-state-g46` (remove it);
   - `wp-dr125` (kept for the prune);
   - `wp6.3a` and its copy `wp6.3a-rA` (at `eb80136a`);
   - `wp6.4` and its copy `wp6.4-rA` (at `d55573f1`);
   - `wp6.1` (KEPT; the hand-filled pack serves the census comparison);
   - `wp6.2` (released).
6. **Prunes owed (the owner's word only):**
   - the wp6.1 builds and pack (6.3a's seat runs no longer need them once 6.3a is accepted);
   - `.worktrees/wp6.2`;
   - `.worktrees/wp-dr125/work/` (the onedir build plus `frozen-runs`);
   - after 6.3a's accept, `.worktrees/wp6.3a/work/` (two onedir builds, `appdata-run1`, `frozen-runs-run1`, the run-2 frozen runs; the pack itself was removed by the seat legs);
   - the reviewers' `work/rva*` / `rvb*` / `rvd*` probe folders in the `-rA` copies (they hold copied `python3.dll` / `_queue.pyd`).

### Gen-46 lessons

- **A dispatch's premise about existing call sites can be wrong.** Gen 46 told the 6.3a cell that `__main__` already called `apply_pending_removal` at every start; it called it only when the marker existed. The delta review caught it through an isolated `__main__.main` child. Grep the call site before writing "no edit needed".
- **A seat kit's SOURCE child imports from a pack without `-B`, so it writes `__pycache__` into the pack**, and the full check rightly fails (143 unlisted `.pyc`). The frozen product writes none: the WP6.1 pack holds 0 `.pyc` after many frozen runs, and the PyInstaller bootloader has `write_bytecode` off. A later kit that maps a pack from a source child adds `-B`.
- **A WSL-run Codex Reviewer B is an ASSET for a portability package**: it checked real POSIX `realpath` semantics directly and found the queue-identity regression that two Windows-run A rounds missed.
- **A review prompt's lock can contradict the brief** (WP6.4 B #8: "no real FFmpeg in a W test" vs clarification 6's granted slow trials). Copy each lock from the brief, not from memory.
- **Run Reviewer B in parallel with a tests-only fold cell**, on a detached copy of the code head: it saved about 40 minutes on WP6.4.
- **Cells overran the 250K yield point once** (cell5 at 314K) when told only "at about 250K". Saying "FIRM" in the next dispatch held: cells 6 and 7 stopped at 169K and 184K.
- **A cell's idle-notification return is TRUNCATED** in the notice. The ledger section it wrote is the full record. Do not reply to the cell to get the rest: a reply re-wakes it.
- **Fold a ruled wording change (N13) into a tiny resumed turn**: one turn, 9K tokens of depth.
- **The fsync cost cannot be measured against a network-dominated install** (248 s vs 124 s across the two runs): report it as unmeasurable, not as a speed-up.
- A bare `cd` slipped once, with a cell live (`cd .worktrees/wp6.3a && git status`), and was restored in the next call.

### Earlier generations' lessons

They are in `git log -p -- docs/orchestrator-state.md` (gen 45's state at `58139313` carries gens 35-45). The ones still binding are in the rules block above.
