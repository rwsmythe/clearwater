# WP3.6P real-photo verification

Candidate: `790541e7`; report turn 10, 2026-11-01. Spec v0.5.7, no spec,
product or interface change. Reviewer B (executing) and the two-leg gate remain
pending; this report is evidence for acceptance, not an acceptance verdict.

All 73 photos read and exported through the product runner. Every class passed
its measured V5 / D53 / V9 checks at 16 bits; one representative per class also
passed at 8 bits. The orientation run attempted all 62 HEICs: 50 discriminating
passes, 12 inconclusive, zero failed. Seven used the narrowly ruled odd-4:2:0
oracle size equivalence. Z and M remain separate candidate rows throughout.

## Evidence and reproducibility

Committed instrument: `tools/photo_verify.py` (orientation, export, memory),
with `tests/test_photo_verify.py`. The cumulative ruling/review/seat record is
[the WP3.6P ledger](../proofs/wp3.6p-ledger.md). The tool reads configured
inputs only and guards writes below the configured working folder's wp3.6p
root. No beside-source output, footage write, new dependency, scene judgement
or look check. All 73 above-surface classifications remain undecided and
reserved for the owner's visual review.

The names-only seven-class map has supplied md5
`07ef683ee2b5a5275a31cdc2597f2fbd`. Its HEIC classes are checked by format/irot;
JPEG A requires an embedded ICC while Z and M require none. ICC presence
cannot distinguish Z from M or establish camera/editor provenance: their
individual assignment remains the inventory map. No metric pools Z/M with
other photos or combines Z and M into one statistics row.

Seat receipts: `work/wp3.6p/seat-turn8/<id>.json` contains the exact command,
measurement UTC, EXIT, wall time and disk figures. Tool summaries were parsed
from the corresponding .log files, without re-reading footage or raw EXIF.
For UTF-16 LE logs the parser locates the UTF-16 JSON schema marker after
any warning prefix, decodes from that byte boundary, then raw-decodes one JSON
object. For UTF-8 logs it locates the UTF-8 schema marker and does the same.
No replacement character was accepted inside a parsed JSON object. Specifically,
5c-16 and both memory logs used UTF-16 LE JSON; 5b, 5b-r2 and 5c-8 used
UTF-8 JSON; q4 was UTF-8 text. The parser chose from the bytes rather than
assuming all PowerShell redirects used the same encoding. Prefix warnings were not promoted into evidence tables.
Local parsed copies and audit facts are under `work/wp3.6p/r10/`.

5a's aggregate I/O-only counts were supplied and recorded in earlier turns;
seat-5a.meta and seat-5a.stdout were re-read for its EXIT/wall/disk receipt.
Its unchanged writer round trip is a supporting witness, not the runner
V5/V9 criterion. The runner's per-class reads below independently cover all 73.

5c-8 ran on `a8c9778d`, before turn 9's `790541e7`. It **stands**: an AST
comparison confirms verify_export, _export_checks, _source_icc, _d63_output,
_png_metadata, _base, class/selection helpers and _safe_record unchanged.
Turn 9 changed the orientation decoder/size comparison and added orientation
flags/counts to the shared projection. Those new keys are absent/zero on
exports and cannot change an existing export measurement. No 8-bit rerun is
needed. 5b-r2 and later runs used the post-turn-9 candidate.

## Reads, layout and colour

5a covered the 73 selected inputs; its recorded read receipt closes the former
permissive-test refusal caveat. Per-class reads/fidelity below come from 5c-16;
every source is 8-bit, and sanitise drops are zero in each class. GPS/MakerNote
kept booleans can include kept absence and are not presence counts. These are
format/fidelity facts, not scene assessments.

