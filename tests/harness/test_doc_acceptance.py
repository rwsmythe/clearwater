"""Content-acceptance checks for the scaffold's shipped docs.

Each doc task carries an acceptance checklist (the doc-equivalent of red-green).
These tests assert the load-bearing content markers are present so a future edit
that drops a required section is caught. The genericity guard
(test_genericity_guard.py) is the separate no-contamination gate; these tests
assert POSITIVE content presence.
"""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _read(rel: str) -> str:
    return (REPO_ROOT / rel).read_text(encoding="utf-8")


HARNESS_README_RELPATHS = ("docs/harness-readme.md", "README.md")


def harness_readme_relpath() -> str:
    """The harness scaffold's README: the root README on a bare clone; an instantiated
    project whose root README is the application's user page keeps the scaffold text at
    docs/harness-readme.md (2026-11-09), which wins when present."""
    for rel in HARNESS_README_RELPATHS:
        if (REPO_ROOT / rel).exists():
            return rel
    return HARNESS_README_RELPATHS[-1]


def _norm(text: str) -> str:
    """Collapse all runs of whitespace to single spaces so a contiguous phrase
    matches regardless of Markdown line-wrapping (the same collapse the live
    never-post-to-mailbox check uses inline; pinned here as a named helper so the
    charter contiguous-fragment checks share one normalization)."""
    return " ".join(text.split())


_FILL_MARKERS = ("what the project does", "domain", "success criteria")
_PLACEHOLDER_TOKENS = ("_(", "(placeholder)", "tbd", "todo", "_()_", "...")
# Stub-only residue: phrases the bare-clone stub carries that a FILLED doc must
# REMOVE. Defined once (auto-review MAJOR) so STATE A (the seed-framing the stub
# must retain) and STATE B (any such residue is an illegal mixed half-edit) stay
# in lockstep. "this file is empty by design" is the full stub sentence; the rest
# are the seed-framing + stub title. (Re-confirm if the template stub body is
# edited -- the live-file test is the canary.)
_STUB_RESIDUE_FRAGMENTS = (
    "this file is empty by design",
    "empty by design",
    "until the interview runs",
    "empty seed",
    "application (stub)",
)
_STUB_FRAMING_FRAGMENTS = ("until the interview runs", "empty seed")


def _answered_fill_markers(text: str) -> set[str]:
    """The SET of fill markers that appear as a real ANSWERED markdown HEADING (a
    `#`-prefixed line whose text is a fill marker, followed by a non-blank,
    non-placeholder content line). A FILLED doc answers all three under headings;
    the bare-clone stub carries the markers as instructional BULLETS under an
    'interview-fill structure' heading, NOT as answered `## <marker>` sections --
    so this returns the empty set for the live stub (the canary test guards that).
    Used in BOTH states: STATE A must have NONE; STATE B must have ALL THREE."""
    answered: set[str] = set()
    lines = text.splitlines()
    for i, raw in enumerate(lines):
        line = raw.strip()
        if not line.startswith("#"):
            continue
        heading = line.lstrip("#").strip().lower().rstrip(":")
        marker = next(
            (m for m in _FILL_MARKERS if heading == m or heading.startswith(m)),
            None)
        if marker is None:
            continue
        # Find the next non-blank line -- a real answer (not a placeholder).
        for nxt in lines[i + 1:]:
            body = nxt.strip()
            if not body:
                continue
            if body.startswith("#"):
                break  # next heading, no content under this one
            low = body.lower()
            if any(tok in low for tok in _PLACEHOLDER_TOKENS):
                break  # an explicit placeholder, not a real answer
            answered.add(marker)  # a substantive answer line under this heading
            break
    return answered


