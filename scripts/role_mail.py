"""Inter-role file mailbox CLI (the generic harness comms core).

A durable, stdlib-only message bus between the harness's roles. One file per
message under a gitignored ``comms/`` tree; ``read`` MOVES a message inbox ->
read (an ack), nothing is ever deleted by this tool.

Roles: one singular director (``charc``), the ``orchestrator``,
and the ``operator``. The taxonomy is intentionally small; adding a peer
director later follows the small enumerated checklist at the bottom of this
module (and the charter's peer-director-add checklist) -- one director ships.

UNIFORM SINGULAR ADDRESSING: every role has ONE fixed inbox
``comms/<role>/inbox`` (+ ``comms/<role>/read``). ``--to charc`` /
``--to operator`` / ``--to orchestrator`` each deliver to the
single named inbox -- there is no ambiguity and no per-generation resolution.
The orchestrator is drained by whichever generation is live (the handoff
transfers the drain; see docs/orchestrator-context.md's stop-drain-on-rollover
convention). The session_id survives ONLY as a role-recovery key (the
UserPromptSubmit hook's resume store), never as an addressing key.

VERIFIED POSTING: ``post-verified`` takes exactly the ``post`` arguments and,
in the same call, confirms the message landed in the inbox it was addressed to
under the mailbox root that was actually resolved (``--expect-root`` asserts
WHICH root that is, up front). It confirms the SPECIFIC message it just wrote --
a per-message ``msg-id`` + ``posted`` discriminator, not the shared headers
alone -- so a header-twin (same from/to/type/subject) cannot answer for it.
Anything else is a non-zero exit naming where the message actually is, or that
it is nowhere.

CONTAINMENT BOUNDARY (what the _within guard is + is NOT): ALL of THIS tool's
mailbox OPERATIONS are ``_within``-guarded fail-closed against a junctioned /
symlinked inbox or role dir -- post-delivery (recipient-tree creation + temp
staging + each delivery target), list/read/peek ENUMERATION (``_list_inbox`` /
``_list_read`` refuse an EXISTING-but-escaping dir BEFORE any glob/read/print),
and ack (SOURCE inbox + DEST read/ dir). Create + enumerate paths route through
``_guarded_mkdir`` / ``_guarded_enum_dir`` (both resolve symlinks + junctions via
``_within``); a MISSING dir stays empty (a not-yet-created singular inbox is
normal). So a reparse point escaping the mailbox root is refused across the whole
role_mail surface. It is NOT a claim that every write under ``comms/`` is
guarded, and it is deliberately NOT a defense against an active attacker.
OUT-OF-MODEL (decisively): the hook's role-recovery store (``comms/roles/``), the
launcher, and the mail UI (SEPARATE modules); a TOCTOU race (a process swapping a
validated dir for a junction BETWEEN check and use); and a DELIBERATELY
junctioned tree. A junctioned comms tree is a SETUP MISCONFIGURATION -- an actor
who can create the junction ALREADY has the filesystem access any read would
grant -- so the operator owns comms-tree setup and the structural answer is an OS
sandbox (BANKED), not a check in this tool.

Governance lock (L1, information-vs-authority): role->role traffic is limited
to ``fyi|status|query|return_report``. ``decision_request`` is valid ONLY when
EVERY recipient is the operator -- this tool refuses to write a
decision_request addressed to any other role (hard error, exit 1). That is the
load-bearing protection: transport is automated, authority is not. Do not
soften it.

ASCII-only console output (Windows cp1252 stdout gotcha); message files are
written/read as UTF-8.

A subject over SUBJECT_MAX_CHARS (120; operator-directed 2026-09-24, was 100) characters is REJECTED (nothing is
written) -- keep it to one line, outcome first, and put the rest in the body.

Usage (from the repo root):
    python scripts/role_mail.py post --from charc --to orchestrator \\
        --type status --subject "Arc 1 shipped" --body "All green."
    python scripts/role_mail.py post-verified --from charc --to opsdir \\
        --type status --subject "Arc 1 shipped" --body "All green." \\
        --expect-root /path/to/comms
    python scripts/role_mail.py list --role charc
    python scripts/role_mail.py read --role charc --all
    python scripts/role_mail.py read --role orchestrator --all
    python scripts/role_mail.py peek --role operator

Layout (auto-created on first use):
    comms/charc/inbox         comms/charc/read

    comms/operator/inbox      comms/operator/read
    comms/orchestrator/inbox  comms/orchestrator/read   (singular)
"""

from __future__ import annotations

import argparse
import contextlib
import os
import re
import secrets
import sys
import tempfile
from datetime import UTC, datetime
from pathlib import Path

# The role set: one singular director (charc), the operator, and the
# orchestrator. Every role's inbox is SINGULAR (one fixed inbox) -- addressing
# is uniform, with no per-generation resolution.
VALID_FROM = ("charc", "orchestrator", "operator")
VALID_TO = ("charc", "orchestrator", "operator")
VALID_TYPES = ("fyi", "status", "query", "return_report", "decision_request")

# The roles whose inbox is SINGULAR (one fixed inbox). Every role is singular;
# VALID_TO == SINGULAR_INBOX_ROLES (kept as its own name because the hooks
# single-source their unread-notice role set from this constant).
SINGULAR_INBOX_ROLES = ("charc", "operator", "orchestrator")

_SLUG_MAX = 40
SUBJECT_MAX_CHARS = 120  # operator-directed 2026-09-24 (was 100)
_REPO_ROOT = Path(__file__).resolve().parent.parent


