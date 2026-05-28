# Baseline — PoshQC Pester Tests

Timestamp: 2026-05-28T12-57
Command: mcp__drm-copilot__run_poshqc_test
EXIT_CODE: 0
Output Summary:
- Tool reported `ok: true`.
- Pester JUnit report (`artifacts/pester/pester-junit.xml`): tests=109, errors=0, failures=0, time=5.346s. All 109 tests passed across three suites (`activate.Tests.ps1` 29, `Initialize-DevEnvironment.Tests.ps1` 70, `run-actionlint.Tests.ps1` 10).
- JaCoCo coverage report (`artifacts/pester/powershell-coverage.xml`) scopes coverage to package `C:/Users/DanMoisan/repos/mix-calculator-wt-2026-05-28-12-52/.claude/hooks`. Counters at baseline: LINE missed=284 covered=0 rate=0.00%, INSTRUCTION missed=433 covered=0 rate=0.00%, METHOD missed=18 covered=0 rate=0.00%, CLASS missed=5 covered=0 rate=0.00%.
- Coverage interpretation: the baseline coverage tracked by PoshQC for the `.claude/hooks` package is 0.00% line / 0.00% branch (the JaCoCo report does not emit a separate branch counter; branch coverage is recorded as `BRANCH` only when conditionals exist, and is absent here, so the line counter is the reported coverage signal). The repo policy thresholds line >= 85% and branch >= 75% from `.claude/rules/general-unit-test.md` apply to changed lines. This baseline value is the starting reference; the Phase 2 Pester test additions are expected to raise the LINE coverage of `.claude/hooks/validate-orchestrator-output.ps1` substantially in the final-QA artifact.
- Baseline state is established; no regression of changed lines must occur in Phase 3 final QA.
