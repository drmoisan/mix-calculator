# Feature Audit: aop-import-schema-driven (Issue #58)

**Audit Date:** 2026-06-08
**Work Mode:** `full-feature` (from `issue.md`)
**AC Sources:** `spec.md` (Status Final, v1.0) and `user-story.md`
**Base (merge-base):** `63522c00`
**Verdict:** PASS (all 9 acceptance criteria verified; one documentation gap noted)

> Note on AC source: work mode `full-feature` resolves AC sources to `spec.md` AND `user-story.md`. `user-story.md` is absent from the feature folder. The canonical AC list (AC-1..AC-9) is identical in `spec.md` and `issue.md`; the missing `user-story.md` contributes no additional criteria. This is recorded as a non-blocking documentation gap; it does not affect AC verification.

## Scope and Baseline

The audited scope is the full working-tree diff on branch `feat/aop-import-schema-driven` for issue #58 against merge-base `63522c00`, comprising 4 production files (`src/gui/pipeline_service.py`, `src/gui/_aop_schema_import.py` [new], `src/schema_loader.py`, `src/schemas/default_aop.schema.json`) and 9 test files. No caller-supplied narrowing was applied; the audit covers the entire branch diff. The baseline for coverage and AC reconciliation is the merge-base commit (987 tests, 99.08% line / 93.96% branch).

## Acceptance Criteria Inventory

| ID | Criterion (abridged) | Source |
|----|----------------------|--------|
| AC-1 | AOP import runs through `SchemaLoader(default_aop)` with no arithmetic identity validation; broken-total source imports without error | spec.md / issue.md |
| AC-2 | Full-year-YTD source imports successfully (regression for reported failure) | spec.md / issue.md |
| AC-3 | Partial-year-YTD source imports successfully | spec.md / issue.md |
| AC-4 | No blank-total fill; blank total cell yields `0` after coercion, not the month sum; `default_aop.fill_rules` empty | spec.md / issue.md |
| AC-5 | `SchemaLoader.load` forwards `resolver`/`is_tty`/`prompt` to `resolve_key`; `import_aop` wires resolver + `never_tty` + `no_stdin_prompt` | spec.md / issue.md |
| AC-6 | Output column set/order and KEY semantics match the prior loader for populated columns | spec.md / issue.md |
| AC-7 | `import_aop` resolves the header row via `detect_header_row`, not a hardcoded row; non-default offset imports | spec.md / issue.md |
| AC-8 | Existing `SchemaLoader` callers and LE/SKU_LU import paths unaffected | spec.md / issue.md |
| AC-9 | Full toolchain pass; coverage >= 85% line / >= 75% branch; no regression on changed lines; T1 property/mutation obligations for `src/schema_loader.py` | spec.md / issue.md |

## Acceptance Criteria Evaluation

