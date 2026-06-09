# Phase 2 — Quality Gate

Timestamp: 2026-06-08T14-30

Phase 2 routed `import_aop` through the schema-driven path. The production change
necessarily invalidated three stale `src.load_aop.load_aop` monkeypatch sites in
GUI tests (the Phase 3 audit targets), which Phase 3 re-targeted at the schema
path. The four-stage toolchain below was run after the Phase 2 production change
plus the Phase 3 stale-patch re-targeting so the full suite passes in one pass.

## Stage 1 — Format
Command: poetry run black .
EXIT_CODE: 0
Output Summary: 231 files left unchanged (Phase 2/3 edits already format-clean after iterative black runs).

## Stage 2 — Lint
Command: poetry run ruff check .
EXIT_CODE: 0
Output Summary: All checks passed. Zero lint errors; no new suppressions.

## Stage 3 — Type check
Command: poetry run pyright
EXIT_CODE: 0
Output Summary: 0 errors, 0 warnings, 0 informations.

## Stage 4 — Test + Coverage
Command: poetry run pytest --cov --cov-branch --cov-report=term-missing
EXIT_CODE: 0
Output Summary:
- 998 passed, 0 failed, 3 warnings in ~34s.
- TOTAL combined coverage: 98%.
- Statements: 4785 total, 44 missed -> line coverage = (4785-44)/4785 = 99.08%.
- Branches: 894 total, 54 partial -> branch coverage = (894-54)/894 = 93.96%.
- src/gui/pipeline_service.py: 85 stmts, 0 missed, 0 branch partial -> 100%.
- src/schema_loader.py: 32 stmts, 0 missed, 6 branch, 0 partial -> 100%.

## File-size finding (deferred to P4-T6 contingency, as planned)
- src/gui/pipeline_service.py: 550 lines after the import_aop rewrite — exceeds the
  500-line cap. The plan's P4-T6 contingency directs extracting the AOP schema-load/
  header-detect logic into src/gui/_aop_schema_import.py. This extraction is performed
  at P4-T6 and re-verified by the final QA loop.

Thresholds met: line >= 85% and branch >= 75%. No regression on changed lines.
