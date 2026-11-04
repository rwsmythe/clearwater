# Dispatch Recipe -- the generic implementer protocol

**Audience:** a dispatched implementer cell. You have NO prior conversation
context and you do NOT inherit the orchestrator's memory. Read this protocol in
full, then read your dispatch brief and execute it.

This recipe is framed around four GENERIC concepts -- it makes **no hard source-
code assumption**, so a non-software domain can supply its own mechanism for
each. The common instantiation on THIS substrate is named as the *substrate
default* (not as a universal requirement).

## 0. The shape of a dispatch

1. Read this recipe + your dispatch brief in full. Re-ground every anchor
   against reality before acting (anchors drift).
2. Work in an **isolated workspace** (1).
3. Produce your **product** under the build cycle (2): produce -> validate ->
   converge, one cycle per logical change.
4. Run the **review to convergence** pointing at seam 3 (3) -- when your brief
   calls for it. Maintain the fill's CUMULATIVE ROUND LEDGER (per round:
   severity counts, in-envelope vs out, NEW vs REOPENED, reverts); **at round 5
   and every 5 rounds thereafter, STOP and report the ledger to your dispatcher
   for APPROVAL TO CONTINUE** -- the gate continues ONLY on new, in-envelope,
   non-reopened critical/major findings, and severity is ENVELOPE-RELATIVE
   (a finding reachable only outside the brief's declared envelope is
   non-blocking by rule: banked, disclosed, never loop-driving).
5. Transfer **acceptance** back to the orchestrator (4): DELIVER the structured
   return report to your dispatcher as your final action (never idle with it
   unsent).
6. Honor the disciplines (5).

A cell may run as a sequence of PROCESS runs rather than one conversation (a substrate
may require it): then one run is one TURN, the run's end is the yield, the next prompt
resumes it, and a cell that cannot write its own history ends every turn naming the files it
changed so its dispatcher records them. Everything else in this recipe applies unchanged.

## 1. Isolated workspace

Parallel implementers must not collide -- each works in its own isolated
workspace. **Substrate default:** a git **worktree** at `.worktrees/<name>`,
branched from the base your brief specifies. A non-source-code domain supplies
its own isolation mechanism (a sandbox copy, a scratch dataset, a separate
document). Leave the workspace intact at the end -- the orchestrator owns the
acceptance transfer.

## 2. The product + validation evidence (the build cycle)

A **product** is whatever the cell produces -- code, a plan, a doc, an artifact.
The build cycle is **produce -> validate -> converge** (the domain's equivalent
of red-green-refactor): write a failing check, see it fail the right way,
produce the minimal change, see it pass, commit. One cycle per logical change.
For a regression check, compute the expected result under BOTH the pre-change
and post-change paths to prove the check distinguishes (a check that passes both
ways is worthless).

**Substrate default for software:** the validation evidence is an automated test
plus the project's lint/format pass; run the WHOLE validation suite to green
BEFORE the review (so the review converges on a green diff) AND again on the
final head. The specific runner / lint / format tools are NOT named here -- they
are part of the project's review/gate seam (seam 3), so the recipe stays
domain-agnostic.

## 3. The review-to-convergence loop (pointing at seam 3)

Run an adversarial **reviewer** over the product, classify findings by severity,
adjudicate each, and iterate to convergence (zero new blocking). **The reviewer
mechanism is NOT named here** -- it is the project's seam-3 fill
(`review-gate-seam.md` defines the contract + a default; the project plugs a
concrete reviewer there). The optional ready-to-use reviewer reference shipped
with the harness (`codex-reviewer.md`) is ONE such plug-in for the `REVIEWER`
slot on this Claude Code + WSL/Windows substrate -- a non-software domain plugs
a different reviewer and ignores it. **Two implementer lanes, one rule: the reviewer is the
OTHER model from the implementer.** A Claude cell's Reviewer A is the Codex reviewer; a Codex
cell's Reviewer A is a Claude pass its dispatcher runs between the cell's turns
(`scripts/codex_cell.py review`). A Codex cell never runs `codex-reviewer.md`'s staged
invocation on its own diff. **Adjudicate, don't blind-fix:** a finding
premised on something the system *verifiably prevents* is out-of-scope -- but
ONLY with the cited constraint; absent the citation it stays in-scope.

