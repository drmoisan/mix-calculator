# Final QA — 500-Line Cap Verification (Issue #48)

Timestamp: 2026-06-01T14-25

Every production, test, and reusable-script Python file touched or added by this
feature is at or under the 500-line hard cap. Line counts:

## Production files
| Lines | File |
|---|---|
| 409 | src/_load_aop_helpers.py |
| 235 | src/build_exe.py |
| 107 | src/gui/_key_mismatch_dialog.py (new) |
| 77 | src/gui/_key_mismatch_seam.py (new) |
| 173 | src/gui/_main_window_view.py |
| 73 | src/gui/_run_wiring.py (new) |
| 271 | src/gui/_schema_wiring.py |
| 494 | src/gui/app.py |
| 481 | src/gui/pipeline_service.py |
| 435 | src/gui/presenters/import_dispatch.py |
| 492 | src/gui/presenters/pipeline_presenter.py |
| 266 | src/gui/presenters/source_selection_presenter.py |
| 349 | src/gui/protocols.py |
| 472 | src/gui/widgets/source_input_widget.py |
| 387 | src/load_aop.py |

## Test / fixture files
| Lines | File |
|---|---|
| 308 | tests/aop_fixtures.py |
| 83 | tests/gui/conftest.py |
| 184 | tests/gui/fakes/fake_pipeline_view.py |
| 84 | tests/gui/fakes/fake_source_selection_view.py |
| 190 | tests/gui/integration/test_behavioral_composition.py |
| 283 | tests/gui/integration/test_behavioral_import_buttons.py |
| 149 | tests/gui/integration/test_behavioral_pipeline_run.py |
| 273 | tests/gui/integration/test_behavioral_schema_import.py |
| 174 | tests/gui/test_app_wiring_schema.py |
| 276 | tests/gui/test_gui_integration.py |
| 174 | tests/gui/test_key_mismatch_dialog.py (new) |
| 129 | tests/gui/test_main_window_view.py (new) |
| 455 | tests/gui/test_pipeline_presenter.py |
| 216 | tests/gui/test_pipeline_presenter_run_gate.py (new) |
| 471 | tests/gui/test_pipeline_service.py |
| 234 | tests/gui/test_pipeline_service_key_seam.py (new) |
| 107 | tests/gui/test_run_wiring.py (new) |
| 375 | tests/gui/test_source_input_widget.py |
| 349 | tests/gui/test_source_selection_presenter.py |
| 427 | tests/test_build_exe.py |
| 494 | tests/test_load_aop.py |
| 193 | tests/test_load_aop_helpers.py (new) |
| 99 | tests/test_load_aop_key.py (new) |

Output Summary:
- Maximum touched-file size: 494 lines (src/gui/app.py and tests/test_load_aop.py).
- `tests/test_load_aop.py` was 583 lines at HEAD (a pre-existing violation that a
  WS5 edit touched); it was split into `tests/test_load_aop_key.py` (KEY-reconcile
  branch tests) so both land under the cap (494 and 99).
- `src/gui/app.py` and `src/gui/presenters/pipeline_presenter.py` were the
  Phase-1 extraction targets and remain under the cap.
- No production, test, or reusable-script file exceeds 500 lines.
