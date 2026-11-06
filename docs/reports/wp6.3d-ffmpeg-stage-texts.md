# WP6.3d - FFmpeg stage licence texts

Turn 3, 2026-11-06. Reviewer A r2 and Reviewer B r1 folds implemented for
the dispatcher's verification; the seat rebuild and acceptance remain at the seat.
This turn bundles the nine ruled folds as one logical review-remediation change.

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
luasocket license and rav1e's PATENTS. Their repository bytes remain exact.
Turn 2 implements CHARC's option (b): declared, lossless UTF-8 transcodes in
artifact notices, annotated with their original encoding and SHA-256. The root
annex links the exact source files. See the turn-2 design and controls below.

## Ruling application

| Source | Application |
|---|---|
| A1; C pass-2 acceptance | Used the seat-staged 105-record census and verified its three binding hashes offline. No fetch or footage access. |
| A2 | Added per-record texts, fail-closed checks, per-row notices, root regeneration, refusal tests and the scripts-change checklist trigger. |
| A3-A4 | Claude A/B, real artifact rebuild, acceptance and release bump are the dispatcher's next steps; none executed in this cell. |
| B S1; C1-C3 | Separate component allowlist = unchanged runtime 15 + B's 16 atoms + C's four. MPL-1.1 stays outside both lists. One parser uses OR-any, AND-all, atomic WITH and complete grammar validation. |
| B C1/C2/C4/C5; C4 | Applied census corrections to openal, chromaprint, mingw and x265; shaderc stays Apache-2.0 because its three static sub-dependencies now have separate records. |
| B S1 gnulib rewrite | Gnulib extra uses `GPL-3.0-or-later AND LGPL-2.1-or-later AND LicenseRef-gnulib-permissive`. |
| B second-pass 1; C4; turn-3 B2 | Added glslang, spirv-tools and spirv-headers-shaderc immediately after shaderc, with the census's full pins, built status, null configure flag, empty extras and via relationship. Used the existing `commit` vocabulary instead of adding `git-commit`. Excluded test-only googletest `52eb8108`, abseil-cpp `dbf88f93`, re2 `972a15ce` and effcee `f8e8a164`: shaderc third_party/CMakeLists.txt L28-30/L50-70 and SPIRV-Tools external/CMakeLists.txt L97-191, CMakeLists.txt L316-317 under BtbN's skip-test flags. Turn 3 records the exact reason durably in shaderc's lock note and both notice surfaces. |
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
Turn-1 review status: A/B were pending; the turn-2 round ledger below records A r1.

## Turn 2 - Reviewer A r1 folds

Binding dispositions are dispatch 2, Appendix D (CHARC `5a293802`) and Appendix
E. All six folds are in envelope. No finding was rejected as a false positive.
The seven owned paths suffice; no native-licence file was edited.

