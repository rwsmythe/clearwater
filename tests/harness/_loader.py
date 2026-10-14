"""Load scripts/ + hook modules by path (the scaffold's scripts/ is not a pkg).

The comms tooling lives under scripts/ and .claude/hooks/ and is run directly,
not imported as a package. Tests load the modules by file path the same way the
production callers (the UI, the hooks importing each other) do.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load_module(name: str, relpath: str):
    """Import a module by name from a repo-relative path (re-exec each call)."""
    path = REPO_ROOT / relpath
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod  # so sibling imports (from session_start import ...) resolve
    spec.loader.exec_module(mod)
    return mod


def load_role_mail():
    return load_module("role_mail", "scripts/role_mail.py")


def load_cell_depth():
    return load_module("cell_depth", "scripts/cell_depth.py")


def load_ruling_review():
    return load_module("ruling_review", "scripts/ruling_review.py")


def load_user_prompt_submit():
    # ARC-8: the role-recovery store + the shared hook helpers live in this hook
    # now (session_start.py / session_end.py were deleted). stop.py imports it by
    # bare name, so keep the hooks dir on sys.path.
    hooks_dir = REPO_ROOT / ".claude" / "hooks"
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))
    return load_module("user_prompt_submit", ".claude/hooks/user_prompt_submit.py")
