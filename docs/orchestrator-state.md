# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 42** (session `clearwater-orchestrator-20261104-0051`) LIVE 2026-11-04 10:51Z. CHARC = **gen 15 `clearwater-charc-20261104-0027`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g42/` (gate.sh / watch.sh / watch2.sh / fill_gate.py, sed g41->g42; drains, posts, helper scripts). Bash gauge at bring-up: 32 ms. State worktree `.worktrees/orch-state-g42` (`git merge --ff-only main` before each edit; ff main to it after the commit).
- **Disk:** C: 80 GB free at ~12:05Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window or gate.
- **Paces at 10:52Z:** Codex 1 % / 2.273 (window reset 10:07Z; elapsed 0.4 %, not yet meaningful); Claude 33 % / 1.134 (resets 2026-11-09 10:00Z).
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE (CLAUDE.md, CHARC `97356556`, after the WP6.1 incident 2026-11-04 ~09:13-09:19Z).** Paste it VERBATIM into EVERY dispatch (CHARC's order): "**Desktop input rule (2026-11-04, after a WP6.1 incident):** no cell or seat sends synthetic keyboard or mouse input to the desktop (SendKeys, SendInput, keybd_event, AppActivate, mouse_event or equivalents). A GUI check uses UI Automation on Clearwater's own window elements, Qt's offscreen platform and test hooks, PrintWindow for a screenshot of Clearwater's own window, or the owner by hand. A stray keystroke lands in whatever the owner has in front." A cell-written GUI script is YIELDED to the seat UNRUN and grepped for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui before it runs.
- **ROLLOVER TIMING (OWNER-RULED, CHARC FYI `08c0b43b`, main `b41a76c8`).** Below the 400K cap a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary AFTER 400K with nothing it started still running. At or past the cap, dispatch nothing new. Owner (2026-11-03): "I do not want rollovers to happen until after 400k is hit. Once it is hit, rollovers should happen as soon as practicable."
- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02, verbatim: "the generations should not have handed over if the previous generation was still working").** An Agent-tool cell and every background process die with the pane.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time. A light Codex / Claude turn beside an IMAGE batch is fine; nothing beside a serial leg, a fullclip leg or a timing window.
- **ONE CODEX CELL AT A TIME** (CLAUDE.md); a Codex REVIEWER pass (`codex exec -s read-only`) is not a cell and may run beside one.
- **Gates carry WP-T7's flags** and the STALL WATCH: `bash work/orch-g41/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial fullclip harness`; summary `work/orch-g41/gate-<run>/summary.txt`) + Monitor `bash work/orch-g41/watch2.sh <run-id> <summary line count before the start>` (30 min cap; re-arm).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` with **run_in_background**; commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>` (it stages new files itself); depth = the footer's `depth_input_tokens`; FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, `tr -d '\r'`; a RESUMED session's prompt = `dispatch-N.md` alone.
- **Reviewer passes (Claude, for a Codex cell):** `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background). Forms this gen: A `clearwater-review-evidence\wp6.2\A\r1\review-prompt-r1.md` (text package), r2/r3 built from it; B `...\wp6.2\B\review-prompt-B.md`. Assert from the seat log's JSON line: model_ok, is_error false, the verdict line, worktree_clean_after.
- **Codex review of a Claude cell (Reviewer A this gen):** a DETACHED review worktree `.worktrees/wp6.1-rA` at the head under review (so the live cell's edits cannot leak in); from it: `cat prompt diff | codex exec -p strong -s read-only --skip-git-repo-check -c 'windows.sandbox="unelevated"' - > review.out 2>&1`; the final answer = the lines after the LAST `^codex$` line up to `^hook: Stop$`. Form `clearwater-review-evidence\wp6.1\A\r2\review-prompt.md`. Reviewer B for a Claude cell = the WSL script `clearwater-review-evidence\wp5.7\B\run_review_B.sh probe|review` (gen 39's form).
- **Backslash-bearing Python helpers are written with the Write tool**, never a heredoc (a quoted heredoc still breaks `\U`). **`rm` takes literal absolute paths.** A NEW file in a worktree must be `git -C <wt> add`ed before a pathspec commit. **Worktree release:** a released worktree's `work/` is pruned only on the owner's word.
- **A bare `cd` moves the session's cwd** (it carries between Bash calls, and a live Claude cell shares the process): use `git -C`, absolute paths, or `( cd X && ... )`. Gen 41 slipped twice; a background command's `cd` does not carry.

### Live board (RESUME HERE) -- gen 42, checkpoint ~12:10Z (LIVE: the WP-T8 gate t8a running; wp61-cell5 building code before its mid-build yield)

1. **WP-T8, tools and tests paydown** (`docs/briefs/wp-t8-brief.md`, FINAL). Codex lane; both nets Claude at my seat. Worktree `.worktrees/wp-t8` (its `.venv` was EMPTY until gen 42 synced it 10:58Z: `uv sync --frozen`), branch `wp-t8`. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp-t8\` (`cell\dispatch-1..7`, returns 1-7; `A\r1`, `B`, `dr116\`, `seat\`).
   - Commits: `90fd9263` group 1, `d558c48a` group 2, `6d0a249a` the report (session 2 `01a1a634-b204-7461-8583-978ef7876d56`, fresh at turn 4), `0e784986` A r1 minors, `a844a37f` merge of main (`23fd9a5f`), `ad385cbb` B follow-up (B1 fallback to basetemp + warning, B8 utf-8, B4 ROW before write, B9, report B3 / B6 / B7 / V8 restore). Session 2 RETIRED at **238,421** (turn-7 end).
   - Reviewer A r1 (Claude, on `6d0a249a`): NO_NEW_CRITICAL_MAJOR, F1-F6 minor fixed at `0e784986`. Reviewer B (Claude, on `a844a37f`): NO_NEW_CRITICAL_MAJOR, B1 minor + B3/B4/B6-B9 advisories fixed at `ad385cbb` (read at the seat), B2 = DR-126's count (11 V8 skips, none yuvj: the yuvj skip is in the PARALLEL leg) -> tell CHARC at the accept, B5 noted.
   - CHARC rulings: both DR-116 reductions DECLINED (`658e4c90`); DR-116 CLOSES at the accept on the attribution (+660 s = new coverage, +617 new / +43 shared); the 3 `test_fixtures.py` audit tests = sandbox-only residual, no DR row (seat passes: main 3/3, worktree 3/3, full set 488, with the shim 3/3).
   - **V8 frames restored** (CHARC `7873d925`): `GX011625_0024.925.png` (8,105,999 B, md5 dab5821e...) and `GX011625_0114.648.png` (3,093,211 B, md5 8ca1d0af...) copied from `D:\clearwater-archive\work\wp1.3\frames\` into the main `work\wp1.3\frames\`, md5 = `D:\clearwater-archive\manifests\wp1.3.md5`; record in the accept record; the gate should now run the 11 V8 nodes (serial skips expected 0).
   - **Gate `t8a`** on `ad385cbb`: `bash work/orch-g42/gate.sh wp-t8 t8a static collect parallel serial fullclip` (bg) + Monitor watch2 `t8a 0`. Summary `work/orch-g42/gate-t8a/summary.txt`. Then: fill the report's gate figures, the accept record `docs/proofs/wp-t8-accept.md` (+ harness registration not needed: no new root/docs file other than the report? CHECK `tests/harness/genericity_lists.py` for `docs/reports/` coverage before Reviewer-B-equivalent; run the harness leg on the merge head), merge `--no-ff` to main via the branch, ff main, post the accept to CHARC.
2. **WP6.1, packaging spike** (`docs/briefs/wp6.1-brief.md`, FINAL + every rulings bullet). Claude opus-high lane; Reviewer A = Codex at my seat (detached `.worktrees/wp6.1-rA`), Reviewer B = WSL Codex script. Worktree `.worktrees/wp6.1`, branch `wp6.1`. Ledger `docs/proofs/wp6.1-ledger.md`. Evidence `clearwater-review-evidence\wp6.1\` (`cell\dispatch-1..7`, `t2a`..`t3c`, later `t3d`).
   - Gen 42: merged main into wp6.1 (`1e043cfc`). **Group 2b-2** (wp61-cell4, RETIRED at **300,127** at its yield): `7af84366` cheap pack check (RECORD sizes, ownership, wheel platform tags) + `build.py --verify`; `472b0b6e` #10 move-to-front with dedupe; `97eff4e6` ledger. Pack hand-filled in `work\wp6.1\t3c\appdata\` (11 dists, 2,701 files, 2,412.6 MiB, `--verify` PASS). STOPPED on F-C2 (bundle lacks `ctypes.wintypes`, `graphlib`) and F-D (CUDA pathfinder's canary runs `sys.executable -m`, which reached the frozen GUI branch: a window possible <=10 s ~11:35-11:40Z, no input; relayed to the owner by CHARC).
   - CHARC rulings (`bfaeba37`): F-C2 (iii) AST-scanned stdlib set + committed extension-only list, build FAILURE on a gap, the set in the build report, two tests; F-D (i) frozen-only `-m` ONLY for modules resolving from the ACTIVATED pack, other `-m` / `-c` refuse with one stderr line and no GUI; F-C no allowlist; the 2b-1 test deviation concurred. **STANDING: no pack-activating run until the F-D handler is in the build under test; never run `t3c\exp\` builds.**
   - **Group 2b-3 = wp61-cell5 (FRESH, dispatched ~11:50Z, `cell\dispatch-7.md`)**: items 1-3 (code + tests), then a **MID-BUILD YIELD**; I give the word to build only when the WP-T8 gate's serial and fullclip legs are DONE. Then both rebuilds, the WITH-pack GPU proof (UIA window listing on its own PIDs = no window), ledger, YIELD. Then Reviewer A r3 (Codex, whole package from `c051306f`; diff `git diff c051306f..<head> -- src tests tools pyproject.toml uv.lock ':!tests/harness'`; form `A\r2\review-prompt.md`).
   - Remaining after: group 2c (the GUI check script YIELDED UNRUN, the frozen loader line); turn 4 timings (EXCLUSIVE window ~35 min) and the report with the CP6a recommendation (F-B under onefile; AD-34 text per CHARC; one line on the incident); Reviewer B; the gate.
3. **DR-125** (export worker crash at interpreter shutdown): CHARC writes the brief after WP6.1's accept (Codex lane, `export_worker.py` + tests).
4. **Push:** main ahead of `origin/main`; a push needs the owner's word.
5. **Worktrees:** main; `orch-state-g42`; `wp6.1` (live); `wp6.1-rA` (detached at `16e03c0f`); `wp-t8` (gate running); `wp6.2` (released, kept for the prune).

### Gen-42 lessons

- **A worktree's `.venv` can be EMPTY** (wp-t8's was created with no packages): `uv run --no-sync pytest` then runs a global pytest, or another venv through an inherited `VIRTUAL_ENV`, and a cell reports false failures. Check `ls <wt>/.venv/Lib/site-packages | wc -l` before trusting a cell's test claims; `uv sync --frozen` fixes it.
- **Codex sandbox residual on the fixture audit tests:** the sandbox's restricted process adds a `nul` open and one launch to the audited child, so 3 `tests/test_fixtures.py` audit tests fail ONLY in the sandbox. The seat run is of record.
- **A library inside the GPU pack can re-enter the frozen exe** (`cuda.pathfinder`'s canary = `sys.executable -m ...`): any `sys.executable` re-entry must be handled by the frozen `__main__`, or it reaches the GUI branch. Ask about `sys.executable` uses in third-party code in every frozen-build review.
- **V8 checks of record read an untracked `work/` path**: a prune silently turned 11 of them into skips for a week (DR-126). Before any prune, list the test nodes that read the pruned paths.
- A bare `cd` slipped once at bring-up (with a cell live, then restored): subshells ONLY.

### Gen-41 lessons

- **A GUI-driving cell script can type into the owner's windows.** wp61-cell1's `AppActivate` + `SendKeys` failed to raise Clearwater and typed a path + Enter into another harness's Claude session and a browser login page. The rule is now in CLAUDE.md (verbatim block above) and memory `no-synthetic-keystrokes`. A GUI script is yielded UNRUN and reviewed at the seat before it runs.
- **Run the Codex reviewer of a Claude cell from a DETACHED copy** (`git worktree add --detach .worktrees/<pkg>-rA <head>`): the live cell keeps editing the package worktree while the review reads files.
- **PyInstaller's standard runtime hooks run before the entry script in EVERY bundle process** (`pyi_rth_pyside6` imports `PySide6.QtCore`), so a deferred import in `__main__` does not make a frozen worker Qt-free. And `--clean` empties PyInstaller's cache at `%LOCALAPPDATA%\pyinstaller` unless `PYINSTALLER_CONFIG_DIR` points into the output folder.
- **A bundle "absent" check must look at every path component, case-folded, ZIP members recursively, every CArchive entry type** -- A r1 and A r2 both broke it with in-memory planted names. Derive the CUDA-name test list from the wheels' own RECORD files (`nvblas64_12.dll` was missed).
- **A text package converges by the text-round rule**: stop at the first round with zero text-bearing findings or after round 3; round 3's exact corrections are applied once without a fourth review; then Reviewer B. WP6.2: three A rounds, B clean, six Codex turns, two sessions.
- **A brief's premise can be wrong about caller behaviour** (WP-T8 Q3 "the export continues uncached"): the cell's caller trace (store -> engine -> export) is the reproduction; route as a STOP with the trace.
- **The seat CHARC can roll while you work**: re-read `comms/.launch-sessions.json` for the cue name after any CHARC rollover notice.
- Bare `cd` slipped twice (once with a cell live); a heredoc with `\U` in a Python string broke a helper (Write tool for any backslash content).

### Gen-40 lessons (WP-H1 additions)

- **A reviewer's mutation probes find untested guards that a green suite hides.** Both nets did it on WP-H1 (A r1 F1 MAJOR; B3). Ask every review prompt for mutation probes against a COPY of the code under the probe folder.
- **A re-port diff (instance → template) can carry hunks that predate the package.** WP-H1's would have put back a private identifier the template had deliberately removed. Before the accept, diff against `template/main` and scan the added lines for instance vocabulary.
- **The Codex sandbox's restricted token cannot list `tempfile.mkdtemp`'s 0o700 dirs.** Preload `scripts/sandbox_mkdir_shim.py` into unittest:
  `PYTHONPATH=scripts uv run --no-sync python -c "import sandbox_mkdir_shim, unittest, sys; ..."`
  The seat's unshimmed run is the suite of record.
- **A dispatch's command spelling can trip a doc guard.** `test_doc_acceptance` bans the literal `--session ` (with a space), so write `--session=<id>` in kernel docs.
- `tests/harness/test_cell_depth.py` imports a sibling `_loader`: run it with `discover -s tests/harness -p test_cell_depth.py`, not `-m unittest tests.harness...`.
- **Native Windows Python does not resolve `/c/...` paths.** Read the driver JSON with `grep`, or pass `C:\` paths.

### Gen-40 lessons

- **A new root-level or `docs/` file needs its harness registration** (`tests/harness/genericity_lists.py`, `INSTANCE_SURFACE_RELPATHS`). Only the harness leg catches it (the genericity guard + manifest accounting); gate `p55`'s harness leg failed on WP5.5's three release files after 70 minutes of green pytest legs. **Run the harness gate on the package head BEFORE Reviewer B**, and put the registration in the brief's owned files.
- **A Codex cell's licence-text copy must decode as UTF-8 bytes explicitly**: the locale default (cp1252) garbled two texts, and the self-check hashed the garbled copy. Ask for hashes of the SOURCE bytes and a marker scan (`Â`, `Ã`, `â€`, U+FFFD).
- **The Codex sandbox has no network**: anything needing an index (`uv run --with ...`, a lean sync with uncached packages) runs at the seat. Record the exact command in a `.record.txt` beside its log, or the reviewer cannot tell what ran.
- **The review driver appends the whole diff**: for a package with a large generated file, exclude it through `codex_cell` (`DIFF_EXCLUDES` patched by a `python -c` wrapper) and tell the reviewer to read it with tools.
- **A dispatcher's fill of a ruling into a cell's report can mis-scope it** (B re-run N-3: my fill made CHARC's concurrence cover a broader sentence): fill with a sentence of its own.
- A bare `cd` in a Bash call moved the session cwd twice this generation (no cell live): use `git -C` or a subshell.

### Gen-39 lessons

- **A relayed amendment is processed AFTER the cell's yield** (third time across generations): wp57-cell8 rewrote `run-part3r.sh` one minute into the seat's GPU piece (bash reads a script as it runs). Before running ANY cell-written script after a yield, send HOLD and wait for the reply, or copy the script into the seat folder and run the copy. Memory updated.
- **Kill only the wrappers** when a running script is compromised: `taskkill /PID <bash> /F` without `/T` left the render (python) running to completion; finish the remaining pieces by hand with the original command and log it in runs.txt.
- **Merge main INTO the package branch (`--no-ff`) instead of rebasing** when the report / ledger cite commit hashes; gate the merge head; a later docs-only main commit gets a second merge plus a harness re-run; then ff main.
- **Reviewer B form for a Claude cell** = the WSL script `clearwater-review-evidence\wp5.7\B\run_review_B.sh probe|review` (gpt-6.1-sol / high per call); assert banner, `^ERROR`, footer, `^ succeeded in`, verdict, NUL; a re-run lists the first pass's table (form `B\r2\`).
- **The harness suite prints "acked 1 message(s); moved inbox -> read."** from its own temp mailbox: not the real inbox (check `ls -t comms/orchestrator/read | head -1`). Capture the harness run to a file and grep `^Ran|^OK|^FAILED`.
- I moved the session cwd with a bare `cd` three times while cells were live (absolute paths saved them): use `( cd X && ... )` or `git -C` ONLY.

### Gen-38 lessons

- **A work addendum queued to a cell is processed BEFORE a later stand-down** (wp57-cell5 committed `368b02d2` after its successor was dispatched): never queue work to a cell you may re-seat; send the stand-down, wait for its reply, then dispatch.
- **Python on Windows prints CRLF into a pipe**: a bash `mapfile` of a tool's list keeps the CR (the Part 3 photo batch refused all 70 ids); strip with `tr -d '\r'` and check cell-written window scripts for list pipes before a window.
- **A rebase orphans every commit hash a test or report pins** (WP-DR25: `6dfccdfc` -> Reviewer B MAJOR). Pin revision-loaded code by BLOB id (rebase-stable) and cite runs by instrument blob id plus subject; merge fast-forward.
- When a Codex report turn is running beside an image batch, CHARC confirmed it is fine (not timed).
- A dispatch's "featured frame" list must be copied from the ledger's table of record, not retyped (gen 37 wrote compilation line 1; Part 1's is line 3).

### Gen-37 lessons (carried)

- Edits made with the Edit tool on a CRLF checkout commit CRs with `-c core.autocrlf=false`: write state edits with a Write-tool script that normalises to LF, then blob-check 0 CR.
- A Codex read-only reviewer on a seat-run instrument keeps finding write-path hardening: declare a hostile local actor OUT OF ENVELOPE in the review prompt up front.
- The WP-DR25 `analyse --long` takes about 85 min; plan the GPU queue around such runs.
- A cell's mid-build yield before GPU work is what lets the seat serialise heavy jobs.

### Gen-36 / 35 lessons (carried)

- A fresh worktree has no `work/` (gate.sh does `mkdir -p work`).
- `TaskStop` on a backgrounded `gate.sh` kills only the outer shell: `taskkill /PID <pid> /T /F` the script's bash (find with `Get-CimInstance Win32_Process | ? CommandLine -match 'gate.sh|pytest.exe'`); confirm nothing is left.
- Count CR bytes with `git show HEAD:<f> | tr -cd '\r' | wc -c`.
- A Codex cell's report that cites `work/<pkg>/...` needs durable copies under `clearwater-review-evidence\<pkg>\` before merge.
- The Codex driver footer's `context_window` changes mid-session (258,400 <-> 475,000): record depth with its window and moment.
- The auto-mode classifier refuses bulk deletion under the main tree's `work/`: stage it in a guarded script and give the owner the `! bash <script>` line.
- A window script that runs a tool by relative path must run with the PACKAGE worktree as cwd.
- An NVENC encode fed slowly can hang (DR-115, now watched by AD-32): diagnose with `Win32_Process` I/O counters sampled twice.
- Run the seat's own `bash -n` on every cell-written script.
