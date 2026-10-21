# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 8** (`clearwater-orchestrator-20261020-1556`) ROLLED OVER 2026-10-21 ~06:05Z at ~400K,
  at a clean boundary (no cell live, main released). **Generation 9 starts here** (verify:
  `comms/.launch-sessions.json`). Earlier: gen 7 `clearwater-orchestrator-20261020-1419`, gen 6
  `-20261020-1134`, gen 5 `-20261020-0802`, gen 4 `-20261020-0524`, gen 3 `-20261019-2346`, gen 2
  `-20261018-1442`, gen 1 `-20261014-1258`.
- **Inbox:** gen 8 drained through CHARC's WP3.16 hold acknowledgement (`8cc28ff9944f6550`) and
  STOPPED DRAINING at its rollover announcement. You are the sole drainer (verify:
  `uv run python scripts/role_mail.py list --role orchestrator`). CHARC's QA of WP3.16 may be
  waiting there: act on it (remove worktrees `wp3.16`, `wp3.16-mc`; branches kept).
- **CHARC is generation 2:** `clearwater-charc-20261020-0636`. Cue that exact name.
- Bash-launch gauge at gen-8 bring-up: 37.0 ms. Re-measure at yours.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question
  goes `--to charc` (type query, recommended answer first, one cross-session cue after posting).
  CHARC answers in the operator's stead except plan s.3 owner-reserved items ("HOLD <item>": pause
  that item, continue the rest). Info-updates (`--type fyi`) to the operator after each accept. No
  AskUserQuestion from this seat.
- **OWNER WORD 2026-10-20 ~16:00Z:** "Gate 1: Option C.  2. Keep.  3. approve 0.5.4". Spec
  **v0.5.4**; plan v1.2 (WP3.21 optimisation package drafted at wave 4 with WP3.14); architecture
  **FINAL 1.0**; interim N6 = 25 min/min at 4K (D106); gain caps KEPT (D100). No owner decision is
  open. Cite v0.5.4.
