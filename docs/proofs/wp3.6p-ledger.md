# WP3.6P cumulative ledger

## Dispatch and current boundary

- Package: WP3.6P, CODEX lane, STRONG tier; CHARC's FINAL rulings govern.
- Dispatch base verified: `c3bf602fe9ac94cd5df25499d97f3a2bc439bb72`.
- Current boundary: turn 5, Reviewer A round 1 REMEDIATED in the owned tool,
  tests and ledger; Reviewer A round 2 is NOT RUN. Turn 4's adjudication was
  committed as `f2396b0e`. Turn 1's ledger was committed
  as `6cc7cdb`; RED as `a66eea6`.
  No owner photo was opened by the cell in any turn.
- `uv sync`: already run by the dispatcher before dispatch, as stated in the
  binding turn-1 instructions. Not repeated: this sandbox cannot reach the index.
- Initial `git status --short`: empty. The existing isolated worktree is retained.
- At round 0, no STOP or question remained. CHARC `e40b0d7b06ee9af8`
  (2026-10-30T04:46:00Z)
  RE-RULES Q3: FFmpeg default composed primary as delivered is the oracle.
  The thumbnail is a recorded second witness, never the pass criterion.
- Current handoff: YIELD for Reviewer A round 2. CHARC resolved R1-QA/QB in
  `d9133089b58091d8`; the ruling and remediation evidence are recorded below.
  No product defect is asserted from a planted instrument control.
- No real-photo acceptance claim, measurement, review convergence or gate pass is
  made at this boundary. All requests below are NOT RUN by this cell.

## Round-0 source map on c3bf602

These are current-base anchors, not the brief's earlier-base line numbers. Each
row names the mechanic and the surface it supports. No footage was inspected.

| Mechanic / current anchor | Surface / consequence |
|---|---|
| `tools/photo_check.py:44` `PHOTO_SUFFIXES`; `:54-73` `collect` | Recursive photo selection; explicitly named files also accepted. |
| `tools/photo_check.py:47` `WORK_SUBDIR`; `:50` `D63_CHANGED` | Existing instrument writes under `wp3.6`; four EXIF fields may change. Neither constant is edited here. |
| `tools/photo_check.py:76-107` `_heic_layout` | Primary item, grid, irot/imir, clap/ispe, auxiliary/thumbnail ids, raw Orientation and library format facts. |
| `tools/photo_check.py:110-126` `_color_record` | Primaries, transfer, assumed, depth, ICC presence/description/md5/validity. |
| `tools/photo_check.py:129-181` `round_trip` | Product-writer I/O-only PNG16 sample/ICC/D63/kept-field comparison; MakerNote/GPS presence checks at `:178-179`. Does not exercise correction or runner. |
| `tools/photo_check.py:184-224` `inspect`, especially `:194` | Raw local records contain an absolute source path. Never copy these objects into committed-facing evidence. |
| `tools/photo_check.py:239-252` `make_guard`; `:255-300` `run`; `:303-332` `main` | Existing guarded output root, per-photo local records, summary and exit behavior. Tool remains unchanged. |
| `tests/test_photo_check.py:132-148` real-photo test; `:146` refusal allowance | Existing serial witness permits unsupported/unreadable verdicts. New instrument must reject any owner-photo refusal rather than infer all-read from this test. |
| `tools/local_config.py:19` `VIDEO_EXTENSIONS`; `:152-158` `find_footage_file` | Video-only lookup cannot select a photo. Resolve photo basenames under configured `Phone`, or use `photo_check.collect`. |
| `src/clearwater/io/photo/reader.py:209-219` `heic_tag_to_apply` | Product applies raw EXIF only without primary irot. Never use this function to construct the oracle. |
| `src/clearwater/io/photo/reader.py:226-236` `_check_decoded_size`; `:239-283` `_read_heic` | Current reader uses `open_heif`, validates primary size, reads raw metadata, sanitises EXIF and returns the additional tag transform. This is the current mechanic even though AD-24's decision text names the Pillow opener. |
| `src/clearwater/io/photo/heif_boxes.py:177` `read_layout` | Product's primary properties are associated through pitm/ipma/ipco. Layout facts can be recorded; the product AD-24 decision is not the pose oracle. |
| `tests/test_wp41_photo_path.py:324-339` HEIC AD-24 test | Fixture output matches generated upright pixels with mean error <6/255, other same-shape poses >10/255; mismatched shapes distinguish the remaining poses. |
| `src/clearwater/io/photo/color.py:37-94` `describe_color` | ICC, PNG sRGB and HEIC nclx are recognised; otherwise bt709/srgb with assumed=True. EXIF ColorSpace is not consulted. |
| `src/clearwater/io/photo/writer.py:36-56` `built_in_profile` | Tagged, profile-less HEIC may receive built-in sRGB/P3; untagged JPEG does not. Source ICC is otherwise preserved. |
| `tools/headless_export.py:669-715` `parameters_for`; `:1199`, `:1201`, `:1221`, `:1226` | Neutral parameters and CLI bit depth, force CPU, neutral and record flags. |
| `tools/headless_export.py:1042-1075` `record_object` | Each photo item's `device` is the job reason, not the video-only observer. Free-form warnings/failures are unsuitable for committed summaries. |
| `tests/test_wp41_photo_path.py:344-356` `v9_difference` | Quantised reference uses writer clipping/round-half-even; both quantised and raw errors are in 1/255 units. |
| `src/clearwater/core/backend.py:1001-1043` `select_backend` | Force CPU first; otherwise GPU only when estimate < free bytes. Equal estimate/free selects CPU; CPU reason contains rounded figures. |
| `src/clearwater/core/memory.py:45-67` `memory_estimate_bytes` | Current estimate for height, width and method c3. Use this function, not an old prototype formula. |
| `tools/prototype/bench.py:1004-1019` `_memory_record`; `:1270-1304` `_GpuSampler`; `:165` `IMAGE_SUFFIXES` | Portable RSS/optional peak_wset pattern and nvidia-smi sampling precedent; prototype cannot read HEIC. |
| `pyproject.toml:40` psutil; `:75-81` markers; `:100-104` mypy | psutil already granted; footprint tests serialize; tools are in strict mypy's files. No dependency or configuration edit needed. |
| `docs/reports/inventory-2026-10-29.md:89`, `:111-113` | 73 photos, 62 HEIF + 11 JPEG, all primary images 8-bit; largest stored size 5712x4284, shared by 38 photos. Header facts, not this package's decode results. |
| Inventory `:195-219`, especially `:208-214` | Phone-relative naming and seven HEIC inventory rows collapse to irot classes 0:23, 90:3, 180:20, 270:16. |
| Inventory `:223-248`, `:366-388`, `:392-397` | JPG-A:2, JPG-Z:8, JPG-M:1; Z/M are candidates only. All 62 HEIC irot/EXIF pairs agree. No tag-only or irot-only owner witness. |
| Inventory `:361-364` | Scene identity cannot be inferred from selected tags. Above-surface identity stays with owner's visual review. |
| `docs/reports/wp4.5-exif-bytes.md:195-207` | Prior I/O-only witness, including 73-photo node at 3020648: 1 passed in 268.01 s. Historical evidence, not rerun evidence. |

Additional governing anchors re-located:

| Current anchor | Binding content |
|---|---|
| `docs/clearwater-implementation-plan.md:66-102`, `:362` | Environment/paths/exclusive hardware/file ownership/DoD; V15 remains WP5.2. |
| `docs/underwater-correction-spec.md:62`, `:91`, `:101`, `:148-149` | D24, D53, D63, D110/D111. |
| Spec `:363-368`, `:410`, `:439`, `:442-445`, `:465` | D63 metadata details, G10, portability, N4 and dependency licensing. |
| Spec `:486`, `:490`, `:496`, `:567` | V5, V9, V15, owner resolution open item. This package changes none of these words. |
| `docs/decisions.md:20`, `:33` | AD-11 and below-source-depth clarification; AD-24's provisional status is CHARC's accept decision. |
| `docs/debt-register.md:15-16`, `:51-52` | DR-6 pixel validation, DR-7 trigger, DR-42(a)/(c), DR-43. No register edit owned. |
| `docs/charc-state.md:33-34`, `:134-135`, `:480-488`, `:243-253` | Current queue, original commission relocated from old :223-226, and FINAL ruling summary. Dispatch prompt's verbatim rulings govern. |
| `docs/briefs/wp3.6-brief.md:219-220`, `:278-284` | Original follow-on approval and owed real-photo work; lane sizing superseded by FINAL ruling. |
| `docs/reports/wp4.1-photo-path.md:159-169`; `docs/proofs/wp4.1-accept.md:53` | Owed HEIC V5/V9, AD-24 and largest-photo legs; viewers stay WP5.1. |
| `docs/reports/wp1.6-gate-report.md:118-119`, `:203`; `docs/briefs/wp1.2b-brief.md:82-85` | Result 2 pending photo row and estimate/free/peak/fallback reporting form. |
| `CLAUDE.md:29-30`; `docs/review-gate-clearwater.md:12-85`, `:87-223` | Owner classification boundary and disk constraint; other-model reviews, convergence/five-round rule, B before ONE two-leg gate. |
| `tools/fixtures/stills.py:375` `heif_primary_properties`; `:865-891` AD24 generator | Independent fixture-side primary-property parser and known asymmetric upright source; oracle never calls product tag-to-apply. |
| `src/clearwater/io/photo/exif.py:289` `sanitise`, `:390` `describe`, `:414` `has_thumbnail` | Detect raw-present/product-absent sanitise drops; compare values privately and emit only names/counts/booleans. |
| `tools/spike_io/guard.py:53` `WriteGuard` | Existing guard reused at the new `wp3.6p` root. No change to guard or photo_check. |

## Tool design (round 0)

### CLI and write boundary

`tools/photo_verify.py` will have three required subcommands. Shared arguments:
`--config PATH` (default local config), `--class-map PATH` (required for owner
runs), `--name RUN` (a new single-component run name). Source selection is the
class map, with optional `--files NAME [NAME ...]` to select listed basenames.
Basenames resolve below configured `footage_path / 'Phone'`; synthetic library
tests pass explicit source paths and a tmp_path-backed config/guard.

- `orientation`: `--max-side 256`. Selects HEIC only, runs the independent
  FFmpeg-default pose comparison plus the recorded thumbnail witness, and
  records all eight scores, dimensions and discrimination margins. A wrong-size
  candidate is marked shape-mismatch, not silently omitted.
- `export`: `--bit-depth {8,16}` (required), `--force-cpu` (default false),
  `--representatives-only` (select exactly seven class representatives). Every
  export uses the runner with neutral parameters, selected depth and its default
  device unless explicitly forced for synthetic tests. This yields 73 runs at
  16 bits and seven representative runs at 8 bits at the seat.
- `memory`: `--file NAME` (one mapped file), `--force-cpu`, `--bit-depth {8,16}`
  (default 16), `--exclusive` (required declaration at the CLI). Uses c3 DEFAULT
  correction parameters, not neutral parameters,
  to measure the full processing memory path. Default-device and forced-CPU legs
  run in separate fresh runner processes in the EXCLUSIVE seat window.

All persistent outputs go through WriteGuard rooted at
`<configured working_path>/wp3.6p/<subcommand>/<name>/`. Guard source/output
separation and every PNG, record, log, settings directory and deletion. Refuse
existing run folders, unsafe names, traversal, duplicate entries, unlisted files,
empty selections, invalid classes, map count mismatches and escaping paths.
The runner always gets `--out`, guarded `--record`, and isolated guarded
`--settings-dir`; it never gets `--beside-source`. No user settings are changed.
All input opens are read-only. Output paths are not printed by the wrapper.

