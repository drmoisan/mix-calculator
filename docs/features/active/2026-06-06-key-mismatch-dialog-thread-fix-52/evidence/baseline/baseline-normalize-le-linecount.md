# Baseline — normalize_le.py line count (P0-T2)

Timestamp: 2026-06-06T11-41

Command: (Get-Content src/normalize_le.py).Count

EXIT_CODE: 0

Output Summary:
Physical line count reported by PowerShell `(Get-Content).Count` = 495.
(The plan anticipated 496; PowerShell does not count the trailing final newline
as a separate line, so the measured controlling value is 495.) Headroom to the
500-line cap = 5 lines. This confirms the Phase 2 `resolver` addition to
`load_source` must be done by EXTRACTION into `src/_normalize_le_columns.py`
rather than in-place addition (AC-7).
