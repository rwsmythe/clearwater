# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 9** (`clearwater-orchestrator-20261020-1959`) ROLLED OVER 2026-10-21 ~09:40Z at ~470K (the
  hook's 400K cap), at the WP3.9 accept boundary. **Generation 10 starts here** (verify:
  `comms/.launch-sessions.json`). Earlier: gen 8 `clearwater-orchestrator-20261020-1556`, gen 7 `-1419`, gen 6
  `-1134`, gen 5 `-0802`, gen 4 `-0524`, gen 3 `-20261019-2346`, gen 2 `-20261018-1442`, gen 1 `-20261014-1258`.
- **Inbox:** gen 9 drained through CHARC's WP3.9 QA note (`f1ee3ebf03b1d591`) and STOPPED DRAINING at its rollover announcement. You are the
  sole drainer (verify: `uv run python scripts/role_mail.py list --role orchestrator`).
- **CHARC is generation 3:** `clearwater-charc-20261020-2115`. Cue that exact name (re-read
  `comms/.launch-sessions.json` before each cue; CHARC rolls over too).
- Bash-launch gauge at gen-9 bring-up: 40.0 ms. Re-measure at yours.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question goes `--to
  charc` (type query, recommended answer first, one cross-session cue after posting). CHARC answers in the
  operator's stead except plan s.3 owner-reserved items. Info-updates (`--type fyi`) to the operator after each
  accept. No AskUserQuestion from this seat.
- **Owner word 2026-10-20:** spec **v0.5.4**, plan v1.2, architecture FINAL 1.0, interim N6 = 25 min/min (D106),
  gain caps KEPT (D100). Owner-pending list (CHARC carries it): photos (WP3.6P), an iPhone clip (DR-15's B-frame
  leg), the V3 ratio figures as information for CP5/WP4.2.
