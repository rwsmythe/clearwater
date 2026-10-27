# WP-T3 — Fixture checker hardening (dispatch brief, FINAL)

**Status:** FINAL 2026-10-27 (CHARC `3c3c35d7e40b525e`); written by a drafting helper for the orchestrator (generation 12) at
CHARC's ruling `6f725eee`. Approved; base = the main commit named in the dispatch prompt.
Closes DR-33 (a)-(d) (`docs/debt-register.md`). Spec **v0.5.5**; AD-14, AD-24 (the fixtures'
owners); the WP2.3 brief `docs/briefs/wp2.3-brief.md` built what this hardens. Owner
decisions: none. Not exclusive; records no timing. Tests and tools only; no product code.
- Cell: `implementer-sonnet-high`. CALIBRATION package, Sonnet lane (design pass
  `docs/proofs/harness-dual-model-implementers.md` section 4.3). Reviewers are the OTHER model:
  Reviewer A (your loop) and Reviewer B (the orchestrator's seat) are both Codex (question 1).
- Worktree `.worktrees/wp-t3`, branch `wp-t3`, base = the main commit named at dispatch.
- **Calibration size facts (measured on main `47c1a1c`, for CHARC's ratio against WP3.20R):**
  - Modules touched: `tools/fixtures/stills.py` (669 lines), `tools/fixtures/flicker.py` (572);
    plus `tests/fixture_plugin.py` (252) for ONE function if question 2 is answered as
    recommended. `tools/fixtures/` has 6 modules (2,803 lines) and `__init__.py`; the other
    four (`files.py`, `generate.py`, `manifest.py`, `video.py`) are not touched.
  - Test file: `tests/test_fixtures.py`, 1,382 lines.
  - Items: 4 (DR-33 (a)-(d)); planted defects: 6 (a 1, b 1, c 2, d 2); planned tests: 10
    functions (8 new, 2 replaced), two of them parametrized (66 and 22 samples).

**Why.** DR-33, adjudicated NOT BLOCKING at the WP2.3 gate: "Fixture-test strength against a
FUTURE generator regression; every committed sample is verified correct by raw probes". The
trigger: "Before ANY regeneration of committed stills or the flicker clip, or the next change to
`tools/fixtures/`: measure the format from magic bytes, detect XMP by its namespace URI and any
`GPS*` property, read `irot` through `ipma` and check `ispe`, and add the two flicker identity
fields, each with a planted defect." Phase 3 tests lean on these samples; a checker that cannot
fail is worse than none.

| Field | Content |
|---|---|
| ID and title | WP-T3 — Fixture checker hardening; closes DR-33 (a)-(d) |
| Goal | The WP2.3 fixture checks FAIL on the four regressions DR-33 names, each shown by a planted defect that fails by name, while every committed fixture stays byte-identical. |
| Scope (exactly DR-33 (a)-(d)) | (a) "A still's container format is not measured from the file: `tests/test_fixtures.py` compares `metadata[\"source_format\"]` with the manifest's `kind`, so a TIFF written to a `.jpg` path would pass after regeneration (all 66 committed stills match by magic bytes)." (b) "The raw XMP/GPS scan matches fixed spellings (`<x:xmpmeta`, `exif:GPS`, `GPSLatitude`), so valid XMP with another prefix carrying only `GPSLongitude`/`GPSAltitude` would pass; no generator writes XMP." (c) "AD-24 `irot` presence is read from `ipco` without its `ipma` association to the primary item, and `stored_width`/`stored_height` are not checked against `ispe`." (d, minor) "the flicker gate's stream identity omits `ffprobe_errors` and packet durations." |
| Files owned | `tools/fixtures/stills.py` (new functions and two call-site edits, tasks 1-3), `tools/fixtures/flicker.py` (task 4), `tests/test_fixtures.py` (the roster below), `tests/fixture_plugin.py` (`verify_generated` ONLY, and ONLY if question 2 is answered as recommended), `docs/reports/wp-t3-fixture-checkers.md` (NEW, short), `docs/proofs/wp-t3-ledger.md` (NEW). |
| NOT owned | Every file under `tests/fixtures/` (the 87 committed files, including `manifest.json`); `tools/fixtures/files.py`, `generate.py`, `manifest.py`, `video.py`, `__init__.py`; `tools/spike_io/` (`photo.heif_transforms` is read-only to you: it stays as the independent second reader); `tests/conftest.py`; `src/`; `src/clearwater/interfaces/` (**frozen: nothing under it changes**); `pyproject.toml`, `uv.lock` (no new dependency). |
| Interfaces consumed | `tools/fixtures/video.py` (`ffprobe_json`, `GenerationError`, `tools_available`), `tools/spike_io/photo.py` (`heif_transforms`, `png_chunks`), `tests/fixture_plugin.py` (`verify_generated`, `FIXTURES_DIR`), the committed `tests/fixtures/manifest.json`; Pillow, pillow-heif, NumPy, FFmpeg 9.0.2 as in WP2.3. |
| Hardware flags | None timed. The flicker tests (tasks 4) generate the 89 MB FFV1 clip once into pytest's basetemp (`--basetemp=work/pytest-wpt3`); they skip with a reason when FFmpeg is absent. |
| Out of scope | Regenerating or editing ANY committed sample or `tests/fixtures/manifest.json` (see the binding constraint); the files-group TIFF and DNG samples (`dng-by-tag`, `dng-by-extension`, `dng-extension-only`: `dng_entry` already reads their tag); the video samples' checks; `photo.heif_transforms` (WP2.1S; WP3.6 tests its own `irot` reading against these samples); a new generator or sample; XMP writing; any GoPro `gpmd` track, IMU or GPS data. |
| Done | Plan 4.5; ruff check, ruff format --check, mypy (strict, `tools`) and the full pytest green; the byte-identity check (task 5) clean; every planted defect fails by name; Reviewer A converged. |

## The binding constraint: NO regeneration of committed samples

`tests/fixtures/` holds 87 tracked files: 86 sample files (66 stills, 8 video, 1 mask, 8 GoPro-name
placeholders, 3 DNG/TIFF copies) plus `manifest.json`; the manifest lists 87 entries
(86 committed + the generated `ad14-flicker`, 89 MB, never committed). All 87 files stay
byte-identical; the gate asserts it (`git diff --quiet <base> -- tests/fixtures`). Every check
below is built to run on the committed bytes as they are. **If an item cannot be checked
without regenerating or editing a committed file, STOP and ask for that item** (with the
reproduction); do not edit the fixture. Never run `generate.py` with `--out tests/fixtures`.

## Task ladder

0. **Ground.** Re-check every line number below against the worktree (anchors drift). A
   mismatch or an unreadable committed file is a STOP, not a workaround.
1. **(a) Container format from magic bytes** (`stills.py`, `tests/test_fixtures.py`).
   - Add `container_format(data: bytes) -> str | None`: `"png"` for the 8-byte PNG signature,
     `"jpeg"` for `FF D8 FF`, `"tiff"` for `II*\0` or `MM\0*`, `"heic"` for an ISO-BMFF file
     whose bytes 4:8 are `ftyp` AND whose major brand is `heic` or `heix` (the committed set);
     else `None`. Nothing from Pillow, the path or the manifest.
   - Add `check_still_format(data: bytes, kind: str) -> str | None`: None when
     `container_format(data) == kind`, else a message naming both.
   - `stills.measure` sets `facts["format"]` from `container_format` (mapped to the existing
     `"PNG"/"JPEG"/"TIFF"/"HEIC"` spellings, so the manifest facts are unchanged) and `_record`
     (line 394) refuses (`ValueError`) when `check_still_format` fails for the requested `kind`.
   - `tests/test_fixtures.py:372` (`assert metadata["source_format"] == entry["kind"]`) compares
     two manifest fields. Replace it with T1 below; keep the rest of that test.
2. **(b) XMP by namespace URI and any `GPS*` property** (`stills.py`, tests).
   - Add `xmp_gps_findings(data: bytes) -> list[str]`: findings are NAMES only, never values.
     It reports (i) each XMP marker present: the packet header `http://ns.adobe.com/xap/1.0/`,
     the meta namespace `adobe:ns:meta/`, the EXIF namespace `http://ns.adobe.com/exif/1.0/`,
     `<?xpacket` (a list in one constant); (ii) every name of the form `GPS` + letters
     (regex over bytes, any or no namespace prefix, element or attribute), reported as the
     property name found, e.g. `GPSLongitude`. Sorted, de-duplicated, deterministic.
   - **No location value is ever printed, logged or committed.** The scan detects GPS
     properties in order to REFUSE them. The planted packet uses synthetic zero values
     (`0,0.0N`); replace the existing planted value at `tests/test_fixtures.py:503`
     (`21,18.5N`) the same way.
   - Replace `XMP_MARKERS`, `_xmp_markers` (lines 476-482) and the two tests at 490 and 498 by
     T3 and T4; the old fixed list survives only as a local constant inside T4, to show the old
     scan misses the plant.
   - Over all 86 committed files the scan must return nothing (run it first: a hit on a real
     sample is a STOP with the file name and the finding name, not a value).
3. **(c) `irot` through `ipma`, `ispe` checked** (`stills.py`, tests).
   - Add `heif_primary_properties(data: bytes) -> dict[str, Any]`: walk `meta` (a full box),
     read `pitm` (primary item id; version 0 is 16-bit, else 32-bit), read EVERY `ipma` box in
     `iprp` (version and flags decide the item-id width, 1-byte or 2-byte association; the
     essential bit is masked off; index 0 means none), and map the primary item's indices to
     the 1-based `ipco` property list. Return `{"item": id, "irot": degrees or None, "imir":
     0/1 or None, "ispe": (width, height)}`. `ValueError` naming the missing piece when `pitm`,
     the primary's `ipma` entry or its `ispe` is absent. Degrees as `photo.heif_transforms`
     reports them: `(byte & 3) * 90`.
   - `stills.measure` takes `irot` and `imir` from it instead of `photo.heif_transforms`
     (keys and values unchanged, so the regenerated manifest is identical).
   - Extents rule, applied by a new `check_heif_extents(facts: dict[str, Any], props:
     dict[str, Any]) -> list[str]` and called from `_record` for HEIC: `ispe` equals
     `(stored_width, stored_height)` when the entry has them (the four `heic-ad24-*` samples);
     for every HEIC, `ispe` swapped when `irot` is 90 or 270 equals `(width, height)` (what
     libheif reports after applying `irot`).
   - Keep the independent reader in the AD-24 test: `photo.heif_transforms(data)["irot"]` stays
     asserted; add `heif_primary_properties(data)["irot"] == irot` beside it.
4. **(d) The flicker gate's identity** (`flicker.py`; `fixture_plugin.py` per question 2).
   - `probe_clip` (line 326) merges the stderr lines of BOTH ffprobe calls into
     `ffprobe_errors` (today the packet call's errors are dropped: `packets, _ =`). A truncated
     clip complains only in the packet scan (checked on a scratch FFV1 clip: `File ended
     prematurely`, 9 of 10 packets, nothing on the stream call). A clean clip stays `[]`.
   - Add `"ffprobe_errors"` to `STREAM_IDENTITY` (line 354). The manifest already records it
     (`[]`), so `verify_generated` compares it with no manifest change.
   - Packet durations: add `packet_durations(path: Path) -> list[int]` (ffprobe
     `-show_entries packet=duration`, ticks of the stream's time base) and
     `identity_problems(path, recorded) -> list[str]`, which returns the existing
     `"<name> is X, the manifest has Y"` messages for `STREAM_IDENTITY` plus
     `"packet_durations is [...], the declared rate gives N ticks"` when any packet's duration
     differs by more than one tick from `Fraction(den, num) / Fraction(time_base)` taken from
     the manifest's own `r_frame_rate` and `time_base` (30000/1001 and 1/1000 give 33). This is
     derived from fields the manifest already holds, so the manifest does NOT change.
     `verify_generated` calls `identity_problems` in place of its inline comprehension and
     keeps its message format (`tests/test_fixtures.py` asserts `"packet_pts_sha256 is"`).
   - Evidence the rule is sound (synthetic 10-frame FFV1 MKV at 30000/1001, scratch run
     2026-10-27, NOT the real clip): every packet duration is 33; `-bsf:v setts=duration=17`
     keeps pts and both rates and makes every duration 17. First measure the real clip: if its
     durations are not within one tick of the rule, STOP and ask (question 2).
   - `build_clip` (line 517) adds the same durations rule to its `wrong` list, so a
     regeneration refuses a clip whose durations disagree with its declared rate.
   - The new duration field is NOT added to `probe_clip`'s dict or to `measure_clip`'s output
     (`facts={"design": design, "stream": measured}` is written into the manifest;
     `test_regenerated_manifest_is_byte_identical` would fail).
5. **Byte identity and gates.** After the last edit: `git diff --stat <base>..HEAD --
   tests/fixtures` is empty; `test_committed_files_match_the_manifest` (line 83) and
   `test_regenerated_manifest_is_byte_identical` (line 1091) stay green; ruff, mypy, pytest as
   in Done. Quote the lines in the ledger.

## Test roster (each planted defect fails BY NAME; recipe section 2: show the OLD check passes it)

| # | Item | Test | Plant (fails by name) |
|---|---|---|---|
| T1 | a | `test_still_container_format_is_read_from_magic_bytes`, parametrized over the 66 stills: `container_format(bytes) == entry["kind"]` and `measure(...)["format"]` agrees | |
| T2 | a | `test_planted_wrong_container_fails_by_name` | a committed `tiff8-*` file's bytes copied to a `tmp_path/x.jpg` (kind `jpeg`) and an `ftyp` file with major brand `mp42` as kind `heic`: `check_still_format` names both formats; show the OLD comparison (`metadata["source_format"] == entry["kind"]`) is unaffected by the bytes |
| T3 | b | `test_no_committed_file_carries_xmp_or_a_gps_property` (replaces line 490): all 86 committed files, any container | |
| T4 | b | `test_planted_xmp_with_another_prefix_and_gps_only_is_caught_by_name` (replaces line 498) | a JPEG with an APP1 XMP packet using prefix `foo:` and ONLY `foo:GPSLongitude` / `foo:GPSAltitude` (zero values): the findings name `GPSLongitude`, `GPSAltitude` and the namespace; the old fixed list returns nothing for it; Pillow still reads the file and EXIF GPS is absent |
| T5 | c | `test_heic_primary_properties_come_through_ipma_and_ispe`, parametrized over the 22 HEIC samples: `heif_primary_properties` agrees with the manifest's `irot`/`imir`, and `check_heif_extents` is empty | |
| T6 | c | `test_planted_irot_not_associated_with_the_primary_fails_by_name` | bytes of `heic-ad24-both` with the `irot` association in `ipma` zeroed (same length): `heif_primary_properties` gives `irot` None while `photo.heif_transforms` still says 270; the manifest comparison fails by name |
| T7 | c | `test_planted_ispe_disagreeing_with_stored_size_fails_by_name` | bytes of `heic-ad24-irot-only` with the `ispe` width field edited: `check_heif_extents` names `ispe` and the stored size |
| T8 | d | `test_flicker_identity_includes_ffprobe_errors_and_packet_durations` (FFmpeg): `STREAM_IDENTITY` contains `ffprobe_errors`; the real clip has `[]` and durations within one tick of the rule; `identity_problems` is empty | |
| T9 | d | `test_planted_truncated_clip_fails_by_name` | the clip with its last 40 bytes cut: `identity_problems` names `ffprobe_errors`; then with every OTHER identity field copied from the plant into a copy of the recorded stream, ONLY `ffprobe_errors` is reported, and the old tuple (without it) passes |
| T10 | d | `test_planted_clip_with_other_packet_durations_fails_by_name` (FFmpeg) | the clip stream-copied with `-bsf:v setts=duration=17` (as `clip_at_25_fps` is built at line 994): pts hash, counts and rates equal, `identity_problems` names `packet_durations`; the old tuple passes it |

If a plant cannot be built as described (for example the cut yields no ffprobe error), say so in
the ledger and use the nearest real file edit; a monkeypatched `ffprobe_json` is the last
resort and must be named as such. No plant is committed under `tests/fixtures/`; all live in
`tmp_path`.

## Declared operating envelope

Windows 11; Python 3.12; FFmpeg 9.0.2 (gyan; FFV1); Pillow 12.3.0, pillow-heif 1.8.1, NumPy as
locked; no GPU; no footage; the committed fixtures as they are (one image item per HEIC, ISO
BMFF `ftyp` brands `heic`/`heix`, EXIF and ICC only, no XMP). Out of envelope (tag findings
reachable only there): a real camera HEIC (grid of tiles, thumbnails, auxiliary items; the
`ipma` reader handles a primary that is not the first item, but no such file is committed),
BigTIFF, AVIF, UTF-16 or zlib-compressed XMP (question 3), other FFmpeg builds, other
operating systems (portable, N1, not run there).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Reviewer: the OTHER model, so **Codex** (WSL transport, `codex-cli 0.162.1`), tier per
  question 4 (recommended STRONG: `-m gpt-6.1-sol -c model_reasoning_effort=high -s read-only
  --skip-git-repo-check`, banner `model: gpt-6.1-sol` / `reasoning effort: high`). Run by you
  at your seat to convergence; five-round gate; ledger `docs/proofs/wp-t3-ledger.md`
  (per round: counts by severity, in-envelope vs out, NEW vs REOPENED, reverts, product-code vs
  test-only fixes, transport and CLI version, the depth the dispatcher gives you).
- Runner shape: copy `C:\Users\rwsmy\clearwater-review-evidence\wp3.20\r1\run_review.sh` and
  `review-prompt.md`; the diff is `git -C <worktree> diff -U8 <base>..HEAD -- . ':!uv.lock'
  ':!docs/proofs'` generated Windows-side; probe first and require one `^ succeeded in`; the
  four anchored assertions per round. Evidence in
  `C:\Users\rwsmy\clearwater-review-evidence\wp-t3\rN\` with md5s.
- **WHAT TO EXAMINE:**
  - each of the four checks fails on its regression and passes the 86 committed bytes: a
    check that cannot fail, or that fails on a good file;
  - `container_format` and the `ftyp` brand rule (a video `ftyp` mistaken for a HEIC);
  - the XMP scan: a name `GPS` + letters inside binary compressed data (false positive on a
    real file), a prefix-less default-namespace form, a finding that prints a value;
  - `heif_primary_properties`: `ipma` versions and flags, essential bit, index 0, more than one
    `ipma` box, a primary that is not the first item, `ispe` absent;
  - the duration rule's tolerance and the `Fraction` arithmetic; errors merged from both ffprobe
    calls; the manifest not changed by the new fields;
  - byte identity of `tests/fixtures/`, no write outside `tmp_path`/`work/`, no footage path
    use, no location value anywhere;
  - comments and docstrings true of the code (STREAM_IDENTITY's docstring, `probe_clip`'s).
- Reviewer B is the orchestrator's seat pass on the merge candidate: Codex at `gpt-6.1-sol` /
  high (the ruling's pin), not the same session as A.

## Notes for the cell

- **Yields.** Yield at every round boundary with the ledger; after a round is adjudicated END
  YOUR TURN before remediating. The dispatcher reads `scripts/cell_depth.py` and tells you the
  figure; ~250K is the evaluation point, ~400K STOP. At round 5 and every 5 after, STOP and
  report the ledger for approval to continue.
- **Test windows.** Inner loop: `uv run pytest tests/test_fixtures.py -q --basetemp=work/pytest-wpt3`,
  output to a file, summary lines only. The full suite (about 4,766 tests, 27-45 min, serial)
  runs ONLY in a window the dispatcher grants by message, in the background with output to a
  file under `work/`; send `WINDOW RELEASED: <summary>` when it finishes. Never two heavy jobs
  at once. Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` to PATH for FFmpeg.
- **STOP for:**
  - any item that cannot be checked without regenerating or editing a committed fixture;
  - a hit of `xmp_gps_findings` or a failure of `container_format` on a committed file;
  - the real clip's packet durations outside the rule;
  - a needed change in `tools/spike_io/`, `tests/conftest.py`, `src/` or `interfaces/`;
  - a dependency; OS-specific code; a write outside the worktree, `tmp_path` and `work/`.
- **Working rules:** `uv sync`; the orchestrator copies `clearwater.local.toml` into the
  worktree (never edit or commit it); commit by pathspec,
  `git -c core.autocrlf=false commit -m "test(wp-t3): ..." -- <paths>` (conventional commits
  carrying `wp-t3`), one logical change each, with a `Co-Authored-By:` footer naming your model;
  every committed blob LF (`git cat-file -p HEAD:<path> | tr -cd '\r' | wc -c` prints 0); never
  a bare `cd`; never `git stash`; never post to a mailbox. The footage folder
  `C:\Users\rwsmy\clearwater-footage\` is read-only and not used here; outputs go under `work/`.
  GoPro `gpmd`, IMU and GPS data are out of scope: nothing of the kind is read, printed or
  committed, and no location tag appears in any committed record.
- **Report** `docs/reports/wp-t3-fixture-checkers.md`: the four checks, the plants, the
  byte-identity lines, limits. Short.
- **Return report** = your FINAL message, under about 70 lines (`docs/dispatch-recipe.md`
  section 4), delivered to your dispatcher: per-commit changes; the gates and skip count; the
  roster with results (each plant: fails by name, and the old check passes it); the byte-identity
  lines; the Reviewer A rounds, assertions and verdict; the ledger path; STOP count with
  reproductions; locks stated honored-on-disk; deviations.

## Rulings

Carried from CHARC `6f725eee` (generation 4): "Scope = DR-33 (a)-(d) exactly: format from magic
bytes; XMP by namespace URI and any `GPS*` property; AD-24 `irot` through `ipma` with `ispe`
checked; the two flicker identity fields; each with a planted defect that fails. NO
regeneration of committed samples (the 87 fixtures stay byte-identical; GATE_CHECKS asserts
it)." Lane: `implementer-sonnet-high`; the pace tiebreak is suspended for the calibration pair.
FINAL (CHARC FINAL `3c3c35d7e40b525e` (2026-10-27 06:33Z, replying to `4b2d7b2e92048eaf`)). Approved: `implementer-sonnet-high`; Codex Reviewer A AND B at
`gpt-6.1-sol`/high.

- Q1 Reviewer A's model: the helper is RIGHT and CHARC's ruling line was WRONG. R2 makes both reviewers the OTHER model: Reviewer A = Codex (the cell's loop), Reviewer B = Codex at the orchestrator's seat. CORRECTED; the brief as drafted stands.
- Q2 packet durations without touching the manifest: ADOPTED (rule derived from the manifest's own `r_frame_rate`/`time_base`; `tests/fixture_plugin.py` `verify_generated` one call; the real clip outside the rule = STOP and CHARC chooses).
- Q3 XMP encodings: ADOPTED accept and state; the UTF-16 / compressed-iTXt gap becomes a MINOR DR row at the accept (trigger: the first PNG sample carrying an iTXt chunk, or XMP writing by any generator).
- Q4 tier: ADOPTED STRONG for A and B (equal rigor across the pair).
- Q5 "87": ADOPTED the gate is `git diff --quiet <base> -- tests/fixtures` (all 87 tracked files, manifest included).
- Q6 HEIC brands: ADOPTED strict `heic`/`heix`.

## Questions for CHARC (recommended answer first)

1. **Reviewer A's model.** The ruling says "Reviewer A = Claude at your seat as usual", but the
   owner's rule (fill Part 1, 2026-10-26/27) makes the reviewer in both nets the OTHER model, so
   a Claude cell gets the Codex reviewer. Recommended: Reviewer A = Codex (run by the cell, as
   drafted), Reviewer B = Codex at `gpt-6.1-sol` / high at the orchestrator's seat. Alternative:
   A = Claude as the ruling reads, which breaks the fill rule and mixes the lane comparison.
2. **Packet durations without touching `manifest.json`.** The manifest records no durations,
   and anything added to `probe_clip`/`measure_clip` output is written into the `stream` facts,
   changing `manifest.json` (a committed fixture, and `test_regenerated_manifest_is_byte_identical`
   would fail). Recommended: derive the expected duration from the manifest's own
   `r_frame_rate` and `time_base` (task 4), which holds the 87 files byte-identical, and let the
   cell edit `verify_generated` (one call, `tests/fixture_plugin.py`) to use
   `flicker.identity_problems`. Alternative: add `packet_durations_sha256` to the flicker
   entry's `stream` facts: one entry of `manifest.json` changes (no sample is regenerated; the
   clip is generated, never committed), which departs from "87 fixtures stay byte-identical" and
   needs your explicit consent. Also: if the real clip's durations do not follow the rule, the
   cell STOPs and you choose.
3. **Accepted limitation, XMP encodings.** The scan is over raw ASCII/UTF-8 bytes. UTF-16 XMP
   and zlib-compressed PNG `iTXt` XMP are not scanned (the PNG samples are separately held to
   the `IHDR/iCCP/IDAT/IEND` chunk set at line 463). Recommended: accept, state it in the report
   and invite Reviewer A to challenge. Alternative: also scan the UTF-16 LE/BE forms of the
   marker list and the `GPS` pattern (more code, one more plant).
4. **Reviewer tier.** The fill says `fast` for "tools under `tools/` that produce no shipped
   output"; WP-T2 used FAST. This is a calibration package, and the ruling pins B at
   `gpt-6.1-sol` / high. Recommended: STRONG for A and B, so the lane comparison rests on equal
   rigor. Alternative: FAST for A (`gpt-6-luna` / medium), STRONG for B.
5. **What "87" counts.** The ruling's "the 87 fixtures stay byte-identical" matches 87 tracked
   files under `tests/fixtures/` (86 samples + `manifest.json`) and, separately, 87 manifest
   entries (86 committed + the generated clip). Recommended reading, used in this brief: the
   gate is `git diff --quiet <base> -- tests/fixtures` (all 87 files, the manifest included).
6. **HEIC brand strictness.** `container_format` accepts major brands `heic`/`heix` only (the
   22 committed files; `mif1` appears only as a compatible brand). Recommended: strict, so a
   video `ftyp` or an AVIF cannot pass as a HEIC; widen when a real camera brand is committed.
   Alternative: accept the HEIF family (`heic`, `heix`, `hevc`, `hevx`, `mif1`, `msf1`).
