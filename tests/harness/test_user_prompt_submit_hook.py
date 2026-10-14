"""UserPromptSubmit hook (ARC-8): role resolution + recovery-record write +
the singular unread notice; ALWAYS exits 0.

The per-generation registry heartbeat / register / per-gen-inbox block was
deleted with the singular-inbox simplification. What the hook still does: resolve
the role (env or the session-keyed recovery store), record it for a future
resume, and fire the unread notice for any comms role reading its shared
comms/<role>/inbox.
"""

from __future__ import annotations

import io
import json
import tempfile
import unittest
from contextlib import redirect_stdout
from datetime import UTC, datetime
from pathlib import Path
from unittest import mock

from _loader import REPO_ROOT, load_user_prompt_submit

ups = load_user_prompt_submit()

T0 = datetime(2024, 6, 1, 12, 0, 0, tzinfo=UTC)


def _usage_line(input_tokens: int, cache_creation: int = 0,
                cache_read: int = 0) -> str:
    """One transcript line whose message.usage sums to the given tokens."""
    return json.dumps({"message": {"usage": {
        "input_tokens": input_tokens,
        "cache_creation_input_tokens": cache_creation,
        "cache_read_input_tokens": cache_read,
    }}})


class TmpRootMixin:
    def setUp(self) -> None:
        self.root = Path(tempfile.mkdtemp())


class NoticeAndRecordTest(TmpRootMixin, unittest.TestCase):
    def _seed_inbox(self, *parts: str, mtype: str = "fyi") -> None:
        inbox = self.root.joinpath(*parts)
        inbox.mkdir(parents=True, exist_ok=True)
        (inbox / "20240601T120000Z-x.md").write_text(
            f"---\ntype: {mtype}\n---\nbody", encoding="utf-8")

    def test_orchestrator_notice_is_the_singular_inbox(self) -> None:
        # ARC-8: the orchestrator reads its shared comms/orchestrator/inbox (no
        # per-generation subtree, no registry entry written).
        self._seed_inbox("orchestrator", "inbox")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ups.handle_user_prompt_submit(
                {"session_id": "sid-1", "transcript_path": "/t"},
                {"HARNESS_ROLE": "orchestrator"}, self.root, T0)
        self.assertIn("[comms] 1 unread for orchestrator", buf.getvalue())
        # No registry entry, no per-generation subtree.
        self.assertFalse((self.root / "sessions").exists())
        self.assertFalse((self.root / "orchestrator" / "sid-1").exists())

    def test_charc_unread_notice_fires(self) -> None:
        self._seed_inbox("charc", "inbox")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ups.handle_user_prompt_submit(
                {"session_id": "sid-c", "transcript_path": "/t"},
                {"HARNESS_ROLE": "charc"}, self.root, T0)
        self.assertIn("[comms] 1 unread for charc", buf.getvalue())
        # No registry (nothing registers now).
        self.assertFalse((self.root / "sessions").exists())

    def test_no_session_id_role_from_env_still_notices(self) -> None:
        # No session_id (and no fallback) -> the role still resolves from the env
        # var; the notice fires. No recovery record is written (nothing to key on).
        self._seed_inbox("charc", "inbox")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ups.handle_user_prompt_submit(
                {"transcript_path": "/t"}, {"HARNESS_ROLE": "charc"},
                self.root, T0)
        self.assertIn("[comms] 1 unread for charc", buf.getvalue())
        self.assertFalse((self.root / "roles").exists()
                         and list((self.root / "roles").iterdir()))

    def test_ctx_notice_prints_after_comms_notice(self) -> None:
        self._seed_inbox("charc", "inbox")
        transcript = self.root / "transcript.jsonl"
        transcript.write_text(_usage_line(250_000), encoding="utf-8")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ups.handle_user_prompt_submit(
                {"session_id": "sid-ctx", "transcript_path": str(transcript)},
                {"HARNESS_ROLE": "charc"}, self.root, T0)
        out = buf.getvalue()
        self.assertIn("[comms]", out)
        self.assertIn("[ctx] 250K of 1000K (25%)", out)
        self.assertLess(out.index("[comms]"), out.index("[ctx]"))

    def test_no_ctx_line_when_transcript_path_absent(self) -> None:
        self._seed_inbox("charc", "inbox")
        buf = io.StringIO()
        with redirect_stdout(buf):
            ups.handle_user_prompt_submit(
                {"session_id": "sid-noctx"}, {"HARNESS_ROLE": "charc"},
                self.root, T0)
        self.assertIn("[comms]", buf.getvalue())
        self.assertNotIn("[ctx]", buf.getvalue())

    def test_degraded_fallback_env_id_keys_the_role_record(self) -> None:
        # No payload session_id, but CLAUDE_CODE_SESSION_ID is present: the role
        # record is written keyed by that fallback id (for a later resume).
        ups.handle_user_prompt_submit(
            {"transcript_path": "/t"},
            {"HARNESS_ROLE": "charc", "CLAUDE_CODE_SESSION_ID": "fallback-sid"},
            self.root, T0)
        self.assertEqual(
            ups.read_session_role(self.root, "fallback-sid"), "charc")

    def test_internal_exception_exits_zero(self) -> None:
        with mock.patch.object(ups, "_read_hook_payload",
                               side_effect=RuntimeError("boom")):
            self.assertEqual(ups.main(), 0)

    def test_unread_notice_counts_decision_request_subset(self) -> None:
        inbox = self.root / "operator" / "inbox"
        inbox.mkdir(parents=True)
        (inbox / "a.md").write_text("---\ntype: decision_request\n---\nx",
                                    encoding="utf-8")
        (inbox / "b.md").write_text("---\ntype: fyi\n---\ny", encoding="utf-8")
        note = ups.unread_notice("operator", self.root)
        self.assertIn("2 unread for operator", note)
        self.assertIn("1 decision_request", note)

    def test_unread_notice_has_no_session_flag(self) -> None:
        # The drain command is uniform now -- no --session anywhere.
        self._seed_inbox("orchestrator", "inbox")
        note = ups.unread_notice("orchestrator", self.root)
        self.assertIsNotNone(note)
        self.assertIn("read --role orchestrator --all", note)
        self.assertNotIn("--session", note)

    def test_refuses_unsafe_session_id_no_path_escape(self) -> None:
        # A crafted traversal session_id is nulled before any path build -- no
        # record is written outside comms/roles/, and the hook never crashes.
        result = ups.handle_user_prompt_submit(
            {"session_id": "../../evil", "transcript_path": "/t"},
            {"HARNESS_ROLE": "charc"}, self.root, T0)
        self.assertIsNone(result)
        self.assertFalse((self.root / "roles").exists()
                         and list((self.root / "roles").iterdir()))
        self.assertFalse((self.root.parent / "evil").exists())

    def test_unknown_role_silent(self) -> None:
        buf = io.StringIO()
        with redirect_stdout(buf):
            ups.handle_user_prompt_submit(
                {"session_id": "x"}, {"HARNESS_ROLE": "nobody"}, self.root, T0)
        self.assertEqual(buf.getvalue(), "")


