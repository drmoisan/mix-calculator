---
name: file-size-regression-during-remediation
description: remediation cycles that fix one 500-line cap violation often introduce another in a heavily-edited test file; always re-scan ALL changed files, do not trust the executor's final-file-sizes evidence
metadata:
  type: feedback
---

When auditing a remediation-cycle EXIT, independently scan EVERY changed/new `.py`
file (production AND test) against the 500-line cap with `awk END{print NR}` over
`git diff main...HEAD --name-only`. Do not rely on the executor's
`evidence/qa-gates/final-file-sizes.md` table — it can omit a violating file.

**Why:** On issue #50 cycle-1 exit, the cycle closed N1 (split a 669-line test) but
added integration tests that pushed `tests/gui/test_schema_builder_presenter.py`
from 229 (main) to 506 lines. The executor's P7-T8 final-file-sizes evidence listed
17 files and did not include this one, so the new cap violation passed the cycle's
self-QA and became the sole blocking finding at exit.

Recurred on issue #58 (2026-06-08, first-pass feature review, not a remediation
cycle): the feature pushed `tests/gui/test_pipeline_service.py` 471->638 and
`tests/test_schema_loader_core.py` 374->501. The executor's
`evidence/qa-gates/file-size-final.md` tracked ONLY the 4 production files (it even
documented extracting a helper to keep `pipeline_service.py` at 500) and never
scanned the changed test files — so two test-file cap violations shipped clean
through self-QA. This blind spot (executor file-size evidence = production-only) is
the consistent failure mode; the audit's independent test-file scan caught both.

**How to apply:** Run a full git-diff line-count scan as a standing reaudit step on
EVERY feature/bug review, not just remediation cycles. Treat any changed test file
> 500 as a blocking FAIL (the cap applies to test code per `general-code-change.md`).
The executor's file-size evidence routinely omits test files; never accept it as the
scan. Compare to the merge-base baseline (`git show <merge-base>:<f>`) to attribute
the regression. See [[issue2-file-size-watch]] for the related normalize-le
clustering pattern.