Before each owner run, record disk free bytes and require at least 20,000,000,000
free bytes, plus the planned retained-output budget derived from round 0.
Check again before each export; stop rather than prune other evidence. Export
only deletes its own guarded PNG after successful measurement and hashing.
Retain the seven representative 16-bit PNGs. The seven 8-bit validation PNGs are
measured and removed; this keeps exactly seven representative PNGs across both
export runs. Failed-check output is kept for diagnosis and the run stops.

Exit status design: 0 = all selected checks passed; 1 = read/check/runner/oracle
failure (stop at the first failed photo, with partial counts); 2 = invalid
arguments/map/empty selection; 3 = guard/disk refusal. No free-form exception
text reaches stdout or committed-facing summaries. A valid read with a failed
pose discrimination is a failed check, never a pass by nearest-pose alone.

### Class-map schema (dispatcher writes JSON under work/)

Seven exact keys, no unlisted or duplicate photo names. Each `files` entry and
`representative` is a bare filename relative to Phone, not a path. Counts below
are inventory expectations to validate, not newly measured reads.

```json
{
  "schema": 1,
  "classes": {
    "HEIC-0": {"files": ["IMG_6703.HEIC"], "representative": "IMG_6703.HEIC"},
    "HEIC-90": {"files": ["IMG_6718.HEIC"], "representative": "IMG_6718.HEIC"},
    "HEIC-180": {"files": ["IMG_6690.HEIC"], "representative": "IMG_6690.HEIC"},
    "HEIC-270": {"files": ["IMG_6720.HEIC"], "representative": "IMG_6720.HEIC"},
    "JPG-A": {"files": ["IMG_6751.JPG"], "representative": "IMG_6751.JPG"},
    "JPG-Z": {"files": ["IMG_6791.JPG"], "representative": "IMG_6791.JPG"},
    "JPG-M": {"files": ["IMG_6794.JPG"], "representative": "IMG_6794.JPG"}
  }
}
```

This is a SCHEMA EXAMPLE with only representatives, not the runnable full map.
Expand `files` from inventory :208-214 and :237-248 to these exact counts:

| Class | Files | Candidate handling |
|---|---:|---|
| HEIC-0 | 23 | Regular class |
| HEIC-90 | 3 | Regular class |
| HEIC-180 | 20 | Regular class |
| HEIC-270 | 16 | Regular class |
| JPG-A | 2 | Regular class |
| JPG-Z | 8 | Pre-corrected candidate, own row |
| JPG-M | 1 | Pre-corrected candidate, own row |

No metric pools Z/M into regular-photo rows. A total selected/attempted count may
show 73 for accounting, but carries no pooled pass/error/colour statistic.
No pixels are classified as above-surface, underwater or visually corrected.

### Oracle and per-photo record

FFmpeg oracle, per CHARC's replacement ruling: decode the PRIMARY using FFmpeg
9.0.2 DEFAULT stream selection, no `-map`, `-frames:v 1 -update 1`,
`-map_metadata -1 -pix_fmt rgb24`. Use the resulting pixels AS DELIVERED. Never
add `-noautorotate`, turn the result by irot/EXIF again, or select a tile by map.
Validate primary dimensions; FFmpeg composes the tile grid and applies its own
transform. FFmpeg's HEIF demuxer/HEVC decoder and the product's pillow-heif /
libheif decode plus Python AD-24 selection share no AD-24 code. The report must
name these libraries and describe the independent implementations explicitly.

The four synthetic fixtures RECORD and ASSERT FFmpeg's honoured rule rather
than assuming it. Reading their generator predicts irot-only handling; the
cell's light default-decode probe confirmed it: both and irot-only are upright,
exif-only stays stored, neither stays upright. FFmpeg does NOT honour an
EXIF-only Orientation. Compare each default decode with its known expected pose
from the asymmetric generated scene. Separately compare the product read with
the generated upright scene on ALL four fixtures. A correct tag-only product
read deliberately DISAGREES with FFmpeg; an EXIF-never mutant agrees with
FFmpeg but fails the generated-reference control. The tests retain both facts,
not a compensating transform that conceals the oracle's limitation.

The HEIC thumbnail through pillow-heif/libheif is a SECOND independent item
witness relative to the product's EXIF selection, recorded for every photo as
`thumbnail_witness` (availability, decoded size, pose scores and fixed failure
code). Record missing or discordant thumbnail evidence without changing the
FFmpeg-based pass criterion. It is not a second independent codec from the
product: the implementations compared for the primary are FFmpeg and libheif;
the thumbnail is additional independently transformed item evidence. The
report says two decoders agree on pose where measured; it does not claim three
independent decoders. Thumbnail fallback is DECLINED because FFmpeg CAN decode
the Apple primary. Never call `heic_tag_to_apply` to build an oracle.

Compare the product read with the upright oracle and all seven other dihedral
poses at a common small size, preserving aspect ratio. Record mean absolute
RGB differences in 1/255 units, the winning pose, upright error, nearest-other
error, margin and shape mismatches. Synthetic fixtures retain the established
<6 upright / >10 other-pose bounds. Owner comparisons use the same explicit
bounds, not an automatically relaxed threshold: a primary/oracle failure is a
failed check and STOP. Thumbnail scores are recorded without gating that check.

Per-photo allow-listed record groups:

| Group | Fields (scalars, enums or explicitly typed lists only) |
|---|---|
| Identity | schema, command, file (bare Phone-relative name), class, candidate_group (none/Z/M), read_ok, failure_code |
| Format | source_format, source_bytes, stored_size, decoded_size, source_bit_depth, orientation_tag |
| HEIC | primary_type, grid, irot, imir, clap, ispe, auxiliary_count, thumbnail_count; no auxiliary payload |
| Colour | primaries, transfer, assumed, icc_present, icc_description, icc_valid, icc_bytes, icc_md5 |
| EXIF | raw_exif_present, exif_present, sanitise_dropped, fields_before/after (names), field_count_before/after, changed_kept_fields (names), gps_ifd_present, gps_kept, maker_note_present, maker_note_kept |
| Orientation | oracle_kind (ffmpeg-default), oracle_size, scores_by_pose, shape_mismatches, winning_pose, upright_mean_255, nearest_other_mean_255, margin_255, orientation_ok, thumbnail_witness (availability, size, scores, fixed failure code) |
| Export | requested_depth, output_depth, png_bytes, png_md5, retained, device_reason, runner_exit, v5_ok, d53_ok, orientation_normal, software_ok, dimensions_ok, thumbnail_absent, icc_expected_present, icc_equal, primaries_equal, transfer_equal, kept_fields_equal, v9_ok, quantised_max_255, quantised_mean_255, raw_max_255, raw_mean_255, failed_checks |
| Memory | method, force_cpu, estimate_bytes, device_free_before_bytes, device_total_bytes, estimate_exceeds_free_before, device_reason, automatic_fallback, forced_cpu, rss_baseline_bytes, rss_tree_peak_bytes, os_peak_working_set_bytes, device_used_baseline_bytes, device_used_peak_bytes, rss_samples, device_samples, sample_intervals_s, sampler_errors, ram_limit_bytes, device_limit_bytes, ram_within_limit, device_within_limit, runner_exit, measured_at_utc, exclusive |

Memory samplers start before runner processing and take a final sample. Parent
tool obtains only dimensions before spawning the runner, avoiding a full extra
owner-photo decode in the measuring parent. RSS samples sum simultaneous RSS
for the tool/runner process tree, keeping the maximum of the sum rather than
summing each process's separate peak. Optional `peak_wset` is read via getattr,
None elsewhere. nvidia-smi samples device-wide used memory, explicitly including
other device use; missing readings stay null with fixed sampler error codes.
Free device memory is the separately labelled pre-run reading, not claimed to
be the exact instant of select_backend's internal query. The actual selection
comes from the runner item's device reason. Any missing required memory figure
prevents a complete Result 2 claim. Compare RAM with 16,000,000,000 bytes and
graphics memory with 8,188 * 2**20 bytes; also show MiB for auditability.

Export V5 reads IHDR/iCCP/eXIf independently from the written PNG, rather than
trusting metadata reported by the runner. Compare source ICC bytes or the
independently pinned D53 built-in; untagged JPEG's expected profile is absent,
recorded as such (Q8's ruled colour-warning observation, never claimed as an
embedded ICC pass). Compare all kept EXIF fields in memory, including private
values, then emit only names, counts and booleans. D63 exceptions are exactly
the existing four changed fields plus discarded thumbnail/HEIC auxiliaries.
The absence of raw EXIF versus a sanitise drop is distinguished independently.
V9 uses the full runner output: quantise the decoded source using the writer's
clip/round-half-even rule at requested depth, and record raw errors as well.
AD-11 max <=2/255 and mean <=0.2/255 are asserted against the quantised reference;
also assert raw errors for all 16-bit exports and 8-bit sources.

### Summary privacy boundary

Construct each record and summary by explicit nested allow-lists and leaf type
checks, never by deleting a few private keys from a raw record. Summary keys:
`schema`, `command`, `selected`, `attempted`, `complete`, `classes`, `records`,
`disk_free_before_bytes`, `disk_free_after_bytes`, `exit_code`. `records` contains
only the groups/fields listed above. Per-class aggregates contain only class,
selected/attempted/read_ok/read_failed counts, orientation/V5/D53/V9 pass/fail
counts, assumed_count, sanitise_drop_count, layout_counts, colour_counts and
max/mean error statistics with their depth and denominator. Z and M stay separate.

No absolute path, config contents, EXIF value, camera/editor string, MakerNote
content, location or serial is a field in that schema. ICC descriptions and
Orientation/irot are the brief's explicit permitted format exceptions. Software
is only a boolean equality result. Device reasons are constrained to the backend
reason grammar (fixed strings or numerical estimate/free forms). Failures/checks
are fixed codes or EXIF field NAMES; raw warnings, exception strings, runner
records and FFmpeg stderr are never promoted into the summary. stdout prints
this same safe summary only, encoded ASCII. Local raw runner logs remain guarded,
ignored evidence and are not committed or quoted into the return report.

## R0-O historical RUN REQUEST: tile evidence VOID

RUN AT THE SEAT, 2026-10-30T04:42:08Z; not run by the cell. This original request
is preserved as the exact historical recipe with the seat's psutil fix folded
in. Its mapped tile-level pose evidence is VOID and MUST NOT be rerun as the
orientation oracle. CHARC's replacement mechanism above governs. Planning
allowance: 1-5 minutes for two photos and raw/default decode pairs, not a measured
timing claim. Run one heavy job at a time. This block uses no hard-coded footage
path. Every output is worktree-relative under `work/wp3.6p/r0/`. Refuse reruns
over existing artifacts rather than overwrite or delete them.

