---
name: audit-verify-production-call-site
description: A unit-tested view/seam method can pass acceptance review while having zero production callers; verify the wiring call site exists, not just the method + its unit test
metadata:
  type: feedback
---

When an acceptance criterion describes user-visible behavior (e.g. "dropdown auto-selects on match / shows placeholder"), passing it does not prove the supporting method is actually invoked in production.

**Why:** Feature #48 (PR #49) shipped `SourceInputWidget.set_schema_list` with a unit test, and its feature-audit marked AC-11/AC-12 PASS — but `set_schema_list` had zero production callers, so the per-tab schema dropdown listed nothing under `poetry run`. The bundled defaults in `src/schemas/` were also invisible because `SchemaRegistry.list_schemas` and `find_best_match_in_registry` read only the user registry dir, never the bundled dir. The ACs as written covered auto-select/placeholder but never required the list to be *populated*, so the gap passed review. Fixed in the 2026-06-01T23-31 remediation cycle: union-aware registry seam (bundled ∪ user, user wins on name) plus a production `populate_schema_lists` call site in `_schema_list_wiring.py`.

**How to apply:** When scoping or auditing GUI/seam features, grep for a production caller of each new view/protocol method (not just its test). A method exercised only by tests is a red flag. For "available X" lists, confirm both the data source (does it include bundled/default sources?) and the wiring (is the populate call invoked at startup/activation?). See [[evidence-and-lifecycle-for-every-change]] for the lifecycle this remediation ran under.
