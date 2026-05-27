# Phase 6 — Toolchain QA Gate (Issue #9)

Timestamp: 2026-05-26T20-00
Scope: `src/mix_pipeline.py`, `src/mix_pipeline_run.py`, `tests/test_mix_pipeline.py`.

Command: `poetry run black .`
EXIT_CODE: 0
Output Summary: PASS. 37 files left unchanged.

Command: `poetry run ruff check .`
EXIT_CODE: 0
Output Summary: PASS. All checks passed; 0 errors; no suppressions.

Command: `poetry run pyright`
EXIT_CODE: 0
Output Summary: PASS. 0 errors, 0 warnings, 0 informations (strict).

Command: `poetry run pytest --cov --cov-branch --cov-report=term-missing`
EXIT_CODE: 0
Output Summary: PASS. 185 passed. Line coverage TOTAL 100%; branch coverage 100%. `mix_pipeline.py` 100%/100%, `mix_pipeline_run.py` 100%/100%. No regression on changed lines.

File-size check: `mix_pipeline.py` 250, `mix_pipeline_run.py` 97, `test_mix_pipeline.py` 270 — all <= 500.

Confidentiality: only fabricated values appear (Acme Foods, Master Group, SKU-001/002, Widget A/B, Category X/Y, PPG-1, US/Canada). No runtime temp files: the workbook is an in-memory BytesIO and the database is a shared `sqlite3.connect(":memory:")` connection.

Implementation notes:
- `main(argv=None) -> int` follows the `argparse` pattern of `load_aop.main`; arguments `--input`/`--output` (required), `--le-sheet` (default "LE-8 + 4"), `--aop-sheet` (default "AOP1"), `--skulu-input` (default = --input), `--skulu-sheet` (default "SKU_LU").
- `main` orchestrates only: it reuses `normalize_le`, `load_aop`, `load_skulu` for the imports, reads the import tables back via `src.pandas_io.read_table`, runs the transforms in topological order (the steps 9-19 chain runs in `src/mix_pipeline_run.run_transforms`), and persists each derived table via `src.pandas_io.write_table` with `if_exists="replace"`. `mix_rollup_4` is persisted as a single-row single-column `{value: float}` table.
- `main` returns 0 on success and 1 on a loader `ValueError`; the integration test verifies all 21 tables (2 import + 19 derived) exist and the customer-layer rollup ties out to the scalar `mix_rollup_4` within 1e-9.
- Deviation: the steps 9-19 chain was factored into `src/mix_pipeline_run.py` (mirroring the `_load_aop_helpers.py` split) so `mix_pipeline.py` stays under 500 lines and keeps `main` free of transform logic.
