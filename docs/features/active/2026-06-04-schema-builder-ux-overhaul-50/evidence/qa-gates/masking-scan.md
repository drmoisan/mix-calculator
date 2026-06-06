# Confidentiality Masking Scan (P13-T2 / P13-T3)

Timestamp: 2026-06-05T13-21
Command: poetry run python scripts/checks/scan_masked_fixtures.py
EXIT_CODE: 0
Output Summary: masking-scan: clean (no forbidden patterns found). The scan was run
both across the feature's changed files explicitly and across the full tree; both
runs reported clean, confirming no real workbook numeric values or proprietary
source column names are committed.

## Documented gate command (P13-T3)

Run this command before committing new fixtures so future additions are checked:

```
poetry run python scripts/checks/scan_masked_fixtures.py
```

A non-zero exit indicates a forbidden pattern (a real workbook value or a
proprietary source column name) was found and must be masked before commit.

## Changed-file scan invocation (P13-T2)

```
poetry run python scripts/checks/scan_masked_fixtures.py \
  tests/gui/test_columns_tab_presenter.py tests/gui/test_columns_tab_widgets.py \
  tests/gui/test_derived_formula_dialog.py tests/gui/test_key_tab_presenter.py \
  tests/gui/test_key_tab_widget.py tests/gui/test_schema_activation.py \
  tests/gui/test_schema_builder_presenter.py tests/gui/test_source_selection_presenter.py \
  tests/gui/test_schema_discovery_wiring.py tests/test_dtype_check.py \
  tests/test_default_schemas.py tests/gui/integration/test_behavioral_schema_import.py \
  src/schemas/default_le.schema.json src/schemas/default_aop.schema.json
```

EXIT_CODE: 0 — clean.
