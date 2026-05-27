---
name: evidence-and-lifecycle-for-every-change
description: Evidence goes only under a feature folder; every change (even a 1-file hook/skill/tooling fix) must be promoted to an issue + active folder before implementation
metadata:
  type: feedback
---

Two linked rules, both corrected by the user on 2026-05-27:

1. Evidence artifacts may be written ONLY under a feature folder at
   `docs/features/active/<date>-<short>-<issue>/evidence/<kind>/`. Never invent
   an evidence location (e.g. `.claude/hooks/evidence/`, `scripts/.../evidence/`).
   "It isn't one of the forbidden `artifacts/*` paths" is NOT a justification —
   the only approved sink is the feature folder.
2. Every change goes through the orchestration lifecycle — open a GitHub issue
   and create the active feature folder BEFORE delegating implementation —
   including small tooling changes (hooks, skills, scripts). "It's just a small
   change" is not an exemption.

**Why:** On the pr-author hook hardening I delegated straight to
`powershell-typed-engineer` and committed directly, without promoting to an
issue or creating an active feature folder. With no feature folder, the engineer
placed QA/baseline evidence under `.claude/hooks/evidence/`, which is not an
approved pattern. The missing issue/folder (root cause) produced the bad evidence
location (symptom).

**How to apply:** Before any implementation delegation, run promotion
(`new_potential_*` → `potential_to_issue` → `new_active_feature_folder`) to get
the issue number and feature folder. Pass that folder's `evidence/<kind>/` path
to the engineer as the only permitted evidence sink, and reject any evidence
written elsewhere during review. This applies to `.claude/` tooling changes too.
Related: [[ci-required-checks-enforceable]].
