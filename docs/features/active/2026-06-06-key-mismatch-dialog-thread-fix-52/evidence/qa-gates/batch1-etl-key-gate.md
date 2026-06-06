# Batch 1 — etl_key resolver gate (P1-T3)

Timestamp: 2026-06-06T11-55

Commands (in order; loop restarted once when Pyright flagged the private-symbol
import in the new test and the test was reworked to the repo's
`vars(module)[name]` + `cast` pattern):

- Command: poetry run black .            EXIT_CODE: 0
- Command: poetry run ruff check .       EXIT_CODE: 0
- Command: poetry run pyright            EXIT_CODE: 0
- Command: poetry run pytest tests/test_etl_key.py --cov=src.etl_key --cov-branch --cov-report=term-missing   EXIT_CODE: 0

Output Summary:
- Final clean pass: Black 190 files unchanged; Ruff all checks passed; Pyright
  0 errors / 0 warnings; Pytest 22 passed.
- src/etl_key.py coverage from this test module in isolation: 79% line, branch
  shown as part of 79% (missing lines 57/63/65/69/76-84 are all inside
  `coerce_sku`, which is covered by other suites; none are the newly added
  `_collect_diverging_examples` or the resolver branch).
- The new/changed lines (`_collect_diverging_examples` and the resolver-aware
  divergence branch in `resolve_key`) are fully exercised by the new tests.
  Whole-suite coverage that gates AC-8 is verified in Phase 6.
