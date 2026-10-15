# WP1.3 — Look check pack, shallow part (dispatch brief, DRAFT by CHARC)

**Status:** DRAFT by CHARC 2026-10-15 for the orchestrator to finalise and dispatch. Spec
**v0.5.2**. Released on the owner's partial CP1 ("shallow confirmed", 2026-10-15; record
`docs/proofs/cp1-footage-sorting.md`). Cell: `implementer-sonnet-high` (the brief fixes the
frames, the variants, the outputs and the tests; nothing to design). Worktree
`.worktrees/wp1.3`, branch `wp1.3`, base = the main commit named in the dispatch. Needs
footage: the four shallow chapters (`GX011625.MP4` 406 MB, `GX011626.MP4` 1390 MB,
`GX011627.MP4` 151 MB, `GX011628.MP4` 17 MB) in `C:\Users\rwsmy\clearwater-footage\`. The
footage folder is READ-ONLY; every output goes to `work/wp1.3/`. Uses the GPU (prototype
`--device gpu`) but records no timing or memory figure, so it is NOT exclusive; it MUST NOT
run inside WP1.2 Part B's bench window (the orchestrator sequences).

| Field | Content |
|---|---|
| ID and title | WP1.3 — Look check pack (shallow part); plan section 6 WP1.3; Gate result 3 |
| Goal | Run the WP1.1 prototype over the owner's shallow footage and deliver before/after material the owner can page through quickly at CP2: still frames from every shallow chapter under both compensation methods, plus one short clip corrected frame by frame with unsmoothed statistics so the flicker is visible (spec 7.1). Record, per frame, the whole-frame statistics the prototype measured, so CP2's verdicts can be tied to numbers. The deeper, open-blue-water, distance-haze and photo cases are PENDING and are added by a later part when the owner sorts that footage. |
| Spec clauses | D103 (informal bar; failure cases and the decision on each recorded); 6.3.1 (Ancuti 2018, blue compensation D51, gain caps D40/D50/D52), 6.3.2 (3C), D99 (white-balance clamp); 7.1 (flicker from per-frame statistics; the clip frame by frame); section 12 cases "Gray-world on open water", "Distance haze", "Deep-water noise" (all PENDING here: say so); 6.5 and D54 (the source's colour tags: BT.709 FULL range on these chapters, per the WP1.5 camera record); 6.4 (32-bit float processing). Plan section 5 CP2; section 9 rows "Defaults the papers leave open" and "Stage definitions". |
| Depends on | WP1.1 and WP1.2A (merged: `tools/prototype/` with `--device gpu`), WP1.5 (merged: the camera record in `work/wp1.5/` and the FFmpeg conventions), partial CP1 (done). |
| Files owned | `tools/lookcheck/__init__.py`, `tools/lookcheck/frames.py` (frame extraction through `ffmpeg` as a process; reused by WP1.4), `tools/lookcheck/pack.py` (runs the prototype on the extracted frames, writes the pack), `tests/test_lookcheck.py`, `docs/reports/wp1.3-look-check.md`, `docs/proofs/wp1.3-ledger.md`. NO change under `tools/prototype/` (if a hook is needed there, STOP), NO `pyproject.toml` change, nothing under `src/`. |
| Interfaces consumed | `tools.prototype.pipeline.correct`, `tools.prototype.params.Params`, `tools.prototype.backend.select_backend` by import (prototype interfaces, not frozen, used as built); `ffmpeg`/`ffprobe` on PATH (WP0.1 install; prepend the WinGet links folder as WP1.5 did); `tools/local_config.py` for the two folders. |
| Interfaces provided | `frames.extract(video, timestamps_s, out_dir, *, short_side=None) -> list[FrameFile]` and `frames.excerpt(video, start_s, duration_s, out_dir) -> list[FrameFile]`, each returning 16-bit PNG paths with the exact source pts of every frame (from `ffprobe -show_frames`) and the stream's colour tags. WP1.4 imports these; document the record shape in the report. |
| Dependencies | None new. |
| Tests | `tests/test_lookcheck.py`: synthetic clips built with `ffmpeg -f lavfi` (skip when ffmpeg/ffprobe are absent, the WP1.5 pattern). (1) Range correctness: a `testsrc2`/solid-colour clip encoded HEVC `yuvj420p` FULL range and the same encoded LIMITED range both extract to the SAME known RGB values within 1/255 (this is the control that the look check is not misleading; a deliberately wrong `-color_range` must FAIL it). (2) Extracted frames carry the exact pts the probe reports. (3) `pack.py` on two synthetic frames writes the pack layout below with every file named in the index. (4) The per-frame statistics JSON holds every field the prototype's `Result` records. (5) `footage`-marked: `frames.extract` on `GX011628.MP4` at one timestamp runs. The real pack is NOT a test; the cell runs it once. |
| Hardware flags | `footage`, `gpu`. Not exclusive; no timing or memory figure is a result (elapsed times informally). |
| Out of scope | Any change to the prototype's method or defaults (record what you see; CP2 and WP2.1 decide); temporal smoothing (WP1.4); the deeper, open-water, haze, photo and chaptered cases (PENDING, next part); timing (WP1.2 Part B); anything under `src/clearwater/`. |
| Done | Plan section 4.5; the four gates green with the `footage` and `gpu` tests RUN; harness gate untouched (no `scripts/`, `.claude/`, kernel-doc or `tests/harness/` change); the pack complete under `work/wp1.3/` with its index; the report complete. |

## What the pack contains (claims)

1. **Frames.** From each of the four shallow chapters, 6 frames at timestamps spaced evenly
   between 5 % and 95 % of the duration (24 frames), extracted at FULL resolution as 16-bit
   PNG with the stream's colour range honoured (BT.709 FULL range on these chapters; the
   extraction reads the tags, never assumes). Each frame file is named
   `<chapter>_<pts-seconds 0000.000>.png`. The exact pts and the tags are in
   `work/wp1.3/frames.json`.
2. **Variants.** Every frame corrected by `tools.prototype` at the defaults under three
   variants: `ancuti2018` (blue off), `ancuti2018 --blue`, `c3`; on the GPU (`--device gpu`;
   if the GPU path raises, STOP). Output 16-bit PNG beside the source frame as
   `<frame>-<variant>.png`. Per frame and variant, the prototype's recorded statistics
   (`CompensationInfo`, `WhiteBalanceInfo`: channel means, effective alpha, whether a gain
   cap or the white-balance clamp BOUND, the gains) go to `work/wp1.3/statistics.json`.
3. **Pairs the owner can page through.** `work/wp1.3/index.html`: one static page, no
   external resource, one row per frame: the source thumbnail and the three variants as
   thumbnails (short side 540 px, generated by Pillow from the PNGs), each linking to the
   full-size PNG; the chapter, the pts, and a one-line statistics summary (red gain, blue
   gain, whether anything bound) under each. A `work/wp1.3/pairs/` folder holds, per frame
   and variant, a side-by-side JPEG (source left, corrected right, short side 1080 px) for
   viewing on any device. The page lists at its head the three variants, the defaults used
   (the `Params` field values), and the pending cases.
4. **The flicker clip.** From `GX011627.MP4`, a 6 s excerpt starting at 30 % of the duration
   (about 180 frames at 30000/1001), every frame extracted at full resolution and corrected
   frame by frame at the defaults with `ancuti2018` (blue off), UNSMOOTHED (each frame its
   own statistics, exactly what the prototype does today), then re-assembled with FFmpeg into
   `work/wp1.3/flicker/GX011627_unsmoothed.mp4` (HEVC NVENC 8-bit `yuv420p`, BT.709 FULL
   range tags matching the source, the source's frame rate, no audio) next to the untouched
   excerpt `GX011627_source.mp4` cut by the same frames. The per-frame statistics of all ~180
   frames go to `work/wp1.3/flicker/statistics.json`, and the report plots or tabulates the
   red gain, the blue gain, the effective alpha and the N{} bounds against pts so the flicker
   is visible as numbers as well. This excerpt is ALSO WP1.4's clip: say its exact pts range.
5. **Caustics note.** For each chapter, one line in the report on whether surface caustics
   are visible in the extracted frames (yes / no / faint), so CP1's category can be refined
   to "shallow with caustics" where it applies. No judgement of the correction: that is the
   owner's at CP2.
6. **CP2 sheet.** `docs/reports/wp1.3-look-check.md` ends with a table the owner fills at
   CP2, one row per spec section 12 case and per obvious artifact class (colour cast
   remaining, magenta push, over-sharpening halo, noise, clipping, flicker), columns:
   observed (yes/no/pending), seriousness, decision. The pending cases are pre-filled PENDING.
7. Docstrings complete; ruff, ruff format, mypy strict and pytest green with the `footage`
   and `gpu` tests RUN; no change outside the owned files.

## Decisions fixed at issue (CHARC)

- **Frame extraction is FFmpeg as a process**, decoding to 16-bit RGB PNG (`-pix_fmt rgb48le`
  or `rgb48be` as FFmpeg's PNG encoder takes it) with chroma upsampled by FFmpeg's default
  scaler. The colour-range handling is PROVEN by test (1), not assumed; the report quotes the
  exact command line and the tags read. (The product's own conversion is WP3.5's; this
  instrument only has to be right.)
- **Defaults, not tuning.** The pack shows the prototype at `Params()` defaults. If a frame
  looks wrong for a reason the cell can name (a cap binding, the clamp binding, the N{} bounds
  collapsing on a flat frame, DR-14), the cell says so in the report's observations list with
  the statistic; it does not re-run at other values. Tuning is CP2's and WP2.1's.
- **The GPU is the device** because CPU is 11-58 s per 4K frame (WP1.2A) and the pack has
  about 250 frames. CPU/GPU agreement is WP1.2A's proven claim; the pack does not re-prove it.
- **16-bit PNG in, 16-bit PNG out, JPEG only for the side-by-side viewing copies** (quality
  92). The owner judges the PNG pairs on a calibrated display if a verdict is close; the
  JPEGs are for paging quickly, as the plan asks.
- **Pending cases are named, not approximated.** No open-water, haze or deep case is faked
  from shallow footage.
- **Outputs.** `work/wp1.3/` only. Nothing large is committed; the report cites paths.
- **ffmpeg invocation.** `-nostdin -hide_banner -y` only inside `work/wp1.3/`; assert before
  each run that the resolved output path is inside the working folder and outside the footage
  folder (the WP1.5 refusal pattern, hard links included).

## Declared operating envelope

Windows 11, the installed FFmpeg 9.0.2 (NVENC for the flicker clip's encode), the four
shallow HERO13 chapters as present (HEVC 8-bit, BT.709 full range, 30000/1001), the
prototype at defaults on the RTX 4070. Deeper footage, photos, HDR/GP-Log sources, other
cameras, temporal smoothing and any parameter tuning are out of envelope.

## Test roster (`tests/test_lookcheck.py`)

As the Tests row: the range-correctness control with its planted failure (a wrong
`-color_range` must fail by name), the pts fidelity test, the pack-layout test on two
synthetic frames, the statistics-field test, and the one `footage` smoke test.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (the pack is what the owner judges at CP2; a wrong colour range or a wrong
  variant label would mislead a reserved decision). Transport, flags, probe, diff, prompt,
  per-round assertions, evidence folder `clearwater-review-evidence/wp1.3/rN/` and ledger
  `docs/proofs/wp1.3-ledger.md` exactly as the WP1.5 brief states them, with `wp1.3`
  substituted.
- WHAT TO EXAMINE: whether the extraction honours the stream's range and matrix (and the test
  proves it); whether every variant is labelled with the parameters actually used; whether the
  per-frame statistics in the JSON are the ones the prototype measured on that frame (not a
  copy from another); whether the flicker clip's frames are the excerpt's frames in order with
  the source's timing; whether any ffmpeg flag could write outside the working folder.
- Reviewer B is the orchestrator's own seat pass on the merge candidate (fill Part 2 item 2).

## Notes for the cell

- Return report = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4: per-commit change list; validation lines; verification-loop record; review
  rounds, ledger and evidence paths; locks honoured; the pack's path and counts (frames,
  variants, pairs, flicker frames); the caustics note per chapter; observations (statistics
  that bound, flat-frame collapses) without judgement; deviations and open questions.
- STOP for: a GPU failure in the prototype; a chapter FFmpeg cannot decode; any need to touch
  `tools/prototype/`; any output outside `work/wp1.3/`; a frame whose extracted colour the
  range test cannot vouch for.
- Working rules as the WP1.5 brief: `uv sync` in the worktree; commit by pathspec with
  `feat(wp1.3): ...` and the `Co-Authored-By:` footer; never a bare `cd`; never post to a
  mailbox; the footage folder is input-only; the local config is copied into the worktree by
  the orchestrator and never committed.
