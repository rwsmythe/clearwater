# Spec revision v0.5.4 — PROPOSAL for the owner (WP2.4; CP4 design freeze)

**Status:** PROPOSED by CHARC 2026-10-20. Applied only on the owner's word. Records the Phase 1
gate outcomes (`docs/reports/wp1.6-gate-report.md`) and the WP2.1 design decisions that touch
spec text (`docs/decisions.md`). One passage waits on the owner's Gate 1 decision (item 1).
Everything else is a recording of decisions already taken, not a new request.

| # | Passage | Current (v0.5.3) | Proposed (v0.5.4) | Source |
|---|---|---|---|---|
| 1 | **D106 / N6** export performance target | "about 3.3 minutes of processing per minute of footage ... tunable after measurement" | **OWNER'S CHOICE at Gate 1.** Option A/C: "about 25 minutes of processing per minute of 4K footage on the owner's laptop (interim; measured unoptimised, 2026-10-19), to be re-set after the Phase 3 optimisation package (target about 10 min/min) is measured at WP5.2". Option B: the figure measured after the optimisation package. | Gate report Result 1; AD-21 |
| 2 | **V16** | "export meets the N6 target at 4K in the owner's recording modes" | unchanged wording; the target is whatever D106 says | same |
| 3 | **D100** gain caps | "kept for now, and kept or dropped according to a prototype noise test" | "KEPT (WP1.4b, 2026-10-20): a tighter cap raises red noise on the deep frames as expected; the default cap 2.0 binds on 1 of 8 deep frames; c3 is the lowest-noise setting on every deep frame" | Gate result 4; owner KEEP confirmation |
| 4 | **D98** staged versus flat | "compared in the prototype gate" | add: "Compared 2026-10-19: no visible difference (owner, CP2); a method may declare one stage; IF-3 stays staged" | Gate result 5 |
| 5 | **D94** edit list "copied, not recalculated" | as is | add the AD-22 reading: "where only the encoder's composition-offset convention differs, 'copied' is read by presentation effect (pts sequence, start offset, duration and first displayed frame exact); the as-written media_time may differ" | WP1.5 section 8; AD-22 |
| 6 | **G12** settings list | output folder, suffix, PNG bit depth, encoder, quality, 10-bit-for-8-bit, provenance, cache limit, clear cache | add "force CPU processing (Advanced)"; add the first-run defaults: PNG 16-bit, encoder auto (NVENC when available, else software), quality Standard, cache 20 GB | AD-9; WP2.2 round-1 ruling |
| 7 | **D75** quality levels | "named levels, mapped per encoder" | add the names High / Standard / Draft and the provisional mapping (NVENC cq 18/23/28; libx265 crf 18/23/28), verified in WP3.10 | AD-12 |
| 8 | **14.1** deferred-to-design list | 19 items open | mark each item DECIDED with its AD number (smoothing AD-3; proxy AD-5; bounds AD-4; kappa/lambda WP1.1; blend direction and neutral set AD-8; defaults AD-8; quality AD-12; tolerances AD-11; presets AD-13; stages and recompute AD-6/AD-7; CPU/GPU AD-1/AD-9; video I/O AD-2/AD-23; chroma AD-10; flicker clip AD-14; analysis-running behaviour AD-15; GP-Log AD-16); "HDR video mode" stays PENDING a clip; `.LRV` already closed | WP2.1 |
| 9 | **6.3 defaults** (where the spec names values) | caps and clamp defaults open | record: red and blue gain caps default 2.0 (None = disabled), white-balance gain clamp default 3.0, N{} bounds 0.5/99.5 percentiles with a 0.02 range floor; "Blend with original" 0 = corrected, 1 = original | AD-8, AD-4 |
| 10 | **12** risks | "statistics on downscaled frames" | add the measured size: 540-line proxy bounds 11-14 % narrower than full frame, accepted as defined behaviour (AD-4) | Part B claim 6 |
| 11 | **7.2** smoothing | window "defined in time (seconds)" | add "default 2.0 s, median then Gaussian (AD-3), provisional; a lighting step within a clip is not hidden by the window (deep CP2); a step-aware variant is a Phase 2/3 design task" | AD-3; CP2 deep |
| 12 | **N1** portability | "nothing specific to one operating system without approval" | add the approved exception: "the enlarged anonymous-pipe buffer for frame transport on Windows (AD-23), with automatic portable fallback" | AD-23 |
| 13 | **D63** photo orientation | as is | add the HEIC rule of AD-24 (apply EXIF Orientation only when no `irot` transform is present), provisional until an owner photo is read | AD-24 |
| 14 | **5.5 / cache lines 339, V17, V10, plan WP3.13 row** chapter- and recording-group remnants | two sentences still mention chapter groups; V10 and the plan's WP3.13 row speak of one collision suffix shared across a recording group | delete the two remnants and the shared-group-suffix phrase (moot in v1 since v0.5.3: every input file is its own clip) | CHARC note at v0.5.3; WP3.13 brief ruling 13.1 |
| 15 | Header | Version 0.5.3, date 13 October 2026 | Version 0.5.4, date of approval; change-log line "0.5.4 — Prototype gate outcomes and WP2.1 design decisions recorded (D100 kept, D98 compared, D106 tuned, D94 reading, G12 defaults and force-CPU, D75 names, 14.1 closed)" | -- |

**What is NOT proposed:** no mandatory requirement is relaxed other than D106, which the spec
itself marks tunable; no scope change; the chapter deferral stands as v0.5.3 made it.

**How it is applied:** on the owner's word ("approved as 0.5.4", with the Gate 1 option named),
CHARC edits exactly the passages above, bumps CLAUDE.md's spec line, and records the word verbatim
with its time in `docs/proofs/cp4-design-freeze.md`.
