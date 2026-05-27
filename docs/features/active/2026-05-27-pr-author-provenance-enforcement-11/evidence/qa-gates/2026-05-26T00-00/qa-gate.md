# QA Gate — enforce-pr-author-skill hook hardening

Timestamp: 2026-05-26T00-00

## Scope (touched files)

- Production: `.claude/hooks/enforce-pr-author-skill.ps1`
- Test: `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1` (new)

## Toolchain note

The PoshQC MCP tools (`mcp__drm-copilot__run_poshqc_format` / `..._analyze` / `..._test`)
are not present in this agent session's tool set. Per the established repo precedent, the
equivalent direct toolchain was executed: `Invoke-Formatter` (PSScriptAnalyzer module),
`Invoke-ScriptAnalyzer`, and Pester 5.6.1 with code coverage. PoshQC-specific gate
identifiers are recorded as UNVERIFIED-IN-ENVIRONMENT; the equivalent direct gates passed.

Orchestrator follow-up (2026-05-27): the canonical PoshQC MCP gates were
subsequently run by the orchestrator (which has those tools) against
`.claude/hooks` and `tests/claude/hooks`:
`mcp__drm-copilot__run_poshqc_format`, `..._analyze`, and `..._test` each
returned `ok: true`. The UNVERIFIED-IN-ENVIRONMENT note above applied only to
the engineer's session; the canonical gates are now verified.

## Format

Command: `Invoke-Formatter` on both files (loop to stable)
EXIT_CODE: 0
Output Summary: Both files reformatted once (hashtable alignment), then stable on re-run.

## Analyze (PSScriptAnalyzer)

Command: `Invoke-ScriptAnalyzer -Recurse` on both files
EXIT_CODE: 0
Output Summary: 0 findings. Baseline was 0 findings on the production file. Delta = 0.
(One transient `PSUseSingularNouns` finding on `Test-PrBodyReceiptExists` was resolved by
renaming the seam to `Test-PrBodyReceiptPresence`, mirroring the existing
`Get-PrContextArtifactExistence` naming convention. No suppressions were added.)

## Test (Pester v5)

Command: `Invoke-Pester` with code coverage on `.claude/hooks/enforce-pr-author-skill.ps1`
EXIT_CODE: 0
Output Summary: 52 passed, 0 failed, 0 skipped.

## Coverage

EXIT_CODE: 0
Output Summary:
- Line/command coverage (changed file): 91.59% (98/107 commands; JaCoCo LINE 81/88 = 92.05%).
- Gate: >= 85% line. PASS.
- Branch coverage: Pester emits command/line coverage, not a BRANCH counter. The >= 75%
  branch obligation is met via explicit per-branch scenario tests: each provenance branch
  (D, E, G, F, H) has dedicated true/false tests, including the staleness equality boundary
  (older, equal, newer) and hash case-insensitivity, plus canonical/non-canonical and
  body-file-present/absent splits.
- 9 uncovered commands: L174 and L356 are unreachable defensive `return $null` statements;
  L435-444 are the script entrypoint, guarded against dot-source and calling `exit`, so they
  cannot execute in-process. The entrypoint JSON/exit-code contract is verified functionally
  by 3 child-process tests (allow on empty input, block on Case B, exit 1 on malformed JSON);
  child-process execution does not register in in-process coverage by design.

## Delta vs baseline

- PSScriptAnalyzer delta: 0 new findings.
- Failing-tests delta: 0 (baseline had no test; now 52 pass, 0 fail).
- Per-file coverage delta: changed file rose from 0% (no covering test) to 91.59%.
  No regression on changed lines.
