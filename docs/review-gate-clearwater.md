# Review / Gate -- Clearwater seam-3 fill (instance)

This is the Clearwater **instance fill** of seam 3. The generic, mechanism-agnostic
contract lives in `docs/review-gate-seam.md` (unchanged); this doc instantiates its
extension points with concrete mechanisms for Clearwater and binds the plan's
definition of done (`docs/clearwater-implementation-plan.md` section 4.5) to them.
It supersedes the seam's minimal defaults for application arcs; the defaults still
cover bootstrap and doc-only changes. Thresholds that are brief-level stay in the
brief. Rules adopted from the sibling harnesses are stated once, without their
incident history; the history is in those harnesses' fills if ever needed.

## Part 1 -- the review-to-convergence loop (Reviewer A, run by the cell)

**Two implementer lanes, one rule (owner, 2026-10-26/27; design pass
`docs/proofs/harness-dual-model-implementers.md`): the reviewer in BOTH nets is the OTHER model
from the implementer.** Claude cells (`implementer-opus-high`, `implementer-sonnet-*`) get the
Codex reviewer below, unchanged. The Codex cell (`implementer-codex-sol-high`, run by the
orchestrator as `codex exec` turns through `scripts/codex_cell.py`) gets the CLAUDE reviewer:
`claude -p --model opus --effort high` (never `--bare`: it drops OAuth), read-only tool policy
(Read/Grep/Glob, `git` reads, the project's runners and `python` probes; Edit/Write/Agent/web
denied), JSON output, run BY THE DRIVER between cell turns on the pre-generated diff
(`codex_cell.py review`), its findings file handed to the cell on the next turn for the cell's
own adjudication, fixes and ledger. Its assertions: the result's `modelUsage` key is the Opus
model; the effort is the invocation record (not echoed); `is_error` false; a `VERDICT:` line;
`git status --porcelain` empty afterwards (the reviewer wrote nothing); every finding tagged
EXECUTED or REASONED. Evidence, tiering (strong = Opus high for product code, fast = Sonnet
medium for docs) and the ledger are as below. The rest of Part 1 reads "Codex" for the Claude
lane and "the Claude pass" for the Codex lane.

