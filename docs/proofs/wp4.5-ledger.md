# WP4.5 - EXIF byte fidelity: cumulative ledger

## Reviewer A Round 4 - CONVERGED, bounded documentation cleanup

Reviewer: Claude opus/high, read-only on `2923402`; findings supplied in the
seat-2 turn-4 dispatch. Verdict: **NO_NEW_CRITICAL_MAJOR**. R4 is the first
round with zero new critical or major findings, so **Reviewer A converged at
R4** under the fill's convergence criterion. Three NEW advisories; none
reopened, no reverts. No additional Reviewer A round is opened for this
documentation-only cleanup. Reviewer B and the orchestrator's gate remain
pending. Evidence root supplied by the brief:
`C:\Users\rwsmy\clearwater-review-evidence\wp4.5\r4\`; individual transcript
filename/hash and process assertion records were not supplied to the cell.

| Finding | Classification / disposition | Authorized cleanup |
| --- | --- | --- |
| A-1 | Advisory, out of envelope, EXECUTED; accept | Clarify F7: repeated same-tag entries can amplify where the base collapsed them into one key; the worst-case order matches the base using distinct tags. Documentation only. |
| A-2 | Advisory, out of envelope, EXECUTED; accept named Limit | An IFD0 already at 65,535 entries cannot take required D63 insertions; edit raises and sanitise drops the block. Base failed too. Add one report Limit sentence; no behavior change. |
| A-3 | Advisory, in envelope, REASONED; accept | Correct the report Implementation/Limit wording and edit docstring: header faults or an IFD0 offset past the block raise; cycles drop only the child (IFD0 has no ancestor). Excess output entries are the further whole-block case. |

Initial git status was clean, HEAD `2923402`. This turn changes only report,
ledger and exif.py docstring text, with no product behavior or test change.
Dispatcher-seat evidence on `2923402` (supplied, not run by this cell): ruff
format/check clean; blobs LF/ASCII; real-photo node
`tests/test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos`
**1 passed in 263.93 s**. Depth at turn-3 yield supplied by dispatcher:
**169,845 input tokens**, binding window **258,400**.

Reviewer-executed evidence, supplied rather than re-run by this cell: 3,000
valid blocks / 85,545 entries checked, zero edit-route fidelity mismatches;
12 from_tiff structure-tag drops matched the rule; zero Pillow-view
differences. Mutation checks covered 20,000 inputs / 54,865 valid outputs,
at most four tables and the corrected +5 entry bound, no exception beyond
ValueError/struct.error. The reviewer confirmed the grant, scope locks,
254-case file and its 8/4/12 R3 case split, with 460 selected photo tests green.
These are independent review results, not final orchestrator gate results.

### R4 cleanup verification and return

A-1's F7 clause now distinguishes repeated SAME-tag inputs (base collapsed
them) from the equal-order worst case using distinct tags. A-2's single Limit
sentence records the 65,535-entry IFD0 plus required D63 insertion failure,
the sanitise whole-block drop and the base's failure. A-3 corrects current
Implementation/Limit wording, the R2 F-C summary and edit's body/Raises
docstring: header fault or IFD0 offset past the block, cycles isolate the
child, entry-count overflow is the further whole-block case. No function
body, test, interface or dependency changed. All three advisories accepted;
no false-positive rejection, reopened item or revert. No register row added.

| Check | Exit | Actual result | Evidence under work/wp4.5/ |
| --- | --- | --- | --- |
| Requested light files: new EXIF-byte file plus test_io_photo_r1.py | 0 | 288 passed, 1 warning in 2.27s | `r4-light.log/xml` |
| `uv run --offline ruff check src/clearwater/io/photo/exif.py` | 0 | All checks passed! | `r4-ruff.log` |
| `uv run --offline mypy` | 0 | Success: no issues found in 141 source files | `r4-mypy.log` |
| Read-only scope/byte/AST/result audit | 0 | Three owned files only; no test change; ASCII/LF, final newlines, no trailing whitespace; diff check clean; executable AST equal to 2923402 after docstrings stripped; JUnit confirms 288 cases / zero failures | `r4-final-audit.log` |

Pytest uses `PYTHONPATH=scripts`, `--basetemp=work/wp4.5/tmp`,
`-p sandbox_mkdir_shim`, `-p no:cacheprovider`, and
`-m "not gpu and not footage and not gui and not slow and not fullclip"`.
All output is file-routed under work/wp4.5. The one Pillow UserWarning is the
existing synthetic bad-value fixture; no warning suppression added. This
bounded documentation cleanup needs no RED test or behavioral remediation.

Verification loop: checked each advisory against the existing parser/writer
paths and supplied execution evidence, corrected only text, then confirmed
the executable AST and tests unchanged and the requested checks green. No
additional in-envelope defect found. Reviewer A remains converged at R4;
Reviewer B and the final orchestrator full parallel + impacted serial gate
are pending. No footage accessed, commit, mailbox post, configuration change
or write outside the worktree. One logical documentation cleanup spans the
three named files. Last supplied depth is 169,845; current depth remains
dispatcher-read at yield, binding window 258,400.

## Reviewer A Round 3 - seat 2 adjudication

Reviewer: Claude opus/high, read-only on `c7c7360`; full R3 findings supplied
in the seat-2 turn-2 dispatch. Verdict: `NEW_CRITICAL_MAJOR_FOUND`.
Governing ruling: CHARC `85978ce0cd76c577`, 2026-10-29, DESIGN GUARD.
Evidence root: `C:\Users\rwsmy\clearwater-review-evidence\wp4.5\r3\`;
individual transcript filename/hash and process assertions were not supplied.
All four findings are NEW; no reopened findings or reverts. This adjudication
precedes new tests and product changes. Initial git status was clean, HEAD
`c7c7360`.

| Finding | Classification / CHARC disposition | Confirmation and commissioned action |
| --- | --- | --- |
| F-1 | Major, in envelope, EXECUTED; FIXED by the design guard | Distinct overlapping child offsets evade the exact-offset cache. Only the first occurrence of each carried pointer tag per parent is followed (34665/34853 in IFD0, 40965 in Exif); later occurrences warn/drop. Parse/write caches removed. P=200/N=400 cases RED then green, with one-child shape and corrected +5 entry bound. |
| F-2 | Minor, out of envelope, EXECUTED; resolved by the commissioned guard | Cache label-sharing confirmed RED. Same-offset siblings now parse per label, Exif alone gets Interop/dimensions, GPS warning names GPS/40965. Ancestor cycle checks retained. |
| F-3 | Advisory, in envelope, REASONED; report corrected | R2's child-cache claims replaced with the guard and corrected bound. F-A and F-1 FIXED by that rule; F7 shared values remains the sole amplification Limit. |
| F-4 | Advisory, in envelope, REASONED; no change ruled | Keep the warning on SubIFDs and other unsupported IFD-valued entries in from_tiff; this matches the binding warning policy. |

The guard narrows R1 F3 only for the three structural pointer tags. All other
non-D63 duplicate fields retain the prior pass-through rule. The R2 shared
child test and R1 duplicate-Exif-child test are amended to the newly ruled
first-pointer-only contract inside the owned test file. No other scope
or dependency change is authorized. R4 blocking on this class must STOP to
CHARC with a cap recommendation, per the dispatch.

Dispatcher-seat evidence on `c7c7360` (supplied, not run by this cell): ruff
format/check clean, all blobs LF/ASCII; real-photo node
`tests/test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos`
**1 passed in 272.04 s**. This predates R3 changes. Depth supplied at seat-2
turn-1 yield: **119,808 input tokens**, binding window **258,400**.

### R3 pre-build STOP - RESOLVED by the turn-3 erratum

The orchestrator's turn-3 erratum to CHARC `85978ce0cd76c577`, reported to
CHARC, resolves this STOP: **written entries <= 4 * len(source block) / 12 + 5**.
The allowance is exactly the at-most-five D63 insertions. All other design
guard requirements stand. The P=200/N=400 regressions must also assert exactly
ONE Exif (or GPS) IFD; that shape assertion is the regression catch. Turn 3
now proceeds with RED tests on the unchanged `c7c7360` product. HEAD is
`e2df398`; git status was clean and product/test diff from `c7c7360` was empty.
This replaces the exact bound as the binding test requirement; the following
STOP evidence is historical.

**[minor, in envelope, EXECUTED] STOP** under the dispatch instruction:
"If you see that the ruled design cannot hold for a reason the ruling did
not foresee, STOP and say so with evidence before building around it."
The rule states "written entries <= 4 x len(block) / 12 by construction".
That exact bound conflicts with mandatory D63 insertion for a valid empty
source table, independently of the pointer/cache design.

Cheap reproduction on unchanged `c7c7360` product:
`uv run --offline python work/wp4.5/r3_bound_probe.py`, exit 0;
output `work/wp4.5/r3-bound-probe.log`. The probe constructs only a classic
TIFF header and empty IFD0, confirms sanitise retains it, then independently
counts output entries using struct. No Pillow serializer or product parser
is used for the output count.

| Synthetic source | Input bytes | Source entries | Required output entries | Exact bound check |
| --- | --- | --- | --- | --- |
| Empty IFD0 with next pointer | 14 | 0 | 5 | `12 * 5 <= 4 * 14` is `60 <= 56`: false |
| Empty IFD0 without next pointer (F-B) | 10 | 0 | 5 | `12 * 5 <= 4 * 10` is `60 <= 40`: false |

The five output entries are IFD0 tags 274, 305, 34665 and Exif tags 40962,
40963: the four mandatory D63 fields plus the required Exif pointer. These
inputs have no source pointer, duplicate, overlap, shared child or cache hit;
the ruled cache removal cannot change this result. Returning fewer entries
would break the unchanged D63 requirement. This is an exact-bound conflict,
not a rejection of the first-pointer-only design or a new amplification class.

Recommendation to CHARC: keep the design guard unchanged, and rule the bound
as `written entries <= 4 * len(source) / 12 + 5` (equivalently, distinguish
the bounded carried source entries from at most five fixed D63 insertions).
This preserves linear growth and the commissioned P=200/N=400 entry-count
tests. Do not silently amend the binding exact bound in code or report.

No new RED tests, product fixes, report amendments, light pytest run or static
gates were performed this turn because the STOP is before building. F-1/F-2
remain unremediated and F-3's report change remains pending; F-4 requires no
change. The R2 test rewrite remains pending, explicitly recorded above.
Only this ledger changes. Scratch probe/log are ignored under work/wp4.5;
no footage access, dependency/interface/config changes, mailbox posts or
commits. R3 process/evidence assertions and final R4/B/gate remain dispatcher
owned. Corrected turn-2 yield depth, supplied in turn 3: **135,854 input
tokens**, binding window **258,400**. The 119,808 figure belongs to turn 1.

## Reviewer A Round 2 - seat 2 adjudication

Reviewer: Claude opus/high, read-only on `3020648`; full findings supplied in
the seat-2 dispatch. Evidence root supplied by the brief:
`C:\Users\rwsmy\clearwater-review-evidence\wp4.5\r2\` (individual transcript
filename/hash not supplied). Verdict: `NEW_CRITICAL_MAJOR_FOUND`.
Governing ruling: CHARC `72fc47f6a4ecfd91`, 2026-10-29T20:02:35Z.
All six reviewer findings are NEW; none reopened, reverted or rejected as false positive.
This adjudication precedes the RED tests and all product changes.

| Finding | Classification / CHARC disposition | Confirmation and authorized action |
| --- | --- | --- |
| F-A | Major, in envelope, EXECUTED; concur, FIX commissioned | `read` and `write` recurse per pointer without memoization. Parse each source child offset once, serialize its shared object once, and retain every pointer's type/count. Ancestor offsets remain cycles. RED uses A=B=C=150 and independent unique-IFD entry counting, with no time bound. Distinct from R1 F7 shared values. |
| F-B | Minor, in envelope, EXECUTED; concur | Parser subtracts six bytes instead of two. Complete entry arrays survive without the unused next pointer; output next pointers remain zero. RED for IFD0 and GPS. |
| F-C | Advisory, in envelope, EXECUTED; ruled damage amendment | Cut arrays retain all whole entries, with one warning identifying the IFD and declared/kept counts. Root raises only for header, invalid root offset or cycle; child offset/cycle faults drop that child. RED for IFD0 and GPS. Supersedes R1's whole-table-fault controls in this WP's new test file. |
| F-D | Advisory, in envelope, EXECUTED; ruled Limit | Follow only pointer types 3/4/13. Type 9 and every other carried pointer type are dropped with an IFD/tag warning. Add a regression control; no pointer-type widening. |
| F-E | Advisory, in envelope, REASONED; concur | Report F-A as FIXED separately from F7. Amend damage wording, add F-D Limit and R2 evidence. |
| F-F | Advisory, in envelope, REASONED; concur | sanitise's trial edit runs quietly using a private keyword, default loud. Writer warns once. RED over actual synthetic read_photo + write_photo, without clearing captured warnings between them. |

Ruling quoted for this dispatch: "Each child IFD is parsed ONCE and written
ONCE, keyed by its SOURCE offset"; "An entry ARRAY cut short, in IFD0 or a child,
keeps every WHOLE entry that fits"; "sanitise()'s trial edit runs quietly
(a private keyword, default loud)". Q1 remains (b), stdlib struct byte rewrite.
No new dependency, frozen-interface change, writer change or other-file grant.
New major at R3 must return to CHARC before remediation; R3 runs after yield.

Dispatcher-seat evidence on `3020648` (supplied, not run by seat 2):
`tests/test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos`
**1 passed in 268.01 s**, all 73 Phone photos. Reviewer supplied 409 light
tests passed and 1,500 valid fuzz blocks / zero mismatches. These predate the
R2 fixes and do not replace final-candidate verification. Seat 2 initial
`git status --short` was empty; no foreign change found. No footage accessed.

RED outcomes and final checks are recorded in the R2 sections at the end.

## Round 0 - STOP resolved: Q1 = (b)

STOP resolved, Q1 = (b) (CHARC `c64900357c363330`, brief commit `b4f2785`).
The existing `Image.Exif.tobytes()` path cannot carry source type pins into its
fresh IFD objects, including Exif, GPS and Interop. CHARC also confirmed rational
reduction and an added NUL for unterminated ASCII, excluding a Pillow value
re-encoding solution. The following Round 0 evidence is historical.

Turn 2 dispatch quotes the governing decision: "RULING: Q1 = (b), the byte-level
IFD rewrite in exif.py. NOT (a')." The rewrite passes source type/count/value
bytes through, relocates supported child IFDs in source byte order, preserves
entry order, inserts D63 entries by tag, drops IFD1/other IFD-valued entries,
isolates damaged children and rejects damaged roots. `from_tiff` uses the same
parser/writer with its structural drop set. BigTIFF is unsupported.

### Dispatch and scope

- Brief: `docs/briefs/wp4.5-brief.md`, FINAL, CHARC `f34420e1c8ff5d29`.
- Product base: main `5a1538a`; inspected worktree HEAD `61446a5`, branch `wp4.5`.
  `git diff --quiet 5a1538a -- src/clearwater/io/photo/exif.py
  src/clearwater/io/photo/writer.py` returned 0: the inspected product is the base.
- Read dispatch recipe, application, CLAUDE entry point, model prompting standard,
  review/gate fill, plan 4.1-4.5, spec D24/D63/8.1, AD-17, complete `exif.py`,
  writer hand-off, reader extraction/sanitisation routes and Pillow source below.
- Turn 1 changes only this ledger. Synthetic probe and runner logs are ignored
  scratch files under `work/wp4.5/`; no real footage or metadata was accessed.
- Writer change is not needed on present evidence: `writer.py:134-140` passes
  `edit()`'s bare bytes directly to `write_png(exif=block)`. Source-format-specific
  EXIF serialization does not occur at that hand-off.
- No product/test implementation, dependency, frozen interface, local configuration,
  existing test, register or harness file changed. No commit attempted.

### Mechanism evidence: installed Pillow 12.3.0

All Pillow paths below are relative to `.venv/Lib/site-packages/PIL/`.

| Mechanic | Source | Measured or affected surface |
| --- | --- | --- |
| Loaded IFD retains raw tag bytes and source type | `TiffImagePlugin.py:936-937` stores `_tagdata[tag]` and `tagtype[tag]` | Each independently loaded source IFD; type is available before decoding |
| Public per-IFD type pin | `TiffImagePlugin.py:535-549` documents `tagtype`; `:674-685` guesses only when the tag has no pin | Direct `ImageFileDirectory_v2` assignment preserves an explicit type 2 |
| Untyped tag guessing | `TiffImagePlugin.py:718-721` maps strings to ASCII and bytes to BYTE | Unpinned LensModel bytes become type 1 |
| ASCII decode/encode loss | `TiffImagePlugin.py:814-827` removes one terminal NUL, decodes latin-1, encodes strings using ASCII replacement and appends one NUL | Base `edit()` and `from_tiff()` replace the synthetic high byte |
| Pinned writer dispatch | `TiffImagePlugin.py:976-990` selects `_write_dispatch[typ]` from `tagtype` | Direct pinned LensModel bytes invoke type 2's bytes-preserving writer |
| Count calculation | `TiffImagePlugin.py:998-1004` uses encoded byte length for types 1, 2 and 7 | Pinned ASCII payload has count 6; guessed BYTE payload has count 5 |
| EXIF top-level reconstruction | `Image.py:4204-4226` creates a fresh IFD and assigns values, without copying source types | A pin on loaded `Exif._info.tagtype` does not survive `Exif.tobytes()` |
| Nested EXIF read loses type metadata | `Image.py:4108-4122` constructs an IFD then returns a plain fixed-up dict; `:4235-4244` selects Exif/GPS/Interop | `get_ifd()` supplies decoded values, not source `tagtype` |
| Nested serialization also rebuilds | `TiffImagePlugin.py:981-987` constructs a fresh IFD with `group=tag`, assigns dict items and recurses | Exif, GPS and Interop source type pins cannot travel through nested dict values |

Proposed source carry, if a serialization route is authorized: inspect IFD0 and
the Exif/GPS pointers in the original TIFF bytes, then Interop via Exif; load each
directory independently so its source types and raw values remain available.
Pin each kept entry's type on its actual destination IFD before assignment.
Retain source byte order for numerical byte fidelity. For non-7-bit ASCII,
supply original bytes under type 2 with exactly one terminal NUL removed when
present, because Pillow's ASCII writer adds one. Counts, multiple NULs and other
raw encodings still need explicit validation; merely replacing strings with
bytes is insufficient. The mechanism for guaranteeing all counts and raw values
is not claimed implemented or proven by this note.

`Image.Exif` exposes no corresponding serialization type map, and the nested
writer copies only `items()` into fresh destination IFDs. No global monkeypatch
or private-dispatch mutation was tried or proposed as the product solution.
Direct typed IFD serialization works; the unresolved decision is how to connect
those IFDs without crossing the ruled mechanism boundary. This evidence does
not claim that every possible Pillow-based serializer is impossible.

### Cheap reproduction and validation record

Commands ran at the cell's seat, with output routed to files first:

| Command / evidence | Result |
| --- | --- |
| `uv sync --offline`, `work/wp4.5/round0-sync.log` | Exit 0; resolved 62 packages, audited 61 packages; no package-index access |
| `uv run --offline python work/wp4.5/round0_probe.py`, `work/wp4.5/round0-probe.log` | Exit 0; Pillow 12.3.0; results below |

The ignored probe uses only a constructed TIFF header and directories, the
synthetic five-byte value `b"ab\x80cd"`, Pillow objects and a 1x1 synthetic TIFF.
Its independent `struct` parser compares types, counts and addressed value bytes.

| Probe | Parsed result |
| --- | --- |
| Direct `ImageFileDirectory_v2`, `tagtype[42036] = 2`, bytes assignment | Type 2, count 6, `b"ab\x80cd\x00"` |
| `Image.Exif.tobytes()`, bytes assignment plus pin on loaded root `_info` | Type 1, count 5, `b"ab\x80cd"` |
| `Image.Exif.tobytes()`, bytes assignment in Exif IFD | Type 1, count 5, `b"ab\x80cd"` |
| Same, GPS IFD | Type 1, count 5, `b"ab\x80cd"` |
| Same, Interop IFD reached through Exif | Type 1, count 5, `b"ab\x80cd"` |
| Base `edit()` with source LensModel type 2 | Type 2, count 6, `b"ab?cd\x00"` |
| Synthetic TIFF source Artist | Type 2, count 6, `b"ab\x80cd\x00"` |
| Base `from_tiff()` on that TIFF | Type 2, count 6, `b"ab?cd\x00"` |

No pytest/static gate ran in this documentation-only turn. No test failure text
is claimed observed: the above are executed probes, and the next section is the
RED-first test roster and predicted diagnostics.

### from_tiff route

`exif.py:from_tiff` opens the synthetic TIFF lazily through Pillow, copies allowed
IFD0 fields into a new `Image.Exif`, carries Exif/GPS dicts, materializes Interop,
and calls `built.tobytes()`. This loses types and non-ASCII bytes before the
writer's `edit()` call. `reader.py:199-201` calls `sanitise(from_tiff(data), name)`;
`sanitise` returns the original usable block, so it cannot recover bytes already
lost in `from_tiff`. An authorized helper must serve both serialization routes,
while keeping TIFF structural/profile filtering and damaged-IFD isolation.

### Planned tests: new tests/test_io_photo_exif_bytes.py only

Every fixture is synthetic and every filesystem write uses its test's `tmp_path`.
No gpu, footage, gui, slow or fullclip markers. An independent bounded TIFF parser
will compare `(tag, type, count, value_bytes)` per kept IFD entry. Pointer values
are followed structurally; their relocated offsets are not compared as payloads.
Both byte orders and inline/out-of-line values will be covered where applicable.

All predictions below concern main `5a1538a`; new tests do not yet exist.

| Planned check | Expected base result / failure diagnostic |
| --- | --- |
| `test_edit_preserves_untyped_ascii_bytes`: LensModel, including bytes 0x80-0xFF | RED: `Exif.LensModel value bytes changed`; type/count also compared, so a bytes-only patch fails `TIFF type changed: 2 -> 1` |
| `test_edit_preserves_nul_filled_make_model`: types and counts with embedded/multiple NULs | Control expected green for normally terminated NUL-filled source ASCII; guards against trimming or string normalization |
| `test_edit_preserves_artist_description_bytes`: latin-1 Artist and UTF-8 ImageDescription | RED: `IFD0.Artist value bytes changed` / `IFD0.ImageDescription value bytes changed` |
| `test_edit_preserves_plain_ascii`: normal text and counts | Control expected green; prevents collateral corruption |
| `test_edit_preserves_types_in_every_ifd`: non-default source types on untyped tags in IFD0, Exif, GPS and Interop | RED: `<IFD>.<tag> TIFF type changed`; ensures carrying only known ASCII tag types cannot pass |
| `test_edit_preserves_makernote_and_gps`: UNDEFINED MakerNote, synthetic refs and rational fields | Standard MakerNote/ref controls expected green; include a synthetic unreduced rational to check raw-byte fidelity rather than numerical equality |
| `test_edit_applies_d63`: orientation 1, Software Clearwater, PixelX/YDimension, IFD1 absent | Control expected green; guards all retained D63 edits and thumbnail removal |
| `test_write_photo_preserves_exif_bytes`: synthetic PNG/JPEG read -> write_photo -> PNG read | RED: `Exif.LensModel value bytes changed` in output metadata/eXIf; source-format cases verify the shared payload hand-off |
| `test_from_tiff_preserves_ascii_bytes`: synthetic TIFF ASCII tag with 0x80 | RED: `IFD0.Artist value bytes changed`, before edit; also compare after edit to exercise the shared carry |

Controls are intentionally predicted green on the base. Claiming each control
is RED would contradict its purpose and the observed behavior. Regression
checks will record actual failing assertion text in the implementation turn.
If an existing test pins a guessed type incompatible with source fidelity, STOP
and name it; no existing test may be edited.

### Limits and remaining gates

Fidelity concerns type, count and value bytes of kept IFD0/Exif/GPS/Interop fields,
excluding the D63 replacements. Entry order and relocated offsets are not fixed.
IFD1 is dropped. MakerNote content is byte-preserved; correctness of MakerNote
internal offsets remains a pre-existing, out-of-scope limitation. No new
dependency or frozen-interface change is authorized.

After a mechanism ruling, turn 2 adds RED tests, implements within exif.py, and
runs the brief's light checks with the sandbox pytest shim. The dispatcher owns
format checking, Reviewer A/B, the full parallel leg and impacted serial nodes;
no full serial leg is requested. No acceptance or convergence is claimed now.

### Cumulative findings / verification loop

| Round | Source | Critical | Major | Minor | In / out | NEW / REOPENED | Reverts | Product / test fixes | Disposition |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | Cell source trace + executed synthetic probe; not Reviewer A | 0 | 1 | 0 | 1 / 0 | 1 / 0 | 0 | 0 / 0 | STOP resolved, Q1 = (b) (CHARC `c64900357c363330`) |
| T2 compatibility check | Executed existing test; not Reviewer A | 0 | 1 | 0 | 1 / 0 | 1 / 0 | 0 | Product rewrite + new regression tests; no compatibility remediation | Original STOP resolved by test-line grant `1d9f88948f4350c4`; granted injection blocked in T3 |
| T3 grant check | Executed base/current test and independent TIFF inspection; not Reviewer A | 0 | 1 | 0 | 1 / 0 | 1 / 0 | 0 | Test-only attempted injection; no product change | STOP resolved by amended grant `8dd13704a85f2237`: placeholder tag then tag-ID patch and presence assertion |
| T4 amended test check | Executed base test and final light run; not Reviewer A | 0 | 0 | 0 | 0 / 0 | 0 / 0 | 0 | Test-only remediation; no product change | Amended real GPS injection passes with rewrite; light run green; Reviewer A R1 pending |
| A R1 | Claude opus/high, read-only; dispatch text and CHARC ruling `980818fc01eb77ea` | 0 | 3 | 2 (+4 advisory) | 8 / 1 | 9 / 0 | 0 | Product fixes F1/F2/F3/F4/F8; tests F6; docs F5/F7/F9 | NEW_CRITICAL_MAJOR_FOUND; remediation green at cell; R2 required |
| A R2 | Claude opus/high, read-only on `3020648`; CHARC `72fc47f6a4ecfd91` | 0 | 1 | 1 (+4 advisory) | 6 / 0 | 6 / 0 | 0 | Product fixes F-A/B/C/F; tests/controls; report F-E and F-D Limit | NEW_CRITICAL_MAJOR_FOUND; seat 2 remediation green (907 light tests); R3 next |
| A R3 | Claude opus/high, read-only on `c7c7360`; CHARC `85978ce0cd76c577` + turn-3 bound erratum | 0 | 1 | 1 (+2 advisory) | 3 / 1 | 4 / 0 | 0 | Product guard F-1/F-2; tests; report F-3; F-4 unchanged | NEW_CRITICAL_MAJOR_FOUND; STOP resolved; 931 light tests green; R4 next |
| R3 pre-build check | Cell independent synthetic struct probe | 0 | 0 | 1 | 1 / 0 | 1 / 0 | 0 | 0 / 0 | Confirmed exact-bound conflict; RESOLVED: five fixed D63 insertions allowed by turn-3 erratum |
| A R4 | Claude opus/high, read-only on `2923402` | 0 | 0 | 0 (+3 advisory) | 1 / 2 | 3 / 0 | 0 | 0 / 0; report/docstring cleanup only | NO_NEW_CRITICAL_MAJOR; first zero-blocking round; Reviewer A CONVERGED at R4 |

- Suspected: the fresh IFD construction drops source type pins.
- Confirmed independently: source trace and parsed synthetic output agree for
  IFD0, Exif, GPS and Interop; bytes-only LensModel changes type and count.
- Rejected false positives: none recorded.
- Fixed: none; authorized scope this turn is the ledger only.
- Reviewer A transport/version/evidence: not supplied; no round has run.

### Dispatcher-read depth

| Turn / boundary | Depth supplied by dispatcher | Action |
| --- | --- | --- |
| Turn 1 / Round 0 | 70,739 input tokens; window 475,000 (supplied in turn 2) | STOP resolved; proceed under Q1(b) |
| Turn 2 yield | 114,882 input tokens; window 258,400 (supplied in turn 3) | Proceed under test-line grant `1d9f88948f4350c4` |
| Turn 3 yield | 128,189 input tokens; window 258,400 (supplied in turn 4) | Proceed under amendment `8dd13704a85f2237` |
| Turn 4 yield | 140,712 input tokens; window 258,400 (supplied in turn 5) | R1 remediation; yield near 230K if incomplete, stop near 250K |
| Seat 1 retirement / Seat 2 dispatch | Seat 1: 188,902 input tokens supplied; seat 2 depth not yet supplied; binding window 258,400 | Fresh seat 2 on clean `3020648`; evaluate at 200K, stop near 250K at a step boundary |
| Seat 2 turn 1 yield / turn 2 dispatch | 119,808 input tokens; binding window 258,400 | R3 design guard commissioned on `c7c7360`; pre-build check before implementation |
| Seat 2 turn 2 yield / turn 3 dispatch | 135,854 input tokens; binding window 258,400 | STOP resolved by the bound erratum; proceed with R3 RED/fix/report/light checks |
| Seat 2 turn 3 yield / turn 4 dispatch | 169,845 input tokens; binding window 258,400 | Reviewer A converged at R4; bounded report/docstring cleanup, no behavior/test changes |

## Reviewer A Round 1 - adjudication and remediation

Reviewer: Claude opus/high, read-only, run by the dispatcher on `5a57d9f`.
Verdict: `NEW_CRITICAL_MAJOR_FOUND`, 3 major, 2 minor, 4 advisory, all NEW.
Evidence: reviewer text supplied in turn-5 dispatch; external evidence is held
by the dispatcher under the brief's WP4.5 evidence root. Transcript filename,
hash and process assertion records were not supplied to the cell. Governing
ruling: CHARC `980818fc01eb77ea`, 2026-10-29T19:41:08Z.

| Finding | Classification and disposition | Independent confirmation / action |
| --- | --- | --- |
| F1 | Major, in envelope, EXECUTED; accept amended entry/table damage rule | Entry value errors escape the non-pointer path; add RED cases, then drop only the faulty entry with one IFD/tag warning. Header/root-table faults still raise; child-table faults drop only that child. |
| F2 | Major, in envelope, EXECUTED; accept | Type-13 check precedes supported pointer handling; add RED tests and carry supported pointer types 3/4/13. Other type-13 entries remain dropped. |
| F3 | Major, in envelope, EXECUTED; accept | `_put` stops at the first match; later D63 duplicates survive. RED tests require first-position replacement and warning/removal of later D63 duplicates only. Other duplicates pass through. |
| F4 | Minor, in envelope, EXECUTED; accept | Empty-child filtering is root-only in from_tiff. RED tests require pruning empty children/pointers at every level in both routes. |
| F5 | Minor, documentation truth, REASONED; accept | Update edit/from_tiff docstrings, report implementation/damage rules and limits to match F1/F2/F4. |
| F6 | Advisory, test coverage, REASONED; accept | New regressions cover the missing cases. Tighten root exception test to ValueError. Reviewer's independent alignment/overlap fuzz found no defect; no layout redesign. |
| F7 | Advisory, out of envelope, EXECUTED; accepted named limit, no fix | Shared large source values can be duplicated on relocation; reviewer measured the same amplification in base. Disposition per CHARC: document limitation, no register row. |
| F8 | Advisory, originally out of envelope, REASONED; commissioned into remediation by CHARC | `_write_entries` packs relocated SHORT pointers as H unconditionally. Add RED boundary cases; retain SHORT if offset fits, otherwise promote to LONG. |
| F9 | Advisory, grant-record wording, REASONED; accept record only | Amendment `8dd13704a85f2237` explicitly authorizes the presence assertion/comment; record alongside grant `1d9f88948f4350c4`. No existing-test change needed. |

R1 row counts F8 within the commissioned remediation; F7 is the sole
out-of-envelope item. No reopened finding or revert. Adjudication was recorded
before tests/product changes. Final RED/green evidence follows below.

### Dispatcher-seat footage evidence

On `5a57d9f`, the dispatcher ran
`tests/test_photo_check.py::test_the_real_photo_leg_reads_and_round_trips_the_owners_photos`:
**1 passed in 328.40 s**, over all the owner's Phone photos. This is supplied
seat evidence, not a cell footage run, and predates R1 remediation. It is not
substituted for the final candidate gate.

### Reviewer-executed checks (supplied, not re-run by this cell)

- 3,000 random valid blocks: zero fidelity/layout mismatches, including II/MM,
  types 1-12, counts 0-9, unsorted IFD0 and child combinations; even offsets,
  non-overlap and next-IFD zero checked.
- 20,000 mutated/truncated blocks: only ValueError/struct.error, no hang;
  reviewer's observed worst probe 1.8 ms is not a product performance claim.
- Ordinary synthetic camera-style block: same 20 decoded fields as base.
- Reviewer reports ruff/format and 318 selected tests passed, with scope locks
  intact. These figures are reviewer evidence, not final gate results.

### R1 remediation, verification and return

F1 now catches value/type errors at the entry boundary, emits exactly one
IFD/tag warning and continues with siblings. Root/header/table errors still
raise into sanitise/from_tiff; child-table faults still drop only the child.
F2 allows type 13 only at carried pointer positions. F3 replaces the first D63
entry in place and drops later copies with individual warnings; non-D63
duplicates, including duplicate Exif pointers, survive. Every Exif child gets
the dimension edits. F4 prunes empty children recursively at parse time. F8
retains fitting SHORT pointers and promotes only overflowing relocated offsets
to LONG. F5/F6 update the docstrings and test controls with these rules.

All rewriter warnings identify directory labels and tag IDs without value
bytes. F7 is a documented limit only; no hostile-amplification mitigation was
introduced. F9's presence assertion/comment are explicitly recorded as granted
in the report's owned-files GRANT line and must be in the completion record.

| Check | Exit | Actual result | Evidence under work/wp4.5/ |
| --- | --- | --- | --- |
| R1 RED, new file before any product fix | 1 | 84 failed, 119 passed in 1.95s | `r1-red.log`, `r1-red.xml`, per-case table below |
| R1 GREEN, new file after fixes/formatting | 0 | 203 passed in 0.81s | `r1-green.log`, `r1-green.xml` |
| Combined authorized light run | 0 | 880 passed, 5 deselected, 132 warnings in 15.69s | `r1-light.log`, `r1-light.xml`, `r1-light-summary.log` |
| Targeted ruff check: exif.py, new test file, granted R1 file | 0 | All checks passed! | `r1-ruff.log` |
| `uv run --offline mypy` | 0 | Success: no issues found in 141 source files | `r1-mypy.log` |
| Format owned Python changes | 0 | 2 files reformatted | `r1-format.log`; dispatcher final format gate remains pending |

Combined-light target counts (all passed): `test_io_photo_*.py` 636, including
the new file's 203; `test_photo_check.py` 6; `test_wp41_photo_path.py` 223;
`test_jobs_export_photo.py` 15. All executions use `PYTHONPATH=scripts`,
`uv run --offline pytest`, the sandbox mkdir shim/no-cache plugins,
`--basetemp=work/wp4.5/tmp`, and the same exclusion expression:
`not gpu and not footage and not gui and not slow and not fullclip`.

Verification loop: all blocking findings were independently reproduced on
`5a57d9f` before fixing. All amended entry/table controls and the new
regressions pass after the fixes. The complete authorized light pass and static
checks find no further failure. No finding was rejected as a false positive;
F7 is explicitly accepted as a limit, F8 is commissioned, F9 is record-only.
No revert or unowned change. The existing granted test is unchanged this turn.

Report implementation, damage rules, test counts and limits now reflect the
R1 rulings; the pre-remediation footage pass is attributed to the dispatcher.
All final gate placeholders remain pending. This is remediation evidence,
not Reviewer A convergence: yield for R2. A second NEW major at R2 requires
re-seating before any further remediation, per CHARC's ruling. No register row,
mailbox post, commit, new dependency, interface/config/fixture change, or cell
footage/GPU/GUI/slow/fullclip run.

## Turn 4 - amended grant implemented; light checks green

CHARC amendment `8dd13704a85f2237` (file `cae0ebba`,
2026-10-29T19:26:42Z) resolves the turn-3 STOP. Only the granted test changes:
it writes LONG/count-1 tag 65000 beside Make, parses the header byte order,
IFD0 offset/count and 12-byte entries to locate it, then patches only the
two-byte tag ID to 34853. A pre-read assertion verifies that the GPS entry
exists with the expected type/count and a past-EOF offset. The original final
three assertions remain verbatim. `struct` was already imported, so no imports
were added or removed. No product code changed in turns 3-4.

Completion-record GRANT line: `tests/test_io_photo_r1.py`, only
`test_a_tiff_with_an_unreadable_gps_ifd_keeps_its_other_fields`, CHARC
`1d9f88948f4350c4`, amended by `8dd13704a85f2237`.

### Final-form base evidence

The final amended test was run against scratch `5a1538a` EXIF code using the
same ignored plugin as turn 3; no worktree product was replaced. The real GPS
presence assertion passed. The original damage-warning assertion failed:

```text
assert 'GPS IFD cannot be read' in "ERROR    tifffile:tifffile.py:6414 <TiffTag.fromfile> raised TiffFileError('<tifffile.TiffTag 34853 @202> invalid value offset 16777200')\n"
```

Result: exit 1, 1 failed, 1 warning in 0.26s. Evidence:
`work/wp4.5/turn4-base.log`, `turn4-base.xml`. The ERROR above is the synthetic
damaged-pointer diagnostic from tifffile, not an infrastructure error. This
record supersedes the direct-extratag attempt as the grant's final base result.

### Final light verification

Combined targets: all `tests/test_io_photo_*.py`, `tests/test_photo_check.py`,
`tests/test_wp41_photo_path.py`, `tests/test_jobs_export_photo.py`. Command uses
`PYTHONPATH=scripts uv run --offline pytest <targets> -q -m "not gpu and not
footage and not gui and not slow and not fullclip" --basetemp=work/wp4.5/tmp
-p sandbox_mkdir_shim -p no:cacheprovider
--junitxml=work/wp4.5/turn4-light.xml`, with output routed to
`work/wp4.5/turn4-light.log`.

| Run | Exit | Actual result |
| --- | --- | --- |
| Combined light targets | 0 | 789 passed, 5 deselected, 132 warnings in 15.34s |
| Targeted ruff check on exif.py, new test file and granted existing test file | 0 | All checks passed! (`turn4-ruff-final.log`) |
| `uv run --offline mypy` | 0 | Success: no issues found in 141 source files (`turn4-mypy.log`) |

The final-form granted test accounts for the difference from turn 2: R1 is now
34 passed/0 failed, and every other per-file count is unchanged. The combined
run includes all 112 new byte-fidelity cases. `turn4-summary.log` records the
JUnit-derived per-file counts. The initial turn-4 lint check found one long
line in the granted test; it was wrapped and the targeted check re-ran green.
No further product behavior or assertions changed.

Final byte/scope check (`turn4-final-check.log`): exit 0. All three changed
files are ASCII/LF-only with final newlines and no trailing whitespace. AST
comparison proves no change outside the granted test, verifies the three
original assertions verbatim, and verifies the added presence assertion. Both
grant IDs and all three report gate placeholders are present. `git diff --check`
exited 0. A read-only `ruff format --diff tests/test_io_photo_r1.py` exited 0 and
reported one file already formatted (`turn4-format-diff.log`).

### Return/report and verification-loop disposition

Created `docs/reports/wp4.5-exif-bytes.md`: root cause, Q1 history and both
grounds for byte pass-through, implementation, test/base evidence, owned/granted
files, limits and the gate placeholders `@@PAR@@`, `@@SER@@`, `@@FOOT@@`.
Reviewer A R1 follows this yield; Reviewer B and final gate figures remain
pending. No full-suite, serial, footage, GPU, GUI, slow or fullclip run was
performed by the cell, and no convergence/acceptance is claimed.

The turn-2 compatibility suspicion and turn-3 filtered-injection suspicion are
both confirmed and resolved under the recorded grants. The amended final test
checks actual damaged data, its presence control passes, its base warning
assertion fails, and its rewritten-product assertions pass. The final light
and static checks reveal no further failure. No new finding is being banked or
declined, and no register row is required.

Only the single granted existing test, ledger and new report changed in turns
3-4. Public interfaces, product code, dependencies/lock file, all other tests,
fixtures, config, footage and harness remain untouched. No commits or mailbox
posts. All generated material is synthetic and remains under the worktree.

## Turn 3 - test-line grant blocked by tifffile filtering (resolved in turn 4)

CHARC `1d9f88948f4350c4`, file `adea9a23`, 2026-10-29T19:22:06Z,
granted only `tests/test_io_photo_r1.py::test_a_tiff_with_an_unreadable_gps_ifd_keeps_its_other_fields`.
The test now removes its monkeypatch parameter/shim, requests GPS tag 34853 as a
LONG/count-1 extratag with an offset beyond the synthetic file, and keeps the
three assertions verbatim. No imports became unused; none were removed. `Image`
remains used elsewhere in the file.

**[major] STOP:** the mandated injection is not written. Installed tifffile
includes 34853 in `TIFF.TAG_FILTERED` and refuses that tag in `extratags`.
`tifffile.py:3507-3516` adds filtered tags to its skip set and logs a warning
instead of writing them. Independent `struct` inspection of the generated
synthetic TIFF confirms Make is present and GPS 34853 is absent. No real
metadata was used.

Actual failure on BOTH main `5a1538a`'s EXIF implementation and the current product:

```text
assert 'GPS IFD cannot be read' in "WARNING  tifffile:tifffile.py:3513 <tifffile.TiffWriter 'gps.tif'> not writing extratag 34853\n"
```

| Probe/run | Exit | Result | Evidence under work/wp4.5/ |
| --- | --- | --- | --- |
| Granted test against scratch base EXIF module | 1 | 1 failed in 0.60s; injection absent | `turn3-base.log`, `turn3-base.xml`, `base_exif.py`, `wp45_base_exif.py` |
| Granted test against current product | 1 | 1 failed in 0.27s; same assertion | `turn3-grant.log`, `turn3-grant.xml` |
| Independent TIFF inspection | 0 | Make present; GPS absent; GPS in TAG_FILTERED | `turn3-filter-probe.log` |

Base method: an ignored pytest plugin obtains `git show
5a1538a:src/clearwater/io/photo/exif.py` using `subprocess.check_output`, writes
those bytes under `work/wp4.5/base_exif.py`, imports that scratch module, and
redirects `reader.exif_tools` and the collected test module's `exif_tools` to it
inside the isolated pytest process. No base file was checked out over the
worktree. Both test runs target exactly the granted node, set
`PYTHONPATH=scripts;work/wp4.5` for the base run (`scripts` for current), load
`sandbox_mkdir_shim` and `no:cacheprovider`, use `--basetemp=work/wp4.5/tmp`, and
apply the same five-marker exclusion as turn 2. The base run additionally loads
`-p wp45_base_exif`.

Recommended amendment: allow a synthetic placeholder LONG/count-1 extratag,
then patch only its two-byte tag ID in the written IFD0 entry to 34853. Its
out-of-range offset remains the real failure injection. Keep all three
assertions verbatim and remain inside the granted test. No such workaround has
been implemented because the grant specifies direct GPS `extratags` writing.

The full light rerun, new static checks and report are deferred at this STOP;
turn 2's results remain historical, not a green claim for the new test form.
No product code changed this turn. No other existing test or import changed.
No report or register row created, no commits/mailbox posts, no footage access.
Reviewer A has not run. The report and completion record must name the grant
above once the injection mechanism is resolved.

## Turn 2 - RED-first roster additions

Added by CHARC's re-ruling: unreduced RATIONAL 1234/100, negative SRATIONAL,
unterminated ASCII, MM source byte order, inline 4-byte/out-of-line 5-byte
boundaries, missing Orientation/dimensions/Exif IFD insertion, damaged child
offset/table isolation, damaged root raising with sanitise dropping, and
SubIFDs/type-13 dropping. Tests also cover source entry order, SHORT dimension
retention/promotion, bounded count/value reads, BigTIFF rejection and None input.
Actual baseline outcomes and light-run results will be recorded below.

### Turn 2 outcome: STOP on an existing test conflict

**[major]** `tests/test_io_photo_r1.py::test_a_tiff_with_an_unreadable_gps_ifd_keeps_its_other_fields`
fails with actual assertion text:

```text
AssertionError: assert 'GPS IFD cannot be read' in ''
```

Mechanism: the test at `tests/test_io_photo_r1.py:389-414` constructs a TIFF with
Make but no GPS IFD, monkeypatches `Image.Exif.get_ifd` to raise for GPS, then
expects the resulting warning. Q1(b) explicitly removes Pillow from `from_tiff`;
the real raw parser sees no GPS pointer and correctly emits no damage warning.
The failure injection is no longer reached. The synthetic damaged-child tests
exercise actual malformed offsets, tables and payloads and all pass.

Recommended disposition: have the owning seat replace the obsolete Pillow
failure injection with a synthetic damaged GPS IFD. This cell cannot edit the
existing test, and has not added an artificial Pillow call or warning to make
the mock fire. Per the dispatch, STOP and yield before any remediation. Reviewer
A has not run; no convergence or completed acceptance is claimed.

Built in `exif.py`: bounded classic-TIFF parsing of IFD0/Exif/GPS/Interop; raw
entry byte carry and relocation; source byte order and kept order preservation;
D63 replacement/insertion with SHORT dimension retention and LONG promotion;
IFD1 removal; unsupported IFD-valued entry dropping with warnings; damaged-child
isolation; malformed-root rejection; BigTIFF rejection; shared raw extraction
for `from_tiff` with structural filtering. Public signatures and Pillow read
views remain unchanged. `from_tiff` extracts source fields; the subsequent
writer call to `edit` applies D63, preserving read-side metadata semantics.

### Light-run evidence

All commands ran offline in the worktree. All pytest invocations set
`PYTHONPATH=scripts`, load `-p sandbox_mkdir_shim -p no:cacheprovider`, and use
`--basetemp=work/wp4.5/tmp`. Marker expression for every invocation:
`not gpu and not footage and not gui and not slow and not fullclip`.

| Run | Exit | Observed summary | Evidence under work/wp4.5/ |
| --- | --- | --- | --- |
| New file after implementation | 0 | 112 passed in 0.55s | `new-green.log`, `new-green.xml` |
| All `tests/test_io_photo_*.py` plus `test_photo_check.py`, `test_wp41_photo_path.py`, `test_jobs_export_photo.py` | 1 | 1 failed, 788 passed, 5 deselected, 132 warnings in 32.61s | `light.log`, `light.xml`, `light-summary.log` |
| `uv run --offline ruff check src/clearwater/io/photo tests/test_io_photo_exif_bytes.py` | 0 | All checks passed! | `ruff-final.log` |
| `uv run --offline mypy` | 0 | Success: no issues found in 141 source files | `mypy-final.log` |
| `uv run --offline ruff format src/clearwater/io/photo/exif.py tests/test_io_photo_exif_bytes.py` | 0 | 2 files reformatted | `format.log`; format CHECK remains at dispatcher seat |

Per-file results from the combined run's JUnit XML (deselected cases are not
emitted as test cases; 5 deselected is pytest's overall summary):

| File under tests/ | Passed | Failed |
| --- | --- | --- |
| test_io_photo_errors.py | 3 | 0 |
| test_io_photo_exif_bytes.py | 112 | 0 |
| test_io_photo_p3.py | 13 | 0 |
| test_io_photo_planted.py | 12 | 0 |
| test_io_photo_r1.py | 33 | 1 |
| test_io_photo_read.py | 163 | 0 |
| test_io_photo_rules.py | 17 | 0 |
| test_io_photo_srgb.py | 19 | 0 |
| test_io_photo_units.py | 68 | 0 |
| test_io_photo_write.py | 104 | 0 |
| test_jobs_export_photo.py | 15 | 0 |
| test_photo_check.py | 6 | 0 |
| test_wp41_photo_path.py | 223 | 0 |

The combined invocation also re-ran all 112 new cases on the formatted product.
An initial targeted lint run found six formatting/list-concatenation findings;
formatting and the new test helper's list expression were corrected before the
final runs. Initial and final mypy both passed. No full suite, footage, GPU,
GUI, slow or fullclip execution was requested or performed by the cell.

### Turn 2 verification loop and locks

- Suspected: Pillow value re-encoding changes kept field bytes/types/counts.
  Confirmed by 78 RED cases on the base; fixed by raw entry copying; all 112 new
  tests pass, including 34 baseline controls.
- Suspected: the existing Pillow-specific GPS injection conflicts with Q1(b).
  Confirmed by the named existing-test failure. No fix made: existing tests are
  outside the owned paths. This is the only failure in the authorized light run.
- Rejected false positives: garbage headers already raised `SyntaxError`; the
  new control now accepts that existing behavior rather than requiring a
  particular exception class.
- Only three owned files changed: `exif.py`, the new test file and this ledger.
  Writer, all existing tests, interfaces, dependencies/lock file, local config,
  fixtures, register and harness files are untouched. No real photos/metadata,
  footage writes, mailbox posts or commits. New tests write only under tmp_path.
- Limits to carry into the final report: BigTIFF unsupported, other IFD-valued
  entries (including SubIFDs and type 13) dropped with warnings, MakerNote
  internal-offset validity not repaired. The report awaits turn 3/seat figures.

### Executed RED baseline (before product changes)

Final RED run: exit 1; **78 failed, 34 passed**, 12 warnings. Product code was unchanged from main `5a1538a`.

Command: `PYTHONPATH=scripts uv run --offline pytest tests/test_io_photo_exif_bytes.py -q -m "not gpu and not footage and not gui and not slow and not fullclip" --basetemp=work/wp4.5/tmp -p sandbox_mkdir_shim -p no:cacheprovider --junitxml=work/wp4.5/red.xml`. Output: `work/wp4.5/red.log`; machine-readable results: `work/wp4.5/red.xml`.

The first drafting run was 79 failed/33 passed. The garbage-header control was corrected to accept the existing `SyntaxError` alongside other parse errors; no product code changed between runs. The final baseline below is authoritative.

| Test case (new file) | Baseline result / actual first failure line |
| --- | --- |
| `test_ascii_type_count_and_value_bytes_survive[42036-\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff\x00-path0-<]` | AssertionError: ('Exif',).42036 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[42036-\x80\x81\x82\x83\x84\x85\x86\x87\x88\x89\x8a\x8b\x8c\x8d\x8e\x8f\x90\x91\x92\x93\x94\x95\x96\x97\x98\x99\x9a\x9b\x9c\x9d\x9e\x9f\xa0\xa1\xa2\xa3\xa4\xa5\xa6\xa7\xa8\xa9\xaa\xab\xac\xad\xae\xaf\xb0\xb1\xb2\xb3\xb4\xb5\xb6\xb7\xb8\xb9\xba\xbb\xbc\xbd\xbe\xbf\xc0\xc1\xc2\xc3\xc4\xc5\xc6\xc7\xc8\xc9\xca\xcb\xcc\xcd\xce\xcf\xd0\xd1\xd2\xd3\xd4\xd5\xd6\xd7\xd8\xd9\xda\xdb\xdc\xdd\xde\xdf\xe0\xe1\xe2\xe3\xe4\xe5\xe6\xe7\xe8\xe9\xea\xeb\xec\xed\xee\xef\xf0\xf1\xf2\xf3\xf4\xf5\xf6\xf7\xf8\xf9\xfa\xfb\xfc\xfd\xfe\xff\x00-path0->]` | AssertionError: ('Exif',).42036 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[271-\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00-path1-<]` | PASS (control) |
| `test_ascii_type_count_and_value_bytes_survive[271-\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00-path1->]` | PASS (control) |
| `test_ascii_type_count_and_value_bytes_survive[272-\x00A\x00\x00B\x00\x00\x00-path2-<]` | PASS (control) |
| `test_ascii_type_count_and_value_bytes_survive[272-\x00A\x00\x00B\x00\x00\x00-path2->]` | PASS (control) |
| `test_ascii_type_count_and_value_bytes_survive[315-caf\xe9\x00-path3-<]` | AssertionError: ().315 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[315-caf\xe9\x00-path3->]` | AssertionError: ().315 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[270-caf\xc3\xa9\x00-path4-<]` | AssertionError: ().270 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[270-caf\xc3\xa9\x00-path4->]` | AssertionError: ().270 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[33432-synthetic copyright\x00-path5-<]` | PASS (control) |
| `test_ascii_type_count_and_value_bytes_survive[33432-synthetic copyright\x00-path5->]` | PASS (control) |
| `test_ascii_type_count_and_value_bytes_survive[65000-abcd-path6-<]` | AssertionError: ().65000 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[65000-abcd-path6->]` | AssertionError: ().65000 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[65000-abcde-path7-<]` | AssertionError: ().65000 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[65000-abcde-path7->]` | AssertionError: ().65000 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[65000-x\x80\x00-path8-<]` | AssertionError: ('GPS',).65000 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[65000-x\x80\x00-path8->]` | AssertionError: ('GPS',).65000 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[65000-x\x80\x00-path9-<]` | AssertionError: ('Exif', 'Interop').65000 type/count/value changed |
| `test_ascii_type_count_and_value_bytes_survive[65000-x\x80\x00-path9->]` | AssertionError: ('Exif', 'Interop').65000 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-4-<]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-4->]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-5-<]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-5->]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-7-<]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-7->]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-8-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path0-8->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path0-9-<]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-9->]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-10-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path0-10->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path0-11-<]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-11->]` | AssertionError: ().65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path0-12-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path0-12->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path1-4-<]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-4->]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-5-<]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-5->]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-7-<]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-7->]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-8-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path1-8->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path1-9-<]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-9->]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-10-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path1-10->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path1-11-<]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-11->]` | AssertionError: ('Exif',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path1-12-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path1-12->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path2-4-<]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-4->]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-5-<]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-5->]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-7-<]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-7->]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-8-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path2-8->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path2-9-<]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-9->]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-10-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path2-10->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path2-11-<]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-11->]` | AssertionError: ('GPS',).65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path2-12-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path2-12->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path3-4-<]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-4->]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-5-<]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-5->]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-7-<]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-7->]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-8-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path3-8->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path3-9-<]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-9->]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-10-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path3-10->]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path3-11-<]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-11->]` | AssertionError: ('Exif', 'Interop').65001 type/count/value changed |
| `test_non_ascii_source_types_and_raw_values_survive[path3-12-<]` | PASS (control) |
| `test_non_ascii_source_types_and_raw_values_survive[path3-12->]` | PASS (control) |
| `test_makernote_and_synthetic_gps_bytes_survive` | AssertionError: ('Exif',).37500 type/count/value changed |
| `test_d63_replaces_fields_and_drops_thumbnail[3-640-3]` | PASS (control) |
| `test_d63_replaces_fields_and_drops_thumbnail[3-65536-4]` | PASS (control) |
| `test_d63_replaces_fields_and_drops_thumbnail[4-640-4]` | AssertionError: assert (40962, 3, 1, b'\x80\x02') == (40962, 4, 1,...\x02\x00\x00') |
| `test_d63_inserts_missing_entries[None]` | AssertionError: assert (40962, 3, 1, b'\x1e\x00') == (40962, 4, 1,...\x00\x00\x00') |
| `test_d63_inserts_missing_entries[sub1]` | AssertionError: assert (40962, 3, 1, b'\x1e\x00') == (40962, 4, 1,...\x00\x00\x00') |
| `test_d63_inserts_missing_entries[sub2]` | AssertionError: assert (40962, 3, 1, b'\x1e\x00') == (40962, 4, 1,...\x00\x00\x00') |
| `test_none_source_has_only_the_four_d63_fields` | AssertionError: assert [(40962, 3, 1... b'\x00\x14')] == [(40962, 4, 1...x00\x00\x14')] |
| `test_kept_entry_order_is_preserved` | AssertionError: kept entry order changed |
| `test_damaged_child_is_dropped_alone[34665-path0-offset]` | AssertionError: damaged child was not reported |
| `test_damaged_child_is_dropped_alone[34665-path0-table]` | assert [1, 36864, 40... 40963, 40965] == [40962, 40963] |
| `test_damaged_child_is_dropped_alone[34665-path0-payload]` | AssertionError: damaged child was not reported |
| `test_damaged_child_is_dropped_alone[34853-path1-offset]` | assert 34853 not in [271, 274, 305, 34665, 34853] |
| `test_damaged_child_is_dropped_alone[34853-path1-table]` | assert 34853 not in [271, 274, 305, 34665, 34853] |
| `test_damaged_child_is_dropped_alone[34853-path1-payload]` | assert 34853 not in [271, 274, 305, 34665, 34853] |
| `test_damaged_child_is_dropped_alone[40965-path2-offset]` | assert 40965 not in [36864, 40962, 40963, 40965] |
| `test_damaged_child_is_dropped_alone[40965-path2-table]` | assert 40965 not in [36864, 40962, 40963, 40965] |
| `test_damaged_child_is_dropped_alone[40965-path2-payload]` | assert 40965 not in [36864, 40962, 40963, 40965] |
| `test_damaged_root_raises_and_sanitise_drops[garbage]` | PASS (control) |
| `test_damaged_root_raises_and_sanitise_drops[II*\x00\xff\xff\xff\xff]` | Failed: DID NOT RAISE any of (<class 'ValueError'>, <class 'struct.error'>, <class 'SyntaxError'>) |
| `test_damaged_root_raises_and_sanitise_drops[II*\x00\x08\x00\x00\x00\xff\xff]` | Failed: DID NOT RAISE any of (<class 'ValueError'>, <class 'struct.error'>, <class 'SyntaxError'>) |
| `test_oversized_root_value_is_rejected` | Failed: DID NOT RAISE <class 'ValueError'> |
| `test_other_ifd_values_are_dropped_with_warning` | AssertionError: unsupported IFD retained |
| `test_write_photo_preserves_bytes_through_png_exif[png]` | AssertionError: ('Exif',).42036 type/count/value changed |
| `test_write_photo_preserves_bytes_through_png_exif[jpeg]` | AssertionError: ('Exif',).42036 type/count/value changed |
| `test_from_tiff_preserves_raw_ascii_and_filters_structure` | AssertionError: ().315 type/count/value changed |
| `test_from_tiff_without_metadata_returns_none` | PASS (control) |
| `test_bigtiff_is_not_carried` | AssertionError: unsupported BigTIFF was not reported |

### R1 RED evidence before fixes on 5a57d9f

Final run: exit 1; **84 failed, 119 passed in 1.95s**. Product code remained unchanged from 5a57d9f. Output: `work/wp4.5/r1-red.log`; JUnit: `work/wp4.5/r1-red.xml`. Same sandbox shim, work temp root and five-marker exclusion as the earlier light runs.

R1 adds 94 cases. Three old whole-child payload-damage cases are superseded by the entry-damage matrix under the amended rule; six offset/table controls remain. The oversized-root-value test now requires dropping only that entry. Root/header cases require ValueError. The first drafting run exposed incorrect big-endian SHORT fixture encoding, which was corrected before any product change; the final results below are authoritative.

| R1 case / changed control | Actual pre-fix outcome |
| --- | --- |
| test_damaged_child_is_dropped_alone[34665-path0-offset] | PASS (control) |
| test_damaged_child_is_dropped_alone[34665-path0-table] | PASS (control) |
| test_damaged_child_is_dropped_alone[34853-path1-offset] | PASS (control) |
| test_damaged_child_is_dropped_alone[34853-path1-table] | PASS (control) |
| test_damaged_child_is_dropped_alone[40965-path2-offset] | PASS (control) |
| test_damaged_child_is_dropped_alone[40965-path2-table] | PASS (control) |
| test_damaged_root_raises_and_sanitise_drops[garbage] | PASS (control) |
| test_damaged_root_raises_and_sanitise_drops[II*\x00\xff\xff\xff\xff] | PASS (control) |
| test_damaged_root_raises_and_sanitise_drops[II*\x00\x08\x00\x00\x00\xff\xff] | PASS (control) |
| test_oversized_root_value_is_dropped_alone | ValueError: IFD value runs past block |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path0-edit-<] | AssertionError: bad entry discarded whole block |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path0-edit->] | AssertionError: bad entry discarded whole block |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path0-from_tiff-<] | AssertionError: bad entry discarded all metadata |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path0-from_tiff->] | AssertionError: bad entry discarded all metadata |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path1-edit-<] | AssertionError: assert (33434, 5, 1, b'\xd2\x04\x00\x00d\x00\x00\x00') in [(40962, 4, 1, b'\x04\x00\x00\x00'), (40963, 4, 1, b'\x03\x00\x00\x00')] |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path1-edit->] | AssertionError: assert (33434, 5, 1, b'\x00\x00\x04\xd2\x00\x00\x00d') in [(40962, 4, 1, b'\x00\x00\x00\x04'), (40963, 4, 1, b'\x00\x00\x00\x03')] |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path1-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path1-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path2-edit-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path2-edit->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path2-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path2-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path3-edit-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path3-edit->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path3-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[unknown_type-path3-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path0-edit-<] | AssertionError: bad entry discarded whole block |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path0-edit->] | AssertionError: bad entry discarded whole block |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path0-from_tiff-<] | AssertionError: bad entry discarded all metadata |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path0-from_tiff->] | AssertionError: bad entry discarded all metadata |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path1-edit-<] | AssertionError: assert (33434, 5, 1, b'\xd2\x04\x00\x00d\x00\x00\x00') in [(40962, 4, 1, b'\x04\x00\x00\x00'), (40963, 4, 1, b'\x03\x00\x00\x00')] |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path1-edit->] | AssertionError: assert (33434, 5, 1, b'\x00\x00\x04\xd2\x00\x00\x00d') in [(40962, 4, 1, b'\x00\x00\x00\x04'), (40963, 4, 1, b'\x00\x00\x00\x03')] |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path1-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path1-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path2-edit-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path2-edit->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path2-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path2-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path3-edit-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path3-edit->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path3-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[past_eof-path3-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path0-edit-<] | AssertionError: bad entry discarded whole block |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path0-edit->] | AssertionError: bad entry discarded whole block |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path0-from_tiff-<] | AssertionError: bad entry discarded all metadata |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path0-from_tiff->] | AssertionError: bad entry discarded all metadata |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path1-edit-<] | AssertionError: assert (33434, 5, 1, b'\xd2\x04\x00\x00d\x00\x00\x00') in [(40962, 4, 1, b'\x04\x00\x00\x00'), (40963, 4, 1, b'\x03\x00\x00\x00')] |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path1-edit->] | AssertionError: assert (33434, 5, 1, b'\x00\x00\x04\xd2\x00\x00\x00d') in [(40962, 4, 1, b'\x00\x00\x00\x04'), (40963, 4, 1, b'\x00\x00\x00\x03')] |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path1-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path1-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path2-edit-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path2-edit->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path2-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path2-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path3-edit-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path3-edit->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path3-from_tiff-<] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_entry_is_dropped_without_losing_siblings[inside_header-path3-from_tiff->] | AssertionError: bad entry discarded sibling fields with its whole IFD |
| test_r1_bad_tiff_software_value_keeps_make | AssertionError: bad Software discarded all TIFF metadata |
| test_r1_bad_ifd0_description_keeps_make[edit] | ValueError: IFD value runs past block |
| test_r1_bad_ifd0_description_keeps_make[from_tiff] | AssertionError: bad description discarded all metadata |
| test_r1_child_table_fault_drops_child_only[edit] | PASS (control) |
| test_r1_child_table_fault_drops_child_only[from_tiff] | PASS (control) |
| test_r1_type13_carried_pointer_survives[parent0-34665-child0-33434-edit-<] | assert (4, 1) == (13, 1) |
| test_r1_type13_carried_pointer_survives[parent0-34665-child0-33434-edit->] | assert (4, 1) == (13, 1) |
| test_r1_type13_carried_pointer_survives[parent0-34665-child0-33434-from_tiff-<] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent0-34665-child0-33434-from_tiff->] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent1-34853-child1-1-edit-<] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent1-34853-child1-1-edit->] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent1-34853-child1-1-from_tiff-<] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent1-34853-child1-1-from_tiff->] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent2-40965-child2-1-edit-<] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent2-40965-child2-1-edit->] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent2-40965-child2-1-from_tiff-<] | AssertionError: carried type-13 pointer lost its child |
| test_r1_type13_carried_pointer_survives[parent2-40965-child2-1-from_tiff->] | AssertionError: carried type-13 pointer lost its child |
| test_r1_d63_duplicates_are_removed_other_duplicates_survive[<-274] | AssertionError: later D63 duplicate retained |
| test_r1_d63_duplicates_are_removed_other_duplicates_survive[<-305] | AssertionError: later D63 duplicate retained |
| test_r1_d63_duplicates_are_removed_other_duplicates_survive[<-40962] | AssertionError: later D63 duplicate retained |
| test_r1_d63_duplicates_are_removed_other_duplicates_survive[<-40963] | AssertionError: later D63 duplicate retained |
| test_r1_d63_duplicates_are_removed_other_duplicates_survive[>-274] | AssertionError: later D63 duplicate retained |
| test_r1_d63_duplicates_are_removed_other_duplicates_survive[>-305] | AssertionError: later D63 duplicate retained |
| test_r1_d63_duplicates_are_removed_other_duplicates_survive[>-40962] | AssertionError: later D63 duplicate retained |
| test_r1_d63_duplicates_are_removed_other_duplicates_survive[>-40963] | AssertionError: later D63 duplicate retained |
| test_r1_empty_child_pointer_is_pruned[path0-edit] | PASS (control) |
| test_r1_empty_child_pointer_is_pruned[path0-from_tiff] | PASS (control) |
| test_r1_empty_child_pointer_is_pruned[path1-edit] | AssertionError: empty child pointer retained |
| test_r1_empty_child_pointer_is_pruned[path1-from_tiff] | PASS (control) |
| test_r1_empty_child_pointer_is_pruned[path2-edit] | AssertionError: empty child pointer retained |
| test_r1_empty_child_pointer_is_pruned[path2-from_tiff] | AssertionError: empty child pointer retained |
| test_r1_nested_empty_tree_leaves_no_tiff_metadata | AssertionError: recursively empty metadata tree was retained |
| test_r1_duplicate_exif_pointers_keep_both_children_with_d63_dimensions[<] | AssertionError: non-D63 duplicate pointer was dropped |
| test_r1_duplicate_exif_pointers_keep_both_children_with_d63_dimensions[>] | AssertionError: non-D63 duplicate pointer was dropped |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent0-34665-5-<] | PASS (control) |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent0-34665-5->] | PASS (control) |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent0-34665-70000-<] | struct.error: 'H' format requires 0 <= number <= 65535 |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent0-34665-70000->] | struct.error: 'H' format requires 0 <= number <= 65535 |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent1-34853-5-<] | PASS (control) |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent1-34853-5->] | PASS (control) |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent1-34853-70000-<] | struct.error: 'H' format requires 0 <= number <= 65535 |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent1-34853-70000->] | struct.error: 'H' format requires 0 <= number <= 65535 |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent2-40965-5-<] | PASS (control) |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent2-40965-5->] | PASS (control) |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent2-40965-70000-<] | struct.error: 'H' format requires 0 <= number <= 65535 |
| test_r1_short_pointer_promotes_only_when_relocated_offset_overflows[parent2-40965-70000->] | struct.error: 'H' format requires 0 <= number <= 65535 |

### R2 RED on unchanged product 3020648

Command: `PYTHONPATH=scripts uv run --offline pytest tests/test_io_photo_exif_bytes.py -k r2 --basetemp=work/wp4.5/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" --junitxml=work/wp4.5/r2-red.xml`. Output: `work/wp4.5/r2-red.log`.

