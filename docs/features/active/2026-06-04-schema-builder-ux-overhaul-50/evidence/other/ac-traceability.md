# Acceptance-Criteria Traceability (P15-T8)

Timestamp: 2026-06-05T13-58

Each spec Acceptance Criterion maps to at least one passing test.

| Acceptance Criterion | Passing test(s) |
|---|---|
| Import button disabled until a schema is selected; re-disables on placeholder | `test_source_input_widget.py::test_import_button_starts_disabled`, `::test_selecting_schema_enables_import_button`, `::test_returning_to_placeholder_disables_import_button`; `test_main_window.py::test_main_window_exposes_import_le_btn_publicly` |
| Activating a source tab auto-selects best match; placeholder when none | `test_source_selection_presenter.py::test_on_schema_discovery_proceed_selects_matched_schema`, `::test_on_schema_discovery_no_match_sets_placeholder`; `test_schema_discovery_wiring.py::test_tab_activation_triggers_schema_discovery` |
| Edit-schema loads existing schema and re-saves | `test_schema_builder_presenter.py::test_load_existing_renders_structured_key_and_dtypes`, `::test_edit_load_modify_save_round_trips` |
| New-from-template seeds from closest existing | `test_schema_builder_presenter.py::test_new_from_template_seeds_clears_name`, `::test_new_from_template_save_as_does_not_overwrite_template`; `test_schema_activation.py::test_partial_match_selects_closest_template` |
| Builder accepts required/optional specs, default key pattern, masked preview slice | `test_schema_builder_presenter.py::test_seed_from_caller_pre_lists_rows_and_parses_key`, `::test_seed_from_caller_reads_preview_slice_without_io`; `test_app_wiring_schema.py::test_wire_build_buttons_seeds_presenter_from_caller_specs` |
| Columns tab renders draggable source-column buttons | `test_columns_tab_widgets.py::test_pool_renders_one_token_per_source_column` |
| Required/optional rows pre-populate via fuzzy match; matched col consumed | `test_columns_tab_presenter.py::test_prepopulate_binds_best_fuzzy_match`, `::test_consumed_column_excluded_from_pool`, `::test_consumed_column_cannot_match_second_row` |
| Matched source→canonical mapping persists as aliases; reload re-matches | `test_columns_tab_presenter.py::test_prepopulate_persists_alias`; `test_schema_builder_presenter.py::test_load_existing_renders_structured_key_and_dtypes` (alias round-trip) |
| Activation-time matching runs first against persisted alias columns; partial → new-from-template | `test_schema_activation.py::test_full_match_proceeds_and_selects_schema`, `::test_partial_match_selects_closest_template`; `test_source_selection_presenter.py::test_on_schema_discovery_partial_match_offers_new_from_template` |
| Matched columns show green check / red X with failing example | `test_columns_tab_presenter.py::test_dtype_indicator_pushed_for_coercible_match`, `::test_dtype_indicator_reports_failing_example_for_non_coercible`; `test_columns_tab_widgets.py::test_dtype_indicator_shows_red_with_masked_example`; `test_dtype_check.py` (pure logic) |
| Key tab drag-drop parts + repeatable Generic Text; default pattern parsed | `test_key_tab_presenter.py::test_parts_maintain_insertion_order`, `::test_generic_text_is_repeatable_with_own_values`, `::test_default_pattern_parses_into_ordered_parts`; `test_key_tab_widget.py::test_column_drop_invokes_add_key_part_as_column_ref`, `::test_generic_text_drop_invokes_add_key_part_as_literal` |
| Dedup defaults to aggregate with Key discriminator; dropdown-only | `test_schema_builder_dialog.py::test_dedup_default_mode_is_aggregate`, `::test_dedup_discriminator_defaults_to_key`, `::test_dedup_discriminator_is_dropdown_of_existing_columns`, `::test_dedup_unknown_discriminator_is_rejected` |
| Derived precedes Columns; dialog creates derived rows; derived appear on Columns | `test_schema_builder_dialog.py::test_tab_order_matches_decision_10`; `test_derived_formula_dialog.py::test_dialog_lists_available_names_and_accepts_expression`, `::test_dialog_surfaces_formula_error_for_invalid_expression`; `test_schema_builder_presenter.py::test_add_derived_appends_row_in_order`; `test_columns_tab_presenter.py::test_derived_column_appears_as_selectable_row` |
| expected_dtype added; version bumped; forward migration; defaults migrated to aggregate | `test_schema_model.py` (expected_dtype), `test_schema_serialization.py` (round-trip + migration), `test_default_schemas.py::test_bundled_defaults_are_format_2_0_with_structured_key_parts`, `::test_le_default_uses_aggregate_dedup_mode`, `::test_bundled_numeric_columns_have_float_expected_dtype` |
| No real workbook values or proprietary column names committed (masking scan) | `evidence/qa-gates/masking-scan.md` (EXIT_CODE 0, clean) |

All 922 tests pass; the mapped tests are part of that green suite.
