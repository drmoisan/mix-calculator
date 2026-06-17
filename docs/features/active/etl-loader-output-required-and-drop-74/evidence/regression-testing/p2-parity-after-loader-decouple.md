# Phase 2 Regression Checkpoint — Parity UNCHANGED after loader decouple (BEFORE any flag flip)

Timestamp: 2026-06-17T14-45
Command: poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py tests/test_default_schemas.py -q
EXIT_CODE: 0
Output Summary:
- tests/test_schema_loader_parity_aop.py: 6 passed.
- tests/test_schema_loader_parity_le.py: 5 passed.
- tests/test_default_schemas.py: 25 passed.
- Combined: 36 passed.
- The loader decouple is in place: `_by_name_optional_columns` (relocated to
  `src/_schema_loader_keepset.by_name_optional_columns`) keys off `located_by_name`;
  the keep-set in `resolve_and_rename` is flag-independent (required OR in_output OR
  referenced, located columns excluded); the none-path emitted order follows
  resolution/in_output position, not the required flag.
- AOP relies on the 2.0 migration seeding `KEY`/`YTG` as located_by_name; LE
  `located_by_name` is still all-False (Phase 4 sets it). No flag flip has occurred.
- AOP + LE parity pass UNCHANGED. Zero emitted-output change.
