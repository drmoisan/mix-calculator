---
name: ci-required-checks-enforceable
description: main now has 5 enforceable required status checks; S9 CI green gate is live (was "no CI configured" earlier)
metadata:
  type: project
---

As of 2026-05-26, branch protection on `main` enforces 5 required status checks on PRs: `CodeQL SAST / CodeQL analyze (python)`, `Dependency review / Dependency review`, `Python quality / Python toolchain (py3.12)`, `Python quality / Python toolchain (py3.13)`, and `Workflow lint / actionlint`. Workflows live under `.github/workflows/` (`ci.yml` orchestrator + `_codeql.yml`, `_dependency-review.yml`, `_python-quality.yml`, `_actionlint.yml` callees).

**Why:** Verified on PR #10 (issue #9) — `gh pr checks <pr> --required` returned all five as required and they ran to completion. This contradicts the issue-#2 checkpoint note that claimed "no .github/workflows and main not protected, so S9 not applicable."

**How to apply:** Treat the S9 CI-green gate as enforceable for every PR. Run `gh pr checks <pr> --required` and poll to completion before writing DONE; do not record `step9_status: not_applicable_no_ci_configured`. Dependency review passes now that the dependency graph is enabled (see user auto-memory). Verify current required-check config with `gh` rather than trusting older checkpoints.
