# configurable-schema-gui-fixes (Issue #60)

- Date captured: 2026-06-09
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/configurable-schema-gui-fixes/ (Issue #60)
- Type: bug (bundle of three related defects in the configurable-schema GUI integration)

- Issue: #60
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/60
- Last Updated: 2026-06-09
- Work Mode: full-bug

## Problem / Why

Three related defects remain in the GUI's configurable-schema import integration.
They are corrections to recently-shipped behavior (issues #48/#50/#54/#58 lineage):

1. **No "Edit Schema" button.** The GUI was supposed to expose an "Edit Schema"
   control next to each per-input "Import" button so a user can open the schema
   builder seeded from the currently-selected schema. Today `SourceInputWidget`
   has only a "Build new schema" button and a `Tools -> Schema Builder...` menu
   action; no Edit-Schema button exists.

2. **No default SKU_LU schema.** `src/schemas/` ships only `default_le.schema.json`
   and `default_aop.schema.json`. There is no bundled `default_sku_lu.schema.json`,
   so SKU_LU import does not auto-match a default schema. The canonical SKU_LU
   columns are defined in `src/load_skulu.py`.

3. **AOP schema does not match the AOP1 tab.** Schema discovery treats the first
   sheet row as the header (`SourceSelectionPresenter.on_schema_discovery` uses
   `headers = rows[0]`). The `AOP1` tab's real header is not on the first row, so
   the matcher compares a non-header row and never activates the AOP schema.

## Proposed Behavior

1. Add an "Edit Schema" button beside the per-input Import button that opens the
   schema builder seeded from the tab's currently-selected schema for editing.
2. Add a bundled `default_sku_lu.schema.json` mirroring the canonical SKU_LU
   columns (`SKU`, `SKU Description`, `Category`, `Country` from `International`)
   with key = `SKU`, so SKU_LU import auto-matches.
3. Make schema discovery honor the actual header row (reuse the existing
   `detect_header_row` from `src/_header_detection.py` and/or each candidate
   schema's `header_row`) so the AOP schema matches the AOP1 tab.

## Acceptance Criteria

The authoritative acceptance criteria for this full-bug issue live in
`spec.md`. They are reproduced here for tracking.

- [ ] AC-1: An "Edit Schema" button is present beside each per-input Import
      button in `SourceInputWidget` (LE, AOP, SKU_LU tabs).
- [ ] AC-2: Clicking "Edit Schema" with a real schema selected opens the schema
      builder seeded from that schema via
      `schema_builder_presenter.load_existing(<selected name>)` (the builder
      shows the selected schema's columns, aliases, key, and dedup, not a blank
      or default-seeded builder).
- [ ] AC-3: The "Edit Schema" button is disabled when no real schema is
      selected (the placeholder `<Choose Schema>` is selected), mirroring the
      Import button's gating; the Edit-schema wiring additionally short-circuits
      (no builder opens, no crash) if invoked with a placeholder or empty name.
- [ ] AC-4: A bundled `src/schemas/default_sku_lu.schema.json` exists with
      columns SKU, SKU Description, Category, Country; `Country` carries alias
      `["International"]`; key parts `[SKU]` with `sku_coercion=false`;
      `header_row` 0; `dedup.mode` "none"; empty `derived_columns`,
      `fill_rules`, and `drop_columns`. It parses against the schema model.
- [ ] AC-5: The registry auto-discovers `default_sku_lu` (it appears in the
      schema dropdown at startup) and `DEFAULT_SOURCE_SCHEMA_NAMES["sku_lu"]`
      maps to `"default_sku_lu"`, so the SKU_LU per-tab "Build new schema"
      button seeds from it and a SKU_LU sheet auto-matches it.
- [ ] AC-6: The country-code mapping (`"0" -> "US"`, `"1" -> "Canada"`) is not
      encoded in `default_sku_lu.schema.json` and remains in `load_skulu`
      unchanged.
- [ ] AC-7: `SourceSelectionPresenter.on_schema_discovery` reads a multi-row
      preview and selects the best-matching header row, so a sheet whose real
      header is on a later row (AOP1: Excel row 3 / index 2, with stray/blank
      leading rows) auto-matches and activates its schema.
- [ ] AC-8: Discovery for LE (`LE-8 + 4`) and SKU_LU (`SKU_LU`), whose headers
      are on row 0, is unchanged: the best-header-row selection returns row 0
      and the same schema activates as before (no regression).
- [ ] AC-9: Discovery does not crash when the first preview row is blank or when
      no file/sheet/schema is selected (the #50 activation-seam guard paths are
      exercised by tests).
- [ ] AC-10: Every production module touched by this change is classified in
      `quality-tiers.yml` (no unclassified project remains; tier-classification
      stays green).
- [ ] AC-11: No regression to existing LE / AOP / SKU_LU import, schema
      discovery, or schema-builder behavior; the existing test suite passes.
- [ ] AC-12: All changed and added files (production, test, reusable scripts)
      remain <= 500 lines.
- [ ] AC-13: Full toolchain pass (Black -> Ruff -> Pyright -> Pytest) with
      coverage >= 85% line / >= 75% branch and no regression on changed lines.

## Constraints & Risks

- GUI changes are Qt-bound; tests must drive the no-file/no-sheet guard paths
  (see prior #50 GUI activation-seam crashes), not only the happy path.
- Header-row detection must not regress LE discovery (LE-8 + 4 header position).
- File-size cap (500 lines) applies to changed GUI and test files; several GUI
  modules are near the cap and may require extraction.
- Subagents cannot open `.xlsx`; the workbook facts (AOP1 header on Excel row 3)
  must be supplied to planning agents by the orchestrator.

## Test Conditions to Consider

- [ ] Unit: discovery honors detected header row for AOP1-style sheets with
      leading non-header rows; LE/SKU_LU unaffected.
- [ ] Unit: SKU_LU default schema parses and is listed/matched.
- [ ] GUI: Edit Schema button opens builder seeded from current schema; disabled
      / guarded when no schema is selected.
- [ ] Integration: end-to-end AOP1 discovery -> activation -> import against the
      real workbook layout.

## Next Step

- [ ] Promote to GitHub issue (bug template, full work-mode)
- [ ] Create active feature folder from the template