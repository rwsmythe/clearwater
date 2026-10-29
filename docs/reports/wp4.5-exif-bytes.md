# WP4.5 - EXIF byte fidelity through the photo writer

Implementation and R1 remediation are complete; light verification is recorded
below. Reviewer A R2, Reviewer B and the orchestrator's final gate remain
pending. Product base: main `5a1538a`.
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
rewritten to the new child/value offsets. Carried pointers retain their source
types 4 (LONG) or 13 (IFD). Type 3 (SHORT) remains SHORT unless the relocated
offset exceeds 65535, when it promotes to LONG. The next-IFD pointer is zero, dropping
IFD1 and its thumbnail. Inserted entries precede the first greater tag, so a
sorted source stays sorted.

The D63 replacements are Orientation SHORT/count 1/value 1, Software ASCII
Clearwater with its terminating NUL, and the written pixel dimensions. Existing
SHORT dimensions remain SHORT when the new value fits; otherwise they become
LONG. Existing LONG dimensions remain LONG, and absent dimensions are inserted
as LONG. Each D63 tag's first occurrence is replaced in its original position;
later duplicates are dropped with one IFD/tag warning per removed entry. Other
duplicates, including duplicate Exif pointers, are retained. Every carried Exif
child receives the dimension edits. An absent Exif IFD is created. A source without EXIF produces only the
four D63 fields and their structural Exif pointer.

Counts, table extents, value lengths and offsets are checked before the
corresponding reads or value copies. An entry with an unknown type or an invalid
value extent/offset is dropped alone, with one warning naming the IFD and tag
ID, never the value bytes. Sibling entries survive in every directory. A faulty
child table is removed with its pointer and a warning; empty children are
pruned recursively in both routes. A damaged header or root IFD0 table raises;
`sanitise()` drops that block and `from_tiff()` returns None with a warning.
One faulty IFD0 value does not discard the whole block.

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
  The fourth presence assertion and revised comment are explicitly covered by
  that amendment (R1 F9); the completion/accept record carries the same note.

The granted test originally injected a failure into Pillow's `get_ifd`, which
the authorized rewrite no longer calls. The initial grant attempted a direct
GPS extratag; installed tifffile filters that tag. Under the amendment, the test
writes a placeholder LONG/count-1 entry beside Make, locates it through the
TIFF header and IFD0 table, and patches only its tag ID to the GPS pointer tag.
Its offset is past EOF. A presence assertion checks the actual GPS entry,
type, count and invalid offset before reading the file. The original three
assertions remain verbatim. Both the fourth presence assertion and revised
comment are explicitly within amendment `8dd13704a85f2237` (R1 finding F9);
the completion/accept record must carry that note. The monkeypatch fixture/shim are removed; no imports
were added or removed (`struct` was already imported).

No other existing test, interface, dependency, lock file, writer, PNG module,
reader, fixture, local configuration, register or harness file changed. No new
dependency or OS-specific product code was introduced. All new test data is
synthetic; test writes use `tmp_path`. No footage was read or written by the cell.

## Tests and baseline results

The original new test file had 112 cases and uses its own `struct` fixture builder and
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

After the initial rewrite all 112 cases passed. R1 now has 203 cases: 94 new
cases plus the remaining original cases, with three whole-child payload-damage
cases superseded by entry-isolation tests under the amended rule. Its pre-fix
run on `5a57d9f` had 84 failures and 119 passing controls; after remediation all
203 pass. The ledger records every R1 failure and changed control. The root
exception tests now require ValueError. The final amended GPS test was also
run against main `5a1538a`'s `exif.py` in an ignored scratch module. Its presence
assertion passed, then the original warning assertion failed because the base
EXIF implementation did not report the invalid child. With the rewrite the
same final test passes.

The scratch-base test imports were redirected only inside that pytest process;
the worktree product was never replaced. The earlier direct-GPS-extratag form
failed on both base and current code because tifffile omitted the injection;
those failures are historical, superseded by the amended final form.

## Verification

Cell light run, turn 4 before R1: **789 passed, 5 deselected**, exit 0. R1 light
results follow in the R1 section. Targets:
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
- Reviewer A R1: 3 major, 2 minor and 4 advisory findings; adjudicated and
  remediated under CHARC `980818fc01eb77ea`; R2 pending, no convergence claim.
- Reviewer B: pending.
- Full parallel leg: @@PAR@@
- Impacted serial nodes: @@SER@@
- Real-photo round trip: @@FOOT@@

