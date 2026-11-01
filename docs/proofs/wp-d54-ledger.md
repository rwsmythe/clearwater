# WP-D54 cumulative ledger

## Scope and grounded anchors

Turn 1 is RED only. Grounded against HEAD `819d0efe` (main `a27b7213`
plus the dispatch brief); product code is unchanged in this turn.

| Anchor on `819d0efe` | Mechanic and measured surface |
|---|---|
| `src/clearwater/io/video/encode.py:616` and `:668-674` | `FFmpegVideoSink._prepare` checks `probe.video.color.assumed`, computes FFmpeg names, joins the codes and appends the D54 sentence to `self._warnings`. The existing export tests inspect `run.report.warnings`. The sentence currently says "assumed values" without "BT.709" or "limited range". |
| `src/clearwater/color/swscale.py:206-228` | `ffmpeg_color_names` maps the resolved description to output option names, retaining real matrix and range values. The new pure test checks those names against independent literal code lists, including BT.601 / full range (`smpte170m` / `pc`). |
| `src/clearwater/interfaces/image.py:25-45` | Frozen IF-1 `ColorDescription` supplies resolved fields and a single `assumed` flag; the test constructs descriptions without changing the interface. |
| `tests/test_io_video_encode.py:288` | `test_untagged_source_is_tagged_bt709_limited_with_a_warning` checks the emitted tags and the sink report. Its former "assumed values" assertion is replaced with words and parenthesized-code checks in the same warning. |
| `tests/test_io_video_encode.py:403-412` | `test_d76_from_a_bt601_source` retains the existing FFmpeg export and fidelity assertions; only its warning assertion is strengthened. |
| `docs/underwater-correction-spec.md:92`, `:278`, `:487` | D54, the video-input colour rule, and V6 require the BT.709 / limited-range warning. Citation correction: the quoted colour rule is in section 6.5 at :278; section 5.4 at :224 concerns damaged inputs. The required behaviour and the ruled sentence are unambiguous. |
| `docs/clearwater-implementation-plan.md:89-102` | Definition of done governs scope, documentation, checks, verification, reporting and independent review. This turn deliberately stops at the dispatched RED boundary. |
| `docs/review-gate-clearwater.md:14-28`, `:53-85`, `:132-137` | The dispatcher runs the Claude reviewer between Codex turns; the cell adjudicates findings and maintains this ledger. Zero new blocking findings terminates review; the full gate follows Reviewer B at the dispatcher's seat. No review round has run yet. |

## Planned pure sentence seam

Use a module-private `_assumed_color_warning(names: Mapping[str, str]) -> str`
helper in `encode.py`. Extract the sentence construction currently at :670-674;
leave the `assumed` condition and `ffmpeg_color_names(probe.video.color)` call at
:668-669 in place. The helper joins the mapping in its existing order and returns
CHARC's exact sentence. `_prepare` will append that return value unchanged.
This avoids additional product imports or any change to tags, flags or status.
The helper itself and its call-site replacement belong to Turn 2.

The new single parametrized test,
`test_d54_warning_words_and_computed_codes`, calls the planned helper through the
already imported module, so its absence fails at runtime without preventing the
two existing tests from collecting. Its cases are fully defaulted BT.709 / limited
and partially defaulted BT.709 primaries and transfer with tagged BT.601 / full
range. It asserts ASCII, the required words, the computed codes against literal
expectations, and the verbatim ruled sentence. Its body performs no FFmpeg or
file I/O; it inherits the module's existing FFmpeg-availability fixture and has no
hardware, footage, GUI, slow or fullclip marker, so it belongs to the parallel leg.

## Turn 1 validation

Run from the worktree root with `PYTEST_ADDOPTS` unset and `PYTHONPATH=scripts`:

```text
uv run pytest -q tests/test_io_video_encode.py -k "untagged_source or d76 or d54_warning_words_and_computed_codes" --basetemp=work/wp-d54/tmp -p sandbox_mkdir_shim -p no:cacheprovider
```

Log: `work/wp-d54/turn1-red-pytest.log` (gitignored, inside this worktree).
Exit code: **1**. Summary: **4 failed, 1 passed, 113 deselected in 5.69s**.
The existing tests reached their changed warning assertions after the preceding
tag / fidelity assertions passed. The pure cases reached the missing helper
after their computed-code checks passed.

