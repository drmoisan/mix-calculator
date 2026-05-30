# schema-model-and-registry — Plan

- **Issue:** #41
- **Parent:** Epic #40 (configurable-schema-subsystem)
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30T12-15
- **Status:** Ready for preflight
- **Version:** 1.0
- **Work Mode:** full-feature

## Required References

Comply with (do not duplicate) the repository policies in the order defined by
`policy-compliance-order`:

1. `CLAUDE.md`
2. `.claude/rules/general-code-change.md`
3. `.claude/rules/general-unit-test.md`
4. `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`
5. `.claude/rules/self-explanatory-code-commenting.md`
6. `.claude/rules/quality-tiers.md`
7. `.claude/rules/tonality.md`

All work must comply with these policies. The atomic-plan, evidence-location, and
timestamp conventions in the `atomic-plan-contract` and
`evidence-and-timestamp-conventions` skills govern this plan.

## Scope and Hard Constraints

- Additive only. Do NOT modify `src/normalize_le.py`, `src/load_aop.py`,
  `src/_load_aop_helpers.py`, `src/etl_columns.py`, `src/etl_key.py`,
  `src/etl_totals.py`, transforms, GUI, or CLI. The existing suite must stay green (AC8).
- New runtime dependencies are prohibited. Use only stdlib `json`, `dataclasses`,
  `pathlib`, `os`, `sys`, and `typing`. Do NOT add `asteval` (Feature C).
- Every new production, test, or reusable file must stay under 500 lines; split if needed.
- Tests must not create temp files or touch network/real filesystem. Serialization is
  tested via pure string round-trips; directory resolution via injected environment and
  platform seams; registry I/O via an injected reader/writer abstraction (callables or a
  small `Protocol`). At least one `hypothesis` property test covers the JSON round-trip (T2).
- Per-batch budget: at most 3 production files and 3 test files per implementation batch.
  Phases below are sized to fit this budget.
- Toolchain per task: Black → Ruff → Pyright (strict) → Pytest with coverage.

## Evidence Locations (non-overridable)

All evidence artifacts resolve under the feature folder canonical scheme
`docs/features/active/2026-05-30-schema-model-and-registry-41/evidence/<kind>/`:

- Phase 0 policy-read evidence and baselines → `evidence/baseline/`
- Final QA gate evidence → `evidence/qa-gates/`
- Regression / existing-suite-green evidence → `evidence/regression-testing/`
- Coverage delta verification → `evidence/qa-gates/`

`EVIDENCE_LOCATION_OVERRIDE_REJECTED:` the delegation prompt's reference to
`artifacts/python/` for coverage *evidence* is rejected and replaced with the canonical
`evidence/baseline/` and `evidence/qa-gates/` paths. The raw coverage tool output files
(`--cov-report=xml:artifacts/python/coverage.xml`, `--cov-report=html:artifacts/python/htmlcov`)
may still be written under `artifacts/python/` as non-evidence tool output, but the
machine-checkable coverage *evidence artifacts* (with `Timestamp`/`Command`/`EXIT_CODE`/
`Output Summary` and numeric coverage headlines) live only under the canonical
`evidence/<kind>/` paths above.

---

## Implementation Plan (Atomic Tasks)

### Phase 0 — Baseline Capture and Policy Read

- [x] [P0-T1] Read the policy files in the required order (`CLAUDE.md`,
  `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`,
  `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`,
  `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/quality-tiers.md`,
  `.claude/rules/tonality.md`) and record a policy-read evidence artifact.
  - Acceptance: `evidence/baseline/phase0-instructions-read.md` exists and contains
    `Timestamp:`, `Policy Order:`, and an explicit list of every file read.
- [x] [P0-T2] Capture the baseline Black formatting state.
  - Command: `poetry run black --check .`
  - Acceptance: `evidence/baseline/black.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, and `Output Summary:` (pass/fail and file count).
- [x] [P0-T3] Capture the baseline Ruff lint state.
  - Command: `poetry run ruff check .`
  - Acceptance: `evidence/baseline/ruff.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, and `Output Summary:` (error count).
