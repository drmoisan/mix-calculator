---
name: powershell-coverage-artifact-scope
description: The canonical PowerShell coverage artifact often covers only .claude/hooks, not the feature file under review
metadata:
  type: project
---

The canonical PowerShell coverage artifact `artifacts/pester/powershell-coverage.xml`
(and sibling `.koverage.xml`) frequently contains only the `.claude/hooks/*` package
(check-powershell-test-purity, check-python-test-purity, enforce-powershell-batch-budget,
enforce-python-batch-budget, validate-bash). When a feature changes a file elsewhere
(e.g. `scripts/dev-tools/activate.ps1`, issue #13), that file is absent from this
artifact, so the policy-required coverage verification cannot be performed from canonical
evidence even when a worker self-check reports a passing per-file percentage.

**Why:** Workers measure feature-file coverage with a targeted `CodeCoverage.Path=<file>`
Pester run but do not persist that targeted XML to the canonical path; the canonical path
is overwritten by a later broader/hooks run. Observed 2026-05-27 on issue #13: worker
self-check reported 86.36% line for activate.ps1, but the persisted artifact had 0 entries
for it.

**How to apply:** Before accepting a PowerShell coverage claim, open
`artifacts/pester/powershell-coverage.xml` and grep for the changed file's basename. If
absent, the coverage threshold is FAIL on evidence verification (canonical artifact does
not cover the changed file) — distinct from a measured deficiency. For a T4 dev tool with
a credible above-threshold worker self-check, classify as Non-blocking-with-condition and
add a remediation item to persist a feature-scoped coverage artifact. Relates to
[[issue2-file-size-watch]] and [[evidence-validator-script-absent]].
