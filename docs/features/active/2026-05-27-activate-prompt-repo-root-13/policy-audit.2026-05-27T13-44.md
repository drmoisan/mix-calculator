# Policy Compliance Audit: activate-prompt-repo-root (Issue #13)

**Audit Date:** 2026-05-27
**Code Under Test:** scripts/dev-tools/activate.ps1 (new, 326 lines); tests/scripts/dev-tools/activate.Tests.ps1 (new, 246 lines)
**Work Mode:** minor-audit
**Base / merge-base:** ee129603facd5384d7f8cee6f75a84de67e78f0d (`main`)

**Coverage Metrics by Language:**

| Language | Files Changed | Tests | Test Result | Baseline Coverage | Post-Change Coverage | New Code Coverage |
|----------|--------------|-------|-------------|-------------------|---------------------|-------------------|
| PowerShell | 1 prod + 1 test | 27 (file) / 107 (suite) | PASS 107 pass, 0 fail (orchestrator) | N/A (new file) | 86.36% lines, 0% in canonical artifact | 86.36% line (worker self-check; not in canonical artifact) |

**Post-change coverage note:** The 86.36% line figure is the worker-measured value from a
targeted Pester run; the canonical artifact `artifacts/pester/powershell-coverage.xml`
reports 0% for the changed file because it does not include `scripts/dev-tools/activate.ps1`
at all (it covers only `.claude/hooks/*`). This is recorded as a FAIL on evidence
verification (see section 5).

**Scope note:** Branch HEAD equals the merge-base with `main`; the change is delivered as
untracked new files, so `git diff main` is empty. The audit treats the new files as
additions reviewed directly.

### Coverage Evidence Checklist

- TypeScript baseline coverage artifact: `N/A - out of scope` (no TypeScript files changed)
- TypeScript post-change coverage artifact: `N/A - out of scope` (no TypeScript files changed)
- PowerShell baseline coverage artifact: `N/A` (new file; no baseline)
- PowerShell post-change coverage artifact: `artifacts/pester/powershell-coverage.xml` — present but does NOT contain `scripts/dev-tools/activate.ps1` (covers only `.claude/hooks/*`)
- Per-language comparison summary: see section 1.2.1 and section 5

## Rejected Scope Narrowing

None detected. The caller brief identifies the same full set of changed files as the
branch-vs-base diff. No instruction attempted to narrow scope, mark a language out of
scope, or skip a required check.

## Evidence Location Compliance

A git-status scan of the new/untracked files for paths under `artifacts/baselines/`,
`artifacts/qa/`, `artifacts/evidence/`, or `artifacts/coverage/` found none. Feature
evidence is written under the canonical `<FEATURE>/evidence/<kind>/` location
(`evidence/baseline/2026-05-27T17-25/`, `evidence/qa-gates/2026-05-27T17-39/`). The
canonical validator `scripts/validate_evidence_locations.py` is absent in this checkout;
a git-status scan was used as the substitute. Result: PASS (no violations).

## Executive Summary

PowerShell coding standards and unit-test structural/determinism requirements are met. The
root-cause fix (depth-robust `Resolve-RepoRoot` replacing the fixed `Split-Path -Parent`
assumption) is correct. One separation-of-concerns finding exists: the production
entrypoint branches on a test-only environment variable. One coverage finding exists: the
canonical PowerShell coverage artifact does not include the changed file, so the reported
86.36% line coverage cannot be verified from the canonical evidence.

**Policy documents evaluated:**
- PASS `general-code-change.md`
- PASS `general-unit-test.md` (structure/determinism); FAIL coverage-artifact verification

**Language-specific policies evaluated:**
- N/A Python; N/A TypeScript; N/A C#
- PARTIAL `powershell.md` (one design finding; coverage-artifact gap)

## 1. General Unit Test Policy Compliance

| Requirement | Status | Evidence |
|------------|--------|----------|
| Independence | PASS | `Invoke-VenvActivation` block saves/restores `global:prompt`, `VIRTUAL_ENV`, `VIRTUAL_ENV_DISABLE_PROMPT` in BeforeEach/AfterEach (Tests 169-196); pure-logic tests share no state. |
| Isolation | PASS | One behavior per `It`; each targets a single function. |
| Fast execution | PASS | No sleeps, I/O, or live processes. |
| Determinism | PASS | All inputs literal; probes injected; OrdinalIgnoreCase comparisons. |
| Readability | PASS | Descriptive `It` names; comments explain edge cases. |
| Scenario completeness | PASS | At-root, descendant, deep nesting, outside-tree, sibling-prefix, case-insensitive, empty/null venv, not-found, missing Activate.ps1, dot-source true/false/empty/&. |
| No temp files / external deps | PASS | None used; wrapper and Test-Path mocked. |
| Coverage thresholds (line >= 85%, branch >= 75%) | FAIL (artifact gap) | Canonical artifact does not contain the changed file; see section 5. |

### 1.2.1 Per-Language Coverage Comparison

