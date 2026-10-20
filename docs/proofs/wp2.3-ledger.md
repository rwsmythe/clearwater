# WP2.3 -- shared test fixtures: cumulative round ledger (Reviewer A)

Cell: implementer-sonnet-high (STRONG). Brief `docs/briefs/wp2.3-brief.md` (FINAL). Base `da074f4`.
Reviewer A: codex-cli 0.162.1 in WSL, `gpt-5.6-sol` / `high`, `-s read-only`; evidence
`C:\Users\rwsmy\clearwater-review-evidence\wp2.3\rN\`. Depth column is the dispatcher's.

## Rounds

| Round | Head reviewed | MAJOR | MINOR | In-envelope / out | NEW / REOPENED | Reverts | Fixes changed | Verdict | Tokens | Depth |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `4ffc8b1` | 7 (4 EXECUTED, 3 REASONED) | 4 (2 E, 2 R) | 11 / 0 | 11 / 0 | 0 | product (generators, manifest schema, committed samples): 7 findings; tests and plugin: 4 | NEW_CRITICAL_MAJOR_FOUND | 178,521 | (dispatcher) |

Round 1 per-finding adjudication: `...\wp2.3\r1\adjudication.md` (md5s in `md5s.txt`). All 11
findings were confirmed (finding 7 partly) and fixed at `b439f70` and `312773f`. The round's
mechanical assertions all hold (banner, no ERROR lines, footer, anchored VERDICT, 27 `^ succeeded
in`, the 13 `docs/proofs` hits are echoes).

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
6. **Conftest line.** The one line is `pytest_plugins = ["fixture_plugin"] *
   Path(__file__).with_name("fixture_plugin.py").is_file()`. The bare `["fixture_plugin"]` stops
   every WP-T1 guard test (`tests/test_conftest_guard.py` copies `conftest.py` alone into a
   miniature repository): reproduced, 40+ failures at the first full run. The conftest diff is that
   line and one blank line.
7. **Git and line endings.** `core.autocrlf=true` here: `manifest.json` is text and a checkout may
   turn its LF into CRLF (the tests normalise the committed side once); the text placeholders hold
   no line break so git cannot change them; every other fixture is binary to git (`git ls-files
   --eol`). A `.gitattributes` line for `tests/fixtures/manifest.json` would end it; not owned.
8. **FFV1/MKV.** The clip is lossless FFV1 RGB in Matroska (ffprobe says `bgr0`); container time
   base 1 ms, so 30000/1001 is the declared rate (`r_frame_rate`). 86 MB, so generated (into
   `work/fixtures/generated`), never committed.
9. **HEIC.** Written with pillow-heif's private `misc.CtxEncode` as WP2.1S did (the public encoder
   cannot write the tag without the `irot` or the reverse).
