"""The core is stdlib-only (zero hard runtime deps) -- proven two ways.

The scaffold's core (scripts/role_mail.py + the three lifecycle hooks, which
carry the shared registry logic) must run with NO third-party packages present.
This is enforced by TWO complementary mechanisms so a lazy / in-function import
cannot slip through:

  1. The STRONG runtime check: each core module is imported AND exercised in a
     SUBPROCESS whose sys.path is stripped of site-packages, so a third-party
     import anywhere on the executed path raises ModuleNotFoundError. A lazy
     `import <thirdparty>` inside a function would fail HERE when that function
     runs -- so the check exercises the public entry points, not just import.

  2. The AST belt: an AST walk over each core file collects EVERY Import /
     ImportFrom node anywhere in the file (module level AND inside functions /
     methods) and asserts each names only a stdlib (or first-party) module.
     This catches a lazy import statically even when no test exercises it.

Either alone is insufficient (top-level-only AST misses lazy imports; a
subprocess-only check misses an unexercised lazy path) -- both ship.

Plus the anchor-vs-runtime gitignore checks (the comms/.gitkeep tracking proof).
"""

from __future__ import annotations

import ast
import subprocess
import sys
import unittest
from pathlib import Path

import genericity_lists as gl
from _corefiles import CORE_RELPATHS, REPO_ROOT, existing_core_files


def _module_name(node: ast.AST) -> list[str]:
    """The top-level module name(s) named by an Import / ImportFrom node."""
    if isinstance(node, ast.Import):
        return [alias.name.split(".")[0] for alias in node.names]
    if isinstance(node, ast.ImportFrom):
        # A relative import (level > 0) is in-tree, never third-party.
        if node.level and node.level > 0:
            return []
        if node.module:
            return [node.module.split(".")[0]]
    return []


# First-party module names the core may import from sibling files (NOT
# third-party). ARC-8: stop.py imports user_prompt_submit (which now hosts the
# role-recovery store + shared helpers); role_mail is loaded by path. Keep tight.
_FIRST_PARTY = {
    "role_mail",
    "user_prompt_submit",
}


class DependencyPostureTest(unittest.TestCase):
    def test_ast_belt_core_imports_are_stdlib_only(self) -> None:
        """EVERY import in every core file names a stdlib or first-party module."""
        stdlib = set(sys.stdlib_module_names)
        offenders: list[str] = []
        core = existing_core_files()
        for path in core:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                for name in _module_name(node):
                    if name in stdlib or name in _FIRST_PARTY or name == "__future__":
                        continue
                    offenders.append(f"{path.name}: third-party import {name!r}")
        self.assertEqual(
            offenders, [],
            "core modules must import only stdlib / first-party; found: "
            + "; ".join(offenders))

    def test_subprocess_no_site_packages_runs_core(self) -> None:
        """Each core module imports + runs with site-packages stripped.

        Runs a child python with `-S` (no site initialization -> no
        site-packages on sys.path) and an extra purge of any site path that
        survives, then imports each core module and exercises a representative
        entry point. A third-party import anywhere on the executed path raises.
        """
        core = existing_core_files()
        if not core:
            self.skipTest("no core modules on disk yet")
        # Build a probe that imports each core file by path and exercises it.
        probe = _SUBPROCESS_PROBE
        result = subprocess.run(
            [sys.executable, "-S", "-c", probe],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=60)
        self.assertEqual(
            result.returncode, 0,
            "core failed to run with site-packages stripped:\n"
            f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}")