```powershell
@'
import json
import subprocess
import sys
from pathlib import Path
import numpy as np
import pillow_heif
import psutil
from PIL import Image
sys.path.insert(0, str(Path('tools').resolve()))
from local_config import load_local_config
from spike_io.guard import WriteGuard
from fixtures.stills import heif_primary_properties
from clearwater.io.photo.heif_boxes import read_layout

cfg = load_local_config()
root = Path('work/wp3.6p/r0').resolve()
guard = WriteGuard(root=root, footage=cfg.footage_path)
guard.check(root)
root.mkdir(parents=True, exist_ok=True)
target = guard.check(root / 'oracle-facts.json')
assert not target.exists(), 'use a fresh request folder for a rerun'
free_before = psutil.disk_usage(str(root)).free
assert free_before >= 20_000_000_000, 'STOP: below 20 GB free'
records = []
for name in ('IMG_6690.HEIC', 'IMG_6720.HEIC'):
    source = cfg.footage_path / 'Phone' / name
    data = source.read_bytes()
    props = heif_primary_properties(data)
    layout = read_layout(data)
    command = ['ffprobe', '-v', 'error', '-show_entries',
        'stream=index,id,codec_name,width,height:stream_disposition=default:'
        'stream_side_data=side_data_type,rotation,displaymatrix',
        '-of', 'json', str(source)]
    probe = subprocess.run(command, capture_output=True, timeout=120)
    guard.check(root / (name + '.probe.stderr')).write_bytes(probe.stderr)
    parsed = json.loads(probe.stdout) if probe.returncode == 0 else {}
    streams = []
    for stream in parsed.get('streams', []):
        fact = {k: stream[k] for k in
            ('index', 'id', 'codec_name', 'width', 'height') if k in stream}
        fact['side_data'] = [{k: side[k] for k in
            ('side_data_type', 'rotation', 'displaymatrix') if k in side}
            for side in stream.get('side_data_list', [])]
        streams.append(fact)
    stored = list(props['ispe'])
    turned = stored[::-1] if props.get('irot') in (90, 270) else stored
    full = [s for s in streams if [s.get('width'), s.get('height')] in (stored, turned)]
    indices = [s['index'] for s in full] or [0]
    attempts = []
    for index in indices:
        for mode in ('raw', 'auto'):
            png = guard.check(root / f'{name}.s{index}.{mode}.png')
            assert not png.exists(), 'refusing an existing output'
            args = ['ffmpeg', '-nostdin', '-hide_banner', '-loglevel', 'error', '-n']
            if mode == 'raw':
                args += ['-noautorotate']
            args += ['-i', str(source), '-map', f'0:{index}', '-frames:v', '1',
                '-map_metadata', '-1', '-pix_fmt', 'rgb24', str(png)]
            done = subprocess.run(args, capture_output=True, timeout=120)
            guard.check(root / f'{name}.s{index}.{mode}.stderr').write_bytes(done.stderr)
            size = None
            if done.returncode == 0 and png.exists():
                with Image.open(png) as image:
                    image.load()
                    size = list(image.size)
            attempts.append({'stream': index, 'mode': mode,
                'exit': done.returncode, 'decoded_size': size})
    pose_scores = []
    poses = {2: Image.Transpose.FLIP_LEFT_RIGHT, 3: Image.Transpose.ROTATE_180,
        4: Image.Transpose.FLIP_TOP_BOTTOM, 5: Image.Transpose.TRANSPOSE,
        6: Image.Transpose.ROTATE_270, 7: Image.Transpose.TRANSVERSE,
        8: Image.Transpose.ROTATE_90}
    for index in indices:
        raw_path = root / f'{name}.s{index}.raw.png'
        auto_path = root / f'{name}.s{index}.auto.png'
        ok_modes = {a['mode'] for a in attempts
            if a['stream'] == index and a['exit'] == 0}
        if ok_modes != {'raw', 'auto'}:
            continue
        with Image.open(raw_path) as opened:
            raw_image = opened.convert('RGB')
        with Image.open(auto_path) as opened:
            auto_image = opened.convert('RGB')
        auto_image.thumbnail((256, 256), Image.Resampling.LANCZOS)
        reference = np.asarray(auto_image, dtype=np.float64)
        scores = {}
        for pose in range(1, 9):
            image = raw_image.copy() if pose == 1 else raw_image.transpose(poses[pose])
            image.thumbnail((256, 256), Image.Resampling.LANCZOS)
            pixels = np.asarray(image, dtype=np.float64)
            scores[str(pose)] = (float(np.abs(pixels-reference).mean())
                if pixels.shape == reference.shape else None)
        pose_scores.append({'stream': index, 'raw_to_auto_mean_255': scores})
    thumbnail_sizes = []
    thumbnail_error = None
    try:
        heif = pillow_heif.open_heif(str(source), convert_hdr_to_8bit=False)
        primary = heif[heif.primary_index]
        for index in range(len(primary.info.get('thumbnails', []))):
            thumb = primary.get_thumbnail(index).to_pillow()
            thumb.load()
            thumbnail_sizes.append(list(thumb.size))
    except Exception as error:
        thumbnail_error = type(error).__name__
    records.append({'file': name, 'grid': layout.is_grid,
        'stored_size': stored, 'transformed_size': turned,
        'irot': props.get('irot'), 'imir': props.get('imir'),
        'thumbnail_count': len(layout.thumbnail_ids),
        'probe_exit': probe.returncode, 'streams': streams, 'attempts': attempts,
        'raw_auto_pose_scores': pose_scores, 'thumbnail_sizes': thumbnail_sizes,
        'thumbnail_error_type': thumbnail_error})
facts = {'disk_free_before_bytes': free_before,
    'disk_free_after_bytes': psutil.disk_usage(str(root)).free, 'records': records}
target.write_text(json.dumps(facts, indent=2, ensure_ascii=True) + '\n', encoding='ascii')
print('R0-O: format facts recorded; return only oracle-facts.json facts')
'@ | uv run python - > work/wp3.6p/r0/oracle-request.log 2>&1
```

`oracle-facts.json` recorded: primary grid/non-grid and associated irot/imir;
stored/transformed dimensions; which streams FFmpeg exposes; its rotation side
data; raw/default decoding EXIT and dimensions; all eight raw-to-default pose
scores; thumbnail item count and decoded sizes for fallback. For a non-mirrored
source the associated irot predicts pose 1/8/3/6 for 0/90/180/270 respectively.
The numeric raw-to-default comparison tests that prediction without a visual
look check. These TILE-LEVEL scores are VOID: no full-size stream was found,
so stream 0 was one tile. The default-selection extra probes, not this request's
mapped output, established primary decoding. FFmpeg's transformed result was
identical with and without noautorotate, so a further irot would turn it twice.

## R0-E historical RUN REQUEST: one largest-size neutral runner export

RUN AT THE SEAT, 2026-10-30T04:43:51Z; not run by the cell. Selected file:
`IMG_6690.HEIC`, inventory 5712x4284. Planning allowance: 1-5 minutes for this
neutral export; this request obtains the actual wall time needed for Q5/Q9.
It is a timing observation: schedule alone, nothing else heavy. No claim on the
full c3 memory path is drawn from a neutral export.

```powershell
@'
import json
import subprocess
import sys
import time
from pathlib import Path
import psutil
sys.path.insert(0, str(Path('tools').resolve()))
from local_config import load_local_config
from spike_io.guard import WriteGuard

cfg = load_local_config()
root = Path('work/wp3.6p/r0').resolve()
guard = WriteGuard(root=root, footage=cfg.footage_path)
guard.check(root)
root.mkdir(parents=True, exist_ok=True)
record = guard.check(root / 'record.json')
facts_path = guard.check(root / 'export-facts.json')
out = guard.check(root / 'out')
settings = guard.check(root / 'settings')
assert not record.exists() and not facts_path.exists() and not out.exists()
assert not settings.exists(), 'fresh default settings required'
free_before = psutil.disk_usage(str(root)).free
assert free_before >= 20_000_000_000, 'STOP: below 20 GB free'
out.mkdir()
settings.mkdir()
command = ['uv', 'run', 'python', 'tools/headless_export.py',
    str(cfg.footage_path / 'Phone' / 'IMG_6690.HEIC'),
    '--neutral', '--bit-depth', '16', '--out', 'work/wp3.6p/r0/out',
    '--record', 'work/wp3.6p/r0/record.json',
    '--settings-dir', 'work/wp3.6p/r0/settings']
moment = time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
start = time.perf_counter()
with guard.check(root / 'runner.stdout').open('wb') as stdout, \
     guard.check(root / 'runner.stderr').open('wb') as stderr:
    done = subprocess.run(command, stdout=stdout, stderr=stderr)
elapsed = time.perf_counter() - start
raw = json.loads(record.read_text(encoding='utf-8')) if record.exists() else {}
items = raw.get('items', [])
pngs = list(out.glob('*.png'))
facts = {'file': 'IMG_6690.HEIC', 'measured_at_utc': moment,
    'runner_exit': done.returncode, 'wall_seconds': elapsed,
    'disk_free_before_bytes': free_before,
    'disk_free_after_bytes': psutil.disk_usage(str(root)).free,
    'counts': raw.get('counts', {}),
    'device_reason': items[0].get('device') if len(items) == 1 else None,
    'png_count': len(pngs), 'png_bytes': [p.stat().st_size for p in pngs]}
facts_path.write_text(json.dumps(facts, indent=2, ensure_ascii=True) + '\n', encoding='ascii')
print('R0-E: export facts recorded; return only export-facts.json facts')
'@ | uv run python - > work/wp3.6p/r0/export-request.log 2>&1
```

Return EXIT, wall seconds, device reason, PNG count/bytes, counts and free disk
before/after; confirm the exclusive conditions. Do not return raw runner
warnings, settings, EXIF, PNG metadata or source paths. No file is deleted.
Use the measured PNG size for the 73-output photo_check budget (which uses its
unchanged `wp3.6` root) and retained representatives plus transient export budget.
Measured wall time sizes neutral-export scheduling; it does not predict default
correction memory-leg duration.

## Round-0 seat evidence and replacement ruling

Evidence below was supplied by the dispatcher, 2026-10-30 04:41Z-04:45Z.
The cell did not open owner files or the dispatcher-written class map.

- Seat edit folded into this commit: R0-O initially raised `TypeError` because
  this psutil requires a string, not WindowsPath, in disk_usage. The dispatcher
  reran with `psutil.disk_usage(str(root))`; all four calls in the two historical
  snippets now match that seat fix. Initial failure log:
  `work/wp3.6p/r0/oracle-request.failed-typeerror.log`. The tool must pass str too.
- R0-O: each photo exposed 61 HEVC streams, none at primary size. IMG_6690
  streams included 640x896 tiles and a 416x312 thumbnail. IMG_6720 streams
  included 512x512 tiles and a 416x312 thumbnail with Display Matrix rotation
  -90. The request fell back to stream 0, one tile; its pose scores are VOID.
  libheif thumbnail decoded sizes: IMG_6690 416x312, IMG_6720 312x416.
- Extra seat probes (`work/wp3.6p/r0/extra-*`): ffprobe showed two Tile Grid
  groups of 45 and 15 tiles. Mapping a group emitted uncomposed tiles and
  failed image2's single-file constraint. DEFAULT selection, no map, with
  `-frames:v 1 -update 1 -map_metadata -1 -pix_fmt rgb24`, composed the primary:
  IMG_6690 5712x4284; IMG_6720 3024x4032. With/without noautorotate was
  identical, pose 1 error 0.000/255. FFmpeg version:
  `ffmpeg version 9.0.2-full_build-www.gyan.dev`.
- FFmpeg primary versus libheif thumbnail, resized to thumbnail dimensions:

| File | Pose 1 | Pose 2 | Pose 3 | Pose 4 | Poses 5-8 |
|---|---:|---:|---:|---:|---|
| IMG_6690.HEIC | 2.82 | 33.4 | 43.0 | 41.0 | Shape mismatch |
| IMG_6720.HEIC | 1.38 | 14.1 | 46.1 | 45.6 | Shape mismatch |

Errors above are mean absolute RGB differences in 1/255 units, not look scores.
No result here is a 62-photo orientation pass.

- CHARC `e40b0d7b06ee9af8`, 04:46:00Z: default FFmpeg primary as delivered is
  the replacement Q3 mechanism; the fixture leg must establish its transform
  rule; thumbnail is recorded second witness only. No further irot is applied.
  The 39 agreeing irot/tag owner files cannot distinguish AD-24 branches.
- R0-E sizes Q5 at about 73 * 37.14 s = 45 minutes, with about 3.8 GB if all
  73 PNGs of the measured size were kept. This is planning arithmetic, not a
  measured total or a retention-policy change. Q9 still keeps seven class
  representative PNGs and removes only the tool's own successfully measured
  nonrepresentative outputs. The 16-bit run is EXCLUSIVE, opened and closed to
  CHARC, with no WP4.6 heavy test/window while open. Stop below 20 GB free.