| Class | Selected/read OK | Refused/read failed | Sanitise drops | Kept EXIF equal | GPS kept | MakerNote kept |
|---|---|---|---|---|---|---|
| HEIC-0 | 23/23 | 0 | 0 | 23 | 23 | 23 |
| HEIC-90 | 3/3 | 0 | 0 | 3 | 3 | 3 |
| HEIC-180 | 20/20 | 0 | 0 | 20 | 20 | 20 |
| HEIC-270 | 16/16 | 0 | 0 | 16 | 16 | 16 |
| JPG-A | 2/2 | 0 | 0 | 2 | 2 | 2 |
| JPG-Z | 8/8 | 0 | 0 | 8 | 8 | 8 |
| JPG-M | 1/1 | 0 | 0 | 1 | 1 | 1 |

HEIC layouts below come from the measured records. All 62 primaries are grids,
with no imir. Auxiliary/thumbnail columns count items per photo and their
multiplicity; no auxiliary payload is published. The 20 irot-180 sources
include two with two auxiliary items. All other HEICs have one auxiliary item.

| Class | Photos | Primary | irot | EXIF Orientation | imir | Auxiliary items/photos | Thumbnail items/photos |
|---|---|---|---|---|---|---|---|
| HEIC-0 | 23 | grid | 0 | 1 | absent | 1 item(s): 23 | 0 item(s): 7, 1 item(s): 16 |
| HEIC-90 | 3 | grid | 90 | 8 | absent | 1 item(s): 3 | 1 item(s): 3 |
| HEIC-180 | 20 | grid | 180 | 3 | absent | 1 item(s): 18, 2 item(s): 2 | 1 item(s): 20 |
| HEIC-270 | 16 | grid | 270 | 6 | absent | 1 item(s): 16 | 1 item(s): 16 |

JPG-A (2), JPG-Z (8) and JPG-M (1) have no HEIC box/auxiliary/thumbnail-item
layout; their measured source Orientation is 1. Product PNG exports have
Orientation normal, dimensions updated, rewritten Software and no EXIF
thumbnail by the instrument's D63 checks. HEIC auxiliary images are not carried
into the PNG image output; no auxiliary-content interpretation is claimed.

| Class | Primaries | Transfer | Assumed | ICC present/matching | ICC description |
|---|---|---|---|---|---|
| HEIC-0 | Display P3 | sRGB | 0 | 23/23 | Display P3 |
| HEIC-90 | Display P3 | sRGB | 0 | 3/3 | Display P3 |
| HEIC-180 | Display P3 | sRGB | 0 | 20/20 | Display P3 |
| HEIC-270 | Display P3 | sRGB | 0 | 16/16 | Display P3 |
| JPG-A | Display P3 | sRGB | 0 | 2/2 | Display P3 |
| JPG-Z | BT.709 | sRGB | 8 | 0/8 (absence matches) | absent |
| JPG-M | BT.709 | sRGB | 1 | 0/1 (absence matches) | absent |

For the tagged classes, the ICC profile is present and byte-equal from an
independent source metadata read to the PNG's inflated iCCP: 62 HEICs and two
JPG-A files. No owner HEIC needs the profile-less nclx built-in branch. For
JPG-Z and JPG-M, expected/output ICC absence matches (8 and 1 respectively);
this is not a claim that those untagged outputs embed an ICC. Their assumed
BT.709 primaries plus sRGB curve preserve the source sample interpretation.

## AD-24 orientation

Independent primary implementations: FFmpeg 9.0.2 HEIF demuxer/HEVC decoder,
versus product pillow-heif 1.8.1 / libheif 1.23.6 plus AD-24 selection. FFmpeg's
DEFAULT composed primary is used as delivered, without stream mapping,
-noautorotate or an extra EXIF/irot transform. The independent box-size check
rejects a tile/thumbnail. All eight dihedral poses are compared; a pass requires
pose 1 to win below 6/255 and every comparable other pose above 10/255.

5b-r2 attempted all 62, with zero read, orientation or oracle failures.
EXIT 1 / complete=false is designed while any discrimination-only case is
inconclusive. Counts below are measured pose outcomes. Oracle-rounded is an
independent flag overlapping a pose outcome; it is not an extra pass category.

