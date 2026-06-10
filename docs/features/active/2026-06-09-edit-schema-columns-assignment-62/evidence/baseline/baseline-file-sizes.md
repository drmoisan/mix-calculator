# Phase 0 — Baseline File Line Counts (Issue #62)

Timestamp: 2026-06-10T02-01

The 500-line file cap (per .claude/rules/general-code-change.md) applies to every
changed production and test file in this fix. Baseline counts of the files
expected to change:

| File | Baseline lines | <= 500 |
|---|---|---|
| src/gui/presenters/_columns_tab_presenter.py | 357 | yes |
| tests/gui/test_columns_tab_presenter.py | 226 | yes |
| tests/gui/test_schema_builder_presenter_core.py | 310 | yes |
| tests/gui/test_edit_schema_wiring.py | 212 | yes |

Out of scope (must NOT be touched): src/gui/widgets/source_input_widget.py.

Output Summary: All four files expected to change are under the 500-line cap at
baseline. The presenter file has the least headroom (357/500) but the planned
second-pass seeding helper is small. src/gui/widgets/source_input_widget.py is
confirmed out of scope and will not be modified.
