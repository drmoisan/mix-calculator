# Final File-Size Check (Remediation Cycle 1, P7-T8)

Timestamp: 2026-06-05T20-28
Command: wc -l <new/modified .py files>
EXIT_CODE: 0
Output Summary: Every new and modified production/test `.py` file is at or under the
500-line cap. The largest touched files are 490 (app.py) and 489
(schema_builder_dialog.py). Extractions performed this cycle to honor the cap:
`_schema_builder_drag_tabs.py`, `_schema_provider_factory.py`,
`_schema_open_helpers.py`, and `_source_signal_wiring.py` (new modules), plus the
N1 test split into `test_schema_serialization_errors.py` and
`test_schema_migration.py`.

## Line counts (new and modified .py files this cycle)

| File | Lines | <= 500 |
|---|---|---|
| src/gui/app.py (modified) | 490 | yes |
| src/gui/widgets/schema_builder_dialog.py (modified) | 489 | yes |
| src/gui/_schema_wiring.py (modified) | 417 | yes |
| src/gui/widgets/_columns_tab_drag.py (modified, N2) | 411 | yes |
| src/gui/widgets/_key_tab_drag.py (modified, N2) | 409 | yes |
| src/gui/widgets/_schema_builder_drag_tabs.py (new) | 303 | yes |
| src/gui/widgets/_schema_builder_tabs.py (modified) | 275 | yes |
| src/gui/_schema_provider_factory.py (new) | 205 | yes |
| src/gui/_schema_open_helpers.py (new) | 160 | yes |
| src/gui/_schema_discovery_wiring.py (modified) | 132 | yes |
| src/gui/_source_signal_wiring.py (new) | 116 | yes |
| tests/gui/test_source_selection_presenter.py (modified) | 443 | yes |
| tests/gui/test_schema_builder_dialog.py (modified) | 414 | yes |
| tests/test_schema_serialization.py (split, N1) | 408 | yes |
| tests/gui/test_app_wiring_schema.py (modified) | 367 | yes |
| tests/test_schema_serialization_errors.py (new, N1) | 217 | yes |
| tests/gui/test_schema_provider_factory.py (new) | 138 | yes |
| tests/test_schema_migration.py (new, N1) | 72 | yes |

All listed files are at or under the 500-line cap.
