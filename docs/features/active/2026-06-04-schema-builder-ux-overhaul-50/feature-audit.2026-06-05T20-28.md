# Feature Audit — schema-builder-ux-overhaul (Issue #50)

- Branch: `feature/schema-builder-ux-overhaul-50`
- Base: `main` (merge-base `5e659f2`); Head: `d8275d9`
- Work Mode: full-feature → AC sources: `spec.md` AND `user-story.md`
- Reviewer: feature-review agent
- Timestamp: 2026-06-05T20-28

## Scope and Baseline

The audit scope is the full branch diff against `main` (`git diff main...HEAD`).
Acceptance criteria are drawn from both `spec.md` (13 items, authoritative,
includes new-from-template, persisted matching, import-gating-on-placeholder)
and `user-story.md` (12 items, a subset). Where the two overlap, the spec text
governs. Verification standard for this feature (per the caller and prior
incident history): an AC is PASS only when production code satisfies it AND is
reachable from the composition root, not merely unit-tested in isolation.

Baseline coverage 99.5% line / 96.6% branch; post-change 97.63% / 93.63%
(PASS). Toolchain green (Black/Ruff/Pyright/Pytest all exit 0). 922 tests pass.

## Acceptance Criteria Inventory

Spec.md AC (authoritative):

1. Import button disabled until a schema is selected; re-disables on placeholder.
2. Activating a source tab auto-selects best-matching schema; placeholder when none.
3. Edit-schema action loads an existing schema into the builder and re-saves.
4. "New from template" seeds a new schema from the closest existing one.
5. Schema Builder accepts required/optional specs, default key pattern, masked preview slice from the per-tab caller.
6. Columns tab renders draggable source-column buttons from the selected sheet.
7. Required/optional rows pre-populate via fuzzy matching; matched source column consumed (removed from pool, cannot re-match).
8. Matched source→canonical mapping persists as aliases; reload re-matches.
9. Activation-time matching runs first against persisted alias columns; partial match surfaces new-from-template.
10. Matched columns show green check (coercible) or red X with a failing example value.
11. Key tab supports drag-and-drop column parts plus a repeatable Generic Text token; default key pattern parsed onto tab via structured key-part model.
12. Dedup defaults to aggregate with Key as discriminator; other columns selectable via dropdown only.
13. Derived tab precedes Columns; a dialog creates derived rows referencing named and previously-derived columns; derived columns appear on Columns.
14. `ColumnSpec.expected_dtype` added; schema version bumped; forward migration in `schema_from_json`; bundled defaults migrated to aggregate mode.
15. No real workbook values or proprietary column names committed (masking scan).

(User-story.md AC are a subset of the above; tracked jointly below.)

## Acceptance Criteria Evaluation

