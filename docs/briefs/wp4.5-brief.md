# WP4.5 — EXIF byte fidelity (dispatch brief, FINAL)

**Status:** FINAL on CHARC `f34420e1c8ff5d29` (2026-10-29T18:58:23Z), Q1 RE-RULED (b) by CHARC `c64900357c363330` (19:09:01Z); its Rulings at the end GOVERN
the Questions. DRAFT 2026-10-29 by the orchestrator (generation 23) on CHARC's commission
`ec87b18228de2958` (file `d3ad4388`, 2026-10-29T18:54:29Z). Spec v0.5.7; no spec clause changes. Base = main `5a1538a`. Worktree `.worktrees/wp4.5`,
branch `wp4.5`. Owner decisions: none.

| Field | Content |
|---|---|
| ID and title | WP4.5 — EXIF byte fidelity through the photo writer (D24, D63) |
| Lane | **CODEX**: `implementer-codex-sol-high` (gpt-6.1-sol / high), `codex exec` turns driven by `scripts/codex_cell.py`. Paces at drafting (18:55Z): Codex **0.359** (7.0 % used at 19.5 % of its window) vs Claude **1.433** (69 % at 48.2 %); the orchestrator re-reads both at dispatch. The cell ends every turn with a FILES CHANGED block; the orchestrator commits and runs every heavy command the cell yields. |
| Tier and nets | Tier **STRONG** (product code). Reviewer A = the Claude pass, `scripts/codex_cell.py review` (`claude -p --model opus --effort high`, read-only), between turns, to convergence, five-round gate. Reviewer B = the Claude pass at the orchestrator's seat. Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp4.5\rN\`, `reviewB\`. |
| Sequencing | Lands on main FIRST, before the `stack-g22` merge (inventory + WP4.3a), whose serial-leg red (b) is this defect. CHARC holds main for the stack until the orchestrator's release post. WP4.3 cell 7 and WP4.4 wait behind the stack. |
| Goal | Every EXIF field the D63 edit does not change leaves the writer with the SAME TIFF type, count and value bytes it had in the source, including ASCII-typed fields whose bytes are not 7-bit ASCII. The D63 edits (Orientation 1, Software, PixelX/YDimension, thumbnail dropped) are unchanged. |
| Files owned | `src/clearwater/io/photo/exif.py` (WP3.6: `edit`, `from_tiff`, and any private helper they need); `src/clearwater/io/photo/writer.py` ONLY if the payload hand-off at `:134-140` must change (state why in round 0); NEW `tests/test_io_photo_exif_bytes.py`; `docs/reports/wp4.5-exif-bytes.md`; `docs/proofs/wp4.5-ledger.md`. |
| NOT owned | `src/clearwater/interfaces/` (IF-1..IF-10 FROZEN), `io/photo/png.py` (the PNG chunk writer beyond the payload it is handed), `io/photo/reader.py`, every other `src/` module, `tools/photo_check.py`, `tests/test_photo_check.py`, every existing test file, `tests/conftest.py`, `tests/fixtures/`, `pyproject.toml`, `uv.lock`, the register. |
| Locks | No frozen interface. No dependency (Pillow only; no piexif, no ExifTool; AD-17). No write under the footage folder; every test writes under `tmp_path` and builds its EXIF synthetically. **Privacy (BINDING, CHARC `b238bd27`):** no real photo's EXIF bytes, GPS values, MakerNote content or serials reach a committed file or a return; GPS test values are synthetic. AD-28 / AD-30: every new test is parallel-leg (no `gpu`, `footage`, `gui` or `slow` marker). |
| Done | Plan 4.5; ruff check, ruff format --check, mypy strict; the touched tests green; Reviewer A converged; Reviewer B returned (clean, or its one remediation and re-run); then the gate at the orchestrator's seat under the OWNER's direction (Verification below). Report and ledger written. No register row (fixed in-package; CHARC). No harness gate. |

**Why.** The two-leg gate on `stack-g22` `8e1114a` went red on
`tests/test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos`,
and it fails on main `27a11ae` too: one of the owner's phone JPGs (the inventory's NUL-filled
Make/Model/Software group) carries a 48-byte binary value in `Exif.LensModel` (tag 0xA434, ASCII
type), with one byte above 0x7F. Pillow decodes an ASCII value as latin-1 and `Image.Exif.tobytes()`
encodes a `str` with `encode("ascii", "replace")`, so the byte comes back as `?`. Spec D24 / 8.1:
"all EXIF preserved except fields made invalid by processing (D63)". The test is right; the product
is wrong (CHARC). Latin-1 or UTF-8 text in Artist, Copyright or ImageDescription from other cameras
meets the same loss.

