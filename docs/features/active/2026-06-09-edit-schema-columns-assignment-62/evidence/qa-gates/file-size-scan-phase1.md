# Phase 1 — 500-Line File-Size Scan (Issue #62, Cycle 1, P1-T11)

Timestamp: 2026-06-10T09-25

Output Summary (line count per changed file; 500-line cap):

Production:
- src/gui/_schema_discovery_wiring.py — 336 lines — under cap
- src/gui/presenters/source_selection_presenter.py — 436 lines — under cap
- src/gui/widgets/_schema_builder_tabs.py — 290 lines — under cap
- src/gui/widgets/schema_builder_dialog.py — 499 lines — under cap
- src/gui/widgets/_schema_builder_window_setup.py — 61 lines — under cap (new
  helper extracted to keep the dialog under the cap, P1-T8)
- src/gui/widgets/_columns_tab_drag.py — 441 lines — under cap (added public
  assignment_text / row_assignment_text test seams for AC-6)

Test:
- tests/gui/test_worksheet_header_columns.py — 175 lines — under cap (new)
- tests/gui/test_columns_tab_widgets.py — 189 lines — under cap
- tests/gui/test_edit_schema_wiring.py — 471 lines — under cap
- tests/gui/test_schema_builder_dialog.py — 438 lines — under cap

Result: every changed production and test file is strictly under 500 lines. No
helper extraction beyond the already-extracted _schema_builder_window_setup.py
was required. src/gui/widgets/source_input_widget.py was NOT modified.
