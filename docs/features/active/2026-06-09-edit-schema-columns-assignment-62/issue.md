# edit-schema-columns-assignment (Issue #62)

- Date captured: 2026-06-09
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/edit-schema-columns-assignment/ (Issue #62)
- Type: bug

- Issue: #62
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/62
- Last Updated: 2026-06-10
- Work Mode: minor-audit

## Problem / Why

The per-tab "Edit Schema" button (delivered in issue #60) opens the schema
builder seeded from the tab's currently-selected schema via
`SchemaBuilderPresenter.load_existing`. When the builder opens in this edit mode,
the **Columns** tab renders every canonical column as unassigned even though the
loaded schema already records its source-column assignments. The displayed state
contradicts the persisted schema: the schema does carry the assignments, but the
Columns tab does not show them.

## Root Cause (verified by code inspection)

The Columns-tab assignment shown to the user is driven by
`SchemaBuilderState.consumed_columns` (a canonical-name -> source-column map),
read by `ColumnsTabPresenter._render_assignments_and_dtypes` via
`view.set_assignment`. That map is populated only by:

1. `ColumnsTabPresenter.prepopulate()` — fuzzy-matching each canonical row against
   the live source-column pool (`state.source_columns`, derived from the masked
   `preview_slice`), or
2. a manual drag-drop (`assign_column`).

The Edit path does not exercise either:

- `SchemaBuilderPresenter.load_existing(name)` calls `_state_from_schema`, which
  loads each column row **with its persisted aliases** (the saved
  source->canonical assignments), then `_render_state` -> `view.set_columns`.
- `DragTabBinder.set_columns` resets `consumed_columns = {}`, rebuilds the source
  pool from the (absent) `preview_slice` — so the pool is empty — and runs
  `prepopulate()`, which has nothing to match against.

Net effect: the persisted aliases that record the prior assignments are loaded
into the column rows but are never reflected into `consumed_columns`, so
`set_assignment(canonical, None)` is pushed for every row and the Columns tab
shows all canonical columns as unassigned.

The persisted assignment is recorded as the column's alias (see
`ColumnsTabPresenter._bind` -> `_add_alias`). The fix must seed the rendered
assignment from those persisted aliases when a schema is loaded for editing,
rather than relying solely on the live source pool (which the Edit-from-button
path does not provide).

## Proposed Behavior

When the schema builder is opened in edit mode (an existing schema loaded via
`load_existing`), the Columns tab must show, for each canonical column, the
source-column assignment recorded in the loaded schema (its persisted alias).
Columns with no persisted alias remain unassigned. The blank "Build new schema"
and the seeded per-tab "Build/Edit schema" (with a live preview slice) paths must
keep their current fuzzy-prepopulation behavior unchanged.

## Acceptance Criteria

These are the authoritative acceptance criteria for this minor-audit bug.

- [x] AC-1: After `SchemaBuilderPresenter.load_existing(name)`, each canonical
      column that carries a persisted alias renders as assigned to that alias on
      the Columns tab — `view.set_assignment(canonical, <alias>)` is called with
      the persisted source column, not `None`.
- [x] AC-2: A canonical column loaded with no persisted alias renders unassigned
      (`set_assignment(canonical, None)`).
- [x] AC-3: The existing blank "Build new schema" path and the seeded per-tab
      "Build/Edit schema" path that supplies a live `preview_slice` keep their
      current fuzzy-prepopulation behavior with no regression (a live source pool
      still drives matching; persisted-alias seeding does not override or
      duplicate a live match, and the one-source-per-row consumption invariant
      holds).
- [x] AC-4: An edit-then-save round-trip through the builder preserves the
      persisted assignments (the saved schema's column aliases are retained).

## Constraints & Risks

- Pure GUI presenter/state logic; no Qt import added, no I/O. No workbook access
  required (the bug and its tests are independent of any .xlsx).
- File-size cap (500 lines) applies to changed production and test files.
- Must not regress the source-pool consumption invariant (one source per row).

## Test Conditions to Consider

- [ ] Unit: `ColumnsTabPresenter` / `DragTabBinder` render persisted aliases as
      assignments when no source pool is present.
- [ ] Unit: live-preview-slice prepopulation path unchanged.
- [ ] Unit: `SchemaBuilderPresenter.load_existing` end-to-end pushes assignments
      to a fake view.
- [ ] Edge: column with multiple aliases; column with no alias; derived columns.

## Next Step

- [x] Promote to GitHub issue (bug template, minor-audit) — Issue #62.
- [x] Create active feature folder from the template.
- [ ] Minimal plan -> implementation -> QC -> minor-audit review.