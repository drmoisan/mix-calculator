# configurable-schema-gui-fixes (Spec)

- **Issue:** #60
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-06-09
- **Status:** Final
- **Version:** 1.0
- **Work Mode:** full-bug

## Context
- Three related defects remain in the GUI's configurable-schema import
  integration. They are corrections to recently-shipped behavior in the
  issues #48/#50/#54/#58 lineage. Each defect is a distinct user-observable
  fault but they share the same configurable-schema GUI surface, so they are
  bundled into one fix.
- Observed environment: `poetry run mix-pipeline-gui` (PySide6 desktop GUI),
  importing LE / AOP / SKU_LU sources from a real workbook.
- Impact and severity:
  1. A user cannot edit the schema currently selected on a source tab; the
     only builder entry points are "Build new schema" (per tab) and the
     `Tools -> Schema Builder...` menu, neither of which seeds from the
     selected schema. Deterministic, every session.
  2. SKU_LU import does not auto-match a bundled default schema because none
     ships; only `default_le.schema.json` and `default_aop.schema.json` are
     bundled. Deterministic.
  3. Selecting the `AOP1` tab of a real AOP workbook never auto-matches and
     activates the AOP schema, because discovery treats the first sheet row as
     the header while the real AOP1 header is on Excel row 3 (zero-based index
     2). Deterministic for that workbook layout.
- First observed: 2026-06-09 on `main` (commit 1d27514, clean). All three are
  corrections to recently-shipped configurable-schema GUI behavior.

## Repro & Evidence

### Defect 1 — no Edit Schema button
- Steps: launch the GUI, select a real schema (for example `default_le`) in a
  source tab's schema combo, then look for a control to edit that schema.
- Expected vs actual: expected an "Edit Schema" button beside the per-input
  Import button that opens the schema builder seeded from the selected schema;
  actual is that `SourceInputWidget` exposes only a "Build new schema" button
  (signal `build_schema_requested`, `source_input_widget.py:87`/`:173`) and a
  `Tools -> Schema Builder...` menu action. No Edit-Schema control exists.
- Determinism: always.

### Defect 2 — no default SKU_LU schema
- Steps: launch the GUI, open the SKU_LU tab, observe schema auto-matching.
- Expected vs actual: expected a bundled `default_sku_lu` schema offered in the
  dropdown and auto-matched for a SKU_LU sheet; actual is that `src/schemas/`
  ships only `default_le.schema.json` and `default_aop.schema.json`, and
  `_schema_provider_factory.py:41` maps `"sku_lu": None`, so the SKU_LU tab has
  no bundled default to seed from or match against.
- Determinism: always.

### Defect 3 — AOP schema does not match the AOP1 tab
- Steps: launch the GUI, select the `AOP1` tab of a real AOP workbook
  (`artifacts/LE v AOP Gross to Net Decomp v3.xlsx`), trigger schema discovery.
- Expected vs actual: expected discovery to auto-match and activate the default
  AOP schema; actual is that `SourceSelectionPresenter.on_schema_discovery`
  reads `max_rows=_HEADER_PREVIEW_ROWS` (`= 1`) and uses `headers = rows[0]`
  (`source_selection_presenter.py:43`/`:195`). For AOP1 the header is on Excel
  row 3 (zero-based index 2); rows 1-2 are stray/blank. Reading only row 1 and
  matching it against the AOP schema's required columns fails every time, so
  `classify_activation` returns `"none"` and the AOP schema never activates.
- Workbook fact (verified externally; subagents cannot open `.xlsx`): in `AOP1`
  the header is on Excel row 3 (zero-based index 2); rows 1-2 are stray/blank;
  the 26 header names match `default_aop.schema.json` exactly. No computed
  workbook cell values are reproduced in this spec.
- Determinism: always, for the AOP1 layout.

## Scope & Non-Goals

### In scope
- Defect 1: an "Edit Schema" button beside each per-input Import button in
  `SourceInputWidget`, opening the schema builder seeded from the tab's
  currently-selected schema via `schema_builder_presenter.load_existing(name)`.
  The button is disabled when no real schema is selected (placeholder
  `<Choose Schema>`), mirroring the Import button's gating. Because
  `source_input_widget.py` is at 497/500 lines, button construction/gating
  helpers are extracted (the planner finalizes the exact extraction).
