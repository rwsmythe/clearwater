# WP4.5 - EXIF byte fidelity through the photo writer

Implementation and Reviewer A R4 cleanup are complete; light verification is
recorded below. Reviewer A converged at R4. Reviewer B and the orchestrator's
final gate remain pending. Product base: main `5a1538a`.
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

Each carried pointer tag is followed only at its FIRST occurrence in its
parent's table order: 34665 and 34853 in IFD0, 40965 in Exif. Every later
occurrence is dropped with one IFD/tag warning, even if the first pointer is
unreadable. Pointers are structure; other non-D63 duplicate field values still
pass through. At most four source tables are parsed and written: IFD0, Exif,
GPS and Interop. No child cache remains. Same-offset siblings are parsed
separately per label, so Interop stays under Exif and dimension edits affect
only the Exif copy. Ancestor offsets remain cycles and drop only that child.
Written entry count is bounded by `4 * len(source block) / 12 + 5`, including
at most five D63 insertions (the turn-3 erratum to CHARC `85978ce0cd76c577`).
This fixes both R2 F-A's shared-child and R3 F-1's overlapping-child entry
multiplication. F7 shared values is the only amplification Limit below.

The D63 replacements are Orientation SHORT/count 1/value 1, Software ASCII
Clearwater with its terminating NUL, and the written pixel dimensions. Existing
SHORT dimensions remain SHORT when the new value fits; otherwise they become
LONG. Existing LONG dimensions remain LONG, and absent dimensions are inserted
as LONG. Each D63 tag's first occurrence is replaced in its original position;
later duplicates are dropped with one IFD/tag warning per removed entry. Other
non-pointer duplicates are retained. The single carried Exif child receives
the dimension edits. An absent Exif IFD is created. A source without EXIF produces only the
four D63 fields and their structural Exif pointer.

Counts, table extents, value lengths and offsets are checked before the
corresponding reads or value copies. An entry with an unknown type or an invalid
value extent/offset is dropped alone, with one warning naming the IFD and tag
ID, never the value bytes. Sibling entries survive in every directory. A cut
entry array retains every whole entry that fits, in IFD0 or a child, with one
warning naming the IFD and declared/kept counts. A complete table needs only
its two-byte count and 12 bytes per entry; a missing next pointer is accepted
as zero. Invalid child offsets or cycles drop that child alone with a warning;
empty children are pruned recursively. Header faults or an IFD0 offset past
the block raise; `sanitise()` drops the block and `from_tiff()` returns None
with a warning. Cycles drop only the child; IFD0 cannot form a cycle. Output
directory entry-count overflow is the further whole-block case noted below.
One faulty IFD0 value does not discard the whole block.
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
  remediated under CHARC `72fc47f6a4ecfd91`; its child-cache mechanism is
  superseded by the R3 guard.
- Reviewer A R3: 1 major, 1 minor (out of envelope) and 2 advisory findings;
  adjudicated under CHARC `85978ce0cd76c577` and the turn-3 bound erratum;
  guard remediation green.
- Reviewer A R4: NO_NEW_CRITICAL_MAJOR, three advisories; documentation-only
  cleanup complete. First round with zero new critical or major, so Reviewer A
  converged at R4.
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
| F3, major | Confirmed duplicate D63 entries survived. Replace the first occurrence and warn/drop later D63 copies. Non-pointer duplicates still pass through; the pointer-tag precision is narrowed by the R3 guard below. |
| F4, minor | Confirmed empty Interop pointers survived. Prune empty child trees recursively in both routes. |
| F5, minor | Update public/private docstrings and this report to distinguish entry faults from table faults and remove stale Pillow writer claims. |
| F6, advisory | Add the missing regressions and require ValueError in the root-raise test. Reviewer layout/alignment/overlap fuzz found no defect. |
| F7, advisory, out of envelope | Accepted named shared-value amplification limit below; no product change or register row, per CHARC. |
| F8, advisory, commissioned fix | Confirmed overflow with RED Exif/GPS/Interop SHORT pointers in both byte orders. Keep fitting SHORT offsets; promote overflowing ones to LONG. |
| F9, advisory | Presence assertion and comment are explicitly granted by `8dd13704a85f2237`; record with original grant in the owned-files line and completion record. No further existing-test edit. |