## 4. Acceptance transfer (the return report)

Acceptance is transferred back to the orchestrator. **DELIVER the structured
return report to your dispatcher as your FINAL ACTION -- via whatever MECHANISM
actually REACHES your dispatcher** (amended 2026-08-25 after a stall: for a
spawned/named cell that is your messaging tool addressed to the dispatcher;
plain unaddressed chat text from such a cell reaches NOBODY). You do NOT post
to any role mailbox (that is the orchestrator's routing) -- the mailbox
prohibition names the one forbidden channel, it does NOT define the delivery
mechanism, and "in chat" was never a mechanism. The dispatcher's brief states
the concrete delivery path; if yours does not, ASK before finishing. The
prohibition constrains the CHANNEL, not the delivery: do NOT finish, go idle, or await further instruction without
having delivered the report -- an undelivered report is a FAILED HANDOFF even
when the work itself is complete, because the report is where deviations,
stop-and-flags, and lock-prevented consequences are disclosed (a written-but-
unsent report fails that disclosure channel closed-but-invisible). **Substrate default:** the
acceptance artifact is a **diff / merge** (the orchestrator rebases your branch,
merges, re-validates the merged head, accepts). A non-source-code domain
supplies its own acceptance artifact. Include in the report: what you produced
(the per-change list), the validation evidence read off the final state, the
review rounds + the final verdict, every brief lock stated as honored-on-disk,
and any deviation / simplification / stop-and-flag.

## 5. Disciplines

**Context is spend (2026-09-06; reader amended 2026-09-07).** A cell CANNOT read its own depth:
the `[ctx]` line is printed by the UserPromptSubmit hook, which never fires for a subagent
(verified 09-07: 0 of 70 cell transcripts carry a hook-produced line). YOUR DISPATCHER reads a
Claude cell's depth and tells it the figure. Before assigning work, read the dispatcher's own main
session with `uv run python scripts/cell_depth.py --project "<project>" --sessions --session="<session-id>"`;
take the in-flight cell census with `uv run python scripts/cell_depth.py --project "<project>" --live 6`;
at every round gate read the named cell at any age with
`uv run python scripts/cell_depth.py --project "<project>" --session="<session-id>" --agent "<ID>"`,
where ID is the filename portion following `agent-a`. The census also lists older cells whose
parent session transcript is fresh, flagged `parked`; an empty live window exits 0 when discovery
found transcripts. Put the dispatcher-provided figure in the ledger, never an estimate.
Never `cat` a runner or reviewer log into your context -- route it to a scratch file and grep the
summary lines; never re-read a document you have already read (the brief quotes what you need);
add the round LEDGER to context per round, not the reviewer's transcript. When your dispatcher
reports you at ~400K, STOP at the round boundary and report with your ledger: it re-dispatches
from a fresh context.

**STOP means YIELD (2026-09-07, `YIELD_TO_RECEIVE`).** You cannot be reached while you are working:
a message from your dispatcher lands only when you END YOUR TURN. So every STOP in this document --
the five-round gate, a failed premise, a suite window, the depth re-dispatch -- is a RETURN: end the
turn with the report (and your ledger) as its content, and the answer arrives as your next prompt.
Never wait in-turn for a reply; never poll for one. Yield at EVERY round boundary even when nothing
is wrong -- that is how your depth figure and any ruling that landed since reach you. Anything a
gate needs you to know mid-turn is in this brief; if it is not here, it cannot reach you until you
yield. **A build turn yields after each task GROUP (2026-10-29):** a build prompt names a yield
after every two or three tasks, never "yield only at a window request or at the end", so a depth
reading falls INSIDE the build and the evaluation point and the stop can act (a build that needed
no window once ran eight tasks in one turn to 553K before its dispatcher could read it).

**A granted heavy run is waited for in the FOREGROUND (2026-10-28).** When your dispatcher grants a
long run inside an exclusive window, run it with a foreground poll-wait (a loop that checks the
process or its result file) or end your turn and let the dispatcher re-prompt you at its end. Never
start it in the background and idle on the completion notice: an idle cell is not woken by it, and
the host sits unused inside the window (one instance lost 33 minutes between two legs this way).

**A deletion grant names what is KEPT in the same message (2026-10-28).** When your dispatcher grants
you deletion of evidence, caches or outputs, the grant lists the files or patterns that stay beside
those that go, and you delete nothing the grant does not name. An amendment that follows a grant is
too late by construction: you act on the first message you read (one instance deleted 27
superseded evidence folders whole a minute before the amendment to keep one file in each arrived).

- **Honor the brief's locks.** They are binding. A defect/gap OUTSIDE your scope
  gets FLAGGED in the return report -- never fixed inline (scope creep), never
  silently absorbed.
- **STOP-and-ask** if a brief premise does not match reality, or a fix would
  cross a tripwire your brief did not authorize. Report the discrepancy; do not
  work around it. **And when you stop, REPRODUCE the problem cheaply if you can
  before asking** (added 2026-08-25, a cell's own correction of the praise it
  got for stopping): a stop WITH a reproduction is a FINDING a director can
  rule on without re-deriving it; a stop without one is only a question. The
  refusal buys the time; the reproduction is what mattered.
- **Ground, don't guess.** Verify shapes against reality (the live system, real
  output), not just the brief text.
