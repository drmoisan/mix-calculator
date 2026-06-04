# Coverage Delta — Baseline vs Post-change (P5-T5)

Timestamp: 2026-06-01T23-31

## Headline totals

| Metric | Baseline (P0-T5) | Post-change (P5-T4) |
|---|---|---|
| baseline line % | 99.47% (3787 stmts, 20 missed) | n/a |
| baseline branch % | 96.59% (674 branch, 23 partial) | n/a |
| post-change line % | n/a | 99.47% (3804 stmts, 20 missed) |
| post-change branch % | n/a | 96.61% (678 branch, 23 partial) |

- Tests: 801 passed (baseline) -> 811 passed (post-change); +10 tests, 0 failures.
- Both line (>= 85%) and branch (>= 75%) thresholds remain satisfied.

## Per-changed-file no-regression

- src/schema_registry.py: baseline 100% line / 100% branch (47 stmts / 6 branch)
  -> post-change 100% line / 100% branch (54 stmts / 8 branch). No regression; the
  new union helper, union listing, and load fallback are fully covered.
- src/gui/_schema_list_wiring.py: new module; post-change 100% line / 100% branch
  (7 stmts / 2 branch). No prior baseline (new code) and fully covered.
- src/gui/app.py: baseline (pre-change) covered to 99% in the full suite; post-change
  99% line / branch (137 stmts, 1 missed = line 299; 10 branch, 1 partial). The only
  uncovered line (299) is the pre-existing fresh-QApplication construction branch,
  not a line added by this change. The added import and the single
  populate_schema_lists call site are covered by tests/gui/test_app_wiring_schema_list.py.

## Conclusion

No regression on changed lines for src/schema_registry.py, src/gui/_schema_list_wiring.py,
or src/gui/app.py. All added production lines are exercised by new tests; overall line
and branch coverage are unchanged within rounding and remain above policy thresholds.
