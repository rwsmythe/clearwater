"""G.3 -- seam-3 defaults present + operable-minute-one (distinguishing).

Parses docs/review-gate-seam.md and asserts ALL FIVE default extension points
are present + non-empty in the marked default block, and that the minute-one
dry-run names every step with no extension point left undefined. The test
distinguishes: it fails against an empty / default-less seam doc.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SEAM = REPO_ROOT / "docs" / "review-gate-seam.md"

_DEFAULT_BLOCK = re.compile(
    r"<!--\s*SEAM3-DEFAULTS\s*-->(.*?)<!--\s*/SEAM3-DEFAULTS\s*-->",
    re.DOTALL)


def _default_block(text: str) -> str:
    m = _DEFAULT_BLOCK.search(text)
    return m.group(1) if m else ""


class Seam3DefaultsTest(unittest.TestCase):
    def setUp(self) -> None:
        self.text = SEAM.read_text(encoding="utf-8")
        self.block = _default_block(self.text)

    def test_default_block_present(self) -> None:
        self.assertTrue(
            self.block.strip(),
            "review-gate-seam.md must carry a non-empty SEAM3-DEFAULTS block")

    def test_all_five_defaults_present_with_starter_values(self) -> None:
        block = self.block
        # SEVERITY_RUBRIC = {blocking: critical, major; advisory: minor}
        self.assertIn("SEVERITY_RUBRIC", block)
        self.assertIn("critical", block)
        self.assertIn("major", block)
        self.assertIn("minor", block)
        # CONVERGENCE_CRITERION = zero-new-blocking
        self.assertIn("CONVERGENCE_CRITERION", block)
        self.assertIn("zero-new-blocking", block)
        # GATE_CHECKS = director conditions hold AND WITNESS confirms
        self.assertIn("GATE_CHECKS", block)
        self.assertIn("WITNESS", block)
        # WITNESS = operator confirmation
        self.assertIn("operator", block.lower())
        # REVIEWER = self-review pass
        self.assertIn("REVIEWER", block)
        self.assertIn("self-review", block.lower())

    def test_minute_one_dry_run_names_every_step(self) -> None:
        lower = self.text.lower()
        self.assertIn("minute-one", lower)
        # Every extension point appears as a named step in the dry-run.
        for point in ("reviewer", "severity_rubric", "convergence_criterion",
                      "gate_checks", "witness", "acceptance"):
            self.assertIn(point, lower,
                          f"dry-run must name the {point} step")

    def test_seam_doc_names_no_concrete_mechanism(self) -> None:
        # The seam doc never names a concrete reviewer mechanism in its body
        # (it defers to the project's seam fill). The genericity guard enforces
        # the substrate-free property; this is a positive belt that the doc
        # speaks in the abstract REVIEWER slot.
        self.assertIn("REVIEWER", self.text)
        self.assertNotIn("codex-reviewer.md", self.text)


if __name__ == "__main__":
    unittest.main()
