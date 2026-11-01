# WP-D54: D54 warning words

Implementation and Reviewer A clean-up are delivered at `5fa56fc4`; Reviewer B
returned on report commit `cc9f3d44`. Its two test gaps are addressed below.
The final gate and acceptance witness remain owed by the dispatcher.

WP5.1 T6-1,
`tests/test_v51_video_acceptance.py::test_v6_untagged_runner_warns_bt709_limited`,
found that the encoder warning carried FFmpeg codes but omitted the words
"BT.709" and "limited range" required by D54 / V6. CHARC `3a1497d6` assigned one
encoder-owned warning; `377fcd25` supplied its initial sentence; `26f0d3d0`
superseded that wording with two branches after Reviewer A's yuvj finding.

## Final text

Resolved LIMITED (`color_range tv`):

```text
The source's colour tags are missing or unexpected; Clearwater assumed BT.709 colours and limited range for the missing or unexpected ones, and the output is tagged with these values (<codes>).
```

Resolved FULL (`color_range pc`):

```text
The source's colour tags are missing or unexpected; Clearwater assumed BT.709 colours for the missing or unexpected ones, and the output is tagged with these values (<codes>).
```

`<codes>` is computed exactly as before with
`", ".join(f"{k} {v}" for k, v in names.items())`, using
`ffmpeg_color_names(probe.video.color)`. Full range is tagged or derived from
an untagged yuvj pixel format; it is never a range default. The probe defaults
range only to limited (`probe.py:265-275`, `:300-304`; yuvj derivation at
`:300-302`). The FULL sentence therefore omits the limited-range clause.

## Changes and verification

`encode.py` adds `_assumed_color_warning` and one call at the existing warning
site, preserving the `assumed` condition and computed tags. Its Google-style
docstring explains both branches. `test_io_video_encode.py` strengthens the two
integration rows to require exactly one colour warning and its whole computed
parenthesis, including the d76 BT.601 matrix. One pure parametrized test covers
defaulted limited range, tagged BT.601 / full range and untagged `yuvj420p` full
range, checking ASCII, literal codes and the exact ruled sentences.
Two additional sink-preparation tests cover one FULL warning for a planted
untagged yuvj result and no colour warning for a fully tagged result. Both use
the existing full-range fixture and execute the real `_prepare` warning path;
no full encode, new fixture file or product change is needed.

All pytest runs below unset `PYTEST_ADDOPTS`, set `PYTHONPATH=scripts`, and use
the sandbox shim. Logs have the corresponding `turn1-*`, `turn2-*` and `turn3-*`
names recorded in `wp-d54-ledger.md`.

| State and commit | Results |
|---|---|
| RED tests `549b4ca4`, unchanged `819d0efe` product | 4 failed, 1 passed, 113 deselected: integration assertions at lines 288 / 466; both missing-helper cases at line 335. |
| GREEN `4aae3824` | Targeted: 5 passed, 113 deselected; pure node: 2 passed; encoder file: 99 passed, 19 deselected. |
| Clean-up RED, tests delivered in `5fa56fc4`, unchanged `4aae3824` product | 2 failed, 4 passed, 113 deselected: partial full range and untagged yuvj exact-sentence assertions at line 343. Stronger integration checks already passed. |
| Clean-up GREEN `5fa56fc4` | Targeted: 6 passed, 113 deselected; pure node: 3 passed; encoder file: 100 passed, 19 deselected, no skips. |

Recorded run lines:

