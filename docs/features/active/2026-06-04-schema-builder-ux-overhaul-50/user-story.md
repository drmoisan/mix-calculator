# `schema-builder-ux-overhaul` — User Story

- Issue: #50
- Owner: drmoisan
- Status: Draft
- Last Updated: 2026-06-04T15-52

## Story Statement

- As a ..., I want ..., so that ...
- As a ..., I want ..., so that ...

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


## Personas & Scenarios

- Persona: ...
  - who the user is
  - what they care about
  - their constraints
  - their goals and frustrations
  - their context and motivations
- Scenario: ...
  - A concrete, step-by-step narrative that describes how a user accomplishes a goal in a real-world context using the system.
  - who is acting?
  - what triggered the action?
  - what steps do they take?
  - what obstacles or decisions occur?
  - what outcome do they expect?


## Acceptance Criteria

- [x] Import button disabled until a schema is selected for the active source tab.
- [x] Activating a source tab auto-selects the best-matching schema; placeholder
- [x] shown when none matches.
- [x] An Edit-schema action loads an existing schema into the builder and re-saves.
- [x] Schema Builder accepts required/optional column specs from the caller.
- [x] Columns tab renders draggable source-column buttons from the selected sheet.
- [x] Required/optional rows pre-populate via fuzzy matching; a matched source
- [x] column is consumed (removed from the pool, cannot re-match).
- [x] Matched columns show a green check (coercible) or red X with a failing
- [x] example value (not coercible).
- [x] Key tab supports drag-and-drop column parts plus a repeatable Generic Text
- [x] token; a caller-supplied default key pattern is parsed onto the tab.
- [x] Dedup defaults to aggregate mode with the Key as discriminator; other
- [x] columns selectable via dropdown only.
- [x] Derived tab precedes Columns; a dialog creates derived rows referencing
- [x] named and previously-derived columns; derived columns appear on Columns.


## Non-Goals

Call out what is explicitly excluded from this feature.