Exit 1: **23 failed, 4 passed, 203 deselected, 1 warning in 28.46s**. All 27 new cases ran before changing exif.py. F-D's four cases are passing controls because the ruled SLONG drop already exists; no artificial RED claimed. F-A actual output entry count was 3,397,952 versus the required 454.

| Case | Actual pre-fix result |
| --- | --- |
| `test_r2_shared_children_are_written_once_by_entry_count[edit-<]` | AssertionError: shared child entries multiplied |
| `test_r2_shared_children_are_written_once_by_entry_count[edit->]` | AssertionError: shared child entries multiplied |
| `test_r2_shared_children_are_written_once_by_entry_count[from_tiff-<]` | AssertionError: shared child entries multiplied |
| `test_r2_shared_children_are_written_once_by_entry_count[from_tiff->]` | AssertionError: shared child entries multiplied |
| `test_r2_complete_table_without_next_pointer_survives[path0-edit-<]` | ValueError: IFD entry table runs past block |
| `test_r2_complete_table_without_next_pointer_survives[path0-edit->]` | ValueError: IFD entry table runs past block |
| `test_r2_complete_table_without_next_pointer_survives[path0-from_tiff-<]` | AssertionError: complete IFD0 lost without next pointer |
| `test_r2_complete_table_without_next_pointer_survives[path0-from_tiff->]` | AssertionError: complete IFD0 lost without next pointer |
| `test_r2_complete_table_without_next_pointer_survives[path1-edit-<]` | AssertionError: complete child lost without next pointer |
| `test_r2_complete_table_without_next_pointer_survives[path1-edit->]` | AssertionError: complete child lost without next pointer |
| `test_r2_complete_table_without_next_pointer_survives[path1-from_tiff-<]` | AssertionError: complete child lost without next pointer |
| `test_r2_complete_table_without_next_pointer_survives[path1-from_tiff->]` | AssertionError: complete child lost without next pointer |
| `test_r2_cut_array_keeps_whole_entries[path0-edit-<]` | ValueError: IFD entry table runs past block |
| `test_r2_cut_array_keeps_whole_entries[path0-edit->]` | ValueError: IFD entry table runs past block |
| `test_r2_cut_array_keeps_whole_entries[path0-from_tiff-<]` | AssertionError: cut IFD0 discarded all metadata |
| `test_r2_cut_array_keeps_whole_entries[path0-from_tiff->]` | AssertionError: cut IFD0 discarded all metadata |
| `test_r2_cut_array_keeps_whole_entries[path1-edit-<]` | AssertionError: cut child discarded whole entries |
| `test_r2_cut_array_keeps_whole_entries[path1-edit->]` | AssertionError: cut child discarded whole entries |
| `test_r2_cut_array_keeps_whole_entries[path1-from_tiff-<]` | AssertionError: cut child discarded whole entries |
| `test_r2_cut_array_keeps_whole_entries[path1-from_tiff->]` | AssertionError: cut child discarded whole entries |
| `test_r2_slong_carried_pointer_is_dropped_with_warning[edit-<]` | PASS (F-D limit control) |
| `test_r2_slong_carried_pointer_is_dropped_with_warning[edit->]` | PASS (F-D limit control) |
| `test_r2_slong_carried_pointer_is_dropped_with_warning[from_tiff-<]` | PASS (F-D limit control) |
| `test_r2_slong_carried_pointer_is_dropped_with_warning[from_tiff->]` | PASS (F-D limit control) |
| `test_r2_read_then_write_warns_once_per_dropped_entry[bad_value]` | AssertionError: read + write warned more than once per dropped entry |
| `test_r2_read_then_write_warns_once_per_dropped_entry[duplicate_d63]` | AssertionError: read + write warned more than once per dropped entry |
| `test_r2_read_then_write_warns_once_per_dropped_entry[unsupported_pointer]` | AssertionError: read + write warned more than once per dropped entry |

