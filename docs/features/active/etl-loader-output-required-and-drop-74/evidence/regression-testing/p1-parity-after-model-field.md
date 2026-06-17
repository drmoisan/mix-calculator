# Phase 1 Regression Checkpoint — Parity UNCHANGED after model field

Timestamp: 2026-06-17T14-20
Command: poetry run pytest tests/test_schema_loader_parity_aop.py tests/test_schema_loader_parity_le.py tests/test_default_schemas.py -q
EXIT_CODE: 0
Output Summary:
- Combined: 36 passed in ~0.98s.
- tests/test_schema_loader_parity_aop.py: 6 passed.
- tests/test_schema_loader_parity_le.py: 5 passed.
- tests/test_default_schemas.py: 25 passed.
- The additive `located_by_name` field (default False), its serialization, and the
  migration seeding did not change any emitted output. AOP + LE parity and the
  default-schema tests pass unchanged. No loader or flag change has been made yet.