Earlier dispatcher-seat evidence on `5a57d9f`: the real-photo round-trip node
passed over all the owner's Phone photos, **1 passed in 328.40 s**. This is
pre-remediation evidence supplied by the dispatcher and does not replace the
final candidate gate or the placeholder above.

The owner directed that a full serial re-run is unnecessary. The orchestrator's
gate is the full parallel leg plus the named impacted serial nodes and real-photo
round trip, after the independent reviews. The cell ran no footage/GPU/GUI/
slow/fullclip leg and recorded no product performance or memory claim.

## Reviewer A R1

Claude opus/high, read-only, returned `NEW_CRITICAL_MAJOR_FOUND` on `5a57d9f`.
CHARC `980818fc01eb77ea` amended the damage rule and dispositioned all findings:

| Finding | Disposition and remediation |
| --- | --- |
| F1, major | Confirmed with RED entry-damage cases across all four IFDs and both routes. Drop only faulty entries; preserve siblings. Header/root-table faults still raise, child-table faults still isolate the child. |
| F2, major | Confirmed with carried type-13 pointers in both byte orders/routes. Carry type 13 at the supported Exif/GPS/Interop pointer positions and retain its source type. Other type-13 entries remain dropped. |
| F3, major | Confirmed duplicate D63 entries survived. Replace the first occurrence and warn/drop later D63 copies. Retain all other duplicates; duplicate Exif children each receive dimension edits. |
| F4, minor | Confirmed empty Interop pointers survived. Prune empty child trees recursively in both routes. |
| F5, minor | Update public/private docstrings and this report to distinguish entry faults from table faults and remove stale Pillow writer claims. |
| F6, advisory | Add the missing regressions and require ValueError in the root-raise test. Reviewer layout/alignment/overlap fuzz found no defect. |
| F7, advisory, out of envelope | Accepted named shared-value amplification limit below; no product change or register row, per CHARC. |
| F8, advisory, commissioned fix | Confirmed overflow with RED Exif/GPS/Interop SHORT pointers in both byte orders. Keep fitting SHORT offsets; promote overflowing ones to LONG. |
| F9, advisory | Presence assertion and comment are explicitly granted by `8dd13704a85f2237`; record with original grant in the owned-files line and completion record. No further existing-test edit. |

R1 checks at the cell: new file **203 passed**, exit 0; broader light run
**880 passed, 5 deselected**, exit 0; targeted ruff check exit 0; mypy exit 0,
no issues in 141 source files. R2 is required for convergence. R1's reviewer
also supplied zero mismatches over 3,000 valid layout/fidelity probes and no
unexpected exception/hang over 20,000 mutated/truncated blocks; these are
reviewer checks, not a substitute for the gate.

## Verification loop and limits

The raw-fidelity problem was confirmed independently by source inspection,
synthetic probes and the RED baseline, then fixed and exercised by the new
tests. The obsolete Pillow-specific injection was confirmed by an existing-test
failure and corrected only after the explicit test-line grant. The direct GPS
extratag failure was reproduced on both product versions and traced to
tifffile's filtered-tag set; the amended real-pointer test resolves it. R1's
additional entry-damage, duplicate, pointer-type, empty-child and SHORT
relocation regressions were confirmed RED before fixes and green afterward.
The final R1 light run and static checks found no further failure. Full acceptance
depends on the pending reviews and gate figures above.

Named limits:

- BigTIFF magic 43 is unsupported for EXIF carry; it is rejected with a warning
  through `from_tiff`/`sanitise` rather than rewritten.
- MakerNote value bytes are preserved. MakerNote internal offsets are not
  repaired or validated; their validity after relocation is a pre-existing limit.
- SubIFDs, type-13 entries outside carried pointer positions, and other IFD
  pointers outside the carried tree are dropped
  with warnings because the structures they address are not carried.
- Classic TIFF field types 1-12 are supported; type 13 is supported at carried
  pointer positions. Unknown types or invalid value extents/offsets drop only
  that entry with an IFD/tag warning. Header/root-table faults discard the block;
  child-table faults discard only that child. Empty children are omitted.
- Hostile inputs can make many entries share one large source value. Relocation
  copies each value separately and can substantially increase output size and
  memory use. Reviewer R1 reproduced the same behavior in the base; CHARC F7
  accepts it as an out-of-envelope limit without remediation or a register row.
- Entry offsets and word padding can change; IFD1 is deliberately absent.
  The fidelity guarantee concerns retained entry types, counts and value bytes.

No further scope expansion is requested. No register row is required by the
rulings. The grant line above must also accompany the completion/accept record.
