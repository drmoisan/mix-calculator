# Feature Audit: Columns Tab Scroll + Responsive Layout (#68)

**Audit Date:** 2026-06-16
**Feature Folder:** `docs/features/active/columns-tab-scroll-responsive-layout-68/`
**Base Branch:** `fix/columns-tab-bidirectional-drag`
**Head Branch:** `fix/columns-tab-scroll-layout`
**Work Mode:** `minor-audit`
**Audit Type:** Initial acceptance review

---

## Scope and Baseline

- **Base branch:** `fix/columns-tab-bidirectional-drag`
- **Head branch/commit:** `fix/columns-tab-scroll-layout`
- **Merge base:** resolved from branch comparison (see git diff output)
- **Evidence sources:**
  - Primary: `docs/features/active/columns-tab-scroll-responsive-layout-68/evidence/qa-gates/ac-verification.md`
  - Secondary baseline diff: `docs/features/active/columns-tab-scroll-responsive-layout-68/evidence/qa-gates/coverage-delta.md`
  - Feature evidence: `docs/features/active/columns-tab-scroll-responsive-layout-68/evidence/`
  - Additional evidence: direct inspection of `src/gui/widgets/_columns_tab_drag.py`, `src/gui/widgets/_columns_tab_layout.py`, `tests/gui/test_columns_tab_layout.py`, `tests/gui/test_columns_tab_widgets.py`
- **Feature folder used:** `docs/features/active/columns-tab-scroll-responsive-layout-68/`
- **Requirements source:** `docs/features/active/columns-tab-scroll-responsive-layout-68/issue.md` — `minor-audit` work mode; `## Acceptance Criteria` section is the sole authoritative AC source.
- **Work mode resolution note:** `issue.md` line 3 contains `- Work Mode: minor-audit`. Per the minor-audit protocol, only the `## Acceptance Criteria` section in `issue.md` is used as the AC source.
- **Scope note:** The branch diff was confirmed from `git diff fix/columns-tab-bidirectional-drag...fix/columns-tab-scroll-layout`. Four files changed in the source/test layer; 14 files in the feature folder's evidence tree also changed (expected for this workflow).

