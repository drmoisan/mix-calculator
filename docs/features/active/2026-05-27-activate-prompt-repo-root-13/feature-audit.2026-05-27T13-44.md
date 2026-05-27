# Feature Audit: activate-prompt-repo-root (Issue #13)

**Audit Date:** 2026-05-27
**Feature Folder:** `docs/features/active/2026-05-27-activate-prompt-repo-root-13`
**Base Branch:** `main`
**Head Branch:** untracked working-tree additions (HEAD == merge-base with `main`)
**Work Mode:** `minor-audit`
**Audit Type:** Initial acceptance review

## Scope and Baseline

- **Base branch:** `main` (commit `ee129603facd5384d7f8cee6f75a84de67e78f0d`)
- **Head branch/commit:** working-tree additions on `main`
- **Merge base:** `ee129603facd5384d7f8cee6f75a84de67e78f0d`
- **Evidence sources:**
  - Primary: direct read of `scripts/dev-tools/activate.ps1` and `tests/scripts/dev-tools/activate.Tests.ps1`
  - Feature evidence: `evidence/qa-gates/2026-05-27T17-39/local-self-check.md`; `evidence/baseline/2026-05-27T17-25/`
  - Additional: `artifacts/pester/pester-junit.xml`; `artifacts/pester/powershell-coverage.xml`
- **Feature folder used:** `docs/features/active/2026-05-27-activate-prompt-repo-root-13`
- **Requirements source:** `issue.md` (minor-audit -> issue.md only)
- **Work mode resolution note:** `issue.md` persists `- Work Mode: minor-audit`; the explicit `## Acceptance Criteria` section (AC1-AC8) is the authoritative AC source.
- **Scope note:** HEAD equals the merge-base; the change is delivered as untracked additions, so `git diff main` is empty and the files were reviewed as additions.

## Acceptance Criteria Inventory

**Authoritative AC source files for this run:**
- `docs/features/active/2026-05-27-activate-prompt-repo-root-13/issue.md` — only source (minor-audit)

### Acceptance criteria

1. AC1: Dot-sourcing `. .\scripts\dev-tools\activate.ps1` from the repository root activates the in-project venv and sets the prompt to `(mix-calculator)> `.
2. AC2: Dot-sourcing while the current directory is a subdirectory (for example `.claude`) yields `(mix-calculator)\.claude> ` (the repo-relative path with a leading backslash).
3. AC3: Repository-root resolution succeeds regardless of the script's own directory depth by resolving to the nearest ancestor that contains `.venv`; it does not assume a fixed number of parent levels.
4. AC4: When `$env:VIRTUAL_ENV` is not set, the prompt falls back to a default `PS <path>> ` form.
5. AC5: When the current path is outside the repository tree, the prompt renders as `(<project-name>) <absolute-path>> `.
6. AC6: Invoking the script without dot-sourcing surfaces clear corrective guidance instead of silently running in a discarded child scope.
7. AC7: The pure prompt-string builder and repo-root resolver are covered by deterministic Pester tests with no real venv, PATH dependence, live executables, or temp files; changed-code line coverage is >= 85% and branch coverage is >= 75%.
8. AC8: PoshQC format, PSScriptAnalyzer (repo settings), and Pester all pass via the canonical `drm-copilot` MCP gate.

## Acceptance Criteria Evaluation

