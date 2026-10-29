# WP4.5 - EXIF byte fidelity through the photo writer

Implementation and light verification are complete. Reviewer A, Reviewer B and
the orchestrator's final gate remain pending. Product base: main `5a1538a`.
This report contains synthetic evidence only; no real photo metadata is included.

## Root cause and mechanism decision

The previous writer decoded EXIF values with Pillow and serialized those Python
values again. Pillow decodes ASCII-typed entries as latin-1, then writes strings
with ASCII replacement, changing non-ASCII bytes. Its fresh directory objects
also guess types rather than retaining every source TIFF type. Changing a
decoded string to bytes therefore changes some untyped ASCII entries into BYTE
entries instead of preserving their type and count.

Round 0 confirmed that source type pins do not travel through either the root
or nested directory reconstruction in `Image.Exif.tobytes()`. The cell stopped
under the original Q1(a) ruling. CHARC `c64900357c363330` re-ruled Q1 = (b), a
byte-level IFD rewrite, on two grounds: those type pins are discarded, and even
direct typed Pillow serialization re-encodes values. In particular, rational
fractions are reduced and ASCII values without terminal NULs acquire one.
Numerical or decoded-text equality cannot prove the required byte fidelity.

## Implementation

`src/clearwater/io/photo/exif.py` now parses classic TIFF headers and entry
tables using stdlib `struct`. It carries IFD0, Exif, GPS and the Exif IFD's
Interop directory. Every retained entry keeps its tag, TIFF type, count and raw
value bytes. The output preserves source byte order and the relative order of
kept entries. Out-of-line values are copied with word padding, and pointers are
rewritten to the new child/value offsets. The next-IFD pointer is zero, dropping
IFD1 and its thumbnail. Inserted entries precede the first greater tag, so a
sorted source stays sorted.

The D63 replacements are Orientation SHORT/count 1/value 1, Software ASCII
Clearwater with its terminating NUL, and the written pixel dimensions. Existing
SHORT dimensions remain SHORT when the new value fits; otherwise they become
LONG. Existing LONG dimensions remain LONG, and absent dimensions are inserted
as LONG. An absent Exif IFD is created. A source without EXIF produces only the
four D63 fields and their structural Exif pointer.

Counts, table extents, value lengths and offsets are checked before the
corresponding reads or value copies. Damaged child directories are removed with
a warning while their siblings and parent fields survive. A damaged root/header
raises; the existing `sanitise()` path drops that block with a warning.

`from_tiff()` uses the same raw parser and serializer on the original TIFF
bytes, dropping TIFF structure/profile/XMP/IPTC/Photoshop entries. It returns
None when no metadata survives. It extracts source metadata; D63 replacements
occur in the subsequent writer call to `edit()`. Pillow remains the decoded
read interface for `load`, `orientation_of`, `describe` and `has_thumbnail`.
The photo writer's bare-byte hand-off already worked and is unchanged.

## Files owned and granted scope

- `src/clearwater/io/photo/exif.py`: raw rewrite, TIFF extraction and documentation.
- `tests/test_io_photo_exif_bytes.py`: new independent byte-level regression tests.
- `docs/proofs/wp4.5-ledger.md`: decisions, per-case baseline outcomes, checks and stops.
- `docs/reports/wp4.5-exif-bytes.md`: this report.
- GRANT: `tests/test_io_photo_r1.py`, only
  `test_a_tiff_with_an_unreadable_gps_ifd_keeps_its_other_fields`, CHARC
  `1d9f88948f4350c4`, amended by `8dd13704a85f2237`.

The granted test originally injected a failure into Pillow's `get_ifd`, which
the authorized rewrite no longer calls. The initial grant attempted a direct
GPS extratag; installed tifffile filters that tag. Under the amendment, the test
writes a placeholder LONG/count-1 entry beside Make, locates it through the
TIFF header and IFD0 table, and patches only its tag ID to the GPS pointer tag.
Its offset is past EOF. A presence assertion checks the actual GPS entry,
type, count and invalid offset before reading the file. The original three
assertions remain verbatim. The monkeypatch fixture/shim are removed; no imports
were added or removed (`struct` was already imported).

No other existing test, interface, dependency, lock file, writer, PNG module,
reader, fixture, local configuration, register or harness file changed. No new
dependency or OS-specific product code was introduced. All new test data is
synthetic; test writes use `tmp_path`. No footage was read or written by the cell.

## Tests and baseline results

The new test file has 112 cases and uses its own `struct` fixture builder and
entry parser. It compares parsed tag/type/count/value bytes, following pointers
structurally rather than comparing whole blobs or relocated offsets. On the
unchanged base implementation it produced **78 failures and 34 passing
controls**. The ledger records each case and its actual failure line.

