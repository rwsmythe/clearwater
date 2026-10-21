# Orchestrator -- Current State (the read-me-FIRST pointer)

> Overwritten each generation; history lives in `git log -- docs/orchestrator-state.md`.
> Every fact carries the method that re-verifies it.

### Generation

- **Generation 7** (`clearwater-orchestrator-20261020-1419`) ROLLED OVER 2026-10-21 near the depth
  cap. **Generation 8 starts here** (verify: `comms/.launch-sessions.json`). Earlier: gen 6
  `clearwater-orchestrator-20261020-1134`, gen 5 `-20261020-0802`, gen 4 `-20261020-0524`, gen 3
  `-20261019-2346`, gen 2 `-20261018-1442`, gen 1 `-20261014-1258`.
- **Inbox:** gen 7 drained through CHARC's WP3.12 AD-5 ruling (`919a415a27f0f0a7`, 00:33:44Z) and
  STOPPED DRAINING at its rollover announcement. You are the sole drainer (verify:
  `uv run python scripts/role_mail.py list --role orchestrator`).
- **CHARC is generation 2:** `clearwater-charc-20261020-0636`. Cue that exact name.
- Bash-launch gauge at gen-7 bring-up: 36.7 ms. Re-measure at yours.
- **GEN 8 LIVE (`clearwater-orchestrator-20261020-1556`, picked up 2026-10-21 ~01:56Z; gauge 37.0 ms;
  host 9.5 GB free of 31.2).** Online posted to CHARC (acked `fda55fee1cbb0cf4`). CHARC ruled the
  WP3.6 ICC scope (`aa1219fb3145208b`, 01:58Z): built-in profiles for nclx sRGB/P3 sources only;
  untagged keeps Q3 (no `iCCP`); out-of-set nclx no `iCCP`; "no output ever lacks iCCP" WITHDRAWN.
  Re-dispatched ~02:00Z (the gen-7 table below is the PRE-dispatch record): `wp312-cell3`
  (sonnet-high; R4 fixes then R5, yield at the five-round gate), `wp36-cell2` (sonnet-high; ICC
  rulings, then WINDOW REQUEST, then A R1), `wp316-cell2` (opus-high; Essentials + S3 RULED, then
  WINDOW REQUEST, then A R1).
- **GEN 8 PROGRESS (2026-10-21 ~04:42Z):** WP3.12 and WP3.6 ACCEPTED (stacked gate; main `4ec835d`,
  3440 passed; records `docs/proofs/wp3.{12,6}-accept.md`; DR-41, DR-42; both Reviewer Bs
  adjudicated at the gate on pass 2). Return report + MAIN RELEASED posted to CHARC (04:40Z);
  operator FYI posted. The first stack run was memory-REAPED (~03:50Z); CHARC approved a restart one
  job at a time (`2e6feaf538c411f4`); a second reap means STOP and ask the owner for a quiet block.
  `wp3.16` REBASED onto main (`6a65145`; old head `wp3.16-pre-rebase` `b8fa742`); Reviewer A
  CONVERGED at R4; fresh cell `wp316-cell3` (opus-high, dispatched ~04:42Z) doing the R4-1..3
  cleanup + by-name `PhotoReadError` catch, no A round; then Reviewer B at this seat and its own gate
  (main's venv: `uv sync --reinstall-package pyside6-essentials --reinstall-package shiboken6` after
  the merge). Retired: `wp312-cell3` (246,012), `wp36-cell2` (222,405), `wp36-cell3` (236,865),
  `wp316-cell2` (266,869). Worktrees `wp3.12`, `wp3.12-mc`, `wp3.6`, `wp3.6-mc`, `wp3.6-mc2` to
  remove after CHARC QA.

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

### Live cells at the gen-7 rollover (they died with gen 7; re-dispatch from the ledgers)

