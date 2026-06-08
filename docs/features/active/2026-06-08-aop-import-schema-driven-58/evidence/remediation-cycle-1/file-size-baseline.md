# File-Size Baseline

Timestamp: 2026-06-08T17-47
Command: awk 'END{print NR}' <file> over the authoritative feature-touched test files
EXIT_CODE: 0
Output Summary:
- tests/aop_fixtures.py = 381
- tests/test_default_schemas.py = 311
- tests/test_schema_loader_core.py = 501  [OVER CAP > 500]
- tests/test_schema_loader_parity_aop.py = 239
- tests/gui/test_pipeline_service.py = 638  [OVER CAP > 500]
- tests/gui/test_pipeline_service_key_seam.py = 300
- tests/gui/integration/test_behavioral_composition.py = 218
- tests/gui/test_gui_integration.py = 303
- tests/gui/test_key_mismatch_dialog.py = 303

Two files exceed the 500-line cap and are the subject of B1:
- tests/gui/test_pipeline_service.py = 638
- tests/test_schema_loader_core.py = 501

The two new modules created by this remediation
(tests/gui/test_pipeline_service_aop_schema.py, tests/test_schema_loader_seam.py)
do not exist at baseline and are scanned only in P3-T7.
