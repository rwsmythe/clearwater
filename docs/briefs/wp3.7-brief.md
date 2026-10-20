# WP3.7 — Video probe and input validation (dispatch brief, DRAFT)

**Status:** DRAFT 2026-10-20 by the orchestrator (generation 4) at CHARC's commission
(`a05f065e53e696d7`), for CHARC approval. Not dispatched before approval; dispatches after CP4
(spec v0.5.4 approval). Owner decisions: none inside the package.
- Spec **v0.5.3**; v0.5.4 items cited as "proposed (v0.5.4, CP4)". Architecture DRAFT 0.1
  section 3 IF-5 and section 5 "Probe (WP3.7)"; AD-16, AD-19, AD-20, AD-22. Frame
  `docs/briefs/wp2.4-phase3-frame.md`. WP1.5 report `docs/reports/wp1.5-container-spike.md`
  section 3 (what the HERO13 writes).
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp3.7`, branch `wp3.7`, base = the main commit named at dispatch.

**Why.** Every video path starts with the probe: decode (WP3.9) and encode (WP3.10) both depend
on WP3.7 (plan Phase 3 table), and the GUI's messages for unsupported, damaged or untagged
inputs (G10) are built from its `Fault` list. Architecture section 5: "ffprobe JSON plus a GPMF
settings read; faults per IF-5; HLG/PQ refused; GP-Log warned (AD-16); sidecars excluded (D83);
VFR reported (D95)."

| Field | Content |
|---|---|
| ID and title | WP3.7 — Video probe and input validation; plan Phase 3 row WP3.7 (size M); module `clearwater.io.video` (plan 8.1, AD-19) |
| Goal | A function that probes one video file into an IF-5 `ProbeResult` with exact timing, colour tags (D54 defaults applied and flagged), tracks, edit list, rotation, VFR, GoPro settings and the IF-5 faults; and an input filter that excludes `.LRV`/`.THM` sidecars (D83). |
| Spec / decision clauses | 5.2 "MP4 container, H.265/HEVC or H.264"; "8-bit and 10-bit sources handled without truncating 10-bit data"; "Constant and variable frame rate accepted". 5.3 "any stream tagged with an HLG or PQ transfer characteristic is refused with a clear message"; "GP-Log: detection is best-effort". 5.4 truncated sources "processed up to the readable portion, with a clear warning (D86)"; "Files that cannot be read at all are refused with a clear message." 5.5 "`.LRV` and `.THM` sidecars are still excluded from input (D83)". D15; D54 "if missing or unexpected, assume BT.709, limited range, and warn"; D73 "'Unsupported HDR' = HLG or PQ transfer tag ... GP-Log detection best-effort"; D83 (amended 0.5.3); D86; D94 (edit list "preserved and verified": the probe reports it as written; AD-22's reading is proposed (v0.5.4, CP4) item 5 and belongs to WP3.10); D95 "Variable-frame-rate input processed with timing preserved"; D105 (rotation, start offset, audio sync are mandatory downstream). Feeds V4 (VFR sample, D115) and V6 ("HLG/PQ test files refused"; "untagged video triggers the BT.709/limited warning"; "damaged files handled per Section 5.4"). AD-16 GP-Log rule; AD-19 "sidecar exclusion (D83) lives in the probe"; AD-20 amendment "IF-5 `rotation` is counter-clockwise positive (FFmpeg display matrix)". Proposed (v0.5.4, CP4) item 8 marks GP-Log DECIDED (AD-16) and leaves "HDR video mode" PENDING a clip. |
| Depends on | WP2.2 merged (IF-5 frozen). **WP2.3 merged**: its video samples (group 3: 8-bit HEVC BT.709 full range, 10-bit `yuv420p10le`, HLG-tagged, PQ-tagged, untagged, truncated, VFR, rotated) and dummy files (group 4: `GX010001.MP4`, `GX020001.MP4`, `GL010001.LRV`, `GX010001.THM`, lower-case variants), by their manifest ids, with the manifest's measured facts as the expected values. |
| Files owned | `src/clearwater/io/__init__.py` (NEW, docstring only: WP3.6 and WP3.9/3.10 add siblings); `src/clearwater/io/video/__init__.py` (NEW); `src/clearwater/io/video/probe.py` (ffprobe run and mapping); `src/clearwater/io/video/boxes.py` (a stdlib ISOBMFF reader for `elst` and `moov/udta/GPMF`); `src/clearwater/io/video/gopro.py` (the three-key GPMF settings decoder); `src/clearwater/io/video/inputs.py` (sidecar filter); `tests/test_io_video_probe*.py` (NEW); `docs/reports/wp3.7-video-probe.md`; `docs/proofs/wp3.7-ledger.md`. NOT owned: `src/clearwater/interfaces/`, `pyproject.toml` (no dependency), `tools/` (`tools/container_spike/` is reference reading only, never imported by `src/`), `tests/conftest.py`, the WP2.3 files. |
| Interfaces provided | `clearwater.io.video.probe(path: Path) -> ProbeResult` (IF-5 `ProbeResult` exactly as frozen, with `VideoStreamInfo`, `AudioStreamInfo`, `DataStreamInfo`, `EditEntry`, `Fault`, `GoProInfo`); an exception for a file that cannot be read at all (5.4), defined in `io.video` (not in `interfaces/`); the sidecar filter of task 6. WP3.9's `VideoSource.probe` delegates to `probe`; WP3.7 does not implement `VideoSource.frames`. |
| Interfaces consumed | IF-1 `ColorDescription` (vocabulary: primaries `bt709`/`display-p3`/`unknown`, transfer `bt709`/`srgb`/`unknown`, matrix `bt709`/`bt601`/`identity`/`unknown`, range `full`/`limited`, `assumed`); IF-5 `FaultKind` (`truncated`, `unreadable_tail`, `missing_tags`, `hlg`, `pq`, `gp_log`, `sidecar`) and severities (`refuse`, `warn`, `exclude`). `ffprobe` 9.0.2 (gyan build) on PATH as a subprocess. |
| Wave-2 consumers | None of wave 2 depends on WP3.7 to build; WP3.16 (shell, wave 2) shows G10 messages from `ProbeResult.faults`. Wave 3: WP3.9, WP3.10 (plan "Depends on WP3.5, WP3.7"), WP3.11 (analysis, keyed by pts and `time_base`). Later: WP3.14, WP4.2. Stub until this merges: `stubs.StubVideoSource(frames, probe_result)`, whose `probe` returns the hand-built `ProbeResult` given at construction, whatever the path. |
| Hardware flags | None timed. `footage` on the optional real-clip test (task 8): read-only, through `tools/local_config.find_footage_file`, skipped when absent. No `gpu`. |
| Out of scope | Decoding frames (WP3.9) and any full-file decode inside the probe; encode, mux, the AD-22 edit-list reading (WP3.10); colour conversion (WP3.5; DR-20 item 1 assigns D54's conversion to WP3.5, and `tools/lookcheck` is NOT a D54 reference); chapter grouping (deferred to v2, v0.5.3 5.5; WP3.8 removed); GoPro "HDR video" mode (AD-16 PENDING a clip; `HDRV` is not read); photos. **Never read** the `gpmd` track's payload, nor any ACCL, GYRO, GRAV, CORI, IORI or GPS key, anywhere (owner ruling: GoPro IMU and GPS out of scope); nothing from a `gpmd` track or a `udta` atom is committed, logged or written to a report. Camera serial numbers and identifier atoms are not read. |
| Done | Plan 4.5; frame section 2 rules 1-11 apply; ruff check, ruff format --check, mypy strict, full pytest green; every WP2.3 video sample probes to its manifest facts; Reviewer A converged. |

## Task ladder

1. **Round 0 yield: the mapping tables.** Before product code, write in the ledger: (a) ffprobe
   colour values to the IF-1 vocabulary, with what counts as "unexpected" (D54); (b) each fault
   kind's detection rule and severity; (c) the exact ffprobe command lines; (d) which GPMF keys
   are decoded. Base (a) and (b) on the WP2.3 manifest facts and WP1.5 section 3. Answers to the
   open questions below go in. YIELD for the dispatcher.
2. **ffprobe run.** One or a few subprocess calls with JSON output (`-show_format
   -show_streams` and the packet entries needed for timing). Locate `ffprobe` on PATH; absent →
   a clear error. Every time is an exact `Fraction` from integer ticks and the stream time base,
   never from ffprobe's decimal strings (`duration_s`, `start_offset_s`, `AudioStreamInfo.start_s`).
3. **Stream facts.** `VideoStreamInfo`: codec, coded size, bit depth from `pix_fmt` (no 10-bit
   truncation, 5.2), `chroma_siting` from `chroma_location` (`unknown` when absent), colour per
   table (a) with `assumed=True` when any D54 default was applied, `frame_rate` (avg) and
   `time_base` as Fractions, `nb_frames` or None, `rotation` from the display-matrix side data
   normalised to 0/90/180/270 counter-clockwise positive (AD-20; `tools/inventory.py` reports
   clockwise), `vfr`. Audio and data streams (`gpmd`, `tmcd` by codec tag; metadata only).
4. **VFR (D95).** From the video packets' pts in presentation order: CFR when every step is the
   same integer number of ticks; VFR otherwise. State the rule for the last frame and for
   reordered (B-frame) pts in the report.
5. **Edit list and GPMF settings (`boxes.py`, `gopro.py`).** ffprobe JSON carries no `elst`.
   Read `moov/trak(video)/edts/elst` (versions 0 and 1) into `EditEntry` (segment duration in
   the movie time scale, media time in the media time scale, `media_time = -1` → None, rate as
   a Fraction). Read `moov/udta/GPMF` (WP1.5 section 3: the camera's global settings atom,
   where WP1.5 read `FMWR`, `PRTN`, `PTCL`) and decode ONLY `FMWR` → `firmware`, `PRTN` →
   `protune`, `PTCL` → `color_profile`; skip every other item by its length without decoding
   it. Strict KLV per DR-30 item 2: nesting, alignment padding and sizes checked; a malformed
   atom gives `gopro=None` with a note, never a crash. A non-GoPro file gives `gopro=None`.
6. **Faults.** `hlg` (`arib-std-b67`) and `pq` (`smpte2084`) severity `refuse`; `missing_tags`
   `warn` (D54); `gp_log` `warn` per AD-16 ("`PTCL` ... a value other than
   `NATURAL`/`FLAT`/`VIBRANT` is treated as log" and "the absence of a transfer tag on a
   Protune clip"; nothing is converted); `truncated` / `unreadable_tail` `warn` (D86) per the
   round 0 rule; `sidecar` `exclude` (D83). Each message user-readable (G10). An unreadable
   file raises the task-2 exception with a clear message (5.4).
7. **Sidecar filter (D83, AD-19).** A function that takes candidate input paths and returns the
   inputs and the excluded sidecars with their `Fault`; extension match case-insensitive
   (`.LRV`, `.THM`), never by opening the file.
8. **Tests.**
   - Every WP2.3 video sample by manifest id: each `ProbeResult` field the manifest records
     (codec, pix_fmt, bit depth, tags, rotation, frame count, pts hash, VFR), the expected
     fault kinds and severities, and no unexpected fault on the clean samples.
   - The D54 cases: untagged → BT.709 limited, `assumed=True`, one `missing_tags` warning.
   - Edit list and GPMF on synthetic boxes the test builds (identity edit, empty edit,
     version 1, malformed atom; a GPMF atom holding the three keys plus an unrelated key that
     must be skipped undecoded).
   - Sidecar filter on the group-4 dummies, upper and lower case.
   - `footage`-marked: GX011627 (WP1.5 section 3: 681 frames, 30000/1001 CFR, BT.709 full,
     rotation 0, one identity edit, `PRTN` Y, `PTCL` NATURAL, firmware H24.01.02.10.00, no
     fault). Read-only.
   - A static test that no module under `clearwater.io.video` names a GPS or IMU key or opens
     the `gpmd` stream's data, and that `src/` does not import `tools`.
   - Dependency rule (plan 8.1, frame rule 5): importing `clearwater.io.video` loads nothing
     from `clearwater.gui`, `.jobs`, `.methods`, nor `PySide6` or `cupy`.

## Declared operating envelope

Windows 11; ffprobe 9.0.2 (gyan); MP4 files from the GoPro HERO13 (WP1.5 section 3) and the
WP2.3 samples; one video stream per file. Out of envelope: other ffprobe builds and versions,
multi-video-stream files, fragmented MP4, files on network shares, hostile files crafted to
break the box reader (single owner; a malformed atom must still not crash or hang).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.7\rN\`; ledger
  `docs/proofs/wp3.7-ledger.md`. Copy the runner and prompt shape from
  `C:\Users\rwsmy\clearwater-review-evidence\wp2.2\r3\run_review.sh` and `review-prompt.md`;
  exclude `docs/proofs` with `--glob '!docs/proofs/**'`. Five-round gate.
- **WHAT TO EXAMINE:**
  - each field measured against the WP2.3 manifest, not against the command line;
  - exact Fractions everywhere (no float, no decimal-string parse);
  - the D54 mapping and what counts as "unexpected";
  - rotation sign and normalisation (AD-20);
  - VFR detection on CFR, VFR and B-frame samples;
  - truncation detection without false positives on intact samples;
  - the box reader on malformed and truncated boxes (bounds, no infinite loop);
  - the GPMF decoder reads three keys only; no IMU/GPS key, no `gpmd` payload;
  - sidecar matching; messages fit G10.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4): the sample table (manifest id, faults, key facts, pass), the mapping tables'
  final form, the gates, the Reviewer A rounds and verdict, open items.
- **STOP for:** a `ProbeResult` field you cannot fill as frozen (AD-20); a sample whose
  measured facts disagree with its manifest; any need to decode frames in the probe; any need
  to read a `gpmd` payload or a key outside the three; a dependency; OS-specific code.
- **Working rules:** `uv sync`. Commit by pathspec, `feat(wp3.7): ...`, with a
  `Co-Authored-By:` footer naming your model. Never a bare `cd`. Never post to a mailbox. The
  full pytest (8-15 min, 892+ tests) runs in the background with output to a file under
  `work/`. Gates: ruff check, ruff format --check, mypy strict, full pytest; no harness gate
  (you touch none of its paths). Report `docs/reports/wp3.7-video-probe.md` (claims, evidence
  paths, limits). Yield at every round boundary; the dispatcher reads your depth (~250K
  evaluation, ~400K stop).

## Open questions for CHARC

1. **Where "GPMF settings" are read.** AD-16 says "the GoPro settings in the GPMF track";
   WP1.5 section 3 read `FMWR`/`PRTN`/`PTCL` from the `moov/udta` `GPMF` atom (spike.py
   `gpmf_settings(udta_atom(chapter, "GPMF"))`), and the spec defines no keys. Recommended: the
   `udta` atom only, the three keys `GoProInfo` carries, never the `gpmd` track (which also
   holds the IMU and GPS the owner ruled out); AD-16's wording corrected to "the GPMF settings
   atom".
2. **Containers and codecs outside 5.2.** 5.2 says "MP4 container, H.265/HEVC or H.264"; no IF-5
   fault kind covers another container or codec (AD-22 mentions an iPhone clip, usually
   `.MOV`). Recommended: a QuickTime `.MOV` with HEVC/H.264 is accepted (ffprobe reads both as
   the same family); any other codec or container is refused through the task-2 exception, not
   a new fault kind.
3. **D54 "unexpected" and partial tags.** Recommended: each missing or unrecognised field
   takes its D54 value (BT.709, limited) individually, `assumed=True` if any did, one
   `missing_tags` warning naming them; an untagged range with a `yuvj` pixel format still
   assumes limited (DR-20 item 1 calls full-range reading of untagged `yuvj420p` the defect).
   Primaries `bt2020` with an SDR transfer: unexpected (assumed BT.709, warned).
4. **`truncated` versus `unreadable_tail`, without a full decode.** IF-5 names both; neither
   the spec nor the architecture defines them, and a full decode in the probe would cost
   minutes on a long 4K clip. Recommended: `truncated` = the container's sample table points
   past the end of the file; `unreadable_tail` = packets present but ffprobe reports read or
   decode errors near the end (a bounded check on the last GOP, `-read_intervals`); a clean
   end gives neither. The cell proves both on the WP2.3 truncated sample and all intact ones.
5. **AD-16's two GP-Log signals.** Recommended: either signal raises `gp_log` (warn); the
   "absence of a transfer tag on a Protune clip" case also raises `missing_tags`.
6. **Colour of an HLG/PQ result.** `ColorDescription.transfer` excludes HLG/PQ ("refused at
   probe"). Recommended: such a result carries `transfer="unknown"`, `assumed=False`, the
   `refuse` fault, and is never decoded.
7. **The sidecar fault's carrier.** A `.THM` is a JPEG; a `ProbeResult` needs a video stream.
   Recommended: exclusion happens in the task-7 filter before probing, which returns the
   `sidecar` `Fault` per path; `probe` on a sidecar path refuses it without running ffprobe.
8. **The FFmpeg locator.** WP3.9 and WP3.10 also need `ffmpeg`/`ffprobe`. Recommended: WP3.7
   owns one small locator in `clearwater.io.video` (PATH lookup, clear error), and the later
   briefs consume it.
