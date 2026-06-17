# Final QA — Bundled-Schema Loader Output Parity (End State)

Timestamp: 2026-06-17T13-10
Command: poetry run pytest tests/test_schema_loader_parity_le.py tests/test_schema_loader_parity_aop.py tests/test_default_schemas.py -q
EXIT_CODE: 0
Output Summary:
- 36 passed in 1.32s (baseline reference was 34 passed; +2 new default_le required-set and required_output_columns tests added to test_default_schemas.py).
- The parity tests assert SchemaLoader(default_le)/SchemaLoader(default_aop) output equals the protected normalizer/loader output in columns, order, dtypes, and values; all pass against the edited 3.0 bundled schemas.
- Zero output regression confirmed: bundled default_le and default_aop emit the same output as the baseline reference. Only the input `required` gate and the version string changed; `in_output` and emitted output are unchanged.
