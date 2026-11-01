# WP3.6P cumulative ledger

## Dispatch and current boundary

- Package: WP3.6P, CODEX lane, STRONG tier; CHARC's FINAL rulings govern.
- Dispatch base verified: `c3bf602fe9ac94cd5df25499d97f3a2bc439bb72`.
- Current boundary: turn 10, session 3. Seat facts/summaries parsed and the
  real-photo report written. Dispatch head verified:
  `790541e77c3be3469c5717ac390f3d2efd21ece9`, initial tracked status empty;
  turn 9 committed as 790541e7 (0 CR, supplied). The new report and this ledger
  are the only changed files. No owner photo was opened by the cell.
- `uv sync`: already run by the dispatcher before dispatch, as stated in the
  binding turn-1 instructions. Not repeated: this sandbox cannot reach the index.
- Initial `git status --short`: empty. The existing isolated worktree is retained.
- At round 0, no STOP or question remained. CHARC `e40b0d7b06ee9af8`
  (2026-10-30T04:46:00Z)
  RE-RULES Q3: FFmpeg default composed primary as delivered is the oracle.
  The thumbnail is a recorded second witness, never the pass criterion.
- Current handoff: YIELD for an EXECUTING
  Reviewer B on the final candidate. CHARC `650bea20b811947c` accepts A3 as
  convergence on that condition; this is not an unconditional B/gate pass.
  R1-QA/QB `d9133089b58091d8`, R2-QA `688ef40fca871a0d` and replacement Q3
  `e40b0d7b06ee9af8` remain governing. No product defect is asserted from a
  planted instrument control. Report wording / Limits are staged below.
- No acceptance verdict, cell hardware measurement, returned Reviewer B or gate
  pass is claimed. Seat receipts/safe tool summaries were read locally; no
  footage was read or seat run rerun by the cell. The report is now delivered
  for B and the ONE two-leg gate. A3 convergence remains conditional on B execution.

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
| A1 / turns 4-5 | 0 | 2 | 6 (+8 advisory) | 15 / 1; #15 out | 16 NEW / 0 REOPENED; #11 rejected, #9/#13 partially rejected | 0 | 13 tool fix groups with RED/GREEN tests; 0 src fixes; 0 test-only fix groups; #16 Limit in ledger | NEW_CRITICAL_MAJOR_FOUND was A1's verdict; adjudication committed f2396b0e; CHARC R1-QA/QB ruled; remediated/committed 7a3810af turn 5; checked A1 fixes HOLD in A2 | Turn 4: 114,259; turn 5: 178,999; previous session 240,970 after turn 3 |
| A2 / turns 6-7 | 0 | 1 | 1 (+8 advisory) | 7 / 3; a-3/a-7/a-10 out | 10 NEW / 0 REOPENED; a-9 behavior confirmed, defect rejected; a-6 conservative rejection retained | 0 | 4 tool fix groups with RED/GREEN controls; 0 src fixes; 1 test-only group (a-8); 5 advisory Limit/report lines in ledger | NEW_CRITICAL_MAJOR_FOUND was A2's verdict; adjudication committed 081f851c; CHARC R2-QA ruled; remediated turn 7; 87 light cases pass; A3 pending | Turn 5: 178,999 before compaction; turn 6: 101,571 after compaction; turn 7 dispatcher to fill |
| A3 / turn 8 | 0 | 0 | 0 (+9 advisory) | 6 / 3; #2/#3/#7 out | 9 NEW / 0 REOPENED blocking findings | 0 | 3 tool fix groups (#8/#1/#9), RED/GREEN controls; 0 src fixes; 0 test-only groups; #5 Limit retained | NO_NEW_CRITICAL_MAJOR; all reviewer findings REASONED after refused execution; CHARC accepts convergence CONDITIONALLY on an executing B; terminating clean-up ruled before this turn | Session 2 retired at 187,455; fresh session 3 turn-8 reading for dispatcher to fill |

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

## Reviewer A round 2: turn-6 adjudication only

Dispatch head: 7a3810af617711b582e82d6a1998085d410514e1. Review evidence:
clearwater-review-evidence/wp3.6p/r2/review.txt, the dispatcher's read-only
Claude opus/high pass, 40 turns. Verdict NEW_CRITICAL_MAJOR_FOUND: 1 MAJOR,
1 MINOR, 8 ADVISORY. The checked round-1 fixes HOLD; none is classified as
REOPENED. This section adjudicates findings, not fixes or acceptance.

The dispatcher supplied the turn-5 seat checks: ruff format --check reports
2 files already formatted; ruff check all passed; selected pytest 59 passed,
1 deselected in 11.09s. Reviewer A separately reports 59 passed, 1 deselected
in 9.94s and clean ruff/format/mypy. Neither result was rerun by the cell or
represented as a new final-state gate in this turn.

All local evidence below is under work/wp3.6p/rA2-adj/. The scratch module
test_adjudication.py imports the unchanged tool and existing synthetic control
helpers. It creates its own synthetic input/Phone and guarded working folders
under pytest's local basetemp; it does not load the owner's local configuration
or open owner footage. Exports force CPU. The RSS/device readings, loop clock
and live-runner state in sampling probes are stubs. No real RAM, GPU peak,
owner-run duration or exclusive-window measurement is claimed.

### Finding dispositions

**M-1 [MAJOR, IN envelope] CONFIRMED.** Expected ICC is circular at
tools/photo_verify.py:706-715, used by :778 and :792-813. The synthetic
test_M1_reader_corruption_is_masked cases replace PhotoReader.read, so the
tool and in-process product runner see the same planted reader bug:

| Synthetic source / mutation | Independent metadata witness | Current tool result |
|---|---|---|
| P3 PNG16, embedded ICC dropped | PIL source ICC bytes present; output iCCP absent | V5 true, D53 true, icc_equal true, failed_checks empty |
| Same PNG, source ICC swapped to sRGB | PIL source ICC bytes differ from output iCCP | Same false pass |
| P3 HEIC, embedded ICC dropped | pillow-heif primary ICC with prof/rICC type present; output iCCP absent | Same false pass |
| P3 JPEG, embedded ICC dropped | PIL source ICC bytes present; output iCCP absent | Same false pass |
| Profile-less HEIC, nclx discarded by the reader | Raw primary metadata says primaries 1 / transfer 13; no embedded ICC | Same false pass, output incorrectly has no D53 built-in |

The fifth case clarifies the review's heic8-gradient-none example: that fixture
has no embedded ICC to drop. The demonstrated defect there is loss of its nclx
colour description, suppressing the mandatory built-in. The embedded-profile
HEIC case above independently demonstrates the actual dropped-ICC defect.
These are planted faults, not evidence of a defect in the unmodified product.

Proposed fix in tools/photo_verify.py, with controls in tests/test_photo_verify.py:

- Read source PNG/JPEG ICC bytes using PIL Image.open(...).info["icc_profile"].
  Determine the format from the library/header, not the product's decoded image.
- Read HEIC primary metadata using pillow_heif.open_heif(...), selecting
  container[container.primary_index].info explicitly. Read ICC bytes together
  with icc_profile_type; accept the defined prof/rICC profile forms. Read raw
  nclx_profile when no embedded ICC exists. An unsupported/ambiguous colour
  source fails closed; it is never silently treated as untagged.
- This helper must not call clearwater.io.photo, its format detector, its ICC
  classifier, its reader or its writer. PIL and pillow-heif are existing
  independent metadata adapters; sharing libheif's container library does not
  share the product's profile-selection gate or ColorDescription logic.
- For embedded ICC, exact source bytes versus independently inflated PNG iCCP
  bytes are the criterion, including mandatory presence. Preserve source ICC
  presence/hash and the expectation's origin as allow-listed format facts,
  never the bytes. Product-derived primaries/transfer/profile-description
  comparisons remain labelled coarser witnesses; they cannot override a raw
  source/output ICC mismatch. A matching embedded ICC directly establishes the
  exported profile's source primaries/transfer provenance.
- For profile-less HEIC, independently map raw nclx (1,13) to the built-in
  sRGB profile and (12,13) to built-in Display P3. Do not consult image.color,
  assumed, source-format metadata from the product, or built_in_profile() to
  decide the expectation. Compare output against the fixed existing byte
  contracts: sRGB 608 bytes / md5 ca34a0279325928fc9fd3fc7eff99eb9; Display P3
  620 bytes / md5 ee27975c71b9ed10be950a696f6fe6f4. These are pinned explicitly
  in tests/test_io_photo_srgb.py and tests/test_io_photo_p3.py. No runtime call
  to a product profile builder supplies the expected bytes/hash. The independent
  raw-code choice and fixed digest make a dropped/swapped built-in detectable.
- The tiny generated nclx controls test_M1_builtin_contract_uses_raw_nclx_and_pinned_digest
  verify both choices against those constants without calling a product profile
  builder. test_M1_independent_profileless_nclx_facts independently verifies the
  existing fixture and its normal output. Add reader-drop/swap and nclx-loss
  RED controls beside the existing writer-dropping-iCCP control in turn 7.

No new dependency, fixture edit, product fix or frozen interface is needed.
No ruling requested for the independent adapter/contract above; it follows D53
and the existing pinned built-in byte contracts.

**m-2 [MINOR, IN envelope] CONFIRMED, with a narrower count observation.**
test_m2_d63_structure_passes[orientation-long] changes output Orientation to
LONG/count 1/value 1. [orientation-duplicate] writes two raw Orientation
entries, one non-normal then one normal. Both still report orientation_normal
and V5 true. The raw kept-entry inventory excludes these fields and the text
view hides the type or duplicate. [software-count] changes Software to ASCII
count 12 with an extra NUL: V5 already fails by name v5_software. Thus not every
bad count escapes the coarse witness; an independent cardinality/type check is
still absent. Proposed tool fix: separately inspect output D63 entries for
uniqueness, required IFD, type, count and required value, without adding those
four fields back to source-preservation equality. RED malformed-type/count/
duplicate controls belong in the owned test file. Exact admissible structure
needs R2-QA below; no structure choice is implemented in this turn.

**a-3 [ADVISORY, OUT of this Apple-photo envelope] CONFIRMED as a limit.**
test_a3_unsupported_types_fail_closed[13/129] constructs raw TIFF entries and
confirms ValueError for non-pointer type 13 and type 129. No V5 false pass is
created. This probe confirms refusal, not a claim that arbitrary raw values are
valid vendor metadata. EXIF 3 UTF-8/non-Apple type support is not commissioned;
do not widen the independent inventory or product. Report limit: unsupported
types fail closed and require adjudication; byte-preservation success is not
claimed for such files. No source/dependency change and no ruling requested.

**a-4 [ADVISORY, IN envelope] CONFIRMED.**
test_a4_empty_gps_pointer_loss_is_not_gps_kept builds a JPEG with a valid empty
GPS child and exports through the real CPU runner. changed_kept_fields includes
IFD0.34853 and V5 is false, while gps_kept is true. Proposed tool/test fix:
include GPS pointer presence/type/multiplicity changes, not just GPS.* payload
changes, in gps_kept. Retain V5's existing fail and expose only the IFD/tag id.
No owner-file defect is inferred from this synthetic empty-child case.

