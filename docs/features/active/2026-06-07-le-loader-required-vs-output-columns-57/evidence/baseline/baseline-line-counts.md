# Phase 0 — Baseline Line Counts

Timestamp: 2026-06-07T20-45
Command: pwsh -NoProfile -Command "foreach ($f in @(...)) { \"$f = $((Get-Content $f).Count)\" }"
EXIT_CODE: 0

Output Summary (measured line counts before edits):
- src/normalize_le.py = 470
- src/_normalize_le_columns.py = 166
- tests/test_normalize_le.py = 446
- tests/test_etl_columns.py = 168
- tests/test_normalize_le_header.py = 59
- tests/le_fixtures.py = 353

All files currently <= 500 lines. The largest production file in scope (normalize_le.py = 470) must stay under 500 after the load_source edit.
