"""UserPromptSubmit hook: role recovery + the unread mailbox notice.

Stdlib-only. Wired via .claude/settings.json so that on EVERY prompt:

  * the session's role is RESOLVED (the launch-time HARNESS_ROLE env var, or the
    session-keyed recovery store on a resume where HARNESS_ROLE is unset) and
    RECORDED for a future resume;
  * the unread mailbox notice fires for the session's role -- the shared
    comms/<role>/inbox for EVERY role (charc / operator / orchestrator
    are all singular inboxes since ARC-8) -- one ASCII
    `[comms] N unread ... run: <drain cmd>` line, with the decision_request
    subset noted. Silent no-op for an unknown role.

ARC-8 collapsed the orchestrator onto the uniform singular-inbox model, so the
per-generation session registry + its lifecycle hooks (SessionStart / SessionEnd
+ the heartbeat here) are GONE. What survives -- and is DEFINED here now, since
this is the only remaining lifecycle hook that other hooks import from -- is the
session-id-keyed ROLE-RECOVERY store (comms/roles/<session_id>): the session_id
lives on ONLY as a role-recovery key, never as an addressing key.

ALWAYS exits 0 -- a hook failure must NEVER block the operator's prompt, so any
internal exception is swallowed.
"""

from __future__ import annotations

import contextlib
import json
import os
import re
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# A session_id becomes a filename under comms/roles/, so it MUST be a safe single
# path segment. Every path-building site (the role-recovery store) and every
# consumer of a payload/env session_id goes through is_valid_session_id, so a
# crafted hook payload / env id can never route a write outside comms/roles/.
_SESSION_ID_RE = re.compile(r"[A-Za-z0-9._-]+")

# The env var carrying the launch-time role (renamed from the legacy harness's
# SWING_ROLE). The hook reads it; the launcher sets it.
ROLE_ENV = "HARNESS_ROLE"


def is_valid_session_id(session_id) -> bool:  # noqa: ANN001
    """True iff session_id is a safe single path segment (no traversal/seps)."""
    if not isinstance(session_id, str) or not session_id:
        return False
    if session_id in (".", ".."):
        return False
    if "/" in session_id or "\\" in session_id:
        return False
    if session_id != Path(session_id).name:
        return False
    return bool(_SESSION_ID_RE.fullmatch(session_id))


# --- path + payload helpers ------------------------------------------------

def _comms_root_from_file() -> Path:
    """The comms/ tree resolved from THIS file's location (NOT cwd).

    .claude/hooks/user_prompt_submit.py -> repo root is two parents up from
    .claude. Resolving from __file__ makes the hooks correct from any session cwd.
    """
    return Path(__file__).resolve().parent.parent.parent / "comms"


def _read_hook_payload() -> dict:
    """Parse the hook JSON from stdin; {} on any problem (degrade-gracefully)."""
    import json
    try:
        raw = sys.stdin.read()
    except Exception:  # noqa: BLE001
        return {}
    if not raw.strip():
        return {}
    try:
        data = json.loads(raw)
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def _degraded_session_id(env: dict) -> str | None:
    """Last-resort fallback id from the undocumented env var (logged-degraded)."""
    return env.get("CLAUDE_CODE_SESSION_ID") or None


