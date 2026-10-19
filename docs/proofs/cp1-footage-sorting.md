# CP1 -- Footage sorting (owner checkpoint record, COMPLETE 2026-10-19)

CP1 is the owner's checkpoint (plan section 5): each clip and photo gets a category, gaps
are noted, and chapter handling in v1 is decided from the inventory. This record is kept by
CHARC in the owner's words with their time. It REPLACES the living record of 2026-10-15
(history: `git log -- docs/proofs/cp1-footage-sorting.md`). Inventory of record:
`docs/reports/inventory-2026-10-18.md` (main `b1fd289`; 35 videos, 0 photos, 0 errors,
0 chaptered recordings).

## The owner's word

- 2026-10-15 ~05:25Z (chat to CHARC): "I have put 4 videos in there. They are all shallow
  snorkel videos. I am working on downloading the rest which will include deeper (~20m) scuba
  videos. I will also work on getting still pictures which will be all shallow snorkel."
- 2026-10-15 ~10:50Z: **"shallow confirmed"** (partial CP1 on GX011625-GX011628).
- 2026-10-18 (chat to CHARC): "The videos are downloaded. I placed snorkel videos in the
  snorkel folder and scuba videos in the scuba folder." On the misnamed 318 MB file: "It looks
  like it is a compilation video. We can rename it and potentially use it as a stress test
  since it has transitions." Then: "renamed to Edits\compilation-20261010-1080p60.mp4, no
  photos for now they are still pending, go."
- 2026-10-19 ~01:20Z (chat to CHARC, to CHARC's folder-wise proposal and the chapter
  recommendation): **"folder-wise confirmed. No open-water or static clips. concur with
  defering chapter handling."**

## Categories (owner)

| Folder | Files | Category | Notes |
|---|---|---|---|
| `Snorkel/` | 26: GX011603-GX011628 | shallow (snorkel) | 4K 29.97 HEVC 8-bit BT.709 full range; caustics per clip are noted by the WP1.3 instrument (only GX011627 showed faint ones on the first four) |
| `SCUBA/` | 8: GX011589-93, GX011598, GX011600, GX011601 | deeper (~20 m scuba) | 4K 29.97 HEVC; largest clip GX011600, 8.9 GB, 17.4 min |
| `edits/` | 1: `compilation-20261010-1080p60.mp4` | stress case (outside the plan's categories) | cloud-made H.264 1080p59.94 compilation, 180 s, hard scene transitions; kept on purpose for a later smoothing stress test, not Part B |
| photo, shallow | 0 | PENDING | owner adds stills later; dependent tests marked pending (D102) |
| photo, deeper | 0 | PENDING (owner expects shallow stills only) | " |
| mostly open blue water | 0 | none (owner) | the WP1.3 open-water row stays PENDING unless a clip is later named |
| static shot | 0 | none (owner) | |
| chaptered recording | 0 | none exists | every GoPro file is chapter 1; the HERO13 kept a 17-minute take in one file |

No `.LRV`/`.THM` sidecars exist (owner, 2026-10-15; D60 closed, spec v0.5.2).

## Chapter handling in v1: DEFERRED to v2 (owner, 2026-10-19)

Owner: "concur with defering chapter handling." Consequences (plan sections 5 and 9, row
"Inventory / No chaptered recordings"): WP3.8 is not built; the chapter review in WP3.19 is
omitted; V12 and the chapter-seam part of V3 are removed; the spec is revised (section 5.5,
D21, D33, D80, D82, D83 and the dependent G7/G11/V3/V12 text). The spec revision is a spec
change and goes to the owner as a decision_request with the exact text (CHARC drafts it; OPEN
until approved). Until the revision is approved the spec text stands as written.

## Released on this word (CHARC)

- WP1.3 and WP1.4 deep parts (deeper look-check cases, the gain-cap noise test WP1.4b) may be
  briefed on `SCUBA/`.
- WP1.2 Part B measures on the real modes of record: one video mode (4K 29.97 HEVC) across both
  folders, plus the 1080p59.94 H.264 compilation as a second decode mode; no chaptered
  recording; no LRV; the largest-photo leg stays queued until stills arrive.
- Gaps carried as PENDING: photos (both rows), open blue water, distance haze and deep-water
  noise until the deep look check runs.
