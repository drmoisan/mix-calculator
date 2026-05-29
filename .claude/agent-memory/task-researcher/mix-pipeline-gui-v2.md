---
name: mix-pipeline-gui-v2
description: Research findings for mix-pipeline-gui v2 (Issue #19): root cause, key design decisions, and open questions
metadata:
  type: project
---

v2 root cause: v1 `SourceInputWidget.show_preview` is a documented no-op; the composition root never routes preview rows to `PreviewWidget`. All button-state (import enable/disable, run, save, export) is also absent from the wiring. The architecture is correct; the wiring is incomplete.

**Why:** v1 AC tests were unit-anchored and never clicked real buttons or verified the assembled application end-to-end.

**How to apply:** Research artifact at `artifacts/research/mix-pipeline-gui-v2-implementation.2026-05-28T14-30.md` covers Q1-Q8. Load-bearing decisions: (1) preview routing via optional `preview_sink` on `SourceSelectionPresenter`; (2) button-state via new `PipelineViewProtocol` methods + `MainWindowPipelineView` adapter extension; (3) behavioral test seam via extended `build_application` with injectable choosers + `worker` on `WiredApplication`.

Open questions pending user input: CSV dialog type (getSaveFileName vs getExistingDirectory); per-table checklist retention in Export; whether behavioral Run tests wait on `worker.finished` or a presenter-level observable.
