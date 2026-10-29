# WP4.5 - EXIF byte fidelity through the photo writer

Implementation and R2 remediation are complete; light verification is recorded
below. Reviewer A R3, Reviewer B and the orchestrator's final gate remain
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

Each child IFD is parsed once by source offset and written once by shared
directory identity. All pointers to that child use its single new offset;
an ancestor offset is a cycle, while repeated sibling offsets share the child.
The dimension edit also runs once per shared Exif child. This fixes R2 F-A's
shared-child entry multiplication; the separate shared-value limit below remains.

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
ID, never the value bytes. Sibling entries survive in every directory. A cut
entry array retains every whole entry that fits, in IFD0 or a child, with one
warning naming the IFD and declared/kept counts. A complete table needs only
its two-byte count and 12 bytes per entry; a missing next pointer is accepted
as zero. Invalid child offsets or cycles drop that child alone with a warning;
empty children are pruned recursively. Header faults, invalid IFD0 offsets
and root cycles raise; `sanitise()` drops the block and `from_tiff()` returns
None with a warning. One faulty IFD0 value does not discard the whole block.
The sanitise trial edit suppresses entry warnings using a private, default-loud
keyword; the writer's actual edit warns once per dropped entry.

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
  remediated under CHARC `980818fc01eb77ea`.
- Reviewer A R2: 1 major, 1 minor and 4 advisory findings; adjudicated and
  remediated under CHARC `72fc47f6a4ecfd91`; R3 pending, no convergence claim.
- Reviewer B: pending.
- Full parallel leg: @@PAR@@
- Impacted serial nodes: @@SER@@
- Real-photo round trip: @@FOOT@@

Earlier dispatcher-seat evidence on `5a57d9f`: the real-photo round-trip node
passed over all the owner's Phone photos, **1 passed in 328.40 s**. This is
pre-remediation evidence supplied by the dispatcher and does not replace the
final candidate gate or the placeholder above.

Dispatcher-seat evidence on `3020648`, supplied to seat 2: the same real-photo
round-trip node passed over all 73 Phone photos, **1 passed in 268.01 s**.
This also predates R2 remediation and is not the final candidate gate.

The owner directed that a full serial re-run is unnecessary. The orchestrator's
gate is the full parallel leg plus the named impacted serial nodes and real-photo
round trip, after the independent reviews. The cell ran no footage/GPU/GUI/
slow/fullclip leg and recorded no product performance or memory claim.

## Reviewer A R1

Claude opus/high, read-only, returned `NEW_CRITICAL_MAJOR_FOUND` on `5a57d9f`.
CHARC `980818fc01eb77ea` amended the damage rule and dispositioned all findings:

| Finding | Disposition and remediation |
| --- | --- |
| F1, major | Confirmed with RED entry-damage cases across all four IFDs and both routes. Drop only faulty entries; preserve siblings. The current array/offset damage rule is the R2 F-C rule below. |
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

## Reviewer A R2

Claude opus/high, read-only, returned `NEW_CRITICAL_MAJOR_FOUND` on `3020648`.
Fresh Codex seat 2 remediated under CHARC `72fc47f6a4ecfd91`:

| Finding | Disposition and remediation |
| --- | --- |
| F-A, major | FIXED. Cache parsed children by source offset and written directories by identity, retaining duplicate pointers, source pointer types/counts and the ancestor cycle check. A=B=C=150 shared-pointer fixtures now have exactly 454 physical entries in three IFDs in both byte orders/routes; pre-fix output had 3,397,952 entries. No timing bound. This is distinct from R1 F7 shared values. |
| F-B, minor | FIXED. Accept complete arrays without a next-IFD pointer in IFD0 and GPS; output next pointers remain zero. |
| F-C, advisory, ruled amendment | FIXED under the new rule: retain all whole entries from a cut array, warn once with the IFD and declared/kept counts. Root header/offset/cycle faults raise; child offset/cycle faults drop only that child. Supersedes whole-table rejection wording and WP4.5 test controls. |
| F-D, advisory, ruled Limit | Existing type-9 pointer drop retained with an IFD/tag warning; four passing regression controls cover both routes/orders. No pointer-type widening. |
| F-E, advisory | Report F-A as fixed separately from the shared-value Limit and replace obsolete damage wording. |
| F-F, advisory | FIXED. Quiet sanitise trial edit, default-loud writer edit. Synthetic read_photo + write_photo tests require one rewriter warning per bad-value, duplicate-D63 or unsupported-pointer entry. |

