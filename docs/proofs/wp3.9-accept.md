# WP3.9 accept record (orchestrator generation 9, 2026-10-21)

**Package:** WP3.9 video decode (`clearwater.io.video.decode`, `clearwater.io.video.pipes`), brief
`docs/briefs/wp3.9-brief.md` (FINAL). Cell `wp39-cell1` (implementer-opus-high), one seat; depths 139,790 (round
0) / 253,896 (R1) / 278,336 (R2) / 288,679 (R3), all at yields.

**Candidate:** branch `wp3.9-mc`, the author branch `wp3.9` (`21972af`, base `de206e2`) rebased onto main `b9f3d09`
with `git -c core.autocrlf=false`; 19 commits; sorted patch-id set md5 `70bbf36b80c5a21c0962bfc5e6e1326e` on both
`de206e2..wp3.9` and `b9f3d09..wp3.9-mc` (identical).

**Footprint (checked at this seat):** `src/clearwater/io/video/{decode,pipes}.py` new, `__init__.py` exports
appended; outside the package only the granted edits: two DR-36 (a) log lines in `probe.py` (`_name(path)`), and
"decode.py", "pipes.py" added to the module set in `tests/test_io_video_probe_rules.py`. `interfaces/`, `color/`,
`pyproject.toml`, `uv.lock` untouched. OS-specific code only in `pipes.py` (`sys.platform == "win32"`,
`_winapi.CreatePipe`; AD-23). No `gpmd`/IMU/GPS stream mapped.

**Round-0 premise corrections (rulings in the report):** Q8 (no CUDA device -> FFmpeg does not fall back; a cached
CUDA check, software decode with one log line); `-ss` under `-copyts` counts from the container start (the seek
subtracts the probe's start offset). CREATE_NO_WINDOW banked to WP4.3 (AD-23 extended by CHARC, `df21ab0`).

## Nets

| Net | Result |
|---|---|
| Reviewer A (cell, STRONG, codex 0.162.1 / gpt-5.6-sol high) | R1 0/1/3, R2 0/1/0, R3 0/0/1 (terminating; cleanup `1068226`); 0 reopened, 0 reverts; evidence `clearwater-review-evidence\wp3.9\r1..r3` |
| Cell's window | full pytest at `d40f46b`: 3669 passed, 1 failed (test-only, a log-record count; fixed `29d2253`), 2 skipped, 1570 s; footage + gpu legs at `29d2253`: 9 passed (6 CUDA sample rows; GX011627 software, forced default pipe and CUDA, 681 frames each, pts k x 1001, per-frame hashes equal an independent FFmpeg run) |
| Candidate full pytest (this seat, `021c8dd` before the record) | 3670 passed, 2 skipped, 1525 s, exit 0 (offscreen) |
| Reviewer B (this seat, `codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s read-only`) | NO_NEW_CRITICAL_MAJOR; banner gpt-5.6-sol / high; 0 `^ERROR`; 22 "succeeded in"; tokens 136,366; VERDICT anchored; withheld paths only as exclusions. 1 minor (concurrent public `close()`, executed) + 1 out-of-envelope advisory -> DR-45; 1 report advisory -> erratum at the gate. md5s in `clearwater-review-evidence\wp3.9\reviewB\md5s.txt` (`review-B.txt` `8d4a38a45e3eacaef2f7ed5a69ca399e`). |

**Debt:** DR-36 (a)(b) CLOSED (the register rows are updated by CHARC at QA); DR-39 (c), DR-20 (3)(5), DR-28 (4)
PARTLY (decode side); DR-45 NEW.

**Consumer notes:** WP3.10's footage legs may now use `FFmpegVideoSource`; WP3.11 and WP3.14 close streams from
other threads -> DR-45 (a).

## Main gates

See the addendum line added after the merge.
