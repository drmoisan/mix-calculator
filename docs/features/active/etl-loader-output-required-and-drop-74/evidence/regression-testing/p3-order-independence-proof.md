# Phase 3 Evidence — Order-Independence Proven PRE-FLIP

Timestamp: 2026-06-17T14-55
Command: poetry run pytest tests/test_schema_loader_helpers.py tests/test_schema_loader_parity_aop.py -q
EXIT_CODE: 0
Output Summary:
- Combined: 13 passed in ~0.94s.
- The fabricated-schema and simulated-flip tests pass on the UNMODIFIED bundled
  AOP JSON (no `required` flag has been changed in the file yet).

Order-independence test (fabricated schema, none dedup):
- tests/test_schema_loader_helpers.py::test_none_path_order_is_independent_of_required_flag
  — measures declared required=False, in_output=True interleaved with required
  dimensions plus a trailing located_by_name optional emit in declared/resolution
  order, located optional last, KEY last. The CF1 finding is reproduced GREEN.

Simulated AOP-flip parity tests (guard the Phase 5 JSON flip):
- tests/test_schema_loader_parity_aop.py::test_aop_simulated_required_flip_preserves_order_with_ytg
- tests/test_schema_loader_parity_aop.py::test_aop_simulated_required_flip_preserves_order_without_ytg
  — using dataclasses.replace to flip every AOP measure (Jan..Dec, YTD, Q1..Q4,
  YTG) to required=False, the SchemaLoader output column order equals the
  load_aop oracle for both the with-YTG and without-YTG fixtures. The CF1
  regression is no longer reproducible.

Public accessor confirmed: SchemaDefinition.required_output_columns()
(src/schema_model.py:201); P3-T3 test reads only that accessor.
