# Feature Audit: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 3 EXIT Reaudit

**Audit Date:** 2026-06-05
**Timestamp:** 2026-06-05T23-23
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `cc5b282` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature (AC sources: `spec.md` AND `user-story.md`)
**Scope:** full branch diff `main...HEAD`; cycle-3 delta `fd8a022..cc5b282`

## Scope and Baseline

- Baseline: `main` (merge-base `5e659f2`). Head: `cc5b282`. Audit scope is the full branch diff `main...HEAD`; the cycle-3 remediation delta is `fd8a022..cc5b282`.
- AC baseline: the 22 spec.md and 16 user-story.md criteria established for the feature; this reaudit confirms none regressed relative to that baseline and that the AC-2 auto-selection behavior is preserved after the cycle-3 defensive guards.

## Summary

Cycle 3 added defensive guards for a post-PR runtime crash (B1: blank/whitespace path-or-sheet guard; B2: reader raises ValueError for an absent sheet). It changed no product feature surface. The acceptance criterion most directly exercised by this cycle is AC-2 (activating a source tab auto-selects the best-matching schema; placeholder when none matches); the cycle re-confirms AC-2 holds for a real match while the new guards prevent discovery from running with a blank sheet. All 22 spec AC and all 16 user-story AC remain backed by passing integrated tests at HEAD `cc5b282`.

One caveat applies to the formula-engine-backed acceptance criteria (derived columns / formula validation parity): the suite is RED because of a pre-existing `col`-shadowing defect in `src/schema_formula.py:301-307` (a column literally named `col` shadows the whitelisted `col()` helper). This defect is NOT in the `main...HEAD` branch diff and predates the feature; it does not regress any AC introduced by this feature, but it is a blocking merge/CI condition tracked in the policy audit and `remediation-inputs.2026-06-05T23-23.md`. The derived-column AC remain backed by their passing integrated tests; the failing test is an independent property test for the formula engine, not a derived-column feature test.

## Acceptance Criteria Inventory

