# Phase 4 Regression Checkpoint — LE Parity UNCHANGED after located-by-name alignment

Timestamp: 2026-06-17T15-00
Command: poetry run pytest tests/test_schema_loader_parity_le.py tests/test_default_schemas.py -q
EXIT_CODE: 0
Output Summary:
- tests/test_schema_loader_parity_le.py: 5 passed.
- tests/test_default_schemas.py: 25 passed.
- `default_le.schema.json` now sets `located_by_name: true` on `KEY` and the
  `YTD/YTG` discriminator only; no other LE field changed (required, in_output,
  dedup, derived, fill rules unchanged).
- `_by_name_optional_columns(default_le)` returns ["KEY", "YTD/YTG"].
- The LE emit path is `aggregate` and rebuilds canonical order via
  `_output_column_order`; the located-by-name flag did not change emitted output.
- LE parity passes UNCHANGED. No emitted-output change for default_le.
