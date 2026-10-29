# WP-T6 cumulative ledger

This package implements AD-30's gate sizing under the FINAL brief at
`docs/briefs/wp-t6-brief.md`, including CHARC ruling `7458b470a82d2dc3`.
The dispatcher runs all footage, GPU and heavy commands. This cell yields at
each required boundary; it does not commit or post to a mailbox.

## Dispatcher depth and tokens

Only dispatcher-supplied figures belong here. A tokens-used footer is not
context depth (HD-1); the dispatcher's last-request input-token reading governs
the evaluation and re-seat lines. Turn 1's figures were supplied at turn 2.

| Turn / gate | Tokens-used footer | Last-request input tokens | Context window | Supplied by / disposition |
|---|---:|---:|---:|---|
| Turn 1, rung 0 / W1 script | 101,355 | 104,555 | 258,400 | Dispatcher at turn 2; turn 1 committed as `c06c808`; dispatch pace Codex 0.54 is not a depth figure |
| Turn 2, W1 corrections | Pending dispatcher | Pending dispatcher | 258,400 | Fill after this turn; keep the round-0 table and rung 2 before about turn 5; evaluate re-seat at the rung-2 commit |

## Rung 0 facts (2026-10-29)

| Check | Observed result | Evidence / limits |
|---|---|---|
| HEAD | `6ecc4e5174dfd15080cc6fd59d63940839a9b430` | `git rev-parse HEAD`; matches the dispatch base |
| Branch | `wp-t6` | `git branch --show-current` |
| Initial worktree state | Clean; no porcelain output | `git status --porcelain` before writing this ledger |
| Baseline code identity | Empty diff stat | `git diff --stat 8bc927a..HEAD -- src tests tools pyproject.toml`; baseline of record stands |
| Environment sync | Already performed by dispatcher | Dispatch says `.venv` is synced; no new dependency or lock change |
| Installed pytest | `8.4.2` | Imported version only; `work/wp-t6/rung0-facts.json` |
| Configuration | Left untouched | Dispatcher supplied the gitignored local configuration; the cell did not open it |
| Baseline all collection at seat | 6,449; EXIT 0 | Dispatcher ran `base-collect.sh`; `work/wp-t6/base-all.txt` and `base-collection-summary.json` |
| Baseline parallel collection at seat | 5,313; EXIT 0 | Current expression; `work/wp-t6/base-parallel.txt` |
| Baseline serial collection at seat | 1,136; EXIT 0 | Current expression; `work/wp-t6/base-serial.txt` |
| Baseline collection identity at seat | PASS | Dispatcher reports no duplicates, disjoint legs, 5,313 + 1,136 = 6,449; `base-collection-summary.json` |

The attempted collection used the current expressions, `PYTEST_ADDOPTS` unset,
`QT_QPA_PLATFORM=offscreen`, `PYTHONPATH=scripts`, and the dispatched pytest shim:

```text
uv run python -m pytest --collect-only -q --basetemp=work/wp-t6/base-collect-all -p sandbox_mkdir_shim -p no:cacheprovider
```

The child started at about 11:07:31Z and was stopped after the 11:12:30Z reading
(296.125 CPU seconds). Captured runner output and its empty ID list are retained
as `work/wp-t6/base-sandbox-all.log` and `base-sandbox-all.txt`. There is no valid
pytest collection summary, no inferred count, and no asserted collection identity.
The hang's cause is unconfirmed. Collection does execute a module-level
`select_backend("auto")` in `tests/test_prototype_backend.py`; this is an observed
import mechanic, not a diagnosis of the hang. No further GPU probe was run.

The dispatcher completed the fallback `work/wp-t6/base-collect.sh` at its seat.
It writes separate logs, retains node-ID lines only in
`base-{all,parallel,serial}.txt`, checks each count against pytest's own summary,
then checks duplicates, disjointness and `parallel + serial = all`. The results
above supersede the incomplete sandbox attempt; the sandbox attempt remains
documented as a substrate limitation, not a test failure.

## W1 script and validation

`work/wp-t6/w1.sh` is gitignored scratch, not a committed file. It is run from
Git Bash at the worktree root, with `PYTEST_ADDOPTS` unset and headless Qt. Each
item has separate outputs under `work/wp-t6/w1/`; `driver.log` ends in `W1 DONE`
or `W1 STOP <why>`. Its `status.json` records the stage and UTC bounds. Each
measurement stage records free memory before work and refuses less than 5 GiB.
The dispatcher supplies the exclusive window conditions.