# Returns [] iff `text` is an acceptable APPLICATION.md (bare-clone stub OR
# filled instance); else the reasons. Two EXPLICIT valid states + reject the
# mixed/partial state, BOTH judged on real ANSWERED fill content (not just marker
# substrings -- R5). STATE A (stub): the FULL declaration sentence "this file is
# empty by design" + the seed-framing ("empty seed" / "until the interview runs")
# + NO answered fill section. STATE B (filled): no stub sentence + ALL three fill
# markers ANSWERED + no residual stub fragment. Anything else is a mixed half-edit.
def application_acceptance_violations(text: str) -> list[str]:
    lower = text.lower()
    out: list[str] = []
    if "SEAM 1" not in text:
        out.append("missing the seam-1 marker")

    stub_marker = "this file is empty by design"
    has_stub_sentence = stub_marker in lower
    # The un-filled stub's distinctive seed-framing -- stable template phrasing the
    # bare clone carries and a FILLED doc removes (it is replaced by real content).
    has_stub_framing = any(f in lower for f in _STUB_FRAMING_FRAGMENTS)
    answered = _answered_fill_markers(text)

    if has_stub_sentence:
        # STATE A (bare-clone stub) -- valid ONLY IF the seed-framing is intact AND
        # there is NO answered fill section. A doc that kept the stub sentence but
        # dropped the framing, OR retained the framing yet ALSO answered fill
        # sections, is the mixed half-edit: the stub declaration must be removed
        # when the doc is filled (R1 m2 / R4 MAJOR).
        if not has_stub_framing or answered:
            out.append("APPLICATION.md carries the 'empty by design' stub "
                       "declaration alongside a non-stub state (missing the "
                       "bare-clone framing or carrying real answered fill "
                       "sections) -- a filled doc must REMOVE the stub "
                       "declaration (mixed half-edit)")
        return out
    # No stub sentence -> the INSTANTIATED state. Valid STATE B requires ALL three
    # fill markers ANSWERED with real content (not just present as placeholder
    # headings -- R5) AND no residual stub-only fragment of ANY kind (the full
    # sentence is gone, but the seed-framing / stub title left behind is the same
    # illegal mixed half-edit -- auto-review MAJOR).
    for m in _FILL_MARKERS:
        if m not in answered:
            out.append(f"instantiated APPLICATION.md fill section {m!r} is not "
                       "answered (missing or placeholder-only -- a filled doc "
                       "needs real content under each fill section)")
    residue = [f for f in _STUB_RESIDUE_FRAGMENTS if f in lower]
    if residue:
        # A stub-only fragment (the full sentence, the seed-framing, or the stub
        # title) survives in a filled doc -> the illegal half-edit / mixed state.
        out.append("instantiated APPLICATION.md leaves a residual bare-stub "
                   f"fragment {sorted(residue)!r} (the stub declaration/framing "
                   "must be removed when the doc is filled)")
    return out


class ReadmeAcceptanceTest(unittest.TestCase):
    """A.2 -- README names the four seams, the germination line, the kernel."""

    def setUp(self) -> None:
        self.text = _read(harness_readme_relpath())
        self.lower = self.text.lower()

    def test_names_all_four_seams(self) -> None:
        # The README must name each of the four seams by its artifact.
        for marker in ("APPLICATION.md", "implementer-template.md",
                       "review-gate-seam.md", "launch_role.ps1"):
            self.assertIn(marker, self.text, f"README must name seam {marker}")
        self.assertIn("seam", self.lower, "README must use the seam framing")

    def test_germination_one_liner(self) -> None:
        self.assertIn("launch charc", self.lower,
                      "README must carry the germination one-liner")

    def test_points_at_kernel_docs(self) -> None:
        for marker in ("docs/charc-bootstrap.md", "docs/charc-charter.md"):
            self.assertIn(marker, self.text, f"README must point at {marker}")

    def test_staged_guarantee_note(self) -> None:
        self.assertIn("staged", self.lower, "README must state the staged guarantee")
        self.assertIn("bare clone", self.lower,
                      "README staged-guarantee must mention the bare-clone case")

    def test_validate_command_documented(self) -> None:
        # F.3 acceptance: the README names the validate command (unittest).
        self.assertIn("python -m unittest discover", self.text,
                      "README must name the validation command")


