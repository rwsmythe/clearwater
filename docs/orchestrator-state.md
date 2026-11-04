# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 45** (session `clearwater-orchestrator-20261104-0836`), LIVE since 2026-11-04 18:36Z.
- CHARC is **gen 16, `clearwater-charc-20261104-0738`**. Re-verify both names in `comms/.launch-sessions.json` before every cue.
- Seat folder `work/orch-g45/`: `gate.sh`, `watch2.sh`, drains 1-3, the posts, and the accept draft `wp-dr125-accept.md`.
- Bash gauge at bring-up: 41 ms.
- State worktree: `.worktrees/orch-state-g45`.
- **Disk:** C: 82 GB free at 19:34Z. Run `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB is needed before any window or gate.
- **Paces at 18:37Z:**
  - Codex 3 % / 0.594 (resets 2026-11-11 10:07Z);
  - Claude 42 % / 1.246 (resets 2026-11-09 10:00Z).
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (the text is in `clearwater-review-evidence\wp-dr125\cell\dispatch-9.md`). A cell-written GUI or proof script is reviewed at the seat (grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow) and RUN AT THE SEAT FROM md5-CHECKED COPIES.
- **WP-DR125 turn-4 ruling, point 4 (CHARC):** NO seat or review run may execute the DR-125 "before" shape: a daemon blocked on `sys.stdin.buffer` at interpreter exit, or the OLD worker at `73453bdc`. Sandbox only. Every review prompt says so.
- **EVERY REVIEW PROMPT BANS `run_in_background`** (gen 45). `codex_cell.py review` keeps only the reviewer's LAST message, so a reviewer that backgrounds a command loses its report (DR-125 B r1). Add: "NEVER use run_in_background ... your FINAL message must be the COMPLETE report". Check that `review.txt` is a full report before acting on it. Memory: `review-driver-background-loses-report`.
- **ROLLOVER TIMING (OWNER-RULED).** Below 400K a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary after 400K with nothing it started still running. At or past the cap, dispatch nothing new.
- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02).**
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time.
- **TWO CODEX SESSIONS ARE ALLOWED** (CHARC `a6934b58`). The seat serialises the HEAVY jobs: one gate, build or seat run at a time.
- **Codex turns:**
  - Run a turn with `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1`, with run_in_background.
  - Commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>`.
  - Depth = the footer's `depth_input_tokens`; evaluate at about 200K, STOP near 250K.
  - FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, with `tr -d '\r'`.
  - A RESUMED session's prompt = `dispatch-N.md` alone (`tr -d '\r'`).
