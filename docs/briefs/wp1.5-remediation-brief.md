# WP1.5 — Remediation brief (Reviewer B round 1)

**Issued by the orchestrator 2026-10-15.** This is the ONE bounded remediation that
`docs/review-gate-clearwater.md` Part 2 item 2 allows after a blocking Reviewer B.

The original author cell is past its context cap, so a fresh cell carries the author's loop
forward on the same branch. Read these first:
- the package brief, `docs/briefs/wp1.5-brief.md` (FINAL);
- the spec, `docs/underwater-correction-spec.md` v0.5.1: 6.5, 7.5, 8.2, 8.3, 8.4, D54, D55,
  D74, D85, D105, D114.

| Field | Content |
|---|---|
| Worktree | `C:\Users\rwsmy\clearwater\.worktrees\wp1.5`, branch `wp1.5`, head `82e5cfc`. It holds a copied `clearwater.local.toml` (gitignored; never edit or commit it). |
| Files owned | The same six as the brief: `tools/container_spike/{__init__,compare,spike}.py`, `tests/test_container_spike.py`, `docs/reports/wp1.5-container-spike.md`, `docs/proofs/wp1.5-ledger.md`. No other file; no `pyproject.toml` change. |
| Outputs | `C:\Users\rwsmy\clearwater\work\wp1.5\` only. The footage folder `C:\Users\rwsmy\clearwater-footage\` is READ-ONLY input. |
| PATH | Prepend `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for every ffmpeg, ffprobe and pytest run. |

## Rulings in force (CHARC; do not re-open)

1. **Edit list.**
   - MANDATORY: the video track's edit list matches AS WRITTEN.
   - MANDATORY: the presentation effect matches on the video and audio tracks.
   - BEST-EFFORT: identity edits the muxer adds to audio and data tracks.
   - Out of envelope: the B-frame case (DR-15).
2. **REQUIRED (D55/D114).** This class weighs as MANDATORY for the recommendation;
   `mandatory_and_required_all_same` is the test.
3. **D54.** A full-range tag is read and matched.
4. **`udta` atoms.** BEST-EFFORT, banked.

## Findings to close

The gate seat (orchestrator) has adjudicated every finding below. Reviewer B evidence:
`C:\Users\rwsmy\clearwater-review-evidence\wp1.5\reviewB\review-B.txt`. You may read it.

