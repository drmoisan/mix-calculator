# Phase 8 — coverage no-regression delta

Timestamp: 2026-05-29T10-15

Command: comparison of `evidence/baseline/pytest-cov.2026-05-29T10-15.md` vs `evidence/qa-gates/p8-pytest-cov.2026-05-29T10-15.md`

EXIT_CODE: 0

Output Summary:
- Baseline (Phase 0) total: 457 tests; 99% line; 2124 statements / 14 missed; 322 branches / 1 partial.
- Post-change (Phase 8) total: 488 tests; 99% line; 2229 statements / 16 missed; 348 branches / 3 partials.
- Delta tests: +31 (build_velopack 30 + app_composition velopack-ordering 1).
- Delta statements: +105 (built from new build_velopack.py 91 statements + bootstrap helper 5 statements + app.py velopack call edits).
- New-code coverage on `src/build_velopack.py`: 98% line (Stmts 91, Miss 1); branch coverage 23/24 reached (~95.8%).
- New-code coverage on `src/gui/_velopack_bootstrap.py`: 100% line (Stmts 5, Miss 0). All statements reached by the GUI composition tests via the patched `velopack.App` factory.
- New-code coverage on `src/gui/app.py` (modified portion): the added `run_velopack_bootstrap()` call is exercised by both `test_main_entry_point_runs_event_loop` and `test_main_calls_velopack_app_run_before_qapplication`.
- No-regression assertion: total project line coverage stayed at 99% (baseline 99%); branch coverage held; no previously-passing test now fails.
- AC15 satisfied: line on `src/build_velopack.py` 98% >= 85%; branch 95.8% >= 75%.
