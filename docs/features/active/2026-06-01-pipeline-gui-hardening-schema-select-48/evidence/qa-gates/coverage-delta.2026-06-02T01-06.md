# Coverage Delta — Baseline vs Post-change (Cycle 2, Issue #48)

Timestamp: 2026-06-02T01-06

## Headline TOTAL coverage

| Metric | Baseline (P0-T5) | Post-change (P4-T4) |
|---|---|---|
| Line coverage % | 99% (3804 stmts, 20 missed) -> 99.47% | 99.48% (3830 stmts, 20 missed) |
| Branch coverage % | 96.6% (678 branches, 23 partial) | 96.63% (682 branches, 23 partial) |
| Tests passed | 811 | 818 (+7) |

Both thresholds remain satisfied: line >= 85%, branch >= 75%.

## Per-changed-file no-regression

### src/gui/runners.py
- Baseline (P0-T6): 100% line, 100% branch (46 stmts).
- Post-change (P4-T4): 100% line, 100% branch (61 stmts, 0 missed; 2 branches, 0 partial).
- Conclusion: NO REGRESSION. The added lifecycle/await_active code is fully covered. The single defensive Qt-object-lifetime recovery branch (the `except RuntimeError` in `await_active`) is excluded with `# pragma: no cover`; forcing it deterministically requires deleting a live C++ QThread (shiboken6.delete), which aborts the interpreter.

### src/gui/_shutdown_wiring.py (new this cycle)
- Post-change (P4-T4): 100% line, 100% branch (9 stmts, 0 missed; 2 branches, 0 partial).
- Conclusion: NO REGRESSION (new file at full coverage, including the no-op degradation path for a runner without `await_active`).

### src/gui/app.py
- Post-change (P4-T4): 99% line (139 stmts, 1 missed — line 297, the pre-existing QApplication-singleton fallback branch that predates this cycle and was not modified); 1 pre-existing branch partial.
- The lines changed this cycle (the `wire_shutdown_cleanup` import and call site) are covered by the build_application composition tests.
- Conclusion: NO REGRESSION on changed lines. Line 297 was not introduced or altered by this cycle.

## Overall conclusion
No coverage regression on any changed file. Aggregate line and branch coverage are at or above baseline and both exceed the repository thresholds.
