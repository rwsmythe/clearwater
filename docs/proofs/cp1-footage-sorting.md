# CP1 — Footage sorting (owner checkpoint record, LIVING until the download is complete)

CP1 is the owner's checkpoint (plan section 5): each clip and photo gets a category, gaps
are noted, and chapter handling in v1 is decided from the inventory. This record is kept by
CHARC, in the owner's words with their time, and is REPLACED (not annotated) as the owner
sorts more footage. The real inventory run (`tools/inventory.py`) still waits on the owner's
word that the download is complete; the partial sorting below is the owner's own word on the
files present, not an inventory-derived guess (DR-6 does not apply).

## Partial sorting 1 — 2026-10-15

Owner, 2026-10-15 in chat to CHARC, on the four files then present:
- ~05:25Z: "I have put 4 videos in there. They are all shallow snorkel videos. I am working
  on downloading the rest which will include deeper (~20m) scuba videos. I will also work on
  getting still pictures which will be all shallow snorkel."
- ~10:50Z, to CHARC's proposal of a partial CP1 on those four: **"shallow confirmed"**.

| File | Size | Category (owner) | Notes |
|---|---|---|---|
| `GX011625.MP4` | 406 MB | shallow (snorkel) | whether caustics are present is noted by WP1.3 |
| `GX011626.MP4` | 1390 MB | shallow (snorkel) | " |
| `GX011627.MP4` | 151 MB | shallow (snorkel) | WP1.5 primary chapter; CFR 30000/1001, HEVC 8-bit, BT.709 full range |
| `GX011628.MP4` | 17 MB | shallow (snorkel) | WP1.5 fast-check chapter |

Each is chapter 01 of its own recording (GoPro `GX01nnnn`); none is a chaptered recording.
No `.LRV`/`.THM` sidecars exist for any of this project's footage (owner, 2026-10-15; D60
closed, spec v0.5.2).

**Released on this word (CHARC):** WP1.3 and WP1.4 start on the shallow category only. The
deeper, open-blue-water, distance-haze, photo and chaptered cases are PENDING (plan D102:
"the dependent test is marked pending") and are added when the owner sorts the rest.

## Pending (owner)

- Scuba clips (~20 m) in `SCUBA/`: not yet sorted; the download is not reported complete.
  Three zero-byte files (`GX011598.mp4`, `GX011600.mp4`, `GX011598 (1).mp4`) were present on
  2026-10-15 ~09:45Z; the owner has been asked to remove or replace them.
- Still photos (shallow snorkel, per the owner): not yet present.
- Chapter handling in v1: decided when the full inventory shows whether any chaptered
  recording exists.