| Class | Attempted | Discriminating pass | Inconclusive | Oracle-rounded | Crop first/last | Failed | Max upright error /255 |
|---|---|---|---|---|---|---|---|
| HEIC-0 | 23 | 14 | 9 | 7 | 0/7 | 0 | 0.753411 |
| HEIC-90 | 3 | 3 | 0 | 0 | 0/0 | 0 | 0.768243 |
| HEIC-180 | 20 | 20 | 0 | 0 | 0/0 | 0 | 0.763468 |
| HEIC-270 | 16 | 13 | 3 | 0 | 0/0 | 0 | 0.814419 |

An inconclusive is a limit of the scene's texture against the oracle's two-pose
discrimination, never a pass and never a product finding. The cited nearest
other pose is the mirror; all eight pose scores are retained. Inconclusives:
HEIC-0 IMG_6752.HEIC through IMG_6759.HEIC and IMG_6761.HEIC; HEIC-270
IMG_6743.HEIC, IMG_6744.HEIC, IMG_6746.HEIC. HEIC-90 and HEIC-180 have none.
The 90/180/270 classes are not mostly inconclusive; no extra discriminator
was commissioned or added.

The earlier 5b halted after 17 HEIC-0 photos: 7 pass, 9 inconclusive and
IMG_6764.HEIC oracle_failed. Product/ispe 3213x5712 versus FFmpeg 3212x5712
was an oracle-size limit, not a product defect. CHARC 2aaa7e0a permits ONLY a
one-pixel-short oracle dimension when the product dimension is odd, source
chroma is 4:2:0 and the other dimension is equal. The full product size must
still match the independent primary size. Both first/last product-edge crops
are evaluated before each full pose comparison; the smaller pose-1 distance
selects the alignment. Two-pixel/tile/other-size differences remain failures.

The restart's seven rounded cases are IMG_6764.HEIC through IMG_6770.HEIC,
all HEIC-0, all discriminating passes, all recorded edge last. The initial
failed file therefore passes with the ruled oracle equivalence; its product
pixels/dimensions were not changed. Synthetic real grids cover odd width and
rotated odd height, with both planted crop edges and rejection controls.

Thumbnail items are an additional transformed-item witness through libheif,
not a third independent decoder and never the pass criterion:

| Class | Available | Concordant | Discordant | Inconclusive |
|---|---|---|---|---|
| HEIC-0 | 16 | 7 | 0 | 9 |
| HEIC-90 | 3 | 3 | 0 | 0 |
| HEIC-180 | 20 | 20 | 0 | 0 |
| HEIC-270 | 16 | 13 | 0 | 3 |

The owner's layouts exercise identity irot=0/tag=1 (23), and nonzero irot with
an agreeing tag (39: 3+20+16). They do not distinguish the tag-only or irot-only
branches: those have synthetic heic-ad24-* generated-reference witnesses.
FFmpeg itself ignores EXIF-only rotation, so a known upright synthetic scene
is the tag-only oracle; no compensating product transform is hidden in the
real-file oracle. Q4's four named owner-HEIC node executed: 1 passed in 10.74s.

**For CHARC (Q3):** AD-24 is "confirmed on the Apple layouts present" to the
measured extent above: 50 discriminating witnesses, 12 explicitly inconclusive,
7 rounded-oracle witnesses, no measured failure. This does not turn the 12 into
passes or prove unwitnessed real branches. CHARC rules AD-24's status at accept;
D63's provisional wording and spec :567 remain for the owner's spec revision.

## Runner export: V5 / D53 / V9

