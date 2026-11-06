<!-- SEAM 1: APPLICATION DEFINITION (filled at bootstrap, 2026-10-14) -->

# Application: Clearwater

## What the project does

Clearwater is a Windows desktop tool (Python, PySide6)
that corrects color cast, contrast loss and haze in amateur underwater photos
(iPhone) and video (GoPro). It applies the Ancuti color-balance-and-fusion method
with two selectable channel-compensation schemes, handles video flicker by
analyzing and temporally smoothing whole-frame statistics before rendering, and
exports PNG photos and HEVC MP4 video with timing, audio and orientation
preserved. Visual quality is the goal, not physically exact color.

## The source of truth

The application is specified, not invented here:

1. `docs/clearwater-implementation-plan.md` (v1.0) -- how the work is organized:
   roles, working rules, the work packages WP0.1 onward, owner checkpoints CP1-CP5,
   the interfaces to freeze (IF-1..IF-10), the module map.
2. `docs/underwater-correction-spec.md` (v0.5) -- WHAT Clearwater does. Decisions
   D1-D117, acceptance tests V1-V18, GUI requirements G1-G13, non-functional
   requirements N1-N13. **If the plan and the spec disagree, the spec wins** and the
   disagreement goes to the owner.
3. `docs/underwater-imagery-correction-research.md` -- background on the method
   family; not normative.

`CLAUDE.md` is the agent-facing entry point (conventions, current state, the next
task). Everything below summarizes those documents for the harness; they govern.

## Domain

- **Entities:** photos (HEIC, JPEG, PNG, TIFF), video clips (MP4; HEVC or H.264;
  8- or 10-bit; constant or variable frame rate), GoPro chaptered recordings and
  their `.LRV`/`.THM` sidecars, parameter sets and presets, per-frame whole-frame
  statistics (raw and smoothed), a proxy cache, export jobs and batches.
- **Substrate:** the owner's Windows 11 laptop with an NVIDIA graphics card and
  32 GB RAM (CPU and card model are read from the machine in WP0.1). Python 3.12
  under uv. A read-only footage folder and a separate working folder, both outside
  version control.
- **Pipeline (per image or frame):** channel compensation (Ancuti 2018 red and
  optional blue, or 3C) -> gray-world white balance with a gain clamp -> two fusion
  inputs (gamma, sharpened) -> three weight maps -> multiscale Laplacian fusion.
  All in 32-bit float, spatial parameters relative to the short side.

## Success criteria

- **Milestones** (spec section 13 / plan section 6): footage inventory -> prototype
  gate (six recorded results, V14) -> core pipeline on CPU and GPU (V1, V9) ->
  video analysis, smoothing, cache and I/O fidelity (V3, V4, V15-V17) -> GUI,
  presets, batch, settings -> verification against V2-V18.
- **"Good" for the owner:** the corrected result is preferred over the original on
  at least 80 percent of the owner's test set with no obvious artifacts (V2, D65),
  flicker with smoothing is at most 25 percent of the unsmoothed baseline on the
  synthetic clip (V3), export runs at about 3.3 minutes of processing per minute of
  4K footage end to end (N6, tunable after measurement), and peak RAM stays at or
  below 16 GB (N4).
- **"Done" for a work package** is the plan's definition of done (section 4.5):
  scope met within the owned files with frozen interfaces unchanged; Google-style
  docstrings on every public function, class and module; `ruff check`,
  `ruff format --check`, `mypy` and `pytest` green; the owner's verification loop
  run until a full pass finds nothing new (suspect -> confirm independently -> fix
  -> repeat); no assumptions where the brief or spec is ambiguous (stop and ask); a
  completion report; and an independent review by an implementer who did not write
  the package.

## Constraints and invariants (never violate)

- **The footage folder is read-only.** No package writes, renames or deletes
  anything in it. All outputs, caches, extracted frames and reports go to the
  working folder, which is outside the footage folder and outside version control.
  Both paths come from a local configuration file that is not committed. The
  owner's footage is never committed.
- **Owner-reserved decisions** (plan section 3): footage categories, the look check
  and the V2 visual review, scope decisions (chapter handling, gain caps, anything
  relaxing a mandatory requirement), and any change to the spec. Nobody else
  decides these; the harness routes them to the operator as `decision_request`.
- **Frozen interfaces** change only by the chief architect's logged decision.
  `core` and `methods` import nothing from `io`, `jobs` or `gui`; `gui` and `jobs`
  reach correction methods only through IF-3.
- **Dependencies** are added only through `pyproject.toml` and the uv lock file,
  only by the package whose brief allows it, and only once the architecture document
  names them (license check, N13; Clearwater is GPL-2.0-or-later).
- **Portability:** no OS-specific code without the architect's approval (N1).
- **Hardware rule:** a package that records a timing or memory figure is
  exclusive -- one at a time, nothing else heavy running, timed on a full clip.
- **Only the orchestrator merges to main.** Implementers work in worktrees and
  change only the files their brief owns.
- **Distribution (from 1.1.0):** a PyInstaller one-folder Windows build and a
  tag-driven GitHub Actions release workflow that drafts a release the owner
  publishes (`docs/release-checklist.md`). No installer, no signing. The test
  gate still runs on the laptop.

## Harness-to-plan role mapping

| Plan role (section 3) | Harness role |
|---|---|
| Owner | operator (the only `decision_request` recipient) |
| Chief architect | CHARC (the director) |
| Orchestrator | orchestrator generation |
| Implementer / independent reviewer | implementer cells (`.claude/agents/implementer-*.md`) |

The application's own toolchain, run from the repo root with the uv environment
(`uv sync` creates it): `uv run pytest` (markers `gpu`, `footage`, `gui`, `slow`;
footage-marked tests skip when the footage path is absent), `uv run ruff check .`,
`uv run ruff format --check .`, `uv run mypy`. The harness's own suite is separate:
`uv run python -m unittest discover -s tests/harness`.
