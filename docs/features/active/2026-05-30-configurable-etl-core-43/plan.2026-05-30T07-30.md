# configurable-etl-core — Plan

- **Issue:** #43
- **Parent:** Epic #40 (configurable-schema-subsystem)
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30T07-30
- **Status:** Ready for preflight
- **Version:** 1.0
- **Work Mode:** full-feature

## Required References

- Policy reading order (precedence): `CLAUDE.md` → `.claude/rules/general-code-change.md` → `.claude/rules/general-unit-test.md` → `.claude/rules/python.md` → `.claude/rules/python-suppressions.md` → `.claude/rules/quality-tiers.md` → `.claude/rules/self-explanatory-code-commenting.md` → `.claude/rules/tonality.md`.
- Feature documents: `spec.md`, `user-story.md` (AC1–AC11), GitHub issue #43, epic `initiative.md`, research `artifacts/research/2026-05-29-configurable-schema-subsystem-research.md` (Sections 1.4, 5.1, 5.3, 6).

**All work must comply with these policies; do not duplicate their content here.**

## Scope & Hard Constraints (binding on every task)

- **Additive only.** Do NOT modify `src/normalize_le.py`, `src/load_aop.py`, `src/_load_aop_helpers.py`, `src/etl_columns.py`, `src/etl_key.py`, `src/etl_totals.py`, `src/etl_column_probe.py`, the Feature A modules (`src/schema_model.py`, `src/schema_serialization.py`, `src/_schema_json_helpers.py`, `src/schema_settings.py`, `src/schema_registry.py`), the Feature B modules (`src/schema_matching.py`, `src/_schema_matching_helpers.py`), the bundled default schema JSON files, the mix transforms, `src/gui/**`, the CLI loaders, or `pipeline_service`. The configurable loader is a parallel additive path (Feature D wires it later).
- **Only new dependency is `asteval`**, already recorded in `pyproject.toml` (`asteval = "^1.0.8"`) and `poetry.lock` (user-approved 2026-05-30). Do NOT run `poetry add`. Add no other dependency.
- **No suppressions** beyond pre-authorized patterns. The asteval-untyped problem MUST be solved with the local stub `typings/asteval/__init__.pyi`, NOT `# type: ignore`. If any suppression appears unavoidable, STOP and escalate (do not self-author a suppression).
- **Every new file < 500 lines.** Split `src/schema_loader.py` into `src/_schema_loader_helpers.py` if it approaches the cap.
- **Tests:** no temp files, no network, no real filesystem. Reuse the existing in-memory fixtures in `tests/le_fixtures.py` and `tests/aop_fixtures.py` so parity is apples-to-apples. T1 modules require >= 1 property test per pure function (Hypothesis).
- **Determinism:** no wall-clock, no RNG. Preserve first-appearance ordering exactly like `normalize_le.normalize` (`groupby(..., sort=False)` and `drop_duplicates(keep="first")`).
- **Toolchain per code/test task:** Black → Ruff → Pyright (strict) → Pytest (+coverage). Restart from formatting on any failure or auto-fix.

## Evidence Location Invariant

All evidence MUST be written under `docs/features/active/2026-05-30-configurable-etl-core-43/evidence/<kind>/` using the canonical kinds (`baseline/`, `qa-gates/`, `regression-testing/`, `other/`). Writing to `artifacts/baselines/`, `artifacts/qa/`, `artifacts/coverage/`, or any other non-canonical path is a policy violation. Timestamps use ISO-8601 `yyyy-MM-ddTHH-mm`. The feature evidence root abbreviation `<FEAT-EV>` below expands to that canonical evidence directory.

## Parity Targets (exact-reproduction contract)

