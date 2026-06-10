# Phase 2 — AC-1..AC-9 Traceability Matrix (Issue #62, Cycle 1, P2-T7)

Timestamp: 2026-06-10T09-25
AC source: docs/features/active/2026-06-09-edit-schema-columns-assignment-62/issue.md (## Acceptance Criteria)
Final suite: 1037 passed, 0 failed (P2-T4).

| AC | Requirement (abbrev) | Production change | Verifying test(s) | Result |
|---|---|---|---|---|
| AC-1 | load_existing renders aliased canonical columns as assigned | Cycle-0 alias-seeding in ColumnsTabPresenter.prepopulate / _seed_from_persisted_aliases (retained, P1-T10) | tests/gui/test_columns_tab_presenter.py::test_prepopulate_seeds_assignments_from_persisted_aliases_empty_pool | PASS |
| AC-2 | column with no persisted alias renders unassigned | Cycle-0 alias-seeding (retained) | tests/gui/test_columns_tab_presenter.py::test_prepopulate_leaves_alias_free_row_unassigned_empty_pool | PASS |
| AC-3 | live preview-slice fuzzy path unchanged; one-source-per-row invariant holds | Cycle-0 alias-seeding (retained); Fix A passes a live slice without altering the fuzzy path | tests/gui/test_columns_tab_presenter.py::test_live_fuzzy_match_wins_over_persisted_alias; tests/gui/test_edit_schema_wiring.py::test_edit_with_placeholder_short_circuits_without_opening | PASS |
| AC-4 | edit-then-save round-trip preserves persisted assignments | Cycle-0 alias-seeding (retained) | tests/gui/test_schema_builder_presenter_seeding.py / _core.py round-trip tests | PASS |
| AC-5 | Edit populates source pool from worksheet real headers (reader + best-header-row, honoring detected header row) | best_header_row (public) + read_worksheet_header_columns in source_selection_presenter.py (P1-T1); _build_edit_preview_slice wiring in _schema_discovery_wiring.py (P1-T3) | tests/gui/test_worksheet_header_columns.py (5 cases, P1-T2); tests/gui/test_edit_schema_wiring.py::test_edit_populates_preview_slice_from_real_worksheet_headers (P1-T4) | PASS |
| AC-6 | matching canonical rows render assigned against populated pool | Fix A end-to-end (preview_slice forwarded into open_schema_builder → DragTabBinder → prepopulate) | tests/gui/test_edit_schema_wiring.py::test_edit_renders_matching_canonical_rows_as_assigned (P1-T4) | PASS |
| AC-7 | Columns tab vertically scrollable | QScrollArea(setWidgetResizable(True)) wrap in build_columns_tab (_schema_builder_tabs.py, P1-T6) | tests/gui/test_columns_tab_widgets.py::test_columns_tab_wraps_widget_in_resizable_scroll_area (P1-T7) | PASS |
| AC-8 | Schema Builder window resizable with min/max/restore controls | apply_schema_builder_window_flags (_schema_builder_window_setup.py) called from SchemaBuilderDialog.__init__ (P1-T8) | tests/gui/test_schema_builder_dialog.py::test_dialog_exposes_minimize_and_maximize_window_controls (P1-T9) | PASS |
| AC-9 | Edit degrades gracefully with no file/sheet (no crash, empty pool, no reader call) | blank-guard in read_worksheet_header_columns + None preview_slice in _build_edit_preview_slice (P1-T1/P1-T3) | tests/gui/test_worksheet_header_columns.py blank-path/blank-sheet/empty-preview cases (P1-T2); tests/gui/test_edit_schema_wiring.py::test_edit_no_file_no_sheet_opens_with_empty_pool_no_reader_call (P1-T5) | PASS |

Every AC-1..AC-9 maps to a production change and at least one passing test. No
gaps. AC-1..AC-4 cycle-0 tests retained at original assertion strength (P1-T10).
