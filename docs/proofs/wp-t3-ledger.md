# WP-T3 cumulative round ledger (Reviewer A)

Package: fixture checker hardening, closes DR-33 (a)-(d). Cell `implementer-sonnet-high`
(calibration, Sonnet lane). Base `9753b7b`; round 1 reviewed HEAD `58581cb`.
Reviewer A: Codex `gpt-6.1-sol` / high, `-s read-only`, WSL transport, `codex-cli 0.162.1`.
Evidence: `C:\Users\rwsmy\clearwater-review-evidence\wp-t3\r1\` (md5s in `md5sums.txt` there).

## Round table

| Round | Head | CRITICAL / MAJOR / MINOR | In / out of envelope | NEW / REOPENED | Reverts | Fixes (product vs test-only) | Transport, CLI | Depth (dispatcher-read) |
|---|---|---|---|---|---|---|---|---|
| 1 | `58581cb` | 0 / 0 / 2 | 2 in / 0 out | 2 NEW / 0 reopened | 0 | cleanup of the terminating round, minor: 1 product (`tools/fixtures/stills.py`), 1 test-only | WSL, codex-cli 0.162.1 | 144,714 (64 turns) |

Round 1 terminates the loop (zero new blocking findings, `ROUND_TERMINATION`); no round 2.

## Round 1 mechanical assertions

- Banner `model: gpt-6.1-sol`, `reasoning effort: high`: OK.
- `ERROR` lines: 0.
- `tokens used` footer present (88,642).
- `VERDICT: NO_NEW_CRITICAL_MAJOR` anchored at column 0 in the output.
- `^ succeeded in` lines: 18 in the review (1 in the probe).
- Evidence md5s (`md5sums.txt`):
  - `review-prompt.md` 0a7f6edfe8ec74c2268af8009ef0f697
  - `review-diff.txt` 1c6d083f7b508a279a27147c14ae6196
  - `review.txt` 346f78f45a1da7c5c1dc6d130553b198
  - `review.stderr.txt` 8f1da820464cd7502826a856900f11bd
  - `probe.txt` 403e9637181818f67cbf9d58b6864f16
  - `probe.stderr.txt` 884cacabe2189f393185f85d6c2cf944
  - `run_review.sh` 56c994517c7937688d9f02a781d95e13
  - `test-summary.txt` 62ff7cb3593860cf6cdc2985ff3f33a0
  - `adjudication.md` af293e8ba3a1d58510731221cba078f3

## Round 1 adjudication

1. MINOR, REASONED, in-envelope, NEW: `stills.py` property reads can cross box boundaries (a short
   `ispe` body reads the next box's bytes). ACCEPTED. Fix: keep each property's box end, require a
   body of 12 bytes (`ispe`) or 1 byte (`irot`, `imir`), `ValueError` naming the property; a
   planted short `ispe` test that fails without the fix. Cleanup of the terminating round, minor,
   product.
2. MINOR, REASONED, in-envelope, NEW: T7 (`test_planted_ispe_disagreeing_with_stored_size_fails_by_name`)
   lacks the old-check control. ACCEPTED. Fix: assert the pre-WP-T3 comparisons
   (`photo.heif_transforms` irot, and the manifest `irot`/`imir` comparison) pass the planted
   bytes. Cleanup of the terminating round, minor, test-only.

The reviewer also reported, independently of the diff: zero XMP/GPS matches and zero
recorded-size mismatches over the 86 committed samples, zero MD5 mismatches over the 78
reproducible samples. It could not check base-to-HEAD byte identity (no git under WSL); the cell
checked it with `git diff --quiet 9753b7b -- tests/fixtures`.

## Other record

- Head after the round 1 cleanup: `b3d612a` (`tests/test_fixtures.py`: 347 passed, 0 skipped;
  ruff, format, mypy clean; `tests/fixtures` identical to `9753b7b`).

- Real clip `ad14-flicker`: 90 packets, every duration 33 ticks (rule 33.37 +/- 1); no STOP.
- Mutation checks (checker deliberately broken, the named test fails): packet-call errors dropped
  -> `test_planted_truncated_clip_fails_by_name`; brand rule relaxed, GPS regex narrowed to
  `GPSLatitude`, `ipma` requirement removed -> `test_planted_wrong_container_fails_by_name`,
  `test_planted_xmp_with_another_prefix_and_gps_only_is_caught_by_name`, and a
  `test_heif_primary_properties_names_the_missing_piece` case.
- T4 deviation (accepted by the orchestrator, round 1 ruling): the main XMP plant is a headerless
  PNG `iTXt` chunk, because a JPEG APP1 packet's `http://ns.adobe.com/xap/1.0/` header was matched
  by the old `ns.adobe.com/xap` marker; the JPEG form is planted too and shown caught by name.
