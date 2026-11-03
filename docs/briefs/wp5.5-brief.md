# WP5.5 — Release preparation (dispatch brief, DRAFT for the orchestrator's fill)

**Status:** DRAFT 2026-11-03 by CHARC (generation 13), the plan's WP5.5 ("confirms the license compatibility of every bundled dependency and adds the required notices (N13), writes the installation and usage instructions, and tags the version; no installer; delivery is a repository that installs with uv"). Dispatched LAST in Phase 5, after WP5.8, WP5.7 and WP-DR25 have merged (the notices and the user guide describe the final tree). Spec v0.5.8. **Owner decisions inside the package: the version tag itself is applied by the orchestrator on the owner's word at the accept (the release checkpoint); the licence findings, if any dependency is incompatible, go to the owner through CHARC.**

| Field | Content |
|---|---|
| ID and title | WP5.5 — Release preparation: third-party notices (N13), the user guide (install and usage), the version string, and the release checklist the orchestrator executes with the owner's word |
| Lane | **CODEX**: `implementer-codex-sol-high` (documentation and a licence audit against a fixed list; one version constant; no product logic). Reviewer A = the Claude pass at the cell's seat; Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp5.5\`. |
| Tier and size | STANDARD. Size S. Codex evaluate at about 200K, STOP near 250K. |
| Base | main after WP5.8, WP5.7 and WP-DR25 accept. Worktree `.worktrees/wp5.5`, branch `wp5.5`. |
| Goal | A person with the owner's machine class (Windows 11, an NVIDIA card or none, Python absent) can clone the repository, follow `docs/user-guide.md`, and correct a photo and a GoPro clip; every third-party component the installed program uses is listed with its licence and the notice its licence requires; the GPL-2.0-or-later terms of Clearwater itself are stated with the components' compatibility; the version is `1.0.0` in the one place the code reads it. |
| Spec / decision clauses | N13 (bundled dependency licences checked for compatibility at packaging; required notices included); N1 (portability: the guide says what is Windows-only: the pipe-buffer tuning, AD-23); D91 (provenance carries the app version); 5.2 / 5.3 (what inputs are accepted and refused: the guide says so in the user's words); the GUI requirements G1-G13 (the guide walks the panels as built, WP4.3's shell). |
| Files owned | **NEW** `docs/user-guide.md`; **NEW** `THIRD_PARTY_NOTICES.md` (repo root); `README.md` (a short "Clearwater, the application" section at the top pointing to the user guide; the harness text below it stays verbatim); `src/clearwater/__init__.py` (`__version__ = "1.0.0"`); `pyproject.toml` (`version = "1.0.0"` only; no dependency change); **NEW** `docs/release-checklist.md` (the steps the orchestrator runs at the accept: gate green, tag `v1.0.0` on the merge commit on the owner's word, the tag message, the archive of the release gate logs). |
| NOT owned | `LICENSE` (GPL-2.0-or-later, in place; unchanged); `docs/underwater-correction-spec.md`; any product module but `__init__.py`'s version; the dependency list; `clearwater.local.example.toml` (read, cited). |
| Locks | No frozen interface. No dependency added or removed; if a dependency's licence is found incompatible with GPL-2.0-or-later, STOP to CHARC (an owner decision: replace, relicense or document; nothing is changed in the package). No installer, no packaged executable (CLAUDE.md). The guide names no path under the owner's home: it uses placeholders and the local-config template. |
| Markers | `tests/test_version.py` (parallel-leg): `clearwater.__version__` equals `pyproject.toml`'s version and `importlib.metadata.version("clearwater")` in the installed environment; a provenance record carries it (reuse WP4.x's provenance test fixture if present, else a unit test on `jobs/provenance.py`'s version field). |
| Hardware flags | None. The guide's "first run" walkthrough is EXERCISED once by the cell on the shipped fixture clip `tests/fixtures/video/hevc8-bt709-full.mp4` and one fixture photo through `uv run python -m clearwater` (offscreen smoke exists: cite it) and the headless tool; no footage item; no timing. |
| Out of scope | An installer or executable; a CI service; a PyPI release; signing; a changelog beyond the release notes section of the guide; the Insta360 input (ON HOLD, owner); chapter handling (v2, spec 0.5.3); any product fix found while writing the guide (STOP to CHARC with the finding; it becomes a package or a debt row). |
| Debt and decided items | At the accept CHARC writes: N13 SATISFIED (the notices file cited); the release record `docs/proofs/release-1.0.0.md` (the tag, the gate figures of record, the open debt rows carried into v1 with the owner's acknowledgement); the plan's Phase 5 CLOSED pointer; CLAUDE.md's current state. |
| Done | Plan 4.5. ruff, format, mypy clean (docs and one constant: trivially); the version test green; the two-leg gate green on the final candidate (the release gate: its logs are the figures of record for 1.0.0); the guide exercised once as written; every dependency in the audit table has a licence, a source URL and a verdict; Reviewer A converged; Reviewer B clean or its single remediation done. |

## The licence audit (N13): the fixed list

The installed program uses, directly or through the listed packages, at least the following; the cell verifies each licence from the installed distribution's metadata (`importlib.metadata`) and the project's own licence file, records the version pinned by `uv.lock`, and states the compatibility with GPL-2.0-or-later and the notice required:

| Component | How it is used | Expected licence (the cell VERIFIES; this column is CHARC's recollection, not a finding) |
|---|---|---|
| Python 3.12 | runtime | PSF-2.0 |
| numpy, scipy | arrays, filters | BSD-3-Clause |
| Pillow | photo I/O | MIT-CMU (HPND) |
| pillow-heif and its bundled libheif, libde265 (and x265 if bundled in the wheel) | HEIC decode | pillow-heif BSD-3; libheif LGPL-3.0; libde265 LGPL-3.0; x265 GPL-2.0 (check whether the installed wheel bundles an encoder at all; HEIC is read, never written) |
| tifffile | TIFF | BSD-3-Clause |
| pyside6-essentials (Qt 6) | the GUI | LGPL-3.0 (also offered under GPL-2.0 / GPL-3.0); the notice must say which terms Clearwater relies on and that Qt is dynamically linked |
| cupy-cuda12x (optional `gpu` extra) with the CUDA runtime it bundles (`[ctk]`) | the device backend | CuPy MIT; the NVIDIA CUDA runtime libraries under NVIDIA's EULA (redistributable components): state that the EULA permits redistribution of the runtime but is not GPL-compatible as a combined work, and that CuPy is an OPTIONAL extra the user installs, so Clearwater does not bundle it (the system-library / optional-component position; the cell quotes the clause, CHARC and the owner judge) |
| FFmpeg (`ffmpeg`, `ffprobe`; the gyan.dev "full" build at WP0.1, 9.0.2) | decode, encode, mux, run as a separate process | GPL-3.0 (the full build includes GPL components; a user may substitute any build with hevc_nvenc / libx265); NOT bundled: the guide tells the user to install it and names the build tested; the notice says the program invokes it as a separate process |
| The dev / comms groups (pytest, ruff, mypy, fastapi, ...) | development only | listed in a separate "not part of the installed program" table, licences recorded, no notice required in the program |

Verdict form per row: COMPATIBLE (and the notice text), COMPATIBLE-WITH-CONDITION (state it: e.g. LGPL dynamic linking, the EULA position), or INCOMPATIBLE (= STOP). The notices file carries each component's copyright line and licence text pointer as its licence requires; GPL-2.0-or-later for Clearwater's own code with the "or later" stated so the GPL-3.0 FFmpeg combination is addressed (FFmpeg runs as a separate process in any case: say so).

## The user guide (`docs/user-guide.md`): the fixed outline

1. What Clearwater does and does not do (one paragraph; the spec's 1-2 in plain words; visual quality, not physically exact colour; what inputs: iPhone HEIC / JPG photos, GoPro and iPhone `.mp4` / `.mov` HEVC or H.264 video; what is refused: HLG / Dolby Vision transfers, spec 5.3, with the message the program shows).
2. Install: uv; `git clone`; `uv sync` (and `uv sync --extra gpu` for an NVIDIA card: the CUDA 12 driver requirement); FFmpeg (the build tested, where to put it, how the program finds it: the local-config template `clearwater.local.example.toml`, copied to `clearwater.local.toml`); the first-run environment report (`tools/environment_report.py`, WP0.1) and what it should say.
3. First run: `uv run python -m clearwater`; the panels in the order a user meets them (open, preview, the Basic panel with the 6.7 controls in the program's own labels, presets, export with the output naming rule D36 / D25, the batch panel); what the progress and cancel do (G8 / D44: cancel leaves nothing behind); where outputs go (beside the source, the `_corrected` suffix, settable).
4. Video: what the analysis pass does and how long it takes (N6's figure in the user's terms: about 12 minutes of processing per minute of 4K footage on a laptop like the owner's, GPU; the CPU route is many times slower and the program says so); the proxy cache (D71) and its limit setting; 10-bit output (D76); the quality presets (D75).
5. Photos: HEIC orientation and colour handling in one paragraph (AD-24: the result matches the phone's own view); 16-bit PNG and the ICC profile (D22 / D53); EXIF carried (WP4.5).
6. When something goes wrong: the messages the program shows and what they mean (refused inputs, the encoder stopped / stopped accepting frames (WP5.8), disk-space refusals, the leftover clean-up at start, D85); the log location (`config/log.py`); what to send when reporting a problem (no file paths with personal folders; the provenance record).
7. Known limitations in v1 (from the register's open rows that touch a user: DR-114 WDDM memory reporting, DR-115 intermittent encoder stall now bounded by the watchdog, DR-117 halos on high-contrast edges and its status, chapter handling deferred, Insta360 not supported, no `.LRV` proxies).
8. Licence (one paragraph pointing to `LICENSE` and `THIRD_PARTY_NOTICES.md`).

The guide is written for the owner's reading level as a camera user, not a developer; every command is in a fenced block; no claim about speed or quality beyond the figures of record (cite the report for each).

## Questions (CHARC's recommended answers)

- **Q1 version.** Recommended: `1.0.0` (the first release the owner can use end to end; the spec's milestone 6). The tag `v1.0.0` is applied by the orchestrator at the accept on the owner's word, never by the cell.
- **Q2 CuPy / CUDA position.** Recommended: optional extra, not bundled, the EULA quoted, the position stated; no change to how it is installed. An INCOMPATIBLE verdict is a STOP, not a cell decision.
- **Q3 README.** Recommended: add a short application section at the top of the existing README (the repository is both the program and the harness instance); do not remove or rewrite the harness text (the template lineage reads it).

## Completion report (`docs/reports/wp5.5-release-prep.md`)

The audit table with verdicts and the evidence per row (metadata, licence file, URL); what the notices file contains; the guide's exercised walkthrough (commands run, what appeared); the version test; the release checklist as written; limits (one machine class exercised; FFmpeg build substitution untested beyond the one build).

## Yields and depth

Turn 1 = round 0 (the audit table skeleton with the installed versions and licences read from metadata, any INCOMPATIBLE or unclear row = STOP; the guide outline confirmed against the shell as built) and YIELD; turn 2 = the notices, the guide, the version, the test, the walkthrough, committed, YIELD for Reviewer A; the report; the nets.

## Orchestrator dispatch fill (for CHARC to finalise)

- Lane paces at dispatch; base commit (after WP5.8, WP5.7 and WP-DR25); worktree; evidence folder.
- GATE_CHECKS: the FULL three-leg gate (parallel, serial, fullclip) plus the harness gate on the final candidate: this is the release gate, and its logs are the figures of record for 1.0.0 (archive them to `clearwater-review-evidence\release-1.0.0\`).
- At the accept: the owner's word for the tag ("tag 1.0.0" in chat to CHARC), then `git tag -a v1.0.0 <merge commit> -m "Clearwater 1.0.0"`; CHARC writes `docs/proofs/release-1.0.0.md`.