## Seat evidence (orchestrator, main `5a1538a`, Pillow 12.3.0, synthetic values only)

1. `str` value `"ab\x80cd"` in an ASCII tag -> written `ab?cd`; the same as `bytes` -> written
   `ab\x80cd`, byte for byte.
2. **The `bytes` shortcut is not enough on its own.** `PIL.TiffTags.lookup(42036)` (LensModel) has
   `type=None`, so Pillow GUESSES the type from the value: `str` -> type 2 ASCII, count 6 (with
   the NUL); `bytes` -> **type 1 BYTE, count 5**. For a tag Pillow types as ASCII (Artist, 315)
   `bytes` stays type 2, count 6. A fix that converts values to `bytes` must also pin the entry's
   type to the SOURCE type, or it trades a byte change for a type change.
3. `edit` re-serialises through `Image.Exif.tobytes()`, which builds a fresh
   `ImageFileDirectory_v2` and re-guesses every untyped tag's type from its Python value. The
   source's types are not carried today for any field (ASCII or not); only the values are compared
   by `tools/photo_check.py`.

## Questions (recommended answer first)

1. **The mechanism.** Recommended: **(a)** keep Pillow's writer and carry the source's entry
   types: load the block, and for every IFD the edit keeps (IFD0, Exif, GPS, Interop) set each
   kept entry's tag type to its SOURCE type and give ASCII values whose text is not 7-bit as their
   original bytes, so `tobytes()` writes them verbatim. Round 0 shows from Pillow's source (by
   line) how the type is pinned, for the nested IFDs too. **(b)** if (a) cannot pin types in
   nested IFDs without private-API reliance the cell cannot defend: a byte-level IFD rewrite in
   `exif.py` that patches only the D63 entries and passes every other entry's bytes through. (b)
   is more code and its own offset arithmetic; choose it only with round 0 evidence.
2. **Scope of "fidelity".** Recommended: type, count and value bytes of every kept entry in IFD0,
   the Exif IFD, the GPS IFD and the Interop IFD are equal, source to written block. NOT in
   scope: entry ORDER and offsets (Pillow sorts and re-lays them out), IFD1 (dropped by D63),
   MakerNote INTERNAL offsets (a MakerNote is UNDEFINED bytes and stays byte-equal; whether its
   internal offsets still resolve is a pre-existing property, out of scope: say so in the report).
3. **`from_tiff`.** It builds a block from Pillow-decoded TIFF tags and calls `tobytes()` too,
   so it meets the same loss before `edit` runs. Recommended: the same carry applies there
   (same helper); one test.
4. **Test file.** Recommended: NEW `tests/test_io_photo_exif_bytes.py`; no existing test is
   edited. If an existing test pins a type Pillow guessed (and the fix now carries the source
   type), STOP and name it; do not edit it.

## Task ladder

1. **Read.** `uv sync`. This brief; spec D24, D63 and 8.1; AD-17 (`docs/decisions.md`);
   `src/clearwater/io/photo/exif.py` whole; `writer.py:120-145`; `reader.py` where it calls
   `strip_prefix`/`sanitise`/`from_tiff` (`:170-201`, `:266-277`); Pillow's
   `PIL/Image.py` `Exif.tobytes` / `get_ifd` and `PIL/TiffImagePlugin.py`
   `ImageFileDirectory_v2.__setitem__` / `_setitem` / `tagtype` / `write_string` / `load_string`
   in the venv.
2. **Round 0 note (turn 1, no product code), in the ledger:** the mechanism (Q1) with Pillow's
   lines; how nested IFDs (Exif, GPS, Interop) carry types; the `from_tiff` route (Q3); every test
   you will add with the base it fails on (main `5a1538a`). YIELD.
3. **RED first** in `tests/test_io_photo_exif_bytes.py`, all synthetic, under `tmp_path`:
   - an ASCII tag Pillow does not type (LensModel 0xA434) holding bytes 0x80-0xFF round-trips
     through `edit` with type 2, the same count and the same bytes;
   - a NUL-filled Make (271) and Model (272) round-trip byte-identical (type and count too);
   - a latin-1 Artist (315) and a UTF-8 ImageDescription (270) likewise;
   - a plain-ASCII control is unchanged;
   - a MakerNote (0x927C, UNDEFINED) and synthetic GPS fields (refs, rationals) keep type, count
     and bytes;
   - the D63 four are still edited (Orientation 1, Software `Clearwater`, PixelX/YDimension set,
     no IFD1);
   - the whole write path: `write_photo` of a small image whose metadata carries such a block,
     re-read with `read_photo`, the field's bytes equal (PNG `eXIf` route; and the JPEG-sourced
     route if the writer distinguishes it);
   - `from_tiff` on a synthetic TIFF whose ASCII tag carries a 0x80 byte (Q3).
   Each fails on the base (state the failure text in the ledger). Then the fix in `exif.py`.
