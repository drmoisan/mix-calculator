# Post-remediation local self-check — activate.ps1 (Issue #13, R-1/R-2)

- Timestamp: 2026-05-27T18-13
- Work Mode: minor-audit (bug, dev tooling, T4)
- Scope (production): scripts/dev-tools/activate.ps1 (321 lines)
- Scope (test): tests/scripts/dev-tools/activate.Tests.ps1
- New evidence artifact (this folder): activate-coverage.jacoco.xml + activate-coverage-note.md

## Remediation status verified in the current working tree

- R-2 (remove test-only switch): COMPLETE. `scripts/dev-tools/activate.ps1`
  contains no `ACTIVATE_PS1_SUPPRESS_SIDEEFFECTS` block and no comment referencing
  it. A repo-wide grep finds the token only in the historical audit/remediation
  markdown (`code-review.2026-05-27T13-44.md`, `remediation-inputs.2026-05-27T13-44.md`),
  which document the prior state and are not edited. The test
  (`tests/scripts/dev-tools/activate.Tests.ps1`) imports function definitions via AST
  extraction (`[System.Management.Automation.Language.Parser]::ParseFile` then
  selecting `FunctionDefinitionAst` nodes and dot-sourcing only those bodies into the
  test scope), per `.claude/rules/powershell.md` Mocking Rules #4. The non-dot-source
  guard and the `Invoke-VenvActivation -ScriptRoot $PSScriptRoot` entrypoint call are
  intact (lines 316-321). The `global:prompt` save/restore for independence
  (`Restore-GlobalPrompt`, BeforeEach/AfterEach in two Describe blocks) is preserved.
- R-1 (persist canonical coverage evidence including activate.ps1): COMPLETE. Coverage
  XML scoped to the changed file is persisted in this folder; see activate-coverage-note.md.

## Toolchain Availability Note

The canonical MCP QA gate (`mcp__drm-copilot__run_poshqc_format`,
`mcp__drm-copilot__run_poshqc_analyze`, `mcp__drm-copilot__run_poshqc_test`) was
attempted but does not surface as a callable tool in this worker session, and the repo
PoshQC tooling/runsettings (`scripts/powershell/PoshQC`) is not present in this checkout.
Per the orchestrator division of labor, the canonical PoshQC/PSScriptAnalyzer/Pester gate
and AC8 are DEFERRED TO ORCHESTRATOR, which re-runs the canonical gate after delivery.
The results below are LOCAL, NON-CANONICAL self-checks using locally installed tools:
- PowerShell 7+ (pwsh)
- PSScriptAnalyzer (default rule set; no repo PSScriptAnalyzerSettings.psd1 found)
- Pester 5.6.1

## PSScriptAnalyzer (local, default rules)

- Command: `Invoke-ScriptAnalyzer -Path 'scripts/dev-tools/activate.ps1'`
- EXIT_CODE: 0
- Output Summary: 0 findings on `scripts/dev-tools/activate.ps1`.

- Command: `Invoke-ScriptAnalyzer -Path 'tests/scripts/dev-tools/activate.Tests.ps1'`
- EXIT_CODE: 0
- Output Summary: 0 findings on `tests/scripts/dev-tools/activate.Tests.ps1`.

- Findings delta vs. baseline (qa-gates/2026-05-27T17-39, remediation-baseline/2026-05-27T17-55):
  0 new findings.

## Pester (local, with coverage on the production file)

- Command:
  ```powershell
  $cfg = New-PesterConfiguration
  $cfg.Run.Path = 'tests/scripts/dev-tools/activate.Tests.ps1'
  $cfg.CodeCoverage.Enabled = $true
  $cfg.CodeCoverage.Path = 'scripts/dev-tools/activate.ps1'
  $cfg.CodeCoverage.OutputFormat = 'JaCoCo'
  Invoke-Pester -Configuration $cfg
  ```
- EXIT_CODE: 0
- Output Summary: 29 passed, 0 failed, 0 skipped (total 29). Command coverage 97.67%
  (42/43). JaCoCo LINE counter: covered 38, missed 1, total 39 = 97.44% line coverage.
  The single missed line is 321 (the entrypoint `Invoke-VenvActivation` call), which the
  AST import deliberately never executes. Pester v5 JaCoCo output emits no BRANCH counter;
  branch coverage is not directly measurable from Pester output (command coverage is the
  available proxy and exceeds 75%).
- Failing-tests delta vs. baseline: 0 new failures.
- Coverage delta vs. baseline: line coverage 97.44% now vs. baseline 86.36% command /
  90.00% JaCoCo-line at 2026-05-27T17-55; no regression on changed file.

## Regression check (dev-tools suite)

- Command: `Invoke-Pester -Configuration <Run.Path=tests/scripts/dev-tools>`
- EXIT_CODE: 0
- Output Summary: 109 passed, 0 failed, 0 skipped across the dev-tools test files
  (activate +2 since the prior 107). No regressions.

## QA Gate Status

- PoshQC format: DEFERRED TO ORCHESTRATOR (canonical gate not callable in this session).
- PSScriptAnalyzer (repo PoshQC settings): DEFERRED TO ORCHESTRATOR. Local default-rule
  run: 0 findings on both files.
- Pester (repo runsettings via MCP): DEFERRED TO ORCHESTRATOR. Local run: 29 passed /
  0 failed; 97.44% line coverage on the changed file.
- File size: activate.ps1 = 321 lines (< 500 limit).
- AC8: left unchecked for orchestrator to verify against the canonical gate.