The script locates GX011627 only through `find_footage_file`, follows the exact
specified stream-copy flags as amended by CHARC R-b below, and checks 4(a)-(e)
before any trim encode. `ALLOWED_TAG_DIFFS` applies R-c by scope: format
`major_brand`, `minor_version`, `compatible_brands`, `encoder`; per-stream
`handler_name`, `language`; audio-only `timecode`. Every tag difference records
scope, KEY and allowed status only. Any disallowed difference stops 4(e).
Other failed trim checks and a levels/size-chain failure also stop the run.

Location values are removed from probe tag dictionaries before comparison.
Probe documents and packet hashes remain in memory; saved packet results carry
counts and equality status. Non-timecode data is compared as copied packet
prefixes, with pts, duration, size and hash, without decoding telemetry. Streams
are paired by kind and codec tag, in index order within a key, with equal counts
asserted and zero-based ordinals recorded. Raw
subprocess diagnostics and helper exception strings are withheld to prevent
metadata escaping into a log. A failed check records its named status and
privacy-filtered diagnostics; no raw probe document is retained.

The round-trip step measures all six plants from the existing test's own AST
dictionary at 30, 6, 10 and 15 frames. The fresh 30-frame run is necessary for
Q4's measured time-saving and half-margin comparisons. It records both signed
margins (mean minus 1.0, share minus 0.01), half-margin comparisons for positive
30-frame margins only, and verdicts for every plant. Nonpositive 30-frame margins
are marked untested, with a null half-margin verdict. Selection remains the next
turn's round-0 table; no
test count is changed this turn. The single row-10 cProfile run retains its
top 15 cumulative rows plus the bench-module rows from that same profile.

The script removes only its newly created `work/wp-t6/w1-scratch/` tree at exit,
after checking its resolved absolute path. It refuses pre-existing scratch and
asserts scratch is outside footage. The script, reports, summary JSON and
profile text stay; the trim, encoded files, binary profile and pytest temp files
inside scratch are removed. A cleanup failure becomes `W1 STOP`.

Scratch-script MD5s (W1 updated at turn 2):

- `work/wp-t6/w1.sh`: `d7b695280f2d5f48444d0cfa7f96cdd3`.
  Turn 1's script was `7e6d01a6a9ce5483a5e44ba254b0c135` (17,356 bytes).
- `work/wp-t6/base-collect.sh`: `7e5b253bec40c5b9e16ecda6c1d931ed`
  (2,641 bytes).

| Validation | Result | Evidence |
|---|---|---|
| Turn-1 embedded Python compile / LF bytes | PASS at turn 1 | `work/wp-t6/w1-static-check.json`; turn-2 validation below supersedes it for the corrected script |
| Synthetic location-value removal | PASS | `work/wp-t6/w1-helper-check.json`; a synthetic sentinel value is absent from the filtered document |
| Synthetic matching packet / stream / tag facts | PASS | Same helper check; 4(a)-(e) all PASS |
| Synthetic changed packet hash | Caught by 4(b) | Same helper check; scratch-only helper validation, not W2's real re-encode control |
| Synthetic extra video packet | Caught by 4(b) and 4(c) | Same helper check; not W2's real N+1 control |
| Collection-summary parser | PASS | `work/wp-t6/w1-static-check.json`; plain, fraction and selected-count summary forms checked |
| Bash syntax invocation | Sandbox blocked, not verified | `work/wp-t6/w1-bash-syntax.log`: Git Bash exits 256 with `CreateFileMapping ... Win32 error 5` before parsing; seat-side `bash -n` requested |
| W1 run 1 at seat | STOP at 4(d), 4(e) | Run 1 and diagnosis below; real footage and GPU commands remain exclusively at the dispatcher's seat |
| Turn-2 extracted program | `python -m py_compile` PASS, EXIT 0 | `work/wp-t6/turn2-py-compile.log`; extracted as `w1-embedded-turn2.py` |
| Turn-2 isolated pairing helper | PASS, EXIT 0 | `work/wp-t6/turn2-self-check.json`: swapped tmcd/gpmd pairs, unequal counts raise, two audio streams pair by sorted index and ordinal |
| Turn-2 checker integration and margin logic | PASS, EXIT 0 | Same self-check: correctly paired gpmd has three packets; audio timecode difference allowed, video timecode and firmware differences stop; negative baseline margin not tested, positive margin below half rejected |

