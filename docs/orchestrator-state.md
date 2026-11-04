# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 43** (session `clearwater-orchestrator-20261104-0421`) LIVE 2026-11-04 14:21Z -> ROLLED at the 400K cap 2026-11-04 ~16:55Z, clean: nothing it started still running (see the board). CHARC = **gen 15 `clearwater-charc-20261104-0027`**; re-verify both names in `comms/.launch-sessions.json` before every cue. Seat folder `work/orch-g43/` (gate.sh WITH a `startup` leg, watch2.sh, run-2c/ the seat-run script copies, drains 1-5, posts). Bash gauge at bring-up: 37 ms. State worktree `.worktrees/orch-state-g43` (`git merge --ff-only main` before each edit; ff main to it after the commit; the successor removes it and adds its own).
- **Disk:** C: 77 GB free at 15:45Z. `df -h /c` before every window, gate and footage run. STOP below 15 GB free; 25 GB before any window or gate.
- **Paces at 14:22Z:** Codex 2 % / 0.792 (resets 2026-11-11 10:07Z); Claude 37 % / 1.187 (resets 2026-11-09 10:00Z). Re-read at the first dispatch.
- **CHARC subjects: under 100 characters.**

### BINDING RULES CARRIED (each verbatim in `comms/orchestrator/read/` or CLAUDE.md)

