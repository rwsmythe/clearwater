# WP3.17 accept record (orchestrator generation 12, 2026-10-26)

**Package:** WP3.17 parameter panels and presets (`clearwater.gui.parameter_panels`, `clearwater.gui.preset_panel`),
brief `docs/briefs/wp3.17-brief.md` (FINAL; CHARC rulings `53d1d906e47fe2c9`, blend ruling). One seat
(implementer-sonnet-high, seat 1, STRONG): round 0 (123,285 at the round-0 yield), round 1 (222,661 at the round-1
yield), Reviewer B pass-1 remediation (249,866); pass-2 fixes on `wp3.17` (depth not recorded by generation 11).

**Candidate:** author branch `wp3.17` (`f819ef3`, base `718324b`, 23 commits); merge candidate `wp3.17-mc` (`0f7b5cd`,
base `7fff7be`, 23 commits). Gate: stacked branch `stackB` = main `ccaecd7` + WP3.17 + WP3.19 + WP3.20 + WP3.18
(cherry-picked ranges, file sets disjoint; head `d71d994` at drafting, 97 commits above `ccaecd7`); every owned file
byte-identical in `stackB`, `wp3.17-mc` and `wp3.17` (`git diff`, 0 lines). Merged: one `git merge --ff-only` of `stackB-acc` onto main; this record's own commit follows the package's last commit.

**Footprint (checked at this seat):** owned files only: `src/clearwater/gui/parameter_panels.py`,
`src/clearwater/gui/preset_panel.py`, `tests/test_gui_parameter_panels.py`, `tests/test_gui_preset_panel.py`, the
report `docs/reports/wp3.17-parameter-panels-presets.md`, the ledger. `interfaces/`, `gui/__init__.py`, `contract.py`,
`pyproject.toml`, `uv.lock` untouched; 0 CR bytes in every owned blob.

**Results:** panels generated from the selected method's IF-3 schema (one control per parameter, D17; D49 rebuild on a
method switch; carry-over of values valid for the new method); every G6 preset operation (load, save as, rename,
delete, import, export) with confirmation before any overwrite (DR-34 (a)) and owners `"parameters"` / `"presets"`
(DR-44 (b)); V13 leg (save -> export -> import -> load). Decimals rule after Reviewer B: shortest-repr decimals of the
default and bounds, 2..15; no slider for a span 15 decimals cannot resolve, a non-finite span or an underflowing step;
slider ends exact. Targeted: 86 passed (both modules + `tests/test_gui_deps.py`).

## Nets

| Net | Result |
|---|---|
| Reviewer A (cell, STRONG, WSL codex-cli / gpt-5.6-sol high) | R1 reviewer-tagged 0/3 MAJOR + 4 MINOR, 7 NEW; adjudicated 0 blocking (#1, #2 MINOR; #4 out of envelope; #5 accepted limitation), upheld: terminated at R1. Cleanup `d330a70` (tests, 5 failed + 1 teardown error on `b2822d3`), `e7efe31`, `2dc845a`, `ca44ae7`, `88d377e`, `5eef87f`; 73 passed after. 10 "succeeded in", 136,361 tokens; evidence `clearwater-review-evidence\wp3.17\r1` |
| Reviewer B pass 1 (this seat, `8e0ed98`, kept as branch `wp3.17-mc1`) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 16 "succeeded in"; 137,846 tokens. #1 MAJOR (spin decimals capped at 6: a 1e-7..2e-7 range collapsed, maximum unreachable), #2, #3 MINOR (test gaps: doubled visible row; NFC + casefold save-over) -> `eda1d94`, `f1d60e9`, `d5c3487`; 2 failed / 79 passed on `6e295c1` + new tests, 81 passed on the head. md5 `review-B.txt` 1f7a19149fd3... (`reviewB\md5sums.txt`) |
| Reviewer B pass 2 (this seat, `bbe9284`, kept as branch `wp3.17-mc2`) | NEW_CRITICAL_MAJOR_FOUND; banner gpt-5.6-sol / high, read-only; 0 `^ERROR`; 24 "succeeded in"; 152,632 tokens. 2 MAJOR, 4 MINOR. SECOND BLOCKING PASS, ADJUDICATED AT THE GATE (generation 11), CHARC UPHELD (msg d329e80e351c3dcc): #2 MAJOR (`float_has_slider` raised for `0..5e-324` / `-1e308..1e308`) `14b448e`; #3 slider ends exact `72356f8`; #4 shared owner clear `c161353`; #5 Save as refresh on failure `7b7b6af`; #6 report `f819ef3`. VERIFIED BY EXECUTION at the orchestrator's seat: 5 failed on `f6b40a9`, 86 passed on the candidate. #1 (a float span or bounds 15 decimals cannot resolve) = LIMIT. md5 `review-B.txt` 3970f4706b65... (`reviewB2\md5sums.txt`) |
| Candidate full pytest (this seat, stack top `d71d994` = main `ccaecd7` + WP3.17 + WP3.19 + WP3.20 + WP3.18) | 4501 passed, 2 skipped, 1579 s, exit 0 (CuPy as installed, offscreen, one background process; log `.worktrees/stackB/work/g12-full.log`). This is also main's figure by code identity: main after the merge differs from `d71d994` in the four accept records only |
| Harness gate | 366 OK (1 skipped) on `d71d994`; ruff clean, 217 formatted, mypy 126 clean; CR check 0 on every changed blob |

**Debt:** no DR row named by the ledger or report. Row by CHARC at QA: the 15-decimal resolution limit (B pass 2 #1;
trigger: a method declaring a float parameter whose span or bounds 15 decimals cannot resolve). Other limits stay in the
report (cross-parameter relation `normalisation_low < normalisation_high` not enforced, an AD-20 matter; equal min and
max get no slider; silent drop of values that do not carry over; shared owner `"parameters"` cleared by either panel).

**Consumer notes:** WP4.3 calls `install_parameter_panels(window)` once (attaches "Basic", "Advanced", "Presets" in
`Area.PARAMETERS`), imports by module path (`gui/__init__.py` exports nothing), and keeps `"c3"` first in
`engines.methods` (selector order; the starter presets are `"c3"`). WP3.4: every `Parameter` needs finite bounds for a
slider; a relation between parameters reaches the user only as the preview's `shell.preview` error at render.
