# Remediation Plan — schema-builder-ux-overhaul (Issue #50) — Cycle 4

- Entry timestamp: 2026-06-05T23-23
- Inputs: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/remediation-inputs.2026-06-05T23-23.md`
- Work Mode: full-feature
- Branch: `feature/schema-builder-ux-overhaul-50`
- Base: `main`; Head: `cc5b282`; Merge-base: `5e659f2`; PR #51 (open)
- Feature folder (`<FEATURE>`): `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50`
- Evidence root: `<FEATURE>/evidence/` (canonical per `evidence-and-timestamp-conventions`)

## Scope

Exactly one blocking finding (C1). The plan is tightly scoped to the formula
engine and its tests. Production change is confined to `src/schema_formula.py`
(method `_build_symtable`); the regression test is added to
`tests/test_schema_formula.py`. No GUI, schema model, migration, or drag-tab
files are touched. `src/_schema_formula_helpers.py`, `validate`, `evaluate`, and
`build_alias_map` are read-only references confirmed consistent; they are not
modified by the chosen approach.

## Chosen Anti-Shadowing Approach

Bind the whitelisted callables (`safe_div`, `sum`, `col`) AFTER the alias-binding
loop in `_build_symtable`. The alias loop populates column values first; the
whitelisted-callable assignment then runs last, so a column whose alias collides
with `col`/`sum`/`safe_div` cannot overwrite the helper in the symbol table. The
`col` accessor reads from the closed-over `context`, not from `symtable`, so
`col("col")` (and `col("sum")`, `col("safe_div")`) still returns the exact-name
column value for every column name. `validate()` requires no change: its
`allowed_names` is already `WHITELISTED_FUNCTIONS | set(alias_map)`, so a column
named `col` (alias `col`) remains a permitted bare name and `col(...)` remains a
permitted whitelisted call. This approach keeps `col(name)` working for ALL
column names and keeps existing alias references working, satisfying both
required invariants.

## C1 -> Task Map

- C1 (root cause — overwrite of whitelisted `col`/`sum`/`safe_div` by colliding column value): P1-T1
- C1 (regression test — column named `col` and `sum` round-trip via `col(...)`; helpers not shadowed): P1-T2
- C1 (acceptance — failing property test `test_property_col_round_trips_values` now passes): P1-T3, P2-T4
- C1 (acceptance — full suite green, EXIT 0): P2-T4
- C1 (coverage no-regression; file-size <= 500; no suppressions; masking clean): P2-T5, P2-T6, P2-T7, P2-T8

---

### Phase 0 — Baseline Capture

- [x] [P0-T1] Read policy files in required order and record them in `<FEATURE>/evidence/remediation-baseline/phase0-instructions-read.2026-06-05T23-23.md` with fields `Timestamp:`, `Policy Order:`, and an explicit list of files read: `CLAUDE.md`, `.claude/rules/general-code-change.md`, `.claude/rules/general-unit-test.md`, `.claude/rules/python.md`, `.claude/rules/python-suppressions.md`, `.claude/rules/quality-tiers.md`, `.claude/rules/self-explanatory-code-commenting.md`, `.claude/rules/tonality.md`. Acceptance: artifact exists with all three fields populated.
- [x] [P0-T2] Capture Black baseline by running `env -u VIRTUAL_ENV poetry run black --check .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `<FEATURE>/evidence/remediation-baseline/baseline-black.2026-06-05T23-23.md`. Acceptance: artifact records the exact command and exit code.
- [x] [P0-T3] Capture Ruff baseline by running `env -u VIRTUAL_ENV poetry run ruff check .` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `<FEATURE>/evidence/remediation-baseline/baseline-ruff.2026-06-05T23-23.md`. Acceptance: artifact records the exact command and exit code.
- [x] [P0-T4] Capture Pyright baseline by running `env -u VIRTUAL_ENV poetry run pyright` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `<FEATURE>/evidence/remediation-baseline/baseline-pyright.2026-06-05T23-23.md`. Acceptance: artifact records the exact command and exit code.
- [x] [P0-T5] Capture Pytest coverage baseline by running `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (including numeric overall line %, branch %, and the `src/schema_formula.py` module line/branch %, plus pass/fail counts; the entry-state expectation is 940 passed, 1 failed) to `<FEATURE>/evidence/remediation-baseline/baseline-pytest.2026-06-05T23-23.md`. Acceptance: artifact records numeric coverage headline values and the failing-test name `tests/test_schema_formula.py::test_property_col_round_trips_values`.
- [x] [P0-T6] Capture the file-size baseline for `src/schema_formula.py` by recording its current line count to `<FEATURE>/evidence/remediation-baseline/baseline-file-sizes.2026-06-05T23-23.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (line count, must be <= 500). Acceptance: artifact records a numeric line count for `src/schema_formula.py`.

### Phase 1 — Fix `col`-Shadowing and Add Regression Coverage

