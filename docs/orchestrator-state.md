# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 6** (`clearwater-orchestrator-20261020-1134`) ROLLED OVER 2026-10-21 at the depth
  cap (~400K). **Generation 7 starts here** (verify: `comms/.launch-sessions.json`). Earlier: gen 5
  `clearwater-orchestrator-20261020-0802`, gen 4 `-20261020-0524`, gen 3 `-20261019-2346`, gen 2
  `-20261018-1442`, gen 1 `-20261014-1258`.
- **Inbox:** gen 6 drained through CHARC's AD-5 ruling (~23:58Z) and STOPPED DRAINING at its
  rollover announcement. You are the sole drainer (verify:
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

### Live cells (ALL died with gen 6; re-dispatch from the ledgers)

Tranche A of wave 2 was dispatched 2026-10-20 ~22:45Z from main `2c5540a` (IF-7 amendment
`f4cd1e4` + FINAL briefs; CHARC approval `53b752a4d7fac4fc`). Prompts at
`C:\Users\rwsmy\clearwater-review-evidence\wp3.N\dispatch.md`.

| Cell | Package | State at rollover | Your action |
|---|---|---|---|
| `wp32-cell` (opus-high) | WP3.2 | **RETURNED.** Head `dfe65d5` (code `1fcb37d`), base `2c5540a`. R1 NO_NEW_CRITICAL_MAJOR (4 minor fixed as cleanup; a `Reconnecting... 2/5` before first output ruled a recovered retry). Full: 2227 passed (868 s); nocupy 1938 / 289 skipped (517 s). 54/54 rows bit-identical to the prototype. Depths 116,822 (R0) / 218,176 (R1) / 241,447 (window). | ACCEPT (stack with WP3.3) |
| `wp33-cell` (opus-high) | WP3.3 | **RETURNED.** Head `b6c47db` (code `d8532dd`). R1 1 major (test/report) + 3 minor fixed; R2 NO_NEW_CRITICAL_MAJOR (1 minor out of envelope, cleanup `4e2e836`). Full: 2233 passed (663 s); nocupy 1958 / 275 skipped (389 s). DR-14 CLOSES on accept. Depths 119,733 / 257,103 (evaluated: continue) / 304,760 (R2). | ACCEPT (stack on WP3.2) |
| `wp35-cell` (sonnet-high) | WP3.5 | See the gen-6 announcement post for whether it returned before the rollover. Bounds FINAL = the tighter set (footage mean <= 1.0, share over 2/255 <= 1 %; testsrc2 mean <= 2.5; max reported) at `abee706`; R1 NO_NEW_CRITICAL_MAJOR (7 minor, cleanup). Its window was GRANTED ~00:05Z. Depths 90,237 / 194,772 / 240,808. | If it returned: accept. If not: run the full pytest yourself on its head (the window was its last step) and write the report from the ledger, or dispatch a sonnet-medium cell for that. |
| `wp312-cell` (sonnet-high) | WP3.12 | **At its EXCLUSIVE REQUEST yield, all committed: head `82a5dbb`** (ledger section "State at the orchestrator rollover"); JPEG q75 4:4:4 (id 2, default) and q80 4:2:0 (id 3) codecs `a21a738`, 60 cache tests green, Pillow moved to `[project]` and re-locked. Grant the EXCLUSIVE window (post OPEN/CLOSE to CHARC; nothing else heavy): the command is `uv run python tools/cache_store_test.py readcost-product` (seconds; writes `work/wp3.12/readcost.json`). Smoke (not exclusive): deflate 9.5 ms, q75 4:4:4 5.4 ms, q80 4:2:0 4.5 ms per `proxy()` (~15 % < CHARC's 30 %: q75 stands unless the official row differs). Then: report, full-pytest window, Reviewer A. Earlier: codec-independent store `b3ac336` (49 own tests). CHARC ruled AD-5 (amended on main `a6ba740`): JPEG q75 4:4:4 default, q80 4:2:0 only if > 30 % faster per scrub step; codec identity in the cache version (test plants a different identity); means/gains <= 1e-3 gate, bounds deviation <= 10 % of range beyond the 8-bit floor; Pillow to `[project]` dependencies (X-B3: WP3.6 re-locks). Pending: JPEG codec + figures, EXCLUSIVE read-cost row (post OPEN/CLOSE to CHARC), report, Reviewer A, window. Depths 87,058 / 152,958. | RE-DISPATCH a fresh sonnet-high cell on the existing branch from its ledger; YOU run the exclusive row first (or let the cell run it in a window you grant). |

Window queue (X5): nobody holds a window after WP3.5. Tranche B (WP3.6 sonnet-high, WP3.16 opus-high;
briefs FINAL at `2c5540a`) may dispatch NOW: two tranche-A cells have returned (CHARC's condition).
Before dispatching WP3.6, note WP3.12 also moves Pillow (X-B3). WP3.6P is queued until photos.

### Where things stand -- the successor starts HERE

1. **Accept WP3.2 + WP3.3 as one stacked gate** (practice note "Stacked merge gate"): `wp3.2-mc` from
   `dfe65d5` onto main, `wp3.3-mc` from `b6c47db` onto `wp3.2-mc`; files are disjoint (both add
   modules under `src/clearwater/methods/`). Patch-id per range; static gates; full pytest normal AND
   cupy-unimportable on the stack top; Reviewer B per package (template
   `clearwater-review-evidence\wp3.1\reviewB\` -- runner + prompt; say git is unavailable in WSL).
   Check at the gate: (a) the "DR-19 rule" sections of the two reports are word for word the same;
   (b) the X-4 message format is identical in both modules; (c) the `_derived_sigma` OverflowError
   guard in both. Bank at accept: core `check_sigma` OverflowError on inf (next core touch); DR-14
   CLOSED (WP3.3); DR-19 stays OPEN (WP3.4). Ask CHARC to HOLD main first; post the release.
2. **WP3.5** and **WP3.12** per the table.
3. **Tranche B** dispatch (WP3.6, WP3.16), worktrees from main after the WP3.2/3.3 merge.
4. **Consumer notes for later briefs:** WP3.11 measures on the STORED round-tripped proxy (the
   proxy is encoded and decoded in memory before any statistic; the float proxy is never a
   statistics source); WP3.11's statistics stores on a key collide with a concurrent proxy store
   (WP3.12 "second writer is a RuntimeError" covers both); WP3.11 reads spec 7.2 line 325 as
   single-clip; WP3.10 cites DR-17 for untagged-output tags and WP3.5's `ffmpeg_color_names`;
   WP3.21 gets WP3.2's per-call uploads (3C inverse, WB gains) and WP3.3's double high-pass on the
   measure path; WP3.7's owner: BT.601 `smpte170m` primaries resolve as "unexpected" (WP3.5).
   Earlier notes (WP3.9 bounded `-read_intervals`, WP3.10 `-y` on the temporary path, WP3.14 one
   `Reservations`, WP4.3 `remove_leftovers` first) still stand.
5. **Photos:** none supplied yet. Gate 2's largest-photo leg, the photo look check and WP3.6P wait.
6. A stale pytest (pid 37676, wp33-cell's) spun for ~30 min; Stop-Process was refused by the
   classifier at the cell's seat and NOT re-run at this seat; it finished on its own. If it recurs,
   surface to the owner.

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

### Pending (still valid)

- The smoothing default is 2.0 s (v0.5.4 7.2), with the step-aware temporal task for WP3.11;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is its input.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- IF-5 `VideoSink.abort` docstring cites D84; it should be D44/D85 (CHARC: fix at the next
  interface touch, not before).
- Open debt: DR-1, 2, 6, 7, 8, 10-20, 22, 23, 25-31, 33-37 (DR-14 closes at WP3.3's accept) (`docs/debt-register.md`; DR-32 CLOSED at the config boundary).
