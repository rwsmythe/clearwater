# WP1.2 Part B — Real footage speed and memory (dispatch brief, DRAFT by CHARC)

**Status:** DRAFT by CHARC 2026-10-15 for the orchestrator to finalise and dispatch when ALL
of these hold: (1) the owner has said the footage download is complete and the real
inventory pass has reported (the recording modes and the largest photo come from it); (2)
WP1.3 and WP1.4 (shallow parts) are merged, or paused at a boundary, because this package is
EXCLUSIVE (plan section 4.3) and uses WP1.4's statistics extraction; (3) WP1.5 is merged
(it is). Spec **v0.5.2**. Cell: `implementer-opus-high`. Worktree `.worktrees/wp1.2b`, branch
`wp1.2b`, base = the main commit named in the dispatch. Footage READ-ONLY; outputs under
`work/wp1.2b/`. **Exclusive from dispatch to return:** no other cell, no harness gate, no
Reviewer B run of another package while a timed run is live; the orchestrator schedules
nothing in parallel.

**Why Part B.** Part A (`docs/reports/wp1.2a-speed-memory.md`, accepted `f6d998a`) settled
the mechanism and library and measured SYNTHETIC per-frame figures. The plan's WP1.2 measures
on the inventory's recording modes, a full real clip end to end with decode and encode, the
largest real photo, and analysis speed. Part B is those figures. **Gate 1 (speed) and Gate 2
(memory) close on this report**, at WP1.6, by CHARC, with the N6 decision reserved to the
owner if the target is missed (plan section 10). The `.LRV` leg is gone (D60 closed, v0.5.2).