| Finding | Fold, mechanic and surface | Test / mutation killed |
|---|---|---|
| F1 MINOR | `tools/package/notices.py:1632`: every non-built stage/extra receives the exact fetched/not-compiled verdict. Both ffnvcodec downloads display it in artifact and regenerated root rows; built rows keep the default. | `tests/test_tools_package_notices.py:551`, `test_fork_ffmpeg_notices_render_all_built_sources_and_explain_exclusions`, pins both download verdicts and built x265. Kills restoring the unconditional default verdict. `audit.py` independently reproduces both false pre-fold verdicts. |
| F2 MINOR | `tests/test_tools_package_ffmpeg.py:205`: the case-change refusal accepts `component text (directory differs|missing/unsafe)`. Case-sensitive filesystems refuse at existence; case-insensitive filesystems refuse at set equality. | `test_component_text_files_fail_closed[case]` still kills accepting case-changed paths, while accepting either valid refusal path. This host exercised the case-insensitive path; no Linux execution is claimed. |
| F3 MINOR | `tools/package/build.py:802`, `:1205`, `:1240`: component-only optional encoding, closed schema/values, strict decoding and exact re-encoding after original-byte SHA-256 verification. `tools/package/notices.py:1613`, `:2626` carries the declaration and renders the annotated transcode. | `tests/test_tools_package_ffmpeg.py:270`, `test_component_text_encoding_refusals`, covers primary/extra undeclared non-UTF-8, undefined cp1252 bytes, unapproved encoding, case alias and wrong type with named `match=` refusals. Kills default replacement decoding, ignoring declarations or permitting arbitrary codecs. The full-source notices test pins all three encodings, note lines/digests and exact reverse transcodes, and strictly decodes the complete artifact. Kills raw-byte rendering, missing/wrong annotations or lossy transcoding. |
| F4 ADVISORY | `tools/package/build.py:1216`: texts are nonempty on every record regardless of status; the downloaded-extra bypass is removed. | `tests/test_tools_package_ffmpeg.py:233`, `test_downloaded_extra_requires_texts_even_when_files_are_removed`, removes an extra's texts and its now-unreferenced files. Kills the accepted A mutant; refusal matches `component texts must be nonempty`. `audit.py` confirms the pre-fold validator accepts this same mutation and the fixed validator refuses it. |
| F6 ADVISORY | `tools/package/ffmpeg.lock.json:63`, `:321`, `:1187`, `:1275`, `:1927`, `:2135`: removed only the duplicate pass-1 phrase from mingw, libpng, aom, chromaprint, glib and libvpx; retained every U5 path list. | `tests/test_tools_package_ffmpeg.py:177`, `test_shaderc_fetched_records_and_ruled_census_counts`, pins one occurrence per named row. Kills reintroducing the duplicate suffix. Independent normalized-lock comparison proves these six suffix removals and three encoding additions are the entire lock diff. |
| F7 ADVISORY | `tools/package/build.py:1271` corrects the validator docstring. `tools/package/notices.py:2801`, `:2815`, `:2820` migrates the in-file pointer, names both populations in the heading and uses one grammatical sentence. Root regenerated only with `--root-annex --write` (`THIRD_PARTY_NOTICES.md:8989`). | `tests/test_tools_package_notices.py:520`, `test_root_annex_has_the_same_component_rows_and_text_hashes_as_artifacts`, pins the heading/new pointer and rejects the stale pointer. Kills stale heading/anchor generation. Existing root-generator check also kills a stale committed annex; independent link audit checks every linked native text exists. Docstring and sentence were checked against the implementation. |

F5 ADVISORY is a seat count only: **478** expected real artifact rows (473 + 3
new records + 2 downloads). No implementation change or real rebuild this turn.
F8 ADVISORY, pre-existing limitation: the expression tokenizer tolerates doubled,
leading and trailing spaces; record only under CHARC's ruling, with no parser edit.

### F3 design and source-byte evidence

Only these three text entries declare `encoding` in the lock:

| Text | Encoding | Original file SHA-256 |
|---|---|---|
| `openjpeg--src--bin--wx--OPJViewer--source--license.txt` | `latin-1` | `8081c33f6953950dcf424aa844714658b73ada0fcaea16e4487f5fa07ef0960d` |
| `rav1e--PATENTS` | `cp1252` | `7b14a70c194b19dbd0625e7eac839a63200f67484521ce5e8d8244b127e8907a` |
| `openmpt--include--premake--binmodules--luasocket--LICENSE` | `cp1252` | `8e8c6314d9e78fe452ee355167f2c40cfbee8207e14dcb5ddd4a2655cb5c6aad` |

No encoding means strict UTF-8. A declaration permits only `latin-1` or
`cp1252`, and decode/re-encode must reproduce the exact bytes. Undefined cp1252
bytes therefore refuse rather than becoming replacement characters. The
runtime text schema stays unchanged. Hash, byte-count checks and deduplication
use original bytes; only the final artifact body becomes UTF-8. Directly under
each affected heading is exactly one line of the form
`transcoded from <encoding>; original file sha256 <64-hex>`.

Adjusted `test_fork_ffmpeg_notices_render_all_built_sources_and_explain_exclusions`:
its turn-1 assertion that every raw file appears in the artifact now compares
the declared UTF-8 transcode for these three files, while preserving exact raw
assertions for all others. It extracts each emitted fenced body and re-encodes
to the original bytes, including original CRLF and final-newline state. This
test and the root/artifact comparison now use strict UTF-8 decoding instead of
`errors="backslashreplace"`.