5c-16 is the actual runner's neutral decode -> process -> PNG path, default
device GPU on all 73, runner EXIT 0 on each. Requested/output depth is 16/16
on every photo; failed_checks and D63 defects are empty. Kept EXIF inventories
match type/count/payload bytes and multiplicity in both directions, excluding
exactly D63 rewrites, discarded IFD1 and relocated pointer values. No sanitise
drop. MakerNote/GPS kept booleans are byte-fidelity witnesses, not private
content or semantic-vendor parsing. The coarser text comparison is secondary.

5c-8 has one inventory representative per class, requested/output 8/8, default
GPU, all runner exits 0 and no failed check. Every source is 8-bit; owner runs
do not witness export below source depth (the P3 PNG16 synthetic tests do).
V9 uses AD-11 max <=2 and mean <=0.2 in 1/255 units against the writer-rule
quantised reference, with raw errors also recorded. All raw max/mean errors
are zero at both export depths. The tiny quantised differences below are
floating-point representation differences, all far inside AD-11.

| Class | 16-bit n | 16-bit V5/D53/V9 passes | Quantised max worst /255 | Quantised mean worst /255 | 8-bit n=1 V5/D53/V9 passes | 8-bit quantised mean /255 | Raw max (both depths) |
|---|---|---|---|---|---|---|---|
| HEIC-0 | 23 | 23/23/23 | 7.56979e-06 | 4.39753e-06 | 1/1/1 | 3.22313e-06 | 0 |
| HEIC-90 | 3 | 3/3/3 | 7.56979e-06 | 4.66518e-06 | 1/1/1 | 4.66518e-06 | 0 |
| HEIC-180 | 20 | 20/20/20 | 7.56979e-06 | 4.43417e-06 | 1/1/1 | 3.04381e-06 | 0 |
| HEIC-270 | 16 | 16/16/16 | 7.56979e-06 | 4.28994e-06 | 1/1/1 | 3.48115e-06 | 0 |
| JPG-A | 2 | 2/2/2 | 7.56979e-06 | 4.51216e-06 | 1/1/1 | 4.51216e-06 | 0 |
| JPG-Z | 8 | 8/8/8 | 7.56979e-06 | 3.4866e-06 | 1/1/1 | 3.48163e-06 | 0 |
| JPG-M | 1 | 1/1/1 | 7.56979e-06 | 2.57006e-06 | 1/1/1 | 2.57006e-06 | 0 |

8-bit quantised max is 7.56979e-06/255 in each representative, equal to the
16-bit worst-max value. Per-class means are worst-photo means, not a pooled
pixel-weighted mean. Z and M have their own denominators and error figures.
Tagged ICC preservation is proved separately from untagged expected absence;
no "ICC present on all 73" conclusion follows from the instrument pass flags.

Disk/retention: all seven successful 16-bit class representatives are retained;
66 other successful 16-bit PNGs were measured/hashed and removed. All seven
8-bit PNGs were measured/hashed and removed. Failed-check PNGs would be kept;
there were none in these export runs. No other evidence was pruned. Every
seat run's recorded free disk remained above the 20,000,000,000-byte floor.
The 16-bit EXCLUSIVE export window was 18:19:13Z-18:27:21Z on 2026-11-01.

## Largest-owner-photo memory leg (Result 2)

IMG_6690.HEIC, HEIC-180, 5712x4284 (24,470,208 pixels, about 24.5 MP), c3
DEFAULT processing, PNG16, fresh runner subprocess per leg. This is not a
neutral export memory surrogate. Both records declare exclusive=true;
exclusive/no-other-heavy-work conditions are seat provenance, not a process
inventory audited by the tool. Measurement UTCs below are run times, never
photo capture times. Wall time includes the wrapper; sampler elapsed is its
own recorded interval.

