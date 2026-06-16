Timestamp: 2026-06-15T22-30
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
  1044 passed, 5 warnings in 36.07s
  Overall line coverage: 98%
  Overall branch coverage: 98%
  src\gui\widgets\_column_assignment_slot.py: 98% line / 93% branch (missing: 173->exit)
  src\gui\widgets\_columns_tab_drag.py: 94% line / ~87% branch (missing: 103, 308, 318, 329, 405->exit, 425->exit)
  All 15 tests in tests\gui\test_columns_tab_widgets.py passed, including:
    - test_drop_gesture_invokes_assign_column_once (updated: uses row.slot.dropEvent)
    - test_drop_row_drag_enter_accepts_text_payload (updated: uses row.slot.dragEnterEvent)
    - test_assigned_row_mousemove_starts_drag_carrying_source_and_origin (updated: patches slot_mod.QDrag)
    - test_unassigned_row_mousemove_does_not_start_drag (updated: patches slot_mod.QDrag)
    - test_assignment_slot_unassigned_style_has_dashed_border (new)
    - test_assignment_slot_assigned_shows_source_button (new)
    - test_source_token_has_visible_styling (new)
