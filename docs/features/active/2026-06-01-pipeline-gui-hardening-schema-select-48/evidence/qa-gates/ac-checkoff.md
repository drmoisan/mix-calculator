# Final QA — AC-1..AC-15 Traceability Checkoff (Issue #48)

Timestamp: 2026-06-01T14-25

AC source: `docs/features/active/2026-06-01-pipeline-gui-hardening-schema-select-48/spec.md`
(work mode: full-feature; spec.md is the AC source for AC-1..AC-15).

| AC | Status | Satisfying task(s) | Evidence |
|---|---|---|---|
| AC-1 (no stdin; KEY-mismatch via Qt modal) | SATISFIED | P5-T1, P5-T2, P5-T4, P8-T3 | tests/gui/test_pipeline_service_key_seam.py (default never reaches stdin), tests/gui/integration/test_behavioral_composition.py::test_composed_import_path_never_reaches_stdin |
| AC-2 (modal Keep existing/Rebuild, default Keep existing, maps to policy) | SATISFIED | P5-T2, P5-T4 | tests/gui/test_key_mismatch_dialog.py (trust/overwrite mapping; default -> trust; composition root injects resolver) |
| AC-3 (LE path same dialog handling, no stdin) | SATISFIED | P5-T3, P8-T3 | tests/gui/test_pipeline_service_key_seam.py::test_injected_resolver_maps_selection_to_le_policy; composition test asserts LE forwards trust |
| AC-4 (packaged build no console; dev console logs-only) | SATISFIED | P6-T1, P6-T2 | tests/test_build_exe.py (argv contains --windows-console-mode=disable; packaged entry is GUI main) |
| AC-5 (can_run() true only with all three keys or derived set) | SATISFIED | P3-T1 | tests/gui/test_pipeline_presenter_run_gate.py (parametrized partial-import gate; all-keys; derived-set; running) |
| AC-6 (partial import disables Run; no cascading KeyError) | SATISFIED | P3-T2, P8-T1 | tests/gui/test_pipeline_presenter_run_gate.py::test_partial_import_failure_disables_run_no_keyerror; tests/gui/integration/test_behavioral_pipeline_run.py::test_partial_import_failure_shows_modal_run_disabled_no_keyerror |
| AC-7 (modal + status-bar error surface) | SATISFIED | P4-T1, P4-T2, P4-T3, P8-T1 | tests/gui/test_main_window_view.py (modal + status summary); tests/gui/integration/test_behavioral_import_buttons.py::test_import_failure_shows_modal_and_leaves_run_disabled |
| AC-8 (YTG present: YTD=Jan..Apr, YTG=May..Dec) | SATISFIED | P2-T1, P2-T2 | tests/test_load_aop_helpers.py (build_per_row_checks split; YTG-present frame validates); evidence/regression-testing/ws5-validate-aop.md |
| AC-9 (YTG absent: YTD=sum(MONTHS)) | SATISFIED | P2-T1, P2-T2 | tests/test_load_aop_helpers.py::test_validate_aop_full_year_passes_when_ytg_absent |
| AC-10 (genuine violations still raise ValueError) | SATISFIED | P2-T3 | tests/test_load_aop_helpers.py (three negative-path tests raise ValueError) |
| AC-11 (auto-select matching schema on proceed) | SATISFIED | P7-T1, P7-T3, P8-T2 | tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_proceed_selects_matched_schema; end-to-end schema flow |
| AC-12 (<Choose Schema> placeholder on resolve) | SATISFIED | P7-T1, P7-T4, P8-T2 | tests/gui/test_source_selection_presenter.py::test_on_schema_discovery_resolve_leaves_placeholder |
| AC-13 (Build new schema opens builder dialog) | SATISFIED | P7-T1, P7-T5, P8-T2 | tests/gui/integration/test_behavioral_schema_import.py::test_build_new_schema_button_opens_builder |
| AC-14 (known-file loaders remain default; additive) | SATISFIED | P7-T6 | tests/gui/test_pipeline_service.py::test_default_import_path_is_additive_and_independent_of_schema |
| AC-15 (no confidential figures; synthetic test values) | SATISFIED | P2-T4, P2-T5, P9-T7 | tests/test_load_aop_helpers.py uses only synthetic values (e.g. range(1,13)); a scan of committed WS5 tests/fixtures/evidence confirms no confidential workbook dollar figures appear |

AC-15 confirmation: All WS5 test values in tests/test_load_aop_helpers.py are
synthetic small integer-derived floats. No confidential workbook financial
figures appear in any committed test, fixture, or evidence artifact authored for
this feature. The diagnosis row counts (1522/648) referenced in user-story.md are
row counts authored by planning, not financial values.

Final toolchain (P9): Black PASS (0), Ruff PASS (0), Pyright PASS (0 errors),
Pytest 801 passed; line coverage 99.47%, branch coverage 96.59%.

Outcome: All 15 acceptance criteria satisfied with cited evidence.
