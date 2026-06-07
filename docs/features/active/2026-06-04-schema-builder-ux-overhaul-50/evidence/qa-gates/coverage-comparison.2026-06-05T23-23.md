# Coverage Comparison — Baseline vs Post-Change (Cycle 4 Remediation)

Timestamp: 2026-06-05T23-23

Thresholds (uniform, `.claude/rules/quality-tiers.md`): line >= 85%, branch >= 75%; no regression on changed lines.

## Overall (whole repository)

| Metric | Baseline (P0-T5) | Post-change (P2-T4) | Delta |
|---|---|---|---|
| Statements total | 4661 | 4664 | +3 (3 new covered prod lines) |
| Statements missed | 44 | 44 | 0 |
| Line coverage | 99.06% | 99.06% | 0.00% |
| Branches total | 856 | 856 | 0 |
| Branches partial | 51 | 51 | 0 |
| Branch coverage | 94.04% | 94.04% | 0.00% |
| Reported TOTAL | 98% | 98% | 0% |

## Targeted module `src/schema_formula.py`

| Metric | Baseline | Post-change |
|---|---|---|
| Statements | 52 (0 missed) | 55 (0 missed) |
| Line coverage | 100% | 100% |
| Branches | 20 (0 partial) | 20 (0 partial) |
| Branch coverage | 100% | 100% |

## Changed-code coverage

The fix added 3 production statements to `src/schema_formula.py` (`_build_symtable`
alias-loop-first restructuring plus three explicit whitelisted-callable bindings).
All changed lines are exercised; the module retains 100% line and 100% branch
coverage. The new regression test and the now-passing property test cover the
colliding-column path directly.

## Determination

PASS. Line coverage 99.06% (>= 85%), branch coverage 94.04% (>= 75%). No regression
on overall coverage and no regression on changed lines (targeted module remains
100%/100%). Changed-code coverage is complete.