### R2 remediation and verification (seat 2)

F-A FIXED: `_read_entries` caches each completed source directory by its offset;
the ancestor check precedes the cache lookup. Every retained pointer shares
that directory object. `_write_entries` caches the object's new offset and
writes its fields once. `_apply_d63` likewise edits each shared Exif child
once, so duplicate pointers do not repeat dimension scans or duplicate-drop
warnings. Source pointer types/counts survive (SHORT still promotes only on
overflow under R1 F8). A=B=C=150 now gives 454 physical entries in exactly
three IFDs for edit/from_tiff and II/MM. This fixes shared CHILD amplification,
distinct from R1 F7 shared VALUES, which remains a named Limit.

F-B FIXED: bounds require only the two-byte count plus whole 12-byte entries;
the ignored source next-IFD pointer need not exist. Serialization always
reserves a zero next pointer. F-C FIXED under the new ruling: clamp the
declared count to whole entries remaining in the block, warn once with IFD
label and declared/kept counts, and carry those entries. Bad entry payloads
still drop individually; invalid child offsets/cycles isolate the child.
F-D is the existing 3/4/13-only pointer policy with four passing controls,
not a new fix. F-E report updated, including F-A FIXED and the one-sentence
F-D Limit. F-F FIXED by private keyword `edit(..., _warn=True)` and quiet
`sanitise(...)->edit(..., _warn=False)`; parser and D63 warning paths both
honor it. Actual writer edits remain loud. Warnings contain labels/tag IDs
or declared/kept counts, never value bytes.

