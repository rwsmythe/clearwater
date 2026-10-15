# WP1.6 — Prototype gate report (TEMPLATE, CHARC; filled when all six results are in)

**Status:** TEMPLATE, drafted by CHARC 2026-10-15 so the owner's CP3 decisions arrive framed
with measured options. The plan names this file `docs/gate-report.md`; it lives under
`docs/reports/` with the other result reports (the harness's instance surface), a
placement decision within CHARC's authority. Spec **v0.5.2**; plan sections 6 (WP1.6), 9, 10;
N5, V14. Each result section states the measurement, the decision it leads to, and who
decides. Sections marked PENDING are filled from the named report when it is accepted.

| Result (N5) | Package | Report | Status 2026-10-15 |
|---|---|---|---|
| 1 Speed | WP1.2 Part A (synthetic) + Part B (real) | `wp1.2a-speed-memory.md`, `wp1.2b-speed-memory.md` | A ACCEPTED (synthetic); B PENDING (footage) |
| 2 Peak memory | WP1.2 Part A + Part B | same | A ACCEPTED (synthetic, no photo); B PENDING |
| 3 Look check | WP1.3 shallow part (+ later part on the deeper footage and photos), CP2 | `wp1.3-look-check.md` | IN FLIGHT (shallow) |
| 4 Gain-cap noise test | WP1.4b (deep frame) | `wp1.4b-noise.md` | PENDING (scuba footage) |
| 5 Staged versus flat | WP1.4 shallow part, CP2 | `wp1.4-statistics.md` | COMMISSIONED |
| 6 Container spike | WP1.5 | `wp1.5-container-spike.md` | ACCEPTED: SIMPLE |

## Result 1 — Speed (N6, D106; plan section 10 rows 1)

**Measured (synthetic, Part A, accepted `f6d998a`; GPU third window, RTX 4070 Laptop):**

| Size | Method | Core per frame (s) | Share of 0.111 s (30 fps) | Share of 0.056 s (60 fps) |
|---|---|---|---|---|
| 4K | ancuti2018 | 0.389 | 3.5x | 6.9x |
| 4K | c3 | 0.652 | 5.9x | 11.6x |
| 5.3K | ancuti2018 | 0.836 | 7.5x | 14.9x |
| 5.3K | c3 | 1.503 | 13.5x | 26.8x |

CPU: 11 to 58 s per frame (99x to 522x), as spec 12 expects. The core ALONE exceeds the whole
end-to-end budget before decode and encode are added; the device-resident path (2.5x / 4.6x
at 4K) does not change that. The pipeline is unoptimised by CHARC's ruling (measure first).

**Measured (real, Part B):** PENDING. Per-mode core time; full-clip end to end in minutes of
processing per minute of footage (target 3.3); the decode / core / encode split; analysis
speed with software and hardware decode; the optimisation candidates with cost estimates.

**Decision this leads to (owner, plan section 10 "GPU misses N6 at 4K"):** on the synthetic
evidence Gate 1 is MISSED at 4K by about 3.5x (ancuti2018) and 5.9x (3C). D106 makes the
target "tunable after measurement". The options CHARC will put to the owner at CP3, with the
Part B figures filled in:

- **Option A — tune the target to the measured figure.** Set N6 to about [Part B minutes per
  minute, e.g. 12-20] minutes of processing per minute of 4K footage. No optimisation
  package; the export of a 3-minute clip takes [X] minutes. Lowest risk to the schedule.
- **Option B — approve an optimisation package before the build**, targeting the measured
  split: [from Part B claim 7: the 3C Gaussian by FFT or recursive filter (expected: brings
  3C near ancuti2018); a device-resident pipeline with only the output copied back (measured
  0.11-0.14 s per 4K frame saved); fewer live intermediates; decode/encode overlap]. Expected
  reach: [estimate]; cost: one package in Phase 3 (WP3.1 scope grows) and a re-measure.
- **Option C (CHARC's lean, to be confirmed by Part B) — both:** adopt an interim target at the
  measured figure now so Phase 2 can freeze interfaces, and carry the optimisation candidates
  as a named Phase 3 package with V16 re-run at WP5.2; the target is tuned again then. 5.3K
  stays best-effort (D106).

Sub-decisions (architect): sparse analysis (D109) only if Part B's analysis speed is
unacceptable: PENDING. NVENC 10-bit and hardware decode are PROVEN (WP1.5), so the "no 10-bit
NVENC" row does not apply.

## Result 2 — Peak memory (N4, D68, D110, D111; plan section 10 row 2)

**Measured (synthetic, Part A):** peak RSS under 3.1 GiB at 5.3K; peak graphics memory
3275 MiB at 5.3K (40 % of 8188 MiB); `memory_estimate_bytes` is 1.16x the pool's reserved
peak, a usable fallback input (D111). **Real (Part B):** PENDING, including the largest photo
and whether the CPU fallback engages.

**Decision:** on the synthetic evidence the 16 GB limit holds with a wide margin for video. The
photo case decides whether a size limit is revisited (owner, only if the largest photo exceeds
16 GB even on CPU; not expected at 24-48 MP from the Part A estimate: about [estimate] GB).

## Result 3 — Look check (D103; plan section 10 row 3) — CP2

**Evidence:** `wp1.3-look-check.md` (shallow part, in flight): 24 frames x 3 variants at
defaults, the unsmoothed flicker clip, per-frame statistics, the caustics note. Deeper,
open-water, haze and photo cases: PENDING the owner's sorting of the rest.

**Decision (owner at CP2, per failure case):** observed / seriousness / decision, recorded in
the report's CP2 sheet; a serious case is addressed by a default, the clamp, or a scope
decision. CHARC carries each decision into WP2.1 (defaults) or the spec revision (WP2.4).

## Result 4 — Gain-cap noise test (D100; plan section 10 row 4) — PENDING

Needs a deep frame (scuba, ~20 m). WP1.4b is commissioned when the owner sorts that footage.
**Decision (owner at CP3):** caps kept or dropped. If dropped: removed from WP3.2, the
parameter schema and V1; spec revised at WP2.4.

## Result 5 — Staged versus flat statistics (D98; plan section 10 row 5)

**Evidence:** `wp1.4-statistics.md` (commissioned): the mismatch per statistic, the residual
flicker of each, and both renders for the owner at CP2; plus the smoothing filter and window
recommendation and the robust N{} bounds study (14.1 items).

**Decision (architect, using the owner's observation at CP2):** if no visible difference, the
method may declare one stage; IF-3 stays staged either way (D98). The smoothing default and
the bounds statistic are WP2.1 decisions from this evidence.

## Result 6 — Container spike (D104, D105; plan section 10 row 6) — ACCEPTED

**Measured (WP1.5, accepted `3242679`):** SIMPLE path (one FFmpeg process, NVENC): on two
chapters all MANDATORY items (full pts sequence, start offset, video edit list as written and
by presentation effect, audio byte-identical and in sync, orientation) and all REQUIRED
items (BT.709 full range, 4:2:0 8-bit, HEVC, MP4) SAME; 8 best-effort differences (camera
`udta` atoms, firmware tag, audio timecode tag, brands, encoder/handler tags, track order and
flags, sample-entry boxes, muxer identity edits on non-video tracks); GPMF, timecode and
creation time kept. NVENC and libx265 8/10-bit and CUDA decode PROVEN. Camera: HERO13 Black,
HEVC Main 8-bit `yuvj420p`, BT.709 FULL range, CFR 30000/1001. No `.LRV` (D60 closed).

**Decision (architect): Gate 6 = SIMPLE; WP3.10 as planned**, with: full range honoured end to
end (D54 reading, CHARC pre-ruling 3); the B-frame edit-list convention decided at WP2.1
(DR-15); `udta` repair as a best-effort item for WP3.10 (debt); the compare instrument's
blind spots DR-18. Formally declared here, not at the WP1.5 accept. Video I/O library choice
(FFmpeg-as-process versus PyAV) is WP2.1's from the WP1.5 report's last section.

## Scope decisions for CP3 (owner), with options and evidence

| Decision | Options | Evidence | Status |
|---|---|---|---|
| N6 target (Result 1) | A tune / B optimise / C both | Part A, Part B | PENDING Part B |
| Gain caps (Result 4) | keep / drop | WP1.4b | PENDING scuba footage |
| Chapter handling in v1 | keep / defer (removes WP3.8, WP3.19's review, V12, the seam test; spec revised) | the full inventory | PENDING download complete |
| Anything relaxing a mandatory requirement | none proposed | — | none |
| Photo size limit (Result 2) | only if the largest photo exceeds 16 GB on CPU | Part B | PENDING |

## Design items decided by the architect from this gate (plan section 9)

Filled at WP2.1 from the reports: smoothing filter and window (WP1.4); robust bounds
statistic (WP1.4); stage definitions and recompute scheme (WP1.4); CPU/GPU mechanism and
memory estimate (WP1.2A: CuPy, `memory_estimate_bytes`); video I/O approach (WP1.5: SIMPLE;
library at WP2.1); proxy resolution (WP1.2A section 8, Part B claim 6); defaults the papers
leave open (WP1.1 open values + CP2).

## V14 record

All six N5 results recorded, each with the decision it led to: PENDING until Results 1 (B),
2 (B), 3, 4 and 5 are in. This section is replaced by the record when the gate closes.