class ApplicationAcceptanceTest(unittest.TestCase):
    """A.3 -- APPLICATION.md: the seam-1 stub on a bare clone, the filled instance
    definition once the interview runs. Accepts BOTH states (via the shared
    application_acceptance_violations helper, above)."""

    def setUp(self) -> None:
        self.text = _read("APPLICATION.md")
        self.lower = self.text.lower()

    def test_carries_seam1_marker(self) -> None:
        self.assertIn("SEAM 1", self.text,
                      "APPLICATION.md must carry the seam-1 marker")

    def test_has_interview_fill_structure(self) -> None:
        # The placeholder structure the interview fills (still present on a bare
        # clone; a filled instance carries the real content under these headings).
        for marker in ("what the project does", "domain", "success criteria"):
            self.assertIn(marker, self.lower,
                          f"stub must carry the interview placeholder {marker!r}")

    def test_live_application_is_acceptable(self) -> None:
        # The LIVE APPLICATION.md (bare-clone stub or filled instance) is
        # acceptable -- routed through the SAME helper the simulated-payload tests
        # use, so the real tree stays green through identical logic.
        self.assertEqual(
            application_acceptance_violations(self.text), [],
            "the live APPLICATION.md must be an acceptable state")


class ApplicationSimulatedPayloadTest(unittest.TestCase):
    """The B-9 dual-state conversion, witnessed on SIMULATED payloads (the live-
    file test alone cannot exercise a FILLED APPLICATION.md on a bare clone)."""

    def test_filled_instance_payload_is_accepted(self) -> None:
        # A FILLED APPLICATION.md (no empty-by-design line, real domain content)
        # is accepted by the converted logic. The OLD stub-only gate
        # (assertIn "empty by design") would REJECT this exact payload -- that is
        # the pre/post witness the live-file test cannot provide.
        filled = ("<!-- SEAM 1 -->\n# MyApp\n"
                  "## What the project does\nA real thing.\n"
                  "## Domain\nThe domain.\n## Success criteria\nShips.\n"
                  "## Constraints\nNone.\n")
        self.assertEqual(
            application_acceptance_violations(filled), [],
            "the converted acceptance must accept a filled instance")
        # Witness the distinguishing delta: the OLD gate required the line.
        self.assertNotIn("empty by design", filled.lower())

    def test_bare_clone_stub_payload_is_accepted(self) -> None:
        # The bare-clone stub (still empty-by-design, with the seed-framing intact)
        # stays acceptable -- the conversion does NOT weaken the stub state.
        stub = ("<!-- SEAM 1 -->\n# APPLICATION (stub)\n"
                "This file is empty by design.\n"
                "Until the interview runs, this is the empty seed.\n"
                "## What the project does\n_(placeholder)_\n## Domain\n_()_\n"
                "## Success criteria\n_()_\n")
        self.assertEqual(
            application_acceptance_violations(stub), [],
            "the bare-clone stub must still be accepted")

    def test_filled_doc_that_still_declares_stub_is_rejected(self) -> None:
        # A filled doc that LEAVES a residual 'empty by design' fragment is caught
        # (the illegal half-edit / mixed state -- non-trivial dual-state logic).
        bad = ("<!-- SEAM 1 -->\n# MyApp\nreal content but also: empty by design\n"
               "## What the project does\nx\n## Domain\nx\n## Success criteria\nx\n")
        self.assertTrue(
            application_acceptance_violations(bad),
            "a filled doc still carrying empty-by-design must be caught")

    def test_filled_doc_retaining_full_stub_sentence_is_rejected(self) -> None:
        # Codex R1 m2: a FILLED doc that retained the FULL stub sentence (not just
        # a fragment) but DROPPED the bare-clone seed-framing -- its body is real
        # content -- is the mixed half-edit. The old logic accepted it as a stub;
        # the framing discriminator now catches it (the stub sentence must be
        # removed when the doc is filled).
        bad = ("<!-- SEAM 1 -->\n# MyApp\nThis file is empty by design.\n"
               "## What the project does\nA real product that ships things.\n"
               "## Domain\nThe real domain.\n## Success criteria\nIt ships.\n")
        self.assertTrue(
            application_acceptance_violations(bad),
            "a filled doc retaining the full stub sentence must be caught")

    def test_full_stub_framing_plus_real_filled_sections_is_rejected(self) -> None:
        # Codex R4 MAJOR: a doc that kept the FULL stub sentence AND the entire
        # bare-clone framing ("until the interview runs" / "empty seed") but ALSO
        # appended real ANSWERED fill sections is the mixed half-edit -- the
        # framing-only discriminator (R1 m2) accepted it; the answered-fill-heading
        # discriminator now rejects it (a filled doc must remove the stub
        # declaration). The live stub stays valid: its fill markers are bullets
        # under 'interview-fill structure', not answered `## <marker>` sections.
        bad = ("<!-- SEAM 1 -->\n# MyApp\nThis file is empty by design.\n"
               "Until the interview runs, this is the empty seed.\n"
               "## What the project does\nA real product that ships things.\n"
               "## Domain\nThe real domain.\n## Success criteria\nIt ships.\n")
        self.assertTrue(
            application_acceptance_violations(bad),
            "a doc keeping the full stub framing AND real answered fill sections "
            "must be caught (the stub declaration must be removed when filled)")

    def test_stub_removed_but_placeholders_remain_is_rejected(self) -> None:
        # Codex R5 MAJOR (STATE B symmetry): a doc that REMOVED the stub sentence
        # but left the fill sections as placeholders (not answered) is a half-edit
        # -- it is NOT a valid instantiated app. The old substring-based
        # has_all_fill_sections accepted it (the markers are present); the answered
        # -content model now rejects it (a filled doc needs real content under each
        # fill section). The fully-answered filled instance still passes.
        bad = ("<!-- SEAM 1 -->\n# App\n"
               "## What the project does\n_(placeholder)_\n"
               "## Domain\n_()_\n## Success criteria\ntbd\n")
        violations = application_acceptance_violations(bad)
        self.assertTrue(
            violations,
            "a stub-removed doc with placeholder-only fill sections must be caught")
        # And it specifically flags the unanswered sections.
        self.assertTrue(
            any("not answered" in v for v in violations),
            "the rejection must cite the unanswered fill sections")

    def test_filled_doc_with_stub_framing_residue_is_rejected(self) -> None:
        # codex-auto-review MAJOR (STATE B residue symmetry): a doc with the full
        # stub SENTENCE removed and ALL three sections answered but the stub
        # FRAMING / title residue left behind ("until the interview runs" / "empty
        # seed" / "application (stub)") is still the illegal mixed half-edit -- the
        # STATE B branch must reject ANY stub-only residue, not just the bare
        # "empty by design" fragment.
        bad = ("<!-- SEAM 1 -->\n# APPLICATION (stub)\n"
               "Until the interview runs, this is the empty seed.\n"
               "## What the project does\nA real answer.\n"
               "## Domain\nReal.\n## Success criteria\nShips.\n")
        violations = application_acceptance_violations(bad)
        self.assertTrue(
            violations,
            "a filled doc with stub framing/title residue must be caught")
        self.assertTrue(
            any("residual bare-stub fragment" in v for v in violations),
            "the rejection must cite the residual stub fragment")


