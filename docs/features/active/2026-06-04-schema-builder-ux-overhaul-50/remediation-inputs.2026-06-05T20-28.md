# Remediation Inputs — schema-builder-ux-overhaul (Issue #50)

- Branch: `feature/schema-builder-ux-overhaul-50`
- Base: `main`; Head: `d8275d9`
- Source artifacts:
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/policy-audit.2026-06-05T20-28.md`
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/code-review.2026-06-05T20-28.md`
  - `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/feature-audit.2026-06-05T20-28.md`
- Timestamp: 2026-06-05T20-28
- Consolidated blocking_count: 6

## Root Cause

New collaborator seams were added with `None`-default parameters and built behind
view-protocols, with full unit tests against the seams in isolation, but the
final composition-root injection and dialog integration were never completed.
High unit-test coverage masked the gap. The Schema Builder dialog the user opens
still renders the pre-feature plain-text/single-line editors.

## Remediation-Required Findings (blocking)

### R1 — Wire the drag-and-drop Columns tab into the live dialog
- AC: spec.md 6, and the UI half of 7 and 10.
- Files: `src/gui/widgets/schema_builder_dialog.py`,
  `src/gui/widgets/_schema_builder_tabs.py` (`build_columns_tab` L160-172),
  `src/gui/widgets/_columns_tab_drag.py`,
  `src/gui/widgets/_dtype_check_widget.py`,
  `src/gui/presenters/_columns_tab_presenter.py`.
- Required: replace the plain-text Columns editor with the drag widget;
  construct and drive `ColumnsTabPresenter`; render dtype-check indicators.
- Add an integrated test that opens `SchemaBuilderDialog` and asserts the
  Columns tab contains draggable source-column buttons and dtype indicators.

### R2 — Wire the drag-and-drop Key tab into the live dialog
- AC: spec.md 11 (UI; the structured-part model is already wired).
- Files: `src/gui/widgets/_schema_builder_tabs.py` (`build_key_tab` L175-187),
  `src/gui/widgets/_key_tab_drag.py`,
  `src/gui/presenters/_key_tab_presenter.py`.
- Required: replace the `QLineEdit` comma-separated Key editor with the drag
  widget + repeatable Generic Text token; drive `KeyTabPresenter`; render the
  caller-supplied default key pattern onto the tab.

### R3 — Wire the PowerQuery-style derived-formula dialog
- AC: spec.md 13 (dialog; tab order already correct).
- Files: `src/gui/widgets/_schema_builder_tabs.py` (`build_derived_tab`
  L213-227), `src/gui/widgets/_derived_formula_dialog.py`,
  `src/gui/widgets/schema_builder_dialog.py`.
- Required: add a button on the Derived tab that opens `DerivedFormulaDialog`;
  the dialog must offer named + previously-derived columns and reuse the
  existing `FormulaEvaluator`; created derived columns must appear on Columns.

### R4 — Construct and inject a `BuildSpecProvider` at the composition root
- AC: spec.md 5.
- Files: `src/gui/app.py`, `src/gui/_schema_discovery_wiring.py` (L74),
  `src/gui/_schema_build_specs.py`, `src/gui/_schema_wiring.py`.
- Required: build a production `BuildSpecProvider` mapping each source key to its
  required/optional specs, default key pattern, and masked preview slice, and
  pass it to `wire_build_schema_buttons`. The per-tab button must seed the
  builder; the menu path remains blank by design (Decision 7).

### R5 — Provide a production caller for `new_from_template`
- AC: spec.md 4.
- Files: `src/gui/presenters/schema_builder_presenter.py` (L231), the
  new-from-template UI affordance.
- Required: surface a "New from template" action that calls
  `new_from_template(closest_schema_name)`; reachable from R6's partial-match
  hand-off and/or an explicit menu/button.

### R6 — Inject `on_partial_match` into the source presenters
- AC: spec.md 9.
- Files: `src/gui/app.py` (L340-347),
  `src/gui/presenters/source_selection_presenter.py`.
- Required: pass an `on_partial_match` callback when constructing the three
  `SourceSelectionPresenter` instances; the callback opens the new-from-template
  builder (R5) for the closest existing schema on a partial activation outcome.

## Non-Blocking Findings (address opportunistically)

### N1 — `tests/test_schema_serialization.py` exceeds the 500-line cap
- 669 lines; split into focused test modules (round-trip vs. migration).

### N2 — Remove no-op `# noqa: N802`
- Files: `src/gui/widgets/_columns_tab_drag.py` (78,207,222),
  `src/gui/widgets/_key_tab_drag.py` (76,169,252,267). The `N` ruleset is not in
  ruff `select`; the directives are dead. Remove, or enable `N` if intended.

### N3 — Reconcile spec text on dedup migration (documentation only)
- `spec.md` Decision 1 and AC 14 say "bundled defaults migrated to aggregate
  mode." AOP correctly retains `mode: none` (no discriminator). Update the spec
  to state the migration applies to schemas that have a discriminator (LE);
  schemas without one (AOP) retain `none`. No code change.

## Verification on Re-Review

After remediation, re-confirm for each of R1–R6 that the seam has a production
caller reachable from `build_application`, not only a unit test. Re-run the full
toolchain and the masking scan; confirm coverage thresholds hold; re-check the
AC boxes in `spec.md` and `user-story.md` against integrated (dialog-level)
tests, not isolated widget tests.
