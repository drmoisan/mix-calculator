# Phase 2 — Coverage Delta / Threshold Verification (Issue #62, Cycle 1, P2-T5)

Timestamp: 2026-06-10T09-25
Baseline source: evidence/baseline/pytest-coverage.md
Post-change source: evidence/qa-gates/final-pytest-coverage.md

## Totals

| Metric | Baseline | Post-change | Threshold | Result |
|---|---|---|---|---|
| Line coverage | 99.10% (4823/4867) | 99.10% (4859/4903) | >= 85% | PASS |
| Branch coverage | 94.09% (860/914) | 94.14% (868/922) | >= 75% | PASS |
| Tests | 1026 passed (1 flaky fail) | 1037 passed, 0 failed | green | PASS |

The post-change run added the cycle-1 tests (worksheet-header-columns, edit
wiring source-pool/no-file, columns scroll area, window controls), raising the
statement and branch totals; both coverage percentages remain effectively flat
and above threshold. The Phase 0 flaky property test passed in the final run.

## Changed-line coverage (no regression on changed lines)

| Changed file | Line % | Branch detail | Regression on changed lines |
|---|---|---|---|
| src/gui/_schema_discovery_wiring.py | 100% | 14/14 branches | none |
| src/gui/presenters/source_selection_presenter.py | 99% | 1 pre-existing partial (399->401) | none |
| src/gui/widgets/_schema_builder_tabs.py | 100% | full | none |
| src/gui/widgets/_schema_builder_window_setup.py (new) | 100% | full | none |
| src/gui/widgets/schema_builder_dialog.py | 98% | 1 missed line (378) + 1 partial (481->exit), both pre-existing in unchanged set_derived/_handle_new_derived | none |

All lines added by this cycle (apply_schema_builder_window_flags, the QScrollArea
wrap in build_columns_tab, read_worksheet_header_columns, _build_edit_preview_slice
and the edit wiring) are fully covered by the new tests. The only uncovered
statements/branches in the changed files are pre-existing and outside this cycle's
edits.

Outcome: PASS — line >= 85%, branch >= 75%, no regression on changed lines.
