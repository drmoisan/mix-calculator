# schema-builder-ux-overhaul (Issue #50)

- Date captured: 2026-06-04
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/schema-builder-ux-overhaul/ (Issue #50)

- Issue: #50
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/50
- Last Updated: 2026-06-04
- Work Mode: full-feature

## Problem / Why

The Mix Pipeline GUI schema selection and schema-builder experience has several
usability and correctness gaps. The current Schema Builder is a passive tabbed
dialog backed by plain-text and single-line editors (pipe-delimited column lines,
comma-separated key columns, `name|expression` derived lines). It does not provide
drag-and-drop column assignment, fuzzy pre-population from the opened workbook,
data-type compatibility feedback, a guided formula builder, or a caller-supplied
required/optional column contract. Schema auto-selection on the import surface is
also not wired into production (carried over as follow-up F2 from issue #48), the
Import button is not gated on schema choice, and there is no way to edit an
already-created schema in the UI.

## Proposed Behavior

Seven coupled improvements to the Mix Pipeline GUI:

1. **Import gating.** Before a schema is chosen for a source tab, the Import
   button is disabled (greyed out). It enables only once a schema is selected.

2. **Schema auto-selection.** When a source tab is activated, the best-matching
   schema is auto-selected from the registry. This finishes wiring the
   `SourceSelectionPresenter.on_schema_discovery` seam left unwired as #48
   follow-up F2.

3. **Edit existing schema.** An "Edit schema" affordance opens a created schema
   in the Schema Builder for modification and re-save.

4. **Columns tab redesign (intuitive, caller-driven).**
   - The Schema Builder receives the **required** and **optional** column
     definitions from the caller as a parameter.
   - The Columns tab shows **draggable buttons** for each column name found in
     the selected sheet/tab of the opened spreadsheet.
   - Below, **rows of required and optional columns** show canonical name,
     description, and expected data type.
   - Rows are **pre-populated via fuzzy matching** against the spreadsheet
     columns. A matched source column is **removed from the draggable pool** and
     cannot match a second row.
   - For each matched column (auto or manual), a **data-type check** runs: a
     green checkmark when the source type is identical or safely coercible to the
     expected type; a red X with a **concrete example value** that cannot be
     converted otherwise.

5. **Key tab redesign (drag-and-drop + concatenation).**
   - Same draggable column-name buttons as Columns.
   - Supports **concatenation with literal text**: a draggable **Generic Text**
     token that is the only token placeable multiple times, each with its own
     value.
   - Each key part is placed in a row (ordered composition).
   - The caller may supply a **default key pattern** that is parsed and rendered
     onto the Key tab.

6. **Dedup tab defaults.**
   - Default mode is **aggregate**.
   - Default discriminator column is the **Key**.
   - All other named columns are offered in a **dropdown** (no free-text entry;
     a non-existent column cannot be a discriminator).

7. **Derived tab (before Columns; PowerQuery-style formula builder).**
   - Tab order places **Derived before Columns**.
   - A button opens a **dialog to create a derived-column row**.
   - The dialog offers all named columns plus any columns derived in rows above
     it.
   - The formula builder behaves like PowerQuery's add-column experience.
   - Any derived column then appears as a selectable column on the Columns tab.

## Acceptance Criteria

Design decisions resolved 2026-06-05; authoritative AC live in `spec.md`. Summary:

- [ ] Import button disabled until a schema is selected; re-disables on placeholder.
- [ ] Activating a source tab auto-selects the best-matching schema; placeholder
      shown when none matches.
- [ ] An Edit-schema action loads an existing schema into the builder and re-saves.
- [ ] A "New from template" action seeds a new schema from the closest existing one.
- [ ] Schema Builder accepts required/optional specs, default key pattern, and a
      masked preview slice from the per-tab caller.
- [ ] Columns tab renders draggable source-column buttons from the selected sheet.
- [ ] Required/optional rows pre-populate via fuzzy matching; a matched source
      column is consumed (removed from the pool, cannot re-match).
- [ ] Matched source->canonical mapping persists as aliases; reload re-matches;
      activation-time matching runs first against persisted alias columns; partial
      match surfaces new-from-template.
- [ ] Matched columns show a green check (coercible) or red X with a failing
      example value (not coercible).
- [ ] Key tab supports drag-and-drop column parts plus a repeatable Generic Text
      token via a structured key-part model; default key pattern parsed onto tab.
- [ ] Dedup defaults to aggregate mode with the Key as discriminator; other
      columns selectable via dropdown only.
- [ ] Derived tab precedes Columns; a dialog creates derived rows referencing
      named and previously-derived columns; derived columns appear on Columns.
- [ ] `ColumnSpec.expected_dtype` added; schema version bumped; forward migration
      in `schema_from_json`; bundled defaults migrated to aggregate mode.
- [ ] No real workbook values or proprietary column names committed (masking scan).

## Constraints & Risks

- PySide6 GUI; T3 adapter/UI tier. 500-line per-file cap applies; the existing
  builder is already split (`schema_builder_dialog.py` + `_schema_builder_tabs.py`)
  and a drag-and-drop redesign will need careful module decomposition.
- Type-coercion checks and fuzzy matching must keep pure logic separated from Qt
  widgets (presenter/service vs. passive view) for testability.
- The formula engine is `asteval` (already approved). The PowerQuery-style builder
  must reuse the existing derived-column formula evaluation rather than introduce
  a second engine.
- Drag-and-drop interaction is difficult to unit-test; behavior must be driven
  through presenter seams with the view kept passive.
- Caller contract changes (required/optional specs, default key pattern) ripple to
  every call site that opens the Schema Builder.
- Confidential workbook figures must never be committed in tests or fixtures.

## Test Conditions to Consider

- [ ] Import-gate enable/disable on schema selection and tab switch.
- [ ] Auto-select match, no-match placeholder, and ambiguous-match behavior.
- [ ] Fuzzy pre-population including consumed-column exclusion and re-match guard.
- [ ] Type-coercion check: identical, coercible, and non-coercible (with example).
- [ ] Key composition: column parts, repeated Generic Text tokens, default-pattern
      parse/round-trip.
- [ ] Dedup defaults and dropdown-only discriminator constraint.
- [ ] Derived dialog: reference named + prior-derived columns; surfacing on Columns;
      formula validation parity with the existing engine.
- [ ] Edit-existing-schema load/modify/save round-trip.

## Next Step

- [ ] Promote to GitHub issue (feature request template)
- [ ] Create `docs/features/active/schema-builder-ux-overhaul/` folder from the template