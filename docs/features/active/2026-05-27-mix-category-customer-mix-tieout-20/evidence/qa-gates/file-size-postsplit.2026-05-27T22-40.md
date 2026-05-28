# File Size Post-Split

Timestamp: 2026-05-27T22-40

Command: `pwsh -NoProfile -Command 'Get-ChildItem tests/test_mix_rollups.py,tests/test_mix_rollups_tieout.py,tests/_mix_rollups_fixtures.py | ForEach-Object { [pscustomobject]@{ Path=$_.FullName; Lines=(Get-Content $_.FullName).Count } }'`

EXIT_CODE: 0

Output Summary:

| Path | Lines |
| --- | --- |
| `tests/test_mix_rollups.py` | 204 |
| `tests/test_mix_rollups_tieout.py` | 167 |
| `tests/_mix_rollups_fixtures.py` | 216 |

Threshold: 500

Verdict: PASS. Every file is at or under the 500-line File Size Limit defined in `.claude/rules/general-code-change.md`.

## Post-Toolchain Verification

Timestamp: 2026-05-27T22-40

Command: `pwsh -NoProfile -Command 'Get-ChildItem tests/test_mix_rollups.py,tests/test_mix_rollups_tieout.py,tests/_mix_rollups_fixtures.py | ForEach-Object { [pscustomobject]@{ Path=$_.FullName; Lines=(Get-Content $_.FullName).Count } }'`

EXIT_CODE: 0

| Path | Lines |
| --- | --- |
| `tests/test_mix_rollups.py` | 204 |
| `tests/test_mix_rollups_tieout.py` | 167 |
| `tests/_mix_rollups_fixtures.py` | 225 |

Note: `_mix_rollups_fixtures.py` grew from 216 to 225 lines after the toolchain loop required an `__all__` declaration (see `pyright-final.2026-05-27T22-40.md`). All three files remain at or under the 500-line threshold.

Threshold: 500

Verdict: PASS.

