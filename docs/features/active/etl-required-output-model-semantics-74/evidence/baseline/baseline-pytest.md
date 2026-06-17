# Baseline — Pytest + Coverage

Timestamp: 2026-06-17T12-40
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 1049 passed, 5 warnings in 47.19s
- TOTAL coverage: line 99.08% (5016 stmts, 46 missed); branch 94.10% (932 branches, 55 partial)
- In-scope modules: src/schema_model.py line 100%; src/schema_serialization.py line 98% (1 partial at line 421); src/_schema_model_specs.py covered within schema_model aggregate.
- Both thresholds satisfied at baseline (line >= 85%, branch >= 75%).