class SingleSourcedRoleSetTest(TmpRootMixin, unittest.TestCase):
    """B-12 Gap 1: the notice hook's role set IS role_mail's SINGULAR_INBOX_ROLES
    (no drift), so adding a peer director to the mail core auto-covers the unread
    notice. ARC-8: every role is singular, so COMMS_ROLES == SINGULAR_INBOX_ROLES."""

    def _load_role_mail(self):
        import importlib.util as ilu
        spec = ilu.spec_from_file_location(
            "role_mail", REPO_ROOT / "scripts" / "role_mail.py")
        rm = ilu.module_from_spec(spec)
        spec.loader.exec_module(rm)
        return rm

    def test_comms_roles_single_sourced_from_role_mail(self) -> None:
        rm = self._load_role_mail()
        self.assertEqual(tuple(ups.SINGULAR_INBOX_ROLES),
                         tuple(rm.SINGULAR_INBOX_ROLES))
        # Every role is singular now: COMMS_ROLES IS the singular set.
        self.assertEqual(set(ups.COMMS_ROLES), set(rm.SINGULAR_INBOX_ROLES))
        self.assertIn("orchestrator", ups.COMMS_ROLES)

    def test_added_director_role_fires_the_notice(self) -> None:
        # Simulate adding a peer director to the mail-core set: the notice must
        # fire for it (the hook consults SINGULAR_INBOX_ROLES, not a hardcode).
        inbox = self.root / "newdir" / "inbox"
        inbox.mkdir(parents=True)
        (inbox / "a.md").write_text("---\ntype: fyi\n---\nx", encoding="utf-8")
        with mock.patch.object(
                ups, "SINGULAR_INBOX_ROLES",
                ("charc", "operator", "orchestrator", "newdir")), \
             mock.patch.object(
                ups, "COMMS_ROLES",
                ("charc", "operator", "orchestrator", "newdir")):
            note = ups.unread_notice("newdir", self.root)
        self.assertIsNotNone(note)
        self.assertIn("[comms] 1 unread for newdir", note)


