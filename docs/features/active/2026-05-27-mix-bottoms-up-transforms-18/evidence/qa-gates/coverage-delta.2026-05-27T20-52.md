# QA Gate — Coverage Delta and Threshold Verification

Timestamp: 2026-05-27T20-52

## Baseline (Phase 0, `pytest-coverage-baseline.2026-05-27T20-52.md`)

- Overall line coverage: 100% (881 statements, 0 missed).
- Overall branch coverage: 100% (192 branches, 0 partial).
- Tests: 185 passed.

## Post-change (Phase 5, `pytest-coverage-final.2026-05-27T20-52.md`)

- Overall line coverage: 100% (981 statements, 0 missed).
- Overall branch coverage: 100% (196 branches, 0 partial).
- Tests: 204 passed (19 new).

## New / changed-code coverage

| Module | Line % | Branch % |
|---|---|---|
| `src/mix_bottomsup.py` (new) | 100% | 100% |
| `src/_mix_bottomsup_helpers.py` (new) | 100% | 100% |
| `src/mix_pipeline_run.py` (changed) | 100% | 100% |

## Threshold check (uniform T1–T4: line >= 85%, branch >= 75%)

- Overall line 100% >= 85%: PASS.
- Overall branch 100% >= 75%: PASS.
- New-module line >= 85% and branch >= 75%: PASS (100%/100%).
- No regression on changed lines: PASS (baseline 100% line/branch, post-change 100%
  line/branch; the changed `mix_pipeline_run.py` lines are fully covered).

Output Summary: All coverage thresholds met with no regression. Overall and
new/changed-code coverage are 100% line and 100% branch. Outcome: PASS.
EXIT_CODE: 0
