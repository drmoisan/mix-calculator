# Coverage Delta Verification (Issue #43)

Timestamp: 2026-05-30T09-22

## Baseline (P0-T5)
- Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
- Baseline total line coverage: 99.21% (2768 stmts, 22 missed).
- Baseline total branch coverage: 97.86% (514 branches, 11 partial).
- Baseline tests: 604 passed.

## Post-change (P5-T3)
- Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
- Post-change total line coverage: 99.01% (3026 stmts, 30 missed).
- Post-change total branch coverage: 96.44% (618 branches, 22 partial).
- Post-change tests: 669 passed (+65).

## Delta
- Total line: 99.21% -> 99.01% (-0.20 pp). The small dip reflects 258 new
  statements and 104 new branches added by the feature, of which a handful of
  defensive guard branches in the private helper modules are not exercised. The
  total remains far above the 85% line / 75% branch floors, and no previously
  covered line regressed (all pre-existing modules remain at their prior
  coverage; see the per-module table in the final-pytest-coverage artifact).
- Total branch: 97.86% -> 96.44% (-1.42 pp), same cause; still above 75%.

## New/changed-code coverage (per module)
| Module | Line % | Branch % | Meets >= 85% / >= 75% |
|---|---|---|---|
| src/schema_formula.py | 100% | 100% | yes |
| src/schema_loader.py | 100% | 100% | yes |
| src/_schema_formula_helpers.py | 95% | 89% | yes |
| src/_schema_loader_helpers.py | 96% | 84% | yes |

## Outcome
PASS. Every new module meets line >= 85% and branch >= 75% (AC10). The overall
total remains above both floors and no changed line regressed below the prior
coverage. All required coverage values are numeric (no placeholders).
