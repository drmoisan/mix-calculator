# Remediation Inputs: mix-pipeline-gui (Issue #19) — Post-Rebase Re-audit

**Date:** 2026-05-28
**Source audits:**
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/policy-audit.2026-05-28T12-17.md`
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/code-review.2026-05-28T12-17.md`
- `docs/features/active/2026-05-27-mix-pipeline-gui-19/feature-audit.2026-05-28T12-17.md`

**Branch:** `feature/mix-pipeline-gui-19` @ `e68ea3d`
**Base:** `main` @ `7836c24`

---

## Findings Requiring Remediation

### Finding 1 — Production button-to-presenter wiring gap (MINOR, recommended)

- **Artifacts:**
  - `policy-audit.2026-05-28T12-17.md` Section 8, Gap 2.
  - `code-review.2026-05-28T12-17.md` Findings Table row 1.
  - `feature-audit.2026-05-28T12-17.md` AC #4-#8 (production-wired PARTIAL).
- **Location:** `src/gui/app.py::build_application` (lines 73-137).
- **Detail:** Six `MainWindow` signals are not connected to presenter handlers in the production composition root: `import_one_requested`, `import_all_requested`, `run_requested`, `save_requested`, `open_db_requested`, `export_requested`. Pressing the corresponding buttons in the launched GUI emits a signal with no connected slot, so the action does not run.
- **Required remediation:** Add the six `connect` calls in `build_application`. Optionally also construct a `QThread` + `PipelineWorker` and route Run through the off-UI-thread path. Add at least one click-driven test (using `qtbot`) that asserts the presenter handler is invoked when the button is clicked, so the wiring cannot regress silently.
- **Estimated effort:** Small (mechanical change of ~10 lines plus a smoke test).

### Finding 2 — Non-pre-authorized `# noqa: N802` in production code (PARTIAL, documentation-only)

- **Artifacts:**
  - `policy-audit.2026-05-28T12-17.md` Section 8, Gap 1.
  - `code-review.2026-05-28T12-17.md` Findings Table row 2.
- **Location:** `src/gui/exporters/excel_exporter.py:69`.
- **Detail:** `# noqa: N802 - mirrors the pandas API member name` on a TYPE_CHECKING Protocol method. Not on the pre-authorized list in `.claude/rules/python-suppressions.md`; no explicit user approval recorded.
- **Required remediation (one of):**
  1. Obtain explicit user approval for this single-line suppression (recorded in the feature folder or a commit message).
  2. Extend `.claude/rules/python-suppressions.md` to pre-authorize "TYPE_CHECKING Protocol view mirroring a third-party API member" as an approved `N802` pattern. The reviewer flags this as documentation-only because the audit does not modify policy documents.
- **Estimated effort:** Very small (one approval message OR a small policy doc edit).

### Finding 3 — Stale PR-context artifacts (INFO, operational)

- **Artifacts:**
  - `policy-audit.2026-05-28T12-17.md` Section 8, Gap 4.
  - `code-review.2026-05-28T12-17.md` Findings Table row 5.
- **Location:** `artifacts/pr_context.summary.txt`, `artifacts/pr_context.appendix.txt`.
- **Detail:** Files reference pre-rebase base `b0e048f…` and head `ad8c84fa…`; current refs are `7836c24` and `e68ea3d`.
- **Required remediation:** Regenerate via the orchestrator's collect-PR-context tool against the live refs before opening a PR. The audit itself used live `git` refs, so this remediation only affects downstream PR-creation tooling.
- **Estimated effort:** Very small (tool invocation).

---

## Findings Not Requiring Remediation

- **T2 property-test density** on `pipeline_service.py`, `exporters/registry.py`, `exporters/base.py` — INFO; modules contain mostly orchestration. Branch coverage is 100%. Strict reading of the rule may not apply. No remediation required; add a registry round-trip property test only if the team wants strict conformance.
- **`PipelineWorker.run` broad-catch** — INFO; documented worker boundary, within policy.

---

## Recommendation Cross-Reference

The companion audit artifacts recommend **Remediate** (policy-audit and feature-audit) and **Conditional Go / Remediate** (code-review) — all three converge on the same prioritized remediation list above. Finding 1 (button-wiring) is the only gap with user-visible behavioral impact; Findings 2 and 3 are documentation/operational.
