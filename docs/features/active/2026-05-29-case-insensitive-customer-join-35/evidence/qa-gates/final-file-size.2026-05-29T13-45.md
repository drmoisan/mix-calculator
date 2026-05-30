# Final QC — File sizes

Timestamp: 2026-05-29T13-45
Command: `wc -l src/mix_lookups.py tests/test_mix_lookups.py tests/test_mix_lookups_casefold.py tests/test_mix_pipeline.py`
EXIT_CODE: 0

Output Summary:
- `src/mix_lookups.py`: 286 lines (baseline 220; +66 from `_customer_join_key` helper, `build_customer_lu` whitespace-strip, `build_aop_norm`/`build_le_norm` whitespace-strip, and `build_aop_vs_le` casefolded pivot rework with WARNING-tagged intent comments). Under 500-line cap.
- `tests/test_mix_lookups.py`: 365 lines (baseline 360; +5 for a pointer comment to the casefold tests). Under cap.
- `tests/test_mix_lookups_casefold.py`: 296 lines (NEW; case-insensitive Customer join tests split out from `test_mix_lookups.py` so both files remain under the 500-line cap). Under cap.
- `tests/test_mix_pipeline.py`: 301 lines (baseline 274; +27 for the new `test_mix_pipeline_nrr_summary_check_ok` smoke test added in Phase 4 P4-T2). Under cap.

All four files satisfy AC9 (under 500-line cap).
