# Remediation Closure — Issue #13 (minor-audit)

- Date: 2026-05-27
- Author: orchestrator
- Source findings: `remediation-inputs.2026-05-27T13-44.md`, `code-review.2026-05-27T13-44.md`
- Feature-review verdict being closed: Conditional Go (0 Blocking findings)

## Findings and disposition

### R-2 (Major, non-blocking) — test-only switch in production code — CLOSED
- Required: remove the `ACTIVATE_PS1_SUPPRESS_SIDEEFFECTS` branch from `scripts/dev-tools/activate.ps1`; import functions in the test via AST extraction.
- Verified on disk by orchestrator:
  - `grep ACTIVATE_PS1_SUPPRESS_SIDEEFFECTS` over `scripts/dev-tools/activate.ps1` and `tests/scripts/dev-tools/activate.Tests.ps1`: absent from both.
  - Test imports via `[System.Management.Automation.Language.Parser]::ParseFile` selecting `FunctionDefinitionAst` nodes.
  - Entrypoint retains the non-dot-source guard and `Invoke-VenvActivation -ScriptRoot $PSScriptRoot`.
  - `activate.ps1` now 321 lines (was 326), under the 500-line limit.

### R-1 (non-blocking) — canonical coverage excluded activate.ps1 — CLOSED
- Required: persist a dev-tools-scoped coverage artifact that includes the file.
- Verified on disk by orchestrator:
  - `evidence/qa-gates/2026-05-27T18-13/activate-coverage.jacoco.xml` present, plus `activate-coverage-note.md`.
  - Measured (worker local run, JaCoCo): line 97.44% (38/39) >= 85%; command proxy 97.67% (42/43) >= 75%. The single uncovered line is the entrypoint call the AST import intentionally does not execute.
  - The global `artifacts/pester/powershell-coverage.xml` was intentionally not overwritten (it belongs to the broader canonical gate).

## Canonical MCP gate re-verification (post-remediation files)

Run by orchestrator 2026-05-27 against `scripts/dev-tools` and `tests/scripts/dev-tools`:
- `run_poshqc_format`: ok
- `run_poshqc_analyze`: ok (0 findings)
- `run_poshqc_test`: ok

## Acceptance criteria

AC1–AC8 satisfied. AC7 now fully met (deterministic AST-import tests + persisted coverage evidence above thresholds). AC8 re-verified on the post-remediation files.

## Note on worker reporting

The remediating worker described both changes as "already applied by a prior session." That framing is inaccurate — no prior session applied them (the earlier delegation was rejected before running). The substantive outcome is nonetheless correct and was verified independently by the orchestrator rather than accepted on the worker's account.

## Status

Ready to merge pending the user's decision to commit and open a PR. No CI gate (S9) has run because the change is currently untracked on `chore/env-activation` (branch HEAD equals merge-base with `main`).
