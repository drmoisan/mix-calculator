# schema-builder-ux-overhaul — Spec

- **Issue:** #50
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-05
- **Status:** Approved (design decisions resolved)
- **Version:** 1.0

## Overview

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

## Behavior

Seven coupled improvements to the Mix Pipeline GUI:

1. **Import gating.** Before a schema is chosen for a source tab, the Import
   button is disabled (greyed out). It enables only once a schema is selected and
   re-disables if the selection returns to the `<Choose Schema>` placeholder.

2. **Schema auto-selection.** When a source tab is activated, the best-matching
   schema is auto-selected from the registry. This finishes wiring the
   `SourceSelectionPresenter.on_schema_discovery` seam left unwired as #48
   follow-up F2.

3. **Edit existing schema.** An "Edit schema" affordance opens a created schema
   in the Schema Builder for modification and re-save. A companion
   **"New from template"** affordance seeds a new schema from the closest
   existing one (see Decision 6).

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
   - The matched source-column-to-canonical mapping is **persisted** on the
     schema (as `ColumnSpec` aliases), so a saved schema re-matches the same
     source on next activation.
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
   - Tab order places **Derived before Columns**:
     `Identity → Derived → Columns → Key → Dedup → Preview`.
   - A button opens a **dialog to create a derived-column row**.
   - The dialog offers all named columns plus any columns derived in rows above
     it.
   - The formula builder reuses the existing `asteval` `FormulaEvaluator`.
   - Any derived column then appears as a selectable column on the Columns tab.

## Resolved Design Decisions

These resolve the open questions in `artifacts/research/schema-builder-ux-overhaul-50.md`
section J. They are authoritative for planning and implementation.

1. **Dedup "aggregate" mode — no backward compatibility burden.** Add
   `"aggregate"` to `DEDUP_MODES`. Backward compatibility is **not** a constraint:
   migrate the bundled default schemas forward as part of this work. The migration
   to `aggregate` mode applies only to a schema that **has a discriminator** column:
   `default_le.schema.json` (discriminator `YTD/YTG`) migrates to `aggregate`. A
   schema **without a discriminator** correctly retains `mode: none` —
   `default_aop.schema.json` has no discriminator and so stays at `mode: none`
   (aggregate dedup is meaningless without a discriminator to collapse across).

2. **Key literal-text tokens — structured model.** Replace the flat
   `KeySpec.columns: tuple[str, ...]` with a structured ordered key-part model
   distinguishing **column-ref** parts from **literal-text** ("Generic Text")
   parts. No `__literal__:`-style string overloading.

3. **Migrate everything forward.** Bump `SchemaDefinition.version` and apply a
   forward-only migration in `schema_from_json`. No dual representation and no
   compatibility shim is retained. Migrate all in-repo schema JSON forward.

4. **Expected data type — new `ColumnSpec` field.** Add
   `expected_dtype: str | None` to `ColumnSpec` with the vocabulary
   `{string, integer, float, date, bool}`; `numeric=True` maps to `float`.
   Because `src/schema_model.py` is at 487/500 lines, split it first (for example
   `src/_schema_model_specs.py` for the spec dataclasses) before adding the field.

5. **Sample data for dtype check — masked preview slice.** Pass a slice of the
   already-read `preview_rows` (up to ~200) to the builder at open time; no new
   I/O inside the builder. **All sampled values and source column names that could
   land in any committed file, test fixture, or artifact must be masked.** No real
   workbook values or proprietary column names may be persisted to the repo
   (see Constraints & Risks).

6. **Persisted matching (configurable schema is the point).** The matched/consumed
   source-column-to-canonical mapping is **persisted** on the schema via
   `ColumnSpec` aliases, not recomputed as ephemeral UI state. Required columns
   do not change across schemas; the **matching columns** are what differ, which
   is why multiple schemas are persisted for the same canonical set. On source-tab
   activation, fuzzy matching runs **first against the persisted consumed/alias
   columns** of existing schemas to confirm whether a pre-existing schema is in
   fact a match. If many columns match but not all, this signals a possibly-new
   schema; a **"New from template"** action seeds a new schema from the closest
   existing one for the user to adjust and save under a new name.

7. **Caller of required/optional specs — per-tab button.** The per-tab
   "Build/Edit schema" button supplies required/optional specs, the default key
   pattern, and the masked preview slice (it knows the active source). The
   menu-action path opens a blank builder without caller specs. The spec
   documents both paths.

8. **Import gating start state — starts disabled.** The Import button starts
   disabled and enables on schema selection; it re-disables on return to the
   placeholder.

9. **`on_schema_discovery` trigger.** Wire to `_tab_combo.currentTextChanged`
   (fires on tab activation with a file already selected). Empty-header and
   reader-error guards already covered by existing tests are retained.

10. **Tab order.** `Identity → Derived → Columns → Key → Dedup → Preview`.

## Inputs / Outputs

- **Inputs:** required/optional `ColumnSpec` definitions, an optional default key
  pattern, and a masked preview slice (header row + up to ~200 masked sample
  rows), all supplied by the per-tab "Build/Edit schema" button. Existing schema
  JSON from the registry for edit / new-from-template flows.
- **Outputs:** `<name>.schema.json` written to the user registry dir (unchanged
  persistence target); the new key-part model, `expected_dtype` field, and
  `aggregate` dedup mode are serialized within it. Migrated bundled defaults under
  `src/schemas/`.
- **Config keys / defaults:** dedup default mode `aggregate`; default discriminator
  `Key`; tab order as in Decision 10.
- **Versioning:** `SchemaDefinition.version` bumped; forward-only migration in
  `schema_from_json`. No backward-compatible read path is retained.

## API / CLI Surface