# The child process: strip every site-packages dir from sys.path, then import
# each existing core file by path and exercise a representative call. Kept as a
# module-level string so the parent test stays readable.
_SUBPROCESS_PROBE = r'''
import sys, os, importlib.util
from pathlib import Path

# Belt-and-suspenders: even under -S, purge any path that looks like a
# third-party install location so a stray import cannot resolve.
sys.path[:] = [p for p in sys.path
               if p and "site-packages" not in p and "dist-packages" not in p]

root = Path(os.getcwd())
core_rel = [
    "scripts/role_mail.py",
    ".claude/hooks/user_prompt_submit.py",
    ".claude/hooks/stop.py",
    "scripts/cell_depth.py",
]
# stop.py imports user_prompt_submit by bare name, so put the hooks dir on path.
hooks_dir = root / ".claude" / "hooks"
if hooks_dir.is_dir():
    sys.path.insert(0, str(hooks_dir))

loaded = {}
for rel in core_rel:
    path = root / rel
    if not path.is_file():
        continue
    name = path.stem
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    loaded[name] = mod

# Exercise a representative public entry point of each loaded module so a lazy
# import on that path would fire. All operate on a throwaway tmp comms root.
import tempfile
tmp = Path(tempfile.mkdtemp())

rm = loaded.get("role_mail")
if rm is not None:
    rm.post_message(tmp, "operator", ["charc"], "fyi", "probe", "body")
    rm.ack_message(tmp, "charc", next((tmp / "charc" / "inbox").glob("*.md")).name)

ups = loaded.get("user_prompt_submit")
if ups is not None:
    # Exercise the role-recovery store + the unread notice (the surviving hook
    # surface) so any lazy import on that path fires under -S.
    ups.write_session_role(tmp, "sid-probe", "charc")
    assert ups.read_session_role(tmp, "sid-probe") == "charc", \
        "role-recovery store failed under -S"
    ups.unread_notice("charc", tmp)

cdp = loaded.get("cell_depth")
if cdp is not None:
    # Exercise the discovery + CLI path against a throwaway, cell-less
    # project directory so any lazy import on that path fires under -S.
    rc = cdp.main(["--project", str(tmp)])
    assert rc == 1, f"cell_depth probe: expected rc 1 on an empty project, got {rc}"

print("OK")
'''


class DependencyPostureIsCoreScopedTest(unittest.TestCase):
    """B-9 operator refinement: the stdlib-only ban is CORE-scoped -- a property
    of the reusable template, NOT of the germinated implementation. The instance
    surface (the project's own code) imports third-party freely; it is never in
    CORE_RELPATHS, so the AST belt + subprocess probe never scan it. A CORE file
    importing third-party still FAILS (test_ast_belt_core_imports_are_stdlib_only,
    unchanged)."""

    def test_no_core_file_is_instance_surface(self) -> None:
        # The decisive CORE-scoping invariant: every CORE_RELPATHS entry is CORE,
        # never instance surface. (If this ever fails, a CORE-scoping bug let an
        # instance path into the stdlib-only set -- the plan-flagged stop case.)
        for rel in CORE_RELPATHS:
            self.assertFalse(
                gl.is_instance_surface(rel),
                f"{rel} is in CORE_RELPATHS but classifies as instance surface")

    def test_instance_surface_paths_are_not_dependency_scanned(self) -> None:
        # An instance-surface file (the germinated project's own code) is NOT in
        # CORE_RELPATHS, so it is never AST/subprocess-scanned -- it may import
        # third-party freely. The ban is CORE-only.
        for instance_rel in ("APPLICATION.md",
                             ".claude/agents/implementer-fast.md",
                             "docs/comms-context.md"):
            self.assertTrue(gl.is_instance_surface(instance_rel))
            self.assertNotIn(
                instance_rel, CORE_RELPATHS,
                f"{instance_rel} is instance surface; it must NOT be dependency-"
                "scanned (third-party is allowed in the germinated layer)")
        # And the CORE remains scanned (a representative core file IS in the set).
        self.assertIn("scripts/role_mail.py", CORE_RELPATHS)


class GitignoreAnchorTest(unittest.TestCase):
    """comms/.gitkeep is tracked while runtime mailbox files stay ignored."""

    def _check_ignore(self, relpath: str) -> int:
        return subprocess.run(
            ["git", "check-ignore", relpath],
            cwd=str(REPO_ROOT), capture_output=True, text=True).returncode

    def test_runtime_mailbox_file_is_ignored(self) -> None:
        # A runtime inbox message path is ignored (rc 0 == matched an ignore rule).
        self.assertEqual(
            self._check_ignore("comms/charc/inbox/x.md"), 0,
            "runtime mailbox files must be gitignored")

    def test_anchor_is_not_ignored(self) -> None:
        # The anchor is un-ignored (rc != 0 == no ignore rule matched).
        self.assertNotEqual(
            self._check_ignore("comms/.gitkeep"), 0,
            "comms/.gitkeep must NOT be ignored (the !comms/.gitkeep negation)")

    def test_anchor_is_actually_tracked(self) -> None:
        # The decisive proof: the anchor is committed/tracked. check-ignore alone
        # only shows ignore-rule behavior -- an unignored-but-never-added anchor
        # would pass the negation check yet fail here.
        rc = subprocess.run(
            ["git", "ls-files", "--error-unmatch", "comms/.gitkeep"],
            cwd=str(REPO_ROOT), capture_output=True, text=True).returncode
        self.assertEqual(
            rc, 0, "comms/.gitkeep must be tracked (git add + commit), not just "
            "unignored")


if __name__ == "__main__":
    unittest.main()
