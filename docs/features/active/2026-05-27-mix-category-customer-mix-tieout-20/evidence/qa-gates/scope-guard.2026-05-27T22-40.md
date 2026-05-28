# Scope Guard

Timestamp: 2026-05-27T22-40

Command: `pwsh -NoProfile -Command 'git diff --name-only main...HEAD'`

EXIT_CODE: 0

Output Summary:

The plan-specified `main...HEAD` command captures the cumulative branch diff (including merged sibling issue #18 work and earlier issue #20 work). That output is preserved verbatim below under "Cumulative branch diff", but the remediation cycle's true scope is the **working-tree-only** delta against the most recent commit. The remediation scope is enumerated under "Remediation-cycle scope". Both views are presented for auditor clarity.

## Remediation-cycle scope (working tree against HEAD `98399b6`)

Source: `git status --porcelain`.

Modified:
- `tests/test_mix_rollups.py`
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/plan.2026-05-27T21-54.md` (checklist updates only)
- `.claude/agent-memory/feature-review/issue2-file-size-watch.md` (agent memory note, not a policy file)

New files:
- `tests/_mix_rollups_fixtures.py`
- `tests/test_mix_rollups_tieout.py`
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/code-review.2026-05-27T22-34.md`
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/feature-audit.2026-05-27T22-34.md`
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/policy-audit.2026-05-27T22-34.md`
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/remediation-inputs.2026-05-27T22-34.md`
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/qa-gates/*.2026-05-27T22-40.md` (this remediation cycle's QA evidence)
- `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/evidence/remediation-baseline/*.2026-05-27T22-40.md` (Phase 0 baselines)

## Scope checklist

| Forbidden category | Touched in remediation scope? |
| --- | --- |
| `src/**` | NO |
| `spec.md` | NO |
| `issue.md` | NO |
| `.claude/rules/**` | NO |
| `tests/mix_bottomsup_fixtures.py` (cross-feature) | NO |
| Any non-listed test module under `tests/**` | NO |
| Dependency manifest (`pyproject.toml`, `poetry.lock`) | NO |

Verdict: PASS. Every changed path in the remediation cycle is one of `tests/test_mix_rollups.py`, `tests/test_mix_rollups_tieout.py`, `tests/_mix_rollups_fixtures.py`, `docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/**`, or the executor agent-memory note `.claude/agent-memory/feature-review/issue2-file-size-watch.md`. No `src/**`, `spec.md`, `issue.md`, or `.claude/rules/**` file was modified.

## Cumulative branch diff (`main...HEAD` per plan command)

The plan-specified command produces the cumulative diff against `main`. Paths shown below predate this remediation cycle (issue #18 merge plus earlier issue #20 commits already in the branch HEAD `98399b6`). They are not part of the remediation cycle's scope; the remediation cycle is the working-tree delta enumerated above.

Output:

```
.claude/agent-memory/atomic-executor/MEMORY.md
.claude/agent-memory/atomic-executor/mix-builder-signature-mix-base.md
.claude/agent-memory/feature-review/MEMORY.md
.claude/agent-memory/feature-review/feature-audit-checkoff-heading-case.md
.claude/agent-memory/feature-review/policy-audit-required-structure.md
.claude/agent-memory/orchestrator/MEMORY.md
.claude/agent-memory/orchestrator/s9-ci-gate-parser-fallback.md
README.md
docs/features/active/2026-05-27-mix-bottoms-up-transforms-18/** (issue #18 merged work; not part of #20)
docs/features/active/2026-05-27-mix-category-customer-mix-tieout-20/** (earlier #20 work plus this remediation)
quality-tiers.yml
src/_mix_bottomsup_helpers.py (issue #18 work)
src/_mix_rollups_helpers.py (earlier #20 work)
src/mix_bottomsup.py (issue #18 work)
src/mix_pipeline_run.py (earlier #20 work)
src/mix_rollups.py (earlier #20 work)
tests/mix_bottomsup_fixtures.py (issue #18 work)
tests/test_mix_bottomsup.py (issue #18 work)
tests/test_mix_pipeline.py (earlier #20 work)
tests/test_mix_rollups.py (modified by this remediation; everything else above predates it)
```

None of these paths were modified by the remediation cycle except `tests/test_mix_rollups.py` (which is in the remediation scope and listed above).