Test-control changes, all inside the WP4.5 new test file:

- The three old child `table` cases (declared count 65535) now exercise a
  missing two-byte count via offset `len(block)-1`, named `missing_count`.
  Cut arrays are covered by the new F-C cases and are no longer child-fatal.
- The root raise case formerly containing a full count of 65535 now ends
  after one count byte, preserving the ruled invalid-root-offset control.
- `test_r1_child_table_fault_drops_child_only[edit/from_tiff]` is renamed to
  `test_r1_child_offset_fault_drops_child_only` and uses a past-EOF pointer.
  These six removed/replacement node IDs reflect F-C's amended contract;
  no existing test outside the owned file was edited in seat 2.
- First GREEN attempt: exit 1, 8 failed / 222 passed, `r2-first-green.log/xml`.
  Six failures were the superseded controls above; the other two were a
  secondary F-A test assertion inadvertently including Software's intentional
  D63 count change. Corrected to compare pointer types/counts/order only.
  The primary entry-count assertion and source fixture did not change, so
  all four original F-A RED failures remain applicable. These two secondary
  failures were test false positives, not additional product defects.

| Check | Exit | Actual result | Evidence under work/wp4.5/ |
| --- | --- | --- | --- |
| R2 RED on unchanged `3020648`, `-k r2` | 1 | 23 failed, 4 passed, 203 deselected, 1 warning in 28.46s | `r2-red.log/xml`; per-case table above |
| New file GREEN | 0 | 230 passed, 1 warning in 0.91s | `r2-green.log/xml` |
| Authorized combined light run, after Python formatting | 0 | 907 passed, 5 deselected, 133 warnings in 15.81s | `r2-light.log/xml` |
| Targeted `uv run --offline ruff check` | 0 | All checks passed! | `r2-ruff.log` |
| `uv run --offline mypy` | 0 | Success: no issues found in 141 source files | `r2-mypy.log` |
| Format the two changed Python files | 0 | 2 files reformatted | `r2-format.log` |
| Owned-file byte/scope/result audit | 0 | Exactly four owned files; ASCII/LF-only, final newlines, no trailing whitespace; diff check clean; JUnit confirms 27 RED / 230 GREEN / 907 light cases | `r2-final-audit.log` |

