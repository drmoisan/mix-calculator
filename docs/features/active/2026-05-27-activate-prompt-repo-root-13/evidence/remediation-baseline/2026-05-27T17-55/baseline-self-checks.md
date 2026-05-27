# Remediation Baseline — activate.ps1 (Issue #13, R-1/R-2)

- Timestamp: 2026-05-27T17-55
- Work Mode: minor-audit
- Scope files:
  - scripts/dev-tools/activate.ps1 (production, 326 lines)
  - tests/scripts/dev-tools/activate.Tests.ps1 (test)
- Note: Canonical PoshQC MCP gate and local PoshQC scripts/runsettings are not
  available in this agent session. Baseline below is captured with local
  PSScriptAnalyzer and local Pester. Canonical PoshQC/PSScriptAnalyzer/Pester are
  deferred to the orchestrator.

## Baseline — PSScriptAnalyzer (local)

- Command: `Invoke-ScriptAnalyzer -Path 'scripts/dev-tools/activate.ps1' -Recurse` and same for the test file
- EXIT_CODE: 0
- Output Summary: 0 findings on `scripts/dev-tools/activate.ps1`; 0 findings on `tests/scripts/dev-tools/activate.Tests.ps1`.

## Baseline — Pester with coverage (local)

- Command:
  ```
  $cfg = New-PesterConfiguration
  $cfg.Run.Path = 'tests/scripts/dev-tools/activate.Tests.ps1'
  $cfg.CodeCoverage.Enabled = $true
  $cfg.CodeCoverage.Path = 'scripts/dev-tools/activate.ps1'
  $cfg.CodeCoverage.OutputFormat = 'JaCoCo'
  Invoke-Pester -Configuration $cfg
  ```
- EXIT_CODE: 0
- Output Summary: 27 passed, 0 failed, 0 skipped (total 27). Command coverage
  86.36% (38/44). JaCoCo LINE counter: covered 36, missed 4, total 40 = 90.00%
  line coverage. Pester v5 JaCoCo output emits no BRANCH counter; branch coverage
  is not directly measurable from Pester output.

## Canonical coverage artifact state (R-1 finding confirmed)

- `artifacts/pester/powershell-coverage.xml` exists but contains only
  `.claude/hooks/*` sourcefiles; zero entries for `scripts/dev-tools/activate.ps1`.
- Verified via grep: only `check-powershell-test-purity.ps1`,
  `check-python-test-purity.ps1`, `enforce-powershell-batch-budget.ps1`,
  `enforce-python-batch-budget.ps1`, `validate-bash.ps1` are present.
