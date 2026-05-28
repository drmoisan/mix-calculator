# QA Gate — 500-Line File-Size Limit Check

Timestamp: 2026-05-27T20-52
Command: line counts via `grep -c "" <file>`
EXIT_CODE: 0

## New and changed production / test files

| File | Lines | <= 500 |
|---|---|---|
| `src/mix_bottomsup.py` (new) | 403 | yes |
| `src/_mix_bottomsup_helpers.py` (new) | 192 | yes |
| `src/mix_pipeline_run.py` (changed) | 119 | yes |
| `tests/test_mix_bottomsup.py` (new) | 442 | yes |
| `tests/mix_bottomsup_fixtures.py` (new) | 293 | yes |
| `tests/test_mix_pipeline.py` (changed) | 273 | yes |

Output Summary: All new and changed production and test files are within the 500-line
limit. The largest is `tests/test_mix_bottomsup.py` at 442 lines; the test fixtures
and expected-column constants were factored into `tests/mix_bottomsup_fixtures.py` to
keep the test module under the limit (the established `*_fixtures.py` repo convention).
