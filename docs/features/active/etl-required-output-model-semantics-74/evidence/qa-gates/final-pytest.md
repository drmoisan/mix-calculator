# Final QA — Pytest + Coverage

Timestamp: 2026-06-17T13-10
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 1058 passed, 5 warnings in 34.36s (baseline was 1049 passed; +9 new tests).
- TOTAL coverage: line 99.09% (5031 stmts, 46 missed); branch 94.10% (932 branches, 55 partial).
- In-scope modules:
  - src/_schema_model_specs.py: line 100%, branch 100%.
  - src/schema_model.py: line 100%, branch 100% (new required_output_columns fully covered).
  - src/schema_serialization.py: line 98% (1 missed: line 486), branch 88% (1 partial: 486).
    Line 486 is the pre-existing key malformed-shape error path, uncovered at baseline
    (baseline reported line 421 for the same branch); it is not a changed line in this work.
- Both thresholds satisfied (line >= 85%, branch >= 75%).
