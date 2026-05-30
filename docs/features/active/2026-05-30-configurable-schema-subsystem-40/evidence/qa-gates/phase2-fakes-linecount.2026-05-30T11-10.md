# Phase 2 — F2 Closure Line Counts (Epic #40, Cycle 1)

Timestamp: 2026-05-30T11-10

Command: `wc -l tests/gui/fakes/*.py`

EXIT_CODE: 0

Output Summary:
F2 resolved. Every file under `tests/gui/fakes/` is <= 500 lines. The former
508-line `fake_views.py` is now a 23-line thin re-export; the view fakes were
split into four per-protocol modules, all comfortably under the ceiling.

```
    1 tests/gui/fakes/__init__.py
  116 tests/gui/fakes/fake_column_matching_view.py
   82 tests/gui/fakes/fake_exporters.py
  169 tests/gui/fakes/fake_pipeline_view.py
  192 tests/gui/fakes/fake_schema_builder_view.py
  414 tests/gui/fakes/fake_services.py
   58 tests/gui/fakes/fake_source_selection_view.py
   23 tests/gui/fakes/fake_views.py
 1055 total
```
