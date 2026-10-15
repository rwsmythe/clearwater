# WP1.5 -- Container spike (D104)

Result 6 of the prototype gate. Two real GoPro chapters were decoded and encoded again with no
correction through FFmpeg run as a process, and each output was compared with its source on every
item spec 8.2 and 7.5 name. **Recommendation: the simple approach** (section 8). Gate 6 is the
architect's; CHARC rules at WP1.6.

Conditions: 2026-10-15 (UTC), Windows 11 laptop, NVIDIA GeForce RTX 4070 Laptop GPU, driver
610.62 (both as nvidia-smi named them during every proof: `capability.json`,
`gpu.names` and `gpu.driver_versions`); FFmpeg and ffprobe 9.0.2
(`9.0.2-full_build-www.gyan.dev`, the WP0.1 install; the `ffprobe` field of each comparison
record); branch `wp1.5`. Every record cited below was produced on `294c393` (the Reviewer B
remediation): the capability record, both re-encodes with their comparison and run records,
and the camera record. The run log `work\wp1.5\logs\r4-records.log` holds the head, each
step's start and end (UTC) and its exit status. Footage folder read only; every file the
spike's FFmpeg runs and record writers produce is under `C:\Users\rwsmy\clearwater\work\wp1.5\`
(below, `work\wp1.5\`). No timing figure is a result here: elapsed times are informal.

## 1. Instrument

- `tools/container_spike/compare.py SOURCE OUTPUT` (the comparison) reads two sources of fact:
  - `ffprobe` for the streams, every decoded video frame's presentation timestamp (`-show_entries
    frame=pts`, the whole sequence, edit list applied as a player sees it) and every audio and
    data packet with an MD5 of its payload (`-show_data_hash MD5`);
  - its own ISO base media box walker for what ffprobe does not show: each track's raw `elst`,
    `stts`/`ctts` (for the earliest composition time), `tkhd` matrix and flags, `hdlr`, the
    first sample entry and (video) its child boxes, `mvhd` creation time, `ftyp`, and the
    `moov/udta` atoms with an MD5 each. Only `ftyp` and `moov` are read; `mdat` is skipped.
- Every timestamp derived from tick counts (pts, durations, starts, edit lists) is an exact
  `Fraction` of seconds, rendered `"<6 decimals> (<n>/<d>)"`; two renderings are equal
  exactly when the values are. The two values ffprobe prints only as microsecond text, the
  format `start_time` and `duration`, are compared as printed. Sequences are compared in full
  and recorded as count, first, last, SHA-256 of the whole and (pts) the count of each step.
- `tools/container_spike/spike.py` runs `capability`, `camera` and `reencode` (sections 2-4).
  Before every FFmpeg run that writes a file, and before every record file is written, that
  file's own resolved path (symbolic links and junctions followed) is checked to lie inside
  `work\wp1.5\` and outside the footage folder, and an existing file at that path with more
  than one hard link is refused (a hard link resolves to itself, so only its link count shows
  that another name, perhaps in the footage folder, shares it) (`check_output_path`,
  `write_checked`); a re-encode checks all of its record paths before FFmpeg starts. `-y` is
  passed only for such a checked path. The other FFmpeg runs (hardware decode, PSNR) write to
  the null muxer (`-f null -`), so nothing. Every FFmpeg and ffprobe process, the tests'
  included, gets the environment without `FFREPORT` (`tool_env`): that variable makes both
  tools write a log file into their current folder, wherever it is.
- **Not guarded: check-to-use races.** The checks run once, before the write. A concurrent
  process that swaps a checked folder for a junction, or plants a link, between the check and
  the write is outside this spike's threat model (no such process runs here); safe writing
  for the product (8.4, D85: write to a temporary name, rename on success) is where that
  belongs.
- The safety statement covers the files the spike itself produces. Python's `__pycache__`
  folders and pytest's `.pytest_cache` are written by the interpreter and the test runner,
  not by the spike, and are not under `work\wp1.5\`.

**JSON record shape** (`<name>.compare.json`): `source`, `output` (paths), `ffprobe` (version
line), `info.{source,output}` (`codec`, `profile`, `bit_rate`, `size_bytes`, `streams`; not
compared), `items[]` with `name`, `class`, `clause`, `source`, `output`, `status` (`SAME` or
`DIFFERENT`), `note`, and `summary` (`items`, `different` count per class, `different_items`
names per class, `mandatory_all_same` for D105's class alone, and
`mandatory_and_required_all_same`, the recommendation's test). Streams are paired across files by handler type and
occurrence (`vide#0`, `soun#0`, `tmcd#0`, `meta#0` = GPMF), never by index, because FFmpeg
reorders the data tracks.

**Classes.** `MANDATORY` (D94, D95, D105, 7.5): the per-frame pts sequence, frame count, video
stream duration, start offset (first frame pts, each video and audio stream's `start_pts`, the
exact earliest start over the video and audio tracks, and ffprobe's format `start_time` as
printed), the video track's edit list as written, the edit lists of the video and audio tracks
by presentation effect, audio present (an item that tests preservation: it is SAME also when
neither file has audio), its packets passed through (pts, duration, size, MD5 per packet), audio
sync (first audio pts minus first video pts), and display orientation (display matrix side data
and the video `tkhd` matrix). `REQUIRED (D55/D114)` (D55, D114, 8.2): spec 8.2's output format,
as two **output requirements** (the output's video codec is `hevc`; its container, named from
the `ftyp` brands, is MP4: a QuickTime `qt  ` major brand is not, an `isom`/`iso2`-`iso9`/`mp41`/
`mp42` brand is), whose status compares the output with the requirement, the source value
recorded beside it for reference only (an H.264 or QuickTime source may lawfully differ);
then colour primaries, transfer, matrix, range, decoded pixel format, chroma subsampling, bit
depth, frame size and sample aspect ratio, compared source against output. These are spec
"musts" outside D105's list, so the label shows it, and **a REQUIRED item DIFFERENT weighs as
MANDATORY for the recommendation** (`mandatory_and_required_all_same`). `BEST-EFFORT` (D105,
8.2): creation time (container tag, `mvhd`, stream tags), the GPMF and timecode tracks, the
timecode value, the camera atoms, brands, other container and stream tags, chroma location,
track layout and flags, video sample entry boxes, the non-video tracks' edit lists as written,
the data tracks' edit lists by effect, the earliest start over all tracks (data tracks
included, derived from every stream's `start_pts`), and the container duration (as printed).

**Two readings this rests on:**

1. *Edit list* (CHARC's ruling on D94 and 7.5, "copied from the source, not recalculated").
   MANDATORY: the **video track's edit list as written** matches (every entry's duration in
   movie seconds, media time in media seconds, rate), AND the **presentation effect** of the
   video and audio tracks' edit lists matches. The effect form takes an absent edit list as the
   implicit identity (the whole media from 0 at rate 1) and each entry's media time relative to
   the track's earliest composition time, so a real trim of the media's head keeps its length
   (unit test `test_head_trim_is_kept`). BEST-EFFORT: the non-video tracks' edit lists as
   written; the identity edits the MP4 muxer adds to audio and data tracks that had none have no
   presentation effect (the effect item covers audio). On the GoPro chapters the video edit list
   matches as written (section 5). Where a source stores a B-frame reorder delay in the video
   edit list, the as-written item is DIFFERENT after a re-encode even though the presentation is
   identical: a libx264 test clip with B-frames stores `media_time` 1/15 s and its libx265
   re-encode stores 0, with the effect and every pts SAME (unit test
   `test_b_frame_source_video_edit_list_differs_as_written_only`). That case is outside this spike's envelope (section 9) and banked
   as DR-15.
2. *Frame durations.* ffprobe's per-frame `duration` is the packet's decode delta (`stts`), which
   follows decode order and moves with the encoder's B-frame structure: on the variable-frame-rate
   synthetic clip, the source and re-encode attach the 0.2 s gap to different frames while every
   pts is identical. It is not compared. A frame's presentation duration is the step to the next
   pts (compared through the full pts sequence) and the last frame ends at the stream duration
   (compared).

## 2. Capability record (D74)

`spike.py capability` on `294c393` (start and end in `work\wp1.5\logs\r4-records.log`); record
`work\wp1.5\capability.json`.

Listed by the build (`ffmpeg -encoders`, `-decoders`, `-hwaccels`; the record's `listing`):
encoders `hevc_nvenc`, `libx265`, `av1_nvenc`, `libsvtav1`, `libaom-av1` all listed; decoders
`hevc_cuvid`, `h264_cuvid`, `av1_cuvid`, `hevc`, `h264` all listed; hardware acceleration
`cuda`, `d3d11va`, `dxva2`, `d3d12va`, `vulkan` all listed. The listing is not the proof; the
proofs follow.

**Proof criterion.** An encode proof holds only when every gating check in its record's
`checks` is true: FFmpeg exit 0, then the ffprobe reading of the output: codec `hevc`, the
expected profile and pixel format, frame size 3840x2160, 60 frames, and the stream's `encoder`
tag naming the encoder used (`hevc_nvenc` or `libx265`); for an NVENC proof also a GPU named by
nvidia-smi during the encode. The NVENC session count and encoder utilisation are recorded
under `gpu` as **supporting evidence only**, not gating: nvidia-smi's session counter can miss
a short encode, and its utilisation is an average over the last sample period, so it can carry
over from a run just before. What proves NVENC is a `hevc_nvenc` encode that ffprobe confirms,
tagged by `hevc_nvenc`, on the GPU nvidia-smi names while it runs. The decode proof holds only
on exit 0 with every container frame decoded, no error, CUDA frames in the graph
(`-hwaccel_output_format cuda` forbids a silent CPU fallback) and a GPU named during the decode.
nvidia-smi was sampled about every 0.1 s during each run, at least once.

Each proof's full command line and the reading of its output, as recorded:

```
NVENC 8-bit  -- proven (every check true)
ffmpeg -nostdin -hide_banner -y -f lavfi -i testsrc2=size=3840x2160:rate=30:duration=2 -c:v hevc_nvenc -pix_fmt yuv420p -profile:v main C:\Users\rwsmy\clearwater\work\wp1.5\capability\proof-hevc_nvenc-yuv420p.mp4
ffprobe: codec_name hevc, profile Main, 3840x2160, pix_fmt yuv420p, nb_frames 60, encoder Lavc63.1.102 hevc_nvenc
nvidia-smi: NVIDIA GeForce RTX 4070 Laptop GPU, driver 610.62, 3 samples
  supporting: NVENC sessions max 1, encoder utilisation max 71 %

NVENC 10-bit  -- proven (every check true)
ffmpeg -nostdin -hide_banner -y -f lavfi -i testsrc2=size=3840x2160:rate=30:duration=2 -c:v hevc_nvenc -pix_fmt p010le -profile:v main10 C:\Users\rwsmy\clearwater\work\wp1.5\capability\proof-hevc_nvenc-p010le.mp4
ffprobe: codec_name hevc, profile Main 10, 3840x2160, pix_fmt yuv420p10le, nb_frames 60, encoder Lavc63.1.102 hevc_nvenc
nvidia-smi: NVIDIA GeForce RTX 4070 Laptop GPU, driver 610.62, 6 samples
  supporting: NVENC sessions max 1, encoder utilisation max 100 %

libx265 8-bit  -- proven (every check true)
ffmpeg -nostdin -hide_banner -y -f lavfi -i testsrc2=size=3840x2160:rate=30:duration=2 -c:v libx265 -pix_fmt yuv420p -profile:v main C:\Users\rwsmy\clearwater\work\wp1.5\capability\proof-libx265-yuv420p.mp4
ffprobe: codec_name hevc, profile Main, 3840x2160, pix_fmt yuv420p, nb_frames 60, encoder Lavc63.1.102 libx265
nvidia-smi: NVIDIA GeForce RTX 4070 Laptop GPU, driver 610.62, 9 samples
  supporting: NVENC sessions max 0, encoder utilisation max 0 %

libx265 10-bit  -- proven (every check true)
ffmpeg -nostdin -hide_banner -y -f lavfi -i testsrc2=size=3840x2160:rate=30:duration=2 -c:v libx265 -pix_fmt yuv420p10le -profile:v main10 C:\Users\rwsmy\clearwater\work\wp1.5\capability\proof-libx265-yuv420p10le.mp4
ffprobe: codec_name hevc, profile Main 10, 3840x2160, pix_fmt yuv420p10le, nb_frames 60, encoder Lavc63.1.102 libx265
nvidia-smi: NVIDIA GeForce RTX 4070 Laptop GPU, driver 610.62, 14 samples
  supporting: NVENC sessions max 0, encoder utilisation max 0 %

Hardware decode (NVDEC)  -- proven
ffmpeg -nostdin -hide_banner -v verbose -hwaccel cuda -hwaccel_output_format cuda -i C:\Users\rwsmy\clearwater-footage\GX011627.MP4 -map 0:v:0 -f null -
FFmpeg: exit 0; "681 frames decoded; 0 decode errors"; filter graph input pixfmt:cuda
ffprobe (-select_streams v:0 -show_entries stream=nb_frames): nb_frames 681
nvidia-smi: NVIDIA GeForce RTX 4070 Laptop GPU, driver 610.62, 6 samples
  supporting: decoder utilisation max 100 %, NVENC sessions 0
```

The synthetic proofs are 4K (2 seconds, 60 frames) so that nvidia-smi samples several times
while an encode runs; the NVENC encodes above still last only about a second
(`elapsed_seconds` 1.17 and 0.84 in the record).

## 3. Camera record (D54, D73)

`spike.py camera GX011625.MP4 GX011626.MP4 GX011627.MP4 GX011628.MP4` on `294c393` (every frame
of all four chapters decoded by ffprobe; start and end in `work\wp1.5\logs\r4-records.log`);
record `work\wp1.5\camera.json`, which holds every value below for each chapter. The four
chapters are identical in every property below except length, so one column holds them all.

| Property | GX011625, GX011626, GX011627, GX011628 |
|---|---|
| Camera, firmware (GPMF `MINF`, `FMWR`) | HERO13 Black, H24.01.02.10.00 |
| Video codec, sample entry, profile | HEVC, `hvc1`, Main |
| Pixel format, chroma, bit depth | `yuvj420p`, 4:2:0, 8-bit |
| Size | 3840 x 2160, SAR 1:1 |
| Colour as written (primaries / transfer / matrix / range) | `bt709` / `bt709` / `bt709` / `pc` (full range), chroma location `left` |
| HLG or PQ transfer tag | none |
| Frame rate (`r_frame_rate`, `avg_frame_rate`) | 30000/1001, 30000/1001 |
| Constant? (decoded pts steps) | yes: one step, 1001/30000 s, on every frame of every chapter |
| Frames decoded = `nb_frames` | 14938, 7345, 681, 434 |
| Start offset | container `start_time` 0; first frame pts 0; `start_pts` 0 on every stream |
| Edit lists as written | video: one identity entry (full duration at `media_time` 0, rate 1, movie timescale 30000); audio, tmcd, gpmd: none |
| Rotation | no display matrix side data; `tkhd` matrix identity |
| Audio | AAC LC, 48 kHz, stereo, one stream |
| Data streams | `tmcd` (handler `GoPro TCD`, 1 sample), `gpmd` GPMF (handler `GoPro MET`, about one packet per second: 498, 245, 23, 15) |
| Timecode | 16:15:01;12, 16:25:52;23, 16:31:28;19, 16:33:27;24 (drop-frame) |
| Creation time (container tag = `mvhd`) | 2026-10-10 06:15:01, 06:25:52, 06:31:28, 06:33:27 UTC |
| `moov/udta` atoms (type, size) | free, FIRM, LENS, CAME, SETT, MUID, HMMT, BCID, GUMI, GPMF (25600 bytes), free |
| GoPro settings (GPMF keys read) | HDR video `HDRV` = N; Protune `PRTN` = Y; colour `PTCL` = NATURAL; bit rate `BITR` = STANDARD |
| Container tags | brand `mp41`; `firmware` H24.01.02.10.00 |

D54: the camera writes the colour tags, and they are BT.709 **full** range (`pc`), not the
limited range D54 assumes for an untagged stream; the decoder reports `yuvj420p` accordingly.
The spike reads only the six GPMF keys named above; the camera's serial number and the other
identifier atoms are not read into any record: in `camera.json` the `udta` atoms appear by type
and size only, and in the comparison records by type, size and an MD5 of the payload.

## 4. The simple re-encode (D104)

`spike.py reencode GX011628.MP4` and `spike.py reencode GX011627.MP4` on `294c393` (start and
end in `work\wp1.5\logs\r4-records.log`), encoder `hevc_nvenc` (every NVENC proof held, so
libx265 was not needed). The exact command for the primary chapter (from
`work\wp1.5\reencode\GX011627_corrected.run.json`):

```
ffmpeg -nostdin -hide_banner -y -copyts -noautorotate
  -i C:\Users\rwsmy\clearwater-footage\GX011627.MP4
  -map 0:0 -map 0:1 -map 0:3
  -c:v hevc_nvenc -preset p5 -tune hq -rc vbr -cq 20 -b:v 0 -pix_fmt yuv420p -profile:v main
  -color_primaries bt709 -color_trc bt709 -colorspace bt709 -color_range pc -tag:v hvc1
  -fps_mode passthrough -enc_time_base:v demux
  -c:a copy -c:d copy -map_metadata 0 -write_tmcd 1 -movflags +negative_cts_offsets
  C:\Users\rwsmy\clearwater\work\wp1.5\reencode\GX011627_corrected.MP4
```

- One video stream decoded and encoded again; audio (`0:1`) and GPMF (`0:3`) copied. The GoPro
  timecode track (`0:2`, `tmcd`) is NOT mapped: the MP4 muxer cannot copy it (`-map 0 -c:d copy`
  fails: "Could not find tag for codec none in stream #2, codec not currently supported in
  container", `work\wp1.5\explore\try1.log`), so it is written again from the `timecode` tag
  (`-write_tmcd 1`). The comparison shows the regenerated sample is byte-identical to the
  camera's (same MD5).
- Naming: the output takes spec 8.3's base name (`GX011627_corrected.MP4`). The spike does NOT
  implement 8.3's collision suffixes (`_corrected_2`, ...) or 8.4's safe writing (temporary name,
  rename on success): a re-run replaces the spike's own outputs in `work\wp1.5\reencode\` on
  purpose (`-y`, after the output-path check). Both belong to the product's naming and writing
  work (WP3.10).
- Pixel format and colour tags from the source probe (D55, D114): 8-bit 4:2:0 full range
  (`yuvj420p`, `pc`) is fed to NVENC as `yuv420p` with `-color_range pc`; the decoded output
  reads back `yuvj420p`, `pc`, BT.709 throughout. A 10-bit source maps to `p010le` / `main10`;
  anything else is refused as outside the spike's envelope.
- Timing: `-copyts` (no shift to zero), `-fps_mode passthrough` (no frame dropped or duplicated),
  `-enc_time_base:v demux` (the source's time base), `+negative_cts_offsets` (NVENC's B-frame
  reordering stored as negative composition offsets, so the video edit list stays the camera's
  `media_time` 0 and a player that ignores edit lists still starts video and audio together).
- Quality settings are only what the spike used (`-preset p5 -tune hq -rc vbr -cq 20`); the
  quality-level mapping is D75, WP2.1's. (Informal, not recorded: NVENC's default without them
  is about 2 Mb/s.)
- Informal elapsed times (`elapsed_seconds` in each run record): 10.72 s for the 22.7 s primary
  chapter, 5.7 s for the 14.5 s one; the run records' supporting GPU readings show one NVENC
  session and 100 % encoder utilisation on the named RTX 4070 Laptop GPU, driver 610.62.

**Identity sanity check (not a quality result).** FFmpeg's `psnr` filter over every frame (the
`psnr` entry of each run record): GX011628 Y 54.80 dB (min 53.04); GX011627 Y 35.83 dB
(min 32.27), at an output bit rate of 19.6 Mb/s against the camera's 55.5 Mb/s on a busier scene
(`info.*.bit_rate` in the comparison record). A full-to-limited range error or a frame
misalignment would show as a far lower figure. (Informal, not recorded: an earlier check on
GX011627's first 120 frames read 32.72 dB at offset 0 against 18.47 dB with the output shifted
one frame.)

## 5. Comparison (D105)

Primary chapter, `work\wp1.5\reencode\GX011627_corrected.compare.json` (md
`GX011627_corrected.compare.md`); the table below is that markdown file's table, values
shortened, full in the JSON, except that a sequence (the pts, each packet track) is recorded
in both as count, first, last and the SHA-256 of the whole sequence: the whole sequences are
compared in memory, element by element.

| Item | Class | Clause | Source | Output | Result |
|---|---|---|---|---|---|
| video frame count | MANDATORY | D94, D95, D105, 7.5 | 681 | 681 | SAME |
| video per-frame pts (presentation, exact, full sequence) | MANDATORY | D94, D95, D105, 7.5 | n=681; first 0.000000 (0/1); last 22.689333 (17017/750); sha256 55dd31ed282a; steps {'0... | n=681; first 0.000000 (0/1); last 22.689333 (17017/750); sha256 55dd31ed282a; steps {'0... | SAME |
| video stream duration | MANDATORY | D94, D95, D105, 7.5 | 22.722700 (227227/10000) | 22.722700 (227227/10000) | SAME |
| start offset: first video frame pts | MANDATORY | D94, D105, 7.5 | 0.000000 (0/1) | 0.000000 (0/1) | SAME |
| start offset: video and audio stream start_pts | MANDATORY | D94, D105, 7.5 | {"vide#0":"0.000000 (0/1)","soun#0":"0.000000 (0/1)"} | {"vide#0":"0.000000 (0/1)","soun#0":"0.000000 (0/1)"} | SAME |
| start offset: container start over video and audio (earliest start, exact) | MANDATORY | D94, D105, 7.5 | 0.000000 (0/1) | 0.000000 (0/1) | SAME |
| start offset: container start_time (ffprobe format, as printed) | MANDATORY | D94, D105, 7.5 | 0.000000 | 0.000000 | SAME (ffprobe prints it in microseconds; compared as text) |
| edit list, video track, as written (media_time in media seconds) | MANDATORY | D94, 7.5 | {"vide#0":[{"duration":"22.722700 (227227/10000)","media_time":"0.000000 (0/1)","rate":... | {"vide#0":[{"duration":"22.722700 (227227/10000)","media_time":"0.000000 (0/1)","rate":... | SAME |
| edit list, video and audio tracks (presentation effect) | MANDATORY | D94, 7.5 | {"vide#0":[{"duration":"22.722700 (227227/10000)","media_start":"0.000000 (0/1)","rate"... | {"vide#0":[{"duration":"22.722700 (227227/10000)","media_start":"0.000000 (0/1)","rate"... | SAME (media start is relative to the track's earliest composition time) |
| audio streams present | MANDATORY | D105, 7.5 | {"soun#0":{"codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,"channe... | {"soun#0":{"codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,"channe... | SAME (tests preservation: SAME also when neither file has audio) |
| audio packets passed through (pts, duration, size, MD5) [soun#0] | MANDATORY | 7.5 | n=1064; first ['0.000000 (0/1)', '0.021333 (8/375)', 505, 'MD5:9363e1198bcbf5d4238b80e7... | n=1064; first ['0.000000 (0/1)', '0.021333 (8/375)', 505, 'MD5:9363e1198bcbf5d4238b80e7... | SAME |
| audio sync: first audio pts minus first video pts | MANDATORY | D105, 7.5 | {"soun#0":"0.000000 (0/1)"} | {"soun#0":"0.000000 (0/1)"} | SAME |
| display orientation: display matrix (ffprobe side data) | MANDATORY | D105, 8.2 | {"rotation":null,"displaymatrix":null} | {"rotation":null,"displaymatrix":null} | SAME |
| display orientation: video tkhd matrix | MANDATORY | D105, 8.2 | [65536,0,0,0,65536,0,0,0,1073741824] | [65536,0,0,0,65536,0,0,0,1073741824] | SAME |
| output video codec (8.2 requires HEVC) | REQUIRED (D55/D114) | 8.2 | hevc | hevc | SAME (output requirement: the output must be hevc; the source value is for reference) |
| output container (8.2 requires MP4) | REQUIRED (D55/D114) | 8.2 | MP4 (ISO BMFF) | MP4 (ISO BMFF) | SAME (output requirement, from the ftyp brands; the source value is for reference) |
| colour primaries | REQUIRED (D55/D114) | D55, 6.5 | bt709 | bt709 | SAME |
| colour transfer | REQUIRED (D55/D114) | D55, 6.5 | bt709 | bt709 | SAME |
| colour matrix | REQUIRED (D55/D114) | D55, 6.5 | bt709 | bt709 | SAME |
| colour range | REQUIRED (D55/D114) | D55, 6.5 | pc | pc | SAME |
| pixel format (decoded) | REQUIRED (D55/D114) | D114, 6.5 | yuvj420p | yuvj420p | SAME |
| chroma subsampling | REQUIRED (D55/D114) | D114, 8.2 | 4:2:0 | 4:2:0 | SAME |
| bit depth | REQUIRED (D55/D114) | 8.2, D76 | 8 | 8 | SAME |
| frame size and sample aspect ratio | REQUIRED (D55/D114) | 8.2 (identity re-encode) | [3840,2160,"1:1"] | [3840,2160,"1:1"] | SAME |
| creation time: container tag | BEST-EFFORT | D105, 8.2 | 2026-10-10T06:31:28.000000Z | 2026-10-10T06:31:28.000000Z | SAME |
| creation time: mvhd (seconds since 1904) | BEST-EFFORT | D105, 8.2 | 3874458688 | 3874458688 | SAME |
| creation time: per-stream tags | BEST-EFFORT | D105, 8.2 | {"vide#0":"2026-10-10T06:31:28.000000Z","soun#0":"2026-10-10T06:31:28.000000Z","tmcd#0"... | {"vide#0":"2026-10-10T06:31:28.000000Z","soun#0":"2026-10-10T06:31:28.000000Z","meta#0"... | SAME |
| GPMF track gpmd (pts, duration, size, MD5) [meta#0] | BEST-EFFORT | D105, 8.2 | n=23; first ['0.000000 (0/1)', '1.001000 (1001/1000)', 23236, 'MD5:3a1a81a6831acd2b1f3d... | n=23; first ['0.000000 (0/1)', '1.001000 (1001/1000)', 23236, 'MD5:3a1a81a6831acd2b1f3d... | SAME |
| timecode track tmcd (pts, duration, size, MD5) [tmcd#0] | BEST-EFFORT | D105, 8.2 | n=1; first ['0.000000 (0/1)', '22.722700 (227227/10000)', 4, 'MD5:f498ffbcb9dabe59a8b7f... | n=1; first ['0.000000 (0/1)', '22.722700 (227227/10000)', 4, 'MD5:f498ffbcb9dabe59a8b7f... | SAME |
| timecode value (stream tags) | BEST-EFFORT | D105, 8.2 | {"vide#0":"16:31:28;19","soun#0":"16:31:28;19","tmcd#0":"16:31:28;19"} | {"vide#0":"16:31:28;19","tmcd#0":"16:31:28;19"} | DIFFERENT |
| camera atoms: moov/udta children (type, bytes, MD5) | BEST-EFFORT | D105, 8.2 | [["free",22,"db46e81649d6863b16bd99ab139c865b"],["FIRM",15,"d86da0c8ef74421cb702c2e4d31... | [["meta",81,"481c1958678e3e19571f6a7b208235e5"]] | DIFFERENT |
| ftyp brands | BEST-EFFORT | D105, 8.2 | ["mp41",["mp41"]] | ["iso4",["iso4","isom","iso2","mp41"]] | DIFFERENT |
| container tags other than creation_time | BEST-EFFORT | D105, 8.2 | {"major_brand":"mp41","minor_version":"538120216","compatible_brands":"mp41","firmware"... | {"major_brand":"iso4","minor_version":"512","compatible_brands":"iso4isomiso2mp41","enc... | DIFFERENT |
| stream tags other than creation_time and timecode | BEST-EFFORT | D105, 8.2 | {"vide#0":{"language":"eng","handler_name":"GoPro H.265","encoder":"GoPro H.265 encoder... | {"vide#0":{"language":"eng","handler_name":"GoPro H.265","encoder":"Lavc63.1.102 hevc_n... | DIFFERENT |
| chroma location | BEST-EFFORT | D105, 8.2 | left | left | SAME |
| track layout (key:sample entry:tkhd flags) | BEST-EFFORT | D105, 8.2 | ["vide#0:hvc1:flags=0xf","soun#0:mp4a:flags=0xf","tmcd#0:tmcd:flags=0xf","meta#0:gpmd:f... | ["vide#0:hvc1:flags=0x3","soun#0:mp4a:flags=0x3","meta#0:gpmd:flags=0x3","tmcd#0:tmcd:f... | DIFFERENT |
| video sample entry child boxes | BEST-EFFORT | D105, 8.2 | ["hvcC"] | ["hvcC","fiel","colr","pasp","btrt"] | DIFFERENT |
| edit lists as written, non-video tracks (media_time in media seconds) | BEST-EFFORT | D105, 8.2 | {"soun#0":null,"tmcd#0":null,"meta#0":null} | {"soun#0":[{"duration":"22.698667 (8512/375)","media_time":"0.000000 (0/1)","rate":"1"}... | DIFFERENT (differs: meta#0 edit list only in output, soun#0 edit list only in output, tmcd#0 edit ...) |
| edit list, data tracks (presentation effect) | BEST-EFFORT | D105, 8.2 | {"tmcd#0":[{"duration":"22.722700 (227227/10000)","media_start":"0.000000 (0/1)","rate"... | {"meta#0":[{"duration":"22.722000 (11361/500)","media_start":"0.000000 (0/1)","rate":"1... | SAME |
| start offset: container start over all tracks (earliest start, exact) | BEST-EFFORT | D105, 8.2 | 0.000000 (0/1) | 0.000000 (0/1) | SAME (includes data tracks; derived from every stream's start_pts, exact) |
| container duration (ffprobe, 1 us) | BEST-EFFORT | D105, 8.2 | 22.722700 | 22.722700 | SAME (the longest track; follows the data tracks) |

Items: 41. DIFFERENT by class: MANDATORY 0, REQUIRED (D55/D114) 0, BEST-EFFORT 8. Every MANDATORY and REQUIRED item SAME (the recommendation's test): True (MANDATORY alone: True).

Fast check, `work\wp1.5\reencode\GX011628_corrected.compare.json`: the same 41 items with
the same result on every row (33 SAME, 8 DIFFERENT, all BEST-EFFORT).

| Item | Class | Clause | Source | Output | Result |
|---|---|---|---|---|---|
| video frame count | MANDATORY | D94, D95, D105, 7.5 | 434 | 434 | SAME |
| video per-frame pts (presentation, exact, full sequence) | MANDATORY | D94, D95, D105, 7.5 | n=434; first 0.000000 (0/1); last 14.447767 (433433/30000); sha256 07e655de2249; steps ... | n=434; first 0.000000 (0/1); last 14.447767 (433433/30000); sha256 07e655de2249; steps ... | SAME |
| video stream duration | MANDATORY | D94, D95, D105, 7.5 | 14.481133 (217217/15000) | 14.481133 (217217/15000) | SAME |
| start offset: first video frame pts | MANDATORY | D94, D105, 7.5 | 0.000000 (0/1) | 0.000000 (0/1) | SAME |
| start offset: video and audio stream start_pts | MANDATORY | D94, D105, 7.5 | {"vide#0":"0.000000 (0/1)","soun#0":"0.000000 (0/1)"} | {"vide#0":"0.000000 (0/1)","soun#0":"0.000000 (0/1)"} | SAME |
| start offset: container start over video and audio (earliest start, exact) | MANDATORY | D94, D105, 7.5 | 0.000000 (0/1) | 0.000000 (0/1) | SAME |
| start offset: container start_time (ffprobe format, as printed) | MANDATORY | D94, D105, 7.5 | 0.000000 | 0.000000 | SAME (ffprobe prints it in microseconds; compared as text) |
| edit list, video track, as written (media_time in media seconds) | MANDATORY | D94, 7.5 | {"vide#0":[{"duration":"14.481133 (217217/15000)","media_time":"0.000000 (0/1)","rate":... | {"vide#0":[{"duration":"14.481133 (217217/15000)","media_time":"0.000000 (0/1)","rate":... | SAME |
| edit list, video and audio tracks (presentation effect) | MANDATORY | D94, 7.5 | {"vide#0":[{"duration":"14.481133 (217217/15000)","media_start":"0.000000 (0/1)","rate"... | {"vide#0":[{"duration":"14.481133 (217217/15000)","media_start":"0.000000 (0/1)","rate"... | SAME (media start is relative to the track's earliest composition time) |
| audio streams present | MANDATORY | D105, 7.5 | {"soun#0":{"codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,"channe... | {"soun#0":{"codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,"channe... | SAME (tests preservation: SAME also when neither file has audio) |
| audio packets passed through (pts, duration, size, MD5) [soun#0] | MANDATORY | 7.5 | n=678; first ['0.000000 (0/1)', '0.021333 (8/375)', 505, 'MD5:9363e1198bcbf5d4238b80e79... | n=678; first ['0.000000 (0/1)', '0.021333 (8/375)', 505, 'MD5:9363e1198bcbf5d4238b80e79... | SAME |
| audio sync: first audio pts minus first video pts | MANDATORY | D105, 7.5 | {"soun#0":"0.000000 (0/1)"} | {"soun#0":"0.000000 (0/1)"} | SAME |
| display orientation: display matrix (ffprobe side data) | MANDATORY | D105, 8.2 | {"rotation":null,"displaymatrix":null} | {"rotation":null,"displaymatrix":null} | SAME |
| display orientation: video tkhd matrix | MANDATORY | D105, 8.2 | [65536,0,0,0,65536,0,0,0,1073741824] | [65536,0,0,0,65536,0,0,0,1073741824] | SAME |
| output video codec (8.2 requires HEVC) | REQUIRED (D55/D114) | 8.2 | hevc | hevc | SAME (output requirement: the output must be hevc; the source value is for reference) |
| output container (8.2 requires MP4) | REQUIRED (D55/D114) | 8.2 | MP4 (ISO BMFF) | MP4 (ISO BMFF) | SAME (output requirement, from the ftyp brands; the source value is for reference) |
| colour primaries | REQUIRED (D55/D114) | D55, 6.5 | bt709 | bt709 | SAME |
| colour transfer | REQUIRED (D55/D114) | D55, 6.5 | bt709 | bt709 | SAME |
| colour matrix | REQUIRED (D55/D114) | D55, 6.5 | bt709 | bt709 | SAME |
| colour range | REQUIRED (D55/D114) | D55, 6.5 | pc | pc | SAME |
| pixel format (decoded) | REQUIRED (D55/D114) | D114, 6.5 | yuvj420p | yuvj420p | SAME |
| chroma subsampling | REQUIRED (D55/D114) | D114, 8.2 | 4:2:0 | 4:2:0 | SAME |
| bit depth | REQUIRED (D55/D114) | 8.2, D76 | 8 | 8 | SAME |
| frame size and sample aspect ratio | REQUIRED (D55/D114) | 8.2 (identity re-encode) | [3840,2160,"1:1"] | [3840,2160,"1:1"] | SAME |
| creation time: container tag | BEST-EFFORT | D105, 8.2 | 2026-10-10T06:33:27.000000Z | 2026-10-10T06:33:27.000000Z | SAME |
| creation time: mvhd (seconds since 1904) | BEST-EFFORT | D105, 8.2 | 3874458807 | 3874458807 | SAME |
| creation time: per-stream tags | BEST-EFFORT | D105, 8.2 | {"vide#0":"2026-10-10T06:33:27.000000Z","soun#0":"2026-10-10T06:33:27.000000Z","tmcd#0"... | {"vide#0":"2026-10-10T06:33:27.000000Z","soun#0":"2026-10-10T06:33:27.000000Z","meta#0"... | SAME |
| GPMF track gpmd (pts, duration, size, MD5) [meta#0] | BEST-EFFORT | D105, 8.2 | n=15; first ['0.000000 (0/1)', '1.001000 (1001/1000)', 23252, 'MD5:9a49c9295987babfdf1d... | n=15; first ['0.000000 (0/1)', '1.001000 (1001/1000)', 23252, 'MD5:9a49c9295987babfdf1d... | SAME |
| timecode track tmcd (pts, duration, size, MD5) [tmcd#0] | BEST-EFFORT | D105, 8.2 | n=1; first ['0.000000 (0/1)', '14.481133 (217217/15000)', 4, 'MD5:0623a45713ee809fa9d5f... | n=1; first ['0.000000 (0/1)', '14.481133 (217217/15000)', 4, 'MD5:0623a45713ee809fa9d5f... | SAME |
| timecode value (stream tags) | BEST-EFFORT | D105, 8.2 | {"vide#0":"16:33:27;24","soun#0":"16:33:27;24","tmcd#0":"16:33:27;24"} | {"vide#0":"16:33:27;24","tmcd#0":"16:33:27;24"} | DIFFERENT |
| camera atoms: moov/udta children (type, bytes, MD5) | BEST-EFFORT | D105, 8.2 | [["free",22,"db46e81649d6863b16bd99ab139c865b"],["FIRM",15,"d86da0c8ef74421cb702c2e4d31... | [["meta",81,"481c1958678e3e19571f6a7b208235e5"]] | DIFFERENT |
| ftyp brands | BEST-EFFORT | D105, 8.2 | ["mp41",["mp41"]] | ["iso4",["iso4","isom","iso2","mp41"]] | DIFFERENT |
| container tags other than creation_time | BEST-EFFORT | D105, 8.2 | {"major_brand":"mp41","minor_version":"538120216","compatible_brands":"mp41","firmware"... | {"major_brand":"iso4","minor_version":"512","compatible_brands":"iso4isomiso2mp41","enc... | DIFFERENT |
| stream tags other than creation_time and timecode | BEST-EFFORT | D105, 8.2 | {"vide#0":{"language":"eng","handler_name":"GoPro H.265","encoder":"GoPro H.265 encoder... | {"vide#0":{"language":"eng","handler_name":"GoPro H.265","encoder":"Lavc63.1.102 hevc_n... | DIFFERENT |
| chroma location | BEST-EFFORT | D105, 8.2 | left | left | SAME |
| track layout (key:sample entry:tkhd flags) | BEST-EFFORT | D105, 8.2 | ["vide#0:hvc1:flags=0xf","soun#0:mp4a:flags=0xf","tmcd#0:tmcd:flags=0xf","meta#0:gpmd:f... | ["vide#0:hvc1:flags=0x3","soun#0:mp4a:flags=0x3","meta#0:gpmd:flags=0x3","tmcd#0:tmcd:f... | DIFFERENT |
| video sample entry child boxes | BEST-EFFORT | D105, 8.2 | ["hvcC"] | ["hvcC","fiel","colr","pasp","btrt"] | DIFFERENT |
| edit lists as written, non-video tracks (media_time in media seconds) | BEST-EFFORT | D105, 8.2 | {"soun#0":null,"tmcd#0":null,"meta#0":null} | {"soun#0":[{"duration":"14.464000 (1808/125)","media_time":"0.000000 (0/1)","rate":"1"}... | DIFFERENT (differs: meta#0 edit list only in output, soun#0 edit list only in output, tmcd#0 edit ...) |
| edit list, data tracks (presentation effect) | BEST-EFFORT | D105, 8.2 | {"tmcd#0":[{"duration":"14.481133 (217217/15000)","media_start":"0.000000 (0/1)","rate"... | {"meta#0":[{"duration":"14.480000 (362/25)","media_start":"0.000000 (0/1)","rate":"1"}]... | SAME |
| start offset: container start over all tracks (earliest start, exact) | BEST-EFFORT | D105, 8.2 | 0.000000 (0/1) | 0.000000 (0/1) | SAME (includes data tracks; derived from every stream's start_pts, exact) |
| container duration (ffprobe, 1 us) | BEST-EFFORT | D105, 8.2 | 14.481133 | 14.481133 | SAME (the longest track; follows the data tracks) |

Items: 41. DIFFERENT by class: MANDATORY 0, REQUIRED (D55/D114) 0, BEST-EFFORT 8. Every MANDATORY and REQUIRED item SAME (the recommendation's test): True (MANDATORY alone: True).

## 6. Classification of each difference

Every MANDATORY and REQUIRED (D55/D114) item is SAME on both chapters
(`mandatory_and_required_all_same` true in both records). The eight DIFFERENT items, all
BEST-EFFORT (D105), with their cause:

| Item | Source | Output | Cause | Cost to keep |
|---|---|---|---|---|
| timecode value (stream tags) | on video, audio and tmcd | on video and tmcd | the MP4 muxer writes a timecode tag only on the tracks it ties to the regenerated `tmcd` | low (the timecode track itself is SAME) |
| camera atoms | `moov/udta`: FIRM, LENS, CAME, SETT, MUID, HMMT, BCID, GUMI, GPMF (25.6 KB of global settings), 2 x free | `udta/meta` (`ilst` encoder tag) | FFmpeg's MP4 muxer does not carry unknown `udta` atoms | a box-level repair could copy them; not attempted (best-effort; section 8) |
| ftyp brands | `mp41` / `mp41` | `iso4` / `iso4 isom iso2 mp41` | `negative_cts_offsets` requires `iso4` | none needed |
| container tags | `firmware H24.01.02.10.00`, brands | `encoder Lavf63.1.102`, brands | `firmware` is not a key the MP4 muxer writes by default | low (`-movflags use_metadata_tags` would write it as an `mdta` key, not as the camera's atom) |
| stream tags | video `encoder GoPro H.265 encoder`; audio no language; tmcd handler `GoPro TCD` | `Lavc63.1.102 hevc_nvenc`; audio `und`; tmcd handler `GoPro H.265` | the encoder tag names the new encoder; the regenerated tmcd takes the video handler name | none needed |
| track layout and flags | v, a, tmcd, gpmd; `tkhd` flags 0xf | v, a, gpmd, tmcd; flags 0x3 (tmcd 0x2) | the muxer orders data tracks and clears "in preview" | none needed |
| video sample entry boxes | `hvcC` | `hvcC fiel colr pasp btrt` | the muxer adds a `colr` box (matching the stream's tags) and others | none needed |
| edit lists as written, non-video tracks | audio, tmcd, gpmd: none | audio, tmcd, gpmd: one identity edit each | the muxer writes an edit list on every track | none needed: no presentation effect (the MANDATORY effect row is SAME; the video edit list matches as written, MANDATORY row) |

Kept, as SAME: creation time (container tag, `mvhd`, every stream tag), the whole GPMF track (23
packets on GX011627, each with the same pts, duration, size and MD5), the timecode track sample,
chroma location `left`, the container duration. Among the MANDATORY and REQUIRED items added in
the Reviewer B remediation, all SAME on both chapters: the format `start_time` (`0.000000` on
both sides), the output video codec (`hevc`) and the output container (MP4, `iso4` with `mp41`
compatible).

## 7. `.LRV` alignment (D60) and other camera checks

- No proxies in the footage; D60 remains open; Part B of WP1.2 and WP2.1 carry it. (`camera.json`
  lists the sidecars found: none; no `.LRV` or `.THM` file is in the folder.)
- D73: no HLG or PQ transfer tag on any chapter (all `bt709`), and the camera's own settings say
  HDR video was off (`HDRV` = `N`). GoPro's plain "HDR video" mode is therefore not exercised.
- GP-Log: the chapters carry Protune on (`PRTN` = `Y`) with colour profile `PTCL` = `NATURAL`;
  no transfer tag and no setting marks a log profile. Whether a GP-Log clip carries a different
  `PTCL` value (the candidate marker) is unverified: no such clip exists. Not exercised.

## 8. Recommendation: the simple approach

**Simple.** One FFmpeg process (decode, encode, mux) with the flags in section 4 leaves every
MANDATORY item SAME on the primary chapter and on the fast check: the full per-frame pts
sequence (681 and 434 frames, exact), frame count, video stream duration, start offset in four
forms (the format `start_time` among them), **the video track's edit list as written** (GX011627: one entry, 22.722700 s
(227227/10000) at `media_time` 0, rate 1, on both sides; GX011628: 14.481133 s (217217/15000) at
0, rate 1, on both sides), the video and audio edit lists by presentation effect, the audio
packets byte-for-byte with their timestamps, audio sync, and the display matrix and `tkhd`
matrix. Every REQUIRED (D55/D114) item is SAME as well: spec 8.2's output format (HEVC video
in an MP4 container) and every colour and pixel-format item; a REQUIRED difference would weigh
as a MANDATORY one (an H.264 output, for example, fails the summary: unit test
`test_an_h264_output_is_required_different`), and the records' `mandatory_and_required_all_same`
is true for both chapters. No MANDATORY or REQUIRED gap exists, so neither a repair pass nor a transplant
was attempted (brief: attempt them only on a MANDATORY difference). What is lost is best-effort only: the camera's `udta` atoms (including GoPro's
global GPMF settings block) and the `firmware` tag. The GPMF telemetry track, the timecode
track and the creation time are kept. If CHARC wants the `udta` atoms, that is a cheap
box-level second pass over the output (copy the atoms into its `moov/udta`), not a reason to
change approach; it was not attempted here.

The recommendation holds under CHARC's edit-list ruling (section 1, reading 1): the video edit
list matches as written, and the identity edits the muxer adds to the audio and data tracks are
best-effort differences with no presentation effect.

**What the simple approach needed from the tool** (for the PyAV versus FFmpeg-as-a-process
choice at WP2.1): an MP4 muxer that keeps source timestamps (`-copyts`, passthrough frame timing,
the demuxer's time base), stores B-frame reordering as negative composition offsets, regenerates
a timecode track from a tag, copies a `gpmd` data track and audio packets untouched, copies
container metadata, and keeps a display matrix (`-noautorotate`); NVENC and libx265 at 8 and 10
bits; NVDEC decode. **Frame access for the correction is NOT exercised here**: the spike never
hands decoded frames to Python and back. How frames leave and re-enter the pipeline (pipes,
PyAV, or another binding) and whether these muxer options stay reachable from that path is
WP2.1's question.

For WP2.1 and WP3.10, two further points:

- **Full range end to end (D54, D55, 6.5).** These GoPro chapters are tagged BT.709 **full**
  range (`pc`, decoded as `yuvj420p`). D54 governs missing or unexpected tags only; a full-range
  tag is read and matched (D55), as this spike does. So the chroma and range path (decode to
  RGB, correction, back to YUV, encode) must honour full range end to end; the 6.5
  limited-range default is the fallback for an untagged stream only.
- **B-frame sources and the video edit list as written (DR-15, CHARC's lean, not yet ruled).**
  The as-written `media_time` is a function of the *encoder's* reorder delay. Copying it
  verbatim onto an output with a different composition-offset convention would shift the
  presentation, the opposite of what 7.5 wants. The probable WP2.1 ruling: where only the
  composition-offset convention differs, "copied, not recalculated" is read by presentation
  effect (pts, start offset, duration and first displayed frame exact), and WP3.10 proves it on
  an iPhone clip. The spike's B-frame test clip shows the case: video edit list as written
  DIFFERENT (`media_time` 1/15 s against 0), presentation effect and every pts SAME.

## 9. Not exercised (out of envelope or absent)

The footage folder changed during the spike: a `SCUBA` subfolder was being downloaded into it
(informal, not recorded: browser `.crswap` files growing, first seen during the first camera
run). The spike reads only the four top-level chapters named in the brief, so no record above
includes those files; the scuba clips are not exercised.

iPhone video; HDR (HLG/PQ) sources; GP-Log; GoPro "HDR video" mode; 10-bit, H.264, 4:2:2 or
rotated real sources (the synthetic tests cover 8-bit HEVC with a start offset and an edit
list, a variable-frame-rate gap and a 90-degree display rotation, re-encoded through libx265,
and use H.264 sources for the B-frame and wrong-codec cases); `.LRV` proxies; chapter
concatenation; any correction; GX011626 beyond the camera record. Sources with B-frames: their
video edit list carries the encoder's reorder delay, so after the simple re-encode the
MANDATORY "video edit list as written" item is DIFFERENT while the presentation is identical
(synthetic test only; DR-15, section 8).

**Untagged sources (D54 fallback NOT implemented).** For a source with no colour tags the
spike passes no colour options at all (`reencode_command` copies only the tags the source
has), and it gives no warning. So D54's fallback, assume BT.709 limited range and warn, is NOT
implemented here; the encoder's defaults decide the output's tags (on the synthetic clip,
libx265 writes a `tv` range into an output whose source had no range tag). The comparison then
reads an absent tag on both sides as SAME. This is a WP3.10 point: the product reads the tags,
falls back to BT.709 limited with a warning when they are missing or unexpected, and sets the
output tags explicitly.

**Not implemented, by scope:** spec 8.3's collision suffixes and 8.4's safe writing (section 4;
a re-run replaces the spike's own outputs); protection against check-to-use races at an output
path (section 1; banked for the product's safe writing, 8.4, D85).
