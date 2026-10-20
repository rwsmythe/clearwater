"""Generate the shared test fixtures and their manifest (WP2.3).

Usage::

    uv run python tools/fixtures/generate.py --out DIR [--generated-out DIR] [--group NAME ...]

Writes the committed samples (stills, dummy files, video clips, the flicker mask) under ``--out``
and the generated ones (the flicker clip, too large to commit) under ``--generated-out``
(default: ``--out``). Without ``--group`` every group is built and ``DIR/manifest.json`` is
written; with ``--group`` only the named groups (``stills``, ``files``, ``video``,
``flicker``) are built and no manifest is written. The repository's committed fixtures are made
with ``--out tests/fixtures --generated-out work/fixtures/generated``.

Every write goes through ``spike_io.guard.WriteGuard`` rooted at the output folder, so nothing is
written outside it. The generators read no owner file: they take no input path at all.

Exit status 0 on success; 2, with a one-line ``error: ...`` on standard error, when a sample
cannot be built (FFmpeg missing or failing, or a written file not what its spec says).
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

if not __package__:
    # Script mode: sys.path[0] is tools/fixtures; put tools first for the sibling packages.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from fixtures import files, flicker, manifest, stills, video
from spike_io.guard import OutputRefusedError, WriteGuard

GROUP_NAMES = ("stills", "files", "video", "flicker")
"""The groups, in build order."""


def _guard(root: Path) -> tuple[WriteGuard, Path]:
    """Create ``root`` and return a guard rooted at its resolved path, and that path."""
    root.mkdir(parents=True, exist_ok=True)
    resolved = root.resolve()
    return WriteGuard(root=resolved), resolved


def generate(
    out: Path, generated_out: Path | None = None, groups: Sequence[str] = GROUP_NAMES
) -> dict[str, Any] | None:
    """Build the named groups of samples.

    Args:
        out: The folder for the committed samples (and ``manifest.json``).
        generated_out: The folder for the generated samples; ``out`` when None.
        groups: The groups to build, from :data:`GROUP_NAMES`.

    Returns:
        The manifest when every group was built (it is also written to ``out``); None otherwise.

    Raises:
        ValueError: An unknown group name.
        video.GenerationError: A sample could not be built, or the manifest is invalid.
    """
    unknown = [name for name in groups if name not in GROUP_NAMES]
    if unknown:
        raise ValueError(f"unknown group {unknown[0]!r}; choose from {', '.join(GROUP_NAMES)}")
    guard, root = _guard(out)
    gen_guard, gen_root = (guard, root) if generated_out is None else _guard(generated_out)
    entries: list[manifest.Entry] = []
    if "stills" in groups:
        entries += stills.build(guard, root)
    if "files" in groups:
        entries += files.build(guard, root)
    if "video" in groups:
        entries += video.build(guard, root)
    if "flicker" in groups:
        entries.append(flicker.build_mask(guard, root))
        entries.append(flicker.build_clip(gen_guard, gen_root))
    if set(groups) != set(GROUP_NAMES):
        return None
    result = manifest.build(entries, stills.OMITTED)
    problems = manifest.validate(result)
    if problems:
        raise video.GenerationError("the manifest is invalid: " + "; ".join(problems))
    target = guard.check(root / "manifest.json")
    target.write_text(json.dumps(result, indent=2) + "\n", encoding="ascii", newline="\n")
    return result


def main(argv: Sequence[str] | None = None) -> int:
    """Run the generator from the command line (see the module docstring).

    Args:
        argv: The arguments; ``sys.argv[1:]`` when None.

    Returns:
        The exit status.
    """
    parser = argparse.ArgumentParser(description="Generate the Clearwater test fixtures.")
    parser.add_argument("--out", type=Path, required=True, help="folder for the committed samples")
    parser.add_argument("--generated-out", type=Path, help="folder for the generated samples")
    parser.add_argument(
        "--group", action="append", choices=GROUP_NAMES, help="build only this group (repeatable)"
    )
    args = parser.parse_args(argv)
    try:
        generate(args.out, args.generated_out, tuple(args.group) if args.group else GROUP_NAMES)
    except (video.GenerationError, OutputRefusedError, OSError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
