# Clearwater architecture (WP2.1, DRAFT 0.1, CHARC, 2026-10-20)

**Status:** DRAFT. Spec v0.5.3, plan v1.1. Decisions are logged in `docs/decisions.md` (AD-n);
this document states the resulting design and freezes the interfaces (plan section 8.2). Three
items are PENDING named evidence: the N6 figure (owner, Gate 1, AD-21), the frame transport
(WP2.1S, AD-2) and the photo-library verification (WP2.1S, AD-17). The owner reviews this
document and the decision log at CP4 (design freeze) with the spec revision v0.5.4.

## 1. Shape of the system

Clearwater is a PySide6 desktop application (D28) around one correction core that runs the same
code on CPU (NumPy) or GPU (CuPy) (AD-1, D107). Photos go through `io.photo` to the core and
back to a 16-bit PNG (D53). Video goes through one FFmpeg process per pass (AD-2): an
**analysis pass** that decodes every frame once, builds a 540-line proxy (AD-5) and measures the
method's whole-frame statistics in stages (AD-6), stored per frame by pts (IF-4); and an
**export pass** that decodes again, renders every frame with the smoothed statistics (AD-3) and
encodes with NVENC or libx265 while audio, timestamps, edit list and the GPMF track pass
through (D94, D105, WP1.5 SIMPLE). The preview renders from the proxy with the same statistics,
so preview and export agree (V8, AD-4). Everything above the core reaches a method only through
IF-3 (spec 10.1).

Modules (plan 8.1, AD-19): `interfaces`, `core`, `methods`, `color`, `io.photo`, `io.video`,
`analysis`, `cache`, `jobs`, `config`, `gui`, `app`. `core` and `methods` import nothing from
`io`, `jobs` or `gui`; `gui` and `jobs` reach methods only through IF-3.

## 2. Data flow

```
photo:  io.photo.read -> Image (IF-1, float32 RGB [0,1], profile kept)
        -> method.analyze (each stage, unsmoothed) -> method.render -> io.photo.write (PNG16 + ICC + EXIF)

video analysis (jobs, IF-8 progress/cancel):
        io.video.probe -> ProbeResult (IF-5)
        io.video.frames (transport AD-2) -> Frame (IF-1, pts exact)
        -> analysis.proxy (AD-5) -> cache.store (IF-7, source-only)
        -> for stage in method.stages: analyze(stage, proxy, params, smoothed earlier) -> StatisticsStore (IF-4)
        -> analysis.smooth (AD-3, per smoothable statistic, over pts)

video preview:
        cache.proxy(pts) + StatisticsStore.smoothed(pts) -> method.render -> gui (provisional first, D108, AD-15)

video export (jobs):
        io.video.frames -> method.render(frame, params, StatisticsStore.smoothed(pts)) -> io.video.sink (NVENC/libx265, copyts, audio+gpmd copy)
        -> jobs.naming / safe write (D34-D36, D83-D85) -> provenance sidecar (D90, IF-9)
```

Parameter change (AD-7): closed-form statistics update directly; others re-measure from the
first invalidated stage within the displayed frame's smoothing reach, then the rest in the
background; export waits for completion.

## 3. Frozen interfaces (IF-1 to IF-10; AD-20)

Types below are the WP2.2 contract. `Array` is the backend's array type (NumPy `ndarray` or CuPy
`ndarray`), always `float32`, shape `(H, W, 3)`, RGB, display-encoded, in `[0, 1]`.

### IF-1 Image and frame

```python
@dataclass(frozen=True)
class ColorDescription:
    primaries: str            # "bt709", "display-p3", "unknown"
    transfer: str             # "bt709", "srgb", "unknown"; HLG/PQ never reach here (refused at probe)
    matrix: str               # "bt709", "bt601", "identity" (photos), "unknown"
    range: str                # "full" | "limited"
    bit_depth: int            # 8 | 10 | 16 (source)
    assumed: bool             # True when D54 defaults were applied (warn once per source)
    icc_profile: bytes | None # photos: the embedded profile, carried to the output

@dataclass(frozen=True)
class Image:
    pixels: Array             # float32 (H, W, 3) RGB [0, 1], on `device`
    device: str               # "cpu" | "cuda:0"
    color: ColorDescription
    orientation_applied: bool # photos: EXIF orientation already applied to the pixels

@dataclass(frozen=True)
class Frame(Image):
    pts: Fraction             # exact source presentation time in seconds (ticks / time_base)
    pts_ticks: int
    time_base: Fraction
    index: int                # decode order position; informational only, never a key
```

