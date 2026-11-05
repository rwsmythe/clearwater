# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 49** (session `clearwater-orchestrator-20261105-0315`). LIVE 2026-11-05 13:16Z. Seat folder `work/orch-g49/` (`gate.sh`, `watch2.sh`, `crcheck.py`, `assemble.py` = the dispatch assembler: `uv run --no-sync python work/orch-g49/assemble.py <body> <cell>\dispatch-N.md`).
- (Gen 48 `clearwater-orchestrator-20261104-1821` rolled clean at ~13:15Z; its seat folder `work/orch-g48/` holds the licence scripts.)
- CHARC is **gen 16, `clearwater-charc-20261104-0738`**. Re-verify both names in `comms/.launch-sessions.json` before every cue.
- Seat folder `work/orch-g48/`:
  - `gate.sh`, `watch2.sh`, `crcheck.py`;
  - the drains, the posts, `dispatch-N-body.md`;
  - the licence scripts (`licence_*.py`, `scriptsd_*.py`, `zvbi_objects.py`).
  Copy `gate.sh` / `watch2.sh` with `sed 's#orch-g48#orch-g49#g'`.
- **Dispatch assembly:** the body carries `@@RULES@@`. A small Python joins it with the two rule lines from `git show HEAD:CLAUDE.md` (see any gen-48 command history: lines starting `**Desktop input rule` / `**Entry-point isolation rule`), asserts no CR / VT, and writes `cell\dispatch-N.md`. A FRESH prompt is the cell def + the brief at HEAD + dispatch-N with `tr -d '\r'`; a RESUMED prompt is dispatch-N alone.
- State worktree: `.worktrees/orch-state-g48`. The successor removes it and adds its own.
- **After the migration:** C: is 3.7 TB with 2.8 TB free (13:13Z). D: has 2.1 TB free. Every path is unchanged (repo root, footage, `D:\clearwater-archive`, `clearwater.local.toml`, worktrees). The STOP-below-15-GB rule still holds; disk is no longer the binding constraint.
- **Paces at 13:13Z:** Codex 7 % / 0.434 (resets 2026-11-11 10:07Z); Claude 61 % / 1.362 (resets 2026-11-09 10:00Z).
- Bash gauge at bring-up: 40 ms.

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
- **QUIT_SCRIPT exception (owner's word, CLAUDE.md `1a38c935`):** `tests/test_app_startup.py::test_python_m_clearwater_starts_the_shell_and_exits_0` runs at the SEAT in gate legs and seat re-runs only. Every cell run keeps `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
- **No `rm -rf` on a command-substituted path** (the safety check refuses it). Use fixed paths under `work/`, or leave the folder.
- **Running downloaded build scripts is refused** by the auto-mode classifier ("code from external"). Read them as text (gen 48's `scriptsd_static.py`).

### Live board (RESUME HERE)

**RUNNING at 13:45Z: WP6.3b turn 13** (FRESH Codex session, dispatch `cell\dispatch-13.md`: release.yml with the seat-resolved SHAs `seat\action-shas.md`, FFmpeg params read from the lock, `--zip` the one pending flag; checklist v2; guide s.2/3/6/7/8; limited root notices WITHOUT the FFmpeg row). Branch `wp6.3b` at **`52754527`** (turn 12). If this generation dies mid-turn, the successor waits for / inspects `turn-13.driver.stdout` and `return-13.md` before anything else.

1. **WP6.3b: the release workflow, bundled FFmpeg, notices, smoke and zip, checklist v2, guide.**
   - Brief `docs/briefs/wp6.3b-brief.md`, rulings tails Round-0 / Turn-3 / Turn-6 / Turn-9 (CHARC commits `e209734e`, `5fb828ba`, `2258e5ab`, `f7250307`).
   - Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.3b\` (`cell\` dispatch / prompt / return / turn files 1-11; `seat\`).

   **Turns and their commits** (driver turn numbers):

   | Turn | Commit | Content | Codex session and depth |
   | --- | --- | --- | --- |
   | t4 | `4e1da00e` | hook group A finish + group B (`--disable-windowed-traceback`, cache variables) | `01a1a9de`, retired at 197,556 |
   | t5 | `30cb8460` | `ffmpeg.lock.json` (98 components) + `--ffmpeg-from` | `01a1ab56` |
   | t6 | `817a31b2` | seat-verified licences in the lock (103 slots, zvbi the one `gpl3_compatible: "no"`) | `01a1ab56` |
   | t7 | `6c793073` | notices coverage planner + the FFmpeg refusal | `01a1ab56`, retired at 208,734 |
   | t8 | `4a2d2782` | report-only STOP on the seat's GPL-3.0 "once" wording; seat-clarified, CHARC concurred | `01a1ab9b` |
   | t9 | `3e97ae00` | the generator finished (rendering, provenance, writer, CLI, `build.py --notices`) | `01a1ab9b` |
   | t10 | `df1cd2e2` | `tools/package/native-licences/` (manifest + OpenSSL 3.5.5 Apache-2.0 text, sha256 `7d5450cb...`) | `01a1ab9b`, retired at 199,050 |
   | t11 | `efe88629` | `.gitattributes` `tools/package/native-licences/** -text` + 2 guard tests; the headless smoke (`tools/package/smoke.py`, `build.py --smoke`) | FRESH `01a1abc1-ffbe-7203-9291-e43fb62f4c74`, 155,874 |
   | t12 | `52754527` | every smoke row under a Windows Job Object (own CreateProcessW, suspended + PROC_THREAD_ATTRIBUTE_JOB_LIST, IsProcessInJob before resume; census = job process list; darwin fail-closed pending WP6.5); seat 479 passed / 1 skipped | `01a1abc1`, retired at 222,977 |

   **Turn 11's OPEN MAJOR: RULED (b) by CHARC (`1a8beb0d`), fixed in turn 12, CLOSED on the seat re-run (`work/orch-g49/seat63b-t12.log`).** WP6.5's brief must carry the native darwin containment (the branch refuses to run until then).

   **HELD (owner): the zvbi licence STOP.**
   - BtbN's win64-gpl-9.0 `ffmpeg.exe` carries zvbi's GPL-2.0-ONLY `src/pdc.*` / `src/packet-830.*` in a GPL-3.0 (`--enable-version3`) binary. Record `seat\licences-5031c6f1.md` section 3.
   - With the owner via CHARC. CHARC recommends (a) a self-build from BtbN's scripts at `5031c6f1` minus `50-zvbi.sh`, fallback (c) user-obtained FFmpeg like the GPU pack, never (b) accept the risk. The laptop's gyan.dev FULL build has the same combination.
   - **The ZIP and any release use of the bundle wait for this ruling.** The notices generator and the smoke are provider-independent: FFmpeg rows appear only when FFmpeg is carried, and the generator refuses a `"no"` row.

   **Seat records this generation** (`clearwater-review-evidence\wp6.3b\seat\`):
   - `scriptsd-5031c6f1.md` + `.tsv` (103 built stages, 98 pinned; static evaluation);
   - `licences-5031c6f1.md` + `.tsv` (every licence at its pin; 7 corrections; the zvbi STOP);
   - `native-licences-openssl.md` (OpenSSL tag `85a9a2ee` -> commit `67b5686b`, source sha256 `b28c9153...`).

   The data folders are `work\wp6.3b-seat\licences\` (per-component licence files), `licence-headers\`, `zvbi-hdr\`, `zvbi.git`, `native-licences\` and `btbn-5031c6f1\` (the unpacked build-scripts archive).

   **Remaining WP6.3b work, in order:**
   1. DONE (turn 12).
   2. **RUNNING as turn 13** (provider-agnostic; the root FFmpeg row and `--zip` wait on zvbi). Then the seat: `actionlint` on release.yml, check each action input against its pinned `action.yml`, register any new harness path. Its content:
      - `release.yml` with pinned action SHAs: round-0 candidates checkout v4.2.2, setup-uv v6.0.1, upload-artifact v4.6.2, download-artifact v4.3.0 and action-gh-release v2.3.2. **The SEAT resolves each to an immutable SHA by `gh api`**; the cell is offline.
      - The checklist items: the FFmpeg re-pin before about 2028-10; re-verify the native-licences manifest when uv's Python changes; the python-build-standalone `20260303` pin as a build input.
      - The root notices: the Python row (1.1.0 redistributes the interpreter natives) and the PyInstaller per-kind wording (run-time hooks Apache-2.0).
      - The guide: sections 2, 3 (the narrow grant), 6, 8; ADV-2 already done in turn 2.
   3. **Reviewer A (Claude), detached `.worktrees/wp6.3b-rA`** (EXISTS, at `df1cd2e2`: `git -C` it to the final head; it has no `.venv`). `codex_cell.py review` from the detached copy; ban `run_in_background` in the prompt. **CHARC's binding addition for the prompt:** sweep EVERY other hash-pinned or byte-compared text file outside `tests/fixtures/**` (the lock, the synthetic FFmpeg listings, any notices golden file) for the CRLF hazard, extending the attribute line where a fresh autocrlf checkout would change bytes. Also carry gen 48's note: `_configure_gpu_caches` imports `clearwater.config.paths` (and so NumPy) on the frozen `-m` and worker branches before `activate()`.
   4. **The seat build proof:**
      - a real `build.py --form onedir --ffmpeg-from ... --notices --smoke`, with the zip after zvbi;
      - the real built folder is the native census: every unknown binary named; libffi / SQLite / Tcl-Tk / MSVC runtime rows only if carried, each a seat fetch plus a manifest row;
      - the UIA window watch, the V4 check and the `hevc_nvenc` line on the bundled binary;
      - `actionlint` (`work\tools\actionlint-1.7.12\actionlint.exe`);
      - the notices read in full.
   5. Reviewer B (a full Claude pass at the seat), then the gate: two legs + harness + `mypy --platform darwin` + the module-alone `tests/test_gpu_pack_install.py`. Then the accept record and the ff.
   6. **CHARC's accept items:** AD-38 (the flag, hook, workflow, bundle rule, native-licences surface, the lazy-import limit); register rows (FFmpeg re-pin about 2028-10; the MinGW-runtime limitation; any native without a row); N13 for 1.1.0.
2. **WP6.5** (Mac validation): brief DRAFT `fea43245`, after 6.3b.
3. **Push:** main is ahead of `origin/main`. CHARC batches the owner's push.
4. **Worktrees:**
   - main;
   - `orch-state-g48` (remove it);
   - `wp6.3b` (live) and `wp6.3b-rA` (detached review copy);
   - `wp-dr125`, `wp6.1`, `wp6.2`, `wp6.3a`, `wp6.4` (kept for the prunes).
5. **Prunes owed (the owner's word only; CHARC batches):**
   - gen 47's list (`wp6.3a/work`, `wp6.3a-rA/work`, `wp-dr125/work/wp6.1` + frozen-runs, the `wp6.1` builds after 6.3b, `wp6.2`, `wp6.4/work`);
   - gen 48's own: `work/seat63b-t3..t11`, `work/rA-crlf*`, the `work/wp6.3b-seat/` licence data folders after the accept.

### Gen-48 lessons

- **A cell's own worktree hides CRLF hazards.** Codex writes new files with LF, and the system `core.autocrlf=true` (Git for Windows' etc/gitconfig) converts them only on a FRESH checkout. Test every byte-pinned file from a fresh detached checkout before trusting the cell's green.
- **Licence detectors over-match.** "(at your option) any later version" is in every GPL text's appendix, and "noncommercial" is in GPL-2 section 3(c). The project's own grant is in its source headers.
- **Debian-style `License: GPL-2` means GPL-2.0-only.** Read the per-file stanzas in `COPYING.md`.
- **A string scan of a stripped static binary cannot prove an object absent:** `vbi.c` showed 0 hits while certainly linked. Trace the call graph from a linked unit instead.
- **A Python print to a redirected file is block-buffered,** so a long script shows nothing until it exits. Add `flush=True` when you need progress.
- **The bare-`cd` slip recurred three times this generation** (each restored in the next call). Prefix with `cd /c/Users/rwsmy/clearwater &&` and use subshells for everything else.

### Earlier generations' lessons

They are in `git log -p -- docs/orchestrator-state.md` (gen 47's state at `26be709f`, gen 46's at `5b6d422f`). The binding ones are in the rules block above.
