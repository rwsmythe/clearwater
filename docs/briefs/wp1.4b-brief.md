# WP1.4b — Gain-cap noise test and deep-frame statistics (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator 2026-10-19 on CHARC's go-ahead
(`cb61a4e41f625d73`) and CHARC's original commission of the noise test as WP1.4b
(`0fd7c88ad56a7083`). Dispatched AFTER WP1.3D merges: it reads WP1.3D's
`work/wp1.3d/deep-frames.json` and the deep clip's pts. Spec **v0.5.3**. Cell:
`implementer-opus-high` (the noise measure, its validation and the trade analysis are
reasoning-dense; the result decides D100). Worktree `.worktrees/wp1.4b`, branch `wp1.4b`, base =
the main commit named in the dispatch. Needs footage: the `SCUBA/` chapters WP1.3D's list names,
and `GX011627.MP4` for the shallow reference. Footage READ-ONLY; outputs under `work/wp1.4b/`.
Uses the GPU; records no timing or memory figure; NOT exclusive.

| Field | Content |
|---|---|
| ID and title | WP1.4b — Gain-cap noise test and deep-frame statistics; plan section 6 WP1.4 (first bullet); Gate result 4; and the `Params()` default flip to c3 (spec v0.5.3 D16) |
| Goal | (a) Flip the prototype's default method to c3, keeping every recorded result reproducible. (b) On real deep frames, measure red-channel noise of the corrected output with the Ancuti 2018 gain caps on and off and at several cap values, and with the white-balance clamp at several settings, with a documented and validated noise measure and crops the owner can check (D100, Gate result 4). (c) From the same frames, give the evidence for the default clamp on deep footage (D99) and for the N{} range floor (DR-14), and settle WP1.4's open question on how the capped alpha is smoothed. |
| Spec clauses | D16 (amended v0.5.3: 3C default); 6.2 step 2 and D99 (clamp, "the pipeline's control for deep-water noise"); 6.3.1 and D40/D50/D52/D100 (the caps: "a fidelity-versus-noise control, not a noise mitigation ... kept or dropped according to a prototype noise test"); section 12 "Deep-water noise"; N5 result 4; 7.1-7.3 (smoothed statistics, proxies); 14.1 (default maximum white-balance gain; robust N{} bounds). Plan section 6 WP1.4 bullet 1; section 9 rows "Defaults the papers leave open; default maximum white-balance gain" and "Robust statistics for normalization bounds". |
| Depends on | WP1.3D (merged: `deep-frames.json`, the deep clip's pts), WP1.4 (merged: `tools/prototype/temporal.py`), WP1.3 (`tools/lookcheck/frames.py`). |
| Files owned | `tools/prototype/params.py` (the default flip and its docstring sentence ONLY); NEW `tools/noise_experiments.py` (the noise estimator, the runner, the crop page); NEW `tools/camera_state.py` (the minimal GPMF camera-state reader of claim 2a); NEW `tests/test_noise_experiments.py`; `docs/reports/wp1.4b-gain-cap-noise.md` (NEW); `docs/proofs/wp1.4b-ledger.md` (NEW). For the flip only (see decisions): the lines in existing tests and tools that relied on the old default, changed ONLY to name `method="ancuti2018"` explicitly. Nothing else under `tools/prototype/`, `tools/lookcheck/`; no `pyproject.toml` change; nothing under `src/`. |
| Interfaces consumed | `tools.prototype.pipeline.correct` and its recorded `Result` (compensation info, white-balance info); `tools.prototype.temporal` (`measure`, `analyse_staged`, `smooth`, `render`, `proxy`, `flicker`); `tools.lookcheck.frames` (`extract`, `excerpt`, `read_png16`, `OutputRoots`, `tool_env`); `tools.local_config.find_footage_file`. |
| Interfaces provided | `Params().method == "c3"`. The noise estimator is an instrument of this package (not V-series); WP2.1 may reuse it. None frozen. |
| Dependencies | None new (NumPy/SciPy/CuPy granted). |
| Tests | `tests/test_noise_experiments.py`: (1) the estimator recovers a known Gaussian sigma (0.002, 0.01, 0.03 on [0, 1]) added to a smooth synthetic gradient within 10 %; (2) on the noise-free gradient it returns below 0.0005; (3) a sharp noise-free edge does not inflate it (the flat-tile selection excludes the edge); (4) scaling a noisy image by g scales the estimate by g within 5 % (the estimator follows gain, which is what the test is about); (5) the settings grid is the one stated in claim 3, each setting labelled with the `Params` actually used; (6) `footage`: the runner on one deep frame and two settings writes its record. Plus the flip's own test: `Params().method == "c3"`. Every existing test passes, with only the explicit-method edits the decisions allow. |
| Hardware flags | `footage`, `gpu`. Not exclusive. |
| Out of scope | The GoPro IMU and GPS (ACCL, GYRO, GRAV, CORI, IORI, GPS5/GPS9): out of the project's scope (owner 2026-10-19 via CHARC `01500d3574412e69`), never read or decoded; a GPMF library dependency; any default change other than `method` (recommend; WP1.6/WP2.1 and, for a spec change, the owner decide); dropping the caps from the code; denoising; V3; the product's engine; timing. |
| Done | Plan section 4.5; the four gates green with `footage` and `gpu` RUN; harness gate untouched; every record and the crop page under `work/wp1.4b/`; the report complete with Gate result 4 and the recommendations. |

## What the package does (claims)

1. **The default flip (first commit, alone).** `Params.method` defaults to `"c3"`; the
   attribute docstring says "Default `"c3"`: spec v0.5.3 D16 (amended after CP2 2026-10-19)".
   Then run the full suite. Each test or tool that fails or changes behaviour because it relied
   on the old default is fixed by naming `method="ancuti2018"` explicitly at that site, never by
   changing an expected value. Tools whose committed reports cite results produced under the old
   default (`tools/statistics_experiments.py`, `tools/prototype/clip.py`, `bench.py`,
   `tools/lookcheck/pack.py`) pin `ancuti2018` where they relied on the default, so a re-run
   reproduces the report; the user-facing `tools/prototype/run.py` follows `Params()` (now c3)
   and its help text says so. **Guards (CHARC `1cc08da6b265e2a6`):** (i) a new test asserts
   `Params().method == "c3"`; (ii) no pinned site may be a product-facing default: `run.py` and
   every CLI help text show c3 as the default and list `ancuti2018` / `ancuti2018-blue` as the
   options, as spec 6.3 does. The report lists every site touched, with the reason. A site
   that needs more than naming the method is a STOP.
2. **Frames.** The 8 deepest frames of `work/wp1.3d/deep-frames.json` (lowest `D = R̄/Ḡ`),
   re-extracted at FULL resolution as 16-bit PNG into `work/wp1.4b/frames/` through
   `frames.extract` (range honoured), plus ONE shallow reference: `GX011627.MP4` at the WP1.3
   flicker excerpt's first pts (205205 ticks at 1/30000), so the same measure is shown where
   nothing binds.
2a. **Camera state per frame (context only; CHARC `01500d3574412e69`).** From the `gpmd` data
   track (handler "GoPro MET"; stream 3 on these files) of each source chapter, read SHUT
   (shutter s), ISOE (sensor ISO), WBAL (white-balance temperature K), WRGB (the camera's applied
   white-balance RGB gains), YAVG and UNIF, and attach the nearest-in-time value to each frame
   of claim 2. Method: extract the track with `ffmpeg -map 0:<gpmd> -codec copy -f data` into
   `work/wp1.4b/gpmd/` (it holds GPS too: never committed, never copied elsewhere); walk the KLV
   (4-char key, 1-byte type, 1-byte size, 2-byte repeat, payload padded to 4 bytes; type 0 =
   nested) and decode ONLY the six keys above; every other key is skipped by its length without
   decoding. Time-index from the sample count and the stream duration (state the rule; 30 Hz
   keys are one per frame). About 60 lines, no new dependency. Tests: a synthetic KLV blob built
   in the test (nested container, padding, an unknown key and an IMU-named key both skipped
   undecoded, a big-endian uint16 and float payload), and a `footage` test reading ISOE from one
   `SCUBA/` chapter in place. NO extract of the owner's track is committed. **Droppable:** if the
   parser threatens your depth or a STOP-free finish, drop it and mark the columns PENDING; the
   noise test does not depend on it.
3. **Settings grid.** Ancuti 2018, blue off, at the defaults except: `red_gain_cap` in
   {None (off), 0.5, 1.0, 2.0 (default)} x `max_white_balance_gain` in {1.5, 2.0, 3.0
   (default), 5.0, 1000 (effectively unclamped; record whether it ever bound)} = 20 settings;
   plus c3 at the defaults x the same five clamp values = 5 settings (c3 has no caps; it is the
   default method, so its row is the reference). 25 settings x 9 frames, rendered on the GPU
   with each frame's own (unsmoothed) statistics. Per render record: the effective alpha, the
   red and blue cap use, whether the cap bound, the three white-balance gains, whether the clamp
   bound, the N{} bounds and range, the noise figures of claim 4, and the residual cast of
   claim 5. Records go to `work/wp1.4b/grid.json`; full-resolution renders need not be kept
   (keep the crops of claim 6).
4. **The noise measure (documented, validated, used identically everywhere).** Primary:
   `sigma_R` = the Donoho estimate on the red channel, `median(|HH1|) / 0.6745`, where HH1 is the
   finest diagonal Haar detail, computed per 64x64 tile and taken as the median over a FIXED
   set of tiles: the 25 % of tiles with the lowest gradient energy of the SOURCE frame's luma.
   The same tiles serve every setting of that frame, so settings are compared on the same
   regions. Report `sigma_R` of the source red on those tiles, of each output, and the
   amplification `sigma_out / sigma_src`; give values also in 8-bit code values (x 255).
   Cross-check: Immerkær's fast noise-variance estimator on the same tiles; if the two rank the
   settings differently on any frame, say so. State the limits: the source is 8-bit HEVC, so
   part of what is measured is compression artefact (which the correction amplifies equally);
   the estimate is spatial, not temporal.
5. **Fidelity side of the trade.** Per render, the residual cast as the output's channel-mean
   ratios `R̄/Ḡ` and `B̄/Ḡ` (1.0 = gray-world neutral), and for Ancuti the fraction of the
   compensated red mean that came from the green term (the cap's purpose, D100: "limits how
   much of the compensated channel is derived from green").
6. **Crops for the owner.** Per frame, two 512x512 crops at 100 %: the flattest region (from
   the fixed tile set) and the most textured one, for 7 settings: Ancuti cap off / 2.0 / 0.5 at
   clamp 3.0; Ancuti cap 2.0 at clamp 1.5 and 1000; c3 at clamp 3.0 and 1000; plus the source.
   Each crop as RGB and as the red channel alone in grayscale (noise reads more clearly).
   `work/wp1.4b/index.html` (static, no external resource) lays them side by side with
   `sigma_R`, the red gain and what bound under each. The report says what the owner should
   look for.
7. **Gate result 4 (D100).** A table: per cap setting at the default clamp, the median over the
   8 deep frames (and the range) of `sigma_R` amplification, the red white-balance gain, the
   residual `R̄/Ḡ`, the green-derived fraction, and the camera's ISOE and WRGB red gain (claim 2a)
   as context columns; the shallow reference beside it. Say whether the noise amplification
   tracks the camera's ISO or its own red gain. Then a
   recommendation: KEEP or DROP the caps, with grounds; the decision is the gate's at WP1.6
   (dropping them is a spec change, so the owner's). Say whether the result agrees with the
   spec's expectation (a tighter cap raises the white-balance gain on the noisy red and so
   raises noise) and, if not, why.
8. **The clamp on deep footage (D99, 14.1).** From the same grid: at each clamp value, how often
   it bound on the deep frames, `sigma_R` amplification and residual cast, for c3 and for Ancuti
   at the default cap. Recommend a default maximum white-balance gain for WP2.1 with grounds; no
   default change.
9. **The N{} range floor (DR-14).** On the 8 deep frames AND the open-water candidates of
   `deep-frames.json`, under c3 and Ancuti at the defaults: the N{} range and the stretch factor
   (1 / range). Propose a floor value with grounds (WP1.4 recommended "a floor far above 1e-6,
   its value to be set from open-water and deep frames"); no default change.
10. **The capped alpha under smoothing (WP1.4 open question).** On the WP1.3D deep clip's frames
    (re-extract by the pts in `work/wp1.3d/clip/statistics.json`), Ancuti at the defaults, 2.0 s
    centred Gaussian, staged, on the 540 NumPy proxy: (A) the effective alpha smoothed as a
    value (what `temporal` does today); (B) the channel means and the source-only cap statistic
    smoothed, and alpha derived from the smoothed values. Report the two alpha series, the mean
    absolute difference of the rendered proxy frames, and the flicker measure of each. If the
    cap binds on fewer than 10 % of the clip's frames, report that and stop this claim there (the
    question then stays open for WP2.1). Implement (B) in `tools/noise_experiments.py` from
    `temporal`'s public functions; if (B) needs a change in `temporal.py`, STOP.
11. Docstrings complete; ruff, ruff format, mypy strict and pytest green with `footage` and
    `gpu` RUN.

## Decisions fixed at issue (orchestrator)

- **The flip is one commit, alone, first,** so the merge's Reviewer B and my bit-identity
  witness can see it in isolation. At the gate I re-run WP1.2R's bit-identity witness (Ancuti
  blue off and on, and 3C; CPU and GPU) with the method given EXPLICITLY: those paths must be
  unchanged bit for bit. Only the default changed.
- **Pinning is the only edit allowed in other packages' files.** The edit names
  `method="ancuti2018"` (or passes it through an existing argument). Anything more is a STOP,
  reported with the site.
- **No default other than `method` changes.** The cap, clamp and N{} recommendations go to the
  report; WP1.6 and WP2.1 decide.
- **The noise test runs on unsmoothed per-frame statistics** for the stills (a still has no
  time axis); smoothing appears only in claim 10.
- **Local configuration in the worktree.** The orchestrator copies the uncommitted
  `clearwater.local.toml` into the worktree root (footage `C:\Users\rwsmy\clearwater-footage`,
  working `C:\Users\rwsmy\clearwater\work`); `work/wp1.4b/` is the MAIN tree's. Never edit or
  commit it.
- **Output roots.** `OutputRoots.from_config(config, subdir="wp1.4b")` on every `frames` call and
  every write, through the checked writer (inside `work/wp1.4b/`, outside the footage folder,
  multi-link targets refused). `FFREPORT` stripped. `work/wp1.3d/` is READ, never written.
- **FFmpeg on PATH.** Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for every
  ffmpeg, ffprobe and pytest run. A skip at the gate fails claim 11.
- **pytest temp root.** `--basetemp` under `C:\Users\rwsmy\clearwater\work\` (for example
  `work/pytest-wp1.4b`). Never inside the footage folder.
- **Memory.** The host stopped background test runs today for low system memory. Run the full
  pytest in the foreground, once per round; never two GPU jobs at once; render the grid one
  frame at a time and release the full-resolution arrays between frames.
- **Disk.** C: has about 116 GB free; keep crops, JSON and the first frame of each set; full
  renders may be discarded after their figures and crops are written.
- **Spec version:** **v0.5.3**. Cite it.
- **Never `git stash`**; use a temporary commit or a scratchpad copy for red/green checks.
- **Commit footer:** `Co-Authored-By:` naming the model you actually run as.

## Declared operating envelope

Windows 11, FFmpeg 9.0.2, the `SCUBA/` HERO13 chapters WP1.3D selected and `GX011627.MP4`
(HEVC 8-bit, BT.709 full range, 30000/1001, 3840x2160), the prototype on the RTX 4070. Photos,
10-bit sources, temporal noise, denoising, other cameras and any default change other than
`method` are out of envelope.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (changes the prototype default; the result decides D100).
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
    `/mnt/c/Users/rwsmy/clearwater/work/wp1.4b/` and `work/wp1.3d/` MAY be read.
  - **Assertions** (all `grep -a`): the banner reads gpt-5.6-sol / high; every `^ERROR` and
    `ERROR codex_core` line classified by provenance; the `^tokens used` footer; an anchored
    VERDICT line; at least one `^ succeeded in`; `grep -a -n 'docs/proofs\|wp1.4b-ledger'` with
    every hit classified as an echo or an access.
  - **Evidence:** `clearwater-review-evidence/wp1.4b/rN/`; ledger `docs/proofs/wp1.4b-ledger.md`.
  - **Convergence:** zero NEW in-envelope blocking findings. Minors fixed once in that round's
    cleanup. FIVE_ROUND_GATE.
- WHAT TO EXAMINE: whether the flip changed only the default and every pinned site only names
  the method; whether the estimator is computed as defined (HH1, 0.6745, the fixed tile set
  from the SOURCE luma) and the tests really validate it; whether every render is labelled with
  the `Params` actually used; whether "bound" flags are read from the pipeline's own record, not
  re-derived; whether the claim 10 variant (B) derives alpha from smoothed values as stated;
  whether every number in the report is in a record; whether any write could leave
  `work/wp1.4b/`.
- Reviewer B is the orchestrator's own seat pass on the merge candidate.

## Notes for the cell

- Return report = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4: per-commit change list; the flip's site list; validation lines; verification-loop
  record; review rounds, ledger and evidence paths; locks honoured; the Gate result 4 table;
  the clamp and N{} floor recommendations with grounds; claim 10's outcome; deviations and open
  questions.
- **Context depth.** The orchestrator reads your context depth at every yield. Keep tool output
  short (tail it; write long output to files under `work/wp1.4b/`). Keep the ledger current at
  each commit, so a re-seated successor can start from the branch head, this brief and the
  ledger.
- STOP for: a pinning site that needs more than naming the method; a bit-identity change on an
  explicit-method path; an estimator that fails its own validation tests; a GPU failure; any
  need to change `temporal.py`, `pipeline.py` or `tools/lookcheck/`; any output outside
  `work/wp1.4b/`; `deep-frames.json` missing or holding fewer than 8 deep frames.
- Working rules: `uv sync` in the worktree; commit by pathspec with `feat(wp1.4b): ...` and the
  footer; never a bare `cd`; never post to a mailbox; the footage folder is input-only; the
  local config is never committed.