```text
uv run pytest -q tests/test_io_video_encode.py -k "untagged_source or d76 or d54_warning_words_and_computed_codes" --basetemp=work/wp-d54/tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q tests/test_io_video_encode.py -k "untagged_source or d76 or d54_warning_words_and_computed_codes" --basetemp=work/wp-d54/turn2-light-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q tests/test_io_video_encode.py::test_d54_warning_words_and_computed_codes --basetemp=work/wp-d54/turn2-pure-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q -rs tests/test_io_video_encode.py -m "not gpu and not footage and not gui" --basetemp=work/wp-d54/turn2-encoder-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q -v tests/test_io_video_encode.py -k "untagged_source or d76 or d54_warning_words_and_computed_codes" --basetemp=work/wp-d54/turn3-red-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q tests/test_io_video_encode.py -k "untagged_source or d76 or d54_warning_words_and_computed_codes" --basetemp=work/wp-d54/turn3-light-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q tests/test_io_video_encode.py::test_d54_warning_words_and_computed_codes --basetemp=work/wp-d54/turn3-pure-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q -rs tests/test_io_video_encode.py -m "not gpu and not footage and not gui" --basetemp=work/wp-d54/turn3-encoder-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

The last three commands passed in both GREEN turns: all lint checks passed,
287 files already formatted, and no mypy issues in 146 source files. Final lint
used a worktree-local `RUFF_CACHE_DIR` after Turn 2's nonfatal default-cache
warning. No full-suite gate is claimed. The verification loop confirmed and
fixed the missing words and full-range contradiction, rejected no finding as a
false positive, and ended with no new in-envelope issue.

## Reviewer A round 1

Claude Opus high returned `NO_NEW_CRITICAL_MAJOR`; its executed encoder-file
run was 99 passed, 19 deselected. The dispatcher validated the round, which
converged with zero new blocking findings. `review.txt` and the cumulative
adjudication are identified in `wp-d54-ledger.md`.

- F1, MINOR / EXECUTED: confirmed yuvj-derived full range contradicts the initial
  sentence. Fixed RED-first with CHARC's resolved-range branch.
- F2, MINOR / EXECUTED: confirmed prefix-only assertion gap. Both integration
  rows now pin the complete parenthesis; already green before the product fix.
- F3, ADVISORY / REASONED: duplicate warnings could satisfy `any(...)`; no actual
  duplicate was found. Both rows now require exactly one colour warning.
- F4, ADVISORY / REASONED: partial full-range wording read inconsistently with
  `pc`. Addressed by F1's branch and the changed FULL-case expectation.

## Reviewer B

The dispatcher's Claude pass on `cc9f3d44` returned
`NO_NEW_CRITICAL_MAJOR`, first executing the light file (100 passed, 19
deselected). Two test-only gaps were fixed:

- F1, MINOR / EXECUTED: the helper-only FULL cases did not guard the sink's
  emission condition. `test_d54_sink_preparation_warns_once_for_assumed_yuvj_full_range`
  plants the real resolver's untagged `yuvj420p` description on existing fixture
  metadata, calls `_prepare`, and requires exactly one complete FULL sentence.
  An in-process wrapper that drops FULL-range colour warnings fails this row
  at line 375 (`0 == 1`); the original method is restored in `finally`.
- F2, ADVISORY / EXECUTED: no row guarded `assumed=False`.
  `test_d54_sink_preparation_does_not_warn_for_tagged_source` requires no colour
  warning. A wrapper adding one for a fully tagged source fails at line 403;
  the original method is restored in `finally`.
- F3, ADVISORY: the LIMITED sentence's per-field reading is unchanged; BANKED
  for CHARC at the accept.
- F4, OUT OF ENVELOPE: the probe's open-path `missing_tags` wording still says
  limited range for untagged yuvj; BANKED for CHARC at the accept.
- F5, ADVISORY: the branch fallback beyond `tv` / `pc` is unreachable; unchanged
  and BANKED for CHARC at the accept.

The new rows passed unmodified product: 2 passed, 119 deselected. Each mutant
run exited 1 with exactly its intended failure and `MUTANT_RESTORED=True`.
The driver is uncommitted scratch evidence (`turn5_mutants.py`); product files
were never edited. Logs are `turn5-rows-pytest.log`, `turn5-mutant-drop-full.log`
and `turn5-mutant-warn-tagged.log`.

```text
uv run python work/wp-d54/turn5_mutants.py drop-full
uv run python work/wp-d54/turn5_mutants.py warn-tagged
uv run pytest -q -rs tests/test_io_video_encode.py -m "not gpu and not footage and not gui and not fullclip" --basetemp=work/wp-d54/turn5-encoder-tmp -p sandbox_mkdir_shim -p no:cacheprovider
```

The final encoder-file run passed: 102 passed, 19 deselected, no skips.
Repository-wide ruff check, format check and mypy pass: all checks passed,
287 files already formatted, and 146 source files clean. The three touched
files have 0 CR bytes, the diff check passes, and product code is unchanged.
These are development checks, not the final two-leg gate.

## Limits and acceptance transfer

The sentence does not name WHICH fields were assumed: frozen IF-1
`ColorDescription` carries only `assumed`. The probe's own `missing_tags` fault
is still not forwarded, by ruling; `probe.py`, `export.py` and the GUI were not
changed. No dependency, platform-specific code, local configuration, tag, flag
or exit-status change was made. All user-facing text is ASCII. No footage or
other worktree was read, and no footage was written. The dispatcher reported
0 CR in all four package files at `5fa56fc4`.

Commissioned to the dispatcher: the final two-leg gate after WP4.6's and the
acceptance witness. After merge, rebase `wp5.1` and run the
WP5.1 node named above at the orchestrator's seat; it is still owed and is not
a figure of record. No open implementation question or unruled deviation
remains. Reviewer B's F3-F5 are banked with CHARC for disposition at the accept.

## For CHARC at the accept

Write DR-102: WP5.1 G4 found that D54's warning carried codes without the
specification's words; WP-D54 closes it with both the LIMITED and FULL branches
under `26f0d3d0`. This cell writes no register row.
