# Coverage Delta / Threshold Verification

Timestamp: 2026-06-17T15-28
Sources compared:
- Baseline: evidence/baseline/baseline-pytest.md
- Post-change: evidence/qa-gates/final-pytest.md

## Totals

| Metric | Baseline | Post-change | Delta |
|---|---|---|---|
| Statements | 5031 | 5057 | +26 |
| Statements missed | 46 | 46 | 0 |
| Line coverage | 99.1% | 99.1% | +0.0 |
| Branches | 932 | 942 | +10 |
| Branch partial | 55 | 57 | +2 |
| Branch coverage | 94.1% | 94.0% | -0.1 |
| Tests passed | 1058 | 1070 | +12 |

Thresholds: line >= 85% (met, 99.1%); branch >= 75% (met, 94.0%).

## Changed / new-code coverage (touched files)

| File | Line coverage | Notes |
|---|---|---|
| src/_schema_model_specs.py | 100% | located_by_name field added; fully covered |
| src/schema_serialization.py | 98% | located_by_name serialize; only pre-existing line 416 partial |
| src/_schema_migration.py (new) | 100% | extracted object_to_column + migration seeding |
| src/_schema_loader_keepset.py (new) | 95% | keep-set helpers; 2 partial branches, no missed lines |
| src/_schema_loader_helpers.py | 92% | loader decouple; missed lines pre-existing/unrelated to changed logic |

## Verdict

No coverage regression on changed lines: every changed/new module is at or above
the 85% line threshold (95%-100% for the new modules). The 0.1-point branch-total
movement reflects 10 newly added branches in new code, 8 of which are covered; the
overall branch coverage (94.0%) remains far above the 75% floor. All values are
numeric and measured. Outcome: PASS.
