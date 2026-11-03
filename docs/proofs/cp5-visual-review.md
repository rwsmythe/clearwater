# CP5 — V2 visual review (owner)

**Pack:** WP5.3 review pack, `work/wp5.3/index.html` (report `docs/reports/wp5.3-review-pack.md`, accept `docs/proofs/wp5.3-accept.md`; 128 items: 126 done, 2 expected HLG refusals; failed 0, pending 0).
**Method:** the owner judged every item in chat with CHARC (gen 13, 2026-11-03 ~05:40-06:20Z) and CHARC transcribed the owner's words into `work/wp5.3/review-sheet.csv` without judging any image. The empty sheet is kept at `work/charc-g13/review-sheet.empty-backup.csv`, the filled sheet at `work/charc-g13/review-sheet.filled-2026-11-03.csv` (md5 `71df41217a70fe5f9e2422632500bf43`).
**Tally of record:** orchestrator gen 36, 2026-11-03T06:23:01Z, from `.worktrees/wp5.3` at `c935b869` (instrument identical to main), the WP5.3 report's config-resolved tally command, exit 0, nothing rebuilt, sheet md5 identical before and after; evidence `clearwater-review-evidence\wp5.3\cp5\` (tally.log, review-sheet.md5, review-sheet.filled.csv); post `e8d5ff0f`.

## Owner's words, verbatim (chat to CHARC, 2026-11-03)

> "6690 through 6737 all preferred, no artifacts; 6739, halo around turtle on the right side."
> "6740 is surface, no preference.  6743 and 6744 both have halo artifacts.  No on 6739, yes on 6743 and 6744."
> "Yes, no artifacts through 6761.  6763 is surface, no preference."
> "Yes, no artifacts through 6771."
> P-Z: "Yes for all except 6802 is surface"
> V-P: "Yes to all except no to 6738; 6738 also has halos"
> V-S: "V-S yesto all, 11627 has halos that begin at the last second."
> V-D: "V-D yes to all, no artifacts"
> V-Z: "V-Z yes to both, 1080 compilation has halos around the legs in  the upper left starting at ~27 seconds."

Transcription rules: "surface, no preference" = `above_surface` yes and `preferred` undecided (the sheet accepts only yes / no / undecided; undecided counts as judged, not preferred); a named artifact = that flag plus the owner's words in `note`; nothing was inferred.

## Tally of record

| Set | Preferred / judged | Halos | Banding | Colour errors | Shimmer | Flicker | Above surface |
|---|---|---|---|---|---|---|---|
| **Headline (P-A, V-P, V-S, V-D)** | **111 / 115 = 96.5 %** | 5 | 0 | 0 | 0 | 0 | 2 |
| P-A photos | 61 / 64 = 95.3 % | 3 | 0 | 0 | — | — | 2 |
| V-P phone clips | 16 / 17 = 94.1 % | 1 | 0 | 0 | 0 | 0 | 0 |
| V-S snorkel clips | 26 / 26 = 100 % | 1 | 0 | 0 | 0 | 0 | 0 |
| V-D deep clips | 8 / 8 = 100 % | 0 | 0 | 0 | 0 | 0 | 0 |
| Candidates (P-Z, V-Z), outside the headline | 10 / 11 = 90.9 % | 1 | 0 | 0 | 0 | 0 | 1 |

Coverage 115 / 115, missing 0, unjudged 0, viewing aids failed 0. Halo rows: IMG_6739 (P-A, preferred no; "halo around turtle on the right side"), IMG_6743 and IMG_6744 (P-A, preferred yes; "halo artifacts"), IMG_6738 (V-P, preferred no; halos), GX011627 (V-S, preferred yes; "halos that begin at the last second"); outside the headline set, compilation-20261010-1080p60 (V-Z, preferred yes; "halos around the legs in the upper left starting at ~27 seconds").

## The D65 reading

D65 / V2: corrected preferred on at least 80 % of the test set AND no obvious artifacts (halos, banding, colour errors, shimmer, flicker). The preference clause is met (96.5 %). The owner observed halos on five headline items (three photos, one phone clip, the last second of one GoPro clip); nothing else was observed. Whether five halo observations in 115 fail the artifact clause is a reading of a mandatory requirement, so CHARC put it to the owner as a decision request in chat (2026-11-03 ~06:20Z) with the recommendation: **CP5 PASS**; the halos recorded as a debt row with the six reproducible cases and a small follow-on package to find their cause before release; WP5.4 (D96 weight-map temporal smoothing) NOT triggered, shimmer 0.

**Owner's word, verbatim, 2026-11-03 ~06:30Z:** "Concur with your D65 recommendation"

## Result

- **CP5: PASS. V2: PASS** (111 / 115 preferred; the five halo observations recorded, not waived: DR-117).
- **DR-117 opened** (halo observations at CP5; the six items; paydown = the follow-on package **WP5.7 halo investigation**, commissioned with WP5.5 at the Phase 5 close).
- **WP5.4 not triggered** (no shimmer seen; V3 passed at WP5.1).
- **Phase 5 gate report `docs/reports/wp5.6-gate-report.md`: FINAL.** Phase 5 verification is complete; release preparation (WP5.5) follows.

## Limits

- The plan's CP5 line also names "views the starter presets"; the pack shows the exported starter presets and the owner did not report on them separately. No preset value is changed by this record; the presets stay as exported at WP5.3 (D75 mapping of record).
- The two surface shots in the headline (IMG_6740, IMG_6763) and one in P-Z (IMG_6802) count as judged-undecided; excluding them would give 111 / 113 = 98.2 %. The tally of record counts them; no exclusion was inferred.
- The owner's viewing device and conditions are not recorded (the pack's pair clips are NVENC HEVC viewing aids; the corrected product outputs are the items of record).
