---
name: pr-context-summary-can-be-stale
description: artifacts/pr_context.summary.txt may describe a prior PR/branch, not the branch under review; verify head ref and fall back to the live git diff
metadata:
  type: feedback
---

`artifacts/pr_context.summary.txt` can be stale: on the issue #60 review it described PR #56 / issue #55 (head `bd49647`, base resolved to `b655d81`), not the branch actually under review (`fix/configurable-schema-gui-fixes`, head `4856661`, merge-base `1d27514`).

**Why:** The summary artifact is regenerated per-run but was not refreshed for this branch, so its Base/Head/Range and "Changed files overview" pointed at an unrelated earlier feature.

**How to apply:** Always cross-check the summary's `Head ref (resolved)` against the actual review head (from the caller prompt / `git rev-parse HEAD`). If they differ, treat the summary as stale, use the live `git diff <merge-base>...<head>` as the authoritative scope, and record the discrepancy in the feature-audit Scope/Baseline section. Do not let a stale summary narrow or misdirect the audit. Related: [[tested-but-unwired-seam-pattern]] (independent verification over reported artifacts).
