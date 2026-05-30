# gui-schema-builder — Spec

- **Issue:** #44
- **Parent:** Epic #40 (configurable-schema-subsystem)
- **Owner:** drmoisan
- **Last Updated:** 2026-05-30
- **Status:** Ready for planning
- **Version:** 1.0

## Overview

Feature D is the integration feature that exposes the configurable-schema
subsystem (Features A–C) through the GUI: a visual, point-and-click **schema
builder**, a **manual column-matching** dialog used when fuzzy matching fails,
and **runtime formula entry** for calculated columns. It wires schema discovery
into the import flow so that loading a file finds the best-matching schema,
explains a non-match, and offers to build or manually map a schema — then drives
the import through the Feature C `SchemaLoader`.

This feature adds new dialogs/presenters/protocols and a `SchemaService` seam,
and makes **behavior-preserving** edits to the existing GUI composition
(`app.py`, `main_window.py`, `protocols.py`, `pipeline_service.py`). For known
AOP/LE files the import result is unchanged because the bundled default schemas
reproduce current output exactly (Feature C parity). No existing CLI, transform,
or loader module behavior changes.

## Behavior

Schema discovery in the import flow:
- After a sheet is selected/previewed, the system reads the header row and calls
  `SchemaService.find_best_match(headers)` (Feature B over the Feature A
  registry). On a suitable match, import proceeds via `SchemaLoader` with the
  matched schema. On no suitable match, the GUI shows the mismatch explanation
  (Feature B `MismatchReport.render()`) and offers two actions: open the manual
  column-matching dialog, or open the schema builder to create a new schema.

Manual Column-Matching Dialog:
- Shows unmatched required columns (with their aliases) and the available source
  columns, with fuzzy suggestions and similarity scores. The user assigns
  matches point-and-click, may mark optional columns as ignored, and may persist
  accepted assignments back to the schema as alias additions (via the registry).

Schema Builder Dialog (point-and-click, tabbed):
- Identity (name, version, description, source-sheet hints); Columns (per-column
  canonical name, role dimension/measure/discriminator/drop, required, aliases);
  Key (ordered key columns + sku coercion); Dedup policy (none/collapse,
  discriminator column, per-measure additive vs select-from); Derived/Formula
  columns (name + formula text with validation via the Feature C
  `FormulaEvaluator`, plus copy-from); and a Preview that applies the in-progress
  schema to the loaded preview rows. Saving persists the schema through the
  Feature A registry.

Runtime formula entry:
- The formula field validates on entry using the Feature C engine; invalid or
  unsafe expressions are rejected inline with the descriptive `FormulaError`
  message; valid expressions are accepted.

Menu/action:
- A "Schema Builder..." action on the main window opens the builder outside the
  import flow for create/edit of schemas.

## Inputs / Outputs

- Inputs: user point-and-click actions; the loaded sheet headers/preview rows;
  persisted schemas from the Feature A registry.
- Outputs: persisted/updated schema JSON in the registry; imported frames
  produced by `SchemaLoader`. No change to the existing DB save/open behavior.
- Backward compatibility: existing import for known AOP/LE files yields identical
  results (Feature C parity); all existing GUI tests stay green.

## API / CLI Surface

No new CLI. New Python/Qt surface (planner finalizes names):
- `src/gui/services/schema_service.py`: `SchemaService` / `SchemaServiceProtocol`
  wrapping `SchemaRegistry`, `find_best_match_in_registry`, and `SchemaLoader`.
- `src/gui/protocols.py`: add `SchemaBuilderViewProtocol`,
  `ColumnMatchingViewProtocol` (no Qt import).
- `src/gui/presenters/schema_builder_presenter.py`,
  `src/gui/presenters/column_matching_presenter.py` (pure Python, no Qt).
- `src/gui/widgets/schema_builder_dialog.py`,
  `src/gui/widgets/column_matching_dialog.py` (passive Qt dialogs; split helper
  modules to respect the 500-line cap).
- Composition wiring in `src/gui/app.py` (+ a small wiring helper if needed) and
  a menu action on `src/gui/main_window.py`; schema-aware import path in
  `src/gui/pipeline_service.py` that preserves existing method behavior.

## Data & State

- The presenters hold the in-progress schema/matching state as plain Python
  (Feature A model objects); the dialogs are passive views.
- Persistence flows only through the Feature A `SchemaRegistry`.
- Determinism: no wall-clock/RNG in presenters; matching is deterministic (B).

## Constraints & Risks

- Existing-file behavior must not regress; edits to `app.py`/`pipeline_service.py`/
  `main_window.py`/`protocols.py` must be additive/behavior-preserving and keep
  the existing GUI test suite green.
- Presenters must be unit-testable without a `QApplication`; dialogs tested via
  `pytest-qt` with `QT_QPA_PLATFORM=offscreen`.
- Every new file < 500 lines; split dialogs/presenters into helper modules as
  needed (the schema builder is the largest widget in the project).
- No new dependency beyond asteval (already added in Feature C).
- Pyright strict; classify new modules in `quality-tiers.yml` (presenters/service
  T2; widgets T3 per the existing adapter/UI tier rationale).
- PySide6 CI needs the documented system libraries and `QT_QPA_PLATFORM=offscreen`.

## Implementation Strategy

- Add the `SchemaService` seam over A/B/C.
- Add the two view protocols, the two pure presenters, and the two passive Qt
  dialogs (+ helper modules as needed).
- Wire schema discovery into the import flow and add the "Schema Builder..."
  action; add a schema-aware import path that uses `SchemaLoader`, defaulting to
  current behavior for known files.
- Update `quality-tiers.yml`.
- No changes to existing CLI/transform/loader modules.

## Definition of Done

- [x] On import, the system finds the best-matching schema; a suitable match drives import via `SchemaLoader` with unchanged results for known AOP/LE files.
- [x] When no schema matches, the GUI shows the Feature B mismatch explanation and offers manual matching or building a new schema.
- [x] The manual column-matching dialog assigns matches point-and-click with fuzzy suggestions/scores and can persist accepted assignments as schema alias additions.
- [x] The schema builder dialog creates/edits and persists a schema point-and-click across all tabs (identity, columns, key, dedup, derived/formula, preview).
- [x] Runtime formula entry validates via the Feature C engine and rejects unsafe/invalid input inline with the descriptive message.
- [x] A "Schema Builder..." menu/action opens the builder outside the import flow.
- [x] Presenters are unit-tested without a `QApplication`; dialogs and import-flow wiring are tested via `pytest-qt`.
- [x] New modules pass Black, Ruff, Pyright (strict); changed code meets >= 85% line / >= 75% branch coverage on presenters/service; `quality-tiers.yml` updated.
- [x] Existing test suite remains green; existing import for known files yields identical results; no existing CLI/transform/loader behavior changed.