| # | Criterion (abbreviated) | Verdict | Evidence / Reason |
|---|---|---|---|
| 1 | Import gating on selection + re-disable on placeholder | PASS | `source_input_widget.py:495` `set_import_enabled(button, is_real)` self-gates on placeholder; `_schema_discovery_wiring.py:115-124` connects `schema_selected` → enable. Reachable via `app.py:436`. |
| 2 | Auto-select best match on tab activation; placeholder when none | PASS | `on_schema_discovery` → `classify_activation` → `set_selected_schema`; `_tab_combo.currentTextChanged` connected at `_schema_discovery_wiring.py:123`, wired from `app.py:436`. |
| 3 | Edit-schema loads existing schema and re-saves | PASS | `SchemaBuilderPresenter.load_existing` present and reachable via the menu/build-button open path (`_schema_wiring.py` open_schema_builder). Round-trip covered by `tests/gui/test_schema_builder_presenter.py`. |
| 4 | New-from-template seeds from closest existing | FAIL | `new_from_template` (`schema_builder_presenter.py:231`) has NO production caller; the partial-match path that would surface it is unwired (see #9). Unit-tested only. |
| 5 | Per-tab caller supplies required/optional specs, default key pattern, masked preview slice | FAIL | `wire_build_schema_buttons` is called without a `spec_provider` (`_schema_discovery_wiring.py:74`); no `BuildSpecProvider` is constructed in `src/`. Per-tab buttons open a blank builder. Seam tested only. |
| 6 | Columns tab renders draggable source-column buttons | FAIL | `_columns_tab_drag.py` has zero production importers; the live dialog uses `build_columns_tab` plain-text editor (`_schema_builder_tabs.py:160-172`). |
| 7 | Fuzzy pre-population + consumed-column exclusion | FAIL (UI) / PARTIAL (logic) | The matching/consume logic exists in `_columns_tab_presenter.py` and is tested, but the presenter is imported only by the orphaned drag widget; not reachable from the live dialog. |
| 8 | Matched mapping persists as aliases; reload re-matches | PASS | Alias persistence is at the model/serialization layer (`ColumnSpec` aliases, `schema_serialization.py`) and is exercised by activation matching (`_schema_activation.py`), which IS wired. Persisted-alias matching reachable independent of the drag UI. |
| 9 | Activation matching first against persisted aliases; partial → new-from-template | PARTIAL (blocking) | Alias-first activation matching IS wired and classifies "partial" (`_schema_activation.py`, `on_schema_discovery`). But the partial branch invokes `_on_partial_match`, which is never injected in production (`app.py:340-347`), so the new-from-template surface never appears. Matching works; the partial→template hand-off is dead. |
| 10 | Matched columns show green check / red X with failing example | FAIL (UI) / PARTIAL (logic) | Pure dtype-check logic (`src/dtype_check.py`) and `_dtype_check_widget.py` are implemented and tested, but the widget has no production importer; not shown in the live dialog. |
| 11 | Key tab drag-and-drop + repeatable Generic Text; default pattern parsed via structured model | FAIL (UI) / PARTIAL (model) | Structured key-part model + default-pattern parse are implemented and wired into the presenter/state (`schema_builder_presenter.py:150-162`); but the Key tab UI is the old `QLineEdit` "comma-separated" editor (`_schema_builder_tabs.py:175-187`). `_key_tab_drag.py` has no production importer. |
| 12 | Dedup defaults to aggregate with Key discriminator; dropdown-only | PASS | `build_dedup_tab` (`_schema_builder_tabs.py:204-210`) defaults mode to `aggregate` and uses a `QComboBox` discriminator (no free-text). Dropdown populated by the dialog. |
| 13 | Derived tab precedes Columns; dialog creates derived rows; derived appear on Columns | PARTIAL (blocking) | Tab order is correct: Identity→Derived→Columns→Key→Dedup→Preview (`schema_builder_dialog.py:86-91`). But the Derived tab is the old `QPlainTextEdit` "name|expression" editor (`_schema_builder_tabs.py:213-227`); the `DerivedFormulaDialog` (`_derived_formula_dialog.py`) is not wired to any button. Tab order PASS, formula-builder dialog FAIL. |
| 14 | expected_dtype + version bump + forward migration + bundled defaults migrated | PASS (with deviation adjudicated) | `expected_dtype` added to `ColumnSpec`; `SCHEMA_FORMAT_VERSION` bump; forward migration in `schema_from_json` (`schema_serialization.py:300-319`); LE migrated to `aggregate`. AOP kept `mode: none` — adjudicated PASS (see policy-audit Section 8; AOP has no discriminator, aggregate would break the model invariant). Spec text should be reconciled. |
| 15 | No real workbook values / proprietary names committed | PASS | `scan_masked_fixtures.py` exit 0 ("clean"); independent currency-signature scan clean; bundled-schema names are pre-existing on `main`, not newly leaked. |

## Summary

- PASS: 1, 2, 3, 8, 12, 14, 15 (7 of 15).
- FAIL: 4, 5, 6 (and the UI halves of 7, 10, 11) — interactive UI redesign and
  caller-contract/new-from-template are unreachable in production.
- PARTIAL (blocking): 9, 13 — the wired half works, the dependent hand-off
  (partial→template; formula-builder dialog) is dead.
- PARTIAL (logic-only, dependent on a FAIL): 7, 10, 11 — pure logic correct and
  tested but not reachable from the live dialog; rolled up under the FAILs.

The model/serialization/migration/activation-matching/import-gating/dedup-default
work is complete and integrated. The drag-and-drop UI, dtype-check display,
PowerQuery-style derived dialog, per-tab caller-spec injection, and
new-from-template flow are implemented and unit-tested but not wired into the
dialog the user opens or the composition root. The dialog still renders the
pre-feature plain-text editors.

### Distinct blocking findings (counted once each)

1. Drag-and-drop Columns tab UI not wired (AC 6; logic half of AC 7, 10).
2. Drag-and-drop Key tab UI not wired (AC 11 UI; default-pattern model is wired).
3. PowerQuery-style derived-formula dialog not wired (AC 13 dialog).
4. Per-tab build-spec provider not constructed/injected (AC 5).
5. `new_from_template` has no production caller (AC 4).
6. `on_partial_match` never injected → partial→new-from-template dead (AC 9).

Consolidated blocking_count for this feature: 6 (the discrete defects above).
The code-review's four blocking findings and the policy-audit's one wiring FAIL
describe the same set of defects and are NOT added again; the authoritative
total is the 6 distinct AC-level defects enumerated here.

Feature-audit verdict: FAIL (6 blocking findings). Remediation inputs written to
`remediation-inputs.2026-06-05T20-28.md`.

## Acceptance Criteria Check-off

No AC source-file checkboxes were changed by this review. The executor had
pre-checked all spec.md and user-story.md AC boxes to `[x]`. Based on this audit,
the following are NOT satisfied in production and their `[x]` marks are
inaccurate; they should be reverted to `[ ]` during remediation:

- spec.md AC 4 (New from template) — revert to `[ ]`.
- spec.md AC 5 (per-tab caller specs) — revert to `[ ]`.
- spec.md AC 6 (draggable Columns buttons) — revert to `[ ]`.
- spec.md AC 7 (fuzzy pre-population UI / consume) — revert to `[ ]`.
- spec.md AC 9 (partial → new-from-template) — revert to `[ ]`.
- spec.md AC 10 (green check / red X display) — revert to `[ ]`.
- spec.md AC 11 (Key drag-and-drop UI) — revert to `[ ]`.
- spec.md AC 13 (derived-formula dialog) — revert to `[ ]`.
- Corresponding user-story.md items — revert to `[ ]`.

This reviewer does not check off any item; items 1, 2, 3, 8, 12, 14, 15 remain
`[x]` (verified PASS).

### Acceptance Criteria Status

- Source: `spec.md` (15 items) and `user-story.md` (12 items, subset)
- Total AC items (spec.md): 15
- Verified PASS (delivered + reachable): 7 — items 1, 2, 3, 8, 12, 14, 15
- Not satisfied (FAIL/blocking-PARTIAL): 8 — items 4, 5, 6, 7, 9, 10, 11, 13
- Items remaining: New-from-template; per-tab caller specs; draggable Columns
  buttons; fuzzy-pre-population UI; partial→new-from-template; dtype check/X
  display; Key drag-and-drop UI; derived-formula dialog.
