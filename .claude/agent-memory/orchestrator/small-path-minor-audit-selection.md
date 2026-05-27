---
name: small-path-minor-audit-selection
description: A bug fix touching ~1-3 production files must run the small path with minor-audit work mode, no spec.md, and AC in issue.md
metadata:
  type: feedback
---

A bug fix whose change budget is roughly 1–3 production files (plus tests) must be
delivered on the **small path** with Work Mode `minor-audit` — not `full-bug`. On
this path there is **no `spec.md`**; all requirements (summary, repro, scope,
test strategy, and an explicit `## Acceptance Criteria` section) live in the
canonical `issue.md`. The `feature-review` agent in `minor-audit` mode reads only
the `## Acceptance Criteria` section of `issue.md` as the AC source.

**Why:** Issue #11 (pr-author-provenance-enforcement) was a single-production-file
hook fix that was incorrectly run on the large path (`full-bug` + `spec.md`) and
marked DONE without on-disk audit artifacts. The user required it be re-run on the
correct small/minor-audit path: requirements consolidated into `issue.md`, work
mode switched to `minor-audit`, `spec.md` deleted, plan rewritten, preflight,
execution, and a real feature-review audit.

**How to apply:** At change-budget routing, if a bug impacts only 1–3 production
files, select small path + `minor-audit`. Ensure `issue.md` carries an explicit
`## Acceptance Criteria` section before delegating to `feature-review`. Do not
create `spec.md` for small-path bugs; its presence in the active folder is a
fail-closed condition for a minor-audit plan. See
[[evidence-and-lifecycle-for-every-change]].
