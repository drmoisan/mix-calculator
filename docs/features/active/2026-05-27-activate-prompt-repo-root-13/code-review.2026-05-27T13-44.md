# Code Review: activate-prompt-repo-root (Issue #13)

**Review Date:** 2026-05-27
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-05-27-activate-prompt-repo-root-13`
**Base Branch:** `main`
**Head Branch:** untracked working-tree additions (HEAD == merge-base with `main`)
**Review Type:** Initial review (minor-audit)

## Executive Summary

The change fixes `scripts/dev-tools/activate.ps1` so that dot-sourcing activates the
in-project Poetry venv and sets a repo-relative prompt. The root cause — repo-root resolved
one level too high via `Split-Path -Parent $PSScriptRoot` — is corrected by a depth-robust
ancestor walk (`Resolve-RepoRoot`) that finds the nearest ancestor containing `.venv`. Pure
logic (root resolution, prompt-string construction, dot-source predicate) is cleanly
separated from thin side-effecting wrappers, and the pure functions are exercised through
real code paths with injected seams. PSScriptAnalyzer is clean and both files are under the
size limit.

**What changed:**
New production file `scripts/dev-tools/activate.ps1` (326 lines) with eight functions and a
guarded entrypoint, plus new Pester v5 tests `tests/scripts/dev-tools/activate.Tests.ps1`
(246 lines, 27 tests). Delivered as untracked additions.

**Top 3 risks:**
1. Production entrypoint branches on a test-only environment variable (CR-1).
2. Canonical PowerShell coverage artifact does not include the changed file, so the
   reported 86.36% line coverage is not independently verifiable.
3. Two entrypoint commands remain uncovered as a consequence of the env-switch design (CR-2).

**PR readiness recommendation:** **Conditional Go** — sound implementation; address the
test-only env switch and persist a coverage artifact that includes the changed file.

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Major | `scripts/dev-tools/activate.ps1` | lines 312-316 | Production entrypoint early-returns when `$env:ACTIVATE_PS1_SUPPRESS_SIDEEFFECTS -eq '1'`, a branch that exists only for the test harness | Import functions in the test via AST/ScriptBlock parse and dot-source of `function` definitions (per `powershell.md` Mocking Rules #4); remove lines 312-316 | Couples production control flow to the test harness; deviates from separation of concerns | activate.ps1 312-316; activate.Tests.ps1 25-31 |
| Minor | `scripts/dev-tools/activate.ps1` | lines 312-326 | Non-dot-source `Write-Error` branch and `Invoke-VenvActivation` call are uncovered because the test suppresses side effects via early return | Adopting CR-1 lets the entrypoint guard be exercised without real activation, narrowing the uncovered set | Quality improvement; follows from CR-1 | evidence/qa-gates/2026-05-27T17-39/local-self-check.md |
| Info | `scripts/dev-tools/activate.ps1` | line 265 | The single dot-source line in `Invoke-VenvActivateScript` is uncovered by design (it is the mocked wrapper seam) | None; correct application of the wrapper-seam pattern | Documents why one uncovered command is acceptable | activate.ps1 245-266 |
| Info | n/a | n/a | No Blocker findings | — | — | — |

## Implementation Audit

### PowerShell implementation audit

#### What changed well

- `Resolve-RepoRoot` (lines 80-93) walks ancestors with an injected `$PathExists` probe and
  a correct `parent -eq current` drive-root termination, making it depth-robust and unit-
  testable without a real filesystem.
- `Get-RepoRelativePrompt` (lines 131-141) guards the sibling-prefix case
  (`mix-calculator-extra` is not a descendant of `mix-calculator`) via the trailing-
  separator check on line 134, and uses OrdinalIgnoreCase to avoid locale/drive-casing
  flakiness.
- The pure/side-effect split (`Get-VenvAwarePrompt` decision vs. `Invoke-VenvActivation`
  orchestration) keeps the testable logic isolated from the dot-source side effect.

#### API and safety notes

- All functions are advanced functions with `[CmdletBinding()]`, typed `[OutputType]`, and
  validation attributes. Approved verbs throughout; analyzer reports 0 findings.
- `VIRTUAL_ENV_DISABLE_PROMPT = '1'` is set before activation so the venv's own prompt does
  not override the script-owned prompt (line 302) — a correct, non-obvious detail.
- `function global:prompt` is installed by design; this is the activator's intended contract
  (AC1/AC2), not incidental global state.
- ShouldProcess is not implemented on the side-effecting functions; acceptable for a
  dot-sourced interactive dev seam.

#### Error handling and logging

- Explicit `throw` with actionable guidance when no `.venv` ancestor is found (line 294) and
  when the resolved Activate.ps1 is missing (line 299).
- Non-dot-source invocation surfaces corrective guidance via `Write-Error` and returns
  (lines 321-323) instead of silently running in a discarded child scope.

## Test Quality Audit

The tests exercise the pure logic through real code paths and mock only the wrapper seam and
`Test-Path`. No real venv, PATH dependence, live executables, or temp files are used.

### Reviewed test and QA artifacts

- `tests/scripts/dev-tools/activate.Tests.ps1` — 27 tests across the pure builders, the
  resolver, the dot-source predicate, the guidance message, and the orchestration (with
  mocked seams and save/restore of prompt and env vars for independence).
- `evidence/qa-gates/2026-05-27T17-39/local-self-check.md` — worker self-check: 27 pass / 0
  fail; 86.36% line coverage on the changed file; dev-tools suite 107 pass / 0 fail.
- `artifacts/pester/powershell-coverage.xml` — present but covers only `.claude/hooks/*`; it
  does NOT contain `activate.ps1`, so it does not substantiate the coverage claim.

### Quality assessment prompts

- **Determinism:** Literal inputs; injected probes; OrdinalIgnoreCase comparisons; no timing
  or environment dependence.
- **Isolation:** One behavior per `It`; orchestration tests save/restore global state.
- **Speed:** No sleeps or I/O; fast by construction.
- **Diagnostics:** Descriptive `It` names and `Should -Match`/`Should -Be` assertions yield
  clear failures.

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | No credentials or secrets present. |
| No unsafe subprocess or command construction | ✅ PASS | No `Invoke-Expression`; dot-source target derived from a validated resolved path. |
| Input validation at boundaries | ✅ PASS | Validation attributes on all parameters. |
| Error handling remains explicit | ✅ PASS | `throw`/`Write-Error`; no silent catch-alls. |
| Configuration / path handling is safe | ✅ PASS | No hard-coded machine paths; repo root resolved at runtime; sibling-prefix guard prevents false descendant matches. |

## Research Log

No external research was required. All findings are grounded in the reviewed files, repo
policy documents, and the feature-folder evidence artifacts.

## Verdict

The implementation is sound for a T4 dev-tooling fix and closes the reported defect. One
Major-category design finding (CR-1: production branch on a test-only env var) is
Non-blocking for this seam but should be remediated via AST/ScriptBlock import to remove the
test-only branch from production code. The coverage-artifact gap (canonical artifact does
not include the changed file) should be closed by persisting a dev-tools-scoped coverage
artifact. No Blocking findings. Recommendation: Conditional Go.