| Failing node ID (all under `tests/test_io_video_encode.py`) | Failure line in Turn 1 | Observed failure |
|---|---|---|
| `test_untagged_source_is_tagged_bt709_limited_with_a_warning` | `:288` | `assert any(...)` is false for the required words and code in one warning. |
| `test_d54_warning_words_and_computed_codes[fully-defaulted]` | `:335` | `AttributeError`: `encode` has no `_assumed_color_warning`. |
| `test_d54_warning_words_and_computed_codes[partially-defaulted-full-range]` | `:335` | Same expected missing-helper `AttributeError`. |
| `test_d76_from_a_bt601_source` | `:466` | `assert any(...)` is false for the required words and code in one warning. |

Additional light checks, each exit **0**:

- `uv run ruff check tests/test_io_video_encode.py`: `All checks passed!`
  (`work/wp-d54/turn1-ruff-check.log`).
- `uv run ruff format --check tests/test_io_video_encode.py`:
  `1 file already formatted` (`work/wp-d54/turn1-ruff-format.log`).

uv warned that inherited `VIRTUAL_ENV` names the main tree's environment and is
ignored in favour of this project's `.venv`. No `--active` override was used.
Repository-wide lint, formatting, mypy, GREEN, independent review and the final
two-leg gate are pending their dispatched turns; no gate result is claimed here.

## Verification loop record

| Suspected issue | Independent confirmation | Disposition |
|---|---|---|
| The sink report omits D54's plain words for fully and partially defaulted inputs. | Both existing FFmpeg tests fail specifically at the strengthened report-warning assertions on unchanged product. | Confirmed; product fix deferred to Turn 2 as dispatched. |
| A pure sentence seam is absent. | Both new cases fail specifically on `_assumed_color_warning` lookup. | Expected RED; extraction deferred to Turn 2. |
| Further in-envelope gaps in the RED deliverable. | Reviewed the diff and test outcomes against Turn 1's scope; product diff is empty. | No additional issue found; no false-positive finding or fix in this turn. |

Only the two owned assertions and one new test were changed in the existing test
file. Product, frozen interfaces, dependencies, local configuration and all other
test files are unchanged. No footage was read or written. Runner outputs and
temporary data are under this worktree's `work/`. No commit or `.git` write was
attempted. The dispatcher owns the commit and its committed-blob LF checks.

## Turn 2: fix and GREEN

Starting HEAD: `549b4ca4`, the dispatcher's accepted RED commit (reported 0 CR in
both committed files). Added `_assumed_color_warning(names: Mapping[str, str])`
at `src/clearwater/io/video/encode.py:503`, with a Google-style docstring, and
replaced only the old sentence-construction block with its call at :687. The
existing `assumed` condition and `ffmpeg_color_names(probe.video.color)` call
remain unchanged. The helper uses the original
`", ".join(f"{k} {v}" for k, v in names.items())` expression and returns CHARC
`377fcd25`'s sentence verbatim.

This turn changes product code and this ledger only; the accepted RED tests are
unchanged. No tag, flag, exit status, interface, dependency, other message or
configuration change was made.

All pytest runs below used `PYTEST_ADDOPTS` unset, `PYTHONPATH=scripts`, the
sandbox mkdir shim and no cache provider. Inherited `VIRTUAL_ENV` was unset so uv
uses the worktree environment without its Turn 1 warning. Commands ran from the
worktree root, with all logs and basetemps under `work/wp-d54/`.

```text
uv run pytest -q tests/test_io_video_encode.py -k "untagged_source or d76 or d54_warning_words_and_computed_codes" --basetemp=work/wp-d54/turn2-light-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q tests/test_io_video_encode.py::test_d54_warning_words_and_computed_codes --basetemp=work/wp-d54/turn2-pure-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q -rs tests/test_io_video_encode.py -m "not gpu and not footage and not gui" --basetemp=work/wp-d54/turn2-encoder-tmp -p sandbox_mkdir_shim -p no:cacheprovider
```