- Defect 2: a bundled `src/schemas/default_sku_lu.schema.json` (columns SKU,
  SKU Description, Category, Country; Country carries alias `["International"]`;
  key `[SKU]`; `header_row` 0; no dedup, no derived columns, no fill rules) so
  SKU_LU import auto-matches. `_schema_provider_factory.py`
  `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]` changes from `None` to
  `"default_sku_lu"`. The registry auto-discovers the new file.
- Defect 3: header-row-aware discovery — `on_schema_discovery` selects the best
  header row from a multi-row preview instead of always using `rows[0]`, so the
  AOP1 tab (header on index 2) auto-matches, without regressing LE
  (`LE-8 + 4`) or SKU_LU (`SKU_LU`) whose headers are on row 0.
- Classifying every production module touched by this change in
  `quality-tiers.yml`.

### Out of scope / non-goals
- No change to the country-code mapping logic (`"0" -> "US"`, `"1" -> "Canada"`)
  in `load_skulu`. That mapping is a loader-side cell-value transform with no
  representation in the schema model; it stays loader-only and is not encoded
  in `default_sku_lu.schema.json`.
- No change to the legacy CLI loaders or to the protected loaders'
  independent header detection on the import path (`_aop_schema_import.py`
  re-detects the header from the full file at import time; discovery and import
  header rows remain independently computed).
- No new third-party dependency.
- No change to the schema builder presenter's `load_existing` contract, the
  schema model, the registry's discovery mechanism, or the
  `classify_activation` interface.
- This spec specifies observable behavior and acceptance criteria only; the
  implementation plan and task breakdown are the atomic-planner's job.

## Root Cause Analysis
- Defect 1: the widget was never given an Edit-Schema control or signal; the
  only seeded-builder entry point (`build_schema_requested`) seeds from the
  bundled default's required/optional specs, not from the selected schema's
  full definition. Affected: `src/gui/widgets/source_input_widget.py`,
  `src/gui/widgets/_source_input_button_wiring.py`, `src/gui/_schema_wiring.py`,
  `src/gui/_schema_discovery_wiring.py`.
- Defect 2: no `default_sku_lu.schema.json` is bundled and
  `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]` is `None`, so the SKU_LU tab has no
  default to match or seed from. Affected:
  `src/schemas/default_sku_lu.schema.json` (new),
  `src/gui/_schema_provider_factory.py`.
- Defect 3: `_HEADER_PREVIEW_ROWS = 1` and `headers = rows[0]` in
  `on_schema_discovery` assume the header is always the first preview row. For
  AOP1 the first row is stray/blank, so matching fails. Affected:
  `src/gui/presenters/source_selection_presenter.py`.

## Proposed Fix

### Design summary (what changes where):
- Defect 1: add an `edit_schema_requested` signal and an "Edit Schema" button
  to `SourceInputWidget`, gated by the same real-vs-placeholder check as the
  Import button. Add a `wire_edit_schema_buttons` function that, per source
  widget, reads the selected schema name, guards against placeholder/empty,
  opens the builder, and calls `schema_builder_presenter.load_existing(name)`.
  `wire_schema_discovery_and_gating` calls the new wiring alongside the build
  wiring. Extract button construction/gating helpers to keep
  `source_input_widget.py` under 500 lines.
- Defect 2: add `src/schemas/default_sku_lu.schema.json`; update
  `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]` to `"default_sku_lu"`.
- Defect 3: read a multi-row preview and select the best-matching header row
  from it; fall back to the first preview row when no row matches a schema, so
  LE and SKU_LU (header on row 0) are unaffected.

### Boundaries and invariants to preserve:
- Import behavior for LE, AOP, and SKU_LU is unchanged. The discovery change
  improves header selection; it must not change which schema activates for LE
  or SKU_LU (still row 0) and must not change import-time header detection.
- The Edit button must never open a builder for the placeholder selection and
  must not crash when no file/sheet/schema is selected (the #50 activation-seam
  lesson: no-file / no-schema paths must not crash).
- Discovery must not crash when the first preview row is blank.
- The country-code mapping in `load_skulu` is untouched.
- All changed/added production, test, and reusable-script files remain
  <= 500 lines.

### Dependencies or blocked work:
- None. Branches off current `main` (commit 1d27514, clean). All upstream
  schema-loader and header-detection machinery is already merged.

### Implementation strategy (what changes, not sequencing):

#### Files/modules to change:
- `src/gui/widgets/source_input_widget.py` — add the Edit-Schema button,
  `edit_schema_requested` signal, and gating; extract helpers to stay under the
  500-line cap.
