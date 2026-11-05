# WP6.4 macOS adaptation: completion report

**Package:** WP6.4 (brief `docs/briefs/wp6.4-brief.md`, FINAL, with its round-0, group-A and
group-B yield rulings).

**Cells:**
- `wp64-cell1` ran round 0.
- `wp64-cell2` built group A, the product (through `283b9d78`; ledger `451799f5`).
- `wp64-cell3` built group B: the tools, the remaining W rows and the M rows (`8b3f62e8`, with
  CHARC's export grant `1a003fe4`). Its file tool refused this report (S-B2); its return carried
  the text.
- `wp64-cell4` ran the A r1 fold-in turn: the W-FS[P30] pair, this report and the ledger's turn-4
  section; then, on CHARC's turn-4 STOP ruling (`a5ca96e5`), S-B1 (the environment facts on by
  default) and the M-TOOL monkeypatch fix (section 10).
- `wp64-cell5` ran the Reviewer A r2 fold-in (turn 5): the footage guard's symlink-then-`..`
  fix and the folded M and W instruments (section 1, "Turn 5").
- `wp64-cell6` ran the Reviewer A r3 fold-in (turn 6): four test-only folds in the W helper
  instruments (section 1, "Turn 6").
- `wp64-cell7` ran the Reviewer B fold-in (turn 7): the queue's current-identity comparison, the
  preset fallback's recheck, the darwin-safe environment tests, the explicit APFS images, two W
  mutant controls and the user guide's upgrade notice (section 1, "Turn 7").

