---
name: new-active-feature-folder-date-prefix
description: new_active_feature_folder names epic folders with a YYYY-MM-DD- prefix but feature folders without it; rename child folders to add the prefix
metadata:
  type: feedback
---

`mcp__drm-copilot__new_active_feature_folder` is inconsistent about the date
prefix: `type: epic` produces `2026-05-30-<name>-<issue>`, but `type: feature`
produces `<name>-<issue>` with NO date prefix.

**Why:** During epic #40 decomposition the epic folder got
`2026-05-30-configurable-schema-subsystem-40` while the four child feature
folders came out as `schema-model-and-registry-41` etc. The user flagged the
missing prefix as a deviation; the canonical convention is the date-prefixed
form for every active folder.

**How to apply:** After creating child feature folders for an epic, immediately
`git mv` each to add the `YYYY-MM-DD-` prefix (matching the epic/capture date),
and update references in `initiative.md` and the orchestrator checkpoint before
committing. The trailing integer is the issue number used for canonical-issue
derivation, so keep that intact. Related: [[potential-to-issue-creates-github-issue]].
