# WP-T3 -- fixture checker hardening (closes DR-33 (a)-(d))

Scope: tests and tools only. Files: `tools/fixtures/stills.py`, `tools/fixtures/flicker.py`,
`tests/fixture_plugin.py` (`verify_generated` only), `tests/test_fixtures.py`. No file under
`tests/fixtures/` changed.

## The four checks

| Item | Check | What it reads |
|---|---|---|
| (a) | `stills.container_format`, `check_still_format`; `measure` sets `facts["format"]`; `_record` refuses a mismatch | the first bytes of the file: PNG signature, `FF D8 FF`, TIFF byte order mark, ISO-BMFF `ftyp` with major brand `heic` or `heix` |
| (b) | `stills.xmp_gps_findings` | raw bytes: four XMP markers (packet header URI, `adobe:ns:meta/`, EXIF namespace URI, `<?xpacket`) and every `GPS` + letters name, any prefix; names only, never a value |
| (c) | `stills.heif_primary_properties`, `check_heif_extents`; `measure` takes `irot`/`imir` from it | `pitm`, every `ipma` (item id width by version, association width by flags, essential bit masked, index 0 none), the `ipco` list; `ispe` against `stored_width/height` and, turned by `irot` 90/270, against the decoded size; property body lengths are checked |
| (d) | `flicker.probe_clip` merges both ffprobe calls' stderr; `STREAM_IDENTITY` gains `ffprobe_errors`; `packet_durations`, `duration_problem`, `identity_problems`; `build_clip` and `verify_generated` use them | packet durations against `1 / r_frame_rate` in ticks of `time_base`, both taken from the manifest's own stream facts (tolerance one tick); the manifest gains no field |

## Plants (each in `tmp_path`; each fails by name; the old check passes it)

- T2 a TIFF under `x.jpg` as kind `jpeg`; an `mp42` `ftyp` file as kind `heic`; `_record` raises. Old: manifest fields only.
- T4 XMP with prefixes `foo`/`ns0` holding only synthetic-zero `GPSLongitude`/`GPSAltitude`: findings name both and the namespaces. Main plant is an uncompressed PNG `iTXt` chunk (no packet header); a JPEG APP1 form is planted too. The old list finds nothing in the PNG form and only the `xap` header in the JPEG form (a JPEG APP1 packet's header contained `ns.adobe.com/xap`, so DR-33's wording "valid XMP with another prefix would pass" was only true of the GPS properties).
- T6 `heic-ad24-both` with the `irot` association zeroed in `ipma`: `irot is None, the manifest has 270`; `photo.heif_transforms` still says 270.
- T7 `heic-ad24-irot-only` with the `ispe` width edited: `ispe is (128, 96), the stored size is (64, 96)`; the old irot reader and manifest comparison pass it.
- Short `ispe` (8-byte body) before another box: refused with `needs 12`; without the check the width/height would be read from the next box.
- T9 the clip with its last 40 bytes cut: `ffprobe_errors is ['Truncating packet of size 1780 to 1740']`, alone once every other identity field is copied; the old tuple passes it.
- T10 the clip restamped with `-bsf:v setts=duration=17`: `packet_durations is [17], the declared rate gives 33.37 ticks`; pts hash, counts and rates equal, the old tuple passes it.
- Mutation checks (checker deliberately broken, the named test fails): packet-call errors dropped, brand rule relaxed, GPS regex narrowed, `ipma` requirement removed, body-length check removed.

## Evidence

- 86 committed files: no scan hit, no format mismatch; 22 HEICs agree with the manifest on `irot`/`imir`, extents empty.
- Real clip `ad14-flicker`: 90 packets, all duration 33; `identity_problems` empty; `ffprobe_errors` `[]`.
- `tests/test_fixtures.py`: 347 passed, 0 skipped. ruff check, ruff format --check, mypy clean.
- Byte identity: `git diff --quiet 9753b7b -- tests/fixtures` succeeds; `test_committed_files_match_the_manifest`, `test_regenerated_manifest_is_byte_identical` and `test_stills_files_and_mask_regenerate_byte_identically` pass.

## Limits (stated, not hidden)

- The XMP scan is over raw ASCII/UTF-8 bytes: UTF-16 XMP and zlib-compressed PNG `iTXt` XMP are not scanned. Trigger for the debt row: the first PNG sample carrying an `iTXt` chunk, or XMP writing by any generator.
- `container_format` accepts only major brands `heic`/`heix`; widen when a real camera brand is committed.
- A real camera HEIC (grid, thumbnails, auxiliary items) is outside the envelope: the `ipma` reader handles a primary that is not the first item, but no such file is committed. A truncated `ipma` may raise `struct.error` rather than `ValueError`.
- A packet with no reported duration reads as -1 and so fails the duration rule.
- Tests build plants with the private helpers `stills._child`, `stills._boxes`, `stills._chunk`.
