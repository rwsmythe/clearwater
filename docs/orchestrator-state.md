# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 6** (`clearwater-orchestrator-20261020-1134`), online 2026-10-20 ~21:35Z, picked up
  from gen 5's state 26b095d (gen 5 `clearwater-orchestrator-20261020-0802` rolled at ~420K with no
  live cell). Earlier: gen 4 `clearwater-orchestrator-20261020-0524`, gen 3
  `clearwater-orchestrator-20261019-2346`, gen 2 `clearwater-orchestrator-20261018-1442`, gen 1
  `clearwater-orchestrator-20261014-1258`.
- **Inbox:** gen 6 is the sole drainer (verify:
  `uv run python scripts/role_mail.py list --role orchestrator`).
- **CHARC is generation 2:** `clearwater-charc-20261020-0636`. Cue that exact name.
- Bash-launch gauge at gen-6 bring-up: 39.6 ms. Re-measure at yours.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question
  goes `--to charc` (type query, recommended answer first, one cross-session cue after posting).
  CHARC answers in the operator's stead except plan s.3 owner-reserved items ("HOLD <item>": pause
  that item, continue the rest). Info-updates (`--type fyi`) to the operator after each accept. No
  AskUserQuestion from this seat.
- **OWNER WORD 2026-10-20 ~16:00Z:** "Gate 1: Option C.  2. Keep.  3. approve 0.5.4". Spec
  **v0.5.4** applied (`9cf16c5`); plan v1.2 adds **WP3.21** (optimisation package, drafted at
  wave 4 with WP3.14); architecture **FINAL 1.0**; CP3 and CP4 records in `docs/proofs/`
  (`3eca7bd`); interim N6 = 25 min/min at 4K (D106); gain caps KEPT (D100). AD-25 (platform
  conventions that are not N1 exceptions), AD-26/27 logged. No owner decision is open. Cite v0.5.4.
- **GoPro IMU and GPS are OUT OF SCOPE** (owner 2026-10-19 via CHARC `01500d3574412e69`): no brief
  reads ACCL/GYRO/GRAV/CORI/IORI/GPS. Nothing from a `gpmd` track is ever committed. GPMF
  settings come only from the `moov/udta` GPMF atom, keys FMWR/PRTN/PTCL (AD-16 as corrected).
- **Cell depth** (owner 2026-10-19/20; kernel `docs/orchestrator-context.md` hazard (6)): read
  `uv run python scripts/cell_depth.py <cell>` at dispatch, every yield, before any ruling; record
  each figure with its moment; read twice across a turn boundary to prove idle. **~250K is an
  EVALUATION point**; **~400K STOP** and re-dispatch from the ledger.

### Live cells

- **None.** Retired (never message): `wp31-cell`, `wp31-cell2`, `wp315-cell`, `wp313-cell`,
  `wp37-cell`, and every earlier cell.
- Worktrees present: none (wp3.1, wp3.1-mc removed after CHARC's QA CONFIRMED `6cadc26e470cd8c6`;
  wave 1 CLOSED). Branches kept.
- Drafting helpers (in-process, uncommitted output): `wave2-drafter-a` (WP3.2, 3.3, 3.5),
  `wave2-drafter-b` (WP3.6, 3.12, 3.16), commission `5a550699b8b58b10` (option 1: six briefs,
  tranche A = 3.2/3.3/3.5/3.12, tranche B = 3.6/3.16 after two A cells return; debt citations).

### Where things stand -- the successor starts HERE

1. **WAVE 1: three of four MERGED 2026-10-20** as one stacked gate (CHARC accepted the form,
   `99e73cf967e2d559`): WP3.15 (`6a3ba24` + record `da54a47`), WP3.13 (`4a570f5` + record
   `6dd5a00`), WP3.7 (`9157b62` + record `6e3417a`). Stack-top full pytest 1671 passed (599 s);
   main gates at the final head in `docs/proofs/wp3.7-accept.md`. DR-34 (WP3.15), DR-35 (WP3.13),
   DR-36 (WP3.7) banked; DR-32 CLOSED at the config boundary. Return reports posted to CHARC and an
   info-update to the operator (thread wave1). CHARC QA CONFIRMED (`3ee39aedcd59a4aa`, every adjudication upheld incl. WP3.15's second B and
   DR-34). Main hold RELEASED (gen 5's return report, 20:58Z).
2. **WP3.1 ACCEPTED 2026-10-20 (gen 6)**: code + erratum/DR-37 `c1fd6ce`, record `f4acbd0`
   (`docs/proofs/wp3.1-accept.md`). Patch-id `392da34a1461` author = candidate. Candidate
   `1cf9564`: 1844 passed (618 s); CuPy unimportable 1738 passed / 106 skipped (361 s). Reviewer B
   one pass NO_NEW_CRITICAL_MAJOR (4 minor, 2 advisory): B#4 report erratum at the gate; the rest
   BANKED as DR-37 (a)-(e). Main gates on `c1fd6ce`: 1844 passed (538 s), harness 366. CHARC QA
   CONFIRMED. **WAVE 1 CLOSED** (WP3.15, WP3.13, WP3.7, WP3.1).
3. **Then:** wave-2 briefs (WP3.2, 3.3, 3.5, 3.6, 3.12, 3.16) at CHARC's commission
   (`docs/briefs/wp2.4-phase3-frame.md`). WP3.12 can go now (WP3.15 merged, X2). Carry these
   consumer notes into the briefs:
   - WP3.3: `percentile` returns float32 (native precision, one cast at the return); the
     high-low stretch bounds are within AD-11, not bit-identical to the prototype; cite DR-14.
   - WP3.9: never an open-ended `-read_intervals` for frame counts (19 partial lists in 400 runs
     on ffprobe 9.0.2); DR-36 (a), (b) are its to close (ascii in two warnings; the pts sha256
     manifest check).
   - WP3.10: FFmpeg gets the SafeWrite TEMPORARY path with `-y`, never the final path; on a
     non-identity edit list `mvhd` and the longest-stream duration may differ (`mvhd` = the
     presentation form, D94).
   - WP3.12 / WP3.16: the `clearwater.config` API table in `docs/reports/wp3.15-...md`
     (`app_locations().cache_dir`; shell start: `load_settings`, `configure_logging`,
     `PresetStore(...).install_starters()`).
   - WP3.14: one `Reservations` to both `plan_output` and `SafeWrite`; validate the output folder
     and suffix at export start (`MissingFolderError` is the last net); DR-35.
   - WP3.21: the device-to-host sync-point list in the WP3.1 ledger.
   - WP4.3: start-up `remove_leftovers` before any job starts (DR-35 c).
4. **Photos:** none supplied yet. Gate 2's largest-photo leg and the photo look check stay PENDING.

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

Kept branches (evidence; do not delete unasked): `wp3.15`, `wp3.15-mc`, `wp3.13`, `wp3.13-mc`, `wp3.7`, `wp3.7-mc`, `wp3.1`, `wp3.1-mc`, `wp2.3`, `wp2.3-mc`, `wp2.2`, `wp2.2-mc`, `wp1.2b`, `wp1.2b-b1`, `wp1.3d`, `wp1.3d-b1`,
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

### Pending (still valid)

- The smoothing default is 2.0 s (v0.5.4 7.2), with the step-aware temporal task for WP3.11;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is its input.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- IF-5 `VideoSink.abort` docstring cites D84; it should be D44/D85 (CHARC: fix at the next
  interface touch, not before).
- Open debt: DR-1, 2, 6, 7, 8, 10-20, 22, 23, 25-31, 33-37 (`docs/debt-register.md`; DR-32 CLOSED at the config boundary).
