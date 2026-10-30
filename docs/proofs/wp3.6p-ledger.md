# WP3.6P cumulative ledger

## Dispatch and current boundary

- Package: WP3.6P, CODEX lane, STRONG tier; CHARC's FINAL rulings govern.
- Dispatch base verified: `c3bf602fe9ac94cd5df25499d97f3a2bc439bb72`.
- Turn 1 / round 0: map, design, RED roster and seat RUN REQUESTs only.
  No tool or test code is introduced. No owner photo was opened by the cell.
- `uv sync`: already run by the dispatcher before dispatch, as stated in the
  binding turn-1 instructions. Not repeated: this sandbox cannot reach the index.
- Initial `git status --short`: empty. The existing isolated worktree is retained.
- No STOP or question from the source mapping. Oracle selection remains PENDING
  the requested seat evidence; inability of FFmpeg to decode the primary selects
  the ruled thumbnail fallback, rather than stopping the package.
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

- `orientation`: `--oracle ffmpeg|thumbnail` (required, selected from round 0),
  `--max-side 256`. Selects HEIC only, runs the independent pose comparison, and
  records all eight scores, dimensions and discrimination margins. A wrong-size
  candidate is marked shape-mismatch, not silently omitted.
- `export`: `--bit-depth {8,16}` (required), `--force-cpu` (default false),
  `--representatives-only` (select exactly seven class representatives). Every
  export uses the runner with neutral parameters, selected depth and its default
  device unless explicitly forced for synthetic tests. This yields 73 runs at
  16 bits and seven representative runs at 8 bits at the seat.
- `memory`: `--file NAME` (one mapped file), `--force-cpu`, `--bit-depth {8,16}`
  (default 16). Uses c3 DEFAULT correction parameters, not neutral parameters,
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

FFmpeg oracle: independently decode the PRIMARY image with `-noautorotate`,
validate full stored extent (a decoded tile/auxiliary/thumbnail is not primary),
apply its associated irot/imir transforms in association order, then downscale.
Read these associations independently of product AD-24 selection. For tag-only
synthetic fixtures, the expected pose is the known generated upright image;
raw EXIF is read independently. The four fixtures also cross-check the transform
code against that generated reference, so the oracle cannot merely share a
faulty product decision. Never call `heic_tag_to_apply` to build the reference.

If round 0 shows FFmpeg cannot deliver the Apple primary, select the HEIC's own
thumbnail item through pillow-heif, whose item transforms are applied by libheif.
No product EXIF rule is used. Verify thumbnail identity and transformed size;
absent/unreadable thumbnail or a non-discriminating comparison is an oracle
failure, not an acceptance. Fixture tests use their known upright source when
no thumbnail exists. Record which independent oracle actually supported each
result; do not label generated-fixture evidence as an owner-thumbnail check.

Compare the product read with the upright oracle and all seven other dihedral
poses at a common small size, preserving aspect ratio. Record mean absolute
RGB differences in 1/255 units, the winning pose, upright error, nearest-other
error, margin and shape mismatches. Synthetic fixtures retain the established
<6 upright / >10 other-pose bounds. Owner comparisons use the same explicit
bounds, not an automatically relaxed threshold: if independent decoders or
thumbnails cannot meet them, report the evidence and STOP for a ruling.

Per-photo allow-listed record groups:

| Group | Fields (scalars, enums or explicitly typed lists only) |
|---|---|
| Identity | schema, command, file (bare Phone-relative name), class, candidate_group (none/Z/M), read_ok, failure_code |
| Format | source_format, source_bytes, stored_size, decoded_size, source_bit_depth, orientation_tag |
| HEIC | primary_type, grid, irot, imir, clap, ispe, auxiliary_count, thumbnail_count; no auxiliary payload |
| Colour | primaries, transfer, assumed, icc_present, icc_description, icc_valid, icc_bytes, icc_md5 |
| EXIF | raw_exif_present, exif_present, sanitise_dropped, fields_before/after (names), field_count_before/after, changed_kept_fields (names), gps_ifd_present, gps_kept, maker_note_present, maker_note_kept |
| Orientation | oracle_kind, oracle_size, scores_by_pose, shape_mismatches, winning_pose, upright_mean_255, nearest_other_mean_255, margin_255, orientation_ok |
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

## RUN REQUEST R0-O: FFmpeg primary/orientation feasibility

NOT RUN. Orchestrator only, from the worktree root in PowerShell. Planning
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
free_before = psutil.disk_usage(root).free
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
    'disk_free_after_bytes': psutil.disk_usage(root).free, 'records': records}