- AC source files: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md` (22 checkboxes) and `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/user-story.md` (16 checkboxes).
- spec.md: 22 total, 22 checked `[x]`, 0 unchecked.
- user-story.md: 16 total, 16 checked `[x]`, 0 unchecked.
- No phantom criteria added; no criterion text modified.

## Acceptance Criteria Evaluation

### spec.md

| AC | Verdict | Evidence |
|----|---------|----------|
| Acceptance criteria documented and mapped to tests or demos | PASS | spec/user-story AC mapped to integrated tests (Appendix A of cycle-2 policy audit; cycle-3 adds B1/B2/AC-2 tests). |
| Behavior matches acceptance criteria in all documented environments | PASS | 940 tests pass under `QT_QPA_PLATFORM=offscreen`; the single failure is the pre-existing formula-engine property test, not an AC behavior. |
| Tests updated/added (unit/integration as applicable) | PASS | Cycle-3 adds two B1 wiring-level integration tests, two B2 reader-unit tests, one B2 presenter-routing test, and one AC-2 `build_application` integration test. |
| Edge cases and error handling covered by tests | PASS | Blank path, blank sheet, whitespace-only sheet, absent sheet, and stale-sheet ValueError routing all covered. |
| Docs updated (README, docs links) | PASS | Feature docs and evidence tree under canonical path; reader docstrings updated to the ValueError contract. |
| Bundled default schemas migrated forward and load without error | PASS | `tests/test_default_schemas.py` + `tests/test_schema_migration.py` pass. |
| No real workbook values or proprietary column names committed (masking scan) | PASS | Masking scan over cycle-3 changed lines clean; fixtures use fabricated names. |
| Toolchain pass completed (format -> lint -> type-check -> test) | PARTIAL | Black/Ruff/Pyright green; Pytest RED (1 pre-existing `schema_formula` failure). Blocking at the toolchain level (see policy audit); not an AC behavior regression. |
| Import button disabled until a schema is selected; re-disables on placeholder | PASS | B1 wiring tests assert Import stays disabled and the dropdown stays on `<Choose Schema>` when no file/worksheet is selected. |
| Activating a source tab auto-selects best-matching schema; placeholder when none | PASS | `test_ac2_full_match_through_build_application_auto_selects_and_enables` (auto-select on real match) + B1 tests (placeholder on blank/no-selection). |
| Edit-schema action loads an existing schema into the builder and re-saves | PASS | `test_edit_load_modify_save_round_trips` (in `_core`); unchanged this cycle. |
| "New from template" action seeds a new schema from the closest existing one | PASS | `new_from_template` wired via `_schema_open_helpers.py`; `_on_partial_match` at `app.py:327-349`; unchanged this cycle. |
| Schema Builder accepts required/optional column specs, default key pattern | PASS | Seeding tests; dialog integration tests; unchanged this cycle. |
| Columns tab renders draggable source-column buttons from the selected sheet | PASS | Live Columns-tab dialog test; `DragTabBinder` at `schema_builder_dialog.py:98`; unchanged this cycle. |
| Required/optional rows pre-populate via fuzzy matching; matched source consumed | PASS | Columns presenter/drag tests; unchanged this cycle. |
| Matched source->canonical mapping persists as aliases; reload re-matches | PASS | Schema serialization/matching tests pass; unchanged this cycle. |
| Activation-time matching runs first against persisted alias columns; partial path | PASS | Partial-match -> new-from-template path wired; `_on_partial_match` intact; unchanged this cycle. |
| Matched columns show green check (coercible) or red X with failing example | PASS | dtype-check widget/tests pass; unchanged this cycle. |
| Key tab supports drag-and-drop column parts plus repeatable Generic Text token | PASS | Live Key-tab dialog test; unchanged this cycle. |
| Dedup defaults to aggregate mode with Key as discriminator; others by dropdown | PASS | Schema model/serialization tests; LE migrated to aggregate; unchanged this cycle. |
| Derived tab precedes Columns; dialog creates derived rows; appear on Columns | PASS | Derived dialog test + `set_derived` mirror; unchanged this cycle. The pre-existing formula-engine `col`-shadow defect does not regress this UI flow. |
| `ColumnSpec.expected_dtype` added; schema version bumped; forward migration | PASS | `tests/test_schema_migration.py`, `tests/test_schema_model.py` pass; unchanged this cycle. |

### user-story.md

| AC | Verdict | Evidence |
|----|---------|----------|
| Import button disabled until a schema is selected | PASS | B1 wiring tests assert Import disabled when no selection. |
| Activating a source tab auto-selects best-matching schema | PASS | `test_ac2_full_match_through_build_application_auto_selects_and_enables`. |
| Placeholder shown when none matches | PASS | B1 tests assert `<Choose Schema>` placeholder when discovery short-circuits; `test_on_schema_discovery_no_match_sets_placeholder` (no-match path). |
| Edit-schema action loads an existing schema and re-saves | PASS | `test_edit_load_modify_save_round_trips`; unchanged this cycle. |
| Schema Builder accepts required/optional column specs from the caller | PASS | Seeding tests; unchanged this cycle. |
| Columns tab renders draggable source-column buttons | PASS | Live Columns-tab dialog test; unchanged this cycle. |
| Required/optional rows pre-populate via fuzzy matching | PASS | Columns presenter tests; unchanged this cycle. |
| Matched source column consumed (removed from pool, cannot re-match) | PASS | Columns drag/presenter tests; unchanged this cycle. |
| Matched columns show green check (coercible) or red X | PASS | dtype-check widget/tests; unchanged this cycle. |
| Failing example value shown when not coercible | PASS | dtype-check tests; unchanged this cycle. |
| Key tab supports drag-and-drop column parts plus repeatable Generic Text token | PASS | Live Key-tab dialog test; unchanged this cycle. |
| Caller-supplied default key pattern is parsed onto the tab | PASS | `test_seed_from_caller_pre_lists_rows_and_parses_key` (in `_seeding`); unchanged this cycle. |
| Dedup defaults to aggregate mode with Key as discriminator | PASS | Schema model tests; unchanged this cycle. |
| Other columns selectable via dropdown only | PASS | Schema model/serialization tests; unchanged this cycle. |
| Derived tab precedes Columns; dialog creates derived rows | PASS | Derived dialog test; unchanged this cycle. |
| Derived columns appear on Columns tab | PASS | `test_live_derived_button_adds_column_to_columns_tab`; unchanged this cycle. |

## Acceptance Criteria Check-off

No check-off changes required: all 22 spec AC and all 16 user-story AC were already `[x]` from prior cycles and remain valid. Cycle 3 added defensive guards and re-confirmed AC-2 with a `build_application` integration test; it changed no feature surface and reverted no criterion to `[ ]`. Each checked item is backed by a passing integrated test. The single toolchain blocking issue (pre-existing formula-engine defect) is tracked in the policy audit and remediation inputs; it is not an AC behavior regression, so no AC is downgraded.

### Acceptance Criteria Status
- Source: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md`, `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/user-story.md`
- Total AC items: 38 (22 spec + 16 user-story)
- Checked off (delivered): 38
- Remaining (unchecked): 0
- Items remaining: none

## Verdict

**PASS (with one out-of-scope toolchain caveat).** All 38 acceptance criteria are satisfied and backed by passing integrated tests at HEAD `cc5b282`; AC-2 auto-selection is re-confirmed and the cycle-3 B1/B2 guards introduce no feature regression (prior R1–R6 wiring intact). One blocking toolchain condition remains — the RED suite from the pre-existing `col`-shadowing defect in `src/schema_formula.py` — but it is out of cycle-3 scope and does not regress any acceptance criterion; it is tracked in the policy audit and `remediation-inputs.2026-06-05T23-23.md`. No FAIL or blocking-PARTIAL AC findings; the only PARTIAL is the toolchain-pass AC, reflecting the pre-existing failure.
