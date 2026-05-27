# Coverage Evidence — activate.ps1 (Issue #13, R-1)

- Timestamp: 2026-05-27T18-13
- Work Mode: minor-audit
- Scope file under coverage: `scripts/dev-tools/activate.ps1`
- Coverage artifact (this folder): `activate-coverage.jacoco.xml`

## Command

```powershell
Import-Module Pester -MinimumVersion 5.0.0
$cfg = New-PesterConfiguration
$cfg.Run.Path = 'tests/scripts/dev-tools/activate.Tests.ps1'
$cfg.Run.PassThru = $true
$cfg.CodeCoverage.Enabled = $true
$cfg.CodeCoverage.Path = 'scripts/dev-tools/activate.ps1'
$cfg.CodeCoverage.OutputFormat = 'JaCoCo'
$cfg.CodeCoverage.OutputPath = '<this folder>/activate-coverage.jacoco.xml'
Invoke-Pester -Configuration $cfg
```

- EXIT_CODE: 0

## Measured Coverage on `scripts/dev-tools/activate.ps1`

- Pester command coverage: 97.67% (42/43 commands executed; 1 missed).
- JaCoCo LINE counter: covered 38, missed 1, total 39 = 97.44% line coverage (>= 85% gate: PASS).
- The single missed line is line 321 (`Invoke-VenvActivation -ScriptRoot $PSScriptRoot`),
  the entrypoint call. The test imports only the script's `FunctionDefinitionAst`
  nodes via `[System.Management.Automation.Language.Parser]::ParseFile`, so the
  entrypoint statement is never executed. This is the intended seam; the entrypoint
  orchestration body (`Invoke-VenvActivation`) is itself fully covered (8/8 lines).
- Branch coverage: Pester v5's JaCoCo emitter does not produce per-line BRANCH
  counters (all `cb`/`mb` values are 0), so branch coverage is not directly
  measurable from this artifact. Command coverage (97.67%) is the closest
  branch-sensitive proxy available from Pester and exceeds the 75% gate. All
  decision branches in the pure functions are exercised by dedicated test cases
  (at-root / descendant / outside-tree / sibling-prefix / case-insensitive for the
  prompt builder; direct-hit / multi-level walk / nearest-ancestor / no-match for
  the resolver; empty / null venv for the venv-aware decision).

## Tier and Gate Context

- Tier: T4 (dev tooling). Uniform thresholds apply: line >= 85%, branch >= 75%.
- Line coverage 97.44% on the changed file satisfies the line gate.

## Canonical Artifact Note (R-1 scope)

- The repo-canonical artifact `artifacts/pester/powershell-coverage.xml` was NOT
  modified. It belongs to the canonical `drm-copilot` MCP gate, which the
  orchestrator re-runs. This dev-tools-scoped artifact persists the
  changed-file coverage evidence required by AC7 under the feature evidence folder.
