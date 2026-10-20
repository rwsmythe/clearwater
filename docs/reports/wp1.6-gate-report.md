# WP1.6 — Prototype gate report (CHARC, 2026-10-20)

**Status:** DRAFT for CP3, all six N5 results in. Written by CHARC from the accept records and
reports named below; the orchestrator fact-checks every figure against its source before the
record section is marked final. Spec **v0.5.3**; plan v1.1 sections 6 (WP1.6), 9, 10; N5, V14.
Each result states the measurement, the decision it leads to, and who decides. Gate 1 (speed)
is the one owner decision left open by this report; everything else is decided here or is
already the owner's recorded word.

Machine for every figure: the owner's laptop, AMD Ryzen 9 7940HS, RTX 4070 Laptop 8 GB,
Windows 11. Part B ran under the owner's best-effort ruling (2026-10-19: "I am not concerned
about contaminated figures as the actual program itself will run in a non-ideal state. Best
effort is fine."), so its figures are **upper bounds on a shared, non-idle laptop**; the one
stray-clean export row is marked.

| Result (N5) | Package | Report | Accept |
|---|---|---|---|
| 1 Speed | WP1.2 Part A (synthetic) + Part B (real) | `wp1.2a-speed-memory.md`, `wp1.2b-speed-memory.md` | `f6d998a`; `2dd06cf` (record `wp1.2b-accept.md`) |
| 2 Peak memory | WP1.2 Part A + Part B | same | same; photo leg PENDING (no photo supplied, D102) |
| 3 Look check | WP1.3 shallow + WP1.3D deep, CP2 shallow + deep | `wp1.3-look-check.md`, `wp1.3d-deep-look-check.md` | `7178540`; `7f9fea1`; CP2 records `cp2-look-check.md`, `cp2-deep-look-check.md` |
| 4 Gain-cap noise test | WP1.4b | `wp1.4b-gain-cap-noise.md` | `afaff0e` (record `wp1.4b-accept.md`) |
| 5 Staged versus flat | WP1.4 shallow, CP2 | `wp1.4-statistics.md` | `91f5775` |
| 6 Container spike | WP1.5 | `wp1.5-container-spike.md` | `3242679` |

## Result 1 — Speed (N6, D106; plan section 10 row 1) — MISSED; owner decision

**N6 as written:** export at most about 3.3 min of processing per minute of footage, end to end;
about 0.111 s per 4K frame at 30 fps.

**Measured, synthetic (Part A, `f6d998a`), core per frame on the GPU:** 4K ancuti2018 0.389 s,
4K c3 0.652 s, 5.3K ancuti2018 0.836 s, 5.3K c3 1.503 s. CPU 11-58 s per frame.

**Measured, real footage (Part B, `2dd06cf`), 4K HEVC 29.97 fps, GPU:**

| Measure | Figure | x N6 | Condition |
|---|---|---|---|
| Core alone, ancuti2018 (claim 2, run of record) | 0.395 s/frame | 3.6x | spread 0.375-0.618 s over 22 runs |
| Core alone, c3 (the default since v0.5.3) | 0.639 s/frame | 5.8x | within 2 % of Part A |
| Export, GX011627 (22.7 s), production-shaped, ancuti2018 | 0.4856 s/frame, **14.55 min/min** | 4.41x | the one stray-clean row |
| Export, GX011627, device-resident variant | 0.3576 s/frame, 10.72 min/min | 3.25x | contaminated |
| Export, GX011625 (498 s, full clip), ancuti2018 | 0.8386 s/frame, **25.13 min/min**, 3.48 h | 7.62x | contaminated; thermal slowdown to 91 C |
| Analysis pass, GX011625, software / CUDA decode | 3.57 / 3.30 min/min | (no target) | contaminated; pipe-bound |
| Analysis pass, GX011627 (re-run) | 2.12 min/min | -- | least loaded window, still contaminated |

