# columns-tab-ux-layout (Issue #66)

- Date captured: 2026-06-15
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/columns-tab-ux-layout/ (Issue #66)

- Issue: #66
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/66
- Last Updated: 2026-06-16
- Work Mode: minor-audit

## Problem / Why

After the bidirectional drag fix (#64), the Columns tab has the correct logic but several critical visual problems make it unusable:

1. **Source column token text invisible** — `SourceColumnToken` QPushButton items in the pool render as empty gray rectangles; text is not visible (Windows theme contrast issue).
2. **Assignment display indistinguishable from canonical label** — the assigned source name is a plain `QLabel` below the canonical name with identical styling; users cannot tell which is the canonical name and which is the assignment.
3. **Layout is vertical, not horizontal** — `ColumnDropRow` uses `QVBoxLayout`, stacking canonical label, assignment, and dtype indicator. The assignment should be BESIDE the canonical name, not below it.
4. **No visible drop zone** — there is no visual affordance (border, background, placeholder text) showing WHERE to drop a token.
5. **Excessive whitespace between rows** — default Qt spacing creates large empty gaps; rows should be compact.

## Proposed Behavior

1. Source column tokens render as clearly visible styled buttons (explicit background color + text color).
2. Each canonical row uses a horizontal layout: `[Canonical Name label] | [Assignment Slot]`.
3. The Assignment Slot is a styled `QFrame` with a dashed border when empty (showing "(drop here)") and a solid border with a draggable source-name button when assigned.
4. Row spacing is compact (minimal margins between rows).
5. All bidirectional drag behaviors from #64 preserved: pool→row assign, assigned→row re-assign, assigned→pool unassign.

## Acceptance Criteria (early draft)

- [x] AC-1: Source column tokens render with visible text (explicit button styling).
- [x] AC-2: Each canonical row is horizontal: canonical name left, assignment slot right.
- [x] AC-3: Assignment slot shows dashed "(drop here)" when empty; solid-border draggable source button when assigned.
- [x] AC-4: Row spacing is compact (no large gaps between canonical rows).
- [x] AC-5: All bidirectional drag behaviors from #64 continue to function.

## Constraints & Risks

- `_columns_tab_drag.py` is at 499 lines; the new `ColumnAssignmentSlot` MUST be in a separate file `_column_assignment_slot.py`.
- `CANONICAL_ORIGIN_MIME` constant moves to `_column_assignment_slot.py` and is re-imported in `_columns_tab_drag.py`.
- Drag/drop methods currently on `ColumnDropRow` (mouseMoveEvent, dragEnterEvent, dropEvent) move to `ColumnAssignmentSlot`.

## Test Conditions to Consider

- [ ] ColumnAssignmentSlot renders dashed border + placeholder when unassigned
- [ ] ColumnAssignmentSlot renders assigned button style and text when assigned
- [ ] ColumnAssignmentSlot.mouseMoveEvent starts drag with both MIME keys when assigned
- [ ] ColumnAssignmentSlot.dropEvent calls on_drop callback
- [ ] ColumnsTabWidget row layout is horizontal (label left, slot right)

## Next Step

- [ ] Promote to GitHub issue (bug template)
- [ ] Create `docs/features/active/` folder from the template