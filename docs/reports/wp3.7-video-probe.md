# WP3.7 -- Video probe and input validation

Module `clearwater.io.video` (`probe.py`, `boxes.py`, `gopro.py`, `inputs.py`). Tests
`tests/test_io_video_probe.py`, `tests/test_io_video_probe_boxes.py`,
`tests/test_io_video_probe_rules.py`. Ledger `docs/proofs/wp3.7-ledger.md` holds the mapping
tables, the rulings and the round record.

## Claims

1. `probe(path) -> ProbeResult` fills IF-5 exactly as frozen. Every time is a `Fraction` from
   integer ticks and a stream time base (`duration_s` = the CONTAINER duration, the longest of the video and audio stream durations as `duration_ts x time_base`, ruled 2b: the video track's own duration is <= `duration_s` and equal on the video-only samples;
   `start_offset_s` and `AudioStreamInfo.start_s` from `start_pts`); `frame_rate` and `time_base`
   are `Fraction`s of ffprobe's rational strings. No decimal string is parsed into a time.
   Evidence: `test_every_video_sample_probes_to_its_manifest_facts` (8 samples against the
   manifest), `test_every_time_is_an_exact_fraction`.
2. Colour follows D54 per field (ledger table (a)): a missing or unexpected primaries, transfer or
   matrix takes BT.709, a missing range takes limited, `assumed=True`, one `missing_tags` warning
   naming the fields. An untagged `yuvj` stream is full range with no range warning (ruling 7.3).
   HLG and PQ are refused (`refuse`) and carry `transfer="unknown"`, `assumed=False`.
3. Rotation is read from the display matrix, counter-clockwise positive, 0/90/180/270. An angle
   that is not a multiple of 90 or a mirrored matrix raises `VideoProbeError("unsupported")`.
4. VFR: successive differences of the sorted video pts (ticks); more than one distinct step is
   VFR. B-frame reordering does not matter. The last frame's own duration is not a step.
5. `truncated`: ffprobe's packet walk reports `partial file`, or fewer readable packets than
   `nb_frames`, or the last packet carries the corrupt flag. Without `nb_frames` only the first
   and last signals apply. `unreadable_tail`: the file is not truncated and a decode of the last
   group of pictures only (`-read_intervals <last keyframe>%+86400`) writes an error, exits
   nonzero, or does not deliver a frame (by pts) for every packet from the last keyframe on, B-frame order included. An HLG/PQ file is refused and never decoded, so it gets no tail decode. The two are exclusive. Every intact
   sample and all 35 real clips give neither; the cut sample gives `truncated` only; a copy with
   the last packet's payload overwritten gives `unreadable_tail` only.
6. Edit list from `moov` (`boxes.py`; `elst` versions 0 and 1; the first `vide` track): segment
   duration over the movie time scale, media time over the media time scale, `-1` is None, rate
   16.16 fixed. Reported as written (AD-22's reading is WP3.10's).
7. GoPro settings from `moov/udta/GPMF` only: `FMWR`, `PRTN`, `PTCL` (`gopro.py`). Every other
   item is skipped by its length; type-0 containers are entered only to reach the keys. A malformed
   atom gives `gopro=None` and one structural log warning (no bytes); GP-Log by `PTCL` is then
   unavailable for that file (AD-16, best effort). `gp_log` (warn): `PTCL` outside
   `NATURAL`/`FLAT`/`VIBRANT`, or Protune on with no transfer tag (which also raises
   `missing_tags`).
8. Sidecars (D83): `filter_inputs` splits paths by extension (`.lrv`, `.thm`, any case) without
   opening them and returns the `sidecar` `Fault` per excluded path; `probe` on a sidecar raises
   kind `"sidecar"` without running ffprobe.
9. The owner's IMU/GPS ruling is honoured structurally: no `gpmd` data, packet or frame of a data
   stream is requested (the packet and tail calls select `v:0`; the stream call names fields and
   asks for no tags), the box reader reads exactly the 8 (or 16, for a 64-bit size) header bytes of `mdat` and none of its payload (byte-count test), and a static test forbids the sensor,
   location and telemetry tokens and `tools` imports under `src/clearwater/io/video` and `src/`.
10. Messages are ASCII: a non-ASCII file name or profile is escaped with backslash escapes (`ascii_text`). A non-`mdat` top-level box that overruns the file is a `BoxError`.
11. The locator `find_tool(name)` (PATH lookup, kind `"missing_tool"`) is public for WP3.9 and
    WP3.10.

Duration (ruling 2b, upheld by CHARC; IF-5 wording on main at `4174484`, not yet on this branch):
"duration_s: The CONTAINER duration in seconds, exact (`mvhd` duration over its timescale, or the
longest stream in integer ticks times its time base); the video track's own end comes from pts and
frame durations, not from this field." The probe takes the second form.

## Evidence

- `uv run pytest tests/test_io_video_probe*.py`: 131 passed (the footage test included).
- Real clips (read only, through `tools/local_config`): GX011627 matches WP1.5 section 3; all 35
  clips in the footage folder probe with no fault and no error in 54.8 s; GX011625 (14,938 frames,
  4K) probes in 1.5 s (`work/probe/allfootage.out`).
- Gates: `ruff check`, `ruff format --check`, `mypy` strict.

## Limits

- ffprobe 9.0.2 (gyan build) only. Fragmented MP4, multiple video streams, network shares and
  hostile files are outside the envelope (a malformed box still ends in `BoxError` with a bounded
  walk, covered for every truncation of a synthetic file).
- `unreadable_tail` is a one-GOP check: damage earlier in the file is not seen by the probe.
  A stream whose packets carry no keyframe flag is not tail-checked.
- An open-ended `-read_intervals` drops frames at random on this ffprobe (19 of 400 runs of `-read_intervals 0.000000%` on `hevc10` delivered a partial frame list with exit 0 and empty stderr; 0 of 500 runs on three samples and 0 of 400 probes of four samples after `%+86400`);
  the explicit end offset is load-bearing and pinned by a test.
- `clearwater.io.video.probe` (function) shadows the submodule attribute of that name.
- GoPro "HDR video" mode is not read (AD-16 PENDING a clip).

## Consumer notes

- WP3.10 (D94 edit-list reading): `duration_s` is the longest stream in integer ticks times its
  time base. On a source with a non-identity edit list that figure and the `mvhd` duration over
  its timescale may differ; if they do, the presentation form (`mvhd`) is the one a player shows.
  On all four video samples the two are exactly equal (360360/240000, 320320/240000).
- WP3.9: never use an open-ended `-read_intervals` interval for frame counts (ledger build notes).
- `read_movie_boxes` ends its walk at `moov`: a later box that overruns the file is not an error.
- `clearwater.io.video.find_tool(name)` is the shared locator for `ffmpeg` and `ffprobe`.
