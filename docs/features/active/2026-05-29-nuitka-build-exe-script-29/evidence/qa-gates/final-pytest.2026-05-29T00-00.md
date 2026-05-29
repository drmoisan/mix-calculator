# Final QA — Pytest + Coverage

Timestamp: 2026-05-29T00-00
Command: `env -u VIRTUAL_ENV poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0

Output Summary:
- Overall headline: `430 passed in 19.23s` (0 failures).
- Per-module headline for `src/build_exe.py`: `31 stmts, 1 miss, 4 branches, 0 BrPart`,
  line coverage **97%**, branch coverage **100%** (4/4 branches fully covered; 0 partial).
  Only missing line is 138 (the body of `_dist_nuitka_exists`, which is monkeypatched in
  every test that exercises the clean branch). Both thresholds (line >= 85%, branch >= 75%)
  are satisfied for `src/build_exe.py`.
- TOTAL row: `1985 stmts, 15 miss, 300 branches, 2 BrPart`, line **99%**, branch ~99%.
- 13 new tests in `tests/test_build_exe.py` are part of the 430 total (baseline was 417;
  delta = +13 tests, all passing).