class OrchestratorContextAcceptanceTest(unittest.TestCase):
    """C.1 -- generic orchestrator-context, orchestrator-inbox-realized."""

    def setUp(self) -> None:
        self.text = _read("docs/orchestrator-context.md")
        self.lower = self.text.lower()

    def test_operating_model_present(self) -> None:
        for marker in ("dispatch brief", "return report", "qa", "accept"):
            self.assertIn(marker, self.lower, f"must cover {marker!r}")
        self.assertIn("operator drives", self.lower)

    def test_orchestrator_inbox_realized_singular(self) -> None:
        # ARC-8: the orchestrator inbox is the singular comms/orchestrator/inbox,
        # addressed by bare --to orchestrator (no per-generation session_id).
        self.assertIn("comms/orchestrator/inbox", self.text)
        self.assertIn("--to orchestrator", self.text)
        # NOT the legacy "no orchestrator inbox in V1" framing, NOR the retired
        # per-generation session_id addressing.
        self.assertNotIn("no orchestrator inbox", self.lower)
        self.assertNotIn("orchestrator/<session_id>", self.text)
        self.assertNotIn("--to orchestrator:<session_id>", self.text)

    def test_implementer_never_posts_to_mailbox(self) -> None:
        self.assertIn("never", self.lower)
        self.assertIn("mailbox", self.lower)

    def test_defers_review_mechanism_to_seam(self) -> None:
        self.assertIn("review-gate-seam.md", self.text)


