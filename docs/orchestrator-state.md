# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 34** (session `clearwater-orchestrator-20261101-2135`), LIVE since 2026-11-02 07:35Z, picked up gen 33's state at `1972429b`. CHARC is **gen 12 `clearwater-charc-20261101-1330`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Bash gauge at bring-up 65 ms. Seat folder `work/orch-g34/` (gate.sh / watch.sh / fill_gate.py repointed to `orch-g34` and `g34-` basetemps; a successor copies to `work/orch-g35/` and seds `g34`->`g35`).
- **Disk:** C: 101 GB free at 09:54Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free (25 GB before any WP5.3 `clips` piece).
- **Paces at 07:35Z:** Claude 98 % (reset 2026-11-02 10:00Z; the 92 % line is void for the new week until reached again, CHARC `32d39a5c`); Codex 17 % (pace 0.24).
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

**DONE gen 34:** **WP-D112 ACCEPTED, main `92d9ff77`** (record `docs/proofs/wp-d112-accept.md`). Reviewer A round 2 started early on the OWNER's override (verbatim "I am going to override.  Start the 2nd round.") = NO_NEW_CRITICAL_MAJOR, converged; turn 7 adopted advisory 4 as a real-sink row; Reviewer B NO_NEW_CRITICAL_MAJOR (F-B1 MINOR -> new DR row + V4 Codex follow-on, CHARC 08:03:39Z; F-B2..4 banked). Gate d112 on `5080d652`: P 6,509/1 skip + 1 bench flake (6/6 pass alone; CHARC 09:51:52Z = **DR-99 (b)**), S 1,257/11 in 2,760 s, F 7/7 in 2,635 s, harness 382. Codex session 3 retired at 172,713 after turn 7. `.worktrees/wp-d112` released (its `work/` kept until the owner's word).

**1. WP5.3 witness -- RUNNING (started 09:54:02Z from `.worktrees/wp5.3` fast-forwarded to `92d9ff77`):** `clips V-P --manifest work/wp5.3/manifests/vp-witness.json` (the 9 DR-112 items by catalog name, `IMG_67xx.MOV`; the 8 done V-P rows untouched). Receipts `work/orch-g34/wp53-runs/summary.txt` + `clips-V-P.log`. Expect ~25-30 min. THEN: `page`, `page --check`, `tally` (form: `work/orch-g33/wp53-runs/`), then ONE Codex read-back turn in a FRESH session (agent file + brief at HEAD + dispatch) that also adds BOTH slow markers: B-F4 `@pytest.mark.slow(reason="5.6-5.75 s under -n 4 at WP5.3 gate w53 (B-F4)")` on both parametrisations of `test_missing_starter_presets_are_pending_until_both_tables_exist`, and DR-99 (b) on `tests/test_io_video_encode_bench.py::test_a_frames_release_is_not_timed_as_its_write` (reason: median write 0.284 s under -n 4 at gate d112). **CP5 to the owner (decision_request, the V2 review) only at pending 0 AND failed 0.** Orphans `work/orch-g33/vs-orphans/` (~2.0 GB) prune only on the owner's word.

**2. F-B1 follow-on (Codex, small):** teach the V4 instrument (`tools/container_spike/compare.py:1252-1261`) the PCM sample-extent + run-equality reading as a fourth equivalence (WP4.4's three are the pattern), D86 floor on the window's final packet, existing records re-run unchanged, ONE new V4 record on an owner PCM shape as the witness. After the WP5.3 witness; NOT beside WP5.2's EXCLUSIVE windows; before the Phase 5 gate report. Brief to draft.

**3. WP5.2** after the witness (CHARC's brief drafted `35735965`, CHARC finalises after the dispatch fill); EXCLUSIVE windows; carries the 5d estimate figure. Phase 5 gate report notes fullclip 2,635 s vs ~26 min.

**Mail:** inbox drained through 09:55Z (`work/orch-g34/drain-*.txt`; posts `work/orch-g34/*.md`). No query open with CHARC.

**Kept worktrees:** `wp5.3` (LIVE for the witness), `orch-state-g34`; `wp-d112` released; older `brief-*`, `orch-state-g21..g33`, `wp5.1` (released).

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
- **Kernel hazard (7):** never an uncommitted edit in the MAIN tree; edits in a worktree branch, then `git merge --ff-only`.
- **Line endings:** every committed blob LF; 0 CR per file at every gate.
- **DR-99** (CHARC `fbbab0bf`): the bench test's `telemetry_origin` failure alone on main is recorded under DR-99 without a STOP; any OTHER serial failure is a STOP.
