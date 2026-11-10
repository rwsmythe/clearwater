# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 66** (session `clearwater-orchestrator-20261110-0123`). LIVE 2026-11-10 11:25Z from gen 65's rollover `6001f924`.
  - Seat folder `work/orch-g66/` (drains, posts, `state-top.md`, `state_update.py`, `ledger_r16.py`). Gen 65's `qa.sh` (writes `work/orch-g65/qa-<label>/`) and window scripts stay in `work/orch-g65/`; gen 64's `gate.sh`, `watch2.sh`, `leg.sh` in `work/orch-g64/`.
  - State worktree `.worktrees/orch-state-g66`. Bash gauge 39 ms.
- **NO Claude cell is live.** `wp65-cell16`, `wp65-cell17`, `wp65-cell18` are DONE: never message any of them (a message re-wakes it).
- **LIVE: WP7.1 Codex turn 16** (turn 7c, the report addendum; RESUMED session `01a1c242-9868-7433-a373-355e1e26af2a`, depth 120,065 at turn 15), launched about 12:25Z from this pane (`clearwater-review-evidence\wp7.1\cell\dispatch-16.md`, driver stdout `turn-16.driver.stdout`). It dies with the pane: do not roll while it runs.
- **CHARC is gen 21, `clearwater-charc-20261108-2037`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.

### PICKUP, in order