Light targets: all `tests/test_io_photo_*.py` (including the new file once),
`tests/test_photo_check.py`, `tests/test_wp41_photo_path.py` and
`tests/test_jobs_export_photo.py`. Every pytest run uses `PYTHONPATH=scripts`,
`--basetemp=work/wp4.5/tmp`, `-p sandbox_mkdir_shim`, `-p no:cacheprovider`, and
`-m "not gpu and not footage and not gui and not slow and not fullclip"`.
All runner output goes to files under `work/wp4.5/`. The added bad-value PNG
fixture produces one Pillow `Truncated File Read` UserWarning on the decoded
read side. The F-F assertions count product logger warnings separately and
require exactly one across read and write without clearing captured logs.
No warning suppression was applied to the pytest run itself.

Verification loop: suspected each R2 mechanism from the review; independently
confirmed with the existing code paths and actual RED failures; fixed in the
owned module; repeated the new-file and combined light checks with no further
failure. Reviewed the final product diff against F-A/B/C/D/F, warning privacy,
docstrings, source byte/type/count carry, and scope. No additional in-envelope
product defect found. No reviewer finding rejected; the secondary test false
positive is recorded above. No dependency/interface/writer/reader/PNG changes,
no existing-test change outside the owned file, no local-config change, no
footage access, no mailbox post, no commit and no write outside the worktree.
No register row or harness gate is required by the ruling.

