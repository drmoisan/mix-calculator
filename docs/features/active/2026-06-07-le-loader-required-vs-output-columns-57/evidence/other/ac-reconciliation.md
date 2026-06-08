# AC Reconciliation — Issue #57

Timestamp: 2026-06-07T20-45
Work Mode: full-bug (AC source: spec.md; mirrored in issue.md)

- AC-1 (LE sheet without YTD/YTG imports): PASS.
  Evidence: tests/test_normalize_le.py::test_load_source_without_ytd_ytg_succeeds_and_drops_it;
  tests/test_normalize_le_columns.py::test_ytd_ytg_absent_is_not_required_and_not_in_selection.
  qa-gates/batch2-pytest-coverage.md, regression-testing/parity-le-aop-suite.md.

- AC-2 (LE sheet without source Super Category imports; output from PPG): PASS.
  Evidence: tests/test_normalize_le.py::test_load_source_without_super_category_output_super_from_ppg;
  tests/test_normalize_le_columns.py::test_source_super_category_absent_is_not_required_and_not_in_selection.

- AC-3 (require only 23 must-have; YTD/YTG + Super Category optional): PASS.
  Evidence: src/_normalize_le_columns.py REQUIRED_COLUMNS (23) + OPTIONAL_BY_NAME + EXPECTED_COLUMNS = REQUIRED_COLUMNS;
  tests/test_normalize_le_columns.py::test_required_columns_has_exactly_23_entries and
  ::test_optional_by_name_is_ytd_ytg_and_super_category and ::test_both_optionals_present_are_located_and_carried_to_canonical_names.

- AC-4 (parity; existing LE loader tests pass): PASS.
  Evidence: tests/test_normalize_le.py::test_full_column_source_output_parity_with_standard_fixture;
  existing test_load_source_header_and_columns green; regression-testing/parity-le-aop-suite.md (100 passed).

- AC-5 (missing must-have raises naming it): PASS.
  Evidence: tests/test_normalize_le_columns.py::test_missing_required_column_raises_value_error_naming_it (PPG);
  existing tests/test_etl_columns.py missing-required cases (23-col set) green.

- AC-6 (flat sheet -> TARGET_COLUMNS): PASS.
  Evidence: tests/test_normalize_le_header.py::test_flat_le84data_style_sheet_imports_to_target_columns;
  tests/test_normalize_le.py::test_load_source_without_both_optionals_yields_all_target_columns.

- AC-7 (load_aop unchanged; AOP imports unaffected): PASS.
  Evidence: src/load_aop.py not modified (git diff shows no change); tests/test_load_aop.py green in
  regression-testing/parity-le-aop-suite.md.

- AC-8 (full toolchain + coverage + file-size): PASS.
  Evidence: final-black.md, final-ruff.md, final-pyright.md (all EXIT 0), final-pytest-coverage.md
  (987 passed, line 99.08% / branch 93.96%), coverage-delta.md (PASS), final-file-size.md (all <= 500).