def _atomic_write_text(path: Path, content: str) -> None:
    """Write content to `path` atomically (stage a same-dir temp + os.replace).

    The same atomic pattern role_mail uses for mail delivery (a lifted stdlib
    helper, NOT a cross-import). The temp is staged in `path`'s OWN directory so
    the os.replace is same-filesystem-atomic (the cross-volume os.replace gotcha).
    A reader never observes a torn intermediate at `path`, and a write that fails
    while staging leaves the prior file at `path` intact.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise
    try:
        os.replace(tmp_name, str(path))
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise


# --- role-recovery store (comms/roles/<session_id>) ------------------------
# A thin session_id -> role record so a RESUMED session (which bypasses the
# launcher, so HARNESS_ROLE is unset) can still recover its role. Written at the
# FIRST prompt of a session when HARNESS_ROLE IS set (the original launch carries
# the role), read as the fallback when it is absent (a resume). One tiny file per
# session_id under comms/roles/, the filename IS the session_id (the path-safety
# contract goes through is_valid_session_id). Plain text: the bare role string.
# Best-effort + degrade-gracefully: a missing/unreadable/empty record reads as
# None (never raises). The recovered string is judged against the known comms
# roles at the HOOK boundary (COMMS_ROLES), so a garbage record is treated as
# absent there -- the store layer stays decoupled from the role set.

def _roles_dir(root: Path) -> Path:
    return root / "roles"


def _role_path(root: Path, session_id: str) -> Path:
    if not is_valid_session_id(session_id):
        raise ValueError(f"unsafe session_id {session_id!r}")
    return _roles_dir(root) / session_id


def write_session_role(root: Path, session_id: str, role: str) -> Path | None:
    """Record session_id -> role for resume-time recovery (best-effort).

    Returns the path written, or None if the inputs are unfit (no/invalid
    session_id, empty role). Never raises on a normal bad-input path; an OS write
    failure propagates to the caller's best-effort guard (the hook swallows it).
    """
    if not session_id or not is_valid_session_id(session_id) or not role:
        return None
    path = _role_path(root, session_id)
    _atomic_write_text(path, role + "\n")
    return path


def read_session_role(root: Path, session_id: str) -> str | None:
    """The recorded role STRING for session_id, or None (missing/unreadable/empty).

    Degrade-gracefully: a missing file, an OS error, or an empty/whitespace file
    returns None. A NON-empty recorded string is returned AS-IS (after strip) --
    this helper does NOT judge whether the string is a recognized comms role; that
    validation belt lives at the HOOK boundary (the caller accepts the recovered
    string only when `recovered in COMMS_ROLES`), so a garbage record is treated
    as absent there. This never raises, so the hook keeps its
    never-block-a-prompt guarantee.
    """
    if not session_id or not is_valid_session_id(session_id):
        return None
    path = _role_path(root, session_id)
    if not path.is_file():
        return None
    try:
        recorded = path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    return recorded or None


# Single-source the singular-inbox role set from the mail core (role_mail.py),
# so adding a peer director to role_mail's SINGULAR_INBOX_ROLES also makes the
# unread notice fire for it (B-12 Gap 1: no drift between delivery + notice).
# Loaded by path (scripts/ is not on the hooks sys.path) and guarded -- a hook
# must NEVER block a prompt, so a missing/broken role_mail degrades to the
# shipped default below.
_DEFAULT_SINGULAR_INBOX_ROLES = ("charc", "operator", "orchestrator")
try:
    import importlib.util as _ilu
    _rm_path = Path(__file__).resolve().parent.parent.parent / "scripts" / "role_mail.py"
    # Load under a PRIVATE module name so this hook-local read of role_mail's
    # constant cannot collide with / reuse a stale-or-partially-initialized
    # "role_mail" already on sys.modules in the hook process.
    _spec = _ilu.spec_from_file_location("_role_mail_hook", _rm_path)
    _rm = _ilu.module_from_spec(_spec)
    _spec.loader.exec_module(_rm)
    SINGULAR_INBOX_ROLES = tuple(_rm.SINGULAR_INBOX_ROLES)
except Exception:  # noqa: BLE001 -- never block a prompt; degrade to the default
    SINGULAR_INBOX_ROLES = _DEFAULT_SINGULAR_INBOX_ROLES

# Every comms role has a singular inbox now, so the unread notice fires for the
# whole SINGULAR_INBOX_ROLES set (single-sourced from role_mail, so a new peer
# director is auto-covered).
COMMS_ROLES = SINGULAR_INBOX_ROLES


def _is_decision_request(path: Path) -> bool:
    """True if the message's frontmatter type is decision_request (else False)."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return False
    if not text.startswith("---"):
        return False
    rest = text.split("\n", 1)[1] if "\n" in text else ""
    for line in rest.split("\n"):
        stripped = line.strip()
        if stripped == "---":
            break
        if stripped.startswith("type:"):
            return stripped.split(":", 1)[1].strip() == "decision_request"
    return False


def _inbox_for_role(root: Path, role: str) -> Path | None:
    """The singular inbox dir whose unread the notice counts for this role."""
    if role in SINGULAR_INBOX_ROLES:
        return root / role / "inbox"
    return None


def unread_notice(role: str, root: Path) -> str | None:
    """One ASCII notice line for role's unread inbox, or None if there is none.

    Pure (takes the root explicitly) so it is testable over a tmp tree. Every
    role reads its shared comms/<role>/inbox (singular model), so the drain
    command is uniform -- no --session.
    """
    inbox = _inbox_for_role(root, role)
    if inbox is None or not inbox.is_dir():
        return None
    msgs = sorted(inbox.glob("*.md"))
    if not msgs:
        return None
    dr = sum(1 for m in msgs if _is_decision_request(m))
    dr_note = f" ({dr} decision_request)" if dr else ""
    role_mail = Path(__file__).resolve().parent.parent.parent / "scripts" / \
        "role_mail.py"
    drain = f'python "{role_mail}" read --role {role} --all'
    return f"[comms] {len(msgs)} unread for {role}{dr_note} -- run: {drain}"


# --- context-depth notice ---------------------------------------------------
# The session's transcript (a .jsonl, one JSON object per line) carries each
# assistant turn's token usage on message.usage. The CURRENT CONTEXT DEPTH is
# input_tokens + cache_creation_input_tokens + cache_read_input_tokens on the
# LAST such line -- printed on every prompt as a one-line ASCII gauge, with a
# roll-over warning once depth reaches the cap. Transcripts run tens of MB and
# this hook fires on EVERY prompt, so only the TAIL of the file is read.

_DEFAULT_CTX_WINDOW = 1_000_000
_DEFAULT_CTX_CAP = 400_000
_CTX_TAIL_BYTES = 512 * 1024
CTX_WINDOW_ENV = "HARNESS_CTX_WINDOW"
CTX_CAP_ENV = "HARNESS_CTX_CAP"