Seat 2 yields one logical R2 remediation spanning product/tests/report/ledger;
dispatcher commits by the listed pathspec. No convergence/acceptance claim:
Reviewer A R3 runs next, then Reviewer B and final full parallel + impacted
serial nodes at the orchestrator's seat, per the owner's direction. Final
format/blob checks are also dispatcher-owned. Seat 2's depth is not supplied;
the dispatcher reads it at this boundary (binding window 258,400).

### R3 RED on unchanged c7c7360 product

HEAD e2df398 contains only the prior ledger commit; product code diff from c7c7360 was empty. Before any product fix: exit 1, **30 failed, 224 deselected in 2.25s**. Evidence: `work/wp4.5/r3-red.log/xml`.

Command: `PYTHONPATH=scripts uv run --offline pytest tests/test_io_photo_exif_bytes.py -k r3 --basetemp=work/wp4.5/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" --junitxml=work/wp4.5/r3-red.xml`.

R2's four A=B=C=150 cases are rewritten to expect duplicate pointer removal (156 physical entries, not 454), under the R3 design guard. R1's two distinct-child duplicate Exif cases now require only the first child and its D63 dimensions. These six amended cases retain the owned file boundary and explain six removed/replacement node IDs. New cases: eight overlapping-child constructions (P=200/N=400, two tags/routes/orders), four same-offset sibling cases, and twelve first-pointer/warning-count cases across the three pointer tags/routes/orders.

