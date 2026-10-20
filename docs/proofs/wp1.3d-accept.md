# WP1.3D — Accept record (look check pack, deep part)

**Accepted 2026-10-20 by the orchestrator** (generation 2, session
`clearwater-orchestrator-20261018-1442`). Gate per `docs/review-gate-clearwater.md` Part 2. Tier
STRONG. Released on CHARC's go-ahead `cb61a4e41f625d73`; the two-package split (WP1.3D, then
WP1.4b) accepted by CHARC `1cc08da6b265e2a6`.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp1.3d-brief.md` (FINAL `c80725b`). Spec v0.5.3. |
| Base SHA | `c80725b` |
| Author heads | Return `f958347`; after the Reviewer B #1 remediation `5f5b90c`. Each read twice across a turn boundary, unchanged and clean. |
| Cells and depth | Three seats, implementer-sonnet-high. `wp13d-cell`: 18,857 at dispatch (22:03Z); 244,164 / 77 turns at its interim yield (00:08Z), re-seated. `wp13d-cell2`: 38,943 at dispatch (00:08Z); 239,534 / 127 turns at its round-2 yield (02:06Z), re-seated. `wp13d-cell3`: 19,551 at dispatch (02:07Z); 130,435 / 88 turns at return (04:37Z); 153,856 / 111 turns after the remediation (05:20Z). The two re-seats were stricter than needed: see Process deviations. |
| Merged head | `7f9fea1` (`wp1.3d-mc` = `5f5b90c` rebased onto main `9379c56`; main fast-forwarded). |
| Byte identity | `git patch-id --stable` = `039db28522a135efab24c230ff34151d2facd80f` on `c80725b..5f5b90c`, on the B #2 candidate `9379c56..7f9fea1`, and on main `9379c56..7f9fea1`. CHARC held main from B #1 to the merge, so the merged tree IS the reviewed tree. The B #1 candidate `b3813b8` (patch-id `35a69ffc`) is kept as branch `wp1.3d-b1`. |
| Reviewer A | STRONG (gpt-5.6-sol / high), WSL, codex-cli 0.162.1, five rounds across the three seats: R1 0/2/3, R2 0/3/2, R3 0/3/4 (2 major and 3 minor in envelope fixed; 2 major out), R4 0/1/2 (the scan grid missed GX011598's 525 s point; fixed and rescanned, 290 frames, the earlier 289 unchanged), R5 0 in envelope (1 major out). Converged at R5 under the envelope ruling; five-round approval GRANTED by the orchestrator. Evidence `clearwater-review-evidence\wp1.3d\r1`..`r5`. |
| Reviewer B | Seat pass #1 on `b3813b8`: BLOCKING, 1 major in envelope, 1 minor in, 1 major out; one remediation. Seat pass #2 (final) on `7f9fea1`: `NO_NEW_CRITICAL_MAJOR`, all three closed end to end, 1 minor out of envelope (banked, DR-29). |
| Owned files | The brief's five exactly (`git diff --stat`): `tools/lookcheck/scan.py` (new), `tools/lookcheck/pack.py`, `tests/test_lookcheck_deep.py` (new), `docs/reports/wp1.3d-deep-look-check.md` (new), the ledger. No change under `tools/prototype/`, to `tools/lookcheck/frames.py`, to `tests/test_lookcheck.py`, `pyproject.toml` or `src/`. |

## Orchestrator rulings during the package

1. **Deep read-back bound.** The clip read-back's own-PNG bound is 5.0 levels for the deep clip; the
   shallow flicker clip keeps 3.0 (a test pins it). The read-back checks frame identity and order,
   not fidelity. Measured on the final clip: c3 own min / mean / max 1.00 / 1.92 / 3.85, smallest
   neighbour margin 2.15; source 0.60 / 1.42 / 3.03, margin 1.63.
2. **Candidate spacing** is measured on the scan grid within one chapter (chapters are separate
   recordings).
3. **Render path.** The clip renders call `pipeline.correct(..., statistics=)` directly, keeping the
   `Result` for the bound record; a test pins bit identity with `temporal.render`.
4. **Envelope (sent with the second re-seat).** One operator running the documented steps in order
   on an untampered working folder. Hand-edited or replaced records and out-of-order steps are OUT
   of envelope (banked, never loop-driving). Blocking: anything that would show the owner the wrong
   thing at CP2, and any write outside `work/wp1.3d/`.

CHARC accepted rulings 1-3 (`462c52005bb99626`, recording the measured 3.85 and the margin beside the
5.0 bound).

## Reviewer B #1 (seat), on candidate `b3813b8`

Transcript `clearwater-review-evidence\wp1.3d\reviewB\review-B.txt`, md5
`8db4a20c30642c67c76264c065ebfd23` (prompt `d9169111`, diff `b055adf8`, stderr `9b211708`).
Assertions: banner gpt-5.6-sol / high / read-only; `^ERROR` 0; the one `ERROR codex_core` hit is an
echo of the brief's text; `tokens used` footer; 31 `succeeded in`; VERDICT anchored. Withheld
access: no command opened `docs/proofs/`, the evidence folder or the footage folder (hits are prompt
and brief echoes and a `git status` name listing).

| # | Finding | Disposition |
|---|---|---|
| 1 | MAJOR in envelope: the report's statistics table labelled the twelve candidates "Deep-water noise #1" ... "Distance haze #4", and the deepest table's case column "Deep-water noise", without "candidate" (from the cell's report generator; the page was clean) | Introduced; REMEDIATED: every label reads "candidate: ...", headings "Candidates for ...", the page's section headings likewise; the report and the page swept. |
| 2 | MINOR in envelope: "9.2 GB" for a 9,847,522,080-byte folder | Fixed: "9,847,522,080 bytes, 9.85 GB". |
| 3 | MAJOR out of envelope: cache validation required D > 0 though the scan can record D = 0 | Fixed anyway (one line): D >= 0, with a test. |

## Reviewer B #2 (seat, final), on candidate `7f9fea1`

Transcript `clearwater-review-evidence\wp1.3d\reviewB2\review-B.txt`, md5
`2213251faeb9e1d1b00a3c32b65b3cd3` (prompt `8466d5d0`, diff `49f12836`, stderr `985316a6`, probe
`403e9637`). Assertions as B #1: all hold; the one `ERROR codex_core` hit is an echo of the brief's
text; 36 `succeeded in`; withheld access clean. **VERDICT: NO_NEW_CRITICAL_MAJOR.**

B #2 closed all three items END TO END and re-derived, by executed probes: the three rankings and the
deepest list from `scan.json`; 240 PNG headers (3840x2160, 16-bit RGB); 668 page links (none missing,
none external); the clip's centring, frame alignment and per-row smoothed statistics; all 107
record-derived report rows. **On `DEEP_CAP_TOLERANCE` (1e-9):** the nearest counted binding is
0.9999926 (about 7.4e-6 below 1) and the largest unbound value 0.9999999999999999, so the tolerance
hides no real cap binding; 104 of 179 stands.

One finding: MINOR, out of envelope: `--part` is defined globally, so a mistyped
`pack.py stills --part encode` runs the whole shallow command instead of failing as on main. Banked,
DR-29.

## Verification QA (orchestrator seat)

- Records against the report: 290 scan frames, 0 excluded; 240 PNGs (60 sources, 180 corrected);
  180 side-by-side JPEGs; clip checks c3 / ancuti2018 / source / readback all ok; three MP4s present.
- After the remediation: no unqualified case label in the report (grep); the page's three section
  headings read "Candidates for: ...".

**Gate checks on the B #1 candidate `b3813b8`:** ruff clean; format 110 files; mypy 20 files clean;
pytest 733 passed, 0 skipped; gpu 35 passed; harness 366 OK (1 skipped).

**Gate checks on the B #2 candidate `7f9fea1`:** ruff clean; format 110 files; mypy 20 files clean;
pytest 734 passed, 0 skipped (485 s); gpu 35 passed; harness 366 OK (1 skipped).

**Gate checks on main `7f9fea1`** after `uv sync`: ruff "All checks passed!"; format "110 files
already formatted"; mypy "Success: no issues found in 20 source files"; pytest 734 passed, 1 warning
(477 s); gpu 35 passed, 699 deselected; harness Ran 366, OK (skipped=1).

## Results for the deep CP2 (candidates; the owner names each case)

- **Pack:** `work\wp1.3d\index.html`: 48 chapter stills from the eight `SCUBA/` chapters and 12 case
  candidates, each as c3 (the default), ancuti2018 and ancuti2018 with blue compensation; side-by-side
  JPEGs in `pairs\`. **Clip:** `work\wp1.3d\clip\GX011600_{c3,ancuti2018,source}.mp4`, 179 frames
  centred on the deepest candidate, staged statistics on the 540 proxy, centred Gaussian 2.0 s.
- **Candidates (chapter_pts):** deep-water noise (lowest D = R/G): GX011600_0665.031 (D 0.209),
  GX011600_0965.031, GX011591_0095.028, GX011593_0065.032. Open blue water (highest W):
  GX011593_0255.021 (W 0.954), GX011593_0105.005, GX011600_0845.011, GX011600_0735.001. Distance haze
  (lowest H, W < 0.5): GX011589_0005.005 (H 0.050), GX011593_0025.025, GX011600_0885.017,
  GX011591_0055.022. No frame serves two cases.
- **Observations (statistics only, 60 frames per variant):** c3: no cap, no clamp, no N{} range below
  0.02 (smallest 0.0276). ancuti2018 and with blue: the red cap bound on one frame (GX011600_0665.031,
  alpha 0.94); no clamp; smallest N{} range 0.0307. Clip: c3 nothing bound; ancuti2018 red cap bound
  on 104 of 179 frames, no clamp.
- **For WP1.4b:** `work\wp1.3d\deep-frames.json` holds the 8 deepest frames (D 0.209-0.369, six from
  GX011600).

## Process deviations

- **Two re-seats stricter than the owner wants.** After the WP1.2B depth breach, the orchestrator
  treated ~250K as an automatic re-seat line and replaced the cell at 244K and 240K. The owner
  (2026-10-20): "You don't need to replace the cell at 240k, that should just be an evaluation
  point". The rule is corrected in the state file and in `docs/orchestrator-context.md` hazard (6)
  (CHARC `5692485`). Each re-seat cost a cold start; the ledger carried the work across without loss.
- **Bare `cd` (orchestrator seat):** two Bash calls moved the session's working directory into
  `work/wp1.3d` and into the `-mc` worktree; reset at once, nothing written in the wrong place.
- **Cell-side:** two docs-only commits (`b3a5fff`, `6bf9752` on the author branch) lack the
  `Co-Authored-By` footer; history not rewritten. `SCAN_END_MARGIN_S` is 0.25 s (the brief said
  "to the end"; the grid reaches the last 0.25 s of a chapter).

## Follow-ons

- **Deep CP2:** CHARC walks the owner through the pack and the clip; the sheet is the report's last
  section (10 rows PENDING).
- **WP1.4b** dispatches next (brief `docs/briefs/wp1.4b-brief.md`): reads `deep-frames.json`, flips
  `Params()` to c3 first.
- **DR-29** (new, OPEN): the instrument's out-of-envelope limits and the `--part` minor.
- Branches kept: `wp1.3d` (`5f5b90c`), `wp1.3d-b1` (`b3813b8`).