- `src/gui/widgets/_source_input_button_wiring.py` — host the extracted
  Edit-button construction/gating helpers.
- `src/gui/_schema_wiring.py` — add `wire_edit_schema_buttons`.
- `src/gui/_schema_discovery_wiring.py` — call `wire_edit_schema_buttons`.
- `src/schemas/default_sku_lu.schema.json` — new bundled schema.
- `src/gui/_schema_provider_factory.py` — map `"sku_lu"` to `"default_sku_lu"`.
- `src/gui/presenters/source_selection_presenter.py` — multi-row preview and
  best-header-row selection in `on_schema_discovery`.
- `quality-tiers.yml` — classify the touched-but-unclassified modules.

#### Functions/classes/CLI commands impacted:
- `SourceInputWidget` (new signal, button, gating), the schema wiring functions,
  `SourceSelectionPresenter.on_schema_discovery`, and `DEFAULT_SOURCE_SCHEMA_NAMES`.
- No CLI surface changes.

#### Data flow and validation changes:
- Discovery reads more than one preview row and selects the row that best
  matches a candidate schema (earliest row wins ties), falling back to the
  first row when no row matches a schema. The Edit button reads the selected
  schema name and routes it to `load_existing`, guarding placeholder/empty.

#### Error handling and logging updates:
- The Edit-button wiring guards against placeholder/empty selection (defense in
  depth alongside the widget-level disabled state). Discovery tolerates a blank
  first preview row without raising.

#### Rollback/feature-flag considerations (if applicable):
- None. Each defect's fix is additive or localized; behavior for existing
  LE/AOP/SKU_LU import is preserved.

### Technical specifications (interfaces/contracts):

#### Inputs/outputs and formats:
- `default_sku_lu.schema.json`: canonical columns `SKU`, `SKU Description`,
  `Category`, `Country`; `Country` aliases `["International"]`; key parts
  `[{"kind": "column-ref", "value": "SKU"}]` with `sku_coercion: false`;
  `header_row: 0`; `dedup.mode: "none"`; empty `derived_columns`, `fill_rules`,
  `drop_columns`. Parses against the schema model and appears in the dropdown.
- The Edit-button path passes the selected schema name (not the placeholder) to
  `schema_builder_presenter.load_existing(name)`, which seeds the builder from
  the full existing schema (columns, aliases, key, dedup, derived columns).

#### Required configuration keys and defaults:
- `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]` default changes from `None` to
  `"default_sku_lu"`. No other config keys change.

#### Backward-compatibility expectations:
- LE and AOP defaults unchanged. The new SKU_LU default is additive. The
  discovery change preserves existing LE/SKU_LU header selection (row 0).

#### Performance constraints (latency/throughput/memory):
- Discovery may match candidate schemas against up to a few preview rows on tab
  activation (a user interaction). The added cost is bounded and acceptable.

## Assumptions, Constraints, Dependencies
- Assumptions: a valid AOP1-style sheet has its real header within the widened
  preview window; LE/SKU_LU headers remain on row 0. The schema builder
  presenter exposes `load_existing(name)` as researched.
- Constraints: 500-line file cap on all changed files; Black/Ruff/Pyright clean;
  no new dependencies; coverage >= 85% line / >= 75% branch with no regression
  on changed lines; every project in `quality-tiers.yml`.
- External dependencies: PySide6, pandas/openpyxl (already present).

## Data / API / Config Impact
- User-facing: a new "Edit Schema" button per source tab; SKU_LU now offers and
  auto-matches a bundled default; AOP1 discovery auto-matches the AOP schema.
- Data/migration: a new bundled schema JSON; no user-data migration.
- Logging/telemetry: optional debug log of the detected discovery header row.
- Compatibility: CLI flags and existing config schemas unchanged.

## Test Strategy
- Defect 1: widget tests that the Edit button is present, disabled on the
  placeholder, enabled on a real schema, and emits `edit_schema_requested`;
  wiring tests that the Edit path opens the builder seeded via `load_existing`
  with the selected name and short-circuits on placeholder/empty.
- Defect 2: `tests/test_default_schemas.py` parses `default_sku_lu`, asserts the
  canonical column order, the `International` alias on `Country`, key `SKU` with
  `sku_coercion=False`, `header_row=0`, and empty dedup/derived/fill_rules;
  `tests/gui/test_schema_provider_factory.py` asserts the new `sku_lu` mapping.