- [x] [P1-T1] Edit `src/schema_formula.py` method `_build_symtable` so the whitelisted callables are bound AFTER the alias-binding loop: move the `for alias, column in alias_map.items(): symtable[alias] = context[column]` loop to populate the dict first, then assign `symtable["safe_div"] = safe_div`, `symtable["sum"] = formula_sum`, `symtable["col"] = col` last; update the method docstring/inline comments to state that whitelisted callables are bound last so a colliding column name cannot shadow them. Acceptance: in the resulting `_build_symtable`, `symtable["col"]`/`symtable["sum"]`/`symtable["safe_div"]` are the callables even when `context` contains keys `col`/`sum`/`safe_div`; no other file is modified.
- [x] [P1-T2] Add a regression test `test_evaluate_column_named_col_round_trips_via_col_callable` (and an analogous assertion for a column named `sum`) to `tests/test_schema_formula.py` that constructs a `FormulaEvaluator`, evaluates `col("col")` against context `{"col": 0.0, "name": "col"}`-style bindings, and asserts the stored value is returned (helper not shadowed); include a case for a column named `sum` resolved via `col("sum")`. Acceptance: test follows Arrange-Act-Assert, has a descriptive docstring, asserts exact returned values for columns named `col` and `sum`.
- [x] [P1-T3] Run only the formula test module under coverage to confirm the targeted fix by executing `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest tests/test_schema_formula.py` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (including that `test_property_col_round_trips_values` and the new regression test pass) to `<FEATURE>/evidence/regression-testing/formula-fix-targeted.2026-06-05T23-23.md`. Acceptance: artifact records EXIT_CODE 0 and names both passing tests; if non-zero, return to P1-T1.

### Phase 2 — Final QA Loop and Evidence

- [x] [P2-T1] Run Black and record evidence by executing `env -u VIRTUAL_ENV poetry run black --check .` and writing `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `<FEATURE>/evidence/qa-gates/final-black.2026-06-05T23-23.md`. Acceptance: EXIT_CODE 0; if files change or the check fails, run `poetry run black .`, then restart the loop from P2-T1.
- [x] [P2-T2] Run Ruff and record evidence by executing `env -u VIRTUAL_ENV poetry run ruff check .` and writing `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `<FEATURE>/evidence/qa-gates/final-ruff.2026-06-05T23-23.md`. Acceptance: EXIT_CODE 0 with zero errors and no new suppressions; if it fails or auto-fixes files, restart from P2-T1.
- [x] [P2-T3] Run Pyright and record evidence by executing `env -u VIRTUAL_ENV poetry run pyright` and writing `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` to `<FEATURE>/evidence/qa-gates/final-pyright.2026-06-05T23-23.md`. Acceptance: EXIT_CODE 0 with zero type errors; if it fails, restart from P2-T1.
- [x] [P2-T4] Run the FULL test suite under coverage by executing `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing` and record `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:` (numeric overall line %, branch %, `src/schema_formula.py` module %, total passed count, zero failures) to `<FEATURE>/evidence/qa-gates/final-pytest.2026-06-05T23-23.md`. Acceptance: EXIT_CODE 0, zero failures, `test_property_col_round_trips_values` passes; if any step changed files, restart from P2-T1.
- [x] [P2-T5] Compare baseline vs post-change coverage by writing `<FEATURE>/evidence/qa-gates/coverage-comparison.2026-06-05T23-23.md` with `Timestamp:`, baseline line/branch % (from P0-T5), post-change line/branch % (from P2-T4), changed-code coverage for `src/schema_formula.py`, and an explicit no-regression determination against thresholds line >= 85% / branch >= 75%. Acceptance: artifact states PASS with all three coverage figures and confirms no regression on changed lines.
- [x] [P2-T6] Verify file size by recording the post-change line count of `src/schema_formula.py` and `tests/test_schema_formula.py` to `<FEATURE>/evidence/qa-gates/file-size-gate.2026-06-05T23-23.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: `src/schema_formula.py` <= 500 lines; no file in scope exceeds 500 lines.
- [x] [P2-T7] Run a masking scan over the changed files (`src/schema_formula.py`, `tests/test_schema_formula.py`) for new `# noqa`, `# type: ignore`, `# pragma: no cover`, weakened/removed assertions, or skipped tests, and record findings to `<FEATURE>/evidence/qa-gates/masking-scan.2026-06-05T23-23.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`. Acceptance: artifact records zero new suppressions and zero masking; any new suppression without authorization per `.claude/rules/python-suppressions.md` fails this task.
- [x] [P2-T8] Confirm scope containment and no cross-cutting regression by recording `git diff --stat main...HEAD` to `<FEATURE>/evidence/qa-gates/scope-containment.2026-06-05T23-23.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`, and asserting the only changed files are `src/schema_formula.py` and `tests/test_schema_formula.py` (no `.github/workflows/**`, no `scripts/benchmarks/**`, no GUI/schema/migration files), and that B1/B2 (cycle 3) and prior R1-R6 wiring remain present. Acceptance: artifact lists exactly the two in-scope changed files and confirms no out-of-scope diff.