The ledger is `docs/proofs/wp6.4-ledger.md`, branch `wp6.4`. **No Mac was run.** Every M test is
written to run natively and is UNEXECUTED until WP6.5. The counts below are the turn-7 cell's own
runs at `61aacbc0`. Reviewer A (Codex) r2 on group B returned NEW_CRITICAL_MAJOR_FOUND and was
folded in turn 5; Reviewer A r3 (the delta on turns 4 + 5) returned NO_NEW_CRITICAL_MAJOR (2 MINOR,
2 ADVISORY), folded in turn 6. Reviewer B (Codex, on `d55573f1`) returned NEW_CRITICAL_MAJOR_FOUND
(3 MAJOR, 3 MINOR, 2 ADVISORY), folded in turn 7 as CHARC ruled (the brief's "Reviewer B
rulings"). A Codex delta on turns 6 + 7 and the package gate follow.

## 1. What was built

### Group A: the product (design items 1-10 and 12)

The per-item build cycles are recorded in ledger A.1.

- **The encoder roster per platform (item 1).**
  - darwin: `hevc_videotoolbox`, then `libx265`.
  - Every other platform: `hevc_nvenc`, then `libx265` (CHARC's ruling).
  - VT test encodes run at 8 and 10 bit with `-allow_sw 0`. A failed 10-bit trial disables 10-bit
    only.
  - The NVENC markers stay scoped to NVENC. VT has its own ASCII-safe reason.
  - A saved known encoder outside the roster is kept and shown as unavailable with its reason (D26).
- **The VT command branch (item 2).**
  - It sits behind `VT_RATE_CONTROL` (default `"B"`) and carries `-allow_sw 0`.
  - The shared `rate_ceiling` exposes `nvenc_rate`'s numeric R. `nvenc_rate` itself is unchanged,
    as the snapshots prove.
  - The geometry refusal now applies to VT as to NVENC.
- **`pipes.py` (item 3).** It uses the AD-36 statement form and AD-37's `start_new_session` (True
  off win32, an explicit False on win32). The default-pipe fallback logs at INFO off Windows.
- **The Library paths in `config/paths.py` (item 4).** See section 8.
- **User-facing text (item 7).**
  - The darwin AD-9 reason is "CPU: graphics-card processing is not available on macOS". Force CPU
    still gives "CPU: forced".
  - AUTO_TEXT is "Automatic (the hardware encoder when available)", with a tooltip that names the
    roster's hardware encoder.
  - The missing-tool text is platform-neutral (P16).
- **Filesystem identity and names.**
  - DR-121: the queue identity is `(st_dev, st_ino)`, with the lexical fallback (P29); labels are
    unchanged (D5). Since turn 7 (Reviewer B 1) every queued path's identity is read again at each
    add, and the lexical key is a second key: an identity is never cached past its file.
  - P70: the output-name refusal names the character and the stem.
  - P71: the wheel accumulates to 120 units per step. This is the fix of a pre-existing Windows
    defect: the old `wheelEvent` zoomed a full step on any non-zero delta, so a precision touchpad
    over-zoomed (section 10).
  - P73: the preset rename does not replace another preset (case-only rename, link then unlink,
    and the EPERM / EXDEV / ENOTSUP / EMLINK fallback with one WARNING), with D1's accepted
    fallback limit: on a volume that makes no hard link the fallback rechecks that the target is
    absent (turn 7, Reviewer B 4) and then uses POSIX `os.rename`, which replaces a file another
    writer creates between that check and the rename (the residual race, DR-34(a)).
- **The P55 docstrings in `interfaces/settings.py`.**
- **The CPU-only dependency expression and the `macos` marker (item 12).**

### Group B: the tools, the tests and the static step

- **Item 5, tools part.** These functions are now in the AD-36 statement form:
  - `tools/prototype/bench.py`: `_windows_power`, `_cpu_brand` and `_platform_name`. `:1467` was
    converted with `:1479`, and its stale comment corrected (D4 (d)).
  - `tools/spike_io/transport.py`: `idle_gate`.

  `mypy --platform darwin` is clean on the full `files` set.
- **Item 6: NEW `tools/footage_guard.py` `is_inside(path, root)` (DR-122).**
  - It first runs the old text check on the lexical and the resolved spellings, so nothing the old
    tools refused is accepted now.
  - It then splits each path into its nearest EXISTING ancestor and the lexical tail of names that
    do not exist yet. The path is inside when the root's existing ancestor is, by identity
    (`os.path.samestat`), the path's existing ancestor or one of that ancestor's own ancestors, and
    the remaining names begin with the root's tail (`normcase`-d).
  - A file system with no file numbers (`st_ino == 0`) falls back to text.
  - The seams `_stat`, `_normcase` and `_realpath` look their functions up at call time, so the
    existing alias tests' monkeypatches still reach them.
  - It is used at five sites, located by name at the base:
    - `inventory.main` (the old `_resolved` is removed);
    - `lookcheck/frames.check_output_path` (the footage check; the output-folder check is
      unchanged);
    - `container_spike/compare.check_output_path` (likewise);
    - `analysis_breakdown.refuse_inside`;
    - `export_oracle.refuse_inside`.
  - `halo_probe._cache_conflict` is noted only: it already uses `headless_export.inside`.
- **The ruled tool edits.**
  - D4 (a): the module-docstring label "Windows / NVIDIA evidence; not a Mac instrument", with its
    row and reason, on eight modules: `video_io_bench` (T13, T37), `reviewpack/build` (T33),
    `prototype/clip` (T34), `container_spike/spike` (T35), `video_fidelity` (T36), `export_bench`
    (T38), `core_speed` (T39) and `device_hold` (T42). The edit script asserted that each module's
    AST is otherwise equal.
  - D4 (b): `export_oracle.record_name` refuses `:` and a backslash on every platform (T52), and
    `tests/test_export_oracle.py` loses its POSIX skip (X46).
  - D4 (c): `inventory --exclude` casefolds both sides on every platform (T16).
  - Item 13: the inventory counts AppleDouble `._` names on their own summary line, "AppleDouble
    files (._ names, macOS metadata; not rows)", and never probes or lists them (T14).
  - Item 13: on darwin, `environment_report`'s NVIDIA fields are null with "not applicable on this
    platform", and `nvidia-smi` is not run there. The default report also holds the machine, the
    process architecture, the correction backend and its reason, and the roster's capability rows
    from the product's trial model (T01, T02), as its last keys before `unavailable`. Group B
    built these behind an opt-in `--platform-facts` flag (STOP S-B1: an unowned test pinned the
    key set); turn 4 made them the default and removed the flag and the `platform_facts`
    parameter (CHARC's S-B1 grant and turn-4 ruling; section 1, "Turn 4").
- **The export grant (CHARC, `63ff45f3`; commit `1a003fe4`).** In `jobs/export.py`, the video job's
  encoder check (the `capability is None or not capability.available` branch after
  `resolve_encoder`): a saved known encoder that the platform's capability report does not list
  now fails with "...is not available here: not offered on this platform". A listed but
  unavailable encoder keeps its own reason. The test is
  `test_portability_export_names_an_encoder_outside_the_roster`: it drives the
  `test_jobs_export_support.Rig` with `hevc_videotoolbox` (absent from the rig's report on every
  platform; red before the edit), with `hevc_nvenc` (listed as unavailable, keeps its reason) as
  the control. This closes open item 3 of ledger A.7.
- **Item 11: the tests.**
  - `tests/test_portability.py` has 180 cases, the W rows of the audit's section 8 (13 functions
    with `site` parameters), plus the snapshots, the per-character refusal, the slow real trials,
    the D3 parity test and the export-grant test.
  - NEW `tests/test_macos_portability.py` has 15 M functions and 178 cases.
  - The `macos` skip policy in `tests/conftest.py`: off darwin, every `macos` item also gets the
    skip "macOS native leg (WP6.5)".

### Turn 4: the A r1 fold-in

- **W-FS[P30] (A r1 ADVISORY).** `_fs_p30` gains the pair `Stra\u00dfe.MP4` (folder `a`) /
  `STRASSE.mp4` (folder `b`) and asserts the unchanged bare labels. The two names differ under
  `normcase` (`str.lower` on Windows, no fold elsewhere) and share only a casefold. An in-memory
  mutant of `batch_panel.item_labels` comparing by `casefold` instead of `normcase` now FAILS the
  case (it adds the parent folders); the unmutated code passes. The case count is unchanged (the
  pair is inside the existing case).
- **S-B1 (GRANTED; built after the turn-4 STOP ruling).**
  - `tools/environment_report.py`: the platform facts are ON BY DEFAULT; the `--platform-facts`
    flag and `collect`'s `platform_facts` parameter are removed. Writing a report now runs the
    product's encoder trials.
  - `tests/test_environment_report.py`, exactly two edits: the five keys appended to
    `EXPECTED_KEY_ORDER` before `unavailable` (existing keys keep their order), and one autouse
    fixture `stub_trial_seam` stubbing `_correction_backend` and `_encoder_rows`.
  - The callers: W-TOOL T01 (`test_portability.py`) reads the facts from the default `collect()`;
    M-TOOL (`test_macos_portability.py`) calls the default `collect()`.
  - No test on the Windows legs reaches the real trial seam: a session-start recorder over the
    three modules (both leg expressions) saw 0 unstubbed calls, where the stub-less simulation
    before the fixture saw 16 of `test_environment_report`'s 19 tests reach it.
- **M-TOOL monkeypatch fix (found in turn 4; CHARC's turn-4 ruling).** `test_macos_tool_reporting`
  ran its W case and its native half on one monkeypatch, so on a Mac the native half read the W
  stubs (encoders `['libx265']`; `sys.platform` left at `win32` after T02's W case) and would have
  failed. The W case now runs in its own `pytest.MonkeyPatch.context()`; a replay shows the stubs
  live inside it and every original restored after it. Native T01 / T02 stay on `macos` only (no
  `slow`): a real VT / x265 trial is the native leg's point, and no case moves between legs.

### Turn 5: the Reviewer A r2 fold-in

Reviewer A r2 (Codex) on group B (`27505be4..107e6c77`) returned NEW_CRITICAL_MAJOR_FOUND: 6 MAJOR,
2 MINOR, 3 ADVISORY. CHARC ruled the fold (brief tail "Reviewer A r2 rulings"); `wp64-cell5` built
it. Commits: `36651814` (items 1-3), `f1175b92` (items 4, 5, 11 and item 6's M-V4), `a9dc9adb`
(items 6, 9, 10), `c5b2608a` (a docstring). The one product-side change is the tool
`tools/footage_guard.py` (item 1); everything else is test code.

Every mutant and probe below ran on Windows, in memory, with the native dependencies STUBBED
(no FFmpeg, ffprobe, encoder trial, `nvidia-smi` or `hdiutil` started). The scripts are
`work\wp6.4\t5_mutants.py` (pytest plugins) and `work\wp6.4\t5_probes.py` (the M functions called
directly, at this head and at the pre-fold head `51c50faf`).

| A r2 finding | Change | Test | Mutant or probe: result |
|---|---|---|---|
| 1 MAJOR: symlink then `..` (`footage_guard.py:55`) | `_absolute` resolves the ORIGINAL spelling (`_realpath(os.fspath(path))`): links first, then `..`; the lexical spelling stays a second candidate in `_texts` | The topology (`alias -> Footage/sub`, target `alias/../output`) through a POSIX `realpath` model (`posix_link_model`; Win32 collapses `..` before a junction, so it cannot be built natively here): in D3 parity (footage_guard and `headless_export.inside` both under the model, 5 paths), and in each caller's refusal (T17 inventory, T26 lookcheck, T27 container_spike, T28 analysis_breakdown, T29 export_oracle): refused, the tree (files AND folders) unchanged. M-FS[T17, T26-T29] repeats it with a real symlink | The old `_absolute` in memory: 6 of 6 FAIL (T17 at the tree check: inventory wrote `output/reports`; T26-T29 at the refusal; D3 at `is_inside`). Unmutated: 6 pass |
| 2 MAJOR: a shared monkeypatch | Every borrowed W case (M-PATH, M-DEVICE, M-TEXT, M-CODEC, M-FS, M-GUARD; M-TOOL since turn 4) runs in its own `pytest.MonkeyPatch.context()`, exited before the native half | NEW W pin `test_portability_macos_module_isolates_every_borrowed_case`: an AST check that each `_w().*_CASES[...]` is called directly with the name of an enclosing context that holds only that call and is used nowhere else; five planted leak forms | Replay with the native half replaced by a recorder: at `51c50faf` P45 runs under `ntpath.samefile`, P48 under `os.link`, X03 under `ntpath.samefile`; at this head none. The pin: this head `[]`; M-FS reverted in memory: 1 offender; `51c50faf`: 6 offenders (M-PATH, M-DEVICE, M-TEXT, M-CODEC, M-FS, M-GUARD; M-TOOL was fixed in turn 4); each planted form: 1 offender |
| 3 MINOR: M-PATH[P01] scratch | `tmp_path / "w"` created before the W case | M-PATH | Native child stubbed: `51c50faf` FileNotFoundError; this head PASS |
| 4 MAJOR: the `_clip` argv | `_lavfi` joins the geometry with `:` when the source has an option; `-display_rotation` moves to `_remux`, BEFORE its `-i` (as `tools/fixtures/video.py:844`) | M-TEXT[P72], M-RATE | Captured argv (no process): `-i color=c=0x204060:size=1280x720:rate=30000/1001:duration=2.0` (was `color=c=0x204060=size=...`); `-display_rotation 90 -i plain.mp4 -c copy rotated.mp4` (was `... -tag:v hvc1 -display_rotation 90 rotated.mp4`) |
| 5 MAJOR: unadvertised depths encoded | M-CODEC, M-RATE, M-SPACE and M-V4 encode only `bit_depths`; `assert_unadvertised_refused` checks each other depth is refused by the sink by name (`unavailable`, "N-bit"); x265 keeps (8, 10) | M-CODEC, M-RATE, M-SPACE, both M-V4 functions | VT `available=True, bit_depths=(8,)`, an encode stub enforcing it: M-RATE at `51c50faf` ERROR (asked for 10-bit), here PASS with 8-bit only; M-V4[P15] at `51c50faf` ERROR (encodes `(VT, 8), (VT, 10)`); the corpus case `(VT, 10)` here takes the refusal path, no encode |
| 6 MAJOR: weak M mechanics (the split as ruled) | M-PIPE: each frame byte-identical to the product's own decode command written to a FILE, pts_ticks equal to ffprobe's, pts exactly `i * 1001/30000` (`pipe_fidelity_failures`). M-FS: save and RENAME INTO each folding-corpus twin (U+0131, U+00DF / SS, NFC / NFD, case) refused on both APFS modes, the occupant's and the mover's bytes unchanged, a free name taking the mover's bytes. M-SPACE: candidates A and B x the advertised depths x the three qualities, each output within D87, the full set asserted. M-V4: NEW `test_macos_videotoolbox_v4_corpus`, 46 cases (below) | M-PIPE[P04, T07], M-FS[P40, P41, P49, P73], M-SPACE[P64], M-V4 corpus | M-PIPE: frame 7's pixels flipped and `pts_ticks = i*i`: `51c50faf` PASS, here FAIL. M-FS (real PresetStore on two NTFS folders): the product passes both heads; a rename mutant checking the exact file name only: `51c50faf` PASS, here FAIL (DID NOT RAISE). M-SPACE: one oversized output at (B, 10, high): `51c50faf` PASS (it encodes only (B, 8, *)), here FAIL (it encodes all 12). M-V4: a record with the pts item DIFFERENT, or the summary not all SAME: FAIL |
| 7 MAJOR: `slow` on native paths | REJECTED (CHARC); no marker added | - | - |
| 8 ADVISORY: `._` hides media | No code; one sentence in section 10 | - | - |
| 9 ADVISORY: W-GUARD text check | `platform_guard_offenders` walks the AST from each marker and EVALUATES each controlling test's polarity (`platform_polarity`: per host, `sys.platform` / `os.name` / `WINDOWS` bound); comments never count | W-GUARD X05-X38 (all 20 real sites still clean), 8 planted probes (`GUARD_PROBES`) | Probes, offenders at this head vs `51c50faf`: a comment 1 vs 0; `if sys.platform != "win32":` 1 vs 0; an inverted early skip 1 vs 0; `skipif(os.name == "nt")` 1 vs 0; the three guarded controls 0 vs 0. X17's real guard inverted in memory: `['test_app_wiring.py:419']` vs `[]`; made a comment: offender vs `[]` |
| 10 ADVISORY: W-SPACE shared constants | `D87_CONTRACT` pins 0.24 bit/pixel, the 1 / 2 / 4 shares, the 1.1 / 0.5 / 0.25 ratios and the 1.25 margin in the test; `SPACE_INPUTS` has one input where the size term binds and one where the ceiling binds (asserted) | W-SPACE[P64] | `MARGIN *= 2`: FAIL (the pin); the estimate doubled: FAIL (the arithmetic); the ceiling term dropped: FAIL (the ceiling-binding input); clean: PASS |
| 11 MINOR: an unavailable VT without a reason | `assert_proved_unavailable`: a non-empty ASCII reason AND `bit_depths == ()`, in M-CODEC, both M-V4 functions and `_vt_or_skip` | M-CODEC[T44], M-V4 | VT unavailable with reason None, `""`, or depths (8,): `51c50faf` PASS, here FAIL; with a reason and no depth: PASS on both |

**The M-V4 corpus** (item 6, as ruled: the synthetic sources the Windows V4 tests build; no
real-footage leg). Sources: the seven WP2.3 samples the Windows V4 test encodes (`tools/fixtures/
video.py`; `test_io_video_encode.DECODABLE`: 8-bit BT.709 full, 10-bit, untagged, truncated, VFR,
rotated, PCM MOV; AAC on the others) and the five sources the Windows V4 tests build with
`test_io_video_encode.Clips` (the start offset with an empty edit, three B-frame composition-offset
clips, the variable-rate gap). Each x {VT, x265} x {the source depth, 10} = 46 cases. Each runs
`video_fidelity.encode_file` and `fidelity_record` (every mandatory and required item SAME, the
roster whole, the frame count), plus the Windows tests' own per-source checks: exact pts for the
VFR sources, the B-frame clips' timing items and their AD-22 note, the rotation kept, the edit list
kept, the D86 warning and note for the truncated sample. The negative-timestamp case is the Windows
test's planted one (`test_open_refuses_negative_timestamps_by_name`: no edit list, every pts
shifted below zero) on the natively built source, refused at open by name for each available
encoder before FFmpeg starts (M-V4[P15, X42]). Reading "start offset, negative CTS" as these
`Clips` builders and the planted table is this cell's interpretation of the ruling (the module
`tools/fixtures/video.py` itself has no such builder).

**Banked to WP6.5 (not built; ONE register row candidate, beside the partial-row row):**
- M-DEVICE: the Mac CPU correction / export against the Windows references within AD-11's
  tolerances. Closure: WP6.5 writes and runs it on the Mac, with the Mac's numbers.
- M-SPAWN / M-BUNDLE: the worker protocol, cancel and descendant clean-up through the frozen
  bundle. Closure: WP6.5, on its own `Clearwater.app`.
- M-GUI: the application-menu merge, native dialog behaviour and Retina pixel mapping. Closure:
  WP6.5's native checks on the Mac, plus the owner's hand checks.

### Turn 6: the Reviewer A r3 fold-in

Reviewer A r3 (Codex, the delta `107e6c77..d55573f1`) returned NO_NEW_CRITICAL_MAJOR: Reviewer A
has converged. Its 2 MINOR and 2 ADVISORY findings, all in the W module's helper instruments, are
folded by `wp64-cell6` in TEST code only: `c6ae9a19` (#1, #4), `688163fc` (#2, #3), `a9e59e13`
(the verification loop's `with` rule). No file under `src/` or `tools/` changed, so Reviewer B's
view of the product at `d55573f1` stands.

The probes load ONLY the instrument definitions from the file (by AST), at this head and at the
pre-fold blob `d55573f1`, and feed them in-memory sources (no pytest collection, no entry point,
no process): `work\wp6.4\t6_guard_probes.py`, `t6_borrow_probes.py`, `t6_link_probes.py`,
`t6_with_variant.py`; logs `t6-*.log`.

| A r3 finding | Change | Test | Probe: `d55573f1` -> this head |
|---|---|---|---|
| 1 MINOR: W-GUARD's `exits()` takes any descendant exit | An earlier statement controls a marker only when it ends EVERY off-Windows path: `stops` / `stops_block` follow each branch the host can take (an off-Windows `if` body, an on-Windows `if`'s `else`, both branches of any other test); a `try` ends when its `finally` does, or its body and every handler do; a loop and a `with` never end a path (a loop may run zero times; `pytest.raises` / `suppress` swallow the exit); nested function and class scopes run nothing. A helper ends the caller's path only when its every path raises or skips (a `return` there reaches the caller). A stub counts only as a statement of its own, `monkeypatch.setattr` of `subprocess.` one of `LAUNCH_OPERATIONS` (`run`, `Popen`, `call`, `check_call`, `check_output`), either spelling | W-GUARD X05-X38; `GUARD_PROBES` 8 -> 15 (the three r3 forms 1 each, the swallowed skip 1, the two controls "every branch exits" and "launch stub" 0) | conditional return `[]` -> `['p:5']`; uncalled nested return `[]` -> `['p:5']`; `setattr(subprocess, 'PIPE', None)` `[]` -> `['p:3']`; `with pytest.raises` around the skip: `[]` -> `['p:5']`. The 20 real sites: 0 -> 0. The real offenders it found before still found: X09 and X18 with their guards renamed to a non-platform name 1 and 2 -> 1 and 2; X36 so renamed 0 -> 1 (`d55573f1` counted an earlier TEST function's `monkeypatch.setattr(subprocess, "run", ...)` as a module-level stop: the r3 #1 class) |
| 2 MINOR: the borrowed-case pin misses aliases and import-time patches | `shared_monkeypatch_offenders` classifies every reference: a `_CASES` attribute only in the isolated direct form (and with the fixture `monkeypatch` unused before its `with`), else an offender, whatever its root; a `_CASES` name, `getattr` text or import; `_w` other than `_w().ATTRIBUTE` with the attribute a registry or one of `W_HELPERS` (the six W instruments M calls natively); the W module named outside `_w`; a `MonkeyPatch` built other than as a `with` item's `.context()`; outside every function body, any `PATCH_OPERATIONS` call or assignment to an attribute or subscript | The pin: the seven real sites `[]`; the six planted leaks (`getattr` text new) `["test_x:3"]`; r3's three surviving forms planted, each caught with its lines | Whole-M mutants (the real M source, raw count still 7): helper alias `[]` -> `['borrow_fs:1583', 'borrow_fs:1584']`; an unclosed module-level `MonkeyPatch` replacing `subprocess.run` `[]` -> `['<module>:2', '<module>:3']`; a fixture `setitem(subprocess.__dict__, 'run', ...)` before the isolated M-FS call `[]` -> `['test_macos_filesystem_semantics:1298']`; the real M `[]` -> `[]` |
| 3 ADVISORY: the POSIX link model | `posix_link_model` now runs the stdlib's own `posixpath.realpath` from a private copy of `posixpath` whose `os` is a virtual file system (`lstat`, `readlink`, `stat` = ELOOP, `getcwd`; a relative name looked up from the working folder; a drive path runs as `/C:/x` and returns in host syntax); an optional `cwd` | NEW `test_portability_posix_link_model_agrees_with_posixpath` (4 cases: relative target, self loop non-strict and strict ELOOP, absolute target, traversal above the target); the five callers and D3 parity unchanged | Against `posixpath.realpath` with `os.lstat` / `os.readlink` / `os.getcwd` mocked to the same tables, cwd `/review`: `deep/alias -> ../Footage/sub`, `deep/alias/../output`: `/Footage/output` -> `/review/Footage/output` (agrees); `loop -> /review/loop`, `loop/x`: RecursionError -> `/review/loop/x` (agrees); a two-link loop RecursionError -> agrees; absolute target, traversal above it, no link: agree on both. The OLD `_absolute` (`t5_mutants.py old-absolute`) under the new model: 6 of 6 FAIL (T17, T26-T29, D3 parity); clean 6 pass |
| 4 ADVISORY: comment-only markers counted as code | `platform_guard_offenders` blanks every `tokenize` COMMENT token in place before matching (line and column positions kept; string literals, docstrings and skip reasons kept) | `GUARD_PROBES` "comment only" 0; "a comment" (a guard written as a comment) still 1 | `def f():` / `# mklink ...` / `pass`: `['p:2']` -> `[]`; the 20 real sites 0 -> 0 |

**Limits of the instruments (kept as such, not findings):** W-GUARD reads one module; a helper
reached through an attribute (`mod.helper()`) or a `match` statement is not followed (it then
counts as no stop, the strict side). The borrowed-case pin knows the fixture by its name
`monkeypatch`; a patch made through another fixture's object (`request.getfixturevalue`) is not
modelled. The link model is a virtual tree in which every non-link name is a folder.

### Turn 7: the Reviewer B fold-in

Reviewer B (Codex under WSL Linux, read-only, on `d55573f1` against `1e7cb908`) returned
NEW_CRITICAL_MAJOR_FOUND: 3 MAJOR, 3 MINOR, 2 ADVISORY
(`clearwater-review-evidence\wp6.4\B\review-B.txt`). CHARC ruled the fold (the brief's "Reviewer
B rulings"); `wp64-cell7` folded B 1, 2, 4, 5, 6 and 7: `b439d093` + `a9131f3c` (B1, B4; product),
`61aacbc0` (B2, B5, B7; tests), then the guide, this section and the ledger. Each "before" run
loads the `d5bef275` definition in memory (a pytest plugin that `exec`s the old function from
`git show` text into the live module, or rebinds the tool's `sys` name): no file of the tree is
reverted, no entry point is called, no Windows API runs under a patched platform. Logs
`work\wp6.4\t7-*.log`.

| B finding | Change | Test | Before -> after (mutant result) |
|---|---|---|---|
| 1 MAJOR: queue identities cached at add time | `gui/batch_panel.py` `add_paths`: the queued paths' lexical keys (`_path_key`, 1.0.0's key) and their CURRENT identities (`_key` re-read for every queued path; a missing file gives its lexical key, so no identity) are built at each call; a new path is a duplicate when its lexical key or its identity matches. `BatchItem.key` stays (the key when queued); labels unchanged (D5) | `test_gui_batch_panel.py`: delete + number reuse (B is queued), replace in place + re-add and a hard link to the replacement (nothing new), two live hard links in one call and two (one item) and one number on two devices (two items); a mutable fake `os.stat` | the old `add_paths` / `_key`: delete + reuse FAIL (B dropped), replace FAIL (A queued twice); the hard-link test passes on both (`t7-b1old.log`); new: 4 of 4 pass |
| 2 MAJOR: four environment tests fail on darwin | `test_environment_report.py`, the THIRD (and last) edit: the NVIDIA parsing cases use the `nvidia_platform` fixture, which on a darwin host rebinds ONLY the tool's own `sys` name to a view with `platform = "linux"` (no other module sees it; nothing Windows-only can run); the key test accepts darwin's disposition (`unavailable` = the three GPU keys, "not applicable"); W-TOOL's darwin "never run `nvidia-smi`" control unchanged | the six NVIDIA cases (`gpu_line_parses`, `gpu_uses_first_line_only`, `nvidia_smi_absent`, `nvidia_smi_bad_output` x6, `ffmpeg_failure`, `psutil_failures_degrade`) and `report_has_every_key` | the tool's `sys.platform` patched to darwin in memory: the `d5bef275` module 5 FAIL (B's four plus `test_psutil_failures_degrade`, which also asserts the parsed GPU model), 14 pass; the new module 19 / 19; on this host 19 / 19 |
| 3 MAJOR (reasoned): a bind mount of a footage SUBfolder | none: BANKED (section 10) | - | - |
| 4 MINOR: "never replaces" overstated; no recheck before the fallback | `config/presets.py` `_rename_without_replace`: after a refused link, `os.path.lexists(target)` (the volume's own name rule) and, when the name is taken, `FileExistsError` as the link raises; the WARNING follows only a rename; section 1's P73 line carries D1's limit | W-FS[P73] gains `PresetStore.rename` on a no-hard-link model (link EPERM; `lexists` and a REPLACING `rename` by an exFAT-like upcase rule, `_upcase`, chosen apart from NFC / casefold): `I` / `\u0131`, `i` / `\u0131` (the policy misses them; the recheck refuses), `Look` / `LOOK`, `caf\u00e9` / NFD (the policy refuses), and the control `Fresh` | the old fallback: FAIL, `DID NOT RAISE` at `I` / `\u0131` (the model's rename replaced `I.json`; `t7-b4old.log`); new: pass |
| 5 MINOR: M-FS relies on the host temp volume's case | `test_macos_portability.py`: `volumes` creates THREE images (`APFS` case-insensitive, `Case-sensitive APFS`, `ExFAT`; `_IMAGES`), no host folder; `_fs_native_alias` (T17, T26-T29) puts its case alias on the insensitive image and its distinct-name controls (`DIVE/FOOTAGE` a second real folder, `dive` absent) on the sensitive one | M-FS[P29, P30, P44, P45, X29] (identity), [P40, P41, P49, P73] (presets), [T17, T26-T29] (aliases) | REASONED: the M cases skip off darwin; WP6.5 runs them |
| 6 MINOR: no upgrade notice | `docs/user-guide.md` section 7, new subsection "Upgrading on macOS from a 1.0.0 source run" (the Library folder; `~/.config/clearwater` and `~/.cache/clearwater` left for the user to copy from or remove) | - | - |
| 7 ADVISORY: two surviving W mutants | W-FS[P29]: one file number on two devices is two keys; W-CODEC[P11]: the no-encoder message is non-empty and says "No HEVC encoder is available" | the two cases | `st_dev` dropped from `_key`: FAIL (`'file:41' != 'file:41'`); the no-encoder message emptied: FAIL; clean: both pass (`t7-b7-*.log`) |
| 8 ADVISORY: the B prompt's launch lock | none (the orchestrator's prompt error, as ruled) | - | - |

### Notable tests

- **The planted footage guard (W-FS T17, T26-T29).**
  - The fixture is a synthetic footage root `Dive/Footage` (with a clip). The output is under the
    differently cased existing spelling `DIVE/FOOTAGE/out`.
  - footage_guard's seams make it behave as macOS does: `normcase` folds nothing and `realpath`
    keeps the typed case, while the host's real `os.stat` gives one identity, as case-insensitive
    APFS does.
  - Each of the five sites refuses before any write, and the tree snapshot is unchanged.
  - The safe sibling `DIVE/Footage-out` passes.
  - The control: the old text check under the same seams lets the unsafe path through, so the test
    discriminates.
- **The D3 parity test.** `footage_guard` agrees with `headless_export.inside` on a real-filesystem
  containment corpus, and with `jobs.naming.is_same_path` on the equality subset (mutual
  containment).
- **W-GUARD.** A checker confirms that every Windows-only construct in the test helpers (mklink,
  junctions, ADS, 8.3 names, volume GUID, drive-relative paths, PowerShell) sits behind a platform
  guard, or behind a helper that skips off Windows, or is only called from guarded tests. A planted
  unguarded `mklink` helper fails by name.
- **W-FS[P30].** The Unicode label pair above kills the `casefold` mutant.
- **The M module.**
  - Disk images: a case-sensitive APFS image and an exFAT image are created with `hdiutil` under
    the temp folder and detached at teardown. They are attached only for the rows that need them.
  - VideoToolbox: real VT trials and encodes. A Mac without VT (a CI Mac) passes on a PROVED
    "unavailable" reason with the x265 fallback, and the VT-only cases skip with that reason.
  - The full comparator: `container_spike.compare` with D105's mandatory class for M-V4.
  - P74: a real `os.killpg` on a parent in its own session. The tool child stays in its own
    session and exits through EOF when its parent dies.
  - Cocoa: a child process for M-GUI. Qt events go only to Clearwater's own widgets.
  - M-BUNDLE: driven by `CLEARWATER_MAC_BUNDLE`.
  - Isolation: every child that imports the product gets HOME, APPDATA, LOCALAPPDATA and the XDG
    variables redirected, and a bounded timeout.
  - No test calls `clearwater.__main__`, `app.main` or the export worker's entry point.
  - Interactive native dialogs and Finder / Dock / Cmd-Q are the owner's hand checks at WP6.5.

## 2. Row-by-row disposition

Disposition categories:
- implemented (A or B) = the recommended change is built;
- validated (W) = a retain row whose portable behaviour is pinned by its W case;
- partly deferred = with the reason.

Every row also has its M case written, unexecuted. The W column names `test_portability_<function>`,
whose `site` parameter is the row ID; W-STATIC is the two mypy runs. Totals: implemented (A) 28,
implemented (B) 27, partly deferred 8, validated (W) 109; 172 rows. A site ending in `...` is
shortened; the full site is the WP6.2 audit's row.

| ID | Site | Disposition | Windows-side (test_portability_...) | Mac (written, unexecuted) |
|---|---|---|---|---|
| P01 | config/paths.py:115 | implemented (A) | `app_locations` | M-PATH[P01] |
| P02 | io/video/pipes.py:56 | implemented (A) | `spawn_policy`, W-STATIC (mypy both targets) | M-SPAWN[P02]; M-STATIC[P02] |
| P03 | io/video/pipes.py:67,85,95,112-116 | implemented (A) | `default_pipe` | M-PIPE[P03] |
| P04 | io/video/decode.py:335,350 | validated (W) | `default_pipe` | M-PIPE[P04] |
| P05 | io/video/decode.py:132-149,759; jobs/export.py... | validated (W) | `cpu_selection` | M-DEVICE[P05] |
| P06 | io/video/decode.py:72 | validated (W) | `tool_text_and_redaction` | M-TEXT[P06] |
| P07 | io/video/capability.py:35-42 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P07] |
| P08 | io/video/capability.py:109 | validated (W) | `tool_text_and_redaction` | M-TEXT[P08] |
| P09 | io/video/capability.py:50-56 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P09] |
| P10 | io/video/capability.py:57-66,160-169 | implemented (A) | `tool_text_and_redaction` | M-TEXT[P10] |
| P11 | io/video/capability.py:248-260 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P11] |
| P12 | io/video/encode.py:107 | implemented (A) | `encoder_rate_mapping` | M-RATE[P12] |
| P13 | io/video/encode.py:256 | implemented (A) | `encoder_rate_mapping` | M-RATE[P13] |
| P14 | io/video/encode.py:323 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P14] |
| P15 | io/video/encode.py:100,404-405,418-421,434-455 | validated (W) | `container_contract` | M-V4[P15] |
| P16 | io/video/probe.py:100; WP6.1 brief, round-0 ru... | implemented (A); bundle half M-BUNDLE at WP6.5 | `spawn_policy` | M-BUNDLE[P16] |
| P17 | io/video/probe.py:74 | validated (W) | `container_contract` | M-V4[P17] |
| P18 | core/memory.py:45 | validated (W) | `cpu_selection` | M-DEVICE[P18] |
| P19 | core/memory.py:85 | validated (W) | `cpu_selection` | M-DEVICE[P19] |
| P20 | core/backend.py:551 | validated (W) | `cpu_selection` | M-DEVICE[P20] |
| P21 | core/backend.py:797 | validated (W) | `cpu_selection` | M-DEVICE[P21] |
| P22 | core/backend.py:933,943,1028-1029; gui/shell.p... | implemented (A) | `cpu_selection`, `gui_contract` | M-DEVICE[P22]; M-GUI[P22] |
| P23 | core/backend.py:1027 | validated (W) | `cpu_selection` | M-DEVICE[P23] |
| P24 | app/composition.py:461; WP6.1 brief, FINAL rul... | partly deferred: bundle: M-BUNDLE at WP6.5 | `spawn_policy` | M-BUNDLE[P24] |
| P25 | app/main.py:270 | validated (W) | `app_locations` | M-PATH[P25] |
| P26 | app/startup.py:69 | validated (W) | `app_locations` | M-PATH[P26] |
| P27 | gui/sources.py:38 | validated (W) | `gui_contract` | M-GUI[P27] |
| P28 | gui/sources.py:57 | validated (W) | `filesystem_semantics` | M-FS[P28] |
| P29 | gui/batch_panel.py:94 | implemented (A) | `filesystem_semantics` | M-FS[P29] |
| P30 | gui/batch_panel.py:107 | validated (W); the Unicode pair kills the casefold mutant (turn 4) | `filesystem_semantics` | M-FS[P30] |
| P31 | gui/shell.py:465-476,488-489 | validated (W) | `gui_contract` | M-GUI[P31] |
| P32 | gui/shell.py:480 | validated (W) | `gui_contract` | M-GUI[P32] |
| P33 | gui/shell.py:274 | validated (W) | `gui_contract` | M-GUI[P33] |
| P34 | gui/batch_panel.py:149 | validated (W) | `gui_contract` | M-GUI[P34] |
| P35 | gui/preset_panel.py:126 | validated (W) | `gui_contract` | M-GUI[P35] |
| P36 | gui/settings_dialog.py:160 | validated (W) | `gui_contract` | M-GUI[P36] |
| P37 | gui/settings_dialog.py:542 | implemented (A) | `encoder_roster_and_commands` | M-GUI[P37] |
| P38 | gui/preview.py:211,294,319,383 | validated (W) | `gui_contract` | M-GUI[P38] |
| P39 | config/presets.py:70 | validated (W) | `filesystem_semantics` | M-FS[P39] |
| P40 | config/presets.py:264,549-564; docs/debt-regis... | validated (W) | `filesystem_semantics` | M-FS[P40] |
| P41 | gui/preset_panel.py:146 | validated (W) | `filesystem_semantics` | M-FS[P41] |
| P42 | jobs/naming.py:34 | validated (W) | `filesystem_semantics` | M-FS[P42] |
| P43 | jobs/naming.py:116 | validated (W) | `filesystem_semantics` | M-FS[P43] |
| P44 | jobs/naming.py:171 | validated (W) | `filesystem_semantics` | M-FS[P44] |
| P45 | jobs/naming.py:188 | validated (W) | `filesystem_semantics` | M-FS[P45] |
| P46 | jobs/naming.py:300 | validated (W) | `filesystem_semantics` | M-FS[P46] |
| P47 | jobs/export.py:111,725 | validated (W) | `filesystem_semantics` | M-FS[P47] |
| P48 | jobs/safe_write.py:112 | validated (W) | `filesystem_semantics` | M-FS[P48] |
| P49 | config/atomic.py:29-38; docs/debt-register.md:... | validated (W) | `filesystem_semantics` | M-FS[P49] |
| P50 | cache/keys.py:106 | validated (W) | `filesystem_semantics` | M-FS[P50] |
| P51 | cache/store.py:573 | validated (W) | `filesystem_semantics` | M-FS[P51] |
| P52 | io/video/inputs.py:54 | validated (W) | `filesystem_semantics` | M-FS[P52] |
| P53 | io/photo/png.py:162 | validated (W) | `filesystem_semantics` | M-FS[P53] |
| P54 | io/photo/reader.py:319 | validated (W) | `filesystem_semantics` | M-FS[P54] |
| P55 | interfaces/settings.py:34,66 | implemented (A) | `encoder_roster_and_commands` | M-CODEC[P55] |
| P56 | gpu_pack.py, pack_root; WP6.1 brief, FINAL Q6 | validated (W) | `app_locations` | M-PATH[P56] |
| P57 | __main__.py; WP6.1 brief, round-0 D1 | partly deferred: bundle: M-BUNDLE at WP6.5 | `spawn_policy` | M-BUNDLE[P57] |
| P58 | gpu_pack.py; WP6.1 brief, round-0 D2 | validated (W) | `spawn_policy`, W-STATIC (mypy both targets) | M-SPAWN[P58]; M-STATIC[P58] |
| P59 | io/video/encode.py:406-408 | implemented (A) | `encoder_rate_mapping` | M-RATE[P59] |
| P60 | io/video/encode.py:703-713 | implemented (A) | `encoder_rate_mapping` | M-RATE[P60] |
| P61 | io/video/encode.py:593-595 | implemented (A) | `encoder_rate_mapping` | M-RATE[P61] |
| P62 | io/video/encode.py:838-842 | implemented (A); export tail by CHARC grant | `encoder_roster_and_commands`; `export_names_an_encoder_outside_the_roster` | M-CODEC[P62] |
| P63 | gui/settings_dialog.py:95,507 | implemented (A) | `gui_contract` | M-GUI[P63] |
| P64 | jobs/disk_space.py:70-120,161 | validated (W) | `disk_space_estimate` | M-SPACE[P64] |
| P65 | io/video/pipes.py:56; review A r2 N1 | implemented (A) | W-STATIC (mypy both targets) | M-STATIC[P65] |
| P66 | io/video/encode.py:143-145 | validated (W) | `tool_text_and_redaction` | M-TEXT[P66] |
| P67 | cache/store.py:126-150 | validated (W) | `filesystem_semantics` | M-FS[P67] |
| P68 | io/video/encode.py:506-515 | validated (W) | `filesystem_semantics` | M-FS[P68] |
| P69 | jobs/safe_write.py:68-74 | validated (W) | `disk_space_estimate` | M-SPACE[P69] |
| P70 | jobs/naming.py:304-311 | implemented (A) | `filesystem_semantics`; `output_name_refusal_names_the_character` | M-FS[P70] |
| P71 | gui/preview.py:394-399 | implemented (A) | `gui_contract` | M-GUI[P71] |
| P72 | io/video/probe.py:67,504 | validated (W) | `tool_text_and_redaction` | M-TEXT[P72] |
| P73 | config/presets.py:395-402; docs/debt-register.... | implemented (A) | `filesystem_semantics` | M-FS[P73] |
| P74 | io/video/pipes.py:45-58; tools/headless_export.... | implemented (A) | `spawn_policy` | M-SPAWN[P74] |
| T01 | environment_report.py:172 | implemented (B): platform facts in the default report (S-B1, turn 4) | `tool_reporting` | M-TOOL[T01] |
| T02 | environment_report.py:171 | implemented (B): darwin NVIDIA fields null, not run | `tool_reporting` | M-TOOL[T02] |
| T03 | prototype/bench.py:1157-1159 | implemented (B): bench._windows_power statement form | `tool_reporting`, W-STATIC (mypy both targets) | M-TOOL[T03]; M-STATIC[T03] |
| T04 | prototype/bench.py:1467 | implemented (B): bench._cpu_brand statement form, comment fixed (D4 (d)) | `tool_reporting` | M-TOOL[T04] |
| T05 | prototype/bench.py:1479-1482 | implemented (B): bench._platform_name statement form | `tool_reporting`, W-STATIC (mypy both targets) | M-TOOL[T05]; M-STATIC[T05] |
| T06 | prototype/bench.py:156 | partly deferred: label not granted (bench.py owned at the mypy lines only); historical scope pinned | `tool_reporting` | M-TOOL[T06] |
| T07 | spike_io/transport.py:378 | validated (W) | `default_pipe` | M-PIPE[T07] |
| T08 | spike_io/transport.py:388 | validated (W) | `default_pipe` | M-PIPE[T08] |
| T09 | spike_io/transport.py:948-950 | implemented (B): transport.idle_gate statement form | `tool_reporting`, W-STATIC (mypy both targets) | M-TOOL[T09]; M-STATIC[T09] |
| T10 | spike_io/transport.py:116 | partly deferred: label not granted (transport.py owned at the mypy line only); pinned | `tool_reporting` | M-TOOL[T10] |
| T11 | spike_io/licences.py:132,149,152,158 | partly deferred: candidate DR 3 (licences.py not owned); M-TOOL xfail until it lands | `tool_reporting` | M-TOOL[T11] |
| T12 | spike_io/licences.py:188,192-210 | partly deferred: candidate DR 3; M-TOOL xfail until it lands | `tool_reporting` | M-TOOL[T12] |
| T13 | video_io_bench.py:118 | implemented (B): label (D4 (a)) | `tool_reporting` | M-TOOL[T13] |
| T14 | inventory.py:822-832 | implemented (B): inventory: AppleDouble counted apart | `filesystem_semantics` | M-FS[T14] |
| T15 | inventory.py:293,301 | validated (W) | `filesystem_semantics` | M-FS[T15] |
| T16 | inventory.py:825 | implemented (B): inventory: --exclude casefold | `filesystem_semantics` | M-FS[T16] |
| T17 | inventory.py:1112,1155 | implemented (B): footage_guard (DR-122) | `filesystem_semantics` | M-FS[T17] |
| T18 | inventory.py:1094 | validated (W) | `filesystem_semantics` | M-FS[T18] |
| T19 | local_config.py:140 | validated (W) | `filesystem_semantics` | M-FS[T19] |
| T20 | local_config.py:196 | validated (W) | `filesystem_semantics` | M-FS[T20] |
| T21 | headless_export.py:598 | validated (W) | `filesystem_semantics` | M-FS[T21] |
| T22 | headless_export.py:761 | validated (W) | `filesystem_semantics` | M-FS[T22] |
| T23 | headless_export.py:790,801 | validated (W) | `filesystem_semantics` | M-FS[T23] |
| T24 | headless_export.py:826,870 | validated (W) | `filesystem_semantics` | M-FS[T24] |
| T25 | headless_export.py:414 | validated (W) | `tool_text_and_redaction` | M-TEXT[T25] |
| T26 | lookcheck/frames.py:161 | implemented (B): footage_guard | `filesystem_semantics` | M-FS[T26] |
| T27 | container_spike/compare.py:1877 | implemented (B): footage_guard | `filesystem_semantics` | M-FS[T27] |
| T28 | analysis_breakdown.py:984 | implemented (B): footage_guard | `filesystem_semantics` | M-FS[T28] |
| T29 | export_oracle.py:645 | implemented (B): footage_guard | `filesystem_semantics` | M-FS[T29] |
| T30 | halo_probe.py:2360 | partly deferred: noted only (brief); pinned: reuses headless_export.inside | `filesystem_semantics` | M-FS[T30] |
| T31 | halo_probe.py:2373 | validated (W) | `filesystem_semantics` | M-FS[T31] |
| T32 | reviewpack/select.py:230 | validated (W) | `filesystem_semantics` | M-FS[T32] |
| T33 | reviewpack/build.py:875 | implemented (B): label | `encoder_roster_and_commands` | M-CODEC[T33] |
| T34 | prototype/clip.py:133 | implemented (B): label | `encoder_roster_and_commands` | M-CODEC[T34] |
| T35 | container_spike/spike.py:78 | implemented (B): label | `encoder_roster_and_commands` | M-CODEC[T35] |
| T36 | video_fidelity.py:377 | implemented (B): label | `encoder_roster_and_commands` | M-V4[T36] |
| T37 | video_io_bench.py:147 | implemented (B): label | `encoder_roster_and_commands` | M-CODEC[T37] |
| T38 | export_bench.py:580 | implemented (B): label | `tool_reporting` | M-TOOL[T38] |
| T39 | core_speed.py:350 | implemented (B): label | `tool_reporting` | M-TOOL[T39] |
| T40 | analysis_breakdown.py:848 | validated (W) | `tool_reporting` | M-TOOL[T40] |
| T41 | photo_verify.py:1161 | validated (W) | `tool_reporting` | M-TOOL[T41] |
| T42 | device_hold.py:57 | implemented (B): label | `cpu_selection` | M-DEVICE[T42] |
| T43 | prototype/backend.py:197 | validated (W) | `cpu_selection` | M-DEVICE[T43] |
| T44 | fixtures/video.py:317 | validated (W) | `encoder_roster_and_commands` | M-CODEC[T44] |
| T45 | fixtures/files.py:36 | validated (W) | `filesystem_semantics` | M-FS[T45] |
| T46 | photo_check.py:68 | validated (W) | `filesystem_semantics` | M-FS[T46] |
| T47 | photo_verify.py:332 | validated (W) | `filesystem_semantics` | M-FS[T47] |
| T48 | photo_memory.py:162 | validated (W) | `filesystem_semantics` | M-FS[T48] |
| T49 | prototype/bench.py:1480; review A r2 N1 | implemented (B): as T05 | W-STATIC (mypy both targets) | M-STATIC[T49] |
| T50 | prototype/bench.py:1159; review A r2 N1 | implemented (B): as T03 | W-STATIC (mypy both targets) | M-STATIC[T50] |
| T51 | spike_io/transport.py:950; review A r2 N1 | implemented (B): as T09 | W-STATIC (mypy both targets) | M-STATIC[T51] |
| T52 | export_oracle.py:661 | implemented (B): export_oracle.record_name refuses : and backslash | `filesystem_semantics` | M-FS[T52] |
| X01 | conftest.py:111 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X01] |
| X02 | conftest.py:215 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X02] |
| X03 | conftest.py:134 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X03] |
| X04 | conftest.py:214 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X04] |
| X05 | test_conftest_guard.py:82 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X05] |
| X06 | test_conftest_guard.py:329 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X06] |
| X07 | test_conftest_guard.py:337 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X07] |
| X08 | test_conftest_guard.py:346 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X08] |
| X09 | test_conftest_guard.py:381 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X09] |
| X10 | test_conftest_guard.py:478 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X10] |
| X11 | test_conftest_guard.py:599 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X11] |
| X12 | test_conftest_guard.py:670 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X12] |
| X13 | test_config_paths.py:44 | implemented (A) | `app_locations` | M-PATH[X13] |
| X14 | test_config_isolation.py:31 | validated (W) | `app_locations` | M-PATH[X14] |
| X15 | test_app_startup.py:178 | implemented (A) | `app_locations` | M-PATH[X15] |
| X16 | test_gui_startup.py:206 | implemented (A) | `app_locations` | M-PATH[X16] |
| X17 | test_app_wiring.py:415 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X17] |
| X18 | test_footage_locator.py:48 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X18] |
| X19 | test_footage_locator.py:78 | validated (W) | `filesystem_semantics` | M-FS[X19] |
| X20 | test_inventory.py:81 | validated (W) | `filesystem_semantics` | M-FS[X20] |
| X21 | test_headless_export.py:603 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X21] |
| X22 | test_headless_export.py:629 | validated (W) | `filesystem_semantics` | M-FS[X22] |
| X23 | test_io_video_decode_lifecycle.py:407 | validated (W) | `default_pipe` | M-PIPE[X23] |
| X24 | test_io_video_decode_lifecycle.py:424 | validated (W) | `default_pipe` | M-PIPE[X24] |
| X25 | test_io_video_decode_rules.py:97 | validated (W) | `tool_text_and_redaction` | M-TEXT[X25] |
| X26 | test_io_video_spawn.py:274,278 | validated (W) | `spawn_policy` | M-SPAWN[X26] |
| X27 | test_io_video_spawn.py:324 | validated (W) | `spawn_policy` | M-SPAWN[X27] |
| X28 | test_jobs_export_process.py:544 | partly deferred: bundle: M-BUNDLE at WP6.5 | `spawn_policy` | M-BUNDLE[X28] |
| X29 | test_jobs_naming.py:182 | validated (W) | `filesystem_semantics` | M-FS[X29] |
| X30 | test_jobs_naming.py:452 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X30] |
| X31 | test_reviewpack.py:366 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X31] |
| X32 | test_wp42a_runner_hardening.py:99 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X32] |
| X33 | test_wp42a_runner_hardening.py:134 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X33] |
| X34 | test_wp42a_runner_hardening.py:197 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X34] |
| X35 | test_wp42a_runner_hardening.py:234 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X35] |
| X36 | test_wp42a_runner_hardening.py:464 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X36] |
| X37 | test_wp42b_naming_guard.py:29 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X37] |
| X38 | test_wp42_runner_video.py:74 | validated (W) | `footage_guard_and_test_helpers` | M-GUARD[X38] |
| X39 | gui_support.py:12 | validated (W) | `gui_contract` | M-GUI[X39] |
| X40 | test_gui_preview.py:349 | validated (W) | `gui_contract` | M-GUI[X40] |
| X41 | test_gui_settings_dialog.py:489 | validated (W) | `encoder_roster_and_commands` | M-GUI[X41] |
| X42 | test_io_video_encode.py:77 | validated (W) | `encoder_roster_and_commands` | M-V4[X42] |
| X43 | test_io_video_encode.py:1851 | validated (W) | `encoder_roster_and_commands` | M-CODEC[X43] |
| X44 | test_core_backend.py:35 | validated (W) | `cpu_selection` | M-DEVICE[X44] |
| X45 | acceptance_support.py:73 | validated (W) | `tool_text_and_redaction` | M-TEXT[X45] |
| X46 | test_export_oracle.py:303-309 | implemented (B): POSIX skip removed | `filesystem_semantics` | M-FS[X46] |

