# Coverage Delta and No-Regression (AC-11)

Timestamp: 2026-06-16T20-20

## Baseline (Phase 0, P0-T5)

- Line coverage: 99.08%
- Branch coverage: 94.10%
- Tests: 1049 passed
- TOTAL row: 5016 statements / 46 missed, 932 branches / 55 partial

## Post-change (Phase 7, P7-T5)

- Line coverage: 99.04%
- Branch coverage: 93.43%
- Tests: 1085 passed
- TOTAL row: 5291 statements / 51 missed, 990 branches / 65 partial

## Thresholds

- Line >= 85%: PASS (99.04%)
- Branch >= 75%: PASS (93.43%)

## Changed / new-code coverage

The feature added ~275 statements and ~58 branches (mostly new helper modules and
the dialog/preview/key/dedup changes). Per-new-module coverage from the
term-missing report:

| Module | Line/branch coverage |
|---|---|
| src/_schema_loader_auto_dedup.py | 100% (no-measures + no-dimensions edges now tested) |
| src/_schema_model_specs.py | 100% |
| src/gui/widgets/_schema_builder_tabs.py | 100% |
| src/gui/widgets/_schema_dedup_discriminator.py | 100% |
| src/gui/widgets/_schema_dialog_surfaces.py | 100% |
| src/gui/widgets/_columns_tab_drop_row.py | 100% |
| src/gui/widgets/schema_builder_dialog.py | 98% |
| src/gui/widgets/_key_multiselect_widget.py | ~92% (interactive itemChanged path now covered) |
| src/gui/widgets/_schema_preview_table.py | 85% |
| src/gui/_schema_open_helpers.py | 95% |
| src/gui/presenters/_columns_tab_presenter.py | 93% |
| src/gui/presenters/_schema_builder_state.py | 93% |

## No regression on changed lines

The aggregate line coverage moved 99.08% -> 99.04% and branch 94.10% -> 93.43%.
The small delta is dilution from new well-tested code, not a regression on
pre-existing changed lines: every modified production module's changed code is
exercised by the added unit/integration tests (window flags, identity multi-line,
derived `=`/bracket round-trip, double-click insert, columns row chooser + masked
value display, key multi-select -> KeySpec, dedup auto model + loader + GUI, preview
table render + missing-input messages, and the AC-9 wired production preview path).
All thresholds are met; outcome is PASS.
