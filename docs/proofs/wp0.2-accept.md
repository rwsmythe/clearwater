# WP0.2 — Accept record

**Accepted 2026-10-15 by the orchestrator** (session `clearwater-orchestrator-20261014-1258`),
on CHARC's commission `1b16f4179b32029c`. Gate per `docs/review-gate-clearwater.md` Part 2.

| Item | Value |
|---|---|
| Brief | `docs/briefs/wp0.2-brief.md` (FINAL at `b0287a2`; CHARC rulings `74d4f692348d2dbd`, `800be25ceb015347`) |
| Base SHA | `b0287a2` |
| Author head | `14e64f0` (branch `wp0.2`, implementer-sonnet-high, 140K depth at first return) |
| Merged head | `4863a90` (branch `wp0.2-mc` = `wp0.2` rebased onto main `e42b414`, which carries CHARC's harness fix `75c091a`; main fast-forwarded) |
| Byte identity | `git patch-id --stable` = `21dbe5cd24fbf8917868ec0b5b97ce18345d2de5` before (b0287a2..14e64f0) and after (main..4863a90) |
| Merge integration | Main's intervening commits: docs, state pointers, and `tests/harness/genericity_lists.py` (CHARC's registration of `docs/debt-register.md`); no file overlap with the arc; both gate surfaces ran on the merged head |
| Reviewer A | Codex fast tier (gpt-5.6-luna / medium), WSL, codex-cli 0.162.1. r1 BLOCKING (1 major: a symlinked/junctioned reports folder could route output into the footage folder; fixed), r2 NO_NEW_CRITICAL_MAJOR. Ledger `docs/proofs/wp0.2-ledger.md` |
| Reviewer B | Independent implementer-sonnet-high cell, brief `docs/briefs/wp0.2-review-brief.md`. Pass 1 on `a309046`: **NO_BLOCKING**, 4 minors (HEIC dimension swap without irot, error text losing its reason, photo-size label vs filter, non-atomic report write). Author cleanup `484b3f6` (no review round, per the fill's minor rule) plus CHARC's two text rulings. Pass 2 on `14e64f0`: **NO_BLOCKING**, all four RESOLVED by reproduction; the new ISOBMFF reader fuzzed (24,615 calls, 0 escapes, max 0.049 s/call); fresh Codex pass on the full arc diff (transcript md5 `0dd3fd8b944a2f54cb075e37dd11dd3d`) |
| Evidence | `C:\Users\rwsmy\clearwater-review-evidence\wp0.2\` — `r1`, `r2` (A), `B`, `B2` (B) |

## Gate checks (orchestrator seat, merged head `4863a90`, main tree)

```
uv run ruff check .            -> All checks passed!
uv run ruff format --check .   -> 32 files already formatted
uv run mypy                    -> Success: no issues found in 4 source files
uv run pytest -q -rs           -> 182 passed, 1 skipped in 6.00s
   SKIPPED [1] tests\test_inventory.py:1125: footage folder not configured; ...  (footage folder absent)
python -m unittest discover -s tests/harness -> Ran 366 tests ... OK (skipped=1)
```

- **Locks:** arc diff = `tools/inventory.py`, `tests/test_inventory.py`, `docs/proofs/wp0.2-ledger.md`,
  `pyproject.toml` (+2 dev-group lines: `pillow>=11,<13`, `pillow-heif>=0.20,<2`), `uv.lock` (adds only
  pillow 12.3.0 and pillow-heif 1.8.1). `tools/local_config.py` and `tools/environment_report.py`
  unchanged. One `subprocess.run`, no shell, 60 s timeout. New imports are stdlib. No mypy override needed.
- **B2 transcript assertions (re-run here, `grep -a`):** banner `gpt-5.6-luna` / `medium`; `^ERROR` 0;
  `ERROR codex_core` 1 = a reviewer command that failed on a mistyped path (provenance: the reviewer's
  own exec, not transport); `^tokens used` 1; `^ succeeded in` 3; anchored `VERDICT: BLOCKING` on one
  Codex major, adjudicated by B and REJECTED on a scope citation (below).
- **Witness (orchestrator reality check):** on the merge candidate, a synthetic tree (two-chapter GoPro
  recording `GX010007`/`GX020007` with a `GL010007.LRV`, a truncated `GX010008.MP4`, a stray text file)
  gave: 3 video rows, 1 probe-error row whose reason survives ("moov atom not found GX010008.MP4"),
  1 ignored, 1 sidecar, mode `320x240 @ 30 h264 8-bit 4:2:0: 2`, "recording 0007: chapters 1, 2",
  LRV 1 of 3, the stored-dimensions header line, CSV header in the brief's order with a BOM, and a
  before/after snapshot of the footage tree unchanged. (The photo leg of this witness did not run:
  the test image was not created because of a temp-path slip at this seat. Photos are covered by
  B's two passes.)
- **Real footage run:** NOT done. `C:\Users\rwsmy\clearwater-footage` did not exist at the accept.
  GoPro naming is therefore confirmed only against the brief's patterns.

## Dispositions

| Item | Disposition |
|---|---|
| Real inventory run and real GoPro naming check | COMMISSION-READY — run `uv run python tools/inventory.py` once the footage download lands (a mechanical pass; no new code); feeds CP1. Any uncovered naming pattern is a follow-on fix. |
| Codex B2 major: a truncated JPEG/HEIC with an intact header reports success | BANKED — owner CHARC; out of scope by the brief ("any correction or decoding of pixels"). Trigger: an inventory run while the download is incomplete. `size_bytes` is in every row. |
| HEIC `orientation` column is the EXIF value, not derived from irot | BANKED — owner CHARC; iPhone HEICs carry both, so in-envelope files agree. Trigger: a non-Apple HEIC in the footage. |
| B2 minor: an ISOBMFF top-level box of size 0 before `meta` -> "HEIF rotation unreadable" note, dimensions as decoded | BANKED — owner CHARC; graceful, rare (real HEICs put meta before mdat). |
| B2 minor: a file vanishing after stat becomes an error row, not a "skipped" count | DECLINED — failure isolation holds and the reason is in the row; wording only. |
| Codex B2: race between the reports-folder check and the writes | DECLINED — concurrent-adversary case, out of envelope. |
| Footage skip reason on main says "not configured" while the config exists and the folder is absent | BANKED — owner CHARC; the message lives in WP0.1's `tests/conftest.py`; cosmetic. |
| CSV cells are not neutralised against formula injection from hostile file names | BANKED (out of envelope) — owner CHARC; the owner's own camera files. |
| mkstemp gives 0600 report files on POSIX | Noted — irrelevant on the Windows target. |
| Additive deviations (`scan_tree`/`ScanResult`, keyword-only args on `write_inventory`, `GS` names, reports-folder link refusal, extra summary sections) | Accepted by CHARC (`800be25ceb015347`); checked against the brief by B. |
