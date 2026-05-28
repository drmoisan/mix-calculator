---
name: potential-to-issue-creates-github-issue
description: The potential_to_issue MCP promotion tool creates the GitHub issue itself; do not also run gh issue create
metadata:
  type: feedback
---

The `mcp__drm-copilot__potential_to_issue` promotion tool creates the GitHub
issue itself (it returns only a "Promoted ... as a <type> workflow" summary, but
the GitHub issue is created as a side effect). The generated `issue.md` already
carries the correct `Issue: #N` and `Issue URL` lines.

**Why:** During issue #15 (nrr-summary) I ran `gh issue create` after
`potential_to_issue`, which produced a duplicate issue (#16) that had to be closed.
The lifecycle tool had already created #15.

**How to apply:** After `potential_to_issue`, read the generated `issue.md` to get
the assigned number; do NOT run `gh issue create`. Derive the canonical issue
number from the feature folder name (the trailing integer), and pass that same
number to `new_active_feature_folder` via `issue_number`. If the folder number and
the tooling-created GitHub issue number disagree, align to the GitHub number.
Related: [[evidence-and-lifecycle-for-every-change]].
