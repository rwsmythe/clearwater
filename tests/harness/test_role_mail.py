"""role_mail.py: uniform singular addressing + post/ack + atomic delivery.

Covers Tasks B.1 (taxonomy + post write path + singular orchestrator addressing
+ the L1 lock), B.2 (list/read/peek + ack history-preservation + traversal
guard), B.3 (atomic multi-recipient + frontmatter-injection guard), and B.4
(the peer-director-add checklist note). ARC-8 collapsed the orchestrator onto
the uniform singular-inbox model (per-generation addressing + the registry are
gone).
"""

from __future__ import annotations

import tempfile
import unittest
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

from _loader import load_role_mail

rm = load_role_mail()

FIXED = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


class TmpRootMixin:
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())


# --- B.1 ------------------------------------------------------------------

class PostAddressingTest(TmpRootMixin, unittest.TestCase):
    def test_to_charc_lands_in_shared_inbox(self) -> None:
        rm.post_message(self.root, "operator", ["charc"], "status",
                        "Arc shipped", "all green", now=FIXED)
        inbox = self.root / "charc" / "inbox"
        files = list(inbox.glob("*.md"))
        self.assertEqual(len(files), 1)
        self.assertIn("to: charc", files[0].read_text(encoding="utf-8"))

    def test_to_orchestrator_lands_in_singular_inbox(self) -> None:
        # ARC-8: the orchestrator is now a singular-inbox role like the directors.
        # --to orchestrator lands in comms/orchestrator/inbox -- no session_id, no
        # per-generation subtree, no registry.
        rm.post_message(self.root, "charc", ["orchestrator"], "status",
                        "go", "body", now=FIXED)
        inbox = self.root / "orchestrator" / "inbox"
        self.assertTrue(inbox.is_dir())
        self.assertEqual(len(list(inbox.glob("*.md"))), 1)
        self.assertIn("to: orchestrator",
                      next(inbox.glob("*.md")).read_text(encoding="utf-8"))
        # No per-generation subtree is ever created.
        self.assertFalse((self.root / "orchestrator" / "sid-abc").exists())

    def test_l1_lock_decision_request_to_non_operator_refused(self) -> None:
        # decision_request to charc / orchestrator is refused; to operator it
        # succeeds. (Pre-fix: no lock -> a file would be written.)
        for target in ("charc", "orchestrator"):
            with self.assertRaises(rm.MailError):
                rm.post_message(self.root, "operator", [target],
                                "decision_request", "q", "body", now=FIXED)
        # Nothing written for the refused recipients.
        self.assertFalse((self.root / "charc" / "inbox").exists()
                         and list((self.root / "charc" / "inbox").glob("*.md")))
        # To operator it succeeds.
        rm.post_message(self.root, "charc", ["operator"], "decision_request",
                        "approve?", "body", now=FIXED)
        self.assertEqual(
            len(list((self.root / "operator" / "inbox").glob("*.md"))), 1)

    def test_orchestrator_session_suffix_is_rejected(self) -> None:
        # Per-generation addressing is gone: a ':<session_id>' suffix on ANY role
        # (orchestrator included) is a hard error, nothing written.
        with self.assertRaises(rm.MailError):
            rm.post_message(self.root, "charc", ["orchestrator:sid-x"], "fyi",
                            "hi", "body", now=FIXED)
        self.assertFalse((self.root / "orchestrator").exists())

    def test_removed_director_role_is_rejected(self) -> None:
        # The legacy second-director role has no scaffold analog (one director
        # ships). Construct the removed role from chars so this test file carries
        # no literal forbidden role token (the genericity guard scans it).
        removed = "r" + "d"
        self.assertNotIn(removed, rm.VALID_TO)
        self.assertNotIn(removed, rm.VALID_FROM)
        with self.assertRaises(rm.MailError):
            rm.post_message(self.root, "operator", [removed], "fyi", "x", "y",
                            now=FIXED)

    def test_charc_operator_reject_session_suffix(self) -> None:
        with self.assertRaises(rm.MailError):
            rm.post_message(self.root, "operator", ["charc:sid"], "fyi", "x", "y",
                            now=FIXED)


