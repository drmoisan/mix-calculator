# pr-author-provenance-enforcement (Plan)

- **Issue:** #11
- **Parent (optional):** none
- **Owner:** drmoisan
- **Last Updated:** 2026-05-27T08-25
- **Status:** Minor-audit remediation — small-path bug fix already implemented and committed on `fix/pr-author-provenance-enforcement-11`; remaining work closes evidence gaps so a `minor-audit` audit can PASS.
- **Version:** 0.2

**Work Mode:** `minor-audit` (per `issue.md` metadata). The sole acceptance-criteria source is the `## Acceptance Criteria` section in `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/issue.md`. There is no `spec.md` and no `user-story.md`; their absence is expected for `minor-audit` and is not a blocker. Presence of `spec.md`/`user-story.md` in the active folder would be a fail-closed condition.

**Scope (small path, PowerShell only):**
- Production (modified, existed at base): `.claude/hooks/enforce-pr-author-skill.ps1`
- Test (new on this branch): `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`
- Documentation (modified): `.claude/skills/orchestrate/SKILL.md`
- In-scope language for toolchain/coverage gates: **PowerShell only.** No Python, TypeScript, or C# files changed.

**Fail-closed evidence rule:** Include explicit baseline artifact tasks, final-QA artifact tasks, and coverage-comparison tasks for the in-scope language (PowerShell) where policy requires coverage. If any required baseline artifact, QA artifact, or coverage artifact is missing or stale, the audit verdict must be BLOCKED or INCOMPLETE, never PASS.

**Evidence accounting rule:** Record the expected artifact path or location in each evidence-producing task. Do not mark evidence-backed work complete without the artifact present and complete on disk. Pre-checked `[x]` tasks below name the existing backing artifact path.

**Evidence path invariant:** All evidence artifacts resolve to `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/<kind>/...` per `.claude/skills/evidence-and-timestamp-conventions/SKILL.md`. The only non-evidence machine-readable artifact the reviewer consumes is the PowerShell coverage XML at `artifacts/pester/powershell-coverage.xml` — that path is the reviewer's expected coverage-artifact location and is not an evidence path.

**PowerShell toolchain order (cited in verification tasks):** PoshQC format -> PoshQC analyze -> Pester test (with coverage). Type-check is **N/A for PowerShell** and is intentionally omitted (not skipped).

---

### Phase 0 — Context & Inputs

- [x] [P0-T1] Record AC source and work mode: acceptance criteria come from the `## Acceptance Criteria` section of `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/issue.md`; Work Mode is `minor-audit` (verified in `issue.md` metadata line `- Work Mode: minor-audit`).
- [x] [P0-T2] Record branch/commit baseline: branch `fix/pr-author-provenance-enforcement-11`; the hook, test, and orchestrate doc change are implemented and committed (commit `e79c183 fix(hooks): enforce pr-author provenance on gh pr create/edit (#11)`).
- [x] [P0-T3] Capture Phase 0 instructions-read evidence (policy reading order). Artifact: `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/baseline/2026-05-26T00-00/phase0-instructions-read.md` (exists; records CLAUDE.md -> general-code-change -> general-unit-test -> powershell -> quality-tiers -> tonality and files read).
- [x] [P0-T4] Capture PowerShell baseline artifact (tool availability + baseline analyzer + baseline test/coverage state). Artifact: `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/baseline/2026-05-26T00-00/baseline.md` (exists; records PowerShell 7.6.0 / Pester 5.6.1 / PSScriptAnalyzer 1.24.0, baseline analyzer = 0 findings, baseline test count = 0, baseline coverage = 0% no covering test).

### Phase 1 — Preparation