No CLI changes. Affected programmatic surfaces:

- `open_schema_builder(...)` / `wire_build_schema_buttons(...)`
  (`src/gui/_schema_wiring.py`) gain required/optional specs, default key pattern,
  and masked preview-slice parameters.
- `SchemaBuilderPresenter` / `SchemaBuilderState` gain source-column pool,
  per-row dtype-check state, structured key-part state, and new-from-template
  seeding.
- `ColumnSpec` gains `expected_dtype`; `KeySpec` gains a structured part model;
  `DEDUP_MODES` gains `aggregate`. `schema_from_json` gains the forward migration.
- `SourceInputWidget` `schema_selected` signal wired to import gating;
  `_tab_combo.currentTextChanged` wired to `on_schema_discovery`.

## Data & State

- **Persisted:** matched source→canonical mapping as `ColumnSpec` aliases;
  `expected_dtype`; structured key parts; `aggregate` dedup mode; bumped version.
- **Migration:** forward-only in `schema_from_json`; bundled defaults migrated in
  place under `src/schemas/`.
- **Ephemeral UI state:** the draggable source-column pool and the dtype-check
  pass/fail indicators are recomputed at open time from the masked preview slice;
  they are not persisted. (The *mapping* is persisted; the *pool view* is not.)
- **Invariant:** a discriminator must reference an existing canonical or derived
  column (dropdown-only enforces this).

## Constraints & Risks

- PySide6 GUI; T3 adapter/UI tier. 500-line per-file cap applies;
  `src/schema_model.py` (487) and `src/gui/app.py` (500) must be decomposed before
  additions. New drag-drop tab/dialog modules must each stay <= 500 lines.
- Type-coercion checks and fuzzy matching keep pure logic separated from Qt
  widgets (presenter/service vs. passive view) for testability.
- Drag-and-drop has no precedent in the repo; assignment logic lives behind a
  view-protocol seam so presenter tests do not simulate drag events.
- The formula engine is `asteval` (already approved); reuse `FormulaEvaluator`.
- **Confidentiality (Decision 5):** real workbook values and proprietary source
  column names must never be committed in tests, fixtures, or artifacts. All
  preview-derived sample data and names must be masked. Scan changed files for
  leaked values before any commit.
- Caller-contract changes ripple to every call site that opens the Schema Builder.
- PySide6 CI needs the Ubuntu system libs and `QT_QPA_PLATFORM=offscreen`
  (see project memory) for pytest-qt collection.

## Implementation Strategy

- **Scope:** schema model split + new fields/model (`expected_dtype`, structured
  key parts, `aggregate` mode, version bump, forward migration); migrate bundled
  defaults; new drag-drop Columns/Key tabs and PowerQuery-style derived dialog;
  dtype-check widget + pure dtype-coercion logic; persisted alias matching +
  new-from-template; import gating; `on_schema_discovery` wiring; tab reorder;
  caller contract through the per-tab button.
- **Decomposition (from research H):** `_schema_model_specs.py`,
  `_columns_tab_drag.py`, `_key_tab_drag.py`, `_derived_formula_dialog.py`,
  `_dtype_check_widget.py`, `_columns_tab_presenter.py`, `_key_tab_presenter.py`,
  plus source-input button-wiring extraction.
- **Dependencies:** none new (`asteval`, `pandas`, `difflib` already present).
- **Reuse:** `find_best_match` / `_closest_candidates` for matching;
  `FormulaEvaluator.validate/.evaluate` + `known_column_names` for derived;
  `SchemaBuilderPresenter.load_existing` for edit-load.
- **Rollout:** no feature flag; forward migration runs on load.

## Definition of Done

- [x] Acceptance criteria documented and mapped to tests or demos
- [x] Behavior matches acceptance criteria in all documented environments
- [x] Tests updated/added (unit/integration as applicable)
- [x] Edge cases and error handling covered by tests
- [x] Docs updated (README, docs/features/active/... links)
- [x] Bundled default schemas migrated forward and load without error
- [x] No real workbook values or proprietary column names committed (masking scan)
- [x] Toolchain pass completed (format → lint → type-check → test)

## Acceptance Criteria

- [x] Import button disabled until a schema is selected; re-disables on placeholder.
- [x] Activating a source tab auto-selects the best-matching schema; placeholder
      shown when none matches.
- [x] An Edit-schema action loads an existing schema into the builder and re-saves.
- [x] A "New from template" action seeds a new schema from the closest existing one.
- [x] Schema Builder accepts required/optional column specs, default key pattern,
      and masked preview slice from the per-tab caller.
- [x] Columns tab renders draggable source-column buttons from the selected sheet.
- [x] Required/optional rows pre-populate via fuzzy matching; a matched source
      column is consumed (removed from the pool, cannot re-match).
- [x] Matched source→canonical mapping persists as aliases; reload re-matches the
      same source.
- [x] Activation-time matching runs first against persisted alias columns; partial
      match surfaces the new-from-template path.
- [x] Matched columns show a green check (coercible) or red X with a failing
      example value (not coercible).
- [x] Key tab supports drag-and-drop column parts plus a repeatable Generic Text
      token; a caller-supplied default key pattern is parsed onto the tab via the
      structured key-part model.
- [x] Dedup defaults to aggregate mode with the Key as discriminator; other
      columns selectable via dropdown only.
- [x] Derived tab precedes Columns; a dialog creates derived rows referencing
      named and previously-derived columns; derived columns appear on Columns.
- [x] `ColumnSpec.expected_dtype` added; schema version bumped; forward migration
      in `schema_from_json`; a bundled default with a discriminator migrates to
      aggregate mode (`default_le`), while one without a discriminator retains
      `mode: none` (`default_aop`).
