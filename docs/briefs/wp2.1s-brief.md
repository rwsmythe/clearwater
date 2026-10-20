# WP2.1S — Transport and photo I/O spike (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator (generation 3) on 2026-10-20. Commissioned by CHARC
(`d99b28e575726fbd`); draft `07339bc`, revised for CHARC's notes on architecture DRAFT 0.1
(`fa9d637063376263`); APPROVED by CHARC with rulings (`5152ed4302874889`, section "Rulings").
Owner decisions: none (agreed by CHARC).
Spec **v0.5.3**. Architecture **DRAFT 0.1** (`docs/architecture.md`, `docs/decisions.md`,
`a27a6f7`): this spike **closes AD-2** (the frame transport) and **AD-17** (the 16-bit PNG + ICC +
EXIF path), and **confirms or corrects AD-18** (licences, including PyAV's wheel build flags).
IF-1 (`Frame.pts` exact per frame) and IF-5 (`VideoSource.frames`) are the contracts the
transport must be able to serve; the spike does not implement them. Cell: `implementer-opus-high`. Tier **STRONG**. Worktree
`.worktrees/wp2.1s`, branch `wp2.1s`, base = the main commit named at dispatch. Footage READ-ONLY;
outputs under `work/wp2.1s/` only.

**Why this spike.** WP2.1 (CHARC) chooses the video transport and the photo I/O libraries (plan
section 8.3) and needs measured evidence for both. Part B (`docs/reports/wp1.2b-speed-memory.md`
section 2, "The pipe") found the 32 KB raw pipe is the analysis pass's bottleneck:
- FFmpeg decoding GX011627 to NUL: 16.2 ms/frame.
- The same decode through the pipe into Python: 93.6 ms/frame; no read over 32,768 bytes.
- A Python child writing in 1 MB / 25 MB blocks: 5.4 / 4.0 ms per 4K frame.

The gate report (`docs/reports/wp1.6-gate-report.md`, Result 1 and candidate #6; Option C) leaves
the transport choice to WP2.1 and says large-block writes are required. Part B's #6 is an
ESTIMATE: -20 to -30 % on the analysis pass. This spike measures it. On photos, the plan lists
Pillow / pypng / OpenCV for "16-bit RGB with both a color profile and EXIF, to be verified".
That has never been verified, and no owner photo exists yet (D102).

| Field | Content |
|---|---|
| ID and title | WP2.1S — Transport and photo I/O spike; evidence for WP2.1 (plan section 8.3) |
| Goal | (1) Decode-to-NumPy time per frame on GX011627, with byte-identity against today's pipe, for each candidate transport; plus an analysis-pass projection. (2) Proof, or disproof, that HEIC reads with ICC and orientation, and that a 16-bit RGB PNG writes with ICC and EXIF, each verified by a reader other than the writer. (3) A license position for every candidate (N13). |
| Spec clauses | Architecture DRAFT 0.1: AD-2, AD-10 (swscale in the transport), AD-17, AD-18; IF-1, IF-5. Spec: N6 / D106 (the budget the analysis projection is set against; the analysis pass itself has no target); 7.2 (decode pass, proxies); D14 / D116 (photo inputs); D53 and 8.1 (PNG 8/16-bit, ICC matching the source primaries); D24 / D63 (EXIF kept except invalidated fields; orientation applied and the tag reset; thumbnail dropped; dimensions updated; Software set); V5 (photo I/O fidelity), V9 (identity round trip: context only); N13 (licenses); N1 (portability: say what is Windows-only). Plan sections 4.3 (exclusive timing), 8.3 (library candidates). |
| Depends on | WP1.2 Part B (merged, `2dd06cf`): `tools/prototype/clip.py` `decode_command`, its reader, and Part B's ambient and stray helpers. Consumed by import, NEVER modified. The WP1.6 gate report (final text `b02ab34`). |
| Files owned | `tools/spike_io/` (NEW: `__init__.py`, `transport.py` (the timing instrument), `photo.py` (the photo leg), and helpers as needed); `tests/test_spike_io_photo.py` (synthetic photo leg ONLY: no timing tests, no footage tests); `docs/reports/wp2.1s-io-spike.md`; `docs/proofs/wp2.1s-ledger.md`. `pyproject.toml`, ONLY to add `av` (PyAV) to the `dev` group with a one-line provenance comment (CHARC grant `5152ed4302874889`; spike and prototype only) and any mypy override it needs; and `uv.lock`. No other dependency (pypng and piexif are NOT granted). NOT owned: `tools/prototype/` (any change, even a hook, is a STOP); `src/clearwater/`; the harness. |
| Interfaces consumed | `local_config.find_footage_file` (WP-T2): GX011627 is named by stem only; `tools.prototype.clip` (`Source`, `decode_command`, `read_frame`, `frame_buffer`, `decode_frames`) and `tools.prototype.bench` (`stray_processes`; the ambient helpers `_ambient`, `_gpu_state`, `_windows_power` may be imported or copied into `tools/spike_io/`, said which), all as merged; the advisory idle gate is Part B's uncommitted `work/wp1.2b/gate/idle_gate.ps1`: copy it into `work/wp2.1s/` and record its md5 (it is not a repository file); `ffmpeg`/`ffprobe` 9.0.2 (gyan full build) from PATH. |
| Interfaces provided | None frozen. This is evidence; WP2.1 decides. |
| Hardware flags | Transport leg: **exclusive** (plan 4.3) under the owner's best-effort ruling (the Part B release: contaminated figures are reported as spread, not discarded). Photo leg: not timed, not exclusive. |
| Out of scope | Encode, export, mux; the core (`correct()`); any optimisation of the prototype; changing defaults; JPEG/PNG/TIFF *inputs* (D14) beyond HEIC; owner photos (none exist; never download a sample photo); viewer checks (V5's "multiple viewers" is a later, owner-visible check); NVIDIA runtime redistribution (WP5.5); installing any system tool (exiftool included, ruling 2); `src/clearwater/`. |
| Done | Plan 4.5; ruff, format, mypy (strict, `tools`) and pytest green, with `footage` and `gpu` RUN where they apply; harness gate untouched; every timed figure in a JSON record under `work/wp2.1s/` with its ambient record; the report has the tables below; Reviewer A converged. |

## What the package delivers (claims)

### Claim 1 — Transport, decode to NumPy (GX011627, 681 frames, 3840x2160 `rgb24`)

Every row decodes the SAME 681 frames to the SAME bytes as Part B (GX011627 is the ONLY clip;
CHARC `fa9d637063376263`): the decode chain of
`clip.decode_command` (tag-driven `scale` with `in_range`, `in_color_matrix`,
`out_range=full`, `accurate_rnd`, then `rgb24`; `-noautorotate`; `-fps_mode passthrough`). Each
frame ends as a C-contiguous `uint8` NumPy array of shape (2160, 3840, 3) in the consuming
process. That arrival is the end of the work being timed. Each frame's arrival is timed;
s/frame is the bracket divided by 681 (first byte requested to last frame whole).

| Row | Transport | Required? |
|---|---|---|
| a | Today's pipe: `decode_command` as-is, read with `clip.read_frame` as `decode_frames` reads it. The baseline; reproduces Part B's 93.6 ms/frame or explains the difference | yes |
| b | FFmpeg process, pipe written and read in 1 MB+ blocks. The FFmpeg-side knob that makes this happen is a FINDING, not given: try `-avioflags direct`, the pipe protocol's `blocksize` option, and Python `readinto` into a preallocated frame buffer, alone and combined; report the write sizes actually seen | yes |
| b-cuda | Row b's best form with `-hwaccel cuda` (parity with Part B's analysis rows) | yes |
| s | FFmpeg process writing to a loopback TCP socket that Python reads in 1 MB+ blocks | only if cheap (under about 30 min of build); else say why it was skipped |
| c | PyAV in-process, software decode, `to_ndarray`/`reformat` to `rgb24` with the same range and matrix conversion; decoder threading stated (PyAV's default and `thread_type="AUTO"`, both measured) | yes, if CHARC grants `av` |
| c-cuda | PyAV with CUDA hardware decode, if the installed wheel's FFmpeg build carries it (report the build's hwaccels either way) | only if the wheel allows |

- **Byte identity is part of every row.** Record a per-frame SHA-256 for row a. Every other row
  is compared frame by frame against it, on frame count, pts list, and hashes.
- **If a row's bytes differ:** report the differing-frame count, the max absolute difference,
  the fraction of differing samples and the cause if found (PyAV's swscale flags are a likely
  one). Mark the row **NOT SAME WORK**. Do not tune the conversion until the hashes match
  unless it takes one documented flag change.
- **Exact pts per candidate (IF-1; CHARC `fa9d637063376263`).** Raw video carries no
  timestamps, so every row reports how it delivers each frame's exact pts in source ticks.
  - The reference is ffprobe's per-frame pts list for the stream (`-show_entries frame=pts`),
    captured once, outside the windows.
  - PyAV: packet/frame pts from the demuxer.
  - FFmpeg process: a side channel. Candidates are `showinfo` on standard error (Part B's
    `showinfo=` option), a second output carrying timestamps, or ffprobe alignment by index;
    with `-copyts` where it applies.
  - Per row report: all 681 pts exact, yes or no (first mismatch if not); the side channel used;
    its cost, timed with and without it on the row's best form. A row that cannot deliver exact
    pts is marked **FAILS IF-1**, whatever its speed (ruling 4).
  - Per row, also one line on whether the WP1.5 section 8 muxer options stay reachable with that
    transport (AD-2). For a decode-only candidate (PyAV decode, FFmpeg-process encode) the
    encode side is unchanged; say so.
- **Swscale flags (AD-10).** Row a's chain uses `accurate_rnd`; AD-10 names
  `accurate_rnd+full_chroma_int+bitexact` for the product. Byte identity is judged against
  row a. Record once, untimed, whether row a's hashes change under AD-10's flags; that is a
  finding for WP3.5, not a re-timing.
- **Repetition:** 3 full-clip runs per row. Report median and min/max of s/frame, plus the
  per-frame min / median / max of the run of record.
- **Analysis-pass projection (claim 1's headline):** for each SAME-WORK row, projected
  analysis s/frame = the row's decode-to-NumPy + Part B's measured per-frame work. That work is
  proxy plus staged statistics, 0.050 s/frame (W3b, contaminated; quote it so).
  - Compare with Part B's measured analysis: 0.0707 s/frame on GX011627, and 0.1190 / 0.1101 on
    GX011625.
  - Label every projected figure PROJECTION. Say whether the reader overlaps decode with the
    work (a reader thread), since that changes the sum to a max.
  - Give minutes per minute of footage. No export projection beyond one sentence: the core
    dominates export (Part B section 10, #6).

### Claim 2 — Photo I/O (synthetic images only)

- **HEIC read (pillow-heif, as locked: 1.8.1).** Write synthetic HEICs with pillow-heif's own
  encoder (or say it has none and how the fixtures were made):
  - 8-bit, and 10-bit if the encoder allows;
  - each with an embedded ICC profile that the test builds itself, with Display P3 primaries. It
    must open in `ImageCms`; no third-party profile file is committed;
  - each with EXIF Orientation 1, 6 and 8;
  - plus one carrying an `irot` transform, if the encoder can write one.

  Read each back. Report per case:
  - ICC bytes identical, yes or no;
  - EXIF read, and which fields;
  - whether the pixels come back already rotated, and by which mechanism (`irot` or EXIF);
  - whether the Orientation tag is still present after the read. Applying the rotation twice
    is the failure to look for (D63);
  - the bit depth the 10-bit case returns, and the option that controls it.
- **16-bit RGB PNG write with ICC and EXIF (AD-17's path, PENDING this spike).**
  - AD-17 names Pillow (as locked: 12.3.0) for 16-bit PNG writing, Pillow ImageCms for profiles,
    and Pillow's EXIF writer (AD-17's piexif fallback is NOT granted for this spike). Try that
    path first. Whether Pillow can write 16-bit-per-channel RGB is a FINDING: the orchestrator
    expects it cannot, and the cell verifies that rather than assuming it.
  - If Pillow cannot write a 16-bit RGB PNG with both the ICC profile and the D63 EXIF subset:
    the ONE alternative is a stdlib PNG writer in `tools/spike_io/` (zlib + struct; `IHDR`
    16-bit RGB, `iCCP`, `eXIf`, `IDAT`, `IEND`), with the EXIF bytes built by Pillow's
    `Image.Exif` (ruling 1b). If that also fails, STOP with the finding; no third attempt.
  - The EXIF written is the D63-edited set: Orientation 1, no thumbnail (IFD1 removed),
    PixelXDimension/PixelYDimension updated, Software `Clearwater`, the other source fields
    kept.
  - Also write an 8-bit RGB PNG with ICC and EXIF through Pillow, since 8.1 offers both depths.
- **Verification by a reader other than the writer.** Re-read every written PNG with a reader
  that did not write it:
  - exact 16-bit sample values;
  - `iCCP` bytes identical to the source profile;
  - the `eXIf` content as written;
  - the chunk order: `iCCP` before `IDAT`; and where `eXIf` sits, with whether Pillow's reader
    finds it.

  Name which reader verified which property. A small stdlib chunk/zlib decoder in the test
  counts as an independent reader, but not for a file the stdlib writer wrote (use Pillow,
  and for exact 16-bit values a decoder written separately from the writer, said so).
  exiftool is ABSENT on this machine (`which exiftool`, 2026-10-20): record its absence in the
  report; do not install it (ruling 2).
- **Tests:** `tests/test_spike_io_photo.py` covers each of the above as a pytest case on the
  synthetic fixtures. A planted defect must fail by name: a wrong ICC byte, a stale Orientation,
  a 16-bit value truncated to 8 bits.

### Claim 3 — License positions (N13; confirms or corrects AD-18)

One row per candidate, one line each. Each row also says whether it CONFIRMS or CORRECTS AD-18's
entry (AD-18 records, for example, pillow-heif bundling libheif LGPL-3, libde265 LGPL-3 and
x265 GPL-2, and the FFmpeg build as GPL-2.0-or-later when built with libx265). An entry AD-18
lacks (PyAV and its bundled FFmpeg) is NEW. For the bundled FFmpeg, record LGPL or GPL, and
which codecs, NVENC and NVDEC it carries: that build would ship with the product if PyAV wins
(ruling 1a).

| Name | Version | License | GPL-2.0-or-later compatibility (yes / yes-if / no / UNKNOWN) | One-line reason |
|---|---|---|---|---|

- **Rows:** PyAV, and the FFmpeg its wheel bundles; pillow-heif, and the native libraries its
  wheel bundles (libheif, libde265, x265, any others; read from the wheel's bundled license
  files); Pillow; NumPy; CuPy (already granted, MIT); the
  FFmpeg CLI build in use (gyan 9.0.2 full: from `ffmpeg -version`'s configuration line).
- **PyAV's build flags:** the bundled FFmpeg's configuration string (`--enable-gpl`,
  `--enable-version3`, `--enable-nonfree` present or absent), its version, whether it carries
  the `hevc` decoder, the `h264` decoder, `hevc_nvenc`, `h264_nvenc` and the `cuda` hwaccel.
  Read these from the installed package, not from documentation.
- These are evidence for WP2.1, confirmed at WP5.5 (plan 8.3 license note). Not legal advice:
  mark anything not read from the artefact itself UNKNOWN.

## Decisions fixed at issue

- **Measure, do not tune** the prototype. `tools/prototype` is read-only for this package.
- **Machine-time cap: 2 hours for the transport leg in total.**
  - Before opening any timed window, write its estimate in the ledger.
  - If the remaining estimate would pass the cap, STOP and report what is measured.
  - Row a at Part B's speed is about 64 s per run.
- **Contamination rule (transport windows).**
  - Each window opens and closes with a probe: row a on its first 120 frames.
  - A window is contaminated if the closing probe drifts more than 10 % from the opening one,
    or a stray check shows a non-system process at 25 % or more of a logical CPU.
  - Contaminated figures are kept and reported as spread (best effort, owner); one re-run per
    window at most.
- **Ambient record as Part B.** Per window: head SHA and changed files; local start and end;
  power scheme and overlay; AC/battery; the card's state at the start and end (P-state, SM
  clock). Before and after each run: the 10 s psutil stray check. Before each window: the
  advisory idle gate. No sampler uses CIM or WMI (CHARC ruling f2d35c83 condition 2).
- **No output outside `work/wp2.1s/`.** Every FFmpeg command writes to a pipe or a socket only.
  A synthetic fixture is written under pytest's basetemp or `work/wp2.1s/`. The footage folder
  is input only.
- **GPMF/IMU/GPS out of scope** (owner 2026-10-19): `-map 0:v:0` only. Nothing from a `gpmd`
  track is read or committed.

## Rulings (CHARC `5152ed4302874889`, 2026-10-20)

1. **(a) `av` (PyAV): GRANTED** into the `dev` group, spike and prototype only, as CuPy was.
   Product adoption is WP2.1's. Claim 3 records the licence of the wheel's bundled FFmpeg build.
   **(b) PNG alternative: NO new dependency.** pypng is not granted. The alternative is the
   stdlib zlib + struct chunk writer; if it fails too, STOP with the finding.
2. **exiftool: do not install.** Record its absence in the report.
3. **Exclusivity:** the owner's Part B ruling ("Best effort is fine", 2026-10-19) covers this
   transport leg; no new owner question. Nothing else runs at this seat during its windows (no
   other cell, no harness gate, no Reviewer B of another package).
4. **Exact pts (AD-2 / IF-1):** every transport row reports whether the exact per-frame pts
   reaches Python, 681/681 against ffprobe. A transport that cannot deliver exact pts FAILS
   IF-1 regardless of speed; say so in the row (claim 1).

**Owner decisions:** none. No owner-reserved item is touched: no footage category, look
check, mandatory-requirement relaxation or spec change. GX011627 is already in use as Part B's
evidence clip.

## Declared operating envelope

Windows 11; FFmpeg 9.0.2 (gyan full build, NVENC/CUDA); RTX 4070 Laptop (8188 MiB); 32 GB RAM;
GX011627 (HERO13 4K 29.97 HEVC 8-bit 4:2:0 BT.709 full range); synthetic photos only. Out of
envelope: 10-bit and VFR video (none exists), other cameras, real iPhone HEICs (none supplied:
the HEIC verdict is PROVISIONAL until an owner photo is read; say so), other operating systems
(name every Windows-only element found, N1).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**. Transport, flags, probe, diff, prompt, per-round assertions and evidence
  layout follow the WP1.5 brief with `wp2.1s` substituted. Evidence in
  `clearwater-review-evidence/wp2.1s/rN/`; ledger `docs/proofs/wp2.1s-ledger.md`. Reviewer A
  rounds run OUTSIDE the timed windows.
- **WHAT TO EXAMINE:**
  - whether every row is truly the same work (hashes, pts, frame count) and the bracket covers
    arrival as a whole NumPy frame;
  - whether row a reproduces Part B, or the difference is explained;
  - whether the block size claimed for a row is the one actually observed;
  - whether a projection is labelled PROJECTION and its arithmetic is right;
  - whether each row's pts claim is checked against ffprobe on all 681 frames;
  - whether the HEIC orientation finding distinguishes `irot` from EXIF and catches a double
    rotation;
  - whether the 16-bit PNG check reads exact values with a reader other than the writer;
  - whether every license row is read from the installed artefact;
  - whether any command could write outside `work/wp2.1s/` or into the footage folder.
- Reviewer B is the orchestrator's own seat pass on the merge candidate (fill Part 2 item 2),
  after the timed windows close.

## Notes for the cell

- **Return report** = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4. Include:
  - the transport table: row, s/frame median and spread, SAME/NOT SAME WORK, observed block
    size, pts exact (side channel and its cost), muxer options reachable, contamination;
  - the AD-2 and AD-17 evidence in one line each, and the AD-18 rows CONFIRMED / CORRECTED /
    NEW;
  - the projection rows;
  - the photo results table;
  - the license table;
  - Reviewer A rounds and verdict;
  - record paths.
- **STOP for:**
  - any need to change `tools/prototype`;
  - a dependency beyond the grant (`av` only);
  - the stdlib PNG writer failing after Pillow (ruling 1b);
  - the 2 h cap;
  - row a more than 25 % off Part B's 93.6 ms/frame with no attributable cause (re-run once,
    then STOP);
  - any output outside `work/wp2.1s/`;
  - any write near the footage folder.
- **Working rules:**
  - `uv sync` in the worktree; commit by pathspec with `feat(wp2.1s): ...` and the
    `Co-Authored-By:` footer.
  - Never a bare `cd`; absolute paths or `git -C`.
  - Never post to a mailbox.
  - The local config is copied into the worktree by the orchestrator and never committed.
  - Read your depth with `uv run python scripts/cell_depth.py` at each round boundary; ~400K is
    a STOP at the boundary (dispatch recipe section 5).
