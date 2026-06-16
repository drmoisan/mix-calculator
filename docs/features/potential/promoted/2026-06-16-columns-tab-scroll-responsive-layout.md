# columns-tab-scroll-responsive-layout (Issue #68)

- Date captured: 2026-06-16
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/columns-tab-scroll-responsive-layout/ (Issue #68)

- Issue: #68
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/68
- Last Updated: 2026-06-16
## Problem / Why

`ColumnsTabWidget` uses a plain vertical layout with no `QScrollArea` and no `QSplitter`.
Two resulting defects are visible in the schema editor:

1. **Derived columns are hidden.** Derived columns are rendered as canonical rows after
   the regular columns (Decision 7). With 25+ regular columns, derived rows fall below
   the visible area and are never seen because there is no scrollbar.

2. **Wasted horizontal space.** On a wide screen the canonical-row list and the source
   token pool stack vertically, leaving most of the horizontal extent unused. The user
   expects the pool (unassigned tokens) on the right and the assignments (canonical rows)
   on the left when space allows.

## Proposed Behavior

- **Wide mode (>= threshold):** `QSplitter` in horizontal orientation — left panel holds a
  `QScrollArea`-wrapped canonical rows section; right panel holds the source token pool.
- **Narrow mode (< threshold):** `QSplitter` switches to vertical orientation and reverses
  panel order — pool on top, scrollable canonical rows on bottom.
- `ColumnsTabWidget.resizeEvent` detects width changes and reorders panels when crossing
  the threshold.

## Acceptance Criteria (early draft)

- [ ] AC-1: Canonical rows are wrapped in a `QScrollArea`; rows beyond the visible height
  are reachable by scrolling.
- [ ] AC-2: Derived column rows (added via Decision 7) are visible when the user scrolls
  to the end of the canonical rows list.
- [ ] AC-3: Wide layout (>= threshold): left panel shows canonical assignments, right panel
  shows source pool.
- [ ] AC-4: Narrow layout (< threshold): top panel shows source pool, bottom panel shows
  scrollable canonical assignments.
- [ ] AC-5: All existing drag-and-drop behaviors (assign, re-assign, unassign from row,
  unassign to pool) continue to function after the layout refactor.

## Constraints & Risks

- `_columns_tab_drag.py` is at 466 lines. The layout additions must keep it under 500 lines;
  extract to a companion file if needed.
- `QScrollArea` requires `setWidgetResizable(True)` to follow the panel width; without it,
  horizontal overflow breaks the layout.
- Panel reorder on orientation switch requires `setParent(None)` + `addWidget` in the correct
  order; `setOrientation` alone does not change widget order.

## Test Conditions to Consider

- [ ] Pool tokens accessible and draggable after layout refactor
- [ ] Canonical rows show correct assignment after `set_assignment`
- [ ] `row_canonicals()` test seam includes derived column rows
- [ ] Splitter orientation changes at threshold (unit-testable via `resizeEvent` stub)

## Next Step

- [x] Promote to GitHub issue (bug template)
- [ ] Create `docs/features/active/` folder from the template