| ID | Verdict | Evidence |
|----|---------|----------|
| AC-1 | PASS | `import_aop` delegates to `import_aop_via_schema` -> `SchemaLoader(default_aop).load` (no arithmetic identity validation in the schema path). `tests/gui/test_pipeline_service.py::test_import_aop_imports_source_with_broken_totals` sets `YTD=999999.0` and asserts it imports and passes through unchanged; `tests/test_schema_loader_parity_aop.py::test_aop_no_arithmetic_validation_loads_broken_totals` corroborates. |
| AC-2 | PASS | `tests/gui/test_pipeline_service.py::test_import_aop_imports_full_year_ytd_source` builds a full-year-YTD workbook (no YTG column, YTD = full Jan..Dec sum via `build_full_year_ytd_workbook`) and asserts a successful import with KEY established. Directly regresses the reported `YTD != sum(months)` failure. |
| AC-3 | PASS | `tests/gui/test_pipeline_service.py::test_import_aop_imports_partial_year_ytd_source` builds a partial-year-YTD (8+4) workbook via `build_aop_workbook` and asserts a successful import. Both real-workbook conventions (full-year and partial-year YTD) are therefore covered by in-memory fixtures. |
| AC-4 | PASS | `src/schemas/default_aop.schema.json` `fill_rules: []` (git diff removes the six fill rules). `tests/test_default_schemas.py::test_aop_fill_rules_cover_ytd_quarters_and_ytg` asserts `schema.fill_rules == ()`; `test_aop_fill_rules_empty_and_header_row_two_round_trips` asserts empty fill rules and `header_row == 2` round-trip. `tests/test_schema_loader_parity_aop.py::test_aop_blank_total_coerces_to_zero_not_month_sum` asserts a blank `YTD` becomes `0.0`, not the month sum. |
| AC-5 | PASS | `src/schema_loader.py` `load()` gains keyword-only `resolver`/`is_tty`/`prompt` forwarded into `resolve_key` (signatures match `src/etl_key.py::resolve_key`). `import_aop_via_schema` passes the resolver callable + `never_tty` + `no_stdin_prompt`. Verified by `tests/test_schema_loader_core.py::test_load_forwards_resolver_seams_to_resolve_key_on_divergence`, the property test `test_property_resolver_action_governs_key_on_divergence`, and the re-targeted `tests/gui/test_pipeline_service_key_seam.py` (AOP forwarding intercepted at `SchemaLoader.load`). The resolver is forwarded as a callable and invoked only on divergence (prompt asserted never called). |
| AC-6 | PASS | `tests/gui/test_pipeline_service.py::test_import_aop_output_columns_and_key_match_prior_loader` and the re-targeted `tests/test_schema_loader_parity_aop.py` (`test_aop_parity_with_ytg`, `test_aop_parity_without_ytg`, `test_aop_parity_sentinel_clean_labels`, `test_aop_parity_no_row_collapse`) verify column set/order and KEY composition. The parity contract (downstream consumes only `Customer`, `Customer Master`, `Super Category`, `PPG`, `SKU Descripiton`, `SKU #`, `Type`, `YTG`, `KEY`) holds; the only observable delta is blank-total rows -> 0 (per Decision 2, no downstream consumer reads those columns). |
| AC-7 | PASS | `import_aop_via_schema` calls `detect_header_row(source, sheet, expected_tokens, min_match=17)` and reads at the detected index; no hardcoded row. `tests/gui/test_pipeline_service.py::test_import_aop_header_detection_drives_the_read` uses a flat (header-at-index-0) workbook where a hardcoded `header=2` would misread and asserts detection drives a correct read (`frame.loc[0, "Customer"] == "Acme Foods"`). |
| AC-8 | PASS | `src/load_aop.py`, `src/_load_aop_helpers.py`, `src/mix_pipeline.py` unchanged (`git diff 63522c00` empty; `evidence/other/non-goal-cli-untouched.md`). `tests/test_schema_loader_core.py::test_load_backward_compatible_without_seam_arguments` confirms positional `load(raw)` / `load(raw, schema)` callers are unaffected. `evidence/regression-testing/unaffected-callers.md` records LE/SKU_LU green. Full suite 998 passed. |
| AC-9 | PASS | Black/Ruff/Pyright clean; pytest 998 passed (+11 vs 987 baseline). Repo-wide 99.08% line / 93.96% branch (above 85%/75%). Changed prod files 100% line (schema_loader.py 100% branch, 6/6) — independently verified from `artifacts/python/lcov.info`. No regression on changed lines (`evidence/qa-gates/coverage-delta.md`). T1 property obligation met (hypothesis resolver-forwarding property test). T1 mutation obligation is a pre-merge/nightly pipeline item per `quality-tiers.md` (`evidence/other/t1-mutation-note.md`); deferral is policy-consistent (mutation runs in pre-merge/nightly, not the per-commit loop). |

## Constraint and Invariant Verification

| Item | Verdict | Evidence |
|------|---------|----------|
| Both real-workbook YTD conventions covered by fixtures | PASS | Full-year via `build_full_year_ytd_workbook`; partial-year (8+4) via `build_aop_workbook`. Both in-memory. |
| Parity contract (downstream-consumed AOP columns + KEY) holds | PASS | Spec parity-contract section + parity suite; no downstream stage reads YTD/quarters/months. |
| No temp files / no `.xlsx` on disk in tests | PASS | Fixtures build `io.BytesIO` workbooks (`tests/aop_fixtures.py`); no filesystem temp files in the changed tests. |
| Blank-total -> 0 behavior tested | PASS | `test_aop_blank_total_coerces_to_zero_not_month_sum` asserts `out.loc[0, "YTD"] == 0.0`. |
| Dedup `mode = none` retained | PASS | `test_aop_parity_no_row_collapse` verifies no row collapse. |
| Non-goal: CLI `load_aop`/`validate_aop`/`build_per_row_checks`/`_import_sources` unchanged | PASS | `git diff 63522c00 -- src/load_aop.py src/_load_aop_helpers.py src/mix_pipeline.py` empty; CLI `mix_pipeline._import_sources` still calls `load_aop.load_aop` at `src/mix_pipeline.py:120`. |

## Acceptance Criteria Check-off

All nine acceptance criteria are evaluated PASS. They are already marked `[x]` in both `spec.md` and `issue.md` (checked off by execution); this audit independently confirms each, so no checkbox change is required. The four "Seeded Test Conditions" / "Test Conditions to Consider" items remain `[ ]` in the source files; they are illustrative seeds, not authoritative acceptance criteria, and their substance is covered by AC-2/AC-3/AC-6 and the integration tests.

### Acceptance Criteria Status

- Source: `spec.md` and `issue.md` (`user-story.md` absent — documentation gap)
- Total AC items: 9
- Checked off (delivered and independently verified): 9
- Remaining (unchecked): 0
- Items remaining: none

## Summary

PASS. All nine acceptance criteria are independently verified against the working-tree diff and the evidence artifacts. One non-blocking documentation gap: `user-story.md` is absent though work mode is `full-feature`. The file-size cap violation on two test files is a policy matter recorded in the policy audit; it does not invalidate any acceptance criterion.
