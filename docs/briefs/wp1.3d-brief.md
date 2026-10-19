# WP1.3D — Look check pack, deep part (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator 2026-10-19 on CHARC's go-ahead
(`cb61a4e41f625d73`: "Draft the WP1.3-deep / WP1.4b brief (SCUBA/, c3 primary with ancuti2018
beside ...)"). The deep work is split into two packages run one after the other: this one (the
pack and the case scan), then WP1.4b (`docs/briefs/wp1.4b-brief.md`: the gain-cap noise test
and the `Params()` default flip), which reads this package's deep-frame list. Spec **v0.5.3**
(D16 amended: 3C is the default method). Released on CP1 (owner 2026-10-19: `SCUBA/` = deeper,
~20 m; `docs/proofs/cp1-footage-sorting.md`). Cell: `implementer-sonnet-high` (the brief fixes
the frames, the scan measures, the variants, the outputs and the tests). Worktree
`.worktrees/wp1.3d`, branch `wp1.3d`, base = the main commit named in the dispatch. Needs
footage: the eight `SCUBA/` chapters (`GX011589`-`GX011593`, `GX011598`, `GX011600`,
`GX011601`; 24.1 GB, 48.2 min in total), found with `find_footage_file`. The footage folder is
READ-ONLY; every output goes to `work/wp1.3d/`. Uses the GPU but records no timing or memory
figure, so it is NOT exclusive.

