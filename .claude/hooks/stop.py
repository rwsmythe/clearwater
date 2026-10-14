"""Stop hook: continue-on-unread for a comms-director session (continuous-ops bridge).

Stdlib-only. Wired via the tracked .claude/settings.json `Stop` hook so a comms
director session (charc) that finishes a turn with UNREAD comms mail CONTINUES to
process it -- a message that arrived mid-turn surfaces at turn-close rather than
waiting for the operator's next prompt. This approximates continuous ops absent an
idle-wake feature. It stays operator-SESSION-bounded (it only fires when a turn
ends; it is NOT an autonomous timer wake) and is consistent with the comms
taxonomy (autonomously processing fyi/status/return_report is in-lane; dispatch
authority stays operator-hand-carried).

Contract:
  * Reads the role from the HARNESS_ROLE env var (via the shared ROLE_ENV). If it
    is not in STOP_HOOK_ROLES -> SILENT no-op (exit 0): does nothing in any
    orchestrator / plain / ad-hoc session. charc is a singular-inbox role, so the
    shared comms/charc/inbox is read and no per-generation session_id is needed.
  * Reads the Stop-hook JSON payload from stdin (RAW BYTES, decoded utf-8-sig so a
    leading BOM is stripped regardless of the console codepage) for
    `stop_hook_active`.
    LOOP-SAFETY (load-bearing): it blocks (continues) ONLY when there is unread AND
    `stop_hook_active` is false -- so a turn gets AT MOST ONE continuation, and a
    stuck/undrained inbox can NEVER run the agent in an unbounded loop. On ANY
    stdin read/decode/parse failure the active-flag DEFAULTS TRUE (allow stop) --
    the safe direction, never the loop direction. The agent drains its inbox each
    cycle, so the natural terminator is an empty inbox.
  * On block: prints {"decision":"block","reason":<notice>} to stdout (the
    Stop-hook block protocol) so the agent continues + sees the unread.
  * Otherwise exits 0 (allow stop / idle).
  * ALWAYS degrades to exit 0 on ANY error -- a hook failure must NEVER trap the
    agent in a non-stoppable state.

Output JSON is ASCII (the Windows-codepage stdout constraint); message files read
as UTF-8.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

# Roles for which the Stop hook fires. V1: the singular-inbox director only
# (the shared comms/<role>/inbox -- no per-generation session_id complexity).
STOP_HOOK_ROLES = ("charc",)

# Resilient sibling-hook import (mirrors user_prompt_submit / session_end): the
# import runs at module load, BEFORE main()'s try/except. A broken / missing
# user_prompt_submit.py would otherwise crash the hook with a nonzero exit and
# TRAP the agent in a non-stoppable state. Put the hooks dir on sys.path and
# guard the import; on failure main() degrades to a logged exit-0 no-op. The
# unread-notice machinery (ROLE_ENV, the file-relative comms root, unread_notice)
# is single-sourced from the UserPromptSubmit hook -- no duplicated logic.
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from user_prompt_submit import (  # noqa: E402  (sibling-hook import by bare name)
        ROLE_ENV,
        _comms_root_from_file,
        unread_notice,
    )
    _IMPORT_OK = True
except Exception as _import_exc:  # noqa: BLE001 -- never trap the agent
    _IMPORT_OK = False
    _IMPORT_ERR = _import_exc


def _parse_stop_payload(raw: bytes) -> dict:
    """Parse the Stop-hook JSON payload bytes into a dict.

    Decodes utf-8-sig so a leading BOM is stripped no matter how the spawning
    shell/console encodes the pipe. On ANY decode/parse failure (or a non-dict
    payload) returns {"stop_hook_active": True} -- the SAFE default: treat the
    stop as already a continuation so the hook ALLOWS it, guaranteeing an
    unreadable/garbled payload can NEVER trap the agent in an unbounded continue
    loop (the dangerous direction). An EMPTY payload is also treated as allow-stop.
    A clean payload is returned as-is; `_stop_hook_active` then defaults a MISSING
    key to active=True (allow stop) -- the same safe direction -- so a genuine
    first stop (the documented payload carries the flag explicitly false) still
    yields the one bounded continuation.
    """
    try:
        # STRICT decode (no errors="replace"): a payload with ANY invalid byte is
        # garbled -> UnicodeDecodeError -> the allow-stop path below. Salvaging a
        # corrupted payload with errors="replace" could resurrect a stale `false`
        # from a byte-damaged body and wrongly block (the fail-open contract).
        cleaned = raw.decode("utf-8-sig").strip()
    except Exception:  # noqa: BLE001
        return {"stop_hook_active": True}  # SAFE: undecodable -> allow stop
    if not cleaned:
        return {"stop_hook_active": True}  # SAFE: empty payload -> allow stop
    try:
        data = json.loads(cleaned)
    except Exception:  # noqa: BLE001
        return {"stop_hook_active": True}  # SAFE: garbled payload -> allow stop
    return data if isinstance(data, dict) else {"stop_hook_active": True}


def _stop_hook_active(payload: dict) -> bool:
    """True (allow stop) UNLESS stop_hook_active is EXACTLY boolean False.

    The documented Stop-hook contract carries an explicit boolean (false on a
    genuine first stop, true on the continuation's own stop). Block-once happens
    ONLY on an exact `false`; a MISSING key OR any present-but-non-boolean value
    (null/None, 0, "", a list) is ambiguous -- the hook cannot distinguish a first
    stop from an Nth continuation -- so it allow-stops (the safe, fail-open
    direction). This closes every unbounded-continue vector: a substrate that ever
    drops, renames, or non-boolean-ifies the field can never loop on a stuck
    inbox; at worst the feature silently no-ops, never traps the agent. (Identity
    `is False` -- not truthiness -- so the int 0 / empty string never count as the
    boolean false.)
    """
    return payload.get("stop_hook_active", True) is not False


def handle_stop(payload: dict, env: dict, root: Path) -> str | None:
    """Return the block-reason string for a gated session with unread mail, else None.

    Separated from main() for unit-testability over a tmp comms root. Pure (takes
    payload/env/root explicitly). Returns None whenever the stop should be ALLOWED
    (non-gated role, the single-continuation guard, or an empty inbox); returns the
    drain-instruction reason ONLY on a first stop with unread mail.
    """
    role = env.get(ROLE_ENV, "")
    if role not in STOP_HOOK_ROLES:
        return None  # no-op in every non-gated session
    # LOOP-SAFETY: continue AT MOST ONCE per stop-cycle. On the continuation's own
    # stop, stop_hook_active is true -> allow stop (the agent has had its one turn
    # to drain; anything still unread surfaces on the next prompt via the
    # UserPromptSubmit hook).
    if _stop_hook_active(payload):
        return None
    # charc is a singular-inbox role: the shared inbox is read (no session_id).
    notice = unread_notice(role, root)
    if not notice:
        return None  # inbox empty -> allow stop (idle)
    return (
        f"{notice}\n"
        "(continue-on-unread close-hook): you finished a turn with comms mail "
        "that arrived mid-turn. DRAIN it now (the read command above) and process "
        "anything actionable, then stop. This fires at most ONCE per turn; if "
        "nothing is actionable after reading, just stop."
    )


def main() -> int:
    # The ENTIRE body is inside the outer try -- including the degraded-import
    # warning -- so even a broken/closed stderr (or a pathological exception repr)
    # on the import-failure path can NEVER make the hook exit nonzero and trap the
    # agent. ALWAYS exit 0.
    try:
        if not _IMPORT_OK:
            # The sibling import failed at load time. Degrade to a logged no-op.
            print(
                "[comms] WARNING Stop hook: could not import the unread-notice "
                f"logic from user_prompt_submit.py ({_IMPORT_ERR!r}); skipping the "
                "continue-on-unread check. The session is NOT blocked.",
                file=sys.stderr)
            return 0
        try:
            raw = sys.stdin.buffer.read()
        except Exception:  # noqa: BLE001 -- cannot read stdin -> allow stop
            raw = b""
        payload = _parse_stop_payload(raw)
        reason = handle_stop(payload, dict(os.environ), _comms_root_from_file())
        if reason is not None:
            print(json.dumps({"decision": "block", "reason": reason}))
    except Exception:  # noqa: BLE001 -- a hook failure must never trap the agent
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