Turn-2 seat-side re-run request (Git Bash): move the old `work/wp-t6/w1/` to
`work/wp-t6/w1-run1/` first, preserving every run-1 artifact. Then run W1 in full:

```bash
bash work/wp-t6/w1.sh > work/wp-t6/w1-seat-driver.log 2>&1
```

W1 requests one exclusive window of about 15 minutes. Return its final DONE/STOP
and item output paths to the cell for turn 3's round-0 table; do not proceed to
a build.

## W1 run 1 -- STOP and diagnosis

The dispatcher ran turn 1's W1 from 2026-10-29 11:18:06.838947Z through
11:18:09.255278Z. It stopped at `stage=02-trim` with 4(d) and 4(e) failing.
`01-packets.json` records N = 90, T = 3.003000 s, 180 packets listed and
keyframe spacing of 30 frames. Checks 4(a), 4(b), 4(c) PASS: the 90 video
packets match in order, including their hashes, and their sorted pts are
contiguous at time base 1/30000. Scratch removal PASS in `06-cleanup.json`.
No levels, round-trip or profile measurements ran after the STOP.

The cell's checker incorrectly paired streams by container index. The source
order is video, audio, tmcd, gpmd; the trim order is video, audio, gpmd, tmcd.
tmcd's position is muxer placement, not a difference. This crossed the data
stream tags and compared source gpmd against trim tmcd, producing the incorrect
one-packet gpmd observation. The dispatcher's `work/wp-t6/w1diag/diag.json`
confirms the trim actually has three equal gpmd packets. It also shows the
format `firmware` key missing under the initial flags and present with
`-movflags use_metadata_tags`; audio `timecode` is absent in both trim variants.
The re-run will report audio timecode key presence again under the ruled flags.

The diagnosis also found `-t T` alone cut exactly 90 video and three gpmd
packets: draft correction (f) did not reproduce. Both `-frames:v N` and `-t T`
remain. No tag values or packet digests are reproduced in this ledger.

Finding classification: **major, confirmed, in-envelope, NEW, script-only**:
index-based stream pairing falsely failed a valid reordered roster and crossed
tag/data comparisons. Fixed through one self-contained `pair_streams` helper,
used for fields, rotation, tags, location-key presence and data packets; equal
per-key counts are asserted, and ordinals are recorded. The stream roster is
now a sorted multiset, retaining duplicates. The synthetic controls above
confirm the fix and reject mismatched counts. No product or test code changed.

CHARC authorized the separate metadata flag and scoped tag exceptions below.
The only added FFmpeg option is `-movflags use_metadata_tags`, before `-f mp4`.
Privacy handling, the 5 GiB guard, failure-text policy and scratch cleanup are
unchanged. W1 must run in full again before any real-measurement verdict.

## CHARC W1 ruling (verbatim)

Ruling ID `5b9dd6b0dfacc46e`, status `12fb9fd7`, supplied by the dispatcher at
turn 2. The following text governs the brief's trim steps 3-4:

**CHARC RULING on the WP-T6 W1 STOP (query 5b9dd6b0dfacc46e): R-a, R-b, R-c, R-d all CONCURRED, with one tightening (R-a) and one Limit sentence (R-c). Re-run W1 in full on turn 2's corrected `w1.sh`.** The diagnosis is sound: 4(b) and 4(c) passing on 90 packets with equal MD5s is the fact that matters (a true stream copy), and both failures are the check pairing streams by index after the muxer placed the regenerated `tmcd` last.