**a-5 [ADVISORY, IN envelope] CONFIRMED.**
test_a5_sampling_wait_is_not_start_to_start_interval uses a fake wait/clock and
0.3 s fake sample duration. The loop's 0.2 s waits produce 0.5 s start gaps;
record() currently labels only the nominal 0.2 s. This is not a measurement of
nvidia-smi speed on the seat. Proposed tool/test fix: explicitly label nominal
values as waits after the preceding sample; add monotonic sampler/runner elapsed
facts and observed RSS/device sample gaps through the numeric allow-list, with
stub-clock controls. Keep samplers, process scope, active-run checks and strict
failure policy unchanged. Do not call nominal waits a guaranteed cadence or
claim a continuous instantaneous peak. No ruling needed to describe observations
accurately; no tighter sampling or acceptance threshold is proposed.

**a-6 [ADVISORY, IN envelope] CONFIRMED behavior; conservative policy retained.**
test_a6_transient_failure_remains_incomplete supplies a successful device
baseline, one unavailable active reading, then two successful active readings.
device_active_samples is 2 and device_unavailable persists. Replaying those
stub facts through verify_memory yields memory_device_measurement. Recovery
does not prove that the missing interval contained no larger peak; a safe
incomplete result is justified. No tool fix or relaxation requested. Report
limit: any unavailable reading invalidates the leg; preserve the error and
successful counts, investigate/repeat at the seat rather than claim success
from partial availability. A truly false owner-run STOP is not demonstrated.

**a-7 [ADVISORY, OUT of the valid IF-1 input envelope] CONFIRMED labeling only.**
test_a7_bad_product_pixels_have_coarse_failure_codes[nan/rgba] injects invalid
product pixel arrays while leaving FFmpeg's synthetic decode real. Non-finite
pixels fail oracle_failed; four channels fail orientation_size. Both stop and
neither yields an AD-24 pass. No product or failure-enum expansion proposed for
these impossible-within-IF-1 arrays. Limit: those broad codes identify a failed
comparison, not proof that FFmpeg alone caused it. Real read/oracle/upright/size
failures still STOP; no owner-file result or product fault is asserted.

**a-8 [ADVISORY, IN envelope] CONFIRMED.**
test_a8_relative_fixture_path_fails_outside_root changes cwd to a synthetic
work folder and calls the existing wrong-irot control. It raises FileNotFoundError
before exercising its assertion. The cited test lines :882, :933, :1071 all
construct cwd-relative fixture paths. Proposed test-only fix: use the existing
sample fixture in those three nodes, with a work-folder-cwd regression control.
No shared fixture/conftest or tool edit is needed for this finding.

**a-9 [ADVISORY, IN envelope] CONFIRM behavior; REJECT as an undocumented
retention defect.** test_a9_retention_policy_was_explicit checks the actual
CLI keep=representative and args.bit_depth == 16 branch AND this ledger's
pre-existing design text: "Retain the seven representative 16-bit PNGs. The
seven 8-bit validation PNGs are measured and removed" (line wrapping normalized
only in the scratch assertion). Its synthetic JPG-A representative export also
runs the real CPU CLI at depth 8: EXIT 0, measured PNG size positive, retained
false and no PNG left under the guard. The seat-run rows also already distinguish
5c-16 retention and 5c-8 removal. No tool fix. Carry this explicit depth wording
into the pending report, including failed-check diagnostic retention; do not
imply both depths were retained. No disk-policy ruling requested.

**a-10 [ADVISORY, OUT of this Apple-photo envelope] CONFIRMED conditional
limit, not a demonstrated owner-file defect.**
test_a10_opaque_makernote_bytes_do_not_prove_external_offsets constructs an
opaque synthetic MakerNote with a hypothetical TIFF-header-relative offset.
Relocating its identical bytes leaves both inventories equal but changes the
target at that absolute offset. This proves the logical limit without parsing
private MakerNote content or asserting any real vendor file is damaged.
No universal MakerNote semantic-validity claim follows from maker_note_kept;
it measures raw-entry byte fidelity. No product fix, vendor parser or dependency
is owned. Name this limit in the report; Apple's content/offset semantics were
not independently decoded by the cell. Any actual owner-file defect still STOPs.

### R2-QA for CHARC: D63 output structure

**Recommended (a):** Require exactly one entry for each of the four rewritten
fields in its required IFD: IFD0 Orientation SHORT/count 1/value 1; IFD0 Software
ASCII/count 11/the fixed product string plus its single terminating NUL; Exif
PixelXDimension and PixelYDimension SHORT or LONG/count 1/the actual upright
width and height. Accept either permitted dimension type without comparing it
to the input's type. Reject duplicates, missing entries, wrong type/count or
wrong value by the existing named V5 check. Keep R1-QA's four exclusions from
kept-entry preservation; do not change pointer/IFD1 rules or any product code.

Why a ruling: D63 and R1-QA specify rewritten values/exclusions, not an exact
output storage-type/count criterion. R2 identifies that missing criterion.
The current product writes SHORT Orientation, ASCII/count 11 Software and
SHORT-or-LONG single dimensions (exif.py:183-206); the proposed independent
criterion checks admissible structure rather than reusing that implementation.
Alternative (b): validate uniqueness and values only, leaving storage type/count
as a documented limit. Recommend (a); byte equality of the other entries alone
does not catch the reproduced duplicate/wrong-type Orientation. Please rule
before turn-7 remediation. This is the only new ruling request this turn.

### Probe record, limits and handoff

Final command, with PowerShell spelling of PYTHONPATH=scripts, all output routed
to local checked-cli.log:

`PYTHONPATH=scripts uv run pytest -q work/wp3.6p/rA2-adj/test_adjudication.py --basetemp=work/wp3.6p/rA2-adj/checked-cli-tmp -p sandbox_mkdir_shim -p no:cacheprovider -o junit_family=legacy --junitxml=work/wp3.6p/rA2-adj/checked-cli.xml`

Observed EXIT 0; **21 passed in 1.91s**. These passing probes assert the
unchanged tool's defective or conservative behavior as specified above; they
are not regression tests proving a fix. No RED/GREEN remediation claim is made.
All ten findings have an executed probe. Initial scratch-only harness issues:
the a-9 wording assertion needed whitespace normalization; an added Software
count mutation actually failed V5 already and was corrected into a narrowing
control. Final log/XML, not those intermediate failures, ground the table.
The existing uv VIRTUAL_ENV mismatch notice is unchanged; uv used this worktree's
environment. No owner path or private EXIF value from a photo is copied here.

Planned turn-7 split: four tool groups (M-1, m-2 subject to R2-QA, a-4, a-5)
with RED-first controls; one test-only group (a-8); no code fix for a-3/a-6/a-7/
a-9/a-10. Report limits/retention wording are staged above for the later report
turn. No edits to tool, test, report, src, fixtures, local config or dependencies
this turn. No reverts, commit, mailbox post, evidence deletion or owner-footage
read/write. Round-1 checks hold; no new product defect is proved. Seat 5a's
successful 73/73 counts remain supplied evidence, not a cell run. Other seat
runs, the report, remediation, Reviewer A convergence, Reviewer B and the one
two-leg gate remain owed. YIELD now, before remediation, as dispatched.

Observed ledger/scope validation: EXIT 0; only this ledger is a tracked diff;
the tool and test bytes match HEAD 7a3810af exactly. ASCII, LF, final newline,
whitespace, all ten dispositions, cumulative/depth/ruling entries and git diff
--check PASS. The ledger and 17 safe record/summary JSON artifacts contain no
planted private marker or absolute synthetic input root. Evidence:
work/wp3.6p/rA2-adj/ledger-validation.log, scope.log and diff-check.log.
The scratch validator initially decoded a PowerShell UTF-16 log as UTF-8;
correcting that local log reader produced the stated PASS, with no tool/test
change. Full ruff/mypy/test gates are not rerun for this ledger-only turn.

## Reviewer A round 2: turn-7 remediation

Dispatch head verified: 081f851c2c19df1d7efd380a97422024999cc5ed; tracked
status was empty. The turn bundles the RED tests with their fixes in one
logical review-remediation change; the dispatcher commits after the turn.
No intermediate commit or write to .git was attempted.

### Governing ruling, verbatim

CHARC 688ef40fca871a0d (2026-10-30T06:39:51Z):

