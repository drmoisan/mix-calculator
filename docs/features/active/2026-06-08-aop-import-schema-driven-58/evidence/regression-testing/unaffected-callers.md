# Phase 3 — Unaffected Callers Regression (P3-T4)

Timestamp: 2026-06-08T14-30

## SchemaLoader unit + LE parity surface
Command: poetry run pytest tests/test_schema_loader_core.py tests/test_schema_loader_derived.py tests/test_schema_loader_integration.py tests/test_schema_loader_parity_le.py -q
EXIT_CODE: 0
Output Summary: 31 passed. All SchemaLoader callers (including the LE parity path and the additive `import_with_schema` path covered in the integration suite) pass with default seams; the new keyword-only seams preserve prior behavior for existing callers.

## LE / SKU_LU pipeline-service paths
Command: poetry run pytest tests/gui/test_pipeline_service.py tests/gui/test_gui_integration.py -q -k "le or skulu or LE or SKU or sources or run_pipeline"
EXIT_CODE: 0
Output Summary: 8 passed, 8 deselected. The LE (`import_le`) and SKU_LU (`import_skulu`) import paths and `import_sources`/`run_pipeline` remain green; only the AOP path changed.

## Full-suite confirmation
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary: 998 passed, 0 failed. No regression in any SchemaLoader caller or LE/SKU_LU import path (AC-8).
