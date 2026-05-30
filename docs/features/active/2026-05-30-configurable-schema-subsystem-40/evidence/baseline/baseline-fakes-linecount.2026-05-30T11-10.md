# Baseline — tests/gui/fakes Line Counts (Epic #40, Cycle 1)

Timestamp: 2026-05-30T11-10

Command: `wc -l tests/gui/fakes/*.py`

EXIT_CODE: 0

Output Summary:
`tests/gui/fakes/fake_views.py` is 508 lines, exceeding the 500-line ceiling (F2).

```
    1 tests/gui/fakes/__init__.py
   82 tests/gui/fakes/fake_exporters.py
  414 tests/gui/fakes/fake_services.py
  508 tests/gui/fakes/fake_views.py   <-- > 500 ceiling
 1005 total
```
