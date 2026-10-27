# WP-T3 accept record (orchestrator generation 14, 2026-10-27)

**Package:** WP-T3 fixture checker hardening (debt row DR-33 (a)-(d)), brief `docs/briefs/wp-t3-brief.md` (FINAL,
CHARC `3c3c35d7e40b525e`). Lane: Claude, `implementer-sonnet-high`, the Sonnet half of the wave 4 CALIBRATION pair
(the Codex half is WP3.20R). Cell `wpt3-cell1`, one seat; depths 144,714 at the R1 yield (64 turns) and 159,635 at
retirement. Report `docs/reports/wp-t3-fixture-checkers.md`; ledger `docs/proofs/wp-t3-ledger.md`.

**Candidate:** branch `wp-t3-mc`, the author branch `wp-t3` (`296eb18`, base `9753b7b`) rebased with
`git -c core.autocrlf=false` onto main `528d865` (`0fbbe44`, gen 13) and again onto main `70e316d` (`d5cda37`, this
seat); 5 commits; `git patch-id --stable` `e38fa930` on `9753b7b..wp-t3` and on `main..wp-t3-mc` (identical).
`528d865..70e316d` changes only `docs/charc-state.md` and `docs/orchestrator-state.md`, so `0fbbe44` and `d5cda37`
are the same code.

**Footprint (checked at this seat):** `tools/fixtures/stills.py`, `tools/fixtures/flicker.py`,
`tests/fixture_plugin.py` (`verify_generated` only), `tests/test_fixtures.py`, the report, the ledger. Q5 byte
identity: `git diff --stat 528d865..wp-t3-mc -- tests/fixtures` is empty; 87 tracked files under `tests/fixtures/`.
Every changed blob has 0 CR bytes.

## Nets

| Net | Result |
|---|---|
| Reviewer A (cell, Codex `gpt-6.1-sol` high, WSL, codex-cli 0.162.1) | R1 on `58581cb`: 0 critical / 0 major / 2 minor, both fixed as cleanup of the terminating round (head `b3d612a`); R1 terminates (zero new blocking). Tokens 88,642. Evidence `clearwater-review-evidence\wp-t3\r1\` (md5s there) |
| Candidate full pytest (gen 13, `0fbbe44`, offscreen) | 4867 passed, 2 skipped, 2873.78 s, exit 0 (07:02:45Z-07:50:41Z; host shared with light cells). Static: ruff clean, format 227, mypy 132 clean |
| Harness gate (this seat, `d5cda37`) | 379 tests OK (skipped 1) |
| Reviewer B (this seat, `codex exec -m gpt-6.1-sol -c model_reasoning_effort=high -s read-only`) | `VERDICT: NO_NEW_CRITICAL_MAJOR`; banner gpt-6.1-sol / high / read-only; 0 `^ERROR`; 15 "succeeded in"; tokens 105,819; withheld paths appear only as exclusion globs. 3 minor + 4 advisory (below). md5s in `clearwater-review-evidence\wp-t3\reviewB\md5sums.txt` (`review-B.txt` `9cca96e62c32bffaceb681d579f2b023`, prompt `684a9c920db64f7356011f6240f7e106`) |

**Reviewer B findings, adjudicated at the gate:**
- B1 MINOR, in envelope, EXECUTED: the HEIF `pitm`/`ipma` readers can read across a box boundary (a short `pitm`
  borrows the next box's size field; a short `ipma` entry list is completed by the next header), and a short `pitm`
  at EOF raises `IndexError`, not the docstring's `ValueError`. No committed file is malformed this way. BANKED
  (register row owed, below).
- B2 ADVISORY: `container_format` ignores the `ftyp` box size (an 8-byte `ftyp` still reads `heic`). BANKED with B1.
- B3 ADVISORY, out of envelope: an extended-size (`size == 1`) `ftyp` is not recognised. BANKED with B1 (the
  report's limit "widen when a real camera brand is committed" is its trigger).
- B4 MINOR, out of envelope: a malformed manifest `r_frame_rate` (`""`, `"30"`) raises `IndexError` out of
  `duration_problem`/`verify_generated` instead of a failure message. BANKED.
- B5 ADVISORY: the duration scan's completeness (packet count against `packet_pts_count`) and its stderr are not
  checked; an empty scan passes. BANKED.
- B6 ADVISORY: "names only" is a pattern guarantee (an attribute VALUE `GPSAltitude` is reported as a name). No
  location value can be printed by it. BANKED.
- B7 MINOR, report: two overstatements ("each in `tmp_path`"; item (d)'s rate source in `build_clip`). Verified at
  this seat (`flicker.py:620-622`). FIXED as "Erratum at the gate" in the report (this commit).

**Debt:** DR-33 (a)-(d) CLOSED by this package (register row by CHARC at QA). Rows owed (CHARC): the brief's Q3 gap
(UTF-16 and compressed `iTXt` XMP not scanned; trigger in the report's Limits), and the B1-B6 checker robustness
items (trigger: the next fixture regeneration, or the first real-camera HEIC committed).

**Calibration figures (HD-1, the Sonnet half):** one seat, 159,635 at retirement; one Reviewer A round; `tests/
test_fixtures.py` 347 passed at the cell's head; candidate suite 4867.

**Fence for WP-T4:** `tests/fixture_plugin.py` -- this package changed `verify_generated` only; WP-T4 rebases onto
this accept.

## Main gates

Main after the ff merge = `d5cda37` + this record and the erratum (docs only): the candidate's full pytest stands
as main's figure by code identity; harness gate re-run on main below.