`work/wp6.3d/turn2/audit.py` reads the pre-fold modules from HEAD and executes
them only in memory; neither module calls a product entry point. Its
`audit.log` confirms: only the permitted lock edits; **282/282** native texts
equal their committed blobs and SHA-256; every declared/default decode is
lossless; both old download verdicts differ from the fix; old artifact bytes
fail strict UTF-8 while new bytes pass with exactly three notes; the root is
strict UTF-8 and matches regeneration; **105 + 232** root rows and no broken
native-file links; F4's texts-plus-files mutant accepted before/refused after.
The synthetic stage notice artifact is retained alongside that log.

### Round ledger and verification loop

| Round | Verdict | Critical / major / minor / advisory | In / out | NEW / REOPENED | Reverts | Fix surface | Depth |
|---|---|---|---|---|---|---|---|
| A r1, Claude at seat; report `work/wp6.3d/review-A-r1.md` | NO_NEW_CRITICAL_MAJOR | 0 / 0 / 3 / 5 | 7 introduced in envelope; F8 pre-existing | 8 / 0 | 0 | Product code, lock/generated notices, tests and report; F5/F8 record only | Turn 1 ended at 207K (dispatcher); turn 2 fresh, no later figure supplied |

The cumulative row is carried in this owned report for the seat's ledger
transfer; `docs/proofs/` is outside this turn's edit ownership. A delta r2 and
B are dispatcher-run Claude processes, not cell-spawned reviews.

| Pass | Suspected / independently confirmed | Fixed / outcome |
|---|---|---|
| 1 | F1/F3/F4 reachable on the actual committed records; confirmed with pre-fold versus fixed modules in `audit.py`. | Truthful verdicts, declared transcodes and unconditional text obligation. |
| 2 | Encoding and row controls could accept drift; focused run exercises all new refusals, both verdicts, three reverse transcodes and root pointer. | `focused.log`: 18 passed. F2 test portable by accepting both correct refusal paths. |
| 3 | Lock edit scope, source bytes or root links could drift. | `audit.log`: all checks pass; no native text changes. Required final suite/static checks below provide the final validation. |

### Turn-2 validation

All logs and the isolated runner are under `work/wp6.3d/turn2/`. The runner
redirects APPDATA, LOCALAPPDATA and XDG roots to disposable worktree paths,
blocks PySide6/shiboken6 imports, disables plugin auto-loading, explicitly loads
pytest-timeout (120 seconds) and `sandbox_mkdir_shim`, disables the cache
provider and excludes `test_python_m_clearwater_starts_the_shell_and_exits_0`.
The sole headless-entry child retains its own GUI stubs/block, redirected roots
and 15-second timeout. No real GUI, frozen executable or build ran.

- `ruff-final.log`: `uv run --no-sync ruff check .` - **All checks passed!**
- `format-final.log`: `uv run --no-sync ruff format --check .` - **337 files already formatted**.
- `mypy-final.log`: `uv run --no-sync mypy` - **Success: no issues found in 166 source files**.
- `mypy-darwin-final.log`: `uv run --no-sync mypy --platform darwin` - **Success: no issues found in 166 source files**.
- `annex-final.log`: `uv run --no-sync python tools/package/notices.py --root-annex` - **root annex matches**.
- `pytest-final.log`: **909 passed, 1 skipped, 5 failed in 221.65 s**. Command:
  `uv run --no-sync python work/wp6.3d/turn2/run_tests.py final tests/test_tools_package_notices.py tests/test_tools_package_build.py tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py tests/test_release_workflow.py -q --basetemp=work/c63d-2`.
  Every failure is `tests/test_release_workflow.py::test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`, cases
  `annotated`, `lightweight`, `wrong-commit`, `mismatched-name`, `deleted-origin`.
  All five fail at the disposable fixture's local Git push, before the gate,
  with exit 128 and sh.exe `CreateFileMapping` under the restricted token.
  The skip remains `test_non_windows_containment_never_silently_skips` (Windows
  host; POSIX native proof belongs to WP6.5). Every other selected test passes.
- `diff-check-final.log`: `git diff --check` exits **0**; only existing
  checkout-policy warnings for Markdown/JSON. The native text folder is untouched.

