# Inventory refresh 2026-10-29 merge record (orchestrator generations 22-23)

**Package:** the footage inventory refresh for the owner's phone footage, commissioned by CHARC `fddf5c88` item 1.
- **Rulings:**
  - review form `a9fc36da`: a read-only mechanical instrument run, where the orchestrator's re-run of the committed probe, five spot checks and CHARC QA substitute for Reviewers A and B, for this arc only;
  - scope `0fd08f9f`: the tree MINUS `Insta360/`, excluded by name, with a one-line `--exclude` in `tools/inventory.py` and its test.
- **Lane:** CODEX (`gpt-6.1-sol`/high), session `01a188a9-4199-7690-9681-6699ed6c54bd`, 5 turns. Pace at dispatch: Codex 0.324, Claude 1.399. Commits were made at this seat with the GPT-6.1 Sol footer.
- **Footage access:** a read-only Codex grant for this package only. The sandbox's writable roots exclude the footage folder.
- **Report:** `docs/reports/inventory-2026-10-29.md`. Probe: `docs/reports/inventory-2026-10-29-probe.py`. Dispatches and returns: `clearwater-review-evidence\inventory-1029\cell\`.

**Commits:**
- author branch `inventory-1029` on `1c59f15`: `c8a4268` (`--exclude` plus its test), `e4cf415` (report and probe), `2cb2510` (the HEIC orientation correction);
- rebased as `inv-mc` `3186ea3` on main `27a11ae`;
- rebased again in `stack-g22` onto main `47a08ae` (after WP4.5) as `83668dd`.

`git patch-id --stable` is `f977203c` on all three ranges.

## Independent verification at this seat (`a9fc36da` form)

- **Re-run of the committed probe** on `2cb2510`: output byte-identical to the cell's. md5s, equal to the report's table:
  - JSON `af348461b43dbf7fbd00c25de16ea0e1`;
  - script blob `235c2170efd7012550c76b414658fadc`;
  - `tools/inventory.py` blob `aa0072b5f33590b50f6e650870dbf8a4`.
- **Privacy grep** with the ruled pattern over the probe JSON and the committed report: 0 hits.
- **Spot checks by hand against disk** (pillow-heif raw EXIF with selected tags only; `ffprobe -show_entries`; `ffprobe -v trace`):
  - `IMG_6690.HEIC`: irot 180, EXIF 3;
  - `IMG_6703.HEIC`: irot 0, EXIF 1;
  - `IMG_6791.JPG`: Make, Model and Software NUL-filled;
  - `IMG_6702.MOV`: `qt  `, HEVC 1920x1440, `has_b_frames=2`, rotation -180, video `elst` media_time 0, negative `ctts`;
  - `dp_color_video_1791675261.mp4`: `mp42`, H.264, no B-frames.

  All match after the correction.
- **The one MISMATCH my spot checks found (fixed in `2cb2510`):** the first report said `IMG_6703.HEIC` had no EXIF orientation. The probe's `info.get("original_orientation", ...)` default never applied, because pillow-heif stores the key with `None`. All 23 null rows were misread 1s. After the fix, all 62 HEICs' EXIF orientation agrees with `irot`, so DR-7 is not reopened.
- **DR-15:** every Phone video's VIDEO-track `elst` media_time is 0 (20 of 20). The `time=2112` entries are on audio tracks. Seat evidence: `clearwater-review-evidence\inventory-1029\seat-dr15-elst-check.md`.

## CHARC QA (`fffae21e`, 2026-10-29T17:50:11Z)

Verdict: **CONFIRMED, no finding.** The QA text is saved verbatim at `clearwater-review-evidence\inventory-1029\charc-qa-fffae21e.md`. CHARC writes the DR-15 register note after the merge.

## Gate

The ONE stacked two-leg gate on `stack-g22` `8e1114a` (this package, then WP4.3a), recorded in `docs/proofs/wp4.3a-accept.md`, section "Gate", with the disposition of its two serial failures (neither in this package's files) and the rebase onto WP4.5.

The inventory part touches `tools/inventory.py`, `tests/test_inventory.py` and two `docs/reports/` files.
