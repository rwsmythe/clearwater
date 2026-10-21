# WP3.5 — Accept record (video colour arguments and sample conversion: `clearwater.color`)

**Accepted 2026-10-21 by the orchestrator** (generation 7, session
`clearwater-orchestrator-20261020-1419`). Gate per `docs/review-gate-clearwater.md` Part 2.
Tier STRONG. Wave 2, tranche A; stacked gate with WP3.3 and WP3.2 (this package merges second).
- Brief approval and rulings: CHARC `53b752a4d7fac4fc` (ruling 5.1: boundary, re-sized S,
  sonnet-high; 5.6: unknown siting as `left` both ways, untagged-output tags are DR-17's /
  WP3.10's). STOP-1 ruling (V9 binds the RGB-side legs; the 8-bit 4:2:0 swscale pair is a
  characterisation): CHARC `229c326b43fb99f2`, AD-11 clarified on main `2ce4266`. FINAL bounds:
  the orchestrator's round-1 ruling (generation 6), tighter than the ruling's example figures.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp3.5-brief.md` (FINAL). Spec v0.5.4, architecture FINAL 1.0. |
| Base SHA | `2c5540a` |
| Author head | `abee706` (Reviewer A terminated at R1; terminating cleanup; report "Deliberate skip"). No Reviewer B remediation. |
| Cell and depth | **`wp35-cell`** (implementer-sonnet-high): 90,237 at the R0 yield; 194,772 at the R1 yield; 240,808 at the window yield. Ended at a clean stop at the orchestrator's generation-6 rollover. |
| Merged head | `wp3.5-mc2` = `abee706` rebased onto `wp3.3-mc2` `f9f1ae1` (`80c1a12`), then onto main after the WP3.3 accept, plus this record, the report erratum and DR-39; main fast-forwarded to the commit that adds this record. Reviewer B ran on `wp3.5-mc` `deb33ea` (the first stack, on WP3.2 + WP3.3); the package's files are byte-identical in both trees. CHARC held main. |
| Byte identity | `git patch-id --stable` = `65edaf3724a2...` on `2c5540a..abee706`, on `b028fd0..deb33ea` (the B tree), on `f9f1ae1..80c1a12` and on the final range. |
| Gates on the candidate | `ruff check`, `ruff format --check`, `mypy` strict clean on every stack top. Full pytest on `80c1a12` (WP3.3 + WP3.5): **2353 passed, 1 skipped, 1 warning (CuPy CUDA_PATH), 892 s, exit 0** (the skip is `test_planted_range_misread_is_caught`'s deliberate `yuvj420p` case); on the final stack top `8e66cbf` (all three) **2904 passed, 1 skipped, 1 warning (CuPy CUDA_PATH), 885 s, exit 0**; with `cupy` and `cupyx` unimportable **2386 passed, 519 skipped, 585 s, exit 0** (both in `.worktrees/wp3.2-mc2`). FFmpeg 9.0.2 on this seat's PATH (`C:\Users\rwsmy\AppData\Local\Microsoft\WinGet\Links\ffmpeg`), so the FFmpeg rows ran; the footage row ran (footage present, read-only). The cell's own final-head run on `abee706`: 1964 passed, 1 skipped, 849 s. |
| Gates on main | Recorded in the WP3.2 accept record (`docs/proofs/wp3.2-accept.md`), the last of the stack: the main gates run once on the merged top. |
| Reviewer A | gpt-5.6-sol / high, WSL, codex-cli 0.162.1. R1 on `3cadc37`: 0 critical, 0 major, 7 minor (3 in envelope, 4 out), fixed as the terminating cleanup (`3f27cd8`..`aa54804`: truth cases for 10-bit BT.709 full and BT.601 limited and full, 8-bit BT.709 full; the range misread planted both ways; the helper checks FFmpeg's exit status and a short final frame; non-positive sizes, empty and non-contiguous input buffers refused; `bt601` dropped from the primaries table; rejected values formatted with `!a`). Terminated at R1. Evidence `clearwater-review-evidence\wp3.5\r1`. Ledger `docs/proofs/wp3.5-ledger.md`. |
| Reviewer B | ONE pass on `deb33ea`: `NO_NEW_CRITICAL_MAJOR` (3 minor, 2 advisory). |
| Witness | At this seat on the final stack top: every 10-bit code 0-1023 through `planes_to_rgb` / `rgb_to_planes` returns the same bytes (float32 between); `ffmpeg_color_names` of an assumed BT.709 limited description gives `bt709` / `bt709` / `bt709` / `tv`. |

## The package

`src/clearwater/color/` (`__init__`, `swscale`, `samples`) and `tests/test_color_*.py`; report
`docs/reports/wp3.5-video-colour.md`. Stdlib and NumPy only; imports nothing above it, runs no
process, no dependency, no interface change. The decode / encode `scale` argument pair (AD-10:
`bicubic+accurate_rnd+full_chroma_int+bitexact` both ways; matrix, range, siting from the
stream; planar RGB at the source depth; never a primaries or transfer option), the IF-1 to
FFmpeg name table, planar G, B, R samples to float32 RGB and back (`numpy.rint`; 8- and 10-bit
integer round trips exact), the supported set `yuv420p` / `yuvj420p` / `yuv420p10le` with BT.709
or BT.601 (anything else, and `yuvj420p` with a limited range, refused by name). Measured pair
characterisation (1/255): GX011627 30 frames mean 0.687, share over 2/255 0.72 %; `testsrc2`
rows mean 1.455-2.023; every planted defect beyond its bound by the margin in the report.

## Reviewer B

ONE pass on `deb33ea`. `clearwater-review-evidence\wp3.5\reviewB\review-B.txt`; md5s in
`md5s.txt` beside it. Assertions: banner gpt-5.6-sol / high; `^ERROR` 0; `tokens used` footer
present; 14 `succeeded in`; VERDICT anchored; no withheld-path access on any command line. It
checked all 70 accepted pixel-format / matrix / range / siting combinations by a source probe
and found no mismatched pair. `VERDICT: NO_NEW_CRITICAL_MAJOR`. Dispositions:
- (1) MINOR in envelope: claim 5 says the RGB-side legs "are exact"; the D76 leg (8-bit RGB to
  10-bit out) is not (max 0.123/255, mean 0.062/255, within AD-11) and is not separately
  asserted against AD-11. ERRATUM; the separate D76 RGB-side assertion BANKED DR-39 (a).
- (2) MINOR: the footage row calls the full video probe, which reads the `moov/udta` GPMF
  settings (FMWR, PRTN, PTCL). DECLINED: that is the standing, permitted GPMF read (AD-16 as
  corrected; owner ruling 2026-10-19: only the `gpmd` track, IMU and GPS are out of scope); the
  finding is against this prompt's over-broad wording "no GPMF data", not against a rule.
- (3) MINOR in envelope: `rgb_to_planes` does not refuse a non-contiguous RGB array (the
  round-1 refusal covers `planes_to_rgb`'s input buffer); the conversion stays correct.
  BANKED DR-39 (b).
- (4) ADVISORY: the FFmpeg pixel rows do not cover the full cross-product (`yuvj420p` + BT.601
  full, matched non-left sitings, D76 from limited or BT.601 sources). BANKED DR-39 (c).
- (5) ADVISORY, out of envelope (EXECUTED): a float bit depth `8.0` is accepted as 8.
  BANKED DR-39 (d).

## Erratum at the gate

Appended to the report: claim 5's "which are exact" covers the `samples.py` round trip at the
source depth; the D76 path (8-bit RGB to 10-bit planes) is within AD-11 (max 0.123/255, mean
0.062/255 by calculation), not exact.

## Debt

- **DR-20 item (1) CLOSED** by this accept (claim 4 and task 6: D54 consumed from WP3.7's
  resolved `ColorDescription`; `vid-untagged` decodes as BT.709 / limited; an untagged `yuvj`
  stream decodes as full). DR-20 items (2)-(9) stay OPEN (WP3.10, 8.4).
- **DR-17** stays OPEN (WP3.10; the name table passes the assumed values through).
- **DR-39** NEW: Reviewer B (1)-(5) dispositions above; trigger: WP3.9's and WP3.10's briefs
  (they consume the pair and the sample conversion), or any widening of the supported set.

## Follow-ons

- Consumer notes for WP3.9 / WP3.10 (report "For other packages"): `ffmpeg_color_names` for the
  output tags (DR-17); BT.601 `smpte170m` primaries resolve as "unexpected" in WP3.7's probe
  (for WP3.7's owner); a `yuvj` source is encoded as its non-`j` form with range `pc`.
