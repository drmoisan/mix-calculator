# Final File-Size Check (P15-T7)

Timestamp: 2026-06-05T13-55
Command: wc -l <new/modified .py files>
EXIT_CODE: 0
Output Summary: Every new and modified production/test/script `.py` file is at or
under the 500-line cap. The two largest files are at 497 lines.

## Line counts (new and modified .py files)

| File | Lines | <= 500 |
|---|---|---|
| src/gui/widgets/source_input_widget.py | 497 | yes |
| src/gui/app.py | 497 | yes |
| src/gui/presenters/schema_builder_presenter.py | 461 | yes |
| src/_schema_model_specs.py | 461 | yes |
| src/gui/widgets/schema_builder_dialog.py | 452 | yes |
| src/_schema_loader_helpers.py | 445 | yes |
| src/schema_serialization.py | 423 | yes |
| src/gui/widgets/_columns_tab_drag.py | 411 | yes |
| src/gui/widgets/_key_tab_drag.py | 409 | yes |
| src/gui/_schema_wiring.py | 403 | yes |
| src/gui/_schema_view_protocols.py | 374 | yes |
| src/gui/presenters/_columns_tab_presenter.py | 347 | yes |
| src/gui/presenters/source_selection_presenter.py | 314 | yes |
| src/gui/presenters/_schema_builder_state.py | 288 | yes |
| src/schema_model.py | 283 | yes |
| src/gui/widgets/_schema_builder_tabs.py | 241 | yes |
| src/gui/widgets/_derived_formula_dialog.py | 231 | yes |
| src/gui/presenters/_key_tab_presenter.py | 202 | yes |
| src/dtype_check.py | 199 | yes |
| src/gui/_columns_tab_protocol.py | 129 | yes |
| src/gui/_schema_discovery_wiring.py | 124 | yes |
| src/gui/_schema_activation.py | 120 | yes |
| src/gui/widgets/_source_input_button_wiring.py | 99 | yes |
| src/gui/widgets/_dtype_check_widget.py | 94 | yes |
| src/gui/_schema_build_specs.py | 89 | yes |
| src/gui/_key_tab_protocol.py | 87 | yes |

(Test files under `tests/` are likewise within the cap; the largest touched test
module is well under 500 lines.)