---

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/columns-tab-scroll-responsive-layout-68/issue.md` — only source (minor-audit work mode)

### Acceptance criteria

1. AC-1: Canonical rows are wrapped in a `QScrollArea`; rows beyond the visible height are reachable by scrolling.
2. AC-2: Derived column rows (added via Decision 7) are visible when the user scrolls to the end of the canonical rows list (i.e., they appear after the regular column rows).
3. AC-3: Wide layout (>= threshold): left panel shows canonical assignments (scrollable), right panel shows source pool.
4. AC-4: Narrow layout (< threshold): top panel shows source pool, bottom panel shows scrollable canonical assignments.
5. AC-5: All existing drag-and-drop behaviors (assign, re-assign, unassign from row, unassign to pool) continue to function after the layout refactor.

---

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|---|---|---|---|---|
| 1 | Canonical rows wrapped in `QScrollArea`; scrollable | PASS | `test_columns_tab_scroll_area_wraps_rows_panel` asserts `len(scroll_areas) >= 1`, `scroll.widgetResizable() is True`, and all `ColumnDropRow` children are descendants of the scroll area's inner widget. `_columns_tab_layout.py` lines 67–70 confirm `setWidgetResizable(True)`. Pytest exit code 0. | `poetry run pytest tests/gui/test_columns_tab_layout.py::test_columns_tab_scroll_area_wraps_rows_panel` | The scroll area is created in `build_columns_panels` with `setWidgetResizable(True)`, satisfying both the wrapping and the resize requirements. |
| 2 | Derived column rows appear after regular rows in the scrollable list | PASS | `test_derived_row_appears_in_row_canonicals` asserts `widget.row_canonicals() == ["RegA", "RegB", "RegC", "DerX", "DerY"]` — derived rows at the end in insertion order. `set_rows` in `_columns_tab_drag.py` appends rows to `_rows_box` in iteration order; the rows inner widget is inside the scroll area, so derived rows are reachable by scrolling. Pytest exit code 0. | `poetry run pytest tests/gui/test_columns_tab_layout.py::test_derived_row_appears_in_row_canonicals` | AC-2 is satisfied structurally: `_rows_box` is inside `rows_inner` which is inside `rows_scroll`. Row insertion order determines scroll position. |
| 3 | Wide layout (>= threshold): left = canonical assignments (scrollable), right = source pool | PASS | `test_wide_layout_rows_left_pool_right` simulates a resize event with `width=500 >= threshold=400`, then asserts `widget.splitter.widget(0) is widget.rows_scroll` and `widget.splitter.widget(1) is widget.pool_panel`. `apply_splitter_orientation` in `_columns_tab_layout.py` lines 112–115 confirm the horizontal, rows-left, pool-right order. Pytest exit code 0. | `poetry run pytest tests/gui/test_columns_tab_layout.py::test_wide_layout_rows_left_pool_right` | The test uses `width_threshold=400` and a `QResizeEvent(QSize(500, 300), QSize(300, 300))` to trigger the wide branch. Splitter index 0 is left in horizontal mode. |
| 4 | Narrow layout (< threshold): top = source pool, bottom = scrollable canonical assignments | PASS | `test_narrow_layout_pool_top_rows_bottom` simulates a resize event with `width=300 < threshold=400`, then asserts `widget.splitter.widget(0) is widget.pool_panel` and `widget.splitter.widget(1) is widget.rows_scroll`. `apply_splitter_orientation` lines 116–119 confirm the vertical, pool-top, rows-bottom order. Pytest exit code 0. | `poetry run pytest tests/gui/test_columns_tab_layout.py::test_narrow_layout_pool_top_rows_bottom` | The test exercises the narrow branch explicitly. Splitter index 0 is top in vertical mode. |
| 5 | All existing drag-and-drop behaviors continue after the layout refactor | PASS | `test_layout_switch_preserves_drag_functionality` performs three orientation transitions (wide→narrow→wide) and asserts `widget.token_names() == ["c", "d"]` and `widget.row_canonicals() == ["D", "E"]` after all transitions. The existing drag tests in `test_columns_tab_widgets.py` (drop gesture invokes assign, pool dragEnterEvent rejects missing origin, pool dropEvent calls clear_row, mouse-move starts drag, etc.) all continue to pass — 1049 total, 0 failed. Pytest exit code 0. | `poetry run pytest tests/gui/test_columns_tab_widgets.py tests/gui/test_columns_tab_layout.py` | The drag-and-drop logic lives in `ColumnAssignmentSlot` and `ColumnsTabWidget.dragEnterEvent`/`dropEvent`, which are unmodified. The layout refactor wraps these in a splitter but does not intercept Qt event propagation. |

---

## Summary

**Overall Feature Readiness:** PASS

**Criteria summary:**
- **PASS:** 5 criteria
- **PARTIAL:** 0 criteria
- **UNVERIFIED:** 0 criteria
- **FAIL:** 0 criteria

**Top gaps preventing PASS:**

1. None.

**Recommended follow-up verification steps:**

1. Manual smoke test: open the schema builder with 2+ derived columns on the Columns tab; scroll to confirm derived rows appear at the bottom of the canonical list (AC-2 runtime verification).
2. Manual resize test: drag the application window to confirm orientation switches at approximately 700 pixels wide (AC-3/AC-4 runtime verification).

---

## Acceptance Criteria Check-off

Per the acceptance-criteria tracking rules, all five criteria evaluate as PASS and all five were already marked `[x]` in `issue.md` (confirmed by inspecting the file). No source-file checkbox changes are required by this audit.

### AC Status Summary

- Source: `docs/features/active/columns-tab-scroll-responsive-layout-68/issue.md`
- Total AC items: 5
- Checked off (delivered): 5
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|---|---|---|---|---|
| `docs/features/active/columns-tab-scroll-responsive-layout-68/issue.md` | 5 | 5 | 0 | Checkbox-backed; all items already marked `[x]` prior to this audit. |