| Field | Content |
|---|---|
| ID and title | WP1.3D — Look check pack (deep part); plan section 6 WP1.3; Gate result 3 (deep rows) |
| Goal | Give the owner the deep half of CP2: still frames from every `SCUBA/` chapter under the three methods (c3 first, the default), the three spec section 12 cases the shallow pack could not show (open blue water, distance haze, deep-water noise) as named CANDIDATE frames picked by a documented scan, and one short deep clip in motion at the provisional smoothing, so deep-water noise can be judged as video. Record the statistics behind every frame. |
| Spec clauses | D103 (informal bar); D16 as amended in v0.5.3 (3C default); 6.3.1 (Ancuti 2018, blue D51, gain caps D40/D50/D52, D100), 6.3.2 (3C), D99 (white-balance clamp); 7.1-7.3 (staged statistics, centred window D95, proxies); section 12 "Gray-world on open water", "Distance haze", "Deep-water noise"; 6.5 and D54 (colour tags: BT.709 FULL range on every `SCUBA/` file per the 2026-10-18 inventory). Plan section 5 CP2. |
| Depends on | WP1.3 (merged: `tools/lookcheck/`), WP1.4 (merged: `tools/prototype/temporal.py`), WP1.2 Part B (merged), CP1 (done). |
| Files owned | `tools/lookcheck/scan.py` (NEW: the case scan), `tools/lookcheck/pack.py` ONLY to add a `deep` command and the parameters it needs (the `stills` and `flicker` commands keep their behaviour and output bit for bit), `tests/test_lookcheck_deep.py` (NEW), `docs/reports/wp1.3d-deep-look-check.md` (NEW), `docs/proofs/wp1.3d-ledger.md` (NEW). NO change under `tools/prototype/` (import only; if a hook is needed there, STOP), NO change to `tools/lookcheck/frames.py` (STOP if needed), NO `pyproject.toml` change, nothing under `src/`. `tests/test_lookcheck.py` is unchanged and must pass unchanged. |
| Interfaces consumed | `tools.lookcheck.frames` (`extract`, `excerpt`, `probe_stream`, `read_png16`, `OutputRoots`, `tool_env`); `tools.lookcheck.pack` (`build_pack`, `default_variants`, `encode_clip`, `verify_clip` and the rest, as built); `tools.prototype.temporal` (`measure`/`analyse_staged`, `smooth`/`Smoother`, `render`, `proxy`); `tools.prototype.pipeline.correct`, `tools.prototype.params.Params`; `tools.local_config.find_footage_file`; `ffmpeg`/`ffprobe` on PATH. |
| Interfaces provided | `work/wp1.3d/deep-frames.json`: the ranked deep-frame list WP1.4b reads (shape in claim 2). None frozen. |
| Dependencies | None new. |
| Tests | `tests/test_lookcheck_deep.py`, synthetic unless marked: (1) each scan measure returns the hand-computed value on a constructed proxy (a uniform frame, a half-flat frame, a known-contrast frame); (2) the excluded-frame rule rejects a near-black frame by name; (3) the candidate picker honours the spacing and per-chapter limits on a constructed ranking, including ties (stable order stated); (4) `deep-frames.json` written from a constructed scan has the documented keys and ordering; (5) the `deep` command on two synthetic frames writes the pack layout with every file named in the index, the variants in the order c3, ancuti2018, ancuti2018-blue; (6) `stills`' output on the WP1.3 synthetic layout test is unchanged (the existing tests pass unchanged and cover it); (7) `footage`-marked: the scan on one `SCUBA/` chapter at 3 timestamps runs and records the three measures. |
| Hardware flags | `footage`, `gpu`. Not exclusive. |
| Out of scope | Any default change, tuning or re-run at other parameters (WP1.4b and WP2.1); the gain-cap noise measurement (WP1.4b); the `Params()` flip (WP1.4b); deciding what a candidate IS (the owner's at CP2: the scan proposes, the owner names); photos (none supplied); anything under `src/`; timing. |
| Done | Plan section 4.5; the four gates green with the `footage` and `gpu` tests RUN; harness gate untouched; the pack, the scan records, `deep-frames.json` and the clips complete under `work/wp1.3d/` with the index; the report complete with the CP2 deep sheet. |

## What the package does (claims)

1. **Case scan.** Over each of the eight `SCUBA/` chapters, extract one frame every 10 s from
   5 s to the end (about 290 frames in all) at short side 540 with `frames.extract(...,
   short_side=540)` (FFmpeg's scaler: acceptable for RANKING, and said so in the report; it is
   not a statistic the pipeline uses). On each, compute on the display-encoded RGB in [0, 1]:
   - **Depth index** `D = R̄ / Ḡ` (raw channel means; lower = deeper, red absorbed).
   - **Open-water fraction** `W` = the fraction of pixels whose luma (BT.709 weights) local
     standard deviation over a 15x15 box is below 0.01 AND whose blue-or-green exceeds red by
     at least 0.05 (flat water, not a flat dark rock). The thresholds are fixed here; the
     report states them and shows the distribution of `W` so the owner can see what it picked.
   - **Haze index** `H` = the luma RMS contrast (standard deviation of luma over the frame);
     lower = hazier.
   - **Exclusion:** a frame whose luma mean is below 0.05 or above 0.95 is excluded from every
     ranking (recorded with the reason, never silently dropped).
   Every value, with chapter, pts and the exclusion reason, goes to `work/wp1.3d/scan.json`.
2. **Candidates.** For each case, 4 candidates, ranked: deep-water noise = lowest `D`; open
   blue water = highest `W`; distance haze = lowest `H` among frames with `W` below 0.5 (so
   open water does not take the haze slots). Two candidates of the same case are at least 30 s
   apart; at most 2 per chapter per case; a frame may serve two cases (say so). Ties break by
   chapter name then pts. `work/wp1.3d/deep-frames.json` holds, per case, the ranked list with
   chapter, pts (exact ticks and time base as `frames` records them) and the measure values,
   plus the 8 deepest frames overall by `D` (WP1.4b's input; no spacing rule on that list
   other than 10 s). The report says plainly that these are CANDIDATES: the owner decides at
   CP2 whether each shows the case.
3. **Stills.** From each `SCUBA/` chapter, 6 frames at the WP1.3 positions
   (`STILL_FRACTIONS`, 5 % to 95 %; 48 frames), plus the 12 case candidates re-extracted at
   FULL resolution, as 16-bit PNG through `frames.extract` with the range honoured. Every frame
   corrected at the prototype defaults with the method set per variant, in the order
   **c3, ancuti2018 (blue off), ancuti2018 --blue**, on the GPU (a GPU failure is a STOP).
   The variant order is the only presentation change from WP1.3: c3 is the default (v0.5.3).
   Per frame and variant, the statistics `build_pack` records (channel means, effective alpha,
   whether a gain cap or the clamp BOUND, the gains, the N{} bounds and range) go to
   `work/wp1.3d/statistics.json`.
4. **Pages.** `work/wp1.3d/index.html` as WP1.3's (one static page, no external resource,
   thumbnails linking to the full-size PNGs, a one-line statistics summary under each, the
   side-by-side JPEGs in `pairs/`), with three sections: the 48 chapter stills, then one
   section per case listing its 4 candidates with the measure value and rank. The head lists
   the variants, the `Params` values used, and the candidate rule of claim 2.