- PowerShell: Baseline: N/A (new file) -> Post-change: 86.36% line (38/44) per worker self-check; branch conditionals all exercised. Change: N/A (new file). New/changed-code coverage: 86.36% line (worker-measured). Disposition: FAIL on canonical-evidence verification — the value is not present in the canonical artifact `artifacts/pester/powershell-coverage.xml`, which covers only `.claude/hooks/*`. Evidence: `evidence/qa-gates/2026-05-27T17-39/local-self-check.md`; `artifacts/pester/powershell-coverage.xml`.

## 2. General Code Change Policy Compliance

| Requirement | Status | Evidence |
|------------|--------|----------|
| Simplicity first | PASS | Straightforward ancestor walk and string builders; no deep indirection. |
| Reusability | PASS | Pure functions factored out and reused by the prompt shim. |
| Extensibility | PASS | Injected `$PathExists` seam; keyword-style params with defaults. |
| Separation of concerns | PARTIAL | Pure logic cleanly separated from side effects; the single exception is the entrypoint branch on a test-only env var (lines 312-316). See code-review CR-1. |
| Cohesive modules / under 500 lines | PASS | activate.ps1 = 326; activate.Tests.ps1 = 246. |
| Naming | PASS | PascalCase functions/params per PowerShell convention. |
| Fail fast and explicitly | PASS | Explicit `throw` with actionable messages for missing `.venv` ancestor and missing Activate.ps1. |
| Dependencies | PASS | No new dependencies. |
| I/O boundaries isolated | PASS | Filesystem probe injected; activation isolated to thin wrapper. |
| Toolchain execution | PASS | Orchestrator: PoshQC format ok, analyze ok (0 findings), test ok. |

## 3. Language-Specific Code Change Policy Compliance

### Section 3B: PowerShell Code Change Policy Compliance

| Requirement | Status | Evidence |
|------------|--------|----------|
| Formatting (PoshQC) | PASS | Orchestrator: `run_poshqc_format` ok. |
| Linting (PSScriptAnalyzer) | PASS | Orchestrator: `run_poshqc_analyze` ok, 0 findings. |
| PowerShell 7+ compatible | PASS | `#Requires -Version 7.0`; uses PS7 `[System.StringComparison]` overloads. |
| Advanced functions + CmdletBinding | PASS | All eight functions declare `[CmdletBinding()]`, typed `[OutputType]`. |
| Parameter validation | PASS | `[ValidateNotNullOrEmpty()]`, `[ValidateNotNull()]`, `[AllowEmptyString()]`, `[AllowNull()]`. |
| ShouldProcess for state-changing actions | PARTIAL (accepted) | Side-effecting functions do not implement ShouldProcess; for a dot-sourced interactive dev seam whose purpose is to mutate the session, ShouldProcess is not idiomatic. Documented as an accepted deviation. |
| Avoid global state | PARTIAL (accepted) | `function global:prompt` is installed by design (AC1/AC2 require a persistent prompt); intended contract, not incidental global state. |
| No Invoke-Expression / secrets / hard-coded paths | PASS | None present; repo root resolved at runtime. |
| Write-Error/throw; no silent catch-alls | PASS | `throw` for missing venv; `Write-Error` for non-dot-source guidance. |
| Approved verbs | PASS | Resolve-, Get-, Test-, Invoke-; analyzer clean. |
| Minimal DI seams | PASS | Injected `$PathExists` adapter seam; `Invoke-VenvActivateScript` wrapper seam. |
| Change budget | PASS | One production + one test file. |

## 4. Language-Specific Unit Test Policy Compliance

### Section 4B: PowerShell Unit Test Policy Compliance

| Requirement | Status | Evidence |
|------------|--------|----------|
| Pester v5.x | PASS | `#Requires -Modules Pester >= 5.0.0`; Describe/Context/It; modern Should. |
| Test location mirrors code | PASS | `tests/scripts/dev-tools/activate.Tests.ps1` mirrors `scripts/dev-tools/activate.ps1`. |
| File naming `*.Tests.ps1` | PASS | Correct. |
| Focused tests | PASS | One behavior per `It`. |
| Mock the wrapper, not the executable | PASS | Mocks `Invoke-VenvActivateScript` (wrapper) and `Test-Path` (cmdlet); no raw executable mocked. |
| Deterministic (no network/PATH/profile/live exe/temp) | PASS | Literal paths; injected probes; no temp files. |
| Coverage thresholds | FAIL (artifact gap) | See section 5. |

## 5. Test Coverage Detail

The designated PowerShell coverage artifact is
`artifacts/pester/powershell-coverage.xml`.

Finding (FAIL): The persisted artifact (report timestamp 2026-05-27 13:41:34, JaCoCo
format) contains a single package, `.claude/hooks`, with five source files
(`check-powershell-test-purity.ps1`, `check-python-test-purity.ps1`,
`enforce-powershell-batch-budget.ps1`, `enforce-python-batch-budget.ps1`,
`validate-bash.ps1`). It contains zero entries for `scripts/dev-tools/activate.ps1`. The
sibling `powershell-coverage.koverage.xml` has the same five-file scope. The canonical
artifact therefore does not substantiate coverage for the changed file.

