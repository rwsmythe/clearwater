# WP1.5 -- Container spike (D104)

Result 6 of the prototype gate. Two real GoPro chapters were decoded and encoded again with no
correction through FFmpeg run as a process, and each output was compared with its source on every
item spec 8.2 and 7.5 name. **Recommendation: the simple approach** (section 8). Gate 6 is the
architect's; CHARC rules at WP1.6.

Conditions: 2026-10-15 (UTC), Windows 11 laptop, NVIDIA GeForce RTX 4070 Laptop GPU, driver
610.62; FFmpeg and ffprobe 9.0.2 (`9.0.2-full_build-www.gyan.dev`, the WP0.1 install); branch
`wp1.5` (instrument at `b3e7869`, proof-folder fix `020c423`). Footage folder read only; every
file written is under `C:\Users\rwsmy\clearwater\work\wp1.5\` (below, `work\wp1.5\`). No timing
figure is a result here: elapsed times are informal.

## 1. Instrument

- `tools/container_spike/compare.py SOURCE OUTPUT` (the comparison) reads two sources of fact:
  - `ffprobe` for the streams, every decoded video frame's presentation timestamp (`-show_entries
    frame=pts`, the whole sequence, edit list applied as a player sees it) and every audio and
    data packet with an MD5 of its payload (`-show_data_hash MD5`);
  - its own ISO base media box walker for what ffprobe does not show: each track's raw `elst`,
    `stts`/`ctts` (for the earliest composition time), `tkhd` matrix and flags, `hdlr`, the
    first sample entry and (video) its child boxes, `mvhd` creation time, `ftyp`, and the
    `moov/udta` atoms with an MD5 each. Only `ftyp` and `moov` are read; `mdat` is skipped.
- Every timing value is an exact `Fraction` of seconds, rendered `"<6 decimals> (<n>/<d>)"`;
  two renderings are equal exactly when the values are. Sequences are compared in full and
  recorded as count, first, last, SHA-256 of the whole and (pts) the count of each step.
- `tools/container_spike/spike.py` runs `capability`, `camera` and `reencode` (sections 2-4).
  Before every FFmpeg run that writes a file, and before every record write, the resolved path
  (links followed) is checked to lie inside `work\wp1.5\` and outside the footage folder
  (`check_output_path`); `-y` is passed only for such a checked path. The other FFmpeg runs
  (hardware decode, PSNR) write to the null muxer (`-f null -`), so nothing.

**JSON record shape** (`<name>.compare.json`): `source`, `output` (paths), `ffprobe` (version
line), `info.{source,output}` (`codec`, `profile`, `bit_rate`, `size_bytes`, `streams`; not
compared), `items[]` with `name`, `class`, `clause`, `source`, `output`, `status` (`SAME` or
`DIFFERENT`), `note`, and `summary` (`items`, `different` count per class, `different_items`
names per class, `mandatory_all_same`). Streams are paired across files by handler type and
occurrence (`vide#0`, `soun#0`, `tmcd#0`, `meta#0` = GPMF), never by index, because FFmpeg
reorders the data tracks.

**Classes.** `MANDATORY` (D94, D95, D105, 7.5): the per-frame pts sequence, frame count, video
stream duration, start offset (first frame pts, each stream's `start_pts`, the container
`start_time`), the edit lists of the video and audio tracks by presentation effect, audio
present, its packets passed through (pts, duration, size, MD5 per packet), audio sync (first
audio pts minus first video pts), and display orientation (display matrix side data and the
video `tkhd` matrix). `REQUIRED` (D55, D114, 8.2): colour primaries, transfer, matrix, range,
decoded pixel format, chroma subsampling, bit depth, frame size and sample aspect ratio; these
are set by encoder options in every approach, so they cannot separate the three approaches, and
are kept apart from D105's two classes rather than folded into either. `BEST-EFFORT` (D105,
8.2): creation time (container tag, `mvhd`, stream tags), the GPMF and timecode tracks, the
timecode value, the camera atoms, brands, other container and stream tags, chroma location,
track layout and flags, video sample entry boxes, the edit lists as written, the data tracks'
edit lists, and the container duration.

