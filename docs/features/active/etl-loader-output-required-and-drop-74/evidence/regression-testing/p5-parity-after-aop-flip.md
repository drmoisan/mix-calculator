# Phase 5 Binding-Oracle Regression — AOP + LE Parity UNCHANGED after the required flip

Timestamp: 2026-06-17T15-15
Command: poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py tests/test_default_schemas.py -q
EXIT_CODE: 0
Output Summary:
- tests/test_schema_loader_parity_aop.py: 8 passed (6 original parity + 2 simulated-flip).
- tests/test_schema_loader_parity_le.py: 5 passed.
- tests/test_default_schemas.py: 25 passed.

State after the AOP minimization (src/schemas/default_aop.schema.json):
- version bumped 2.0 -> 3.0 (decision: prevents the migration from re-seeding
  located_by_name on the now-required=false measures).
- required set = exactly the seven dimensions (Customer, SKU Descripiton, SKU #,
  Customer Master, Type, Super Category, PPG).
- every measure (Jan..Dec, YTD, Q1..Q4, YTG) is required=false, in_output=true.
- located_by_name set on KEY and YTG only.

Zero output regression confirmed: the AOP and LE parity tests assert
`list(schema_output.columns) == list(load_aop/normalize_le output.columns)` and
identical KEY composition/values. Emitted columns, order, values, dtypes, and
index are UNCHANGED for both bundled schemas after the required-flag flip. The
CF1 order regression does not recur.

Supporting broader suite (not part of the gate command, run for confidence):
- test_schema_loader_core/integration/seam/derived + test_schema_registry: 45 passed.
