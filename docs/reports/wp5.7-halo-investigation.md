# WP5.7 halo investigation (DR-117)

Spec v0.5.8. Brief `docs/briefs/wp5.7-brief.md` (FINAL); cell ledger `docs/proofs/wp5.7-ledger.md`
(the measurement of record, part by part, with every command, RED / GREEN and review round).
Instruments: `tools/halo_probe.py` (Parts 1-2), `tools/halo_part3.py` (Part 3), with their tests.
No `src/` change, no default changed, no dependency, no frozen interface touched. Every render ran
through the product's own method code (`methods/ancuti_fusion.py`, `methods/fusion.py`). The
probe runs (Parts 1-2 and the Part 3 crops, `tools/halo_probe.py`) also rebuilt each render from
its saved stages and checked it bit for bit against `method.render`. The Part 3 whole-set renders
(`tools/halo_part3.py`) call `method.render` directly: they ARE the product's `method.render`
output, with no separate equality check. The cell takes no decision: this report states
measurements and CHARC's rulings; the owner's eye is the only artifact oracle.

Evidence aliases. The configured working folder is `C:\Users\rwsmy\clearwater\work\`. The durable
evidence folder is `C:\Users\rwsmy\clearwater-review-evidence\wp5.7\` (`evidence/` below):

| Alias | Path | Durable copy |
|---|---|---|
| `P1` | `work/wp5.7/part1s/` (the Part 1 table of record, step 2B) | `evidence/records/part1s/`: the records, the `table-*.txt` files, the marked crops |
| `P2` | `work/wp5.7/part2/` (the candidate runs; `table-photos.txt`; `logs/runs.txt`, `runs-video.txt`) | `evidence/records/part2/`: the records `<setting>/<item>/<item>.json`, `table-photos.txt`, `logs/`, the two IMG_6739 photo crops of section 5 |
| `P3` | `work/wp5.7/part3/` (the Part 3 window) | `evidence/records/part3/`: `crops/` whole, `logs/`, `n6/` (the bench records, the sidecars, the summary), `wholeset/items/<item>/<item>.json` (the 120 records), the sheet folder; also `evidence/part3/` (runs.txt, the N6, V3, photo and sheet logs, both run scripts) and `evidence/v3/` (v3.json, v3-table.md, the clips, fixtures and legs) |
| scratch | the worktree's `work/c57-p2h2/`, `work/c57-p3r/` (the tabulators and their outputs) | `evidence/cell-scratch/c57-p2h2/`, `evidence/cell-scratch/c57-p3r/` |
| `CP5` | `work/wp5.3/` (the CP5 pack, read-only) | the pack itself |

The durable copies under `evidence/records/` are byte-identical to the working copies (862 files,
checked by Reviewer A round 5). Deliberately NOT copied, as viewing outputs only: the two kept N6
exports (`P3/n6/run-*`, 282 MB) and the whole-set 8-bit renders (`P3/wholeset/items/*/*.png`,
4.5 GB); no figure in this report is read from them. The analysis caches are not copied either.

## 1. Summary

- **Reproduced:** all six owner observations reproduce at the shipped defaults (`c3`) at the
  regions the owner named (section 2).
- **Cause:** fusion input 2 (spec 6.2 step 3). On these frames the N{} bounds are narrow (proxy
  range 0.018-0.051), so the stretched high-pass saturates within one to two sharpening sigmas of
  an edge, and input 2 there becomes `I / 2` or `(I + 1) / 2`: a ring whose height is set by I, not
  by the edge. The Laplacian weight favours input 2 at the edge, and the fusion carries the ring
  into the output. Every qualifying fused band is attributed to input 2. A shallow pyramid is
  REJECTED as a cause. No divergence from spec 6.2 / 6.6 was found, so this is not outcome B.
- **Candidates on the six (Part 2):** the parameter candidates (a) sharpening strength, (e1) N{}
  percentiles, (e2) the AD-4 range floor, and (c) delta make the band smaller but do not show it
  absent: at their strongest settings the band is `none` on 0 of 3 decided photo lines and 0-3 of
  31 decided video frame-lines. (b) pyramid depth changes nothing material. (e3) full-resolution
  bounds shrinks the photo bands slightly and grows the video bands slightly. Candidate (d) clips input 2 to the local range of its unsharpened form (1 sigma). It
  shows the band absent on 2 of 3 photo lines and 21 of 31 video frame-lines.
- **(d) on the 120 other CP5 items (Part 3):** the edge-scan qualifying sides fall from 963 to 39
  (video; three items' stills pending the round-5 re-render, section 5) and from 248 to 13
  (photo). No item's scan rises. Texture changes set-wide: the
  whole-frame std L* falls on 219 of 220 images, by up to 81 % on a group of P-A photos.
  OBSERVATION (CHARC's viewing of the contact sheet; the cell has no eye on it): CHARC, viewing
  the sheet, reports that (d) visibly softens fine texture wherever the local range is narrow,
  not only at halo edges: the fabric pattern on item 01 (IMG_6762; whole-image mean abs 0.0191,
  p99 0.1254) and the grain on item 06 (IMG_6751; 0.0856 / 0.1526). No preference judgement.
- **V3:** (d) passes every asserted bound on WP4.2's two clips, and the shipped leg reproduced the
  record. On `ad14-flicker` the contrast ratio rises (section 6).
- **N6:** shipped runs at 10.95 min/min median and (d) at 12.43 (+13.59 %). As measured, (d) is
  OVER N6 (about 12 min/min) on the clip of record (section 7).
- **Outcome (CHARC's A-prime):** nothing is proposed or shipped for v1.0.x. (d) at 1 sigma is
  stated as an amendment of spec 6.2 step 3. The owner has two options: (i) defer to Phase 6 with
  DR-117 open, or (ii) commission the optimisation now (section 8).

## 2. The six reproductions

Regions and lines are in source pixels (video frames in coded orientation). The owner's words map
to lines the cell chose and recorded with marked crops (ledger Round 0 items 8-9; Part 1 commands).
Under `P1/<item>/`, each item folder holds 16-bit crops of every 6.2 stage, `*-source-marked.png` /
`*-output-marked.png` with the lines drawn, the overviews, and the JSON record.

| Item (owner's words) | Region and lines | Marked crops (`P1/<item>/`) |
|---|---|---|
| IMG_6739 ("halo around turtle on the right side") | the turtle on the right of the frame: shell left edge `1700,2500 -> 2200,2500`, flipper `1560,2300 -> 1810,2300`, right flank `2900,2300 -> 2450,2300` | `photo-source-marked.png`, `photo-output-marked.png` |
| IMG_6743 ("halo artifacts") | object tip `2450,600 -> 1850,600`, lower edge `835,1008 -> 1132,670` | same names |
| IMG_6744 ("halo artifacts") | lower edge `1300,950 -> 1300,450`, tip `2550,200 -> 2100,200` | same names |
| IMG_6738 (phone clip; halos) | fin and turtle flipper, `1130,1296 -> 900,1296` and `1056,600 -> 1056,430`, 49 frames 0-1.7 s | `t0000.167-*`, `t0000.833-*`, `t0001.467-*` |
| GX011627 ("halos that begin at the last second") | fin edge, top right, `3300,420 -> 3700,40`, the 30 frames 21.7-22.7 s | `t0021.788-*`, `t0022.189-*`, `t0022.589-*` |
| compilation-20261010-1080p60 ("around the legs in the upper left starting at ~27 seconds") | three lines on the legs, upper left, 27.0-27.5 s of the CP5 EXCERPT (read in place from `CP5/excerpts/`; source time about 97.9 s) | `t0027.010-*`, `t0027.494-*` |

The stage table of record (step 2B, `P1`; luma, half width 4; "first qualifying" = the first
product stage whose band qualifies; "attributed" = the input carrying the larger share of the
qualifying FUSED band at its peak; band = the fused stage's band over the source's edge contrast C).
A band qualifies on a non-weak edge (|C| >= 0.02) when at least 3 consecutive samples exceed 10 % of
C and 3 x the water-side noise. `undecided` is not evidence either way.

| Item | Line | First qualifying | Attributed | Fused band x C / abs (verdict) | FWHM px (/ sigma) | Wbar2 edge / plateau | N{} range proxy / full |
|---|---|---|---|---|---|---|---|
| IMG_6739 | shell left edge | undecided | undecided | 1.04 / 0.071 (undecided) | 14.7 (0.97) | 0.65 / 0.51 | 0.0512 / 0.0772 |
| IMG_6739 | flipper (weak, C 0.016) | undecided | undecided | 1.55 / 0.025 (undecided) | 2.1 (0.14) | 0.48 / 0.50 | same |
| IMG_6739 | right flank (no clean edge) | input2 | input2 | 3.07 / 0.142 (band) | 7.1 (0.47) | 0.42 / 0.54 | same |
| IMG_6743 | object tip | input2 | input2 | 1.48 / 0.174 (band) | 31.7 (1.48) | 0.63 / 0.52 | 0.0206 / 0.0332 |
| IMG_6743 | lower edge | input2 | input2 | 2.32 / 0.179 (band) | 22.1 (1.03) | 0.61 / 0.56 | same |
| IMG_6744 | lower edge | undecided (input2 at half width 12) | undecided | 2.38 / 0.172 (undecided) | 7.8 (0.36) | 0.67 / 0.58 | 0.0183 (floor) / 0.0321 |
| IMG_6744 | tip | undecided | undecided | 0.80 / 0.118 (undecided) | 4.7 (0.22) | 0.71 / 0.55 | same |
| IMG_6738 | 49 frames x 2 lines (83 non-weak) | input2 16, fused 3, undecided 59, none 5 | input2 17, undecided 57, none 9 | 17 band; 0.833 s flipper 1.45 / 0.163 (band) | 9.6 at 0.833 s (1.34) | 0.60 / 0.57 | 0.0234-0.0239 / 0.0208-0.0230 |
| GX011627 | 30 frames (14 non-weak) | input2 7, fused 2, undecided 5 | input2 9, undecided 3, none 2 | 9 band; 22.122 s 1.84 / 0.162 (band) | 20.3 (1.88) | 0.68 / 0.48 | 0.0349-0.0361 / 0.0318-0.0341 |
| compilation | 3 lines (56 non-weak) | input2 4, fused 2, undecided 35, none 15 | input2 5, undecided 36, none 15 | 5 band; 27.010 s shin (line 3) 3.22 / 0.200 (band) | 6.2 (1.15) | 0.65 / 0.51 | 0.0315-0.0319 / 0.0365-0.0369 |

No compensated, white-balanced or input-1 band qualifies on any frame-line, at half width 4 or 12.
The pointwise stages are measured against the source remapped through their own operation (CHARC
S1). Every qualifying fused band (34 at half width 4) is attributed to input 2: its terms carry
0.89-1.10 of the band at its peak, and the clip's share is 0.000. The pyramids are 7-9 levels deep
(coarsest 17-24 px). The band's FWHM is 0.017-0.26 of one coarsest-level pixel, and the
attribution sits in input 2's levels 0-5.

## 3. Hypothesis verdict

- **The sharpened input carries the band: CONFIRMED.** On every decided line it is the first
  qualifying stage, or `fused` with input 2 attributed. The refinement is that input 2's N{}
  saturates: the band's height is set by the N{} stretch, not by the edge. The bounds measured on
  these frames are very narrow (photos 0.018-0.051, videos 0.023-0.036). On IMG_6744 the 0.02 floor
  binds (AD-4 / DR-14), below the 0.028-0.64 span WP1.4b measured. The stretched high-pass therefore
  reaches 0 or 1 within about 1-2 sigma of any edge stronger than about 0.02. This gives fused bands
  of 1-7 x the source contrast on low-contrast underwater edges. The same saturation amplifies
  noise: input 2's water plateau is 10-20 x noisier than the source's, which is why many lines are
  undecided.
- **The Laplacian weight favours input 2 at the edge: CONFIRMED.** Wbar2 is 0.60-0.71 at the edge,
  against 0.47-0.58 on the water plateau.
- **A shallow pyramid leaves a band at the coarsest scale: REJECTED.** The attribution sits in
  levels 0-5 (1-32 px scales), and the single-scale counterfactual blend has a band of the same
  size. Deeper pyramids, candidate (b), move nothing material.
- **No implementation divergence** from spec 6.2 / 6.6 was found in the code reading (Round 0) or
  by Reviewer A in rounds 0-4. The band is the designed behaviour of input 2 with whole-frame N{}
  bounds on these edges. This is not outcome B.
- **Side observation (AD-4 by design):** the photo bounds measured on the proxy are 0.57-0.66 of the
  full-resolution range. On video the two agree within 15 %. Measuring at full resolution, (e3),
  shrinks the photo bands a little and grows the video bands slightly.

## 4. Each candidate on the six (Part 2)

Settings, switches and how each was applied: ledger Part 2 step 1. A switch is an instrument-only
patch, scoped and restored, and the render-equality check runs under the same switch. The decided
set is 3 photo lines (IMG_6739 line 3, IMG_6743 lines 1 and 2) and 31 video frame-lines (IMG_6738
17, GX011627 9, the compilation 5). Each cell gives the split band / none / undecided after the
candidate; only `none` shows the band absent. Whole-image change is the mean absolute per-value
difference against the run's own shipped-defaults render. Records `P2/<setting>/<item>/<item>.json`;
tables `P2/table-photos.txt` and the worktree scratch `work/c57-p2h2/table-videos.txt` /
`threeway.txt` (ledger Part 2 step 3). Rounding: each figure is its unrounded record value rounded
once, half to even, to the places shown (Reviewer A round 5 corrected five cells that had been
rounded from 4-decimal figures).

| Setting | Photo b / n / u (of 3) | Photo mean abs (6739 / 6743 / 6744) | Video b / n / u (of 31) (+ new) | Video mean abs (6738 / GX / comp) | Video p99 | (i) statistics change | Whole-frame diagnostic, NOT V3 (GX011627 mean L* / std L*) |
|---|---|---|---|---|---|---|---|
| shipped | 3 / 0 / 0 | - | 31 / 0 / 0 | - | - | - | - |
| (a) 0.75 | 3 / 0 / 0 | .010/.017/.017 | not run | - | - | YES | - |
| (a) 0.5 | 1 / 0 / 2 | .020/.033/.034 | 22 / 0 / 9 (+1) | .017/.018/.023 | .086 | YES | 1.10 / 1.10 |
| (a) 0.25 | 1 / 0 / 2 | .030/.048/.048 | 10 / 1 / 20 | .025/.027/.034 | .123 | YES | 1.17 / 1.15 |
| (e1) 0.1/99.9 | 2 / 0 / 1 | .021/.031/.025 | not run | - | - | YES | - |
| (e1) 0.01/99.99 | 2 / 0 / 1 | .039/.049/.054 | 22 / 0 / 9 (+2) | .021/.018/.015 | .100 | YES | 1.48 / 1.11 |
| (e1) 0/100 | 1 / 0 / 2 | .065/.062/.071 | 13 / 3 / 15 | .026/.026/.023 | .134 | YES | 1.60 / 1.13 |
| (e2) 0.05 | 3 / 0 / 0 | .000/.037/.039 | not run | - | - | YES | - |
| (e2) 0.1 | 2 / 0 / 1 | .019/.050/.051 | 22 / 1 / 8 (+2) | .019/.012/.014 | .101 | YES | 0.95 / 1.07 |
| (e2) 0.2 | 1 / 0 / 2 | .029/.056/.057 | 12 / 3 / 16 (+1) | .022/.015/.017 | .121 | YES | 0.98 / 1.08 |
| **(d) unsharpened 1 sigma** | **0 / 2 / 1** | .034/.059/.060 | **1 / 21 / 9** | .024/.015/.018 | .140 | YES | 1.02 / 1.11 |
| (d) unsharpened 3 sigma | 0 / 2 / 1 | .032/.057/.058 | 1 / 17 / 13 | .023/.014/.017 | .137 | YES | 1.02 / 1.11 |
| (d) balanced 1 / 3 sigma (rows) | 0 / 0 / 3 | .030/.055/.056; .025/.052/.053 | not run | - | - | YES | - |
| (d) input1 1 / 3 sigma (rows) | 0 / 1 / 2 | .058/.067/.069; .051/.063/.065 | not run | - | - | YES | - |
| (e3) full-res bounds | 2 / 0 / 1 | .013/.024/.024 | 30 / 0 / 1 (+1) | .002/.006/.003 | .011 | YES | 1.03 / 1.00 |
| (b) 8 | 3 / 0 / 0 | .001/.001/.001 | not run | - | - | NO | - |
| (b) 4 | 3 / 0 / 0 | .002/.002/.002 | 31 / 0 / 0 | .002/.001/.001 | .007 | NO | 1.00 / 1.00 |
| (c) 0.3 | 3 / 0 / 0 | .003/.005/.005 | not run | - | - | NO | - |
| (c) 1.0 | 3 / 0 / 0 | .005/.008/.009 | 25 / 0 / 6 (+1) | .004/.002/.003 | .020 | NO | 0.98 / 0.98 |

- **The whole-frame diagnostic is NOT V3** (Reviewer A round 4 finding 1). It is the population
  standard deviation of the 29 frame-to-frame differences of each WHOLE-frame measure over GX011627
  21.7-22.7 s, candidate over baseline, both smoothed. V3 (spec V3, D112) measures an untouched
  region of a synthetic clip, excludes whole-frame means, and compares smoothed against unsmoothed.
  The fin's entry and the camera's motion enter this diagnostic. V3 itself was measured for (d)
  in Part 3 (section 6).
- **(i) The statistics / cache column** (ledger Part 2 half 2 (i)). (a) and (e1) are fusion
  parameters in the schema hash, so the engine's change detection recomputes the fusion stage.
  (e2), (d) and (e3) change the smoothed fusion statistics (input 2's saliency mean, and the bounds
  for (e3)) without any parameter that names them. They are not in the schema hash, so adopting one
  needs a cache / schema version bump (CHARC C5; DR-14 / spec 7). (e3) also needs a full-resolution
  decode pass per clip. (b) and (c) change no statistic. For `c3`, the disk cache holds proxies
  only, and no candidate changes a proxy.
- **Featured frame-lines** (fused band x C; `*` band, `?` undecided, `-` none). IMG_6738 0.833 s
  L2: shipped 1.45*, (d) 1 sigma 0.03-. GX011627 22.122 s: 1.84*, 0.04-. Compilation 27.010 s line
  3 (the shin, of record): 3.22*, 0.15*. Compilation 27.010 s line 1: 3.87*, 0.05-. The other
  settings are in the ledger's featured-frame table.
- **(d) as an amendment of the paper.** Ancuti 2018's input 2 is `S = (I + N{I - G*I}) / 2`, with
  N{} ONE global linear stretch (spec 6.2 step 3). (d) adds a LOCAL, nonlinear step: input 2 is
  clipped per pixel and channel to the minimum and maximum of `(I + N{0}) / 2` (the unsharpened
  form) over a square window of half side 1 sharpening sigma (the clamped unsharp mask). No 6.7
  parameter reaches it. Adopting it changes the definition of input 2 in spec 6.2 step 3, which is
  a spec change and owner-reserved. It is not a defect fix. CHARC's Q-d ruling made the
  `unsharpened` reference the (d) of record. The literal "local range of input 1" reading moves
  input 2 on every flat region, because input 2 is about `(I + 0.5) / 2` there. The ledger's Q-d
  reproduction shows this, and the `input1` rows shift the channel means by about 0.05.

## 5. (d) 1 sigma on the whole set (Part 3; C1, C2)

The 120 other CP5 items are the pack manifest's 126 `done` items minus the six halo items: 70
photos (P-A 61, P-Z 9) and 50 videos (V-D 8, V-P 16, V-S 25, V-Z 1). Each video is read from the
pack's excerpt where the pack excerpted it. Per photo, two full renders (shipped defaults
unswitched; (d) switched), each from its own proxy statistics. Per video, two whole-clip analyses
and the frames at the pack's three still positions (10 / 50 / 90 %), rendered from each analysis's
smoothed records (150 frames; 51,445 frames analysed per setting). Records:
`P3/wholeset/items/<item>/<item>.json` with both 8-bit renders per frame; the sheet is
`P3/wholeset/sheet-20261103T202754214375Z/` (`summary.tsv` one row per item, `sheet.json`,
`contact-sheet.html`).

**Pending re-statement (Reviewer A round 5 finding 1).** On GX011590, GX011603 and GX011609 all
three stills were taken one frame late: CP5 records a still's ABSOLUTE source time, these clips'
first pts is not 0 (510 and 570 ticks of 1/30000 s), and the instrument matched the still time
on the time from the first frame. The three items are re-rendered at the corrected frames under
`work/wp5.7/part3r/`, and the video figures, counts and contact sheet of this section are
re-stated from that run (ledger, Reviewer A round 5). The other 47 videos and the 70 photos are
unaffected (their selected frames are the stills' frames).

**The edge-band scan** (the brief's "maximum edge-band overshoot found by scanning strong edges";
the cell's design, `tools/halo_part3.py`):

- **Points:** the 48 strongest source-luma gradient points per image, at or above the 99.5th
  percentile, at most one per square cell.
- **Measure:** through each point, a line along the gradient, half-length 8 sigmas, measured from
  both ends with the probe's own `water_band` (half width 4, threshold 0.10, the same noise and
  support rules).
- **Verdict:** each side is band / none / undecided, as on Part 1's lines.

| | Photos (70) | Videos (50; 150 frames) |
|---|---|---|
| Mean abs change: min / median / max | 0.0082 / 0.0215 / 0.0856 | 0.0086 / 0.0172 / 0.0293 |
| p99 abs change: min / median / max | 0.0869 / 0.1249 / 0.1847 | 0.0910 / 0.1201 / 0.1413 |
| Largest channel-mean shift: median / max | 0.0037 / 0.0189 | 0.0028 / 0.0109 |
| Clipped fraction shipped -> (d): max | 0.0041 -> 0.0000 | 0.0047 -> 0.0000 |
| Scan sides b / n / u, shipped | 248 / 1,709 / 4,763 (of 6,720) | 963 / 3,894 / 9,543 (of 14,400) |
| Scan sides b / n / u, (d) | 13 / 3,403 / 3,304 | 39 / 8,196 / 6,165 |
| Items with a qualifying side, shipped -> (d) | 50 -> 11 | 49 -> 18 |
| Largest qualifying band x C, shipped -> (d) | 13.79 -> 2.57 | 15.20 -> 2.05 |
| Shipped `band` sides under (d): band / none / undecided | 12 / 105 / 131 | 37 / 567 / 359 |
| Whole-frame std L*, (d) / shipped: min / median / max | 0.189 / 0.895 / 0.980 | 0.522 / 0.895 / 1.006 |
| Whole-frame mean L* shift: min / median / max | -2.09 / -0.34 / +0.06 | -1.12 / -0.17 / +0.08 |
| Input-2 smoothed saliency mean moved (Lab): min / median / max | - | 0.070 / 0.167 / 0.684 |

Per-item figures: `summary.tsv`, and the ledger's Part 3 results. Readings (measurement, not a
look judgement):

- **The scanned band falls set-wide.** Of the shipped qualifying sides, 567 / 963 (video) and
  105 / 248 (photo) go to `none`. 359 and 131 go to `undecided`, which is not removal. 37 and 12
  stay `band`.
- **Which items' scans rise under (d): none.** By the sheet's rule (more qualifying sides, or a
  larger largest qualifying band) no item rises, and no frame either (`scan_regressions: []`).
- **At the side level, three sides qualify only under (d).** Two are smaller bands that now clear
  their noise level: GX011610 f90, 1.68 -> 0.21 x C, and IMG_6716 f50, 3.56 -> 1.26. On the third
  the band rises: IMG_6800, a photo, side 5 at (5343, 4032), 0.11 -> 0.56 x C.
- **Bands larger under (d) at the side level:** 154 photo sides and 380 video sides, of 21,120.
  On 180 of these the (d) band is at least 0.10 x C on a non-weak edge: 115 go none -> undecided,
  64 stay undecided, and 1 is IMG_6800 above.
- **Texture changes set-wide, most on a group of P-A photos.** The whole-frame std L* falls on
  every photo and on 149 of 150 video frames; the exception is IMG_6742 f10, 13.75 -> 13.83. The
  largest whole-image changes are ten P-A photos, IMG_6746 and IMG_6751-IMG_6759, with a mean
  absolute change of 0.063-0.086 (about 16-22 / 255). At the shipped defaults their scan is
  undecided on 94-96 of 96 sides. Their std L* falls to 0.19-0.45 of shipped (IMG_6751 11.75 ->
  2.57). This is consistent with section 3: the saturated N{} amplifies noise and fine texture,
  and the clip limits that everywhere. std L* does not separate noise from texture, and whether
  this is the look the owner preferred is the owner's judgement.
  OBSERVATION (attributed to CHARC's viewing of the contact sheet, CHARC msg 61fa577714607f97;
  the cell has no eye on it): CHARC, viewing the sheet, reports that (d) visibly softens fine
  texture wherever the local range is narrow, not only at halo edges: the fabric pattern on item
  01 (IMG_6762; whole-image mean abs 0.0191, p99 0.1254) and the grain on item 06 (IMG_6751;
  0.0856 / 0.1526). No preference judgement.
- **The measurement columns for CHARC's two items.** The cell's part is the columns below, from
  the item records (`P3/wholeset/items/<item>/<item>.json`) and the sheet's
  `summary.tsv`. CHARC's set-wide counts were checked against the records and agree: qualifying
  scan sides 963 -> 39 over the 50 videos and 248 -> 13 over the 70 photos, and a clipped fraction
  of 0 under (d) on every image. No preference judgement is made here.

  | # | Item | Frame | Mean abs change | p99 abs change | Max channel-mean shift | Whole-frame std L* shipped -> (d) | Scan b / n / u shipped -> (d) |
  |---|---|---|---|---|---|---|---|
  | 01 | IMG_6762 (V-P) | f90 | 0.0191 | 0.1254 | 0.0086 | 18.37 -> 17.93 | 60/82/146 -> 1/204/83 |
  | 06 | IMG_6751 (P-A) | photo | 0.0856 | 0.1526 | 0.0092 | 11.75 -> 2.57 | 0/0/96 -> 0/0/96 |

  On IMG_6762 the whole-frame std L* moves by only 2.4 %, so a texture loss on part of the frame
  (a fabric pattern) is not visible in the whole-frame measure. The mean absolute and p99 columns
  carry it, alongside the item's input-2 saliency movement (0.684 Lab, the set's largest).
- **No clipped pixel under (d)** on any image.
- **The smoothed statistics:** only input 2's saliency mean moves. White-balance records and
  fusion bounds are unchanged on all 50 videos.

**The contact sheet's 20** (`contact-sheet.html`; shipped | (d), 1200 px a half; 8-bit values, not
display-converted, both halves alike). The selection rule (`select_contact`) takes the 5 videos
whose smoothed input-2 saliency mean moves most (CHARC C3 (3)), then the 15 largest whole-image mean
absolute changes among the rest. Each item is shown at its frame of largest change. No scan
regression item was added.

| # | Item | Group | Frame | Mean abs | p99 | Max shift | Input-2 saliency moved | Scan b / n / u shipped -> (d) |
|---|---|---|---|---|---|---|---|---|
| 1 | IMG_6762 | V-P | f90 | 0.0191 | 0.1254 | 0.0086 | 0.684 | 60/82/146 -> 1/204/83 |
| 2 | GX011601 | V-D | f10 | 0.0135 | 0.0956 | 0.0024 | 0.409 | 3/163/122 -> 0/225/63 |
| 3 | GX011600 | V-D | f10 | 0.0127 | 0.1016 | 0.0025 | 0.329 | 2/109/177 -> 0/173/115 |
| 4 | GX011590 | V-D | f90 | 0.0187 | 0.1110 | 0.0028 | 0.302 | 3/114/171 -> 0/177/111 |
| 5 | GX011625 | V-S | f10 | 0.0172 | 0.1268 | 0.0045 | 0.267 | 15/55/218 -> 0/128/160 |
| 6 | IMG_6751 | P-A | photo | 0.0856 | 0.1526 | 0.0092 | - | 0/0/96 -> 0/0/96 |
| 7 | IMG_6758 | P-A | photo | 0.0700 | 0.1842 | 0.0166 | - | 0/0/96 -> 0/1/95 |
| 8 | IMG_6753 | P-A | photo | 0.0687 | 0.1800 | 0.0179 | - | 0/0/96 -> 0/1/95 |
| 9 | IMG_6755 | P-A | photo | 0.0679 | 0.1834 | 0.0189 | - | 0/0/96 -> 0/3/93 |
| 10 | IMG_6754 | P-A | photo | 0.0674 | 0.1847 | 0.0189 | - | 0/0/96 -> 0/3/93 |
| 11 | IMG_6757 | P-A | photo | 0.0662 | 0.1800 | 0.0184 | - | 0/1/95 -> 0/3/93 |
| 12 | IMG_6746 | P-A | photo | 0.0649 | 0.1716 | 0.0103 | - | 0/2/94 -> 0/10/86 |
| 13 | IMG_6759 | P-A | photo | 0.0641 | 0.1780 | 0.0170 | - | 0/0/96 -> 0/2/94 |
| 14 | IMG_6756 | P-A | photo | 0.0636 | 0.1777 | 0.0174 | - | 0/0/96 -> 0/0/96 |
| 15 | IMG_6752 | P-A | photo | 0.0631 | 0.1780 | 0.0168 | - | 0/0/96 -> 0/0/96 |
| 16 | IMG_6768 | P-A | photo | 0.0526 | 0.1625 | 0.0154 | - | 1/4/91 -> 0/19/77 |
| 17 | IMG_6770 | P-A | photo | 0.0462 | 0.1446 | 0.0120 | - | 0/2/94 -> 0/10/86 |
| 18 | IMG_6767 | P-A | photo | 0.0432 | 0.1564 | 0.0136 | - | 1/10/85 -> 0/42/54 |
| 19 | IMG_6769 | P-A | photo | 0.0431 | 0.1417 | 0.0123 | - | 2/4/90 -> 0/18/78 |
| 20 | IMG_6761 | P-A | photo | 0.0403 | 0.1492 | 0.0109 | - | 0/2/94 -> 0/17/79 |

**The ten undecided lines and the one remaining band (C2), shipped vs (d) 1 sigma.** These are the
11 lines that are not `none` under (d) in Part 2. The video crops come from the window's six probe
runs, `P3/crops/<shipped|candidate>/<item>/t<time>-output.png`, with every render check equal, and
their bands equal Part 2's records for the same pts. The photo crop is Part 2's own,
`P2/defaults|d-unsharpened-1/IMG_6739/photo-output.png`. In words: at shipped every one of the
eleven is a qualifying band of 1.97-7.42 x C, attributed to input 2. Under (d) each falls to
0.10-0.29 x C, which is 2.5-5.6 % of the shipped band on the ten video lines and 7.7 % on
IMG_6739. Ten of them are then UNDECIDED: they show neither a band nor its absence, so an
undecided line is not a removal. The eleventh, the compilation shin (27.010 s line 3, the
featured frame of record), keeps a qualifying band of 0.15 x C attributed to input 2.

| Line | Shipped | (d) 1 sigma |
|---|---|---|
| IMG_6739 photo line 3 | 3.07 band | 0.24 undecided |
| IMG_6738 0.433 / 0.467 / 0.633 s line 2 | 3.26 / 5.40 / 1.97 band | 0.17 / 0.20 / 0.11 undecided |
| GX011627 22.155 / 22.356 / 22.389 / 22.422 / 22.456 s | 3.85 / 7.42 / 4.41 / 4.01 / 6.76 band | 0.10 / 0.18 / 0.14 / 0.15 / 0.29 undecided |
| compilation 27.027 s line 1 | 6.77 band | 0.21 undecided |
| compilation 27.010 s line 3 (shin) | 3.22 band | 0.15 band |

## 6. V3 (C3 as amended by Q2)

V3 was measured on WP4.2's two synthetic clips by WP4.2's own code (`test_wp42_v3_product._v3`,
imported, run in this process inside the switch). The smoothed leg is an export through the
composition root's engine, and the per-frame leg uses `provisional_record`. PASS / FAIL uses the
suite's own predicates `_v3_holds` (V3, 25 %) and `_ad14_holds` (AD-14, 0.5/255). Record
`evidence/v3/v3.json` and `v3-table.md`; log `evidence/part3/v3.log`.

| Clip | Method | Setting | AD-14 /255 per-frame -> smoothed | V3 ratio L* / a* / b* / contrast | Asserted bound | V3 <= 25 % |
|---|---|---|---|---|---|---|
| jitter | c3 | shipped | 0.1006 -> 0.0017 | 0.018 / 0.014 / 0.026 / 0.016 | V3: PASS | yes |
| jitter | c3 | (d) | 0.0569 -> 0.0009 | 0.016 / 0.014 / 0.026 / 0.020 | V3: PASS | yes |
| jitter | ancuti2018 | shipped | 0.1055 -> 0.0017 | 0.012 / 0.016 / 0.024 / 0.012 | V3: PASS | yes |
| jitter | ancuti2018 | (d) | 0.0660 -> 0.0010 | 0.011 / 0.016 / 0.024 / 0.022 | V3: PASS | yes |
| ad14 | c3 | shipped | 0.0416 -> 0.0102 | 0.053 / 0.200 / 0.401 / 0.072 | AD-14: PASS | no |
| ad14 | c3 | (d) | 0.0331 -> 0.0087 | 0.037 / 0.198 / 0.408 / 0.316 | AD-14: PASS | no |
| ad14 | ancuti2018 | shipped | 0.0388 -> 0.0067 | 0.061 / 0.257 / 0.497 / 0.071 | AD-14: PASS | no |
| ad14 | ancuti2018 | (d) | 0.0298 -> 0.0057 | 0.080 / 0.257 / 0.502 / 0.387 | AD-14: PASS | no |

- **Result of record:** (d) passes every clip's asserted bound. Condition 2 is met: the shipped
  leg reproduced WP4.2's four rows of record ("reproduces record: yes" on each).
- **Not buried:** on `ad14-flicker` the CONTRAST ratio rises under (d), c3 0.072 -> 0.316 and
  ancuti2018 0.071 -> 0.387. That clip's asserted bound is AD-14, which passes: c3 0.0331 ->
  0.0087 /255 under (d), against shipped 0.0416 -> 0.0102. Its a* / b* ratios are already over
  25 % at the shipped defaults (c3 0.200 / 0.401), as AD-14's 2026-10-21 extension records.
- **On the jittering clip** the contrast ratio also rises (c3 0.016 -> 0.020, ancuti2018 0.012 ->
  0.022), within 25 %.

## 7. N6 (C4 and CHARC's STOP ruling)

Instrument of record: `tools/export_bench.py`, WP5.2 W52-1's form (GX011627 4K 29.97 fps, c3,
GPU, device frames, auto -> hevc_nvenc, cold, 681 frames), built in-process. The (d) runs ran
inside the switch, with a call counter on `fusion_inputs` in both settings. There were six
alternating runs, one process each, in an EXCLUSIVE window (2026-11-03 15:11-15:40Z, the
orchestrator's seat, nothing else heavy). Logs `evidence/part3/n6-1-shipped.log` ...
`n6-6-candidate.log` and `n6-summary.log`. Records `P3/n6/` (the bench records, the sidecars, the
summary).

| Run | Setting | min/min | s/frame | Peak GPU MiB | memory_check / tied | fusion_inputs calls / clip in effect |
|---|---|---|---|---|---|---|
| 1 | shipped | 10.9467 | 0.3653 | 3,692 | True / True | 1,362 / False |
| 2 | (d) | 12.4234 | 0.4145 | 3,840 | True / True | 1,362 / True |
| 3 | shipped | 10.8630 | 0.3625 | 3,756 | True / True | 1,362 / False |
| 4 | (d) | 12.4346 | 0.4149 | 3,760 | True / True | 1,362 / True |
| 5 | shipped | 11.0729 | 0.3695 | 3,756 | True / True | 1,362 / False |
| 6 | (d) | 12.6115 | 0.4208 | 3,762 | True / True | 1,362 / True |

- **Medians:** shipped 10.9467, (d) 12.4346 min/min. Effect +13.59 %; pair ratios 1.1349,
  1.1447 and 1.1389. VALID True. The shipped median is within 0.5 % of W52-1's cold median of
  record (10.89).
- **CHARC's ruling** (4c60bacc3de85d88): the binding figure is N6 itself, about 12 min/min at 4K
  (D106, spec v0.5.8), not the 10 % threshold. As measured, (d) at 12.43 is OVER N6 on the clip of
  record. It is NOT adoptable in v1.0.x on cost alone.
- **The headroom for any implementation of the clip** is about 1.0 min/min, about +9.6 % on
  GX011627 (12 / 10.95 = 1.096). An optimised clip must fit that budget with margin. D106 also
  records the GUI path at about 11.7-11.8 min/min, with WP4.6's worker margin; the headroom on that
  path is smaller, and it is not measured here.
- **The cost as measured** is the instrument's clip: a per-channel 23 x 23 `ndimage` minimum /
  maximum at 4K, unoptimised. A separable or fused min / max is a candidate at an UNMEASURED cost.

## 8. Outcome A-prime (CHARC C5) and the owner's two options

- **Nothing for v1.0.x.** The report proposes no change for v1.0.x, and the package ships nothing:
  no `src/` path in the diff, and no default changed.
- **What (d) would change.** (d) at 1 sigma (input 2 clipped to the local range of its
  unsharpened form) is an AMENDMENT of spec 6.2 step 3, not a parameter default and not a defect
  fix.
- **Adoption costs:** the spec amendment (owner-reserved); a code path in `fusion_inputs`; a
  cache / schema version bump, because (d) changes input 2's smoothed saliency mean and is not in
  the schema hash (DR-14 / spec 7); and an implementation whose cost fits N6's headroom.
- **Cost as measured** (section 7): (d) at 12.43 min/min against shipped 10.95 on GX011627, which
  is OVER N6 (about 12). Any implementation of the clip has a budget of about +9.6 % (12 / 10.95)
  and must fit it with margin.
- **The owner's choice** (CHARC routes it at the accept, not this package):
  - **(i) DEFER to Phase 6.** DR-117 stays open, with an optimisation item that re-measures the
    clip against N6.
  - **(ii) Commission the optimisation now** as a Phase 6-class package before 1.0.0.
- There is no "adopt now" option. No optimisation spike was run in this package.
- **The parameter alternatives** ((a), (e1), (e2), (c); section 4) keep the paper's input 2 and
  the spec text, and (a) and (e1) are user-reversible per item. At the strongest settings tried
  they show the band absent on no decided photo line and on at most 3 of 31 video frame-lines,
  at a whole-image change of the same order as (d)'s. They were not measured by V3 or N6.

## 9. Limits

- **The oracle.** The owner's eye is the only artifact oracle. The band metric, its noise rule
  (factor 3, extrapolation + AR(1)), the half width 4 of record and the edge-band scan are the
  cell's instruments, not the owner's judgement. `undecided` is not evidence either way.
  Correlated plateau noise at 8 px can still qualify in 7-13 % of seeds (ledger step 2A).
- **Display and viewing.** The previews and crops are 8-bit values, not display-converted (the
  CP5 pack converts video stills BT.1886 -> sRGB), and the halves are alike. A viewer, display
  or scaling difference can change what is seen. The CP5 pairs remain the record of what the owner
  saw.
- **The whole-frame measures are not artifact measures.** std L* does not separate noise from
  texture. The mean absolute change does not separate the halo from texture or tone. The scan
  samples 48 points per image at the strongest source gradients only.
- **GX011627's last second cannot carry V3.** The fin enters and the camera moves, and spec V3
  needs a truly static region on real footage. There, real-footage flicker is the owner's V2
  judgement. The whole-frame temporal diagnostic of section 4 is context, not V3.
- **The timed clip is unoptimised** (section 7). N6 was timed on GX011627 only. The Part 3 walls
  are indicative: the (d) analysis ran second and read the cached proxies.
- **Not every setting was run on video.** Part 2 ran 12 video settings. The photo-only settings
  have no video figure, and only (d) 1 sigma has V3 and N6 figures.
- **The CRLF seat fix.** `wholeset-list` prints CRLF on Windows, and the window's runner kept the
  CR, so the first photo attempt refused every id before any write (exit 2 in 1 s). The
  orchestrator added `| tr -d '\r'` to the runner's two list lines (`run-part3.sh.orig` kept; both
  durable). Follow-up note, not fixed here: `wholeset-list` should write LF.
- **A stale label outside the owned files.** `tools/export_bench.py:99` holds
  `D106_MIN_PER_MIN = 25.0`, the 0.5.4 interim figure, so its ROW lines print "meets D106 25", (d)
  included. The min/min figures are unaffected. A follow-up for the bench's owner.
- **The write-path limits, rounds 2-4, adjudicated out of envelope.** These belong to a seat-run
  tool on the owner's single-user laptop:
  - Confinement is checked at start-up and does not pin ancestors against a concurrent junction
    swap or a link planted in the fresh staging folder.
  - On POSIX, `Path.rename` can replace an empty directory, so the collision refusals are Windows
    guarantees.
  - The product's cache store writes through a junction pre-planted under a cache-entry name; this
    was routed to CHARC as possible product debt.
  - The commit point of a publication is the final rename: an interrupt after it leaves the new
    publication and the kept old one.

## 10. Evidence, durable copies, review

- **Durable** (`C:\Users\rwsmy\clearwater-review-evidence\wp5.7\`, the evidence aliases above):
  - the dispatches (`cell/`) and the Reviewer A transcripts (`A/r0` ... `A/r5`);
  - `records/part1s/`, `records/part2/`, `records/part3/`: every record, table, log, crop and the
    sheet folder this report cites; 862 files, byte-identical to the working copies (Reviewer A
    round 5);
  - `cell-scratch/c57-p2h2/`, `cell-scratch/c57-p3r/`: the scratch tabulators and their outputs;
  - `part3/`: `runs.txt`, `n6-*.log`, `n6-summary.log`, `v3.log`, `wholeset-photos.log`,
    `wholeset-sheet.log`, `run-part3.sh` and `.orig`; and `v3/`.
- **Not copied, deliberately** (viewing outputs; no figure here is read from them): the two kept
  N6 exports `P3/n6/run-*` (282 MB), the whole-set 8-bit renders `P3/wholeset/items/*/*.png`
  (4.5 GB) and the analysis caches.
- **Review:** Reviewer A (Codex) rounds 0-5 are in the ledger's cumulative round table. Round 3
  converged the instrument; round 4 corrected the conclusions (V3 relabelled, three-way counts);
  round 5 found the three one-frame-late video items, the sheet's staging-folder count, the
  `n6-summary` re-read and five rounding cells (ledger, Reviewer A round 5). Reviewer B and the
  gate follow.