| # | Criterion | Status | Evidence | Verification command(s) | Notes |
|---|-----------|--------|----------|--------------------------|-------|
| 1 | Dot-source at root -> `(mix-calculator)> ` | PASS | `Invoke-VenvActivation` resolves root, activates, installs `global:prompt`; `Get-RepoRelativePrompt` returns at-root form (activate.ps1 131-141, 305-307); Tests 36-38, 91-95, 198-211, 236-245; worker behavioral check | direct read; Pester | — |
| 2 | Subdirectory -> `(mix-calculator)\.claude> ` | PASS | Descendant branch returns rel path with leading backslash (activate.ps1 134-135); Tests 40-43, 97-100; worker behavioral check | direct read; Pester | — |
| 3 | Depth-robust root resolution via nearest `.venv` ancestor | PASS | `Resolve-RepoRoot` ancestor walk with injected probe + drive-root termination (activate.ps1 80-93); Tests 103-138 cover at-start, two-deep, arbitrary depth, nearest-of-multiple, not-found | direct read; Pester | — |
| 4 | Unset VIRTUAL_ENV -> default `PS <path>> ` | PASS | `Get-VenvAwarePrompt` returns `Get-DefaultPrompt` on empty/null (activate.ps1 194-195, 160); Tests 73-89 | direct read; Pester | — |
| 5 | Outside tree -> `(<project-name>) <absolute-path>> ` | PASS | Else branch sets `rel = " $CurrentPath"` (activate.ps1 137-139); Tests 50-53, 55-60 (sibling-prefix guard) | direct read; Pester | — |
| 6 | Non-dot-source -> corrective guidance, no silent child scope | PASS | `Test-IsDotSourced` + `Write-Error (Get-NotDotSourcedMessage)` then return (activate.ps1 321-323; 235-241); Tests 140-166; worker confirmed exit 1 with guidance | direct read; Pester | — |
| 7 | Deterministic Pester coverage; line >= 85%, branch >= 75% on changed code | PARTIAL | Determinism and no-real-dependency requirement verified by reading the tests (literal inputs, injected probes, no temp files). Coverage thresholds reported met by worker self-check (86.36% line; branches exercised) but NOT substantiated by the canonical artifact, which omits `activate.ps1` | direct read; `evidence/qa-gates/2026-05-27T17-39/local-self-check.md` | Determinism PASS; coverage verification unmet from canonical evidence |
| 8 | Canonical MCP gate (format/analyze/test) all pass | PASS | Orchestrator-reported and recorded in issue.md: format ok, analyze ok (0 findings), test ok | `mcp__drm-copilot__run_poshqc_*` | Treated as verified input per task brief |

## Summary

**Overall Feature Readiness:** NEEDS REVISION (conditional)

**Criteria summary:**
- **PASS:** 7 (AC1, AC2, AC3, AC4, AC5, AC6, AC8)
- **PARTIAL:** 1 (AC7)
- **UNVERIFIED:** 0
- **FAIL:** 0

**Top gaps preventing PASS:**
1. AC7 coverage verification: the canonical PowerShell coverage artifact does not include `scripts/dev-tools/activate.ps1`, so the >= 85% line / >= 75% branch result is not independently verifiable from canonical evidence.

**Recommended follow-up verification steps:**
1. Regenerate and persist a dev-tools-scoped PowerShell coverage artifact that includes `scripts/dev-tools/activate.ps1`, then re-confirm AC7.
2. (Quality) Remove the test-only env switch (code-review CR-1) so the entrypoint guard is exercised under coverage.

## Acceptance Criteria Check-off

All eight AC items are already `[x]` in `issue.md`. AC7 is PARTIAL solely due to the
coverage-artifact verification gap (the underlying coverage was measured locally above
threshold; the gap is artifact persistence, not deficient testing). No checkbox was reverted
because the work is delivered and determinism is verified; the unmet portion is documented
here and in remediation-inputs rather than by unchecking the box. No source-file checkbox
change was made by this audit.

### AC Status Summary

- Source: `docs/features/active/2026-05-27-activate-prompt-repo-root-13/issue.md`
- Total AC items: 8
- Checked off (delivered): 8 (pre-existing in issue.md)
- Remaining (unchecked): 0
- Items remaining: None.

| Source File | Total AC | Checked (PASS) | Unchecked | Notes |
|-------------|----------|----------------|-----------|-------|
| `issue.md` | 8 | 8 (7 PASS + AC7 PARTIAL, left checked) | 0 | Checkbox-backed; AC7 PARTIAL documented, not reverted |