- **DESKTOP INPUT RULE and ENTRY-POINT ISOLATION RULE (CLAUDE.md hardware section).** Paste BOTH VERBATIM into EVERY dispatch (CHARC's order; the text is in `clearwater-review-evidence\wp6.1\cell\dispatch-14.md`). A cell-written GUI script is YIELDED to the seat UNRUN, reviewed (grep for SendKeys / AppActivate / SendInput / keybd_event / mouse_event / pyautogui / SetForegroundWindow; PID-tree filter; redirect; bounds) and RUN AT THE SEAT FROM md5-CHECKED COPIES.
- **ROLLOVER TIMING (OWNER-RULED, CHARC FYI `08c0b43b`).** Below the 400K cap a seat starts the next unit WHATEVER ITS SIZE; it rolls at the first clean boundary AFTER 400K with nothing it started still running. At or past the cap, dispatch nothing new. Owner (2026-11-03): "I do not want rollovers to happen until after 400k is hit. Once it is hit, rollovers should happen as soon as practicable."
- **NO ROLLOVER WHILE A JOB RUNS (OWNER, 2026-11-02, verbatim: "the generations should not have handed over if the previous generation was still working").** An Agent-tool cell and every background process die with the pane.
- **NO PYTEST DURING A SERIAL OR FULLCLIP LEG** or a window; one heavy job at a time. A light Codex / Claude turn beside an IMAGE batch is fine; nothing beside a serial leg, a fullclip leg or a timing window.
- **ONE CODEX CELL AT A TIME** (CLAUDE.md); a Codex REVIEWER pass (`codex exec -s read-only`) is not a cell and may run beside one.
- **Gates carry WP-T7's flags** and the STALL WATCH: `bash work/orch-g43/gate.sh <worktree> <run-id> <legs...>` (legs `static collect parallel serial startup fullclip harness`; `startup` = WP6.1's GATE_CHECKS serial start-up modules + its 3 owned modules; summary `work/orch-g43/gate-<run>/summary.txt`) + Monitor `bash work/orch-g43/watch2.sh <run-id> <summary line count before the start>` (30 min cap; re-arm).
- **Codex turns:** `uv run python scripts/codex_cell.py turn --worktree <ABS> --prompt <p> --evidence <dir> --turn N [--session <id>] > <dir>\turn-N.driver.stdout 2>&1` with **run_in_background**; commit with `codex_cell.py commit --worktree <ABS> --return-file <return-N.md>` (it stages new files itself); depth = the footer's `depth_input_tokens`; FRESH prompt = `.claude/agents/implementer-codex-sol-high.md` + the brief at HEAD + `dispatch-N.md`, joined, `tr -d '\r'`; a RESUMED session's prompt = `dispatch-N.md` alone.
- **Reviewer passes (Claude, for a Codex cell):** `uv run python scripts/codex_cell.py review --worktree <abs> --base <sha> --prompt <p> --out <dir> > <dir>\review.seat.log 2>&1` (background). Forms: A `clearwater-review-evidence\wp6.2\A\r1\review-prompt-r1.md` (text package); B `...\wp6.2\B\review-prompt-B.md`. Assert from the seat log's JSON line: model_ok, is_error false, the verdict line, worktree_clean_after.
- **Codex review of a Claude cell:** Reviewer A = a DETACHED review worktree `.worktrees/wp6.1-rA` at the head under review; from it (IN A SUBSHELL): `cat prompt diff | codex exec -p strong -s read-only --skip-git-repo-check -c 'windows.sandbox="unelevated"' - > review.out 2>&1`; the final answer = the lines after the LAST `^codex$` line up to `^hook: Stop$`. Forms `clearwater-review-evidence\wp6.1\A\r4\` / `r5\`. Reviewer B = the WSL script `clearwater-review-evidence\wp6.1\B\run_review_B.sh probe|review` (`MSYS_NO_PATHCONV=1 wsl.exe bash -ilc 'bash /mnt/c/.../run_review_B.sh review'`; assert `review.done` exit=0, 0 `^ERROR`, model gpt-6.1-sol / high, the VERDICT line).
- **Backslash-bearing Python helpers are written with the Write tool**, never a heredoc. **`rm` takes literal absolute paths.** A NEW file in a worktree must be `git -C <wt> add`ed before a pathspec commit. **Worktree release:** a released worktree's `work/` is pruned only on the owner's word.
- **A bare `cd` moves the session's cwd** (it carries between Bash calls, and a live Claude cell shares the process). ONLY `( cd X && ... )`, `git -C`, absolute paths. Gen 43 slipped THREE times (twice with a cell live).

### Live board (RESUME HERE) -- gen 43 ROLLED at the 400K cap: NOTHING RUNNING (no cell, no Codex turn, no reviewer, no gate, no GUI)

**Gen 44: first acts, in order.** (1) Read `comms/orchestrator/inbox`. (2) Re-read the paces. (3) **WP6.1's Reviewer B fold-in** (Codex turn 1, fresh session, `clearwater-review-evidence\wp6.1\cell\dispatch-15.md`, evidence `cell\codex-b\`): DONE and COMMITTED `7316b3ce` on `wp6.1` (fresh session `01a1a74f-bfb3-7880-a926-1c1927bcdd64`; depth 117,846 / 475,000 at turn-1 end; 330 passed in the sandbox with the mkdir shim; marker collection parallel 328 / serial 2; `src/` UNTOUCHED; 0 CR). Fill the ledger's `Depth at the B fold-in end: DISPATCHER TO FILL` with 117,846 (Codex input tokens, turn-1 end). **ALSO DONE before the roll:** the OWNER RULED (CHARC `c4b790e9`, verbatim "onedir; go; prune"): **CP6a = ONEDIR** for 1.1.0 (record it in the accept: on CHARC's recommendation; N14 figures are onedir's). **D6 hand check RAN** (onedir only, 16:11-16:51Z, the seat-run script md5 `0e05e8e7`): HEIC->PNG (6 EXIF entries), JPEG->PNG (3), `vfr.mp4`->MP4 all `ok; device GPU`, clean close exit 0, nothing left, owner-log md5 unchanged; record + outputs in `clearwater-review-evidence\wp6.1\d6\`. **The owner's WORDS on D6 come via CHARC**: put them in the accept record (only a D6 FAILURE reopens). **THE PRUNE IS YOURS (owner "prune")**: delete `.worktrees/wp6.1/work/wp6.1/cold-onedir-1..3` and `cold-onefile-1..3` (3.49 GiB) and `.worktrees/wp-t8`'s `work/`, then `git worktree remove .worktrees/wp-t8` (the branch stays); record `docs/proofs/prune-2026-11-04.md` (what, size, free before / after) or a section of the accept record; nothing else is pruned on this word (the `dist-on{dir,file}` builds stay until the accept). If the auto-mode classifier refuses the deletion, stage a guarded script and give the owner its `! bash` line. Post + cue CHARC when recorded.  (4) **The Claude review pass on that delta** at the seat: `codex_cell.py review --worktree C:\Users\rwsmy\clearwater\.worktrees\wp6.1 --base 68cc1f33 --prompt <p> --out clearwater-review-evidence\wp6.1\cell\codex-b\review-1` (write `<p>` from `wp6.2\A\r1\review-prompt-r1.md`'s form: the six B findings `B\review-B.txt` as the checklist, each fix + its test + mutation claim; `src/` must be untouched; tests isolated per CLAUDE.md; the `slow` marker on the wall-clock test). A finding = one more resumed Codex turn (`--session <id>` from turn-1's driver footer). (5) If `build.py` has a read-only bundle-check entry point, re-run it on both existing builds (`work\wp6.1\dist-on{dir,file}`, of `dc784b4f`) with the new checker; else say so (CHARC: the gate's test of the checker then stands). (6) **THE GATE** on the package head: `df -h /c`; `bash work/orch-g43/gate.sh wp6.1 p61 static collect parallel startup harness` (background) + the watch2 Monitor. Then `git diff --name-only main...wp6.1` = the owned paths (`src/clearwater/__main__.py`, `gpu_pack.py`, `app/composition.py`, the 3 test modules, `tools/package/build.py` + `README.md`, the ledger, the report, `pyproject.toml` + `uv.lock` (N13 pin)); 0 CR on every changed blob; the real `%LOCALAPPDATA%\Clearwater` ABSENT during the gate (checked 16:0xZ: absent). (7) **THE ACCEPT** (CHARC PRE-RULED `c85d332f`: proceed with D6 and CP6a recorded as "PENDING owner"; do NOT hold or ask again; only a D6 FAILURE reopens): fill the ledger's open `DISPATCHER TO FILL` depth lines (turn-4 report: wp61-cell9 at its final report 277,694 + the B fold-in Codex depth); if main moved, `git -C .worktrees/wp6.1 merge --no-ff main` and re-run the harness leg; write `docs/proofs/wp6.1-accept.md` (form `docs/proofs/wp-t8-accept.md`: nets A r1-r5 + B with verdicts and evidence paths, the gate summary, the GUI check + timings, D6 + CP6a PENDING owner with the step list (ledger "The owner's hand check (D6)") and the CP6a table (report section 1), DR-125 occurrences, the prunes owed); commit it on `wp6.1`; ff main; post the accept to CHARC (it writes AD-33 / AD-34 / N13 row / N14 figures and the DR-125 brief).

1. **WP6.1, packaging spike**: CODE FINAL at `dc784b4f`; report `68cc1f33` (form-neutral, CHARC `85e45a92`). Worktree `.worktrees/wp6.1`, branch `wp6.1`; ledger `docs/proofs/wp6.1-ledger.md`; evidence `clearwater-review-evidence\wp6.1\` (`cell\dispatch-1..12, 14, 15` (13 was an inline message), `t3f`..`t3i`, `codex-b`; `A\r1..r5`; `B\`; `timings\t4\`).
   - Gen 43's record: main merged into wp6.1 `49150ccf`; wp61-cell7 2b-4 one rebuild + WITH-pack proof PASS (`fa32af1f`) + r4 fold (`08a96243`, `09cbba2c`), retired 371,271; wp61-cell8 2b-6 re-proof PASS (`e9dfe81f`) + 2c-a r5 fold (`dc784b4f`) + scripts, retired 321,383; the SEAT ran the GUI check (PASS) and the exclusive timings (COMPLETE) from md5-checked copies (`1c35a01f`); wp61-cell9 the report (`865e12ee` + form-neutral `68cc1f33`), retired 277,694.
   - Nets: Reviewer A (Codex at the seat) r4 1 MAJOR (grammar) -> folded; **r5 NO_NEW_CRITICAL_MAJOR (converged)**; **Reviewer B (WSL Codex, on `dc784b4f`) NO_NEW_CRITICAL_MAJOR**, 4 minor + 2 adv -> the Codex fold-in above. Harness 423 OK on `68cc1f33`.
   - CHARC rulings this gen: `bae5dba5` (proof accepted as evidenced; canary not-found correct; header lookup INFERRED, three legs; fail-closed shim; A r4 dispositions + the grammar version pin); `cdc4b279` (DR-125 occurrence recorded; report line on DR-125); `85e45a92` (report form-neutral; CP6a presented to the owner, CHARC recommends onedir; D6 offered); `c85d332f` (fix all six B findings before the gate; #1's test plants a GPU-named option and expects FAIL; PRE-RULING: accept may proceed with D6 / CP6a PENDING owner).
   - **D6 owner hand check, on the owner's go (via CHARC or chat):** from the wp6.1 worktree root, `( cd C:/Users/rwsmy/clearwater/.worktrees/wp6.1 && .venv/Scripts/python.exe -B C:/Users/rwsmy/clearwater-review-evidence/wp6.1/cell/t3i/seat-run/gui_check.py owner --form onedir )` then `--form onefile` (md5 `0e05e8e7171f73c74ece4715f87a75eb`; it refuses an existing `work\wp6.1\t3i\hand\<form>\`; it needs `handler-check-t3i.json` newer than the dists, which holds while the dists are not rebuilt). Copy the staged outputs into evidence; the owner's words are the evidence.
   - Owner-log md5 `69ed0432c562db9445daecbe8f15fe27` (a check only, never repaired). Prunes on the owner's word only: cold copies 3.49 GiB `work\wp6.1\cold-*`; `.worktrees/wp-t8`'s `work/`; later the wp6.1 worktree's builds and the hand-filled pack.
2. **DR-125** (export worker crash at exit; the F-E stdin isolation moves into the worker and the `__main__` shim is removed; fail-closed inherited): CHARC writes the brief after WP6.1's accept (Codex lane). Occurrences: 1 of 12 frozen worker runs (2b-4 + 2b-6), 0 of 12 in the timing window.
3. **Push:** main ahead of `origin/main`; a push needs the owner's word.
4. **Worktrees:** main; `orch-state-g43` (the successor removes it, adds its own); `wp6.1` (live package); `wp6.1-rA` (detached at `926bfdfa`, Reviewer A's copy; release after the accept); `wp-t8` (released; `work/` kept for the owner's prune word); `wp6.2` (released, kept for the prune).

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
