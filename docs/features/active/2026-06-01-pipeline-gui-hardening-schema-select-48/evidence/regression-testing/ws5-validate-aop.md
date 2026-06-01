# WS5 Regression Evidence — Corrected validate_aop YTD Identity (Issue #48)

Timestamp: 2026-06-01T12-55

Command: env -u VIRTUAL_ENV poetry run pytest tests/test_load_aop_helpers.py --cov=src._load_aop_helpers --cov-branch
EXIT_CODE: 0

Output Summary:
- Tests: 9 passed in the dedicated WS5 helper test module. 0 failed.
- Module coverage (this targeted run): src/_load_aop_helpers.py 51% line, 3 partial
  branches. The 51% reflects that this targeted run exercises only the WS5
  functions (`build_per_row_checks` and `validate_aop`); the remaining helpers
  (`build_parser`, `print_summary`, `safe_index_name`, `clean_label_sentinels`,
  `coerce_numeric`) are covered by tests/test_load_aop.py and
  tests/test_load_aop_io.py. In the full suite run these helpers are 100% covered.
- WS5 functions specifically exercised by this module:
  - `build_per_row_checks`: YTG-present split (YTD=Jan..Apr, YTG=May..Dec),
    YTG-absent full-year YTD, quarter identities, and a Hypothesis property test
    asserting the YTD/YTG month-set partition (AC-8, AC-9, AC-15).
  - `validate_aop`: YTG-present synthetic frame passes (YTD=sum(Jan..Apr),
    YTG=sum(May..Dec)); full-year synthetic frame passes (no YTG, YTD=sum(Jan..Dec));
    and three negative-path frames raise ValueError on genuine YTD/YTG identity
    violations (AC-10).

Correctness notes:
- The identity is CORRECTED, not relaxed: every negative-path test confirms a
  genuine identity violation still raises ValueError.
- The load-time blank-fill map in `src/load_aop.py` now reuses the same
  `build_per_row_checks` map so a blank-filled total is consistent with what
  `validate_aop` then checks.

AC-15 (synthetic-only): All values in tests/test_load_aop_helpers.py are synthetic
(small integer-derived floats such as range(1, 13)). No confidential workbook
figures appear in any committed file.