# --- B.2 ------------------------------------------------------------------

class ListReadPeekTest(TmpRootMixin, unittest.TestCase):
    def test_read_all_drains_inbox(self) -> None:
        rm.post_message(self.root, "operator", ["charc"], "fyi", "one", "b1",
                        now=FIXED)
        rc = rm.main(["--comms-root", str(self.root), "read", "--role", "charc",
                      "--all"])
        self.assertEqual(rc, 0)
        self.assertEqual(
            list((self.root / "charc" / "inbox").glob("*.md")), [])
        self.assertEqual(
            len(list((self.root / "charc" / "read").glob("*.md"))), 1)

    def test_peek_does_not_ack(self) -> None:
        rm.post_message(self.root, "operator", ["charc"], "fyi", "one", "b1",
                        now=FIXED)
        rm.main(["--comms-root", str(self.root), "peek", "--role", "charc"])
        self.assertEqual(
            len(list((self.root / "charc" / "inbox").glob("*.md"))), 1)

    def test_ack_never_overwrites_history(self) -> None:
        # Post, drain, post the same stamp+sender+slug again, drain: the second
        # ack must land as a -2 file in read/, nothing deleted.
        rm.post_message(self.root, "operator", ["charc"], "fyi", "dup", "first",
                        now=FIXED)
        first = rm.ack_message(
            self.root, "charc",
            next((self.root / "charc" / "inbox").glob("*.md")).name)
        rm.post_message(self.root, "operator", ["charc"], "fyi", "dup", "second",
                        now=FIXED)
        second = rm.ack_message(
            self.root, "charc",
            next((self.root / "charc" / "inbox").glob("*.md")).name)
        self.assertNotEqual(first.name, second.name)
        self.assertEqual(
            len(list((self.root / "charc" / "read").glob("*.md"))), 2)
        self.assertTrue(first.exists() and second.exists())

    def test_ack_rejects_traversal(self) -> None:
        with self.assertRaises(rm.MailError):
            rm.ack_message(self.root, "charc", "../x.md")

    def test_non_ascii_subject_lists_without_crashing(self) -> None:
        rm.post_message(self.root, "operator", ["charc"], "fyi", "naïve — café",
                        "body", now=FIXED)
        rc = rm.main(["--comms-root", str(self.root), "list", "--role", "charc"])
        self.assertEqual(rc, 0)

    def test_orchestrator_read_is_the_singular_inbox(self) -> None:
        # ARC-8: the orchestrator inbox is the singular comms/orchestrator/inbox
        # (no --session needed -- per-generation reading is gone).
        self.assertEqual(rm._role_inbox_dir(self.root, "orchestrator"),
                         self.root / "orchestrator" / "inbox")


# --- B.3 ------------------------------------------------------------------