| Fact | Default device | Forced CPU |
|---|---|---|
| Wrapper start UTC | 2026-11-01T18:28:34.6247676Z | 2026-11-01T18:28:45.9751258Z |
| Device reason | GPU | CPU: forced |
| Estimate bytes | 6,128,796,496 | 6,128,796,496 |
| Device free before bytes | 8,189,378,560 | 8,189,378,560 |
| Device total / limit bytes | 8,585,740,288 | 8,585,740,288 |
| RSS baseline bytes | 86,265,856 | 86,368,256 |
| RSS tree peak bytes | 1,926,164,480 | 3,138,392,064 |
| Individual-process OS peak bytes | 1,839,742,976 | 3,092,070,400 |
| Device used baseline bytes | 145,752,064 | 145,752,064 |
| Device-wide peak bytes | 4,108,320,768 | 145,752,064 |
| RSS samples / active | 157 / 155 | 870 / 868 |
| Device samples / active | 42 / 39 | 224 / 222 |
| Sampler elapsed s | 10.312 | 57.297 |
| Wrapper wall s | 11.3000835 | 58.4422013 |
| Estimate / RSS tree peak | 3.181866 | 1.952846 |
| Estimate / device-wide peak | 1.491801 | not a CPU graphics-work ratio |
| RAM <=16,000,000,000 bytes | true | true |
| Device <=8,188 MiB | true | true |
| Automatic / capacity fallback | false / false | false / false |
| Forced CPU | false | true |
| Sampler errors / failed checks | empty / empty | empty / empty |

Estimate 6,128,796,496 < separately sampled free-before 8,189,378,560 bytes;
pre-run fits=true / exceeds=false in both legs. GPU was selected automatically
on the default leg; no capacity fallback occurred. The required second leg
selected CPU explicitly. It proves a measured CPU path, not automatic D111
fallback under exhausted graphics memory. Device-wide CPU-leg peak stayed
at its baseline; no baseline is subtracted from either reported peak.

RSS is the maximum sampled simultaneous sum over the tool/runner process tree,
including sampler children. The OS peak is the maximum observed INDIVIDUAL
process peak, not a sum or replacement for tree sampling; either can breach
RAM independently. Device peak is device-wide, including existing device use.
The GPU estimate/peak ratio uses that full device peak; RSS ratios have a
different resource/scope and are labelled separately. All measured figures
remain subject to sampling and the approved startup race limitation below.

Observed successful-sample start-gap cadence (seconds):

| Leg | RSS min/mean/max | Device min/mean/max |
|---|---|---|
| 5d-default | 0.046000 / 0.065705 / 0.079000 | 0.062000 / 0.250366 / 0.344000 |
| 5d-cpu | 0.031000 / 0.065880 / 0.079000 | 0.078000 / 0.256655 / 0.297000 |

Nominal waits after a sample are 0.05s RSS and 0.2s device; they are not
start-to-start guarantees. Python 3.12.13 here reports monotonic resolution
0.015625s, so gaps and elapsed time are coarse. Baseline/final observations
are included in totals; positive active-run sample counts are reported apart.

**For CHARC (Q6):** the Result 2 largest-photo row now has default-GPU and
forced-CPU measured evidence below 16 GB RAM and 8,188 MiB graphics limits,
with estimate/free/reason/peaks recorded. It is ready for CHARC's acceptance
ruling subject to B/gate and these Limits. The owner maximum is about 24.5 MP;
no 48 MP result or universal photo-size ceiling is claimed. V15 / WP5.2 and
automatic capacity-fallback acceptance remain separate obligations.

## Limits and debt disposition for CHARC

- V5 here reports the runner's measured metadata/depth/fidelity checks plus
  the separately scoped orientation evidence. Multiple-viewer verification
  remains WP5.1; this report does not close that part of V5 or the look check.
- The FFmpeg/libheif primary implementations are independent of AD-24 selection,
  but RGB matrix/range differences could cross the fixed pose bound. No bound
  was relaxed. Thumbnail decoding shares libheif with the product and is
  non-gating. Inconclusive texture and the narrow odd-420 equivalence are
  reported explicitly; no visual photo-look judgement is part of this work.
