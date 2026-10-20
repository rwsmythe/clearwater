# WP2.2 — Interface module (dispatch brief, DRAFT for CHARC approval)

**Status:** DRAFT, written by the orchestrator (generation 3) on 2026-10-20 at CHARC's commission
(`9fb52c00bbb58a9b`). **Do not dispatch until CHARC approves.** Items needing CHARC's ruling are
in "For CHARC before dispatch". Owner decisions: none.
- Spec **v0.5.3**. Architecture **DRAFT 0.1** as updated at `3591e80` (`docs/architecture.md`
  section 3; `docs/decisions.md` AD-20). Gate report `docs/reports/wp1.6-gate-report.md`.
- Cell: `implementer-sonnet-high`. Tier **STRONG**.
- Worktree `.worktrees/wp2.2`, branch `wp2.2`, base = the main commit named at dispatch.

**Why.** Plan WP2.2: "Implement the frozen interfaces as code: types, protocols and data classes,
with docstrings, and no behavior. Provide a stub for each interface so Phase 3 packages can build
and test before their dependencies exist." AD-20 froze IF-1 to IF-10 as written in
`docs/architecture.md` section 3. After this package, an interface changes only by CHARC's
decision.

| Field | Content |
|---|---|
| ID and title | WP2.2 — Interface module (`clearwater.interfaces`); plan section 6 WP2.2, section 8.1 |
| Goal | IF-1 to IF-10 as importable Python: frozen dataclasses, `typing.Protocol` classes, type aliases and the one function signature (`select_backend`), with Google docstrings, in `src/clearwater/interfaces/`; one stub per protocol in `clearwater.interfaces.stubs`; tests proving each stub satisfies its protocol, the dataclasses are frozen, and IF-9/IF-10 serialise. |
| Spec / decision clauses | AD-20 (the freeze), AD-6, AD-8, AD-9, AD-12, AD-13 (IF-9 JSON), AD-22; architecture section 3 verbatim; plan 8.1 (the dependency rule: `interfaces` imports nothing from `core`, `methods`, `io`, `jobs` or `gui`), 8.2 (what each IF must carry); spec D16, D54, D56, D63, D71, D74, D83, D84, D86, D95, D98, D113, D116, G12. |
| Depends on | WP2.1 DRAFT 0.1 (`3591e80`). Nothing else. |
| Files owned | `src/clearwater/interfaces/` (NEW): `__init__.py` (re-exports the public names), one module per IF (`image.py` IF-1, `backend.py` IF-2, `method.py` IF-3, `statistics.py` IF-4, `video.py` IF-5, `photo.py` IF-6, `cache.py` IF-7, `jobs.py` IF-8, `parameters.py` IF-9, `settings.py` IF-10), `stubs.py`; `tests/test_interfaces.py` (and `tests/test_interfaces_stubs.py` if it helps); `docs/proofs/wp2.2-ledger.md`. NOT owned: `src/clearwater/__init__.py` (stays a stub), `pyproject.toml` (`dependencies` stays `[]`; NumPy stays in `dev` until WP3.1 per CHARC), `docs/architecture.md`, `docs/decisions.md`, `tools/`, the harness. |
| Interfaces provided | IF-1 to IF-10, FROZEN from accept (AD-20). |
| Hardware flags | None. No `gpu`, `footage` or timing. CuPy is never imported. |
| Out of scope | Any behaviour: no algorithm, no I/O, no FFmpeg, no file writes outside pytest's basetemp. The stubs are in-memory fakes (rules below). No `core`, `methods`, `io`, `jobs`, `config` or `gui` modules. No settings file location or loading (WP3.15). No change to any signature in section 3. A needed change is a STOP to CHARC. |
| Done | Plan 4.5; ruff check, ruff format --check, mypy (strict, `src/clearwater` and `tools`), and the full pytest all green; harness gate untouched; every round-1 ruling applied; Reviewer A converged. |

