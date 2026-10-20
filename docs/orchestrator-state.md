# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 3 LIVE**, session `clearwater-orchestrator-20261019-2346` (verify:
  `comms/.launch-sessions.json`); online at bring-up on main `fa6c41f`. Bash-launch gauge at
  bring-up: 37 ms (under the 1 s flag; re-measure with PowerShell
  `Measure-Command { & $env:CLAUDE_CODE_GIT_BASH_PATH -c true }`).
- Generation 2 (`clearwater-orchestrator-20261018-1442`) rolled over 2026-10-20 ~09:55Z at its
  400K cap, nothing in flight. Generation 1 was `clearwater-orchestrator-20261014-1258`.
- **Inbox:** generation 3 is the sole drainer; at bring-up 0 unread, 64 read (generation 2 drained
  through `257db38e6727db20`). Verify: `uv run python scripts/role_mail.py list --role orchestrator`.

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

- **`wp21s-cell2`** (implementer-opus-high, STRONG): WP2.1S successor, worktree `.worktrees/wp2.1s`,
  branch `wp2.1s`, from handoff `c6a70f9`; dispatched 2026-10-20 ~11:19Z. Scope: photo leg (claim 2),
  licences (claim 3), report sections 8-9, full suite, Reviewer A over the whole package. No timed
  window (the transport leg is closed). Depth at dispatch: 0.
- `wp21s-cell` RETIRED 2026-10-20 at 257K (95 turns) after closing the transport leg (6 clean
  windows, ~60/120 machine min) and the CHARC rulings (`871d4f17e78c10b3`); stood down. Do not
  message it again.
- Every generation-2 cell is retired; do not message any of them (`wp12b-cell`, `wp13d-cell`,
  `wp13d-cell2`, `wp13d-cell3`, `wp14b-cell`, `wp14b-cell2`).

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
3. **WP2.1S (transport and photo I/O spike) DISPATCHED.** Brief FINAL `docs/briefs/wp2.1s-brief.md`
   (`aa1f5f0`; draft `07339bc`; CHARC approval and rulings `5152ed4302874889`: `av` granted into
   dev, no pypng (stdlib PNG writer, else STOP), no exiftool, Part B best-effort covers the
   exclusive leg, exact pts per transport row). Closes AD-2 and AD-17, confirms AD-18
   (architecture DRAFT 0.1, `a27a6f7`). On return: QA, Reviewer B at this seat, accept.
   CHARC holds WP2.2-2.4 until WP2.1S returns (`fa9d637063376263`).
4. **Next for this seat otherwise:** nothing until CHARC directs. After CP3: Phase 2. WP2.1 (architecture
   document and decisions) is the architect's (CHARC); the orchestrator's likely next packages are
   WP2.2 (interface module) and WP2.3 (shared test fixtures) after WP2.1, and WP2.4 briefs with CHARC.
   Wait for CHARC's commission; do not start Phase 2 work unasked.
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
- **Memory pressure:** the host stopped background test runs on 2026-10-19 for low system memory;
  do not restart a killed run on your own; ask.

### Pending (still valid)

- WP1.6: the smoothing row reads "2 s provisional, re-measure per DR-25(3)", never a settled 2 s;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is input to a
  step-aware temporal design in Phase 2.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- Open debt: DR-1, 2, 6, 7, 8, 10-20, 22, 23, 25-30 (`docs/debt-register.md`).
