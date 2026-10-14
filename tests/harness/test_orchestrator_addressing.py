"""Orchestrator addressing -- the SINGULAR inbox (ARC-8).

The orchestrator is now a singular-inbox role like the directors: `--to
orchestrator` delivers to the one `comms/orchestrator/inbox`, drained by
whichever generation is live. Per-generation addressing, the session registry,
and newest-live resolution were deleted by ARC-8; this file replaces the old
D.5 per-generation suite with the singular-model assertions.
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path

from _loader import load_role_mail

rm = load_role_mail()
FIXED = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


class TmpRootMixin:
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())


class SingularAddressingTest(TmpRootMixin, unittest.TestCase):
    def test_orchestrator_lands_in_the_single_inbox(self) -> None:
        rm.post_message(self.root, "charc", ["orchestrator"], "status",
                        "for orch", "body", now=FIXED)
        inbox = self.root / "orchestrator" / "inbox"
        self.assertEqual(len(list(inbox.glob("*.md"))), 1)
        # No per-generation subtree exists.
        subdirs = [p for p in (self.root / "orchestrator").iterdir()
                   if p.is_dir() and p.name not in ("inbox", "read")]
        self.assertEqual(subdirs, [], "no per-generation subtree may be created")

    def test_orchestrator_accepts_all_info_types(self) -> None:
        for mtype in ("fyi", "status", "query", "return_report"):
            rm.post_message(self.root, "charc", ["orchestrator"], mtype,
                            f"m {mtype}", "body", now=FIXED)
        inbox = self.root / "orchestrator" / "inbox"
        self.assertEqual(len(list(inbox.glob("*.md"))), 4)

    def test_session_suffix_is_rejected(self) -> None:
        # Per-generation addressing is gone: a ':<session_id>' suffix is refused.
        with self.assertRaises(rm.MailError):
            rm.post_message(self.root, "charc", ["orchestrator:sid-a"], "fyi",
                            "x", "body", now=FIXED)
        self.assertFalse((self.root / "orchestrator" / "sid-a").exists())

    def test_read_drains_the_single_orchestrator_inbox(self) -> None:
        rm.post_message(self.root, "charc", ["orchestrator"], "fyi", "one",
                        "body", now=FIXED)
        rm.main(["--comms-root", str(self.root), "read", "--role",
                 "orchestrator", "--all"])
        self.assertEqual(
            list((self.root / "orchestrator" / "inbox").glob("*.md")), [])
        self.assertEqual(
            len(list((self.root / "orchestrator" / "read").glob("*.md"))), 1)


if __name__ == "__main__":
    unittest.main()
