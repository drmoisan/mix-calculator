---
name: ac-must-reproduce-real-user-path
description: For GUI behavior bugs, define ACs/tests against the real bundled data and exact user path, not a narrow fake-only condition
metadata:
  type: feedback
---

For a reported GUI behavior bug, the acceptance criteria and at least one test must reproduce the user's exact path against the real bundled artifact — not a narrowly-framed condition validated only with fakes.

**Why:** In #62 the first cycle framed the AC around "seed Columns-tab assignments from persisted aliases." It passed local audit and CI (fakes carried aliases), but the user-observable bug was unchanged: the bundled default schemas (e.g. `src/schemas/default_aop.schema.json`) declare every column with empty `aliases` (mapping is implicit — `canonical_name` == worksheet header), so the alias-seeding seeded nothing. The real defect was that the Edit Schema button opened the builder with no `preview_slice`, leaving the source-column pool empty. The fake-backed AC was vacuously satisfiable while the production path stayed broken. A second remediation cycle was needed after the user verified manually.

**How to apply:** When scoping a GUI/data bug, before writing ACs: (1) identify the actual data the user is editing (here, the bundled default schema) and check whether the proposed fix condition is even exercised by it; (2) trace the exact production signal-to-render path (here `edit_schema_requested` -> wiring -> reader/preview_slice -> `prepopulate` -> rendered assignment) and assert against the rendered state object the UI shows, not an internal presenter object that is not what renders; (3) add at least one test that drives that real path. Relates to [[audit-verify-production-call-site]] (wired-but-wrong-condition is a sibling failure to tested-but-unwired). The orchestrator should not accept a green audit when the AC text does not describe the user-observable symptom.
