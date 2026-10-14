"""role_mail hardening: verified posting + the ARC-8 salvage list (D1/D2/D4).

ARC-8 deleted the per-generation orchestrator machinery, and with it the whole
fail-closed-generation-addressing surface (the old UnknownGeneration /
_known_generation_ids tests). What survives + is exercised here, each proved in
BOTH directions (a check that passes both ways is worthless):

  (a) ``post-verified`` posts AND confirms the landing in one call -- a mailbox-
      root mismatch caught BEFORE the write, a landing that does not match what
      was asked for, and the ack-in-the-gap acceptance (D2).
  (b) D1 -- the per-message discriminator: post-verified confirms THE specific
      message it wrote (posted stamp + msg-id nonce), so a header-twin sharing
      from/to/type/subject cannot answer for it.
  (c) D4 -- ``_within`` resolves symlinks/junctions before containment, and
      post_message REFUSES (pre-staging, nothing written) a delivery target that
      escapes the mailbox root.
"""

from __future__ import annotations

import io
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

from _loader import load_role_mail

rm = load_role_mail()

from datetime import UTC, datetime  # noqa: E402

FIXED = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _tree(root: Path) -> set[str]:
    """Every path under root, relative + normalized (the wrote-nothing witness)."""
    if not root.exists():
        return set()
    return {p.relative_to(root).as_posix() for p in root.rglob("*")}


def _make_dir_link(link: Path, target: Path) -> bool:
    """Create link -> target as a dir junction/symlink; True on success.

    A Windows directory junction (mklink /J) needs no privilege, unlike a
    symlink; POSIX uses os.symlink. Returns False if neither can be made.
    """
    try:
        if sys.platform == "win32":
            proc = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(target)],
                capture_output=True, text=True)
            return proc.returncode == 0 and link.exists()
        os.symlink(str(target), str(link), target_is_directory=True)
        return True
    except (OSError, NotImplementedError):
        return False


class TmpRootMixin:
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())


# --- (b) post-verified ------------------------------------------------------