### IF-2 Array backend

```python
class ArrayBackend(Protocol):
    name: str                                   # "numpy" | "cupy"
    device: str
    def asarray(self, a, dtype=...) -> Array: ...
    def to_host(self, a: Array) -> numpy.ndarray: ...
    def gaussian_blur(self, a: Array, sigma_px: float) -> Array: ...          # symmetric borders, 4-sigma truncation
    def pyramid_reduce(self, a: Array) -> Array: ...                           # [1 4 6 4 1]/16, keep even rows/cols
    def pyramid_expand(self, a: Array, shape) -> Array: ...                    # zero-insert, same filter, normalised
    def rgb_to_ycbcr(self, a: Array, matrix: str, range_: str) -> Array: ...
    def ycbcr_to_rgb(self, a: Array, matrix: str, range_: str) -> Array: ...
    def percentile(self, a: Array, q: Sequence[float]) -> Array: ...           # linear interpolation (R-7)
    def memory_estimate_bytes(self, height: int, width: int, method_id: str) -> int: ...
    def free_device_bytes(self) -> int | None: ...                            # None on CPU

def select_backend(settings: Settings, height: int, width: int, method_id: str) -> tuple[ArrayBackend, str]:
    """Returns the backend and a human reason ("GPU", "CPU: forced", "CPU: estimate 1,982 MiB exceeds free 1,200 MiB")."""
```

Spatial parameters are fractions of the short side (D56); the backend converts to pixels.

### IF-3 Correction method

```python
@dataclass(frozen=True)
class Parameter:
    name: str; type: Literal["float", "int", "bool", "enum"]; default: Any
    minimum: float | None; maximum: float | None; choices: tuple[str, ...] | None
    panel: Literal["basic", "advanced"]; label: str; help: str; neutral: Any   # neutral value for V9

@dataclass(frozen=True)
class Stage:
    name: str                         # "compensation" | "white_balance" | "fusion"
    statistics: tuple[str, ...]       # names produced, e.g. ("means", "alpha")
    smoothed: tuple[str, ...]         # subset of `statistics`
    depends_on_parameters: tuple[str, ...]
    depends_on_stages: tuple[str, ...]
    source_only: bool                 # True: cacheable with the proxies (D113)

Statistics = Mapping[str, numpy.ndarray]   # per stage: name -> small float array (e.g. shape (3,) for means)

class CorrectionMethod(Protocol):
    id: str                                   # "ancuti2018" | "c3"  (c3 is the default, D16)
    label: str
    parameters: tuple[Parameter, ...]
    stages: tuple[Stage, ...]                 # ordered; one stage is valid (D98)
    def analyze(self, stage: str, image: Image, params: Mapping[str, Any],
                earlier: Mapping[str, Statistics]) -> Statistics: ...
    def render(self, image: Image, params: Mapping[str, Any],
               statistics: Mapping[str, Statistics]) -> Image: ...   # refuses a missing stage
    def closed_form(self, stage: str, params: Mapping[str, Any],
                    earlier: Mapping[str, Statistics], measured: Statistics) -> Statistics | None: ...
    # optional context inputs (D61) are keyword-only extras on analyze/render in a future version
```

`methods.ancuti_fusion` registers two `CorrectionMethod` instances sharing the fusion code:
`c3` (stages white_balance, fusion) and `ancuti2018` (compensation, white_balance, fusion), with
`ancuti2018-blue` as `ancuti2018` with `blue_compensation=True` (AD-6, AD-8).

### IF-4 Statistics store

```python
class StatisticsStore(Protocol):
    def put(self, pts_ticks: int, stage: str, raw: Statistics) -> None: ...
    def raw(self, pts_ticks: int, stage: str) -> Statistics: ...          # KeyError if absent
    def smoothed(self, pts_ticks: int, stage: str) -> Statistics: ...
    def smooth(self, stage: str, names: Sequence[str], window_s: float, kind: str) -> None: ...  # AD-3, over pts
    def invalidate_from(self, stage: str) -> None: ...                      # AD-7
    def pts_range(self) -> tuple[int, int]: ...
    def all_pts(self) -> Sequence[int]: ...
    schema_hash: str                                                        # method id + params that shaped the stats (DR-25 erratum)
```

Keys are pts ticks (D95); a CFR series is the special case. No group breaks in v1 (v0.5.3 5.5).

### IF-5 Video source and sink

