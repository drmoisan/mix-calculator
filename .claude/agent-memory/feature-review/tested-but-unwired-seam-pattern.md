---
name: tested-but-unwired-seam-pattern
description: This repo has a recurring defect where new collaborator seams are unit-tested in isolation but never injected at the composition root (app.py build_application); high unit coverage masks it
metadata:
  type: project
---

Recurring defect class in the mix-pipeline GUI: a new seam (presenter method,
widget, wiring function) is added with a `None`-default optional parameter, fully
unit-tested by constructing the seam directly, but never wired into
`src/gui/app.py` `build_application` or the live dialog. Unit-test line coverage
stays high (the tests instantiate the seam), which hides that production cannot
reach it.

**Why:** confirmed on issue #50 (schema-builder-ux-overhaul) — the entire
drag-and-drop Columns/Key UI, the dtype-check widget, the PowerQuery-style
`DerivedFormulaDialog`, `SchemaBuilderPresenter.new_from_template`,
`SourceSelectionPresenter.on_partial_match`, and the per-tab `BuildSpecProvider`
were all implemented + tested but had ZERO production importers/callers. The live
`SchemaBuilderDialog` still used the pre-feature plain-text editors
(`_schema_builder_tabs.py` `build_columns_tab`/`build_key_tab`/`build_derived_tab`).
The caller explicitly flagged prior incidents of this exact pattern.

**How to apply:** During feature review of GUI work, for every new seam grep for
its production caller, not just its test. Verify the chain reaches
`build_application` (`app.py`). Specifically check: (1) new widget modules are
imported by `schema_builder_dialog.py`/`_schema_builder_tabs.py`, not only by
their test; (2) optional callback params (`on_partial_match`, `spec_provider`)
are actually passed at construction in `app.py`, not left at `None`; (3) the
live `build_*_tab` functions return the new drag widgets, not `QPlainTextEdit`/
`QLineEdit`. Coverage % is not evidence of wiring. See
[[configurable-schema-persisted-matching]] (orchestrator memory) for the
intended persisted-matching design these seams were meant to serve.