## Task ladder

1. **Ground.** Read `docs/architecture.md` section 3 and AD-20 in full. Copy every type,
   field, method, parameter, default and comment into the code exactly. Comments become
   docstrings, and each docstring keeps the clause references the comment carries.
2. **Unnamed types. Propose them; do not invent behind the ruling.** Section 3 uses nine names
   it does not define: `VideoStreamInfo`, `AudioStreamInfo`, `DataStreamInfo`, `EditEntry`,
   `Fault`, `GoProInfo`, `PhotoMetadata`, `CacheEntry`, `SinkReport`.
   - For each one, write a ledger table (name; field; type; the spec or decision clause it
     comes from; why). `VideoStreamInfo` starts from the comment at IF-5. `Fault` covers the
     kinds the IF-5 comment lists.
   - Implement the proposal as frozen dataclasses marked PROPOSED in their docstrings.
   - Then YIELD with the table for CHARC's round-1 ruling, before Reviewer A round 1. Apply the
     ruling exactly.
3. **Annotation gaps.** Some section-3 parameters carry no annotation:
   - `asarray(self, a, dtype=...)`;
   - `pyramid_expand(self, a, shape)`;
   - `Parameter.default` / `neutral: Any`;
   - `Settings` field types and defaults, which section 3 names without types.

   Mypy strict needs every parameter annotated. Use the narrowest type the section-3 comment or
   the cited spec clause implies, and list each one in the same ledger table for the round-1
   ruling. `Settings` defaults come from G12, AD-8, AD-9 and AD-12 where those state one. A
   default no clause states is listed, not invented.
4. **The `Array` alias.** Implement it per CHARC's ruling (item 1 below).
5. **IF-9 and IF-10 serialisation.**
   - `ParameterSet.to_json()` / `from_json()` in the AD-13 format, plus the provenance form
     (AD-13 with `source` and `settings`).
   - The "method-schema validation step" is a function that checks a `ParameterSet` against a
     `CorrectionMethod.parameters` tuple: method id, unknown names, type, minimum/maximum, enum
     choices. It returns a list of problems.
   - `Settings` gets `to_json()` / `from_json()` (a JSON string in and out). No file I/O.
   - Round trips are exact. `created` is ISO-8601.
6. **Stubs** (`clearwater.interfaces.stubs`). One per protocol, named `Stub<Protocol>`, plus a
   stub `select_backend`. Rules (decision fixed at issue; CHARC may overrule, item 3):
   - **In-memory, deterministic, no I/O, no GPU.**
   - **Trivial behaviour only.**
     - `StubCorrectionMethod`: id `"stub"`, one stage, `analyze` returns zeros of the declared
       statistic names, `render` returns the input image unchanged and refuses a missing stage
       as IF-3 says.
     - `StubStatisticsStore`: a dict keyed by pts ticks; `smooth` copies raw to smoothed.
     - `StubVideoSource`: serves `Frame`s from a list given at construction, with their exact
       pts.
     - `StubVideoSink` and `StubPhotoSink`: record what they receive.
     - `StubProxyCache`: a dict.
     - `StubProgress`: records reports; cancellable by a flag.
   - **Anything that needs an algorithm** raises `NotImplementedError` naming the IF and the
     package that implements it: the `ArrayBackend` image operations (blur, pyramid, colour
     conversion, percentile) go to WP3.1.
   - `StubArrayBackend.asarray` / `to_host` are NumPy identity conversions to float32.