- Dispatcher class map: schema 1, seven counts 23/3/20/16/2/8/1, total 73,
  reported set-equal to the listing; md5 `07ef683ee2b5a5275a31cdc2597f2fbd`.
  Representatives as specified in the schema example. Not read by this cell.

## RED tests (turn 2)

All new tests are parallel-leg, use tmp_path and synthetic/committed WP2.3
fixtures, except the ONE expressly marked footage test. No gpu test is added.
Committed fixtures are read-only; any mutated copy is under tmp_path.
Base `c3bf602` and pre-RED head `6cc7cdb` have neither new module nor test file. The RED is the
intentional import/collection failure for `photo_verify`; after its API exists,
the assertions below must fail on their named planted bad implementation.

| Test / cases | RED baseline and discriminating failure |
|---|---|
| `test_ffmpeg_default_decode_records_irot_only_rule`, four heic-ad24-* | 6cc7cdb: missing module. Actual default decode must be upright for both/irot-only/neither, stored for exif-only. record_property retains rule and pose scores. An additional rotation or EXIF assumption fails by case. |
| `test_orientation_matches_generated_upright`, four heic-ad24-* | 6cc7cdb: missing module. Product must match generated upright on all four; FFmpeg agreement is asserted false for exif-only and true otherwise. Eight poses and shape discrimination prevent a nearest-only false pass. |
| `test_orientation_rejects_exif_always`, both | 6cc7cdb: missing module; planted extra tag application fails `orientation_upright`, naming heic-ad24-both. |
| `test_orientation_rejects_exif_never`, exif-only | 6cc7cdb: missing module; planted omission fails generated-reference `orientation_upright`, naming heic-ad24-exif-only, while explicitly agreeing with FFmpeg. This records the oracle's branch limitation. |
| `test_thumbnail_disagreement_is_recorded_but_never_the_pass_criterion` | 6cc7cdb: missing module; a planted wrong-pose thumbnail must produce discordant witness scores while the correct primary/FFmpeg comparison still passes. |
| `test_export_v5_v9`, heic8-gradient-none / png16-lowred-display-p3 / jpeg-gradient-none, depths 8 and 16 | c3bf602: missing module; actual runner output must satisfy V5/D53 rules, AD-11 quantised bounds and applicable raw bounds. P3 PNG16 at depth 8 witnesses below-source quantisation. |
| `test_export_rejects_off_neutral_gamma` | c3bf602: missing module; planted gamma default instead of neutral fails `v9_identity`, not merely a pixel inequality in the test. |
| `test_export_rejects_dropped_iccp` | c3bf602: missing module; planted writer removes iCCP from a profile-bearing export and fails `v5_icc_equal`/`v5_icc_present` by name. |
| `test_export_d63_and_kept_exif` | c3bf602: missing module; synthetic EXIF contains kept entries and thumbnail. Assert Orientation normal, dimensions, Software equality boolean, thumbnail absence and kept-field comparison; planted loss of a kept entry fails `v5_kept_exif` by name. |
| `test_export_rejects_lost_kept_exif` | 6cc7cdb: missing module; writer double drops the whole kept block, actual runner output fails `v5_kept_exif`. |
| `test_summary_and_stdout_exclude_private_values` | c3bf602: missing module; tmp JPEG has synthetic GPS and Make in a tmp footage folder. Parse every safe record/summary and stdout: planted values and absolute footage path must be absent, including errors/nested extra keys. No comparison value is printed. |
| `test_cli_summary_and_record_files_stay_private_and_guarded` | 6cc7cdb: missing module; actual export CLI on a synthetic mapped JPEG must print/save safe summary, select one photo, preserve input hashes and put summary under the working guard. |
| `test_export_deletes_only_measured_nonrepresentative_png` | 6cc7cdb: missing module; measured PNG is removed with bytes/md5 retained and unrelated evidence preserved. |
| `test_all_records_and_runner_targets_stay_guarded` | c3bf602: missing module; spy on guard checks during a real runner export. An escaped oracle target is refused before a write; successful export targets stay under the guard. CLI input hashes and deletion-control tests supply the complementary write/deletion evidence. |
| `test_memory_records_sampler_facts` | 6cc7cdb: missing module; real tiny CPU runner plus stubbed samplers supplies estimate/free/RSS/device peak and `CPU: forced`. No GPU run. |
| `test_memory_default_records_actual_runner_reason` | 6cc7cdb: missing module; controlled CPU runner adapter simulates no-CUDA reason while samplers are stubbed. Wrapper must retain that actual adapter reason and distinguish automatic fallback from force CPU. |
| `test_memory_missing_device_samples_cannot_pass` | 6cc7cdb: missing module; absent device samples remain null and fail `memory_device_measurement`, never become a zero-peak pass. |
| `test_class_map_rejects_unsafe_or_incomplete_inventory`, four damages | 6cc7cdb: missing module; traversal, duplicate, wrong count and unknown class each refuse. |
| `test_class_map_and_summary_keep_candidate_rows_separate` | 6cc7cdb: missing module; full synthetic map and unequal A/Z/M metrics retain separate rows and assumed counts; no pooled error at top level. |
| `test_owner_heic_orientation_four_irot_classes` | c3bf602: missing module; ONE `footage` test, reason beside marker: serial owner-photo I/O. IMG_6703/6718/6690/6720, independent oracle upright checks. Skip only absent footage; when available, missing/refused photo or unusable oracle fails. Cell does not execute it. |

RED command run this turn (PowerShell environment spelling of the required shim):

```powershell
$env:PYTHONPATH = 'scripts'
uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" *> work/wp3.6p/red.log
```

After GREEN: same touched-file selection/shim, targeted ruff and `uv run mypy`,
all redirected under work/wp3.6p. Dispatcher runs format check at its seat due
to the known sandbox artifact. No full suite before Reviewer B; ONE two-leg
gate on the final candidate after reviews and seat evidence; no fullclip or
harness gate for this owned file set.

### Turn-2 execution and test-facing API

Observed final RED: pytest EXIT 2, `ModuleNotFoundError: No module named
'photo_verify'`, `1 error in 0.18s`. This is the required new-module collection
RED; none of the individual test bodies ran. Every test above is RED on the
pre-RED head through that absent module, rather than a claimed executed mutant
failure. Evidence: `work/wp3.6p/red.log`; the command is shown above.

Light synthetic probe, separate from the blocked test collection: all four
FFmpeg default decodes EXIT 0. Command per fixture (via the local venv Python
subprocess adapter, stdout/stderr captured under work):

```text
ffmpeg -nostdin -hide_banner -loglevel error -y -i tests/fixtures/stills/heic/heic-ad24-<case>.heic -frames:v 1 -update 1 -map_metadata -1 -pix_fmt rgb24 work/wp3.6p/r0/synthetic-ffmpeg/<case>.png
```

| Case | Default decoded size | Expected reference | Mean error /255 |
|---|---|---|---:|
| both | 96x64 | Generated upright | 1.174262 |
| irot-only | 96x64 | Generated upright | 1.174262 |
| exif-only | 64x96 | Stored pose (generated upright turned CCW 90) | 1.174262 |
| neither | 96x64 | Generated upright | 1.170736 |

Evidence: `work/wp3.6p/r0/synthetic-ffmpeg-probe.log` and
`work/wp3.6p/r0/synthetic-ffmpeg/facts.json`. No owner footage was involved.
These are fixture characterization figures, not product/owner verification.
The committed tests reproduce the characterization and record the rule with
pytest record_property once the new module exists. No RUN REQUEST is pending
from this turn.

Test-facing Python API for the GREEN turn (new tool API, no frozen interface):

- `make_guard(config)` creates the guarded wp3.6p root.
- `ffmpeg_decode(source, out_png, guard)` returns RGB in 0..255 as delivered by
  FFmpeg default selection; validates the write target before subprocess work.
- `compare_poses(pixels, reference)` accepts RGB in 0..255 and returns the
  allow-listed pose figures plus named `orientation_upright` failure.
- `verify_orientation(source, guard, photo_class=...)` uses `read_photo` and
  FFmpeg, records `thumbnail_decode(source)` as a non-gating witness.
- `verify_export(source, guard, photo_class=..., bit_depth=..., force_cpu=...,
  keep=..., parameters=None, exports=None)` runs the real runner; optional
  runner parameters/engine injection support the planted controls without
  modifying product code. Public result contains facts, never output paths.
- `verify_memory(source, guard, photo_class=..., force_cpu=...)` launches a
  fresh real runner, with MemorySampler start/stop/record lifecycle and a
  separately sampled `device_memory()` dictionary (free/total/used bytes).
  `launch_runner(source, out, record_path, settings_dir, bit_depth=...,
  force_cpu=..., neutral=...)` returns `(exit_code, runner_record)`; the default
  selection test uses a controlled real-CPU adapter simulating a no-CUDA host.
  Default memory processing remains non-neutral. Sample failures stay null.
- `load_class_map(path)` validates and returns the schema-1 map;
  `summarise(records, command=...)` applies nested allow-lists and class
  separation; `print_summary(summary)` prints only its ASCII-safe projection;
  `main(argv)` exercises the actual CLI on a synthetic inventory.

Additional light checks: `uv run ruff check tests/test_photo_verify.py` EXIT 0,
`All checks passed!`; ruff format applied to that file, EXIT 0. Seat format
check remains owed. `git diff --check` EXIT 0 (Git emitted its standard LF/CRLF
configuration warning; actual file bytes are LF). Static validation passed:
ASCII/LF/whitespace, 20 test functions, exactly one footage marker, no gpu
marker, both historical request snippets parse, four str disk_usage calls
inside those snippets, and tool file absent. Logs:
`work/wp3.6p/red-ruff.log`, `red-format.log`, `red-static-validation.log`.
Mypy and full suite are not claimed run for this RED-only turn.

## Review ledger and verification record

### Turn 3 GREEN: implementation and final light evidence

Built NEW `tools/photo_verify.py`, with no RED test modification or test fix:

- Three CLI legs plus the test-facing library functions listed above. FFmpeg
  default selection composes the primary; the code neither maps a tile nor
  adds a transform. It independently checks the primary dimensions using the
  fixture-side property parser. All eight pose scores and shape mismatches are
  recorded. Thumbnail availability/scores are a non-gating second witness.
- Export runs the real headless runner library API through the composition
  root, with neutral c3 parameters by default, chosen depth and actual device
  reason. It saves the local runner record, independently parses written PNG
  metadata, compares D63/kept EXIF and ICC, and measures AD-11 quantised/raw
  errors. Untagged JPEG's expected ICC absence is explicit, not an assertion
  that a profile was embedded. Successful nonrepresentative PNGs are hashed,
  sized and removed; representatives and failed-check PNGs stay.
- Memory uses a fresh runner subprocess with c3 defaults, isolated settings,
  explicit output and no neutral flag. Its parent reads dimensions without
  decoding the full photo. Separate sampler threads collect simultaneous
  process-tree RSS sums and device-wide nvidia-smi memory.used; optional OS
  peak is the maximum observed INDIVIDUAL process peak, not a tree sum.
  Pre-run free memory is labelled separately from the backend's actual choice.
  Missing measurements or sampler errors cannot produce a complete pass.
- Every tool write/delete is guarded under the configured wp3.6p root; isolated
  per-run/per-photo directories prevent accidental overwrites. Disk checks use
  str paths, the 20 GB floor and header-derived output budgets. CLI memory's
  --exclusive records the seat's window declaration, not an automatic claim
  that the tool inspected every other host process. Real window scheduling
  remains the dispatcher's responsibility, as commissioned.
- Per-photo JSON and summaries use typed allow-lists; stdout is re-projected.
  Seven class rows keep Z and M separate. Failed photos stop the CLI with safe
  codes; source/config exception text and raw subprocess logs are never copied
  into public summaries. Raw runner/oracle logs remain ignored local evidence.

Final-state light runs, from the worktree root, all output redirected to files:

