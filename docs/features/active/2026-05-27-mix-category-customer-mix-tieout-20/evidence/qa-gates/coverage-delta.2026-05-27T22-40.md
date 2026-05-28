# Coverage Delta (Baseline vs Post-Split)

Timestamp: 2026-05-27T22-40

Command: `env -u VIRTUAL_ENV poetry run pytest --cov=src --cov-branch --cov-report=term-missing`

EXIT_CODE: 0

Policy thresholds (`.claude/rules/quality-tiers.md`): line >= 85%, branch >= 75%.

Output Summary:

| File | Baseline Line | Baseline Branch | Post-Split Line | Post-Split Branch |
| --- | --- | --- | --- | --- |
| `src/mix_rollups.py` | 100% | 100% (n/a — 0 branches) | 100% | 100% (0 branches) |
| `src/_mix_rollups_helpers.py` | 100% | 100% (n/a — 0 branches) | 100% | 100% (0 branches) |
| `src/mix_pipeline_run.py` | 100% | 100% (n/a — 0 branches) | 100% | 100% (0 branches) |
| TOTAL (project) | 100% | 100% | 100% | 100% |

Baseline source: `evidence/remediation-baseline/pytest-baseline.2026-05-27T22-40.md`.
Post-split source: `evidence/qa-gates/pytest-final.2026-05-27T22-40.md`.

Delta: no regression on changed lines. This remediation modified only test files (`tests/test_mix_rollups.py`, `tests/test_mix_rollups_tieout.py`, `tests/_mix_rollups_fixtures.py`); no `src/**` line was changed. Production coverage is identical to baseline.

Verdict: PASS. Every post-split coverage value is at or above the baseline value; both thresholds are met.
