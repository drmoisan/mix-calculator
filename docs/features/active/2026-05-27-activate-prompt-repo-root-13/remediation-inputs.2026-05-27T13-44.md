# Remediation Inputs — activate-prompt-repo-root (Issue #13)

- Timestamp: 2026-05-27T13-44
- Work Mode: minor-audit
- Source artifacts:
  - policy-audit.2026-05-27T13-44.md
  - code-review.2026-05-27T13-44.md
  - feature-audit.2026-05-27T13-44.md

## Remediation-Required Findings

### R-1 (FAIL / Coverage artifact gap) — Canonical PowerShell coverage artifact does not include the changed file

- Source: policy-audit.2026-05-27T13-44.md (Coverage); feature-audit AC7 (PARTIAL).
- Detail: `artifacts/pester/powershell-coverage.xml` (and sibling
  `powershell-coverage.koverage.xml`) cover only `.claude/hooks/*` and contain zero
  entries for `scripts/dev-tools/activate.ps1`. Coverage verification for the changed file
  cannot be performed from the canonical artifact. The worker self-check reports 86.36%
  line coverage on the file via a targeted Pester run, but that result was not persisted.
- Required remediation: regenerate a PowerShell coverage artifact whose scope includes
  `scripts/dev-tools/activate.ps1` (CodeCoverage.Path targeting the dev-tools file or the
  dev-tools suite) and persist it so line >= 85% and branch >= 75% on the changed file are
  independently verifiable.
- Severity in context: Non-blocking-with-condition. The file is T4 dev tooling and the
  targeted local measurement exceeds the 85% line gate; the gap is artifact persistence,
  not demonstrated coverage deficiency.

### R-2 (Major / Non-blocking for T4) — Production entrypoint branches on a test-only environment variable

- Source: code-review.2026-05-27T13-44.md (CR-1).
- Detail: `scripts/dev-tools/activate.ps1` lines 312-316 early-`return` when
  `$env:ACTIVATE_PS1_SUPPRESS_SIDEEFFECTS -eq '1'`; this branch exists only so the test can
  dot-source and import functions without side effects. It couples production control flow
  to the test harness (`.claude/rules/general-code-change.md`, separation of concerns).
- Required remediation: import the script's functions in the test via AST/ScriptBlock parse
  and dot-source of the `function` definitions only (per `.claude/rules/powershell.md`
  Mocking Rules #4), removing lines 312-316; or move the entrypoint side effects behind a
  single dot-source-gated call and import in a child scope. Option 1 is preferred.
- Severity in context: Non-blocking for a T4 seam (explicit variable name, documented,
  unset in normal use, no security/data path). Remediate to avoid normalizing the pattern.

## Blocking Findings

None.

## Artifact Paths

- policy-audit-path: docs/features/active/2026-05-27-activate-prompt-repo-root-13/policy-audit.2026-05-27T13-44.md
- code-review-path: docs/features/active/2026-05-27-activate-prompt-repo-root-13/code-review.2026-05-27T13-44.md
- feature-audit-path: docs/features/active/2026-05-27-activate-prompt-repo-root-13/feature-audit.2026-05-27T13-44.md
- remediation-inputs-path: docs/features/active/2026-05-27-activate-prompt-repo-root-13/remediation-inputs.2026-05-27T13-44.md
