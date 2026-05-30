# QA Gate — Coverage Delta and New-Code Thresholds (Issue #41)

Timestamp: 2026-05-30T07-25
Command: `poetry run pytest --cov=src.schema_model --cov=src.schema_serialization --cov=src._schema_json_helpers --cov=src.schema_settings --cov=src.schema_registry --cov-branch --cov-report=term-missing`
EXIT_CODE: 0

## Baseline vs Post-Change (whole repository)

| Metric | Baseline (P0-T5) | Post-change (P7-T4) |
|---|---|---|
| Line coverage (TOTAL) | 99.26% (2295 stmts, 17 missed) | 99.31% (2612 stmts, 18 missed) |
| Branch coverage (TOTAL) | 98.88% (356 br, 4 partial) | 98.90% (456 br, 5 partial) |
| Tests passed | 510 | 578 |

No regression: overall line and branch coverage did not decrease; no changed line
regressed coverage (the feature is additive, and all new modules are covered).

## New-Code Coverage (focused per-module run)

| Module | Line | Branch | Threshold met |
|---|---|---|---|
| src/schema_model.py | 100% (113/113) | 100% (48/48) | yes (>= 85% / >= 75%) |
| src/schema_serialization.py | 100% (66/66) | 100% (4/4) | yes |
| src/_schema_json_helpers.py | 98% (69/70, miss line 160) | 98% (37/38) | yes |
| src/schema_registry.py | 100% (47/47) | 100% (6/6) | yes |
| src/schema_settings.py | 100% (21/21) | 100% (4/4) | yes |
| TOTAL (new modules) | 99% (316/317) | 99% (99/100) | yes |

Output Summary: New-code line coverage 99% and branch coverage 99% both exceed the
>= 85% line / >= 75% branch thresholds for every new module. Overall coverage shows
no regression from baseline. Result: PASS.

The single uncovered line (`_schema_json_helpers.py:160`) is a defensive type-guard
inside the optional-int accessor that is not reachable through the public parse path
exercised by the suite; all error paths consumed by the schema shape are covered.
Module line/branch coverage remains 98%/98%, above the thresholds.
