# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 21 ROLLED OVER 2026-10-29 ~17:05Z at ~380K, at a clean boundary.** WP4.3 cell 5 yielded at its R3 verdict, was stood down, and dies with this generation. The WP4.3a Codex seat-2 session survives; its turn 5 finished and is committed (`a0b9235`).
  - Session `clearwater-orchestrator-20261029-0425`. CHARC is gen 7, `clearwater-charc-20261029-0428` (re-verify: `comms/.launch-sessions.json`).
  - Bash-launch gauge 33 ms at bring-up; free memory ~9-10 GB.
  - **RESUME HERE (gen 22):**
    - **Phase 4 state** (re-verify: `git log --oneline -15 main`, `docs/debt-register.md`): **WP-T6 ACCEPTED** (main `fe65e6a`; CHARC QA CONFIRMED, accept edits `c5c194e`: GATE_CHECKS now carry `and not fullclip`, DR-86/87/88). Two packages IN FLIGHT: **WP4.3** (Claude, opus-high) and **WP4.3a** (Codex). **Queued:** the DR-87 `bench.py:1305` `stray_processes` Codex micro-package, BEHIND WP4.3a (CHARC). WP4.3's gate waits on WP4.3a's DR-85 fix being on main (the strict `xfail`), so WP4.3a merges first; the other rebases with patch-id re-proved.
    - **Standing rule (recipe `e831448`):** every BUILD dispatch names a yield after each task GROUP. It worked all generation: cells 4 and 5 yielded every group on time.
    - **Gate expressions (fill, from `c5c194e`):** PARALLEL `-n 4 -m "not gpu and not footage and not gui and not slow and not fullclip"`; SERIAL `-m "(gpu or footage or gui or slow) and not fullclip"`. Serial leg about 1,389 s, two-leg about 35 min. Gen 21's WP-T6 gate script is the template: `clearwater-review-evidence\wp-t6\work-copy\mc\gate-g1.sh`. It runs static checks, four collections and parallel, then waits on a `serial.go` file so the timed serial leg runs only with every cell verified idle.
  - **CHARC's rulings on BOTH open queries are WAITING UNREAD in the orchestrator inbox** (cue at ~17:08Z, message `d41f80f6`; gen 21 did not drain it). In CHARC's cue: R3-1 fixed in BOTH `app/startup.py` and, under a granted WP4.3a scope addition, `settings_store`'s per-field default; R3-2 fixed by the (id, folder) pair and reclassified MINOR; R3-3..R3-5 test-only; WP4.3a F1 fixed at the real resolve site; F4 GRANTED. Read the post itself for the binding text, save it verbatim to both evidence folders, and carry it into cell 6's prompt and WP4.3a's `prompt-6.md`.
  - **WP4.3 (application wiring), Claude lane `implementer-opus-high`, Codex nets (WSL `gpt-6.1-sol`/high):**
    - **Brief and rulings:** brief `docs/briefs/wp4.3-brief.md` FINAL. Rulings, all verbatim in the ledger `docs/proofs/wp4.3-ledger.md` and saved in `clearwater-review-evidence\wp4.3\`:
      - `fcb2a920` (round 0) and `68d5b4c7` (build);
      - `d530b564` (R1; major 2 REVERSED to fail-readably);
      - `ace08fbb` (R1-13 = (a) on AD-11's domain clause, three conditions; the D85 missing-folder Limit with DR-89);
      - `38a7c702` (R2; R2-3 GRANT narrow for `gui/settings_dialog.py`, one closed signal; R2-4 BANKED DR-90).
    - **Worktree and cells:** `.worktrees/wp4.3`, branch `wp4.3`, base `038f02e`, **head `21ba03f`** (ledger only since `028bc4f`).
      - cells 1-3 as in gen 20's state;
      - cell 4 did the R1 remediation (Groups A-C) and R2, stood down at 355,066;
      - cell 5 did the R2 remediation (Groups A-C) and **R3**, stood down at 271,612 (its R3 yield).
    - **R3 = `NEW_CRITICAL_MAJOR_FOUND`, 0 / 2 MAJOR / 3 minor, all in-envelope** (evidence `wp4.3\r3\`, review `21392d76`, adjudication `abf49f67`). This is **round 3 of the five-round gate**. POSTED to CHARC by gen 21 (query `4e934f90`, with the WP4.3a F4 grant); gen 22 drains the answer.
      - **R3-1 MAJOR:** a `settings.json` `output_folder` containing NUL is accepted by `load_settings`, then start-up's `clean_leftovers` raises `ValueError` before `show()`, so the program cannot start. The cell proposes skip-and-log in `app/startup.py` for any folder `_is_path` refuses. **FLAG:** the settings store accepts the NUL path at its source (`config/`, WP4.3a's file set). Ask CHARC whether WP4.3a (in flight, same files) also refuses it at the source.
      - **R3-2 MAJOR:** two journal entries with one id (only a foreign or hand-edited journal; real ids are uuid4); a failed clean-up of one folder then drops both. The proposed fix removes entries by the (id, folder) pair. CHARC may reclassify to minor under the DR-89 class.
      - **R3-3 and R3-4 (minor, REOPENED R1-12):** the V7 (e) and (b) witnesses. Test-only.
      - **R3-5 (minor):** the DR-44 (c) close test's predicates; test-only plus the report sentence at `:100`.
    - **NEXT:**
      1. Drain CHARC's answer to `4e934f90` (R3 dispositions; R3-1's source-side refusal possibly added to WP4.3a's scope).
      2. **Fresh cell 6** (opus-high) from the ledger and `r3\adjudication.md`. Base the prompt on `clearwater-review-evidence\wp4.3\prompt-wp4.3-cell5.md`: READ FIRST tight; the CHARC R3 ruling verbatim; Group A (R3-1, R3-2), then Group B (R3-3..R3-5), each a yield; then **R4** review only (`wp4.3\r4\`, "THIS IS ROUND 4"), yield at the verdict.
      3. After A converges: the windows (V7 (a)-(f) of record; the GX011627 V18/V8 leg with p99 at k=2 ASSERTED, per `ace08fbb`; DR-44 (c)/DR-50 on footage), EXCLUSIVE, each posted to CHARC.
      4. My Reviewer B (Codex, WSL runner `clearwater-review-evidence\wp4.2\reviewB2\run_review_B.sh` shape).
      5. The ONE gate under the amended expressions, after WP4.3a is on main. Rebase WP4.3 and drop the DR-85 `xfail(strict)`.
      6. The accept record carries the AD-11 domain sentence (`ace08fbb` condition 3), DR-89 and DR-90 (CHARC's rows).
    - **Cell depths this generation** (`cell_depth.py`, each at a yield): cell 4 140,559 / 219,999 / 316,716 / 355,066 (A / B / C / R2); cell 5 108,533 / 168,297 / 222,999 / 271,612 (A / B / C / R3). An R round costs a cell about 40-50K.
  - **WP4.3a (spawn helper and import / redaction hardening), Codex lane, Claude pass as both nets, STRONG:**
    - **Brief and rulings:** brief `docs/briefs/wp4.3a-brief.md` FINAL on `8fb519ba` (main `e879106`). B4 ruling `a2ef868a` (saved `clearwater-review-evidence\wp4.3a\b4-ruling-b6aa800a.md`, verbatim in the ledger): GRANT a narrow edit of `tests/test_headless_export.py::test_b4_...` plus the runner's redacting WARNING handler.
    - **Worktree:** `.worktrees/wp4.3a`, branch `wp4.3a`, base main `fe65e6a`, head `a0b9235`.
      - Commits: `a614160` round 0; `ef903e5` the spawn helper; `fa2afab` tasks 4-5 (B4 red by design); `553d1f2` the B4 grant and the WARNING handler; `a0b9235` seat 2's R1 ledger.
      - I commit every turn by pathspec with the GPT-6.1 Sol footer.
    - **Seat 1** (session `01a18856-955d-74e3-b211-dfb519efdf0c`) RETIRED at input depth 237,170 of 258,400 (turn 4 footer).
    - **Seat QA at my seat on `553d1f2`:** ruff / format 269 / mypy 141 clean; task 6's full light-run list (`io/video` with GPU and slow, config, runner, naming, layering) **884 passed, 12 footage deselected** (`work/wp4.3a/seat-t6.log`).
    - **Reviewer A R1** (the Claude pass, `codex_cell.py review` with the ABSOLUTE worktree path; evidence `wp4.3a\r1\`, md5s in `md5sums.txt`) = **`NEW_CRITICAL_MAJOR_FOUND`: 1 MAJOR / 2 minor / 6 advisory.**
      - F1: DR-81 (b)'s real route, `Path.resolve` in `write_target_refusal`, is outside the new guard, and the test planted the raise elsewhere.
      - F2: the AST guard sees only run/Popen.
      - F3: stale report lines.
      - F4: the `--parameters` help line `:1203` is OUTSIDE the file grant. **One-line grant ASKED of CHARC in gen 21's query `4e934f90` (recommended: grant).**
      - F5-F9: REPORT-ONLY, or F9 a one-liner.
    - **Seat 2** = Codex session **`01a18899-4b87-7f51-8850-3b34a92b7076`** (fresh; prompt `clearwater-review-evidence\wp4.3a\cell\prompt-s2-1.md`). **Turn 5 (ledger turn 5) DONE and committed** (`a0b9235`, ledger only): R1 adjudicated, 9 NEW / 0 REOPENED; FIX F1, F2, F3, F9; REPORT-ONLY F4-F8 (F4 = the `:1203` help line, pending CHARC's one-line grant, asked in gen 21's query `4e934f90`). Depth: turn 5 `tokens used` 89,765; input depth 86,848 of 258,400.
      - **NEXT:** write `prompt-6.md`: the depth row, CHARC's F4 answer, and the R1 remediation (F1 with the test raising from the REAL `Path.resolve` route plus the NUL `ValueError`; F2's widened AST guard pinned at seven sites with planted forms; F3 report fixes and F8's line; F9 one-liner), RED first, one yield. Then run it with `codex_cell.py turn --worktree "C:/Users/rwsmy/clearwater/.worktrees/wp4.3a" ... --turn 6 --session 01a18899-4b87-7f51-8850-3b34a92b7076` (use the id above), commit, QA, then R2 at my seat (evidence folder wp4.3a/r2 under clearwater-review-evidence, with a "THIS IS ROUND 2" section).
      - A first Codex turn needs an ABSOLUTE `--worktree`: with a relative path, `codex exec -C` resolves it against the worktree cwd and fails (gen 21 lost one launch to this).
    - **After A converges:** Reviewer B (the Claude pass, process, neutral prompt), the ONE gate (`gate-g1.sh` template), the accept. CHARC closes DR-58 (b), DR-76, DR-77, DR-81 (a)(b)(c) and DR-85 and writes the AD-13/AD-23 notes. DR-81's closure text also gets the pre-existing WARNING route.
  - **Gen-21 slips (reported to CHARC):**
    - two bare `cd`s into `.worktrees/wp-t6` (no cell live);
    - one into `.worktrees/wp4.3a` with WP4.3 cell 5 live (it uses absolute paths);
    - each reverted in the next call.
    - Also one relative `--worktree` on a first Codex turn (no harm; re-run).
  - **Practice confirmed this generation:**
    - Holding a gate's SERIAL leg behind a go-file until every live cell is verified idle (two depth readings across a turn boundary) keeps the timed leg exclusive while the parallel leg overlaps light work.
    - A Codex cell close to its cap: do the task-6 light runs at YOUR seat, so the next seat starts at the reviewer.
    - Codex `context_window` footers print 475,000; the window of record stays 258,400.
  - **Worktrees:** live `wp4.3`, `wp4.3a`, `orch-state-g21` (this commit). Removed: `wp-t6`, `wp-t6-mc` (logs copied to `clearwater-review-evidence\wp-t6\work-copy\`; branches `wp-t6`, `wp-t6-mc`, `wp-t6-mc-gated` kept). `wp4.3-rev` is removable.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to
  charc` (type query, recommended answer first, one cross-session cue after posting). CHARC answers in the
  operator's stead except plan s.3 owner-reserved items. Info-updates (`--type fyi`) to the operator after each
  accept. No AskUserQuestion from this seat.
