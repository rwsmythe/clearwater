# Harness change: dual-model implementers (Claude and Codex), cross-model review, weekly-headroom dispatch

CHARC design pass, 2026-10-27. Status: **Stage 0 and Stage 1 DONE 2026-10-27 (sections 4.1a/4.1b; the Stage 1 commit after main `68e3a2c`); Stage 2 calibration pending the wave 4 briefs.** Originally: WRITTEN UP for the owner; calibration starts this phase
(owner, 2026-10-27: "Start calibration this phase, write up the harness change").** Nothing in the
operating docs changes until the Stage 1 edits below are made; this pass is the argument, the
evidence and the exact edit list, per the dispatch recipe's rule that argument lives in the design
pass and the brief stays a ladder.

## 1. The owner's direction (verbatim, 2026-10-26)

- "I would like to more fully utilize the codex subscription. Right now we just have it as the
  review engine. I would like to generally equalize claude and codex subscription token spend and
  start using it for development as well. If there is one task that is better implemented by claude
  or codex, that task agent should use it regardless of the spend delta."
- "codex reviews claude, claude reviews codex. Claude maintains director and orchestrator roles,
  codex fits in only in implementer/reviewer roles. For equalization, I was thinking more towards
  big-picture weekly token limit. All else being equal, the choice of implementer claude or codex
  comes down to which has more overhead on remaining the weekly allotment (assuming that can be
  pulled for both claude and codex by the orchestrator/director)."

Three rules follow, in priority order: (R1) task fit decides first; (R2) the reviewer is always the
other model from the implementer; (R3) when task fit is equal, the implementer with more weekly
headroom takes the package. Director and orchestrator stay Claude.

## 2. Evidence

### 2.1 The two research notes (`research/multi-model development/`, owner-supplied, untracked)

Both notes, one from each vendor's assistant, land on the same routing: Sonnet-class and Sol-class
models are the implementation workhorses; Opus takes ambiguity, architecture and multi-file
reasoning; Astra is the escalation and independent-reasoning tier; Haiku and Luna take mechanical
work. Points this design uses:

- Codex's recurring weakness is drift, scope creep and style mismatch on loosely specified work;
  its strength is bounded, testable tasks with tight specs. Our gate already refuses exactly that
  failure (owned-files-only footprint, frozen interfaces untouched, the five mechanical review
  assertions), so the exposure is wasted rounds, not bad merges.
- Effort peaks before max on both sides (Sol: high > xhigh = max). A Codex implementer runs at
  high, never above; escalation is to Astra at medium, never Sol at xhigh.
- The cross-model review study (116 tasks, previous generation): Claude reviewing Codex raised the
  pass rate; Codex reviewing Claude LOWERED it when the reviewer rewrote code. Our B is read-only,
  findings-only, adjudicated by the orchestrator; the fix goes through the author's loop with a
  failing-before test. That shape stays mandatory in both directions.
- A controlled study found persistent instruction files did not measurably improve correctness.
  The gate, not a ported cell prompt, is the control on a Codex implementer.
- Terminal-Bench 4.0 (agent + model): Opus 5.5 64.85, Sonnet 5.5 61.82, Codex Astra and Sol 58.18,
  Fable 5.1 57.88. Fable never implements; it stays at the director seat.
- Codex automations can run at medium regardless of global effort; the banner assertion (model and
  effort lines in the transcript) carries over to every Codex implementer run.
- Both notes are silent on subscription quota mechanics; section 2.3 supplies them.

### 2.2 The Codex model catalog at this login (app-server `model/list`, 2026-10-27)

`gpt-6.1-sol` (DEFAULT), `gpt-6-astra`, `gpt-6.1-terra`, `gpt-6-sol`, `gpt-6-luna`, `gpt-5.6-sol`,
`gpt-5.6-terra`, `gpt-5.6-luna`; efforts low/medium/high/xhigh/max (+ultra on all but luna).
**Our Reviewer B pin (`~/.codex/strong.config.toml`, `gpt-5.6-sol` / high) is one generation behind
the catalog default.** The pin is not wrong, and the banner assertion still passes; upgrading it is
a separate gate decision (section 4.6).

### 2.3 Weekly readouts, both confirmed live 2026-10-27 02:41Z

