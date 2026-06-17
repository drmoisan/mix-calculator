# Final QA — Coverage Delta and No-Regression on Changed Lines

Timestamp: 2026-06-17T13-10

## Totals

| Metric | Baseline | Post-change | Delta |
|---|---|---|---|
| Line coverage | 99.08% (5016 stmts, 46 missed) | 99.09% (5031 stmts, 46 missed) | +0.01 pp |
| Branch coverage | 94.10% (932 branches, 55 partial) | 94.10% (932 branches, 55 partial) | 0.00 pp |
| Tests passed | 1049 | 1058 | +9 |

Both thresholds satisfied: line >= 85%, branch >= 75%.

## Changed-module coverage (in-scope production files)

| Module | Line | Branch | Notes |
|---|---|---|---|
| src/schema_model.py | 100% | 100% | New `required_output_columns()` fully covered. |
| src/_schema_model_specs.py | 100% | 100% | Docstring-only edits; coverage unchanged. |
| src/schema_serialization.py | 98% | 88% | Only line 486 missed (pre-existing `key` malformed-shape error path). |

## No-regression on changed lines

- The new code in `src/schema_serialization.py` (the `_version_predates_required_output` helper including its `except ValueError` legacy branch, and the `migrated_required = parsed_required and in_output if migrate_required else parsed_required` mapping) is fully covered by the migration tests in `tests/test_schema_migration.py` (2.0 drop-when-not-emitted, 2.0 stay-when-emitted, 3.0 pass-through, 3.0 round-trip stable, and unparseable-version-treated-as-legacy).
- The only uncovered line in the changed module (486) is the pre-existing `key`-shape error path that was already uncovered at baseline (reported at line 421 before this work shifted line numbers). No previously-covered line became uncovered.

## Outcome

PASS — post-change line and branch coverage meet thresholds; no regression on changed lines.
