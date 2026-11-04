# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 44** (session `clearwater-orchestrator-20261104-0652`) LIVE from 2026-11-04 16:53Z. CHARC = **gen 15 `clearwater-charc-20261104-0027`**. Re-verify both names in `comms/.launch-sessions.json` before every cue.
- Seat folder `work/orch-g44/`:
  - `gate.sh` (legs `static collect parallel serial startup fullclip harness`; basetemps still named `g43-<run>-*`);
  - `watch2.sh`;
  - the drains;
  - the posts;
  - `fill_accept.py`.
- Bash gauge at bring-up: 44 ms.
- State worktree `.worktrees/orch-state-g44`. Run `git merge --ff-only main` before each edit, and ff main to it after the commit. The successor removes it and adds its own.
- **Disk:** C: 84 GB free at 17:12Z. Run `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB is needed before any window or gate.
- **Paces at 16:53Z:**
  - Codex 2 % / 0.497 (resets 2026-11-11 10:07Z);
  - Claude 39 % / 1.194 (resets 2026-11-09 10:00Z).

  Re-read at the next dispatch.
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (CHARC's order; the text is in `clearwater-review-evidence\wp6.1\cell\dispatch-15.md`). A cell-written GUI script is YIELDED to the seat UNRUN and reviewed before it runs:
  - grep it for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow;
  - check the PID-tree filter, the redirect and the bounds.

  It is then RUN AT THE SEAT FROM md5-CHECKED COPIES.
- **ROLLOVER TIMING (OWNER-RULED, CHARC FYI `08c0b43b`).** Below the 400K cap a seat starts the next unit WHATEVER ITS SIZE. It rolls at the first clean boundary AFTER 400K, with nothing it started still running. At or past the cap, dispatch nothing new.
- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02).** An Agent-tool cell and every background process die with the pane.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time.
- **ONE CODEX CELL AT A TIME**; a Codex REVIEWER pass is not a cell.
- **Gates:** `bash work/orch-g44/gate.sh <worktree> <run-id> <legs...>` (background), plus a Monitor on `bash work/orch-g44/watch2.sh <run-id> <summary line count before the start>` (30 min cap; re-arm).
- **Codex turns:**
  - Run a turn with `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1`, with **run_in_background**.
  - Commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`.
  - Depth = the footer's `depth_input_tokens`.
  - FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, with `tr -d '\r'`.
  - A RESUMED session's prompt = `dispatch-N.md` alone.
