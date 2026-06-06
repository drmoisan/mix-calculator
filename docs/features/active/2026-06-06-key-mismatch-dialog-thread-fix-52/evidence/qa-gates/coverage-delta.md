# Coverage delta & file-size invariants (P6-T5, AC-7 + AC-8)

Timestamp: 2026-06-06T13-10

Command: compare Phase 0 baseline coverage (P0-T6) against final coverage (P6-T4),
plus the file-size enumeration from P5-T4.

EXIT_CODE: 0

Output Summary:

Coverage comparison (whole-repository TOTAL):
- Baseline (P0-T6): 818 tests; line 99.48% (3830 stmts, 20 missed);
  branch 96.63% (682 branches, 23 partial).
- Post-change (P6-T4): 834 tests; line 99.49% (3891 stmts, 20 missed);
  branch 96.70% (698 branches, 23 partial).
- Delta: line +0.01 pts; branch +0.07 pts. No regression. Both well above the
  policy floors (line >= 85%, branch >= 75%).

Changed-module new-code coverage:
- Every changed/added in-scope module is at 100% line and 100% branch except
  src/gui/app.py at 99% (one uncovered pre-existing fallback line 297, not a
  changed line). No regression on changed lines: all new logic
  (_collect_diverging_examples, the resolver-aware resolve_key branch,
  resolve_le_columns, the loader resolver pass-throughs, the example-aware seam
  and dialog, the cross-thread bridge, and the app wiring) is fully covered.

File-size compliance (cross-reference P5-T4; all <= 500):
- etl_key.py 313; normalize_le.py 450; _normalize_le_columns.py 166;
  load_aop.py 396; gui/pipeline_service.py 493; gui/_key_mismatch_seam.py 85;
  gui/_key_mismatch_dialog.py 159; gui/_key_mismatch_bridge.py 187;
  gui/app.py 500.

Verdict: PASS. Coverage thresholds met with no regression (AC-8); all
changed/added source files <= 500 lines (AC-7).