**Two readings this rests on** (open to challenge):

1. *Edit list.* The MANDATORY item compares each video and audio track's edit list by its
   presentation effect: an absent edit list is the implicit identity (the whole media from 0 at
   rate 1), and each entry's media time is taken relative to the track's earliest composition
   time. Reason: an edit list's `media_time` is coupled to the encoded stream's composition
   offsets, so a raw copy is not meaningful across a re-encode. On the synthetic test clip the
   libx264 source stores its B-frame delay as `media_time` 1/15 s with positive offsets and the
   re-encode stores 0 with negative offsets; both present frame 0 at 0.5 s (the empty edit is
   kept), and the per-frame pts agree exactly. A real trim of the media's head keeps its length
   under this reading (unit test `test_head_trim_is_kept`). The raw form is still compared, as
   the BEST-EFFORT item "edit lists as written".
2. *Frame durations.* ffprobe's per-frame `duration` is the packet's decode delta (`stts`), which
   follows decode order and moves with the encoder's B-frame structure: on the variable-frame-rate
   synthetic clip, the source and re-encode attach the 0.2 s gap to different frames while every
   pts is identical. It is not compared. A frame's presentation duration is the step to the next
   pts (compared through the full pts sequence) and the last frame ends at the stream duration
   (compared).

## 2. Capability record (D74)

`spike.py capability`, 2026-10-15 06:18:15-06:18:21Z; record `work\wp1.5\capability.json`.

Listed by the build (`ffmpeg -encoders`, `-decoders`, `-hwaccels`): encoders `hevc_nvenc`,
`libx265`, `av1_nvenc`, `libsvtav1`, `libaom-av1` all listed; decoders `hevc_cuvid`,
`h264_cuvid`, `av1_cuvid`, `hevc`, `h264` all listed; hardware acceleration `cuda`, `d3d11va`,
`dxva2`, `d3d12va`, `vulkan` all listed. The listing is not the proof; the proofs follow.

| Proof | Command (abridged; full in the record) | ffprobe reading of the output | GPU during the run | Proven |
|---|---|---|---|---|
| NVENC 10-bit | `ffmpeg -nostdin -hide_banner -y -f lavfi -i testsrc2=size=1920x1080:rate=30:duration=2 -c:v hevc_nvenc -pix_fmt p010le -profile:v main10 ...\capability\proof-hevc_nvenc-p010le.mp4` | hevc, Main 10, yuv420p10le, 1920x1080, 60 frames, encoder `Lavc63.1.102 hevc_nvenc` | RTX 4070 Laptop GPU, NVENC sessions max 1 | yes |
| NVENC 8-bit | same, `-pix_fmt yuv420p -profile:v main` | hevc, Main, yuv420p, 60 frames, `hevc_nvenc` | RTX 4070 Laptop GPU, NVENC sessions max 1 | yes |
| libx265 10-bit | same, `-c:v libx265 -pix_fmt yuv420p10le -profile:v main10` | hevc, Main 10, yuv420p10le, 60 frames, `libx265` | NVENC sessions 0 | yes |
| libx265 8-bit | same, `-c:v libx265 -pix_fmt yuv420p -profile:v main` | hevc, Main, yuv420p, 60 frames, `libx265` | NVENC sessions 0 | yes |
| Hardware decode | `ffmpeg -nostdin -hide_banner -v verbose -hwaccel cuda -hwaccel_output_format cuda -i GX011627.MP4 -map 0:v:0 -f null -` | exit 0; FFmpeg: 681 frames decoded, 0 decode errors; container `nb_frames` 681; filter graph input `pixfmt:cuda` | decoder utilisation max 100 %, NVENC 0 | yes |

`nvidia-smi` was sampled every 0.2 s during each run (name, encoder and decoder utilisation,
`encoder.stats.sessionCount`); the GPU named in every sample is the RTX 4070 Laptop GPU. A proof
holds only on an ffprobe reading that matches (codec, profile, pixel format, 60 frames) or, for
the decode, exit 0 with every frame decoded, no error and CUDA frames in the graph
(`-hwaccel_output_format cuda` forbids a silent CPU fallback). The first capability run, before
`020c423`, failed all four encode proofs because the proof folder did not exist; the record
caught it (`proven: false`, FFmpeg could not open the output) and the rerun above is the result.

