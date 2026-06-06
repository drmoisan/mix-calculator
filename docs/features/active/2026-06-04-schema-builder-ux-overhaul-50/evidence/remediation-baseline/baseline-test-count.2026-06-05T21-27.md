# Baseline — Pre-Split Test Count and File Size (Cycle 2)

Timestamp: 2026-06-05T21-27
Command: env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest tests/gui/test_schema_builder_presenter.py --collect-only -q
EXIT_CODE: 0

Output Summary:
- Pre-split collected-item count (parametrized cases counted individually): 20.
  - 18 distinct `test_` functions; `test_validate_formula_rejects_bad_expressions` is
    parametrized into 3 cases, so 17 functions contribute 1 case each + 1 function
    contributes 3 cases = 20 collected items. (13 core functions, one parametrized to
    3 cases = 15 core items; 5 seeding functions = 5 items; 15 + 5 = 20.)
- File line count of tests/gui/test_schema_builder_presenter.py: 506 lines
  (`wc -l` newline count; matches expected 506).

This is the authoritative pre-split reference. Post-split sum across
test_schema_builder_presenter_core.py + test_schema_builder_presenter_seeding.py MUST
equal 20 collected items, and the over-cap 506-line original MUST be removed.