## 3. The VT argument lists, per depth and quality, for both Q1 candidates

Source: ledger A.2 and the evidence file `vt-argument-lists-group-a.txt`. The encoder segment is
shown below. Everything outside it is NVENC's argument list, byte for byte (W-V4[P15]). Each R is
`nvenc_rate`'s maxrate for the same case (W-RATE[P13]).

R values:
- 4K60 HEVC source (level 5.1 Main, so R is capped at 40 Mb/s): High 40,000,000; Standard
  20,000,000; Draft 10,000,000.
- 1080p29.97 H.264 source (no source cap): High 14,915,004; Standard 7,457,502; Draft 3,728,751.

Candidate B (the default):

    -c:v hevc_videotoolbox -allow_sw 0 -b:v R -maxrate R -pix_fmt yuv420p -profile:v main      (8-bit)
    -c:v hevc_videotoolbox -allow_sw 0 -b:v R -maxrate R -pix_fmt p010le -profile:v main10     (10-bit)

Candidate A (`VT_RATE_CONTROL = "A"`). The Q values are PLACEHOLDERS, measured at WP6.5 (High 65,
Standard 55, Draft 45):

    -c:v hevc_videotoolbox -allow_sw 0 -q:v Q -maxrate R -pix_fmt yuv420p -profile:v main      (8-bit)
    -c:v hevc_videotoolbox -allow_sw 0 -q:v Q -maxrate R -pix_fmt p010le -profile:v main10     (10-bit)

