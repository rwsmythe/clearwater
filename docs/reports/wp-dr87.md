# WP-DR87 - bench test sampling and TIFF EXIF debts

Candidate status: implementation and cell checks complete on turn 3; awaiting
Reviewer A, Reviewer B and the orchestrator's final two-leg gate. This is not
an acceptance record. Dispatch base: `00518bb`; turn-3 parent: `d301d98`.

## Changes

- DR-87: `tests/test_prototype_backend.py` has the same autouse
  `_short_stray_check` fixture as `tests/test_prototype_clip.py`, with the
  identical docstring and `bench.STRAY_SAMPLE_S = 0.2` monkeypatch. All
  in-process bench calls in that module use the shortened interval. Existing
  assertions and the subprocess smoke test are unchanged.
- DR-93: `src/clearwater/io/photo/exif.py::from_tiff` catches
  `(ValueError, struct.error, MemoryError)`. An exhausted relocation now
  returns None and emits the existing warning once. The warning text is
  unchanged; no bare `Exception` handler was added.
- DR-94: the IFD0 drop set gains exactly 37724 ImageSourceData and 50740
  DNGPrivateData. The comment and dropped-blob docstring sentence name both
  and describe their payloads. No other tag is newly excluded.

## DR-87 measurements of record

The orchestrator ran these commands at its seat; the cell did not run a GPU
command. Both runs used:

```text
uv run pytest -q tests/test_prototype_backend.py::test_bench_gpu_records_graphics_memory --durations=0 -p no:cacheprovider
```

Each had its own worktree basetemp and log redirections, as recorded in the
ledger's exact RUN REQUESTS and the seat scripts. Both returned EXIT 0 and
passed the existing ratio assertion.

| Run | Code / fixture state | UTC start (2026-10-30) | Call | Pytest total | External wall | Result |
| --- | --- | --- | --- | --- | --- | --- |
| Before R0-A | Product/tests match `00518bb`, no backend fixture | 02:08:11Z | 87.01 s | 90.93 s | 96.684 s | 1 passed, 1 warning; EXIT 0 |
| After R2 | `d301d98`, fixture commit `4d066da`; product still matches `00518bb` | 02:23:03Z | 24.24 s | 25.24 s | 26.511 s | 1 passed, 1 warning; EXIT 0 |

Observed reduction: 65.69 s in pytest total, 70.173 s external wall. This is
a two-frame synthetic tools-cost comparison, not a spec timing row or a
fullclip performance claim. The stray scan still enumerates the system's
processes; the fixture shortens its sampling sleep.

Conditions: the seat reported nothing else heavy running, outside WP4.3
windows. During the after run, one read-only Codex review in WSL for another
package and one Claude cell writing a report were active. Preflight after:
188,014,583,808 bytes disk free; 8,648,544,256 bytes RAM available. The guarded
seat script refused a failed preflight, changed product diff or existing
basetemp; `after-product-diff.txt` was empty. These were not EXCLUSIVE runs.

Evidence under `work/wp-dr87/`: `r0/base-node.log`, `base-node-wall.txt`,
`base-node-exit.txt`, `base-node-start-utc.txt`; `r2/after-node.log`,
`after-node-wall.txt`, `after-node-exit.txt`, `after-node-start-utc.txt`,
`after-head.txt`, `after-preflight.txt`, `after-product-diff.txt` and
`run_after.sh`. Basetemp directories were not inspected or deleted by the cell.

CHARC's closing notes (`492c000c93b33597`, 2026-10-30T02:15:31Z):

1. The tool's real-run cost is unchanged by design. `tools/prototype/bench.py`
   is untouched; its default `STRAY_SAMPLE_S` remains 10.0, and its recorded
   keys and measurement logic are unchanged.
2. WP-T6's historical "sampler stop 16.3 s" did not reproduce under cProfile
   on this path. `_GpuSampler` is not constructed in core mode. R0-B measured
   `_PeakRssSampler.stop` at 0.606 s and four `stray_processes` calls at
   63.242 s cumulative of 66.558 s profiled (about 63.24 of 66.56 s).

R0-B started 2026-10-30T02:09:48Z, EXIT 0, external wall 67.015 s; the ratio
assertion passed. Its top-15 cumulative frames were pytest wrappers down to
`runner.py:114(pytest_runtest_protocol)` at 64.268 s. The separate filtered
bench block showed 4 stray calls, 0.010 s own / 63.242 s cumulative, and
1 stop call, 0.000 s own / 0.606 s cumulative. Cumulative times overlap and
must not be added. Evidence: `r0/base-node.prof`,
`base-profile-top15-and-samplers.txt`, `base-profile-wall.txt`,
`base-profile-exit.txt` and `base-profile-start-utc.txt`. No sampler remedy
was commissioned.