def _deleted_addressing_hits(text: str, patterns: tuple[str, ...]) -> list[str]:
    """The dead-command / retired-machinery tokens REPRODUCED in text -- a PURE
    substring match, no instruction-vs-correction NLP (that discriminator was
    brittle: it both false-negatived a multi-clause "do not" line and
    false-positived a "has been replaced" correction). The invariant is simpler
    and robust: a LIVE durable operating-model doc must not REPRODUCE the dead
    command syntax AT ALL -- a "this changed" note DESCRIBES the change without
    quoting the dead command (e.g. "address the orchestrator directly, no session
    suffix" -- NOT "`--to orchestrator:<session_id>` is replaced"). Shared logic,
    driven by BOTH the live-doc test and the non-vacuity test."""
    return [p for p in patterns if p in text]


def _durable_operating_docs() -> list[str]:
    """The LIVE OPERATING docs an agent FOLLOWS to operate -- the real threat
    surface (a stale addressing directive in one breaks a live agent), DISCOVERED
    BY PATTERN so a future operating doc is auto-covered without editing a list:
    docs/*-context / *-bootstrap / *-charter, PLUS the live dispatch recipe + the
    README. Nothing else -- see the class docstring for the exclusion rationale."""
    docs = REPO_ROOT / "docs"
    found: set[str] = set()
    for pat in ("*-context.md", "*-bootstrap.md", "*-charter.md"):
        for p in docs.glob(pat):
            found.add(f"docs/{p.name}")
    found.add("docs/dispatch-recipe.md")
    found.add("README.md")
    found.add(harness_readme_relpath())
    return sorted(found)