At 10-bit the `-vf` chain still ends `format=yuv420p10le,setparams=...` (AD-10 unchanged).

The trials:
- 8-bit: `-c:v hevc_videotoolbox -allow_sw 0 -pix_fmt yuv420p -profile:v main`
- 10-bit: `... -pix_fmt p010le -profile:v main10`

## 4. The NVENC and x265 snapshot evidence

Source: ledger A.3. `capture_snapshots.py` ran on the base tree `c1458747` and on the head:
- the 24-case sha256 grid is equal;
- the 4 full argument literals are equal;
- the 4 trial commands are equal.

`test_portability_windows_encoder_command_snapshot[hevc_nvenc, libx265]` holds the base literals.
It passed on the unchanged code before any edit, and on every later commit.

## 5. The dual-target mypy output

At `a6294d43` (turn 4), run from the worktree root:

    uv run --no-sync mypy                    Success: no issues found in 162 source files
    uv run --no-sync mypy --platform darwin  Success: no issues found in 162 source files

At the base, the darwin target found 4 errors in 3 files: `pipes.py:56`, `prototype/bench.py:1159`
and `:1480`, and `spike_io/transport.py:950`. At the group-A yield 3 remained, all tool sites. At
group B there are 0, and still 0 at turn 4. `strict` and `warn_unreachable` are unchanged, and
there is no `platform` key in `[tool.mypy]`.

