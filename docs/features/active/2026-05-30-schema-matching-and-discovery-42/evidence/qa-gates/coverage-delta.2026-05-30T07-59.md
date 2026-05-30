# Coverage Delta Verification (baseline vs post-change vs new code)

Timestamp: 2026-05-30T07-59

## Inputs
- Baseline (P0-T5): `evidence/baseline/pytest-baseline.2026-05-30T07-05.md`
- Post-change (P5-T4): `evidence/qa-gates/pytest-final.2026-05-30T07-59.md`
- New-code (P5-T5): `evidence/qa-gates/newcode-coverage.2026-05-30T07-59.md`

## Total coverage
| Metric | Baseline | Post-change |
|---|---|---|
| Tests passed | 578 | 604 (+26 new) |
| Statements | 2612 | 2768 |
| Line coverage TOTAL | 99% (~18 missed) | 99% (22 missed) |
| Branches | 456 (5 partial) | 514 (11 partial) |

- No regression: total line coverage held at 99% after the additive change.
  The feature added 156 new statements and 26 tests; the new statements are
  covered to 95% line / ~90% branch, so the repository total did not drop.

## New / changed-code coverage (AC7 thresholds: >= 85% line, >= 75% branch)
| Module | Line cov | Branch cov | Verdict |
|---|---|---|---|
| `src/etl_column_probe.py` | 100% | 100% | PASS |
| `src/schema_matching.py` | 95% | ~86% | PASS |
| `src/_schema_matching_helpers.py` | 86% | 80% | PASS |

## No regression on changed lines
- All changes are additive: three new production modules and five new test
  modules. No existing production line was modified (see P5-T7 protected-files
  diff), so there are no changed lines in existing modules to regress.

## Verdict
PASS — total coverage shows no regression (99% -> 99%), and every new module
meets both the >= 85% line and >= 75% branch thresholds. All required numeric
values are present.
