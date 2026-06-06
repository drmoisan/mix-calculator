# Acceptance-Criteria Reconciliation (Remediation Cycle 1, P7-T10)

Timestamp: 2026-06-05T20-28
Work Mode: full-feature → AC sources are `spec.md` AND `user-story.md`.

This reconciliation confirms that every acceptance criterion delivered by the R1-R6
remediation is proven by an integrated test that drives the production object
(opened `SchemaBuilderDialog` or `build_application`), not an isolated
widget/presenter unit test. No AC remains `[x]` without a named passing integrated
test. Criterion text was not altered.

## spec.md — remediated ACs and their proving integrated test

| spec.md AC | Finding | Integrated test (passing) | State |
|---|---|---|---|
| AC 4 — "New from template" seeds a new schema from the closest existing one | R5 | `test_app_wiring_schema.py::test_build_application_new_from_template_seeds_live_dialog` | [x] |
| AC 5 — Builder accepts required/optional specs, default key pattern, masked preview slice from the per-tab caller | R4 | `test_app_wiring_schema.py::test_build_application_per_tab_button_seeds_via_injected_provider` | [x] |
| AC 6 — Columns tab renders draggable source-column buttons from the selected sheet | R1 | `test_schema_builder_dialog.py::test_live_columns_tab_has_drag_tokens_and_dtype_indicators` | [x] |
| AC 7 — required/optional rows pre-populate via fuzzy matching; matched source consumed | R1 (UI half) | `test_schema_builder_dialog.py::test_live_columns_tab_has_drag_tokens_and_dtype_indicators` (prepopulate runs on the live tab; consumed source removed from the pool) | [x] |
| AC 9 — activation-time matching; partial match surfaces new-from-template | R6 | `test_source_selection_presenter.py::test_build_application_partial_match_reaches_new_from_template` | [x] |
| AC 10 — matched columns show green check / red X with failing example | R1 (UI half) | `test_schema_builder_dialog.py::test_live_columns_tab_has_drag_tokens_and_dtype_indicators` (populated `DtypeCheckWidget` asserted on the live tab) | [x] |
| AC 11 — Key tab drag-and-drop column parts + repeatable Generic Text; default pattern parsed onto the tab | R2 | `test_schema_builder_dialog.py::test_live_key_tab_has_drag_widget_with_seeded_parts` | [x] |
| AC 13 — Derived tab dialog creates derived rows; derived columns appear on Columns | R3 | `test_schema_builder_dialog.py::test_live_derived_button_adds_column_to_columns_tab` | [x] |

The remaining spec.md ACs (Import gating, auto-select, edit-schema, alias
persistence, dedup defaults, expected_dtype/version/migration) were delivered and
verified in the prior implementation cycle and are unaffected by this remediation;
they remain `[x]` backed by the existing suite (922 → 932 tests all passing).

## user-story.md — remediated ACs

The user-story AC list mirrors the spec ACs (draggable columns, fuzzy pre-populate
+ consume, green/red dtype indicator, Key drag + Generic Text + default pattern,
Derived dialog, accepts caller specs, edit/auto-select/import-gate). Each remediated
user-story criterion is proven by the same integrated test named above for its spec
counterpart and remains `[x]`. Note: several user-story criteria are authored across
two wrapped lines each (a text-wrap artifact); per the acceptance-criteria-tracking
skill the criterion text was not reformatted, and every checkbox is `[x]`.

## AC Status Summary

- Source: docs/.../spec.md (## Acceptance Criteria) and docs/.../user-story.md (## Acceptance Criteria)
- spec.md — Total AC items: 14; Checked off (delivered): 14; Remaining: 0
- user-story.md — Total checkbox lines: 16 (12 logical criteria across wrapped lines); Checked off: 16; Remaining: 0
- Items remaining: none
- No AC remains `[x]` without a named passing integrated test for the criteria
  remediated this cycle (spec AC 4, 5, 6, 7, 9, 10, 11, 13).
