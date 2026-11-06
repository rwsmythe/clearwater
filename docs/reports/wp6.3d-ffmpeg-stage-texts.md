# WP6.3d - FFmpeg stage licence texts

Turn 1, 2026-11-06. Implementation candidate for the dispatcher's Claude A
delta review; Claude B, the seat rebuild and acceptance remain at the seat.
One logical change bundles the ruled census, validation, notices and controls.

## Built and evidence

- `tools/package/native-licences/ffmpeg-components/`: 282 byte-exact census
  files, retaining the census's representative names and deduplication within
  this folder. Identical bytes already in other native surfaces remain copied
  here, keeping the component folder independently checkable.
- `tools/package/ffmpeg.lock.json:32`: 100 primary components plus 5 extra
  repository records = 105 records; 352 row-text references; 282 referenced
  names = 282 folder files. Every record has texts, including the two
  downloaded-not-built nv-codec-headers records. The existing 97 primary rows
  retain absent status; the three new rows explicitly say built. Extra source
  statuses, all existing source pins and every non-component lock field are
  unchanged.
- `tools/package/build.py:719`, `:734`: stage/extra text and chosen fields;
  optional primary status/via. `:883` adds the separate 35-atom component
  allowlist; the 15-atom runtime allowlist remains unchanged. `:910` is the
  shared parser; `:1191`, `:1199`, `:1229` implement closed fields, status,
  expression, chosen and text checks. `validate_ffmpeg_lock` at `:1245`
  checks files, hashes and exact directory membership, with a directory
  override for isolated notice surfaces. A missing status means built.
  The three fetched records share shaderc's script through the explicit
  `shaderc git-sync-deps` relationship; ordinary duplicate stages still refuse.
- `tools/package/notices.py:1121` registers the component folder beside the
  separately locked toolchain folder. Neither folder is a manifest component;
  `manifest.json` therefore needs no edit. `:1522` validates the selected
  surface; `:1588` builds each stage/extra row from its own text identities,
  without filtering records with texts by status. The aggregate row retains
  `ffmpeg-LICENSE.txt`. Identity-bearing inputs are checked again by the
  existing renderer. The artifact embeds the texts using the same mechanism
  as `ffmpeg-toolchain/`.
- `tools/package/notices.py:2705` regenerates the root annex from the same
  stage/runtime row helpers. Hash aliases preserve the old runtime links
  when bytes are shared between folders. `THIRD_PARTY_NOTICES.md` was changed
  only by `python tools/package/notices.py --root-annex --write`.
- `docs/release-checklist.md:67` adds the scripts-change census trigger and
  the fetch-step census sentence.

The component population grows by three, but artifact notice rows grow by
**five**: 473 + 3 fetched shaderc records + 2 previously omitted downloads =
**478 expected rows** in the seat's otherwise unchanged artifact. The synthetic
FFmpeg surface has 338 rows: aggregate + 105 stage/extra + 232 runtime.
The real artifact count remains a seat rebuild observation, not a cell claim.

The copy/verifier is `work/wp6.3d/turn1/stage_texts.py`. It verifies the three
binding census hashes, then every copied size, SHA-256 and supplied Git blob
SHA-1 in sorted order, copies with byte I/O and checks destination bytes.
Repeated outputs `text-inventory2.json` and `text-inventory3.json` are identical.
`audit.py` independently compares every row's texts to the census, all source
identities/statuses to HEAD, all file bytes to the staged originals, and Git's
text attribute for all 282 files. `audit.log` records all checks passing.
The existing `.gitattributes:2` rule `tools/package/native-licences/** -text`
covers every new file, so no attributes change or checkout conversion is needed.

Three upstream files are not UTF-8: openjpeg's OPJViewer license, openmpt's
luasocket license and rav1e's PATENTS. Their bytes are preserved, including
inside artifact notices under the existing verbatim renderer. Display-oriented
test comparisons use backslash replacement when decoding; integrity assertions
compare raw bytes and SHA-256. The root annex links the exact source files.