- **(R-a) CONCUR.** 4(d)'s roster is a MULTISET of (`codec_type`, `codec_name`, `codec_tag_string`); per-stream fields, tags and data packets are PAIRED by (`codec_type`, `codec_tag_string`). TIGHTENING: if more than one source stream shares a pairing key, pair them in source index order within that key, and the fixture asserts the trim has the same count under that key; the ordinal is recorded so a future two-audio clip cannot cross-pair silently. The fixture, the rung-2 test and `w1.sh` use ONE pairing helper. `tmcd`'s position is muxer placement, not a difference; the report says so in one sentence.
- **(R-b) CONCUR.** `-movflags use_metadata_tags` joins the FIXED flags (the trim is a SOURCE stand-in, so it keeps as much of the source's container as a copy can; `firmware` is what a real-container test may read). It is the only addition; the no-other-flag rule stands after it. The re-run reports whether the stream-level audio `timecode` survives under it (by key).
- **(R-c) CONCUR.** `ALLOWED_TAG_DIFFS` = muxer-written keys only: format `major_brand`, `minor_version`, `compatible_brands`, `encoder`; per stream `handler_name`, `language`; audio `timecode`. Any other key = STOP. Keys and scopes only, never a value. LIMIT for the report and the accept record: V4's tag items that read `handler_name` or the audio `timecode` are exercised against the real container only by the `fullclip` form; the `[trim]` form exercises them against the trim (the output is compared with what the test read).
- **(R-d) CONCUR.** The draft's correction (f) did not reproduce (`-t T` alone cut exactly 90 video and 3 `gpmd` packets); recorded in the report; `-frames:v N -t T` both stay.

For the record at the accept: N = 90, T = 3.003 s, keyframes every 30 frames (counts only). Codex depth 104,555 of 258,400 after turn 1: the ~250K evaluation point is at about turn 5 at this rate; plan the yields so the round-0 table and rung 2 land before it, and re-seat at the rung-2 commit if the figure says so.

Additional binding turn-2 instruction on Q4: test half-margin retention only
for a margin strictly positive at 30 frames; report both margins regardless.
The script marks other margins untested and applies every positive margin's
half-margin test. The unit check uses the script's actual comparison AST.

## Heavy-run ledger

One row per actual heavy run will include start, end, exact command, selected
counts, EXIT, free memory before and evidence paths. Requested runs are explicitly
pending and are not validation results.

| Window | Start / end UTC | Command | Counts / EXIT | Free memory before | Evidence / disposition |
|---|---|---|---|---|---|
| W1 run 1 | 2026-10-29 11:18:06.838947Z / 11:18:09.255278Z | `bash work/wp-t6/w1.sh > work/wp-t6/w1-seat-driver.log 2>&1` | N=90; 4(a)-(c) PASS, 4(d)-(e) FAIL; STOP; process EXIT not supplied | 10,942,857,216 bytes before item 1; 10,942,246,912 before item 2; guard passed | `work/wp-t6/w1/` to be preserved as `w1-run1/`; checker fixed, re-run requested |
| W1 run 2 (requested, about 15 min) | Pending dispatcher | `bash work/wp-t6/w1.sh > work/wp-t6/w1-seat-driver.log 2>&1` | Pending | Script records bytes per stage; >= 5 GiB required | Fresh `work/wp-t6/w1/`; not yet run |

## Review-round ledger

No Reviewer A or B round has run. Future rows carry severity counts,
in-envelope/out-of-envelope, NEW/REOPENED, reverts, product-code/test-only fixes,
transport/model evidence and dispatcher-read depth. Reviewer A uses the
Codex-lane Claude pass at FAST tier under Q11; the fill governs convergence.

## Verification loop and turn boundary

Turn 1 examined the script against rung 1, its fixed flags and privacy locks.
Synthetic checks confirmed that the in-memory checker rejects changed packet
bytes and an extra packet, and discards location values. The helper checks are
script validation only; W2's real controls remain pending. An initial multi-path
shell `PYTHONPATH` was replaced with explicit portable Python path entries,
avoiding dependence on Git Bash path-list conversion. The final script compile
and helper checks are repeated after that edit. No product or test code changed.

Turn 2 applies the ruling above to W1 and records the dispatcher's baseline
collections. The isolated pairing and integration controls and extracted-program
`py_compile` pass, EXIT 0; the corrected script MD5 is recorded above. This is
script validation, not real footage evidence or W2's planted controls.

Pending at handoff: W1's full re-run and turn 3's round-0 table/ruling. No build
in `tests/` or `pyproject.toml` is authorized before that ruling. The one tracked
change this turn is this ledger; W1, the extracted program and synthetic checks
remain under gitignored `work/`. No change was made to the base-collection script.
