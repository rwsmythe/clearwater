# WP-T2 -- footage locator: cumulative round ledger (Reviewer A)

Brief: `docs/briefs/wp-t2-brief.md` (FINAL). Base `36535bf`. Reviewed head `c4d53bf`
(commits `f75144a`, `b1eeb38`, `c4d53bf`). Cell: `implementer-sonnet-high` (Sonnet 5.5).

## Round ledger

| Round | Transport / CLI | Tier | Critical | Major | Minor | In / out of envelope | NEW / REOPENED | Reverts | Fixes changed | Dispatcher-read depth |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | WSL, codex-cli 0.162.1 | fast: `-m gpt-5.6-luna -c model_reasoning_effort=medium -s read-only --skip-git-repo-check` | 0 | 0 | 0 | 0 in / 0 out | 0 / 0 | 0 | nothing (no findings) | not supplied to the cell |

The reviewer's final message lists three "no finding" lines tagged REASONED (it described the
locator, the preflight and the docstrings as consistent) and one disclosure: it could not execute
anything useful (read-only sandbox, scratch-file creation failed, Windows-only venv), so its
result is a REASONED read of the diff, not a measurement. Verdict `NO_NEW_CRITICAL_MAJOR`.

## Mechanical assertions (all `grep -a`)

- Probe through the exact invocation before the round: banner `gpt-5.6-luna` / `medium` /
  `read-only`, one ` succeeded in 0ms` line.
- Banner: `OpenAI Codex v0.162.1`, `model: gpt-5.6-luna`, `reasoning effort: medium`: matches the tier.
- `^ERROR` count 0; `ERROR codex_core` count 0 (nothing to classify).
- `^tokens used` footer: 1.
- Anchored `^VERDICT: NO_NEW_CRITICAL_MAJOR`: 1 (final message, line 8).
- `^ succeeded in [0-9]`: 6.
- `grep -a -n 'docs/proofs\|wp-t2-ledger'` on the transcript: one hit, line 32, the echo of the
  prompt's own withholding sentence (an echo, not an access). The same line is the only hit for
  `clearwater-footage` and `.codex-`: also the echoed prohibition. No file under `docs/proofs`,
  the evidence folder, or the footage folder was opened.

Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp-t2\r1\` (prompt, diff, transcript,
final message, probe; `md5s.txt` inside):

    09b44298cc52a692eb20472f188d53d9  diff-r1.txt
    7f62fd5fa0cb6e618bf88af4c7002c30  final-message-r1.txt
    17f283dea83009a094bc42a1c7c05047  probe.txt
    d218298e224a779fde25426bf53c25da  review-prompt-r1.md
    fec433fbbfbc509e7bfef0b3d859b48b  transcript-r1.txt

## Own verification loop (suspect -> confirm independently -> fix)

Because the reviewer ran nothing, the cell's own checks carry the weight.

| # | Suspect | Check | Result |
|---|---|---|---|
| 1 | The walk follows a directory symlink | planted `followlinks=True` and no pruning, ran (g) | 4 failed by name (below); real code passes |
| 2 | The walk follows a junction (`os.walk(followlinks=False)` still descends) | planted: only the `isjunction` clause removed | `test_g_a_directory_link_out_of_the_root_is_not_followed[junction]` fails, 3 others pass; real code passes |
| 3 | A symlinked file named like a video matches | covered by planted control 1 | `test_g_a_file_symlink_named_like_a_video_is_not_a_match` failed |
| 4 | Runner preflight missing, so chapter 1 is written before chapter 2 is found absent | planted: preflight disabled, ran (l) | 3 failed (the `must_not_run` guard fires); real code passes |
| 5 | An unreadable subfolder is skipped silently and the chapter reads as "not in the footage folder" | read `os.walk` default (`onerror=None`) | guarded in the first draft: `onerror` raises `FootageLookupError`; not separately tested |
| 6 | `from local_config import VIDEO_EXTENSIONS` breaks `inventory.VIDEO_EXTENSIONS` | test (k) and `tests/test_inventory.py` (628 passed in the full run) | rejected, no change |
| 7 | An ambiguous folder turns into a skip in a footage test | read the three test bodies: `if exc.matches: raise` before `pytest.skip` | confirmed by reading; not reproducible without a second real chapter (STOP condition forbids planting one in the real folder) |

Counts: suspected 7; confirmed 3 as guarded by a failing planted control (items 1, 2, 4; 3 is
item 1's file case); item 5 was designed in before the first commit (no defect existed to fix);
rejected as false positive 1 (item 6); item 7 confirmed by reading only. No product-code change
resulted from the loop or from the review round.

## Positive control (g), recorded

Planted (locally, never committed; restored with `git checkout -- tools/local_config.py`):
`os.walk(..., followlinks=True)`, the directory pruning removed, the symlink skip removed.
`pytest tests/test_footage_locator.py -k test_g`: **4 failed**:

    test_g_a_directory_link_out_of_the_root_is_not_followed[symlink]   DID NOT RAISE FootageLookupError
    test_g_a_directory_link_out_of_the_root_is_not_followed[junction]  DID NOT RAISE FootageLookupError
    test_g_a_file_symlink_named_like_a_video_is_not_a_match            DID NOT RAISE FootageLookupError
    test_g_a_real_file_beside_a_link_is_still_found                    FootageLookupError: GX011628 matches 2 files ... Snorkel/GX011628.mp4, linked/GX011628.mp4

No link variant was skipped: this machine created both symlinks and junctions.
Junction-only control: removing just the `isjunction` clause failed
`...[junction]` (1 failed, 3 passed). Control for (l): preflight disabled, 3 failed.
