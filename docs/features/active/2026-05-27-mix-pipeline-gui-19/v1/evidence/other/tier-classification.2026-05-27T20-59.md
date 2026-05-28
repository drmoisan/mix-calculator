# Tier Classification — src/gui/

Timestamp: 2026-05-27T20-59
Command: poetry run python artifacts/orchestration/verify_tier_classification.py
EXIT_CODE: 0

Output Summary:

Every `src/gui/**/*.py` module is classified in `quality-tiers.yml`. Total
modules: 24. Unclassified: 0. The classification matches the research tier
table (T2 for the service seam, view Protocols, exporter base/registry, and
plain-Python presenters; T3 for adapters, concrete exporters, the worker, the
widgets/dialogs, and the main window shell; T4 for empty package markers and
the app composition root).

Module : Tier

```
src/gui/__init__.py : T4
src/gui/app.py : T4
src/gui/exporters/__init__.py : T4
src/gui/exporters/base.py : T2
src/gui/exporters/csv_exporter.py : T3
src/gui/exporters/excel_exporter.py : T3
src/gui/exporters/registry.py : T2
src/gui/main_window.py : T3
src/gui/pipeline_service.py : T2
src/gui/presenters/__init__.py : T4
src/gui/presenters/export_presenter.py : T2
src/gui/presenters/pipeline_presenter.py : T2
src/gui/presenters/source_selection_presenter.py : T2
src/gui/protocols.py : T2
src/gui/services/__init__.py : T4
src/gui/services/db_service.py : T3
src/gui/services/workbook_reader.py : T3
src/gui/widgets/__init__.py : T4
src/gui/widgets/export_dialog.py : T3
src/gui/widgets/preview_widget.py : T3
src/gui/widgets/progress_dialog.py : T3
src/gui/widgets/source_input_widget.py : T3
src/gui/workers/__init__.py : T4
src/gui/workers/pipeline_worker.py : T3
```

Markers (all T4) confirmed: `src/gui/__init__.py`,
`src/gui/services/__init__.py`, `src/gui/exporters/__init__.py`,
`src/gui/presenters/__init__.py`, `src/gui/workers/__init__.py`,
`src/gui/widgets/__init__.py`.

PASS: no unclassified `src/gui` module remains; the `tier-classification` CI
stage would not flag any new module.