Corroborating non-canonical evidence: the worker self-check
(`evidence/qa-gates/2026-05-27T17-39/local-self-check.md`) reports a targeted Pester run
with `CodeCoverage.Path=scripts/dev-tools/activate.ps1` producing 86.36% line/command
coverage (38/44); the 6 uncovered commands are the mocked dot-source and the 5 entrypoint
commands skipped under the test suppression guard. Branch analysis claims every
conditional in the testable units is exercised. This is credible and consistent with the
test file read directly, but was not persisted to a machine-checkable coverage artifact at
the policy path.

Verdict: FAIL on evidence-verification (the canonical artifact does not cover the changed
file). Added to remediation triggers. Severity is Non-blocking-with-condition for the
overall verdict: the file is T4 dev tooling, the targeted local measurement exceeds the
85% line gate, and the gap is artifact persistence rather than demonstrated coverage
deficiency.

## 6. Test Execution Metrics

| Metric | Value | Status |
|--------|-------|--------|
| Total Tests (activate suite) | 27 | PASS |
| Tests Passed | 27 (100%) | PASS |
| Tests Failed | 0 | PASS |
| dev-tools suite (regression) | 107 pass / 0 fail | PASS |
| Line coverage (changed file, worker self-check) | 86.36% (38/44) | PASS (not in canonical artifact) |
| Branch coverage (changed file) | Conditionals exercised (manual proxy) | PASS (not in canonical artifact) |
| Coverage artifact contains changed file | No | FAIL |

## 7. Code Quality Checks

**For PowerShell:**

| Check | Command | Result | Status |
|-------|---------|--------|--------|
| Invoke-Formatter | `mcp__drm-copilot__run_poshqc_format` | ok | PASS |
| PSScriptAnalyzer | `mcp__drm-copilot__run_poshqc_analyze` | 0 findings | PASS |
| Pester Tests | `mcp__drm-copilot__run_poshqc_test` | ok | PASS |

**Notes:** Toolchain results are orchestrator-reported and treated as verified inputs per
the task brief.

## 8. Gaps and Exceptions

### Identified Gaps
- Coverage artifact gap: the canonical PowerShell coverage artifact does not include the
  changed file `scripts/dev-tools/activate.ps1`. Remediation: persist a dev-tools-scoped
  coverage artifact that includes the file (see remediation-inputs).

### Approved Exceptions
- ShouldProcess not implemented on side-effecting functions: accepted for a dot-sourced
  interactive dev seam.
- `function global:prompt` installation: accepted as the intended contract of an
  activator (AC1/AC2).

### Removed/Skipped Tests
None.

## 9. Summary of Changes

### Files Modified
1. **scripts/dev-tools/activate.ps1** (NEW) — depth-robust repo-root resolution, pure
   prompt builders, thin activation wrappers, non-dot-source guard.
2. **tests/scripts/dev-tools/activate.Tests.ps1** (NEW) — Pester v5 tests for the pure
   logic and orchestration with injected/mocked seams.

## 10. Compliance Verdict

### Overall Status: ⚠️ PARTIALLY COMPLIANT

PowerShell coding standards pass; unit-test structure and determinism pass. Two items
prevent a clean PASS: one separation-of-concerns finding (test-only env switch in
production code) and one coverage-artifact verification gap (the canonical artifact does
not include the changed file). Both are Non-blocking for a T4 dev tool but require
remediation.

**Fail-closed note:** The coverage-artifact gap is recorded as FAIL on evidence
verification; the overall recommendation is Conditional Go pending the remediation items,
not an unconditional PASS.

### Recommendation

**Conditional Go.** Address the two remediation items (persist a coverage artifact that
includes `activate.ps1`; remove the test-only env switch via AST/ScriptBlock import). No
Blocking findings.

**Audit Completed By:** feature-review agent
**Audit Date:** 2026-05-27

## Appendix A: Test Inventory

`tests/scripts/dev-tools/activate.Tests.ps1` (27 tests):

- Get-RepoRelativePrompt > at-root / one-level descendant / deeper nesting / outside-tree / sibling-prefix guard / case-insensitive at-root / case-insensitive descendant (7)
- Get-DefaultPrompt > default PS-prefixed form (1)
- Get-VenvAwarePrompt > empty venv fallback / null venv fallback / at-root from venv parent / descendant from venv parent (4)
- Resolve-RepoRoot > at-start / two-deep walk / arbitrary depth / nearest-of-multiple / not-found exhausts (5)
- Test-IsDotSourced > dot true / script name false / ampersand false / empty false (4)
- Get-NotDotSourcedMessage > states must-be-dot-sourced / includes correct command (2)
- Invoke-VenvActivation > activates and installs prompt / throws when no .venv ancestor / throws when Activate.ps1 missing / installs delegating prompt (4)

## Appendix B: Toolchain Commands Reference

```text
# Canonical MCP gate (orchestrator-run)
mcp__drm-copilot__run_poshqc_format
mcp__drm-copilot__run_poshqc_analyze
mcp__drm-copilot__run_poshqc_test

# Coverage artifact inspected (does not include the changed file)
artifacts/pester/powershell-coverage.xml
```
