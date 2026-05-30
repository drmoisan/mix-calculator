# schema-matching-and-discovery - Plan

- **Issue:** #42
- **Parent:** Epic #40 (configurable-schema-subsystem)
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30T06-52 (revised to remove private-symbol reuse in P1-T1)
- **Status:** Ready for preflight
- **Version:** 1.1
- **Work Mode:** full-feature

## Required References

Read in the order defined by the `policy-compliance-order` skill. Auto-loaded
path-scoped rules apply; do not duplicate their content here.

1. `CLAUDE.md` (standing instructions)
2. `.claude/rules/general-code-change.md`
3. `.claude/rules/general-unit-test.md`
4. `.claude/rules/quality-tiers.md`
5. `.claude/rules/python.md`
6. `.claude/rules/python-suppressions.md`
7. `.claude/rules/self-explanatory-code-commenting.md`
8. `.claude/rules/tonality.md`

**All work must comply with these policies; do not duplicate their content here.**

## Scope, Constraints, and Module Decisions

This feature is additive, pure logic only. It builds on Feature A
(`src/schema_model.py`, `src/schema_serialization.py`, `src/_schema_json_helpers.py`,
`src/schema_settings.py`, `src/schema_registry.py`,
`src/schemas/default_{aop,le}.schema.json`) and reuses the existing resolver
helpers in `src/etl_columns.py`.

Module-placement decision (recorded for executor): `src/etl_columns.py` is 205
lines. To keep `resolve_columns` byte-for-byte behaviorally unchanged and avoid
editing the existing resolver file at all, `probe_columns` and its `ProbeResult`
value object are placed in a new sibling module `src/etl_column_probe.py`, which
imports and reuses only the PUBLIC symbols `normalize_name` and
`DEFAULT_THRESHOLD` from `src/etl_columns.py`. The probe MUST NOT import the
private `_best_fuzzy_index`: importing a `_`-prefixed symbol across module
boundaries fails `poetry run pyright` strict mode (`reportPrivateUsage`), and the
resolver file may not be edited to add a public alias (AC1 requires it
byte-for-byte unchanged), no `# pyright: ignore[reportPrivateUsage]` is
pre-authorized in `.claude/rules/python-suppressions.md`, and `getattr`
indirection returns an untyped value that violates strict typing. The probe
therefore reimplements the fuzzy-selection logic locally as a private helper that
reproduces the exact normalized-equality-then-`difflib.SequenceMatcher`-ratio
selection that `_best_fuzzy_index` performs, so `probe_columns` binds the same
expected->actual pairs `resolve_columns` does on a resolvable input. This
satisfies AC1 (resolver unchanged) and keeps both files well under the 500-line
cap.

New production modules (all classified T2 in `quality-tiers.yml`):
- `src/etl_column_probe.py` — non-raising `probe_columns` + `ProbeResult`.
- `src/schema_matching.py` — `MismatchReport`, `MatchResult`, `find_best_match`,
  `find_best_match_in_registry`, and the report renderer.

Hard constraints carried into every task:
- Additive only. Do NOT modify `src/normalize_le.py`, `src/load_aop.py`,
  `src/_load_aop_helpers.py`, transforms, GUI, CLI, or any Feature A public
  contract. `resolve_columns` retains its raising contract unchanged.
- No new runtime dependency (stdlib `difflib` + Feature A model). Do NOT add
  `asteval`. `hypothesis` is a dev/test dependency only.
- Every new/edited file < 500 lines.
- Tests must not create temp files or touch network/real filesystem. The matcher
  is tested with in-process `SchemaDefinition` objects; the registry-integrated
  path is tested via an in-memory `SchemaFileStore` fake (the Feature A injectable
  store Protocol), never real disk.
- Determinism: no wall-clock, no RNG; deterministic tie-breaking (newer version,
  then name).
- Per-batch budget: at most 3 production files and 3 test files per phase.

### Protected files (regression target for P5-T4)