| Check | Command | Observed result | Evidence |
|---|---|---|---|
| Selected tests | PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" -o junit_family=legacy --junitxml=work/wp3.6p/green-synthetic.xml | EXIT 0; 33 passed, 1 deselected in 4.97s | work/wp3.6p/green-pytest.log |
| Ruff | uv run ruff check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; All checks passed! | work/wp3.6p/green-ruff.log |
| Strict typing | uv run mypy | EXIT 0; Success: no issues found in 147 source files | work/wp3.6p/green-mypy.log |
| Formatting applied | uv run ruff format tools/photo_verify.py | EXIT 0; seat format --check still owed | work/wp3.6p/green-format.log |
| RED tests unchanged | git diff --exit-code -- tests/test_photo_verify.py | EXIT 0; no diff | work/wp3.6p/green-tests-unchanged.log |

The sole deselection is the explicitly marked owner-footage node. No footage,
gpu, gui, slow or fullclip node ran. Tests use synthetic inputs and tmp_path;
memory tests stub samplers/device readings and force actual work to CPU.
JUnit's four ffmpeg_transform_rule properties were parsed and verified present:
irot honoured, EXIF-only ignored. The JUnit legacy output option avoids pytest's
four record_property/xunit2 compatibility warnings seen on the earlier evidence
run. The final run has no pytest warnings. uv still prints the existing harmless
VIRTUAL_ENV mismatch notice; it selects this worktree's .venv. No test was changed
to suppress a failure or warning.

Additional independent synthetic verification logs:
`work/wp3.6p/green-verification.log` (confirmed early-summary defect),
`green-verification-after.log` (fixed summary/config/read/EXIF checks), and
`green-final-verification.log` (final failure/schema/record-persistence checks).
No owner photo, class-map file or other worktree was read for these probes.
The build ran no full suite, Reviewer A/B, harness gate or seat measurement.
Final scope/privacy check: PASS for ASCII/LF/whitespace of tool and ledger,
absence of planted private markers/literal footage-folder name there, and no
planted GPS/Make values or synthetic input-folder name in the test CLI summaries.
`git diff --check` EXIT 0; RED-test diff EXIT 0; status shows only the owned
ledger modified and new tool untracked. Evidence:
`work/wp3.6p/green-final-scope.log`, `green-diff-check.log`.

| Turn-3 suspect | Confirmation / control | Disposition |
|---|---|---|
| [MINOR] stdout projection could drop unattempted class rows | Independent two-class partial summary: saved selected JPG-Z row vanished from print_summary output | CONFIRMED and FIXED; final probe retains selected=1/attempted=0 for that class. |
| [MINOR] invalid configuration/read errors could expose paths or look complete | Traced exceptions beyond the old typed catch; synthetic missing-config and broken-photo probes | CONFIRMED and FIXED; config exits 2 without a path/complete claim; broken selected photo exits 1 with read_failed and attempted=1. |
| [MINOR] malformed raw EXIF could be confused with a failed photo read | Synthetic JPEG with a damaged EXIF block reads successfully but sanitise drops metadata | CONFIRMED and FIXED; read_ok=True, sanitise_dropped=True, V5 fails v5_kept_exif by name. |
| [MINOR] missing RSS samples could be mislabelled as a device failure | Traced the shared sampler-error branch; separated RSS/device error checks | CONFIRMED and FIXED; missing peaks remain null and incomplete, with the corresponding fixed code. |
| A RED test might require a product change | All 33 selected cases pass against the new tool, including planted controls | REJECTED; no test fix, product file or frozen interface change required. |
| Public summary might admit synthetic private values | Planted GPS/Make/path contamination, CLI summary and source-hash tests pass | REJECTED after verification; allow-list boundary and source preservation hold on tested paths. |

Verification loop: after these fixes, traced read -> oracle/export/memory ->
record -> summary and each guarded write/delete again, then ran the final
selected suite, ruff, strict mypy and independent synthetic probes. This pass
found no new issue. This is build verification, not independent review or
real-photo acceptance. Public module/functions/classes have Google-style
docstrings; the module explicitly names both decoding implementations.

For Reviewer A, the tool's required claims (whole artifact, not a review verdict):

1. FFmpeg default composed-primary agreement with all eight poses; fixture
   characterization says irot-only, with EXIF-only limitation explicit. Thumbnail
   evidence is recorded and does not decide the result.
2. V5/D53/AD-11 measurement on actual runner output at selected depth; permitted
   D63 edits only, ICC expected-presence/matching facts explicit, Z/M separated.
3. Fresh non-neutral memory runner, estimate/pre-run free/actual device reason,
   simultaneous RSS tree peak, device-wide memory peak, limits and unavailable
   measurement failures recorded without inferring unmeasured host conditions.
4. Config-derived read-only inputs, guarded outputs/deletion, disk floor, safe
   schema/ASCII stdout and no private metadata values in summary JSON.

Owned files this turn: tool and ledger only. No test fix is bundled. No src,
dependency, local-config, fixture, existing test or other-worktree change.
The owner-photo, EXCLUSIVE export/memory, seat format check, Reviewer A/B and
final two-leg gate remain PENDING. No new RUN REQUEST is issued this turn.

Reviewer A runs via dispatcher (Claude opus/high, read-only) between turns.
Each adjudication turn changes only this ledger and yields before remediation.
Convergence is zero NEW in-envelope blocking findings. At round 5 and each fifth
round: yield for dispatcher approval under the fill; no self-authorised extension.

### Turn 4: Reviewer A round 1 adjudication ONLY

Base/head verified: `70bd6999073ac2180ab53cd2e513bfe7ecdbd7df`;
initial status empty. Fresh session after the previous session's dispatcher-read
240,970 tokens. Read the ledger, owned tool/tests and full findings file; product
and fixture code was inspected only to resolve cited findings. No owner footage,
local configuration contents or dispatcher class map was read. No remediation,
source/test edit, commit, mailbox post or evidence deletion occurred.