**The split (GX011627):** decode-only 0.089 s/frame, encode-only 0.037, core 0.395; the export
(0.486) lies between the largest stage and their sum, so decode and encode already overlap the
core. The decode figure is bound by the Windows raw pipe (32 KB chunks: 0.094 s/frame through
the pipe against 0.016 s decoding to NUL; 1 MB+ blocks reach 4-6 GB/s).

**Supersession note (CHARC, 2026-10-20, after WP2.1S `a866f06`).** The Part B decode and pipe figures above (decode-only 0.089 s/frame; pipe 0.094 s vs 0.016 to NUL; candidate #6's -20 to -30 % analysis estimate) were measured under sibling-harness load and are superseded by WP2.1S's clean rows on the same clip: today's pipe **55.9 ms/frame**, a 32 MiB-buffered pipe **16.1 ms** (CUDA decode 13.0), decode-to-null floor 13.45 ms; analysis-pass projection with the large pipe about **1.5-2.0 min/min**. The D109 sub-decision below stands a fortiori. The core figures and the Gate 1 options are unchanged.

**No measured export used c3.** The production export row is ancuti2018; c3 costs 0.244 s/frame
more in the core (0.639 vs 0.395), so a c3 export on the same clip is estimated at about
0.73 s/frame, **about 22 min/min (6.6x)** unoptimised. This estimate is CHARC's, from the two measured rows, assuming the core delta adds 1:1 to the export (the core dominates and decode and encode already overlap it); it was not run.

**Optimisation candidates (Part B claim 7; none tried; estimates, not measurements):**

| # | Candidate | Effect | Cost |
|---|---|---|---|
| 6 | Raw transport with large writes (PyAV in-process, or a pipe/socket in 1 MB+ blocks) | takes the decode stage from 0.089-0.094 s/frame toward the 0.016 s to-NUL figure (1 MB+ blocks: 4.0-5.4 ms/frame in the transport record); on the analysis pass the source estimates **-20 to -30 %** (it becomes decode- and statistics-bound); little for export while the core dominates | low-moderate; WP2.1's transport choice |
| 1 | Device-resident pipeline, copy back the output only | measured -26 % end to end; core -30 % for ancuti2018 (0.395 -> 0.276 s) and -20 % for c3 (0.639 -> 0.514 s); contaminated windows | low |
| 5 | Upload/download overlap on CUDA streams | about 0.02-0.03 s on top of #1 | moderate |
| 3 | 3C large Gaussian by FFT or recursive filter | up to -0.24 s/frame for c3 only (its sigma-108, 865-tap Gaussian) | moderate; numerical agreement to re-verify |
| 2 | Fewer materialised intermediates in the render | about 0.1 s/frame, overlapping #1 | moderate |
| 4 | Pyramid memory release | memory only (-27 % peak) | low; matters for 5.3K and photos |
| 7 | Sustained thermal margin | the full-clip core moved 0.56-0.93 s across the clip | not code: the owner's power and cooling |

Best estimated reach with #1 + #5 + #3: core about **0.25-0.29 s/frame for either method**,
about 2.3-2.6x N6. **N6 as written is not reachable at 4K on this laptop by any listed route**;
it would need all of the above plus work not yet identified.

**Decision this leads to (OWNER, plan section 10 "GPU misses N6 at 4K"; D106 makes the target
"tunable after measurement"). The options:**

- **Option A — tune N6 to the measured figure, no optimisation package.** N6 becomes about
  **25 min of processing per minute of 4K footage** (the c3 estimate, 22, with a margin for
  thermal slowdown on long clips). A 3-minute clip exports in about 75 minutes; the 8-minute
  GX011625 in about 3.5 hours. Lowest schedule risk; the product is slow.
- **Option B — approve an optimisation package before the build.** Candidates #6, #1, #5, #3
  as one named package (WP3.1's scope grows), re-measured on GX011627 and GX011625 before
  Phase 3 proceeds. Estimated reach about 0.25-0.29 s/frame core (the source's estimate); export about **8-10 min/min** (2.4-3x N6), CHARC's estimate adding decode, encode and the residual to that core. Cost: one opus-high package plus an exclusive re-measure (about 4 h of machine
  time); Phase 2 interface freezes wait for it only where the transport choice (#6) touches them.
- **Option C (CHARC's recommendation) — both, in this order.** (1) Adopt now an **interim N6 of
  25 min/min at 4K** so Phase 2 can freeze interfaces and the V16 test has a number. (2) Make
  the transport choice (#6) in WP2.1 as planned, since it is a design decision Phase 2 must take
  anyway. (3) Carry #1, #5 and #3 as a named Phase 3 optimisation package with V16 re-run at
  WP5.2, target **10 min/min**. (4) Tune N6 finally at WP5.2 from the re-measure. 5.3K stays
  best-effort (D106). This gets the build moving on honest numbers and spends optimisation effort
  once, after the transport is settled, where its estimates can be confirmed.

Whichever option, N6's "about 3.3 min/min" sentence in D106 changes, which is a spec change
(v0.5.4) and the owner's.

**Sub-decisions (CHARC):**
- **D109 sparse analysis: NOT named.** Analysis runs at 3.3-3.6 min/min pipe-bound (2.1 in the
  least loaded window); with candidate #6 the source estimates -20 to -30 %, so about 2.3-2.9
  min/min. That is acceptable: the analysis pass is one pass per clip beside an export of 15-25
  min/min, so it is about a tenth of the processing time, and sparse analysis could save at most
  that tenth while adding a statistics-accuracy risk. Sparse analysis stays in reserve.
- The "no usable card / no 10-bit NVENC" row does not apply: NVENC 8/10-bit and CUDA decode
  are PROVEN (WP1.5).
- Observation for the test plan: the full pytest suite now takes 8-15 minutes (771 tests), past
  one 10-minute tool call at the orchestrator's seat; the gate step runs it in the background or
  in two selections. Not a gate item.

## Result 2 — Peak memory (N4, D68, D110, D111; plan section 10 row 2) — HOLDS

**Measured, synthetic (Part A):** peak RSS under 3.1 GiB at 5.3K; peak graphics memory 3,275 MiB
at 5.3K (40 % of 8,188); `memory_estimate_bytes` 1.16x the pool's reserved peak.

**Measured, real (Part B, GX011625 full-clip export, 4K):** process tree peak RSS **3,682 MiB**
(Python 1,996; FFmpeg children 1,740) against the 16 GB limit; device-wide graphics memory peak
**2,860 MiB** of 8,188 (CuPy pool 1,709 reserved / 1,585 used; NVENC included);
`memory_estimate_bytes` 1,982 MiB for a 4K frame, 1.16x the pool, so the estimate is a usable
fallback input (D111). The CPU fallback did not engage (the estimate was below free device
memory), so D111's switch is untested on real data: a test-plan item for WP3.x, not a gate gap.

**Largest photo: PENDING** (D102: no photo in the inventory; the owner's photos are still to be
supplied). Queued for the first photo, not dropped.

**Decision (CHARC):** the 16 GB limit holds for video with a wide margin (23 % used at 4K,
including FFmpeg). No photo size limit is proposed; the owner's row in plan section 10 ("largest
photo exceeds 16 GB even on CPU") is not reached and is not expected to be at iPhone sizes (assumed 24-48 MP; no photo is inventoried yet).

## Result 3 — Look check (D103; plan section 10 row 3) — CP2 COMPLETE, shallow and deep

**Evidence:** `wp1.3-look-check.md` (24 shallow frames x 3 variants, flicker clip) and
`wp1.3d-deep-look-check.md` (48 scuba stills + 12 case candidates x 3 variants, 6 s deep clip).
Records: `cp2-look-check.md` (2026-10-19) and `cp2-deep-look-check.md` (2026-10-20).

**Owner's findings (verbatim in the records):** shallow: "Both of the ancuti algorithms seem to
cause too much red in the scene (skin and white boat show this in particular. C3 seems to match my
recollection of the actual scene"; "I saw no indications of halo, noise, or clipping. c3 should be
the default, we can keep the other two as options"; no flicker, no brightness or colour pulsing.
Deep: "c3 throughout showed the best performance, same issues with ancuti as in the previous
scenes. No halo or clipping noted. For the clips, c3 also renders the best"; "No grain noted. No
flicker noted. The cast is fairly well greyed". All three spec-12 cases (open blue water, distance
haze, deep-water noise) handled by c3; four candidates per case recorded.

**Decisions:** c3 is the default and the Ancuti variants are selectable options: applied as spec
v0.5.3 (D16 amended, owner "approved as 0.5.3"). No failure case was serious; no default, clamp
or scope change follows from the look check. **One finding carried to Phase 2:** the deep clip
shows a discontinuity at a genuine rock-to-open-water lighting step at 0.90 s (owner: "less
pronounced in the original"); WP1.4b showed that neither a window reset at the step nor a 0.5 s
window shrinks it and both add flicker, so it is an input to the Phase 2 temporal design (a
step-aware scheme), not a defect of the colour method.

## Result 4 — Gain-cap noise test (D100; plan section 10 row 4) — KEEP

**Measured (WP1.4b, `afaff0e`):** 8 deepest scuba frames (D 0.209-0.369, six from GX011600) plus
one shallow reference; grid red cap {off, 0.5, 1.0, 2.0} x clamp {1.5, 2, 3, 5, 1000} plus c3 at
each clamp; noise = Immerkaer sigma on fixed flat tiles (Donoho MAD as cross-check; Donoho reads
0 on deep 8-bit HEVC tiles, which the report documents as the quantisation regime). On the
red-lit tiles (source red >= 16/255), median over the 8 frames: **sigma_R 0.736 at cap off, 0.736
at the default 2.0, 0.783 at 1.0, 0.938 at 0.5; c3 0.481**, the lowest on every deep frame. The
default cap binds on 1 of 8 frames. Total red gain (camera WB gain x ours) is about 6x for
Ancuti at the default and about 4x for c3. The one-frame signal that a tighter cap lowers red
noise did NOT hold: it appears only on tiles whose source red is below the quantisation floor
(an inference, per the errata; not spec-bearing).

**Decision (OWNER at CP3, recommended KEEP):** the caps earn their place: a tighter cap raises
noise as D100 expects, and the default cap neither hurts nor binds on most frames. KEEP means no
change to WP3.2, the parameter schema, V1 or the spec. Sub-decisions for WP2.1 (CHARC, from the
same evidence): clamp stays 3.0 (never binds; 1.5 binds on 5 of 8 frames, leaves a cast to R/G 0.80 and
cuts red noise by less than 1 %); N{} range floor 0.02 (DR-14 closes at WP2.1; binds on no measured frame); the capped
alpha is smoothed as a value, not derived from smoothed means (flicker 0.388 against 0.483, 20 % less).

## Result 5 — Staged versus flat statistics (D98; plan section 10 row 5) — ONE STAGE PERMITTED

**Evidence:** `wp1.4-statistics.md` (`91f5775`): mismatch per statistic, residual flicker of
each, both renders at CP2. **Owner at CP2 (2026-10-19):** "I see no flicker in the staged or flat
clips. I see no difference in either of those."

**Decision (CHARC, using the owner's observation):** no visible difference, so a method may
declare one stage; **IF-3 stays staged** (D98). WP2.1 inputs from the same report: smoothing
`median_gaussian` (3-frame median then Gaussian), window 2.0 s **PROVISIONAL** per DR-25(3) and
now with the Result 3 lighting-step finding against it; bounds statistic 0.5/99.5 percentiles
with the 0.02 range floor from Result 4.

## Result 6 — Container spike (D104, D105; plan section 10 row 6) — SIMPLE

**Measured (WP1.5, `3242679`):** one FFmpeg process with NVENC: all MANDATORY and REQUIRED
container items SAME on two chapters; 8 best-effort differences (camera `udta` atoms, firmware
tag, audio timecode tag, brands, encoder/handler tags, track order and flags, sample-entry boxes,
muxer identity edits); the GPMF track, timecode and creation time kept (the `udta` GPMF settings atom is among the best-effort differences). NVENC and libx265 8/10-bit and CUDA
decode PROVEN. Camera HERO13 Black, HEVC Main 8-bit `yuvj420p`, BT.709 FULL range, CFR
30000/1001. Part B's exports re-confirmed the MANDATORY/REQUIRED items SAME on every export
(GX011627 production and resident, GX011625, encode-only and passthrough).

**Decision (CHARC): Gate 6 = SIMPLE; WP3.10 as planned**, with full range honoured end to end
(D54 reading), the B-frame edit-list convention at WP2.1 (DR-15), `udta` repair best-effort in
WP3.10, compare blind spots DR-18. The transport choice (FFmpeg-as-process with a large-block
pipe, or PyAV in-process) is WP2.1's, now with Result 1's pipe measurement as its main input.

## Scope decisions for CP3 (owner), with options and evidence

| Decision | Options | Evidence | Status |
|---|---|---|---|
| N6 target (Result 1) | A tune to 25 min/min / B optimise first / **C both (recommended)** | Part A, Part B | **OPEN: owner** |
| Gain caps (Result 4) | **keep (recommended)** / drop | WP1.4b | OPEN: owner confirms |
| Chapter handling in v1 | keep / defer | inventory b1fd289 | CLOSED 2026-10-19: deferred to v2, spec v0.5.3, plan v1.1 |
| Anything relaxing a mandatory requirement | none proposed beyond N6 | -- | none |
| Photo size limit (Result 2) | only if the largest photo exceeds 16 GB on CPU | Part B photo leg | PENDING photos; not expected |

## Design items decided by the architect from this gate (plan section 9)

For WP2.1: smoothing `median_gaussian` 2.0 s provisional, with a step-aware scheme to design
(Results 3, 5); bounds 0.5/99.5 with a 0.02 range floor (Results 4, 5); one statistics stage
permitted, IF-3 staged (Result 5); clamp 3.0, alpha smoothed as a value (Result 4); CPU/GPU
mechanism CuPy with `memory_estimate_bytes` as the fallback input (Result 2); video I/O SIMPLE,
transport chosen at WP2.1 with large-block writes required (Results 1, 6); proxy resolution per
Part A section 8 and Part B claim 6; defaults from WP1.1 plus CP2 (c3). Debt carried (selected from the register's open items; also open and relevant to Phase 2-3: DR-19 method-agnostic C3 validation, DR-20 D54 untagged-range fallback, DR-23): DR-14 (closes at WP2.1), DR-15, DR-18, DR-25, DR-26, DR-27, DR-28, DR-29, DR-30.

## V14 record

| N5 result | Outcome | Decision | By |
|---|---|---|---|
| 1 Speed | MISSED at 4K: core 3.6x (ancuti2018) / 5.8x (c3); export 4.4x measured (ancuti2018), ~6.6x estimated (c3) | N6 tuned and/or optimisation package: **OPEN** | Owner |
| 2 Memory | HOLDS: 3,682 MiB RSS, 2,860 MiB graphics at 4K; photo PENDING | no limit change | CHARC |
| 3 Look | PASSED shallow and deep; c3 default; lighting-step finding to Phase 2 | spec v0.5.3 applied | Owner (CP2) |
| 4 Noise | caps KEEP recommended; c3 lowest noise | keep | Owner (CP3) |
| 5 Statistics | no visible difference | one stage permitted; IF-3 staged | CHARC |
| 6 Container | SIMPLE meets all mandatory items | WP3.10 as planned | CHARC |

The gate closes when the owner's word on Result 1 (and the KEEP confirmation on Result 4) is
recorded here with its time, and the orchestrator's fact-check is attached.
