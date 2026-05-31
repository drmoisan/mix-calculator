# Remediation Baseline — src/gui/app.py Line Count (Triple Counter)

- Timestamp: 2026-05-31T02-43
- Command:
  - `wc -l src/gui/app.py`
  - `awk 'END{print NR}' src/gui/app.py`
  - `pwsh -NoProfile -Command "(Get-Content 'src/gui/app.py').Count"`
- EXIT_CODE: 0
- Output Summary:
  - `wc -l` -> `503`
  - `awk 'END{print NR}'` -> `503`
  - `(Get-Content ...).Count` -> `503`
  - All three counters agree at 503 lines. Over the 500-line cap by 3 lines, consistent with remediation-inputs.2026-05-31T02-43.md and the R1 finding. Remediation by P2 (extract crash-handler bootstrap).
