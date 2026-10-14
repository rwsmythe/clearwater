"""Role recovery (the ARC-8 CHARC-required carve-out).

The session_id -> role recovery store + the resume role-resolution fallback in
the UserPromptSubmit hook. ARC-8 deleted the per-generation registry but the
role-recovery store MUST survive: a RESUMED session (HARNESS_ROLE unset) recovers
its role from comms/roles/<session_id> so the unread notice still fires. This is
the binding regression the carve-out requires, exercised for EVERY comms role
(charc / operator / orchestrator -- all singular inboxes now). Both the
store helpers and the resume-role functions live in user_prompt_submit.py after
the fold. Stdlib unittest.
"""

from __future__ import annotations

import io
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path

from _loader import load_user_prompt_submit

ups = load_user_prompt_submit()

T0 = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


class RoleStoreHelperTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())

    def test_write_then_read_round_trips(self) -> None:
        p = ups.write_session_role(self.root, "sid-1", "charc")
        self.assertIsNotNone(p)
        self.assertEqual(ups.read_session_role(self.root, "sid-1"), "charc")
        # The store lives under comms/roles/, its own tree (the registry is gone).
        self.assertTrue((self.root / "roles" / "sid-1").is_file())
        self.assertFalse((self.root / "sessions").exists())

    def test_missing_record_reads_none(self) -> None:
        self.assertIsNone(ups.read_session_role(self.root, "absent"))

    def test_unsafe_session_id_never_builds_a_path(self) -> None:
        self.assertIsNone(ups.write_session_role(self.root, "../evil", "charc"))
        self.assertIsNone(ups.read_session_role(self.root, "../evil"))
        self.assertFalse((self.root.parent / "evil").exists())

    def test_empty_role_is_not_written(self) -> None:
        self.assertIsNone(ups.write_session_role(self.root, "sid-1", ""))
        self.assertIsNone(ups.read_session_role(self.root, "sid-1"))

    def test_garbage_record_strips_and_reads_back(self) -> None:
        (self.root / "roles").mkdir(parents=True)
        (self.root / "roles" / "sid-blank").write_text("  \n", encoding="utf-8")
        self.assertIsNone(ups.read_session_role(self.root, "sid-blank"))
        (self.root / "roles" / "sid-junk").write_text("nonsense\n",
                                                      encoding="utf-8")
        self.assertEqual(ups.read_session_role(self.root, "sid-junk"),
                         "nonsense")


class RecoveryWritePathTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())

    def test_launch_records_role_for_resume(self) -> None:
        # HARNESS_ROLE set (the original launch) + a session_id -> the role store
        # is written, so a later HARNESS_ROLE-absent resume can recover it.
        for role in ("charc", "operator", "orchestrator"):
            ups.handle_user_prompt_submit(
                {"session_id": f"sid-{role}", "transcript_path": "/t"},
                {"HARNESS_ROLE": role}, self.root, T0)
            self.assertEqual(
                ups.read_session_role(self.root, f"sid-{role}"), role)
        # Nothing registers for liveness (the registry is gone).
        self.assertFalse((self.root / "sessions").exists())

    def test_no_session_id_does_not_write_a_record(self) -> None:
        ups.handle_user_prompt_submit(
            {"transcript_path": "/t"}, {"HARNESS_ROLE": "charc"}, self.root, T0)
        self.assertFalse((self.root / "roles").exists()
                         and list((self.root / "roles").iterdir()))