class DurableDocsNoDeletedAddressingTest(unittest.TestCase):
    """ARC-8 (FIX-2): no LIVE OPERATING doc an agent FOLLOWS may REPRODUCE the
    deleted per-generation orchestrator addressing. The other doc-acceptance tests
    assert a doc EXISTS + carries the singular model in the spots they check -- so
    a MISSED doc (a peer director's context doc with a stale `--to orchestrator:<session_id>`)
    slipped through. This closes the CLASS with a ROBUST PURE PATTERN (no
    instruction-vs-correction NLP): a live operating doc DESCRIBES the change, it
    does not quote the dead command.

    SCOPE = the OPERATING docs (see _durable_operating_docs): *-context /
    *-bootstrap / *-charter + the dispatch recipe + README. These are what a live
    agent reads to operate, so a stale directive here is the real hazard.

    DELIBERATELY EXCLUDED, each with a reason:
      * TEMPLATE-FEEDBACK docs (docs/template-feedback-*) -- upstream META
        (proposals to the template-CHARC); agents do NOT bootstrap from them and
        they legitimately CONTRAST old-vs-new. The planned inter-instance comms
        RECONCILIATION owns them, not this guard.
      * HISTORICAL dispatch briefs (docs/briefs/walk-*) -- past-phase records
        (they reference June-2026 plans); do not rewrite history.
      * TRANSIENT per-role STATE files (orchestrator-state.md / <role>-state.md /
        charc-state.md) + role memories -- overwritten each generation; CHARC's
        post-landing sweep + each role's own cutover maintenance.

    DISCLOSED LIMIT: this flags LITERAL dead-command syntax. A PROSE-ONLY
    paraphrase ("address the live generation using its session id as a suffix")
    is outside a pattern guard -- irreducible (the analog of "a golden can't catch
    arbitrary logic"). Mitigated because the operating-doc set is NARROW and
    human-reviewed (this arc read each for a prose-only stale directive too)."""

    # Literal dead-command / retired-machinery tokens. A LIVE durable doc must not
    # REPRODUCE any of these (describe-not-reproduce) -- pure substring match.
    DELETED_ADDRESSING_PATTERNS = (
        "orchestrator:<",          # the explicit per-generation address token
        "--to orchestrator:",      # addressing a specific generation
        "comms/sessions",          # the retired session-registry path
        "--session ",              # the deleted per-generation drain flag
        "= newest-live",           # "bare --to orchestrator = newest-live"
        "newest-live generation",  # the newest-live resolution as a target
        "comms-orchestrator-registry",  # a pointer to the RETIRED registry doc
    )

    def test_no_durable_doc_reproduces_deleted_addressing(self) -> None:
        offenders: list[str] = []
        for rel in _durable_operating_docs():
            for pat in _deleted_addressing_hits(_read(rel),
                                                self.DELETED_ADDRESSING_PATTERNS):
                offenders.append(f"{rel}: {pat!r}")
        self.assertEqual(
            offenders, [],
            "live durable operating-model docs must not REPRODUCE the deleted "
            "per-generation orchestrator addressing (describe-not-reproduce); "
            f"found: {offenders}")

    def test_scope_is_the_operating_docs_only(self) -> None:
        # The guarded set must be exactly the OPERATING docs an agent follows (a
        # guard over an empty set is vacuous; an over-inclusive one sweeps META).
        covered = set(_durable_operating_docs())
        for rel in ("docs/orchestrator-context.md",
                    "docs/charc-charter.md", "docs/charc-bootstrap.md",
                    "docs/dispatch-recipe.md", "README.md"):
            self.assertIn(rel, covered, f"{rel} must be in the operating scope")
        # EXCLUDED (each with its own disposition -- see the class docstring):
        # template-feedback META, historical briefs, transient state files.
        for rel in ("docs/template-feedback-comms-simplification.md",
                    "docs/template-feedback-close-hook-inbox-check.md",
                    "docs/orchestrator-state.md",
                    "docs/charc-state.md"):
            self.assertNotIn(
                rel, covered,
                f"{rel} is META/transient -- out of the operating-doc scope")

    def test_the_pure_pattern_is_non_vacuous(self) -> None:
        P = self.DELETED_ADDRESSING_PATTERNS
        # A doc REPRODUCING the dead command FAILS in ANY context -- including the
        # two codex cases the NLP discriminator got wrong: a multi-clause "do not"
        # line (false-negative under NLP) and a "has been replaced" correction
        # that QUOTES the command (false-positive under NLP). Pure match flags all.
        for reproduction in (
                "Post via `--to orchestrator:legacy`.",
                "Do not wait: post with `--to orchestrator:legacy` now.",
                "`--to orchestrator:<session_id>` has been replaced by bare form.",
                "Drain via `read --role orchestrator --session <id>`."):
            self.assertTrue(
                _deleted_addressing_hits(reproduction, P),
                f"a doc reproducing the dead command must be flagged: {reproduction!r}")
        # DESCRIBE-not-reproduce PASSES (the corrected-doc shape):
        for described in (
                "Address the orchestrator directly -- `--to orchestrator`, no session suffix.",
                "The per-generation session-suffix addressing was retired; use bare addressing.",
                "The orchestrator inbox is singular now (no newest-live, no registry)."):
            self.assertEqual(
                _deleted_addressing_hits(described, P), [],
                f"a describe-not-reproduce phrasing must pass: {described!r}")


class DispatchRecipeAcceptanceTest(unittest.TestCase):
    """C.2 -- generic implementer protocol; substrate defaults NAMED."""

    def setUp(self) -> None:
        self.text = _read("docs/dispatch-recipe.md")
        self.lower = self.text.lower()

    def test_four_generic_concepts(self) -> None:
        for marker in ("isolated workspace", "product", "validation",
                       "acceptance"):
            self.assertIn(marker, self.lower, f"must frame {marker!r}")

    def test_substrate_defaults_named_not_assumed(self) -> None:
        self.assertIn("substrate default", self.lower)
        self.assertIn("worktree", self.lower)  # named as the default
        self.assertIn("diff", self.lower)      # acceptance default

    def test_review_loop_points_at_seam_not_a_mechanism(self) -> None:
        self.assertIn("review-gate-seam.md", self.text)
        # The recipe references the optional reviewer reference but does not put
        # the mechanism in the protocol body (it is the seam fill).
        self.assertIn("seam 3", self.lower)

    def test_reports_up_in_chat_not_mailbox(self) -> None:
        self.assertIn("mailbox", self.lower)