The following paths MUST NOT change. Phase 5 proves
`git diff --name-only main -- <these paths>` is empty:

- `src/normalize_le.py`
- `src/load_aop.py`
- `src/_load_aop_helpers.py`
- `src/etl_columns.py`
- `src/etl_key.py`
- `src/etl_totals.py`
- `src/schema_model.py`
- `src/schema_serialization.py`
- `src/_schema_json_helpers.py`
- `src/schema_settings.py`
- `src/schema_registry.py`
- `src/schemas/default_aop.schema.json`
- `src/schemas/default_le.schema.json`

### Evidence location invariant

All evidence artifacts resolve to
`docs/features/active/2026-05-30-schema-matching-and-discovery-42/evidence/<kind>/`
per `evidence-and-timestamp-conventions`. Non-canonical paths (e.g.
`artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`) are forbidden and
must be rejected and substituted. In this plan `<FEATURE>` denotes
`docs/features/active/2026-05-30-schema-matching-and-discovery-42`.

## Implementation Plan (Atomic Tasks)

### Phase 0 — Baseline Capture & Policy Read

- [x] [P0-T1] Read the repository policy files in the order listed under "Required References" above and record the read.
  - Acceptance: `<FEATURE>/evidence/baseline/phase0-instructions-read.md` exists and contains `Timestamp:`, `Policy Order:`, and an explicit list of every file read (the eight files in "Required References").

- [x] [P0-T2] Capture the baseline Black formatting state of the repository.
  - Command: `poetry run black --check .`
  - Acceptance: `<FEATURE>/evidence/baseline/black-baseline.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (pass/fail and count of files that would be reformatted).

- [x] [P0-T3] Capture the baseline Ruff lint state of the repository.
  - Command: `poetry run ruff check .`
  - Acceptance: `<FEATURE>/evidence/baseline/ruff-baseline.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (error count).

- [x] [P0-T4] Capture the baseline Pyright type-check state of the repository.
  - Command: `poetry run pyright`
  - Acceptance: `<FEATURE>/evidence/baseline/pyright-baseline.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` (error/warning counts).

- [x] [P0-T5] Capture the baseline Pytest + coverage state of the repository.
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `<FEATURE>/evidence/baseline/pytest-baseline.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` including the numeric baseline total line-coverage percent and branch-coverage percent and the passed/failed test counts. This is the green-suite reference for AC8.

### Phase 1 — Non-Raising Column Probe (AC1)

- [x] [P1-T1] Implement `ProbeResult` (frozen dataclass) and `probe_columns(actual, expected, *, threshold=DEFAULT_THRESHOLD) -> ProbeResult` in new file `src/etl_column_probe.py`. Import ONLY the PUBLIC symbols `normalize_name` and `DEFAULT_THRESHOLD` from `src/etl_columns.py`. Do NOT import the private `_best_fuzzy_index` (or any other `_`-prefixed symbol) from `src/etl_columns.py`: a cross-module private import fails `poetry run pyright` strict mode under `reportPrivateUsage`, the resolver file may not be edited to expose a public alias (AC1 requires it byte-for-byte unchanged), no `# pyright: ignore[reportPrivateUsage]` is pre-authorized in `.claude/rules/python-suppressions.md`, and `getattr` indirection returns an untyped value that violates strict typing. Instead, reimplement the fuzzy-selection logic locally in `src/etl_column_probe.py` as a private, fully type-annotated helper (e.g. `_best_fuzzy_index(expected_norm: str, actual_norms: list[str], available: list[int], threshold: float) -> int | None`) that reproduces the EXACT selection logic of the resolver's helper: first return the earliest available index whose normalized actual name is exactly equal to `expected_norm`; otherwise return the available index with the highest `difflib.SequenceMatcher(None, expected_norm, actual_norms[index]).ratio()` that meets `threshold`, using a strict greater-than comparison so ties resolve to the earliest candidate. Run resolution in the same two passes `resolve_columns` uses (position pass binding expected columns whose normalized name equals the actual at the same index, then the fuzzy pass over remaining unbound columns using the local helper) so that on a fully-resolvable input the probe binds the identical expected->actual pairs. `ProbeResult` carries `matched: dict[str, str]` (expected canonical -> actual), `unmatched_expected: list[str]`, and `unmatched_actual: list[str]`; the function returns partial results instead of raising when a required column cannot bind.
  - Preconditions: `src/etl_columns.py` is NOT modified; only the public `normalize_name` and `DEFAULT_THRESHOLD` are importable and used from it; the private `_best_fuzzy_index` is NOT imported from it.
  - Acceptance: `src/etl_column_probe.py` exists, is < 500 lines, has module/class/function docstrings per the commenting policy, fully type-annotated, imports no `_`-prefixed symbol from `src/etl_columns.py`; `from src.etl_column_probe import ProbeResult, probe_columns` imports cleanly and `poetry run pyright` reports no `reportPrivateUsage` for this module.

