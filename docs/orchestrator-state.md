# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 47** (session `clearwater-orchestrator-20261104-1446`), LIVE 2026-11-05 00:46Z, ROLLED at the 400K cap at ~04:20Z on 2026-11-05. The roll was clean: nothing it started is still running (see the board).
- CHARC is **gen 16, `clearwater-charc-20261104-0738`**. Re-verify both names in `comms/.launch-sessions.json` before every cue.
- Seat folder `work/orch-g47/`: `gate.sh`, `watch2.sh`, drains 1-N, the posts, the fill scripts, `crcheck.py` (the CR count of a blob, which replaces the unreliable `grep -c $'\r'` on piped `git cat-file`). Copy `gate.sh` and `watch2.sh` with `sed 's#orch-g47#orch-g48#g'`.
- Bash gauge at bring-up: 37 ms.
- State worktree: `.worktrees/orch-state-g47`. The successor removes it and adds its own.
- **Disk:** C: 71 GB free at 03:27Z. Run `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB is needed before any window or gate.
- **Paces at 03:27Z (2026-11-05):**
  - Codex 6 % / 0.582 (resets 2026-11-11 10:07Z);
  - Claude 52 % / 1.334 (resets 2026-11-09 10:00Z).
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (the text is in `clearwater-review-evidence\wp6.3b\cell\dispatch-1.md`).
  - A cell-written GUI or proof script is reviewed at the seat: grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow.
  - Such a script is RUN AT THE SEAT FROM md5-CHECKED COPIES.
- **No seat or review run executes the DR-125 "before" shape:** a daemon blocked on `sys.stdin.buffer` at interpreter exit, or the OLD worker at `73453bdc`.
- **EVERY CLAUDE REVIEW PROMPT BANS `run_in_background`.** `codex_cell.py review` keeps only the reviewer's LAST message. Check that `review.txt` is a full report before acting.
- **Launch a Codex turn or review ONLY with the Bash tool's `run_in_background`, never a shell `&`.**
- **ROLLOVER TIMING (OWNER-RULED).** Below 400K a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary after 400K with nothing it started still running. At or past the cap, dispatch nothing new.
- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02).**
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time (gate, build, seat run). **Never edit a worktree a gate is running from** (gen 47 held two granted test edits until p64-s ended).
- **TWO CODEX SESSIONS ARE ALLOWED** (CHARC `a6934b58`), on disjoint files.
- **Codex turns:**
  - Run a turn with `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session=<id>] > <dir>\turn-N.driver.stdout 2>&1`, with run_in_background.
  - Commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`.
  - Depth = the footer's `depth_input_tokens`; evaluate at about 200K, STOP near 250K.
  - FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, with `tr -d '\r'`.
  - A RESUMED session's prompt = `dispatch-N.md` alone, with `tr -d '\r'`.
  - Never send the Write of a dispatch and the turn that reads it in ONE parallel batch.
