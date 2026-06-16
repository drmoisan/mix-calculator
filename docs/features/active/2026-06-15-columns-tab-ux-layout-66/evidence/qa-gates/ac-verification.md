Timestamp: 2026-06-15T22-30

# Acceptance Criteria Verification

## AC-1: Source column tokens render with visible text

Evidence: test_source_token_has_visible_styling PASSED in P4-T4 pytest run (1044 passed).
Verification: SourceColumnToken.__init__ calls self.setStyleSheet(...) with "color: white" and
  "background: #5c88d4". The test asserts token.styleSheet() != "".
Verdict: PASS

## AC-2: Each canonical row is horizontal (QHBoxLayout)

Evidence: grep src\gui\widgets\_columns_tab_drag.py for QHBoxLayout:
  Line 30: QHBoxLayout,  (import)
  Line 160: row = QHBoxLayout(self)  (inside ColumnDropRow.__init__)
ColumnDropRow.__init__ uses QHBoxLayout — label on left, slot in middle, indicator on right.
Verdict: PASS

## AC-3: Assignment slot shows dashed "(drop here)" unassigned; solid-border assigned button

Evidence:
  test_assignment_slot_unassigned_style_has_dashed_border PASSED — asserts "dashed" in slot.styleSheet().
  test_assignment_slot_assigned_shows_source_button PASSED — asserts slot.assignment_text() == "col_a"
    after slot.set_assignment("col_a").
Both tests passed in P4-T4 pytest run (1044 passed).
Verdict: PASS

## AC-4: Compact row spacing

Evidence: grep src\gui\widgets\_columns_tab_drag.py for setSpacing and setContentsMargins:
  Line 289: self._pool_box.setSpacing(4)
  Line 291: self._rows_box.setSpacing(2)
  Line 292: self._rows_box.setContentsMargins(0, 0, 0, 0)
Both spacing calls are present in ColumnsTabWidget.__init__.
Verdict: PASS

## AC-5: Bidirectional drag behaviors from #64 continue to function

Evidence: all six tests from #64 PASSED in P4-T4 pytest run (1044 passed):
  - test_drop_gesture_invokes_assign_column_once: PASSED (updated to use row.slot.dropEvent)
  - test_drop_row_drag_enter_accepts_text_payload: PASSED (updated to use row.slot.dragEnterEvent)
  - test_assigned_row_mousemove_starts_drag_carrying_source_and_origin: PASSED
      (updated to patch slot_mod.QDrag and call row.slot.mouseMoveEvent)
  - test_unassigned_row_mousemove_does_not_start_drag: PASSED
      (updated to patch slot_mod.QDrag and call row.slot.mouseMoveEvent)
  - test_pool_dropEvent_with_canonical_origin_calls_clear_row: PASSED (unchanged)
  - test_pool_dragEnterEvent_rejects_missing_canonical_origin: PASSED (unchanged)
Verdict: PASS

## Overall Verdict: ALL 5 ACs PASS