- [x] [P1-T2] Add the T2 classification entries for `src/etl_column_probe.py` to `quality-tiers.yml` (contributes to AC8).
  - Acceptance: `quality-tiers.yml` contains `src/etl_column_probe.py: T2` under `projects:` with a short rationale comment.

- [x] [P1-T3] Create `tests/test_etl_column_probe.py` covering: a fully matched set (empty `unmatched_expected`/`unmatched_actual`), a partial match (some required unmatched, returned without raising), an all-unmatched set, extra/unrecognized actual columns reported in `unmatched_actual`, threshold boundary behavior, and an explicit assertion that `probe_columns` never raises on a mismatch. Each test follows Arrange-Act-Assert with a descriptive name/docstring.
  - Preconditions: no temp files, no filesystem, no network.
  - Acceptance: `tests/test_etl_column_probe.py` exists and asserts the three `ProbeResult` fields for each scenario.

- [x] [P1-T4] Add a resolver-parity test in `tests/test_etl_column_probe.py` asserting that on a fully-resolvable input (one where `resolve_columns` does not raise), `probe_columns(actual, expected)` produces the same expected->actual bindings as `resolve_columns(actual, expected)`. Build at least one case that exercises the fuzzy pass (a typo/variant actual name above threshold) and one position-pass case, and assert `probe_result.matched == resolve_mapping` and `set(probe_result.unmatched_actual) == set(resolve_extras)` for each. This verifies the locally reimplemented fuzzy helper reproduces `resolve_columns` selection. Arrange-Act-Assert with a descriptive name/docstring; no temp files, no filesystem, no network.
  - Acceptance: the parity test imports `resolve_columns` from `src.etl_columns` and `probe_columns` from `src.etl_column_probe`, and asserts byte-equal `matched` mapping (and matching unmatched-actual sets) on each fully-resolvable input.

- [x] [P1-T5] Add a regression test asserting `resolve_columns` behavior is unchanged: it still raises `ValueError` naming the unmatched required column(s) for an unresolvable input, and returns the same `(mapping, extras)` for a resolvable input. Place in `tests/test_etl_column_probe.py` or a clearly named test in the existing resolver test module without modifying production code.
  - Acceptance: test asserts `resolve_columns` raises `ValueError` on the unresolvable case (AC1 raising contract preserved).

- [x] [P1-T6] Run the Python toolchain loop for Phase 1 changes (format -> lint -> type-check -> test) and restart on any failure or file change until one clean pass.
  - Commands: `poetry run black .`; `poetry run ruff check .`; `poetry run pyright`; `poetry run pytest tests/test_etl_column_probe.py --cov=src.etl_column_probe --cov-branch --cov-report=term-missing`
  - Acceptance: all four stages pass in a single pass; `src/etl_column_probe.py` shows >= 85% line and >= 75% branch coverage in the run output.

### Phase 2 — Mismatch Report (AC5, AC6)