class PostVerifiedTest(TmpRootMixin, unittest.TestCase):
    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = rm.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def test_success_reports_the_absolute_landing_path(self) -> None:
        rc, out, _ = self._run([
            "--comms-root", str(self.root), "post-verified",
            "--from", "charc", "--to", "operator", "--type", "status",
            "--subject", "verified-hi", "--body", "b"])
        self.assertEqual(rc, 0)
        landed = list((self.root / "operator" / "inbox").glob("*.md"))
        self.assertEqual(len(landed), 1)
        self.assertIn("verified", out)
        self.assertIn(str(landed[0].resolve()), out)

    def test_success_on_the_singular_orchestrator(self) -> None:
        # ARC-8: the orchestrator is a plain singular recipient now.
        rc, out, _ = self._run([
            "--comms-root", str(self.root), "post-verified",
            "--from", "charc", "--to", "orchestrator",
            "--type", "status", "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 0)
        self.assertEqual(
            len(list((self.root / "orchestrator" / "inbox").glob("*.md"))), 1)

    def test_multi_recipient_all_verified(self) -> None:
        rc, out, _ = self._run([
            "--comms-root", str(self.root), "post-verified",
            "--from", "charc", "--to", "operator,orchestrator", "--type", "status",
            "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 0)
        self.assertEqual(out.count("verified ->"), 2)

    def test_acked_in_the_gap_still_verifies_landed(self) -> None:
        # D2: a receiver that acks the message (inbox -> read) between the post
        # and the verify has NOT lost it -- post-verified accepts the read/
        # sibling as a legitimate landing (not a "did not land" false negative).
        # Drive it by acking inside a post_message wrapper so the ack lands in
        # the verify gap.
        real_post = rm.post_message

        def post_then_ack(root, sender, recipients, mtype, subject, body,
                          thread=None, now=None, posted_ids=None):
            finals = real_post(root, sender, recipients, mtype, subject, body,
                               thread, now, posted_ids)
            for f in finals:  # receiver acks in the gap
                rm.ack_message(root, "operator", f.name)
            return finals

        with mock.patch.object(rm, "post_message", post_then_ack):
            rc, out, err = self._run([
                "--comms-root", str(self.root), "post-verified",
                "--from", "charc", "--to", "operator", "--type", "status",
                "--subject", "acked-gap", "--body", "b"])
        self.assertEqual(rc, 0, err)
        # The message is in read/, not inbox/, yet verification PASSED.
        self.assertEqual(
            len(list((self.root / "operator" / "read").glob("*.md"))), 1)

    # --- the failure paths (constructed, not asserted-happy-only) ---

    def test_expected_root_mismatch_fails_before_writing_anything(self) -> None:
        other = Path(tempfile.mkdtemp())
        rc, out, err = self._run([
            "--comms-root", str(self.root), "post-verified",
            "--expect-root", str(other),
            "--from", "charc", "--to", "operator", "--type", "status",
            "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 1)
        self.assertIn(str(self.root.resolve()), err)
        self.assertIn(str(other.resolve()), err)
        self.assertEqual(_tree(self.root), set(), "nothing may be written")
        self.assertEqual(_tree(other), set())

    def test_expected_root_match_is_accepted(self) -> None:
        rc, _, _ = self._run([
            "--comms-root", str(self.root), "post-verified",
            "--expect-root", str(self.root),
            "--from", "charc", "--to", "operator", "--type", "status",
            "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 0)

    def test_landing_that_vanished_is_reported_as_did_not_land(self) -> None:
        ghost = self.root / "operator" / "inbox" / "never-written.md"
        with mock.patch.object(rm, "post_message", lambda *a, **k: [ghost]):
            rc, out, err = self._run([
                "--comms-root", str(self.root), "post-verified",
                "--from", "charc", "--to", "operator", "--type", "status",
                "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 1)
        self.assertIn("did not land", err)
        self.assertIn("never-written.md", err)

    def test_landing_in_the_wrong_inbox_is_reported_with_the_actual_path(self) -> None:
        def wrong_place(root, sender, recipients, mtype, subject, body,
                        thread=None, now=None, posted_ids=None):
            stray = Path(root) / "charc" / "inbox" / "misrouted.md"
            stray.parent.mkdir(parents=True, exist_ok=True)
            stray.write_text(
                "---\nfrom: charc\nto: operator\ntype: status\n"
                "subject: s\nposted: x\n---\n\nb\n", encoding="utf-8")
            return [stray]

        with mock.patch.object(rm, "post_message", wrong_place):
            rc, out, err = self._run([
                "--comms-root", str(self.root), "post-verified",
                "--from", "charc", "--to", "operator", "--type", "status",
                "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 1)
        self.assertIn("misrouted.md", err)
        self.assertIn("charc", err)

    def test_a_dropped_recipient_is_caught(self) -> None:
        # Two addressed, one delivered: verification must not call that success.
        real_post = rm.post_message

        def only_one(root, sender, recipients, mtype, subject, body,
                     thread=None, now=None, posted_ids=None):
            return real_post(root, sender, ["operator"], mtype, subject, body,
                             thread, now)

        with mock.patch.object(rm, "post_message", only_one):
            rc, out, err = self._run([
                "--comms-root", str(self.root), "post-verified",
                "--from", "charc", "--to", "operator,orchestrator",
                "--type", "status", "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 1)
        self.assertIn("orchestrator", err)

    def test_the_governance_lock_still_applies(self) -> None:
        rc, _, err = self._run([
            "--comms-root", str(self.root), "post-verified",
            "--from", "charc", "--to", "charc", "--type", "decision_request",
            "--subject", "s", "--body", "b"])
        self.assertEqual(rc, 1)
        self.assertEqual(_tree(self.root), set())


# --- (b) D1 the per-message discriminator ----------------------------------

class D1DiscriminatorTest(TmpRootMixin, unittest.TestCase):
    """D1: post-verified confirms THE specific message (posted + msg-id), not a
    header-twin. Proved in both directions -- the twin is REJECTED while the
    genuine (same nonce) landing is ACCEPTED."""

    def _compose_file(self, dst: Path, msg_id: str, posted: str = "2024-06-01T12:00:00Z") -> None:
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(
            f"---\nfrom: operator\nto: charc\ntype: fyi\nsubject: s\n"
            f"posted: {posted}\nmsg-id: {msg_id}\n---\n\nbody\n",
            encoding="utf-8")

    def test_compose_embeds_a_msg_id(self) -> None:
        finals = rm.post_message(self.root, "operator", ["charc"], "fyi", "s",
                                 "body", now=FIXED)
        fm = rm._read_frontmatter(finals[0])
        self.assertTrue(fm.get("msg-id"), "a posted message must carry a msg-id")

    def test_verify_rejects_a_header_twin_at_the_read_sibling(self) -> None:
        # The final never landed in inbox; a header-twin (same from/to/type/
        # subject) with a DIFFERENT msg-id sits at the read/ sibling. The D2
        # accept-if-either-path would find it -- D1 rejects it (wrong nonce).
        inbox = self.root / "charc" / "inbox"
        read = self.root / "charc" / "read"
        final = inbox / "20240601T120000Z-operator-s-deadbeef.md"
        twin = read / final.name  # same filename, but a different message's nonce
        self._compose_file(twin, msg_id="TWINNONCE")
        # With the write-side discriminators for OUR message supplied, the twin
        # is caught.
        problem = rm._verify_landing(
            self.root, final, "operator", "fyi", "s",
            want_posted="2024-06-01T12:00:00Z", want_msg_id="OURNONCE")
        self.assertIsNotNone(problem)
        self.assertIn("msg-id", problem)
        # The OTHER direction: the SAME nonce (a genuine ack-in-gap) verifies.
        self._compose_file(twin, msg_id="OURNONCE")
        self.assertIsNone(rm._verify_landing(
            self.root, final, "operator", "fyi", "s",
            want_posted="2024-06-01T12:00:00Z", want_msg_id="OURNONCE"))

    def test_landing_matches_request_ties_to_this_posts_nonces(self) -> None:
        # A landed file bearing the right label but a foreign nonce does NOT
        # answer the request when the posted-id set is known.
        landed_twin = [("charc", "TWINNONCE")]
        self.assertFalse(
            rm._landing_matches_request("charc", landed_twin, {"OURNONCE"}))
        # The genuine nonce answers it.
        self.assertTrue(
            rm._landing_matches_request("charc", [("charc", "OURNONCE")],
                                        {"OURNONCE"}))
        # Degrade: with no known posted-id set (a mocked post), fall back to
        # label-only -- never a regression from the pre-D1 behavior.
        self.assertTrue(
            rm._landing_matches_request("charc", landed_twin, set()))


# --- (c) D4 the containment guard ------------------------------------------

class WithinContainmentTest(unittest.TestCase):
    """_within resolves symlinks AND junctions before the containment check."""

    def test_in_tree_child_is_contained(self) -> None:
        root = Path(tempfile.mkdtemp())
        child = root / "charc" / "inbox"
        child.mkdir(parents=True)
        self.assertTrue(rm._within(root, child))

    def test_a_reparse_escape_is_not_contained(self) -> None:
        root = Path(tempfile.mkdtemp())
        outside = Path(tempfile.mkdtemp())
        link = root / "escape"
        if not _make_dir_link(link, outside):
            self.skipTest("cannot create a junction/symlink on this platform")
        # The LEXICAL path reads as inside root, but it resolves OUTSIDE.
        escaped = link / "inbox"
        (outside / "inbox").mkdir()
        self.assertFalse(rm._within(root, escaped),
                         "_within must resolve the reparse point and reject it")


class ContainmentGuardWiredTest(TmpRootMixin, unittest.TestCase):
    """post_message refuses a delivery target that escapes the root, BEFORE any
    temp is staged (D4-(b)). Distinguished: refused with the guard, delivered
    with the guard stubbed to always-contained."""

    def test_escaping_target_is_refused_and_writes_nothing(self) -> None:
        before = _tree(self.root)
        with mock.patch.object(rm, "_within", lambda parent, child: False):
            with self.assertRaises(rm.MailError) as ctx:
                rm.post_message(self.root, "operator", ["charc"], "fyi", "s",
                                "body", now=FIXED)
        self.assertIn("OUTSIDE the mailbox root", str(ctx.exception))
        self.assertEqual(_tree(self.root), before,
                         "a refused delivery must write NOTHING (pre-staging)")

    def test_contained_target_delivers(self) -> None:
        # The other direction -- the guard is not simply always-fail.
        finals = rm.post_message(self.root, "operator", ["charc"], "fyi", "s",
                                 "body", now=FIXED)
        self.assertEqual(len(finals), 1)
        self.assertTrue(finals[0].is_file())


class AckContainmentTest(TmpRootMixin, unittest.TestCase):
    """ack_message routes its read-dir creation + move through the same
    _within-guarded choke point -- so a junctioned role dir cannot make the ack
    rename land OUTSIDE the mailbox root (FIX-1 r2: the ack path was the next
    unguarded write path after the post path was scoped)."""

    def test_ack_through_a_junctioned_role_is_blocked(self) -> None:
        outside = Path(tempfile.mkdtemp())
        # comms/charc is a junction escaping the mailbox root.
        link = self.root / "charc"
        if not _make_dir_link(link, outside):
            self.skipTest("cannot create a junction/symlink on this platform")
        # Seed a message directly in the (escaped) inbox, bypassing role_mail
        # (posting would itself be refused -- that path is already guarded).
        (outside / "inbox").mkdir()
        (outside / "inbox" / "m.md").write_text(
            "---\nfrom: operator\nto: charc\ntype: fyi\nsubject: s\n"
            "posted: x\nmsg-id: y\n---\n\nb\n", encoding="utf-8")
        # The ack is REFUSED (the read/ dest escapes the root), nothing moved.
        with self.assertRaises(rm.MailError) as ctx:
            rm.ack_message(self.root, "charc", "m.md")
        self.assertIn("OUTSIDE the mailbox root", str(ctx.exception))
        # The escape target is byte-untouched: no read/ created, msg still in inbox.
        self.assertFalse((outside / "read").exists(),
                         "a blocked ack must not create the escaped read/ dir")
        self.assertTrue((outside / "inbox" / "m.md").is_file(),
                        "a blocked ack must not move the message")

    def test_ack_from_a_junctioned_inbox_is_blocked(self) -> None:
        # The SOURCE side (FIX-1 r4): comms/charc/inbox ITSELF is a junction to an
        # external dir (charc/ + charc/read stay in-tree, so the DEST guard alone
        # would pass) -- ack must refuse BEFORE it reads/removes the external
        # source file.
        outside = Path(tempfile.mkdtemp())
        ext_inbox = outside / "ext_inbox"
        ext_inbox.mkdir()
        (ext_inbox / "m.md").write_text(
            "---\nfrom: operator\nto: charc\ntype: fyi\nsubject: s\n"
            "posted: x\nmsg-id: y\n---\n\nb\n", encoding="utf-8")
        (self.root / "charc").mkdir()
        if not _make_dir_link(self.root / "charc" / "inbox", ext_inbox):
            self.skipTest("cannot create a junction/symlink on this platform")
        with self.assertRaises(rm.MailError) as ctx:
            rm.ack_message(self.root, "charc", "m.md")
        self.assertIn("OUTSIDE the mailbox root", str(ctx.exception))
        # The external source is NOT moved/removed, and no read/ was created.
        self.assertTrue((ext_inbox / "m.md").is_file(),
                        "a blocked ack must not move/remove the external source")
        self.assertFalse((self.root / "charc" / "read").exists())

    def test_ack_in_a_normal_tree_still_works(self) -> None:
        # The other direction -- the guard is not always-fail.
        finals = rm.post_message(self.root, "operator", ["charc"], "fyi", "s",
                                 "body", now=FIXED)
        dest = rm.ack_message(self.root, "charc", finals[0].name)
        self.assertTrue(dest.is_file())
        self.assertEqual(dest.parent, self.root / "charc" / "read")


class EnumerationContainmentTest(TmpRootMixin, unittest.TestCase):
    """list/read/peek REFUSE a junctioned inbox BEFORE enumerating/printing its
    external content (FIX-1 r5: _list_inbox is the enumeration choke, reached by
    read/list/peek BEFORE ack's source guard would fire). Tested at the CLI level
    because the ordering -- list+print happens before ack -- is what matters."""

    def _run(self, argv: list[str]) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            rc = rm.main(argv)
        return rc, out.getvalue(), err.getvalue()

    def _junction_inbox_with_secret(self) -> Path:
        """Make comms/charc/inbox a junction to an external dir holding a message
        with a DISTINCTIVE body; return the external dir. Skips if unbuildable."""
        outside = Path(tempfile.mkdtemp())
        ext = outside / "ext"
        ext.mkdir()
        (ext / "m.md").write_text(
            "---\nfrom: operator\nto: charc\ntype: fyi\nsubject: SECRET-SUBJ\n"
            "posted: x\nmsg-id: y\n---\n\nEXTERNAL-SECRET-BODY\n",
            encoding="utf-8")
        (self.root / "charc").mkdir()
        if not _make_dir_link(self.root / "charc" / "inbox", ext):
            self.skipTest("cannot create a junction/symlink on this platform")
        return ext

    def test_read_all_cli_refuses_before_printing_external_content(self) -> None:
        ext = self._junction_inbox_with_secret()
        rc, out, err = self._run(["--comms-root", str(self.root), "read",
                                  "--role", "charc", "--all"])
        self.assertEqual(rc, 1)
        # The external content was NOT listed/printed (refused before enumeration).
        self.assertNotIn("EXTERNAL-SECRET-BODY", out)
        self.assertNotIn("SECRET-SUBJ", out)
        self.assertIn("OUTSIDE the mailbox root", err)
        # Nothing moved; no read/ created.
        self.assertTrue((ext / "m.md").is_file())
        self.assertFalse((self.root / "charc" / "read").exists())

    def test_peek_and_list_cli_also_refuse(self) -> None:
        self._junction_inbox_with_secret()
        for cmd in ("peek", "list"):
            rc, out, err = self._run(["--comms-root", str(self.root), cmd,
                                      "--role", "charc"])
            self.assertEqual(rc, 1, cmd)
            self.assertNotIn("EXTERNAL-SECRET-BODY", out, cmd)
            self.assertIn("OUTSIDE the mailbox root", err, cmd)

    def test_missing_inbox_reads_empty_normal(self) -> None:
        # The pre-migration/normal case: a not-yet-created singular inbox is
        # EMPTY, not an escape -- read must NOT raise.
        rc, out, _ = self._run(["--comms-root", str(self.root), "read",
                                "--role", "charc", "--all"])
        self.assertEqual(rc, 0)
        self.assertIn("empty", out)

    def test_normal_inbox_reads_fine(self) -> None:
        rm.post_message(self.root, "operator", ["charc"], "fyi", "hello",
                        "NORMAL-BODY", now=FIXED)
        rc, out, _ = self._run(["--comms-root", str(self.root), "read",
                                "--role", "charc", "--all"])
        self.assertEqual(rc, 0)
        self.assertIn("NORMAL-BODY", out)


class UnaddressedRoleContainmentTest(TmpRootMixin, unittest.TestCase):
    """A post must NEVER create an UNADDRESSED role's tree -- so a junctioned
    unaddressed role cannot be escaped through on a post that never names it.

    (FIX-1: the pre-fix _ensure_singular_tree unconditionally mkdir'd EVERY
    role's inbox/read, so posting --to orchestrator with comms/charc a junction
    to an outside dir mutated the outside target. The scoped
    _ensure_recipient_trees only touches THIS post's validated recipients.)
    """

    def test_post_never_creates_an_unaddressed_junctioned_role(self) -> None:
        outside = Path(tempfile.mkdtemp())
        # comms/charc is a junction escaping the mailbox root; charc is NOT a
        # recipient of the post below.
        link = self.root / "charc"
        if not _make_dir_link(link, outside):
            self.skipTest("cannot create a junction/symlink on this platform")
        before = {p.name for p in outside.iterdir()}
        finals = rm.post_message(self.root, "operator", ["orchestrator"], "fyi",
                                 "s", "body", now=FIXED)
        # The addressed recipient delivered.
        self.assertEqual(len(finals), 1)
        self.assertEqual(
            len(list((self.root / "orchestrator" / "inbox").glob("*.md"))), 1)
        # The unaddressed junctioned role's tree was NOT created -> the escape
        # target is untouched (pre-fix: outside/inbox + outside/read appear).
        self.assertEqual({p.name for p in outside.iterdir()}, before,
                         "an unaddressed junctioned role must not be created")
        self.assertFalse((outside / "inbox").exists())
        self.assertFalse((outside / "read").exists())


class LinkedCheckoutNoticeTest(TmpRootMixin, unittest.TestCase):
    """The defaulted-root advisory (never a failure -- a deliberate post into a
    linked working copy is legitimate)."""

    def _pointer(self, primary: Path, linked: Path) -> None:
        (primary / ".git" / "worktrees" / "wt").mkdir(parents=True)
        (linked / ".git").write_text(
            f"gitdir: {(primary / '.git' / 'worktrees' / 'wt').as_posix()}\n",
            encoding="utf-8")

    def test_primary_checkout_behind_a_linked_copy_is_resolved(self) -> None:
        primary = Path(tempfile.mkdtemp())
        linked = Path(tempfile.mkdtemp())
        self._pointer(primary, linked)
        self.assertEqual(rm._linked_checkout_primary(linked).resolve(),
                         primary.resolve())

    def test_a_normal_checkout_yields_no_notice(self) -> None:
        normal = Path(tempfile.mkdtemp())
        (normal / ".git").mkdir()
        self.assertIsNone(rm._linked_checkout_primary(normal))

    def test_notice_is_printed_only_when_the_root_was_defaulted(self) -> None:
        primary = Path(tempfile.mkdtemp())
        linked = Path(tempfile.mkdtemp())
        self._pointer(primary, linked)
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(rm, "_REPO_ROOT", linked):
            with redirect_stdout(out), redirect_stderr(err):
                rc = rm.main(["post-verified", "--from", "charc", "--to",
                              "operator", "--type", "status", "--subject", "s",
                              "--body", "b"])
        self.assertEqual(rc, 0, "the notice must never fail the post")
        self.assertIn(str(primary.resolve()), err.getvalue())

    def test_notice_accompanies_a_root_mismatch(self) -> None:
        primary = Path(tempfile.mkdtemp())
        linked = Path(tempfile.mkdtemp())
        self._pointer(primary, linked)
        err = io.StringIO()
        with mock.patch.object(rm, "_REPO_ROOT", linked):
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                rc = rm.main(["post-verified", "--expect-root",
                              str(primary / "comms"), "--from", "charc",
                              "--to", "operator", "--type", "status",
                              "--subject", "s", "--body", "b"])
        text = err.getvalue()
        self.assertEqual(rc, 1)
        self.assertIn("notice:", text)
        self.assertIn("mailbox root mismatch", text)
        self.assertLess(text.index("notice:"), text.index("error:"))
        self.assertEqual(_tree(linked / "comms"), set())

    def test_a_matching_expected_root_suppresses_the_notice(self) -> None:
        primary = Path(tempfile.mkdtemp())
        linked = Path(tempfile.mkdtemp())
        self._pointer(primary, linked)
        err = io.StringIO()
        with mock.patch.object(rm, "_REPO_ROOT", linked):
            with redirect_stdout(io.StringIO()), redirect_stderr(err):
                rc = rm.main(["post-verified", "--expect-root",
                              str(linked / "comms"), "--from", "charc", "--to",
                              "operator", "--type", "status", "--subject", "s",
                              "--body", "b"])
        self.assertEqual(rc, 0)
        self.assertNotIn("notice:", err.getvalue())

    def test_notice_is_skipped_when_the_root_is_explicit(self) -> None:
        primary = Path(tempfile.mkdtemp())
        linked = Path(tempfile.mkdtemp())
        self._pointer(primary, linked)
        err2 = io.StringIO()
        with mock.patch.object(rm, "_REPO_ROOT", linked):
            with redirect_stdout(io.StringIO()), redirect_stderr(err2):
                rm.main(["--comms-root", str(self.root), "post-verified",
                         "--from", "charc", "--to", "operator", "--type",
                         "status", "--subject", "s", "--body", "b"])
        self.assertNotIn(str(primary.resolve()), err2.getvalue())


if __name__ == "__main__":
    unittest.main()
