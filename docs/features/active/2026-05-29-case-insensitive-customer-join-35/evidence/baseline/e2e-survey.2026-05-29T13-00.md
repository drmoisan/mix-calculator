# Baseline — End-to-end test survey

Timestamp: 2026-05-29T13-00
Command: `Grep "LE v AOP Gross to Net Decomp" tests/` and `Grep "mix_pipeline.main" tests/`
EXIT_CODE: 0

SearchScope: `tests/`
SearchPatterns: `"LE v AOP Gross to Net Decomp"`, `"mix_pipeline.main"`, `"from src.mix_pipeline import main"`, `"from src import mix_pipeline"`
SearchResult:
- `tests/test_mix_pipeline.py` (uses `mix_pipeline.main` against an in-memory synthetic workbook; does NOT reference the canonical `artifacts/LE v AOP Gross to Net Decomp.xlsx`).
- No test file references the literal string `LE v AOP Gross to Net Decomp`.

Output Summary: No existing canonical-workbook test present. AC7 end-to-end will be satisfied by the existing in-memory integration test (`tests/test_mix_pipeline.py`) plus a new synthetic Winco/WINCO fixture added during Phase 1. Phase 4 will add a small in-memory smoke test that asserts the `nrr_summary.Check` shape on the in-memory pipeline run.
