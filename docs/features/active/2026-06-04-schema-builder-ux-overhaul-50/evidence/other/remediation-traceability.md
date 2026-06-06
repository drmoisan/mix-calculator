# Remediation Traceability — Cycle 1 (P7-T9)

Timestamp: 2026-06-05T20-28

Each blocking finding R1-R6 is closed by an integrated test that drives the
production object (the opened `SchemaBuilderDialog` or `build_application`), and
each wired seam has a production call site reachable from the composition root or
the opened dialog (not only a unit test).

## R1-R6 → integrated test + production call site

| Finding | Integrated test (passing) | Production call site (grep-confirmed) |
|---|---|---|
| R1 — drag Columns tab wired into live dialog | `tests/gui/test_schema_builder_dialog.py::test_live_columns_tab_has_drag_tokens_and_dtype_indicators` (opens real `SchemaBuilderDialog` via `open_schema_builder`, asserts `ColumnsTabWidget` present with non-empty `token_names()` and a populated `DtypeCheckWidget`) | `ColumnsTabWidget` constructed in `src/gui/widgets/_schema_builder_tabs.py` (`build_columns_tab`) and driven by `src/gui/widgets/_schema_builder_drag_tabs.py` (`DragTabBinder`), owned by `schema_builder_dialog.py` |
| R2 — drag Key tab wired into live dialog | `tests/gui/test_schema_builder_dialog.py::test_live_key_tab_has_drag_widget_with_seeded_parts` (opens real dialog, asserts `KeyTabWidget` with rendered structured parts + `GenericTextToken` + header column tokens) | `KeyTabWidget` constructed in `_schema_builder_tabs.py` (`build_key_tab`), driven by `DragTabBinder` |
| R3 — derived-formula dialog wired into Derived tab | `tests/gui/test_schema_builder_dialog.py::test_live_derived_button_adds_column_to_columns_tab` (clicks the live "New derived column" button, opens real `DerivedFormulaDialog`, accepts, asserts derived column on Columns tab) | `DerivedFormulaDialog` opened in `src/gui/_schema_open_helpers.py` (`install_new_derived_handler`), installed by `open_schema_builder` |
| R4 — `BuildSpecProvider` injected at composition root | `tests/gui/test_app_wiring_schema.py::test_build_application_per_tab_button_seeds_via_injected_provider` (drives `build_application`, triggers per-tab `build_schema_requested`, asserts seeded required specs + masked preview slice; menu path blank) | `build_spec_provider(_svc)` constructed and passed in `src/gui/app.py:430` → `wire_schema_discovery_and_gating(..., spec_provider=...)` → `wire_build_schema_buttons` |
| R5 — production caller for `new_from_template` | `tests/gui/test_app_wiring_schema.py::test_build_application_new_from_template_seeds_live_dialog` (drives `build_application`, reaches `new_from_template` via the partial-match hand-off, asserts seeded dialog with blank name) | `presenter.new_from_template(template_name)` in `src/gui/_schema_open_helpers.py:159` (`open_new_from_template_builder`), invoked from `app.py` `_on_partial_match` |
| R6 — `on_partial_match` injected into source presenters | `tests/gui/test_source_selection_presenter.py::test_build_application_partial_match_reaches_new_from_template` (drives `build_application`, a partial-band activation invokes the injected callback and reaches new-from-template) | three `on_partial_match=_on_partial_match` at `src/gui/app.py:335,342,349` (the three `SourceSelectionPresenter` constructions) |

## Verification standard

The defect class that caused the cycle-entry FAIL was isolated unit coverage that
masked missing production wiring. Every R# above is proven by an integrated test
that instantiates the production object (`SchemaBuilderDialog` opened via the
production open path, or `build_application` as the composition root), satisfying
the inputs' "Verification on Re-Review" requirement.

## Non-blocking findings

- N1 — `tests/test_schema_serialization.py` (669 lines) split into
  `test_schema_serialization.py` (408), `test_schema_serialization_errors.py` (217),
  and `test_schema_migration.py` (72); union of tests preserved (28 tests, all
  passing). CLOSED.
- N2 — dead `# noqa: N802` directives removed from `_columns_tab_drag.py` and
  `_key_tab_drag.py`; `ruff check` exits 0. CLOSED.
- N3 — `spec.md` Decision 1 and AC 14 reworded to discriminator-conditional
  migration (LE -> aggregate; AOP retains `mode: none`); no code/schema changed.
  CLOSED.
