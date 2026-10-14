# Codex Reviewer -- an OPTIONAL `REVIEWER` plug-in reference

A stocked-toolbox reference for the review/gate seam's `REVIEWER` extension
point: how to incorporate Codex as the adversarial reviewer on this Claude Code
+ WSL/Windows substrate. **This is ONE optional mechanism, not THE reviewer.** A
non-software domain plugs a different reviewer and ignores this file; the core
review/gate contract (`review-gate-seam.md`) stays mechanism-agnostic and never
references this file.

## Transports + liveness probe

**TWO working transports exist; they differ in APPROVAL SEMANTICS, not
reliability.** (Corrected 2026-08-08: this doc previously called the MCP
transport "unreliable here" -- FALSE. The observed prompting was codex's own
approval fallback, not a transport fault; two strong-tier gating passes ran
cleanly over MCP once parameterized.)

- **PINNED for implementer cells: the Windows-native CLI, Git-Bash-direct**
  (the Staging section below). `codex exec` is NON-INTERACTIVE by construction
  -- no approval parameter to forget, which is exactly why cells never hit the
  prompting. Probe liveness FIRST: `codex --version` from Git Bash (any
  `codex-cli <version>` line proves it; use `--version` as the proof, never
  `command -v codex`).
- **The in-editor MCP transport** (`mcp__plugin_copowers_codex__codex` /
  `-reply`) is VALID at a director/orchestrator seat -- but it is INTERACTIVE
  BY DEFAULT: `~/.codex/config.toml` sets no `approval_policy` key and a global
  `sandbox = "elevated"`, so an MCP session falls back to asking on EVERY shell
  command (these prompts are codex's own, NOT the harness permission system --
  the tools are already allowlisted). **Pass `approval-policy: "never"`
  TOGETHER WITH `sandbox: "read-only"` PER CALL** -- read-only is what makes
  never-ask safe (the reviewer reads and probes but cannot write). **NEVER fix
  this by editing `~/.codex/config.toml`** -- it is user-level and shared with
  the operator's other projects; a global `approval_policy` would loosen
  behaviour far outside this repo.
- **Troubleshooting: a DISCONNECTED codex MCP server produces the
  review-handoff stall shape exactly** (a cell idle at the gates/review
  handoff, holding a finished result) -- check MCP server status FIRST on any
  recurrence. The cell-side rule (poll-never-await; a missing MCP tool is a
  BLOCKED report, never a wait) lives in the seam-2 cell files (`5d5f34d`).
- The WSL probe, HISTORICAL FALLBACK only (the PATH prefix is required so
  Codex resolves the native binary, not a dead shim):
  `wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; codex --version'`

## Review tiering (by blast-radius of a MISSED finding)

Tier the model + reasoning effort by the blast-radius of a *missed* finding, NOT
by task difficulty:

- a **strong** tier (strong model + high effort) for any production-code /
  high-blast-radius review -- never tier this down;
- a **fast** tier (cheaper model and/or lower effort) for plan / doc / low-blast
  reviews.

Mechanism: add `-p <tier>` to the `codex exec` command (a Codex *profile*
layered over the base config). **The profiles are CONFIGURED (2026-07-22,
operator-directed; mapping per the OpenAI model docs
developers.openai.com/api/docs/models/all):** `strong` = `gpt-5.6-sol` / high
effort (sol = "frontier model for complex professional work"; gating and
production-code reviews -- `-p strong` is REQUIRED for them, never omitted);
`fast` = `gpt-5.6-luna` / medium (luna = "optimized for cost-sensitive
workloads"; plan / doc / low-blast rounds). `gpt-5.6-terra` (the
intelligence/cost balance) is unassigned -- adopt it only via a deliberate tier
decision. Current Codex CLIs take profiles as PER-PROFILE FILES
(`~/.codex/<tier>.config.toml`), not a legacy `[profiles.*]` table in
`config.toml` (the table now ERRORS). The files live in the WINDOWS `~/.codex`;
if the WSL codex path is revived, mirror them into the WSL-side `~/.codex` (a
separate home). **Fallback:** if a named profile is missing at a new seat,
recreate the file -- do NOT silently omit `-p` for a gating review. Tier the
model/effort, NEVER the rigor -- and tier from the MODEL DOCS, never from an
indirect signal (a token-burn probe misread luna as the deep tier once).

