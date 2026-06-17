# Final QA — File-size and Invariant Check

Timestamp: 2026-06-17T15-30
Command: poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py -q  (plus wc -l of each changed file)
EXIT_CODE: 0

## Changed-file line counts (500-line cap)

| File | Lines | <= 500 |
|---|---|---|
| src/_schema_model_specs.py | 494 | yes |
| src/schema_serialization.py | 427 | yes |
| src/_schema_migration.py (new) | 131 | yes |
| src/_schema_loader_helpers.py | 458 | yes |
| src/_schema_loader_keepset.py (new) | 115 | yes |
| tests/test_schema_migration.py | 259 | yes |
| tests/test_schema_loader_helpers.py (new) | 290 | yes |
| tests/test_schema_loader_parity_aop.py | 349 | yes |
| tests/test_default_schemas.py | 480 | yes |
| src/schemas/default_le.schema.json | 443 | n/a (data) |
| src/schemas/default_aop.schema.json | 296 | n/a (data) |

All changed Python files are <= 500 lines.

## Binding-oracle result

- poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py -q
- 13 passed (6 original AOP parity + 2 simulated-flip + 5 LE parity).
- The binding parity oracle passes UNCHANGED after all changes, including the AOP
  required-flag flip. Zero emitted-output regression for both bundled schemas
  (columns, order, values, dtypes, index identical to load_aop / normalize_le).