- [x] [P0-T4] Capture the baseline Pyright strict state.
  - Command: `poetry run pyright`
  - Acceptance: `evidence/baseline/pyright.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, and `Output Summary:` (error/warning counts).
- [x] [P0-T5] Capture the baseline Pytest run with coverage to establish the pre-change
    line and branch coverage headline.
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
  - Acceptance: `evidence/baseline/pytest-coverage.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, and `Output Summary:` recording numeric baseline TOTAL line
    coverage percent and branch coverage percent, plus the passed/failed test counts.

### Phase 1 — Schema Model Dataclasses

- [x] [P1-T1] Create `src/schema_model.py` defining the frozen dataclasses `ColumnSpec`
    (`canonical_name`, `role`, `required`, `aliases`, `numeric`, `sentinel_clean`),
    `MeasureAggregation` (`measure`, `mode` ∈ {additive, select_from}, optional
    `select_values`), `DedupPolicy` (`mode` ∈ {none, collapse}, optional
    `discriminator_column`, `measure_aggregations`), `DerivedColumnSpec`
    (`name`, `expression`, optional `copy_from`), `KeySpec` (ordered `columns`,
    `sku_coercion`), and `FillRule` (`total`, ordered `components`), each with a class
    docstring per the commenting policy.
  - Acceptance: `src/schema_model.py` defines all six nested frozen dataclasses with full
    type annotations; file is under 500 lines; module imports only stdlib.
- [x] [P1-T2] Add the `SchemaDefinition` frozen dataclass to `src/schema_model.py` with
    identity fields (`name`, `version`, `description`), `source_sheet_hints`, `header_row`,
    `columns`, `key`, `dedup`, `derived_columns`, `fill_rules`, and `drop_columns`,
    including a docstring documenting the JSON shape and the as-built quirk representation.
  - Acceptance: `SchemaDefinition` exists in `src/schema_model.py` with full type
    annotations and references the nested dataclasses from P1-T1.
- [x] [P1-T3] Implement the `__post_init__` invariants in `src/schema_model.py`: non-empty
    `name`; non-empty `version`; every `key.columns`, `dedup.measure_aggregations`,
    `derived_columns` (`copy_from` and any declared dependency name stored structurally),
    and `fill_rules` reference names a declared `ColumnSpec.canonical_name`; and a
    `discriminator_column` is present and declared when `dedup.mode == "collapse"`. Each
    violation raises a `SchemaValidationError` (defined in this module) with a descriptive
    message naming the offending reference (AC4).
  - Acceptance: `SchemaValidationError` is defined and `__post_init__` raises it with a
    specific message for each invariant; no bare `KeyError`/`ValueError`.
- [x] [P1-T4] Create `tests/test_schema_model.py` covering positive construction of a
    minimal valid `SchemaDefinition`, and AAA-structured negative tests asserting
    `SchemaValidationError` for empty `name`, missing `version`, a `key.columns` entry that
    names an undeclared column, a `derived_columns` reference to an undeclared column, a
    `fill_rules` reference to an undeclared column, a `dedup.measure_aggregations` entry
    naming an undeclared measure, and `collapse` mode with a missing/undeclared
    `discriminator_column`.
  - Acceptance: `tests/test_schema_model.py` runs green; each negative test asserts the
    specific `SchemaValidationError` message substring; no temp files created.
- [x] [P1-T5] Run the Python toolchain loop for the Phase 1 files and confirm a clean pass.
  - Command: `poetry run black src/schema_model.py tests/test_schema_model.py` then
    `poetry run ruff check src/schema_model.py tests/test_schema_model.py` then
    `poetry run pyright src/schema_model.py tests/test_schema_model.py` then
    `poetry run pytest tests/test_schema_model.py`
  - Acceptance: all four stages exit 0 in a single pass after any required re-runs.

### Phase 2 — Typed JSON Serialization Adapter