1. **WP6.5: READY POSTED** (`dc6fea0d`, 12:13Z): `wp6.5` head **`ae128116`**, range `a93a0ab7..ae128116` (27 commits), nothing under `src/`, `release.yml` unchanged, `MACOS_FFMPEG_BUNDLED: "false"`. Waiting on CHARC's push and the run-4 id.
   - Path there: `wp65-cell18` folded A r14 (M1 `b38e7420`, residual `976f8c26`, M2), A r15's three recorder gaps (`2222a794`); Codex **A r16 converged** (`NO_NEW_CRITICAL_MAJOR`, two recorder-only advisories) and, under CHARC's stop rule `d13c6ce4`, the seat recorded them in the ledger's uncovered list (`ae128116`, which also fills cell18's depths 144,199 / 178,735 / 216,833).
   - Seat QA on `49232840` ALL GREEN (`work/orch-g65/qa-4923/summary.txt`); harness on `ae128116` 423 OK (`work/orch-g66/harness-ae12.txt`). First-head gate on `0a40c058` stands.
   - **Run 4:** watch it (a background `until gh run view`), download read-only into `wp6.5\runner\run-<id>\`, build the runner table, and send the F0-2 round-0 data (`app-listing.txt`, `containment-census.txt`) to CHARC.
   - **At the WP6.5 accept** CHARC opens one DR row for the recorder's uncovered list (`d13c6ce4`).
   - **F0-2's brief must carry:** the f02-sizing (`work/orch-g64/f02-sizing.md`, size M; item 5 done); the CUDA skip for `test_wp321_bench.py::test_a_device_frame_run_gives_the_sink_device_frames`; the Mac native rows from run 4's listing; cell17's note that the notices inventory pointed at a `.app` follows `find_executable`'s `is_file()` and `(home / "_internal").is_dir()` before refusing.
2. **WP7.1 CLOSING SEQUENCE (CHARC `d59a2893`), IN PROGRESS:**
   - (1) **Codex turn 16 (7c) RUNNING**: section 9 of `docs/reports/wp7.1-insta360-exports.md`. Seat-staged inputs in `.worktrees/wp7.1/work/wp7.1/seat-stage/` (`pytest-overlap.log` md5 `592557d1...`, `MD5SUMS` md5 `5b547f9e...`). On return: check the figures, commit by pathspec in the worktree (`codex_cell.py commit` or by hand), count CRs.
   - (2) Claude Reviewer A on the addendum delta (report only; `codex_cell.py review --worktree <detached copy> --base 65c28219 ...`; form `wp6.3a\B\delta2\review-prompt-delta2.md`); B is not re-run.
   - (3) The full TWO-LEG gate + static + harness on the `wp7.1` head (`work/orch-g64/gate.sh wp7.1 <run> collect parallel serial harness`, after `uv sync --frozen`; Monitor on `watch2.sh`). NO cell or Codex turn may test during the serial leg; check run-4 timing (the gate is laptop-local, the runner is not).
   - (4) Merge `wp7.1` to main (rebase or merge as history allows; range-diff record) and post the main head. CHARC then writes the accept.
3. **Worktrees to tidy at the accepts** (owner's word for any prune): `wp7.1-iA`, `wp7.1-instrument`, `wp6.5-rB`, `wp6.5-rA`, plus the old `wp-dr125`, `wp6.1`, `wp6.3a`, `wp6.3b`, `wp6.4`, `wp7.2`, `wp7.2-rB`, `wp7.1-rA`, and the state worktrees `orch-state-g65`, `orch-state-g66`.

### GEN-66 RECORD

- Online `d2113e99`; ack `2d986fcf`.
- `wp65-cell18` (dispatch-19, 19b, 19c): returns 24-26 in `wp6.5\cell\`. A r15 `FINDINGS` (3 MINOR recorder-only); query `e7a234d7` -> CHARC stop rule `d13c6ce4`; A r16 `NO_NEW_CRITICAL_MAJOR`. Ready `dc6fea0d`.
- WP7.1 turn 16 launched.

### Gen-66 lessons

- **Fold a cell's own declared residual before the next review round** (dispatch-19b): it closed in the same cell and saved a round.
- **A test instrument converges asymptotically:** after the product was clean, each review found a new recorder false-negative class (r13-r15). Ask the director for a stop rule (instrument-only findings become ledger advisories) as soon as the trend shows; CHARC accepted it at once.
- **A cell's return can arrive in chat while its transcript's last text is mid-turn:** save the chat return to the evidence folder, not the transcript's last text.

### GEN-65 RECORD

- **Online:** post `27ee1878`; CHARC ack `d9f82775`.
- **WP7.1 instrument:** A r4 (Claude) clean with zero findings; `wp7.1` ff to `65c28219`; post `19308fc6`. Look exhibits kept (`a4cd23fe`).
- **WP6.5 run 3** (`42781244075`): parallel clean; serial 15 failures (FFmpeg 5, GPU-pack 8, cache 2); the `.app` link rule; T14. Runner table built.
- **Run-3 group:** `wp65-cell16` (dispatch-17) returned `0a40c058`. Its S2 dispute was RIGHT; my run-3 premise was false (a grep for `sys.platform` missed the `pack_root()` gate). The DR row and the XS package were DROPPED.
- **Codex A r11:** FINDINGS, 1 MAJOR + 3 MINOR, all upheld; fold cell17 dispatched.
- **Window 3:**
  - the first launch refused `--timeout-s 3600` against the 7,408 s V4 bound (a staging defect; relaunched as `export-hevc62r2`);
  - the hold message to cell16 never reached it (QUEUED mid-turn), so the cell's pytest overlapped the export leg.

### Gen-65 lessons

- **An exclusive window is gated on the cell having YIELDED, never on a hold message or on "no pytest at launch".** A message to a mid-turn Agent-tool cell is queued and NOT delivered until its turn ends; it then re-wakes the cell after its return. This is the second occurrence after gen 61. Dispatch an exclusive window only with no cell live, or launch the cell after the window.
- **Read the product's gate before asserting a product defect:** "nothing checks the platform" came from a `sys.platform` grep. The real gate was `pack_root()`. Read the call path from the entry (menu action -> handler -> dialog -> plan) before posting a premise CHARC will rule on.
- **A staged seat script must be dry-checked against the driver's own argument checks** (`run_export.py:51` `v4_bound`) before a window. Gen 64 staged `--timeout-s 3600` for a leg whose inline V4 needs more than 7,408 s.
- **The heredoc backslash collapse struck again** (`\r` in a state-top path became CR); repaired with a Write-tool script. **The bare-`cd` slip struck twice** (into the look folder; into the wp7.1 worktree while cell16 was live); each was restored in the next call, and nothing was written while moved.

### GEN-64 RECORD

- **WP6.5:**
  - CHARC ruled the `69538abe` gate STANDS with DR-96. The owner said "push"; CHARC pushed and **run 2** (`42764505729`) ran: parallel 4 failed / 7762 passed / 1227 skipped (run 1: 63). The four: C2 (HEIC max 2-3 / p99 1), C16 (FFT max 1.79e-7, inside 1e-5), the NEW beat-file test, the NEW darwin containment EPERM. Serial and bundle steps were skipped.
  - CHARC ruled each item. `wp65-cell15` (dispatch-16) fixed all six (`2e98ca1c`).
  - **A r8 MAJOR:** CHARC's switch-keyed continuation skipped the bundle tests in RELEASE mode (`macos.log` missing). Re-ruled MODE-keyed (`success() || (!cancelled() && !inputs.release-version)`) with a four-case EVALUATED guard. Fold `eeefd4cf`.
  - **A r9 MINOR:** evaluator precedence; fold `a93a0ab7`. **A r10: zero findings.**
  - **Gate on `2e98ca1c`** from the detached `wp6.5-rB`: identity 10,574; parallel 9,020 / 210 / 0; serial 1,318 / 19 / 0. On `a93a0ab7`: release_workflow 122, harness 423 OK, actionlint clean, statics clean.
- **WP7.1:**
  - Plan R (V4-only on the retained outputs) was REFUSED: `frame_end` is called by `encode.py:1312`, so WP7.2 changed the EXPORT path.
  - The owner's "reading" became the instrument sub-package above.
- **Slips:**
  - one bare `cd` into `wp7.1-instrument` (restored the next call; nothing written; no live cell affected);
  - a seat QA basetemp without its parent (45 errors, re-run green);
  - my restated probe swapped the media and movie timescales (the Codex cell STOPPED correctly at I2).

### Gen-64 lessons

- **Read a diff by CALLER, not by file:** `verify.py` hosts both instrument helpers and the encoder's end-of-stream arithmetic (`frame_end`). "Only verify.py changed" did not mean "only the instrument changed". Grep the callers of every changed function before claiming a change's reach.
- **A ruling's WORDING can name the wrong axis** (the bundling switch instead of the run MODE); the reviewer caught it as a release-mode regression. When a ruling conditions on a flag, ask which axis the distinction really is, and check both modes of a workflow before relaying.
- **A gate leg must not run from a worktree a cell is editing:** run it from a detached copy at the gate sha (`wp6.5-rB`, with toml + `uv sync --frozen`). Then the cell folds in parallel, and the fold head re-runs only the touched ids (CHARC plan 2).
- **Do not run a Qt / GUI test module under xdist `-n`** at the seat: a 5-min timeout left a hung worker tree (`taskkill /T` on the pytest root).
- **The `codex_cell.py commit` parser refuses returns** whose block sits after prose in the same line run; commit by pathspec in the worktree, and count CRs per blob. The CRLF-checkout trap struck once more (I1: 1,600 CRs; amended before use).
- **When restating a reviewer's probe, copy its facts exactly** or point at the file: "timescale 30000" lost its "media" and cost a Codex turn.
- **A Claude review's `review.json` keeps only the final message:** its probe code is gone. Ask reviewers to inline the probe's inputs in the finding.

### Gen-63 lessons

- **An autouse fixture that requests `monkeypatch` reorders every test's teardown,** even when its body is a no-op on that platform: the requested fixture is set up earlier, so finalizers registered later run BEFORE the monkeypatch undo. An order-dependent defect like this hides from module runs and shows in the xdist leg. `-p <module>` preloads a module as a plugin, making such a failure deterministic.
- **Read the follow-up drivers' input gates before a FAIL verdict reaches them:** both `load_export` and `project_long` refused a V4-FAIL record. The pickup rule ("STOP if they refuse") caught it before any blind run.
- **A review transcript can contain OTHER sessions' transcripts** (B printed A's review files with `cat`): count `^session id:` headers before reading the "tokens used" count.
- **A cell's round 0 can show that a fix clears fewer rows than the brief's Done line assumed** (the source file's own movie-level roundings): the brief's STOP clause did its job. Amend the Done line by ruling, never silently.

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (current text: `clearwater-review-evidence\wp6.5\cell\dispatch-3.md`, with the QUIT_SCRIPT exception and the Mac HOME reading).
  - A cell-written GUI or proof script is reviewed at the seat: grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow.
  - Such a script is RUN AT THE SEAT FROM md5-CHECKED COPIES (WP7.1: `clearwater-review-evidence\wp7.1\seat\frozen-t6\MD5SUMS`; `md5sum -c` from the driver folder before each run).
- **No seat or review run executes the DR-125 "before" shape.**
- **EVERY CLAUDE REVIEW PROMPT BANS `run_in_background`** (and every Codex review prompt now says "no background execution; whole report in the FINAL message"). Check that `review.txt` is a full report before acting. Four "ERROR: Reconnecting... n/5" lines in `review.out` with one `tokens used` and a full report are a network blip, not a failed review.
- **Launch a Codex turn or review ONLY with the Bash tool's `run_in_background`, never a shell `&`.**
- **ROLLOVER TIMING (OWNER-RULED).** Below 400K a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary after 400K with nothing it started still running (a live Agent-tool cell dies with the pane: wait for its return). At or past the cap, dispatch nothing new.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time. **Never edit a worktree a gate is running from.** WP7.1's EXCLUSIVE legs (C/D/E) run only when no WP6.5 cell is running tests (CHARC).
- **TWO CODEX SESSIONS ARE ALLOWED** (CHARC `a6934b58`), on disjoint files.
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session=<id>] > <dir>\turn-N.driver.stdout 2>&1` with run_in_background; commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>` (it refuses a return without a parseable block: then `git -C <wt> add <file>` + commit by pathspec in the worktree). Depth = the footer's `depth_input_tokens`; evaluate ~200K, STOP ~250K; a resumed turn adds 30-40K: resume only below ~160K. FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + every prior return and dispatch (2..N) + `dispatch-N.md`, joined, `tr -d '\r'`; RESUMED = `dispatch-N.md` alone. Never Write a dispatch and launch the turn that reads it in ONE batch. The first (non-resumed) turn needs an ABSOLUTE `--worktree`.
- **Claude cells (Agent tool):** depth with `uv run --no-sync python scripts/cell_depth.py --live 3 <name>` at dispatch, every yield, before any ruling; ~250K evaluate, ~400K STOP; build dispatches name a mid-turn yield at ~300K. A SendMessage to a cell that has already yielded RE-WAKES it (it re-sends its return): read depth first; if it has returned, do not message it. Their reviewer is CODEX: `cat review-prompt.md review-diff.txt | tr -d '\r' | codex exec -p strong -s read-only --skip-git-repo-check -o review.txt - > review.out 2>&1` from the DETACHED copy (`( cd <copy> && ... )`); assert banner `gpt-6.1-sol` / `high`, `grep -ac '^tokens used'` = 1, the verdict.
- **Claude review of a Codex cell:** `codex_cell.py review --worktree <DETACHED copy> --base <sha> --prompt <p> --out <dir>`, background, at the seat (forms `wp6.3a\B\r1\review-prompt-B.md`, `wp6.3a\B\delta2\review-prompt-delta2.md`).
- **A gate runs from a DETACHED copy at the gate sha when a cell may edit the package worktree** (gen 64; `wp6.5-rB`). Never run a Qt / GUI module under `-n` at the seat.
- **Gates:** `bash work/<seat>/gate.sh <worktree> <run-id> <legs...>` (background) + a Monitor on `watch2.sh <run-id> <summary line count>`, re-armed at 30 min; run `uv run mypy --platform darwin` beside the static leg. Copy the toml and `uv sync --frozen` in a new worktree first.
- **Backslash-bearing Python goes through the Write tool**, never a heredoc (it struck AGAIN in gen 60: `wp6.5\\A\\r1` in a heredoc became `\A` + CR; fixed forward `41ef6dd5`).
- **A bare `cd` moves the session's cwd.** ONLY `( cd X && ... )`, `git -C`, absolute paths. (Gen 60 slipped three times; each restored next call.)
- **role_mail subjects are capped at 120 chars** and a refused post writes nothing: read the `posted ->` line before cueing.
- **QUIT_SCRIPT exception:** `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` runs at the SEAT in gate legs only; every cell run (and the macOS job, F0-11) keeps `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
- **Running downloaded build scripts / binaries is refused** at this seat; read them as text (the seat's pinned actionlint 1.7.12 is the one standing tool).
- **CI-SHAPED REHEARSAL BEFORE EVERY TAG** (`work/orch-g58/rehearsal.py --runner-path`); **THE RELEASE SWEEP** before any Codex read of a bump; **RELEASE NOTES STATE BEHAVIOUR BY SHAPE** (DR-159 carries them into checklist v3).
- **A NEW WORKTREE'S `.venv` IS AN EMPTY SHELL** (`uv sync --frozen` first).
- **CLAUDE.md is CHARC's**; the orchestrator never appends to it.
- **Claude lane:** the ~95 % hold ended at the 2026-11-09 10:00Z weekly reset; read `scripts/usage_claude.py` before each Claude dispatch and report the share.

### Gen-61 lessons

- **A cell's return can arrive HOURS late, or never, as a chat message**: cell7 returned at 12:10Z and the seat sat idle until ~16:53Z; cell5's and cell8's chat returns were truncated. When a cell's depth is static and its commits have landed, read its LAST assistant text from `~/.claude/projects/C--Users-rwsmy-clearwater/<session>/subagents/agent-a<name>-*.jsonl` (python, last `assistant` text) and save it to the evidence folder.
- **A queued SendMessage re-wakes a cell after its return**: the CHARC addendum relayed to cell6 made it fold a SECOND time after its return (a new commit, a new helper sha) while the seat was preparing the delta read on the first. Before using a return's shas, re-read `git log` and the helper clone's reflog.
- **A cell asked to "hold tests" may not honour it within the leg**: cell8 kept working and ran its suites after leg 1 ended; nothing overlapped by luck. For an exclusive leg, gate on the cell having YIELDED (depth static across a turn boundary), not on a message.
- **GitHub can refuse a dispatch on a fork with "Actions has been disabled" (422) while `actions/permissions` says enabled**: the fork's web-only "enable workflows" state; and a macOS arm64 job can sit unacquired and be cancelled ("not acquired by Runner of type hosted") under capacity constraints. Neither spends the owner's dispatch; record both, ask CHARC before a re-run.
- **Conservative refusal beats emulation in a validator** (two Codex rounds on shell-pattern and byte-scan emulation; the third fold refused the hard classes outright and converged in one pass).
- **The heredoc backslash collapse struck twice more** (a `sed` replacement in a review prompt and a Python heredoc building this state block: `\r` -> CR, `\f` -> FF); repaired with Write-tool scripts. **The bare-`cd` slip struck twice** (into the transcripts folder; into a cell's scratch folder while the cell was live); each restored in the next call, nothing written while moved.

### Gen-60 lessons

- **A cell-written driver's acceptance check can be wrong about a product field's vocabulary:** run A's export succeeded and its driver failed on `device.startswith("cuda:")` (the product's field is the backend REASON, `"GPU"`). Before a long seat run, grep the product for every value a driver asserts on.
- **A driver's hard-coded sub-timeout is a second bound:** V4's `timeout=900` inside an 1,800 s outer bound killed A2. Read every `timeout=` in a seat driver, not only the CLI bound, and size each from the measured rate.
- **A round-0 premise of the brief can be false** (ProRes "admitted on paper"): the Codex cell's round 0 caught it with file:line; verify at the seat and route to CHARC before any build turn.
- **A SendMessage to a cell after it yielded re-wakes it** (wp65-cell2 re-sent its return twice). Read depth twice; if the return has landed, do not message.
- **Fold Reviewer A's findings into the NEXT group's fresh cell** (A r1's three findings rode into G2b's turn): one cell, one review round.
- **The bare-`cd` slip recurred three times in gen 60; the heredoc backslash collapse once; one refused over-length subject.**

### Gen-59 lessons

- **A ruling's wording can itself be false:** CHARC's A1 phrase went into a fix commit and the next read found it false. Verify supplied wording against the code BEFORE committing it.
- **A clause list in release notes is a magnet for findings:** three successive reads each found one false clause in one sentence. Propose the shape-only form as soon as a second round finds a clause.
- **Main moves under a release branch** (CHARC's state commits): rebase onto main, record `git range-diff` (all "=") and the tree diff, then ff.
- **Read the workflow's gate before planning a run on it:** WP6.5's stage-1 plan assumed a branch dispatch of `release.yml`; its version gate refuses any non-tag ref. Caught at the fill, ruled as Q5.
- **The runner's skip set can differ from the CI-shaped rehearsal's** by host facts the rehearsal cannot mimic (8.3 short names, the `C$` admin share): diff SKIPPED reasons, never assume (7515 / 1062 vs 7517 / 1060).
- **A harness run's tail can print "acked 1 message(s); moved inbox -> read."** It is fixture output; check the real inbox listing.
- **The heredoc backslash collapse struck again** (prune2's KEEP block). The Write tool is the only safe route for any Python with a Windows path.
- **The bare-`cd` slip recurred twice in gen 59** (`cd .worktrees/... &&` at the start of a command). Each was restored in the next call.

### Gen-58 lessons

- **A seat instrument goes INTO the environment under test, never around it.** The spy plugin, copied into the clone venv's site-packages and removed after (no PYTHONPATH), gave a leg identical in shape to the plain one: `7519 / 1058`, then `7517 / 1060`. Check that equality before reading the spy's list.
- **"Passes for the wrong reason" has one shape here:** a REAL tool call runs BEFORE the injected fault, fails when the tool is absent, and lands on the status the test expects. A guard is needed exactly when the asserts accept that status. Read the call order (file:line) for every spawning parameter, and guard per parameter.
- **A cell's collection run can fail on its OWN tooling.** The Codex turn-5 GUI-import block gave 27 collection errors and footer ERROR lines; its corrected runner collected 8,577. Read the transcript before treating footer ERROR lines as package failures.
- **`codex_cell.py commit` can refuse a well-formed return block** (`files_changed: []`). Commit by pathspec inside the worktree, with your own message.
- **Placeholders multiply:** the report had FOUR "(the seat fills)" lines, not the two the ruling named. `grep -n "seat fills"` before a seat fact commit.
- **A laptop floor and a CI-shaped floor differ by the toml-absent skips.** Here `8370 / 207` vs `8367 / 210`. Diff the `SKIPPED` reason lines to prove it; never assume.
- **A serial-leg flake gets: re-run alone 3x, the junit history (`g43-*-serial.xml` across worktrees), the package's footprint, then a CHARC ruling** (here DR-158 WATCH).
- **The heredoc collapse struck again:** a `\\n` inside a quoted heredoc Python literal became `\n`, so the assert missed. Any Python with a backslash goes through the Write tool.
- **The bare-`cd` slip recurred FOUR times in gen 58** (`cd <dir> && ...`; once a `cd <worktree> 2>/dev/null;` meant only to grep). Each was restored in the next call; nothing was written while the session was moved. Use `( cd X && ... )`, `git -C`, absolute paths, or the Grep / Read tools. Never type `cd` at the start of a Bash command other than the repo root.
- **A Codex read flags KEPT history strings as CRITICAL** when the prompt says "a wrong version string shipped is CRITICAL": `notices.py:2191` was ruled KEEP an hour earlier, and the read still made it F1. Sweep for version-bearing prose that RENDERS INTO THE ARTIFACT, not only for version pins, and settle it before the read.

### Gen-57 lessons

- **A release workflow that has never run on a runner fails on the runner's facts, not the laptop's.** v1.1.0's run died 3 s into the tests on `--basetemp=work/ci-parallel` (`work/` is gitignored; pytest does not create the parent). Then the seat's CI-shaped rehearsal found the toml class (12), and Reviewer A found the bigger one: the runner image has NO FFmpeg, and the rehearsal had inherited the laptop's PATH (152 more tests in 15 modules). A rehearsal is only CI-shaped when its PATH and GPU are too: drop every PATH entry holding ffmpeg / ffprobe and set `CUDA_VISIBLE_DEVICES=-1` (`work/orch-g57/rehearsal.py --runner-path`). Check the runner image's software list (`actions/runner-images` `images/windows/<image>-Readme.md`; the image name is in the run log's "Runner Image" group).
- **A causal split settles "what caused these N failures" in one minute:** re-run ONLY the failed node ids under each candidate cause alone (`work/orch-g57/cause_split.py`). Here: FFmpeg dropped -> the same 152; GPU hidden -> 152 pass.
- **A step timeout in a seat driver kills only the wrapper:** the 30-min sync limit killed PowerShell and left `uv sync` running as an orphan that finished the install. Size step limits for this laptop's link (the CUDA wheels took ~17 min), and look for orphans (`Get-CimInstance Win32_Process`) before re-running.
- **A no-log-growth stall alarm is wrong for `uv sync`** (it prints nothing while downloading). Read the process's write-transfer counter instead.
- **Builds are not byte-reproducible across trees** (zip `d233d8c0...` vs `2529b42f...` for the same commit; notices byte-identical). Compare member sets.
- **The bare-`cd` slip recurred twice in gen 57** (once `cd <state worktree> 2>/dev/null;` moved the session cwd into the worktree; once inside a background command, which did not move it). Only `( cd X && ... )`, `git -C` and absolute paths.

- **A seat instrument must not change the environment the tests check.** The spy run set `PYTHONPATH` to load its plugin, and `build.py` refuses a set PYTHONPATH: 253 failures that were the instrument's, not the package's. Install a seat plugin into the clone's venv instead, and compare the instrumented leg's summary with the plain leg's before reading anything from it.

### Gen-56 lessons

- **A harness gate run before `git add` cannot see a new file**: CHARC's notes file `docs/release-notes-1.1.0.md` reached main unregistered and failed the harness's tracked-files test on main for hours; seat QA on a package head found it. Register a new root/docs file in the same commit, and run the harness AFTER staging.
- **Release-notes claims need a reviewer claim table every round**: r4 found a sixth false claim ("licence and source" for every component, while the MSVC runtime carries terms only) after three rounds; the linked user guide also carried prerelease text ("not released yet") and a stale size. Ask the reviewer to grep the linked docs too.
- **Fold advisories from two nets in ONE turn** (CHARC ruled): running B on the same head as A's converged delta, then folding A r2 + B r1 together, saved a full turn + review round.
- **A seat-verifiable census can be staged into the Codex worktree's gitignored `work/`** (byte-compared file by file) when the sandbox cannot read the evidence folder; the cell then copies by a script verified against the census index, and the seat re-checks from the COMMITTED BLOBS (`qa_texts.py`).
- **The heredoc backslash collapse struck again** (`work\release-proof-gpu\roots` in a heredoc Python literal became CR bytes in the build record); caught by the edit notice and repaired with a Write-tool script. Any Windows path in Python goes through the Write tool or `chr(92)`.
- **The bare-`cd` slip recurred three times in gen 56** (`cd <worktree> && ...`, each restored in the next call; nothing written while moved).

### Gen-55 lessons

- **A version bump's own checks must include EVERY test that pins the app version**, not only the version test and the package modules: `tests/test_gpu_pack_install.py:340` pinned the User-Agent `Clearwater/1.0.0` and would have failed the tag build's parallel leg. Codex's read caught it. For any bump: `git grep -nE '"1\.0\.0"|/1\.0\.0'` over `tests src tools` (minus `native-licences`), and run `test_gpu_pack_install.py` alone.
- **Release notes need a claim-by-claim read against the code.** Three Codex rounds found five false or overstated claims in the notes (auto-restart, a menu ellipsis, start-up hashing, "every tool pinned", "with the licence texts"). The last one exposed a real N13 gap (FFmpeg's ~100 build-stage components carried no texts) and became WP6.3d. Ask the reviewer for a per-claim file:line table.
- **A licence census's real yield can be the record SET, not the texts**: pass 1 found shaderc's `git-sync-deps` sub-dependencies (glslang, SPIRV-Tools, SPIRV-Headers) statically linked with no lock rows at all. Brief every census to follow each stage's own fetch steps (DEPS, submodules, cargo, sync scripts).
- **A gate of record must not overlap a build**: an 11 s pytest ran while the release build was finishing (harmless, but against "one heavy job at a time"). Wait for the build's exit line.
- **The bare-`cd` slip recurred twice in gen 55** (each restored in the next call; nothing written while the session was moved).
- **A quoted heredoc turned `seat\\r2-codex-read\\review.txt` in a Python literal into two CRs** (the known collapse; the 2 CRs were caught by a CR count printed by the same script). And `Path.read_text` then turned the CRs into newlines, so the repair anchor had to be the newline form. Write ANY backslash-bearing script with the Write tool; build Windows paths with `chr(92)`.
- **The bare-`cd` slip recurred once in gen 55** (`cd <worktree> && ...` to read the brief; restored in the next call, nothing written). Only `( cd X && ... )`, `git -C` and absolute paths.
- **A worktree "release" is a prune** when it holds ignored `work/` content: hold it for the owner's word (CHARC concurred).

### Gen-54 lessons

- **A heredoc collapsed the backslashes in a Python string literal holding a Windows path** (`'C:\Users\...'` -> a `\U` escape SyntaxError): the dispatch-17 head fix failed, and because the Write of the fix and the turn launch went out in ONE parallel batch, turn 17 launched with a stale pointer (killed seconds in, relaunched; `cell\turn-17-aborted.*`). Fix dispatch text with the Write tool, and never launch a turn in the same batch as the edit it depends on.
- **`codex_cell.py commit` refuses a FILES CHANGED line that is not a literal path** (t15 wrote "folder/ -- 157 new texts;"; nothing was committed). Dispatches now say "one literal repository-relative path per line, nothing else". When it refuses, commit by pathspec inside the worktree (its own index).
- **A census subagent can finish before a mid-run addendum lands, then pick it up as a SECOND pass** (its first return lacked the `basis` field; the queued message re-woke it). Check every binding against the returned files, not the report's prose.
- **A cell that appends to a report with PowerShell `Add-Content` leaves a few CRLFs in an otherwise-LF file**: anchors built for one line-ending style miss. Inspect the tail bytes before a scripted edit; git normalises on commit (blob CR 0).
- **Ask whether a review finding needs a NEW field before ruling "key it on the existing one"**: B r2 adv 5 wanted the sentence "basis-dependent", but `basis: lock-graph` covered 11 linked std crates; t17 added `linkage`.
- **The bare-`cd` slip recurred three times in gen 54** (each restored in the next call or the same one). Only `( cd X && ... )`, `git -C` and absolute paths.

### Gen-53 lessons

- **Pinning a release TAG can fail against a build system's floating dependency pins.** BtbN's scripts track dependency HEADs, and FFmpeg's `n9.0.2` predates a fix those pins need. Pin the maintained branch at a full 40-hex commit (`git checkout --detach` after the clone), never a short sha or a tag, and check the binary's `-g` hash (F3b).
- **Check the reviewer MODEL in the brief's Lane row before naming it.** Gen 53 told CHARC "B (Codex)" three times for a Codex-lane package whose nets are both Claude. A seat-made artifact in a Codex-lane package then has NO cross-model reader unless one is added (CHARC ruled a read-only Codex read).
- **A substring licence check misfires on `--disable-*` flags** (`libfdk-aac` matched `--disable-libfdk-aac`). Test the ENABLE flag.
- **`grep -c $'\r'` inside a `for` loop in `$( )` counted lines and reported phantom CRs**, and once broke quoting. Count CR bytes with `work/orch-g53/crcheck.py`.
- **The bare-`cd` slip recurred four times in gen 53** (each restored in the next call, none during a write). Only `( cd X && ... )`, `git -C` and absolute paths; never `cd X 2>/dev/null;` "just to read".
- **A cell-written proof driver is cheap and safe when the seat freezes a copy and reads all of it before running** (export_proof: 1,006 lines; isolation before any product import; PATH limited to the bundle).

### Gen-52 lessons

- **The auto-mode classifier refuses outward and destructive acts even with the owner's recorded authorisation** ("Create Public Surface" on `gh repo fork`; "Irreversible Local Destruction" on the prune script). Do not work around it: write the exact commands / script, record them in the evidence folder, and ask the owner to type them with `!` in this pane (output lands in the session for the record). Tell CHARC in the same breath.
- **Pin a seat record's hash in a dispatch only after its producing subagent has RETURNED** (CHARC rule). t9's first launch was killed a minute in because the fetch subagent re-hashed the record after the dispatch pinned it; an addendum sent mid-run crossed with its reply.
- **An `ff-only` merge into the state worktree checks files out CRLF** (system `autocrlf=true`); a following `git -c core.autocrlf=false commit -- <file>` commits the CRLF working copy even when the edit itself was refused (`037a2e1f`, 151 CRs, fixed forward in `cd4cbef0`). Before committing a docs file from a worktree, WRITE its full LF bytes with Python (`git show <rev>:<path>` as the base) and check the blob's CR count after the commit; never let a chained commit run after a failed edit (use `&&` only after a step that exits non-zero on failure, and check the script's exit).
- **`codex_cell.py review` excludes only `docs/proofs` and `uv.lock`;** a package with a large data surface needs `work/orch-g52/review63c.py` (adds excludes) or the reviewer drowns in the manifest.
- **The bare-`cd` slip recurred twice in gen 52** (each restored in the next call). Only `( cd X && ... )`, `git -C` and absolute paths.
- **A cell dispatched before a ruling lands misses the ruling's additions** (t11 lacked CHARC's literal content-hashed test): check every ruling against the next return and fold the gap into a small fresh turn.

### Gen-51 lessons

- **A new tracked file outside the instance prefixes fails ONLY the harness leg** (`.github/workflows/release.yml` at p63b2, after 40 minutes of green pytest legs). Run the harness on the package head before Reviewer B. WP6.3c's fill (seat clarification 7) binds it.
- **A Codex worktree's helper clone must live INSIDE the worktree** (its gitignored `work/`): the sandbox writes only the workdir. The cell edits files; the seat makes the commit and the `format-patch`.
- **The auto-mode classifier refuses running a downloaded build script** (`generate.sh`, as gen 48's). Read it statically, record that, and offer the owner a by-hand run.
- **A census subagent at the seat is the right tool for licence evidence** (gen 51 ran two: 240 + 170 blob-verified texts). Spot-check 3-4 of its claims in the binaries / against GitHub before relaying, and byte-check the cell's copied texts against the seat files after the cell turn.
- **A cell that meets one missing input stops the whole turn unless told otherwise** (t6 cost a turn over bzip2). Every data-loading dispatch now carries the per-row STOP rule.
- **A quoted heredoc still collapsed `\\U` in a Python string** (a dispatch-7 build script died on a `\U` escape). Write any backslash-bearing script with the Write tool. (Memory: bash-heredoc-backslash-collapse.)
- **The bare-`cd` slip recurred twice in gen 51** (each restored in the next call). Only `( cd X && ... )`.

### Gen-50 lessons

- **A package worktree needs the uncommitted `clearwater.local.toml` copied in before its first GATE.** Its absence passes every cell run and every seven-module re-run, then fails 12 tests in the parallel leg. Copy it when the worktree is created.
- **A load-sensitive test bound shows up when the owner's desktop is busy.** Before calling a failure a defect, re-run it alone, and at the previous head in the review copy.
- **Codex's sandbox cannot run real-git tests** (Win32 error 5). Plan the seat run of the RED and GREEN from a throwaway detached worktree (`git worktree add --detach`, copy the new test in, run, `git worktree remove --force`).
- **A REASONED MAJOR about a third-party action is settled cheaply** by reading its source at the pinned SHA with a read-only `gh api repos/<o>/<r>/contents/<path>?ref=<sha>`.
- **`grep -c $'\r'` in this Git Bash counts LINES, not CR bytes** (a false CRLF alarm at t19). Count bytes in Python.
- **`mkdir -p` the basetemp's parent before a seat pytest run** (a FileNotFoundError at setup looked like a test failure).

### Gen-49 lessons

- **PyInstaller collects DLLs through PATH.** A Git Bash build bundles `/mingw64/bin`'s OpenSSL and any JDK's UCRT. Hash-bind every native, and sanitize PATH inside the build.
- **Python's `Path.write_text` writes CRLF on Windows** (state commit `6d2be2e5` carried 128 CRs). Use `write_bytes` or `newline='\n'`. The memory file is updated.
- **A heredoc turns `\a` into BEL** (a state line said `seat<BEL>ction-shas`). Write backslash paths with the Write tool, or as `chr(92)` in Python.
- **The bare-`cd` slip recurred four times this generation** (each restored in the next call). The safe forms are `( cd X && ... )`, `git -C` and absolute paths.
- **The `rm` safety check refuses `rm $VAR/$VAR`.** Use a literal absolute path.
- **A resumed Codex session is cheaper only while depth is below about 150K.** A turn that adds about 40-60K needs a fresh session at 175K and above.
- **Read the third-party trees yourself.** SciPy's own `LICENSES_bundled.txt` omits cobyqa and mislabels packaging; PBS's `downloads.py` libffi pin is not what its Windows build uses.

### Gen-48 lessons

- **A cell's own worktree hides CRLF hazards.** Codex writes new files with LF, and the system `core.autocrlf=true` (Git for Windows' etc/gitconfig) converts them only on a FRESH checkout. Test every byte-pinned file from a fresh detached checkout before trusting the cell's green.
- **Licence detectors over-match.** "(at your option) any later version" is in every GPL text's appendix, and "noncommercial" is in GPL-2 section 3(c). The project's own grant is in its source headers.
- **Debian-style `License: GPL-2` means GPL-2.0-only.** Read the per-file stanzas in `COPYING.md`.
- **A string scan of a stripped static binary cannot prove an object absent:** `vbi.c` showed 0 hits while certainly linked. Trace the call graph from a linked unit instead.
- **A Python print to a redirected file is block-buffered,** so a long script shows nothing until it exits. Add `flush=True` when you need progress.
- **The bare-`cd` slip recurred three times this generation** (each restored in the next call). Prefix with `cd /c/Users/rwsmy/clearwater &&` and use subshells for everything else.
### Earlier generations' lessons

They are in `git log -p -- docs/orchestrator-state.md` (gen 47's state at `26be709f`, gen 46's at `5b6d422f`). The binding ones are in the rules block above.