R0-C, the unchanged `test_bench_works_as_a_script`, started
2026-10-30T02:10:55Z: 32.81 s call, **1 passed, 1 warning in 33.83 s**, wall
34.917 s, EXIT 0. This CPU subprocess test belongs to the parallel leg and
retains the real 10 s sampling interval. CHARC `492c000c93b33597` ruled
**no remedy**, because its cost is not material; no child-side seam was built.
Evidence: `r0/base-script.log`, `base-script-wall.txt`,
`base-script-exit.txt` and `base-script-start-utc.txt`.

## DR-93 and DR-94 regression evidence

The two tests were committed RED as `51a90dd`, before the product change.
The full light run on that state returned **2 failed, 289 passed,
18 deselected, 2 warnings in 65.78s**, EXIT 1. Only these two nodes failed:

| Node in `tests/test_io_photo_exif_bytes.py` | Failure on unchanged product | GREEN behavior on turn 3 |
| --- | --- | --- |
| `test_from_tiff_memory_error_returns_none_with_warning` | `MemoryError: synthetic rewrite exhaustion` escaped `from_tiff`. | Returns None, calls the bounded writer seam once, and emits exactly one WARNING with the unchanged text. |
| `test_from_tiff_drops_private_ifd0_blobs_and_keeps_metadata` | `AssertionError: private IFD0 blobs retained: [37724, 50740]`. Make/PrintIM byte comparisons passed first. | Neither private tag survives; Make and PrintIM retain type, count and bytes via independent `_same` comparisons; structural tags stay excluded. |

The DR-93 test builds a tiny valid TIFF and monkeypatches only the private
`_write_entries` step to raise `MemoryError`; it never allocates a hostile
amount of memory. It tests the real `from_tiff` exception boundary and warning.
The DR-94 test uses the existing independent synthetic TIFF builder/parser,
small out-of-line payloads, type 7 for 37724 and type 1 for 50740. All test
files are synthetic and under per-test `tmp_path`.

Final drop additions, confirmed by CHARC's final round-0 ruling:

