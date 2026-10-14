"""Task C (B-14) -- the Stop hook decision matrix.

Stdlib unittest (no [web] extra). The Stop hook continues a comms-director
session that finished a turn with unread mail, so a message that arrived
mid-turn is drained at turn-close rather than waiting for the next prompt. These
tests drive the testable seam (handle_stop / _parse_stop_payload) over a tmp
comms root so the real comms/ tree is never touched; the subprocess exit-0
portability discipline is covered by test_hooks_wiring (the HOOKS tuple).
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOKS_DIR = REPO_ROOT / ".claude" / "hooks"


def _load_stop():
    # The Stop hook imports its sibling unread-notice logic by bare name, so the
    # hooks dir must be on sys.path (the same not-a-package pattern the hooks use).
    sys.path.insert(0, str(HOOKS_DIR))
    spec = importlib.util.spec_from_file_location("stop", HOOKS_DIR / "stop.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["stop"] = mod
    spec.loader.exec_module(mod)
    return mod


class StopHookTest(unittest.TestCase):
    def setUp(self) -> None:
        self.mod = _load_stop()
        self.root = Path(tempfile.mkdtemp())

    def _seed_charc_inbox(self, subject: str = "ping", mtype: str = "fyi") -> str:
        inbox = self.root / "charc" / "inbox"
        inbox.mkdir(parents=True, exist_ok=True)
        name = "20240601T120000Z-operator-ping.md"
        (inbox / name).write_text(
            f"---\nfrom: operator\nto: charc\ntype: {mtype}\n"
            f"subject: {subject}\n---\n\nbody\n",
            encoding="utf-8")
        return name

    def test_stop_hook_roles_is_charc_only(self) -> None:
        # V1 gating: the singular-inbox director only (no per-generation session).
        self.assertEqual(self.mod.STOP_HOOK_ROLES, ("charc",))

    def test_non_comms_role_is_silent_noop(self) -> None:
        # Unread mail present, but a non-gated role never blocks.
        self._seed_charc_inbox()
        self.assertIsNone(
            self.mod.handle_stop({"stop_hook_active": False}, {}, self.root))
        self.assertIsNone(self.mod.handle_stop(
            {"stop_hook_active": False},
            {"HARNESS_ROLE": "orchestrator"}, self.root))

    def test_charc_unread_first_stop_blocks(self) -> None:
        self._seed_charc_inbox(subject="hello-director")
        reason = self.mod.handle_stop(
            {"stop_hook_active": False}, {"HARNESS_ROLE": "charc"}, self.root)
        self.assertIsInstance(reason, str)
        self.assertTrue(reason)

    def test_charc_stop_hook_active_true_allows_stop(self) -> None:
        # The single-continuation loop guard: on the continuation's own stop the
        # flag is true, so a naive impl that ignored it would block forever. This
        # impl allows the stop.
        self._seed_charc_inbox()
        self.assertIsNone(self.mod.handle_stop(
            {"stop_hook_active": True}, {"HARNESS_ROLE": "charc"}, self.root))

    def test_empty_inbox_allows_stop(self) -> None:
        self.assertIsNone(self.mod.handle_stop(
            {"stop_hook_active": False}, {"HARNESS_ROLE": "charc"}, self.root))

    def test_malformed_stdin_allows_stop(self) -> None:
        # A garbled payload defaults the flag TRUE (the safe direction) -> allow
        # stop even with unread mail; never the unbounded-continue direction.
        self._seed_charc_inbox()
        payload = self.mod._parse_stop_payload(b"not json at all")
        self.assertTrue(payload.get("stop_hook_active"))
        self.assertIsNone(self.mod.handle_stop(
            payload, {"HARNESS_ROLE": "charc"}, self.root))

    def test_key_absent_allows_stop(self) -> None:
        # Loop-safety: a valid payload that LACKS stop_hook_active is ambiguous
        # (first stop vs Nth continuation indistinguishable) -> allow stop, never
        # block, even with unread mail. Closes the only unbounded-continue vector
        # if the substrate ever drops/renames the field. A naive absent->False
        # impl would block here; this impl allows the stop.
        self._seed_charc_inbox()
        self.assertIsNone(self.mod.handle_stop(
            {"session_id": "x"}, {"HARNESS_ROLE": "charc"}, self.root))

    def test_non_boolean_falsey_values_allow_stop(self) -> None:
        # Loop-safety hardening: ONLY an exact boolean False (a genuine first
        # stop) blocks. A present-but-non-boolean falsey value (null/0/""/[]) is
        # ambiguous/malformed -> allow stop, never block, even with unread mail.
        # A naive bool()-truthiness impl would block on these; this impl (identity
        # `is not False`) allow-stops.
        self._seed_charc_inbox()
        for value in (None, 0, "", []):
            self.assertIsNone(
                self.mod.handle_stop(
                    {"stop_hook_active": value},
                    {"HARNESS_ROLE": "charc"}, self.root),
                f"a non-boolean falsey stop_hook_active {value!r} must allow stop")

    def test_empty_and_unreadable_stdin_default_to_allow_stop(self) -> None:
        # The fail-open default: an empty (or whitespace-only) stdin payload
        # parses to the safe sentinel {"stop_hook_active": True} -> allow stop.
        for raw in (b"", b"  \n", b"\xef\xbb\xbf"):
            payload = self.mod._parse_stop_payload(raw)
            self.assertTrue(payload.get("stop_hook_active"),
                            f"empty/unreadable stdin {raw!r} must allow stop")

    def test_invalid_utf8_payload_allows_stop(self) -> None:
        # A byte-corrupted payload that would otherwise parse to a stale `false`
        # (an invalid byte in an unrelated field) must NOT be salvaged into a
        # block: the strict decode raises -> the allow-stop sentinel. A naive
        # errors="replace" decode would resurrect the false and block.
        raw = b'{"stop_hook_active": false, "x": "\xff"}'
        payload = self.mod._parse_stop_payload(raw)
        self.assertTrue(payload.get("stop_hook_active"),
                        "an invalid-UTF-8 payload must allow stop (fail-open)")
        self._seed_charc_inbox()
        self.assertIsNone(self.mod.handle_stop(
            payload, {"HARNESS_ROLE": "charc"}, self.root))

    def test_import_failure_path_exits_zero_even_if_stderr_raises(self) -> None:
        # The always-exit-0 contract on the degraded-import path: even if the
        # warning write to a broken/closed stderr raises, main() must still return
        # 0 (never a nonzero exit that traps the agent). The whole body, including
        # the _IMPORT_OK branch, is inside the outer try.
        class _BrokenStderr:
            def write(self, *a, **k):  # noqa: ANN002, ANN003
                raise OSError("broken pipe")

            def flush(self, *a, **k):  # noqa: ANN002, ANN003
                pass

        with mock.patch.object(self.mod, "_IMPORT_OK", False), \
                mock.patch.object(self.mod, "_IMPORT_ERR",
                                  RuntimeError("boom"), create=True), \
                mock.patch.object(sys, "stderr", _BrokenStderr()):
            rc = self.mod.main()
        self.assertEqual(rc, 0)

    def test_block_emits_decision_json(self) -> None:
        # main() emits the Stop-hook block protocol JSON on a first stop with
        # unread mail. Drives main() over the tmp root (no real comms touched).
        self._seed_charc_inbox()
        buf = io.StringIO()
        fake_stdin = mock.Mock()
        fake_stdin.buffer = io.BytesIO(b'{"stop_hook_active": false}')
        with mock.patch.object(self.mod, "_comms_root_from_file",
                               return_value=self.root), \
                mock.patch.dict(os.environ, {"HARNESS_ROLE": "charc"}), \
                mock.patch.object(sys, "stdin", fake_stdin), \
                contextlib.redirect_stdout(buf):
            rc = self.mod.main()
        self.assertEqual(rc, 0)
        out = json.loads(buf.getvalue())
        self.assertEqual(out["decision"], "block")
        self.assertTrue(out["reason"])


if __name__ == "__main__":
    unittest.main()
