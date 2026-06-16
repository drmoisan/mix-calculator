---
Timestamp: 2026-06-15T01-02
---

# Acceptance Criteria Verification — Issue #64

## AC-1: Re-assign via drag (row → row)

**Status: PASS**

Evidence: `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin` PASSED in P4-T4
run (1041 passed, 0 failed).

The test verifies that `ColumnDropRow.mouseMoveEvent` (when the row is assigned) produces
a `QMimeData` with:
- `text/plain` = the assigned source column name
- `application/x-canonical-origin` = this row's canonical name

When a user drags from an assigned row and drops onto another `ColumnDropRow`, the target
row's `dropEvent` reads `text/plain` via `e.mimeData().text()` and calls
`_on_drop(source, canonical)` — the existing re-assign path. The MIME design is validated
as correctly supporting re-assignment without changes to `ColumnDropRow.dropEvent`.

## AC-2: Unassign via pool drop (row → pool)

**Status: PASS**

Evidence: `test_pool_dropEvent_with_canonical_origin_calls_clear_row` PASSED in P4-T4 run.

The test verifies that `ColumnsTabWidget.dropEvent` reads `CANONICAL_ORIGIN_MIME` from the
drop event and calls `clear_row(canonical_origin)` with the decoded canonical name. The
`clear_row` method routes through `_on_release` to the presenter's `clear_row`, which is
wired in `DragTabBinder.__init__` (`columns_widget.clear_row = self._columns_presenter.clear_row`).

## AC-3: No regression on pool-to-row drag

**Status: PASS**

Evidence: P4-T4 run shows 1041 passed, 0 failed. All 8 pre-existing tests in
`test_columns_tab_widgets.py` remain green:
- `test_columns_tab_wraps_widget_in_resizable_scroll_area` PASSED
- `test_pool_renders_one_token_per_source_column` PASSED
- `test_rows_display_name_description_and_dtype` PASSED
- `test_drop_gesture_invokes_assign_column_once` PASSED
- `test_dtype_indicator_shows_green_for_coercible` PASSED
- `test_dtype_indicator_shows_red_with_masked_example` PASSED
- `test_source_token_starts_drag_on_left_button_move` PASSED
- `test_drop_row_drag_enter_accepts_text_payload` PASSED

No pre-existing test was deleted, modified, or weakened.

## AC-4: Test coverage of new paths

**Status: PASS**

Evidence: All 4 new tests are present, correctly named, and PASSED in P4-T4 run.

| Test Name | Status |
|-----------|--------|
| `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin` | PASSED |
| `test_unassigned_row_mousemove_does_not_start_drag` | PASSED |
| `test_pool_dropEvent_with_canonical_origin_calls_clear_row` | PASSED |
| `test_pool_dragEnterEvent_rejects_missing_canonical_origin` | PASSED |

These four tests cover:
- The happy path for assigned-row drag (AC-1, AC-4)
- The guard-clause branch for unassigned rows (P1-T4 branch)
- The pool-area drop unassign path (AC-2, AC-4)
- The negative path: pool-token drags rejected by `ColumnsTabWidget.dragEnterEvent` (P1-T7)

## Overall Verdict: ALL 4 ACs PASS
