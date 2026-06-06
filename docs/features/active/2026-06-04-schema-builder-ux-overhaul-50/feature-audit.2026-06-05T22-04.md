# Feature Audit: schema-builder-ux-overhaul (Issue #50) — Remediation Cycle 2 EXIT Reaudit

**Audit Date:** 2026-06-05
**Timestamp:** 2026-06-05T22-04
**Branch:** `feature/schema-builder-ux-overhaul-50` | **Base:** `main` | **Head:** `fd8a022` | **Merge-base:** `5e659f2`
**Work Mode:** full-feature (AC sources: `spec.md` AND `user-story.md`)
**Scope:** full branch diff `main...HEAD`; cycle-2 delta `7b8994c..fd8a022`

## Scope and Baseline

- Baseline: `main` (merge-base `5e659f2`). Head: `fd8a022`. Audit scope is the full branch diff `main...HEAD`; the cycle-2 remediation delta is `7b8994c..fd8a022`.
- AC baseline: the 22 spec.md and 16 user-story.md criteria established for the feature; this reaudit confirms none regressed relative to that baseline.

## Summary

Cycle 2 changed no product features: it split an over-cap test file (B1) and adjusted coverage config (N4). No acceptance criterion is affected by these changes. The cycle-1 feature behavior (R1–R6 wiring) remains intact and integration-tested, and the full suite passes (932 tests) at HEAD `fd8a022`. All 22 spec AC and all 16 user-story AC remain backed by passing integrated tests; none are checked `[x]` without proof.

## Acceptance Criteria Inventory