## Ruling application

| Source | Application |
|---|---|
| A1; C pass-2 acceptance | Used the seat-staged 105-record census and verified its three binding hashes offline. No fetch or footage access. |
| A2 | Added per-record texts, fail-closed checks, per-row notices, root regeneration, refusal tests and the scripts-change checklist trigger. |
| A3-A4 | Claude A/B, real artifact rebuild, acceptance and release bump are the dispatcher's next steps; none executed in this cell. |
| B S1; C1-C3 | Separate component allowlist = unchanged runtime 15 + B's 16 atoms + C's four. MPL-1.1 stays outside both lists. One parser uses OR-any, AND-all, atomic WITH and complete grammar validation. |
| B C1/C2/C4/C5; C4 | Applied census corrections to openal, chromaprint, mingw and x265; shaderc stays Apache-2.0 because its three static sub-dependencies now have separate records. |
| B S1 gnulib rewrite | Gnulib extra uses `GPL-3.0-or-later AND LGPL-2.1-or-later AND LicenseRef-gnulib-permissive`. |
| B second-pass 1; C4 | Added glslang, spirv-tools and spirv-headers-shaderc immediately after shaderc, with the census's full pins, built status, null configure flag, empty extras and via relationship. Used the existing `commit` vocabulary instead of adding `git-commit`. The four test-only fetched dependencies stay excluded for the census's pinned CMake reasons. |
| B U5/P1-P7; C7 | Carried all ruled vendored texts and appended the literal vendored-subtree/compilation-undetermined note on every census row naming it. |
| B U1; C7 | Both freetype rows choose GPL-2.0-or-later; both alternative texts remain carried. |
| B U3 | Gnulib retains COPYING and the four FSF texts; its row note discloses that per-module notices are not enumerated. |
| B U4; C2 | Carried libxml2 dict.c/list.c excerpts and full blobs; its expression is `MIT AND ISC-Veillard`. |
| B U6 | Avisynth's C-interface linking exception is in the row note; expression unchanged. |
| B U7/U8/U11 | Preserved the census's text populations, including PacketVideo NOTICE and canonical SPDX/header material. Existing seat-verified lock basis fields remain intact. |
| B U10 | Whole Avisynth/nv-codec headers accompany their excerpts. |
| B U12; C7 | Every record with texts renders, including both nv-codec downloaded-not-built extras; status is disclosed in their notes. |
| B U13/U14 | Census network-log reconstruction remains a stated census limit; no new network activity. Kept the census's shared names within the new folder and duplicated equal bytes across existing folders. |
| B checklist sentence | Added the stage's own fetch-step sentence (git-sync-deps, DEPS, cargo, submodules) to the re-pin step. |
| C1-C2 | Added AML-glslang and MIT-Khronos-old under their SPDX names, plus LicenseRef-PFFFT-modified-BSD and ISC-Veillard. Shaderc/glslang row notes carry CHARC's two-sentence NVIDIA reasoning. |
| C4 | Shaderc's note contains the required static-link/DEPS sentence; its old proposed combined expression is not retained. |
| C5 | Dropped `openssl--util--perl--OpenSSL--copyright.pm` and `xz--build-aux--license-check.sh`: scripts, not licence texts. Thus 284 census texts become 282 copies, and 354 references become 352. |
| C6 | No mass status edit: absent primary status is built; explicit statuses are from the closed built/downloaded-not-built set. |

All 105 final component/extra expressions parse successfully against the
component allowlist. There are six corrected existing expressions: mingw,
gnulib, libxml2, chromaprint, openal and x265. Shaderc's original Apache-2.0
expression is retained as ruled.

## Parser behavior and controls

