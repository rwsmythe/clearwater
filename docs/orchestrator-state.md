# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 33** (session `clearwater-orchestrator-20261101-1352`) ONLINE 2026-11-01 23:53Z (gen 32 `...-0959` rolled at ~405K). Bash gauge 44 ms. CHARC is **gen 12 `clearwater-charc-20261101-1330`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g33/` (gate.sh / watch.sh / fill_gate.py copied from gen 32; sed the `orch-g32` paths before use).
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

**OWNER PAUSE (owner in chat to gen 33, 2026-11-02 ~00:50Z, verbatim: "once the run is complete, we will pause further execution based on the proximity to the weekly limit.").** After the V-S re-run exits: record its receipt, then START NOTHING (no read-back, no build piece, no reviewer pass, no gate) until the owner says resume. CHARC told (`6ea904cf`).

**DONE gen 32:** WP3.6P ACCEPTED (`f1733802`); WP5.1 ACCEPTED (`0e8f0e00`); both CHARC-confirmed. DR-112 found by WP5.3 and routed; WP-D112 commissioned, briefed (FINAL), RED and GREEN.

**1. WP5.3 `clips V-S` RE-RUN IS RUNNING from gen 33's pane** (started 00:39:09Z, lock pid 13684, `.worktrees/wp5.3` at `0b04e372`; receipts `work/orch-g33/wp53-runs/summary.txt` + `clips-V-S.log`; ~95 min). Gen 32's run died with its pane ~00:36:53Z, recorded nothing (records are written when the group returns); its 20 outputs, the partial, 11 V-S excerpts and `V-S-excerpts.json` were MOVED (not deleted) to `work/orch-g33/vs-orphans/` after a pack.json reference check, stale lock kept there; prune only on the owner's word. Next pieces, one at a time, from the worktree root with the same receipt form: `( cd .worktrees/wp5.3 && unset PYTEST_ADDOPTS; uv run python -m tools.reviewpack.build clips V-D )`, then `clips V-Z`, `clips V-R`, `page` (EXIT 2 while pending or failed), `page --check` (links only), tally (`uv run python -c "import sys; sys.path.insert(0,'tools'); from local_config import load_local_config; from tools.reviewpack.build import main; raise SystemExit(main(['tally',str(load_local_config().working_path/'wp5.3'/'review-sheet.csv')]))"`). After each piece a Codex READ-BACK turn in session 6 (`01a1995b-0d16-75e1-a8fc-45fff4e2eac4`, 81,940 after turn 14; form `wp5.3\cell\dispatch-14.md`; non-slow light run only while a piece runs). Pack state: photos 73 done; V-P 8 done + **9 PRODUCT refusals (DR-112)**; head `0b04e372`. Then the report turn, the two-leg gate (B-F4: time `test_missing_starter_presets_are_pending_until_both_tables_exist` under `-n 4`), the accept (may land with the 9 V-P rows loud; CHARC: AD-13 NOTE). **CP5 to the owner only at pending 0 AND failed 0** = after WP-D112 merges and `clips V-P` re-runs (then `page`, `page --check`, tally).

**2. WP-D112 (Codex; DR-112 fix).** Brief FINAL `docs/briefs/wp-d112-brief.md` (CHARC fold `4bff0b93`) + my turn-2 rulings (both PCM totals: presented = sum of packet durations, stored = payload bytes / (channels x bytes); the four consumer edits; the fixture row is a CONTROL). Worktree `.worktrees/wp-d112`, head **`bd655a07`** (turn 3 `202d1b2e`, session 2 `01a1997a-06d8-7871-8516-d5fb560c7d67` at 136,826: GREEN, 21 RED rows pass; fixture `tests/fixtures/video/pcm-irregular.mov` 219,463 B; real-sink control passes). **The audit STOP is CLEARED** (gen 33, CHARC-concurred `3d187a38`): the three generator-audit rows pass at the seat, 3 passed 22.6 s (`clearwater-review-evidence\wp-d112\audit-d112.log`); sandbox-only; ledger `bd655a07`. NEXT: Reviewer A round 1 (Claude pass, after 10:00Z), adjudication turn, Reviewer B (executing), the THREE-leg gate (the fullclip leg IS triggered: `gx011627` full forms reach the check), the accept (CHARC: DR-112 CLOSED, AD-30 NOTE), then WP5.3's `clips V-P` re-run as the witness. Seat experiment files: `work/orch-g32/pcm/` (the `hook/sitecustomize.py` is seat-only, never committed).

**3. WP5.2** after WP-D112 and WP5.3's accepts (CHARC's brief drafted, `35735965`); carries the 5d estimate figure.

**Mail:** inbox drained 23:33Z (`work/orch-g32/drain-*.txt`; posts `work/orch-g32/*.md`). No query open with CHARC. Last post: WP-D112 RED checkpoint (23:38Z, `d4e2b3da`); then this rollover announcement.

**Kept worktrees:** `wp5.3`, `wp-d112` (LIVE); `wp5.1` (released; junits copied; owner prune); `orch-state-g32`; older `brief-*`, `orch-state-g21..g31`.

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
