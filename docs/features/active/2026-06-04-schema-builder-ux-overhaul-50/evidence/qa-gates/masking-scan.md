# Confidentiality Masking Scan (Remediation Cycle 1, P7-T7)

Timestamp: 2026-06-05T20-28
Command: env -u VIRTUAL_ENV poetry run python scripts/checks/scan_masked_fixtures.py
EXIT_CODE: 0
Output Summary: masking-scan: clean (no forbidden patterns found). The full-tree
scan reported clean, confirming no real workbook numeric values or proprietary
source column names were introduced by this remediation cycle.

## Files changed/added this cycle (Decision 5 review)

New source modules and changed files introduce only synthetic/masked content:

- `src/gui/_schema_provider_factory.py` — the production preview slice uses
  obviously-synthetic placeholders (`masked_<col>_<row>`); no real workbook values.
- `src/gui/widgets/_schema_builder_drag_tabs.py`, `_schema_open_helpers.py`,
  `_source_signal_wiring.py` — pure wiring; carry no data fixtures.
- Test files (`test_schema_builder_dialog.py`, `test_schema_provider_factory.py`,
  `test_app_wiring_schema.py`, `test_source_selection_presenter.py`) use fabricated
  names ("Customer", "Sales", "Region", "Notes", "Account") and synthetic cell
  values ("Cust-0001", "Reg-A", "masked_*"); no proprietary content.
- The N1 test split (`test_schema_migration.py`, `test_schema_serialization_errors.py`)
  preserves the prior fabricated JSON fixtures verbatim; no new data introduced.

## Gate command

```
env -u VIRTUAL_ENV poetry run python scripts/checks/scan_masked_fixtures.py
```

A non-zero exit indicates a forbidden pattern (a real workbook value or a
proprietary source column name) was found and must be masked before commit.
