# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 33** (session `clearwater-orchestrator-20261101-1352`) **ROLLED OVER 2026-11-02 ~07:45Z at ~335K**, at a CLEAN GAP per the owner's no-rollover-while-a-job-runs rule: NOTHING of gen 33's is running (no cell turn, no reviewer pass, no gate leg, no build piece, no Monitor). CHARC is **gen 12 `clearwater-charc-20261101-1330`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Bash gauge at gen 33 bring-up 44 ms. Seat folder `work/orch-g33/` (gate.sh / watch.sh already repointed to `orch-g33` and `g33-` basetemps; copy to `work/orch-g34/` and sed `g33`->`g34`).
- **Disk:** C: 162 GB free at 23:53Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (25 GB before any WP5.3 `clips` piece).
- **Paces at 23:54Z:** Claude **94 %** (pace 1.00; resets 2026-11-02 10:00Z) = over THE LINE; Codex 16 % (pace 0.25).
- **CHARC subjects: under 100 characters** (CHARC `3d187a38`).

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/`)

- **NO ROLLOVER WHILE A JOB RUNS (OWNER, in chat to gen 33, 2026-11-02 ~00:40Z, verbatim: "the generations should not have handed over if the previous generation was still working").** No generation hands over while a build piece, gate leg or live cell it started is still running; roll in the gap between pieces; never start a long piece (a clips piece is ~50-95 min) when the depth leaves no room to see it exit and read it back. Paid for: gen 32 rolled with `clips V-S` as its pane's child; the run died ~00:36:53Z unrecorded.
- **92 % rule (CHARC `e4282d85`):** NO Claude pass STARTS at >= 92 %; after the 10:00Z reset Claude passes resume. Codex turns and WP5.3 run requests continue. NEVER lower the reviewer tier.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** (Codex light suites and Claude passes included); no WP5.3 build piece beside any gate leg or window; one heavy job at a time. Codex light (non-slow) runs beside a build piece are allowed.
- **Gates carry WP-T7's flags** and the STALL WATCH. Scripts (copy to `work/orch-g33/` and sed the paths, as gen 32 did from gen 31): `work/orch-g32/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`; summary `work/orch-g32/gate-<run>/summary.txt`) + Monitor `bash work/orch-g32/watch.sh <run-id>` (30 min cap; re-arm). Junit report fill: `work/orch-g32/fill_gate.py <report> <label> P=<xml> S=<xml> F=<xml>`.
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` (run_in_background); commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`; blob-check 0 CR; `ruff format --check` at the seat. FRESH session prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md` (forms: `clearwater-review-evidence\wp-d112\cell\dispatch-3.md`, `wp5.3\cell\dispatch-14.md`).
- **Reviewer passes (Claude, after 10:00Z):** `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background); prompt forms `clearwater-review-evidence\wp5.3\B\review-prompt-B.md` (B, executing); commands must START with `uv run`, `timeout`, `python`, `.venv/Scripts/python.exe`, `git diff|log|show|status|cat-file|branch`, `grep`, `ls`; give the exact `uv run pytest` line first. Assert: model opus, `is_error` false, verdict line, worktree clean, the light run first.
- **Rulings folded** with `C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\08801258-a62c-4e7b-b28c-70f4138fdb5c\scratchpad\fold_any.py <brief abs> <ruling file in comms/orchestrator/read> "## <heading>"` (pass the `## `), then commit by pathspec in the worktree with `-c core.autocrlf=false`.
- **Worktree release:** a released worktree's `work/` is pruned only on the owner's word; copy its junits to `clearwater-review-evidence\<pkg>\gate\` first.

### Live board (RESUME HERE)

**Owner hold RELEASED** (owner in chat to gen 33, 2026-11-02 ~06:12Z, verbatim: "Hold released, resume all activity"); CHARC: it supersedes the 92 % rule for this window (`1cbf5816`). Claude weekly 97 % at 06:14Z, reset 2026-11-02 10:00Z.

**DONE gen 33:** WP5.3 ACCEPTED, main `91db201b` (accept record `docs/proofs/wp5.3-accept.md`; gate w53 on `b6521664`: P 6,446/1 in 699 s, S alone 1,255/11 in 2,752 s, harness 382; CHARC AD-13 NOTE `da16fc19`). V-S re-run, V-D, V-Z, V-R, page, page --check, tally all ran and were read back (Codex session 6 turns 15-19); report turn 20 (session 7 `01a19ace-0e2d-7fd1-b019-5d505692919b`, 106,986). Pack: 117 done, **9 V-P OPEN (DR-112)**, 2 refused, pending 0. Disk: the 61 GB drop during gate w53 is NOT ours (CHARC closed; Temp unchanged since 10-29; pagefile written during the gate); C: 93 GB free.

**1. WP-D112 (Codex; DR-112 fix) -- TURN 5 DONE, NEXT = REVIEWER A ROUND 2.** Worktree `.worktrees/wp-d112`, head **`78d2a03e`** (turn 5, FRESH session 3 `01a19b24-11a5-7512-b1a1-ade19f406611` at **106,962** after turn 5 (record this depth in the next dispatch); RED 13 failed / 7 passed, then GREEN 20 new rows; light run 64 passed; unit module 126 passed; real-sink integration 3 passed with byte-identical readable PCM; ruff / format / mypy clean; 0 CR in all five files; the `encode.py` change is EXACTLY the granted 6 lines after `check_output` (`source.pcm_dropped_bytes(...)` -> one warning line), verified at the seat). History: Reviewer A round 1 (`clearwater-review-evidence\wp-d112\r1\`, prompt form `review-prompt-r1.md`, base `9d37169b`) = NEW_CRITICAL_MAJOR_FOUND (F1 MAJOR truncated PCM under D86; F2 MINOR no pts after the first; F3 ADVISORY); turn 4 adjudicated (`2e471364`); CHARC ruled `b44b0ee7` (F1 D86-only exception + warning; F2 RUN EQUALITY, the cell's source refusal rejected; F3 banked) and granted ONE bounded `encode.py` edit `81ebcf52`; both folded (`4c5f6b89`, `981724b9`). **NEXT:** Reviewer A ROUND 2: copy `r1\review-prompt-r1.md` to `r2\review-prompt-r2.md`; set head `78d2a03e`; add to "Accepted by ruling": the F1 D86-only exception (`b44b0ee7`, conditions verbatim), run equality in source ticks, the warning line and the bounded `encode.py` grant (`81ebcf52`), F3 banked; make the probe folder `work/wp-d112/rA2-tmp/` in the worktree and point the prompt's EXECUTION paths at it; ask the reviewer to re-probe F1 (the three truncated cuts) and F2 (shift, all-zero, close/open a gap, a gapful source copied faithfully). Run: `uv run python scripts/codex_cell.py review --worktree C:\Users\rwsmy\clearwater\.worktrees\wp-d112 --base 9d37169b --prompt <r2 prompt> --out <r2 dir> > <r2 dir>\review.seat.log 2>&1` (background; NOT beside a serial or fullclip leg). Then the adjudication turn (resume session 3), Reviewer B (executing; form `clearwater-review-evidence\wp5.3\B\review-prompt-B.md`), the THREE-leg gate (`bash work/orch-g34/gate.sh wp-d112 d112 static collect parallel serial fullclip harness` + the watch; fullclip IS triggered; compare skips with w53: parallel 1, serial 11; serial wall vs w53's 2,752 s and WP5.1's 2,039 s, CHARC `d4224524`), rebase onto main with patch-id check, the accept record (form `docs/proofs/wp5.3-accept.md`), ff main; CHARC then: DR-112 CLOSED, AD-30 NOTE incl. the D86 exception, F3 register note. The report turn (`docs/reports/wp-d112-pcm-audio.md`, with the reviewer's side fact as a Limit: a short trailing packet is one trigger of the sink's re-chunking) comes before the gate.

**2. WP5.3 witness (after WP-D112 merges):** rebase `.worktrees/wp5.3` onto main, `clips V-P` re-run from it (receipt form `work/orch-g33/wp53-runs/`; the instrument keeps done rows), then `page`, `page --check`, tally, and ONE Codex read-back turn (fresh session; also the B-F4 marker: `@pytest.mark.slow(reason="5.6-5.75 s under -n 4 at WP5.3 gate w53 (B-F4)")` on both parametrisations of `test_missing_starter_presets_are_pending_until_both_tables_exist`, CHARC `d4224524`). **CP5 to the owner only at pending 0 AND failed 0.** Orphans of the lost V-S attempt: `work/orch-g33/vs-orphans/` (~2.0 GB), prune only on the owner's word.

**3. WP5.2** after WP-D112's accept and the witness (CHARC's brief drafted, `35735965`); EXCLUSIVE windows; carries the 5d estimate figure.

**Mail:** inbox drained through 07:25Z (`work/orch-g33/drain-*.txt`; posts `work/orch-g33/*.md`). No query open with CHARC. Last post: this rollover announcement; gen 33 does not drain after it.

**Kept worktrees:** `wp5.3` (LIVE for the witness), `wp-d112` (LIVE); `orch-state-g33`; older `brief-*`, `orch-state-g21..g32`, `wp5.1` (released).

### Gen-33 lessons

- A generation never rolls over with a job it started still running (owner rule, kernel `215b1fd6`); a clips piece is 1-2.5 h.
- The review-pack instrument writes a group's records only when the whole group returns; a killed group run leaves outputs unrecorded (move orphans aside before a re-run so names stay clean).
- `grep -c $'\r'` inside a `while read` loop over `git show` miscounted (returned line counts); verify CR with Python bytes.count.
- A fresh Codex prompt = agent file + brief at HEAD + dispatch, joined with blank lines; a resumed turn's prompt is the dispatch alone with `--session`.

### Gen-32 lessons

- `page --check` ALONE only checks an existing page; the build is `page`, then `--check`.
- A product's spawned worker can be instrumented at the seat with a `sitecustomize.py` on `PYTHONPATH` gated by an environment variable (the DR-112 experiment); never commit it.
- FFmpeg emulations of the sink did NOT reproduce the product's PCM re-chunking; only the product's own path did. Prove a product behaviour through the product.
- ffprobe PCM: sum(packet duration) = `duration_ts` (presented); sum(size)/bytes = `nb_frames` (stored); they differ at a trimmed last packet.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to charc` (type query, recommended answer first, one cross-session cue after posting). No AskUserQuestion from this seat.
- **GoPro IMU and GPS are OUT OF SCOPE**; nothing from `gpmd`, IMU or GPS is ever committed.
- **Cell depth:** Claude cells via `scripts/cell_depth.py`; ~250K evaluate, ~400K STOP. Codex: footer `depth_input_tokens`; evaluate ~200K, STOP near 250K.
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): the bench test's `telemetry_origin` failure alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