| # | Reviewer B finding | Disposition: what to do |
|---|---|---|
| B1 | CRITICAL (reasoned): containment bypass by an NTFS hard link at a record or output path, or by a race that swaps a checked parent for a junction. | **Partly fix.** Refuse to write when the target already exists with a link count above 1 (`os.stat(path).st_nlink > 1`). Apply this in the same checks that already refuse symbolic links (`check_output_path`, `write_checked`, and before `-y`). Add a test: a hard link in the spike folder pointing to a file outside it is refused and the outside file is unchanged. **Races are NOT fixed here:** they need a concurrent process acting mid-run, which is outside the threat model. Banked for the product's safe writing (8.4, D85). State this in the report. |
| B2 | MAJOR: the test helper `_ffmpeg()` does not pass `tool_env()`, so an inherited `FFREPORT` writes a report while fixtures build. The FFREPORT test sets the variable only after its fixture is built. | **Fix.** Every ffmpeg and ffprobe call in the tests goes through `tool_env()`. Add a test where `FFREPORT` is set BEFORE a clip is built, with nothing written. **Rejected part:** `__pycache__` and `.pytest_cache` are Python's and pytest's, not files the spike writes. Reword the report's safety sentence to its true scope: "every file the spike's FFmpeg runs and record writers produce". |
| B3 | MAJOR (executed): an H.264 output with otherwise identical items gets `mandatory_and_required_all_same: true`. Codec and container are informational only. | **Fix.** Add REQUIRED (D55/D114) items for 8.2's output format: video codec HEVC, and container MP4/ISO BMFF. Compare them as output requirements, or source-against-output where that is meaningful; choose and document. Add a test: an H.264 output reports REQUIRED DIFFERENT and the summary is false. |
| B4 | MAJOR: 8.3 collision numbering is absent; a re-run overwrites `GX0116xx_corrected.MP4`. | **Not a defect of the spike.** The brief claims the 8.3 base name only, and the item-5 re-run overwrote on purpose. Collision suffixes (8.3) and safe writing (8.4) belong to the product's naming and writing work. **Report only:** state that the spike applies 8.3's base name, does not implement collision suffixes or 8.4 safe writing, and that a re-run replaces the spike's own outputs in `work\wp1.5\`. |
| B5 | MAJOR, OUT of envelope: an untagged source gets no colour options and no warning (D54 fallback). | **No code.** Check that the report's section 9 states plainly that the spike passes no colour options for an untagged source, so D54's BT.709-limited fallback with a warning is NOT implemented here. Name it as a WP3.10 point. CHARC banks it. |
| B6 | MINOR (executed): "container start" is described as the exact ffprobe container `start_time`, but the item uses the minimum stream start and ignores `format.start_time`. | **Fix.** Either add `format.start_time` as its own MANDATORY item, compared exactly as ffprobe prints it, or correct the note and the report to say what is compared. Prefer adding the item. |
| B7 | MINOR: the proof criteria omit width and height; a leftover encoder-utilisation reading can satisfy "NVENC activity" with zero sessions sampled. | **Fix.** (a) Add width and height to the proof criterion. (b) The gating GPU evidence for an NVENC proof is the brief's: the GPU named by nvidia-smi DURING the encode, plus the ffprobe reading, including the output's encoder tag naming `hevc_nvenc`. Record the session count and encoder utilisation as SUPPORTING evidence only, not gating. Keep the 4K proof clip. Update the tests and the report's criterion text. Re-run `spike.py capability`. |
| B8 | MINOR: report statements not backed by the cited records. | **Fix each.** For every number or claim, either cite a file under `work\wp1.5\` that holds it, or mark it informal, or remove it. The claims are: driver 610.62, wall-clock times, "16 of 16", the earlier failed and same-reading capability runs, the byte-identical regeneration, and the 120-frame alignment figures. Also: **(a)** SAR for all four chapters: add SAR to the camera record and re-run `camera`, or drop the claim. **(b)** "type, size and MD5" for `udta` in the camera record: match the wording to what `camera.json` holds. **(c)** "every timing value is an exact Fraction": it conflicts with the microsecond `format.duration` item; reword. |
| B9 | ADVISORY, out of envelope: `ctts` version 0 read signed. | No action; it was already declined with a reason in round 1. |
| B10 | ADVISORY, out of envelope: "audio streams present" is SAME when both files lack audio. | Optional: rename the item, or add a note that it tests preservation. No test needed. |

## Then

1. **Records.**
   - Re-run `spike.py capability` (for B7).
   - Re-run `camera` if you add SAR (B8a).
   - Re-run `spike.py reencode` on GX011627 and GX011628 so the run and compare records carry the
     new items (B3, B6).
   - Update the report's tables and summaries from the new records.
2. **Gates.**
   - Run `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy`,
     `uv run pytest -q -rs` (the WP1.5 footage test and both NVENC gpu tests RUN),
     `uv run pytest -q -m gpu` and `uv run python -m unittest discover -s tests/harness`.
   - The WP0.2 `test_real_footage_has_one_row_per_media_file` fails while a `.crswap` file in
     `SCUBA` grows. If it fails, record the differing file and do not fix it.
3. **ONE Reviewer A round** on the delta `82e5cfc..HEAD`, per the brief's "Review loop" section.
   - Tier STRONG; WSL; codex-cli 0.162.1.
   - Per-call flags `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`.
   - The diff is generated Windows-side, excluding `uv.lock` and `docs/proofs`.
   - In the prompt: the withheld paths named (`docs/proofs/`, `clearwater-review-evidence`),
     "never read or list the footage folder", and the EXECUTED/REASONED paragraph verbatim from
     `docs/codex-reviewer.md`.
   - The six assertions, including `grep -a -n 'docs/proofs\|wp1.5-ledger'` with every hit
     classified.
   - Fix minors once. Append round 4 to the ledger; evidence to
     `C:\Users\rwsmy\clearwater-review-evidence\wp1.5\r4\` with md5s.
   - A new critical or major found in this round is FIXED if it is introduced by this
     remediation; otherwise report it.
4. **Commit** by pathspec with conventional messages (`fix(wp1.5): ...`, `docs(wp1.5): ...`) and
   the footer `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## STOP for

- any MANDATORY or REQUIRED item DIFFERENT on a real chapter;
- any need to write outside `work\wp1.5\`;
- any dependency change.

## Return (your FINAL message, under about 60 lines)

- the new head and a per-commit list;
- each of B1-B10 with what was done and the test that covers it;
- the new items' results on both chapters, and `mandatory_and_required_all_same`;
- the gate lines;
- round 4's result with its assertions;
- the locks.

**Working rules:** never use a bare `cd`; never post to a mailbox.
