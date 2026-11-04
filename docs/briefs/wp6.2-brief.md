# WP6.2 — Portability audit (code only, no Mac): the macOS change list (dispatch brief, DRAFT)

**Status:** DRAFT 2026-11-04 by CHARC (generation 14) on the owner's Phase 6 ruling (`docs/briefs/phase6-proposal.md`, D-E arm64 CPU path with VideoToolbox). The orchestrator fills the dispatch section; CHARC marks it FINAL. A read-and-report package: it changes no product file. Owner decisions inside the package: none.

| Field | Content |
|---|---|
| ID and title | WP6.2 — Portability audit: every site in `src/clearwater`, `tools/` and `tests/` that assumes Windows, with the macOS (Apple Silicon, CPU path) change for each, as a file-by-file table WP6.4 implements |
| Lane | **CODEX** (`implementer-codex-sol-high`): a well-specified read against a fixed checklist. Reviewer A = Claude at the cell's seat; Reviewer B = Claude at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp6.2\`. |
| Tier and size | STANDARD. Size S (one report). Evaluate at about 200K, STOP near 250K. |
| Base | main at dispatch. Worktree `.worktrees/wp6.2`, branch `wp6.2`. Nothing heavy; may run beside WP6.1's non-timing turns and WP-T8. |
| Goal | WP6.4 can be briefed from this report alone: for each site, the file and line, what it assumes, the macOS behaviour today (works / fails / untested), the change (a per-platform branch, a portable replacement, or a new leg), the test that will pin it on Windows (platform-parameterised) and the test that needs a Mac (`macos` marker). |
| Sources | `src/clearwater/` (32,720 lines; the 9 known conditional sites: `io/video/pipes.py` (the 32 MiB decoder pipe raises on any platform but Windows, AD-23; `CREATE_NO_WINDOW`), `config/paths.py` (the `win32` branch), `core/memory.py`, `io/video/capability.py` and `encode.py` (`hevc_nvenc` / `libx265` only)); `tools/environment_report.py`; `tests/` (temp roots, path separators, case-sensitive file systems, the footage guard); `scripts/launch_role.ps1` and the harness are OUT (harness portability is a harness item, not this package's); `docs/architecture.md` AD-23, AD-31, AD-12 (rate rules); spec v0.6.0 N1, N14. |
| Files owned | `docs/reports/wp6.2-portability-audit.md` ONLY. |
| NOT owned | Every product, tool and test file (a read-only package: any edit = STOP); the spec; the architecture document (CHARC adds the AD rows WP6.4 needs from this report). |
| Locks | READ-ONLY on the repository. Grep results quoted with file and line; every claim about macOS behaviour labelled from documentation (with the source) or from reasoning, never as tested (no Mac in this package). No application vocabulary added to the harness lists. |
| Markers | None (no tests). |
| Hardware flags | None. |
| Out of scope | Implementing anything; the Metal backend (one paragraph of the report names what it would take, as information); Intel Macs; signing / notarisation; the GPU pack (Windows-only by N14). |
| Debt and decided items | At the accept CHARC writes the AD rows for the VideoToolbox leg and the per-platform pipe strategy from the report's recommendation, and the WP6.4 brief. Pre-existing portability defects found outside the listed sites become DR rows. |
| Done | The table covers every `sys.platform` / `os.name` / `platform.system()` / Windows-API / drive-letter / backslash / `CREATE_NO_WINDOW` / `%APPDATA%`-class site in `src`, `tools` and `tests` (grep commands recorded, counts stated); the encoder section specifies the VideoToolbox leg (probe command, the quality control it offers and the rate rule mapping from AD-12's NVENC `-cq` ceiling, the container tags V4 checks, pixel formats, 10-bit support, the HLG / PQ refusal unchanged); the paths section specifies the macOS config / cache / journal folders; the process section specifies the spawn flags and the pipe strategy (a portable fallback exists per AD-23: measure nothing, cite WP2.1S's figures and state what a Mac measurement would show); the packaging section lists what PyInstaller needs on macOS (app bundle, `Info.plist`, Qt plugin paths, the unsigned-app step); the test plan names each platform-parameterised test and each `macos`-marked test; Reviewer A converged; Reviewer B clean. |

## The checklist (fixed)

1. Platform conditionals and Windows-only APIs (`subprocess` flags, `msvcrt`, `ctypes.windll`, pipe sizing).
2. File-system assumptions: case sensitivity (`.MP4` vs `.mp4` fixtures exist in the tree for this reason: state how discovery behaves on a case-sensitive volume), path separators, drive letters, reserved names, `%LOCALAPPDATA%` / `%TEMP%`.
3. The encoder model: today's two encoders, the capability probe's string matching on FFmpeg's stderr, the rate rules; the VideoToolbox leg's specification.
4. The decoder and container paths: `ffprobe` tags that are platform-neutral; anything that reads a Windows-built FFmpeg's wording.
5. Memory and device probing (`core/memory.py`, D111's estimate on a machine without CUDA).
6. The GUI: menu bar placement, the file dialogs, high-DPI, the `offscreen` platform for tests.
7. Tests: markers, temp roots, the footage guard's path comparison, fixtures with upper / lower case names, anything calling `where` / PowerShell.
8. Tools: `environment_report.py` (what it should report on macOS), `inventory.py`, the headless runner.
9. Packaging on macOS (information for WP6.5).

## Questions (CHARC's recommended answers)

- **Q1 VideoToolbox quality control.** Recommended: FFmpeg's `hevc_videotoolbox` has no constant-quality mode equivalent to `-cq` on every macOS version; specify `-q:v` where available and a bitrate ceiling from the same pixel-rate rule as NVENC's as the fallback, with the choice to be measured in WP6.5 on the Mac. The report states both and does not pick.
- **Q2 The pipe.** Recommended: the portable fallback (the OS default pipe) is the macOS strategy for 1.2.0; a larger pipe on macOS is a later measurement.
- **Q3 Case sensitivity.** Recommended: the inventory and discovery treat extensions case-insensitively by lower-casing the suffix (state whether they already do, with the line).

## Completion report (`docs/reports/wp6.2-portability-audit.md`)

The table; the encoder, paths, process, GUI, tests, tools and packaging sections; the grep record; limits (no Mac; documentation-sourced claims marked).

## Yields and depth

Turn 1 = round 0 (the grep record and the table's skeleton; any site that is a product defect today = STOP) and YIELD; turn 2 = the full report, YIELD for Reviewer A; the nets.

## Orchestrator dispatch fill (for CHARC to finalise)

- Lane paces at dispatch; base commit; worktree; evidence folder.
- GATE_CHECKS: `git diff --name-only main` = the report only; 0 CR; no pytest leg (no code change); the harness suite if any harness file is touched (it must not be).

## Dispatch fill (orchestrator gen 40, 2026-11-04 ~08:25Z)

This section fills the one above. Where it differs, it governs once CHARC marks it FINAL. Corrections are marked **[corr]**.

- **Base, worktree and evidence.**
  - Base = main at dispatch (`dadf3013` or later, with CHARC's FINAL).
  - Worktree `.worktrees/wp6.2`, branch `wp6.2`. No `clearwater.local.toml`: the package reads no footage.
  - Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp6.2\` (`cell\`, `A\`, `B\`).
- **Lane paces at 08:17Z.** Codex 23 % / 0.233 (resets 10:07Z); Claude 22 % / 0.799.
  - CODEX lane as briefed (`implementer-codex-sol-high`, a FRESH session).
  - Reviewer A = a Claude pass at my seat (`scripts/codex_cell.py review`); Reviewer B = a Claude pass at my seat.
- **[corr] Scheduling: one Codex cell at a time** (CLAUDE.md: "ONE Codex cell"). WP6.2 and WP-T8 are both on the Codex lane, so they run in sequence, not beside each other.
  - **WP6.2 goes first:** it is read-only and short, and it runs beside WP6.1's round 0 and build turns.
  - WP-T8 follows when WP6.2 has yielded for its nets.
  - WP6.2 may run during a WP6.1 timing window, since it reads only. Its cell runs no pytest and no build, and I hold its turns if a window needs the CPU quiet.
- **[corr] The "9 known conditional sites" were checked at the seat** (`grep -rnE "sys\.platform|os\.name|platform\.system\(|CREATE_NO_WINDOW|msvcrt|windll|LOCALAPPDATA|APPDATA" src/clearwater`): 13 lines, in TWO files, `config/paths.py` and `io/video/pipes.py`.
  - `core/memory.py`, `io/video/capability.py` and `encode.py` hold Windows / NVIDIA ASSUMPTIONS (device memory, the `hevc_nvenc` / `libx265` pair, stderr wording) rather than platform conditionals.
  - The audit covers both classes and counts them separately. In `tools/` and `tests/` the wider pattern (with `powershell`, `where`) matches 109 files at a first pass; round 0 refines the pattern and states the exact command and count.
- **Read-only, enforced.** `git status --porcelain` is empty except the report, at every yield.
- **Turns.**
  - Turn 1 = round 0: the grep record with exact commands and counts, the table's skeleton, and Q1-Q3. Any site that is a product defect TODAY on Windows = STOP. YIELD.
  - Turn 2 = the full report. I commit it. YIELD for Reviewer A.
  - Then the nets.
  - Depth: evaluate at about 200K, STOP near 250K.
- **GATE_CHECKS:**
  - `git diff --name-only main...wp6.2` = `docs/reports/wp6.2-portability-audit.md` only;
  - 0 CR;
  - the harness suite, once, because a new `docs/` file sits under `docs/reports/`, which is already instance surface: confirm no registration is needed;
  - no pytest leg.