| Subscription | Readout | Used | Window elapsed | Pace | Resets |
|---|---|---|---|---|---|
| Claude (Max 20x) | `GET https://api.anthropic.com/api/oauth/usage` with the Claude Code OAuth bearer token (`~/.claude/.credentials.json`) and `anthropic-beta: oauth-2025-04-20`; fields `five_hour`, `seven_day` (`utilization`, `resets_at`), `limits[]` (session / weekly_all / weekly_scoped Fable = 50 % of weekly), `seven_day_breakdown` | 21 % (Claude Code 97 % of it; Fable scoped 14 % of its own half) | ~10 % (window began 2026-10-26 10:00Z) | **~2.1x** | 2026-11-02 10:00Z |
| Codex (prolite) | native `codex.exe app-server`, JSON-RPC `initialize` -> `initialized` -> `account/rateLimits/read`; `rateLimits.primary = {usedPercent, windowDurationMins: 10080, resetsAt}` | 22 % | ~11 % (window began 2026-10-26 08:03Z) | **~2.0x** (CORRECTED 2026-10-27 03:49Z: the first write-up mis-converted the epoch and said 1.0x) | 2026-11-02 08:03Z |

Both lanes run near 2x pace: wave 3's gates spent a fifth of EACH week in under a day (Claude on
the cells and the director, Codex on the Reviewer A loops and the B passes). Neither coasts; the
case for the change is CAPACITY (two allotments) and the ability to steer spend between them, and
the dispatch rule compares PACE (projected end-of-window utilization), not used percent, because
the two windows reset at different hours and started a day apart.

