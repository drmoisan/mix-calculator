# Acceptance-Criteria Reconciliation (P4-T7)

Timestamp: 2026-06-08T14-30
AC source: docs/features/active/2026-06-08-aop-import-schema-driven-58/spec.md (## Acceptance Criteria, AC-1..AC-9)

| AC | Implementing tasks | Evidence (test / artifact) | Status |
|---|---|---|---|
| AC-1: schema-driven import, no arithmetic validation | P1-T11, P2-T2, P2-T4, P2-T8, P2-T12 | `test_aop_no_arithmetic_validation_loads_broken_totals` (parity), `test_import_aop_imports_source_with_broken_totals` (pipeline_service); import_aop routes through SchemaLoader(default_aop) | PASS |
| AC-2: full-year-YTD imports (regression) | P2-T1, P2-T7 | `test_import_aop_imports_full_year_ytd_source`; `aop_fixtures.build_full_year_ytd_workbook` | PASS |
| AC-3: partial-year-YTD imports | P2-T7 | `test_import_aop_imports_partial_year_ytd_source` | PASS |
| AC-4: no blank-total fill (blank -> 0) | P1-T1, P1-T3, P1-T4, P1-T11 | `default_aop.fill_rules == ()`; `test_aop_fill_rules_empty_and_header_row_two_round_trips`, `test_aop_blank_total_coerces_to_zero_not_month_sum` | PASS |
| AC-5: seam forwarding + import_aop wiring | P1-T5, P1-T6, P1-T8, P1-T9, P2-T4, P2-T11, P3-T3 | `test_load_forwards_resolver_seams_to_resolve_key_on_divergence`, `test_property_resolver_action_governs_key_on_divergence`, `test_import_aop_forwards_injected_resolver_callable`, `test_build_application_injects_resolver_callable` | PASS |
| AC-6: output column set/order + KEY parity | P1-T11, P2-T10 | `_assert_aop_parity` (column set/order + KEY), `test_import_aop_output_columns_and_key_match_prior_loader` | PASS |
| AC-7: header resolved via detect_header_row | P1-T2, P2-T1, P2-T3, P2-T9 | `default_aop.header_row == 2`; `test_import_aop_header_detection_drives_the_read`; `aop_fixtures.build_offset_header_workbook` | PASS |
| AC-8: existing callers + LE/SKU_LU unaffected | P1-T5, P1-T10, P2-T5, P2-T12, P3-T1, P3-T2, P3-T4 | `test_load_backward_compatible_without_seam_arguments`; unaffected-callers.md (31 + 8 passed); full suite 998 passed | PASS |
| AC-9: full toolchain pass; coverage; T1 obligations | P1-T12, P2-T13, P4-T1..P4-T8 | phase1-qa.md, phase2-qa.md, final-*.md, coverage-delta.md (line 99.08% / branch 93.96%), t1-mutation-note.md | PASS |

All nine acceptance criteria map to completed, evidence-backed tasks with at least one passing test or evidence artifact each.
