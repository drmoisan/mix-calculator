# Acceptance Criteria Traceability (AC-11)

Timestamp: 2026-06-16T20-20

Each AC mapped to the passing test(s) that prove it. All tests run under
`QT_QPA_PLATFORM=offscreen` for GUI cases.

| AC | Behavior | Proving test(s) |
|---|---|---|
| AC-1 | Resizable top-level window, sizable below default, min/max/close | `tests/gui/test_schema_builder_dialog.py::test_dialog_is_resizable_top_level_window_below_default` |
| AC-2 | Identity description is multi-line, wraps, round-trips multi-line text | `test_identity_description_round_trips_multi_line_text`, `test_identity_description_is_wrapping_multiline_widget` (test_schema_builder_dialog.py) |
| AC-3 | Derived rows render/parse as `name = expression`, no `|` produced | `test_derived_rows_render_with_equals_separator`, `test_derived_parse_splits_on_first_equals_only` (test_schema_builder_dialog.py) |
| AC-4 | Display `[Name]`; stored `col("Name")`; formula grammar unchanged | `tests/gui/test_schema_builder_derived_format.py` (8 tests incl. names-with-spaces, evaluator-validates-stored-form); `test_derived_stores_col_form_and_displays_brackets`, `test_derived_bracketed_entry_strips_to_col_on_read` (test_schema_builder_dialog.py) |
| AC-5 | Double-click available column inserts bracketed name at cursor | `tests/gui/test_derived_formula_dialog.py::test_double_click_inserts_bracketed_name`, `::test_double_click_inserts_at_cursor_position` |
| AC-6 | Columns row chooser; chosen row's masked value replaces dtype glyph | `tests/gui/test_columns_tab_presenter.py::test_set_preview_row_*` (row 0, non-zero, None-restore, unassigned); `tests/gui/test_columns_tab_widgets.py::test_row_chooser_bounds_and_seam`, `::test_set_value_display_routes_masked_value_to_row` |
| AC-7 | Key tab multi-select composes ordered `column-ref` KeySpec; model/loader unchanged | `tests/gui/test_schema_builder_dialog.py::test_key_selection_round_trip`, `::test_key_multiselect_composes_ordered_column_ref_keyspec`, `::test_key_multiselect_round_trips_through_assemble_schema`; `tests/gui/test_schema_builder_dialog_live.py::test_live_key_tab_is_multiselect_with_seeded_selection`; `tests/gui/test_schema_builder_dialog_dedup.py::test_key_multiselect_tracks_check_order_interactively` |
| AC-8 | Dedup `auto` mode: no discriminator, dimension-groupby/measure-sum; LE explicit path unchanged | Model: `tests/test_schema_model.py::test_aggregate_mode_is_a_dedup_mode`. Loader + LE regression: `tests/test_schema_loader_dedup.py` (LE `select_from` unchanged; auto groupby/sum; no-discriminator construct; no-measure/no-dimension edges; aggregate still requires discriminator). GUI: `tests/gui/test_schema_builder_dialog_dedup.py::test_dedup_default_mode_is_auto`, `::test_dedup_auto_assembles_without_discriminator` |
| AC-9 | Preview tab renders result table from masked slice via tabular widget (wired production path) | `tests/gui/test_schema_builder_dialog_live.py::test_live_preview_tab_renders_table_from_masked_slice` (drives the real tab-change seam; does NOT call update_preview directly). Production caller grep: `src/gui/_schema_open_helpers.py:install_preview_refresh_handler` invokes `presenter.update_preview` |
| AC-10 | Missing-input / assembly-failure shows a specific message, not nothing | `tests/gui/test_schema_builder_dialog_live.py::test_live_preview_shows_no_source_message_for_blank_slice` ("No source data available to preview"); `::test_live_preview_shows_specific_missing_input_message` (specific SchemaValidationError name message) |
| AC-11 | Full toolchain green; coverage >= 85% line / >= 75% branch; all files <= 500 lines | `evidence/qa-gates/final-black.md`, `final-ruff.md`, `final-pyright.md`, `final-pytest.md`, `coverage-delta.md`, `file-size-scan.md` |

## AC-9 production-wiring note

`update_preview` had no production caller at baseline (single definition at
`schema_builder_presenter.py`). P6-T4 added the real call site in
`src/gui/_schema_open_helpers.py::install_preview_refresh_handler`, installed by
`open_schema_builder` in `src/gui/_schema_wiring.py`. P6-T5's integration test
drives the opened production dialog and the real `QTabWidget.currentChanged` seam
(not a direct `update_preview` call), asserting the `QTableWidget` is populated
from the masked slice.

## AC-8 LE-regression note

`tests/test_schema_loader_dedup.py::test_le_explicit_select_from_dedup_unchanged`
asserts the LE explicit `select_from`/discriminator collapse output is unchanged
(`Picked` from the discriminator-matched row; `Added` summed). The `DedupPolicy`
invariant was relaxed only for `auto`; `collapse`/`aggregate` still require a
discriminator (asserted by `test_aggregate_still_requires_discriminator_after_auto_added`).