- [x] [P2-T1] Implement `MismatchReport` (typed, frozen dataclass) in new file `src/schema_matching.py`. It holds, per unmatched required column: canonical name, declared aliases (from `ColumnSpec.aliases`), and up to N closest actual candidates with `difflib` similarity scores (best ratios below threshold), plus the list of unrecognized actual columns. Add a `render() -> str` method producing a concise, professional, human-readable explanation (tonality policy applies: no hyperbole, no humor).
  - Preconditions: imports only stdlib + Feature A model + `src.etl_column_probe`; does not import or modify loaders/GUI/CLI.
  - Acceptance: `src/schema_matching.py` exists, < 500 lines, fully type-annotated with docstrings; `MismatchReport.render()` returns a `str`.

- [x] [P2-T2] Add the T2 classification entry for `src/schema_matching.py` to `quality-tiers.yml` (contributes to AC8).
  - Acceptance: `quality-tiers.yml` contains `src/schema_matching.py: T2` under `projects:` with a short rationale comment.

- [x] [P2-T3] Create `tests/test_schema_matching_report.py` covering `MismatchReport`: an unmatched required column lists its canonical name, its declared aliases, and the closest actual candidates with descending similarity scores capped at N; unrecognized actual columns are listed; `render()` returns a non-empty string naming each unmatched required column and its closest candidate. Use in-process `SchemaDefinition`/`ColumnSpec` objects only.
  - Acceptance: tests assert the structured fields and that `render()` output contains each unmatched required canonical name.

- [x] [P2-T4] Run the Python toolchain loop for Phase 2 changes (format -> lint -> type-check -> test) and restart on any failure or file change until one clean pass.
  - Commands: `poetry run black .`; `poetry run ruff check .`; `poetry run pyright`; `poetry run pytest tests/test_schema_matching_report.py --cov=src.schema_matching --cov-branch --cov-report=term-missing`
  - Acceptance: all four stages pass in a single pass; the report code paths in `src/schema_matching.py` exercised by these tests pass without error.

### Phase 3 — Best-Match Scoring (AC2, AC3)

- [x] [P3-T1] Implement `MatchResult` (frozen dataclass: `schema: SchemaDefinition | None`, `score: float`, `report: MismatchReport`) and `find_best_match(headers, schemas, *, threshold=DEFAULT_THRESHOLD) -> MatchResult` in `src/schema_matching.py`. Scoring is the fraction of required essential columns matched (a required column matches when any of its canonical name or aliases resolves to an actual header via `probe_columns`/the shared fuzzy helpers). Ties break deterministically by newer schema `version`, then by name. No wall-clock, no RNG.
  - Preconditions: reuses the Phase 1 probe and Phase 2 report; does not modify `etl_columns.py` or Feature A modules.
  - Acceptance: `find_best_match` returns a `MatchResult` whose `score` is the coverage fraction and whose `schema` is the highest-scoring candidate; documented schema-acceptance policy default recorded in a docstring.

- [x] [P3-T2] Create `tests/test_schema_matching_best.py` covering: a clear best match among multiple schemas; the LE-drift scenario from the user story (two renamed required columns -> LE selected with a sub-threshold score and a report naming the two unmatched columns with closest candidates); empty schema list returns `schema=None`; alias-based matching counts toward coverage.
  - Acceptance: tests assert selected schema identity, the numeric score relationship, and report contents for the drift scenario.

- [x] [P3-T3] Add a tie-break determinism test: two schemas with equal coverage score where the newer `version` wins, and a second pair with equal version where the lexicographically-ordered name wins; assert repeated calls return identical results (AC3 determinism).
  - Acceptance: test asserts deterministic, version-then-name tie resolution and identical output across repeated calls.

- [x] [P3-T4] Add a `hypothesis` property test for scoring determinism (T2 requirement, AC7) in `tests/test_schema_matching_property.py`: for generated header lists and schema sets, `find_best_match` called twice on the same inputs returns identical `(schema, score)`; print the seed on failure per the determinism-infrastructure policy. No wall-clock, no `Date.now`/`time` usage.
  - Acceptance: `tests/test_schema_matching_property.py` exists and uses `hypothesis` strategies; the property asserts call-to-call equality of the result.