4. **Light runs** (the cell's): the new file; `tests/test_io_photo_*.py` (not `footage`-marked);
   `tests/test_photo_check.py -m "not footage"`; `tests/test_wp41_photo_path.py`;
   `tests/test_jobs_export_photo.py`. The orchestrator runs the footage and serial legs.
5. **Reviewer A** (the orchestrator runs it between turns) to convergence; adjudicate each finding
   in the ledger; END YOUR TURN as soon as a round's verdict is adjudicated, BEFORE remediating.
6. **Report** `docs/reports/wp4.5-exif-bytes.md`: root cause (no real EXIF bytes), the mechanism,
   the tests with their base failures, the limits (Q2), the verification figures the orchestrator
   supplies.

## Verification (the orchestrator's seat; the OWNER's direction governs)

Owner, 2026-10-29 ~18:47Z, in chat to the orchestrator (verbatim): "full re-run of the serial is
not required once the issue with the round-trip test is identified and fixed and that test
verifies passed (along with any test impacted by code changed by the fix)."

CHARC's form (`ec87b18228de2958` item 4): the two-leg PARALLEL leg in full, plus the serial tests
impacted, named by node id in the record: `tests/test_photo_check.py` (the footage round trip on
ALL phone photos, now green), `tests/test_io_photo*.py`, `tests/test_wp41_photo_path.py`,
`tests/test_wp41_v8.py`, with their markers. NO full serial leg. Static gates (ruff, format, mypy)
and the CR-byte blob check on every changed file.

## Rulings

CHARC `f34420e1c8ff5d29` (2026-10-29T18:58:23Z), FINAL on fold-in, verbatim:

- **Q1 = (a).** Keep Pillow's writer; pin every KEPT entry's SOURCE TIFF type per IFD (IFD0, Exif, GPS, Interop) from the source bytes, and carry any ASCII-typed value whose bytes are not 7-bit ASCII as its original bytes under the pinned type 2. Round 0 proves from Pillow's own source lines (the `_write_dispatch` / type-guess path) that a pinned type is honoured for a `bytes` value, nested IFDs included; it shows the LensModel case (untyped tag, bytes value) writes type 2 count 6, not type 1. (b), the byte-level IFD rewrite, ONLY if round 0 shows (a) cannot pin a type for an untyped tag; that is a STOP to me with the evidence, not the cell's choice.
- **Q2 = as recommended.** Fidelity = type, count and value bytes of every kept entry equal; NOT entry order or offsets, NOT IFD1 (dropped by D63), NOT MakerNote internal offsets (pre-existing; a named Limit). The tests compare parsed entries (tag, type, count, bytes), not whole-blob equality.
- **Q3 = yes.** `from_tiff` gets the same carry (it calls `tobytes()` before `edit`); one RED-first test on a TIFF source with a non-7-bit ASCII tag.
- **Q4 = yes.** NEW `tests/test_io_photo_exif_bytes.py`; no existing test edited; an existing test that pins a guessed type is a STOP to me, not an edit.

Verification per the owner's direction as the brief quotes it: the full parallel leg + the impacted serial nodes by id (`test_photo_check.py` real-photo round trip over all 73 Phone photos now green; `test_io_photo*`, `test_wp41_photo_path.py`, `test_wp41_v8.py` with markers). Lane Codex (0.359 vs 1.433): concurred.

### Q1 RE-RULED at the round-0 STOP: CHARC `c64900357c363330` (2026-10-29T19:09:01Z), verbatim

This supersedes Q1 = (a) above. Q2-Q4 and Verification stand.

RULING: Q1 = (b), the byte-level IFD rewrite in exif.py. NOT (a').

Grounds, both verified at my seat on the venv's Pillow 12.3.0:
1. The STOP condition in my Q1 ruling is MET. Image.py:4204-4226 builds a fresh ImageFileDirectory_v2 and assigns values only; TiffImagePlugin.py:980-986 builds a fresh IFD per nested dict. No tagtype travels. The cell's and your reading of the lines is correct.
2. (a') fails Q2 on a SECOND fact the ledger only planned to test: Pillow's RATIONAL/SRATIONAL writer REDUCES fractions (TiffImagePlugin.py:843 via _limit_rational / Fraction.limit_denominator). Probe at my seat: a pinned type-5 entry loaded from raw bytes 1234/100 is written back as 617/50. Apple writes GPS coordinates, lens specifications and exposure values unreduced, so (a') would change the bytes of kept rationals across the owner's photos while photo_check's numeric compare stayed green. The same writer path also appends a NUL to an ASCII value that has none in the source (count +1). Q2 as ruled (type, count, value bytes equal for every kept entry) is therefore not reachable by any route that re-encodes values through Pillow; only pass-through of the source entry bytes reaches it. (b) is that route.

SHAPE OF (b), binding on the cell:
- A private rewriter in exif.py, stdlib struct only, no new dependency (AD-17). It parses the TIFF header (II or MM, magic 42; a BigTIFF magic 43 is "cannot be read": None with a warning, a named Limit), walks IFD0, the Exif IFD (34665), the Interop IFD (40965 inside Exif) and the GPS IFD (34853), and writes a new block in the SOURCE byte order. Every kept entry is copied as its source (tag, type, count, value bytes); an out-of-line value is relocated (data copied, offset rewritten, word padded); a pointer entry keeps its source type and count and gets the child's new offset. Kept entries keep their source order; an inserted entry goes at its ascending tag position (a sorted source stays sorted). IFD0's next-IFD pointer is written 0: IFD1 and its thumbnail (513/514) are dropped. Any other IFD-valued entry (330 SubIFDs, or a type-13 IFD entry) is dropped with a warning and named in the report: its value is an offset into a structure the block does not carry.
- The D63 edits by entry: Orientation 274 = SHORT count 1 value 1 (replaced in place, or inserted); Software 305 = ASCII "Clearwater\0" count 11; PixelXDimension 40962 and PixelYDimension 40963 in the Exif IFD keep the source entry's type when present (SHORT or LONG are both legal; a value that does not fit SHORT promotes the entry to LONG), else inserted as LONG; the Exif IFD is created when absent; a None source yields the minimal four-field block as today.
- Damage: a child IFD whose offset or entry table runs past the block is dropped alone with a warning (its pointer removed from the parent), matching from_tiff's documented isolation today; a damaged IFD0 or header RAISES, so sanitise() drops the block exactly as today. Parsing is bounded: every count and offset is checked against the block length before any read or allocation.
- Q3: from_tiff runs the SAME rewriter on the TIFF file bytes (a TIFF file is a header plus IFD0) with a drop set for IFD0 = _TIFF_STRUCTURE plus 330, then the D63 edit; Pillow's Image.open is no longer needed there. Returns None when no entry survives, as today. Existing from_tiff tests (not owned) must stay green; a conflict is a STOP to me, not an edit (Q4 stands).
- Pillow stays on the READ side (load, orientation_of, describe, has_thumbnail) unchanged. The module docstring's "Pillow serialises" sentence is corrected. writer.py untouched (round 0 confirmed the hand-off is bare bytes).

TESTS: the ledger's roster stands under Q2 (parsed entries, independent struct parser, synthetic only, parallel-leg). ADD: an unreduced RATIONAL (1234/100) and a negative SRATIONAL, bytes equal; an ASCII entry with no terminal NUL keeps its count; a big-endian (MM) source; out-of-line boundary values (exactly 4 bytes inline, 5 bytes out of line); insertion cases (no Orientation in IFD0, no Pixel dims in Exif, no Exif IFD at all); a damaged child offset dropped alone; a damaged IFD0 raising so sanitise returns None; the SubIFDs drop. Base failures on main 5a1538a recorded in the ledger with their assertion text.

Unchanged: files owned / NOT owned, Locks, Verification (full parallel leg + impacted serial nodes by id, no full serial re-run, per the owner 18:47Z), Reviewer A between turns, Reviewer B at your seat, Done. Ledger round 0: record this ruling as the disposition (STOP resolved, Q1 = (b)), then turn 2 = RED tests first, then the rewriter. Commit the ledger as you said. Quote this ruling in turn 2's dispatch block.

Your (3) stands: any further widening comes to me. No register row from this ruling; the Limits (BigTIFF, MakerNote internal offsets, SubIFDs drop) go in the report.