Final verification pass: code comments/docstrings now describe the encoding
exception and per-record texts accurately; the final source-byte/root audit
and static checks pass. No new in-envelope defect remains. The initial
development run (`red.log`) was not a stable pre-fold baseline (implementation
edits began while it ran); before/after claims above rely on the separate
in-memory HEAD comparisons in `audit.log`, not that run.

No scope deviation, new dependency, frozen-interface change or lock identity /
provenance change. No network, real build, frozen/GUI run, desktop input,
footage/profile access or worktree Git write. Only seven owned paths changed;
scratch logs/instruments remain under `work/wp6.3d/turn2/`. No stopped item or
implementation fold remains. Claude A delta r2, Claude B, the real-Git gate,
the 478-row seat rebuild and CHARC acceptance remain at the dispatcher.

## Turn 3 - Reviewer A r2 and Reviewer B r1 folds

Dispatch 3 binds CHARC's 2026-11-06T19:37Z ruling on all four A advisories
and the seat's disposition to fold all five B findings. Both reviewers returned
**NO_NEW_CRITICAL_MAJOR** at `cd7faecb`. The reports are
`work/wp6.3d/review-A-r2.md` and `work/wp6.3d/review-B-r1.md`.

| Finding | Fold / current file:line | Test and mutation killed |
|---|---|---|
| R2-1 ADVISORY | `tools/package/build.py:1285`, `:1304`: a declared encoding on strict UTF-8 bytes refuses; a declared decode containing U+0080-U+009F refuses after exact-byte hash and round-trip checks. The three real declarations pass. | `tests/test_tools_package_ffmpeg.py:293`, `test_declared_latin1_cannot_turn_patent_quotes_into_c1_controls`, plants Latin-1 on rav1e PATENTS and matches the C1-control refusal. `:305`, `test_declared_encoding_is_refused_for_utf8_text`, plants each allowed encoding on UTF-8 bytes and matches the named refusal. Kills trusting round-trip alone and allowing unnecessary declarations. |
| R2-2 ADVISORY, REQUIRED | `tools/package/notices.py:2626`, `:2659`: the complete joined document decodes as strict UTF-8 before return. Each emitted block retains its byte range and source/file label; failure becomes `ValueError` with the global byte offset and that source. There is no population filter. | `tests/test_tools_package_notices.py:694`, `test_whole_document_utf8_backstop_names_wheel_source_and_offset`, plants non-UTF-8 bytes in the synthetic numpy dist-info licence. `:711`, `test_whole_document_utf8_backstop_names_runtime_source_and_offset`, plants a runtime text and updates its exact-byte hash so integrity checks pass first. Both match the exact independently computed offset and their source/file. Kills returning the joined bytes without the backstop or reporting a local offset/wrong source. |
| R2-3 ADVISORY | `tools/package/notices.py:2639`: declared transcodes label their metadata `Original SHA-256` and `Original bytes`; other blocks keep their existing labels. | `tests/test_tools_package_notices.py:614`, within the full-source notices test, pins the original digest and size labels for all three declarations. Kills describing the original identity as the displayed body's identity. Root hash-link extraction continues to resolve every source file. |
| R2-4 ADVISORY | `tools/package/notices.py:1601`: missing/empty texts raise with the stage/extra title instead of silently skipping. | `tests/test_tools_package_notices.py:674`, `test_component_row_renderer_refuses_missing_texts_without_validator`, directly bypasses lock validation for missing/empty primary and extra texts and matches the record-specific refusal. Kills restoring `continue`. |
| B1 MINOR | `tools/package/notices.py:2518`: any build-component or toolchain-runtime row emits the representative-file-name/shared-text disclaimer, naming both populations and explaining that a label may name another component's identical copy. | `tests/test_tools_package_notices.py:657`, `test_stage_only_notices_explain_representative_and_shared_text_labels`, renders 105 stage rows with no runtime rows and pins the full disclaimer. Kills the runtime-only condition and runtime-only wording. |
| B2 MINOR | `tools/package/ffmpeg.lock.json:961`: shaderc retains its entire prior note, then appends exactly the ruled sentence naming googletest `52eb8108`, abseil-cpp `dbf88f93`, re2 `972a15ce`, effcee `f8e8a164`, the two BtbN flags and the pinned CMake line evidence. | `tests/test_tools_package_notices.py:644`, within the full-source notices test, pins the suffix, passes the entire note unchanged through artifact and root rendering, and checks the sentence has no Markdown-active characters. Kills dropping/changing any exclusion or omitting it from either notice surface. `audit.py` independently proves this sentence is the entire lock diff. The earlier ruling table now names all four exclusions too. |
| B3 ADVISORY | `docs/release-checklist.md:71`, `:93`: names all five accepted drift cases, requires text verification at every new pin, equality of distinct component/excluded stages and the scripts' list, and a reviewed `via` change for new fetching stages. Uses the annex's new name. | Documentation verification against B's executed mutants and `build.py`'s byte/schema/configure checks and hard-coded shaderc relationship. No validator behavior change is claimed for these five residuals; the checklist supplies the required independent census procedure. |
| B4 ADVISORY | `tools/package/build.py:1259`: a path-to-encoding map over all references refuses disagreements before decoding any reference, including declared-versus-absent. | `tests/test_tools_package_ffmpeg.py:318`, `test_shared_component_file_encoding_must_agree`, appends rav1e PATENTS under earlier-sorting aom. Latin-1 versus cp1252 and absent versus declared each match the conflict refusal; two cp1252 references pass. Kills per-reference-only validation and a check that ignores undeclared references. |
| B5 ADVISORY | `tools/package/build.py:921` and `docs/release-checklist.md:81`: documents exact complete-selection `chosen` grammar, the compound example and cartesian/exponential growth. Parser behavior is unchanged. | Existing `test_chosen_preserves_and_obligations_and_requires_a_compatible_branch` pins complete versus partial selections for both populations; the shared parser tests pin AND/OR/WITH behavior. Documentation was checked against the parser's cartesian-product implementation and both chosen-membership checks. |