- [x] [P3-T5] Run the Python toolchain loop for Phase 3 changes (format -> lint -> type-check -> test) and restart on any failure or file change until one clean pass.
  - Commands: `poetry run black .`; `poetry run ruff check .`; `poetry run pyright`; `poetry run pytest tests/test_schema_matching_best.py tests/test_schema_matching_property.py --cov=src.schema_matching --cov-branch --cov-report=term-missing`
  - Acceptance: all four stages pass in a single pass.

### Phase 4 — Registry-Integrated Match (AC4)

- [x] [P4-T1] Implement `find_best_match_in_registry(headers, registry, *, threshold=DEFAULT_THRESHOLD) -> MatchResult` in `src/schema_matching.py`. It loads candidate schemas from the Feature A `SchemaRegistry` (via `list_schemas`/`load`) and applies `find_best_match`. Use only the public `SchemaRegistry` API; do not modify `src/schema_registry.py`.
  - Acceptance: function exists, fully typed, and delegates scoring to `find_best_match`; `src/schema_matching.py` remains < 500 lines (split a helper to a `_schema_matching_helpers.py` sibling if it would exceed the cap, classifying it T2 in `quality-tiers.yml`).

- [x] [P4-T2] Create `tests/test_schema_matching_registry.py` exercising the registry path through an in-memory `SchemaFileStore` fake (dict-backed implementation of the Feature A Protocol) seeded with serialized schemas — no real disk, no temp files. Cover: best match selected across registry-loaded candidates; empty registry returns `schema=None`.
  - Acceptance: test constructs `SchemaRegistry` with the in-memory fake store and asserts `find_best_match_in_registry` returns the expected `MatchResult`.

- [x] [P4-T3] Run the Python toolchain loop for Phase 4 changes (format -> lint -> type-check -> test) and restart on any failure or file change until one clean pass.
  - Commands: `poetry run black .`; `poetry run ruff check .`; `poetry run pyright`; `poetry run pytest tests/test_schema_matching_registry.py --cov=src.schema_matching --cov-branch --cov-report=term-missing`
  - Acceptance: all four stages pass in a single pass.

### Phase 5 — Final QA Loop, Coverage Delta, and Regression (AC7, AC8)

- [x] [P5-T1] Run the full Black formatting check across the repository and persist the result.
  - Command: `poetry run black --check .`
  - Acceptance: `<FEATURE>/evidence/qa-gates/black-final.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`; EXIT_CODE is 0 (rerun the loop from Black if any prior stage reformatted files).

- [x] [P5-T2] Run the full Ruff lint check across the repository and persist the result.
  - Command: `poetry run ruff check .`
  - Acceptance: `<FEATURE>/evidence/qa-gates/ruff-final.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`; 0 errors.

- [x] [P5-T3] Run the full Pyright (strict) type check across the repository and persist the result.
  - Command: `poetry run pyright`
  - Acceptance: `<FEATURE>/evidence/qa-gates/pyright-final.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`; 0 errors for the new modules and no new errors introduced relative to the P0-T4 baseline.

- [x] [P5-T4] Run the full Pytest suite with coverage across the repository and persist the result.
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `<FEATURE>/evidence/qa-gates/pytest-final.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` including numeric post-change total line and branch coverage percentages and passed/failed counts; the full existing suite is green (AC8) and EXIT_CODE is 0.

- [x] [P5-T5] Capture per-module coverage for the new modules and assert the new-code thresholds.
  - Command: `poetry run pytest --cov=src.etl_column_probe --cov=src.schema_matching --cov-branch --cov-report=term-missing`
  - Acceptance: `<FEATURE>/evidence/qa-gates/newcode-coverage.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` recording the line and branch coverage for `src/etl_column_probe.py` and `src/schema_matching.py` (and any helper sibling); both modules show >= 85% line and >= 75% branch (AC7).

