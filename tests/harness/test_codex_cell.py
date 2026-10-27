"""The Codex implementer-lane driver (scripts/codex_cell.py): pure parts.

Banner and return-file parsing on canned text, and the pinned command shapes.
No subprocess, no network. The facts pinned here were probed on 2026-10-27.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "scripts" / "codex_cell.py"


def _load():
    spec = importlib.util.spec_from_file_location("codex_cell", SCRIPT)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    sys.modules["codex_cell"] = mod
    spec.loader.exec_module(mod)
    return mod


BANNER = """OpenAI Codex v0.162.1 (research preview)
--------
workdir: C:\\x\\wt
model: gpt-6.1-sol
provider: openai
approval: never
sandbox: workspace-write [workdir, /tmp, $TMPDIR, C:\\x\\uv]
reasoning effort: high
reasoning summaries: auto
session id: 01a17b87-0f63-7081-a923-5c4cf10f1e02
--------
exec
powershell -Command 'git status --porcelain' in C:\\x\\wt
 succeeded in 258ms:
?? tools/note.md
ERROR codex_core::tools::router: error=exec_command failed
codex
done
tokens used
36,182
"""

RETURN = """Report text.

FILES CHANGED:
- src/pkg/mod.py
- `tests/test_mod.py`
COMMIT: feat(wp9.9): add the thing
VERDICT: TURN_DONE
"""


class BannerParse(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()

    def test_fields(self) -> None:
        b = self.m.parse_banner(BANNER)
        self.assertEqual(b["model"], "gpt-6.1-sol")
        self.assertEqual(b["effort"], "high")
        self.assertTrue(b["sandbox"].startswith("workspace-write"))
        self.assertEqual(b["session_id"], "01a17b87-0f63-7081-a923-5c4cf10f1e02")
        self.assertEqual(b["tokens_used"], 36182)
        self.assertEqual(b["succeeded_in"], 1)
        self.assertEqual(len(b["error_lines"]), 1)

    def test_missing_banner_is_none(self) -> None:
        b = self.m.parse_banner("nothing here\n")
        self.assertIsNone(b["model"])
        self.assertIsNone(b["tokens_used"])


class ReturnParse(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()

    def test_files_and_subject(self) -> None:
        r = self.m.parse_return(RETURN)
        self.assertEqual(r["files_changed"], ["src/pkg/mod.py", "tests/test_mod.py"])
        self.assertEqual(r["commit_subject"], "feat(wp9.9): add the thing")
        self.assertEqual(r["verdict_lines"], ["VERDICT: TURN_DONE"])

    def test_no_block(self) -> None:
        r = self.m.parse_return("no block\n")
        self.assertEqual(r["files_changed"], [])
        self.assertIsNone(r["commit_subject"])


class Commands(unittest.TestCase):
    def setUp(self) -> None:
        self.m = _load()

    def test_first_turn_carries_every_override(self) -> None:
        cmd = self.m.build_turn_command(
            worktree="C:/x/wt", session_id=None, return_file="r.md", writable_roots=("C:\\x\\uv",)
        )
        joined = " ".join(cmd)
        self.assertIn('model="gpt-6.1-sol"', joined)
        self.assertIn("model_reasoning_effort=high", joined)
        self.assertIn('windows.sandbox="unelevated"', joined)
        self.assertIn('sandbox_workspace_write.writable_roots=["C:/x/uv"]', joined)
        self.assertIn("workspace-write", cmd)
        self.assertEqual(cmd[:2], ["codex", "exec"])
        self.assertEqual(cmd[-1], "-")

    def test_resume_turn_has_no_exec_only_flags(self) -> None:
        cmd = self.m.build_turn_command(worktree="C:/x/wt", session_id="abc", return_file="r.md")
        self.assertEqual(cmd[:4], ["codex", "exec", "resume", "abc"])
        self.assertNotIn("-s", cmd)
        self.assertNotIn("-m", cmd)
        self.assertNotIn("--add-dir", cmd)
        self.assertIn('windows.sandbox="unelevated"', " ".join(cmd))

    def test_review_is_read_only(self) -> None:
        cmd = self.m.build_review_command()
        joined = " ".join(cmd)
        self.assertNotIn("--bare", cmd)
        self.assertIn("--output-format", cmd)
        self.assertIn("Edit,Write", joined)
        self.assertIn("Bash(git diff:*)", joined)
        self.assertIn("--effort", cmd)


if __name__ == "__main__":
    unittest.main()