- [x] [P2-T1] Create `src/schema_serialization.py` defining `schema_to_json(schema:
    SchemaDefinition) -> str` that produces deterministic, key-ordered JSON via a typed
    conversion of the dataclass tree (no untyped `dict[str, Any]` in the public signature),
    with a module docstring describing the typed-adapter pattern (mirroring `pandas_io.py`).
  - Acceptance: `schema_to_json` exists with full annotations; returns `str`; file under
    500 lines; stdlib `json`/`dataclasses` only.
- [x] [P2-T2] Add `schema_from_json(text: str) -> SchemaDefinition` to
    `src/schema_serialization.py` that parses JSON behind a typed boundary and rebuilds the
    dataclass tree, raising a descriptive `SchemaSerializationError` (defined in this
    module) for malformed JSON, missing required fields, and unknown/extra keys — the
    unknown-key message must name the offending key(s) (AC2, AC3). Invariant failures from
    `__post_init__` propagate as `SchemaValidationError`.
  - Acceptance: `schema_from_json` exists with full annotations; raises
    `SchemaSerializationError` with a specific message for each malformed/incomplete/
    unknown-key case; no bare `KeyError`/`ValueError`.
- [x] [P2-T3] Create `tests/test_schema_serialization.py` covering: a positive
    round-trip (`schema_from_json(schema_to_json(s)) == s`) on a representative schema; an
    AAA negative test for malformed JSON text; for missing required field; for an unknown
    top-level key (asserting the key name in the message); and for an unknown nested key.
  - Acceptance: `tests/test_schema_serialization.py` runs green; each negative test asserts
    the specific error type and message substring; no temp files created.
- [x] [P2-T4] Add a `hypothesis` property test to `tests/test_schema_serialization.py` that
    generates valid `SchemaDefinition` instances from a strategy and asserts the JSON
    round-trip is lossless (`schema_from_json(schema_to_json(s)) == s`) for every generated
    case, printing the failing example on failure (T2 property-test requirement).
  - Acceptance: the property test runs green using `hypothesis`; `hypothesis` is already an
    available test dependency (no new runtime dependency added).
- [x] [P2-T5] Run the Python toolchain loop for the Phase 2 files and confirm a clean pass.
  - Command: `poetry run black src/schema_serialization.py tests/test_schema_serialization.py`
    then `poetry run ruff check src/schema_serialization.py tests/test_schema_serialization.py`
    then `poetry run pyright src/schema_serialization.py tests/test_schema_serialization.py`
    then `poetry run pytest tests/test_schema_serialization.py`
  - Acceptance: all four stages exit 0 in a single pass after any required re-runs.

### Phase 3 — Registry Directory Resolution (Settings Seam)

- [x] [P3-T1] Create `src/schema_settings.py` defining a pure
    `resolve_registry_dir(*, env: Mapping[str, str], platform: str, home: Path) -> Path`
    (and the `MIX_CALCULATOR_SCHEMA_DIR` constant) that returns the env-override path when
    set, otherwise a per-user default (`%APPDATA%`-based on Windows, XDG-style otherwise),
    independent of any `.db` path. Environment, platform marker, and home directory are
    injected so no real filesystem or `os.environ` access occurs during resolution (AC5).
  - Acceptance: `resolve_registry_dir` exists with full annotations and reads only its
    injected seams; file under 500 lines; stdlib `pathlib`/`typing` only.
- [x] [P3-T2] Create `tests/test_schema_settings.py` with AAA-structured tests asserting:
    the env override wins when `MIX_CALCULATOR_SCHEMA_DIR` is set; the Windows default uses
    the injected `%APPDATA%`; the non-Windows default uses the injected XDG/home path; and
    resolution is independent of any database path. All seams are injected; no disk access.
  - Acceptance: `tests/test_schema_settings.py` runs green; no `os.environ` mutation, no
    temp files, no real filesystem reads.
