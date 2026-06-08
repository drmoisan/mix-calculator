# Coverage Delta and Threshold Verification (P4-T5)

Timestamp: 2026-06-08T14-30

## Baseline vs post-change (whole repository)

| Metric | Baseline (P0-T6) | Post-change (P4-T4) | Delta |
|---|---|---|---|
| Tests passed | 987 | 998 | +11 |
| Line coverage | 99.08% (4730/4774) | 99.08% (4749/4793) | flat |
| Branch coverage | 93.96% (840/894) | 93.96% (840/894) | flat |

## Changed / new production code coverage

| File | Stmts | Missed | Branch | Partial | Line/Branch |
|---|---|---|---|---|---|
| src/schema_loader.py | 32 | 0 | 6 | 0 | 100% / 100% |
| src/gui/pipeline_service.py | 76 | 0 | 0 | 0 | 100% |
| src/gui/_aop_schema_import.py (new) | 17 | 0 | 0 | 0 | 100% |
| src/schemas/default_aop.schema.json | data-only | n/a | n/a | n/a | covered by parse/round-trip + parity tests |

## Threshold assertions

- Line coverage 99.08% >= 85% threshold: PASS.
- Branch coverage 93.96% >= 75% threshold: PASS.
- No regression on changed lines: PASS (every changed/new production module is at 100% line and branch coverage).

Outcome: PASS. All three thresholds met with numeric evidence.