## 6. The lock diff summary

Source: ledger A.4 and `uv-lock.record.txt`.
- `uv lock --offline` exited 0 (uv 0.10.9, 70 packages), and `uv lock --check --offline` exited 0.
- A tomllib comparison against `c1458747:uv.lock` found:
  - the top-level keys equal (`version 1`, `revision 3`, no `resolution-markers`);
  - the same 70 package names;
  - no package other than `clearwater` changed, and no version moved.
- The diff is 4 lines, all in the `clearwater` entry: the darwin marker on the four cupy edges.
- `test_gpu_pack.py::test_locked_distributions_equal_the_lock` passes, so the eleven pack wheels
  are unchanged.

## 7. The W and M test counts per gate leg

Re-taken by the turn-7 cell at `61aacbc0` (`-p no:cacheprovider --timeout 600`,
`QT_QPA_PLATFORM=offscreen`, `PYTEST_ADDOPTS` unset; the parallel expression with `-n 4`, the
serial expression without; `work\wp6.4\t7_yield.sh`, `t7-yield.log`):

| Module | Parallel leg (collected / passed / skipped) | Serial leg (collected / passed / skipped) | Fullclip |
|---|---|---|---|
| `test_portability` (185) | 168 / 168 / 0 | 17 / 17 / 0 (14 `gui`, 3 `slow`) | 0 |
| `test_macos_portability` (224) | 205 / 0 / 205 | 19 / 0 / 19 (`macos` + `gui`: M-GUI 15, M-BUNDLE 4) | 0 |
| `test_environment_report` (19) | 19 / 19 / 0 | 0 | 0 |