The toolchain behavior deliberately changes: an unknown but syntactically valid
OR alternative no longer poisons a compatible sibling. Both allowlists use the
same parser. A bare unknown atom, an OR with no compatible branch, an AND with
an unknown required part and malformed syntax still refuse. WITH is one atom.
Every branch is parsed, so a passing OR branch cannot conceal malformed text.
Compatible choices retain all AND obligations; an incompatible or partial chosen
selection refuses. The existing known-combined-text guard now compares the
terms of complete selections; the committed runtime census still passes.

`test_runtime_licence_parser_refuses_unknown_atoms_and_invalid_grammar` no longer
lists `MIT OR Unknown` as a refusal. It moved to the accepting roster, with the
reverse order too, because C3 supersedes the old strict-OR expectation. The
malformed `MIT OR Apache-2.0.` control remains a refusal. The synthetic notices
incompatibility test now uses a parsed GPL-2.0-or-later expression with its
explicit negative compatibility verdict, preserving its aggregate diagnostic
purpose while the new parser independently refuses unknown expressions.

| Control / planted defect | Mutation killed |
|---|---|
| `test_component_obligations_fail_closed`, missing/empty primary and extra texts | Remove nonempty-text obligation. |
| `test_component_text_files_fail_closed`, missing | Remove file-existence check (must raise the named ValueError). |
| Same, hash | Skip file SHA-256 comparison. |
| Same, orphan/directory/case | Weaken exact directory set equality or case-sensitive names. |
| Obligation/chosen tests, including compound expressions | Skip chosen membership or permit a partial/incompatible branch. |
| Component expression tests and shared parser, bare unknown | Trust the compatibility marker instead of the expression. |
| Shared parser, unknown OR compatible in either order | Replace OR union with intersection (old strict behavior). |
| Shared parser, unknown OR unknown | Accept all unknown atoms. |
| Shared parser, MIT AND Unknown | Replace AND cross-product with union. |
| Shared parser, WITH known/unknown exception | Discard the WITH exception binding. |
| Shared parser, malformed/trailing tokens | Stop parsing once a compatible prefix is found. |
| `test_component_absent_status_means_built` | Treat missing status as invalid or bypass the built text obligation. |
| Obligation/status tests | Remove the closed-set/type status check. |
| Component text-schema tests | Permit unknown fields, unsafe paths or invalid digests. |
| Shaderc record/count test | Drop/reorder a fetched record, change its relationship or enlarge either allowlist. |
| `test_ffmpeg_component_text_integrity_uses_the_selected_surface` | Read the default folder instead of the selected surface, or skip render-time identity checks. |
| Full stage-row notices test | Reuse the aggregate licence, omit raw source bytes/hash blocks, or restore built-only rendering (loses two rows). |
| Root/artifact component comparison | Omit a root stage row or mislink one of its text hashes. |

`work/wp6.3d/turn1/mutations.py` executes guard changes only in memory, with
passing baseline controls. `mutations-final.log`: **13 guard mutants killed**;
includes nonempty texts, chosen, status, strict OR, weak AND, WITH, tail grammar,
unknown atoms, absent status, missing/hash/orphan files and built-only rendering.
The remaining table entries are planted-data/assertion controls in the tests.

## Validation and verification loop

All runner outputs are under `work/wp6.3d/turn1/`. The isolated pytest runner
redirects APPDATA, LOCALAPPDATA and all XDG roots to disposable worktree paths,
blocks PySide6/shiboken6 imports, loads `sandbox_mkdir_shim`, disables the cache
provider and excludes `test_python_m_clearwater_starts_the_shell_and_exits_0`.
Plugin auto-loading is disabled so pytest-qt cannot import the blocked GUI;
pytest-timeout is loaded explicitly (120 seconds per test, outer 600-second
bound). The existing headless-entry test's child has its own GUI block,
redirected roots and 15-second timeout. No product GUI or frozen build ran.