- [x] [P3-T3] Run the Python toolchain loop for the Phase 3 files and confirm a clean pass.
  - Command: `poetry run black src/schema_settings.py tests/test_schema_settings.py` then
    `poetry run ruff check src/schema_settings.py tests/test_schema_settings.py` then
    `poetry run pyright src/schema_settings.py tests/test_schema_settings.py` then
    `poetry run pytest tests/test_schema_settings.py`
  - Acceptance: all four stages exit 0 in a single pass after any required re-runs.

### Phase 4 — Schema Registry (Injectable File-I/O Boundary)

- [x] [P4-T1] Create `src/schema_registry.py` defining a small file-I/O `Protocol` (e.g.
    `SchemaFileStore` with `list_files(dir) -> list[str]`, `read_text(path) -> str`,
    `write_text(path, text) -> None`, `exists(path) -> bool`) and a default real-disk
    implementation kept isolated from the pure logic, with module and class docstrings.
  - Acceptance: the `Protocol` and a default implementation exist in
    `src/schema_registry.py` with full annotations; the pure registry logic depends only on
    the `Protocol`, never on `open`/`pathlib` I/O directly.
- [x] [P4-T2] Add the `SchemaRegistry` class to `src/schema_registry.py` with
    `list_schemas() -> list[str]`, `load(name: str) -> SchemaDefinition`,
    `save(schema: SchemaDefinition) -> None`, and `load_bundled_default(name: str) ->
    SchemaDefinition`, taking the resolved registry directory and the file-store
    `Protocol` via constructor injection and delegating JSON parsing to
    `schema_serialization`. `load_bundled_default` reads from the packaged `src/schemas/`
    directory through the same injectable boundary (AC6).
  - Acceptance: `SchemaRegistry` exposes the four methods with full annotations; all file
    access flows through the injected store; file under 500 lines (split a helper module if
    needed to stay under the limit).
- [x] [P4-T3] Create `tests/test_schema_registry.py` with an in-memory fake implementing
    the file-store `Protocol` (backed by an in-process dict, no disk), covering: `save`
    then `load` round-trips a schema; `list_schemas` returns the saved schema names; `load`
    of a missing name raises a descriptive error; and `load_bundled_default` reads a
    fixture schema served by the fake store. All tests use AAA structure.
  - Acceptance: `tests/test_schema_registry.py` runs green using the in-memory fake; no
    real files, no temp files, no network.
- [x] [P4-T4] Run the Python toolchain loop for the Phase 4 files and confirm a clean pass.
  - Command: `poetry run black src/schema_registry.py tests/test_schema_registry.py` then
    `poetry run ruff check src/schema_registry.py tests/test_schema_registry.py` then
    `poetry run pyright src/schema_registry.py tests/test_schema_registry.py` then
    `poetry run pytest tests/test_schema_registry.py`
  - Acceptance: all four stages exit 0 in a single pass after any required re-runs.

### Phase 5 — Bundled Default Schemas (AOP and LE)

- [x] [P5-T1] Create `src/schemas/default_aop.schema.json` encoding the current AOP schema
    from `src/_load_aop_helpers.py`: the `SOURCE_COLUMNS` canonical set and order
    (`KEY`, `Customer`, `SKU Descripiton`, `SKU #`, `Customer Master`, `Type`, `Jan`..`Dec`,
    `YTD`, `Q1`..`Q4`, `YTG`, `Super Category`, `PPG`), per-column roles (dimensions vs.
    numeric measures from `NUMERIC_COLS`), `required` flags (`KEY` and `YTG` optional per
    `EXPECTED_COLUMNS`), `sentinel_clean` on `LABEL_COLUMNS` (`Super Category`, `PPG`), the
    `key` (`Customer`, `SKU #`, `Type` with `sku_coercion` true), `dedup.mode == "none"`
    (AOP does not collapse), the AOP `fill_rules` (`YTD <- Jan..Dec`, each `Qn <- its
    months`, `YTG <- May..Dec`), empty `derived_columns`, and empty `drop_columns`.
  - Acceptance: the file is valid JSON and parses via `schema_from_json` into a
    `SchemaDefinition` without raising; it is not referenced by any existing loader/CLI.
