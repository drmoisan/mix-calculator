# Feature Audit: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 4 EXIT Reaudit

**Audit Date:** 2026-06-05
**Timestamp:** 2026-06-05T23-44
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `a45a987` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature (AC sources: `spec.md` AND `user-story.md`)
**Scope:** full branch diff `main...HEAD`; cycle-4 delta `cc5b282..a45a987`

## Scope and Baseline

- Baseline: `main` (merge-base `5e659f2`). Head: `a45a987`. Audit scope is the full branch diff `main...HEAD`; the cycle-4 remediation delta is `cc5b282..a45a987`.
- AC baseline: the 22 spec.md and 16 user-story.md criteria established for the feature. This reaudit confirms all 38 are satisfied and that the cycle-4 C1 fix introduced no regression.

## Summary

Cycle 4 closed the single cycle-entry blocking finding C1 — the formula-engine `col`-shadowing defect that had left the test suite RED at the cycle-3 exit. With the fix in `src/schema_formula.py._build_symtable` (whitelisted callables bound after the alias loop), the full pytest suite is now green (942 passed, 0 failed, EXIT 0). The cycle changed no feature surface; it repaired a latent engine defect that backs the derived-column / formula-validation acceptance criteria.

All 22 spec.md and all 16 user-story.md acceptance criteria are satisfied and backed by passing integrated tests at HEAD `a45a987`. The previously-noted toolchain caveat (RED suite from C1) is resolved, so the toolchain-pass acceptance criterion is now PASS rather than PARTIAL. No acceptance criterion is FAIL or blocking-PARTIAL.

## Acceptance Criteria Inventory