- **RESUMED 2026-10-26** at the owner's word ("resume", relayed by CHARC `064e23c84876bdfd`) after the 2026-10-21 pause.
- **Owner word 2026-10-20:** spec **v0.5.4**, plan v1.2, architecture FINAL 1.0, interim N6 = 25 min/min (D106),
  gain caps KEPT (D100). Owner-pending list (CHARC carries it): photos (WP3.6P), an iPhone clip (DR-15's B-frame
  leg), the V3 ratio figures as information for CP5/WP4.2 (now also in the WP3.11 record).
- **GoPro IMU and GPS are OUT OF SCOPE**: nothing from a `gpmd` track, IMU or GPS is ever COMMITTED (the owner's rule;
  CHARC `b238bd27`: a byte hash in an uncommitted `work\` record is within it, kept out of evidence copies too); no product
  module decodes or parses `gpmd`; GPMF settings only from `moov/udta` (FMWR/PRTN/PTCL). Location tags never reach a
  committed record (WP3.10 R1 #2).
- **Cell depth:** read `uv run python scripts/cell_depth.py <cell>` at dispatch, every yield, before any ruling;
  ~250K evaluation, ~400K STOP. Opus cells re-grounding from a ledger with a TIGHT reading list started at 0 and
  reached 90-120K by their first yield this generation (much less than wave 3's 140-220K).
- **Kernel hazard (7)** (CHARC, 2026-10-21): never an uncommitted edit in the MAIN tree's working copy. Every edit --
  briefs, state, records, contract amendments -- in a worktree on its own branch, then `git merge --ff-only`.
- **Line endings (CHARC, 2026-10-26: "keep that blob check in the gate recipe for every accept"):** every committed
  blob is LF (main has 0 CR bytes everywhere, the debt register included). At every gate: for each file in
  `git diff --name-only <base>..<cand>`, `git cat-file -p <cand>:<f> | tr -cd '\r' | wc -c` must be 0.

### Live cells and RESUME HERE (written by gen 13 at its rollover; gen 14 starts here)

Base of the wave: main `9753b7b`; main now `528d865`+ (CHARC's sandbox shim `542bc11`). Pace at dispatch: Codex 1.71, Claude
2.115. **Claude cells died with gen 13; Codex SESSIONS survive** (resume with `codex_cell.py turn --session <id>`).

| Package | State at rollover | Branch head | Next action (gen 14) |
|---|---|---|---|
| WP-T3 (sonnet; calibration) | DONE by the cell (`wpt3-cell1` retired at 159,635). A converged R1 (0 blocking; 2 minors fixed in cleanup). | `wp-t3` `296eb18`; candidate `wp-t3-mc` `0fbbe44` on `528d865`, patch-id `e38fa930` = author | Candidate full pytest: DONE at gen 13: 4867 passed, 2 skipped, EXIT=0 (07:02:45Z-07:50:41Z, 2873.78 s, host shared with light cells; log .worktrees/wp-t3-mc/work/pt-full.log). Static gates on the candidate clean (ruff, format 227, mypy 132). NEXT: Reviewer B (Codex `gpt-6.1-sol`/high): prompt, diff and runner STAGED in `clearwater-review-evidence\wp-t3\reviewB\`, probe PASSED (banner gpt-6.1-sol/high, 1 succeeded in). Run `MSYS_NO_PATHCONV=1 wsl.exe bash -ilc 'bash /mnt/c/Users/rwsmy/clearwater-review-evidence/wp-t3/reviewB/run_review_B.sh review'` (>= 5 GB free, nothing heavy). Then harness gate, accept record, ff main, debt rows (DR-33 (a)-(d) close; Q3 MINOR DR row for UTF-16/compressed-iTXt XMP), release post to CHARC, operator FYI. |
| WP3.20R (Codex; calibration) | BUILD DONE: 6 turns (tokens 64,199 / 92,340 / 111,584 / 131,507 / 149,041 / 204,598). A R1 (Claude opus/high, `wp3.20r\r1\`, md5s) NO_NEW_CRITICAL_MAJOR, 3 minor + 3 advisory; turn 6 cleanup: 1,3,5 fixed, 2 one-line fix, 4 declined, 6 banked (origin `54e2749`). Final return report = `cell\return-6.md`. | `wp3.20r` `32d30dc` on base `528d865` | Candidate `wp3.20r-mc` on main, patch-id, full pytest (FULL: shared GUI module), then the HEAD-TO-HEAD B: Claude B of record (`codex_cell.py review --base <main> --out ...\wp3.20r\reviewB\`, prompt built neutrally from the brief, NOT from r1's) AND a Codex B (`gpt-6.1-sol`/high, WSL runner as WP-T3's) on the same tree; table both. HD-1 calibration figures: test counts from the report, the six token figures, Claude review cost. Session id `01a17c14-71f3-7dd1-9c62-766a10c9c8cf`. |
| WP3.14 (opus) | Cell 1 retired at 238,362 (R0 + engine); cell 2 (`wp314-cell2`) retired with gen 13 at ~208K+, IDLE at a yield: build items 1-3 DONE, waiting for WINDOWS. Rulings O1-O4 + ORDER in the ledger; O1 UPHELD by CHARC. | `wp3.14` `7bb5d85` (base `9753b7b`) | Re-dispatch cell 3 (opus-high) from `prompt-wp3.14-cell2.md` + the ledger's RESUME HERE (cell 2's status). Window queue CONFIRMED to the cell: (1) footage `uv run pytest tests/test_jobs_export_video.py -m footage` (GX011627 V4 leg); (2) full `uv run pytest -m "not footage"` offscreen (5.3K leg inside); (3) Reviewer A R1 (Codex gpt-6.1-sol/high). V16 rows later, EXCLUSIVE, OPEN/CLOSE to CHARC. |
| WP-T4 (Codex by pace) | Turns 1-3 committed (`cd4697e` lock via orchestrator `uv lock`; `0fa0757` guard cases (w1)-(w4), 60 passed unshimmed at this seat; `28af9ba` cold-cache race REPRODUCED + lock + two-process test). Tokens 73,551 / 119,645 / 220,811 (past 250K soon: evaluate; bounded steps continue). | `wp-t4` `28af9ba` on base `528d865` | Pending RUN REQUEST (turn 3, `cell\return-3.md`): `powershell -NoProfile -File work/wp-t4/run_parallel_01.ps1` in the worktree (READ the wrapper and `monitor_pytest.py` first), in a window; hand the log paths back in turn 4 (rung 3.3 classification). Session id `01a17c16-3707-7e30-b81b-ecb9320feb6b`. Fence: `tests/fixture_plugin.py` -- WP-T3 `verify_generated`, WP-T4 imports + `SampleProvider`; merge WP-T3 first. |

- **Host queue (one heavy job at a time):** WP-T3 suite (running at rollover in gen 13's shell; if it died, rerun
  `( cd .worktrees/wp-t3-mc && QT_QPA_PLATFORM=offscreen uv run pytest -q -rs -p no:cacheprovider --basetemp=work/pt-mc )`)
  -> WP-T3 B -> WP3.14 footage -> WP3.14 full -> WP-T4 PARALLEL leg 1 -> WP3.20R candidate full + B pair. Reorder freely.
- **Codex-lane practice (gen 13):** every turn = `codex_cell.py turn` in the background, then `codex_cell.py commit`
  (check CR bytes; run `ruff format --check .` at THIS seat: the sandbox's exit 101 is an artifact); the cell never
  sees a tool result you do not paste into the next prompt. Prompts live in `clearwater-review-evidence\<arc>\cell\prompt-N.md`.
  Sandbox pytest form: `PYTHONPATH=scripts ... -p sandbox_mkdir_shim -p no:cacheprovider` (CHARC `542bc11`). A sandbox
  cannot reach the package index (`uv lock` is a RUN REQUEST). Delete the stray `work/sandbox/` copies at teardown.
- **Gen-13 slips:** four bare `cd`s (twice with cells live), each reverted next call. Put EVERY worktree command in a
  `( cd <wt> && ... )` subshell; never start a command line with `cd <wt>`.

### Where things stand (gen 12)

1. **WP3.10 ACCEPTED at main `47bc6d6`** (2026-10-27; one ff of `wp3.10-acc` `831fb8d` on main `ceec6b9`; record
   `docs/proofs/wp3.10-accept.md`). Candidate `wp3.10-mc` `7f98848` full pytest 4766 passed / 2 skipped (2715 s) = main's
   figure by code identity; harness 379 OK; mypy 132 clean. AD-12 RULED (cq 22/26/30, crf 21/26/30, 0.24 FINAL;
   `759f0d0`); floor row 0.155 s/frame NVENC 4K, fits D106. B pass 1 blocked (completeness) -> seat-9 remediation; B pass 2
   blocked (a regression: truncated B-frame refusal, EXECUTED at this seat) ADJUDICATED AT THE GATE, CHARC UPHELD
   (`b4e4a184`), gate fix `39bc9ac`. Release post 05:37Z (owed rows listed there); operator FYI posted. **CHARC QA pending.**
2. **Tranche B ACCEPTED at main `d31dd0f`** (WP3.17-3.20); CHARC QA CONFIRMED (static half); DR-49..DR-52.
3. **Harness changes landed (CHARC, owner-directed, 2026-10-27):**
   - **Dual-model implementer lane** (`3c230e4`; design `docs/proofs/harness-dual-model-implementers.md`): Codex cell
     `implementer-codex-sol-high` driven by `scripts/codex_cell.py`; the reviewer is always the OTHER model. **At the wave 4
     briefs name the first two Sonnet-class packages (well-specified, no frozen interface, comparable size) as the
     CALIBRATION pair**; CHARC assigns one to `implementer-sonnet-high`, one to the Codex cell. A Codex-implemented package
     gets a Claude Reviewer A and a Claude Reviewer B run by you as a `claude -p` PROCESS (pinned invocation in the fill;
     never improvise it). Dispatch tiebreak on weekly PACE (`scripts/usage_codex.py`, `scripts/usage_claude.py`), both
     readings in the dispatch row.
   - **Reviewer B pin moved** (`fac53e9`): `gpt-6.1-sol` / high (fast `gpt-6-luna` / medium). Banner assertion value
     `model: gpt-6.1-sol` from 2026-10-27; a `gpt-5.6-sol` transcript now FAILS assertion 1. WP3.10's two passes stand.
4. **WP3.10 CHARC QA CONFIRMED (static) at `47bc6d6`; WAVE 3 COMPLETE** (`d834993`: DR-17/18/26 closed, DR-20 (4)(6),
   DR-39 (a); DR-56..DR-58 new; the fill's GATE_CHECKS now copy `clearwater.local.toml` into gate worktrees).
5. **WAVE 4 RULED (CHARC gen 4 `clearwater-charc-20261026-2007`, msg `6f725eee`, saved at
   `clearwater-review-evidence\wave4-ruling-6f725eee.md`). GRANTS:**
   - **WP3.14 export jobs and batch -> `implementer-opus-high`** (Claude lane; Reviewer A and B = Codex `gpt-6.1-sol`/high).
     Dispatch FIRST. Its brief carries the ruling's item-3 list. V16 export timing row EXCLUSIVE, OPEN/CLOSE to CHARC.
   - **WP3.20R settings dialog hardening (DR-53, DR-54, DR-55) -> `implementer-codex-sol-high`** (Codex lane; Reviewer A
     and B = the Claude pass `scripts/codex_cell.py review`, opus/high; B is YOUR process). DR-54 RULED: refuse OK with a
     `settings`-owned message; the injected-rule test uses a DISAGREEING rule and asserts the 10-bit state. You commit each
     turn from the FILES CHANGED block with `Co-Authored-By: GPT-6.1 Sol via Codex <noreply@openai.com>`. At its gate the
     LANE HEAD-TO-HEAD is owed: run BOTH a Codex B (`gpt-6.1-sol`) and the Claude B on the same tree; the Claude pass is the
     B of record.
   - **WP-T3 fixture checker hardening (DR-33 (a)-(d)) -> `implementer-sonnet-high`** (Claude lane; Reviewer B = Codex
     `gpt-6.1-sol`/high; the ruling's "Reviewer A = Claude" wording contradicts the other-model rule -- raised to CHARC via
     the brief's questions). NO regeneration: the committed fixtures stay byte-identical.
   - The pair is CALIBRATION (pass 4.3): the pace tiebreak is suspended for the two; one Codex turn and one Claude cell may
     run together; one heavy job at a time rules the suites. Size ratio (WP-T3 ~1.3-1.5x WP3.20R) goes in HD-1.
   - **WP3.21 opens AFTER WP3.14's accept**; its brief MAY be drafted while WP3.14 runs (cite AD-21, the plan row, WP3.10's
     floor figures; measurement rows EXCLUSIVE, last).
   - **WP-T4 parallel test workers COMMISSIONED** (owner "commission it"; CHARC `f0741947`, saved at
     `clearwater-review-evidence\wpt4-commission-f0741947.md`; AD-28 on main `e2b471d`): Sonnet-class, dispatched THIRD after
     the pair, lane by the pace tiebreak (R3) at dispatch with both readouts in the dispatch row; reviewer = the other model.
     At its accept the fill's GATE_CHECKS suite line becomes the two-leg command (you write it from its report).
   - **Spec is v0.5.5** (`a5f9245`, D75 erratum, text only); every wave 4 brief cites v0.5.5.
   - **DONE by gen 13:** CHARC FINAL `3c3c35d7e40b525e`; briefs FINAL at main `9753b7b`; all four dispatched (Live
     cells above). WP3.21's brief may be drafted while WP3.14 runs.
   - (gen 12's resume text, superseded:) FOUR briefs DRAFT on branch `wave4-briefs` `b7764c5` (worktree `.worktrees/wave4-briefs`;
     author branches `brief-wp3.14`, `brief-wp3.20r`, `brief-wpt3`, `brief-wpt4`), posted to CHARC 06:28Z (`9ea33cc0` file),
     FINAL pending. Then: (1) apply CHARC's FINAL edits on `wave4-briefs` (a FINAL commit as wave 3's `0f51822`), ff main;
     (2) dispatch WP3.14 (opus-high) FIRST; (3) the pair: WP3.20R via `scripts/codex_cell.py turn` (Codex cell; you commit
     each turn from FILES CHANGED with the GPT-6.1 Sol footer) and WP-T3 (sonnet-high subagent); (4) WP-T4 third, by the
     pace tiebreak (`scripts/usage_codex.py`, `scripts/usage_claude.py`). Gen 12 disagreed with the WP-T4 helper's Q6
     (a FAST "Claude Sonnet medium" reviewer): the fill's pinned Claude pass is opus/high; follow CHARC's FINAL.
     Write each dispatch prompt in your scratchpad; cell depth read at every yield. WP3.21's brief may be drafted while
     WP3.14 runs (CHARC ruling item 1).
   - FYI: the owner asked CHARC about pytest-xdist; do NOT add it unless commissioned.
6. **Gen-12 slips:** five bare `cd`s moved the shared cwd (into `.worktrees/stackB`, `orch-state-g12`, `wp3.10-mc` twice,
   `subagents`); each reverted in the next call. Use `git -C <wt>` and absolute paths; a worktree command that must run
   inside it goes in a `( cd <wt> && ... )` subshell, never `cd <wt> && ...` at top level.

### (older) Where things stood at the gen-10 handover


1. **Gen 10 did, in order:** picked up under the pause; RESUME (`064e23c84876bdfd`); rebased `wp3.10` onto main
   (union conflicts in the probe-rules module set and `io/video/__init__.py`); WP3.4 seat 4 first with its EXCLUSIVE
   window (CPU-subsample STOP ruled no, CHARC upheld); WP3.10 seats 4-6 and WP3.11 seats 2-3 in parallel; **WP3.4
   ACCEPTED** (main `ad15ab4`; CHARC QA static half CONFIRMED `d3c7ebcf9749a876`, register rows `6b58619`); **WP3.11
   ACCEPTED** (main `47235b6`; CHARC QA pending).
2. **OWED ON MAIN `47235b6`: a full pytest.** The stacked candidate `f1c1bd8` ran CuPy 4200 passed / 2 skipped; its
   no-CuPy leg was STOPPED by Claude Code's low-memory reaper (not restarted, per the reaper's rule; the brief needs
   none). Main's code = `f1c1bd8`'s. I asked CHARC to let its QA suite on main stand as main's figure; if CHARC asks
   you instead, run it (offscreen, background, >= 5 GB free, nothing else heavy).
3. **Rulings this generation (in records/ledgers):** CPU subsample is evidence, not D106's STOP (WP3.4; CHARC upheld);
   Reviewer B dtype finding taken as a remediation (CHARC: RIGHT); WP3.11 B2 second blocking pass adjudicated at the
   gate (signed-zero fixed and verified by execution; two cancel races as limits, DR-47) -- CHARC to look; WP3.10
   five-round gate continue (tool code is result-bearing); WP3.10 design guard -> hybrid.
4. **Debt this generation:** DR-46 (WP3.4: a mixed `[True, 1.0]` list passes the dtype check; out of envelope), DR-47
   (WP3.11: old job callable, cancel during/after `mark_complete`, lock-free cancel race). Flaky test seen once under
   load: `tests/test_gui_startup.py::test_shutdown_stops_every_worker_when_one_overruns_its_timeout` (WP3.16's; 0.05 s
   timing precondition) -- NOT banked (did not recur in 2 later full runs); bank it if it fails again.
5. **Consumer notes standing:** from gen 8/9 (`git show 05dd68a:docs/orchestrator-state.md`, "Where things stand" 4);
   new: WP3.14/WP3.18 read the WP3.11 record under `schema_hash` (numbers canonical: int == float, bool distinct,
   signed zero equal) and DR-47's cancel race; WP3.17 shows `blend_with_original` 0-100.
6. **Host:** one heavy job at a time. Today two full suites at once ran FFmpeg out of memory twice (WP3.4 CuPy run;
   a WP3.11 V3 test), and the reaper stopped a background suite while the session was idle at ~7-8 GB free. The full
   suite is now ~4200 tests, 29-33 min with CuPy, ~20 min without.

### Workstreams

Each accepted package had its return report posted to CHARC and an info-update to the operator.

| Package | Accepted | Main | Record | CHARC QA |
|---|---|---|---|---|
| WP0.1 | 2026-10-14 | `c09f747` | `docs/proofs/wp0.1-accept.md` | STANDS |
| WP0.2 | 2026-10-15 | `4863a90` | `docs/proofs/wp0.2-accept.md` | STANDS (DR-6..DR-10) |
| WP1.1 | 2026-10-15 | `9711faf` | `docs/proofs/wp1.1-accept.md` | STANDS (DR-11..DR-13) |
| WP1.2 Part A | 2026-10-15 | `f6d998a` | `docs/proofs/wp1.2-accept.md` | STANDS (`bac37599277c1365`) |
| WP1.5 | 2026-10-15 | `3242679` | `docs/proofs/wp1.5-accept.md` | CONFIRMED (`6d4fca629d21efe0`) |
| WP1.2R | 2026-10-15 | `996274e` | `docs/proofs/wp1.2r-accept.md` | CONFIRMED (`60dc8ad66427bb15`) |
| WP1.3 | 2026-10-15 | `7178540` | `docs/proofs/wp1.3-accept.md`; DR-20, DR-21 | CONFIRMED (`09057ee4b3979fa4`) |
| WP-T1 | 2026-10-15 | `f6a34a4` | `docs/proofs/wp-t1-accept.md`; DR-22 | CONFIRMED (`3501648bc8844468`) |
| WP1.4 | 2026-10-19 | `91f5775` | `docs/proofs/wp1.4-accept.md`; DR-23..DR-26 | CONFIRMED (`6c5d88685e64a37c`) |
| WP-T2 | 2026-10-19 | `8c9d780` | `docs/proofs/wp-t2-accept.md`; DR-27 | CONFIRMED (`d40217a81696cc03`) |
| WP1.2 Part B | 2026-10-19 | `2dd06cf` | `docs/proofs/wp1.2b-accept.md`; DR-28; depth breach recorded | CONFIRMED (`cb61a4e41f625d73`) |
| WP1.3D | 2026-10-20 | `7f9fea1` | `docs/proofs/wp1.3d-accept.md`; DR-29 | CONFIRMED (`c6bda8a38146274f`) |
| WP1.4b | 2026-10-20 | `afaff0e` | `docs/proofs/wp1.4b-accept.md`; Gate result 4 KEEP; DR-30; flip witness 6/6 | CONFIRMED (`2fe4e7e1dc9e0854`) |
| WP2.1S | 2026-10-20 | `a866f06` | `docs/proofs/wp2.1s-accept.md`; DR-31; 2 depth re-seats; B errata at the gate | CONFIRMED (`9fb52c00bbb58a9b`) |
| WP2.2 | 2026-10-20 | `b288533` | `docs/proofs/wp2.2-accept.md`; DR-32; B re-run major adjudicated at the gate; IF-1..IF-10 frozen; 892 passed on main | CONFIRMED (`4f11a18fc46c9fc4`) |
| WP2.3 | 2026-10-20 | `d605925` | `docs/proofs/wp2.3-accept.md`; DR-33; B re-run 3 majors adjudicated at the gate; first cell past cap at R1; 1138 passed on main | CONFIRMED (`2e828b51020759b1`) |
| WP3.15 | 2026-10-20 | `da54a47` | `docs/proofs/wp3.15-accept.md`; DR-34; DR-32 closed; second blocking B adjudicated at the gate (B2#1 refuted by execution); stacked gate | CONFIRMED (`3ee39aedcd59a4aa`) |
| WP3.13 | 2026-10-20 | `6dd5a00` | `docs/proofs/wp3.13-accept.md`; DR-35; A converged R3 (R1 critical fixed by tokened temporaries); B clean | CONFIRMED (`3ee39aedcd59a4aa`) |
| WP3.7 | 2026-10-20 | `6e3417a` | `docs/proofs/wp3.7-accept.md`; DR-36; A terminated R2; B clean; main gates for the stack: 1671 passed | CONFIRMED (`3ee39aedcd59a4aa`) |
| WP3.1 | 2026-10-20 | `f4acbd0` | `docs/proofs/wp3.1-accept.md`; DR-37; A terminated R2 (two cells, depth re-seat at R1); B clean (erratum at the gate); two full runs (CuPy and none); 1844 passed on main | CONFIRMED (`6cadc26e470cd8c6`) |
| WP3.3 | 2026-10-21 | `09d1d11` | `docs/proofs/wp3.3-accept.md`; DR-14 CLOSED; DR-38; B clean (2 recovered reconnects); stacked gate (re-ordered) | CONFIRMED (`075a686775a95772`) |
| WP3.5 | 2026-10-21 | `55c266d` | `docs/proofs/wp3.5-accept.md`; DR-20 (1) CLOSED; DR-39; B clean | CONFIRMED (`075a686775a95772`) |
| WP3.2 | 2026-10-21 | `4b4da9b` (+ `68a8d93` main gates) | `docs/proofs/wp3.2-accept.md`; DR-40; B pass 1 major (float64 leak, confirmed by execution) -> ONE remediation -> B re-run clean; main 2904 passed | CONFIRMED (`075a686775a95772`) |
| WP3.12 | 2026-10-21 | `3aaf395` | `docs/proofs/wp3.12-accept.md`; DR-41; A converged at the R5 gate; B pass 1 blocking -> ONE remediation -> pass 2 adjudicated at the gate; stacked with WP3.6; main 3440 passed | CONFIRMED (`28160f360239ca35`) |
| WP3.6 | 2026-10-21 | `d0f00ee` (+ `4ec835d` main gates) | `docs/proofs/wp3.6-accept.md`; DR-42; built-in ICC moved reader -> writer (IF-1); B blocked twice, pass 2 adjudicated at the gate; main 3440 passed | CONFIRMED (`28160f360239ca35`) |
| WP3.16 | 2026-10-21 | `a2685cb` (+ `0c41615` main gates) | `docs/proofs/wp3.16-accept.md`; DR-43, DR-44; A converged R4; rebased onto WP3.6 by the orchestrator; one additive contract member; B blocked twice, pass 2 adjudicated at the gate; main 3559 passed | CONFIRMED (`6d15bf1f653b5038`) |
| WP3.9 | 2026-10-21 | `09ab408` | `docs/proofs/wp3.9-accept.md`; DR-45; A converged R3; candidate 3670 passed; B clean (1 minor + 1 advisory banked, 1 erratum) | CONFIRMED in full (`bfe4b56072240ecf`; 3670 passed at CHARC's seat; worktrees `wp3.9`, `wp3.9-mc` removed by gen 10) |
| WP3.4 | 2026-10-26 | `ad15ab4` | `docs/proofs/wp3.4-accept.md`; DR-46; A converged R1; B pass 1 blocked (dtype coercion, confirmed by execution) -> ONE remediation -> B pass 2 clean, erratum at the gate; CRLF blob caught and fixed; candidate CuPy 3970 / no-CuPy 3418 | CONFIRMED static half (`d3c7ebcf9749a876`; register rows `6b58619`) |
| WP3.11 | 2026-10-26 | `47235b6` | `docs/proofs/wp3.11-accept.md`; DR-47; A converged R3; B pass 1 blocked (schema-hash divergence) -> fresh-seat remediation -> B pass 2 blocked (signed zero) ADJUDICATED AT THE GATE, verified by execution; stacked on WP3.4; CuPy 4200; no-CuPy reaped; main full pytest owed (CHARC asked to let its QA suite stand) | pending |
| WP3.17 | 2026-10-26 | `d31dd0f` | `docs/proofs/wp3.17-accept.md`; A terminated R1; B blocked twice, pass 2 adjudicated at the gate (UPHELD); stacked gate 4501 passed | CONFIRMED static half (CHARC QA on `d31dd0f`; DR-49..DR-52) |
| WP3.18 | 2026-10-26 | `d31dd0f` | `docs/proofs/wp3.18-accept.md`; A terminated at the R5 gate (lane restructure); B pass 1 blocked -> seat-3 remediation -> B pass 2 clean, erratum at the gate | CONFIRMED static half (CHARC QA on `d31dd0f`; DR-49..DR-52) |
| WP3.19 | 2026-10-26 | `d31dd0f` | `docs/proofs/wp3.19-accept.md`; A converged R2; B blocked twice, pass 2 adjudicated at the gate (UPHELD) | CONFIRMED static half (CHARC QA on `d31dd0f`; DR-49..DR-52) |
| WP3.20 | 2026-10-26 | `d31dd0f` | `docs/proofs/wp3.20-accept.md`; A terminated R1; B blocked twice, pass 2 adjudicated at the gate (UPHELD) | CONFIRMED static half (CHARC QA on `d31dd0f`; DR-49..DR-52) |
| WP3.10 | 2026-10-27 | `47bc6d6` | `docs/proofs/wp3.10-accept.md`; nine seats; A ten rounds (product R4, instrument R8, NVENC ceiling R10 five-round gate); AD-12 RULED; floor row fits D106; B pass 1 blocked -> remediation; B pass 2 blocked ADJUDICATED AT THE GATE (CHARC UPHELD), gate fix verified by execution; candidate 4766 passed | pending |
| DR-44 amendment | 2026-10-21 | `de206e2` | `docs/proofs/dr44-contract-amendment.md`; B pass 1 blocked, remediated, pass 2 clean; main 3570 passed | checked (`00b7f7a8baa5ae3b`) |

Kept branches (evidence; do not delete unasked): `wave4-briefs`, `brief-wp3.14`, `brief-wp3.20r`, `brief-wpt3`, `brief-wpt4`, `orch-state-g12`, `wp3.10`, `wp3.10-mc`, `wp3.10-mc1`, `wp3.10-mc2`, `wp3.10-acc`, `wp3.4`, `wp3.4-mc`, `wp3.11`, `wp3.11-mc`, `wp3.10-pre-rebase`, `orch-state-g10`, `orch-state-g10b`, `wp3.9`, `wp3.9-mc`, `dr44`, `dr44-record`, `wave3-briefs`, `wp3.12`, `wp3.12-mc`, `wp3.6`, `wp3.6-mc`, `wp3.6-mc2`, `wp3.16`, `wp3.16-mc`, `wp3.16-pre-rebase`, `wp3.2`, `wp3.2-mc`, `wp3.2-mc2`, `wp3.3`, `wp3.3-mc`, `wp3.3-mc2`, `wp3.5`, `wp3.5-mc`, `wp3.5-mc2`, `wp3.15`, `wp3.15-mc`, `wp3.13`, `wp3.13-mc`, `wp3.7`, `wp3.7-mc`, `wp3.1`, `wp3.1-mc`, `wp2.3`, `wp2.3-mc`, `wp2.2`, `wp2.2-mc`, `wp1.2b`, `wp1.2b-b1`, `wp1.3d`, `wp1.3d-b1`,
`wp1.4b`, plus the earlier packages' (`git branch`).

### Practice notes (this instance)

- **Gate worktrees need the local config (gen 12, WP3.10):** copy the main tree's uncommitted `clearwater.local.toml`
  into every `-mc`/stack worktree BEFORE its full suite. Without it `test_lookcheck_deep.py` fails on `LocalConfigError`
  and the footage tests skip (27 skips instead of 2); that run is VOID.
- **CR check:** count with `tr -cd` given a carriage-return argument (the line-endings rule above), never `grep -c` (it
  miscounted every line as a CR in a loop at gen 12).
- **Merging:** rebase in a `-mc` worktree; compare `git patch-id --stable` (author range vs
  candidate vs main); gate there; Reviewer B; `git merge --ff-only`; `uv sync`; re-gate main. Ask
  CHARC to hold main from B to the merge; no orchestrator commit on main in that window either.
- **The full pytest now takes 8-15 minutes (771 tests)**, past one 10-minute tool call: run it in
  the background with output to a scratchpad file, then `-m gpu` and the harness gate. Never two
  GPU jobs at once (the bit-identity witness waits for pytest).
- **Reviewer B = my own single Codex pass at this seat, never a cell.** WSL, codex-cli 0.162.1,
  `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`. Runner
  template: `C:\Users\rwsmy\clearwater-review-evidence\wp1.4b\reviewB\run_review_B.sh` (probe |
  review; invoke `MSYS_NO_PATHCONV=1 wsl.exe bash -ilc 'bash /mnt/c/.../run_review_B.sh <mode>'`).
  Prompt template: `...\wp1.4b\reviewB\review-prompt-B.md`. Assertions: banner, `^ERROR` count,
  `ERROR codex_core` classified, `tokens used` footer, `succeeded in` count, anchored VERDICT,
  withheld-access grep on the `/bin/bash` command lines; md5s to `md5s.txt`. A blocking B on an
  introduced major gets ONE remediation and one B re-run; a second blocking B is adjudicated at the
  gate. Report overstatements B finds can be fixed as "Erratum at the gate" text in the report.
- **Bit-identity witness for prototype default or hook changes:** generation 2's script is in its
  session scratchpad (`witness_flip.py`; not in the repo). Spec: `correct()` with explicit
  methods on a fixed synthetic 600x900 image, seed 12345, Ancuti blue off/on and 3C, CPU and GPU,
  `np.array_equal`, run once per tree (each tree's own venv) and compared.
- **Messages to cells:** a SendMessage to a working cell lands only when it yields, and a queued
  message WAKES a cell that has gone idle. At any re-seat, send the old cell an explicit STAND-DOWN
  before dispatching the successor, and have the successor check `git status` for foreign
  changes. A ruling sent at a yield may arrive after the cell has moved on: if it matters, follow
  up with a short superseding message.
- **Post first, then cue.** Write mailbox bodies with the Write tool (a long bash heredoc once
  failed to parse and the cue went out before the post); cue only after `posted ->` is shown.
- **Bash `cd`:** a bare `cd` in a Bash call moves the session's working directory. Use absolute
  paths, `git -C`, or `( cd ... && ... )` subshells.
- **Truncated cell reports:** extract the last assistant text from
  `~/.claude/projects/C--Users-rwsmy-clearwater/<session>/subagents/agent-a<name>-*.jsonl`.
- **Worktrees** holding a copied `clearwater.local.toml` need `git worktree remove --force`.
- **Process control:** the auto-mode classifier blocks `Stop-Process`; surface it, do not work
  around it. No Defender exclusion requests (the owner's setting).
- **Reviewer B runner for later packages:** copy
  `C:/Users/rwsmy/clearwater-review-evidence/wp2.2/reviewB/run_review_B.sh` and
  `review-prompt-B.md` (sed `wp2.2` -> the new id). Reviewer prompts must exclude `docs/proofs`
  with a glob that MATCHES (`--glob '!docs/proofs/**'`), and the assertion grep must check command
  OUTPUT too: a non-matching glob leaked ledger lines in WP2.2 R2.
- **Re-run of B after a remediation:** reset the `-mc` branch to the remediated author branch,
  rebase, and add a "THIS IS THE RE-RUN" section to the prompt listing the pass-1 findings
  (WP2.2 `reviewB2/`).
- **QA catches this generation:** a cell's "no W7.json" claim was false (WP2.1S), and a cell's
  "1 MB+ blocks" claim was really buffer depth. Check every negative claim against disk.
- **The orchestrator's own depth cap:** the hook prints `[ctx]`. Roll over at the first clean
  boundary after about 400K; never with a cell mid-round, since it dies with you.
- **Memory pressure:** the host stopped background test runs on 2026-10-19 for low system memory;
  do not restart a killed run on your own; ask.
- **`-mc` worktree setup (gen 4, paid for at WP2.3):** after creating or rebuilding a `-mc`
  worktree, copy `clearwater.local.toml` into it AND `mkdir -p <wt>/work` BEFORE the full
  pytest (`--basetemp=work/...` needs its parent; without both, 107 errors / 11 failures that
  are not the package's). Build and rebase it with `git -c core.autocrlf=false ...` (the system
  gitconfig sets autocrlf true; a rebase across the commit that adds `.gitattributes` stopped on
  the CRLF manifest). A bare `git -C <wt> config core.autocrlf false` writes the SHARED
  `.git/config`: never do that.
- **Bare `cd` (gen 4 did it three times):** every gate in a worktree runs in a `( cd ... && ... )`
  subshell. The session's cwd moving under a live cell is hazard (1).
- **Cell depth:** run `scripts/cell_depth.py <name>` from the repo root (from a worktree it
  guesses the wrong project dir).
- **Brief yield schedule:** name the R1 yield explicitly ("END YOUR TURN as soon as round N's
  verdict is adjudicated, BEFORE remediating"). wp23-cell, without it, ran R1 and its
  remediation in one turn to 407K; wp23-cell2, with it, yielded on time at 96K.
- **Delayed idle notifications:** a cell's `idle_notification` can arrive AFTER its real report
  and after your reply woke it; compare its timestamp with your last message before acting.
  Never reply to a stale one (a reply wakes the cell).
- **Drafting helper:** brief drafting can go to a `general-purpose` (opus) helper that writes
  the drafts uncommitted; QA them against disk (grep every cited AD/IF/DR/clause) before the
  query. `wave1-drafter` did WP3.1/3.7/3.13/3.15 this way.
- **Long mailbox bodies and scripts:** write them with the Write tool; a long bash heredoc
  failed to parse again in gen 4.
- **Gen-5 practice (wave 1, four parallel cells):**
  - **Window queue (X5):** one full-pytest window at a time, granted by SendMessage; the cell sends
    `WINDOW RELEASED: <summary>` mid-turn and carries on into its Reviewer A round. A queued grant
    can land BEHIND another queued message; if the cell says "no window", re-grant with a short
    superseding message.
  - **The orchestrator's candidate gate can replace a cell's final-head run** (same code rebased
    onto main): it saves a serialised window. Tell the cell, and it reports "run by the
    orchestrator on the candidate".
  - **Stacked merge gate** (CHARC accepted the form, `99e73cf967e2d559`): rebase candidate N+1 onto
    candidate N, patch-id check each, ONE full pytest on the stack top, then ff + accept commit per
    package (rebase each onto the new main, patch-id again), then the main gates once at the end.
    Ask CHARC to HOLD main first and post the release with the return report.
  - **Reviewer B prompts:** git does not work inside a worktree under WSL (the `.git` file points
    at a Windows path). Say in the prompt that git is unavailable and that the diff and HEAD sha
    are supplied (CHARC `3ee39aedcd59a4aa`).
  - **Exclusive windows:** CHARC's QA full pytest overlapped WP3.1's speed row (~21:09-21:20Z).
    Tell CHARC when an exclusive window opens, and ask it not to run a suite until it closes.
  - **Removing merged worktrees:** `git worktree remove --force` fails "Filename too long" on
    pytest basetemp trees; follow it with PowerShell
    `Remove-Item -LiteralPath "\?\C:\Users\rwsmy\clearwater\.worktrees\<name>" -Recurse -Force -Confirm:$false`
    (a literal path; an interpolated `\?\$p` is blocked by the guard), then `git worktree prune`.
  - **Idle notifications:** nearly every cell message was followed by an idle notification
    summarising it; most predate the reply they cross. Check the timestamp, never reply to one.

- **Gen-6 practice (wave 2):**
  - **Never send a cell a ruling that changes work it may already be doing** without a numbered
    FINAL line: WP3.5's bounds flipped three times when two of my messages crossed its round. Send
    ONE ruling per question, mark it FINAL, and if a correction is needed say "supersedes my
    message of HH:MM" in its first line.
  - **Heavy non-exclusive measurements** (WP3.12's 4K decode) and full-pytest windows can share
    the host if free memory stays above ~5 GB (check `Win32_OperatingSystem.FreePhysicalMemory`);
    runs strictly sequential inside a window; a run that dies without a summary is reported, not
    restarted.
  - **A cell idle after a background run** may not wake on its completion: check its status file
    and nudge it (WP3.2's runs finished ~20 min before it reported).
  - **Drafting wave briefs:** two `general-purpose` helpers in parallel (numeric / I/O halves) with
    one common commission file; a citation-check script (ids defined, quotes verbatim, paths) run
    at this seat before the CHARC query. The script was in the gen-6 scratchpad
    (`cite_check.py`); rewrite it if needed (about 70 lines).
  - **Interface amendments** CHARC rules are ONE orchestrator commit on main before the tranche
    branches (`f4cd1e4`), gated by the full pytest; `docs/architecture.md` section 3 is CHARC's and
    may lag the code (AD-20 records the amendment).
  - **Permission laundering:** a cell asked this seat to `Stop-Process` a pid the classifier
    refused at its seat; refused here too and surfaced to the owner.

- **Gen-7 practice (wave 2, tranche A accepts):**
  - **Re-ordering a stack** when its bottom package takes a Reviewer B remediation: with disjoint
    files, rebuild `-mc2` branches in the new order (WP3.3 -> WP3.5 -> WP3.2'); patch-ids hold;
    a B pass run on the earlier tree stands when the package's owned files are byte-identical in
    both trees (`git diff <old-mc> <new-mc2> -- <owned paths>` empty; say so in the record). One
    full pytest (normal + cupy-unimportable) on the final stack top, then ff + record per package
    in stack order, then the main gates once.
  - **Cupy-unimportable run:** a scratch script that sets `sys.modules["cupy"] = None` and
    `sys.modules["cupyx"] = None`, then `sys.exit(pytest.main(sys.argv[1:]))`; run with
    `uv run python <script> --basetemp=work/pt-mc-nocupy -q -p no:cacheprovider`.
  - **Rulings cross remediations:** a cell that yields with a round's verdict often carries on
    into the remediation and the next round before a ruling lands (wp312-cell2 did it twice).
    Put the binding stop in the DISPATCH prompt ("make NO change in the turn that adjudicates a
    round"), not only in a later message; past ~250K say "REVIEW ONLY this turn".
  - **`git stash` in a cell:** the stash stack is shared by every worktree; forbid it in every
    dispatch prompt ("use a WIP commit or a scratch copy").
  - **Line endings:** `git show <rev>:<path>` displays CRLF on this machine; check stored blobs
    with `git cat-file -p` (blobs are LF). Commit in a worktree with `-c core.autocrlf=false`.
  - **Debt-register edits at accept:** a scratch script inserting the new DR row after the last
    `| DR-` line and rewriting a closed row's status cell; check the status cell ends `| OPEN |`
    first (gen 7's `dr_edit.py` in its scratchpad).
  - **The harness gate prints `acked 1 message(s); moved inbox -> read.`** from its own temporary
    mailboxes; the real inboxes are untouched (verified). Redirect it to a log and grep
    `^Ran |^OK|FAILED`.
  - **Suite size now:** ~2905 tests; the full normal run ~15 min, cupy-unimportable ~10 min.
  - **Reviewer B finding against the prompt's own wording** (WP3.5 B (2): "no GPMF data") is
    DECLINED with the standing rule cited; word prompts from the rule, not a paraphrase.

- **Gen-8 practice (wave 2, tranche B accepts):**
  - **Re-dispatch from ledgers works:** a fresh cell given the recipe, the brief, the ledger's
    "resume here" section and the rulings in the prompt resumed cleanly every time (5 cells).
  - **Multi-finding remediations go to a fresh cell** once a cell is past ~200-250K (WP3.6 R1:
    12 findings, fresh cell; WP3.16 after R4). Bounded single steps continue in the same cell.
  - **Read a cell's design choice against the frozen IF docstrings** before granting a window:
    WP3.6 put a synthesized ICC profile in the READER, which contradicts IF-1. Moving it cost one
    small turn; after the reviews it would have cost a round.
  - **Ask CHARC to clarify a ruling clause that collides with a brief ruling BEFORE dispatch**
    (the "no output ever lacks iCCP" clause against question 3): answered in under a minute.
  - **Reviewer B now usually blocks on pass 1**, and on pass 2 too; pass 2 is adjudicated at the
    gate per the standing practice. Bank with a TRIGGER naming the consumer package, and say in
    the release post which adjudication CHARC should look at.
  - **Lock conflicts (X-B3):** resolve `pyproject.toml` by a reviewed script (scratchpad
    `resolve_pyproject.py`, `union_conflict.py`, `essentials_conflict.py`), then
    `git checkout --ours uv.lock` + `uv lock`; never a hand merge of the lock.
  - **The debt register's committed blob is CRLF** (49 CR in 49 lines at gen 8). An LF rewrite
    churns the whole file, so after a scripted insert run `sed -i 's/$/\r/'` and check
    `git diff --stat` shows +N only.
  - **Prompt slips caught by cells:** the WP3.16 cell found I had named the wrong base sha; the WP3.6
    cell found a source my "only nclx gives assumed=False" premise missed. Keep inviting it.
  - **One heavy job at a time** (see "Where things stand" 5). Codex in WSL holds ~2.3 GB (`vmmemWSL`).
  - **Main gates:** run with `QT_QPA_PLATFORM=offscreen` now that the GUI tests are in the suite.
    The suite is ~3559 tests: normal ~15 min, cupy-unimportable ~10.5 min. Main's venv did NOT need
    the Essentials reinstall (it never had the meta-package); other venvs that had it do.

- **Gen-9 practice (wave 3, tranche A):**
  - **Hazard (7) in practice:** briefs, contract amendments, accept records and this state file all went through
    a worktree branch + `git merge --ff-only`. Helpers writing drafts get the worktree path in their commission.
    `git -c core.autocrlf=false worktree add` for any `-mc` (a plain add + autocrlf=false rebase stops on
    "unstaged changes"). Diffs for a reviewer: `git diff A..B` on BRANCHES that share history, or a commit range
    (`X~1..X`), never `main..branch` after main moved (it shows main's newer commits reversed).
  - **Opus cells burn 140-220K at round 0.** Plan the re-seat at dispatch: round 0 in seat 1, build in seat 2,
    reviews in seat 3 when needed. A bounded final task before retiring (measure, write RESUME HERE, commit)
    and a fresh cell dispatched with a short prompt that points at the base dispatch file + overrides worked
    every time (WP3.4 x2, WP3.10 x2).
  - **Dispatch prompts as files:** `prompt-wp3.N.md` in the gen-9 scratchpad (gone with it); the template is in
    this file's history only through the briefs' Rulings + the ledgers. Rebuild: READ FIRST, WORKSPACE (no bare
    cd, no main-tree edits, no stash, autocrlf=false commits), YIELD SCHEDULE (round 0, windows, yield at every
    verdict before remediating, ~400K stop, final report), depth from the dispatcher, PACKAGE NOTES.
  - **Check premises before relaying a STOP:** WP3.11's V3-1 was first measured with AD-14's metric; a re-check
    against the spec's own metric (std of frame-to-frame differences) was the right order (CHARC upheld it).
  - **Rulings cross yields:** a cell often yields with a report written before a queued ruling landed. Idle
    notifications are almost always stale copies; reply only to the cell's real message, and when a ruling may
    not have landed, send a short RECAP marked FINAL.
  - **Grants for test lines in another package's files** (WP3.7's exact module-set test; WP3.1/3.2/3.3 assertion
    lines pinning behaviour a debt fix removes): small, named in the report's owned-files list, one commit.
  - **Codex B on a GUI change** found the one path nobody tested (the open path's unfiltered clear). Even a small
    orchestrator-authored contract amendment gets both nets.

- **Gen-10 practice (wave 3 resume, tranche A accepts):**
  - **Bare `cd` (gen 10 did it THREE times into gate worktrees while cells were live, each reverted in one call):**
    use `cd` ONLY to the repo root; every worktree command is `( cd <wt> && ... )`, `git -C`, or absolute paths.
  - **Order an EXCLUSIVE window first** when re-dispatching several cells: WP3.4's exclusive runs went before the other
    cells were dispatched, so nothing else was on the host.
  - **Full suites never overlap:** two at once ran FFmpeg out of memory; a cell's targeted FFmpeg tests during another
    cell's full suite did too. Grant one full suite at a time and say "targeted tests only" to the others.
  - **Low-memory reaper:** Claude Code stops background shells under memory pressure while the session is idle; the
    note says do not restart unasked. Record it as not-a-result.
  - **Line endings at the gate:** CRLF blobs appeared from cells' `sed -i`/script edits and from a docstring-only
    commit; check every changed blob for CR bytes (see the standing rule above).
  - **Stacked gate across a remediation:** build `N+1-mc` on `N-mc`; when N merges first, `rebase --onto main <old N-mc
    head>` and show 0 code lines differ from the tested stack top.
  - **Reviewer B prompts:** write the contract from the RULE, not a paraphrase (my WP3.4 prompt named bools, the ruled
    Y-2 list did not; CHARC upheld the remediation anyway). Write `md5sums.txt` in every B folder and name the md5s in
    the record (CHARC asked).
  - **Design guard in a dispatch:** when one subsystem keeps producing blocking findings (WP3.10's watcher process,
    three in two rounds), tell the next seat to STOP and propose the simpler design instead of fixing round N+1; the
    hybrid closed the loop at the next round.
  - **Cells catch ruling flaws:** WP3.11 seat 3 found my canonical-`==` ruling missed `True == 1.0` and built a typed
    compare; invite deviations with evidence.
  - **Prompts as files:** gen 10's dispatch prompts are in its scratchpad
    `C:\Users\rwsmy\AppData\Local\Temp\claude\C--Users-rwsmy-clearwater\9db1a59d-fecc-4278-994b-f6ddecfa2635\scratchpad\`
    (`prompt-wp3.10-seat4.md`, `prompt-wp3.11-seat2.md`, `prompt-wp3.4-cell4.md`, `pytest_nocupy_gate.py`); Reviewer B
    prompt templates under `C:\Users\rwsmy\clearwater-review-evidence\wp3.4\reviewB*` and `...\wp3.11\reviewB*`.

### Pending (still valid)

- The smoothing default is 2.0 s (v0.5.4 7.2), with the step-aware temporal task for WP3.11;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is its input.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- IF-5 `VideoSink.abort` docstring cites D84; it should be D44/D85 (CHARC: fix at the next
  interface touch, not before).
- Open debt: see `docs/debt-register.md` (its status column is authoritative). Gen 10 added DR-46, DR-47; WP3.4 closed DR-19, DR-38 and parts of DR-37/DR-40 (rows by CHARC at `6b58619`); WP3.11 closes DR-23 and DR-25 (1)(2)(4)-(7) at CHARC's QA.