- Defect 3: presenter unit tests with a multi-row preview where the first rows
  are stray/blank and the real header is on a later row (AOP1-style) match and
  select the correct header; LE/SKU_LU single-row-header previews still select
  row 0; a blank first preview row does not crash discovery.
- No-regression: existing LE/AOP/SKU_LU import, discovery, and builder tests
  pass unchanged.
- Toolchain: Black -> Ruff -> Pyright -> Pytest (`--cov --cov-branch`),
  coverage >= 85% line / >= 75% branch, no regression on changed lines.
- Determinism: tests use `FakeWorkbookReader` preview rows; no temp files, no
  wall-clock, no network.

## Acceptance Criteria
- [x] AC-1: An "Edit Schema" button is present beside each per-input Import
      button in `SourceInputWidget` (LE, AOP, SKU_LU tabs).
- [x] AC-2: Clicking "Edit Schema" with a real schema selected opens the schema
      builder seeded from that schema via
      `schema_builder_presenter.load_existing(<selected name>)` (the builder
      shows the selected schema's columns, aliases, key, and dedup, not a blank
      or default-seeded builder).
- [x] AC-3: The "Edit Schema" button is disabled when no real schema is
      selected (the placeholder `<Choose Schema>` is selected), mirroring the
      Import button's gating; the Edit-schema wiring additionally short-circuits
      (no builder opens, no crash) if invoked with a placeholder or empty name.
- [x] AC-4: A bundled `src/schemas/default_sku_lu.schema.json` exists with
      columns SKU, SKU Description, Category, Country; `Country` carries alias
      `["International"]`; key parts `[SKU]` with `sku_coercion=false`;
      `header_row` 0; `dedup.mode` "none"; empty `derived_columns`,
      `fill_rules`, and `drop_columns`. It parses against the schema model.
- [x] AC-5: The registry auto-discovers `default_sku_lu` (it appears in the
      schema dropdown at startup) and `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]`
      maps to `"default_sku_lu"`, so the SKU_LU per-tab "Build new schema"
      button seeds from it and a SKU_LU sheet auto-matches it.
- [x] AC-6: The country-code mapping (`"0" -> "US"`, `"1" -> "Canada"`) is not
      encoded in `default_sku_lu.schema.json` and remains in `load_skulu`
      unchanged.
- [x] AC-7: `SourceSelectionPresenter.on_schema_discovery` reads a multi-row
      preview and selects the best-matching header row, so a sheet whose real
      header is on a later row (AOP1: Excel row 3 / index 2, with stray/blank
      leading rows) auto-matches and activates its schema.
- [x] AC-8: Discovery for LE (`LE-8 + 4`) and SKU_LU (`SKU_LU`), whose headers
      are on row 0, is unchanged: the best-header-row selection returns row 0
      and the same schema activates as before (no regression).
- [x] AC-9: Discovery does not crash when the first preview row is blank or when
      no file/sheet/schema is selected (the #50 activation-seam guard paths are
      exercised by tests).
- [x] AC-10: Every production module touched by this change is classified in
      `quality-tiers.yml` (no unclassified project remains; tier-classification
      stays green).
- [x] AC-11: No regression to existing LE / AOP / SKU_LU import, schema
      discovery, or schema-builder behavior; the existing test suite passes.
- [x] AC-12: All changed and added files (production, test, reusable scripts)
      remain <= 500 lines.
- [x] AC-13: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with
      coverage >= 85% line / >= 75% branch and no regression on changed lines.

## Risks & Mitigations
- Risk: best-header-row selection changes which schema activates for LE/SKU_LU.
  Mitigation: AC-8 asserts row-0 selection and parity for LE/SKU_LU; fall back
  to the first row when no row matches.
- Risk: the Edit button opens a builder for the placeholder or crashes on the
  no-file/no-schema seam. Mitigation: AC-3 and AC-9 require both widget-level
  disabling and wiring-level guards, with tests on the guard paths.
- Risk: `source_input_widget.py` exceeds the 500-line cap when the Edit button
  is added. Mitigation: extract button construction/gating helpers (AC-12).
- Risk: an unclassified touched module fails the `tier-classification` CI stage.
  Mitigation: AC-10 requires classifying every touched module.

## Rollout & Follow-up
- Rollout: standard PR to `main` with green CI.
- Post-fix: confirm AOP1 auto-match end to end against the real workbook layout
  during manual GUI validation.
- Links: issue #60; research
  `artifacts/research/configurable-schema-gui-fixes-60.md`.