Access constraints: the Codex read needs no credential handling by an agent. The Claude read uses
the stored OAuth token, which the auto-mode classifier refuses to let an agent touch ("Credential
Exploration"); the owner ran `work/claude_usage_probe.py` by hand. The `codex.cmd` npm shim hangs
under pipes; spawn the native exe
(`%APPDATA%\npm\node_modules\@openai\codex\node_modules\@openai\codex-win32-x64\vendor\x86_64-pc-windows-msvc\bin\codex.exe`).

## 3. The design

### 3.1 Implementer selection (R1 then R3)

- **Opus-class packages** (the `implementer-opus-high` description: reasoning-dense, interface
  design inputs, algorithm prototypes, the analysis engine, encode/mux/timing) stay Claude. Codex
  is never the implementer of a package that designs or touches a frozen interface.
- **Sonnet-class packages** (`implementer-sonnet-high`: well-specified builds whose brief fixes the
  interfaces, algorithms and tests; `implementer-sonnet-medium`: mechanical passes with nothing to
  decide) are ELIGIBLE for either lane. The Codex lane is `implementer-codex-sol-high` (section
  3.3): `gpt-6.1-sol` at high for the sonnet-high class; the same model at medium for the
  sonnet-medium class (Luna is not adopted: 16 % on the agentic benchmark).
- **Tiebreak (R3):** at dispatch the orchestrator reads both figures and computes for each lane
  `pace = used_percent / elapsed_fraction_of_window` (elapsed fraction = 1 - (resets_at - now) /
  window). The lane with the LOWER pace takes the package. A lane whose pace projects above 100 %
  never takes an eligible package while the other projects below. Both readings, the pace figures
  and the choice go in the dispatch row of `docs/orchestrator-state.md` and in the brief's header.
- **Task-fit override (R1):** the orchestrator may name a lane regardless of pace with a one-line
  reason in the dispatch row (e.g. a GUI package with visual judgment -> Claude; a shell/CI/tool
  instrument with a fixed recipe -> Codex). CHARC may rule a lane at brief time.
- **Escalation inside a lane:** a Codex package that stalls on reasoning goes to `gpt-6-astra` at
  medium for ONE re-seat, never to Sol at xhigh; a second stall re-dispatches the package to the
  Claude lane from the ledger. The Claude lane escalates as today (sonnet -> opus).

### 3.2 Reviewer pairing (R2)

| Implementer lane | Reviewer A (the cell's loop) | Reviewer B (orchestrator's own pass at its seat) |
|---|---|---|
| Claude (today's cells) | Codex, unchanged (`docs/codex-reviewer.md`, strong tier) | Codex, unchanged |
| Codex (`implementer-codex-sol-high`) | Claude Opus at high, non-interactive `claude -p` run by the cell's driver (section 3.4) | Claude Opus at high, non-interactive `claude -p` run by the orchestrator as a PROCESS at its seat |

B's form rule (orchestrator-context: "YOUR single-pass adversarial gate at YOUR seat", never a
subagent) holds in both rows: `codex exec` and `claude -p` are both processes the orchestrator
runs, neither is an Agent-tool subagent. Independence holds because the orchestrator wrote none
of the code in either row. The B-independence disciplines (neutral prompt, never from the author's
map; "B stops being productive when the work is good") apply verbatim to the Claude pass. The
reviewer never writes: read-only is enforced by the Codex sandbox in row 1 and by tool policy plus
a post-pass `git status --porcelain` = empty control in row 2.

### 3.3 The Codex implementer cell

- **Cell file:** `.claude/agents/implementer-codex-sol-high.md`, authored from the template with
  the same section order as `implementer-sonnet-high.md` (the instance-surface tests treat any
  `.claude/agents/implementer-*.md` as a domain cell, exempt from the vocabulary bans). Frontmatter
  `model: codex/gpt-6.1-sol`, `effort: high`; the body is the Sonnet cell's contract with the
  Codex-specific disciplines below. It is NOT a Claude subagent; the orchestrator never passes it
  to the Agent tool. The file is the staged preamble of every Codex dispatch.
- **Invocation (pinned after the Stage 0 probe):**

  ```
  cat .claude/agents/implementer-codex-sol-high.md <brief> | \
    codex exec -C <worktree> -m gpt-6.1-sol -c model_reasoning_effort=high \
      -s workspace-write --add-dir <work folder> --skip-git-repo-check \
      -o <worktree>/.codex-return-rN.md - > <evidence>\cell\turn-N.txt 2>&1
  ```

  One `codex exec` run is ONE TURN of the cell: the process exit is the yield. The next turn is
  `codex exec resume <session-id> -` with the dispatcher's ruling or depth figure as the prompt
  (the session id is read from the first turn's transcript). The five-round gate, STOP-and-ask and
  the re-seat line map onto turn boundaries exactly as they do for a Claude cell.
- **Sandbox is a benefit:** workspace-write confines writes to the worktree plus the added
  working folder; the footage folder, outside both, is read-only at the kernel level, a stronger
  control than the Claude cell's prompt lock. The dispatcher still proves the footage path
  untouched at the gate (unchanged GATE_CHECK).
- **Depth:** `scripts/cell_depth.py` reads Claude transcripts only. A Codex cell's figure is the
  `tokens used` footer of each turn plus the session file under `~/.codex/sessions/`; Stage 0
  pins the reading and the ~250K evaluation / ~400K STOP lines are re-expressed in Codex tokens
  (same numbers until measured otherwise).
- **Assertions per turn** (carried from the reviewer doc): banner model `gpt-6.1-sol` and
  `reasoning effort: high`; `^ERROR` classified by provenance; `tokens used` footer; the return
  report delivered as the `-o` file (an absent file is a failed handoff).
- **Commits:** pathspec only, conventional commits with the work-package id, attribution footer
  naming the model. Proposed form: `Co-Authored-By: GPT-6.1 Sol via Codex <noreply@openai.com>`
  (owner decision 6.1; the plan requires the footer to name the model, not a vendor placeholder).
- **Reviewer A for the cell is Claude (section 3.4).** The cell stages the diff and prompt exactly
  as today (`.codex-diff.txt` becomes `.review-diff.txt`; gitignore pattern added) and invokes the
  Claude pass; the evidence folder layout (`rN\` with prompt, diff, transcript, md5s) is unchanged.

### 3.4 The Claude reviewer pass (both rows of section 3.2's Codex lane)

```
cat review-prompt.md .review-diff.txt | \
  claude -p --bare --model opus --effort high \
    --disallowedTools "Edit,Write,NotebookEdit,Agent" \
    --allowedTools "Read,Grep,Glob,Bash(git diff:*),Bash(git log:*),Bash(git show:*),Bash(uv run pytest:*),Bash(uv run ruff:*),Bash(uv run mypy:*)" \
    --output-format json > review-rN.json 2> review-rN.err
```

- `--bare` skips hooks and the project's MCP servers so the pass is a clean process; cwd = the
  worktree at the candidate (the reviewer may read any file); the ledger and the author's report
  are withheld exactly as today.
- Five assertions adapted: (1) the JSON result's model field = the intended Opus model and the
  effort echoed from the invocation (the probe pins the field names); (2) every `error`-typed
  line in stderr classified by provenance; (3) at least one tool execution in the result (the
  pass read or ran something); (4) the usage block present (tokens in/out); (5) `VERDICT:` anchored
  in the final text. (6) NEW for this row: `git -C <worktree> status --porcelain` empty after the
  pass (the reviewer wrote nothing).
- Tiering: strong = Opus high for product code; fast = Sonnet medium for docs and briefs.
- Cost note: a Claude review pass spends Claude's week; on the first reading that is the scarcer
  budget. Section 4.3 measures it; if a Claude B costs more than the Codex package saves, the
  pairing still stands (R2 is the owner's rule) and the dispatch tiebreak absorbs it.

### 3.5 The readouts in the harness

- **Codex:** `scripts/usage_codex.py` (new, stdlib): spawns the native exe, runs the three
  JSON-RPC calls, prints `{used_percent, resets_at, window_mins, pace}`; the orchestrator calls it
  at every eligible dispatch. Harness-core, application-agnostic.
- **Claude:** the token must not be touched by an agent. Two options; CHARC recommends (a).
  (a) A Windows scheduled task under the owner's account runs `scripts/usage_claude.py` every 30
  minutes and writes `comms/.usage-claude.json` (gitignored); `scripts/usage_claude.py` is the
  probe plus the same `pace` field. The orchestrator READS the file; a stale file (older than 2 h)
  is reported as "no Claude reading" and the tiebreak falls back to the Codex lane for eligible
  packages. (b) A project permission rule allowing exactly `Bash(python scripts/usage_claude.py)`
  for the orchestrator session; simpler, but it is a standing credential-read grant to an agent.
- **Both scripts register** in `tests/harness/` (a stdlib parse test on a canned response each,
  no network) and in the launcher's dry-run text if the scheduled task is adopted.

### 3.6 What does NOT change

- Director and orchestrator stay Claude (Fable medium, Opus high). The B form rule, the five
  assertions, the evidence folder discipline, GATE_CHECKS, the accept record, the debt register,
  the one-heavy-job rule, the footage lock and the commit-by-pathspec rule are unchanged.
- The Codex review profile (`strong` = `gpt-5.6-sol` high) stays pinned until section 4.6 is
  decided; the Codex IMPLEMENTER uses `-m`/`-c` per call, never the profile.
- Codex `ultra` effort (auto-subagents) is never used in this harness; the Codex `--worktree`
  flag is not used (the orchestrator owns worktree creation).

## 4. Rollout

### 4.1 Stage 0: probes (CHARC, this week, no product impact)

1. `codex exec` in a scratch worktree with `-s workspace-write`: it edits, runs `uv run pytest -q`
   on one test file, commits by pathspec with the footer, writes the `-o` return file; a write
   outside the worktree and the added folder is REFUSED (the positive control for the sandbox).
2. `codex exec resume <id> -` continues the same session with a second prompt; the transcript
   banner shows model and effort on both turns.
3. Depth reading from the session file; pin the field.
4. The `claude -p` reviewer pass on a finished tree (the WP3.10 candidate is the natural subject):
   JSON field names for model, effort, usage and tool count; the `--bare` flag's effect on the
   project's hooks; `git status` empty afterwards; the one-time head-to-head B-independence
   transition: Codex B and Claude B on the SAME tree, findings compared (free exactly once).
5. `scripts/usage_codex.py` and `scripts/usage_claude.py` with their parse tests; the scheduled
   task created by the owner if option (a) is chosen.

### 4.1a Stage 0 RESULTS (CHARC, 2026-10-27; probes in `.worktrees/probe-codex` and `clearwater-cells/probe-codex`; evidence `clearwater-review-evidence\probes\`)

- **The Codex write lane WORKS under the UNELEVATED Windows sandbox.** The user config's `[windows] sandbox =
  "elevated"` (legacy) fails every command with `helper_unknown_error: setup refresh had errors`; passing
  `-c windows.sandbox="unelevated"` per call gives a working `workspace-write` sandbox: writes inside the worktree
  succeed, and `uv run ruff` runs once the uv cache is a writable root (`--add-dir C:\Users\rwsmy\AppData\Local\uv`).
  The pinned invocation in 3.3 gains both flags.
- **The sandbox protects every `.git` directory**, in a worktree AND in a plain clone: `git add` fails with
  `index.lock: Permission denied`. So the Codex cell CANNOT commit. Rule: the DRIVER (the orchestrator) commits
  after each turn, by pathspec, from the files the return report names, with the footer `Co-Authored-By: GPT-6.1
  Sol via Codex <noreply@openai.com>`; one commit per turn (a limit against the recipe's one-per-logical-change,
  recorded in the cell file). Isolation stays the worktree; a clone buys nothing.
- **An outside write is swallowed SILENTLY:** `Set-Content` to a path outside the writable roots returned
  "succeeded" to the model and produced NO file. Good for the footage lock, bad for trust: a Codex cell's report
  of any effect outside the workspace is unverifiable from inside; the gate's footage-untouched and footprint
  checks stay mandatory and the cell file says so.
- **`codex exec resume <session-id>` accepts NO `-m`, `-s` or `--add-dir`.** Every resumed turn must carry
  `-c model="gpt-6.1-sol" -c model_reasoning_effort=high -c windows.sandbox="unelevated"
  -c sandbox_workspace_write.writable_roots=["..."]`, or the turn silently runs on the GLOBAL config's model
  (observed: `gpt-6-astra`, caught by the banner assertion) under the legacy sandbox. The banner assertion is per
  TURN, not per cell.
- **The auto-mode classifier refused `--dangerously-bypass-approvals-and-sandbox`** ("Create Unsafe Agents");
  not pursued, the sandboxed lane is the design.
- **The Claude reviewer pass:** `--bare` drops OAuth ("Not logged in"), so the pass runs WITHOUT `--bare` (the
  project hooks run; harmless). The `--output-format json` result carries `modelUsage` keyed by the model id
  (assertion 1's model half), `session_id`, `permission_denials`, `num_turns`, `usage`; EFFORT is not echoed, so
  that half of assertion 1 is the invocation record. stdin works from a combined prompt+diff file when the process
  is started DETACHED with redirected stdin (a Claude Code background shell is reaped under memory pressure; a
  detached process is not). The head-to-head on the WP3.20 candidate (the Codex B's own prompt and diff, verbatim)
  was launched 2026-10-27 ~04:02Z; its result is recorded in 4.1b when in.
- **Readouts:** `scripts/usage_codex.py` and `scripts/usage_claude.py` are live and tested
  (`tests/harness/test_usage_readouts.py`), the Claude one under the standing rule
  `Bash(python scripts/usage_claude.py*)` in `.claude/settings.json` (owner, 2026-10-27; main `9c15d0c`). Second
  reading 03:57Z: Claude 22 % at 10.7 % elapsed = pace 2.06; Codex 22 % at 11.8 % = pace 1.87.

### 4.1b The Claude reviewer pass on WP3.20 (2026-10-27 04:02Z-04:11Z; evidence `clearwater-review-evidence\probes\claudeB-wp3.20\`)

- **Form that ran:** `claude -p --model opus --effort high --no-session-persistence --output-format json`, cwd the
  `wp3.20-mc` worktree (head `e47c8d2`), tools Read/Grep/Glob plus `git diff|log|show|status` and
  `uv run pytest|ruff|mypy`, Edit/Write/Agent/web denied; stdin = the Codex B pass 1 prompt and diff verbatim.
  Result JSON: `claude-opus-5-5`, 40 turns, 512 s, 46.5K output tokens, 170K cache-creation, 4.48M cache-read,
  list cost $3.19; `VERDICT: NO_NEW_CRITICAL_MAJOR`; `git status --porcelain` empty afterwards (control 6 passed);
  8 permission denials (grep/python/PowerShell probes and a scratch write under `work/`).
- **Not a same-tree head-to-head, and the pass SAID SO:** the Codex pass 1 diff was against `bbf44e2`, the tree
  was `e47c8d2` (both Codex-found majors already fixed). The pass reconciled the two before reviewing and tagged
  every finding EXECUTED or REASONED as the prompt demands. The strict transition head-to-head (both B's on one
  finished tree) is still owed once, at the first Codex-implemented package's gate.
- **What it found on the accepted tree, none raised by either Codex pass:** six minors and advisories, all in
  envelope and all checked at this seat: a stored over-long or newline suffix bypasses `validate_suffix` through
  the field's truncation (DR-53); a stored encoder the sink now reports UNAVAILABLE is accepted (DR-54); the
  report cites four pre-rebase SHAs and omits `cache_limiter` from the public API (DR-52 errata); the interim
  rule's error behaviour differs from WP3.10's although a test claims they match (DR-52 amended); the injected-rule
  test cannot fail on a restated rule (DR-54 disposition). Reading: the Claude pass is a credible B; it hunts the
  same "what is absent" class, verifies on reality where its tools allow, and reports what it could not execute.
- **Tool policy change for Stage 1:** allow `Bash(uv run:*)`, `Bash(python:*)`, `Bash(.venv/Scripts/python.exe:*)`,
  `Bash(grep:*)`, `Bash(ls:*)` so probes EXECUTE (the Codex sandbox lets its reviewer write to /tmp; the Claude pass
  had no scratch at all); Edit/Write stay denied; the post-pass `git status` control is the integrity check. Cost
  per pass is of the same order as a Codex pass (Codex WP3.20 passes: 160K and 148K tokens).

### 4.2 Stage 1: the operative edits (CHARC, after Stage 0, one harness commit, harness gate green)

| File | Change |
|---|---|
| `.claude/agents/implementer-codex-sol-high.md` | NEW cell file (section 3.3). |
| `docs/review-gate-clearwater.md` Part 1 | `REVIEWER` becomes lane-dependent: Codex for Claude cells (unchanged text), the Claude pass (section 3.4) for Codex cells; the assertions list gains the adapted set and the `git status` control; staging file names generalised. |
| `docs/review-gate-clearwater.md` Part 2 | B's tier/transport line becomes "the OTHER model from the implementer"; the Claude B invocation and assertions; everything else unchanged. |
| `docs/orchestrator-context.md` | Two-net block: a sentence that the reviewer in both nets is the other model from the implementer, pointing at the fill; the dispatch row gains the two readings, the pace figures and the lane. |
| `docs/codex-reviewer.md` | A short "Codex as IMPLEMENTER" section pointing at the cell file and the pinned `codex exec` write-mode invocation; the model catalog note (2.2). Core doc: substrate vocabulary allowed, no application vocabulary. |
| `docs/dispatch-recipe.md` | One sentence in section 0: a cell's turns may be process runs (yield = process exit; resume = the next prompt). Generic, no substrate name. |
| `scripts/usage_codex.py`, `scripts/usage_claude.py`, `tests/harness/test_usage_readouts.py` | NEW (section 3.5); registered in the manifest accounting as support files as that test requires. |
| `.gitignore` | `.review-diff*.txt`, `.codex-return-*.md`, `comms/.usage-*.json`. |
| `CLAUDE.md` "The harness" | One line: implementer lanes (Claude cells, Codex cell), reviewer = the other model, dispatch tiebreak on weekly pace. |
| `docs/charc-state.md`, `docs/decisions.md` | State row; a harness decision row (HD-1) recording the three rules and the calibration outcome when known. |

### 4.3 Stage 2: calibration, this phase

- **Subjects:** the first two Sonnet-class packages wave 4's briefs produce (the orchestrator names
  them at the wave 4 brief; WP3.10, the last wave 3 package, is Opus-class and mid-gate, so wave 3
  is not a subject). One goes to `implementer-sonnet-high`, one to `implementer-codex-sol-high`,
  by CHARC's assignment at brief time (the pace tiebreak is suspended for these two so each lane
  gets one). Briefs of comparable size (ladder lines, owned files, test roster) are preferred;
  if the two differ in size, the ratio is recorded and the metrics are read per ladder rung.
- **Metrics, all from figures the gate already produces:**

  | Metric | Source |
  |---|---|
  | Reviewer A rounds to converge; blocking findings per round; product-code vs test-only rounds | the cell's ledger |
  | STOP-and-ask count and whether each stop carried a reproduction | the ledger and return report |
  | B pass-1 verdict; findings upheld / not upheld / pre-existing | the adjudication table |
  | Footprint and lock violations (owned files, interfaces, dependencies, footage path) | GATE_CHECKS |
  | Full-suite regressions at the candidate gate | pytest output |
  | Tokens per lane (cell turns + its A rounds + its B pass), as a share of that week's window; wall-clock from dispatch to accept | tokens footers, the readouts, timestamps |
  | Scope discipline: unrequested changes removed at review | the ledger's reverts column |

- **Decision rule after both accepts (CHARC rules, owner informed):** the Codex lane STAYS for
  the sonnet-high class if its package reached accept with no more than one extra Reviewer A
  round and no more B-upheld blocking findings than the Claude package, and no lock violation.
  Otherwise the Codex lane is restricted to the sonnet-medium class (mechanical passes) for one
  more calibration package before CHARC rules again. The outcome and figures go in HD-1.

### 4.4 Stage 3: template port (`rwsmythe/harness-template`)

The owner's call, as for the reaper launcher change. The portable pieces are the Codex cell
template, the readout scripts, the lane-dependent reviewer wording in the seam fill pattern, and
the dispatch-recipe sentence; the instance-specific pieces (model names, the Clearwater cell body)
stay here.

### 4.5 Risks and mitigations

- **Windows reliability of long Codex runs** (stalls and oversized requests reported on the 0.153
  line; we run 0.162.1): a cell turn with no transcript growth for 20 minutes is a BLOCKED
  condition the dispatcher handles like a missing MCP tool; the first calibration package doubles
  as the reliability probe.
- **Drift and scope creep:** caught by the footprint GATE_CHECK and B; the Sonnet cell rule "the
  brief states scope and out-of-scope literally" applies doubly to the Codex cell.
- **Silent effort downgrade:** the banner assertion per turn; an unknown `-p` profile is never
  used (per-call `-m`/`-c` only).
- **Claude B cost on the scarcer budget:** measured in 4.3; R2 stands regardless.
- **Two windows, two reset times:** the pace formula, never raw percent; a missing reading falls
  back as 3.5 states.

### 4.6 A separate decision: the Codex review pin -- DONE 2026-10-27 (owner: "We also need to update the reviewer codex invocation, it sounds like the model versions are out of date")

Moved the same day, not at the wave boundary: `strong` = `gpt-6.1-sol` / high, `fast` = `gpt-6-luna` /
medium, in `~/.codex/{strong,fast}.config.toml` on Windows and on WSL (the WSL `review-strong` /
`review-fast` profiles belong to the sibling harnesses and still pin `gpt-5.5` / `gpt-5.4-mini`, names
ABSENT from this login's catalog; left alone here, flagged to those harnesses' CHARCs); the fill's per-call `-m` and the banner assertion value in
`docs/codex-reviewer.md` follow. Both transports gave `model: gpt-6.1-sol` / `reasoning effort: high`
on codex-cli 0.162.1. WP3.10's two B passes ran on the old pin and stand. The transition
head-to-head (same tree `bbf44e2`, same prompt and diff as the WP3.20 B pass 1 of 2026-10-26, WSL
transport) is recorded below when in. The original recommendation follows for the record.


`strong` = `gpt-5.6-sol` is one generation behind the catalog default `gpt-6.1-sol`. CHARC
recommends upgrading the pin at the wave 4 boundary, with the B-independence transition
head-to-head run once (old pin and new pin on the same finished tree, the WP3.10 candidate if its
gate is still open, else the first wave 4 accept), and re-probing the banner values on the new
model. Not before: changing B's model mid-gate changes the net under a package in flight.

## 5. Decisions needed from the owner -- ALL DECIDED 2026-10-27

Owner, 2026-10-27, verbatim: "Concur with attribution footer; I am ok with the standing permission rule; concur with the pin upgrade; we will port to the template once we have execution experience to verify the changes are positive." So: (1) footer `Co-Authored-By: GPT-6.1 Sol via Codex <noreply@openai.com>`; (2) the Claude readout runs under a standing project permission rule for `scripts/usage_claude.py` (option (b)); (3) the review pin upgrades to `gpt-6.1-sol` at the wave 4 boundary with the one-time head-to-head; (4) the template port waits for calibration experience. The questions as they were put:

1. **Attribution footer for Codex commits:** `Co-Authored-By: GPT-6.1 Sol via Codex
   <noreply@openai.com>` (CHARC's proposal) or another form.
2. **Claude readout access:** scheduled task writing a file (CHARC recommends) or a standing
   permission rule for the orchestrator session.
3. **The Codex review pin upgrade** to `gpt-6.1-sol` at the wave 4 boundary (CHARC recommends yes).
4. **Template port** (Stage 3): now, after calibration, or not at all.

Everything else in this pass is within CHARC's harness authority and proceeds on the owner's
"start calibration this phase" direction: Stage 0 begins now; Stage 1 lands before the wave 4
briefs; Stage 2 runs on the first two Sonnet-class wave 4 packages.
