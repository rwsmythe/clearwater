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

- `REVIEWER` = the Codex CLI as an adversarial correctness reviewer
  (`docs/codex-reviewer.md`). **Transport pinned at bootstrap: WSL** (`wsl.exe
  bash -ilc` with the PATH prefix; `codex-cli 0.157.0` verified live 2026-10-14;
  no Windows-native codex is installed on this machine). Re-probe liveness at the
  bring-up of every review loop with a one-command probe through the exact
  invocation and require one `^ succeeded in` line before round 1. Tier by the
  blast radius of a MISSED finding: `strong` (`-m gpt-5.6-sol -c
  model_reasoning_effort=high`, passed PER CALL) for every product-code package;
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
2. **Reviewer B** -- the plan's **independent review** (section 4.5 item 7): an
   implementer cell that did NOT write the package reviews it against the brief
   and the spec clauses, never against the author's report, on the finished tree
   (whole-artifact, repo-access, Codex at the same tier as its instrument). B
   checks the artifact's own top-level claims FIRST, measured end to end against
   the running code, before any code-level lens. B's prompt is built neutrally,
   never from the author's "areas worth pointing it at". Findings go back through
   the author's verification loop; B's transcript on the tree being merged is part
   of the accept record.

`GATE_CHECKS` (the orchestrator runs every one at its own seat, on the merge
candidate rebased onto main, and records the actual output lines):

- `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`,
  `uv run pytest` (with the hardware-marked tests the brief requires, run solo
  where a test is normally skipped or load-sensitive, quoting the enabling reading
  and the suite's skip count); and the harness gate `uv run python -m unittest
  discover -s tests/harness` whenever the change touches `scripts/`, `.claude/`,
  the kernel docs or `tests/harness/`.
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