| Case | Actual pre-fix result |
| --- | --- |
| `test_r3_duplicate_exif_pointer_keeps_first_child_with_d63_dimensions[<]` | AssertionError: later Exif pointer retained |
| `test_r3_duplicate_exif_pointer_keeps_first_child_with_d63_dimensions[>]` | AssertionError: later Exif pointer retained |
| `test_r3_shared_child_duplicate_pointers_are_dropped[edit-<]` | AssertionError: duplicate pointer entries retained |
| `test_r3_shared_child_duplicate_pointers_are_dropped[edit->]` | AssertionError: duplicate pointer entries retained |
| `test_r3_shared_child_duplicate_pointers_are_dropped[from_tiff-<]` | AssertionError: duplicate pointer entries retained |
| `test_r3_shared_child_duplicate_pointers_are_dropped[from_tiff->]` | AssertionError: duplicate pointer entries retained |
| `test_r3_overlapping_children_keep_one_ifd_with_bounded_entry_count[34665-edit-<]` | AssertionError: more than one carried IFD for pointer tag |
| `test_r3_overlapping_children_keep_one_ifd_with_bounded_entry_count[34665-edit->]` | AssertionError: more than one carried IFD for pointer tag |
| `test_r3_overlapping_children_keep_one_ifd_with_bounded_entry_count[34665-from_tiff-<]` | AssertionError: more than one carried IFD for pointer tag |
| `test_r3_overlapping_children_keep_one_ifd_with_bounded_entry_count[34665-from_tiff->]` | AssertionError: more than one carried IFD for pointer tag |
| `test_r3_overlapping_children_keep_one_ifd_with_bounded_entry_count[34853-edit-<]` | AssertionError: more than one carried IFD for pointer tag |
| `test_r3_overlapping_children_keep_one_ifd_with_bounded_entry_count[34853-edit->]` | AssertionError: more than one carried IFD for pointer tag |
| `test_r3_overlapping_children_keep_one_ifd_with_bounded_entry_count[34853-from_tiff-<]` | AssertionError: more than one carried IFD for pointer tag |
| `test_r3_overlapping_children_keep_one_ifd_with_bounded_entry_count[34853-from_tiff->]` | AssertionError: more than one carried IFD for pointer tag |
| `test_r3_same_offset_siblings_are_parsed_per_label[edit-<]` | AssertionError: GPS parse discarded Exif Interop |
| `test_r3_same_offset_siblings_are_parsed_per_label[edit->]` | AssertionError: GPS parse discarded Exif Interop |
| `test_r3_same_offset_siblings_are_parsed_per_label[from_tiff-<]` | AssertionError: GPS parse discarded Exif Interop |
| `test_r3_same_offset_siblings_are_parsed_per_label[from_tiff->]` | AssertionError: GPS parse discarded Exif Interop |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent0-34665-edit-<]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent0-34665-edit->]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent0-34665-from_tiff-<]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent0-34665-from_tiff->]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent1-34853-edit-<]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent1-34853-edit->]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent1-34853-from_tiff-<]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent1-34853-from_tiff->]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent2-40965-edit-<]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent2-40965-edit->]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent2-40965-from_tiff-<]` | AssertionError: later carried pointer retained |
| `test_r3_duplicate_pointer_tags_follow_first_and_warn_per_later_entry[parent2-40965-from_tiff->]` | AssertionError: later carried pointer retained |

### R3 remediation and verification (seat 2, turn 3)

Design guard implemented as ruled: a parent-local set consumes the first
occurrence of each carried pointer tag in table order BEFORE pointer/value
validation. Every later occurrence is dropped without following it, with one
warning naming the parent IFD and tag ID. An unreadable first pointer never
falls back to a later duplicate. Only IFD0 can follow Exif/GPS, only Exif can
follow Interop, and the other labels cannot follow further children. Each
label can therefore be parsed at most once: four source tables in total.
Both the source-offset parse cache and identity write cache are removed,
along with the shared-child dimension deduplication set. The single Exif
child alone receives dimension edits. Same-offset siblings get independent
per-label lists; ancestor offsets remain cycles and drop that child alone.
F-C's whole-entry clamping, source type/count/value-byte carry, order, pointer
type retention/promotion and the rest of D63 are unchanged.

F-A and F-1 are FIXED by the guard, not banked as Limits. F7 shared VALUES,
already reproduced on the base, remains the only amplification Limit. The
entry-count bound is the corrected `written entries <= 4 * source bytes / 12
+ 5`, not a byte-size bound on potentially shared values. F-2's same-offset
case is fixed by removing the cache and keeping labels independent. F-3's
report now describes the actual guarded implementation, with the R2 cache
history explicitly superseded. F-4 has no change, as ruled.

The R3 RED roster has 30 cases: six rewritten controls and 24 new cases.
All 30 failed through assertions on the unchanged c7c7360 product, not fixture
errors. After the fix every case in the 254-case new file passes on the first
GREEN run. No review finding rejected as a false positive, no reopened item,
no revert. The rewritten A=B=C=150 case now retains 156 physical entries
(one Exif pointer, one Interop pointer, and all 150 non-pointer Interop fields)
and warns once for each of the 298 later structural pointers. The ordinary
duplicate-field and D63 duplicate controls remain green.

| Check | Exit | Actual result | Evidence under work/wp4.5/ |
| --- | --- | --- | --- |
| R3 RED, `-k r3`, product unchanged from c7c7360 | 1 | 30 failed, 224 deselected in 2.25s | `r3-red.log/xml`, per-case assertions above |
| New file GREEN | 0 | 254 passed, 1 warning in 0.88s | `r3-green.log/xml` |
| Authorized combined light run, after formatting | 0 | 931 passed, 5 deselected, 133 warnings in 15.46s | `r3-light.log/xml` |
| Targeted `uv run --offline ruff check` | 0 | All checks passed! | `r3-ruff.log` |
| `uv run --offline mypy` | 0 | Success: no issues found in 141 source files | `r3-mypy.log` |
| Format the two owned Python files | 0 | 1 file reformatted (tests), 1 file left unchanged | `r3-format.log` |
| Final read-only scope/byte/result audit and seven boundary probes | 0 | Four owned files only; ASCII/LF, final newlines, no trailing whitespace; diff check clean; JUnit 30 RED / 254 GREEN / 931 light; seven probes passed | `r3-final-audit.log` |

Light targets and marker expression are unchanged from R2: all
`tests/test_io_photo_*.py` (new file included once), `tests/test_photo_check.py`,
`tests/test_wp41_photo_path.py`, `tests/test_jobs_export_photo.py`;
`-m "not gpu and not footage and not gui and not slow and not fullclip"`.
All pytest runs use `PYTHONPATH=scripts`, `--basetemp=work/wp4.5/tmp`,
`-p sandbox_mkdir_shim` and `-p no:cacheprovider`. All runner output is routed
to work/wp4.5 files. The existing bad-value fixture's one separate Pillow
UserWarning remains; no pytest warning suppression was added.

Independent boundary probes, all synthetic and in memory: root-ancestor
cycles for Exif/GPS drop that child alone; unreadable-first-plus-valid-later
cases for all three pointer tags do not follow the later pointer and emit
two IFD/tag warnings; 14-byte and 10-byte empty IFD0 cases produce the five
mandatory D63 entries and satisfy the corrected +5 bound. These are seven
executed probes in `r3_final_audit.py`, not additional pytest case counts.

Verification loop: suspected the reviewed distinct-overlap and label-sharing
mechanisms; confirmed independently by code paths and RED structural/count
assertions; removed the caching approach under the simpler guard; new-file,
light, static and boundary checks pass. A final diff review checked the
four-table call graph, first-occurrence-before-validation behavior, source
entry byte carry, warning privacy, label-local D63 edits, cycle rule,
docstrings and scope. No additional in-envelope defect found. The earlier
exact-bound suspicion was confirmed and resolved only under the explicit
erratum, now quoted in the Round 3 section and report.

One logical guard remediation spans the four owned files. No writer/reader/
PNG/interface/dependency/config/fixture/harness changes, no other existing-test
edit, no footage read/write, no mailbox post, no commit and no write outside
the worktree. The granted R1 test is unchanged in seat 2. Supplied footage
and static evidence on c7c7360 and corrected depth are recorded above; this
cell performs no footage or full-suite gate. Reviewer A R4 runs after yield;
Reviewer B, final format/blob checks and the full parallel + impacted serial
gate remain at the orchestrator's seat. No convergence or acceptance claim.
If R4 blocks on this amplification class again, STOP to CHARC with the cap
recommendation, as ruled. Last dispatcher-supplied depth is 135,854 input
tokens; current depth is dispatcher-read at this boundary, window 258,400.