class MailError(Exception):
    """A validation / governance error to surface as exit 1 with a message."""


class VerificationError(MailError):
    """A posted message did not land where it was addressed (post-verified)."""


class _AsciiArgumentParser(argparse.ArgumentParser):
    """ArgumentParser whose own usage/error output is cp1252-safe."""

    def _print_message(self, message, file=None):  # noqa: ANN001
        if message:
            super()._print_message(_ascii(message), file)


def _now() -> datetime:
    """UTC clock seam (monkeypatched in tests for deterministic stamps)."""
    return datetime.now(UTC)


def _ascii(text: str) -> str:
    """Make text safe for Windows cp1252 stdout (backslash-escape non-ASCII)."""
    return text.encode("ascii", "backslashreplace").decode("ascii")


def _write_temp(root: Path, final: Path, content: str) -> Path:
    """Write content to a temp file in final's directory; return the temp path.

    Same-directory temp keeps the later os.replace on one filesystem (the
    Windows os.replace cross-volume gotcha). Cleans up on write failure. The
    parent-dir creation routes through the single _within-guarded choke point
    (_guarded_mkdir), so a symlinked/junctioned inbox cannot host the temp
    outside the mailbox root.
    """
    _guarded_mkdir(root, final.parent)
    fd, tmp_name = tempfile.mkstemp(dir=str(final.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(content)
    except BaseException:
        with contextlib.suppress(OSError):
            os.unlink(tmp_name)
        raise
    return Path(tmp_name)


def _slugify(subject: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", subject.lower()).strip("-")
    if len(slug) > _SLUG_MAX:
        slug = slug[:_SLUG_MAX].rstrip("-")
    return slug or "msg"


def _comms_root(args: argparse.Namespace) -> Path:
    root = getattr(args, "comms_root", None)
    if root:
        return Path(root)
    return _REPO_ROOT / "comms"


# --- addressing: parse + resolve a --to target -----------------------------

def _parse_to_target(target: str) -> tuple[str, str | None]:
    """Split a single --to token into (role, session_id_or_None).

    Every role is a singular inbox now, so the returned session_id is ALWAYS
    None (the tuple shape is kept so the landing helpers stay verbatim). A
    ``:<session_id>`` suffix is rejected -- per-generation addressing is gone.
    """
    raw = target.strip()
    if ":" in raw:
        raise MailError(
            f"per-generation addressing was removed; {target!r} carries a "
            "':<session_id>' suffix. Every role is a singular inbox -- address "
            "it by bare name (e.g. 'orchestrator').")
    if raw not in VALID_TO:
        raise MailError(
            "invalid recipient " + repr(raw) + "; valid roles: "
            + "|".join(VALID_TO))
    return raw, None


def _within(parent: Path, child: Path) -> bool:
    """True iff `child` resolves to a path CONTAINED in `parent` (both resolved).

    ``resolve()`` follows symlinks AND Windows junctions, so this catches a
    reparse point that escapes the mailbox tree even though the LEXICAL path
    still reads as contained -- the hole behind a delivery that lands through a
    link elsewhere while ``relative_to(root)`` reads as inside. Any resolve/
    comparison error is treated as NOT contained (fail-closed).
    """
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except (OSError, ValueError):
        return False


def _guarded_mkdir(root: Path, target: Path) -> None:
    """Create `target` (mkdir -p) ONLY if it resolves INSIDE `root`.

    The single containment choke point for THIS tool's MAILBOX DELIVERY paths --
    post's recipient-tree creation + temp staging, and ack's move all route their
    directory creation through here. It is TARGETED defense-in-depth on the
    delivery paths, NOT a guard over every write under comms/ (a junctioned comms
    tree at large -- the role-recovery store, the launcher's writes -- is
    out-of-model; see the CONTAINMENT BOUNDARY note in the module docstring).
    Resolves symlinks AND junctions first (via _within), so a reparse-point dir
    that escapes the mailbox tree while its lexical path reads as inside is
    REFUSED fail-closed.
    """
    if not _within(root, target):
        raise MailError(
            f"refusing to create {target}: it resolves OUTSIDE the mailbox "
            f"root {root} (symlink/junction escape); nothing was written.")
    target.mkdir(parents=True, exist_ok=True)


def _guarded_enum_dir(root: Path, d: Path) -> Path:
    """Return `d` for enumeration, REFUSING an existing-but-escaping dir.

    The read-side sibling of _guarded_mkdir: the mailbox READ paths (list / read
    / peek all go through _list_inbox/_list_read) must not glob/read/print the
    content of a junctioned/symlinked inbox that resolves OUTSIDE the mailbox
    root. A MISSING dir is fine and returned as-is -- a not-yet-created singular
    inbox/read is normal (the caller treats absence as empty); only an EXISTING
    dir that escapes once resolved is refused fail-closed.
    """
    if d.exists() and not _within(root, d):
        raise MailError(
            f"refusing to enumerate {d}: it resolves OUTSIDE the mailbox root "
            f"{root} (symlink/junction escape); nothing was read.")
    return d


def _inbox_for_target(root: Path, role: str, session_id: str | None = None,
                      now: datetime | None = None) -> Path:
    """Resolve a (role, session_id) target to its concrete inbox directory.

    Every role is singular now, so session_id is ignored (kept in the signature
    so the landing verify stays verbatim). Raises on an unknown role.
    """
    if role in SINGULAR_INBOX_ROLES:
        return root / role / "inbox"
    raise MailError(
        "invalid recipient " + repr(role) + "; valid roles: " + "|".join(VALID_TO))


def _ensure_recipient_trees(
        root: Path,
        resolved: list[tuple[str, str | None, Path]]) -> None:
    """Create the inbox/read dirs for ONLY this post's validated recipients.

    Scoped to the ADDRESSED recipients -- never an unaddressed role -- so a post
    can never mkdir a foreign role's tree. That matters for containment: if an
    UNADDRESSED role dir (e.g. comms/charc) is a junction/symlink escaping the
    tree, blindly creating every role's tree on every post would mutate the
    escape target even for a post that never named that role. Every dir is
    created through the single _within-guarded choke point (_guarded_mkdir); the
    recipients' inboxes were already contained-checked in post_message's
    pre-staging loop, so a refusal there leaves the root byte-for-byte untouched.
    """
    for _role, _sid, inbox in resolved:
        _guarded_mkdir(root, inbox)
        _guarded_mkdir(root, inbox.parent / "read")


def _parse_recipients(raw: str, now: datetime | None = None
                      ) -> list[tuple[str, str | None]]:
    """Parse + validate + de-dupe a comma-separated --to into (role, None) pairs.

    De-dupe is by the resolved (role, session_id) identity (session_id is always
    None in the singular model).
    """
    tokens = [t.strip() for t in raw.split(",") if t and t.strip()]
    if not tokens:
        raise MailError(
            "no recipients given; valid roles: " + "|".join(VALID_TO))
    seen: list[tuple[str, str | None]] = []
    for tok in tokens:
        pair = _parse_to_target(tok)
        if pair not in seen:
            seen.append(pair)
    return seen


def _compose(sender: str, recipient: str, mtype: str, subject: str,
             posted: str, msg_id: str, thread: str | None, body: str) -> str:
    lines = [
        "---",
        f"from: {sender}",
        f"to: {recipient}",
        f"type: {mtype}",
        f"subject: {subject}",
        f"posted: {posted}",
        f"msg-id: {msg_id}",
    ]
    if thread:
        lines.append(f"thread: {thread}")
    lines.append("---")
    text = "\n".join(lines) + "\n\n" + body.rstrip("\n") + "\n"
    return text


def _recipient_label(role: str, session_id: str | None = None) -> str:
    """The 'to:' frontmatter label for a resolved recipient (always the role)."""
    return role


def _unique_path(inbox: Path, stamp: str, sender: str, slug: str) -> Path:
    """A collision-PROOF final path: stamp + sender + slug + a random token.

    The leading stamp+sender+slug keep filenames human-sortable/readable; the
    short random token defeats the same-second cross-process race (two processes
    posting the same sender/subject in the same second would otherwise both pick
    the same name and the second os.replace would clobber the first). The token
    is collision-resistant; the existence loop is a belt for the astronomically-
    unlikely token clash.
    """
    base = f"{stamp}-{sender}-{slug}-{secrets.token_hex(4)}"
    candidate = inbox / f"{base}.md"
    suffix = 2
    while candidate.exists():
        candidate = inbox / f"{base}-{suffix}.md"
        suffix += 1
    return candidate


def _unique_dest(dest_dir: Path, filename: str) -> Path:
    """A non-colliding path in dest_dir for filename (suffix -2, -3, ...).

    Used when acking inbox -> read so an archived message with the same name is
    never overwritten -- ack must never delete history.
    """
    candidate = dest_dir / filename
    if not candidate.exists():
        return candidate
    stem = filename[:-3] if filename.endswith(".md") else filename
    suffix = 2
    while True:
        candidate = dest_dir / f"{stem}-{suffix}.md"
        if not candidate.exists():
            return candidate
        suffix += 1


# --- the single write path (CLI + UI both go here) -------------------------

def post_message(
    root: Path,
    sender: str,
    recipients: list[str],
    mtype: str,
    subject: str,
    body: str,
    thread: str | None = None,
    now: datetime | None = None,
    posted_ids: list[tuple[Path, str, str, str]] | None = None,
) -> list[Path]:
    """Validate, governance-lock, and deliver one message.

    ``recipients`` are raw --to tokens (each a bare role: ``charc`` /
    ``operator`` / ``orchestrator``). Every role is a singular
    inbox. Validation order: sender -> type -> CR/LF guard -> recipients parse
    -> L1 lock -> resolve inboxes -> containment guard -> deliver. Returns the
    committed final Paths (recipient order).

    ``posted_ids`` (optional out-param, backward-compatible): if a list is
    passed, it is EXTENDED with one ``(final_path, to_label, posted, msg_id)``
    record per committed delivery -- the WRITE-side authoritative per-message
    discriminators ``post-verified`` uses to confirm THE specific message it
    wrote (not a header-twin). Left None by every other caller (cmd_post, the
    UI), so the delivery contract is unchanged for them.

    DELIVERY CONTRACT (the honest one -- a file mailbox cannot give cross-
    process transactional atomicity, and the database that could was
    deliberately declined; context is single-machine cooperating roles):

      * PER-RECIPIENT atomicity IS real: each recipient's file is staged to a
        same-directory temp and committed with a single ``os.replace``, so a
        reader never observes a torn or half-written message.
      * The multi-recipient "all-or-nothing" rollback is BEST-EFFORT on a
        QUIESCENT tree, NOT a transaction. If a later recipient's commit fails,
        already-committed copies are unlinked -- but under concurrency an
        earlier recipient (or a reader) may observe that recipient's copy in the
        window before the failure triggers the rollback, and a committed copy
        that cannot be unlinked is REPORTED as an incomplete rollback (named in
        the error), never hidden.
      * Pre-delivery validation failures -- a bad sender/type, a CR/LF
        injection, the L1 governance lock, a delivery target that resolves
        outside the mailbox root -- are all checked BEFORE any temp is staged,
        so those refusals genuinely leave the mailbox root byte-for-byte
        untouched ("nothing was written" is exact there; the multi-recipient
        window above is the one honest exception).

    Raises MailError on any validation/governance/IO failure.
    """
    if now is None:
        now = _now()
    if sender not in VALID_FROM:
        raise MailError(
            "invalid --from " + repr(sender)
            + "; valid senders: " + "|".join(VALID_FROM))
    if mtype not in VALID_TYPES:
        raise MailError(
            "invalid --type " + repr(mtype)
            + "; valid types: " + "|".join(VALID_TYPES))
    # Reject CR/LF in line-oriented frontmatter fields (frontmatter injection).
    for label, value in (("subject", subject), ("thread", thread)):
        if value is not None and ("\n" in value or "\r" in value):
            raise MailError(
                f"{label} may not contain newlines (frontmatter injection). "
                "Nothing was written.")
    if subject is not None and len(subject) > SUBJECT_MAX_CHARS:
        raise MailError(
            f"subject exceeds {SUBJECT_MAX_CHARS} characters "
            f"({len(subject)} given); one line, outcome first -- put the "
            "content in the body. Nothing was written.")
    pairs = _parse_recipients(",".join(recipients) if isinstance(recipients, list)
                              else recipients, now)
    # L1 governance lock: decision_request must address ONLY the operator.
    if mtype == "decision_request" and any(role != "operator"
                                           for role, _ in pairs):
        raise MailError(
            "L1: type 'decision_request' may be addressed ONLY to operator "
            "(role->role traffic is fyi|status|query|return_report). "
            "Nothing was written.")

    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    posted = now.strftime("%Y-%m-%dT%H:%M:%SZ")
    slug = _slugify(subject)

    # Resolve each recipient to its concrete inbox FIRST and de-dupe by the
    # RESOLVED concrete inbox -- so a repeated recipient collapses to one
    # delivery instead of two duplicate final paths in a single atomic post.
    resolved: list[tuple[str, str | None, Path]] = []
    seen_inboxes: set[Path] = set()
    for role, sid in pairs:
        inbox = _inbox_for_target(root, role, sid, now)
        if inbox in seen_inboxes:
            continue
        seen_inboxes.add(inbox)
        resolved.append((role, sid, inbox))

    # Compose each delivery + the D4-(b) PRE-WRITE CONTAINMENT GUARD: resolve
    # each delivery TARGET and refuse (before staging ANY temp) if it escapes
    # the mailbox root through a symlink/junction -- so a reparse-point inbox
    # cannot route the temp OR the commit out of tree while the lexical path
    # reads as inside. Checked here (pre-staging) => a refusal leaves the root
    # byte-for-byte untouched (all-or-nothing).
    targets: list[tuple[Path, str]] = []
    records: list[tuple[Path, str, str, str]] = []
    for role, sid, inbox in resolved:
        final = _unique_path(inbox, stamp, sender, slug)
        if not _within(root, final):
            raise MailError(
                f"post refused: delivery target {final} resolves OUTSIDE the "
                f"mailbox root {root} (symlink/junction escape); nothing was "
                "written.")
        msg_id = secrets.token_hex(8)
        label = _recipient_label(role, sid)
        content = _compose(sender, label, mtype, subject, posted, msg_id,
                           thread, body)
        targets.append((final, content))
        records.append((final, label, posted, msg_id))

    # All targets validated + contained: NOW create the trees for THIS post's
    # recipients ONLY (never an unaddressed role -- see _ensure_recipient_trees),
    # so a refusal above left the mailbox root byte-for-byte untouched.
    _ensure_recipient_trees(root, resolved)

    staged: list[tuple[Path, Path]] = []  # (temp, final)
    try:
        for final, content in targets:
            staged.append((_write_temp(root, final, content), final))
    except Exception as exc:
        for tmp, _ in staged:
            with contextlib.suppress(OSError):
                tmp.unlink()
        raise MailError(
            f"post failed while staging ({exc}); nothing was delivered."
        ) from exc
    committed: list[Path] = []
    try:
        for tmp, final in staged:
            os.replace(str(tmp), str(final))
            committed.append(final)
    except OSError as exc:
        unremoved: list[Path] = []
        for final in committed:
            try:
                final.unlink()
            except OSError:
                unremoved.append(final)
        for tmp, _ in staged:
            with contextlib.suppress(OSError):
                tmp.unlink()
        if unremoved:
            raise MailError(
                f"post failed during delivery ({exc}); rollback INCOMPLETE -- "
                "these were delivered and could not be removed: "
                + ", ".join(p.name for p in unremoved)) from exc
        raise MailError(
            f"post failed during delivery ({exc}); rolled back, nothing "
            "delivered.") from exc

    if posted_ids is not None:
        # Report the WRITE-side discriminators for the committed deliveries (all
        # of them on success -- a partial failure raised above).
        committed_set = set(committed)
        posted_ids.extend(r for r in records if r[0] in committed_set)
    return committed


# --- ack / inbox resolution ------------------------------------------------

def _role_inbox_dir(root: Path, role: str, session_id: str | None = None) -> Path:
    """The inbox dir for a role to LIST/READ/ACK (singular for every role)."""
    if role in SINGULAR_INBOX_ROLES:
        return root / role / "inbox"
    raise MailError(
        "invalid role " + repr(role) + "; valid roles: " + "|".join(VALID_TO))


def _role_read_dir(root: Path, role: str, session_id: str | None = None) -> Path:
    if role in SINGULAR_INBOX_ROLES:
        return root / role / "read"
    raise MailError(
        "invalid role " + repr(role) + "; valid roles: " + "|".join(VALID_TO))


def ack_message(root: Path, role: str, filename: str,
                session_id: str | None = None) -> Path:
    """Ack one message: move <inbox>/<filename> -> <read>/ (returns the dest).

    The single ack path (the CLI's cmd_read and the UI both call THIS). Uses
    _unique_dest so an archived message of the same name is never overwritten
    (ack must never delete history). filename MUST be a bare basename --
    traversal attempts are rejected (L3 mail custody). BOTH ends of the move are
    containment-guarded through _within: the SOURCE inbox (so a junctioned inbox
    cannot make ack read/remove an EXTERNAL source file) and the DEST read/ dir
    (via _guarded_mkdir). So a junctioned/symlinked role or inbox dir cannot make
    the ack rename read or land OUTSIDE the mailbox root. Raises MailError on
    invalid role, traversal, a missing inbox file, or a containment escape.
    """
    if filename != Path(filename).name or "/" in filename or "\\" in filename:
        raise MailError(f"refusing non-basename filename {filename!r}")
    inbox = _role_inbox_dir(root, role, session_id)
    if not _within(root, inbox):
        # Guard the SOURCE side: a junctioned inbox would otherwise have ack
        # read + remove a file OUTSIDE the mailbox root. Nothing is moved.
        raise MailError(
            f"refusing to ack from {inbox}: it resolves OUTSIDE the mailbox "
            f"root {root} (symlink/junction escape); nothing was moved.")
    src = inbox / filename
    if not src.is_file():
        raise MailError(
            f"no inbox message named {filename!r} for role {role}")
    read_dir = _role_read_dir(root, role, session_id)
    _guarded_mkdir(root, read_dir)  # guard the DEST side (junctioned role dir)
    dest = _unique_dest(read_dir, src.name)
    src.rename(dest)
    return dest


# --- subcommands -----------------------------------------------------------

def _read_frontmatter(path: Path) -> dict[str, str]:
    fm: dict[str, str] = {}
    try:
        text = path.read_text(encoding="utf-8")
    except OSError:
        return fm
    if not text.startswith("---"):
        return fm
    body = text.split("\n", 1)[1] if "\n" in text else ""
    for line in body.split("\n"):
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, val = line.partition(":")
            key = key.strip()
            if key not in fm:  # first occurrence wins; ignore injected dupes
                fm[key] = val.strip()
    return fm


def _resolve_body(args: argparse.Namespace) -> str:
    if args.body is not None:
        return args.body
    if args.body_file is not None:
        return Path(args.body_file).read_text(encoding="utf-8")
    return sys.stdin.read()


def cmd_post(args: argparse.Namespace) -> int:
    root = _comms_root(args)
    sender = args.__dict__["from"]
    body = _resolve_body(args)
    recipients = [r.strip() for r in args.to.split(",") if r.strip()]
    finals = post_message(
        root, sender, recipients, args.type, args.subject, body, args.thread)
    for final in finals:
        # final is <root>/<role>/inbox/<file>; show the path under comms/.
        rel = final.relative_to(root)
        print(f"posted -> {rel.as_posix()}")
    return 0


# --- post-verified: post + confirm the landing in ONE call ------------------
# The manual discipline this mechanizes is "post, then go look whether the file
# is really where you meant it" -- skipped exactly when it matters, and the
# failure it catches is silent by nature (the post reports success either way).

def _same_dir(a: Path, b: Path) -> bool:
    """True iff two paths name the same directory (existing or not)."""
    with contextlib.suppress(OSError, ValueError):
        if a.exists() and b.exists():
            return os.path.samefile(str(a), str(b))
    return (os.path.normcase(os.path.abspath(str(a)))
            == os.path.normcase(os.path.abspath(str(b))))


def _linked_checkout_primary(repo_root: Path) -> Path | None:
    """The PRIMARY checkout behind a linked working copy, or None.

    A linked working copy carries a ``.git`` FILE (a ``gitdir:`` pointer) where
    a primary checkout has a ``.git`` directory. Used only to NOTICE that a
    DEFAULTED mailbox root belongs to the linked copy -- posting into one on
    purpose is perfectly legitimate, so this never fails a post. Any problem
    reading the pointer yields None (advisory, best-effort, never raises).
    """
    try:
        marker = repo_root / ".git"
        if not marker.is_file():
            return None
        text = marker.read_text(encoding="utf-8", errors="replace").strip()
        prefix = "gitdir:"
        if not text.lower().startswith(prefix):
            return None
        pointer = Path(text[len(prefix):].strip())
        for parent in pointer.parents:
            if parent.name == ".git":
                return parent.parent
    except (OSError, ValueError):
        return None
    return None


def _read_sibling(inbox_path: Path) -> Path | None:
    """For an ``.../inbox/<file>`` path, its ``.../read/<file>`` sibling.

    None when the path is not directly under an ``inbox/`` directory. The
    landing check uses it to accept a message a receiver already acked (moved
    inbox/ -> read/) between the post and the verify -- see ``_actual_landing``.
    """
    if inbox_path.parent.name != "inbox":
        return None
    return inbox_path.parent.parent / "read" / inbox_path.name


def _actual_landing(inbox_final: Path) -> Path | None:
    """Where the message REALLY is now, or None if it is nowhere.

    The addressed inbox path, or -- if a receiver acked it in the verify gap --
    the ``read/`` sibling. Closes the ack-race false negative (an ack is normal,
    expected traffic, not a delivery failure): a landing check that only looked
    in ``inbox/`` reported a delivered-then-acked message as "did not land",
    driving a needless retry / duplicate.
    """
    if inbox_final.is_file():
        return inbox_final
    sibling = _read_sibling(inbox_final)
    if sibling is not None and sibling.is_file():
        return sibling
    return None


def _landed_in_expected(landed_dir: Path, expected_inbox: Path) -> bool:
    """True iff landed_dir is the addressed inbox OR its ``read/`` sibling.

    The ``read/`` sibling counts because a receiver may ack (inbox -> read) in
    the verify gap; both are legitimate resting places for the message.
    """
    if _same_dir(landed_dir, expected_inbox):
        return True
    if expected_inbox.name == "inbox":
        return _same_dir(landed_dir, expected_inbox.parent / "read")
    return False


def _verify_landing(root: Path, final: Path, sender: str, mtype: str,
                    subject: str, want_posted: str | None = None,
                    want_msg_id: str | None = None) -> str | None:
    """Why `final` is NOT a valid landing under `root`, or None if it is.

    Checks the message is really on disk (in its addressed ``inbox/`` OR the
    ``read/`` sibling a receiver may have acked it into), really CONTAINED in
    the mailbox root once symlinks/junctions are RESOLVED (a lexical containment
    check blesses a reparse point that escapes the tree), really in the inbox
    its own ``to:`` header names, really carries what was asked for, AND -- when
    the write-side discriminators are supplied (``want_posted`` / ``want_msg_id``,
    the D1 per-message identity) -- really is THE specific message just composed
    rather than a header-twin sharing from/to/type/subject. So "a file exists
    somewhere" cannot pass, and neither can "a file with the same headers".
    """
    landed = _actual_landing(final)
    if landed is None:
        return f"did not land at all: {final} is not there"
    if not _within(root, landed):
        return f"landed OUTSIDE the mailbox root: {landed}"
    fm = _read_frontmatter(landed)
    if not fm:
        return f"landed unreadable (no frontmatter): {landed}"
    label = fm.get("to", "")
    try:
        role, sid = _parse_to_target(label)
        expected = _inbox_for_target(root, role, sid)
    except MailError as exc:
        return f"landed carrying an unusable 'to: {label}' ({exc}): {landed}"
    if not _landed_in_expected(landed.parent, expected):
        return (f"landed in the WRONG inbox: {landed} -- addressed to "
                f"{label!r}, whose inbox is {expected}")
    for field, want in (("from", sender), ("type", mtype),
                        ("subject", subject)):
        if fm.get(field) != want:
            return (f"landed with {field}={fm.get(field)!r}, expected "
                    f"{want!r}: {landed}")
    # D1 per-message discriminator: when the write side told us WHICH message
    # this final is (its posted stamp + msg-id nonce), a landing that matches the
    # shared headers but carries a DIFFERENT stamp/nonce is a header-twin, not
    # our message -- reject it. Skipped when the discriminators are absent (a
    # mocked post / a legacy file), degrading to the header-only check.
    if want_posted is not None and fm.get("posted") != want_posted:
        return (f"landed with posted={fm.get('posted')!r}, expected "
                f"{want_posted!r} (header-twin, not the message just posted): "
                f"{landed}")
    if want_msg_id is not None and fm.get("msg-id") != want_msg_id:
        return (f"landed with msg-id={fm.get('msg-id')!r}, expected "
                f"{want_msg_id!r} (header-twin, not the message just posted): "
                f"{landed}")
    return None


def _landing_matches_request(token: str, landed: list[tuple[str, str]],
                             posted_msg_ids: set[str] | None = None) -> bool:
    """True iff a requested --to token is answered by one of the landed files.

    ``landed`` is a list of ``(to_label, msg_id)`` read off the files that
    really landed. A token matches when some landed file carries its role label
    AND -- when the write-side msg-id set is known (``posted_msg_ids``) and the
    landed file carries a msg-id -- that msg-id belongs to THIS post (a header-
    twin with a foreign/absent nonce does not answer the request). When the
    posted set is unknown (a mocked post) or the landed file has no msg-id, the
    match degrades to label-only (the pre-D1 behavior -- never a regression).
    """
    role, _ = _parse_to_target(token)
    for lbl, mid in landed:
        if lbl != role:
            continue
        if posted_msg_ids and mid and mid not in posted_msg_ids:
            continue  # right label, but not one of THIS post's messages
        return True
    return False


def cmd_post_verified(args: argparse.Namespace) -> int:
    root = _comms_root(args)
    defaulted = getattr(args, "comms_root", None) is None
    expect = getattr(args, "expect_root", None)
    mismatch = expect is not None and not _same_dir(root, Path(expect))
    # The notice goes out FIRST, so when the root is also wrong it is standing
    # next to the error explaining how the root got that way. Suppressed when
    # --expect-root was given and MATCHED: the caller stated this exact intent.
    if defaulted and (expect is None or mismatch):
        primary = _linked_checkout_primary(_REPO_ROOT)
        if primary is not None:
            print(
                _ascii(
                    f"notice: mailbox root defaulted to {Path(root).resolve()},"
                    f" which belongs to a linked working copy. The primary "
                    f"copy's mailbox is {(primary / 'comms').absolute()}. Pass "
                    "--comms-root if you meant that one."),
                file=sys.stderr)
    if mismatch:
        # Checked BEFORE the write: a root mismatch means the message would
        # land in a mailbox nobody is reading, so do not write it at all.
        raise MailError(
            f"mailbox root mismatch: resolved {Path(root).absolute()} but "
            f"--expect-root named {Path(expect).absolute()}. Nothing was "
            "written. Pass --comms-root to choose the root explicitly.")

    sender = args.__dict__["from"]
    body = _resolve_body(args)
    recipients = [r.strip() for r in args.to.split(",") if r.strip()]
    posted_ids: list[tuple[Path, str, str, str]] = []
    finals = post_message(
        root, sender, recipients, args.type, args.subject, body, args.thread,
        posted_ids=posted_ids)

    # The WRITE-side per-message discriminators, keyed by the exact final path
    # this post returned (independent of what is read back -- that is what makes
    # them a real discriminator, not a self-consistency tautology).
    want_by_final = {f: (posted, mid) for f, _lbl, posted, mid in posted_ids}
    posted_msg_ids = {mid for _f, _lbl, _p, mid in posted_ids}

    problems: list[str] = []
    for f in finals:
        want_posted, want_msg_id = want_by_final.get(f, (None, None))
        problem = _verify_landing(root, f, sender, args.type, args.subject,
                                  want_posted, want_msg_id)
        if problem is not None:
            problems.append(problem)

    # Read each landed file where it REALLY is now -- including the read/ sibling
    # a receiver may have acked it into in the verify gap -- so an acked
    # recipient is not misreported as a dropped one (the ack race the landing
    # check absorbs). Collect (to_label, msg_id) so the per-recipient match ties
    # to THIS post's messages (the D1 discriminator), not the shared label alone.
    landed: list[tuple[str, str]] = []
    for f in finals:
        actual = _actual_landing(f)
        if actual is not None:
            lfm = _read_frontmatter(actual)
            landed.append((lfm.get("to", ""), lfm.get("msg-id", "")))
    for token in recipients:
        if not _landing_matches_request(token, landed, posted_msg_ids):
            landed_labels = [lbl for lbl, _ in landed]
            problems.append(
                f"nothing landed for requested recipient {token!r} "
                f"(landed: {', '.join(landed_labels) or 'nothing'})")
    if problems:
        raise VerificationError(
            "post could NOT be verified -- "
            + "; ".join(problems)
            + ". The write path reported success, so treat the message as "
              "NOT delivered until this is resolved.")
    for final in finals:
        print(f"posted -> {final.relative_to(root).as_posix()}")
        # resolve(), not absolute(): under a Windows 8.3 short-form TEMP the two
        # are different spellings of one directory (template issue #4, item 2).
        print(f"verified -> {final.resolve()}")
    return 0


def _list_inbox(root: Path, role: str, session_id: str | None = None) -> list[Path]:
    # The enumeration choke shared by read/list/peek -- guarded FIRST so a
    # junctioned inbox is refused BEFORE any glob/read/print (the read path's
    # containment guard, mirroring ack's source guard).
    inbox = _guarded_enum_dir(root, _role_inbox_dir(root, role, session_id))
    return sorted(inbox.glob("*.md")) if inbox.is_dir() else []


def _list_read(root: Path, role: str, session_id: str | None = None) -> list[Path]:
    read_dir = _guarded_enum_dir(root, _role_read_dir(root, role, session_id))
    return sorted(read_dir.glob("*.md")) if read_dir.is_dir() else []


def cmd_list(args: argparse.Namespace) -> int:
    root = _comms_root(args)
    inbox = _list_inbox(root, args.role)
    read_count = len(_list_read(root, args.role))
    print(f"inbox for {args.role}: {len(inbox)} unread, {read_count} read")
    if not inbox:
        print("  (inbox empty)")
        return 0
    print(f"  {'posted':20} {'from':12} {'type':15} subject")
    print("  " + "-" * 70)
    for path in inbox:
        fm = _read_frontmatter(path)
        print("  {:20} {:12} {:15} {}".format(
            _ascii(fm.get("posted", "?")), _ascii(fm.get("from", "?")),
            _ascii(fm.get("type", "?")), _ascii(fm.get("subject", path.name))))
    return 0


def _print_message(path: Path) -> None:
    print("=" * 72)
    print(f"file: {_ascii(path.name)}")
    print("-" * 72)
    print(_ascii(path.read_text(encoding="utf-8").rstrip("\n")))
    print()


def cmd_read(args: argparse.Namespace) -> int:
    root = _comms_root(args)
    inbox = _list_inbox(root, args.role)
    if args.id:
        targets = [p for p in inbox if p.name == args.id]
        if not targets:
            raise MailError(
                f"no inbox message named {args.id!r} for role {args.role}")
    else:
        targets = inbox  # --all (or default): drain the whole inbox
    if not targets:
        print(f"inbox for {args.role} is empty; nothing to read.")
        return 0
    for path in targets:
        _print_message(path)
        ack_message(root, args.role, path.name)
    print(f"acked {len(targets)} message(s); moved inbox -> read.")
    return 0


def cmd_peek(args: argparse.Namespace) -> int:
    root = _comms_root(args)
    inbox = _list_inbox(root, args.role)
    if not inbox:
        print(f"inbox for {args.role} is empty.")
        return 0
    print(f"PEEK (no ack): {len(inbox)} unread for {args.role}")
    for path in inbox:
        _print_message(path)
    return 0


def _add_comms_root(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "--comms-root", default=argparse.SUPPRESS,
        help="mailbox root (default: <repo>/comms; tests pass a tmp path)")


def _add_post_arguments(p: argparse.ArgumentParser) -> None:
    """The message arguments shared by `post` and `post-verified`.

    Single-sourced so `post-verified` is a drop-in for `post` -- swapping the
    subcommand word can never silently change how the message is addressed.
    """
    _add_comms_root(p)
    p.add_argument("--from", required=True, dest="from",
                   help="sender: " + "|".join(VALID_FROM))
    p.add_argument(
        "--to", required=True,
        help="recipient(s), comma-separated: " + "|".join(VALID_TO))
    p.add_argument("--type", required=True,
                   help="message type: " + "|".join(VALID_TYPES))
    p.add_argument("--subject", required=True)
    p.add_argument("--body", default=None, help="inline body text")
    p.add_argument("--body-file", dest="body_file", default=None,
                   help="read body from this file")
    p.add_argument("--thread", default=None, help="optional thread slug")


def build_parser() -> argparse.ArgumentParser:
    parser = _AsciiArgumentParser(
        description="Inter-role file mailbox (generic harness comms core).")
    parser.add_argument(
        "--comms-root", default=None,
        help="mailbox root (default: <repo>/comms; tests pass a tmp path)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_post = sub.add_parser("post", help="post a message to recipient inbox(es)")
    _add_post_arguments(p_post)
    p_post.set_defaults(func=cmd_post)

    p_verified = sub.add_parser(
        "post-verified",
        help="post AND confirm the message landed where it was addressed")
    _add_post_arguments(p_verified)
    p_verified.add_argument(
        "--expect-root", dest="expect_root", default=None,
        help="fail BEFORE writing unless the resolved mailbox root is this "
             "directory (guards against posting into the wrong checkout)")
    p_verified.set_defaults(func=cmd_post_verified)

    p_list = sub.add_parser("list", help="list a role's inbox")
    _add_comms_root(p_list)
    p_list.add_argument("--role", required=True, help="|".join(VALID_TO))
    p_list.add_argument("--unread-only", action="store_true",
                        help="(default already lists only the inbox)")
    p_list.set_defaults(func=cmd_list)

    p_read = sub.add_parser("read", help="print + ack message(s) (inbox -> read)")
    _add_comms_root(p_read)
    p_read.add_argument("--role", required=True, help="|".join(VALID_TO))
    g = p_read.add_mutually_exclusive_group()
    g.add_argument("--all", action="store_true", help="read+ack the whole inbox")
    g.add_argument("--id", default=None, help="read+ack one message by filename")
    p_read.set_defaults(func=cmd_read)

    p_peek = sub.add_parser("peek", help="print unread WITHOUT acking")
    _add_comms_root(p_peek)
    p_peek.add_argument("--role", required=True, help="|".join(VALID_TO))
    p_peek.set_defaults(func=cmd_peek)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except MailError as exc:
        # Sanitize: the message can echo raw user input (sender/role values).
        print(f"error: {_ascii(str(exc))}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())


# --- peer-director-add checklist (NOT executed here: one director ships) ----
# Adding a SECOND peer director touches this small enumerated set; the charter
# (docs/charc-charter.md section 8) carries the generic authority/routing half.
# A sibling harness executed it once (a second director joined by following
# exactly these steps), so the checklist is known to be complete:
#
#   1. VALID_FROM / VALID_TO   -- add the new director role to both tuples.
#   2. SINGULAR_INBOX_ROLES    -- every role is singular, so add it here too
#                                 (its inbox is comms/<role>/inbox, created on
#                                 first delivery TO it by _ensure_recipient_trees
#                                 -- a post never touches an unaddressed role). This
#                                 ALSO auto-covers the UserPromptSubmit unread
#                                 notice: .claude/hooks/user_prompt_submit.py
#                                 single-sources its role set from this constant
#                                 (B-12 Gap 1), so no separate hook edit is needed.
#   3. The charter vs context -- the GENERIC peer-director contract (comms
#                                 routing + custody: a director cannot bus-reply
#                                 to a foreign role it does not own -- route via
#                                 the operator) is ALREADY in the kernel charter
#                                 (docs/charc-charter.md sections 5.1/6/8); do NOT
#                                 add a new director's INSTANCE authority there
#                                 (it stays generic + upstreamable). The new
#                                 director's instance authority goes in its own
#                                 docs/<role>-context.md instance doc (charter
#                                 section 8 item 2).
#   4. The launcher (optional) -- a launch default for the new role
#                                 (launch_role.ps1 ValidateSet + BootstrapFiles),
#                                 if it runs as a long-lived CLI session.
#   5. The mailbox UI (optional) -- the optional [web] mail UI carries the role
#                                 in its role / bus / launch / compose tuples
#                                 (the mailbox-UI script). It is import-isolated
#                                 from this core, so it is a separate touch-point.
#   6. The genericity registration -- if the director carries instance content,
#                                 register its instance docs in
#                                 tests/harness/genericity_lists.py INSTANCE_SURFACE_RELPATHS.
#
# Nothing else changes: the singular addressing model, the L1 lock, and the
# atomic write path are role-agnostic. VALID_TO carries three roles / one
# director -- no peer-director-add has been commissioned in this harness.