- AC source files: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md` (22 checkboxes) and `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/user-story.md` (16 checkboxes).
- spec.md: 22 total, 22 checked `[x]`, 0 unchecked.
- user-story.md: 16 total, 16 checked `[x]`, 0 unchecked.
- No phantom criteria added; no criterion text modified.

## Acceptance Criteria Evaluation

### spec.md

| AC | Verdict | Evidence |
|----|---------|----------|
| Acceptance criteria documented and mapped to tests or demos | PASS | spec/user-story AC mapped to integrated tests (Appendix A of cycle-2 policy audit). |
| Behavior matches acceptance criteria in all documented environments | PASS | 932 tests pass under `QT_QPA_PLATFORM=offscreen`. |
| Tests updated/added (unit/integration as applicable) | PASS | Cycle-1 integrated tests retained; cycle-2 split preserved all presenter tests. |
| Edge cases and error handling covered by tests | PASS | Partial-match, no-match, blank menu path, unknown discriminator, invalid formula covered. |
| Docs updated (README, docs links) | PASS | Feature docs and evidence tree under canonical path. |
| Bundled default schemas migrated forward and load without error | PASS | `tests/test_default_schemas.py` + `tests/test_schema_migration.py` pass. |
| No real workbook values or proprietary column names committed (masking scan) | PASS | `scan_masked_fixtures.py` clean; schema JSON holds canonical metadata only. |
| Toolchain pass completed (format -> lint -> type-check -> test) | PASS | Black/Ruff/Pyright/Pytest all green at HEAD `fd8a022`. |
| Import button disabled until a schema is selected; re-disables on placeholder | PASS | Import-gate tests pass. |
| Activating a source tab auto-selects best-matching schema; placeholder when none | PASS | `test_on_schema_discovery_no_match_sets_placeholder` + activation tests. |
| Edit-schema action loads an existing schema into the builder and re-saves | PASS | `test_load_existing_renders_schema_into_view`, `test_edit_load_modify_save_round_trips` (now in `_core`). |
| "New from template" action seeds a new schema from the closest existing one | PASS | `test_new_from_template_seeds_clears_name` (now in `_seeding`); R5 wired at `_schema_open_helpers.py:159`. |
| Schema Builder accepts required/optional column specs, default key pattern | PASS | Seeding tests in `_seeding`; dialog integration tests. |
| Columns tab renders draggable source-column buttons from the selected sheet | PASS | `test_live_columns_tab_has_drag_tokens_and_dtype_indicators`; R1 wired at `_schema_builder_tabs.py:186`. |
| Required/optional rows pre-populate via fuzzy matching; matched source consumed | PASS | Columns presenter/drag tests (`_columns_tab_presenter.py` 93%, `_columns_tab_drag.py` 95%). |
| Matched source->canonical mapping persists as aliases; reload re-matches | PASS | Schema serialization/matching tests pass. |
| Activation-time matching runs first against persisted alias columns; partial path | PASS | `test_build_application_partial_match_reaches_new_from_template`; R6 wired at `app.py:335/342/349`. |
| Matched columns show green check (coercible) or red X with failing example | PASS | `_dtype_check_widget.py` + dtype-check tests (`test_dtype_check.py`). |
| Key tab supports drag-and-drop column parts plus repeatable Generic Text token | PASS | `test_live_key_tab_has_drag_widget_with_seeded_parts`; R2 wired at `_schema_builder_tabs.py:206`. |
| Dedup defaults to aggregate mode with Key as discriminator; others by dropdown | PASS | Schema model/serialization tests; LE migrated to aggregate. |
| Derived tab precedes Columns; dialog creates derived rows; appear on Columns | PASS | `test_live_derived_button_adds_column_to_columns_tab`; R3 wired via shared open path. |
| `ColumnSpec.expected_dtype` added; schema version bumped; forward migration | PASS | `tests/test_schema_migration.py`, `tests/test_schema_model.py` pass; schema `version: "2.0"`. |

### user-story.md

| AC | Verdict | Evidence |
|----|---------|----------|
| Import button disabled until a schema is selected | PASS | Import-gate tests. |
| Activating a source tab auto-selects best-matching schema | PASS | Activation/discovery tests. |
| Placeholder shown when none matches | PASS | `test_on_schema_discovery_no_match_sets_placeholder`. |
| Edit-schema action loads an existing schema and re-saves | PASS | `test_edit_load_modify_save_round_trips`. |
| Schema Builder accepts required/optional column specs from the caller | PASS | Seeding tests. |
| Columns tab renders draggable source-column buttons | PASS | Live Columns-tab dialog test. |
| Required/optional rows pre-populate via fuzzy matching | PASS | Columns presenter tests. |
| Matched source column consumed (removed from pool, cannot re-match) | PASS | Columns drag/presenter tests. |
| Matched columns show green check (coercible) or red X | PASS | dtype-check widget/tests. |
| Failing example value shown when not coercible | PASS | dtype-check tests. |
| Key tab supports drag-and-drop column parts plus repeatable Generic Text token | PASS | Live Key-tab dialog test. |
| Caller-supplied default key pattern is parsed onto the tab | PASS | `test_seed_from_caller_pre_lists_rows_and_parses_key` (now in `_seeding`). |
| Dedup defaults to aggregate mode with Key as discriminator | PASS | Schema model tests. |
| Other columns selectable via dropdown only | PASS | Schema model/serialization tests. |
| Derived tab precedes Columns; dialog creates derived rows | PASS | Derived dialog test. |
| Derived columns appear on Columns tab | PASS | `test_live_derived_button_adds_column_to_columns_tab`. |

## Acceptance Criteria Check-off

No check-off changes required: all 22 spec AC and all 16 user-story AC were already `[x]` from the cycle-1 exit and remain valid (cycle 2 changed no features). Each checked item is backed by a passing integrated test, as enumerated above. No item is checked without proof; no item required reverting to `[ ]`.

### Acceptance Criteria Status
- Source: `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/spec.md`, `docs/features/active/2026-06-04-schema-builder-ux-overhaul-50/user-story.md`
- Total AC items: 38 (22 spec + 16 user-story)
- Checked off (delivered): 38
- Remaining (unchecked): 0
- Items remaining: none

## Verdict

**PASS.** All acceptance criteria are satisfied and backed by passing integrated tests at HEAD `fd8a022`. The cycle-2 remediation (test split + coverage-omit) introduced no feature regression; R1–R6 wiring is intact. No FAIL or blocking-PARTIAL AC findings.