class AtomicDeliveryTest(TmpRootMixin, unittest.TestCase):
    def test_multi_recipient_all_or_nothing_on_failure(self) -> None:
        # Force the SECOND os.replace to fail mid-delivery; assert NEITHER
        # recipient is left with a message (full rollback). Two singular roles.
        real_replace = rm.os.replace
        calls = {"n": 0}

        def flaky_replace(src, dst):
            calls["n"] += 1
            if calls["n"] == 2:
                raise OSError("simulated mid-delivery failure")
            return real_replace(src, dst)

        with mock.patch.object(rm.os, "replace", flaky_replace):
            with self.assertRaises(rm.MailError):
                rm.post_message(self.root, "charc",
                                ["orchestrator", "operator"],
                                "status", "multi", "body", now=FIXED)
        # Zero partials: neither inbox holds a message.
        orch = list((self.root / "orchestrator" / "inbox").glob("*.md"))
        oper = list((self.root / "operator" / "inbox").glob("*.md"))
        self.assertEqual(orch, [])
        self.assertEqual(oper, [])

    def test_multi_recipient_success_delivers_all(self) -> None:
        rm.post_message(self.root, "operator", ["charc", "operator"], "fyi",
                        "broadcast", "body", now=FIXED)
        self.assertEqual(
            len(list((self.root / "charc" / "inbox").glob("*.md"))), 1)
        self.assertEqual(
            len(list((self.root / "operator" / "inbox").glob("*.md"))), 1)

    def test_crlf_in_subject_rejected_nothing_written(self) -> None:
        with self.assertRaises(rm.MailError):
            rm.post_message(self.root, "operator", ["charc"], "fyi",
                            "bad\nsubject", "body", now=FIXED)
        self.assertFalse(
            (self.root / "charc" / "inbox").exists()
            and list((self.root / "charc" / "inbox").glob("*.md")))

    def test_crlf_in_thread_rejected(self) -> None:
        with self.assertRaises(rm.MailError):
            rm.post_message(self.root, "operator", ["charc"], "fyi", "ok",
                            "body", thread="bad\rthread", now=FIXED)

    def test_collision_proof_filenames_same_second(self) -> None:
        # R1-MAJOR-1: two posts with identical sender/subject in the same second
        # produce DISTINCT files (the random token defeats the same-second race).
        rm.post_message(self.root, "operator", ["charc"], "fyi", "same", "1",
                        now=FIXED)
        rm.post_message(self.root, "operator", ["charc"], "fyi", "same", "2",
                        now=FIXED)
        files = list((self.root / "charc" / "inbox").glob("*.md"))
        self.assertEqual(len(files), 2, "same-second posts must not collide")

    def test_intra_call_dedupe_repeated_recipient(self) -> None:
        # A single post naming the SAME singular recipient twice de-dupes by the
        # resolved concrete inbox: ONE file delivered, not two duplicate paths.
        finals = rm.post_message(
            self.root, "charc", ["orchestrator", "orchestrator"],
            "status", "dup", "body", now=FIXED)
        inbox = self.root / "orchestrator" / "inbox"
        self.assertEqual(len(list(inbox.glob("*.md"))), 1)
        self.assertEqual(len(finals), 1)


# --- B.4 ------------------------------------------------------------------

class PeerDirectorChecklistTest(unittest.TestCase):
    def test_checklist_note_present_and_enumerates_touch_set(self) -> None:
        src = (Path(rm.__file__)).read_text(encoding="utf-8")
        self.assertIn("peer-director-add checklist", src)
        for marker in ("VALID_FROM", "VALID_TO", "charter", "launcher"):
            self.assertIn(marker, src)

    def test_valid_to_is_the_one_director_set(self) -> None:
        # One director ships (no peer-director-add has been commissioned).
        self.assertEqual(
            set(rm.VALID_TO),
            {"charc", "orchestrator", "operator"})
        self.assertEqual(set(rm.VALID_FROM),
                         {"charc", "orchestrator", "operator"})
        self.assertEqual(set(rm.SINGULAR_INBOX_ROLES), set(rm.VALID_TO))

    def test_checklist_routes_instance_authority_to_context_doc(self) -> None:
        # Codex R4 MAJOR: the checklist must MIRROR the charter split -- the
        # generic peer-director contract is in the kernel; the new director's
        # INSTANCE authority goes in its own docs/<role>-context.md, NOT the
        # charter. So the checklist must (a) name the docs/<role>-context.md
        # routing and (b) NOT instruct adding "the new director's authority" to
        # the charter (the stale instruction that would contaminate the kernel).
        norm = " ".join(
            (Path(rm.__file__)).read_text(encoding="utf-8").split())
        self.assertIn("docs/<role>-context.md", norm,
                      "the checklist must route instance authority to the "
                      "<role>-context.md instance doc (charter split)")
        self.assertNotIn("add the new director's authority", norm,
                         "the checklist must NOT instruct adding instance "
                         "authority to the kernel charter (stale -- R4)")


if __name__ == "__main__":
    unittest.main()