class ContextDepthNoticeTest(TmpRootMixin, unittest.TestCase):
    """context_depth_notice: the [ctx] gauge computed off a transcript's tail."""

    def _write(self, name: str, text: str) -> Path:
        path = self.root / name
        path.write_text(text, encoding="utf-8")
        return path

    def test_two_usage_lines_uses_the_last_ones_sum(self) -> None:
        # First line sums to 100_000; the LAST line sums to 250_000 across all
        # three fields -- the notice must reflect the last, not the first.
        path = self._write("t.jsonl", "\n".join([
            _usage_line(100_000),
            _usage_line(200_000, cache_creation=30_000, cache_read=20_000),
        ]))
        notice = ups.context_depth_notice(str(path), {}, "charc")
        self.assertEqual(notice, "[ctx] 250K of 1000K (25%)")

    def test_cap_line_appears_at_and_above_cap_not_below(self) -> None:
        below = self._write("below.jsonl", _usage_line(399_999))
        at = self._write("at.jsonl", _usage_line(400_000))
        above = self._write("above.jsonl", _usage_line(400_001))
        below_notice = ups.context_depth_notice(str(below), {}, "charc")
        at_notice = ups.context_depth_notice(str(at), {}, "charc")
        above_notice = ups.context_depth_notice(str(above), {}, "charc")
        self.assertNotIn("DEPTH CAP", below_notice)
        self.assertIn("DEPTH CAP 400K REACHED", at_notice)
        self.assertIn("docs/charc-state.md", at_notice)
        self.assertIn("DEPTH CAP 400K REACHED", above_notice)

    def test_cap_line_role_label_defaults_to_role_when_unknown(self) -> None:
        path = self._write("cap.jsonl", _usage_line(400_000))
        notice = ups.context_depth_notice(str(path), {}, None)
        self.assertIn("docs/role-state.md", notice)

    def test_env_overrides_honored(self) -> None:
        path = self._write("t.jsonl", _usage_line(600))
        notice = ups.context_depth_notice(
            str(path),
            {"HARNESS_CTX_WINDOW": "1000", "HARNESS_CTX_CAP": "1000000"},
            "charc")
        self.assertEqual(notice, "[ctx] 1K of 1K (60%)")
        self.assertNotIn("DEPTH CAP", notice)

    def test_bad_env_values_ignored_defaults_kept(self) -> None:
        path = self._write("t.jsonl", _usage_line(250_000))
        notice = ups.context_depth_notice(
            str(path),
            {"HARNESS_CTX_WINDOW": "not-a-number",
             "HARNESS_CTX_CAP": "also-bad"},
            "charc")
        self.assertEqual(notice, "[ctx] 250K of 1000K (25%)")

    def test_missing_file_returns_none(self) -> None:
        missing = self.root / "does-not-exist.jsonl"
        self.assertIsNone(ups.context_depth_notice(str(missing), {}, "charc"))

    def test_empty_file_returns_none(self) -> None:
        path = self._write("empty.jsonl", "")
        self.assertIsNone(ups.context_depth_notice(str(path), {}, "charc"))

    def test_malformed_only_line_returns_none(self) -> None:
        path = self._write("bad.jsonl", "not json at all {{{")
        self.assertIsNone(ups.context_depth_notice(str(path), {}, "charc"))

    def test_no_transcript_path_returns_none(self) -> None:
        self.assertIsNone(ups.context_depth_notice(None, {}, "charc"))
        self.assertIsNone(ups.context_depth_notice("", {}, "charc"))

    def test_big_file_still_finds_usage_past_600kb_of_filler(self) -> None:
        filler = ("x" * 200 + "\n") * 4000  # well over 600 KB of filler lines
        path = self.root / "big.jsonl"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(filler)
            fh.write(_usage_line(300_000))
        self.assertGreater(path.stat().st_size, 600 * 1024)
        notice = ups.context_depth_notice(str(path), {}, "charc")
        self.assertEqual(notice, "[ctx] 300K of 1000K (30%)")


if __name__ == "__main__":
    unittest.main()
