"""J.3 -- manifest accounting (one model, no dual count).

Every tracked file is EITHER a section-4 shipped-manifest file OR a repository-
support appendix file (tests + config). This test pins that exact partition so an
implementer/CHARC knows which files are scaffold surface vs repository support,
and so a stray file outside both sets is caught.
"""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

import genericity_lists as gl

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# The section-4 SHIPPED-SCAFFOLD MANIFEST (the operating surface a fresh CHARC
# uses). ARC-8 collapsed the comms model onto uniform singular inboxes: the
# per-generation SessionStart/SessionEnd hooks + the registry doc are gone, and
# the surviving role-recovery store + shared helpers folded into
# user_prompt_submit.py (the HTMX client stays inlined in comms_ui.py; the
# orchestrator bring-up stays folded in charc-bootstrap.md) -- ZERO extra files.
SHIPPED_MANIFEST = {
    "README.md",
    # 2026-11-09: the scaffold README text, moved out of the root README when an
    # instantiated project makes the root README its application's user page.
    "docs/harness-readme.md",
    "APPLICATION.md",
    "comms/.gitkeep",
    "scripts/role_mail.py",
    "scripts/comms_ui.py",
    "scripts/launch_role.ps1",
    "scripts/cell_depth.py",
    # 2026-10-27: the dual-model implementer lane (generic/stdlib-only/no-app
    # vocabulary): the two weekly-usage readouts and the Codex cell driver.
    "scripts/usage_codex.py",
    "scripts/usage_claude.py",
    "scripts/codex_cell.py",
    ".claude/settings.json",
    ".claude/hooks/user_prompt_submit.py",
    ".claude/hooks/stop.py",
    ".claude/agents/implementer-template.md",
    "docs/charc-charter.md",
    "docs/charc-bootstrap.md",
    "docs/model-prompting-standard.md",
    "docs/charc-state.md",
    "docs/orchestrator-context.md",
    "docs/dispatch-recipe.md",
    "docs/review-gate-seam.md",
    "docs/codex-reviewer.md",
}

# The repository-support appendix: a repo's standard config (tracked + guard-
# scanned but NOT scaffold-manifest files).
SUPPORT_CONFIG = {
    "pyproject.toml",
    ".gitignore",
    # ARC-5 (2026-07-23): byte-integrity attributes for the committed evidence base
    # (_graded_evidence/** -text). A repo-root config file, exactly like .gitignore.
    ".gitattributes",
}


def _tracked() -> set[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=str(REPO_ROOT), capture_output=True, text=True,
        check=True).stdout
    return {line.replace("\\", "/") for line in out.splitlines() if line}


def _unaccounted(tracked: set[str]) -> list[str]:
    """The files in `tracked` that are neither manifest, support, tests, nor
    instance surface (the partition the gate asserts is empty). The single
    accounting model -- the production gate AND the distinguishing test both go
    through HERE, so the instance-surface branch cannot be tested by a
    re-implementation (B-9; the production-path witness)."""
    out = []
    for rel in sorted(tracked):
        if rel in SHIPPED_MANIFEST or rel in SUPPORT_CONFIG:
            continue
        if rel.startswith("tests/"):
            continue  # the section-2.1 tests/** support appendix
        if gl.is_instance_surface(rel):
            continue  # the instantiation surface (see genericity_lists.py)
        out.append(rel)
    return out