The W and M modules together at `61aacbc0`: parallel 373 collected, 168 passed, 205 skipped;
serial 36 collected, 17 passed, 19 skipped; fullclip 0; `--collect-only` 409 = 373 + 36. Turn 7
adds no case id (its W checks sit inside W-FS[P29], W-FS[P73] and W-CODEC[P11]); whole modules at
`61aacbc0`: `test_gui_batch_panel` 47 passed (three new tests, `gui`, serial leg),
`test_config_presets` 121 passed, `test_gui_preset_panel` 46 passed. Turn 6
adds four W cases (the A r3 #3 model test), on the parallel leg; turn 5 added one W case (the
item-2 pin) and 46 M cases (the M-V4 corpus), all on the parallel leg and all skipped off darwin.
No case moved between legs.

The footage guard's callers' modules, turn 5's run at `c5b2608a` (all passed, none skipped; their
files and the guard are unchanged since): `test_inventory`,
`test_export_oracle`, `test_lookcheck`, `test_lookcheck_deep`, `test_container_spike`,
`test_container_spike_compare_equivalences`, `test_analysis_breakdown`. All ten modules together:
parallel 826 collected, 621 passed, 205 skipped; serial 44 collected, 25 passed, 19 skipped (W at
164 parallel then; four more now).

On Windows every M case is collected and skipped with "macOS native leg (WP6.5)"; no other skip
reason appears. The gate's two marker expressions are unchanged, and the collection identity
counts the M cases. The S-B1 seam check (`work\wp6.4\sb1_check.py`) re-run on both legs: 0
unstubbed seam calls.

