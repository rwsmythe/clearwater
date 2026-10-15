# WP1.5 — Container spike (dispatch brief, FINAL)

**Status:** FINAL, issued by the orchestrator 2026-10-15 from CHARC's draft (a0c1a96) on CHARC's
commission `9ea69283f746b163`. Spec **v0.5.1**. Dispatched only AFTER WP1.2 Part A is closed:
neither its exclusive bench window nor its Reviewer B window may overlap this package's NVENC
runs. Cell: `implementer-opus-high` (metadata forensics and an approach recommendation are
reasoning-dense). Worktree `.worktrees/wp1.5`, branch `wp1.5`, base = the main commit named in
the dispatch (it carries this file). Needs
footage: the four GoPro chapters present in `C:\Users\rwsmy\clearwater-footage\` on 2026-10-15
(`GX011625.MP4` 406 MB, `GX011626.MP4` 1390 MB, `GX011627.MP4` 151 MB, `GX011628.MP4` 17 MB; all
shallow snorkel; no `.LRV`/`.THM` sidecars present). The footage folder is READ-ONLY: never
write, rename or delete there; every output goes to `work/wp1.5/`.

| Field | Content |
|---|---|
| ID and title | WP1.5 — Container spike (D104) |
| Goal | Re-encode one real GoPro chapter with no correction through the simplest FFmpeg-tooling approach, compare source and output on every item spec 8.2 and 7.5 name, classify each difference as mandatory or best-effort (D105), record what the camera writes (D54), confirm NVENC and 10-bit encode and hardware decode in the installed build (D74), test `.LRV` alignment if proxies exist, and recommend one of the three approaches (simple, encode-then-repair, transplant) with evidence. Result 6 of the prototype gate. |
| Spec clauses | D104 (the spike); D105 and 7.5 (mandatory: per-frame timestamps, start offset, edit list, audio sync, display orientation; best-effort: creation time, GPMF, timecode, camera atoms); D94, D95 (timing preserved, VFR); D54, D55 and 6.5 (colour tags read and matched; BT.709 limited assumed and warned when absent); D114 and 8.2 (chroma subsampling and pixel format match the source; HEVC MP4; 10-bit when the source is); D74 (encoder capability detection); D60 (`.LRV` only if alignment verified); D73 (GoPro "HDR video" transfer tag; GP-Log marker, best-effort); D83 (sidecars excluded from grouping); 8.3 naming for the output name. Plan section 6 WP1.5; section 8.3 candidate row "Video decode, encode, mux"; section 9 Gate 6 rows. |
| Depends on | WP0.2 (merged; `tools/inventory.py` has an ffprobe wrapper and an ISOBMFF box walker the cell MAY import if the interface suits, else its own). Not on CP1. |
| Files owned | `tools/container_spike/__init__.py`, `tools/container_spike/compare.py` (the source-versus-output comparison instrument), `tools/container_spike/spike.py` (the re-encode runner), `tests/test_container_spike.py`, `docs/reports/wp1.5-container-spike.md`, `docs/proofs/wp1.5-ledger.md`. NO `pyproject.toml` change: FFmpeg 9.0.2 (Gyan full build, installed by WP0.1) is the only tool; PyAV is NOT granted (see decisions). |
| Interfaces consumed | `ffmpeg`, `ffprobe` on PATH (the WP0.1 install); optionally `tools/inventory.py` functions by import; `tools/local_config.py` for the two folders. |
| Interfaces provided | None frozen. `compare.py` is an instrument WP3.10's tests will reuse in spirit; its JSON record shape is documented in the report. |
| Dependencies | None new. The product's choice between PyAV and FFmpeg-as-a-process is made by CHARC at WP2.1 from this report; the cell does not install PyAV. |
| Tests | `tests/test_container_spike.py`: on a SYNTHETIC clip the test builds with `ffmpeg -f lavfi` (short, with an audio track, a non-zero start offset and an edit list where ffmpeg can produce one); skipped when `ffmpeg`/`ffprobe` are not on PATH (the WP0.2 skip pattern). The real-footage runs are NOT tests; they are the spike, run once by the cell, recorded in the report with the JSON paths. One `footage`-marked smoke test that `compare.py` runs on the smallest real chapter when the folder exists. |
| Hardware flags | `footage`, `gpu` (NVENC). Not timing-exclusive: no timing figure is a result here; elapsed times may appear informally. MUST NOT run while WP1.2 Part A's bench or Reviewer B window is open (the orchestrator sequences). |
| Out of scope | Any colour correction (the re-encode is identity); the product's video I/O module (WP3.10); quality-level mapping beyond recording which encoder settings the spike used (D75 is WP2.1's); timing or memory results (WP1.2); chapter concatenation (D83 grouping is WP3.8); anything under `src/clearwater/`. |
| Done | Plan section 4.5; the four gates and the harness gate green on the final head (the `footage` test RUN at the gate on this machine); the report complete with the comparison table per chapter, the classification, the camera's tag record, the capability record, and ONE recommendation with its evidence. |

## What the spike does (claims)

1. **Capability record (D74).** From the installed build: `ffmpeg -encoders` and `-hwaccels`
   filtered to HEVC (`hevc_nvenc`, `libx265`), AV1 and the CUDA/D3D11VA/DXVA2 decoders; then a
   PROOF per claim, not the listing alone: a 2-second synthetic encode with `hevc_nvenc` at
   `p010le` (10-bit) and at `yuv420p` (8-bit) that ffprobe confirms; a hardware decode of one
   real chapter (`-hwaccel cuda`) that completes; the GPU in use named by `nvidia-smi` during
   the encode. Each proof's command and ffprobe output in the report.
2. **Camera record (D54, D73).** For all four chapters: codec, profile, pixel format, bit
   depth, colour primaries / transfer / matrix / range as written (or absent), frame rate and
   whether it is constant (ffprobe `-show_frames` timestamp deltas), start offset (first pts
   and `start_time`), edit list (`elst` from the box walker), rotation / display matrix, audio
   codec and layout, data streams (GPMF `gpmd`, timecode `tmcd`), creation time, and the
   `udta` / `firm` / `lens` style camera atoms present. Note any HLG/PQ transfer tag or any
   marker that looks like GP-Log (none expected on these shallow snorkel clips; say so).
3. **The simple re-encode (D104).** On `GX011627.MP4` (151 MB, the primary chapter) and
   `GX011628.MP4` (17 MB, the fast check): decode -> encode with `hevc_nvenc` at the source's
   bit depth and pixel format, colour tags set to match the source (D55), audio `-c:a copy`,
   data streams copied where ffmpeg can (`-map 0 -c:d copy` or the nearest that works),
   `-map_metadata 0`, timestamps carried through (`-vsync passthrough` / `-fps_mode
   passthrough`, `-copyts` where needed), output named per spec 8.3 (`GX011627_corrected.MP4`)
   into `work/wp1.5/`. Record the exact command line. If NVENC fails a proof in claim 1, use
   `libx265` for the re-encode and say so; the NVENC failure is itself a result.
4. **The comparison (D105).** `compare.py <source> <output>` writes a JSON record and a
   markdown table with, per item: source value, output value, SAME / DIFFERENT, and the class
   (MANDATORY per D105: per-frame pts sequence including VFR gaps, start offset, edit list,
   audio stream present and in sync (pts of first audio sample relative to first video frame),
   display orientation; BEST-EFFORT: creation time, GPMF track, timecode track, camera atoms,
   other tags). Frame count and duration are checked too. The per-frame pts comparison is
   exact on the full sequence, not sampled.
5. **`.LRV` alignment (D60).** No `.LRV` files are present on 2026-10-15. If any arrive
   before the cell starts, compare frame count, timestamps and a per-frame luma correlation at
   matching indices for one pair and state whether alignment is exact. If none, record "no
   proxies in the footage; D60 remains open; Part B of WP1.2 and WP2.1 carry it".
6. **The recommendation.** ONE of: simple (claim 3 leaves every MANDATORY item SAME),
   encode-then-repair (a named MANDATORY gap that a second pass over the output container can
   close: say which tool step and show it closing on the real file), or transplant (a gap that
   repair cannot close: show the attempt). Evidence is the claim-4 table. Gate 6's owner is the
   architect; the cell recommends, CHARC rules at WP1.6.
7. Docstrings complete; ruff, ruff format, mypy strict and pytest green (the `footage` test
   run, not skipped); harness gate green; no `pyproject.toml` change.

## Decisions fixed at issue (CHARC)

- **Tooling: FFmpeg as a process, nothing else.** The plan's candidate row names PyAV and
  FFmpeg-as-a-process. The spike runs on the installed FFmpeg only: it already has NVENC, 10-bit
  and the hardware decoders, so the D104 questions are answerable without a new dependency, and
  PyAV's prebuilt wheels carry their own FFmpeg without NVENC, which would answer a different
  question. The product choice is CHARC's at WP2.1 from this report; the report's last section
  states what the simple approach needed from the tool (frame access for correction is NOT
  exercised here; say so plainly) so that choice is informed.
- **Identity re-encode, not a copy.** `-c:v copy` would prove nothing about the encode path.
  The video stream IS re-encoded (decode -> encode) at matched settings; everything else is
  copied. That is the path WP3.10 will take with the correction inserted.
- **Approach order.** Simple first on the primary chapter. Encode-then-repair is attempted
  ONLY on a MANDATORY difference, on the real output, with the repair step named. Transplant
  (moving the encoded stream into a copy of the source container) is attempted ONLY if repair
  fails. Do not attempt all three for completeness.
- **Which chapters.** Primary `GX011627.MP4`; fast check `GX011628.MP4`; camera record on all
  four; nothing on `GX011626.MP4` (1.4 GB) beyond the camera record unless a finding needs it.
- **Outputs.** `work/wp1.5/` (the working folder, gitignored): re-encoded files, ffprobe
  dumps, JSON comparison records. The report cites paths; nothing large is committed.
- **Spec reading.** Sections 6.5, 7.5, 8.2, 8.3; the D-rows named above; plan section 6 WP1.5
  and section 9 Gate 6. Nothing else unless cited there.
- **ffmpeg invocation.** Always `-nostdin -hide_banner -y` only INSIDE `work/wp1.5/` (never a
  flag that could write elsewhere); the source path is an input only. The cell asserts before
  each run that the output path is under the working folder.

## Decisions fixed at issue (orchestrator)

- **Local configuration in the worktree.** `tools/local_config.py` reads
  `<repo root>/clearwater.local.toml`, which is uncommitted and exists only in the main tree.
  - The orchestrator copies it into the worktree root at creation. It is gitignored, so it
    cannot be committed.
  - Its paths are absolute: footage `C:\Users\rwsmy\clearwater-footage`, working
    `C:\Users\rwsmy\clearwater\work`.
  - So the `footage` test RUNS in the worktree, and `work/wp1.5/` above means the MAIN tree's
    `C:\Users\rwsmy\clearwater\work\wp1.5\`.
  - Never edit or commit that file.
- **FFmpeg on PATH.** The WinGet links folder is not on the agents' default Bash PATH. Prepend
  `/c/Users/rwsmy/AppData/Local/Microsoft/WinGet/Links` for every ffmpeg, ffprobe and pytest
  run. Without it, the module skip hides the tests, and a skip at the gate fails claim 7.
- **Output-path assertion.** Before each ffmpeg run, `spike.py` asserts two things about the
  resolved output path (links resolved; the same refusal pattern as WP0.2's reports-folder
  check):
  - it is inside the configured working folder's `wp1.5` directory;
  - it is NOT inside the footage folder.
- **Spec version.** Read spec **v0.5.1** (`docs/underwater-correction-spec.md` on main).

## Test roster (`tests/test_container_spike.py`)

- Skip module when `ffmpeg`/`ffprobe` are absent.
- Synthetic clip builder: 2 s `testsrc2` + `sine`, 30 fps, yuv420p, H.264 or HEVC (software),
  with `-output_ts_offset 0.5` or a set `start_time`; the comparison of the clip with itself
  reports every item SAME.
- A re-encoded synthetic (software encoder) through `spike.py` reports frame count, duration
  and audio presence SAME; per-frame pts SAME; any DIFFERENT item is in the BEST-EFFORT class
  (this is the roster's floor; the real chapters may show more).
- `compare.py` on a clip with a deliberately changed start offset reports that item
  DIFFERENT and MANDATORY.
- The capability record function returns the documented keys and marks an encoder absent
  without raising when the listing lacks it (monkeypatched listing).
- (`footage`) `compare.py` on `GX011628.MP4` against itself runs and reports all SAME.

## Declared operating envelope

Windows 11, the installed FFmpeg 9.0.2 full build, GoPro HEVC/H.264 MP4 chapters as present,
one chapter at a time. iPhone video, HDR (HLG/PQ) sources, GP-Log, chapter concatenation, and
any correction are out of envelope; report them as not exercised.

## Review loop (Reviewer A) -- per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG** (this result selects the product's video I/O approach).
  - **Transport and flags:** WSL, pinned to codex-cli 0.162.1. Per-call flags, never `-p`:
    `-m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check`. Banner
    assertion: `gpt-5.6-sol` / `high`.
  - **Diff:** generated Windows-side with
    `git -C <worktree> diff -U8 <base>..HEAD -- . ':!uv.lock' ':!docs/proofs'` into a scratch
    file; WSL never runs git.
  - **Invocation**, with cwd the worktree:
    `wsl.exe bash -ilc 'export PATH="$HOME/.local/node22/bin:$PATH"; cd /mnt/c/Users/rwsmy/clearwater/.worktrees/wp1.5 && cat <prompt> <diff> | codex exec -m gpt-5.6-sol -c model_reasoning_effort=high -s read-only --skip-git-repo-check - > <transcript> 2>&1'`
  - **Probe:** one probe through this exact invocation before round 1, expecting one
    `^ succeeded in` line.
  - **Prompt:**
    - the claim list;
    - the envelope, with a request to TAG out-of-envelope findings;
    - `CORRECTNESS REVIEW` / `WHAT TO EXAMINE` framing;
    - "report every finding with a severity tag";
    - the read-only-sandbox EXECUTED/REASONED paragraph verbatim from `docs/codex-reviewer.md`;
    - its own paragraph: "Do NOT read `docs/proofs/` or anything under
      `clearwater-review-evidence`".

    Include the report in the diff. Never point Codex at the footage folder.
  - **Per-round assertions** (all with `grep -a`):
    - the banner;
    - `^ERROR` and `ERROR codex_core` lines, each classified by provenance;
    - the `^tokens used` footer;
    - an anchored VERDICT line;
    - at least one `^ succeeded in` line;
    - `grep -a -n 'docs/proofs\|wp1.5-ledger'`, with each hit classified as an echo or an
      access.
  - **Convergence:** zero NEW in-envelope blocking findings. Minors are fixed once in that
    round's cleanup. FIVE_ROUND_GATE: at round 5, yield with the ledger.
  - **Evidence and ledger:** evidence in `C:/Users/rwsmy/clearwater-review-evidence/wp1.5/rN/`;
    ledger `docs/proofs/wp1.5-ledger.md`, with the depth column left to the dispatcher. Delete
    `.codex-*` staging files at teardown. WHAT TO EXAMINE: whether the comparison is
  complete against D105's list and exact on timestamps; whether the capability proofs are
  proofs (an ffprobe-confirmed output) rather than listings; whether the recommendation
  follows from the table; whether any ffmpeg flag could write outside the working folder.
- Reviewer B: ORDERED (orchestrator, per the fill). An independent implementer-opus-high cell
  runs after your return:
  - re-runs `compare.py` on your output files and confirms the table reproduces;
  - re-runs the NVENC 10-bit proof;
  - reviews the recommendation against the table;
  - runs its own Codex pass.

## Notes for the cell

- Return report = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4: per-commit change list; validation lines; verification-loop record; review
  rounds, ledger and evidence paths; locks honored; the comparison table for the primary
  chapter; the capability record; the recommendation with its one-paragraph justification;
  deviations and open questions.
- STOP for: a mandatory item whose comparison you cannot make exact (say what ffprobe will
  not show); a real chapter ffmpeg cannot decode; any need to write outside `work/wp1.5/`;
  a dependency beyond the installed FFmpeg. Do not stop for a best-effort item lost: record it.
- **Working rules:**
  - Run `uv sync` in the worktree.
  - Commit by pathspec with a conventional message (`feat(wp1.5): ...`) and the
    `Co-Authored-By:` footer.
  - Never use a bare `cd`.
  - Never post to a mailbox.
  - The footage folder is input-only.
- The owner's note for context: these four clips are shallow snorkel; deeper (~20 m) scuba
  clips and shallow still photos arrive later. The spike's result does not depend on depth.