class ManifestAccountingTest(unittest.TestCase):
    def test_manifest_count_is_twenty_three(self) -> None:
        # The shipped-manifest count: 17 post-ARC-8, PLUS the 2026-08 harness-wide
        # model-prompting standard (docs/model-prompting-standard.md) = 18, PLUS
        # the 2026-09 dispatcher depth instrument (scripts/cell_depth.py,
        # generic/stdlib-only/no-app-vocabulary) = 19, PLUS the 2026-10-27
        # dual-model implementer lane (two usage readouts + the Codex cell
        # driver, same posture) = 22, PLUS the 2026-11-09 scaffold README file
        # (docs/harness-readme.md) = 23.
        self.assertEqual(
            len(SHIPPED_MANIFEST), 23,
            "the shipped manifest is 23 files (17 post-ARC-8 plus the "
            "model-prompting standard, the cell-depth instrument, the three "
            "dual-model lane scripts and the scaffold README file)")

    def test_charc_state_pointer_is_shipped(self) -> None:
        # The state-pointer file must be a tracked shipped-manifest file.
        self.assertIn("docs/charc-state.md", SHIPPED_MANIFEST)
        self.assertIn("docs/charc-state.md", _tracked())

    def test_every_shipped_manifest_file_exists(self) -> None:
        tracked = _tracked()
        missing = SHIPPED_MANIFEST - tracked
        self.assertEqual(
            missing, set(),
            f"section-4 manifest files missing from the tree: {sorted(missing)}")

    def test_every_tracked_file_is_manifest_or_support(self) -> None:
        # The single accounting model: a file is a manifest file OR a support
        # file (config OR a tests/ file) OR an instance-surface file (B-9).
        # Nothing in between. Drives the SAME _unaccounted helper the
        # distinguishing test drives, so the partition logic is single-sourced.
        unaccounted = _unaccounted(_tracked())
        self.assertEqual(
            unaccounted, [],
            "every tracked file must be a section-4 manifest file OR a support "
            f"file (config / tests) OR instance surface; unaccounted: {unaccounted}")

    def test_production_partition_accounts_instance_surface(self) -> None:
        # Drive the REAL partition helper (the one the production gate uses) with
        # a simulated filled-germination tracked set. It yields [] ONLY because
        # the helper executes `if gl.is_instance_surface(rel): continue`. WITHOUT
        # that branch the instance files are unaccounted (the pre-fix path), so
        # this test FAILS pre-fix and PASSES post-fix -- the production method is
        # the witness (no re-implementation, no bare is_instance_surface() call).
        simulated = set(SHIPPED_MANIFEST) | SUPPORT_CONFIG | {
            "docs/briefs/arc-1.md", "docs/review-gate-myapp.md",
            ".claude/agents/implementer-fast.md",
        }
        self.assertEqual(
            _unaccounted(simulated), [],
            "the production partition must account instance surface")

    def test_doc_partition_matches_manifest_docs(self) -> None:
        # Single-source: the guard's docs/ partition (CORE_DOC_RELPATHS +
        # INSTANCE_STUB_RELPATHS) must, as a DISJOINT union, equal the docs/*.md
        # subset of the shipped manifest. If a new manifest doc is added but
        # forgotten in BOTH guard sets, the suffix patterns could wrongly exempt
        # it -- this cross-check FAILS loud at build time (the future-safe + no-
        # blur witness).
        manifest_docs = {m for m in SHIPPED_MANIFEST
                         if m.startswith("docs/") and m.endswith(".md")}
        core = set(gl.CORE_DOC_RELPATHS)
        stub = set(gl.INSTANCE_STUB_RELPATHS)
        self.assertEqual(
            core & stub, set(),
            "CORE_DOC_RELPATHS and INSTANCE_STUB_RELPATHS must be disjoint")
        self.assertEqual(
            core | stub, manifest_docs,
            "the docs/ partition (core + instance-stub) must equal the "
            "manifest's docs/*.md set (single source; no drift)")

    def test_agent_partition_matches_manifest_agents(self) -> None:
        # Codex R3 -- the AGENTS namespace must have the same registry cross-check
        # as docs (symmetry). A shipped core .claude/agents/*.md added to the
        # manifest but forgotten in CORE_AGENT_RELPATHS would otherwise pass
        # manifest accounting AND be classified instance surface by
        # _matches_implementer_cell -- skipping the core guard (the registry-only-
        # forgotten case the docs cross-check already closes). Assert the manifest's
        # .claude/agents/*.md set equals CORE_AGENT_RELPATHS (the template has no
        # agent instance stub; one would join this union like INSTANCE_STUB_RELPATHS
        # does for docs). FAILS loud at build time if a new core cell is forgotten
        # in the registry.
        manifest_agents = {m for m in SHIPPED_MANIFEST
                           if m.startswith(".claude/agents/") and m.endswith(".md")}
        self.assertEqual(
            set(gl.CORE_AGENT_RELPATHS), manifest_agents,
            "CORE_AGENT_RELPATHS must equal the manifest's .claude/agents/*.md set "
            "(a shipped core cell forgotten in the registry would be wrongly "
            "exempted as instance surface)")

    def test_default_build_added_no_extra_shipped_files(self) -> None:
        # The three folded details add no files: there is no separate registry.py,
        # no standalone orchestrator_bootstrap.md, no separate htmx asset.
        tracked = _tracked()
        self.assertNotIn(".claude/hooks/registry.py", tracked)
        self.assertNotIn("scripts/orchestrator_bootstrap.md", tracked)
        # No separate htmx asset file shipped (inlined in comms_ui.py).
        self.assertEqual(
            [t for t in tracked if t.endswith("htmx.min.js")], [],
            "the HTMX client is inlined in comms_ui.py (no separate asset file)")


if __name__ == "__main__":
    unittest.main()