- [x] [P5-T6] Write the coverage-delta verification comparing baseline (P0-T5) to post-change (P5-T4) and the new-code coverage (P5-T5).
  - Acceptance: `<FEATURE>/evidence/qa-gates/coverage-delta.<ISO-8601>.md` records baseline total coverage, post-change total coverage, and new/changed-code coverage with explicit numeric values, and asserts no regression on changed lines and new code meeting >= 85% line / >= 75% branch. If any required value is unavailable, the verdict is remediation-required, not PASS.

- [x] [P5-T7] Verify no protected file changed relative to `main`.
  - Command: `git diff --name-only main -- src/normalize_le.py src/load_aop.py src/_load_aop_helpers.py src/etl_columns.py src/etl_key.py src/etl_totals.py src/schema_model.py src/schema_serialization.py src/_schema_json_helpers.py src/schema_settings.py src/schema_registry.py src/schemas/default_aop.schema.json src/schemas/default_le.schema.json`
  - Acceptance: `<FEATURE>/evidence/regression-testing/protected-files-diff.<ISO-8601>.md` exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:`; the command output is empty (AC1, AC8 — Feature A contracts and existing loaders unchanged).

- [x] [P5-T8] Verify `quality-tiers.yml` classifies every new module and that no project is unclassified.
  - Acceptance: `<FEATURE>/evidence/qa-gates/tier-classification.<ISO-8601>.md` records that `src/etl_column_probe.py`, `src/schema_matching.py`, and any helper sibling are present as `T2`; confirms AC8 tier requirement.

## Test Plan

- Unit: `tests/test_etl_column_probe.py` (probe matched/partial/unmatched/extra,
  threshold boundary, non-raising; resolver-parity equality on resolvable inputs;
  resolver-unchanged regression),
  `tests/test_schema_matching_report.py` (typed report fields + `render()`),
  `tests/test_schema_matching_best.py` (best-match selection, LE-drift scenario,
  empty list, alias coverage), `tests/test_schema_matching_registry.py`
  (registry path via in-memory store fake).
- Property: `tests/test_schema_matching_property.py` (`hypothesis` scoring
  determinism, seed printed on failure).
- Integration: registry-integrated match exercised only through the Feature A
  injectable in-memory `SchemaFileStore` fake; no real disk, no network, no temp
  files.
- Coverage evidence:
  - Baseline: `<FEATURE>/evidence/baseline/pytest-baseline.<ISO-8601>.md`.
  - Post-change: `<FEATURE>/evidence/qa-gates/pytest-final.<ISO-8601>.md`.
  - New-code: `<FEATURE>/evidence/qa-gates/newcode-coverage.<ISO-8601>.md`.
  - Comparison: `<FEATURE>/evidence/qa-gates/coverage-delta.<ISO-8601>.md`.

## Open Questions / Notes

- Module-placement decision recorded above: `probe_columns` lives in the new
  sibling `src/etl_column_probe.py` rather than in `src/etl_columns.py`, so the
  existing resolver file is not edited and `resolve_columns` stays byte-for-byte
  unchanged (AC1).
- Private-symbol revision (v1.1): the probe imports only the public
  `normalize_name` and `DEFAULT_THRESHOLD` from `src/etl_columns.py` and
  reimplements the fuzzy-selection helper locally. Importing the private
  `_best_fuzzy_index` across modules fails Pyright strict mode
  (`reportPrivateUsage`) and cannot be resolved within the hard constraints
  (resolver is protected/byte-for-byte unchanged, no pre-authorized
  `reportPrivateUsage` suppression, `getattr` indirection is untyped). The new
  `[P1-T4]` parity test asserts the local reimplementation binds the same
  expected->actual pairs as `resolve_columns` on resolvable inputs.
- The validator gate (`mcp__drm-copilot__validate_orchestration_artifacts`,
  `artifact_type: "plan"`) and the executor preflight are run by the orchestrator,
  not by the planner. This plan is not self-approved.
