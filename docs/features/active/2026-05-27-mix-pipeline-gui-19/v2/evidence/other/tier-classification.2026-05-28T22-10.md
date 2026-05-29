# Tier Classification Verification — v2

Timestamp: 2026-05-28T22-10
Command: `env -u VIRTUAL_ENV poetry run python /tmp/list-tiers.py` (Python enumeration that parses `quality-tiers.yml` and compares its entries against `glob.glob('src/gui/**/*.py')`).
EXIT_CODE: 0
Output Summary:

- Total `src/gui/**/*.py` files on disk: 26.
- Total classified in `quality-tiers.yml`: 26.
- Unclassified: None.
- New v2 entries: `src/gui/runners.py: T2` (registered in P1-T1, the RunnerProtocol seam) and `src/gui/_wiring.py: T4` (registered in P7-T1, the composition-root chooser helpers).
- All v1 `src/gui/**` classifications retained without modification.

Per-module tier listing:

```
src/gui/__init__.py: T4
src/gui/_wiring.py: T4
src/gui/app.py: T4
src/gui/exporters/__init__.py: T4
src/gui/exporters/base.py: T2
src/gui/exporters/csv_exporter.py: T3
src/gui/exporters/excel_exporter.py: T3
src/gui/exporters/registry.py: T2
src/gui/main_window.py: T3
src/gui/pipeline_service.py: T2
src/gui/presenters/__init__.py: T4
src/gui/presenters/export_presenter.py: T2
src/gui/presenters/pipeline_presenter.py: T2
src/gui/presenters/source_selection_presenter.py: T2
src/gui/protocols.py: T2
src/gui/runners.py: T2
src/gui/services/__init__.py: T4
src/gui/services/db_service.py: T3
src/gui/services/workbook_reader.py: T3
src/gui/widgets/__init__.py: T4
src/gui/widgets/export_dialog.py: T3
src/gui/widgets/preview_widget.py: T3
src/gui/widgets/progress_dialog.py: T3
src/gui/widgets/source_input_widget.py: T3
src/gui/workers/__init__.py: T4
src/gui/workers/pipeline_worker.py: T3
```