R1 checks at the cell: new file **203 passed**, exit 0; broader light run
**880 passed, 5 deselected**, exit 0; targeted ruff check exit 0; mypy exit 0,
no issues in 141 source files. These historical checks precede R2/R3. R1's reviewer
also supplied zero mismatches over 3,000 valid layout/fidelity probes and no
unexpected exception/hang over 20,000 mutated/truncated blocks; these are
reviewer checks, not a substitute for the gate.

## Reviewer A R2

Claude opus/high, read-only, returned `NEW_CRITICAL_MAJOR_FOUND` on `3020648`.
Fresh Codex seat 2 remediated under CHARC `72fc47f6a4ecfd91`:

| Finding | Disposition and remediation |
| --- | --- |
| F-A, major | FIXED by the R3 guard below, together with R3 F-1. R2's exact-offset cache was incomplete: distinct overlapping offsets still multiplied child entries. The superseded R2 candidate had 454 physical entries for A=B=C=150; pre-R2 had 3,397,952. The current guard drops duplicate pointers and has 156 entries. No timing bound. Distinct from R1 F7 shared values. |
| F-B, minor | FIXED. Accept complete arrays without a next-IFD pointer in IFD0 and GPS; output next pointers remain zero. |
| F-C, advisory, ruled amendment | FIXED under the new rule: retain all whole entries from a cut array, warn once with the IFD and declared/kept counts. Header faults or an IFD0 offset past the block raise; child offset/cycle faults drop only that child. Entry-count overflow is the further whole-block Limit named at R4. Supersedes whole-table rejection wording and WP4.5 test controls. |
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

## Reviewer A R3

Claude opus/high, read-only on `c7c7360`, returned
`NEW_CRITICAL_MAJOR_FOUND`: one new major, one out-of-envelope minor, and two
advisories. CHARC `85978ce0cd76c577` replaced R2's cache with the DESIGN GUARD.
The cell's pre-build STOP proved that the exact entry bound omitted mandatory
D63 insertions: a valid 14-byte empty IFD0 needs five output entries. The
orchestrator's turn-3 erratum, reported to CHARC, allows those five insertions;
all other guard requirements stand. This is an arithmetic erratum, not a
change to the D63 contract or the pointer guard.

| Finding | Disposition and verification |
| --- | --- |
| F-1, major, in envelope | FIXED with R2 F-A by following each carried pointer tag only once per parent and dropping each later occurrence with one warning. Remove both child caches and the shared-child dimension deduplication set. P=200/N=400 overlapping-offset fixtures for Exif and GPS, both routes/orders, require exactly one pointer/child for that label, at most four total IFDs, and `12 * output entries <= 4 * source bytes + 60`. |
| F-2, minor, out of envelope | Resolved by the same commissioned guard. GPS-before-Exif same-offset fixtures preserve Interop only under Exif and dimensions only in Exif. The sole unsupported Interop warning correctly names GPS and tag 40965. No label-sharing cache remains. |
| F-3, advisory | Report F-A and F-1 as FIXED by the guard and state the erratum's entry-count bound. F7 shared values, reproduced in the base, remains the only amplification Limit. |
| F-4, advisory | No change, as ruled. from_tiff continues warning on SubIFDs and unsupported IFD-valued entries. |

RED before product changes, against the unchanged `c7c7360` product:
**30 failed, 224 deselected**, exit 1. The ledger records each actual
failure. Six cases amend prior tests in the owned file: R1's two distinct-child
duplicate Exif cases now keep only the first child with its D63 dimensions;
R2's four A=B=C=150 cases now drop duplicates and retain 156 physical entries,
including all 150 non-pointer Interop values. The 24 new cases cover eight
overlapping-offset, four same-offset sibling and twelve pointer-tag cases
(first occurrence, source type/count, one warning per later entry). Tests
compare entry counts and structure, with no wall-clock bound.

GREEN: **254 passed, 1 warning in 0.88 s**, exit 0. The authorized combined
light run passed **931 tests, 5 deselected, 133 warnings in 15.46 s**, exit 0.
Targeted ruff check: exit 0, All checks passed. Strict mypy: exit 0, no issues
in 141 source files. Ruff formatted the owned test file; exif.py was already
formatted. All pytest commands use the same sandbox shim, work temp root and
five-marker exclusion documented above. Logs/JUnit: `work/wp4.5/r3-{red,green,light}.{log,xml}`;
static/format logs: `r3-ruff.log`, `r3-mypy.log`, `r3-format.log`. The existing
synthetic bad-value fixture still produces one separate Pillow UserWarning.
The final byte/scope audit passes: exactly four owned files, ASCII/LF-only,
final newlines and no trailing whitespace; `git diff --check` clean. Seven
additional in-memory synthetic probes confirm ancestor-cycle isolation,
no fallback after an unreadable first pointer for all three tags, and the
corrected +5 bound on 14-byte and 10-byte empty source tables. Evidence:
`work/wp4.5/r3-final-audit.log`.