- **LE (AC1):** `SchemaLoader.load(raw_le_frame, default_le)` must equal `normalize_le.normalize(load_source(<same workbook>))`. The raw frame is the openpyxl read at `header=2` (i.e. `src.pandas_io.read_excel_sheet(buffer, sheet_name="LE-8 + 4", header=2)`); the loader internally performs resolve+rename, blank-`Customer` drop, `fill_blank_totals({"FY": months, **QUARTER_TO_MONTHS})`, `resolve_key`, collapse-by-KEY (text/dimensions from first row; SUM_COLUMNS additive), derive `YTG = sum(May..Dec)`, apply the `Super Category <- PPG` copy_from quirk, drop `YTD/YTG`, and emit the 26 LE `TARGET_COLUMNS` in order. Compare with `pandas.testing.assert_frame_equal` (`check_dtype=True`, `check_like=False`).
- **AOP (AC2):** `SchemaLoader.load(raw_aop_frame, default_aop)` must equal `load_aop(<same workbook>)` (the full validated frame: resolve+rename, blank-`Customer` drop, `fill_blank_totals` incl. optional YTG, `resolve_key`, `coerce_numeric`, `clean_label_sentinels(LABEL_COLUMNS)`, `validate_aop`, NO row collapse, NO PPG quirk, emit `TARGET_COLUMNS == SOURCE_COLUMNS`). No `transform` callable is applied. Compare with `assert_frame_equal`.
- Both raw frames are produced from the SAME in-memory workbook buffers built by `build_workbook`/`make_row` (LE) and `build_aop_workbook`/`make_aop_row` (AOP). New parity helpers may read the buffer to a raw frame and pass it to both the protected loader path and the `SchemaLoader` path so the comparison is exact.

## Implementation Plan (Atomic Tasks)

### Phase 0 — Baseline Capture & Policy Read

- [x] [P0-T1] Read the policy files in the required precedence order (`CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`) and write `<FEAT-EV>/baseline/phase0-instructions-read.md`.
  - Acceptance: Artifact exists with `Timestamp:`, `Policy Order:`, and an explicit list of every file read.
- [x] [P0-T2] Capture the formatting baseline by running `poetry run black --check .` and write `<FEAT-EV>/baseline/black.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` of files that would reformat (or "all formatted").
- [x] [P0-T3] Capture the lint baseline by running `poetry run ruff check .` and write `<FEAT-EV>/baseline/ruff.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` (violation count or "all checks passed").
- [x] [P0-T4] Capture the type-check baseline by running `poetry run pyright` and write `<FEAT-EV>/baseline/pyright.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` (error/warning counts).
- [x] [P0-T5] Capture the test+coverage baseline by running `poetry run pytest --cov --cov-branch --cov-report=term-missing` and write `<FEAT-EV>/baseline/pytest-coverage.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, and an `Output Summary:` with numeric passed/failed counts and the baseline total line% and branch% headline values.
- [x] [P0-T6] Capture the protected-files baseline by running `git status --porcelain` and `git rev-parse HEAD`, recording HEAD SHA and a clean working tree, into `<FEAT-EV>/baseline/protected-files-head.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:`, the HEAD SHA, and an `Output Summary:` confirming the working tree is clean at the start. Note for the final regression check: on the shared epic branch, `git diff --name-only main` will include committed Feature A/B ancestry; the correct THIS-feature check is that `git diff --name-only HEAD` and `git status` show no modifications to any protected path (committed ancestry is not a violation).

### Phase 1 — asteval Type Stub & Formula Engine (T1)

- [x] [P1-T1] Create `typings/asteval/__init__.pyi` declaring a minimal typed `Interpreter` surface covering only what the adapter uses: constructor params `symtable: dict[str, object] | None = ...`, `user_symbols: dict[str, object] | None = ...`, `use_numpy: bool = ...`, `minimal: bool = ...`, `readonly_symbols: object | None = ...`, `no_print: bool = ...` (include `**kwargs: object` for the unused tail); a `__call__(self, expr: str) -> object` method; a `symtable: dict[str, object]` attribute; and an `error: list[object]` attribute. Annotate every signature fully (Pyright strict, no `Any`).
  - Preconditions: `asteval = "^1.0.8"` already present in `pyproject.toml`; default Pyright `stubPath` is `typings/` (no override in `pyproject.toml`), so the stub is auto-discovered.
  - Acceptance: File < 500 lines, fully annotated, no `# type: ignore`; `poetry run pyright typings/asteval/__init__.pyi` reports 0 errors.
