# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 59** (session `clearwater-orchestrator-20261107-1113`). LIVE 2026-11-07 ~21:13Z; ROLLED 2026-11-09 at the 400K cap at a clean boundary (wp65-cell1 returned; nothing running). Bash gauge 28 ms.
- **CHARC is gen 20, `clearwater-charc-20261107-0949`.** Re-verify the name in `comms/.launch-sessions.json` before every cue.
- **Seat folder `work/orch-g59/`:** `gate.sh` + `watch2.sh` (repointed to orch-g59); `build_uia.py` (= gen 56's, md5 `48ae19ef`); `gpu_proof.seat.py` (label-only change); `check_build.py`, `check_draft.py`, `skipdiff.py`; `prune.py`, `prune2.py`; `wp65-fill.md`, `wp71-fill.md`; posts and drains. The CI-shaped rehearsal is still `work/orch-g58/rehearsal.py` (md5 `b93db3bf`).
- **State worktree:** `.worktrees/orch-state-g59` (branch `orch-state-g59`; remove it and add your own).
- **WP6.5 worktree:** `.worktrees/wp6.5` (branch `wp6.5`; venv synced, toml copied in).
- **Worktree list (8):** main, orch-state-g59, wp-dr125, wp6.1, wp6.3a, wp6.3b, wp6.4, wp6.5. Nothing owed to prune (the 2026-11-07 and 2026-11-09 batches are done: `docs/proofs/prune-2026-11-07.md`, `prune-2026-11-09.md`).

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (current text: `clearwater-review-evidence\wp6.5\cell\dispatch-1.md`, with the QUIT_SCRIPT exception and the Mac HOME reading).
  - A cell-written GUI or proof script is reviewed at the seat: grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow.
  - Such a script is RUN AT THE SEAT FROM md5-CHECKED COPIES.
- **No seat or review run executes the DR-125 "before" shape.**
- **EVERY CLAUDE REVIEW PROMPT BANS `run_in_background`.** `codex_cell.py review` keeps only the reviewer's LAST message. Check that `review.txt` is a full report before acting.
- **Launch a Codex turn or review ONLY with the Bash tool's `run_in_background`, never a shell `&`.**
- **ROLLOVER TIMING (OWNER-RULED).** Below 400K a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary after 400K with nothing it started still running (a live Agent-tool cell dies with the pane: wait for its return). At or past the cap, dispatch nothing new.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time. **Never edit a worktree a gate is running from.**
- **TWO CODEX SESSIONS ARE ALLOWED** (CHARC `a6934b58`), on disjoint files.
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session=<id>] > <dir>\turn-N.driver.stdout 2>&1` with run_in_background; commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>` (FILES CHANGED one literal path per line; else commit by pathspec in the worktree). Depth = the footer's `depth_input_tokens`; evaluate ~200K, STOP ~250K. FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, `tr -d '\r'`; RESUMED = `dispatch-N.md` alone. Never Write a dispatch and launch the turn that reads it in ONE batch. The first (non-resumed) turn needs an ABSOLUTE `--worktree`.
- **Claude cells (Agent tool):** depth with `uv run --no-sync python scripts/cell_depth.py --live 3 <name>` at dispatch, every yield, before any ruling; ~250K evaluate, ~400K STOP. Their reviewer is CODEX: `cat review-prompt.md review-diff.txt | tr -d '\r' | codex exec -p strong -s read-only --skip-git-repo-check -o review.txt - > review.out 2>&1` from the DETACHED copy (`( cd <copy> && ... )`); assert banner `gpt-6.1-sol` / `high`, `grep -ac '^ERROR'` = 0, `grep -ac '^tokens used'` = 1, the verdict.
- **Claude review of a Codex cell:** `codex_cell.py review --worktree <DETACHED copy> --base <sha> --prompt <p> --out <dir>`, background, at the seat (forms `wp6.3a\B\r1\review-prompt-B.md`, `wp6.3a\B\delta2\review-prompt-delta2.md`).
- **Gates:** `bash work/<seat>/gate.sh <worktree> <run-id> <legs...>` (background) + a Monitor on `watch2.sh <run-id> <summary line count>`, re-armed at 30 min; run `uv run mypy --platform darwin` beside the static leg. Copy the toml and `uv sync --frozen` in a new worktree first.
- **Backslash-bearing Python goes through the Write tool**, never a heredoc (it struck again in gen 59: a heredoc with `r"C:\Users..."` died on `\U`).
- **A bare `cd` moves the session's cwd.** ONLY `( cd X && ... )`, `git -C`, absolute paths.
- **QUIT_SCRIPT exception:** `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` runs at the SEAT in gate legs only; every cell run keeps `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
- **Running downloaded build scripts / binaries is refused** at this seat; read them as text.
- **CI-SHAPED REHEARSAL BEFORE EVERY TAG** (`work/orch-g58/rehearsal.py --runner-path`); **THE RELEASE SWEEP** before any Codex read of a bump; **RELEASE NOTES STATE BEHAVIOUR BY SHAPE** (DR-159 carries them into checklist v3).
- **A NEW WORKTREE'S `.venv` IS AN EMPTY SHELL** (`uv sync --frozen` first; the harness in an unsynced state worktree skips 40 -- run the harness on main).
- **CLAUDE.md is CHARC's** (owner 2026-11-09: the Current-state block is rewritten at each accept; narrative goes to `docs/project-log.md`); the orchestrator never appends to it.
- **Claude lane hold (CHARC, 2026-11-09):** if Claude weekly usage passes ~95 % before the 2026-11-09 09:59Z reset, hold the next Claude turn (WP6.5) and tell CHARC; Codex (WP7.1) proceeds regardless.

### Live board (RESUME HERE)

**1.1.1 is RELEASED** (published 2026-11-09 05:30Z by CHARC on the owner's word after the owner's clean-account check passed; record `docs/proofs/release-1.1.1.md`). Nothing more for the release.

**WP6.5 macOS validation** (brief `docs/briefs/wp6.5-brief.md` FINAL + my fill `49ca01bf`; Claude `implementer-opus-high`; both nets Codex; evidence `clearwater-review-evidence\wp6.5\`):
- Round 0 dispatched 05:36Z: cell `wp65-cell1`, dispatch `wp6.5\cell\dispatch-1.md` (READ-ONLY; ledger `docs/proofs/wp6.5-ledger.md`); depth 68,866 at dispatch.
- ROUND-0 RETURNED 2026-11-09 ~06:00Z: ledger commit **`a186c3ee`** on `wp6.5` (`docs/proofs/wp6.5-ledger.md`, 33,606 B, 0 CR; full evidence in its sections 0.0 and 3-8). Depth at the round-0 yield **254,025** (evaluation point): **group 1 goes to a FRESH `wp65-cell2` from the ledger**, not a resume. No STOP; ELEVEN findings for CHARC (the cell's return text is summarised here; the ledger is of record):
  - **F0-6 CONFLICTS WITH CHARC's Q5 RULING -- RAISE FIRST:** `workflow_dispatch` fires only for a workflow file present on the DEFAULT branch, so a new `macos-validation.yml` that exists only on `wp6.5` cannot be dispatched. The cell recommends instead ONE reusable `.github/workflows/macos-build.yml` with triggers `workflow_call` (input release-version) + `workflow_dispatch` + `push: branches: ["macos-validation/**"]`, called by `release.yml`'s `macos` job (`needs: windows`); the owner's stage-1 act is a push of the branch to `refs/heads/macos-validation/wp6.5` (`git push origin wp6.5:refs/heads/macos-validation/wp6.5`); windows job byte-identical; needs a grant for `tests/test_release_workflow.py` pins (:59-69, :441-458, :603). Gen 60 VERIFIES F0-6 at the seat (GitHub docs: "workflow_dispatch ... the workflow must be on the default branch") and posts the conflict to CHARC with the cell's alternative.
  - **F0-1 (ruling needed):** M-BUNDLE tests assume a `.app` (`tests/test_macos_portability.py:1566-1572`, `:1583-1606`); the onedir zip ships `Clearwater/Clearwater` + `_internal`; and `build.py` passes `--windowed`, so PyInstaller builds a `.app` on macOS anyway (makespec.py:472-474, :869-871). Q3 interacts.
  - **F0-2 (sizing):** `notices.py` is Windows-shaped; the Mac's N13 needs its own host census + a macOS FFmpeg lock with component texts + a toolchain census; the largest item, may need its own group.
  - **F0-3 / F0-4 correct CHARC note 4:** the runner (macos-latest = macos-26 = 26.6.2) is NEWER than the Mac (26.3.1); macOS 15+ has no Control-click Open (System Settings > Privacy & Security > Open Anyway, Apple support 102445).
  - **F0-5:** the notices skip hides 35 functions / 158 ids (not ~22); one more function reads `.venv/Lib/site-packages`.
  - **F0-7:** setup-uv's checksum is per platform: the seat must fetch the `uv-aarch64-apple-darwin` 0.10.9 sha256.
  - **F0-8:** standard arm64 runner = 3 vCPU M1 / 7 GB / 14 GB disk: `-n 3` on the macOS job only.
  - **F0-9:** framework symlinks in macOS builds; `build.py:2636-2637` (origin) and `_release_files` `:2769`/`:2777-2782` (zip) refuse every link.
  - **F0-10:** README is core-scanned; FORBIDDEN_TERMS includes the test-runner and linter names; the macOS prerequisites section must not name them.
  - **F0-11:** does the runner's serial leg run the QUIT_SCRIPT test (seat-only exception) or carry the cell `-k` exclusion? CHARC rules.
  - **Q1:** recommended label `macos-26` (arm64, 26.6.2, image 20261026.0455.2); no FFmpeg on the image; `hevc_videotoolbox` on the runner UNVERIFIED (the first run's `-allow_sw 0` trial decides).
  - **Q2 (no pick):** BtbN does NOT build macOS; martin-riedl.de 9.0.2 arm64 (sha256 sidecars, GPLv3 with libzvbi, build script Apache-2.0 with `-SKIP_ZVBI`, personal host); osxexperts FAILS (mutable URL, source points at 6.1); evermeet Intel-only + zvbi; jellyfin 8.1.3 not 9.x; **self-build in the owner's fork (Riedl script, `-SKIP_ZVBI`, macos-26, FFmpeg `b204e94e`) is the only candidate meeting every rule.**
  - **Q3:** `--windowed` = `.app` on macOS; PyInstaller ad-hoc re-signs; adding FFmpeg after signing may break the seal ("damaged") -- unverified, a run-sheet observation.
  - **CHARC notes designs:** note 1 = move the skip onto the `release` fixture (:191) and the native-reading test (:1049); note 2 = darwin PATH (interpreter bin, venv bin, /usr/bin, /bin, /usr/sbin, /sbin) + strip `DYLD_*`, set the DYLD fallbacks; the origin rule = a stdlib-struct Mach-O normalised identity (segments except `__LINKEDIT`, `__LINKEDIT` up to the signature, load commands without LC_CODE_SIGNATURE / LC_RPATH, dylib names by basename; one `@loader_path` rpath; relative in-folder framework links only), tested on Windows with synthetic thin and fat Mach-O fixtures; plus `smoke.py:578-597`'s darwin containment.
  - **M census:** 224 / 9,921 collected (matches WP6.4); runner families vs stage-2 families in the ledger section 7.
  - **Run sheet:** 15 steps; smallest full SCUBA clip GX011589 (48.8 MB, 6.4 s, start-up dominated; min 7 GiB) or GX011592 (396 MB, 42.3 s; min 8 GiB) -- CHARC picks.
  - **Groups:** G1 Windows-proved (note 1, note 2 + Mach-O identity + links, DR-123, smoke containment); G2a the macOS FFmpeg per Q2 + macOS notices census (+ an owner fork act if self-build); G2b the workflow per Q5 + release job + pins + actionlint; G3 fold each runner run; stage 2 the run sheet.
  - **Registration:** the new workflow file needs an `INSTANCE_SURFACE_RELPATHS` line beside `release.yml` (`tests/harness/genericity_lists.py:254`): a harness-file edit (seat edit or grant), then the harness gate.
- **Gen 60's next for WP6.5:** verify at the seat (read-only): F0-6 (GitHub's workflow_dispatch default-branch rule), Q1's runner lines, Q2's candidate claims (BtbN README line, Riedl sha sidecars / licence / `-SKIP_ZVBI`), F0-1's test lines, F0-9's build.py lines; then ONE query to CHARC: F0-6 vs the Q5 ruling FIRST (with the cell's push-trigger alternative), then Q1-Q3, F0-1, F0-2 sizing, F0-3/4 note corrections, F0-7..F0-11, the run-sheet clip pick, the group split. On rulings: write `dispatch-2.md` (group 1) for a FRESH `wp65-cell2` (FRESH prompt = the brief + the ledger at `a186c3ee` + dispatch-2; the hardware rules verbatim).
- **CHARC rulings already in hand (fold into dispatch-2):**
  - **Q5 RULED (`c0be531c`) -- BUT round 0's F0-6 says its dispatch vehicle cannot fire from a non-default branch; re-put to CHARC before any build:** option (a) in REUSABLE form: `.github/workflows/macos-build.yml` (`on: workflow_call`; inputs ref / version label; the job: CPU-only sync, W + M legs with `-rs`, both mypy targets, onedir bundle with the bundled FFmpeg, smoke, notices inventory, zip + sidecar as a WORKFLOW ARTIFACT); callers: `.github/workflows/macos-validation.yml` (`workflow_dispatch` on ANY ref, no gate, no release job = stage 1's vehicle) and a `macos` job in `release.yml` = `uses: ./.github/workflows/macos-build.yml` after the untouched tag gate (windows job byte-identical; the release job's `needs` and assets gain the macOS zip + sidecar; notices one file per platform, named by platform). Both new files GRANTED into Files owned; `actionlint` on all three; `tests/test_release_workflow.py` pins extended (Windows job unchanged by text, gate unchanged, validation workflow has no release job and no tag gate); every third-party action 40-hex pinned. (b) DECLINED. AD-38 (18) at the accept. Both new `.github/workflows/*.yml` files need `genericity_lists` registration.
  - **Stage-1 run:** when the first macos-build is ready and the two CHARC-note items are proved on Windows, post CHARC "ready for the owner's push of wp6.5 + dispatch of macos-validation on it" with the exact two lines; CHARC asks the owner each time.
  - **Fill clarifications 2-10 CONCURRED**; lane margin hold concurred.
- (superseded: see the round-0 entry's last bullet for gen 60's next steps.)

**WP7.1 Insta360 Studio exports** (brief `docs/briefs/wp7.1-brief.md` FINAL + my fill `c0569d03`; Codex `implementer-codex-sol-high`; both nets Claude; evidence `clearwater-review-evidence\wp7.1\`):
- **NOT YET DISPATCHED** (gen 59 was at the cap). Gen 60: create `.worktrees/wp7.1` from main (`git worktree add -b wp7.1 .worktrees/wp7.1 main`), copy the toml, `uv sync --frozen`, `mkdir` the evidence folders, write `wp7.1\cell\dispatch-1.md` (round 0 READ-ONLY: Q2 export_oracle, the probe / decode / export / timing driver plan, the entry-point redirection, the seat-run split per fill clarification 1, the inventory file name `docs/reports/inventory-2026-11-09.md`), then a FRESH Codex turn 1.
- **Q3 RULED (`9f2b04a1`): do NOT install the GPU pack;** the figures are source runs on the venv's CuPy. Fill clarifications 1-7 CONCURRED.
- Every EXCLUSIVE timing run and multi-minute export is run AT THE SEAT from md5-checked copies of the cell's drivers, CHARC told before each, never during a WP6.5 heavy run.

**Other standing items:** open rows DR-148..DR-153, DR-155, DR-157, DR-158 (watch), DR-159 (CHARC's checklist v3). C: about 2.6 TB free.

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