- **Claude reviewer pass for a Codex cell:** `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background).
  - Latest form: `clearwater-review-evidence\wp6.1\cell\codex-b\review-1\review-prompt-1.md` (a code delta, with mutation probes and the isolation pre-read).
  - Text-package form: `...\wp6.2\A\r1\review-prompt-r1.md`.
  - Assert from the seat log's JSON line: `model_ok`, `is_error` false, the verdict line, `worktree_clean_after`. Read `permission_denials` from `review.json`.
- **Codex review of a Claude cell:**
  - Reviewer A runs in a DETACHED review worktree, from a subshell: `cat prompt diff | codex exec -p strong -s read-only --skip-git-repo-check -c 'windows.sandbox="unelevated"' -`. Forms: `wp6.1\A\r4\` / `r5\`.
  - Reviewer B = the WSL script `clearwater-review-evidence\wp6.1\B\run_review_B.sh probe|review`.
- **Backslash-bearing Python helpers are written with the Write tool**, never a heredoc.
- **`rm` takes literal absolute paths.**
- A NEW file in a worktree must be `git -C <wt> add`ed before a pathspec commit.
- **A bare `cd` moves the session's cwd.** This includes `cd X && ...` at the START of a Bash command: the harness carries it whenever X is inside the working directories. Use ONLY `( cd X && ... )`, `git -C` and absolute paths. Gen 44 slipped twice at pickup, with no cell live.

### Live board (RESUME HERE)

**Nothing running** (no cell, no Codex turn, no reviewer, no gate) as of 17:15Z.

1. **WP6.1 ACCEPTED** 2026-11-04 17:14Z. Main at `b2eb4f74`. Record: `docs/proofs/wp6.1-accept.md`.
   - Nets: A converged r5; B clean; the Claude review of the Codex fold-in clean.
   - Gate `p61` green. D6 PASS. CP6a = ONEDIR.
   - Posted to CHARC and cued. CHARC writes AD-33 / AD-34 / the N13 row / the N14 onedir figures and the DR-125 brief.
   - Five fold-in advisories are banked in the record, for WP6.3 or the register.
2. **DR-125** (the export worker crashes at exit; the F-E stdin isolation moves into the worker and the `__main__` shim is removed; fail-closed inherited). WAIT for CHARC's brief (Codex lane), then dispatch.
   - Occurrences: 1 of 12 frozen worker runs; 0 in the timing window, the GUI check and D6.
3. **WP6.3** (the downloader plus the GitHub Actions workflow; onedir per CP6a). Expect CHARC's brief. Its hand check stages a REAL colour photo copied from the footage folder under `work/` (CHARC's D6 lesson).
4. **Push:** main is ahead of `origin/main`; a push needs the owner's word.
5. **Worktrees:**
   - main;
   - `orch-state-g44`;
   - `wp6.1`, kept for WP6.3: its `work\wp6.1\dist-on{dir,file}` builds and the hand-filled pack under `work\wp6.1\t3c\appdata` are pruned on the owner's word;
   - `wp6.2`, released, kept for the prune.

   `wp6.1-rA` and `wp-t8` were removed (branches kept).
6. **Prunes owed (owner's word only):** the wp6.1 builds and pack after WP6.3; `.worktrees/wp6.2`.

### Gen-44 lessons

- **Main can move between your `git log main` read and your merge** (CHARC's state commits). After `git merge main` into a package branch, read the merge's actual second parent (`git log --graph`) before citing it in a record.
- **`build.py` has no CLI bundle checker**: a read-only re-check of an existing build calls `forbidden_paths(root)` and `forbidden_entries(find_executable(root))` from the package venv (`python -B`).
- **A Claude review's `permission_denials`** were all compound shell lines it re-ran in allowed forms. Read them from `review.json` and say so in the record, rather than counting them as gaps.

### Gen-43 lessons

- **Run a reviewer pass IN PARALLEL with a cell when the cell's group changes no code** (a rebuild + proof, a report): r4, r5 and B each ran beside a cell and saved an hour. Detach the review copy at the code head; the cell's later ledger-only commits do not touch it.
- **A cell-written GUI / timing script is best RUN AT THE SEAT from md5-checked copies** after review: no queued-message race, the seat sees the windows' outcome first-hand, and the cell's depth is spared.
- **A queued amendment lands AFTER the cell's commit more often than not** (cell7 folded CHARC's amendment as a follow-up commit; cell9 committed a recommendation before the form-neutral amendment). Expect a follow-up commit; when a later bounded item duplicates what the amendment already did, send a STAND DOWN and wait for its reply (cell7: "stood down, no change").
- **A string `replace` on a shell script can hit a nested `case` arm** (`"    fullclip)"` matched the collect leg's inner `fullclip)`): anchor on a unique multi-line string and assert its count is 1.
- **`gate.sh` needed a `startup` leg** for a brief whose GATE_CHECKS name serial modules rather than the whole serial leg.
- Bare `cd` slipped three times this gen (twice with a cell live): every `cd` goes in a subshell, no exceptions.

### Gen-42 lessons

- **A worktree's `.venv` can be EMPTY** (wp-t8's was created with no packages): `uv run --no-sync pytest` then runs a global pytest, or another venv through an inherited `VIRTUAL_ENV`, and a cell reports false failures. Check `ls <wt>/.venv/Lib/site-packages | wc -l` before trusting a cell's test claims; `uv sync --frozen` fixes it.
- **Codex sandbox residual on the fixture audit tests:** the sandbox's restricted process adds a `nul` open and one launch to the audited child, so 3 `tests/test_fixtures.py` audit tests fail ONLY in the sandbox. The seat run is of record.
- **Every `sys.executable` re-entry must be handled by the frozen `__main__`**, or it reaches the GUI branch. WP6.1 found four: CuPy's canary (`-m`), CPython's flag prefixes (`-I -m`, `-Xutf8`, `-OO`), and `--multiprocessing-fork` / `--multiprocessing-resource-tracker`. Ask about `sys.executable` uses in third-party code in every frozen-build review.
- **A before-record run of a NEW test against an OLD revision executes the old code's branches**: wp61-cell5's test reached the old GUI branch with the owner's real profile. Hence CLAUDE.md's entry-point isolation rule (redirect app data AND block the GUI on ANY revision).
- **A blocked synchronous stdin read in a parent hangs every child that inherits that stdin on Windows** (F-E): a child spawned with `stdin=None` inherits STD_INPUT_HANDLE. The 1.0.0 export worker's cancel watcher does this; the product's own children set `stdin=` explicitly, third-party spawns do not.
- **V8 checks of record read an untracked `work/` path**: a prune silently turned 11 of them into skips for a week (DR-126). Before any prune, list the test nodes that read the pruned paths.
- **A cell's idle notification often arrives BEFORE it has processed your queued messages**: read what it says it is waiting for; do not resend.
- **Fold a reviewer's fixes into a pending code change BEFORE an expensive rebuild** (A r3 into F-E): one rebuild, one proof.
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
