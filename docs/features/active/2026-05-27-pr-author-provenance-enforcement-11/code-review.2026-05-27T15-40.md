# Code Review: pr-author-provenance-enforcement (Issue #11)

**Review Date:** 2026-05-27
**Reviewer:** feature-review agent
**Feature Folder:** `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11`
**Feature Folder Selection Rule:** Folder suffix `-11` matches the issue number in the branch name `fix/pr-author-provenance-enforcement-11`.
**Base Branch:** `main` (merge-base `4c1e8faf8166c2ff1da680fb83dd3c4998adc187`)
**Head Branch:** `fix/pr-author-provenance-enforcement-11` (`3e6677dfcbc88c101e0dbd0d973cdcfa1afce689`)
**Review Type:** Initial review

---

## Executive Summary

This change hardens the `enforce-pr-author-skill.ps1` PreToolUse hook so that `gh pr create` / `gh pr edit` commands carrying `--body-file` are allowed only when the PR body was produced by the pr-author handoff. The prior hook checked command shape only: presence of `--body-file` plus an existing `artifacts/pr_context.summary.txt`. That allowed a self-authored body at an arbitrary path (for example `/tmp/pr_body_9.md`), which is the defect reported in issue #11. The fix adds provenance enforcement in `Get-PrAuthorProvenanceReason`: canonical body path `artifacts/pr_body_<N>.md`, a sibling receipt `artifacts/pr_body_<N>.receipt.json`, `receipt.number == <N>`, `sha256(body) == receipt.sha256`, and `receipt.created_at` strictly newer than the context summary write time. Five reason codes were added; the JSON output contract and prior block cases A/B/C plus the metadata-only `gh pr edit` allow path are preserved.

**What changed:**
- `.claude/hooks/enforce-pr-author-skill.ps1` (+260/-6): new pure decision core `Get-PrAuthorProvenanceReason`; adapter seams `Get-PrContextWriteTime`, `Test-PrBodyReceiptPresence`, `Get-PrBodyReceipt`, `Get-PrBodyFileHash`; parser `Get-PrBodyFilePath`; provenance dispatch added to `Get-PrAuthorBypassReason`.
- `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1` (NEW, +396): 52-test Pester suite covering every reason code and boundary.
- `.claude/skills/orchestrate/SKILL.md` (+45): documents the pr-author handoff, receipt schema, and PR Creation Gate condition.

**Top 3 risks:**
1. Receipt non-repudiation is out of scope by design: one actor can write both the body and the receipt, so the gate raises friction and creates an audit trail rather than providing unforgeable proof. This is documented in `issue.md` non-goals and is an accepted limitation, not a defect.
2. Coverage on the changed hook (92.05% LINE) leaves the dot-source-guarded entrypoint (lines 435-444) uncovered in-process; it is verified functionally via child-process tests, which is an appropriate compensating control.
3. Work-mode marker divergence between local `issue.md` (`minor-audit`) and the GitHub issue body (`full-bug`); does not affect implementation quality but should be reconciled.

**PR readiness recommendation:** **Go** — The implementation is policy-compliant, the toolchain is clean, coverage meets gates, and no Blocker or Major findings were identified.

---

## Findings Table

| Severity | File | Location | Finding | Recommendation | Rationale | Evidence |
|---|---|---|---|---|---|---|
| Info | `.claude/hooks/enforce-pr-author-skill.ps1` | `Get-PrAuthorProvenanceReason` Case H | `created_at` is parsed with `[datetimeoffset]::Parse` using `AssumeUniversal`/`AdjustToUniversal`; a malformed `created_at` string would throw and surface as an exit-1 error rather than a structured block reason. | Optional: validate/parse defensively and map a parse failure to a dedicated stale/invalid reason code if structured feedback is preferred. | A throw still fails closed (blocks the PR), so this is informational, not a defect. | Inspected lines 247-255; entrypoint try/catch at lines 434-440 converts throws to exit 1. |
| Info | `.claude/hooks/enforce-pr-author-skill.ps1` | `Get-PrAuthorBypassReason` lines 295-296 | The `--body` vs `--body-file` discrimination uses regex `--body(?!-file)\b`; this is correct for the observed forms but depends on flag spelling rather than a tokenized parse. | None required; current behavior is covered by tests. Consider tokenized arg parsing only if future flags complicate the regex. | Regex-based flag detection is acceptable for this constrained surface and is exercised by tests. | Inspected lines 288-320; parser tests in the suite. |
| Info | `.claude/skills/orchestrate/SKILL.md` | doc | Documentation-only change adding the receipt schema and PR Creation Gate condition; not a language-toolchain file. | None. | Keeps the enforcement and its documentation in sync. | Diff +45 lines. |

No Blockers or Major findings.

---

## Implementation Audit

### PowerShell implementation audit

#### What changed well

