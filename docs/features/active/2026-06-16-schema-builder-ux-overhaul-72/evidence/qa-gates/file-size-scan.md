# File-Size Scan — 500-Line Cap (AC-11)

Timestamp: 2026-06-16T18-44

Scope: all changed production and test Python files (modified + new).

Result: PASS — no file exceeds 500 lines.

| Lines | File |
|---|---|
| 75  | src/_schema_loader_auto_dedup.py (new) |
| 471 | src/_schema_loader_helpers.py |
| 484 | src/_schema_model_specs.py |
| 147 | src/gui/_columns_tab_protocol.py |
| 211 | src/gui/_schema_open_helpers.py |
| 421 | src/gui/_schema_wiring.py |
| 475 | src/gui/presenters/_columns_tab_presenter.py |
| 369 | src/gui/presenters/_schema_builder_state.py |
| 476 | src/gui/presenters/schema_builder_presenter.py |
| 426 | src/gui/widgets/_columns_tab_drag.py |
| 185 | src/gui/widgets/_columns_tab_drop_row.py (new) |
| 80  | src/gui/widgets/_columns_tab_source_token.py (new) |
| 288 | src/gui/widgets/_derived_formula_dialog.py |
| 117 | src/gui/widgets/_dtype_check_widget.py |
| 262 | src/gui/widgets/_key_multiselect_widget.py (new) |
| 219 | src/gui/widgets/_schema_builder_derived_format.py (new) |
| 192 | src/gui/widgets/_schema_builder_drag_tabs.py |
| 361 | src/gui/widgets/_schema_builder_tabs.py |
| 73  | src/gui/widgets/_schema_builder_window_setup.py |
| 133 | src/gui/widgets/_schema_dedup_discriminator.py (new) |
| 114 | src/gui/widgets/_schema_dialog_surfaces.py (new) |
| 117 | src/gui/widgets/_schema_preview_table.py (new) |
| 494 | src/gui/widgets/schema_builder_dialog.py |
| 418 | tests/gui/test_columns_tab_presenter.py |
| 482 | tests/gui/test_columns_tab_widgets.py |
| 106 | tests/gui/test_derived_formula_dialog.py |
| 109 | tests/gui/test_schema_builder_derived_format.py (new) |
| 401 | tests/gui/test_schema_builder_dialog.py |
| 152 | tests/gui/test_schema_builder_dialog_dedup.py (new) |
| 392 | tests/gui/test_schema_builder_dialog_live.py (new) |
| 180 | tests/test_schema_loader_dedup.py (new) |
| 435 | tests/test_schema_model.py |

Watch-list confirmation:
- `_columns_tab_drag.py`: 426 (was 497 baseline; `SourceColumnToken` and `ColumnDropRow` extracted).
- `schema_builder_dialog.py`: 494 (was 499 baseline; accessors delegated to helper modules; namespace imports).
- Newly extracted modules all under cap: `_columns_tab_drop_row.py` (185), `_columns_tab_source_token.py` (80), `_key_multiselect_widget.py` (262), `_schema_builder_derived_format.py` (219), `_schema_dedup_discriminator.py` (133), `_schema_dialog_surfaces.py` (114), `_schema_preview_table.py` (117), `_schema_loader_auto_dedup.py` (75).
