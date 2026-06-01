# Post-Extraction File Sizes (Phase 1, Issue #48)

Timestamp: 2026-06-01T12-35

Per-file line counts after the Phase 1 behavior-preserving extraction:

| File | Baseline | Post-Extraction | Cap | Status |
|---|---|---|---|---|
| src/gui/app.py | 499 | 478 | 500 | OK (decreased 21) |
| src/gui/presenters/pipeline_presenter.py | 490 | 492 | 500 | OK (cap headroom 8; gate body moved out, +2 from mandatory structured docstring) |
| src/gui/presenters/import_dispatch.py | 386 | 416 | 500 | OK (gained required_keys_present predicate) |
| src/gui/_run_wiring.py | (new) | 73 | 500 | OK (new sibling wiring module) |
| src/gui/_schema_wiring.py | 137 | 221 | 500 | OK (gained default factories + open_schema_builder) |

Output Summary:
- All Phase 1 production modules are <= 500 lines with headroom for later phases.
- `app.py` dropped from 499 to 478, restoring headroom for any composition-root
  injection needed by WS1a (P5-T4).
- `pipeline_presenter.py` is 492/500. The Run-gate body is now delegated to
  `import_dispatch.required_keys_present`, so the WS3 strengthening (P3-T1) edits
  that predicate, not this file. The small +2 net is the mandatory structured
  docstring (`Returns:` section required by the commenting policy).
- All later phases have confirmed headroom: import_dispatch.py 416/500,
  source_input_widget.py 355/500, protocols.py 298/500, pipeline_service.py
  437/500, _main_window_view.py 108/500.