| Cell | Package | State at rollover | Your action |
|---|---|---|---|
| `wp36-cell` (sonnet-high) | WP3.6 photo I/O | Dispatched 01:20Z from main `4b4da9b`, worktree `.worktrees/wp3.6`, branch `wp3.6`. R0 table committed and RULED (depth 96,178 / 18 turns at the R0 yield): table accepted; item 1 `errors.py` + `__init__` export + test FIRST (X-B2, so WP3.16 can cherry-pick it); item 2 (an nclx-only Display-P3 HEIC: embed a built-in Display P3 ICC profile in the output PNG) ruled PROVISIONALLY and built ISOLATED in its own commit, pending CHARC (asked in the release post); notes accepted (LZW / JPEG-in-TIFF refused by name; Zstd ModuleNotFoundError -> "unsupported"; HEIC 12-bit refused; HLG/PQ nclx -> transfer "unknown"; ICC classification by a stdlib tag reader -- report the deviation from question 4's wording); `tifffile` + Pillow to `[project]` (X-B3), `uv lock`. **BUILD COMPLETE, CHECKPOINTED** at `9662282` (ledger "State at the orchestrator gen-7 rollover -- resume here"; build `5636ed0`: `PhotoReadError` first in `748ac75`; the provisional P3 ICC isolated in `23fdfd9`; `pillow` + `pillow-heif` moved to `[project]`, `tifffile>=2025.1,<2027` added, re-locked; `PhotoReader` / `PhotoWriter` on IF-6 unchanged; `tools/photo_check.py`; report `docs/reports/wp3.6-photo-io.md`). Photo tests 376 passed, 1 skipped (footage leg); 48 MP PNG16 read 10.6 s / 1.67 GiB peak, write 11.1 s (informational). Depth **300,809 / 107 turns** at 01:44:00Z (past the evaluation point). It asked for a WINDOW before Reviewer A. | Re-dispatch a FRESH sonnet-high cell from the ledger: first apply CHARC's 01:32Z conditions (item 8 below: the built-in sRGB profile for sRGB nclx sources too, md5-pinned profiles, provenance line; check against question 3), then the full-pytest window (one at a time, host memory-tight), then Reviewer A, yielding at each round BEFORE remediating. |
| `wp316-cell` (opus-high) | WP3.16 app shell | Dispatched 01:20Z from main `4b4da9b`, worktree `.worktrees/wp3.16`, branch `wp3.16`. R0 committed (`d754a98` deps `pyside6>=6.12,<7` + `pytest-qt>=4.5,<5` re-locked; `795e57f` `gui/__init__.py` + `contract.py` FROZEN; `3de47f8` ledger) and RULED at 152,774 / 35 turns: table and contract accepted (`position_changed = Signal(object)` deviation stated in the report); S1 `default_engines` estimates an id outside `core.METHOD_IDS` as "c3" (stub-era adapter WP4.3 removes); S2 photo errors by `kind` until WP3.6 merges; S3 downscale rule PROVISIONAL (edge blocks average the pixels they cover, ceil(H/k) x ceil(W/k), proxy k = max(1, short // 540): 540 at 4K, 605 at 12 MP, 598 at 5.3K), with CHARC; S4-S7 as recommended; `pyside6` kept as granted, PySide6-Essentials with CHARC. **BUILD COMPLETE** at `614fc5d` (report and ledger build section): contract names unchanged (only the `JobRunner.run` coalescing docstring); job progress reaches the main thread by a 50 ms poll; V7 worst gap 11-12 ms (bound 100 ms, informational); V8 harness exact with the identity stub; 1:1 bit-exact; the gpu test ran ("Device: GPU"); 90 GUI tests headless ~14 s; ruff / format / mypy clean. Open for WP4.3: a pure-Python GIL-holding job gave 216-796 ms gaps (out of envelope, in the report). Commit `fda06b7`'s subject "(V7)" overstates (report and ledger correct it). Depth **317,238 / 109 turns** at 01:55:13Z. It asked for a WINDOW before Reviewer A; CHECKPOINTED at `a702a4d` (ledger "State at the orchestrator gen-7 rollover -- resume here"). | Re-dispatch a FRESH opus-high cell from the ledger: first apply CHARC's 01:32Z ruling (PySide6-Essentials replaces `pyside6`: one line + `uv lock`, re-run the GUI tests), then the full-pytest window (one at a time), then Reviewer A, yielding at each round BEFORE remediating. |
| `wp312-cell2` (sonnet-high) | WP3.12 proxy cache | STOOD DOWN at 283,367 / 108 turns (R4 yield). Branch `wp3.12` head `2b486a0` (its last ledger line: the R4 ruling and the stand-down). Report done (`1b4da4e`), CHARC's AD-5 ruling applied in the report. Reviewer A: R1 4M/7m, R2 2M/2m, R3 3M/1m (all fixed; R2 and R3 remediated before my rulings landed: two recorded yield breaches); R4 on `9b2890d`: 3 major (R4-1 reopened family: failed discovery removal untracked, `_entry_for_write` leaves a stale `complete`; R4-2 torn sole proxy keeps the shape lock; R4-3 instrument run identity) + 1 minor (R4-4 constructor codec vs `CODECS`), adjudicated, NOT remediated; planned fixes in the ledger. **No full suite has run on any WP3.12 head.** | Dispatch a FRESH sonnet-high cell on `wp3.12` for the R4 remediation from the ledger, then Reviewer A ROUND 5 (the FIVE_ROUND_GATE applies: continue only if new in-envelope non-reopened blocking findings keep arriving AND the fixes change product code), yield BEFORE remediating; then grant the full-pytest window (normal + cupy-unimportable). Tell it: never `git stash` (shared; the last cell used it four times). |

Retired this generation: `wp32-rem` (WP3.2 B remediation; 109,633 at its last return).

### Where things stand -- the successor starts HERE

1. **Accepted this generation (stacked gate, re-ordered after WP3.2's B remediation):** WP3.3
   (`09d1d11`), WP3.5 (`55c266d`), WP3.2 (`4b4da9b`), main gates filled in `68a8d93`. Records
   `docs/proofs/wp3.{3,5,2}-accept.md`. DR-14 CLOSED; DR-20 (1) CLOSED; DR-38, DR-39, DR-40 NEW.
   Return report + main release posted to CHARC (`charc/inbox/20261021T013038Z-orchestrator-main-released-...`, with three queries: WP3.6 nclx-only P3 ICC, WP3.16 S3 downscale rule, PySide6-Essentials); CHARC QA CONFIRMED (`075a686775a95772`, ~01:50Z; CHARC's own pytest was host-killed for memory
   pressure, the main run here is the figure of record). The nine worktrees are REMOVED (branches kept).
   **Host is memory-tight: full-pytest windows strictly one at a time.**
2. **WP3.12:** the table row above.
3. **Tranche B:** the two rows above. Window queue (X5): nobody holds a window; WP3.12's first
   window and tranche B's windows are serialised (one full pytest at a time; the suite is now
   ~2900 tests, 15 min normal + 10 min cupy-unimportable).
4. **X-B3 lock merges:** WP3.12 (Pillow to `[project]`), WP3.6 (Pillow, pillow-heif, tifffile),
   WP3.16 (PySide6, pytest-qt) all edit `pyproject.toml` / `uv.lock`; whichever merges second
   and third rebases and re-runs `uv lock` (never a hand merge) and says so.
5. **Consumer notes for later briefs (still valid):** WP3.11 measures on the STORED round-tripped
   proxy only, a second concurrent store on a key is a RuntimeError, spec 7.2 line 325 reads
   single-clip; WP3.10 cites DR-17 and WP3.5's `ffmpeg_color_names`; WP3.21 gets WP3.2's per-call
   uploads (DR-40 b), WP3.3's double high-pass on the measure path and three host reads per
   frame on the two-input path (DR-38 a); WP3.4 gets DR-38 (a)(b)(d) and DR-40 (a); WP3.9 /
   WP3.10 get DR-39; WP3.7's owner: BT.601 `smpte170m` primaries resolve as "unexpected".
   Earlier notes (WP3.9 bounded `-read_intervals`, WP3.10 `-y` on the temporary path, WP3.14 one
   `Reservations`, WP4.3 `remove_leftovers` first) still stand.
6. **Photos:** none supplied yet. Gate 2's largest-photo leg, the photo look check and WP3.6P wait.
7. **AD-5 wording:** CHARC amends AD-5 on main after the release (q75 stays, the 10 GB bound
   read on the median frame size; the stored proxy's N{} range differs by up to 10 % of the range
   of EITHER sign, median slightly wider).

8. **CHARC rulings of 01:32Z (`d06ed7c969d6249f`; AD-5 and AD-18 updated on main `d971ee7`) -- NOT yet relayed to any cell; relay them in the re-dispatch prompts:**
   - WP3.6: the built-in Display P3 ICC is RULED YES with conditions: used ONLY when the source carries no ICC (a source ICC is still copied byte-identical); the built-in profile's bytes pinned by a test (md5); provenance records "profile: built-in Display P3"; **sRGB nclx sources get a built-in sRGB profile the same way, so no output ever lacks `iCCP`** (new scope for the cell; check it against the brief's question 3, the untagged photo, and STOP to CHARC if they conflict). Keep the isolated commit. No `imagecodecs` grant.
   - WP3.16: S3 RULED (k = max(1, short // 540), edge blocks average the pixels they cover, ceil(H/k) x ceil(W/k); 605 at 12 MP, 598 at 5.3K accepted; one function, WP3.14/WP4.1 and V8's area average cite it). **PySide6-Essentials replaces `pyside6`** (AD-18 amended): one `pyproject.toml` line plus `uv lock` in WP3.16. S1, S2, S4-S7, `Signal(object)` upheld.
   - WP3.12: the five-round gate at round 5 reads the ledger's REOPENED column (R4-1 is a reopened family); the two yield breaches and the stash use go in the accept record.

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

Kept branches (evidence; do not delete unasked): `wp3.2`, `wp3.2-mc`, `wp3.2-mc2`, `wp3.3`, `wp3.3-mc`, `wp3.3-mc2`, `wp3.5`, `wp3.5-mc`, `wp3.5-mc2`, `wp3.15`, `wp3.15-mc`, `wp3.13`, `wp3.13-mc`, `wp3.7`, `wp3.7-mc`, `wp3.1`, `wp3.1-mc`, `wp2.3`, `wp2.3-mc`, `wp2.2`, `wp2.2-mc`, `wp1.2b`, `wp1.2b-b1`, `wp1.3d`, `wp1.3d-b1`,
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

### Pending (still valid)

- The smoothing default is 2.0 s (v0.5.4 7.2), with the step-aware temporal task for WP3.11;
  the WP1.4b lighting-step finding (a genuine step at 0.90 s in GX011600) is its input.
- No `.LRV`/`.THM` exist (owner); D60 handled in v0.5.2.
- `_windows_power()` in `bench.py` is instrument-only (CHARC); never into `src/clearwater/`
  without a fresh ruling.
- IF-5 `VideoSink.abort` docstring cites D84; it should be D44/D85 (CHARC: fix at the next
  interface touch, not before).
- Open debt: DR-1, 2, 6, 7, 8, 10-13, 15-20 (DR-20 item 1 CLOSED), 22, 23, 25-31, 33-40 (DR-14 CLOSED at WP3.3) (`docs/debt-register.md`; DR-32 CLOSED at the config boundary).