- [x] [P1-T2] Create `src/schema_formula.py` defining `FormulaError(Exception)` and the whitelisted pure helpers `safe_div(num: float, den: float) -> float` (returns `0.0` when `den` is `None`/NaN/`<= 0`, else `num / den`) and the `col` accessor strategy (a `col(name: str) -> object` callable bound to the current evaluation context plus a deterministic identifier-alias map so formulas can reference columns with spaces/special chars such as `SKU #` and `Off Invoice $`). Full docstrings per the commenting policy.
  - Acceptance: Module imports the stubbed `asteval.Interpreter`; `safe_div` and `col` are fully annotated; no suppressions.
- [x] [P1-T3] Implement `FormulaEvaluator` in `src/schema_formula.py` wrapping `asteval.Interpreter` behind the typed adapter: an expression-validation entry point (`validate(expression: str, known_columns: Sequence[str]) -> None`) that rejects syntactically invalid expressions, disallowed constructs (imports, attribute access to dunders, subscripting, comprehensions, lambdas, calls to non-whitelisted names), and unknown-column references with a descriptive `FormulaError` naming the offending construct/column; and `evaluate(expression: str, context: Mapping[str, object]) -> object` that constrains the symtable to the supplied row/column values plus the whitelisted function set (`safe_div`, `sum`, `col`) and returns the evaluated value. Inspect the interpreter `.error` list after evaluation and raise `FormulaError` on any error entry.
  - Acceptance: The symtable contains only whitelisted names plus the provided column values; evaluation is side-effect free and deterministic; module < 500 lines (split a `src/_schema_formula_helpers.py` if needed, keeping it < 500 lines and classifying it in `quality-tiers.yml`).
- [x] [P1-T4] Create `tests/test_schema_formula.py` with unit tests (Arrange–Act–Assert) for: valid arithmetic expression evaluation; evaluation of `sum(...)`; column references with spaces/special chars via the `col`/alias map (`SKU #`, `Off Invoice $`) (AC6); ratio recompute via `safe_div`; and descriptive `FormulaError` on syntactically invalid input, disallowed constructs (import, dunder attribute access, subscript, lambda), and unknown-column reference (AC6).
  - Acceptance: Every test passes; failure messages are actionable; no temp files; tests import the adapter from `src.schema_formula`.
- [x] [P1-T5] Add Hypothesis property tests in `tests/test_schema_formula.py` (T1 ≥ 1 property test per pure function, AC9): `safe_div` returns `0.0` for any zero/negative/null/NaN denominator and equals `num/den` for any positive finite denominator; `col`/alias resolution round-trips for arbitrary column-name strings; the validator rejects a generated corpus of unsafe constructs (fuzz: imports/attribute/subscript/call-to-unknown) and accepts a generated corpus of safe arithmetic-over-known-columns expressions.
  - Acceptance: Property tests pass deterministically; on failure the Hypothesis seed is reported.
- [x] [P1-T6] Run the Phase 1 QA loop (`poetry run black .` → `poetry run ruff check .` → `poetry run pyright` → `poetry run pytest tests/test_schema_formula.py --cov=src/schema_formula --cov-branch --cov-report=term-missing`), restarting from formatting on any failure or auto-fix, and write `<FEAT-EV>/qa-gates/phase1-schema-formula.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`, `Command:`, `EXIT_CODE:` for each stage and an `Output Summary:` including the numeric line% and branch% for `src/schema_formula.py` (and any `_schema_formula_helpers.py`) meeting ≥ 85% line / ≥ 75% branch; a clean single pass through all four stages.