Only the eight owned paths are changed this turn. The root annex was regenerated
only by `uv run --no-sync python tools/package/notices.py --root-annex --write`.
No file under `native-licences/` changed. The stage/runtime source population and
all hashes, pins and lock provenance are unchanged. F8's whitespace-tolerance
limitation remains record-only as ruled; the real rebuild target remains 478 rows.

### Turn-3 cumulative round ledger

| Review | Verdict | Critical / major / minor / advisory | In / out | NEW / REOPENED | Reverts | Disposition / fix surface | Depth |
|---|---|---|---|---|---|---|---|
| A r1, Claude | NO_NEW_CRITICAL_MAJOR | 0 / 0 / 3 / 5 | 7 introduced in envelope; F8 pre-existing | 8 / 0 | 0 | Six folds in turn 2; F5 count and F8 limitation recorded. Product, lock/notices, tests/report. | Turn 1 207K, dispatcher figure |
| A r2, Claude, delta | NO_NEW_CRITICAL_MAJOR | 0 / 0 / 0 / 4 | 4 in / 0 out | 4 / 0 | 0 | All four confirmed and folded this turn. Product renderer/validator, tests/report. | No new dispatcher figure supplied |
| B r1, Claude, whole package | NO_NEW_CRITICAL_MAJOR | 0 / 0 / 2 / 3 | 5 in / 0 out | 5 / 0 | 0 | All five confirmed and folded this turn. Product, lock/generated notices, tests, checklist/report; no test-only remediation round. | No new dispatcher figure supplied |

The owned report carries these cumulative rows for the seat's ledger transfer;
there is no cell-spawned review and no edit under `docs/proofs/`.

### Turn-3 validation and owner verification loop

Logs, instruments and disposable profiles are under `work/wp6.3d/turn3/`.
The copied isolated runner retains redirected APPDATA/LOCALAPPDATA/XDG roots,
the PySide6/shiboken6 import block, plugin auto-load disabled, explicit
pytest-timeout (120 seconds), `sandbox_mkdir_shim`, cache provider disabled,
and the required `-k 'not test_python_m_clearwater_starts_the_shell_and_exits_0'`.
The existing entry-point child retains GUI stubs/block, redirected roots and
its 15-second timeout; no GUI/frozen executable/build was run.

- Pre-fold RED (`red.log`, exit 1): **13 failed, 1 passed in 4.54 s**, on the
  stable turn-2 implementation before any turn-3 product edit. The passing
  control is repeated matching cp1252 declarations. The new refusal and notice-rendering
  tests fail on the pre-fold behavior.
