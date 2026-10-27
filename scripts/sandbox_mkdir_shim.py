"""Pytest plugin for a sandboxed implementer cell whose restricted token cannot read 0o700 dirs.

Python 3.12.4+ on Windows turns ``os.mkdir(path, 0o700)`` into an owner-only ACL. Under the
Codex unelevated sandbox's restricted token that ACL denies the sandbox's own ``listdir``, so
pytest's ``tmp_path_factory`` (which creates its basetemp and numbered directories with mode
0o700) fails at session finish with ``PermissionError [WinError 5]`` and every ``tmp_path``
fixture errors (found by orchestrator gen 13 on WP3.20R turn 1, 2026-10-27).

The shim maps mode 0o700 to 0o777 in ``os.mkdir`` so the directory inherits its parent's ACL.
It changes nothing else. It is loaded ONLY by a sandboxed cell's own test runs::

    PYTHONPATH=scripts uv run pytest ... -p sandbox_mkdir_shim -p no:cacheprovider

Gate runs at the orchestrator's seat and CHARC QA never load it. Stdlib only; application
agnostic (harness core).
"""

from __future__ import annotations

import os

_real_mkdir = os.mkdir


def _mkdir(
    path: str | bytes | os.PathLike[str] | os.PathLike[bytes],
    mode: int = 0o777,
    *,
    dir_fd: int | None = None,
) -> None:
    """``os.mkdir`` with mode 0o700 widened to 0o777; every other call unchanged."""
    if mode == 0o700:
        mode = 0o777
    _real_mkdir(path, mode, dir_fd=dir_fd)


os.mkdir = _mkdir