| Run | Log under `work/wp-d54/` | Exit | Result |
|---|---|---|---|
| Targeted GREEN | `turn2-light-pytest.log` | 0 | 5 passed, 113 deselected in 6.32s |
| Pure test's own node | `turn2-pure-pytest.log` | 0 | 2 passed in 0.13s |
| Whole encoder file with permitted markers | `turn2-encoder-pytest.log` | 0 | 99 passed, 19 deselected in 108.45s (0:01:48); no skips |

Repository-wide light checks (not a substitute for the dispatcher's final gate):

| Command | Log under `work/wp-d54/` | Exit | Summary |
|---|---|---|---|
| `uv run ruff check .` | `turn2-ruff-check-clean.log` | 0 | All checks passed! |
| `uv run ruff format --check .` | `turn2-ruff-format.log` | 0 | 287 files already formatted |
| `uv run mypy` | `turn2-mypy.log` | 0 | Success: no issues found in 146 source files |

The first lint attempt also exited 0 with `All checks passed!` but emitted
nonfatal default-cache write warnings (`turn2-ruff-check.log`). Re-ran the same
command with `RUFF_CACHE_DIR=work/wp-d54/turn2-ruff-cache`; the recorded clean run
has no warnings. No repository configuration was edited.

Verification loop: confirmed the two Turn 1 report-warning failures and both
missing-helper failures are fixed by the targeted GREEN run and the separate
pure-node run. The pure cases independently check literal FFmpeg codes, the full
ruled sentence and ASCII, including retained BT.601 / full-range tags. Inspected
the product diff: only the helper insertion and original :670-674 replacement
changed; the conversion and warning condition are preserved. `git diff --check`
passed. The whole encoder-file run passed all 99 tests selected by the dispatched
marker expression, with no remaining old-warning assertion failure or other
failure. A final pass against the brief and the diff found no new in-envelope
issue. No false-positive finding was recorded in Turn 2.

Reviewer A round 1, Reviewer B, the final two-leg gate, the post-merge WP5.1
witness and the final completion report remain pending at their dispatched
boundaries. No footage or other worktree was read; no commit, stash or `.git`
write was attempted.

## Turn 3: Reviewer A round 1 clean-up (terminating)

Turn 2 was committed by the dispatcher as `4aae3824` with 0 CR reported. Turn 3
started at `3c27d51e`, which adds CHARC's ruling to the brief. Ruling
`26f0d3d0`, at `docs/briefs/wp-d54-brief.md:32-43`, supersedes the original
single sentence: resolved `tv` keeps "BT.709 colours and limited range"; resolved
`pc` says "BT.709 colours". No owner input or interface change is needed.

Reviewer A round 1 evidence (read-only):
`C:\Users\rwsmy\clearwater-review-evidence\wp-d54\r1\review.txt`, MD5
`f95dcc5c566a457db3b0f02aaa1e8cab`. The reviewer returned
`VERDICT: NO_NEW_CRITICAL_MAJOR` and reported an executed encoder-file run of
99 passed, 19 deselected in 110.63s. The dispatcher supplied these validity
assertions: model `claude-opus-5-5`, high effort requested, 18 turns,
`is_error=false`, zero permission denials, and a clean worktree after review.
The round counts and terminates the loop; this turn is its bounded clean-up,
not another review round. The dispatcher retains the durable evidence bundle.

### Findings and adjudication

| Finding | Classification and confirmation | RED / already-green evidence | Fix and surface |
|---|---|---|---|
| F1 | MINOR, in envelope, NEW, EXECUTED. Confirmed: `probe._resolve_color({}, "yuvj420p", 8)` derives full range while defaulting the other colour fields. `probe.py:301-304` distinguishes that derivation from the limited-only range default; :265-275 records actual defaults. | The new `untagged-yuvj420p-full-range` case fails on the unchanged `4aae3824` product, because the sentence includes "and limited range" with `color_range pc`. | Product: the existing private helper chooses its range clause from `names.get("color_range") == "tv"`; its docstring explains both branches and why full range is never assumed. The call site stays unchanged. Test: add the untagged yuvj case to the existing pure test, using the real pure probe resolver and then the same mapping/helper path as the encoder. |
| F2 | MINOR, in envelope, NEW, EXECUTED. Confirmed test gap: the prefix-only checks accept a wrong matrix/range suffix. No current output defect was found. | Both strengthened integration rows already pass on `4aae3824`'s product. | Test-only: assert the entire parenthesis through its final `).`; the d76 row pins `colorspace smpte170m, color_range tv`. |
| F3 | ADVISORY, in envelope, NEW, REASONED. Confirmed assertion gap: the former `any(...)` could accept duplicate colour warnings; reviewer found no actual duplicate emission. | Both strengthened integration rows already pass on `4aae3824`'s product. | Test-only: select colour-tag warnings and assert length exactly one before checking its words and full parenthesis. |
| F4 | ADVISORY, in envelope, NEW, REASONED. The old partial full-range wording was permitted by the earlier ruling but reads inconsistently with `pc`; CHARC's new wording removes that ambiguity. | The existing `partially-defaulted-full-range` case now expects the FULL branch and fails on the unchanged `4aae3824` product. This is an intentional expected-sentence change under the new ruling. | Same product fix as F1; test-only expected words now omit limited range for this case. No additional product change. |

The single parametrized pure test now resolves source tags through
`probe._resolve_color` rather than constructing descriptions manually. Its
three cases cover untagged non-yuvj limited range, tagged BT.601 / full range
with other fields defaulted, and completely untagged yuvj-derived full range.
Independent literal code expectations still check the resolved mapping before
the helper is called. Exact sentence and ASCII assertions remain in place.

### RED before the helper fix

With `PYTEST_ADDOPTS` and inherited `VIRTUAL_ENV` unset, `PYTHONPATH=scripts`:

```text
uv run pytest -q -v tests/test_io_video_encode.py -k "untagged_source or d76 or d54_warning_words_and_computed_codes" --basetemp=work/wp-d54/turn3-red-tmp -p sandbox_mkdir_shim -p no:cacheprovider
```

Log: `work/wp-d54/turn3-red-pytest.log`; exit **1**:
**2 failed, 4 passed, 113 deselected in 8.54s**. Immediately after this run,
`git diff --quiet 4aae3824 -- src/clearwater/io/video/encode.py` exited 0,
confirming that the RED ran on Turn 2's unchanged product.

| Failing node ID (under `tests/test_io_video_encode.py`) | RED failure line | Observed failure |
|---|---|---|
| `test_d54_warning_words_and_computed_codes[partially-defaulted-full-range]` | `:343` | Exact sentence assertion: actual contains "and limited range"; expected FULL branch omits it, retaining `colorspace smpte170m, color_range pc`. |
| `test_d54_warning_words_and_computed_codes[untagged-yuvj420p-full-range]` | `:343` | Same wrong range clause, retaining `colorspace bt709, color_range pc`. |

The four passes include both integration rows, so F2 and F3's stronger checks
were already green before the product fix. The fully-defaulted LIMITED case
also remained green. RED and fix are delivered together in this turn as
dispatched; no intermediate commit was attempted.

### GREEN and light checks

All commands ran from this worktree root. Pytest used `PYTEST_ADDOPTS` unset,
`PYTHONPATH=scripts`, and the required sandbox shim. Each run has its own fresh
basetemp; all logs and generated data stay under `work/wp-d54/`.

```text
uv run pytest -q tests/test_io_video_encode.py -k "untagged_source or d76 or d54_warning_words_and_computed_codes" --basetemp=work/wp-d54/turn3-light-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q tests/test_io_video_encode.py::test_d54_warning_words_and_computed_codes --basetemp=work/wp-d54/turn3-pure-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run pytest -q -rs tests/test_io_video_encode.py -m "not gpu and not footage and not gui" --basetemp=work/wp-d54/turn3-encoder-tmp -p sandbox_mkdir_shim -p no:cacheprovider
uv run ruff check .
uv run ruff format --check .
uv run mypy
```

| Run | Log under `work/wp-d54/` | Exit | Result |
|---|---|---|---|
| Targeted GREEN | `turn3-light-pytest.log` | 0 | 6 passed, 113 deselected in 7.06s |
| Pure test's own node | `turn3-pure-pytest.log` | 0 | 3 passed in 0.20s |
| Whole encoder file, permitted markers | `turn3-encoder-pytest.log` | 0 | 100 passed, 19 deselected in 155.62s (0:02:35); no skips |
| Repository-wide ruff check | `turn3-ruff-check.log` | 0 | All checks passed! |
| Repository-wide ruff format check | `turn3-ruff-format.log` | 0 | 287 files already formatted |
| Repository-wide mypy | `turn3-mypy.log` | 0 | Success: no issues found in 146 source files |

Ruff used `RUFF_CACHE_DIR=work/wp-d54/turn3-ruff-cache` to avoid the known
default-cache permissions warning; no configuration file changed. Verification
so far confirms both full-range RED failures are fixed, the LIMITED sentence is
unchanged, complete parentheses and one-warning checks pass, and `git diff
--check` passes. Scope inspection finds product changes confined to the existing
helper and test changes confined to the two owned assertions and pure test.
The whole encoder-file run passed all 100 selected tests, including the added
yuvj case, with no failure or skip. The final verification pass against the
ruling, diff and run results found no new in-envelope issue. All four review
findings are addressed; no finding was rejected as a false positive.

No frozen interface, probe, export, GUI, dependency or local configuration was
changed. No footage or other worktree was read; no commit, stash or `.git` write
was attempted. The final report turn, Reviewer B, final two-leg gate and
post-merge WP5.1 witness remain pending at the dispatcher's boundaries.

## Turn 4: report

Starting HEAD: `5fa56fc4`, the dispatcher's committed terminating clean-up.
The dispatcher reports 0 CR in all four package files and confirms Reviewer A
has converged. Supplied depth after Turn 3: 118,386 tokens (recorded below).

Added `docs/reports/wp-d54-warning-words.md`: the original finding, three CHARC
rulings, verbatim final range branches, implementation, RED and GREEN evidence
by commit with commands and counts, all four finding dispositions, limits,
acceptance witness still owed, and DR-102's two-branch handoff to CHARC.
The cumulative round-1 row below is complete; no new review round is opened.

This is a documentation-only turn: no product or test change, no new test run,
no dependency or configuration change. Report claims use the recorded run
results, the unchanged implementation and the dispatcher's commit assertions.
Validation found 0 non-ASCII bytes and 0 CR bytes in the new report;
`git diff --check` exited 0. `git diff --quiet HEAD -- src tests` exited 0,
confirming product and tests are unchanged. Rechecked the recorded Turn 3 log
summaries: targeted 6 passed, pure 3 passed, encoder file 100 passed / 19
deselected, ruff clean, 287 files formatted, mypy 146 source files clean.
Reviewer B, the final two-leg gate and the post-merge WP5.1 witness remain
commissioned to the dispatcher; no accept or full-gate result is claimed.

## Cumulative review rounds

Reviewer A round 1 counts and terminates the loop with zero new blocking
findings. All four findings are adjudicated above; Reviewer B remains pending.

| Round | Critical / major / minor | In / out of envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Transport / CLI | Verdict | Evidence |
|---|---|---|---|---|---|---|---|---|
| A1 | 0 critical / 0 major / 2 minor / 2 advisory | 4 in / 0 out | 4 NEW / 0 REOPENED | 0 | Product helper changed for F1; F4 shares that fix. F2/F3 and case updates are tests. | `claude -p`, Opus high (`claude-opus-5-5`); CLI version not supplied | `NO_NEW_CRITICAL_MAJOR`; terminating clean-up | `C:\Users\rwsmy\clearwater-review-evidence\wp-d54\r1\review.txt` (MD5 above); dispatcher validity assertions recorded above |

## Dispatcher-read depth

| Boundary | Context depth (dispatcher fills) | Disposition |
|---|---|---|
| Turn 1 RED yield | 75,711 tokens (dispatcher supplied in Turn 2; session `01a19680-681b-7e73-9fa1-893bc1fdefaa`) | RED accepted and committed as `549b4ca4`. |
| Turn 2 GREEN yield | 89,798 tokens (dispatcher supplied in Turn 3) | Committed as `4aae3824`; Reviewer A round 1 returned. |
| Turn 3 terminating clean-up yield | 118,386 tokens (dispatcher supplied in Turn 4) | Committed as `5fa56fc4`; Reviewer A converged. |
| Turn 4 report yield | Pending dispatcher figure | Report delivered; dispatcher owns Reviewer B, gate and acceptance witness. |
