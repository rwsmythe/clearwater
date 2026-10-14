"""B-9 -- the instance-surface model (is_instance_surface + the CORE-doc registry).

The genericity guard's vocabulary + ticker bans are scoped to the reusable CORE;
the germination INSTANCE surface (APPLICATION.md, the domain implementer cells,
the briefs, the seam-3 fill, a peer director's state/context docs) is application
content by design and is EXEMPT. is_instance_surface() is the shared predicate.

These tests pin the predicate's classification directly (the over-broad-exemption
guard the brief demands): an instance file is exempt, a CORE file (incl. a CORE
doc that happens to match an instance suffix pattern) is NOT.
"""

from __future__ import annotations

import unittest

import genericity_lists as gl


class IsInstanceSurfaceTest(unittest.TestCase):
    def test_explicit_instance_relpaths(self) -> None:
        self.assertTrue(gl.is_instance_surface("APPLICATION.md"))
        self.assertTrue(gl.is_instance_surface("docs/charc-state.md"))

    def test_instance_prefixes(self) -> None:
        self.assertTrue(gl.is_instance_surface("docs/briefs/arc-1.md"))

    def test_instance_suffix_patterns(self) -> None:
        # The seam-3 concrete fill + peer-director state/context docs.
        self.assertTrue(gl.is_instance_surface("docs/review-gate-myapp.md"))
        self.assertTrue(gl.is_instance_surface("docs/rd-state.md"))
        self.assertTrue(gl.is_instance_surface("docs/rd-context.md"))

    def test_domain_implementer_cells_are_instance(self) -> None:
        self.assertTrue(
            gl.is_instance_surface(".claude/agents/implementer-fast.md"))

    def test_core_files_are_not_instance(self) -> None:
        # The over-broad-exemption guard: CORE files (incl. those matching an
        # instance suffix pattern) must NOT be exempted.
        self.assertFalse(gl.is_instance_surface("docs/review-gate-seam.md"))
        self.assertFalse(gl.is_instance_surface("docs/orchestrator-context.md"))
        self.assertFalse(
            gl.is_instance_surface(".claude/agents/implementer-template.md"))
        self.assertFalse(gl.is_instance_surface("scripts/role_mail.py"))
        self.assertFalse(gl.is_instance_surface("docs/charc-charter.md"))

    def test_every_registered_core_doc_stays_core(self) -> None:
        # The future-safe registry gate: every doc registered in CORE_DOC_RELPATHS
        # is NEVER instance surface, even if it matches a suffix pattern. The two
        # sets are disjoint (charc-state.md is an instance stub, not core), so no
        # exception is needed here.
        for d in gl.CORE_DOC_RELPATHS:
            self.assertFalse(
                gl.is_instance_surface(d),
                f"{d} is a registered core doc; it must stay scanned")

    def test_pattern_vs_registry_boundary(self) -> None:
        # The DESIGNED exempt-until-registered boundary (R6 Major 2), executable:
        #   - an UNregistered docs/*-context.md is instance surface (a new
        #     germinated instance doc);
        #   - the registered core orchestrator kernel is NOT.
        self.assertTrue(
            gl.is_instance_surface("docs/comms-context.md"),
            "an unregistered docs/*-context.md is instance surface")
        self.assertFalse(
            gl.is_instance_surface("docs/orchestrator-context.md"),
            "the registered core orchestrator kernel is not instance surface")

    def test_core_doc_and_instance_stub_sets_are_disjoint(self) -> None:
        # The two docs/ partitions never blur (R6 Major 1): charc-state.md lives
        # only in INSTANCE_STUB_RELPATHS, never in CORE_DOC_RELPATHS.
        self.assertEqual(
            set(gl.CORE_DOC_RELPATHS) & set(gl.INSTANCE_STUB_RELPATHS), set(),
            "CORE_DOC_RELPATHS and INSTANCE_STUB_RELPATHS must be disjoint")
        self.assertIn("docs/charc-state.md", gl.INSTANCE_STUB_RELPATHS)
        self.assertNotIn("docs/charc-state.md", gl.CORE_DOC_RELPATHS)

    def test_windows_path_separators_normalized(self) -> None:
        # The predicate normalizes backslashes (git ls-files can emit either).
        self.assertTrue(gl.is_instance_surface("docs\\briefs\\arc-1.md"))
        self.assertTrue(gl.is_instance_surface("APPLICATION.md"))

    def test_nested_docs_suffix_paths_are_not_exempted(self) -> None:
        # Codex R1 MAJOR 1: the docs/ suffix patterns must match a SINGLE path
        # segment only (docs/<name>.md), so a NESTED path under a subdir is NOT
        # exempted -- a future docs/core/foo-context.md core doc would otherwise
        # be silently exempted (the over-broad-exemption hole).
        self.assertFalse(gl.is_instance_surface("docs/core/foo-context.md"))
        self.assertFalse(gl.is_instance_surface("docs/archive/bar-state.md"))
        self.assertFalse(gl.is_instance_surface("docs/sub/review-gate-x.md"))
        # The single-segment instance docs still ARE exempt.
        self.assertTrue(gl.is_instance_surface("docs/rd-context.md"))
        self.assertTrue(gl.is_instance_surface("docs/rd-state.md"))
        self.assertTrue(gl.is_instance_surface("docs/review-gate-myapp.md"))

    def test_implementer_cells_must_be_markdown(self) -> None:
        # Codex R1 MAJOR 1: the implementer-cell pattern is markdown-only (the
        # seam-2 cells are .md). A non-md sibling (e.g. a stray .py) is NOT an
        # instance cell -- it stays CORE-scanned.
        self.assertTrue(
            gl.is_instance_surface(".claude/agents/implementer-fast.md"))
        self.assertFalse(
            gl.is_instance_surface(".claude/agents/implementer-helper.py"))
        self.assertFalse(
            gl.is_instance_surface(".claude/agents/implementer-fast.txt"))
        # And a nested path under the cells dir is not a single-segment cell.
        self.assertFalse(
            gl.is_instance_surface(".claude/agents/sub/implementer-fast.md"))

    def test_registered_core_agent_cells_stay_core(self) -> None:
        # Codex R2 MAJOR 2 (agents-namespace symmetry): every registered CORE
        # agent cell (CORE_AGENT_RELPATHS) is NEVER instance surface -- the same
        # exempt-until-registered gate as CORE_DOC_RELPATHS. The shipped generic
        # cell is the one registered core agent today.
        self.assertIn(".claude/agents/implementer-template.md",
                      gl.CORE_AGENT_RELPATHS)
        for cell in gl.CORE_AGENT_RELPATHS:
            self.assertFalse(
                gl.is_instance_surface(cell),
                f"{cell} is a registered core agent; it must stay scanned")
        # An UNregistered implementer-*.md cell IS instance surface (the designed
        # exempt-until-registered boundary for the agents namespace).
        self.assertTrue(
            gl.is_instance_surface(".claude/agents/implementer-myapp.md"))

    def test_registered_core_always_wins_over_instance_rules(self) -> None:
        # codex-auto-review MINOR: a registered core file is NEVER instance surface,
        # even if it ALSO matches an unconditional instance relpath or prefix -- the
        # registry check runs FIRST. Simulate the worst case by registering paths
        # that collide with an explicit instance relpath and an instance prefix,
        # and assert the registry wins. (Uses a fresh frozenset patched onto the
        # module so the live registries are untouched.)
        from unittest import mock
        colliding_doc = "docs/briefs/foo.md"          # also an instance PREFIX hit
        colliding_relpath = "APPLICATION.md"          # also an explicit instance relpath
        with mock.patch.object(
                gl, "CORE_DOC_RELPATHS",
                frozenset({colliding_doc, colliding_relpath})):
            self.assertFalse(
                gl.is_instance_surface(colliding_doc),
                "a registered core doc under an instance prefix must NOT be exempt")
            self.assertFalse(
                gl.is_instance_surface(colliding_relpath),
                "a registered core doc that is also an explicit instance relpath "
                "must NOT be exempt (registered core always wins)")


if __name__ == "__main__":
    unittest.main()
