# Phase 3 — Legacy CLI AOP Path Untouched (P3-T5)

Timestamp: 2026-06-08T14-30

## Inspection / grep result

Command: git diff HEAD -- src/load_aop.py src/_load_aop_helpers.py src/mix_pipeline.py
EXIT_CODE: 0
Output Summary: Empty diff. None of the legacy CLI AOP files were modified relative to the baseline HEAD (63522c00).

## Symbol presence confirmation

- `src/load_aop.py` `main` — present at line 351 (unchanged).
- `validate_aop` — imported (line 57) and invoked in the loader's validation path (line 287); re-exported in `__all__` (line 92). Defined in `src/_load_aop_helpers.py` (unchanged).
- `build_per_row_checks` — imported (line 52) and used to build the per-row identity map (line 264). Defined in `src/_load_aop_helpers.py` (unchanged).
- `coerce_numeric` and `clean_label_sentinels` in `src/_load_aop_helpers.py` — unchanged; still consumed by `SchemaLoader._coerce_and_clean`.

## CLI wiring confirmation

- `src/mix_pipeline.py` line 120: `aop_frame = load_aop.load_aop(args.input, sheet=args.aop_sheet)` — the CLI `_import_sources` path still calls `load_aop.load_aop`, unchanged. The schema-driven routing applies only to the GUI `PipelineService.import_aop` import path (Scope 1B).

Conclusion: the legacy arithmetic-validating CLI AOP path is unchanged (non-goals honored).
