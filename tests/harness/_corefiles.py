"""The CORE module set whose stdlib-only posture the dependency test enforces.

The core comms/registry/hook surface MUST run with zero third-party packages
available (pyproject declares no hard runtime deps). This list names the core
files by repo-relative path. The optional UI (scripts/comms_ui.py) is NOT here
-- it is the `[web]` extra and is import-isolated from the core.

The role-recovery store + shared hook helpers live INSIDE user_prompt_submit.py
(ARC-8 folded them there when session_start.py/session_end.py were deleted with
the per-generation registry). The dependency test only checks the files in this
list that actually EXIST, so the list is correct whether a given file has
shipped yet.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# Repo-relative paths of the stdlib-only core. This is the reusable CORE whose
# stdlib-only posture the dependency test enforces (the template itself stays
# dependency-light). The germination INSTANCE surface (the project's own code:
# the domain implementer cells, a filled APPLICATION, peer-director docs --
# genericity_lists.is_instance_surface) imports third-party FREELY and is
# DELIBERATELY not listed here: the stdlib-only constraint is a property of the
# template, NOT a constraint on the consumed implementation (B-9 operator
# refinement). So the dependency-posture ban is CORE-scoped by construction --
# no instance-surface path ever appears in CORE_RELPATHS.
CORE_RELPATHS = (
    "scripts/role_mail.py",
    ".claude/hooks/user_prompt_submit.py",
    ".claude/hooks/stop.py",
    # The dispatcher's depth instrument (2026-09-07): also core, also
    # required to stay stdlib-only (its own docstring says so), so it gets
    # the SAME mechanized guard rather than staying true only by inspection.
    "scripts/cell_depth.py",
    # The dual-model implementer lane (2026-10-27): readouts + the Codex cell
    # driver, all stdlib-only by design (they run at a bare seat).
    "scripts/usage_codex.py",
    "scripts/usage_claude.py",
    "scripts/codex_cell.py",
)


def existing_core_files() -> list[Path]:
    """Absolute paths of the core files that currently exist on disk."""
    return [REPO_ROOT / rel for rel in CORE_RELPATHS
            if (REPO_ROOT / rel).is_file()]
