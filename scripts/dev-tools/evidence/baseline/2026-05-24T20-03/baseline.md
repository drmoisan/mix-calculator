# Baseline — Initialize-DevEnvironment dev-tooling change

Timestamp: 2026-05-24T20-03

## Scope (in-scope files)

- Production: `scripts/dev-tools/Initialize-DevEnvironment.ps1` (does not exist yet)
- Test: `tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1` (does not exist yet)

## Tool availability

Command: `pwsh -NoProfile -Command '$PSVersionTable.PSVersion'`
EXIT_CODE: 0
Output Summary: PowerShell 7.6.0 available. Pester 5.6.1 and PSScriptAnalyzer 1.24.0 available locally.

## PoshQC MCP gates

Command: `mcp__drm-copilot__run_poshqc_format` / `..._analyze` / `..._test`
EXIT_CODE: UNVERIFIED
Output Summary: The PoshQC MCP tools are not present in the agent tool set, and the
repo has no `scripts/powershell/PoshQC/settings/pester.runsettings.psd1`. The PoshQC
gates cannot be executed in this environment. The toolchain is instead run directly via
`pwsh` + PSScriptAnalyzer + Pester, and the PoshQC-specific gates are marked UNVERIFIED.

## Baseline PSScriptAnalyzer (in-scope files)

Command: `Invoke-ScriptAnalyzer` on in-scope files
EXIT_CODE: N/A
Output Summary: No in-scope PowerShell files exist prior to this change. Baseline findings = 0.

## Baseline Pester (in-scope files)

Command: `Invoke-Pester` on in-scope test file
EXIT_CODE: N/A
Output Summary: No in-scope test file exists prior to this change. Baseline tests = 0, failures = 0.

## Baseline coverage (in-scope files)

EXIT_CODE: N/A
Output Summary: No in-scope PowerShell files exist prior to this change. Baseline coverage = N/A (new file).
