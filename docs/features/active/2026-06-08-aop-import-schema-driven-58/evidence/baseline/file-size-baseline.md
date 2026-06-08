# Baseline — Production File Line Counts

Timestamp: 2026-06-08T14-30
Command: wc -l (the three in-scope production files)

| File | Lines | Under 500 cap |
|---|---|---|
| src/schemas/default_aop.schema.json | 357 | yes |
| src/schema_loader.py | 223 | yes |
| src/gui/pipeline_service.py | 493 | yes (7 lines headroom) |

Note: src/gui/pipeline_service.py is at 493 lines with only 7 lines of headroom. P4-T6 contingency
(extract src/gui/_aop_schema_import.py) applies if Phase 2 edits push it over 500.
