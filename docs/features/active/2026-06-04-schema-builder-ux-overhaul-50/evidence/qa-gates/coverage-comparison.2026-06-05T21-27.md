# Coverage Comparison vs Cycle-2 Baseline (Cycle 2, P2-T6)

Timestamp: 2026-06-05T21-27
Command: compare P0-T5 baseline (baseline-pytest.2026-06-05T21-27.md) against P2-T4
post-change (final-pytest.2026-06-05T21-27.md); both run
`env -u VIRTUAL_ENV QT_QPA_PLATFORM=offscreen poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0

## Figures

| Metric | Cycle-2 baseline (P0-T5) | Post-change (P2-T4) | Threshold | Status |
|---|---|---|---|---|
| Statements | 4671 | 4653 | — | -18 (omitted protocol stmts) |
| Missed statements | 62 | 44 | — | -18 |
| Line coverage | (4671-62)/4671 = 98.67% | (4653-44)/4653 = 99.05% | >= 85% | PASS |
| Branches | 850 | 850 | — | unchanged |
| Partial branches | 51 | 51 | — | unchanged |
| Branch coverage | (850-51)/850 = 93.99% | (850-51)/850 = 93.99% | >= 75% | PASS |
| Tests | 932 passed | 932 passed | — | unchanged |

## Changed-code coverage (this cycle)

This cycle changes no production behavior. The only edits are:
- The B1 test-file split (test files are excluded from coverage measurement via the
  pre-existing `tests/*` omit entries), and
- The N4 coverage-config change: reverting the no-op `# pragma: no cover` lines in the
  two type-only protocol modules and adding those two modules to
  `[tool.coverage.run].omit`.

No measured source line was added or modified, so there is no changed-source-line
coverage to regress. The 18-statement / 18-missed reduction in the TOTAL row is
exactly the two omitted protocol modules (10 + 8 = 18 statements, all previously
counted as missed).

## Protocol-module absence confirmation

Both `src/gui/_columns_tab_protocol.py` and `src/gui/_key_tab_protocol.py` no longer
appear as rows in the per-file coverage report; the baseline reported each at 0%
(10/10 and 8/8 missed). They are now omitted via `[tool.coverage.run].omit`. This
closes N4 (0%-covered rows removed) without weakening any measured coverage.

## No-regression on changed lines

No previously-covered source line regressed. Line coverage increased
(98.67% -> 99.05%) and branch coverage held exactly (93.99% -> 93.99%).

## Verdict

PASS. Line >= 85% and branch >= 75% hold; the two protocol modules are absent from the
coverage report; no changed line regressed.