- `REVIEWER` = the Codex CLI as an adversarial correctness reviewer
  (`docs/codex-reviewer.md`). **Transport pinned at bootstrap: WSL** (`wsl.exe
  bash -ilc` with the PATH prefix; `codex-cli 0.162.1` verified live 2026-10-14 at the WP0.1 accept (0.157.0 at bootstrap).
  Since 2026-10-27 a Windows-native `codex-cli 0.162.1` is ALSO installed (the implementer lane uses it); both
  transports gave the same banner for the new pin on 2026-10-27. B stays on WSL unless a seat records a reason). Re-probe liveness at the
  bring-up of every review loop with a one-command probe through the exact
  invocation and require one `^ succeeded in` line before round 1. Tier by the
  blast radius of a MISSED finding: `strong` (`-m gpt-6.1-sol -c
  model_reasoning_effort=high`, passed PER CALL; **pin moved from `gpt-5.6-sol` on 2026-10-27, owner-directed,
  banner value `model: gpt-6.1-sol` from that date; the WP3.10 gate's two B passes ran on the old pin and stand**)
  for every product-code package;
  `fast` for docs, briefs and tools under `tools/` that produce no shipped output.
  Never tier the rigor.
- `PRODUCT_REPRESENTATION` = the pre-generated diff against the brief's base SHA
  (`git diff -U8 <base>..HEAD`, Windows-side) plus read-only access to the
  worktree so the reviewer sees unchanged surrounding code. The prompt is staged in
  a file, never inline, and carries: the brief's required end state (the claim
  list), the declared operating envelope with a request to TAG findings reachable
  only outside it, the accepted limitations with reasons and an invitation to
  challenge them, the read-only-sandbox paragraph requiring every finding to be
  tagged EXECUTED or REASONED, the ledger path and prior rounds named as WITHHELD
  (and absent from the bundle), and `CORRECTNESS REVIEW` / `WHAT TO EXAMINE`
  framing (adversarial framing trips the provider's content filter).
- `SEVERITY_RUBRIC` = blocking: critical, major; advisory: minor. Severity is
  ENVELOPE-RELATIVE: a finding reachable only outside the brief's declared envelope
  is non-blocking by rule -- banked on the accept with its nominal severity, never
  loop-driving. A finding on code the arc did not introduce is BANKED with
  `git log -S` evidence of its origin; contested provenance counts as introduced.
- `CONVERGENCE_CRITERION` = a round with ZERO NEW BLOCKING findings terminates the
  loop (`ROUND_TERMINATION`). Non-blocking findings are fixed once in the
  terminating round's cleanup and never open another round; a result-bearing minor
  is named in the accept record. Supersession in any artifact is by REPLACEMENT,
  never annotation. The cell keeps a CUMULATIVE ROUND LEDGER (per round: counts by
  severity, in-envelope vs out, NEW vs REOPENED, reverts, whether the fixes changed
  PRODUCT code or only tests/controls, the transport and CLI version, the
  dispatcher-read context depth). **FIVE_ROUND_GATE:** at round 5 and every 5
  rounds the cell yields with the ledger; the dispatcher continues ONLY if new,
  in-envelope, non-reopened blocking findings are still arriving AND the round's
  fixes changed product code -- test-only rounds are polish, and polish is
  complete. **Re-seat line:** a multi-finding remediation is never ordered into a
  cell above ~250K tokens of context; the cell is re-dispatched fresh from its
  ledger. Text artifacts (briefs, design passes) get at most three counted rounds.
- **Per-round mechanical assertions** (a crashed or silenced round is never
  clean; all with `grep -a`): the banner's model and effort match the tier; every
  `ERROR` line classified by provenance (a transport error disqualifies, an echoed
  subprocess line does not); the `tokens used` footer present; the VERDICT line
  anchored on normalised text; at least one `^ succeeded in` execution line. A round
  failing an assertion does not count toward convergence, but its findings are
  still adjudicated.
- **Evidence per round:** the prompt, the diff input, the full transcript and the
  per-finding adjudication are copied the moment a round closes to the durable
  evidence folder OUTSIDE every repo tree (`C:\Users\rwsmy\clearwater-review-evidence\<arc>\rN\`),
  with md5s; the cumulative ledger is committed once, after Reviewer B, to
  `docs/proofs/<arc>-ledger.md`. The `.codex-*` staging files are gitignored, arc-
  scoped in name, relocated to the session scratchpad for the loop's duration, and
  deleted at teardown.

## Part 2 -- the gate (before accept)

Two nets, both required for every code-bearing package; a read-only or byte-
identity arc may substitute independent verification with the reason stated in
the brief.

1. **Reviewer A** -- the cell's loop above, converged, with the ledger.
2. **Reviewer B** -- the plan's **independent review** (section 4.5 item 7):
   **ONE Codex pass the ORCHESTRATOR RUNS ITSELF, at its own seat, on the merge
   candidate** (`docs/orchestrator-context.md`, "Reviewer B -- YOUR single-pass
   adversarial gate at YOUR seat"; the same shape as the coa-chess and
   swing-trading harnesses). It is NOT an implementer cell. *(Corrected 2026-10-15
   on the owner's catch: the first fill text made B a subagent cell; WP1.1, WP1.2A
   and WP1.5's first B ran in that form. See the accept records for the
   retroactive pass.)* Shape:
   - **The other model (2026-10-27):** for a Claude-implemented package B is the Codex pass
     below; for a Codex-implemented package B is the CLAUDE pass of Part 1, run by the
     orchestrator as a PROCESS at its seat (`scripts/codex_cell.py review` against the merge
     candidate's base, or the same command by hand), never a subagent; its assertions and
     evidence files as Part 1, the prompt built neutrally as below. The one-time transition
     head-to-head (both B's on one finished tree) is owed at the first Codex-implemented
     package's gate.
   - **Tier:** the package's tier (STRONG for product-bearing results), the pinned
     WSL transport, per-call flags, probe and the five mechanical assertions
     exactly as Part 1; stdout and stderr split; a done marker written last. The
     run script and prompt are kept in the evidence folder (`B/run_review_B.sh`,
     `B/review-prompt-B.md`, `B/review-B.txt`).
   - **Product:** whole-artifact. cwd = the worktree at the merge candidate (Codex
     may read any file); appended input = `git diff -U8 <base>..<candidate> --
     <owned paths> ':!uv.lock' ':!docs/proofs'`. The ledger and the author's report
     are WITHHELD and named as withheld in the prompt, with the access assertion.
   - **Prompt:** built by the orchestrator, neutrally, never from the author's
     "areas worth pointing it at": the contract (the brief's claim list and the
     spec clauses, by path), the envelope with the TAG request, lenses that ask
     for every control that can fail and every sentence the code makes false, and
     the EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md`.
   - **Claims first:** the prompt lists the brief's REQUIRED END STATE and asks
     Codex to check those claims against the running code before any code-level
     lens (`CLAIMS_FIRST`).
   - **Disposition:** B is not required to return clean. Every critical or major
     is DISPOSITIONED: introduced by this package -> ONE bounded remediation
     through the author's loop and ONE re-run of B; pre-existing or out of
     envelope -> BANKED in `docs/debt-register.md` with file:line, mechanism and
     reachability. A second blocking B is adjudicated by irreversibility at the
     gate seat, never a third remediation in the same package.
   - **Order (owner, 2026-10-29, after WP4.2's suite ran twice):** ONE full two-leg
     gate per package, run on the FINAL candidate AFTER Reviewer A has converged and
     Reviewer B has returned (clean, or its single remediation and re-run done). A
     full-suite run before B is development evidence, not the gate, and gets no
     window; during the build the cell runs the touched files and the markers it
     needs. B is light and read-only, so it precedes the suite.
   - **Record:** B's transcript on THE TREE BEING MERGED (path, md5, the five
     assertion results, verdict) is named in the accept record. No transcript, no
     accept.

   The orchestrator's own **verification QA** is the separate half of the gate
   (`orchestrator-context.md`: "plus your verification QA"): the claims re-run at
   its seat, the GATE_CHECKS below and the WITNESS. A heavy MECHANICAL reproduction
   (a bench matrix, a real-footage compare) MAY be delegated to an
   `implementer-sonnet-medium` cell as an instrument with a fixed recipe; that is
   QA evidence, never Reviewer B.

`GATE_CHECKS` (the orchestrator runs every one at its own seat, on the merge
candidate rebased onto main, and records the actual output lines):

- **Before any suite in a gate worktree, copy the main tree's uncommitted `clearwater.local.toml`
  into it** (WP3.10's first gate run was VOID without it: the footage tests skipped and the
  look-check tests failed on `LocalConfigError`; added 2026-10-27).
- `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`, the
  TWO-LEG pytest gate below (with the hardware-marked tests the brief requires,
  run solo where a test is normally skipped or load-sensitive, quoting the
  enabling reading and each leg's skip count); and the harness gate `uv run python -m unittest
  discover -s tests/harness` whenever the change touches `scripts/`, `.claude/`,
  the kernel docs or `tests/harness/`.
- **W-STATIC (WP6.4 accept, AD-36, from 2026-11-05):** `uv run mypy --platform darwin` beside the default
  `uv run mypy`, the same `files` set, `strict` and `warn_unreachable` unchanged; BOTH runs must report 0
  errors (the early-return guard form fails one target with [unreachable]; the statement form passes both).
- **Entry-point isolation, recorded exception (owner's word 2026-11-05; WP6.3b turn 3):** an existing
  integration test whose purpose IS the real GUI start (`tests/test_app_startup.py` `QUIT_SCRIPT`) imports
  PySide6 and runs the event loop under redirected roots, `QT_QPA_PLATFORM=offscreen` and a bounded timeout,
  at the SEAT in a gate leg only; no cell runs it on any revision.
- **The two-leg pytest gate** (WP-T4, AD-28, from 2026-10-28; measurements and limits in
  `docs/reports/wp-t4-parallel-tests.md`; sizing in `docs/reports/wp-t6-gate-sizing.md`; after
  WP-T6 the per-package gate is parallel about 714 s + serial about 1,389 s, about 35 min wall,
  against about 64 min at WP-T4). From Git Bash (a PowerShell 5.1 redirect writes UTF-16), with
  `QT_QPA_PLATFORM=offscreen`, `PYTEST_ADDOPTS` unset, and a new RUN identifier per gate; every
  execution and collection leg uses its own fresh `--basetemp` under `work/`, never footage.
  Before each heavy leg check at least 5 GiB available
  (`uv run python -c "import psutil; assert psutil.virtual_memory().available >= 5*2**30"`).
  Run, one heavy job at a time (WP-T6, from 2026-10-29: the `fullclip` marker names the
  full-GX011627 forms of the seven gate tests; the trim forms stay in the serial leg):
  `uv run pytest -q -rs -n 4 --timeout 600 -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/pytest-gate-RUN-parallel > work/pytest-gate-RUN-parallel.log 2>&1`,
  then `uv run pytest -q -rs --timeout 1200 -m "(gpu or footage or gui or slow) and not fullclip" --basetemp=work/pytest-gate-RUN-serial --durations=0 --junitxml=work/pytest-gate-RUN-serial.xml > work/pytest-gate-RUN-serial.log 2>&1`.
  Under `-n 4`, the earlier core faulthandler dump on stderr is the only stack,
  so each leg's log must retain both streams.
  **STALL WATCH:** every leg reports on completion or after its log has not changed
  for 5 minutes (15 minutes for fullclip, whose single nodes can run for minutes
  without output). A watch report triggers INVESTIGATION, not automatic STOP:
  identify the running node from the basetemp's newest directories against the
  `--collect-only` order, and check process-tree CPU time and files growing under
  the basetemp. Progress means a long node: keep watching; no progress for a further
  5 minutes means STOP with the node and whatever stack exists, including the core
  dump on stderr (DR-108). This resolves the coincidence with the 300 s diagnostic
  timer: a dump alone is not a STOP; a dump plus sustained lack of progress is.
  STANDING RULE (your fill, effective now): while a gate's SERIAL leg runs, NO other pytest invocation of any size runs on this host, at any seat or in any sandbox (a Codex light suite included); the gui nodes are timing-sensitive and the leg is the figure of record. Codex turns that need their light suite wait for the leg or run before it. (CHARC 97d5abbf, 2026-11-01)
  CHARC `823921b8` (item 3) extends it to the fullclip leg: no other pytest runs during a serial OR fullclip leg.
  A thread timeout dumps stacks and exits the process once its timer can acquire the
  GIL (a native GIL-holding deadlock defers it; only the 300 s faulthandler dump on stderr
  and the stall watch catch that case, with the stall watch providing the STOP and the
  dump its stack); a timed-out leg is a STOP with the node and the stacks, followed
  by a re-run of the leg after the fix.
  Under xdist the worker's pytest-timeout dump IS absent: xdist does not forward
  its terminal writer; the parent reports `node down: Not properly terminated` and
  `worker 'gwN' crashed while running '<node>'`, can replace the worker and finish
  the remaining tests, and retains only the core faulthandler stack on stderr.
  That dump carries no node ID (tie it to the crash line), fires once 300 s after
  the node starts (setup included), and shows normal work if the node hangs later.
  `timeout_func_only` leaves every fixture (session and function, setup and teardown)
  un-timed: a fixture hang gets the faulthandler dump and the stall watch, not a test failure.
  Faulthandler dumps from legitimately long nodes (fullclip or slow session trims) are
  diagnostic noise, not failures; a dump alone is not a STOP.
  Hangs outside the test protocol (collection/import, session-start/session-finish
  hooks, interpreter exit such as a non-daemon thread or multiprocessing atexit
  join, or the xdist controller waiting on a worker at shutdown) get neither a
  test timer nor a timed faulthandler dump; only the stall watch catches them.
  The thread method's `os._exit` kills only the pytest process: on Windows spawned
  export-worker/FFmpeg children survive, so identify and end leftover `python` /
  `ffmpeg` processes belonging to that run before re-running with a fresh `--basetemp`.
  The terminated process loses its summary, `--durations` and `--junitxml`; exit 1
  also means ordinary failure, so identify a timeout by `+++ Timeout +++` without
  a summary in-process, or by the xdist crash line (the controller can still finish
  with a summary after losing the worker's normal final output).
  **FULLCLIP** (`uv run pytest -q -rs --timeout 2400 -m "fullclip" --basetemp=work/pytest-gate-RUN-fullclip --durations=0 > work/pytest-gate-RUN-fullclip.log 2>&1`, no `-n`,
  about 26 min) runs at least ONCE per phase-end gate report and whenever a package brief asks
  for it; a per-package gate does not run it. The trim forms prove V4 MANDATORY and REQUIRED;
  three best-effort container items are proved by the fullclip forms only (WP-T6 report, Limits).
  **Collection:** collect all and the three expressions
  (`uv run pytest --collect-only -q [-m "<expression>"] --basetemp=work/pytest-gate-RUN-collect-<all|parallel|serial|fullclip> > work/pytest-gate-RUN-<all|parallel|serial|fullclip>.txt`),
  each exiting 0, and keep only node-ID lines (starting `tests/` and containing `::`). Each
  list's length equals pytest's own "N tests collected" line. Require no duplicates, pairwise
  disjoint lists, a union equal to all, and **parallel + serial + fullclip = all**. Diff the
  candidate's full list against main's: every removed ID is explained by the package's diff, or
  the gate is void.
  **Outcomes:** each leg is green with passed + skipped + xfailed + xpassed equal to its
  selected count and zero failures or errors. Quote each leg's `-rs` skip lines and compare them
  with the previous accepted gate's. A new or moved skip (a seat where CuPy does not initialise,
  or `clearwater.local.toml` not copied) is explained or the gate is void. Recollect at every
  gate; the counts are not frozen (WP-T4 4032 + 1046 = 5078; WP-T6 gate 5313 + 1137 + 7 = 6457).
  **New parallel-leg tests** use a per-test `tmp_path` and no shared path. A new wall-clock bound
  in one is marked `slow` with a reason, as E1 was. The reason names the bound and says the
  marker is for timing isolation, not duration. A generous sanity ceiling, ten times the
  expected figure or more and there to catch a hang, is not such a bound and stays parallel
  (CHARC, WP-T4 accept). Any other exception is also `slow` with a reason. Existing bounds in
  the parallel leg are watch items for their owning packages (the report lists them). Product timing and memory figures come from serial runs only, in their own windows.
  Where a memory sampler is available, stop and report if any sample at N=4 falls below 2 GiB
  available.
- Every public function, class and module has a Google-style docstring; comments
  checked against the code (plan 4.5 item 2).
- The verification-loop record and the completion report are present and the
  report's claims audit against tool results (plan 4.5 items 4 and 6).
- The brief's locks hold on disk: only owned files changed, frozen interfaces
  untouched, no new dependency beyond the grant, no write under the footage path
  (a test or a grep proves the absence).
- Every follow-on, gap or deferred item in the return report has an explicit
  disposition: COMMISSIONED (named package), BANKED (owner + trigger), or
  DECLINED (cited ground).
- Byte identity across the rebase is proven with `git patch-id` on the arc
  patch before and after; merge integration is a named gate that asks the runtime
  question (this code against the live main), not only file-set disjointness.
- A timing or memory figure (plan 4.3) carries its conditions: full clip, nothing
  else heavy running, the moment of the reading.

`WITNESS` = the owner at the checkpoints the plan reserves (CP1 footage sorting,
CP2 look check, CP3 gate scope decisions, CP4 design-freeze review, CP5 V2 visual
review), run step by step with the owner's word read back verbatim with its time;
elsewhere the orchestrator's own reality check of the claimed behavior (the tool
run on a known input, the output inspected), which the automated reviewer never
replaces.

`ACCEPTANCE` = the orchestrator merges the rebased, re-validated package to main
(the only role that merges), commits by pathspec, and writes the accept record
under `docs/proofs/` naming the base SHA, the merged head, both reviewers'
verdicts, the ledger path, the evidence folder, and every banked item.

## Part 3 -- disciplines carried from the seam (binding, unchanged)

Review is a filter, never the gate; QA at every boundary by the superior;
adjudicate, don't blind-fix (out-of-scope only with the cited constraint); verify
on reality, not from the report; ground or STOP. Every control needs a positive
control: a planted defect it must catch, counted as caught only on a failed line
by name.