## 3. Camera record (D54, D73)

`spike.py camera`, 2026-10-15 06:21:17-06:33:37Z (every frame of all four chapters decoded by
ffprobe); record `work\wp1.5\camera.json`. The four chapters are identical in every property
below except length, so one column holds them all.

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
| `moov/udta` atoms | free, FIRM, LENS, CAME, SETT, MUID, HMMT, BCID, GUMI, GPMF (25600 bytes), free |
| GoPro settings (GPMF keys read) | HDR video `HDRV` = N; Protune `PRTN` = Y; colour `PTCL` = NATURAL; bit rate `BITR` = STANDARD |
| Container tags | brand `mp41`; `firmware` H24.01.02.10.00 |

D54: the camera writes the colour tags, and they are BT.709 **full** range (`pc`), not the
limited range D54 assumes for an untagged stream; the decoder reports `yuvj420p` accordingly.
The spike reads only the six GPMF keys named above; the camera's serial number and the other
identifier atoms are not read into any record (their `udta` atoms appear by type, size and MD5
only).

## 4. The simple re-encode (D104)

`spike.py reencode GX011628.MP4` (06:18:25-06:18:58Z) and `spike.py reencode GX011627.MP4`
(06:18:58-06:20:13Z), encoder `hevc_nvenc` (every NVENC proof held, so libx265 was not needed).
The exact command for the primary chapter (from `work\wp1.5\reencode\GX011627_corrected.run.json`):

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
  container"), so it is written again from the `timecode` tag (`-write_tmcd 1`). The comparison
  shows the regenerated sample is byte-identical to the camera's (same MD5).
- Pixel format and colour tags from the source probe (D55, D114): 8-bit 4:2:0 full range
  (`yuvj420p`, `pc`) is fed to NVENC as `yuv420p` with `-color_range pc`; the decoded output
  reads back `yuvj420p`, `pc`, BT.709 throughout. A 10-bit source maps to `p010le` / `main10`;
  anything else is refused as outside the spike's envelope.
- Timing: `-copyts` (no shift to zero), `-fps_mode passthrough` (no frame dropped or duplicated),
  `-enc_time_base:v demux` (the source's time base), `+negative_cts_offsets` (NVENC's B-frame
  reordering stored as negative composition offsets, so the video edit list stays the camera's
  `media_time` 0 and a player that ignores edit lists still starts video and audio together).
- Quality settings are only what the spike used (`-preset p5 -tune hq -rc vbr -cq 20`); the
  quality-level mapping is D75, WP2.1's. NVENC's default without them is 2 Mb/s.
- Informal: 8.7 s for the 22.7 s primary chapter, 5.6 s for the 14.5 s one (NVENC sessions 1,
  encoder utilisation 100 %).

**Identity sanity check (not a quality result).** FFmpeg's `psnr` filter over every frame:
GX011628 Y 54.80 dB (min 53.04); GX011627 Y 35.83 dB (min 32.27) at 19.6 Mb/s against the
camera's 55.5 Mb/s on a busier scene. Frame alignment was checked on GX011627 (first 120 frames,
Y): 32.72 dB at offset 0 against 18.47 dB with the output shifted one frame, so the frames line
up; a full-to-limited range error would also show as a far lower figure.

## 5. Comparison (D105)

Primary chapter, `work\wp1.5\reencode\GX011627_corrected.compare.json` (md
`GX011627_corrected.compare.md`); values shortened, the JSON holds every value.

