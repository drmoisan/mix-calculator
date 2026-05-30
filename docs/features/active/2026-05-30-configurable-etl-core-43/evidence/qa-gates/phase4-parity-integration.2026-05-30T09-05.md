# Phase 4 QA Gate — Parity & Integration (Issue #43, AC1/AC2/AC8)

Timestamp: 2026-05-30T09-05
Single clean pass through all four stages.

## Stage 1 — Black
Command: poetry run black .
EXIT_CODE: 0
Output Summary: No reformatting on the final pass.

## Stage 2 — Ruff
Command: poetry run ruff check (the three new parity/integration test files)
EXIT_CODE: 0
Output Summary: All checks passed.

## Stage 3 — Pyright (strict)
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations. No suppressions.

## Stage 4 — Pytest + coverage
Command: poetry run pytest tests/test_schema_loader_parity_le.py tests/test_schema_loader_parity_aop.py tests/test_schema_loader_integration.py --cov=src.schema_loader --cov=src._schema_loader_helpers --cov=src.schema_formula --cov=src._schema_formula_helpers --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 11 passed, 0 failed.
- LE parity: SchemaLoader(default_le).load(raw) == normalize_le.normalize(load_source(...))
  via assert_frame_equal(check_dtype=True, check_like=False) for multi-row
  collapse, blank-totals fill quirk, PPG copy quirk, and multiple-key matrices
  (AC1: PASS).
- AOP parity: SchemaLoader(default_aop).load(raw) == load_aop(...) via
  assert_frame_equal for with-YTG, without-YTG, sentinel-clean labels, and
  no-row-collapse cases (AC2: PASS).
- Integration: pivot_le and pivot_aop produce identical output from the
  SchemaLoader frame and the protected-loader frame (AC8: PASS).
- Coverage shown here is for the parity/integration suite in isolation (it does
  not run the validator-rejection unit tests); the combined-suite new-module
  coverage (line 94% / branch ~88%) is recorded in the Phase 3 artifact and the
  final coverage-delta artifact. assert_frame_equal flags were NOT relaxed.
