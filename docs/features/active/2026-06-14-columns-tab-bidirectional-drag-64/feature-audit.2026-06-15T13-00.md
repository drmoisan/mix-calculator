# Feature Audit: Columns Tab Bidirectional Drag (#64)

**Audit Date:** 2026-06-15
**Feature Folder:** `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/`
**Base Branch:** `main`
**Head Branch:** `fix/columns-tab-bidirectional-drag` (`50919cd`)
**Work Mode:** `minor-audit`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `main` (commit `b53cf3ef2a57f9853215b0638842e014279fa14b`)
- **Head branch/commit:** `fix/columns-tab-bidirectional-drag` (commit `50919cd4275e3658c1939d30e52c1f974fece84c`)
- **Merge base:** `b53cf3ef2a57f9853215b0638842e014279fa14b`
- **Evidence sources:**
  - Primary: `artifacts/pr_context.summary.txt`
  - Secondary baseline diff: `artifacts/pr_context.appendix.txt`
  - Feature evidence: `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/`
  - Additional evidence: `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/evidence/qa-gates/ac-verification.md`
- **Feature folder used:** `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/`
- **Requirements source:** `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/issue.md`
- **Work mode resolution note:** `issue.md` contains `- Work Mode: minor-audit`. Acceptance criteria sourced exclusively from the `## Acceptance Criteria` section of `issue.md`. No `spec.md` or `user-story.md` consulted.
- **Scope note:** Full branch diff against merge base `b53cf3ef`. Changed production files: `src/gui/widgets/_columns_tab_drag.py` (+96/-38), `src/gui/widgets/_schema_builder_drag_tabs.py` (+1/-0). Changed test file: `tests/gui/test_columns_tab_widgets.py` (+182/-0).

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/issue.md` — only source (minor-audit work mode)

### Acceptance criteria

The following criteria are taken verbatim from the `## Acceptance Criteria` section of `issue.md`:

1. AC-1: Dragging an assigned source column onto a different canonical row re-assigns it (old row shows unassigned, new row shows the source).
2. AC-2: Dragging an assigned source column onto the pool area unassigns it (the row shows "(unassigned)", the token returns to the pool).
3. AC-3: Pool tokens (unassigned columns) continue to be draggable onto canonical rows as before (no regression).
4. AC-4: Tests cover the new drag-from-assignment and pool-drop paths at the widget seam level.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | AC-1: Dragging an assigned source column onto a different canonical row re-assigns it (old row shows unassigned, new row shows the source). | PASS | `ColumnDropRow.mouseMoveEvent` (lines 254-274 of `_columns_tab_drag.py`) sets MIME text to `_current_source` and carries `CANONICAL_ORIGIN_MIME`. The target row's pre-existing `dropEvent` reads `text()` and calls `_on_drop(source, canonical)`. `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin` verifies MIME carries correct keys. `evidence/qa-gates/ac-verification.md` §AC-1. | `poetry run pytest tests/gui/test_columns_tab_widgets.py::test_assigned_row_mousemove_starts_drag_carrying_source_and_origin` | Re-assign path reuses pre-existing `ColumnDropRow.dropEvent` unchanged; no seam regression risk. |
| 2 | AC-2: Dragging an assigned source column onto the pool area unassigns it (the row shows "(unassigned)", the token returns to the pool). | PASS | `ColumnsTabWidget.dragEnterEvent` (lines 352-361) accepts only drags carrying both MIME keys. `ColumnsTabWidget.dropEvent` (lines 363-374) reads `CANONICAL_ORIGIN_MIME` and calls `clear_row(canonical_origin)`. `DragTabBinder.__init__` wires `columns_widget.clear_row = self._columns_presenter.clear_row` (line 93 of `_schema_builder_drag_tabs.py`). `test_pool_dropEvent_with_canonical_origin_calls_clear_row` verifies `clear_row` called with decoded canonical name. `evidence/qa-gates/ac-verification.md` §AC-2. | `poetry run pytest tests/gui/test_columns_tab_widgets.py::test_pool_dropEvent_with_canonical_origin_calls_clear_row` | Wiring confirmed in `_schema_builder_drag_tabs.py` line 93. |
| 3 | AC-3: Pool tokens (unassigned columns) continue to be draggable onto canonical rows as before (no regression). | PASS | Pytest run post-change: 1041 passed, 0 failed. All 8 pre-existing tests in `test_columns_tab_widgets.py` pass including `test_drop_gesture_invokes_assign_column_once`, `test_source_token_starts_drag_on_left_button_move`, `test_pool_renders_one_token_per_source_column`. `ColumnsTabWidget.dragEnterEvent` explicitly rejects plain pool-token drags (no `CANONICAL_ORIGIN_MIME`); `test_pool_dragEnterEvent_rejects_missing_canonical_origin` verifies the rejection. `evidence/qa-gates/qa-pytest.md`, `evidence/qa-gates/ac-verification.md` §AC-3. | `poetry run pytest --cov --cov-branch --cov-report=term-missing` | No pre-existing test modified or removed. |
| 4 | AC-4: Tests cover the new drag-from-assignment and pool-drop paths at the widget seam level. | PASS | Four new tests added to `tests/gui/test_columns_tab_widgets.py`: `test_assigned_row_mousemove_starts_drag_carrying_source_and_origin`, `test_unassigned_row_mousemove_does_not_start_drag`, `test_pool_dropEvent_with_canonical_origin_calls_clear_row`, `test_pool_dragEnterEvent_rejects_missing_canonical_origin`. All 4 PASSED in post-change Pytest run. Tests cover: drag-source positive path (AC-1), drag-source guard-clause negative, pool-drop positive path (AC-2), pool-drag-enter rejection. `evidence/qa-gates/qa-pytest.md`, `evidence/qa-gates/ac-verification.md` §AC-4. | `poetry run pytest tests/gui/test_columns_tab_widgets.py` | Test coverage of `_columns_tab_drag.py`: 94% line post-change. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 4 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Monitor `_columns_tab_drag.py` line count. At 499 lines it has one line of headroom before the 500-line cap; a future addition will require extraction.

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules, all 4 criteria evaluated as PASS are checked off in `issue.md`. The checkboxes in `issue.md` were already marked `[x]` by the executor prior to this review, consistent with the check-off protocol. This audit confirms that evidence supports all four checkboxes.

### AC Status Summary

- Source: `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/issue.md`
- Total AC items: 4
- Checked off (delivered): 4
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `docs/features/active/2026-06-14-columns-tab-bidirectional-drag-64/issue.md` | 4 | 4 | 0 | Checkbox-backed; all `[x]` verified by this audit |

All four AC items in `issue.md` were marked `[x]` by the executor (confirmed in `issue.md` read). This audit verifies the evidence supports each check-off.