| Item | Class | Clause | Source | Output | Result |
|---|---|---|---|---|---|
| video frame count | MANDATORY | D94, D95, D105, 7.5 | 681 | 681 | SAME |
| video per-frame pts (presentation, exact, full sequence) | MANDATORY | D94, D95, D105, 7.5 | n=681; first 0.000000 (0/1); last 22.689333 (17017/750); sha256 55dd31ed282a; steps {'0... | n=681; first 0.000000 (0/1); last 22.689333 (17017/750); sha256 55dd31ed282a; steps {'0... | SAME |
| video stream duration | MANDATORY | D94, D95, D105, 7.5 | 22.722700 (227227/10000) | 22.722700 (227227/10000) | SAME |
| start offset: first video frame pts | MANDATORY | D94, D105, 7.5 | 0.000000 (0/1) | 0.000000 (0/1) | SAME |
| start offset: video and audio stream start_pts | MANDATORY | D94, D105, 7.5 | {"vide#0":"0.000000 (0/1)","soun#0":"0.000000 (0/1)"} | {"vide#0":"0.000000 (0/1)","soun#0":"0.000000 (0/1)"} | SAME |
| start offset: container start_time (ffprobe, 1 us) | MANDATORY | D94, D105, 7.5 | 0.000000 | 0.000000 | SAME |
| edit list, video and audio tracks (presentation effect) | MANDATORY | D94, 7.5 | {"vide#0":[{"duration":"22.722700 (227227/10000)","media_start":"0.000000 (0/1)","rate"... | {"vide#0":[{"duration":"22.722700 (227227/10000)","media_start":"0.000000 (0/1)","rate"... | SAME (media start is relative to the track's earliest composition time) |
| audio streams present | MANDATORY | D105, 7.5 | {"soun#0":{"codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,"channe... | {"soun#0":{"codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,"channe... | SAME |
| audio packets passed through (pts, duration, size, MD5) [soun#0] | MANDATORY | 7.5 | n=1064; first ['0.000000 (0/1)', '0.021333 (8/375)', 505, 'MD5:9363e1198bcbf5d4238b80e7... | n=1064; first ['0.000000 (0/1)', '0.021333 (8/375)', 505, 'MD5:9363e1198bcbf5d4238b80e7... | SAME |
| audio sync: first audio pts minus first video pts | MANDATORY | D105, 7.5 | {"soun#0":"0.000000 (0/1)"} | {"soun#0":"0.000000 (0/1)"} | SAME |
| display orientation: display matrix (ffprobe side data) | MANDATORY | D105, 8.2 | {"rotation":null,"displaymatrix":null} | {"rotation":null,"displaymatrix":null} | SAME |
| display orientation: video tkhd matrix | MANDATORY | D105, 8.2 | [65536,0,0,0,65536,0,0,0,1073741824] | [65536,0,0,0,65536,0,0,0,1073741824] | SAME |
| colour primaries | REQUIRED | D55, 6.5 | bt709 | bt709 | SAME |
| colour transfer | REQUIRED | D55, 6.5 | bt709 | bt709 | SAME |
| colour matrix | REQUIRED | D55, 6.5 | bt709 | bt709 | SAME |
| colour range | REQUIRED | D55, 6.5 | pc | pc | SAME |
| pixel format (decoded) | REQUIRED | D114, 6.5 | yuvj420p | yuvj420p | SAME |
| chroma subsampling | REQUIRED | D114, 8.2 | 4:2:0 | 4:2:0 | SAME |
| bit depth | REQUIRED | 8.2, D76 | 8 | 8 | SAME |
| frame size and sample aspect ratio | REQUIRED | 8.2 (identity re-encode) | [3840,2160,"1:1"] | [3840,2160,"1:1"] | SAME |
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
| edit lists as written (all tracks; media_time in media seconds) | BEST-EFFORT | D105, 8.2 | {"vide#0":[{"duration":"22.722700 (227227/10000)","media_time":"0.000000 (0/1)","rate":... | {"vide#0":[{"duration":"22.722700 (227227/10000)","media_time":"0.000000 (0/1)","rate":... | DIFFERENT (media_time is tied to the encoded stream's composition offsets) |
| edit list, data tracks (presentation effect) | BEST-EFFORT | D105, 8.2 | {"tmcd#0":[{"duration":"22.722700 (227227/10000)","media_start":"0.000000 (0/1)","rate"... | {"meta#0":[{"duration":"22.722000 (11361/500)","media_start":"0.000000 (0/1)","rate":"1... | SAME |
| container duration (ffprobe, 1 us) | BEST-EFFORT | D105, 8.2 | 22.722700 | 22.722700 | SAME (the longest track; follows the data tracks) |

Items: 36. DIFFERENT by class: MANDATORY 0, REQUIRED 0, BEST-EFFORT 8. Every MANDATORY item SAME: True.

Fast check, `work\wp1.5\reencode\GX011628_corrected.compare.json`: the same 36 items with
the same result on every row (28 SAME, 8 DIFFERENT, all BEST-EFFORT).

| Item | Class | Clause | Source | Output | Result |
|---|---|---|---|---|---|
| video frame count | MANDATORY | D94, D95, D105, 7.5 | 434 | 434 | SAME |
| video per-frame pts (presentation, exact, full sequence) | MANDATORY | D94, D95, D105, 7.5 | n=434; first 0.000000 (0/1); last 14.447767 (433433/30000); sha256 07e655de2249; steps ... | n=434; first 0.000000 (0/1); last 14.447767 (433433/30000); sha256 07e655de2249; steps ... | SAME |
| video stream duration | MANDATORY | D94, D95, D105, 7.5 | 14.481133 (217217/15000) | 14.481133 (217217/15000) | SAME |
| start offset: first video frame pts | MANDATORY | D94, D105, 7.5 | 0.000000 (0/1) | 0.000000 (0/1) | SAME |
| start offset: video and audio stream start_pts | MANDATORY | D94, D105, 7.5 | {"vide#0":"0.000000 (0/1)","soun#0":"0.000000 (0/1)"} | {"vide#0":"0.000000 (0/1)","soun#0":"0.000000 (0/1)"} | SAME |
| start offset: container start_time (ffprobe, 1 us) | MANDATORY | D94, D105, 7.5 | 0.000000 | 0.000000 | SAME |
| edit list, video and audio tracks (presentation effect) | MANDATORY | D94, 7.5 | {"vide#0":[{"duration":"14.481133 (217217/15000)","media_start":"0.000000 (0/1)","rate"... | {"vide#0":[{"duration":"14.481133 (217217/15000)","media_start":"0.000000 (0/1)","rate"... | SAME (media start is relative to the track's earliest composition time) |
| audio streams present | MANDATORY | D105, 7.5 | {"soun#0":{"codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,"channe... | {"soun#0":{"codec_name":"aac","profile":"LC","sample_rate":"48000","channels":2,"channe... | SAME |
| audio packets passed through (pts, duration, size, MD5) [soun#0] | MANDATORY | 7.5 | n=678; first ['0.000000 (0/1)', '0.021333 (8/375)', 505, 'MD5:9363e1198bcbf5d4238b80e79... | n=678; first ['0.000000 (0/1)', '0.021333 (8/375)', 505, 'MD5:9363e1198bcbf5d4238b80e79... | SAME |
| audio sync: first audio pts minus first video pts | MANDATORY | D105, 7.5 | {"soun#0":"0.000000 (0/1)"} | {"soun#0":"0.000000 (0/1)"} | SAME |
| display orientation: display matrix (ffprobe side data) | MANDATORY | D105, 8.2 | {"rotation":null,"displaymatrix":null} | {"rotation":null,"displaymatrix":null} | SAME |
| display orientation: video tkhd matrix | MANDATORY | D105, 8.2 | [65536,0,0,0,65536,0,0,0,1073741824] | [65536,0,0,0,65536,0,0,0,1073741824] | SAME |
| colour primaries | REQUIRED | D55, 6.5 | bt709 | bt709 | SAME |
| colour transfer | REQUIRED | D55, 6.5 | bt709 | bt709 | SAME |
| colour matrix | REQUIRED | D55, 6.5 | bt709 | bt709 | SAME |
| colour range | REQUIRED | D55, 6.5 | pc | pc | SAME |
| pixel format (decoded) | REQUIRED | D114, 6.5 | yuvj420p | yuvj420p | SAME |
| chroma subsampling | REQUIRED | D114, 8.2 | 4:2:0 | 4:2:0 | SAME |
| bit depth | REQUIRED | 8.2, D76 | 8 | 8 | SAME |
| frame size and sample aspect ratio | REQUIRED | 8.2 (identity re-encode) | [3840,2160,"1:1"] | [3840,2160,"1:1"] | SAME |
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
| edit lists as written (all tracks; media_time in media seconds) | BEST-EFFORT | D105, 8.2 | {"vide#0":[{"duration":"14.481133 (217217/15000)","media_time":"0.000000 (0/1)","rate":... | {"vide#0":[{"duration":"14.481133 (217217/15000)","media_time":"0.000000 (0/1)","rate":... | DIFFERENT (media_time is tied to the encoded stream's composition offsets) |
| edit list, data tracks (presentation effect) | BEST-EFFORT | D105, 8.2 | {"tmcd#0":[{"duration":"14.481133 (217217/15000)","media_start":"0.000000 (0/1)","rate"... | {"meta#0":[{"duration":"14.480000 (362/25)","media_start":"0.000000 (0/1)","rate":"1"}]... | SAME |
| container duration (ffprobe, 1 us) | BEST-EFFORT | D105, 8.2 | 14.481133 | 14.481133 | SAME (the longest track; follows the data tracks) |

## 6. Classification of each difference

Every MANDATORY and REQUIRED item is SAME on both chapters. The eight DIFFERENT items, all
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
| edit lists as written | video identity edit; audio, tmcd, gpmd none | video identical (22.7227 s at `media_time` 0); audio, tmcd, gpmd get an identity edit | the muxer writes an edit list on every track | none needed: the presentation effect is SAME (MANDATORY row) |

Kept, as SAME: creation time (container tag, `mvhd`, every stream tag), the whole GPMF track (23
packets on GX011627, each with the same pts, duration, size and MD5), the timecode track sample,
chroma location `left`, the container duration.

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
sequence (681 and 434 frames, exact), frame count, video stream duration, start offset in three
forms, the video and audio edit lists by presentation effect (and the video's as written), the
audio packets byte-for-byte with their timestamps, audio sync, and the display matrix and `tkhd`
matrix; every REQUIRED colour and format item is SAME as well. No MANDATORY gap exists, so
neither a repair pass nor a transplant was attempted (brief: attempt them only on a MANDATORY
difference). What is lost is best-effort only: the camera's `udta` atoms (including GoPro's
global GPMF settings block) and the `firmware` tag. The GPMF telemetry track, the timecode
track and the creation time are kept. If CHARC wants the `udta` atoms, that is a cheap
box-level second pass over the output (copy the atoms into its `moov/udta`), not a reason to
change approach; it was not attempted here.

The recommendation holds under the edit-list reading in section 1. If the edit list must match
as written, the only gap on these chapters is the identity edit lists the muxer adds to the
audio and data tracks (the video's matches exactly); closing it is a repair step (drop those
`edts` boxes), which would make the result encode-then-repair. CHARC's call.

**What the simple approach needed from the tool** (for the PyAV versus FFmpeg-as-a-process
choice at WP2.1): an MP4 muxer that keeps source timestamps (`-copyts`, passthrough frame timing,
the demuxer's time base), stores B-frame reordering as negative composition offsets, regenerates
a timecode track from a tag, copies a `gpmd` data track and audio packets untouched, copies
container metadata, and keeps a display matrix (`-noautorotate`); NVENC and libx265 at 8 and 10
bits; NVDEC decode. **Frame access for the correction is NOT exercised here**: the spike never
hands decoded frames to Python and back. How frames leave and re-enter the pipeline (pipes,
PyAV, or another binding) and whether these muxer options stay reachable from that path is
WP2.1's question.

## 9. Not exercised (out of envelope or absent)

iPhone video; HDR (HLG/PQ) sources; GP-Log; GoPro "HDR video" mode; 10-bit, H.264, 4:2:2 or
rotated real sources (the synthetic tests cover 8-bit H.264 with a start offset and an edit list,
a variable-frame-rate gap and a 90-degree display rotation through libx265); `.LRV` proxies;
chapter concatenation; any correction; GX011626 beyond the camera record. Untagged sources: on
the synthetic clip, libx265 writes a `tv` range into an output whose source had no range tag (a
D54/D55 point for WP3.10: the product assumes BT.709 limited for such a source and should set
the tags explicitly).
