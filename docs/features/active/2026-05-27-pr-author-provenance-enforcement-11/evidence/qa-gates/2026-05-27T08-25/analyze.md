# Final QC — PoshQC Analyze (PSScriptAnalyzer)

Timestamp: 2026-05-27T08-25

## Scope (in-scope files)

- Production: `.claude/hooks/enforce-pr-author-skill.ps1`
- Test: `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`

## Stage 2 — Analyze

Command: `mcp__drm-copilot__run_poshqc_analyze` (workspace_root `c:\Users\DanMoisan\repos\mix-calculator`; scan_folders `.claude/hooks`, `tests/claude/hooks`)
EXIT_CODE: 0
Output Summary: `ok: true`. Ran bundled PoshQC analyze (PSScriptAnalyzer) against the workspace with 2 selected scan folders. 0 findings. Baseline analyzer state for the production file was 0 findings (per `evidence/baseline/2026-05-26T00-00/baseline.md`); delta = 0 (no regression). No suppressions added. Post-run `git status --porcelain` on both in-scope files reported no changes; no loop restart required.