### Phase 2 — Schema Loader Core (resolve → key → fill → coerce → dedup) (T1)

- [x] [P2-T1] Create `src/schema_loader.py` defining `SchemaLoader` with constructor `__init__(self, schema: SchemaDefinition, *, formula_evaluator: FormulaEvaluator | None = None)` and the public method signature `load(self, raw: pd.DataFrame, schema: SchemaDefinition | None = None) -> pd.DataFrame` with a full class docstring (purpose, responsibilities, high-level flow, invariants, side effects). Stub the phase pipeline as private methods to be filled by subsequent tasks.
  - Acceptance: Class and method fully annotated; module imports reuse `resolve_columns`/`normalize_name` (`src.etl_columns`), `resolve_key`/`coerce_sku` (`src.etl_key`), `fill_blank_totals` (`src.etl_totals`), and the AOP `coerce_numeric`/`clean_label_sentinels` (`src._load_aop_helpers`); module < 500 lines.
- [x] [P2-T2] Implement the column-resolution phase: resolve the raw header to the schema's canonical names using `resolve_columns` over the schema's required `ColumnSpec` canonical names (honoring the optional/by-name handling for `KEY` and optional `YTG`/discriminator analogues), rename to canonical, warn-and-drop extras, then drop blank-`Customer` (blank-key) padding rows exactly as the loaders do (`isna() | str.strip() == ""`).
  - Acceptance: For both default schemas the resolved/renamed/blank-dropped frame matches the column set and row set the protected loaders produce at the equivalent step; covered by P2-T6 unit tests.
- [x] [P2-T3] Implement the key + fill + coerce/sentinel phases: establish the business key via `resolve_key` driven by the schema `KeySpec` (reusing `coerce_sku`); apply `fill_blank_totals` from the schema `fill_rules` (total → components); coerce numeric measures and clean sentinels by reusing `coerce_numeric` and `clean_label_sentinels` on the columns the schema marks `numeric` / `sentinel_clean`.
  - Acceptance: Key semantics, fill semantics, coercion, and sentinel cleaning reproduce the protected loaders' results on the shared fixtures; covered by P2-T6.
- [x] [P2-T4] Implement the dedup phase per `DedupPolicy`: `mode == "none"` preserves all rows in first-appearance order (AOP); `mode == "collapse"` groups by KEY with `sort=False`, takes dimension columns from the first row (`drop_duplicates(keep="first")`), aggregates each measure by its declared mode — `additive` sums (NaN→0 via default `min_count=0`), `select_from` picks the value from the row whose discriminator is in `select_values`; non-additive/ratio measures are NOT summed here (dropped pre-aggregation, recomputed in Phase 3). Preserve first-appearance ordering exactly like `normalize_le.normalize`.
  - Acceptance: Dedup honors `additive` vs `select_from` per measure and `mode == none` preserves rows with dimensions from the first row (AC3); covered by P2-T6.
- [x] [P2-T5] If `src/schema_loader.py` approaches 500 lines, extract the phase helpers into `src/_schema_loader_helpers.py` (fully annotated, < 500 lines, full docstrings) and re-export/import them from `src/schema_loader.py`; otherwise record in the QA artifact that no split was required.
  - Acceptance: Both files < 500 lines; if created, `_schema_loader_helpers.py` is classified in `quality-tiers.yml` (P5-T1).
- [x] [P2-T6] Create `tests/test_schema_loader_core.py` with unit + Hypothesis property tests (T1 ≥ 1 property test per pure phase function) covering: resolve/rename/extra-warn/blank-drop; key establishment; fill rules; coercion + sentinel cleaning; dedup `none` (row-preserving), dedup `collapse` additive (sum property: collapsed measure equals sum of group), and dedup `collapse` `select_from` (selected value equals the discriminator-matched row). Use the existing in-memory fixtures; no temp files.
  - Acceptance: All tests pass; property tests report seed on failure; dedup-aggregation property holds for generated multi-row groups (AC3).