def _int_env(env: dict, name: str, default: int) -> int:
    """default, unless env[name] parses as an int (bad/missing -> default)."""
    raw = env.get(name)
    if raw is None:
        return default
    try:
        return int(raw)
    except (TypeError, ValueError):
        return default


def _fmt_k(n: int) -> str:
    """n rendered as whole thousands, e.g. 449_000 -> '449K'."""
    return f"{round(n / 1000)}K"


def _last_usage_dict(transcript_path: Path) -> dict | None:
    """The last message.usage dict in transcript_path, or None on any problem.

    Reads only the tail (_CTX_TAIL_BYTES) of the file and scans lines backwards
    for the last one that both contains "usage" and parses to a JSON object
    with a dict message.usage -- best-effort, never raises.
    """
    try:
        size = transcript_path.stat().st_size
    except OSError:
        return None
    try:
        with open(transcript_path, "rb") as fh:
            if size > _CTX_TAIL_BYTES:
                fh.seek(-_CTX_TAIL_BYTES, os.SEEK_END)
            data = fh.read()
    except OSError:
        return None
    for raw in reversed(data.split(b"\n")):
        raw = raw.strip()
        if not raw or b"usage" not in raw:
            continue
        try:
            record = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(record, dict):
            continue
        message = record.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if isinstance(usage, dict):
            return usage
    return None


def context_depth_notice(transcript_path, env: dict, role: str | None) -> str | None:
    """The one-line ASCII [ctx] gauge for transcript_path, or None.

    Best-effort + silent: a missing transcript_path, an unreadable file, no
    usage line, or malformed JSON all return None -- never raises. window/cap
    default to 1_000_000 / 400_000, overridable via HARNESS_CTX_WINDOW /
    HARNESS_CTX_CAP (bad values ignored, default kept).
    """
    if not transcript_path:
        return None
    usage = _last_usage_dict(Path(transcript_path))
    if usage is None:
        return None
    try:
        depth = (int(usage.get("input_tokens") or 0)
                + int(usage.get("cache_creation_input_tokens") or 0)
                + int(usage.get("cache_read_input_tokens") or 0))
    except (TypeError, ValueError):
        return None

    window = _int_env(env, CTX_WINDOW_ENV, _DEFAULT_CTX_WINDOW)
    cap = _int_env(env, CTX_CAP_ENV, _DEFAULT_CTX_CAP)
    pct = round(depth * 100 / window) if window else 0
    line = f"[ctx] {_fmt_k(depth)} of {_fmt_k(window)} ({pct}%)"
    if depth >= cap:
        role_label = role or "role"
        line += (f" -- DEPTH CAP {_fmt_k(cap)} REACHED: roll over at the next "
                 f"boundary (write docs/{role_label}-state.md, announce, stop "
                 "draining)")
    return line


def handle_user_prompt_submit(payload: dict, env: dict, root: Path,
                              now: datetime) -> None:
    """The UserPromptSubmit action (separated from main() for testability).

    Resolves the session_id (for the role-recovery key), resolves the role
    (HARNESS_ROLE, or the session-keyed recovery store on a resume), records the
    role for a future resume, then fires the unread notice for any comms role,
    then the context-depth gauge for any session with a transcript.
    ALWAYS best-effort; never blocks a prompt.
    """
    # 0. Resolve + validate the session_id (the role-recovery fallback keys on
    #    it). An unsafe id is nulled so it never reaches a path build.
    raw_session_id = payload.get("session_id")
    session_id = raw_session_id
    if not session_id:
        session_id = _degraded_session_id(env)
    if session_id and not is_valid_session_id(session_id):
        session_id = None

    # 1. Resolve the role: the launch-time env var, OR the session-keyed recovery
    #    store on a resume (HARNESS_ROLE absent). The recovered string is accepted
    #    ONLY when it is a known comms role (the validation belt) -- a garbage
    #    record is treated as absent, never a crash.
    role = env.get(ROLE_ENV, "")
    if not role and session_id:
        recovered = read_session_role(root, session_id)
        if recovered in COMMS_ROLES:
            role = recovered

    # 2. Record role -> session for a FUTURE resume (best-effort), only at the
    #    ORIGINAL launch (HARNESS_ROLE set) with a usable session_id. A write
    #    failure must never block a prompt.
    if env.get(ROLE_ENV) and session_id:
        try:
            write_session_role(root, session_id, env[ROLE_ENV])
        except OSError:
            pass

    # 3. Unread notice (any comms role reads its shared singular inbox).
    if role in COMMS_ROLES:
        notice = unread_notice(role, root)
        if notice:
            print(notice)

    # 4. Context-depth gauge (any session with a transcript, role known or
    #    not) -- best-effort/silent per context_depth_notice's own contract.
    ctx_notice = context_depth_notice(payload.get("transcript_path"), env, role)
    if ctx_notice:
        print(ctx_notice)


def main() -> int:
    try:
        payload = _read_hook_payload()
        handle_user_prompt_submit(payload, dict(os.environ),
                                  _comms_root_from_file(), datetime.now(UTC))
    except Exception:  # noqa: BLE001 -- a hook failure must never block a prompt
        return 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
