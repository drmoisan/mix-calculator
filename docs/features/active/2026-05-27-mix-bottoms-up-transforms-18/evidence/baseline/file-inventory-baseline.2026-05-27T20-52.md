# Baseline — In-Scope File Inventory and Line Counts

Timestamp: 2026-05-27T20-52

## Existing in-scope files (current line counts)

| File | Lines |
|---|---|
| `src/mix_pipeline_run.py` | 98 (per editor; `wc -l` reports 97 due to no counted trailing newline) |
| `quality-tiers.yml` | 48 |
| `README.md` | 136 |
| `tests/test_mix_pipeline.py` | 270 |
| `tests/test_mix_rollups.py` | 338 (fixture-pattern source) |

## New files (confirmed absent at baseline)

- `src/mix_bottomsup.py` — does not exist.
- `src/_mix_bottomsup_helpers.py` — does not exist.
- `tests/test_mix_bottomsup.py` — does not exist.

Output Summary: All in-scope existing files are well under the 500-line limit; the three
new files do not yet exist. Baseline confirmed for the later 500-line check.
EXIT_CODE: 0