- [x] [P2-T7] Run the Phase 2 QA loop (`black .` → `ruff check .` → `pyright` → `pytest tests/test_schema_loader_core.py tests/test_schema_formula.py --cov=src/schema_loader --cov=src/schema_formula --cov-branch --cov-report=term-missing`), restarting on any failure/auto-fix, and write `<FEAT-EV>/qa-gates/phase2-schema-loader-core.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`/`Command:`/`EXIT_CODE:` per stage and an `Output Summary:` with numeric line% and branch% for `src/schema_loader.py` (and `_schema_loader_helpers.py` if present) meeting ≥ 85% / ≥ 75%; clean single pass.

### Phase 3 — Derived Columns, Drop, Output Emission (T1)

- [x] [P3-T1] Implement the derived-columns phase in `src/schema_loader.py` (post-aggregation): for each `DerivedColumnSpec`, when `copy_from` is set, populate the derived column directly from the named column (the LE `Super Category <- PPG` quirk); when `expression` is set, evaluate it via the `FormulaEvaluator` against the aggregated frame, including ratio recompute from summed dollars/volume using `safe_div` (denominator null/NaN/`<= 0` yields 0) (AC4, AC5). Evaluate deterministically (vectorized where practical, else row-wise in index order).
  - Acceptance: `default_le` produces `YTG == sum(May..Dec)` on the aggregated rows and both `Super Category` and `PPG` equal the source `PPG`; covered by P3-T4 and the Phase 4 parity tests.
- [x] [P3-T2] Implement the drop + emission phase: drop the schema `drop_columns` (e.g. LE `YTD/YTG`) and emit exactly the declared canonical output columns in schema order (LE: 26 `TARGET_COLUMNS`; AOP: full `SOURCE_COLUMNS` order). Reset the index so the output shape matches the protected loaders (LE `normalize` returns a default RangeIndex after `reset_index`; AOP preserves the post-drop index as the loaders do — verify against the protected output and match exactly).
  - Acceptance: Output column list and order equal the protected loaders' outputs for both schemas; index matches; covered by Phase 4 parity tests.
- [x] [P3-T3] Implement the column-builder path so a schema that declares a measure as a derived `expression` (rather than a source column) constructs that missing column from other columns post-resolution (AC4), and add a focused unit test in `tests/test_schema_loader_derived.py` driving a small schema whose output column is built from an expression over existing columns.
  - Acceptance: The built column's values equal the expected expression result on the fixture; test passes.
- [x] [P3-T4] Create `tests/test_schema_loader_derived.py` unit + property tests covering: `copy_from` quirk; `expression`-derived `YTG`; ratio recompute with `safe_div` edge cases (zero/negative/null/NaN denominator → 0) as a Hypothesis property (AC5); drop-columns removal; and exact output column order/index for both default schemas (constructed from bundled schemas via `SchemaRegistry.load_bundled_default`).
  - Acceptance: All tests pass; ratio-safe-division property holds across generated denominators; no temp files.
- [x] [P3-T5] Run the Phase 3 QA loop (`black .` → `ruff check .` → `pyright` → `pytest tests/test_schema_loader_derived.py tests/test_schema_loader_core.py tests/test_schema_formula.py --cov=src/schema_loader --cov=src/schema_formula --cov-branch --cov-report=term-missing`), restarting on any failure/auto-fix, and write `<FEAT-EV>/qa-gates/phase3-derived-output.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`/`Command:`/`EXIT_CODE:` per stage and an `Output Summary:` with numeric line%/branch% for the new modules meeting ≥ 85% / ≥ 75%; clean single pass.

### Phase 4 — Parity & Integration (AC1, AC2, AC8)

