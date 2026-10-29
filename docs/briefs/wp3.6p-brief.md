# WP3.6P -- Real-photo verification (dispatch brief, DRAFT)

**Status:** DRAFT 2026-10-29, written by a drafting helper for the orchestrator (generation 24)
from CHARC's commission (quoted verbatim below); CHARC rules it. Spec v0.5.7; no spec clause
changes. Anchors read at main `1beadd0`; RE-LOCATE every line at round 0 on the dispatch base.
Owner decisions: none inside the package (the photo look check is owner-reserved and NOT
commissioned).

| Field | Content |
|---|---|
| ID and title | WP3.6P -- Real-photo verification on the owner's 73 phone photos: AD-24 on real Apple HEIC, V5 / D53 / V9 through the runner, the Result 2 photo memory leg; the pre-corrected Z/M group reported separately |
| Lane | sonnet-medium (WP3.6 Q11) or CODEX by pace (Codex 0.376 vs Claude 1.423 at 21:50Z); the orchestrator re-reads both at dispatch; recommended CODEX (`implementer-codex-sol-high`, `codex exec` turns driven by `scripts/codex_cell.py`; the cell ends every turn with a FILES CHANGED block; the orchestrator commits and runs every footage, `gpu` and heavy command the cell yields). Q1 on task fit. |
| Tier and nets | Recommended Tier **STRONG** (Q1). Nets are the OTHER model from the implementer: for the Codex lane, Reviewer A = the Claude pass, `scripts/codex_cell.py review` (`claude -p --model opus --effort high`, read-only), between turns, to convergence, five-round gate (`docs/review-gate-clearwater.md` Part 1); Reviewer B = the Claude pass at the orchestrator's seat (Part 2). Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp3.6p\rN\`, `reviewB\`. |
| Base and worktree | Base = main at dispatch, after the inventory QA (the report is on main at `e34c4a9`; the orchestrator confirms CHARC's QA at dispatch) and clear of WP4.3's windows (commission). Worktree `.worktrees/wp3.6p`, branch `wp3.6p`. On the Codex lane it queues behind WP4.4 and WP-DR87 (one Codex lane). No file overlap with WP-DR87 (`io/photo/exif.py`): this package owns no `src/` file. |
| Goal | A committed, re-runnable instrument and a report that state, per photo class and from the owner's own files: (1) whether AD-24 orients every real Apple HEIC exactly once, shown against an oracle independent of the product's AD-24 logic; (2) V5 (EXIF except D63, ICC present and matching, bit depth honoured) and V9 (neutral identity within AD-11) on the RUNNER's output, not only the I/O round trip; (3) D53 (source primaries kept, matching ICC); (4) the Result 2 photo half: peak RAM, peak graphics memory, the estimate against free device memory and the device chosen, on the largest owner photo; (5) every figure of the pre-corrected Z/M group in its own rows. |
| Files owned | NEW `tools/photo_verify.py` (Q2: subcommands `orientation`, `export`, `memory`); NEW `tests/test_photo_verify.py`; `docs/reports/wp3.6p-real-photos.md`; `docs/proofs/wp3.6p-ledger.md`. |
| NOT owned | All of `src/` (`src/clearwater/interfaces/` IF-1..IF-10 FROZEN; `io/photo/` included: a defect the run proves is a STOP to CHARC with the evidence, never a fix here); `tools/photo_check.py` and `tests/test_photo_check.py` (Q2); `tools/headless_export.py`; `tools/local_config.py`; `tools/prototype/`; `tools/spike_io/`; every other existing test; `tests/conftest.py`, `tests/fixtures/`; `pyproject.toml`, `uv.lock`; the spec; `docs/decisions.md`; the register; the inventory report. |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict (`tools` is in mypy's files); the new tests green; the seat runs of task 5 recorded in the ledger (command, counts, EXIT, free disk before and after); Reviewer A converged; Reviewer B returned; the standard two-leg gate at the orchestrator's seat (no fullclip leg); report and ledger written. No harness gate. |

## The commission (CHARC, verbatim)

- `docs/charc-state.md:223-226` (CHARC's commission to gen 22, OWNER INPUT 17:10Z entry): "(2)
  WP3.6P real-photo verification (sonnet-medium as approved at WP3.6 Q11, or Codex by pace; AD-24
  on real Apple HEIC, V5/D53/V9, Result 2 memory leg; pre-corrected class reported separately;
  after the inventory QA and clear of WP4.3's windows)" ... "Look-check on phone photos NOT
  commissioned (owner's visual review)."
- `docs/charc-state.md:35-36` (the queue): "WP3.6P brief (sonnet-medium or Codex; on the 73 phone
  photos; AD-24 on real Apple HEIC; pre-corrected Z/M group reported separately)".
- Origin: `docs/briefs/wp3.6-brief.md:277-284`, question 11: "Waiting for the owner's photos: the
  AD-24 layout of a real iPhone HEIC (grid primary, `ipma`, tag and `irot` together), MakerNote and
  GPS survival through Pillow's EXIF writer, Display P3 classification of Apple's profile, the
  largest photo for the Result 2 photo leg and V15, and the photo look check. Recommended: a named
  follow-on **WP3.6P "Real-photo verification"** (sonnet-medium, a mechanical run of
  `tools/photo_check.py` from task 8 on the owner's photos, plus any fix it proves), commissioned
  when photos arrive". Ruling `:219-220`: "**11:** WP3.6P "Real-photo verification" APPROVED as a
  queued sonnet-medium package, dispatched when the owner supplies photos."
- Owner input (`CLAUDE.md:29`): "the above-surface and possibly pre-corrected files are identified
  by the inventory refresh and WP3.6P, never assumed."
- WP4.1's owed leg (`docs/reports/wp4.1-photo-path.md:159-169`): "V5 and V9 on the owner's iPhone
  HEIC (AD-24 provisional until an owner photo is read)"; "The largest photo for N4/D110 (V15,
  WP5.2)."; "DR-42 (a) on real files (WP3.6P)."; the runner command `uv run python
  tools/headless_export.py <photo> [...] --out work/wp3.6p/out --bit-depth 16 --record
  work/wp3.6p/record.json` "and, for V9, the same with `--neutral`"; "No photo look check
  (owner-reserved)." Accept record `docs/proofs/wp4.1-accept.md:53`: "**OWED** (the report): the
  owner HEIC V5/V9 and AD-24 legs, the 48 MP photo (V15), DR-42 (a) on real files, the viewers
  (WP5.1)."

## Spec and decision clauses (v0.5.7, verbatim; non-ASCII characters transliterated: "<=" for the less-or-equal sign, "->" for the arrow)

- D24 (`docs/underwater-correction-spec.md:62`): "*(amended by D63)* EXIF metadata preserved,
  except fields made invalid by processing"
- D53 (`:91`): "Photos keep source primaries end to end (e.g., Display P3); matching ICC profile
  embedded in PNG output"
- D63 (`:101`): "Photo orientation: pixels rotated, Orientation tag reset; thumbnail dropped,
  dimensions updated, Software set, HEIC gain/depth maps dropped. HEIC rule (0.5.4, AD-24,
  provisional until an owner photo is read): the file's `irot`/`imir` transforms are applied by the
  reader; the EXIF Orientation tag is applied additionally only when no `irot` transform is present"
- D110 (`:148`): "Memory limits cover photos as well as video: the largest supported photo is
  tested, and graphics memory is measured"; D111 (`:149`): "Automatic CPU fallback when an image or
  frame is estimated not to fit in graphics memory; no tiled processing in v1"
- 8.1 (`:363-368`): "**Metadata:** all EXIF preserved except fields made invalid by processing
  (D63):" pixels rotated and Orientation normal; thumbnail removed; pixel dimensions updated;
  Software set to Clearwater; "HEIC auxiliary images (HDR gain map, depth map) are dropped."
- N4 (`:443-445`, three bullets): "peak RAM <= 16 GB, for video (including 5.3K 8:7) and for the
  largest supported photo;" / "graphics memory is measured and treated as a second limit;" / "if an
  image or frame is estimated not to fit in graphics memory, it is processed on CPU automatically;"
- V5 (`:486`): "EXIF preserved except D63 fields; orientation correct for rotated and portrait
  sources in multiple viewers; ICC profile present and matching; selected bit depth honored."
- V9 (`:490`): "with every stage set to its neutral value ... the output matches the input within a
  small color-difference tolerance for photos and video. This exercises the full decode -> process
  -> encode path, including color tags and ICC handling."
- V15 (`:496`): "peak RAM <= 16 GB on a 5.3K 8:7 clip and on the largest supported photo; peak
  graphics memory recorded; the CPU fallback engages when an image does not fit in graphics
  memory." (V15 itself is WP5.2's: plan `docs/clearwater-implementation-plan.md:362`.)
- G10 (`:410`): "Clear messages for unsupported, damaged, or untagged inputs (Sections 5.1, 5.3,
  5.4, 6.5), including ProRAW/DNG."
- Open item (`:567`, "Decided by the footage inventory"): "Photo resolution (24 MP or 48 MP) and the
  video recording modes in use."
- AD-24 (`docs/decisions.md:33`): "**HEIC orientation rule (D63), PROVISIONAL until an owner photo
  is read:** read through pillow-heif's Pillow opener (libheif applies `irot`/`imir`; the opener
  resets EXIF Orientation to 1); additionally read the raw EXIF Orientation with `open_heif`
  metadata and, when the file carries an Orientation tag other than 1 and NO `irot` transform,
  apply that Orientation to the pixels before resetting it, so a tag-only file is not left
  unrotated and an `irot` file is not rotated twice."
- AD-11 (`docs/decisions.md:20`): "V9 identity round trip (neutral parameters, pre-encode): max abs
  diff **<= 2/255**, mean <= 0.2/255", and (Clarified 2026-10-28, WP4.1 S8) "when the export's bit
  depth is BELOW the source's ... the V9 bound is measured against the source quantised to the
  export depth by the writer's own rounding rule".
- Result 2 (`docs/reports/wp1.6-gate-report.md:117-118`): "**Largest photo: PENDING** (D102: no
  photo in the inventory; the owner's photos are still to be supplied). Queued for the first
  photo, not dropped."; its row (`:203`): "Photo size limit (Result 2) | only if the largest photo
  exceeds 16 GB on CPU | Part B photo leg | PENDING photos; not expected". The leg's form
  (`docs/briefs/wp1.2b-brief.md:82-85`): "the `memory_estimate_bytes` figure, the measured peak,
  whether the estimate exceeded the card's free memory, and whether the CPU fallback engaged (if it
  did not, force it once with `--device cpu` and record the CPU peak RSS). Against 16 GB and 8188
  MiB."
- Debt rows naming this package: DR-42 (`docs/debt-register.md:51`), trigger "(a): WP3.6P real-photo
  checks, or an owner report of a wide-gamut PNG/TIFF without an ICC profile; ... (c): the next
  touch of `tiff.py` (WP3.6P)."; DR-43 (`:52`), trigger "WP3.14 (export) or the next touch of
  `io.photo` (WP3.6P), or an owner report of lost metadata." Also read DR-7 (`:16`, trigger "A
  non-Apple HEIC in the footage") and DR-6 (`:15`).

## The code today (read at `1beadd0`)

- **The instrument:** `tools/photo_check.py`. `collect` `:54-73` walks folders for `PHOTO_SUFFIXES`
  `:44`; `_heic_layout` `:76-107` records the primary item (`grid`, `irot`, `imir`, `clap`,
  `ispe`, auxiliary and thumbnail ids) and the raw EXIF tag; `_color_record` `:110-126` (primaries,
  transfer, `assumed`, ICC description, md5, validity); `round_trip` `:129-181` writes a 16-bit PNG
  with the PRODUCT WRITER (not the runner, no correction stage), re-reads it, and checks samples,
  ICC, Orientation 1, Software, dimensions, no thumbnail, and every other field by
  `exif.describe` (`D63_CHANGED` `:50`), plus `maker_note_kept` and `gps_kept` `:178-179`;
  `inspect` `:184-224` puts the absolute source `path` in every record (`:194`); outputs under
  `<working>/wp3.6/photo-check/<run>/` (`WORK_SUBDIR` `:47`, `run` `:255-300`); exit codes `:303-332`.
- **Its footage test:** `tests/test_photo_check.py:132-148`
  (`test_the_real_photo_leg_reads_and_round_trips_the_owners_photos`, `footage`, serial leg) walks
  the whole configured footage folder. It ALLOWS refusals (`:146`, `"unsupported"` or
  `"unreadable"`), so it does not prove that every photo reads. WP4.5 made it pass over all 73
  photos (`docs/reports/wp4.5-exif-bytes.md:195-207`: "1 passed in 268.01 s" on `3020648`; on the
  candidate within the impacted serial nodes). **Already shown, not redone here:** the I/O round
  trip's D63 field compare, MakerNote and GPS kept, on every readable owner photo, through the
  WP4.5 byte-level rewriter (which replaced the "Pillow's EXIF writer" of WP3.6 Q11).
- **Finding a photo:** `tools/local_config.find_footage_file` (`:152-158`) matches VIDEO files only
  (`VIDEO_EXTENSIONS` `:19` = `.mp4`, `.mov`, `.360`); it never returns a photo. Photos are reached
  through `photo_check.collect([config.footage_path])` or `config.footage_path / "Phone" / <name>`.
- **AD-24 in the product:** `src/clearwater/io/photo/reader.py:209-219` `heic_tag_to_apply`
  (`return tag if layout.irot is None else 1`), `_check_decoded_size` `:226`, `_read_heic` `:239`;
  the box reader `heif_boxes.read_layout` `:177`. The fixture-level witness:
  `tests/test_wp41_photo_path.py:324-339` (the four `heic-ad24-*` samples exported `--neutral`,
  upright within mean 6, every other pose apart by more than 10).
- **Colour:** `src/clearwater/io/photo/color.py:37-49` `describe_color`: an RGB ICC profile, a PNG
  `sRGB` chunk, a HEIC `nclx`; "otherwise the photo is untagged and read as BT.709 primaries with
  the sRGB curve, ``assumed=True``". EXIF ColorSpace is NOT read (no match for `ColorSpace`, `40961`
  or `0xa001` under `io/photo/`). `writer.built_in_profile` `:36-56` embeds a built-in profile only
  for a tagged, profile-less HEIC.
- **The runner:** `tools/headless_export.py` `--bit-depth` `:1199`, `--force-cpu` `:1201`,
  `--neutral` `:1221` (`parameters_for` `:670`), `--record` `:1226`. V9's house form:
  `tests/test_wp41_photo_path.py:344-356` `v9_difference` (quantised reference by the writer's
  rule, then the raw error, in 1/255).
- **Memory:** `src/clearwater/core/backend.py:1001` `select_backend` (GPU when the estimate is
  strictly below free device memory, else `"CPU: estimate ... exceeds free ..."`, `:1027-1043`);
  `core/memory.py:45` `memory_estimate_bytes`. The prototype instrument's samplers are
  `tools/prototype/bench.py:1004` `_memory_record` (psutil RSS, `peak_wset`) and `:1270`
  `_GpuSampler` (`nvidia-smi`); bench reads no HEIC (`IMAGE_SUFFIXES` `:165`). `psutil` is in the
  `dev` group (`pyproject.toml:40`).
- **The inventory** (`docs/reports/inventory-2026-10-29.md`): photos 73 = HEIF 62 + JPEG 11
  (`:89`, `:111`); all primary images 8-bit. HEIC rows `:208-216`: `irot` 180 / EXIF 3 (20), 0 / 1
  (9 + 7 + 7 = 23), 90 / 8 (3), 270 / 6 (11 + 5 = 16); "every pair agrees" and "no genuinely absent
  EXIF orientations" (`:392-397`); all 62 carry a Display P3 ICC and no `nclx` (`:201-205`).
  JPGs `:223-248`: group A (2, Apple-tagged, Display P3 ICC), group Z (8, NUL-filled camera and
  editor strings, no ICC, EXIF ColorSpace sRGB), group M (1, those tags absent, no ICC, ColorSpace
  sRGB); all 11 EXIF orientation 1. Pre-corrected CANDIDATES `:366-388` = the nine Z/M JPGs (the
  mp4 is a video, out of scope); above-surface candidates: "None can be named from the selected
  tags" (`:361-364`). Largest stored size 5712x4284 (38 photos, about 24.5 MP; `:111-112`).

## Locks

- No frozen interface; no `src/` change; no dependency (numpy, Pillow, pillow-heif, psutil and the
  FFmpeg CLI already present); no OS-specific code in the tool (a Windows-only `peak_wset` is
  recorded as `None` elsewhere, as bench does).
- The footage folder is read only: never written, renamed or opened for writing; every output under
  `<working>/wp3.6p/` through a write guard (as `photo_check.make_guard`); tests under `tmp_path`.
  The runner is always given `--out` under `work/` (never `--beside-source`).
- **Privacy (BINDING):** no GPS, location, device serial, MakerNote content, EXIF value or footage
  path in any committed file or return. Format facts only: pixel and stored sizes, bit depth, box
  layout, Orientation and `irot` codes, ICC description and classification, EXIF field NAMES and
  counts, presence booleans (GPS IFD present, MakerNote kept). Photo names relative to `Phone/`
  only, as the inventory does (`inventory-2026-10-29.md:195`). Camera make, model and software
  strings are EXIF values: never written. The tool's committed-facing summary is built by an
  allow-list of keys, and a test proves a planted synthetic GPS value, Make string and footage
  path never reach it. GoPro IMU and GPS are out of scope.
- No look check, no scene judgement of any photo (owner-reserved; Q7).
- Every new test is parallel-leg except the one `footage` test of Q4 (serial leg, reason beside the
  marker); no `gpu` test (the GPU runs are seat runs).

## Task ladder

1. **Read and map** the anchors above on the dispatch base; `uv sync`.
2. **Round 0 (no code), in the ledger, then YIELD:** (a) the re-located anchors; (b) the tool's
   design: subcommands, the per-photo record fields, the class map (Q7), the summary allow-list;
   (c) the oracle of Q3 with a RUN REQUEST at the seat, outputs under `work/wp3.6p/r0/`: FFmpeg
   on `Phone/IMG_6690.HEIC` (`irot` 180 class) and `Phone/IMG_6720.HEIC` (270): does FFmpeg's HEIF
   demuxer decode the primary (grid or not), at what size, with what rotation side data, and does
   `-noautorotate` give the stored orientation; report format facts only; (d) a RUN REQUEST timing
   ONE runner export of a 5712x4284 owner HEIC (`--neutral --bit-depth 16 --out
   work/wp3.6p/r0/out --record ...`, default device): wall time, the record's device reason, PNG
   size, free disk; this sizes Q5 and Q9; (e) the RED list, each test with the base it fails on;
   (f) the depth reading. A FFmpeg that cannot decode the Apple primary is NOT a STOP: Q3's
   fallback applies; say which.
3. **RED, then the tool** (`tests/test_photo_verify.py`, all synthetic, under `tmp_path`):
   - `orientation` on the four `heic-ad24-*` samples: the product read matches the oracle's
     upright pose and is apart from every other pose; a planted "EXIF always honoured" and a
     planted "EXIF never honoured" read each fail by name on the layout they break;
   - `export` on WP2.3 stills (one HEIC, one P3 PNG16, one untagged JPEG): V9 quantised max and
     mean within AD-11, raw recorded; V5: bit depth equals the requested one at 8 and 16, ICC equal
     to the source's or the D53 built-in, D63 fields set and every other field kept; a planted
     off-neutral parameter set misses V9 by name; a planted writer dropping `iCCP` fails V5 by name;
   - privacy: a test-built JPEG carrying synthetic GPS values and a synthetic Make string, in a
     tmp "footage" folder: the summary and stdout contain none of them and no path under that
     folder; the record files stay under the guard root;
   - `memory` on a tiny still with the samplers stubbed: the record carries the estimate, the free
     memory reading, the device reason, peak RSS and peak device memory keys; `--force-cpu` gives
     `"CPU: forced"`;
   - the Q4 footage test (serial leg), if ruled.
4. **Light runs** (the cell's): `uv run pytest -q tests/test_photo_verify.py -m "not footage"`,
   ruff, format, mypy. Reviewer A to convergence (END YOUR TURN once a round's verdict is
   adjudicated, BEFORE remediating).
5. **Seat runs (the orchestrator; RUN REQUEST each, with free disk checked first, Q9):**
   (a) `uv run python tools/photo_check.py --name wp3.6p-io` over the configured footage folder (73
   photos; the record of read verdicts, layout and colour; I/O round trip as WP4.5 left it);
   (b) `photo_verify.py orientation` over the 62 HEICs; (c) `photo_verify.py export` per Q5;
   (d) `photo_verify.py memory` per Q6 in an EXCLUSIVE window. Each: command, counts, EXIT, wall
   time, free disk before and after, in the ledger.
6. **Report** `docs/reports/wp3.6p-real-photos.md`: per class (Q7) tables: read verdicts; HEIC
   layout (grid, `irot`, `imir`, auxiliary and thumbnail counts); AD-24 result per `irot` class
   and which AD-24 branches the owner's files do and do not exercise; colour classification
   (primaries, transfer, `assumed`, ICC description); V5 and V9 figures; the memory record; the Z/M
   group in its own rows; "for CHARC" lines (Q3, Q6, Q8). Ledger: rounds, depth, every seat run.
7. **Gate:** Reviewer B at the orchestrator's seat, then the ONE two-leg gate.

## Hardware flags

- The memory leg (task 5 d) records memory figures: **EXCLUSIVE** (plan 4.3: nothing else heavy
  running), `gpu`, clear of WP4.3's windows, at the orchestrator's seat.
- The `photo_check`, `orientation` and `export` runs are heavy (73 photos up to 24.5 MP; PNGs of
  tens of MB each) but record no timing or memory figure: one heavy job at a time, not exclusive.
- Disk: C: was at 97 % used on 2026-10-29 ~17:55Z (`CLAUDE.md:30`); check free space before every
  seat run (Q9); `work/` is pruned only on the owner's word.

## STOP for

Any `src/` change, or a defect the run proves in `io/photo/`, the runner or the core (evidence to
CHARC, no fix); a photo that reads in a way AD-24 does not predict; a refusal or a read failure of
any owner photo; any edit outside the owned list; any write under the footage folder; any value
the privacy lock forbids appearing in a record that would be committed; a dependency; a choice this
brief leaves open.

## Return report

Commits by the orchestrator: `feat(wp3.6p): ...`, `test(wp3.6p): ...`, `docs(wp3.6p): ...`, by
pathspec, `-c core.autocrlf=false`, LF blobs, a `Co-Authored-By:` footer. The final turn names:
the per-change list; the light runs read off the final state; Reviewer A's rounds and verdict; each
lock honoured on disk (the privacy grep over the report, the ledger and the tool's summary); the
seat-run figures by class; the AD-24 statement for CHARC; any deviation or STOP.

## Questions for CHARC (recommended answer first)

- **Q1. Lane and tier.** WP3.6 Q11 sized this as "a mechanical run of `tools/photo_check.py`"
  (sonnet-medium). The commission asks more than `photo_check` measures: an AD-24 oracle
  independent of the product, V5 and V9 on the RUNNER's output, and a memory instrument for HEIC
  (bench reads no HEIC). That is an instrument build, the class `implementer-codex-sol-high` and
  `implementer-sonnet-high` cover, not sonnet-medium's "brief leaves nothing to decide".
  Recommended: **CODEX** (pace), nets the Claude pass; Tier **STRONG** although no `src/` file
  changes, because a missed finding here becomes a false CONFIRMED on AD-24 and closes owed V5/V9
  legs (`review-gate-clearwater.md:36-42`: "Tier by the blast radius of a MISSED finding").
  Alternative: sonnet-high on the Claude lane in parallel with the Codex queue (WP4.4, WP-DR87),
  or tier `fast` per the literal "tools under `tools/` that produce no shipped output".
- **Q2. Where the instrument lives.** Recommended: NEW `tools/photo_verify.py` and
  `tests/test_photo_verify.py`; `tools/photo_check.py` and its test UNCHANGED (its footage test is
  the gate's real-photo witness WP4.5 relied on; widening it lengthens every serial leg). Alternative:
  extend `photo_check.py` with the three legs as flags (owns `tests/test_photo_check.py` for new
  tests only).
- **Q3. The AD-24 oracle, and what AD-24's status can become.** Image size cannot show a double
  rotation of the 20 `irot` 180 / EXIF 3 files (180 twice is upright-sized), so the check compares
  pixels. Recommended: (a) an independent decode by the FFmpeg CLI (its own HEVC decoder and HEIF
  demuxer), read with `-noautorotate` and turned by the file's own `irot`/`imir`, downscaled; the
  product read must be nearest the upright pose and apart from the other seven (the
  `test_wp41_photo_path.py:324-339` form); fallback if round 0 shows FFmpeg cannot decode Apple's
  primary: the HEIC's own thumbnail item decoded by pillow-heif (libheif applies the thumbnail's
  transforms; the product's EXIF logic is not involved). The owner's files exercise only two AD-24
  layouts: `irot` with an AGREEING EXIF tag (39) and identity (`irot` 0, tag 1; 23); the
  tag-only and `irot`-only branches have no real witness. So the report states AD-24 "confirmed on
  the Apple layouts present" with the counts, and CHARC rules AD-24's status at the accept. The
  D63 words "provisional until an owner photo is read" are spec text: their change is the owner's
  (next spec revision), as is the `:567` open item (the owner's photos are at most 24.5 MP).
  Alternative: report the `photo_check` layout facts only and leave AD-24 PROVISIONAL.
- **Q4. A real-photo regression test.** Recommended: ONE `footage` test in
  `tests/test_photo_verify.py` on four HEICs, one per `irot` class (`IMG_6703` 0, `IMG_6718` 90,
  `IMG_6690` 180, `IMG_6720` 270; names from the inventory `:208-219`), asserting the oracle's
  upright pose; skip only when the footage is absent (as `test_photo_check.py:134-139`); about
  tens of seconds on the serial leg. Alternative: no footage test (the seat run is the evidence).
- **Q5. The export leg's scope.** Recommended: every one of the 73 through the runner with
  `--neutral --bit-depth 16` on the default device (V9 and V5 on each, the record's device named),
  plus `--bit-depth 8` on one photo per class (seven) for "selected bit depth honored" and AD-11's
  below-source-depth clarification; each PNG measured then handled per Q9. Alternative: one photo
  per class at both depths (fewer hours; V9 on 7 of 73).
- **Q6. The Result 2 memory leg.** Recommended: the PRODUCT runner (the prototype cannot read
  HEIC) on one 5712x4284 HEIC (the largest owner size; 38 photos share it), in an EXCLUSIVE
  window: default device, then `--force-cpu`; record `memory_estimate_bytes` for that size and c3,
  free device memory, the device reason, the runner's process-tree peak RSS (psutil sampling) and
  device-wide peak graphics memory (`nvidia-smi` sampling), against 16 GB and 8,188 MiB. This
  closes Result 2's PENDING photo row on the owner's largest photo; V15 and any 48 MP figure stay
  WP5.2's. Alternative: also a 5712x4284 Z-group JPEG through the same runner (a second decoder),
  or the prototype `bench.py` on that JPEG for comparability with the Part B figures.
- **Q7. Classes; pre-corrected and above-surface.** Recommended: the tool takes a class map (the
  inventory's lists, as a small JSON under `work/` the orchestrator writes; names only): HEIC by
  `irot` class (0, 90, 180, 270), JPG-A, and the pre-corrected candidate group Z/M (9); every
  table reports Z/M in separate rows and no pooled figure includes them. No scene classification:
  the I/O, orientation and memory checks are scene-independent, so above-surface photos need no
  separate treatment here; the report says all 73 stay undecided on that question and leaves it
  to the owner's visual review. Alternative: a pixel heuristic naming above-surface CANDIDATES
  (a judgement on scenes; not recommended without the owner).
- **Q8. DR-42, DR-43 and a new colour observation.** No owner photo is a PNG or TIFF and every
  HEIC carries an ICC, so DR-42 (a) has no real-file witness and DR-42 (c) (`tiff.py`) is not
  touched; DR-43 needs an IF-6 field or an `io.photo` change (neither owned). The Z/M JPGs declare
  sRGB only by EXIF ColorSpace, which `describe_color` does not read: they read as untagged
  (`assumed=True`, the G10 "untagged" warning) though their colours are read as sRGB anyway.
  Recommended: no product fix here; the report counts per class the `assumed` readings and any
  photo whose EXIF `sanitise` dropped (DR-43's real-file witness, expected zero), and CHARC decides
  the rows (DR-42 (a) and (c) re-targeted; a new MINOR row or an extension of DR-42 (a) for EXIF
  ColorSpace). Alternative: a CHARC grant of `io/photo/color.py` to read EXIF ColorSpace 1 as tagged
  sRGB (product, STRONG; changes a G10 message).
- **Q9. Disk.** 73 16-bit PNGs of up to 24.5 MP, for each of task 5 (a) and (c), plus the seven
  8-bit ones. Recommended: the `export` leg deletes each of its own PNGs under
  `<working>/wp3.6p/` after measuring it (md5 and size kept in the record), keeping the seven class
  representatives; `photo_check` keeps its PNGs as today (unchanged tool); the orchestrator checks
  free space before each run against round 0's measured PNG size and stops below 20 GB free.
  Alternative: keep every output and ask the owner for a prune afterwards.