- **Claude cells (Agent tool):** read depth with `uv run --no-sync python scripts/cell_depth.py --live 3 <name>` at dispatch, every yield and before any ruling; about 250K = evaluate, about 400K = STOP. Their reviewer is CODEX. Reviewer A: `cat review-prompt.md review-diff.txt | tr -d '\r' | codex exec -p strong -s read-only --skip-git-repo-check -o review.txt - > review.out 2>&1` from the DETACHED copy (`( cd <copy> && ... )`). Assertions: banner `gpt-6.1-sol` / `high`, `grep -ac '^ERROR'` = 0, `grep -ac '^tokens used'` = 1, the verdict.
- **Claude review of a Codex cell:** `codex_cell.py review --worktree <DETACHED copy> --base <sha> --prompt <p> --out <dir>`, in the background at the seat. Forms: `wp6.3a\B\r1\review-prompt-B.md` (full B), `wp6.3a\B\delta2\review-prompt-delta2.md` (a delta).
- **Gates:** `bash work/<seat>/gate.sh <worktree> <run-id> <legs...>` (background), plus a Monitor on `watch2.sh <run-id> <summary line count>`. Re-arm the Monitor at its 30-minute expiry. gate.sh's static leg runs win32 mypy only: run `uv run mypy --platform darwin` beside it (W-STATIC since WP6.4's accept).
- **Backslash-bearing Python is written with the Write tool**, never a heredoc or `sed -i` (gen 47's `sed` edit of a `\r` assert silently did nothing).
- **A bare `cd` moves the session's cwd.** Use ONLY `( cd X && ... )`, `git -C` and absolute paths. Gen 47 slipped once (`cd .worktrees/wp6.3a && grep ...`), restored in the next call.

### Live board (RESUME HERE)

**Nothing running** at the roll: the last Codex turn (WP6.3b turn 3) returned and was committed; no gate, review, cell or fetch is live (the slow `scripts.d` table script was killed by its timeout; no python left).

1. **WP6.3a: ACCEPTED, main `f1ab5057`** (record `docs/proofs/wp6.3a-accept.md`; CHARC's dispositions at `e2013308`: DR-128 CLOSED, DR-132 / DR-133, AD-33 / AD-34 amended). CHARC shows the owner the N13 text; any change is a docs-only edit.
2. **WP6.4: ACCEPTED, main `f2117494`** (record `docs/proofs/wp6.4-accept.md`). Gate p64's serial leg FAILED on two causes:
   - the P31 semantic merge conflict with 6.3a's Tools actions, reconciled at the seat (`f4ff6c88`, plus `e65ab384` for the COCOA_PROBE filter and the docstring);
   - a transient sticky `CUDA_ERROR_UNKNOWN`, not reproduced in two repros (CHARC: a watch row; a recurrence in any gate = STOP and bisect).

   p64-s serial was green, 1,318 in 2,089 s. CHARC writes the 6.4 dispositions (its accept post is pending or done; check its inbox reply).
3. **WP6.3b (the release workflow, bundled FFmpeg, notices, checklist v2, guide, exception hook): brief FINAL `370d74d0`** (owned additions 1-3 and seat clarifications 1-6 confirmed). Worktree `.worktrees/wp6.3b`, branch `wp6.3b` at `f2117494`, `uv sync --frozen --extra gpu` done (CuPy present). Evidence `clearwater-review-evidence\wp6.3b\` (`cell\`, `A\`, `B\`, `seat\`, `gate\`).
   - **Round 0** (session `01a1a9bf-de4a-78e0-b723-c0c42445f4c5`, 146,885) RULED by CHARC `e209734e` (brief tail "## Round-0 rulings"): STOP 1 one hook site in `export_worker.py`'s `__main__` block; STOP 2 ADV-3 reworded; STOP 3 the guide section-3 launch paragraph; Q1 = BtbN `win64-gpl-9.0` pinned to `autobuild-2026-10-31-12-59` under conditions (a)-(e).
   - **Seat fetches DONE:** `wp6.3b\seat\ffmpeg-fetch.md` (asset `ffmpeg-n9.0.2-39-g7adfbe40dc-win64-gpl-9.0.zip`, sha256 `693f3e22...68b9` = GitHub digest = checksums; gpl + libx265 present, nonfree absent, only `--disable-libfdk-aac`; hevc_nvenc + libx265 listed; archive kept at `work\wp6.3b-seat\ffmpeg\`), `actionlint.md` (`work\tools\actionlint-1.7.12\actionlint.exe`, sha256 matched), `q1-verify.md`.
   - **Turn 2** (resumed `01a1a9bf`, retired at 208,561): ADV-1, ADV-3, D4(d) committed `9a2d9fd3`; seat re-run outside the sandbox green (181 / 113 module-alone / native ADV-3).
   - **Turn 3** (FRESH session `01a1a9de-3cfd-7e43-aaba-f41f398a4bef`, 156,514 at its group-A yield): committed `74ce225c`; group A (hook) built but NOT complete, group B untouched. TWO STOPs posted to CHARC at 04:20Z (MAJOR: the reporter cannot reach AD-25's resolver without importing `clearwater.config` -> NumPy; recommended (c) a stated limitation. MINOR: `test_app_startup.py` `QUIT_SCRIPT` runs the real GUI; recommended a recorded exception). Plus a seat re-run owed: the worker eager-import witness failed only inside the sandbox.
   - **DO NOT run `tests/test_app_startup.py`'s QUIT_SCRIPT test outside a gate leg until CHARC rules STOP 2.**
   - **NEXT:**
     1. Drain CHARC's ruling on turn 3's two STOPs.
     2. Seat re-run of turn 3's set outside the sandbox (EXCEPT the QUIT_SCRIPT test until ruled): `tests/test_exception_hook.py tests/test_frozen_entry.py tests/test_app_export_worker.py tests/test_gui_startup.py tests/test_tools_package_build.py` plus `tests/test_app_startup.py -k 'not <the QUIT_SCRIPT test>'`.
     3. Build the per-component `scripts.d` table for turn 4's lock from the build commit `5031c6f1` in ONE request (the tag's source archive `https://github.com/BtbN/FFmpeg-Builds/archive/5031c6f1082414e53688d39e521849905071070d.zip`, then parse every `scripts.d/**/*.sh` for SCRIPT_REPO / SCRIPT_COMMIT locally); gen 47's one-API-call-per-file script was too slow (600 s timeout). Write it to `wp6.3b\seat\scriptsd-5031c6f1.md`.
     4. Dispatch-4 RESUMES `01a1a9de` (under 200K): finish group A per the ruling, then group B (`--disable-windowed-traceback` + test; the two cache variables beside the three `activate()` sites + tests). FIRM yield points as dispatch-3.
     5. Then turns 4-7 per the round-0 split (FFmpeg lock / notices / smoke + zip / workflow + checklist + guide + report), Reviewer A (Claude, `codex_cell.py review`, detached `.worktrees/wp6.3b-rA`), the seat build proof, Reviewer B, the gate (+ darwin mypy + module-alone install tests), the accept. Then WP6.5's fill (brief DRAFT `fea43245`).
4. **Push:** main is ahead of `origin/main`. CHARC batches the owner's push.
5. **Worktrees:** main; `orch-state-g47` (remove it); `wp-dr125`, `wp6.3a`, `wp6.4` (kept for the prunes); `wp6.1` (KEPT until 6.3b, CHARC); `wp6.2` (released); `wp6.3b` (live).
6. **Prunes owed (the owner's word only; CHARC batches):**
   - `.worktrees/wp6.3a/work/` and the leftover `.worktrees/wp6.3a-rA/work/` (unregistered; long paths: delete with a `\\?\` prefix or `robocopy /MIR` from an empty folder);
   - `.worktrees/wp-dr125/work/wp6.1/` plus `frozen-runs`;
   - `.worktrees/wp6.1` builds and pack after 6.3b;
   - `.worktrees/wp6.2`;
   - `.worktrees/wp6.4/work/` (gen 47's small repro basetemps).

### Gen-47 lessons

- **A package's own gate cannot see a semantic conflict with a package accepted beside it.** WP6.4's P31 pinned the Tools menu, and 6.3a added two actions. Only the second-to-accept package's gate, after merging main, found it. Expect this whenever two packages touch one GUI surface, and **ask the one-hunk reviewer to look for the SAME conflict on the other side** (Codex found the M-side `COCOA_PROBE` twin, which no Windows gate can run).
- **A sticky per-process CUDA fault shows as a burst of `CUDA_ERROR_UNKNOWN` across every later GPU test, then CPU-fallback walls** (a 64 s test took 1,153 s). Before believing a product regression, check:
  - a fresh process's CuPy kernel;
  - the System log for nvlddmkm / TDR;
  - a reproduction of the exact serial slice.
- **pytest's faulthandler "Timeout (0:05:00)!" dump is not a kill.** The real-photo leg always runs about 309 s, so it always dumps.
- **The piped `grep -c $'\r'` on `git cat-file` output gave a false 97.** Use `work/orch-g47/crcheck.py <repo> <rev> <path>`.
- **Long reviewer probe paths can block `git worktree remove`** (`Filename too long`): the worktree is unregistered, but its `work/` stays. List it for the prune.

### Earlier generations' lessons

They are in `git log -p -- docs/orchestrator-state.md` (gen 46's state at `5b6d422f`; gen 45's at `58139313` carries gens 35-45). The ones still binding are in the rules block above.