R2 adds 27 cases. On unchanged `3020648`, **23 failed, 4 passed, 203
deselected**, exit 1, before any product fix. The ledger records each actual
failure: shared-child multiplication, missing-next-pointer table rejection,
cut-array field loss, and duplicate read/write warnings. The four SLONG cases
already pass on that head and serve as controls. After remediation and the
superseded damage controls' update, **230 passed**, exit 0. The entry-count
test's secondary assertion compares pointer types/counts/order, allowing the
intentional D63 Software count change.

Authorized light run on the final product/test changes: **907 passed, 5
deselected, 133 warnings in 15.81 s**, exit 0, using the sandbox form and
targets listed above. Targeted ruff check: exit 0, All checks passed. Mypy:
exit 0, no issues in 141 source files. Ruff formatting applied to the two
changed Python files; the dispatcher owns the final format check. The new
bad-value read/write fixture triggers one Pillow `Truncated File Read`
UserWarning while decoding its synthetic metadata; it is separate from the
single product logger warning asserted by the test. No cell footage run.
Logs and JUnit files: `work/wp4.5/r2-{red,green,light}.{log,xml}`,
`r2-ruff.log`, `r2-mypy.log`, `r2-format.log`.

## Verification loop and limits

The raw-fidelity problem was confirmed independently by source inspection,
synthetic probes and the RED baseline, then fixed and exercised by the new
tests. The obsolete Pillow-specific injection was confirmed by an existing-test
failure and corrected only after the explicit test-line grant. The direct GPS
extratag failure was reproduced on both product versions and traced to
tifffile's filtered-tag set; the amended real-pointer test resolves it. R1's
additional entry-damage, duplicate, pointer-type, empty-child and SHORT
relocation regressions were confirmed RED before fixes and green afterward.
R2's shared-child, missing-next-pointer, cut-array and warning-count defects
were independently confirmed by the code paths and RED tests, fixed and checked
green. F-D is an existing-behavior control, not a newly implemented fix. The
final R2 light run and static checks found no further failure. Full acceptance
depends on the pending reviews and gate figures above.

Named limits:

- BigTIFF magic 43 is unsupported for EXIF carry; it is rejected with a warning
  through `from_tiff`/`sanitise` rather than rewritten.
- MakerNote value bytes are preserved. MakerNote internal offsets are not
  repaired or validated; their validity after relocation is a pre-existing limit.
- SubIFDs, type-13 entries outside carried pointer positions, and other IFD
  pointers outside the carried tree are dropped
  with warnings because the structures they address are not carried.
- Carried pointers of types other than 3, 4 or 13 (including SLONG/9) are dropped
  with a warning: no known writer emits one; the base followed any type.
- Classic TIFF field types 1-12 are supported; type 13 is supported at carried
  pointer positions. Unknown types or invalid value extents/offsets drop only
  that entry with an IFD/tag warning. Cut arrays retain whole entries with one
  count warning; header/root-offset/cycle faults discard the block, child
  offset/cycle faults discard only that child. Empty children are omitted.
- Hostile inputs can make many entries share one large source value. Relocation
  copies each value separately and can substantially increase output size and
  memory use. Reviewer R1 reproduced the same behavior in the base; CHARC F7
  accepts it as an out-of-envelope limit without remediation or a register row.
- Entry offsets and word padding can change; IFD1 is deliberately absent.
  The fidelity guarantee concerns retained entry types, counts and value bytes.

No further scope expansion is requested. No register row is required by the
rulings. The grant line above must also accompany the completion/accept record.