| Coverage | Base outcome |
| --- | --- |
| Non-7-bit LensModel, latin-1 Artist, UTF-8 description, nested GPS/Interop ASCII | Raw-entry equality failures |
| ASCII without a terminal NUL, inline four-byte and out-of-line five-byte values | Count/value equality failures |
| NUL-filled Make/Model and plain ASCII controls | Passed |
| Source types in IFD0, Exif, GPS and Interop; unreduced RATIONAL and negative SRATIONAL | Type/value equality failures for affected cases; unchanged encodings passed as controls |
| MakerNote UNDEFINED and synthetic GPS entries | Raw-entry equality failures |
| Little- and big-endian source blocks | Exercised throughout the parameterized cases |
| D63 replacements, SHORT retention/promotion, missing Orientation/dimensions/Exif IFD, None input | Existing behavior controls plus failures where the base guessed SHORT instead of required LONG |
| Kept entry order, unsupported SubIFDs/type-13 removal | Ordering/drop failures |
| Malformed child offsets/tables/payloads and malformed root/value bounds | Missing warnings, retained dangling entries or missing exceptions; garbage-header control passed |
| Synthetic PNG/JPEG source -> write_photo -> PNG read | LensModel raw-entry equality failures |
| Synthetic TIFF extraction and subsequent edit | Artist raw-entry equality failure |
| BigTIFF and TIFF without metadata | Missing BigTIFF warning; empty-metadata control passed |

After the rewrite all 112 new cases pass. The final amended GPS test was also
run against main `5a1538a`'s `exif.py` in an ignored scratch module. Its presence
assertion passed, then the original warning assertion failed because the base
EXIF implementation did not report the invalid child. With the rewrite the
same final test passes.

The scratch-base test imports were redirected only inside that pytest process;
the worktree product was never replaced. The earlier direct-GPS-extratag form
failed on both base and current code because tifffile omitted the injection;
those failures are historical, superseded by the amended final form.

## Verification

Cell light run, turn 4: **789 passed, 5 deselected**, exit 0. Targets:
`tests/test_io_photo_*.py`, `tests/test_photo_check.py`,
`tests/test_wp41_photo_path.py`, `tests/test_jobs_export_photo.py`. Every target
used `-m "not gpu and not footage and not gui and not slow and not fullclip"`,
`PYTHONPATH=scripts`, `--basetemp=work/wp4.5/tmp`, `-p sandbox_mkdir_shim` and
`-p no:cacheprovider`. All output was routed under `work/wp4.5/`.

- Targeted ruff check: exit 0, All checks passed.
- Mypy: exit 0, no issues in 141 source files.
- Cell byte/scope check: exit 0; all changed files ASCII/LF-only, original three
  assertions verbatim, no AST change outside the granted test. The granted test
  file's read-only formatting diff reports it already formatted.
- Dispatcher reported changed-file format/ruff and LF/ASCII clean after turn 2.
  Final candidate formatting and blob checks remain dispatcher gate checks.
- Reviewer A R1: pending; no convergence claim.
- Reviewer B: pending.
- Full parallel leg: @@PAR@@
- Impacted serial nodes: @@SER@@
- Real-photo round trip: @@FOOT@@

The owner directed that a full serial re-run is unnecessary. The orchestrator's
gate is the full parallel leg plus the named impacted serial nodes and real-photo
round trip, after the independent reviews. The cell ran no footage/GPU/GUI/
slow/fullclip leg and recorded no product performance or memory claim.

## Verification loop and limits

The raw-fidelity problem was confirmed independently by source inspection,
synthetic probes and the RED baseline, then fixed and exercised by the new
tests. The obsolete Pillow-specific injection was confirmed by an existing-test
failure and corrected only after the explicit test-line grant. The direct GPS
extratag failure was reproduced on both product versions and traced to
tifffile's filtered-tag set; the amended real-pointer test resolves it. The final
authorized light run and static checks found no further failure. Full acceptance
depends on the pending reviews and gate figures above.

Named limits:

- BigTIFF magic 43 is unsupported for EXIF carry; it is rejected with a warning
  through `from_tiff`/`sanitise` rather than rewritten.
- MakerNote value bytes are preserved. MakerNote internal offsets are not
  repaired or validated; their validity after relocation is a pre-existing limit.
- SubIFDs, type-13 entries and IFD pointers outside the carried tree are dropped
  with warnings because the structures they address are not carried.
- Classic TIFF field types 1-12 are supported. An unknown field type rejects
  the root block or drops the affected child directory, with the corresponding
  warning at the public extraction/sanitisation boundary.
- Entry offsets and word padding can change; IFD1 is deliberately absent.
  The fidelity guarantee concerns retained entry types, counts and value bytes.

No further scope expansion is requested. No register row is required by the
rulings. The grant line above must also accompany the completion/accept record.
