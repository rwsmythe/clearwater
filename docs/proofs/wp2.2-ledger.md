# WP2.2 ledger (interface module)

Cell: implementer-sonnet-high. Worktree `.worktrees/wp2.2`, branch `wp2.2`, base `d3bcdba`.
Spec v0.5.3, architecture DRAFT 0.1 section 3. Reviewer A rounds: none yet (round 1 is the
dedicated CHARC-ruling yield, ruling 4).

## Round-1 ruling (CHARC b7b012f7c6d5a1e6) as applied

Everything below APPROVED as tabled; PROPOSED markers removed from the code. Applied: png_bit_depth
16; video_encoder "auto" (NVENC HEVC when D74 capability says available, else libx265; provenance
records the resolved encoder, never "auto"; stated in the Settings and EncoderCapability
docstrings); quality_level "standard" (lower-case high/standard/draft); cache_limit_bytes
`20 * 10**9`; rotation int degrees, FFmpeg convention (counter-clockwise positive), normalised to
0/90/180/270; `created` a timezone-aware datetime written and read in UTC (naive refused:
ValueError on write, FormatError on read); shape (H, W); stage dependencies own-parameters only;
stub `parameters = ()` with the docstring note; KeyError / ValueError for render / analyze.
Settings stays kw_only, section-3 order, all fields now defaulted. Additions kept.

## Round 1: proposals for CHARC's ruling (historical)

Implemented as PROPOSED (docstrings say so). Rulings apply exactly; each row is one decision.

### (a) The nine unnamed types

All frozen dataclasses in `src/clearwater/interfaces/`. "Why" is the reason the field exists.

`VideoStreamInfo` (video.py), starts from the IF-5 comment:

