# WP4.5 - EXIF byte fidelity: cumulative ledger

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
| T2 compatibility check | Executed existing test; not Reviewer A | 0 | 1 | 0 | 1 / 0 | 1 / 0 | 0 | Product rewrite + new regression tests; no compatibility remediation | STOP: existing test injects failure in removed Pillow dependency; existing tests not owned |

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
