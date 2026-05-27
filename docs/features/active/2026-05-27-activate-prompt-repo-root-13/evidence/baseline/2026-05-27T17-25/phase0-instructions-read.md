# Phase 0 — Instructions Read

Timestamp: 2026-05-27T17-25

Policy Order:
1. CLAUDE.md (standing instructions)
2. .claude/rules/general-code-change.md
3. .claude/rules/general-unit-test.md
4. .claude/rules/powershell.md (language-specific, in scope for **/*.ps1)
5. .claude/rules/quality-tiers.md
6. .claude/rules/tonality.md

Files read (this session):
- scripts/dev-tools/activate.ps1 (in-scope production file; defect confirmed)
- .claude/rules/powershell.md
- tests/scripts/dev-tools/run-actionlint.Tests.ps1 (pattern reference)
- tests/scripts/dev-tools/Initialize-DevEnvironment.Tests.ps1 (pattern reference)
- scripts/dev-tools/run-actionlint.ps1 (dot-source/entrypoint-guard + seam pattern reference)
- pyproject.toml (project name source)
- .mcp.json (toolchain availability check)
- docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/issue.md (minor-audit issue.md format)

Hard constraints acknowledged:
- No edits to .claude/rules/** or .github/instructions/**.
- No secrets / .env creation.
- Use MCP toolchain functions; do not substitute task wrappers.
- Direct-mode budget: <= 2 production PowerShell files (this change touches 1).