- **GoPro IMU and GPS are OUT OF SCOPE** (owner 2026-10-19 via CHARC `01500d3574412e69`): no brief
  reads ACCL/GYRO/GRAV/CORI/IORI/GPS. Nothing from a `gpmd` track is ever committed. GPMF
  settings come only from the `moov/udta` GPMF atom, keys FMWR/PRTN/PTCL (AD-16 as corrected) --
  that read IS permitted (a Reviewer B prompt must not say "no GPMF data"; say "no `gpmd`, IMU or
  GPS data").
- **Cell depth** (owner 2026-10-19/20; kernel `docs/orchestrator-context.md` hazard (6)): read
  `uv run python scripts/cell_depth.py <cell>` at dispatch, every yield, before any ruling; record
  each figure with its moment. **~250K is an EVALUATION point**; **~400K STOP** and re-dispatch.

### Live cells at the gen-8 rollover

NONE. Every gen-8 cell returned and was stood down: `wp312-cell3` (246,012), `wp36-cell2` (222,405),
`wp36-cell3` (236,865), `wp316-cell2` (266,869), `wp316-cell3` (206,214). Wave 2 is COMPLETE.

### Where things stand -- the successor starts HERE

1. **Wave 2 is fully accepted.** Gen 8 accepted WP3.12 (`3aaf395`) and WP3.6 (`d0f00ee` + `4ec835d`
   main gates) as a stacked gate, then WP3.16 (`a2685cb` + `0c41615` main gates). Main `0c41615`:
   harness 366 OK, static clean, full pytest 3559 passed / 2 skipped (offscreen), 810 s. CHARC QA CONFIRMED WP3.12 + WP3.6 (`28160f360239ca35`); WP3.16's QA is pending
   (the release post went at ~06:0xZ). Records `docs/proofs/wp3.{12,6,16}-accept.md`. NEW debt
   DR-41..DR-44.
2. **Every Reviewer B of gen 8 blocked twice** (pass 1 -> one remediation -> pass 2 adjudicated at
   the gate). The gate adjudications are in each record and in
   `clearwater-review-evidence\wp3.{12,6,16}\reviewB2\adjudication-B2.md`; CHARC upheld DR-41/42.
3. **Consumer notes for the next briefs (wave 3+):**
   - WP3.17-3.20 (GUI panels): `clearwater.gui.contract` gained ONE additive member,
     `Session.settings_refusal() -> Message | None` (WP3.20 must not save while not None).
     **DR-44 (b)**: before those briefs freeze, the contract needs an additive message owner, so
     one panel's success does not clear another panel's error.
   - WP3.18 (scrubber): **DR-44 (a)**: request exact frame pts from the cache's `pts_ticks`;
     `set_position` commits before the decode succeeds (an additive decode-completion signal).
   - WP4.3: **DR-44 (c)** (a job outliving `QtJobRunner.close()` keeps its callbacks); remove S1's
     `default_engines` "c3" adapter; re-measure V7 with real engines (216-796 ms GIL gaps seen
     with a pure-Python job).
   - WP3.14 / WP4.1: export re-measures photo statistics with `clearwater.gui.imaging.
     measure_statistics` on `downscale(pixels, statistics_factor(H, W))` (R3-1); **DR-43**: WP3.6
     drops a damaged EXIF block with a log warning only (no G10 signal).
   - WP3.6P (real photos): **DR-42 (a)** `cICP`/`cHRM`/`gAMA`/TIFF colorimetry read as untagged;
     **(c)** the one-line WhiteIsZero + associated-alpha fix in `tiff.py`.
   - WP3.11: stores proxies through `DiskProxyCache` (`DEFAULT_CODEC` q75 4:4:4);
     `mark_complete` now refuses an entry with no proxy; a second concurrent store on one key is a
     `RuntimeError`; **DR-41** applies only to non-registered codecs.
   - The earlier gen-7 notes (WP3.21 per-call uploads DR-40 b, DR-38 a; WP3.4 DR-38 a/b/d, DR-40 a;
     WP3.9/WP3.10 DR-39; WP3.7's BT.601 `smpte170m` note) still stand.
4. **Next work (not started):** wave 3 briefs are CHARC's call; ask CHARC for direction at pickup if
   no commission is waiting. WP3.6P waits for photos from the owner.
5. **Host:** memory-tight. A background gate run was REAPED once (~03:50Z, with Codex and pytest
   concurrent). CHARC's rule (`2e6feaf538c411f4`): ONE heavy job at a time (Codex or pytest),
   >= 6 GB free before each leg, cells idle during gate runs; a second reap = STOP and ask the owner
   for a quiet block.

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
| WP3.16 | 2026-10-21 | `a2685cb` (+ `0c41615` main gates) | `docs/proofs/wp3.16-accept.md`; DR-43, DR-44; A converged R4; rebased onto WP3.6 by the orchestrator; one additive contract member; B blocked twice, pass 2 adjudicated at the gate; main 3559 passed | pending |

Kept branches (evidence; do not delete unasked): `wp3.12`, `wp3.12-mc`, `wp3.6`, `wp3.6-mc`, `wp3.6-mc2`, `wp3.16`, `wp3.16-mc`, `wp3.16-pre-rebase`, `wp3.2`, `wp3.2-mc`, `wp3.2-mc2`, `wp3.3`, `wp3.3-mc`, `wp3.3-mc2`, `wp3.5`, `wp3.5-mc`, `wp3.5-mc2`, `wp3.15`, `wp3.15-mc`, `wp3.13`, `wp3.13-mc`, `wp3.7`, `wp3.7-mc`, `wp3.1`, `wp3.1-mc`, `wp2.3`, `wp2.3-mc`, `wp2.2`, `wp2.2-mc`, `wp1.2b`, `wp1.2b-b1`, `wp1.3d`, `wp1.3d-b1`,
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

### Pending (still valid)

- The smoothing default is 2.0 s (v0.5.4 7.2), with the step-aware temporal task for WP3.11;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is its input.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- IF-5 `VideoSink.abort` docstring cites D84; it should be D44/D85 (CHARC: fix at the next
  interface touch, not before).
- Open debt: DR-1, 2, 6, 7, 8, 10-13, 15-20 (DR-20 item 1 CLOSED), 22, 23, 25-31, 33-44 (DR-14 CLOSED at WP3.3) (`docs/debt-register.md`; DR-32 CLOSED at the config boundary).