| Tag id | Name / purpose | Source |
| --- | --- | --- |
| 37724 / 0x935C | ImageSourceData; Photoshop layer/mask image data | [Adobe Photoshop TIFF Technical Notes, March 22 2002, p. 11](https://alternatiff.com/resources/TIFFphotoshop.pdf#page=11), Adobe-authored primary document on a mirror; also [Adobe Photoshop File Formats, TIFF tags](https://www.adobe.com/devnet-apps/photoshop/fileformatashtml/). |
| 50740 / 0xC634 | DNGPrivateData; raw converter's manufacturer-private block, IFD0 | [Adobe DNG Specification 1.7.1.0, September 2023, p. 41](https://helpx.adobe.com/content/dam/help/en/camera-raw/digital-negative/jcr_content/root/content/flex/items/position/position-par/download_section_733958301/download-1/DNG_Spec_1_7_1_0.pdf#page=41). |

PrintIM 50341 and Photoshop Annotations 50255 stay carried. Existing exclusions
700 XMP / 33723 IPTC / 34377 Photoshop resources / 34675 ICC are unchanged.
Description, authorship and capture fields remain outside the drop set;
the downstream D63 Orientation/Software edits are unchanged. No additional
private tag was proposed or removed; no DNG input support was added.

## Final-state cell checks

On the turn-3 product diff, using the required sandbox shim:

```text
PYTHONPATH=scripts uv run pytest -q tests/test_io_photo_exif_bytes.py tests/test_prototype_backend.py --basetemp=work/wp-dr87/tmp -p sandbox_mkdir_shim -p no:cacheprovider -m "not gpu and not footage and not gui and not slow and not fullclip"
291 passed, 18 deselected, 2 warnings in 59.71s
EXIT 0

uv run ruff check .
All checks passed!
EXIT 0

uv run mypy
Success: no issues found in 141 source files
EXIT 0
```

Logs: `work/wp-dr87/r3/light-green.log`, `light-green-exit.txt`,
`ruff-check.log`, `ruff-check-exit.txt`, `mypy.log`, `mypy-exit.txt`.
RED logs are in `r2/light-red.log` and `light-red-exit.txt`.
The two light-run warnings are the CuPy CUDA-path warning and Pillow's
truncated-file warning on the existing malformed-value test. uv also reports
the inherited `VIRTUAL_ENV` mismatch and ignores it in favor of this project's
environment. Neither runner failed for those warnings.

The dispatcher reported both test files clean under Ruff check/format after
turn 2. `ruff format --check` for the turn-3 candidate is reserved to the seat.
No final two-leg gate, fullclip leg or harness gate was run by this cell.
The package requires one two-leg gate after Reviewer A converges and B returns;
no fullclip leg or harness gate is commissioned here.

## Verification loop, locks and handoff

| Suspected issue | Independent confirmation / disposition |
| --- | --- |
| Fixed stray-sampling cost dominates the tiny GPU node | Source call map plus seat cProfile: four stray calls dominate. Fixture applied; seated after run passed with the figures above. |
| MemoryError escapes TIFF-to-EXIF degradation | Bounded RED on `51a90dd`; add only MemoryError to the tuple; the same test passes in the GREEN light run. |
| Private IFD0 image blobs are carried as EXIF | Independent synthetic RED retains exactly the two ruled tags; add exactly those ids; the same test passes, with Make/PrintIM byte controls. |
| Historical 16.3 s stop delay requires sampler work | Not reproduced: 0.606 s in the actual core sampler; `_GpuSampler` attribution rejected by the sole construction site in the clip path. No sampler fix authorized. |
| Pool-ratio failure under load | Observation only, as below; not reproduced in either baseline GPU run or the after run. No assertion or estimator change. |

The final cell pass checks the owned diff against the brief, exact tag/exception
changes, warning identity, unchanged controls and green light/lint/type output.
No new issue was found in that pass. Independent review and the final gate
remain pending; this does not claim package acceptance.

Bounded AST/byte checks returned EXIT 0 in `work/wp-dr87/r3/scope-check.log`:
the drop-set difference is exactly the ruled two ids, the warning AST is
identical, and all other product AST is unchanged after accounting for the
authorized tuple/drop-set/docstring edits. Tests are unchanged on this turn,
`bench.py` is byte-identical to `00518bb`, and cumulative ownership is exactly
the five granted paths. All five artifacts were verified ASCII/LF;
`git diff --check` also returned EXIT 0 (`r3/diff-check.log`).

The WP4.4 gate once observed `ratio_to_gpu_pool_reserved = 0.514 < 1.0`, then
the node passed alone. The ratio divides the frame's working-set estimate by
the process-local default CuPy pool's reserved bytes, not device-wide usage.
Live allocations or unreleasable split/cached pool state can enlarge that
denominator beyond this small frame's estimate. This is a plausible mechanism,
not a reproduced cause for that event. External load alone does not establish
it. The fixture shortens stray CPU sampling and does not isolate the GPU pool
or remedy this assertion. CHARC keeps it observation-only; a reproduced flake
must be returned with its record.

| Lock | Evidence / honored state |
| --- | --- |
| Owned files only | Cumulative changes are the two owned test files, `exif.py`, this report and the ledger. No other product/test module is edited. |
| Frozen IF-1..IF-10 | No interface file changed. |
| Real bench figures and defaults | `bench.py` byte-unchanged from `00518bb`; no key or real-run branch/default changed. |
| Narrow degradation | Only MemoryError joins the existing tuple; warning literal unchanged; other exception behavior unchanged. |
| Exact DR-94 list | Drop-set difference is exactly `{37724, 50740}`; 50341, 50255 and protected metadata fields remain absent from the drop set. |
| Existing tests | Their bodies/assertions unchanged; only the fixture and two new tests were added. |
| No dependency / OS-specific code | No dependency/configuration file changed; additions use existing portable Python/pytest paths. |
| Footage / outputs | No footage command or owner-source access; synthetic tests write only under worktree `work/` via `tmp_path`; no local config edit. |
| Other worktrees / git / communication | No other worktree access, commit, stash, mailbox post or deletion by the cell. Commits, reviews and GPU runs belong to the dispatcher. |
| Documentation | Existing public signatures unchanged; new tests have docstrings. The changed comment/docstring match the exact drop mechanics. All committed artifacts are required ASCII/LF. |

Depth readings, supplied by the dispatcher (no estimates substituted):

| Boundary | Tokens |
| --- | --- |
| After turn 1, received turn 2 | 131,491 |
| After turn 2, received turn 3 | 155,735 |
| After turn 3 | Await dispatcher reading; evaluate around 200K, stop at a step boundary near 250K. |

Reviewer A: **to be filled after the rounds**. Claude opus/high process,
STRONG tier, run by the driver on `00518bb..HEAD`; adjudication turns update
only the ledger and yield before remediation.

Reviewer B and the single two-leg gate: pending at the orchestrator's seat.
No deviation or unresolved product choice is raised. Dispositions: child-test
remedy DECLINED by CHARC; sampler remedy not commissioned because the reported
delay did not reproduce; ratio flake remains observation-only under CHARC's
ruling. Acceptance, register closure and commits remain with the dispatcher.