| Field | Content |
|---|---|
| ID and title | WP1.2 Part B — CPU/GPU variant, real-footage speed and memory; plan section 6 WP1.2; Gate results 1 and 2 |
| Goal | On the owner's real footage: per-frame core time on the GPU (and CPU, one short run) in EVERY recording mode the inventory lists; a FULL-CLIP end-to-end timing (decode → correct → encode → mux, the WP1.5 SIMPLE path with the correction inserted), sustained, on two clips; peak RAM and graphics memory on the largest video mode and on the largest photo in the inventory, with the CPU fallback exercised if the photo's estimate exceeds the card; analysis-pass speed (decode to proxy and the staged statistics of WP1.4) with software decode and with hardware decode; the proxy-resolution effect on real frames. Every figure against the N6 budget and the N4 limits. |
| Spec clauses | N6 / D106 (3.3 min per min, 0.111 s per 4K frame at 30 fps, 0.056 s at 60 fps, END TO END; measured at 4K in the owner's modes; 5.3K best effort); N4 / D68 / D110 / D111 (16 GB RAM, graphics memory as a second limit, automatic CPU fallback); N5 item 1 and 2; D109 (sparse analysis in reserve: only if analysis speed is unacceptable); D107 (one code path); 7.2 and 7.3 (decode pass, proxies); V15, V16. Plan section 4.3 (exclusive, full clip), section 10 rows 1 and 2. |
| Depends on | WP1.2A, WP1.5 (merged); WP1.3 and WP1.4 shallow parts (merged, or paused at a boundary); the real inventory report (modes, largest photo, chaptered recordings); full CP1 is NOT needed. |
| Files owned | `tools/prototype/bench.py` (extend: a `--input <video or image>` real-frame source beside the synthetic one; an end-to-end mode), `tools/prototype/clip.py` (NEW: the end-to-end runner: FFmpeg decode to a raw pipe → `correct()` per frame → FFmpeg NVENC encode from a raw pipe → mux, with the WP1.5 flags for timestamps, tags and audio copy), `tests/test_prototype_clip.py`, `docs/reports/wp1.2b-speed-memory.md`, `docs/proofs/wp1.2b-ledger.md`. `tools/prototype/pipeline.py`, `params.py`, `backend.py` NOT owned (no numerical change; a needed hook is a STOP). NO `pyproject.toml` change. |
| Interfaces consumed | `tools.prototype` as merged (incl. WP1.4's `temporal.py` statistics extraction and the `statistics=` hook); `tools.lookcheck.frames` for still frames; `tools/container_spike/compare.py` to verify the end-to-end output's container (MANDATORY and REQUIRED items SAME against the source, as WP1.5 did for the identity re-encode); `ffmpeg`/`ffprobe`; `tools/inventory.py` output (the modes list) by reading its CSV/JSON, not by re-scanning. |
| Interfaces provided | None frozen. `clip.py` is the first draft of the product's export loop (WP3.14/WP3.9/WP3.10 read it); its decode/encode pipe shape and buffer sizes are documented in the report for WP2.1. |
| Dependencies | None new. |
| Tests | `tests/test_prototype_clip.py`: synthetic clip through `clip.py` with `--neutral` parameters (the identity set, V9) yields a decodable HEVC MP4 whose frame count, pts sequence and tags are SAME per `compare.py`, and whose frames match the source within the encode's PSNR floor (state it); the raw-pipe frame boundaries are exact (a frame-size assertion; a planted off-by-one must fail by name); the bench's real-frame source reads one frame at the exact pts; `gpu`-marked; `footage`-marked smoke on `GX011628.MP4` (434 frames). |
| Hardware flags | `gpu`, `footage`, **exclusive**. Every figure carries its conditions (plan 4.3 / fill GATE_CHECKS): full clip, nothing else heavy, the moment of the reading, power scheme and overlay, GPU clocks and state at loop start and end (the WP1.2A ambient record), the stray-process check. |
| Out of scope | Optimising the core (CHARC ruling stands: measure, do not tune; candidates are LISTED for WP1.6 with a one-line cost estimate each); any default change; chapter spans; the product's export engine; the `.LRV` leg (D60 closed); sparse analysis (D109: only named if analysis speed is unacceptable); `src/clearwater/`. |
| Done | Plan section 4.5; gates green with `gpu` and `footage` RUN; harness gate untouched; every figure in a JSON record under `work/wp1.2b/` with its ambient record; the report complete with the tables below and the budget comparison; the end-to-end outputs verified by `compare.py`. |

## What the package measures (claims)

1. **Modes.** From the inventory report: every video recording mode present (resolution,
   frame rate, bit depth). Expected at least 4K 30000/1001 HEVC 8-bit (the four shallow
   chapters); the scuba clips may add modes. One representative clip per mode, named in the
   report with its pts range.
2. **Per-frame core time on real frames** (the WP1.2A table, real): for each mode, GPU,
   both methods, N = 60 sustained frames read from the clip (consecutive frames from 30 % of
   its duration), median and p95 and drift, with the WP1.2A ambient record. CPU: one run per
   mode, `ancuti2018` only, N = 10 (it is 11 s per frame). Compare with the synthetic rows:
   the difference is the real content's effect (texture, noise), stated.
3. **Full clip end to end (N6 as written).** Through `clip.py` on the GPU, `ancuti2018` at
   defaults, with the WP1.4-recommended smoothing applied from a prior analysis pass (so the
   loop is the product's render pass: decode → render with supplied statistics → encode):
   `GX011627.MP4` (681 frames, 22.7 s) and `GX011625.MP4` (14938 frames, 8.3 min), each
   timed from the first decoded frame to the muxer's close; report seconds per frame and
   minutes of processing per minute of footage against 3.3. Then the SPLIT on `GX011627`:
   decode-only pass-through (decode to the pipe, discard), encode-only (feed the decoded
   frames unchanged), and the core alone (claim 2), so the report shows where the time goes.
   Output verified by `compare.py` (MANDATORY and REQUIRED SAME; best-effort differences
   listed). The device-resident variant (WP1.2A supplementary) MAY be timed as a second row
   but the production-shaped row is the figure.
4. **Analysis speed** (7.2 decode pass + statistics): on `GX011625.MP4`, frames decoded to
   the proxy (short side 540) and the staged statistics computed (WP1.4's path), once with
   software decode and once with `-hwaccel cuda` decode; seconds per frame and minutes per
   minute of footage. D109 is named only if both are unacceptable (the report states the
   number; CHARC judges acceptability at WP1.6).
5. **Memory (N4, V15).** Peak RSS and peak graphics memory during claim 3 on the largest
   video mode in the inventory (5.3K 8:7 if present, else the largest present, said so);
   and on the largest photo in the inventory through `run.py --device gpu`: the
   `memory_estimate_bytes` figure, the measured peak, whether the estimate exceeded the
   card's free memory, and whether the CPU fallback engaged (if it did not, force it once with
   `--device cpu` and record the CPU peak RSS). Against 16 GB and 8188 MiB.
6. **Proxy resolutions on real frames** (WP1.2A section 8 repeated): short sides 270, 540,
   1080 and full, on 20 frames of `GX011627`: each whole-frame statistic's deviation from the
   full-frame value, with WP1.4's stability measure.
7. **Optimisation candidates, listed not done:** from the measured split, each candidate
   with the step it targets and a one-line cost/benefit estimate (3C Gaussian by FFT or
   recursive filter; device-resident pipeline; fewer intermediates copied back; pyramid
   memory; decode/encode overlap with the core through pipelining). This is CHARC's input for
   the Gate 1 options to the owner.
8. Docstrings complete; the four gates green; no change outside owned files.

## Decisions fixed at issue (CHARC)

- **Measure, do not tune.** The core's mathematics and defaults are frozen for this package
  (WP1.1 open values, WP1.2R). Gate 1 is decided on what IS, with the candidates of claim 7
  as the options.
- **The end-to-end loop is production-shaped:** FFmpeg decode → raw RGB pipe (8-bit source
  → `rgb24`; a 10-bit source → `rgb48le`; FFmpeg does the YCbCr→RGB and chroma upsampling
  here, which the product does itself under WP3.5: say so) → float32 → `correct(...,
  statistics=smoothed)` → raw pipe → `hevc_nvenc` at the source's bit depth with the WP1.5
  tag and timestamp flags → mux with audio and data copied. Frame timestamps are carried by
  the decode order (CFR on these clips; a VFR clip gets `-fps_mode passthrough` and a
  per-frame pts list, stated). Bounded buffering: at most 2 frames in flight each side.
- **Smoothing is applied, not computed, in the timed export loop:** the analysis pass is
  timed separately (claim 4), as the product separates them (7.2).
- **Exclusivity and ambient record** as WP1.2A: power scheme and overlay, GPU state at loop
  start and end, stray-process check, the harness gate never inside a window, every timed
  window's head SHA and local time.
- **Largest photo:** whatever the inventory names; if no photo is present at dispatch, claim 5's
  photo half is PENDING and WP1.6 says so (D102).
- **Outputs.** `work/wp1.2b/` only; the end-to-end MP4s are evidence, not committed.
- **ffmpeg invocation** as WP1.5: inside `work/wp1.2b/` only, with the output-path assertion.

## Declared operating envelope

Windows 11, FFmpeg 9.0.2 (NVENC), the owner's HERO13 footage in the inventory's modes,
`ancuti2018` and `c3` at defaults, RTX 4070 Laptop (8188 MiB), 32 GB RAM, the machine
otherwise idle. Other cameras, HDR/GP-Log, chapter spans, photos above the inventory's
largest, and any tuning are out of envelope.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**. Transport, flags, probe, diff, prompt, per-round assertions, evidence
  `clearwater-review-evidence/wp1.2b/rN/`, ledger `docs/proofs/wp1.2b-ledger.md`, exactly as
  the WP1.5 brief states them with `wp1.2b` substituted. Reviewer A rounds run OUTSIDE the
  timed windows.
- WHAT TO EXAMINE: whether the end-to-end timing brackets the whole loop (first decoded frame
  to muxer close) and the split rows add up within the stated tolerance; whether the raw
  pipe's frame boundaries are exact; whether the output's container passes `compare.py`;
  whether the smoothed statistics applied are the ones from the analysis pass on the same
  clip; whether every figure carries its ambient conditions; whether the minutes-per-minute
  arithmetic is right; whether any ffmpeg flag could write outside the working folder.
- Reviewer B is the orchestrator's own seat pass on the merge candidate (fill Part 2 item 2),
  run AFTER the timed windows close.

## Notes for the cell

- Return report = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4, with the per-mode table, the end-to-end rows with minutes per minute, the split,
  the analysis-speed rows, the memory rows, and the optimisation candidates list; every row
  with its record path and ambient summary.
- STOP for: a mode the prototype cannot process (memory); a pipe/encode failure that cannot
  be made byte-exact; a figure that moved more than 10 % between two windows without an
  attributable cause (re-run once, then STOP); any need to touch `pipeline.py`; any output
  outside `work/wp1.2b/`.
- Working rules as the WP1.5 brief: `uv sync` in the worktree; commit by pathspec with
  `feat(wp1.2b): ...` and the `Co-Authored-By:` footer; never a bare `cd`; never post to a
  mailbox; the footage folder is input-only; the local config is copied into the worktree by
  the orchestrator and never committed.