class ResumeRecoveryTest(unittest.TestCase):
    """THE CHARC-required regression: a HARNESS_ROLE-absent resume recovers its
    role from the session-keyed store, so the unread notice fires. Each case
    FAILS pre-recovery (role='' -> silent) / PASSES with the store. Exercised for
    EVERY comms role (all singular inboxes post-ARC-8)."""

    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())

    def _seed_inbox(self, *parts: str) -> None:
        inbox = self.root.joinpath(*parts)
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "20240601T120000Z-x.md").write_text(
            "---\ntype: fyi\n---\nbody", encoding="utf-8")

    def test_every_role_recovers_on_resume_and_notice_fires(self) -> None:
        # For each role: seed a recovery record + its singular inbox, resume with
        # NO HARNESS_ROLE, and assert the role-specific notice fires purely from
        # the store (no registry, no per-generation subtree).
        for role in ("charc", "operator", "orchestrator"):
            sid = f"sid-{role}"
            ups.write_session_role(self.root, sid, role)
            self._seed_inbox(role, "inbox")
            buf = io.StringIO()
            with redirect_stdout(buf):
                ups.handle_user_prompt_submit(
                    {"session_id": sid, "transcript_path": "/t"},
                    {},  # NO HARNESS_ROLE -- the resume case
                    self.root, T0)
            self.assertIn(f"[comms] 1 unread for {role}", buf.getvalue(),
                          f"resumed {role} must recover its role + notice")
        # No liveness registry was ever created by any recovery.
        self.assertFalse((self.root / "sessions").exists())

    def test_recovery_uses_the_store_not_a_registry(self) -> None:
        # There is no registry anymore, so the ONLY source is the store: no
        # sessions/<id>.json exists, yet the notice fires from the role record.
        ups.write_session_role(self.root, "sid-c", "charc")
        self._seed_inbox("charc", "inbox")
        self.assertFalse((self.root / "sessions").exists())
        buf = io.StringIO()
        with redirect_stdout(buf):
            ups.handle_user_prompt_submit(
                {"session_id": "sid-c"}, {}, self.root, T0)
        self.assertIn("[comms] 1 unread for charc", buf.getvalue())

    def test_safe_degrade_no_store_no_env_role_is_silent_no_crash(self) -> None:
        # No HARNESS_ROLE + no recovery record -> role stays '' -> no notice, no
        # crash (the hook returns None; main() would exit 0).
        self._seed_inbox("charc", "inbox")
        buf = io.StringIO()
        with redirect_stdout(buf):
            result = ups.handle_user_prompt_submit(
                {"session_id": "sid-x"}, {}, self.root, T0)
        self.assertIsNone(result)
        self.assertEqual(buf.getvalue(), "")

    def test_no_concurrency_ambiguity_two_roles_one_clone(self) -> None:
        # Two roles in ONE clone (two session_ids). Seed each session's record,
        # then DRIVE THE HOOK for EACH session_id and assert each resume resolves
        # to ITS OWN role -- the session-keyed store disambiguates concurrent
        # roles where a single shared file could not.
        ups.write_session_role(self.root, "sid-c", "charc")
        ups.write_session_role(self.root, "sid-o", "orchestrator")
        self._seed_inbox("charc", "inbox")
        self._seed_inbox("orchestrator", "inbox")
        buf_c = io.StringIO()
        with redirect_stdout(buf_c):
            ups.handle_user_prompt_submit({"session_id": "sid-c"}, {},
                                          self.root, T0)
        self.assertIn("for charc", buf_c.getvalue())
        self.assertNotIn("for orchestrator", buf_c.getvalue())
        buf_o = io.StringIO()
        with redirect_stdout(buf_o):
            ups.handle_user_prompt_submit({"session_id": "sid-o"}, {},
                                          self.root, T0)
        self.assertIn("for orchestrator", buf_o.getvalue())
        self.assertNotIn("for charc", buf_o.getvalue())

    def test_env_role_wins_over_a_stale_store_record(self) -> None:
        # A relaunched session whose stored record is STALE (a different role
        # under the same id). The LAUNCH env var must win (role = env OR
        # recovery), proven through the hook: env=charc fires the CHARC notice,
        # NOT the orchestrator notice the stale record would imply.
        ups.write_session_role(self.root, "sid-c", "orchestrator")  # stale seed
        self._seed_inbox("charc", "inbox")
        self._seed_inbox("orchestrator", "inbox")  # would fire if wrong
        buf = io.StringIO()
        with redirect_stdout(buf):
            ups.handle_user_prompt_submit(
                {"session_id": "sid-c"}, {"HARNESS_ROLE": "charc"},
                self.root, T0)
        self.assertIn("for charc", buf.getvalue())
        self.assertNotIn("for orchestrator", buf.getvalue())
        # The live launch also REFRESHES the record to the current role.
        self.assertEqual(ups.read_session_role(self.root, "sid-c"), "charc")


if __name__ == "__main__":
    unittest.main()