- [x] [P5-T2] Create `src/schemas/default_le.schema.json` encoding the current LE schema
    from `src/normalize_le.py`: the canonical column set (`Customer`, `SKU Descripiton`,
    `SKU #`, `Type`, `GtN Mapping`, `Jan`..`Dec`, `FY`, `Q1`..`Q4`, plus the dropped
    `YTD/YTG` source column), the `key` (`Customer`, `SKU #`, `Type`, `sku_coercion` true),
    `dedup.mode == "collapse"` with `discriminator_column == "YTD/YTG"` and additive
    aggregation for the `SUM_COLUMNS` measures (months + `FY` + quarters), the derived
    `YTG` (`expression` = sum of `May..Dec`), the `Super Category` derived column with
    `copy_from == "PPG"` (the as-built quirk), the LE `fill_rules` (`FY <- Jan..Dec`, each
    `Qn <- its months`), and `drop_columns == ["YTD/YTG"]`.
  - Acceptance: the file is valid JSON and parses via `schema_from_json` into a
    `SchemaDefinition` without raising; the `Super Category <- PPG` quirk, derived `YTG`,
    additive dedup, and dropped `YTD/YTG` are all structurally present.
- [x] [P5-T3] Create `tests/test_default_schemas.py` asserting that
    `default_aop.schema.json` and `default_le.schema.json` (loaded through an in-memory
    file store, not real disk, by reading the file text once into the fake at test setup
    via a packaged-resource read that is itself the only allowed read) parse into
    `SchemaDefinition` objects whose declared columns, column order, key composition, dedup
    policy, derived definitions, fill rules, drop columns, and sentinel-clean labels match
    the canonical AOP/LE sets documented in `_load_aop_helpers.py` and `normalize_le.py`
    (AC7). Include explicit assertions for the LE additive dedup, derived `YTG = sum(May..
    Dec)`, dropped `YTD/YTG`, and the `Super Category <- PPG` quirk.
  - Acceptance: `tests/test_default_schemas.py` runs green; assertions name the exact
    canonical column lists; no temp files are created and no SQLite/Excel I/O occurs.
- [x] [P5-T4] Run the Python toolchain loop for the Phase 5 files and confirm a clean pass.
  - Command: `poetry run black tests/test_default_schemas.py` then
    `poetry run ruff check tests/test_default_schemas.py` then
    `poetry run pyright tests/test_default_schemas.py` then
    `poetry run pytest tests/test_default_schemas.py`
  - Acceptance: all four stages exit 0 in a single pass after any required re-runs.

### Phase 6 — Tier Classification

- [x] [P6-T1] Update `quality-tiers.yml` to classify the new modules as T2 (Core):
    `src/schema_model.py`, `src/schema_serialization.py`, `src/schema_settings.py`,
    `src/schema_registry.py` (and any helper module created in P4-T2), with a comment block
    documenting the T2 rationale consistent with the existing ETL-core entries (AC9).
  - Acceptance: every new `src/` module added by this feature has exactly one T2 entry in
    `quality-tiers.yml`; no module is left unclassified.

### Phase 7 — Final QA Loop and Coverage Evidence

- [x] [P7-T1] Run the full-repository Black format check and record the QA gate evidence.
  - Command: `poetry run black --check .`
  - Acceptance: `evidence/qa-gates/black.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE: 0`, and `Output Summary:`. If this step changes files, restart
    the loop from P7-T1.
- [x] [P7-T2] Run the full-repository Ruff lint check and record the QA gate evidence.
  - Command: `poetry run ruff check .`
  - Acceptance: `evidence/qa-gates/ruff.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE: 0`, and `Output Summary:` (0 errors).
- [x] [P7-T3] Run the full-repository Pyright strict check and record the QA gate evidence.
  - Command: `poetry run pyright`
  - Acceptance: `evidence/qa-gates/pyright.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE: 0`, and `Output Summary:` (0 errors, 0 warnings).