**Command form (codex-cli 0.145.0+):** `-p <tier>` must PRECEDE the `review`
subcommand, and `--base` cannot combine with a custom prompt. The working gating
form: `codex exec -p strong review -` with the lens prompt piped via stdin (the
review subcommand auto-detects the branch diff). The older
`codex exec review -p strong --base master` form FAILS on current CLIs.

## Staging -- THE PINNED IMPLEMENTER-CELL INVOCATION (verified 2026-07-24)

**PRIMARY PATH: Git-Bash-direct, Windows-native.** The Windows codex CLI
(`codex-cli` 0.145.0+, on PATH via npm) runs non-interactively from Git Bash
end-to-end -- verified live at the CHARC seat (profile layered, clean
completion). An implementer cell with the Bash tool invokes it DIRECTLY; no
WSL, no PATH wrapper, no detach-checkout:

  ```
  # from the worktree root; prompt staged OFFLINE in a file (never inline --
  # shell-quoting/backtick traps); output to a file:
  git diff -U8 <base>..HEAD > .codex-diff.txt          # gitignored
  cat review-prompt.md .codex-diff.txt | \
    codex exec -p strong -s read-only --skip-git-repo-check - \
    > .codex-review-r<N>.txt 2>&1
  ```

- `-p strong` is REQUIRED for every gating/production review (`-p fast` =
  cheap probe/doc rounds only). Profiles are per-profile FILES
  (`~/.codex/strong.config.toml`) in the WINDOWS home; `-p <name>` layers
  `$CODEX_HOME/<name>.config.toml` on the base config.
- `--skip-git-repo-check` + a pre-generated diff stays the safe default in a
  WORKTREE. Windows-native codex reads the Windows tree directly, so the
  WSL-era failure modes (the unresolvable worktree `.git` pointer, the
  CRLF phantom-churn blindness) do not arise on this path.