```python
@dataclass(frozen=True)
class ProbeResult:
    path: Path; container: str; duration_s: Fraction; start_offset_s: Fraction
    video: VideoStreamInfo       # codec, width, height, bit_depth, pix_fmt, chroma siting, color: ColorDescription,
                                 # frame_rate (avg), time_base, nb_frames | None, rotation (display matrix), vfr: bool
    audio: tuple[AudioStreamInfo, ...]; data: tuple[DataStreamInfo, ...]   # gpmd, tmcd
    edit_list: tuple[EditEntry, ...]
    faults: tuple[Fault, ...]    # truncated, unreadable tail, missing tags (assumed per D54), hlg/pq (refusal), gp-log (warn, AD-16), sidecar (excluded, D83)
    gopro: GoProInfo | None      # firmware, protune, colour profile (PTCL) from GPMF settings

class VideoSource(Protocol):
    def probe(self, path: Path) -> ProbeResult: ...
    def frames(self, probe: ProbeResult, *, hw_decode: bool, start_s: Fraction | None = None,
               end_s: Fraction | None = None) -> Iterator[Frame]: ...   # exact pts; stops at the readable end (D86)

@dataclass(frozen=True)
class EncoderCapability:   # D74
    name: str; available: bool; reason: str | None; bit_depths: tuple[int, ...]; hw: bool

class VideoSink(Protocol):
    def capabilities(self) -> tuple[EncoderCapability, ...]: ...
    def open(self, probe: ProbeResult, out_path: Path, *, encoder: str, quality: str,   # AD-12
             bit_depth: int, provenance: Mapping[str, Any] | None) -> None: ...
    def write(self, frame: Frame) -> None: ...        # in pts order; sink preserves pts, start offset, edit list (AD-22), audio, gpmd, tmcd, rotation
    def close(self) -> SinkReport: ...                # frames written, warnings, best-effort items not carried
    def abort(self) -> None: ...                      # removes the partial (D84)
```

### IF-6 Photo source and sink

```python
class PhotoSource(Protocol):
    def read(self, path: Path) -> tuple[Image, PhotoMetadata]: ...   # HEIC/JPEG/PNG/TIFF; orientation applied; ICC kept; DNG/ProRAW refused (D116)

class PhotoSink(Protocol):
    def write(self, image: Image, meta: PhotoMetadata, out_path: Path, *, bit_depth: int,
              provenance: Mapping[str, Any] | None) -> None: ...   # PNG 8/16-bit, ICC embedded, EXIF per D63
```

### IF-7 Proxy cache

```python
@dataclass(frozen=True)
class CacheKey:
    size: int; mtime_ns: int; cache_version: int       # D71, D113

class ProxyCache(Protocol):
    def lookup(self, key: CacheKey) -> CacheEntry | None: ...
    def store_proxy(self, key: CacheKey, pts_ticks: int, proxy: numpy.ndarray) -> None: ...   # uint8 (540 short side) AD-5
    def proxy(self, key: CacheKey, pts_ticks: int) -> numpy.ndarray: ...
    def store_source_statistics(self, key: CacheKey, stage: str, pts_ticks: int, stats: Statistics) -> None: ...
    def limit_bytes(self) -> int; def set_limit_bytes(self, n: int) -> None: ...   # default 20 GB, oldest first
    def clear(self) -> None: ...
```

### IF-8 Jobs

```python
class Progress(Protocol):
    def report(self, done: int, total: int | None, message: str) -> None: ...
    def cancelled(self) -> bool: ...

@dataclass(frozen=True)
class JobResult:
    ok: bool; outputs: tuple[Path, ...]; warnings: tuple[str, ...]; failure: str | None; device: str; elapsed_s: float
```

Analysis, export and batch share these; the GUI runs jobs on a worker thread and marshals
`report` to the main thread.

### IF-9 Parameter set

JSON per AD-13: `format_version`, `method`, `parameters`, `created`, `app_version`; the provenance
sidecar adds `source` (path, size, mtime, probe summary) and `settings` (encoder, quality, bit
depth, device). `ParameterSet` dataclass with `to_json()` / `from_json()` and a method-schema
validation step.

### IF-10 Settings

`Settings` dataclass (G12 + AD-9): `output_folder`, `output_suffix`, `png_bit_depth`,
`video_encoder`, `quality_level`, `ten_bit_for_eight_bit`, `provenance`, `cache_limit_bytes`,
`force_cpu`, `last_parameters: ParameterSet | None`. Stored as JSON in the platform app-data
folder; `clearwater.local.toml` stays the developer-only override for folders.

