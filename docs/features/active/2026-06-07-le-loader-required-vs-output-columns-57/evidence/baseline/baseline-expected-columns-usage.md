# Phase 0 — EXPECTED_COLUMNS Importer/User Survey

Timestamp: 2026-06-07T20-45
Command: Grep pattern "EXPECTED_COLUMNS" across src/ and tests/
EXIT_CODE: 0

Output Summary:

Each module/test defines and uses its OWN module-local EXPECTED_COLUMNS, except
tests/test_etl_columns.py, which imports LE EXPECTED_COLUMNS from src.normalize_le.

LE EXPECTED_COLUMNS (src/_normalize_le_columns.py:90, re-exported from src/normalize_le.py:62):
- src/_normalize_le_columns.py:90 (definition), :152 (resolve_columns required set), :162 (selection build)
- src/normalize_le.py:36 (import), :62 (__all__ re-export), :151 (header tokens), :177 (columns_to_keep)
- tests/test_etl_columns.py:17 (import from src.normalize_le), and lines 50,54,60,63,67,73,76,86,89,99,103,109,112,116,123,128 (uses as both actual and expected arg to resolve_columns)

Other (NOT affected — own EXPECTED_COLUMNS, different modules):
- src/load_aop.py / src/_load_aop_helpers.py:83 — AOP EXPECTED_COLUMNS
- src/load_skulu.py:47 — skulu EXPECTED_COLUMNS
- tests/test_load_aop.py:21,53 — imports AOP EXPECTED_COLUMNS (own module)
- tests/test_load_skulu.py:18,42,122,136 — imports skulu EXPECTED_COLUMNS (own module)

Confirmation: tests/test_etl_columns.py is the SOLE consumer of LE EXPECTED_COLUMNS
outside src/. It uses LE EXPECTED_COLUMNS as BOTH the actual and the expected argument to
resolve_columns in the identity/reorder/extra cases (self-consistent under a 23-column
redefinition). The trailing-space case mutates "Customer" (required), the fuzzy case mutates
"GtN Mapping" (required), and the missing-required cases drop "PPG" (required). None of the
cases reference YTD/YTG or Super Category, so all remain valid with the 23-column set without
fixture edits. AOP and skulu importers are unaffected (they import their own EXPECTED_COLUMNS).
