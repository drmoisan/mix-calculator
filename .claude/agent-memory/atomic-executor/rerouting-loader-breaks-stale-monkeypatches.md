---
name: rerouting-loader-breaks-stale-monkeypatches
description: Rerouting a GUI import away from a loader silently breaks every monkeypatch.setattr on the old loader symbol; they pass vacuously then fail
metadata:
  type: project
---

When a `PipelineService.import_*` method is rerouted from one loader to another
(e.g. #58 moved `import_aop` from `src.load_aop.load_aop` to the schema-driven
`SchemaLoader` path), every test that did `monkeypatch.setattr("src.load_aop.load_aop", ...)`
becomes a stale patch: the patched symbol is no longer called, so the real read
path runs against the test's sentinel path arg and the test fails (or worse,
passes vacuously if it only asserts a recorder that is never populated).

**Why:** the GUI test suite patches loaders at their source-module symbol, not at
the import location in `pipeline_service`. Local imports inside the method
(`from src.pandas_io import read_excel_sheet`) resolve the attribute at call time,
so re-targeting works by patching `src.pandas_io.read_excel_sheet` and
`src._header_detection.detect_header_row` (for the buffer-substitution pattern) or
`src.schema_loader.SchemaLoader.load` (for resolver-forwarding assertions).

**How to apply:** after rerouting any `import_*` loader call, grep the whole test
tree for `setattr("src.<old_loader>` and re-target each site at the new read
boundary. Known sites for the AOP reroute were in `tests/gui/test_pipeline_service.py`,
`tests/gui/test_pipeline_service_key_seam.py`,
`tests/gui/integration/test_behavioral_composition.py`,
`tests/gui/test_gui_integration.py`, and `tests/gui/test_key_mismatch_dialog.py`.
LE/SKU_LU stay patched at their loader entry points, so patching the shared
`read_excel_sheet`/`detect_header_row` boundary only affects the AOP path in those
tests.
