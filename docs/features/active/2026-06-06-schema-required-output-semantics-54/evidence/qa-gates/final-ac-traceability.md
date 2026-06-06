# Final QA — Acceptance Criteria Traceability

Timestamp: 2026-06-06T15-55

| AC | Description | Satisfying evidence / artifacts |
|----|-------------|---------------------------------|
| AC-1 | `default_le` `YTD/YTG` required:false, in_output:false, drop_columns [] | src/schemas/default_le.schema.json (edited); tests/test_default_schemas.py::test_le_drops_ytd_ytg_source_column; tests/test_schema_loader_derived.py::test_in_output_false_excludes_le_discriminator_from_output; phase2-gate.md, phase3-gate.md |
| AC-2 | Output by `in_output` inclusion (+ KEY + derived), not `drop_columns` | src/_schema_loader_helpers.py `_output_column_order` + `emit_output_columns`; tests/test_schema_loader_derived.py::test_in_output_true_column_is_included_in_output, ::test_in_output_false_column_is_excluded_from_output; phase2-gate.md |
| AC-3 | LE output equals `normalize_le.TARGET_COLUMNS` exactly | tests/test_schema_loader_parity_le.py (5 pass); phase3-parity-le.md |
| AC-4 | AOP output equals `load_aop`, incl. `YTG` | src/schemas/default_aop.schema.json (YTG in_output:true); tests/test_schema_loader_parity_aop.py (4 pass); phase3-parity-aop.md |
| AC-5 | Processing-only column present, used for dedup, excluded from output | tests/test_schema_loader_derived.py::test_processing_only_discriminator_used_for_dedup_but_excluded; src/_schema_loader_helpers.py `_by_name_optional_columns` docstring; phase3-gate.md |
| AC-6 | `in_output` defaults True; absent loads True; round-trips | src/_schema_model_specs.py ColumnSpec.in_output=True; src/schema_serialization.py; tests/test_schema_serialization.py::test_absent_in_output_defaults_to_true, ::test_in_output_false_round_trips, property test extended; phase1-gate.md |
| AC-7 | Builder carries `in_output` end-to-end; provider-factory split | src/gui/presenters/_schema_builder_state.py (5-tuple + assemble_schema); schema_builder_presenter.py; _columns_tab_presenter.py; _schema_view_protocols.py; schema_builder_dialog.py; _schema_builder_drag_tabs.py; tests/gui/test_schema_builder_assemble.py; tests/gui/test_schema_provider_factory.py::test_real_bundled_le_ytd_ytg_is_in_optional_specs; phase4-gate.md |
| AC-8 | Full toolchain pass; coverage >= 85%/75%; no regression | final-black.md, final-ruff.md, final-pyright.md, final-pytest.md, final-coverage-delta.md (line 99.07%, branch 94.15%, all green) |

Determination: every AC maps to at least one passing artifact. AC-1..AC-8 satisfied.
