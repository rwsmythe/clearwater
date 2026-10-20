# WP3.5 — Video colour handling and chroma resampling (dispatch brief, FINAL)

**Status:** FINAL 2026-10-20, approved by CHARC 53b752a4d7fac4fc with rulings; base = the pre-dispatch main commit named at dispatch. Drafted by the
orchestrator (gen 6, drafting helper). Owner decisions: none inside the package (the output tags
of an untagged source are decided by DR-17 and are WP3.10's). The package's boundary is ruled
(ruling 5.1): what plan WP3.5 describes is largely done by FFmpeg (AD-10) and by WP3.7's probe;
this brief states what is left, re-sized S.
- Spec **v0.5.4**. Architecture FINAL 1.0 section 3 IF-1 and IF-5, section 5; AD-2, AD-10,
  AD-11, AD-19, AD-20. Frame `docs/briefs/wp2.4-phase3-frame.md` (sections 1-4). WP3.7 report
  `docs/reports/wp3.7-video-probe.md` (claim 2, D54 per field). DR-20 item (1) (closes),
  WP3.1 R0-1, DR-36 (c), DR-17 (row "Debt and decided items").
- Cell: `implementer-sonnet-high` (ruling 5.1; the frame named opus-high). Tier **STRONG**.
- Worktree `.worktrees/wp3.5`, branch `wp3.5`, base = the main commit named at dispatch.

**Why.** WP3.9 (decode) and WP3.10 (encode) are wave 3 and run in parallel (plan "Depends on
WP3.5, WP3.7"). Each needs one half of a matched pair: the swscale arguments that take the
stream's Y′CbCr to the working RGB and the arguments that take it back, plus the conversion
between FFmpeg's planar integer samples and IF-1's float32 `(H, W, 3)` array. If each package
wrote its own half, nothing would hold the two halves inverse to each other; V9's identity round
trip depends on exactly that. AD-10 gives WP3.5 the tolerance test: "The identity round trip
(V9) is measured on the decoded-RGB side of the encoder, with the encoder excluded; WP3.5 owns
the tolerance test." This package builds the pair, the sample conversion and that test before
either transport exists.

**What is already done elsewhere (do not rebuild).** Tag reading and D54: WP3.7's probe maps
ffprobe's tags to the IF-1 vocabulary, applies "BT.709 ... limited range" per missing or
unexpected field, sets `ColorDescription.assumed`, and emits one `missing_tags` `Fault` naming
the fields (WP3.7 report claim 2; `src/clearwater/io/video/probe.py` `_resolve_color`,
`_colour_faults`). Showing the warning is the GUI's (WP3.16 shows G10 messages from
`ProbeResult.faults`). Running FFmpeg, the pipe transport, `-hwaccel cuda`, timestamps:
WP3.9 / WP3.10 (AD-2, AD-23). Encoder options and the output's tag flags (`-color_primaries`,
`-color_trc`, `-colorspace`, `-color_range`): WP3.10 (plan WP3.10 "matches the source's tags and
chroma format"). The Y′CbCr conversion and chroma resampling themselves: FFmpeg swscale (AD-10).

| Field | Content |
|---|---|
| ID and title | WP3.5 — Video colour handling and chroma resampling; plan Phase 3 row WP3.5 (plan size M, re-sized S by ruling 5.1); module `clearwater.color` (plan 8.1 "Video color conversion and chroma resampling", AD-19) |
| Goal | From a probed stream's `VideoStreamInfo` (its D54-resolved `ColorDescription`, `pix_fmt`, `bit_depth`, `chroma_siting`): the FFmpeg arguments that decode to planar RGB at the source bit depth and encode back to the source's Y′CbCr, matrix, range, chroma format and siting, by AD-10's swscale settings; the conversion of planar integer samples to IF-1 float32 RGB in [0, 1] and back (quantisation only there, D39); and the AD-10 tolerance test proving the pair is an identity within AD-11's V9 bound. |
| Spec / decision clauses | 6.5 "**Working encoding:** the pipeline operates on display-encoded RGB in the source's primaries. Neither method requires linearization (3C uses YCbCr, a linear transform of the encoded values)." "**Video in:** matrix, range, primaries and transfer characteristics are read from the stream. If missing or unexpected, BT.709 with limited range is assumed and the user is warned (D54). Chroma upsampling to full resolution is performed before processing." "**Video out:** matrix, range, primaries and transfer tags match the source (D55). Chroma subsampling and pixel format also match the source, normally 4:2:0 for GoPro footage (D114). The resampling method in each direction is fixed at design, because it affects the identity round trip (V9)." 6.4 "All processing in 32-bit floating point, normalized to [0, 1]; quantization only at export." D39 "Internal processing in 32-bit float; quantization only at export"; D54 "Video color tags read from the stream; if missing or unexpected, assume BT.709, limited range, and warn"; D55 "Output video color tags and range match the source"; D76 "Optional 10-bit output for 8-bit sources, off by default"; D114 "Output video chroma subsampling and pixel format match the source". 5.2 "8-bit and 10-bit sources handled without truncating 10-bit data." Feeds V4 "output matches source ... bit depth (or the selected 10-bit option), chroma format ...; color tags match the source" (the colour half; the rest is WP3.10's) and V9 "the output matches the input within a small color-difference tolerance for photos and video. This exercises the full decode → process → encode path, including color tags" (the decoded-RGB half, per AD-10). AD-10 "Chroma resampling in both directions is done by FFmpeg's swscale inside the transport (decode to planar RGB at the source bit depth with `accurate_rnd+full_chroma_int+bitexact`; encode from the same), bicubic in both directions, honouring the stream's chroma siting." AD-11 "V9 identity round trip (neutral parameters, pre-encode): max abs diff **≤ 2/255**, mean ≤ 0.2/255"; "Looser (hides range/matrix errors, which show as ≥ 10/255)". |
| Depends on | WP3.7 merged (`ProbeResult`, `VideoStreamInfo`, the D54 resolution, `clearwater.io.video.find_tool`). WP2.2 (IF-1, IF-5 frozen, `b288533`). WP2.3 video samples: `vid-hevc8-bt709-full` (8-bit, `yuvj420p`, `pc`, BT.709), `vid-hevc10` (10-bit `yuv420p10le`, `tv`, BT.709), `vid-untagged` (H.264 `yuv420p`, no tags: the D54 case), `vid-rotated`, `vid-vfr`, `vid-truncated` (8-bit full; regression rows), and `vid-hlg`, `vid-pq` (refused at probe, so never reach this module); all eight declare chroma location `left`. No BT.601 sample is committed: a test may generate one in `tmp_path` with FFmpeg (question 4). The plan's WP3.1 dependency is not load-bearing (WP3.1 is merged in any case; the backend's `rgb_to_ycbcr` may serve as an independent test reference, see Notes). No stub is needed. |
| Files owned | `src/clearwater/color/` (NEW: `__init__.py`, `swscale.py` (the argument pair and the IF-1 to FFmpeg name table), `samples.py` (planar samples to float32 and back)); `tests/test_color_*.py` (NEW); `docs/reports/wp3.5-video-colour.md`; `docs/proofs/wp3.5-ledger.md`. NOT owned: `src/clearwater/io/video/` (WP3.7 merged; WP3.9 and WP3.10 extend it), `src/clearwater/interfaces/`, `src/clearwater/core/`, `tools/` (no instrument), `pyproject.toml` (no dependency), `tests/conftest.py`, `tests/fixture_plugin.py`, `tests/fixtures/`. |
| Interfaces provided | No frozen interface. The public API of `clearwater.color` (question 1's table) is tabled at round 0 for CHARC; WP3.9 and WP3.10 consume it. |
| Interfaces consumed | IF-1 `ColorDescription` (`primaries`, `transfer`, `matrix`, `range`, `bit_depth`, `assumed`), `Array`. IF-5 `VideoStreamInfo` (`pix_fmt`, `bit_depth`, `chroma_siting`, `color`, `width`, `height`). `clearwater.color` imports only `clearwater.interfaces`, the stdlib and NumPy (it sits below `io.video`, which will import it); tests may use `clearwater.io.video.probe` and `find_tool` and run FFmpeg. |
| Consumers | WP3.9 (decode: the decode arguments, the planar-to-float conversion; yields IF-1 `Frame`s), WP3.10 (encode: the encode arguments, the float-to-planar quantisation, the name table for the output tags), WP4.2 (video path end to end, V9 through the encoder). WP3.21 may later move the sample conversion to the GPU; not here. |
| Hardware flags | FFmpeg-using tests take the `ffmpeg_tools` fixture (they skip when FFmpeg is absent). No `gpu`. `footage` on one optional row (question 5), read-only through `tools/local_config.find_footage_file`, untimed, not exclusive. No timing figure (frame section 3: exclusive timing lives in WP3.1's and WP3.10's reports). |
| Out of scope | Running FFmpeg in product code, pipes, transport, hardware decode selection (WP3.9, WP3.10; AD-2, AD-23); encoder options and output tag flags (WP3.10); re-resolving tags or re-implementing D54 (WP3.7 did it; consume `ColorDescription` as given); the warning UI (WP3.16); photo colour management (WP3.6, D53); any primaries, transfer or gamut conversion (6.5: source primaries kept, no linearisation); HLG/PQ (refused at probe); GP-Log conversion (AD-16: warn only); GPU sample conversion (WP3.21); GoPro IMU/GPS and the `gpmd` track (owner: out of scope; nothing here reads any data stream); chapters (v2). |
| Debt and decided items | **DR-20 item (1) (OPEN, "WP3.5 (colour conversion) owns (1)") — CLOSES:** the D54 fallback the look-check instrument lacked is in the product as WP3.7's per-field resolution (WP3.7 report claim 2; `probe.py` `_resolve_color`): a missing or unexpected primaries, transfer or matrix takes BT.709, a missing range takes limited, `assumed=True`, one `missing_tags` fault naming the fields; an untagged `yuvj` stream is full range with no range warning (WP3.7 brief ruling 7.3, amended: "a `yuvj` pixel format IS a full-range signal"). WP3.5 CONSUMES that `ColorDescription` and those faults; it never re-probes, re-reads tags or re-resolves; task 6 is the closure evidence and the accept records DR-20 (1) CLOSED. DR-20 items (2)-(9) are WP3.10's and 8.4's (the register's trigger) and are not touched. **WP3.1 R0-1 — the one definition, must not fork:** any float representation of limited-range Y′CbCr inside `clearwater.color` or its tests uses R0-1's convention (`docs/proofs/wp3.1-ledger.md`: `Y' = 16/255 + (219/255) Y`, `Cb' = (224/255) Cb`, `Cr' = (224/255) Cr`, chroma centred on 0, exact inverse, unclipped; implemented by `clearwater.core` `rgb_to_ycbcr(..., "limited")`); FFmpeg's integer planes (chroma at 128 or 512) are converted to it explicitly, never given a second float convention. Relation to `samples.py`: the sample conversion handles RGB only (swscale delivers and takes full-range planar RGB, AD-10), so `/ (2**n - 1)` is the RGB normalisation of IF-1 and defines no Y′CbCr float form; R0-1 is needed only where a test builds a float Y′CbCr reference. If the round-0 table finds any product path that needs float Y′CbCr in another form, that is a question to CHARC, not a second definition. **DR-36 (c) — not relied on:** a partial-tag `missing_tags` message can say "limited range" when range is explicitly full; the resolved `ColorDescription` is right, so WP3.5 reads `ColorDescription.range`, never a fault message. **DR-17 (OPEN) — not this package's, cited:** "WP3.10 (video I/O): implement and test the D54 fallback (assume BT.709 limited, warn, tag the output) on a synthetic untagged clip." The output tags of an untagged source are thereby decided (tag the output with the assumed values) and are WP3.10's; WP3.5's name table passes the assumed values through unchanged so WP3.10 can write them. |
| Done | Plan 4.5; frame section 2 rules 1-11; ruff check, ruff format --check, mypy strict, full pytest green (in a granted window, X5); the AD-10 round trip within AD-11's V9 bound on every in-envelope sample, figures reported; DR-20 (1) closure evidence; Reviewer A converged. |

## Task ladder

1. **Read and table (round 0 yield).** Read IF-1, IF-5, `src/clearwater/io/video/probe.py`
   (`_resolve_color`, `_colour_faults`, the `chroma_siting` read), AD-10, the WP2.1S report
   section 2 (the decode command and the a-ad10 row) and the WP1.5 report section 4 (how
   `yuvj420p` / `pc` reaches the encoder). Write in the ledger: for each WP2.3 video sample, the
   probed `ColorDescription`, `pix_fmt`, `bit_depth`, `chroma_siting`, and the decode and encode
   arguments you would build; the proposed public API (question 1); the answers you take to
   questions 2-6. YIELD for the dispatcher before product code.
2. **The argument pair (`swscale.py`).**
   - Decode: one `scale` filter with `in_color_matrix`, `in_range`, `in_chroma_loc` from the
     stream, `out_range=full`, `flags=bicubic+accurate_rnd+full_chroma_int+bitexact` (AD-10),
     then `format=` planar RGB at the source bit depth (`gbrp` for 8-bit, `gbrp10le` for 10-bit;
     AD-10 "planar RGB at the source bit depth"). The same arguments serve software and
     `-hwaccel cuda` decode (WP2.1S row b-cuda used one filter for both).
   - Encode: the inverse `scale` from full-range planar RGB to the source's matrix, range,
     chroma subsampling and siting, same flags, then `format=` the source pixel format (a
     `yuvj` format becomes its non-`j` form with full range, as WP1.5 section 4 fed NVENC), or
     the 10-bit form when the D76 option asks for 10-bit from an 8-bit source.
   - Never pass primaries or transfer options (FFmpeg 9's `scale` can convert them; 6.5 keeps
     the source's). Unsupported inputs per question 3 raise a named error.
   - The IF-1 to FFmpeg name table (`bt709`, `bt601` → `smpte170m`, `display-p3` →
     `smpte432`, `srgb` → `iec61966-2-1`, `limited` → `tv`, `full` → `pc`), the inverse of the
     probe's tables, for the swscale options and for WP3.10's tags.
3. **Sample conversion (`samples.py`).** Planar G, B, R planes (FFmpeg's plane order) at 8 or
   10 bits to float32 `(H, W, 3)` RGB in [0, 1] (divide by `2**n - 1`), and back: clip to [0, 1],
   scale, round per question 2, to the planar layout and dtype FFmpeg reads. 10-bit data is
   never truncated (5.2). Host NumPy; the caller uploads with `backend.asarray`.
4. **The AD-10 tolerance test (V9, decoded-RGB side, encoder excluded).** Per in-envelope sample:
   decode with the decode arguments to raw planar RGB; to float and back with `samples.py`;
   through the encode arguments to raw Y′CbCr in the source pixel format (`-f rawvideo`, no
   encoder); decode that again with the decode arguments; compare the two float RGB results:
   max ≤ 2/255, mean ≤ 0.2/255 (AD-11), the measured figures reported. Also for the D76 path
   (8-bit source, 10-bit out).
5. **Planted wrong arguments fail by name**, each where AD-11 can see it (AD-11: range or
   matrix errors show as ≥ 10/255) and otherwise by an argument-level test: range read as full
   on a limited stream; BT.601 for BT.709; `accurate_rnd` dropped (limited range decodes 2-3
   levels dark, WP1.3 accept); `out_range` not full; the planes in R, G, B order; 10-bit scaled
   by 255; decode and encode siting different; a primaries option present.
6. **D54 consumed, DR-20 (1).** `vid-untagged` probes to BT.709 / limited with `assumed=True`
   and one `missing_tags` fault (WP3.7), and its decode arguments say BT.709 and limited; a
   `yuvj` stream with no range tag is full range with no range warning (WP3.7 ruling 7.3) and
   decodes as full. This is the evidence for closing DR-20 (1).
7. **Dependency rule** (plan 8.1, frame rule 5): a subprocess test that importing
   `clearwater.color` loads nothing from `clearwater.io`, `.core`, `.methods`, `.jobs`, `.gui`,
   `.config`, nor `PIL`, `av`, `PySide6`, `cupy`, and starts no process.

## Declared operating envelope

Windows 11; Python 3.12; the gyan FFmpeg CLI build 9.0.2 on PATH (WP0.1); SDR sources at 8 or
10 bits in planar 4:2:0 (`yuv420p`, `yuvj420p`, `yuv420p10le`; the owner's inventory and the
WP2.3 samples), matrix BT.709 or BT.601, full or limited range, chroma siting as declared;
frames up to 4K (5.3K 8:7 per V15 in principle). Out of envelope: 4:2:2, 4:4:4, RGB-coded
(`identity` matrix) and 12-bit video (question 3), BT.2020 (only HLG/PQ carry it here and they
are refused), other FFmpeg builds, other operating systems (portable, N1, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**, run by you at your seat to convergence; five-round gate. Evidence
  `C:\Users\rwsmy\clearwater-review-evidence\wp3.5\rN\`; ledger `docs/proofs/wp3.5-ledger.md`.
  Copy the runner and prompt shape from `C:\Users\rwsmy\clearwater-review-evidence\wp3.1\r2\`
  (`run_review.sh`, `review-prompt.md`; the round also keeps `review-diff.txt`, `review.txt`,
  `adjudication.md`, `md5sums.txt` as there); the reviewer excludes `docs/proofs` with
  `--glob '!docs/proofs/**'`.
- **WHAT TO EXAMINE:**
  - the decode and encode arguments are inverse for every in-envelope stream (matrix, range,
    subsampling, siting, bit depth) and use AD-10's flags in both directions;
  - no primaries, transfer or gamut conversion anywhere;
  - `ColorDescription` consumed as resolved, never re-resolved; D54's assumed values reach
    the arguments;
  - sample conversion exact at 8 and 10 bits (an integer round trip is the identity), the plane
    order right, quantisation only on the way out;
  - the tolerance test measures what AD-10 says (decoded-RGB side, encoder excluded), with
    figures, and would fail on the planted defects;
  - unsupported inputs refused by name, never guessed;
  - `clearwater.color` imports nothing above it and runs no process;
  - nothing outside the owned files changed.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Yields.** Round 0: read and table, then YIELD before product code. After each review
  round: END YOUR TURN as soon as round N's verdict is adjudicated, BEFORE remediating. Yield
  at every round boundary; the dispatcher reads your depth (~250K evaluation point, ~400K
  stop).
- **Full-pytest windows (X5).** The full suite (about 1844 tests, 9-11 min) runs ONLY in a
  window the dispatcher grants by message, in the background with output to a file under
  `work/`; send `WINDOW RELEASED: <summary>` when it finishes and carry on. Inner loops run only
  your own tests.
- **One float convention for limited range (R0-1).** FFmpeg's integer planes put chroma at
  128 (8-bit) or 512 (10-bit); R0-1 keeps it centred on 0 (row "Debt and decided items"). Where
  a test uses the backend's `rgb_to_ycbcr` as an independent reference for FFmpeg's output,
  convert the integer codes to R0-1 explicitly; do not define another float form.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the public API, the argument pair per sample, the round-trip figures per sample
  (max and mean, in 1/255 units), the planted-defect table, DR-20 (1) evidence, the gates, the
  Reviewer A rounds and verdict, open items for WP3.9 and WP3.10.
- **STOP for:** any change needed in `src/clearwater/interfaces/` (AD-20) or in
  `src/clearwater/io/video/`; a round trip outside AD-11's V9 bound on an in-envelope sample
  (do not loosen it); swscale settings other than AD-10's; any dependency (PyAV stays dev-only,
  AD-2); OS-specific code; the round-0 table showing a choice the brief left open.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.5): ...` (conventional commits
  carrying the WP id), with a `Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>` footer. Never a bare `cd`.
  Never post to a mailbox. Test outputs go under `tmp_path` (the WP-T1 guard keeps the temp
  root out of the footage folder); never write next to a fixture or into the footage folder.
  Gates: ruff check, ruff format --check, mypy strict, full pytest (in a window); no harness
  gate. Report `docs/reports/wp3.5-video-colour.md` (claims, evidence paths, limits). GoPro
  IMU/GPS data is out of scope everywhere.

## Rulings (CHARC `53b752a4d7fac4fc`, 2026-10-20)

CHARC `53b752a4d7fac4fc`, 2026-10-20: every recommended answer is the ruling unless amended here.
- **5.1 (boundary and size):** WP3.5 is the colour-arguments and sample-conversion module with the
  AD-10 tolerance test, as recommended; re-sized **S**; cell **`implementer-sonnet-high`** (tier
  STRONG, Reviewer A at the cell's seat and the yield schedule unchanged). Ground (CHARC): AD-10
  and WP3.7's D54 resolution fix the contract; AD-11 catches a matrix or range error at >= 10/255.
- **5.6 (siting and untagged output):** (a) unknown chroma siting is treated as `left` in both
  directions, passed explicitly. (b) The output tags of an untagged source are DECIDED by DR-17
  ("assume BT.709 limited, warn, tag the output"), and are WP3.10's matter; WP3.5 only cites
  DR-17 and passes the assumed values through its name table.
- CHARC accepted the drafter's corrections to its debt list: WP3.7 brief ruling 7.3 (amended) is
  the citation for an untagged `yuvj` stream being full range; no line here changes.

### Questions as drafted (recommended answer = ruling unless amended above)

1. **The package boundary and its size (thin after AD-10 and WP3.7).** Plan WP3.5 says it
   "converts between the stream's Y′CbCr and the working RGB using the stream's matrix and
   range, resamples chroma in both directions by the method fixed in WP2.1, and applies the
   BT.709/limited default with a warning when tags are missing". After AD-10 the conversion and
   resampling are FFmpeg's, and WP3.7 already applies D54 and emits the warning fault.
   Recommended: keep WP3.5 as the colour-arguments and sample-conversion module, with this
   public API (names indicative; the round-0 table fixes them):
   `decode_filter(stream: VideoStreamInfo) -> str`, `decode_pix_fmt(stream) -> str`,
   `encode_filter(stream, *, bit_depth: int) -> str`, `encode_pix_fmt(stream, *, bit_depth) ->
   str`, `ffmpeg_color_names(color: ColorDescription) -> Mapping[str, str]`,
   `planes_to_rgb(data, *, width, height, bit_depth) -> NDArray[np.float32]`,
   `rgb_to_planes(a, *, bit_depth) -> bytes`, plus the AD-10 tolerance test. Reason: WP3.9 and
   WP3.10 run in parallel in wave 3, and one owner of both halves keeps them inverse, with the
   round trip pinned before either transport exists. Alternatives: fold WP3.5 into WP3.9 (then
   WP3.10 waits for WP3.9's halves, losing wave-3 parallelism), or into WP3.9 and WP3.10
   separately (nothing then owns the pair).
   **For CHARC: re-size M -> S?** Recommended yes (plan row M; the remaining scope is one small
   module and one test family). **Cell: sonnet-high instead of opus-high?** Possible once CHARC
   fixes the API table above; it changes nothing else in the brief except the cell line and the
   `Co-Authored-By:` model name (tier STRONG, Reviewer A, yields and envelope stay as written).
2. **Rounding at quantisation.** Recommended: clip to [0, 1], multiply by `2**n - 1`, round
   half to even (`numpy.rint`), cast to `uint8` / `uint16`; the 8- and 10-bit integer round
   trips are then exact, which a test pins.
3. **Inputs outside 4:2:0 SDR.** The probe can deliver `matrix="identity"` (a `gbr` stream)
   and other pixel formats. Recommended: support exactly `yuv420p`, `yuvj420p`, `yuv420p10le`
   (and `yuvj` with explicit tags) in v1, and refuse anything else with a named error listing
   the supported set (out of envelope; none occurs in the owner's inventory or the samples). A
   later package can widen the set with its own round-trip rows.
4. **BT.601 coverage.** No committed sample is BT.601, but the probe maps `smpte170m` and
   `bt470bg` to `bt601`. Recommended: the test generates a small BT.601 clip in `tmp_path`
   with FFmpeg (`lavfi` source, explicit tags), uncommitted, and runs the round trip on it; no
   WP2.3 change (DR-33's trigger is any change to `tools/fixtures/`).
5. **A footage row.** Recommended: one `footage`-marked test runs the round trip on the first
   30 frames of `GX011627` (4K, 8-bit, BT.709 full range, the owner's main case), read-only
   through `tools/local_config.find_footage_file`, untimed; it skips when footage is absent.
6. **Unknown chroma siting, and the output tags of an untagged source.** (a) `chroma_siting`
   is `"unknown"` when the stream declares none; every WP2.3 sample declares `left`.
   Recommended: treat unknown as `left` (the H.264/HEVC default for 4:2:0) in both directions
   and pass it explicitly, so decode and encode cannot disagree. (b) For a source with assumed
   tags (D54), D55 says the output's tags "match the source", which had none. Recommended:
   WP3.5 only exposes the name table (the assumed values included, `assumed` passed through);
   whether WP3.10 writes the assumed tags or leaves the output untagged is WP3.10's brief to
   settle. Lean for that brief: write the assumed BT.709 / limited tags, so a player reads the
   output as Clearwater read the source; CHARC decides whether that is a reading of D55 or a
   change needing the owner.
