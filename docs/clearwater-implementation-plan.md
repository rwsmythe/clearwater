# Clearwater — Implementation Plan

**Version:** 1.2 (draft) -- amended 2026-10-20 for spec v0.5.4 (Gate 1 option C: WP3.21 optimisation package; recording-group suffix removed from WP3.13); 1.1 amended 2026-10-19 for spec v0.5.3 (chapter handling deferred to v2; 3C default)
**Date:** 13 October 2026
**Built on:** Specification v0.5 (`underwater-correction-spec.md`)
**Status:** Ready for owner review. Both inputs the plan left open are CLOSED: the laptop's CPU and graphics card (WP0.1, 2026-10-14) and chapter handling (CP1, 2026-10-19: deferred to v2, spec v0.5.3).

---

## 1. How to use this plan

- **The specification is the source of truth for what Clearwater does.** This plan says how the work is organized. If the two disagree, the spec wins and the disagreement is raised to the chief architect.
- **Readers:**
  - the **owner** needs Sections 2, 5 and 10;
  - the **chief architect** needs all of it;
  - the **orchestrator** needs Sections 3, 4, 6, 7 and 11;
  - an **implementer** needs Section 4 and the brief for its own work package.
- **Design depth:** this plan fixes module boundaries and names each interface that must be frozen. Interface signatures and library choices are made by the chief architect after the prototype gate, because the gate's measurements decide them.
- References such as D97, V3, N5 and G4 point to the spec. References such as WP3.2, IF-3 and CP2 point to this plan.

---

## 2. Planning inputs

Settled with the owner on 13 October 2026.

| # | Input | Setting |
|---|---|---|
| PD1 | Who implements | Multi-agent framework: a chief architect directs an orchestrator, which uses multiple generic implementers |
| PD2 | Work-package format | None imposed by the framework; defined in Section 4.6 |
| PD3 | Design depth | Module boundaries and named interfaces now; signatures and library choices after the gate |
| PD4 | Owner checkpoints | Footage sorting, look check, scope decisions, design-freeze review, V2 visual review |
| PD5 | Architect's authority | All other technical decisions, each logged with its evidence; reviewed by the owner once, at the design freeze |
| PD6 | Where agents run | On the owner's laptop, with direct access to the graphics card and the footage folder |
| PD7 | Isolation | The orchestrator isolates implementers in git worktrees |
| PD8 | Repository | Created as the first step: local repository plus a private GitHub repository |
| PD9 | Tooling | uv with a lock file, Python 3.12 (verified at the gate), pytest, ruff, mypy, Google-style docstrings |
| PD10 | Layout | `src/clearwater/`, `tests/`, `tools/`, `docs/` |
| PD11 | Performance target machine | The owner's laptop only; no minimum specification for other users |

---

## 3. Roles and authority

| Role | Responsibilities | May decide |
|---|---|---|
| **Owner** | Sorts footage, judges the look, approves scope and spec changes, reviews the design freeze, performs the V2 review | Anything; the only role that may change the spec or relax a mandatory requirement |
| **Chief architect** | Owns the design: architecture document, interface signatures, library choices, defaults and tolerances, the decision log, the gate report | All technical decisions not reserved to the owner |
| **Orchestrator** | Schedules work packages from the dependency graph, creates worktrees, assigns implementers and reviewers, enforces the graphics-card rule, merges completed packages | Scheduling and assignment only |
| **Implementer** | Executes one work package from its brief; or reviews one it did not write | Implementation detail inside its owned files |

**Reserved to the owner (PD4):**
- Which clips belong to which footage category.
- The look check and the V2 visual review.
- Scope decisions: whether chapter handling stays in v1, whether the gain caps are kept or dropped, and anything that would relax a mandatory requirement (for example the export target N6 or timing fidelity D94, D105).
- Any change to the spec.

**Integration.** The orchestrator is the only role that merges to the main branch. Integration code is written by implementers under the Phase 4 work packages.

---

## 4. Working rules

These apply to every work package.

### 4.1 Repository and environment
- One repository; the main branch always passes lint, type checks and the non-hardware tests.
- Dependencies are added only through `pyproject.toml` and the uv lock file, and only by the package whose brief says it may. A new dependency not named in the architecture document needs the architect's approval, because of the license check (N13).
- The spec, this plan, the architecture document, the decision log and the gate report live in `docs/`.
- Code is kept portable: nothing specific to one operating system without the architect's approval (N1, D29).
- **No CI service is included.** Checks run on the laptop. Raise it with the owner if a hosted check is wanted.

### 4.2 Footage and working files
- The footage folder is **read-only**. No package writes, renames or deletes anything in it.
- All outputs, caches, extracted frames and reports go to a separate working folder outside the footage folder and outside version control.
- Both paths are read from a local configuration file that is not committed.
- The owner's footage is never committed. Tests that need it are marked `footage` and skipped when the path is absent.
- Test material that the project generates itself (WP2.3) is produced by scripts; large generated files are not committed.

### 4.3 Graphics card rule
- Any package that records a timing or a memory figure is flagged **exclusive**.
- The orchestrator runs exclusive measurements one at a time, with no other heavy job running, so parallel work does not distort the results.
- Timings are taken on a full clip, not one frame, because sustained speed on a laptop may fall under heat.

### 4.4 File ownership
- Each brief lists the files and folders the package owns. An implementer changes only those.
- A change needed in another package's files, or in a frozen interface, is raised to the orchestrator and decided by the architect.

### 4.5 Definition of done
A package is done when all of the following hold.

