# Test-Count Parity — Pre-Split vs Post-Split (Cycle 2)

Timestamp: 2026-06-05T21-27
Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_builder_presenter_core.py tests/gui/test_schema_builder_presenter_seeding.py --collect-only -q
EXIT_CODE: 0

Output Summary:
- Pre-split collected-item count (authoritative reference from P0-T6): 20
  (parametrized cases counted individually; the original
  tests/gui/test_schema_builder_presenter.py).
- Post-split collected-item sum across the two new modules: 20
  - tests/gui/test_schema_builder_presenter_core.py: 15 items (13 core functions, one
    of which — test_validate_formula_rejects_bad_expressions — is parametrized into 3
    cases: 12 functions x 1 + 1 function x 3 = 15).
  - tests/gui/test_schema_builder_presenter_seeding.py: 5 items.
  - 15 + 5 = 20.
- Equality result: pre-split 20 == post-split 20. No test lost or added by the split.