- **A CRASHED round is NEVER clean -- and the principle alone has DEMONSTRATED
  HOLES (adopted 2026-08-11 from the PEER HARNESS's reciprocal reference --
  the 2026-08-11 pair in `docs/proofs/` (reciprocal reference + its
  adjudication), Sec 1 there, each hole incident-proven). Run the FOUR ANCHORED ASSERTIONS per round before it may
  count:**
  1. **BANNER** -- the transcript's model and effort lines say what you
     intended. **CONCRETE VALUES for a `-p strong` gating round, so a cell can
     assert without knowing what the profile resolves to: `model: gpt-5.6-sol`
     AND `reasoning effort: high` (version-coupled: probed at codex-cli
     0.147.0 2026-08-11 and RE-PROBED at **0.152.1** 2026-09-07 by two
     independent cells plus the orchestrator's own gating round -- banner FORMAT
     and VALUES unchanged across the bump; re-probe on any further CLI bump).** PROBED FACT, ours not
     inherited: an unknown `-p` profile name produces NO error and NO warning
     -- the run silently proceeds at `gpt-5.6-terra` / `medium`, a downgrade of
     BOTH model and effort that every pre-assertion check passed. The positive
     control fires: the two banners are cleanly distinguishable. The doc is a
     lead; the banner is the evidence.
  2. **`grep -ac '^ERROR'` -- LINE-ANCHORED, never bare, and `-a`.** (A bare grep
     false-positives on repo prose the reviewer echoed after reading files --
     every repo-access round is exposed.)
     **AMENDED 2026-08-24 (CHARC, after a production firing disqualified 3 of
     4 rounds on one arc): the line-anchor was calibrated against PROSE
     echoes only, and it is UNSATISFIABLE for any round whose transcript
     carries raw SUBPROCESS output -- a test runner in a read-only sandbox
     (no writable temp) prints `ERROR:` at column 0 legitimately, and one
     round died on a PROMPT line beginning "ERROR." echoed back. The rounds
     that verify hardest are exactly the rounds the naive anchor
     disqualifies. The rule is now two-step:** a `^ERROR` count > 0 does not
     disqualify by itself -- it triggers CLASSIFICATION of each matched line,
     recorded in the round ledger: a codex TRANSPORT/content-filter line
     disqualifies the round; a line inside echoed subprocess output or echoed
     input does not. Classification is by provenance (is the match inside
     output of a command the reviewer itself ran, or inside quoted input?),
     not by content plausibility. **Two standing mitigations:** the review
     prompt instructs the reviewer to route test-runner output through a
     scratch file and report counts, never inline-echo raw runner output;
     and forbidding the reviewer to run tests at all is NOT a remedy -- it
     silences the verification to save the assertion (the only round that
     "passed" under that regime never executed the tests). **The same
     silencing arrives through the SANDBOX (2026-09-08): with no writable
     temp dir a reviewer that tried to run the suite fell back to reasoning
     and reported it as measurement. Every review prompt therefore carries
     this paragraph verbatim:** "You are in a read-only sandbox. You may be
     unable to run the test suite. If a command fails for that reason, SAY SO
     EXPLICITLY next to the finding it bears on, and mark that finding
     REASONED rather than EXECUTED. Do NOT silently fall back to inferring
     behaviour from the diff and reporting it with the confidence of a
     measurement. Tag EVERY finding EXECUTED or REASONED -- including the
     ones you never attempted to execute -- and for an EXECUTED tag show the
     probe and its output in the transcript." (`EXECUTED_OR_REASONED` in the
     review-gate instance doc; the per-finding tag was added 2026-09-08 after
     its first outing produced an auditable, volunteered negative -- "no test
     runner was invoked" -- where the paragraph alone is only reactive.) **BANKED PROBE
     (owner CHARC): capture the pinned codex version's actual transport-error
     line format and re-anchor mechanically on it; until then the
     classification step is the gate.** This supersedes the banked
     "`^ERROR` false-positive on pasted unittest transcripts" item -- same
     class, now closed into the rule.
  3. **`grep -ac '^tokens used'` -- the completion footer, line-anchored, `-a`.**
     (Truncation removes the END of a file, so the banner survives every
     truncation by construction; the footer is the only line written AT
     completion. Banner = started right; footer = finished; `^ERROR` = the
     middle. A bare footer grep once returned true ten seconds into a
     220-second round, off prose.)
  4. **The VERDICT line, ANCHORED -- never a substring match.** (A killed run's
     only convergence strings were prose echoes from the repo.)
  5. **EXECUTION LIVENESS -- `grep -acE '^ succeeded in [0-9]'` is AT LEAST 1, and
     `grep -ac 'ERROR codex_core'` is CLASSIFIED (CHARC, 2026-09-21; this DISCHARGES
     the banked transport-error probe in assertion 2).** Found live: the codex CLI
     moved 0.152.1 -> 0.155.1 outside any seat, and under 0.155.1 every command in
     the Windows sandbox failed (`helper_unknown_error: setup refresh had errors`).
     A review round then passed ALL FOUR assertions above -- right banner, zero
     `^ERROR`, footer, an anchored `VERDICT: NO_NEW_CRITICAL_MAJOR` -- while the
     reviewer could read nothing and run nothing. It was ruled VOID (a silenced
     round). The transport-error line is TIMESTAMP-PREFIXED
     (`2026-...Z ERROR codex_core::tools::router: error=exec_command failed: ...`),
     so the column-0 anchor is blind to it BY CONSTRUCTION. Two readings, measured
     on our own evidence: the void round has 4 `ERROR codex_core` lines and ZERO
     `^ succeeded in` lines; a healthy round (3a round 7) has 2 such ERROR lines
     -- one failed command, one model-list refresh timeout -- among 60
     `^ succeeded in` lines. So the ERROR token ALONE does not disqualify (it
     triggers the same by-provenance classification as assertion 2), and the
     POSITIVE CONTROL is the success count: **a round in which the reviewer
     completed no command is VOID whatever its verdict says.** Both formats are
     version-coupled: re-probe them, with the banner, on every CLI bump, and
     record the CLI version in every round's ledger line. **AT BRING-UP OF ANY
     REVIEW LOOP, run a one-command probe through the exact invocation the loop
     will use and require one `^ succeeded in` line BEFORE round 1.**

  **ALL FOUR ASSERTIONS TAKE `grep -a` (CHARC, 2026-09-07; positive control run at
  the orchestrator's seat and recorded in the stdin close-out accept).** A codex
  transcript can carry a NUL byte -- it echoes whatever a command it ran printed --
  and GNU grep then treats the whole file as BINARY. **The failure is asymmetric and
  that is what makes it dangerous:** the three COUNT assertions keep returning correct
  counts (`grep -c` is unaffected), so three of four still pass; only assertion 4,
  which must READ THE VERDICT TEXT BACK, breaks -- it prints `Binary file <path>
  matches` to stdout with **exit status 0** and no verdict line. A checker reading
  that gets an empty match it cannot distinguish from "the reviewer emitted no
  verdict", while every other assertion reassures it. **POSITIVE CONTROL (run it on
  any fixture you doubt, and record BOTH readings):** take a transcript with a NUL
  injected mid-file; the pre-fix `grep '^VERDICT:'` prints `Binary file ... matches`
  with empty stdout at exit 0, and `grep -a '^VERDICT:'` on the SAME file prints
  `VERDICT: NO_NEW_CRITICAL_MAJOR`. Strip the NUL and the pre-fix command prints the
  line too -- that is the control proving the NUL, not the pattern, is the cause.
  The live stdin close-out round carried **zero** NUL bytes, so `-a` was prophylactic
  there; record that reading rather than implying the fix fired.
  **The CONTENT-FILTER shape + its banked remedy:** exit 0, footer present,
  zero findings, no verdict -- only the `^ERROR` grep catches it; the trigger
  is FRAMING, not content. Remedy (rigour proven unchanged by re-run):
  `ADVERSARIAL CODE REVIEW` -> `CORRECTNESS REVIEW`; `WHAT TO ATTACK` ->
  `WHAT TO EXAMINE`; "scrutinise hardest" -> "review most carefully".
  **GATE-VERSUS-RITUAL:** a round failing a mechanical assertion may not COUNT
  toward convergence -- but its CONTENT may still be verified and used. Never
  re-argue an assertion when inconvenient; disqualify the round, keep the
  finding.
