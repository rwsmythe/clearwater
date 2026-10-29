# WP4.5 - EXIF byte fidelity: cumulative ledger

## Round 0 - STOP: the Image.Exif writer discards type pins

Recommended ruling: authorize the Q1(b) fallback. Alternatively, explicitly
approve assembling separately serialized, typed Pillow IFDs with explicit
nested-IFD offsets as Q1(a). No implementation of either alternative has begun.
The existing `Image.Exif.tobytes()` path cannot carry source type pins into its
fresh IFD objects, including Exif, GPS and Interop. A change in serialization
mechanism needs the dispatcher's/CHARC's ruling under Q1 before turn 2.

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
| 0 | Cell source trace + executed synthetic probe; not Reviewer A | 0 | 1 | 0 | 1 / 0 | 1 / 0 | 0 | 0 / 0 | STOP for mechanism ruling; no remediation begun |

- Suspected: the fresh IFD construction drops source type pins.
- Confirmed independently: source trace and parsed synthetic output agree for
  IFD0, Exif, GPS and Interop; bytes-only LensModel changes type and count.
- Rejected false positives: none recorded.
- Fixed: none; authorized scope this turn is the ledger only.
- Reviewer A transport/version/evidence: not supplied; no round has run.

### Dispatcher-read depth

| Turn / boundary | Depth supplied by dispatcher | Action |
| --- | --- | --- |
| Turn 1 / Round 0 | Not supplied | No estimate recorded; yield after ledger |