5. **The deep clip in motion.** A 6 s excerpt centred on the deepest candidate (lowest `D`;
   clamp the start to the chapter), every frame extracted at full resolution, with statistics
   measured on the 540 proxy (the WP1.4 construction: an exact 4x4 area mean in NumPy, NOT
   FFmpeg's scaler), analysed STAGED and smoothed with the centred Gaussian at 2.0 s (the
   provisional default, DR-25(3)), then rendered through `temporal.render` for **c3** and for
   **ancuti2018**. Encode `work/wp1.3d/clip/<chapter>_c3.mp4`, `<chapter>_ancuti2018.mp4` and
   the untouched `<chapter>_source.mp4` cut by the same frames, with WP1.3's `encode_clip` and
   `verify_clip` (NVENC, BT.709 FULL range tags as the source, the source's frame rate, no
   audio). The per-frame raw and smoothed statistics go to `clip/statistics.json`; the report
   tabulates the red and blue white-balance gains, the effective alpha and whether the clamp
   or a cap bound, against pts.
6. **CP2 deep sheet.** `docs/reports/wp1.3d-deep-look-check.md` ends with the table the owner
   fills at CP2, same columns as WP1.3's section 9 (observed yes/no/pending, seriousness,
   decision), rows: the three section 12 cases (each naming its candidate files), colour cast
   remaining, magenta/red push, over-sharpening halo, noise (stills), noise in motion (the
   clip), clipping, flicker (the clip). Pre-filled PENDING.
7. **Observations, statistics only.** Per variant: on how many frames a gain cap bound, the
   clamp bound, N{} range fell below 0.02 (the DR-14 territory WP1.4 described), with the
   frames named. No judgement of the look: that is the owner's.
8. Docstrings complete; ruff, ruff format, mypy strict and pytest green with the `footage`
   and `gpu` tests RUN; `tests/test_lookcheck.py` unchanged and green.

## Decisions fixed at issue (orchestrator)

- **Defaults, not tuning.** The pack shows the prototype at `Params()` defaults with only
  `method` (and `blue_compensation` for the third variant) set per variant. Do not change
  `Params()`: its default still reads `ancuti2018` on main; WP1.4b flips it. Because every
  variant sets its method explicitly, the flip does not change this pack. Say so in the page
  head and the report.
- **The scan proposes; the owner names.** Never call a candidate "open water" or "haze" as a
  fact; call it "candidate (highest W)" and so on.
- **Statistics for the clip come from the proxy built in NumPy** (an exact 4x4 block mean of
  the 3840x2160 frame), as WP1.4 fixed it. The scan's FFmpeg-scaled 540 frames are for
  ranking only and are never fed to the pipeline.
- **Reuse WP1.3's and WP1.4's instruments as built.** If `frames.py`, `temporal.py`,
  `pipeline.py` or `params.py` needs a change, STOP.