- [x] [P7-T4] Run the full Pytest suite with coverage and record the post-change coverage
    evidence, confirming the existing suite remains green (AC8).
  - Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing
    --cov-report=xml:artifacts/python/coverage.xml`
  - Acceptance: `evidence/qa-gates/pytest-coverage.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE: 0`, and `Output Summary:` recording numeric post-change TOTAL
    line and branch coverage percent and the passed/failed counts (all existing tests
    pass). If this step changes files or fails, restart the loop from P7-T1.
- [x] [P7-T5] Verify the coverage delta and new-code thresholds and record the comparison
    evidence: report baseline line/branch coverage (from P0-T5), post-change line/branch
    coverage (from P7-T4), and the line/branch coverage of the new schema modules
    (`src/schema_model.py`, `src/schema_serialization.py`, `src/schema_settings.py`,
    `src/schema_registry.py` and any helper). Confirm new-code line coverage >= 85% and
    branch coverage >= 75%, and that no changed line regresses overall coverage.
  - Command: `poetry run pytest --cov=src.schema_model --cov=src.schema_serialization
    --cov=src.schema_settings --cov=src.schema_registry --cov-branch
    --cov-report=term-missing`
  - Acceptance: `evidence/qa-gates/coverage-delta.<timestamp>.md` exists with `Timestamp:`,
    `Command:`, `EXIT_CODE:`, and `Output Summary:` recording baseline, post-change, and
    per-module new-code numeric line and branch coverage, with an explicit pass/fail against
    the >= 85% line / >= 75% branch thresholds. If thresholds are unmet, the outcome is
    remediation-required, not PASS.
- [x] [P7-T6] Confirm no existing loader, transform, CLI, or GUI file was modified and
    record the regression evidence (AC8).
  - Command: `git diff --name-only main -- src/normalize_le.py src/load_aop.py
    src/_load_aop_helpers.py src/etl_columns.py src/etl_key.py src/etl_totals.py src/gui`
  - Acceptance: `evidence/regression-testing/no-existing-files-modified.<timestamp>.md`
    exists with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` confirming the
    command produced no output (no protected files changed).

## Test Plan

- Unit: dataclass construction and `__post_init__` invariants (`tests/test_schema_model.py`);
  JSON round-trip and descriptive error handling (`tests/test_schema_serialization.py`);
  directory resolution via injected seams (`tests/test_schema_settings.py`); registry
  list/load/save/bundled-default via an in-memory file store (`tests/test_schema_registry.py`);
  bundled-default structural parity with the canonical AOP/LE sets
  (`tests/test_default_schemas.py`).
- Property-based: `hypothesis` JSON round-trip property in `tests/test_schema_serialization.py`
  (T2 requirement).
- Integration: none in this feature (additive, no pipeline consumer yet).
- Manual/CLI: none (no new CLI surface).
- Coverage evidence:
  - Baseline: `evidence/baseline/pytest-coverage.<timestamp>.md`
  - Post-change: `evidence/qa-gates/pytest-coverage.<timestamp>.md`
  - Comparison/new-code: `evidence/qa-gates/coverage-delta.<timestamp>.md`

## Open Questions / Notes

- The delegation prompt referenced `artifacts/python/` for coverage outputs. Raw coverage
  tool output (xml/html) may be written there, but coverage *evidence artifacts* are written
  only under `evidence/<kind>/` per the non-overridable evidence-path clause. Recorded as
  `EVIDENCE_LOCATION_OVERRIDE_REJECTED` in the Evidence Locations section.
- No `issue.md` exists in the feature folder; `spec.md` and `user-story.md` are present, so
  this is a `full-feature` plan per mode-source precedence (fail-closed to `full-feature`).
- If `src/schema_registry.py` approaches the 500-line limit once docstrings are added, split
  the default real-disk `SchemaFileStore` implementation into a sibling module and add it to
  the `quality-tiers.yml` T2 entries in P6-T1.