- **SCRATCH-IN-INPUT (adopted 2026-08-11, same source Sec 2 -- two of OUR OWN
  correct rules compose into this hazard: repo read-access + round artifacts
  staged at the worktree root): relocate every `.codex-*` file, the findings
  file, AND the round ledger to a session scratchpad FOR THE DURATION of the
  loop; restore to the worktree at the end (QA's audit home unchanged).** Add
  an explicit prohibition in the review prompt and a per-round grep that the
  reviewer touched neither glob. **SCRATCH FILENAMES ARE ARC-SCOPED, NEVER
  GENERIC (standing protocol 2026-08-13): a shared scratchpad plus a generic
  name (`review-prompt-r2.md`) let one cell silently overwrite a concurrent
  sibling's review file mid-arc -- a silently swapped review file means a cell
  reviews the WRONG DIFF and never learns it, the worst failure a review loop
  can have. Prefix every scratch/staging file with the arc slug.** (The peer harness's incident: a round read the previous
  round's findings out of the worktree and replayed them verbatim while every
  mechanical assertion passed. No assertion can catch an echo. **AND OURS,
  recorded so the class is grounded in our own history: flip-classifier round
  10 read leftover `.codex-review-r*.txt` and RE-RAISED already-fixed round-7/8
  findings -- caught and re-run at the time, recorded as an incident; the peer
  harness's pass is what turned the incident into a CLASS. Note also that the ROUND
  LEDGER -- our 08-09 fix for loop auditability -- is itself reviewer-readable:
  one hazard's fix created another, seen only by an outside pass.**)
- **Repo access for production code:** a pure diff-only review is blind to a
  defect whose correctness depends on un-changed surrounding code. For
  production-code review, either point Codex's cwd at the worktree (`-s
  read-only` -- it reads the surrounding reference graph itself) OR include the
  reference-graph files in the stdin bundle.

**WSL IS THE PINNED TRANSPORT FROM 2026-09-21 (CHARC), UNTIL THE WINDOWS SANDBOX IS
SHOWN REPAIRED BY THE BRING-UP PROBE OF ASSERTION 5 -- for cell rounds AND for Reviewer
B.** The Windows CLI regressed at 0.155.1 (above). WSL's codex is the same version and
its own sandbox runs commands and reads worktree files. The tier is passed PER CALL,
never from the global config (which an update rewrote: its default model changed
under us): `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only`, and the banner
assertion checks exactly those values. Every ledger line records transport + CLI
version. The rest of this paragraph is the wrapper as first written:
**THE WINDOWS PATH IS REPAIRED BY ONE PER-CALL FLAG (CHARC, 2026-09-21, on the operator's
word to investigate; WSL STAYS PINNED by the operator's decision -- this is the verified
ALTERNATE, not the default).** Cause, read from `~/.codex/.sandbox/sandbox.<date>.log`: at
0.155.1 the ELEVATED Windows sandbox's setup helper validates read/execute access over the
Codex DESKTOP app's runtime tree (`AppData/Local/OpenAI/Codex/runtimes/cua_node/...`), and its
`CreateFileW` fails on a 283-character path there (over MAX_PATH; the OS long-path switch is
on, the helper is not long-path-safe). Every command is then rejected with
`helper_unknown_error: setup refresh had errors`. The tree predates the bump; the CLI's
validation is what is new. It is NOT our invocation and NOT a broken install. **Fix: add
`-c 'windows.sandbox="unelevated"'` to the pinned `codex exec` line** (the restricted-token
sandbox, which has no setup helper). Verified at the CHARC seat: ZERO-TOKEN reproducer
`codex sandbox -- cmd /c echo X` fails as above, and with the flag it prints X; under the
flag a write inside the repo AND a write in the user profile are both `Access is denied`;
an end-to-end `codex exec -p strong -s read-only --skip-git-repo-check -c
'windows.sandbox="unelevated"' -` probe gave banner `v0.155.1 / gpt-5.6-sol / high /
read-only`, 1 success line, 0 `ERROR codex_core`, footer present. Run `codex sandbox` from
PowerShell, or Git Bash rewrites `/c` into a path. NOT measured: whether the unelevated
sandbox restricts NETWORK as the elevated one may -- the review prompt's OFFLINE line stays.
NEVER write this key into `~/.codex/config.toml`; it is per call, like the tier. Drop the
flag when the zero-token reproducer passes without it on a later CLI.
**FALLBACK (only if the Windows CLI regresses): the WSL wrapper.**
A worktree's `.git` is a file WSL git cannot resolve -- never let WSL Codex run
git; pre-generate the diff Windows-side and pipe via the PATH wrapper:
`wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; cat <prompt>.md
.codex-diff.txt | codex exec [-p <tier>] -s read-only --skip-git-repo-check - >
.codex-review-r<N>.txt 2>&1'` -- and cross-check any line-ending-churn finding
against Windows `git diff --numstat` (the WSL CRLF phantom).

## Run to convergence + persist every response

- **STATE THE BRIEF'S DECLARED OPERATING ENVELOPE IN THE REVIEW PROMPT, and ask
  the reviewer to TAG any finding it believes is reachable only OUTSIDE it**
  (added 2026-08-09, operator-directed, after repeated rounds hardening against
  inputs the code will never see). Report-everything is UNCHANGED -- never tell
  the reviewer to be conservative or to drop findings; the tag pre-sorts triage,
  it never suppresses. Severity is ENVELOPE-RELATIVE per the fill's
  `ENVELOPE_SEVERITY`: an out-of-envelope finding is non-blocking by rule
  (banked on the accept, never loop-driving). Findings never generated cost
  zero rounds -- the envelope in the prompt is the cheapest control in the
  chain.
- Iterate rounds until `NO_NEW_CRITICAL_MAJOR` (zero new critical/major) --
  judged envelope-relative, with the fill's ROUND_LEDGER maintained and the
  FIVE_ROUND_GATE honored (stop at round 5 and every 5 for dispatcher approval;
  continue only on new, in-envelope, non-reopened critical/major findings).
- After EACH round, append the full verbatim Codex response + your per-finding
  adjudication to a gitignored findings file -- so convergence is independently
  verifiable from the real transcript, not just claimed.
- **CLOSEOUT CLEANUP (part of the arc's accept/teardown, not optional;
  operator-directed to cover BOTH families 2026-07-24):** ALL non-durable
  reviewer working files are DELETED when the arc closes -- their evidentiary
  value ends at the accept (the durable record = the rounds + verdict
  reported in the return and the accept record, never staging litter):
    * `.codex-*` (prompts / diffs / round outputs), repo root AND worktrees;
    * `.copowers-*` (staging: prompts / `-r{n}.txt` round outputs /
      `-findings.md` / `-trace.txt`), repo root AND worktrees -- the
      implementer-runs-A loop stages these at the CELL seat, so the cell's
      closeout sweeps its own;
    * the `~/.codex/sessions/` CLI rollout-log accumulation (periodic sweep).
  NEVER touch config/auth: `.copowers.yaml` (tracked config),
  `~/.codex/config.toml` / `auth.json` / the `*.config.toml` profile files
  (load-bearing, incl. the pinned `-p strong` profile). A worktree-side
  review's files die with the worktree; main-tree files are removed at
  teardown. Provenance: 83 stale `.codex-*` + 199 `.copowers-*` + 898
  rollout logs (~375 MB total) were swept 2026-07-24 -- this rule exists so
  the accumulation does not recur.

## B-independence disciplines (adopted 2026-08-11, the reciprocal reference Sec 5)

- **Never build the B prompt from the author's offered "areas worth pointing it
  at"** -- a cell's return report is an accurate, generous, AUTHOR'S map of
  where to look, and adopting it re-couples exactly what B's independent seat
  exists to decouple. B's framing stays neutral and its own; read the return
  report AFTER forming the pass, or for triage only.
- **The transition head-to-head, ONCE at any B-assignment change:** the old
  seat's B and the new seat's B on the SAME finished tree. (The peer harness's instance:
  the author-adjacent B found 6 and converged; the independent B on the
  identical tree returned NEW_CRITICAL_MAJOR_FOUND, including a regression the
  arc's own test blessed.) Free exactly once; banked here with that trigger.
- **B's success criterion: "it stops being productive when the work is good."**
  A B round finding only pre-existing debt and nothing introduced is B WORKING,
  not B failing -- do not read a quiet round as grounds to retire the pass.

## Codex is replaceable

Codex is **one replaceable `REVIEWER` implementation, not part of the core
protocol.** The seam's `REVIEWER` extension point can be filled by any
adversarial reviewer; a non-software domain ignores this file entirely.