- [x] [P4-T1] Create `tests/test_schema_loader_parity_le.py` proving `SchemaLoader(default_le).load(raw_le_frame)` equals `normalize_le.normalize(load_source(<same workbook>))` via `pandas.testing.assert_frame_equal`. Build the raw frame and the protected-path output from the SAME in-memory workbook (reuse `tests.le_fixtures.build_workbook`/`make_row`; read the raw frame with `src.pandas_io.read_excel_sheet(buffer, sheet_name="LE-8 + 4", header=2)`). Cover multi-row collapse, the blank-totals fill quirk, and the PPG quirk; `default_le` is loaded via `SchemaRegistry.load_bundled_default("default_le")`.
  - Acceptance: `assert_frame_equal` passes (columns, order, dtypes, values, PPG quirk, derived YTG, dropped `YTD/YTG`) for every parity fixture (AC1); no temp files.
- [x] [P4-T2] Create `tests/test_schema_loader_parity_aop.py` proving `SchemaLoader(default_aop).load(raw_aop_frame)` equals `load_aop(<same workbook>)` via `assert_frame_equal`. Build the raw frame and the protected-path output from the SAME in-memory workbook (reuse `tests.aop_fixtures.build_aop_workbook`/`make_aop_row`; read the raw frame with `read_excel_sheet(buffer, sheet_name="AOP1", header=2)`). Cover the with-YTG and without-YTG source layouts and the sentinel-clean label columns; `default_aop` is loaded via `SchemaRegistry.load_bundled_default("default_aop")`.
  - Acceptance: `assert_frame_equal` passes (columns, order, dtypes, values, no row collapse, no PPG quirk) for every parity fixture (AC2); no temp files.
- [x] [P4-T3] Create `tests/test_schema_loader_integration.py` feeding `SchemaLoader` output through an existing pipeline transform to a consistent result (AC8): persist the loader's AOP-equivalent frame in-memory and run it through `src.mix_transforms.pivot_aop` (and/or the LE frame through `pivot_le`), asserting the transform produces the same result as when fed the protected loader's output.
  - Acceptance: The integration transform output from the `SchemaLoader` frame equals the output from the protected-loader frame; test passes; no temp files, no network.
- [x] [P4-T4] Run the Phase 4 QA loop (`black .` → `ruff check .` → `pyright` → `pytest tests/test_schema_loader_parity_le.py tests/test_schema_loader_parity_aop.py tests/test_schema_loader_integration.py --cov=src/schema_loader --cov=src/schema_formula --cov-branch --cov-report=term-missing`), restarting on any failure/auto-fix, and write `<FEAT-EV>/qa-gates/phase4-parity-integration.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`/`Command:`/`EXIT_CODE:` per stage and an `Output Summary:` confirming all parity and integration tests pass with numeric coverage headline values.

### Phase 5 — Tier Classification & Final QA Loop

- [x] [P5-T1] Update `quality-tiers.yml` to classify the new modules: `src/schema_formula.py` and `src/schema_loader.py` as **T1** (formula engine + loader core; a bug causes silent data corruption); `src/_schema_loader_helpers.py` and `src/_schema_formula_helpers.py` as **T2** when those helper files were created (only add entries for files that exist), with a brief block comment stating the rationale (AC10). Do not alter existing entries.
  - Acceptance: Every new `src/*.py` module created in this feature has exactly one tier entry; no existing project entry is changed; the file remains valid YAML.
- [x] [P5-T2] Run the full final formatting+lint+type stages on the whole repo (`poetry run black .` → `poetry run ruff check .` → `poetry run pyright`), restarting from formatting on any failure/auto-fix, and write `<FEAT-EV>/qa-gates/final-format-lint-type.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`/`Command:`/`EXIT_CODE:` per stage and an `Output Summary:` confirming 0 format diffs, 0 lint violations, 0 Pyright errors with NO suppressions added (verify no new `# type: ignore`/`# noqa` outside pre-authorized patterns).
- [x] [P5-T3] Run the full final test suite with coverage (`poetry run pytest --cov --cov-branch --cov-report=term-missing`) and write `<FEAT-EV>/qa-gates/final-pytest-coverage.<timestamp>.md`.
  - Acceptance: Artifact records `Timestamp:`/`Command:`/`EXIT_CODE:` and an `Output Summary:` confirming the existing suite remains green (AC11) and the post-change total line%/branch% with numeric values (not placeholders).
