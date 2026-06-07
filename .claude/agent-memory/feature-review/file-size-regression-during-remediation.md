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

**How to apply:** Run a full git-diff line-count scan as a standing reaudit step.
Treat any changed test file > 500 as a blocking FAIL (the cap applies to test code
per `general-code-change.md`). Compare to the `main` baseline (`git show main:<f>`)
to characterize whether the cycle introduced the regression. See
[[issue2-file-size-watch]] for the related normalize-le clustering pattern.
