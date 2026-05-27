# Baseline — fix activate.ps1 repo-root resolution and prompt

Timestamp: 2026-05-27T17-25
Work Mode (proposed): minor-audit (bug, dev tooling, T4)
Scope (production): scripts/dev-tools/activate.ps1
Scope (test): tests/scripts/dev-tools/activate.Tests.ps1 (does not yet exist)

## Toolchain Availability Note

The mandatory MCP toolchain commands required by `.claude/rules/powershell.md` and the
`powershell-qa-gate` skill (`mcp__drm-copilot__run_poshqc_format`,
`mcp__drm-copilot__run_poshqc_analyze`, `mcp__drm-copilot__run_poshqc_test`) are NOT
available in this agent session. The repo's PoshQC tooling directory
(`scripts/powershell/PoshQC`) and the Pester runsettings
(`scripts/powershell/PoshQC/settings/pester.runsettings.psd1`) referenced by the standard
are not present in this checkout (they ship inside the `@danmoisan/drm-copilot-mcp` package).

Locally installed underlying tools were used for baseline capture only:
- PSScriptAnalyzer 1.24.0 (default rule set; no repo PSScriptAnalyzerSettings.psd1 found)
- Pester 5.6.1

Because the exact repo analyzer settings and Pester runsettings could not be loaded, and the
MCP toolchain could not be invoked, any QA result produced here is marked UNVERIFIED against
the canonical gate.

## PSScriptAnalyzer baseline

Command: Invoke-ScriptAnalyzer -Path .\scripts\dev-tools\activate.ps1   (default rules)
EXIT_CODE: 0
Output Summary: No findings on the current activate.ps1 with the default PSScriptAnalyzer
rule set. (UNVERIFIED against repo PoshQC analyzer settings, which were unavailable.)

## Pester baseline

Command: (none — no test file exists for activate.ps1)
EXIT_CODE: n/a
Output Summary: No Pester test file `tests/scripts/dev-tools/activate.Tests.ps1` exists.
Per-file coverage for `scripts/dev-tools/activate.ps1` baseline: 0% (untested unit).

## Behavioral baseline (defect reproduction)

Command: . .\scripts\dev-tools\activate.ps1   (dot-sourced from repo root)
EXIT_CODE: terminating error caught
Output Summary:
- Dot-source throws: "venv missing at
  C:\Users\DanMoisan\repos\mix-calculator\scripts\.venv\Scripts\Activate.ps1. Run 'poetry install' first."
- The `prompt` function is NOT redefined (custom VIRTUAL_ENV prompt absent).

Confirmed root cause: line 5 `Split-Path -Parent $PSScriptRoot` resolves to
`<repoRoot>/scripts` because the script now lives at `scripts/dev-tools/activate.ps1`
(one level deeper than the original `scripts/activate.ps1`). The `.venv` lookup therefore
targets `<repoRoot>/scripts/.venv`, which does not exist; the `throw` on line 7 fires and
the prompt function is never reached.

Filesystem facts verified:
- `<repoRoot>/.venv/Scripts/Activate.ps1` exists: True
- `<repoRoot>/scripts/.venv` exists: False
- pyproject.toml project name: "mix-calculator"
- repo root leaf: "mix-calculator"