> R2-QA: the D63 output structure is checked by exactly ONE entry per rewritten field in its IFD: IFD0 Orientation SHORT count 1 value 1; IFD0 Software ASCII, value starting "Clearwater" and ending in exactly one NUL, count = the byte length of the value INCLUDING that NUL (derived from the value found, never a pinned number, so a version suffix is not a silent rule change; the report records the string seen); Exif PixelXDimension and PixelYDimension SHORT or LONG, count 1, equal to the upright width and height of the written image. A duplicate, a missing entry, a wrong type, count or value fails the named V5 check (the record names the field and the defect, never the bytes). (b) declined: type and count are what WP4.5's rewriter promises for the D63 edits.
>
> M-1 (expected ICC taken from the product reader itself): a real oracle defect, fix as proposed: the source ICC read INDEPENDENTLY (Pillow `info["icc_profile"]` for PNG / JPEG; the pillow-heif primary's profile and type for HEIC), compared to the PNG's iCCP bytes, or to the D53 built-in for a profile-less nclx source; a planted-reader control that drops or swaps the profile must FAIL. Advisories a-4, a-5, a-8 fixed; a-3, a-6, a-7, a-9, a-10 report wording or Limits: concurred.

The valid rewritten Software string is the ruling's explicit reporting
exception. It is read from the output, not copied from source EXIF. Invalid or
source Software values are not emitted. All other privacy restrictions stand.

### RED on the unchanged 081f851c tool

Added failing controls before any tool edit. All evidence is local under
work/wp3.6p/rA2-fix/. The final corrected baseline run is red2.log/red2.xml:

`PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/rA2-fix/red2-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" -k "r2 or test_r1_inconclusive_continues or test_r1_owner_map_rejects_wrong_irot or test_r1_owner_map_rejects_jpeg" -o junit_family=legacy --junitxml=work/wp3.6p/rA2-fix/red2.xml`

Observed EXIT 1: **25 failed, 3 passed, 57 deselected in 2.59s**, with one
expected Pillow warning for the deliberately excessive Orientation count.
Tool bytes were still the dispatch version. Only the owned test file had been
changed. Three existing a-8 controls were given a work-folder cwd to expose
their relative paths. The remaining REDs exercise real guarded CPU exports,
independent TIFF mutations and the real sampler loop with fake readings/clock.

Node IDs below have the common prefix tests/test_photo_verify.py::. GREEN
means PASSED in final4.xml on the final state, not only an intermediate run.

| Fix | RED node id(s) on 081f851c | Observed RED failure line | Final GREEN |
|---|---|---|---|
| M-1 embedded ICC | test_r2_source_icc_is_independent_of_reader[drop-png], [drop-jpeg], [drop-heic], [swap-png], [swap-jpeg], [swap-heic] | AssertionError: reader-corrupted ICC passed V5/D53 | All 6 PASSED; named v5_icc_equal failure and D53 false for planted product faults |
| M-1 nclx expectation | test_r2_nclx_builtin_cannot_be_suppressed_by_reader[1], [12] | AssertionError: lost nclx silently removed D53 built-in | Both PASSED; absence no longer matches the independent built-in expectation |
| m-2 type / duplicate / count | test_r2_d63_structure_rejects_malformed_entries[IFD0-274-IFD0.Orientation-v5_orientation-type], [IFD0-274-IFD0.Orientation-v5_orientation-duplicate], [IFD0-274-IFD0.Orientation-v5_orientation-count] | AssertionError: malformed D63 structure passed V5 | All 3 PASSED; field and type/duplicate/count defects recorded |
| m-2 missing Orientation | test_r2_d63_structure_rejects_malformed_entries[IFD0-274-IFD0.Orientation-v5_orientation-missing] | AssertionError: D63 field/defect not recorded | PASSED; named missing field |
| m-2 Software count / missing | test_r2_d63_structure_rejects_malformed_entries[IFD0-305-IFD0.Software-v5_software-extra-nul], [IFD0-305-IFD0.Software-v5_software-missing] | AssertionError: D63 field/defect not recorded | Both PASSED; v5_software and count/missing defects |
| m-2 dimension type / duplicate | test_r2_d63_structure_rejects_malformed_entries[Exif-40962-Exif.ExifImageWidth-v5_dimensions-type], [Exif-40963-Exif.ExifImageHeight-v5_dimensions-duplicate] | Type: AssertionError: D63 field/defect not recorded; duplicate: AssertionError: malformed D63 structure passed V5 | Both PASSED; v5_dimensions and field/defect facts |
| m-2 dimension count / missing | test_r2_d63_structure_rejects_malformed_entries[Exif-40962-Exif.ExifImageWidth-v5_dimensions-count], [Exif-40963-Exif.ExifImageHeight-v5_dimensions-missing] | AssertionError: D63 field/defect not recorded | Both PASSED |
| m-2 derived Software count | test_r2_software_version_uses_derived_count_and_records_string (unparameterised at baseline RED) | AssertionError: valid Software version suffix was rejected | Final version and tab-version parameter cases PASSED; found string recorded and count derived |
| a-4 | test_r2_gps_pointer_is_part_of_kept_boolean | AssertionError: lost empty GPS pointer was called kept | PASSED; pointer mismatch makes gps_kept false, V5 remains false |
| a-5 | test_r2_device_cadence_includes_sample_duration[0.3-0.5], [0.9-1.1] | AssertionError: device cadence missing or nominal | Both PASSED; means/min/max 0.5 and 1.1 from fake post-call waits, not nominal 0.2 |
| a-8 | test_r1_inconclusive_continues_without_becoming_a_pass; test_r1_owner_map_rejects_wrong_irot; test_r1_owner_map_rejects_jpeg_as_heic | FileNotFoundError on each relative synthetic fixture path after cwd changed | All 3 PASSED with sample fixture; actual CLI assertions still exercised |

The three baseline positive cases already passed: two normal nclx exports
matching independently pinned sRGB/P3 byte contracts and a legal SHORT
dimension. They are supporting controls, not falsely claimed REDs.
The first scratch RED's dimension-SHORT mutator had left a LONG's big-endian
inline bytes in place. Corrected the test's encoding and reran before changing
the tool. red2.xml is the baseline evidence; no product or tool fix is credited
for that harness correction. red2-lines.log contains the extracted failure
messages; full logs and values are not copied into the ledger.

### Final changes and independent witnesses

- **M-1:** _source_icc reads PNG/JPEG metadata through PIL and HEIC primary
  metadata through pillow-heif with its explicit primary index and profile
  type. It does not call a product format detector, reader, classifier,
  profile builder or writer. Embedded bytes are compared directly with the
  independent PNG chunk reader's inflated iCCP. nclx raw primaries/transfer
  choose the existing pinned byte-length/md5 contracts, never Image.color.
  Unknown or unreadable colour metadata fails closed. Safe records include
  source ICC presence, origin, parse status and digest; never profile bytes.
  Product-derived primaries/transfer comparisons remain coarser witnesses and
  cannot turn a raw ICC mismatch into a V5/D53 pass. V9 is unchanged.
- **m-2:** the independent TIFF inventory optionally includes the four D63
  fields for a separate output-structure pass. The kept-entry comparison still
  excludes exactly those four and retains its existing pointer/IFD1 rules.
  Checks enforce exactly one entry, the ruled type/count/value, and actual PNG
  header dimensions read independently through PIL. Software count comes from
  the found ASCII value with exactly one terminal NUL. ASCII version suffixes
  are permitted, including ASCII control characters escaped by JSON; no extra
  printable-only restriction was authorised. Valid output software_seen and
  allow-listed field/defect pairs are reported; invalid Software bytes/values
  and every unrelated EXIF value remain private.
- **a-4:** gps_kept includes IFD0.34853 presence/type/multiplicity changes as
  well as GPS.* raw-entry differences. A valid empty source child also counts
  as gps_ifd_present by its raw pointer, even with no coarse GPS.* fields.
- **a-5:** retain nominal waits in sample_intervals_s, explicitly labelled
  sample_interval_kind=wait-after-sample. Record actual successful-sample
  start-gap count/min/mean/max for RSS and device, plus sampler_elapsed_s from
  monotonic construction through stop, including baseline/final observations.
  Sort start timestamps before gap calculation because attach/background calls
  can complete out of order. These are sampling-cadence facts, not guaranteed
  instantaneous peaks or the runner's exact process duration. Active-run counts
  and strict unavailable-sample failure policy are unchanged. Only numeric
  cadence keys pass projection; process paths/ids and arbitrary nested values
  do not. No host memory/timing figure is measured in the fake-clock tests.
- **a-8, test only:** the three cited nodes now use sample and run from an
  alternate work-folder cwd. Their actual orientation/selection assertions are
  retained. No shared fixture or conftest is changed.

### Owner verification loop

| Suspected issue | Independent confirmation / rejection | Resolution and final evidence |
|---|---|---|
| [MINOR] New elapsed time froze at attachment rather than stop | test_r2_sampler_elapsed_finishes_at_stop: RED on first remediated tool, elapsed-red.xml, EXIT 1; "elapsed time stopped at runner attachment", 2.0 instead of 10.0 | Fixed finish timestamp in stop; final4 PASSED; later record does not extend stopped elapsed time |
| [MINOR] Out-of-order completions could give negative/incorrect cadence | test_r2_overlapping_sample_completions_keep_chronological_cadence: deterministic re-entry completes later-started observation first; cadence-red.xml EXIT 1; "completion order corrupted chronological sample gaps", min -0.5 / mean 0.25 | Fixed chronological snapshot; final4 PASSED, all gaps 0.5 |
| [MINOR] New Software test imposed printable-only ASCII beyond R2-QA | Added tab-version parameter: ascii-red.xml EXIT 1, one failed / one passed / 86 deselected; "valid Software version suffix was rejected" | Fixed ASCII check and safe projection; both final version cases PASSED; JSON escaping retained |
| [MINOR] Empty GPS child presence still depended on coarse field names | Extended test_r2_gps_pointer_is_part_of_kept_boolean: gps-presence-red.xml EXIT 1; "an empty source GPS IFD was reported absent" | Fixed presence from independent raw pointer; final4 PASSED; no source GPS value emitted |
| New fields might bypass privacy projection | Extended existing planted private-value/path test with Software, D63 defect and cadence contamination; scan final safe JSON artifacts | Rejected on final tested surfaces; constrained projection and private-value test PASSED |

The four verification-loop REDs above are on intermediate remediated tools,
NOT on 081f851c. They refine the same m-2/a-4/a-5 groups; no fix is counted as
src/product code. No reverts. Following these fixes, traced independent source
ICC -> raw output iCCP -> V5/D53, both raw EXIF inventories -> D63/coarse
witnesses -> safe projection, GPS pointer handling, sampler start/attach/stop
and chronological cadence -> safe record, and cwd-independent CLI controls.
Then ran the final light checks and scope/privacy validation. No new issue
found in that last pass. This is cell verification, not Reviewer A convergence.

### Limit / report wording staged for the later report turn

- **a-3 LIMIT:** unsupported EXIF types (including non-Apple UTF-8/type 129 and
  non-pointer type 13) fail closed. Do not call such a failure proven byte loss
  or claim those vendor/type classes verified. No support expansion here.
- **a-6 LIMIT:** any unavailable RSS/device reading invalidates that leg even
  after later successful active samples. Preserve error/count facts and obtain
  a complete seat rerun; partial availability does not establish an accepted
  peak. The conservative policy remains unchanged.
- **a-7 LIMIT:** oracle_failed and orientation_size are broad comparison
  failure labels for invalid/non-finite/wrong-channel product arrays too;
  they do not alone prove that FFmpeg is at fault. Both remain failures/STOPs,
  never AD-24 passes. No invalid IF-1 product behavior was proved on owner data.
- **a-9 REPORT:** keep exactly seven successful representative PNGs from the
  16-bit leg. The seven 8-bit validation outputs are measured then removed.
  Failed-check diagnostic PNGs remain retained. Do not imply both depths kept.
- **a-10 LIMIT:** maker_note_kept establishes raw-entry type/count/payload and
  multiplicity fidelity, not universal vendor MakerNote offset semantics after
  relocation. The cell does not parse private MakerNote contents or prove
  semantic validity for other camera vendors. Actual product defects still STOP.

### Final light checks / handoff

All output is captured under work/wp3.6p/rA2-fix/; summaries read from the
final state. PowerShell sets PYTHONPATH=scripts for every pytest invocation.

| Check | Exact command | Observed result / evidence |
|---|---|---|
| Tests | PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/rA2-fix/final4-tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" -o junit_family=legacy --junitxml=work/wp3.6p/rA2-fix/final4.xml | EXIT 0; 87 passed, 1 deselected in 10.01s; final4-pytest.log |
| Ruff | uv run ruff check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; All checks passed!; final4-ruff.log |
| Strict typing | uv run mypy | EXIT 0; Success: no issues found in 147 source files; final4-mypy.log |
| Formatting | uv run ruff format --check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; 2 files already formatted; final4-format.log |

The 87 cases comprise 59 prior cases plus 28 new round-2 cases. The one footage
node is deselected. All exports force CPU, all memory readings are stubs, and
no gpu/footage/gui/slow/fullclip node or heavy/exclusive measurement ran. The
deliberate excessive-Orientation-count case filters only its known Pillow
metadata warning; final pytest has no warnings. uv's existing environment
mismatch notice remains and uv uses this worktree's environment. Initial
ruff formatting/pairwise and third-party metadata/Literal typing issues were
fixed; only the final checks above support the final claims. No full suite,
independent review, owner run, report or gate is claimed at this boundary.

Only tools/photo_verify.py, tests/test_photo_verify.py and this ledger are
submitted. No src, frozen interface, dependency, lockfile, shared fixture,
unrelated test, local config or other-worktree edit. Source ICC/TIFF bytes stay
in memory, not safe records. The valid rewritten Software string is the sole
new EXIF reporting exception authorised by R2-QA. Inputs and outputs in the
tests are synthetic and guarded under the worktree basetemp. No owner-footage
read/write, direct owner-config read/edit, mailbox post, commit or scene
judgement. Seat 5a remains supplied evidence; other seat runs, the report,
Reviewer A round 3/convergence, Reviewer B and the one two-leg gate remain owed.
No new ruling request or STOP. YIELD now before Reviewer A round 3.

Observed final scope/privacy validation: EXIT 0, final-validation.log under
work/wp3.6p/rA2-fix/. PASS for the exact three-file tracked scope, ASCII/LF,
newline/whitespace and git diff --check; 25 baseline REDs, four independent
verification-loop RED records, 87 final passing cases / one footage deselection,
28 new cases, independent source-ICC helper, public tool docstrings, ruling,
depth and cumulative entries. The ledger and 73 safe record/summary JSON files
were scanned without planted private markers or absolute synthetic input roots.
Supporting scope/diff evidence: final-scope.log and final-diff-check.log.

## Reviewer A round 3: turn-8 adjudication and terminating clean-up

Read in the dispatched order: this full ledger, the owned tool/tests, then
clearwater-review-evidence/wp3.6p/r3/review.txt. Product/test code was inspected
only for cited findings. The review was Claude opus/high, read-only, 34 turns;
VERDICT NO_NEW_CRITICAL_MAJOR, nine ADVISORY findings, all REASONED because
execution was refused. Dispositions: six in envelope, three out; no critical,
major or minor finding, no blocking REOPENED finding, no revert. This turn
bundles adjudication and the three ruled remediation groups in one logical
change, authorised before dispatch. No product defect on owner data is proved.

### Governing ruling, verbatim

CHARC 650bea20b811947c (2026-11-01T08:32:58Z):

> RULING: R3 counts as CONVERGENCE on the condition you already set: Reviewer B on the final candidate EXECUTES (the pytest selection, the planted-reader control and the ICC-presence class check at least), with the execution path proved by one `^ succeeded`-style line before B's findings are read; a B that is again refused execution is NOT a returned B (re-run with the path fixed, and tell me). Reason: a clean round with eight refused executions is a reasoned read of fixes that rounds 1 and 2 saw executed; acceptable as the last A round, not as the only execution of the final tree.
>
> Clean-up list CONCURRED: #8 (ICC-presence class check against Q7's pooling risk), #1 (failure labels), #9 (JPEG refusal in `orientation --files`); #4 / #6 report wording; the three out-of-envelope advisories as report Limits (the Software prefix allow-list: the product writes the constant "Clearwater", so note it as a tool limit, not a product gap).

### All nine dispositions and synthetic confirmations

Evidence root: work/wp3.6p/rA3-adj/. Six report-only probes ran against the
UNCHANGED 649b5662 tool in test_advisories.py: probes.xml/probes.log,
**6 passed in 0.81s**. All readings/runners in those probes are stubs except
the runtime clock-description query; no host peak, footage or GPU measurement.
The other three advisories are confirmed by the baseline regression REDs below.

| Finding | Classification / adjudication | Executed evidence and disposition |
|---|---|---|
| #1 | [ADVISORY, IN] CONFIRMED labels, not a new product defect | r3 product nan/rgba/runtime, comparison, output-parse and command-exception controls fail on the baseline. FIXED: invalid product pixels -> product_pixels_failed; unexpected _base exception -> product_read_failed/read_failed; comparison exception -> orientation_comparison_failed; unexpected orientation-command exception -> orientation_failed; output-check parse exception -> output_parse_failed. Genuine FFmpeg errors retain oracle_failed; failed runner execution retains runner_failed. All remain failures/STOPs. |
| #2 | [ADVISORY, OUT] CONFIRMED conditional tool Limit | test_2_prefix_projection_limit retains a synthetic ASCII/tab suffix following the permitted Software prefix. Existing R2 version/tab controls also establish the ruled acceptance. Product exif.py:20 writes the constant Clearwater; no product privacy gap is proved. No tighter Software rule is authorised; report Limit below. |
| #3 | [ADVISORY, OUT] CONFIRMED conditional tool Limit | test_3_unparseable_ifd1_is_reported_absent builds a valid empty IFD0 with a nonzero out-of-range next-IFD pointer; has_thumbnail returns False while the independently read raw pointer is nonzero. Pillow warnings captured locally. This is not an owner-file defect; no new independent thumbnail parser in this terminating clean-up. |
| #4 | [ADVISORY, IN] CONFIRMED runtime fact | test_4_clock_resolution_fact records Python 3.12.13, monotonic=True, adjustable=False, resolution_s=0.015625 in clock-facts.json. This confirms the cited 15.625 ms clock granularity here; it does not measure a sampler cadence or peak. Report wording below; no OS-specific code added. |
| #5 | [ADVISORY, IN] CONFIRMED interleaving mechanism; Limit | test_5_reentrant_peak_update_loses_larger_reading deterministically interleaves a 9,000-byte stub reading during a 2,000-byte max operation after a 1,000-byte baseline: recorded peak becomes 2,000. This models the unlocked read/max/write race without scheduling or real readings. A correct lock covers shared update regions in both sampling methods (and is not a two-line change); it also affects existing reentrant cadence controls. Under the dispatched two-line/no-risk restriction, no lock fix is made. Report the limitation beside memory figures. |
| #6 | [ADVISORY, IN] CONFIRMED distinct-query semantics | test_6_prerun_fit_is_not_backend_choice uses the real select_backend with a fake GPU: wrapper free=estimate+1, backend free=estimate-1. Record retains fits=True alongside the actual CPU capacity reason. No CUDA context cost is measured; report the separate sources/instants, not the review's approximate context figure as a new measurement. |
| #7 | [ADVISORY, OUT] CONFIRMED alternate-config limitation | test_7_subprocess_does_not_forward_wrapper_config captures launch_runner's guarded argv using fake Popen; no --config is forwarded. headless_export.py:725-744/:1369 consults its default local config. Tool output boundaries remain guarded. Default-config seat requests below avoid this alternate-config case; no launch interface expansion here. |
| #8 | [ADVISORY, IN] CONFIRMED class-map pooling risk | Three real synthetic JPEG CLI controls swap the ICC-presence classification relative to the map, and all pass the old class gate. FIXED using independently read embedded ICC presence. The source fixtures establish P3 JPEG has ICC and untagged JPEG has none. Mismatch refuses by name, declared class and observed compatible class, with class_layout; never exports into a misleading row. |
| #9 | [ADVISORY, IN] CONFIRMED explicit-input omission | The baseline mixed HEIC/JPEG --files control runs the HEIC and silently omits the JPEG. FIXED: preflight refusal before any per-photo decode/export, status 2, named JPEG/class and fixed message 'orientation requires HEIC; explicitly selected JPEG refused'. Implicit all-photo orientation still selects only the 62 HEICs. |

#8 checks precisely the commissioned FORMAT distinction: JPG-A must have an
embedded ICC; JPG-Z and JPG-M must have none. It does not infer camera/editor
strings, scenes, correction history or Z versus M from absent ICC. Accordingly,
observed_class is JPG-A or JPG-Z/M (the latter is a compatible set, never a
pooled statistics row). The declared class remains separate in the refusal.
The inventory's finer Z/M split still depends on the names-only map. An
ICC-bearing JPEG of another profile is not independently proved to be Apple's
A provenance by this presence-only check. No owner file/map was read to test it.

### RED on 649b5662, then GREEN

Added the controls BEFORE editing the tool. The corrected baseline run red2.xml
was 11 failed, 4 passed, 88 deselected in 1.41s. The first scratch #9 stub
returned None and raised before the intended assertion; corrected it to a valid
record and reran BEFORE any tool change. No tool fix is credited for that
control correction. All other initial REDs were the intended assertions.

For an explicit exit-code receipt after formatting, repeated against a byte-exact
ignored copy from `git show 649b5662:tools/photo_verify.py`, loaded as photo_verify
by baseline_override (never overwrote/reverted the tracked tool):

`PYTHONPATH=scripts;work/wp3.6p/rA3-adj/baseline uv run pytest -q tests/test_photo_verify.py -k r3_ --basetemp=work/wp3.6p/rA3-adj/baseline-red-tmp -p sandbox_mkdir_shim -p no:cacheprovider -p baseline_override -o junit_family=legacy --junitxml=work/wp3.6p/rA3-adj/baseline-red.xml`

Observed pytest EXIT **1** (baseline-red.exit): **11 failed, 4 passed,
88 deselected in 1.13s**. Tool baseline content is unchanged 649b5662.
The four supporting positives already pass: correct ICC-presence classes (3)
and genuine oracle failure attribution (1); they are not claimed REDs.
Common node prefix in this table: tests/test_photo_verify.py::.

| Fix | RED node id(s) on 649b5662 | RED failure line | Final GREEN |
|---|---|---|---|
| #8 | test_r3_jpeg_icc_class_mismatch_is_refused[JPG-A-jpeg-gradient-none-JPG-Z/M], [JPG-Z-jpeg-gradient-display-p3-JPG-A], [JPG-M-jpeg-gradient-display-p3-JPG-A] | AssertionError: ICC-mislabelled JPEG was pooled into its declared class | All 3 PASSED |
| #1 product pixels | test_r3_orientation_product_failure_labels[nan], [rgba] | AssertionError: product failure blamed on oracle or runner | Both PASSED |
| #1 unexpected read | test_r3_orientation_product_failure_labels[runtime] | Failed: unexpected product-read exception escaped its step | PASSED |
| #1 comparison | test_r3_orientation_step_failure_labels[compare_poses-orientation_comparison_failed] | AssertionError: comparison failure blamed on oracle | PASSED; ffmpeg_decode-oracle_failed positive also PASSED |
| #1 output parsing | test_r3_output_parse_failure_label[_png_metadata], [read_photo] | AssertionError: output parse blamed on runner | Both PASSED; runner EXIT remains 0 and failed PNG retained |
| #1 command | test_r3_orientation_command_unexpected_failure_label | AssertionError: orientation command exception blamed on runner | PASSED; exit remains 1 |
| #9 | test_r3_orientation_explicit_jpeg_is_refused | AssertionError: explicit JPEG was silently skipped | PASSED; preflight exit 2, no orientation adapter call |

New safe keys observed_class and refusal_reason are finite enums; the new
failure codes/checks are explicit allow-lists. No exception string is projected.
The source-ICC expectation, V9 rules, D63 checks, byte fidelity, pose thresholds,
inconclusive continuation, sampler semantics and deletion policy are unchanged.

### Report staging: round-3 wording / Limits

Carry these into the later report beside the applicable evidence, in addition
to the earlier round-1/2 limitations:

- **#2 LIMIT:** software_seen permits any ASCII suffix after Clearwater under
  R2-QA, including tabs. It is an output-Software reporting exception, not a
  general private-text sanitizer. Today's product writes only Clearwater;
  no product gap is inferred. Never promote source Software into this field.
- **#3 LIMIT:** thumbnail_absent uses the product's Pillow-based has_thumbnail
  witness. It does not independently prove a zero raw next-IFD pointer or
  exclude a malformed/unparseable retained IFD1. No such owner defect is proved.
- **#4 WORDING:** observed start-gap and elapsed figures use time.monotonic;
  Python 3.12.13 here reports 15.625 ms resolution. Those statistics are coarse,
  successful-sample observations, not continuous or exact instantaneous peaks.
- **#5 LIMIT:** attach and background sampling have unlocked peak updates;
  an interleaving at runner startup can lose a larger observation. Reported
  sampled peaks carry that limitation as well as ordinary sampling gaps.
  The cell did not establish that an owner measurement loses an observation.
- **#6 WORDING:** pre-run free bytes / estimate_fits_free_before come from
  nvidia-smi before runner CUDA-context creation (whole MiB); backend selection
  uses its later CuPy reading. These can disagree. The actual reason is the
  runner's record, and a forced CPU leg is not an automatic capacity event.
- **#7 LIMIT:** a wrapper --config is not forwarded to the memory subprocess's
  own footage-refusal config; it reads the default config. Outputs still stay
  under the wrapper's guard. The commissioned seat runs use the default config.
- **#1 supersedes R2 a-7 label wording:** invalid RGB product arrays now have
  product_pixels_failed rather than oracle_failed/orientation_size; comparison,
  unexpected product-read, unexpected command and output-parse failures have
  separate fixed labels. Labels identify the instrument step, not a diagnosis
  or proof of a product defect on an owner photo. Every such result still STOPs.
- **#8 LIMIT:** ICC presence separates A from the compatible Z/M set only;
  the names-only inventory map determines the individual Z and M rows. No
  combined Z/M metric or scene/provenance inference is introduced.

### Verification loop and final light results

Executed all nine confirmations, traced the three fix groups through CLI and
safe projection, and ran the complete selected synthetic file. Suspected
privacy leakage via new diagnostics was rejected by the existing planted
GPS/Make/path and guarded CLI tests plus final safe-JSON scan. Suspected
class-reclassification of Z versus M was rejected: only ICC presence is read;
the rows remain separate. #5's race was confirmed and retained as an explicit
Limit under the dispatched size/risk restriction. No other issue found in the
final scope/privacy/step-label pass. No new product bug or scope grant needed.

All logs under work/wp3.6p/rA3-adj/; final counts are from the final tree.
PowerShell spells PYTHONPATH=scripts as $env:PYTHONPATH = 'scripts'.

| Check | Exact command | Result / evidence |
|---|---|---|
| Selected tests | PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" -o junit_family=legacy --junitxml=work/wp3.6p/rA3-adj/final.xml | EXIT 0; 102 passed, 1 deselected in 9.89s; final-pytest.log/final.xml |
| Ruff | uv run ruff check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; All checks passed!; final-ruff.log |
| Strict typing | uv run mypy | EXIT 0; Success: no issues found in 147 source files; final-mypy.log |

15 new cases supplement 87 prior cases; ONE footage node remains deselected.
All actual exports force CPU; samplers/device reads in memory tests are stubs.
No footage/gpu/gui/slow/fullclip, owner run, full suite or hardware measurement
ran. Ruff initially found N818 on the private refusal exception; renamed it to
_SelectionRefusedError and reran. Formatting applied locally (2 reformatted);
the dispatcher's format --check remains owed. Existing uv environment notice
is unchanged. No test warning or product failure was suppressed.

Only tool, owned test and ledger changed; all committed-facing bytes are ASCII
and LF. No src/frozen interface, dependency/lockfile, shared fixture/conftest,
other test, local config or other-worktree edit. No footage read/write, scene
judgement, mailbox post, .git write, commit or evidence pruning. The later
report, remaining seat runs, executing Reviewer B and ONE two-leg gate are owed.

Observed final validation: EXIT 0, final-validation.log. Exact three-file
tracked scope, ASCII/LF/final newline/whitespace, Python syntax, ledger/depth,
11 baseline REDs and 102 final passes confirmed. Privacy scan of the tool,
ledger and 83 final safe record/summary JSON artifacts found no planted private
markers or synthetic input root; the report is not yet written. New diagnostic
fields remain finite enums. git diff --check EXIT 0 (diff-check.log).
PowerShell AST parsing of the request wrapper plus five request blocks passed
(request-syntax.log); none was executed. No claim of seat/B/gate completion.

### Remaining RUN REQUESTs, in execution order (NOT RUN by cell)

Run from this worktree root, one heavy job at a time. Verify privately that the
default local config's working folder is under this worktree's work/; no source
path/config value goes into the return. CLI outputs use its configured
<working>/wp3.6p/{orientation,export,memory}/<name>/ guard; wrapper logs/facts
below use work/wp3.6p/seat-turn8/. Stop below 20,000,000,000 free bytes before
each run. The tool additionally checks header-derived output budgets. R0's
51,873,583-byte PNG sizes seven retained plus one transient at about 415 MB;
that is a planning allowance, not a new measured output total. No prune.

Use this PowerShell wrapper once at the seat to capture exact command, EXIT,
wall time and free disk before/after. It does not print photo/config metadata.
The Id/log/facts targets must be fresh; do not overwrite a previous run.

```powershell
function Invoke-WP36PSeatRun {
    param([string]$Id, [string[]]$UvArgs, [switch]$UsesClassMap)
    $runRoot = Join-Path (Get-Location) 'work/wp3.6p/seat-turn8'
    New-Item -ItemType Directory -Force $runRoot | Out-Null
    $runLog = Join-Path $runRoot ($Id + '.log')
    $runFacts = Join-Path $runRoot ($Id + '.json')
    if ((Test-Path -LiteralPath $runLog) -or (Test-Path -LiteralPath $runFacts)) {
        throw 'STOP: use fresh run identifiers'
    }
    if ($UsesClassMap) {
        $mapHash = (Get-FileHash -Algorithm MD5 -LiteralPath 'work/wp3.6p/class-map.json').Hash
        if ($mapHash -ne '07ef683ee2b5a5275a31cdc2597f2fbd') { throw 'STOP: class map mismatch' }
    }
    $runDrive = [System.IO.DriveInfo]::new((Get-Location).Drive.Root)
    $freeBefore = $runDrive.AvailableFreeSpace
    if ($freeBefore -lt 20000000000) { throw 'STOP: below 20 GB free' }
    $runAt = [DateTime]::UtcNow.ToString('o')
    $runTimer = [Diagnostics.Stopwatch]::StartNew()
    & uv @UvArgs *> $runLog
    $runExit = $LASTEXITCODE
    $runTimer.Stop()
    $runDrive = [System.IO.DriveInfo]::new((Get-Location).Drive.Root)
    [ordered]@{
        id = $Id; command = (@('uv') + $UvArgs); measured_at_utc = $runAt
        exit = $runExit; wall_seconds = $runTimer.Elapsed.TotalSeconds
        disk_free_before_bytes = $freeBefore
        disk_free_after_bytes = $runDrive.AvailableFreeSpace
    } | ConvertTo-Json -Depth 4 | Set-Content -Encoding ascii -LiteralPath $runFacts
    if ($runExit -ne 0) { throw ('STOP: run failed: ' + $Id) }
}
```

1. **5b orientation:** planning 10-30 minutes (not a measurement), 62 HEICs;
   needs the class map. Return per-class pass/inconclusive/fail counts, named
   inconclusives and thumbnail counts, not raw metadata. Nonzero is a STOP for
   review; the tool itself continues only ruled discrimination inconclusives.

```powershell
Invoke-WP36PSeatRun -Id '5b' -UsesClassMap -UvArgs @('run', 'python', 'tools/photo_verify.py', 'orientation', '--class-map', 'work/wp3.6p/class-map.json', '--name', 'wp3.6p-5b')
```

2. **Q4 footage node:** planning 1-3 minutes, four named HEICs; no class map.
   Run at the seat, with its unrestricted temp handling (no sandbox shim).
   It must execute and pass, not skip, when footage is available. Keep basetemp.

```powershell
Invoke-WP36PSeatRun -Id 'q4' -UvArgs @('run', 'pytest', '-q', 'tests/test_photo_verify.py::test_owner_heic_orientation_four_irot_classes', '--basetemp=work/wp3.6p/seat-q4-tmp', '-p', 'no:cacheprovider')
```

3. **5c-8 export:** planning 3-8 minutes, seven representatives; needs class
   map. Neutral is intrinsic to this subcommand; default device, no force flag.
   Return V5/D53/V9 and bit-depth/error/device facts by each of seven classes.
   Successful PNGs are measured/hashed then removed (none retained at 8 bits).

```powershell
Invoke-WP36PSeatRun -Id '5c-8' -UsesClassMap -UvArgs @('run', 'python', 'tools/photo_verify.py', 'export', '--class-map', 'work/wp3.6p/class-map.json', '--name', 'wp3.6p-5c-8', '--bit-depth', '8', '--representatives-only')
```

4. **5c-16 export, EXCLUSIVE:** planning 45-75 minutes from R0's one-photo
   37.14 s, not a total timing claim. Needs class map; all 73, intrinsic neutral,
   default device. Open/close the window with CHARC at dispatcher seat; no other
   heavy work, including WP4.6. Keep seven successful representatives; other
   successful PNGs removed. Failed-check diagnostic PNGs retained. Return all
   seven class rows separately; no Z/M pooling. Return safe counts and EXIT.

```powershell
Invoke-WP36PSeatRun -Id '5c-16' -UsesClassMap -UvArgs @('run', 'python', 'tools/photo_verify.py', 'export', '--class-map', 'work/wp3.6p/class-map.json', '--name', 'wp3.6p-5c-16', '--bit-depth', '16')
```

5. **5d memory, EXCLUSIVE:** planning 5-20 minutes per leg (CPU defaults may
   be longer; the neutral timing is not its estimate). Needs class map for both.
   Same largest-size IMG_6690.HEIC, c3 DEFAULTS, fresh runner each time. Keep
   exclusive scheduling through both legs; record conditions/moment. Return
   estimate, independently sampled pre-run free/total, actual reason, sampled
   tree RSS/optional individual OS peak, device-wide baseline/peak, cadence,
   active counts/errors and limits, retaining the staged #4/#5/#6 limitations.
   Default leg first; force-CPU leg is mandatory regardless of first selection.

```powershell
Invoke-WP36PSeatRun -Id '5d-default' -UsesClassMap -UvArgs @('run', 'python', 'tools/photo_verify.py', 'memory', '--class-map', 'work/wp3.6p/class-map.json', '--name', 'wp3.6p-5d-default', '--file', 'IMG_6690.HEIC', '--bit-depth', '16', '--exclusive')
Invoke-WP36PSeatRun -Id '5d-cpu' -UsesClassMap -UvArgs @('run', 'python', 'tools/photo_verify.py', 'memory', '--class-map', 'work/wp3.6p/class-map.json', '--name', 'wp3.6p-5d-cpu', '--file', 'IMG_6690.HEIC', '--bit-depth', '16', '--exclusive', '--force-cpu')
```

All requests use the default config (no alternate-config #7 case), no
beside-source target, and only Phone-relative names appear above. Cell did not
read class-map.json; the dispatcher's supplied md5 is the request precondition.
Every seat run needs command/counts/EXIT/wall/free-before/free-after in the
seat-run table. Stop on a refused/unreadable photo, actual defect or unexpected
AD-24 result; no source fix is owned. No scene judgement is added.

Before reading B's findings, the dispatcher must prove B's execution path with
one `^ succeeded`-style receipt. B must EXECUTE the final synthetic selection,
the planted-reader ICC control (test_r2_source_icc_is_independent_of_reader),
and the ICC-presence class checks (test_r3_jpeg_icc_class_mismatch_is_refused
and test_r3_jpeg_icc_class_positive), at least. A refused-execution B is not a
returned B: repair the execution path, rerun B, notify CHARC. The cell's green
runs and forthcoming owner runs do not substitute for that B condition.
No further Reviewer A pass is requested by this ruled terminating clean-up.

## Turn 9: odd-width size equivalence (CHARC 2aaa7e0a)

Dispatch head a8c9778d verified, tracked status empty. Dispatcher-supplied turn-8
seat checks: format --check 2 files already formatted, ruff all passed, light
pytest 102 passed / 1 deselected. These are supplied receipts, not new cell runs.
Depth after turn 8 is **152,054 tokens, session 3**; depth table updated. This
turn bundles RED tests and the ruled fix in one logical change; no commit by
cell. No footage/class-map/local-config file was opened.

### Supplied seat STOP and governing ruling

Seat 5b at 2026-11-01T09:22:07Z: selected 62, attempted 17, complete false.
All attempted were HEIC-0: 7 discriminating passes, 9 inconclusive (pose 1
wins, nearest mirror under 10/255; discrimination-only), 1 oracle_failed on
IMG_6764.HEIC. Its stored/product size is 3213x5712, grid primary, ispe
3213x5712, irot 0; FFmpeg 9.0.2 default composition delivered 3212x5712,
empty stderr. The old strict-size check correctly halted. EXIT 1, wall 52.6 s,
free 189,399,732,224 -> 188,959,887,360 bytes. This is supplied evidence only;
the cell did not inspect any owner input or stopped-run artifact. Row below
records the counts and name, without private metadata or a source path.

CHARC 2aaa7e0a705f2191 (2026-11-01T09:25:03Z), verbatim:

> RULING on 88f61e06 (WP3.6P 5b STOP, IMG_6764 odd width), PRIMARY: CHARC. (a) GRANTED with one addition; oracle LIMIT confirmed as the reading (FFmpeg rounds an odd 4:2:0 composed dimension down by one; the product keeps the HEIF's ispe 3213: nothing in the product is implicated).
>
> (a) as recommended: the narrow size equivalence applies ONLY when the product dimension is odd, the source chroma is 4:2:0, FFmpeg's matching dimension is exactly ONE less and the other dimension is equal; any other difference still fails as today. ADDITION: which edge FFmpeg dropped is not known a priori, so the common-region crop of the product image is tried at BOTH alignments (drop the first column/row, drop the last), the pose comparison is taken on the alignment with the smaller pose-1 distance, and the record carries `oracle_size_rounded: true` AND `oracle_crop_edge: first|last`; the per-class counts report both. The fixture (pillow-heif, odd-width 4:2:0 grid) proves: the equivalence passes, a 2-pixel difference fails, a tile-sized difference fails, and the recorded edge matches the planted construction. One RED-first turn in session 3 (152,054), then 5b re-runs from the start.
>
> Characterisation (9 of 17 irot-0 INCONCLUSIVE, mirror pose within 10/255): recorded, not a STOP, per QB. For my AD-24 status at the accept the report states, per irot class: discriminating photos (pass), inconclusive, oracle-rounded, failed, with the sentence that an inconclusive is a limit of the scene's texture against the oracle's two-pose discrimination, never a pass and never a product finding. If the irot 90 / 180 / 270 classes also come out mostly inconclusive, tell me in the 5b close post: I may then ask for ONE extra discriminator (an asymmetric-content check on the EXIF thumbnail witness) as a follow-on, not inside this package.

### RED first on unchanged a8c9778d

Evidence root work/wp3.6p/r9/. Test-local pillow-heif CtxEncode HEVC quality
100 / chroma 420 / tile_size 128 creates a real grid primary at 257x192.
Seeded asymmetric grayscale RGB content makes either one-pixel shift very
visible without chroma-conversion noise. Assertions independently require
primary grid and source chroma 420; these are not hvc1 or RGB-format guesses.
A quarter-turn control makes the delivered dimensions 192x257, covering a
lost row as well as a column. Every fixture/output is synthetic and guarded.

Initial light characterisation (probe.log / probe-facts.json): FFmpeg EXIT 0
and empty stderr; outputs 256x192 / 192x256. The generated-content independent
crop means are **last 0.137980/255, first 74.655111/255** for both orientations.
This establishes LAST for these fixtures only; the tool never assumes that
edge on another file. No owner-photo edge has been measured by the cell.

Added tests before editing tools/photo_verify.py, then executed:

`PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py -k r9_ --basetemp=work/wp3.6p/r9/red-tmp -p sandbox_mkdir_shim -p no:cacheprovider -o junit_family=legacy --junitxml=work/wp3.6p/r9/red.xml`

Observed pytest EXIT **1**, **7 failed, 7 passed, 103 deselected in 7.51s**;
red.exit / red.log / red.xml / red-lines.txt. The seven passing negative
controls already fail closed on the baseline; they are not claimed REDs.
Common node prefix below is tests/test_photo_verify.py::.

| Node(s), on a8c9778d | RED failure line | Final GREEN |
|---|---|---|
| test_r9_real_odd_420_grid_uses_last_edge[1-1], [6-0] | AssertionError: odd 4:2:0 grid refused as oracle_failed | Both PASSED, real FFmpeg, recorded edge last |
| test_r9_both_crop_edges_before_all_poses[first-1-1], [first-0-6], [last-1-1], [last-0-6] | AssertionError: permitted one-pixel crop did not compare | All 4 PASSED; planted first/last on columns/rows, all 8 scores, pose 1 winner, class counts |
| test_r9_unrounded_summary_and_projection | AssertionError: assert (True and None is False) | PASSED; exact-size read has rounded false, zero first/last counts; invalid flag/edge excluded |

Supporting controls test_r9_decode_rejects_larger_size_difference[two-pixels]
and [tile] run the real FFmpeg decode, then independently crop its emitted
PNG to 255x192 or 128x128 before its header is checked. Both remain
oracle_failed before pose comparison; no size equivalence is recorded.
The five original test_r9_near_misses_still_fail cases (444 / even / two-axes /
larger / unknown-chroma) retain orientation_size failures for independently
planted oracle arrays. They passed before and after the fix.

### Ruled implementation and owner verification loop

- Source transformed primary size still comes from the independent fixture-side
  box parser, applying only the same existing irot dimension swap. FFmpeg
  command/default stream/decode pixels are unchanged. The header gate admits
  only a single exactly-one-short odd dimension with its other dimension equal
  AND primary source chroma reported as integer 420 by pillow-heif. Absent,
  different or unverifiable chroma gets no equivalence. No source RGB/chroma
  inference, resize, padding or general size tolerance is introduced.
- Full product size must still match that independent primary size before the
  crop exception can apply. Both first-edge and last-edge common regions of
  the product are compared with the delivered oracle. Each crop is made BEFORE
  its complete eight-pose comparison. Select the alignment by smaller pose-1
  mean alone, preserving all original bounds, other-pose scores, shape
  mismatches and pass/inconclusive/failure policy. Ties deterministically keep
  first. The thumbnail remains a non-gating witness and is unchanged.
- Records include allow-listed boolean oracle_size_rounded and, for an applied
  equivalence, finite enum oracle_crop_edge (first/last). Each class row adds
  oracle_size_rounded_count and oracle_crop_edge_counts with first/last counts.
  Reprojection/stdout derives these counts from the same safe records. Z and M
  remain separate. Original product and oracle dimensions remain in the record.
- Verification suspect: a product padded from an even source size to an odd
  size could otherwise borrow the oracle exception. Added
  test_r9_near_misses_still_fail[product-extra] as an independent adversarial
  control; it passes with orientation_size, not an equivalence. This is a new
  supporting control, not a claimed baseline RED or a found product defect.
- Verification suspect: permitting one crop edge could hide the other or
  alter pose discrimination. Rejected on the four planted edge/axis cases,
  all-eight-score and fixed-bound assertions, and all prior orientation
  controls. Both alignments are actually evaluated before min(pose-1).
- Verification suspect: new diagnostic fields might publish arbitrary text.
  Rejected by explicit bool/enum projection, its planted invalid-field test,
  existing GPS/Make/path controls and final safe-JSON scan. No new EXIF value,
  source path, dependency, product/source/interface or shared fixture change.

Final pass traced both header and product size gates, crop-before-transform,
pose-1 selection, all eight scores, per-class counts and privacy projection;
then ran the final light checks. No additional issue found. No new review round,
product defect, acceptance or owner orientation pass is claimed. Prior A3
convergence remains conditional on an executing Reviewer B under 650bea20.

### Final light checks

All outputs captured under work/wp3.6p/r9/. PowerShell sets PYTHONPATH=scripts.

| Check | Exact command | Observed result |
|---|---|---|
| Tests | PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" -o junit_family=legacy --junitxml=work/wp3.6p/r9/final.xml | EXIT 0; 117 passed, 1 deselected in 17.98s; final-pytest.log |
| Ruff | uv run ruff check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; All checks passed!; final-ruff.log |
| Strict typing | uv run mypy | EXIT 0; Success: no issues found in 147 source files; final-mypy.log |

15 new cases supplement the prior 102; ONE footage node remains deselected.
JUnit records both real last-edge facts in final-edge-facts.json. Every new
case is synthetic/parallel-leg. Existing exports force CPU, memory readings
are stubs; no owner/GPU/heavy/exclusive measurement ran. Formatting applied
locally (2 files reformatted); dispatcher format --check is still owed for
this tree. No test warning; existing uv environment-mismatch notice unchanged.
No full suite, B or two-leg gate run by the cell.

Observed final scope/privacy validation: EXIT 0, final-validation.log.
Exact three-file tracked scope; ASCII/LF/final newline/whitespace; Python
syntax; ruling/depth/seat entries; seven baseline REDs; 117 final passing
cases; both real last-edge facts; tool/ledger and 98 safe JSON artifacts scanned
without planted private markers or synthetic input roots. git diff --check
EXIT 0 (diff-check.log). Report remains unwritten pending owner-run results.

### Report staging and restart handoff

Per irot class the later report must show discriminating passes, inconclusive,
oracle-rounded and failed, plus first/last edge counts. Rounded is an
independent flag and may overlap a pose outcome; never add it as a separate
pass. Use: "An inconclusive is a limit of the scene's texture against the
oracle's two-pose discrimination, never a pass and never a product finding."
All eight pose scores remain measured; the mirror is the cited nearest-other
pose on these supplied inconclusives. If the restarted 90/180/270 classes are
also mostly inconclusive, tell CHARC in the dispatcher's 5b close post. Any
extra asymmetric thumbnail discriminator is a possible follow-on, not owned
or implemented here. AD-24 status stays CHARC's accept decision.

**5b unchanged, re-run from the start.** No flags/selection/threshold change to
request 1. Use fresh run identifiers/output name under the existing
no-overwrite rule; keep the stopped evidence. Needs the same class map with
supplied md5 07ef683ee2b5a5275a31cdc2597f2fbd, not read by the cell. No request
2-5 change. Remaining seat runs/report/executing B/two-leg gate remain owed.
No new STOP or question. YIELD after this one logical turn as ruled.

## Turn 10: seat runs recorded; report

Dispatch head 790541e7 verified, initial tracked status empty. Turn-9 depth
**184,466 tokens (session 3)** recorded. Supplied gen-29 checks on turn 9:
117 passed / 1 deselected; ruff/format/mypy clean; 0 CR in committed blobs.
Keep this report turn bounded: only the local wrapper facts, safe tool summaries,
seat-5a receipt and prior staged Limits were read; no footage/config/map/other
worktree read, tool/test/source edit, commit, mailbox post or hardware rerun.

### Receipt parsing, cross-check and 5c-8 provenance

Read every seat-turn8/<id>.json receipt and extracted each tool summary directly
from its .log bytes. Byte detection found UTF-8 JSON in 5b, 5b-r2 and 5c-8;
UTF-16 LE JSON in 5c-16, 5d-default and 5d-cpu. In the latter, locate the
UTF-16 JSON schema marker after any differently encoded warning prefix and
raw-decode one JSON object from that aligned suffix. UTF-8 logs similarly use
the schema marker. No replacement character is accepted within the parsed
object; warnings are not copied into the committed report/summary. q4.log is
UTF-8: 1 passed in 10.74s. Local parser evidence: work/wp3.6p/r10/parse.log,
parse-methods.json, parsed *-summary.json and compact-facts.json.

The 5a .meta and .stdout read-only receipts confirm EXIT 0, wall 309s, moment
2026-10-30T05:20:40Z-05:25:50Z and disk 188,759,597,056 -> 186,750,087,168.
The existing 5a ledger row retains its previously supplied 73-read / zero
refusal / zero round-trip-problem / kept-boolean counts; its output directory
and owner records were NOT opened. Per-class runner read/fidelity in the new
report comes independently from 5c-16. No permissive-test success was substituted
for the actual read counts. Every newly supplied receipt now has a command,
counts, EXIT, wall, disk before/after and measurement moment in the table.

5c-8 ran on a8c9778d at 09:24:33Z, before turn 9 committed 790541e7 at
09:33:36Z. It STANDS: ASTs of verify_export / _export_checks / _source_icc /
_d63_output / _png_metadata / _base / _owner_class_matches / _observed_class /
_selection / load_class_map / _safe_record are identical across those commits.
Turn 9's only reachable export-summary difference is additional orientation
flags/zero class counters; no existing export figure or selection can change.
Its orientation decoder/crop helpers are not called by export. Audit evidence:
work/wp3.6p/r10/audit.log and report-facts.json. No STOP/rerun recommendation.

### Recorded results and delivered report

NEW docs/reports/wp3.6p-real-photos.md contains per-class read/fidelity, HEIC
layout, colour/ICC, AD-24 outcomes and thumbnail counts, neutral 16-bit/8-bit
runner V5/D53/V9 figures, both largest-photo memory records and separately
labelled estimate/tree-RSS/device-peak ratios. Z and M retain their own rows
and denominators. No scene/look assessment, source metadata value or footage
path is promoted. Measurement moments are not photo capture times.

- 5b-r2: all 62 attempted; 0 read/orientation/oracle failures; HEIC-0 14 pass /
  9 inconclusive / 7 rounded last / 0 failed; HEIC-90 3/0/0/0; HEIC-180
  20/0/0/0; HEIC-270 13/3/0/0. Rounded is independent of pose outcome, not an
  extra pass. Designed EXIT 1 remains for 12 inconclusives, never a product
  finding or hidden pass. The 90/180/270 classes are not mostly inconclusive;
  no further thumbnail discriminator is commissioned. All first-edge counts 0.
- Export: 5c-16 per-class V5/D53/V9 passes equal n (23,3,20,16,2,8,1 in
  labelled rows); 5c-8 one per class, all three checks pass. Requested/output
  depths match, GPU reasons, runner exits 0, no failed check/D63 defect. Raw
  max/mean 0.0 /255 per class for each of 5c-8 (8-bit) and 5c-16 (16-bit);
  quantised max worst 7.569789888e-06 /255 in each leg, with individual
  class means in /255 units in the report. At 16 bits the written values equal
  the writer-rounded reference exactly up to float32 representation, not a
  half-LSB error (CHARC e0c7b856). Tagged ICC byte matches are
  distinct from Z/M expected absence; no assertion of ICC present on Z/M.
- Largest-photo c3-default legs: estimate 6,128,796,496 bytes vs free-before
  8,189,378,560; default GPU with tree RSS 1,926,164,480 and device peak
  4,108,320,768; forced CPU tree RSS 3,138,392,064 and device peak at baseline
  145,752,064. Ratios estimate/tree RSS 3.181866 and 1.952846; default
  estimate/device peak 1.491801. This 6.13 GB admission estimate versus
  4.11 GB sampled GPU peak is a Limit: conservative by design (V16 / AD-21),
  with conservatism assessment deferred to WP5.2, not fixed here. The forced
  CPU characterisation is 3.14 GB tree RSS / 58.4 s for this 24.5 MP HEIC at
  16 bits, not an automatic capacity-fallback event.
  All recorded limits pass, sample errors empty;
  actual capacity fallback was not exercised. The approved sampling/race,
  query-instant/scope, cadence and alternate-config Limits are explicit.

For CHARC: Q3 says confirmed on the Apple layouts present with the bounded
50-pass / 12-inconclusive / 7-rounded / zero-failure evidence; identity 23 and
agreeing nonzero-irot/tag 39, no owner tag-only/irot-only witness. AD-24 status
is CHARC's accept decision; D63/spec :567 edits are the owner's. Q6's Result 2
photo row is ready for accept on about 24.5 MP, subject to Limits/B/gate; no
48 MP or V15 closure. Q8 DR-42(a)/(c) lack the relevant real PNG/TIFF missing-
ICC/tiff.py-touch witness; DR-43 zero sanitise drops per class and no IF-6 or
io.photo change. The new MINOR ColorSpace-1-as-untagged observation is JPG-Z
8 and JPG-M 1, each in its own row, no colour change or product fix. Register
rulings remain CHARC's. No debt/spec/source edit is made by this report turn.

### Verification loop and final light checks

Suspected 5c-8 staleness was independently rejected by the AST/call-path audit.
Suspected encoding corruption was rejected by byte-based suffix detection,
JSON decoding and no U+FFFD inside summaries. Cross-checked the extracted
class counts, depths, devices, errors, rounded edges, memory values and all
seat moments/disk receipts against the dispatch; they agree. Corrected the
first report draft's blanket UTF-16 statement using the actual parser-method
facts: 5b/5b-r2 are UTF-8. This was a report wording correction, not a tool fix.
Final report/ledger claims and privacy/scope are verified below; no new issue
or STOP found in the last pass. No new Reviewer A round is claimed.

Outputs captured under work/wp3.6p/r10/; no full suite/hardware/gate rerun.
PowerShell sets PYTHONPATH=scripts; the sandbox shim remains mandatory for
cell pytest despite the seat request's shorter command spelling.

| Check | Exact command | Observed result |
|---|---|---|
| Selected light tests | PYTHONPATH=scripts uv run pytest -q tests/test_photo_verify.py -m "not footage" -p sandbox_mkdir_shim -p no:cacheprovider --basetemp=work/wp3.6p/tmp -o junit_family=legacy --junitxml=work/wp3.6p/r10/final.xml | EXIT 0; 117 passed, 1 deselected in 19.10s; pytest.log / final.xml |
| Ruff | uv run ruff check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; All checks passed!; ruff.log |
| Format | uv run ruff format --check tools/photo_verify.py tests/test_photo_verify.py | EXIT 0; 2 files already formatted; format.log |
| Strict typing | uv run mypy | EXIT 0; Success: no issues found in 147 source files; mypy.log |

No test warning; existing uv environment mismatch notice is unchanged. Actual
light exports force CPU and memory samplers are stubs. No owner/GPU node ran.
Privacy grep (privacy.log / privacy-facts.json): PASS, zero prohibited
matches across report, ledger, tool and six extracted commitment-facing safe
summaries (161 records, including repeated runs). Patterns: quoted source-value
assignment keys Make / Model / GPSLatitude / GPSLongitude / GPSAltitude /
GPSDateStamp / GPSTimeStamp / MakerNote / body-camera-lens serial / original-
digitized capture time; drive-absolute paths, UNC paths and absolute Unix
source-style roots; the planted private camera/GPS markers and synthetic input
root. Only existing review-evidence absolute references are excepted, not any
footage path. Every summary record equals the tool's fresh explicit allow-list
projection. Owner ICC descriptions are Display P3/absent, output Software is
Clearwater/absent; timestamp-valued record strings occur only as measured_at_utc,
never capture time. Source field NAMES and presence/kept booleans are permitted.

Final byte/scope/report-claim verification is recorded in final-validation.log:
report and ledger only, tool/tests unchanged; 0 CR, ASCII/LF/final newline,
no trailing whitespace; parsed receipt counts/commands/disk/moments and report
tables/ratios checked against local summaries. No private source path/value
was introduced or committed; no raw runner/EXIF data is copied to the report.

Reviewer B must EXECUTE (650bea20), with the succeeded-style execution receipt
before reading findings, then the ONE two-leg gate at dispatcher seat. A3's
conditional convergence is not substituted for returned B/gate. At this
report boundary near 200K, YIELD as dispatched; dispatcher fills current depth.

## Turn 11: CHARC report items (dbf02ad7, e0c7b856)

Turn 10 is committed as 271b127c; brief fold 6569355c supplied by dispatcher.
Depth after turn 10 is **234,009 tokens (session 3)**. This is the dispatched
short report-only turn, ending at this report/handoff boundary before B.

- UNIT, CHARC e0c7b856: 5c-16's written 16-bit values equal the writer-rounded
  reference exactly, up to float32 representation. Quantised max
  7.57e-06 /255 = 2.97e-08 in [0,1]; half a 16-bit LSB would be
  1.95e-03 /255. raw_max_255 is 0.0 /255 in every class. 5c-8's 8-bit
  quantised max is 7.56979e-06 /255, with raw max/mean 0.0 /255 in every
  representative. Report headers/prose and the turn-10 figures now state
  depth and /255 units explicitly; no error is characterised as half an LSB
  or rounding-limited. AD-11 limits remain max <=2 /255, mean <=0.2 /255
  for both legs. No numeric measurement changed.
- CLASSES: all seven rows remain separate, with no pooled statistics row.
  The report names the eight JPG-Z files and the one JPG-M file from the
  previously parsed 5c-16 safe records as the class map's no-ICC assumed set.
  The other classes have zero assumed readings; no class map or footage read.
- ESTIMATE LIMIT: 6,128,796,496 bytes (6.13 GB) versus sampled GPU peak
  4,108,320,768 bytes (4.11 GB), ratio 1.491801 (about 1.5x), is explicitly
  a Limit. The V16 / AD-21 admission estimate is conservative by design;
  whether it is too conservative is a WP5.2 question, carried by CHARC into
  that brief. No fix here. Forced CPU is CPU-fallback characterisation for
  one 24.5 MP HEIC at 16 bits: tree RSS 3,138,392,064 bytes (3.14 GB),
  wall 58.4 s. It remains an explicitly forced leg, not proof of automatic
  capacity fallback.

Verification: report/ledger privacy scan repeats the recorded private-value-key,
Windows drive/UNC/Unix absolute-source-path and planted-marker patterns from
work/wp3.6p/r10/privacy-facts.json; the existing review-evidence references
remain excepted. Capture-time key assignments and EXIF date/time-shaped
values are also checked. Zero prohibited matches. Both changed files are
ASCII/LF with 0 CR, final newline and no trailing whitespace. Tool/test bytes
are unchanged; no pytest, ruff, format or mypy run in this report-only turn.
Local check receipt: work/wp3.6p/r11/validation.log. Reviewer B executing and
the ONE two-leg gate remain pending at the dispatcher seat. YIELD.

## Seat-run ledger

| Run | Command / scope | Counts | EXIT | Wall time | Free disk before / after | Evidence / conditions |
|---|---|---|---|---|---|---|
| R0-O | Historical request above, psutil str fix; two HEICs | 2 probed; 61 HEVC streams each; mapped stream 0 was a tile | 0 | 2 s | 189,229,633,536 / 189,228,720,128 bytes | 2026-10-30T04:42:08Z; oracle-facts.json; mapped tile pose scores VOID |
| R0-E | Historical request above, psutil str fix; IMG_6690 neutral PNG16/default device | done 1, others 0; one PNG 51,873,583 bytes; GPU | 0 | 37.14 s | 189,175,160,832 / 189,113,147,392 bytes | 2026-10-30T04:43:51Z; export-facts.json; dispatcher-seat timing observation |
| 5a | uv run python tools/photo_check.py --name wp3.6p-io; configured folder, all 73 | photos 73; read_ok 73; refused 0; round_trip_problems 0; verdict ok 73; gps_kept and maker_note_kept each 73/73 | 0 | 309 s | 188,759,597,056 / 186,750,087,168 bytes | Dispatcher supplied: 2026-10-30T05:20:40Z-05:25:50Z; work/wp3.6/photo-check/wp3.6p-io/ in main tree; unchanged instrument's existing root; NOT opened/rerun by cell |
| 5b | `uv run python tools/photo_verify.py orientation --class-map work/wp3.6p/class-map.json --name wp3.6p-5b` | selected 62 / attempted 17, HEIC-0: 7 pass, 9 inconclusive, 1 oracle_failed IMG_6764.HEIC; incomplete | 1 | 52.6347192 s | 189,399,732,224 / 188,959,887,360 bytes | 2026-11-01T09:22:07.2291929Z; a8c9778d; old strict oracle size STOP; CHARC 2aaa7e0a granted narrow equivalence; seat-turn8/5b.json/.log |
| 5b-r2 | `uv run python tools/photo_verify.py orientation --class-map work/wp3.6p/class-map.json --name wp3.6p-5b-r2` | selected/attempted 62; read failed 0; HEIC-0 pass/inc/rounded/fail 14/9/7/0; HEIC-90 3/0/0/0; HEIC-180 20/0/0/0; HEIC-270 13/3/0/0; incomplete solely due to inconclusives | 1 | 227.1362275 s | 188,824,584,192 / 187,323,396,096 bytes | 2026-11-01T09:42:38.0493140Z; 790541e7; restarted from start; 7 rounded all last, no orientation/oracle failure; 50 pass / 12 inconclusive accounting; seat-turn8/5b-r2.json/.log |
| q4 | `uv run pytest -q tests/test_photo_verify.py::test_owner_heic_orientation_four_irot_classes --basetemp=work/wp3.6p/seat-q4-tmp -p no:cacheprovider` | 1 passed in 10.74s; four named HEICs, not skipped | 0 | 11.9233379 s | 188,957,294,592 / 188,924,227,584 bytes | 2026-11-01T09:24:21.8867497Z; unrestricted dispatcher seat, no sandbox shim; receipt q4.log; seat-turn8/q4.json/.log |
| 5c-8 | `uv run python tools/photo_verify.py export --class-map work/wp3.6p/class-map.json --name wp3.6p-5c-8 --bit-depth 8 --representatives-only` | 7 selected/attempted, complete; one per class, V5/D53/V9 1/1/1 each; depth 8/8, GPU, no failed check | 0 | 55.4948595 s | 188,924,223,488 / 188,923,252,736 bytes | 2026-11-01T09:24:33.9033965Z; a8c9778d before turn 9; export evidence stands by AST audit; seven successful PNGs measured/removed; seat-turn8/5c-8.json/.log |
| 5c-16 | `uv run python tools/photo_verify.py export --class-map work/wp3.6p/class-map.json --name wp3.6p-5c-16 --bit-depth 16` | 73 selected/attempted, complete; class n HEIC-0 23, HEIC-90 3, HEIC-180 20, HEIC-270 16, JPG-A 2, JPG-Z 8, JPG-M 1: V5/D53/V9 all n; depth 16/16, GPU, no failed check | 0 | 487.7224381 s | 179,173,720,064 / 178,657,312,768 bytes | 2026-11-01T18:19:13.2348080Z; EXCLUSIVE 18:19:13Z-18:27:21Z; seven representatives retained, 66 others removed; Z/M separate; seat-turn8/5c-16.json/.log |
| 5d-default | `uv run python tools/photo_verify.py memory --class-map work/wp3.6p/class-map.json --name wp3.6p-5d-default --file IMG_6690.HEIC --bit-depth 16 --exclusive` | 1 HEIC-180; GPU; estimate 6,128,796,496; RSS peak 1,926,164,480; device peak 4,108,320,768 bytes; within limits, no fallback/errors | 0 | 11.3000835 s | 178,652,057,600 / 178,511,532,032 bytes | 2026-11-01T18:28:34.6247676Z; seat-declared EXCLUSIVE, c3 defaults / fresh runner / no neutral; sampler_errors empty; seat-turn8/5d-default.json/.log |
| 5d-cpu | `uv run python tools/photo_verify.py memory --class-map work/wp3.6p/class-map.json --name wp3.6p-5d-cpu --file IMG_6690.HEIC --bit-depth 16 --exclusive --force-cpu` | 1 HEIC-180; CPU: forced; RSS peak 3,138,392,064; device peak 145,752,064 bytes (baseline); within limits, no errors | 0 | 58.4422013 s | 178,511,527,936 / 178,369,970,176 bytes | 2026-11-01T18:28:45.9751258Z; seat-declared EXCLUSIVE, same photo/c3 defaults / fresh forced-CPU runner; sampler_errors empty; seat-turn8/5d-cpu.json/.log |

## Depth and handoff

| Turn / boundary | Dispatcher-read depth | Action |
|---|---|---|
| 1 / round 0 | 118,810 tokens (dispatcher reading after turn 1) | R0 committed 6cc7cdb; evidence and ruling received on turn 2 |
| 2 / RED | 168,789 tokens (dispatcher reading after turn 2) | RED committed a66eea6; GREEN dispatched on turn 3 |
| 3 / GREEN | 240,970 tokens (dispatcher reading after turn 3; previous session) | GREEN committed 70bd699; previous session retired at depth boundary |
| 4 / Reviewer A round 1 adjudication | 114,259 tokens (dispatcher reading after turn 4; FRESH session) | Ledger committed f2396b0e; 16 dispositions; no remediation; R1-QA/QB ruled before turn 5 |
| 5 / Reviewer A round 1 remediation | 178,999 tokens (dispatcher reading after turn 5) | 13 tool fix groups plus RED/GREEN controls; committed 7a3810af; #16 Limit staged in ledger; all light checks green; A2 dispatched on turn 6 |
| 6 / Reviewer A round 2 adjudication | 101,571 tokens (dispatcher reading after turn 6; transcript context compaction) | Adjudication committed 081f851c; 10 dispositions, 21 passing probes; R2-QA ruled before turn 7; turn-5 reading 178,999 was before compaction |
| 7 / Reviewer A round 2 remediation | 187,455 tokens (dispatcher reading; session 2 retired) | 4 tool fix groups plus RED/GREEN controls, 1 test-only group; 87 light cases pass; 5 Limit/report lines staged; YIELD for A3 |
| 8 / Reviewer A round 3 adjudication and terminating clean-up | 152,054 tokens (dispatcher reading; session 3) | 9 advisories adjudicated; 3 tool fix groups with RED/GREEN controls; 102 light cases pass; conditional A convergence; YIELD for seat runs and executing B |
| 9 / odd-width size equivalence, CHARC 2aaa7e0a | 184,466 tokens (dispatcher reading; session 3) | 7 RED cases on a8c9778d; 15 new controls, 117 light passes; both crop edges and class counts; YIELD for 5b restart |
| 10 / seat rows and real-photo report | 234,009 tokens (dispatcher reading; session 3) | 5b-r2 / 5c-8 / 5c-16 / both 5d legs parsed; q4 and 5a receipts checked; report delivered; light checks green; YIELD for executing B |
| 11 / CHARC report items | PENDING dispatcher reading; session 3 | Report units/classes/estimate Limit clarified; docs-only privacy and byte checks; YIELD for executing B |

Evaluate near 200K; stop at a step boundary near 250K per this dispatch.
The supplied readings are 178,999 after turn 5 and 101,571 after turn 6,
with transcript context compaction between them. Evaluated at this remediation
boundary; this turn ends here as dispatched. No current cumulative token number
is invented; turn 7 is 187,455 (session 2), turn 8 is 152,054 (session 3);
turn 9 is 184,466 (session 3); turn 10 is 234,009 (session 3). Evaluated at this
report/handoff boundary near 200K; STOP/YIELD here as dispatched, before B.
Historical turn-1 validation was limited to the ledger's ASCII/LF and owned-file diff.
Observed validation: PASS for ASCII, LF, final newline, no trailing whitespace,
both embedded Python RUN REQUEST snippets parsing, seven-class example JSON
parsing, and absence of a literal footage path. Evidence:
`work/wp3.6p/r0/ledger-validation.log`. Snippets were parsed, not executed.
Turn 1 changed only this ledger. Turn 2 changed the ledger and new test file;
no src, frozen interface, dependency, fixture, existing test, local config or
other-worktree change. No deletion, commit, mailbox post or footage read was
made by the cell. Turn-2 RED and turn-3 GREEN evidence is recorded above.