## 4. Correction core (WP3.1-3.4)

As prototyped in `tools/prototype` and measured through Phase 1: Ancuti 2018 fusion with
selectable compensation (3C default, Ancuti red/blue with caps as options), gray-world white
balance with strength and the D99 clamp (3.0), gamma and sharpened inputs, Laplacian/saliency/
saturation weights, multiscale blend; all spatial parameters as fractions of the short side
(D56); 32-bit float throughout (D39); one code path on `ArrayBackend` (AD-1). Defaults: AD-8.
The product core is a re-implementation against IF-2/IF-3 with the prototype as the numerical
reference (the WP3.x briefs carry bit-identity or tolerance tests against recorded prototype
outputs, DR-19).

Performance: the core runs 0.395 s (Ancuti) / 0.639 s (c3) per 4K frame on the owner's GPU
unoptimised; the N6 target is the owner's at Gate 1 (AD-21). Optimisation candidates and their
order: transport (AD-2), device-resident pipeline, upload/download overlap, FFT or recursive
Gaussian for 3C (gate report Result 1).

## 5. Video pipeline (WP3.5, 3.7, 3.9, 3.10, 3.11, 3.12)

- **Probe** (WP3.7): ffprobe JSON plus a GPMF settings read; faults per IF-5; HLG/PQ refused;
  GP-Log warned (AD-16); sidecars excluded (D83); VFR reported (D95).
- **Decode** (WP3.9): FFmpeg process, software or `-hwaccel cuda`, output planar RGB at source
  bit depth, full or limited range honoured (AD-10, D54/D55); transport per WP2.1S (AD-2);
  exact pts from `-copyts` and a timestamp side channel.
- **Analysis** (WP3.11): proxy 540 (AD-5) to the cache (AD-5, IF-7); staged statistics (AD-6);
  smoothing (AD-3) with a step-aware variant as a design task; provisional preview (AD-15).
- **Encode and mux** (WP3.10): one FFmpeg process; flags of WP1.5 section 4; NVENC or libx265
  at 8 or 10 bits; quality levels AD-12; audio, gpmd, tmcd copied; `-copyts -fps_mode
  passthrough -enc_time_base:v demux +negative_cts_offsets`; display matrix kept; best-effort
  `udta` repair as a second box-level pass if cheap (debt otherwise); DR-15 per AD-22.
- **Proxy cache** (WP3.12): key (size, mtime, version); uint8 proxies in the store chosen by the
  measured test of AD-5; source-only statistics beside them; 20 GB default, oldest first, clear.

## 6. Photos (WP3.6)

pillow-heif / Pillow read with ICC and orientation; 16-bit PNG write with the profile and the
D63 EXIF subset; provenance (D90); ProRAW/DNG refused (D116). Library verification PENDING
WP2.1S (AD-17).

## 7. Jobs, config, GUI (WP3.13-3.20, WP4.x)

Naming and safe writing per 8.3-8.4 (partial file, rename on success, never overwrite without
the setting); export and batch queue with progress and cancel (IF-8; WP3.19 is batch queue and
export progress only, v0.5.3); presets and settings (AD-13, IF-10); PySide6 GUI with the Basic
panel listing c3 first (6.3), CPU/GPU shown in the status bar (AD-9), export disabled during
analysis with the reason (AD-15).

## 8. Testing and tolerances

Fixtures from WP2.3 (AD-14 flicker clip; synthetic stills; 8/10-bit, HLG/PQ-tagged, untagged,
truncated, VFR, rotated samples; sidecar dummies; a DNG for refusal). Tolerances AD-11 (V8,
V9, N10). V16 carries the interim N6 once the owner rules. The suite now exceeds one 10-minute
call; the gate runs it in the background or in selections.

## 9. Licence position

AD-18. Confirmed at WP5.5 with the final wheel set; CUDA runtime files are never redistributed.

## 10. Open items in this document

| Item | Closed by |
|---|---|
| N6 figure for V16 and the optimisation package | Owner, Gate 1 (AD-21) |
| Frame transport (pipe/socket blocks vs PyAV decode) | WP2.1S (AD-2) |
| 16-bit PNG + ICC + EXIF write path | WP2.1S (AD-17) |
| Proxy store container | WP3.12 brief's measured test (AD-5) |
| Step-aware smoothing variant | WP3.11 design task (AD-3) |
| GoPro "HDR video" mode | a clip, if one is ever supplied (AD-16) |