- **Conventional commits** carrying the task id; the ATTRIBUTION FOOTER the
  harness mandates (`Co-Authored-By:` naming the model) is REQUIRED -- it is
  the commit's provenance, not a vanity trailer (amended 2026-09-02: the prior
  "NO co-author footer" line was violated by every commit on master, so it was
  never a rule; the practice wins and a directive requires it; the `Claude-Session:`
  trailer was dropped 2026-10-14 for the same reason -- no commit ever carried it); no OTHER
  trailers; no verification-skipping; a new commit per fix. Keep user-facing strings within
  the substrate's safe encoding (the Windows console is unforgiving of
  non-ASCII).

**Rounds, rulings, and evidence (2026-09-07; the fill's `RULING_PACKET`,
`TEXT_ROUND_CRITERION`, `EVIDENCE_PER_ROUND`).** If your work is TEXT (a doctrine block, a
brief, a design pass): classify every reviewer finding TEXT-BEARING or not in the ledger --
text-bearing changes a sentence the model reads, a citation row, or a guard; fix the rest
without a round; stop at the first round with zero text-bearing findings and in any case
after round 3, then hand to the gate. Do NOT start a revision while a director ruling is
outstanding -- wait for the packet; if a ruling arrives piecemeal, say so in the ledger
rather than amending per message. EVERY round, the moment it closes: commit the cumulative
ledger + that round's reviewer summary to `docs/proofs/<rung>-ledger.md` in your worktree,
and keep the full reviewer transcript at a durable path outside session temp, named in the
ledger. Your dispatcher fills the depth column; you fill the rest. **A citation row names
the MECHANIC and the SURFACE** (2026-09-07, the fill's `VERIFIED_WORLD_CLAIMS`): for every
sentence the text carries -- KEPT or new -- the row says which code makes it true (the function
or constant, at file:line) and on which surface the effect was measured (the model-facing module
in its true call order, never a per-row figure a filter marginalises). A line number alone is a
pointer, not a verification; a kept sentence with no named mechanic is an OPEN ITEM you route,
not a given you carry.

**A brief is a task ladder + a test roster, capped at ~1,000 lines.** Argument, history,
limitation reasoning, and rulings live in the design pass (`docs/proofs/`) and the ledger,
never in the brief. Over the cap = two rungs.
