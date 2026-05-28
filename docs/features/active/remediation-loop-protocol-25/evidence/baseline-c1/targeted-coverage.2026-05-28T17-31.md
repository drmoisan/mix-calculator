# Cycle-1 Entry Baseline — Targeted Pester Coverage on `.claude/hooks/validate-orchestrator-output.ps1`

Timestamp: 2026-05-28T17-31
Command:
```powershell
Import-Module Pester
$cfg = New-PesterConfiguration
$cfg.Run.Path = 'tests/claude/hooks/validate-orchestrator-output.remediation-loop.Tests.ps1'
$cfg.Run.PassThru = $true
$cfg.CodeCoverage.Enabled = $true
$cfg.CodeCoverage.Path = '.claude/hooks/validate-orchestrator-output.ps1'
$cfg.CodeCoverage.OutputFormat = 'JaCoCo'
$cfg.CodeCoverage.OutputPath = 'artifacts/pester/targeted-cov-c1-baseline.xml'
$cfg.Output.Verbosity = 'None'
$r = Invoke-Pester -Configuration $cfg
```
EXIT_CODE: 0
Output Summary:
- Pester results: PassedCount=6, FailedCount=0, TotalCount=6.
- BRANCH (Pester `CommandsExecutedCount` / `CommandsAnalyzedCount`): 54 / 132 = 40.9%.
- JaCoCo `artifacts/pester/targeted-cov-c1-baseline.xml`, sourcefile `validate-orchestrator-output.ps1`:
  - LINE covered=32, missed=44, total=76 -> 42.10% (matches policy-audit Appendix A baseline of 42.1%).
  - INSTRUCTION covered=54, missed=78.
  - METHOD covered=2, missed=2.
- Both gate thresholds fail at cycle-1 entry: LINE 42.1% < 85% required; BRANCH 40.9% < 75% required.
- This baseline confirms the policy-audit measurement and establishes the starting point for Phase 2 coverage uplift.
