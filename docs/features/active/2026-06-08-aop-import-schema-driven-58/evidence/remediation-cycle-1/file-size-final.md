# File-Size Final Scan

Timestamp: 2026-06-08T18-00
Command: awk 'END{print NR}' <file> over the changed test files plus the modules created by this remediation
EXIT_CODE: 0
Output Summary (every file <= 500):
- tests/aop_fixtures.py = 381
- tests/test_default_schemas.py = 311
- tests/test_schema_loader_core.py = 345   (was 501 at baseline; now under cap)
- tests/test_schema_loader_parity_aop.py = 239
- tests/gui/test_pipeline_service.py = 437   (was 638 at baseline; now under cap)
- tests/gui/test_pipeline_service_key_seam.py = 300
- tests/gui/integration/test_behavioral_composition.py = 218
- tests/gui/test_gui_integration.py = 303
- tests/gui/test_key_mismatch_dialog.py = 303
- tests/gui/test_pipeline_service_aop_schema.py = 162   (new module, Batch 1)
- tests/test_schema_loader_seam.py = 148   (new module, Batch 2)
- tests/gui/_pipeline_service_fixtures.py = 84   (new shared-helper module, Batch 1)
- tests/_schema_loader_fixtures.py = 54   (new shared-helper module, Batch 2)

Assertion: every listed file is <= 500 lines. The two files that exceeded the cap
at baseline (test_pipeline_service.py = 638, test_schema_loader_core.py = 501) are
both now under the cap.

Note on the two additional shared-helper modules: relocating `_patch_loaders`
(Batch 1) and `_load_default`/`_MONTHS_A`/`_MONTHS_B` (Batch 2) into dedicated
underscore-prefixed fixture modules was the in-scope helper relocation the plan's
remediation strategy authorizes. It was required to keep the cross-module shared
helpers Pyright-clean under strict mode (reportPrivateUsage) via `__all__` export,
matching the existing repo pattern in tests/_mix_rollups_fixtures.py. No production
file and no non-oversized test file was altered beyond importing these relocated
helpers.
