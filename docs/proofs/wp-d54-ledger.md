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

## Cumulative review rounds

No Reviewer A or Reviewer B round yet. The following row schema will be populated
when findings are dispatched; this RED turn is not a review round.

| Round | Critical / major / minor | In / out of envelope | NEW / REOPENED | Reverts | Product / test-only fixes | Transport / CLI | Verdict | Evidence |
|---|---|---|---|---|---|---|---|---|

## Dispatcher-read depth

| Boundary | Context depth (dispatcher fills) | Disposition |
|---|---|---|
| Turn 1 RED yield | 75,711 tokens (dispatcher supplied in Turn 2; session `01a19680-681b-7e73-9fa1-893bc1fdefaa`) | RED accepted and committed as `549b4ca4`. |
| Turn 2 GREEN yield | Pending dispatcher figure | Fix and light validation; yield for Reviewer A round 1. |