- The independent EXIF inventory fails closed on unsupported types (including
  UTF-8/type 129 and non-pointer type 13); those vendor/type classes are not
  proved preserved. Opaque MakerNote byte fidelity does not establish all
  vendor-relative offset semantics after relocation. No such owner defect was
  proved or repaired here.
- thumbnail_absent uses the product's Pillow-based has_thumbnail witness; it
  does not independently prove a zero raw next-IFD pointer or exclude a
  malformed retained IFD1. Software's R2-QA output reporting exception permits
  any ASCII suffix after Clearwater, including tabs; today's product writes
  Clearwater. It is not a general private-text sanitizer and source Software
  is never promoted into that field. These are tool limits, not product gaps.
- Memory is sampled, not a continuous instantaneous maximum. The approved
  unlocked attach/background peak-update race can lose a larger observation
  at startup; no such lost owner observation is established. Any unavailable
  RSS/device sample invalidates a leg even if later samples recover. The two
  seat legs have no recorded sample error, but that does not remove the race
  or sampling gaps.
- Free-before uses nvidia-smi in whole MiB before runner CUDA-context creation;
  the actual backend uses its later CuPy free-memory query. They can disagree.
  Actual device reason comes from the runner. A wrapper --config is not
  forwarded to the memory subprocess's own footage-refusal config; these
  seat runs use the default config, with outputs still guarded by the wrapper.
- JPEG ICC presence separates A from the compatible no-ICC Z/M set only.
  Individual Z/M names and all above-surface/correction-history judgements
  remain with the inventory and owner; candidate does not mean confirmed
  pre-corrected. No pooled Z/M success/error/colour figure is used.

**For CHARC (Q8 / DR-42):** no owner photo is PNG/TIFF and every HEIC has an
ICC, so DR-42(a)'s relevant wide-gamut missing-ICC real-file witness is absent.
DR-42(c) is not triggered by an edit: tiff.py was not touched. Synthetic P3
PNG16/nclx controls are not owner PNG/TIFF evidence. Retarget/annotate the debt
rows at accept; no register edit is owned here.

**For CHARC (Q8 / DR-43):** sanitise drops are zero in every class (JPG-Z 0/8,
JPG-M 0/1 included separately); kept-entry checks pass. IF-6 and io.photo are
unchanged. Record the real-file observation; closure or retargeting remains
CHARC's, not an inferred result of this tool-only package.

**For CHARC (Q8 / new MINOR):** EXIF ColorSpace 1 is read as untagged for
JPG-Z (8) and JPG-M (1), assumed=true, while interpreted as BT.709/sRGB anyway.
This is the ruled spurious G10-warning observation (9 affected files, with
class rows separate), not a colour-change finding. ColorSpace tag values
were identified by the inventory; the seat records independently count the
assumed classifications. No colour.py grant or product fix was made. CHARC
owns the new MINOR debt row at accept.

## Verification and remaining gate

Reviewer A rounds 1 and 2 were remediated; round 3 returned
NO_NEW_CRITICAL_MAJOR, nine reasoned advisories after execution refusals.
CHARC 650bea20 accepts convergence conditionally on Reviewer B executing the
final pytest selection, planted-reader ICC control and ICC-presence class
checks. A refused-execution B is not returned: prove its execution path before
reading findings, repair/rerun if needed. B and the ONE two-leg gate follow
at dispatcher seat; no fullclip or harness gate is commissioned.

Turn-10 light checks: 117 passed / 1 footage deselected in 19.10s with the
sandbox shim; ruff clean, format 2 files already formatted, mypy clean across
147 files. Privacy grep over report/ledger/tool/safe summaries found zero
prohibited matches for source-value assignment keys, drive/UNC/Unix absolute
source paths, planted private markers or capture-time values. Existing
review-evidence references are excepted; source metadata values are not.
Records also equal fresh allow-list projection. Details/patterns in the ledger.
No source, tool or test code changes in this report turn. All committed report
and ledger bytes are ASCII/LF, with no private EXIF values or footage paths.