class ImplementerTemplateAcceptanceTest(unittest.TestCase):
    """C.3 -- the seam-2 generic cell template."""

    def setUp(self) -> None:
        self.text = _read(".claude/agents/implementer-template.md")
        self.lower = self.text.lower()

    def test_points_at_dispatch_recipe(self) -> None:
        self.assertIn("docs/dispatch-recipe.md", self.text)

    def test_never_post_to_mailbox_discipline(self) -> None:
        # newline-tolerant (the phrase may wrap across lines).
        normalized = " ".join(self.lower.split())
        self.assertIn("never post to a role mailbox", normalized)

    def test_names_no_application_uses_placeholder(self) -> None:
        self.assertIn("<application>", self.text)

    def test_seam2_marker(self) -> None:
        self.assertIn("SEAM 2", self.text)


class ReviewGateSeamAcceptanceTest(unittest.TestCase):
    """G.1 -- the mechanism-agnostic contract + three parts + defaults."""

    def setUp(self) -> None:
        self.text = _read("docs/review-gate-seam.md")
        self.lower = self.text.lower()

    def test_three_parts(self) -> None:
        self.assertIn("review-to-convergence", self.lower)
        self.assertIn("gate", self.lower)
        self.assertIn("disciplines", self.lower)

    def test_extension_points_named(self) -> None:
        for point in ("REVIEWER", "PRODUCT_REPRESENTATION", "SEVERITY_RUBRIC",
                      "CONVERGENCE_CRITERION", "GATE_CHECKS", "WITNESS",
                      "ACCEPTANCE"):
            self.assertIn(point, self.text, f"must name {point}")

    def test_no_substrate_token_no_codex_path(self) -> None:
        # The seam doc is mechanism-agnostic: NO substrate word, NO codex path.
        self.assertNotIn("codex-reviewer", self.lower)
        self.assertNotIn("codex", self.lower)
        self.assertNotIn("wsl", self.lower)

    def test_filter_not_gate_discipline(self) -> None:
        self.assertIn("filter", self.lower)

    def test_points_at_instance_fill_doc(self) -> None:
        # B-9 point 4: the agnostic seam doc points at the per-instance concrete
        # fill convention (docs/review-gate-<app>.md) so a germination's concrete
        # reviewer/gate fill does NOT pollute this mechanism-agnostic contract.
        # The pointer names the <app> PLACEHOLDER, never a concrete mechanism --
        # so test_no_substrate_token_no_codex_path stays green (the contract
        # remains substrate-free).
        self.assertIn("review-gate-<app>.md", self.text,
                      "the seam doc must name the per-instance fill convention")


class CodexReviewerAcceptanceTest(unittest.TestCase):
    """G.2 -- the optional substrate-coupled reviewer reference."""

    def setUp(self) -> None:
        self.text = _read("docs/codex-reviewer.md")
        self.lower = self.text.lower()

    def test_substrate_coupled_reference(self) -> None:
        # Codex / WSL allowed here (the file-scope exception file).
        self.assertIn("codex", self.lower)
        self.assertIn("wsl", self.lower)

    def test_framed_optional_replaceable(self) -> None:
        self.assertIn("replaceable", self.lower)
        self.assertIn("not the reviewer", self.lower)

    def test_pointed_at_by_dispatch_recipe_and_readme(self) -> None:
        # The seam->plug-in linkage lives in the dispatch-recipe + README, NOT
        # the seam doc.
        self.assertIn("codex-reviewer.md", _read("docs/dispatch-recipe.md"))
        self.assertIn("docs/codex-reviewer.md", _read(harness_readme_relpath()))


