---
name: branch-base-check-unmerged-pr-deps
description: Before branching a new feature off main, verify it doesn't functionally depend on code that only exists in an unmerged PR; base on that branch (or wait for merge) if it does
metadata:
  type: feedback
---

When starting a new feature branch, do NOT default to branching off `origin/main`
without first checking whether the new work functionally depends on code that is
still only in an unmerged PR/branch.

**Why:** On issue #58 (AOP schema-driven import) I branched off `origin/main`,
but #58's `import_aop` needed `src/_header_detection.py` / `detect_header_row`,
which existed only in the unmerged PR #56 (issues #55+#57). The user caught it:
"Why is this orchestration not building off of the work for issue #57?" The base
on `main` would have forced a hardcoded `header=2` instead of header detection.
Conceptually related issues (#54/#57 over-constrained-loader theme -> #58 is the
AOP analog) are a strong signal of shared dependencies.

**How to apply:** Before choosing a branch base, run `git cat-file -e
origin/main:<file>` / `git show origin/main:<file>` to confirm the symbols/files
the plan relies on exist on the chosen base. If they live only in an open PR,
either (a) base the new branch on that PR's branch (stack), or (b) recommend
merging it first then base on main. Check file overlap too: even if no functional
dependency, overlapping edits mean conflicts. See [[real-pipeline-workbook-location]].