- Focused GREEN (`focused.log`, exit 0): **14 passed in 4.27 s** on the fold.
- Independent audit (`audit.log`): the exact shaderc sentence is the entire
  lock diff; 282 component and 157 runtime source hashes match; original bytes
  decode/re-encode exactly; synthetic stage/runtime output and regenerated
  root are strict UTF-8; all three original labels exist; the note is intact
  on both surfaces; 105 + 232 rows and no broken native links. An additional
  planted wheel block after all three transcodes checks its exact global
  error offset and provenance. Only owned paths changed.

- `ruff-final.log`: `uv run --no-sync ruff check .` - **All checks passed!** (exit 0).
- `format-final.log`: `uv run --no-sync ruff format --check .` - **337 files already formatted** (exit 0).
- `mypy-final.log`: `uv run --no-sync mypy` - **Success: no issues found in 166 source files** (exit 0).
- `mypy-darwin-final.log`: `uv run --no-sync mypy --platform darwin` - **Success: no issues found in 166 source files** (exit 0).
- `annex-final.log`: `uv run --no-sync python tools/package/notices.py --root-annex` - **root annex matches** (exit 0).
- `pytest-final.log` / `pytest-final-exit.txt`: **922 passed, 1 skipped, 5 failed in 226.21 s** (exit 1).
  Command: `uv run --no-sync python work/wp6.3d/turn3/run_tests.py final tests/test_tools_package_notices.py tests/test_tools_package_build.py tests/test_tools_package_smoke.py tests/test_tools_package_ffmpeg.py tests/test_release_workflow.py -q -rs --basetemp=work/c63d-3`.
  Every failure is `tests/test_release_workflow.py::test_real_git_gate_restores_checkout_overwrite_and_refuses_invalid_tags`,
  cases `annotated`, `lightweight`, `wrong-commit`, `mismatched-name`,
  `deleted-origin`. Each fails at its disposable fixture's local Git push,
  before the gate, with exit 128 and Git sh.exe's `CreateFileMapping` error
  under the restricted token. Every other selected test passes.
  The exact skip line is `tests\test_tools_package_smoke.py:754: POSIX process-group native proof belongs to WP6.5`.
- `diff-check-final.log`: `git diff --check` exits **0**; only the existing
  checkout-policy warnings for Markdown/JSON. All runner output is file-backed.

| Verification pass | Suspected / independently confirmed | Fixed / final outcome |
|---|---|---|
| 1 | A r2 and B r1 findings: reproduced the new refusal/output gaps on stable pre-fold code (13 failures, one positive control), checked the census's pinned exclusion evidence and actual validator/parser limits. | All nine findings confirmed; none rejected as false positive. Implemented the exact ruling; no scope deviation. |
| 2 | Offset attribution after earlier transcodes, source-byte drift, shared declarations, note/metadata loss, or stale root links. | Focused controls pass; independent audit proves exact global offset after three transcodes, exact shaderc-only lock diff, 439 unchanged text identities and intact links/labels. No further defect found. |
| 3 | Final selected suite, static checks or completion claims could disagree with the files. | 922 passes plus only the five confirmed sandbox Git failures and existing POSIX skip; Ruff/format, both mypy targets, root check and audit pass. Final changes after pytest were only adjacent string-literal wrapping for E501 and validator documentation; emitted strings and test regexes are unchanged. No new in-envelope finding in the final verification pass. |

No implementation fold remains. The seat owns QA of the final candidate,
the real-Git cases, any subsequent review disposition, the real rebuild
(478 rows) and acceptance. No dependency, frozen interface, source text,
asset, pin, lock provenance or parser behavior changed. No network fetch,
GUI/frozen run, real PyInstaller build, synthetic desktop input, real profile /
footage access, role-mailbox action or worktree Git write was performed.
The required tests attempted only local pushes in disposable fixture repositories;
no command stages, commits, pushes or tags the worktree or a real remote.

## STOPPED ITEMS and remaining work

No ruling STOP. Seat review, real-Git cases, the real artifact rebuild and its
478-row observation, acceptance and release remain the dispatcher's work.
No implementation item is left undone. No change outside the owned paths was
needed. The report records test limitations instead of claiming the sandbox
provided a green real-Git gate.
