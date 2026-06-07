# Targeted Regression — Formula Engine Fix (C1) (Cycle 4 Remediation)

Timestamp: 2026-06-05T23-23
Command: `env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest tests/test_schema_formula.py`
EXIT_CODE: 0
Output Summary:
- Result: 37 passed in 0.91s.
- `tests/test_schema_formula.py::test_property_col_round_trips_values` -> PASSED (previously failing entry-state property test now passes after the fix).
- `tests/test_schema_formula.py::test_evaluate_column_named_col_round_trips_via_col_callable` -> PASSED (new C1 regression test; columns named `col`/`sum`/`safe_div` round-trip via `col(...)` without shadowing the helper).

The fix binds the whitelisted callables (`safe_div`, `sum`, `col`) AFTER the
alias-binding loop in `_build_symtable`, so a colliding column value can no longer
overwrite the helper callable. The Hypothesis falsifying example (cached in the
local `.hypothesis` DB) no longer reproduces because the property now holds for
all examples.
