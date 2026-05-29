# Coverage Delta — Baseline vs Post-Change

Timestamp: 2026-05-27T20-59

## Baseline (pre-feature)
Source: `evidence/baseline/pytest-coverage.2026-05-27T20-59.md`
- Tests: 185 passed
- Line coverage: 100% (881 stmts, 0 missed)
- Branch coverage: 100% (192 branches, 0 partial)

## Post-change (final QA loop)
Source: `evidence/qa-gates/final-pytest-coverage.2026-05-27T20-59.md`
- Tests: 279 passed (185 prior + 94 new across GUI suite)
- Line coverage: 100% (1538 stmts, 0 missed)
- Branch coverage: 100% (238 branches, 0 partial)

## New / changed-code coverage (`src/gui/**`)
Every new GUI module is at 100% line and 100% branch coverage. The 24 modules
under `src/gui/**` (657 new statements, 46 new branches) all measure 100%. No
new code is uncovered.

## Verdict
- Repository-wide gate: line 100% >= 85% PASS; branch 100% >= 75% PASS.
- No regression on changed lines: the pre-existing `src/` modules remain at 100%
  line / 100% branch, identical to the baseline.
- New-code coverage: 100% line / 100% branch on every `src/gui/**` module.
- Outcome: PASS (no remediation required).

## Method
Baseline values are taken directly from the Phase-0 baseline artifact (captured
on the developer workstation, the same environment as the post-change run).
Post-change values are from the final pytest run under
`QT_QPA_PLATFORM=offscreen` with `--cov --cov-branch --cov-report=term-missing`.
The new-code percentages are read directly from the per-module rows of the
post-change report; every `src/gui/**` row shows 100% / 100%.