The source-offset parse cache, identity write cache and shared-dimension set
are removed. Parent-local first-tag tracking precedes pointer validation, so
an unreadable first occurrence does not allow a later pointer to be followed.
There is one Exif/GPS slot from IFD0 and one Interop slot from Exif; GPS and
Interop cannot recurse, so at most four tables are parsed. Offsets equal to
ancestors still drop the cyclic child; equal sibling offsets get fresh lists
under their own labels. Entry value relocation/type/count/order behavior and
the F-C cut-array rule are unchanged. All new warnings name IFD/tag only.
R3's candidate proceeded to R4; that round's result is recorded below.

## Reviewer A R4

Claude opus/high, read-only on `2923402`, returned
`NO_NEW_CRITICAL_MAJOR`: the first round with zero new critical or major
findings, so Reviewer A converged at R4. The three advisories require only
this report and the edit docstring cleanup; no behavior or test change.

- A-1, out of envelope: clarify the repeated-same-tag variation of F7 while
  retaining its worst-case comparison to the base.
- A-2, out of envelope: name the 65,535-entry IFD0 overflow Limit; no code fix.
- A-3, in envelope: remove the impossible root-cycle raise claim and distinguish
  header/IFD0-offset rejection from child-cycle isolation and entry overflow.

The reviewer checked 3,000 valid blocks / 85,545 entries, with no edit-route
fidelity mismatch; the twelve from_tiff differences were ruled structure-tag
drops. Its 20,000 mutated/truncated inputs produced 54,865 valid outputs,
with at most four tables and the corrected +5 bound. Layout, ordinary-photo
views, D63, grant and scope checks held. These are supplied reviewer checks.

Dispatcher-seat evidence on `2923402`: ruff format/check and LF/ASCII clean;
the real-photo round-trip node passed **1 test in 263.93 s**. This precedes the
documentation-only cleanup and is not the final orchestrator gate. Reviewer B
and the final full parallel + impacted serial gate remain pending.

Cleanup checks at the cell: `tests/test_io_photo_exif_bytes.py` plus
`tests/test_io_photo_r1.py`, **288 passed, 1 warning in 2.27 s**, exit 0, with
the sandbox shim, work temp root and the same five-marker exclusion. Targeted
ruff check: exit 0, All checks passed. Strict mypy: exit 0, no issues in 141
source files. No test changed. A read-only AST comparison against `2923402`,
after stripping docstrings, confirms identical executable code. Final scope
and byte checks pass: exactly report/ledger/exif.py, ASCII/LF-only, final
newlines, no trailing whitespace, clean `git diff --check`. Evidence:
`work/wp4.5/r4-light.log/xml`, `r4-ruff.log`, `r4-mypy.log`,
`r4-final-audit.log`. The one Pillow warning is the previously recorded
synthetic bad-value fixture. No behavior change or additional review round.

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
green. F-D is an existing-behavior control, not a newly implemented fix.
R3 independently confirmed the distinct-overlap and same-offset-label
defects RED, then removed the cache under the guard and checked every new and
amended case green. The final R3 light run and static checks found no further
failure. Full acceptance depends on the pending reviews and gate figures above.

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
  count warning; header faults or an IFD0 offset past the block discard the
  block, while child offset/cycle faults discard only that child. IFD0 cannot
  form a cycle. Empty children are omitted.
- An IFD0 already at 65,535 entries cannot take required D63 insertions: edit
  raises and sanitise drops the block; this is out of envelope and the base
  failed as well.
- Hostile inputs can make many entries share one large source value. Relocation
  copies each value separately and can substantially increase output size and
  memory use. Repeated SAME-tag entries sharing a value amplify where the base
  collapsed them into one key; the worst-case order matches the base, reachable
  with distinct tags. Reviewer R1 reproduced that distinct-tag behavior in the
  base; CHARC F7 accepts it as an out-of-envelope limit without remediation or
  a register row.
- Entry offsets and word padding can change; IFD1 is deliberately absent.
  The fidelity guarantee concerns retained entry types, counts and value bytes.

No further scope expansion is requested. No register row is required by the
rulings. The grant line above must also accompany the completion/accept record.
