# Post-change local self-check — fix activate.ps1 repo-root resolution and prompt

Timestamp: 2026-05-27T17-39
Work Mode: minor-audit (bug, dev tooling, T4)
Scope (production): scripts/dev-tools/activate.ps1
Scope (test): tests/scripts/dev-tools/activate.Tests.ps1

## Toolchain Availability Note

The canonical MCP QA gate (`mcp__drm-copilot__run_poshqc_format`,
`mcp__drm-copilot__run_poshqc_analyze`, `mcp__drm-copilot__run_poshqc_test`) is NOT
available in this worker session, and the repo PoshQC tooling/runsettings directory
(`scripts/powershell/PoshQC`) is not present in this checkout. Per the orchestrator's
division of labor, the canonical gate (and AC8) is DEFERRED TO ORCHESTRATOR.

The results below are LOCAL, NON-CANONICAL self-checks using locally installed tools:
- PowerShell 7.6.0
- PSScriptAnalyzer 1.24.0 (default rule set; no repo PSScriptAnalyzerSettings.psd1 found)
- Pester 5.6.1

## PSScriptAnalyzer (local, default rules)

Command: Invoke-ScriptAnalyzer -Path .\scripts\dev-tools\activate.ps1
EXIT_CODE: 0
Output Summary: activate.ps1: 0 findings.

Command: Invoke-ScriptAnalyzer -Path .\tests\scripts\dev-tools\activate.Tests.ps1
EXIT_CODE: 0
Output Summary: activate.Tests.ps1: 0 findings.

Note: an initial run flagged PSUseBOMForUnicodeEncodedFile (two em-dashes in the doc
comment) and PSReviewUnusedParameter (an always-false probe). Both were corrected; the
re-run is clean.

## Pester (local, with coverage on the production file)

Command: Invoke-Pester -Configuration <Run.Path=tests/scripts/dev-tools/activate.Tests.ps1; CodeCoverage.Enabled; CodeCoverage.Path=scripts/dev-tools/activate.ps1>
EXIT_CODE: 0
Output Summary: 27 passed, 0 failed, 0 skipped. Line/command coverage 86.36% (38/44),
above the 85% target. The 6 uncovered commands are the irreducible side-effect lines:
the dot-source inside the Invoke-VenvActivateScript wrapper (intentionally mocked to avoid
executing a real Activate.ps1) and the 5 entrypoint commands skipped under the test
suppression guard (the non-dot-source Write-Error branch and the Invoke-VenvActivation
call). All pure logic and orchestration branches are covered.

Branch coverage (manual analysis; Pester command coverage is the available proxy): every
conditional in the testable units is exercised — Resolve-RepoRoot (found-at-start /
found-after-walk / not-found-exhausts and the parent==current break), Get-RepoRelativePrompt
(at-root / descendant / outside-tree), Get-VenvAwarePrompt (empty-or-null / set),
Test-IsDotSourced (true / false), Invoke-VenvActivation (no-root throw / missing-activate
throw / success). This meets the >= 75% branch target on changed code.

## Regression check (sibling dev-tools suites)

Command: Invoke-Pester -Configuration <Run.Path=tests/scripts/dev-tools>
EXIT_CODE: 0
Output Summary: 107 passed, 0 failed, 0 skipped across the three dev-tools test files
(activate, Initialize-DevEnvironment, run-actionlint). No regressions.

## Behavioral verification (defect fixed)

Command: . .\scripts\dev-tools\activate.ps1 ; prompt ; (cd .claude) prompt
EXIT_CODE: 0
Output Summary:
- prompt at repo root: "(mix-calculator)> "
- prompt inside .claude: "(mix-calculator)\.claude> "
The previously-thrown "venv missing at <repoRoot>\scripts\.venv\..." error no longer
occurs; the repo root is now resolved by walking ancestors to the first containing .venv.

Command: & .\scripts\dev-tools\activate.ps1   (run WITHOUT dot-source)
EXIT_CODE: 1
Output Summary: Surfaces corrective guidance ("activate.ps1 must be dot-sourced ...",
including the correct command ". .\scripts\dev-tools\activate.ps1") via Write-Error under
$ErrorActionPreference='Stop'. It does not silently activate in a discarded child scope.

## QA Gate Status

- PoshQC format: DEFERRED TO ORCHESTRATOR (unverified by worker).
- PSScriptAnalyzer (repo PoshQC settings): DEFERRED TO ORCHESTRATOR (unverified by worker).
  Local default-rule run: 0 findings on both files.
- Pester (repo runsettings via MCP): DEFERRED TO ORCHESTRATOR (unverified by worker).
  Local run: 27 passed / 0 failed; 86.36% line coverage on changed file.
- AC8: left unchecked for orchestrator to verify against the canonical gate.
