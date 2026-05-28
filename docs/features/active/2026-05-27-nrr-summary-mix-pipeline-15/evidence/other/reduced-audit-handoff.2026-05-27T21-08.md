# Reduced-Audit Handoff Note (Issue #15, Small Path)

Timestamp: 2026-05-27T21-08
Author: atomic-executor
Purpose: Hand off to the small-audit reviewer for the reduced post-implementation
audit (plan task [P2-T7]).

## Pre-Audit Self-Assessment Verdict: INCOMPLETE (NOT PASS)

The end-to-end reconciliation acceptance criterion (AC10 / plan [P2-T6]) is not
satisfied: the real-data `nrr_summary` `Check` resolves to `"ERROR"`, not the
required `"CHECK"`. Per the reduced-audit acceptance gate, the verdict must be
BLOCKED or INCOMPLETE (never PASS) when the end-to-end artifact does not show
`Check == "CHECK"`. The reviewer should treat this feature as INCOMPLETE pending
a specification revision (see "Blocker" below).

## Reduced Artifact Checklist (for the reviewer)

Phase 0 — policy-read + four baseline artifacts (present, schema-complete):
- `evidence/baseline/phase0-instructions-read.md` (Timestamp, Policy Order,
  files read, minor-audit precondition confirmation).
- `evidence/baseline/black-baseline.2026-05-27T20-49.md` (EXIT_CODE 0).
- `evidence/baseline/ruff-baseline.2026-05-27T20-49.md` (EXIT_CODE 0).
- `evidence/baseline/pyright-baseline.2026-05-27T20-49.md` (EXIT_CODE 0).
- `evidence/baseline/pytest-baseline.2026-05-27T20-49.md` (EXIT_CODE 0; 185
  passed; 100% line / 100% branch baseline).

Phase 2 — final-QC artifacts (present, schema-complete, single clean pass):
- `evidence/qa-gates/black-final.2026-05-27T21-01.md` (EXIT_CODE 0; clean no-op).
- `evidence/qa-gates/ruff-final.2026-05-27T21-01.md` (EXIT_CODE 0; 0 errors; no
  suppressions added).
- `evidence/qa-gates/pyright-final.2026-05-27T21-01.md` (EXIT_CODE 0; 0 errors, 0
  warnings; no type suppressions).
- `evidence/qa-gates/pytest-final.2026-05-27T21-01.md` (EXIT_CODE 0; 199 passed;
  100% line / 100% branch).
- `evidence/qa-gates/coverage-delta.2026-05-27T21-01.md` (numeric baseline vs
  post-change; changed-code 100% line / 100% branch; thresholds met; no
  regression).

End-to-end artifact (present; reconciliation FAILS):
- `evidence/other/e2e-run.2026-05-27T21-08.md` (EXIT_CODE 0; `nrr_summary`
  written as final table; 20 rows; `Check == "ERROR"`; no confidential values).

## AC-to-Task Traceability (AC1-AC10)

- AC1-AC6 -> [P1-T1]: builder implemented, pure, <= 500 lines per file (split
  into `src/mix_nrr_summary.py` and `src/_mix_nrr_summary_helpers.py`); each
  block reproduced; reconciliation logic implemented. VERIFIED by unit tests.
- AC7 -> [P1-T2], [P2-T6]: integration in `src/mix_pipeline_run.py`;
  `nrr_summary` persisted as the final derived table via `src/pandas_io.py`;
  stdout lists it; CLI exit semantics unchanged. VERIFIED (run exit 0,
  `nrr_summary` last).
- AC8 -> [P1-T3], [P2-T4], [P2-T5]: deterministic fabricated-input tests cover
  each block, the per-Lb/% zero-denominator and empty-input edges, and the
  `Check == "ERROR"` divergence path; changed-code coverage >= thresholds.
  VERIFIED.
- AC9 -> [P1-T4], [P2-T1..T4]: `quality-tiers.yml` classifies both new modules
  T2; `README.md` documents the appended `nrr_summary` table; one clean
  toolchain pass. VERIFIED.
- AC10 -> [P2-T6]: end-to-end `Check == "CHECK"`. NOT SATISFIED — `Check ==
  "ERROR"` on real data.

## Confidentiality

No confidential source numerics, SKU descriptions, or category names appear in
any test, fixture, doc, or evidence artifact. The e2e artifact reports only the
`Check` result, table presence, section names, and row count. Temporary
diagnostic scripts used during the blocker investigation were deleted from
`artifacts/`.

## Blocker (root cause for the INCOMPLETE verdict)

AC5 prescribes that `Category Mix` and `Customer Mix` are the plain `[[#Totals]]`
column sums of `mix_2_category["Category Mix"]` and
`mix_3_customer["Customer Mix"]`. On the real workbook, those cascade-table
column totals do not equal the figures the workbook's NRR_Summary tab uses
(verified by reading the tab directly): `SKU Mix` and `Country Mix` match, but
`Category Mix` and `Customer Mix` differ by several orders of magnitude because
the customer/country mix layers apply `fill_zero_with_avg` recomputation
(`src/mix_rollups.py::_apply_fill_zero_and_recompute`). The workbook derives
those two mix figures from a bottoms-up worksheet computation the pipeline does
not produce as those column totals. As a result `Total Mix` does not tie out and
`Check` is `"ERROR"`.

Recommended remediation (requires planner/spec owner, outside small-path scope):
- Revise AC5 to define the correct `Category Mix` / `Customer Mix` total
  derivation that matches the workbook NRR_Summary tab, OR
- Authorize an expansion to derive those mix totals from the bottoms-up mix
  computation.

The builder is structured so that only the `_mix_rows` inputs (the two affected
totals) would change; the attribute/realization/pricing/reconciliation blocks
already match the workbook.
