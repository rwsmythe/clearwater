# WP-T2 — Accept record (footage locator; closes DR-24)

**Accepted 2026-10-19 by the orchestrator** (generation 2, session
`clearwater-orchestrator-20261018-1442`), on CHARC's rulings `35b13416` (scope), `e5505505`
(sequence) and `59860def` (relocate `VIDEO_EXTENSIONS`). Gate per
`docs/review-gate-clearwater.md` Part 2. Tier FAST (tests and tools only, no shipped output).

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp-t2-brief.md` (FINAL, in `36535bf`). Spec v0.5.2. |
| Base SHA | `36535bf` |
| Author head | `3567c56` (`wpt2-cell`, implementer-sonnet-high; one round; head read unchanged at three readings 01:21Z-01:26Z across turns). |
| Merged head | `8c9d780` (`wp-t2-mc` = `wp-t2` rebased onto main `12013bc`; main fast-forwarded). |
| Byte identity | `git patch-id --stable` = `e5354e8d4f884b47a791a51e24009a85c79171e4` on `36535bf..3567c56`, on the B candidate `6b8cba1..9d42c07`, and on main `12013bc..8c9d780`. The merged tree differs from the B-reviewed tree `9d42c07` only in `docs/proofs/cp1-footage-sorting.md` (CHARC's CP1 record, committed on main during the gate). |
| Reviewer A | Codex FAST (gpt-5.6-luna / medium), WSL, codex-cli 0.162.1. One round: 0 / 0 / 0, `NO_NEW_CRITICAL_MAJOR`; REASONED only (the sandbox could not execute). The cell's planted positive controls carry the verification (below). Ledger `docs/proofs/wp-t2-ledger.md`; evidence `clearwater-review-evidence\wp-t2\r1\`. |
| Reviewer B | My seat pass on `9d42c07`: one major, REJECTED with cause; one minor and one advisory BANKED (below). |
| Owned files | The brief's nine paths exactly (`git diff --stat`); no dependency change. |

## Reviewer B (seat), on candidate `9d42c07`

Evidence `C:\Users\rwsmy\clearwater-review-evidence\wp-t2\reviewB\` (`md5s.txt` there). Tier
FAST, as the package. Assertions:
- the banner reads gpt-5.6-luna / medium (probe READY 01:22Z, same invocation);
- `^ERROR` 0; one `ERROR codex_core` hit, an echo of the brief it read;
- footer 1; 7 `succeeded in`;
- an anchored `VERDICT: NEW_CRITICAL_MAJOR_FOUND`;
- no withheld access: every `docs/proofs`, ledger, evidence and footage hit is the prompt's own
  withholding list, the diff header, or the brief's text.

| File | md5 |
|---|---|
| prompt | `72f662948d0d9bb8981c002e9ac538a6` |
| diff | `09b44298cc52a692eb20472f188d53d9` |
| transcript | `880b88c6071ca0b06622a035338d4be5` |
| stderr | `f11bac86a25129acc10d54982def94c9` |

| # | Finding | Disposition |
|---|---|---|
| 1 | MAJOR (reasoned): a `root` that is itself a directory symlink or junction is walked, so the locator returns a file whose physical location is the link's target. | **REJECTED, not a defect.** The brief's rule (claim 2, "never leaves the root") is about links UNDER the root, which could lead out of the footage folder; the root is the folder the owner configured, and following it is the intended meaning (a footage folder moved behind a junction must keep working). The locator only reads. The configured root is a plain folder (`os.path.islink` and `os.path.isjunction` False, `realpath` equal, read at my seat). |
| 2 | MINOR (reasoned): an unreadable root or subfolder raises `FootageLookupError` with `matches == ()`, which the three footage tests treat as zero matches and SKIP. | **BANKED, DR-27(1).** The skip is visible under `-rs` with the "cannot search" message, so it is not a silent pass; the gate asserts 0 skipped. The cell flagged it in its return. |
| 3 | ADVISORY: the `tests/test_prototype_temporal.py` module docstring still names `GX011628.MP4`. | **BANKED, DR-27(2)** (outside the owned lines; the cell flagged it). |

## Verification QA (orchestrator seat)

**Gate checks on the candidate `9d42c07`**, WinGet links on PATH:

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 96 files already formatted
uv run mypy                    -> Success: no issues found in 18 source files
uv run pytest -q -rs           -> 628 passed, 1 warning (0 skipped)
uv run pytest -q -m gpu        -> 24 passed, 604 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

**Gate checks on main `8c9d780`** after `uv sync`:

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 96 files already formatted
uv run mypy                    -> Success: no issues found in 18 source files
uv run pytest -q -rs           -> 628 passed, 1 warning (0 skipped)
uv run pytest -q -m gpu        -> 24 passed, 604 deselected
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

The "0 skipped" assertion is restored: the three footage tests that skipped since the owner's
2026-10-18 layout (`docs/proofs/wp1.4-accept.md`, DR-24) run and pass.

**Witness (the real footage, read-only).** From the candidate's `tools/`: every video file
under the configured footage folder (35, found by an independent `os.walk`) resolves through
`find_footage_file(<its stem>)` to itself, 35 of 35, at about 0.5 ms per lookup; no stem occurs
twice; `GX011625`..`GX011628` (and `gx011628`) resolve to `Snorkel\GX01162x.mp4`; an absent stem
raises `FootageLookupError` with `matches == ()`. Script in the session scratchpad
(`wit/locwit.py`).

**Code read at my seat.** The diff of `tools/local_config.py`, `tools/inventory.py`,
`tools/lookcheck/pack.py` and `tools/statistics_experiments.py` matches claims 1-3: one
`VIDEO_EXTENSIONS` definition (stdlib-only module), junctions pruned explicitly, symlink files
skipped, sorted matches, the runner's lookup before the first write for every phase that reads a
chapter.

**Positive controls (the cell's, planted and reverted, ledger):** a link-following walk fails
the four (g) tests by name; removing only the junction clause fails the junction test; disabling
the runner's preflight fails the three (l) tests.

**Deviations accepted.**
- `tools/inventory.py`: two lines (the existing import widened, the definition deleted) instead
  of the brief's one, to keep imports above module constants (ruff E402/I001). Same effect;
  the WP0.2 suite passes unchanged.
- The three switched tests also changed their import lines (one dropped an unused import).
  These are mechanical, within the owned files.

## Follow-ons

| Item | Disposition |
|---|---|
| DR-24 (footage-layout skips) | CLOSED by this package. |
| The unreadable-folder skip; the stale test docstring | BANKED, DR-27. |
| `tools/container_spike/spike.py` root-path CLI | Stays BANKED, DR-26 (CHARC `6c5d88685e64a37c`). |
| WP1.2 Part B | Next (EXCLUSIVE); its brief gains CHARC's CP1 notes (`99f6abaf9afd829e`) before dispatch. |

Branches kept: `wp-t2` (`3567c56`, the author head) and `wp-t2-b` (`9d42c07`, B's candidate).

## CHARC QA (post-Part B)

Suite re-run at the CHARC seat on main `5e3aa33` (WP-T2 plus later main commits), 2026-10-19
~14:10Z, after the Part B exclusive window closed: `uv run pytest -q -p no:cacheprovider
--basetemp=work/pytest-charc` -> **628 passed, 0 skipped** in 151 s. Matches the accept's gate
count. The cheap checks (patch-id `e5354e8d`, md5s, VERDICT line) were confirmed 2026-10-19 before
the window. WP-T2 QA is CONFIRMED.
