"""E.2 + E.3 -- settings.json hook registration (portable path) + hook
portability (file-relative comms root, HARNESS_ROLE, stdin JSON, always exit 0).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
# ARC-8: two wired hooks remain (the per-generation SessionStart/SessionEnd
# registry lifecycle was deleted with the singular-inbox simplification).
HOOKS = ("user_prompt_submit.py", "stop.py")


class SettingsJsonTest(unittest.TestCase):
    """E.2 -- the two hooks registered with a portable (non-absolute) path."""

    def setUp(self) -> None:
        self.data = json.loads(
            (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8"))

    def test_two_hook_events_registered(self) -> None:
        events = set(self.data["hooks"])
        self.assertEqual(
            events,
            {"UserPromptSubmit", "Stop"})

    def test_each_event_points_at_its_hook_script(self) -> None:
        mapping = {
            "UserPromptSubmit": "user_prompt_submit.py",
            "Stop": "stop.py",
        }
        for event, script in mapping.items():
            cmd = self.data["hooks"][event][0]["hooks"][0]["command"]
            self.assertIn(script, cmd, f"{event} must point at {script}")

    def test_hook_paths_are_portable_not_machine_absolute(self) -> None:
        # No machine-specific absolute path (the legacy harness hard-coded one);
        # paths resolve against $CLAUDE_PROJECT_DIR (a portable placeholder).
        raw = (REPO_ROOT / ".claude" / "settings.json").read_text(encoding="utf-8")
        self.assertIn("$CLAUDE_PROJECT_DIR", raw,
                      "hook paths must use the portable project-dir placeholder")
        self.assertNotIn("C:/Users", raw)
        self.assertNotIn("C:\\\\Users", raw)

    def test_interpreter_portability_documented(self) -> None:
        # R2-MAJOR-2: the commands use `python` (the Windows-substrate launcher);
        # the comment must document the python->python3 per-machine substitution
        # so a python3-only clone is a documented one-line edit, not a silent
        # hook-execution failure.
        comment = self.data.get("_comment", "")
        self.assertIn("python3", comment,
                      "the settings comment must document the python/python3 "
                      "interpreter substitution for non-Windows clones")


class HookPortabilityTest(unittest.TestCase):
    """E.3 -- each hook works from an arbitrary cwd + exits 0 on bad input."""

    def _run_hook(self, script: str, payload: str, env_extra: dict,
                  cwd: Path) -> subprocess.CompletedProcess:
        env = dict(os.environ)
        env.update(env_extra)
        return subprocess.run(
            [sys.executable, str(REPO_ROOT / ".claude" / "hooks" / script)],
            input=payload, capture_output=True, text=True, env=env,
            cwd=str(cwd), timeout=30)

    def test_each_hook_resolves_comms_root_from_file_not_cwd(self) -> None:
        # Run from a DIFFERENT cwd; the role-recovery record the UserPromptSubmit
        # hook writes must land in the REPO's comms/roles/ (file-relative), not
        # under the arbitrary cwd. Use a throwaway session id + clean it up.
        sid = "wiring-test-sid"
        other_cwd = Path(tempfile.mkdtemp())
        try:
            proc = self._run_hook(
                "user_prompt_submit.py",
                json.dumps({"session_id": sid, "transcript_path": "/t"}),
                {"HARNESS_ROLE": "charc"}, other_cwd)
            self.assertEqual(proc.returncode, 0)
            # The record is under the REPO comms/, not the arbitrary cwd.
            repo_rec = REPO_ROOT / "comms" / "roles" / sid
            cwd_rec = other_cwd / "comms" / "roles" / sid
            self.assertTrue(repo_rec.is_file(),
                            "hook must resolve comms/ from __file__, not cwd")
            self.assertFalse(cwd_rec.exists())
        finally:
            rec = REPO_ROOT / "comms" / "roles" / sid
            if rec.is_file():
                rec.unlink()

    def test_each_hook_reads_harness_role_and_exits_zero_on_malformed(self) -> None:
        for script in HOOKS:
            proc = self._run_hook(
                script, "not json at all", {"HARNESS_ROLE": "orchestrator"},
                Path(tempfile.mkdtemp()))
            self.assertEqual(
                proc.returncode, 0,
                f"{script} must exit 0 on a malformed stdin payload")

    def test_each_hook_exits_zero_with_no_role(self) -> None:
        for script in HOOKS:
            proc = self._run_hook(script, "{}", {}, Path(tempfile.mkdtemp()))
            self.assertEqual(proc.returncode, 0,
                             f"{script} must exit 0 with no HARNESS_ROLE")

    def test_sibling_import_failure_still_exits_zero(self) -> None:
        # The sibling `from user_prompt_submit import ...` in stop.py runs at
        # module load, BEFORE main()'s try/except. If it fails (a broken/missing
        # user_prompt_submit.py), the un-guarded hook would crash with a nonzero
        # exit and TRAP the agent. Copy stop.py into an ISOLATED dir with NO
        # user_prompt_submit.py beside it (and a guaranteed-unimportable
        # PYTHONPATH) so the bare import fails -- the guarded hook must STILL
        # exit 0. (ARC-8: session_end.py is gone; user_prompt_submit.py no longer
        # has a bare sibling import, so stop.py is the only importing hook left.)
        for script in ("stop.py",):
            isolated = Path(tempfile.mkdtemp())
            (isolated / script).write_text(
                (REPO_ROOT / ".claude" / "hooks" / script).read_text(
                    encoding="utf-8"), encoding="utf-8")
            # No user_prompt_submit.py in `isolated`; force PYTHONPATH to it so
            # the bare `import user_prompt_submit` cannot resolve.
            env = dict(os.environ)
            env["HARNESS_ROLE"] = "charc"
            env["PYTHONPATH"] = str(isolated)
            proc = subprocess.run(
                [sys.executable, str(isolated / script)],
                input=json.dumps({"session_id": "x", "transcript_path": "/t"}),
                capture_output=True, text=True, env=env, cwd=str(isolated),
                timeout=30)
            self.assertEqual(
                proc.returncode, 0,
                f"{script} must exit 0 even when the sibling import fails "
                f"(stderr: {proc.stderr})")


if __name__ == "__main__":
    unittest.main()