The M functions, with their case counts:

| Function | Cases |
|---|---|
| M-STATIC | 9 |
| M-PATH | 8 |
| M-SPAWN | 5 |
| M-PIPE | 6 |
| M-DEVICE | 10 |
| M-TEXT | 8 |
| M-CODEC | 12 |
| M-RATE | 5 |
| M-V4 | 4 |
| M-V4 corpus | 46 |
| M-SPACE | 2 |
| M-FS | 51 |
| M-GUARD | 24 |
| M-TOOL | 15 |
| M-GUI | 15 |
| M-BUNDLE | 4 |

The package gate's full-suite figures are the gate's (not run by a cell).

## 8. The Library path table as built

| Platform | config_dir: settings.json, presets/, logs/clearwater.log, write-journal.json | cache_dir | GPU pack root |
|---|---|---|---|
| win32 | `%APPDATA%\Clearwater` | `%LOCALAPPDATA%\Clearwater\cache` | `%LOCALAPPDATA%\Clearwater\gpu-pack` |
| darwin | `~/Library/Application Support/Clearwater` | `~/Library/Caches/Clearwater` | None (no lookup) |
| other | `$XDG_CONFIG_HOME/clearwater` (default `~/.config/clearwater`) | `$XDG_CACHE_HOME/clearwater` (default `~/.cache/clearwater`) | `$XDG_DATA_HOME/clearwater/gpu-pack` |