- **Local configuration in the worktree.** The orchestrator copies the uncommitted
  `clearwater.local.toml` into the worktree root. Footage `C:\Users\rwsmy\clearwater-footage`,
  working `C:\Users\rwsmy\clearwater\work`; so `work/wp1.3d/` is the MAIN tree's
  `C:\Users\rwsmy\clearwater\work\wp1.3d\`. Never edit or commit that file.
- **Output roots.** `OutputRoots.from_config(config, subdir="wp1.3d")` on EVERY `frames` call
  and every write; every write and delete goes through the checked writer (inside
  `work/wp1.3d/`, outside the footage folder, a target with more than one hard link refused).
  `FFREPORT` stripped (`frames.tool_env()`).
- **FFmpeg on PATH.** Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for every
  ffmpeg, ffprobe and pytest run. A skip at the gate fails claim 8.
- **pytest temp root.** Pass `--basetemp` under `C:\Users\rwsmy\clearwater\work\` (for
  example `work/pytest-wp1.3d`). Never inside the footage folder (`tests/conftest.py` refuses).
- **Disk.** C: has about 116 GB free. The pack is about 240 full-resolution 16-bit PNGs (about
  10 GB). The clip's full-resolution PNG sets (about 180 frames x 3) MAY be deleted once the
  three MP4s are encoded and verified; keep the first, middle and last frame of each set and
  every JSON.
- **Memory.** The host stopped two background test runs today for low system memory. Run the
  full pytest once, in the foreground, at the end of each round, not in the background, and do
  not run two GPU jobs at once.
- **Spec version:** **v0.5.3**. Cite it.
- **Never `git stash`**; use a temporary commit or a scratchpad copy for red/green checks.
- **Commit footer:** `Co-Authored-By:` naming the model you actually run as.

## Declared operating envelope

Windows 11, FFmpeg 9.0.2, the eight `SCUBA/` HERO13 chapters as present (HEVC 8-bit, BT.709
full range, 30000/1001, 3840x2160), the prototype at defaults on the RTX 4070. Photos, other
cameras, HDR/GP-Log, chapter spans, parameter tuning and timing are out of envelope.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (the pack feeds an owner-reserved decision; a wrong range, a mislabelled
  variant or a candidate presented as a fact would mislead it).
  - **Transport and flags:** WSL, codex-cli 0.162.1. Per-call flags
    `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
  - **Probe:** one probe through the exact invocation before round 1.
  - **Diff:** generated Windows-side with
    `git -C <worktree> diff -U8 <base>..HEAD -- . ':!uv.lock' ':!docs/proofs'`; WSL never runs
    git.
  - **The prompt** includes the claim list, the envelope with a request to TAG out-of-envelope
    findings, and the report. It carries the EXECUTED/REASONED paragraph verbatim from
    `docs/codex-reviewer.md`, and its own paragraph: "Do NOT read `docs/proofs/` or anything
    under `clearwater-review-evidence`; those are withheld. Never read or list
    `/mnt/c/Users/rwsmy/clearwater-footage`." The records under
    `/mnt/c/Users/rwsmy/clearwater/work/wp1.3d/` MAY be read.
  - **Assertions** (all `grep -a`): the banner reads gpt-5.6-sol / high; every `^ERROR` and
    `ERROR codex_core` line classified by provenance; the `^tokens used` footer; an anchored
    VERDICT line; at least one `^ succeeded in`; `grep -a -n 'docs/proofs\|wp1.3d-ledger'`
    with every hit classified as an echo or an access.
  - **Evidence:** `clearwater-review-evidence/wp1.3d/rN/`; ledger `docs/proofs/wp1.3d-ledger.md`.
  - **Convergence:** zero NEW in-envelope blocking findings. Minors fixed once in that round's
    cleanup. FIVE_ROUND_GATE.
- WHAT TO EXAMINE: whether the scan measures are computed as defined (thresholds, exclusion);
  whether the candidate rule (spacing, per-chapter limit, haze excluding open water, ties) is
  applied as stated; whether each variant is labelled with the parameters actually used and in
  the stated order; whether the clip's statistics come from the NumPy proxy and are STAGED and
  smoothed at 2.0 s centred; whether the clip's frames are the excerpt's frames in order with
  the source's timing; whether `stills` and `flicker` are unchanged; whether any ffmpeg flag
  could write outside the working folder; whether every number in the report is in a record.
- Reviewer B is the orchestrator's own seat pass on the merge candidate.

## Notes for the cell

- Return report = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4: per-commit change list; validation lines; verification-loop record; review
  rounds, ledger and evidence paths; locks honoured; the pack's path and counts (stills,
  candidates, variants, clip frames); the candidate table per case (chapter, pts, measure);
  the 8 deepest frames; observations (claim 7) without judgement; deviations and open
  questions.
- **Context depth.** The orchestrator reads your context depth at every yield. Keep tool
  output short (tail it, write long output to files under `work/wp1.3d/`). If you are re-seated,
  your successor starts from the branch head, this brief and the ledger: keep the ledger
  current at each commit.
- STOP for: a GPU failure in the prototype; a chapter FFmpeg cannot decode; any need to touch
  `tools/prototype/` or `tools/lookcheck/frames.py`; any output outside `work/wp1.3d/`; a
  change in `stills` or `flicker` output you cannot avoid; fewer than 4 non-excluded frames
  for a case (report it, do not lower the bar).
- Working rules: `uv sync` in the worktree; commit by pathspec with `feat(wp1.3d): ...` and the
  footer; never a bare `cd` (use absolute paths or `git -C`); never post to a mailbox; the
  footage folder is input-only; the local config is never committed.