- RED: `red2.log`, before implementation: 52 failed / 202 passed; the new
  component/parser obligations were absent. The first attempted runner stopped
  before tests because pytest-qt tried to import blocked GUI bindings; corrected
  by disabling plugin auto-load, without relaxing the GUI block.
- Development: `recheck.log`: **681 passed** in the two owned modules.
- `ruff-final.log`: **All checks passed!**
- `format-final.log`: **337 files already formatted**.
- `mypy-final.log`: **Success: no issues found in 166 source files**.
- `mypy-darwin-final.log`: **Success: no issues found in 166 source files**.
- `annex-final.log`: **root annex matches** (default `--root-annex` check).
- Required five-module suite, `pytest-final.log`: **898 passed, 1 skipped,
  5 failed in 198.40 s**. Every failure is
  `tests/test_release_workflow.py::test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`
  with cases `annotated`, `lightweight`, `wrong-commit`, `mismatched-name`,
  `deleted-origin`. All five fail at the fixture's local-only Git push to its
  disposable origin: exit 128, Git's sh.exe fatal CreateFileMapping error under
  the restricted token. They do not reach the tag gate. The skip is
  `test_non_windows_containment_never_silently_skips`: POSIX process-group
  native proof belongs to WP6.5. Every other selected test passes.
  Command: `uv run --no-sync python work/wp6.3d/turn1/run_tests.py final
  tests/test_tools_package_notices.py tests/test_tools_package_build.py
  tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py
  tests/test_release_workflow.py -q --basetemp=work/c63d-1`.
- `diff-check-final.log`: `git diff --check` exits 0. Its only output is the
  existing checkout-policy warning for the generated Markdown and lock JSON;
  the native text folder is explicitly excluded from line-ending conversion.

Owner verification loop:

| Pass | Suspected | Independently confirmed / rejected | Fixed / disposition |
|---|---|---|---|
| 1 | Shared shaderc stage paths conflict with old uniqueness; strict runtime OR rejects cairo. | Confirmed by original validator/parser and RED controls. | Explicit fetched-stage relationship, one OR-any parser and closed checks. |
| 2 | Complete parser selections conflict with the runtime combined-text guard. | Confirmed by failed root generation and compiler_builtins' one-text expression. | Compare full selections' terms with the known combined text; root generation and runtime tests pass. |
| 3 | New notice tests fail. | Confirmed: sorted planner rows versus lock order, non-UTF-8 upstream bytes, whitespace and render-time byte-count diagnostic. Product byte preservation was correct; no product defect in these five failures. | Corrected tests to identify rows by name, preserve bytes, compare syntax safely and match the actual diagnostic. |
| 4 | Source identities, folder bytes, claims or text coverage drifted. | Independent audit PASS; 13 guard mutants killed; repeated copy inventories identical; focused modules green. | No further defect found. Final five-module result below supplies the gate evidence. |
| 5 | A final package test or report claim is wrong. | The five-module log confirms 898 passes, the existing POSIX skip and only the five anticipated real-Git sandbox failures. Final Ruff/format and diff checks pass. | Full final pass finds no new in-envelope defect; transfer the candidate and disclosed sandbox limits to the seat. |

No design dispute or out-of-envelope edit was needed. Frozen product interfaces,
dependencies, fork, asset and provenance are untouched. No network fetch,
footage or owner-profile access, worktree Git metadata write, PyInstaller build,
desktop input or workflow action. The required real-Git fixture creates only
disposable repositories under its basetemp and attempts local-only pushes there;
no cell command stages, commits, pushes or tags this worktree or any real remote.
Review rounds: none yet; A/B belong to the dispatcher's seam-3 process.

## STOPPED ITEMS and remaining work

No ruling STOP. Seat review, real-Git cases, the real artifact rebuild and its
478-row observation, acceptance and release remain the dispatcher's work.
No implementation item is left undone. No change outside the owned paths was
needed. The report records test limitations instead of claiming the sandbox
provided a green real-Git gate.