- **Claude review of a Codex cell:**
  - Run `codex_cell.py review --worktree <DETACHED review copy> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background at the SEAT is fine; the REVIEWER must not background).
  - The review copy: `git worktree add --detach .worktrees/<pkg>-rA <head>` + `uv sync --frozen` + `clearwater.local.toml`. Move it with `git -C <copy> checkout -q --detach <new head>`.
  - Forms: `wp-dr125\B\r1b\review-prompt-B.md` (a full B pass), `wp-dr125\B\delta\review-prompt-delta.md` (a fold-in delta), `wp6.3a\A\r1\review-prompt-r1.md`.
- **Gates:** `bash work/<seat>/gate.sh <worktree> <run-id> <legs...>` (background), plus a Monitor on `watch2.sh <run-id> <summary line count>`.
- **Backslash-bearing Python is written with the Write tool**, never a heredoc (gen 45 slipped once: `\f` in a path).
- **A bare `cd` moves the session's cwd**, including `cd X && ...` at the start of a Bash call. Use ONLY `( cd X && ... )`, `git -C` and absolute paths. Gen 45 slipped once, into the memory folder.

### Live board (RESUME HERE)

1. **WP-DR125: AT THE GATE.** Branch `wp-dr125` at **`ee3877c1`**; the product is final at `96c364f0`; main is merged at `15ee158d`.
   - Nets: A converged at r2; B r1 + r1b and the delta review are all NO_NEW_CRITICAL_MAJOR and folded in turns 7-9.
   - The frozen re-check of `96c364f0` is GREEN (`wp-dr125\frozen2\`) and the report section is filled.
   - Gate `pdr125` (static collect parallel serial harness) is running from 19:34Z; static and collect are green.
   - The accept draft is `work/orch-g45/wp-dr125-accept.md`. Fill GATE_TABLE / GATE_SUMMARY / MERGE_TEXT, copy it to `docs/proofs/wp-dr125-accept.md` in the worktree, re-run the harness, commit by pathspec, `git merge --ff-only wp-dr125` on main, post to CHARC (CHARC closes DR-125 and amends AD-34 / AD-31), and archive the gate to `clearwater-review-evidence\wp-dr125\gate\`.
   - Then release `.worktrees/wp-dr125-rA`.
   - The cell session `01a1a7b0` is at 230,686 / 475,000 (turn-9 end). It is not to be resumed further: re-seat if anything more is needed.
2. **WP6.3a: the fold-in dispatch is READY.** It is `wp6.3a\cell\dispatch-4.md`, with reading A confirmed by CHARC `6299db37` plus the three added lines.
   - **AFTER the DR-125 accept:**
     - merge main into `wp6.3a` (conflicts in `__main__.py`, `test_frozen_entry.py`, `tools/package/README.md` and `gpu_pack.py`: keep both packages; 6.3a's head `53748e82` still has the shim lines DR-125 deleted);
     - set `HEAD_TBD` in dispatch-4;
     - run a resumed turn of `01a1a7b8-97bb-7451-bb5a-adeb5a5c6387` (140,581 / 475,000 at turn-3 end).
   - Then A r2 on `.worktrees/wp6.3a-rA`; the seat run (onedir build from the 6.3a head; 1.725 GB download into a redirected LOCALAPPDATA; expect **2,679 files**); B; the gate; the accept.
3. **WP6.3b and WP6.4:** the briefs are DRAFT on main, for your fill. 6.3b goes after 6.3a's accept, with CHARC's additions (`--disable-windowed-traceback` + a product exception hook). 6.4 goes after DR-125's accept (Claude opus-high).
4. **Push:** main is ahead of `origin/main`. CHARC batches the owner's push.
5. **Worktrees:** main; `orch-state-g45`; `wp-dr125` + `wp-dr125-rA`; `wp6.3a` + `wp6.3a-rA`; `wp6.1` (KEPT: the hand-filled pack at `work\wp6.1\t3c\appdata\Local\Clearwater\gpu-pack\14.2.0-cu12` serves the frozen checks); `wp6.2` (released).
6. **Prunes owed (the owner's word only):** the wp6.1 builds and pack after 6.3a's seat run; `.worktrees/wp6.2`; the `wp-dr125` onedir build after the accept.

### Gen-45 lessons

- **`codex_cell.py review` loses a reviewer's report if it backgrounds a command.** See the binding rule above. Recovery was a full re-run (`B\r1b`), about 15 min.
- **A fold-in that changes product bytecode after a frozen check needs a rebuild and a re-check.** That took 71 s to build plus 70 s for 12 runs from `frozen2\` copies. Freeze `src/` for later fold turns (turn 9: "NO PRODUCT FILE CHANGES").
- **A behavioural replacement of a structural test can lose coverage** (DR-125 M-3): console `python.exe` masks a `SetStdHandle` skip. A Win32 slot fact must be taken under `pythonw.exe`. Ask the delta review for the mutant the OLD test caught.
- **Run a delta review of a fold-in that touches product code**, in parallel with the rebuild. It caught the M-3 regression.

### Gen-44 lessons

- **A stand-in for an interpreter-exit crash must use the STANDARD stream.** A private `io.open(dup)` reader is never finalised, so it cannot crash; `sys.stdin.buffer` is. Read the original repro (`wp6.1\cell\t3e\stdin_parent.py:17`) before trusting a "deterministic" witness.
- **A fatal Python abort behaves differently in the Codex sandbox and at the seat.** In the sandbox it hangs (WER, no desktop); at the seat it exits 0xC0000005. Keep deliberate-crash shapes out of the gate, and run them in the sandbox only, with `SetErrorMode` suppression (CPython's `SuppressCrashReport`).
- **A brief's factual premise about third-party artefacts can be wrong** (6.3a: "none of the eleven wheels has a `.data`"; cupy has `cupy/.data/`). Ask the reviewer to check premises against the real artefacts (the uv cache, the venv's RECORDs), read-only.
- **Console `python.exe` updates the Win32 std handle on `dup2`; `pythonw.exe` and a windowed frozen exe do not.** A test of `SetStdHandle` must run under `pythonw.exe`.
- **Run Reviewer A in parallel with a cell turn that changes no product code** (DR-125 r1 beside the records turn; 6.3a r1 beside DR-125's fold-in). This saved about an hour.
- **Main moves under you** (CHARC commits often): read a merge's real second parent before citing it.
- **WP6.1's `proof4.py` / `headless.py` / `handler_check.py` re-target with a small path patch** (`wp-dr125\frozen\patch_paths.py`). `handler_check.py` takes its source paths as arguments. Keep the pack read-only in place.

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