- [x] [P5-T4] Write the coverage-delta verification artifact `<FEAT-EV>/qa-gates/coverage-delta.<timestamp>.md` comparing baseline (P0-T5) vs post-change (P5-T3) total coverage and reporting the per-module new-code coverage for `src/schema_formula.py` and `src/schema_loader.py` (and any helper modules).
  - Acceptance: Artifact reports baseline line%/branch%, post-change line%/branch%, and new/changed-code line% ≥ 85% and branch% ≥ 75% for each new module (AC10); if any required coverage value is unavailable, the outcome is remediation-required, not PASS.
- [x] [P5-T5] Write the protected-files regression artifact `<FEAT-EV>/regression-testing/protected-files-diff.<timestamp>.md` by running `git diff --name-only HEAD` and `git status --porcelain` and confirming no protected path (the files listed in Scope & Hard Constraints) appears as modified.
  - Acceptance: Artifact records `Timestamp:`/`Command:`/`EXIT_CODE:` and an `Output Summary:` confirming the only changed paths are the new feature files (`typings/asteval/__init__.pyi`, `src/schema_formula.py`, `src/schema_loader.py`, optional helper modules, the new `tests/test_schema_*` files, and `quality-tiers.yml`); explicitly note that committed Feature A/B ancestry shown by `git diff --name-only main` is NOT a violation per the P0-T6 note.

## Test Plan

- **Unit:** `tests/test_schema_formula.py` (formula validation, evaluation, `safe_div`, `col`/alias, rejection), `tests/test_schema_loader_core.py` (resolve/key/fill/coerce/dedup), `tests/test_schema_loader_derived.py` (derived/copy_from/drop/output order).
- **Property (Hypothesis, T1 ≥ 1 per pure function):** `safe_div` edge cases, `col`/alias round-trip, unsafe-expression rejection corpus, dedup-aggregation sum property, ratio safe-division property.
- **Parity:** `tests/test_schema_loader_parity_le.py` (== `normalize`), `tests/test_schema_loader_parity_aop.py` (== `load_aop`), both via `assert_frame_equal` on shared in-memory fixtures.
- **Integration:** `tests/test_schema_loader_integration.py` (loader output → `mix_transforms.pivot_aop`/`pivot_le`).
- **Coverage evidence:**
  - Baseline: `<FEAT-EV>/baseline/pytest-coverage.<timestamp>.md`.
  - Per-phase QA: `<FEAT-EV>/qa-gates/phase{1..4}-*.<timestamp>.md`.
  - Final: `<FEAT-EV>/qa-gates/final-pytest-coverage.<timestamp>.md`.
  - Delta/threshold: `<FEAT-EV>/qa-gates/coverage-delta.<timestamp>.md`.
- **Regression:** `<FEAT-EV>/regression-testing/protected-files-diff.<timestamp>.md`.

## Open Questions / Notes

- The `col`/alias strategy for non-identifier column names (`SKU #`, `Off Invoice $`) is left to the executor to finalize between a `col("exact name")` callable and a deterministic identifier-alias map exposed in the symtable; both AC6 cases (spaces and `#`/`$`) must be covered by tests either way.
- If the AOP/LE output index shape from `SchemaLoader` cannot be made to match the protected loaders byte-for-equivalent under `assert_frame_equal`, treat it as a parity defect and fix the loader (do not relax `assert_frame_equal` flags); if a relaxation appears unavoidable, STOP and escalate.
- The asteval-untyped problem is solved exclusively by `typings/asteval/__init__.pyi`. If Pyright strict still reports an asteval-related error that the stub cannot resolve, STOP and escalate rather than adding any suppression.
