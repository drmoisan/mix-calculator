# Pass-After Evidence (Issue #20, AC2/AC4/AC6)

Timestamp: 2026-05-27T22-17

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Output Summary:
The full Python toolchain completed in a single clean pass after the Phase 2 fix:
- Black: `poetry run black .` — 40 files left unchanged (no reformat).
- Ruff: `poetry run ruff check .` — All checks passed (0 errors). The TC002 finding for the now type-only `pandas` import in `src/_mix_rollups_helpers.py` was resolved by moving the import under `if TYPE_CHECKING:`.
- Pyright: `poetry run pyright` — 0 errors, 0 warnings, 0 informations.
- Pytest: 201 passed, 0 failed. Overall line coverage 100% (985 statements, 0 missed); overall branch coverage 100% (202 branches, 0 partial).

The Phase 1 expect-fail regression tests now PASS (confirmed via `-k "single_scenario or full_aggregation_minus_rollup"`):
- `test_category_layer_retains_single_scenario_volume` — PASS
- `test_customer_layer_retains_single_scenario_volume` — PASS
- `test_layer_mix_equals_full_aggregation_minus_rollup` — PASS

Per-module coverage for in-scope files (post-change):
- `src/mix_rollups.py`: 59 statements, 0 missed, 0 branch — 100% line / 100% branch.
- `src/_mix_rollups_helpers.py`: 30 statements, 0 missed, 0 branch — 100% line / 100% branch (statement count dropped from 49 to 30 after removing `unstack_to_long`).
- `src/mix_pipeline_run.py`: 22 statements, 0 missed, 0 branch — 100% line.
