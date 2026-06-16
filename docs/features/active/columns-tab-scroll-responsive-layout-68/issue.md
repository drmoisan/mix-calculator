# columns-tab-scroll-responsive-layout-68

- Work Mode: minor-audit
- Issue: #68

## Problem / Why

`ColumnsTabWidget` uses a plain vertical layout with no `QScrollArea` and no `QSplitter`,
causing two visible defects:

1. **Derived columns hidden.** With 25+ regular canonical rows, derived-column rows (added
   via Decision 7) fall below the visible area and are inaccessible — there is no scrollbar.
   The user reports "neither of those two columns appear" after adding them on the Derived tab.

2. **Horizontal space wasted.** On a wide screen the source pool and canonical rows stack
   vertically, ignoring most of the horizontal extent. The user expects the source pool
   (unassigned tokens) on the right and the canonical assignments on the left when the window
   is wide.

## Implementation Intent

Replace the plain `QVBoxLayout` in `ColumnsTabWidget.__init__` with a `QSplitter` whose
two panels are a `QScrollArea`-wrapped canonical rows section (left/bottom) and the source
token pool (right/top). Implement `resizeEvent` to switch orientation and panel order at a
configurable width threshold. Keep `_columns_tab_drag.py` under 500 lines.

## Acceptance Criteria

- [x] AC-1: Canonical rows are wrapped in a `QScrollArea`; rows beyond the visible height
  are reachable by scrolling.
- [x] AC-2: Derived column rows (added via Decision 7) are visible when the user scrolls
  to the end of the canonical rows list (i.e., they appear after the regular column rows).
- [x] AC-3: Wide layout (>= threshold): left panel shows canonical assignments (scrollable),
  right panel shows source pool.
- [x] AC-4: Narrow layout (< threshold): top panel shows source pool, bottom panel shows
  scrollable canonical assignments.
- [x] AC-5: All existing drag-and-drop behaviors (assign, re-assign, unassign from row,
  unassign to pool) continue to function after the layout refactor.

## Dependencies / Risks

- `_columns_tab_drag.py` is currently 466 lines. Layout additions must keep it under 500
  lines; extract to a companion file if needed.
- Panel reorder on orientation switch requires `setParent(None)` + `addWidget` in the correct
  order; `setOrientation` alone does not swap widget positions.
- `QScrollArea` requires `setWidgetResizable(True)` to track panel width; without it,
  horizontal overflow breaks the layout.

## Verification Steps

1. Run the schema builder with a schema that has 2+ derived columns; switch to the Columns
   tab and scroll to confirm derived rows appear at the bottom of the canonical list.
2. Widen the window past the threshold; confirm left=assignments, right=pool.
3. Narrow the window below the threshold; confirm top=pool, bottom=assignments.
4. Confirm drag-assign, drag-re-assign, and drag-to-pool all function in both orientations.

## Evidence Checklist

- [x] baseline
- [x] targeted verification
- [x] end-state
