# Feature Audit: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 1 EXIT Reaudit

- **Timestamp:** 2026-06-05T21-27
- **Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `7b8994c`
- **Work Mode:** full-feature → AC sources: `spec.md` (Acceptance Criteria, 14 items) AND `user-story.md` (Acceptance Criteria, condensed subset)
- **Verdict:** All acceptance criteria are backed by passing integrated tests. No AC remains `[x]` without proof. Feature behavior is delivered. (A separate file-size policy violation is recorded in the policy audit; it does not invalidate any AC.)

## Scope and Baseline

The audit scope is the full feature branch diff against the resolved base branch
`main` (merge-base `5e659f2`; head `7b8994c`), per the PR context artifacts. This
is the EXIT reaudit of remediation cycle 1, which performed integration wiring for
the prior cycle's six blocking findings (R1–R6). Acceptance criteria are evaluated
relative to the `main` baseline: the feature adds drag-drop schema-builder tabs, a
derived-formula dialog, a caller-driven `BuildSpecProvider`, new-from-template
seeding, partial-match handling, an `expected_dtype` field, a structured key-part
model, an `aggregate` dedup mode, and a forward schema migration. No scope
narrowing to any plan/task/phase was applied; the full branch diff was audited.

## Summary

The remediation cycle delivers the full acceptance-criteria set. All 14 spec AC
and all 12 condensed user-story AC are satisfied and proven by passing integrated
tests that drive the production objects (`build_application` and the opened
`SchemaBuilderDialog`). The tested-but-unwired defect class that caused the prior
FAIL is closed. One blocking policy violation (a 506-line test file over the
500-line cap) is tracked separately in the policy audit and remediation inputs; it
is a file-size policy issue, not an unmet acceptance criterion, so it does not
change any AC verdict.

## Acceptance Criteria Inventory

Authoritative AC source for full-feature mode: `spec.md` lines 237-263 (14 criteria) and `user-story.md` lines 46-61 (condensed restatement). The remediation cycle's blocking findings R1–R6 mapped to spec AC 4, 5, 6, 7, 9, 10, 11, 13.

Spec AC index (paraphrased):
1. Import gating; re-disable on placeholder.
2. Tab activation auto-selects best-matching schema; placeholder on no-match.
3. Edit-schema loads existing schema and re-saves.
4. "New from template" seeds a new schema from the closest existing one. (R5)
5. Builder accepts required/optional specs, default key pattern, masked preview slice from per-tab caller. (R4)
6. Columns tab renders draggable source-column buttons. (R1)
7. Required/optional rows pre-populate via fuzzy matching; matched column consumed. (R1 UI)
8. Matched mapping persists as aliases; reload re-matches.
9. Activation-time matching runs first against persisted aliases; partial match surfaces new-from-template. (R6)
10. Matched columns show green check / red X with failing example value. (R1 dtype)
11. Key tab supports drag-and-drop parts + repeatable Generic Text; default key pattern parsed. (R2)
12. Dedup defaults to aggregate with Key discriminator; dropdown-only.
13. Derived tab precedes Columns; dialog creates derived rows; derived columns appear on Columns. (R3)
14. `ColumnSpec.expected_dtype` added; version bumped; forward migration; LE→aggregate, AOP retains none. (N3 reconciled)

## Acceptance Criteria Evaluation

