# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 57** (session `clearwater-orchestrator-20261106-1214`). LIVE 2026-11-06 ~22:15Z; ROLLED 2026-11-07 ~18:30Z past the 400K cap at a clean boundary (nothing running: no cell, rehearsal, review, gate or build). Bash gauge 41 ms.
- **CHARC is gen 19, `clearwater-charc-20261106-1034`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g57/`:**
  - `gate.sh` + `watch2.sh` (repointed to orch-g57).
  - `rehearsal.py`: the CI-shaped rehearsal (`<commit> <evidence> [--from-step N] [--to-step N] [--reuse-clone] [--runner-path]`).
  - `cause_split.py`; `classify_fail.py`.
  - `spy/ffspy.py` + `spy/spy_report.py`: the ffmpeg-spawn spy, seat tooling only, never committed.
  - `prune.py` + `prune-log.jsonl` (the prune is DONE).
  - `make_prune_record.py`, `fill_d3.py`, posts and drains.
- **State worktree:** `.worktrees/orch-state-g57` (branch `orch-state-g57`; remove it and add your own).
- **Review copy:** `.worktrees/wp6.3e-rA` (detached, at `d6db4a0f`, its own `.venv`, deliberately NO `clearwater.local.toml`).

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (current text: `clearwater-review-evidence\wp6.3b\cell\dispatch-11.md`, with the QUIT_SCRIPT exception).
  - A cell-written GUI or proof script is reviewed at the seat: grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow.
  - Such a script is RUN AT THE SEAT FROM md5-CHECKED COPIES.
- **No seat or review run executes the DR-125 "before" shape:** a daemon blocked on `sys.stdin.buffer` at interpreter exit, or the OLD worker at `73453bdc`.
- **EVERY CLAUDE REVIEW PROMPT BANS `run_in_background`.** `codex_cell.py review` keeps only the reviewer's LAST message. Check that `review.txt` is a full report before acting.
- **Launch a Codex turn or review ONLY with the Bash tool's `run_in_background`, never a shell `&`.**
- **ROLLOVER TIMING (OWNER-RULED).** Below 400K a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary after 400K with nothing it started still running. At or past the cap, dispatch nothing new.
- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02).**
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time (gate, build, seat run). **Never edit a worktree a gate is running from** (gen 47 held two granted test edits until p64-s ended).
- **TWO CODEX SESSIONS ARE ALLOWED** (CHARC `a6934b58`), on disjoint files.
- **Codex turns** (FILES CHANGED must be one literal path per line, or `codex_cell.py commit` refuses; commit by pathspec in the worktree then):
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
- **A bare `cd` moves the session's cwd.** Use ONLY `( cd X && ... )`, `git -C` and absolute paths. It slipped in every generation 47-54 (gen 54: three times); each was restored in the next call.
- **QUIT_SCRIPT exception (owner's word, CLAUDE.md `1a38c935`):** `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` runs at the SEAT in gate legs and seat re-runs only. Every cell run keeps `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
- **No `rm -rf` on a command-substituted path** (the safety check refuses it). Use fixed paths under `work/`, or leave the folder.
- **Running downloaded build scripts is refused** by the auto-mode classifier ("code from external"). Read them as text (gen 48's `scriptsd_static.py`).
- **CI-SHAPED REHEARSAL BEFORE EVERY TAG (gen 57; CHARC rulings on WP6.3e).** A fresh `git clone` with no `work/`, no toml, no footage; the runner's PATH (no ffmpeg / ffprobe) and no GPU (`CUDA_VISIBLE_DEVICES=-1`); the workflow's own `run:` blocks extracted, not retyped: `work/orch-g57/rehearsal.py --runner-path`. The proof binds the head that gets tagged.

### Live board (RESUME HERE)

**The release is 1.1.1** (owner "tag 1.1.1" 2026-11-07 ~16:05Z, relayed by CHARC `9678e40f`). It authorises everything through the annotated tag `v1.1.1` made by the orchestrator. It does NOT authorise a push: the owner types the push lines after the tag report. `v1.1.0` (tag object `0127e1a2` -> `356f2e4d`) is ON ORIGIN with NO release and is NEVER moved. Its run `42387791040` failed at "Run parallel tests" on `--basetemp=work/ci-parallel` (record `clearwater-review-evidence\release-1.1.0\workflow\run-42387791040\`). The 1.1.1 notes are on main (`848701ce`, CHARC's).

**WP6.3e "release workflow fresh-tree fix"** (brief `docs/briefs/wp6.3e-brief.md` FINAL `ea4d6a36`; Codex lane, both nets Claude). Branch `wp6.3e` in `.worktrees/wp6.3e`, base `d14a09c1`, HEAD **`d6db4a0f`**; evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3e\`.

Turns (`cell\`):
- t1 `e9cde49d` (fresh session `01a1b6b8`): `New-Item -Force work` before the pytest line; `-Force` on staging; 2 pins; checklist step-9 sentence; the report.
- t2 `c66af644` (resumed): `_footage_root` stand-in in `tests/test_lookcheck_deep.py` (CHARC `a0df6f36`).
- t3 `8a30d6d4` (FRESH session `01a1b71b`): 93 FFmpeg guards across 15 granted modules (CHARC `3b0e47f3` + grant `875e398a`); `-rs` on the workflow line plus the pin; F-2 / F-4.
- t4 `d6db4a0f` (resumed `01a1b71b`, depth 184K): R2-1 / R2-2 unconditional guards in `tests/test_photo_verify.py` (CHARC `616c87d6`).

Reviews (Claude via `codex_cell.py review` on the copy `.worktrees/wp6.3e-rA`):
- A r1 on `c66af644`: NEW_CRITICAL_MAJOR. F-1, the runner has NO FFmpeg, was CONFIRMED (image `windows-2025-vs2026`; `actions/runner-images` `Windows2025-VS2026-Readme.md` lists none).
- A r2 on `8a30d6d4`: NO_NEW_CRITICAL_MAJOR, F-1 closed, R2-1 / R2-2 MINOR (folded in t4).
- A r3 (FINAL, must converge; else STOP to CHARC, no silent fourth) on `d6db4a0f`: NO_NEW_CRITICAL_MAJOR, NO findings (A CONVERGED; `A\r3\review.txt`, 35 turns).

Seat rehearsals (`seat\rehearsal\`, driver `work/orch-g57/rehearsal.py`):
- `e9cde49`: run 1 hit the driver's own sync limit; run 2 found the predicted 12 toml failures; run 3 build + staging PASS.
- `c66af64`: full run with the laptop PATH, PASS (8,367 / 210). Plus `skip-reasons.log` (the 3 extra skips = toml-absent skips by design).
- `c66af64-runnerpath`: runner PATH, 149 failed + 3 errors, all FFmpeg-absent. Causal split in `c66af64-causesplit\`: 152 node ids; FFmpeg dropped -> the same 152 fail; GPU hidden -> 152 pass.
- `8a30d6d-runnerpath`: the PRE-FOLD record, full runner-path run on t3's head: PASS end to end under runner PATH (sync 0 / 1,044 s; parallel `7522 passed, 1055 skipped` 0 in 246 s; build 0, no window; staging 0).

**NEXT (gen 58), per CHARC `616c87d6`:**
1. **The SPY RUN** (CHARC item 2) on `d6db4a0f`, under runner PATH, over the WHOLE parallel selection. **Gen 57's spy run 1 is INVALID** (`seat/spy/d6db4a0/`, driver `work/orch-g57/spy/run_spy.py`): it set `PYTHONPATH` to the spy folder to load `-p ffspy`, and `tools/package/build.py`'s environment check refuses a set PYTHONPATH (`ValueError: build environment: PYTHONPATH is set`, 231 E lines), so the leg read `253 failed, 7251 passed, 1058 skipped, 15 errors` (vs 0 failed without the plugin). Its partial list (17 passing nodes that spawned, 0 which-only) is NOT the record. FIX: copy `ffspy.py` into the clone's `.venv/Lib/site-packages/` (the clone is seat-owned, never committed) and drop `PYTHONPATH` from `run_spy.py`'s env; use a new `ev` folder (the script refuses an existing `ffspy-out`); the clone `work/ci-rehearsal/8a30d6d/src` is already checked out at `d6db4a0f`. Check the spy leg's summary equals the plain runner-path leg's (0 failed) before reading the list.
   - Seat tooling `work/orch-g57/spy/ffspy.py`: `-p ffspy`, PYTHONPATH = the spy folder, `FFSPY_OUT` = an existing folder. Then `spy_report.py <out>`.
   - Cheapest form: in the `8a30d64` pre-fold clone (`work/ci-rehearsal/8a30d6d/src`), `git -C <clone> fetch <repo> wp6.3e && git -C <clone> checkout --detach d6db4a0f` (the venv stays valid: same lock). Then the workflow's pytest line plus `-p ffspy`, with the env from `rehearsal.py --runner-path`: WinGet Links dropped from PATH, `CUDA_VISIBLE_DEVICES=-1`, redirected roots, `UV_FROZEN` / `UV_NO_SYNC`.
   - Every PASSING node that attempted an ffmpeg / ffprobe spawn gets a disposition: (a) legitimate (its asserts do not depend on the tool's result; one line of evidence each), or (b) a guard. The 7 tool-absent-purpose tests A r2 named are (a).
   - Any (b) means a turn 5 of guards only under the same grant (resumed `01a1b71b` is at 184K: use a FRESH session), then the spy run again.
   - The list and dispositions go into the report's `## Spy run` section. The seat writes it via a turn, or as a seat commit by pathspec in the worktree if CHARC allows.
2. **REHEARSAL OF RECORD on the FINAL head**, from a NEW fresh clone, `--runner-path`, every step: `uv run --no-sync python work/orch-g57/rehearsal.py <full sha> '<evidence>\seat\rehearsal\<sha7>-runnerpath' --runner-path`.
   - The sync takes about 17.5 min on this link (allowed 2 h). Expected: parallel 0 failed, about 1,055 skipped (1,055 at t3), build 0 with no window, staging 0.
   - The report's `Seat runner-path rehearsal on the final head` line gets the figures.
3. **Reviewer B (Claude, the whole package `d14a09c1..HEAD`)** at the seat on the final head (form: `wp6.3e\A\r1\review-prompt-A1.md` widened to the whole package plus the brief; ban `run_in_background`).
4. **The package gate** on the final head (GATE_CHECKS: static, collect, parallel, harness; serial too, since t3 touched serial-leg modules). The laptop parallel floor is expected UNCHANGED at 8,367 passed / 210 skipped, collection 8,577 (CHARC Q3 (b)). `gate.sh` lives in `work/orch-g57/`; copy `clearwater.local.toml` into the worktree first (it IS there).
5. **ACCEPT** (CHARC writes AD-38 item (17), the register rows: the 1.1.0 workflow-failure record, (b) banked "the workflow leg runs the FFmpeg tests against the bundled FFmpeg", the non-reproducible-zip limit), then ff main.
6. **THE 1.1.1 BUMP** (owner's word in force):
   - Bump in the five places: `pyproject.toml`, `src/clearwater/__init__.py`, `uv.lock`'s root package, the `THIRD_PARTY_NOTICES.md` title, and `tests/test_version.py`.
   - Plus the GPU pack installer User-Agent pin `Clearwater/1.1.1` and its test. Grep: `git grep -nE '"1\.1\.0"|/1\.1\.0'` over `tests src tools`, minus `native-licences`.
   - ONE read-only Codex pass over the bump diff + the WHOLE `docs/release-notes-1.1.1.md`, with a per-claim table.
   - ff + FREEZE.
   - Release build + proofs at the new head (`work/orch-g56/build_uia.py`, md5 `48ae19ef`; CPU export V4; GPU proof NOT repeated, stated as a limit).
   - The FULL step-6 gate (static + darwin mypy, collect, parallel, serial, fullclip, harness, `test_gpu_pack_install.py` alone).
   - The annotated tag `v1.1.1` at the main checkout on the gated commit; report to CHARC.
7. Then the owner's push, steps 8-10 (run watch; draft assets: zip sha256 = the runner's OWN sidecar, member SET vs the local build since builds are NOT byte-reproducible, notices byte-equal, `# source-commit:` = the tagged commit = github.sha), the clean-account check, CHARC's `docs/proofs/release-1.1.1.md`, Publish.

**Other standing items:** `.worktrees/release-1.1.0` and `work/release` (the 1.1.0 local build) are kept until CHARC says otherwise. WP6.5 (Mac) and WP7.1 (Insta360) come after 1.1.1. Open rows DR-148..DR-153.

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
