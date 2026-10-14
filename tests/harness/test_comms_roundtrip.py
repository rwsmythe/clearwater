"""J.1 -- comms round-trip across the three roles (the "comms works" half).

Post -> read -> ack across charc / orchestrator / operator over the real
role_mail + a tmp comms root; the single-write-path + idempotency locks
exercised end-to-end. ARC-8: every role (orchestrator included) is a singular
inbox, so the orchestrator leg is addressed by bare name.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from _loader import load_role_mail

rm = load_role_mail()
FIXED = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


class CommsRoundTripTest(unittest.TestCase):
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())

    def _post_read_ack(self, sender: str, to_token: str, inbox: Path,
                       read_dir: Path, role: str,
                       session: str | None = None) -> None:
        rm.post_message(self.root, sender, [to_token], "fyi",
                        f"{sender}->{to_token}", "body", now=FIXED)
        unread = sorted(inbox.glob("*.md"))
        self.assertEqual(len(unread), 1)
        dest = rm.ack_message(self.root, role, unread[0].name, session)
        # ack moved inbox -> read; nothing deleted.
        self.assertEqual(sorted(inbox.glob("*.md")), [])
        self.assertTrue(dest.is_file())
        self.assertEqual(len(sorted(read_dir.glob("*.md"))), 1)

    def test_all_three_role_pairs_round_trip(self) -> None:
        # operator -> charc -> ack (shared inbox).
        self._post_read_ack(
            "operator", "charc",
            self.root / "charc" / "inbox", self.root / "charc" / "read", "charc")
        # charc -> orchestrator -> ack (the singular orchestrator inbox).
        self._post_read_ack(
            "charc", "orchestrator",
            self.root / "orchestrator" / "inbox",
            self.root / "orchestrator" / "read", "orchestrator")
        # orchestrator -> operator -> ack (the operator's own inbox).
        self._post_read_ack(
            "orchestrator", "operator",
            self.root / "operator" / "inbox", self.root / "operator" / "read",
            "operator")

    def test_subject_at_the_max_length_posts(self) -> None:
        subject = "s" * rm.SUBJECT_MAX_CHARS
        rm.post_message(self.root, "operator", ["charc"], "fyi", subject,
                        "body", now=FIXED)
        unread = sorted((self.root / "charc" / "inbox").glob("*.md"))
        self.assertEqual(len(unread), 1)

    def test_subject_over_the_max_length_rejected_nothing_written(self) -> None:
        subject = "s" * (rm.SUBJECT_MAX_CHARS + 1)
        with self.assertRaises(rm.MailError) as ctx:
            rm.post_message(self.root, "operator", ["charc"], "fyi", subject,
                            "body", now=FIXED)
        self.assertIn(str(rm.SUBJECT_MAX_CHARS), str(ctx.exception))
        self.assertEqual(
            sorted((self.root / "charc" / "inbox").glob("*.md")), [])

    def test_idempotent_ack_history_preserved(self) -> None:
        # The single-write-path idempotency: re-posting the same stamp+sender+slug
        # across an emptied inbox archives both (history-preserving -2 suffix).
        rm.post_message(self.root, "operator", ["charc"], "fyi", "dup", "1",
                        now=FIXED)
        rm.ack_message(self.root, "charc",
                       next((self.root / "charc" / "inbox").glob("*.md")).name)
        rm.post_message(self.root, "operator", ["charc"], "fyi", "dup", "2",
                        now=FIXED)
        rm.ack_message(self.root, "charc",
                       next((self.root / "charc" / "inbox").glob("*.md")).name)
        self.assertEqual(
            len(list((self.root / "charc" / "read").glob("*.md"))), 2)


if __name__ == "__main__":
    unittest.main()
