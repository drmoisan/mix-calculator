# Feature Audit: Columns Tab UX Redesign (#66)

**Audit Date:** 2026-06-15
**Feature Folder:** `docs/features/active/2026-06-15-columns-tab-ux-layout-66/`
**Base Branch:** `fix/columns-tab-bidirectional-drag` (merge base `3152ee285818262f328518cdc9ad8611a6a1b7ca`)
**Head Branch:** `fix/columns-tab-ux-redesign` (commit `608a0aaf55d145d394a60df8dd34ffe15c5c476b`)
**Work Mode:** `minor-audit`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `fix/columns-tab-bidirectional-drag` (commit `3152ee285818262f328518cdc9ad8611a6a1b7ca`)
- **Head branch/commit:** `fix/columns-tab-ux-redesign` (commit `608a0aaf55d145d394a60df8dd34ffe15c5c476b`)
- **Merge base:** `3152ee285818262f328518cdc9ad8611a6a1b7ca`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt` and `artifacts/pr_context.appendix.txt`
  - Secondary baseline diff: `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/baseline/pytest-baseline.md`
  - Feature evidence: `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/`
  - AC verification: `docs/features/active/2026-06-15-columns-tab-ux-layout-66/evidence/qa-gates/ac-verification.md`
- **Feature folder used:** `docs/features/active/2026-06-15-columns-tab-ux-layout-66/`
- **Requirements source:** `docs/features/active/2026-06-15-columns-tab-ux-layout-66/issue.md` (minor-audit mode; `## Acceptance Criteria` section only)
- **Work mode resolution note:** Work mode `minor-audit` is read directly from the `- Work Mode: minor-audit` marker in `issue.md`. AC source is the explicit `## Acceptance Criteria` section in `issue.md`. `spec.md` and `user-story.md` are not consulted.
- **Scope note:** The audit scope is the full branch diff (`3152ee2..608a0aa`) against the resolved base branch. Only changed Python files are in scope; no TypeScript, PowerShell, C#, or Bash files are changed on this branch.

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-06-15-columns-tab-ux-layout-66/issue.md` — only source (minor-audit mode)

### Acceptance criteria

1. AC-1: Source column tokens render with visible text (explicit button styling).
2. AC-2: Each canonical row is horizontal: canonical name left, assignment slot right.
3. AC-3: Assignment slot shows dashed "(drop here)" when empty; solid-border draggable source button when assigned.
4. AC-4: Row spacing is compact (no large gaps between canonical rows).
5. AC-5: All bidirectional drag behaviors from #64 continue to function.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Source column tokens render with visible text (explicit button styling) | PASS | `SourceColumnToken.__init__` calls `self.setStyleSheet("background: #5c88d4; color: white; border-radius: 3px; padding: 4px 8px; font-weight: bold;")` at `_columns_tab_drag.py` lines 83-86. Test `test_source_token_has_visible_styling` asserts `token.styleSheet() != ""` and passed in the post-change run (1044 passed). AC verification artifact confirms PASS with grep and test evidence. | `grep -n "setStyleSheet" src/gui/widgets/_columns_tab_drag.py` | The base branch `SourceColumnToken` had no explicit stylesheet, causing invisible text on Windows. The fix adds a styled QPushButton with explicit background and white text color. |
| 2 | Each canonical row is horizontal: canonical name left, assignment slot right | PASS | `ColumnDropRow.__init__` in `_columns_tab_drag.py` uses `QHBoxLayout(self)` (line 160) with `addWidget(self._label, 2)`, `addWidget(self._slot, 1)`, `addWidget(self._indicator, 0)` placing the label on the left, the assignment slot in the middle, and the dtype indicator on the right. AC verification artifact confirms PASS with grep evidence (import at line 30, `QHBoxLayout(self)` at line 160). | `grep -n "QHBoxLayout" src/gui/widgets/_columns_tab_drag.py` | The base branch used `QVBoxLayout`, stacking canonical label, assignment, and dtype indicator vertically. |
| 3 | Assignment slot shows dashed "(drop here)" when empty; solid-border draggable source button when assigned | PASS | `_column_assignment_slot.py` defines `_UNASSIGNED_STYLE` containing `"border: 2px dashed #aaa"` and `_ASSIGNED_STYLE` containing `"border: 2px solid #4a75c0"`. `set_assignment` toggles between them. Test `test_assignment_slot_unassigned_style_has_dashed_border` asserts `"dashed" in slot.styleSheet()` (PASS). Test `test_assignment_slot_assigned_shows_source_button` asserts `slot.assignment_text() == "col_a"` after `set_assignment("col_a")` (PASS). The slot's `_placeholder = QLabel("(drop here)")` is visible when unassigned; `_button = QPushButton(source)` is visible when assigned. Both tests passed in the post-change run. | `poetry run pytest tests/gui/test_columns_tab_widgets.py::test_assignment_slot_unassigned_style_has_dashed_border tests/gui/test_columns_tab_widgets.py::test_assignment_slot_assigned_shows_source_button -v` | `mouseMoveEvent` in `ColumnAssignmentSlot` starts a drag from the assigned slot, satisfying the "draggable source button" part of AC-3. |
| 4 | Row spacing is compact (no large gaps between canonical rows) | PASS | `ColumnsTabWidget.__init__` sets `self._rows_box.setSpacing(2)` (line 291) and `self._rows_box.setContentsMargins(0, 0, 0, 0)` (line 292). `ColumnDropRow.__init__` sets `row.setContentsMargins(4, 2, 4, 2)` (line 161) and `row.setSpacing(8)` (line 162). AC verification artifact confirms PASS with grep evidence. | `grep -n "setSpacing\|setContentsMargins" src/gui/widgets/_columns_tab_drag.py` | The base branch used default Qt spacing, producing large empty gaps between rows. The fix applies explicit compact spacing to both the rows container and individual rows. |
| 5 | All bidirectional drag behaviors from #64 continue to function | PASS | All six tests from #64 pass after the refactor. Updated tests correctly target `row.slot.dropEvent`, `row.slot.dragEnterEvent`, and `row.slot.mouseMoveEvent` (drag/drop methods moved from `ColumnDropRow` to `ColumnAssignmentSlot`). Tests: `test_drop_gesture_invokes_assign_column_once`, `test_drop_row_drag_enter_accepts_text_payload`, `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin`, `test_unassigned_row_mousemove_does_not_start_drag`, `test_pool_dropEvent_with_canonical_origin_calls_clear_row`, `test_pool_dragEnterEvent_rejects_missing_canonical_origin` — all PASS per post-change pytest run. | `poetry run pytest tests/gui/test_columns_tab_widgets.py -v` | The MIME key `CANONICAL_ORIGIN_MIME` is re-exported from `_columns_tab_drag.py` via `__all__`, so existing callers importing from the old module are not broken. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 5 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None. All 5 AC items are satisfied with direct test and code evidence.

**Recommended follow-up verification steps:**

1. Run CI on the branch head and confirm green status before merging. (CI status was not available at time of this review per `artifacts/pr_context.summary.txt`.)
2. Resolve the procedural finding regarding unauthorized `# type: ignore[override]` suppressions in `_column_assignment_slot.py` (documented in `policy-audit.2026-06-15T23-00.md` Section 8). This is not an AC gap but a policy compliance item.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules, all 5 AC items are evaluated as PASS and are eligible for check-off. Inspecting `issue.md`, all 5 items are already marked `[x]` by the executor during plan execution. No further check-off action is needed by this reviewer.

### AC Status Summary

- Source: `docs/features/active/2026-06-15-columns-tab-ux-layout-66/issue.md`
- Total AC items: 5
- Checked off (delivered): 5
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-06-15-columns-tab-ux-layout-66/issue.md` | 5 | 5 | 0 | Checkbox-backed; all items already marked `[x]` by executor |