- The decision logic is cleanly separated into a pure core (`Get-PrAuthorProvenanceReason`, no I/O) and an orchestration layer (`Get-PrAuthorBypassReason`) that resolves facts through narrow adapter seams. This matches the repository's minimal-DI seam guidance and makes every branch deterministically testable without touching disk or the clock.
- I/O is resolved lazily: the receipt and body hash are only read when the path is canonical and the receipt exists, so earlier failure cases (non-canonical path, missing receipt) avoid unnecessary filesystem access.
- The provenance checks return the first failure in a fixed order (D, E, G, F, H), which yields a single actionable reason code per command and keeps the control flow simple.
- The output contract is preserved exactly: compact `{"decision":"allow"}` / `{"decision":"block","reason":...}`, exit 0 on success, exit 1 on malformed JSON, allow on missing input/command, and the dot-source guard for test import.

#### API and safety notes

- All functions are advanced functions with `[CmdletBinding()]` and `[OutputType]`. Mandatory parameters and `[AllowEmptyString()]`/`[AllowNull()]` attributes are used intentionally where empty/null inputs are valid states.
- Function names use approved verbs (`Get-`, `Test-`, `Invoke-`). Analyzer reports 0 findings with no suppressions added.
- Script-scoped state is limited to two read-only constants (`$script:PrContextArtifactPath`, `$script:PrBodyCanonicalPattern`); there is no mutable global state.
- The hash comparison normalizes both sides to lowercase invariant before comparing, correctly making the SHA-256 check case-insensitive.

#### Error handling and logging

- Malformed `CLAUDE_TOOL_INPUT` JSON throws with added context and the entrypoint converts it to a `Write-Error` plus exit 1 — fail-fast and explicit, no silent catch-all.
- Missing tool input or missing command text returns allow, which is the correct conservative default for a hook that should not block unrelated commands.
- Block reasons are specific and actionable, each naming the exact remediation (run `collect_pr_context`, apply pr-author handoff, reference the canonical path).

---

## Test Quality Audit

The Pester suite (52 tests) was reviewed against the changed hook and the regenerated coverage artifact. The suite exercises each reason code (D/E/G/F/H), the staleness equality boundary (older/equal/newer), hash case-insensitivity, the `--body-file`/`=`/quoted parser, malformed and empty `CLAUDE_TOOL_INPUT`, and the metadata-only `gh pr edit` allow path. Changed-hook line coverage is 92.05% (>= 85% gate); the uncovered lines are two unreachable defensive `return $null` statements and the dot-source-guarded entrypoint, the latter verified by child-process tests.

### Reviewed test and QA artifacts

- `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1` — 52 Pester tests; mirrors the code file path; mocks only the filesystem/clock adapter seams, leaving the decision core running real.
- `artifacts/pester/powershell-coverage.xml` — JaCoCo coverage scoped to the changed hook; verified to contain exactly `sourcefilename="enforce-pr-author-skill.ps1"` with top-level LINE 81 covered / 7 missed = 92.05%.
- `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/coverage-comparison.md` — threshold verification: line >= 85% PASS, no regression on changed lines.
- `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/regression-testing/fail-before-exception.2026-05-27T08-25.md` — schema-valid fail-before exception dossier documenting the pre-fix `allow` behavior.

### Quality assessment prompts

- **Determinism:** Filesystem and clock reads route through mockable seams; the staleness comparison uses an injected `ContextWriteTime`. No wall-clock, RNG, or network dependency.
- **Isolation:** Each `It` targets one behavior (one reason code or boundary); the pure core is tested independently of the orchestration layer.
- **Speed:** 52 in-process tests with mocked I/O; PoshQC test gate returns `ok:true` promptly.
- **Diagnostics:** Assertions check on specific reason-code prefixes, so a failure identifies the broken case directly.

---

## Security / Correctness Checks

| Check | Status | Evidence |
|---|---|---|
| No secrets in code | ✅ PASS | No credentials, tokens, or secrets in the hook or tests; inspected full diff. |
| No unsafe subprocess or command construction | ✅ PASS | The hook inspects command text and reads files; it does not construct or execute shell commands. No `Invoke-Expression`. |
| Input validation at boundaries | ✅ PASS | Malformed JSON throws/exits 1; empty input allows; the `--body-file` parser handles bare/quoted/`=` forms and returns `$null` when absent. |
| Error handling remains explicit | ✅ PASS | Fail-fast on malformed JSON; first-failure provenance ordering; no broad catch-all. |
| Configuration / path handling is safe | ✅ PASS | Canonical path enforced via anchored regex `^artifacts[/\\]pr_body_(\d+)\.md$`; receipt path derived by replacing the `.md` suffix; `Test-Path -LiteralPath` used throughout to avoid wildcard interpretation. |

---

## Research Log

No external research was required. The review is based on diff inspection of the two PowerShell files, the regenerated coverage artifact, the feature-folder QA evidence, and independent re-runs of the PoshQC format/analyze/test gates.

---

## Verdict

The change is ready for normal PR flow. It correctly closes the issue #11 defect by replacing shape-only validation with provenance enforcement, while preserving the existing output contract and allow/block cases. The implementation follows the repository's separation-of-concerns and minimal-DI seam guidance, the toolchain is clean (format/analyze/test all `ok:true`), changed-hook coverage meets the 85% line gate with branch obligations met via explicit per-branch scenarios, and both files are under the 500-line limit. The only items are Info-level observations (defensive `created_at` parsing, regex-based flag detection) and a non-blocking work-mode marker divergence to reconcile before archive. PR readiness: Go.
