# Phase 0 — Baseline File Sizes (Issue #48)

Timestamp: 2026-06-01T12-05

Per-file line counts (near-cap and to-be-touched files):

| File | Lines | Cap | Headroom |
|---|---|---|---|
| src/gui/app.py | 499 | 500 | 1 — REQUIRES EXTRACTION before additions |
| src/gui/presenters/pipeline_presenter.py | 490 | 500 | 10 — REQUIRES EXTRACTION before additions |
| src/gui/presenters/import_dispatch.py | 386 | 500 | 114 |
| src/gui/widgets/source_input_widget.py | 355 | 500 | 145 |
| src/gui/protocols.py | 298 | 500 | 202 |
| src/gui/pipeline_service.py | 437 | 500 | 63 |
| src/gui/_main_window_view.py | 108 | 500 | 392 |
| src/gui/_schema_wiring.py | 137 | 500 | 363 |
| src/gui/presenters/source_selection_presenter.py | 198 | 500 | 302 |
| src/gui/services/schema_service.py | 245 | 500 | 255 |
| src/_load_aop_helpers.py | 368 | 500 | 132 |
| src/build_exe.py | 228 | 500 | 272 |

Output Summary:
- BLOCKING for additions: `src/gui/app.py` (499/500) and
  `src/gui/presenters/pipeline_presenter.py` (490/500) must have logic extracted into
  sibling `_*.py` wiring / `import_dispatch.py` modules BEFORE any later phase adds code.
  Phase 1 performs this extraction.
- All other listed files have sufficient headroom for their planned changes.
