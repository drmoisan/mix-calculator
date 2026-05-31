---
name: powershell-measure-object-line-undercount
description: PowerShell `Measure-Object -Line` undercounts vs wc -l/awk NR; always cross-check file-size-cap evidence with awk NR before trusting it.
metadata:
  type: feedback
---

The repo's `phase4/file-sizes.md` evidence command `(Get-Content <path> | Measure-Object -Line).Lines` undercounts lines compared to `wc -l` and `awk 'END{print NR}'`. On issue #46, it reported `src/gui/app.py = 439` when the actual count was 503 — concealing an AC-12 (500-line cap) violation.

**Why:** `Measure-Object -Line` counts line-terminator characters and drops trailing-newline-less partial lines; the policy enforcement tools use `wc -l`-equivalent counting.

**How to apply:** Whenever a feature audit cites a `phase*/file-sizes.md` artifact attesting AC-12 PASS, re-run `awk 'END{print NR}' <each-changed-production-file>` directly before trusting the verdict. If any file is within 100 lines of the cap by the PowerShell number, re-measure; if within 50 lines, treat the PowerShell number as suspect.

Recommended commands for evidence regeneration:
- PowerShell: `(Get-Content <path>).Count`
- Bash/WSL: `wc -l <path>`
- awk: `awk 'END{print NR}' <path>`

Related: [[issue2-file-size-watch]] (similar pattern, normalize-le tests).
