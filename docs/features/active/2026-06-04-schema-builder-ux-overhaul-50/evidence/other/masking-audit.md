# Confidentiality Masking Audit (P13-T1)

Timestamp: 2026-06-05T13-20

## Scope

Every new or changed test fixture and artifact introduced by this feature was
reviewed for real workbook values and proprietary source column names. All values
used are synthetic/masked; no real workbook data or proprietary source column
names are committed.

## Fixture files reviewed (synthetic-only confirmed)

- `tests/test_dtype_check.py` — synthetic tokens only (`"alpha"`, `"beta"`,
  `"1"`, `"1.5"`, `"true"`, `"bad"`, `"notnum"`, ISO dates). No workbook values.
- `tests/gui/test_columns_tab_presenter.py` — synthetic source/canonical names
  (`"customer"`, `"sales"`, `"extra_col"`, `"col_a"`) and synthetic cell values.
- `tests/gui/test_columns_tab_widgets.py` — synthetic header/cell values
  (`"col_a"`, `"bad"`).
- `tests/gui/test_key_tab_presenter.py` / `test_key_tab_widget.py` — synthetic
  column names (`"Customer"`, `"SKU #"`) and literal segments (`"-"`, `"PRE-"`).
- `tests/gui/test_derived_formula_dialog.py` — synthetic column names and
  expressions (`"Sales * Units"`).
- `tests/gui/test_schema_activation.py` — synthetic schema/column names.
- `tests/gui/test_schema_builder_presenter.py` — synthetic schema fixtures
  (`"tmpl"`, `"Customer"`, alias `"cust_col"`).
- `tests/gui/test_schema_discovery_wiring.py` — synthetic header rows.
- `tests/gui/test_source_selection_presenter.py` — synthetic headers
  (`"Customer"`, `"Net Sales"`).
- `tests/gui/integration/test_behavioral_schema_import.py` — uses the existing
  in-repo synthetic fixtures (`tests/aop_fixtures`, `tests/le_fixtures`); the new
  cases add only synthetic header/column names.
- `src/schemas/default_le.schema.json` / `default_aop.schema.json` — migrated in
  place; column names are the as-built canonical schema names already committed
  prior to this feature (no new proprietary names introduced) and contain no
  sample data values.

## Result

All reviewed fixtures contain synthetic/masked content only. The automated masking
scan (`scripts/checks/scan_masked_fixtures.py`) reports clean across the changed
files and the full tree (see `evidence/qa-gates/masking-scan.md`).