| Field | Type | Clause | Why |
|---|---|---|---|
| codec | str | IF-5 comment | e.g. "hevc" |
| width, height | int | IF-5 comment | coded size |
| bit_depth | int | IF-5, D114 | 8 or 10 |
| pix_fmt | str | IF-5 | e.g. "yuv420p10le"; chroma format matches source (D114) |
| chroma_siting | str | IF-5 "chroma siting", AD-10 | "left", "center", ..., "unknown" (ffprobe `chroma_location`) |
| color | ColorDescription | IF-5, D54 | stream tags / assumed defaults |
| frame_rate | Fraction | IF-5 "(avg)" | exact, no float |
| time_base | Fraction | IF-5, D95 | pts ticks |
| nb_frames | int \| None | IF-5 | container may not say |
| rotation | int | IF-5 "rotation (display matrix)", D105 | degrees, 0 = none. OPEN: sign/convention (propose ffprobe's `rotation` value) |
| vfr | bool | IF-5, D95 | |

`AudioStreamInfo`: index int; codec str; sample_rate int; channels int; start_s Fraction (first audio
pts, for audio sync, D105; the WP1.5 report measures sync as first audio pts minus first video pts).

`DataStreamInfo`: index int; codec_tag str ("gpmd", "tmcd"; IF-5 comment, D105).

`EditEntry` (D94, AD-22, WP1.5 edit-list rows `duration`, `media_time`, `rate`): segment_duration_s
Fraction; media_time_s Fraction \| None (None = empty edit); media_rate Fraction.

`Fault`: kind (Literal) "truncated" | "unreadable_tail" | "missing_tags" | "hlg" | "pq" | "gp_log" |
"sidecar" (the seven kinds the IF-5 comment lists; D86, D54, AD-16, D83); severity Literal "refuse" |
"warn" | "exclude" (refusal for hlg/pq, warn for the rest, exclude for sidecar; the mapping of
kind to severity is the producer's, not the type's); message str.

`GoProInfo` (IF-5 "firmware, protune, colour profile (PTCL) from GPMF settings"; AD-16;
WP1.5 section 7 keys `FMWR`, `PRTN`, `PTCL`): firmware str \| None; protune bool \| None;
color_profile str \| None. Not proposed: camera model (`MINF`), `HDRV` (AD-16 leaves HDR mode
PENDING).

`PhotoMetadata` (IF-6, D63, AD-17 "EXIF bytes from Pillow's Image.Exif", AD-24): source_format str
("heic" | "jpeg" | "png" | "tiff"); exif bytes \| None (source block; the sink applies the D63 edits:
Orientation reset, thumbnail dropped, Software set); orientation int (source tag 1-8, 1 when absent;
informational, the pixels already carry it).

`CacheEntry` (IF-7, D71, D113): key CacheKey; pts_ticks tuple[int, ...] (proxies stored, ascending,
D95); stages tuple[str, ...] (stages with source-only statistics); size_bytes int (for the limit).

`SinkReport` (IF-5 comment "frames written, warnings, best-effort items not carried"; D105):
frames_written int; warnings tuple[str, ...]; not_carried tuple[str, ...].

### (b) Annotation gaps (mypy strict)

| Place | Section 3 | Proposed | Clause / reason |
|---|---|---|---|
| `ArrayBackend.asarray` `a` | none | `ArrayLike` | narrowest NumPy type; CuPy accepted at run time (ruling 1) |
| `asarray` `dtype` | `dtype=...` | `DTypeLike = ...` (protocol keeps the ellipsis; stub default `np.float32`) | IF-3 types say "always float32"; stub refuses other dtypes |
| `pyramid_expand` `shape` | none | `tuple[int, int]` (height, width) | arrays are `(H, W, 3)`; OPEN: or a 3-tuple |
| `to_host` return, `Statistics` values, `proxy` | bare `numpy.ndarray` | `NDArray[Any]`; the uint8 proxies `NDArray[np.uint8]` | strict forbids bare generics; IF-7 comment says uint8 |
| `Parameter.default` / `neutral` | `Any` | alias `ParameterValue = bool \| int \| float \| str \| None` | None only where a parameter can be off (gain caps, D100); enums are str. OPEN: whether None is wanted |
| `Statistics` | `Mapping[str, numpy.ndarray]` | `Mapping[str, NDArray[Any]]` | as above |
| `Array` | prose | `type Array = NDArray[np.float32]` | ruling 1 |
| `ParameterSet` fields | none given | method str; parameters Mapping[str, ParameterValue]; created datetime; app_version str; source, settings Mapping[str, Any] \| None (provenance only); `format_version` is the module constant `FORMAT_VERSION = 1`, not a field | AD-13. OPEN: `created` as datetime (proposed) or ISO string |
| `Parameter.minimum/maximum` | `float \| None` | as written, inclusive bounds | |

Additions beyond section 3 (needed by tasks 5 and 6, all in `parameters.py`/`video.py`):
`ParameterSet.to_dict/from_dict` (the Settings nest uses them), `loads_object`,
`check_format_version`, `FormatError`, `UnsupportedFormatVersionError`, `ParameterProblem`,
`validate_parameter_set(parameter_set, method_id, parameters) -> list[ParameterProblem]` (problem
kinds method_mismatch, unknown_name, wrong_type, not_finite, below_minimum, above_maximum,
not_a_choice; a partial set is valid; None is legal only where the parameter's default is None),
`FaultKind`, `ProblemKind`. Interface-level `select_backend` raises NotImplementedError naming WP3.1.
Exception named `...Error` (ruff N818).

### (c) `Settings` field types and defaults

`@dataclass(frozen=True, kw_only=True)`; section 3 order kept.

| Field | Type | Default | Clause for the default |
|---|---|---|---|
| output_folder | Path \| None | None (= source folder) | D34 |
| output_suffix | str | "_corrected" | D36 |
| png_bit_depth | int (8 \| 16) | OPEN, required | D22 says user-selectable; no default stated |
| video_encoder | str | OPEN, required | D26 user choice; no default, and no encoder name strings frozen (AD-12 uses NVENC HEVC / libx265) |
| quality_level | str | OPEN, required | D75; AD-12 names High / Standard / Draft, spec 8.2 says "Standard / High / Very High" (e.g.); no default stated. Discrepancy flagged |
| ten_bit_for_eight_bit | bool | False | D76 "off by default" |
| provenance | bool | True | D91 "on by default" |
| cache_limit_bytes | int | `20 * 1024**3` | D71 "20 GB"; OPEN: GB read as GiB (proposal) or 10**9 |
| force_cpu | bool | False | AD-1 (GPU when it fits) and AD-9 (an override); no clause states "off" in words |
| last_parameters | ParameterSet \| None | None | D89 (nothing persisted yet) |

JSON: `format_version` 1, one key per field, `output_folder` as `str(path)`, `last_parameters`
nested in its AD-13 form; every field required on read; unknown keys and wrong types are
`FormatError`; another version is `UnsupportedFormatVersionError`.

### (d) c3 stage list for `StubCorrectionMethod.stages` (AD-6, WP1.4 section 7)

Statistic names drop the stage prefix (IF-3 comment style `("means", "alpha")`); arrays are the
prototype's `Statistics` fields, zeros in the stub.

| # | name | statistics (shape) | smoothed | depends_on_parameters | depends_on_stages | source_only |
|---|---|---|---|---|---|---|
| 1 | white_balance | means (3,), gains (3,) | both (AD-6: every statistic smoothable) | kappa, lambda_, c3_strength, c3_kernel_fraction, c3_mask_threshold, c3_mask_smooth_fraction | () | False |
| 2 | fusion | bounds (2,), saliency_means (2, 3) | both | white_balance_strength, max_white_balance_gain, sharpen_blur_fraction, normalisation_low, normalisation_high, gamma, sharpen_strength | ("white_balance",) | False |

Derivation: WP1.4 section 7 rows "c3 1 white balance" and "c3 2 fusion" ("as Ancuti 2018 stage 3,
with the 3C parameters in place of stage 1's"). The dependency lists are each stage's OWN
parameters, upstream ones carried by `depends_on_stages`. The strength and D99 clamp
(`white_balance_strength`, `max_white_balance_gain`) are closed-form for stage 1's gains but change
the white-balanced image, so they invalidate fusion (WP1.4 section 7). source_only is False for
both: 3C has no whole-frame compensation statistic (WP1.4 section 7, last bullets). OPEN: whether
dependency lists should repeat upstream parameters; the stub's `parameters` is `()` (WP3.2 owns the
real tuple), so these names refer to parameters the stub does not declare.

Other stub choices to confirm: `render` raises `KeyError` naming the stage for a missing stage;
`analyze` raises `ValueError` for an unknown stage; `StubStatisticsStore.invalidate_from` knows the
stage order from its constructor (default the c3 names).

## Round ledger

| Round | Critical | Major | Minor | In envelope | NEW/REOPENED | Reverts | Product / test-only | Depth |
|---|---|---|---|---|---|---|---|---|
| 1 (proposal yield) | - | - | - | - | - | - | - | 148,021 tokens / 36 turns (orchestrator) |
| R1 (Reviewer A) | 0 | 5 (3 fixed, 1 rejected as ruled, 1 raised) | 4 (3 fixed, 1 rejected, 1 raised) | all in | 9 NEW / 0 REOPENED | 0 | product (#2, #4, #5) and tests (#8, #9) | see dispatcher |

Reviewer A round 1: codex-cli (WSL) gpt-5.6-sol/high, 131,404 tokens, 40 executed commands, verdict
NEW_CRITICAL_MAJOR_FOUND. Transcript, prompt, diff and adjudication:
`C:\Users\rwsmy\clearwater-review-evidence\wp2.2\r1\`. Fixed: 2 (IF-4 member order), 4 (huge int
OverflowError), 5 (`1e400` read as inf), 8, 9 (test strength). Rejected: 1 (uint8 proxies are ruled),
6 (int for float is documented). Raised to CHARC: 3 (a gain cap defaults to 2.0 and None disables it,
which the ruled "None only where the default is None" rejects) and 7 (rotation sign: ruled CCW, but
`tools/inventory.py` normalises clockwise). Full suite before the round: 881 passed.

## Gates at the round-1 commit

ruff check, ruff format --check, mypy: clean (39 source files); `tests/test_interfaces.py` and
`tests/test_interfaces_stubs.py`: 57 passed. Full suite: not yet run (reserved for the gate before
review round 1).