| AC | Verdict | Backing integrated test / evidence |
|----|---------|------------------------------------|
| 1 Import gating | PASS | `test_source_selection_presenter.py` import-gate tests; `app.py` source-signal wiring re-enables/disables on selection. |
| 2 Auto-select on activation | PASS | `test_on_schema_discovery_proceed_selects_matched_schema`; `_no_match_sets_placeholder`. |
| 3 Edit existing schema | PASS | `schema_builder_presenter.load_existing` round-trip tests; build-button path opens existing schema. |
| 4 New from template (R5) | PASS | `test_build_application_new_from_template_seeds_live_dialog` — drives `build_application`, asserts `new_from_template` ran and dialog seeded with blank name. Production caller `_schema_open_helpers.py:159`. |
| 5 Caller specs + key pattern + preview slice (R4) | PASS | `test_build_application_per_tab_button_seeds_via_injected_provider` — injected `BuildSpecProvider` from `build_application` (`app.py:430`) seeds presenter; menu path asserted blank. |
| 6 Draggable source-column buttons (R1) | PASS | `test_live_columns_tab_has_drag_tokens_and_dtype_indicators` — live dialog Columns tab is `ColumnsTabWidget`, `token_names()` non-empty. |
| 7 Fuzzy pre-populate + consume (R1 UI) | PASS | Columns presenter `prepopulate`/consumed-pool tests + the live-dialog token test; `DragTabBinder.set_columns` runs prepopulate. |
| 8 Persisted alias mapping; reload re-matches | PASS | `test_schema_serialization*` / `test_schema_migration` alias round-trip; matching registry tests. |
| 9 Activation matching first against aliases; partial → template (R6) | PASS | `test_build_application_partial_match_reaches_new_from_template` — partial band through `build_application` invokes injected `on_partial_match` (three call sites `app.py:335,342,349`); placeholder retained, Import stays disabled. |
| 10 Green check / red X with failing example (R1 dtype) | PASS | `_dtype_check_widget` + columns-tab dtype-indicator tests; live-dialog test asserts at least one dtype indicator; failing example masked (Decision 5). |
| 11 Key drag parts + Generic Text + default pattern (R2) | PASS | `test_live_key_tab_has_drag_widget_with_seeded_parts` — `KeyTabWidget`, `parts_text()` reflects seeded pattern, Generic Text token present. |
| 12 Dedup aggregate default + dropdown-only | PASS | `test_dedup_default_mode_is_aggregate`; `test_dedup_discriminator_is_dropdown_of_existing_columns`; `test_dedup_unknown_discriminator_is_rejected`. |
| 13 Derived before Columns; dialog; surfaces on Columns (R3) | PASS | `test_tab_order_matches_decision_10`; `test_live_derived_button_adds_column_to_columns_tab` — real `DerivedFormulaDialog`, accepted column appears on Columns tab. |
| 14 expected_dtype + version bump + migration (LE→aggregate, AOP none) | PASS | `test_schema_model` / `test_dtype_check` / `test_schema_migration`; JSON inspection: LE `mode: aggregate` (discriminator `YTD/YTG`), AOP `mode: none` (null discriminator); spec Decision 1 / AC 14 reconciled (N3). |

User-story.md AC (lines 46-61) are a condensed subset of the spec AC (it omits AC 4 new-from-template and AC 8 persistence wording). Every user-story AC maps to a spec AC evaluated PASS above; all are backed by the same integrated tests. No user-story AC is `[x]` without proof.

## Acceptance Criteria Check-off

- spec.md: all 14 AC are `[x]`. Verified each is backed by a named passing integrated test (table above). No change required; none rolled back.
- user-story.md: all 12 condensed AC are `[x]`. Verified each maps to a PASS spec AC with a passing integrated test. No change required.

No phantom criteria were added; criterion text was not modified.

### Acceptance Criteria Status

- Source: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md` and `.../user-story.md`
- Total AC items: 14 (spec) + 12 (user-story condensed)
- Checked off (delivered): 14 (spec) + 12 (user-story)
- Remaining (unchecked): 0 / 0
- Items remaining: none

## Notes

- The defect class that caused the prior FAIL (tested-but-unwired seams) is closed: all R1–R6 seams have production callers reachable from `build_application` or the opened `SchemaBuilderDialog`, proven by dialog-level / composition-root integration tests rather than isolated widget tests.
- A blocking file-size policy violation (`tests/gui/test_schema_builder_presenter.py` = 506 lines) is tracked in `policy-audit.2026-06-05T21-27.md` and `remediation-inputs.2026-06-05T21-27.md`. It is a policy violation, not an unmet acceptance criterion.
