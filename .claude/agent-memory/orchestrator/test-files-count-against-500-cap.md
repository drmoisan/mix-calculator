---
name: test-files-count-against-500-cap
description: The 500-line file cap applies to TEST files too; atomic plans that add tests must include a changed-test-file size scan in final QA or risk a remediation cycle
metadata:
  type: feedback
---

The `.claude/rules/general-code-change.md` 500-line file cap applies to test
code, not just production code (only throwaway scripts, raw text fixtures, and
Markdown are exempt). When a plan adds substantial tests, the final QA phase must
scan the CHANGED/CREATED test files for the cap, not only production files.

**Why:** Issue #58 execution passed all gates but the executor's file-size guard
scanned only the 4 production files. Two test files crossed the cap from added
tests (`tests/gui/test_pipeline_service.py` 471->638; `tests/test_schema_loader_core.py`
374->501), which the feature-review policy-audit flagged as the sole Blocking
finding (B1), forcing a full remediation cycle (split into sibling modules) before
the PR could go green.

**How to apply:** When briefing atomic-planner for any change that adds tests,
require Phase 0 baseline + final QA tasks to run a line-count scan across ALL
changed/created `.py` files (production AND test) asserting each <= 500, and have
the planner pre-empt likely over-cap files with a split task. Splitting shared
test helpers may hit strict Pyright `reportPrivateUsage`; relocate them into an
underscore-prefixed fixture module with `__all__` (repo pattern:
`tests/_mix_rollups_fixtures.py`) rather than cross-importing privates or adding
suppressions.