- The home is the existing injectable parameter (HOME through `Path.home()`). No override variable
  was added.
- There is no migration from XDG on macOS (AD-25(a)): a Mac developer with data under
  `~/.config/clearwater` starts fresh.

## 9. The dependency expression

    gpu = ["cupy-cuda12x[ctk]>=14.2,<15; sys_platform != 'darwin'"]                (the gpu extra)
    "cupy-cuda12x[ctk]>=14.2,<15; sys_platform != 'darwin'",                       (the dev group)

A Mac `uv sync` installs no CuPy, and the product runs CPU-only (P22).

## 10. Limits

- **No Mac was run.** Every M test is unexecuted until WP6.5.
- **The VT texts are SYNTHETIC.** The VT listing and help texts (`tests/ffmpeg_text/`), the VT
  stderr markers and the macOS showinfo sample lines are synthetic. WP6.5 replaces them with a
  capture.
- **Interactive checks are the owner's.** The native file dialogs (P33-P36: picking a file), and
  the bundle's Finder / Terminal launch, Dock Quit, Cmd-Q and logout during an export, are the
  owner's hand checks at WP6.5. No synthetic desktop input is used.
- **Banked to WP6.5 (Reviewer A r2 item 6, as ruled; ONE register row candidate, beside the
  partial-row row below), each with its closure:** M-DEVICE's AD-11 comparison of the Mac CPU
  output with the Windows references (WP6.5 writes and runs it with the Mac's numbers); M-SPAWN /
  M-BUNDLE's worker protocol, cancel and descendant clean-up (WP6.5, through its own frozen
  bundle); M-GUI's application-menu merge, native dialog behaviour and Retina mapping (WP6.5's
  native checks and the owner's hand checks). WP6.5's brief lists them as owned work.
- **`._` is a reserved inventory prefix** (Reviewer A r2 item 8): every `._` name is counted as
  AppleDouble metadata by name, so a real clip named `._name.MP4` is not listed.
- **The native tests are unmarked beyond `macos` by ruling** (A r2 item 7, REJECTED): they run
  real FFmpeg and encoder trials on the Mac; WP6.5 sets their markers from the measured walls.
- **Linux has a roster (NVENC then x265, as ruled), but nothing is proved for Linux.**
- **A bind mount of a footage SUBfolder bypasses the guard on Linux** (Reviewer B 3, BANKED as
  ruled; pre-existing): `realpath` keeps the mount's spelling, so `Footage/sub` bound at `/alias`
  is not seen inside `Footage`. The owner's envelope is covered: Windows `realpath` resolves
  junctions and mount points, and macOS has no user bind mounts.
- **The preset fallback's residual race** (Reviewer B 4, D1's accepted limit): on a volume that
  makes no hard link, the rename rechecks that the target is absent and then uses POSIX
  `os.rename`, which replaces a target created in between. "The preset rename never replaces"
  holds only where the volume makes hard links (and on Windows).
- **P71's Windows behaviour change is the FIX of a pre-existing Windows defect.** The old
  `wheelEvent` zoomed a full step on any non-zero delta, so a precision touchpad over-zoomed.
  - A mouse notch (120) is unchanged.
  - Sub-120 touchpad deltas now accumulate to one step.
  - A single 240 event now takes two steps.
  - Not checked on real hardware.
- **The jobs/export.py empty-reason gap** (ledger A.7, item 3) is closed by CHARC's grant
  (`1a003fe4`; section 1).
- **M-TOOL[T01] / [T02] run real trials natively, by design.** Their W case now runs in its own
  `pytest.MonkeyPatch.context()` (turn 4), so the native half calls the unstubbed default
  `collect()`: on a Mac that runs the product's real VT / x265 trials. They stay on the `macos`
  marker only, not `slow`; the "no real trial unless `slow` / `gpu`" rule binds the Windows legs
  (CHARC's turn-4 ruling). Before the fix both would have failed on a Mac, reading the W stubs;
  the fix is shown on Windows by a replay only, and its native run is WP6.5's.
- **The environment report now runs the product's encoder trials by default** (S-B1). A report
  run on a machine without FFmpeg still writes, with every encoder unavailable and its reason.
- **The rows built only in part without a Mac.** For ONE register row at the accept; each row with
  its Windows proof and the WP6.5 native check that closes it (ledger B.6):

| Row(s) | Windows proof (W) | WP6.5 native check (M) that closes it |
|---|---|---|
| P09 P10 P12 P14 P59 | the VT argument lists, reasons and branch from snapshot / argv and the SYNTHETIC listings (W-CODEC, W-RATE, W-TEXT) | M-CODEC[P09, P14]: real VT 8 / 10-bit trials and a sink encode. M-RATE: both Q1 candidates under R. M-TEXT[P08, P10]: the real listing and reasons. Plus replacing the synthetic listings with a capture |
| P01 P25 P26 | injected-home Library paths (W-PATH) | M-PATH: a child with HOME redirected resolves the Library roots natively |
| P03 P74 | INFO fallback and `start_new_session` built with stubs (W-PIPE, W-SPAWN) | M-PIPE[P03]: the native INFO fallback. M-SPAWN[P74]: `os.killpg` leaves the child in its own session, and it exits on its parent's death |
| P22 | the darwin reason through a patched platform (W-DEVICE, W-GUI) | M-DEVICE: the reason with no CuPy installed. M-GUI[P22]: the Cocoa status text |
| P29 | identity on a fake stat and on NTFS (W-FS) | M-FS[P29]: case-insensitive and case-sensitive APFS images |
| P73 | the link / unlink / fallback branches stubbed (W-FS) | M-FS[P40, P41, P49, P73]: the DR-34(a) folding corpus on both APFS modes. M-FS[P48]: exFAT link refusal |
| P71 | synthetic offscreen `QWheelEvent`s (W-GUI) | M-GUI[P71]: Cocoa wheel phases including momentum; the owner's trackpad by hand |
| T14 | a synthetic `._` tree (W-FS) | M-FS[T14]: exFAT AppleDouble files made by `xattr` |
| T17 T26-T29 | the planted case alias reproduced through footage_guard's text and link-resolution seams on NTFS, and the symlink-then-`..` alias through a POSIX `realpath` model (W-FS, D3 parity) | M-FS[T17, T26-T29]: a native symlink alias, a native case alias on the case-insensitive APFS image (its distinct-name controls on the case-sensitive one) and a native symlink-then-`..` alias |
| T01 T02 | the environment facts with stubs (W-TOOL); on by default (S-B1) | M-TOOL[T01, T02]: the native report (arm64, macosx-*, NVIDIA not applicable, the VT / x265 rows) |
| T11 T12 | the Windows licence-scan forms are pinned (W-TOOL) | M-TOOL[T11, T12]: xfail until candidate DR 3 adds the Mach-O forms |
| P16 P24 P57 X28 | source / frozen command construction (W-SPAWN) | M-BUNDLE with `CLEARWATER_MAC_BUNDLE`, plus the owner's Finder, Dock-Quit and Cmd-Q checks |

- **Other notes.**
  - The P30 labels are unchanged (D5); turn 4's Unicode pair pins that against a casefold change.
  - `tools/package/build.py:645` is reported only (WP6.3b, D4 (d)).
  - The `test_prototype_clip` order dependence is not caused by this package. It is reproduced on
    main at HEAD.
  - Two failures under `-n 4` in group B's runs (a MemoryError in `analysis_breakdown` and the
    container spike's x265 proof) passed serially; host load.
