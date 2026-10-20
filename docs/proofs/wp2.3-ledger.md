# WP2.3 -- shared test fixtures: cumulative round ledger (Reviewer A)

Cell: implementer-sonnet-high (STRONG). Brief `docs/briefs/wp2.3-brief.md` (FINAL). Base `da074f4`.
Reviewer A: codex-cli 0.162.1 in WSL, `gpt-5.6-sol` / `high`, `-s read-only`; evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp2.3\rN\`. Depth column is the dispatcher's.

## Rounds

| Round | Head reviewed | MAJOR | MINOR | In-envelope / out | NEW / REOPENED | Reverts | Fixes changed | Verdict | Tokens | Depth |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `4ffc8b1` | 7 (4 EXECUTED, 3 REASONED) | 4 (2 E, 2 R) | 11 / 0 | 11 / 0 | 0 | product (generators, manifest schema, committed samples): 7 findings; tests and plugin: 4 | NEW_CRITICAL_MAJOR_FOUND | 178,521 | (dispatcher) |
| 2 | `1e2d2f6` | 0 | 3 (3 E, 0 R) | 3 / 0 | 3 / 0 | 0 | none in the round; post-convergence cleanup of the 3 minors, docstring and test only (see below) | NO_NEW_CRITICAL_MAJOR | 190,698 | 96,313 tokens / 55 turns at the R2 yield |

Round 1 per-finding adjudication: `...\wp2.3\r1\adjudication.md` (md5s in `md5s.txt`). All 11
findings were confirmed (finding 7 partly) and fixed at `b439f70` and `312773f`. The round's
mechanical assertions all hold (banner, no ERROR lines, footer, anchored VERDICT, 27 `^ succeeded
in`, the 13 `docs/proofs` hits are echoes).

Round 2 per-finding adjudication: `...\wp2.3\r2\adjudication.md` (md5s in `md5s.txt`). The reviewer
re-raised none of the 11 round-1 findings and none of the three rulings. Mechanical assertions hold
(banner, no ERROR lines, footer, anchored VERDICT, 30 `^ succeeded in`, the 8 `docs/proofs` hits are
echoes). The 3 minors (stale `pytest_plugins` quote in `tests/fixture_plugin.py:3`, the no-GPS test
omitting the 3 DNG/TIFF dummies, `video.py:3` saying 45 frames for all clips though `vid-vfr` has 30)
are CONFIRMED; per the fill they are fixed once in the terminating round's cleanup and open no round.

## Gates (read off tool output)

| Head | Gate | Result |
|---|---|---|
| `d495b57` (first cell's run, `work/fixtures/runs/full3.txt`) | full `uv run pytest -q -p no:cacheprovider` | 1130 passed, 1 warning, 503.43 s, EXIT 0 |
| `1e2d2f6` | `ruff check .`, `ruff format --check .`, `mypy` (46 files) | all passed (`work/fixtures/runs/lint-r2b.txt`) |
| `1e2d2f6` | `tests/test_fixtures.py` + `tests/test_conftest_guard.py` | 282 passed, 66.54 s |
| `1e2d2f6` | full pytest (`work/fixtures/runs/full4.txt`) | 1130 passed, 1 warning, 478.55 s, EXIT 0 |

## Post-convergence cleanup (after round 2; no round 3, docstring and test only)

Commit after `7660b1f` fixes the 3 round-2 minors: `tests/fixture_plugin.py` docstring quotes the
ruled conditional statement; `test_stills_carry_no_gps` also scans `dng-by-extension`, `dng-by-tag`
and `dng-extension-only`; `tools/fixtures/video.py` overview names the 30-frame VFR clip. Gates on it:
`ruff check`, `ruff format --check`, `mypy` pass; `tests/test_fixtures.py` + `tests/test_conftest_guard.py`
282 passed. No full pytest (the orchestrator runs it on the merge candidate).

## Rulings applied (CHARC `ef7b272564ddeb9d`, 2026-10-20)

- **R1-1** (AD-14 geometry accepted): disc CENTRE track in the lower third; binding property is that
  the measured upper half is never touched (existing test proves it). `flicker.py` module docstring,
  the `DISC_CENTRE_ROW` docstring and the manifest `exercises` text say exactly this (`1e2d2f6`; the
  manifest was regenerated: only that one string changed, every other committed file is
  byte-identical).
- **R1-2** (conftest): ruling R1-2 applied as ruff's layout of the ruled statement (102 cols > 100);
  accepted by the orchestrator at the R2 yield. The line is the ruled conditional expression, wrapped in
  parentheses by `ruff format`. REPRODUCED: the literal one-line text is 102 columns, so `ruff check` reports E501 (limit
  100) and `ruff format --check` wants to reformat it. The parenthesised form is the same statement
  (`241b415`); tests/conftest.py is otherwise unchanged apart from that statement; the WP-T1 guard and
  `tests/test_conftest_guard.py` untouched and green. DEVIATION for the orchestrator to note.
- **R1-3** (`.gitattributes`): new repo-root file, single line `tests/fixtures/** -text` (`241b415`).
  `git ls-files --eol tests/fixtures` after: all 87 files `attr/-text`; 78 binary files `i/-text w/-text`,
  8 text placeholders `i/none w/none`, `manifest.json` `i/lf w/lf`. Before the attribute the manifest was
  already `i/lf` in the blob and `w/lf` in the working tree here, so autocrlf had not converted it on
  this checkout; the attribute makes that independent of `core.autocrlf`. The manifest byte test now
  compares raw bytes on both sides; `_norm_newlines` is deleted (`241b415`).

## Statistics the AD-14 texture is tuned to (ruling 1)

Source: the owner's shallow clip `GX011627` (WP1.3's flicker clip, 180 frames), as WP1.3 measured it.
No owner pixel is used; the still is procedural (`tools/fixtures/flicker.py`, seed 7).

| Quantity | WP1.3 value (report line) | Fixture still (measured, manifest `facts.design`) |
|---|---|---|
| channel means R, G, B | 0.426, 0.572, 0.546: the mean over the 180 frames of `compensation.channel_means` in `work/wp1.3/flicker/statistics.json` (the report text gives the resulting gains, `wp1.3-look-check.md:294-295`, not the means) | 0.4264, 0.5715, 0.5452 |
| N{} spread (high minus low) | 0.271 to 0.516, mean 0.380: minimum quoted at `wp1.3-look-check.md:190`; mean = N{} high mean 0.203 minus low mean -0.177 (lines 297-298); maximum from the same JSON (not in the report text) | 0.395 |
| white-balance gains R, B (Ancuti 2018, `Params()` defaults) | red 1.125, blue 0.975 mean over the 180 frames (lines 294-295) | 1.129, 0.969 |

## Decisions made in the cell and disclosed (for the orchestrator to rule on)

1. **AD-14 geometry.** A disc of 10 % of a 960 x 540 frame is 257 px across; the lower third is 180
   rows. It cannot lie inside the lower third. The disc centre is row 405 (inside the lower third,
   which starts at row 360); the disc spans rows 277 to 532; the measured region (rows 0 to 269) is
   untouched. Parameters are constants in `flicker.py` (`DISC_CENTRE_ROW`, `DISC_FRACTION`).
2. **No 16-bit RGB TIFF.** Pillow 12.3.0 cannot write one (`fromarray` rejects uint16 RGB;
   `frombytes(..., "RGB;16B")` makes an 8-bit image). Listed in the manifest's `omitted`; not
   substituted.
3. **DNG refusal has no `Fault` kind.** `Fault` kinds are video probe faults; the manifest states the
   refusal as `expect.refusal` = clause D116 and how it is recognised. A third DNG file
   (`dng-extension-only`, a `.dng` with no tag) was added so refusal by extension alone is testable.
4. **`truncated` vs `unreadable_tail`.** The truncated clip expects `truncated`/`warn`. Which kind a
   cut-off file maps to is the probe package's to rule; IF-5 gives no discriminator.
5. **Untagged clip is H.264.** x265 always writes a video signal type (explicit limited range);
   x264 writes none.
6. **Conftest line.** The ruled conditional expression (R1-2), as `ruff format` lays it out in
   parentheses because the literal one-line text is 102 columns. A bare `["fixture_plugin"]` stops
   every WP-T1 guard test (`tests/test_conftest_guard.py` copies `conftest.py` alone into a
   miniature repository): reproduced, 40+ failures at the first full run.
7. **Git and line endings.** `core.autocrlf=true` here. `.gitattributes` (`tests/fixtures/** -text`,
   R1-3) stops git converting any committed fixture; the manifest byte test compares raw bytes.
8. **FFV1/MKV.** The clip is lossless FFV1 RGB in Matroska (ffprobe says `bgr0`); container time
   base 1 ms, so 30000/1001 is the declared rate (`r_frame_rate`). 86 MB, so generated (into
   `work/fixtures/generated`), never committed.
9. **HEIC.** Written with pillow-heif's private `misc.CtxEncode` as WP2.1S did (the public encoder
   cannot write the tag without the `irot` or the reverse).

## Reviewer B (orchestrator's seat, candidate `a32e5fb` = `cea7a7e` rebased) and the one remediation

B: `review-B.txt` in `C:\Users\rwsmy\clearwater-review-evidence\wp2.3\reviewB\`; verdict
NEW_CRITICAL_MAJOR_FOUND: 4 MAJOR (B1 EXECUTED, B2-B4 REASONED) and 1 ADVISORY. Adjudication (orchestrator):
B1 and B2 blocking; B3 and B4 strengthen; B5 banked. All four fixed in one commit (`1d0e04d`); each has a
regression test that fails on the pre-fix code.

| # | Finding | Fix | Regression test (pre-fix result) |
|---|---|---|---|
| B1 | `vid-vfr`'s stts ended 1001,1001,1001 (track 39039 ticks), not the stated 1001,1001,2002 cycle (40040); `measure()` used pts deltas only; the test checked the set | WENT THE PREFERRED WAY: FFmpeg writes the last frame as 2002. `-bsf:v setts=duration=if(eq(N\,29)\,2\,DURATION)` (`video.VFR_LAST_DURATION_BSF`; `setts` counts in the encoder time base, so 2 is 2002 track ticks). Deterministic: two regenerations gave a byte-identical `vfr.mp4`. `measure()` now records `pts.frame_durations` (ffprobe packet durations, last included), `pts.track_duration_ticks` and `stts_durations` (a stdlib walk of the MP4 sample table, `video.stts_durations`); `mismatches()` compares the exact 30-entry lists and the track duration; the intended average rate is 22500/1001 (30 frames over 40040 ticks) | `test_vfr_frame_durations_are_the_stated_cycle_including_the_last`: on the pre-fix `vfr.mp4` it FAILS (`At index 29 diff: 1001 != 2002`, `work/fixtures/runs/b1-prefix.txt`) |
| B2 | TIFF bit depth hard-coded 8 in `stills.measure` and the test | `stills.tiff_bits_per_sample` reads tag 258 from the file bytes; `measure()` uses it for TIFF; the test's `_read_still` reads `tag_v2[258]` (Pillow, independent of the generator's reader) | `test_tiff_bit_depth_is_read_from_the_file_not_assumed`: a `tiff8-gradient-none` copy with tag 258 patched to 16,16,16 measures 16 in both and so disagrees with the manifest's 8. Pre-fix `measure()` on that file returns 8 (executed) and the test fails on the missing reader (`work/fixtures/runs/b2-prefix.txt`) |
| B3 | `verify_generated` checked only decoded pixels and count | `flicker.probe_clip` (split out of `measure_clip`) and `flicker.STREAM_IDENTITY`: `verify_generated` checks container, codec, pix_fmt, size, `r_frame_rate`, `avg_frame_rate`, time base, packet pts count and hash, then the frame count and hash. `decode_sha256` now decodes with `-fps_mode passthrough`, so the frame hash is pixel-only and timing is the identity check's job (before, ffmpeg's CFR conversion duplicated frames when the rate changed, so the two checks overlapped). A cache hit WAS already verified on first use per session (`SampleProvider.path` calls `verify_generated` before it records the path); now stated in the docstring and tested | `test_planted_clip_at_another_rate_fails_by_name`: the clip's packets stream-copied with `-itsscale 1.1988` (about 25 fps) keep the 90 frames and hash and fail on `packet_pts_sha256` by name (the stream still declares 30000/1001, so `r_frame_rate` does not differ). `test_cache_hit_is_verified_before_it_is_handed_out`: that file in the cache makes the provider regenerate. Pre-fix both FAIL (`assert None is not None`; `DID NOT RAISE`, `b3-prefix.txt`) |
| B4 | no XMP or `udta` check | `test_no_committed_file_carries_an_xmp_packet_or_gps_text` scans the RAW bytes of every committed file for `<x:xmpmeta`, `<?xpacket`, `ns.adobe.com/xap`, `exif:GPS`, `GPSLatitude`; `test_mp4_user_data_holds_nothing_beyond_the_empty_meta` walks each MP4 (`video.mp4_boxes`, shared with the stts walk): top-level boxes within ftyp/moov/free/mdat, moov within mvhd/trak/udta, no trak-level udta, udta exactly one meta of hdlr plus an empty ilst | `test_planted_xmp_gps_packet_is_caught_by_name` (a JPEG with an APP1 XMP GPS packet: the old EXIF-only GPS check passes it, asserted in the test; the new scan names all four markers) and `test_planted_udta_payload_is_caught_by_name` (a GoPro-style GPMF atom in udta: the old `has_location_tag` check passes it, asserted; the walk names `udta holds [b'meta', b'GPMF']`) |
| B5 | ADVISORY, OUT-OF-ENVELOPE: video file sizes (encoder build) are serialised into the byte-identical manifest | BANKED, no change: another FFmpeg or libx264 build is outside the declared envelope; video is already stated non-byte-reproducible, and the regeneration test fails by name on the manifest bytes there. Trigger to revisit: supporting a second FFmpeg build. Nominal severity advisory | none |

Committed files whose bytes changed, and why: `tests/fixtures/video/vfr.mp4` (41,268 -> 41,276 bytes; the
last frame's duration is now 2002 and the track 40040 ticks) and `tests/fixtures/manifest.json` (the new
duration and stts fields on every video entry, the vfr entry's size, md5 and 22500/1001 expectation, and the
flicker stream facts re-ordered by the `measure_clip` split; no flicker value changed). Every other
committed file regenerated byte-identically (`cmp` against a fresh `generate.py` run).
Gates after the remediation: ruff check, ruff format --check, mypy pass; `tests/test_fixtures.py` +
`tests/test_conftest_guard.py` 290 passed (70.5 s). No full pytest (the orchestrator runs it). Reviewer A
was not re-run (instruction).
