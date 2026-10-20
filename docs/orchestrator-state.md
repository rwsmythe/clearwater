# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 4** (`clearwater-orchestrator-20261020-0524`) is LIVE since 2026-10-20 ~15:25Z
  (verify: `comms/.launch-sessions.json`). Earlier: gen 3 `clearwater-orchestrator-20261019-2346`
  (rolled at 400K), gen 2 `clearwater-orchestrator-20261018-1442`, gen 1
  `clearwater-orchestrator-20261014-1258`.
- **Inbox:** gen 4 is the sole drainer; drained through CHARC `4f11a18fc46c9fc4` (WP2.2 QA).
- Bash-launch gauge at gen-4 bring-up: 34 ms.

### Standing operator rulings

- **Unattended operation** (owner, 2026-10-14; CLAUDE.md "Roles"): every operator-bound question
  goes `--to charc` (type query, recommended answer first, one cross-session cue after posting).
  CHARC answers in the operator's stead except plan s.3 owner-reserved items ("HOLD <item>": pause
  that item, continue the rest). Info-updates (`--type fyi`) to the operator after each accept. No
  AskUserQuestion from this seat.
- **Spec v0.5.3** (D16: 3C default; chapter handling deferred to v2). Plan v1.1. Cite v0.5.3.
  The prototype `Params()` default IS c3 since WP1.4b (`b23bad9`).
- **GoPro IMU and GPS are OUT OF SCOPE** (owner 2026-10-19 via CHARC `01500d3574412e69`): no brief
  reads ACCL/GYRO/GRAV/CORI/IORI/GPS. Nothing from a `gpmd` track is ever committed (it carries the
  owner's dive sites).
- **Cell depth** (owner 2026-10-19/20; kernel: `docs/orchestrator-context.md` hazard (6), CHARC
  `5692485`): read `uv run python scripts/cell_depth.py <cell>` at dispatch, at every yield and
  before any ruling; record each figure with its moment; read depth AND head twice across a turn
  boundary. **~250K is an EVALUATION point** (bounded remaining work continues; a large or
  open-ended load goes to a fresh cell); **~400K STOP** and re-dispatch from the ledger.

### Live cells

- **`wp23-cell2`** (implementer-sonnet-high, STRONG): WP2.3 successor, R2 onward, worktree
  `.worktrees/wp2.3`, branch `wp2.3`, from head `d495b57` (R1 closed, 11/11 fixed), dispatched
  2026-10-20 ~16:37Z, depth 0 at dispatch. It applies CHARC's R1 ruling `ef7b272564ddeb9d`
  (AD-14 centre track; the readable conditional conftest line; NEW `.gitattributes`
  `tests/fixtures/** -text`) and yields at R2's verdict BEFORE remediating.
- `wp23-cell` RETIRED at its R1 yield: 216,593/62 mid-build, 379,109/145 mid-remediation (it ran
  R1 and remediated without yielding), 406,816/164 at the yield (PAST CAP); stood down 16:34Z.
  The accept record must say so (CHARC: the corrective is an explicit R1 yield in the brief).
- CHARC rolled to generation 2 (`clearwater-charc-20261020-0636`) at 16:36Z. Owner word
  ~16:00Z: Gate 1 option C, caps kept, spec v0.5.4 approved (`9cf16c5`, `3eca7bd`;
  architecture FINAL 1.0). Wave-1 briefs (WP3.1/3.7/3.13/3.15) APPROVED (`47b9738`); at FINAL
  each cites v0.5.4 + architecture 1.0 (drop "proposed"), fills WP2.3 manifest ids (X3), and
  WP3.1 gets the one-line Gate 1 section (IF-2 ops written so WP3.21 can keep arrays
  device-resident; no implicit host copies). All four dispatch once WP2.3 merges; serialise
  full-pytest gate windows (X5).
- Retired (never message): `wp23-cell`, `wave1-drafter`, `wp22-cell`, `wp21s-cell`, `wp21s-cell2`, `wp21s-cell3`, the gen-2
  cells. The wp2.2 worktrees are removed; branches `wp2.2`, `wp2.2-mc`, `wp2.1s`, `wp2.1s-mc` are
  kept as evidence.

### Where things stand -- the successor starts HERE

1. **Phase 1 (prototype gate) is complete.** All six N5 results are in. CHARC wrote the WP1.6 gate
   report (`docs/reports/wp1.6-gate-report.md`, draft `a0c87d2`); generation 2 fact-checked every
   figure (4 mismatches, 4 imprecisions, 3 advisories) and CHARC applied all of them (`4d40f49`,
   `b02ab34`; CHARC `257db38e6727db20`). D109 (sparse analysis) stays NOT named, on the corrected
   2.3-2.9 min/min figure.
2. **Gate 1 (N6 speed) is with the OWNER** as a decision request from CHARC: options A (tune N6 to
   ~25 min/min), B (optimise first), C (both; CHARC recommends: interim N6 25 min/min, transport
   choice at WP2.1, optimisation package in Phase 3, final tune at WP5.2). Gate result 4 (KEEP the
   caps) awaits the owner's confirmation at CP3. The gate record is final when the owner's word is
   recorded and the fact-check attached.
3. **WP2.1S ACCEPTED** (main `a866f06`); CHARC QA CONFIRMED (`9fb52c00bbb58a9b`). AD-2/17/18 are
   closed and AD-23/24 logged (`3591e80`).
4. **WP2.2 ACCEPTED 2026-10-20, main `b288533`** (record `docs/proofs/wp2.2-accept.md`; DR-32).
   IF-1 to IF-10 are FROZEN (AD-20). The return report went to CHARC (return_report, thread
   wp2.2, 15:23Z), with the hold on main released.
   - DONE by gen 4: 892 passed on main (record row, `da074f4`); CHARC QA CONFIRMED; wp2.2
     worktrees removed; WP2.3 brief FINAL and dispatched (see Live cells).
   - **WP2.3 notes:**
     - The manifest uses WP2.2's `Fault` kinds (`src/clearwater/interfaces/video.py`: seven
       kinds, severity refuse/warn/exclude).
     - The brief allows ONE `pytest_plugins` line in `tests/conftest.py`.
     - The flicker clip is procedural, 960x540 FFV1, generated into `work/`; its decoded-frame
       hash is checked against the manifest.
     - Size limits: no committed file over 2 MB; `tests/fixtures/` under 10 MB.
   - Then WP2.4 (Phase 3-5 briefs and spec v0.5.4 for CP4) is CHARC's with this seat. Wait
     for CHARC's commission.
5. **Photos:** none supplied yet. Gate 2's largest-photo leg and the photo look check stay PENDING
   until the owner supplies photos.

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

Kept branches (evidence; do not delete unasked): `wp1.2b`, `wp1.2b-b1`, `wp1.3d`, `wp1.3d-b1`,
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

### Pending (still valid)

- WP1.6: the smoothing row reads "2 s provisional, re-measure per DR-25(3)", never a settled 2 s;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is input to a
  step-aware temporal design in Phase 2.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- Open debt: DR-1, 2, 6, 7, 8, 10-20, 22, 23, 25-32 (`docs/debt-register.md`).
