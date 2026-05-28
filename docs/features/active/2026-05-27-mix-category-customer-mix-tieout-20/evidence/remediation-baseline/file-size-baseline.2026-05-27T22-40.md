# File Size Baseline (Pre-Remediation)

Timestamp: 2026-05-27T22-40

Command: `pwsh -NoProfile -Command "(Get-Content tests/test_mix_rollups.py).Count"`

EXIT_CODE: 0

Output Summary:
- `tests/test_mix_rollups.py`: 562 lines (wc -l semantics)
- Policy threshold (`.claude/rules/general-code-change.md` File Size Limit): 500
- Verdict: FAIL — file exceeds threshold by 62 lines. Matches the upstream Finding 1 measurement in `remediation-inputs.2026-05-27T22-34.md`.
