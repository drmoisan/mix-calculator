# columns-tab-bidirectional-drag (Issue #64)

- Date captured: 2026-06-14
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/columns-tab-bidirectional-drag/ (Issue #64)

- Issue: #64
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/64
- Last Updated: 2026-06-15
- Work Mode: minor-audit

## Problem / Why

The Columns tab of the schema editor only supports one-directional drag (pool → canonical row). Once a source column is assigned to a canonical row, it is displayed as a static `QLabel` with no drag affordance. Users cannot:

1. Drag an assigned source column to a different canonical row (re-assign).
2. Drag an assigned source column back to the unassigned pool (unassign / clear).

The intended UX was bidirectional: all unmatched column names at the top (pool), assigned names draggable to another canonical row or back into the unassigned bucket.

**Root cause**: `ColumnDropRow._assignment` is a `QLabel` with no `mouseMoveEvent`. `ColumnsTabWidget` has no drop handling for the pool area. Once a column is consumed (assigned), there is no UI affordance to release it.

## Proposed Behavior

1. When a source column is assigned to a canonical row, it renders as a draggable widget (not a static label).
2. Dragging that assigned widget onto another canonical row re-assigns it (the original row is cleared, the new row is assigned).
3. Dragging that assigned widget back onto the pool area (any part of `ColumnsTabWidget` not covered by a canonical row) unassigns it, returning it to the pool.
4. Pool tokens (unassigned columns) remain draggable onto canonical rows as before.

The existing `ColumnsTabPresenter.assign_column` already handles re-assignment correctly (releases old target, releases old source binding, binds new pair). The gap is purely in the widget layer — no presenter logic changes are required.

## Acceptance Criteria (early draft)

- [x] AC-1: Dragging an assigned source column onto a different canonical row re-assigns it (old row shows unassigned, new row shows the source).
- [x] AC-2: Dragging an assigned source column onto the pool area unassigns it (the row shows "(unassigned)", the token returns to the pool).
- [x] AC-3: Pool tokens (unassigned columns) continue to be draggable onto canonical rows as before (no regression).
- [x] AC-4: Tests cover the new drag-from-assignment and pool-drop paths at the widget seam level.

## Constraints & Risks

- `_columns_tab_drag.py` is at 441 lines; additions must keep it at or below 500.
- The MIME approach carries source name as `text/plain` (existing) and canonical origin as a secondary MIME key `application/x-canonical-origin` (new) so pool-drop and row-drop can be distinguished.
- The `ColumnDropRow` already has `setAcceptDrops(True)` + `dragEnterEvent` + `dropEvent`; adding `mouseMoveEvent` to make it a drag source when assigned must not interfere with its role as a drop target.

## Test Conditions to Consider

- [ ] `ColumnDropRow.mouseMoveEvent` starts a drag carrying both source and canonical-origin MIME when a source is assigned.
- [ ] `ColumnDropRow.mouseMoveEvent` does NOT start a drag when no source is assigned.
- [ ] `ColumnsTabWidget.dropEvent` fires when a drag with canonical-origin MIME lands outside a canonical row and calls `clear_row(canonical_origin)`.
- [ ] `ColumnsTabWidget.dropEvent` is NOT triggered by plain pool-token drags (no canonical-origin MIME).

## Next Step

- [ ] Promote to GitHub issue (bug template)
- [ ] Create `docs/features/active/` folder from the template