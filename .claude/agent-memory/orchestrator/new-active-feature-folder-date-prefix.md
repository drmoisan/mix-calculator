---
name: new-active-feature-folder-date-prefix
description: new_active_feature_folder date-prefix is context-dependent — standalone features get the YYYY-MM-DD- prefix automatically, but epic-child feature folders do not (git mv those)
metadata:
  type: feedback
---

`mcp__drm-copilot__new_active_feature_folder` date-prefix behavior depends on
context:

- A **standalone** feature promotion DOES get the prefix automatically. In #48
  (2026-06-01), `type: feature` produced
  `2026-06-01-pipeline-gui-hardening-schema-select-48` with the `YYYY-MM-DD-`
  prefix and no `git mv` was needed.
- **Epic-child** feature folders did NOT. During epic #40 decomposition the epic
  folder got `2026-05-30-configurable-schema-subsystem-40` while the four child
  feature folders came out as `schema-model-and-registry-41` etc. (no prefix).

**Why:** The user flagged the missing prefix on the epic children as a deviation;
the canonical convention is the date-prefixed form for every active folder.

**How to apply:** After creating folders, verify the name. For standalone
features the prefix is usually already present (just confirm). For epic-child
feature folders, `git mv` each to add the `YYYY-MM-DD-` prefix (matching the
epic/capture date) and update references in `initiative.md` and the orchestrator
checkpoint before committing. The trailing integer is the issue number used for
canonical-issue derivation, so keep it intact. Related:
[[potential-to-issue-creates-github-issue]].