- **GoPro IMU and GPS are OUT OF SCOPE**: no `gpmd`, IMU or GPS data read or committed; GPMF settings only from
  `moov/udta` (FMWR/PRTN/PTCL). Location tags must never reach a committed record (WP3.10 R1 #2).
- **Cell depth:** read `uv run python scripts/cell_depth.py <cell>` at dispatch, every yield, before any ruling;
  ~250K evaluation, ~400K STOP. THIS WAVE: every opus cell reached 140-220K by its round-0 yield (deep
  re-grounding). Re-seat from a RESUME HERE ledger whenever the remaining load is large; it worked every time.
- **Kernel hazard (7)** (CHARC, 2026-10-21, after my slip): never an uncommitted edit in the MAIN tree's working
  copy. Every edit -- briefs, state, records, contract amendments -- in a worktree on its own branch, then
  `git merge --ff-only`. This state file was written that way.

### Live cells at the gen-9 rollover (they died with gen 9; re-dispatch from their ledgers)

**PAUSED at the owner's word** (2026-10-21 ~09:15Z, in the gen-9 chat: "Let's pause at the end of this portion of
the work"). Nothing is dispatched, no window is open. On resume: confirm with the owner/CHARC that work resumes,
then re-dispatch each package from its ledger's RESUME HERE (each worktree is intact; `clearwater.local.toml`,
`work\` and `.venv` in place). Every cell below is DEAD (gen-9 subagents); depths are AT PARK.

| Package | Branch / head (worktree `.worktrees/<branch>`) | Seats so far | State at park | Next step on resume |
|---|---|---|---|---|
| WP3.4 method assembly | `wp3.4` `3fae1d5` | 3 (cell 3 at 133K) | Built; Reviewer A CONVERGED R1 (0/0/3, minors fixed); V8 test per amended AD-11; full pytest 3868 passed at `84ad0ef` (product code changed since: F1 fix, F2 docstrings) | Fresh cell from RESUME HERE: EXCLUSIVE `--memory` then `--whole --cpu-frames 10` windows (one at a time, post OPEN/CLOSE to CHARC), full pytest CuPy-unimportable then with CuPy, finish the report. Then my gate. |
| WP3.10 video encode | `wp3.10` `98ee54a` | 3 (cell 3 at 361K) | R1 remediated (3 commits); R2 adjudicated: #1 rejected (repro), #2 out-of-envelope REOPENED and banked, #3 minor cleanup, **S1 self-found in-envelope MAJOR** (a truncated source cut at a packet boundary: the last frame is stretched to the whole file's presentation end) | **Ruling owed (gen-9 recommendation: YES to all):** fix S1 by taking the next pts from the source's own sample table; fold #2's exact head-trim refusal (media_time == earliest composition time) into the same read; #3 cleanup; then Reviewer A round 3, then a full-pytest window. The footage legs (AD-12 quality, the product GX011627 leg, the export FLOOR row EXCLUSIVE) can now run: WP3.9 is on main (rebase `wp3.10` onto main first). Banked: WP3.7's `probe.py` `_run_ffprobe` still inherits FFREPORT. |
| WP3.11 analysis engine | `wp3.11` `e82aa2b` | 1 (cell 1 at 359K) | Built; step-aware eval run (default stands); R1 adjudicated 0/3/5 (F1, F2 cancel-path MAJORs; F5 V3 metric, superseded); CHARC's V3-1 ruling copied into the ledger | Fresh cell from RESUME HERE: fix F1-F4, F6-F8 failing-first (F7 needs a window to re-run the eval), implement the V3-1 ruling (seeded jittering-patch clip asserted at 25 % on all four measures, ad14 tests record), Reviewer A R2, full pytest window, report. The Y-1 text is reconciled with WP3.4's at the gate. |
| WP3.9 video decode | ACCEPTED, main `09ab408` | 1 | -- | -- (DR-45 banked) |

Tranche B (WP3.17-3.20, sonnet-high) briefs are FINAL on main; CHARC's commission: dispatch after two tranche-A
returns (WP3.9 is one).

### Where things stand -- the successor starts HERE

1. **Gen 9 did, in order:** wave-3 commission from CHARC (`e7745b2be6fdd55c`); eight briefs drafted by three
   helpers, cite-checked, approved with amendments (`53d1d906e47fe2c9`), FINAL on main (`0f51822`); the DR-44
   pre-dispatch contract amendment (`701055d`, `7bee620`, `de206e2`; both nets; record
   `docs/proofs/dr44-contract-amendment.md`); tranche A dispatched; WP3.9 ACCEPTED (`09ab408`, record
   `docs/proofs/wp3.9-accept.md`, DR-45). CHARC QA of WP3.9 is pending (return report posted ~09:13Z).
2. **Main gates on `09ab408`:** harness 366 OK, ruff clean, 180 formatted, mypy 109 clean; full pytest:
   3670 passed, 2 skipped, 1562 s, exit 0 (offscreen, `work/pt-main-wp39`). CHARC QA static half CONFIRMED (`f1ee3ebf03b1d591`), DR-36 (a)(b) closed in the register (`1d1ead6`); CHARC's own full pytest of WP3.9 was waiting for mine.
3. **CHARC rulings this generation (all on main or in the briefs):** V8 for k>1 = mean <= 1/255 and p99 <= 2/255
   (k=2), <= 4/255 (k=4), max recorded (AD-11 `df21ab0`); AD-23 extended (CREATE_NO_WINDOW for every FFmpeg/ffprobe
   child, ONE spawn helper, WP4.3); WP3.10 Q-C absent edit list = identity (AD-22 `09ac181`) + build notes (1-byte
   sentinel invariant with a positive control; no carrier detail in IF-5; unreadable_tail warning in SinkReport;
   16 KiB provenance limit as a report note); P8 non-square SAR refused at open, unseen SAR = 1:1; V3-1 (AD-14
   `b9f3d09`): V3's 25 % asserted on a seeded jittering-patch clip, ad14-flicker records the ratios, owner
   information for CP5.
4. **Consumer notes still standing** (from gen 8, see `git show bbc0b02:docs/orchestrator-state.md`): WP3.14/WP4.1
   re-measure photo statistics with `gui.imaging.measure_statistics` (R3-1); DR-43 (WP3.6 EXIF warning);
   WP3.6P DR-42 (a)(c); WP4.3 DR-44 (c) + remove S1's `default_engines` "c3" adapter + re-measure V7. New:
   DR-45 (a) for WP3.11/WP3.14 (concurrent public `close()` of a `FrameStream`); the GUI shell clears only its own
   banners on a new source (panels clear theirs on `source_changed`); WP3.18 consumes `Session.frame_decoded`
   (a test of the frame_decoded -> set_statistics pairing was banked for it).
5. **Host:** one heavy job at a time (pytest, Codex, footage runs, EXCLUSIVE timing); >= 5 GB free measured each
   time (10-11 GB was typical this session). The full suite is ~3670 tests, 15-26 min.

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
| WP3.9 | 2026-10-21 | `09ab408` | `docs/proofs/wp3.9-accept.md`; DR-45; A converged R3; candidate 3670 passed; B clean (1 minor + 1 advisory banked, 1 erratum) | pending |
| DR-44 amendment | 2026-10-21 | `de206e2` | `docs/proofs/dr44-contract-amendment.md`; B pass 1 blocked, remediated, pass 2 clean; main 3570 passed | checked (`00b7f7a8baa5ae3b`) |

Kept branches (evidence; do not delete unasked): `wp3.9`, `wp3.9-mc`, `dr44`, `dr44-record`, `wave3-briefs`, `wp3.12`, `wp3.12-mc`, `wp3.6`, `wp3.6-mc`, `wp3.6-mc2`, `wp3.16`, `wp3.16-mc`, `wp3.16-pre-rebase`, `wp3.2`, `wp3.2-mc`, `wp3.2-mc2`, `wp3.3`, `wp3.3-mc`, `wp3.3-mc2`, `wp3.5`, `wp3.5-mc`, `wp3.5-mc2`, `wp3.15`, `wp3.15-mc`, `wp3.13`, `wp3.13-mc`, `wp3.7`, `wp3.7-mc`, `wp3.1`, `wp3.1-mc`, `wp2.3`, `wp2.3-mc`, `wp2.2`, `wp2.2-mc`, `wp1.2b`, `wp1.2b-b1`, `wp1.3d`, `wp1.3d-b1`,
`wp1.4b`, plus the earlier packages' (`git branch`).

### Practice notes (this instance)

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

### Pending (still valid)

- The smoothing default is 2.0 s (v0.5.4 7.2), with the step-aware temporal task for WP3.11;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is its input.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- IF-5 `VideoSink.abort` docstring cites D84; it should be D44/D85 (CHARC: fix at the next
  interface touch, not before).
- Open debt: DR-1, 2, 6, 7, 8, 10-13, 15-20 (DR-20 item 1 CLOSED), 22, 23, 25-31, 33-45 (DR-14 CLOSED at WP3.3; DR-36 closed by WP3.9, register row pending CHARC QA) (`docs/debt-register.md`; DR-32 CLOSED at the config boundary).