1. **Scope:** the brief's requirements and its listed spec clauses are met, within the owned files, with the frozen interfaces unchanged.
2. **Documentation:** every public function, class and module has a Google-style docstring. Comments are checked against the code they describe and corrected where they differ.
3. **Checks:** `ruff check`, `ruff format --check`, `mypy` and `pytest` pass. Hardware-marked tests are run on the laptop when the brief requires them.
4. **Verification loop** (the owner's standing rule):
   1. review the work against the brief and the spec clauses, looking for logical faults and unmet requirements;
   2. for each suspected issue, confirm independently that it is real, by reproducing it with a test or tracing the code, before changing anything;
   3. fix confirmed issues;
   4. repeat from step 1 until a complete pass finds nothing new.
5. **No assumptions:** where the brief or the spec is ambiguous, the implementer stops and raises the question. It does not guess.
6. **Completion report:** what was built, test results, the verification loop record (issues suspected, confirmed, rejected as false positives, fixed), any deviations, and open questions.
7. **Independent review:** an implementer who did not write the package reviews it against the brief and the spec, not against the author's report. Findings go back through step 4.

### 4.6 Work-package brief format
The architect and orchestrator issue each package as a self-contained brief. Implementers start with no project knowledge, so the brief carries everything they need.

| Field | Content |
|---|---|
| ID and title | As in Section 6 |
| Goal | One or two sentences |
| Spec clauses | The sections and decision, test and requirement numbers that apply, quoted or linked |
| Files owned | Paths the package may create or change |
| Interfaces consumed | Which frozen interfaces it calls, with their signatures |
| Interfaces provided | Which frozen interfaces it implements |
| Dependencies | Packages that must be merged first; stubs to use until then |
| Tests | Tests to write, and the acceptance tests (V numbers) they feed |
| Hardware flags | `gpu`, `footage`, exclusive timing |
| Out of scope | What the package must not do |
| Done | Section 4.5, plus any package-specific acceptance item |

### 4.7 Decision log
- Kept in `docs/decisions.md` by the architect.
- Each entry: identifier, date, the decision, options considered, the evidence (a gate result, a test, a source), who decided, and whether the spec is affected.
- A decision that affects the spec becomes a proposed spec revision for the owner.

---

## 5. Owner checkpoints

Work behind a checkpoint waits for it. CP2 and CP3 can be done in one sitting.

| # | Checkpoint | After | What the owner does | What it unblocks |
|---|---|---|---|---|
| CP1 | Footage sorting | WP0.2 | Assigns each clip and photo a category in the inventory; notes gaps; decides whether chapter handling stays in v1 if the inventory shows no chaptered recordings | WP1.3, WP1.4 |
| CP2 | Look check | WP1.3, WP1.4 | Views the before/after pairs and comparison clips; records which failure cases appear and how serious each is. Informal bar, no numeric threshold (D103) | WP1.6 |
| CP3 | Gate scope decisions | WP1.6 | Reads the gate report; decides the gain caps, and anything that would relax a mandatory requirement | Phase 2 |
| CP4 | Design-freeze review | WP2.4 | Reads the decision log and architecture document in one pass; may overturn any decision; approves the spec revision | Phase 3 |
| CP5 | V2 visual review | WP5.3 | Judges the corrected test set against the 80% rule and the artifact list (D65); views the starter presets | Release (WP5.5); may trigger WP5.4 |

**Owner actions needed at the start (WP0.1):**
- Confirm the GitHub account and the repository name (proposed: `clearwater`), and that the laptop can authenticate to GitHub.
- Give the footage folder path and a location for the working folder.
- Place the spec and the research notes in the repository's `docs/` folder, or tell the architect where to fetch them.

---

## 6. Phases and work packages

Size is relative effort: S, M or L. No durations are estimated.

**Mapping to the spec's milestones (§13):** Phase 0 is milestone 1; Phase 1 is milestone 2; Phases 2–4 cover milestones 3–5; Phase 5 is milestone 6.

### Phase 0 — Setup and footage inventory

| WP | Title | Size | Depends on | Flags |
|---|---|---|---|---|
| WP0.1 | Repository, scaffolding and environment report | S | Owner actions | — |
| WP0.2 | Footage inventory tool | S | WP0.1 | `footage` |

**WP0.1 Repository, scaffolding and environment report**
- Create the local repository and the private GitHub repository (PD8).
- Scaffold per PD9 and PD10: `pyproject.toml`, uv lock file, ruff and mypy configuration, pytest with the markers `gpu`, `footage`, `gui` and `slow`, the GPL-2.0-or-later license file (D93), and ignore rules for the working folder and local configuration.
- Add the local configuration file template (footage path, working path).
- Install the FFmpeg command-line tools as development tools for the inventory and the container spike. This is not a decision on the product's video library.
- Write `tools/environment_report.py`: records the CPU model, RAM, graphics card model, dedicated graphics memory, driver version, Windows version and Python version to the working folder.
- **Closes the open item** "laptop CPU and graphics card" (spec §14.2) by reading it from the machine.

**WP0.2 Footage inventory tool**
- Write `tools/inventory.py` (D102). For each video it records: resolution, frame rate, whether the frame rate is variable, bit depth, codec, chroma format, color tags and range, duration, rotation, the list of tracks, GoPro recording and chapter numbers, and whether an `.LRV` file sits beside it. For each photo: format, pixel dimensions, bit depth, color profile, orientation.
- Output: a table with an empty category column, and a summary of the recording modes and photo sizes found.
- Categories for CP1: shallow with caustics; deeper; mostly open blue water; photo, shallow; photo, deeper; chaptered recording; static shot (if any).
- Gaps are either filled by the owner with new footage or the dependent test is marked pending.
- **Feeds:** the modes at which N6 is measured, the largest photo for V15, and the chapter-handling decision.

### Phase 1 — Prototype gate (N5, V14)

Two tracks run in parallel: the algorithm track (WP1.1–WP1.4) and the container track (WP1.5).

Prototype code is evidence, not product. It lives under `tools/prototype/`. Phase 3 packages may reuse it, but must meet the full definition of done.

| WP | Title | Size | Depends on | Flags | Gate result |
|---|---|---|---|---|---|
| WP1.1 | Reference pipeline prototype | M | WP0.1 | — | — |
| WP1.2 | CPU/GPU variant, speed and memory | M | WP1.1 | `gpu`, exclusive | 1, 2 |
| WP1.3 | Look check pack | S | WP1.1, CP1 | `footage` | 3 |
| WP1.4 | Noise and statistics experiments | M | WP1.1, CP1 | `footage` | 4, 5 |
| WP1.5 | Container spike | M | WP0.2 | `footage`, `gpu` | 6 |
| WP1.6 | Gate report | S | WP1.2–WP1.5, CP2 | — | all |

**WP1.1 Reference pipeline prototype**
- A script-level implementation of the whole pipeline (spec §6.2–6.3) on one image, on CPU: both compensation methods, optional blue compensation, gain caps, white balance with the gain clamp (D99), both fusion inputs, the three weight maps, and multiscale fusion.
- Size-relative spatial parameters (D56), so results at different resolutions can be compared.
- Confirms the κ→Cr, λ→Cb correspondence for 3C against the paper (spec §14.1).
- Records every place where the papers leave a value open, with the value used.

**WP1.2 CPU/GPU variant, speed and memory**
- Run the same pipeline on the graphics card using the candidate mechanisms (Section 8.3), from one code base where the candidate allows it (D107).
- Measure, at 4K and at each recording mode in the inventory, and at 5.3K if present:
  - per-frame time on CPU and on GPU, against the N6 budget;
  - a full-clip, end-to-end timing including decode and encode, using the path from WP1.5 when available;
  - peak RAM and peak graphics memory, including the largest photo in the inventory (D110);
  - analysis-pass speed with software decode, hardware decode and `.LRV` files (D60, D109).
- Confirm that Python 3.12 works with the candidate libraries on Windows (PD9).
- Report the proxy resolutions tried and their effect on the statistics.

**WP1.3 Look check pack**
- Run WP1.1 over the sorted footage: photos and extracted video frames, both compensation methods, as before/after pairs.
- Process one short clip frame by frame with unsmoothed statistics, so the flicker is visible.
- Include the open-blue-water, distance-haze and deep-noise cases where the inventory has them (spec §12).
- Deliver in a form the owner can page through quickly. Feeds CP2.

**WP1.4 Noise and statistics experiments**
- **Gain-cap noise test (D100):** on a deep frame, measure red-channel noise with the caps on and off, and with the white-balance clamp at several settings. The noise measure is documented, and crops are supplied so the owner can confirm what the numbers show.
- **Staged versus flat (D98):** on a short clip, compute statistics both ways with temporal smoothing, measure the mismatch, and render both versions for the owner to compare at CP2.
- Try candidate smoothing filters and window lengths, and candidate robust statistics for the normalization bounds (spec §14.1), and report the results.

**WP1.5 Container spike (D104)**
- Re-encode one real chapter with no correction using the simplest approach (decode, then encode and mux with FFmpeg-based tooling).
- Compare source and output on: tracks present, per-frame timestamps, start offset, edit list, audio stream and sync, display orientation, color tags and range, chroma format, creation time, GPMF, timecode and camera atoms.
- Classify each difference as **mandatory** (D94, D105: timing, start offset, audio sync, orientation) or **best-effort**.
- Record the color tags and range the camera actually writes (D54).
- Confirm NVENC, 10-bit encode and hardware decode in the chosen build (D74).
- Test whether `.LRV` frames align exactly with the main video (D60).
- If the inventory has such clips: check the transfer tag of GoPro's plain "HDR video" mode (D73), and look for any marker of GP-Log.
- Recommend one of the three approaches: simple, encode-then-repair, or transplant.

**WP1.6 Gate report**
- The architect compiles the six results into `docs/gate-report.md`, each with its measurement, the decision it leads to, and who decides.
- Lists the scope decisions for CP3, with options and evidence.
- Satisfies V14.

### Phase 2 — Design freeze

| WP | Title | Size | Depends on | Owner |
|---|---|---|---|---|
| WP2.1 | Architecture document and decisions | L | CP3 | Architect |
| WP2.2 | Interface module | M | WP2.1 | Implementer |
| WP2.3 | Shared test fixtures | M | WP2.1 | Implementer |
| WP2.4 | Package briefs and spec revision | M | WP2.1, WP2.2 | Architect, orchestrator |

**WP2.1 Architecture document and decisions**
- Resolve every design item in spec §14.1 (assignment in Section 9 of this plan).
- Choose the libraries (Section 8.3) and record the license position of each (N13).
- Write the signatures for interfaces IF-1 to IF-10 (Section 8.2).
- Confirm or adjust the module boundaries in Section 8.
- Log each decision (Section 4.7).

**WP2.2 Interface module**
- Implement the frozen interfaces as code: types, protocols and data classes, with docstrings, and no behavior.
- Provide a stub for each interface so Phase 3 packages can build and test before their dependencies exist.
- From this point, an interface changes only by the architect's decision.

**WP2.3 Shared test fixtures**
Generated by scripts, so no owner footage is needed:
- still images: uniform, gradient, near-zero red channel, 8-bit and 16-bit, with and without color profiles, rotated and portrait orientations;
- the synthetic flicker clip for V3 (D112): a still image repeated as frames with a moving disturbance, and a mask of the untouched region;
- video samples: 8-bit and 10-bit, HLG-tagged, PQ-tagged, untagged, truncated, variable frame rate (D115), rotated;
- a set of dummy files with GoPro chapter naming, including `.LRV` and `.THM` sidecars;
- a ProRAW/DNG-type file for the refusal test (D116).

**WP2.4 Package briefs and spec revision**
- Write the Phase 3–5 briefs in the Section 4.6 format, adjusted for the gate outcomes.
- Draft the spec revision that records the gate outcomes (for example caps kept or dropped, chapter handling, staged or flat, a tuned N6). The owner approves it at CP4.
- The build starts from the revised spec.

### Phase 3 — Parallel build

All packages depend on WP2.2 (interfaces) and use WP2.3 (fixtures). The "Depends on" column lists build dependencies beyond those. Until a dependency is merged, a package builds against the stubs.

**Core and correction method**

| WP | Title | Size | Depends on | Spec | Feeds |
|---|---|---|---|---|---|
| WP3.1 | Array backend and image operations | L | — | D39, D56, D107, D111; §6.4, §6.6 | V1, V15 |
| WP3.2 | Channel compensation and white balance | M | WP3.1 | §6.2 steps 1–2, §6.3; D47–D52, D99 | V1, V9 |
| WP3.3 | Fusion inputs, weights and blending | M | WP3.1 | §6.2 steps 3–5 | V1, V9 |
| WP3.4 | Method assembly: stages and parameter schema | M | WP3.2, WP3.3 | D61, D97; §6.7, §10.1 | V1, V8, V9 |

- **WP3.1** provides the CPU/GPU-portable primitives (IF-2): size-relative Gaussian blur, Gaussian and Laplacian pyramids with depth set by minimum level size, RGB↔YCbCr (BT.709) and the conversion saliency needs, whole-frame statistics, a memory estimate for an image of a given size, and device selection with automatic CPU fallback. Tests include CPU-versus-GPU agreement within tolerance.
- **WP3.2** covers Ancuti 2018 red and optional blue compensation with separate caps, 3C with its mask, the gray-world step, and the gain clamp. If the caps were dropped at CP3, they are omitted.
- **WP3.3** covers the gamma input, the sharpened input with its normalization, the Laplacian, saliency and saturation weights with the paper's regularization, and the multiscale blend.
- **WP3.4** assembles the plug-in (IF-3): the ordered statistic stages with their dependencies, `analyze` per stage, `render` from supplied statistics, the parameter schema with Basic/Advanced placement, and "blend with original". Includes the neutral-parameter identity test at method level.

**Input and output**

| WP | Title | Size | Depends on | Spec | Feeds |
|---|---|---|---|---|---|
| WP3.5 | Video color handling and chroma resampling | M | WP3.1 | §6.5; D54, D55, D114 | V4, V9 |
| WP3.6 | Photo input and output | M | — | §5.1, §8.1; D22, D53, D63, D91, D116 | V5, V6, V9 |
| WP3.7 | Video probe and input validation | M | — | §5.2–5.4; D15, D54, D73, D86, D95 | V4, V6 |
| WP3.8 | Chapter grouping -- REMOVED (CP1 2026-10-19: chapter handling deferred to v2, spec v0.5.3 §5.5) | -- | -- | -- | -- |
| WP3.9 | Video decode | M | WP3.5, WP3.7 | §5.2, §7.5; D86, D94 | V4, V9 |
| WP3.10 | Video encode, mux and timing | L | WP3.5, WP3.7 | §7.5, §8.2; D25, D26, D62, D74–D76, D91, D94, D105 | V4, V9 |

- **WP3.5** converts between the stream's Y′CbCr and the working RGB using the stream's matrix and range, resamples chroma in both directions by the method fixed in WP2.1, and applies the BT.709/limited default with a warning when tags are missing.
- **WP3.6** reads HEIC, JPEG, PNG and TIFF with the color profile honored and orientation applied to the pixels; writes 8- or 16-bit PNG with the matching profile, EXIF per D63, and provenance; refuses ProRAW/DNG with a clear message.
- **WP3.7** reads stream information, timestamps and tracks; refuses HLG and PQ; applies best-effort GP-Log detection; reports truncated or unreadable files; and reports variable frame rate and rotation.
- **WP3.8** is NOT built: chapter handling is deferred to v2 (CP1 2026-10-19; spec v0.5.3). Sidecar exclusion from input (D83) stays in WP3.7's probe/validation. The number is kept so later references stay stable.
- **WP3.9** yields frames (IF-1) with their exact source timestamps, by software or hardware decode, and stops cleanly at the readable end of a truncated file.
- **WP3.10** is the highest-risk package. It encodes HEVC through NVENC or the software encoder at 8 or 10 bits and the named quality levels, matches the source's tags and chroma format, passes audio through unchanged, preserves per-frame timestamps, start offset, edit list and display orientation, carries best-effort metadata where cheap, and reports encoder capabilities. Its approach is the one chosen from WP1.5.

**Analysis, cache and jobs**

| WP | Title | Size | Depends on | Spec | Feeds |
|---|---|---|---|---|---|
| WP3.11 | Analysis engine | L | — | §7.1–7.3; D57, D59, D70, D95, D97, D108 | V3, V18 |
| WP3.12 | Proxy cache | M | — | §7.3; D71, D113 | V17 |
| WP3.13 | Output naming and safe writing | S | — | §8.3–8.4; D34–D36, D83–D85, D87 | V10, V11 |
| WP3.14 | Export jobs and batch | L | WP3.13 | §8, G7, G8; D43–D45, D80, D81, D111 | V4, V11, V16 |
| WP3.15 | Presets, settings and logging | M | — | D37, D38, D88–D90; N9, N11 | V13 |
| WP3.21 | Optimisation package (Gate 1 option C, 2026-10-20): device-resident pipeline, upload/download overlap, FFT or recursive Gaussian for 3C; exclusive re-measure on GX011627 and GX011625; target about 10 min/min at 4K | M | WP3.4, WP3.9, WP3.10, WP3.14 | D106, N6; gate report Result 1 | V16 (re-run at WP5.2) |

- **WP3.11** runs the decode pass that stores proxies; computes statistics stage by stage from the proxies, each stage using the smoothed results of earlier ones; applies the centered, time-based smoothing; limits recomputation after a parameter change to frames near the one displayed; supplies per-frame statistics for the provisional preview; and supports cancel. It is built and tested against a stub method and a stub frame source, so it does not wait for WP3.4 or WP3.9.
- **WP3.12** stores and retrieves proxies keyed by file size, modification date and cache format version, evicts oldest-first at the size limit, and clears on request. It holds only results that depend on the source file alone.
- **WP3.13** builds output paths with the suffix and collision numbering, writes to a temporary name and renames on success, removes leftovers at start, and estimates disk space.
- **WP3.14** runs photo export, video export (decode, render, encode as a stream, within the memory limits of N4) and the batch queue, with progress, cancel, skip-and-log on failure, and an end-of-run report (IF-8).
- **WP3.15** provides the preset store with method and format version, import and export, the starter presets, persistent settings and last-used parameters, and the rotating log.

**Interface (PySide6)**

WP3.16 owns the main window and defines the places where the other packages attach their widgets. Each other package owns only its own widget modules. All are built against stubs of the engines.

| WP | Title | Size | Depends on | Spec | Feeds |
|---|---|---|---|---|---|
| WP3.16 | Application shell and preview | L | — | G1, G2, G9, G10; D27, D41 | V7, V8 |
| WP3.17 | Parameter panels and presets | M | WP3.16 | G3, G6; D17 | V13 |
| WP3.18 | Timeline and analysis | M | WP3.16 | G4, G5; D70, D72, D108 | V7, V18 |
| WP3.19 | Batch queue and export progress | M | WP3.16 | G7, G8 | V7, V11 |
| WP3.20 | Settings | S | WP3.16 | G12, G13; D74 | — |

- **WP3.16:** file open, the split-view slider, zoom including 1:1, the screen-resolution preview worker running off the interface thread, and messages for unsupported, damaged or untagged inputs.
- **WP3.17:** Basic and Advanced panels generated from the method's parameter schema, including controls that hide by method (D49); preset save, load, rename, delete, import and export.
- **WP3.18:** the scrubber showing proxy frames while dragging and the full-resolution frame when stopped; analysis progress and cancel; the switch from provisional to smoothed preview.
- **WP3.19:** the batch queue, export progress and cancel, and the end-of-run report. The chapter grouping review (G11) is deferred to v2 with WP3.8.
- **WP3.20:** the settings listed in G12, with unavailable encoder options shown disabled with a reason.

### Phase 4 — Integration

Run in order. Each is one implementer's package, working on the main branch after the Phase 3 merges it needs.

| WP | Title | Size | Depends on | Feeds |
|---|---|---|---|---|
| WP4.1 | Photo path end to end | M | WP3.4, WP3.6, WP3.13, WP3.14, WP3.15 | V5, V8, V9, V10 |
| WP4.2 | Video path end to end | L | WP4.1, WP3.5, WP3.7–WP3.12 | V3, V4, V9, V12, V17 |
| WP4.3 | Application wiring | L | WP4.2, WP3.16–WP3.20 | V7, V8, V18 |

- **WP4.1** replaces stubs with real components for photos, and adds a headless runner under `tools/` so acceptance tests can drive an export without the interface. The runner is a test tool, not a product feature.
- **WP4.2** joins probe, decode, analysis, cache, render and encode; every input file is its own clip (no cross-chapter smoothing in v1).
- **WP4.3** connects the interface to the engines, adds start-up work (encoder and graphics-card detection, leftover cleanup), and shows the user whether CPU or GPU is in use.

### Phase 5 — Verification and release

| WP | Title | Size | Depends on | Flags |
|---|---|---|---|---|
| WP5.1 | Automated acceptance suite | L | WP4.3 | `gui`, `footage` |
| WP5.2 | Performance and memory runs | M | WP4.2 | `gpu`, exclusive |
| WP5.3 | Visual review pack | S | WP4.3 | `footage` |
| WP5.4 | Weight-map temporal smoothing *(conditional)* | M | CP5 or WP5.1 | — |
| WP5.5 | Release preparation | S | CP5 | — |

- **WP5.1** implements the acceptance tests in Section 7 that are not already covered by package tests, and runs the whole set. Failures go back to the owning package through the verification loop.
- **WP5.2** measures V15 (peak RAM on the largest video mode and the largest photo, peak graphics memory, the CPU fallback) and V16 (the N6 target at 4K in the owner's recording modes), on full clips.
- **WP5.3** produces the corrected test set and the starter-preset samples for CP5.
- **WP5.4** is built only if V3 fails or the owner sees shimmer at CP5 (D96).
- **WP5.5** confirms the license compatibility of every bundled dependency and adds the required notices (N13), writes the installation and usage instructions, and tags the version. **No installer is included**; the spec does not ask for one. Delivery is a repository that installs with uv.

---

## 7. Verification matrix

Every acceptance test in spec §11, with where it is built and where it is run to completion.

**Completion pointer (2026-11-01, WP5.1 accepted, main `0e8f0e00`):** every test this table completes in WP5.1 (V1, V3 minus the deferred chapter seam, V4-V11, V13, V17, V18; N10 / D92 and D91) has a committed, passing node or a cited figure of record, traced in `tests/test_v51_traceability.py`; the matrix of nodes, figures and gate results is `docs/reports/wp5.1-acceptance.md`, the accept record `docs/proofs/wp5.1-accept.md`. Still open after WP5.1: V2 (the owner's visual review at CP5, from the WP5.3 pack), V14 (the prototype gate, done), V15 and V16 (WP5.2, performance and memory on full clips, EXCLUSIVE), and the V7 figures of record (WP4.6's window).

**Completion pointer (2026-11-03, CP5 complete, Phase 5 gate report FINAL):** V2 PASS at CP5 (owner's review, 111 / 115 = 96.5 % preferred, five halo observations recorded as DR-117, `docs/proofs/cp5-visual-review.md`); N6 SET at about 12 min/min (spec v0.5.8, AD-21 SET); the Phase 5 gate report `docs/reports/wp5.6-gate-report.md` is FINAL (gate p5b green on all three legs). Phase 5 verification is complete; remaining in Phase 5: WP5.5 release preparation, plus the follow-ons WP-DR25 (DR-25 (3) staged run) and WP5.7 (DR-117 halo investigation). WP5.4 not triggered (no shimmer seen).

**Phase 5 CLOSED (2026-11-04, Clearwater 1.0.0 tagged):** WP5.5 release preparation accepted (main `40d2ce04`, `docs/proofs/wp5.5-accept.md`; release gate p55 green: parallel 6,786 / 1, serial 1,262 / 11, fullclip 7, harness 382; N13 SATISFIED on `THIRD_PARTY_NOTICES.md`); the follow-ons WP-DR25 (AD-3 CONFIRMED, DR-25 closed), WP5.7 (DR-117 cause found, fix DEFERRED by the owner) and WP5.8 (AD-32 watchdog, DR-115 closed) accepted. **Tag `v1.0.0` on `40d2ce04`** on the owner's word 2026-11-04 ("tag 1.0.0"), not pushed; release record `docs/proofs/release-1.0.0.md`. Open debt carried into 1.0.0 is listed there. Next: WP-H1, then the Phase 6 proposals.

**Completion pointer (2026-11-02, WP5.2 accepted, main `2da5d0c7`):** V15 and V16 have figures of record on full clips (`docs/reports/wp5.2-performance-memory.md`, accept `docs/proofs/wp5.2-accept.md`): V16 GX011627 c3 NVENC cold median 10.89 min/min and GX011625 sustained 10.78 (the N6 figure is proposed to the owner from these; D106 re-set at the owner's ruling); V15 peak RAM 5,340 MiB and graphics memory 7,085 MiB on the synthetic 5.3K 8:7 clip, 6.64 GB RAM on the 48 MP photo, which is also the D111 automatic-fallback witness (`CPU: estimate 11,649 MiB exceeds free 7,064 MiB`). V7 figures of record are WP4.6's (`bbb4ef3e`). Still open: V2 (CP5, in progress).

| Test | Subject | Built in | Completed in |
|---|---|---|---|
| V1 | Stage correctness | WP3.1–WP3.4 | WP5.1 |
| V2 | Visual review | WP5.3 | CP5 |
| V3 | Temporal consistency (the chapter-seam part is deferred to v2) | WP3.11, WP4.2 | WP5.1 |
| V4 | Video I/O fidelity | WP3.9, WP3.10, WP4.2 | WP5.1 |
| V5 | Photo I/O fidelity | WP3.6, WP4.1 | WP5.1 |
| V6 | Unsupported inputs | WP3.6, WP3.7 | WP5.1 |
| V7 | Responsiveness | WP3.16, WP4.3 | WP5.1 |
| V8 | Preview versus export | WP3.4, WP4.1, WP4.3 | WP5.1 |
| V9 | Identity round trip | WP3.4, WP4.1, WP4.2 | WP5.1 |
| V10 | Naming and non-overwrite | WP3.13, WP4.1 | WP5.1 |
| V11 | Cancel and failure cleanup | WP3.13, WP3.14 | WP5.1 |
| V12 | Chapter grouping -- deferred to v2 with WP3.8 | -- | -- |
| V13 | Preset round trip | WP3.15, WP3.17 | WP5.1 |
| V14 | Prototype gate | WP1.2–WP1.5 | WP1.6 |
| V15 | Memory | WP3.1, WP3.14 | WP5.2 |
| V16 | Performance | WP3.14 | WP5.2 |
| V17 | Cache | WP3.12, WP4.2 | WP5.1 |
| V18 | Provisional preview | WP3.11, WP3.18, WP4.3 | WP5.1 |

V12 and the chapter-seam part of V3 are deferred to v2 (CP1 2026-10-19).

**Requirements with no V test of their own:**

| Requirement | Checked in |
|---|---|
| N1 portability | Independent review of every package (Section 4.5) |
| N2 language | Fixed by PD9 |
| N3 one core for CPU and GPU | WP3.1, with its CPU-versus-GPU agreement tests; exercised by V15 and V16 |
| N8 non-destructive | WP3.13 and the read-only footage rule (Section 4.2); exercised by V10 |
| N7 code quality | Definition of done (Section 4.5) |
| N10 reproducibility (D92) | WP5.1: the same export run twice, compared within the tolerance from WP2.1 |
| D91 provenance in photo and video output | WP3.6, WP3.10; checked in WP5.1 |
| N12, N13 licensing | WP2.1, WP5.5 |

---

## 8. Module boundaries and interfaces

### 8.1 Modules

| Module | Responsibility | Built by |
|---|---|---|
| `clearwater.interfaces` | Frozen types and protocols; no behavior | WP2.2 |
| `clearwater.core` | Array backend, image operations, device selection, memory estimate | WP3.1 |
| `clearwater.methods` | Correction method plug-ins; v1 has one, Ancuti fusion with selectable compensation | WP3.2–WP3.4 |
| `clearwater.color` | Video color conversion and chroma resampling | WP3.5 |
| `clearwater.io.photo` | Photo read and write, profiles, EXIF | WP3.6 |
| `clearwater.io.video` | Probe, validation, chapters, decode, encode, mux | WP3.7–WP3.10 |
| `clearwater.analysis` | Decode pass, staged statistics, smoothing, recompute | WP3.11 |
| `clearwater.cache` | Proxy cache | WP3.12 |
| `clearwater.jobs` | Naming, safe writing, export, batch | WP3.13, WP3.14 |
| `clearwater.config` | Presets, settings, logging | WP3.15 |
| `clearwater.gui` | PySide6 interface | WP3.16–WP3.20 |
| `clearwater.app` | Entry point and start-up | WP4.3 |

**Dependency rule:** `gui` and `jobs` reach correction methods only through IF-3 (spec §10.1). `core` and `methods` import nothing from `io`, `jobs` or `gui`.

### 8.2 Interfaces to freeze

Signatures are written in WP2.1. This table fixes what each must carry.

| # | Interface | Must carry |
|---|---|---|
| IF-1 | Image and frame | Pixel data as 32-bit float in [0, 1]; which device holds it; dimensions; the source's color description (primaries, transfer, matrix, range) and bit depth; for video, the exact source timestamp |
| IF-2 | Array backend | One code path for CPU and GPU; device selection; a memory estimate for a given image size; fallback to CPU when the estimate exceeds graphics memory |
| IF-3 | Correction method | Ordered statistic stages, each with its statistics, which are smoothed, and its parameter and stage dependencies; `analyze` per stage; `render` from supplied statistics; parameter schema; optional context inputs (D61, D97) |
| IF-4 | Statistics store | Per-frame statistics by stage, indexed by time; raw and smoothed values; resets at group breaks |
| IF-5 | Video source and sink | Probe result (streams, tags, timestamps, tracks, rotation, faults); a frame iterator with exact timestamps; a sink that takes frames with timestamps and preserves timing, audio and orientation; an encoder capability report |
| IF-6 | Photo source and sink | Read to IF-1 with profile, orientation applied and metadata carried; write PNG with profile, EXIF rules and provenance |
| IF-7 | Proxy cache | Key (size, date, cache version); store and fetch proxies; size limit and eviction; clear |
| IF-8 | Jobs | Progress reporting, a cancel signal, and a result per item with warnings and failures; shared by analysis, export and batch |
| IF-9 | Parameter set | A method identifier, parameter values and a format version; the form presets and provenance are saved in |
| IF-10 | Settings | The persistent settings of G12 and the last-used parameters |

### 8.3 Library candidates

The architect chooses in WP2.1 from the gate's evidence. These are candidates, not decisions. PySide6 is fixed by D28.

| Need | Candidates | Decided by |
|---|---|---|
| CPU/GPU array code | NumPy with CuPy; PyTorch | WP1.2: speed, memory, one code path, installation on Windows |
| Video decode, encode, mux | PyAV; FFmpeg run as a separate process; either with a repair pass | WP1.5: mandatory timing fidelity, NVENC and 10-bit support |
| HEIC reading | pillow-heif | WP2.1 |
| PNG writing | Pillow; pypng; OpenCV | WP2.1: must write 16-bit RGB with both a color profile and EXIF, to be verified |
| Color profiles | Pillow's ImageCms | WP2.1 |
| EXIF | Pillow; piexif; ExifTool | WP2.1 |
| Interface tests | pytest-qt | WP2.1 |

**License note (N13).** Clearwater is GPL-2.0-or-later. The license of each chosen library, of the FFmpeg and x265 builds, and of any NVIDIA runtime files that would be distributed with it is checked at WP2.1 and confirmed at WP5.5. This plan asserts nothing about their compatibility.

---

## 9. Design items and where they are decided

Every item in spec §14.1. Decisions are made by the architect in WP2.1 unless noted, and logged.

| Design item | Evidence from |
|---|---|
| GoPro plain "HDR video" mode output | WP1.5, if the inventory has such a clip; otherwise pending |
| GP-Log detection method and limits | WP1.5 |
| `.LRV` files as proxies | WP1.5 (alignment), WP1.2 (speed) |
| Smoothing filter type and default window | WP1.4 |
| Proxy resolution and storage format | WP1.2 |
| Robust statistics for normalization bounds | WP1.4 |
| κ→Cr, λ→Cb correspondence for 3C | WP1.1 |
| Direction of "blend with original"; neutral value of each parameter | WP2.1 |
| Defaults the papers leave open; default maximum white-balance gain | WP1.1, WP1.3, WP1.4, CP2 |
| Quality levels mapped to each encoder | WP1.5 |
| Tolerances: reproducibility, identity round trip, preview versus export | WP2.1; tunable after WP5.1 |
| Preset file format and starter preset values | WP2.1; values shown to the owner at CP5 |
| Stage definitions per compensation method; live-preview recompute scheme | WP1.4 |
| CPU/GPU mechanism, library, and graphics memory estimate | WP1.2 |
| Reporting CPU or GPU use to the user; whether it can be overridden | WP2.1 |
| Video I/O library and approach; carrying best-effort metadata | WP1.5 |
| Chroma resampling method | WP2.1 |
| Synthetic flicker clip design | WP2.1, built in WP2.3 |
| Scrubbing, parameter changes and export while analysis is running | WP2.1 |

---

## 10. Gate outcomes and what each changes

The gate can change the plan. These are the branches foreseen; anything else is raised at CP3.

| Result | Outcome | Effect | Decided by |
|---|---|---|---|
| 1 Speed | GPU meets N6 at 4K | Proceed as planned | Architect |
| 1 Speed | GPU misses N6 at 4K | Architect presents measured options; the owner tunes the target (D106 allows this) or approves optimization work | Owner |
| 1 Speed | Analysis pass too slow by every route | Sparse analysis considered (D109) | Architect |
| 1 Speed | No usable NVIDIA card, or no 10-bit NVENC | Software paths only; the affected options are shown disabled (D74); N6 reassessed | Owner |
| 2 Memory | Largest photo exceeds 16 GB even on CPU | A photo size limit is revisited (spec §12) | Owner |
| 3 Look | A failure case is serious | Addressed by a default, the clamp, or a scope decision, recorded per case (D103) | Owner |
| 4 Noise | Caps do not earn their place | Caps dropped: removed from WP3.2, the schema and V1; spec revised | Owner |
| 5 Statistics | No visible difference | The method may declare one stage; IF-3 stays staged (D98) | Architect, using the owner's observation at CP2 |
| 6 Container | Simple approach meets the mandatory items | WP3.10 as planned | Architect |
| 6 Container | Gaps in mandatory items | Encode-then-repair; WP3.10 grows | Architect |
| 6 Container | Repair cannot meet them | Transplant approach; WP3.10 is re-planned as several packages | Architect, reported at CP4 |
| Inventory | No chaptered recordings (CLOSED 2026-10-19: none among 34 GoPro files) | Owner deferred chapter handling to v2; WP3.8, the chapter review in WP3.19, V12 and the seam test removed; spec revised as v0.5.3 | Owner |
| Environment | Python 3.12 not supported by a chosen library | Architect selects the version | Architect |

---

## 11. Scheduling

### 11.1 Critical path
The gate has two chains that meet at the gate report:
- WP0.1 → WP1.1 → WP1.2 → WP1.6
- WP0.1 → WP0.2 → CP1 → WP1.3 and WP1.4 → CP2 → WP1.6

From there: WP1.6 → CP3 → WP2.1 → WP2.2 → WP2.4 → CP4 → WP3.1 → WP3.2 and WP3.3 → WP3.4 → WP4.1 → WP4.2 → WP4.3 → WP5.1 → CP5 → WP5.5.

WP1.1 starts as soon as WP0.1 is merged; it does not wait for CP1. WP3.10 is the largest risk in the build and should start as early as its dependencies allow.

### 11.2 Parallel groups

| Group | Packages that can run together |
|---|---|
| Phase 1 | WP1.1 alongside WP1.5; then WP1.2, WP1.3 and WP1.4 (only WP1.2 timings are exclusive) |
| Phase 2 | WP2.2 and WP2.3 after WP2.1 |
| Phase 3, first | WP3.1, WP3.6, WP3.7, WP3.11, WP3.12, WP3.13, WP3.15, WP3.16 |
| Phase 3, second | WP3.2, WP3.3, WP3.5, WP3.8, WP3.14, WP3.17, WP3.18, WP3.19, WP3.20 |
| Phase 3, third | WP3.4, WP3.9, WP3.10 |
| Phase 4 | In order, one at a time |
| Phase 5 | WP5.1 and WP5.3 together; WP5.2 exclusive |

WP3.9 and WP3.10 may move to the second group by building against a stub of WP3.5.

---

## 12. Open items

| Item | Closed by |
|---|---|
| Laptop CPU and graphics card | WP0.1, read from the machine |
| Chapter handling in v1 | CLOSED 2026-10-19: deferred to v2 (CP1; spec v0.5.3) |
| Photo resolution and video recording modes | WP0.2 |
| Gain caps kept or dropped | CP3 |
| Staged or flat statistics | WP2.1, after CP2 |
| Sparse analysis | WP2.1, from WP1.2 |
| Weight-map temporal smoothing | WP5.1 or CP5 |
| GitHub account, repository name, footage and working folder paths | Owner, before WP0.1 |

**Not included in this plan.** Raise with the owner if wanted:
- a hosted CI service;
- an installer or packaged executable;
- testing on machines other than the owner's laptop (PD11);
- making the repository public (PD8 keeps it private initially).
