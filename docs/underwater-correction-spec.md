# Clearwater — Underwater Image & Video Correction Tool

## Specification

**Version:** 0.5.7 (draft)
**Date:** 29 October 2026
**Status:** Second review (10 concerns, 6 planning questions) worked through with the owner and incorporated. Requirements are stable for implementation planning. Items left to the design stage are listed in Section 14.1. Open decisions, including scope items that depend on test results, are listed in Section 14.2.

**Change log**
- 0.1 — Initial draft.
- 0.2 — Incorporated review decisions D11–D32; named project.
- 0.3 — Incorporated review decisions D33–D46.
- 0.4 — Incorporated adversarial review findings F1–F24 as decisions D47–D96. Added 3C definition, color management, video metadata, plug-in interface contract, failure handling, measurable acceptance criteria, feasibility gate, caching, licensing. Amended D24, D25, D41, D42, D46. Added Section 15 (review traceability).
- 0.5 — Incorporated review of v0.4 as decisions D97–D117. Added staged statistics, white-balance gain clamp, prototype gate (replacing the feasibility gate), footage inventory, container spike, export performance target, CPU/GPU-portable core, provisional preview, photo memory limits and CPU fallback, synthetic flicker test, cache versioning, output chroma format. Deferred ProRAW/DNG. Amended D14, D30, D31, D42, D46, D57, D61, D62, D64, D68, D69, D71. Withdrew D23, D77, D78, D79. Split Section 14 into design items and open decisions; added Section 15.2.
- 0.5.1 — Text only (owner-approved 2026-10-15): recorded the measured target machine (WP0.1 environment report, 2026-10-14) in D117, Section 12, Section 14.2 (item closed) and Section 15.2 Q1. No decision changed.
- 0.5.2 — Text only (owner-approved 2026-10-15): D60 closed — no GoPro `.LRV` proxies exist for this project (sidecars deleted at cloud upload); Clearwater generates its own proxy (Section 7.3). Section 14.1 item closed; the `.LRV` leg removed from the analysis-speed measurement (Section 7.3, Section 13.1). No decision changed in substance.
- 0.5.5 — Text only (owner-approved 2026-10-27: "Apply D75 erratum"): D75's parenthetical updated from the provisional AD-12 mapping (cq 18/23/28, crf 18/23/28) to the mapping measured and ruled at WP3.10 on 2026-10-27 (NVENC cq 22/26/30 with a 0.24 bit/pixel ceiling scaled 1, 1/2, 1/4; libx265 crf 21/26/30). No decision changed; D75 already deferred to AD-12.
- 0.5.7 — Input container (owner-approved 2026-10-29 ~17:50Z: "update the spec to include .mov", after the owner's iPhone videos arrived as QuickTime `.MOV` files, brand `qt`, HEVC): Section 5.2 accepts the MP4 and QuickTime containers (`.mp4`, `.mov`), which FFmpeg reads, decodes and verifies through one demuxer; Section 8.3 states that output is written as MP4 with the `.mp4` extension for a `.mov` source (a consequence of D25, not a new decision). No decision changed. The product's video suffix set and output naming follow in a work package.
- 0.5.6 — Text only (owner-approved 2026-10-29: "Apply N6 erratum"): the N6 body in Section 10.2 still carried the original 3.3 min/min figure (10 minutes for a 3-minute clip; 0.11 s per frame at 30 fps, 0.056 s at 60 fps) that D106 (tuned 0.5.4, Gate 1 option C) had already replaced with the interim of about 25 minutes per minute of 4K footage; N6 now states D106's interim and the WP5.2 re-set. No decision changed; the register item DR-64 closes.
- 0.5.4 — Prototype gate outcomes and WP2.1 design decisions recorded (owner-approved 2026-10-20 ~16:00Z: "Gate 1: Option C.  2. Keep.  3. approve 0.5.4"). D106 tuned to an interim 25 min/min with a named Phase 3 optimisation package (Gate 1, option C); D100 caps KEPT; D98 compared (no visible difference, one stage permitted); D94 reading by presentation effect (AD-22); G12 gains force-CPU and its first-run defaults; D75 names and provisional mapping; D63 HEIC rule (AD-24); N1 exception for the Windows pipe buffer (AD-23); Section 6 defaults, 7.2 smoothing default, Section 12 proxy-bounds measurement recorded; 14.1 items marked DECIDED with their AD numbers; chapter- and recording-group remnants removed from 7.3, V10 and V17. Design: `docs/architecture.md`, `docs/decisions.md`.
- 0.5.3 — Owner decisions 2026-10-19 (CP1, CP2; owner-approved 2026-10-19: "approved as 0.5.3"). (a) D16 amended: 3C is the default channel-compensation method; Ancuti 2018 (red, optional blue) remains selectable. (b) Chapter handling deferred to v2: D21, D33, D80, D82 and the recording-group suffix of D83 marked deferred; Section 5.5 replaced; G11 and V12 deferred; the chapter clauses removed from G7, V3 (and D64's seam threshold), V4, Sections 8.2 and 8.3 and UC2/UC3; Section 14.2 item closed. Each file is one clip in v1.

---

## 1. Purpose

Clearwater is a desktop GUI tool that corrects color cast, contrast loss, and haze in amateur underwater photos and video, producing visually pleasing results without training data or manual labeling.

**Primary goal:** visual quality (natural, pleasing appearance), not physically exact color.

---

## 2. Decision log

Decisions marked *(amended)* were changed by a later decision; the body of the spec reflects the amended form. Decisions marked *(withdrawn)* no longer apply.

| # | Decision |
|---|---|
| D1 | Goal is visual quality for photography/video |
| D2 | No capability to label data or train models |
| D3 | Implemented in Python, run by the user |
| D4 | NVIDIA GPU available |
| D5 | Shooting conditions: shallow and deeper natural light (no artificial lights) |
| D6 | v1 covers both photos and video |
| D7 | Interface is a GUI |
| D8 | v1 correction method: Ancuti color balance + fusion |
| D9 | Source cameras: GoPro HERO13-class (video), iPhone 15-class (photos) |
| D10 | Video processing is offline (not real-time) |
| D11 | Correction methods implement a common plug-in interface allowing depth maps and multi-frame inputs (contract defined by D61, D97) |
| D12 | Batch processing is in v1 |
| D13 | Presets (save/load named parameter sets) are in v1 |
| D14 | *(amended by D116)* Photo inputs: HEIC, JPEG, PNG, TIFF |
| D15 | Video inputs: standard GoPro color profiles only; GP-Log and HDR not supported in v1 (HDR defined by D73) |
| D16 | *(amended 0.5.3)* Both channel-compensation methods (Ancuti 2018 and 3C) included, user-selectable; 3C is the default (owner, CP2 2026-10-19: Ancuti 2018 over-corrects red on skin and white objects in the shallow footage; 3C matched the scene) |
| D17 | All parameters exposed; technical parameters in an Advanced panel |
| D18 | Video flicker handled by two-pass approach: analyze, temporally smooth whole-frame statistics, render |
| D19 | No scene-cut detection; inputs are raw, continuous camera clips |
| D20 | Audio passed through unchanged; frame rate, resolution, and timing preserved exactly (see D94) |
| D21 | *(deferred to v2, 0.5.3)* GoPro chaptered recordings treated as one clip for smoothing; output as matching chapters |
| D22 | Photo output: PNG, user-selectable 8-bit or 16-bit |
| D23 | *(withdrawn by D116)* ProRAW/DNG inputs: original left untouched, corrected PNG exported |
| D24 | *(amended by D63)* EXIF metadata preserved, except fields made invalid by processing |
| D25 | *(amended by D76)* Video output: MP4, HEVC only; 10-bit when source is 10-bit, optionally 10-bit for 8-bit sources |
| D26 | Video encoder: user choice of NVENC or software encoder |
| D27 | GUI before/after: split-view slider only (no side-by-side, no drag-and-drop) |
| D28 | GUI framework: PySide6 |
| D29 | Platform: Windows 11 officially supported; code kept portable |
| D30 | *(amended by D107)* Core written once to run on CPU or GPU; GPU is the expected export path, CPU the fallback |
| D31 | *(amended by D106)* Export performance target set by D106; no other hard performance targets for v1 (memory limits D68, D110) |
| D32 | Project name: Clearwater |
| D33 | *(deferred to v2, 0.5.3)* Chapter grouping: automatic from GoPro file naming, shown to the user for review and adjustment |
| D34 | Output location: source folder by default; user setting to choose a different output folder |
| D35 | Existing output files are never overwritten; a number is appended instead |
| D36 | Output suffix defaults to `_corrected`, editable in settings |
| D37 | Presets stored in the user's app-data folder; can be exported and imported as files |
| D38 | Clearwater ships with starter presets |
| D39 | Internal processing in 32-bit float; quantization only at export |
| D40 | Gain cap applies to the compensated channel(s) of Ancuti 2018; Advanced panel (defined by D50, D52; retention subject to D100) |
| D41 | *(amended by D56)* Live preview at screen resolution while adjusting; closely approximates export, exact at 1:1 zoom |
| D42 | *(amended by D59, D72, D108)* Video preview uses temporally smoothed statistics once analysis has produced them, and a provisional per-frame preview before that; analysis runs on clip open |
| D43 | Progress indicator with cancel, and non-blocking GUI |
| D44 | On cancel, the partial output file is deleted; completed files kept |
| D45 | Cancel during batch stops the whole remaining batch |
| D46 | *(amended by D64–D67, D112)* Verification criteria (originally V1–V7, now V1–V18), with measurable thresholds; UIQM/UCIQE not used |
| D47 | 3C works in YCbCr using a fixed BT.709 matrix (internal only) |
| D48 | 3C strength: one Basic slider scaling κ and λ from the paper's 1.0/0.7 ratio; κ and λ individually adjustable in Advanced |
| D49 | Gain cap does not apply to 3C; cap controls hidden when 3C is selected |
| D50 | Ancuti 2018 gain cap is a global strength cap: per image/frame, the mean added amount is limited to a set multiple of the channel's original mean |
| D51 | Ancuti 2018 blue compensation included as an option, off by default |
| D52 | Separate red and blue gain caps |
| D53 | Photos keep source primaries end to end (e.g., Display P3); matching ICC profile embedded in PNG output |
| D54 | Video color tags read from the stream; if missing or unexpected, assume BT.709, limited range, and warn |
| D55 | Output video color tags and range match the source |
| D56 | All spatial parameters size-relative (fraction of short side); pyramid depth set by minimum level size |
| D57 | *(amended by D97)* All whole-frame statistics (incl. sharpening normalization, saliency reference) are analyzed and smoothed, in dependency order |
| D58 | Flicker test covers color, brightness and contrast |
| D59 | Parameter changes recompute statistics from a low-resolution proxy cache built during analysis |
| D60 | GoPro .LRV proxies not available for this project (sidecars deleted at cloud upload, owner 2026-10-15); Clearwater generates its own proxy (7.3). CLOSED. |
| D61 | *(amended by D97)* Plug-in interface: ordered statistic stages, analyze per stage, smoothing declaration, parameter and stage dependencies, render, parameter schema |
| D62 | *(amended by D105)* Video output fidelity: timing, audio sync and display orientation mandatory; creation date/time, GPMF telemetry, timecode and camera atoms best-effort |
| D63 | Photo orientation: pixels rotated, Orientation tag reset; thumbnail dropped, dimensions updated, Software set, HEIC gain/depth maps dropped. HEIC rule (0.5.4, AD-24, provisional until an owner photo is read): the file's `irot`/`imir` transforms are applied by the reader; the EXIF Orientation tag is applied additionally only when no `irot` transform is present |
| D64 | *(amended by D112; amended 0.5.3)* V3 thresholds: flicker ≤ 25% of the unsmoothed baseline, measured on a synthetic clip (the chapter-seam threshold is deferred with chapter handling) |
| D65 | V2 pass rule: corrected preferred on ≥ 80% of the test set and no obvious artifacts |
| D66 | V7: UI responds within 100 ms during processing |
| D67 | New tests: identity round trip, color tags/ICC, orientation, preview vs export, naming/non-overwrite, cancel cleanup, chapter grouping, preset round trip |
| D68 | *(amended by D110)* Peak RAM ≤ 16 GB, for video and photos; graphics memory measured as a second limit |
| D69 | *(amended by D101, D106)* Prototype gate before the core build; CPU and GPU per-frame time measured against the D106 budget |
| D70 | Analysis pass has a cancel control |
| D71 | *(amended by D113)* Analysis proxies and source-only statistics cached in app data, keyed with a cache format version; default limit 20 GB, editable; oldest removed first; clear-cache button |
| D72 | Timeline scrubbing shows proxy frames while dragging, full-resolution corrected frame when stopped |
| D73 | "Unsupported HDR" = HLG or PQ transfer tag; GoPro plain "HDR video" mode output verified with a test clip at design; GP-Log detection best-effort |
| D74 | Unavailable encoder options shown disabled with a reason |
| D75 | Video quality set by named levels High / Standard / Draft, mapped per encoder (mapping AD-12, verified at WP3.10 on the owner's footage, 0.5.5: NVENC HEVC cq 22 / 26 / 30 with a rate ceiling of 0.24 bit/pixel scaled 1 / 1/2 / 1/4, libx265 crf 21 / 26 / 30) |
| D76 | Optional 10-bit output for 8-bit sources, off by default |
| D77 | *(withdrawn by D116)* DNG variants: whatever the raw library reads; others refused with a clear message |
| D78 | *(withdrawn by D116)* Raw development output: Display P3, display-encoded |
| D79 | *(withdrawn by D116)* Raw development look: generic first; closeness to Apple's rendering revisited after testing |
| D80 | *(deferred to v2, 0.5.3)* Batch: chapter grouping reviewed once up front, then runs unattended |
| D81 | Batch failure: skip the failed item, log it, continue, report at end |
| D82 | *(deferred to v2, 0.5.3)* Non-consecutive chapter groups: warn, then reset smoothing at each break |
| D83 | *(amended 0.5.3)* .LRV/.THM sidecars excluded from input (the grouping clause and the per-recording-group collision suffix are deferred with chapter handling) |
| D84 | Photo name clashes across formats resolved by collision numbering |
| D85 | Outputs written to a temporary name and renamed on success; leftovers cleaned on next start |
| D86 | Truncated/corrupt video: process the readable portion and warn |
| D87 | Disk space estimated before export; out-of-space during export fails cleanly |
| D88 | Rotating log file in app data |
| D89 | Settings and last-used parameters persist between sessions |
| D90 | Preset files record their method and a format version |
| D91 | Clearwater version and parameters embedded in output metadata; on by default, can be turned off |
| D92 | Reproducibility: same inputs and parameters give output identical within tolerance |
| D93 | Distribution: free, open source, GPL-2.0-or-later; bundled library license compatibility confirmed at packaging |
| D94 | Per-frame timestamps, start offset and edit list preserved and verified. *(0.5.4 reading, AD-22)* Where only the encoder's composition-offset convention differs from the source's, "copied, not recalculated" is read by presentation effect: pts sequence, start offset, duration and first displayed frame exact; the as-written `media_time` may differ |
| D95 | Variable-frame-rate input processed with timing preserved; smoothing window defined in time, not frames (tested per D115) |
| D96 | Weight-map temporal smoothing is conditional: added to v1 if V3 fails or shimmer is seen in V2 |
| D97 | Whole-frame statistics are analyzed in ordered stages; each stage is measured using the smoothed results of the stages before it. A method may declare a single stage |
| D98 | Staged analysis is the v1 default; staged and flat (single-stage) results were compared in the prototype gate (owner, CP2 2026-10-19: no visible difference); a method may declare one stage; the plug-in interface stays staged |
| D99 | White-balance gain clamp: a maximum per-channel white-balance gain, in the Advanced panel, applying with either compensation method |
| D100 | *(decided 0.5.4)* Gain caps (D40, D50, D52) are a fidelity-versus-noise control, not a noise mitigation; **KEPT** (WP1.4b noise test, owner 2026-10-20: a tighter cap raises red noise on the deep frames as expected; the default cap 2.0 binds on 1 of 8 deep frames; 3C is the lowest-noise setting on every deep frame) |
| D101 | Prototype gate replaces the feasibility gate, with six recorded results: speed, peak memory, look check, gain-cap noise test, staged-versus-flat comparison, container spike |
| D102 | Footage inventory precedes the prototype gate; gaps are filled by new footage or the dependent test is marked pending |
| D103 | Look check uses an informal bar: the owner judges, with no numeric threshold; failure cases and the decision on each are recorded |
| D104 | Container spike: one real chapter re-encoded with no correction; source and output compared; result selects the video I/O approach and library |
| D105 | Video fidelity priorities: per-frame timing, start offset, audio sync and display orientation are mandatory; other video metadata is best-effort |
| D106 | *(tuned 0.5.4, Gate 1 option C)* Export performance target: **interim, about 25 minutes of processing per minute of 4K footage on the owner's laptop** (measured unoptimised 2026-10-19: core 0.395 s/frame Ancuti 2018, 0.639 s/frame 3C; production export 14.6 min/min Ancuti, about 22 estimated with 3C), end to end; a named Phase 3 optimisation package (device-resident pipeline, upload/download overlap, FFT or recursive Gaussian for 3C; the large-buffer transport is already in the build) targets about 10 min/min and the figure is re-set from the WP5.2 re-measure. The original intent of about 3.3 min/min is recorded as not reachable at 4K on this machine by any identified route. 5.3K is supported but best-effort on speed |
| D107 | Core is written so the same code runs on CPU or GPU from the start |
| D108 | Provisional preview: on clip open the current frame is shown at once using its own unsmoothed statistics while analysis runs in the background |
| D109 | Sparse analysis (statistics from a subset of frames) is held in reserve, considered only if measured analysis speed is unacceptable |
| D110 | Memory limits cover photos as well as video: the largest supported photo is tested, and graphics memory is measured |
| D111 | Automatic CPU fallback when an image or frame is estimated not to fit in graphics memory; no tiled processing in v1 |
| D112 | V3 flicker is measured on a synthetic clip, in the region not touched by the disturbance; real-footage flicker is judged in V2 |
| D113 | Cache key includes a cache format version; the cache holds only results that depend on the source file alone; smoothing is always recomputed |
| D114 | Output video chroma subsampling and pixel format match the source |
| D115 | One variable-frame-rate sample is added to the V4 test set |
| D116 | ProRAW/DNG input deferred to a later version; refused with a clear message in v1 |
| D117 | Usage profile: clips typically a few minutes or less; 4K the expected maximum resolution, without limiting the tool to it; target machine is the owner's laptop with 32 GB RAM; confirmed 2026-10-14: AMD Ryzen 9 7940HS, NVIDIA RTX 4070 Laptop GPU, 8 GB |

---

## 3. Scope

### 3.1 In scope (v1)
- Correction of photos and video with Ancuti fusion, using Ancuti 2018 compensation (red, optional blue) or 3C.
- Temporal consistency handling for video (Section 7).
- Color management for photos and video (Section 6.5).
- GUI with before/after preview, parameter controls, presets, batch processing, and export.
- Metadata preservation for photos, and timing, audio sync and orientation preservation for video (Section 8).

### 3.2 Out of scope (v1)
- Physics-based correction (Sea-thru + monocular depth).
- Diffusion-based correction (Osmosis) and learned video methods (UnDIVE).
- Model training of any kind.
- Footage lit by video lights or strobes.
- GP-Log and HDR (HLG/PQ) video.
- Scene-cut detection and edited footage.
- Real-time / live processing.
- Official macOS/Linux support.
- HEIC auxiliary images (HDR gain map, depth map) in output.
- ProRAW/DNG input (D116).
- Tiled processing of large images (D111).

### 3.3 Future versions
- The plug-in interface (Section 10.1) exists so later methods such as Sea-thru + depth or multi-frame video methods can be added without reworking the GUI or I/O layers.
- ProRAW/DNG input can be added later through the same input layer.

---

## 4. Use cases

- **UC1 — Single photo:** Load a photo, view before/after, adjust parameters, export.
- **UC2 — Single video clip:** Load a clip, scrub and preview corrected frames, adjust parameters, export.
- **UC3 — Batch:** Apply one parameter set to multiple files, export all unattended.
- **UC4 — Presets:** Save, load, apply, import, and export named parameter sets; start from shipped starter presets.

**Usage profile (D117):** clips are typically a few minutes or less; 4K is the expected maximum resolution, though the tool is not limited to it.

---

## 5. Inputs

### 5.1 Photos
| Format | Notes |
|---|---|
| HEIC | iPhone default; requires a HEIC-capable reader. Auxiliary images (gain map, depth) ignored |
| JPEG | — |
| PNG | 8- and 16-bit |
| TIFF | 8- and 16-bit |

- Embedded color profiles are honored (Section 6.5).
- Orientation metadata is applied by rotating pixels on load (Section 8.1).
- ProRAW and DNG files are refused with a clear message in v1 (D116).

### 5.2 Video
- MP4 or QuickTime container (`.mp4`, `.mov`; 0.5.7), H.265/HEVC or H.264. Both are ISO base media files read by the same FFmpeg demuxer; the iPhone records QuickTime (`qt` brand), the GoPro MP4.
- 8-bit and 10-bit sources handled without truncating 10-bit data.
- Standard color profiles only.
- Resolutions and frame rates up to the camera's maximum (including 5.3K and 8:7 modes). 4K is the resolution at which the performance target is measured (D106).
- Constant and variable frame rate accepted; timing preserved (Section 7.5).

### 5.3 Unsupported video inputs
- **HDR:** any stream tagged with an HLG or PQ transfer characteristic is refused with a clear message.
- GoPro's plain "HDR video" mode is believed to produce SDR output; this is verified with a test clip at design before it is processed as SDR (D73).
- **GP-Log:** detection is best-effort, as the format may carry no distinguishing tag; undetectable cases are documented as a known limitation.

### 5.4 Damaged inputs
- Truncated or corrupt video sources (e.g., last chapter after a battery failure) are processed up to the readable portion, with a clear warning (D86).
- Files that cannot be read at all are refused with a clear message.

### 5.5 Chaptered recordings (deferred to v2)
The footage inventory of 2026-10-18 found no chaptered recording; the camera keeps a 17-minute take in one file. Chapter grouping, review and cross-chapter smoothing (D21, D33, D80, D82) are deferred to v2 (owner, CP1 2026-10-19). In v1 every input file is its own clip: smoothing starts and ends within the file. `.LRV` and `.THM` sidecars are still excluded from input (D83). Nothing in v1 prevents v2 from adding grouping on top.

---

## 6. Correction method

### 6.1 Reference algorithms
- **Color Balance and Fusion for Underwater Image Enhancement** — Ancuti et al., IEEE TIP 27(1), 2018.
- **Color Channel Compensation (3C)** — Ancuti et al., IEEE TIP 29, 2020.

The formulas in the reference papers are authoritative over the summaries below. Where a paper leaves a value unspecified (e.g., the gamma for fusion input 1), the chosen default is documented in the design.

### 6.2 Pipeline (per image/frame)
1. **Channel compensation** (user-selectable; Section 6.3).
2. **White balance** — gray-world style balancing of the compensated image.
   - **Gain clamp (D99):** each channel's white-balance gain is limited to a maximum (default 3.0, 0.5.4), set in the Advanced panel. The clamp applies with either compensation method, and to the gains actually used for rendering (the smoothed gains for video).
   - When the clamp limits a gain, the frame keeps some color cast instead of gaining noise. This is the pipeline's control for deep-water noise.
3. **Derive two fusion inputs** from the white-balanced image:
   - Input 1: gamma-corrected version.
   - Input 2: sharpened version, `S = (I + N{I − G∗I}) / 2`, where N{} is a linear normalization (histogram stretch) whose bounds are whole-frame statistics (Section 7).
4. **Compute weight maps** for each input: Laplacian contrast, saliency (Achanta et al.), and saturation. Normalize across inputs with the paper's regularization, `W̄k = (Wk + δ) / (ΣWk + K·δ)`, δ = 0.1, K = 2.
5. **Multiscale fusion** — Laplacian pyramid of inputs blended with Gaussian pyramid of weights, then collapsed.

### 6.3 Channel compensation methods
3C is the default method (D16, amended 0.5.3); Ancuti 2018 remains selectable.

#### 6.3.1 Ancuti 2018 (red, optional blue)
- **Red:** `Irc = Ir + α·(Ḡ − R̄)·(1 − Ir)·Ig` (additive; channel values in [0, 1]).
- **Blue (optional, off by default; for turbid or plankton-rich water):** `Ibc = Ib + α·(Ḡ − B̄)·(1 − Ib)·Ig`.
- α is the compensation strength (paper default 1).
- **Gain cap (global strength cap):** per image/frame, the effective strength is reduced so that the mean added amount does not exceed a set multiple of the channel's original mean. Red and blue have separate caps (D50, D52), default 2.0 each, disabled by an empty value (0.5.4, AD-8). Because the cap is computed from whole-frame statistics, it is smoothed over time along with them.
- **What the cap is for (D100):** it limits how much of the compensated channel is derived from green, which preserves true detail in that channel. It does not reduce noise. Less compensation leaves the channel's mean lower, so the gray-world step applies a larger gain to the original, noisy channel. The cap therefore trades fidelity against noise and overlaps with α.
- **Status:** the caps are kept for now. The prototype gate measures red-channel noise on a deep frame with the caps on and off, and the caps are kept or dropped from that result.

#### 6.3.2 3C (Color Channel Compensation)
- **Working space:** YCbCr using a fixed BT.709 matrix, applied to the display-encoded working image (D47). The paper reports results in Lab, YUV and YCbCr are similar.
- **Equations:** `Cr' = Cr − κ·M·G{Cr}`, `Cb' = Cb − λ·M·G{Cb}`, where G{} is a Gaussian local mean with large spatial support. In the paper, κ applies to the red–green opponent channel (a\*) and λ to the blue–yellow channel (b\*); in YCbCr these correspond most closely to Cr and Cb respectively. The paper's underwater defaults are κ = 1.0 and λ = 0.7. The correspondence is confirmed at design.
- **Mask M:** 0 where mean(R, G, B) > 0.85, 1 elsewhere, smoothed with a Gaussian; protects bright regions.
- **Kernel sizes:** expressed relative to image size (Section 6.6); defaults chosen at design with reference to the paper's comparison of kernel sizes.
- **Strength controls:** one Basic slider scales κ and λ together from the 1.0/0.7 ratio; κ and λ are individually adjustable in the Advanced panel (D48).
- **Gain cap:** does not apply; cap controls are hidden when 3C is selected (D49). The white-balance gain clamp (Section 6.2) still applies.
- 3C is followed by the white balance step (step 2), as the paper intends it as pre-processing before color constancy.

### 6.4 Precision
- All processing in 32-bit floating point, normalized to [0, 1]; quantization only at export.

### 6.5 Color management
- **Working encoding:** the pipeline operates on display-encoded RGB in the source's primaries. Neither method requires linearization (3C uses YCbCr, a linear transform of the encoded values).
- **Photos:** embedded ICC profiles (or equivalent color data) are read. Source primaries are kept end to end; Display P3 sources stay Display P3. The PNG output embeds a matching ICC profile (D53).
- **Video in:** matrix, range, primaries and transfer characteristics are read from the stream. If missing or unexpected, BT.709 with limited range is assumed and the user is warned (D54). Chroma upsampling to full resolution is performed before processing.
- **Video out:** matrix, range, primaries and transfer tags match the source (D55). Chroma subsampling and pixel format also match the source, normally 4:2:0 for GoPro footage (D114). The resampling method in each direction is fixed at design, because it affects the identity round trip (V9).

### 6.6 Resolution independence
- All spatial parameters (sharpening blur, Laplacian, saliency blur, 3C kernels and mask smoothing) are expressed as a fraction of the image's short side (D56).
- Pyramid depth is set by a minimum coarsest-level size rather than a fixed count; the Advanced "pyramid" control adjusts that size.
- Consequently, a screen-resolution preview closely approximates the full-resolution result, and a 1:1 view is exact (verified by V8).

### 6.7 User-adjustable parameters

The parameter set is defined per method through the parameter schema (Section 10.1). For v1:

**Basic panel**
- Compensation method (3C, the default / Ancuti 2018)
- Compensation strength (α for Ancuti 2018; combined κ/λ for 3C)
- Blue compensation on/off (Ancuti 2018 only)
- White balance strength
- Sharpening strength (fusion input 2)
- Blend with original (0–100%; 0 = fully corrected, 100 = the original, 0.5.4 AD-8)

**Advanced panel**
- Red gain cap and blue gain cap (Ancuti 2018 only; subject to D100)
- κ and λ individually (3C only)
- Maximum white-balance gain (D99)
- Gamma (fusion input 1)
- Pyramid minimum level size

---

## 7. Video temporal consistency

### 7.1 Problem
The method computes whole-frame statistics per frame. Applied independently, these fluctuate and cause flicker in color, brightness, sharpening and contrast; shallow-water caustics make this worse. The whole-frame statistics include at least:
- channel means for compensation and the derived gain-cap limits;
- white-balance gains;
- the sharpening normalization bounds N{};
- the saliency reference value(s).

**The statistics are chained.** Each is measured on the output of the stage before it: white-balance gains on the compensated image, and the sharpening bounds and saliency reference on the white-balanced image. If every statistic is measured once and smoothed independently, the gains applied at render no longer match the image they are applied to, which leaves a residual flicker. Statistics are therefore analyzed in stages (D97).

Each method declares its stages and statistics through the plug-in interface (Section 10.1). With 3C, compensation uses local means only, so the chain starts at white balance.

### 7.2 Approach
1. **Decode pass:** every frame is decoded once and a low-resolution proxy of it is stored (Section 7.3). Runs in the background when a clip is opened, shows progress, and can be cancelled (cancel returns to an unloaded state).
2. **Staged statistics (D97):** for each stage, in the method's declared order:
   - the stage's statistics are computed for every frame from the proxies, using the smoothed results of earlier stages;
   - a centered (non-causal) temporal filter is applied to each statistic the method declares smoothable. The window is defined in time (seconds), not frames (D95). Default (0.5.4, AD-3, provisional): a 3-frame median followed by a Gaussian with a 2.0 s window. A genuine lighting step inside a clip is not hidden by the window (deep look check 2026-10-20); a step-aware variant is a design task for the analysis engine.
3. **Render pass:** correct each frame using the smoothed statistics. Used for both preview and export.

- A single-stage (flat) method is permitted. Staged and flat results are compared in the prototype gate (D98).
- Smoothing spans chapter boundaries within a consecutive recording group and resets at breaks (Section 5.5).
- No scene-cut handling; inputs are continuous clips.

**Provisional preview (D108).** When a clip is opened, the current frame is shown immediately, corrected with its own unsmoothed statistics, while analysis runs in the background. The preview switches to the smoothed statistics when they are available. On a still frame the two differ little, since the difference is flicker.

**Analysis speed.** The prototype gate measures analysis speed with software decode and hardware decode (the `.LRV` leg is not available, D60). Sparse analysis, which takes statistics from a subset of frames, is held in reserve and considered only if those are all too slow (D109). It risks missing fast changes such as caustics and leaves gaps in the scrubbing proxies.

### 7.3 Parameter changes and the proxy cache
- When a parameter changes, the statistics that depend on it, and every later stage, are recomputed from the proxy cache rather than by re-decoding the source (D59), then re-smoothed.
- For live preview, only frames within reach of the displayed frame's smoothing windows need recomputing. The recompute scheme is a design item.
- Statistics with a closed-form dependency on a parameter or on an earlier stage may be updated directly without touching the proxy.
- GoPro `.LRV` files are not available for this project (D60, closed 2026-10-15); Clearwater generates its own proxy.
- **Cache (D71, D113):**
  - Stored in app data, identified by source file size, modification date, and a cache format version. A version mismatch triggers re-analysis.
  - Holds only results that depend on the source file alone: the proxies, and any statistics that depend on neither parameters nor other frames.
  - Smoothing, and statistics that depend on parameters or earlier stages, are always recomputed from the cache.
  - Reopening a clip skips the decode pass.
  - Default limit 20 GB, editable in settings; oldest entries removed first; a clear-cache button is provided.

### 7.4 Weight maps (conditional scope)
Per-pixel weight maps are computed per frame in v1. Temporal smoothing of weight maps is added to v1 if the V3 flicker test fails or shimmer is observed in V2 visual review (D96).

### 7.5 Audio and timing
Timing and audio sync are the mandatory part of video output fidelity (D105).

- Audio passed through unchanged.
- Per-frame presentation timestamps, start offset and MP4 edit list are copied from the source, not recalculated (D94).
- Variable-frame-rate input is processed with its original timing preserved (D95).

---

## 8. Outputs

### 8.1 Photos
- **Format:** PNG, user-selectable 8-bit or 16-bit, with an embedded ICC profile matching the source primaries.
- **Metadata:** all EXIF preserved except fields made invalid by processing (D63):
  - pixels are physically rotated per the source orientation, and the Orientation tag is set to normal;
  - the embedded thumbnail is removed;
  - pixel dimensions are updated;
  - Software is set to Clearwater;
  - HEIC auxiliary images (HDR gain map, depth map) are dropped.
- **Provenance:** Clearwater version and parameters embedded in metadata; on by default, can be turned off (D91).

### 8.2 Video
- **Format:** MP4, HEVC. 10-bit when the source is 10-bit; optional 10-bit output for 8-bit sources, off by default (D76). Chroma subsampling and pixel format match the source (D114).
- **Encoder:** NVENC or software, user-selectable. Encoder capabilities (including 10-bit support) are detected at startup; unavailable options are shown disabled with a reason (D74).
- **Quality:** named levels (e.g., Standard / High / Very High), each mapped to settings for each encoder (D75).
- **Color tags** match the source (Section 6.5).
- **Mandatory fidelity (D105):**
  - per-frame timestamps, start offset and audio sync (Section 7.5);
  - display orientation: the output plays in the same orientation as the source, by keeping the rotation flag or an equivalent.
- **Best-effort metadata (D105):** creation date/time, GPMF telemetry track, timecode track and camera-settings atoms are kept where the chosen video I/O approach preserves them at low cost. Items that are not preserved are documented as a known limitation.
- **Provenance:** Clearwater version and parameters embedded in metadata; on by default, can be turned off.

### 8.3 Location and naming
- **Location:** same folder as the source by default; a setting allows a different output folder.
- **Naming:** source filename plus suffix, default `_corrected`, editable in settings. Photos change extension to `.png`. Examples: `GX010123.MP4` → `GX010123_corrected.MP4`; a `.mov` source is written as MP4 and takes the `.mp4` extension (`IMG_1234.MOV` → `IMG_1234_corrected.mp4`; D25, 0.5.7); `IMG_1234.HEIC` → `IMG_1234_corrected.png`.
- **Collisions:** existing files are never overwritten; a number is appended (`_corrected_2`, …). This also resolves cross-format photo clashes such as `IMG_1234.HEIC` and `IMG_1234.JPG` (D84).
- Source files are never modified.

### 8.4 Safe writing
- Outputs are written to a temporary name and renamed to the final name only on success (D85).
- Leftover temporary files from a crash are cleaned up on the next start.
- On cancel or failure, the temporary file is deleted (consistent with D44).
- Before export, required disk space is estimated and the user warned if insufficient; running out of space during export fails cleanly without leaving a partial output (D87).

---

## 9. GUI requirements

- **G1** Open photos and videos via file dialog.
- **G2** Before/after comparison via split-view slider.
- **G3** Parameter controls (Section 6.7) generated from each method's parameter schema, in Basic and Advanced panels. Preview updates live at screen resolution while adjusting; exact at 1:1 zoom.
- **G4** Video: timeline scrubber. While dragging, proxy frames are shown; when stopped, the full-resolution corrected frame is shown (D72). Preview uses temporally smoothed statistics once analysis has produced them, and the provisional preview before that (D108).
- **G5** Analysis runs in the background on clip open, shows progress and can be cancelled.
- **G6** Presets: save, load, rename, delete, import from file, export to file. Starter presets included.
- **G7** Batch queue: add multiple files; apply one parameter set or preset; run unattended; report per-item success, warnings and failures at the end. A failed item is skipped and logged, and the batch continues (D80, D81).
- **G8** Export and batch show progress with a cancel control:
  - cancel deletes the in-progress temporary output;
  - completed files are kept;
  - in batch mode, cancel stops the whole remaining batch.
- **G9** GUI stays responsive during analysis, export and batch processing (work runs off the UI thread).
- **G10** Clear messages for unsupported, damaged, or untagged inputs (Sections 5.1, 5.3, 5.4, 6.5), including ProRAW/DNG.
- **G11** *(deferred to v2, 0.5.3)* Chapter grouping review: display detected groups, allow adjustment, warn on non-consecutive groups.
- **G12** Settings: output folder, output suffix, PNG bit depth, video encoder, quality level, 10-bit-for-8-bit option, provenance on/off, cache size limit, clear cache, force CPU processing (Advanced; AD-9). First-run defaults (0.5.4): PNG 16-bit; encoder "auto" (NVENC when available, else the software encoder; provenance records the encoder actually used); quality Standard; cache 20 GB; provenance on; force CPU off.
- **G13** Settings and last-used parameters persist between sessions (D89).

Framework: PySide6.

---

## 10. Non-functional requirements

### 10.1 Plug-in interface
Every correction method implements (D61, D97):
- **Statistic stages:** an ordered list. Each stage declares:
  - the whole-frame statistics it produces;
  - which of them are temporally smoothed;
  - which parameters they depend on;
  - which earlier stages they depend on.
- **analyze(stage, frame, params, earlier statistics) → statistics:** the per-frame statistics for one stage, given the smoothed results of earlier stages.
- **render(frame, params, statistics) → frame:** correction using externally supplied (e.g., smoothed) statistics.
- **Parameter schema:** names, types, ranges, defaults, and Basic/Advanced placement, so the GUI is method-agnostic.
- Optional context inputs (e.g., depth map, neighboring frames) for future methods.

A method with one stage is valid; this is the flat scheme. Dependencies let the host redo only the affected work when a parameter changes.

The GUI, video and I/O layers depend only on this interface.

### 10.2 Resources and performance
- **Target machine (D117):** the owner's laptop, 32 GB RAM. AMD Ryzen 9 7940HS (8C/16T), NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB dedicated memory (confirmed 2026-10-14 by tools/environment_report.py).
- **N1 Platform:** Windows 11 officially supported; no OS-specific code without the architect's approval. Approved exception (0.5.4, AD-23): the enlarged anonymous-pipe buffer for frame transport on Windows, with an automatic portable fallback that yields identical frames and timestamps.
- **N2 Language:** Python.
- **N3 Compute (D107):** the core is written so the same code runs on CPU or GPU from the start. GPU is the expected path for export; CPU is the fallback.
- **N4 Memory (D68, D110, D111):**
  - peak RAM ≤ 16 GB, for video (including 5.3K 8:7) and for the largest supported photo;
  - graphics memory is measured and treated as a second limit;
  - if an image or frame is estimated not to fit in graphics memory, it is processed on CPU automatically;
  - frame parallelism and buffering are bounded to meet these limits.
- **N5 Prototype gate (D101):** before the core build, a prototype records six results:
  1. **Speed:** per-frame time on CPU and on GPU against the N6 budget, a timing of a full clip (sustained, not one frame), and analysis speed.
  2. **Peak memory:** RAM and graphics memory, including the largest photo in the inventory.
  3. **Look check (D103):** both compensation methods on the owner's photos and extracted video frames, plus one short clip processed frame by frame. Informal bar; failure cases and decisions recorded.
  4. **Gain-cap noise test (D100):** red-channel noise on a deep frame with caps on and off.
  5. **Staged versus flat statistics (D98).**
  6. **Container spike (D104):** one real chapter re-encoded with no correction; source and output compared on tracks, atoms, timestamps, edit list and color tags; the color tags and range the camera writes are recorded; NVENC and 10-bit confirmed in the chosen build.
- **N6 Performance target (D106):** export takes, as an interim target, at most about 25 minutes of processing per minute of 4K footage on the owner's laptop, end to end including decode and encode (D106, tuned 0.5.4 under Gate 1 option C; the original intent of about 3.3 minutes per minute is recorded there as not reachable at 4K on this machine by any identified route). Measured at 4K in the owner's actual recording modes; the figure is re-set from the WP5.2 re-measure after the named optimisation package. 5.3K is supported but best-effort on speed. No other hard performance targets for v1.

### 10.3 Quality and robustness
- **N7 Code quality:** well documented, Pythonic, each processing stage independently testable.
- **N8 Non-destructive:** source files never modified; existing outputs never overwritten.
- **N9 Logging:** rotating log file in app data (D88).
- **N10 Reproducibility:** same inputs and parameters give output identical within a defined tolerance (D92).
- **N11 Presets:** preset files record their method and a format version (D90).

### 10.4 Licensing
- **N12** Clearwater is free, open-source software under GPL-2.0-or-later (D93).
- **N13** Bundled dependency licenses (e.g., GPL x265/FFmpeg builds, LGPL PySide6 and HEIC libraries) are checked for compatibility at packaging, and required notices are included.

---

## 11. Verification and acceptance

Standard underwater quality metrics (UIQM, UCIQE) are unreliable and are not used. Thresholds marked "tunable" are starting values that may be adjusted with justification after initial testing.

- **V1 Correctness:** unit tests for each stage (both compensation methods, red/blue compensation, gain caps, 3C mask and kernels, white balance and its gain clamp, normalization, weights, pyramid fusion, staged statistics ordering), including edge cases: uniform images, near-zero red channel, 10-bit input.
- **V2 Visual review:** on a test set of your own photos and footage spanning shallow and deeper conditions, the corrected result is preferred over the original for ≥ 80% of items, and no obvious artifacts (halos, banding, color errors, shimmer, flicker) are observed (D65).
- **V3 Temporal consistency (tunable) (D112):**
  - **Synthetic clip:** a still image repeated as frames, with a moving disturbance (e.g., a colored patch or a brightness ripple) over part of the frame.
  - In the region the disturbance never touches, the per-frame mean of color (a\*, b\*), brightness (L\*) and a contrast measure are computed on the output.
  - flicker = standard deviation of the frame-to-frame differences of each measure;
  - pass if flicker with smoothing ≤ 25% of flicker with per-frame (unsmoothed) statistics.
  - Whole-frame means are not used: per-frame gray-world forces every frame's mean color to gray, which hides the flicker being tested.
  - Flicker on real footage is judged in V2. The same region-based measurement may be run on a real clip if a truly static one is available.
- **V4 Video I/O fidelity:**
  - mandatory: output matches source frame count, per-frame timestamps, start offset, resolution, bit depth (or the selected 10-bit option), chroma format, audio and display orientation; color tags match the source;
  - best-effort: which of creation time, GPMF, timecode and camera atoms are present is recorded;
  - the test set includes one variable-frame-rate sample (D115).
- **V5 Photo I/O fidelity:** EXIF preserved except D63 fields; orientation correct for rotated and portrait sources in multiple viewers; ICC profile present and matching; selected bit depth honored.
- **V6 Unsupported inputs:** HLG/PQ test files refused with a clear message; ProRAW/DNG refused with a clear message; untagged video triggers the BT.709/limited warning; damaged files handled per Section 5.4.
- **V7 Responsiveness:** UI responds within 100 ms during analysis, export and batch processing (D66).
- **V8 Preview vs export:** screen-resolution preview vs downsampled full-resolution output differ by less than a threshold set at design; 1:1 view exact.
- **V9 Identity round trip:** with every stage set to its neutral value (compensation and white balance strength 0, sharpening 0, gamma 1, and blend fully toward the corrected result), each stage reduces to identity and the output matches the input within a small color-difference tolerance for photos and video. This exercises the full decode → process → encode path, including color tags and ICC handling.
- **V10 Naming and non-overwrite:** collision numbering, cross-format photo clashes, and no source or existing output ever overwritten.
- **V11 Cancel and failure cleanup:** cancel and simulated failures (crash, disk full) leave no partial outputs; leftover temporaries removed on next start.
- **V12** *(deferred to v2, 0.5.3)* **Chapter grouping:** correct automatic grouping, sidecar exclusion, warning and smoothing reset for non-consecutive groups.
- **V13 Preset round trip:** export then import reproduces identical parameters, method and version.
- **V14 Prototype gate:** all six N5 results recorded, each with the decision it led to.
- **V15 Memory:** peak RAM ≤ 16 GB on a 5.3K 8:7 clip and on the largest supported photo; peak graphics memory recorded; the CPU fallback engages when an image does not fit in graphics memory.
- **V16 Performance (tunable):** export meets the N6 target at 4K in the owner's recording modes (interim 25 min/min per D106; re-set after the Phase 3 optimisation package at WP5.2).
- **V17 Cache:** reopening an unchanged clip skips the decode pass; a cache format version mismatch triggers re-analysis.
- **V18 Provisional preview:** on opening a clip, a corrected frame is shown before analysis completes, and it updates to the smoothed statistics afterwards.

---

## 12. Constraints and known risks

- **Deep-water noise:** boosting a nearly absent channel amplifies noise and compression artifacts, especially in 8-bit video; mitigated by the white-balance gain clamp and the optional 10-bit output. The gain caps do not mitigate it (Section 6.3.1).
- **Gray-world on open water:** gray-world assumes the scene averages to gray; a frame that is mostly blue water is pushed toward red or magenta. Checked in the prototype look check.
- **Distance haze:** the method ignores range, so far regions stay hazy.
- **Export speed:** the N6 budget is about 18 times tighter than the earlier 2 s gate at 30 fps, and about 36 times at 60 fps. A CPU implementation is expected to miss it at 4K and above; GPU is not guaranteed to meet it at 5.3K 60 fps. On a laptop, sustained speed under heat may be lower than a single-frame timing suggests.
- **Memory:** one full-color 32-bit float buffer is about 100 MB at 4K, 190 MB at 5.3K 16:9, 300 MB at 5.3K 8:7, 290 MB for a 24 MP photo and 580 MB for a 48 MP photo (exact pixel dimensions to be confirmed by the inventory). Fusion holds many such buffers, plausibly 2–4 GB per 5.3K frame and 6–12 GB for a 48 MP photo; these totals are extrapolations, not measurements. A large photo may not fit in graphics memory, hence the CPU fallback. If the largest photo exceeds 16 GB of RAM even on CPU, a size limit is revisited.
- **Container fidelity:** FFmpeg-based muxing is believed to write its own edit list and timing tables and to drop data tracks and vendor atoms by default; unverified until the container spike. The spike decides whether D94 can be met as written with the simple approach or needs a repair pass.
- **Staged recompute cost:** a parameter change invalidates all later stages; live preview depends on limiting the recompute to nearby frames.
- **Statistics on downscaled frames:** normalization bounds computed on downscaled frames differ from full-resolution extremes: measured 2026-10-19 on real 4K frames, the 540-line proxy's 0.5/99.5-percentile bounds are 11-14 % narrower than the full frame's and steadier frame to frame. Accepted as the method's defined behaviour (AD-4): statistics are measured on the proxy and used unchanged for preview and export, with a 0.02 floor on the range.
- **HDR mode identification:** GoPro's plain "HDR video" mode output not yet verified (D73); GP-Log may be undetectable.
- **PNG metadata support:** PNG stores EXIF in an `eXIf` chunk and color profiles in `iCCP`; viewer support varies.
- **Encoder builds:** 10-bit software HEVC requires a high-bit-depth x265 build; NVENC 10-bit requires a supported GPU.
- **Licensing:** compatibility of each bundled library with GPL-2.0-or-later must be confirmed at packaging.

---

## 13. Development milestones

1. **Footage inventory (D102):** a script reads each file's resolution, frame rate, bit depth, color tags, chapter numbering and `.LRV` presence; the owner sorts scenes into categories (shallow with caustics, deeper, open blue water, photos shallow and deeper, chaptered recording). Gaps are filled later or the dependent test is marked pending.
2. **Prototype gate (N5, V14):** six recorded results and the decisions they lead to, including the video I/O approach, the CPU/GPU mechanism, the fate of the gain caps, and staged versus flat statistics.
3. Core pipeline and both compensation methods, portable across CPU and GPU, with unit tests (V1, V9).
4. Video analysis (staged statistics), smoothing, proxy cache, and I/O fidelity (V3, V4, V15–V17).
5. GUI, presets, batch, settings.
6. Verification against V2–V18.

Test material generated by the project, not supplied by the owner: the synthetic flicker clip, HLG and PQ samples, an untagged file, a truncated file, and a variable-frame-rate sample.

---

## 14. Deferred and open items

### 14.1 Deferred to design

*(0.5.4: decided in WP2.1; the decision log is `docs/decisions.md`.)*

- Verification of GoPro plain "HDR video" mode output with a test clip. — PENDING a clip (none in the inventory; AD-16).
- GP-Log detection method and limitations. — DECIDED AD-16.
- Feasibility of `.LRV` files as proxies (frame alignment) — CLOSED 2026-10-15: no `.LRV` files exist for this project's footage (D60).
- Temporal smoothing filter type and default window (in seconds). — DECIDED AD-3 (median then Gaussian, 2.0 s, provisional).
- Proxy resolution and storage format. — DECIDED AD-5 (540-line proxy; store container by measured test in WP3.12).
- Robust statistic choices for normalization bounds. — DECIDED AD-4.
- Confirmation of the κ→Cr, λ→Cb correspondence for 3C. — CONFIRMED WP1.1.
- Direction of the "Blend with original" slider (which end is the original) and the neutral value of each parameter used by V9. — DECIDED AD-8.
- Default values where the papers leave them unspecified (e.g., gamma for input 1, kernel fractions, minimum pyramid level size, gain cap multiples) and the default maximum white-balance gain. — DECIDED AD-8.
- Mapping of named quality levels to each encoder's settings. — DECIDED AD-12 (provisional).
- Reproducibility tolerance (N10), identity round-trip tolerance (V9), and preview-vs-export threshold (V8). — DECIDED AD-11.
- Preset file format and starter preset values. — DECIDED AD-13 (values shown at CP5).
- Stage definitions for each compensation method, and the scheme for limiting recompute during live preview. — DECIDED AD-6, AD-7.
- Mechanism for running the core on CPU or GPU, the GPU library, and how graphics memory need is estimated for the fallback. — DECIDED AD-1.
- How CPU or GPU use is reported to the user, and whether it can be overridden. — DECIDED AD-9.
- Video I/O library and approach, following the container spike, including how best-effort metadata is carried. — DECIDED AD-2, AD-23.
- Chroma resampling method in each direction. — DECIDED AD-10.
- Design of the synthetic flicker clip (disturbance type, measured region). — DECIDED AD-14.
- Behavior of scrubbing, parameter changes and export while analysis is still running. — DECIDED AD-15.

### 14.2 Open decisions

**For the owner**
- **Laptop CPU and graphics card** — CLOSED 2026-10-14: AMD Ryzen 9 7940HS (8C/16T), NVIDIA GeForce RTX 4070 Laptop GPU, 8 GB dedicated memory (tools/environment_report.py). Consequence for the open sub-questions: an Ada-generation card has NVENC HEVC 10-bit and AV1 encode, so NVENC 10-bit availability is expected; the container spike (WP1.5) verifies it in the chosen FFmpeg build. Whether N6 is realistic and when the CPU fallback engages are measured by WP1.2.
- **Minimum specification for other users.** Whether the owner's machine is the only target that must perform well, or a minimum (for example, no NVIDIA card) is stated. The second adds testing of the CPU-only path.

**Decided by the footage inventory**
- **Chapter handling in v1** (D21, D33, D80, D82, D83) — CLOSED 2026-10-19: DEFERRED to v2 (owner, CP1; the inventory of 2026-10-18 found no chaptered recording among 34 GoPro files). Section 5.5.
- Photo resolution (24 MP or 48 MP) and the video recording modes in use.

**Decided by the prototype gate**
- Gain caps kept or dropped (D100). — CLOSED 2026-10-20: KEPT (0.5.4).
- Staged or flat statistics (D98).
- Whether sparse analysis is needed (D109).

**Decided by later testing**
- Weight-map temporal smoothing (D96).

---

## 15. Review traceability

### 15.1 Adversarial review of v0.3 (24 findings)

Each finding was checked against the source papers or published specifications where it relied on external facts; no false positives were found. Some resolutions below were amended in v0.5; the decision log shows the current form.

| Finding | Severity | Resolution |
|---|---|---|
| F1 3C undefined in pipeline | Critical | D47, D48, D49; §6.3.2 |
| F2 No color-encoding contract | Critical | D53, D54, D55; §6.5 |
| F3 Preview depends on resolution | Major | D56; §6.6; V8 |
| F4 Unsmoothed whole-frame statistics | Major | D57, D58; §7.1; V3 |
| F5 Exact preview updates infeasible | Major | D59, D60; §7.3 |
| F6 Gain cap undefined | Major | D50; §6.3.1 |
| F7 Video metadata unspecified | Major | D62; §8.2; V4 |
| F8 Interface can't express two-pass scheme | Major | D61; §10.1 |
| F9 Orientation and stale EXIF | Major | D63; §8.1; V5 |
| F10 V3 untestable | Major | D64; V3 |
| F11 Memory/throughput understated | Major | D68, D69; N4, N5; §13 |
| F12 Analysis cancel and caching | Major | D70, D71, D72; §7.2–7.3 |
| F13 "HDR" ambiguous | Minor | D73; §5.3 |
| F14 Encoder details | Minor | D74, D75, D76; §8.2 |
| F15 ProRAW feasibility and look | Minor | D77, D78, D79 (withdrawn by D116) |
| F16 Batch vs chapter review | Minor | D80, D81; G7 |
| F17 Chapter edits and naming gaps | Minor | D82, D83, D84; §5.5, §8.3 |
| F18 Failure handling, atomic writes | Minor | D85, D86, D87, D88; §8.4 |
| F19 Persistence and reproducibility | Minor | D89, D90, D91, D92 |
| F20 Licensing | Minor | D93; §10.4 |
| F21 Timing fidelity | Minor | D94, D95; §7.5 |
| F22 Blue compensation omitted | Minor | D51, D52 |
| F23 Status line contradiction | Minor | Status line revised; D96; §7.4 |
| F24 Verification gaps | Minor | D65, D66, D67; V8–V15 |

### 15.2 Review of v0.4 (10 concerns, 6 planning questions)

The concerns rest on reasoning from the pipeline's formulas and on the reviewer's understanding of tool behavior. Figures quoted in them are estimates, not measurements. Anything that needs measuring has been routed to the prototype gate.

| Item | Type | Resolution |
|---|---|---|
| C1 Statistics are chained; interface treats them as flat | Concern | D97, D98; §7.1–7.3, §10.1 |
| C2 Gain cap does not mitigate noise | Concern | D99, D100; §6.2, §6.3.1, §12 |
| C3 Nothing tests the look early | Concern | D101, D102, D103; N5; §13 |
| C4 Container fidelity has no gate | Concern | D104, D105; §8.2; N5; V4 |
| C5 Throughput and the wait on open | Concern | D106, D107, D108, D109; §7.2; N3, N6; V16, V18 |
| C6 Memory worst case is photos | Concern | D110, D111; N4; V15 |
| C7 V3 measure cannot see the flicker | Concern | D112; V3 |
| C8 Cache key has no version | Minor | D113; §7.3; V17 |
| C9 Output chroma format unstated | Minor | D114; §6.5, §8.2 |
| C10 Variable-frame-rate effort | Minor | Largely withdrawn; D95 kept; D115; V4 |
| Q1 Target machine | Question | 32 GB RAM; Ryzen 9 7940HS; RTX 4070 Laptop 8 GB (closed 2026-10-14) |
| Q2 Clip profile and acceptable export time | Question | D106, D117 |
| Q3 ProRAW use | Question | Not used; D116 |
| Q4 Test footage | Question | Originals available, coverage unknown; D102 |
| Q5 Who implements | Question | Multi-agent; carried into the implementation plan |
| Q6 Update spec or carry as plan risks | Question | Spec updated (this revision) |

---

## 16. References

- Ancuti, C. O., Ancuti, C., De Vleeschouwer, C., & Bekaert, P. (2018). Color Balance and Fusion for Underwater Image Enhancement. *IEEE Transactions on Image Processing*, 27(1), 379–393. https://research.dial.uclouvain.be/handle/2078.5/253495
- Ancuti, C. O., Ancuti, C., De Vleeschouwer, C., & Sbert, M. (2020). Color Channel Compensation (3C): A Fundamental Pre-Processing Step for Image Enhancement. *IEEE Transactions on Image Processing*, 29, 2653–2665. https://research.dial.uclouvain.be/handle/2078.5/169548
- Companion research notes: `underwater-imagery-correction-research.md`