- [x] [P1-T1] Confirm scope is locked to the three in-scope files and that no out-of-scope language (Python/TypeScript/C#) is touched. Backing: `issue.md` `## Scope & Non-Goals` (PowerShell hook + Markdown skill only) and the committed diff.
- [x] [P1-T2] Sync workspace to `fix/pr-author-provenance-enforcement-11` head and confirm PowerShell toolchain availability (pwsh 7+, Pester 5, PSScriptAnalyzer) for the re-verification run in Phase 4.

### Phase 2 — Regression Test (fail-first proof)

- [x] [P2-T1] Confirm the regression test exists and exercises every reason code and boundary. Artifact on disk: `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1` (new on this branch; Pester 5). Backing record: `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-26T00-00/qa-gate.md` (52 passing tests).
- [x] [P2-T2] [expect-fail] Satisfy the fail-before requirement. Because the fix is already committed, a fresh failing run is not reproducible. Produce a schema-valid fail-before exception dossier at `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/regression-testing/fail-before-exception.2026-05-27T08-25.md` containing: `Timestamp:`, `WhyFailingRunImpossible:` (fix already in place on branch head), and an alternative-proof section citing the documented pre-fix behavior `gh pr create ... --body-file /tmp/pr_body_9.md` -> `{"decision":"allow"}` recorded in `issue.md` (Logs/Screenshots and Actual Behavior sections). Per `evidence-and-timestamp-conventions`, a schema-valid exception dossier satisfies the fail-before requirement. If a failing-run artifact is instead found under `evidence/regression-testing/`, reference it and mark this complete.

### Phase 3 — Minimal Fix (already applied)

- [x] [P3-T1] Provenance enforcement applied to `Get-PrAuthorBypassReason` in `.claude/hooks/enforce-pr-author-skill.ps1`: canonical body path `artifacts/pr_body_<N>.md`, sibling receipt `artifacts/pr_body_<N>.receipt.json`, `receipt.number == <N>`, `sha256(body) == receipt.sha256`, and `receipt.created_at` strictly newer than `artifacts/pr_context.summary.txt`; new reason codes `PR_BODY_PATH_NONCANONICAL`, `PR_AUTHOR_RECEIPT_MISSING`, `PR_AUTHOR_RECEIPT_NUMBER_MISMATCH`, `PR_AUTHOR_RECEIPT_HASH_MISMATCH`, `PR_AUTHOR_RECEIPT_STALE`. Output contract and existing block cases A/B/C and metadata-only `gh pr edit` allow path preserved. Committed (commit `e79c183`).

### Phase 4 — Verification Loop (PowerShell toolchain; coverage artifact regeneration)

- [x] [P4-T1] Run PoshQC **format** on the in-scope files (`.claude/hooks/enforce-pr-author-skill.ps1`, `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`) against branch head. Expected: no residual changes. Record a final-QC artifact at `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/format.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P4-T2] Run PoshQC **analyze** (PSScriptAnalyzer) on the in-scope files against branch head. Expected: 0 findings, 0 regression vs baseline. Record a final-QC artifact at `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/analyze.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, `Output Summary:`.
- [x] [P4-T3] Run PoshQC **Pester test with code coverage scoped to include `.claude/hooks/enforce-pr-author-skill.ps1`**, regenerating the machine-readable coverage artifact at `artifacts/pester/powershell-coverage.xml` so it includes the changed hook (the current XML is STALE — it covers 5 unrelated hook files and omits `enforce-pr-author-skill.ps1`, which the reviewer's PowerShell coverage gate would read as a missing/failing target). Record a final-QC artifact at `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/test.md` with `Timestamp:`, `Command:`, `EXIT_CODE:`, and `Output Summary:` including numeric headline values (test pass/fail counts and changed-file line/branch coverage percent). Type-check stage is N/A for PowerShell — state this explicitly in the artifact so the reviewer sees it is intentional. Restart the loop from P4-T1 if any stage fails or changes files.
- [x] [P4-T4] Coverage comparison/threshold verification for the changed hook. Confirm `artifacts/pester/powershell-coverage.xml` now contains `.claude/hooks/enforce-pr-author-skill.ps1` and that it shows line coverage >= 85% and the branch obligation >= 75% is met, with no regression on changed lines. Record the comparison at `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/qa-gates/2026-05-27T08-25/coverage-comparison.md` reporting: baseline coverage (0% — no covering test pre-change, per the Phase 0 baseline artifact), post-change line/branch coverage (from the regenerated XML; expected ~91.59% line per the existing qa-gate narrative), and changed-code coverage. Reference the consumed artifact path `artifacts/pester/powershell-coverage.xml` explicitly.

### Phase 5 — Documentation & Status

- [x] [P5-T1] Orchestrate skill documentation updated: `.claude/skills/orchestrate/SKILL.md` documents the PR Authoring (pr-author handoff) step, the receipt schema (`pr_body_<N>.receipt.json`), and PR Creation Gate **condition 5** (PR body produced via the pr-author handoff). Verified present in the committed file (section "PR Authoring (pr-author Handoff)" and "PR Creation Gate" condition 5).
- [x] [P5-T2] Mirror the issue/AC status update for issue #11 to `docs/features/active/2026-05-27-pr-author-provenance-enforcement-11/evidence/issue-updates/issue-11.2026-05-27T08-25.md` with `Timestamp:`, the exact update text, and `PostedAs:` once the final-QC and coverage evidence is complete.

### Phase 6 — PR & Handoff

- [x] [P6-T1] Prepare PR notes (summary, in-scope files, fail-before exception rationale, regenerated coverage artifact, links to the Phase 4 qa-gate artifacts and `issue.md` acceptance criteria) and route through the pr-author handoff per `.claude/skills/orchestrate/SKILL.md` PR Creation Gate condition 5.

### Phase 7 — Rollout / Follow-up

- [x] [P7-T1] Record traceability links (issue #11, branch `fix/pr-author-provenance-enforcement-11`, PR, and the qa-gate/coverage evidence folder under `2026-05-27T08-25/`) for audit reference.

---

## Acceptance-Criteria Mapping (source: `issue.md` `## Acceptance Criteria`)

| AC (issue.md) | Verifying task(s) | Evidence |
|---|---|---|
| Repro now blocked with `PR_BODY_PATH_NONCANONICAL` | P3-T1, P2-T2 | committed hook diff; fail-before exception dossier |
| Regression tests added and passing (52 tests) | P2-T1, P4-T3 | `tests/claude/hooks/enforce-pr-author-skill.Tests.ps1`; `evidence/qa-gates/2026-05-27T08-25/test.md` |
| Edge cases / invalid inputs handled | P2-T1, P4-T3 | test file scenarios; test.md |
| No unintended behavior changes outside scope | P1-T1, P3-T1, P4-T2 | analyze.md (0 regression) |
| Logs/telemetry: output contract unchanged | P3-T1 | committed hook diff |
| Performance: one small-file hash per command | P3-T1 | committed hook diff |
| Full toolchain pass (format -> analyze -> test; type-check N/A); changed-file line coverage >= 85% | P4-T1, P4-T2, P4-T3, P4-T4 | format.md, analyze.md, test.md, coverage-comparison.md; `artifacts/pester/powershell-coverage.xml` |
| Docs updated: orchestrate SKILL handoff + receipt schema + PR Creation Gate condition 5 | P5-T1 | `.claude/skills/orchestrate/SKILL.md` |