7. **Tests** (`tests/test_interfaces*.py`):
   - each stub passes `isinstance(stub, Protocol)` (`@runtime_checkable` on every protocol);
   - mypy accepts each stub assigned to a variable of its protocol type. Do this in
     `stubs.py` itself (an `if TYPE_CHECKING:` block of assignments), because mypy checks
     `src/clearwater` but not `tests/`;
   - every dataclass is frozen: assignment raises `FrozenInstanceError`;
   - `Frame` is an `Image`;
   - IF-9 round trip, provenance round trip, and validation catches each problem kind by name;
   - IF-10 round trip;
   - the dependency rule: a test that imports `clearwater.interfaces` and asserts no `cupy`,
     `av`, `PIL`, `PySide6` or `clearwater.<other>` module was imported;
   - a planted defect fails by name: a non-frozen dataclass, a stub missing a protocol method,
     a validation miss.
8. **Docstrings** on every public module, class, function and field group (Google style).

## For CHARC before dispatch

1. **`Array` alias.** Section 3 says `Array` is a NumPy or CuPy `ndarray`, always float32,
   (H, W, 3). `interfaces` must not import CuPy, and mypy has no CuPy stubs. Recommended:
   `Array: TypeAlias = numpy.typing.NDArray[numpy.float32]`. The docstring says a CuPy array is
   accepted at run time, structurally, and that the backend owns the distinction. Alternative:
   `Any`, which loses type checking on every pixel field.
2. **IF-9 validation in WP2.2.** Recommended YES, because IF-9 names the step and it needs no
   algorithm beyond comparisons. Alternative: the schema only, with validation in WP3.15.
3. **Stub rules** as task 6: trivial in-memory behaviour, and `NotImplementedError` for anything
   algorithmic. Recommended. Alternative: every stub method raises, which leaves Phase 3 nothing
   to test against.
4. **Round 1** = your ruling on the ledger table (task 2 types, task 3 annotations and
   defaults). The cell YIELDS for it before its first Reviewer A round.

## Declared operating envelope

Python 3.12, mypy strict, NumPy 2.x as locked; no GPU; Windows 11 (the code is portable, N1).
Out of envelope: CuPy at type-check time; serialised files from other versions
(`format_version` other than 1 is refused by name, nothing more).

## Review loop (Reviewer A), per `docs/review-gate-clearwater.md` Part 1

- Tier **STRONG**. Transport, flags, probe, prompt, per-round assertions and evidence layout as
  the WP1.5 brief, with `wp2.2` substituted. Evidence in
  `clearwater-review-evidence/wp2.2/rN/`; ledger `docs/proofs/wp2.2-ledger.md`.
- **WHAT TO EXAMINE:**
  - every signature against `docs/architecture.md` section 3, character for character in
    names, parameter order, keyword-only markers, defaults and return types;
  - every field of every dataclass, against section 3 and the round-1 ruling;
  - frozen-ness and inheritance (`Frame(Image)`);
  - `@runtime_checkable` on every protocol;
  - stubs that satisfy their protocols in substance, not only by name (signatures match);
  - no behaviour beyond the stub rules;
  - the dependency rule;
  - serialisation round trips, including `None`, enum values and floats;
  - validation completeness;
  - docstrings that say what the section-3 comment says, and no more.
- Reviewer B is the orchestrator's seat pass on the merge candidate.

## Notes for the cell

- **Return report** = your FINAL message, under about 70 lines, per `docs/dispatch-recipe.md`
  section 4. Include:
  - the module list;
  - the round-1 ruling as applied;
  - the stub table (protocol, stub, behaviour);
  - the gates, read off the final head;
  - the Reviewer A rounds and verdict.
- **STOP for:**
  - any section-3 signature that cannot be written as given (quote it; propose; do not
    change it);
  - a contradiction between section 3 and a cited clause;
  - any need to touch a file you do not own.
- **Working rules:**
  - `uv sync` in the worktree.
  - Commit by pathspec with `feat(wp2.2): ...` and the `Co-Authored-By:` footer.
  - Never a bare `cd`.
  - Never post to a mailbox.
  - The full pytest takes 8-15 minutes: run it in the background with output to a file under
    `work/wp2.2/`.
  - Yield at every round boundary. The orchestrator reads your depth there.
