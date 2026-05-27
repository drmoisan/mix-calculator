# activate-prompt-repo-root (Issue #13)

- Date captured: 2026-05-27
- Author: Dan Moisan
- Status: Promoted -> docs/features/active/activate-prompt-repo-root/ (Issue #13)

> Automation note: Keep the section headings below unchanged; the promotion tooling maps each of them into the GitHub bug issue template.

- Issue: #13
- Issue URL: https://github.com/drmoisan/mix-calculator/issues/13
- Last Updated: 2026-05-27
- Work Mode: minor-audit

## Summary

The developer activation script `scripts/dev-tools/activate.ps1` does not replace the PowerShell prompt as intended. It resolves the repository root one directory too high, so the in-project `.venv` is never found and activation aborts before the prompt function is defined.

## Environment

- OS/version: Windows, PowerShell 7+
- Python version: 3.13 (Poetry in-project `.venv`)
- Command/flags used: `. .\scripts\dev-tools\activate.ps1` (dot-sourced)
- Data source or fixture: in-project venv at `<repoRoot>/.venv`

## Steps to Reproduce

1. From the repository root, dot-source the script: `. .\scripts\dev-tools\activate.ps1`.
2. Observe the result.
3. Note the prompt is unchanged.

## Expected Behavior

After dot-sourcing, the in-project venv is activated and the prompt becomes `(<project-name>)<repo-relative-path>> ` — for example `(mix-calculator)> ` at the repository root and `(mix-calculator)\.claude> ` inside `.claude`.

## Actual Behavior

Activation throws `venv missing at <repoRoot>\scripts\.venv\Scripts\Activate.ps1` and the `prompt` function is never redefined. The prompt is unchanged.

## Acceptance Criteria

- [x] AC1: Dot-sourcing `. .\scripts\dev-tools\activate.ps1` from the repository root activates the in-project venv and sets the prompt to `(mix-calculator)> `.
- [x] AC2: Dot-sourcing while the current directory is a subdirectory (for example `.claude`) yields `(mix-calculator)\.claude> ` (the repo-relative path with a leading backslash).
- [x] AC3: Repository-root resolution succeeds regardless of the script's own directory depth by resolving to the nearest ancestor that contains `.venv`; it does not assume a fixed number of parent levels.
- [x] AC4: When `$env:VIRTUAL_ENV` is not set, the prompt falls back to a default `PS <path>> ` form.
- [x] AC5: When the current path is outside the repository tree, the prompt renders as `(<project-name>) <absolute-path>> `.
- [x] AC6: Invoking the script without dot-sourcing surfaces clear corrective guidance instead of silently running in a discarded child scope.
- [x] AC7: The pure prompt-string builder and repo-root resolver are covered by deterministic Pester tests with no real venv, PATH dependence, live executables, or temp files; changed-code line coverage is >= 85% and branch coverage is >= 75%. Evidence (2026-05-27T18-13): tests import function definitions via AST extraction (no test-only switch in production); 29 passed / 0 failed; line coverage 97.44% (JaCoCo 38/39) on scripts/dev-tools/activate.ps1, the single uncovered line being the entrypoint call the AST import does not execute; command coverage 97.67% as the branch proxy (Pester v5 JaCoCo emits no BRANCH counter). Persisted coverage artifact: evidence/qa-gates/2026-05-27T18-13/activate-coverage.jacoco.xml (+ activate-coverage-note.md).
- [x] AC8: PoshQC format, PSScriptAnalyzer (repo settings), and Pester all pass via the canonical `drm-copilot` MCP gate. Verified by orchestrator 2026-05-27: run_poshqc_format ok, run_poshqc_analyze ok (0 findings), run_poshqc_test ok.

## Logs / Screenshots

- [x] Attached minimal logs or screenshot
- Snippet: `venv missing at C:\Users\DanMoisan\repos\mix-calculator\scripts\.venv\Scripts\Activate.ps1. Run 'poetry install' first.`

## Impact / Severity

- [ ] Blocker
- [ ] High
- [ ] Medium
- [x] Low

## Suspected Cause / Notes

The script was placed at `scripts/dev-tools/activate.ps1` (two levels deep) but line 5 computes `$repoRoot = Split-Path -Parent $PSScriptRoot`, which yields `<repoRoot>/scripts` rather than `<repoRoot>`. The `.venv` probe therefore targets `<repoRoot>/scripts/.venv`, which does not exist, and the guard `throw`s before the prompt is set. Verified: `<repoRoot>/.venv/Scripts/Activate.ps1` exists; `<repoRoot>/scripts/.venv` does not.

## Proposed Fix / Validation Ideas

- [x] Resolve the repository root by walking ancestor directories upward to the first one that contains `.venv`, so the script is robust to its own depth.
- [x] Add a guard that detects non-dot-sourced invocation and surfaces corrective guidance instead of silently running in a discarded child scope.
- [x] Extract the pure prompt-string builder and repo-root resolver into testable units (Pester) with deterministic, injected filesystem/env seams (no real venv, no PATH dependence, no temp files).
- [x] Manual verification: dot-source at repo root and inside `.claude`; confirm prompt strings.

## Next Step

- [x] Promote to GitHub issue (bug-report template)
- [x] Move to active fix folder / branch