class CharterAcceptanceTest(unittest.TestCase):
    """H.1 -- the generic director kernel."""

    def setUp(self) -> None:
        self.text = _read("docs/charc-charter.md")
        self.lower = self.text.lower()

    def test_role_definition_and_disciplines(self) -> None:
        self.assertIn("director", self.lower)
        self.assertIn("owns harness", self.lower)
        self.assertIn("tripwire", self.lower)
        self.assertIn("debt", self.lower)  # debt-register concept
        self.assertIn("custodian of form", self.lower)

    def test_comms_routing(self) -> None:
        self.assertIn("decision_request", self.text)
        self.assertIn("operator", self.lower)
        self.assertIn("never posts to a mailbox", self.lower)

    def test_peer_director_add_checklist(self) -> None:
        self.assertIn("peer-director-add checklist", self.lower)

    def test_peer_director_checklist_names_genericity_registration(self) -> None:
        # B-12 Gap 2: the section-8 peer-director-add checklist must gain the
        # genericity-registration item. Assert UNIQUE CONTIGUOUS substrings from
        # the NEW item (a loose "instance surface"/"genericity" check could
        # false-pass on prose elsewhere). Use the shared _norm helper so line-
        # wrapping does not break the contiguous match.
        norm = _norm(self.text)
        self.assertIn("the new director's instance docs", norm.lower())
        self.assertIn("is_instance_surface", norm)
        self.assertIn("instance_surface_relpaths", norm.lower())

    def test_peer_director_checklist_splits_kernel_vs_instance_authority(self) -> None:
        # B-12 Gap 3: section-8 item 2 must split "generic contract already in the
        # kernel" vs "instance authority in the new director's own context doc".
        # Assert UNIQUE contiguous fragments from the rewritten item 2 via _norm
        # (a loose kernel/already check false-passes -- 'kernel' pre-exists).
        norm = _norm(self.text)
        self.assertIn(
            "the generic peer-director contract is already in this kernel", norm)
        self.assertIn(
            "goes in its own `docs/<role>-context.md` instance doc", norm)


class BootstrapAcceptanceTest(unittest.TestCase):
    """H.2/H.3 -- the first-run flow + 5-step checklist + folded bring-up."""

    def setUp(self) -> None:
        self.text = _read("docs/charc-bootstrap.md")
        self.lower = self.text.lower()

    def test_names_all_five_checklist_steps(self) -> None:
        for marker in ("APPLICATION.md", "implementer-template.md",
                       "review-gate-seam.md", "launch_role.ps1"):
            self.assertIn(marker, self.text)
        self.assertIn("bring up the orchestrator", self.lower)

    def test_staged_guarantee_stated(self) -> None:
        self.assertIn("staged guarantee", self.lower)
        self.assertIn("bare clone", self.lower)

    def test_verify_comms_split_pre_and_post_step5(self) -> None:
        # PRE-step-5 verifies charc<->operator without a live orchestrator;
        # POST-step-5 (in step 5) verifies the orchestrator round-trip.
        self.assertIn("pre-step-5", self.lower)
        self.assertIn("post-step-5", self.lower)
        # No step-2 check requires a live orchestrator.
        self.assertIn("no orchestrator", self.lower)

    def test_folded_orchestrator_bringup_block_realized_inbox(self) -> None:
        # The bring-up block lives IN this doc (no separate file by default) and
        # reflects the REALIZED SINGULAR inbox (ARC-8: no per-generation subtree).
        self.assertIn("HARNESS_ROLE=orchestrator", self.text)
        self.assertIn("comms/orchestrator/inbox", self.text)
        self.assertIn("--to orchestrator", self.text)
        self.assertNotIn("orchestrator/<session_id>", self.text)

    def test_interview_fills_seams_by_name(self) -> None:
        for seam in ("seam 1", "seam 2", "seam 3"):
            self.assertIn(seam, self.lower)

    def test_names_review_gate_app_convention(self) -> None:
        # B-9 point 4: the bootstrap documents that the concrete seam-3 fill lives
        # in a NEW docs/review-gate-<app>.md instance doc (NOT review-gate-seam.md,
        # which stays the mechanism-agnostic contract).
        self.assertIn("review-gate-<app>.md", self.text,
                      "the bootstrap must name the review-gate-<app>.md convention")

    def test_documents_resume_role_command(self) -> None:
        # B-16 part (b): the bootstrap doc carries the role-on-resume note +
        # the explicit re-set command (placeholder-only).
        self.assertIn("$env:HARNESS_ROLE='<role>'", self.text)
        self.assertIn("--resume <id>", self.text)


if __name__ == "__main__":
    unittest.main()