- AC source files: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md` (22 checkboxes) and `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/user-story.md` (16 checkboxes).
- spec.md: 22 total, 22 checked `[x]`, 0 unchecked.
- user-story.md: 16 total, 16 checked `[x]`, 0 unchecked.
- No phantom criteria added; no criterion text modified.

## Acceptance Criteria Evaluation

### spec.md

| AC | Verdict | Evidence |
|----|---------|----------|
| Acceptance criteria documented and mapped to tests or demos | PASS | spec/user-story AC mapped to integrated tests across the feature suite. |
| Behavior matches acceptance criteria in all documented environments | PASS | 942 tests pass under `QT_QPA_PLATFORM=offscreen`; 0 failures. |
| Tests updated/added (unit/integration as applicable) | PASS | Cycle 4 adds the C1 regression test; prior cycles added GUI/wiring/schema tests. |
| Edge cases and error handling covered by tests | PASS | Column-name-collides-with-helper edge case now covered; B1/B2 blank/absent-sheet cases retained. |
| Docs updated (README, docs links) | PASS | Feature docs and evidence tree under canonical path; `_build_symtable` docstring updated. |
| Bundled default schemas migrated forward and load without error | PASS | `tests/test_default_schemas.py` + `tests/test_schema_migration.py` pass. |
| No real workbook values or proprietary column names committed (masking scan) | PASS | Masking scan over cycle-4 changed lines clean; fixtures use fabricated names (`col`/`sum`/`safe_div` literals). |
| Toolchain pass completed (format -> lint -> type-check -> test) | PASS | Black/Ruff/Pyright/Pytest all green at HEAD `a45a987` (EXIT 0). The cycle-3 RED-suite caveat is resolved. |
| Import button disabled until a schema is selected; re-disables on placeholder | PASS | B1 wiring tests assert Import stays disabled and dropdown stays on `<Choose Schema>` when no file/worksheet is selected. |
| Activating a source tab auto-selects best-matching schema; placeholder when none | PASS | `test_ac2_full_match_through_build_application_auto_selects_and_enables` (auto-select) + B1 tests (placeholder). |
| Edit-schema action loads an existing schema into the builder and re-saves | PASS | `test_edit_load_modify_save_round_trips`; unchanged this cycle. |
| "New from template" action seeds a new schema from the closest existing one | PASS | `new_from_template` wired via `_schema_open_helpers.py:159`; `_on_partial_match` at `app.py:327-349`. |
| Schema Builder accepts required/optional column specs, default key pattern | PASS | Seeding tests; dialog integration tests. |
| Columns tab renders draggable source-column buttons from the selected sheet | PASS | Live Columns-tab dialog test; `DragTabBinder` at `schema_builder_dialog.py:98`. |
| Required/optional rows pre-populate via fuzzy matching; matched source consumed | PASS | Columns presenter/drag tests. |
| Matched source->canonical mapping persists as aliases; reload re-matches | PASS | Schema serialization/matching tests pass. |
| Activation-time matching runs first against persisted alias columns; partial path | PASS | Partial-match -> new-from-template path wired; `_on_partial_match` intact. |
| Matched columns show green check (coercible) or red X with failing example | PASS | dtype-check widget/tests pass. |
| Key tab supports drag-and-drop column parts plus repeatable Generic Text token | PASS | Live Key-tab dialog test. |
| Dedup defaults to aggregate mode with Key as discriminator; others by dropdown | PASS | Schema model/serialization tests; LE migrated to aggregate. |
| Derived tab precedes Columns; dialog creates derived rows; appear on Columns | PASS | Derived dialog test + `set_derived` mirror. The formula-engine `col`-shadow defect backing this flow is now fixed (C1 closed). |
| `ColumnSpec.expected_dtype` added; schema version bumped; forward migration | PASS | `tests/test_schema_migration.py`, `tests/test_schema_model.py` pass. |

### user-story.md

| AC | Verdict | Evidence |
|----|---------|----------|
| Import button disabled until a schema is selected | PASS | B1 wiring tests assert Import disabled when no selection. |
| Activating a source tab auto-selects best-matching schema | PASS | `test_ac2_full_match_through_build_application_auto_selects_and_enables`. |
| Placeholder shown when none matches | PASS | B1 tests assert `<Choose Schema>` placeholder; `test_on_schema_discovery_no_match_sets_placeholder`. |
| Edit-schema action loads an existing schema and re-saves | PASS | `test_edit_load_modify_save_round_trips`. |
| Schema Builder accepts required/optional column specs from the caller | PASS | Seeding tests. |
| Columns tab renders draggable source-column buttons | PASS | Live Columns-tab dialog test. |
| Required/optional rows pre-populate via fuzzy matching | PASS | Columns presenter tests. |
| Matched source column consumed (removed from pool, cannot re-match) | PASS | Columns drag/presenter tests. |
| Matched columns show green check (coercible) or red X | PASS | dtype-check widget/tests. |
| Failing example value shown when not coercible | PASS | dtype-check tests. |
| Key tab supports drag-and-drop column parts plus repeatable Generic Text token | PASS | Live Key-tab dialog test. |
| Caller-supplied default key pattern is parsed onto the tab | PASS | `test_seed_from_caller_pre_lists_rows_and_parses_key`. |
| Dedup defaults to aggregate mode with Key as discriminator | PASS | Schema model tests. |
| Other columns selectable via dropdown only | PASS | Schema model/serialization tests. |
| Derived tab precedes Columns; dialog creates derived rows | PASS | Derived dialog test. |
| Derived columns appear on Columns tab | PASS | `test_live_derived_button_adds_column_to_columns_tab`. |

## Acceptance Criteria Check-off

No check-off changes required: all 22 spec AC and all 16 user-story AC were already `[x]` from prior cycles and remain valid. Cycle 4 fixed the latent formula-engine defect (C1) that backs the derived-column / formula-validation criteria; it reverted no criterion to `[ ]` and added no feature surface. Each checked item is backed by a passing integrated test at HEAD `a45a987`. The cycle-3 toolchain caveat is resolved, so no AC carries an out-of-scope caveat this cycle.

### Acceptance Criteria Status
- Source: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md`, `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/user-story.md`
- Total AC items: 38 (22 spec + 16 user-story)
- Checked off (delivered): 38
- Remaining (unchecked): 0
- Items remaining: none

## Verdict

**PASS (0 blocking findings).** All 38 acceptance criteria are satisfied and backed by passing integrated tests at HEAD `a45a987`. The cycle-4 C1 fix closed the formula-engine `col`-shadowing defect, making the full suite green and resolving the only prior toolchain caveat; the toolchain-pass criterion is now PASS. Prior R1–R6 wiring, B1/B2 guards, schema model/migration, and AC-2 auto-selection are all intact with no regression. No FAIL or blocking-PARTIAL AC findings. This is the final cycle.