target.write_text(json.dumps(facts, indent=2, ensure_ascii=True) + '\n', encoding='ascii')
print('R0-O: format facts recorded; return only oracle-facts.json facts')
'@ | uv run python - > work/wp3.6p/r0/oracle-request.log 2>&1
```

`oracle-facts.json` answers: primary grid/non-grid and associated irot/imir;
stored/transformed dimensions; which streams FFmpeg exposes; its rotation side
data; raw/default decoding EXIT and dimensions; all eight raw-to-default pose
scores; thumbnail item count and decoded sizes for fallback. For a non-mirrored
source the associated irot predicts pose 1/8/3/6 for 0/90/180/270 respectively.
The numeric raw-to-default comparison tests that prediction without a visual
look check; it is feasibility evidence, not yet the product/oracle comparison.
Return those scores as format evidence, not scene descriptions. An output
matching only a tile's dimensions is NOT a primary
decode. If a full raw primary cannot be obtained, use Q3's thumbnail oracle for
owner files; return whether each tested HEIC has a usable thumbnail. If FFmpeg
does deliver the primary, return which stream and whether raw/default pixel
comparison agrees with stored/turned orientation. These results determine the
tool's actual oracle mode before the GREEN implementation turn.

## RUN REQUEST R0-E: one largest-size neutral runner export

NOT RUN. Orchestrator only, from the worktree root in PowerShell. Selected file:
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
free_before = psutil.disk_usage(root).free
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
    'disk_free_after_bytes': psutil.disk_usage(root).free,
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

## RED roster for the next turn

All new tests are parallel-leg, use tmp_path and synthetic/committed WP2.3
fixtures, except the ONE expressly marked footage test. No gpu test is added.
Committed fixtures are read-only; any mutated copy is under tmp_path.
Base `c3bf602` has neither new module nor test file. The initial RED is the
intentional import/collection failure for `photo_verify`; after its API exists,
the assertions below must fail on their named planted bad implementation.

| Planned test / cases | RED baseline and discriminating failure |
|---|---|
| `test_orientation_matches_generated_upright`, four heic-ad24-* | c3bf602: missing module. Generated asymmetric upright reference, all eight poses and shape checks catch a wrong pose. No oracle derived from product AD-24. |
| `test_orientation_rejects_exif_always`, both | c3bf602: missing module; planted extra tag application fails `orientation_ok`, naming heic-ad24-both. |
| `test_orientation_rejects_exif_never`, exif-only | c3bf602: missing module; planted omission of additional tag fails `orientation_ok`, naming heic-ad24-exif-only. |
| `test_export_v5_v9`, heic8-gradient-none / png16-lowred-display-p3 / jpeg-gradient-none, depths 8 and 16 | c3bf602: missing module; actual runner output must satisfy V5/D53 rules, AD-11 quantised bounds and applicable raw bounds. P3 PNG16 at depth 8 witnesses below-source quantisation. |
| `test_export_rejects_off_neutral_gamma` | c3bf602: missing module; planted gamma default instead of neutral fails `v9_identity`, not merely a pixel inequality in the test. |
| `test_export_rejects_dropped_iccp` | c3bf602: missing module; planted writer removes iCCP from a profile-bearing export and fails `v5_icc_equal`/`v5_icc_present` by name. |
| `test_export_d63_and_kept_exif` | c3bf602: missing module; synthetic EXIF contains kept entries and thumbnail. Assert Orientation normal, dimensions, Software equality boolean, thumbnail absence and kept-field comparison; planted loss of a kept entry fails `v5_kept_exif` by name. |
| `test_summary_and_stdout_exclude_private_values` | c3bf602: missing module; tmp JPEG has synthetic GPS and Make in a tmp footage folder. Parse every safe record/summary and stdout: planted values and absolute footage path must be absent, including errors/nested extra keys. No comparison value is printed. |
| `test_all_records_and_runner_targets_stay_guarded` | c3bf602: missing module; spy on writes and runner arguments. A planted escaped target is refused; no target or deletion escapes the working guard or reaches footage. |
| `test_memory_records_sampler_facts`, default and force CPU | c3bf602: missing module; tiny still and stubbed samplers provide known estimate/free/reason/RSS/device peaks. Force CPU must record `CPU: forced`; missing sample is null plus failure, never a zero-peak pass. |
| `test_class_map_validation_and_separate_candidate_rows` | c3bf602: missing module; validate schema/counts/traversal/duplicates and separate JPG-Z/JPG-M rows. Reject a planted pooled candidate metric. |
| `test_owner_heic_orientation_four_irot_classes` | c3bf602: missing module; ONE `footage` test, reason beside marker: serial owner-photo I/O. IMG_6703/6718/6690/6720, independent oracle upright checks. Skip only absent footage; when available, missing/refused photo or unusable oracle fails. Cell does not execute it. |

Next-turn RED command (PowerShell environment spelling of the required shim):

```powershell
$env:PYTHONPATH = 'scripts'
uv run pytest -q tests/test_photo_verify.py --basetemp=work/wp3.6p/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip" *> work/wp3.6p/red.log
```

After GREEN: same touched-file selection/shim, targeted ruff and `uv run mypy`,
all redirected under work/wp3.6p. Dispatcher runs format check at its seat due
to the known sandbox artifact. No full suite before Reviewer B; ONE two-leg
gate on the final candidate after reviews and seat evidence; no fullclip or
harness gate for this owned file set.

## Review ledger and verification record

Reviewer A runs via dispatcher (Claude opus/high, read-only) between turns.
Each adjudication turn changes only this ledger and yields before remediation.
Convergence is zero NEW in-envelope blocking findings. At round 5 and each fifth
round: yield for dispatcher approval under the fill; no self-authorised extension.

| Round | Critical | Major | Minor | In / out envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Verdict / evidence | Depth |
|---|---:|---:|---:|---|---|---|---|---|---|
| 0 | - | - | - | - | - | 0 | None; ledger only | Mapping/design complete; R0-O/R0-E NOT RUN; A not started | Dispatcher fills |

| Suspected item | Independent confirmation | Disposition |
|---|---|---|
| Existing photo_check's success might prove every photo reads | Code at tests/test_photo_check.py:146 explicitly permits refusals | Rejected inference; new wrapper requires every selected photo read. No product defect asserted. |
| Current reader might still use the opener named in AD-24 prose | `_read_heic` at reader.py:250 uses open_heif and later returns the additional-tag decision | Current mechanic mapped explicitly; no behavior defect or interface change inferred. |
| Generic runner records might be safe to copy wholesale | headless_export.py:48-57 documents malformed-tag text in failures; record_object retains warning/failure strings | Confirmed privacy hazard for copying raw records; explicit safe schema planned. No existing tool edited. |

## Seat-run ledger (pending)

| Run | Command / scope | Counts | EXIT | Wall time | Free disk before / after | Evidence / conditions |
|---|---|---|---|---|---|---|
| R0-O | PowerShell request above; two named HEICs | PENDING | NOT RUN | PENDING | PENDING | work/wp3.6p/r0/oracle-facts.json; no cell footage access |
| R0-E | PowerShell request above; one largest-size neutral PNG16 | PENDING | NOT RUN | PENDING | PENDING | work/wp3.6p/r0/export-facts.json; exclusive timing observation |
| 5a | photo_check --name wp3.6p-io, all 73 | PENDING | NOT RUN | PENDING | PENDING | Dispatcher; unchanged instrument has its existing wp3.6 output root |
| 5b | photo_verify orientation, all 62 HEICs | PENDING | NOT RUN | PENDING | PENDING | Oracle determined by R0-O |
| 5c-16 | photo_verify export, all 73, neutral/depth 16 | PENDING | NOT RUN | PENDING | PENDING | Seven retained representative PNGs |
| 5c-8 | photo_verify export, seven representatives, neutral/depth 8 | PENDING | NOT RUN | PENDING | PENDING | PNGs measured then removed by tool |
| 5d-default | photo_verify memory, IMG_6690.HEIC/default device/c3 defaults | PENDING | NOT RUN | PENDING | PENDING | EXCLUSIVE; default processing, not neutral |
| 5d-cpu | photo_verify memory, same photo/force CPU/c3 defaults | PENDING | NOT RUN | PENDING | PENDING | EXCLUSIVE; 16 GB and 8188 MiB comparisons |

## Depth and handoff

| Turn / boundary | Dispatcher-read depth | Action |
|---|---|---|
| 1 / round 0 | PENDING dispatcher reading; not estimated by cell | Yield for oracle/timing evidence and next-turn dispatch |

Evaluate near 200K; stop at a step boundary near 250K per this dispatch.
Turn 1 validation is limited to the ledger's ASCII/LF and owned-file diff.
Observed validation: PASS for ASCII, LF, final newline, no trailing whitespace,
both embedded Python RUN REQUEST snippets parsing, seven-class example JSON
parsing, and absence of a literal footage path. Evidence:
`work/wp3.6p/r0/ledger-validation.log`. Snippets were parsed, not executed.
Final scope check: only this ledger is untracked; no tracked-file changes.
No pytest, lint, mypy, Reviewer A/B or owner-photo command is claimed run.
Only docs/proofs/wp3.6p-ledger.md is changed; no src, frozen interface,
dependency, fixture, existing test, local config or other-worktree change.
No deletion, commit, mailbox post or footage read was made by the cell.
