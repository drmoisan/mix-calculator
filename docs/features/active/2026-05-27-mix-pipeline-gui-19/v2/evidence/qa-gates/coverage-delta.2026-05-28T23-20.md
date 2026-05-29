Timestamp: 2026-05-28T23-20

# Coverage Delta — Cycle 1 Remediation

## Measured points (read from on-disk evidence)

- **v2 execution baseline** (source: `v2/evidence/baseline/pytest-coverage.2026-05-28T22-10.md`)
  - Tests: 333 passed, 0 failed
  - Line coverage (TOTAL): 100% (1793 statements, 0 missed)
  - Branch coverage (TOTAL): 100% (262 branches, 0 partial)

- **Cycle-1 baseline** (source: `v2/evidence/baseline/baseline.2026-05-28T23-20.md`, pytest section)
  - Tests: 416 passed, 0 failed
  - Line coverage (TOTAL): 99% (1956 statements, 14 missed)
  - Branch coverage (TOTAL): 99% (296 branches, 2 partial)

- **Post-remediation** (source: `v2/evidence/qa-gates/final-pytest-coverage.2026-05-28T23-20.md`)
  - Tests: 417 passed, 0 failed (the cycle adds one new positive test
    `test_build_application_uses_injected_exporter_registry`)
  - Line coverage (TOTAL): 99% (1954 statements, 14 missed)
  - Branch coverage (TOTAL): 99% (296 branches, 2 partial)

## Deltas

| Comparison | Line % | Branch % | Tests passed |
|---|---|---|---|
| v2 execution baseline -> Cycle-1 baseline | 100% -> 99% | 100% -> 99% | 333 -> 416 (+83) |
| Cycle-1 baseline -> Post-remediation | 99% -> 99% (no change) | 99% -> 99% (no change) | 416 -> 417 (+1) |
| v2 execution baseline -> Post-remediation | 100% -> 99% | 100% -> 99% | 333 -> 417 (+84) |

## Threshold check

- Repository-wide line coverage >= 85%: **met** (99%).
- Repository-wide branch coverage >= 75%: **met** (99%).

## Changed-lines no-regression check

- `src/gui/app.py`: 100% line / 100% branch (the new `exporter_registry`
  branch is exercised by the new positive test). No regression.
- `src/gui/presenters/pipeline_presenter.py`: 99% line / 95% branch. The
  removed `set_imported_tables_for_test` body is no longer counted (statement
  count dropped by 2). No regression on the changed surface.
- `tests/gui/integration/test_behavioral_dialogs.py`: 100% (test file
  coverage; rewritten CSV test is exercised once per run).
- `tests/gui/integration/test_behavioral_pipeline_run.py`: 100% (test file).
- `tests/gui/test_app_wiring.py`: 100% (test file).

## Interpretation

The 1-percentage-point drop between the v2 execution baseline and the
cycle-1 baseline is the consequence of v2's own merge (v2's execution
baseline was taken before later merges added the `src/gui/runners.py`
`ThreadedRunner` callback path; that path is the dominant source of the 14
uncovered lines and is exercised in production rather than the
`SynchronousRunner` tests). It is not introduced by this cycle's diff;
cycle-1 baseline and post-remediation are identical at the percentage level.

If any required coverage value were unavailable the outcome would be
remediation-required; all values were captured and are above the gates.