Reviewer evidence (outside the worktree, read only):
`C:/Users/rwsmy/clearwater-review-evidence/wp3.6p/r1/review.txt`.
Reviewer verdict: `NEW_CRITICAL_MAJOR_FOUND`; receipt counts: 0 critical,
2 major, 7 minor, 7 advisory. Adjudicated counts: 0 critical, 2 major,
6 minor, 8 advisory; 15 in envelope, 1 out (#15); all 16 NEW, none REOPENED.
#9 is downgraded to advisory because the implemented scope is already described
accurately. #11's asserted command departure is rejected. Confirmations below
distinguish measured mechanisms, conditional risks and actual product defects.

Synthetic evidence is entirely under `work/wp3.6p/rA1-adj/`:
`test_adjudication.py`, `facts.json`, `probe-complete.log`, and guarded temporary
outputs. Probe numbers in facts.json match review finding numbers. The first
EXIF probe failed to plant its mutation: Pillow normalised the equivalent
rational representation back to its original form. The
corrected control changes the serialized rational bytes directly, then verifies
both the byte difference and the missed check. This was a probe correction,
not an instrument fix. Final probe suite: EXIT 0, 18 passed in 1.21s.
These passing probes reproduce weaknesses/limitations; they do not mean the
instrument has been repaired or the real-photo legs accepted.

1. **[MAJOR, IN, CONFIRMED] Wrong-size product result can pass.**
   Mechanic: `verify_orientation` at tools/photo_verify.py:530 passes pixels
   directly to compare_poses; :369 shrinks each operand independently.
   Probe 1 replaces only the returned product pixels with a half-resolution
   version of heic-ad24-both. At max_side=32, decoded 48x32 versus oracle
   96x64 still yields orientation_ok=True. The current reader DOES have
   `_check_decoded_size` (reader.py:226-236, called at :268) before its final
   result; this is not evidence that today's decoder emits a wrong size.
   The verification instrument must independently catch an incorrect final
   read instead of relying on the code being verified. Proposed owned fix:
   check full product/oracle dimensions before pose reduction; emit a named
   size failure, preserve both sizes and retain diagnostic output. Add a
   half-resolution mutant test and an equal-size positive control. No src fix.

2. **[MAJOR, IN, CONFIRMED; BYTE-FIDELITY RULING REQUESTED] Kept EXIF is
   neither byte-exact nor a complete field-set comparison.** Mechanic:
   tools/photo_verify.py:618-624 uses exif.describe and iterates only source
   keys. Product exif.py:390-411 stringifies Pillow values and omits traversing
   Interop. Probe 2 changes XResolution's serialized rational representation
   without changing its numeric meaning,
   adds Artist, and obtains v5_ok=True / kept_fields_equal=True. A separate
   same-length Interop payload mutation leaves describe's entire result equal;
   only the pointer's numeric location is visible, not the child fields.
   Thus additions and Interop loss/change are blind spots even if CHARC selects
   value-level fidelity. Recommended fix after ruling: an independent raw TIFF
   entry inventory in tools/photo_verify.py, comparing IFD-qualified tag,
   type, count and payload bytes, with duplicate multiplicity and child IFDs;
   exclude the four D63 fields, discarded thumbnail and relocated pointer
   addresses, not arbitrary kept payloads. Compare both directions. Expose only
   field names/counts/booleans, never payload bytes or values. Add independent
   mutants for rational bytes, added field and Interop change/drop in the owned
   test. Product exif.py is not reused as the comparison oracle or edited.

3. **[MINOR, IN, CONFIRMED] Known OS peak above 16 GB is ignored.**
   Probe 3 supplies sampled simultaneous-tree RSS 15,000,000,000 and recorded
   individual-process OS peak 20,000,000,000 bytes; verify_memory reports
   ram_within_limit=True with no failed_checks. Mechanic: :1024-1033 checks
   only rss_tree_peak_bytes. Proposed fix: fail the RAM limit if EITHER sampled
   tree peak or an available individual-process OS peak exceeds it. Preserve
   both figures and their distinct scopes; never add individual OS peaks or
   replace an unavailable tree measurement with one process's peak. Add positive,
   exceeded-OS-peak and unavailable-OS-peak synthetic controls.

4. **[MINOR, IN, CONFIRMED MECHANISM; CONTINUATION RULING REQUESTED]
   Pose discrimination can be inconclusive on a correctly oriented scene.**
   Probe 4 compares a synthetic vertical gradient plus seeded noise with itself:
   upright 0.0/255, nearest other 3.343859/255, winner 1, failure solely
   orientation_discrimination. A synthetic two-file CLI selection attempts only
   one, exits 1. Mechanic: :391-394 and main's break at :1377. This matches the
   current ledger's strict <6/>10 rule and STOP policy; it is not a violation of
   that implementation contract or evidence of a wrong product orientation.
   Proposed policy only if CHARC authorises: record a distinct inconclusive
   outcome for upright agreement without discrimination, continue collecting
   remaining files, never count the inconclusive file as an orientation pass,
   and end nonzero/incomplete. Otherwise retain the present halt and disclose
   the incomplete class counts. Do not relax bounds, remove mirror poses or
   use the thumbnail to turn the case into a pass.

5. **[MINOR, IN, CONFIRMED] Source EXIF parse errors can pass vacuously.**
   Probe 5 makes describe fail only on a valid source block while a planted
   writer drops all kept EXIF. v5_ok=True, raw_exif_present=True,
   field_count_before=0, with no failed_checks. Mechanic: :442-445 and :617-620
   turn the exception into an empty inventory. This is an instrument control,
   not evidence of malformed owner metadata: supplied 5a evidence has all 73
   readable with no round-trip problem. Proposed fix: separately record parse
   success/absence/failure and fail v5_kept_exif whenever a present source block
   cannot be inventoried; do not call it absent or claim zero kept fields.
   Add a parse-error mutant and a genuinely absent-EXIF positive control.

6. **[MINOR, IN, CONFIRMED] Owner class-map labels are not checked against
   decoded format/layout.** Probe 6 labels the irot-270 fixture HEIC-180 without
   class_layout failure; a stubbed JPEG memory run is accepted as HEIC-0.
   Mechanic: _base at :434 only validates the label enum; verify_memory validates
   neither that enum nor format/layout. Proposed fix: validate owner CLI selected
   source format and HEIC irot against the class map, emit class_layout and stop
   on disagreement; reject unknown class labels in every library leg. Preserve
   the explicitly commissioned synthetic PNG/HEIC export tests, whose reporting
   labels are test buckets rather than a real owner inventory. Add CLI wrong-
   irot and JPEG-in-HEIC-class controls; keep selected-by-class accounting.
   No scene judgement or metadata-based A/Z/M reclassification is proposed.

7. **[MINOR, IN, CONFIRMED COVERAGE GAP; NO GRID DECODER DEFECT PROVED]
   The four transform fixtures do not witness grid/180 handling.** Probe 7
   independently reads each fixture layout: all hvc1, no thumbnails, irot 270
   for both/irot-only and absent for exif-only/neither. This agrees with the
   generator at tools/fixtures/stills.py:865-891. The reviewer's joint scenario
   (FFmpeg ignores grid irot AND the product double-rotates 180) is conditional,
   not observed. Proposed owned fix: extend test-local generated asymmetric
   HEIC controls to all four rotations, including a known stored-pixel grid/180
   primary; assert FFmpeg delivery against the independently generated upright
   scene, and plant the extra 180 product rotation. Generate under tmp_path;
   do not change shared fixtures or product code. Also aggregate available/
   concordant/discordant thumbnail witness counts per class so a real-file
   disagreement is visible. Keep the thumbnail non-gating under Q3. If a real
   generated-grid construction needs a dependency or changes elsewhere, STOP
   rather than substitute an hvc1-only test and claim grid coverage.

8. **[MINOR, IN, CONFIRMED] Baseline/final samples alone can pass memory.**
   Probe 8 disables only thread execution while retaining real MemorySampler
   baseline/final calls and an instantaneous stub runner. rss_samples=2 and
   device_samples=2 pass all measurement checks with ZERO during-run samples.
   Mechanic: :804-805 and :853-854 increment the same counters checked at
   :1028. Proposed fix: distinguish baseline, active-run and final samples;
   require active-run RSS/device observations for a complete memory result.
   Bracket the actual runner lifetime, not just sampler.start/stop or the
   surrounding launch call. Add zero-active-sample negative controls and
   timed stub lifecycle positive controls; retain unavailable readings as null.

9. **[ADVISORY, IN; SCOPE FACT CONFIRMED, MISLABELLING CLAIM REJECTED]
   The RSS scope includes the tool and sampler children.** Probe 9 supplies
   root RSS 100, runner 200 and sampler child 5; recorded simultaneous total is
   305. Mechanic: verify_memory passes its OWN process at :996; :819 enumerates
   all descendants. The current tool docstrings (:788, :860) and turn-3 ledger
   already explicitly call this the tool/runner tree, so it is not secretly
   labelled runner-only in the artifact. It is a conservative envelope relative
   to runner-only RSS. Proposed owned clarification: record the scope explicitly
   as a fixed enum and use that exact description in the report. Do not subtract
   the baseline to invent a runner peak, or sum separate process maxima. No
   measurement-scope change without a stated need/ruling.

10. **[ADVISORY, IN, CONFIRMED] Decoder versions are absent from safe records.**
    Probe 10 shows version fields disappear at _safe_record. The independent
    decoder names are already present in the module, ledger and required report;
    absence of versions does not invalidate Q3's implemented independence.
    Proposed owned improvement: numeric version facts for FFmpeg, pillow-heif
    and libheif, with constrained version grammar and no build paths, banners
    or arbitrary executable output. Add projection controls. No dependency.

11. **[ADVISORY, IN, REJECTED] FFmpeg flags are NOT an unauthorised departure.**
    Probe 11 captures the real synthetic command and successful 96x64 output:
    no map/no noautorotate, metadata removed, rgb24. The round-0 replacement
    design above explicitly specifies BOTH -map_metadata -1 and -pix_fmt rgb24,
    alongside -frames:v 1 -update 1, as does the recorded default-primary seat
    probe. Neither flag selects a different stream or applies another transform.
    No fix or additional ruling; retain the exact authorised command.

12. **[ADVISORY, IN, CONFIRMED TEST GAP] No real embedded-thumbnail branch
    in the committed synthetic tests.** Probe 12 calls actual thumbnail_decode
    on all four AD-24 fixtures and gets None throughout; the committed positive
    witness test injects pixels. Proposed owned test improvement: generate a
    temporary HEIC carrying an actual thumbnail item, call the real decode path
    and check availability/size/pose; also retain absent/error and disagreeing
    witness controls. Do not replace it with an EXIF JPEG thumbnail or a mock
    and claim the libheif item API was exercised. It remains non-gating.

13. **[ADVISORY, IN, EQUALITY FACT CONFIRMED; FALSE BOOLEAN CLAIM REJECTED]
    The estimate predicate is literally exceeds, not fits.** Probe 13 stubs
    free bytes equal to the estimate and calls the actual select_backend with
    a stub GPU: the backend selects CPU, while estimate_exceeds_free_before is
    False. Both are correct for their stated predicates (> versus <); the
    pre-run query is already explicitly distinguished from the backend query.
    Proposed owned clarification: add estimate_fits_free_before using strict <,
    preserve the accurately named exceeds predicate, and test equality. Do not
    represent the pre-run sample as the backend's exact free-memory reading.

14. **[ADVISORY, IN, CONFIRMED BROAD MEANING] automatic_fallback includes
    unavailable-GPU reasons.** Probe 14 obtains automatic_fallback=True for
    CPU: no CUDA device, as the existing default-reason test intentionally
    asserts. It is automatic CPU selection, not proof of a D111 capacity event.
    Proposed owned clarification: retain the broad fact and add a separate
    memory_capacity_fallback boolean derived only from the validated estimate/
    free reason grammar. Report actual reason, automatic CPU selection, capacity
    event and forced CPU separately. A forced CPU leg is not a capacity test.

15. **[ADVISORY, OUT, CONFIRMED PERMITTED EXCEPTION; NO FIX] ICC description
    is source-controlled text.** Probe 15 retains a synthetic description
    sentinel while removing an unexpected Make key. This is exactly the brief's
    explicit ICC-description exception, not a demonstrated privacy-lock breach.
    No new commitment-facing EXIF/value field is proposed. Keep the allow-list
    and its private-value controls; do not redact the permitted ICC description
    based on a hypothetical planted profile. Cannot drive convergence.

16. **[ADVISORY, IN, CONFIRMED CONDITIONAL LIMITATION; NO ACTUAL DECODER
    DISAGREEMENT PROVED] RGB conversion differences can exceed the pose bound.**
    Probe 16 adds an artificial +8 RGB offset to the same upright reference:
    mean 7.881944/255 fails orientation_upright. This proves threshold
    sensitivity, not different FFmpeg/libheif matrices on an owner file.
    No automatic threshold relaxation or product change. Preserve raw scores,
    identify any real run failure as a STOP/RUN REQUEST with safe evidence,
    and disclose the two decoders and this limitation in the owned report.

#### Ruling packet for CHARC (recommended answers FIRST)

- **R1-QA / finding 2: require byte-level kept-entry fidelity**, as preserved
  by WP4.5: type/count/value bytes and complete kept-entry multiplicity across
  IFD0/Exif/GPS/Interop, ignoring relocation addresses and the authorised D63
  changes. This remains inside tools/photo_verify.py and its new tests. An
  alternative value-level ruling still requires added-field detection and
  Interop comparison, and drops the byte-representation part of finding 2 to
  MINOR with narrower report wording. The current text-based implementation
  must not claim byte fidelity under either answer.
- **R1-QB / finding 4: record solely discrimination-limited cases as
  INCONCLUSIVE and continue the remaining photos**, ending nonzero/incomplete
  and excluding those cases from AD-24 pass counts. Keep all eight poses and
  the fixed bounds. Real read/oracle/size/upright failures still STOP. Alternative:
  retain the current halt on the first inconclusive case and accept a partial
  attempted set pending another ruling. This is a policy choice because the
  present ledger explicitly says failed discrimination halts; no change is
  made before the ruling.

No other finding needs a product/interface/dependency grant. Proposed test-local
grid/thumbnail generation must remain within the owned file/dependency envelope;
inability to do so is a future STOP, never permission to claim unmeasured coverage.
No recommendation above is implemented in this adjudication-only turn.

#### Turn-4 verification evidence and locks

All runner output was redirected under work/wp3.6p/rA1-adj; only summary lines
were read into the return. Commands run from the worktree root:

| Check | Command | Result / local log |
|---|---|---|
| Adjudication probes | PYTHONPATH=scripts uv run pytest -q work/wp3.6p/rA1-adj/test_adjudication.py --basetemp=work/wp3.6p/rA1-adj/tmp-complete -p sandbox_mkdir_shim -p no:cacheprovider | EXIT 0; 18 passed in 1.21s; probe-complete.log |
| Unchanged package tests | PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/rA1-adj/package-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" | EXIT 0; 33 passed, 1 deselected in 3.98s; package-tests.log |
| Ruff | uv run ruff check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; All checks passed!; ruff.log |
| Strict typing | uv run mypy | EXIT 0; Success: no issues found in 147 source files; mypy.log |

These are light synthetic checks, not an owner/GPU run or a memory measurement.
Samplers/devices/runners in memory probes were stubbed. Actual export probes
forced CPU. FFmpeg decoded committed synthetic fixtures only. The existing uv
VIRTUAL_ENV notice remains; no product failure or pytest warning was suppressed.
No format command or full suite was needed for the unchanged Python files;
the dispatcher's earlier clean format check is Reviewer A evidence, not a new
cell-run claim. No review convergence, Reviewer B or final gate is claimed.

Privacy and scope: synthetic EXIF values were compared only in ignored scratch
artifacts. This ledger names format facts, field names and booleans only; no
source footage path, GPS/location, camera/editor/serial or MakerNote value is
copied into it. Source code/tests and all other owned/unowned tracked files are
unchanged. No footage file was opened, no scene judgement made, no local config
edited, no dependency introduced, no frozen interface/source file changed, and
no host measurement/exclusive-window claim made. Only this ledger is submitted
for commit; scratch files stay ignored. Final ledger validation and scope logs:
work/wp3.6p/rA1-adj/ledger-validation.log and scope.log.
Observed final validation: EXIT 0, PASS for ASCII/LF/final newline/whitespace,
16 numbered dispositions, the cumulative row/depth/ruling entries, exclusion
of planted private markers, safe synthetic summary projection, and the ledger
as the sole tracked diff. git diff --check and unchanged-tool/test checks both
EXIT 0. No prohibited value was discovered in a committed-facing artifact.

| Round | Critical | Major | Minor | In / out envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Verdict / evidence | Depth |
|---|---:|---:|---:|---|---|---|---|---|---|
| 0 | - | - | - | - | - | 0 | None; ledger only | R0 seat evidence received; mapped tile scores VOID; Q3 replaced by CHARC | 118,810 after turn 1 |
| Build turn 3 (not A) | - | - | - | Owned tool/ledger | - | 0 | New tool; no test fix | GREEN: 33 passed, 1 footage deselected; ruff/mypy green; Reviewer A PENDING | 168,789 after turn 2; turn-3 reading pending |
| A1 / turns 4-5 | 0 | 2 | 6 (+8 advisory) | 15 / 1; #15 out | 16 NEW / 0 REOPENED; #11 rejected, #9/#13 partially rejected | 0 | 13 tool fix groups with RED/GREEN tests; 0 src fixes; 0 test-only fix groups; #16 Limit in ledger | NEW_CRITICAL_MAJOR_FOUND was A1's verdict; adjudication committed f2396b0e; CHARC R1-QA/QB ruled; remediated turn 5; A2 pending | Turn 4: 114,259; turn 5 dispatcher to fill; previous session 240,970 after turn 3 |

| Suspected item | Independent confirmation | Disposition |
|---|---|---|
| Existing photo_check's success might prove every photo reads | Code at tests/test_photo_check.py:146 explicitly permits refusals | Rejected inference; new wrapper requires every selected photo read. No product defect asserted. |
| Current reader might still use the opener named in AD-24 prose | `_read_heic` at reader.py:250 uses open_heif and later returns the additional-tag decision | Current mechanic mapped explicitly; no behavior defect or interface change inferred. |
| Generic runner records might be safe to copy wholesale | headless_export.py:48-57 documents malformed-tag text in failures; record_object retains warning/failure strings | Confirmed privacy hazard for copying raw records; explicit safe schema planned. No existing tool edited. |
| [MAJOR] R0 mapped output might establish the primary oracle | Dispatcher extra probes: mapped stream 0 is a tile; default selection composes the primary and already applies irot | Confirmed; tile pose scores VOID; Q3 mechanism replaced under CHARC ruling, with no product change. |
| [MINOR] psutil may accept a Path in disk_usage | Dispatcher initial R0-O TypeError; successful reruns passed str(root) | Confirmed seat edit folded into both historical snippets (four calls); new tool must pass str. |
| FFmpeg might honour raw EXIF as well as irot | Four default synthetic decodes: tag-only stays stored, both/irot-only upright | Rejected EXIF-handling assumption; test explicitly records irot-only rule and generated-reference branch controls. |

### Turn 5: CHARC ruling and round-1 remediation

Dispatch head: `f2396b0eeee9dc0932d781d44c1a846d9c31d115`, initial status
empty. Dispatcher-read depth after turn 4: **114,259 tokens**, this fresh session.
Previous session's 240,970 reading is historical and is not this session's depth.
Turn 5 bundles the new RED tests and their fixes in ONE logical round-1
remediation commit, as authorised; there are no intervening cell commits.

CHARC `d9133089b58091d8` (2026-10-30T05:43:16Z), verbatim:

> R1-QA = (a) BYTE-LEVEL kept-entry fidelity. V5 reads "all EXIF preserved except fields made invalid by processing (D63)" and WP4.5 built exactly that at the byte level, so the verification instrument measures what the product claims: an INDEPENDENT raw TIFF-entry inventory in `tools/photo_verify.py` (not `exif.py`, which is the thing under test) compares, per IFD (IFD0 / Exif / GPS / Interop), tag, type, count and payload bytes with multiplicity, in BOTH directions (nothing lost, nothing added); excluded exactly the four D63 fields (Orientation, Software, PixelX/YDimension), the dropped thumbnail / IFD1 and the relocated pointer VALUES (pointer tags compared by presence and type only). Privacy stands: the record and the report expose tag names, IFD labels, counts and booleans, never bytes or values. A mismatch names the IFD and tag id. The text-level comparison of `photo_check` is kept as the second, coarser witness in the record (not the criterion).
>
> R1-QB = (a) INCONCLUSIVE and CONTINUE for a discrimination-only failure: a file whose pose-1 (upright) score wins and is under 6/255 but whose nearest other pose is not over 10/255 is recorded INCONCLUSIVE (symmetric or featureless scene), never an AD-24 pass; all eight poses and the fixed bounds are kept; the thumbnail never turns it into a pass; the run continues to the next file and ends nonzero / incomplete; a read, oracle, size or upright failure still STOPs the run. The report counts inconclusive files per class beside the thumbnail-concordance counts (#7), and names them (file names only). Reason: the instrument's job is to attempt every owner file and report what each shows; one open-water frame must not hide the other 61.
>
> The other fixes (#1, #3, #5, #6, #7 with the real-grid-180 control or a STOP, #8, #9, #10, #12, #13, #14; #16 a Limit; #11 rejected): concurred as listed; owned files only, no `src/` change, no dependency.
>
> Seat run 5a (photo_check 73/73 read, 0 refused, 0 round-trip problems, GPS and MakerNote kept 73/73): noted; the "allows refusals" caveat closes in the report.

#### RED record on the unchanged tool

All initial RED nodes below ran BEFORE any tools/photo_verify.py change. Command:

```powershell
$env:PYTHONPATH = 'scripts'
uv run pytest -q tests/test_photo_verify.py -k r1_ --basetemp=work/wp3.6p/rA1-fix/red-tmp -p sandbox_mkdir_shim -p no:cacheprovider --junitxml=work/wp3.6p/rA1-fix/red.xml *> work/wp3.6p/rA1-fix/red.log
```

Observed EXIT 1: **20 failed, 34 deselected in 7.13s**, all assertion failures;
no collection, fixture, dependency or grid-generation error. Full local evidence
is red.log/red.xml; compact failure-line index is red-node-summary.txt under
work/wp3.6p/rA1-fix. Every node in the table has prefix
`tests/test_photo_verify.py::`; parameter suffixes are literal node ids.

| Finding | RED node id(s), after the prefix above | Failure line on unchanged tool | GREEN on final state |
|---|---|---|---|
| #1 | test_r1_size_is_checked_before_pose_reduction | AssertionError: wrong-size product read passed | PASSED |
| #2 | test_r1_kept_exif_is_byte_exact_in_both_directions[rational-bytes], [added-field], [interop-value] | Initial RED: expected IFD0.282 / IFD0.315 / Interop.2 missing from changed_kept_fields; incidental coarse pointer-offset failure isolated and corrected below | All 3 PASSED |
| #3 | test_r1_os_peak_also_enforces_ram_limit | AssertionError: OS peak above limit was ignored | PASSED |
| #4 | test_r1_inconclusive_continues_without_becoming_a_pass | AssertionError: inconclusive frame hid later inputs | PASSED |
| #5 | test_r1_source_exif_parse_failure_cannot_pass | AssertionError: present unparsed EXIF passed vacuously | PASSED |
| #6 | test_r1_owner_map_rejects_wrong_irot | AssertionError: wrong irot was accepted into an owner class | PASSED |
| #7 | test_r1_real_grid_rotations_and_thumbnail_class_counts[1-0], [8-90], [3-180], [6-270] | AssertionError: thumbnail evidence is missing from class row | All 4 PASSED; grid/rotation assertions already succeeded before that RED line |
| #8 | test_r1_baseline_and_final_are_not_active_samples; test_r1_sampler_counts_only_live_runner_samples | AssertionError: no active RSS sample passed; AssertionError: runner lifetime was not sampled | Both PASSED |
| #9 | test_r1_memory_scope_is_explicit | AssertionError: assert None == 'tool-runner-tree-including-sampler-children' | PASSED |
| #10 | test_r1_decoder_versions_are_safe_and_reproducible | AssertionError: decoder versions were not recorded | PASSED |
| #12 | test_r1_real_thumbnail_item_is_decoded | AssertionError: real thumbnail could not be compared at a common size | PASSED; actual item API, no thumbnail mock |
| #13 | test_r1_estimate_fit_is_strict | AssertionError: equality must not fit | PASSED |
| #14 | test_r1_capacity_fallback_is_distinct[CPU: no CUDA device-False], [CPU: estimate 3 MiB exceeds free 2 MiB-True] | AssertionError: assert None is False / True | Both PASSED |

EXIF control correction (disclosed, not a hidden product/test fix): the initial
three controls had a coarse Interop pointer-location failure unrelated to the
planted mutation, so v5_ok was already false even though the required raw tag
failure was missing. The corrected test source starts with D63 layout already
present; only the Interop case contains that child. Mutations remain independently
specified raw payload/addition changes. An ignored, byte-exact copy obtained with
`git show f2396b0e:tools/photo_verify.py` was loaded as photo_verify by a temporary
pytest plugin; the tracked tool was never reverted or overwritten. All three
corrected controls then fail against that UNCHANGED baseline at the stronger line:
`AssertionError: byte-level EXIF mutation passed: <case>`. Command: same shim,
`-k r1_kept_exif_is_byte`, `-p baseline_override`, basetemp exif-red-tmp;
PYTHONPATH includes scripts and work/wp3.6p/rA1-fix/baseline. EXIT 1:
**3 failed, 57 deselected in 0.38s**. Evidence: exif-red.log/exif-red.xml and
baseline/ under that local evidence root. All three are GREEN in final2.xml.

#### Fixes implemented in owned files

- **#1 size:** verify_orientation compares full product and FFmpeg primary shapes
  before reduction. A mismatch records both sizes, failed status and named
  orientation_size/orientation_upright checks. It stops; a smaller same-aspect
  read cannot pass through resampling. Existing extra-tag mutant stays detected.
- **#2 byte fidelity:** independent _entry_inventory parses classic TIFF in both
  byte orders, traversing IFD0/Exif/GPS/Interop with bounds/type/cycle checks.
  Counters retain entry multiplicity, tag/type/count/payload bytes; source and
  output inventories are compared in both directions. Only IFD-qualified D63
  fields and IFD1 are discarded. Existing directory pointers compare presence,
  type and multiplicity without their relocated addresses. The Exif pointer
  newly required to hold inserted D63 dimensions is accounted for when the
  source had none and the output child contains no kept entries; arbitrary
  added kept fields or other pointers are never exempted. A no-source-EXIF
  positive test covers that necessary D63 scaffolding. Raw mismatches name
  IFD plus numeric tag id, never payload values. The product's parser/rewriter
  is NOT the inventory oracle. The separately labelled text_kept_fields_equal,
  text_changed_kept_fields and text parse status retain the coarser witness;
  relocated Interop offsets do not become spurious text changes. GPS/MakerNote
  kept booleans now use the same byte-level result as the V5 preservation claim.
- **#3 RAM:** either a sampled tree peak or an available individual-process OS
  peak over the limit fails RAM. Missing active samples still fail measurement;
  they cannot erase an already known limit breach. Both original figures remain
  distinct; no separate-process peaks are summed and no baseline is subtracted.
- **#4 inconclusive:** compare_poses retains all eight scores and fixed bounds,
  classifies the ruled discrimination-only case as orientation_status=inconclusive
  with orientation_ok=False, and leaves the thumbnail non-gating. main continues
  ONLY that exact failed-check/status/read-ok combination. Final exit is nonzero,
  complete=False. Class rows count/name inconclusive files separately from true
  failures and passes. All other failure kinds retain the existing STOP.
- **#5 parse failure:** a present block that cannot be inventoried cannot pass
  V5. Source text parse failure is explicitly recorded, never converted into a
  successful empty-source comparison. Raw parse status is independent. Absent
  source EXIF remains a valid distinct case; output D63 fields are still checked.
- **#6 class labels:** owner CLI checks detected format and HEIC irot against
  each selected inventory label before running that photo. Wrong format/irot
  records class_layout and stops. All library legs reject unknown class enums.
  Synthetic library PNG/HEIC export tests retain their test reporting buckets;
  the owner CLI only accepts the commissioned HEIC/JPEG map formats. A/Z/M
  contents are not inferred or reclassified by scene or camera/editor strings.
- **#7 real grids/witness counts:** the EXISTING installed pillow-heif CtxEncode
  supports tile_size and thumbnails. Test-local generation encodes asymmetric
  384x256 scenes as real multi-tile grid primaries with all four rotations and
  agreeing tags; read_layout must establish grid, not hvc1, for every control.
  FFmpeg default delivery is checked against generated upright pixels, before
  the product comparison; the 180 control rejects a planted extra 180 turn.
  No shared fixture/dependency change or hvc1 substitute was needed. Class rows
  now show thumbnail available/concordant/discordant/inconclusive counts.
- **#8 active memory observations:** baseline/final counts remain recorded, but
  separate rss_active_samples/device_active_samples must each be positive for
  completeness. launch_runner uses the actual Popen lifetime; the sampler polls
  it live before AND after a reading. Thread startup or a surrounding adapter
  call alone cannot create an active observation. A tiny real CPU subprocess
  exercises that lifecycle with RSS/device readings stubbed, not host figures.
- **#9 scope:** the allow-listed rss_scope enum is explicitly
  tool-runner-tree-including-sampler-children in every memory record. No claim
  of runner-only RSS or estimate of a baseline-subtracted peak was added.
- **#10 versions:** records include constrained numeric FFmpeg, pillow-heif and
  libheif versions. Only a numeric FFmpeg prefix is parsed from the captured
  version command; banners, build paths and arbitrary output are not projected.
  Unavailable numeric facts remain null; malformed/private version strings are
  excluded on summary reprojection. No source metadata is used as a version.
- **#12 thumbnail item:** a real encoded HEIF thumbnail item is decoded through
  get_thumbnail, with item count/size and concordance asserted. compare_poses
  uses the smaller common maximum side, without upscaling a small thumbnail.
  Primary size equality is separately enforced by #1. Existing absent/error
  handling and discordant-witness tests retain the non-gating policy.
- **#13 fit:** estimate_fits_free_before uses strict <, remains null if the
  sample is unavailable, and is distinct from the literal exceeds predicate.
  Equality does not fit; neither predicate claims to be the backend's later
  internal free-memory sample.
- **#14 capacity:** memory_capacity_fallback is true only for the validated
  estimate/free CPU reason. Broad automatic CPU selection, explicit forced CPU
  and actual reason remain separate; no-CUDA is not evidence of a D111 event.
- **#16 LIMIT FOR THE REPORT:** FFmpeg/libheif RGB matrix or range differences
  may exceed the fixed upright bound even when poses agree. No such owner-file
  discrepancy is proved by the synthetic offset probe. Preserve scores; a real
  upright/oracle failure still STOPs for CHARC. No automatic bound relaxation.

#11 remains rejected; the authorised FFmpeg default command is unchanged.
#15 remains out-of-envelope; the explicitly permitted ICC description exception
is unchanged. No recommendation here changes a product interface or source file.

Additional raw-inventory controls independently lay out TIFF bytes in both
endiannesses and assert duplicate multiplicity, type, count, payload, pointer
type, permitted child relocation and discarded IFD1 behavior. They do not derive
their expected inventory from the product rewriter. A real JPEG-in-HEIC-map
negative control and a genuinely absent-source-EXIF positive control also pass.

#### Owner verification loop, then final light checks

| Suspected / confirmed issue during implementation | Evidence / independent control | Fixed / rejected |
|---|---|---|
| [MINOR] Thumbnail comparison at separate small sizes cannot compare an actual smaller thumbnail | RED real item decoded, but witness concordance false | CONFIRMED/FIXED by common bound; actual item now concordant; no oracle policy change |
| [MINOR] Interop relocated pointer values contaminate the coarser text witness | First GREEN raw mismatches correct but text witness false on equivalent/hidden payload mutations | CONFIRMED/FIXED; structural text pointer value excluded, raw pointer type/presence comparison retained |
| [MINOR] Initial EXIF RED could be confounded by a different coarse failure | Corrected sources, isolated unchanged f2396b0e module; all 3 now pass the old V5 and fail the new test | CONFIRMED; control corrected and stronger baseline RED recorded; no tool revert |
| [MINOR] GPS kept boolean could remain true for text-equivalent changed bytes | test_r1_gps_kept_uses_byte_fidelity RED: text-equal GPS bytes were incorrectly called kept | CONFIRMED/FIXED; final node PASSED, GPS.2 named and V5 fails |
| [MINOR] Missing active samples could hide a known OS-limit breach in the record | test_r1_known_os_limit_failure_survives_missing_active_samples RED: known OS limit breach was hidden by missing samples | CONFIRMED/FIXED; final node PASSED, both measurement and limit failures retained |
| A real grid/180 witness might require a dependency or shared fixture change | Four generated grid controls decode with installed CtxEncode/FFmpeg; grid and known-pose assertions pass | REJECTED; no dependency/fixture change and no STOP needed |
| Version facts or new field/tag records could bypass privacy projection | Numeric-version contamination control and existing planted GPS/Make/path tests | REJECTED on final tested surfaces; constrained nested projection retained |

The two additional verification-loop RED nodes ran on the first remediated tool,
not on f2396b0e: EXIT 1, 2 failed / 58 deselected in 0.86s, verify-red.log.
This distinction is intentional. Their subsequent final GREEN is in final2.xml.
After those fixes, traced raw read/inventory/metadata -> record -> summary,
orientation failure/inconclusive continuation, guard/retention, and memory
sampling/lifetime/limits again. Ran the final selected suite and independent
static/privacy checks. No new issue found in that last pass. This is cell
verification, not independent review convergence or owner-photo acceptance.

Final light commands (outputs under work/wp3.6p/rA1-fix, PowerShell environment
spelling of PYTHONPATH; all logs captured, not pasted):

| Check | Exact command | Observed final result / evidence |
|---|---|---|
| Tests | PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/rA1-fix/final2-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" -o junit_family=legacy --junitxml=work/wp3.6p/rA1-fix/final2.xml | EXIT 0; 59 passed, 1 deselected in 10.30s; final2-pytest.log |
| Ruff | uv run ruff check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; All checks passed!; final2-ruff.log |
| Strict typing | uv run mypy | EXIT 0; Success: no issues found in 147 source files; final2-mypy.log |
| Formatting | uv run ruff format --check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; 2 files already formatted; final2-format-check.log |

The 59 include the original 33 selected cases plus 26 new regression/control
cases. The ONE footage node remains deselected. All exports in tests force CPU;
memory figures in tests are stubbed, including the live-subprocess sampling
control's process/device readings. No owner photo, GPU, GUI, slow, fullclip or
heavy/exclusive measurement ran. Final pytest has no test warnings; legacy JUnit
avoids the four record_property/xunit2 warnings on the first intermediate run.
uv still emits the existing VIRTUAL_ENV mismatch notice and uses this worktree's
environment. No full suite or additional gate is claimed/run by the cell.

Scope/privacy on disk: only tools/photo_verify.py, tests/test_photo_verify.py and
this ledger are changed. All three are ASCII with LF blobs. New raw inventories
and comparisons live in memory; serialized records contain names, numeric tag
ids, IFD labels, counts, format facts and booleans only. Synthetic private values
remain excluded from commitment-facing records/summary/stdout, as exercised by
the unchanged privacy/guard tests and final static projection check. No footage
path/value, camera/editor/serial string, GPS/location or MakerNote content is
copied into this ledger or the return. No src, frozen interface, shared fixture,
existing unrelated test, config, dependency, lockfile or other-worktree edit.
No read/edit of the owner's local config, owner-footage read/write, commit, mailbox post, scene
judgement or evidence deletion. The fixture/control files are temporary guarded
test outputs; the original synthetic input bytes stay read-only during tool runs.

Seat run 5a remains the supplied successful 73-photo evidence below. The report
will close its historical refusal allowance caveat on those actual counts, not
merely on the old test's permissive assertion. Other seat runs, the report,
Reviewer A round 2, Reviewer B and the one two-leg gate remain owed. R1-QA/QB
are resolved; no new ruling request or STOP. YIELD now before Reviewer A round 2.
Final scope/privacy/static validation logs are final-scope.log and
final-ledger-validation.log under the same local evidence root.
Observed final static validation: EXIT 0, PASS for the exact three-file scope,
ASCII/LF/whitespace, 59 executed passing cases / one footage deselection,
26 round-1 controls, 49 safe record/summary JSON files scanned without planted
private markers, nested privacy projection, ruling/depth entries, public tool
docstrings and importability. git diff --check EXIT 0. The initial scratch
validator's JUnit deselection accounting and PowerShell-log decoding were
corrected before this PASS; neither required a product/tool/test change.

## Seat-run ledger

| Run | Command / scope | Counts | EXIT | Wall time | Free disk before / after | Evidence / conditions |
|---|---|---|---|---|---|---|
| R0-O | Historical request above, psutil str fix; two HEICs | 2 probed; 61 HEVC streams each; mapped stream 0 was a tile | 0 | 2 s | 189,229,633,536 / 189,228,720,128 bytes | 2026-10-30T04:42:08Z; oracle-facts.json; mapped tile pose scores VOID |
| R0-E | Historical request above, psutil str fix; IMG_6690 neutral PNG16/default device | done 1, others 0; one PNG 51,873,583 bytes; GPU | 0 | 37.14 s | 189,175,160,832 / 189,113,147,392 bytes | 2026-10-30T04:43:51Z; export-facts.json; dispatcher-seat timing observation |
| 5a | uv run python tools/photo_check.py --name wp3.6p-io; configured folder, all 73 | photos 73; read_ok 73; refused 0; round_trip_problems 0; verdict ok 73; gps_kept and maker_note_kept each 73/73 | 0 | 309 s | 188,759,597,056 / 186,750,087,168 bytes | Dispatcher supplied: 2026-10-30T05:20:40Z-05:25:50Z; work/wp3.6/photo-check/wp3.6p-io/ in main tree; unchanged instrument's existing root; NOT opened/rerun by cell |
| 5b | photo_verify orientation, all 62 HEICs | PENDING | NOT RUN | PENDING | PENDING | FFmpeg DEFAULT primary; thumbnail is recorded witness |
| 5c-16 | photo_verify export, all 73, neutral/depth 16 | PENDING | NOT RUN | PENDING | PENDING | EXCLUSIVE window opened/closed to CHARC; WP4.6 cannot run heavy work; seven retained representative PNGs |
| 5c-8 | photo_verify export, seven representatives, neutral/depth 8 | PENDING | NOT RUN | PENDING | PENDING | PNGs measured then removed by tool |
| 5d-default | photo_verify memory, IMG_6690.HEIC/default device/c3 defaults | PENDING | NOT RUN | PENDING | PENDING | EXCLUSIVE; default processing, not neutral |
| 5d-cpu | photo_verify memory, same photo/force CPU/c3 defaults | PENDING | NOT RUN | PENDING | PENDING | EXCLUSIVE; 16 GB and 8188 MiB comparisons |

## Depth and handoff

| Turn / boundary | Dispatcher-read depth | Action |
|---|---|---|
| 1 / round 0 | 118,810 tokens (dispatcher reading after turn 1) | R0 committed 6cc7cdb; evidence and ruling received on turn 2 |
| 2 / RED | 168,789 tokens (dispatcher reading after turn 2) | RED committed a66eea6; GREEN dispatched on turn 3 |
| 3 / GREEN | 240,970 tokens (dispatcher reading after turn 3; previous session) | GREEN committed 70bd699; previous session retired at depth boundary |
| 4 / Reviewer A round 1 adjudication | 114,259 tokens (dispatcher reading after turn 4; FRESH session) | Ledger committed f2396b0e; 16 dispositions; no remediation; R1-QA/QB ruled before turn 5 |
| 5 / Reviewer A round 1 remediation | PENDING dispatcher reading | 13 tool fix groups plus RED/GREEN controls; #16 Limit staged in ledger; all light checks green; YIELD for A2 |

Evaluate near 200K; stop at a step boundary near 250K per this dispatch.
Historical turn-1 validation was limited to the ledger's ASCII/LF and owned-file diff.
Observed validation: PASS for ASCII, LF, final newline, no trailing whitespace,
both embedded Python RUN REQUEST snippets parsing, seven-class example JSON
parsing, and absence of a literal footage path. Evidence:
`work/wp3.6p/r0/ledger-validation.log`. Snippets were parsed, not executed.
Turn 1 changed only this ledger. Turn 2 changed the ledger and new test file;
no src, frozen interface, dependency, fixture, existing test, local config or
other-worktree change. No deletion, commit, mailbox post or footage read was
made by the cell. Turn-2 RED and turn-3 GREEN evidence is recorded above.
