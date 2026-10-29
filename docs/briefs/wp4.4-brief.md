# WP4.4 -- .MOV input (dispatch brief, DRAFT)

**Status:** DRAFT 2026-10-29 by a drafting helper for the orchestrator, from CHARC's commission
`4096c6d3b96cee21` (saved at `C:\Users\rwsmy\clearwater-review-evidence\wp4.4\commission-4096c6d3.md`;
its WP4.4 paragraph, carried verbatim below, governs this brief). CHARC rules this draft. Spec
v0.5.7 (no further spec change). Anchors read at main `922aaa5`; RE-LOCATE every line number at
round 0 on the dispatch base (WP4.3a edits `tools/headless_export.py` and `io/video/`).

| Field | Content |
|---|---|
| ID and title | WP4.4 -- `.mov` sources accepted, named `<stem>_corrected.mp4`, exported unchanged through probe/decode/V4/mux |
| Lane | **CODEX**: `implementer-codex-sol-high` (gpt-6.1-sol / high), `codex exec` turns driven by `scripts/codex_cell.py`. Pace at dispatch: Codex @@, Claude @@. The cell ends every turn with a FILES CHANGED block; the orchestrator commits and runs every heavy command and every footage run the cell yields. |
| Tier and nets | Tier **STRONG** (product code). Reviewer A = the Claude pass, `scripts/codex_cell.py review` (`claude -p --model opus --effort high`, read-only), between turns, to convergence, five-round gate (`docs/review-gate-clearwater.md` Part 1). Reviewer B = the Claude pass at the orchestrator's seat (Part 2). Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.4\rN\`, `reviewB\`. |
| Base, worktree | Base = main at dispatch, **only AFTER WP4.3a's accept on main** (it owns `tools/headless_export.py` and `io/video/` until then). Worktree `.worktrees/wp4.4`, branch `wp4.4`. Does not displace WP4.3 / WP4.3a (commission). |
| Gate | The standard two-leg gate at the orchestrator's seat (`docs/review-gate-clearwater.md:171-172`): `-n 4 -m "not gpu and not footage and not gui and not slow and not fullclip"`, then `-m "(gpu or footage or gui or slow) and not fullclip"`. No fullclip leg. Every new test is parallel-leg except the ONE `footage` test (serial leg; reason beside its marker: reads owner footage). |
| Goal | An iPhone `.MOV` opens in the GUI and the runner as a video, and exports to `<stem>_corrected.mp4` with V4's MANDATORY and REQUIRED items SAME, with no change to `io/video/`. |
| Files owned | `src/clearwater/gui/sources.py` (`VIDEO_SUFFIXES` and its docstring only); `src/clearwater/jobs/naming.py` (the video extension rule in `_base_plan` and the docstrings that state it); `tools/headless_export.py` (its `VIDEO_SUFFIXES` and docstring only); `tests/test_jobs_naming.py` (new tests; `:64-66` per Q1); `tests/test_gui_open.py` (`:93`, `:109` per Q1); NEW `tests/test_wp44_mov_input.py`; `docs/reports/wp4.4-mov-input.md`; `docs/proofs/wp4.4-ledger.md`. |
| NOT owned | `src/clearwater/io/video/` (all of it; Q2), `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN), `src/clearwater/jobs/export.py`, `gui/` beyond `sources.py`, `app/`, `tools/video_fidelity.py`, `tools/container_spike/`, `tools/local_config.py`, `tests/conftest.py`, `tests/fixtures/`, every other existing test, `pyproject.toml`, `uv.lock`, the spec, the register. |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict; Reviewer A converged; Reviewer B returned; the two-leg gate green; report and ledger written; the 5.2 and 8.3 lines quoted in the report. No harness gate. |

## The commission (CHARC `4096c6d3b96cee21`, its WP4.4 paragraph and scope, verbatim)

**COMMISSION: WP4.4 ".MOV input" (small, well-specified; Codex-eligible under the lane rule, or sonnet-high; nets = the other model).** Brief helper drafts from this and the inventory's brand column; I rule the draft. Scope, all RED-first:
1. `src/clearwater/gui/sources.py:25` `VIDEO_SUFFIXES` gains `.mov` (case-insensitive as today); the docstring cites 5.2 (0.5.7).
2. `src/clearwater/jobs/naming.py`: a video source whose suffix is `.mov` (any case) plans `<stem>_corrected.mp4` (D25 output container is MP4); `.mp4` sources keep their suffix as today; the collision and `.clearwater-partial` rules unchanged; every existing naming test unchanged.
3. `tools/headless_export.py`: the runner accepts `.mov` sources wherever it accepts `.mp4` (its own suffix rule, if any; the brief helper finds it); refusal texts unchanged.
4. Probe/verify: a `qt`-brand QuickTime fixture built under `tmp_path` by FFmpeg (`-f mov`, HEVC or H.264, a few frames, PCM audio like the phone) proves `probe`, decode, the V4 comparison and the output mux pass unchanged through the existing path (expected: no code change in `io/video/`; if one IS needed it is a STOP to me, `io/video/` stays WP4.3a's until its accept).
5. One `footage`-marked test on `Phone/IMG_6702.MOV` (0.5 s, 15 frames, HEVC 1920x1440, PCM, two Core Media data tracks): end-to-end export via the runner, V4 within the AD-11 bound, output name `IMG_6702_corrected.mp4`; skips when the footage is absent.
6. Report + ledger; the spec 5.2/8.3 lines quoted. NOT owned: `io/video/` (WP4.3a), `gui/` beyond `sources.py`, `interfaces/`.
Gate: standard two-leg at your seat.

## Spec and decision clauses (v0.5.7, verbatim)

- 5.2 (`docs/underwater-correction-spec.md:213`): "MP4 or QuickTime container (`.mp4`, `.mov`; 0.5.7), H.265/HEVC or H.264. Both are ISO base media files read by the same FFmpeg demuxer; the iPhone records QuickTime (`qt` brand), the GoPro MP4."
- 8.3 (`:384`): "**Naming:** source filename plus suffix, default `_corrected`, editable in settings. Photos change extension to `.png`. Examples: `GX010123.MP4` → `GX010123_corrected.MP4`; a `.mov` source is written as MP4 and takes the `.mp4` extension (`IMG_1234.MOV` → `IMG_1234_corrected.mp4`; D25, 0.5.7); `IMG_1234.HEIC` → `IMG_1234_corrected.png`."
- D25 (`:63`): "*(amended by D76)* Video output: MP4, HEVC only; 10-bit when source is 10-bit, optionally 10-bit for 8-bit sources"
- D105 (`:143`): "Video fidelity priorities: per-frame timing, start offset, audio sync and display orientation are mandatory; other video metadata is best-effort"
- V4 (`:482-485`), mandatory part: "output matches source frame count, per-frame timestamps, start offset, resolution, bit depth (or the selected 10-bit option), chroma format, audio and display orientation; color tags match the source"

## The code today (read at `922aaa5`)

- **GUI suffix set:** `sources.py:25` `VIDEO_SUFFIXES = frozenset({".mp4"})`, docstring `:26`; `route` lower-cases the suffix (`:57-61`); `file_filter` builds `*.mp4` from the set (`:39`). Callers: `gui/shell.py:421`, `gui/batch_panel.py:274`.
- **Runner suffix set:** its own copy, `tools/headless_export.py:140-141` (`VIDEO_SUFFIXES: Final = frozenset({".mp4"})`, "equal to `clearwater.gui.sources.VIDEO_SUFFIXES` (a `gui` test pins it)"); `route` `:544-561`; the refusal text `:561` stays. The pin: `tests/test_headless_export.py:114-122` (`gui`-marked), which holds unchanged once both sets gain `.mov`.
- **Naming:** `naming.py:296` `extension = PHOTO_EXTENSION if kind is MediaKind.PHOTO else source.suffix` (a video keeps its suffix exactly). The DR-80 composed-name check `:297-305` runs on `base + extension`; `TEMP_MARKER` `:28`; `temporary_path` `:119-130` takes the FINAL path's suffix, so a `.mov` source's temporary ends `.mp4`. Docstrings stating the old rule: `:317-318`, `:329`, `:386`.
- **Probe/decode/mux:** nothing keys on the `.mp4` suffix or an `isom`/`mp42` brand. `probe.py:565-569` accepts a `format_name` holding `mov` or `mp4` (FFmpeg's one demuxer names both `mov,mp4,m4a,3gp,3g2,mj2`); `:64` HEVC/H.264; `:65` accepts `yuvj` formats. The sink always writes `-f mp4` (`encode.py:436-437`), copies audio and every non-`tmcd` data track (`:378-383`, `-c:a copy -c:d copy` `:422-425`). `verify.py:862-897` reports an uncarried data track as best-effort (`not_carried`).
- **The known risk:** WP3.10's report, Limits (`docs/reports/wp3.10-video-encode.md:385-387`): "data tracks other than the HERO13 set (for example an iPhone `mebx` track) and audio codecs MP4 cannot hold are passed to the muxer, which fails (`encoder_failed`, with FFmpeg's message)." IMG_6702 carries two Core Media data tracks and PCM audio. Q2.
- **V4 instrument:** `tools/video_fidelity.py:1251` `fidelity_record`; the house assertion is `tests/test_wp42_video_path.py:373-385` (`summary.mandatory_and_required_all_same`, the roster item `:148` SAME). Its container item is a requirement on the OUTPUT ("output container (8.2 requires MP4)", `tools/container_spike/compare.py:1284`; `container_kind` `:1023` names `qt  ` QuickTime); "ftyp brands" is BEST_EFFORT (`:1403-1410`). Location-like tags are withheld before comparison (`video_fidelity.py:48-50`, `:151`).
- **Recipes:** synthetic clips `tests/test_io_video_encode.py:110-153` (`_ffmpeg`, `Clips.make`: lavfi `testsrc2` + `sine`, `-bf 0` unless B-frames); `tests/test_inventory.py:61-64`. Footage lookup: `tools/local_config.py:152` `find_footage_file(stem)` (`.mov` already in `VIDEO_EXTENSIONS`, `:19`); skip-only-when-absent helper `tests/test_io_video_encode.py:1477-1488`; the conftest skips every `footage` test without a configured folder (`tests/conftest.py:338-346`).

## Locks

No frozen interface; no `io/video/` edit (Q2 is a STOP); no new dependency; no OS-specific code.
The 8.3 rule only: `.mov` in any case maps to lower-case `.mp4`; every other video suffix is kept
exactly (`.MP4` stays `.MP4`). Collision numbering, the source guard, the temporary marker and the
DR-80 name check unchanged and applied to the mapped name. Refusal texts unchanged. Nothing
written under the footage folder: fixtures and outputs under `tmp_path`; round-0 output under
`work/wp4.4/`. PRIVACY: no location, device serial or EXIF value in any assertion, ledger or
report; the footage test asserts format facts and the output name only, and never prints the
fidelity record or the source's tags.

## Task ladder

1. **Read and map** the anchors above on the dispatch base; re-locate every line.
2. **Round 0 (no product code), in the ledger, then YIELD:** (a) the re-located anchors; (b) the
   RED list, each test with the base it fails on; (c) a RUN REQUEST for the orchestrator on the
   UNCHANGED base (the runner refuses `.mov` there, so the sink is driven directly):
   `vf.encode_file(<IMG_6702>, work/wp4.4/r0/IMG_6702-r0.mp4, encoder="libx265", bit_depth=8)`
   (`tools/video_fidelity.py:350`, the product sink, no suffix check) and `vf.fidelity_record`
   on it, reporting the exit, any failure text, the stream types and codec tags, and the NAMES of
   any DIFFERENT items only (no tag values); (d) the depth reading. A mux failure on the `mebx`
   tracks or the PCM audio, or a MANDATORY or REQUIRED item DIFFERENT, is a STOP to CHARC
   through the orchestrator with that evidence (Q2, Q3).
3. **RED, the suffix sets, GREEN.** In `tests/test_wp44_mov_input.py` (no `gui` import): runner
   `route` gives `"video"` for `a.mov`, `a.MOV`, `a.Mov`; the refusal text for `notes.txt` is
   unchanged. Q1's two `test_gui_open.py` edits. Then `.mov` joins both sets, docstrings citing
   5.2 (0.5.7). CHECK: `tests/test_headless_export.py:114-122` passes unchanged.
4. **RED, the naming rule, GREEN.** New tests in `tests/test_jobs_naming.py`, through BOTH
   `final_output_path` and `plan_output`: `IMG_6702.MOV` -> `IMG_6702_corrected.mp4`; `x.mov`,
   `x.Mov` likewise; `--suffix`-edited (`_fixed`) and empty-suffix forms; `IMG_1.MOV` and
   `IMG_1.mp4` in one folder plan `IMG_1_corrected.mp4` and `IMG_1_corrected_2.mp4` (D35); an
   existing `IMG_1_corrected.mp4` or its `.clearwater-partial-<token>.mp4` temporary numbers a
   `.MOV` source to `_2`; `temporary_path` of the mapped final ends `.mp4`; `x.mov:s` still
   raises `OutputNameError`. Q1's `:64-66` edit. Then the rule at `naming.py:296` and the three
   docstrings. CHECK: every other existing test in the file unchanged and green, the WP2.3
   control `:508-528` included.
5. **The qt fixture (parallel leg).** A session-or-test fixture under `tmp_path` modelled on
   `Clips.make`: `testsrc2` about 192x144, 30 fps, 0.5 s; `-c:v libx265` with B-frames
   (`-x265-params bframes=2:log-level=error`); `sine` 48 kHz `-c:a pcm_s16le`; `-f mov`; named
   `clip.MOV`, with a display rotation of 180 (`-display_rotation 180` before `-i`, or the
   `-metadata:s:v rotate` form FFmpeg 9 honours; IMG_6702 carries -180 and display orientation is
   a MANDATORY V4 item). Assert the fixture IS what it claims: ftyp major brand `qt  ` (compare's
   `Movie`), `has_b_frames > 0` and the display-matrix rotation present. Then: `probe` (container holds `mov`), a full decode (frame count = the
   probe's), one export through `he.main([... "--out", out, "--cache-dir", cache, "--force-cpu"])`
   exiting 0, the output named `clip_corrected.mp4` only, and `fidelity_record` with
   `mandatory_and_required_all_same` true and the roster SAME (the `_assert_v4` form).
6. **The footage test (serial leg)** in the same file: `@pytest.mark.footage` with its reason;
   `find_footage_file("IMG_6702")` through the skip-only-when-absent pattern; the runner as in
   step 5 with `--record`; assert exit 0, the one output `IMG_6702_corrected.mp4`, the record's
   item `done`, V4 as in step 5, `video frame count` 15. RUN REQUEST it; never run it at the cell.
7. **Report and ledger.** `docs/reports/wp4.4-mov-input.md`: the 5.2 and 8.3 lines quoted; the
   rule and where it sits; RED/GREEN node ids; the round-0 and footage evidence (format facts
   only); the best-effort items `not_carried` lists for IMG_6702 (names only); a "for CHARC" line
   on DR-15's iPhone leg (Q4). Ledger: rounds, depth readings, every heavy run (command, counts,
   EXIT).
8. **Lint and types**, Reviewer A to convergence (yield after each round once adjudicated, before
   remediating), then the orchestrator's Reviewer B and the ONE two-leg gate.

Light runs (the cell's): `uv run pytest -q tests/test_wp44_mov_input.py tests/test_jobs_naming.py
tests/test_headless_export.py -m "not gpu and not footage and not gui and not slow"`. Depth read
every turn (~250K evaluation point, ~400K STOP).

## Hardware flags

No timing or memory figure; not exclusive. The fixture export is CPU (`--force-cpu`, libx265).
The footage test reads 0.5 s of owner footage read-only, CPU only; serial leg.

## STOP for

Any `io/video/` change (Q2); any existing test change beyond Q1's edits; any edit outside
the owned list; a change to any name a `.mp4` or photo source plans today; a frozen interface; a
dependency; any write under the footage folder; a choice this brief leaves open.

## Return report

Commits by the orchestrator: `feat(wp4.4): ...`, `test(wp4.4): ...`, `docs(wp4.4): ...`, by
pathspec, `-c core.autocrlf=false`, LF blobs, a `Co-Authored-By:` footer. The final turn names:
the per-change list, the light runs read off the final state, Reviewer A's rounds and verdict,
each lock honoured on disk, the removed and added node ids (Q1), and any deviation or STOP.

## Questions for CHARC (recommended answer first)

- **Q1. Three existing tests pin the pre-0.5.7 behaviour; the commission says "every existing
  naming test unchanged".** `tests/test_jobs_naming.py:64-66` asserts `clip.mov` ->
  `clip_corrected.mov` (the 8.3 rule now says `.mp4`); `tests/test_gui_open.py:109` routes
  `a.mov` to `"refusal"`; `:93` lists the filter's suffixes (additive). Recommended: OWNED for
  exactly these edits: `:64-66` becomes `clip.mov` -> `clip_corrected.mp4` and a new test keeps
  the case-preservation intent with `clip.Mp4` -> `clip_corrected.Mp4`; `:109` becomes
  `("a.mov", "video")` with an `a.MOV` row; `:93` gains `"*.mov"`. The removed node id
  `test_routing_by_extension[a.mov-refusal]` is explained in the gate's collection diff.
  Alternative: none that meets 8.3 (the old assertion contradicts it).
- **Q2. The `mebx` data tracks at the mux -- SETTLED ON EVIDENCE at the orchestrator's seat
  (2026-10-29, FFmpeg 9.0.2, output under `work/wp4.4-seat/`, footage read-only).** IMG_6702's
  streams: `hevc`/`hvc1` video, `pcm_s16le`/`lpcm` audio, two data tracks `mebx` ("Core Media
  Metadata"). `ffmpeg -i IMG_6702.MOV -map 0 -c copy -f mp4 out.mp4` FAILS: "Could not find tag
  for codec none in stream #2, codec not currently supported in container" / "Could not write
  header". `-map 0:v -map 0:a -c copy -f mp4` SUCCEEDS with HEVC + `pcm_s16le` in the MP4, so PCM
  is NOT a problem; the `mebx` tracks are. The sink as it stands therefore fails on every phone
  MOV, and round 0 (c) will show it. Recommended: CHARC grants `io/video/encode.py`'s data-track map only (`:381-383`,
  free once WP4.3a is accepted, which this dispatch already waits for): a non-`tmcd` data track
  is mapped only when its tag is one the MP4 muxer carries (the HERO set the sink is proved on),
  the dropped track reported by the existing `not_carried` text ("data track mebx"), best-effort
  per D105, named in the report as a known limitation; one RED test with a dropped tag (the qt
  fixture of step 5 then carries one `mebx`-like data track if FFmpeg can author one; if it
  cannot, the footage test is the witness and the report says so). Dropping `mebx` also keeps
  Apple's Core Media metadata out of the output, which is the safer default under the owner's
  location rule. Alternative: WP4.4 lands steps 1-5, the footage test `xfail(strict=True)` naming
  a new DR, and a follow-on package owns the fix.
- **Q5. Two phone clips are Dolby Vision** (inventory 2026-10-29, colour group C2: DV RPU present,
  base layer HEVC). Recommended: OUT of this package; WP4.4's tests use IMG_6702 (no DV) and the
  qt fixture; the report names the DV clips as untested here and the DV RPU as best-effort under
  D105 (not carried by an HEVC re-encode). Alternative: a DV clip as a second footage test (its
  bit depth, transfer and colour tags would then be V4 items on a 10-bit HLG-class source).
- **Q3. "V4 within the AD-11 bound."** AD-11 (`docs/decisions.md:20`) sets N10, V9 and V8
  bounds; it sets none for V4, whose MANDATORY items are SAME by D105. Recommended: the footage
  and fixture tests assert V4 as the house form does (MANDATORY and REQUIRED SAME, roster SAME,
  `tests/test_wp42_video_path.py:373-385`); no pixel bound (V9 needs the pre-encode seam, not
  reachable through the runner). Alternative: add V9 at neutral parameters on the qt fixture
  through the composition (`test_wp42_video_path.py:464-482` form; max 2/255, mean 0.2/255).
- **Q4. DR-15's iPhone leg** (`docs/debt-register.md:24`, OPEN; WP3.10 left it waiting for an
  iPhone clip). IMG_6702's video edit list has media_time 0 with negative ctts. Recommended: the
  report records the edit-list rows of the footage V4 record as evidence; CHARC rules any DR-15
  closure at the accept, not the cell. Alternative: leave DR-15 untouched by this package.
