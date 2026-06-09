# File-Size Guard — Final (P4-T6)

Timestamp: 2026-06-08T14-30

The Phase 2 `import_aop` rewrite pushed `src/gui/pipeline_service.py` to 550 lines,
exceeding the 500-line cap. Per the planned P4-T6 contingency, the AOP
schema-load / header-detect / read / transform sequence was extracted into the
new private helper module `src/gui/_aop_schema_import.py`, and `import_aop`
delegates to it. The Phase 2 and Phase 4 gates were re-run after the extraction.

| File | Baseline (P0-T7) | Final | <= 500 cap |
|---|---|---|---|
| src/schemas/default_aop.schema.json | 357 | 294 | yes |
| src/schema_loader.py | 223 | 254 | yes |
| src/gui/pipeline_service.py | 493 | 500 | yes (at cap) |
| src/gui/_aop_schema_import.py (new) | n/a | 133 | yes |

All in-scope production files are at or under the 500-line cap.

Note on per-batch budget: the Phase 2 batch produced two production files
(`src/gui/pipeline_service.py` plus the new `src/gui/_aop_schema_import.py`),
within the 3-production-file per-batch budget.

Post-extraction re-run (final QA loop) results:
- black: EXIT 0 (no changes)
- ruff: EXIT 0 (all checks passed)
- pyright: EXIT 0 (0 errors)
- pytest: EXIT 0 (998 passed); pipeline_service.py and _aop_schema_import.py both 100% covered.
