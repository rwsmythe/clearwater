<!-- SEAM 3: REVIEW MECHANISM + GATE CRITERIA -->

# Review / Gate Seam -- the mechanism-agnostic contract

This is **seam 3**: the review-to-convergence + gate CONTRACT, with named
extension points the project fills at bootstrap. It defines the *shape* of
review + the gate, plus a minimal generic DEFAULT that is operable from minute
one. **It names NO concrete mechanism** -- the `REVIEWER` slot is filled by the
project (an optional ready-to-use reviewer reference is catalogued in the
harness's reference set and named in the bootstrap's seam-3 step). This doc stays
mechanism-agnostic on purpose, so it transfers to any domain.

A project's CONCRETE fill of these extension points (naming its real reviewer /
gate) lives in its own `docs/review-gate-<app>.md` instance doc, so THIS contract
stays mechanism-agnostic; accept the shipped defaults below until that fill exists.

## Part 1 -- the review-to-convergence protocol (shape fixed; mechanism is a seam)

The loop: **product -> adversarial REVIEWER -> severity-classified findings ->
adjudicate each -> iterate to convergence (zero new blocking).**

Extension points the project fills:

- `REVIEWER` -- the adversarial reviewer that produces findings over a product.
- `PRODUCT_REPRESENTATION` -- how the product is handed to the reviewer.
- `SEVERITY_RUBRIC` -- the severity classes + which are blocking.
- `CONVERGENCE_CRITERION` -- when the loop stops.

## Part 2 -- the gate (director-owned, before accept)

A checklist of pass/fail checks the director runs before accepting. Extension
points:

- `GATE_CHECKS` -- the pass/fail checks.
- `WITNESS` -- the irreducible reality / human check the automated reviewer
  cannot replace.
- `ACCEPTANCE` -- what merge / accept means for this project.

## Part 3 -- carry-over disciplines (filled -- generic wisdom)

- The reviewer is **fallible**; the WITNESS is the true net. **Review is a
  filter, never the gate.**
- **QA at every boundary, BY the superior.** Each superior->subordinate boundary
  carries a review performed by the superior (the orchestrator over the
  implementer's product at accept; the director over the orchestrator's product
  at the tripwire / audit). The `REVIEWER` is the superior's INSTRUMENT for that
  review, never a substitute for the superior performing it. (WHAT each checks is
  per-project; THAT it happens at every boundary is the contract.)
- **Run to convergence** -- do not pad, do not stop early while blocking
  findings surface.
- **Adjudicate, don't blind-fix.** A finding premised on something the system
  *verifiably prevents* is out-of-scope -- but ONLY with the cited constraint;
  absent the citation it stays in-scope.
- **Verify on reality, not from the report.**
- **Ground or STOP.**

## The minimal generic DEFAULT (operable from minute one; replaceable starters)

So a fresh CHARC can run review + gate against its OWN bootstrap changes BEFORE
customizing, the seam ships defaults. These are clearly **replaceable
starters** -- the interview swaps in the domain's real rubric / gate / reviewer.

<!-- SEAM3-DEFAULTS -->
- `SEVERITY_RUBRIC` = blocking: critical, major; advisory: minor. **The reviewer
  reports EVERY finding it makes, including uncertain and low-severity ones,
  each with a severity tag -- classification and adjudication filter DOWNSTREAM,
  never at the finding step.** (Never instruct a reviewer to "only report
  serious issues": current models follow that literally and silently drop real
  findings. See `docs/model-prompting-standard.md`.)
- `CONVERGENCE_CRITERION` = zero-new-blocking. **The ROUND POLICY (a pre-set cap
  vs run-to-convergence) is itself an extension point the project's seam-3 fill
  sets** -- the shipped default is a cap set in the brief BEFORE the loop starts,
  with capped non-convergence a PERMITTED outcome (say so, name the residual).
  A fill that suspends the cap states its own anti-spiral guardrails. Briefs
  take the round policy FROM THE FILL, never improvised per-arc.
- `GATE_CHECKS` = the director's stated conditions hold AND the WITNESS confirms.
- `WITNESS` = operator confirmation.
- `REVIEWER` = a self-review pass (CHARC or a fresh agent re-reads the product
  adversarially) until a domain reviewer is plugged.
<!-- /SEAM3-DEFAULTS -->

## Minute-one dry-run (run any product through the default loop)

The exact ordered steps to take ANY product (e.g. a CHARC bootstrap edit)
through the default loop with no extension point left undefined:

1. **Product** -- identify the product (the change / artifact under review).
2. **REVIEWER pass** -- run the default `REVIEWER` (a self-review pass): a fresh
   adversarial read of the product, producing findings.
3. **Classify** -- tag each finding by the default `SEVERITY_RUBRIC`
   (critical / major = blocking; minor = advisory).
4. **Adjudicate** -- resolve each blocking finding, or mark it out-of-scope WITH
   a cited constraint (never blind-fix).
5. **Iterate** -- repeat 2-4 until the default `CONVERGENCE_CRITERION`
   (zero-new-blocking) holds.
6. **GATE_CHECKS** -- confirm the director's stated conditions hold.
7. **WITNESS** -- the operator confirms (the irreducible reality check).
8. **ACCEPTANCE** -- accept the product (merge / adopt per the project's
   `ACCEPTANCE` definition).

This loop is operable with ONLY the shipped defaults -- the project replaces any
extension point at app-definition.
