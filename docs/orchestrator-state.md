# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 34** (session `clearwater-orchestrator-20261101-2135`) **ROLLED OVER 2026-11-02 ~11:05Z at ~413K** (the 400K cap), at a CLEAN GAP: NOTHING of gen 34's is running (no Codex turn, no reviewer pass, no gate leg, no build piece, no Monitor). CHARC is **gen 13 `clearwater-charc-20261102-0046`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g34/` (gate.sh / watch.sh / fill_gate.py on `orch-g34` and `g34-` basetemps; copy to `work/orch-g35/` and sed `g34`->`g35`).
- **Disk:** C: 89 GB free at 11:02Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any WP5.2 window.
- **Paces at 10:12Z:** Codex 17 % (pace 0.238, resets 2026-11-04 10:07Z); Claude 1 % (week reset 10:00Z). The 92 % line is void this week until reached (CHARC `32d39a5c`).
- **CHARC subjects: under 100 characters.** Kernel hazards are numbered (4)-(7) in text order (CHARC `15d1c828`): the uncommitted-edit rule is (6), the one-index rule (7). The rollover sequence is THREE acts (CHARC `d5b76c53`).

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

**DONE gen 34:** WP-D112 ACCEPTED (main `92d9ff77`; DR-112 CLOSED, DR-113 opened, DR-99 (b)). WP5.3 DR-112 witness GREEN (V-P 17 done; page / check / tally; read-back turn 21 + both slow markers, main `69050ead`). **CP5 is WITH THE OWNER** (pack `work\wp5.3\index.html`, sheet `work\wp5.3\review-sheet.csv`, 126 rows; the owner's finding "pairs stack vertically" FIXED at my seat, main `c935b869`, page --check EXIT 0). After the owner fills the sheet (through CHARC): `uv run python -m tools.reviewpack.build tally C:\Users\rwsmy\clearwater\work\wp5.3\review-sheet.csv` from `.worktrees/wp5.3`. CHARC walks the owner through CP5 step by step (step 2 = the P-A photos).

**1. WP-DR113 (Codex; V4 instrument PCM reading; brief FINAL `dc018f25`, CHARC no-tripwire `001d01e4`) -- NEXT = DISPATCH TURN 4 (already written).** Worktree `.worktrees/wp-dr113`, head **`b48c94b3`** (GREEN). Session 1 `01a19bc4-...` retired at 216,276 (turns 1-2); **session 2 `01a19bd8-3481-7ec3-b790-975d7bc645a2` at 111,996** after turn 3. Reviewer A round 1 (`clearwater-review-evidence\wp-dr113\r1\`, prompt form `review-prompt-r1.md`, base `c0bdccba`) = **NO_NEW_CRITICAL_MAJOR, CONVERGED** (2 MINOR, 6 ADVISORY; dispositions in `cell\dispatch-4.md`, posted to CHARC). RUN: `uv run python scripts/codex_cell.py turn --worktree C:\Users\rwsmy\clearwater\.worktrees\wp-dr113 --prompt <E>\dispatch-4.md --evidence <E> --turn 4 --session 01a19bd8-3481-7ec3-b790-975d7bc645a2 > <E>\turn-4.driver.stdout 2>&1` (E = `C:\Users\rwsmy\clearwater-review-evidence\wp-dr113\cell`; run_in_background). Then: the report turn (`docs/reports/wp-dr113-v4-pcm.md`; Limits: F-B2 dropped MD5, ADV 3, 6, 7, the `_facts` disclosure), Reviewer B (form `clearwater-review-evidence\wp-d112\B\review-prompt-B.md`), the THREE-leg gate (`bash work/orch-g35/gate.sh wp-dr113 dr113 static collect parallel serial fullclip harness` + watch; skips vs d112: P 1, S 11), rebase with patch-id, accept record (form `docs/proofs/wp-d112-accept.md`), ff main, then the WITNESS at my seat: `uv run python tools/video_fidelity.py compare C:\Users\rwsmy\clearwater-footage\Phone\IMG_6731.MOV C:\Users\rwsmy\clearwater\work\wp5.3\clips\IMG_6731_corrected.mp4 --out C:\Users\rwsmy\clearwater\work\wp3.10\dr113-green` (the out folder MUST be under `work\wp3.10`); RED of record at `work\wp3.10\dr113-red` = 46 items, MANDATORY DIFFERENT 2 (audio packets [soun#0] first difference at index 94; audio priming/side data at index 95), BEST-EFFORT 9; GREEN expected MANDATORY all SAME with the PCM notes. CHARC then closes DR-113 with that record.

**2. WP5.2 (Codex; brief FINAL `70c3a5db` + round-0 ruling `6e0128fd` + WDDM ruling `eade11c9` folded) -- NEXT = REVIEWER A ROUND 1 on the tool code (before ANY window).** Worktree `.worktrees/wp5.2`, head **`26f02528`**. Session 1 `01a19bc5-...` retired at 169,581 (round 0); **session 2 `01a19bd1-d026-7af0-843a-76486cb6ab96` at 179,121** after turn 3 (EVALUATE: the adjudication may need a fresh session 3). Built: DR-72 exit-3 stop (`tools/export_bench.py`), `tools/device_hold.py`, `tools/photo_memory.py` + the 48 MP PNG16 recipe; tests `test_export_bench_breach.py` (parallel), `test_device_hold.py` (gpu; **PASSES at my seat, 1 passed, on 26f02528**; it stalls in the Codex sandbox, so never ask the cell to run it), `test_photo_memory.py`; light 156 passed. **DR-114 (CHARC, main `44e12a56`): under WDDM each process sees its own cudaMemGetInfo free; an external holder cannot force D111's fallback** (2 GiB probe: holder 7,411,335,168 -> 5,261,754,368 in its own process; a second process 7,411,335,168 unchanged; nvidia-smi 663 -> 2,826 MiB). Reviewer A round 1 prompt to WRITE (form `wp-dr113\r1\review-prompt-r1.md`; base `70c3a5db`; executing the breach test and the photo adapter's light test; the holder test is gpu and runs by node id outside the sandbox). Then adjudication, then the WINDOWS (each named to CHARC first, df >= 25 GB, clocks / temperature / strays, nothing of WP-DR113 running): **W52-1 = R1 alone** (`uv run python tools/export_bench.py v16 --device-frames --subdir wp5.2/v16/W52-1`, ~115 min; rename the record with a `W52-1-` prefix byte-preserving after); **W52-2 = R2 (three whole-GX011627 exports: held ~1.5 GiB device-wide free / free / --force-cpu; --keep these three only; 30-frame comparisons) + R3 (`tools/photo_memory.py` on the 48 MP PNG16; the D111 engagement witness)**; exact commands in the ledger `docs/proofs/wp5.2-ledger.md` `## Session 2 / Turn 3`. Records land in the MAIN tree's `work\wp5.2\` (ruling R0-F2); the cell reads them read-only. Then read-back turns, report, Reviewer B executing, the two-leg gate.

**ORDER (CHARC):** WP-DR113's turns, Reviewer B and gate first; WP5.2's Reviewer A + adjudication may run beside DR-113's Codex turns; NO WP5.2 window while anything of DR-113 runs (gate leg, reviewer pass, test-running turn, V4 witness); no pytest beside a serial or fullclip leg.

**Mail:** inbox drained through 11:00Z (`work/orch-g34/drain-*.txt`; posts `work/orch-g34/*.md`). No query open with CHARC. Last post: the gen-34 rollover announcement; gen 34 does not drain after it.

**Kept worktrees:** `wp-dr113` (LIVE), `wp5.2` (LIVE), `wp5.3` (CP5 tally later), `brief-dr113`, `brief-wp5.2`, `orch-state-g34`; `wp-d112` released (its `work/` kept until the owner's word); older `brief-*`, `orch-state-g21..g33`, `wp5.1` (released). Orphans `work/orch-g33/vs-orphans/` (~2.0 GB) prune only on the owner's word.

### Gen-34 lessons

- `codex_cell.py review` exits 1 when `worktree_clean_after` is false; a concurrent docs-only cell turn in the same worktree causes that without harm (the review diffs committed `base..HEAD`). Commit the cell's docs AFTER the review returns so HEAD does not move under it.
- The review-pack instrument's `--manifest` takes catalog names WITH the extension (`IMG_6729.MOV`); pack.json's `item` field holds them; validate with `PYTHONPATH=tools uv run python -c ... select.catalog()` first.
- A bare `cd` in a Bash call repoints the session's primary working directory; use `git -C` and absolute paths.

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
- **Kernel hazard (6):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): the bench test's `telemetry_origin` failure alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
