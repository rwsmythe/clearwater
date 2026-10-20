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
